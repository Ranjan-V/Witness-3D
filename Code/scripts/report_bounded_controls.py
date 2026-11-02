"""Summarize and audit the separate post-hoc bounded baseline control."""
import json
from pathlib import Path
from collections import Counter
import numpy as np
from witness3d.io import atomic_json, load_inputs

out = Path('docs/validation')
root = out/'results/bounded_controls'
summary = json.loads((root/'summary.json').read_text())
primary = json.loads((out/'results/sweep/summary.json').read_text())
lookup = {(r['scenario'], r['method']): r['metrics']['abs_rel']['mean'] for r in primary+summary}
lines = ['# Post-hoc bounded robust baseline controls', '',
         'Executed after the predeclared sweep exposed runaway unbounded Huber estimates. '
         'Same saved inputs, seeds and finite world box; no reference information enters fitting. '
         'The original results remain intact. These are generic Huber least-squares controls, not state-of-the-art reproductions. '
         'Full configuration and identity are in `results/bounded_controls/protocol.json`.', '',
         '| Scenario | Bounded robust reprojection | Bounded robust depth | RANSAC | All-target selective |',
         '|---|---:|---:|---:|---:|']
for scenario in sorted({r['scenario'] for r in summary}):
    lines.append('| '+scenario+' | '+' | '.join(f'{lookup[(scenario, method)]:.6f}' for method in
                 ['bounded_robust_triangulation', 'bounded_robust_depth', 'ransac', 'local_all'])+' |')
counts = Counter()
states = Counter()
for path in root.glob('*/seed_*/records.json'):
    case = out/'results/sweep'/path.parent.parent.name/path.parent.name
    inputs = load_inputs(case/'inputs.json')
    for record in json.loads(path.read_text()):
        counts['records'] += 1
        states[record['state']] += 1
        if 'point' in record:
            counts['points'] += 1
            point = np.array(record['point'])
            valid = np.all(np.isfinite(point)) and np.all(point >= np.array(inputs.box.lower, float)-1e-9) and np.all(point <= np.array(inputs.box.upper, float)+1e-9)
            counts['points_outside_box_or_nonfinite'] += int(not valid)
        counts['invalid_reported_depths'] += sum(not np.isfinite(v) or v <= 0 for v in record['depths'].values())
assert counts['records'] == 2240
assert counts['points_outside_box_or_nonfinite'] == counts['invalid_reported_depths'] == 0
atomic_json(out/'bounded_control_checks.json', {'counts': dict(counts), 'states': dict(states)})
lines += ['', 'All 2,240 reported records were audited for finite positive depths and valid returned points within the common world box. '
          'See `bounded_control_checks.json`. The controls remove arbitrarily large depths but do not make Huber fitting robust to every false correspondence. '
          'RANSAC remains a stronger comparator in the tested outlier cases; Witness3D does not establish an accuracy advantage over it.', '',
          'Executed runtime: '+json.dumps(json.loads((root/'efficiency.json').read_text()))]
(out/'bounded_baseline_comparisons.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(json.dumps({'counts': dict(counts), 'states': dict(states)}))
