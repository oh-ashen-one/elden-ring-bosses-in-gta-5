# SPDX-License-Identifier: Apache-2.0
"""Refresh opaque GTA skeleton cache IDs after bind/hierarchy changes.

Pinned szio 1.4.0.dev1 documents that distinct addon rigs with the same
Unknown50/54/58 can share the wrong cached skeleton. Like its CW adapter, use
deterministic content-derived nonzero IDs; these are not claimed R*'s exact CRC.
"""
import json,zlib
from xml.etree import ElementTree as E

def refresh(root):
    skeleton=root.find('Skeleton')
    if skeleton is None:raise ValueError('Skeleton absent')
    bones=skeleton.findall('Bones/Item');layout=[];bind=[]
    for b in bones:
        base=[b.findtext('Name'),int(b.find('Tag').get('value')),int(b.find('Index').get('value')),int(b.find('ParentIndex').get('value')),b.findtext('Flags','')]
        layout.append(base)
        bind.append([base,*[[float(b.find(t).get(a)) for a in axes] for t,axes in [('Translation','xyz'),('Rotation','xyzw'),('Scale','xyz')]]])
    topology=json.dumps(layout,separators=(',',':')).encode();pose=json.dumps(bind,separators=(',',':')).encode()
    h=0
    for byte in topology:
        h=(h+byte)&0xffffffff;h=(h+(h<<10))&0xffffffff;h^=h>>6
    h=(h+(h<<3))&0xffffffff;h^=h>>11;h=(h+(h<<15))&0xffffffff
    values={'Unknown50':h or 1,'Unknown54':zlib.crc32(topology) or 1,'Unknown58':zlib.crc32(pose) or 1}
    for tag,value in values.items():
        node=skeleton.find(tag)
        if node is None:node=E.SubElement(skeleton,tag)
        node.set('value',str(value))
    return values
