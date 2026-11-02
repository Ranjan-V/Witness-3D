# Written internal mathematical audit

This is a self-audit by the authoring assistant, not independent human review.

| Claim | Dimensions / positivity / boundary review | Classical relationship and conclusion |
|---|---|---|
| G1 | r_a is 1x3, X 3x1; normalized bounds dimensionless, rows times X in meters. fx,fy,z positive. Closed zero-width boxes allowed. | Classical fixed-camera cone intersection. Signs checked by moving both upper and lower affine terms. |
| G2 | X* must satisfy box, visible inlier and all imposed interval premises simultaneously. | Contradiction gives a disjunction of failed premises, never automatic model blame. |
| C1 | y length m, A^T y length 3, beta scalar. y>=0 essential. | Classical Farkas. Full alternative invoked, not invented. |
| C2 | Residual minimized on the same finite 3D box as the problem; strict exact inequality. | Elementary bounded-domain residual correction. Box omitted from physical interpretation would be unsound. |
| C3 | c length 3 and t meters; same residual/domain arithmetic. y=0 always legal. | Weak duality with explicit residual correction. Support LP failure loses tightness, not validity. |
| C4 | Exact row and domain checks, including boundaries. | Tautological feasibility certificate; finite search not complete. |
| W1 | At most q bad auxiliaries, correct target, full enumeration, no predicted depths; all true inliers satisfy cheirality. | Nontrivial problem-specific composition, but set containment and scalar projection are classical. Cannot claim novelty. |
| W2 | Same target and domain as q changes; q<n-1. | Set inclusion; computed loose endpoints can violate apparent nesting. |
| E1/E2 | Dimension fixed at three; box may count as one convex set; complete oracle required. | Helly and LP decidability classical; finite-budget implementation has no minimum/completeness promise. |
| R1 | 3K point variables; widths positive; weights fixed/nonnegative; nonempty compact product domain; eta>0. | Standard convex existence/uniqueness. Not numerical convergence or truth accuracy. |
| R2 | Identity operator outside mask; duplicate/conflicting dense edits rejected. | Engineering invariant, must later be tested. |

Major counterexamples are catalogued separately. Strong unsupported claims removed: unique fault attribution from one conflict, accuracy from feasibility, exactness from solver status, universal repair improvement, dense correction safety, always-complete certificates, automatically useful q-robust envelopes, automatic TPU acceleration and guaranteed main-track novelty.

Phase gate: fixed-camera model is internally consistent under explicit premises. Mathematical source and this audit were completed before creating the Python codebase. Implementation correctness remains unexecuted and needs future tests.
