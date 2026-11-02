from witness3d.exact import Box, Polytope, RowTag
from witness3d.verify import check_artifact
from witness3d.witnesses import extract_conflict


def test_minimal_analytic_two_row_conflict():
    p = Polytope(((1, 0, 0), (-1, 0, 0), (0, 1, 0)), (0, -1, 100),
                  tuple(RowTag("t", str(i), "c", "depth_upper") for i in range(3)), Box((-10, -10, -10), (10, 10, 10)))
    for method in ("small", "deletion", "dual"):
        conflict = extract_conflict(p, method=method, max_queries=100)
        assert conflict is not None
        assert check_artifact(conflict.decision.artifact(p.subset(conflict.indices))).accepted


def test_budget_does_not_invent_minimum():
    p = Polytope(((1, 0, 0), (-1, 0, 0)), (0, -1),
                  (RowTag("t", "a", "c", "depth_upper"), RowTag("t", "b", "c", "depth_lower")),
                  Box((-10, -10, -10), (10, 10, 10)))
    conflict = extract_conflict(p, method="small", max_queries=1)
    assert conflict is not None
    assert "minimum" not in conflict.qualification

