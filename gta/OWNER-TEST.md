# Elden Los Santos — owner preview

**Diagnostic build v6.** Creature spawning is still unresolved. Hari approved one automatic, model-only import check once Story Mode is loaded. It creates and immediately removes test objects and writes results; these are not playable bosses. Key **7** starts the same check manually; **3** cancels it. No controller, tutorial or combat automation is performed.

## Start

1. Launch **GTA V Legacy** from **Steam inside CrossOver**, as usual.
2. Choose **Story Mode** and load your free-roam save. The owner has completed the tutorial.
3. Look for **ELDEN LOS SANTOS** at the top left. Combat starts **OFF** so you can inspect the creatures first.

Use the **top-row number keys 1–6**. No Fn key is needed. These keys are reserved for the mod while playing; use GTA’s weapon wheel to change weapons. Numpad flight controls are left alone.

| Key | Action |
| --- | --- |
| 1 | Select Malenia, Red Wolf of Radagon, or Giant Crab. |
| 2 | Spawn the selected creature ahead of you. Maximum three at once. |
| 3 | Remove this mod's creatures. Keeps your helicopter. |
| 4 | Toggle creature attacks/pursuit. Starts OFF. |
| 5 | Receive a carbine and RPG with ammunition. |
| 6 | Place an armed Buzzard nearby. Enter/fly it normally. |

Use a clear outdoor area for the first test. These are animated creature objects with custom GTA-side combat; they are not a port of the Elden Ring executable or its complete AI.

## Short first test

1. Start with **Malenia** (the default selection), keep combat OFF and press **2 once** outdoors. If she fails to appear, stop here; don’t cycle through other creatures or repeatedly retry. The log now distinguishes model loading, animation loading and creation. A failed creature is locked for that session.
2. Shoot it while combat is OFF. Confirm the health bar drops.
3. Toggle combat ON. Check pursuit, close attacks and the red warning sphere before a ranged blast.
4. Use the RPG, a vehicle collision, then the helicopter weapons. Check each damage channel separately.
5. Defeat the creature, clear it with 3, then spawn another one.

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

- Script Hook V, the ASI loader and this script ran under CrossOver on GTA 1.0.3889.0. The v2 package failed creature creation and later crashed after a crab request. The v3 texture repair still failed object creation. v4 proved stock-object creation works, while the custom model still failed. v5 adds prop registration; owner retest is pending.
- Malenia uses selected phase-one meshes. The AI is custom: chase, melee wind-up, stagger, increased aggression below half health and telegraphed ranged blasts.
- Ranged effects and damage use GTA explosions; original Elden Ring VFX, spell systems, AI, sounds and cloth simulation are not ported.
- Collision uses whole-body boxes. Direct line-of-sight movement is simple, with no pathfinding around buildings. Animation-role choices and strike timing need owner review.
- Native health loss is preferred for incoming damage. Hit flags provide a logged fallback where drawable objects do not reduce native health. Weapon/explosion/vehicle balance still needs calibration.
- Materials use original textures with approximated layered shaders; Malenia's procedural hair tint is baked from source data. Optional source mesh variants may need visibility tuning.
- No FPS, controller compatibility or completed ten-minute gameplay claim is made.
- Story Mode only. The plugin guards network sessions; Script Hook V itself does not support GTA Online.

**Do not upload or share the private package:** it contains assets extracted from your games and separately obtained runtime files. The public repository distributes original source and conversion/setup instructions, not those files.
