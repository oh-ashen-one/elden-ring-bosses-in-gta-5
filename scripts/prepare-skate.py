#!/usr/bin/env python3
"""Prepare the user's own Skate 3 data using pinned upstream conversion tools."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVISION = "cb7968930f14dad38457e98720d1a274e469eec2"
REPOSITORY = "https://github.com/SK8-ENGINE/skate-3-rust-engine.git"
REQUIRED = ["data/big/miscload.big", "data/big/miscboot.big", "data/big/db.big", "data/content/createacharacter.big"]


def run(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xex", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, default=ROOT / "runtime/target/play/iw4l")
    parser.add_argument("--engine-checkout", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    xex = args.xex.expanduser().resolve()
    missing = [str(xex)] if not xex.is_file() or xex.name.lower() != "default.xex" else []
    missing.extend(str(xex.parent / p) for p in REQUIRED if not (xex.parent / p).is_file())
    if missing:
        raise SystemExit("Skate 3 data is missing; nothing was downloaded or converted:\n" + "\n".join(missing))
    out = args.out.expanduser().resolve()
    if out == xex.parent or xex.parent.is_relative_to(out) or out.is_relative_to(xex.parent):
        raise SystemExit("Conversion output must be separate from the original game installation.")
    if out.exists() or out.with_name(out.name + ".partial").exists():
        raise SystemExit("Choose a new output folder; this helper does not overwrite existing conversions.")
    if args.check_only:
        print("Required input files are present. Content validity and conversion have not been tested.")
        return
    if not args.runtime.is_file():
        raise SystemExit("Build the Mac runtime first, or pass --runtime.")
    state = Path(os.environ.get("MW2AI_HOME", Path.home() / "Library/Application Support/Modern Warfare 2 AI"))
    tools = state / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    checkout = args.engine_checkout or tools / ("skate-engine-" + REVISION[:12])
    if not checkout.exists():
        run(["git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, checkout])
        run(["git", "-C", checkout, "sparse-checkout", "init", "--cone"])
        run(["git", "-C", checkout, "sparse-checkout", "set", "tools"])
        run(["git", "-C", checkout, "fetch", "--depth", "1", "origin", REVISION])
        run(["git", "-C", checkout, "checkout", "--detach", REVISION])
    observed = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if observed != REVISION:
        raise SystemExit(f"Converter checkout must be {REVISION}; found {observed}.")
    runner = tools / ("converter-" + REVISION[:12])
    runner.mkdir(exist_ok=True)
    link = runner / "tools"
    expected = (checkout / "tools").resolve()
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or link.resolve() != expected:
            raise SystemExit("Converter tools path is occupied by a different checkout.")
    else:
        link.symlink_to(expected, target_is_directory=True)
    converter = runner / "convert.py"
    shutil.copyfile(ROOT / "runtime/skate/converter/iw4l_skate_convert.py", converter)
    venv = runner / "venv"
    if not (venv / "bin/python").exists():
        run([sys.executable, "-m", "venv", venv])
    python = venv / "bin/python"
    run([python, "-m", "pip", "install", "numpy==2.3.3", "Pillow==11.3.0"])
    env = os.environ.copy()
    env["PATH"] = str(Path.home() / ".cargo/bin") + os.pathsep + env.get("PATH", "")
    run([python, converter, "--xex", xex, "--out", out], env=env)
    assets = out / "assets"
    run([args.runtime.resolve(), "prepare-skate", assets], env=env)
    print(json.dumps({"assets": str(assets), "converter_revision": REVISION}, indent=2))


if __name__ == "__main__":
    main()
