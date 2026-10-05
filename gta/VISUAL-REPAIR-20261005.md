# October 5 visual repair

## Observed failure

The owner’s actual GTA screenshots showed missing Malenia head/armor pieces, blue/chrome material patches and opaque fur fins. The owner confirmed improved original running/attack/hit animations and health reduction. Those observations supersede the older claim that the October 4 streaming candidate had never loaded.

## Concrete corrections

- Owned `regulation.bin` NPC display masks select Malenia groups 0, 10, **12, 13**, 21. The old manual selection omitted 12 (head metalwork, 4,558 vertices) and 13 (armor, 9,649 vertices). The selected model now has 48,764 source vertices and 61,914 triangles. No decimation was applied.
- Removed the shared white specular texture and uniform high reflection response. Original normal RG supplies surface detail, normal B supplies gloss, and original metallic maps supply the adapted specular response. Hair/fur opacity uses the authored strand mask, secondary UVs and vertex layer alpha. These are explicit GTA shader adaptations, not an Elden Ring shader port.
- Original diffuse and normal DDS pixel/mip payloads are copied unchanged. Only equivalent sRGB header metadata is normalized for GTA Legacy. Derived tint/opacity/specular maps use full-resolution lossless RGBA. No additional BC7/BC5 recompression is used in this candidate.
- Standard YTD parent dictionaries keep texture data separate from skinned drawables. Large full-resolution lossless maps can still produce 64 MiB graphics pages. This remains a streaming/performance risk requiring actual tests; the old 32 MiB review budget is not claimed as passed. All 39 resources independently inflate correctly; none uses an extended-size archive header.
- Fire Giant’s 304-bone target rig needs local byte-index skin palettes. Every weighted global joint association is preserved; the largest geometry uses 139 joints. No weighted joints are dropped.
- Fire Giant and Godfrey require original source rest axes for animated nonuniform scaling. Blender-adjusted axes caused sheared local transforms. Radahn’s small cloth-joint head drift is corrected within a strict 2 cm bound, retaining the downstream 2 mm joint guard.
- Original five clips per boss are converted at full rate. No custom animation is authored in Blender. The pinned Havok reader’s ThreeComp48 tuple-read defect has a narrow compatibility adapter. Geometry conversion uses Blender/Sollumz; animation conversion reads source poses directly.
- Original TAE AttackBehavior intervals drive weapon contact. Radahn samples both hand-held swords; Godfrey’s attack has two separate source contact windows. Gameplay movement, damage, collision and decisions remain GTA-side code. No original ER AI or projectile system is claimed.

## Roster

Malenia, Starscourge Radahn, Fire Giant and Godfrey replace the old Malenia/Wolf/Crab selector. One boss is active at a time during initial large-model validation. Clear before choosing another. The public `roster.json` records display masks and melee equipment selection.

Radahn’s leg armor has coincident source triangles. The conversion emitted 4,590 fewer triangles there. A geometric coverage check found every source triangle covered within 0.000001661 m, with no unmatched face above 0.1 mm. This establishes surface coverage only; it does not establish identical shading or rendered quality.

## Reuse and reproducibility

Keep the existing working native ASI, Script Hook V, RageOpenV, pinned Soulstruct/Havok, Blender/Sollumz and CodeWalker conversion route. No er-mario engine hooks were copied. Its source-pose/contact/host-damage methods inform the existing architecture; see ER-MARIO-LESSONS.md.

`build_owned_assets.py` now reads the four-boss roster and runs geometry-only Blender conversion through the explicitly supplied shared GPU root, followed by source material adaptation, corrected source animation conversion, private motion generation and native packaging. Pass `--gpu-root /absolute/verified/coordinator`. The helper `er_npc_masks.c` reads display masks with a separately obtained compatible Paramdex NpcParam definition; it never prints keys. Generated assets and motion-bearing binaries remain private.

Twenty offline suites passed before packaging. Native round-trip checks compare animation values and full texture payloads. The pinned CodeWalker reader truncates small block-compressed mip tails in its in-memory readback; the adapter independently checks the complete saved bytes at native texture pointers rather than ignoring that discrepancy.

## Acceptance boundary

Installation receipts, guarded launch, screenshots and actual runtime outcomes belong in HANDOFF.md. A successful export, package audit, source test or spawn is not a completed boss fight. Different lighting, cloth simulation, complete movesets and original ER AI are not provided by copying source assets.
