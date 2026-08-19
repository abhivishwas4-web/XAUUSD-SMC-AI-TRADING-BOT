import pytest
from src.orchestrator.analysis_orchestrator import AnalysisOrchestrator


def make_candle(ts, o, h, l, c):
    return {'datetime': ts, 'open': o, 'high': h, 'low': l, 'close': c}


def test_orchestrator_bullish_flow(monkeypatch, tmp_path):
    # Setup orchestrator with a test config
    ao = AnalysisOrchestrator()
    cfg = ao.cfg

    # Prepare fake candles for each timeframe
    candles_4h = [make_candle('t0',1900,1910,1890,1905) for _ in range(10)]
    candles_1h = [make_candle('t0',1905,1915,1900,1910) for _ in range(10)]
    candles_15m = [make_candle('t0',1910,1920,1905,1915) for _ in range(20)]
    candles_5m = [make_candle('t0',1915,1925,1910,1920) for _ in range(30)]

    # Monkeypatch provider to return these candles
    class DummyProvider:
        def get_candles(self, symbol, timeframe, output_size):
            if timeframe == '4H':
                return candles_4h
            if timeframe == '1H':
                return candles_1h
            if timeframe == '15M':
                return candles_15m
            if timeframe == '5M':
                return candles_5m
            return []
        def health_check(self):
            return {'status': 'HEALTHY'}
        def get_current_price(self, symbol):
            return {'price': '1920.0', 'datetime': '2026-01-01T00:00:00Z'}

    monkeypatch.setattr(ao, 'provider', DummyProvider())
    # Ensure cache is empty by pointing to tmp dir
    ao.cache = ao.cache.__class__(str(tmp_path))
    ao.budget = ao.budget.__class__(daily_budget=1000, safety_reserve=10, per_minute_limit=100)

    res = ao.analyze()
    assert res['data_status'] == 'OK'
    # Expect direction to be LONG or NEUTRAL depending on derived bias
    assert 'action' in res
    assert 'setup_score' in res


def test_orchestrator_budget_protection(monkeypatch, tmp_path):
    ao = AnalysisOrchestrator()
    # monkeypatch provider to not be used
    class DummyProvider:
        def health_check(self):
            return {'status': 'HEALTHY'}
    monkeypatch.setattr(ao, 'provider', DummyProvider())
    ao.cache = ao.cache.__class__(str(tmp_path))
    # budget exhausted
    ao.budget = ao.budget.__class__(daily_budget=0, safety_reserve=0, per_minute_limit=1)

    # Monkeypatch cache.load to always miss to force API request which will be blocked by budget
    def fake_load(symbol, tf):
        return (None, 'miss')
    monkeypatch.setattr(ao.cache, 'load', fake_load)

    res = ao.analyze()
    assert res['data_status'] == 'API BUDGET PROTECTION — ANALYSIS TEMPORARILY LIMITED'


def test_orchestrator_provider_failure(monkeypatch):
    ao = AnalysisOrchestrator()
    class BadProvider:
        def health_check(self):
            return {'status': 'ERROR'}
    monkeypatch.setattr(ao, 'provider', BadProvider())
    res = ao.analyze()
    assert res['data_status'] == 'DATA ERROR — XAUUSD MARKET DATA UNAVAILABLE'
