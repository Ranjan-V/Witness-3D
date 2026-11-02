# Witness3D: Counterexample-Guided Geometric Verification and Repair of Vision Foundation Models

**Research status: RETIRED as a CVPR main-track candidate.**

This repository preserves a reproducible research and negative-results archive. It is not an accepted or submitted CVPR paper. Controlled experiments validated the geometric verification and certificate implementation, and the final recorded suite reported **114 passing tests**. Classical robust triangulation generally outperformed the proposed repair method. Conventional depth-disagreement selectors reproduced the apparent selective-repair advantage. The central construction overlapped established q-relaxed intersection, and no substantial new algorithmic contribution was established.

## Research record

- [Theory](Theory/README.md): formulation, assumptions, prior work, novelty assessment and experimental design.
- [Mathematics](Math/proof_status_ledger.md): geometry, certificates, conditional guarantees, counterexamples and claim status.
- [Implementation](Code/README.md): source, tests, configurations, adapters and reproduction scripts.
- [Phase 2 validation](Code/docs/validation/README.md): mathematical review, actual tests, exact oracle, synthetic experiments, baseline comparisons and limitations.
- [Phase 3 retirement decision](Code/docs/phase3/README.md): leakage audit, matched-mask comparisons, difficult regimes, attempted rescue and final RETIRE decision.
- [Phase 3 protocol and commands](Code/docs/phase3/audit_and_protocol.md).

The original phase-specific documents and evidence are retained, including historical statements that code had not yet been executed. Later phase reports supersede those execution-status statements. `Paper/` contains only a directory placeholder; no manuscript was written.

## Recorded findings

The reference scenario reported AbsRel 0.19583 for original predictions, 0.00824 for all-target repair, 0.00299 for triangulation and 0.00114 for triangulation on the selective mask. Phase 3 reproduced the last value with a conventional normalized depth-disagreement selector. The synthetic exact-versus-biased prediction mixture explained much of this advantage. Conditional certificate soundness does not establish accurate physical cameras, correct correspondences or improved joint reconstruction.

See the phase reports for every denominator, seed, failure fallback and uncertainty assumption. The archive includes unsuccessful outcomes, invalidated overclaims and regression failures before fixes. No measurements were repeated during GitHub archival.

## Reproduction

The recorded local environment was Python 3.11.9 on Windows, NumPy 1.26.4, SciPy 1.11.1 and pytest 8.4.2. See the [full environment record](Code/docs/validation/environment.json), [observed dependency versions](Code/docs/validation/requirements-validation.txt), [Phase 2 commands](Code/docs/validation/commands.ps1) and [Phase 3 protocol](Code/docs/phase3/audit_and_protocol.md). The local virtual environment is excluded. Source execution used `PYTHONPATH`; offline editable installation was blocked by missing build dependencies. A Linux environment or wheel build was not validated.

After provisioning compatible dependencies, run from `Code/` in a fresh copy:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$env:CUDA_VISIBLE_DEVICES = '-1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest -q
python scripts/validate_synthetic.py --pilot --output outputs/reproduction_pilot
```

The historical final suite count is 114; the commands above are instructions, not archival execution claims. The linked protocols contain full sweep, numerical audit, artifact verification and Phase 3 commands. Some diagnostic scripts intentionally use fixed paths under `docs/`; reproduce in a fresh clone to retain the original recorded evidence. Absolute Windows paths embedded in historical records identify their original environment and may require adaptation. GitHub-relative navigation is provided here.

No pretrained weights, private datasets, credentials, virtual environments or temporary inference caches are included. Model adapters and Kaggle preparation are historical, unvalidated future plans; no model training or real-data validation is claimed. Read [archival provenance](ARCHIVAL.md) and [the file manifest](ARCHIVE_MANIFEST.json) for inclusion and integrity details.
