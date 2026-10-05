# SPDX-License-Identifier: Apache-2.0
"""Synthetic coverage for large skeletons and lossless texture partitioning."""
import sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as E
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]/'asset-tools'))
from compact_skin_palette import compact,identity
from geometry_fidelity import reject_inward
from correct_bind_heads import correct,source_axes
from rebuild_animation import TargetRig,matrix,world_matrices,Y_UP_TO_Z_UP
from texture_dictionaries import partition,parenting
from animation_conversion_test import drawable

class Fidelity(unittest.TestCase):
    def test_mirrored_flver_faces_must_not_be_reversed_twice(self):
        # Clockwise LH source triangle becomes outward RH simply by mirroring
        # Z. The old extra index swap made the visible outer face disappear.
        root=E.fromstring('<Drawable><Geometries><Item><VertexBuffer><Layout><Position/><Normal/></Layout><Data>0 0 0 0 1 0  1 0 0 0 1 0  0 0 -1 0 1 0</Data></VertexBuffer><IndexBuffer><Data>'+('0 1 2 '*20)+'</Data></IndexBuffer></Item></Geometries></Drawable>')
        self.assertEqual(reject_inward(root)['outward'],20)
        root.find('.//IndexBuffer/Data').text='0 2 1 '*20
        with self.assertRaisesRegex(ValueError,'inward faces'):reject_inward(root)

    def test_global_identity_mapping_keeps_the_same_weighted_joints(self):
        root=E.fromstring('<Drawable><Skeleton><Bones>'+('<Item/>'*5)+'</Bones></Skeleton><Geometries><Item><BoneIDs>4, 1</BoneIDs><VertexBuffer><Layout><BlendWeights/><BlendIndices/></Layout><Data>128 127 0 0 0 1 0 0</Data></VertexBuffer></Item></Geometries></Drawable>')
        identity(root);g=root.find('.//Geometries/Item');row=np.fromstring(g.findtext('VertexBuffer/Data'),sep=' ')
        self.assertEqual(row[4:6].tolist(),[4,1]);self.assertEqual(g.findtext('BoneIDs'),'0, 1, 2, 3, 4')
    def test_high_global_joint_indices_survive_byte_palette(self):
        root=E.fromstring('<Drawable><Geometries><Item><BoneIDs>'+','.join(map(str,range(305)))+'</BoneIDs><VertexBuffer><Layout><BlendWeights/><BlendIndices/></Layout><Data>128 127 0 0 302 4 0 0\n255 0 0 0 299 0 0 0</Data></VertexBuffer></Item></Geometries></Drawable>')
        report=compact(root);g=root.find('.//Geometries/Item');palette=list(map(int,g.findtext('BoneIDs').split(',')))
        rows=np.fromstring(g.findtext('VertexBuffer/Data'),sep=' ').reshape(-1,8)
        self.assertEqual(report[0]['new_palette'],3)
        self.assertEqual([palette[int(x)] for x in rows[0,4:6]],[302,4])
        self.assertEqual(palette[int(rows[1,4])],299)
        self.assertLess(rows[:,4:].max(),256)

    def test_bind_correction_preserves_axes_and_rejects_large_errors(self):
        source=SimpleNamespace(names={'Joint':0},rest=np.array([np.eye(4)]))
        shifted=Y_UP_TO_Z_UP.copy();shifted[0,3]=.007
        tree=drawable([shifted],[-1],['Joint']);rotation=E.tostring(tree.find('Skeleton/Bones/Item/Rotation'))
        with self.assertRaisesRegex(ValueError,'bind joints'):TargetRig(tree,source)
        correct(tree,source);TargetRig(tree,source)
        self.assertEqual(rotation,E.tostring(tree.find('Skeleton/Bones/Item/Rotation')))
        shifted[0,3]=.5
        with self.assertRaisesRegex(ValueError,'Unexpected bind'):correct(drawable([shifted],[-1],['Joint']),source)

    def test_original_axes_preserve_nonuniform_animated_skin_matrix(self):
        from scipy.spatial.transform import Rotation
        rest=matrix([0,1,0],Rotation.from_euler('z',30,degrees=True).as_quat(),[1,1,1])
        source=SimpleNamespace(names={'Joint':0},rest=np.array([rest]))
        roll=matrix([0,0,0],Rotation.from_euler('y',37,degrees=True).as_quat(),[1,1,1])
        tree=drawable([Y_UP_TO_Z_UP@rest@roll],[-1],['Joint']);source_axes(tree,source)
        rig=TargetRig(tree,source)
        animated=matrix([1,2,0],Rotation.from_euler('z',60,degrees=True).as_quat(),[1.2,.8,1])
        actual=world_matrices([matrix(*p) for p in rig.pose(np.array([animated]))],rig.parents)[0]@np.linalg.inv(rig.rest[0])
        expected=Y_UP_TO_Z_UP@animated@np.linalg.inv(rest)@np.linalg.inv(Y_UP_TO_Z_UP)
        np.testing.assert_allclose(actual,expected,atol=1e-8)

    def test_texture_partition_preserves_whole_payloads_and_parent_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);root=E.Element('TextureDictionary')
            for i,size in enumerate([9,7,4,2]):
                item=E.SubElement(root,'Item');E.SubElement(item,'Name').text=str(i);E.SubElement(item,'FileName').text=str(i)+'.dds'
                (folder/(str(i)+'.dds')).write_bytes(bytes([i])*size)
            before={p.name:p.read_bytes() for p in folder.iterdir()};groups,sizes=partition(root,folder,10)
            self.assertEqual(sorted(x.findtext('Name') for group in groups for x in group),['0','1','2','3'])
            self.assertTrue(all(s<=10 for s in sizes));self.assertEqual(before,{p.name:p.read_bytes() for p in folder.iterdir()})
            meta=parenting([['boss','boss_t01','boss_t02']]);self.assertEqual([(x.findtext('child'),x.findtext('parent')) for x in meta.findall('txdRelationships/Item')],[('boss','boss_t01'),('boss_t01','boss_t02')])
            with self.assertRaises(ValueError):parenting([['a','b','a']])

if __name__=='__main__':unittest.main()
