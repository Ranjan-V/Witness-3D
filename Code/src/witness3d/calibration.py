"""Relative inverse-depth calibration using independent image-only geometry.

No reference depth parameter is accepted. Input anchors must be made by the
geometry-only calibration command, and evaluated track IDs must be disjoint.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares


@dataclass(frozen=True)
class InverseCalibration:
    scale: float
    shift: float
    track_ids: tuple[str, ...]
    provenance: str = "image_only_triangulation"

    def __post_init__(self) -> None:
        if not np.isfinite(self.scale) or self.scale <= 0 or not np.isfinite(self.shift):
            raise ValueError("Positive finite inverse scale and finite shift required")
        if self.provenance != "image_only_triangulation":
            raise ValueError("Unsupported calibration provenance")
        object.__setattr__(self, "track_ids", tuple(self.track_ids))

    def apply(self, inverse, evaluation_track_ids=()):
        if set(evaluation_track_ids) & set(self.track_ids):
            raise ValueError("Calibration/evaluation track overlap")
        denominator = self.scale * np.asarray(inverse, float) + self.shift
        result = np.full(denominator.shape, np.nan)
        valid = np.isfinite(denominator) & (denominator > 0)
        result[valid] = 1 / denominator[valid]
        return result


def fit_inverse_calibration(inverse, geometric_optical_depth, track_ids) -> InverseCalibration:
    p, z = np.asarray(inverse, float), np.asarray(geometric_optical_depth, float)
    ids = np.asarray(track_ids, str)
    if p.shape != z.shape or p.ndim != 1 or ids.shape != p.shape:
        raise ValueError("Calibration sample shapes differ")
    valid = np.isfinite(p) & np.isfinite(z) & (z > 0)
    if valid.sum() < 8 or np.ptp(p[valid]) <= 1e-8:
        raise ValueError("Insufficient independent calibration anchors or inverse-depth variation")
    A = np.column_stack((p[valid], np.ones(valid.sum())))
    if np.linalg.matrix_rank(A) != 2:
        raise ValueError("Unidentifiable affine inverse-depth calibration")
    solution = least_squares(lambda v: A @ v - 1/z[valid], [1.0, 0.0],
                             bounds=([1e-12, -np.inf], [np.inf, np.inf]), loss="soft_l1")
    if not solution.success or np.any(A @ solution.x <= 0):
        raise ValueError("Calibration failed or nonpositive fitted inverse depths")
    return InverseCalibration(float(solution.x[0]), float(solution.x[1]), tuple(sorted(set(ids[valid]))))

