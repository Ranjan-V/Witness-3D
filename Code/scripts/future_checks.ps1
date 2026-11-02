# WRITE-ONLY DELIVERABLE: not executed by the authoring assistant.
# Run manually from Code after preparing your environment.
$ErrorActionPreference = 'Stop'
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; stop before experiments.' }
python -m witness3d --cpu-threads 2 synthetic --config configs/synthetic_cpu.yaml --output outputs/synthetic_cpu
if ($LASTEXITCODE -ne 0) { throw 'Synthetic experiment failed.' }

