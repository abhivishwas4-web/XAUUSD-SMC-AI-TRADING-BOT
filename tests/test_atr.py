import pytest
from src.technical_analysis.atr import calculate_atr


def make_candle(ts, o, h, l, c):
    return {'datetime': ts, 'open': o, 'high': h, 'low': l, 'close': c}


def test_atr_normal():
    candles = []
    # create 15 candles with small ranges
    for i in range(15):
        candles.append(make_candle(f'2026-01-01T0{i}:00:00Z', 100+i, 101+i, 99+i, 100.5+i))
    res = calculate_atr(candles, period=14)
    assert res.status == 'OK'
    assert res.atr > 0


def test_atr_insufficient():
    candles = [make_candle('t0',1,2,0.9,1.5)]
    res = calculate_atr(candles, period=14)
    assert res.status == 'INSUFFICIENT_DATA'


def test_atr_invalid():
    candles = [{'datetime':'t','open':1,'high':'NaN','low':0.9,'close':1.1}]
    res = calculate_atr(candles, period=14)
    assert res.status == 'INSUFFICIENT_DATA' or res.status == 'INVALID_DATA'
