import numpy as np

from witness3d.matching import Match, assemble_tracks


def test_conflicting_same_view_merge_rejected():
    matches = [Match("a", 0, "b", 0, .9), Match("b", 0, "c", 0, .8), Match("c", 0, "a", 1, .7)]
    tracks = assemble_tracks(matches)
    assert len(tracks) == 1
    assert tracks[0].nodes == (("a", 0), ("b", 0), ("c", 0))
    assert tracks[0].confidence == .8


def test_empty_features_and_matching():
    import pytest
    pytest.importorskip("cv2")
    from witness3d.matching import detect, descriptor_matches
    features = detect(np.zeros((80, 80, 3), dtype=np.uint8))
    assert features.xy.shape == (0, 2)
    assert descriptor_matches(features, features, "a", "b") == []

