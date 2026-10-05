#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Private source-driven GTA material adaptation; no game/renderer launch.

ER metallic masks and normal-map gloss become bounded GTA specular inputs.
Shell-fin opacity is baked from the authored strand mask and alternate UVs.
This is an explicit target-renderer approximation, not an ER shader port.
"""
import argparse,copy,hashlib,json,re,shutil,struct,unicodedata
from pathlib import Path,PureWindowsPath
from xml.etree import ElementTree as E
import numpy as np
from PIL import Image
from upgrade_visuals import SIZES,read_image,normal_pixels,convert_layout,write_dds
from normalize_dds import normalize_dds
from compact_skin_palette import compact

def key(path):return PureWindowsPath(path).stem.lower()
def sample(image,uv):
    h,w=image.shape[:2];u=(uv[...,0]%1)*(w-1);v=(uv[...,1]%1)*(h-1)
    x=np.floor(u).astype(int);y=np.floor(v).astype(int);fx=u-x;fy=v-y
    return ((image[y,x]*(1-fx)[...,None]+image[y,np.minimum(x+1,w-1)]*fx[...,None])*(1-fy)[...,None]+
            (image[np.minimum(y+1,h-1),x]*(1-fx)[...,None]+image[np.minimum(y+1,h-1),np.minimum(x+1,w-1)]*fx[...,None])*fy[...,None])

def fields(geometry):
    vb=geometry.find('VertexBuffer');names=[n.tag for n in vb.find('Layout')]
    values=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,sum(SIZES[n] for n in names));out={};i=0
    for name in names:out[name]=values[:,i:i+SIZES[name]];i+=SIZES[name]
    return out

def fur_opacity(geometries,mask,size,tile):
    """Bake UV1 strand coverage into the retained primary UV atlas.

    Overlapping fin islands use maximum coverage. Source layer alpha provides
    a tip fade. This avoids rendering procedural shell fins as solid triangles.
    """
    width,height=size;alpha=np.zeros((height,width),np.float32);covered=np.zeros((height,width),bool)
    for g in geometries:
        f=fields(g)
        if 'TexCoord1' not in f:raise ValueError('Shell material requires preserved alternate UVs')
        triangles=np.fromstring(g.findtext('IndexBuffer/Data'),sep=' ',dtype=int).reshape(-1,3)
        for ids in triangles:
            uv=f['TexCoord0'][ids];shift=np.floor(uv.mean(0));p=(uv-shift)*[width-1,height-1]
            lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),[width-1,height-1])
            if (lo>hi).any():continue
            a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-8:continue
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
            w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w2=1-w0-w1
            inside=(w0>=-.002)&(w1>=-.002)&(w2>=-.002)
            weights=np.stack([w0,w1,w2],axis=-1);secondary=weights@f['TexCoord1'][ids]
            strands=sample(mask.astype(np.float32),secondary*np.asarray(tile))[:,:,3]/255
            layer=np.clip((weights@f['Colour0'][ids,3])/255,0,1)
            opacity=np.sqrt(np.clip(strands*(1-layer),0,1))
            target=alpha[lo[1]:hi[1]+1,lo[0]:hi[0]+1];target[inside]=np.maximum(target[inside],opacity[inside])
            covered[lo[1]:hi[1]+1,lo[0]:hi[0]+1]|=inside
    if not covered.any():raise ValueError('No valid fin UV coverage')
    # One-texel dilation avoids sampling transparent black at island borders.
    image=Image.fromarray(np.rint(alpha*255).astype(np.uint8))
    from PIL.ImageFilter import MaxFilter
    return np.asarray(image.filter(MaxFilter(3)))

def spec_pixels(normal,metal,kind):
    width=normal.shape[1];height=normal.shape[0]
    gloss=np.asarray(Image.fromarray(normal[:,:,2]).resize((width,height),Image.Resampling.LANCZOS)).astype(float)/255
    m=np.asarray(Image.fromarray(metal[:,:,0]).resize((width,height),Image.Resampling.LANCZOS)).astype(float)/255 if metal is not None else np.zeros_like(gloss)
    if kind in ('skin','fabric','hair','fur'):m*=0
    # GTA squares R/G then multiplies intensity; white was maximal everywhere.
    reflectance=np.clip(.025+.24*m,.025,.265)
    out=np.zeros((height,width,4),np.uint8);strength=np.rint(np.sqrt(reflectance)*255).astype(np.uint8)
    out[:,:,0]=strength;out[:,:,1]=strength
    out[:,:,3]=np.rint(np.clip(gloss,.08,.9)*255).astype(np.uint8)
    return out

def adapt(converted,source_root,out,roster):
    if out.exists():raise ValueError('Use a new output directory')
    out.mkdir(parents=True)
    materials={key(k):v for k,v in json.loads((source_root/'materials-with-params.json').read_text()).items()}
    reports=[]
    for boss in roster:
        character,name=boss['character'],boss['model'];src=converted/character;dest=out/character;dest.mkdir();textures=dest/name;textures.mkdir()
        receipt=json.loads((src/(name+'.conversion.json')).read_text());tree=E.parse(src/(name+'.ydr.xml'));shaders=tree.findall('ShaderGroup/Shaders/Item')
        sources=receipt['shader_source_paths']
        if len(sources)!=len(shaders) or not all(sources):raise ValueError('Missing/ambiguous material provenance')
        dictionary=tree.find('ShaderGroup/TextureDictionary')
        if dictionary is None:dictionary=E.SubElement(tree.find('ShaderGroup'),'TextureDictionary')
        for item in list(dictionary):dictionary.remove(item)
        texture_paths={p.stem.lower():p for p in (source_root/'textures/common').glob('*.dds')}
        texture_paths.update({p.stem.lower():p for p in (source_root/'textures'/character).glob('*.dds')})
        image_cache={};written={};details=[]
        def pixels(path):
            if path not in image_cache:image_cache[path]=read_image(path)
            return image_cache[path]
        def add_texture(label,data,usage='DIFFUSE',source=None):
            label=unicodedata.normalize('NFKC',label).lower();label.encode('ascii')
            if label in written:return label
            filename=label+'.dds';path=textures/filename
            if source:
                original=source.read_bytes();encoded,changed=normalize_dds(original)
                # Keep every original mip/pixel byte. Only DXGI sRGB metadata
                # may change to its storage-identical Legacy enum.
                offset=148 if encoded[84:88]==b'DX10' else 128
                assert original[offset:]==encoded[offset:]
                path.write_bytes(encoded)
                levels=max(1,struct.unpack_from('<I',encoded,28)[0])
                if encoded[84:88]==b'DX10':
                    dxgi=struct.unpack_from('<I',encoded,128)[0]
                    fmt={28:'D3DFMT_A8B8G8R8',61:'D3DFMT_L8',65:'D3DFMT_A8',71:'D3DFMT_DXT1',74:'D3DFMT_DXT3',77:'D3DFMT_DXT5',80:'D3DFMT_ATI1',83:'D3DFMT_ATI2',87:'D3DFMT_A8R8G8B8',98:'D3DFMT_BC7'}[dxgi]
                else:
                    fmt={b'DXT1':'D3DFMT_DXT1',b'DXT3':'D3DFMT_DXT3',b'DXT5':'D3DFMT_DXT5',b'ATI1':'D3DFMT_ATI1',b'ATI2':'D3DFMT_ATI2'}.get(encoded[84:88])
                    if fmt is None:raise ValueError('Unsupported source DDS metadata: '+str(source))
                metrics={'source':str(source),'source_payload_sha256':hashlib.sha256(original[offset:]).hexdigest(),'pixel_payload_identical':True,'header_normalized':changed}
            else:
                _,_,levels=write_dds(path,data);encoded=path.read_bytes();fmt='D3DFMT_A8B8G8R8'
                if not np.array_equal(read_image(path),data):raise ValueError('Lossless derived map mismatch')
                metrics={'derived_shader_map':True,'lossless_base_pixels':True}
            item=E.SubElement(dictionary,'Item');E.SubElement(item,'Name').text=label;E.SubElement(item,'Unk32',value='0');E.SubElement(item,'Usage').text=usage
            for tag,value in [('ExtraFlags',0),('Width',data.shape[1]),('Height',data.shape[0]),('MipLevels',levels)]:E.SubElement(item,tag,value=str(value))
            E.SubElement(item,'Format').text=fmt;E.SubElement(item,'FileName').text=filename
            written[label]={'width':data.shape[1],'height':data.shape[0],'bytes':len(encoded),'format':fmt,**metrics};return label
        for index,(shader,source_path) in enumerate(zip(shaders,sources)):
            material=materials[key(source_path)];params={p['name']:p['value'] for p in material['params']};samplers=material['samplers']
            def find(token,prefer=''):
                matches=[s for s in samplers if token in s['type'].lower() and s['path'] and key(s['path']) in texture_paths]
                matches.sort(key=lambda s:0 if prefer and prefer in s['type'] else 1)
                return texture_paths[key(matches[0]['path'])] if matches else None
            original=key(source_path);stype=material['shader'].lower();hair='hair' in original or 'hair' in stype;fur='shell' in stype
            kind='fur' if fur else 'hair' if hair else 'skin' if 'sss' in stype or 'skin' in original else 'fabric' if any(x in original for x in ('fabric','fablic','frabic','mant','cloak','cloth','belt','rope')) else 'metal' if any(x in original for x in ('metal','armor','blade','axe','sword','weapon','hd_')) else 'body'
            diffuse_path=find('albedo','_7_AlbedoMap');normal_path=find('normal','_0_NormalMap');metal_path=find('metallic')
            if fur:normal_path=find('normal','_8_NormalMap')
            normal=pixels(normal_path) if normal_path else np.full((4,4,4),[128,128,255,255],np.uint8)
            if hair and 'chrcustomize' in stype:
                tint=np.asarray(params.get('P_ChrCustomize__Hair__snp_0_color_4',[.6,.4,.3])[:3])*np.asarray(params.get('g_DiffuseMapColor',[1,1,1])[:3])
                tint=np.where(tint<=.0031308,12.92*tint,1.055*tint**(1/2.4)-.055)
                diffuse=np.zeros_like(normal);diffuse[:,:,:3]=np.rint(np.clip(tint,0,1)*255).astype(np.uint8);diffuse[:,:,3]=normal[:,:,3]
                diffuse_name='ergt_'+character+'_hair_'+str(index)
            else:
                if not diffuse_path:raise ValueError('Missing authored diffuse for '+original)
                diffuse=pixels(diffuse_path).copy();diffuse_name=diffuse_path.stem.lower()
                if fur:
                    strand=next((texture_paths[key(s['path'])] for s in samplers if '_6_AlbedoMap' in s['type'] and s['path'] and key(s['path']) in texture_paths),None)
                    if strand is None:strand=texture_paths.get('aat500_shellfur_00_a')
                    if strand is None:raise ValueError('Shell material lacks an authored strand mask')
                    geometry=[g for g in tree.findall('.//Geometries/Item') if int(g.find('ShaderIndex').get('value'))==index]
                    diffuse[:,:,3]=fur_opacity(geometry,pixels(strand),(diffuse.shape[1],diffuse.shape[0]),params.get('group_7_CommonUV-UVParam',[40,40]))
                    diffuse_name='ergt_'+character+'_fur_'+str(index)
            normal_name='ergt_'+(normal_path.stem.lower() if normal_path else 'flat')+'_normal'
            spec_name='ergt_'+hashlib.sha256((str(normal_path)+str(metal_path)+kind).encode()).hexdigest()[:16]+'_spec'
            diffuse_name=add_texture(diffuse_name,diffuse,source=diffuse_path if not fur and not (hair and 'chrcustomize' in stype) else None)
            normal_name=add_texture(normal_name,normal,'NORMAL',source=normal_path)
            spec_name=add_texture(spec_name,spec_pixels(normal,pixels(metal_path) if metal_path else None,kind),'SPECULAR')
            blend=hair or fur;shader.find('Name').text='normal_spec';shader.find('FileName').text='normal_spec_alpha.sps' if blend else 'normal_spec.sps';shader.find('RenderBucket').set('value','1' if blend else '0')
            old=shader.find('Parameters');shader.remove(old);p=E.SubElement(shader,'Parameters')
            for n,value in [('DiffuseSampler',diffuse_name),('BumpSampler',normal_name),('SpecSampler',spec_name)]:
                i=E.SubElement(p,'Item',name=n,type='Texture');E.SubElement(i,'Name').text=value
            values={'HardAlphaBlend':0 if blend else 1,'useTessellation':0,'wetnessMultiplier':0,'bumpiness':1,
                    'specMapIntMask':1,'specularIntensityMult':.7 if kind=='metal' else .35,
                    'specularFalloffMult':160 if kind=='metal' else 80 if kind=='skin' else 45,
                    'specularFresnel':.085 if kind=='metal' else .035}
            for n,value in values.items():E.SubElement(p,'Item',name=n,type='Vector',x=str(value),y='0',z='0',w='0')
            details.append({'source_material':source_path,'kind':kind,'specular_source':str(metal_path) if metal_path else 'nonmetal baseline','gloss_source':'original normal B','shader':shader.findtext('FileName')})
        for geometry in tree.findall('.//Geometries/Item'):convert_layout(geometry)
        palette=compact(tree.getroot())
        E.indent(tree);tree.write(dest/(name+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
        if (src/(name+'_anims.ycd.xml')).exists():shutil.copy2(src/(name+'_anims.ycd.xml'),dest/(name+'_anims.ycd.xml'))
        receipt['material_fidelity']={'shader_count':len(shaders),'white_spec_removed':True,'normal_packing':'RG compatible; original B used for gloss','runtime_verified':False};receipt['skin_palettes']=palette
        (dest/(name+'.conversion.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        reports.append({'model':name,'materials':details,'textures':written,'palettes':palette,'runtime_verified':False})
        print('Prepared source-driven materials',name,flush=True)
    (out/'material-fidelity-report.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('converted','source-root','out','roster'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();adapt(a.converted,a.source_root,a.out,json.loads(a.roster.read_text())['bosses'])
