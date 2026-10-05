# SPDX-License-Identifier: Apache-2.0
"""Partition whole drawable geometries into <=255-bone synchronized parts.

Preserves every face, weighted bone, source tag and ancestor/rest transform.
No decimation, skeleton simplification or invented animation is performed.
"""
import argparse,copy,json,shutil
from pathlib import Path
from xml.etree import ElementTree as E
import numpy as np
from upgrade_visuals import SIZES
from geometry_fidelity import reject_inward

def rows(g):
    vb=g.find('VertexBuffer');names=[n.tag for n in vb.find('Layout')];widths=[SIZES[n] for n in names]
    data=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,sum(widths))
    return data,sum(widths[:names.index('BlendWeights')]),sum(widths[:names.index('BlendIndices')])

def partition(root,limit=255):
    bones=root.findall('Skeleton/Bones/Item');parents=[int(b.find('ParentIndex').get('value')) for b in bones]
    geometries=root.findall('.//Geometries/Item');requirements=[]
    for g in geometries:
        data,wi,ii=rows(g);palette=np.array([int(v) for v in g.findtext('BoneIDs').split(',')])
        used=set(map(int,palette[data[:,ii:ii+4].astype(int)[data[:,wi:wi+4]>0]]))
        for i in list(used):
            seen=set()
            while i>=0:
                if i in seen:raise ValueError('Bone parent cycle')
                seen.add(i);used.add(i);i=parents[i]
        if len(used)>limit:raise ValueError('A geometry needs bone-aware triangle partitioning')
        requirements.append(used)
    groups=[]
    for n,needed in sorted(enumerate(requirements),key=lambda x:len(x[1]),reverse=True):
        for group in groups:
            if len(group['bones']|needed)<=limit:group['bones']|=needed;group['geometries'].add(n);break
        else:groups.append({'bones':set(needed),'geometries':{n}})
    result=[]
    for group in groups:
        doc=copy.deepcopy(root);selected=sorted(group['bones']);remap={old:new for new,old in enumerate(selected)}
        target_bones=doc.find('Skeleton/Bones')
        for b in list(target_bones):target_bones.remove(b)
        for old in selected:
            b=copy.deepcopy(bones[old]);new=remap[old];parent=remap.get(parents[old],-1)
            b.find('Index').set('value',str(new));b.find('ParentIndex').set('value',str(parent))
            siblings=[x for x in selected if parents[x]==parents[old] and x>old]
            b.find('SiblingIndex').set('value',str(remap[siblings[0]] if siblings else -1));target_bones.append(b)
        index=0;triangles=0
        for lod in list(doc):
            if not lod.tag.startswith('DrawableModels'):continue
            for model in list(lod):
                gs=model.find('Geometries')
                if gs is None:continue
                for g in list(gs):
                    chosen=index in group['geometries'];index+=1
                    if not chosen:gs.remove(g);continue
                    data,wi,ii=rows(g);palette=np.array([int(v) for v in g.findtext('BoneIDs').split(',')]);active=data[:,wi:wi+4]>0
                    original=palette[data[:,ii:ii+4].astype(int)[active]];mapped=np.zeros((len(data),4),int);mapped[active]=[remap[int(x)] for x in original]
                    if not np.array_equal(np.array(selected)[mapped[active]],original):raise ValueError('Weighted joint association changed')
                    data[:,ii:ii+4]=mapped;g.find('BoneIDs').text=', '.join(map(str,range(len(selected))))
                    g.find('VertexBuffer/Data').text='\n'+'\n'.join(' '.join(format(float(x),'.9g') for x in row) for row in data)+'\n'
                    triangles+=len(g.findtext('IndexBuffer/Data').split())//3
                if not len(gs):lod.remove(model)
        if index!=len(geometries):raise ValueError('Unhandled geometry hierarchy')
        reject_inward(doc);result.append((doc,{'bones':len(selected),'geometries':len(group['geometries']),'triangles':triangles,'weighted_associations_preserved':True}))
    original_triangles=sum(len(g.findtext('IndexBuffer/Data').split())//3 for g in geometries)
    if sum(r[1]['triangles'] for r in result)!=original_triangles:raise ValueError('Faces lost/duplicated across parts')
    return result

def prepare(converted,out,roster):
    if out.exists():raise ValueError('Use a fresh output directory')
    out.mkdir(parents=True);reports=[];extended=copy.deepcopy(roster)
    for boss in roster['bosses']:
        c,name=boss['character'],boss['model'];source=converted/c;root=E.parse(source/(name+'.ydr.xml')).getroot()
        if len(root.findall('Skeleton/Bones/Item'))<=255:shutil.copytree(source,out/c);continue
        parts=partition(root)
        if len(parts)!=2:raise ValueError('Current runtime supports exactly one synchronized visual child')
        receipt=json.loads((source/(name+'.conversion.json')).read_text())
        for i,(doc,report) in enumerate(parts):
            target_name=name if i==0 else name+'_part1';target_char=c if i==0 else c+'_part1';dst=out/target_char;dst.mkdir()
            if doc.find('Name') is not None:doc.find('Name').text=target_name
            shutil.copytree(source/name,dst/target_name)
            E.indent(doc);E.ElementTree(doc).write(dst/(target_name+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
            shutil.copy2(source/(name+'_anims.ycd.xml'),dst/(target_name+'_anims.ycd.xml'))
            rec=copy.deepcopy(receipt);rec['render_partition']=report;(dst/(target_name+'.conversion.json')).write_text(json.dumps(rec,indent=2)+'\n')
            reports.append({'model':target_name,**report})
            if i:extended['bosses'].append({**boss,'character':target_char,'model':target_name,'visual_child_of':name})
    (out/'render-roster.json').write_text(json.dumps(extended,indent=2)+'\n');(out/'rig-partitions.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('converted','out','roster'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.converted,a.out,json.loads(a.roster.read_text())),indent=2))
