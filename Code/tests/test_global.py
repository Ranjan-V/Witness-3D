from dataclasses import replace

import numpy as np

from witness3d.observations import Track
from witness3d.reconcile import huber, reconcile


def test_huber_known_values():
    np.testing.assert_allclose(huber(np.array([0., 1., 3., -3.]), 1), [0, .5, 2.5, 2.5])


def test_global_fixed_pose_solution(track, cameras, box):
    result = reconcile([track], cameras, box, ridge=.001, max_iterations=30)
    assert result.state == "CONVERGED_NUMERICALLY"
    assert all(new <= old+1e-6 for old, new in zip(result.objective_history, result.objective_history[1:]))
    for depth in result.depths.values():
        assert abs(depth-2) < .01


def test_global_abstains_on_impossible_pixel_geometry(track, cameras, box):
    bad = Track(track.id, (track.observations[0], replace(track.observations[1], uv=(600, 400))))
    result = reconcile([bad], cameras, box)
    assert result.state == "ABSTAINED" and result.points is None

