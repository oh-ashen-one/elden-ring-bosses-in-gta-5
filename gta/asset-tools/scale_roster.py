# SPDX-License-Identifier: Apache-2.0
"""Uniform authored-model scale, including rig, clips and physical bounds.

Rotations, times, UVs, texture pixels and topology remain unchanged. Separate
owned root/weapon tracks use the same roster scale in export_roster_motion.
"""
import argparse,json,shutil,math
from pathlib import Path
from xml.etree import ElementTree as E
import numpy as np
from upgrade_visuals import SIZES

def scale_drawable(doc,scale):
    if not math.isfinite(scale) or not .1<=scale<=5:raise ValueError('Unreviewed model scale')
    for g in doc.findall('.//Geometries/Item'):
        vb=g.find('VertexBuffer');names=[x.tag for x in vb.find('Layout')];i=sum(SIZES[n] for n in names[:names.index('Position')])
        data=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,sum(SIZES[n] for n in names));data[:,i:i+3]*=scale
        vb.find('Data').text='\n'+'\n'.join(' '.join(format(float(x),'.9g') for x in row) for row in data)+'\n'
    for b in doc.findall('Skeleton/Bones/Item'):
        t=b.find('Translation')
        for axis in 'xyz':t.set(axis,format(float(t.get(axis))*scale,'.12g'))
    for node in doc.iter():
        if node.tag in ('BoundingBoxMin','BoundingBoxMax','BoundingSphereCenter','BoxMin','BoxMax','BoxCenter','SphereCenter'):
            for axis in 'xyz':
                if node.get(axis) is not None:node.set(axis,format(float(node.get(axis))*scale,'.12g'))
        elif node.tag in ('BoundingSphereRadius','SphereRadius','Margin') and node.get('value') is not None:node.set('value',format(float(node.get('value'))*scale,'.12g'))
        elif node.tag=='Volume':node.set('value',format(float(node.get('value'))*scale**3,'.12g'))
        elif node.tag=='Inertia':
            for axis in 'xyz':node.set(axis,format(float(node.get(axis))*scale**2,'.12g'))
        elif node.tag=='CompositeTransform' and node.text:
            values=np.fromstring(node.text,sep=' ')
            if len(values)!=16:raise ValueError('Unknown collider matrix')
            values[12:15]*=scale;node.text=' '.join(format(float(x),'.12g') for x in values)

def scale_animation(doc,scale):
    for animation in doc.findall('Animations/Item'):
        tracks=[int(x.find('Track').get('value')) for x in animation.findall('BoneIds/Item')]
        for seq in animation.findall('Sequences/Item'):
            channels=seq.findall('SequenceData/Item')
            if len(channels)!=len(tracks):raise ValueError('Animation channel map mismatch')
            for kind,channel in zip(tracks,channels):
                if kind!=0:continue
                for item in channel.findall('Channels/Item'):
                    storage=item.find('Type').get('value')
                    if storage=='StaticVector3':
                        for axis in 'xyz':item.find('Value').set(axis,format(float(item.find('Value').get(axis))*scale,'.12g'))
                    elif storage=='RawFloat':
                        values=np.fromstring(item.findtext('Values'),sep=' ')*scale;item.find('Values').text=' '.join(format(float(x),'.12g') for x in values)
                    else:raise ValueError('Unsupported translation channel storage')

def prepare(converted,out,roster):
    if out.exists():raise ValueError('Use new output')
    out.mkdir(parents=True)
    for b in roster:
        c,n=b['character'],b['model'];dst=out/c;shutil.copytree(converted/c,dst);scale=float(b.get('model_scale',1))
        if scale==1:continue
        drawable=E.parse(dst/(n+'.ydr.xml'));scale_drawable(drawable.getroot(),scale);E.indent(drawable);drawable.write(dst/(n+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
        animation=E.parse(dst/(n+'_anims.ycd.xml'));scale_animation(animation.getroot(),scale);E.indent(animation);animation.write(dst/(n+'_anims.ycd.xml'),encoding='utf-8',xml_declaration=True)
        p=dst/(n+'.conversion.json');r=json.loads(p.read_text())
        if r.get('applied_model_scale',1)!=1:raise ValueError('Refusing a double scale')
        for key in ('collision','render_bounds'):
            if key in r:
                for side in ('min','max'):r[key][side]=[x*scale for x in r[key][side]]
        r['applied_model_scale']=scale;p.write_text(json.dumps(r,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('converted','out','roster'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();prepare(a.converted,a.out,json.loads(a.roster.read_text())['bosses'])
