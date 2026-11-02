"""Diagnostic validity tests, not tests of a proposed new research method."""
import importlib.util
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase3_selectors import select,scores
from phase3_mechanism import generate_candidates,choose
from witness3d.synthetic import generate,SyntheticConfig


def test_equal_case_and_track_budgets():
    eligible=np.array([1,0,1,1,1,1],bool);w=np.array([0,1,1,0,1,0],bool)
    groups=np.array(['a','a','a','b','b','b'])
    for policy in [False,True]:
        m=select(np.arange(6),eligible,groups,w,12,policy)
        assert m.sum()==2 and not (m & ~eligible).any()
        if policy:
            assert m[:3].sum()==m[3:].sum()==1


def test_scores_accept_no_reference_and_are_deterministic():
    inputs,truth=generate(SyntheticConfig(tracks=2))
    a=scores(inputs,11)
    truth.depths.clear();truth.points.clear()
    b=scores(inputs,11)
    for k in a: np.testing.assert_array_equal(a[k],b[k])


def test_zero_budget_and_random_ties():
    e=np.ones(20,bool);g=np.zeros(20);w=np.zeros(20,bool)
    assert not select(np.zeros(20),e,g,w,1).any()
    w[:4]=True
    assert not np.array_equal(select(np.zeros(20),e,g,w,1),select(np.zeros(20),e,g,w,2))


def test_coherent_decoy_is_on_target_ray():
    inputs,target,patch,candidates,truth=generate_candidates(2,'coherent_decoy')
    # Both hypotheses can have consistent geometry; certification supplies no
    # image evidence absent from the conventional photo/geometric baseline.
    result,_=choose(inputs,target,patch,candidates)
    assert result['joint_photo_geometry']['choice']==result['certificate_conflict_filter']['choice']
    assert result['joint_photo_geometry']['state']=='ESTIMATE'


def test_standard_condition_guard_rejects_zero_baseline():
    from phase3_condition_control import usable
    inputs,_=generate(SyntheticConfig(tracks=1,baseline=0.))
    assert not usable(inputs.tracks[0],inputs.cameras,[0,0,3],inputs.box,.5)
    assert not usable(inputs.tracks[0],inputs.cameras,[0,0,100],inputs.box,0.)
