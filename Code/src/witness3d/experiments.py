"""Reproducible future experiments and resumable per-track baseline evaluation."""
from __future__ import annotations

import copy
import json
import os
from dataclasses import asdict, replace
from itertools import product
from pathlib import Path

import numpy as np

from . import baselines
from .constraints import track_polytope
from .exact import Box
from .graph import image_neighbor_edges
from .io import atomic_json, file_hash, load_inputs, plain, save_inputs, spec_hash
from .metrics import binary_metrics, depth_metrics, macro_scene_aggregate, repair_metrics, witness_metrics, paired_scene_difference
from .observations import Track
from .pipeline import environment_record, source_fingerprint
from .profiling import Profile
from .reconcile import reconcile
from .repair import RepairConfig, local_repair
from .solver import SolverConfig, Status, solve
from .synthetic import Inputs, SyntheticConfig, Truth, generate
from .verify import check_artifact, check_envelope

METHODS = {"none", "fusion", "triangulation", "ransac", "robust_triangulation", "robust_depth",
           "residual_threshold", "witness_only", "local", "local_all", "global", "global_uniform", "ba_diagnostic"}


def _changed_track(track, depths):
    observations = []
    for observation in track.observations:
        value = depths.get(observation.id, observation.depth)
        if value is None or not np.isfinite(value) or value <= observation.half_width:
            raise ValueError("Baseline produced an invalid fixed-width depth interval")
        observations.append(replace(observation, depth=float(value)))
    return Track(track.id, tuple(observations))


def run_inputs(inputs: Inputs, config: dict, output: str) -> list[dict]:
    """Profile complete inference work, including shared status queries and I/O."""
    existing = len(list((Path(output) / "records").glob("*.json")))
    with Profile() as total:
        records = _run_inputs(inputs, config, output)
    atomic_json(Path(output) / "run_efficiency.json", {**total.as_dict(),
                                                       "preexisting_record_checkpoints": existing,
                                                       "record_count": len(records),
                                                       "scope": "all_selected_methods_including_shared_queries_and_io"})
    return records


def _run_inputs(inputs: Inputs, config: dict, output: str) -> list[dict]:
    """Inference-only entrypoint: no Truth/reference parameter exists here."""
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    methods = config.get("methods", ["none", "triangulation", "ransac", "robust_depth", "witness_only", "local", "local_all", "global"])
    if len(set(methods)) != len(methods) or not set(methods) <= METHODS:
        raise ValueError("Unknown or duplicate methods")
    if int(config.get("global", {}).get("block_tracks", 32)) < 1:
        raise ValueError("Positive global block size required")
    solver = SolverConfig(**config.get("solver", {}))
    repair = RepairConfig(**config.get("repair", {}))
    identity = {"config": config, "inputs": {"box": inputs.box, "tracks": inputs.tracks,
                                               "cameras": [vars(c) for c in inputs.cameras.values()]},
                "implementation_hash": source_fingerprint(Path(__file__).parent), "environment": environment_record()}
    signature = spec_hash(identity)
    state_path, records_path = output_path / "state.json", output_path / "records.jsonl"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state["signature"] != signature:
            raise ValueError("Run spec changed; resume refused")
    else:
        state = {"signature": signature, "identity": plain(identity), "completed": [], "schema_version": 1}
        if records_path.exists():
            raise ValueError("Records exist without their run state")
        atomic_json(state_path, state)
    # Each record is an independent atomic checkpoint; assemble JSONL from these
    # files, avoiding an append/state crash race or duplicate resumed records.
    records_dir = output_path / "records"
    records_dir.mkdir(exist_ok=True)
    records = []
    for track_index, track in enumerate(inputs.tracks):
        system = track_polytope(track, inputs.cameras, inputs.box, repair.z_min)
        before = solve(system, solver)
        original_depths = {o.id: o.depth for o in track.observations}
        for method in methods:
            key = spec_hash([track.id, method])
            checkpoint = records_dir / f"{key}.json"
            if checkpoint.exists():
                record = json.loads(checkpoint.read_text())
                if record.get("run_signature") != signature:
                    raise ValueError("Checkpoint signature mismatch")
                records.append(record)
                continue
            record = {"schema_version": 1, "run_signature": signature, "track": track.id,
                      "method": method, "original_depths": original_depths, "depths": dict(original_depths),
                      "state": "UNCHANGED", "status_before": before.status.value, "status_after": before.status.value,
                      "detected": [], "edit_ids": [], "artifacts": [], "geometry_residual_flags": [],
                      "z_min": repair.z_min}
            point = None
            with Profile() as profile:
                if method in {"local", "local_all"}:
                    result = local_repair(track, inputs.cameras, inputs.box,
                                          replace(repair, localize=method != "local_all"), solver)
                    record.update(depths={o.id: o.depth for o in result.repaired.observations},
                                  state="SELECTIVE_REPAIR", status_after=result.after.status.value,
                                  detected=list(result.edits), edit_ids=list(result.edits),
                                  measurement_status=result.measurement.status.value, reason=result.reason,
                                  conflict=result.conflict, envelopes=plain(result.envelopes))
                    record["envelope_trace_checks"] = {
                        oid: check_envelope(plain(envelope)).accepted
                        for oid, envelope in result.envelopes.items()} if repair.save_evidence else {}
                    if result.conflict is not None and result.conflict["artifact"] is not None:
                        record["artifacts"].append(result.conflict["artifact"])
                    artifact = result.after.artifact(track_polytope(result.repaired, inputs.cameras, inputs.box, repair.z_min))
                    if artifact is not None:
                        record["artifacts"].append(artifact)
                elif method == "witness_only":
                    record["state"] = "DETECTION_ONLY"
                    artifact = before.artifact(system)
                    if artifact is not None:
                        record["artifacts"].append(artifact)
                    # No group membership is mislabeled individual depth fault.
                    record["group_contradiction"] = before.status == Status.CONTRADICTION
                elif method == "none":
                    pass
                elif method in {"global", "global_uniform"}:
                    # Joint baseline is run on a bounded neighborhood around this
                    # track. Centered block membership is deterministic.
                    size = min(128, int(config.get("global", {}).get("block_tracks", 32)))
                    start = (track_index // size) * size
                    block = inputs.tracks[start:start+size]
                    global_key = spec_hash([method, start])
                    global_path = output_path / "global" / (global_key + ".json")
                    if global_path.exists():
                        global_record = json.loads(global_path.read_text())
                    else:
                        controls = {k: v for k, v in config.get("global", {}).items() if k != "block_tracks"}
                        result = reconcile(block, inputs.cameras, inputs.box, image_neighbor_edges(block),
                                           uniform_weights=method == "global_uniform", solver=solver, z_min=repair.z_min,
                                           **controls)
                        global_record = {"state": result.state, "depths": result.depths,
                                         "points": plain(result.points), "history": result.objective_history,
                                         "reason": result.reason, "run_signature": signature}
                        atomic_json(global_path, global_record)
                    if global_record["run_signature"] != signature:
                        raise ValueError("Global checkpoint mismatch")
                    record["state"], record["reason"] = global_record["state"], global_record["reason"]
                    if global_record["state"] == "CONVERGED_NUMERICALLY":
                        record["depths"] = {o.id: global_record["depths"][o.id] for o in track.observations}
                        point = np.array(global_record["points"][track_index-start])
                    record["runtime_scope"] = "first_record_in_block_computes_global_solve_others_read_cache"
                elif method == "ba_diagnostic":
                    diagnostic_path = output_path / "ba_diagnostic.json"
                    if diagnostic_path.exists():
                        estimate = json.loads(diagnostic_path.read_text())
                    else:
                        estimate = plain(baselines.bundle_adjustment_style(inputs.tracks[:32], inputs.cameras))
                        atomic_json(diagnostic_path, estimate)
                    record["state"] = estimate["state"]
                    record["information_regime"] = "joint_pose_refinement_with_pose_prior"
                    if estimate["points"] is not None and track_index < 32:
                        point = np.array(estimate["points"][track_index])
                        record["depths"] = {o.id: float((np.array(estimate["cameras"][o.camera_id][0]) @ point +
                                                               np.array(estimate["cameras"][o.camera_id][1]))[2]) for o in track.observations}
                    elif track_index >= 32:
                        record["state"] = "OUTSIDE_DIAGNOSTIC_BLOCK_KEEP_ORIGINAL"
                elif method == "residual_threshold":
                    flags = baselines.residual_threshold(track, inputs.cameras, config.get("residual_threshold", 2.0))
                    record["geometry_residual_flags"] = [o.id for o, flag in zip(track.observations, flags) if flag]
                    record["state"] = "RESIDUAL_DETECTION_ONLY"
                else:
                    if method == "fusion":
                        estimate = baselines.average_fusion(track, inputs.cameras)
                    elif method == "triangulation":
                        estimate = baselines.linear_triangulation(track, inputs.cameras)
                    elif method == "ransac":
                        estimate = baselines.ransac_triangulation(track, inputs.cameras, config.get("seed", 0),
                                                                 threshold=config.get("ransac_threshold", 2.0))
                    else:
                        estimate = baselines.robust_refine(track, inputs.cameras, method == "robust_depth",
                                                            loss=config.get("robust_loss", "huber"))
                    record["state"] = estimate.state
                    point = estimate.point
                    if point is not None:
                        record["depths"] = baselines.depths_from_point(track, inputs.cameras, point)
                if method not in {"local", "local_all", "none", "witness_only", "residual_threshold"}:
                    try:
                        repaired_track = _changed_track(track, record["depths"])
                        checked = solve(track_polytope(repaired_track, inputs.cameras, inputs.box, repair.z_min), solver)
                        record["status_after"] = checked.status.value
                    except ValueError as exc:
                        record["state"] = "FAILED_KEEP_ORIGINAL"
                        record["reason"] = str(exc)
                        record["depths"] = original_depths.copy()
                        point = None
                    record["edit_ids"] = [id for id, d in record["depths"].items() if d != original_depths[id]]
                if point is not None:
                    from .metrics import consistency_metrics
                    record["point"] = point.tolist()
                    record["consistency"] = consistency_metrics(track, inputs.cameras, point)
            record["efficiency"] = profile.as_dict()
            record["certificate_checks"] = [check_artifact(a).accepted for a in record["artifacts"]]
            atomic_json(checkpoint, record)
            records.append(plain(record))
            state["completed"].append(key)
            atomic_json(state_path, state)
    temporary = records_path.with_suffix(".tmp")
    temporary.write_text("".join(json.dumps(plain(record), allow_nan=False) + "\n" for record in records), encoding="utf-8")
    os.replace(temporary, records_path)
    return records


def evaluate_synthetic(records: list[dict], truth: Truth, inputs: Inputs, scene: str, seed: int) -> list[dict]:
    by_method = {}
    for record in records:
        by_method.setdefault(record["method"], []).append(record)
    results = []
    track_by_id = {track.id: track for track in inputs.tracks}
    for method, group in by_method.items():
        ids = [id for record in group for id in record["original_depths"]]
        before = np.array([d for record in group for d in record["original_depths"].values()])
        after = np.array([record["depths"][id] for record in group for id in record["original_depths"]])
        reference = np.array([truth.depths[id] for id in ids])
        detected = {id for record in group for id in record["detected"]}
        detection = binary_metrics([id in detected for id in ids], [truth.wrong_claims[id] for id in ids])
        result = {"scene": scene, "seed": seed, "method": method, **depth_metrics(after, reference),
                  **repair_metrics(before, after, reference), "claim_detection": detection,
                  "before_abs_rel": depth_metrics(before, reference)["abs_rel"],
                  "unknown_fraction": float(np.mean([r["status_after"] == Status.UNKNOWN.value for r in group])),
                  "certificate_submissions": sum(len(r["certificate_checks"]) for r in group),
                  "certificate_valid": sum(sum(r["certificate_checks"]) for r in group),
                  "wall_seconds": sum(r["efficiency"]["wall_seconds"] for r in group),
                  "conditional_premises_pixel_coverage": float(np.mean(list(truth.pixel_contained.values())))}
        claims = {o.id: o for track in inputs.tracks for o in track.observations}
        result["mean_depth_interval_width_m"] = float(np.mean([2*claims[id].half_width for id in ids]))
        result["measured_depth_interval_coverage"] = float(np.mean([not truth.wrong_claims[id] for id in ids]))
        row_sizes, block_sizes, submissions = [], [], []
        suspect_ids = set()
        for record in group:
            submissions.extend(record["certificate_checks"])
            conflict = record.get("conflict")
            if conflict is not None:
                artifact = conflict["artifact"]
                y = artifact["certificate"]["y"]
                from .exact import rational
                active = [tag for tag, multiplier in zip(artifact["system"]["tags"], y) if rational(multiplier) > 0]
                row_sizes.append(len(active))
                block_sizes.append(len({tag["observation"] for tag in active if tag["observation"]}))
                suspect_ids.update(conflict["depth_suspects"])
        known_feasible = [track_polytope(track_by_id[r["track"]], inputs.cameras, inputs.box,
                                         r.get("z_min", .01)).contains(truth.points[r["track"]]) for r in group]
        result["witness"] = witness_metrics([r["status_before"] for r in group], submissions, row_sizes, known_feasible)
        result["witness"]["mean_observation_blocks"] = float(np.mean(block_sizes)) if block_sizes else None
        result["suspect_group_localization"] = binary_metrics([id in suspect_ids for id in ids], [truth.wrong_claims[id] for id in ids])
        if any("point" in r for r in group):
            from .metrics import point_metrics
            usable = [r for r in group if "point" in r]
            result["point_accuracy"] = point_metrics([r["point"] for r in usable], [truth.points[r["track"]] for r in usable])
        results.append(result)
    return results


def run_synthetic(config: dict, output: str) -> dict:
    output_path = Path(output)
    identity = spec_hash({"config": config, "source": source_fingerprint(Path(__file__).parent)})
    identity_path = output_path / "experiment_identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text())["signature"] != identity:
        raise ValueError("Synthetic specification changed; select a fresh output directory")
    atomic_json(identity_path, {"signature": identity, "config": config})
    metrics = []
    base = dict(config.get("synthetic", {}))
    for seed in config.get("seeds", [0]):
        controls = SyntheticConfig(**{**base, "seed": seed})
        inputs, truth = generate(controls)
        path = output_path / f"seed_{seed}"
        save_inputs(path / "inputs.json", inputs)
        atomic_json(path / "evaluation_truth.json", truth)
        records = run_inputs(inputs, {**config.get("experiment", {}), "seed": seed}, str(path / "run"))
        metrics.extend(evaluate_synthetic(records, truth, inputs, str(config.get("scene_name", "synthetic")), seed))
    methods = sorted({r["method"] for r in metrics})
    report = {"schema_version": 1, "config": config, "records": metrics,
              "aggregates": {method: macro_scene_aggregate([r for r in metrics if r["method"] == method],
                                                             ["abs_rel", "before_abs_rel", "rmse", "damaged_fraction", "corrected_fraction"])
                             for method in methods}}
    if "none" in methods:
        report["paired_abs_rel_vs_none"] = {method: paired_scene_difference(metrics, method, "none", "abs_rel")
                                             for method in methods if method != "none"}
    atomic_json(output_path / "metrics.json", report)
    return report


def expand_ablation(config: dict) -> list[dict]:
    axes = config["axes"]
    names = sorted(axes)
    if any(not isinstance(axes[name], list) or not axes[name] for name in names):
        raise ValueError("Every ablation axis must have values")
    output = []
    for values in product(*(axes[name] for name in names)):
        spec = copy.deepcopy(config["base"])
        for dotted, value in zip(names, values):
            current = spec
            parts = dotted.split(".")
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value
        widths = {name: value for name, value in zip(names, values) if "width" in name or "radius" in name}
        output.append({"id": spec_hash(spec)[:16], "spec": spec, "uncertainty_controls": widths,
                       "comparability_warning": "Changing width/coverage changes the decision problem; compare matched strata" if widths else None})
    return output

