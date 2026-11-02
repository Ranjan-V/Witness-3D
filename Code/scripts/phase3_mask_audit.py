"""Replay saved Phase 2 inputs with equal-budget selector controls, CPU only."""
from collections import defaultdict
import csv
import json
from pathlib import Path
import numpy as np
from phase3_selectors import scores, select
from witness3d.io import atomic_json, load_inputs
from witness3d.metrics import binary_metrics, repair_metrics
from witness3d.profiling import Profile


def evaluate(inputs, records, truth, label, seed):
    by = {(r['track'], r['method']): r for r in records}
    obs = [o for t in inputs.tracks for o in t.observations]
    ids = [o.id for o in obs]
    groups = np.array([t.id for t in inputs.tracks for o in t.observations])
    original = np.array([o.depth for o in obs])
    reference = np.array([truth['depths'][i] for i in ids])
    wrong = np.array([truth['wrong_claims'][i] for i in ids])
    witness = np.array([o.id in by[(t.id, 'local_all')]['edit_ids'] for t in inputs.tracks for o in t.observations])
    score = scores(inputs, seed)
    output = []
    for candidate in ['triangulation', 'ransac']:
        proposed = np.array([by[(t.id, candidate)]['depths'][o.id] for t in inputs.tracks for o in t.observations])
        eligible = np.isfinite(proposed) & (proposed > 0) & (proposed != original)
        masks = [('witness', witness & eligible, 'both', 0)]
        for policy in [False, True]:
            for name, values in score.items():
                for draw in range(32 if name == 'random' else 1):
                    mask = select(values, eligible, groups, witness, seed*1009+draw, policy)
                    masks.append((name, mask, 'track' if policy else 'case', draw))
        for name, mask, policy, draw in masks:
            after = np.where(mask, proposed, original)
            output.append({'scenario': label, 'seed': seed, 'candidate': candidate, 'selector': name,
                           'budget_scope': policy, 'random_draw': draw, 'population': len(ids),
                           'requested_witness_count': int(witness.sum()), 'edits': int(mask.sum()),
                           'mask': binary_metrics(mask, wrong),
                           'abs_rel': float(np.mean(abs(after-reference)/reference)),
                           'before_abs_rel': float(np.mean(abs(original-reference)/reference)),
                           **repair_metrics(original, after, reference)})
    # Original W mask across every observation, including non-actionable DLT failures.
    output.append({'scenario': label, 'seed': seed, 'candidate': 'mask_only', 'selector': 'witness',
                   'budget_scope': 'full_population', 'mask': binary_metrics(witness, wrong),
                   'population': len(ids), 'edits': int(witness.sum())})
    return output


if __name__ == '__main__':
    root = Path('docs/validation/results/sweep')
    out = Path('docs/phase3')
    rows = []
    with Profile() as profile:
        for case in sorted(root.glob('*/seed_*')):
            inputs = load_inputs(case/'inputs.json')
            records = [json.loads(line) for line in (case/'run/records.jsonl').read_text().splitlines()]
            # All scores are computed from inference inputs; truth is evaluation-only.
            truth = json.loads((case/'evaluation_truth.json').read_text())
            rows.extend(evaluate(inputs, records, truth, case.parent.name, int(case.name.split('_')[1])))
            print(case.parent.name, case.name, flush=True)
    atomic_json(out/'mask_results.json', rows)
    atomic_json(out/'mask_efficiency.json', profile.as_dict())
    aggregate = defaultdict(list)
    for r in rows:
        aggregate[(r['scenario'], r['candidate'], r['selector'], r['budget_scope'])].append(r)
    table = []
    for keys, group in aggregate.items():
        counts = {k: sum(r['mask'][k] for r in group) for k in ['tp', 'fp', 'fn', 'tn']}
        table.append(dict(zip(['scenario','candidate','selector','budget_scope'], keys),
                          **counts, precision=counts['tp']/(counts['tp']+counts['fp']) if counts['tp']+counts['fp'] else None,
                          recall=counts['tp']/(counts['tp']+counts['fn']) if counts['tp']+counts['fn'] else None,
                          fpr=counts['fp']/(counts['fp']+counts['tn']) if counts['fp']+counts['tn'] else None,
                          abs_rel=np.mean([r['abs_rel'] for r in group]) if 'abs_rel' in group[0] else None,
                          improved=np.mean([r['corrected_fraction'] for r in group if r.get('corrected_fraction') is not None]) if 'abs_rel' in group[0] else None))
    atomic_json(out/'mask_summary.json', table)
    with (out/'mask_summary.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
