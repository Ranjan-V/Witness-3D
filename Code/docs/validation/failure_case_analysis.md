# Failure cases and scientific implications

## Valid certificates can accompany harmful physical repairs

The all-target selective method made 882 edits across the 28-scenario sweep: 876 reduced absolute error and six increased it. None of the six satisfied the evaluated W1 premises. There were 753 premise-eligible edits with zero observed increases. The original localized method added three duplicate harm observations across the same stress tracks; `observed_harm_examples.json` preserves all nine method/observation records and source paths.

Examples from actual runs:

| Case | Original = true depth | Repaired depth | Actual error introduced |
|---|---:|---:|---:|
| Gaussian noise 0.75 px, seed 23, observation 1:0 | 4.5 m | 4.369395599 m | 0.130604401 m |
| Gaussian noise 0.75 px, seed 37, observation 3:0 | 4.5 m | 4.651067337 m | 0.151067337 m |
| Pose translation sigma 0.01 m, seed 23, observation 7:0 | 4.5 m | 4.651429604 m | 0.151429604 m |

All these certificates remained arithmetically valid. The first noise examples violate asserted pixel containment; the pose example uses an incorrect physical depth query/camera model. One noise-damaged target itself has a contained pixel while an auxiliary does not, demonstrating why target containment alone is insufficient. All six increases stayed below the 5% “damaged” classification threshold; therefore the sweep's zero 5%-damage rate for selective repair must **not** be reported as zero harm.

Analytical CPU counterexamples make the effect larger (`explicit_counterexamples.json`): with true target depth 2 m, an auxiliary ray shifted to imply depth 4 m and q=0 yields 3.999680026 m; a doubled supplied baseline yields 3.999840006 m. Both repaired systems are verified feasible. Allowing q=1 with only two views produces no edit because every auxiliary can be removed. A 2 px auxiliary error outside a 0.001 px asserted radius produces 2.083246531 m from a correct 2 m prediction. These refute unconditional non-damage and consistency-implies-accuracy, not conditional W1.

## Localization and marginal feasibility

In the reference scenario, original local localization repairs 35 of 47 false intervals, leaving 12 undetected; ten of forty tracks remain contradictory. One conflict is not an enumeration of every bad claim. local_all repairs all 47, and all forty reference tracks become feasible, but this does not establish a general joint-feasibility theorem.

The adversarial proper-camera fixture has depths (s,0.6s+1), s in [1,2]. Predictions (2,1.6) each belong to their marginal envelope, but no common point realizes both. The code returns a checked contradiction and performs no local scalar edit. A multiview point-error guarantee does not follow from marginal depth non-increase.

## Weak geometry and excess conservatism

Zero baseline and pure rotation yielded no selective edits. With three views and q=2, mean computed envelope width was 9.9 m and no edits were justified. Reducing baseline from 0.3 m to 0.03 m increased mean width from about 0.165 m to 1.750 m; all-target AbsRel was 0.10443 versus triangulation's 0.02994. Radius 2 px gave all-target AbsRel 0.03577. Relative depth half-width 0.4 covered the biased depths, so the method correctly declined to refute intervals even though the centers remained inaccurate.

## Baseline failures are retained

Unbounded Huber reprojection estimates can diverge toward very large depths in outlier/scale-degenerate cases: the 10% outlier scenario produced mean AbsRel 4838.13 for that generic baseline. This exposes the ill-posed unbounded fitting problem; it is not evidence of Witness3D superiority over strong robust geometry. RANSAC was much stronger. A separate post-hoc bounded-control experiment constrains robust estimates to the same world box; its records/results are kept separately and cannot replace the predeclared sweep silently.

Global reconciliation produced 848 numerically converged, 268 abstained and four nonconverged track records. Its block-of-four policy means one infeasible pixel track can force abstention for its block. On nonconvergence/abstention the evaluation retains original depths. The Huber minimizer's existence theorem does not imply the implemented capped optimizer always converges or improves truth.

## Empirical value and limitation

There is real selective-correction value under favorable synthetic geometry: large biased depths improve while exact original depths remain unchanged. Yet triangulation has lower reference accuracy error, and triangulation on the same selective mask improves further with the same observed preservation on this sample. The guaranteed worst-case contract distinguishes the endpoint update; an empirical accuracy/damage advantage over matched strong geometry is not established. The deliberately exact/bias-mixture predictions make preservation especially visible and are not a realistic pretrained error distribution.
