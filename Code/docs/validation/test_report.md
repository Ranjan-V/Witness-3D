# Actual CPU test results

Latest full suite: **109 passed, 0 failed, 0 errors, 0 skipped**. Pytest reported 4.69 s; JUnit suite duration 4.643 s. Evidence: `tests_after_fixes.txt` and `tests_after_fixes.xml`. These are actual executions, not inferred from test definitions.

| Execution | Passed | Failed | Skipped | Purpose |
|---|---:|---:|---:|---|
| Original suite | 69 | 0 | 0 | Existing 67 functions, expanded by parametrization. |
| Initial adversarial extension | 105 | 0 | 0 | Geometry, certificates, complete envelopes and premise attacks. |
| Two targeted regression demonstrations | 0 | 2 | 0 | Exposed damage-denominator and stale-native-point bugs; 36 other cases deselected by explicit `-k`. |
| Full suite after fixes | 109 | 0 | 0 | All original tests plus 40 added test cases. |

No original test was deleted, skipped, weakened or rewritten. Optional OpenCV matching tests executed because a compatible installed cv2 was available. Model tests validate adapter/configuration contracts; no pretrained model was run. Ground-truth isolation tests poison reference access and exercise inference without a Truth argument.

| Module | Passed |
|---|---:|
| test_geometry | 6 |
| test_exact_certificates | 9 |
| test_constraints | 5 |
| test_solver | 5 |
| test_envelopes_and_repair | 7 |
| test_witnesses | 2 |
| test_synthetic_and_baselines | 4 |
| test_global | 3 |
| test_datasets | 8 |
| test_metrics | 8 |
| test_matching | 2 |
| test_calibration_and_models | 3 |
| test_io_and_integration | 4 |
| test_pipeline_contracts | 3 |
| test_phase2_adversarial | 40 |

The added cases cover valid/invalid multipliers, tampered rows and complete traces, strict zero-margin rejection, gaps below solver tolerance, nearly feasible boundaries, failed solver fallback, empty/domain-only systems, explicit rejection of unbounded boxes, invalid poses/tracks/visibility, zero baseline, broad envelopes, all admissible budgets, miscalibrated pixel bounds, wrong baseline, underestimated outlier budget, harmful repairs and individually plausible but jointly inconsistent depths. Significant fixes have retained regression tests.

Beyond pytest, the numerical audit executed 48 exact-oracle cases and 240 support comparisons; the isolated artifact checker inspected 10,080 saved records. These are separate checks, **not additional pytest passes**. The envelope scaling experiment has 27 configurations/seed instances, six of which correctly abstained at the cap. See `numerical_verification.md`.

The executable environment and commands are in `environment.json`, `requirements-validation.txt` and `commands.ps1`. Pytest plugin autoload was disabled to avoid unrelated globally installed plugins. Runtime dependencies were reused locally; no network installation occurred. Offline packaging remains unvalidated because wheel is missing and the venv's setuptools is below the declared build minimum.
