#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Selectively extract owned ER characters without changing the game installation.

Windows CNG raw-RSA is unavailable in our CrossOver build, so the small archive
header is decoded on macOS. The standalone C helper reads the paired BDT and
uses the owned game's Oodle DLL. No game executable is patched or launched.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_public_key


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def windows_path(path):
    return "Z:" + str(path.resolve()).replace("/", "\\")


def decode_header(source, public_key, output):
    source_sha = digest(source)
    receipt = output.with_suffix(".json")
    if output.exists():
        if not receipt.exists():
            raise ValueError(f"Untracked existing header: {output}")
        recorded = json.loads(receipt.read_text())
        if recorded["source_sha256"] != source_sha or recorded["output_sha256"] != digest(output):
            raise ValueError("Archive changed or cached header was modified; choose a fresh output directory")
        return
    numbers = load_pem_public_key(public_key.read_bytes()).public_numbers()
    raw = source.read_bytes()
    if len(raw) % 256:
        raise ValueError("Invalid RSA block alignment")
    # BHD5's raw 2048-bit RSA blocks encode exactly 255 bytes each, including
    # leading zero bytes. This is the file format's public-key operation.
    plain = b"".join(pow(int.from_bytes(raw[i:i+256], "big"), numbers.e, numbers.n)
                     .to_bytes(255, "big") for i in range(0, len(raw), 256))
    if plain[:4] != b"BHD5":
        raise ValueError("Decoded header is not BHD5")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(plain)
    receipt.write_text(json.dumps({"source_sha256": source_sha, "output_sha256": digest(output)}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path, help="Owned ELDEN RING/Game directory")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--keys", required=True, type=Path, help="Pinned BinderKeys/EldenRing_PC directory")
    parser.add_argument("--helper", required=True, type=Path)
    parser.add_argument("--wine", type=Path, default=Path.home() / "Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine")
    parser.add_argument("--bottle", default="ERGTA-Tools")
    parser.add_argument("--characters", nargs="+", default=["c2120", "c3181", "c2270"])
    args = parser.parse_args()
    game, output = args.game.resolve(), args.out.resolve()
    if output == game or output.is_relative_to(game) or game.is_relative_to(output):
        raise ValueError("Output must be separate from the original game installation")
    for character in args.characters:
        if not re.fullmatch(r"c[0-9]{4}", character):
            raise ValueError(f"Invalid character ID: {character}")
    required = [game / "Data3.bhd", game / "Data3.bdt", game / "oo2core_6_win64.dll", args.helper]
    if not all(p.is_file() for p in required):
        raise ValueError("Missing game data, owned Oodle DLL, or compiled extraction helper")
    output.mkdir(parents=True, exist_ok=True)
    header = output / "headers/Data3.bhd"
    key = args.keys / "Key/Data3.pem"
    decode_header(game / "Data3.bhd", key, header)
    dictionary = (args.keys / "Hash/Data3.txt").read_text().splitlines()
    paths = sorted({p.strip() for p in dictionary if any(
        re.fullmatch(r"/chr/" + c + r"(?:_div[0-9]+)?\.(?:chr|ani)bnd\.dcx", p.strip())
        or p.strip() == f"/chr/{c}_h.texbnd.dcx" for c in args.characters)})
    if not paths:
        raise ValueError("No matching character files in the pinned dictionary")
    manifest_file = output / "extraction-manifest.json"
    manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {
        "schema_version": 1, "gameplay_verified": False,
        "source_archive": "Data3", "source_header_sha256": digest(game / "Data3.bhd"),
        "source_bdt_size": (game / "Data3.bdt").stat().st_size,
        "files": {},
    }
    if manifest["source_header_sha256"] != digest(game / "Data3.bhd"):
        raise ValueError("Game archive changed since prior extraction")
    for archive_path in paths:
        name = Path(archive_path).name.removesuffix(".dcx")
        char = name[:5]
        destination = output / "raw" / char / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        previous = manifest["files"].get(archive_path)
        if destination.exists():
            if not previous or previous["sha256"] != digest(destination):
                raise ValueError(f"Existing output is untracked or modified: {destination}")
            print(f"Verified cached {name}", flush=True)
            continue
        command = [str(args.wine), "--bottle", args.bottle, "--no-gui", "--cx-app",
                   windows_path(args.helper), windows_path(header), windows_path(game / "Data3.bdt"),
                   windows_path(key), archive_path, windows_path(destination), windows_path(game)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError(f"{name}: helper exit {result.returncode}: {result.stderr[-1200:]}")
        manifest["files"][archive_path] = {"path": str(destination.relative_to(output)),
                                          "bytes": destination.stat().st_size, "sha256": digest(destination)}
        temp = manifest_file.with_suffix(".tmp")
        temp.write_text(json.dumps(manifest, indent=2) + "\n")
        temp.replace(manifest_file)
        print(f"Extracted {name}: {destination.stat().st_size:,} bytes", flush=True)


if __name__ == "__main__":
    main()
