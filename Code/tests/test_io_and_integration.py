import json

import pytest

from witness3d.experiments import expand_ablation, run_inputs
from witness3d.io import atomic_json, load_config, load_inputs, save_inputs
from witness3d.synthetic import SyntheticConfig, generate
from witness3d.verify import check_artifact


def test_input_roundtrip_and_gt_rejection(tmp_path):
    inputs, _ = generate(SyntheticConfig(tracks=2))
    path = tmp_path / "inputs.json"
    save_inputs(path, inputs)
    recovered = load_inputs(path)
    assert recovered.tracks == inputs.tracks
    content = json.loads(path.read_text())
    content["ground_truth"] = {}
    atomic_json(path, content)
    with pytest.raises(ValueError):
        load_inputs(path)


def test_config_missing_environment_is_error(tmp_path, monkeypatch):
    monkeypatch.delenv("W3D_TEST_MISSING", raising=False)
    path = tmp_path / "config.yaml"
    path.write_text("path: ${W3D_TEST_MISSING}\n")
    with pytest.raises(ValueError):
        load_config(path)


def test_pipeline_resume_and_changed_spec_refusal(tmp_path):
    inputs, _ = generate(SyntheticConfig(tracks=2, views=3, depth_bias=1.5))
    config = {"methods": ["none", "witness_only", "local"], "repair": {"extraction": "dual"}}
    first = run_inputs(inputs, config, str(tmp_path))
    second = run_inputs(inputs, config, str(tmp_path))
    assert first == second
    assert len(first) == 6
    for record in first:
        for artifact in record["artifacts"]:
            assert check_artifact(artifact).accepted
    with pytest.raises(ValueError):
        run_inputs(inputs, {**config, "seed": 99}, str(tmp_path))


def test_ablation_coverage_warnings_and_distinct_specs():
    runs = expand_ablation({"base": {"synthetic": {}}, "axes": {"synthetic.pixel_radius": [.5, 1.0], "synthetic.views": [2, 3]}})
    assert len(runs) == 4
    assert len({run["id"] for run in runs}) == 4
    assert all(run["comparability_warning"] for run in runs)

