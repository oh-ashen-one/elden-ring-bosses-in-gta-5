#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned HKX root motion + skinned sword endpoints -> PRIVATE C++ build input.

No proprietary samples ship with the source. Do not publish the generated
header or a plugin compiled with it. The track is separate from pose channels:
applying it to both the skeleton and entity would double the displacement.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path, PureWindowsPath
import numpy as np
from soulstruct.containers import Binder
from soulstruct.havok.core import HKX
from soulstruct.havok.fromsoft.eldenring import AnimationHKX
from rebuild_animation import SourceGLB, Y_UP_TO_Z_UP


def root_samples(container, count):
    motion=container.hkx_animation.extractedMotion
    if motion is None:return np.zeros((count,4))
    if not np.allclose(list(motion.up),[0,1,0,0]) or not np.allclose(list(motion.forward),[0,0,1,0]):
        raise ValueError('Unexpected reference frame axes')
    values=np.asarray(container.get_reference_frame_samples(),dtype=float)
    if values.ndim!=2 or values.shape[1]!=4 or not np.isfinite(values).all():raise ValueError('Invalid root samples')
    if abs(float(motion.duration)-float(container.hkx_animation.duration))>1e-4:raise ValueError('Root/pose duration mismatch')
    # Source -> reflected glTF -> Z-up GTA: (x,y,z) -> (x,z,y).
    # Reflection changes the sign of axial yaw. These selected clips have no
    # turning root; reject turning/jumping moves until their runtime is added.
    result=values[:,[0,2,1,3]].copy();result[:,3]*=-1
    result-=result[0]
    if np.max(np.abs(result[:,2:]))>0.01:raise ValueError('Turning/jumping root motion is not supported by this grounded encounter')
    return np.column_stack([np.interp(np.linspace(0,1,count),np.linspace(0,1,len(result)),c) for c in result.T])


def export(raw,glb,model,clips,out,weapon_mesh):
    if not re.fullmatch(r'[a-z0-9_]+',model) or any(not re.fullmatch(r'a\d+_\d+',c) for c in clips):raise ValueError('Invalid identifier')
    source=SourceGLB(glb);skin=source.doc['skins'][0]
    inverse=source.accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    matches=[m for m in source.doc['meshes'] if m['name']==weapon_mesh]
    if len(matches)!=1 or len(matches[0]['primitives'])!=1:raise ValueError('Ambiguous weapon mesh')
    a=matches[0]['primitives'][0]['attributes'];pos=source.accessor(a['POSITION'])
    joints=source.accessor(a['JOINTS_0']).astype(int);weights=source.accessor(a['WEIGHTS_0'])
    # Keep actual skinned extreme vertices along the blade's principal axis.
    # It is a conservative straight blade approximation, not ER hitbox data.
    _,_,axes=np.linalg.svd(pos-pos.mean(0),full_matrices=False);along=pos@axes[0]
    endpoints=[int(np.argmin(along)),int(np.argmax(along))]
    p=np.column_stack([pos[endpoints],np.ones(2)]);j=joints[endpoints];w=weights[endpoints]
    tracks={};receipts=[]
    for path in sorted(raw.glob('*.anibnd')):
        binder=Binder.from_path(path);entry=next((e for e in binder.entries if e.name.endswith('.compendium')),None)
        compendium=HKX.from_bytes(entry.get_uncompressed_data()) if entry else None
        for e in binder.entries:
            name=PureWindowsPath(e.name).stem
            if name not in clips:continue
            if name in tracks:raise ValueError('Duplicate animation source')
            container=AnimationHKX.from_bytes(e.get_uncompressed_data(),compendium=compendium).animation_container
            duration=float(container.hkx_animation.duration);count=container.frame_count
            animation=source.animations[name]
            if not 2<=count<=2048 or not 0<duration<=60:raise ValueError('Unbounded animation')
            times=source.accessor(animation['samplers'][0]['input'])[:,0]
            if len(times)!=count or abs(times[-1]-duration)>1e-4:raise ValueError('Full-rate matching glTF required')
            root=root_samples(container,count);samples=[]
            for time,r in zip(times,root):
                matrices=source.sample(name,float(time))[skin['joints']]@inverse
                posed=np.sum(np.einsum('nvij,nj->nvi',matrices[j],p)*w[:,:,None],axis=1)
                blade=(Y_UP_TO_Z_UP@posed.T).T[:,:3]
                samples.append([*r,*blade.reshape(-1)])
            values=np.asarray(samples)
            if not np.isfinite(values).all():raise ValueError('Invalid skinned samples')
            tracks[name]=(duration,values)
            receipts.append({'clip':name,'frames':count,'duration':duration,'root_end':root[-1].tolist(),
                             'source_hkx_sha256':hashlib.sha256(e.get_uncompressed_data()).hexdigest()})
    if set(tracks)!=set(clips):raise ValueError('Missing source clips')
    def f(v):
        value=format(float(v),'.9g');return value+('f' if '.' in value or 'e' in value else '.0f')
    lines=['// PRIVATE DERIVED GAME DATA. Do not publish.','#pragma once','namespace ergt {']
    for name,(_,values) in tracks.items():
        lines.append('inline constexpr MotionSample motion_'+name+'[] = {')
        for v in values:lines.append('    {{'+','.join(map(f,v[:3]))+'},'+f(v[3])+',{'+','.join(map(f,v[4:7]))+'},{'+','.join(map(f,v[7:10]))+'}},')
        lines.append('};')
    lines.append('inline constexpr std::array<MotionTrack,'+str(len(tracks))+'> owned_motion_tracks{{')
    for name,(duration,values) in tracks.items():
        lines.append('    {"'+model+'","'+name+'",'+f(duration)+',motion_'+name+','+str(len(values))+',true},')
    lines+=['}};','}']
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as handle:handle.write('\n'.join(lines)+'\n')
    report={'model':model,'glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'clips':receipts,
            'weapon_mesh':weapon_mesh,'gta_runtime_verified':False,'header_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    with out.with_suffix('.json').open('x') as handle:json.dump(report,handle,indent=2);handle.write('\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('raw','glb','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--model',required=True);p.add_argument('--clips',nargs='+',required=True);p.add_argument('--weapon-mesh',required=True)
    a=p.parse_args();print(json.dumps(export(a.raw,a.glb,a.model,a.clips,a.out,a.weapon_mesh),indent=2))
