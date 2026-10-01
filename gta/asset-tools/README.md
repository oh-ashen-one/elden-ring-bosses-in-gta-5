# Elden Ring asset extraction (GPL-3.0-or-later)

These standalone conversion tools are separate from the Apache-2.0 GTA gameplay plugin. The C/Python adapters link to or import GPL libraries and are distributed under GPL-3.0-or-later; see LICENSE. Exceptions: CodeWalkerBridge, build_dlc.py and bootstrap_tools.py are original Apache-2.0 API/packaging adapters, as stated in their source headers and the root LICENSE. No proprietary assets, game libraries, archive keys, or converted models are distributed here.

## Verified on the Studio

- Original PC Elden Ring archives remain read-only.
- Selective Data3 extraction succeeded for Malenia (c2120), Red Wolf of Radagon (c3181), and Giant Crab (c2270): models, animation binders including Malenia's split binders, and high-resolution texture binders.
- Source headers and each output are recorded with SHA-256 hashes in a LOCAL extraction manifest.
- Native Mac Python can parse Malenia's FLVER and Havok skeleton. A compressed animation was decoded with its companion Havok compendium.
- Exported all three characters to rigged glTF with four source clips each in the current candidate. Latest interchange files have zero errors/warnings in Khronos glTF Validator 2.0.0-dev.3.10. This verifies format structure, not visual fidelity or gameplay.
- Data-only Blender 5.2/Sollumz conversion created local editable .blend files and GTA CodeWalker XML. Malenia converted to native YDR/YCD and loaded back through CodeWalker.Core: 96 bones and four clips preserved. Red Wolf and Crab native resources also round-trip, with 138 and 53 bones and four clips each. All three include whole-body collision boxes with an animal collision material.
- None of this establishes in-game compatibility. No game, renderer or gameplay/performance test was launched. Materials are approximations, collision is coarse, animation roles need review, and DLC packaging/runtime integration remain in progress.

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
