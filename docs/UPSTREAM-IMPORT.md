# Upstream import

## Source

- Project: [2010 Rust Rewrite Mashup](https://github.com/chasmlol/2010-rust-rewrite-mashup)
- Revision: [ab43b8a9e923bdc4ad7effb874f6efec155577f1](https://github.com/chasmlol/2010-rust-rewrite-mashup/tree/ab43b8a9e923bdc4ad7effb874f6efec155577f1)
- Imported path: `runtime/`
- Root license: Apache-2.0. Original `runtime/LICENSE` and `runtime/NOTICE` are preserved.

The upstream NOTICE credits vladtrc/IW4L, chasmlol, the in-tree skating components, MinecraftOSS, fonts and research tools. Its `docs/SKATE.md` identifies the skating source revision as `cb7968930f14dad38457e98720d1a274e469eec2`; the vendored MinecraftOSS README records `4013a68`.

This is a pinned source snapshot, not a claim that we authored the upstream runtime. The original history is available at the source revision above.

## Import exclusions

- Git internals and upstream GitHub workflows.
- Upstream maintainer-only AGENT.md and CONTEXT.md files.
- Third-party gameplay reference screenshots under docs/screenshots.
- No game installation, converted assets, binary release or cache was imported.

Upstream generated gameplay-metadata catalogs remain as part of the source. Retail artwork, maps, models, sounds and executable content do not.

## Initial local changes

- Added this provenance pointer to the vendored README.
- Disabled automatic Minecraft data downloading unless explicitly enabled; our Mac launcher always disables it.
- Added a renderer-free `prepare-skate` command.
- Added the missing Mac board/rig preparation step when converted skating data is configured.
- Pinned the verified Rust 1.98.1 toolchain for reproducible builds.

Original work outside runtime/ includes the native SwiftUI setup app, Rust setup CLI, deterministic mission/block rule crate, Mac packaging, source-license inventory and documentation.

## Dependency notices

The packaging script collects license files for the resolved Apple Silicon dependency graph. Where published crates omit their license files, licenses/dependency-overrides.json records exact upstream license sources. Three packages use canonical SPDX terms plus their original package license declarations; this distinction is recorded rather than inventing copyright notices.

This inventory preserves declared terms and source references. It does not make an independent guarantee about the provenance of every upstream line or grant rights to commercial game content.
