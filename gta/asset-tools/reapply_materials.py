# SPDX-License-Identifier: Apache-2.0
"""Apply new shader maps to an already corrected private rig/pose conversion."""
import argparse,copy,json,shutil
from pathlib import Path
from xml.etree import ElementTree as E

def apply(converted,materials,out,roster):
    if out.exists():raise ValueError('Use new output')
    out.mkdir(parents=True)
    for b in roster:
        c,n=b['character'],b['model'];src=converted/c;mat=materials/c;dst=out/c;dst.mkdir()
        receipt=json.loads((src/(n+'.conversion.json')).read_text());new=json.loads((mat/(n+'.conversion.json')).read_text())
        if receipt['shader_source_paths']!=new['shader_source_paths']:raise ValueError('Material/geometry order changed')
        doc=E.parse(src/(n+'.ydr.xml'));shaders=E.parse(mat/(n+'.ydr.xml')).find('ShaderGroup')
        old=doc.find('ShaderGroup')
        if len(old.findall('Shaders/Item'))!=len(shaders.findall('Shaders/Item')):raise ValueError('Shader count changed')
        index=list(doc.getroot()).index(old);doc.getroot().remove(old);doc.getroot().insert(index,copy.deepcopy(shaders))
        E.indent(doc);doc.write(dst/(n+'.ydr.xml'),encoding='utf-8',xml_declaration=True)
        shutil.copytree(mat/n,dst/n);shutil.copy2(src/(n+'_anims.ycd.xml'),dst/(n+'_anims.ycd.xml'))
        receipt['material_fidelity']=new['material_fidelity'];(dst/(n+'.conversion.json')).write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('converted','materials','out','roster'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();apply(a.converted,a.materials,a.out,json.loads(a.roster.read_text())['bosses'])
