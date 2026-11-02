#!/usr/bin/env bash
# WRITE-ONLY DELIVERABLE. The assistant did not execute this file.
set -euo pipefail
: "${W3D_CODE:?Path to prepared Code directory}"
: "${W3D_MANIFEST:?Path to vetted manifest.json}"
: "${W3D_OUTPUT:?Writable run directory}"
: "${W3D_DAV2_METRIC_SOURCE:?Local upstream metric_depth directory}"
: "${W3D_DAV2_CHECKPOINT:?Local metric Hypersim Small checkpoint}"
cd "$W3D_CODE"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
# Environment provisioning is a separate user action documented in docs/kaggle.md.
python -m pytest tests -q
python -m witness3d --cpu-threads 2 synthetic --config configs/synthetic_cpu.yaml --output "$W3D_OUTPUT/synthetic"
python -m witness3d depth --config configs/depth_t4.yaml --manifest "$W3D_MANIFEST" --output "$W3D_OUTPUT/depth"
python -m witness3d extract --config configs/extract.yaml --manifest "$W3D_MANIFEST" --cache "$W3D_OUTPUT/depth" --output "$W3D_OUTPUT/tracks"
python -m witness3d run --config configs/geometric_cpu.yaml --inputs "$W3D_OUTPUT/tracks/inputs.json" --output "$W3D_OUTPUT/run"
python -m witness3d evaluate --manifest "$W3D_MANIFEST" --sampling "$W3D_OUTPUT/tracks/sampling.json" --results "$W3D_OUTPUT/run/records.jsonl" --output "$W3D_OUTPUT/metrics.json"
python -m witness3d apply-depth --sampling "$W3D_OUTPUT/tracks/sampling.json" --results "$W3D_OUTPUT/run/records.jsonl" --method local --output "$W3D_OUTPUT/repaired_depth"
python -m witness3d evaluate-dense --manifest "$W3D_MANIFEST" --sampling "$W3D_OUTPUT/tracks/sampling.json" --depth-index "$W3D_OUTPUT/repaired_depth/index.json" --output "$W3D_OUTPUT/dense_metrics.json"
python -m witness3d plot --metrics "$W3D_OUTPUT/metrics.json" --output "$W3D_OUTPUT/plots"
python -m witness3d ablate --config configs/ablations_geometry.yaml --output "$W3D_OUTPUT/ablation_geometry"
# Review generated specs before manually adding --execute to an ablate command.

