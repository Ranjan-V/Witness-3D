# Algorithms and decision logic

## Algorithm 1: principal research candidate

Inputs: cameras, track observations, metric depth claims, declared world box, z_min, outlier budget q, maximum hypotheses, LP time limit. No reference depth is accepted by this interface.

```
assemble exact-rational P_all and P_pix; obtain checked statuses
if P_pix is verified contradictory and q=0: measurement conflict; preserve depths
if P_all is not verified contradictory: preserve depths; return status
extract an inconsistent row subset with its own certificate (optional explanation)
for every depth observation implicated by that subset (or all when localization disabled):
    enumerate every q-deletion auxiliary hypothesis, keeping this target
    if count exceeds cap: abstain for this target, never truncate enumeration
    for each hypothesis:
        discard only on an independently checked contradiction
        otherwise bound +/- target-camera depth with checked support inequalities
        fallback for a failed optimization: world-domain bound, not omission
    if all hypotheses discarded: measurement conflict; preserve target
    else if target depth interval is disjoint from envelope:
        clamp original depth center to outward-rounded envelope; keep width fixed
        record support multipliers, excluded hypotheses, domain, and trust premises
rebuild all depth intervals around edited centers and independently recheck P_all
report per-depth refutation, edits, and joint post-repair status separately
```

Only explicit sampled observations can change. Dense output uses a sparse edit mask and leaves every other pixel byte-equivalent when dtype permits; no propagation is part of the guarantee. When several tracks request different values at one pixel, conservative application rejects *all* conflicting edits. Duplicate observations are checked at track construction. Do not average two certified edits and assume a retained guarantee.

Explanation extraction uses exhaustive row subsets up to four on small 3D systems, with a configured query budget. This is cardinality-smallest only if every smaller candidate was conclusively resolved; otherwise label it `small_verified_subset`. Deletion shrinking is larger-instance approximation; irreducible is claimed only if every single-row deletion is verified feasible. Numerical uncertainty prevents minimality claims. Helly's theorem explains the four-row existence bound, not a new result.

Attribution has two levels: conflict membership gives a *suspect group*; a prediction-independent envelope can refute an individual interval under stronger assumptions. Group frequency, solver dual magnitude, and match confidence are heuristic rankings, not probabilities of fault.

## Algorithm 2: global reconciliation baseline

Fix cameras, let X_k be track points and d_ki=r3_i X_k+t3_i. Constrain each X_k to its pixel polytope. Minimize robust, confidence-weighted residuals to model depths, plus ridge preservation relative to an initial feasible point and optional graph penalties preserving *original depth differences* between neighboring tracks. Each edge is supplied from image-space proximity and appearance; no reference geometry is read. Fixed positive weights and convex Huber losses give a convex problem; IRLS is a numerical strategy with a cap and explicit failed/nonconverged state, not a certified minimizer. Incorrect correspondences can make hard pixel constraints infeasible, so prefilter/RANSAC or abstain. A soft-pixel robust least-squares baseline handles that case but relinquishes bounded-pixel feasibility.

Global reconciliation can improve reconstruction when individual envelopes are weak; it can also damage correct values. It offers no per-depth non-degradation theorem. Its purpose is to test whether the proposed selective local protocol contributes beyond robust point refinement and spatial smoothing.

## Counterexample-guided computation

Certificates identify constraints preventing a current explanation; depth-free envelopes ask what evidence permits changing a particular claim. q-hypothesis enumeration is the implemented small-instance reference. Witness-guided hitting-set search over deletion sets is a potential accelerator: any retained contradiction must lose at least one auxiliary block to become feasible. Do not claim its global completeness until it covers every admissible deletion or conservatively bounds uncovered branches. This accelerator is deliberately an open question, not an unimplemented core dependency.

## Exact checker / numerical proposer separation

SciPy HiGHS proposes points and normalized nonnegative multipliers. A standalone Fraction-based checker consumes exact rows, exact domain and proposed numbers. Nonzero dual residuals are handled by minimizing the residual linear form over B; no arbitrary tolerance proves an unbounded system infeasible. Export self-contained JSON certificate artifacts. Envelope certificates use the same residual-corrected support inequality. Solver tolerances affect availability of evidence, never the validity criterion.
