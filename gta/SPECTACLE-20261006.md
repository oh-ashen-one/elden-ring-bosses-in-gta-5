# Single-player city encounters —2026-10-06

Owner scope: implement the five proposed single-player improvements, exclude co-op, and **do not launch GTA for testing**. Work stays in the original GTA task on `codex/boss-motion-polish`. No renderer or GPU lock is needed for these source/build checks.

## Implemented behavior

| Feature | Runtime implementation | Boundaries |
| --- | --- | --- |
| Fire Giant aerial fight | Original source attack contact cues release visible moving boulders/fireball markers from the sampled weapon tip; asynchronous swept spheres govern motion and explosion-at-contact. Misses expire after6s. Ground attacks emit expanding contact waves. | Up to6 projectiles;38m/s requested movement with conservative per-frame/cast pacing. No homing, explosions at predicted targets, imported ER fire VFX, building destruction or new pathfinding. |
| Radahn gravity traffic | Original source attack winds up with velocity-controlled ambient cars; observed source contact releases ballistic throws toward a committed target position. |3 cars in phase1,5 in phase2. Current/player-occupied/mission/test vehicles excluded; no gravity/collision disabling, deletion or permanent state changes on ambient cars. City debris remains after reset. |
| City response | Police, SWAT and a police helicopter stream asynchronously, arrive from a road node, use native approach/exit/flight and shooting tasks. Boss object receives ordinary native weapon damage. |3 vehicles, at most7 peds, one attempt each per encounter. No wanted-level manipulation, fake boss damage or direct player targeting. Real native AI effectiveness remains unverified. |
| Second phase | One50% threshold transition, still vulnerable, with original reaction animation, visible label/light and faster source playback/cadence. Radahn throws more cars, giant releases a fan of3 shots, Godfrey adds a ground wave. |Custom GTA behavior; same5 imported clips per boss. No ER phase2 model/AI/full movesets. Malenia gains cadence, not a newly imported Waterfowl/Scarlet Aeonia attack. |
| Filming/reset |8 hides normal HUD while preserving boss health;9 cycles3 clipped camera positions and exits on movement/fire/menu/20s.0 clears owned effects/responders and restarts the same boss at its original anchor. |No recording/upload, slow motion, player teleport/heal, or world/save rollback. Owner helicopter preserved; an occupied support vehicle is released to GTA instead of deleted. |

## Integration and ownership

- `combat.hpp`: deterministic phase state/rates and source-duration scheduling. Actual outgoing contacts remain native-animation-driven.
- `spectacle.hpp`: pure cue, flight, deadline, camera-exit and radial-contact math.
- `spectacle_runtime.hpp`: native adapter, one encounter's bounded resources. No listener or new dependency. The existing ASI/ScriptHook and motion header remain in use.
- `encounter_plugin.cpp`: controls, source playback integration and reset anchor. A committed attack keeps its valid target so newly spawned support does not cancel every swing.
- Hashes/arity for new calls are checked against the already-pinned `alloc8or/gta5-nativedb-data@424fb51b089049a9fbcebcc641500b1d44d255b4`. Original code only; the native database is queried for API facts, not bundled.
- Cape candidate preserves both source cape surfaces; no model decimation, texture changes or replacement/custom Blender animations are introduced by this update.

## Checks and honest limits

The build and fixtures cover pending/invalid/stale collision results, no target-only explosion, projectile expiry, occupied/mission car exclusions, retained cleanup ownership on deletion failure, late-result draining, native responder tasks, camera exit and original-anchor reset. Production adapter code is compiled into the native-world fixtures, alongside the existing damage/motion/asset/profile tests.

Windows x64 compilation and source checks establish a candidate, **not a verified fight**. Actual flight/damage, gravity appearance, AI accuracy, cape visibility, camera placement, handling, audio and frame time require the owner's M3 playtest. Rollback preserves the previous accepted private package and untouched Retail executable. No retail-derived assets, generated motion header or motion-enabled binary are published.
