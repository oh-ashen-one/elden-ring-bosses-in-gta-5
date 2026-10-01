# Handoff

Updated: 2026-10-01 (native API v4 repair after v3 creature-spawn failure).

## Current priority and verified state

- This thread owns GTA V × Elden Ring. Midir owns Dark Souls × MW2. Keep those lanes separate.
- Repo: https://github.com/oh-ashen-one/modern-warfare-2-ai; branch `codex/elden-assets-and-combat`; draft PR #2 targets `codex/gta-damage-probe`. No merge permission.
- Chat default cwd points at another lane (`/Users/midir/Documents/ChatGPT/combiing games`). ALWAYS pass this GTA checkout as the working directory.
- All six games finished installing. Hari CANCELLED the slow SD-card migration; leave games internal. The task-owned partial copy was removed without removing source game files. Do not resume migration.
- The `move-steam-games-after-downloads-finish` automation was deleted at Hari's request. Do not recreate it.
- Latest standing instruction: **open GTA V Legacy after installing patches**, without asking again. Hari owns gameplay, rendering review and performance testing. Use the shared renderer slot and verified Studio desktop; do not interrupt active unsaved gameplay or enter a crash/relaunch loop. No tutorial/combat input automation is authorized.
- Hari now reports the tutorial completed. The previous window was saved at 800×600; he was given in-game window/resolution steps. Mac and Windows Steam both recognized DualSense; an empty GTA mapping was observed and Steam Input instructions supplied. Controller resolution is not independently confirmed.
- Actual GTA build is 1.0.3889.0. Script Hook V initialized successfully, registered and executed `EldenLosSantos.asi`; ASI loader also loaded RageOpenV. The mod received two owner spawn commands but logged `create_object_failed` after its model and animation streaming gates. No visible creature or combat success is established.

## Launch recovery after the computer restart

- Hari reported the previous GTA launch froze the whole computer. Live host boot time confirms a restart at 14:26:36 America/New_York. The prior launch receipt recorded GPU utilization at 100% before launch; using a second renderer at that load was inappropriate even below the old process cap.
- Root coordination error: the prior GTA helper locked `~/.cache/gpu-slot`, while active Unreal jobs use `/Users/midir/sm2-n1/_scratch/gpu`. Future GTA launches must share the ACTUAL current lock directory and be exclusive. Do not use the old private owner_launch.py helper (now retired).
- Also found GTA saved at 3440×2752, RefreshRate 0. Backed up its display settings locally, changed to 1920×1080 windowed, requested 60 Hz and retained half VSync. Launch flags pin 1920×1080. Actual FPS and full stability are unverified; keep this lower resolution for now.
- Hari authorized asking the Unreal session to pause. It is an external Claude session, unavailable through Codex task messaging. No message was sent through another terminal. Hari relayed the pause request himself; the coordinator stopped its renderer and wrote `owner opening GTA V 14:48 - renders paused; auto-lift after GTA5.exe exits` to its PAUSED marker. Only the null-RHI import remained; desktop-only GPU baseline was ~20%.
- New original `gta/tools/launch_owner.py` uses that protocol's existing exclusive perf.lock for the entire actual GTA process lifetime. Normal launch uses the protocol's 15%-for-10s idle gate; the explicit owner reservation supports the measured desktop baseline below 30% over 12 seconds, while admitting NO other renderer. It never clears/renames PAUSED, stops another process, raises the shared cap or auto-relaunches. An emergency/non-owner pause always blocks it. This reservation is not an FPS benchmark.
- Eight source-only launch guard tests pass, including the previous 97% GPU case, low-util live renderer, unknown GPU, logged-out desktop, stuck exiting headless engine and emergency pause. A current read-only check refused launch until the owner reservation existed and other rendering stopped.
- Lower-resolution v3 launch succeeded under that reservation at 14:53 America/New_York: GTA5.exe PID 50731, Script Hook initialization and DirectX initialization confirmed. A 20-second startup check sampled GPU values 0–31% (mostly 20–21%); desktop console remained midir. This is startup evidence, not sustained gameplay/FPS or creature verification. The exclusive slot remains held until the actual game process exits; the other coordinator owns its pause/auto-lift. Hari retains gameplay control.

## Current installed candidate: native-contract-v4

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

- Private bundle: `~/Applications/EldenLosSantosPreview/`; owner guide `START-HERE.md`; editable inputs `SourceAssets/`; latest private DLC build `SourceAssets/dlc-build/v3-textures/`.
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
