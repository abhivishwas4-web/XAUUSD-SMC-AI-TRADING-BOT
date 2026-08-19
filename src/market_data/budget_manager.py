src/market_data/budget_manager.py

from datetime import datetime, timedelta


class APICreditManager:
    def __init__(self, daily_budget: int, safety_reserve: int):
        self.daily_budget = daily_budget
        self.safety_reserve = safety_reserve
        self.requests_today = 0
        self.estimated_credits_used = 0
        self.last_reset = datetime.utcnow().date()

    def reset_if_needed(self):
        if datetime.utcnow().date() != self.last_reset:
            self.requests_today = 0
            self.estimated_credits_used = 0
            self.last_reset = datetime.utcnow().date()

    def can_request(self, cost: int = 1) -> bool:
        self.reset_if_needed()
        remaining = self.daily_budget - self.estimated_credits_used
        return remaining - cost >= self.safety_reserve

    def record_request(self, cost: int = 1):
        self.reset_if_needed()
        self.requests_today += 1
        self.estimated_credits_used += cost
