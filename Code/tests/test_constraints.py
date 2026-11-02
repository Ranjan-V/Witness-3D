from dataclasses import replace

import numpy as np
import pytest

from witness3d.constraints import track_polytope
from witness3d.exact import rational
from witness3d.observations import Track


def test_true_analytic_point_satisfies_all_rows(track, cameras, box):
    full = track_polytope(track, cameras, box)
    assert len(full.A) == 7*len(track.observations)+6
    assert full.contains([0, 0, 2])
    pixel = track_polytope(track, cameras, box, include_depth=False)
    assert len(pixel.A) == 5*len(track.observations)+6


def test_bounds_equivalent_to_projection(track, cameras, box):
    p = track_polytope(track, cameras, box, include_depth=False)
    for point in ([0, 0, 2], [5, 0, 2], [0, 0, -1]):
        inside = True
        for observation in track.observations:
            uv, _, positive = cameras[observation.camera_id].project(point, .01)
            inside &= bool(positive and np.all(np.abs(uv-observation.uv) <= observation.pixel_radius))
        assert p.contains(point) == inside


def test_no_silent_depth_convention(track):
    with pytest.raises(ValueError):
        replace(track.observations[0], depth_convention="relative_inverse")


def test_invisible_and_duplicate_rejected(track, cameras, box):
    invisible = replace(track.observations[0], visible=False)
    with pytest.raises(ValueError):
        track_polytope(Track("bad", (invisible, track.observations[1])), cameras, box)
    with pytest.raises(ValueError):
        Track("bad", (track.observations[0], track.observations[0]))


def test_no_zero_cheirality_margin(track, cameras, box):
    with pytest.raises(ValueError):
        track_polytope(track, cameras, box, z_min=0)

