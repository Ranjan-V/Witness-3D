"""Generic original reference baselines; no equivalence to named papers claimed."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from .geometry import Camera
from .observations import Track


@dataclass
class PointEstimate:
    point: np.ndarray | None
    state: str
    inliers: np.ndarray | None = None


def no_repair(track: Track) -> dict[str, float]:
    return {o.id: o.depth for o in track.observations}


def depths_from_point(track: Track, cameras: Mapping[str, Camera], point) -> dict[str, float]:
    return {o.id: float(cameras[o.camera_id].camera_points(point)[2]) for o in track.observations}


def average_fusion(track: Track, cameras: Mapping[str, Camera], uniform: bool = False) -> PointEstimate:
    points = [cameras[o.camera_id].backproject(o.uv, o.depth) for o in track.observations]
    weights = np.array([1 if uniform else o.confidence for o in track.observations])
    if weights.sum() <= 0:
        return PointEstimate(None, "NO_POSITIVE_WEIGHT")
    return PointEstimate(np.average(points, axis=0, weights=weights), "NUMERICAL_ESTIMATE")


def linear_triangulation(track: Track, cameras: Mapping[str, Camera], indices: Sequence[int] | None = None) -> PointEstimate:
    indices = list(range(len(track.observations))) if indices is None else list(indices)
    if len(indices) < 2:
        return PointEstimate(None, "TOO_FEW_VIEWS")
    rows = []
    for i in indices:
        obs = track.observations[i]
        cam = cameras[obs.camera_id]
        x, y = cam.normalized(obs.uv)
        P = np.column_stack((cam.R, cam.t))
        rows.extend([x * P[2] - P[0], y * P[2] - P[1]])
    A = np.array(rows)
    _, singular, vh = np.linalg.svd(A)
    if len(singular) < 3 or singular[-2] < 1e-10 or abs(vh[-1, 3]) < 1e-12:
        return PointEstimate(None, "DEGENERATE")
    point = vh[-1, :3] / vh[-1, 3]
    valid = all(cameras[track.observations[i].camera_id].project(point)[2] for i in indices)
    return PointEstimate(point if valid else None, "NUMERICAL_ESTIMATE" if valid else "BEHIND_CAMERA")


def reprojection_residuals(track: Track, cameras: Mapping[str, Camera], point) -> np.ndarray:
    result = []
    for obs in track.observations:
        uv, _, valid = cameras[obs.camera_id].project(point)
        result.append(float(np.linalg.norm(uv - obs.uv)) if valid else float("inf"))
    return np.array(result)


def residual_threshold(track: Track, cameras: Mapping[str, Camera], threshold: float = 2.0) -> np.ndarray:
    fused = average_fusion(track, cameras)
    if fused.point is None:
        return np.ones(len(track.observations), dtype=bool)
    return reprojection_residuals(track, cameras, fused.point) > threshold


def robust_refine(track: Track, cameras: Mapping[str, Camera], include_depth: bool = False,
                  loss: str = "huber", indices: Sequence[int] | None = None,
                  uniform: bool = False) -> PointEstimate:
    chosen = list(range(len(track.observations))) if indices is None else list(indices)
    initial = linear_triangulation(track, cameras, chosen)
    if initial.point is None:
        initial = average_fusion(track, cameras, uniform)
    if initial.point is None:
        return initial
    if loss not in {"linear", "huber", "soft_l1", "cauchy"}:
        raise ValueError("Unsupported robust loss")

    def residual(point):
        values = []
        for i in chosen:
            obs = track.observations[i]
            camera = cameras[obs.camera_id]
            x = camera.camera_points(point)
            z = max(float(x[2]), 1e-6)
            uv = np.array([camera.K[0, 0] * x[0] / z + camera.K[0, 2],
                           camera.K[1, 1] * x[1] / z + camera.K[1, 2]])
            w = np.sqrt(1 if uniform else obs.confidence)
            radius = np.maximum(obs.pixel_radius, 0.5)
            values.extend(w * (uv - obs.uv) / radius)
            values.append(w * max(0, 0.01 - x[2]) * 1000)
            if include_depth:
                values.append(w * (x[2] - obs.depth) / obs.half_width)
        return np.asarray(values)

    solution = least_squares(residual, initial.point, loss=loss, f_scale=1, max_nfev=200)
    return PointEstimate(solution.x if solution.success else None,
                         "NUMERICALLY_CONVERGED" if solution.success else "FAILED")


def ransac_triangulation(track: Track, cameras: Mapping[str, Camera], seed: int = 0,
                         threshold: float = 2.0, max_trials: int = 64) -> PointEstimate:
    rng = np.random.default_rng(seed)
    pairs = list(combinations(range(len(track.observations)), 2))
    rng.shuffle(pairs)
    best, best_cost = None, float("inf")
    for pair in pairs[:max_trials]:
        estimate = linear_triangulation(track, cameras, pair)
        if estimate.point is None:
            continue
        errors = reprojection_residuals(track, cameras, estimate.point)
        inliers = errors <= threshold
        score = (-int(inliers.sum()), float(np.minimum(errors, threshold).sum()))
        if best is None or score < best_cost:
            best, best_cost = inliers, score
    if best is None or best.sum() < 2:
        return PointEstimate(None, "NO_CONSENSUS")
    output = robust_refine(track, cameras, indices=np.flatnonzero(best).tolist())
    output.inliers = best
    return output


def bundle_adjustment_style(tracks: Sequence[Track], cameras: Mapping[str, Camera],
                             pose_prior: float = 10.0, max_nfev: int = 100):
    """Anchored local point/pose refinement with pose priors, not COLMAP BA.

    Changes camera information; use only as a separately labeled diagnostic.
    """
    if len(cameras) < 2 or not tracks or pose_prior <= 0:
        raise ValueError("BA requires cameras, tracks and a positive pose prior")
    ids = sorted(cameras)
    estimates = [linear_triangulation(t, cameras) for t in tracks]
    if any(e.point is None for e in estimates):
        return {"state": "FAILED_INITIALIZATION", "points": None, "cameras": None}
    points0 = np.array([e.point for e in estimates])
    initial_poses = np.array([np.r_[Rotation.from_matrix(cameras[i].R).as_rotvec(), cameras[i].t]
                             for i in ids[1:]])
    x0 = np.r_[points0.ravel(), initial_poses.ravel()]

    def unpack(x):
        points = x[:3*len(tracks)].reshape(-1, 3)
        pose = x[3*len(tracks):].reshape(-1, 6)
        transforms = {ids[0]: (cameras[ids[0]].R, cameras[ids[0]].t)}
        transforms.update({i: (Rotation.from_rotvec(p[:3]).as_matrix(), p[3:]) for i, p in zip(ids[1:], pose)})
        return points, pose, transforms

    def residual(x):
        points, pose, transforms = unpack(x)
        values = []
        for point, track in zip(points, tracks):
            for obs in track.observations:
                R, t = transforms[obs.camera_id]
                camera = cameras[obs.camera_id]
                xc = R @ point + t
                z = max(float(xc[2]), 1e-6)
                uv = (camera.K @ xc)[:2] / z
                values.extend((uv - obs.uv) / np.maximum(obs.pixel_radius, 0.5))
                values.append(max(0, 0.01 - xc[2]) * 1000)
        values.extend((pose_prior * (pose - initial_poses)).ravel())
        return np.array(values)

    result = least_squares(residual, x0, loss="huber", max_nfev=max_nfev)
    points, _, transforms = unpack(result.x)
    return {"state": "NUMERICALLY_CONVERGED" if result.success else "NONCONVERGED",
            "points": points, "cameras": transforms, "cost": float(result.cost)}

