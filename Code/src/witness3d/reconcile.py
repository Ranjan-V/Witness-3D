"""Fixed-camera global convex Huber reference, solved approximately by IRLS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import LinearConstraint, minimize
from scipy.sparse import block_diag, csr_matrix

from .constraints import track_polytope
from .exact import Box
from .geometry import Camera
from .observations import Track
from .solver import SolverConfig, Status, solve


@dataclass
class GlobalResult:
    state: str
    points: np.ndarray | None
    depths: dict[str, float]
    objective_history: list[float]
    iterations: int
    reason: str


def huber(residual: np.ndarray, delta: float) -> np.ndarray:
    a = np.abs(residual)
    return np.where(a <= delta, residual**2 / 2, delta * (a - delta / 2))


def reconcile(tracks: Sequence[Track], cameras: Mapping[str, Camera], box: Box,
              edges: Sequence[tuple[int, int, str, float]] = (), delta: float = 1.0,
              ridge: float = 1e-3, spatial: float = 0.0, max_iterations: int = 20,
              tolerance: float = 1e-6, uniform_weights: bool = False,
              solver: SolverConfig = SolverConfig(), z_min: float = 0.01) -> GlobalResult:
    if not tracks or len(tracks) > 128 or delta <= 0 or ridge <= 0 or spatial < 0 or max_iterations < 1:
        raise ValueError("Reference solver requires 1..128 tracks and valid convex controls")
    polytopes = [track_polytope(t, cameras, box, z_min, False) for t in tracks]
    decisions = [solve(p, solver) for p in polytopes]
    if any(d.status != Status.FEASIBLE for d in decisions):
        return GlobalResult("ABSTAINED", None, {}, [], 0, "A pixel polytope lacks a checked feasible point")
    x0 = np.concatenate([np.array(d.point, dtype=float) for d in decisions])
    A = block_diag([p.float_arrays()[0] for p in polytopes], format="csr")
    b = np.concatenate([p.float_arrays()[1] for p in polytopes])
    constraint = LinearConstraint(A.toarray(), -np.inf, b)
    rows, targets, weights = [], [], []
    by_track = [{o.camera_id: o for o in track.observations} for track in tracks]
    for k, track in enumerate(tracks):
        for obs in track.observations:
            camera = cameras[obs.camera_id]
            row = np.zeros(3 * len(tracks))
            row[3*k:3*k+3] = camera.R[2] / obs.half_width
            rows.append(row)
            targets.append((obs.depth - camera.t[2]) / obs.half_width)
            weights.append(1.0 if uniform_weights else obs.confidence)
    M = np.array(rows)
    target, weight = np.array(targets), np.array(weights)
    graph_rows, graph_targets = [], []
    for k, l, camera_id, confidence in edges:
        if not (0 <= k < len(tracks) and 0 <= l < len(tracks)) or confidence < 0:
            raise ValueError("Invalid graph edge")
        if camera_id not in by_track[k] or camera_id not in by_track[l]:
            raise ValueError("Edge requires observations in its shared camera")
        row = np.zeros(3 * len(tracks))
        row[3*k:3*k+3] = cameras[camera_id].R[2]
        row[3*l:3*l+3] -= cameras[camera_id].R[2]
        graph_rows.append(row * np.sqrt(confidence))
        graph_targets.append((by_track[k][camera_id].depth - by_track[l][camera_id].depth) * np.sqrt(confidence))
    G = np.array(graph_rows).reshape(-1, len(x0))
    gt = np.array(graph_targets)

    def objective(x):
        return float(np.dot(weight, huber(M @ x - target, delta)) +
                     ridge / 2 * np.sum((x - x0)**2) + spatial / 2 * np.sum((G @ x - gt)**2))

    x, history = x0.copy(), [objective(x0)]
    state, reason, iteration = "NONCONVERGED", "Iteration cap reached", 0
    for iteration in range(1, max_iterations + 1):
        residual = M @ x - target
        irls = weight * np.minimum(1, delta / np.maximum(np.abs(residual), 1e-15))
        H = (M.T * irls) @ M + ridge * np.eye(len(x)) + spatial * G.T @ G
        linear = M.T @ (irls * target) + ridge * x0 + spatial * G.T @ gt
        result = minimize(lambda v: float(v @ H @ v / 2 - linear @ v), x,
                          jac=lambda v: H @ v - linear, method="SLSQP", constraints=[constraint],
                          options={"maxiter": 200, "ftol": tolerance / 10})
        if not result.success or not np.isfinite(result.x).all():
            state, reason = "FAILED", str(result.message)
            break
        if np.max(A @ result.x - b) > tolerance:
            state, reason = "FAILED", "Numerical pixel constraint violation"
            break
        value = objective(result.x)
        if value > history[-1] + tolerance:
            state, reason = "FAILED", "Nonmonotone numerical IRLS step"
            break
        step = np.linalg.norm(result.x - x)
        x = result.x
        history.append(value)
        if step <= tolerance * (1 + np.linalg.norm(x)):
            state, reason = "CONVERGED_NUMERICALLY", "Step tolerance; no exact optimality certificate"
            break
    points = x.reshape(-1, 3)
    depths = {o.id: float(cameras[o.camera_id].camera_points(points[k])[2])
              for k, track in enumerate(tracks) for o in track.observations}
    return GlobalResult(state, points, depths, history, iteration, reason)

