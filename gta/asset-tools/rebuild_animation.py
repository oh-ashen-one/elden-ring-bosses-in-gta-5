#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Rebuild private GTA animation channels from the source glTF poses.

The YDR and glTF use different per-bone rest axes. Preserve the YDR bind rig and
map source animated world matrices through that constant rest-axis correction;
then derive local GTA tracks. This avoids reinterpreting Blender pose f-curves.
No game/renderer is launched, no source file is overwritten, no retail data is
redistributed. Output XML remains private derived game data.
"""
import argparse
import json
import struct
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation

Y_UP_TO_Z_UP = np.array([[1.,0,0,0],[0,0,-1.,0],[0,1.,0,0],[0,0,0,1.]])


def matrix(translation, rotation, scale):
    result=np.eye(4)
    result[:3,:3]=Rotation.from_quat(rotation).as_matrix()@np.diag(scale)
    result[:3,3]=translation
    return result


def world_matrices(locals_, parents):
    result=[None]*len(locals_)
    visiting=set()
    def resolve(i):
        if result[i] is not None:return result[i]
        if i in visiting:raise ValueError('Skeleton cycle')
        visiting.add(i)
        parent=parents[i]
        result[i]=locals_[i] if parent<0 else resolve(parent)@locals_[i]
        visiting.remove(i)
        return result[i]
    return np.array([resolve(i) for i in range(len(locals_))])


def split_matrix(value):
    translation=value[:3,3]
    scale=np.linalg.norm(value[:3,:3],axis=0)
    if np.min(scale)<1e-8:raise ValueError('Singular animation transform')
    rot=value[:3,:3]/scale
    if np.linalg.det(rot)<0:scale[0]*=-1;rot[:,0]*=-1
    if not np.allclose(rot.T@rot,np.eye(3),atol=1e-3):raise ValueError('Sheared animation transform')
    return translation,Rotation.from_matrix(rot).as_quat(),scale


class SourceGLB:
    def __init__(self,path):
        raw=path.read_bytes()
        if raw[:4]!=b'glTF' or struct.unpack_from('<I',raw,4)[0]!=2:raise ValueError('Expected glTF 2.0')
        n,kind=struct.unpack_from('<I4s',raw,12)
        if kind!=b'JSON':raise ValueError('Missing JSON chunk')
        self.doc=json.loads(raw[20:20+n]);length,kind=struct.unpack_from('<I4s',raw,20+n)
        if kind!=b'BIN\0':raise ValueError('Missing embedded BIN chunk')
        self.binary=raw[28+n:28+n+length]
        self.nodes=self.doc['nodes'];self.parents=[-1]*len(self.nodes);self.arrays={}
        for i,node in enumerate(self.nodes):
            for child in node.get('children',[]):self.parents[child]=i
        joints=sorted({i for skin in self.doc['skins'] for i in skin['joints']})
        names=[self.nodes[i].get('name') for i in joints]
        if len(set(names))!=len(names):raise ValueError('Ambiguous duplicate source node names')
        self.names={self.nodes[i]['name']:i for i in joints}
        self.rest_trs=[(np.array(n.get('translation',[0.,0,0])),np.array(n.get('rotation',[0.,0,0,1.])),np.array(n.get('scale',[1.,1,1]))) for n in self.nodes]
        if any('matrix' in n for n in self.nodes):raise ValueError('Expected source exporter TRS nodes')
        self.rest=world_matrices([matrix(*v) for v in self.rest_trs],self.parents)
        self.animations={a['name']:a for a in self.doc.get('animations',[])}

    def accessor(self,index):
        if index in self.arrays:return self.arrays[index]
        a=self.doc['accessors'][index];v=self.doc['bufferViews'][a['bufferView']]
        if 'sparse' in a or 'byteStride' in v:raise ValueError('Unexpected sparse/interleaved source accessor')
        dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        values=np.frombuffer(self.binary,dtype=dtype,count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width).astype(float)
        if not np.isfinite(values).all():raise ValueError('Non-finite glTF data')
        self.arrays[index]=values;return values

    def sample(self,name,time):
        animation=self.animations[name];trs=[[x.copy() for x in triple] for triple in self.rest_trs]
        for channel in animation['channels']:
            sampler=animation['samplers'][channel['sampler']]
            times=self.accessor(sampler['input'])[:,0];values=self.accessor(sampler['output'])
            kind=sampler.get('interpolation','LINEAR')
            if kind not in ('LINEAR','STEP'):raise ValueError('Unsupported source interpolation')
            slot={'translation':0,'rotation':1,'scale':2}[channel['target']['path']]
            i=max(0,min(len(times)-2,int(np.searchsorted(times,time)-1)))
            if len(times)==1 or kind=='STEP':value=values[i].copy()
            else:
                alpha=float(np.clip((time-times[i])/(times[i+1]-times[i]),0,1))
                a,b=values[i].copy(),values[i+1].copy()
                if slot==1:
                    dot=float(np.dot(a,b))
                    if dot<0:b=-b;dot=-dot
                    dot=np.clip(dot,-1,1)
                    if dot<0.9995:
                        angle=np.arccos(dot)
                        value=(np.sin((1-alpha)*angle)*a+np.sin(alpha*angle)*b)/np.sin(angle)
                    else:value=a*(1-alpha)+b*alpha
                    value/=np.linalg.norm(value)
                else:value=a*(1-alpha)+b*alpha
            trs[channel['target']['node']][slot]=value
        return world_matrices([matrix(*v) for v in trs],self.parents)


class TargetRig:
    def __init__(self,drawable,source):
        bones=drawable.findall('Skeleton/Bones/Item')
        if not bones:raise ValueError('Drawable lacks skeleton')
        def vector(element,axes='xyz'):return [float(element.get(a)) for a in axes]
        self.names=[b.findtext('Name') for b in bones]
        self.tags=[int(b.find('Tag').get('value')) for b in bones]
        self.parents=[int(b.find('ParentIndex').get('value')) for b in bones]
        self.locals=[matrix(vector(b.find('Translation')),vector(b.find('Rotation'),'xyzw'),vector(b.find('Scale'))) for b in bones]
        self.rest=world_matrices(self.locals,self.parents)
        self.source_ids=[source.names.get(name) for name in self.names]
        self.corrections=[np.linalg.inv(Y_UP_TO_Z_UP@source.rest[gi])@self.rest[i] if gi is not None else np.eye(4) for i,gi in enumerate(self.source_ids)]
        if len(set(self.tags))!=len(self.tags):raise ValueError('Duplicate GTA bone tags')
        for i,gi in enumerate(self.source_ids):
            if gi is None and self.names[i]!='ERGT_Root':raise ValueError('Unmapped target bone: '+self.names[i])
            if gi is not None and np.linalg.norm(self.corrections[i][:3,3])>0.002:
                raise ValueError('Source and GTA bind joints differ in position: '+self.names[i])

    def pose(self,source_world):
        world=[]
        for i,gi in enumerate(self.source_ids):
            if gi is not None:world.append(Y_UP_TO_Z_UP@source_world[gi]@self.corrections[i])
            else:world.append(self.rest[i])
        return [split_matrix(value if self.parents[i]<0 else np.linalg.inv(world[self.parents[i]])@value) for i,value in enumerate(world)]


def set_channel_data(sequence, values, quaternion=False):
    channels=ET.SubElement(sequence,'Channels')
    constant=np.max(np.abs(values-values[0]))<1e-9
    # Native StaticQuaternion stores XYZ only and reconstructs POSITIVE W.
    # q and -q encode the same rotation; flip all four components together.
    # Near W=0 the square-root reconstruction loses precision, so keep all
    # four float components explicitly even for a constant rotation.
    static_value=values[0].copy()
    if quaternion and static_value[3]<0:static_value=-static_value
    compact=constant and (not quaternion or static_value[3]>=0.05)
    if compact:
        item=ET.SubElement(channels,'Item');ET.SubElement(item,'Type',value='StaticQuaternion' if quaternion else 'StaticVector3')
        ET.SubElement(item,'Value',**{a:format(float(v),'.9g') for a,v in zip('xyzw' if quaternion else 'xyz',static_value)})
    else:
        for component in values.T:
            item=ET.SubElement(channels,'Item');ET.SubElement(item,'Type',value='RawFloat')
            ET.SubElement(item,'Values').text=' '.join(format(float(v),'.9g') for v in component)


def rebuild(glb,drawable,template,out):
    if out.exists():raise ValueError('Use a new output; existing files are preserved')
    source=SourceGLB(glb);rig=TargetRig(ET.parse(drawable),source)
    document=ET.parse(template);report=[]
    for animation in document.findall('Animations/Item'):
        encoded=animation.findtext('Hash');matches=[n for n in source.animations if encoded.endswith('_'+n)]
        if len(matches)!=1:raise ValueError('Animation name mapping is ambiguous')
        name=matches[0];count=int(animation.find('FrameCount').get('value'));duration=float(animation.find('Duration').get('value'))
        if count<2 or duration<=0:raise ValueError('Invalid template duration')
        samples=[rig.pose(source.sample(name,t)) for t in np.linspace(0,duration,count)]
        by_bone=[]
        for i in range(len(rig.names)):
            tracks=[np.stack([pose[i][track] for pose in samples]) for track in range(3)]
            for f in range(1,count):
                if np.dot(tracks[1][f-1],tracks[1][f])<0:tracks[1][f]*=-1
            by_bone.append(tracks)
        ids=animation.find('BoneIds');sequences=animation.find('Sequences')
        for e in list(ids):ids.remove(e)
        for e in list(sequences):sequences.remove(e)
        sequence=ET.SubElement(sequences,'Item');ET.SubElement(sequence,'Hash').text='hash_00000000'
        ET.SubElement(sequence,'FrameCount',value=str(count));data=ET.SubElement(sequence,'SequenceData')
        for track in range(3):
            for i in sorted(range(len(rig.tags)),key=lambda x:rig.tags[x]):
                b=ET.SubElement(ids,'Item');ET.SubElement(b,'BoneId',value=str(rig.tags[i]));ET.SubElement(b,'Track',value=str(track));ET.SubElement(b,'Unk0',value='1' if track==1 else '0')
                set_channel_data(ET.SubElement(data,'Item'),by_bone[i][track],track==1)
        source_samples=max(len(source.accessor(s['input'])) for s in source.animations[name]['samplers'])
        report.append({'clip':name,'target_frames':count,'source_samples_available':source_samples,'duration':duration})
    out.parent.mkdir(parents=True,exist_ok=True);ET.indent(document)
    with out.open('xb') as f:document.write(f,encoding='utf-8',xml_declaration=True)
    receipt={'source':str(glb),'bones':len(rig.tags),'clips':report,'runtime_verified':False,
             'note':'Preserves available glTF motion. Re-export from owned source at full rate to recover samples omitted by older exporter.'}
    out.with_suffix(out.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['glb','drawable','template','out']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(rebuild(a.glb,a.drawable,a.template,a.out),indent=2))
