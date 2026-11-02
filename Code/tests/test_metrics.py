import numpy as np
import pytest

from witness3d.metrics import binary_metrics, depth_metrics, macro_scene_aggregate, point_metrics, repair_metrics, witness_metrics, paired_scene_difference


def test_depth_analytic_values():
    result = depth_metrics([1, 4], [1, 2])
    assert result["abs_rel"] == .5
    assert result["rmse"] == pytest.approx(np.sqrt(2))
    assert result["delta1"] == .5


def test_empty_and_invalid_accounting():
    result = depth_metrics([np.nan, 0], [1, 2])
    assert result["count"] == 0 and result["abs_rel"] is None
    assert result["invalid_prediction_fraction"] == 1
    assert binary_metrics([], [])["precision"] is None


def test_detection_and_localization():
    result = binary_metrics([True, True, False], [True, False, True])
    assert result["precision"] == .5 and result["recall"] == .5
    assert result["jaccard"] == pytest.approx(1/3)


def test_repair_damage_and_correction():
    result = repair_metrics([2, 1, 1], [1, 2, 1], [1, 1, 1], [True, True, False])
    assert result["corrected_fraction"] == 1
    assert result["damaged_fraction"] == .5
    assert result["outside_mask_change_fraction"] == 0


def test_witness_metrics_have_real_denominators():
    result = witness_metrics(["UNKNOWN", "VERIFIED_CONTRADICTION"], [True, False], [2, 4], [False, True])
    assert result["unknown_fraction"] == .5
    assert result["certificate_validity_rate"] == .5
    assert result["incorrect_contradiction_rate"] == 1


def test_macro_scene_average_not_pixel_weighting():
    records = [{"scene": "a", "error": 0}, {"scene": "a", "error": 2}, {"scene": "b", "error": 10}]
    result = macro_scene_aggregate(records, ["error"], seed=1, bootstrap=20)
    assert result["metrics"]["error"]["mean"] == 5.5
    assert result == macro_scene_aggregate(records, ["error"], seed=1, bootstrap=20)


def test_point_shape_and_known_distance():
    assert point_metrics([[0, 0, 0]], [[0, 3, 4]])["mean_point_error"] == 5
    with pytest.raises(ValueError):
        point_metrics([1, 2, 3], [1, 2, 3])


def test_paired_scene_difference_keeps_pairing():
    records = [{"scene": scene, "method": method, "error": error}
               for scene, method, error in [("a", "first", 1), ("a", "second", 2),
                                             ("b", "first", 10), ("b", "second", 13),
                                             ("unpaired", "first", 100)]]
    result = paired_scene_difference(records, "first", "second", "error", bootstrap=20)
    assert result["difference"] == -2
    assert result["paired_scenes"] == 2

