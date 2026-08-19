src/market_data/cache_manager.py

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class JSONCacheManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, symbol: str, timeframe: str) -> Path:
        fname = f"{symbol.replace('/', '_')}_{timeframe}.json"
        return self.cache_dir / fname

    def load(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        p = self._path(symbol, timeframe)
        if not p.exists():
            return None
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def save(self, symbol: str, timeframe: str, payload: Dict[str, Any]):
        p = self._path(symbol, timeframe)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(payload, f, default=str)
