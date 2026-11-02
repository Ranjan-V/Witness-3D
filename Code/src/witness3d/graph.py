from __future__ import annotations

from itertools import combinations

import numpy as np


def image_neighbor_edges(tracks, radius_pixels: float = 25.0):
    """Reference graph from image coordinates only; no reference depth access."""
    if radius_pixels <= 0:
        raise ValueError("Positive graph radius required")
    by_track = [{o.camera_id: o for o in t.observations} for t in tracks]
    edges = []
    for k, l in combinations(range(len(tracks)), 2):
        for camera in sorted(set(by_track[k]) & set(by_track[l])):
            a, b = by_track[k][camera], by_track[l][camera]
            distance = np.linalg.norm(np.asarray(a.uv)-b.uv)
            if distance <= radius_pixels:
                weight = min(a.confidence, b.confidence) * np.exp(-distance**2/(2*radius_pixels**2))
                edges.append((k, l, camera, float(weight)))
    return edges

