# Elden Ring asset extraction (GPL-3.0-or-later)

These standalone conversion tools are separate from the Apache-2.0 GTA gameplay plugin. They link to or import GPL libraries and are distributed under GPL-3.0-or-later; see LICENSE. No proprietary assets, game libraries, archive keys, or converted models are distributed here.

## Verified on the Studio

- Original PC Elden Ring archives remain read-only.
- Selective Data3 extraction succeeded for Malenia (c2120), Red Wolf of Radagon (c3181), and Giant Crab (c2270): models, animation binders including Malenia's split binders, and high-resolution texture binders.
- Source headers and each output are recorded with SHA-256 hashes in a LOCAL extraction manifest.
- Native Mac Python can parse Malenia's FLVER and Havok skeleton. A compressed animation was decoded with its companion Havok compendium.
- None of this establishes GTA asset compatibility or in-game gameplay. Conversion to GTA formats, material adaptation, animation retargeting and collision still require implementation/verification.

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
