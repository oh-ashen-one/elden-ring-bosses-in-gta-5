#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Package already converted, locally owned assets as a private GTA DLC.

Does not install or launch the game. Never publish the resulting DLC archive.
"""
import argparse
import hashlib
import json
import math
import shutil
import copy
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from normalize_dds import normalize_dds
from dlc_manifest import validate_registration
from texture_dictionaries import partition, parenting, normalize_names
from geometry_fidelity import reject_inward

CHARACTERS = [("c2120", "ergt_malenia"), ("c3181", "ergt_redwolf"), ("c2270", "ergt_crab")]


def value(parent, tag, number):
    return ET.SubElement(parent, tag, {"value": str(number).lower()})


def write_xml(root, path):
    ET.indent(root)
    with path.open("xb") as stream:
        ET.ElementTree(root).write(stream, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converted", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--bridge", type=Path, required=True)
    parser.add_argument("--roster",type=Path)
    parser.add_argument("--external-textures",action="store_true",help="Use standard separate YTD resources to avoid bloating skinned drawables")
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists(): raise ValueError("Use a new packaging directory; existing outputs are preserved")
    output.mkdir(parents=True)
    models = output / "model-input"; models.mkdir()
    stage = output / "dlc-input"; stage.mkdir()
    bridge = [str(args.dotnet.resolve()), str(args.bridge.resolve())]
    def invoke(*arguments):
        result = subprocess.run([*bridge, *map(str, arguments)], capture_output=True, text=True, timeout=180)
        if result.returncode: raise RuntimeError(result.stderr[-4000:])
        print(result.stdout.strip(), flush=True)
    map_types = ET.Element("CMapTypes")
    ET.SubElement(map_types, "extensions")
    archetypes = ET.SubElement(map_types, "archetypes")
    manifest_models = [];texture_chains=[];chains_by_model={};conversions_by_model={}
    bosses=json.loads(args.roster.read_text())['bosses'] if args.roster else [{'character':c,'model':n} for c,n in CHARACTERS]
    characters=[(b['character'],b['model']) for b in bosses];parents={b['model']:b.get('visual_child_of') for b in bosses}
    for character, name in characters:
        shared_parent=parents[name]
        if shared_parent and (not args.external_textures or shared_parent not in conversions_by_model):raise ValueError('Visual child requires an already packaged external-texture parent')
        folder = args.converted / character
        receipt = json.loads((folder / f"{name}.conversion.json").read_text())
        if receipt["missing_base_materials"]: raise ValueError(f"{name}: unresolved base materials")
        # Keep source files untouched. Normalize copied DDS headers before the
        # native importer, which otherwise silently encodes sRGB formats as zero.
        conversion = output / "conversion-input" / character
        conversion.mkdir(parents=True)
        drawable_xml = folder / f"{name}.ydr.xml"
        reject_inward(ET.parse(drawable_xml))
        shutil.copy2(drawable_xml, conversion / drawable_xml.name)
        normalized_document=ET.parse(conversion/drawable_xml.name);normalize_names(normalized_document)
        normalized_document.write(conversion/drawable_xml.name,encoding='utf-8',xml_declaration=True)
        texture_folder = conversion / name; texture_folder.mkdir()
        normalized_count = 0
        for texture in ([] if shared_parent else ET.parse(drawable_xml).findall("ShaderGroup/TextureDictionary/Item")):
            filename = texture.findtext("FileName")
            if not filename or Path(filename).name != filename:
                raise ValueError("Unsafe or missing embedded texture filename")
            destination = texture_folder / filename
            if destination.exists(): continue
            data, changed = normalize_dds((folder / name / filename).read_bytes())
            with destination.open("xb") as stream: stream.write(data)
            normalized_count += int(changed)
        if args.external_textures:
            document=ET.parse(conversion/drawable_xml.name);dictionary=document.find('ShaderGroup/TextureDictionary')
            if dictionary is None:raise ValueError('Expected embedded texture inputs before separation')
            if shared_parent:
                chain=chains_by_model[shared_parent];parent_conversion=conversions_by_model[shared_parent]
                for txd in chain:
                    shutil.copy2(parent_conversion/(txd+'.ytd.xml'),conversion/(txd+'.ytd.xml'))
                    (conversion/txd).symlink_to((parent_conversion/txd).resolve(),target_is_directory=True)
            else:
                groups,sizes=partition(dictionary,texture_folder)
                chain=[name if i==0 else name+'_t'+str(i).zfill(2) for i in range(len(groups))]
                texture_chains.append(chain)
                for txd,group in zip(chain,groups):
                    if txd!=name:(conversion/txd).symlink_to(texture_folder.name,target_is_directory=True)
                    write_xml(group,conversion/(txd+'.ytd.xml'))
                    invoke('convert',conversion/(txd+'.ytd.xml'),models/(txd+'.ytd'))
                    (models/(txd+'.ytd.json')).rename(output/(txd+'.ytd.verification.json'))
                chains_by_model[name]=chain
            (conversion/(name+'.textures.json')).write_text(json.dumps([txd+'.ytd.xml' for txd in chain]))
            document.find('ShaderGroup').remove(dictionary);ET.indent(document)
            document.write(conversion/drawable_xml.name,encoding='utf-8',xml_declaration=True)
        for extension, stem in [("ydr", name), ("ycd", name + "_anims")]:
            if shared_parent and extension=='ycd':continue
            source = conversion if extension == "ydr" else folder
            invoke("convert", source / f"{stem}.{extension}.xml", models / f"{stem}.{extension}")
            (models / f"{stem}.{extension}.json").rename(output / f"{stem}.{extension}.verification.json")
        render_bounds = receipt.get("render_bounds", receipt["collision"])
        low, high = render_bounds["min"], render_bounds["max"]
        centre = [(a+b)/2 for a,b in zip(low,high)]
        radius = math.sqrt(sum(((b-a)/2)**2 for a,b in zip(low,high)))
        item = ET.SubElement(archetypes, "Item", {"type": "CBaseArchetypeDef"})
        # These are script-animated creatures, not static map props. Declare
        # their clip dictionary, and bind the collision embedded in each YDR.
        # The in-game isolation check accepted 131072|512 (Dynamic + Has Anim)
        # with the full original rig/collision; 512 and 32|512 returned zero.
        value(item,"lodDist",250); value(item,"flags",131072 | 512); value(item,"specialAttribute",0)
        for tag, vector in [("bbMin",low),("bbMax",high),("bsCentre",centre)]:
            ET.SubElement(item,tag,{axis:format(v,".9g") for axis,v in zip("xyz",vector)})
        value(item,"bsRadius",radius); value(item,"hdTextureDist",150)
        ET.SubElement(item,"name").text=name
        ET.SubElement(item,"textureDictionary").text=shared_parent or name
        ET.SubElement(item,"clipDictionary").text=(shared_parent or name)+"_anims"
        ET.SubElement(item,"drawableDictionary"); ET.SubElement(item,"physicsDictionary").text=name
        ET.SubElement(item,"assetType").text="ASSET_TYPE_DRAWABLE"
        ET.SubElement(item,"assetName").text=name
        ET.SubElement(item,"extensions")
        manifest_models.append({"source_character":character,"model":name,"clips":receipt["clips"],
                                "collision":receipt["collision"],"normalized_srgb_textures":normalized_count,"gta_runtime_verified":False})
        conversions_by_model[name]=conversion
    ET.SubElement(map_types,"name").text="ergt"
    ET.SubElement(map_types,"dependencies"); ET.SubElement(map_types,"compositeEntityTypes")
    ytyp_xml=output/"ergt.ytyp.xml"; write_xml(map_types,ytyp_xml)
    invoke("convert",ytyp_xml,models/"ergt.ytyp")
    (models/"ergt.ytyp.json").rename(output/"ergt.ytyp.verification.json")
    archive_dir=stage/"x64/models/cdimages";archive_dir.mkdir(parents=True)
    invoke("pack",models,archive_dir/"ergt_assets.rpf")
    setup=ET.Element("SSetupData")
    for tag,text in [("deviceName","dlc_ergt"),("datFile","content.xml"),("timeStamp","10/01/2026 00:00:00"),("nameHash","ergt")]:
        ET.SubElement(setup,tag).text=text
    groups=ET.SubElement(setup,"contentChangeSetGroups");group=ET.SubElement(groups,"Item")
    ET.SubElement(group,"NameHash").text="GROUP_STARTUP"
    changes=ET.SubElement(group,"ContentChangeSets"); ET.SubElement(changes,"Item").text="ergt_startup"
    ET.SubElement(setup,"type").text="EXTRACONTENT_COMPAT_PACK"
    value(setup,"order",30);value(setup,"minorOrder",0);value(setup,"isLevelPack",False)
    write_xml(setup,stage/"setup2.xml")
    content=ET.Element("CDataFileMgr__ContentsOfDataFileXml")
    for tag in ("disabledFiles","includedXmlFiles","includedDataFiles"):ET.SubElement(content,tag)
    files=ET.SubElement(content,"dataFiles")
    archive_path="dlc_ergt:/%PLATFORM%/models/cdimages/ergt_assets.rpf"
    entries=[(archive_path,"RPF_FILE"),(archive_path+"/ergt.ytyp","DLC_ITYP_REQUEST")]
    if texture_chains:
        meta=stage/'common/data/gtxd.meta';meta.parent.mkdir(parents=True)
        write_xml(parenting(texture_chains),meta)
        entries.append(('dlc_ergt:/common/data/gtxd.meta','GTXD_PARENTING_DATA'))
    for filename,kind in entries:
        item=ET.SubElement(files,"Item");ET.SubElement(item,"filename").text=filename;ET.SubElement(item,"fileType").text=kind
        value(item,"overlay",False);value(item,"disabled",True);value(item,"persistent",True)
        if kind == "DLC_ITYP_REQUEST":
            # Register script-spawnable object model information, not merely
            # world/map archetypes. Asset streaming alone is not sufficient.
            ET.SubElement(item,"contents").text="CONTENTS_PROPS"
    changes=ET.SubElement(content,"contentChangeSets");change=ET.SubElement(changes,"Item")
    ET.SubElement(change,"changeSetName").text="ergt_startup"
    ET.SubElement(change,"mapChangeSetData")
    for tag in ("filesToDisable","filesToEnable","txdToLoad","txdToUnload","residentResources","unregisterResources"):
        node=ET.SubElement(change,tag)
        if tag=="filesToEnable":
            for filename,_ in entries:ET.SubElement(node,"Item").text=filename
    value(change,"requiresLoadingScreen",False)
    ET.SubElement(content,"patchFiles")
    write_xml(content,stage/"content.xml")
    validate_registration(stage/"setup2.xml", stage/"content.xml")
    invoke("pack",stage,output/"dlc.rpf")
    with (output/"dlc.rpf").open("rb") as stream: sha=hashlib.file_digest(stream,"sha256").hexdigest()
    (output/"package.json").write_text(json.dumps({"schema_version":1,"gta_runtime_verified":False,
        "dlc_name":"ergt","sha256":sha,"models":manifest_models,
        "notice":"Private derived retail assets; do not redistribute"},indent=2)+"\n")
    print("Private DLC package prepared; GTA loading/playability NOT verified.")


if __name__=="__main__":main()
