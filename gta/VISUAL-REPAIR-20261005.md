# October 5 visual repair

## Observed failure

The owner’s actual GTA screenshots showed missing Malenia head/armor pieces, blue/chrome material patches and opaque fur fins. The owner confirmed improved original running/attack/hit animations and health reduction. Those observations supersede the older claim that the October 4 streaming candidate had never loaded.

## Initial corrections (later live corrections below supersede the palette proposal)

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

## Follow-up from the split-rig live test

The first60m split-rig run spawned both pieces and accepted idle playback but still showed a broken pose. Pinned szio's `gta5/cwxml/drawable.py` explicitly documents that distinct addon rigs sharing Unknown50/54/58 can render with the wrong cached skeleton. Both new parts had retained all three identifiers from the original304-bone rig. `skeleton_identity.py` now refreshes deterministic nonzero topology/bind identifiers after bind changes, scaling and partitioning; a regression ensures different partitions differ. These opaque identifiers are not claimed as Rockstar's exact checksum algorithm.

The C[Fur] mask reduced solid fins, but live Radahn hair showed a white transparent sheen. The converter's pinned `Shaders.xml` supplies the matching normal-spec cutout variant in render bucket3; ordinary hair/fur now uses that cutout path rather than the alpha-blended variant. Godfrey's explicitly spectral Beast_Light materials retain alpha blending. The following candidate changes these cache IDs and material pass selection; actual visual acceptance remains required.

## Verified render improvements and remaining boundary

The distinct skeleton IDs fixed the split Fire Giant pose in actual GTA (`cache-firegiant-front.png`): face, torso, arms and shield now align at the owner-requested building scale. His source has explicit C[c4760]_Snow materials; their white areas are authored snow, not automatically missing textures.

A lossless BGRA8 storage variant preserves all colour/alpha pixels and mip levels while using GTA's conventional uncompressed format. Combined current render frames show red Radahn strands, coherent Malenia and Fire Giant, and Godfrey with Serosh. The earlier Radahn frame also differed in alpha/cutout pass, so the screenshots do not isolate texture format as the sole cause. The generator now emits BGRA8 for derived maps. Hair/ghost shading remains a renderer adaptation and still needs the owner's video-quality judgment.

The bounded technical channel adds `REVIEW_FIGHT`, `REVIEW_HEADSHOT` and `REVIEW_ROCKET`: follow the actor during live GTA-side combat, or fire one actual native carbine/RPG projectile from an elevated point at80% of its body height. These are fixed diagnostics, not arbitrary script execution. The projectile calls explicitly request30/300 damage; they test native collision/intake, not retail weapon balance or a manually piloted helicopter encounter. Current results must be recorded after running them.

## Live damage/movement check and collision follow-up

The fixed native RPG test caused actual damage/fire on Malenia; the rendered `malenia-combat-live.png` shows her moving with the imported run clip and reduced HP. Logs then recorded accepted source defeat playback and `corpse_settled`, followed by cleanup. No complete melee/vehicle/helicopter encounter pass is implied.

The elevated Fire Giant carbine/RPG diagnostic recorded projectile calls but no damage intake. His box used asymmetric local extents from below the feet to65m with a zero local centre. The next asset candidate uses canonical symmetric primitive extents plus a translation to the intended model-space centre, with matching composite centres/radius. It preserves the intended world-space box and render geometry. This is intended to repair upper-body collision and still requires the repeated native test.

## Confirmed upper-body damage and engagement-distance follow-up

Repeating the same elevated probe after canonicalizing the collider produced24 points of native rifle damage and1600 points of applied RPG damage on Fire Giant, with the visible health bar falling (`full-height-native-hits.png`). The firing target was47.84m above his base. This confirms elevated native projectile collision/damage, not a piloted Buzzard fight or exact retail weapon balance.

Malenia visibly chased and played her original sword swing, but the first contact run repeatedly missed at point-blank distance. Her source lunge contributes about3.2m before the active window; the blade's centre crossing is another~2.5m ahead. Engagement now starts at6m rather than3.5m; the damage sweep/radius/window remain unchanged. Physical stagger now persists while aggression is paused or the target disappears. Per-window telemetry records actual actor/target positions for the next live check.

The guarded owner shortcut can select an existing recognized GTA reservation or use the ordinary exclusive gate when no such reservation exists. It creates/clears no pause and still rejects emergency holds and competing renderers. This allows this task's own temporary pause to be released after testing without leaving the owner's shortcut unusable.

## Final bounded runtime outcome

With the6m engagement distance, the actual game recorded four Malenia blade contacts on NPC2818 at native phase~0.432–0.435 and then retargeted. Original run/attack animations advanced with world motion. Native RPG intake triggered source stagger a000_008030. Three fresh Malenia create/clear cycles reset native health to10000; the large Fire Giant primary/child also created and cleared. Logs and images remain private.

The earlier native-damage run logged source defeat and corpse settling. A later intended death still captured the player at the hospital; it is NOT boss-death evidence. Full manual car/Buzzard fighting, complete kill/reset cycles, FPS, and final hair/fur/ghost/video-quality acceptance remain open. The canonical collider fixed elevated native rifle/RPG intake, but it is still coarse body collision. Giant city placement can intersect buildings; test the approximately60m model in an open area.

Final native assets: DLC SHA25611bd019517f539962524f6843713bc6c76af33ada63aaf5301b540aa4d377822, ASI source f71043a. Updated shortcut installer also preserves executable permissions rather than replacing .command files with0644. Transactional mode-repair regression passes. Source/helpers/docs are published on the task branch; retail-derived assets and motion-bearing ASI stay private.

## Continued material and gameplay review

The live vehicle/weapon run exposed remote helicopter shots setting GTA's vehicle-damage flag. Physical impact damage now requires current/recent collision contact with that same actor; native weapon damage still applies. Malenia creates lunge spacing using her existing original run, and heavy damage gets a short post-reaction resistance interval so rockets cannot keep restarting the same reaction. Actual tests and failures remain in the current handoff.

The converter also ignored source `g_AlphaRef` values. `cutout_fidelity.py` maps each primary authored threshold to the target cutout boundary while retaining alpha coverage in derived mips. It preserves RGB and all geometry/clips. The second Fire Giant part uses the parent's texture names/dictionary.

Malenia's P[ChrCustomize][Hair] material references `c2120_hair_shadow_1m` on UV1, alongside strand normal/alpha on UV0; the flat-tint conversion had omitted that shadow. [DSAnimStudio's source shader configuration](https://github.com/Meowmaritus/DSAnimStudio/blob/master/DSAnimStudioNETCore/ShaderConfig/ER/P%5BChrCustomize%5D%5BHair%5D.json) corroborates the UV assignment. `hair_shadow.py` adapts the owned grayscale atlas into the target colour map in linear light while preserving alpha, dimensions, geometry and source tint. Overlapping UV0 islands average authored UV1 samples, an explicit approximation required by this GTA material's single diffuse UV set. This is not an exact ER shader port. No DSAnimStudio code/assets were copied.
