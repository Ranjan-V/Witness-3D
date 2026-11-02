"""Post-sweep control: constrain robust point estimation to the same world box.

Added after observing runaway unbounded Huber estimates; does not overwrite the
predeclared sweep or alter Witness3D. No truth is passed to estimate().
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import runpy

import numpy as np
from scipy.optimize import least_squares

from witness3d.baselines import linear_triangulation, average_fusion, depths_from_point
from witness3d.constraints import track_polytope
from witness3d.io import atomic_json, load_inputs, plain, spec_hash
from witness3d.observations import Track
from witness3d.profiling import Profile
from witness3d.solver import solve
from witness3d.synthetic import Truth


def estimate(track, inputs, include_depth):
    initial = linear_triangulation(track, inputs.cameras).point
    if initial is None:
        initial = average_fusion(track, inputs.cameras).point
    lo, hi = np.array(inputs.box.lower, float), np.array(inputs.box.upper, float)
    initial = np.clip(initial, lo+1e-9, hi-1e-9)
    def residual(point):
        values = []
        for obs in track.observations:
            camera = inputs.cameras[obs.camera_id]
            x = camera.camera_points(point)
            z = max(float(x[2]), 1e-6)
            uv = np.array([camera.K[0, 0]*x[0]/z+camera.K[0, 2], camera.K[1, 1]*x[1]/z+camera.K[1, 2]])
            weight = np.sqrt(obs.confidence)
            values.extend(weight*(uv-obs.uv)/np.maximum(obs.pixel_radius, .5))
            values.append(weight*max(0, .01-x[2])*1000)
            if include_depth:
                values.append(weight*(x[2]-obs.depth)/obs.half_width)
        return values
    result = least_squares(residual, initial, bounds=(lo, hi), loss='huber', f_scale=1, max_nfev=200)
    return result.x if result.success else None, result.message


helpers = runpy.run_path('scripts/validate_synthetic.py')
root = Path('docs/validation/results/sweep')
out = Path('docs/validation/results/bounded_controls')
atomic_json(out/'protocol.json', {
    'status': 'Executed post-hoc diagnostic; not part of the original predeclared sweep',
    'motivation': 'Unbounded robust reprojection had runaway estimates; compare with the same finite box',
    'methods': ['bounded_robust_triangulation', 'bounded_robust_depth'],
    'loss': 'huber', 'f_scale': 1, 'max_nfev': 200, 'pixel_scale_floor': .5,
    'source_sweep_signature': json.loads((root/'identity.json').read_text())['signature'],
    'script_hash': spec_hash(Path(__file__).read_text())})
rows = []
with Profile() as whole:
    for case in sorted(root.glob('*/seed_*')):
        inputs = load_inputs(case/'inputs.json')
        old_records = [json.loads(line) for line in (case/'run/records.jsonl').read_text().splitlines()]
        original = {r['track']: r for r in old_records if r['method'] == 'none'}
        records = []
        for track in inputs.tracks:
            for include_depth, method in [(False, 'bounded_robust_triangulation'), (True, 'bounded_robust_depth')]:
                record = deepcopy(original[track.id])
                record['method'] = method
                with Profile() as profile:
                    point, message = estimate(track, inputs, include_depth)
                    record['state'], record['reason'] = 'NUMERICALLY_CONVERGED' if point is not None else 'FAILED_KEEP_ORIGINAL', message
                    if point is not None:
                        depths = depths_from_point(track, inputs.cameras, point)
                        if any(not np.isfinite(depths[o.id]) or depths[o.id] <= o.half_width for o in track.observations):
                            record['state'] = 'FAILED_KEEP_ORIGINAL'
                        else:
                            changed = Track(track.id, tuple(replace(o, depth=depths[o.id]) for o in track.observations))
                            record['depths'], record['point'] = depths, point.tolist()
                            record['status_after'] = solve(track_polytope(changed, inputs.cameras, inputs.box)).status.value
                            record['edit_ids'] = [o.id for o in track.observations if depths[o.id] != o.depth]
                record['efficiency'] = profile.as_dict()
                records.append(record)
        scenario, seed = case.parent.name, int(case.name.split('_')[1])
        atomic_json(out/scenario/case.name/'records.json', records)
        # Evaluation truth is opened only after every inference result is produced.
        t = json.loads((case/'evaluation_truth.json').read_text())
        truth = Truth(**{**t, 'points': {k: np.array(v) for k, v in t['points'].items()}})
        q = json.loads((case/'experiment.json').read_text())['repair']['q']
        rows.extend(helpers['evaluate'](records, inputs, truth, scenario, seed, q))
        print(json.dumps({'scenario': scenario, 'seed': seed, 'records': len(records)}), flush=True)
atomic_json(out/'metrics_by_seed.json', rows)
atomic_json(out/'summary.json', helpers['summarize'](rows, 20261102, 2000))
atomic_json(out/'efficiency.json', whole.as_dict())
print(json.dumps({'complete': True, **whole.as_dict()}), flush=True)
