#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CARGO_BIN="${CARGO:-$HOME/.cargo/bin/cargo}"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo "This build script targets Apple Silicon macOS." >&2
  exit 2
fi
if [[ ! -x "$CARGO_BIN" ]]; then
  echo "Install Rust from https://rust-lang.org/tools/install/ and run this script again." >&2
  exit 2
fi
JOBS="${MW2AI_BUILD_JOBS:-8}"
"$CARGO_BIN" build --manifest-path "$ROOT/Cargo.toml" --target-dir "$ROOT/target" --locked --release -p mw2ai-launcher -j "$JOBS"
"$CARGO_BIN" build --manifest-path "$ROOT/runtime/Cargo.toml" --target-dir "$ROOT/runtime/target" --locked --profile play -p launcher -j "$JOBS"
OUTPUT="${MW2AI_OUTPUT_DIR:-$ROOT/dist}"
mkdir -p "$OUTPUT"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/mw2ai-bundle.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
APP="$STAGE/Modern Warfare 2 AI.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/runtime" "$APP/Contents/Resources/licenses"
xcrun swiftc -swift-version 5 -target arm64-apple-macos14.0 -parse-as-library -O -framework SwiftUI -framework AppKit \
  "$ROOT/macos/Launcher.swift" -o "$APP/Contents/MacOS/Modern Warfare 2 AI"
cp "$ROOT/macos/Info.plist" "$APP/Contents/Info.plist"
cp "$ROOT/target/release/mw2ai" "$APP/Contents/Resources/mw2ai"
cp "$ROOT/runtime/target/play/iw4l" "$APP/Contents/Resources/runtime/iw4l"
cp "$ROOT/LICENSE" "$APP/Contents/Resources/licenses/PROJECT-LICENSE"
cp "$ROOT/NOTICE" "$APP/Contents/Resources/licenses/PROJECT-NOTICE"
cp "$ROOT/runtime/LICENSE" "$APP/Contents/Resources/licenses/UPSTREAM-LICENSE"
cp "$ROOT/runtime/NOTICE" "$APP/Contents/Resources/licenses/UPSTREAM-NOTICE"
cp "$ROOT/runtime/crates/ui/assets/OFL-Oxanium.txt" "$APP/Contents/Resources/licenses/"
cp "$ROOT/runtime/crates/console/assets/COPYING-FreeFont.txt" "$APP/Contents/Resources/licenses/"
cp "$ROOT/docs/MAC-SETUP.md" "$APP/Contents/Resources/README.md"
python3 "$ROOT/scripts/collect-licenses.py" --output "$APP/Contents/Resources/licenses/dependencies"
# Finder metadata on local build outputs is incompatible with code signing.
# Remove only these metadata fields, never quarantine or system trust controls.
xattr -rd com.apple.FinderInfo "$APP" 2>/dev/null || true
xattr -rd com.apple.ResourceFork "$APP" 2>/dev/null || true
codesign --force --sign - "$APP/Contents/Resources/runtime/iw4l"
codesign --force --sign - "$APP/Contents/Resources/mw2ai"
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"
ditto -c -k --keepParent --norsrc "$APP" "$OUTPUT/Modern-Warfare-2-AI-Mac-Setup-Preview.zip"
ditto --norsrc "$APP" "$OUTPUT/Modern Warfare 2 AI.app"
codesign --verify --deep --strict "$OUTPUT/Modern Warfare 2 AI.app"
(cd "$OUTPUT" && shasum -a 256 Modern-Warfare-2-AI-Mac-Setup-Preview.zip > SHA256SUMS.txt)
echo "Built $OUTPUT/Modern Warfare 2 AI.app"
