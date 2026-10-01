#!/usr/bin/env python3
"""Exercise real APFS clones/links using tiny synthetic files, never retail data."""
import importlib.util
import json
import struct
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("profiles", Path(__file__).parents[1]/"tools/profile_manager.py")
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)

class Registry:
    value = "builtin"
    reject = False
    def read(self): return self.value
    def set(self,value):
        if self.reject and value == "native,builtin": raise RuntimeError("simulated registry write failure")
        self.value=value

if sys.platform != "darwin": raise SystemExit("APFS profile checks require macOS")
with tempfile.TemporaryDirectory(prefix="ergt-profile-check-") as temp:
    root=Path(temp); game=root/"Steam/Game"; game.mkdir(parents=True)
    (game/"update").mkdir()
    exe=b"MZ"+b"\0"*30+struct.pack("<6I",0xfeef04bd,0x10000,1<<16,(3889<<16),0,0)
    (game/"GTA5.exe").write_bytes(exe)
    (game/"update/update.rpf").write_bytes(b"original retail archive fixture")
    (game/"unchanged.bin").write_bytes(b"original")
    bundle=root/"bundle";(bundle/"payload").mkdir(parents=True)
    (bundle/"payload/EldenLosSantos.asi").write_bytes(b"synthetic mod fixture")
    manifest={"files":{"EldenLosSantos.asi":p.digest(bundle/"payload/EldenLosSantos.asi")}}
    (bundle/"manifest.json").write_text(json.dumps(manifest))
    profiles=root/"profile";profiles.mkdir(); state_path=profiles/"profile-state.json"
    state=p.stage(game,bundle,profiles,state_path)
    clone=Path(state["profile"])
    (clone/"unchanged.bin").write_bytes(b"modified clone")
    assert (game/"unchanged.bin").read_bytes()==b"original", "clone writes affected original"
    registry=Registry();registry.reject=True
    try: p.activate(state,state_path,registry)
    except RuntimeError: pass
    else: raise AssertionError("activation should stop when registry setup fails")
    assert game.is_dir() and not game.is_symlink(), "failed activation moved original"
    assert registry.value=="builtin"
    registry.reject=False;p.activate(state,state_path,registry)
    assert game.is_symlink() and (game/"EldenLosSantos.asi").is_file()
    assert Path(state["retail"]).joinpath("unchanged.bin").read_bytes()==b"original"
    p.restore(state,state_path,registry)
    assert not game.is_symlink() and (game/"GTA5.exe").read_bytes()==exe
    assert not (game/"EldenLosSantos.asi").exists() and registry.value=="builtin"
    manifest["files"]={"../outside": "bad"}; (bundle/"manifest.json").write_text(json.dumps(manifest))
    profiles2=root/"profile2";profiles2.mkdir()
    try: p.stage(game,bundle,profiles2,profiles2/"state.json")
    except ValueError: pass
    else: raise AssertionError("path traversal was accepted")
print("APFS isolation, activation rollback, restoration and payload-path checks passed; no game or real registry touched")
