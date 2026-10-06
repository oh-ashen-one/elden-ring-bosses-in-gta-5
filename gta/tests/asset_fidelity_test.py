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
from split_large_rig import partition as partition_rig
from scale_roster import scale_drawable,scale_animation
from fur_material import bake
from cutout_fidelity import remap_alpha
from hair_shadow import bake_shadow
from material_fidelity import fields,sample
from correct_bind_heads import correct,source_axes
from rebuild_animation import TargetRig,matrix,world_matrices,Y_UP_TO_Z_UP
from texture_dictionaries import partition,parenting
from animation_conversion_test import drawable

class Fidelity(unittest.TestCase):
    def test_authored_hair_shadow_uses_secondary_uv_and_preserves_strand_alpha(self):
        g=E.fromstring('<Item><VertexBuffer><Layout><Position/><TexCoord0/><TexCoord1/></Layout><Data>0 0 0 0 0 .01 .01\n1 0 0 1 0 .01 .99\n0 1 0 0 1 .99 .01</Data></VertexBuffer><IndexBuffer><Data>0 1 2</Data></IndexBuffer></Item>')
        p=np.full((16,16,4),[190,98,83,140],np.uint8);mask=np.full((16,16,4),255,np.uint8);mask[:8,:,:3]=40
        result,report=bake_shadow([g],p,mask)
        np.testing.assert_array_equal(result[:,:,3],p[:,:,3]);self.assertTrue(report['alpha_unchanged'])
        self.assertLess(int(result[0,2,0]),int(result[0,12,0]));self.assertEqual(int(result[0,12,0]),190)

    def test_cutout_mapping_preserves_every_source_accept_reject_decision_and_rgb(self):
        p=np.zeros((1,256,4),np.uint8);p[0,:,3]=np.arange(256);p[:,:,:3]=[71,126,193]
        for threshold in [45,70,85,128,140,200]:
            out=remap_alpha(p,threshold)
            np.testing.assert_array_equal(out[:,:,3]>=128,p[:,:,3]>=threshold)
            np.testing.assert_array_equal(out[:,:,:3],p[:,:,:3])
            self.assertEqual(out[0,0,3],0);self.assertEqual(out[0,-1,3],255)

    def test_large_rig_split_preserves_faces_and_named_weight_associations(self):
        root=E.Element('Drawable');bones=E.SubElement(E.SubElement(root,'Skeleton'),'Bones')
        for i in range(5):
            b=E.SubElement(bones,'Item');E.SubElement(b,'Name').text='bone'+str(i)
            for tag,v in [('Tag',100+i),('Index',i),('ParentIndex',-1 if i==0 else 0),('SiblingIndex',-1)]:E.SubElement(b,tag,value=str(v))
            E.SubElement(b,'Translation',x='0',y='0',z='0');E.SubElement(b,'Rotation',x='0',y='0',z='0',w='1');E.SubElement(b,'Scale',x='1',y='1',z='1')
        gs=E.SubElement(E.SubElement(E.SubElement(root,'DrawableModelsHigh'),'Item'),'Geometries')
        for pair in [(1,2),(3,4)]:
            g=E.SubElement(gs,'Item');E.SubElement(g,'BoneIDs').text=','.join(map(str,pair));vb=E.SubElement(g,'VertexBuffer');layout=E.SubElement(vb,'Layout')
            for n in ['Position','BlendWeights','BlendIndices','Normal']:E.SubElement(layout,n)
            E.SubElement(vb,'Data').text='0 0 0 255 0 0 0 0 0 0 0 0 0 1\n1 0 0 255 0 0 0 1 0 0 0 0 0 1\n0 1 0 255 0 0 0 0 0 0 0 0 0 1'
            E.SubElement(E.SubElement(g,'IndexBuffer'),'Data').text='0 1 2'
        parts=partition_rig(root,3);self.assertEqual(len(parts),2);self.assertNotEqual(parts[0][1]['skeleton_cache_ids'],parts[1][1]['skeleton_cache_ids']);self.assertEqual(sum(r['triangles'] for _,r in parts),2)
        for (part,report),expected in zip(parts,[['bone1','bone2','bone1'],['bone3','bone4','bone3']]):
            names=[b.findtext('Name') for b in part.findall('Skeleton/Bones/Item')];g=part.find('.//Geometries/Item');f=fields(g)
            self.assertEqual([names[int(i)] for i in f['BlendIndices'][:,0]],expected)
        with self.assertRaises(ValueError):partition_rig(root,2)

    def test_building_scale_changes_positions_clips_and_collision_not_uv_or_rotation(self):
        root=E.fromstring('<Drawable><BoundingSphereRadius value="3"/><Skeleton><Bones><Item><Translation x="1" y="2" z="3"/></Item></Bones></Skeleton><Geometries><Item><VertexBuffer><Layout><Position/><TexCoord0/></Layout><Data>1 2 3 .25 .75</Data></VertexBuffer></Item></Geometries><Bounds><BoxMin x="-1" y="-1" z="0"/><BoxMax x="1" y="1" z="23"/><Volume value="92"/><Inertia x="1" y="2" z="3"/></Bounds></Drawable>')
        scale_drawable(root,2.6);data=np.fromstring(root.findtext('.//VertexBuffer/Data'),sep=' ')
        np.testing.assert_allclose(data,[2.6,5.2,7.8,.25,.75]);self.assertAlmostEqual(float(root.find('Bounds/BoxMax').get('z')),59.8)
        anim=E.fromstring('<ClipDictionary><Animations><Item><BoneIds><Item><Track value="0"/></Item><Item><Track value="1"/></Item></BoneIds><Sequences><Item><SequenceData><Item><Channels><Item><Type value="StaticVector3"/><Value x="1" y="2" z="3"/></Item></Channels></Item><Item><Channels><Item><Type value="StaticQuaternion"/><Value x="0" y="0" z="0" w="1"/></Item></Channels></Item></SequenceData></Item></Sequences></Item></Animations></ClipDictionary>')
        rotation=E.tostring(anim.findall('.//SequenceData/Item')[1]);scale_animation(anim,2.6)
        self.assertEqual(rotation,E.tostring(anim.findall('.//SequenceData/Item')[1]));self.assertAlmostEqual(float(anim.find('.//SequenceData/Item/Channels/Item/Value').get('y')),5.2)

    def test_fur_uses_authored_uv2_transparency_without_changing_geometry(self):
        g=E.fromstring('<Item><VertexBuffer><Layout><Position/><Normal/><TexCoord0/><TexCoord2/></Layout><Data>0 0 0 0 0 1 0 0 0 0\n1 0 0 0 0 1 1 0 1 0\n0 1 0 0 0 1 0 1 0 1</Data></VertexBuffer><IndexBuffer><Data>0 1 2</Data></IndexBuffer></Item>')
        original=E.tostring(g);base=np.full((8,8,4),[180,40,20,255],np.uint8);strand=np.full((8,8,4),255,np.uint8);strand[:4,:,3]=0
        normal=np.full((8,8,4),[128,128,128,255],np.uint8)
        result,_,report=bake([g],base,strand,normal,fields,sample)
        self.assertEqual(original,E.tostring(g));self.assertTrue(report['authored_uv2_strands']);self.assertGreater(result[:,:,3].max(),128);self.assertEqual(result[:,:,3].min(),0)
        np.testing.assert_array_equal(result[6,0,:3],base[6,0,:3])
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
