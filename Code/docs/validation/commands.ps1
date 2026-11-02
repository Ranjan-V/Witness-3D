# Run from D:/CVPR/Code. No command installs packages from the network.
# Executed environment creation:
# py -3.11 -m venv --system-site-packages .venv-validation
# Attempted offline editable install (FAILED: wheel absent; setuptools 65.5.0
# also falls below pyproject's build requirement >=68). Do not count as installed:
# .\.venv-validation\Scripts\python.exe -m pip --disable-pip-version-check install --no-index --no-deps --no-build-isolation -e .

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/CVPR/Code'
$env:CUDA_VISIBLE_DEVICES = '-1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONPATH = 'D:/CVPR/Code/src'
$validationPython = 'D:/CVPR/Code/.venv-validation/Scripts/python.exe'

& $validationPython scripts/validation_environment.py
if ($LASTEXITCODE) { throw 'Environment inventory failed' }
& $validationPython -m pytest -q --junitxml=docs/validation/tests_final.xml
if ($LASTEXITCODE) { throw 'Tests failed' }
# Use fresh output paths to obtain fresh timing rather than resume checkpoints.
& $validationPython scripts/validate_synthetic.py --pilot --output docs/validation/results/pilot_reproduction
if ($LASTEXITCODE) { throw 'Pilot failed' }
& $validationPython scripts/validate_synthetic.py --output docs/validation/results/sweep_reproduction
if ($LASTEXITCODE) { throw 'Sweep failed' }
& $validationPython scripts/validate_numerics.py docs/validation/reproduction
if ($LASTEXITCODE) { throw 'Numerical audit failed' }

# Actual initial runs used results/pilot and results/sweep. Their logs are
# pilot_log.txt and sweep_log.txt. Initial pytest: tests_initial.xml (69 tests).
# Expanded pre-fix suite: tests_adversarial_initial.xml (105 tests).
# Regression demonstration: -k 'invalid_after_depth or failed_baseline',
# tests_regressions_before_fix.xml (2 failed, 36 deselected).
# Fixed full suite: tests_after_fixes.xml (109 tests).
# Additional executed validation/postprocessing commands (from Code):
# python scripts/verify_validation_artifacts.py docs/validation/results/sweep docs/validation/standalone_checker_results.json
# python scripts/summarize_validation.py
# python scripts/validate_bounded_baselines.py
# python scripts/report_bounded_controls.py
# These supplemental scripts deliberately read/write the recorded validation paths;
# use a copied workspace if reproducing without replacing their derived reports.
