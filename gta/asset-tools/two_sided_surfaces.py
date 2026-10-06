#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Retain explicit source two-sided cloth through GTA's single-sided shader.

The front surface is unchanged. A reverse-facing copy uses the same positions,
UVs and skin weights, with reversed normals/tangent handedness. This adds no
thickness and authors no replacement animation or cloth deformation.
"""
import argparse,json,shutil
from pathlib import Path,PureWindowsPath
from xml.etree import ElementTree as E
import numpy as np
from upgrade_visuals import SIZES


def add_back_surface(geometry):
    vb=geometry.find('VertexBuffer');names=[x.tag for x in vb.find('Layout')];offsets={};offset=0
    for n in names:offsets[n]=offset;offset+=SIZES[n]
    front=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,offset)
    indices=np.fromstring(geometry.findtext('IndexBuffer/Data'),sep=' ',dtype=int).reshape(-1,3)
    if len(front)*2>65535:raise ValueError('Two-sided geometry exceeds native16-bit vertex range')
    if not np.isfinite(front).all() or indices.min()<0 or indices.max()>=len(front):raise ValueError('Invalid geometry')
    back=front.copy();n=offsets['Normal'];back[:,n:n+3]*=-1
    if 'Tangent' in offsets:back[:,offsets['Tangent']+3]*=-1
    rows=np.concatenate([front,back]);new_indices=np.concatenate([indices,indices[:,[0,2,1]]+len(front)])
    vb.find('Data').text='\n'+'\n'.join(' '.join(format(float(v),'.9g') for v in row) for row in rows)+'\n'
    geometry.find('IndexBuffer/Data').text='\n'+'\n'.join(' '.join(map(str,row)) for row in new_indices)+'\n'
    return {'front_vertices':len(front),'front_triangles':len(indices),'added_reverse_triangles':len(indices),'original_front_preserved':True,'skinning_uvs_positions_preserved':True}


def apply(converted,out,roster):
    if out.exists():raise ValueError('Use a new output directory')
    shutil.copytree(converted,out);reports=[]
    for b in roster:
        targets=set(b.get('two_sided_materials',[]))
        if not targets:continue
        c,n=b['character'],b['model'];p=out/c/(n+'.ydr.xml');doc=E.parse(p);receipt_path=out/c/(n+'.conversion.json');receipt=json.loads(receipt_path.read_text())
        if receipt.get('two_sided_surfaces'):raise ValueError('Already adapted; refuse duplicate backfaces')
        paths=receipt['shader_source_paths'];selected={i for i,s in enumerate(paths) if PureWindowsPath(s).stem.lower() in targets}
        found={PureWindowsPath(paths[i]).stem.lower() for i in selected}
        if found!=targets:raise ValueError('Missing source material provenance: '+str(targets-found))
        changes=[]
        for i,g in enumerate(doc.findall('.//Geometries/Item')):
            si=int(g.find('ShaderIndex').get('value'))
            if si in selected:changes.append({'geometry':i,'source_material':paths[si],**add_back_surface(g)})
        if not changes:raise ValueError('No source two-sided geometry selected')
        E.indent(doc);doc.write(p,encoding='utf-8',xml_declaration=True);receipt['two_sided_surfaces']=changes;receipt_path.write_text(json.dumps(receipt,indent=2)+'\n');reports.append({'model':n,'changes':changes})
    (out/'two-sided-report.json').write_text(json.dumps(reports,indent=2)+'\n');return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['converted','out','roster']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(apply(a.converted,a.out,json.loads(a.roster.read_text())['bosses']),indent=2))
