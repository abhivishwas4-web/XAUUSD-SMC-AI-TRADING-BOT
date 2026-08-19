import pytest
from src.market_data.symbol_mapper import map_symbol


def test_symbol_mapping_xauusd():
    assert map_symbol('XAUUSD') == 'XAU/USD'


def test_symbol_mapping_xau_slash_usd():
    assert map_symbol('XAU/USD') == 'XAU/USD'
