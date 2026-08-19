"""Fair Value Gap (FVG) detection

Standard three-candle FVG:
- Bullish: candle1.high < candle3.low
- Bearish: candle1.low > candle3.high
"""
from typing import List, Dict, Any


def detect_fvg(candles: List[Dict[str, Any]], min_size: float = 0.1) -> List[Dict[str, Any]]:
    events = []
    n = len(candles)
    if n < 3:
        return events
    for i in range(n - 2):
        c1 = candles[i]
        c2 = candles[i + 1]
        c3 = candles[i + 2]
        c1h = float(c1['high'])
        c1l = float(c1['low'])
        c3h = float(c3['high'])
        c3l = float(c3['low'])
        # bullish
        if c1h < c3l:
            upper = c3l
            lower = c1h
            size = upper - lower
            if size >= min_size:
                events.append({'direction': 'bull', 'lower': lower, 'upper': upper, 'size': size, 'index': i+2, 'timestamp': c3['datetime'], 'mitigated': False})
        # bearish
        if c1l > c3h:
            upper = c1l
            lower = c3h
            size = upper - lower
            if size >= min_size:
                events.append({'direction': 'bear', 'lower': lower, 'upper': upper, 'size': size, 'index': i+2, 'timestamp': c3['datetime'], 'mitigated': False})
    return events
