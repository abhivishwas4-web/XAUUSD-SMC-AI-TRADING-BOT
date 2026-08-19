import pytest
from src.market_data.budget_manager import APICreditManager
from datetime import datetime, timedelta


def test_budget_basic():
    bm = APICreditManager(daily_budget=10, safety_reserve=2, per_minute_limit=3)
    assert bm.can_request()
    bm.record_request()
    assert bm.requests_today == 1
    assert bm.estimated_credits_used == 1


def test_budget_safety_reserve():
    bm = APICreditManager(daily_budget=5, safety_reserve=3)
    # remaining = 5 - 0, but safety reserve prevents spending if below reserve
    assert not bm.can_request(cost=3)


def test_per_minute_limit():
    bm = APICreditManager(daily_budget=100, safety_reserve=1, per_minute_limit=2)
    assert bm.can_request()
    bm.record_request()
    assert bm.can_request()
    bm.record_request()
    # third immediately should be blocked
    assert not bm.can_request()
