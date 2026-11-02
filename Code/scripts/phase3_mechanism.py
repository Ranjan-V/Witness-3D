"""Minimal image-patch/counterfactual-association falsification experiment.

Tiny generated patches, not real images. Same candidates/patches/cameras for all
methods. Truth is returned separately and used only after selection.
"""
from itertools import product
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
from scipy.optimize import linprog
from witness3d.synthetic import generate,SyntheticConfig
from witness3d.observations import Track
from witness3d.constraints import track_polytope
from witness3d.solver import solve,Status
from witness3d.baselines import linear_triangulation
from witness3d.io import atomic_json


def generate_candidates(seed,mode):
    inputs,truth=generate(SyntheticConfig(seed=seed,tracks=1,views=4,baseline=.25))
    rng=np.random.default_rng(seed+2200);track=inputs.tracks[0]
    true=truth.points['0']; center=inputs.cameras['0'].center
    decoy=center+1.7*(true-center)  # same target ray, distinct physical depth
    prototype=rng.uniform(0,1,(8,8)); target_patch=prototype+rng.normal(0,.02,(8,8))
    candidates=[]
    for j,o in enumerate(track.observations[1:]):
        uv=inputs.cameras[o.camera_id].project(true)[0]
        wrong_uv=inputs.cameras[o.camera_id].project(decoy)[0]
        if mode=='generic_distractors': wrong_uv=wrong_uv+np.array([0.,20.+j])
        correct_patch=prototype+rng.normal(0,.04,(8,8))
        false_patch=(prototype if mode=='repeated_texture' else rng.uniform(0,1,(8,8)))+rng.normal(0,.04,(8,8))
        if mode=='occluded' and j==0:
            uv=wrong_uv; correct_patch=false_patch.copy()  # true candidate absent
        pair=[(replace(o,uv=tuple(uv)),correct_patch),(replace(o,uv=tuple(wrong_uv)),false_patch)]
        rng.shuffle(pair);candidates.append(pair)
    return inputs,track.observations[0],target_patch,candidates,float(truth.depths['0:0'])


def choose(inputs,target,patch,candidates):
    hypotheses=[]
    for choice in product([0,1],repeat=len(candidates)):
        obs=[target]+[candidates[j][k][0] for j,k in enumerate(choice)]
        cost=sum(float(np.mean((patch-candidates[j][k][1])**2)) for j,k in enumerate(choice))
        track=Track('candidate',tuple(obs));poly=track_polytope(track,inputs.cameras,inputs.box,include_depth=False)
        A,b=poly.float_arrays()
        classic=linprog([0.,0.,0.],A_ub=A,b_ub=b,bounds=[(float(l),float(h)) for l,h in zip(inputs.box.lower,inputs.box.upper)],method='highs')
        decision=solve(poly)
        hypotheses.append((cost,choice,track,classic.success,decision.status!=Status.CONTRADICTION))
    results={}
    for method,eligible in [('photometric',lambda r:True),('joint_photo_geometry',lambda r:r[3]),('certificate_conflict_filter',lambda r:r[4])]:
        pool=[r for r in hypotheses if eligible(r)]
        if not pool: results[method]={'state':'ABSTAIN','choice':None,'depth':None};continue
        winner=min(pool,key=lambda r:(r[0],r[1]));point=linear_triangulation(winner[2],inputs.cameras).point
        results[method]={'state':'ESTIMATE' if point is not None else 'ABSTAIN','choice':winner[1],
                         'depth':float(inputs.cameras[target.camera_id].camera_points(point)[2]) if point is not None else None}
    return results,len(hypotheses)


if __name__=='__main__':
    rows=[]
    for mode in ['generic_distractors','coherent_decoy','repeated_texture','occluded']:
        for seed in range(40):
            inputs,target,patch,candidates,truth=generate_candidates(seed,mode)
            result,count=choose(inputs,target,patch,candidates)
            rows.append({'mode':mode,'seed':seed,'truth':truth,'hypotheses':count,'results':result})
    atomic_json('docs/phase3/mechanism_results.json',rows)
    print('cases',len(rows),'mismatched classical/certificate decisions',sum(r['results']['joint_photo_geometry']['choice']!=r['results']['certificate_conflict_filter']['choice'] for r in rows))
