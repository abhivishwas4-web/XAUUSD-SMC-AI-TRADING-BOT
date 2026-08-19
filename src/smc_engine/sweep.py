"""Liquidity sweep detection

Detect basic sweeps: a sweep is a wick that takes out a liquidity level then price rejects and reclaims.
"""
from typing import List, Dict, Any, Optional


def detect_sweep_for_level(level_price: float, candles: List[Dict[str, Any]], lookahead: int = 5, tolerance: float = 0.0) -> Optional[Dict[str, Any]]:
    """Scan candles to find a sweep of the given level.

    Simple heuristic:
    - Find index i where candle wick breaches level (high > level_price + tol for buy-side sweep or low < level_price - tol for sell-side)
    - Within next `lookahead` candles, check for rejection (close back inside the range)
    - Return sweep details
    """
    n = len(candles)
    for i in range(n):
        c = candles[i]
        h = float(c['high'])
        l = float(c['low'])
        o = float(c['open'])
        cl = float(c['close'])
        # bullish sweep (take buy-side liquidity) occurs when low < level (price dipped below) then reclaimed
        if l < level_price - tolerance:
            # check subsequent candles for reclaim above level
            reclaim = False
            end_idx = min(n, i + lookahead + 1)
            for j in range(i + 1, end_idx):
                if float(candles[j]['close']) > level_price:
                    reclaim = True
                    break
            return {
                'liquidity_level': level_price,
                'sweep_index': i,
                'sweep_timestamp': c['datetime'],
                'sweep_direction': 'bullish',
                'reclaim': reclaim,
                'confirmation': reclaim
            }
        # bearish sweep (take sell-side liquidity)
        if h > level_price + tolerance:
            reclaim = False
            end_idx = min(n, i + lookahead + 1)
            for j in range(i + 1, end_idx):
                if float(candles[j]['close']) < level_price:
                    reclaim = True
                    break
            return {
                'liquidity_level': level_price,
                'sweep_index': i,
                'sweep_timestamp': c['datetime'],
                'sweep_direction': 'bearish',
                'reclaim': reclaim,
                'confirmation': reclaim
            }
    return None
