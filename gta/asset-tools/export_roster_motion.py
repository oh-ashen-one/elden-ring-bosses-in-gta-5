# SPDX-License-Identifier: GPL-3.0-or-later
"""Create PRIVATE phase-driven root/weapon tracks and original TAE hit windows.

Uses existing pinned readers. Source data and output ASI must stay private.
"""
import argparse,json,sys
from pathlib import Path,PureWindowsPath
import numpy as np
from soulstruct.containers import Binder
from soulstruct.havok import HKX
from soulstruct.havok.fromsoft.eldenring import AnimationHKX
from havok_compat import install
from export_motion import root_samples
from rebuild_animation import SourceGLB,Y_UP_TO_Z_UP
install()

WEAPONS={'c2120':[['#00#_Sword']], 'c4730':[['#00#'],['#00#']],
         'c4760':[['#00#']], 'c4720':[['#00#Axe','#01#Broken blade']]}

def windows(events,duration):
    intervals=sorted((float(e['start']),float(e['end'])) for e in events if e['type']==1)
    merged=[]
    for start,end in intervals:
        if not 0<=start<end<=duration+.04:raise ValueError('Attack event outside source clip')
        end=min(end,duration)
        if merged and start<=merged[-1][1]+1e-5:merged[-1][1]=max(end,merged[-1][1])
        else:merged.append([start,end])
    if not merged:raise ValueError('Original attack events absent')
    return merged

def build(root,roster,out):
    if out.exists():raise ValueError('Use new output')
    out.mkdir(parents=True);all_tracks=[];reports=[]
    def f(v):
        s=format(float(v),'.9g');return s+('f' if '.' in s or 'e' in s else '.0f')
    for boss in roster:
        c,model=boss['character'],boss['model'];source=SourceGLB(root/'interchange-final'/(c+'.glb'));skin=source.doc['skins'][0]
        inverse=source.accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);weapons=[]
        for weapon_number,names in enumerate(WEAPONS[c]):
            chunks=[]
            for mesh in source.doc['meshes']:
                if mesh['name'] not in names:continue
                for primitive in mesh['primitives']:
                    a=primitive['attributes'];chunks.append((source.accessor(a['POSITION']),source.accessor(a['JOINTS_0']).astype(int),source.accessor(a['WEIGHTS_0'])))
            if not chunks:raise ValueError('Weapon mesh missing: '+str(names))
            p,j,w=(np.concatenate([item[i] for item in chunks]) for i in range(3))
            if c=='c4730':
                bone='R_Sword' if weapon_number==0 else 'L_Sword'
                bone_index=skin['joints'].index(source.names[bone]);keep=np.sum(w*(j==bone_index),axis=1)>.5
                if not np.any(keep):raise ValueError('Hand-bound sword vertices absent')
                p,j,w=p[keep],j[keep],w[keep]
            _,_,axes=np.linalg.svd(p-p.mean(0),full_matrices=False);projection=p@axes[0];ends=[np.argmin(projection),np.argmax(projection)]
            weapons.append((np.column_stack([p[ends],np.ones(2)]),j[ends],w[ends]))
        tracks={};source_events=json.loads((root/(c+'-attack-events.json')).read_text())
        for path in sorted((root/'raw'/c).glob('*.anibnd')):
            binder=Binder.from_path(path);entry=next((e for e in binder.entries if e.name.endswith('.compendium')),None)
            compendium=HKX.from_bytes(entry.get_uncompressed_data()) if entry else None
            for entry in binder.entries:
                name=PureWindowsPath(entry.name).stem
                if name not in boss['clips']:continue
                a=AnimationHKX.from_bytes(entry.get_uncompressed_data(),compendium=compendium).animation_container
                duration=float(a.hkx_animation.duration);count=a.frame_count;motion=root_samples(a,count,True)
                times=source.accessor(source.animations[name]['samplers'][0]['input'])[:,0]
                if len(times)!=count or abs(times[-1]-duration)>1e-4:raise ValueError('Source pose/root timing mismatch')
                samples=[]
                for time,step in zip(times,motion):
                    matrices=source.sample(name,float(time))[skin['joints']]@inverse;ends=[]
                    for p,j,w in weapons:
                        posed=np.sum(np.einsum('nvij,nj->nvi',matrices[j],p)*w[:,:,None],axis=1)
                        ends.extend((Y_UP_TO_Z_UP@posed.T).T[:,:3].reshape(-1))
                    if len(weapons)==1:ends.extend([0]*6)
                    samples.append([*step,*ends])
                hit_windows=windows(source_events['events'],duration) if name==boss['clips'][2] else []
                tracks[name]=(duration,np.asarray(samples),hit_windows)
        if set(tracks)!=set(boss['clips']):raise ValueError('Missing clip')
        lines=['// PRIVATE DERIVED GAME DATA - NEVER PUBLISH','#pragma once','namespace ergt {']
        for name,(duration,samples,contact) in tracks.items():
            symbol=model+'_'+name
            lines.append('inline constexpr MotionSample samples_'+symbol+'[] = {')
            for v in samples:
                lines.append(' {{'+','.join(map(f,v[:3]))+'},'+f(v[3])+','+','.join('{'+','.join(map(f,v[i:i+3]))+'}' for i in (4,7,10,13))+'},')
            lines.append('};')
            if contact:lines.append('inline constexpr ContactWindow contacts_'+symbol+'[] = {'+','.join('{'+f(a/duration)+','+f(b/duration)+'}' for a,b in contact)+'};')
            all_tracks.append('{"'+model+'","'+name+'",'+f(duration)+',samples_'+symbol+','+str(len(samples))+',true,'+('true' if len(weapons)>1 else 'false')+','+('contacts_'+symbol if contact else 'nullptr')+','+str(len(contact))+'}')
            reports.append({'model':model,'clip':name,'frames':len(samples),'duration':duration,'root_end':samples[-1,:4].tolist(),'source_attack_windows_seconds':contact,'weapon_groups':WEAPONS[c]})
        lines.append('}');(out/(model+'.hpp')).write_text('\n'.join(lines)+'\n')
    includes=['#pragma once']+['#include "'+b['model']+'.hpp"' for b in roster]
    includes+=['namespace ergt {','inline constexpr std::array<MotionTrack,'+str(len(all_tracks))+'> owned_motion_tracks{{',',\n'.join(all_tracks),'}};','}']
    (out/'bosses.hpp').write_text('\n'.join(includes)+'\n');(out/'motion-report.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','roster','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.root,json.loads(a.roster.read_text())['bosses'],a.out)
