"""ATR calculation module

Provides ATR calculation using True Range and simple moving average over period.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ATRResult:
    atr: float
    period: int
    timestamp: str
    status: str


def compute_true_range(prev_close: float, high: float, low: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def calculate_atr(candles: List[Dict[str, Any]], period: int = 14) -> ATRResult:
    """Calculate ATR over the provided candles (oldest->newest).

    Returns ATRResult with status 'OK' or 'INSUFFICIENT_DATA' or 'INVALID_DATA'.
    """
    if not candles or len(candles) < 2:
        return ATRResult(atr=0.0, period=period, timestamp=datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(), status='INSUFFICIENT_DATA')

    # Validate OHLC
    tr_values: List[float] = []
    prev_close = None
    for idx, c in enumerate(candles):
        try:
            h = float(c['high'])
            l = float(c['low'])
            cl = float(c['close'])
        except Exception:
            return ATRResult(atr=0.0, period=period, timestamp=datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(), status='INVALID_DATA')
        if idx == 0:
            prev_close = cl
            continue
        tr = compute_true_range(prev_close, h, l)
        tr_values.append(tr)
        prev_close = cl

    if len(tr_values) < 1:
        return ATRResult(atr=0.0, period=period, timestamp=datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(), status='INSUFFICIENT_DATA')

    # Use simple moving average of last `period` TR values (or all available if less)
    used = tr_values[-period:]
    atr = sum(used) / len(used)
    ts = candles[-1].get('datetime') or datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    return ATRResult(atr=atr, period=len(used), timestamp=ts, status='OK')
