# Phase 2 mathematical review — 2026-11-02

This review rederived the arguments from the nine requested source files before test execution. It is a second adversarial review by the same AI assistant, not an independent human review, external peer review, or machine-checked proof. Original ledger, theorem text and complexity text are preserved in `history/`.

## Reconstruction and findings

For a world-to-camera affine map, write a=r1 X+t1 and z=r3 X+t3. Positive fx and z imply `(u_min-cx) z/fx <= a <= (u_max-cx) z/fx`; moving terms gives precisely the two implemented u rows. The v rows follow identically. Optical-axis depth is affine z, not Euclidean range: upper and lower depth rows have right sides d+width-t3 and t3-d+width respectively. The box and z_min are restrictions on the problem, not consequences of projection.

For any nonnegative y and feasible X in B, `min_B (A^T y)^T X <= y^T AX <= b^T y`. Strict reversal of these bounds proves infeasibility even with nonzero dual residual. Substituting A^T y-c proves the support inequality. No floating tolerance can replace the strict rational comparison. These are elementary bounded-domain versions of classical duality; Farkas necessity is invoked from the classical theorem rather than proved in this repository.

For W1, extend the actual bad auxiliary set to exactly q deletions. The remaining target and inlier rows contain X*. Sound exclusion cannot remove that branch. Sound support bounds and the hull therefore contain z*. Clipping to an interval containing z* decreases absolute error by exactly the clipping distance; squared improvement is a^2+2ab, with a the move and b the remaining error. Unselected entries remain identical. This proof survives UNKNOWN branches only if they remain represented with sound bounds. It fails if enumeration is truncated optimistically.

W1's phrase “fixed cameras” needs an explicit distinction: the encoded scalar guarantee concerns the supplied affine query r3 X*+t3. An actual physical-depth guarantee additionally requires this query to equal physical optical depth and true projections to obey the supplied model. A fixed but erroneous pose is not enough. This premise is now explicit in the theorem text; the original is preserved. Coefficient uncertainty is not certified by exact arithmetic on nominal floats.

For W2, remove an additional auxiliary from each q branch to embed its feasible set in a (q+1) branch. This establishes monotonicity only for exact hulls; independently loose solver bounds may violate observed nesting. For R1, convex affine Huber terms and nonnegative squared affine terms plus eta/2 times squared distance have Hessian lower bound eta I where differentiable and satisfy strong convexity generally. Compactness supplies existence, positive eta uniqueness; neither implies capped numerical IRLS convergence.

Helly gives at most four sets in R3, including any used domain halfspaces or fixed box. Searching row subsets of increasing size with a complete oracle finds a smallest row conflict relative to the always-present box. That is not a minimum number of erroneous observations or a minimum physical explanation. Finite budgets invalidate a completeness/minimality guarantee.

## Status of every ledger claim

| ID | Phase 2 status | Conclusion |
|---|---|---|
| G1 | VERIFIED BY MATHEMATICAL REVIEW | Reversible signs and dimensions correct; fixed positive-focal zero-skew pinhole, z>=z_min required. |
| G2 | CONDITIONAL | Correct physical inputs imply containment; premises are unverified physical assumptions. |
| C1 | VERIFIED BY MATHEMATICAL REVIEW | Classical Farkas alternative; sufficiency rederived, necessity imported. |
| C2 | VERIFIED BY MATHEMATICAL REVIEW | Exact nonnegative y plus finite declared box and strict positive margin suffice. |
| C3 | VERIFIED BY MATHEMATICAL REVIEW | Residual support formula and zero-multiplier fallback correct. |
| C4 | VERIFIED BY MATHEMATICAL REVIEW | Exact point membership proves encoded feasibility. |
| W1 | CONDITIONAL | Valid under containment, trusted target, budget and complete sound coverage; physical-depth interpretation clarified. |
| W2 | VERIFIED BY MATHEMATICAL REVIEW | Exact union nesting, not numerical-bound nesting. |
| E1 | CONDITIONAL | Helly/finite enumeration correct with complete oracle; fixed box accounted separately. |
| E2 | CONDITIONAL | Exact LP oracle decides encoded problem; not the implemented proposer. |
| E3 | INCORRECT | General software completeness is false; UNKNOWN permitted by design. |
| R1 | VERIFIED BY MATHEMATICAL REVIEW | Existence/uniqueness under stated convexity/compactness assumptions. |
| R2 | VERIFIED BY MATHEMATICAL REVIEW | Identity outside mask; numerical values preserved on float64 materialization. |
| R3 | INCORRECT | Marginal clipping need not have a common 3D preimage. |
| R4 | INCORRECT | Consistency does not imply accuracy. |
| R5 | UNRESOLVED | No proof of capped IRLS convergence. |
| N1 | UNRESOLVED | Mathematical review cannot establish substantial novelty. |
| H1 | UNRESOLVED | Requires real-image evidence; synthetic validation is insufficient. |

## Constructive attacks and their implications

1. Two rectified cameras, f=100, baseline=1, target at principal point: true point (0,0,2) has auxiliary u=-50 in centered coordinates. Supplying u=-25 instead creates a consistent depth-4 explanation. A correct prediction 2 can be clipped toward 4 with q=0. This violates the auxiliary-budget premise, not W1. With q=1 both views individually permit a broad depth range and the harmful refutation disappears.
2. The same observations with a supplied baseline twice the physical baseline imply depth 4 instead of 2. Pixel containment/physical-camera assumptions fail. Exact certificates remain algebraically valid and can still authorize physically harmful edits.
3. An auxiliary localization error exceeding an asserted tiny pixel box can similarly exclude the true point. Gaussian noise cannot be covered deterministically by a finite fixed radius. Increasing depth widths cannot fix this pixel-premise error.
4. Two rotated/translated cameras can induce depths (s,0.6s+1) along the target ray for s in [1,2]. Marginals [1,2] and [1.6,2.2] admit (2,1.6), but no shared s. Independent scalar plausibility is insufficient for joint reconstruction. This is a concrete proper-rotation realization of the existing abstract counterexample.
5. Zero baseline and pure rotation leave metric scale unobservable. A finite box supplies an envelope, but its width may be almost the entire depth extent. “Bounded” does not mean informative.
6. Without finite B, the residual certificate is invalid in general: epsilon*x<=-1 is feasible at x=-1/epsilon. The implementation intentionally rejects unbounded boxes. Empty feasible sets are supported; unbounded feasible regions are outside the API.

No counterexample was found to W1 with all its explicit premises satisfied. This is not proof that the software realizes W1; executable adversarial checks follow separately.

## Complexity correction

H=binomial(n-1,q). Each hypothesis uses one decision call (up to TWO numerical LPs), and up to two support LPs. Thus at most four LP proposals per retained branch, not three; active-set exact recovery adds up to binomial(recovery_rows,3) checks. Across all n targets cost is O(n H) small decision/support calls, with nonconstant rational bit complexity. q around n/2 is exponential. Saved branch systems cost O(H n) per target and O(H n^2) across all targets on a track. The previous O(n) streaming phrase did not describe retained evidence or the runner's in-memory records. Numerical global optimization is dense at its SLSQP boundary. These accounting errors are corrected, without changing the contribution.
