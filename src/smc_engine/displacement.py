"""Displacement detection

Detect meaningful displacement defined as a candle (or series) with body size significantly larger than recent ATR.
"""
from typing import List, Dict, Any


def compute_simple_atr(candles: List[Dict[str, Any]], period: int = 14) -> float:
    if not candles:
        return 0.0
    ranges = []
    for c in candles[-period:]:
        ranges.append(abs(float(c['high']) - float(c['low'])))
    if not ranges:
        return 0.0
    return sum(ranges) / len(ranges)


def detect_displacement(candles: List[Dict[str, Any]], atr_multiplier: float = 1.5, lookback: int = 20) -> List[Dict[str, Any]]:
    """Return list of displacement events where candle body > atr_multiplier * ATR

    Each event contains: direction, index, timestamp, body, range, strength
    """
    events = []
    if len(candles) < 1:
        return events
    atr = compute_simple_atr(candles[:-1], period=min(14, max(1, len(candles)-1))) if len(candles) > 1 else 0.0
    for i in range(max(0, len(candles) - lookback), len(candles)):
        c = candles[i]
        o = float(c['open'])
        cl = float(c['close'])
        h = float(c['high'])
        l = float(c['low'])
        body = abs(cl - o)
        rng = h - l
        direction = 'bull' if cl > o else 'bear'
        threshold = atr_multiplier * (atr if atr > 0 else 0.0001)
        if body >= threshold and body/rng > 0.4:
            events.append({'direction': direction, 'index': i, 'timestamp': c['datetime'], 'body': body, 'range': rng, 'strength': body/threshold})
    return events
