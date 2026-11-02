# Witness3D research reference

**Phase 2 status (2026-11-02): 109 CPU tests passed; controlled synthetic validation completed.** See [the full validation report](docs/validation/README.md) for actual results, preserved failures/fixes, limitations and the NO-GO decision for the unchanged research contribution. No pretrained inference, training, GPU/TPU, external dataset download, Kaggle execution or Paper editing occurred. The original unexecuted Phase 1 README is preserved in `docs/validation/history/Code_README.md`.

This is a sparse, fixed-camera research reference, not a validated reconstruction system or a manuscript. Start with `../Theory/problem_statement.md`, `../Math/specification.md`, and `docs/static_audit.md`.

## Method

Undistorted pixel rectangles and metric optical-axis depth intervals define exact rational half-spaces in a track's world point. SciPy proposes solutions and multipliers; a separate standard-library arithmetic checker accepts feasible points, bounded-domain contradictions and affine support bounds. An unverified numerical result is `UNKNOWN`.

The principal candidate method uses depth-free target-preserving q-outlier hypotheses to bound a target depth independently of all predicted depths. Only individually refuted depth claims are clipped to conservative outer envelopes; untouched observations remain equal. Every edited track is rebuilt and rechecked. A complete-envelope checker audits hypothesis coverage as well as each support/exclusion certificate.

The conditional result is scalar depth-error non-increase when the target association, camera, inlier-pixel containment, auxiliary outlier budget and world-domain premises hold. It does not establish physical camera accuracy, authenticate a correspondence, guarantee dense accuracy, or guarantee joint feasibility after several scalar edits. The novelty of this protocol remains unresolved.

## Contents

* `src/witness3d/`: geometry, exact systems/checker, LP proposals, witnesses, q-hypothesis envelopes, local repair, convex global baseline, pretrained adapters, ORB tracks, four dataset adapters, synthetic generation, baselines, metrics, resource instrumentation, staged pipelines and CLI.
* `tests/`: analytic, integration and adversarial tests; the latest executed suite passed 109 cases with no failures/skips. See `docs/validation/test_report.md`.
* `configs/`: CPU/T4/model/uncertainty/ablation controls and vetted-export manifest templates.
* `scripts/`: future verification, artifact extraction, plotting and execution sequences.
* `docs/`: assumptions, schemas, model/dataset dependencies, Kaggle sequence, resources and static audit.

## Future environment preparation

These commands are provided as files only; execute them yourself when ready. Use Python >=3.10 and a dedicated environment. The authoring environment has not been inspected for installed dependencies.

```bash
python -m pip install -e '.[test,plots]'
# Install an appropriate PyTorch/torchvision pair for your CPU/CUDA environment,
# then add vision dependencies. The environment must be verified by the user.
python -m pip install -e '.[vision]'
```

The core requires NumPy, SciPy/HiGHS, Pillow and PyYAML. `psutil` is optional for sampled process RSS. No runtime dependency lock is supplied without a working environment; record resolved versions after successful user validation. Local upstream model repositories have additional dependencies and licensing requirements. Do not assume unconstrained newest `timm` works with historical MiDaS internals.

## Future CPU-first validation

From this directory, after preparation:

```bash
python -m pytest tests -q
python -m witness3d --cpu-threads 2 synthetic --config configs/synthetic_cpu.yaml --output outputs/synthetic_cpu
python -m witness3d plot --metrics outputs/synthetic_cpu/metrics.json --output outputs/synthetic_cpu/plots
```

Stop after a failed test. Investigate rather than relaxing the exact checker. On Windows a corresponding sequence is written in `scripts/future_checks.ps1`. The test suite includes exact analytic contradictions and feasible negative-coordinate systems, false-certification attacks, outward rounding, complete q-hypothesis accounting, repair locality, metadata formats and resume identity checks.

## Future real-data sequence

1. Prepare a small, registered, undistorted RGB export with vetted calibration and poses. Edit a manifest adapter template, replacing `REQUIRED_...` provenance and setting the actual world domain. Templates intentionally refuse unchanged provenance.
2. Set local input/checkpoint/source paths. No command retrieves data or model weights.
3. Prepare a canonical JSON manifest; cache frozen depth; extract tracks; run geometric baselines/repair; only then read reference depth for evaluation.

```bash
python -m witness3d prepare --config configs/manifests/tum.yaml --output outputs/manifest.json
python -m witness3d depth --config configs/depth_cpu.yaml --manifest outputs/manifest.json --output outputs/depth
python -m witness3d extract --config configs/extract.yaml --manifest outputs/manifest.json --cache outputs/depth --output outputs/tracks
python -m witness3d run --config configs/geometric_cpu.yaml --inputs outputs/tracks/inputs.json --output outputs/run
python -m witness3d evaluate --manifest outputs/manifest.json --sampling outputs/tracks/sampling.json --results outputs/run/records.jsonl --output outputs/metrics.json
python -m witness3d apply-depth --sampling outputs/tracks/sampling.json --results outputs/run/records.jsonl --method local --output outputs/repaired_depth
python -m witness3d plot --metrics outputs/metrics.json --output outputs/plots
```

The default evaluation is **unique track-sampled pixels**, with all conflicting repeated-pixel proposals rejected. Materialized float64 maps preserve other values exactly; no dense propagation is performed. Full-grid evaluation is a separate command documented in `docs/evaluation.md`. Neither sparse evaluation nor materialization may be called a dense improvement result without full-grid reference metrics and coverage.

## Future certificate inspection

```bash
python scripts/extract_certificates.py outputs/run/records.jsonl outputs/certificates
python scripts/verify_certificate.py outputs/certificates/000000.json
python -m witness3d verify outputs/certificates/000000.json
# A full Envelope object exported from a record can be checked with:
python -m witness3d verify path/to/envelope.json --envelope
```

The verifier accepts only finite encoded input-level facts. It does not independently know that an image, camera pose or declared domain represents reality.

## Future ablations

```bash
python -m witness3d ablate --config configs/ablations_geometry.yaml --output outputs/geometry_specs
python -m witness3d ablate --config configs/ablations_robustness.yaml --output outputs/robustness_specs
python -m witness3d ablate --config configs/ablations_models_datasets.yaml --output outputs/model_dataset_specs
# Only after reviewing the run count and resource needs:
python -m witness3d ablate --config configs/ablations_geometry.yaml --output outputs/geometry_runs --execute
python scripts/plot_ablation.py outputs/geometry_runs/ablation_index.json outputs/coverage_recall.png
```

Real/model/dataset axes generate explicit staged run specifications; they are not silently executed through the synthetic runner. Use each spec to prepare its own manifest/cache/tracks and run config. `proposal_tolerance` changes numerical proposals only; the exact acceptance inequality has no tolerance. Changing uncertainty widths changes the verification task; always report width and measured coverage beside detection rates.

## Resource and resume contract

CPU verification is independent of GPUs. Start with 16 synthetic tracks and 3-view windows, q=0, then q=1. Exact rational arithmetic and exhaustive conflict extraction can be expensive. `small` extraction is for tiny systems, `dual` is the default and makes no minimum claim. A hypothesis cap causes abstention, never partial enumeration. The global reference uses <=128 tracks per block and dense constrained numerical subproblems, so start with 16-32.

Model cache and geometric-run signatures include input/config, package source and environment identities; cache entries also hash RGB and depth files. Per-record writes are atomic. Changed specs refuse resume. Run directories and cache directories must be isolated between processes/devices. RSS sampling requires optional psutil; GPU time is synchronized and peak allocated bytes are recorded by the adapters. No runtime or memory figure here is measured.

For the exact Kaggle preparation and execution sequence, see `docs/kaggle.md` and `scripts/kaggle_sequence.sh`. TPU is explicitly disabled pending a real supported workload. Two T4s are independent devices, not a pooled-memory accelerator.

## Research decision

Classical triangulation, Farkas certificates, Helly support sets, IIS extraction, scalar clipping, robust losses, RANSAC, BA and factor graphs are not inventions of this project. A targeted literature audit is in `../Theory/related_work.md`; set-membership and duality-based outlier removal remain particularly important unresolved overlaps. Main-track novelty and practical utility require future comparative experiments and deeper prior-art review.
