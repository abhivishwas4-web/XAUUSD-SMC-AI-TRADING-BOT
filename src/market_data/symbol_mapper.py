src/market_data/symbol_mapper.py

from typing import Dict


SYMBOL_MAP = {
    'XAUUSD': 'XAU/USD',
    'XAU/USD': 'XAU/USD'
}


def map_symbol(alias: str) -> str:
    alias = alias.strip()
    if alias not in SYMBOL_MAP:
        raise ValueError(f"Unknown symbol alias: {alias}")
    return SYMBOL_MAP[alias]
