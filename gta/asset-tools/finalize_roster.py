#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Finalize private full-rate boss rigs, animations and body contact bounds."""
import argparse,json,shutil
from pathlib import Path
from xml.etree import ElementTree as E
from rebuild_animation import SourceGLB,TargetRig,rebuild
from correct_bind_heads import correct,source_axes
from source_animation_template import create
from align_ground_contact import CONTACTS,BODY_RADII,adjust,body_box

def finalize(materials,interchange,roster,out):
    if out.exists():raise ValueError('Use a new output directory')
    out.mkdir(parents=True);reports=[]
    for b in roster:
        char,name=b['character'],b['model'];src=materials/char;dst=out/char;dst.mkdir()
        shutil.copytree(src/name,dst/name)
        glb=interchange/(char+'.glb');source=SourceGLB(glb)
        doc=E.parse(src/(name+'.ydr.xml'));corrections=correct(doc,source)
        if char in ('c4760','c4720'):corrections.append(source_axes(doc,source))
        TargetRig(doc,source) # Keep the strict 2mm source/target joint guard.
        floor=CONTACTS[char][1];adjust(doc.getroot(),floor,allow_lower=True);body_box(doc.getroot(),BODY_RADII[char])
        drawable=dst/(name+'.ydr.xml');E.indent(doc);doc.write(drawable,encoding='utf-8',xml_declaration=True)
        template=dst/'template.xml';create(name,b['clips'][0],template)
        animation=rebuild(glb,drawable,template,dst/(name+'_anims.ycd.xml'),b['clips']);template.unlink()
        receipt=json.loads((src/(name+'.conversion.json')).read_text())
        receipt['render_bounds']=receipt.get('render_bounds',{'min':receipt['collision']['min'][:],'max':receipt['collision']['max'][:]})
        receipt['collision']['min'][2]=floor
        receipt['collision']['min'][:2]=[-BODY_RADII[char]]*2;receipt['collision']['max'][:2]=[BODY_RADII[char]]*2
        receipt['collision']['note']='Coarse body collider; source-animation weapon sweeps handled in runtime'
        receipt['clips']=b['clips'];receipt['bind_head_corrections']=corrections
        (dst/(name+'.conversion.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        reports.append({'model':name,'bind_head_corrections':corrections,'animation':animation,'runtime_verified':False})
        print('Finalized',name,flush=True)
    (out/'finalization-report.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('materials','interchange','roster','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();finalize(a.materials,a.interchange,json.loads(a.roster.read_text())['bosses'],a.out)
