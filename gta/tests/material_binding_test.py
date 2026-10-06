# SPDX-License-Identifier: Apache-2.0
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

path=Path(__file__).parents[1]/'asset-tools/audit_material_bindings.py'
spec=importlib.util.spec_from_file_location('bindings',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class BindingAudit(unittest.TestCase):
    def fixture(self,root):
        folder=root/'character';(folder/'boss').mkdir(parents=True)
        data=bytearray(128);data[:4]=b'DDS ';struct.pack_into('<II',data,12,4,4);struct.pack_into('<I',data,28,3)
        (folder/'boss/colour.dds').write_bytes(data)
        (folder/'boss.ydr.xml').write_text('''<Drawable><ShaderGroup><TextureDictionary><Item><Name>colour</Name><FileName>colour.dds</FileName></Item></TextureDictionary><Shaders><Item><FileName>normal_spec.sps</FileName><Parameters><Item name="DiffuseSampler" type="Texture"><Name>colour</Name></Item><Item name="specularIntensityMult" type="Vector" x="0.35" y="0" z="0" w="0" /></Parameters></Item></Shaders></ShaderGroup></Drawable>''')
        return {'dictionaries':[{'name':'boss','textures':[]},{'name':'boss_t01','textures':[{'name':'colour','width':4,'height':4,'mips':3}]}],
            'archetypes':[{'model_hash':m.joaat('boss'),'texture_dictionary_hash':m.joaat('boss')}],
            'drawables':[{'name':'boss','shaders':[{'file_hash':m.joaat('normal_spec.sps'),'parameters':[
                {'name_hash':m.joaat('DiffuseSampler'),'type':0,'texture':'colour'},
                {'name_hash':m.joaat('specularIntensityMult'),'type':1,'vector':[.35,0,0,0]}]}]}]}
    def test_native_parent_chain_and_shader_parameters(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=self.fixture(root)
            meta=b'<CMapParentTxds><txdRelationships><Item><child>boss</child><parent>boss_t01</parent></Item></txdRelationships></CMapParentTxds>'
            with patch.object(m,'binary_members',return_value=[('gtxd.meta',meta)]):
                self.assertTrue(m.audit(data,root,b'private fixture')['ok'])
                data['drawables'][0]['shaders'][0]['parameters'][0]['texture']='missing'
                self.assertTrue(any('unreachable' in e for e in m.audit(data,root,b'x')['issues']))
                data['drawables'][0]['shaders'][0]['parameters'][0]['texture']='colour'
                data['drawables'][0]['shaders'][0]['parameters'][1]['vector'][0]=5
                self.assertTrue(any('parameter changed' in e for e in m.audit(data,root,b'x')['issues']))
    def test_missing_parent_rejects_unreachable_texture_elsewhere(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=self.fixture(root)
            with patch.object(m,'binary_members',return_value=[('gtxd.meta',b'<CMapParentTxds><txdRelationships /></CMapParentTxds>')]):
                self.assertFalse(m.audit(data,root,b'x')['ok'])

if __name__=='__main__':unittest.main()
