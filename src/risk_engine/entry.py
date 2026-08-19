"""Entry engine for Stage 5

Functions to determine entry zones/prices from SMC signals like FVG and sweep.
"""
from typing import Dict, Any, Optional, Tuple


def determine_entry(setup: Dict[str, Any], market_price: float, config: Dict[str, Any]) -> Dict[str, Any]:
    """Determine an entry price or zone for a given SMC setup.

    setup: {
      'direction': 'LONG'|'SHORT',
      'fvg': {'direction': 'bull'|'bear', 'lower': float, 'upper': float, 'size': float} or None,
      'liquidity_level': float or None,
      'mss_confirmed': bool
    }

    Returns:
      {
        'direction', 'entry_type', 'entry_price' or 'entry_zone', 'valid', 'reason', 'timestamp'
      }
    """
    direction = setup.get('direction')
    fvg = setup.get('fvg')
    tol_cfg = config.get('risk', {}).get('entry_retest_tolerance', {'price_pct': 0.002})
    price_pct = tol_cfg.get('price_pct', 0.002)

    res = {'direction': direction, 'valid': False, 'reason': 'NO_VALID_ENTRY'}

    if direction not in ('LONG', 'SHORT'):
        res.update({'reason': 'INVALID_DIRECTION'})
        return res

    if not fvg:
        res.update({'reason': 'NO_FVG'})
        return res

    # Ensure fvg direction matches setup direction
    if direction == 'LONG' and fvg.get('direction') != 'bull':
        res.update({'reason': 'FVG_DIRECTION_MISMATCH'})
        return res
    if direction == 'SHORT' and fvg.get('direction') != 'bear':
        res.update({'reason': 'FVG_DIRECTION_MISMATCH'})
        return res

    lower = float(fvg['lower'])
    upper = float(fvg['upper'])
    # Define entry zone as the FVG range
    entry_zone = (lower, upper) if lower < upper else (upper, lower)

    # If price is already beyond the zone (moved too far), require retest
    if direction == 'LONG':
        # price should be at or below upper for entry; if above by tolerance -> wait
        tolerance_price = upper * (1 + price_pct)
        if market_price > tolerance_price:
            return {'direction': direction, 'valid': False, 'reason': 'WAIT_FOR_RETEST', 'entry_zone': entry_zone}
        # If price inside zone, valid market entry; prefer conservative entry at lower+ (mid)
        if lower <= market_price <= upper:
            entry_price = market_price
            return {'direction': direction, 'valid': True, 'entry_type': 'MARKET_IN_ZONE', 'entry_price': entry_price, 'entry_zone': entry_zone, 'reason': 'IN_ZONE'}
        # If market price below zone, prefer limit at upper
        if market_price < lower:
            entry_price = upper
            return {'direction': direction, 'valid': True, 'entry_type': 'LIMIT_AT_POI', 'entry_price': entry_price, 'entry_zone': entry_zone, 'reason': 'PRICE_BELOW_ZONE'}
    else:  # SHORT
        tolerance_price = lower * (1 - price_pct)
        if market_price < tolerance_price:
            return {'direction': direction, 'valid': False, 'reason': 'WAIT_FOR_RETEST', 'entry_zone': entry_zone}
        if lower <= market_price <= upper:
            entry_price = market_price
            return {'direction': direction, 'valid': True, 'entry_type': 'MARKET_IN_ZONE', 'entry_price': entry_price, 'entry_zone': entry_zone, 'reason': 'IN_ZONE'}
        if market_price > upper:
            entry_price = lower
            return {'direction': direction, 'valid': True, 'entry_type': 'LIMIT_AT_POI', 'entry_price': entry_price, 'entry_zone': entry_zone, 'reason': 'PRICE_ABOVE_ZONE'}

    return res
