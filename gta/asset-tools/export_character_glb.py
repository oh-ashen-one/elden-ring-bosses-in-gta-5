#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline, local-only FLVER/Havok -> rigged glTF 2.0 interchange export.

This is an intermediate asset, NOT a GTA-ready model. It preserves source rigs
and animation identifiers. Materials use available base/normal textures; ER's
layered shaders, cloth simulation and effects are not recreated here.
"""
import argparse
import hashlib
import io
import json
import re
import struct
from pathlib import Path, PureWindowsPath

import numpy as np
from PIL import Image, ImageOps
from scipy.spatial.transform import Rotation
from soulstruct.containers import Binder
from soulstruct.flver import FLVER
from soulstruct.flver.bone_tools import BoneTree
from soulstruct.havok import HKX
from soulstruct.havok.fromsoft.eldenring import SkeletonHKX, AnimationHKX
from havok_compat import install as install_havok_compat
install_havok_compat()


class GLB:
    def __init__(self):
        self.data = bytearray()
        self.doc = {"asset": {"version": "2.0", "generator": "ERGT local asset tools"},
                    "scene": 0, "scenes": [{"nodes": [0]}],
                    "nodes": [{"name": "Character", "children": []}],
                    "meshes": [], "skins": [], "materials": [], "textures": [],
                    "images": [], "accessors": [], "bufferViews": [], "animations": []}

    def blob(self, raw, target=None):
        self.data.extend(b"\0" * (-len(self.data) % 4))
        item = {"buffer": 0, "byteOffset": len(self.data), "byteLength": len(raw)}
        if target: item["target"] = target
        self.doc["bufferViews"].append(item)
        self.data.extend(raw)
        return len(self.doc["bufferViews"]) - 1

    def array(self, values, kind, component=5126, target=None, bounds=False):
        dtype = {5126: "<f4", 5125: "<u4", 5123: "<u2"}[component]
        values = np.asarray(values, dtype=dtype)
        if not np.isfinite(values).all(): raise ValueError("Non-finite asset data")
        item = {"bufferView": self.blob(values.tobytes(), target), "componentType": component,
                "count": len(values), "type": kind}
        if bounds:
            item["min"] = np.atleast_1d(values.min(axis=0)).tolist()
            item["max"] = np.atleast_1d(values.max(axis=0)).tolist()
        self.doc["accessors"].append(item)
        return len(self.doc["accessors"]) - 1

    def image(self, dds_path, normal=False):
        dds = bytearray(dds_path.read_bytes())
        dxgi = struct.unpack_from("<I", dds, 128)[0] if len(dds) >= 148 and dds[84:88] == b"DX10" else None
        # Pillow lacks the BC1/2/3 sRGB aliases. Their block encoding is the
        # same as UNORM; keep the original source file and pixel values intact.
        if dxgi in {72, 75, 78}: struct.pack_into("<I", dds, 128, dxgi - 1)
        image = Image.open(io.BytesIO(dds)).convert("RGBA")
        if normal:
            if dxgi in {82, 83, 84}:  # BC5 stores only tangent-space X/Y.
                pixels = np.asarray(image).copy()
                xy = pixels[:, :, :2].astype(float) / 127.5 - 1.0
                pixels[:, :, 2] = np.rint((np.sqrt(np.maximum(0, 1 - (xy * xy).sum(axis=2))) + 1) * 127.5).astype(np.uint8)
                image = Image.fromarray(pixels)
            r, g, b, a = image.split()
            image = Image.merge("RGBA", (r, ImageOps.invert(g), b, a))
        out = io.BytesIO(); image.save(out, format="PNG")
        self.doc["images"].append({"name": dds_path.stem + ("_gl_normal" if normal else ""),
                                   "bufferView": self.blob(out.getvalue()), "mimeType": "image/png"})
        self.doc["textures"].append({"source": len(self.doc["images"]) - 1})
        return len(self.doc["textures"]) - 1

    def write(self, path):
        for key in ["animations", "textures", "images", "materials"]:
            if not self.doc[key]: del self.doc[key]
        self.doc["buffers"] = [{"byteLength": len(self.data)}]
        encoded = json.dumps(self.doc, separators=(",", ":"), allow_nan=False).encode()
        encoded += b" " * (-len(encoded) % 4)
        self.data.extend(b"\0" * (-len(self.data) % 4))
        total = 12 + 8 + len(encoded) + 8 + len(self.data)
        with path.open("xb") as out:
            out.write(struct.pack("<4sII", b"glTF", 2, total))
            out.write(struct.pack("<I4s", len(encoded), b"JSON")); out.write(encoded)
            out.write(struct.pack("<I4s", len(self.data), b"BIN\0")); out.write(self.data)


# FromSoftware left-handed Y-up -> glTF right-handed Y-up. Triangle winding
# reverses too. GTA's Z-up conversion belongs to the subsequent GTA adapter.
BASIS = np.diag([1., 1., -1., 1.])


def trs(matrix):
    translation = matrix[:3, 3]
    scale = np.linalg.norm(matrix[:3, :3], axis=0)
    if (scale < 1e-9).any(): raise ValueError("Degenerate bone transform")
    rotation = matrix[:3, :3] / scale
    if np.linalg.det(rotation) < 0:
        scale[0] *= -1; rotation[:, 0] *= -1
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-3):
        raise ValueError("Bone contains unsupported shear")
    return translation.tolist(), Rotation.from_matrix(rotation).as_quat().tolist(), scale.tolist()


def material_key(path):
    return PureWindowsPath(path).stem.lower()


def load_flver(path):
    binder = Binder.from_path(path)
    entry = next(e for e in binder.entries if e.name.lower().endswith(".flver"))
    return FLVER.from_bytes(entry.get_uncompressed_data())


def rest_matrices(flver):
    transforms = BoneTree(flver).get_bone_armature_space_transforms()
    matrices = []
    for translation, rotation, scale in transforms:
        matrix = np.eye(4)
        matrix[:3, :3] = rotation.data @ np.diag(scale.data)
        matrix[:3, 3] = translation.data
        matrices.append(matrix)
    return matrices


def mesh_skin(mesh, vertices):
    count = len(vertices)
    if "bone_weights" in vertices.dtype.names and mesh.is_dynamic:
        weights = np.maximum(vertices["bone_weights"].astype(float), 0)
        joints = vertices["bone_indices"].astype(np.int64)
        if mesh.bone_indices is not None:
            safe = np.where(weights > 0, joints, 0)
            if (safe < 0).any() or (safe >= len(mesh.bone_indices)).any():
                raise ValueError("Invalid local bone palette index")
            joints = np.asarray(mesh.bone_indices)[safe]
        empty = weights.sum(axis=1) < 1e-8
        joints[empty] = max(0, mesh.default_bone_index)
        weights[empty] = [1, 0, 0, 0]
        joints[weights <= 0] = 0
        weights /= weights.sum(axis=1)[:, None]
    else:
        joints = np.full((count, 4), max(0, mesh.default_bone_index), dtype=np.int64)
        weights = np.zeros((count, 4)); weights[:, 0] = 1
    return joints, weights


def combined_vertices(mesh):
    # Cloth splits positions and UV/weight data into separate GPU streams.
    # Repeated position streams are simulation/motion variants; retain the
    # first authored stream and merge missing semantic fields from the others.
    fields = {}
    count = len(mesh.vertex_arrays[0].array)
    for buffer in mesh.vertex_arrays:
        array = buffer.array
        if len(array) != count: raise ValueError("Vertex stream lengths differ")
        for name in array.dtype.names:
            if name not in fields: fields[name] = (array.dtype.fields[name][0], array[name])
    result = np.empty(count, dtype=[(name, info[0]) for name, info in fields.items()])
    for name, (_, values) in fields.items(): result[name] = values
    return result


def export(root, char, destination, masks, max_animations, clip_names=None, include_unmasked=False):
    raw = root / "raw" / char
    flver = load_flver(raw / f"{char}.chrbnd")
    original_rest = rest_matrices(flver)
    materials = {material_key(k): v for k, v in json.loads((root / "materials.json").read_text()).items()}
    textures = {p.stem.lower(): p for p in (root / "textures/common").glob("*.dds")}
    textures.update({p.stem.lower(): p for p in (root / "textures" / char).glob("*.dds")})
    override_file = root / "material-overrides.json"
    overrides = json.loads(override_file.read_text()) if override_file.exists() else {}
    glb = GLB()
    glb.doc["nodes"][0]["name"] = char
    selected = []
    used = set()
    for mesh in flver.meshes:
        mask = re.match(r"#(\d+)#", mesh.material.name)
        if masks is not None and ((mask is None and not include_unmasked) or (mask is not None and int(mask[1]) not in masks)): continue
        vertices = combined_vertices(mesh)
        if not len(vertices): continue
        joints, weights = mesh_skin(mesh, vertices)
        weighted = set(int(i) for i in joints[weights > 0])
        if any(i < 0 or i >= len(flver.bones) for i in weighted): raise ValueError("Joint outside skeleton")
        used.update(weighted)
        selected.append((mesh, vertices, joints, weights))
    if not selected: raise ValueError("No meshes selected")
    for joint in list(used):
        visited = set()
        while joint >= 0:
            if joint in visited: raise ValueError("Cyclic skeleton")
            visited.add(joint); used.add(joint)
            joint = flver.bones[joint].parent_bone_index
    bone_ids = sorted(used)
    remap = {old: new for new, old in enumerate(bone_ids)}
    rest = {i: BASIS @ original_rest[i] @ BASIS for i in bone_ids}
    bone_nodes = {}
    for i in bone_ids:
        bone = flver.bones[i]
        parent = bone.parent_bone_index
        local = np.linalg.inv(rest[parent]) @ rest[i] if parent >= 0 else rest[i]
        translation, rotation, scale = trs(local)
        bone_nodes[i] = len(glb.doc["nodes"])
        glb.doc["nodes"].append({"name": bone.name, "translation": translation,
                                  "rotation": rotation, "scale": scale})
    for i in bone_ids:
        parent = flver.bones[i].parent_bone_index
        parent_node = bone_nodes[parent] if parent >= 0 else 0
        glb.doc["nodes"][parent_node].setdefault("children", []).append(bone_nodes[i])
    inverse_bind = np.asarray([np.linalg.inv(rest[i]).T.reshape(16) for i in bone_ids])
    glb.doc["skins"].append({"name": char + "_source_rig", "joints": [bone_nodes[i] for i in bone_ids],
                               "skeleton": 0, "inverseBindMatrices": glb.array(inverse_bind, "MAT4")})
    image_cache = {}
    exported_materials = []
    all_positions = []
    triangles_total = 0
    for mesh, vertices, joints, weights in selected:
        position = vertices["position"].astype(float)
        normal = vertices["normal"].astype(float)
        if not mesh.is_dynamic:
            matrix = original_rest[max(0, mesh.default_bone_index)]
            position = (matrix @ np.column_stack([position, np.ones(len(position))]).T).T[:, :3]
            normal = (np.linalg.inv(matrix[:3, :3]).T @ normal.T).T
        position[:, 2] *= -1; normal[:, 2] *= -1
        normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-8)
        all_positions.append(position)
        faces = next((f for f in mesh.face_sets if int(f.flags) == 0), mesh.face_sets[0])
        triangles = faces.triangulate(uses_0xffff_separators=len(vertices) < 65535)
        if (triangles < 0).any() or (triangles >= len(vertices)).any(): raise ValueError("Invalid triangle")
        triangles = triangles[:, [0, 2, 1]].copy()
        triangles_total += len(triangles)
        # Zero-weight lanes must still reference an existing joint.
        mapped = np.zeros_like(joints)
        for row, column in np.argwhere(weights > 0): mapped[row, column] = remap[int(joints[row, column])]
        attributes = {"POSITION": glb.array(position, "VEC3", target=34962, bounds=True),
                      "NORMAL": glb.array(normal, "VEC3", target=34962),
                      "JOINTS_0": glb.array(mapped, "VEC4", 5123, target=34962),
                      "WEIGHTS_0": glb.array(weights, "VEC4", target=34962)}
        if "uv_0" in vertices.dtype.names:
            attributes["TEXCOORD_0"] = glb.array(vertices["uv_0"], "VEC2", target=34962)
        # Preserve alternate source UVs/vertex masks for material-specific
        # reconstruction. They are data, not assumed GTA lighting colours.
        for uv_index in (1,2):
            if f"uv_{uv_index}" in vertices.dtype.names:
                attributes[f"TEXCOORD_{uv_index}"]=glb.array(vertices[f"uv_{uv_index}"],"VEC2",target=34962)
        if 'color_0' in vertices.dtype.names:
            attributes['COLOR_0']=glb.array(np.clip(vertices['color_0'],0,1),'VEC4',target=34962)
        if "tangent_0" in vertices.dtype.names:
            tangent = vertices["tangent_0"].astype(float).copy()
            tangent[:, 2] *= -1
            tangent[:, :3] -= normal * (tangent[:, :3] * normal).sum(axis=1)[:, None]
            degenerate = np.linalg.norm(tangent[:, :3], axis=1) < 1e-8
            axes = np.tile([0., 1., 0.], (int(degenerate.sum()), 1))
            axes[np.abs(normal[degenerate, 1]) > 0.9] = [1., 0., 0.]
            tangent[degenerate, :3] = np.cross(axes, normal[degenerate])
            tangent[:, :3] /= np.maximum(np.linalg.norm(tangent[:, :3], axis=1)[:, None], 1e-8)
            tangent[:, 3] = np.where(tangent[:, 3] < 0, 1.0, -1.0)
            attributes["TANGENT"] = glb.array(tangent, "VEC4", target=34962)
        source_material = materials.get(material_key(mesh.material.mat_def_path), {})
        samplers = source_material.get("samplers", [])
        material = {"name": mesh.material.name, "doubleSided": True,
                    "pbrMetallicRoughness": {"metallicFactor": 0, "roughnessFactor": 0.65},
                    "extras": {"source_material": mesh.material.mat_def_path,
                               "layered_shader_recreated": False}}
        resolved = {}
        for role, token in [("base", "albedo"), ("normal", "normal")]:
            candidates = [s for s in samplers if token in s["type"].lower() and s["path"]]
            override = overrides.get(material_key(mesh.material.mat_def_path), {})
            if role in override: candidates.insert(0, {"path": override[role]})
            for sampler in candidates:
                texture = textures.get(PureWindowsPath(sampler["path"]).stem.lower())
                if not texture: continue
                key = (str(texture), role)
                if key not in image_cache: image_cache[key] = glb.image(texture, normal=role == "normal")
                index = image_cache[key]
                if role == "base": material["pbrMetallicRoughness"]["baseColorTexture"] = {"index": index}
                else: material["normalTexture"] = {"index": index}
                resolved[role] = texture.name
                break
        if any(word in mesh.material.name.lower() for word in ["hair", "fur", "butterfly"]):
            material["alphaMode"] = "MASK"; material["alphaCutoff"] = 0.25
        exported_materials.append({"name": mesh.material.name, "resolved": resolved,
                                   "source_shader": source_material.get("shader"), "samplers": samplers,
                                   "override": overrides.get(material_key(mesh.material.mat_def_path))})
        glb.doc["materials"].append(material)
        primitive = {"attributes": attributes,
                     "indices": glb.array(triangles.reshape(-1), "SCALAR", 5125, 34963),
                     "material": len(glb.doc["materials"]) - 1}
        mesh_index = len(glb.doc["meshes"])
        glb.doc["meshes"].append({"name": mesh.material.name, "primitives": [primitive]})
        glb.doc["scenes"][0]["nodes"].append(len(glb.doc["nodes"]))
        glb.doc["nodes"].append({"name": mesh.material.name, "mesh": mesh_index, "skin": 0})

    animations = []
    skeleton_binder = Binder.from_path(raw / f"{char}.anibnd")
    skeleton_entry = next((e for e in skeleton_binder.entries if e.name.lower().endswith("skeleton.hkx")), None)
    if max_animations and skeleton_entry is None: raise ValueError("Animation skeleton absent; resolve inherited binder")
    if max_animations:
        skeleton_compendium_entry = next((e for e in skeleton_binder.entries if e.name.lower().endswith(".compendium")), None)
        skeleton_compendium = HKX.from_bytes(skeleton_compendium_entry.get_uncompressed_data()) if skeleton_compendium_entry else None
        skeleton = SkeletonHKX.from_bytes(skeleton_entry.get_uncompressed_data(), compendium=skeleton_compendium).skeleton
        name_to_flver = {b.name: i for i, b in enumerate(flver.bones) if i in used}
        sources = [raw / f"{char}.anibnd", *sorted(raw.glob(f"{char}_div*.anibnd"))]
        for source in sources:
            binder = Binder.from_path(source)
            compendium_entry = next((e for e in binder.entries if e.name.endswith(".compendium")), None)
            compendium = HKX.from_bytes(compendium_entry.get_uncompressed_data()) if compendium_entry else None
            for entry in sorted(binder.entries, key=lambda e: e.name):
                animation_name = PureWindowsPath(entry.name).stem
                if not re.fullmatch(r"a\d+_\d+", animation_name) or not entry.name.endswith(".hkx"): continue
                if clip_names and animation_name not in clip_names: continue
                if len(animations) >= max_animations: break
                source_animation = AnimationHKX.from_bytes(entry.get_uncompressed_data(), compendium=compendium)
                container = source_animation.animation_container
                if container.frame_count < 2: continue
                decoded = container.to_interleaved_container() if container.is_spline else container
                decoded.load_interleaved_data()
                armature = decoded.get_interleaved_data_in_armature_space(skeleton)
                track_bones = decoded.get_track_bone_indices()
                mapped_tracks = {t: name_to_flver[skeleton.bones[b].name] for t, b in enumerate(track_bones)
                                 if skeleton.bones[b].name in name_to_flver}
                # Preserve every decoded source sample. Downsampling here permanently
                # discards motion before the GTA conversion even starts.
                frames = list(range(len(armature)))
                times = np.asarray(frames) * float(container.hkx_animation.duration) / (len(armature)-1)
                time_accessor = glb.array(times, "SCALAR", bounds=True)
                samples = {i: {"translation": [], "rotation": [], "scale": []} for i in bone_ids}
                for frame in frames:
                    animated = {i: rest[i].copy() for i in bone_ids}
                    for track, bone in mapped_tracks.items():
                        animated[bone] = BASIS @ armature[frame][track].to_matrix4().data @ BASIS
                    # FLVER-only auxiliary bones follow their retained parent.
                    done = set(mapped_tracks.values())
                    def resolve(i):
                        if i in done: return animated[i]
                        parent = flver.bones[i].parent_bone_index
                        if parent >= 0:
                            animated[i] = resolve(parent) @ np.linalg.inv(rest[parent]) @ rest[i]
                        done.add(i)
                        return animated[i]
                    for i in bone_ids: resolve(i)
                    for i in bone_ids:
                        parent = flver.bones[i].parent_bone_index
                        local = np.linalg.inv(animated[parent]) @ animated[i] if parent >= 0 else animated[i]
                        t, q, s = trs(local)
                        prior = samples[i]["rotation"]
                        if prior and np.dot(prior[-1], q) < 0: q = (-np.asarray(q)).tolist()
                        samples[i]["translation"].append(t); samples[i]["rotation"].append(q); samples[i]["scale"].append(s)
                animation = {"name": animation_name, "samplers": [], "channels": []}
                for i, channels in samples.items():
                    for path, values in channels.items():
                        kind = "VEC4" if path == "rotation" else "VEC3"
                        index = len(animation["samplers"])
                        animation["samplers"].append({"input": time_accessor, "output": glb.array(values, kind), "interpolation": "LINEAR"})
                        animation["channels"].append({"sampler": index, "target": {"node": bone_nodes[i], "path": path}})
                glb.doc["animations"].append(animation)
                animations.append({"name": animation_name, "duration": float(container.hkx_animation.duration),
                                   "source_frames": len(armature), "exported_frames": len(frames),
                                   "mapped_tracks": len(mapped_tracks), "semantic_role_verified": False})
                print(f"Decoded {char} {animation_name}: {len(frames)} frames", flush=True)
            if len(animations) >= max_animations: break
        if clip_names and set(clip_names) != {a["name"] for a in animations}:
            raise ValueError(f"Requested clips not exported: {set(clip_names) - {a['name'] for a in animations}}")

    position = np.vstack(all_positions)
    report = {"character": char, "gameplay_verified": False, "gta_ready": False,
              "source_bones": len(flver.bones), "exported_bones": len(bone_ids),
              "meshes": len(selected), "vertices": len(position), "triangles": triangles_total,
              "bounds_min": position.min(axis=0).tolist(), "bounds_max": position.max(axis=0).tolist(),
              "display_masks": sorted(masks) if masks is not None else "all", "include_unmasked": include_unmasked,
              "animations": animations, "materials": exported_materials,
              "limitations": ["Intermediate glTF only", "Layered materials approximated by available base/normal textures",
                              "Source root-motion track not reapplied separately", "Cloth, particles and runtime behavior absent",
                              "Animation role and visual fidelity await review"]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    glb.write(destination)
    with destination.open("rb") as stream: report["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    destination.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Exported {destination.name}: {len(position):,} vertices, {len(bone_ids)} bones, {len(animations)} clips", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--character", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--masks", nargs="*", type=int)
    parser.add_argument("--animations", type=int, default=3)
    parser.add_argument("--clip-names", nargs="*")
    parser.add_argument("--include-unmasked",action="store_true",help="Keep unmasked base meshes alongside the NPC display-mask selection")
    args = parser.parse_args()
    if not re.fullmatch(r"c[0-9]{4}", args.character): parser.error("Invalid character ID")
    if not 0 <= args.animations <= 20: parser.error("Choose 0-20 clips per bounded export")
    export(args.root.resolve(), args.character, args.out.resolve(),
           set(args.masks) if args.masks is not None else None, args.animations, args.clip_names,args.include_unmasked)
