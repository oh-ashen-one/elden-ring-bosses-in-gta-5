#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Sample real source joint transforms without a renderer or game launch.

Outputs are private derived game data, not redistributable fixtures. A motion
landmark is a tuning reference; it is not proof of a visual contact in GTA.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from rebuild_animation import SourceGLB, Y_UP_TO_Z_UP


def audit(path,clip,anchor,fps=30):
    source=SourceGLB(path)
    if clip not in source.animations or anchor not in source.names:raise ValueError('Unknown clip or skeleton joint')
    duration=max(float(source.accessor(s['input'])[-1,0]) for s in source.animations[clip]['samplers'])
    if not 0<duration<=60 or not 1<=fps<=60:raise ValueError('Bounded audit requires 0-60 second clips at 1-60 samples/second')
    times=np.unique(np.r_[np.arange(0,duration,1/fps),duration])
    positions=np.stack([(Y_UP_TO_Z_UP@source.sample(clip,float(t)))[source.names[anchor],:3,3] for t in times])
    speeds=np.linalg.norm(np.diff(positions,axis=0),axis=1)/np.diff(times)
    peak=int(np.argmax(speeds))
    return {'clip':clip,'anchor':anchor,'duration':duration,'coordinate_system':'GTA model space, Z up; apply entity heading/translation to get world space',
            'sample_times_seconds':times.tolist(),'positions':positions.tolist(),
            'fastest_sweep_seconds':float((times[peak]+times[peak+1])/2),'peak_speed_mps':float(speeds[peak]),
            'gta_runtime_verified':False,'note':'Joint motion only. No collider, material, contact timing or visual acceptance claim.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--glb',type=Path,required=True)
    p.add_argument('--clip',required=True);p.add_argument('--anchor',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();result=audit(a.glb,a.clip,a.anchor);a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('clip','anchor','duration','fastest_sweep_seconds','gta_runtime_verified')}))
