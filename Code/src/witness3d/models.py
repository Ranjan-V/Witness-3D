"""Local-only frozen-model adapters. Import torch only when constructing one.

API assumptions and upstream source URLs are recorded in docs/models.md.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Protocol, Sequence

import numpy as np


@dataclass
class Prediction:
    values: np.ndarray
    convention: str
    model: str


class DepthAdapter(Protocol):
    last_inference_seconds: float
    peak_gpu_bytes: int | None
    def predict(self, images: Sequence[np.ndarray], batch_size: int = 1) -> list[Prediction]: ...


def _source_root(path: str, package: str) -> Path:
    root = Path(path).resolve(strict=True)
    if not (root / package).is_dir():
        raise ValueError(f"Expected local upstream package {package} under {root}")
    if package in sys.modules:
        existing = Path(sys.modules[package].__file__).resolve()
        if root not in existing.parents:
            raise RuntimeError("A conflicting upstream package is already imported; use a fresh process")
    sys.path.insert(0, str(root))
    return root


class _Batched:
    def predict(self, images: Sequence[np.ndarray], batch_size: int = 1) -> list[Prediction]:
        import torch
        import torch.nn.functional as F
        if batch_size < 1:
            raise ValueError("Positive microbatch size required")
        groups = defaultdict(list)
        shapes = []
        for index, image in enumerate(images):
            if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
                raise ValueError("Adapters expect uint8 RGB HxWx3 images")
            tensor = self.preprocess(image)
            if tensor.ndim != 3:
                raise ValueError("Preprocessing must return CHW")
            groups[tuple(tensor.shape)].append((index, tensor))
            shapes.append(image.shape[:2])
        outputs: list[Prediction | None] = [None] * len(images)
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
            torch.cuda.reset_peak_memory_stats(self.device)
        started = perf_counter()
        with torch.inference_mode():
            for group in groups.values():
                for start in range(0, len(group), batch_size):
                    part = group[start:start+batch_size]
                    batch = torch.stack([tensor for _, tensor in part]).to(self.device)
                    result = self.model(batch)
                    if result.ndim == 4 and result.shape[1] == 1:
                        result = result[:, 0]
                    if result.ndim != 3 or result.shape[0] != len(part):
                        raise RuntimeError("Unsupported upstream model output; verify installed source version")
                    for local, (index, _) in enumerate(part):
                        resized = F.interpolate(result[local:local+1, None], size=shapes[index],
                                                mode=self.interpolation, align_corners=self.align_corners)
                        values = resized[0, 0].float().cpu().numpy()
                        outputs[index] = Prediction(values, self.convention, self.name)
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
            self.peak_gpu_bytes = int(torch.cuda.max_memory_allocated(self.device))
        else:
            self.peak_gpu_bytes = None
        self.last_inference_seconds = perf_counter() - started
        if any(output is None for output in outputs):
            raise RuntimeError("Missing batched output")
        return list(outputs)


class DepthAnythingV2Small(_Batched):
    def __init__(self, repository: str, checkpoint: str, device: str = "cpu",
                 input_size: int = 518, max_depth: float = 20.0):
        import torch
        import cv2
        _source_root(repository, "depth_anything_v2")
        # repository must be the *metric_depth* directory, not relative-depth root.
        module = importlib.import_module("depth_anything_v2.dpt")
        transform = importlib.import_module("depth_anything_v2.util.transform")
        checkpoint_path = Path(checkpoint).resolve(strict=True)
        if input_size < 28 or max_depth <= 0:
            raise ValueError("Invalid metric model configuration")
        self.device = torch.device(device)
        self.model = module.DepthAnythingV2(encoder="vits", features=64,
                                            out_channels=[48, 96, 192, 384], max_depth=max_depth)
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        self.model.load_state_dict(state, strict=True)
        self.model.to(self.device).eval().requires_grad_(False)
        self.resize = transform.Resize(input_size, input_size, resize_target=False, keep_aspect_ratio=True,
                                       ensure_multiple_of=14, resize_method="lower_bound",
                                       image_interpolation_method=cv2.INTER_CUBIC)
        self.convention, self.name = "optical_z", "depth_anything_v2_metric_small"
        self.interpolation, self.align_corners = "bilinear", True

    def preprocess(self, image):
        import torch
        sample = self.resize({"image": image.astype(np.float32) / 255})["image"]
        normalized = (sample - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
        return torch.from_numpy(np.ascontiguousarray(normalized.transpose(2, 0, 1), dtype=np.float32))


class MidasSmall(_Batched):
    def __init__(self, repository: str, checkpoint: str, backbone_repository: str, device: str = "cpu"):
        import torch
        _source_root(repository, "midas")
        checkpoint_path = Path(checkpoint).resolve(strict=True)
        backbone_path = Path(backbone_repository).resolve(strict=True)
        if not (backbone_path / "hubconf.py").is_file():
            raise ValueError("Local gen-efficientnet-pytorch source with hubconf.py required")
        blocks = importlib.import_module("midas.blocks")
        # Upstream otherwise asks torch.hub for a remote backbone even when the
        # MiDaS weights are local. Replace this one construction factory locally.
        previous = blocks._make_pretrained_efficientnet_lite3

        def local_backbone(use_pretrained, exportable=False):
            backbone = torch.hub.load(str(backbone_path), "tf_efficientnet_lite3", source="local",
                                       pretrained=False, exportable=exportable)
            return blocks._make_efficientnet_backbone(backbone)

        blocks._make_pretrained_efficientnet_lite3 = local_backbone
        try:
            network = importlib.import_module("midas.midas_net_custom")
            # Nonempty path disables the upstream pretrained backbone request.
            self.model = network.MidasNet_small(path=str(checkpoint_path), features=64,
                                                backbone="efficientnet_lite3", exportable=True,
                                                non_negative=True, blocks={"expand": True})
        finally:
            blocks._make_pretrained_efficientnet_lite3 = previous
        hub = importlib.util.spec_from_file_location("witness3d_local_midas_hub", Path(repository) / "hubconf.py")
        if hub is None or hub.loader is None:
            raise ImportError("Cannot load local MiDaS transforms")
        local = importlib.util.module_from_spec(hub)
        hub.loader.exec_module(local)
        self.transform = local.transforms().small_transform
        self.device = torch.device(device)
        self.model.to(self.device).eval().requires_grad_(False)
        self.convention, self.name = "relative_inverse", "midas_v21_small"
        self.interpolation, self.align_corners = "bicubic", False

    def preprocess(self, image):
        return self.transform(image)[0]


def make_adapter(config: dict) -> DepthAdapter:
    parameters = dict(config)
    name = parameters.pop("name")
    if name == "da_v2_metric_small":
        return DepthAnythingV2Small(**parameters)
    if name == "midas_small":
        return MidasSmall(**parameters)
    raise ValueError(f"Unsupported adapter {name}")

