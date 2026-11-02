# Post-hoc bounded robust baseline controls

Executed after the predeclared sweep exposed runaway unbounded Huber estimates. Same saved inputs, seeds and finite world box; no reference information enters fitting. The original results remain intact. These are generic Huber least-squares controls, not state-of-the-art reproductions. Full configuration and identity are in `results/bounded_controls/protocol.json`.

| Scenario | Bounded robust reprojection | Bounded robust depth | RANSAC | All-target selective |
|---|---:|---:|---:|---:|
| baseline_0p03 | 0.029961 | 0.124108 | 0.029961 | 0.104433 |
| baseline_1 | 0.000897 | 0.001091 | 0.000897 | 0.002432 |
| bias_1p1 | 0.002991 | 0.009649 | 0.002991 | 0.008237 |
| bias_2 | 0.002991 | 0.028210 | 0.002991 | 0.008237 |
| clean_q1 | 0.002991 | 0.028305 | 0.002991 | 0.017861 |
| clean_q2 | 0.002991 | 0.028305 | 0.002991 | 0.195833 |
| correct_predictions | 0.002991 | 0.001119 | 0.002991 | 0.000000 |
| depth_width_0p005 | 0.002991 | 0.028399 | 0.002991 | 0.008237 |
| depth_width_0p1 | 0.002991 | 0.003286 | 0.002991 | 0.008237 |
| depth_width_0p4 | 0.002991 | 0.003022 | 0.002991 | 0.195833 |
| gaussian_noise_0p2 | 0.005239 | 0.028575 | 0.005239 | 0.007566 |
| gaussian_noise_0p75 | 0.017699 | 0.031561 | 0.031176 | 0.136695 |
| outliers_10pct_q0 | 0.268871 | 0.099645 | 0.015486 | 0.032137 |
| outliers_10pct_q1 | 0.268871 | 0.099645 | 0.015486 | 0.029132 |
| outliers_30pct_q0 | 0.556870 | 0.251428 | 0.052861 | 0.114983 |
| outliers_30pct_q1 | 0.556870 | 0.251428 | 0.052861 | 0.071170 |
| pixel_radius_2 | 0.002991 | 0.058529 | 0.002991 | 0.035767 |
| pose_rotation_0p002 | 0.011763 | 0.030517 | 0.019816 | 0.108331 |
| pose_translation_0p002 | 0.004543 | 0.028656 | 0.005052 | 0.008339 |
| pose_translation_0p01 | 0.020061 | 0.032587 | 0.051254 | 0.139324 |
| pure_rotation | 0.219670 | 0.124667 | 0.195833 | 0.195833 |
| reference | 0.002991 | 0.028305 | 0.002991 | 0.008237 |
| track_2_of_5 | 0.004792 | 0.028564 | 0.004792 | 0.011064 |
| track_3_of_5 | 0.002557 | 0.002585 | 0.002557 | 0.003901 |
| undersized_pixel_box | 0.002991 | 0.028305 | 0.005861 | 0.100536 |
| views_2 | 0.005586 | 0.114915 | 0.005586 | 0.021579 |
| views_5 | 0.001357 | 0.002462 | 0.001357 | 0.003825 |
| zero_baseline | 0.195834 | 0.124667 | 0.195833 | 0.195833 |

All 2,240 reported records were audited for finite positive depths and valid returned points within the common world box. See `bounded_control_checks.json`. The controls remove arbitrarily large depths but do not make Huber fitting robust to every false correspondence. RANSAC remains a stronger comparator in the tested outlier cases; Witness3D does not establish an accuracy advantage over it.

Executed runtime: {"wall_seconds": 122.22791369998595, "cpu_seconds": 51.59375, "peak_rss_bytes_sampled": 88743936, "rss_sampling_period_seconds": 0.02}
