from dataclasses import replace

import numpy as np

from witness3d.baselines import average_fusion, linear_triangulation, ransac_triangulation, robust_refine
from witness3d.constraints import track_polytope
from witness3d.synthetic import SyntheticConfig, generate


def test_synthetic_reproducibility_and_truth_separation():
    config = SyntheticConfig(tracks=4, seed=17, depth_bias=1.5)
    inputs, truth = generate(config)
    repeat, truth_repeat = generate(config)
    assert inputs.tracks == repeat.tracks
    assert truth.depths == truth_repeat.depths
    assert not hasattr(inputs, "depths") and not hasattr(inputs, "points")


def test_perfect_synthetic_geometry():
    inputs, truth = generate(SyntheticConfig(tracks=4, pixel_radius=.1, depth_bias=1))
    for track in inputs.tracks:
        assert track_polytope(track, inputs.cameras, inputs.box).contains(truth.points[track.id])


def test_analytic_baselines(track, cameras):
    for estimate in (average_fusion(track, cameras), linear_triangulation(track, cameras),
                     robust_refine(track, cameras), ransac_triangulation(track, cameras)):
        assert estimate.point is not None
        np.testing.assert_allclose(estimate.point, [0, 0, 2], atol=1e-6)


def test_degenerate_triangulation_is_flagged():
    inputs, _ = generate(SyntheticConfig(tracks=1, configuration="identical"))
    assert linear_triangulation(inputs.tracks[0], inputs.cameras).point is None

