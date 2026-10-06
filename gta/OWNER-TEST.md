# Elden Los Santos — owner preview

**2026-10-06 city spectacle candidate — owner test required.** The previous build received the owner's “everything here looks great” feedback. This update adds five requested single-player features and the staged two-sided cape correction. **GTA was not opened for this update, as requested.** Source/build checks do not verify its new visuals, AI or balance. Co-op is excluded.

The previous candidate's actual M3 checks covered car impacts, player/Buzzard weapons, source contact timing, defeat and reset. Those results remain baseline evidence, not a pass for this candidate. Malenia, Starscourge Radahn, the approximately **60m Fire Giant**, and Godfrey are retained with the same source meshes and clips; only the already-staged cape backfaces change the asset package.

## Start

1. When other heavy GPU work is stopped or coordinated, open **Check Elden Los Santos.command** in `~/Applications/EldenLosSantosPreview/`. If it passes, open **Play Elden Los Santos.command** in the same folder. Play detects an existing owner reservation or uses the normal exclusive gate, refuses foreign/emergency holds, repeats the checks and launches GTA V Legacy through CrossOver under the exclusive shared GPU lock. Keep using these guarded shortcuts for this mod preview.
2. Choose **Story Mode** and load your free-roam save. The owner has completed the tutorial.
3. Look for **ELDEN LOS SANTOS** at the top left. Creatures now start **AGGRESSIVE**. Press **4** before spawning to inspect them with combat paused.

Use the **top-row number keys 0–9**. No Fn key is needed. These keys are reserved for the mod while playing; use GTA’s weapon wheel to change weapons. Numpad flight controls are left alone.

| Key | Action |
| --- | --- |
| 1 | Select Malenia, Starscourge Radahn, Fire Giant, or Godfrey. |
| 2 | Spawn the selected creature ahead of you. One active boss at a time while the new heavy roster is validated. |
| 3 | Remove this mod's creatures. Keeps your helicopter. |
| 4 | Pause/resume creature aggression. Starts ON. |
| 5 | Receive a carbine and RPG with ammunition. |
| 6 | Place an armed Buzzard nearby, or replace your destroyed one. Keeps a usable helicopter. |
| 7 | Toggle city support. Starts ON: one police car, one SWAT SUV and one police helicopter, at most seven responders. |
| 8 | Toggle clean filming HUD. Keeps the boss bar; hold GTA's weapon-wheel key normally when needed. |
| 9 | Cycle wide, side, detail and normal cameras. Movement/firing, a menu or20 seconds returns control to the gameplay camera. |
| 0 | Clear and restart the same boss at its original spawn point, with full HP and phase1. Keeps your helicopter; move away from that spawn point first. |

Use a clear outdoor area for the first test. These are animated creature objects with custom GTA-side combat; they are not a port of the Elden Ring executable or its complete AI.

## Owner play / subjective review

### New features — recommended first pass

1. **Radahn traffic:** start beside a broad road with ordinary traffic. Select Radahn with1, spawn with2, then stand about30–50m away. During his original attack animation, up to three nearby ambient cars should lift, then fly toward the position he committed to. Dodge sideways. Your current vehicle, the supplied Buzzard and mission vehicles are excluded. A parking lot/airfield with no ambient cars cannot demonstrate this feature.
2. **City response:** leave7 ON. After roughly6/18/30 seconds, police, SWAT and helicopter support each attempt to arrive. They use native driving/flying/shooting tasks against the boss, with actual bullet damage. Unsafe road placement or a failed model load skips that unit and logs the reason. Check that they target the boss, that the boss can retaliate, and whether the fight becomes too easy. Press7 to compare without support.
3. **Second phase:** reduce a boss below half health. Expect one visible original reaction animation, an UNBOUND banner and colored light, then faster attacks/movement. Malenia gets faster attack cadence; Radahn can throw five cars; Fire Giant launches three fireballs; Godfrey gains an expanding ground shockwave. These are custom GTA encounter phases using existing original clips, **not imported ER phase2 movesets**. The boss remains damageable throughout the transition.
4. **Giant and helicopter:** clear the encounter, travel to a broad beach/airfield, select Fire Giant and spawn. Use6 for the Buzzard. Fireballs should visibly travel from the sampled source weapon position, then explode only when a native collision sweep hits something. A missed shot expires. Fly sideways or use buildings as cover; verify incoming helicopter damage and return fire. His melee contact also starts a ground shockwave that pushes/damages traffic. Existing conservative navigation still cannot route a60m boss around buildings.
5. **Filming and reset:** try8 and9, move or fire to exit the camera, then press0 from a safe distance. Check full boss health, phase1, and removal of old fireballs/responders. Previously thrown ambient cars remain normal GTA traffic/debris; reset does not undo city damage or teleport/heal the player. Inspect Malenia's cape from the side/back and while moving.

Report the first failing step, boss and exact symptom. A short recording is most useful for timing/camera/physics problems. Check FPS with city support on and off; the new effects/AI have not been performance-tested.

### Core encounter regression pass

1. **Spawn and appearance:** load your existing Story Mode save in a clear outdoor area. Malenia is the default selection. Press **4 once** to pause aggression, then **2 once**. Wait up to five seconds. If “Failed zlib call,” a loading failure, or a crash returns, stop; do not cycle the roster or keep retrying. Send the exact message.
2. **Close-up:** with aggression paused, inspect her face/helmet/hair, body proportions, sword and feet from the front and side. She should hold an animated idle, with no crumpled mesh or missing texture patches. If wrong, send one close-up screenshot and stop; logs cannot establish visual quality.
3. **Sword encounter:** press **5**, shoot once or twice, then **4** to resume. Back away and sidestep a swing. Check foot/body movement and the lunge, committed facing, a connected hit when in reach, and a miss when you evade. Nearby NPCs may also attract her aggression. She currently has one source sword attack, not the full Elden Ring moveset.
4. **Damage and stagger:** use several rifle rounds, one RPG, then a moving-car impact. HP should drop, a heavy hit should interrupt her with a visible reaction, and a parked car touching her should not drain HP. Those incoming channels were checked in the actual game; judge whether their strength feels right.
5. **Defeat and reset:** finish her, observe the kneeling defeat and settled body, press **3**, then **2**. Repeat three times; HP and attack state should reset and no old bodies or damage should remain.
6. **Helicopter:** press **6** and test Buzzard weapons. Report damage, stability and how the encounter looks from the air. Key3 keeps your helicopter; key6 preserves a usable one and can replace its destroyed wreck.

If the first gate fails, the later gates are not passed. If appearance fails, stop before a long combat session. The most useful report is the failed step plus a screenshot or exact error; this thread will read its own private logs. After Malenia, repeat the appearance/animation gate for Radahn, Fire Giant and Godfrey, clearing between selections. Use a large open area for the giants.

## Building-height Fire Giant / helicopter test

1. Use a broad beach or airfield with open ground ahead. At this scale a city street can place his body through buildings.
2. From a fresh launch: press **4** to pause aggression, **1 twice** to select Fire Giant, then **2**. Wait for the full two-part animated model.
3. Press **6** for the armed Buzzard, enter it with normal GTA controls, and climb above nearby obstacles. Circle the giant's torso/head. His approximate height is60m and his body collision scales with him.
4. Test helicopter guns/rockets, then **4** to enable his aggression. Actual Buzzard gun/rocket damage and giant defeat were verified, and a source attack contacted an occupied Buzzard. Pilot handling and difficulty remain your subjective call.
5. **3** clears the giant while preserving your helicopter. **2** starts a fresh boss.

## Locations on this Studio

- Private package: `~/Applications/EldenLosSantosPreview/`
- Active profile: `~/Library/Application Support/EldenLosSantos/Game/`
- Preserved original game: `~/Library/Application Support/EldenLosSantos/Retail/`
- Profile state: `~/Library/Application Support/EldenLosSantos/profile-state.json`

Steam's existing GTA folder points to the active profile. APFS cloning shares the original game blocks; this did not create a second full-size game-data copy. Only GTA5.exe's `dinput8` DLL override was set in Wine; its prior value is recorded. Other games' overrides, authentication stores and existing saves were not changed.

## Restore the previous accepted mod build

Quit GTA, then run this Studio-local command. It uses the same stopped-game checks and rollback journal; it does not launch GTA:

```sh
python3 ~/Applications/EldenLosSantosPreview/Tools/upgrade_profile.py --candidate "$HOME/Library/Application Support/EldenLosSantos/StagedCandidates/20261006-before-city-spectacle"
```

## Restore the unmodified game

Quit GTA first, then run:

```sh
python3 ~/Applications/EldenLosSantosPreview/Tools/profile_manager.py restore
```

The command restores the exact original directory to Steam's path and restores the prior GTA-specific DLL override. It keeps the preview profile available. To activate it again, use the same command with `activate` instead of `restore`. Neither command launches a game.

## Known limits

- Imported Elden Ring geometry, rigs and original clips with GTA-side combat. This is not a port of Elden Ring AI or its complete boss movesets.
- Five full-rate clips per boss: idle, run, one attack, stagger and defeat. Contact windows come from original TAE AttackBehavior events; geometry sweeps use the native playback phase. Radahn uses both hand-held swords. Godfrey has two source attack contact windows.
- No original spell/VFX, voice or cloth simulation. This candidate adds GTA-side travelling fireballs, gravity cars, shockwaves and phase2 logic; appearance/contact/native AI behavior remain unverified in the game. Source hair/fur materials use GTA shader adaptations.
- Conservative body boxes receive native bullets/physics; sampled weapon sweeps handle outgoing contact. Movement stops at obstacles but does not route around buildings. Giants may be constrained in city streets.
- Original source diffuse/normal DDS mip bytes are preserved, with header-only sRGB normalization. Derived gloss/metal/opacity maps are source-resolution lossless BGRA8. GTA lighting will differ from Elden Ring; do not claim one-to-one renderer parity.
- Native car/weapon/attack/death/reset checks passed on the previous core build; this candidate needs the above regression pass. Approximate earlier rates were27–31FPS in1080p windows. New effects and city AI are not covered by those measurements.
- Story Mode only. Network-session guard remains active. Keep the private rollback until owner acceptance.

**Do not upload or share the private package or its motion-enabled ASI:** it contains assets extracted from your games and separately obtained runtime files. The public repository distributes original source and conversion/setup instructions, not those files.
