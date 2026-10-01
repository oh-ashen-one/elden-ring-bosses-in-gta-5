# Elden Los Santos

Original GTA V Story Mode mod code and a local conversion pipeline for owned Elden Ring creatures. Current characters: **Malenia, Red Wolf of Radagon, Giant Crab**.

**Status: guns/helicopter owner-confirmed; native-call repair awaiting creature retest.** v3 streamed all three models/animation dictionaries but GTA still returned zero object handles. Rechecking the owner-supplied universal-modder example for the same GTA 3889 build revealed an omitted eighth argument to `CREATE_OBJECT_NO_OFFSET`. A full audit found more missing trailing native arguments; v4 corrects them and adds regression checks against 72 pinned API signatures. Creature rendering/combat remain unverified. See the [owner guide](OWNER-TEST.md).

## What is implemented

- Original Windows x64 ASI: creature selection/spawning, up to three active creatures, health bars, native health-loss/hit-flag damage intake, custom melee/ranged/chase/stagger/enrage behavior, source-animation playback, reset, optional weapons and an armed helicopter.
- Offline asset extraction from owned Elden Ring archives, rigged interchange exports, textures/material adaptation, background data-only Blender/Sollumz conversion, native GTA resource conversion and DLC packaging.
- Twelve original animation clips, coarse collision, and a three-archetype local DLC. Assets, textures and game-derived metadata are private, not Git contents.
- A reversible APFS profile manager that keeps original retail bytes intact and scopes the Wine DLL override to GTA5.exe.
- Independent rule/ABI tests plus fixture tests for clone isolation and profile restoration. These checks do not prove game behavior.

## Build original code

Requires CMake and C++17. For the Windows target on Mac, install MinGW-w64 from Homebrew.

```sh
cmake -S gta -B build/gta-native -DCMAKE_BUILD_TYPE=Release
cmake --build build/gta-native
ctest --test-dir build/gta-native --output-on-failure

cmake -S gta -B build/gta-win64 -DCMAKE_TOOLCHAIN_FILE=tools/mingw.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build/gta-win64

# macOS/APFS synthetic fixture checks; does not touch real games or registry
python3 gta/tests/profile_test.py
```

Main output: `build/gta-win64/EldenLosSantos.asi`. The separate `EldenLosSantosProbe.asi` is a diagnostic using a GTA test actor; do not install both together because their hotkeys overlap.

## Rebuild owned assets

Read [asset-tool licenses, dependencies and limitations](asset-tools/README.md) first. On a Mac with CrossOver, Blender 5.2, Python 3.13+, Git, CMake and MinGW-w64:

```sh
python3 gta/asset-tools/bootstrap_tools.py
```

Create a separate accountless **ERGTA-Tools** Windows 10 64-bit CrossOver bottle for the console converters. The current Studio already has it. Then choose a **new output directory** and run:

```sh
.cache/gta-tools/asset-python/bin/python gta/asset-tools/build_owned_assets.py \
  --elden-game '/path/to/ELDEN RING/Game' \
  --gta-game '/path/to/Grand Theft Auto V' \
  --out '/path/to/private/ergt-assets'
```

This reconstructs local artifacts and does not launch either game. The dependency bootstrap and complete conversion orchestration were exercised on the Studio with a fresh asset output directory. The rebuilt DLC matched the installed candidate byte-for-byte. A separate-machine rebuild and actual GTA playtest remain unverified. Dependency revisions and downloaded runtime hashes are recorded in [dependencies.json](dependencies.json).

## Scope and publication

This adds selected authentic creatures and custom combat to GTA. It does not include Elden Ring's complete world, quests or original AI. The first encounter is a milestone toward an open-ended sandbox, not a ten-minute timer.

Original gameplay/profile code is Apache-2.0. The GPL conversion adapters and their dependencies keep their applicable licenses. Script Hook V, RageOpenV and CodeWalker are separately obtained tools; this repository does not redistribute their binaries. Refer to the upstream notices before redistributing anything built with them.

The local private DLC, game archives, DDS/GLB/Blend/native assets, runtime binaries, saves and account stores must not be committed or uploaded. Users need their own game installations. This unofficial fan project is not affiliated with Rockstar, Take-Two, FromSoftware or Bandai Namco.

## Studio launch coordination

After the owner-reported desktop crash, agent launches use `tools/launch_owner.py` with the actual current shared GPU protocol directory. It keeps exclusive GPU ownership until GTA exits, refuses other renderers/unknown GPU readings, and never relaunches a crashed game. `--check` is read-only. Coordinate with the other session first; `--owner-reservation` is only for its explicit PAUSED marker reserving the machine for Hari’s GTA test. It leaves that marker and other sessions’ jobs untouched. This path requests 1920×1080 windowed; it does not establish measured FPS or crash-free operation.

## Native API contract references

`native-contracts.json` records interface names and argument counts from [alloc8or’s native database at the audited revision](https://github.com/alloc8or/gta5-nativedb-data/blob/424fb51b089049a9fbcebcc641500b1d44d255b4/natives.json). `tests/native_contract_test.py` checks every constant-hash call in both plugins, and rejects the original seven-argument object-spawn call. The same-build cross-check is [universal-modder’s working GTA 3889 native wrapper](https://github.com/rehan-remade/universal-modder/blob/15d6f9d5fbd32de9b1884f29ddec3be9133bd912/examples/minecraft-gta5-passthrough/gta/src/natives.h).

That Minecraft demo runs Minecraft beside GTA and composites its frames, with native GTA collision proxies; it does not convert Minecraft mobs into native GTA models. Its native object-spawn signature and reference prop are useful interoperability evidence for our single-game asset import. We did not copy its two-game renderer or claim it verifies our Elden Ring import.

After an owner-triggered creature failure, v4 requests its known-working `prop_box_wood01a` once, creates it below the player and deletes it in the same tick. Only its result is logged; it is never kept or presented as a boss. This separates a general native object-creation failure from rejection of our custom assets without another diagnostic installation.
