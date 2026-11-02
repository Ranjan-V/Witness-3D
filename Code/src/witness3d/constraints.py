"""Exact rational assembly from finite pinhole-camera inputs."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from .exact import Box, Polytope, Q, RowTag, rational as q, vector
from .geometry import Camera
from .observations import Observation, Track


def domain_rows(box: Box):
    rows, rhs, tags = [], [], []
    for j in range(3):
        row = [Q(0)] * 3
        row[j] = Q(1)
        rows += [tuple(row), tuple(-v for v in row)]
        rhs += [box.upper[j], -box.lower[j]]
        tags += [RowTag("", "", "", f"domain_upper_{j}"), RowTag("", "", "", f"domain_lower_{j}")]
    return rows, rhs, tags


def observation_rows(camera: Camera, observation: Observation, track_id: str,
                     z_min: float, include_depth: bool):
    if not observation.visible:
        raise ValueError("Invisible observations cannot assert a visible static track")
    u, v = vector(observation.uv)
    eu, ev = vector(observation.pixel_radius)
    if not (0 <= u < camera.width and 0 <= v < camera.height):
        raise ValueError("Observation center outside image")
    fx, fy, cx, cy = map(q, (camera.K[0, 0], camera.K[1, 1], camera.K[0, 2], camera.K[1, 2]))
    lx, hx = (u - eu - cx) / fx, (u + eu - cx) / fx
    ly, hy = (v - ev - cy) / fy, (v + ev - cy) / fy
    r1, r2, r3 = (vector(row) for row in camera.R)
    t1, t2, t3 = vector(camera.t)
    rows = [tuple(a - hx * b for a, b in zip(r1, r3)),
            tuple(-a + lx * b for a, b in zip(r1, r3)),
            tuple(a - hy * b for a, b in zip(r2, r3)),
            tuple(-a + ly * b for a, b in zip(r2, r3)), tuple(-v for v in r3)]
    rhs = [hx * t3 - t1, t1 - lx * t3, hy * t3 - t2, t2 - ly * t3, t3 - q(z_min)]
    kinds = ["pixel_u_upper", "pixel_u_lower", "pixel_v_upper", "pixel_v_lower", "cheirality"]
    if include_depth:
        d, width = q(observation.depth), q(observation.half_width)
        rows += [r3, tuple(-v for v in r3)]
        rhs += [d + width - t3, t3 - d + width]
        kinds += ["depth_upper", "depth_lower"]
    tags = [RowTag(track_id, observation.id, camera.id, kind) for kind in kinds]
    return rows, rhs, tags


def track_polytope(track: Track, cameras: Mapping[str, Camera], box: Box, z_min: float = 0.01,
                   include_depth: bool = True, keep: Sequence[int] | None = None) -> Polytope:
    if q(z_min) <= 0:
        raise ValueError("z_min must be positive")
    rows, rhs, tags = domain_rows(box)
    selected = list(range(len(track.observations))) if keep is None else list(keep)
    if len(set(selected)) != len(selected) or any(i < 0 or i >= len(track.observations) for i in selected):
        raise ValueError("Invalid selected observation indices")
    for i in selected:
        obs = track.observations[i]
        extra, bounds, provenance = observation_rows(cameras[obs.camera_id], obs, track.id, z_min, include_depth)
        rows.extend(extra)
        rhs.extend(bounds)
        tags.extend(provenance)
    return Polytope(tuple(rows), tuple(rhs), tuple(tags), box)

