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

## Actual runtime review and controlled follow-up

The first guarded October 5 Story Mode run spawned Malenia but FAILED the close-up review: visibly distorted pieces and incomplete-looking shading. The owner also reported “looks messed up.” No crash occurred. The source/native checks above did not predict this rendering failure.

A controlled local diagnostic restores only Malenia's full identity/global skin palette while preserving every other native resource. Its distant silhouette is more coherent, but a close-up is still required before attributing the failure to palette handling. Keep that diagnostic distinct from a confirmed fix.

The existing file-only technical request channel now accepts `REVIEW_SPAWN_0` through `REVIEW_SPAWN_3` (one boss slot), `REVIEW_FRONT`, `REVIEW_SIDE`, `REVIEW_DETAIL`, `REVIEW_STOP` and `REVIEW_CLEAR`, each followed by a newline. File: `EldenLosSantos.import-check.request` beside the private ASI. Commands are single-use, Story Mode guarded and contain no arbitrary script/network listener. Inspection pauses aggression and uses a native GTA camera for at most 45 seconds. Ordinary mod keys immediately restore the gameplay camera. This supports actual rendered screenshots; it does not establish a visual pass by itself.

## Decisive face-orientation diagnosis

The fixed native inspection camera showed a coherent Malenia pose with the global identity palette, but apparent wrong surfaces/materials remained. A direct triangle-cross-product versus authored-normal audit found **61,894 inward-facing triangles versus 14 outward** in her old export (helmet alone 4,865 versus 1). The same systematic reversal affected Radahn, Fire Giant and Godfrey. The exporter mirrored FLVER Z and then reversed indices again; the second reversal was wrong for FLVER's original handedness/winding. GTA culled the intended outer surfaces, exposing interior faces. Preserving texture bytes or bone counts could not detect this.

`export_character_glb.py` now keeps original triangle order after the coordinate reflection. `geometry_fidelity.py` repairs ONLY predominantly inward legacy exports into a new directory and preserves topology/materials/animation. `build_dlc.py` refuses overwhelmingly inward inputs. A synthetic regression explicitly exercises the old double-flip failure. Identity/global object skin palettes are retained for rigs that fit byte indices; the large Fire Giant palette still needs its separate native review.

Corrected native XML counts: Malenia 61,894 outward/14 inward; Radahn 170,681/75; Fire Giant 403,032/119; Godfrey 235,964/327. Small residual disagreement can occur in authored smoothing/degenerate surfaces; no per-face heuristic rewinding was applied. This is concrete data evidence, with corrected GTA-rendered acceptance still pending at this checkpoint.

## Live results after winding correction; next candidate

- Actual M3 GTA frames `outward-malenia-front.png` and `outward-malenia-side.png` show restored outside dress, armor, helmet and sword with a coherent idle. This is a real rendering improvement, not full encounter acceptance. Hair/material refinement remains.
- Radahn's armor/swords and Godfrey's armor/axe render, but C[Fur] strands remain opaque. DSAnimStudio's primary shader mapping confirms the colour atlas is UV0 and strand albedo/normal use UV2. `fur_material.py` now flattens that authored opacity/detail into lossless target maps, including tangent-frame conversion. Overlapping UV0 islands choose maximum coverage; this remains an explicit renderer adaptation.
- Fire Giant's 304-bone object visibly deforms with compact per-geometry indices. `split_large_rig.py` now retains every geometry, weighted bone, tag and ancestor across two identity-indexed render parts (255 and 147 bones). The child shares textures/clips with the primary, attaches to its root, receives the same animation and phase, has no duplicate collision/damage, and is cleaned up with ownership/failure checks.
- Hari requested a building-height giant for helicopter flight. `model_scale: 2.6` makes the measured ~23m idle span about60m. Vertices, bind translations, animation translations, root/weapon tracks, bounds, collision, contact radii/reach and spawn clearance scale together. Rotations/times, topology and texture pixels remain unchanged by scaling. Walk pace remains slow; no flight/damage pass is implied by scaling math.
- The next private package has65 independently audited resources, with one shared Fire Giant texture family/clip dictionary and five render archetypes for four bosses. Live validation of the fur/split/scale candidate is pending.20 offline suites plus the actual ownership cleanup fixture pass;9 asset-fidelity cases cover orientation, UV2 opacity, partitioning and scale.
