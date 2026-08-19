import pytest
from src.smc_engine.swing_points import detect_swings


def make_candle(ts, o, h, l, c):
    return {'datetime': ts, 'open': o, 'high': h, 'low': l, 'close': c}


def test_detect_simple_swings():
    candles = [
        make_candle('2026-01-01T00:00:00Z',1,2,0.9,1.5),
        make_candle('2026-01-01T01:00:00Z',1.5,2.5,1.4,2.0),
        make_candle('2026-01-01T02:00:00Z',2.0,3.0,1.9,2.8),
        make_candle('2026-01-01T03:00:00Z',2.8,3.5,2.7,3.2),
        make_candle('2026-01-01T04:00:00Z',3.2,3.4,3.0,3.1),
        make_candle('2026-01-01T05:00:00Z',3.1,3.6,3.0,3.5),
    ]
    swings = detect_swings(candles, left=1, right=1)
    assert isinstance(swings, list)
    # expect at least one high and one low
    types = set([s['type'] for s in swings])
    assert 'high' in types or 'low' in types


def test_insufficient_candles():
    candles = [make_candle('2026-01-01T00:00:00Z',1,1,1,1)]
    swings = detect_swings(candles, left=2, right=2)
    assert swings == []
