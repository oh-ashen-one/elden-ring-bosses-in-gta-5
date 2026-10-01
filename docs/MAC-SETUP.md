# Mac setup preview

This preview contains an Apple Silicon build of the imported IW4L mashup runtime and a native setup app. The Terminal crossover mission is not playable yet. No commercial game assets are included, and automatic Minecraft downloads are disabled.

## Build

On Apple Silicon macOS 14 or newer, install Xcode command line tools and Rust. Then run:

```sh
bash scripts/build-mac.sh
```

The script produces `dist/Modern Warfare 2 AI.app` and a ZIP. It uses local ad-hoc signing, not Apple notarization. It does not alter Gatekeeper or trust settings.

If your checkout is in iCloud/Documents, use a local output folder to avoid File Provider metadata interfering with signing:

```sh
MW2AI_OUTPUT_DIR="$HOME/Applications/Modern-Warfare-2-AI-Preview" bash scripts/build-mac.sh
```

## Skate conversion helper

After supplying your own extracted game, run this from the source checkout:

```sh
python3 scripts/prepare-skate.py \
  --xex "/path/to/Skate 3/default.xex" \
  --out "/path/to/new-conversion"
```

The helper validates the input before downloading any tooling, fetches the exact upstream converter revision, creates a private Python environment and refuses to overwrite an existing conversion or write into the retail installation. It then asks the Mac runtime to generate the board/rig files. Select the resulting `assets` folder in the app.

The missing-input path is verified; actual conversion is still untested without Skate 3 data.

## Add your game data

Open the app and select each available folder. Configuration is saved under `~/Library/Application Support/Modern Warfare 2 AI/settings.json`, outside the game installations.

- **MW2:** Windows PC data for Modern Warfare 2 (2009), including its multiplayer zones. Terminal and common zone headers must be recognized before the launch button is enabled.
- **Skate 3 source:** extracted Xbox 360 data containing `default.xex` and the `data` folder. It requires conversion.
- **Skate 3 converted data:** select the output asset root after conversion; presence checks alone do not prove all animation banks work.
- **Skyrim:** a local Special Edition installation or its Data folder. Dragon conversion/integration remains pending.
- **Minecraft:** a prepared MinecraftOSS root with resourcepacks and datapacks. This preview does not acquire Minecraft or its data for you.

Only MW2 is required to try the base Terminal runtime. Skating needs the additional converted data. A successful setup check verifies selected file signatures/presence, not gameplay completeness.

## Command line

The companion `mw2ai` executable supports:

```sh
mw2ai doctor --json
mw2ai configure --mw2 "/path/to/Modern Warfare 2"
mw2ai configure --skate-source "/path/to/Skate 3"
mw2ai configure --skate-assets "/path/to/converted/assets"
mw2ai launch --runtime "/path/to/iw4l" --map mp_terminal
mw2ai demo-check
```

`MW2AI_HOME` selects a separate settings/output directory for testing. Paths are passed as process arguments, never evaluated as shell code.

`demo-check` runs a deterministic mission-rule scenario. It is not a gameplay, physics, art, or rendering verification.

## What still needs game data

Terminal rendering, shooting and bots, real skating animations/controls, converted Skyrim content, runtime block integration and the full ten-minute run require actual game data and live verification. See the project handoff for current evidence.

## Network behavior

The setup app and its doctor do not listen on a port or contact a service. Launching the upstream game may use its networking stack; review any normal OS permission prompt yourself. This app does not change system permissions.
