# Handoff

## Current state

- Scope: public repository foundation, source credits, Terminal integration proposal and a ten-minute demo/release specification.
- Owner confirmed Terminal means MW2's airport map.
- Current contents are original documents and a source metadata snapshot; no upstream game implementation or proprietary assets have been imported.
- No build, engine launch, gameplay test or performance measurement has occurred.
- Intended runtime base: chasmlol/2010-rust-rewrite-mashup, pending component license/provenance review and target-host verification.
- Branch: codex/terminal-foundation.
- Public remote: https://github.com/oh-ashen-one/modern-warfare-2-ai.
- Local verification: 10 recorded source revisions, relative document links, Apache-2.0 license and a document-only file inventory validated.
- Latest requested outcome: a public open source project and a ten-minute playable demonstration for the video.
- Proposed minimum: builder weapon, skating, confirmed-trick charge, allied dragon strike, objectives and restart; see docs/DEMO-SPEC.md.
- Preflight verified an M3 Ultra Mac Studio with 256 GB memory, Xcode and CMake. Rust/Cargo were absent from PATH and usual install locations.
- A bounded check of the Studio Steam library and Games folder did not locate the required game data.

## Next work

1. Obtain game-data locations/download needs and the first playable platform choice from the owner.
2. Finish source component license review and preserve original authorship/notices; do not infer every nested component's license from the root.
3. Set up the build toolchain, establish a pinned baseline and prove the combined fork's build/runtime on the intended host.
4. Follow docs/DEMO-SPEC.md, beginning with unchanged Terminal combat and skating, then the builder weapon and bounded dragon strike.

## Open questions and constraints

- Native macOS support for the combined mashup is not verified.
- Direct Skyrim integration is new work; SkyCraft's bridge runs in the opposite direction.
- Current upstream documentation is not local runtime evidence.
- No other agent, engine or process is owned by this project.
