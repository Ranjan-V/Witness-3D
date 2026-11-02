# Kaggle readiness — future work only

**No Kaggle session, upload, installation, model inference or real dataset run was performed.** CPU synthetic correctness is locally exercised. Real-data readiness remains blocked by calibrated geometry, trustworthy target/budget assumptions, adapter parity and a defensible contribution beyond established robust set estimation. The current research framing is NO-GO for an expensive benchmark/manuscript campaign; a narrowly scoped calibration/feasibility pilot can be designed after these issues are addressed.

## Preconditions

1. Decide whether to pursue a verification benchmark or a materially stronger method. Use `novelty_risk.md` and the matched-mask results; do not start with a claim of superior reconstruction accuracy.
2. Supply a small user-owned static scene export with rectified RGB, registered metric optical-axis reference depth, explicitly directed poses and vetted K. Keep calibration and evaluation scenes separate. Set the world box from external scene knowledge; the illustrative box is not validated for a real scene.
3. Measure pose/pixel/association uncertainty on calibration data and freeze the budget/width protocol. Either supply conservative camera/query error bounds or label corrections nominal and conditional. q=1 is not justified merely by an average outlier percentage. Target association and surface sampling remain distinct premises.
4. For a later frozen-depth pilot, supply the local DA-V2 metric Small source and correct checkpoint, and check adapter/upstream parity on a few images. No weights or model compatibility were validated in Phase 2. MiDaS additionally requires its local backbone source and a disjoint geometry-only scale calibration; defer it until the metric pipeline is verified.
5. Reproduce CPU tests in the target Linux environment. The local run used source imports; wheel packaging was blocked by missing wheel and old build-tool version. If packaging is needed, provide a compatible offline wheelhouse (including setuptools>=68 and wheel) or obtain explicit authorization for network provisioning. Windows versions are observations, not a tested Linux lock.

## Precise next CPU sequence, after a future Kaggle run is authorized

Copy the Code directory to a writable working directory and define W3D_CODE and W3D_OUTPUT. Use fresh output directories. Provision compatible CPU dependencies first; the commands below do not install or download anything.

```bash
cd "$W3D_CODE"
export PYTHONPATH="$W3D_CODE/src"
export CUDA_VISIBLE_DEVICES=-1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
mkdir -p "$W3D_OUTPUT"
python -m pip freeze > "$W3D_OUTPUT/environment_freeze.txt"
python -m pytest -q --junitxml="$W3D_OUTPUT/tests.xml"
python scripts/validate_synthetic.py --pilot --output "$W3D_OUTPUT/pilot"
python scripts/validate_numerics.py "$W3D_OUTPUT/numerics"
python scripts/validate_synthetic.py --output "$W3D_OUTPUT/sweep"
python scripts/verify_validation_artifacts.py "$W3D_OUTPUT/sweep" "$W3D_OUTPUT/checker.json"
```

The current expected pytest count is 109 with no failures/skips. Numerical results may vary in solver proposals/timing; accepted artifacts must remain sound, and premise-qualified selective harm must remain zero. Stop and inspect any violation instead of relaxing the exact checker. These commands have been exercised locally through their Windows equivalents, not on Kaggle.

## Real-data pilot sequence, after preconditions and future authorization

Keep model inference and geometry/evaluation as separate stages. Set W3D_MANIFEST, W3D_DAV2_METRIC_SOURCE and W3D_DAV2_CHECKPOINT to vetted local assets. Start with one small scene, batch 1, and a reduced geometric configuration with global block_tracks=4, both local/local_all, q=0 and q=1 recorded separately, and full evidence. Use the CPU model configuration initially if CPU inference is explicitly authorized; no GPU is required for the geometry stage.

```bash
python -m witness3d depth --config configs/depth_cpu.yaml --manifest "$W3D_MANIFEST" --output "$W3D_OUTPUT/depth"
python -m witness3d extract --config configs/extract.yaml --manifest "$W3D_MANIFEST" --cache "$W3D_OUTPUT/depth" --output "$W3D_OUTPUT/tracks"
python -m witness3d --cpu-threads 1 run --config "$W3D_PILOT_GEOMETRY_CONFIG" --inputs "$W3D_OUTPUT/tracks/inputs.json" --output "$W3D_OUTPUT/run"
python -m witness3d evaluate --manifest "$W3D_MANIFEST" --sampling "$W3D_OUTPUT/tracks/sampling.json" --results "$W3D_OUTPUT/run/records.jsonl" --output "$W3D_OUTPUT/sparse_metrics.json"
python scripts/extract_certificates.py "$W3D_OUTPUT/run/records.jsonl" "$W3D_OUTPUT/certificates"
python -m witness3d apply-depth --sampling "$W3D_OUTPUT/tracks/sampling.json" --results "$W3D_OUTPUT/run/records.jsonl" --method local_all --output "$W3D_OUTPUT/repaired_depth"
python -m witness3d evaluate-dense --manifest "$W3D_MANIFEST" --sampling "$W3D_OUTPUT/tracks/sampling.json" --depth-index "$W3D_OUTPUT/repaired_depth/index.json" --output "$W3D_OUTPUT/dense_metrics.json"
```

The scene manifest, calibrated extraction config and pilot geometry config must exist before these commands. Evaluate native-grid sparse improvements separately from full-grid changes; do not present sparse edits as dense reconstruction. Report all abstentions, invalid matches, interval coverage, width and harmed predictions. Only scale beyond the pilot if a meaningful accuracy/damage/coverage advantage survives matched RANSAC/triangulation controls and the assumptions are empirically credible. The original `docs/kaggle.md` is a Phase 1 future plan; this assessment supersedes its readiness implications.
