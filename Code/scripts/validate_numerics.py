"""Independent small-polytope vertex oracle and envelope scaling benchmark.

The oracle uses determinants/Cramer's rule, not the production active-set
recovery or LP feasibility classification. All arithmetic is rational.
"""
from fractions import Fraction as F
from itertools import combinations
import json
from math import comb
from pathlib import Path
import sys

import numpy as np

from witness3d.constraints import domain_rows
from witness3d.envelopes import depth_envelope
from witness3d.exact import Box, Polytope, RowTag
from witness3d.io import atomic_json, plain
from witness3d.profiling import Profile
from witness3d.solver import Status, solve, support_upper
from witness3d.synthetic import SyntheticConfig, generate
from witness3d.verify import check_artifact, check_envelope


def det(a):
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
            -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
            +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))


def vertices(poly):
    rows, rhs, _ = domain_rows(poly.box)
    A, b = list(poly.A)+rows, list(poly.b)+rhs
    found = set()
    for active in combinations(range(len(A)), 3):
        matrix = [A[i] for i in active]
        determinant = det(matrix)
        if determinant == 0:
            continue
        x = []
        for column in range(3):
            changed = [list(row) for row in matrix]
            for j, i in enumerate(active):
                changed[j][column] = b[i]
            x.append(det(changed)/determinant)
        # Separate direct membership, not Polytope.contains or verify.*.
        if all(sum(v*w for v, w in zip(row, x)) <= limit for row, limit in zip(A, b)):
            found.add(tuple(x))
    return found


def exact_audit():
    rng = np.random.default_rng(20261102)
    results = []
    with Profile() as profile:
        for index in range(48):
            rows = rng.integers(-3, 4, size=(6, 3)).tolist()
            bounds = rng.integers(-3, 6, size=6).tolist()
            if index % 3 == 0:
                bounds = [abs(b) for b in bounds]  # origin is feasible
            if index % 3 == 1:
                rows[:2], bounds[:2] = [[1, 0, 0], [-1, 0, 0]], [0, -1]
            p = Polytope(tuple(map(tuple, rows)), tuple(bounds),
                         tuple(RowTag('oracle', str(j), '', 'test') for j in range(6)),
                         Box((-2, -2, -2), (2, 2, 2)))
            all_vertices = vertices(p)
            decision = solve(p)
            artifact = decision.artifact(p)
            mismatch = (decision.status == Status.FEASIBLE and not all_vertices or
                        decision.status == Status.CONTRADICTION and bool(all_vertices))
            queries = []
            for c in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, -2, 3), (-1, 2, -3)]:
                support = support_upper(p, c, F(1, 7))
                optimum = max((sum(F(ci)*xi for ci, xi in zip(c, x))+F(1, 7) for x in all_vertices), default=None)
                queries.append({'c': c, 'bound': str(support.bound),
                                'exact_optimum': str(optimum) if optimum is not None else None,
                                'sound': optimum is None or support.bound >= optimum,
                                'artifact_accepted': check_artifact(support.artifact(p, c, F(1, 7))).accepted})
            results.append({'case': index, 'system': p.to_dict(), 'vertex_count': len(all_vertices),
                            'oracle_empty': not all_vertices, 'status': decision.status.value,
                            'mismatch': bool(mismatch), 'decision_artifact': artifact,
                            'artifact_accepted': check_artifact(artifact).accepted if artifact else None,
                            'support_queries': queries})
    assert not any(r['mismatch'] for r in results)
    assert all(q['sound'] and q['artifact_accepted'] for r in results for q in r['support_queries'])
    assert all(r['artifact_accepted'] is not False for r in results)
    return {'seed': 20261102, 'cases': results, 'efficiency': profile.as_dict(),
            'mismatches': sum(r['mismatch'] for r in results),
            'unknown': sum(r['status'] == 'UNKNOWN' for r in results),
            'empty': sum(r['oracle_empty'] for r in results),
            'support_queries': sum(len(r['support_queries']) for r in results)}


def scaling():
    results = []
    for views, q in [(3, 0), (3, 1), (5, 1), (5, 2), (7, 2), (7, 3), (9, 3), (9, 4), (13, 6)]:
        for seed in [11, 23, 37]:
            # Fixed total span: increasing n does not artificially increase baseline.
            inputs, truth = generate(SyntheticConfig(seed=seed, tracks=1, views=views,
                                                     baseline=.6/(views-1), bounded_noise=.2,
                                                     depth_bias=1.5))
            with Profile() as profile:
                env = depth_envelope(inputs.tracks[0], 0, inputs.cameras, inputs.box,
                                     q=q, max_hypotheses=64, save_evidence=True)
            trace = plain(env)
            results.append({'views': views, 'q': q, 'seed': seed, 'hypotheses': comb(views-1, q),
                            'state': env.state, 'evidence_bytes': len(json.dumps(trace).encode()),
                            'envelope_width_m': float(env.upper-env.lower) if env.lower is not None else None,
                            'truth_contained': env.lower <= F(truth.depths['0:0']) <= env.upper if env.lower is not None else None,
                            'trace_accepted': check_envelope(trace).accepted if env.evidence else None,
                            **profile.as_dict()})
            print(json.dumps(results[-1]), flush=True)
    return results


if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'docs/validation')
    audit = exact_audit()
    atomic_json(out/'numerical_oracle_results.json', audit)
    print(json.dumps({key: value for key, value in audit.items() if key != 'cases'}), flush=True)
    atomic_json(out/'enumeration_scaling_results.json', scaling())
