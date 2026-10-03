#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Adjust private box-contact floors to inspected animated idle geometry.

Copies converted inputs to a NEW output directory. Render/culling bounds,
meshes, materials, rigs, clips and source pixels stay unchanged. This is a
coarse body collider, not animated limb collision or a GTA runtime proof.
"""
import argparse
import json
import math
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

# Metres in model space, measured from the existing decoded idle geometry.
# Keep consistent with CreatureSpec.minimum_z; clearances remain in the runtime.
CONTACTS={'c2120':('ergt_malenia',-0.005),'c3181':('ergt_redwolf',-0.075),'c2270':('ergt_crab',-0.355)}


def adjust(root, floor):
    bound=root.find('Bounds')
    if bound is None or bound.get('type')!='Composite':raise ValueError('Expected embedded composite bound')
    children=bound.findall('Children/Item')
    if len(children)!=1 or children[0].get('type')!='Box':raise ValueError('Only the verified single-box collider is supported')
    transform=[float(x) for x in children[0].findtext('CompositeTransform','').split()]
    identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    if len(transform)!=16 or any(abs(a-b)>1e-6 for a,b in zip(transform,identity)):raise ValueError('Unexpected collider transform; preserving it')
    before=[]
    for item in [bound,children[0]]:
        lo=[float(item.find('BoxMin').get(k)) for k in 'xyz'];hi=[float(item.find('BoxMax').get(k)) for k in 'xyz']
        if not math.isfinite(floor) or not lo[2]<=floor<hi[2]:raise ValueError('Floor must raise the existing lower face without inverting it')
        before.append(lo[2]);lo[2]=floor;item.find('BoxMin').set('z',str(floor))
        size=[b-a for a,b in zip(lo,hi)]
        item.find('Volume').set('value',format(math.prod(size),'.9g'))
        for i,axis in enumerate('xyz'):
            moment=sum(size[j]**2 for j in range(3) if j!=i)/12
            item.find('Inertia').set(axis,format(moment,'.9g'))
        # Preserve centre/transform semantics, conservatively enclosing every
        # new corner instead of shrinking broad-phase coverage.
        centre=[float(item.find('SphereCenter').get(k)) for k in 'xyz']
        radius=math.sqrt(sum(max(abs(a-c),abs(b-c))**2 for a,b,c in zip(lo,hi,centre)))
        item.find('SphereRadius').set('value',format(max(float(item.find('SphereRadius').get('value')),radius),'.9g'))
    return before


def prepare(converted,animations,out):
    if out.exists():raise ValueError('Use a new output directory')
    out.mkdir(parents=True);reports=[]
    for character,(name,floor) in CONTACTS.items():
        source=converted/character;dest=out/character;dest.mkdir()
        shutil.copytree(source/name,dest/name)
        drawable=ET.parse(source/(name+'.ydr.xml'))
        old=adjust(drawable.getroot(),floor);ET.indent(drawable)
        drawable.write(dest/(name+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
        # Use the current repaired animation, never regress to the older
        # f-curve conversion that accompanies the material-conversion folder.
        clip=animations/character/(name+'_anims.ycd.xml');shutil.copy2(clip,dest/clip.name)
        receipt=json.loads((source/(name+'.conversion.json')).read_text())
        receipt['render_bounds']=receipt.get('render_bounds',{'min':receipt['collision']['min'][:],'max':receipt['collision']['max'][:]})
        receipt['collision']['min'][2]=floor;receipt['collision']['ground_reference']='inspected animated idle mesh; runtime contact unverified'
        (dest/(name+'.conversion.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        reports.append({'model':name,'prior_floor':old,'new_floor':floor,'render_bounds_preserved':True,'gta_runtime_verified':False})
    (out/'ground-contact-report.json').write_text(json.dumps(reports,indent=2)+'\n');return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['converted','animations','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.converted,a.animations,a.out),indent=2))
