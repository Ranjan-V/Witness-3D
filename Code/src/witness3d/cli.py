from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Witness3D future-run research tools")
    p.add_argument("--cpu-threads", type=int, default=2)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("synthetic", "run", "depth", "extract", "prepare", "ablate"):
        s = sub.add_parser(name)
        s.add_argument("--config", required=True)
        s.add_argument("--output", required=True)
        if name == "run":
            s.add_argument("--inputs", required=True)
        if name in {"depth", "extract"}:
            s.add_argument("--manifest", required=True)
        if name == "extract":
            s.add_argument("--cache", required=True)
        if name == "ablate":
            s.add_argument("--execute", action="store_true", help="Otherwise write run specifications only")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--manifest", required=True)
    evaluate.add_argument("--sampling", required=True)
    evaluate.add_argument("--results", required=True)
    evaluate.add_argument("--output", required=True)
    dense = sub.add_parser("evaluate-dense")
    dense.add_argument("--manifest", required=True)
    dense.add_argument("--sampling", required=True)
    dense.add_argument("--depth-index", required=True)
    dense.add_argument("--output", required=True)
    calibrate = sub.add_parser("calibrate")
    calibrate.add_argument("--manifest", required=True)
    calibrate.add_argument("--cache", required=True)
    calibrate.add_argument("--output", required=True)
    calibrate.add_argument("--views", type=int, default=3)
    verify = sub.add_parser("verify")
    verify.add_argument("artifact")
    verify.add_argument("--envelope", action="store_true")
    plot = sub.add_parser("plot")
    plot.add_argument("--metrics", required=True)
    plot.add_argument("--output", required=True)
    apply = sub.add_parser("apply-depth")
    apply.add_argument("--sampling", required=True)
    apply.add_argument("--results", required=True)
    apply.add_argument("--method", default="local")
    apply.add_argument("--output", required=True)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.cpu_threads < 1:
        raise ValueError("Positive CPU thread budget required")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(name, str(args.cpu_threads))
    if args.command == "verify":
        from .verify import check_artifact, check_envelope
        checked = (check_envelope if args.envelope else check_artifact)(json.loads(Path(args.artifact).read_text()))
        print(json.dumps({"accepted": checked.accepted, "reason": checked.reason,
                          "exact_value": str(checked.value), "uses_domain": checked.uses_domain}))
        return 0 if checked.accepted else 1
    from .io import atomic_json, load_config, load_inputs
    if args.command == "prepare":
        from .datasets import prepare_manifest
        atomic_json(args.output, prepare_manifest(load_config(args.config)))
    elif args.command == "synthetic":
        from .experiments import run_synthetic
        run_synthetic(load_config(args.config), args.output)
    elif args.command == "run":
        from .experiments import run_inputs
        run_inputs(load_inputs(args.inputs), load_config(args.config), args.output)
    elif args.command == "depth":
        from .pipeline import cache_depth
        cfg = load_config(args.config)
        cache_depth(args.manifest, cfg["model"], args.output, cfg.get("batch_size", 1), cfg.get("max_pixels", 1_000_000))
    elif args.command == "extract":
        from .pipeline import extract_tracks
        extract_tracks(args.manifest, args.cache, args.output, load_config(args.config))
    elif args.command == "calibrate":
        from .pipeline import calibrate_relative
        calibrate_relative(args.manifest, args.cache, args.output, args.views)
    elif args.command == "evaluate":
        from .pipeline import evaluate_real
        atomic_json(args.output, evaluate_real(args.manifest, args.sampling, args.results))
    elif args.command == "evaluate-dense":
        from .pipeline import evaluate_dense
        atomic_json(args.output, evaluate_dense(args.manifest, args.depth_index, args.sampling))
    elif args.command == "apply-depth":
        from .pipeline import materialize_depth
        materialize_depth(args.sampling, args.results, args.method, args.output)
    elif args.command == "plot":
        from .plotting import plot_metrics
        plot_metrics(args.metrics, args.output)
    elif args.command == "ablate":
        from .experiments import expand_ablation, run_synthetic
        runs = expand_ablation(load_config(args.config))
        atomic_json(Path(args.output) / "ablation_index.json", {"runs": runs})
        for run in runs:
            atomic_json(Path(args.output) / run["id"] / "spec.json", run)
            if args.execute:
                if run["spec"].get("kind", "synthetic") != "synthetic":
                    raise ValueError("Real/model/dataset axes generate specs; use the staged cache/extract/run commands")
                run_synthetic(run["spec"], str(Path(args.output) / run["id"]))
    return 0

