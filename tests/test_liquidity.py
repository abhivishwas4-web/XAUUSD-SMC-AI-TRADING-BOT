import pytest
from src.smc_engine.liquidity import previous_day_high_low, equal_levels, classify_liquidity_level


def make_candle(ts, o, h, l, c):
    return {'datetime': ts, 'open': o, 'high': h, 'low': l, 'close': c}


def test_previous_day_high_low():
    candles = []
    # day1
    candles += [make_candle('2026-01-01T00:00:00Z',1,2,0.9,1.5), make_candle('2026-01-01T12:00:00Z',1.4,2.1,1.3,1.9)]
    # day2
    candles += [make_candle('2026-01-02T00:00:00Z',1.9,2.5,1.8,2.3), make_candle('2026-01-02T12:00:00Z',2.3,2.6,2.1,2.5)]
    pdh, pdl = previous_day_high_low(candles)
    assert pdh == 2.1
    assert pdl == 1.3


def test_equal_levels_and_classify():
    candles = [make_candle('t1',1,2,0.9,1.5), make_candle('t2',1,2.001,0.91,1.6), make_candle('t3',1,2.002,0.92,1.7)]
    eqh, eql = equal_levels(candles, tolerance=0.002)
    assert len(eqh) >= 1
    lvl = eqh[0]
    cls = classify_liquidity_level(lvl, candles)
    assert cls in ('UNTOUCHED','SWEPT','RECLAIMED')
