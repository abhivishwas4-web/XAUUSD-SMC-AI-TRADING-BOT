"""Market regime classification based on ATR, price behavior and structure

Returns a deterministic single regime string and reasoning.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


def classify_regime(candles: List[Dict[str, Any]], atr_value: float, config: Dict[str, Any], structure_events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Return regime classification dict:
    - regime: one of TRENDING, RANGING, CHOPPY, HIGH_VOLATILITY, LOW_VOLATILITY, TRANSITION
    - reason: textual reason
    - atr: atr_value
    - timestamp
    """
    out = {'regime': 'TRANSITION', 'reason': '', 'atr': atr_value, 'timestamp': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()}

    if not candles or atr_value is None:
        out['regime'] = 'TRANSITION'
        out['reason'] = 'Insufficient data'
        return out

    # Determine average price for ATR relative threshold
    closes = []
    for c in candles[-20:]:
        try:
            closes.append(float(c['close']))
        except Exception:
            continue
    if not closes:
        out['regime'] = 'TRANSITION'
        out['reason'] = 'No valid closes'
        return out
    avg_price = sum(closes) / len(closes)
    atr_pct = atr_value / avg_price if avg_price > 0 else 0.0

    thresholds = config.get('technical', {}).get('regime', {})
    high_vol = thresholds.get('high_volatility_atr_pct', 0.008)
    low_vol = thresholds.get('low_volatility_atr_pct', 0.002)

    # High volatility
    if atr_pct >= high_vol:
        out['regime'] = 'HIGH_VOLATILITY'
        out['reason'] = f'ATR_pct {atr_pct:.4f} >= high_vol {high_vol}'
        return out

    # Low volatility
    if atr_pct <= low_vol:
        out['regime'] = 'LOW_VOLATILITY'
        out['reason'] = f'ATR_pct {atr_pct:.4f} <= low_vol {low_vol}'
        return out

    # Directional consistency heuristic (using closes)
    recent = closes[-5:]
    up = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i - 1])
    down = sum(1 for i in range(1, len(recent)) if recent[i] < recent[i - 1])
    dir_consistency = abs(up - down)

    trending_threshold = thresholds.get('trending_consistency', 3)

    if dir_consistency >= trending_threshold:
        out['regime'] = 'TRENDING'
        out['reason'] = f'directional consistency up={up} down={down}'
        return out

    # Range vs Chop using ATR and price range
    price_range = max(closes) - min(closes)
    range_threshold = thresholds.get('range_price_ratio', 0.02)  # price_range / avg_price
    if avg_price > 0 and (price_range / avg_price) <= range_threshold:
        out['regime'] = 'RANGING'
        out['reason'] = f'price range ratio {(price_range/avg_price):.4f} <= {range_threshold}'
        return out

    # Default to CHOPPY
    out['regime'] = 'CHOPPY'
    out['reason'] = 'Mixed directional signals and moderate ATR'
    return out
