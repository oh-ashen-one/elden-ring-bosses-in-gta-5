# SPDX-License-Identifier: Apache-2.0
"""Minimal format template for corrected source-pose YCD construction.

Contains no retail motion samples. rebuild_animation fills every real channel
from the locally owned GLB; no Blender frame evaluation is required.
"""
from xml.etree import ElementTree as E

def create(model,name,path):
    root=E.Element('ClipDictionary');clips=E.SubElement(root,'Clips');clip=E.SubElement(clips,'Item')
    E.SubElement(clip,'Hash').text=name;E.SubElement(clip,'Name').text='pack:/'+name
    E.SubElement(clip,'Type',value='Animation');E.SubElement(clip,'Unknown30',value='0')
    E.SubElement(clip,'AnimationHash').text=model+'_'+name
    for tag,value in [('StartTime','0'),('EndTime','1'),('Rate','1')]:E.SubElement(clip,tag,value=value)
    animations=E.SubElement(root,'Animations');animation=E.SubElement(animations,'Item');E.SubElement(animation,'Hash').text=model+'_'+name
    for tag,value in [('Unknown10','0'),('FrameCount','2'),('SequenceFrameLimit','32'),('Duration','1')]:E.SubElement(animation,tag,value=value)
    E.SubElement(animation,'Unknown1C').text='hash_B95E7FE6';E.SubElement(animation,'BoneIds');E.SubElement(animation,'Sequences')
    E.indent(root)
    with path.open('xb') as f:E.ElementTree(root).write(f,encoding='utf-8',xml_declaration=True)
