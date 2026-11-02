from unittest.mock import patch

import numpy as np
from scipy.optimize import OptimizeResult

from witness3d.exact import Box, Polytope, RowTag
from witness3d.solver import SolverConfig, Status, solve, support_upper
from witness3d.verify import check_artifact


def p(rows, b, box=None):
    return Polytope(tuple(tuple(r) for r in rows), tuple(b), tuple(RowTag("", "", "", "test") for _ in b),
                    box or Box((-10, -10, -10), (10, 10, 10)))


def test_feasible_negative_coordinate_not_default_nonnegative_lp():
    system = p([[1, 0, 0], [-1, 0, 0]], [-1, 2])
    result = solve(system)
    assert result.status == Status.FEASIBLE
    assert result.point[0] < 0
    assert check_artifact(result.artifact(system)).accepted


def test_analytic_infeasible():
    system = p([[1, 0, 0], [-1, 0, 0]], [0, -1])
    result = solve(system)
    assert result.status == Status.CONTRADICTION
    assert check_artifact(result.artifact(system)).accepted


def test_infeasibility_status_alone_is_unknown():
    fabricated = OptimizeResult(status=2, x=None)
    with patch("witness3d.solver.linprog", return_value=fabricated):
        assert solve(p([[1, 0, 0]], [1])).status == Status.UNKNOWN


def test_invalid_dual_does_not_certify_feasible_system():
    replies = [OptimizeResult(status=2, x=None), OptimizeResult(status=0, x=np.array([1., 0, 0, 0, 0, 0, 0]))]
    with patch("witness3d.solver.linprog", side_effect=replies):
        assert solve(p([[1, 0, 0]], [1])).status == Status.UNKNOWN


def test_support_falls_back_on_failure():
    system = p([[1, 0, 0]], [1], Box((-2, -2, -2), (3, 3, 3)))
    with patch("witness3d.solver.linprog", side_effect=RuntimeError("timeout")):
        support = support_upper(system, [1, 0, 0])
    assert support.bound == 3
    assert not support.optimized
    assert check_artifact(support.artifact(system, [1, 0, 0], 0)).accepted

