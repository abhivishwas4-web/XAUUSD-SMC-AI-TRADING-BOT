src/market_data/health_check.py

from typing import Dict


def provider_status_ok(info: Dict) -> bool:
    status = info.get('status')
    return status == 'HEALTHY' or status == 'OK' or status == 'UNKNOWN'
