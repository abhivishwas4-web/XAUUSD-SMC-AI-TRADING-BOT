"""Market structure detection (HH/HL/LH/LL, BOS, MSS)

The module operates on swing points produced by swing_points.detect_swings and on candles.
"""
from typing import List, Dict, Any, Optional


def detect_structure_from_swings(swings: List[Dict[str, Any]], price_key: str = 'price') -> List[Dict[str, Any]]:
    """Detect structure events from the sequence of swings.

    Rules (deterministic):
    - Compare successive swing highs to determine HH (higher high) or LH (lower high)
    - Compare successive swing lows for HL/LL
    - BOS (Break of Structure) is detected when price breaks the last confirmed swing high/low by an amount > 0 (strict)

    Returns list of events {type: 'HH'|'HL'|'LH'|'LL'|'BOS', direction: 'bull'|'bear', broken_level, timestamp, index}
    """
    events: List[Dict[str, Any]] = []
    # Build lists of highs and lows in order
    highs = [s for s in swings if s['type'] == 'high']
    lows = [s for s in swings if s['type'] == 'low']

    # Detect HH/LH from highs
    for i in range(1, len(highs)):
        prev = highs[i - 1]
        curr = highs[i]
        if curr[price_key] > prev[price_key]:
            events.append({'type': 'HH', 'direction': 'bull', 'broken_level': prev[price_key], 'timestamp': curr['timestamp'], 'index': curr['index']})
        elif curr[price_key] < prev[price_key]:
            events.append({'type': 'LH', 'direction': 'bear', 'broken_level': prev[price_key], 'timestamp': curr['timestamp'], 'index': curr['index']})

    # Detect HL/LL from lows
    for i in range(1, len(lows)):
        prev = lows[i - 1]
        curr = lows[i]
        if curr[price_key] > prev[price_key]:
            events.append({'type': 'HL', 'direction': 'bull', 'broken_level': prev[price_key], 'timestamp': curr['timestamp'], 'index': curr['index']})
        elif curr[price_key] < prev[price_key]:
            events.append({'type': 'LL', 'direction': 'bear', 'broken_level': prev[price_key], 'timestamp': curr['timestamp'], 'index': curr['index']})

    # Sort events by index/time
    events.sort(key=lambda e: e['index'])
    # Simple BOS detection heuristic: if an event changes direction compared to previous major structure
    bos_events: List[Dict[str, Any]] = []
    last_dir: Optional[str] = None
    for ev in events:
        if last_dir and ev['direction'] != last_dir:
            bos_events.append({'type': 'BOS', 'direction': ev['direction'], 'broken_level': ev['broken_level'], 'timestamp': ev['timestamp'], 'index': ev['index']})
        last_dir = ev['direction']
    events.extend(bos_events)
    events.sort(key=lambda e: e['index'])
    return events
