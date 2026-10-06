#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Adapt an authored alternate-UV hair shadow atlas into GTA's colour atlas.

Explicit approximation: reused UV0 islands average their authored UV1 shadow.
Original geometry, source tint, normal detail, cutout alpha and resolution stay.
"""
import argparse,copy,json,shutil
from pathlib import Path,PureWindowsPath
from xml.etree import ElementTree as E
import numpy as np
from material_fidelity import fields,sample
from upgrade_visuals import read_image,write_dds


def bake_shadow(geometries,pixels,shadow):
    h,w=pixels.shape[:2];total=np.zeros((h,w),np.float64);count=np.zeros((h,w),np.uint32);source=shadow.astype(float)
    for g in geometries:
        f=fields(g)
        if 'TexCoord1' not in f:raise ValueError('Authored hair shadow requires UV1')
        triangles=np.fromstring(g.findtext('IndexBuffer/Data'),sep=' ',dtype=int).reshape(-1,3)
        for ids in triangles:
            uv=f['TexCoord0'][ids];p=(uv-np.floor(uv.mean(0)))*[w-1,h-1]
            lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),[w-1,h-1])
            if (lo>hi).any():continue
            a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
            a0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            a1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;a2=1-a0-a1
            inside=(a0>=-.001)&(a1>=-.001)&(a2>=-.001)
            if not inside.any():continue
            uv1=np.stack([a0,a1,a2],axis=-1)@f['TexCoord1'][ids]
            mask=sample(source,uv1)[:,:,0]/255;region=(slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1))
            total[region][inside]+=mask[inside];count[region][inside]+=1
    covered=count>0
    if not covered.any():raise ValueError('No authored shadow UV coverage')
    mask=np.ones((h,w));mask[covered]=total[covered]/count[covered]
    rgb=pixels[:,:,:3].astype(float)/255
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)*mask[:,:,None]
    rgb=np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
    out=pixels.copy();out[:,:,:3]=np.rint(rgb*255).clip(0,255).astype(np.uint8)
    return out,{'shadow_mean':float(mask[covered].mean()),'shadow_range':[float(mask[covered].min()),float(mask[covered].max())],'overlap_rule':'average authored UV1 samples','alpha_unchanged':bool(np.array_equal(out[:,:,3],pixels[:,:,3]))}


def apply(converted,geometry,source_root,out,roster):
    if out.exists():raise ValueError('Use new output')
    shutil.copytree(converted,out);materials={PureWindowsPath(k).stem.lower():v for k,v in json.loads((source_root/'materials-with-params.json').read_text()).items()};reports=[]
    for boss in roster:
        if boss.get('visual_child_of'):continue
        c,n=boss['character'],boss['model'];folder=out/c
        receipt=json.loads((folder/(n+'.conversion.json')).read_text());targets=[]
        for i,path in enumerate(receipt['shader_source_paths']):
            m=materials[PureWindowsPath(path).stem.lower()]
            if 'chrcustomize' not in m['shader'].lower() or 'hair' not in m['shader'].lower():continue
            shadow=next((s['path'] for s in m['samplers'] if '_3_Mask1Map_1' in s['type'] and s['path']),None)
            if shadow:targets.append((i,shadow))
        if not targets:continue
        raw=E.parse(geometry/c/(n+'.ydr.xml'));doc=E.parse(folder/(n+'.ydr.xml'));dictionary=doc.find('ShaderGroup/TextureDictionary');entries={x.findtext('Name'):x for x in dictionary}
        for index,shadow in targets:
            shader=doc.findall('ShaderGroup/Shaders/Item')[index];sampler=shader.find("Parameters/Item[@name='DiffuseSampler']/Name");entry=entries[sampler.text]
            path=source_root/'textures'/c/(PureWindowsPath(shadow).stem.lower()+'.dds')
            if not path.exists():raise ValueError('Source shadow atlas missing')
            pixels=read_image(folder/n/entry.findtext('FileName'))
            gs=[g for g in raw.findall('.//Geometries/Item') if int(g.find('ShaderIndex').get('value'))==index]
            result,report=bake_shadow(gs,pixels,read_image(path));label=n+'_authored_shadow_'+str(index);filename=label+'.dds';_,_,mips=write_dds(folder/n/filename,result,alpha_coverage=128)
            fresh=copy.deepcopy(entry);fresh.find('Name').text=label;fresh.find('FileName').text=filename;fresh.find('MipLevels').set('value',str(mips));fresh.find('Format').text='D3DFMT_A8R8G8B8';dictionary.append(fresh);sampler.text=label
            reports.append({'model':n,'material':receipt['shader_source_paths'][index],'source':str(path),**report})
        used={p.text for p in doc.findall("ShaderGroup/Shaders/Item/Parameters/Item[@type='Texture']/Name")}
        for item in list(dictionary):
            if item.findtext('Name') not in used:dictionary.remove(item)
        E.indent(doc);doc.write(folder/(n+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
    (out/'hair-shadow-report.json').write_text(json.dumps(reports,indent=2)+'\n');return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['converted','geometry','source-root','out','roster']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(apply(a.converted,a.geometry,a.source_root,a.out,json.loads(a.roster.read_text())['bosses']),indent=2))
