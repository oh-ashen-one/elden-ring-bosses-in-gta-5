# ER Mario lessons applied to the GTA encounter

Reviewed [deltarooo/er-mario at ff6b9b2](https://github.com/deltarooo/er-mario/tree/ff6b9b2d44c7bb211ef289ebc500c3fd354c9a65) on 2026-10-04. This is a reference review: no upstream code, model or ROM asset was copied. It does not establish compatibility between its Elden Ring hooks and GTA/CrossOver.

| Reference lesson | Application here | Evidence boundary |
| --- | --- | --- |
| `engine_mario.rs` explicitly converts simulation matrices into the host character frame, accounting for handedness, scale and inverse character rotation. | Retain corrected per-bone rest-axis conversion. Separate HKX extracted root motion from the skeletal pose. Convert source `(x,y,z)` to GTA model `(x,z,y)`, then apply the actual entity heading once. Unsupported turning/jumping tracks are rejected. | Inspected skinned source poses and native animation channels. Actual GTA world/render agreement remains unverified. |
| Frame interpolation must reject discontinuous transforms. | Native playback phase drives motion; invalid/backwards/stalled phase does not advance it. Loop wrap is explicit; phase jumps and large steps are consumed without catch-up teleportation. | Synthetic discontinuity/wrap witnesses and actual runtime-helper fixtures pass. |
| `collision_geometry.rs` and `moving.rs` treat host collision and moving surfaces as part of the mechanic. | Three overlapping asynchronous sphere probes check each Malenia movement step. A pending, invalid, obstructed or stale result cannot move her; vehicle impact displacement wins over an old planned move. Her torso box no longer includes the extended rest-pose sword. | Tests exercise pending/wall/impact/stale cases. Native shape flags, slope behavior and traffic collisions require GTA inspection. |
| `combat.rs` connects the imported character's attack interaction to host-game damage behavior. | Malenia's active sword segment comes from actual skinned source vertices and native animation phase. Victim capsule/vehicle box intersection and line of sight precede GTA damage calls. Each victim/vehicle is hit once per attack. | Geometry/native-call fixtures pass. These are conservative GTA-side hit approximations, not ER hitbox/TAE or AI imports. |
| A visible character needs a coherent animation/state lifecycle. | Replace the wrongly assigned turn-as-death clip with the inspected kneeling defeat. Use a source stagger clip for heavy hits. Keep attack facing committed; drain shape-test handles and retain ownership on failed cleanup. | Source poses and code checks pass. Repeated complete encounters still require the guarded technical run. |

## Current Malenia content

- Five full-rate clips: idle `a000_000020`, run `a000_002100`, sword attack `a000_003000`, stagger `a000_008030`, kneeling defeat `a000_010000`.
- The old `a000_005000` selection remains available only in preserved private reference data; it is an upright turn, not the selected defeat.
- One committed melee attack, a provisional 1.03–1.36 second damage window, and faster pursuit below half health. No claim of her complete moveset, original AI or phase-two transformation.
- The generic telegraphed GTA explosion is disabled for Malenia. Wolf/Crab retain their previous behavior pending their own focused repair.
- GTA bullets, explosions and vehicles remain the incoming damage path. Their current-candidate engine behavior and balance are not established by fixture tests.

## Reproduction and next gate

The public repository contains original converters/runtime code and synthetic fixtures. Users generate the model, clips and motion header locally from their owned games. The generated header and a plugin compiled with it contain derived retail data and stay private.

The 2026-10-04 work used bounded CPU-only data conversion, native resource read-back and single-job builds. No game or renderer was launched. Hari chose to keep launches on hold while the shared coordinator remains emergency-paused. Once runtime work resumes, this original thread must inspect the actual rendered fight, repair visible/contact failures, and only then request Hari's final subjective playtest.
