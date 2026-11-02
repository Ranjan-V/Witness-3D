"""Manifest-first dataset adapters with explicit camera/depth registration.

RGB inference records and evaluation-only reference records are separate types.
No dataset is downloaded and no uncalibrated RGB/depth alignment is assumed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image

from .geometry import Camera, quaternion_rotation


@dataclass(frozen=True)
class FrameInput:
    id: str
    scene: str
    rgb: Path
    camera: Camera
    timestamp: float | None = None

    def image(self) -> np.ndarray:
        image = np.array(Image.open(self.rgb).convert("RGB"))
        if image.shape[:2] != (self.camera.height, self.camera.width):
            raise ValueError("RGB grid differs from manifest calibration")
        return image


@dataclass(frozen=True)
class ReferenceDepth:
    frame_id: str
    path: Path
    units_per_meter: float
    invalid_values: tuple[float, ...]
    width: int
    height: int

    def load(self) -> np.ndarray:
        if self.path.suffix.lower() == ".npy":
            raw = np.load(self.path, allow_pickle=False)
        else:
            raw = np.array(Image.open(self.path))
        if raw.shape != (self.height, self.width) or self.units_per_meter <= 0:
            raise ValueError("Reference must already be registered to the RGB optical-z grid")
        depth = raw.astype(np.float64) / self.units_per_meter
        invalid = ~np.isfinite(depth) | (depth <= 0)
        for value in self.invalid_values:
            invalid |= raw == value
        depth[invalid] = np.nan
        return depth


@dataclass
class Dataset:
    frames: list[FrameInput]
    references: dict[str, ReferenceDepth]
    metadata: dict[str, Any]


def _array(value, root: Path) -> np.ndarray:
    return np.loadtxt(root / value) if isinstance(value, str) else np.asarray(value, dtype=float)


def load_manifest(path: str | Path, root_override: str | Path | None = None) -> Dataset:
    path = Path(path).resolve(strict=True)
    content = json.loads(path.read_text(encoding="utf-8"))
    if content.get("schema_version") != 1:
        raise ValueError("Unsupported dataset manifest schema")
    root = Path(root_override if root_override is not None else content.get("root", path.parent))
    if not root.is_absolute():
        root = path.parent / root
    root = root.resolve()
    if not content.get("undistorted_pinhole", False):
        raise ValueError("Raw distorted images must be rectified outside this adapter")
    frames, references, ids = [], {}, set()
    for frame in content["frames"]:
        id = str(frame["id"])
        if id in ids:
            raise ValueError("Duplicate frame ID")
        ids.add(id)
        K = _array(frame.get("K", content.get("K")), root)
        width, height = int(frame["width"]), int(frame["height"])
        if frame.get("pose_convention", content.get("pose_convention")) != "camera_to_world":
            raise ValueError("Manifest must explicitly normalize poses to camera_to_world")
        camera = Camera.from_c2w(id, K, _array(frame["pose"], root), width, height)
        frames.append(FrameInput(id, str(frame["scene"]), root / frame["rgb"], camera, frame.get("timestamp")))
        if frame.get("depth") is not None:
            if not frame.get("depth_registered_to_rgb", content.get("depth_registered_to_rgb", False)):
                raise ValueError("Unregistered evaluation depth is unsupported")
            if frame.get("depth_convention", content.get("depth_convention")) != "optical_z":
                raise ValueError("Reference convention must be optical_z")
            units = float(frame.get("units_per_meter", content.get("units_per_meter", 0)))
            if not np.isfinite(units) or units <= 0:
                raise ValueError("Explicit positive depth units required")
            invalid = tuple(frame.get("invalid_values", content.get("invalid_values", [0])))
            references[id] = ReferenceDepth(id, root / frame["depth"], units, invalid, width, height)
    return Dataset(frames, references, {k: v for k, v in content.items() if k != "frames"})


def read_timestamp_file(path: Path) -> list[tuple[float, list[str]]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if fields and not fields[0].startswith("#"):
            records.append((float(fields[0]), fields[1:]))
    return sorted(records)


def associate(first: Sequence[tuple[float, Any]], second: Sequence[tuple[float, Any]],
               max_difference: float = 0.02) -> list[tuple[int, int]]:
    """One-to-one nearest timestamp association with explicit maximum gap."""
    if max_difference < 0:
        raise ValueError("Nonnegative association tolerance required")
    times = np.array([record[0] for record in second])
    candidates = []
    for i, (timestamp, _) in enumerate(first):
        begin = int(np.searchsorted(times, timestamp-max_difference, side="left"))
        end = int(np.searchsorted(times, timestamp+max_difference, side="right"))
        candidates.extend((abs(timestamp-times[j]), i, j) for j in range(begin, end))
    used_a, used_b, output = set(), set(), []
    for _, i, j in sorted(candidates):
        if i not in used_a and j not in used_b:
            used_a.add(i)
            used_b.add(j)
            output.append((i, j))
    return sorted(output)


def _base(options: dict) -> dict:
    if not options.get("undistorted_pinhole") or not options.get("depth_registered_to_rgb"):
        raise ValueError("Explicit vetted rectification and RGB-depth registration are required")
    provenance = options.get("provenance", "")
    if not provenance or provenance.startswith(("REQUIRED", "UNVERIFIED")):
        raise ValueError("Replace template provenance with the actual calibrated-export procedure")
    return {"schema_version": 1, "root": str(Path(options["root"]).resolve()),
            "source": options["dataset"], "undistorted_pinhole": True,
            "depth_registered_to_rgb": True, "depth_convention": "optical_z",
            "pose_convention": "camera_to_world", "provenance": provenance,
            "frames": []}


def tum_manifest(options: dict) -> dict:
    output = _base(options)
    root = Path(output["root"])
    rgb = read_timestamp_file(root / options.get("rgb_list", "rgb.txt"))
    poses = read_timestamp_file(root / options.get("poses", "groundtruth.txt"))
    depth = read_timestamp_file(root / options.get("depth_list", "depth.txt"))
    rgb_depth = dict(associate(rgb, depth, options.get("max_dt", 0.02)))
    rgb_pose = dict(associate(rgb, poses, options.get("max_pose_dt", 0.02)))
    # No interpolated-pose certainty is implied; timing error is a separate premise.
    output.update(K=options["K"], units_per_meter=5000, invalid_values=[0])
    stride = int(options.get("stride", 10))
    if stride < 1:
        raise ValueError("Positive frame stride required")
    for index in sorted(set(rgb_depth) & set(rgb_pose))[::stride]:
        fields = [float(v) for v in poses[rgb_pose[index]][1]]
        if len(fields) != 7:
            raise ValueError("TUM pose requires tx ty tz qx qy qz qw")
        pose = np.eye(4)
        pose[:3, :3] = quaternion_rotation(fields[3:], "xyzw")
        pose[:3, 3] = fields[:3]
        output["frames"].append({"id": str(index), "scene": options["scene"], "rgb": rgb[index][1][0],
                                  "depth": depth[rgb_depth[index]][1][0], "pose": pose.tolist(),
                                  "width": options["width"], "height": options["height"], "timestamp": rgb[index][0]})
    return output


def seven_scenes_manifest(options: dict) -> dict:
    output = _base(options)
    root = Path(output["root"])
    # K must describe the exported RGB grid; official default depth K is insufficient.
    output.update(K=options["K"], units_per_meter=1000, invalid_values=[0, 65535])
    for sequence in options["sequences"]:
        files = sorted((root / sequence).glob("*.color.png"))[::int(options.get("stride", 10))]
        for rgb in files:
            stem = rgb.name.removesuffix(".color.png")
            depth = rgb.with_name(stem + options.get("depth_suffix", ".depth.proj.png"))
            pose = rgb.with_name(stem + ".pose.txt")
            if not depth.is_file() or not pose.is_file():
                raise ValueError("Missing vetted registered depth or camera-to-world pose")
            output["frames"].append({"id": f"{sequence}/{stem}", "scene": options["scene"],
                                      "rgb": rgb.relative_to(root).as_posix(), "depth": depth.relative_to(root).as_posix(),
                                      "pose": pose.relative_to(root).as_posix(), "width": options["width"], "height": options["height"]})
    return output


def scannet_manifest(options: dict) -> dict:
    output = _base(options)
    root = Path(output["root"])
    output.update(K=options["K"], units_per_meter=options["depth_shift"], invalid_values=[0])
    pose_frame = options["pose_frame"]
    if pose_frame not in {"color", "depth"}:
        raise ValueError("ScanNet exported pose frame must be specified")
    transform = np.eye(4) if pose_frame == "color" else _array(options["T_color_depth"], root)
    for index in options["frame_ids"]:
        rgb = options.get("rgb_pattern", "color/{id}.jpg").format(id=index)
        depth = options.get("depth_pattern", "registered_depth/{id}.png").format(id=index)
        pose_path = root / options.get("pose_pattern", "pose/{id}.txt").format(id=index)
        pose = np.loadtxt(pose_path)
        if not np.isfinite(pose).all():
            continue  # Sensor exports may contain invalid tracking poses.
        pose_color = pose @ np.linalg.inv(transform)
        output["frames"].append({"id": str(index), "scene": options["scene"], "rgb": rgb, "depth": depth,
                                  "pose": pose_color.tolist(), "width": options["width"], "height": options["height"]})
    return output


def colmap_text(cameras_path: Path, images_path: Path):
    calibrations, poses = {}, []
    for line in cameras_path.read_text(encoding="utf-8").splitlines():
        values = line.split()
        if not values or values[0].startswith("#"):
            continue
        id, model, width, height = values[:4]
        params = [float(v) for v in values[4:]]
        if model == "PINHOLE" and len(params) == 4:
            fx, fy, cx, cy = params
        elif model == "SIMPLE_PINHOLE" and len(params) == 3:
            fx, cx, cy = params
            fy = fx
        else:
            raise ValueError(f"Undistort COLMAP model {model} before using this adapter")
        calibrations[id] = (np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]), int(width), int(height))
    # COLMAP images.txt alternates image metadata and an optional empty points2D line.
    expect_image = True
    for line in images_path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        if expect_image:
            if not line.strip():
                continue
            values = line.split(maxsplit=9)
            if len(values) != 10:
                raise ValueError("Malformed COLMAP image metadata")
            id, *rest = values
            R = quaternion_rotation([float(v) for v in rest[:4]], "wxyz")
            t = np.array([float(v) for v in rest[4:7]])
            pose = np.eye(4)
            pose[:3, :3], pose[:3, 3] = R.T, -R.T @ t
            poses.append((id, rest[7], rest[8], pose))
            expect_image = False
        else:
            expect_image = True
    return calibrations, poses


def eth3d_manifest(options: dict) -> dict:
    output = _base(options)
    root = Path(output["root"])
    calibration, poses = colmap_text(root / options["cameras"], root / options["images_metadata"])
    # Reference depths must be a documented registered pinhole optical-z export.
    output.update(units_per_meter=1, invalid_values=[0])
    for id, camera_id, name, pose in poses[::int(options.get("stride", 1))]:
        K, width, height = calibration[camera_id]
        depth = options["reference_pattern"].format(name=name, stem=Path(name).stem, id=id)
        output["frames"].append({"id": id, "scene": options["scene"], "rgb": str(Path(options["images_root"]) / name),
                                  "depth": depth, "K": K.tolist(), "pose": pose.tolist(), "width": width, "height": height})
    return output


def prepare_manifest(options: dict) -> dict:
    adapters = {"tum": tum_manifest, "7scenes": seven_scenes_manifest,
                "scannet": scannet_manifest, "eth3d": eth3d_manifest}
    if options["dataset"] not in adapters:
        raise ValueError("Unsupported dataset")
    return adapters[options["dataset"]](options)

