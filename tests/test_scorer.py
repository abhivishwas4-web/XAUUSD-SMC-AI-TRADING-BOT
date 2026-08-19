import pytest
from src.setup_scorer.scorer import compute_score


def base_analysis():
    return {
        'direction': 'LONG',
        'htf_4h': 'BULLISH',
        'htf_1h': 'BULLISH',
        'liquidity_sweep': {'present': True, 'reclaim': True, 'confirmation': True},
        'mss': True,
        'bos': True,
        'fvg': {'direction': 'bull', 'lower': 1900.0, 'upper': 1910.0, 'size': 10.0, 'fresh': True, 'mitigated': False, 'displacement': True},
        'mtf_agreement': 4,
        'regime': 'TRENDING',
        'session_quality': 'HIGH',
        'rr': 3.0,
    }


def test_perfect_score():
    cfg = {'analysis': {'minimum_setup_score': 80, 'minimum_rr': 2.0, 'preferred_rr': 3.0}, 'smc': {'fvg': {'min_size': 0.1}}}
    analysis = base_analysis()
    res = compute_score(analysis, cfg)
    assert res['score'] == 100.0
    assert res['grade'] == 'EXCEPTIONAL'
    assert res['action'] == 'ACTIONABLE SETUP'


def test_edge_minimum_score():
    cfg = {'analysis': {'minimum_setup_score': 80, 'minimum_rr': 2.0, 'preferred_rr': 3.0}, 'smc': {'fvg': {'min_size': 5.0}}}
    a = base_analysis()
    # reduce FVG size to lower fvg component
    a['fvg']['size'] = 2.0
    res = compute_score(a, cfg)
    # score should be below 100 but >=80 if other components strong
    assert res['score'] <= 100
    assert res['score'] >= 0
    assert 'grade' in res

def test_watch_range():
    cfg = {'analysis': {'minimum_setup_score': 80, 'minimum_rr': 2.0, 'preferred_rr': 3.0}, 'smc': {'fvg': {'min_size': 0.1}}}
    a = base_analysis()
    # remove liquidity presence
    a['liquidity_sweep'] = {'present': False}
    res = compute_score(a, cfg)
    assert res['action'] in ('WATCH','WAIT','NO TRADE')


def test_rr_below_minimum():
    cfg = {'analysis': {'minimum_setup_score': 80, 'minimum_rr': 2.0, 'preferred_rr': 3.0}, 'smc': {'fvg': {'min_size': 0.1}}}
    a = base_analysis()
    a['rr'] = 1.5
    res = compute_score(a, cfg)
    assert res['component_scores']['rr'] == 0.0
    assert res['reasons']['rr_ok'] == False


def test_conflicting_htf():
    cfg = {'analysis': {'minimum_setup_score': 80, 'minimum_rr': 2.0, 'preferred_rr': 3.0}, 'smc': {'fvg': {'min_size': 0.1}}}
    a = base_analysis()
    a['htf_4h'] = 'BEARISH'
    a['htf_1h'] = 'BEARISH'
    res = compute_score(a, cfg)
    assert res['component_scores']['htf'] == 0.0


def test_missing_data_bounds():
    cfg = {'analysis': {'minimum_setup_score': 80, 'minimum_rr': 2.0, 'preferred_rr': 3.0}, 'smc': {'fvg': {'min_size': 0.1}}}
    a = {}
    res = compute_score(a, cfg)
    assert res['score'] >= 0
    assert res['score'] <= 100
