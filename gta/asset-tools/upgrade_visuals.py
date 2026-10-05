#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Adapt private converted creatures to skinned object materials, without Blender.

Preserves source vertices, weights, bones, animations and source pixel dimensions.
All outputs are derived retail content and MUST remain private. This does not
recreate Elden Ring's renderer, shell fur, cloth simulation or layered shading.
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

CHARACTERS = [('c2120', 'ergt_malenia'), ('c3181', 'ergt_redwolf'), ('c2270', 'ergt_crab')]
SIZES = {'Position': 3, 'BlendWeights': 4, 'BlendIndices': 4, 'Normal': 3,
         'Colour0': 4, 'Colour1': 4, 'TexCoord0': 2, 'TexCoord1': 2, 'TexCoord2': 2, 'Tangent': 4}


def read_image(path):
    data = bytearray(path.read_bytes())
    if data[84:88] == b'DX10':
        fmt = struct.unpack_from('<I', data, 128)[0]
        if fmt in (72, 75, 78): struct.pack_into('<I', data, 128, fmt-1)
    return np.array(Image.open(io.BytesIO(data)).convert('RGBA'))


def normal_pixels(pixels):
    """ER RG encodes the normal; B/A can hold material data, not normal Z."""
    out = pixels.copy()
    xy = pixels[:, :, :2].astype(np.float64)/127.5-1
    length = np.sqrt(np.maximum(1, (xy*xy).sum(axis=2)))
    xy /= length[:, :, None]
    out[:, :, :2] = np.rint((xy+1)*127.5).astype(np.uint8)
    out[:, :, 2] = np.rint((np.sqrt(np.maximum(0, 1-(xy*xy).sum(axis=2)))+1)*127.5).astype(np.uint8)
    out[:, :, 3] = 255
    return out


def write_dds(path, pixels, normal=False):
    """RGBA8 with a complete mip chain. No lossy extra compression/upscaling."""
    height, width = pixels.shape[:2]
    levels = []
    image = Image.fromarray(pixels)
    while True:
        level = np.array(image)
        if normal: level = normal_pixels(level)
        levels.append(level.tobytes())
        if image.size == (1, 1): break
        image = image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.LANCZOS)
    header = [124, 0x2100f, height, width, width*4, 0, len(levels), *([0]*11),
              32, 0x41, 0, 32, 0xff, 0xff00, 0xff0000, 0xff000000,
              0x401008, 0, 0, 0, 0]
    with path.open('xb') as f: f.write(b'DDS '+struct.pack('<31I',*header)+b''.join(levels))
    return width, height, len(levels)


def tangents(position, normal, uv, indices):
    triangles = indices.reshape(-1,3)
    p = position[triangles];t = uv[triangles]
    e1,e2 = p[:,1]-p[:,0],p[:,2]-p[:,0]
    t1,t2 = t[:,1]-t[:,0],t[:,2]-t[:,0]
    determinant = t1[:,0]*t2[:,1]-t1[:,1]*t2[:,0]
    inv = np.divide(1,determinant,out=np.zeros_like(determinant),where=np.abs(determinant)>1e-10)
    s = (e1*t2[:,1,None]-e2*t1[:,1,None])*inv[:,None]
    b = (e2*t1[:,0,None]-e1*t2[:,0,None])*inv[:,None]
    total=np.zeros_like(position);bitangent=np.zeros_like(position)
    for lane in range(3):
        np.add.at(total,triangles[:,lane],s);np.add.at(bitangent,triangles[:,lane],b)
    total -= normal*(total*normal).sum(axis=1)[:,None]
    lengths=np.linalg.norm(total,axis=1)
    bad=lengths<1e-8
    axes=np.tile([0.,1.,0.],(int(bad.sum()),1))
    axes[np.abs(normal[bad,1])>0.9]=[1,0,0]
    total[bad]=np.cross(axes,normal[bad])
    total /= np.maximum(np.linalg.norm(total,axis=1)[:,None],1e-8)
    handed=np.where((np.cross(normal,total)*bitangent).sum(axis=1)<0,-1.,1.)
    return np.column_stack([total,handed])


def convert_layout(geometry):
    vb=geometry.find('VertexBuffer');layout=vb.find('Layout')
    names=[x.tag for x in layout];width=sum(SIZES[n] for n in names)
    data=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,width)
    arrays={};offset=0
    for name in names:
        arrays[name]=data[:,offset:offset+SIZES[name]].copy();offset+=SIZES[name]
    indices=np.fromstring(geometry.findtext('IndexBuffer/Data'),sep=' ',dtype=np.int64)
    arrays['Tangent']=tangents(arrays['Position'],arrays['Normal'],arrays['TexCoord0'],indices)
    names=['Position','BlendWeights','BlendIndices','Normal','Colour0','TexCoord0','Tangent']
    for child in list(layout):layout.remove(child)
    for name in names:ET.SubElement(layout,name)
    data=np.column_stack([arrays[name] for name in names])
    vb.find('Data').text='\n'+'\n'.join(' '.join(format(v,'.9g') for v in row) for row in data)+'\n'
    return len(data),len(indices)//3


def upgrade(source, root, output):
    if output.exists():raise ValueError('Use a new output directory; originals are preserved')
    output.mkdir(parents=True)
    report=[]
    materials=json.loads((root/'materials-with-params.json').read_text())
    hair_material=next(v for k,v in materials.items() if 'c2120' in k.lower() and 'hair_long.matbin' in k.lower())
    hair_params={p['name']:p['value'] for p in hair_material['params']}
    for character,name in CHARACTERS:
        folder=source/character;out=output/character;out.mkdir()
        texture_dir=out/name;shutil.copytree(folder/name,texture_dir)
        document=ET.parse(folder/(name+'.ydr.xml'));drawable=document.getroot()
        dictionary=drawable.find('ShaderGroup/TextureDictionary')
        texture_by_name={t.findtext('Name'):t for t in dictionary}
        conversions={};samples=[]
        def texture(pixels,filename,normal=False):
            if filename in conversions:return Path(filename).stem
            w,h,mips=write_dds(texture_dir/filename,pixels,normal)
            item=ET.SubElement(dictionary,'Item');ET.SubElement(item,'Name').text=Path(filename).stem
            ET.SubElement(item,'Unk32',value='0');ET.SubElement(item,'Usage').text='NORMAL' if normal else 'DIFFUSE'
            for tag,value in [('ExtraFlags',0),('Width',w),('Height',h),('MipLevels',mips)]:ET.SubElement(item,tag,value=str(value))
            ET.SubElement(item,'Format').text='D3DFMT_A8B8G8R8';ET.SubElement(item,'FileName').text=filename
            conversions[filename]={'width':w,'height':h,'mips':mips}
            return Path(filename).stem
        spec_name=texture(np.full((4,4,4),255,dtype=np.uint8),'ergt_spec_white.dds')
        for shader in drawable.findall('ShaderGroup/Shaders/Item'):
            old=shader.find('Parameters')
            def sampler(n):return old.findtext(f"Item[@name='{n}']/Name")
            diffuse,bump=sampler('DiffuseSampler'),sampler('BumpSampler')
            cutout='cutout' in shader.findtext('FileName')
            hair=character=='c2120' and diffuse and '_hair_long' in diffuse
            if hair:
                # HairLong's actual material uses PCHair_n opacity, not the
                # unrelated c2120_hair2 atlas formerly borrowed as a fallback.
                npath=root/'textures/common/AAT500_PCHair_n.dds'
                packed=read_image(npath)
                mask=read_image(root/'textures/common/AAT500_PCHair_3m.dds')
                if mask.shape!=packed.shape:raise ValueError('Hair source atlas sizes differ')
                linear=np.array(hair_params['P_ChrCustomize__Hair__snp_0_color_4'][:3])*np.array(hair_params['g_DiffuseMapColor'][:3])
                srgb=np.where(linear<=0.0031308,12.92*linear,1.055*linear**(1/2.4)-0.055)
                rgba=np.zeros_like(packed);rgba[:,:,:3]=np.rint(srgb[None,None,:]*(0.65+0.35*mask[:,:,2:3]/255)*255).astype(np.uint8)
                rgba[:,:,3]=packed[:,:,3]
                diffuse=texture(rgba,'ergt_malenia_hair_source_atlas.dds')
                bump=texture(normal_pixels(packed),'ergt_malenia_hair_normal.dds',True)
            elif bump:
                item=texture_by_name[bump];pixels=read_image(texture_dir/item.findtext('FileName'))
                bump=texture(normal_pixels(pixels),'ergt_'+bump+'_rgbn.dds',True)
            if diffuse and 'furblurnoise' in diffuse:
                # The original shell shader uses procedural expansion. Treating
                # its noise as albedo made a low-resolution noise coat. Use the
                # character's existing base atlas on the retained shell geometry.
                replacement='c2120_body_a' if character=='c2120' else 'c3181_body_a'
                if replacement in texture_by_name:diffuse=replacement
            shader.find('Name').text='normal_spec'
            shader.find('FileName').text='normal_spec_cutout.sps' if cutout else 'normal_spec.sps'
            shader.find('RenderBucket').set('value','3' if cutout else '0')
            shader.remove(old);params=ET.SubElement(shader,'Parameters')
            for key,val in [('DiffuseSampler',diffuse),('BumpSampler',bump),('SpecSampler',spec_name)]:
                if not val:raise ValueError(f'{name}: missing {key}')
                item=ET.SubElement(params,'Item',name=key,type='Texture');ET.SubElement(item,'Name').text=val
            # Conservative approximation; ER metallic/roughness channels are
            # not blindly reinterpreted as GTA's unrelated specular encoding.
            values={'HardAlphaBlend':1,'useTessellation':0,'wetnessMultiplier':1,'bumpiness':1,
                    'specMapIntMask':1,'specularIntensityMult':0.18 if cutout else 0.45,
                    'specularFalloffMult':35 if cutout else 75,'specularFresnel':0.65}
            for key,val in values.items():ET.SubElement(params,'Item',name=key,type='Vector',x=str(val),y='0',z='0',w='0')
        vertices=triangles=0
        for geometry in drawable.findall('DrawableModelsHigh/Item/Geometries/Item'):
            v,t=convert_layout(geometry);vertices+=v;triangles+=t
        ET.indent(document);document.write(out/(name+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
        for suffix in ['.conversion.json','_anims.ycd.xml']:
            shutil.copy2(folder/(name+suffix),out/(name+suffix))
        report.append({'model':name,'vertices':vertices,'triangles':triangles,'new_textures':conversions,
                       'source_skeleton_animation_preserved':True,'runtime_visual_verified':False})
    (output/'visual-upgrade.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--converted',type=Path,required=True)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();upgrade(a.converted.resolve(),a.root.resolve(),a.out.resolve())
