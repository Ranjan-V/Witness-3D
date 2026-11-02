# Fixed-camera geometric formulation

For track k, unknown point X in R^3, observation i, let camera rows be r1,r2,r3 and translation components t1,t2,t3. Write a=r1 X+t1, b=r2 X+t2, z=r3 X+t3. With zero-skew K, normalized bounds are l_x=(u_min-cx)/fx, h_x=(u_max-cx)/fx and likewise for v. This mapping is exact for axis-aligned pixel boxes under the restricted K.

Pinhole projection gives x=a/z, y=b/z. Because z>=z_min>0, multiplying does not reverse inequalities:

```
(r1 - h_x r3) X <= h_x t3 - t1
(-r1 + l_x r3) X <= t1 - l_x t3
(r2 - h_y r3) X <= h_y t3 - t2
(-r2 + l_y r3) X <= t2 - l_y t3
-r3 X <= t3 - z_min
```

Depth interval [d_low,d_high] adds `r3 X <= d_high-t3` and `-r3 X <= t3-d_low`. Six world-box rows supply X in B=[L_B,U_B]. Each observation contributes five pixel/cheirality rows and optionally two depth rows. All rows carry track, observation, camera, and semantic-kind provenance. Intersections are convex closed polyhedra, compact when B is finite. A single point variable is not a surface reconstruction.

If z could be zero or negative, the multiplication equivalence fails. Strict z>0 is open; replace it by the explicitly justified physical margin z>=z_min. Rays with true depth in (0,z_min) are outside the problem, not counterexamples to the derivation.

## Separate systems

* P_pix: only pixel, positive-depth, domain constraints. A contradiction here implicates the measurement model or assumptions.
* P_all: P_pix plus model depth intervals. Infeasibility proves at least one supplied assumption/claim incompatible, not a unique bad prediction.
* P_S for a target j: target and auxiliary pixel constraints after deleting exactly q auxiliary observations, or all auxiliaries when fewer than q exist. More precisely enumeration requires 0<=q<=n-1; reject other budgets. Deleting extra inliers covers every case with <=q bad auxiliaries. No depth constraints enter P_S.

The possible-geometry set is union_S P_S. For target affine depth z_j(X)=r3_j X+t3_j, use an outer interval J_j=[min_S lower_S,max_S upper_S]. Never discard a hypothesis because an LP returned infeasible without a checked certificate. Unknown hypotheses contribute conservative bounds, at worst the target depth range over B. Convexifying the union loses holes, intentionally producing fewer refutations.

If all hypotheses are certified empty, return measurement conflict. If the target interval lies outside J_j, refute that interval under the trust premises. Otherwise abstain. Narrowness is measured separately from consistency.

## Acquisition and transformations

Inference maps return the original image grid. For a resize with half-pixel sampling u'=s_x(u+0.5)-0.5, K'=H K with H=[s_x,0,(s_x-1)/2;0,s_y,(s_y-1)/2;0,0,1]. Crops subtract crop origin from principal point. Bounds must transform by the same map. Adapter-internal resizing followed by upsampling to the original grid does not change the external K. Pixel uncertainty must include resampling and matching localization effects.

Convert c2w T_wc=[R_wc,C;0,1] to R_cw=R_wc^T, t_cw=-R_wc^T C. Quaternion order must be explicit. Euclidean range rho converts to z=rho/sqrt(1+x^2+y^2) at a known pixel; bounding a range over a pixel box generally requires nonlinear extrema, so the core rejects range intervals.

## Where LP fails

Unknown R multiplies X; radial distortion changes the image rectangle; Euclidean reprojection disks yield second-order rather than four linear sides; relative depth with unknown scale/shift couples predictions and geometry; visibility and correspondence selection introduce discrete choices. These are extensions, not covered by the base LP equivalence. Fixed-affine inverse-depth calibration is treated as an adapter, and its estimation uncertainty is not certified.
