"""Continuous-error stress controls; truth used only in generation/evaluation."""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
from phase3_mask_audit import evaluate
from witness3d.synthetic import generate, SyntheticConfig, Inputs
from witness3d.observations import Track
from witness3d.io import atomic_json, save_inputs
from witness3d.experiments import run_inputs
from witness3d.profiling import Profile

SCENARIOS = {'continuous': {}, 'near_zero': {'baseline': .001},
             'contamination': {'outlier_rate': .2}, 'pose_uncertainty': {'pose_translation_sigma': .01},
             'partial_occlusion': {}, 'heterogeneous_quality': {}, 'misleading_confidence': {}}


def make(name, controls, seed):
    inputs, truth = generate(SyntheticConfig(seed=seed, tracks=12, views=5, baseline=.2,
                                             pixel_radius=.5, bounded_noise=.2, **controls)) if 'baseline' not in controls else generate(SyntheticConfig(seed=seed, tracks=12, views=5, pixel_radius=.5, bounded_noise=.2, **controls))
    rng=np.random.default_rng(seed+91000)
    tracks=[]
    for track in inputs.tracks:
        obs=[]
        for j,o in enumerate(track.observations):
            error=rng.normal(0,.08)+(rng.choice([-1,1])*.35 if rng.random()<.25 else 0.)
            d=o.depth*np.exp(error)
            uv=np.array(o.uv); radius=.5; confidence=1.
            if name=='heterogeneous_quality':
                sigma=[.1,.2,.5,1.,2.][j]
                uv+=rng.normal(0,sigma,2); radius=3*sigma
                confidence=1/(1+sigma)
            if name=='misleading_confidence':
                confidence=.99 if abs(error)>.1 else .1
            if name=='partial_occlusion' and j not in [0,4] and rng.random()<.7:
                continue  # missing observations; no claim of rendered occlusion boundaries
            new=replace(o, depth=float(d), half_width=float(.03*d), uv=tuple(uv),
                        pixel_radius=(radius,radius),confidence=confidence)
            obs.append(new)
            truth.wrong_claims[o.id]=abs(d-truth.depths[o.id])>new.half_width
        tracks.append(Track(track.id,tuple(obs)))
    return Inputs(inputs.cameras,tracks,inputs.box),truth


if __name__=='__main__':
    out=Path('docs/phase3/stress');rows=[]
    atomic_json(out/'protocol.json',{'seeds':[11,23,37,53,71],'tracks':12,'views':5,'scenarios':SCENARIOS,
             'error':'log depth N(0,.08^2) plus signed .35 with probability .25',
             'width':'3 percent of prediction','q':1,'occlusion':'missing views only'})
    with Profile() as p:
        for name,controls in SCENARIOS.items():
            for seed in [11,23,37,53,71]:
                inputs,truth=make(name,controls,seed);path=out/name/f'seed_{seed}'
                save_inputs(path/'inputs.json',inputs)
                cfg={'methods':['none','triangulation','ransac','local_all'],'seed':seed,
                     'repair':{'q':1,'localize':False,'save_evidence':True},'ransac_threshold':2.}
                records=run_inputs(inputs,cfg,str(path/'run'))
                atomic_json(path/'evaluation_truth.json',truth)
                # Data serialization only; no reference supplied to run_inputs.
                t=json.loads((path/'evaluation_truth.json').read_text())
                rows.extend(evaluate(inputs,records,t,name,seed))
                atomic_json(out/'mask_results.json',rows)
                print(name,seed,flush=True)
    atomic_json(out/'efficiency.json',p.as_dict())
