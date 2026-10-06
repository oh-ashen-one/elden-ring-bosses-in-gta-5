# Getting started

This is the public **source code and conversion toolkit** for Elden Ring Bosses in GTA 5. It is not a downloadable copy of either game, a standalone Mac game, or an installer with the bosses already bundled.

## 1. Get the current code

```sh
git clone https://github.com/oh-ashen-one/elden-ring-bosses-in-gta-5.git
cd elden-ring-bosses-in-gta-5
```

Use `main` for the published version or the `v0.1.0` tag for this release. The old `modern-warfare-2-ai` URL redirects to this repository.

## 2. Check the source without either game

Requirements: Python 3.13, CMake, and a C++17 compiler. These checks work on Linux/macOS and do not launch a game or renderer.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r gta/requirements-test.lock
cmake -S gta -B build/gta-native -DCMAKE_BUILD_TYPE=Release \
  -DPython3_EXECUTABLE="$PWD/.venv/bin/python"
cmake --build build/gta-native --parallel 2
ctest --test-dir build/gta-native --output-on-failure
```

The tests use synthetic fixtures. Passing them does not establish visual quality or performance in GTA.

## 3. Prepare your own private playable build

The documented host is **GTA V Legacy 1.0.3889.0 on an M3 Ultra through CrossOver**, in Story Mode. GTA Enhanced, GTA Online and a complete second-machine setup are not verified.

You need your own GTA V Legacy and Elden Ring installations, the pinned dependencies in [gta/dependencies.json](gta/dependencies.json), Blender/Sollumz and the external conversion tools. Follow [the technical build guide](gta/README.md) and [asset-tool instructions](gta/asset-tools/README.md).

The guarded full asset driver currently requires the documented shared GPU coordinator. The checked-in Studio shortcuts contain machine-specific paths/hostname and must not be treated as portable installers. This release exposes the conversion steps and tools; a universal installer is not included.

The asset driver produces these **private** outputs:

- `motion/bosses.hpp`: generated animation/contact data used when compiling the mod.
- `dlc-build/dlc.rpf`: converted boss models, materials, textures and animations.
- `newmods/common/data/dlclist.xml`: local DLC registration overlay.

Build the Windows mod with MinGW-w64 and your generated header:

```sh
cmake -S gta -B build/gta-win64 -DCMAKE_TOOLCHAIN_FILE=tools/mingw.cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DERGT_MOTION_HEADER=/absolute/path/to/private/ergt-assets/motion/bosses.hpp
cmake --build build/gta-win64 --target EldenLosSantos --parallel 2
```

The resulting `EldenLosSantos.asi` contains derived game motion data and must remain private. Obtain compatible Script Hook V and RageOpenV runtimes from the pinned upstream sources; they are not redistributed here. The complete local profile payload consists of `EldenLosSantos.asi`, `RageOpenV.asi`, `ScriptHookV.dll`, `dinput8.dll`, `newmods/dlcpacks/ergt/dlc.rpf` and the DLC-list overlay. The profile tools require a checksum manifest for that private package; see their CLI help and [verification guide](gta/README.md).

Keep original game files and saves backed up. The included APFS profile manager supports reversible staging/activation/restoration on macOS. It is not a Windows filesystem installer.

## 4. Play and report issues

Use **Story Mode**. The top-row keys are:

| Key | Action |
| --- | --- |
| 1 | Select boss type. |
| 2 | Add a boss, including duplicates. |
| 3 | Clear all bosses/effects. |
| 4 | Pause/resume combat. |
| 5 | Receive weapons/ammunition. |
| 6 | Place an armed Buzzard. |
| 7 | Toggle police/SWAT/helicopter support. |
| 8 | Toggle filming HUD. |
| 9 | Cycle camera views. Movement/firing restores the gameplay camera. |
| 0 | Reset the current boss lineup at its original spawn points. |

Start with two bosses in open space. The approximately 60m Fire Giant needs a much larger area. There is no fixed mod boss-count cap; the game's actual resource limits still apply.

For an issue, include the source commit/tag, GTA version, host/runtime, boss, exact steps and a short screenshot/video when relevant. Review logs before attaching them; do not upload credentials, saves or retail game files. See [test steps](gta/OWNER-TEST.md) and [known implementation limits](gta/SPECTACLE-20261006.md).

## What is public

Original mod/tool code, tests, docs and upstream attribution are public. Retail/converted assets, generated motion headers, motion-enabled binaries, vendor runtimes and saves are excluded. The repository also preserves an older Terminal prototype; its archived Mac setup release is not the GTA mod.
