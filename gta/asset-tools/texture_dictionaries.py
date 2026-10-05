# SPDX-License-Identifier: Apache-2.0
"""Bounded texture dictionaries with standard GTA parent relationships.

Partition whole textures, never their pixels or mip chains. A single large
authored/derived texture may exceed the grouping target; report it explicitly.
"""
import copy
import unicodedata
from xml.etree import ElementTree as E

def normalize_names(document):
    """GTA stores these names as ASCII; preserve source filenames separately."""
    names={}
    for item in document.findall('ShaderGroup/TextureDictionary/Item'):
        old=item.findtext('Name');new=unicodedata.normalize('NFKC',old).lower();new.encode('ascii')
        if new in names.values():raise ValueError('Texture names collide after ASCII normalization')
        names[old]=new;item.find('Name').text=new
    for sampler in document.findall('ShaderGroup/Shaders/Item/Parameters/Item[@type="Texture"]/Name'):
        sampler.text=names[sampler.text]
    return names

def partition(dictionary, folder, target=22*1024*1024):
    if target<=0:raise ValueError('Positive texture grouping target required')
    groups=[];sizes=[];seen=set()
    for item in sorted(dictionary, key=lambda i:(folder/i.findtext('FileName')).stat().st_size,reverse=True):
        name=item.findtext('Name');filename=item.findtext('FileName')
        if not name or name in seen or not filename or '/' in filename or '\\' in filename:raise ValueError('Unsafe/duplicate texture')
        seen.add(name);size=(folder/filename).stat().st_size
        index=next((i for i,s in enumerate(sizes) if s+size<=target),len(groups))
        if index==len(groups):groups.append(E.Element('TextureDictionary'));sizes.append(0)
        groups[index].append(copy.deepcopy(item));sizes[index]+=size
    if not groups:raise ValueError('Empty texture dictionary')
    return groups,sizes

def parenting(chains):
    root=E.Element('CMapParentTxds');relationships=E.SubElement(root,'txdRelationships');children=set()
    for chain in chains:
        if len(set(chain))!=len(chain):raise ValueError('Cyclic texture dictionary chain')
        for child,parent in zip(chain,chain[1:]):
            if child in children:raise ValueError('Multiple parents for texture dictionary')
            children.add(child);item=E.SubElement(relationships,'Item')
            E.SubElement(item,'parent').text=parent;E.SubElement(item,'child').text=child
    return root
