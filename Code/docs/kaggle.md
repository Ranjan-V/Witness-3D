# Exact future Kaggle sequence

**Nothing in this sequence was executed by the assistant.** Every command below is a future user action. No notebook is needed; no executed notebook or dummy output exists.

## 1. Prepare inputs outside the run

Select a small static scene export with RGB, calibration, known poses and registered reference depth. Complete `docs/datasets.md` requirements, accept applicable dataset terms and record source licenses. Put the local DA-V2 metric source, its correct Small checkpoint, Code directory and a vetted manifest in Kaggle inputs using your own account. This task did not upload anything. Choose a writable output directory yourself.

For MiDaS, additionally provide local MiDaS and EfficientNet sources, checkpoint and a separate geometry-only calibration manifest. Do not use any evaluation frame for calibration. No paid service is required by this design.

## 2. Prepare and record the environment

Use an available CPU/GPU session. Copy the Code directory into a writable working directory before editable installation; attached Kaggle input directories may be read-only. Keep Kaggle's compatible torch/torchvision/CUDA pair when possible. Environment/package/API verification is required; no lock is claimed to have been tested. If internet is disabled, attach compatible local wheels and upstream sources yourself. Network-enabled provisioning is optional, not part of inference.

```bash
export W3D_CODE=/path/to/your/Code
export W3D_MANIFEST=/path/to/your/vetted/manifest.json
export W3D_OUTPUT=/path/to/your/writable/output
export W3D_DAV2_METRIC_SOURCE=/path/to/Depth-Anything-V2/metric_depth
export W3D_DAV2_CHECKPOINT=/path/to/depth_anything_v2_metric_hypersim_vits.pth
cd "$W3D_CODE"
mkdir -p "$W3D_OUTPUT"
python -m pip install -e '.[test,plots,vision]'
# Optional RSS instrumentation:
python -m pip install psutil
python -m pip freeze > "$W3D_OUTPUT/environment_freeze.txt"
```

Create W3D_OUTPUT before redirecting into it. If the wheel set is already prepared offline, use your local wheelhouse provisioning procedure instead of online package installation. No auto-downloader exists in the Witness3D CLI. Upstream local sources must also be complete, including their small dependencies.

## 3. Validate on CPU before model work

```bash
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
python -m pytest tests -q
python -m witness3d --cpu-threads 2 synthetic --config configs/synthetic_cpu.yaml --output "$W3D_OUTPUT/synthetic"
```

Stop at any test failure, invalid certificate or unexpected conditional-damage result. Do not change exact acceptance to a floating tolerance. Inspect analytical fixtures first. The synthetic run contains evaluation truth in a separate file and passes only `Inputs` to algorithms.

## 4. Cache frozen model output

On a single available T4 (or use `depth_cpu.yaml` with CPU):

```bash
python -m witness3d depth --config configs/depth_t4.yaml --manifest "$W3D_MANIFEST" --output "$W3D_OUTPUT/depth"
```

Start batch 1 if unsure; `depth_t4.yaml` currently specifies 2 as a future measured trial. The official adapter parity check in `docs/models.md` should precede benchmark interpretation. Resume reuses only identical source/checkpoint/config/image hashes. Different device/source/environment may require a new cache directory.

## 5. Extract tracks and run CPU geometry

First edit `configs/extract.yaml` world_box to external scene limits in the manifest world frame. Do not derive the box from evaluation reference depths.

```bash
python -m witness3d extract --config configs/extract.yaml --manifest "$W3D_MANIFEST" --cache "$W3D_OUTPUT/depth" --output "$W3D_OUTPUT/tracks"
python -m witness3d --cpu-threads 2 run --config configs/geometric_cpu.yaml --inputs "$W3D_OUTPUT/tracks/inputs.json" --output "$W3D_OUTPUT/run"
```

Outputs distinguish no repair, fusion, triangulation, RANSAC, robust refinements, detection-only, witness-localized repair, unlocalized repair and global confidence controls. BA-style pose refinement is available only as an explicit separately labeled diagnostic. It is not enabled by default.

## 6. Evaluate and inspect artifacts

```bash
python -m witness3d evaluate --manifest "$W3D_MANIFEST" --sampling "$W3D_OUTPUT/tracks/sampling.json" --results "$W3D_OUTPUT/run/records.jsonl" --output "$W3D_OUTPUT/metrics.json"
python -m witness3d apply-depth --sampling "$W3D_OUTPUT/tracks/sampling.json" --results "$W3D_OUTPUT/run/records.jsonl" --method local --output "$W3D_OUTPUT/repaired_depth"
python -m witness3d evaluate-dense --manifest "$W3D_MANIFEST" --sampling "$W3D_OUTPUT/tracks/sampling.json" --depth-index "$W3D_OUTPUT/repaired_depth/index.json" --output "$W3D_OUTPUT/dense_metrics.json"
python -m witness3d plot --metrics "$W3D_OUTPUT/metrics.json" --output "$W3D_OUTPUT/plots"
python scripts/extract_certificates.py "$W3D_OUTPUT/run/records.jsonl" "$W3D_OUTPUT/certificates"
```

Inspect exact certificate JSONs and envelope trace checks, UNKNOWN rates, widths, q, locality, corruption/damage, runtime and memory. A full trace with no saved evidence is explicitly unauditable offline; broad performance sweeps may disable evidence only after an audited pilot and must disclose that choice.

## 7. Generate and review ablations before executing

```bash
python -m witness3d ablate --config configs/ablations_geometry.yaml --output "$W3D_OUTPUT/geometry_specs"
python -m witness3d ablate --config configs/ablations_robustness.yaml --output "$W3D_OUTPUT/robustness_specs"
# After reviewing the run count, inputs and budget:
python -m witness3d ablate --config configs/ablations_geometry.yaml --output "$W3D_OUTPUT/geometry_runs" --execute
```

The grids can be expensive. Start with a reduced pilot configuration and preserve that config. Do not launch the full Cartesian product merely because it is written. Real model/dataset axes generate staged specs only; each requires its own manifest/cache/extract/run sequence. Hold uncertainty widths and measured coverage fixed for comparisons, and group seeds/windows by scene.

`scripts/kaggle_sequence.sh` contains the same core post-provisioning sequence with stop-on-error semantics. No TPU job exists. Multi-T4 scaling means separate isolated shards with cuda:0/cuda:1 in different configurations; memory is never shared across cards.

Expected output: `depth/index.json`, `depth/depth/*.npy`, `tracks/{inputs,sampling}.json`, `run/state.json`, `run/records/*.json`, `run/records.jsonl`, optional `run/global/*.json`, `metrics.json`, `repaired_depth/*.npy`, `plots/*.png` and exported certificate JSON. Checkpoint/resume occurs per model batch and per track/method record. No research result is included in this repository.
