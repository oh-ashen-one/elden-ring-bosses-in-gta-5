# SPDX-License-Identifier: GPL-3.0-or-later
"""Narrow compatibility repair for the pinned soulstruct-havok 1.5.0 reader.

ThreeComp48 contains three int16 values. That release mistakenly calls the
single-value API for '3h'. Keep its own quaternion decoder and all other paths.
"""
from importlib.metadata import version

def install():
    from soulstruct.havok import spline_compression as spline
    if version('soulstruct-havok')!='1.5.0':return
    previous=spline.unpack_quantized_quaternion
    if getattr(previous,'ergt_48_fix',False):return
    def read(reader,kind):
        if kind==spline.RotationQuantizationType.ThreeComp48:
            return spline.Quaternion.decode_ThreeComp48(*reader.unpack('3h'))
        return previous(reader,kind)
    read.ergt_48_fix=True
    spline.unpack_quantized_quaternion=read
