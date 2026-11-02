# Experimental protocol and metric definitions

No measurements exist yet. The following is a prospective protocol. Primary unit of replication: scene; secondary: seed/window within scene. Freeze model weights, input frames, tracks, depth centers and uncertainty widths before comparing methods.

## Stages and hypotheses

1. Analytic systems and synthetic known-pose tracks: exact input-level correctness, sound abstention and q-budget behavior. H1: no invalid exact certificate; a single counterexample blocks release. H2: conditional safe edits never increase absolute optical-depth error when containment assumptions hold. Violations outside assumptions are counted, not hidden.
2. Noise/short-baseline/pose stress: sweep pixel radius, baseline, q, pose perturbation, depth width. H3: envelope width predicts useful correction coverage; if only unrealistically large baselines work, narrow the scope.
3. Pilot metric DA-V2-Small on a few static TUM windows; then vetted registered/calibrated 7-Scenes and sampled ScanNet; ETH3D pinhole subset if export and evaluation references are appropriate. All real-camera guarantees remain conditional.
4. Matched sparse edit budget against robust triangulation, interval triangulation without q, residual clipping, local robust refinement and global reconciliation. H4: lower damage for comparable corrected-error count and CPU cost. If no advantage, do not claim substantial novelty.

Report depth on the same sparse pixel set before/after; also report the full valid reference grid with exact unchanged mask coverage. Sparse gains must not masquerade as dense reconstruction improvements. Report no-alignment metric scores first; optional scale/affine aligned relative-depth scores are separately labeled and fitted on declared calibration points only.

## Metrics (undefined denominators return null)

For valid reference z*>0 and estimate d>0, N samples:

* AbsRel = mean |d-z*|/z*; RMSE = sqrt(mean(d-z*)^2).
* delta_a = mean[max(d/z*,z*/d)<a], a in {1.25,1.25^2,1.25^3}.
* Reprojection = mean Euclidean pixel distance between projection of reconstructed point and measured pixel, only positive projected depths; invalid projection fraction reported separately.
* Multiview inconsistency = mean |z_i(X)-d_i| over evaluated observations; this is a residual, not reference accuracy.
* Point error = mean ||X-X*|| in the declared common metric frame; depth alignment error is unaligned depth RMSE. Alignment transformations must be reported separately.
* Detection precision TP/(TP+FP), recall TP/(TP+FN). A synthetic depth claim is erroneous when z* lies outside its claimed interval. Whole-system truth means no point satisfies the declared system, not merely one erroneous input. Real depth-error labels are proxies and kept separate from exact feasibility labels.
* Incorrect contradiction rate = certified contradictions on systems known feasible / known-feasible systems. Also report false depth-refutation rate among true depth claims. Ground-truth labels for whole-system infeasibility require analytic construction or an independent exact reference oracle, never the solver under test.
* Witness size = number of positive multiplier rows plus, separately, distinct observation blocks; domain support used by residual checking is included in the explanation.
* Localization = set precision/recall and Jaccard between implicated depth claims and labeled wrong claims. Group membership is not individual blame.
* Certificate validity rate = accepted by independent checker / submitted certificates; inconclusive fraction = UNKNOWN / all queries. Empty submission sets yield null.
* Corrected-error fraction = previously erroneous predictions now within a preregistered relative tolerance tau / previously erroneous predictions. Damage = previously within tau now outside tau / previously within tau. These differ from the non-degradation property of absolute error.
* Locality = changed samples / all samples and changed-outside-authorized-mask / outside-mask samples. Also report mean and max change. Zero authorized violations is an engineering property, not an accuracy result.
* Efficiency = wall CPU core-stage time, synchronized GPU inference time, peak RSS and peak allocated GPU bytes. Throughput is tracks/sec at fixed views/q/extraction settings. Improvement/overhead uses paired error difference and seconds; do not divide by near-zero runtime.

Macro-average per-scene metrics; average repeated seeds/windows within scene first. Report number of scenes and valid counts; bootstrap scenes, keeping method pairs intact, for uncertainty intervals. Do not treat correlated pixels as independent trials. Seed lists and splits are materialized in configurations. No significance claim from a tiny pilot.

## Baseline matrix

No repair; depth-to-world weighted averaging; residual thresholding; linear/robust triangulation; seeded pair-RANSAC with robust refit; fixed-camera robust least squares; anchored pose/point BA-style least squares as a diagnostic with changed information explicitly disclosed; detection-only; repair-all without witness localization; uniform versus confidence weighting; q=0 versus q>0 conservative union; numerical-only versus checked certificates. Baseline implementations are generic references, not reproductions of CARVE, Self-Geometry, TEASER, COLMAP or C-3PO.

## Anti-gaming controls

Keep detection and accuracy metrics at fixed uncertainty widths and measured empirical coverage. Larger intervals mechanically reduce contradictions. Plot refutation/coverage/width/accuracy together; record domain bounds, q, z_min, discarded matches and abstention. Do not choose intervals per-method from evaluation depth. Geometry-only calibration for relative models uses separate track IDs, and calibration failure is not silently replaced with reference alignment. Compare the same edit count and the same inlier oracle access. Ablations expose all required axes and record a run-spec hash; changing a spec invalidates resume.
