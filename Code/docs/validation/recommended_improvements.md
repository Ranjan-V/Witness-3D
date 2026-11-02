# Methodological improvements — proposals, not executed results

These proposals do not replace the executed method. No performance improvement is claimed for them.

## 1. Address calibration uncertainty before broad deployment

The exact certificate validates nominal finite coefficients. Suppose independently justified coefficient bounds satisfy |Delta A_ij|<=e_ij and |Delta b_i|<=f_i, and the box supplies |X_j|<=M_j. Any physically feasible true row implies the nominal relaxed row

`Ahat_i X <= bhat_i + f_i + sum_j e_ij M_j`.

This follows by adding/subtracting the coefficient errors and using the triangle inequality. Such relaxed pixel rows preserve true-point containment. Target affine depth also needs an error bound: if |Delta c_j|<=g_j and |Delta t|<=h, inflate the nominal depth envelope by `h+sum_j g_j M_j` at both ends. Only then does W1 transfer to physical depth. Pose-rotation uncertainty must be propagated into these bounds rather than guessed as a Gaussian standard deviation. Conservative propagation may yield unusably wide envelopes; measure that failure honestly.

## 2. Test an estimate-guided, provably safe scalar move

Endpoint clipping is only one uniformly non-damaging action. Given a guaranteed interval J=[L,U] and original depth d, define

```
S(d,J) = [d, 2L-d]       if d < L
         [2U-d, d]       if d > U
         {d}            if L <= d <= U.
```

For every x in S(d,J) and every possible true z in J, `|x-z|<=|d-z|`, hence also squared-error non-increase. Proof when d<L: z>=L>d and |x-z|<=z-d is equivalent to d<=x<=2z-d. Intersect over all z in J to obtain [d,2L-d]. The d>U case is symmetric. If d belongs to J, taking z=d forces x=d. Thus this set is the **maximal** uniformly safe scalar action set for a full interval J.

A future variant could project a robust triangulation estimate onto S(d,J), intersected with the admissible fixed-width positive-depth domain. It retains conditional non-increase while permitting movement past the nearest envelope endpoint when justified. It still cannot prove joint feasibility, inherits every trust assumption, and is not claimed novel. Near floating boundaries, exact predicates/conservative representable actions are required; naïvely rounding the action bounds outward is unsafe here because those bounds delimit permitted actions. Unlike W1's outward-enlarged *truth envelope*, the allowed-action interval must not admit unsafe points.

## 3. Improve coverage without silently changing localization claims

A single inconsistent subset does not enumerate all erroneous depth claims. Under pixel-only conflicts and q>0, the selected conflict may contain no depth rows, leaving the original localized method with no targets. The executed local_all ablation tests all targets and documents this coverage cost. An iterative workflow could remove/resolve one certified claim and seek another conflict, or rank all targets and process them under a declared budget. Any skipped target must remain unchanged. This changes coverage and runtime, not the per-edit theorem.

## 4. Bound unexplored hypotheses instead of exhaustive enumeration

Use conflict-guided branch-and-bound over auxiliary blocks. A checked conflict shows that at least one of its auxiliary blocks must be deleted for that branch to be feasible; target/domain-only conflicts eliminate the branch. Every unexpanded branch must retain a sound depth enclosure. At interruption, hull explored and unexpanded bounds. This can preserve W1 while reducing work, but complete tree accounting, grouping and an independent trace verifier need implementation/proof. The current enumeration remains the reference; no speedup has been measured.

## 5. Real-data gates and stronger controls

Use held-out calibration scenes to assess pixel/pose bounds, correspondence-budget violation and trusted-target failures. Freeze widths/budgets before held-out evaluation. If adopting probabilistic bounds, state a joint failure budget for all observations used by the selected hypothesis; a per-pixel percentile is not a track-level guarantee. Keep sparse and dense denominators separate.

Compare against interval triangulation/q-relaxed set estimation, robust geometry with the same edit mask and compute budget, and stronger calibrated robust estimators. Report every failure fallback. Require an advantage beyond preserving exactly correct synthetic predictions under exact cameras. The proposed next phase should be designed to falsify practical usefulness and novelty, not to maximize an isolated favorable metric.
