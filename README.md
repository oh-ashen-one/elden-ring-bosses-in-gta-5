# Elden Ring Bosses in GTA 5

Fight **Malenia, Starscourge Radahn, Fire Giant and Godfrey inside actual GTA V Story Mode** using GTA guns, explosives, cars and helicopter weapons.

This is an open-source mod and local asset-conversion toolkit. The imported Elden Ring models, rigs and animation clips run inside GTA with custom GTA-side encounter behavior. The in-game mod is called **Elden Los Santos**.

## Current status

The core crossover has run on an **M3 Ultra through CrossOver with GTA V Legacy 1.0.3889.0**. Technical gameplay checks covered imported animation, native gun/car/Buzzard damage, attack contacts, stagger, defeat and reset. The owner subsequently reported that the playable build looked great.

The latest **2026-10-06 enhancement build** adds travelling fireballs, gravity-thrown traffic, police/SWAT/helicopter support, custom second phases, filming cameras and quick reset. Its Windows build and 23 offline test suites pass; **these new features still require the owner's in-game playtest**. They are not claimed as verified gameplay or original Elden Ring AI.

**Start here:** [Setup and build instructions](gta/README.md) · [Playtest guide and controls](gta/OWNER-TEST.md) · [Latest features and limits](gta/SPECTACLE-20261006.md)

## Bosses and encounters

| Boss | Encounter |
| --- | --- |
| **Malenia** | Original imported rig/clips, source-timed sword contact, stagger and defeat. |
| **Starscourge Radahn** | Dual-sword contact, with GTA traffic gravity throws in the new candidate. |
| **Fire Giant** | Enlarged to approximately 60 metres for helicopter-scale fights; the new candidate adds travelling fireballs and ground shockwaves. |
| **Godfrey** | Original imported axe animation/contact, with a custom second-phase ground shockwave in the new candidate. |

The mod runs one boss at a time. You can explore GTA between encounters; there is no ten-minute play limit. The new city-support and filming features are optional. Co-op is not included.

## What you need

- Your own **GTA V Legacy** and **Elden Ring** installations and locally supplied game assets.
- The compatible native ASI / Script Hook V setup described in the [technical guide](gta/README.md).
- The documented local conversion/build tools to produce your own private asset package.

The currently tested host is an M3 Ultra running Windows GTA V through CrossOver. This is a mod for the retail game, not a standalone game download or a native macOS port. The complete setup has not yet been reproduced on a second machine.

## Code and documentation

| Location | Contents |
| --- | --- |
| [gta/src/](gta/src/) | Native mod, combat, animation/root motion, damage, city support and filming controls. |
| [gta/asset-tools/](gta/asset-tools/) | Local extraction, rig/material/animation conversion and DLC packaging. |
| [gta/tools/](gta/tools/) | Guarded launch, package verification and reversible installation. |
| [gta/tests/](gta/tests/) | Native API, combat, collision, asset and installation regression checks. |
| [gta/OWNER-TEST.md](gta/OWNER-TEST.md) | Controls, precise test steps and rollback. |
| [HANDOFF.md](HANDOFF.md) | Current implementation state and outstanding owner review. |

## Fidelity and scope

We preserve imported source geometry, rigs and selected animations while adapting them to GTA's renderer and engine. GTA shading, hair/fur, cloth, collision and behavior differ from Elden Ring. This is not a one-to-one port of Elden Ring's renderer, complete boss movesets or AI. The new second phases and crossover abilities are our GTA-side encounter design.

## Open source and credits

Our original code is [Apache-2.0 licensed](LICENSE). Upstream components retain their own licenses and attribution; see [NOTICE](NOTICE), [UPSTREAMS.json](UPSTREAMS.json), [asset-tool credits](gta/asset-tools/README.md) and the [ER Mario implementation lessons](gta/ER-MARIO-LESSONS.md).

**Retail game files, converted models/textures/animations, generated motion data, motion-enabled binaries, vendor runtimes, saves and credentials are not distributed in this public repository.** Players supply their own game content locally.

This is an unofficial fan project, unaffiliated with Rockstar Games, Take-Two, FromSoftware or Bandai Namco.

## Earlier prototype history

This repository began as **Modern Warfare 2 AI**, exploring an MW2 Terminal airport crossover. That older prototype remains in the history and legacy folders, including `runtime/`, `crates/` and the [Terminal plan](docs/TERMINAL-PLAN.md), with its upstream notices intact. It is not the current GTA mod or its setup path. Other active crossover builds, such as Dark Souls × MW2, are separate projects; the [backlog and ownership notes](docs/CROSSOVER-BACKLOG.md) record that split.
