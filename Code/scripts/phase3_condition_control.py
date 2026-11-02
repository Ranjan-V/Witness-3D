"""Conventional parallax/domain rejection, evaluated separately post-hoc."""
from itertools import combinations
import json
from pathlib import Path
import numpy as np
from witness3d.io import load_inputs,atomic_json


def usable(track,cameras,point,box,angle_degrees):
    if point is None:return False
    point=np.array(point)
    if not np.isfinite(point).all() or np.any(point<np.array(box.lower,float)) or np.any(point>np.array(box.upper,float)):return False
    rays=[]
    for o in track.observations:
        cam=cameras[o.camera_id];ray=cam.R.T@np.r_[cam.normalized(o.uv),1.]
        rays.append(ray/np.linalg.norm(ray))
    angle=max(np.degrees(np.arccos(np.clip(a@b,-1,1))) for a,b in combinations(rays,2))
    return angle>=angle_degrees


if __name__=='__main__':
    rows=[]
    for case in Path('docs/phase3/stress').glob('*/seed_*'):
        inputs=load_inputs(case/'inputs.json');tracks={t.id:t for t in inputs.tracks}
        records=[json.loads(line) for line in (case/'run/records.jsonl').read_text().splitlines()]
        # Select/reject before opening evaluation truth.
        estimates=[]
        for theta in [.1,.5,1.,2.]:
            for method in ['triangulation','ransac']:
                group=[];rejected=0
                for r in records:
                    if r['method']!=method:continue
                    accepted=usable(tracks[r['track']],inputs.cameras,r.get('point'),inputs.box,theta)
                    rejected+=not accepted
                    group.append(r['depths'] if accepted else r['original_depths'])
                estimates.append((theta,method,group,rejected))
        truth=json.loads((case/'evaluation_truth.json').read_text())['depths']
        for theta,method,group,rejected in estimates:
            rows.append({'scenario':case.parent.name,'seed':int(case.name.split('_')[1]),'angle_degrees':theta,'method':method,
                         'rejected_tracks':int(rejected),'abs_rel':float(np.mean([abs(v-truth[k])/truth[k] for depths in group for k,v in depths.items()]))})
    atomic_json('docs/phase3/condition_control_results.json',rows)
