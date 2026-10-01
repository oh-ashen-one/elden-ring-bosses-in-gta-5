#!/usr/bin/env python3
"""Synthetic layout/mip/normal regressions; no retail fixtures or renderer."""
import importlib.util
import sys
import tempfile
import unittest
import struct
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('visuals',Path(__file__).parents[1]/'asset-tools/upgrade_visuals.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class VisualTests(unittest.TestCase):
    def test_packed_normal_reconstruction(self):
        source=np.array([[[128,128,12,0],[200,80,20,10]]],dtype=np.uint8)
        rgb=v.normal_pixels(source)
        self.assertGreater(rgb[0,0,2],250)
        self.assertTrue(np.all(rgb[:,:,3]==255))
        lengths=np.linalg.norm(rgb[:,:,:3].astype(float)/127.5-1,axis=2)
        np.testing.assert_allclose(lengths,1,atol=0.012)
        self.assertEqual(source[0,0,2],12) # originals untouched

    def test_mips_keep_native_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.dds'
            dimensions=v.write_dds(path,np.full((8,16,4),200,dtype=np.uint8))
            self.assertEqual(dimensions,(16,8,5))
            data=path.read_bytes()
            self.assertEqual(struct.unpack_from('<I',data,28)[0],5)
            self.assertEqual(len(data),128+4*(128+32+8+2+1))
            self.assertEqual(v.read_image(path).shape,(8,16,4))
            with self.assertRaises(FileExistsError):v.write_dds(path,np.zeros((1,1,4),dtype=np.uint8))

    def test_tangent_basis_handles_mirrored_and_degenerate_uvs(self):
        p=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
        n=np.tile([0.,0.,1.],(3,1));indices=np.array([0,1,2])
        for uv in [np.array([[0.,0.],[1.,0.],[0.,1.]]),np.array([[0.,0.],[-1.,0.],[0.,1.]]),np.zeros((3,2))]:
            t=v.tangents(p,n,uv,indices)
            self.assertTrue(np.isfinite(t).all())
            np.testing.assert_allclose(np.linalg.norm(t[:,:3],axis=1),1)
            np.testing.assert_allclose((t[:,:3]*n).sum(axis=1),0)
        self.assertLess(v.tangents(p,n,np.array([[0.,0.],[-1.,0.],[0.,1.]]),indices)[0,3],0)

if __name__=='__main__':unittest.main()
