import pytest
from src.smc_engine.fvg import detect_fvg


def make_candle(ts, o, h, l, c):
    return {'datetime': ts, 'open': o, 'high': h, 'low': l, 'close': c}


def test_bullish_fvg():
    candles = [
        make_candle('t0',1,1.0,0.9,0.95),
        make_candle('t1',0.95,1.05,0.9,1.0),
        make_candle('t2',1.2,1.3,1.1,1.25),
    ]
    fgvs = detect_fvg(candles, min_size=0.05)
    assert any(f['direction']=='bull' for f in fgvs)

def test_bearish_fvg():
    candles = [
        make_candle('t0',1.3,1.4,1.2,1.25),
        make_candle('t1',1.25,1.35,1.2,1.3),
        make_candle('t2',1.0,1.1,0.9,1.05),
    ]
    fgvs = detect_fvg(candles, min_size=0.05)
    assert any(f['direction']=='bear' for f in fgvs)

def test_invalid_fvg():
    candles = [make_candle('t0',1,1.02,0.98,1.0), make_candle('t1',1,1.03,0.99,1.01), make_candle('t2',1,1.025,0.995,1.02)]
    fgvs = detect_fvg(candles, min_size=0.05)
    assert fgvs == []
