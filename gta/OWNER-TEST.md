# Elden Los Santos — owner preview

**Experimental build. The profile is installed, but mod loading, visuals and combat have not been tested in GTA.** Hari confirmed the unmodified game reaches Story Mode. This preparation did not launch a game, render a scene, control input, or measure FPS.

## Start

1. Launch **GTA V Legacy** from **Steam inside CrossOver**, as usual.
2. Choose **Story Mode** and finish the opening tutorial until you can roam freely.
3. Look for **ELDEN LOS SANTOS** at the top left. Combat starts **OFF** so you can inspect the creatures first.

On a Mac keyboard, hold **Fn** if the function keys activate macOS shortcuts.

| Key | Action |
| --- | --- |
| F5 | Select Malenia, Red Wolf of Radagon, or Giant Crab. |
| F6 | Spawn the selected creature ahead of you. Maximum three at once. |
| F7 | Remove this mod's creatures. Keeps your helicopter. |
| F8 | Toggle creature attacks/pursuit. Starts OFF. |
| F9 | Receive a carbine and RPG with ammunition. |
| F10 | Place an armed Buzzard nearby. Enter/fly it normally. |

Use a clear outdoor area for the first test. These are animated creature objects with custom GTA-side combat; they are not a port of the Elden Ring executable or its complete AI.

## Short first test

1. Spawn one creature. Confirm the model and textures appear and animation plays.
2. Shoot it while combat is OFF. Confirm the health bar drops.
3. Toggle combat ON. Check pursuit, close attacks and the red warning sphere before a ranged blast.
4. Use the RPG, a vehicle collision, then the helicopter weapons. Check each damage channel separately.
5. Defeat the creature, clear it with F7, then spawn another one.

A failure at an earlier step is useful feedback; you do not need to repeat the rest. If anything fails, send the visible error and `EldenLosSantos.log` from the active profile directory. No header usually means the ASI loader/plugin did not load; “Model unavailable” means the creature DLC was not registered.

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

- CrossOver + Script Hook V + RageOpenV + this DLC has not yet been exercised in a game session.
- Malenia uses selected phase-one meshes. The AI is custom: chase, melee wind-up, stagger, increased aggression below half health and telegraphed ranged blasts.
- Ranged effects and damage use GTA explosions; original Elden Ring VFX, spell systems, AI, sounds and cloth simulation are not ported.
- Collision uses whole-body boxes. Direct line-of-sight movement is simple, with no pathfinding around buildings. Animation-role choices and strike timing need owner review.
- Native health loss is preferred for incoming damage. Hit flags provide a logged fallback where drawable objects do not reduce native health. Weapon/explosion/vehicle balance still needs calibration.
- Materials use original textures with approximated layered shaders; Malenia's procedural hair tint is baked from source data. Optional source mesh variants may need visibility tuning.
- No FPS, controller compatibility or completed ten-minute gameplay claim is made.
- Story Mode only. The plugin guards network sessions; Script Hook V itself does not support GTA Online.

**Do not upload or share the private package:** it contains assets extracted from your games and separately obtained runtime files. The public repository distributes original source and conversion/setup instructions, not those files.
