# Handoff

Updated: 2026-10-02 (owner authorized applying the staged repair; update preparation underway, game remains closed).

## Current owner instruction and update ownership

- Hari directly requested “update as much as possible” after the repaired candidate was staged. This authorizes the bounded active-profile/private-package update. The earlier “do not open it yet” still applies: **leave GTA closed** and keep other sessions' GPU reservations untouched.
- This thread resumed the original authoring checkout on its own successor branch `codex/apply-pose-repair`, based on audited local commit `21e528e`. The independent auditor's `codex/preplay-launch-safety` checkout is read-only input and is not being edited.
- The added `upgrade_profile.py` uses `profile.lock`, checks the exact six payloads and unchanged game executable, rejects running GTA, stages atomic replacements, preserves a rollback journal and verifies both destinations. No registry, account, save, retail archive or GPU protocol change is part of this update.
- Source remains local/private under the current no-publication constraint. Do not push this branch or merge a default branch without owner direction. Installation completion must be read from the local receipt and confirmed hashes, not this preparation note.

## Isolated pre-play repair status (prior audit)

- This checkout is `codex/preplay-launch-safety`, based on public/shared `codex/elden-assets-and-combat` commit `6a24a33dd13c8a56942fbc2c3b1b09a4d04ff6cd`. Changes are local and unpublished. The shared source checkout, active profile, retail game, saves and Steam configuration were not edited.
- Current instruction for this audit: lightweight source/data checks only while the other Unreal session has priority. Do not launch GTA/Elden Ring, acquire renderer slots, run full extraction/Blender conversion, install this candidate or publish. This supersedes the older open-after-install instruction below for this audit.
- Fixed stationary/unattributed vehicle contacts leaking native HP loss through the impact threshold. A test compiles the actual `observe_damage` function with fixture native events: ten parked/moving/bullet/explosion/cooldown scenarios pass; the original source fails the parked-contact witness.
- Fixed attack playback switching to idle at the strike: recovery now keeps the attack clip and lasts at least the remaining measured source clip duration. Combat OFF, stagger and defeat still change playback. Ten CTest suites pass, including synthetic rig-axis checks, and the small Windows x64 ASI builds with one job.
- Confirmed per-bone rest-axis conversion error in existing animation data. `rebuild_animation.py` derives GTA local tracks from source glTF world poses while preserving the target bind rig. Peer comparisons of 36 poses reduce worst RMS error from 1.19–2.08 metres to below 0.54 millimetres. An independent Malenia text rebuild matches the peer SHA-256 exactly. This is offline evidence; visible deformation is unverified.
- Native read-back also exposed compact static quaternions reconstructing positive W after storing only XYZ. The adapter now flips the entire constant quaternion when needed and retains four explicit floats near a half-turn. Six synthetic pose/encoding cases pass; all three corrected YCDs pass 10,332 sampled native channels with maximum component error below 4.4e-7. The first private animation/DLC candidate was rejected and preserved separately.
- The source exporter now retains every decoded frame. Existing v6 interchange data still omitted alternate frames, so repair from that data cannot restore the missing samples. Full-rate regeneration remains separate future work.
- Launcher checks now include native IW4L, Roblox and ArkWeb renderers and fail closed when process inventory cannot be read. `verify_candidate.py` checks private package/profile hashes, supported executable/version, source commit and helper agreement without loading a game or changing the profile. Both package agreement and native format round-trips require separate owner gameplay acceptance.
- The task workspace contains a separate private candidate and exact audit/patch receipts under `/Users/midir/Documents/Codex/2026-10-02/task`. The installed candidate remains `aggressive-visuals-v8`. Preserve the original ER/GTA data and keep all derived assets out of Git.

## Current priority and verified state

- This thread owns GTA V × Elden Ring. Midir owns Dark Souls × MW2. Keep those lanes separate.
- Repo: https://github.com/oh-ashen-one/modern-warfare-2-ai; branch `codex/elden-assets-and-combat`; draft PR #2 targets `codex/gta-damage-probe`. No merge permission.
- Chat default cwd points at another lane (`/Users/midir/Documents/ChatGPT/combiing games`). ALWAYS pass this GTA checkout as the working directory.
- All six games finished installing. Hari CANCELLED the slow SD-card migration; leave games internal. The task-owned partial copy was removed without removing source game files. Do not resume migration.
- The `move-steam-games-after-downloads-finish` automation was deleted at Hari's request. Do not recreate it.
- Latest standing instruction: **open GTA V Legacy after installing patches**, without asking again. Hari owns gameplay, rendering review and performance testing. Use the shared renderer slot and verified Studio desktop; do not interrupt active unsaved gameplay or enter a crash/relaunch loop. No tutorial/combat input automation is authorized.
- Hari now reports the tutorial completed. The previous window was saved at 800×600; he was given in-game window/resolution steps. Mac and Windows Steam both recognized DualSense; an empty GTA mapping was observed and Steam Input instructions supplied. Controller resolution is not independently confirmed.
- Actual GTA build is 1.0.3889.0. Script Hook V initialized successfully, registered and executed `EldenLosSantos.asi`; ASI loader also loaded RageOpenV. Earlier candidates failed creature creation after streaming. v7 created all three original creatures; Hari confirmed the assets are visible and bullets reduce their health. He reported crumpled shapes, bald Malenia, very poor quality and no visible movement. v8 below is the response; it is not visually/gameplay verified yet.

## Launch recovery after the computer restart

- Hari reported the previous GTA launch froze the whole computer. Live host boot time confirms a restart at 14:26:36 America/New_York. The prior launch receipt recorded GPU utilization at 100% before launch; using a second renderer at that load was inappropriate even below the old process cap.
- Root coordination error: the prior GTA helper locked `~/.cache/gpu-slot`, while active Unreal jobs use `/Users/midir/sm2-n1/_scratch/gpu`. Future GTA launches must share the ACTUAL current lock directory and be exclusive. Do not use the old private owner_launch.py helper (now retired).
- Also found GTA saved at 3440×2752, RefreshRate 0. Backed up its display settings locally, changed to 1920×1080 windowed, requested 60 Hz and retained half VSync. Launch flags pin 1920×1080. Actual FPS and full stability are unverified; keep this lower resolution for now.
- Hari authorized asking the Unreal session to pause. It is an external Claude session, unavailable through Codex task messaging. No message was sent through another terminal. Hari relayed the pause request himself; the coordinator stopped its renderer and wrote `owner opening GTA V 14:48 - renders paused; auto-lift after GTA5.exe exits` to its PAUSED marker. Only the null-RHI import remained; desktop-only GPU baseline was ~20%.
- New original `gta/tools/launch_owner.py` uses that protocol's existing exclusive perf.lock for the entire actual GTA process lifetime. Normal launch uses the protocol's 15%-for-10s idle gate; the explicit owner reservation supports the measured desktop baseline below 30% over 12 seconds, while admitting NO other renderer. It never clears/renames PAUSED, stops another process, raises the shared cap or auto-relaunches. An emergency/non-owner pause always blocks it. This reservation is not an FPS benchmark.
- Eight source-only launch guard tests pass, including the previous 97% GPU case, low-util live renderer, unknown GPU, logged-out desktop, stuck exiting headless engine and emergency pause. A current read-only check refused launch until the owner reservation existed and other rendering stopped.
- Lower-resolution v3 launch succeeded under that reservation at 14:53 America/New_York: GTA5.exe PID 50731, Script Hook initialization and DirectX initialization confirmed. A 20-second startup check sampled GPU values 0–31% (mostly 20–21%); desktop console remained midir. This is startup evidence, not sustained gameplay/FPS or creature verification. The exclusive slot remains held until the actual game process exits; the other coordinator owns its pause/auto-lift. Hari retains gameplay control.

## Current installed candidate: aggressive-visuals-v8

- Owner feedback: authentic assets are visibly in GTA and taking bullet damage, but appear crumpled/low quality, Malenia looks bald, and creatures do not visibly move. Owner closed GTA. This establishes a successful import milestone, not visual/combat acceptance.
- Prepared and installed v8 with GTA/PlayGTAV absent. All six active-profile/private-package hashes match; original retail GTA executable is unchanged. Private rollback: `Backups/2026-10-01-aggressive-visuals-v8/` includes prior ASI/DLC, manifests, and graphics settings.
- ASI SHA-256 `e9f45353b1436a6418e4e35cec0a3550040a5b81561988eca7236feb8e974759`; DLC SHA-256 `f889ca6084fb4825036a656c043b026de861c1cfa80b2009eda62e3120341e21` (57,730,048 bytes). Source assets: `SourceAssets/gta/v8-object-materials`; package: `SourceAssets/dlc-build/v8-object-materials`.
- Material candidate diagnosis: the original converter used specialized `ped_default` shaders on animated objects, leaving pedestrian body/palette/volume inputs unbound. v8 uses generic skinned `normal_spec`/cutout shaders and generated tangents. This is a plausible crumpling repair, NOT a verified cause/fix yet. Source vertices, normals, UVs, indices, weights, bone indices, skeleton and animation XML are unchanged and compared numerically/byte-for-byte.
- Confirmed hair issue: original HairLong material references `AAT500_PCHair_n`/`_3m`; the prior fallback borrowed unrelated 512×512 `c2120_hair2_a`. v8 uses the actual 2048×1024 normal/opacity atlas plus local tint parameters. Normal RG is reconstructed to RGB; packed B/A are no longer mistaken for normal XYZ. Full mip chains and original source resolutions retained, no upscaling. Specular response/layered shaders/shell fur remain approximate. Editable Blender originals are preserved but do not contain the new post-export XML material changes.
- Aggression defaults ON per owner request. **4 pauses/resumes**, **1 selects**, **2 spawns**, **3 clears**, **5 weapons**, **6 Buzzard**. Targets nearby pedestrians/drivers and player; retaliation biases toward a player who hits it; target changes cancel queued strikes. Uses optional official ScriptHook `worldGetAllPeds`/`worldGetAllVehicles` exports, verified present in installed runtime.
- Vehicle contact damage scales with measured recent impact speed, has a 650 ms repeat cooldown, ignores parked/creeping contacts, and briefly lets collision physics move the creature before pursuit resumes. Small unsourced settling HP losses are filtered. NPC bullets use native health loss; player fallback stays attributed/logged. Real car/helicopter damage still needs owner testing.
- Animation requests explicitly set speed and always-prerender/force-update. Logs `animation_started` and three `animation_sample` phase readings after each transition; one bounded recovery for a stuck looping clip. These are diagnostic/repair candidates; visible movement/rig correctness remain unverified. State marker `loaded_aggressive_visuals_v8_owner_verification_pending`. No new automatic import diagnostic is queued.
- HUD now uses slimmer bottom bars, gold trim and delayed damage trails; controls fade after a few seconds. ShaderQuality changed 0→2 and anisotropic filtering 0→16; existing TextureQuality 2, 1920×1080 window and conservative distance/shadow settings retained. Performance is unmeasured.
- Verified: all seven CTest groups; Windows x64 compilation; native round-trip of three rigs/12 clips/35 textures; correct DLC resource types; source geometry preservation and finite unit orthogonal tangents. No claim of Elden Ring visual parity or completed encounter.
- Launch guard refused before starting GTA: GPU 0%, but the shared PAUSED marker now reads `OWNER RESERVATION: DSR-MW2 startup and owner play; background renders remain paused.` Do not alter it or stop the other session. Requested owner permission to message that Codex session for a GPU handoff. No message has been sent yet. Keep source pushed while waiting.

## Previous installed candidate: dynamic-creatures-v7

- On the owner-requested reopen, GTA5.exe PID 49563 remained running beyond three minutes under the exclusive reservation. The v7 log records valid existing entities for Malenia (2562/2818), Red Wolf (3074/3330) and Giant Crab (3586/3842), with native dynamic=false/true respectively. Stock reference also passed; `import_diagnostics_complete value=0`. This verifies object creation for every production model, not their appearance, animation, damage or encounter quality. Do not repeat the diagnostic unless a new failure warrants it.
- **Runtime isolation found the decisive setting:** the full Malenia asset with Dynamic+HasAnim flags (`131584`) created valid objects in every v6 run, with both native dynamic arguments. Examples: handles 2306/2562, 3586/3842, 9218/9474. The baseline (flags 512), static+animation/default-clip variant (544), collisionless variant and unskinned/static variant returned zero. This is native creation proof for the real rigged/collidable Malenia asset, not visual/gameplay acceptance.
- v7 applies `Dynamic (131072) | HasAnim (512)` to ALL THREE original archetypes. Original YDR/YCD mesh, rig, texture, collision and animation resources are byte-identical to the texture-corrected v3 originals. No placeholder/proxy/ped replacement is used. Experimental aliases and the default-clip alias were removed from the production DLC.
- Normal controls are restored to **1–6**. Temporary key 7 removed; file-only, fixed-command technical verification remains. The owner-approved one-shot check of stock object + original Malenia/Wolf/Crab has run and passed on their real model names. It deleted the technical samples immediately and consumed the request file. Press 2 for a persistent normal creature with combat OFF.
- ASI SHA-256: `6971f83a331654d8b79aaabe9c2bb240f3ce0917b038a8dbcdf53706a6bb62df`.
- DLC SHA-256: `ccad3b6a638074c46edcdf478ba96458b6612f2c89086f301c3ee6e6f321c28b`, 27,295,744 bytes; build `SourceAssets/dlc-build/v7-dynamic-creatures/`.
- v7 script marker: `loaded_dynamic_creatures_v7_owner_verification_pending`; technical sweep completion has `value=0` if the production native call succeeded for every model. Normal persistent spawns log `creature_created` and native HP; animation failures are separate events.
- Owner saved/closed GTA for this patch. It was installed with no GTA/PlayGTAV process present; six payload hashes verified and original retail executable unchanged. Rollback: `~/Applications/EldenLosSantosPreview/Backups/2026-10-01-dynamic-creatures-v7/`.
- v7 guarded launch requested under the explicit OWNER PAUSE reservation, 1080p/windowed; check actual launch/runtime logs. Await current model checks plus owner visual/combat review before upgrading completion claims. All six source test suites and Windows x64 compilation pass.

## Previous import-diagnostics-v6 checkpoint

- v5 also FAILED for all three custom creatures; stock reference object still succeeded (2306). Do not repeat claims that arity/texture/CONTENTS_PROPS corrections completed spawning. Root custom-asset failure remains unresolved.
- Hari explicitly approved the model-only technical import check: briefly create/remove six model variants and log acceptance. This authorizes the fixed file command for this diagnostic, not tutorial/combat/controller automation. One request is queued at `Game/EldenLosSantos.import-check.request` containing `CHECK_IMPORTS_ONCE` plus newline. It waits for Story Mode (scripts skip pause/cutscenes/network), then is consumed once. Key **7** triggers the same check; **3** cancels it. No listener/server.
- Models tested: stock `prop_box_wood01a`, baseline `ergt_malenia`, full rig+collision/static-animation/default clip `ergt_test_sta`, full rig+collision/dynamic-animation `ergt_test_dyn`, rig without collision `ergt_test_nocol`, and unskinned ordinary-shader/no-collision `ergt_test_rigid`. Each tries the native creation dynamic argument false and true, logging `import_check`. Successful diagnostic objects are deleted in the same tick below the player. They are not playable bosses or visual acceptance.
- The static animated probe includes an additional default clip keyed to its model name, backed by CodeWalker's renderer lookup (`ycd.ClipMap.TryGetValue(arche.Hash,...)`). Existing dictionaries only had the ER clip names. Other original clips remain. Native YCD round-trip: 5 Malenia dictionary clips, 4 animations; no animation data was regenerated.
- Offline format checks: 7 archetypes, 11 native resource entries of correct versions, textures validated. Static/dynamic/collisionless probes retain 96 bones; rigid probe has no skeleton and removes only skinning channels while retaining vertex positions/UVs. This is a diagnostic package, not a finished repair.
- ASI SHA-256: `b14d1ae35f51d1977e2f13b785fcc9ef9bd2ceb261806e7cc7b4d7cd709cca8e`.
- DLC SHA-256: `fb3092a8faeab8c5ac0859416b4b87054241801a6d16ade411654ca5eb281fa9`, 73,625,088 bytes. Build at `SourceAssets/dlc-build/v6-default-clip-checks/`.
- v6 script marker: `loaded_import_diagnostics_v6_owner_verification_pending`. Await `import_diagnostics_complete` and all `import_check` lines. Failed load stage/creation must remain distinguished.
- Owner says he paused ALL Unreal work. Live GPU registry confirmed no Unreal engines/holders, with an explicit marker: `OWNER PAUSE 15:41: everything stopped until the owner says resume (GTA for a few hours)`. Launcher recognizes this exact owner reservation, never an emergency pause, and leaves the marker untouched. One initial v6 launch attempt was refused before launching due to a GPU spike (84%). The guard now waits up to 60 seconds for the same below-30% condition to hold for 12 seconds; it does not relax the limit. No game was started by that refused attempt.
- A new guarded v6 launch is requested, with the approved one-shot import check queued. Check launch status and the runtime log. Hari must enter Story Mode himself if at the menu; no automatic menu clicks.

## Previous prop-registration-v5 checkpoint

- v4 owner test FAILED to create Malenia, but its stock-object A/B probe returned entity 2050 and deleted it immediately. This proves the native object factory works after the signature corrections and isolates custom asset setup. Owner confirmed the visible failure and then saved/closed GTA for replacement.
- Found missing `<contents>CONTENTS_PROPS</contents>` on this project's DLC_ITYP_REQUEST, present in prop-pack declaration references. v5 adds only that field to content.xml. Nested ergt_assets.rpf is byte-identical, and the v4 ASI remains installed. This is a focused registration test, not another model/texture rewrite.
- New manifest validation rejects the previous missing prop classification and any disabled file never enabled by GROUP_STARTUP. Archive verification confirms all seven native entries are resource entries, with YDR=165, YCD=46, YTYP=2. All six CTest suites pass.
- v5 DLC SHA-256: `43ea11054ee6dfeb6cd63ce48087ab621c22e43ca478cc12ec87a3adbd1bd771`, 27,295,744 bytes. ASI remains `1057fbd214f863aa84751ed874e0295e0450f32ede34d153f0c065c29b6a5f4a`, so its runtime log marker remains `loaded_native_contract_v4_owner_verification_pending`.
- Installed while game stopped; six payload hashes verified in package/profile, original retail bytes unchanged. Rollback at `~/Applications/EldenLosSantosPreview/Backups/2026-10-01-prop-registration-v5/`. Source build under `SourceAssets/dlc-build/v5-prop-registration/`.
- Owner explicitly asked the Unreal coordinator to keep rendering paused across restarts. v5 relaunch requested through the exclusive guard at 1080p; prelaunch GPU 9%, no other renderer. Await one owner press of 2 outdoors with Malenia selected and combat off. Do not claim a creature spawned until the log and owner confirm it.

## Previous native-contract-v4 checkpoint

- Owner reported all creatures still failed in v3; guns/helicopter worked. Logs now prove all three custom models passed model and animation streaming gates, then returned zero from CREATE_OBJECT_NO_OFFSET. No new crash was reported for this bounded test. GTA subsequently exited; no game files were replaced while running.
- Revisited user-supplied `rehan-remade/universal-modder` at commit 15d6f9d5fbd32de9b1884f29ddec3be9133bd912. Its working Minecraft/GTA example uses GTA Legacy 3889 + SHV 3889. Its native wrapper passes EIGHT arguments to CREATE_OBJECT_NO_OFFSET (last 0); our code passed seven. The same eight-argument signature is in alloc8or native DB revision 424fb51b089049a9fbcebcc641500b1d44d255b4.
- Corrected 12 incomplete call sites in the main plugin and 6 in the older probe: object/vehicle creation, ground queries, entity health/invincibility, ped damage, explosions, HUD text/rectangles and probe death query. No geometry/texture changes in this patch.
- Added `gta/native-contracts.json` (72 API interface facts with pinned source links) and a parser-based regression suite checking every literal-hash native call in both plugins. The original seven-argument object call is explicitly rejected. All five CTest suites and both Windows x64 plugin builds pass. Arity is a verified bug; whether it completely fixes creature spawning is still an owner test.
- If a creature still fails, one owner-triggered reference check creates/removes universal-modder's known stock prop `prop_box_wood01a` in the same tick below the player. See `reference_object_creation_result`: nonzero isolates custom assets, zero suggests a general object/native path issue. Never claim this diagnostic prop is a boss or a completed import.
- v4 loading marker: `loaded_native_contract_v4_owner_verification_pending`.
- Current ASI SHA-256: `1057fbd214f863aa84751ed874e0295e0450f32ede34d153f0c065c29b6a5f4a`.
- DLC remains the v3 texture-corrected package, SHA-256 `af119ef181a0f02ef7457a64a35f83c399c050992035b3258376ebb54d341765` (27,295,744 bytes). Prior v2 had 11 invalid texture enums; v3 corrected them and all 22 textures pass offline format checks, but that did not by itself fix spawning.
- v4 installed with GTA stopped; six payload hashes match active profile and private bundle; original retail checksum unchanged. Backup: `~/Applications/EldenLosSantosPreview/Backups/2026-10-01-native-contract-v4/`.
- Hari relayed another request to the external Unreal session to keep rendering paused ACROSS GTA restarts until this test finishes. Observed coordinator marker: `owner reopening GTA 15:02 - renders paused by game_watch.sh (pre-emptive)`. Launcher now recognizes this exact reservation shape as well as the earlier opening-GTA-V marker; emergency pause remains blocked. No other session processes or pause files were changed.
- v4 relaunch requested under the exclusive owner reservation at 1080p. Read local launch status for actual outcome. Owner should press **2 once** outdoors, default Malenia, combat OFF. Read log rather than repeating identical failed attempts. No creature success is claimed yet.

## Local profile and asset boundaries

- Private bundle: `~/Applications/EldenLosSantosPreview/`; owner guide `START-HERE.md`; editable inputs `SourceAssets/`; latest private DLC build `SourceAssets/dlc-build/v5-prop-registration/`.
- Steam's existing GTA path is a symlink to `~/Library/Application Support/EldenLosSantos/Game`. Exact original retail directory remains `~/Library/Application Support/EldenLosSantos/Retail`. APFS clonefile shares original blocks, not a second full-size copy.
- Profile state: `~/Library/Application Support/EldenLosSantos/profile-state.json`. Only GTA5.exe's Wine `dinput8` override is `native,builtin`, with prior absence recorded. Account stores and saves were not changed.
- Restore with GTA closed: `python3 ~/Applications/EldenLosSantosPreview/Tools/profile_manager.py restore`; use `activate` to reactivate. Do not unlink game/profile paths manually.
- Owned-game data, converted assets, runtime files, saves and account stores must never be published. Public `gta/` contains original tools/code and source references.
- ERGTA-Tools is a separate accountless conversion bottle. Data-only conversion is permitted; all rendered/gameplay validation belongs to Hari.
- Custom GTA AI, coarse whole-body collision and approximate materials remain experimental. Original ER AI/cloth/VFX/audio are not ported. No verified boss encounter, damage balance or FPS claim.

## Source groundwork saved when the owner cancelled the follow-up

- Added original GTA diagnostic ASI source under gta/: a dormant F6/F7 test-actor probe, raw native health/death observation, HUD, local log, Script Hook V dynamic ABI wrapper, portable checks and CMake/Mingw build configuration. Read gta/README.md.
- Native unit checks passed. Windows x64 ASI cross-compilation passed. A generated import library now declares the ScriptHookV.dll dependency through its game-version export, alongside KERNEL32 and Universal CRT imports. All eight dynamic entry points match the inspected official runtime export table. No in-game loader test yet. No plugin installed or executed in GTA; no game launched and no Elden Ring assets imported.
- Official SDK/runtime downloads were inspected in ignored scratch only; archive redistribution is prohibited, so they are not published. Native hashes/signatures and runtime exports were used as API interoperability references. GTA5.exe version 1.0.3889.0 matches the runtime's advertised supported Legacy build.
- Homebrew mingw-w64 14.0.0_3 installed (compiler reports GCC 16.2.0); dependency isl upgraded by Homebrew. No tap trust settings changed.
- Steam downloads were left running. Latest content log showed Elden Ring downloading at about 986 Mbps, despite the on-disk manifest's stale zero-byte progress. Never treat that manifest counter alone as a stuck download.

## Midir coordination

- On 2026-10-01 Hari explicitly authorized this session to own the main GTA V × Elden Ring game. He subsequently confirmed Midir owns Dark Souls × MW2. A correction was delivered to the dot thread; the earlier candidate Elden Ring/MW2 Zombies assignment is superseded.
- Sent the updated scope, candidate side-demo brief, repository/branch pointer, and strict checkout/bottle/download/process ownership boundaries using send_message_to_thread to the dot conversation 01a0f57b-1eee-7674-9735-1ab9034fe0f7 on host durable. The API confirmed delivery; do not claim acceptance or a running side build until observed.
- That dot previously spawned Review game combines project (01a0f57f-2350-7535-a601-3d6186da00c2), which had read an older mac-prototype snapshot. The new brief corrects its outdated target and setup status.
- We did not create an additional fork/session. Recommend separate repositories for different game hosts, or isolated worktrees/branches when sharing code. Do not mix active game/mod profiles.

## Previous Terminal goal and owner decisions

- Public open source project with a ten-minute Terminal crossover demo for a video.
- Mac is the first build target. The owner authorized autonomous implementation and will provide game data later.
- Earlier implementation lacked retail data. The new owner report and current audit above supersede that setup status.
- Terminal means the MW2 airport map.
- Signature proposal: builder gun, skating, confirmed-trick charge, dragon killstreak, objective/extraction/restart loop.
- Additional research: universal-modder, the Minecraft/Elden Ring clip, libsm64 and CrossOver. Preserve the Terminal objective while expanding through reusable adapters.

## Repository and ownership

- Public remote: https://github.com/oh-ashen-one/modern-warfare-2-ai
- Earlier implementation branch: codex/mac-prototype, based on codex/terminal-foundation. Current branch is listed above.
- The original foundation branch remains the default; no main/default-branch merge is authorized or performed.
- No other session's game process, bottle or checkout was changed.

## Completed and verified

- Pinned mashup source imported into runtime/ with upstream LICENSE/NOTICE. See docs/UPSTREAM-IMPORT.md.
- Rust 1.98.1 installed and pinned. Native arm64 optimized engine executable built successfully on the M3 Ultra Studio.
- SwiftUI setup app, Rust setup CLI, safe process launch path, file validation and game-folder configuration implemented.
- Minecraft automatic data downloads disabled in the Mac launcher. No commercial game data downloaded.
- Mac board/rig preparation command added. The Skate conversion helper refuses missing data and existing output paths.
- Independent mission/block rule crate implemented; eight meaningful tests pass. Strict Clippy and formatting pass for original Rust crates.
- Native setup window inspected visually and through accessibility; refresh and folder-picker cancellation verified. Launch stays disabled with missing MW2 data.
- Apple Silicon setup preview packaged with local ad-hoc signing and license notices for 499 Rust packages.
- Local deliverable folder: ~/Applications/Modern-Warfare-2-AI-Preview/
- Packaging is reproducible with scripts/build-mac.sh; use MW2AI_OUTPUT_DIR outside iCloud/Documents to avoid File Provider signing metadata.

## Honest boundary

- The mission/block rules are NOT yet wired into the runtime.
- No Terminal rendering, shooting, bots, skating or full gameplay session has been tested because retail data is missing.
- No Skyrim model/animation conversion or dragon encounter has been implemented.
- No claim of 60 fps, full controller compatibility or finished ten-minute gameplay is made.
- The delivered app is a setup preview plus compiled base runtime, not the finished game.

## CrossOver and more-game research

- CrossOver 26.2 is installed on the Studio.
- The earlier missing-bottle finding is superseded: the Steam bottle now exists and Windows Steam is downloading games.
- universal-modder's published worked bridge is Minecraft/GTA V on Windows. The linked Elden Ring clip is by a different creator; captions were unavailable, and only four frames were sampled.
- Neither universal-modder nor libsm64 has been imported or installed. They are references in docs/MORE-GAMES.md.

## Previous Terminal next steps (backlog)

1. Provide owned MW2 (2009 PC) multiplayer data to the native setup app; verify the unchanged Terminal baseline first.
2. Supply/convert Skate 3 data and verify real controls, animation, collision, death and restart.
3. Connect the prepared mission/block rules to actual game events and collision/rendering; add the builder weapon.
4. Supply Skyrim data, establish the conversion pipeline, and implement the bounded dragon strike.
5. Complete the ten-minute mission and obtain owner gameplay feedback before calling it finished.
6. For Windows-host experiments on the Mac, locate the actual CrossOver bottle storage and create a separate task-owned bottle before testing loader/depth/compositor compatibility.

## Commands

- cargo test --workspace --locked
- cargo clippy --workspace --all-targets --locked -- -D warnings
- cargo fmt --all --check
- MW2AI_OUTPUT_DIR="$HOME/Applications/Modern-Warfare-2-AI-Preview" bash scripts/build-mac.sh
- cargo run -p mw2ai-launcher -- doctor --json
- cargo run -p mw2ai-launcher -- demo-check

Read docs/BUILD-STATUS.md and docs/MAC-SETUP.md for exact limitations. Do not treat the scripted rule check as gameplay evidence.

## Original preparation handoff (superseded by the current candidate above)

- The preview is active. Next step is owner-only launch of GTA V Legacy through the existing CrossOver Steam path, finish the tutorial/free-roam save, and follow gta/OWNER-TEST.md.
- All runtime and visual claims remain pending that owner test. If no header appears, inspect the loader chain. If models are unavailable, inspect the DLC mount and YTYP registration. If models appear but no damage/animations, use the local EldenLosSantos.log for focused fixes.
- Do not run GTA, render previews or conduct agent playtests. No recurring continuation/reminder exists for this thread.

## Original preparation verification (before the first owner spawn test)

- Full dependency bootstrap succeeded. Its public runtime downloader was corrected to use the publishers' normal curl download route after urllib received HTTP 406; both downloaded archives matched their pinned SHA-256 values.
- Complete build_owned_assets.py pipeline succeeded into a fresh asset output directory, without any game or render. Rebuilt DLC exactly matches the staged candidate SHA-256 48500df2c04e3e57103a086f4fd75dea54c238aaa743ec78beee80b9e0801018 (27,295,744 bytes).
- Final rigged interchange files (four clips each) also pass the Khronos glTF validator with zero errors and zero warnings. Native resources preserve 96/138/53 bones, four clips each, and collision. See gta/VERIFICATION.json.
- Source review: draft PR https://github.com/oh-ashen-one/modern-warfare-2-ai/pull/2, based on codex/gta-damage-probe. No merge performed. GitHub source checks passed for the preceding source checkpoint; final docs/download fix triggers the same checks.
- Private named deliverables are under ~/Applications/EldenLosSantosPreview. SourceAssets contains the retained editable assets; the old ignored assets/private/eldenring path is maintained as a local symlink so saved Blender texture references remain valid. Older intermediate exports and duplicate verification outputs are disposable and being cleaned up, along with task-owned build/tool caches. Recreate tools with bootstrap_tools.py when development resumes.
- Preview profile ACTIVE; original retail bytes and all six installed payload hashes verified. No game was launched. The remaining gate is Hari's own loading/visual/gameplay/performance check, starting with gta/OWNER-TEST.md.
