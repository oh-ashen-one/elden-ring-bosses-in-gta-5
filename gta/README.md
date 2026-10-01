# Elden Ring × GTA V: damage probe groundwork

Status: original source groundwork only. No game launch or in-game verification has occurred. This is not an Elden Ring boss implementation or a playable crossover release.

This diagnostic ASI plugin requests one GTA-owned test actor using F6, shows its raw native health, logs observed health loss and death, and removes the owned actor using F7. It does not install itself, modify retail files, spawn a helicopter, or claim that any damage channel has passed an in-game check. The intended next test covers firearms, explosions, vehicle impacts and helicopter weapons separately. Damage classification and balancing are not implemented.

## Build

Portable state/ABI checks on macOS or Linux:

```sh
cmake -S gta -B build/gta-native -DCMAKE_BUILD_TYPE=Release
cmake --build build/gta-native
ctest --test-dir build/gta-native --output-on-failure
```

Cross-compile the Windows x64 ASI on the Mac with CMake and Homebrew mingw-w64:

```sh
cmake -S gta -B build/gta-win64 -DCMAKE_TOOLCHAIN_FILE=tools/mingw.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build/gta-win64
```

The output is `build/gta-win64/EldenLosSantosProbe.asi`. No vendor SDK or runtime is required to compile the original dynamic ABI wrapper. A separately obtained compatible Script Hook V runtime and ASI loader are required to use it in a dedicated GTA Story Mode mod profile. Runtime compatibility through CrossOver has not been tested. Do not modify the original installation to test this draft.

## Loader dependency

The build generates a small import library from the original `tools/runtime.def`. Its C alias resolves to Script Hook V's game-version export, ensuring the Windows loader loads the runtime before our DllMain binds the other APIs. The resulting PE import table and all eight dynamic export names were checked against the official runtime. No vendor library is copied into the repository. The verified Windows build uses MinGW-w64; MSVC support is not implemented.

## Runtime contract and remaining checks

- No actor appears until F6; F7 removes the task-owned actor. Press F7 before a Script Hook development reload, because detach callbacks cannot safely call game natives.
- Streaming has a ten-second timeout and requires a ground query to succeed.
- It uses GTA's actual health; it does not simulate damage or periodically heal the test actor. Critical hits and ragdoll are disabled for this diagnostic target.
- A native-dead actor is recorded as dead even when the engine reports nonzero raw health. Lost actors are recorded separately from kills.
- The UI identifies the subject as a **GTA test actor**. No Elden Ring model, animation, attack or AI has been imported.
- The plugin writes `EldenLosSantosProbe.log` next to itself. Keep runtime logs and assets local.
- Verify keyboard focus, spawn placement, target deletion, save/load behavior, model streaming failure and every damage source in an actual game session before using this foundation further.

## Provenance

Original code is covered by the repository's Apache-2.0 license. Script Hook V is Alexander Blade's separately distributed runtime: https://www.dev-c.com/gtav/scripthookv/ . Its SDK and runtime archives prohibit archive redistribution and are not included here. The wrapper uses API signatures/native identifiers from the official SDK and runtime export table for interoperability; it does not copy the SDK implementation or sample code.

Inspected official archives (local research only):

- ScriptHookV_SDK_1.0.617.1a.zip — SHA-256 `56b6ad265b2b93aa4e73f79f97949d72f3683a35576b977e63dde91c6485fe22`
- ScriptHookV_3889.0_1158.13.zip — SHA-256 `b64c97c3353906f14621e7e9511e4aec2a7d436ecc21ed124d3816585e2e6188`

On 2026-10-01 the locally installed GTA5.exe reports file version 1.0.3889.0, matching the runtime's advertised Legacy build. This is a version match, not proof that the runtime works on CrossOver.
