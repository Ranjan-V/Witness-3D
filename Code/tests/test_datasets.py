import json

import numpy as np
import pytest
from PIL import Image

from witness3d.datasets import ReferenceDepth, associate, colmap_text, load_manifest, prepare_manifest, read_timestamp_file


def test_timestamp_association_is_one_to_one_and_bounded():
    a = [(0., "a"), (.01, "b"), (2., "c")]
    b = [(.005, "x"), (3., "y")]
    result = associate(a, b, .02)
    assert len(result) == 1
    assert len({j for _, j in result}) == len(result)


def test_tum_timestamp_and_quaternion_parser(tmp_path):
    (tmp_path / "rgb.txt").write_text("# list\n1.0 rgb.png\n")
    (tmp_path / "depth.txt").write_text("1.0 depth.png\n")
    (tmp_path / "groundtruth.txt").write_text("1.0 1 2 3 0 0 0 1\n")
    config = {"dataset": "tum", "root": str(tmp_path), "scene": "s", "K": np.eye(3).tolist(),
              "width": 2, "height": 2, "undistorted_pinhole": True, "depth_registered_to_rgb": True,
              "provenance": "test calibrated export", "stride": 1}
    manifest = prepare_manifest(config)
    assert manifest["units_per_meter"] == 5000
    np.testing.assert_allclose(np.array(manifest["frames"][0]["pose"])[:3, 3], [1, 2, 3])


def test_reference_depth_units_and_sentinel(tmp_path):
    path = tmp_path / "depth.png"
    Image.fromarray(np.array([[5000, 0], [10000, 65535]], dtype=np.uint16)).save(path)
    depth = ReferenceDepth("f", path, 5000, (0, 65535), 2, 2).load()
    assert depth[0, 0] == 1 and depth[1, 0] == 2
    assert np.isnan(depth[0, 1]) and np.isnan(depth[1, 1])


def test_manifest_refuses_uncalibrated_or_unregistered(tmp_path):
    content = {"schema_version": 1, "undistorted_pinhole": False, "frames": []}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        load_manifest(path)
    with pytest.raises(ValueError):
        prepare_manifest({"dataset": "7scenes", "root": str(tmp_path)})


def test_colmap_wxyz_world_to_camera_and_empty_point_line(tmp_path):
    cameras = tmp_path / "cameras.txt"
    images = tmp_path / "images.txt"
    cameras.write_text("# cameras\n1 PINHOLE 640 480 100 100 320 240\n")
    images.write_text("# images\n1 1 0 0 0 -1 0 0 1 a.jpg\n\n2 1 0 0 0 -2 0 0 1 b.jpg\n\n")
    calibration, poses = colmap_text(cameras, images)
    assert len(poses) == 2
    np.testing.assert_allclose(poses[0][3][:3, 3], [1, 0, 0])
    assert calibration["1"][1:] == (640, 480)


def test_colmap_distortion_refused(tmp_path):
    cameras, images = tmp_path / "cameras.txt", tmp_path / "images.txt"
    cameras.write_text("1 RADIAL 640 480 100 320 240 .1 .01\n")
    images.write_text("")
    with pytest.raises(ValueError):
        colmap_text(cameras, images)


def test_seven_scenes_registration_suffix_and_units(tmp_path):
    sequence = tmp_path / "seq-01"
    sequence.mkdir()
    (sequence / "frame-000001.color.png").write_bytes(b"not read during manifest preparation")
    (sequence / "frame-000001.depth.proj.png").write_bytes(b"not read")
    np.savetxt(sequence / "frame-000001.pose.txt", np.eye(4))
    config = {"dataset": "7scenes", "root": str(tmp_path), "scene": "chess", "K": np.eye(3).tolist(),
              "width": 640, "height": 480, "undistorted_pinhole": True, "depth_registered_to_rgb": True,
              "provenance": "test calibrated export", "sequences": ["seq-01"], "stride": 1}
    result = prepare_manifest(config)
    assert result["units_per_meter"] == 1000
    assert 65535 in result["invalid_values"]
    assert result["frames"][0]["depth"].endswith(".depth.proj.png")


def test_scannet_depth_to_color_pose_conversion(tmp_path):
    (tmp_path / "pose").mkdir()
    np.savetxt(tmp_path / "pose/0.txt", np.eye(4))
    T = np.eye(4)
    T[0, 3] = .1
    config = {"dataset": "scannet", "root": str(tmp_path), "scene": "s", "K": np.eye(3).tolist(),
              "width": 640, "height": 480, "undistorted_pinhole": True, "depth_registered_to_rgb": True,
              "provenance": "test calibrated export", "pose_frame": "depth", "T_color_depth": T.tolist(),
              "depth_shift": 1000, "frame_ids": [0]}
    result = prepare_manifest(config)
    assert np.array(result["frames"][0]["pose"])[0, 3] == pytest.approx(-.1)

