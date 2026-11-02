import json
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from witness3d.datasets import FrameInput, ReferenceDepth
from witness3d.io import atomic_json, file_hash, load_inputs, plain, spec_hash
from witness3d.matching import Features, FeatureTrack
from witness3d.pipeline import _sample_tracks, extract_tracks, materialize_depth


def test_subpixel_sampling_expands_localization_box(cameras):
    frames = [SimpleNamespace(id=i, camera=cameras[i], scene="s") for i in ("0", "1")]
    features = {i: Features(np.array([[320.2, 240.4]]), np.zeros((1, 32), dtype=np.uint8)) for i in ("0", "1")}
    depth = {i: np.full((480, 640), 2.0) for i in ("0", "1")}
    tracks, locations = _sample_tracks([FeatureTrack("t", (("0", 0), ("1", 0)), .8)], features, frames,
                                        depth, "s:0", .5, .03, .01, 1)
    assert len(tracks) == 1
    observation = tracks[0].observations[0]
    assert observation.uv == (320, 240)
    np.testing.assert_allclose(observation.pixel_radius, [.7, .9])


def test_extract_does_not_read_reference_depth(tmp_path, cameras, monkeypatch):
    frames = []
    cache_path, output = tmp_path / "cache", tmp_path / "tracks"
    cache_path.mkdir()
    entries = {}
    for i in ("0", "1"):
        image_path = tmp_path / f"{i}.png"
        Image.fromarray(np.zeros((480, 640, 3), dtype=np.uint8)).save(image_path)
        np.save(cache_path / f"{i}.npy", np.full((480, 640), 2.0))
        pose = np.eye(4)
        pose[:3, 3] = cameras[i].center
        frames.append({"id": i, "scene": "s", "rgb": image_path.name, "K": cameras[i].K.tolist(),
                       "pose": pose.tolist(), "width": 640, "height": 480,
                       "depth": "never_open_reference.png"})
        entries[i] = {"path": f"{i}.npy", "convention": "optical_z", "depth_hash": file_hash(cache_path / f"{i}.npy"),
                      "rgb_hash": file_hash(image_path)}
    manifest = tmp_path / "manifest.json"
    atomic_json(manifest, {"schema_version": 1, "root": str(tmp_path), "undistorted_pinhole": True,
                           "depth_registered_to_rgb": True, "depth_convention": "optical_z", "units_per_meter": 1000,
                           "pose_convention": "camera_to_world", "frames": frames})
    atomic_json(cache_path / "index.json", {"signature": "test", "identity": {"manifest_hash": file_hash(manifest)}, "frames": entries})
    features = {i: Features(np.array([cameras[i].project([0, 0, 2])[0]]), np.zeros((1, 32), dtype=np.uint8)) for i in ("0", "1")}
    monkeypatch.setattr("witness3d.pipeline.match_window", lambda *args, **kwargs: (features, [FeatureTrack("t", (("0", 0), ("1", 0)), 1)]))
    monkeypatch.setattr(ReferenceDepth, "load", lambda self: pytest.fail("GT leaked into extraction"))
    result = extract_tracks(str(manifest), str(cache_path), str(output),
                             {"views": 2, "world_box": {"lower": [-10, -10, .01], "upper": [10, 10, 20]}})
    assert result["tracks"] == 1
    assert len(load_inputs(output / "inputs.json").tracks) == 1


def test_materialization_rejects_nonexistent_method(tmp_path):
    sampling = {"inputs_signature": spec_hash({}), "cache": str(tmp_path / "cache"), "cache_signature": "test"}
    atomic_json(tmp_path / "sampling.json", sampling)
    atomic_json(tmp_path / "state.json", {"identity": {"inputs": {}}})
    atomic_json(tmp_path / "cache/index.json", {"signature": "test", "frames": {}})
    (tmp_path / "records.jsonl").write_text(json.dumps({"method": "none"}) + "\n")
    with pytest.raises(ValueError, match="no result records"):
        materialize_depth(str(tmp_path / "sampling.json"), str(tmp_path / "records.jsonl"), "local", str(tmp_path / "output"))
