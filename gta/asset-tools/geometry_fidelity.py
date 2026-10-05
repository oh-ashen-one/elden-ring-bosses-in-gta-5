#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Audit triangle orientation and repair the known legacy double-flip export.

No geometry decimation, texture edits, animation changes or game launch.
"""
import argparse,json,shutil
from pathlib import Path
from xml.etree import ElementTree as E
import numpy as np
from upgrade_visuals import SIZES
from compact_skin_palette import identity

def orientation(geometry):
    vb=geometry.find('VertexBuffer');names=[x.tag for x in vb.find('Layout')]
    data=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,sum(SIZES[n] for n in names))
    pi=sum(SIZES[n] for n in names[:names.index('Position')]);ni=sum(SIZES[n] for n in names[:names.index('Normal')])
    p,n=data[:,pi:pi+3],data[:,ni:ni+3];ix=np.fromstring(geometry.findtext('IndexBuffer/Data'),sep=' ',dtype=int).reshape(-1,3)
    dots=np.sum(np.cross(p[ix[:,1]]-p[ix[:,0]],p[ix[:,2]]-p[ix[:,0]])*n[ix].mean(1),axis=1)
    return {'triangles':len(ix),'outward':int((dots>1e-8).sum()),'inward':int((dots< -1e-8).sum())}

def audit(drawable):
    stats=[orientation(g) for g in drawable.findall('.//Geometries/Item')]
    return {k:sum(s[k] for s in stats) for k in ('triangles','outward','inward')}

def reject_inward(drawable):
    stats=audit(drawable)
    if stats['inward']>max(1,stats['outward'])*10:raise ValueError('Predominantly inward faces: likely coordinate/winding double flip')
    return stats

def repair(converted,out,roster):
    if out.exists():raise ValueError('Use a new output directory')
    out.mkdir(parents=True);reports=[]
    for boss in roster:
        c,name=boss['character'],boss['model'];dst=out/c;shutil.copytree(converted/c,dst)
        path=dst/(name+'.ydr.xml');doc=E.parse(path);before=audit(doc)
        if before['inward']<=max(1,before['outward'])*10:raise ValueError('Not the known legacy inward-face failure: '+name)
        for g in doc.findall('.//Geometries/Item'):
            ib=g.find('IndexBuffer/Data');ix=np.fromstring(ib.text,sep=' ',dtype=int).reshape(-1,3)[:,[0,2,1]]
            ib.text='\n'+'\n'.join(' '.join(map(str,row)) for row in ix)+'\n'
        after=reject_inward(doc);count=len(doc.findall('Skeleton/Bones/Item'))
        palette=identity(doc) if count<=256 else {'large_rig_palette_runtime_verification_pending':True}
        E.indent(doc);doc.write(path,encoding='utf-8',xml_declaration=True)
        report={'model':name,'before':before,'after':after,'skin_palette':palette,'runtime_verified':False}
        receipt=dst/(name+'.conversion.json');data=json.loads(receipt.read_text());data['geometry_fidelity']=report;receipt.write_text(json.dumps(data,indent=2)+'\n')
        reports.append(report);print(name,before,'->',after,flush=True)
    (out/'geometry-fidelity-report.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('converted','out','roster'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();repair(a.converted,a.out,json.loads(a.roster.read_text())['bosses'])
