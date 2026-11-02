# Leakage audit, fairness and reproducibility

## Source paths reviewed

Read generator `src/witness3d/synthetic.py`, inference dispatch `experiments.py`, point estimators `baselines.py`, mask construction `repair.py`, depth-free union `envelopes.py` (Phase 2 review plus current call graph), input serialization `io.py`, and Phase 2 `scripts/validate_synthetic.py` including masked_controls/evaluate. Inference accepts Inputs, never Truth. local_repair uses the full prediction system as a gate, then depth-free target envelopes; its **bounds**, not its entire edit mask, are prediction-independent. The gate can change mask coverage. No path inspected reads evaluation_truth.json during inference. Tests poison/alter truth and verify selector invariance, in addition to existing reference-access tests. This is source review and finite checks, not a formal noninterference proof of every possible Python execution.

Phase 2 matching is synthetic correspondence input, not image extraction or neural inference. Model predictions are generated from truth in the controlled generator, as required for known-error experiments. That is not hidden inference leakage, but the reference mixture (exact truth or 1.5x truth) is unusually favorable. Positive-only gross bias, parallel camera depths, two planes, fixed clean cameras, tiny bounded noise, widths proportional to prediction, constant confidence and a finite scene box simplify selection. Width magnitude itself encodes some bias information. Every relevant baseline has access to these inputs. None should be called an image-conditioned estimator based on the original 28 scenarios: those inputs contain no image patches.

The Phase 2 mask-matched methods replace only selected values and keep the entire population in depth evaluation. They receive Witness3D's mask (and therefore its computation) for free in the diagnostic, not GT. They are not independent faster methods. Native point metrics use successful point subsets and cannot be compared as if they had identical coverage; Phase 3 conclusions use full-population scalar errors, including fallbacks. Wrong correspondences' reference is the latent intended track point, not the actual surface at a random mismatched pixel. This limits physical interpretation under occlusion.

## Equal-budget experiment

Reused all 140 saved case/seeds from all 28 scenarios; 1,120 tracks and 3,360 scalar depths per estimator. Nine selectors: fusion reprojection score, DLT disagreement, robust-triangulation disagreement, robust reprojection score, RANSAC outlier flag, RANSAC depth disagreement, predicted width, supplied confidence, and random. Witness3D is the comparator. All disagreement scores divide by the original half-width. Reprojection rankings implement budget-matched quantile thresholds, with high residual selected. Neither true errors nor labels determine thresholds or rankings.

DLT and RANSAC replacement depths are the unchanged saved Phase 2 outputs, including original-depth fallbacks. Selection is restricted identically to actionable finite positive candidate changes; Witness3D's actionable count sets K. Both per-case and per-track K are evaluated. Thus exact actual edit counts match for every selector; no-op/failed slots do not masquerade as edits. requested_witness_count is retained separately. Full-population unfiltered Witness3D mask precision/recall/FPR are also reported. This shared budget is an experimental control rather than a deployable method for choosing K. Per-track budgets additionally share information about which tracks merit editing and are labeled accordingly.

Ties are shuffled deterministically without GT. Constant-confidence scores have no information; they tie-break randomly. Random uses 32 draws per seed. Those draws are not independent scene replicates, and repeated confusion counts in random aggregates must not be interpreted as 32x more data. Seed-level results are retained. No statistical significance is claimed; scenario means are descriptive. Empty selections have null precision; recall is zero when false intervals exist. Correct_predictions/depth_width_0p4 can have undefined recall when no false interval exists. Improvement rates use the Phase 2 5%-relative-error definition; strict error changes are separately retained. The mask labels are false **intervals**, not merely nonzero center error.

## Additional difficult-regime controls

35 case/seeds, 420 tracks, five cameras and continuous log-depth error: N(0,.08^2) plus a signed .35 term with probability .25. Reference depths are no longer an exact-versus-gross-bias mixture. Width is 3% of prediction. Modes: continuous control, near-zero baseline .001 m, 20% contamination, .01 m camera translation sigma, missing auxiliary views, heterogeneous pixel noise/radii/confidences, and deliberately misleading prediction confidence. Five seeds remain 11/23/37/53/71. Missing views simulate one aspect of partial occlusion; no rendered boundaries, visibility segmentation or real image occlusions are claimed.

Geometry runs none/DLT/RANSAC/local_all, q=1. All see identical inputs. Per-view quality is available through the same confidence/radius fields. The existing RANSAC is retained at its 2 px threshold; in the heterogeneous case a stronger scale-normalized implementation could do better, so no optimality claim is made. Main conclusions use cases where conventional geometry wins, not advantages against its failure modes. Phase 2 bounded robust controls remain available, unchanged.

A separately labeled post-hoc conventional control rejects points outside the same world box or with maximum observed inter-ray angle below .1/.5/1/2 degrees. All thresholds are saved; none uses evaluation truth. The report quotes .5 degrees as an illustrative guard, not a tuned optimum. This prevents the raw near-zero RANSAC runaway estimate from being used as a weak comparison. Both DLT/RANSAC can abstain and retain the original prediction, just like Witness3D.

## Executed commands

From D:/CVPR/Code, use .venv-validation/Scripts/python.exe with PYTHONPATH=D:/CVPR/Code/src; CUDA_VISIBLE_DEVICES=-1; OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1. Set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 for pytest. All packages were already local. Commands executed:

```
python scripts/phase3_mask_audit.py
python scripts/phase3_stress.py
python scripts/phase3_mechanism.py
python scripts/phase3_condition_control.py
python scripts/phase3_report.py
python -m pytest -q --junitxml=docs/phase3/tests.xml
```

The candidate generator was corrected before reporting to place the decoy along the actual target-camera ray (not the world-origin ray), then rerun. No favorable run was selected. Code, results and logs are preserved under scripts/phase3*, tests/test_phase3_diagnostics.py and docs/phase3*. Raw Phase 2 code/results remain unchanged. Package/environment versions remain those recorded in docs/validation/environment.json. CPU replay took 7.384 s; continuous stress took 112.368 s with sampled peak RSS 138,575,872 bytes. Remaining timings are not claimed as isolated benchmarks. No downloads, training, model inference, GPU, Kaggle or Paper edits occurred.
