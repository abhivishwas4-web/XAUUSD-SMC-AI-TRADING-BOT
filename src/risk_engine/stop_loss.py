"""Stop loss engine

Compute stop loss levels based on structural invalidation and optional ATR buffer.
"""
from typing import Dict, Any, Optional


def compute_stop_loss(entry_price: float, direction: str, invalidation_level: float, atr: Optional[float], config: Dict[str, Any]) -> Dict[str, Any]:
    """Compute SL. For LONG, SL is below invalidation_level; for SHORT, above.

    atr buffer may be applied: buffer = atr * multiplier
    """
    if direction not in ('LONG', 'SHORT'):
        return {'valid': False, 'reason': 'INVALID_DIRECTION'}
    try:
        entry_price = float(entry_price)
        invalidation_level = float(invalidation_level)
    except Exception:
        return {'valid': False, 'reason': 'INVALID_PRICE_VALUES'}

    atr_mult = config.get('risk', {}).get('atr_sl_buffer_multiplier', 0.0)
    buffer = (atr * atr_mult) if (atr is not None and atr_mult and atr > 0) else 0.0

    if direction == 'LONG':
        sl = invalidation_level - buffer
        if sl >= entry_price:
            return {'valid': False, 'reason': 'SL_NOT_BELOW_ENTRY', 'stop_loss': sl}
        return {'valid': True, 'stop_loss': sl, 'invalidation_level': invalidation_level, 'buffer': buffer, 'distance': entry_price - sl}
    else:
        sl = invalidation_level + buffer
        if sl <= entry_price:
            return {'valid': False, 'reason': 'SL_NOT_ABOVE_ENTRY', 'stop_loss': sl}
        return {'valid': True, 'stop_loss': sl, 'invalidation_level': invalidation_level, 'buffer': buffer, 'distance': sl - entry_price}
