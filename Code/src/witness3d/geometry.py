from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


def finite_array(value, shape: tuple[int, ...]) -> Array:
    a = np.array(value, dtype=np.float64, copy=True)
    if a.shape != shape or not np.isfinite(a).all():
        raise ValueError(f"Expected finite array of shape {shape}")
    a.flags.writeable = False
    return a


@dataclass(frozen=True)
class Camera:
    id: str
    K: Array
    R: Array
    t: Array
    width: int
    height: int
    undistorted: bool = True

    def __post_init__(self) -> None:
        for name, shape in (("K", (3, 3)), ("R", (3, 3)), ("t", (3,))):
            object.__setattr__(self, name, finite_array(getattr(self, name), shape))
        if self.width <= 0 or self.height <= 0 or not self.undistorted:
            raise ValueError("Positive image size and undistorted pinhole pixels required")
        if (self.K[0, 0] <= 0 or self.K[1, 1] <= 0 or self.K[0, 1] != 0 or
                self.K[1, 0] != 0 or not np.array_equal(self.K[2], [0, 0, 1])):
            raise ValueError("Core supports positive focal, zero-skew pinhole K only")
        if not np.allclose(self.R @ self.R.T, np.eye(3), atol=1e-6, rtol=0) or not np.isclose(
                np.linalg.det(self.R), 1, atol=1e-6, rtol=0):
            raise ValueError("R must be a proper rotation (within ingestion tolerance)")

    @classmethod
    def from_c2w(cls, id: str, K, pose, width: int, height: int) -> Camera:
        pose = finite_array(pose, (4, 4))
        if not np.array_equal(pose[3], [0, 0, 0, 1]):
            raise ValueError("Invalid homogeneous pose")
        R = pose[:3, :3].T
        return cls(id, K, R, -R @ pose[:3, 3], width, height)

    @property
    def center(self) -> Array:
        return -self.R.T @ self.t

    def camera_points(self, world) -> Array:
        points = np.asarray(world, dtype=np.float64)
        if points.shape[-1] != 3:
            raise ValueError("Expected (...,3) world points")
        return points @ self.R.T + self.t

    def project(self, world, z_min: float = 1e-6) -> tuple[Array, Array, NDArray[np.bool_]]:
        x = self.camera_points(world)
        z = x[..., 2]
        valid = np.isfinite(x).all(axis=-1) & (z >= z_min)
        with np.errstate(divide="ignore", invalid="ignore"):
            uv = (x @ self.K.T)[..., :2] / z[..., None]
        valid &= np.isfinite(uv).all(axis=-1)
        return uv, z, valid

    def normalized(self, uv) -> Array:
        uv = np.asarray(uv, dtype=np.float64)
        if uv.ndim < 1 or uv.shape[-1] != 2 or not np.isfinite(uv).all():
            raise ValueError("Expected finite (...,2) pixel coordinates")
        return (uv - self.K[:2, 2]) / np.array([self.K[0, 0], self.K[1, 1]])

    def backproject(self, uv, depth) -> Array:
        xy = self.normalized(uv)
        depth = np.asarray(depth, dtype=np.float64)
        if not np.isfinite(depth).all() or np.any(depth <= 0):
            raise ValueError("Optical-axis depth must be finite and positive")
        ray = np.concatenate((xy, np.ones(xy.shape[:-1] + (1,))), axis=-1)
        x_cam = ray * depth[..., None]
        return (x_cam - self.t) @ self.R

    def resized(self, width: int, height: int) -> Camera:
        sx, sy = width / self.width, height / self.height
        H = np.array([[sx, 0, (sx - 1) / 2], [0, sy, (sy - 1) / 2], [0, 0, 1]])
        return replace(self, K=H @ self.K, width=width, height=height)


def convert_depth(values, xy, convention: Literal["optical_z", "range", "inverse_z"]) -> Array:
    values = np.asarray(values, dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError("Positive finite depth values required")
    if convention == "optical_z":
        return values.copy()
    if convention == "range":
        return values / np.sqrt(1 + np.sum(np.asarray(xy) ** 2, axis=-1))
    if convention == "inverse_z":
        return 1 / values
    raise ValueError("Unsupported depth convention")


def quaternion_rotation(q, order: str = "xyzw") -> Array:
    from scipy.spatial.transform import Rotation
    q = np.asarray(q, dtype=np.float64)
    if q.shape != (4,) or not np.isfinite(q).all() or np.linalg.norm(q) == 0:
        raise ValueError("Invalid quaternion")
    if order == "wxyz":
        q = q[[1, 2, 3, 0]]
    elif order != "xyzw":
        raise ValueError("Explicit xyzw or wxyz order required")
    return Rotation.from_quat(q).as_matrix()

