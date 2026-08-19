from typing import Dict
from datetime import datetime, timezone
from src.utils.logger import get_logger

logger = get_logger(__name__)


def provider_status_ok(info: Dict) -> bool:
    status = info.get('status')
    return status in ('HEALTHY', 'OK')


def health_check(provider, cache_manager, budget_manager, symbol: str, timeframes: Dict[str, dict]) -> Dict:
    """Perform a multi-faceted health check across provider, cache and budget.

    Returns a dict with status and details. Does not expose API keys.
    """
    out = {'provider': 'twelvedata', 'status': 'UNKNOWN', 'details': {}}

    # provider basic check
    try:
        pinfo = provider.health_check()
        out['details']['provider'] = pinfo
    except Exception as e:
        out['status'] = 'ERROR'
        out['details']['error'] = 'Provider health_check failed'
        logger.exception('Provider health_check failed')
        return out

    # budget status
    try:
        out['details']['budget'] = budget_manager.status()
    except Exception:
        out['details']['budget'] = {'error': 'budget status unavailable'}

    # check XAU/USD availability via cache or quick price
    cache_ok = False
    try:
        # check 1H timeframe cache as representative
        tf = '1H' if '1H' in timeframes else list(timeframes.keys())[0]
        data, reason = cache_manager.load(symbol, tf)
        if data and cache_manager.is_fresh(data):
            cache_ok = True
            out['details']['cache'] = {'status': 'FRESH', 'timeframe': tf}
        elif data:
            out['details']['cache'] = {'status': 'STALE', 'timeframe': tf}
        else:
            out['details']['cache'] = {'status': 'MISS', 'timeframe': tf}
    except Exception:
        out['details']['cache'] = {'status': 'ERROR'}

    # determine overall status
    if pinfo.get('status') == 'HEALTHY' and cache_ok and out['details']['budget']['remaining_budget'] > 0:
        out['status'] = 'HEALTHY'
    elif pinfo.get('status') == 'WARNING' or out['details']['budget']['remaining_budget'] <= 0:
        out['status'] = 'WARNING'
    else:
        out['status'] = 'ERROR'

    out['checked_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    return out
