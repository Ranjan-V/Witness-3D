# Witness3D Phase 2 — validation report

Completed 2026-11-02. **Research decision: NO-GO for the unchanged CVPR contribution claim.** The conditional arithmetic/geometry core survived this validation, but the current formulation has not established sufficient practical advantage or novelty. This is a research-gate decision, not a claim that the core theorem is false or that the tests failed.

Only local CPU tests and synthetic experiments were executed. No network package installation, pretrained inference, training, GPU/TPU, external dataset processing/download, Kaggle usage, or Paper writing occurred. `Paper/` was inspected read-only and remained empty. The review was a separate adversarial pass by the same AI assistant, not external peer review or formal machine verification.

## Actual checks and fixes

* **109 passed, 0 failed, 0 errors, 0 skipped** in the final full suite. The original 69 cases all passed before changes. Forty new cases cover adversarial certificates, numerical boundaries, degeneracies, premise failures and regressions. Two deliberate regression demonstrations failed before their fixes; both logs are retained. [Test report](test_report.md).
* **11,965/11,965 arithmetic artifacts and 3,728/3,728 complete envelope traces accepted** in a separate process forbidding numerical-library imports. [Independent checker results](standalone_checker_results.json).
* An exact determinant-based oracle agreed on **48/48** bounded rational polytopes (29 feasible, 19 empty), with **240/240** support bounds sound. Numerical LP success was correctly overridden for inconsistent gaps as small as 1e-20. [Numerical report](numerical_verification.md).
* Fixed invalid-after-depth damage denominators and stale rejected native-point metrics. Added configurable RANSAC thresholds and independently variable synthetic track lengths, with regressions. Original source/claims are preserved in [audit history](audit_history.md) and `history/`.
* Python 3.11.9 and installed local CPU packages worked through an explicit source path. Offline editable installation failed because wheel is absent; setuptools 65.5.0 also falls below the declared build minimum. Packaging and model compatibility are not validated. [Environment](environment.json), [versions](requirements-validation.txt), [commands](commands.ps1).

## Mathematical conclusions

The 18-claim ledger contains eight VERIFIED BY MATHEMATICAL REVIEW, four CONDITIONAL, three INCORRECT and three UNRESOLVED entries. The three incorrect statements were already overclaims/refuted in Phase 1: universal software completeness, joint feasibility from marginal clipping, and generic truth improvement from consistency. They are not newly invalidated versions of W1.

G1's pixel-cone signs, optical-depth intervals, C2's bounded-domain contradiction margin, C3's residual-aware support bound, exact point checking, exact-budget nesting and convex-objective existence/uniqueness are correct under their stated conditions. W1 remains conditional on the true point/domain, correct supplied target depth query, trusted target, bounded inlier pixels, <=q bad auxiliaries and complete sound hypothesis accounting. No counterexample satisfying all premises was found. We explicitly clarified that fixed but erroneous cameras do not establish a physical-depth guarantee.

A proper-camera counterexample verifies that two individually plausible depths may be jointly impossible. Wrong outlier budgets or a doubled baseline move a correct 2 m prediction to approximately 4 m while producing a verified feasible repaired system. Complexity now accounts for up to four LP proposals per retained branch and O(H n^2) saved evidence across targets, H=binomial(n-1,q). [Mathematical audit](mathematical_audit.md), [updated ledger](proof_status_ledger.md).

## Actual controlled results

The predeclared sweep used **28 scenarios x five seeds x eight tracks = 1,120 track instances**, 3,360 scalar observations per method and 10,080 primary method records. It varied all ten requested axes. A separate post-hoc control added 2,240 bounded robust-baseline records on the same saved inputs; two mask-sharing diagnostics were derived without GT. Seeds: 11, 23, 37, 53, 71. Five-seed bootstrap intervals are exploratory; no significance or real-scene generalization claim is made. [Protocol](experiment_protocol.md), [configuration](synthetic_config.yaml).

Reference scenario, 40 tracks/120 depths:

| Method | AbsRel | Depth MAE m | Edited depths | Previously correct damaged at 5% |
|---|---:|---:|---:|---:|
| Original | 0.19583 | 0.73750 | 0/120 | 0 |
| Triangulation | 0.00299 | 0.01170 | 120/120 | 0 |
| Robust reprojection / RANSAC | 0.00299 | 0.01170 | 120/120 | 0 |
| Robust depth | 0.02830 | 0.12505 | 120/120 | 0 |
| Witness3D localized | 0.05617 | 0.21197 | 35/120 | 0 |
| Witness3D all targets | 0.00824 | 0.03261 | 47/120 | 0 |
| Global reconciliation | 0.00914 | 0.03482 | 120/120 | 0 |
| Triangulation on the selective mask | 0.00114 | 0.00448 | 47/120 | 0 |

All-target selective repair corrected all 47 initially false intervals and preserved all 73 exact predictions in this reference. Its individual-refutation precision/recall were 1.0/1.0; localized repair found 35/47. All-target AbsRel's exploratory seed CI was [0.00683, 0.00976], versus triangulation [0.00246, 0.00356]. Mean shared fused-point error fell from 0.74315 m to 0.03294 m, while triangulation reached 0.01193 m. Reprojection readout fell from 3.19659 px to 0.22405 px, versus triangulation 0.10375 px. These shared readouts do not turn scalar repair into a joint-reconstruction theorem.

Full triangulation introduced small nonzero error into the 73 initially exact predictions but none crossed the 5% damage threshold. The same-mask diagnostic preserved them and was more accurate than endpoint clipping on this sample. It shares Witness3D's mask and computation, so it is not an independent cheaper competitor and has no universal non-damage guarantee.

Across the sweep, all-target repair made **882 edits: 876 improved, six worsened**. Among **753 edited observations satisfying evaluated premises**, none worsened. These are finite controlled observations, not a reliability estimate for real imagery. The six harmful edits occurred under pose/noise premise violations and remained below 5% relative error: reporting only threshold damage would conceal them. Example: a correct 4.5 m depth became 4.65143 m under pose error. Individual refutation precision dropped to 0.875 under 1 cm pose perturbation and 0.78947 under 0.75 px noise.

The 889 contradictory/231 feasible group labels agreed with a separately formulated **numerical** elastic LP; that cross-check is weaker than an exact oracle. Zero baseline, pure rotation and three-view q=2 produced no selective correction. The mean q=2 envelope spanned 9.9 m, versus 0.16498 m for q=0. Global output states were 848 converged, 268 abstained and four nonconverged tracks, with failed/abstained depths preserved.

Unbounded robust fitting produced runaway estimates in some outlier cases. The added common-box controls removed unbounded values; all 2,240 outputs were finite and in-domain. On the reference, bounded robust reprojection still achieved 0.00299 AbsRel. Under 10% outliers/q=1, bounded robust reprojection was 0.26887, bounded robust depth 0.09964, all-target Witness3D 0.02913 and RANSAC 0.01549. RANSAC remains the stronger accuracy comparator there. [Full baseline tables](baseline_comparisons.md), [bounded controls](bounded_baseline_comparisons.md), [CSV](synthetic_results.csv), [paired seed differences](paired_seed_comparisons.json), [failure analysis](failure_case_analysis.md).

## Runtime and usefulness gates

The main sweep took **515.657 s**, using **110.28 MiB sampled peak RSS**; the separate bounded control took **122.228 s**, 84.63 MiB. Small-window CPU evaluation is practical. At nine views/q=3, 56 hypotheses cost a mean 1.671 s **per target** and about 631 KB of evidence. Seventy or 924 hypotheses exceeded the cap of 64 and abstained; they were not solved quickly. [Runtime/memory report](runtime_memory.md).

The method demonstrates conditional selective correction and transparent abstention. It does **not** demonstrate superior reconstruction accuracy over triangulation/RANSAC or a superior observed accuracy/damage tradeoff over the same-mask controls. Useful geometry disappears with weak baselines or permissive deletion budgets. Accurate cameras, trusted targets and joint error coverage remain restrictive, unvalidated real-data premises.

The auxiliary-deletion union is exactly a trusted-target restriction of the established q-relaxed intersection. That close structural predecessor, classical interval bounds/duality, and elementary clipping substantially weaken the central novelty framing. A new artifact format or implementation is insufficient. Substantial vision-specific novelty remains unestablished. [Primary-source novelty assessment](novelty_risk.md).

## Next research steps

Before a broad real-data campaign, address camera/query uncertainty and target/budget calibration, validate a local model adapter and a vetted registered dataset export, reproduce CPU checks on Linux, and establish a concrete contribution beyond robust set estimation. A mathematically justified future improvement is to guide a correction by robust geometry while restricting it to the maximal scalar action interval that cannot worsen error for any truth in the certified envelope; this proposal is proved but not implemented or empirically evaluated. Complete branch bounding and broader conflict coverage are additional proposals. [Recommended improvements](recommended_improvements.md).

[Kaggle readiness and exact future commands](kaggle_readiness.md) separate CPU reproduction from a future authorized calibration pilot and model inference. No Kaggle readiness is inferred from these Windows CPU results. Do not proceed to paper writing or promote the current method as a substantial novel CVPR contribution on this evidence.

![Recorded validation overview](D:/CVPR/Code/docs/validation/validation_overview.png)

**NO-GO — the unchanged research formulation has unresolved practical-premise and contribution-validation problems; the tested certificate core remains a useful reference.**
