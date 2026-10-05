#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rebuild the private four-boss DLC from owned installs. No game launch.

Run with the asset Python environment created by bootstrap_tools.py. Use a fresh
output directory. The resulting retail-derived assets must not be redistributed.
"""
import argparse
import os
import json
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
    parser.add_argument('--gpu-root',type=Path,required=True,help='Verified active shared renderer coordinator, never a fallback lock root')
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2]; tools=repo/"gta/asset-tools"; cache=repo/".cache/gta-tools"
    roster_path=repo/'gta/roster.json';bosses=json.loads(roster_path.read_text())['bosses']
    wrapper=args.gpu_root.resolve()/'bin/gpu_slot.py'
    if not wrapper.is_file():raise RuntimeError('Shared renderer coordinator missing')
    output=args.out.resolve();game=args.elden_game.resolve()
    if output.exists():raise ValueError("Use a fresh output directory")
    for original in [game,args.gta_game.resolve()]:
        if output==original or output.is_relative_to(original) or original.is_relative_to(output):
            raise ValueError("Output must be separate from original installs")
    wine=Path.home()/"Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine"
    bottle=Path.home()/"Library/Application Support/CrossOver/Bottles"/args.bottle
    if not bottle.is_dir():raise RuntimeError("Create a separate ERGTA-Tools Windows 10 64-bit bottle first; do not use your game bottle")
    def run(*command,**kwargs):subprocess.run(list(map(str,command)),cwd=repo,check=True,**kwargs)
    def windows(executable,*arguments,**kwargs):
        run(wine,"--bottle",args.bottle,"--no-gui","--cx-app",windows_path(repo/"build/asset-tools"/executable),*arguments,**kwargs)
    run(sys.executable,tools/"extract_characters.py","--game",game,"--out",output,"--keys",cache/"BinderKeys/EldenRing_PC",
        "--helper",repo/"build/asset-tools/er-extract.exe","--bottle",args.bottle,"--characters",*[b["character"] for b in bosses])
    key=cache/"BinderKeys/EldenRing_PC/Key/Data0.pem";header=output/"headers/Data0.bhd"
    decode_header(game/"Data0.bhd",key,header)
    for source,name in [("/material/allmaterial.matbinbnd.dcx","allmaterial.matbinbnd"),("/parts/common_body.tpf.dcx","common_body.tpf")]:
        windows("er-extract.exe",windows_path(header),windows_path(game/"Data0.bdt"),windows_path(key),source,windows_path(output/name),windows_path(game))
    for character in [*[b["character"] for b in bosses],"common"]:
        destination=output/"textures"/character;destination.mkdir(parents=True)
        source=output/"common_body.tpf" if character=="common" else output/"raw"/character/(character+"_h.texbnd")
        windows("er-unpack.exe","--textures",windows_path(source),windows_path(destination))
    windows("er-unpack.exe","--materials",windows_path(output/"allmaterial.matbinbnd"),windows_path(output/"materials.json"))
    # Current material index includes parameters as well as samplers.
    (output/"materials-with-params.json").write_bytes((output/"materials.json").read_bytes())
    run(sys.executable,tools/"prepare_material_overrides.py","--root",output)
    for boss in bosses:
        character,name,clips=boss['character'],boss['model'],boss['clips']
        glb=output/'interchange-final'/(character+'.glb')
        command=[sys.executable,tools/'export_character_glb.py','--root',output,'--character',character,'--out',glb,
                 '--animations',str(len(clips)),'--clip-names',*clips,'--masks',*map(str,boss['display_masks'])]
        if boss['include_unmasked']:command.append('--include-unmasked')
        run(*command)
        env=dict(os.environ,BLENDER_USER_CONFIG=str(cache/'blender-profile'),GPU_SLOT_DIR=str(args.gpu_root.resolve()))
        run(sys.executable,wrapper,'capture','--label','ergt-owned-geometry','--timeout','60','--',
            args.blender,'--background','--factory-startup','--disable-autoexec','--threads','2','--python',tools/'blender_to_gta.py','--',
            '--repo',repo,'--input',glb,'--textures',output/'textures'/character,'--out',output/'gta'/character,'--name',name,'--geometry-only',env=env)
        if not (output/'gta'/character/(name+'.conversion.json')).is_file():raise RuntimeError('Blender conversion did not complete')
        event_file=output/(character+'-attack-events.json')
        with event_file.open('w') as event_output:
            windows('er-tae-events.exe',windows_path(output/'raw'/character/(character+'.anibnd')),'3000',stdout=event_output)
        event_data=json.loads(event_file.read_text())
        if not event_data.get('events'):raise ValueError('Original attack events absent')
    run(sys.executable,tools/'material_fidelity.py','--converted',output/'gta','--source-root',output,'--roster',roster_path,'--out',output/'gta-materials')
    run(sys.executable,tools/'finalize_roster.py','--materials',output/'gta-materials','--interchange',output/'interchange-final','--roster',roster_path,'--out',output/'gta-ready')
    run(sys.executable,tools/'scale_roster.py','--converted',output/'gta-ready','--roster',roster_path,'--out',output/'gta-scaled')
    run(sys.executable,tools/'split_large_rig.py','--converted',output/'gta-scaled','--roster',roster_path,'--out',output/'gta-parts')
    run(sys.executable,tools/'cutout_fidelity.py','--converted',output/'gta-parts','--source-root',output,'--roster',output/'gta-parts/render-roster.json','--out',output/'gta-cutouts')
    run(sys.executable,tools/'export_roster_motion.py','--root',output,'--roster',roster_path,'--out',output/'motion')
    dotnet=cache/'dotnet/dotnet';bridge=repo/'build/cw-bridge/CodeWalkerBridge.dll'
    run(sys.executable,tools/'build_dlc.py','--converted',output/'gta-cutouts','--out',output/'dlc-build','--dotnet',dotnet,'--bridge',bridge,'--roster',output/'gta-parts/render-roster.json','--external-textures')
    run(sys.executable,tools/'rpf_audit.py',output/'dlc-build/dlc.rpf','--out',output/'archive-audit.json')
    run(dotnet,bridge,"prepare-dlclist",args.gta_game.resolve(),output/"newmods/common/data/dlclist.xml")
    print("Private owned-asset DLC prepared. No game launched. Runtime verification is still required.")


if __name__=="__main__":main()
