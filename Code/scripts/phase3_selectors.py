"""Phase 3 diagnostic selectors. No truth argument or reference-file access."""
from itertools import combinations
import numpy as np
from witness3d import baselines as b


def scores(inputs, seed):
    values = {k: [] for k in ['reprojection', 'depth_disagreement', 'robust_depth_disagreement',
              'robust_reprojection', 'ransac_outlier', 'ransac_depth_disagreement',
              'uncertainty', 'low_confidence', 'random']}
    for track in inputs.tracks:
        tri = b.linear_triangulation(track, inputs.cameras)
        robust = b.robust_refine(track, inputs.cameras)
        ran = b.ransac_triangulation(track, inputs.cameras, seed, threshold=2.)
        fusion = b.average_fusion(track, inputs.cameras)
        for i, o in enumerate(track.observations):
            for name, estimate in [('depth_disagreement', tri), ('robust_depth_disagreement', robust), ('ransac_depth_disagreement', ran)]:
                values[name].append(abs(float(inputs.cameras[o.camera_id].camera_points(estimate.point)[2])-o.depth)/o.half_width if estimate.point is not None else 0.)
            values['reprojection'].append(b.reprojection_residuals(track, inputs.cameras, fusion.point)[i] if fusion.point is not None else 0.)
            values['robust_reprojection'].append(b.reprojection_residuals(track, inputs.cameras, robust.point)[i] if robust.point is not None else 0.)
            values['ransac_outlier'].append(float(not ran.inliers[i]) if ran.inliers is not None else 0.)
            values['uncertainty'].append(o.half_width)
            values['low_confidence'].append(1-o.confidence)
            values['random'].append(0.)
    return {k: np.nan_to_num(v, nan=0., posinf=1e30, neginf=-1e30) for k, v in values.items()}


def select(score, eligible, groups, witness_mask, seed, per_track=False):
    """Equal ACTION counts, including zero-budget cases; ties randomized without GT."""
    rng = np.random.default_rng(seed)
    mask = np.zeros(len(score), bool)
    partitions = sorted(set(groups)) if per_track else [None]
    for group in partitions:
        pool = np.flatnonzero(eligible & (groups == group if group is not None else np.ones(len(score), bool)))
        count = int(np.sum(witness_mask[pool]))
        shuffled = rng.permutation(pool)
        chosen = shuffled[np.argsort(-score[shuffled], kind='stable')[:count]]
        mask[chosen] = True
    assert mask.sum() == (witness_mask & eligible).sum()
    return mask
