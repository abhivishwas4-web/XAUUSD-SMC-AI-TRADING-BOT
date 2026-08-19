"""Risk/Reward and position sizing utilities
"""
from typing import Dict, Any, Optional


def compute_rr(entry_price: float, stop_loss: float, take_profit: float) -> Dict[str, Any]:
    try:
        entry = float(entry_price)
        sl = float(stop_loss)
        tp = float(take_profit)
    except Exception:
        return {'valid': False, 'reason': 'INVALID_PRICE_VALUES'}

    risk = abs(entry - sl)
    reward = abs(tp - entry)
    if risk == 0:
        return {'valid': False, 'reason': 'ZERO_RISK'}
    rr = reward / risk
    return {'valid': True, 'risk': risk, 'reward': reward, 'rr': rr}


def position_size(account_balance: float, risk_percent: float, entry_price: float, stop_loss: float) -> Dict[str, Any]:
    try:
        bal = float(account_balance)
        rp = float(risk_percent)
        entry = float(entry_price)
        sl = float(stop_loss)
    except Exception:
        return {'valid': False, 'reason': 'INVALID_INPUTS'}
    if bal <= 0 or rp <= 0:
        return {'valid': False, 'reason': 'INVALID_ACCOUNT_OR_RISK'}
    risk_amount = bal * (rp / 100.0)
    risk_per_unit = abs(entry - sl)
    if risk_per_unit == 0:
        return {'valid': False, 'reason': 'ZERO_PRICE_RISK'}
    size = risk_amount / risk_per_unit
    return {'valid': True, 'position_size': size, 'risk_amount': risk_amount}
