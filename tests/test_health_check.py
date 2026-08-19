import pytest
from src.market_data.providers.twelvedata_provider import TwelveDataProvider
from src.market_data.cache_manager import JSONCacheManager
from src.market_data.budget_manager import APICreditManager
from src.market_data.health_check import health_check
from unittest.mock import Mock


class DummyProvider(TwelveDataProvider):
    def __init__(self, cfg, healthy=True):
        super().__init__(cfg)
        self._healthy = healthy

    def health_check(self):
        if self._healthy:
            return {'status':'HEALTHY','details':{}}
        return {'status':'ERROR','details':{'error':'unhealthy'}}


def test_health_check_fresh_cache(tmp_path):
    cfg = {'env': {'TWELVE_DATA_API_KEY': 'DUMMY'}, 'symbol': 'XAU/USD', 'timeframes': {'1H':{}}}
    prov = DummyProvider(cfg)
    cm = JSONCacheManager(str(tmp_path))
    candles = [{'datetime':'2026-08-19T10:00:00Z','open':1,'high':2,'low':1,'close':2}]
    cm.save('twelvedata','XAU/USD','1H',candles,ttl_minutes=60)
    bm = APICreditManager(daily_budget=100,safety_reserve=1)
    res = health_check(prov, cm, bm, 'XAU/USD', cfg['timeframes'])
    assert res['status'] == 'HEALTHY'


def test_health_check_stale_cache(tmp_path):
    cfg = {'env': {'TWELVE_DATA_API_KEY': 'DUMMY'}, 'symbol': 'XAU/USD', 'timeframes': {'1H':{}}}
    prov = DummyProvider(cfg)
    cm = JSONCacheManager(str(tmp_path))
    # create stale cache
    cm.save('twelvedata','XAU/USD','1H',[],ttl_minutes=0)
    bm = APICreditManager(daily_budget=0,safety_reserve=0)
    res = health_check(prov, cm, bm, 'XAU/USD', cfg['timeframes'])
    assert res['details']['cache']['status'] in ('STALE','MISS') or res['status'] in ('WARNING','ERROR')
