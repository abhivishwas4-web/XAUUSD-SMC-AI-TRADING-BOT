import pytest
from datetime import datetime
from src.technical_analysis.sessions import get_session


def test_sessions_boundaries():
    cfg = {'session': {'timezone':'UTC','asian':{'start':'00:00','end':'08:00'},'london':{'start':'07:00','end':'15:00'},'newyork':{'start':'12:00','end':'20:00'},'quality':{}}}
    # 07:30 UTC -> London and Asian overlap? Asian ends at 08:00 so 07:30 in Asian and London
    ts = datetime.fromisoformat('2026-01-01T07:30:00')
    res = get_session(ts, cfg)
    assert res['session'] in ('LONDON','ASIAN','LONDON_NEW_YORK_OVERLAP')

def test_newyork_session():
    cfg = {'session': {'timezone':'UTC','asian':{'start':'00:00','end':'08:00'},'london':{'start':'07:00','end':'15:00'},'newyork':{'start':'12:00','end':'20:00'},'quality':{}}}
    ts = datetime.fromisoformat('2026-01-01T13:00:00')
    res = get_session(ts, cfg)
    assert res['session'] == 'NEW_YORK' or res['session']=='LONDON_NEW_YORK_OVERLAP'

def test_outside_session():
    cfg = {'session': {'timezone':'UTC','asian':{'start':'00:00','end':'06:00'},'london':{'start':'07:00','end':'10:00'},'newyork':{'start':'12:00','end':'13:00'},'quality':{}}}
    ts = datetime.fromisoformat('2026-01-01T22:00:00')
    res = get_session(ts, cfg)
    assert res['session'] == 'OUTSIDE_MAJOR_SESSION'
