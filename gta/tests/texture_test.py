# SPDX-License-Identifier: Apache-2.0
"""Regression fixtures for sRGB DDS formats silently becoming GTA format zero."""
import importlib.util
import struct
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("normalize_dds", Path(__file__).resolve().parents[1] / "asset-tools/normalize_dds.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def dds(dxgi, pixels=bytes(range(16)), mips=1):
    header = bytearray(148)
    header[:4] = b"DDS "
    for offset, value in [(4,124),(12,4),(16,4),(28,mips),(76,32),(128,dxgi),(132,3),(140,1)]:
        struct.pack_into("<I", header, offset, value)
    header[84:88] = b"DX10"
    return bytes(header) + pixels


class TextureNormalization(unittest.TestCase):
    def test_srgb_bc1_and_bc7_preserve_pixel_data(self):
        for srgb, linear in [(72,71),(99,98)]:
            original = dds(srgb)
            result, changed = module.normalize_dds(original)
            self.assertTrue(changed)
            self.assertEqual(struct.unpack_from("<I",result,128)[0],linear)
            self.assertEqual(result[:128],original[:128])
            self.assertEqual(result[132:],original[132:])

    def test_normal_map_bc7_is_unchanged(self):
        original = dds(98)
        self.assertEqual(module.normalize_dds(original),(original,False))

    def test_unknown_dxgi_rejected_before_native_conversion(self):
        with self.assertRaisesRegex(ValueError,"no supported GTA"):
            module.normalize_dds(dds(97))  # Typeless BC7 cannot be guessed.

    def test_truncated_block_and_mip_tail_rejected(self):
        for original in [dds(99,b'\0'*15),dds(72,b'\0'*8,mips=2)]:
            with self.assertRaisesRegex(ValueError,"Truncated DDS mip data"):
                module.normalize_dds(original)

    def test_array_not_silently_flattened(self):
        original=bytearray(dds(99));struct.pack_into('<I',original,140,2)
        with self.assertRaisesRegex(ValueError,"single 2D"):
            module.normalize_dds(bytes(original))


if __name__ == '__main__': unittest.main()
