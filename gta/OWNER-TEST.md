# Elden Los Santos — owner preview

**2026-10-05 complete-model/material candidate.** Malenia’s helmet/additional armor restored from the original NPC display masks. Original color/normal texture pixels and source clips are preserved; GTA shader adaptations remain approximations. New selection: Malenia, Starscourge Radahn, Fire Giant and Godfrey. Crab/Wolf removed from the menu.

Hari authorized autonomous technical Story Mode/spawn/screenshots for this candidate. Installation and actual rendered results are recorded in HANDOFF.md; this guide alone does not establish a pass.

## Start

1. When the GPU has been explicitly reserved for your GTA test, open **Check Elden Los Santos.command** in `~/Applications/EldenLosSantosPreview/`. If it passes, open **Play Elden Los Santos.command** in the same folder. Play repeats the checks and launches GTA V Legacy through CrossOver under the exclusive shared GPU lock. Keep using these guarded shortcuts for this mod preview.
2. Choose **Story Mode** and load your free-roam save. The owner has completed the tutorial.
3. Look for **ELDEN LOS SANTOS** at the top left. Creatures now start **AGGRESSIVE**. Press **4** before spawning to inspect them with combat paused.

Use the **top-row number keys 1–6**. No Fn key is needed. These keys are reserved for the mod while playing; use GTA’s weapon wheel to change weapons. Numpad flight controls are left alone.

| Key | Action |
| --- | --- |
| 1 | Select Malenia, Starscourge Radahn, Fire Giant, or Godfrey. |
| 2 | Spawn the selected creature ahead of you. One active boss at a time while the new heavy roster is validated. |
| 3 | Remove this mod's creatures. Keeps your helicopter. |
| 4 | Pause/resume creature aggression. Starts ON. |
| 5 | Receive a carbine and RPG with ammunition. |
| 6 | Place an armed Buzzard nearby, or replace your destroyed one. Keeps a usable helicopter. |

Use a clear outdoor area for the first test. These are animated creature objects with custom GTA-side combat; they are not a port of the Elden Ring executable or its complete AI.

## Malenia test — stop at the first failed gate

1. **Spawn and appearance:** load your existing Story Mode save in a clear outdoor area. Malenia is the default selection. Press **4 once** to pause aggression, then **2 once**. Wait up to five seconds. If “Failed zlib call,” a loading failure, or a crash returns, stop; do not cycle the roster or keep retrying. Send the exact message.
2. **Close-up:** with aggression paused, inspect her face/helmet/hair, body proportions, sword and feet from the front and side. She should hold an animated idle, with no crumpled mesh or missing texture patches. If wrong, send one close-up screenshot and stop; logs cannot establish visual quality.
3. **Sword encounter:** press **5**, shoot once or twice, then **4** to resume. Back away and sidestep a swing. Check foot/body movement and the lunge, committed facing, a connected hit when in reach, and a miss when you evade. Nearby NPCs may also attract her aggression. She currently has one source sword attack, not the full Elden Ring moveset.
4. **Damage and stagger:** use several rifle rounds, one RPG, then a moving-car impact. HP should drop, a heavy hit should interrupt her with a visible reaction, and a parked car touching her should not drain HP. Source tests alone do not confirm these channels.
5. **Defeat and reset:** finish her, observe the kneeling defeat and settled body, press **3**, then **2**. Repeat three times; HP and attack state should reset and no old bodies or damage should remain.
6. **Helicopter:** press **6** and test Buzzard weapons. Report damage, stability and how the encounter looks from the air. Key3 keeps your helicopter; key6 preserves a usable one and can replace its destroyed wreck.

If the first gate fails, the later gates are not passed. If appearance fails, stop before a long combat session. The most useful report is the failed step plus a screenshot or exact error; this thread will read its own private logs. After Malenia, repeat the appearance/animation gate for Radahn, Fire Giant and Godfrey, clearing between selections. Use a large open area for the giants.

## Locations on this Studio

- Private package: `~/Applications/EldenLosSantosPreview/`
- Active profile: `~/Library/Application Support/EldenLosSantos/Game/`
- Preserved original game: `~/Library/Application Support/EldenLosSantos/Retail/`
- Profile state: `~/Library/Application Support/EldenLosSantos/profile-state.json`

Steam's existing GTA folder points to the active profile. APFS cloning shares the original game blocks; this did not create a second full-size game-data copy. Only GTA5.exe's `dinput8` DLL override was set in Wine; its prior value is recorded. Other games' overrides, authentication stores and existing saves were not changed.

## Restore the unmodified game

Quit GTA first, then run:

```sh
python3 ~/Applications/EldenLosSantosPreview/Tools/profile_manager.py restore
```

The command restores the exact original directory to Steam's path and restores the prior GTA-specific DLL override. It keeps the preview profile available. To activate it again, use the same command with `activate` instead of `restore`. Neither command launches a game.

## Known limits

- Imported Elden Ring geometry, rigs and original clips with GTA-side combat. This is not a port of Elden Ring AI or its complete boss movesets.
- Five full-rate clips per boss: idle, run, one attack, stagger and defeat. Contact windows come from original TAE AttackBehavior events; geometry sweeps use the native playback phase. Radahn uses both hand-held swords. Godfrey has two source attack contact windows.
- No original spell/VFX, voice or cloth simulation. No travelling projectile is implemented. Source hair/fur materials require GTA alpha/shader adaptation, which must be judged in real rendered frames.
- Conservative body boxes receive native bullets/physics; sampled weapon sweeps handle outgoing contact. Movement stops at obstacles but does not route around buildings. Giants may be constrained in city streets.
- Original source diffuse/normal DDS mip bytes are preserved, with header-only sRGB normalization. Derived gloss/metal/opacity maps are source-resolution lossless RGBA. GTA lighting will differ from Elden Ring; do not claim one-to-one renderer parity.
- Native gun, explosion, vehicle and helicopter damage, stagger, death and repeated reset need candidate-specific gameplay checks. No FPS or complete encounter acceptance is implied by export/tests.
- Story Mode only. Network-session guard remains active. Keep the private rollback until owner acceptance.

**Do not upload or share the private package or its motion-enabled ASI:** it contains assets extracted from your games and separately obtained runtime files. The public repository distributes original source and conversion/setup instructions, not those files.
