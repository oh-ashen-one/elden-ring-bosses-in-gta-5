#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare pinned external conversion dependencies in this repo's ignored cache.

Requires an existing Python >=3.13, CMake, Git, MinGW-w64, CrossOver and Blender.
Never launches games, changes account settings, or installs system-wide packages.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender",type=Path,default=Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    parser.add_argument("--blender-python",type=Path,default=Path("/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13"))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]; cache=root/".cache/gta-tools";cache.mkdir(parents=True,exist_ok=True)
    pins=json.loads((root/"gta/dependencies.json").read_text())
    if sys.version_info<(3,13):raise RuntimeError("Python 3.13 or newer is required")
    for tool in ("git","curl","cmake","x86_64-w64-mingw32-gcc","x86_64-w64-mingw32-g++"):
        if not shutil.which(tool):raise RuntimeError(f"Missing prerequisite: {tool}")
    if not args.blender.is_file() or not args.blender_python.is_file():raise RuntimeError("Set the Blender and bundled Python paths")
    def run(*cmd,**kwargs):subprocess.run(list(map(str,cmd)),cwd=root,check=True,**kwargs)
    for name,item in pins["repositories"].items():
        folder=cache/name
        if not folder.exists():run("git","clone","--filter=blob:none",item["url"],folder)
        dirty=subprocess.check_output(["git","-C",str(folder),"status","--porcelain"],text=True)
        if dirty:raise RuntimeError(f"Dependency checkout has changes: {name}; preserving it")
        run("git","-C",folder,"fetch","origin",item["revision"])
        run("git","-C",folder,"checkout","--detach",item["revision"])
    venv=cache/"asset-python"
    if not (venv/"bin/python").exists():run(sys.executable,"-m","venv",venv)
    run(venv/"bin/python","-m","pip","install","--only-binary=:all:","-r",root/"gta/asset-tools/requirements-mac.lock")
    run(args.blender_python,"-m","pip","install","--no-deps","--target",cache/"blender-python",f"szio=={pins['szio']}")
    dotnet=cache/"dotnet/dotnet"
    if not dotnet.exists():
        installer=cache/"dotnet-install.sh"
        urllib.request.urlretrieve("https://dot.net/v1/dotnet-install.sh",installer)
        run("bash",installer,"--version",pins["dotnet_sdk"],"--architecture","arm64","--os","osx","--install-dir",dotnet.parent,"--no-path")
    source=cache/"souls-formats-c";build=root/"build/souls-formats"
    run("cmake","-S",source,"-B",build,"-DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-mingw-w64.cmake",
        "-DCMAKE_BUILD_TYPE=Release","-DBUILD_TESTING=OFF","-DSF_BUILD_EXAMPLES=OFF",
        *[f"-DCPM_{name}_SOURCE={cache/name}" for name in ("klib","zlib-ng","zstd","mxml")])
    run("cmake","--build",build,"-j","4")
    output=root/"build/asset-tools";output.mkdir(parents=True,exist_ok=True)
    libraries=[build/"libsouls_formats.a",build/"_deps/zlib-ng-build/libz.a",build/"_deps/zstd-build/lib/libzstd.a",build/"libmxml4.a"]
    for src,name in [("er_extract.c","er-extract.exe"),("er_unpack.c","er-unpack.exe")]:
        run("x86_64-w64-mingw32-gcc","-std=c11","-O2","-Wall","-Wextra","-Werror","-municode","-static",
            "-I",source/"include",root/"gta/asset-tools"/src,*libraries,"-lbcrypt","-lcrypt32","-o",output/name)
    env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT="1",DOTNET_NOLOGO="1")
    core=root/"build/codewalker-core"
    run(dotnet,"build",cache/"CodeWalker/CodeWalker.Core/CodeWalker.Core.csproj","-c","Release","-o",core,env=env)
    run(dotnet,"build",root/"gta/asset-tools/CodeWalkerBridge","-c","Release",f"-p:CodeWalkerCore={core}",
        f"-p:BaseIntermediateOutputPath={root/'build/cw-bridge-obj'}/","-o",root/"build/cw-bridge",env=env)
    for name,item in pins["runtime_downloads"].items():
        path=cache/(name+".zip")
        if not path.exists():
            # The publisher rejects urllib's default request with HTTP 406;
            # use its normal public download route and verify the pinned hash.
            temporary=path.with_suffix(".download")
            run("curl","-fL","--max-time","60","-e",item["reference"],"-o",temporary,item["url"])
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=item["sha256"]:
                raise RuntimeError(f"Download checksum mismatch: {name}")
            temporary.replace(path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item["sha256"]:raise RuntimeError(f"Download checksum mismatch: {name}")
    print("Pinned source/conversion dependencies prepared. Games were not launched.")


if __name__=="__main__":main()
