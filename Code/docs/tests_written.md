# Written tests — all unexecuted

No Python interpreter, test runner, import probe, syntax parser, notebook, numerical smoke test or model inference was executed during authoring. Test expectations below are specifications, not passing results.

| File | Intended coverage |
|---|---|
| conftest.py | Analytic rectified cameras, true point and declared box fixtures. |
| test_geometry.py | Projection/backprojection, c2w inversion, pixel-center resizing, normalized pixels, range/inverse conversion, quaternion order, invalid K/depth. |
| test_exact_certificates.py | Hand Farkas ray, tiny-residual false-certification attack, domain dependence, exact support, tampering, NaN/Inf, dimension checks, rational vertex/roundtrip. |
| test_constraints.py | Analytically feasible points, row count, projection/inequality equivalence, convention rejection, visibility, duplicate tracks, z_min. |
| test_solver.py | Feasible negative coordinates, known contradiction, numerical status alone insufficient, invalid dual ray, conservative bound fallback. |
| test_envelopes_and_repair.py | Prediction independence, q-outlier containment, full trace checks, missing branch rejection, cap-before-solve, unknown retention, outward rounding, known-error repair, locality/conflicting edits. |
| test_witnesses.py | Small/deletion/dual verified conflicts and budget-limited minimality labels. |
| test_synthetic_and_baselines.py | Seeds, separate truth, perfect geometry, analytic fusion/triangulation/RANSAC/refinement, degeneracy. |
| test_global.py | Huber values, objective history/fixed-pose example, impossible-pixel abstention. |
| test_datasets.py | Timestamp association, TUM units/pose, reference sentinels, calibration gates, COLMAP alternation and quaternion convention, distortion rejection, 7-Scenes registration, ScanNet frame conversion. |
| test_metrics.py | Analytic depth/detection/damage/point values, invalid/empty cases, scene rather than pixel averaging. |
| test_matching.py | Conflicting same-view track merge and optional OpenCV empty feature path. |
| test_calibration_and_models.py | Analytic inverse-depth conversion, calibration/evaluation overlap, identifiability rejection, local source gates. No checkpoint inference. |
| test_io_and_integration.py | Input roundtrip, GT-field rejection, required env vars, future per-method run/resume/signature checks, ablation identity/coverage warnings. |
| test_pipeline_contracts.py | Nearest-pixel localization inflation, reference-depth access forbidden during extraction, cache/track integration and nonexistent-method materialization rejection. |

Still requiring future verification: actual installed dependency compatibility, Python parsing/imports, all test outcomes, model adapter parity, real dataset registration and camera conventions, memory peaks, runtime, repair coverage, robustness under violated premises, dense outputs and full-grid evaluation. The static audit cannot establish any of these by execution.
