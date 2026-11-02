# Witness3D Phase 3: RETIRE

**Retire Witness3D as a CVPR main-track candidate.** Preserve it as a tested certificate/robust-set-estimation reference. The strongest apparent empirical finding is reproduced by a simple conventional selector; the difficult-regime controls and the one examined image-conditioned rescue mechanism provide no compelling original algorithmic contribution. This is a decision about this formulation, not a claim that selective estimation or certifiable perception has no research value.

## Why the reference mask wins

The original generator emits exactly correct depths or a large positive multiplicative bias. Full triangulation improves the biased values but introduces small noise into the exact ones. The Witness3D mask selects all 47 false intervals and preserves all 73 exact depths in the 120-depth reference population. Applying triangulation only to that mask removes the noise introduced on the 73 exact values. Every depth remains in the evaluation denominator.

The difference between full triangulation's 0.0029905932 AbsRel and masked triangulation's 0.0011379296 is **0.0018526636**, exactly the contribution removed by preserving unselected originals. This is a selection effect, not improved triangulation. A normalized prediction-versus-triangulation disagreement score reproduces that same mask, precision 1, recall 1, FPR 0, and **the identical 0.0011379296 AbsRel**. Robust- and RANSAC-depth disagreement also reproduce it. Per-track uncertainty ranking does too, because proportional widths expose the large positive bias within each equal-depth track.

No ground-truth file access was found in the inspected mask/inference paths. However, the synthetic exact/gross-bias mixture, proportional widths, known cameras, low pixel noise and confidence=1 favor simple detection. The mask-sharing diagnostic receives Witness3D's computation, not an independent cheap selector or an oracle truth mask. [Audit and full protocol](audit_and_protocol.md).

## All 28 original scenarios

The replay covers all five saved seeds in all 28 scenarios, 1,120 tracks and 3,360 scalar depths per estimator. It evaluates nine conventional selectors plus Witness3D, DLT/RANSAC replacement values, both per-case/per-track equal actual edit counts, and 32 random draws per seed. All inputs and evaluation populations are shared. Failed/no-op candidate slots are accounted for identically; full Witness3D mask statistics are reported separately.

At equal case budgets with common DLT replacements, conventional depth-disagreement selection ties Witness3D in **20 scenarios**, is better in **four**, and is worse in **four**. The four Witness3D wins are correspondence-contamination cases where raw DLT disagreement can be misleading. These localized wins do not establish superiority over robust geometry: RANSAC-based depth disagreement and RANSAC estimation are included as stronger controls. Zero-budget ties mean shared abstention, not successful reconstruction.

Full precision, recall, false-positive rate and repair improvement data for every scenario/selector are in [mask comparison tables](mask_comparisons.md), [CSV](mask_summary.csv), and [raw per-seed/draw results](mask_results.json). Example reference results:

| Selector, common DLT replacements and edit budget | AbsRel | Mask precision | Recall | FPR |
|---|---:|---:|---:|---:|
| Witness3D | 0.001138 | 1.0000 | 1.0000 | 0 |
| Depth disagreement | 0.001138 | 1.0000 | 1.0000 | 0 |
| Robust-depth disagreement | 0.001138 | 1.0000 | 1.0000 | 0 |
| RANSAC-depth disagreement | 0.001138 | 1.0000 | 1.0000 | 0 |
| Fusion reprojection threshold ranking | 0.146865 | 0.2553 | 0.2553 | 0.4795 |
| Robust reprojection ranking | 0.105279 | 0.4681 | 0.4681 | 0.3425 |
| RANSAC outlier flag | 0.097023 | 0.5106 | 0.5106 | 0.3151 |
| Predicted uncertainty magnitude | 0.055398 | 0.7234 | 0.7234 | 0.1781 |
| Low supplied confidence (all tied) | 0.097023 | 0.5106 | 0.5106 | 0.3151 |
| Random, averaged across draws | 0.117447 | 0.4063 | 0.4063 | 0.3823 |

These rankings diagnose different kinds of error; correspondence residual alone is not a strong model-depth-error selector. The strong disagreement variants prevent this from becoming a comparison against only weak residual baselines. Shared edit counts are experimental side information available to every selector, not a deployable calibration rule. No significance is claimed from scenario win counts or repeated random draws.

## Difficult regimes with continuous prediction error

Seven additional modes x five seeds x twelve tracks = **420 track instances**, with five available views. Predictions have continuous log-depth error and signed gross errors; no exact-depth atom. Uncertainty is 3% of prediction. Occlusion is represented by missing views only. Heterogeneous localization quality and misleading confidence are explicitly controlled. Full saved inference/evaluation inputs and records are in stress/.

| Regime | Original | DLT all | RANSAC all | Witness3D repair | Witness mask + RANSAC | RANSAC disagreement mask + RANSAC |
|---|---:|---:|---:|---:|---:|---:|
| Continuous errors | 0.13621 | 0.00187 | 0.00187 | 0.02310 | 0.01073 | 0.01068 |
| 20% contamination | 0.13621 | 0.45551 | 0.00212 | 0.06487 | 0.05844 | 0.02949 |
| Camera translation uncertainty | 0.13621 | 0.00802 | 0.01072 | 0.12101 | 0.12037 | 0.10802 |
| Missing auxiliary views | 0.14607 | 0.00199 | 0.00199 | 0.06447 | 0.04870 | 0.02378 |
| Heterogeneous view quality | 0.12589 | 0.01930 | 0.00785 | 0.06191 | 0.03628 | 0.03410 |
| Misleading model confidence | 0.13621 | 0.00187 | 0.00247 | 0.02310 | 0.01111 | 0.01111 |

Full-estimator outputs edit more observations than the mask controls; both comparisons are reported, not conflated. At equal budgets the conventional selector generally matches or improves the corresponding robust-estimator control here. Under contamination, switching to a robust estimator matters far more than preserving the original mask.

Near-zero baseline genuinely fails: raw DLT AbsRel 0.40090; unbounded RANSAC refinement runs away to 181.76835. Witness3D abstains and retains the original 0.13621. This is not accepted as a win over deliberately weak triangulation: a separately executed conventional parallax/domain guard at .5 degrees also retains 0.13621. All guard thresholds .1/.5/1/2 degrees are recorded, with original outputs retained. The guarded RANSAC results in the other six modes equal the strong RANSAC rows above. No new metric depth is recovered from inadequate parallax by Witness3D. [Stress tables](stress_comparisons.md), [all guard results](condition_control_results.json).

The original Phase 2 bounded robust controls remain unchanged. These are generic reference baselines, not exhaustive best-in-class implementations. No claim of beating an optimized MVS system is made. The finite-world-box and abstention options are available to conventional methods as well as Witness3D.

## Research rescue proposal gate

One distinct candidate was examined: using shared geometric conflicts to guide counterfactual image association search and additional patch comparisons. Its formulation, closest prior work, proposed new component, desired nontrivial theorem, counterexamples, falsifiable hypotheses and fair baselines are in [novelty/proposal assessment](novelty_and_proposal.md).

The minimum experiment gave identical candidate assignment choices for conventional photometric/geometric feasibility and certificate filtering in **160/160 cases** across 40 seeds per mode. Under repeated texture both had mean AbsRel 0.3675. With an absent true correspondence and the same wrong all-view constraint both had 0.7. The latter is a counterexample to that constraint, not evidence against visibility-aware robust MVS. No adaptive search speedup was implemented or claimed. Raw outcomes are in [mechanism results](mechanism_results.json), with [summary](mechanism_summary.json).

Shared conflict recording already belongs to constraint learning; photometric/geometric hypothesis and visibility selection already belong to MVS. A new image-query/complexity result would be needed to distinguish the proposed mechanism. None is established. The measured equivalence defeats an estimation novelty claim; a speculative unmeasured computational gap does not meet RESCUE's high threshold. No second proposal is labeled novel to fill a quota.

Phase 3 supplies classical masked-error and constrained-selection identities, plus identifiability counterexamples; **no original nontrivial theoretical claim**. Certificates authenticate deductions from the supplied evidence, but add no missing image/pose/parallax observations. They may have engineering/auditing value without supporting a new vision algorithm.

## Validation, preservation and next problem

Latest suite: **114 passed, zero failed/errors/skipped**, including five Phase 3 diagnostic tests. [Actual test log](tests.txt), [JUnit](tests.xml). The 109 earlier cases remain present. Phase 2 implementation/results were preserved; Phase 3 adds diagnostic scripts/tests/reports and CPU outputs. No repair optimization, training, model inference, dataset download, GPU/TPU, Kaggle or Paper editing occurred. Environment and source identities are recorded in integrity.json; executable commands are in the protocol.

The original mask replay took 7.384 s; difficult-regime experiments 112.368 s with sampled peak memory about 132.16 MiB. These finite synthetic controls do not establish behavior on real imagery. Their negative findings are sufficient to withhold rescue, not to prove that no future visual estimation method can improve on robust geometry.

**Recommend a different problem:** study *which independent measurements or controlled interventions make camera/calibration faults distinguishable from scene motion and correspondence errors*. Begin with an identifiability question across timestamped camera/IMU/rig observations, construct indistinguishable fault pairs, and determine what extra sensing breaks them. Establish the novelty gap and measurement protocol before authoring another method. This is a proposed problem investigation, not a claim that fault diagnosis itself is new. Do not rename the existing mask/certificate pipeline as that contribution.

**RETIRE — no compelling substantial original vision contribution or realistic evidence-backed main-track rescue is established.**
