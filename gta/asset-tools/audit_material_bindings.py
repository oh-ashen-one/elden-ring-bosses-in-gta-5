# SPDX-License-Identifier: Apache-2.0
"""Check decoded native YDR samplers against reachable YTDs and source DDS.

Input native JSON comes from CodeWalkerBridge audit-materials. Parent links are
read from the actual packed DLC. Does not change textures or launch a renderer.
"""
import argparse
import hashlib
import json
import math
import struct
import zlib
from pathlib import Path
from xml.etree import ElementTree as E


def joaat(text):
    value=0
    for c in text.lower().encode('ascii'):
        value=(value+c)&0xffffffff;value=(value+(value<<10))&0xffffffff;value^=value>>6
    value=(value+(value<<3))&0xffffffff;value^=value>>11
    return (value+(value<<15))&0xffffffff


def binary_members(data):
    magic,count,names_size,encryption=struct.unpack_from('<4I',data)
    if magic!=0x52504637 or encryption not in (0,0x4e45504f):raise ValueError('Expected unencrypted task DLC')
    names=data[16+count*16:16+count*16+names_size]
    for i in range(count):
        entry=data[16+i*16:32+i*16];a,b,c,d=struct.unpack('<4I',entry)
        if b==0x7fffff00 or b&0x80000000:continue
        offset=int.from_bytes(entry[5:8],'little')*512;size=int.from_bytes(entry[2:5],'little')
        name=names[a&0xffff:].split(b'\0',1)[0].decode()
        payload=data[offset:offset+(size or c)]
        if size:payload=zlib.decompress(payload,-15)
        yield name,payload
        if name.endswith('.rpf'):yield from binary_members(payload)


def audit(native,converted,dlc):
    issues=[];rows=[];dictionaries={d['name']:d for d in native['dictionaries']}
    hashes={joaat(name):name for name in dictionaries}
    roots={a['model_hash']:hashes.get(a['texture_dictionary_hash']) for a in native['archetypes']}
    packed=dict(binary_members(dlc));parenting=E.fromstring(packed['gtxd.meta'])
    parents={e.findtext('child'):e.findtext('parent') for e in parenting.findall('txdRelationships/Item')}
    for drawable in native['drawables']:
        name=drawable['name'];current=roots.get(joaat(name));seen=set();available={}
        if not current:issues.append(name+': native archetype TXD root missing')
        while current:
            if current in seen:issues.append(name+': texture parent cycle');break
            seen.add(current)
            if current not in dictionaries:issues.append(name+': missing parent dictionary '+current);break
            for t in dictionaries[current]['textures']:
                if t['name'] in available:issues.append(name+': duplicate reachable texture '+t['name'])
                available[t['name']]=t
            current=parents.get(current)
        source_files=list(converted.glob('*/'+name+'.ydr.xml'))
        if len(source_files)!=1:issues.append(name+': source drawable missing');continue
        source=E.parse(source_files[0]);shaders=source.findall('ShaderGroup/Shaders/Item')
        source_textures={t.findtext('Name'):t for t in source.findall('ShaderGroup/TextureDictionary/Item')}
        if len(shaders)!=len(drawable['shaders']):issues.append(name+': shader count changed')
        samplers=0
        for index,shader in enumerate(drawable['shaders']):
            if index>=len(shaders):continue
            authored=shaders[index];expected={joaat(p.get('name')):p for p in authored.findall('Parameters/Item')}
            if joaat(authored.findtext('FileName'))!=shader['file_hash']:issues.append(name+': shader filename changed')
            for param in shader['parameters']:
                field=expected.get(param['name_hash'])
                if field is None:issues.append(name+': native parameter absent from source');continue
                if param['type']!=0:
                    if param.get('vector') is not None:
                        expected_vector=[float(field.get(axis,'0')) for axis in 'xyzw']
                        if any(not math.isfinite(v) or abs(v-e)>1e-5 for v,e in zip(param['vector'],expected_vector)):
                            issues.append(name+': shader parameter changed '+field.get('name'))
                    continue
                samplers+=1;ref=param['texture'];source_name=field.findtext('Name')
                if ref!=source_name.lower():issues.append(name+': sampler name mismatch '+str(ref))
                if ref not in available:issues.append(name+': unreachable sampler '+str(ref));continue
                item=source_textures.get(source_name);t=available[ref]
                if item is not None:
                    filename=item.findtext('FileName');path=source_files[0].parent/name/filename
                    if path.is_file():
                        data=path.read_bytes();height,width=struct.unpack_from('<II',data,12);levels=max(1,struct.unpack_from('<I',data,28)[0])
                        if (width,height,levels)!=(t['width'],t['height'],t['mips']):issues.append(name+': DDS dimensions/mips changed '+ref)
                    else:issues.append(name+': source DDS missing '+filename)
                else:issues.append(name+': source texture name missing '+str(source_name))
                if min(t['width'],t['height'],t['mips'])<=0:issues.append(name+': empty texture '+ref)
        rows.append({'model':name,'shaders':len(shaders),'samplers':samplers,'reachable_textures':len(available),'parent_dictionaries':len(seen)})
    return {'ok':not issues,'issues':issues,'models':rows,'native_textures':sum(len(d['textures']) for d in dictionaries.values()),
            'dlc_sha256':hashlib.sha256(dlc).hexdigest(),'rendering_verified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','converted','dlc','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=audit(json.loads(a.native.read_text()),a.converted,a.dlc.read_bytes())
    if a.out.exists():raise ValueError('Preserving previous audit')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['ok'] else 1)
