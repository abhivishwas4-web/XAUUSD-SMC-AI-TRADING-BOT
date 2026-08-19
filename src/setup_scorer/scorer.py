"""Setup scorer for SMC setups (Stage 6)

Scoring components (weights):
HTF Bias Alignment        20
Liquidity Sweep           15
MSS/BOS Confirmation      20
FVG/POI Quality           15
Multi-Timeframe Confluence 10
Market Regime             5
Session Quality           5
Risk/Reward Quality      10

Total = 100

The scorer evaluates an `analysis` dict produced by earlier stages and a `config` dict (from load_config()).
It returns a structured result with component scores, total score, grade and action.
"""
from typing import Dict, Any
from datetime import datetime, timezone


WEIGHTS = {
    'htf': 20,
    'liquidity': 15,
    'mss_bos': 20,
    'fvg': 15,
    'mtf': 10,
    'regime': 5,
    'session': 5,
    'rr': 10,
}

GRADE_MAP = [
    (90, 'EXCEPTIONAL'),
    (80, 'HIGH QUALITY'),
    (70, 'GOOD / WATCH'),
    (60, 'WEAK'),
    (0, 'NO TRADE'),
]


def _cap(v: float) -> float:
    if v < 0:
        return 0.0
    if v > 100:
        return 100.0
    return v


def score_htf(analysis: Dict[str, Any]) -> float:
    """HTF bias alignment: expects analysis to contain 'htf_4h' and 'htf_1h' and 'direction'"""
    weight = WEIGHTS['htf']
    dir_ = analysis.get('direction')
    if not dir_:
        return 0.0
    h4 = analysis.get('htf_4h')
    h1 = analysis.get('htf_1h')
    # h4/h1 can be 'BULLISH'/'BEARISH'/'NEUTRAL' or None
    score = 0.0
    if h4 == dir_ and h1 == dir_:
        score = weight
    elif h4 == dir_ or h1 == dir_:
        score = weight * 0.5
    elif h4 == 'NEUTRAL' or h1 == 'NEUTRAL':
        score = weight * 0.25
    else:
        score = 0.0
    return float(score)


def score_liquidity(analysis: Dict[str, Any]) -> float:
    """Liquidity sweep scoring: expects analysis['liquidity_sweep'] with keys: present(bool), reclaim(bool), confirmation(bool)
    """
    weight = WEIGHTS['liquidity']
    sweep = analysis.get('liquidity_sweep')
    if not sweep:
        return 0.0
    present = bool(sweep.get('present'))
    reclaim = bool(sweep.get('reclaim'))
    confirmation = bool(sweep.get('confirmation'))
    if present and reclaim and confirmation:
        return float(weight)
    if present and reclaim:
        return float(weight * 0.7)
    if present:
        return float(weight * 0.4)
    return 0.0


def score_mss_bos(analysis: Dict[str, Any]) -> float:
    weight = WEIGHTS['mss_bos']
    mss = analysis.get('mss')
    bos = analysis.get('bos')
    # mss/bos can be booleans or dicts
    mss_ok = bool(mss)
    bos_ok = bool(bos)
    if mss_ok and bos_ok:
        return float(weight)
    if mss_ok or bos_ok:
        return float(weight * 0.5)
    return 0.0


def score_fvg(analysis: Dict[str, Any], config: Dict[str, Any]) -> float:
    weight = WEIGHTS['fvg']
    fvg = analysis.get('fvg')
    if not fvg:
        return 0.0
    # fvg expected fields: direction, size, fresh(bool), mitigated(bool), displacement_related(bool)
    size = float(fvg.get('size', 0.0))
    fresh = bool(fvg.get('fresh', True))
    mitigated = bool(fvg.get('mitigated', False))
    displacement = bool(fvg.get('displacement', False))
    # quality scoring: base on size and flags
    cfg_min = config.get('smc', {}).get('fvg', {}).get('min_size', 0.1)
    # size score: 0..1 relative to cfg_min*3 (cap)
    denom = max(cfg_min * 3, 1e-6)
    size_score = min(1.0, size / denom)
    score = size_score * 0.6
    if displacement:
        score += 0.2
    if fresh:
        score += 0.15
    if mitigated:
        score -= 0.3
    # clamp 0..1 then multiply weight
    score = max(0.0, min(1.0, score))
    return float(score * weight)


def score_mtf_confluence(analysis: Dict[str, Any]) -> float:
    weight = WEIGHTS['mtf']
    # expects analysis['mtf_agreement'] integer 0..4 representing how many timeframes agree (4H,1H,15M,5M)
    agree = int(analysis.get('mtf_agreement', 0))
    if agree >= 4:
        return float(weight)
    if agree == 3:
        return float(weight * 0.7)
    if agree == 2:
        return float(weight * 0.4)
    if agree == 1:
        return float(weight * 0.1)
    return 0.0


def score_regime(analysis: Dict[str, Any]) -> float:
    weight = WEIGHTS['regime']
    regime = analysis.get('regime')
    if not regime:
        return 0.0
    if regime == 'TRENDING':
        return float(weight)
    if regime == 'RANGING':
        return float(weight * 0.6)
    if regime == 'CHOPPY':
        return float(weight * 0.2)
    if regime == 'HIGH_VOLATILITY':
        return float(weight * 0.5)
    if regime == 'LOW_VOLATILITY':
        return float(weight * 0.4)
    return 0.0


def score_session(analysis: Dict[str, Any]) -> float:
    weight = WEIGHTS['session']
    quality = analysis.get('session_quality')
    if not quality:
        return 0.0
    if quality == 'HIGH':
        return float(weight)
    if quality == 'MEDIUM':
        return float(weight * 0.6)
    if quality == 'LOW':
        return float(weight * 0.2)
    return 0.0


def score_rr(analysis: Dict[str, Any], config: Dict[str, Any]) -> float:
    weight = WEIGHTS['rr']
    rr = analysis.get('rr')
    if rr is None:
        return 0.0
    try:
        rr = float(rr)
    except Exception:
        return 0.0
    minimum_rr = config.get('analysis', {}).get('minimum_rr', config.get('risk', {}).get('minimum_rr', 2.0))
    preferred_rr = config.get('analysis', {}).get('preferred_rr', config.get('risk', {}).get('preferred_rr', 3.0))
    if rr < minimum_rr:
        return 0.0
    if rr >= preferred_rr:
        return float(weight)
    # linear interpolation between minimum and preferred
    frac = (rr - minimum_rr) / max((preferred_rr - minimum_rr), 1e-6)
    return float(weight * frac)


def compute_score(analysis: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # component scores
    c_htf = score_htf(analysis)
    c_liq = score_liquidity(analysis)
    c_mss = score_mss_bos(analysis)
    c_fvg = score_fvg(analysis, config)
    c_mtf = score_mtf_confluence(analysis)
    c_reg = score_regime(analysis)
    c_sess = score_session(analysis)
    c_rr = score_rr(analysis, config)

    total = c_htf + c_liq + c_mss + c_fvg + c_mtf + c_reg + c_sess + c_rr
    total = _cap(total)

    # grade
    grade = 'NO TRADE'
    for thresh, g in GRADE_MAP:
        if total >= thresh:
            grade = g
            break

    # determine action
    minimum_score = config.get('analysis', {}).get('minimum_setup_score', 80)
    rr_val = analysis.get('rr')
    rr_ok = (rr_val is not None and isinstance(rr_val, (int, float)) and float(rr_val) >= config.get('analysis', {}).get('minimum_rr', 2.0))
    critical_ok = True
    # define critical confirmations: liquidity present and MSS/BOS and fvg valid
    liq = analysis.get('liquidity_sweep')
    mss = analysis.get('mss')
    fvg = analysis.get('fvg')
    if not liq or not liq.get('present'):
        critical_ok = False
    if not (mss or analysis.get('bos')):
        critical_ok = False
    if not fvg:
        critical_ok = False

    if not critical_ok:
        action = 'WAIT'
    elif total >= minimum_score and rr_ok:
        action = 'ACTIONABLE SETUP'
    elif 70 <= total < minimum_score:
        action = 'WATCH'
    else:
        action = 'NO TRADE'

    result = {
        'score': round(total, 2),
        'grade': grade,
        'direction': analysis.get('direction'),
        'action': action,
        'component_scores': {
            'htf': round(c_htf, 2),
            'liquidity': round(c_liq, 2),
            'mss_bos': round(c_mss, 2),
            'fvg': round(c_fvg, 2),
            'mtf': round(c_mtf, 2),
            'regime': round(c_reg, 2),
            'session': round(c_sess, 2),
            'rr': round(c_rr, 2),
        },
        'reasons': {
            'rr_ok': rr_ok,
            'critical_ok': critical_ok,
        },
        'rr': analysis.get('rr'),
        'minimum_score': minimum_score,
        'timestamp': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    }

    return result
