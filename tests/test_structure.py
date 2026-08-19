import pytest
from src.smc_engine.structure import detect_structure_from_swings


def test_structure_hh_hl():
    swings = [
        {'index':0,'timestamp':'t0','price':100,'type':'low'},
        {'index':1,'timestamp':'t1','price':110,'type':'high'},
        {'index':2,'timestamp':'t2','price':105,'type':'low'},
        {'index':3,'timestamp':'t3','price':115,'type':'high'},
    ]
    events = detect_structure_from_swings(swings)
    # expect HH at index 3
    assert any(e['type']=='HH' for e in events)

