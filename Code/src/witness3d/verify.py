"""Independent arithmetic verifier: no NumPy, SciPy, PyTorch or solver imports."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Sequence

from .exact import Polytope, Q, dot, rational, vector


@dataclass(frozen=True)
class Check:
    accepted: bool
    reason: str
    value: Q | None = None
    uses_domain: bool = False


def multipliers(system: Polytope, y: Sequence[Any]) -> tuple[Q, ...]:
    result = vector(y)
    if len(result) != len(system.A) or any(v < 0 for v in result):
        raise ValueError("Expected one nonnegative multiplier per row")
    return result


def contradiction(system: Polytope, y: Sequence[Any]) -> Check:
    try:
        ys = multipliers(system, y)
        residual = system.transpose_product(ys)
        margin = system.box.minimum(residual) - dot(system.b, ys)
        return Check(margin > 0, "exact bounded-domain margin", margin, any(residual))
    except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        return Check(False, str(exc))


def upper_bound(system: Polytope, c: Sequence[Any], t: Any,
                y: Sequence[Any], claimed: Any | None = None) -> Check:
    try:
        ys = multipliers(system, y)
        cs = vector(c)
        if len(cs) != 3:
            raise ValueError("Query must have dimension three")
        residual = tuple(a - ci for a, ci in zip(system.transpose_product(ys), cs))
        bound = dot(system.b, ys) - system.box.minimum(residual) + rational(t)
        accepted = claimed is None or rational(claimed) >= bound
        return Check(accepted, "exact residual-corrected upper bound", bound, any(residual))
    except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        return Check(False, str(exc))


def feasible_point(system: Polytope, point: Sequence[Any]) -> Check:
    try:
        ok = system.contains(point)
        return Check(ok, "exact point and domain evaluation")
    except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        return Check(False, str(exc))


def check_artifact(payload: dict[str, Any]) -> Check:
    """Validate a self-contained certificate, including its exact input system."""
    try:
        system = Polytope.from_dict(payload["system"])
        cert = payload["certificate"]
        if cert["kind"] == "contradiction":
            return contradiction(system, cert["y"])
        if cert["kind"] == "point":
            return feasible_point(system, cert["point"])
        if cert["kind"] == "upper_bound":
            return upper_bound(system, cert["c"], cert["t"], cert["y"], cert["bound"])
        return Check(False, "Unknown certificate kind")
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        return Check(False, "Malformed artifact: " + str(exc))


def check_envelope(payload: dict[str, Any]) -> Check:
    """Check all deletion branches and support bounds of a declared finite union.

    This checks the encoded systems; it cannot authenticate cameras or tracks
    against a physical scene. Missing/duplicate branches are always rejected.
    """
    try:
        n, target, budget = payload["views"], payload["target"], payload["budget"]
        if not (isinstance(n, int) and isinstance(target, int) and isinstance(budget, int)
                and n >= 2 and 0 <= target < n and 0 <= budget < n):
            raise ValueError("Invalid envelope hypothesis metadata")
        if payload["state"] not in {"BOUNDED", "MEASUREMENT_CONFLICT"}:
            raise ValueError("No complete bounded/excluded union supplied")
        ids = payload["observation_ids"]
        if len(ids) != n or len(set(ids)) != n:
            raise ValueError("Observation ID metadata mismatch")
        query, offset = vector(payload["query"]), rational(payload["offset"])
        if len(query) != 3:
            raise ValueError("Invalid depth query")
        expected = set(combinations([i for i in range(n) if i != target], budget))
        records = payload["evidence"]
        deleted = [tuple(record["deleted"]) for record in records]
        if len(records) != len(expected) or set(deleted) != expected:
            raise ValueError("Missing or duplicate deletion hypothesis")
        lows, highs = [], []
        observation_rows = {}
        common_box = None
        for record in records:
            keep = {ids[i] for i in range(n) if i not in record["deleted"]}
            if record["status"] == "VERIFIED_CONTRADICTION":
                artifact = record["exclusion"]
                if artifact["certificate"]["kind"] != "contradiction" or not check_artifact(artifact).accepted:
                    raise ValueError("Unverified hypothesis exclusion")
                system = Polytope.from_dict(artifact["system"])
            elif "fallback" in record:
                system = Polytope.from_dict(record["domain_system"])
                lows.append(system.box.minimum(query) + offset)
                highs.append(-system.box.minimum(tuple(-v for v in query)) + offset)
            else:
                hi, neglo = record["upper"], record["negative_lower"]
                system = Polytope.from_dict(hi["system"])
                if Polytope.from_dict(neglo["system"]) != system:
                    raise ValueError("Upper/lower systems differ")
                for artifact, c, t in ((hi, query, offset), (neglo, tuple(-v for v in query), -offset)):
                    cert = artifact["certificate"]
                    if cert["kind"] != "upper_bound" or vector(cert["c"]) != c or rational(cert["t"]) != t:
                        raise ValueError("Hypothesis uses a different affine depth query")
                    if not check_artifact(artifact).accepted:
                        raise ValueError("Invalid support certificate")
                lows.append(-rational(neglo["certificate"]["bound"]))
                highs.append(rational(hi["certificate"]["bound"]))
            observed = {tag.observation for tag in system.tags if tag.observation}
            if observed != keep or any(tag.kind.startswith("depth_") for tag in system.tags):
                raise ValueError("Depth-dependent or incomplete pixel-only hypothesis")
            if common_box is None:
                common_box = system.box
            elif system.box != common_box:
                raise ValueError("Hypotheses use different world domains")
            for observation in observed:
                rows = tuple((row, b, tag) for row, b, tag in zip(system.A, system.b, system.tags)
                             if tag.observation == observation)
                if observation in observation_rows and observation_rows[observation] != rows:
                    raise ValueError("An observation changes its constraints between hypotheses")
                observation_rows[observation] = rows
        if not lows:
            return Check(payload["state"] == "MEASUREMENT_CONFLICT", "All union branches independently excluded")
        if payload["state"] != "BOUNDED":
            raise ValueError("Nonempty/unresolved branch cannot be called a measurement conflict")
        lo, hi = rational(payload["lower"]), rational(payload["upper"])
        return Check(lo <= min(lows) and hi >= max(highs) and lo <= hi,
                     "Complete hypothesis coverage and independent support checks")
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        return Check(False, "Malformed envelope: " + str(exc))

