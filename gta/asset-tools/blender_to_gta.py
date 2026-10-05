# SPDX-License-Identifier: GPL-3.0-or-later
"""Run with Blender --background --factory-startup --disable-autoexec.

Data-only conversion: no render, game launch, input control or saved user prefs.
Creates a local editable .blend plus CodeWalker XML drawable/animation assets.
"""
from pathlib import Path
import argparse
import json
import struct
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--input", type=Path, required=True)
parser.add_argument("--textures", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
parser.add_argument("--name", required=True)
parser.add_argument("--geometry-only",action="store_true",help="Use direct corrected glTF-to-YCD conversion after this data-only geometry export")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
repo = args.repo.resolve()
sys.path.insert(0, str(repo / ".cache/gta-tools/blender-python"))
sys.path.insert(0, str(repo / ".cache/gta-tools"))

import bpy
from mathutils import Matrix, Vector
import Sollumz
bpy.ops.preferences.addon_enable(module="Sollumz")
from Sollumz.sollumz_properties import SollumType, LODLevel
from Sollumz.ydr.properties import BoneProperties
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.ydr.ydrexport import export_ydr
import Sollumz.ydr.ydrexport as drawable_export
import Sollumz.ydr.vertex_buffer_builder as vertex_export
from Sollumz.iecontext import ExportContext, ExportSettings, export_context_scope
from Sollumz.tools.meshhelper import get_color_attr_name, get_uv_map_name
from Sollumz.ycd.ycdimport import create_clip_dictionary_template, create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
from Sollumz.tools.animationhelper import get_action_duration_secs, get_action_duration_frames
from Sollumz.sollumz_helper import get_sollumz_materials
from Sollumz.ybn.collision_materials import collisionmats, create_collision_material_from_index
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
if (out / f"{args.name}.blend").exists() or (out / f"{args.name}.ydr.xml").exists():
    raise RuntimeError("Refusing to replace an existing converted asset")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(args.input.resolve()))
source_rig = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
source_actions = list(bpy.data.actions)
report = json.loads(args.input.with_suffix(".json").read_text())
raw_glb=args.input.read_bytes();json_length=struct.unpack_from('<I',raw_glb,12)[0]
gltf=json.loads(raw_glb[20:20+json_length])
source_by_path={}
for mat in gltf['materials']:
    source_path=mat.get('extras',{}).get('source_material')
    resolved={}
    for role,texture in [('base',mat.get('pbrMetallicRoughness',{}).get('baseColorTexture')),('normal',mat.get('normalTexture'))]:
        if texture is not None:
            name=gltf['images'][gltf['textures'][texture['index']]['source']]['name']
            resolved[role]=name.removesuffix('_gl_normal')+'.dds'
    source_by_path[source_path]={'resolved':resolved}

# One explicit root with tag 0; FLVER rigs can contain several root bones.
# Retain all source rest matrices, names and action channels below that root.
source_bones = [(b.name, b.parent.name if b.parent else None, b.matrix_local.copy(), b.length)
                for b in source_rig.data.bones]
armature = bpy.data.armatures.new(args.name + "_rig")
rig = bpy.data.objects.new(args.name, armature)
bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
root = armature.edit_bones.new("ERGT_Root")
root.matrix = Matrix.Identity(4); root.length = 0.1
for name, parent, matrix, length in source_bones:
    bone = armature.edit_bones.new(name)
    bone.matrix = matrix; bone.length = max(length, 0.001)
for name, parent, _, _ in source_bones:
    armature.edit_bones[name].parent = armature.edit_bones[parent] if parent else root
bpy.ops.object.mode_set(mode="OBJECT")
rig.sollum_type = SollumType.DRAWABLE
rig.drawable_properties.lod_dist_high = 250
rig.drawable_properties.lod_dist_med = 250
rig.drawable_properties.lod_dist_low = 250
rig.drawable_properties.lod_dist_vlow = 250
used_tags = {0}
tags = {}
for i, bone in enumerate(armature.bones):
    tag = 0 if i == 0 else BoneProperties.calc_tag_hash(bone.name)
    if i:
        while tag in used_tags: tag = 1 + tag % 65535
    used_tags.add(tag); tags[bone.name] = tag
    bone.bone_properties.use_manual_tag = True
    bone.bone_properties.manual_tag = tag
    for flag_name in ("RotX", "RotY", "RotZ", "TransX", "TransY", "TransZ", "ScaleX", "ScaleY", "ScaleZ"):
        bone.bone_properties.flags.add().name = flag_name

source_materials = {m["name"]: m for m in report["materials"]}
missing_base = []
mesh_objects = [o for o in source_rig.children_recursive if o.type == "MESH"]
for obj in mesh_objects:
    source_mesh = obj.data
    if not source_mesh.materials: raise RuntimeError(f"Imported mesh has no material: {obj.name}")
    original = source_mesh.materials[0]
    matrix_world = obj.matrix_world.copy()
    obj.parent = rig; obj.matrix_world = matrix_world
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE": modifier.object = rig
    obj.sollum_type = SollumType.DRAWABLE_MODEL
    obj.sz_lods.active_lod_level = LODLevel.HIGH
    obj.sz_lods.high.mesh = source_mesh
    obj.data = source_mesh
    for i,uv in enumerate(obj.data.uv_layers):uv.name=get_uv_map_name(i)
    imported_colour=next(iter(obj.data.color_attributes),None)
    source_alpha=None
    if imported_colour:
        # ER colour RGB commonly encodes blend masks, not GTA baked lighting.
        source_alpha=[imported_colour.data[loop.vertex_index if imported_colour.domain=='POINT' else i].color[3]
                      for i,loop in enumerate(obj.data.loops)]
    for index in (0, 1):
        name = get_color_attr_name(index)
        color = obj.data.color_attributes.get(name) or obj.data.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        values=[v for i in range(len(color.data)) for v in (1.0,1.0,1.0,source_alpha[i] if source_alpha else 1.0)]
        color.data.foreach_set("color",values)
    source_path=original.get('source_material')
    source = source_by_path.get(source_path,source_materials.get(original.name, source_materials.get(original.name.rsplit(".", 1)[0], {})))
    material_kind = (original.name + " " + (source.get("source_shader") or "")).lower()
    cutout = any(word in material_kind for word in ("hair", "fur", "butterfly"))
    material = create_shader("ped_default_cutout.sps" if cutout else "ped_default.sps")
    material.name = original.name + "_gta"
    material["ergt_source_material"] = original.name
    material["ergt_source_material_path"] = source_path or ''
    resolved = source.get("resolved", {})
    for role, sampler in (("base", "DiffuseSampler"), ("normal", "BumpSampler")):
        texture_name = resolved.get(role)
        if not texture_name:
            if role == "base": missing_base.append(original.name)
            continue
        texture_path = args.textures / texture_name
        if not texture_path.exists(): texture_path = args.textures.parent / "common" / texture_name
        node = material.node_tree.nodes.get(sampler)
        if node is None: raise RuntimeError(f"Missing shader sampler {sampler}")
        node.image = bpy.data.images.load(str(texture_path.resolve()), check_existing=True)
        node.texture_properties.embedded = True
    obj.data.materials.clear(); obj.data.materials.append(material)
bpy.data.objects.remove(source_rig, do_unlink=True)
armature.pose_position = "REST"
bpy.context.view_layer.update()

# Conservative whole-body collision for the first owner test. This is a
# bounding box, not per-limb collision or FromSoftware's original hitboxes.
points = [obj.matrix_world @ vertex.co for obj in mesh_objects for vertex in obj.data.vertices]
low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
composite = bpy.data.objects.new(args.name + "_bounds", None)
bpy.context.collection.objects.link(composite)
composite.sollum_type = SollumType.BOUND_COMPOSITE; composite.parent = rig
collision_mesh = bpy.data.meshes.new(args.name + "_collision")
corners = [(x,y,z) for z in (low.z,high.z) for y in (low.y,high.y) for x in (low.x,high.x)]
collision_mesh.from_pydata(corners, [], [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)])
collision = bpy.data.objects.new(args.name + "_body_box", collision_mesh)
bpy.context.collection.objects.link(collision)
collision.sollum_type = SollumType.BOUND_BOX; collision.parent = composite
collision_index = next(i for i, material in enumerate(collisionmats) if material.name == "ANIMAL_DEFAULT")
collision_mesh.materials.append(create_collision_material_from_index(collision_index))
collision.composite_flags1.object = True
for flag in ("map_weapon", "map_dynamic", "map_vehicle", "vehicle_not_bvh", "vehicle_bvh", "vehicle_box",
             "ped", "ragdoll", "animal", "object", "projectile", "explosion", "test_weapon", "test_script"):
    setattr(collision.composite_flags2, flag, True)
bpy.context.view_layer.update()

target = AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)
# Retain source UV sets in the PRIVATE intermediate for material baking. The
# final material adapter removes unused channels before native GTA packing.
saved_remove_uvs=drawable_export.remove_unused_uvs
saved_used_uvs=vertex_export.get_mesh_used_texcoords_indices
drawable_export.remove_unused_uvs=lambda vertices,used:vertices
vertex_export.get_mesh_used_texcoords_indices=lambda mesh:list(range(len(mesh.uv_layers)))
with export_context_scope(ExportContext(args.name, ExportSettings((target,)))):
    bundle = export_ydr(rig)
    if not bundle: raise RuntimeError("Drawable conversion failed")
    bundle.save(out, (target,))
drawable_export.remove_unused_uvs=saved_remove_uvs
vertex_export.get_mesh_used_texcoords_indices=saved_used_uvs

clip_dictionary, clips, animations = create_clip_dictionary_template(args.name + "_anims")
clip_names = []
for action in ([] if args.geometry_only else source_actions):
    animation = create_anim_obj(SollumType.ANIMATION)
    animation.name = args.name + "_" + action.name
    animation.parent = animations
    animation.animation_properties.target_id = rig.data
    animation.animation_properties.target_id_prev = rig.data
    animation.animation_properties.action = action
    animation.animation_properties.hash = animation.name
    clip = create_anim_obj(SollumType.CLIP)
    clip.parent = clips; clip.name = action.name
    clip.clip_properties.hash = action.name
    clip.clip_properties.name = action.name
    clip.clip_properties.duration = get_action_duration_secs(action)
    link = clip.clip_properties.animations.add()
    link.animation = animation
    link.start_frame = 0
    link.end_frame = get_action_duration_frames(action)
    clip_names.append(action.name)
bpy.context.view_layer.update()
if not args.geometry_only and not export_ycd(clip_dictionary, str(out / f"{args.name}_anims.ycd.xml")):
    raise RuntimeError("Animation conversion failed")
if args.geometry_only:clip_names=[a['name'] for a in report['animations']]
armature.pose_position = "POSE"
bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{args.name}.blend"))
(out / f"{args.name}.conversion.json").write_text(json.dumps({
    "model": args.name, "source": report["character"], "bones": tags,
    "clips": clip_names, "missing_base_materials": missing_base,
    "shader_sources": [m.get("ergt_source_material",m.name) for m in get_sollumz_materials(rig)],
    "shader_source_paths": [m.get("ergt_source_material_path",'') for m in get_sollumz_materials(rig)],
    "gta_runtime_verified": False, "kind": "animated_drawable",
    "collision": {"type": "whole_body_box", "min": list(low), "max": list(high)},
    "limitations": ["Whole-body box collision; not per-limb hitboxes", "Layered ER materials approximated", "Animation roles unverified"],
}, indent=2) + "\n")
print("GTA_XML_CONVERSION_COMPLETE", args.name, len(tags), len(clip_names), flush=True)
