# Numerical verification report

## Independent arithmetic audit of saved results

`scripts/verify_validation_artifacts.py` was executed in a separate Python process with an import hook that rejects NumPy, SciPy, PyTorch and OpenCV. It read **10,080 record files**, checked **11,965 arithmetic artifacts** and **3,728 complete envelope traces**, and found **zero rejected artifacts/traces**. None of the forbidden modules was loaded. Actual counters: `standalone_checker_results.json`.

The counts include repeated systems across targets and methods. They are submission counts, not independent trials or a statistical confidence bound on software correctness. The checker validates the declared rational systems, domains and branch coverage; it does not authenticate physical cameras or prove their uncertainty bounds.

## Exact oracle, separate from the LP proposer

`scripts/validate_numerics.py` enumerated all rank-three active intersections of 48 small rational polytopes using determinant/Cramer's-rule arithmetic and direct row comparisons. It did not use the production active-set recovery or LP feasibility labels as its reference. Every system included a finite box; a nonempty bounded polyhedron has an extreme point, so exhaustive vertex enumeration decides these cases, including lower-dimensional boundaries when independent active faces exist.

Seed 20261102 generated 29 nonempty and 19 empty systems. Production decisions had **0 disagreements and 0 UNKNOWN** on this finite sample. Five support queries per case gave **240/240 sound bounds**, compared with the exact maximum over all feasible vertices when nonempty. Empty-system bounds are vacuous and were not assigned fake numerical optima. Decision and support artifacts also passed the checker. Raw systems and query values are in `numerical_oracle_results.json`.

This exact oracle uses the same finite input representation and domain-row helper, so it is algorithmically independent of the proposer, not a fully independent implementation of the entire geometry pipeline. Geometric row signs and transformations are covered separately by mathematical review and analytical tests.

## Tolerance boundaries

For x<=0 and x>=epsilon, with epsilon in {1e-6, 1e-10, 1e-14, 1e-20}, all four initial numerical LP calls returned success/status 0 at configured proposal tolerance 1e-6. The exact gate rejected the proposed feasible point and the alternative multiplier path produced VERIFIED_CONTRADICTION in all four cases. Analytic y=(1,1) has exact positive margin epsilon. See `tolerance_boundary_results.json` and the parametrized pytest fixture. This is direct evidence why numerical feasibility status must not be treated as a certificate.

Touching and positive-slack systems were not falsely refuted. Negative, nonfinite or wrong-length multipliers and zero margins were rejected. A tiny residual on an enormous finite domain was correctly retained rather than treated as zero. Unbounded boxes are rejected at ingestion; this is a scope restriction, not an implemented unbounded LP guarantee.

The tolerance probe executed the same two-row Polytope construction and `solve(..., SolverConfig(proposal_tolerance=1e-6))` as `test_subtolerance_contradiction_never_accepted_as_feasible`, additionally recording the numerical status and exact analytic margin for exponents 6, 10, 14 and 20.

## Numerical reference for the larger sweep

The separately formulated elastic LP classified 889 empty and 231 feasible track systems; it agreed with all initial exact-checked group decisions, with 0 ambiguous classifications. Thus observed group precision and recall against this **numerical** reference were both 1.0. This agreement is weaker than an exact oracle on every scene and is reported as such. Individual depth-fault precision is a different quantity and falls under wrong pixel/pose assumptions.

## Remaining limitations

Finite samples cannot establish solver completeness or prove absence of all software bugs. UNKNOWN behavior remains intentional under failed proposals/time caps. Exact rationals encode nominal binary inputs, not interval camera coefficients. Standalone serialized-system checking does not authenticate source measurements. Global optimization remains approximate; its step-based convergence label is not an exact optimality certificate. The main sweep observed four nonconverged global track outputs, with original depths preserved.
