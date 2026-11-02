"""Summarize Phase 3 executed diagnostics without altering earlier artifacts."""
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from witness3d.io import atomic_json

out=Path('docs/phase3');a=json.loads((out/'mask_summary.json').read_text())
look={(r['scenario'],r['candidate'],r['selector'],r['budget_scope']):r for r in a}
lines=['# Equal-budget mask replay: all 28 scenarios','','All scalar observations remain in the evaluation population. Ranking thresholds are chosen to match Witness3D’s edit count, without labels. The count is shared side information; this is not an independently calibrated deployment threshold. Every selector uses the same DLT replacement values. Failed/no-op replacement slots are excluded identically before matching counts; full-population Witness3D mask statistics are shown separately. Random results average 32 draws per seed. Undefined values are —.','','| Scenario | W precision | W recall | W FPR | W mask + DLT | Depth disagreement + DLT | RANSAC disagreement + DLT | Random + DLT |','|---|---:|---:|---:|---:|---:|---:|---:|']
def fmt(x):return '—' if x is None else f'{x:.6f}'
wins=defaultdict(int)
for s in sorted({r['scenario'] for r in a}):
    w=look[(s,'mask_only','witness','full_population')]
    vals=[look[(s,'triangulation',sel,'both' if sel=='witness' else 'case')]['abs_rel'] for sel in ['witness','depth_disagreement','ransac_depth_disagreement','random']]
    lines.append('| '+s+' | '+' | '.join(fmt(x) for x in [w['precision'],w['recall'],w['fpr']]+vals)+' |')
    d=vals[1]-vals[0]
    wins['disagreement_better' if d < -1e-12 else ('witness_better' if d > 1e-12 else 'equal')]+=1
lines+=['','## Reference selector comparison (same DLT values, same case edit count)','','| Selector | AbsRel | Precision | Recall | FPR |','|---|---:|---:|---:|---:|']
for r in a:
    if r['scenario']=='reference' and r['candidate']=='triangulation' and r['budget_scope'] in ['case','both']:
        lines.append('| '+r['selector']+' | '+' | '.join(fmt(r[k]) for k in ['abs_rel','precision','recall','fpr'])+' |')
lines+=['','Both per-case and per-track budgets, DLT and RANSAC replacement estimators, every selector and all seeds/draws are in mask_results.json and mask_summary.csv. Confidence is constant 1 in Phase 2, so low-confidence selection is a randomized tie, not an informative model confidence baseline. Scores named depth disagreement are normalized by the supplied half-width. Reprojection and RANSAC-outlier scores identify different failure types from inaccurate model depths; their disagreement-based versions are included as the stronger depth-repair selectors.']
(out/'mask_comparisons.md').write_text('\n'.join(lines)+'\n')
stress=json.loads((out/'stress/mask_results.json').read_text());summary=[]
lines=['# Continuous-error difficult-regime controls','','Five seeds, 12 tracks/seed, five available cameras. Partial occlusion means missing observations, not rendered boundaries. Width is 3% of prediction. Shared observations and all-population evaluation. These are controlled falsification cases, not realistic imagery or significance tests.','','| Scenario | Original | DLT all | RANSAC all | W repair | W mask + DLT | Depth disagreement + DLT | W mask + RANSAC | RANSAC disagreement + RANSAC |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for s in sorted({r['scenario'] for r in stress}):
    full=defaultdict(list)
    for case in (out/'stress'/s).glob('seed_*'):
        truth=json.loads((case/'evaluation_truth.json').read_text())['depths']
        rec=[json.loads(line) for line in (case/'run/records.jsonl').read_text().splitlines()]
        for method in ['none','triangulation','ransac','local_all']:
            group=[r for r in rec if r['method']==method]
            full[method].append(np.mean([abs(v-truth[k])/truth[k] for r in group for k,v in r['depths'].items()]))
    vals=[float(np.mean(full[k])) for k in ['none','triangulation','ransac','local_all']]
    for candidate,selector,scope in [('triangulation','witness','both'),('triangulation','depth_disagreement','case'),('ransac','witness','both'),('ransac','ransac_depth_disagreement','case')]:
        vals.append(float(np.mean([r['abs_rel'] for r in stress if r['scenario']==s and r['candidate']==candidate and r['selector']==selector and r['budget_scope']==scope])))
    lines.append('| '+s+' | '+' | '.join(fmt(x) for x in vals)+' |')
    summary.append({'scenario':s,**dict(zip(['original','dlt','ransac','witness_repair','w_mask_dlt','disagreement_dlt','w_mask_ransac','disagreement_ransac'],vals))})
(out/'stress_comparisons.md').write_text('\n'.join(lines)+'\n')
atomic_json(out/'stress_summary.json',summary)
mechanism=json.loads((out/'mechanism_results.json').read_text());ms=[]
for mode in sorted({r['mode'] for r in mechanism}):
    g=[r for r in mechanism if r['mode']==mode]
    for method in ['photometric','joint_photo_geometry','certificate_conflict_filter']:
        usable=[r for r in g if r['results'][method]['depth'] is not None]
        ms.append({'mode':mode,'method':method,'cases':len(g),'returned':len(usable),
                   'conditional_abs_rel':float(np.mean([abs(r['results'][method]['depth']-r['truth'])/r['truth'] for r in usable])) if usable else None,
                   'abstained':len(g)-len(usable)})
atomic_json(out/'mechanism_summary.json',ms)
atomic_json(out/'headline_results.json',{'scenario_comparison_dlt_disagreement':dict(wins),
      'replay_case_seeds':140,'stress_case_seeds':35,'stress_tracks':420,
      'mechanism_cases':160,'mechanism_assignment_disagreements':sum(r['results']['joint_photo_geometry']['choice']!=r['results']['certificate_conflict_filter']['choice'] for r in mechanism)})
print(dict(wins));print(json.dumps(summary,indent=2));print(json.dumps(ms,indent=2))
