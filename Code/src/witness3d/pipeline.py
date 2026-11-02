"""Disk-cached real-data pipeline. Reference depth is opened only in evaluation."""
from __future__ import annotations

import importlib.metadata
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .baselines import linear_triangulation
from .calibration import InverseCalibration, fit_inverse_calibration
from .datasets import FrameInput, load_manifest
from .exact import Box
from .io import atomic_json, file_hash, save_inputs, spec_hash
from .matching import FeatureTrack, match_window
from .metrics import depth_metrics, repair_metrics
from .models import make_adapter
from .observations import Observation, Track
from .synthetic import Inputs


def source_fingerprint(path: Path) -> str:
    return spec_hash({p.relative_to(path).as_posix(): file_hash(p) for p in sorted(path.rglob("*.py"))
                      if ".git" not in p.parts and "__pycache__" not in p.parts})


def environment_record() -> dict[str, Any]:
    import platform
    versions = {}
    for package in ("witness3d", "numpy", "scipy", "torch", "torchvision", "opencv-python-headless", "timm"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {"python": platform.python_version(), "platform": platform.platform(), "versions": versions}


def _save_npy(path: Path, array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.npy")
    np.save(temporary, array, allow_pickle=False)
    os.replace(temporary, path)


def cache_depth(manifest: str, model_config: dict, output: str, batch_size: int = 1,
                 max_pixels: int = 1_000_000) -> dict:
    dataset = load_manifest(manifest)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    source = Path(model_config["repository"])
    identity = {"manifest_hash": file_hash(manifest), "model": model_config,
                "checkpoint_hash": file_hash(model_config["checkpoint"]),
                "upstream_source_hash": source_fingerprint(source),
                "implementation_hash": source_fingerprint(Path(__file__).parent),
                "environment": environment_record()}
    if "backbone_repository" in model_config:
        identity["backbone_source_hash"] = source_fingerprint(Path(model_config["backbone_repository"]))
    signature = spec_hash(identity)
    index_path = output_path / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {
        "schema_version": 1, "signature": signature, "identity": identity, "frames": {}, "batches": []}
    if index["signature"] != signature:
        raise ValueError("Cache specification changed; choose a new output directory")
    missing = []
    for frame in dataset.frames:
        if frame.camera.width * frame.camera.height > max_pixels:
            raise ValueError("Frame exceeds configured pixel budget; prepare a calibrated smaller export")
        image_hash = file_hash(frame.rgb)
        prior = index["frames"].get(frame.id)
        if prior is not None:
            if prior["rgb_hash"] != image_hash:
                raise ValueError("Cached image changed")
            if (output_path / prior["path"]).is_file() and file_hash(output_path / prior["path"]) == prior["depth_hash"]:
                continue
        missing.append((frame, image_hash))
    if batch_size < 1:
        raise ValueError("Positive batch size required")
    if not missing:
        return index
    adapter = make_adapter(model_config)
    for start in range(0, len(missing), batch_size):
        group = missing[start:start+batch_size]
        predictions = adapter.predict([frame.image() for frame, _ in group], batch_size)
        for (frame, rgb_hash), prediction in zip(group, predictions):
            name = "depth/" + spec_hash(frame.id)[:20] + ".npy"
            _save_npy(output_path / name, prediction.values)
            index["frames"][frame.id] = {"path": name, "convention": prediction.convention,
                                          "model": prediction.model, "shape": list(prediction.values.shape),
                                          "rgb_hash": rgb_hash, "depth_hash": file_hash(output_path / name)}
        index["batches"].append({"frame_ids": [f.id for f, _ in group],
                                  "inference_seconds_synchronized": adapter.last_inference_seconds,
                                  "peak_gpu_bytes": adapter.peak_gpu_bytes})
        atomic_json(index_path, index)
    return index


def _windows(frames: list[FrameInput], views: int, stride: int):
    if views < 2 or stride < 1:
        raise ValueError("Invalid window controls")
    scenes = {}
    for frame in frames:
        scenes.setdefault(frame.scene, []).append(frame)
    for scene, records in scenes.items():
        for start in range(0, len(records)-views+1, stride):
            yield scene, start, records[start:start+views]


def _sample_tracks(feature_tracks: list[FeatureTrack], features, frames, depth_maps,
                    prefix: str, pixel_radius: float, relative_width: float, absolute_width: float,
                    max_tracks: int, geometry_only: bool = False):
    if min(pixel_radius, relative_width, absolute_width) < 0 or relative_width + absolute_width <= 0:
        raise ValueError("Invalid uncertainty widths")
    frame_by_id = {f.id: f for f in frames}
    tracks, sampling = [], {}
    for feature_track in sorted(feature_tracks, key=lambda t: (-len(t.nodes), -t.confidence, t.id)):
        observations, samples = [], {}
        tid = prefix + ":" + feature_track.id
        for frame_id, index in feature_track.nodes:
            uv = features[frame_id].xy[index]
            x, y = np.rint(uv).astype(int)
            camera = frame_by_id[frame_id].camera
            if not (0 <= x < camera.width and 0 <= y < camera.height):
                continue
            d = 1.0 if geometry_only else float(depth_maps[frame_id][y, x])
            width = 0.01 if geometry_only else max(absolute_width, relative_width*d)
            if not np.isfinite(d) or d <= width:
                continue
            oid = f"{tid}@{frame_id}"
            radius = tuple(pixel_radius + np.abs(np.array([x, y])-uv))
            observations.append(Observation(oid, frame_id, (float(x), float(y)), radius, d, width,
                                            feature_track.confidence))
            samples[oid] = {"frame_id": frame_id, "x": int(x), "y": int(y), "scene": frame_by_id[frame_id].scene}
        if len(observations) >= 2:
            tracks.append(Track(tid, tuple(observations)))
            sampling.update(samples)
        if len(tracks) >= max_tracks:
            break
    return tracks, sampling


def extract_tracks(manifest: str, cache: str, output: str, config: dict) -> dict:
    dataset, cache_path = load_manifest(manifest), Path(cache)
    index = json.loads((cache_path / "index.json").read_text())
    if index["identity"]["manifest_hash"] != file_hash(manifest):
        raise ValueError("Cache belongs to a different manifest")
    calibration = None
    if config.get("inverse_calibration"):
        record = json.loads(Path(config["inverse_calibration"]).read_text())
        # Frame identifiers should be globally qualified. A shared identifier is
        # conservatively rejected even across differently named manifests.
        if {frame.id for frame in dataset.frames} & set(record["frame_ids"]):
            raise ValueError("Relative-depth calibration and evaluation frames overlap")
        if record["provenance"] != "image_only_triangulation":
            raise ValueError("Only independent image-only geometry calibration is supported")
        calibration = InverseCalibration(record["scale"], record["shift"], tuple(record["track_ids"]))
    box = Box(tuple(config["world_box"]["lower"]), tuple(config["world_box"]["upper"]))
    all_tracks, sampling = [], {}
    for scene, start, frames in _windows(dataset.frames, config.get("views", 3), config.get("window_stride", 3)):
        images = {frame.id: frame.image() for frame in frames}
        cameras = {frame.id: frame.camera for frame in frames}
        depths = {}
        for frame in frames:
            entry = index["frames"][frame.id]
            if file_hash(cache_path / entry["path"]) != entry["depth_hash"] or file_hash(frame.rgb) != entry["rgb_hash"]:
                raise ValueError("Depth cache or RGB content changed")
            depth = np.load(cache_path / entry["path"], allow_pickle=False)
            if depth.shape != (frame.camera.height, frame.camera.width):
                raise ValueError("Cached depth grid mismatch")
            if entry["convention"] == "relative_inverse":
                if calibration is None:
                    raise ValueError("Relative inverse depth requires disjoint calibration")
                depth = calibration.apply(depth)
            elif entry["convention"] != "optical_z":
                raise ValueError("Unsupported cached prediction convention")
            depths[frame.id] = depth
        features, feature_tracks = match_window(images, cameras, config.get("max_features", 1500), config.get("seed", 0))
        tracks, locations = _sample_tracks(feature_tracks, features, frames, depths, f"{scene}:{start}",
                                            config.get("pixel_radius", 1.0), config.get("relative_width", 0.03),
                                            config.get("absolute_width", 0.01), config.get("max_tracks_per_window", 128))
        all_tracks.extend(tracks)
        sampling.update(locations)
    if not all_tracks:
        raise ValueError("No valid multiview tracks found")
    inputs = Inputs({frame.id: frame.camera for frame in dataset.frames}, all_tracks, box)
    output_path = Path(output)
    save_inputs(output_path / "inputs.json", inputs)
    atomic_json(output_path / "sampling.json", {"locations": sampling, "manifest": str(Path(manifest).resolve()),
                                                 "manifest_hash": file_hash(manifest), "cache": str(cache_path.resolve()),
                                                 "cache_signature": index["signature"], "config": config,
                                                 "inputs_hash": file_hash(output_path / "inputs.json"),
                                                 "inputs_signature": spec_hash({"box": inputs.box, "tracks": inputs.tracks,
                                                                                 "cameras": [vars(c) for c in inputs.cameras.values()]}),
                                                 "calibration_hash": file_hash(config["inverse_calibration"]) if calibration else None})
    return {"tracks": len(all_tracks), "observations": len(sampling)}


def calibrate_relative(manifest: str, cache: str, output: str, views: int = 3,
                        max_reprojection: float = 1.0, min_angle_degrees: float = 2.0) -> dict:
    """Use a disjoint manifest; triangulate pixels without reading any reference depth."""
    from .baselines import reprojection_residuals
    dataset = load_manifest(manifest)
    index = json.loads((Path(cache) / "index.json").read_text())
    if index["identity"]["manifest_hash"] != file_hash(manifest):
        raise ValueError("Calibration cache/manifest mismatch")
    inverse_values, geometric_depths, track_ids = [], [], []
    for scene, start, frames in _windows(dataset.frames, views, views):
        cameras = {f.id: f.camera for f in frames}
        features, feature_tracks = match_window({f.id: f.image() for f in frames}, cameras)
        tracks, locations = _sample_tracks(feature_tracks, features, frames, {}, f"cal:{scene}:{start}", 1, .03, .01, 128, True)
        inverse = {}
        for frame in frames:
            entry = index["frames"][frame.id]
            if entry["convention"] != "relative_inverse":
                raise ValueError("Calibration command expects relative inverse predictions")
            if file_hash(Path(cache) / entry["path"]) != entry["depth_hash"]:
                raise ValueError("Calibration cache changed")
            if file_hash(frame.rgb) != entry["rgb_hash"]:
                raise ValueError("Calibration RGB changed")
            inverse[frame.id] = np.load(Path(cache) / entry["path"], allow_pickle=False)
        for track in tracks:
            estimate = linear_triangulation(track, cameras)
            if estimate.point is None or np.max(reprojection_residuals(track, cameras, estimate.point)) > max_reprojection:
                continue
            rays = [estimate.point-cameras[o.camera_id].center for o in track.observations]
            rays = np.array([ray/np.linalg.norm(ray) for ray in rays])
            angles = np.degrees(np.arccos(np.clip(rays @ rays.T, -1, 1)))
            if np.max(angles) < min_angle_degrees:
                continue
            for observation in track.observations:
                sample = locations[observation.id]
                value = float(inverse[observation.camera_id][sample["y"], sample["x"]])
                depth = float(cameras[observation.camera_id].camera_points(estimate.point)[2])
                inverse_values.append(value)
                geometric_depths.append(depth)
                track_ids.append(track.id)
    result = fit_inverse_calibration(inverse_values, geometric_depths, track_ids)
    record = {**asdict(result), "frame_ids": [f.id for f in dataset.frames],
              "manifest_hash": file_hash(manifest), "cache_signature": index["signature"],
              "max_reprojection": max_reprojection, "min_angle_degrees": min_angle_degrees}
    atomic_json(output, record)
    return record


def _check_result_identity(sampling: dict, results_path: str) -> None:
    state = json.loads((Path(results_path).parent / "state.json").read_text())
    if spec_hash(state["identity"]["inputs"]) != sampling["inputs_signature"]:
        raise ValueError("Result input identity differs from sampled tracks")


def evaluate_real(manifest: str, sampling_path: str, results_path: str) -> dict:
    """Reference-depth access is confined to this explicit post-inference function."""
    from .metrics import macro_scene_aggregate
    dataset = load_manifest(manifest)
    sampling = json.loads(Path(sampling_path).read_text())
    if sampling["manifest_hash"] != file_hash(manifest):
        raise ValueError("Evaluation manifest differs from sampling manifest")
    _check_result_identity(sampling, results_path)
    records = [json.loads(line) for line in Path(results_path).read_text().splitlines() if line.strip()]
    locations = sampling["locations"]
    frames = {f.id: f for f in dataset.frames}
    references = {}
    metrics, by_method_scene = [], {}
    unique_samples = {}
    for record in records:
        method = record["method"]
        for oid, before in record["original_depths"].items():
            location = locations[oid]
            fid = location["frame_id"]
            if fid not in dataset.references:
                continue
            if fid not in references:
                if len(references) >= 8:
                    references.pop(next(iter(references)))
                references[fid] = dataset.references[fid].load()
            reference = references[fid][location["y"], location["x"]]
            after = record["depths"].get(oid)
            key = (method, fid, location["y"], location["x"])
            value = unique_samples.setdefault(key, {"before": before, "after": set(), "reference": reference,
                                                      "scene": location["scene"]})
            if value["before"] != before:
                raise ValueError("Repeated pixel has inconsistent original predictions")
            value["after"].add(after)
    for (method, _, _, _), sample in unique_samples.items():
        candidates = sample["after"]
        after = next(iter(candidates)) if len(candidates) == 1 and None not in candidates else sample["before"]
        by_method_scene.setdefault((method, sample["scene"]), []).append((sample["before"], after, sample["reference"]))
    for (method, scene), rows in by_method_scene.items():
        values = np.array(rows)
        before, after, reference = values.T
        result = {"scene": scene, "method": method, **depth_metrics(after, reference),
                  **repair_metrics(before, after, reference)}
        result["before_abs_rel"] = depth_metrics(before, reference)["abs_rel"]
        metrics.append(result)
    methods = sorted({r["method"] for r in metrics})
    return {"schema_version": 1, "scope": "track_sampled_depth_only", "records": metrics,
            "aggregates": {method: macro_scene_aggregate([r for r in metrics if r["method"] == method],
                                                           ["abs_rel", "before_abs_rel", "rmse", "delta1", "damaged_fraction", "corrected_fraction"])
                           for method in methods},
            "note": "Unique sampled pixels; all conflicting repeated-pixel proposals are rejected"}


def materialize_depth(sampling_path: str, results_path: str, method: str, output: str) -> dict:
    from .repair import apply_sparse_edits
    sampling = json.loads(Path(sampling_path).read_text())
    _check_result_identity(sampling, results_path)
    cache = Path(sampling["cache"])
    index = json.loads((cache / "index.json").read_text())
    if index["signature"] != sampling["cache_signature"]:
        raise ValueError("Sampling/cache mismatch")
    records = [json.loads(line) for line in Path(results_path).read_text().splitlines() if line.strip()]
    if not any(record["method"] == method for record in records):
        raise ValueError("Selected method has no result records")
    proposals = {}
    for record in records:
        if record["method"] != method:
            continue
        for oid, value in record["depths"].items():
            location = sampling["locations"][oid]
            proposals.setdefault(location["frame_id"], []).append((location["y"], location["x"], value))
    outputs = {}
    calibration = None
    if sampling["config"].get("inverse_calibration"):
        if file_hash(sampling["config"]["inverse_calibration"]) != sampling["calibration_hash"]:
            raise ValueError("Calibration changed after track extraction")
        calibration_record = json.loads(Path(sampling["config"]["inverse_calibration"]).read_text())
        calibration = InverseCalibration(calibration_record["scale"], calibration_record["shift"],
                                          tuple(calibration_record["track_ids"]))
    for fid, entry in index["frames"].items():
        if file_hash(cache / entry["path"]) != entry["depth_hash"]:
            raise ValueError("Cached map changed")
        original = np.load(cache / entry["path"], allow_pickle=False).astype(np.float64)
        if entry["convention"] == "relative_inverse":
            if calibration is None:
                raise ValueError("Missing metric conversion")
            original = calibration.apply(original)
        authorized = np.zeros(original.shape, dtype=bool)
        for y, x, _ in proposals.get(fid, []):
            authorized[y, x] = True
        repaired, rejected = apply_sparse_edits(original, proposals.get(fid, []), authorized)
        name = spec_hash(fid)[:20] + ".npy"
        _save_npy(Path(output) / name, repaired)
        outputs[fid] = {"path": name, "hash": file_hash(Path(output) / name), "rejected_pixels": rejected,
                         "changed_pixels": int(np.count_nonzero(~np.isclose(original, repaired, rtol=0, atol=0, equal_nan=True)))}
    atomic_json(Path(output) / "index.json", {"method": method, "convention": "optical_z", "frames": outputs,
                                               "sampling_hash": file_hash(sampling_path), "results_hash": file_hash(results_path)})
    return outputs


def evaluate_dense(manifest: str, materialized_index: str, sampling_path: str) -> dict:
    """Explicit full-grid metric evaluation after materializing sparse edits."""
    from .metrics import macro_scene_aggregate
    dataset = load_manifest(manifest)
    sampling = json.loads(Path(sampling_path).read_text())
    if sampling["manifest_hash"] != file_hash(manifest):
        raise ValueError("Dense evaluation manifest mismatch")
    repaired_path = Path(materialized_index)
    repaired = json.loads(repaired_path.read_text())
    if repaired["sampling_hash"] != file_hash(sampling_path):
        raise ValueError("Materialized maps belong to different sampling metadata")
    cache_path = Path(sampling["cache"])
    cache = json.loads((cache_path / "index.json").read_text())
    if cache["signature"] != sampling["cache_signature"]:
        raise ValueError("Dense cache signature changed")
    calibration = None
    if sampling["config"].get("inverse_calibration"):
        cp = sampling["config"]["inverse_calibration"]
        if file_hash(cp) != sampling["calibration_hash"]:
            raise ValueError("Calibration changed")
        cr = json.loads(Path(cp).read_text())
        calibration = InverseCalibration(cr["scale"], cr["shift"], tuple(cr["track_ids"]))
    records = []
    for frame in dataset.frames:
        if frame.id not in dataset.references or frame.id not in repaired["frames"]:
            continue
        entry = cache["frames"][frame.id]
        if file_hash(cache_path / entry["path"]) != entry["depth_hash"]:
            raise ValueError("Cached original changed")
        before = np.load(cache_path / entry["path"], allow_pickle=False)
        if entry["convention"] == "relative_inverse":
            if calibration is None:
                raise ValueError("Missing inverse calibration")
            before = calibration.apply(before)
        after_path = repaired_path.parent / repaired["frames"][frame.id]["path"]
        if file_hash(after_path) != repaired["frames"][frame.id]["hash"]:
            raise ValueError("Materialized depth changed")
        after = np.load(after_path, allow_pickle=False)
        reference = dataset.references[frame.id].load()
        result = {"scene": frame.scene, "frame": frame.id, "method": repaired["method"],
                  **depth_metrics(after, reference), **repair_metrics(before, after, reference)}
        result["before_abs_rel"] = depth_metrics(before, reference)["abs_rel"]
        records.append(result)
    return {"schema_version": 1, "scope": "full_reference_grid_sparse_edits", "records": records,
            "aggregate": macro_scene_aggregate(records, ["abs_rel", "before_abs_rel", "rmse", "delta1", "changed_fraction", "damaged_fraction"])}

