"""Adversarial validation: truth is confined to these fixtures and assertions."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
from types import SimpleNamespace

import numpy as np
import pytest

from witness3d.constraints import track_polytope
from witness3d.envelopes import depth_envelope
from witness3d.exact import Box, Polytope, RowTag
from witness3d.geometry import Camera
from witness3d.io import plain
from witness3d.observations import Observation, Track
from witness3d.repair import RepairConfig, local_repair
from witness3d.solver import SolverConfig, Status, solve, support_upper
from witness3d.verify import check_artifact, check_envelope, contradiction, feasible_point


def poly(rows, bounds, box=None):
    return Polytope(tuple(map(tuple, rows)), tuple(bounds),
                    tuple(RowTag('test', str(i), 'c', 'test') for i in range(len(rows))),
                    box or Box((-10, -10, -10), (10, 10, 10)))


@pytest.mark.parametrize('gap', [Q(1, 10**6), Q(1, 10**10), Q(1, 10**14), Q(1, 10**20)])
def test_subtolerance_contradiction_never_accepted_as_feasible(gap):
    p = poly([[1, 0, 0], [-1, 0, 0]], [0, -gap])
    assert contradiction(p, [1, 1]).accepted
    decision = solve(p, SolverConfig(proposal_tolerance=1e-6))
    assert decision.status != Status.FEASIBLE
    if decision.artifact(p):
        assert check_artifact(decision.artifact(p)).accepted


@pytest.mark.parametrize('slack', [Q(0), Q(1, 10**12), Q(1, 10**20)])
def test_touching_and_nearly_feasible_not_false_contradictions(slack):
    p = poly([[1, 0, 0], [-1, 0, 0]], [slack, 0])
    assert feasible_point(p, [0, 0, 0]).accepted
    assert not contradiction(p, [1, 1]).accepted
    assert solve(p).status != Status.CONTRADICTION


@pytest.mark.parametrize('y', [[-1, 1], [1], [1, 1, 1], [float('nan'), 1], [float('inf'), 1]])
def test_invalid_certificate_multipliers_rejected(y):
    p = poly([[1, 0, 0], [-1, 0, 0]], [0, -1])
    assert not contradiction(p, y).accepted


def test_certificate_boundary_and_row_tampering():
    p = poly([[1, 0, 0], [-1, 0, 0]], [0, -1])
    artifact = {'system': p.to_dict(), 'certificate': {'kind': 'contradiction', 'y': ['1', '1']}}
    assert check_artifact(artifact).accepted
    artifact['system']['b'][1] = '0'
    assert not check_artifact(artifact).accepted  # zero margin is insufficient


def test_empty_and_domain_only_regions():
    impossible = poly([[0, 0, 0]], [-1])
    assert solve(impossible).status == Status.CONTRADICTION
    domain_only = poly([], [])
    assert solve(domain_only).status == Status.FEASIBLE
    assert support_upper(domain_only, [1, 0, 0]).bound == 10


@pytest.mark.parametrize('end', [float('inf'), -float('inf'), float('nan')])
def test_unbounded_domain_explicitly_rejected(end):
    with pytest.raises(ValueError):
        Box((-1, -1, -1), (end, 1, 1))


def test_arbitrarily_small_dual_residual_is_not_zero():
    epsilon = Q(1, 10**30)
    p = poly([[epsilon, 0, 0]], [-1], Box((-2*10**30, -1, -1), (0, 1, 1)))
    assert p.contains([-10**30, 0, 0])
    assert not contradiction(p, [1]).accepted


def test_solver_failure_keeps_domain_fallback(track, cameras, box, monkeypatch):
    monkeypatch.setattr('witness3d.solver.linprog', lambda *a, **k: SimpleNamespace(status=4, x=None))
    env = depth_envelope(track, 0, cameras, box, q=1)
    assert env.unknown == env.hypotheses and env.excluded == 0
    assert env.lower <= 2 <= env.upper
    assert check_envelope(plain(env)).accepted


@pytest.mark.parametrize('mutation', ['duplicate', 'query', 'domain', 'negative_multiplier'])
def test_complete_envelope_tampering_rejected(track, cameras, box, mutation):
    payload = plain(depth_envelope(track, 0, cameras, box, q=1))
    assert check_envelope(payload).accepted
    if mutation == 'duplicate':
        payload['evidence'][1] = deepcopy(payload['evidence'][0])
    elif mutation == 'query':
        payload['query'] = ['1', '0', '0']
    elif mutation == 'domain':
        payload['evidence'][0]['upper']['system']['box']['upper'][2] = '21'
    else:
        payload['evidence'][0]['upper']['certificate']['y'][0] = '-1'
    assert not check_envelope(payload).accepted


def analytic_pair(aux_u=270., supplied_baseline=1., radius=.001):
    K = np.array([[100., 0, 320.], [0, 100., 240.], [0, 0, 1.]])
    cams = {str(i): Camera(str(i), K, np.eye(3), [-i*supplied_baseline, 0, 0], 640, 480) for i in range(2)}
    track = Track('pair', (Observation('a', '0', (320, 240), (radius, radius), 2, .01),
                           Observation('b', '1', (aux_u, 240), (radius, radius), 2, .01)))
    return track, cams, Box((-2, -2, .1), (2, 2, 10))


@pytest.mark.parametrize('case', ['wrong_budget', 'wrong_baseline', 'undersized_pixel_box'])
def test_violated_premises_can_damage_correct_depth(case):
    track, cams, box = analytic_pair(aux_u=295. if case == 'wrong_budget' else
                                     (272. if case == 'undersized_pixel_box' else 270.),
                                     supplied_baseline=2. if case == 'wrong_baseline' else 1.)
    result = local_repair(track, cams, box, RepairConfig(localize=False))
    assert result.edits
    assert result.repaired.observations[0].depth > 2.05
    assert all(check_envelope(plain(e)).accepted for e in result.envelopes.values())
    if case == 'wrong_budget':
        safe = local_repair(track, cams, box, RepairConfig(q=1, localize=False))
        assert not safe.edits  # deleting all auxiliaries removes this false refutation


def test_zero_baseline_has_wide_depth_envelope():
    track, cams, box = analytic_pair(aux_u=320., supplied_baseline=0.)
    envelope = depth_envelope(track, 0, cams, box)
    assert envelope.upper - envelope.lower > 9
    assert not local_repair(track, cams, box).edits


@pytest.mark.parametrize('rotation', [np.diag([1., 1., -1.]), np.diag([2., 1., 1.]), np.full((3, 3), np.nan)])
def test_invalid_camera_pose_rejected(rotation):
    with pytest.raises(ValueError):
        Camera('x', np.diag([100., 100., 1.]), rotation, [0, 0, 0], 640, 480)


def test_invalid_correspondence_tracks_and_visibility(track, cameras, box):
    with pytest.raises(ValueError):
        Track('bad', (track.observations[0], track.observations[0]))
    with pytest.raises(ValueError):
        track_polytope(Track('bad', (replace(track.observations[0], visible=False), track.observations[1])), cameras, box)
    with pytest.raises(ValueError):
        track_polytope(Track('bad', (replace(track.observations[0], uv=(-1, 0)), track.observations[1])), cameras, box)


def test_joint_inconsistency_despite_individually_plausible_depths():
    # Along X=(0,0,s): camera depths are (s, .6s+1), s in [1,2].
    K = np.array([[100., 0, 320.], [0, 100., 240.], [0, 0, 1.]])
    rotation = np.array([[.6, 0, -.8], [0, 1, 0], [.8, 0, .6]])
    cams = {'0': Camera('0', K, np.eye(3), [0, 0, 0], 640, 480),
            '1': Camera('1', K, rotation, [0, 0, 1], 640, 480)}
    track = Track('coupled', (Observation('a', '0', (320, 240), (100, 100), 2., .001),
                              Observation('b', '1', (270, 240), (100, 100), 1.6, .001)))
    box = Box((0, 0, 1), (0, 0, 2))
    for i in range(2):
        env = depth_envelope(track, i, cams, box)
        assert env.lower <= Q(track.observations[i].depth) <= env.upper
    assert solve(track_polytope(track, cams, box)).status == Status.CONTRADICTION
    assert not local_repair(track, cams, box, RepairConfig(localize=False)).edits


@pytest.mark.parametrize('q', [0, 1, 2])
def test_all_valid_budget_envelopes_contain_truth(track, cameras, box, q):
    for target in range(3):
        env = depth_envelope(track, target, cameras, box, q=q)
        assert env.lower <= 2 <= env.upper
        assert check_envelope(plain(env)).accepted


def test_ground_truth_not_available_to_inference(tmp_path, monkeypatch):
    from witness3d.experiments import run_inputs
    from witness3d.synthetic import SyntheticConfig, generate
    inputs, truth = generate(SyntheticConfig(tracks=2, depth_bias=1.5))
    class Poison:
        def __getattribute__(self, name):
            raise AssertionError('Truth accessed by inference')
    monkeypatch.setattr('witness3d.experiments.Truth', Poison)
    del truth
    records = run_inputs(inputs, {'methods': ['local_all', 'triangulation', 'global']}, str(tmp_path))
    assert len(records) == 6


def test_invalid_after_depth_counts_as_damage():
    from witness3d.metrics import repair_metrics
    result = repair_metrics([1., 1., 2.], [float('nan'), -1., 1.], [1., 1., 1.])
    assert result['damaged_fraction'] == 1.
    assert result['corrected_fraction'] == 1.
    assert result['absolute_error_increased_fraction'] == pytest.approx(2/3)


def test_failed_baseline_does_not_report_rejected_point(tmp_path, monkeypatch):
    from witness3d.baselines import PointEstimate
    from witness3d.experiments import run_inputs
    from witness3d.synthetic import SyntheticConfig, generate
    inputs, _ = generate(SyntheticConfig(tracks=1))
    monkeypatch.setattr('witness3d.baselines.linear_triangulation',
                        lambda *a, **k: PointEstimate(np.array([0., 0., -1.]), 'NUMERICAL_ESTIMATE'))
    record = run_inputs(inputs, {'methods': ['triangulation']}, str(tmp_path))[0]
    assert record['state'] == 'FAILED_KEEP_ORIGINAL'
    assert record['depths'] == record['original_depths']
    assert 'point' not in record


def test_track_length_independent_of_camera_count():
    from witness3d.synthetic import SyntheticConfig, generate
    inputs, truth = generate(SyntheticConfig(tracks=3, views=5, track_length=2))
    assert len(inputs.cameras) == 5
    assert all(len(t.observations) == 2 for t in inputs.tracks)
    assert len(truth.depths) == 6
    with pytest.raises(ValueError):
        generate(SyntheticConfig(views=3, track_length=4))


def test_ransac_threshold_is_configurable(tmp_path, monkeypatch):
    from witness3d.baselines import PointEstimate
    from witness3d.experiments import run_inputs
    from witness3d.synthetic import SyntheticConfig, generate
    inputs, _ = generate(SyntheticConfig(tracks=1))
    thresholds = []
    def estimator(*args, **kwargs):
        thresholds.append(kwargs['threshold'])
        return PointEstimate(None, 'NO_CONSENSUS')
    monkeypatch.setattr('witness3d.baselines.ransac_triangulation', estimator)
    run_inputs(inputs, {'methods': ['ransac'], 'ransac_threshold': .75}, str(tmp_path))
    assert thresholds == [.75]
