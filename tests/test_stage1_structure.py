tests/test_stage1_structure.py

import pytest
from src.market_data.symbol_mapper import map_symbol
from src.utils.config import load_config


def test_symbol_mapping():
    assert map_symbol('XAUUSD') == 'XAU/USD'
    assert map_symbol('XAU/USD') == 'XAU/USD'


def test_load_config():
    cfg = load_config()
    assert 'provider' in cfg
    assert 'timeframes' in cfg
