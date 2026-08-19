"""Liquidity detection utilities

Detect PDH/PDL, PWH/PWL, equal highs/lows, major swings classification
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime


def previous_day_high_low(candles: List[Dict[str, Any]]) -> Tuple[float, float]:
    """Return (PDH, PDL) based on date grouping. Assumes candles are oldest->newest."""
    if not candles:
        raise ValueError('Empty candles')
    # Group by date (UTC iso date)
    by_date = {}
    for c in candles:
        dt = c['datetime']
        date = dt.split('T')[0]
        by_date.setdefault(date, []).append(c)
    dates = sorted(by_date.keys())
    if len(dates) < 2:
        # Not enough history for previous day; return today's high/low
        todays = by_date[dates[-1]]
        highs = [float(x['high']) for x in todays]
        lows = [float(x['low']) for x in todays]
        return max(highs), min(lows)
    prev_date = dates[-2]
    prev_candles = by_date[prev_date]
    highs = [float(x['high']) for x in prev_candles]
    lows = [float(x['low']) for x in prev_candles]
    return max(highs), min(lows)


def equal_levels(candles: List[Dict[str, Any]], tolerance: float = 0.001) -> Tuple[List[float], List[float]]:
    """Detect equal highs and lows using tolerance (fractional or absolute?)

    Tolerance interpreted as relative fraction of price if < 1, else absolute value.
    Returns (equal_highs, equal_lows)
    """
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]

    def is_close(a, b):
        if tolerance < 1:
            return abs(a - b) <= a * tolerance
        return abs(a - b) <= tolerance

    eq_highs = []
    eq_lows = []
    # naive O(n^2) detection for Stage 3 deterministic behavior
    n = len(highs)
    for i in range(n):
        for j in range(i + 1, n):
            if is_close(highs[i], highs[j]):
                eq_highs.append((highs[i] + highs[j]) / 2)
            if is_close(lows[i], lows[j]):
                eq_lows.append((lows[i] + lows[j]) / 2)
    return list(sorted(set(eq_highs))), list(sorted(set(eq_lows)))


def classify_liquidity_level(level_price: float, candles: List[Dict[str, Any]], tolerance: float = 0.001) -> str:
    """Classify a level as UNTOUCHED / SWEPT / RECLAIMED based on recent wicks.

    - SWEPT: there exists a candle whose wick completely breaches the level and close moves back across
    - RECLAIMED: breach occurred and subsequent candles close beyond level
    - UNTOUCHED: no breach
    """
    breached = False
    reclaimed = False
    for c in candles:
        h = float(c['high'])
        l = float(c['low'])
        o = float(c['open'])
        cl = float(c['close'])
        # breach if wick crosses level
        if h > level_price and l < level_price:
            breached = True
            # check if close reclaimed above level
            if cl > level_price:
                reclaimed = True
    if reclaimed:
        return 'RECLAIMED'
    if breached:
        return 'SWEPT'
    return 'UNTOUCHED'
