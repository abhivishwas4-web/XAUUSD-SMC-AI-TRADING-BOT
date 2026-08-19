"""Analysis Orchestrator (Stage 7)

Coordinates data retrieval, caching, analysis, SMC engine, technical analysis, risk engine and scorer.
The orchestrator uses existing modules and keeps logic lightweight: it calls into components and assembles the final report.

For testability, many components are expected to be monkeypatched in unit tests (provider, cache, budget, analysis functions).
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.utils.config import load_config
from src.market_data.provider_factory import get_provider
from src.market_data.cache_manager import JSONCacheManager
from src.market_data.budget_manager import APICreditManager
from src.market_data.symbol_mapper import map_symbol
from src.smc_engine import swing_points, structure, liquidity as liq_mod, sweep, displacement as disp_mod, fvg as fvg_mod
from src.technical_analysis import atr as atr_mod, regime as regime_mod, sessions as sessions_mod
from src.risk_engine import entry as entry_mod, stop_loss as sl_mod, take_profit as tp_mod, rr as rr_mod
from src.setup_scorer import scorer as scorer_mod
from src.utils.logger import get_logger
from src.utils.exceptions import DataError

logger = get_logger(__name__)


class AnalysisOrchestrator:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None):
        self.cfg = cfg or load_config()
        self.provider_name = self.cfg.get('provider', 'twelvedata')
        self.symbol_alias = self.cfg.get('symbol', 'XAU/USD')
        try:
            self.mapped_symbol = map_symbol(self.symbol_alias)
        except Exception:
            # allow direct symbol
            self.mapped_symbol = self.symbol_alias
        cache_path = self.cfg.get('cache', {}).get('path', 'data/cache')
        self.cache = JSONCacheManager(cache_path)
        api_cfg = self.cfg.get('api_budget', {})
        self.budget = APICreditManager(api_cfg.get('daily_api_budget', 700), api_cfg.get('safety_reserve', 100), api_cfg.get('per_minute_limit', 8))
        # provider instantiated lazily to allow test monkeypatching
        self.provider = None

    def _get_provider(self):
        if not self.provider:
            self.provider = get_provider(self.provider_name, self.cfg)
        return self.provider

    def _fetch_timeframe(self, timeframe: str) -> Dict[str, Any]:
        # Check cache
        data, reason = self.cache.load(self.mapped_symbol, timeframe)
        if data and self.cache.is_fresh(data):
            self.budget.record_cache_hit()
            return {'source': 'cache', 'candles': data.get('candles'), 'cache_reason': reason}
        # Not fresh -> check budget
        self.budget.record_cache_miss()
        if not self.budget.can_request(cost=1):
            raise DataError('API BUDGET PROTECTION — ANALYSIS TEMPORARILY LIMITED')
        prov = self._get_provider()
        # Use configured output_size
        tf_cfg = self.cfg.get('timeframes', {}).get(timeframe, {})
        output_size = tf_cfg.get('output_size', 100)
        candles = prov.get_candles(self.mapped_symbol, timeframe, output_size)
        # validate candles minimally
        if not candles or not isinstance(candles, list):
            raise DataError('DATA ERROR — XAUUSD MARKET DATA UNAVAILABLE')
        # save to cache
        ttl = tf_cfg.get('ttl_minutes', 60)
        self.cache.save(self.provider_name, self.mapped_symbol, timeframe, candles, ttl)
        self.budget.record_request(cost=1)
        return {'source': 'api', 'candles': candles, 'cache_reason': reason}

    def analyze(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {'symbol': self.mapped_symbol, 'provider': self.provider_name, 'timestamp': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(), 'data_status': 'OK', 'reasons': [], 'warnings': []}
        try:
            # provider health check
            prov = self._get_provider()
            pinfo = prov.health_check()
            result['provider_health'] = pinfo
            if pinfo.get('status') not in ('HEALTHY', 'UNKNOWN'):
                result['data_status'] = 'DATA ERROR — XAUUSD MARKET DATA UNAVAILABLE'
                return result

            # Fetch timeframes
            timeframes = ['4H', '1H', '15M', '5M']
            candles_tf: Dict[str, List[Dict[str, Any]]] = {}
            cache_status = {}
            for tf in timeframes:
                try:
                    fetched = self._fetch_timeframe(tf)
                    candles_tf[tf] = fetched['candles']
                    cache_status[tf] = fetched['source']
                except DataError as e:
                    msg = str(e)
                    if 'BUDGET' in msg:
                        result['data_status'] = 'API BUDGET PROTECTION — ANALYSIS TEMPORARILY LIMITED'
                        return result
                    else:
                        result['data_status'] = msg
                        return result

            result['cache_status'] = cache_status
            # Basic validation
            if any(not candles_tf.get(tf) for tf in timeframes):
                result['data_status'] = 'INSUFFICIENT DATA — ANALYSIS DISABLED'
                return result

            # 4H analysis: swings & structure
            swings_4h = swing_points.detect_swings(candles_tf['4H'], left=self.cfg.get('smc', {}).get('swing', {}).get('left', 2), right=self.cfg.get('smc', {}).get('swing', {}).get('right', 2))
            events_4h = structure.detect_structure_from_swings(swings_4h)
            result['4h_analysis'] = {'swings': swings_4h, 'structure_events': events_4h}

            # 1H analysis
            swings_1h = swing_points.detect_swings(candles_tf['1H'], left=self.cfg.get('smc', {}).get('swing', {}).get('left', 2), right=self.cfg.get('smc', {}).get('swing', {}).get('right', 2))
            events_1h = structure.detect_structure_from_swings(swings_1h)
            result['1h_analysis'] = {'swings': swings_1h, 'structure_events': events_1h}

            # HTF bias
            def derive_bias(events):
                # simplistic: count bull vs bear events
                bulls = sum(1 for e in events if e.get('direction') == 'bull')
                bears = sum(1 for e in events if e.get('direction') == 'bear')
                if bulls > bears:
                    return 'BULLISH'
                if bears > bulls:
                    return 'BEARISH'
                return 'NEUTRAL'

            bias_4h = derive_bias(events_4h)
            bias_1h = derive_bias(events_1h)
            result['htf_bias'] = {'4h': bias_4h, '1h': bias_1h}

            # 15M analysis
            swings_15m = swing_points.detect_swings(candles_tf['15M'], left=1, right=1)
            events_15m = structure.detect_structure_from_swings(swings_15m)
            pdh, pdl = liq_mod.previous_day_high_low(candles_tf['15M'])
            eq_highs, eq_lows = liq_mod.equal_levels(candles_tf['15M'], tolerance=self.cfg.get('smc', {}).get('liquidity', {}).get('equal_tolerance', 0.001))
            result['15m_analysis'] = {'swings': swings_15m, 'structure_events': events_15m, 'pdh': pdh, 'pdl': pdl, 'equal_highs': eq_highs, 'equal_lows': eq_lows}

            # detect liquidity sweep on PDH/PDL
            sweep_pdh = sweep.detect_sweep_for_level(pdh, candles_tf['15M'])
            sweep_pdl = sweep.detect_sweep_for_level(pdl, candles_tf['15M'])
            result['liquidity'] = {'pdh': pdh, 'pdl': pdl, 'eq_highs': eq_highs, 'eq_lows': eq_lows}
            result['liquidity_sweep'] = {'pdh_sweep': sweep_pdh, 'pdl_sweep': sweep_pdl}

            # 5M analysis
            swings_5m = swing_points.detect_swings(candles_tf['5M'], left=1, right=1)
            events_5m = structure.detect_structure_from_swings(swings_5m)
            result['5m_analysis'] = {'swings': swings_5m, 'structure_events': events_5m}

            # MSS/BOS detection: look for BOS in events_5m or events_15m
            bos_present = any(e.get('type') == 'BOS' for e in events_5m + events_15m)
            mss_present = bool(events_5m) and bool(events_15m)
            result['mss'] = mss_present
            result['bos'] = bos_present

            # displacement
            disp = disp_mod.detect_displacement(candles_tf['5M'], atr_multiplier=self.cfg.get('smc', {}).get('displacement', {}).get('atr_multiplier', 1.5), lookback=self.cfg.get('smc', {}).get('displacement', {}).get('lookback', 20))
            result['displacement'] = disp

            # fvg detection on 5M
            fgvs = fvg_mod.detect_fvg(candles_tf['5M'], min_size=self.cfg.get('smc', {}).get('fvg', {}).get('min_size', 0.1))
            result['fvg'] = fgvs

            # technical analysis: ATR and regime
            atr_res = atr_mod.calculate_atr(candles_tf['15M'], period=self.cfg.get('technical', {}).get('atr', {}).get('period', 14))
            regime_res = regime_mod.classify_regime(candles_tf['15M'], atr_res.atr if hasattr(atr_res, 'atr') else 0.0, self.cfg)
            result['atr'] = {'value': atr_res.atr, 'period': atr_res.period, 'status': atr_res.status}
            result['market_regime'] = regime_res

            # session
            sess = sessions_mod.get_session(datetime.utcnow(), self.cfg)
            result['session'] = sess
            result['session_quality'] = sess.get('quality')

            # current market price
            try:
                price_info = prov.get_current_price(self.mapped_symbol)
                market_price = float(price_info.get('price'))
            except Exception:
                market_price = None
            result['market_price'] = market_price

            # Build analysis input for scorer and risk engine
            analysis_input = {
                'direction': 'LONG' if bias_4h == 'BULLISH' and bias_1h == 'BULLISH' else ('SHORT' if bias_4h == 'BEARISH' and bias_1h == 'BEARISH' else 'NEUTRAL'),
                'htf_4h': bias_4h,
                'htf_1h': bias_1h,
                'liquidity_sweep': {'present': bool(sweep_pdh or sweep_pdl), 'reclaim': bool((sweep_pdh and sweep_pdh.get('reclaim')) or (sweep_pdl and sweep_pdl.get('reclaim'))), 'confirmation': bool((sweep_pdh and sweep_pdh.get('confirmation')) or (sweep_pdl and sweep_pdl.get('confirmation')))},
                'mss': mss_present,
                'bos': bos_present,
                'fvg': fgvs[0] if fgvs else None,
                'mtf_agreement': (4 if (bias_4h == bias_1h == ('BULLISH' if bias_1h=='BULLISH' else 'BEARISH')) else 2),
                'regime': regime_res.get('regime'),
                'session_quality': sess.get('quality'),
                'rr': None,
            }

            # Entry calculation
            setup = {'direction': analysis_input['direction'], 'fvg': analysis_input['fvg'], 'liquidity_level': pdh if analysis_input['direction']=='LONG' else pdl, 'mss_confirmed': analysis_input['mss']}
            entry_res = entry_mod.determine_entry(setup, market_price, self.cfg)
            result['entry'] = entry_res

            if not entry_res.get('valid'):
                # no valid entry -> finalize with scorer that will likely say WAIT/NO TRADE
                analysis_input['rr'] = None
                score = scorer_mod.compute_score(analysis_input, self.cfg)
                result['setup_score'] = score
                result['action'] = score.get('action')
                return result

            entry_price = entry_res.get('entry_price')

            # Stop loss
            # choose invalidation level = swept low/high or nearest swing
            invalidation = pdl if analysis_input['direction']=='LONG' else pdh
            sl_res = sl_mod.compute_stop_loss(entry_price, analysis_input['direction'], invalidation, atr_res.atr if hasattr(atr_res, 'atr') else None, self.cfg)
            result['stop_loss'] = sl_res

            if not sl_res.get('valid'):
                analysis_input['rr'] = None
                score = scorer_mod.compute_score(analysis_input, self.cfg)
                result['setup_score'] = score
                result['action'] = score.get('action')
                return result

            # Take profit
            # assemble liquidity targets from equal highs/lows and PDH/PDL
            liquidity_targets = []
            if result['liquidity'].get('eq_highs'):
                liquidity_targets.extend(result['liquidity']['eq_highs'])
            if result['liquidity'].get('eq_lows'):
                liquidity_targets.extend(result['liquidity']['eq_lows'])
            liquidity_targets.extend([result['liquidity'].get('pdh'), result['liquidity'].get('pdl')])
            tp_res = tp_mod.select_tps(entry_price, analysis_input['direction'], [t for t in liquidity_targets if t], self.cfg)
            result['tp'] = tp_res

            if not tp_res.get('valid'):
                analysis_input['rr'] = None
                score = scorer_mod.compute_score(analysis_input, self.cfg)
                result['setup_score'] = score
                result['action'] = score.get('action')
                return result

            # RR calculation using TP1
            rr_calc = rr_mod.compute_rr(entry_price, sl_res.get('stop_loss'), tp_res.get('tp1'))
            result['rr'] = rr_calc
            analysis_input['rr'] = rr_calc.get('rr') if rr_calc.get('valid') else None

            # Score
            score = scorer_mod.compute_score(analysis_input, self.cfg)
            result['setup_score'] = score
            result['setup_grade'] = score.get('grade')
            result['action'] = score.get('action')

            return result

        except Exception as e:
            logger.exception('Unexpected error in analysis_orchestrator')
            result['data_status'] = 'ERROR'
            result['reasons'].append(str(e))
            return result
