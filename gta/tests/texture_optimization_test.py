# SPDX-License-Identifier: Apache-2.0
import io
import importlib.util
import struct
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).parents[1]/'asset-tools'))
from optimize_textures import encode,quality

class TextureEncoding(unittest.TestCase):
    def test_rectangular_and_small_block_mips(self):
        for width,height in [(16,8),(4,4),(1,1),(1,8)]:
            source=np.full((height,width,4),128,dtype=np.uint8);source[:,:,3]=255
            data,levels=encode(source)
            expected=sum(((max(1,width>>i)+3)//4)*((max(1,height>>i)+3)//4)*16 for i in range(levels))
            self.assertEqual(len(data),128+expected);self.assertEqual(data[84:88],b'DXT5')
            self.assertEqual(struct.unpack_from('<I',data,28)[0],max(width,height).bit_length())
            self.assertEqual(Image.open(io.BytesIO(data)).size,(width,height))
            self.assertTrue(quality(source,data,False)['dimensions_preserved'])
    def test_normal_direction_and_cutout_coverage(self):
        pixels=np.zeros((8,8,4),dtype=np.uint8);pixels[:,:,:]=[128,128,255,255]
        data,_=encode(pixels,True);q=quality(pixels,data,True)
        self.assertLess(q['normal_angle_p99_degrees'],5)
        pixels[:4,:,3]=0;data,_=encode(pixels)
        self.assertEqual(quality(pixels,data,False)['alpha_128_coverage_change'],0)
    @unittest.skipUnless(importlib.util.find_spec('ispc_texcomp'),'Pinned optional BC7 encoder required')
    def test_bc7_rectangular_and_tiny_mips(self):
        from normalize_dds import normalize_dds
        for width,height in [(16,8),(1,1),(1,8)]:
            pixels=np.full((height,width,4),128,dtype=np.uint8);pixels[:,:,3]=255
            data,levels=encode(pixels,codec='BC7');checked,changed=normalize_dds(data)
            self.assertEqual(data,checked);self.assertFalse(changed)
            self.assertEqual(data[84:88],b'DX10');self.assertEqual(struct.unpack_from('<I',data,128)[0],98)
            self.assertEqual(Image.open(io.BytesIO(data)).size,(width,height))
            self.assertEqual(struct.unpack_from('<I',data,28)[0],levels)

if __name__=='__main__':unittest.main()
