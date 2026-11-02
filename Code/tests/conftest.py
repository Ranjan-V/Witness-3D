import numpy as np
import pytest

from witness3d.exact import Box
from witness3d.geometry import Camera
from witness3d.observations import Observation, Track


@pytest.fixture
def cameras():
    K = np.array([[100., 0, 320.], [0, 100., 240.], [0, 0, 1.]])
    return {str(i): Camera(str(i), K, np.eye(3), np.array([-i * .2, 0., 0.]), 640, 480) for i in range(3)}


@pytest.fixture
def box():
    return Box((-10, -10, .01), (10, 10, 20))


@pytest.fixture
def track(cameras):
    observations = []
    for id, camera in cameras.items():
        uv, z, _ = camera.project([0, 0, 2])
        observations.append(Observation(id, id, tuple(uv), (.02, .02), float(z), .02))
    return Track("analytic", tuple(observations))

