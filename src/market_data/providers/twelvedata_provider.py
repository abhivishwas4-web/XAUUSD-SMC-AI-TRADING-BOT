from typing import List, Dict, Any, Optional
import requests
import time
import logging
from datetime import datetime, timezone
import os

from src.market_data.interface import MarketDataProvider
from src.utils.exceptions import DataError, RateLimitError

logger = logging.getLogger(__name__)


class TwelveDataProvider(MarketDataProvider):
    """Twelve Data provider implementation (lightweight, injectable via factory).

    Configuration expected in cfg dict (loaded from config.yaml):
      cfg['env']['TWELVE_DATA_API_KEY']
      cfg['timeframes'] -> mapping for output_size & ttl
    """

    BASE_URL = os.getenv('TWELVE_DATA_BASE_URL', 'https://api.twelvedata.com')

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.api_key = cfg.get('env', {}).get('TWELVE_DATA_API_KEY')
        self.session = requests.Session()
        self.timeout = cfg.get('provider', {}).get('timeout_seconds', 10) if isinstance(cfg.get('provider'), dict) else 10

    def _require_api_key(self):
        if not self.api_key:
            raise DataError('TWELVE_DATA_API_KEY not configured')

    def _validate_candle(self, c: Dict[str, Any]) -> Dict[str, Any]:
        # Expected fields: datetime (or timestamp), open, high, low, close, volume(optional)
        dt = c.get('datetime') or c.get('time') or c.get('timestamp')
        if not dt:
            raise DataError('Candle missing datetime')
        # parseable datetime
        try:
            # Twelve Data returns ISO format string
            ts = datetime.fromisoformat(dt.replace('Z', '+00:00')) if isinstance(dt, str) else datetime.fromtimestamp(int(dt), tz=timezone.utc)
        except Exception:
            raise DataError('Invalid candle datetime')

        try:
            o = float(c.get('open'))
            h = float(c.get('high'))
            l = float(c.get('low'))
            cl = float(c.get('close'))
        except Exception:
            raise DataError('Invalid numeric OHLC in candle')

        vol = c.get('volume')
        if vol is not None:
            try:
                vol = float(vol)
            except Exception:
                vol = None

        return {
            'datetime': ts.replace(tzinfo=timezone.utc).isoformat(),
            'open': o,
            'high': h,
            'low': l,
            'close': cl,
            'volume': vol,
        }

    def _call_api(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._require_api_key()
        url = f"{self.BASE_URL}/{path}"
        params = dict(params)
        params['apikey'] = self.api_key
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            logger.exception('Network error calling Twelve Data')
            raise DataError('Network error when calling provider')

        if r.status_code == 429:
            # Rate limited
            logger.warning('Twelve Data returned 429')
            raise RateLimitError('Provider rate limited (429)')

        if r.status_code >= 400:
            logger.error('Twelve Data returned HTTP %s: %s', r.status_code, r.text)
            raise DataError(f'Provider HTTP error {r.status_code}')

        try:
            payload = r.json()
        except ValueError:
            logger.exception('Malformed JSON from provider')
            raise DataError('Malformed JSON from provider')

        # Twelve Data may include an 'status'='error' and 'message'
        if isinstance(payload, dict) and payload.get('status') == 'error':
            msg = payload.get('message') or payload.get('msg') or 'Provider error'
            logger.error('Provider error payload: %s', msg)
            raise DataError(f'Provider error: {msg}')

        return payload

    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Return latest price dict with keys: price, timestamp"""
        # Use Twelve Data /price endpoint
        self._require_api_key()
        mapped = symbol
        params = {'symbol': mapped}
        try:
            payload = self._call_api('price', params)
        except RateLimitError:
            raise
        except DataError:
            raise

        price = payload.get('price')
        ts = payload.get('datetime') or payload.get('timestamp')
        if price is None:
            raise DataError('Price missing in provider response')
        try:
            price = float(price)
        except Exception:
            raise DataError('Invalid price format')

        # timestamp may be absent; if present, convert
        if ts:
            try:
                ts_parsed = datetime.fromisoformat(ts.replace('Z', '+00:00')) if isinstance(ts, str) else datetime.fromtimestamp(int(ts), tz=timezone.utc)
                ts_str = ts_parsed.replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                ts_str = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        else:
            ts_str = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

        return {'price': price, 'timestamp': ts_str}

    def get_candles(self, symbol: str, timeframe: str, output_size: int) -> List[Dict[str, Any]]:
        """Fetch candles from Twelve Data and return list of validated candles ordered oldest->newest"""
        # Map timeframe to Twelve Data interval string
        # Expect timeframe strings like '4H', '1H', '15M', '5M', '1M'
        tf_map = {
            '4H': '4h',
            '1H': '1h',
            '15M': '15min',
            '5M': '5min',
            '1M': '1min'
        }
        interval = tf_map.get(timeframe.upper())
        if not interval:
            raise DataError(f'Unsupported timeframe: {timeframe}')

        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': output_size,
            'format': 'JSON'
        }

        try:
            payload = self._call_api('time_series', params)
        except RateLimitError:
            raise
        except DataError:
            raise

        # Twelve Data returns 'values' array with newest-first
        values = payload.get('values')
        if not values or not isinstance(values, list):
            raise DataError('No candle values returned')

        candles = []
        # values are newest->oldest; reverse to oldest->newest
        for raw in reversed(values):
            candle = self._validate_candle(raw)
            candles.append(candle)

        return candles

    def health_check(self) -> Dict[str, Any]:
        """Return provider health information without exposing API keys."""
        info: Dict[str, Any] = {'provider': 'twelvedata', 'status': 'UNKNOWN', 'details': {}}
        try:
            # Quick call to price for XAU/USD (do not throw API key error here, handle gracefully)
            if not self.api_key:
                info['status'] = 'ERROR'
                info['details']['error'] = 'API key not configured'
                return info

            # request price for mapped XAU/USD symbol
            try:
                res = self.get_current_price(self.cfg.get('symbol', 'XAU/USD'))
                info['status'] = 'HEALTHY'
                info['details']['last_price_timestamp'] = res.get('timestamp')
            except RateLimitError:
                info['status'] = 'WARNING'
                info['details']['warning'] = 'Rate limited (429)'
            except DataError as e:
                info['status'] = 'ERROR'
                info['details']['error'] = str(e)
        except Exception as e:
            logger.exception('Unexpected error in health_check')
            info['status'] = 'ERROR'
            info['details']['error'] = 'Unexpected error'
        return info
