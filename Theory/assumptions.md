# Assumptions, trust boundaries, and interpretation

## Required for the base mathematical model

1. World and camera coordinates are right-handed, measured in meters; camera x points right, y down, z forward. `x_c = R_cw X_w + t_cw`. Pixel centers are integers. Pinhole intrinsics have positive fx,fy, zero skew, last row (0,0,1). The implementation rejects skew rather than silently boxing a sheared pixel region.
2. Observations have already been rectified into this pinhole image. Each supplied rectangular pixel box contains the actual projection when its observation is an inlier. Undistorting only the box corners is not generally conservative for nonlinear distortion. Raw distorted images are rejected by the manifest gate.
3. Visibility means the same physical static surface point is associated across included views, is in the image, and has z >= z_min > 0. Positive depth is encoded; occlusion cannot be proved from sparse pinhole inequalities. Masks and tracks assert visibility and are not certificates of it.
4. A finite world box B contains the relevant scene point. This box is part of the claim, never an invisible solver convenience. Altering it changes the verified problem. It must be set from an external scene specification, not test depth. Camera translation errors can invalidate this assumption and the pixel cones.
5. Depth claims are closed intervals in meters of camera optical-axis z. They are not Euclidean range. Predictions and widths are finite and positive. There is no built-in coverage guarantee for a chosen relative width.
6. Every exact certificate concerns exact rational coefficients assembled from the finite supplied numbers. The cameras need not be exact physical cameras for a certificate to be valid for this algebraic problem. Physical guarantees additionally require that these supplied inequalities conservatively contain the physical point. No automatic calibration-error enclosure is implemented.

## Stronger assumptions for individual attribution and safe correction

The target pixel association is correct, and its sampled model/reference depth refers to the same surface point represented by that association. This extra sampling premise matters when a subpixel feature is snapped to a discrete depth-map pixel, especially at occlusion boundaries. Enlarging a pixel box covers localization error but does not prove same-surface sampling. At most q auxiliary observations in its track are wrong. Every retained inlier pixel box contains the true projection. All true visible depths satisfy z_min and the world box contains the true point. Construct the envelope without any predicted depths. At least one enumerated deletion hypothesis then contains the true point. If a budget cap prevents full enumeration, return no refutation and make no edits. A known-correspondence synthetic task meets these assumptions; real matching scores do not establish them.

## Distinctions that must survive reporting

| Distinction | Operational treatment |
|---|---|
| Known versus uncertain poses | Exact supplied-camera problem versus perturbation stress test; no pose uncertainty theorem. |
| Metric versus relative depth | Metric accepted; relative inverse depth must be converted by separately fitted positive affine inverse-depth calibration, otherwise rejected. |
| Correct tracks versus outliers | q-budget on auxiliary observations conditional on trusted target; ORB/RANSAC scores are heuristics. |
| Static versus dynamic | Static is a premise; motion causes assumption failures, not automatic model blame. |
| Depth versus pose error | Depth-free geometry conflict triggers abstention; it cannot identify which camera is wrong. |
| Feasibility versus correctness | A feasible point is not ground truth and need not be unique. |
| Bounds versus confidence | Deterministic premise versus distributional coverage; no 95% confidence label without calibrated coverage and joint accounting. |

## Statistical uncertainty

Pixel noise drawn from an unbounded Gaussian does not obey a deterministic finite box with probability one. Evaluate coverage failures explicitly. A union bound gives joint failure <= sum of marginal failure probabilities without independence; selection and dataset shift still need analysis. Split-conformal marginal coverage, if later added, would not by itself certify each selected track or simultaneous image coverage. Calibration scenes, development scenes, and evaluation scenes must be disjoint.
