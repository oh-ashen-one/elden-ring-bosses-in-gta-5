# Handoff

Updated: 2026-10-01 (GTA V × Elden Ring priority and setup audit).

## Current priority and setup audit

- Active goal: GTA V × Elden Ring, with a boss damaged by native GTA firearms, explosives, vehicle impacts and helicopter weapons. See docs/CROSSOVER-BACKLOG.md.
- Windows Steam is installed and authenticated sufficiently to download games in the CrossOver Steam bottle. Rosetta is installed. Hari has confirmed GTA V Story Mode works and is currently playing the opening robbery/tutorial. Elden Ring gameplay and the crossover mod remain unverified.
- Latest audit: GTA V Legacy has StateFlags 4 with all 129,049,797,551 bytes staged; MW2, Escape the Backrooms and Phasmophobia also report installed. Elden Ring and Dark Souls Remastered remain pending. Recheck live manifests and queue before use.
- Storage: 512 GB writable exFAT SD card named memory, mounted at /Volumes/memory, UUID AB55E1EC-D2BD-38BD-961F-56347E0F5C9D; CrossOver maps it as D:. Initial inventory showed roughly 512 GB free. Reserved logical game files total roughly 274 GB; live totals may grow.
- All six games and shared redistributables finished downloading. The owner then CANCELLED the SD-card migration because the sustained copy speed was too slow. Keep all games in the existing internal CrossOver Steam library. The task-owned rsync was stopped cleanly with SIGTERM (exit 20); no source files were removed and neither Steam library configuration was changed. Partial SD copies were removed and Windows Steam was reopened successfully (verified process). No storage migration is authorized now.
- Owner cancelled the automatic follow-up on 2026-10-01; automation move-steam-games-after-downloads-finish was deleted successfully. He subsequently confirmed downloads finished and resumed work, then cancelled only the SD-card migration. Main GTA V × Elden Ring work remains authorized on internal storage. Do not recreate the reminder.
- CrossOver, Steam and all game data stay INTERNAL per the latest owner instruction. Do not resume the SD-card move.
- Product scope is real GTA V Story Mode with Elden Ring bosses in an open-ended Los Santos sandbox. One roughly ten-minute encounter is the first verification milestone, not a playtime limit or a replacement for the larger game. No mod loader installed, no boss converted, no GTA gameplay verified. Current independent work can cover the encounter specification, original boss rules and tests, and investigation of the asset conversion route. GTA adapter and visible gameplay require the installed game.
- Working branch: codex/elden-assets-and-combat, based on codex/gta-damage-probe; earlier branches remain preserved.

## Current asset implementation checkpoint

- Hari authorized all work possible without playing GTA or Elden Ring, targeting multiple Elden Ring bosses/monsters imported directly into GTA. No game launches or agent gameplay tests are needed/authorized for this lane.
- Added GPL-3.0-or-later standalone tools under gta/asset-tools (separate from the Apache GTA plugin).
- Pinned souls-formats-c compiled to Windows console binaries on Mac via MinGW. Created ERGTA-Tools CrossOver bottle solely for headless asset conversion; it has no Steam/account/game install.
- Successfully extracted owned Malenia c2120, Red Wolf c3181 and Giant Crab c2270 model/animation/high-texture binders. Output: ignored assets/private/eldenring, with extraction-manifest.json and checksums. Game archives unmodified.
- Native Python environment scratch/asset-venv contains pinned Soulstruct 2.6.0 / soulstruct-havok 1.5.0 and dependencies recorded in gta/asset-tools/requirements-mac.lock. Parsing Malenia's 899 FLVER bones/35 meshes and 337 Havok skeleton bones succeeded; a 136-frame/145-track compressed animation decoded with its compendium.
- Next: texture/material unpacking and rig/animation export; then GTA-format conversion and runtime boss systems. No GTA-ready imported boss exists yet.
- Read gta/asset-tools/README.md for tested workarounds (native BHD5 header decode and full 64-bit archive path hash), licenses and source pins. Latest Soulstruct Blender package is Windows-only via pyrelink; do not assume its release ZIP works on native Mac. Installed /Applications/Blender.app is 5.2.0, not the older 4.5 path from prior notes.

## Owner testing handoff (latest instruction)

- Hari explicitly asked to handle game launching and playtesting himself to avoid spending agent credits on runtime testing. Do not launch or automate GTA/other game playtests unless he asks again. Focus this session on source, asset conversion and building reviewable artifacts, then give short owner test steps.
- No GTA game was launched by this session. The latest attempted baseline launch stopped at read-only safety checks when the owner changed this workflow. Other sessions' Unreal processes were untouched.
- Baseline owner check PASSED for launch: Hari reports GTA V Legacy Story Mode working and is playing the opening robbery/tutorial. A live GTA5.exe process was also observed. This is owner-reported baseline gameplay, not a mod test or performance measurement. Let him finish; do not close or restart GTA/Steam/Rockstar or change the running game files. Boss/probe behavior remains unverified.
- At his request, quit our unused Modern Warfare 2 AI setup preview (verified exited), and dismissed the CrossOver manager window. Other sessions' Unreal/terminal work and GTA dependencies stay running.

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
