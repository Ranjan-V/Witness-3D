"""Metric definitions mirror Theory/experimental_protocol.md. GT is evaluation-only."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

import numpy as np


def ratio(numerator: float, denominator: float) -> float | None:
    return float(numerator / denominator) if denominator > 0 else None


def depth_metrics(prediction, reference, mask=None) -> dict[str, Any]:
    p, r = np.asarray(prediction, dtype=float), np.asarray(reference, dtype=float)
    if p.shape != r.shape:
        raise ValueError("Depth shape mismatch")
    valid_ref = np.isfinite(r) & (r > 0)
    if mask is not None:
        if np.asarray(mask).shape != r.shape:
            raise ValueError("Mask shape mismatch")
        valid_ref &= np.asarray(mask, dtype=bool)
    valid = valid_ref & np.isfinite(p) & (p > 0)
    out: dict[str, Any] = {"count": int(valid.sum()), "reference_count": int(valid_ref.sum()),
                           "invalid_prediction_fraction": ratio(int((valid_ref & ~valid).sum()), int(valid_ref.sum()))}
    if not valid.any():
        return {**out, "abs_rel": None, "rmse": None, "delta1": None, "delta2": None, "delta3": None}
    p, r = p[valid], r[valid]
    relative = np.maximum(p / r, r / p)
    out.update(abs_rel=float(np.mean(np.abs(p-r)/r)), rmse=float(np.sqrt(np.mean((p-r)**2))))
    out.update({f"delta{i}": float(np.mean(relative < 1.25**i)) for i in (1, 2, 3)})
    return out


def binary_metrics(predicted, labels) -> dict[str, Any]:
    p, y = np.asarray(predicted, dtype=bool), np.asarray(labels, dtype=bool)
    if p.shape != y.shape:
        raise ValueError("Binary-label shape mismatch")
    tp, fp, fn, tn = (int((p & y).sum()), int((p & ~y).sum()),
                      int((~p & y).sum()), int((~p & ~y).sum()))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": ratio(tp, tp+fp), "recall": ratio(tp, tp+fn),
            "false_positive_rate": ratio(fp, fp+tn), "jaccard": ratio(tp, tp+fp+fn)}


def repair_metrics(before, after, reference, authorized=None, tolerance: float = 0.05) -> dict[str, Any]:
    b, a, r = (np.asarray(v, dtype=float) for v in (before, after, reference))
    if not (b.shape == a.shape == r.shape) or tolerance < 0:
        raise ValueError("Repair metric input mismatch")
    valid = np.isfinite(r) & (r > 0) & np.isfinite(b) & (b > 0) & np.isfinite(a) & (a > 0)
    correct_before = valid & (np.abs(b-r) <= tolerance * r)
    correct_after = valid & (np.abs(a-r) <= tolerance * r)
    erroneous = valid & ~correct_before
    changed = a != b
    mask = np.ones(b.shape, dtype=bool) if authorized is None else np.asarray(authorized, dtype=bool)
    if mask.shape != b.shape:
        raise ValueError("Authorized shape mismatch")
    return {"corrected_fraction": ratio(int((erroneous & correct_after).sum()), int(erroneous.sum())),
            "damaged_fraction": ratio(int((correct_before & ~correct_after).sum()), int(correct_before.sum())),
            "changed_fraction": ratio(int(changed.sum()), b.size),
            "outside_mask_change_fraction": ratio(int((changed & ~mask).sum()), int((~mask).sum())),
            "absolute_error_increased_fraction": ratio(int((valid & (np.abs(a-r) > np.abs(b-r)+1e-12)).sum()), int(valid.sum())),
            "mean_change": float(np.mean(np.abs(a-b))) if b.size else None,
            "max_change": float(np.max(np.abs(a-b))) if b.size else None}


def point_metrics(points, reference) -> dict[str, Any]:
    p, r = np.asarray(points, float), np.asarray(reference, float)
    if p.shape != r.shape or p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("Point metric requires matching Nx3 arrays")
    valid = np.isfinite(p).all(axis=1) & np.isfinite(r).all(axis=1)
    return {"count": int(valid.sum()), "mean_point_error": float(np.mean(np.linalg.norm(p[valid]-r[valid], axis=1)))
            if valid.any() else None}


def consistency_metrics(track, cameras, point) -> dict[str, Any]:
    reprojection, depth_residual, invalid = [], [], 0
    for observation in track.observations:
        uv, z, valid = cameras[observation.camera_id].project(point)
        if not valid:
            invalid += 1
            continue
        reprojection.append(np.linalg.norm(uv - observation.uv))
        depth_residual.append(abs(float(z) - observation.depth))
    return {"reprojection_mean_px": float(np.mean(reprojection)) if reprojection else None,
            "depth_inconsistency_m": float(np.mean(depth_residual)) if depth_residual else None,
            "invalid_projection_fraction": ratio(invalid, len(track.observations))}


def witness_metrics(statuses: Sequence[str], certificate_acceptance: Sequence[bool],
                     row_sizes: Sequence[int], known_feasible=None) -> dict[str, Any]:
    statuses = np.asarray(statuses)
    out = {"unknown_fraction": ratio(int((statuses == "UNKNOWN").sum()), len(statuses)),
           "certificate_validity_rate": ratio(sum(certificate_acceptance), len(certificate_acceptance)),
           "mean_witness_rows": float(np.mean(row_sizes)) if row_sizes else None}
    if known_feasible is not None:
        valid = np.asarray(known_feasible, dtype=bool)
        if valid.shape != statuses.shape:
            raise ValueError("Feasibility-label shape mismatch")
        out["incorrect_contradiction_rate"] = ratio(int(((statuses == "VERIFIED_CONTRADICTION") & valid).sum()), int(valid.sum()))
    return out


def macro_scene_aggregate(records: Sequence[dict[str, Any]], metrics: Sequence[str],
                           seed: int = 0, bootstrap: int = 1000) -> dict[str, Any]:
    if bootstrap < 0:
        raise ValueError("Nonnegative bootstrap count required")
    by_scene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_scene[str(record["scene"])].append(record)
    rng = np.random.default_rng(seed)
    out = {"scenes": len(by_scene), "metrics": {}}
    for name in metrics:
        values = []
        for scene in by_scene.values():
            within = [r[name] for r in scene if r.get(name) is not None and np.isfinite(r[name])]
            if within:
                values.append(float(np.mean(within)))
        if not values:
            out["metrics"][name] = {"mean": None, "ci95": None, "scene_count": 0}
            continue
        samples = np.asarray(values)
        ci = None
        if len(samples) >= 2 and bootstrap:
            means = np.mean(rng.choice(samples, (bootstrap, len(samples)), replace=True), axis=1)
            ci = np.quantile(means, [0.025, 0.975]).tolist()
        out["metrics"][name] = {"mean": float(np.mean(samples)), "ci95": ci, "scene_count": len(values)}
    return out


def paired_scene_difference(records: Sequence[dict[str, Any]], first: str, second: str,
                             metric: str, seed: int = 0, bootstrap: int = 1000) -> dict[str, Any]:
    """Bootstrap paired scene differences after averaging each scene's seeds."""
    grouped = defaultdict(lambda: defaultdict(list))
    for record in records:
        value = record.get(metric)
        if record.get("method") in {first, second} and value is not None and np.isfinite(value):
            grouped[str(record["scene"])][record["method"]].append(value)
    differences = np.array([np.mean(values[first])-np.mean(values[second]) for values in grouped.values()
                            if first in values and second in values])
    if not len(differences):
        return {"difference": None, "ci95": None, "paired_scenes": 0}
    rng = np.random.default_rng(seed)
    ci = None
    if len(differences) >= 2 and bootstrap > 0:
        samples = rng.choice(differences, (bootstrap, len(differences)), replace=True).mean(axis=1)
        ci = np.quantile(samples, [.025, .975]).tolist()
    return {"difference": float(differences.mean()), "ci95": ci, "paired_scenes": len(differences),
            "direction": f"{first} minus {second}"}

