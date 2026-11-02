from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

import numpy as np

from witness3d.envelopes import Envelope, depth_envelope
from witness3d.observations import Track
from witness3d.repair import RepairConfig, apply_sparse_edits, local_repair
from witness3d.solver import Decision, Status
from witness3d.io import plain
from witness3d.verify import check_envelope


def test_prediction_independence(track, cameras, box):
    first = depth_envelope(track, 0, cameras, box)
    changed = Track(track.id, tuple(replace(o, depth=8, half_width=.1) for o in track.observations))
    second = depth_envelope(changed, 0, cameras, box)
    assert first.lower == second.lower and first.upper == second.upper
    assert first.lower <= 2 <= first.upper
    assert check_envelope(plain(first)).accepted


def test_outlier_budget_contains_true_point(track, cameras, box):
    outlier = replace(track.observations[2], uv=(500., 400.))
    corrupted = Track(track.id, (*track.observations[:2], outlier))
    envelope = depth_envelope(corrupted, 0, cameras, box, q=1)
    assert envelope.state == "BOUNDED"
    assert envelope.lower <= 2 <= envelope.upper
    assert envelope.hypotheses == 2
    payload = plain(envelope)
    assert check_envelope(payload).accepted
    payload["evidence"].pop()
    assert not check_envelope(payload).accepted


def test_never_truncate_hypotheses(track, cameras, box):
    with patch("witness3d.envelopes.solve", side_effect=AssertionError("must abstain before solver")):
        result = depth_envelope(track, 0, cameras, box, q=1, max_hypotheses=1)
    assert result.state == "BUDGET_EXCEEDED" and result.lower is None


def test_unknown_hypothesis_not_dropped(track, cameras, box):
    with patch("witness3d.envelopes.solve", return_value=Decision(Status.UNKNOWN)):
        result = depth_envelope(track, 0, cameras, box, q=1)
    assert result.excluded == 0 and result.unknown == result.hypotheses
    assert result.lower <= 2 <= result.upper


def test_outward_rounding():
    env = Envelope("BOUNDED", Fraction(1, 3), Fraction(2, 3))
    lo, hi = env.outward_floats()
    assert Fraction.from_float(lo) <= env.lower
    assert Fraction.from_float(hi) >= env.upper


def test_selective_repair_does_not_damage_known_true_depths(track, cameras, box):
    corrupted = Track(track.id, (replace(track.observations[0], depth=5), *track.observations[1:]))
    result = local_repair(corrupted, cameras, box, RepairConfig(extraction="deletion", extraction_queries=200))
    assert result.before.status == Status.CONTRADICTION
    assert result.edits
    for old, new in zip(corrupted.observations, result.repaired.observations):
        assert abs(new.depth-2) <= abs(old.depth-2)+1e-12
        if old.id not in result.edits:
            assert new == old


def test_sparse_conflicts_and_locality():
    original = np.ones((3, 3), dtype=np.float64)
    mask = np.zeros((3, 3), dtype=bool)
    mask[1, 1] = mask[2, 2] = True
    result, rejected = apply_sparse_edits(original, [(1, 1, 2), (1, 1, 3), (2, 2, 4)], mask)
    assert rejected == [(1, 1)]
    assert result[1, 1] == 1 and result[2, 2] == 4
    np.testing.assert_array_equal(result[~mask], original[~mask])

