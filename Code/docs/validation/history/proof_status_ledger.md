# Claim ledger — exactly one status per claim

| ID | Claim | Status | Evidence / limits |
|---|---|---|---|
| G1 | Pinhole rectangular bounds + positive optical depth are exactly linear for fixed zero-skew cameras | PROVED UNDER EXPLICIT ASSUMPTIONS | `geometric_constraints.tex`, reversible derivation. Classical. |
| G2 | Conservative physical inputs contain the true point in encoded geometry | PROVED UNDER EXPLICIT ASSUMPTIONS | Rowwise G1; physical premises not checked automatically. |
| C1 | Classical Farkas alternative | PROVED | Established classical theorem invoked; sufficiency shown. Not original. |
| C2 | Exact residual-aware bounded-domain contradiction checker is sound | PROVED UNDER EXPLICIT ASSUMPTIONS | `witness_certificates.tex`; finite exact box and nonnegative rational multipliers. |
| C3 | Exact residual-aware affine support bound is valid | PROVED UNDER EXPLICIT ASSUMPTIONS | Same file; empty sets allowed; domain fallback valid. |
| C4 | Direct exact rational row/domain point check proves encoded feasibility | PROVED | Definition plus exact comparison; no physical guarantee. |
| W1 | Full target-preserving q-hypothesis envelope contains true depth; disjoint interval refutation and clipped scalar error non-increase | PROVED UNDER EXPLICIT ASSUMPTIONS | Full proof in `theorems_and_proofs.tex`; correct target and at most q bad auxiliaries. Not a claim of novel mathematics. |
| W2 | Exact union envelopes widen with increasing outlier budget | PROVED UNDER EXPLICIT ASSUMPTIONS | Same target, cameras, bounds; numerical loose-bound nesting not guaranteed. |
| E1 | <=4-row conflict exists in 3D; exhaustive conclusive oracle can find a smallest such conflict | PROVED UNDER EXPLICIT ASSUMPTIONS | Classical Helly plus enumeration; finite-budget software may not establish minimum. |
| E2 | Complete exact LP oracle decides the encoded fixed-camera problem | PROVED UNDER EXPLICIT ASSUMPTIONS | G1 and classical LP decidability. |
| E3 | Implemented floating proposer + finite checker search is always complete | REFUTED | Time/proposal caps and lower-dimensional point-recovery failure yield UNKNOWN. |
| R1 | Fixed-weight compact-domain convex global objective has a minimizer, unique with positive ridge | PROVED UNDER EXPLICIT ASSUMPTIONS | `repair_optimization.tex`; ordinary convex analysis. |
| R2 | Principal operator preserves observations outside the edit mask | PROVED | Identity outside mask by definition; dense conflict rejection required. |
| R3 | Marginal envelope clipping always yields a jointly feasible reconstruction | REFUTED | Coupled marginal counterexample in `counterexamples.md`. |
| R4 | Generic consistent repair improves ground-truth geometry | REFUTED | Wrong feasible point / incorrect pose examples. |
| R5 | The implemented capped IRLS converges to the unique minimizer for every input | UNRESOLVED | Solver failures, conditioning and stopping policy need analysis/testing. |
| N1 | The combined decision protocol is a substantial original vision contribution | UNRESOLVED | Targeted literature audit incomplete; no experiments. |
| H1 | Conservative outlier-budgeted correction has a useful accuracy/damage/coverage frontier on real imagery | CONJECTURE | Prospective hypothesis only. |

No theorem is marked experimentally validated. This ledger records logical status, not external review or executed proof checking.
