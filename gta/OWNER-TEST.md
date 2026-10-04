# Elden Los Santos — owner preview

**2026-10-04 Malenia streaming repair candidate.** The previous owner test crashed while loading Malenia’s model, before her animation/combat ran. This candidate changes only her embedded texture storage: same dimensions and material references, seven unused maps removed, generated maps encoded in high-quality BC7. The mesh, rig, animations, collision and gameplay plugin are preserved. It is ready for a controlled owner test, not a completed or visually accepted fight.

**GTA remains closed at Hari’s request.** No automatic test or restart is queued. The confirmed old failure and exact limits are in `CRASH-20261004.md` in the public source.

## Start

1. When the GPU has been explicitly reserved for your GTA test, open **Check Elden Los Santos.command** in `~/Applications/EldenLosSantosPreview/`. If it passes, open **Play Elden Los Santos.command** in the same folder. Play repeats the checks and launches GTA V Legacy through CrossOver under the exclusive shared GPU lock. Keep using these guarded shortcuts for this mod preview.
2. Choose **Story Mode** and load your free-roam save. The owner has completed the tutorial.
3. Look for **ELDEN LOS SANTOS** at the top left. Creatures now start **AGGRESSIVE**. Press **4** before spawning to inspect them with combat paused.

Use the **top-row number keys 1–6**. No Fn key is needed. These keys are reserved for the mod while playing; use GTA’s weapon wheel to change weapons. Numpad flight controls are left alone.

| Key | Action |
| --- | --- |
| 1 | Select Malenia, Red Wolf of Radagon, or Giant Crab. |
| 2 | Spawn the selected creature ahead of you. Maximum three at once. |
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

If the first gate fails, the later gates are not passed. If appearance fails, stop before a long combat session. The most useful report is the failed step plus a screenshot or exact error; this thread will read its own private logs. Wolf and Crab are not the acceptance target and their earlier visual failures are not claimed fixed.

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

- Script Hook V, the ASI loader and this script ran under CrossOver on GTA 1.0.3889.0. The v2 package failed creature creation and later crashed after a crab request. The v3 texture repair still failed object creation. v4 proved stock-object creation works, while the custom model still failed. v5 registration alone still failed. Runtime isolation then identified the Dynamic archetype flag; v7 applied it and the owner confirmed all three visible imports. The current candidate’s appearance, animation and aggressive combat are still unverified.
- Malenia uses selected phase-one meshes. Her GTA-side behavior includes chase, a committed sword swing, stagger and faster pursuit below half health. The five selected clips were inspected offline; original ER AI, the full moveset and second phase are not ported.
- Wolf/Crab ranged effects and damage use GTA explosions; original Elden Ring VFX, spell systems, AI, sounds and cloth simulation are not ported.
- Malenia uses a conservative torso box for GTA bullets/physics and a separate sampled sword sweep for attacks. Her movement probes stop at obstacles; they do not plan a route around buildings. Wolf and Crab retain coarse whole-body boxes. Real contact timing needs the guarded technical run.
- Native health loss is preferred for incoming damage. Hit flags provide a logged fallback where drawable objects do not reduce native health. Weapon/explosion/vehicle balance still needs calibration.
- Materials preserve source image dimensions and use GTA's skinned-object normal/specular shader. Hair opacity comes from the HairLong material's actual normal atlas. Specular response, layered shading and shell fur remain approximations; this is not yet Elden Ring visual parity. Optional meshes may need visibility tuning.
- No FPS, controller compatibility or completed ten-minute gameplay claim is made.
- Story Mode only. The plugin guards network sessions; Script Hook V itself does not support GTA Online.

**Do not upload or share the private package or its motion-enabled ASI:** it contains assets extracted from your games and separately obtained runtime files. The public repository distributes original source and conversion/setup instructions, not those files.
