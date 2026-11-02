# Actual baseline comparisons

Reference scenario: five seeds, 40 tracks, 120 scalar depths. Means below are seed means. Full seed-bootstrap intervals and all scenarios are in `synthetic_results.csv` and `results/sweep/summary.json`. Undefined cells are shown as —. See `experiment_protocol.md` for denominators, uncertainty matching and failure policy.

| Method | AbsRel | MAE m | Shared fused point error m | Reprojection px | Edited % | Wrong corrected % | Correct damaged % | Strict error increase % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 0.19583 | 0.73750 | 0.74315 | 3.19659 | 0.00 | 0.00 | 0.00 | 0.00 |
| fusion | 0.19583 | 0.73750 | 0.74289 | 2.65154 | 82.50 | 0.00 | 81.44 | 48.33 |
| triangulation | 0.00299 | 0.01170 | 0.01193 | 0.10375 | 100.00 | 100.00 | 0.00 | 60.83 |
| robust_triangulation | 0.00299 | 0.01170 | 0.01193 | 0.10375 | 100.00 | 100.00 | 0.00 | 60.83 |
| ransac | 0.00299 | 0.01170 | 0.01193 | 0.10375 | 100.00 | 100.00 | 0.00 | 60.83 |
| robust_depth | 0.02830 | 0.12505 | 0.12585 | 0.35574 | 100.00 | 87.05 | 0.00 | 60.83 |
| local | 0.05617 | 0.21197 | 0.21386 | 1.06416 | 29.17 | 75.58 | 0.00 | 0.00 |
| local_all | 0.00824 | 0.03261 | 0.03294 | 0.22405 | 39.17 | 100.00 | 0.00 | 0.00 |
| global | 0.00914 | 0.03482 | 0.03517 | 0.22297 | 100.00 | 100.00 | 0.00 | 60.83 |
| triangulation_on_selective_mask | 0.00114 | 0.00448 | 0.00490 | 0.11438 | 39.17 | 100.00 | 0.00 | 0.00 |
| robust_triangulation_on_selective_mask | 0.00114 | 0.00448 | 0.00490 | 0.11438 | 39.17 | 100.00 | 0.00 | 0.00 |

The shared fused point is an evaluation readout for scalar outputs. Native-point errors are separately recorded; selective repair supplies no native point. A zero 5%-threshold damage rate does not mean zero numerical error increase. In this reference, the 73 originally exact depths are changed slightly by full triangulation/global estimation; selective repair preserves them. The mask-sharing diagnostic also preserves them and has lower measured error than endpoint clipping, without a universal non-damage theorem.

## Stress scenarios: actual AbsRel

| Scenario | Original | Triangulation | Robust reprojection | RANSAC | Local | All-target local | Global |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline_0p03 | 0.19583 | 0.02994 | 0.02996 | 0.02996 | 0.12831 | 0.10443 | 0.06623 |
| baseline_1 | 0.19583 | 0.00090 | 0.00090 | 0.00090 | 0.05182 | 0.00243 | 0.00501 |
| bias_1p1 | 0.03917 | 0.00299 | 0.00299 | 0.00299 | 0.01617 | 0.00824 | 0.01065 |
| bias_2 | 0.39167 | 0.00299 | 0.00299 | 0.00299 | 0.10617 | 0.00824 | 0.04852 |
| clean_q1 | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.06325 | 0.01786 | 0.00914 |
| clean_q2 | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.19583 | 0.19583 | 0.00914 |
| correct_predictions | 0.00000 | 0.00299 | 0.00299 | 0.00299 | 0.00000 | 0.00000 | 0.00000 |
| depth_width_0p005 | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.05617 | 0.00824 | 0.00601 |
| depth_width_0p1 | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.05617 | 0.00824 | 0.01851 |
| depth_width_0p4 | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.19583 | 0.19583 | 0.01869 |
| gaussian_noise_0p2 | 0.19583 | 0.00524 | 0.00524 | 0.00524 | 0.05575 | 0.00757 | 0.00861 |
| gaussian_noise_0p75 | 0.19583 | 0.01773 | 0.01770 | 0.03118 | 0.15243 | 0.13669 | 0.19583 |
| outliers_10pct_q0 | 0.18750 | 0.10285 | 4838.13167 | 0.01549 | 0.07993 | 0.03214 | 0.13189 |
| outliers_10pct_q1 | 0.18750 | 0.10285 | 4838.13167 | 0.01549 | 0.07439 | 0.02913 | 0.13189 |
| outliers_30pct_q0 | 0.16667 | 0.35373 | 11889.61636 | 0.05286 | 0.13086 | 0.11498 | 0.16667 |
| outliers_30pct_q1 | 0.16667 | 0.35373 | 11889.61636 | 0.05286 | 0.09404 | 0.07117 | 0.16667 |
| pixel_radius_2 | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.07670 | 0.03577 | 0.02584 |
| pose_rotation_0p002 | 0.19583 | 0.01181 | 0.01176 | 0.01982 | 0.13209 | 0.10833 | 0.13247 |
| pose_translation_0p002 | 0.19583 | 0.00454 | 0.00454 | 0.00505 | 0.05628 | 0.00834 | 0.00885 |
| pose_translation_0p01 | 0.19583 | 0.02016 | 0.02006 | 0.05125 | 0.15553 | 0.13932 | 0.14695 |
| pure_rotation | 0.19583 | 0.19583 | 1.41569 | 0.19583 | 0.19583 | 0.19583 | 0.12467 |
| reference | 0.19583 | 0.00299 | 0.00299 | 0.00299 | 0.05617 | 0.00824 | 0.00914 |
| track_2_of_5 | 0.16250 | 0.00479 | 0.00479 | 0.00479 | 0.03451 | 0.01106 | 0.00887 |
| track_3_of_5 | 0.13750 | 0.00256 | 0.00256 | 0.00256 | 0.03623 | 0.00390 | 0.00565 |
| undersized_pixel_box | 0.19583 | 0.00299 | 0.00299 | 0.00586 | 0.12955 | 0.10054 | 0.19583 |
| views_2 | 0.23750 | 0.00559 | 0.00559 | 0.00559 | 0.07226 | 0.02158 | 0.01781 |
| views_5 | 0.17250 | 0.00136 | 0.00136 | 0.00136 | 0.08938 | 0.00383 | 0.00689 |
| zero_baseline | 0.19583 | 0.19583 | 4.65758 | 0.19583 | 0.19583 | 0.19583 | 0.12467 |
