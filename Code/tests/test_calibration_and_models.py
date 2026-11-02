import numpy as np
import pytest

from witness3d.calibration import fit_inverse_calibration
from witness3d.models import _source_root, make_adapter


def test_inverse_depth_calibration_disjoint_ids():
    inverse = np.linspace(.1, 1, 20)
    geometric = 1 / (2*inverse+.1)
    result = fit_inverse_calibration(inverse, geometric, [f"cal_{i}" for i in range(20)])
    np.testing.assert_allclose(result.apply(inverse, ["held_out"]), geometric, rtol=1e-5)
    with pytest.raises(ValueError):
        result.apply(inverse, ["cal_0"])


def test_degenerate_inverse_calibration_rejected():
    with pytest.raises(ValueError):
        fit_inverse_calibration(np.ones(10), np.ones(10), [str(i) for i in range(10)])


def test_missing_local_source_refused(tmp_path):
    with pytest.raises(ValueError):
        _source_root(str(tmp_path), "nonexistent_model_package")
    with pytest.raises(ValueError):
        make_adapter({"name": "unknown"})

