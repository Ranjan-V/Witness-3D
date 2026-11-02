from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, is_dataclass
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .exact import Box
from .geometry import Camera
from .observations import Observation, Track
from .synthetic import Inputs


def plain(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def atomic_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(plain(value), indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def spec_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(plain(value), sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_config(path: str | Path) -> dict:
    def expand(value):
        if isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        if isinstance(value, list):
            return [expand(v) for v in value]
        if isinstance(value, str):
            def substitute(match):
                key = match.group(1)
                if key not in os.environ:
                    raise ValueError(f"Required environment variable {key} is unset")
                return os.environ[key]
            return re.sub(r"\$\{([A-Za-z_][A-Za-z_0-9]*)\}", substitute, value)
        return value
    result = expand(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    if not isinstance(result, dict):
        raise ValueError("Configuration root must be a mapping")
    return result


def save_inputs(path: str | Path, inputs: Inputs) -> None:
    atomic_json(path, {"schema_version": 1, "box": inputs.box,
                       "cameras": [vars(c) for c in inputs.cameras.values()], "tracks": inputs.tracks})


def load_inputs(path: str | Path) -> Inputs:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported input schema")
    if any(key in data for key in ("truth", "reference_depth", "ground_truth")):
        raise ValueError("Inference inputs cannot include evaluation truth")
    cameras = {c["id"]: Camera(**c) for c in data["cameras"]}
    tracks = [Track(t["id"], tuple(Observation(**o) for o in t["observations"])) for t in data["tracks"]]
    return Inputs(cameras, tracks, Box(**data["box"]))

