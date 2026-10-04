#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independently inspect an unencrypted private RPF7, including actual DEFLATE.

Does not use CodeWalker or launch GTA. The optional per-resource budget is our
preview's review limit, NOT a claimed universal GTA engine limit.
"""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

MAX_BYTES=256*1024*1024

def page_sizes(flags):
    base=512<<(flags&15)
    return [base*weight for shift,mask,weight in ((27,1,1),(26,1,2),(25,1,4),(24,1,8),
            (17,127,16),(11,63,32),(7,15,64),(5,3,128),(4,1,256)) for _ in range((flags>>shift)&mask)]

def inflate(data,expected):
    if not 0<expected<=MAX_BYTES:raise ValueError('Unbounded inflated size')
    decoder=zlib.decompressobj(-15)
    result=decoder.decompress(data,expected+1)
    if not decoder.eof or decoder.unconsumed_tail or decoder.unused_data or len(result)!=expected:
        raise ValueError('DEFLATE stream is incomplete, trailing, or disagrees with declared memory size')
    return result

def audit(data,label='dlc.rpf',depth=0):
    if depth>4 or len(data)<16 or len(data)>MAX_BYTES:raise ValueError('Invalid archive size/depth')
    magic,count,names_size,encryption=struct.unpack_from('<4I',data)
    if magic!=0x52504637 or encryption not in (0,0x4e45504f):raise ValueError('Only unencrypted RPF7 is supported')
    end=16+count*16+names_size
    if not 1<=count<=10000 or end>len(data):raise ValueError('Invalid archive table')
    names=data[16+16*count:end];rows=[];ranges=[]
    for i in range(count):
        entry=data[16+i*16:32+i*16];a,b,c,d=struct.unpack('<4I',entry)
        if b==0x7fffff00:
            if c+d>count:raise ValueError('Directory outside table')
            continue
        no=int.from_bytes(entry[:2],'little')
        if no>=len(names) or b'\0' not in names[no:]:raise ValueError('Invalid name offset')
        name=names[no:].split(b'\0',1)[0].decode('utf-8')
        if not name or any(x in name for x in ('/','\\','..')):raise ValueError('Unsafe member name')
        size=int.from_bytes(entry[2:5],'little');offset=(int.from_bytes(entry[5:8],'little')&0x7fffff)*512
        resource=bool(b&0x80000000)
        if resource and size==0xffffff:
            h=data[offset:offset+16]
            if len(h)!=16:raise ValueError('Missing extended resource header')
            size=h[7]|h[14]<<8|h[5]<<16|h[2]<<24
        stored=size if resource or size else c
        if offset<end or stored<=0 or offset+stored>len(data):raise ValueError('Member outside archive')
        if any(offset<hi and offset+stored>lo for lo,hi in ranges):raise ValueError('Overlapping archive members')
        ranges.append((offset,offset+stored));payload=data[offset:offset+stored]
        if resource:
            if size<17:raise ValueError('Resource lacks compressed payload')
            pages=page_sizes(c)+page_sizes(d);expected=sum(pages)
            raw=inflate(payload[16:],expected)
            rows.append({'file':label+'/'+name,'stored_bytes':stored,'inflated_bytes':expected,
                         'largest_page_bytes':max(pages),'version':((c>>28)<<4)|(d>>28),
                         'extended_size_header':stored>=0xffffff,'deflate_verified':True,
                         'inflated_sha256':hashlib.sha256(raw).hexdigest()})
        else:
            if d:raise ValueError('Encrypted binary member unsupported')
            raw=inflate(payload,c) if size else payload
            if name.lower().endswith('.rpf'):rows.extend(audit(raw,label+'/'+name,depth+1))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path)
    p.add_argument('--out',type=Path);p.add_argument('--max-resource-mib',type=float)
    a=p.parse_args();rows=audit(a.archive.read_bytes());over=[]
    if a.max_resource_mib is not None:over=[r['file'] for r in rows if r['inflated_bytes']>a.max_resource_mib*1024*1024]
    report={'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'resources':rows,
            'review_budget_mib':a.max_resource_mib,'over_review_budget':over,'gameplay_verified':False}
    if a.out:
        with a.out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))
    raise SystemExit(2 if over else 0)
