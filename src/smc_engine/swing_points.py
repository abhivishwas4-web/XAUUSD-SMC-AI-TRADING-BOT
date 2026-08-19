"""SMC engine - swing points detection

Candles expected format: list of dicts ordered oldest->newest with keys:
- datetime (ISO8601 string)
- open, high, low, close (floats)
- volume optional

"""
from typing import List, Dict, Any


def detect_swings(candles: List[Dict[str, Any]], left: int = 2, right: int = 2) -> List[Dict[str, Any]]:
    """Detect swing highs and swing lows.

    Simple deterministic algorithm:
    - A swing high at index i if candle[i].high > all highs in window [i-left, i+right] excluding i
    - A swing low at index i if candle[i].low < all lows in window

    Returns list of swings with fields: index, timestamp, price, type ('high'|'low'), strength (distance)
    """
    swings = []
    n = len(candles)
    if n == 0:
        return swings
    for i in range(n):
        l = max(0, i - left)
        r = min(n - 1, i + right)
        if i - l < left or r - i < right:
            # insufficient neighbors to confirm
            continue
        center = candles[i]
        center_high = float(center['high'])
        center_low = float(center['low'])
        is_high = True
        is_low = True
        max_dist_high = 0.0
        max_dist_low = 0.0
        for j in range(l, r + 1):
            if j == i:
                continue
            c = candles[j]
            h = float(c['high'])
            lo = float(c['low'])
            if center_high <= h:
                is_high = False
            else:
                max_dist_high = max(max_dist_high, center_high - h)
            if center_low >= lo:
                is_low = False
            else:
                max_dist_low = max(max_dist_low, lo - center_low)
        if is_high:
            swings.append({
                'index': i,
                'timestamp': center['datetime'],
                'price': center_high,
                'type': 'high',
                'strength': max_dist_high
            })
        if is_low:
            swings.append({
                'index': i,
                'timestamp': center['datetime'],
                'price': center_low,
                'type': 'low',
                'strength': max_dist_low
            })
    return swings
