# Elden Ring Bosses in GTA 5

[![Source checks](https://github.com/oh-ashen-one/elden-ring-bosses-in-gta-5/actions/workflows/checks.yml/badge.svg?branch=main)](https://github.com/oh-ashen-one/elden-ring-bosses-in-gta-5/actions/workflows/checks.yml)

Fight **Malenia, Starscourge Radahn, Fire Giant and Godfrey inside actual GTA V Story Mode** using GTA guns, explosives, cars and helicopter weapons.

This is an open-source mod and local asset-conversion toolkit. The imported Elden Ring models, rigs and animation clips run inside GTA with custom GTA-side encounter behavior. The in-game mod is called **Elden Los Santos**.

## Public source release

The core crossover has run on an **M3 Ultra through CrossOver with GTA V Legacy 1.0.3889.0**. Technical gameplay checks covered imported animation, native gun/car/Buzzard damage, attack contacts, stagger, defeat and reset. The owner subsequently reported that the playable build looked great.

The **v0.1.0 source release** includes multi-boss battles, travelling fireballs, gravity-thrown traffic, police/SWAT/helicopter support, custom second phases, filming cameras and quick reset. Publication was approved by the project owner on October 6, 2026.

**Verification scope:** the Windows mod compiles and 24 offline regression suites pass. The latest multi-boss/spectacle additions have not been independently verified in rendered gameplay; the complete setup has not been reproduced on a second machine. Those limits are documented without treating build checks as gameplay evidence.

**Start here:** [Getting started](GETTING_STARTED.md) · [Technical setup and build instructions](gta/README.md) · [Playtest guide and controls](gta/OWNER-TEST.md) · [Latest features and limits](gta/SPECTACLE-20261006.md)

## Bosses and encounters

| Boss | Encounter |
| --- | --- |
| **Malenia** | Original imported rig/clips, source-timed sword contact, stagger and defeat. |
| **Starscourge Radahn** | Dual-sword contact, with GTA traffic gravity throws in the source release. |
| **Fire Giant** | Enlarged to approximately 60 metres for helicopter-scale fights; the source release adds travelling fireballs and ground shockwaves. |
| **Godfrey** | Original imported axe animation/contact, with a custom second-phase ground shockwave in the source release. |

The mod removes the fixed boss-count restriction and lets bosses fight each other, including duplicates. Actual game capacity and performance still apply. You can explore GTA between encounters; there is no ten-minute play limit. The new city-support and filming features are optional. Co-op is not included.

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
| [HANDOFF.md](HANDOFF.md) | Implementation handoff and verification history. |

See the [compiled material audit](gta/MATERIAL-AUDIT-20261006.md) for the texture/shader feedback check.

## Fidelity and scope

We preserve imported source geometry, rigs and selected animations while adapting them to GTA's renderer and engine. GTA shading, hair/fur, cloth, collision and behavior differ from Elden Ring. This is not a one-to-one port of Elden Ring's renderer, complete boss movesets or AI. The new second phases and crossover abilities are our GTA-side encounter design.

## Open source and credits

Our original code is [Apache-2.0 licensed](LICENSE). Upstream components retain their own licenses and attribution; see [NOTICE](NOTICE), [UPSTREAMS.json](UPSTREAMS.json), [asset-tool credits](gta/asset-tools/README.md) and the [ER Mario implementation lessons](gta/ER-MARIO-LESSONS.md).

**Retail game files, converted models/textures/animations, generated motion data, motion-enabled binaries, vendor runtimes, saves and credentials are not distributed in this public repository.** Players supply their own game content locally.

This is an unofficial fan project, unaffiliated with Rockstar Games, Take-Two, FromSoftware or Bandai Namco.

## Earlier prototype history

This repository began as **Modern Warfare 2 AI**, exploring an MW2 Terminal airport crossover. That older prototype remains in the history and legacy folders, including `runtime/`, `crates/` and the [Terminal plan](docs/TERMINAL-PLAN.md), with its upstream notices intact. It is not the current GTA mod or its setup path. Other active crossover builds, such as Dark Souls × MW2, are separate projects; the [backlog and ownership notes](docs/CROSSOVER-BACKLOG.md) record that split.
