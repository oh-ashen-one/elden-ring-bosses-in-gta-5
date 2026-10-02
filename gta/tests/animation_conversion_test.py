#!/usr/bin/env python3
"""Synthetic rig-space tests; no retail assets, Blender, game or renderer."""
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as E
import numpy as np
from scipy.spatial.transform import Rotation

spec=importlib.util.spec_from_file_location('repair',Path(__file__).parents[1]/'asset-tools/rebuild_animation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def drawable(matrices,parents,names):
    root=E.Element('Drawable');skeleton=E.SubElement(root,'Skeleton');bones=E.SubElement(skeleton,'Bones')
    for i,(matrix,parent,name) in enumerate(zip(matrices,parents,names)):
        b=E.SubElement(bones,'Item');E.SubElement(b,'Name').text=name
        E.SubElement(b,'Tag',value=str(i));E.SubElement(b,'ParentIndex',value=str(parent))
        t,q,s=m.split_matrix(matrix)
        for key,values,axes in [('Translation',t,'xyz'),('Rotation',q,'xyzw'),('Scale',s,'xyz')]:
            E.SubElement(b,key,**{a:str(v) for a,v in zip(axes,values)})
    return root


class AnimationConversion(unittest.TestCase):
    def test_rotated_bind_axes_preserve_skin_motion(self):
        # Source joint rests at +Y. Target rests at +Z and rolls its bone axes.
        source_rest=np.eye(4);source_rest[1,3]=1
        source=SimpleNamespace(names={'Joint':0},rest=np.array([source_rest]))
        roll=np.eye(4);roll[:3,:3]=Rotation.from_euler('y',60,degrees=True).as_matrix()
        target_world=m.Y_UP_TO_Z_UP@source_rest@roll
        rig=m.TargetRig(drawable([m.Y_UP_TO_Z_UP,np.linalg.inv(m.Y_UP_TO_Z_UP)@target_world],[-1,0],['ERGT_Root','Joint']),source)
        animated=np.eye(4);animated[:3,:3]=Rotation.from_euler('z',90,degrees=True).as_matrix();animated[:3,3]=[2,1,0]
        local=rig.pose(np.array([animated]));actual_world=m.world_matrices([m.matrix(*x) for x in local],rig.parents)
        skin=actual_world[1]@np.linalg.inv(rig.rest[1])
        # A vertex one unit along source +X ends at source [2,2,0], GTA [2,0,2].
        vertex=m.Y_UP_TO_Z_UP@np.array([1.,1,0,1])
        np.testing.assert_allclose((skin@vertex)[:3],[2,0,2],atol=1e-8)

    def test_parent_motion_preserved_across_different_rest_axes(self):
        root=np.eye(4);tip=np.eye(4);tip[1,3]=2
        source=SimpleNamespace(names={'Root':0,'Tip':1},rest=np.array([root,tip]))
        roll=np.eye(4);roll[:3,:3]=Rotation.from_euler('x',35,degrees=True).as_matrix()
        worlds=[m.Y_UP_TO_Z_UP,m.Y_UP_TO_Z_UP@root@roll,m.Y_UP_TO_Z_UP@tip]
        rig=m.TargetRig(drawable([worlds[0],np.linalg.inv(worlds[0])@worlds[1],np.linalg.inv(worlds[1])@worlds[2]],[-1,0,1],['ERGT_Root','Root','Tip']),source)
        rotation=np.eye(4);rotation[:3,:3]=Rotation.from_euler('z',90,degrees=True).as_matrix()
        source_animated=np.array([rotation,rotation@tip])
        transformed=m.world_matrices([m.matrix(*x) for x in rig.pose(source_animated)],rig.parents)
        np.testing.assert_allclose(transformed[2][:3,3],[-2,0,0],atol=1e-8)

    def test_mismatched_bind_positions_are_rejected(self):
        source=SimpleNamespace(names={'Root':0},rest=np.array([np.eye(4)]))
        shifted=np.eye(4);shifted[0,3]=10
        with self.assertRaisesRegex(ValueError,'bind joints differ'):
            m.TargetRig(drawable([shifted],[-1],['Root']),source)

    def test_cycles_shear_and_singular_matrices_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'cycle'):m.world_matrices([np.eye(4),np.eye(4)],[1,0])
        value=np.eye(4);value[0,1]=1
        with self.assertRaisesRegex(ValueError,'Sheared'):m.split_matrix(value)
        value=np.eye(4);value[0,0]=0
        with self.assertRaisesRegex(ValueError,'Singular'):m.split_matrix(value)

if __name__=='__main__':unittest.main()
