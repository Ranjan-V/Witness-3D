"""Prediction-independent, target-preserving auxiliary-outlier hypothesis hulls."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import comb, isfinite
from typing import Any, Mapping

import numpy as np

from .constraints import track_polytope
from .exact import Box, Q, rational, vector
from .geometry import Camera
from .observations import Track
from .solver import SolverConfig, Status, solve, support_upper


@dataclass
class Envelope:
    state: str
    lower: Q | None = None
    upper: Q | None = None
    hypotheses: int = 0
    excluded: int = 0
    unknown: int = 0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    target: int = 0
    views: int = 0
    budget: int = 0
    query: tuple[str, ...] = ()
    offset: str = "0"
    observation_ids: tuple[str, ...] = ()

    def outward_floats(self) -> tuple[float, float]:
        if self.lower is None or self.upper is None or self.lower > self.upper:
            raise ValueError("No usable envelope")
        lo, hi = float(self.lower), float(self.upper)
        if not isfinite(lo) or not isfinite(hi):
            raise ValueError("Envelope cannot be represented finitely")
        if rational(lo) > self.lower:
            lo = float(np.nextafter(lo, -np.inf))
        if rational(hi) < self.upper:
            hi = float(np.nextafter(hi, np.inf))
        if not isfinite(lo) or not isfinite(hi):
            raise ValueError("Outward float endpoints overflowed")
        return lo, hi


def depth_envelope(track: Track, target: int, cameras: Mapping[str, Camera], box: Box,
                   q: int = 0, z_min: float = 0.01, max_hypotheses: int = 64,
                   solver: SolverConfig = SolverConfig(), save_evidence: bool = True) -> Envelope:
    n = len(track.observations)
    if not 0 <= target < n or not 0 <= q <= n - 1 or max_hypotheses < 1:
        raise ValueError("Invalid target, outlier budget or hypothesis cap")
    total = comb(n - 1, q)
    if total > max_hypotheses:
        return Envelope("BUDGET_EXCEEDED", hypotheses=total)
    camera = cameras[track.observations[target].camera_id]
    c, t = vector(camera.R[2]), rational(camera.t[2])
    negative_c = tuple(-v for v in c)
    lower, upper = [], []
    output = Envelope("BOUNDED", hypotheses=total, target=target, views=n, budget=q,
                      query=tuple(str(v) for v in c), offset=str(t),
                      observation_ids=tuple(o.id for o in track.observations))
    auxiliary = [i for i in range(n) if i != target]
    for deleted in combinations(auxiliary, q):
        keep = [i for i in range(n) if i not in deleted]
        system = track_polytope(track, cameras, box, z_min, include_depth=False, keep=keep)
        decision = solve(system, solver)
        record: dict[str, Any] = {"deleted": list(deleted), "status": decision.status.value}
        if decision.status == Status.CONTRADICTION:
            output.excluded += 1
            if save_evidence:
                record["exclusion"] = decision.artifact(system)
                output.evidence.append(record)
            continue
        output.unknown += int(decision.status == Status.UNKNOWN)
        hi = support_upper(system, c, t, solver)
        minus_lo = support_upper(system, negative_c, -t, solver)
        lo_value, hi_value = -minus_lo.bound, hi.bound
        if lo_value > hi_value:
            # Mutually separating support bounds imply emptiness, but keep the
            # hypothesis with a domain-only hull unless an exclusion was exported.
            lo_value = system.box.minimum(c) + t
            hi_value = -system.box.minimum(negative_c) + t
            record["fallback"] = "domain_after_empty_support_range"
            if save_evidence:
                record["domain_system"] = system.to_dict()
        elif save_evidence:
            record["upper"] = hi.artifact(system, c, t)
            record["negative_lower"] = minus_lo.artifact(system, negative_c, -t)
        lower.append(lo_value)
        upper.append(hi_value)
        if save_evidence:
            record["lower"] = str(lo_value)
            record["upper_value"] = str(hi_value)
            output.evidence.append(record)
    if not lower:
        output.state = "MEASUREMENT_CONFLICT"
        return output
    output.lower, output.upper = min(lower), max(upper)
    return output

