# Verified Mac build status

## Completed

- Imported the pinned IW4L/Minecraft/skating runtime with upstream credits and notices.
- Built an optimized Mach-O arm64 game executable on an Apple M3 Ultra Mac Studio.
- Built a native SwiftUI setup app targeting macOS 14+ on Apple Silicon.
- Verified the local app signature and dependency-license collection (499 Rust packages).
- Opened the setup app, inspected its layout and accessibility state, checked refresh, and opened/cancelled the folder picker.
- Verified that missing MW2 data disables the Terminal launch button.
- Eight original-code tests pass: mission completion/timeout, objective ordering, replayed rewards, missing dragon assets, pause/death/reset, block limits/persistence/rays and setup validation.
- Original crates pass strict Clippy and formatting checks.
- Verified that a missing Skate source fails before tool downloads or conversion.

Toolchain used: Rust 1.98.1 and Apple Swift 6.4. Upstream crates emit existing warnings; their compilation completed successfully.

## Not yet verified

- Rendering Terminal, MW2 gameplay, bots, audio or in-game performance.
- Actual Skate 3 conversion, controller feel, animation and gameplay.
- Blocks placed inside Terminal, builder gun visuals or shared runtime collision.
- Skyrim asset conversion, the dragon model/animations, its strike or effects.
- Mission events connected to real game events, or a full ten-minute playable run.

The mission/block crate is domain logic and currently has no runtime adapter. Its scripted `demo-check` output explicitly reports `gameplay_verified: false`.

## Delivery boundary

The app is a **setup preview with a compiled base runtime**, not the finished crossover demo. Commercial game data is required for the next integration and live-testing stage. The Mac was selected as the first target; no Windows testing is required from the owner for this preview.

Local signing is ad-hoc. Apple notarization and signing with a distribution identity have not been performed.
