from fractions import Fraction

import pytest

from witness3d.exact import Box, Polytope, RowTag, rational, solve_three
from witness3d.verify import check_artifact, contradiction, feasible_point, upper_bound


def system(rows, bounds, box=None):
    return Polytope(tuple(tuple(row) for row in rows), tuple(bounds),
                    tuple(RowTag("t", str(i), "c", "test") for i in range(len(rows))),
                    box or Box((-10, -10, -10), (10, 10, 10)))


def test_analytic_farkas_ray():
    p = system([[1, 0, 0], [-1, 0, 0]], [0, -1])
    assert contradiction(p, [1, 1]).accepted
    assert not contradiction(p, [1, 0]).accepted
    assert not contradiction(p, [-1, 1]).accepted


def test_tiny_residual_is_not_proof():
    eps = Fraction(1, 10**12)
    p = system([[eps, 0, 0]], [-1], Box((-2*10**12, -1, -1), (0, 1, 1)))
    assert feasible_point(p, [-10**12, 0, 0]).accepted
    assert not contradiction(p, [1]).accepted


def test_domain_must_be_part_of_certificate():
    p = system([[1, 0, 0]], [-1], Box((0, 0, 0), (1, 1, 1)))
    assert contradiction(p, [1]).accepted
    expanded = system(p.A, p.b, Box((-2, 0, 0), (1, 1, 1)))
    assert not contradiction(expanded, [1]).accepted


def test_support_bound_and_tampering():
    p = system([[1, 0, 0]], [1])
    bound = upper_bound(p, [1, 0, 0], 2, [1])
    assert bound.accepted and bound.value == 3
    assert not upper_bound(p, [1, 0, 0], 2, [1], claimed=2).accepted
    payload = {"system": p.to_dict(), "certificate": {"kind": "upper_bound", "c": [1, 0, 0], "t": 2, "y": [1], "bound": 3}}
    assert check_artifact(payload).accepted
    payload["certificate"]["y"] = [-1]
    assert not check_artifact(payload).accepted


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_rejected(bad):
    with pytest.raises(ValueError):
        rational(bad)
    p = system([[1, 0, 0]], [1])
    assert not contradiction(p, [bad]).accepted


def test_dimensions_and_exact_vertex():
    p = system([[3, 0, 0]], [1])
    assert feasible_point(p, [Fraction(1, 3), 0, 0]).accepted
    assert not feasible_point(p, [1, 0]).accepted
    assert not contradiction(p, []).accepted
    assert solve_three([[3, 0, 0], [0, 2, 0], [0, 0, 1]], [1, 1, 1]) == (Fraction(1, 3), Fraction(1, 2), 1)
    assert solve_three([[0, 0, 0]]*3, [0, 0, 0]) is None


def test_roundtrip():
    p = system([[Fraction(1, 7), 0, 0]], [Fraction(3, 11)])
    assert Polytope.from_dict(p.to_dict()) == p

