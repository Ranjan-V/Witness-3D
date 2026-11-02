"""Generate tables, plots and failure-case excerpts from recorded CPU runs."""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import runpy

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from witness3d.io import atomic_json, plain
from witness3d.repair import local_repair, RepairConfig

out = Path('docs/validation')
root = out/'results/sweep'
summary = json.loads((root/'summary.json').read_text())
rows = json.loads((root/'metrics_by_seed.json').read_text())
indexed = {(r['scenario'], r['method']): r for r in summary}


def value(scenario, method, metric):
    return indexed[(scenario, method)]['metrics'][metric]['mean']


def fmt(number, digits=5):
    return '—' if number is None else f'{number:.{digits}f}'


flat = []
for row in summary:
    r = {'scenario': row['scenario'], 'method': row['method'], 'seeds': row['seeds'], **row['totals']}
    for metric, data in row['metrics'].items():
        r[metric] = data['mean']
        r[metric+'_ci95_low'] = data['seed_bootstrap_ci95'][0] if data['seed_bootstrap_ci95'] else None
        r[metric+'_ci95_high'] = data['seed_bootstrap_ci95'][1] if data['seed_bootstrap_ci95'] else None
    r['individual_precision'] = row.get('individual_precision')
    r['individual_recall'] = row.get('individual_recall')
    r['states'] = json.dumps(row['states'])
    r['joint_status_after'] = json.dumps(row['joint_status_after'])
    flat.append(r)
with (out/'synthetic_results.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
    writer.writeheader()
    writer.writerows(flat)

methods = ['none', 'fusion', 'triangulation', 'robust_triangulation', 'ransac', 'robust_depth',
           'local', 'local_all', 'global', 'triangulation_on_selective_mask', 'robust_triangulation_on_selective_mask']
lines = ['# Actual baseline comparisons', '',
         'Reference scenario: five seeds, 40 tracks, 120 scalar depths. Means below are seed means. '
         'Full seed-bootstrap intervals and all scenarios are in `synthetic_results.csv` and `results/sweep/summary.json`. '
         'Undefined cells are shown as —. See `experiment_protocol.md` for denominators, uncertainty matching and failure policy.', '',
         '| Method | AbsRel | MAE m | Shared fused point error m | Reprojection px | Edited % | Wrong corrected % | Correct damaged % | Strict error increase % |',
         '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for method in methods:
    data = [value('reference', method, key) for key in ['abs_rel', 'depth_mae_m', 'fused_point_error_m', 'fused_reprojection_mean_px']]
    percent = [100*value('reference', method, key) for key in ['changed_fraction', 'corrected_fraction', 'damaged_fraction', 'absolute_error_increased_fraction']]
    lines.append('| '+method+' | '+' | '.join(fmt(v) for v in data)+' | '+' | '.join(fmt(v, 2) for v in percent)+' |')
lines += ['', 'The shared fused point is an evaluation readout for scalar outputs. Native-point errors are separately recorded; selective repair supplies no native point. '
          'A zero 5%-threshold damage rate does not mean zero numerical error increase. In this reference, the 73 originally exact depths are changed slightly by full triangulation/global estimation; '
          'selective repair preserves them. The mask-sharing diagnostic also preserves them and has lower measured error than endpoint clipping, without a universal non-damage theorem.', '',
          '## Stress scenarios: actual AbsRel', '',
          '| Scenario | Original | Triangulation | Robust reprojection | RANSAC | Local | All-target local | Global |',
          '|---|---:|---:|---:|---:|---:|---:|---:|']
for scenario in sorted({r['scenario'] for r in summary}):
    lines.append('| '+scenario+' | '+' | '.join(fmt(value(scenario, method, 'abs_rel')) for method in
                                               ['none', 'triangulation', 'robust_triangulation', 'ransac', 'local', 'local_all', 'global'])+' |')
(out/'baseline_comparisons.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')

# Paired resampling across seed differences, not independent method samples.
rng = np.random.default_rng(20261102)
paired = []
for scenario in sorted({r['scenario'] for r in rows}):
    for other in ['none', 'triangulation', 'ransac', 'triangulation_on_selective_mask', 'global']:
        local = {r['seed']: r['abs_rel'] for r in rows if r['scenario'] == scenario and r['method'] == 'local_all'}
        baseline = {r['seed']: r['abs_rel'] for r in rows if r['scenario'] == scenario and r['method'] == other}
        differences = np.array([local[s]-baseline[s] for s in sorted(local.keys() & baseline.keys())])
        ci = np.quantile(rng.choice(differences, (2000, len(differences)), replace=True).mean(axis=1), [.025, .975]).tolist()
        paired.append({'scenario': scenario, 'comparison': 'local_all minus '+other,
                       'paired_seeds': len(differences), 'abs_rel_difference': float(differences.mean()),
                       'seed_bootstrap_ci95': ci, 'significance_claim': False})
atomic_json(out/'paired_seed_comparisons.json', paired)

local = [r for r in rows if r['method'] == 'local_all']
totals = {'scenarios': len({r['scenario'] for r in rows}), 'case_seeds': len(local),
          'tracks': sum(r['tracks'] for r in local), 'depths_per_method': sum(r['count'] for r in local),
          'primary_method_records': sum(r['tracks'] for r in local)*9,
          'certificate_submissions': sum(r['certificate_submissions'] for r in rows),
          'invalid_certificates': sum(r['invalid_certificates'] for r in rows),
          'envelope_traces': sum(r['envelope_traces'] for r in rows),
          'invalid_envelope_traces': sum(r['invalid_envelope_traces'] for r in rows),
          'local_all': {key: sum(r[key] for r in local) for key in ['edited_count', 'edited_improved_count',
                       'premise_eligible_count', 'premise_eligible_edited_count', 'conditional_edited_harm_count']},
          'global_states': dict(sum((Counter(r['states']) for r in rows if r['method'] == 'global'), Counter()))}
none = [r for r in rows if r['method'] == 'none']
totals['group_contradiction_vs_elastic_reference'] = {
    key: sum(r['group_contradiction_vs_numerical_elastic_reference'][key] for r in none) for key in ['tp', 'fp', 'fn', 'tn']}
totals['elastic_reference_ambiguous'] = sum(r['elastic_reference_ambiguous'] for r in none)
atomic_json(out/'result_totals.json', totals)

failures = []
for scenario in sorted({r['scenario'] for r in rows}):
    for seed in [11, 23, 37, 53, 71]:
        case = root/scenario/f'seed_{seed}'
        truth = json.loads((case/'evaluation_truth.json').read_text())
        for path in sorted((case/'run/records').glob('*.json')):
            record = json.loads(path.read_text())
            if record['method'] not in ['local', 'local_all']:
                continue
            for oid in record['edit_ids']:
                before, after, true = record['original_depths'][oid], record['depths'][oid], truth['depths'][oid]
                if abs(after-true) > abs(before-true)+1e-10:
                    env = record['envelopes'][oid]
                    failures.append({'scenario': scenario, 'seed': seed, 'method': record['method'],
                                     'observation': oid, 'before': before, 'after': after, 'truth': true,
                                     'before_abs_error': abs(before-true), 'after_abs_error': abs(after-true),
                                     'envelope_lower': env['lower'], 'envelope_upper': env['upper'],
                                     'record_path': str(path), 'physical_pixel_contained': truth['pixel_contained'][oid]})
atomic_json(out/'observed_harm_examples.json', failures)

# Reuse the adversarial test generator to preserve exact numerical counterexamples.
fixture = runpy.run_path('tests/test_phase2_adversarial.py')['analytic_pair']
explicit = []
for name, args in [('wrong_outlier_budget', {'aux_u': 295.}),
                   ('wrong_baseline', {'supplied_baseline': 2.}),
                   ('undersized_pixel_box', {'aux_u': 272.})]:
    track, cameras, box = fixture(**args)
    for q in [0, 1]:
        repair = local_repair(track, cameras, box, RepairConfig(q=q, localize=False))
        explicit.append({'case': name, 'q': q, 'physical_target_depth': 2.,
                         'before': track.observations[0].depth, 'after': repair.repaired.observations[0].depth,
                         'edits': repair.edits, 'before_status': repair.before.status.value,
                         'after_status': repair.after.status.value,
                         'envelope': plain(repair.envelopes.get('a'))})
atomic_json(out/'explicit_counterexamples.json', explicit)

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(2, 2, figsize=(12.5, 9), layout='constrained')
plot_methods = ['none', 'triangulation', 'ransac', 'robust_depth', 'local', 'local_all', 'global', 'triangulation_on_selective_mask']
labels = ['Original', 'Triangulation', 'RANSAC', 'Robust depth', 'Selective: localized', 'Selective: all targets', 'Global', 'Triangulation: same mask']
means = [value('reference', m, 'abs_rel') for m in plot_methods]
cis = [indexed[('reference', m)]['metrics']['abs_rel']['seed_bootstrap_ci95'] for m in plot_methods]
axes[0, 0].barh(labels, means, color=['#78838b', '#258ca0', '#258ca0', '#258ca0', '#ce7933', '#ce7933', '#6b68a4', '#258ca0'])
axes[0, 0].errorbar(means, range(len(means)), xerr=np.array([[m-c[0], c[1]-m] for m, c in zip(means, cis)]).T,
                   fmt='none', color='#27313b', capsize=3)
axes[0, 0].invert_yaxis()
axes[0, 0].set_xscale('log')
axes[0, 0].set(xlabel='Mean absolute-relative depth error (log scale)', title='Reference: accuracy favors triangulation')
scenarios = ['reference', 'baseline_0p03', 'zero_baseline', 'outliers_10pct_q1', 'pose_translation_0p01', 'gaussian_noise_0p75']
positions = np.arange(len(scenarios))
for method, label, color in [('none', 'Original', '#78838b'), ('triangulation', 'Triangulation', '#258ca0'), ('local_all', 'Selective: all', '#ce7933')]:
    axes[0, 1].plot(positions, [value(s, method, 'abs_rel') for s in scenarios], 'o-', label=label, color=color)
axes[0, 1].set_xticks(positions, ['Reference', 'Small baseline', 'Zero baseline', '10% outliers, q=1', 'Pose error 1 cm', 'Noise 0.75 px'], rotation=30, ha='right')
axes[0, 1].set(ylabel='Mean absolute-relative depth error', title='Selected stresses; no pooled ranking')
axes[0, 1].legend(fontsize=8)
widths = [value(s, 'local_all', 'envelope_width_mean_m') for s in ['reference', 'clean_q1', 'clean_q2']]
axes[1, 0].bar(['q=0', 'q=1', 'q=2'], widths, color='#ce7933')
axes[1, 0].set(ylabel='Mean computed envelope width (m)', title='Three views: deleting both auxiliaries is vacuous')
for i, width in enumerate(widths):
    axes[1, 0].text(i, width+.12, f'{width:.3f}', ha='center')
axes[1, 0].set_ylim(0, 11)
scale = json.loads((out/'enumeration_scaling_results.json').read_text())
groups = defaultdict(list)
for r in scale:
    if r['state'] == 'BOUNDED':
        groups[r['hypotheses']].append(r['wall_seconds'])
xs = sorted(groups)
axes[1, 1].plot(xs, [np.mean(groups[h]) for h in xs], 'o-', color='#6b68a4')
axes[1, 1].set(xlabel='Deletion hypotheses per target', ylabel='Measured seconds per target',
               title='Enumeration cost; 70+ hypotheses abstain at cap 64')
fig.suptitle('Witness3D — controlled CPU validation\n5 seeds × 8 tracks per scenario; intervals show exploratory seed bootstrap', fontsize=14)
fig.savefig(out/'validation_overview.png', dpi=160)
fig.savefig(out/'validation_overview.svg')
plt.close(fig)
print(json.dumps(totals, indent=2))
print('Observed strict-harm records:', len(failures))
