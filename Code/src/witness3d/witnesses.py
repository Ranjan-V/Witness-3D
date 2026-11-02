from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .exact import Polytope
from .solver import Decision, SolverConfig, Status, solve


@dataclass
class Conflict:
    indices: tuple[int, ...]
    decision: Decision
    qualification: str
    queries: int

    def observation_ids(self, system: Polytope) -> set[str]:
        return {system.tags[i].observation for i in self.indices
                if system.tags[i].kind.startswith("depth_")}


def extract_conflict(system: Polytope, method: str = "deletion", max_queries: int = 256,
                     config: SolverConfig = SolverConfig()) -> Conflict | None:
    if method not in {"deletion", "small", "dual"} or max_queries < 1:
        raise ValueError("Invalid extraction settings")
    full = solve(system, config)
    if full.status != Status.CONTRADICTION:
        return None
    if max_queries == 1:
        return Conflict(tuple(range(len(system.A))), full, "budget_limited_full_conflict", 1)
    indices = tuple(i for i, tag in enumerate(system.tags) if not tag.kind.startswith("domain_"))
    if method == "dual" and full.y is not None:
        # Drop zero rows only when the resulting subsystem itself verifies.
        proposed = tuple(i for i in indices if full.y[i] > 0)
        checked = solve(system.subset(proposed), config)
        if checked.status == Status.CONTRADICTION:
            return Conflict(proposed, checked, "sparse_verified_subset", 2)
        return Conflict(tuple(range(len(system.A))), full, "full_verified_conflict", 2)
    queries = 1
    if method == "small":
        unknown_smaller = False
        for size in range(1, min(4, len(indices)) + 1):
            unknown_this_size = False
            for chosen in combinations(indices, size):
                if queries >= max_queries:
                    return Conflict(tuple(range(len(system.A))), full, "budget_limited_full_conflict", queries)
                decision = solve(system.subset(chosen), config)
                queries += 1
                if decision.status == Status.CONTRADICTION:
                    label = "small_verified_subset" if unknown_smaller else "minimum_rows_relative_to_domain"
                    return Conflict(chosen, decision, label, queries)
                unknown_this_size |= decision.status == Status.UNKNOWN
            unknown_smaller |= unknown_this_size
        return Conflict(tuple(range(len(system.A))), full, "full_verified_conflict", queries)
    current = list(indices)
    inconclusive = False
    for i in indices:
        if queries >= max_queries - 1:
            inconclusive = True
            break
        proposed = [j for j in current if j != i]
        decision = solve(system.subset(proposed), config)
        queries += 1
        if decision.status == Status.CONTRADICTION:
            current = proposed
        elif decision.status == Status.UNKNOWN:
            inconclusive = True
    checked = solve(system.subset(current), config)
    queries += 1
    if checked.status != Status.CONTRADICTION:
        return Conflict(tuple(range(len(system.A))), full, "full_verified_conflict", queries)
    return Conflict(tuple(current), checked,
                    "verified_subset_unknown_minimality" if inconclusive else "irreducible_relative_to_domain", queries)

