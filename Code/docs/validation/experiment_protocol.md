# Executed Phase 2 protocol

Scope: local CPU synthetic geometry only. No GPU/TPU, training, pretrained inference, external dataset processing/download, Kaggle execution, or Paper edits. The runs use one BLAS/OpenMP thread per process. The host has 12 physical cores and 16,782,307,328 bytes RAM; see `environment.json`. Two short numerical-audit/scaling processes overlapped part of the main sweep, so recorded wall times are practical observations, not isolated hardware benchmarks.

## Design fixed before the sweep

`synthetic_config.yaml` defines 28 scenarios, seeds 11/23/37/53/71, and eight tracks per seed: 1,120 track instances, each supplied identically to nine methods. There are also two matched-mask diagnostics. The reference has three parallel cameras spaced 0.3 m apart, points on z=3 or z=4.5 m planes, uniform independent pixel noise in +/-0.2 px, declared +/-0.5 px rectangles, 35% probability of a 1.5x depth bias, and depth half-width 2% of the prediction. Bias and outlier Bernoulli draws give realized fractions different from nominal values. These are small controlled scenes, not realistic image reconstructions.

The sweep varies views, baseline, bias, pixel radius, interval width, correspondence outlier probability, q, pose translation/rotation noise, Gaussian image noise and track length. The five-camera track-length cases randomly select two or three cameras; the five-view case uses all five. Random seeds match methods exactly within a case. A change in generator dimension can change subsequent random draws, so different-view scenarios are not paired point-for-point. There is no full factorial interaction analysis or statistical significance claim.

## Methods and fairness

| Label | Information / behavior |
|---|---|
| none | Original scalar predictions, no edits. |
| fusion | Confidence-weighted mean of predicted-depth backprojections. |
| triangulation | Homogeneous fixed-camera multiview DLT; degeneracy/behind-camera failures preserve predictions. |
| robust_triangulation | Huber reprojection refinement; may initialize from depth fusion if triangulation fails. |
| ransac | Deterministic pair sampling, reprojection consensus, robust inlier refinement. |
| robust_depth | Huber reprojection plus prediction residuals scaled by their fixed half-widths. |
| local | Witness3D's original single-conflict localization followed by conditional envelope repair. |
| local_all | Same certificate/envelope rules, examining every target. |
| global | Fixed-camera constrained Huber/ridge/graph baseline, blocks of four tracks; preserve predictions on failure/nonconvergence/abstention. |
| *_on_selective_mask | Replace only local_all's edited entries with triangulation or robust-triangulation values. These share Witness3D's mask and cost; they are diagnostics, not independent competitors. |

All methods receive the same cameras, pixel centers, radii, predicted depths and widths. No method receives reference geometry or labels. RANSAC uses sqrt(2)*pixel_radius as its Euclidean threshold, the circumradius of the square rectangle. Robust least squares retains the original implementation's 0.5 px soft-scale floor; thus the deliberately undersized 0.1 px box scenario is explicitly a miscalibration stress case, not an identical-hard-feasible-set comparison. DLT ignores uncertainty, as ordinary DLT does. No exact reproduction of a named published method is claimed. The global graph is image-derived and its weights are uniform confidence values in this generator. No GT tuning or best-seed selection is used.

No new correction method is substituted. The original single-conflict localization is retained even when it misses other erroneous targets, so its limitation remains measurable. Fixed depth widths, box and positivity requirements remain unchanged across methods within a case.

## Metrics and their denominators

All original observations count in scalar accuracy, including preserved predictions after failures. MAE is in meters; AbsRel is mean |d-z|/z. “Correct” and “damaged” use a 5% relative-error threshold: corrected fraction is wrong-before becoming correct divided by wrong-before; damaged fraction is correct-before becoming wrong divided by correct-before. Strict error-increase and strict improvement are separately counted (1e-10 threshold in premise diagnostics, 1e-12 in the existing general metric). Undefined fractions are null, not zero.

The shared 3D readout averages backprojections of each method's reported depths. Its point and reprojection errors are **evaluation readouts**, not a claim that scalar repair returns a unique reconstruction. Native point estimates are evaluated separately with their successful-point count. Reprojection means against all observed pixels can include corrupted correspondences; an inlier-only readout is also recorded. Failure-preserving scalar errors and success-only native-point errors must not be conflated.

Individual refutation precision/recall compares edited/refuted depth intervals with latent reference-depth interval membership. Group contradiction precision/recall is compared separately against an elastic four-variable numerical LP with normalized rows: optimal slack >1e-7 is labeled empty, <=1e-9 labeled feasible, intermediate/failed queries unclassified. This is a numerical cross-check, **not an exact oracle**. A separate exact bounded-polytope vertex oracle validates small systems. Neither “some incorrect depths” nor “some bad correspondences” is treated as a logically sufficient label for infeasibility.

Every saved direct certificate, branch support/exclusion certificate and complete envelope trace is rechecked. Invalid-certificate frequency counts submitted arithmetic artifacts; duplicated systems across targets/methods remain submissions, not independent trials. Abstention and UNKNOWN are not invalid certificates.

Envelope widths and containment concern computed bounded envelopes only. Scenarios with no tested targets or measurement conflicts have null widths; do not interpret null as zero width. The reported premise-eligible fraction is an evaluation diagnostic requiring an inlier target, encoded pixel containment of X*, target depth-query agreement within 1e-12, and <=q bad auxiliaries. It is unavailable at inference and is not a deployable trust detector. For synthetic corrupted correspondences, the reference is the latent intended track point; no rendered surface at the random wrong pixel is supplied.

## Uncertainty, runtime and reproducibility

Each scenario has five seed replicates. Summary intervals are 2,000 percentile-bootstrap resamples of seed-level means (bootstrap seed 20261102). They reflect generator/seed variability only and can be unstable with five replicates. They are not population confidence guarantees, real-scene CIs, or evidence of significance. Per-scenario pairing is retained for method-difference analysis; cross-scenario means are not a performance ranking.

Per-method times include each record's work and numerical postchecks but exclude the shared initial status query and outer JSON serialization. Global solves are charged to the first track in a four-track block; later records read the same cached solution. Total run profiles include all inference methods, shared work and I/O. The overall sweep includes generation, evaluation, certificate rechecks and result writes. RSS is process memory sampled every 20 ms, including imports and retained records; it is not exact peak allocation or incremental method memory. No GPU memory is queried.

Each case saves input JSON, separate evaluation truth, experiment configuration, source/environment/run signatures, atomic per-track checkpoints, full envelope evidence and per-seed metrics. Source changes force fresh run directories. `metrics_by_seed.json` and `summary.json` contain actual results only. A four-track one-seed pilot is separate and excluded from sweep statistics.

## Executed post-hoc bounded controls

After the main sweep exposed runaway unbounded robust estimates, two additional Huber least-squares controls constrained points to the identical finite world box. They reused all 1,120 saved input tracks, with no GT fitting or hyperparameter tuning. All 2,240 outputs were finite and within the box, and all reported numerical convergence. The new results are in `results/bounded_controls/`, with comparisons in `bounded_baseline_comparisons.md`; the predeclared sweep was not replaced. This exploratory control demonstrates that the method comparison does not depend on arbitrarily large unbounded estimates. It still does not establish a state-of-the-art robust baseline or a statistical significance claim.
