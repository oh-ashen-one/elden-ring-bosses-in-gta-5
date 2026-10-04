# GTA V × Elden Ring handoff

Updated 2026-10-04. This original thread owns the GTA crossover. **Malenia candidate installed; GTA remains closed; actual rendered encounter is NOT yet verified.**

## Authority and current launch hold

- Hari requested one convincing boss fight end to end, applying er-mario lessons, with this thread performing technical rendered gameplay checks before his final subjective playtest.
- After a read-only launch check found the shared emergency pause, Hari explicitly answered **“Keep working without launching for now.”** That is the current launch instruction. No game/renderer was launched in this update and no technical test is queued.
- Verified host: `midirstudio.local`, Mac15,14, Apple M3 Ultra, 256 GiB, console owner `midir`. Desktop accessibility was available after the reboot. Recheck before any future launch.
- Actual shared GPU root: `/Users/midir/sm2-n1/_scratch/gpu`. Its unchanged PAUSED marker says `23:42 auto-pause by health_monitor: WindowServer starved (gpu 100% ws_cpu 0)`. This predates the current boot. Do not clear/rename it, substitute another lock root, or stop another session's processes.
- GTA requires exclusive GPU use despite the global cap of two renderers. Use `gta/tools/launch_owner.py`, current host identity and the full shared safety protocol. Emergency pauses always block it. Keep 1920×1080 windowed/VSync. Never enter a crash/relaunch loop.
- Leave Midir's Dark Souls × MW2, Spider-Man, M5 benchmark, Unity and completed Minecraft × MW2 work alone. Do not create another thread or message another session without the required human authorization.

## Source ownership and publication

- Authoring checkout: `/Users/midir/Documents/Codex/2026-09-30/yo-take-a-look-at-this/modern-warfare-2-ai`.
- Task branch: `codex/boss-motion-polish`; remote `origin`, repository `oh-ashen-one/modern-warfare-2-ai`.
- The chat default cwd `/Users/midir/Documents/ChatGPT/combiing games` belongs to another lane. Always set this GTA workdir explicitly.
- Implementation commit: `b4ec51e94f11f07a4c18ffebdc45fd4724ec3494`. A subsequent handoff commit does not change the compiled runtime. Push this task branch in the same session; never merge/push main without explicit permission.
- Original public code only. Generated motion headers, motion-enabled ASIs, native DLCs, GLB/DDS/Blender files, game archives, saves and credentials remain private. The ASI now embeds derived motion samples and therefore is NOT an asset-free redistributable binary.
- ER Mario reviewed at `deltarooo/er-mario@ff6b9b2d44c7bb211ef289ebc500c3fd354c9a65`; no source/model/ROM code copied. See `gta/ER-MARIO-LESSONS.md` and `UPSTREAMS.json`.

## Installed candidate and rollback

- Candidate: `20261004-malenia-root-motion`.
- Private bundle: `~/Applications/EldenLosSantosPreview`.
- Active profile: `~/Library/Application Support/EldenLosSantos/Game`; preserved original: sibling `Retail`; state: `profile-state.json`.
- Windows Steam's `Grand Theft Auto V` directory in the CrossOver Steam bottle points to the active APFS profile. Account/client data remains internal. The SD migration was cancelled and the reminder deleted; do not recreate either.
- GTA V Legacy `1.0.3889.0`. Original executable SHA-256 remains `677e4e355cfbdb13273b1d992407e3c261b3a108dc4dd5c8a0c4c1da651802e5`.
- ASI SHA-256: `c1280e7863bc37c847e06caf4fb789a3a06a7d312cd86630ba6254c0ea55ef3d`.
- DLC SHA-256: `d547c9bf3390d86885ca10356e5018bf2b527596038ec6ffc416bc1b7828dc26`.
- Runtime marker: `loaded_root_motion_20261004_runtime_verification_pending`. It has not been observed in a game session.
- Reversible installation used `upgrade_profile.py`, the profile lock, stopped-game checks and six-payload verification. Both package/profile passed, with original executables unchanged. Full prior-candidate backup: `~/Applications/EldenLosSantosPreview/Backups/upgrade-20261004T063226Z-363f606e`.
- Guarded shortcut host names were corrected to `midirstudio.local`; the previous shortcuts are saved under that backup's `shortcuts/`. No shortcut was run.
- Installation receipt: `~/Library/Application Support/EldenLosSantos/update-receipt-20261004.json`. Final source-pointer and verification receipts use the same date. Preserve this and the older full rollback backups.

## What changed

- **Actual source discovery:** `a000_005000`, previously assigned as Malenia's death, is a 90-degree turn with upright poses. Skinned source-pose inspection identified `a000_008030` as a recoil/recovery and `a000_010000` as a kneeling defeat. Neither is an imported ER AI state machine.
- Malenia now uses five full-rate source clips: idle `a000_000020` (136 frames), run `a000_002100` (24), sword `a000_003000` (83), stagger `a000_008030` (41), defeat `a000_010000` (221). The other two creatures retain their earlier four clips each.
- Rest-axis-corrected YCD channels preserve the existing rig. The run and attack have separate HKX extracted motion (previously discarded). Native playback phase drives that horizontal root displacement; invalid/stalled/jumping phases cannot produce catch-up teleports. Run playback rate matches pursuit speed, including the below-half-health increase.
- Attack facing is committed. The upright entity frame is restored after impact recovery so pose/root/blade calculations agree. Native car physics gets its recovery interval before scripted movement resumes.
- Malenia's physical box now approximates her torso, one metre wide. The old rest-pose sword made it nearly four metres wide. Mesh, rig, materials, pixels and render/culling bounds are unchanged. This remains coarse bullet/physics collision, not original ER limb hitboxes.
- Three asynchronous overlapping sphere probes check each <=0.35 m scripted movement step. Pending, obstructed, invalid or stale results do not move her. An external impact or animation change invalidates an old planned move. There is no pathfinding around buildings.
- Malenia's sword sweep samples actual skinned sword endpoints at the native animation phase. Damage requires the provisional 1.03–1.36 second active window, advancing/playing/accepted playback, victim capsule or vehicle-box intersection, and line of sight. One hit per victim/vehicle per attack. Stalls/pause/phase jumps cannot bank a hit.
- Her generic GTA explosion attack is disabled. Wolf/Crab retain their old telegraphed GTA explosions; none is a travelling magic projectile. This is a grounded, single-attack Malenia encounter, not her full moveset or phase two.
- Heavy damage uses/restarts the 1.334-second source stagger. Defeated actors stop damage, retain physics until near-ground settling, then freeze and disable collision. Actual landing/corpse behavior is unverified.
- Clear drains pending shape tests before releasing slots. Failed deletion keeps ownership/slot and logs failure; key3 explicitly retries. Reused model handles are not controlled/deleted. Retargeting restarts the correct animation even if the combat state immediately re-enters the same attack.
- Previous parked-vehicle impact filtering and dense-traffic dedup fixes are included. Native gun/explosion/vehicle/Buzzard incoming damage still needs current-candidate runtime checks.

## Evidence and exact verification boundary

- **17 CTest suites passed**, including actual runtime-helper fixtures for pending/blocked/stale movement and blade misses, playback stop, phase jumps, pause and duplicate vehicle damage. Existing damage/ABI/launcher/update/pose/cleanup fixtures remain passing.
- Single-job Windows x64 ASI build passed with the private generated header. Source-only builds without that header deliberately refuse Malenia spawning.
- Native CodeWalker read-back compared **145,440 Malenia frame/channel values**, maximum component error `1.4901161e-7`; five animation/clip bindings survived. All three native models/resources and 35 textures passed packaging checks. This is not rendering proof.
- Private CPU-skinned pose sheets were inspected for the old turn, stagger and kneeling defeat. They are clearly labelled offline diagnostics, NOT GTA images. No current-candidate appearance, native contact/damage, FPS, complete encounter or subjective gameplay pass is claimed.
- Earlier v7 owner evidence: all three real creatures visible and bullet health loss, but crumpled/bald/low-quality/stationary appearance. Subsequent material/pose repairs have not yet been visually verified in GTA.
- Private evidence: `~/Applications/EldenLosSantosPreview/Evidence/20261004-root-motion`.

## Private editable inputs and reproducibility

- `SourceAssets/ACTIVE-CANDIDATE.json` points to `gta/root-motion-20261004`, `interchange/20261004/c2120-phase1.glb`, `motion-20261004/malenia.hpp` and `dlc-build/root-motion-20261004`. Old inputs were preserved.
- `export_motion.py` validates source axes, durations and full-rate frame correspondence. It rejects unsupported turning/jumping root data. It emits private motion/weapon samples and hashes; it does not bake root translation into the pose a second time.
- `rebuild_animation.py --source-clips ...` selects full-rate source clips against the existing bind rig. `CodeWalkerBridge` now validates every decoded animation channel, including compact quaternions and end frames.
- Build the plugin with `-DERGT_MOTION_HEADER=/absolute/private/malenia.hpp`. `build_owned_assets.py` generates this header during future full reconstruction. Current update reused the preserved model/material sources and did not run Blender, extraction tools or any renderer.
- Pinned Soulstruct 2.6.0 / Havok 1.5.0, CodeWalker/Sollumz revisions and requirements remain in `gta/dependencies.json` and `gta/asset-tools/requirements-mac.lock`. Read the conversion docs before rebuilding. Keep the proven native ASI/Script Hook V route.
- Preserve the decisive runtime import fixes: eight-argument CREATE_OBJECT_NO_OFFSET; CONTENTS_PROPS registration; Dynamic+HasAnim archetype flags **131584**; normalized texture formats; rest-axis-corrected tracks with canonical static quaternion encoding.

## Next work when Hari resumes runtime testing

1. Recheck current rules, Studio/console identity, desktop, process ownership and shared GPU protocol. Emergency hold must be released by its owner; no workaround lock root. Use the guarded launcher under an exclusive GTA reservation.
2. Verify exact installed candidate/marker, load the existing completed-tutorial Story Mode save, and inspect actual rendered Malenia close up: skin deformation, normals, hair/materials, scale and ground reference.
3. Inspect run/attack/root motion through the committed swing and recovery. Use `animation_sample` phase/rate/world-coordinate logs and `blade_contact` events alongside visible frames. Fix visible or timing failures, not just log assertions.
4. Verify guns, RPG/explosions, moving-car impact, parked-car no-drain, occupied-vehicle blade contacts and Buzzard weapons. Inspect actual stagger, airborne impact recovery, kneeling defeat, corpse settling and repeated clear/respawn. Check pause/retarget cancellation and destroyed-helicopter replacement. No claimed passing result yet.
5. Capture actual performance/stability under the reservation. Stop after the safety crash threshold. Once technical issues are resolved, ask Hari only for the final subjective gameplay/video-quality review.

Controls: **1 select, 2 spawn, 3 clear, 4 aggression toggle, 5 carbine/RPG, 6 Buzzard**. Combat starts ON. Up to three owned creatures; helicopter persists across clear. The future AI-memory interface remains an optional expiring advisory mailbox: local gameplay timing, movement and damage must never wait for network replies.

Historical per-candidate debugging notes and prior rollback hashes remain in Git history (previous full handoff at `bb643985f29c6172c51e3084b97f2fa37b4b4470`). This current handoff supersedes their stale launch/publication/install instructions.
