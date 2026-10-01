# Terminal: ten-minute playable demo

## Release objective

Ship a public, reproducibly buildable open source prototype. Import only components whose terms permit the intended release, preserve their applicable licenses/notices, and offer original contributions under Apache-2.0. Players supply the required commercial game data locally.

The requested outcome is a ten-minute playable version that demonstrates AI-assisted changes to nostalgic games. The following is the proposed first-release scope, pending baseline feasibility and platform selection.

Current state: the imported engine compiles to an Apple Silicon executable; the native setup app and independent mission/block rules are verified. No retail game session or combined mission has been run.

## Signature loop

**Build a ramp with an MW2 weapon, skate the resulting route, earn a dragon killstreak from landed tricks, and call the dragon over Terminal.**

Use one map, one local player and bots. The dragon follows a bounded flight and fire-attack route for this first version. Its visual source, animation conversion and license requirements must be established before integration.

The minimum package contains:

- Terminal with reliable MW2 movement, weapons, bots and player damage.
- A builder mode for one weapon, with a short approved set of Minecraft blocks.
- Skating on both selected Terminal routes and player-placed block ramps.
- A visible trick-charge meter tied to confirmed landings.
- A Skyrim dragon strike with a cooldown/charge requirement and real effects on the encounter.
- A ten-minute run, clear objectives, a result screen, checkpoint recovery and restart.

Additional spells, extra maps, Minecraft mob waves, full map destruction and network multiplayer are extensions beyond this minimum.

## Target session

The times below are pacing targets within a ten-minute run, not prerecorded events the player merely watches.

| Approximate time | Player goal | Mechanic introduced |
| --- | --- | --- |
| 0–2 minutes | Clear a short concourse encounter and reach the builder pickup. | MW2 combat and the objective HUD. |
| 2–4 minutes | Build a ramp/bridge to a marked route near the aircraft. | Block placement, limited resources and collision. |
| 4–6 minutes | Complete a short skating line and bank tricks. | Skating and dragon-charge rewards. |
| 6–9 minutes | Defend the objective, build cover and finish charging the strike. | The combined loop under pressure. |
| 9–10 minutes | Call the dragon strike and reach extraction. | The visual payoff, win state and restart. |

The player can retry a checkpoint after death with a visible time cost. Reaching extraction completes the run. Running out of time produces an explicit failure result with Retry. Difficulty and route timing need owner playtesting.

## Build order

1. **Baseline gate:** pin the existing mashup, audit component provenance, prepare the required local game data, build it and run Terminal on the target host. Record actual controls and existing bugs.
2. **Core compatibility:** verify walking, combat, skating, camera transitions, death and restart before adding features.
3. **Builder weapon:** place a small block layer on Terminal. Validate walking/skating collision, weapon traces, removal and persistence.
4. **Dragon strike:** import/convert one locally supplied model and required clips, implement a fixed attack route, targeting and effects, then verify damage and cleanup.
5. **Trick reward:** connect confirmed trick landings to a capped charge meter. Bails, duplicate events and restart must not award charge.
6. **Ten-minute mode:** add objectives, pacing, checkpoints, result/retry flow, input prompts and audio feedback.
7. **Release pass:** repeat the complete session, profile the worst combined view, test a clean install using user-supplied data, and obtain owner gameplay feedback.

The source import and baseline build can proceed independently of feature art once component permissions are established. Runtime and asset-conversion checks require the original local game files.

## Completion evidence

- A successful clean build from the published revision.
- A setup path that asks for local game folders and identifies missing data clearly.
- A complete recorded run through objectives, dragon strike, result screen and restart.
- Damage remains active while skating; switches do not duplicate bodies or lose inventory.
- Built geometry agrees with collision for the player, skateboard, weapons and applicable NPCs.
- Tricks award charge once, and dragon effects respect the shared damage rules.
- Declared resolution/quality settings and measured frame times on the actual target machine.
- Owner review of controls, skating feel, difficulty and fun.

A video cold open is recorded from this same playable build. No generated shot substitutes for a gameplay feature.

## Public delivery

Publish source changes with upstream history/provenance, licenses, notices, build instructions, the data-import workflow, controls and known issues. Package a versioned executable for each platform actually tested. Keep proprietary maps, textures, audio, animations, executables and account information outside the public repository and downloadable build.

Project code being open source does not make the original game content redistributable.

## Prerequisites checked

The available development host was verified as an Apple M3 Ultra Mac Studio with 256 GB memory. Xcode and CMake are present. Rust/Cargo 1.98.1 were installed for this task.

The Steam library manifest and the standard Games folder checked on the Studio did not contain MW2, Skate 3 or Skyrim data. This is a bounded check, not a claim that no copy exists elsewhere.

Still needed from the owner:

1. Access to MW2 (2009 PC) multiplayer files, an extracted owned Skate 3 Xbox 360 copy, and Skyrim Special Edition data; or identification of which need downloading. Confirm Minecraft Java ownership as well; an upstream downloader is not evidence of the user's content rights.
2. First playable target: the Mac Studio, or an available Windows testing machine.
3. A compatible controller for skating review and a short owner playtest once the slice runs.

Mac is the selected first target. The full fork compiles for Apple Silicon, but its rendered game session still needs MW2 data and live verification.
