from datetime import datetime, timedelta
from collections import deque
from typing import Optional
import threading
import logging

logger = logging.getLogger(__name__)


class APICreditManager:
    def __init__(self, daily_budget: int = 700, safety_reserve: int = 100, per_minute_limit: int = 8):
        self.daily_budget = daily_budget
        self.safety_reserve = safety_reserve
        self.per_minute_limit = per_minute_limit

        self.requests_today = 0
        self.estimated_credits_used = 0
        self.last_reset_time = datetime.utcnow().replace(tzinfo=None).date()
        self.cache_hits = 0
        self.cache_misses = 0
        self.rate_limit_errors = 0
        self.last_successful_request = None
        # Queue of request timestamps (seconds) for per-minute limiting
        self._minute_queue = deque()
        self._lock = threading.Lock()

    def reset_if_needed(self):
        today = datetime.utcnow().date()
        if today != self.last_reset_time:
            self.requests_today = 0
            self.estimated_credits_used = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.rate_limit_errors = 0
            self.last_successful_request = None
            self._minute_queue.clear()
            self.last_reset_time = today

    def remaining_budget(self) -> int:
        self.reset_if_needed()
        return max(0, self.daily_budget - self.estimated_credits_used)

    def can_request(self, cost: int = 1) -> bool:
        """Check daily budget and safety reserve and per-minute limit"""
        self.reset_if_needed()
        if self.remaining_budget() - cost < self.safety_reserve:
            return False
        # per-minute
        now = datetime.utcnow().timestamp()
        with self._lock:
            # remove timestamps older than 60 seconds
            while self._minute_queue and self._minute_queue[0] <= now - 60:
                self._minute_queue.popleft()
            if len(self._minute_queue) >= self.per_minute_limit:
                return False
        return True

    def record_request(self, cost: int = 1):
        self.reset_if_needed()
        self.requests_today += 1
        self.estimated_credits_used += cost
        self.last_successful_request = datetime.utcnow().isoformat()
        now = datetime.utcnow().timestamp()
        with self._lock:
            self._minute_queue.append(now)

    def record_cache_hit(self):
        self.reset_if_needed()
        self.cache_hits += 1

    def record_cache_miss(self):
        self.reset_if_needed()
        self.cache_misses += 1

    def record_rate_limit_error(self):
        self.reset_if_needed()
        self.rate_limit_errors += 1

    def status(self) -> dict:
        self.reset_if_needed()
        return {
            'daily_api_budget': self.daily_budget,
            'safety_reserve': self.safety_reserve,
            'requests_today': self.requests_today,
            'estimated_credits_used': self.estimated_credits_used,
            'remaining_budget': self.remaining_budget(),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'rate_limit_errors': self.rate_limit_errors,
            'last_successful_request': self.last_successful_request,
            'last_reset_time': str(self.last_reset_time)
        }
