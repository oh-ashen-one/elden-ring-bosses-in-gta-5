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
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from normalize_dds import normalize_dds

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
    manifest_models = []
    for character, name in CHARACTERS:
        folder = args.converted / character
        receipt = json.loads((folder / f"{name}.conversion.json").read_text())
        if receipt["missing_base_materials"]: raise ValueError(f"{name}: unresolved base materials")
        # Keep source files untouched. Normalize copied DDS headers before the
        # native importer, which otherwise silently encodes sRGB formats as zero.
        conversion = output / "conversion-input" / character
        conversion.mkdir(parents=True)
        drawable_xml = folder / f"{name}.ydr.xml"
        shutil.copy2(drawable_xml, conversion / drawable_xml.name)
        texture_folder = conversion / name; texture_folder.mkdir()
        normalized_count = 0
        for texture in ET.parse(drawable_xml).findall("ShaderGroup/TextureDictionary/Item"):
            filename = texture.findtext("FileName")
            if not filename or Path(filename).name != filename:
                raise ValueError("Unsafe or missing embedded texture filename")
            destination = texture_folder / filename
            if destination.exists(): continue
            data, changed = normalize_dds((folder / name / filename).read_bytes())
            with destination.open("xb") as stream: stream.write(data)
            normalized_count += int(changed)
        for extension, stem in [("ydr", name), ("ycd", name + "_anims")]:
            source = conversion if extension == "ydr" else folder
            invoke("convert", source / f"{stem}.{extension}.xml", models / f"{stem}.{extension}")
            (models / f"{stem}.{extension}.json").rename(output / f"{stem}.{extension}.verification.json")
        low, high = receipt["collision"]["min"], receipt["collision"]["max"]
        centre = [(a+b)/2 for a,b in zip(low,high)]
        radius = math.sqrt(sum(((b-a)/2)**2 for a,b in zip(low,high)))
        item = ET.SubElement(archetypes, "Item", {"type": "CBaseArchetypeDef"})
        # These are script-animated creatures, not static map props. Declare
        # their clip dictionary, and bind the collision embedded in each YDR.
        value(item,"lodDist",250); value(item,"flags",512); value(item,"specialAttribute",0)
        for tag, vector in [("bbMin",low),("bbMax",high),("bsCentre",centre)]:
            ET.SubElement(item,tag,{axis:format(v,".9g") for axis,v in zip("xyz",vector)})
        value(item,"bsRadius",radius); value(item,"hdTextureDist",10)
        ET.SubElement(item,"name").text=name
        ET.SubElement(item,"textureDictionary").text=name
        ET.SubElement(item,"clipDictionary").text=name+"_anims"
        ET.SubElement(item,"drawableDictionary"); ET.SubElement(item,"physicsDictionary").text=name
        ET.SubElement(item,"assetType").text="ASSET_TYPE_DRAWABLE"
        ET.SubElement(item,"assetName").text=name
        ET.SubElement(item,"extensions")
        manifest_models.append({"source_character":character,"model":name,"clips":receipt["clips"],
                                "collision":receipt["collision"],"normalized_srgb_textures":normalized_count,"gta_runtime_verified":False})
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
    for filename,kind in entries:
        item=ET.SubElement(files,"Item");ET.SubElement(item,"filename").text=filename;ET.SubElement(item,"fileType").text=kind
        value(item,"overlay",False);value(item,"disabled",True);value(item,"persistent",True)
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
    invoke("pack",stage,output/"dlc.rpf")
    with (output/"dlc.rpf").open("rb") as stream: sha=hashlib.file_digest(stream,"sha256").hexdigest()
    (output/"package.json").write_text(json.dumps({"schema_version":1,"gta_runtime_verified":False,
        "dlc_name":"ergt","sha256":sha,"models":manifest_models,
        "notice":"Private derived retail assets; do not redistribute"},indent=2)+"\n")
    print("Private DLC package prepared; GTA loading/playability NOT verified.")


if __name__=="__main__":main()
