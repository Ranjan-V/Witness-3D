"""OpenCV ORB/descriptor matching and conflict-aware track assembly."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping, Sequence

import numpy as np

from .geometry import Camera


@dataclass
class Features:
    xy: np.ndarray
    descriptors: np.ndarray


@dataclass(frozen=True)
class Match:
    frame_a: str
    index_a: int
    frame_b: str
    index_b: int
    confidence: float


@dataclass
class FeatureTrack:
    id: str
    nodes: tuple[tuple[str, int], ...]
    confidence: float


def detect(image: np.ndarray, max_features: int = 1500) -> Features:
    import cv2
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3 or max_features < 1:
        raise ValueError("Expected uint8 RGB image and positive feature cap")
    keypoints, descriptors = cv2.ORB_create(nfeatures=max_features).detectAndCompute(
        cv2.cvtColor(image, cv2.COLOR_RGB2GRAY), None)
    if descriptors is None:
        return Features(np.empty((0, 2)), np.empty((0, 32), dtype=np.uint8))
    return Features(np.array([k.pt for k in keypoints]), descriptors)


def descriptor_matches(a: Features, b: Features, frame_a: str, frame_b: str,
                        ratio: float = 0.75) -> list[Match]:
    import cv2
    if not 0 < ratio < 1:
        raise ValueError("Ratio test must lie in (0,1)")
    if len(a.descriptors) < 2 or len(b.descriptors) < 2:
        return []
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    forward = matcher.knnMatch(a.descriptors, b.descriptors, k=2)
    reverse = matcher.match(b.descriptors, a.descriptors)
    reverse_best = {m.queryIdx: m.trainIdx for m in reverse}
    accepted = []
    for pair in forward:
        if len(pair) != 2:
            continue
        best, second = pair
        if best.distance < ratio * second.distance and reverse_best.get(best.trainIdx) == best.queryIdx:
            confidence = max(0.0, 1 - best.distance / max(second.distance, 1e-12))
            accepted.append(Match(frame_a, best.queryIdx, frame_b, best.trainIdx, confidence))
    return accepted


def geometric_filter(matches: Sequence[Match], features: Mapping[str, Features],
                      cameras: Mapping[str, Camera], threshold: float = 2.0,
                      ransac: bool = True, seed: int = 0) -> list[Match]:
    import cv2
    if not matches:
        return []
    a_id, b_id = matches[0].frame_a, matches[0].frame_b
    if any((m.frame_a, m.frame_b) != (a_id, b_id) for m in matches):
        raise ValueError("Geometric filtering accepts one image pair at a time")
    a, b = cameras[a_id], cameras[b_id]
    R = b.R @ a.R.T
    t = b.t - R @ a.t
    skew = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
    F = np.linalg.inv(b.K).T @ skew @ R @ np.linalg.inv(a.K)
    x = np.array([features[a_id].xy[m.index_a] for m in matches])
    y = np.array([features[b_id].xy[m.index_b] for m in matches])
    if np.linalg.norm(F) < 1e-12:
        # Pure rotation does not define a useful epipolar distance. Retain and let
        # the geometry verifier abstain; never divide by a zero fundamental matrix.
        return list(matches)
    xh, yh = np.c_[x, np.ones(len(x))], np.c_[y, np.ones(len(y))]
    fx, fty = xh @ F.T, yh @ F
    denominator = np.sum(fx[:, :2]**2 + fty[:, :2]**2, axis=1)
    sampson = np.sum(yh * fx, axis=1)**2 / np.maximum(denominator, 1e-30)
    keep = sampson <= threshold**2
    if ransac and len(matches) >= 8:
        cv2.setRNGSeed(seed)
        _, mask = cv2.findFundamentalMat(x, y, cv2.FM_RANSAC, threshold, 0.999)
        if mask is not None and mask.size == len(matches):
            keep &= mask.ravel().astype(bool)
        else:
            keep[:] = False
    return [m for m, selected in zip(matches, keep) if selected]


def assemble_tracks(matches: Sequence[Match], min_views: int = 2) -> list[FeatureTrack]:
    parent, members, scores = {}, {}, {}

    def find(node):
        if node not in parent:
            parent[node], members[node], scores[node] = node, {node}, []
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for match in sorted(matches, key=lambda m: (-m.confidence, m.frame_a, m.index_a, m.frame_b, m.index_b)):
        a, b = (match.frame_a, match.index_a), (match.frame_b, match.index_b)
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if {n[0] for n in members[ra]} & {n[0] for n in members[rb]}:
            continue  # Reject a merge that would assign two features in one frame.
        parent[rb] = ra
        members[ra] |= members.pop(rb)
        scores[ra] += scores.pop(rb) + [match.confidence]
    components = sorted((sorted(nodes), root) for root, nodes in members.items() if len(nodes) >= min_views)
    return [FeatureTrack(str(i), tuple(nodes), float(min(scores[root])) if scores[root] else 0.0)
            for i, (nodes, root) in enumerate(components)]


def match_window(images: Mapping[str, np.ndarray], cameras: Mapping[str, Camera],
                  max_features: int = 1500, seed: int = 0):
    features = {id: detect(image, max_features) for id, image in images.items()}
    matches = []
    for a, b in combinations(sorted(images), 2):
        pair = descriptor_matches(features[a], features[b], a, b)
        matches.extend(geometric_filter(pair, features, cameras, seed=seed))
    return features, assemble_tracks(matches)

