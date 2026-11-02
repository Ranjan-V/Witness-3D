# Counterexamples and failure criteria

| Situation | What can go wrong | Required response / falsification |
|---|---|---|
| Pure rotation / identical cameras | Pixel cones leave long depth segments; wrong depth may be feasible. | Wide envelope, abstention; detection recall need not approach one. |
| Very short baseline | Pixel noise dominates parallax. | Measure interval width and condition sensitivity, not only point accuracy. |
| Broad depth intervals | False predictions can intersect correct geometry. | Consistency does not validate the center. Fixed-coverage comparisons. |
| Shared coherent depth bias | All depths fit a wrong point allowed by pixel uncertainty. | No contradiction; independent geometry may also be uninformative. |
| Pose or calibration error | Correct depths become inconsistent with wrong rays. | Conditional claims only; depth-free conflict and perturbation curves. |
| Wrong target correspondence | Auxiliary q-budget cannot rescue attribution at the wrong target. | Trusted-target premise must be explicit; test its violation. |
| More than q auxiliary outliers | True point may be absent from every hypothesis. | Report assumption failure; no unconditional safe-correction claim. |
| Occlusion / motion / reflections | Tracks can refer to different surfaces or apparent features. | Masks and temporal checks are heuristics; abstain and label failure. |
| Unknown scale / affine inverse depth | Metric inequalities are meaningless before calibration. | Reject unsupported convention; disjoint geometry calibration only. |
| Incorrect world box | A domain-based certificate may be valid but physically irrelevant. | Serialize box; stress box size; never estimate it from held-out depth. |
| Numerical residual | Tiny nonzero A^T y can fabricate unbounded contradiction. | Exact residual-aware domain checker; reject epsilon-as-proof. |
| Envelope hull fills gaps | A depth in the convex hull may fit no deletion hypothesis. | Conservative loss of power is allowed; report unresolved. |
| Independent scalar edits | Marginally admissible depths may have no joint point. | Mandatory reconstructed-system check; report unresolved repair. |
| Dense diffusion | A correct sparse change can corrupt an unobserved surface. | No diffusion in principal method; spatial global method is a baseline. |
| Border / resampling ambiguity | Depth sample and feature may represent different surfaces. | Explicit nearest-pixel sampling and pixel box, boundary exclusions. |
| Runtime explosion | q hypotheses scale combinatorially. | Exact count cap leads to abstention, never optimistic truncation. |

Release-blocking criteria: any accepted invalid exact certificate, any hidden GT access in inference, any edit outside the authorized mask, any missing hypothesis treated as impossible, or any cached run resumed under a changed spec. Research-blocking criteria: no useful real-data correction coverage under credible assumptions, no gain beyond matched robust baselines, or a direct prior method with the same protocol.
