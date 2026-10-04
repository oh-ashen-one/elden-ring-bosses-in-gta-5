#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage a texture-only streaming experiment, preserving source inputs.

Prune unused embedded textures and compress generated RGBA maps to standard
BC7 at identical dimensions (BC3 is available for comparison). Encoding is measured, never described
as pixel-identical. No game, renderer, install or retail modification.
"""
import argparse
import io
import json
import shutil
import struct
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image
from upgrade_visuals import read_image,normal_pixels

def encode(pixels,normal=False,codec='BC3'):
    image=Image.fromarray(pixels);chunks=[];levels=0
    if codec not in ('BC3','BC7'):raise ValueError('Unsupported texture codec')
    if codec=='BC7':
        import ispc_texcomp as itc
        settings=itc.BC7EncSettings.from_profile('alpha_slow')
    while True:
        if normal:image=Image.fromarray(normal_pixels(np.asarray(image)))
        expected=((image.width+3)//4)*((image.height+3)//4)*16
        if codec=='BC3':
            buffer=io.BytesIO();image.save(buffer,format='DDS',pixel_format='DXT5');data=buffer.getvalue()
            if levels==0:header=bytearray(data[:128])
            chunk=data[128:]
            if data[84:88]!=b'DXT5':raise ValueError('Unexpected BC3 encoder layout')
        else:
            # The SIMD encoder expects complete 4x4 blocks, including tiny mips.
            array=np.asarray(image);pw=(image.width+3)//4*4;ph=(image.height+3)//4*4
            array=np.pad(array,((0,ph-image.height),(0,pw-image.width),(0,0)),mode='edge')
            chunk=itc.compress_blocks_bc7(itc.RGBASurface(array.tobytes(),pw,ph,pw*4),settings)
            if levels==0:
                words=[124,0xA1007,image.height,image.width,expected,0,0,*([0]*11),32,4,int.from_bytes(b'DX10','little'),0,0,0,0,0,0x401008,0,0,0,0]
                header=bytearray(b'DDS '+struct.pack('<31I',*words)+struct.pack('<5I',98,3,0,1,0))
        if len(chunk)!=expected:raise ValueError('Unexpected block payload size')
        chunks.append(chunk);levels+=1
        if image.size==(1,1):break
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.LANCZOS)
    # Correct dimensions, full mip count and block-compressed base slice size.
    struct.pack_into('<I',header,8,0xA1007);struct.pack_into('<I',header,20,len(chunks[0]))
    struct.pack_into('<I',header,28,levels);struct.pack_into('<I',header,108,0x401008)
    return bytes(header)+b''.join(chunks),levels

def quality(original,encoded,normal):
    decoded=np.asarray(Image.open(io.BytesIO(encoded)).convert('RGBA'));a=original.astype(np.float32);b=decoded.astype(np.float32)
    report={'dimensions_preserved':list(decoded.shape)==list(original.shape),'channel_rmse':np.sqrt(np.mean((a-b)**2,axis=(0,1))).tolist(),
            'alpha_128_coverage_change':float(np.mean((a[:,:,3]>=128)!=(b[:,:,3]>=128)))}
    if normal:
        x=a[:,:,:3]/127.5-1;y=b[:,:,:3]/127.5-1
        x/=np.maximum(np.linalg.norm(x,axis=2)[:,:,None],1e-8);y/=np.maximum(np.linalg.norm(y,axis=2)[:,:,None],1e-8)
        angles=np.rad2deg(np.arccos(np.clip(np.sum(x*y,axis=2),-1,1)))
        report['normal_angle_mean_degrees']=float(angles.mean());report['normal_angle_p99_degrees']=float(np.percentile(angles,99))
    return report

def prepare(converted,out,character,model,codec='BC7'):
    if any(Path(v).name!=v or v in ('.','..') for v in (character,model)):raise ValueError('Invalid model/character identifier')
    if out.exists():raise ValueError('Preserving existing output; choose a new directory')
    shutil.copytree(converted,out)
    path=out/character/(model+'.ydr.xml');tree=ET.parse(path);dictionary=tree.find('ShaderGroup/TextureDictionary')
    refs={p.findtext('Name') for p in tree.findall("ShaderGroup/Shaders/Item/Parameters/Item[@type='Texture']")}
    available={t.findtext('Name') for t in dictionary}
    if not refs<=available:raise ValueError('Unresolved sampler; preserving staged output for diagnosis')
    removed=[];changed=[];folder=out/character/model
    for item in list(dictionary):
        name=item.findtext('Name');filename=item.findtext('FileName')
        if not filename or Path(filename).name!=filename:raise ValueError('Unsafe texture filename')
        if name not in refs:dictionary.remove(item);removed.append(name);continue
        if item.findtext('Format')!='D3DFMT_A8B8G8R8' or name=='ergt_spec_white':continue
        pixels=read_image(folder/filename);normal=item.findtext('Usage')=='NORMAL'
        data,levels=encode(pixels,normal,codec);metrics=quality(pixels,data,normal)
        # A bounded proposed encoding, not a blind quality downgrade.
        if not metrics['dimensions_preserved'] or metrics['alpha_128_coverage_change']>.001 or metrics.get('normal_angle_p99_degrees',0)>3:
            raise ValueError('Compression review threshold exceeded: '+name+' '+str(metrics))
        newfile=Path(filename).stem+'_'+codec.lower()+'.dds'
        with (folder/newfile).open('xb') as f:f.write(data)
        item.find('FileName').text=newfile;item.find('Format').text='D3DFMT_DXT5' if codec=='BC3' else 'D3DFMT_BC7';item.find('MipLevels').set('value',str(levels))
        changed.append({'name':name,'before_bytes':(folder/filename).stat().st_size,'after_bytes':len(data),**metrics})
    ET.indent(tree);tree.write(path,encoding='utf-8',xml_declaration=True)
    report={'model':model,'codec':codec,'unused_textures_removed':removed,'textures_compressed':changed,'geometry_rig_clips_unchanged':True,
            'encoding_lossy':True,'gta_runtime_verified':False,'status':'staged texture-only hypothesis; not a proven crash repair'}
    (out/'streaming-experiment.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('converted','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--character',default='c2120');p.add_argument('--model',default='ergt_malenia')
    p.add_argument('--codec',choices=['BC7','BC3'],default='BC7')
    a=p.parse_args();print(json.dumps(prepare(a.converted,a.out,a.character,a.model,a.codec),indent=2))
