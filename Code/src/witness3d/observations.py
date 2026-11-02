from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Observation:
    id: str
    camera_id: str
    uv: tuple[float, float]
    pixel_radius: tuple[float, float]
    depth: float
    half_width: float
    confidence: float = 1.0
    visible: bool = True
    depth_convention: str = "optical_z"

    def __post_init__(self) -> None:
        object.__setattr__(self, "uv", tuple(float(v) for v in self.uv))
        object.__setattr__(self, "pixel_radius", tuple(float(v) for v in self.pixel_radius))
        if not self.id or not self.camera_id:
            raise ValueError("Observation and camera IDs must be nonempty")
        if len(self.uv) != 2 or len(self.pixel_radius) != 2:
            raise ValueError("Pixel values must have two axes")
        values = (*self.uv, *self.pixel_radius, self.depth, self.half_width, self.confidence)
        if not all(isfinite(v) for v in values):
            raise ValueError("Observation contains nonfinite values")
        if any(v < 0 for v in self.pixel_radius) or self.half_width <= 0:
            raise ValueError("Nonnegative pixel radius and positive depth width required")
        if self.depth - self.half_width <= 0 or not 0 <= self.confidence <= 1:
            raise ValueError("Depth interval must be positive; confidence must lie in [0,1]")
        if self.depth_convention != "optical_z":
            raise ValueError("Convert to metric optical-axis depth before constraint construction")


@dataclass(frozen=True)
class Track:
    id: str
    observations: tuple[Observation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", tuple(self.observations))
        if not self.id:
            raise ValueError("Track ID must be nonempty")
        if len(self.observations) < 2:
            raise ValueError("At least two views per track required")
        ids = [o.id for o in self.observations]
        cameras = [o.camera_id for o in self.observations]
        if len(set(ids)) != len(ids) or len(set(cameras)) != len(cameras):
            raise ValueError("Duplicate observation or camera in track")

