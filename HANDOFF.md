# GTA V × Elden Ring handoff

Updated 2026-10-05. **Actual native combat checks completed; original assets with GTA-side behavior, ready for owner subjective review.** No full ER AI/moveset/renderer-parity claim.

## Ownership / current installation

- This original GTA thread owns `codex/boss-motion-polish` in `oh-ashen-one/modern-warfare-2-ai`. Task branch pushed; main merge not authorized. The default chat cwd is a different lane: use this authoring checkout explicitly.
- Owner explicitly authorized all remaining material, vehicle/helicopter, balance and defeat/reset work, actual M3 launches/captures and AppleScript/macOS input specifically for GTA. Other game/benchmark sessions remain untouched. SD migration/reminder remain cancelled.
- Verified host `Mac`, Mac15,14, M3 Ultra, console midir. Shared brain3be383eed864 refreshed from GitHub this session.
- Private bundle `~/Applications/EldenLosSantosPreview`; active profile `~/Library/Application Support/EldenLosSantos/Game`; original `Retail` sibling. GTA Legacy1.0.3889.0; retail exe SHA256677e4e355cfbdb13273b1d992407e3c261b3a108dc4dd5c8a0c4c1da651802e5 unchanged.
- Candidate `20261005-seated-state`; binary source `2fc89dea964a3396c9fc4022ef91b90c4650e523`; ASI SHA25624b8e9d6e4d467ff00cf0cb39bc5fec8ff1a5bfedbdbf5ddf4bbe5725fa276a9.
- DLC SHA25685d063521c99f4b2cb45f06c4b73b9aae2b8e0b065575b4cac406310a8d2ba53:66 resources,4 bosses/5 render pieces. Documentation commit can be newer; installed manifest records both source and binary source. `verify_candidate --source` requires metadata matching HEAD.
- Latest binary install backup `Backups/upgrade-20261006T004150Z-2120b165`; prior full asset update `upgrade-20261006T002003Z-7a309e23`; original October4 owner-working rollback `upgrade-20261005T194303Z-c8c633d6`. Preserve all rollback until acceptance.
- Never publish retail/converted assets, generated motion headers, motion-enabled ASI, vendor binaries, saves or raw game logs. Public source/conversion tools remain original code with upstream notices.

## Current improvements

- Restored missing Malenia helmet/armor, corrected double-reversed faces, original rest axes/global skin indices, distinct skeleton cache IDs and the giant's255/147-bone synchronized pieces. No vertex decimation or custom Blender animation; original clips/rigs retained.
- Source colour/normal payloads retained where compatible. Derived maps are full-resolution lossless BGRA. Fur UV2 opacity/normals, authored alpha-test thresholds and mip coverage are adapted for the GTA material. Malenia's omitted `c2120_hair_shadow_1m` UV1 atlas is now used; overlapping UV islands average authored shadow values explicitly. GTA's lighting, fur/ghost shading and missing cloth simulation remain visible limitations.
- Fire Giant remains2.6× source size, approximately60m, with geometry/rig/clip/root/weapon translations, collision/reach and clearance scaled together. He needs a large open area. Movement respects conservative probes and can stop at buildings; no navigation around them.
- Malenia makes room using her original run when too close for her lunge, then recommits at6m. Source TAE windows/native playback phase still gate actual weapon sweeps. Repeated rockets cannot keep restarting a reaction: source stagger completes with a short resistance interval.
- Vehicle damage flags also include mounted weapon hits. Only current/recent physical contact adds kinetic damage/recovery; measured remote native HP loss survives even when GTA omits the generic weapon flag. Slow/parked contact is filtered. Occupancy uses actual seated state before treating a melee victim as a vehicle occupant.
- Corpse settling tolerates body-scaled terrain differences and requires750ms stable support after the source collapse; it preserves the supported position and releases the obsolete standing collider. Clear/respawn drains pending probes and owns both giant parts.
- Fixed technical commands in `encounter_review.hpp` stage an airfield, bounded native car/Buzzard/weapon actions and30-second frame sampling. They never set custom boss HP to manufacture a pass. Setup can exit a vehicle using a native task, expires, and restores original player position/heading/wanted state. These are controlled technical checks, not a human balance verdict.

## Actual runtime evidence

Private directory `Evidence/20261005-completion` in the bundle. Reports from individual candidates remain separate; failed setup files are not passing evidence.

| Check | Result / evidence |
| --- | --- |
| Materials/spawns | All4 render in actual GTA. `final-malenia-hair.png`, `final-radahn.png`, `final-godfrey.png`; giant in helicopter frames. Hair/cloth/spectral shading is still approximate; owner visual acceptance pending. |
| Car impact | `car-refined.log`: real Sultan collision caused369.66 plus39.85 HP damage and source stagger/pushback. Earlier run362.28+36.76 also observed. |
| Slow contact / stop | `creep-verified.log`: true contact for repeated samples at0.65m/s; Malenia stayed3600HP throughout and after stopping. Earlier parked-only setup left a gap and was correctly rejected as contact evidence. |
| On-foot guns/RPG | Real player-held carbine and RPG reduced bossHP. No artificial custom-HP writes. Source stagger and death played. |
| Malenia full resets | `run2-full-kill-resets.log` + `run2.log`:3 complete kills, source kneeling defeats, corpse settling, clear and fresh3600HP. Later changes keep the same clips/geometry and passed relevant source tests. |
| Outgoing attack contact | Malenia hit NPCs and the PLAYER at source phase~0.424, lowering playerHP150→123. Spacing refinement produced further phase-timed contacts. Giant moved tens of metres and hit NPCs plus occupied Buzzard206082 at phase0.46155 in `run4.log`. |
| Mounted weapons | Buzzard gun hash46b89c8e and rocket hashf8a3939f accepted and damaged the giant. `final-heli-gun.log`:14000→11510 during3s with zero false vehicle-impact events. These are actual mounted weapons commanded through the native API, not the earlier generic projectile probe. Keyboard throttle also raised the helicopter in the live run. |
| Giant defeat/reset | `run2.log`: mounted rockets killed him and full-health reset worked. Final candidate `final-giant-kill-settle.log`: player RPG killed entity47626, source collapse played, corpse_settled at tick163093492, then full14000HP reset (`final-giant-reset.png`). |
| Player death cleanup | One active helicopter fight ended with player death; the test correctly cleared owned boss/vehicle and vanilla hospital respawn followed. Cause of death not established; do not attribute it to a particular boss hit. No game/computer crash occurred. |
| Source/native checks |21 CTest suites passed;11 asset-fidelity fixtures; native ABI, actual strike/observer/motion helpers tested.66 resources independently inflate. Packaging/tests alone are not a fight pass. |

## Performance / graphics boundary

Two30-second game-reported frame-time samples from the earlier `20261005-completion` candidate, one exclusive M3 game instance, captured1920×1080 window:

- Malenia:921 frames, mean32.614ms (~30.7FPS), p9537.249ms, p9944.459ms.
- Giant/Buzzard:808 frames, mean37.178ms (~26.9FPS), p9546.195ms, p9949.061ms.

These are not uncapped GPU benchmarks or a60FPS claim. Saved preferences read3440×2752, VSync2, SamplingMode0, while launcher/captures were1920×1080; do not infer exact internal scaling from the saved file. FXAA was disabled; it was enabled with a private backup at `Backups/graphics-20261005-fxaa/settings-before.xml`. Final FXAA rendered check passed (`final-fxaa-malenia.png`):937 frames in30s, mean32.068ms (~31.2FPS), p9536.263ms, p9939.571ms. Edges are smoother, while cloth/material differences remain. No other graphics field was changed.

## Private reproducibility

Under `SourceAssets/roster-20261005`:

- Current editable native input `gta-authored-hair-shadow`, package `dlc-authored-hair-shadow`, private motion header `motion-building-scale/bosses.hpp`.
- Preserve `gta-final-input` (original UV0/1/2/provenance), `gta-collision-origin` (corrected geometry/rig/collider baseline), `interchange-final`, raw/textures/material indices and current outputs. `ACTIVE-CANDIDATE.json` points at installed inputs.
- Pinned dependencies in `gta/dependencies.json` and `asset-tools/requirements-mac.lock`; CPU environment `~/Library/Caches/EldenLosSantos/roster-python-20261005/bin/python`. Recreate compiler outputs using README commands/private motion-header argument after cache cleanup.
- Public orchestration now includes cutout and shadow conversion. A clean second-machine reconstruction remains unverified. Do not use old partial `dlc-collision-origin` or first `dlc-cutout-thresholds` attempts.

## Launch / owner handoff

- Actual shared coordinator `/Users/midir/sm2-n1/_scratch/gpu`; global hard cap2, GTA exclusive. Use the packaged guarded launcher,1920×1080 window/VSync. Foreign/emergency holds block. No automatic relaunch after crashes.
- Completion run4 closed normally, its owned PAUSED marker was released under the shared perf lock. The final FXAA run also closed normally; only this thread's exact reservation is released under the shared lock after guard exit. Final private receipt records closure/release.
- Controls:1 select,2 spawn,3 clear,4 aggression,5 carbine/RPG,6 Buzzard. Starts aggressive; one boss at a time. Key3 keeps the owner's usable helicopter. The technical review uses separately owned temporary vehicles.
- All technical setup/firing requests must be consumed/cleared before handoff. No delayed run or reminder is authorized/queued.
- Ready for owner judgment of appearance, controls and difficulty. Full ER AI/movesets/phase2, native cloth/VFX/audio, exact shader parity, a formal whole-roster balance pass and measured60FPS remain unclaimed. Radahn/Godfrey received rendered-spawn checks, not the same complete encounter coverage as Malenia/Fire Giant.

Detailed failure history remains in `gta/VISUAL-REPAIR-20261005.md`, `gta/CRASH-20261004.md` and Git history. This rolling handoff supersedes old launch/roster/candidate snapshots.
