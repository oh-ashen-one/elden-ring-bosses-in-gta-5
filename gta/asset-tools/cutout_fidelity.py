#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Preserve authored alpha-test coverage in a standard GTA cutout material.

New private outputs only. Does not change geometry, RGB, rigs or animation.
The primary source g_AlphaRef is mapped to GTA's half-alpha cutout. Mip alpha
coverage is retained as closely as quantized mip texels allow.
"""
import argparse,copy,json,shutil
from pathlib import Path,PureWindowsPath
from xml.etree import ElementTree as E
import numpy as np
from upgrade_visuals import read_image,write_dds


def remap_alpha(pixels,threshold):
    if not 0<threshold<255:raise ValueError('Alpha threshold must lie inside byte range')
    out=pixels.copy();a=pixels[:,:,3].astype(float)
    # Map the first accepted source byte exactly to128; preserve both endpoints.
    mapped=np.where(a<threshold,a*127/max(threshold-1,1),128+(a-threshold)*127/(255-threshold))
    out[:,:,3]=np.rint(mapped).clip(0,255).astype(np.uint8)
    return out


def apply(converted,source_root,out,roster):
    if out.exists():raise ValueError('Use new output')
    shutil.copytree(converted,out)
    materials={PureWindowsPath(k).stem.lower():v for k,v in json.loads((source_root/'materials-with-params.json').read_text()).items()}
    reports=[]
    for boss in roster:
        c,n=boss['character'],boss['model'];folder=out/c
        tree=E.parse(folder/(n+'.ydr.xml'));receipt=json.loads((folder/(n+'.conversion.json')).read_text())
        dictionary=tree.find('ShaderGroup/TextureDictionary');entries={x.findtext('Name'):x for x in dictionary}
        for i,(shader,path) in enumerate(zip(tree.findall('ShaderGroup/Shaders/Item'),receipt['shader_source_paths'])):
            if 'cutout' not in shader.findtext('FileName',''):continue
            params={p['name']:p['value'] for p in materials[PureWindowsPath(path).stem.lower()]['params']}
            threshold=round(params.get('g_AlphaRef',[128])[0])
            if not 0<threshold<255:continue
            sampler=shader.find("Parameters/Item[@name='DiffuseSampler']/Name");old=entries[sampler.text]
            data=read_image(folder/n/old.findtext('FileName'));adapted=remap_alpha(data,threshold)
            label=boss.get('visual_child_of',n)+'_cutout_'+str(i);filename=label+'.dds';output=folder/n/filename
            _,_,mips=write_dds(output,adapted,alpha_coverage=128)
            if not np.array_equal(read_image(output),adapted):raise ValueError('Base pixels changed in storage')
            entry=copy.deepcopy(old);entry.find('Name').text=label;entry.find('FileName').text=filename;entry.find('MipLevels').set('value',str(mips));entry.find('Format').text='D3DFMT_A8R8G8B8';dictionary.append(entry);sampler.text=label
            reports.append({'model':n,'material':path,'source_cutoff':threshold,'source_coverage':float((data[:,:,3]>=threshold).mean()),'target_coverage':float((adapted[:,:,3]>=128).mean()),'rgb_unchanged':bool(np.array_equal(data[:,:,:3],adapted[:,:,:3]))})
        # Keep only used textures so the adaptation cannot inflate streaming.
        used={p.text for p in tree.findall("ShaderGroup/Shaders/Item/Parameters/Item[@type='Texture']/Name")}
        for entry in list(dictionary):
            if entry.findtext('Name') not in used:dictionary.remove(entry)
        E.indent(tree);tree.write(folder/(n+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
    (out/'cutout-fidelity-report.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['converted','source-root','out','roster']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(apply(a.converted,a.source_root,a.out,json.loads(a.roster.read_text())['bosses']),indent=2))
