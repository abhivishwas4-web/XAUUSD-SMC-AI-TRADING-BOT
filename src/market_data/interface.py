src/market_data/interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class MarketDataProvider(ABC):
    """Abstract interface for market data providers."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Return latest price dict with keys: price, timestamp"""

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, output_size: int) -> List[Dict[str, Any]]:
        """Return list of OHLCV candles (dicts) ordered newest-last or oldest-first as documented."""

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return provider health information."""
