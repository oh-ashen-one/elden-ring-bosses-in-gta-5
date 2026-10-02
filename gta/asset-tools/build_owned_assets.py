#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rebuild the private three-creature DLC from owned installs. No game launch.

Run with the asset Python environment created by bootstrap_tools.py. Use a fresh
output directory. The resulting retail-derived assets must not be redistributed.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from extract_characters import decode_header, windows_path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elden-game",type=Path,required=True)
    parser.add_argument("--gta-game",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--blender",type=Path,default=Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    parser.add_argument("--bottle",default="ERGTA-Tools")
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2]; tools=repo/"gta/asset-tools"; cache=repo/".cache/gta-tools"
    output=args.out.resolve();game=args.elden_game.resolve()
    if output.exists():raise ValueError("Use a fresh output directory")
    for original in [game,args.gta_game.resolve()]:
        if output==original or output.is_relative_to(original) or original.is_relative_to(output):
            raise ValueError("Output must be separate from original installs")
    wine=Path.home()/"Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine"
    bottle=Path.home()/"Library/Application Support/CrossOver/Bottles"/args.bottle
    if not bottle.is_dir():raise RuntimeError("Create a separate ERGTA-Tools Windows 10 64-bit bottle first; do not use your game bottle")
    def run(*command,**kwargs):subprocess.run(list(map(str,command)),cwd=repo,check=True,**kwargs)
    def windows(executable,*arguments):
        run(wine,"--bottle",args.bottle,"--no-gui","--cx-app",windows_path(repo/"build/asset-tools"/executable),*arguments)
    run(sys.executable,tools/"extract_characters.py","--game",game,"--out",output,"--keys",cache/"BinderKeys/EldenRing_PC",
        "--helper",repo/"build/asset-tools/er-extract.exe","--bottle",args.bottle,"--characters","c2120","c3181","c2270")
    key=cache/"BinderKeys/EldenRing_PC/Key/Data0.pem";header=output/"headers/Data0.bhd"
    decode_header(game/"Data0.bhd",key,header)
    for source,name in [("/material/allmaterial.matbinbnd.dcx","allmaterial.matbinbnd"),("/parts/common_body.tpf.dcx","common_body.tpf")]:
        windows("er-extract.exe",windows_path(header),windows_path(game/"Data0.bdt"),windows_path(key),source,windows_path(output/name),windows_path(game))
    for character in ["c2120","c3181","c2270","common"]:
        destination=output/"textures"/character;destination.mkdir(parents=True)
        source=output/"common_body.tpf" if character=="common" else output/"raw"/character/(character+"_h.texbnd")
        windows("er-unpack.exe","--textures",windows_path(source),windows_path(destination))
    windows("er-unpack.exe","--materials",windows_path(output/"allmaterial.matbinbnd"),windows_path(output/"materials.json"))
    # Current material index includes parameters as well as samplers.
    (output/"materials-with-params.json").write_bytes((output/"materials.json").read_bytes())
    run(sys.executable,tools/"prepare_material_overrides.py","--root",output)
    entries=[("c2120","ergt_malenia",["a000_000020","a000_002000","a000_003000","a000_005000"]),
             ("c3181","ergt_redwolf",["a000_000000","a000_001020","a000_003000","a000_005000"]),
             ("c2270","ergt_crab",["a000_000000","a000_001020","a000_003000","a000_005000"])]
    for character,name,clips in entries:
        glb=output/"interchange"/(character+".glb")
        command=[sys.executable,tools/"export_character_glb.py","--root",output,"--character",character,"--out",glb,
                 "--animations","4","--clip-names",*clips]
        if character=="c2120":command.extend(["--masks","0","10","21"])
        run(*command)
        env=dict(os.environ,BLENDER_USER_CONFIG=str(cache/"blender-profile"))
        run(args.blender,"--background","--factory-startup","--disable-autoexec","--python",tools/"blender_to_gta.py","--",
            "--repo",repo,"--input",glb,"--textures",output/"textures"/character,"--out",output/"gta"/character,"--name",name,env=env)
        if not (output/"gta"/character/(name+".conversion.json")).is_file():raise RuntimeError("Blender conversion did not complete")
    run(sys.executable,tools/"upgrade_visuals.py","--converted",output/"gta","--root",output,"--out",output/"gta-object-materials")
    # Reconstruct native local animation tracks from source world poses after
    # material conversion. The original Blender f-curve export stays available
    # for diagnosis in this new output tree; retail/source files are untouched.
    for character,name,_ in entries:
        converted=output/"gta-object-materials"/character
        template=converted/(name+"_anims.ycd.xml")
        repaired=output/"animation-repaired"/character/(name+"_anims.ycd.xml")
        run(sys.executable,tools/"rebuild_animation.py","--glb",output/"interchange"/(character+".glb"),
            "--drawable",converted/(name+".ydr.xml"),"--template",template,"--out",repaired)
        template.rename(converted/(name+"_anims.blender-source.xml"))
        shutil.copy2(repaired,template)
    dotnet=cache/"dotnet/dotnet";bridge=repo/"build/cw-bridge/CodeWalkerBridge.dll"
    run(sys.executable,tools/"build_dlc.py","--converted",output/"gta-object-materials","--out",output/"dlc-build","--dotnet",dotnet,"--bridge",bridge)
    run(dotnet,bridge,"prepare-dlclist",args.gta_game.resolve(),output/"newmods/common/data/dlclist.xml")
    print("Private owned-asset DLC prepared. No game launched. Runtime verification is still required.")


if __name__=="__main__":main()
