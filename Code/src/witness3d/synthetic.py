"""Controlled generators. Truth is returned separately from inference inputs."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from .exact import Box
from .geometry import Camera
from .observations import Observation, Track


@dataclass(frozen=True)
class SyntheticConfig:
    seed: int = 0
    tracks: int = 32
    views: int = 3
    track_length: int | None = None
    baseline: float = 0.3
    pixel_sigma: float = 0.0
    pixel_radius: float = 0.5
    bounded_noise: float = 0.0
    depth_relative_width: float = 0.02
    depth_bias: float = 1.0
    biased_fraction: float = 0.3
    outlier_rate: float = 0.0
    pose_translation_sigma: float = 0.0
    pose_rotation_sigma: float = 0.0
    configuration: str = "translated"
    scene: str = "planes"


@dataclass
class Inputs:
    cameras: dict[str, Camera]
    tracks: list[Track]
    box: Box

    def __post_init__(self) -> None:
        if any(key != camera.id for key, camera in self.cameras.items()):
            raise ValueError("Camera dictionary keys must match camera IDs")
        ids = [t.id for t in self.tracks]
        observations = [o.id for t in self.tracks for o in t.observations]
        if len(ids) != len(set(ids)) or len(observations) != len(set(observations)):
            raise ValueError("Track and observation IDs must be globally unique")
        if any(o.camera_id not in self.cameras for t in self.tracks for o in t.observations):
            raise ValueError("Observation references an unknown camera")


@dataclass
class Truth:
    points: dict[str, np.ndarray]
    depths: dict[str, float]
    wrong_claims: dict[str, bool]
    outliers: dict[str, bool]
    pixel_contained: dict[str, bool]


def generate(config: SyntheticConfig = SyntheticConfig()) -> tuple[Inputs, Truth]:
    c = config
    if c.views < 2 or c.tracks < 1 or c.depth_relative_width <= 0 or c.depth_bias <= 0:
        raise ValueError("Invalid synthetic size or depth controls")
    if c.track_length is not None and not 2 <= c.track_length <= c.views:
        raise ValueError("Track length must lie between 2 and views")
    if any(not 0 <= v <= 1 for v in (c.biased_fraction, c.outlier_rate)):
        raise ValueError("Rates must lie in [0,1]")
    if any(v < 0 for v in (c.baseline, c.pixel_sigma, c.pixel_radius, c.bounded_noise,
                           c.pose_translation_sigma, c.pose_rotation_sigma)):
        raise ValueError("Noise/baseline controls must be nonnegative")
    rng = np.random.default_rng(c.seed)
    K = np.array([[300., 0, 319.5], [0, 300., 239.5], [0, 0, 1.]])
    physical, supplied = {}, {}
    for i in range(c.views):
        if c.configuration == "identical":
            center, R = np.zeros(3), np.eye(3)
        elif c.configuration == "pure_rotation":
            center = np.zeros(3)
            R = Rotation.from_rotvec([0, (i - (c.views-1)/2)*0.03, 0]).as_matrix()
        elif c.configuration == "translated":
            center, R = np.array([(i - (c.views-1)/2) * c.baseline, 0., 0.]), np.eye(3)
        else:
            raise ValueError("Unknown trajectory")
        physical[str(i)] = Camera(str(i), K, R, -R @ center, 640, 480)
        perturbed_R = Rotation.from_rotvec(rng.normal(0, c.pose_rotation_sigma, 3)).as_matrix() @ R
        perturbed_center = center + rng.normal(0, c.pose_translation_sigma, 3)
        supplied[str(i)] = Camera(str(i), K, perturbed_R, -perturbed_R @ perturbed_center, 640, 480)
    tracks, points, depths, wrong, outliers, contained = [], {}, {}, {}, {}, {}
    for k in range(c.tracks):
        point = np.array([rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4), rng.uniform(2.5, 5)])
        if c.scene == "planes":
            point[2] = 3.0 if k % 2 == 0 else 4.5
        elif c.scene != "points":
            raise ValueError("Unknown synthetic scene")
        observations = []
        selected_views = (set(rng.choice(list(physical), c.track_length, replace=False))
                          if c.track_length is not None else set(physical))
        for i, camera in physical.items():
            if i not in selected_views:
                continue
            uv, z, valid = camera.project(point)
            if not valid:
                raise ValueError("Synthetic trajectory projects point behind camera")
            observed = uv + rng.normal(0, c.pixel_sigma, 2) + rng.uniform(-c.bounded_noise, c.bounded_noise, 2)
            is_outlier = bool(rng.random() < c.outlier_rate)
            if is_outlier:
                observed = rng.uniform([10, 10], [629, 469])
            if not (0 <= observed[0] < 640 and 0 <= observed[1] < 480):
                raise ValueError("Synthetic noise/baseline moved observation outside image")
            predicted = float(z) * (c.depth_bias if rng.random() < c.biased_fraction else 1)
            width = max(1e-5, predicted * c.depth_relative_width)
            oid = f"{k}:{i}"
            observations.append(Observation(oid, i, tuple(observed), (c.pixel_radius, c.pixel_radius),
                                            predicted, width, 1.0))
            depths[oid] = float(z)
            wrong[oid] = abs(predicted - float(z)) > width
            outliers[oid] = is_outlier
            contained[oid] = bool(np.all(np.abs(observed - uv) <= c.pixel_radius))
        tracks.append(Track(str(k), tuple(observations)))
        points[str(k)] = point
    return Inputs(supplied, tracks, Box((-3, -3, 0.1), (3, 3, 10))), Truth(points, depths, wrong, outliers, contained)

