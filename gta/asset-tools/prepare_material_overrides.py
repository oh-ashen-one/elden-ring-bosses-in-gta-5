#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bake a documented approximation of ER's procedural hair tint for GTA.

Uses an original character hair diffuse and the original material's tint.
The source files stay unchanged; output is private derived game content.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path, PureWindowsPath
import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    materials = json.loads((root / "materials-with-params.json").read_text())
    source = root / "textures/c2120/c2120_hair2_a.dds"
    image = np.asarray(Image.open(source).convert("RGBA")).copy()
    overrides = {}
    for name, material in materials.items():
        key = PureWindowsPath(name).stem.lower()
        if "c2120" not in key or "hair_long" not in key: continue
        params = {p["name"]: p["value"] for p in material["params"]}
        tint = params.get("P_ChrCustomize__Hair__snp_0_color_4")
        if not tint: continue
        gain = np.array(tint[:3]) * np.array(params.get("g_DiffuseMapColor", [1,1,1]))
        pixels = image.copy()
        pixels[:,:,:3] = np.rint(np.clip(pixels[:,:,:3] * gain, 0, 255)).astype(np.uint8)
        height, width = pixels.shape[:2]
        # Standard uncompressed RGBA8 DDS. No vendor compressor is bundled.
        header = [124, 0x100f, height, width, width*4, 0, 1, *([0]*11),
                  32, 0x41, 0, 32, 0xff, 0xff00, 0xff0000, 0xff000000,
                  0x1000, 0, 0, 0, 0]
        data = b"DDS " + struct.pack("<31I", *header) + pixels.tobytes()
        filename = "ergt_" + key.replace("[", "_").replace("]", "_") + "_tinted.dds"
        output = root / "textures/common" / filename
        if output.exists() and output.read_bytes() != data: raise ValueError("Material bake output changed")
        if not output.exists(): output.write_bytes(data)
        overrides[key] = {"base": filename,
                          "note": "Approximation: original c2120 hair diffuse/opacity plus HairLong material tint; UV appearance unverified",
                          "source_texture": source.name, "source_material": name,
                          "tint_gain": gain.tolist(), "sha256": hashlib.sha256(data).hexdigest()}
    (root / "material-overrides.json").write_text(json.dumps(overrides, indent=2) + "\n")
    print(f"Prepared {len(overrides)} documented material approximations")


if __name__ == "__main__": main()
