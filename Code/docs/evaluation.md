# Evaluation and reporting contract

Definitions were written before code in `../../Theory/experimental_protocol.md`. All results are absent until future execution. The artifact contains no generated plots or numeric benchmark tables.

`metrics.py` implements metric optical-depth AbsRel/RMSE/delta thresholds, invalid-prediction accounting, binary detection/localization counts, point error, reprojection/depth consistency residuals, certificate/UNKNOWN statistics, corrected/damaged fractions and repair locality. Scene aggregation first averages windows/seeds within each scene, then macro-averages scenes. Paired scene differences and scene-bootstrap intervals are available; a single synthetic scene has no meaningful multi-scene confidence interval and returns null.

Three truths must be separated: input-level whole-system feasibility, a depth interval containing the reference target depth, and a chosen accuracy tolerance for prediction centers. An erroneous interval need not make the full system infeasible, and a consistent center need not be accurate. Do not label all tracks containing an injected error as analytically infeasible. Known-feasible synthetic labels are established by directly checking the exact encoded system at its separately supplied true point; all other whole-system labels remain unknown without an analytic/reference proof.

The default real evaluator deduplicates (method, frame, pixel). If repeated tracks propose different values at a pixel, it retains the original value. Materialization uses the same all-conflicts-rejected policy. Its float64 output preserves original values elsewhere without narrowing a certified float64 correction. Sparse edits are not dense learned completion.

To score the entire reference grid after materializing a method:

```bash
python -m witness3d evaluate-dense --manifest /path/to/manifest.json --sampling /path/to/tracks/sampling.json --depth-index /path/to/repaired_depth/index.json --output /path/to/dense_metrics.json
```

Dense metrics and sparse metrics must appear under distinct labels. Dense invalid-prediction counts, edited-pixel fraction and full-grid damage are mandatory when claiming whole-map effects. Calibration and world boxes cannot use reference depth. Relative models use independently triangulated disjoint calibration frames and report that extra information.

Certificate size reports positive multiplier rows and distinct observation blocks. Residual corrections can additionally use the world box, so box involvement must be disclosed; a small explicit y-support alone is not a complete physical explanation. Group suspects are scored as localization heuristics, whereas `detected` holds individually refuted depth claims only. Witness-only whole-system contradictions have no automatic individual detection label. Complete envelope traces validate branch coverage, common domain, consistent observation rows, no model-depth rows and support/exclusion arithmetic. They still certify the encoded problem, not physical calibration.

Efficiency records are unmeasured until execution. Per-record wall/CPU timing excludes the initial shared before-status solve; `run_efficiency.json` includes shared queries, all selected methods and run I/O. GPU cache records use synchronized timing. For fair total compute comparisons, include manifest preprocessing and matching as separate stages as well. Run one method per fresh isolated run directory when comparing total method runtimes, disclosing shared-work policy; resumed/cache-hit times are not fresh solver runtimes.

Interval-width, coverage, q, domain bounds, z_min and abstention must accompany detection rates. The supplied ablation planner records width/radius changes and flags non-comparability. Run matched edit-budget comparisons externally from saved record edit counts; do not select thresholds on held-out reference depth.
