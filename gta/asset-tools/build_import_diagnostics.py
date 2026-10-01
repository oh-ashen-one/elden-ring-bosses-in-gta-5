# SPDX-License-Identifier: Apache-2.0
"""Prepare PRIVATE same-mesh import variants; not a completed creature port.

Keep every original input untouched. Does not run GTA or render anything.
"""
import argparse
import copy
import json
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

WIDTHS = {'Position':3,'BlendWeights':4,'BlendIndices':4,'Normal':3,
          'Colour0':4,'Colour1':4,'TexCoord0':2,'TexCoord1':2,'Tangent':4}


def rigid_mesh(root):
    for tag in ['Skeleton','Joints','Bounds']:
        node=root.find(tag)
        if node is not None: root.remove(node)
    for model in root.findall('DrawableModelsHigh/Item'):
        for tag,value in [('Flags',0),('HasSkin',0),('BoneIndex',0),('Unknown1',0)]:model.find(tag).set('value',str(value))
        for geometry in model.findall('Geometries/Item'):
            ids=geometry.find('BoneIDs')
            if ids is not None: ids.text=''
            buffer=geometry.find('VertexBuffer');layout=buffer.find('Layout')
            fields=[n.tag for n in layout];total=sum(WIDTHS[n] for n in fields)
            keep=[];offset=0
            for field in fields:
                width=WIDTHS[field]
                if field not in {'BlendWeights','BlendIndices'}:keep.extend(range(offset,offset+width))
                offset+=width
            for field in list(layout):
                if field.tag in {'BlendWeights','BlendIndices'}:layout.remove(field)
            for data_tag in ['Data','Data2']:
                data=buffer.find(data_tag)
                if data is None:continue
                lines=[]
                for line in (data.text or '').splitlines():
                    tokens=line.split()
                    if not tokens:continue
                    if len(tokens)!=total:raise ValueError('Unexpected vertex layout length')
                    lines.append(' '.join(tokens[i] for i in keep))
                data.text='\n'+'\n'.join(lines)+'\n'
    # Simple ordinary-prop shader: retain only the existing source diffuse map.
    for shader in root.findall('ShaderGroup/Shaders/Item'):
        shader.find('Name').text='default';shader.find('FileName').text='default.sps'
        shader.find('RenderBucket').set('value','0')
        parameters=shader.find('Parameters')
        for param in list(parameters):
            if param.get('name')!='DiffuseSampler':parameters.remove(param)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True,help='Existing v3-textures build directory')
    parser.add_argument('--registered',type=Path,required=True,help='Existing v5 DLC input directory')
    parser.add_argument('--animation-xml',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--dotnet',type=Path,required=True)
    parser.add_argument('--bridge',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve()
    if out.exists():raise ValueError('Use a fresh output directory')
    out.mkdir(parents=True);models=out/'model-input';shutil.copytree(args.base/'model-input',models)
    ytyp=ET.parse(args.base/'ergt.ytyp.xml');archetypes=ytyp.getroot().find('archetypes')
    template=next(n for n in archetypes if n.findtext('name')=='ergt_malenia')
    source=args.base/'conversion-input/c2120';variants=[
        ('ergt_test_sta',544,'rigged, static+animation, collision, matching default clip'),
        ('ergt_test_dyn',131584,'rigged, dynamic+animation, collision'),
        ('ergt_test_nocol',544,'rigged, static+animation, no collision'),
        ('ergt_test_rigid',32,'rigid, ordinary shader, no collision')]
    command=[str(args.dotnet.resolve()),str(args.bridge.resolve())]
    def run(*arguments):
        result=subprocess.run([*command,*map(str,arguments)],capture_output=True,text=True,check=True)
        print(result.stdout.strip(),flush=True)
    for name,flags,label in variants:
        folder=out/'xml'/name;folder.mkdir(parents=True)
        shutil.copytree(source/'ergt_malenia',folder/name)
        drawable=ET.parse(source/'ergt_malenia.ydr.xml');root=drawable.getroot();root.find('Name').text=name
        no_collision=name in {'ergt_test_nocol','ergt_test_rigid'}
        if no_collision:
            bounds=root.find('Bounds')
            if bounds is not None:root.remove(bounds)
        if name=='ergt_test_rigid':rigid_mesh(root)
        xml=folder/(name+'.ydr.xml');drawable.write(xml,encoding='utf-8',xml_declaration=True)
        run('convert',xml,models/(name+'.ydr'))
        (models/(name+'.ydr.json')).rename(out/(name+'.verification.json'))
        definition=copy.deepcopy(template)
        for tag in ['name','assetName','textureDictionary']:definition.find(tag).text=name
        definition.find('flags').set('value',str(flags))
        definition.find('physicsDictionary').text='' if no_collision else name
        if name=='ergt_test_rigid':definition.find('clipDictionary').text=''
        archetypes.append(definition)
    # Animated-prop lookup uses the archetype hash to select a default clip.
    # Add this only to the static+animated probe, preserving all original clips.
    clips=ET.parse(args.animation_xml);entries=clips.getroot().find('Clips')
    idle=next(n for n in entries if n.findtext('Hash')=='a000_000020')
    default=copy.deepcopy(idle);default.find('Hash').text='ergt_test_sta'
    default.find('Name').text='pack:/ergt_test_sta.clip';entries.append(default)
    clip_xml=out/'ergt_malenia_anims.ycd.xml';clips.write(clip_xml,encoding='utf-8',xml_declaration=True)
    (models/'ergt_malenia_anims.ycd').unlink()
    run('convert',clip_xml,models/'ergt_malenia_anims.ycd')
    (models/'ergt_malenia_anims.ycd.json').rename(out/'ergt_malenia_anims.verification.json')
    xml=out/'ergt.ytyp.xml';ET.indent(ytyp);ytyp.write(xml,encoding='utf-8',xml_declaration=True)
    (models/'ergt.ytyp').unlink()  # only our fresh copy, never original input
    run('convert',xml,models/'ergt.ytyp');(models/'ergt.ytyp.json').rename(out/'ergt.ytyp.verification.json')
    stage=out/'dlc-input';shutil.copytree(args.registered,stage)
    archive=stage/'x64/models/cdimages/ergt_assets.rpf';archive.unlink()
    run('pack',models,archive);run('pack',stage,out/'dlc.rpf')
    (out/'diagnostics.json').write_text(json.dumps({'variants':variants,'gameplay_verified':False},indent=2)+'\n')


if __name__=='__main__':main()
