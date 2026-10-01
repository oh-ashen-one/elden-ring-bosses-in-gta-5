# Source catalog

Research snapshot: 2026-09-30. These are the GitHub projects discussed or inspected for this project. **No implementation code has been imported.** Root license metadata below is GitHub's report, not a complete review of nested components or game content.

## vladtrc/iw4L

MW2 runtime reference: asset loaders, gameplay, rendering and scripting.

- Repository: [vladtrc/iw4L](https://github.com/vladtrc/iw4L)
- Observed branch: `master`
- Observed revision: [`11514ea37d1e`](https://github.com/vladtrc/iw4L/tree/11514ea37d1e80d75bf2c1ba332bbd68fac5db4e)
- Root license reported by GitHub: Apache-2.0.
- Relationship: primary technical reference / proposed foundation; code imported: **no**.

## chasmlol/2010-rust-rewrite-mashup

Candidate implementation base: MW2 plus skating and a Minecraft world. Audit its bundled components as well as the root license before import.

- Repository: [chasmlol/2010-rust-rewrite-mashup](https://github.com/chasmlol/2010-rust-rewrite-mashup)
- Observed branch: `main`
- Observed revision: [`ab43b8a9e923`](https://github.com/chasmlol/2010-rust-rewrite-mashup/tree/ab43b8a9e923bdc4ad7effb874f6efec155577f1)
- Root license reported by GitHub: Apache-2.0.
- Relationship: primary technical reference / proposed foundation; code imported: **no**.

## SK8-ENGINE/skate-3-rust-engine

Skating and mod SDK reference. Its repository has no root license detected by GitHub; component terms require inspection before direct reuse.

- Repository: [SK8-ENGINE/skate-3-rust-engine](https://github.com/SK8-ENGINE/skate-3-rust-engine)
- Observed branch: `main`
- Observed revision: [`60efdef86600`](https://github.com/SK8-ENGINE/skate-3-rust-engine/tree/60efdef86600d8d8d4feb4b7c608fa0efd0643d7)
- Root license reported by GitHub: **not detected**; do not infer reuse permission.
- Relationship: primary technical reference / proposed foundation; code imported: **no**.

## chasmlol/SkyCraft

Skyrim/Minecraft bridge reference. Uses a C++ SKSE plugin and a Java Fabric mod; it is not a Rust Skyrim runtime.

- Repository: [chasmlol/SkyCraft](https://github.com/chasmlol/SkyCraft)
- Observed branch: `main`
- Observed revision: [`0f0a953181cc`](https://github.com/chasmlol/SkyCraft/tree/0f0a953181cc1d2eccec31e4941b3f01a9f173cf)
- Root license reported by GitHub: MIT.
- Relationship: primary technical reference / proposed foundation; code imported: **no**.

## in0finite/SanAndreasUnity

Related reference: a partial GTA San Andreas engine recreation in Unity with multiplayer and C# game modes.

- Repository: [in0finite/SanAndreasUnity](https://github.com/in0finite/SanAndreasUnity)
- Observed branch: `dev`
- Observed revision: [`f685c437f487`](https://github.com/in0finite/SanAndreasUnity/tree/f685c437f48721afc0787f27d22c85d96e8684c7)
- Root license reported by GitHub: MIT.
- Relationship: additional research reference; code imported: **no**.

## coop-deluxe/sm64coopdx

Related reference: multiplayer Mario 64 port with a Lua modding API. Review its actual component terms before reuse.

- Repository: [coop-deluxe/sm64coopdx](https://github.com/coop-deluxe/sm64coopdx)
- Observed branch: `main`
- Observed revision: [`8cd6e5977d9f`](https://github.com/coop-deluxe/sm64coopdx/tree/8cd6e5977d9f920d51ca71f2c61801d019ed79c6)
- Root license reported by GitHub: **not detected**; do not infer reuse permission.
- Relationship: additional research reference; code imported: **no**.

## open-goal/jak-project

Related reference: Jak & Daxter tooling, decompiled GOAL code, asset conversion and live editing.

- Repository: [open-goal/jak-project](https://github.com/open-goal/jak-project)
- Observed branch: `master`
- Observed revision: [`efb21c3e8c5a`](https://github.com/open-goal/jak-project/tree/efb21c3e8c5a40a74f2e86510f915da55eaeba34)
- Root license reported by GitHub: ISC.
- Relationship: additional research reference; code imported: **no**.

## Interkarma/daggerfall-unity

Related reference: Daggerfall recreated in Unity with extensive content and gameplay mod support.

- Repository: [Interkarma/daggerfall-unity](https://github.com/Interkarma/daggerfall-unity)
- Observed branch: `master`
- Observed revision: [`2343305d1d83`](https://github.com/Interkarma/daggerfall-unity/tree/2343305d1d83ccc0de57a81e3b1e61188a997e34)
- Root license reported by GitHub: MIT.
- Relationship: additional research reference; code imported: **no**.

## OpenMW/openmw

Related reference: Morrowind-compatible engine and editor. GitHub is a mirror; upstream development is hosted on GitLab.

- Repository: [OpenMW/openmw](https://github.com/OpenMW/openmw)
- Observed branch: `master`
- Observed revision: [`46bd4599203e`](https://github.com/OpenMW/openmw/tree/46bd4599203ee52ffc0f3e8edb3fc159a0303a49)
- Root license reported by GitHub: GPL-3.0.
- Relationship: additional research reference; code imported: **no**.

## hedge-dev/UnleashedRecomp

Additional researched reference: Sonic Unleashed static recompilation and modding.

- Repository: [hedge-dev/UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp)
- Observed branch: `main`
- Observed revision: [`cf829a9eca8f`](https://github.com/hedge-dev/UnleashedRecomp/tree/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c)
- Root license reported by GitHub: GPL-3.0.
- Relationship: additional research reference; code imported: **no**.

## Release and video references

- [MW2 video: The Modern Warfare 2 Rust Rewrite is Here...](https://www.youtube.com/watch?v=9UbADrcEW5w) — format reference: introduce a working game, make an AI-assisted edit, test it, then attempt a larger crossover. Reviewed through its transcript.
- [SkyCraft 0.1.0](https://github.com/chasmlol/SkyCraft/releases/tag/v0.1.0) — originally shared release.
- [SkyCraft 0.1.1](https://github.com/chasmlol/SkyCraft/releases/tag/v0.1.1) — adds terrain digging and explosion craters; those features should not be attributed to the original 0.1.0 tag.
- [2010 Rust Rewrite Mashup 0.3.2](https://github.com/chasmlol/2010-rust-rewrite-mashup/releases/tag/v0.3.2) — inspected Windows release and listed integration bugs.
- [Skate 3 experimental release](https://github.com/SK8-ENGINE/skate-3-rust-engine/releases/tag/experimental) — rolling release; its contents can change.

## Supporting references named by IW4L

These are upstream research/tool credits, not dependencies of this repository:

- [OpenAssetTools](https://github.com/Laupetin/OpenAssetTools)
- [OpenAssetTools x64 fork](https://github.com/iw4x-x64/oat)
- [IW4x](https://github.com/iw4x/iw4x-client)
- [KisakCOD](https://github.com/SwagSoftware/KisakCOD)
- [Ghidra](https://github.com/NationalSecurityAgency/ghidra)
- [MinecraftOSS crates included in the mashup](https://github.com/chasmlol/2010-rust-rewrite-mashup/tree/main/third_party/minecraftoss) — the fork records source commit 4013a68; confirm component provenance before import.

## Recording future imports

For every code import, record the source URL, exact revision, copied paths, applicable license/NOTICE files and our modifications. Change the relationship from reference to imported dependency only after that import actually happens.

