# Equal-budget mask replay: all 28 scenarios

All scalar observations remain in the evaluation population. Ranking thresholds are chosen to match Witness3D’s edit count, without labels. The count is shared side information; this is not an independently calibrated deployment threshold. Every selector uses the same DLT replacement values. Failed/no-op replacement slots are excluded identically before matching counts; full-population Witness3D mask statistics are shown separately. Random results average 32 draws per seed. Undefined values are —.

| Scenario | W precision | W recall | W FPR | W mask + DLT | Depth disagreement + DLT | RANSAC disagreement + DLT | Random + DLT |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline_0p03 | 1.000000 | 1.000000 | 0.000000 | 0.011301 | 0.011301 | 0.011301 | 0.128000 |
| baseline_1 | 1.000000 | 1.000000 | 0.000000 | 0.000342 | 0.000342 | 0.000342 | 0.116627 |
| bias_1p1 | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.024426 |
| bias_2 | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.233723 |
| clean_q1 | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.117447 |
| clean_q2 | — | 0.000000 | 0.000000 | 0.195833 | 0.195833 | 0.195833 | 0.195833 |
| correct_predictions | — | — | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| depth_width_0p005 | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.117447 |
| depth_width_0p1 | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.117447 |
| depth_width_0p4 | — | — | 0.000000 | 0.195833 | 0.195833 | 0.195833 | 0.195833 |
| gaussian_noise_0p2 | 1.000000 | 1.000000 | 0.000000 | 0.001872 | 0.001872 | 0.001872 | 0.118248 |
| gaussian_noise_0p75 | 0.789474 | 0.319149 | 0.054795 | 0.136893 | 0.119390 | 0.119390 | 0.165799 |
| outliers_10pct_q0 | 1.000000 | 0.866667 | 0.000000 | 0.025926 | 0.151050 | 0.025926 | 0.141704 |
| outliers_10pct_q1 | 1.000000 | 0.933333 | 0.000000 | 0.032979 | 0.142761 | 0.032979 | 0.140406 |
| outliers_30pct_q0 | 1.000000 | 0.325000 | 0.000000 | 0.112698 | 0.220019 | 0.119220 | 0.179492 |
| outliers_30pct_q1 | 1.000000 | 0.625000 | 0.000000 | 0.121246 | 0.267589 | 0.121246 | 0.201493 |
| pixel_radius_2 | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.117447 |
| pose_rotation_0p002 | 1.000000 | 0.468085 | 0.000000 | 0.106994 | 0.106992 | 0.106992 | 0.159919 |
| pose_translation_0p002 | 1.000000 | 1.000000 | 0.000000 | 0.001678 | 0.001678 | 0.001678 | 0.117995 |
| pose_translation_0p01 | 0.875000 | 0.297872 | 0.027397 | 0.140238 | 0.131785 | 0.131785 | 0.167478 |
| pure_rotation | — | 0.000000 | 0.000000 | 0.195833 | 0.195833 | 0.195833 | 0.195833 |
| reference | 1.000000 | 1.000000 | 0.000000 | 0.001138 | 0.001138 | 0.001138 | 0.117447 |
| track_2_of_5 | 1.000000 | 1.000000 | 0.000000 | 0.001693 | 0.001693 | 0.001693 | 0.106885 |
| track_3_of_5 | 1.000000 | 1.000000 | 0.000000 | 0.000643 | 0.000643 | 0.000643 | 0.096539 |
| undersized_pixel_box | 1.000000 | 0.489362 | 0.000000 | 0.100625 | 0.100615 | 0.100615 | 0.157499 |
| views_2 | 1.000000 | 1.000000 | 0.000000 | 0.002791 | 0.002791 | 0.002791 | 0.119068 |
| views_5 | 1.000000 | 1.000000 | 0.000000 | 0.000413 | 0.000413 | 0.000413 | 0.112345 |
| zero_baseline | — | 0.000000 | 0.000000 | 0.195833 | 0.195833 | 0.195833 | 0.195833 |

## Reference selector comparison (same DLT values, same case edit count)

| Selector | AbsRel | Precision | Recall | FPR |
|---|---:|---:|---:|---:|
| witness | 0.001138 | 1.000000 | 1.000000 | 0.000000 |
| reprojection | 0.146865 | 0.255319 | 0.255319 | 0.479452 |
| depth_disagreement | 0.001138 | 1.000000 | 1.000000 | 0.000000 |
| robust_depth_disagreement | 0.001138 | 1.000000 | 1.000000 | 0.000000 |
| robust_reprojection | 0.105279 | 0.468085 | 0.468085 | 0.342466 |
| ransac_outlier | 0.097023 | 0.510638 | 0.510638 | 0.315068 |
| ransac_depth_disagreement | 0.001138 | 1.000000 | 1.000000 | 0.000000 |
| uncertainty | 0.055398 | 0.723404 | 0.723404 | 0.178082 |
| low_confidence | 0.097023 | 0.510638 | 0.510638 | 0.315068 |
| random | 0.117447 | 0.406250 | 0.406250 | 0.382277 |

Both per-case and per-track budgets, DLT and RANSAC replacement estimators, every selector and all seeds/draws are in mask_results.json and mask_summary.csv. Confidence is constant 1 in Phase 2, so low-confidence selection is a randomized tie, not an informative model confidence baseline. Scores named depth disagreement are normalized by the supplied half-width. Reprojection and RANSAC-outlier scores identify different failure types from inaccurate model depths; their disagreement-based versions are included as the stronger depth-repair selectors.
