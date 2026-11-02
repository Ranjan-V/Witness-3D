import numpy as np
import pytest

from witness3d.geometry import Camera, convert_depth, quaternion_rotation


def test_projection_backprojection(cameras):
    points = np.array([[0.1, .2, 2], [-.3, .1, 4]])
    for camera in cameras.values():
        uv, z, valid = camera.project(points)
        assert valid.all()
        np.testing.assert_allclose(camera.backproject(uv, z), points, atol=1e-12)


def test_camera_to_world_inverse(cameras):
    camera = cameras["1"]
    pose = np.eye(4)
    pose[:3, :3] = camera.R.T
    pose[:3, 3] = camera.center
    recovered = Camera.from_c2w("x", camera.K, pose, 640, 480)
    np.testing.assert_allclose(recovered.t, camera.t)


def test_resizing_uses_half_pixel(cameras):
    camera = cameras["0"]
    point = [0.2, 0.3, 2]
    uv, _, _ = camera.project(point)
    resized, _, _ = camera.resized(320, 240).project(point)
    np.testing.assert_allclose(resized, .5*(uv+.5)-.5)


def test_normalization_and_range(cameras):
    xy = cameras["0"].normalized([420, 240])
    np.testing.assert_allclose(xy, [1, 0])
    assert convert_depth(2*np.sqrt(2), xy, "range") == pytest.approx(2)
    assert convert_depth(.5, xy, "inverse_z") == pytest.approx(2)


def test_quaternion_order():
    np.testing.assert_allclose(quaternion_rotation([1, 0, 0, 0], "wxyz"), np.eye(3))
    with pytest.raises(ValueError):
        quaternion_rotation([0, 0, 0, 0])


def test_invalid_inputs(cameras):
    camera = cameras["0"]
    assert not camera.project([0, 0, -1])[2]
    assert not camera.project([0, 0, 0])[2]
    with pytest.raises(ValueError):
        camera.backproject([0, 0], -1)
    K = camera.K.copy()
    K[0, 1] = .1
    with pytest.raises(ValueError):
        Camera("skew", K, camera.R, camera.t, 640, 480)

