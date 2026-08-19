import pytest
from src.technical_analysis.regime import classify_regime


def make_candle(c):
    return {'datetime':'t','open':c-0.5,'high':c+0.5,'low':c-1,'close':c}


def test_regime_high_volatility():
    candles = [make_candle(100+i) for i in range(20)]
    # simulate very large ATR
    res = classify_regime(candles, atr_value=10.0, config={'technical':{'regime':{'high_volatility_atr_pct':0.05,'low_volatility_atr_pct':0.001,'trending_consistency':3,'range_price_ratio':0.02}}})
    assert res['regime'] == 'HIGH_VOLATILITY'


def test_regime_low_volatility():
    candles = [make_candle(100) for _ in range(20)]
    res = classify_regime(candles, atr_value=0.01, config={'technical':{'regime':{'high_volatility_atr_pct':0.05,'low_volatility_atr_pct':0.0005,'trending_consistency':3,'range_price_ratio':0.02}}})
    assert res['regime'] == 'LOW_VOLATILITY'


def test_regime_trending():
    candles = [make_candle(100+i) for i in range(10)]
    res = classify_regime(candles, atr_value=0.5, config={'technical':{'regime':{'high_volatility_atr_pct':0.05,'low_volatility_atr_pct':0.0005,'trending_consistency':2,'range_price_ratio':0.02}}})
    assert res['regime'] == 'TRENDING'


def test_regime_ranging():
    # small price range around 100
    candles = [make_candle(100 + ((-1)**i) * 0.5) for i in range(20)]
    res = classify_regime(candles, atr_value=0.3, config={'technical':{'regime':{'high_volatility_atr_pct':0.05,'low_volatility_atr_pct':0.0001,'trending_consistency':5,'range_price_ratio':0.02}}})
    assert res['regime'] in ('RANGING','CHOPPY')
