#!/usr/bin/env python3
"""Collect the declared Rust dependency licenses and their available license/notice files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cargo = os.environ.get("CARGO", str(Path.home() / ".cargo/bin/cargo"))
    packages = {}
    for manifest in [ROOT / "Cargo.toml", ROOT / "runtime/Cargo.toml"]:
        result = json.loads(subprocess.check_output([
            cargo, "metadata", "--format-version", "1", "--locked",
            "--filter-platform", "aarch64-apple-darwin",
            "--manifest-path", str(manifest),
        ]))
        ids = {node["id"] for node in result["resolve"]["nodes"]}
        for package in result["packages"]:
            if package["id"] in ids:
                packages[package["id"]] = package
    index = []
    missing = []
    overrides = json.loads((ROOT / "licenses/dependency-overrides.json").read_text())
    for package in sorted(packages.values(), key=lambda p: (p["name"], p["version"])):
        folder = Path(package["manifest_path"]).parent
        candidates = []
        for pattern in ["LICENSE*", "LICENCE*", "COPYING*", "NOTICE*", "UNLICENSE*"]:
            candidates.extend(p for p in folder.glob(pattern) if p.is_file())
        if package.get("license_file"):
            candidate = folder / package["license_file"]
            if candidate.is_file():
                candidates.append(candidate)
        if not candidates and folder.is_relative_to(ROOT):
            # Vendored local components are described by the preserved upstream NOTICE.
            scope = ROOT / "runtime" if folder.is_relative_to(ROOT / "runtime") else ROOT
            candidates = [scope / "LICENSE", scope / "NOTICE"]
        if not candidates:
            override = overrides.get(package["name"] + "@" + package["version"])
            if override:
                candidates = [ROOT / path for path in override["files"]]
        entry = {
            "name": package["name"], "version": package["version"],
            "license": package.get("license"),
            "repository": package.get("repository"), "files": [],
        }
        for candidate in sorted(set(candidates)):
            blob = candidate.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            name = f'{package["name"]}-{package["version"]}-{candidate.name}'
            (args.output / name).write_bytes(blob)
            entry["files"].append({"file": name, "sha256": digest})
        if not entry["files"]:
            missing.append(f'{package["name"]} {package["version"]}: {package.get("license")}')
        index.append(entry)
    (args.output / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    (args.output / "README.txt").write_text(
        "Rust dependency license inventory for the Apple Silicon build.\n"
        "Declarations come from Cargo metadata; license/notice files are copied verbatim.\n"
        "Local vendored components retain the upstream root LICENSE and NOTICE.\n"
        "This inventory records source declarations; it is not an independent provenance guarantee.\n"
    )
    if missing:
        raise SystemExit("Missing license files:\n" + "\n".join(missing))
    print(f"Collected license notices for {len(index)} Rust packages.")


if __name__ == "__main__":
    main()
