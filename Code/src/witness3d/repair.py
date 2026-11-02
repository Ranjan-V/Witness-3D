from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Mapping

import numpy as np

from .constraints import track_polytope
from .envelopes import Envelope, depth_envelope
from .exact import Box, rational
from .geometry import Camera
from .observations import Track
from .solver import Decision, SolverConfig, Status, solve
from .witnesses import extract_conflict
from .verify import check_envelope


@dataclass(frozen=True)
class RepairConfig:
    q: int = 0
    z_min: float = 0.01
    max_hypotheses: int = 64
    extraction: str = "dual"
    extraction_queries: int = 128
    localize: bool = True
    save_evidence: bool = True

    def __post_init__(self) -> None:
        if self.q < 0 or self.max_hypotheses < 1 or self.extraction_queries < 1:
            raise ValueError("Invalid outlier or extraction budget")
        if not np.isfinite(self.z_min) or self.z_min <= 0:
            raise ValueError("Positive finite z_min required")
        if self.extraction not in {"dual", "small", "deletion"}:
            raise ValueError("Unsupported extraction method")


@dataclass
class RepairResult:
    original: Track
    repaired: Track
    before: Decision
    after: Decision
    measurement: Decision
    edits: dict[str, dict[str, Any]] = field(default_factory=dict)
    envelopes: dict[str, Envelope] = field(default_factory=dict)
    conflict: dict[str, Any] | None = None
    reason: str = ""


def local_repair(track: Track, cameras: Mapping[str, Camera], box: Box,
                 config: RepairConfig = RepairConfig(), solver: SolverConfig = SolverConfig()) -> RepairResult:
    full = track_polytope(track, cameras, box, config.z_min)
    pixels = track_polytope(track, cameras, box, config.z_min, include_depth=False)
    before, measurement = solve(full, solver), solve(pixels, solver)
    output = RepairResult(track, track, before, before, measurement)
    if before.status != Status.CONTRADICTION:
        output.reason = "No checked full-system contradiction; preserve predictions"
        return output
    if measurement.status == Status.CONTRADICTION and config.q == 0:
        output.reason = "Pixel-only measurement conflict; no individual depth blame"
        return output
    conflict = extract_conflict(full, config.extraction, config.extraction_queries, solver)
    selected = {o.id for o in track.observations}
    if config.localize and conflict is not None:
        selected = conflict.observation_ids(full)
    if conflict is not None:
        subsystem = full.subset(conflict.indices)
        output.conflict = {"rows": list(conflict.indices), "qualification": conflict.qualification,
                           "artifact": conflict.decision.artifact(subsystem),
                           "depth_suspects": sorted(conflict.observation_ids(full))}
    observations = list(track.observations)
    for index, observation in enumerate(track.observations):
        if observation.id not in selected:
            continue
        env = depth_envelope(track, index, cameras, box, config.q, config.z_min,
                             config.max_hypotheses, solver, config.save_evidence)
        output.envelopes[observation.id] = env
        if env.state != "BOUNDED" or env.lower is None or env.upper is None:
            continue
        if config.save_evidence and not check_envelope(asdict(env)).accepted:
            # An independently rejected coverage trace cannot authorize an edit.
            env.state = "TRACE_REJECTED"
            continue
        d, width = rational(observation.depth), rational(observation.half_width)
        if not (d + width < env.lower or d - width > env.upper):
            continue
        try:
            lo, hi = env.outward_floats()
        except (ValueError, OverflowError):
            continue
        corrected = float(np.clip(observation.depth, lo, hi))
        # Fixed interval width cannot be retained for nonpositive lower endpoints.
        if not np.isfinite(corrected) or corrected <= observation.half_width or corrected == observation.depth:
            continue
        observations[index] = replace(observation, depth=corrected)
        output.edits[observation.id] = {"before": observation.depth, "after": corrected,
                                        "decision": "DEPTH_REFUTED",
                                        "conditional_on": "trusted_target_and_q_auxiliary_budget"}
    output.repaired = Track(track.id, tuple(observations))
    rebuilt = track_polytope(output.repaired, cameras, box, config.z_min)
    output.after = solve(rebuilt, solver)
    output.reason = "Scalar edits and joint reconstructed-system status reported separately"
    return output


def apply_sparse_edits(depth_map, proposals: list[tuple[int, int, float]], authorized_mask):
    """Reject every conflicting edit at a pixel; preserve all other array entries."""
    original = np.asarray(depth_map)
    if original.ndim != 2 or original.dtype.kind != "f":
        raise ValueError("A floating HxW depth map is required")
    mask = np.asarray(authorized_mask, dtype=bool)
    if mask.shape != original.shape:
        raise ValueError("Authorized mask shape mismatch")
    grouped: dict[tuple[int, int], set[float]] = {}
    for y, x, value in proposals:
        if not (0 <= y < original.shape[0] and 0 <= x < original.shape[1]) or not mask[y, x]:
            raise ValueError("Proposal outside authorized mask")
        if not np.isfinite(value) or value <= 0:
            raise ValueError("Invalid proposed depth")
        grouped.setdefault((y, x), set()).add(value)
    # Float64 avoids narrowing a certified float64 endpoint on float32 output.
    # Unchanged pixels retain exactly the same numerical values, including NaNs.
    result = original.astype(np.float64, copy=True)
    rejected = []
    for (y, x), values in grouped.items():
        if len(values) != 1:
            rejected.append((y, x))
        else:
            result[y, x] = next(iter(values))
    return result, rejected

