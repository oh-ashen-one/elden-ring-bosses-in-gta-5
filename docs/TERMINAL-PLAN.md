# Terminal Playground: integration proposal

## Owner direction

Combine MW2, Minecraft, Skate 3 and Skyrim in one playable space. The owner confirmed that **Terminal means MW2's airport map**, not an in-game computer or a launcher.

This document is a design proposal. No integrated build has been produced or tested.

## What the first scene could look like

Start in Terminal with the familiar MW2 weapon and HUD. Switch to a skateboard, follow a curated line through the concourse, place a small Minecraft ramp or barricade, and return to combat. A Skyrim creature enters the encounter; the player has one spell or shout in addition to their weapon.

A dragon approaching the glass terminal and aircraft is the later cinematic target. The first Skyrim implementation should be a bounded creature/attack test so that asset conversion, animation and damage can be verified independently.

## Proposed architecture

Use the 2010 Rust Rewrite Mashup as the candidate base, subject to component provenance and license review. Keep IW4L as the host runtime.

| System | Existing basis | Work required for Terminal |
| --- | --- | --- |
| Map and MW2 combat | IW4L's retail-data loader, gameplay and bots | Verify Terminal, spawns, match state, damage and restart on the chosen build. |
| Skating | The mashup's skating worker, collision adapter, retargeting and rail extraction | Verify Terminal collision and curated rails; preserve player health, weapon state and damage when entering or leaving board mode. |
| Blocks | The mashup's Minecraft world, items and hotbar | Add a sparse block layer to a fixed MW2 map, block placement/removal, shared raycasts/collision and local persistence. |
| Skyrim encounter | New integration, with SkyCraft as a design reference | Convert a locally supplied asset, adapt its rig/animations, and implement the creature's gameplay in the host runtime. |
| Spell or shout | New host-runtime gameplay | Add a bounded ability with cooldown, targeting, effects and damage/impulse rules. |

The target is one combined runtime. This proposal does not start four retail games and synchronize them.

SkyCraft runs Minecraft alongside Skyrim and links them with a Windows SKSE/Fabric bridge. It does not provide a complete Skyrim implementation we can insert into IW4L. A Skyrim asset provides appearance; its AI, abilities, animation behavior and quests do not automatically transfer with it.

## Upstream baseline and known gaps

The mashup documents MW2 gunplay, skating on maps, and a separate generated Minecraft world. Its recorded v0.3.2 release lists bot-related performance regression/stutter, bodies accumulating after death in skate mode, an invisible board on some maps and missing grind rails on Minecraft block edges.

Treat these as baseline checks. Public documentation and compilation are not proof of a working combined scene.

Reference: [mashup release](https://github.com/chasmlol/2010-rust-rewrite-mashup/releases/tag/v0.3.2), [skating adapter](https://github.com/chasmlol/2010-rust-rewrite-mashup/blob/main/docs/SKATE.md).

## Minecraft on Terminal

- Anchor a sparse voxel grid in Terminal's coordinate system with an explicit unit scale.
- Initially edit only player-placed blocks. Destructible original Terminal geometry is a separate feature.
- Validate placement against the player, spawn points and required traversal routes.
- Merge placed-block collision into walking, skating, weapon raycasts and creature queries.
- Refresh affected grind routes when blocks change, or deliberately restrict grinding to verified static routes in the first prototype.
- Save changes by map identity and content revision in ignored local artifacts.
- Keep original retail files read-only.

The first check is a small ramp and a wall: walk on them, skate on them, shoot around them, remove them, and reload them.

## Skyrim content

Use a user-supplied game installation for any proprietary content. Record the source and conversion tools without publishing the asset itself.

Begin with a single model and a few animation clips. Validate scale, axes, bone hierarchy, material conversion and collision before adding behavior. If a dragon is selected, flying, landing, hit reactions and targeting are separate implementation tasks.

SkyCraft is a useful example of damage/collision translation, but its Skyrim-specific plugin calls must be replaced with our host engine's systems. Full Skyrim quests, dialogue, NPC simulation and save compatibility are outside this first prototype.

## One player state

Use one authoritative player health/inventory/combat state across walking and skating. Switching movement controllers must not create a second invulnerable actor, lose damage, duplicate bodies or break restart.

Every hostile creature and spell must use the same targeting/damage conventions as the chosen host mode. Start offline with bots; extend network replication only after the local interaction loop works.

## Delivery stages and proof

| Stage | Deliverable | Required proof |
| --- | --- | --- |
| 0 | Licensed, pinned baseline and build instructions | Exact source revision, component notices, successful build and a rendered launch on the target host. |
| 1 | Terminal with walking, weapons, bots and skating | Spawn, movement, rails, damage in both modes, death and restart in a recorded local run. |
| 2 | A block ramp and wall on Terminal | Placement/removal, collision for each movement mode, weapon rays, persistence after reload. |
| 3 | One Skyrim encounter and one ability | Model/animation inspection, hit detection, attack/cooldown behavior, recovery and cleanup. |
| 4 | Combined playable slice | Repeat the complete loop, review frame times at declared settings, then obtain owner gameplay feedback. |

Current status: every stage is pending.

## Platform decision

IW4L documents native macOS support, while the mashup currently distributes a Windows x64 build and its skating conversion packaging is Windows-oriented. The intended heavy-work host is the verified Mac Studio.

First establish whether this exact combined fork builds and runs natively on the Studio, including its converter dependencies. Do not assume a Windows binary is usable on macOS or that base IW4L support proves the combined fork works. If a port or a separate Windows host is needed, report that concrete finding before changing the target.

Engine work must use a task-owned instance and the shared renderer-slot protocol.

## Recording idea

Show Terminal working, ask the coding agent for one visible addition, test it, then introduce the larger crossover. A proposed sequence is:

1. Skate a short airport line.
2. Ask for a placeable block ramp and use it.
3. Add the Skyrim encounter and test a spell during the same loop.
4. Show the real result, including remaining problems.

This is a proposed capture sequence, not footage we already have.

