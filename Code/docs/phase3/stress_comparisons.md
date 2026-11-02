# Continuous-error difficult-regime controls

Five seeds, 12 tracks/seed, five available cameras. Partial occlusion means missing observations, not rendered boundaries. Width is 3% of prediction. Shared observations and all-population evaluation. These are controlled falsification cases, not realistic imagery or significance tests.

| Scenario | Original | DLT all | RANSAC all | W repair | W mask + DLT | Depth disagreement + DLT | W mask + RANSAC | RANSAC disagreement + RANSAC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| contamination | 0.136210 | 0.455511 | 0.002123 | 0.064871 | 0.237286 | 0.420326 | 0.058443 | 0.029490 |
| continuous | 0.136210 | 0.001866 | 0.001866 | 0.023101 | 0.010728 | 0.010683 | 0.010728 | 0.010683 |
| heterogeneous_quality | 0.125893 | 0.019298 | 0.007851 | 0.061909 | 0.040391 | 0.039629 | 0.036278 | 0.034104 |
| misleading_confidence | 0.136210 | 0.001866 | 0.002470 | 0.023101 | 0.010728 | 0.010683 | 0.011108 | 0.011115 |
| near_zero | 0.136210 | 0.400897 | 181.768355 | 0.136210 | 0.136210 | 0.136210 | 0.136210 | 0.136210 |
| partial_occlusion | 0.146072 | 0.001994 | 0.001994 | 0.064468 | 0.048703 | 0.023781 | 0.048703 | 0.023782 |
| pose_uncertainty | 0.136210 | 0.008025 | 0.010724 | 0.121013 | 0.120139 | 0.107324 | 0.120372 | 0.108025 |
