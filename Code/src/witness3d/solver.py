"""Numerical proposals with independent exact acceptance; UNKNOWN is normal."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Any, Sequence

import numpy as np
from scipy.optimize import linprog

from .exact import Polytope, Q, rational, solve_three, vector
from .verify import contradiction, feasible_point, upper_bound


class Status(str, Enum):
    FEASIBLE = "VERIFIED_FEASIBLE"
    CONTRADICTION = "VERIFIED_CONTRADICTION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SolverConfig:
    time_limit: float = 2.0
    proposal_tolerance: float = 1e-8
    recovery_rows: int = 12

    def __post_init__(self) -> None:
        if not np.isfinite(self.time_limit) or self.time_limit <= 0:
            raise ValueError("Positive finite LP time limit required")
        if not 0 < self.proposal_tolerance < 1 or self.recovery_rows < 3:
            raise ValueError("Invalid proposal/recovery controls")


@dataclass
class Decision:
    status: Status
    point: tuple[Q, ...] | None = None
    y: tuple[Q, ...] | None = None
    numerical_status: int | None = None
    reason: str = ""

    def artifact(self, system: Polytope) -> dict[str, Any] | None:
        if self.status == Status.FEASIBLE and self.point is not None:
            cert = {"kind": "point", "point": [str(v) for v in self.point]}
        elif self.status == Status.CONTRADICTION and self.y is not None:
            cert = {"kind": "contradiction", "y": [str(v) for v in self.y]}
        else:
            return None
        return {"schema_version": 1, "system": system.to_dict(), "certificate": cert}


@dataclass
class Support:
    bound: Q
    y: tuple[Q, ...]
    optimized: bool

    def artifact(self, system: Polytope, c: Sequence[Any], t: Any) -> dict[str, Any]:
        return {"schema_version": 1, "system": system.to_dict(),
                "certificate": {"kind": "upper_bound", "c": [str(v) for v in vector(c)],
                                "t": str(rational(t)), "y": [str(v) for v in self.y],
                                "bound": str(self.bound)}}


def _lp(system: Polytope, objective, config: SolverConfig):
    A, b = system.float_arrays()
    # Even when extracting a row subset, the declared domain remains active.
    bounds = [(float(lo), float(hi)) for lo, hi in zip(system.box.lower, system.box.upper)]
    return linprog(objective, A_ub=A if len(A) else None, b_ub=b if len(b) else None,
                   bounds=bounds, method="highs", options=_options(config))


def _options(config: SolverConfig) -> dict[str, float]:
    return {"time_limit": config.time_limit,
            "primal_feasibility_tolerance": max(1e-10, config.proposal_tolerance),
            "dual_feasibility_tolerance": max(1e-10, config.proposal_tolerance)}


def _recover(system: Polytope, point, config: SolverConfig) -> tuple[Q, ...] | None:
    if point is None or not np.isfinite(point).all():
        return None
    candidate = vector(point)
    if feasible_point(system, candidate).accepted:
        return candidate
    A, b = system.float_arrays()
    # Include box faces even if the extraction subset contains no domain rows.
    rows, rhs = list(system.A), list(system.b)
    for j in range(3):
        e = tuple(Q(int(k == j)) for k in range(3))
        rows += [e, tuple(-v for v in e)]
        rhs += [system.box.upper[j], -system.box.lower[j]]
    af = np.array(rows, dtype=float).reshape(-1, 3)
    bf = np.array(rhs, dtype=float)
    scale = np.maximum(np.linalg.norm(af, axis=1), 1e-30)
    order = np.argsort(np.abs(af @ point - bf) / scale)[:config.recovery_rows]
    for indices in combinations(order.tolist(), 3):
        x = solve_three([rows[i] for i in indices], [rhs[i] for i in indices])
        if x is not None and feasible_point(system, x).accepted:
            return x
    return None


def solve(system: Polytope, config: SolverConfig = SolverConfig()) -> Decision:
    numerical_status = None
    try:
        proposed = _lp(system, np.zeros(3), config)
        numerical_status = int(proposed.status)
        point = _recover(system, getattr(proposed, "x", None), config)
        if point is not None:
            return Decision(Status.FEASIBLE, point=point, numerical_status=numerical_status)
    except (ValueError, RuntimeError, FloatingPointError, OverflowError):
        pass
    # Separate normalized alternative proposal; do not trust solver status=2.
    try:
        A, b = system.float_arrays()
        # Add implicit box faces to the proposal, then fold their contribution into
        # residual-aware checking by retaining only the original row multipliers.
        extra_A, extra_b = [], []
        for j in range(3):
            e = np.eye(3)[j]
            extra_A.extend([e, -e])
            extra_b.extend([float(system.box.upper[j]), -float(system.box.lower[j])])
        aa = np.vstack((A, extra_A))
        bb = np.concatenate((b, extra_b))
        equality = np.vstack((aa.T, np.ones(len(bb))))
        proposal = linprog(bb, A_eq=equality, b_eq=[0, 0, 0, 1], bounds=(0, None),
                           method="highs", options=_options(config))
        if proposal.x is not None and np.isfinite(proposal.x).all():
            y = vector(np.maximum(proposal.x[:len(b)], 0))
            if contradiction(system, y).accepted:
                return Decision(Status.CONTRADICTION, y=y, numerical_status=numerical_status)
    except (ValueError, RuntimeError, FloatingPointError, OverflowError):
        pass
    return Decision(Status.UNKNOWN, numerical_status=numerical_status,
                    reason="No independently accepted point or contradiction proposal")


def support_upper(system: Polytope, c: Sequence[Any], t: Any = 0,
                  config: SolverConfig = SolverConfig()) -> Support:
    cs, ts = vector(c), rational(t)
    zero = (Q(0),) * len(system.A)
    fallback = upper_bound(system, cs, ts, zero)
    assert fallback.accepted and fallback.value is not None
    best = Support(fallback.value, zero, False)
    try:
        proposed = _lp(system, -np.array(cs, dtype=float), config)
        marginal = getattr(getattr(proposed, "ineqlin", None), "marginals", None)
        if marginal is not None and len(marginal) == len(system.A) and np.isfinite(marginal).all():
            y = vector(np.maximum(-np.asarray(marginal), 0))
            checked = upper_bound(system, cs, ts, y)
            if checked.accepted and checked.value is not None and checked.value < best.bound:
                best = Support(checked.value, y, True)
    except (ValueError, RuntimeError, FloatingPointError, OverflowError):
        pass
    return best

