# Material feedback and native binding audit

The owner's third-party feedback suggested checking diffuse names, specular settings, shader choice, mipmaps, compression and normal-map green-channel orientation. These are useful diagnostic categories, not proof of the current failure's cause or universal settings.

## Checked on the installed asset package

CodeWalker decoded the actual native YDR/YTD resources. The audit followed each native YTYP texture root through `gtxd.meta` from the packed DLC, compared sampler names with reachable native texture names, and compared source DDS dimensions/mip counts and shader vectors with the native results.

| Render piece | Shader instances | Texture references | Reachable textures |
| --- | ---: | ---: | ---: |
| Malenia |24|72|22|
| Fire Giant |27|81|59|
| Fire Giant secondary rig |27|81|59|
| Godfrey |44|132|84|
| Radahn |34|102|75|

**Result: all468 references resolve across156 shader instances.**240 native textures in56 YTDs; no missing references, missing parent dictionaries, source-DDS dimension/mip mismatch or shader-parameter drift. The giant's second rig intentionally shares its parent's dictionaries. DLC SHA256: `641824cb2c5093f8eaf6451699f47283692aa74c9dadc9e36df0e835b8ab4170`.

This proves those specific bindings and conversion properties, not rendered appearance. No GTA launch or texture rewrite was performed for this audit. Private detailed results are retained in the installed preview's `Evidence/20261006-material-battle-audit` directory.

## What the advice means for this pipeline

- **Grey surfaces:** missing diffuse bindings are one possible cause. Here the native bindings resolve. A texture may still be semantically wrong or poorly adapted despite resolving; UVs, vertex color and lighting also need actual visual inspection.
- **Shader:** the pipeline already uses `normal_spec.sps` plus cutout/alpha variants where needed. Albedo is in `DiffuseSampler`, with separate normal and derived specular maps. The original white-everywhere specular fallback was removed before this audit.
- **Specular settings:** current nonmetal intensity is0.35, with falloff45 for fabric/hair/fur and80 for skin; metal uses0.7/160. The multiplier acts on our already-low nonmetal specular map, so0.1–0.2/30 is not a universal correction. Changes should be compared on the actual material under consistent light.
- **Normal green channel:** flip only when the source/target tangent conventions require it. The pinned [Sollumz normal-map preview code](https://github.com/Sollumz/Sollumz/blob/82817d1211e7769bf3b9eb45866b6f8b802864fe/ydr/shader_materials.py) explicitly inverts green when displaying a GTA normal map in Blender. That preview conversion is not an instruction to invert every exported DDS again.
- **Texture names:** the material must resolve the name stored in the reachable YTD. A source filename may be different if the converter explicitly records that mapping. The audit checks both sides of the conversion.
- **Resolution/encoding:** shrinking everything to1K/2K or recompressing everything toDXT1/DXT5 would introduce loss and is not indicated by this audit. The existing supported encodings and source resolution are retained. `texconv` is a useful converter when a format actually needs conversion, not a cure for every grey material.

The correct next visual comparison remains the owner's real GTA playtest. Exact ER shader/cloth parity is not claimed.

## Reproduce the binding check

Use the external pinned CodeWalker dependency through our original `CodeWalkerBridge audit-materials` adapter, then `audit_material_bindings.py --native REPORT.json --converted PRIVATE_CONVERTED_FOLDER --dlc PRIVATE_DLC.rpf --out NEW_REPORT.json`. Inputs and detailed decoded game-resource metadata stay private. Synthetic fixtures test unresolved parents, sampler mismatches and vector drift.
