"""Exact finite-input representation. Numerical arrays are optional copies."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Any, Iterable, Sequence

Q = Fraction


def rational(value: Any) -> Q:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, str):
        return Q(value)
    if isinstance(value, int):
        return Q(value)
    number = float(value)
    if not isfinite(number):
        raise ValueError("Exact input must be finite")
    return Q.from_float(number)


def vector(values: Iterable[Any]) -> tuple[Q, ...]:
    return tuple(rational(v) for v in values)


def dot(a: Sequence[Q], b: Sequence[Q]) -> Q:
    if len(a) != len(b):
        raise ValueError("Dot-product dimension mismatch")
    return sum((x * y for x, y in zip(a, b)), Q(0))


@dataclass(frozen=True)
class Box:
    lower: tuple[Q, ...]
    upper: tuple[Q, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "lower", vector(self.lower))
        object.__setattr__(self, "upper", vector(self.upper))
        if len(self.lower) != 3 or len(self.upper) != 3:
            raise ValueError("World box must be 3D")
        if any(a > b for a, b in zip(self.lower, self.upper)):
            raise ValueError("Reversed box")

    def minimum(self, coefficients: Sequence[Q]) -> Q:
        if len(coefficients) != 3:
            raise ValueError("Expected a 3D linear form")
        return sum((min(c * lo, c * hi) for c, lo, hi in
                    zip(coefficients, self.lower, self.upper)), Q(0))

    def contains(self, point: Sequence[Q]) -> bool:
        return len(point) == 3 and all(lo <= x <= hi for lo, x, hi in
                                       zip(self.lower, point, self.upper))


@dataclass(frozen=True)
class RowTag:
    track: str
    observation: str
    camera: str
    kind: str


@dataclass(frozen=True)
class Polytope:
    A: tuple[tuple[Q, ...], ...]
    b: tuple[Q, ...]
    tags: tuple[RowTag, ...]
    box: Box

    def __post_init__(self) -> None:
        object.__setattr__(self, "A", tuple(vector(row) for row in self.A))
        object.__setattr__(self, "b", vector(self.b))
        if not (len(self.A) == len(self.b) == len(self.tags)):
            raise ValueError("Row metadata mismatch")
        if any(len(row) != 3 for row in self.A):
            raise ValueError("All constraints must have three columns")

    def subset(self, indices: Sequence[int]) -> Polytope:
        return Polytope(tuple(self.A[i] for i in indices),
                        tuple(self.b[i] for i in indices),
                        tuple(self.tags[i] for i in indices), self.box)

    def contains(self, point: Sequence[Any]) -> bool:
        p = vector(point)
        return self.box.contains(p) and all(dot(row, p) <= b for row, b in zip(self.A, self.b))

    def transpose_product(self, y: Sequence[Q]) -> tuple[Q, ...]:
        if len(y) != len(self.A):
            raise ValueError("Multiplier dimension mismatch")
        return tuple(sum((row[j] * yi for row, yi in zip(self.A, y)), Q(0)) for j in range(3))

    def float_arrays(self):
        import numpy as np
        return np.array(self.A, dtype=np.float64).reshape(-1, 3), np.array(self.b, dtype=np.float64)

    def to_dict(self) -> dict[str, Any]:
        return {"A": [[str(v) for v in row] for row in self.A],
                "b": [str(v) for v in self.b],
                "box": {"lower": [str(v) for v in self.box.lower],
                        "upper": [str(v) for v in self.box.upper]},
                "tags": [vars(tag) for tag in self.tags]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Polytope:
        return cls(tuple(tuple(row) for row in data["A"]), tuple(data["b"]),
                   tuple(RowTag(**tag) for tag in data["tags"]), Box(**data["box"]))


def solve_three(rows: Sequence[Sequence[Q]], rhs: Sequence[Q]) -> tuple[Q, ...] | None:
    """Exact Gaussian elimination for a proposed 3-row active intersection."""
    if len(rows) != 3 or len(rhs) != 3 or any(len(r) != 3 for r in rows):
        raise ValueError("Expected a 3 by 3 system")
    a = [list(vector(r)) + [rational(b)] for r, b in zip(rows, rhs)]
    for j in range(3):
        pivot = next((i for i in range(j, 3) if a[i][j] != 0), None)
        if pivot is None:
            return None
        a[j], a[pivot] = a[pivot], a[j]
        scale = a[j][j]
        a[j] = [v / scale for v in a[j]]
        for i in range(3):
            if i != j:
                factor = a[i][j]
                a[i] = [v - factor * w for v, w in zip(a[i], a[j])]
    return tuple(a[i][3] for i in range(3))

