# Elden Ring asset extraction (GPL-3.0-or-later)

These standalone conversion tools are separate from the Apache-2.0 GTA gameplay plugin. The C/Python adapters link to or import GPL libraries and are distributed under GPL-3.0-or-later; see LICENSE. Exceptions: CodeWalkerBridge, build_dlc.py, normalize_dds.py, dlc_manifest.py, upgrade_visuals.py, bootstrap_tools.py and rebuild_animation.py are original Apache-2.0 adapters, as stated in their source headers and the root LICENSE. No proprietary assets, game libraries, archive keys, or converted models are distributed here.

## Animation pose repair

`rebuild_animation.py` rebuilds private animation XML from existing source glTF poses and a target drawable's bind skeleton. The converter's source and target bones can have different rest axes; preserving names and counts alone does not preserve animated skinning. The repair maps source world poses through each bone's constant rest-axis correction, then derives target local translation, rotation and scale tracks. It refuses existing output files and mismatched bind positions.

CodeWalker's native compact static-quaternion channel stores XYZ and reconstructs positive W. The adapter flips all four components of a constant negative-W quaternion together, preserving its rotation; near W=0 it stores four explicit float channels to avoid reconstruction precision loss. Native read-back must compare actual channels with the intended values, in addition to checking clip counts and resource types.

```sh
python gta/asset-tools/rebuild_animation.py \
  --glb /private/source.glb \
  --drawable /private/creature.ydr.xml \
  --template /private/creature_anims.ycd.xml \
  --out /private/new-output/creature_anims.ycd.xml
```

This data-only operation does not run Blender or a game. Its output still needs native conversion and resource validation before private packaging. It preserves the motion available in the glTF: old exports omitted alternate source frames, and interpolation cannot recover them. The exporter now retains every decoded source sample for a future full-rate rebuild. Numeric pose agreement and native resource checks do not establish visible motion, strike timing or gameplay acceptance.

Future `build_owned_assets.py` runs invoke this repair after material conversion and before DLC packaging, preserving the Blender-exported animation XML as a diagnostic source. The full extraction/Blender pipeline was not rerun during the lightweight 2026-10-02 audit.

## Verified on the Studio

- Original PC Elden Ring archives remain read-only.
- Selective Data3 extraction succeeded for Malenia (c2120), Red Wolf of Radagon (c3181), and Giant Crab (c2270): models, animation binders including Malenia's split binders, and high-resolution texture binders.
- Source headers and each output are recorded with SHA-256 hashes in a LOCAL extraction manifest.
- Native Mac Python can parse Malenia's FLVER and Havok skeleton. A compressed animation was decoded with its companion Havok compendium.
- Exported all three characters to rigged glTF with four source clips each in the current candidate. Latest interchange files have zero errors/warnings in Khronos glTF Validator 2.0.0-dev.3.10. This verifies format structure, not visual fidelity or gameplay.
- Data-only Blender 5.2/Sollumz conversion created local editable .blend files and GTA CodeWalker XML. Malenia converted to native YDR/YCD and loaded back through CodeWalker.Core: 96 bones and four clips preserved. Red Wolf and Crab native resources also round-trip, with 138 and 53 bones and four clips each. All three include whole-body collision boxes with an animal collision material.
- These offline conversions do not establish in-game compatibility. Owner testing confirmed the guns/helicopter, but creatures failed and a crab request preceded a crash. The current texture-format repair is awaiting owner retest; materials, collision, animation roles and combat remain unverified.

## Dependencies and provenance

- [souls-formats-c](https://github.com/soarqin/souls-formats-c), GPL-3.0-or-later, pinned `a01057b3bf7554bfdaaf69376b2e605e93aa9d39`; linked only into er-extract.exe. This is a pre-alpha library.
- [BinderKeys](https://github.com/JKAnderson/BinderKeys), Apache-2.0, pinned `b95a32c509e35e5b18306c1d37a7778ea4034f38`; public archive-format resources are fetched separately and kept outside published sources.
- [Soulstruct](https://github.com/Grimrukh/soulstruct) 2.6.0 and [soulstruct-havok](https://github.com/Grimrukh/soulstruct-havok) 1.5.0, GPL-3.0-or-later; native Python parsing.
- The owned game's `oo2core_6_win64.dll` is loaded by the standalone helper through CrossOver. It is never copied into a release.
- Character IDs checked against [ER-Documentation](https://github.com/vawser/ER-Documentation/blob/main/Info%20-%20Chr%20IDs.txt).

The original Mac orchestration script works around two observed integration issues: CrossOver's Windows CNG path returned a raw-RSA crypto error, so BHD5 public-key decoding occurs natively on macOS; the pinned C library's generic 64-bit filename helper widens a 32-bit hash, so our helper computes Elden Ring's full 64-bit 0x85 polynomial and calls the explicit hash lookup. No upstream source was modified.

Use a separate task-owned CrossOver bottle named ERGTA-Tools for the console helper. Do not install games, log into accounts, or change the Steam bottle for conversion.

## Extraction command

With the pinned helper built, dependencies in `.cache/gta-tools`, and a Python environment containing `requirements-mac.lock`:

```sh
python gta/asset-tools/extract_characters.py \
  --game '/path/to/ELDEN RING/Game' \
  --out assets/private/eldenring \
  --keys .cache/gta-tools/BinderKeys/EldenRing_PC \
  --helper build/asset-tools/er-extract.exe \
  --characters c2120 c3181 c2270
```

The output must be separate from the game installation. Existing outputs are reused only when they match the recorded digest. If an archive changes, use a new output directory. Never publish the output directory.

## Additional private conversion dependencies

- Sollumz (GPL-3.0-or-later), pinned `82817d1211e7769bf3b9eb45866b6f8b802864fe`; szio 1.4.0.dev1 (MIT), installed only into the task's isolated Python path.
- CodeWalker.Core, pinned `485d56bec00262ed7fa472261cce7bbc6202b96e`: separately obtained/built in the ignored tool cache. No root license was found in the inspected repository. Its code and binaries are NOT copied into our published source or distributed/relicensed by this project. The original C# adapter calls its public conversion API locally.
- Portable Microsoft .NET SDK 10.0.401 (macOS arm64) was installed into the ignored tool cache from Microsoft's official download, without changing system PATH or accounts.

`export_character_glb.py` is the rigged interchange converter. `blender_to_gta.py` runs in background/factory startup without rendering or saving user preferences. `CodeWalkerBridge` converts XML to native GTA resources and checks a format round-trip. Binary/output receipts explicitly set `gta_runtime_verified` to false.

All .blend, .glb, .dds, .ydr, .ycd and game-derived metadata stay under the ignored private asset directory. They are not redistributable project source.

## Animated creature archetypes

The DLC packager declares `Dynamic | Has Anim (YCD)` (131584), links each clip dictionary and embedded texture dictionary, and sets `physicsDictionary` to the model name for embedded YDR collision. It does not mark moving creatures as static scenery. The native round-trip verifier checks these bindings, not just the archetype count. Sources: [Sollumz archetype flags](https://docs.sollumz.org/documentation/archetype-definition.ytyp/archetype-flags) and [CodeWalker embedded-bound binding](https://github.com/dexyfex/CodeWalker/blob/485d56bec00262ed7fa472261cce7bbc6202b96e/CodeWalker/Project/ProjectForm.cs#L3480). These format checks do not establish a successful GTA spawn.

## Texture-format regression found during owner testing

The v2 native YDRs contained 11 invalid texture format enums (zero): Malenia 4/10 textures, Wolf 4/6 and Crab 3/6. CodeWalker’s pinned `DDSIO.GetTextureFormat` maps UNORM DXGI formats, but its sRGB variants fall through to zero. The old skeleton/count round-trip check did not catch it. See [the importer mapping](https://github.com/dexyfex/CodeWalker/blob/485d56bec00262ed7fa472261cce7bbc6202b96e/CodeWalker.Core/GameFiles/Utils/DDSIO.cs#L479).

`normalize_dds.py` now normalizes only the equivalent DDS header format in a separate packaging copy, preserving compressed pixels and mip bytes. It validates dimensions, single-image layout and mip payload length, and rejects unmapped formats. `CodeWalkerBridge` rejects unknown GTA texture formats, empty dimensions/mips and missing/truncated base texture data both before writing and after native round-trip. All 22 embedded textures in v3 pass. Five synthetic regressions plus rejection of the actual original Malenia input were checked; no game was launched for this repair.

The captured crash is an access violation in Wine’s `RtlVirtualUnwind2` during the loading interval. That alone does not prove the first engine fault or establish that fixing textures resolves all creature compatibility issues. The malformed native texture enums are independently confirmed and corrected. Keep raw minidumps private.

## Prop registration (v5)

The owner-triggered v4 test proved that the full native spawn call creates/deletes the stock reference object (handle 2050), while Malenia still returned zero after model/animation streaming. This isolates the remaining failure to the custom asset path. The DLC request lacked `<contents>CONTENTS_PROPS</contents>`, present in the [prop-pack declaration reference](https://gist.github.com/Stuyk/44a717390854b2a0614c868efab200fa). v5 adds only this declaration to `content.xml`: plugin, nested native asset RPF, models, textures, skeletons and clips are unchanged. The native archive verifier also confirms all seven entries are resource entries with the correct Legacy versions (YDR 165, YCD 46, YTYP 2). The new manifest validator rejects the prior missing classification and files not enabled at startup. Gameplay retest determines whether this is sufficient.

## Import isolation tools

`build_import_diagnostics.py` (original Apache-2.0 adapter) produces private variants of the same owned Malenia source: static/dynamic archetype flags, collisionless, and unskinned/default shader. It preserves original inputs. The static animated variant includes a default clip alias matching its model hash, following [CodeWalker's default-clip lookup](https://github.com/dexyfex/CodeWalker/blob/485d56bec00262ed7fa472261cce7bbc6202b96e/CodeWalker/Rendering/Renderer.cs#L3688). This is a diagnostic tool, not a verified game conversion. Its outputs must stay private.

## Runtime result: Dynamic archetypes

On 2026-10-01 the bounded owner-approved import test created the complete Malenia variant with flags 131584 repeatedly; the original flags 512 and static/animated variants returned zero. Stock GTA objects also succeeded, isolating the issue from the native invocation layer. The production packager now includes Dynamic (131072) alongside Has Anim (512). Setting entity dynamics after a failed creation cannot repair the archetype used by that creation. v7 preserves the six original native mesh/animation files byte-for-byte and changes the three archetype flags. This native creation evidence does not itself prove visual fidelity or combat.

## Object material repair (v8)

The owner confirmed v7 assets appeared and bullets reduced health, but reported crumpled shapes, bald Malenia and poor image detail. The initial converter selected `ped_default.sps`, whose extra pedestrian palette/volume/body-shaping inputs were left unbound. `upgrade_visuals.py` instead selects the generic `normal_spec` skinned-object layout, generates unit tangent bases, and preserves the original geometry, weights, indices, UVs, skeleton and animation XML. This is a candidate repair; shader selection alone is not proof that deformation is resolved in GTA.

The original HairLong material references the shared PCHair normal/opacity atlas. The earlier fallback borrowed `c2120_hair2_a`, an unrelated 512-square atlas. The repair uses the referenced 2048×1024 atlas and local material tint parameters. ER packed normal RG is reconstructed into an RGB normal instead of interpreting its packed B/A material channels as XYZ. New maps retain source dimensions and receive complete RGBA8 mip chains; no artificial texture upscaling. Source textures stay unchanged. GTA specular response and shell-fur rendering remain approximate.

Run `upgrade_visuals.py --converted /private/old-gta-xml --root /private/extraction --out /private/new-gta-xml`, then package the new directory with `build_dlc.py`. The full owned-assets orchestrator now includes this step. For editable sources, retain both the original Blender scenes and the derived XML/script; these post-export material changes are not saved back into the old Blender scenes.

Schema references: [Sollumz shader conversion](https://github.com/Sollumz/Sollumz/blob/82817d1211e7769bf3b9eb45866b6f8b802864fe/ydr/shader_materials.py) and szio 1.4.0.dev1 `gta5/Shaders.xml`. Runtime motion telemetry uses the pinned native database already listed in `gta/native-contracts.json`; phase advancement is evidence of playback, not human acceptance of the pose or attack timing.

## Motion and ground contact review (2026-10-03)

`audit_motion.py` samples actual glTF joint transforms and reports motion landmarks without a renderer. Its outputs are private derived game data. Inspect poses as well as statistics; neither a speed peak nor a successful export proves a GTA damage contact.

The imported model front is -Y, so the runtime applies a 180-degree heading offset. Provisional melee contact times follow inspected source poses: Malenia 1150 ms, wolf 1350 ms, crab 900 ms. Playback acceptance failures suppress damage; per-strike logs expose engine phase and world coordinates for the owner test.

`align_ground_contact.py` adjusts the verified single-box collision floors to the inspected animated neutral geometry, keeping the matching runtime placement values. It preserves all drawable XML outside `Bounds`, source pixels, rigs, clips and render/culling bounds. A native reader confirmed the composite and child floors. Only 31–40 decompressed resource bytes changed in each existing YDR; the animation binaries are identical to the accepted pose repair. This improves the initial ground reference but remains a coarse collider, not original ER limb hitboxes. Terrain contact, physics and scale still require actual GTA review.


## Full-rate Malenia and root motion (2026-10-04)

`rebuild_animation.py --source-clips ...` creates the chosen clip list with each source sample and duration, while retaining the verified drawable bind rig. CodeWalkerBridge now compares every decoded native frame/channel with the XML input; successful counts alone are insufficient.

`export_motion.py` reads the owned HKX reference frames and the matching full-rate glTF. It keeps root motion separate from skeletal pose and samples the actual skinned sword endpoints. It validates source axes, duration and sample count, rejects turning/jumping moves outside this grounded runtime’s supported contract, and writes a **private** C++ header plus hashes. No Blender/game/renderer is used in this step.

```sh
python gta/asset-tools/export_motion.py \
  --raw /private/ergt-assets/raw/c2120 \
  --glb /private/ergt-assets/interchange/c2120.glb \
  --model ergt_malenia --weapon-mesh '#00#_Sword' \
  --clips a000_000020 a000_002100 a000_003000 a000_008030 a000_010000 \
  --out /private/ergt-assets/motion/malenia.hpp
```

The complete owned-assets orchestrator now generates that header. Pass its absolute path as `-DERGT_MOTION_HEADER=...` when compiling the Windows plugin. Neither the header nor that asset-bearing ASI may be published with the open-source code.

Malenia’s old death selection `a000_005000` is a turn, with a -90-degree reference-frame rotation and upright source poses. Inspected `a000_008030` recoils and recovers; `a000_010000` ends kneeling. Her run and attack contain metres of previously discarded root motion. These findings were checked against skinned source poses; actual GTA playback remains a separate required gate.

`align_ground_contact.py` also gives Malenia a conservative one-metre-wide torso box. The old rest-pose bounds included the extended sword and were nearly four metres wide. Her attack sweep now samples the weapon separately. Body boxes and victim capsules remain GTA-side approximations, not imported original ER hitboxes or Havok physics.


## Streaming failure follow-up

The owner test failed with ERR_GEN_ZLIB_2 while Malenia's model streamed. [Diagnosis](../CRASH-20261004.md) records the evidence and uncertainties. `rpf_audit.py` independently validates nested RPF7 bounds, extended resource lengths, actual raw-DEFLATE termination and declared page-memory sizes. `--max-resource-mib 32` is a conservative preview review budget, not a universal engine limit.

`optimize_textures.py` creates a new private input copy, prunes unreferenced Malenia textures and encodes generated RGBA maps as BC7 using pinned `ispc_texcomp==1.0.1`. Full dimensions/mips are retained; lossy error is measured. The gates reject normal-map p99 angular error above 3 degrees or alpha threshold-coverage change above 0.1 percent. The BC3 alternative failed on the actual body map and was not installed. No model, material binding, rig, clip, behavior or additional boss is changed by this operation. The full owned-assets recipe now applies this step to Malenia and audits the final archive. Runtime crash resolution and appearance still require the owner's test.
