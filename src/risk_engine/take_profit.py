"""Take profit engine

Select logical TP1 and TP2 based on known liquidity targets.
"""
from typing import Dict, Any, List, Optional


def select_tps(entry_price: float, direction: str, liquidity_targets: List[float], config: Dict[str, Any]) -> Dict[str, Any]:
    """Return TP1 and TP2 based on nearest logical liquidity targets in the trade direction.

    liquidity_targets: list of price levels (floats)
    """
    try:
        entry = float(entry_price)
    except Exception:
        return {'valid': False, 'reason': 'INVALID_ENTRY_PRICE'}
    if direction not in ('LONG', 'SHORT'):
        return {'valid': False, 'reason': 'INVALID_DIRECTION'}

    # Filter targets in direction
    if direction == 'LONG':
        candidates = sorted([t for t in liquidity_targets if t > entry])
    else:
        candidates = sorted([t for t in liquidity_targets if t < entry], reverse=True)

    if not candidates:
        return {'valid': False, 'reason': 'NO_VALID_TARGET'}

    tp1 = candidates[0]
    tp2 = candidates[1] if len(candidates) > 1 else None

    return {'valid': True, 'tp1': tp1, 'tp2': tp2, 'candidates': candidates}
