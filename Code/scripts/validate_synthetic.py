"""CPU-only controlled validation; generation/inference/evaluation are separate.

Run with PYTHONPATH=src. Never imports torch or calls a model adapter.
All extra masked controls use input predictions and the selective edit mask,
never truth. Truth is accessed only by evaluate() and serialization for audit.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
import yaml

from witness3d.baselines import average_fusion
from witness3d.constraints import track_polytope
from witness3d.exact import rational
from witness3d.experiments import run_inputs
from witness3d.io import atomic_json, plain, save_inputs, spec_hash
from witness3d.metrics import binary_metrics, depth_metrics, repair_metrics
from witness3d.observations import Track
from witness3d.pipeline import source_fingerprint
from witness3d.profiling import Profile
from witness3d.verify import check_artifact, check_envelope
from witness3d.synthetic import SyntheticConfig, generate


def masked_controls(records):
    """Matched edit-mask diagnostics, not independent competing algorithms."""
    indexed = {(r['track'], r['method']): r for r in records}
    extra = []
    for local in [r for r in records if r['method'] == 'local_all']:
        for method in ('triangulation', 'robust_triangulation'):
            base = indexed[(local['track'], method)]
            depths = dict(local['original_depths'])
            for oid in local['edit_ids']:
                depths[oid] = base['depths'][oid]
            extra.append({'method': method+'_on_selective_mask', 'track': local['track'],
                          'original_depths': local['original_depths'], 'depths': depths,
                          'state': 'SHARED_SELECTIVE_MASK_DIAGNOSTIC', 'detected': [],
                          'edit_ids': [i for i in depths if depths[i] != local['original_depths'][i]],
                          'status_before': local['status_before'], 'status_after': 'NOT_RECHECKED',
                          'artifacts': [], 'certificate_checks': [],
                          'efficiency': {'wall_seconds': None, 'peak_rss_bytes_sampled': None}})
    return extra


def elastic_reference(poly):
    """Separate elastic LP reference; numerical classification, NOT exact truth."""
    A, b = poly.float_arrays()
    scales = np.maximum(np.linalg.norm(A, axis=1), 1.)
    result = linprog([0., 0., 0., 1.], A_ub=np.column_stack((A/scales[:, None], -np.ones(len(b)))),
                     b_ub=b/scales, bounds=[(float(l), float(u)) for l, u in zip(poly.box.lower, poly.box.upper)]+[(0, None)],
                     method='highs', options={'primal_feasibility_tolerance': 1e-9, 'dual_feasibility_tolerance': 1e-9})
    if not result.success:
        return None
    slack = float(result.x[3])
    return True if slack > 1e-7 else (False if slack <= 1e-9 else None)


def evaluate(records, inputs, truth, scenario, seed, q):
    """Evaluation only. This function never feeds truth back to inference."""
    tracks = {t.id: t for t in inputs.tracks}
    observations = {o.id: o for t in inputs.tracks for o in t.observations}
    numerical_empty = {t.id: elastic_reference(track_polytope(t, inputs.cameras, inputs.box)) for t in inputs.tracks}
    premises = {}
    for track in inputs.tracks:
        X = truth.points[track.id]
        valid = {o.id: not truth.outliers[o.id] and track_polytope(
            track, inputs.cameras, inputs.box, include_depth=False, keep=[j]).contains(X)
                 for j, o in enumerate(track.observations)}
        for o in track.observations:
            query_agrees = abs(float(inputs.cameras[o.camera_id].camera_points(X)[2])-truth.depths[o.id]) <= 1e-12
            premises[o.id] = (valid[o.id] and query_agrees and
                              sum(not valid[a.id] for a in track.observations if a.id != o.id) <= q)
    by_method = defaultdict(list)
    for record in records:
        by_method[record['method']].append(record)
    output = []
    for method, group in by_method.items():
        ids = [i for r in group for i in r['original_depths']]
        before = np.array([r['original_depths'][i] for r in group for i in r['original_depths']])
        after = np.array([r['depths'][i] for r in group for i in r['original_depths']])
        target = np.array([truth.depths[i] for i in ids])
        edits = after != before
        premise_mask = np.array([premises[i] for i in ids])
        increased = np.abs(after-target) > np.abs(before-target)+1e-10
        improved = np.abs(after-target) < np.abs(before-target)-1e-10
        result = {'scenario': scenario, 'seed': seed, 'method': method, 'tracks': len(group),
                  **depth_metrics(after, target), **repair_metrics(before, after, target),
                  'depth_mae_m': float(np.mean(np.abs(after-target))),
                  'strictly_improved_fraction': float(improved.mean()),
                  'edited_count': int(edits.sum()),
                  'edited_improved_count': int((edits & improved).sum()),
                  'premise_eligible_count': int(premise_mask.sum()),
                  'premise_eligible_fraction': float(premise_mask.mean()),
                  'premise_eligible_edited_count': int((premise_mask & edits).sum()),
                  'premise_eligible_error_increased_count': int((premise_mask & increased).sum()),
                  'conditional_edited_harm_count': int((premise_mask & increased & edits).sum()),
                  'states': dict(Counter(r['state'] for r in group)),
                  'joint_status_after': dict(Counter(r['status_after'] for r in group)),
                  'depth_interval_coverage': float(np.mean([not truth.wrong_claims[i] for i in ids])),
                  'physical_pixel_coverage': float(np.mean([truth.pixel_contained[i] for i in ids]))}
        detected = {i for r in group for i in r['detected']}
        result['individual_refutation'] = binary_metrics([i in detected for i in ids], [truth.wrong_claims[i] for i in ids]) if method.startswith('local') else None
        labels = [numerical_empty[r['track']] for r in group]
        decided = [(r, label) for r, label in zip(group, labels) if label is not None]
        result['group_contradiction_vs_numerical_elastic_reference'] = binary_metrics(
            [r['status_before'] == 'VERIFIED_CONTRADICTION' for r, _ in decided], [label for _, label in decided])
        result['elastic_reference_ambiguous'] = sum(v is None for v in labels)
        widths, hull_contains, certs, traces = [], [], [], []
        for r in group:
            certs.extend(check_artifact(a).accepted for a in r['artifacts'])
            for oid, env in r.get('envelopes', {}).items():
                if env['state'] in {'BOUNDED', 'MEASUREMENT_CONFLICT'}:
                    traces.append(check_envelope(env).accepted)
                for branch in env['evidence']:
                    for key in ('upper', 'negative_lower', 'exclusion'):
                        if key in branch:
                            certs.append(check_artifact(branch[key]).accepted)
                if env['state'] == 'BOUNDED':
                    lo, hi = rational(env['lower']), rational(env['upper'])
                    widths.append(float(hi-lo))
                    hull_contains.append(lo <= rational(truth.depths[oid]) <= hi)
        result.update(certificate_submissions=len(certs), invalid_certificates=sum(not c for c in certs),
                      envelope_traces=len(traces), invalid_envelope_traces=sum(not c for c in traces),
                      envelope_count=len(widths), envelope_width_mean_m=float(np.mean(widths)) if widths else None,
                      envelope_width_median_m=float(np.median(widths)) if widths else None,
                      envelope_contains_reference_fraction=float(np.mean(hull_contains)) if hull_contains else None)
        # Shared readout: average backprojection of each method's reported scalar
        # depths. This adds no repair. Native estimated points are reported apart.
        fused_errors, reproj, inlier_reproj, native_errors = [], [], [], []
        for r in group:
            track = tracks[r['track']]
            changed = Track(track.id, tuple(replace(o, depth=r['depths'][o.id]) for o in track.observations))
            point = average_fusion(changed, inputs.cameras).point
            if point is not None:
                fused_errors.append(float(np.linalg.norm(point-truth.points[track.id])))
                for o in track.observations:
                    uv, _, valid = inputs.cameras[o.camera_id].project(point)
                    if valid:
                        residual = float(np.linalg.norm(uv-o.uv))
                        reproj.append(residual)
                        if not truth.outliers[o.id]:
                            inlier_reproj.append(residual)
            if 'point' in r:
                native_errors.append(float(np.linalg.norm(np.array(r['point'])-truth.points[track.id])))
        times = [r['efficiency']['wall_seconds'] for r in group if r['efficiency']['wall_seconds'] is not None]
        rss = [r['efficiency']['peak_rss_bytes_sampled'] for r in group if r['efficiency']['peak_rss_bytes_sampled'] is not None]
        result.update(fused_point_error_m=float(np.mean(fused_errors)),
                      fused_reprojection_mean_px=float(np.mean(reproj)) if reproj else None,
                      fused_inlier_reprojection_mean_px=float(np.mean(inlier_reproj)) if inlier_reproj else None,
                      native_point_error_m=float(np.mean(native_errors)) if native_errors else None,
                      native_point_count=len(native_errors), wall_seconds=sum(times) if times else None,
                      peak_rss_bytes_sampled=max(rss) if rss else None)
        output.append(result)
    return output


def summarize(rows, boot_seed, boot_count):
    rng = np.random.default_rng(boot_seed)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['scenario'], row['method'])].append(row)
    out = []
    metrics = ['abs_rel', 'depth_mae_m', 'rmse', 'changed_fraction', 'corrected_fraction', 'damaged_fraction',
               'absolute_error_increased_fraction', 'strictly_improved_fraction', 'envelope_width_mean_m',
               'envelope_contains_reference_fraction', 'premise_eligible_fraction', 'fused_point_error_m',
               'native_point_error_m', 'fused_reprojection_mean_px', 'fused_inlier_reprojection_mean_px', 'wall_seconds']
    for (scenario, method), group in sorted(grouped.items()):
        result = {'scenario': scenario, 'method': method, 'seeds': len(group), 'metrics': {}}
        for key in metrics:
            values = np.array([r[key] for r in group if r.get(key) is not None], dtype=float)
            ci = np.quantile(rng.choice(values, (boot_count, len(values)), replace=True).mean(axis=1), [.025, .975]).tolist() if len(values) >= 2 else None
            result['metrics'][key] = {'mean': float(values.mean()) if len(values) else None, 'seed_bootstrap_ci95': ci, 'valid_seeds': len(values)}
        result['totals'] = {key: sum(r[key] for r in group) for key in [
            'count', 'tracks', 'edited_count', 'edited_improved_count', 'premise_eligible_count',
            'premise_eligible_edited_count', 'conditional_edited_harm_count', 'certificate_submissions',
            'invalid_certificates', 'envelope_traces', 'invalid_envelope_traces', 'envelope_count']}
        for name in ['states', 'joint_status_after']:
            result[name] = dict(sum((Counter(r[name]) for r in group), Counter()))
        if group[0]['individual_refutation'] is not None:
            counts = {key: sum(r['individual_refutation'][key] for r in group) for key in ['tp', 'fp', 'fn', 'tn']}
            result['individual_refutation_counts'] = counts
            result['individual_precision'] = counts['tp']/(counts['tp']+counts['fp']) if counts['tp']+counts['fp'] else None
            result['individual_recall'] = counts['tp']/(counts['tp']+counts['fn']) if counts['tp']+counts['fn'] else None
        result['peak_rss_bytes_sampled'] = max((r['peak_rss_bytes_sampled'] for r in group if r['peak_rss_bytes_sampled'] is not None), default=None)
        out.append(result)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='docs/validation/synthetic_config.yaml')
    parser.add_argument('--output', required=True)
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())
    if args.pilot:
        config['seeds'] = config['seeds'][:1]
        config['scenarios'] = config['scenarios'][:1]
        config['base']['tracks'] = 4
    out = Path(args.output)
    identity = {'config': config, 'source_hash': source_fingerprint(Path('src/witness3d')),
                'runner_hash': spec_hash(Path(__file__).read_text())}
    signature = spec_hash(identity)
    if (out/'identity.json').exists() and json.loads((out/'identity.json').read_text())['signature'] != signature:
        raise ValueError('Changed validation inputs/source; use a new output directory')
    atomic_json(out/'identity.json', {'signature': signature, **identity})
    rows = []
    with Profile() as whole:
        for scenario in config['scenarios']:
            controls = {**config['base'], **scenario.get('synthetic', {})}
            for seed in config['seeds']:
                path = out/scenario['name']/f'seed_{seed}'
                inputs, truth = generate(SyntheticConfig(**controls, seed=seed))
                save_inputs(path/'inputs.json', inputs)
                atomic_json(path/'evaluation_truth.json', truth)
                experiment = deepcopy(config['experiment'])
                experiment['seed'] = seed
                experiment['repair']['q'] = scenario.get('q', 0)
                # Circumscribed Euclidean threshold for the same square pixel box.
                experiment['ransac_threshold'] = max(1e-6, np.sqrt(2)*controls['pixel_radius'])
                atomic_json(path/'experiment.json', experiment)
                started = perf_counter()
                records = run_inputs(inputs, experiment, str(path/'run'))
                augmented = records+masked_controls(records)
                metrics = evaluate(augmented, inputs, truth, scenario['name'], seed, experiment['repair']['q'])
                atomic_json(path/'metrics.json', metrics)
                rows.extend(metrics)
                atomic_json(out/'metrics_by_seed.json', rows)
                print(json.dumps({'scenario': scenario['name'], 'seed': seed,
                                  'elapsed_s': round(perf_counter()-started, 3), 'records': len(records)}), flush=True)
    atomic_json(out/'summary.json', summarize(rows, config['bootstrap_seed'], config['bootstrap_replicates']))
    atomic_json(out/'efficiency.json', whole.as_dict())
    print(json.dumps({'complete': True, 'metric_rows': len(rows), **whole.as_dict()}), flush=True)


if __name__ == '__main__':
    main()
