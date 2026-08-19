import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class JSONCacheManager:
    def __init__(self, cache_dir: str, default_max_age_minutes: int = 720):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_max_age = default_max_age_minutes

    def _path(self, symbol: str, timeframe: str) -> Path:
        fname = f"{symbol.replace('/', '_')}_{timeframe}.json"
        return self.cache_dir / fname

    def load(self, symbol: str, timeframe: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """Return tuple (payload_or_None, reason)

        reason: 'hit', 'miss', 'corrupted'
        """
        p = self._path(symbol, timeframe)
        if not p.exists():
            return None, 'miss'
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            logger.exception('Corrupted cache file: %s', p)
            try:
                p.unlink()
            except Exception:
                pass
            return None, 'corrupted'

        return data, 'hit'

    def save(self, provider: str, symbol: str, timeframe: str, candles: list, ttl_minutes: int):
        p = self._path(symbol, timeframe)
        payload = {
            'provider': provider,
            'symbol': symbol,
            'timeframe': timeframe,
            'candles': candles,
            'fetched_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'last_update': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'ttl_minutes': ttl_minutes
        }
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(payload, f, default=str)
        except Exception:
            logger.exception('Failed to write cache to %s', p)

    def is_fresh(self, data: Dict[str, Any]) -> bool:
        if not data:
            return False
        ttl = data.get('ttl_minutes') or self.default_max_age
        fetched = data.get('fetched_at') or data.get('last_update')
        if not fetched:
            return False
        try:
            ts = datetime.fromisoformat(fetched)
        except Exception:
            return False
        age = datetime.utcnow().replace(tzinfo=timezone.utc) - ts
        return age <= timedelta(minutes=ttl)

    def data_age_seconds(self, data: Dict[str, Any]) -> Optional[int]:
        if not data:
            return None
        fetched = data.get('fetched_at') or data.get('last_update')
        if not fetched:
            return None
        try:
            ts = datetime.fromisoformat(fetched)
        except Exception:
            return None
        age = datetime.utcnow().replace(tzinfo=timezone.utc) - ts
        return int(age.total_seconds())
