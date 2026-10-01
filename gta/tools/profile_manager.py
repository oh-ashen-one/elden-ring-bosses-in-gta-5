#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reversible local GTA mod profile; never launches GTA or edits retail bytes.

Stage uses APFS clonefile, not a second full-size game copy. Activate switches
the existing Steam game-directory path to that clone. Restore puts the exact
original directory back. Account stores and game saves are never copied.
"""
import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import uuid
from pathlib import Path

EXPECTED_VERSION = (1, 0, 3889, 0)
REGISTRY_KEY = r"HKCU\Software\Wine\AppDefaults\GTA5.exe\DllOverrides"
RUNTIME_FILES = {"EldenLosSantos.asi", "ScriptHookV.dll", "dinput8.dll", "RageOpenV.asi"}


def digest(path):
    with path.open("rb") as stream: return hashlib.file_digest(stream, "sha256").hexdigest()


def version(path):
    raw = path.read_bytes()
    if raw[:2] != b"MZ": raise ValueError("Game executable is not a PE file")
    signature = struct.pack("<II", 0xfeef04bd, 0x10000)
    offset = raw.find(signature)
    if offset < 0: raise ValueError("Game version resource missing")
    major, minor = struct.unpack_from("<II", raw, offset + 8)
    return (major >> 16, major & 65535, minor >> 16, minor & 65535)


def ensure_game_stopped():
    processes = subprocess.check_output(["ps", "-axo", "pid=,comm="], text=True)
    for line in processes.splitlines():
        if re.search(r"(?:^|[\\/])(?:GTA5|GTA5_Enhanced|PlayGTAV)\.exe$", line, re.I):
            raise RuntimeError("GTA is running. Save and quit it before changing profiles; no process was stopped.")


def write_state(path, state):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2) + "\n")
    temp.replace(path)


def clone_tree(source, destination):
    if sys.platform != "darwin": raise RuntimeError("This profile tool currently requires macOS/APFS")
    clone = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True).clonefile
    clone.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    clone.restype = ctypes.c_int
    destination.mkdir()
    for folder, directories, files in os.walk(source, followlinks=False):
        relative = Path(folder).relative_to(source)
        target = destination / relative
        for name in directories:
            entry = Path(folder) / name
            if entry.is_symlink(): raise ValueError("Unexpected directory symlink in retail source")
            (target / name).mkdir()
        for name in files:
            entry = Path(folder) / name
            if not stat.S_ISREG(entry.lstat().st_mode): raise ValueError("Unexpected non-regular retail file")
            result = clone(os.fsencode(entry), os.fsencode(target / name), 0)
            if result:
                error = ctypes.get_errno()
                raise OSError(error, "APFS clone failed; full-copy fallback is deliberately disabled", str(entry))


class Registry:
    def __init__(self, wine, bottle): self.wine, self.bottle = wine, bottle
    def call(self, *arguments):
        return subprocess.run([str(self.wine), "--bottle", self.bottle, "--no-gui", "--cx-app",
            r"C:\windows\system32\reg.exe", *arguments], capture_output=True, text=True, timeout=30)
    def read(self):
        result = self.call("query", REGISTRY_KEY, "/v", "dinput8")
        if result.returncode == 1: return None
        if result.returncode: raise RuntimeError("Cannot read GTA-specific DLL override")
        match = re.search(r"dinput8\s+REG_SZ\s+([^\r\n]+)", result.stdout, re.I)
        if not match: raise RuntimeError("Unexpected registry query response")
        value = match[1].strip()
        if value.lower() not in {"native,builtin", "builtin,native", "native", "builtin", "n,b", "b,n", "n", "b", ""}:
            raise RuntimeError("Unrecognized existing GTA-specific DLL override; preserving it")
        return value
    def set(self, value):
        result = self.call("delete", REGISTRY_KEY, "/v", "dinput8", "/f") if value is None else self.call(
            "add", REGISTRY_KEY, "/v", "dinput8", "/t", "REG_SZ", "/d", value, "/f")
        if result.returncode and not (value is None and result.returncode == 1):
            raise RuntimeError("Could not update the GTA-specific DLL override")
        if self.read() != value: raise RuntimeError("DLL override verification failed")


def stage(game, bundle, root, state_path):
    if state_path.exists(): raise RuntimeError("Profile state already exists; inspect/restore it before staging another profile")
    if game.is_symlink(): raise RuntimeError("Existing Steam game path is a symlink; preserving it")
    source = game.resolve()
    if source == root or source.is_relative_to(root) or root.is_relative_to(source):
        raise ValueError("Profile and original game directories must be separate")
    if version(source / "GTA5.exe") != EXPECTED_VERSION: raise ValueError("Unsupported game build for this candidate")
    manifest = json.loads((bundle / "manifest.json").read_text())
    payload = bundle / "payload"
    if not manifest.get("files"): raise ValueError("Empty candidate payload")
    for name, sha in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not (name in RUNTIME_FILES or relative.parts[0] == "newmods"):
            raise ValueError("Payload contains an unexpected path")
        if (source / relative).exists(): raise ValueError(f"Existing game/mod file conflicts with candidate: {name}")
        file = payload / relative
        if file.is_symlink() or not file.is_file() or digest(file) != sha: raise ValueError(f"Payload checksum mismatch: {name}")
    source_exe = digest(source / "GTA5.exe")
    source_update = (source / "update/update.rpf").stat()
    staging = root / ("Game.staging-" + uuid.uuid4().hex)
    target = root / "Game"
    if target.exists(): raise ValueError("Profile directory already exists")
    try:
        clone_tree(source, staging)
        for name, sha in manifest["files"].items():
            destination = staging / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(payload / name, destination)
            if digest(destination) != sha: raise IOError("Staged payload checksum mismatch")
        updated = (source / "update/update.rpf").stat()
        if digest(source / "GTA5.exe") != source_exe or (updated.st_size, updated.st_mtime_ns) != (source_update.st_size, source_update.st_mtime_ns):
            raise RuntimeError("Original game changed during staging; candidate not activated")
        if digest(staging / "GTA5.exe") != source_exe: raise IOError("Cloned game executable differs")
        staging.rename(target)
        state = {"schema_version": 1, "phase": "staged", "install": str(game.absolute()), "profile": str(target),
                 "retail": str(root / "Retail"), "original_exe_sha256": source_exe,
                 "game_version": list(EXPECTED_VERSION), "files": manifest["files"],
                 "previous_dinput8": None, "gta_runtime_verified": False}
        write_state(state_path, state)
        return state
    except BaseException:
        if staging.exists(): shutil.rmtree(staging)  # only this new incomplete clone
        raise


def activate(state, state_path, registry):
    if state["phase"] != "staged": raise RuntimeError("Profile is not staged")
    install, profile, retail = (Path(state[k]) for k in ("install", "profile", "retail"))
    if install.is_symlink() or not install.is_dir() or retail.exists(): raise RuntimeError("Game paths changed; preserving all paths")
    if digest(install / "GTA5.exe") != state["original_exe_sha256"]: raise RuntimeError("Original game changed after staging")
    for name, sha in state["files"].items():
        if digest(profile / name) != sha: raise RuntimeError("Staged mod payload changed")
    previous = registry.read()
    state["previous_dinput8"] = previous; state["phase"] = "activating"; write_state(state_path, state)
    temporary_link = install.with_name(install.name + ".ergt-link-" + uuid.uuid4().hex)
    try:
        registry.set("native,builtin")
        temporary_link.symlink_to(profile, target_is_directory=True)
        install.rename(retail)
        temporary_link.rename(install)
        if install.resolve() != profile.resolve(): raise RuntimeError("Profile path switch failed")
        state["phase"] = "active"; write_state(state_path, state)
    except BaseException:
        if temporary_link.is_symlink(): temporary_link.unlink()
        if install.is_symlink() and install.resolve() == profile.resolve(): install.unlink()
        if retail.exists() and not install.exists(): retail.rename(install)
        registry.set(previous)
        state["phase"] = "staged"; write_state(state_path, state)
        raise


def restore(state, state_path, registry):
    if state["phase"] not in {"active", "activating"}: raise RuntimeError("Profile is not active")
    install, profile, retail = (Path(state[k]) for k in ("install", "profile", "retail"))
    if not retail.is_dir(): raise RuntimeError("Original retail directory is missing")
    if install.exists() and (not install.is_symlink() or install.resolve() != profile.resolve()):
        raise RuntimeError("Game path is no longer our profile link; preserving it")
    registry.set(state["previous_dinput8"])
    was_link = install.is_symlink()
    try:
        if was_link: install.unlink()
        retail.rename(install)
    except BaseException:
        if was_link and not install.exists(): install.symlink_to(profile, target_is_directory=True)
        registry.set("native,builtin")
        raise
    state["phase"] = "staged"; write_state(state_path, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["stage", "activate", "restore", "status"])
    parser.add_argument("--game", type=Path, default=Path.home()/"Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--root", type=Path, default=Path.home()/"Library/Application Support/EldenLosSantos")
    parser.add_argument("--wine", type=Path, default=Path.home()/"Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine")
    parser.add_argument("--bottle", default="Steam")
    args = parser.parse_args()
    root = args.root.expanduser().resolve(); root.mkdir(parents=True, exist_ok=True)
    state_path = root / "profile-state.json"
    with (root/"profile.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == "status":
            print(state_path.read_text() if state_path.exists() else '{"phase":"not_staged"}')
            return
        ensure_game_stopped()
        registry = Registry(args.wine, args.bottle)
        if args.action == "stage":
            if not args.bundle: parser.error("--bundle is required to stage")
            state = stage(args.game, args.bundle.resolve(), root, state_path)
        else:
            state = json.loads(state_path.read_text())
            if args.action == "activate": activate(state, state_path, registry)
            else: restore(state, state_path, registry)
        print(json.dumps({"phase": state["phase"], "game_launched": False, "retail_bytes_modified": False}))


if __name__ == "__main__": main()
