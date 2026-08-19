import pytest
from src.smc_engine.displacement import compute_simple_atr, detect_displacement


def make_candle(o,h,l,c,ts='t'):
    return {'datetime':ts,'open':o,'high':h,'low':l,'close':c}

def test_compute_atr_and_displacement():
    candles = []
    for i in range(20):
        candles.append(make_candle(1+i*0.1,1+i*0.1+0.2,1+i*0.1-0.2,1+i*0.1+0.1, ts=f't{i}'))
    atr = compute_simple_atr(candles, period=14)
    assert atr > 0
    # create a big displacement candle
    candles.append(make_candle(3.0,4.5,2.9,4.4, ts='big'))
    events = detect_displacement(candles, atr_multiplier=1.0, lookback=5)
    assert any(e['timestamp']=='big' for e in events)
