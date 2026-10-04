# SPDX-License-Identifier: Apache-2.0
"""Independent archive witnesses, including extended resource sizes."""
import importlib.util
import random
import struct
import unittest
import zlib
from pathlib import Path
s=importlib.util.spec_from_file_location('audit',Path(__file__).parents[1]/'asset-tools/rpf_audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture(raw,shift=0):
    flags=0xa8000000|shift;gfx=0x50000000
    data=bytearray(struct.pack('<4I',0x37435352,165,flags,gfx)+zlib.compress(raw)[2:-4])
    size=len(data);packed=min(size,0xffffff)
    if packed==0xffffff:
        for index,offset in [(7,0),(14,8),(5,16),(2,24)]:data[index]=(size>>offset)&255
    names=b'\0fixture.ydr\0';head=struct.pack('<4I',0x52504637,2,len(names),0x4e45504f)
    root=struct.pack('<4I',0,0x7fffff00,1,1)
    entry=struct.pack('<H',1)+packed.to_bytes(3,'little')+(0x800001).to_bytes(3,'little')+struct.pack('<II',flags,gfx)
    return (head+root+entry+names).ljust(512,b'\0')+data

class ArchiveAudit(unittest.TestCase):
    def test_valid_resource_and_truncated_archive(self):
        raw=bytes(range(256))*2;b=fixture(raw);r=m.audit(b)[0]
        self.assertEqual(r['inflated_bytes'],512);self.assertTrue(r['deflate_verified']);self.assertEqual(r['version'],165)
        with self.assertRaisesRegex(ValueError,'outside archive'):m.audit(b[:-1])
    def test_declared_size_is_not_evidence_of_valid_inflate(self):
        b=fixture(b'X'*1024) # entry advertises only 512
        with self.assertRaisesRegex(ValueError,'DEFLATE'):m.audit(b)
    def test_reject_trailing_and_corrupt_compression(self):
        raw=b'X'*512;compressed=zlib.compress(raw)[2:-4]
        with self.assertRaises(ValueError):m.inflate(compressed+b'junk',512)
        with self.assertRaises((ValueError,zlib.error)):m.inflate(b'\xff'*16,512)
    def test_large_resource_header_is_decoded(self):
        raw=random.Random(7).randbytes(16*1024*1024)
        row=m.audit(fixture(raw,15))[0]
        self.assertTrue(row['extended_size_header']);self.assertEqual(row['inflated_bytes'],len(raw))
        self.assertEqual(row['largest_page_bytes'],len(raw))

if __name__=='__main__':unittest.main()
