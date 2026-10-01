# Handoff

Updated: 2026-10-01 (number keys and repair candidate after first owner spawn failure).

## Current priority and verified state

- This thread owns GTA V × Elden Ring. Midir owns Dark Souls × MW2. Keep those lanes separate.
- Repo: https://github.com/oh-ashen-one/modern-warfare-2-ai; branch `codex/elden-assets-and-combat`; draft PR #2 targets `codex/gta-damage-probe`. No merge permission.
- Chat default cwd points at another lane (`/Users/midir/Documents/ChatGPT/combiing games`). ALWAYS pass this GTA checkout as the working directory.
- All six games finished installing. Hari CANCELLED the slow SD-card migration; leave games internal. The task-owned partial copy was removed without removing source game files. Do not resume migration.
- The `move-steam-games-after-downloads-finish` automation was deleted at Hari's request. Do not recreate it.
- Hari owns gameplay, rendering and performance testing. He explicitly requested one GTA launch; the session launched Legacy through Windows Steam, then handed control back. No tutorial/input/playtest automation was performed. Do not launch again unless asked.
- Hari now reports the tutorial completed. The previous window was saved at 800×600; he was given in-game window/resolution steps. Mac and Windows Steam both recognized DualSense; an empty GTA mapping was observed and Steam Input instructions supplied. Controller resolution is not independently confirmed.
- Actual GTA build is 1.0.3889.0. Script Hook V initialized successfully, registered and executed `EldenLosSantos.asi`; ASI loader also loaded RageOpenV. The mod received two owner spawn commands but logged `create_object_failed` after its model and animation streaming gates. No visible creature or combat success is established.

## Current installed candidate: number-keys-spawn-v2

- Original C++ plugin now uses **top-row 1 select / 2 spawn / 3 clear / 4 combat / 5 weapons / 6 Buzzard**. No Fn chord. It reserves corresponding GTA direct weapon-selection actions; the weapon wheel remains available. Numpad flight keys are not used by the mod.
- Fixed missing archetype declarations: Has Anim flag 512, physics dictionary bound to embedded collision, and texture dictionary bound to embedded textures. Removed static-scenery flag 32. These omissions are verified; whether they fully explain GTA's failed creation is still an owner test.
- Local non-door spawn call plus one bounded standard-object fallback on a zero handle. Fallback corrects GTA's model-radius Z offset. Invalid coordinates are rejected. Logs include exact model/hash, loaded state, type, spawn coordinates and both creation return values; no placeholder replacement is used.
- Three authentic owned ER creatures: Malenia phase-one meshes, Red Wolf of Radagon and Giant Crab. Twelve clips have provisional idle/movement/attack/death roles. Skeletons, mesh resources and clips are unchanged by this repair.
- Current private DLC: 27,295,744 bytes; SHA-256 `27d1ec032b91e2fb49b6df3f596d87e1efebd235f9da3cca53615a9d06a9e8a6`.
- Current ASI SHA-256: `074d1bfa71fea1b3e82316de289a2008e3e33af7a691f3d0bce8fd5cb9dc54b6`.
- Verified Windows x64 compile, two portable native scenario suites, all three native archetype bindings, archive structure and six unchanged YDR/YCD resources. These are source/format checks, not gameplay proof.
- Installed with GTA and PlayGTAV both stopped. All six payload checksums match the active profile and private bundle. Original retail executable checksum unchanged. Prior ASI/DLC, manifest and profile state backed up privately under `~/Applications/EldenLosSantosPreview/Backups/2026-10-01-number-keys-v2/`.
- **Remaining blocker: owner must relaunch Story Mode and press 2 once in a clear outdoor area.** If creation fails, inspect `EldenLosSantos.log` for the `loaded_number_keys_spawn_v2_owner_verification_pending` marker and the new detailed spawn events. Stop at the first failing step. Do not claim this repair spawned a creature until that happens.

## Local profile and asset boundaries

- Private bundle: `~/Applications/EldenLosSantosPreview/`; owner guide `START-HERE.md`; editable inputs `SourceAssets/`; latest private DLC build `SourceAssets/dlc-build/v2-bindings/`.
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
