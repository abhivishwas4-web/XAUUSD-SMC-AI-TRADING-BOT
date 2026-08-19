src/market_data/provider_factory.py

from src.market_data.interface import MarketDataProvider


def get_provider(name: str, cfg: dict) -> MarketDataProvider:
    name = name.lower()
    if name == 'twelvedata':
        from src.market_data.providers.twelvedata_provider import TwelveDataProvider
        return TwelveDataProvider(cfg)
    raise NotImplementedError(f"Provider '{name}' is not implemented")
