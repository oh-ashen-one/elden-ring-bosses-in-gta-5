# Crossover priorities

Owner decision: 2026-10-01. GTA V × Elden Ring is the active first demo. Earlier Terminal work is preserved as a backlog item.

## 1. GTA V × Elden Ring — active

Target: a roughly ten-minute repeatable GTA V Story Mode encounter with an Elden Ring boss in Los Santos. Native GTA firearms, vehicle impacts and helicopter weapons must damage the boss. Give the boss attacks that can threaten the player on foot and in the helicopter, a visible health bar, defeat state, and restart/cleanup.

Proposed first boss: Malenia, subject to owner preference and a successful model/rig conversion test. A humanoid first boss reduces initial skeleton complexity; her complete Elden Ring behavior does not transfer automatically. Flight must remain an actual combat phase, with telegraphed ranged attacks and balanced damage.

### Build order

1. Locate the Windows GTA V Legacy and Elden Ring installations on the Studio. Resolve CrossOver/Rosetta and Steam/Rockstar sign-in. Verify an unmodified Story Mode launch in a task-owned setup using the shared engine slot protocol.
2. Verify a compatible Script Hook V/ASI loader against the exact GTA build. Prove native bullet, explosion and helicopter-weapon damage on a disposable test enemy.
3. Convert one locally supplied Elden Ring model and animation set; validate scale, rig, materials, hit regions and animation in GTA. Keep retail and converted assets out of Git.
4. Implement boss decisions, attacks, health/stagger, ranged threat, death and reset in the GTA host. Tune separate weapon damage channels so helicopter explosives neither fail to register nor erase the encounter immediately.
5. Build the ten-minute encounter: short briefing and ground fight, helicopter access and aerial phase, finish/reward, clean restart. Measure performance on the Studio and obtain owner gameplay feedback.

The Mac route is Windows GTA V through CrossOver. Neither the required mod loader combination nor this boss integration is verified on this machine. universal-modder is a workflow reference; its published Minecraft/GTA bridge does not supply an Elden Ring boss implementation. We do not need to run both retail games simultaneously for a converted boss plus GTA-hosted behavior.

Publish original mod code, build/setup instructions and eligible tooling as open source. Players provide their own game content; this is not a standalone redistribution of GTA V or Elden Ring.

References: [Script Hook V](https://www.dev-c.com/gtav/scripthookv/), [universal-modder](https://github.com/rehan-remade/universal-modder), [Sollumz](https://github.com/Sollumz/Sollumz).

## Backlog — not started

- **Elden Ring enemies × MW2 guns × Zombies:** ten-minute wave survival, ammo economy, escalating enemies, final boss and restart. Host engine remains to be selected; do not assume the reference video provides a complete implementation.
- **Terminal Playground:** preserve the existing native Mac setup/runtime foundation and mission rules. Minecraft construction, Skate 3 movement and Skyrim encounter; see TERMINAL-PLAN.md and DEMO-SPEC.md.
- **MW2 AC-130 × Minecraft:** gunship support, destructible blocks, distinct weapon calibers and a ground combat phase.
- **Line Rider × Zombies:** draw a rideable escape route while defending against waves; reference implementation provenance remains unverified.
- **JEV co-op companion:** goal selection layered over deterministic combat/navigation, with safe fallback when the service is unavailable.
- **Skyrim × Minecraft:** separate bridge demonstration, informed by SkyCraft.
- **Pokémon Emerald Arena:** reference for changing mechanics within an existing game; no code imported. https://github.com/GBurgardt/pokemon-emerald-arena
- Other famous-game combinations remain ideas until a host, asset route and bounded playable loop are selected.

## Ownership and parallel work

Owner confirmed this split on 2026-10-01:

- **This game-combines session:** the main GTA V × Elden Ring playable mod, Studio/CrossOver integration and verification, and the already scheduled post-download SD-card migration.
- **Midir dot:** separate crossover showcase builds; propose two feasible combinations, build one bounded playable demo first, keep the second queued. A Zombies-style Elden Ring enemies/MW2 guns demo is a candidate, not a confirmed implementation choice.
- **Additional sessions:** may inherit chat context, but use separate repositories for different host engines, or distinct worktrees and branches for reusable shared code. Never share a dirty working directory or a mutable game/mod profile.

A coordination brief was successfully sent through the supported task API to the dot conversation connected to its earlier Review game combines project task. Delivery is verified; acceptance, a new side-build task and implementation progress are not yet verified. No extra session was created from this thread.

Each showcase needs actual player input, one clear crossover interaction, a short objective and restart. Do not describe an unverified combination as never done before. Keep proprietary assets local, preserve upstream attribution, and verify performance/gameplay separately from successful compilation.
