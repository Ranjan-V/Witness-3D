# Claim ledger — Phase 2 mathematical review (2026-11-02)

The original Phase 1 ledger is preserved at `../Code/docs/validation/history/proof_status_ledger.md`. This review is by the same AI assistant in a separate validation pass, not external peer review or formal machine verification. Detailed arguments and boundary attacks: `../Code/docs/validation/mathematical_audit.md`. “VERIFIED BY MATHEMATICAL REVIEW” always retains the listed theorem assumptions.

| ID | Claim | Status | Evidence / limits |
|---|---|---|---|
| G1 | Pinhole rectangular bounds + positive optical depth are exactly linear for fixed zero-skew cameras | VERIFIED BY MATHEMATICAL REVIEW | Reversible derivation, positive focal lengths and z_min. Classical. |
| G2 | Conservative physical inputs contain the true point in encoded geometry | CONDITIONAL | Rowwise G1; physical premises not checked automatically. |
| C1 | Classical Farkas alternative | VERIFIED BY MATHEMATICAL REVIEW | Classical necessity invoked; sufficiency rederived. Not original. |
| C2 | Exact residual-aware bounded-domain contradiction checker is sound | VERIFIED BY MATHEMATICAL REVIEW | Finite exact box, nonnegative rational multipliers and strictly positive exact margin. |
| C3 | Exact residual-aware affine support bound is valid | VERIFIED BY MATHEMATICAL REVIEW | Same algebra; empty sets allowed and domain fallback valid. |
| C4 | Direct exact rational row/domain point check proves encoded feasibility | VERIFIED BY MATHEMATICAL REVIEW | Exact comparison; no physical guarantee. |
| W1 | Complete q-envelope containment and clipped scalar error non-increase | CONDITIONAL | Trusted target, correct supplied geometry/depth query, <=q bad auxiliaries, complete sound bounds. Physical interpretation clarified with original preserved. |
| W2 | Exact union envelopes widen with increasing outlier budget | VERIFIED BY MATHEMATICAL REVIEW | Same target, cameras, bounds; loose numerical bounds need not nest. |
| E1 | <=4-row conflict exists in 3D; exhaustive conclusive oracle can find a smallest row conflict | CONDITIONAL | Helly with the fixed domain included; complete oracle required for minimum. |
| E2 | Complete exact LP oracle decides the encoded fixed-camera problem | CONDITIONAL | Exact LP decidability, not implementation completeness. |
| E3 | Implemented floating proposer + finite checker search is always complete | INCORRECT | Finite proposal/recovery limits permit UNKNOWN. |
| R1 | Compact-domain convex global objective has a minimizer, unique with positive ridge | VERIFIED BY MATHEMATICAL REVIEW | Convexity/strong convexity correct; says nothing about numerical convergence. |
| R2 | Principal operator preserves observations outside the edit mask | VERIFIED BY MATHEMATICAL REVIEW | Identity outside mask by definition; numerical value preservation in dense application. |
| R3 | Marginal clipping always yields a jointly feasible reconstruction | INCORRECT | Proper-camera coupled-depth counterexample in Phase 2 audit. |
| R4 | Generic consistent repair improves ground-truth geometry | INCORRECT | Wrong feasible point and wrong calibration examples. |
| R5 | Capped IRLS converges to the unique minimizer for every input | UNRESOLVED | Convergence theorem absent; empirical failures are possible. |
| N1 | Combined protocol is a substantial original vision contribution | UNRESOLVED | Targeted prior-art review incomplete; implementation differences do not establish novelty. |
| H1 | Useful accuracy/damage/coverage frontier on real imagery | UNRESOLVED | Controlled synthetic experiments cannot establish real-data usefulness. |

Tests and synthetic results, recorded separately under `Code/docs/validation/`, evaluate a finite software/sample setting. They do not prove universal claims or validate physical assumptions on real imagery.
