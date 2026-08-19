import pytest
from src.smc_engine.sweep import detect_sweep_for_level


def make_candle(ts, o, h, l, c):
    return {'datetime': ts, 'open': o, 'high': h, 'low': l, 'close': c}


def test_detect_bullish_sweep():
    candles = [
        make_candle('t0',2.0,2.2,1.9,2.1),
        make_candle('t1',2.1,2.15,1.7,2.12), # dip below level 1.8
        make_candle('t2',2.12,2.2,2.0,2.18), # reclaim
    ]
    res = detect_sweep_for_level(1.8, candles, lookahead=3)
    assert res is not None
    assert res['sweep_direction'] == 'bullish'
    assert res['reclaim'] == True

def test_no_sweep():
    candles = [make_candle('t0',2,2.1,1.9,2.05), make_candle('t1',2.05,2.1,2.0,2.08)]
    res = detect_sweep_for_level(1.5, candles)
    assert res is None
