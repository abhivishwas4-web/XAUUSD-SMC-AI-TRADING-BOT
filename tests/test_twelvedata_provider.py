import pytest
import requests
from types import SimpleNamespace
from unittest.mock import Mock
from src.market_data.providers.twelvedata_provider import TwelveDataProvider
from src.utils.exceptions import DataError, RateLimitError


class DummyCfg(dict):
    pass


def make_provider(monkeypatch, resp_json, status_code=200):
    cfg = {'env': {'TWELVE_DATA_API_KEY': 'DUMMY'}}
    provider = TwelveDataProvider(cfg)

    class DummyResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = str(json_data)

        def json(self):
            return self._json

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(status_code, resp_json)

    monkeypatch.setattr(provider.session, 'get', fake_get)
    return provider


def test_get_current_price_valid(monkeypatch):
    resp = {'price': '1934.55', 'datetime': '2026-08-19T10:00:00Z'}
    p = make_provider(monkeypatch, resp)
    out = p.get_current_price('XAU/USD')
    assert out['price'] == 1934.55
    assert 'timestamp' in out


def test_get_current_price_missing_price(monkeypatch):
    resp = {'datetime': '2026-08-19T10:00:00Z'}
    p = make_provider(monkeypatch, resp)
    with pytest.raises(DataError):
        p.get_current_price('XAU/USD')


def test_get_current_price_invalid_price(monkeypatch):
    resp = {'price': 'N/A', 'datetime': '2026-08-19T10:00:00Z'}
    p = make_provider(monkeypatch, resp)
    with pytest.raises(DataError):
        p.get_current_price('XAU/USD')


def test_get_current_price_429(monkeypatch):
    resp = {'status': 'error', 'message': 'rate limit'}
    p = make_provider(monkeypatch, resp, status_code=429)
    # fake_get returns status_code 429 which triggers RateLimitError
    def fake_get(url, params=None, timeout=None):
        class R:
            status_code = 429
            text = '429'
            def json(self):
                return {'status': 'error', 'message': 'rate limit'}
        return R()
    monkeypatch.setattr(p.session, 'get', fake_get)
    with pytest.raises(RateLimitError):
        p.get_current_price('XAU/USD')


def test_get_candles_valid(monkeypatch):
    # Twelve Data values newest-first
    resp = {'values': [
        {'datetime': '2026-08-19T10:05:00Z', 'open': '1934', 'high': '1935', 'low': '1933', 'close': '1934.5', 'volume': '100'},
        {'datetime': '2026-08-19T10:00:00Z', 'open': '1933', 'high': '1934', 'low': '1932', 'close': '1933.5', 'volume': '120'}
    ]}
    p = make_provider(monkeypatch, resp)
    candles = p.get_candles('XAU/USD', '15M', 2)
    assert isinstance(candles, list)
    assert candles[0]['datetime'].startswith('2026-08-19')
    assert candles[0]['open'] == 1933.0


def test_get_candles_malformed(monkeypatch):
    resp = {'values': [{'open': '1934'}]}
    p = make_provider(monkeypatch, resp)
    with pytest.raises(DataError):
        p.get_candles('XAU/USD', '15M', 1)
