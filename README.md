# Modern Warfare 2 AI

An open source experiment in combining **MW2, Minecraft, Skate 3 and Skyrim** through AI-assisted development.

**Current priority: Elden Ring bosses in GTA V**, fought with GTA guns and helicopter weapons. See the [active plan and crossover backlog](docs/CROSSOVER-BACKLOG.md). The earlier Terminal airport prototype is preserved for a later demo.

> **Status: Mac setup preview.** The imported engine builds as a native Apple Silicon executable. A setup app and tested mission/block rule modules are available. The four-game Terminal mission is not playable yet; real game data and runtime integration/testing are still required.

## GTA V × Elden Ring owner preview

Original source and setup tools are under [gta/](gta/README.md). The owner liked the previous playable build with imported bosses, source-timed attacks, GTA car/gun/Buzzard damage, defeat and reset. **The2026-10-06 candidate adds travelling fireballs, gravity traffic, police/SWAT/air support, custom second phases and filming/reset controls. These additions are built and checked offline; the owner will test them in GTA.** See the [feature boundaries](gta/SPECTACLE-20261006.md) and [owner guide](gta/OWNER-TEST.md). Rendering remains a GTA shader adaptation. Retail-derived assets, motion-enabled binaries and third-party runtime files are private.

## Mac setup preview

- Build the native app with `bash scripts/build-mac.sh`.
- Run original-code tests with `cargo test --workspace --locked`.
- The app checks your locally supplied game data and keeps Terminal launch disabled until the required MW2 zone headers are present.
- No game data is bundled or automatically downloaded. The builder/dragon/mission modules are not yet wired into a retail game session.

See [Mac setup](docs/MAC-SETUP.md), [verified build status](docs/BUILD-STATUS.md) and [upstream import provenance](docs/UPSTREAM-IMPORT.md).

## The idea: Terminal Playground

One map, one player, four sets of possibilities:

- **MW2:** the airport, gunplay, bots, HUD and combat.
- **Skate 3:** board movement, tricks and selected grind routes through the concourse and aircraft area.
- **Minecraft:** placeable blocks, ramps and barricades layered onto Terminal.
- **Skyrim:** an initial creature encounter and a spell or shout, with a dragon over the airport as a later visual target.

The proposed foundation is [2010 Rust Rewrite Mashup](https://github.com/chasmlol/2010-rust-rewrite-mashup), which already combines IW4L, skating and a Minecraft world. Its Minecraft building currently belongs to its Minecraft map; adding a block layer to Terminal is new work. Skyrim integration is also new work.

[Read the integration plan](docs/TERMINAL-PLAN.md).

The proposed first release is a **ten-minute solo Terminal run**: build a ramp, skate it, earn a dragon killstreak from tricks, then call the strike and extract. The [demo specification](docs/DEMO-SPEC.md) defines the build order, gameplay goals and release checks.

## Projects our work builds on

We credit the research, tools and implementations that make this direction possible. The pinned 2010 Rust Rewrite Mashup is imported under `runtime/`, retaining its source credits, licenses and notices. Other projects remain references unless the import record says otherwise.

| Project | Authors / maintainers | Intended role |
| --- | --- | --- |
| [IW4L](https://github.com/vladtrc/iw4L) | vladtrc and contributors | MW2 runtime, asset loading, gameplay and rendering foundation. |
| [2010 Rust Rewrite Mashup](https://github.com/chasmlol/2010-rust-rewrite-mashup) | chasmlol and contributors | Candidate starting implementation for MW2, Skate 3 and Minecraft together. |
| [Skate 3 Rust Engine](https://github.com/SK8-ENGINE/skate-3-rust-engine) | SK8-ENGINE and contributors | Skating, animation, collision and modding references. |
| [SkyCraft](https://github.com/chasmlol/SkyCraft) | chasmlol and contributors | Reference for interactions between Minecraft and Skyrim; its SKSE/Fabric bridge is not a drop-in IW4L module. |

Upstream authorship, licenses and notices are preserved alongside the code. The import record identifies the exact source revision and our changes. Credit here does not claim that we authored those projects.

## More projects we studied

These are additional references, not current dependencies:

- [San Andreas Unity](https://github.com/in0finite/SanAndreasUnity) — GTA San Andreas engine recreation in Unity.
- [SM64CoopDX](https://github.com/coop-deluxe/sm64coopdx) — Mario 64 multiplayer and Lua modding.
- [OpenGOAL](https://github.com/open-goal/jak-project) — Jak & Daxter decompilation, tooling and live code editing.
- [Daggerfall Unity](https://github.com/Interkarma/daggerfall-unity) — a Unity recreation with extensive mod support.
- [OpenMW](https://github.com/OpenMW/openmw) — Morrowind-compatible engine and world editor.
- [Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp) — Sonic Unleashed recompilation and modding.
- [universal-modder](https://github.com/rehan-remade/universal-modder) — modding workflows and a Minecraft/GTA V bridge example.
- [libsm64](https://github.com/libsm64/libsm64) — Mario movement/rendering as an embeddable library.

The [more-games plan](docs/MORE-GAMES.md) covers reusable adapters and an optional CrossOver route for Windows hosts on Mac.

The [source catalog](docs/SOURCES.md) records revisions, license observations, release links and video references. [UPSTREAMS.json](UPSTREAMS.json) is the machine-readable research snapshot.

## First milestones

1. Review the candidate base's component licenses, import eligible code with provenance, and establish a reproducible build on the intended host.
2. Load Terminal and verify MW2 combat and skating in the same session.
3. Implement placeable Minecraft blocks on Terminal with consistent collision and persistence.
4. Add one Skyrim creature and one spell through a documented local asset conversion path.
5. Verify that combat, skating, blocks and the new encounter interact correctly, then hand over a playable build for owner review.

The baseline compilation and setup app are complete. Rendered baseline verification and the integrated gameplay milestones remain pending game data.

## Open source and game content

Our original contributions are offered under [Apache-2.0](LICENSE). Existing third-party components retain their own licenses; our license does not relicense them.

This repository does not distribute proprietary game executables, maps, models, textures, audio, animations, ISOs or account data. Any needed commercial game content must be supplied locally by the user under the applicable terms. Converted game assets and caches remain local.

This is an unofficial fan project, unaffiliated with Activision, Infinity Ward, EA, Mojang, Microsoft, Bethesda or ZeniMax. Names and trademarks belong to their respective owners.

See [NOTICE](NOTICE), [the integration plan](docs/TERMINAL-PLAN.md) and [HANDOFF.md](HANDOFF.md) for provenance and current status.
