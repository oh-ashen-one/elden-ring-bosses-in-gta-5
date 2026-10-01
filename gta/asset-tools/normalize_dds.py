# SPDX-License-Identifier: Apache-2.0
"""Normalize DDS storage metadata for CodeWalker's Legacy texture importer.

The importer maps UNORM DXGI formats to GTA enums, but maps the equivalent
sRGB variants to zero. Both variants have the same compressed pixel storage.
Relabel the header only; preserve every source pixel and mip byte. GTA Legacy
uses its material/shader conventions rather than an sRGB TextureFormat enum.
"""
import struct

SRGB_TO_UNORM = {29: 28, 72: 71, 75: 74, 78: 77, 91: 87, 99: 98}
SUPPORTED_DXGI = {28, 61, 65, 71, 74, 77, 80, 83, 86, 87, 98}


def normalize_dds(data: bytes) -> tuple[bytes, bool]:
    if len(data) < 128 or data[:4] != b"DDS " or struct.unpack_from("<I", data, 4)[0] != 124:
        raise ValueError("Invalid or truncated DDS header")
    if struct.unpack_from("<I", data, 76)[0] != 32:
        raise ValueError("Invalid DDS pixel-format header")
    height, width = struct.unpack_from("<II", data, 12)
    if not 0 < width <= 16384 or not 0 < height <= 16384:
        raise ValueError("Invalid DDS dimensions")
    if data[84:88] != b"DX10":
        return data, False  # The native importer validates legacy DDS formats.
    if len(data) < 148:
        raise ValueError("Truncated DDS DX10 extension")
    dxgi, dimension, misc, array_size = struct.unpack_from("<4I", data, 128)
    if dimension != 3 or array_size != 1 or misc & 4:
        raise ValueError("Creature textures must be single 2D images, not arrays/cubemaps/volumes")
    normalized = SRGB_TO_UNORM.get(dxgi, dxgi)
    if normalized not in SUPPORTED_DXGI:
        raise ValueError(f"DXGI texture format {dxgi} has no supported GTA Legacy mapping")
    # Validate all mip payloads before packaging, including the 4x4 block tails.
    mips = max(1, struct.unpack_from("<I", data, 28)[0])
    if mips > max(width, height).bit_length():
        raise ValueError("DDS mip count exceeds texture dimensions")
    required = 0
    for level in range(mips):
        w, h = max(1, width >> level), max(1, height >> level)
        if normalized in {71, 74, 77, 80, 83, 98}:
            required += ((w + 3) // 4) * ((h + 3) // 4) * (8 if normalized in {71, 80} else 16)
        else:
            required += w * h * (1 if normalized in {61, 65} else 2 if normalized == 86 else 4)
    if len(data) - 148 < required:
        raise ValueError(f"Truncated DDS mip data: expected {required}, got {len(data) - 148}")
    if normalized == dxgi:
        return data, False
    result = bytearray(data)
    struct.pack_into("<I", result, 128, normalized)
    return bytes(result), True
