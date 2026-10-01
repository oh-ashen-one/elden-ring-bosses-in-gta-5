# Elden Ring asset extraction (GPL-3.0-or-later)

These standalone conversion tools are separate from the Apache-2.0 GTA gameplay plugin. The C/Python adapters link to or import GPL libraries and are distributed under GPL-3.0-or-later; see LICENSE. Exceptions: CodeWalkerBridge, build_dlc.py, normalize_dds.py, dlc_manifest.py and bootstrap_tools.py are original Apache-2.0 API/packaging adapters, as stated in their source headers and the root LICENSE. No proprietary assets, game libraries, archive keys, or converted models are distributed here.

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

The DLC packager declares `Has Anim (YCD)` (512), links each clip dictionary and embedded texture dictionary, and sets `physicsDictionary` to the model name for embedded YDR collision. It does not mark moving creatures as static scenery. The native round-trip verifier checks these bindings, not just the archetype count. Sources: [Sollumz archetype flags](https://docs.sollumz.org/documentation/archetype-definition.ytyp/archetype-flags) and [CodeWalker embedded-bound binding](https://github.com/dexyfex/CodeWalker/blob/485d56bec00262ed7fa472261cce7bbc6202b96e/CodeWalker/Project/ProjectForm.cs#L3480). These format checks do not establish a successful GTA spawn.

## Texture-format regression found during owner testing

The v2 native YDRs contained 11 invalid texture format enums (zero): Malenia 4/10 textures, Wolf 4/6 and Crab 3/6. CodeWalker’s pinned `DDSIO.GetTextureFormat` maps UNORM DXGI formats, but its sRGB variants fall through to zero. The old skeleton/count round-trip check did not catch it. See [the importer mapping](https://github.com/dexyfex/CodeWalker/blob/485d56bec00262ed7fa472261cce7bbc6202b96e/CodeWalker.Core/GameFiles/Utils/DDSIO.cs#L479).

`normalize_dds.py` now normalizes only the equivalent DDS header format in a separate packaging copy, preserving compressed pixels and mip bytes. It validates dimensions, single-image layout and mip payload length, and rejects unmapped formats. `CodeWalkerBridge` rejects unknown GTA texture formats, empty dimensions/mips and missing/truncated base texture data both before writing and after native round-trip. All 22 embedded textures in v3 pass. Five synthetic regressions plus rejection of the actual original Malenia input were checked; no game was launched for this repair.

The captured crash is an access violation in Wine’s `RtlVirtualUnwind2` during the loading interval. That alone does not prove the first engine fault or establish that fixing textures resolves all creature compatibility issues. The malformed native texture enums are independently confirmed and corrected. Keep raw minidumps private.

## Prop registration (v5)

The owner-triggered v4 test proved that the full native spawn call creates/deletes the stock reference object (handle 2050), while Malenia still returned zero after model/animation streaming. This isolates the remaining failure to the custom asset path. The DLC request lacked `<contents>CONTENTS_PROPS</contents>`, present in the [prop-pack declaration reference](https://gist.github.com/Stuyk/44a717390854b2a0614c868efab200fa). v5 adds only this declaration to `content.xml`: plugin, nested native asset RPF, models, textures, skeletons and clips are unchanged. The native archive verifier also confirms all seven entries are resource entries with the correct Legacy versions (YDR 165, YCD 46, YTYP 2). The new manifest validator rejects the prior missing classification and files not enabled at startup. Gameplay retest determines whether this is sufficient.

## Import isolation tools

`build_import_diagnostics.py` (original Apache-2.0 adapter) produces private variants of the same owned Malenia source: static/dynamic archetype flags, collisionless, and unskinned/default shader. It preserves original inputs. The static animated variant includes a default clip alias matching its model hash, following [CodeWalker's default-clip lookup](https://github.com/dexyfex/CodeWalker/blob/485d56bec00262ed7fa472261cce7bbc6202b96e/CodeWalker/Rendering/Renderer.cs#L3688). This is a diagnostic tool, not a verified game conversion. Its outputs must stay private.
