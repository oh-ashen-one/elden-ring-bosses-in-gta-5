# Extending the crossover to more games

## New references

- [universal-modder](https://github.com/rehan-remade/universal-modder), inspected at `15d6f9d5fbd32de9b1884f29ddec3be9133bd912`, MIT. A collection of modding workflows, tools and examples; it is not one ready-made universal game runtime.
- [Minecraft × GTA V worked example](https://github.com/rehan-remade/universal-modder/tree/main/examples/minecraft-gta5-passthrough). A Fabric guest and a ScriptHookV/ReShade host exchange cameras, collision and gameplay events. Its documented environment is Windows/GTA V Legacy.
- [Minecraft In Elden Ring Mod](https://www.youtube.com/watch?v=TmgAK5JjcDM), Tobyn Jacobs. No subtitles or automatic captions were available. Four sampled frames showed Minecraft UI/crafting and a CoD-style weapon in Elden Ring. The exact weapon provenance and implementation are not established by those frames. The supplied universal-modder repository does not contain this Elden Ring implementation.
- [libsm64](https://github.com/libsm64/libsm64), inspected at `fd11813208272b4271d92bd92feb8f3fdbe61be5`. A library exposing Mario movement/rendering, with documented Mac builds. It requires the user's own ROM for assets. Review component licensing before import.

The modding toolkit was researched, not installed; no account, paid generation service or game loader was changed.

## Mac routes

1. **Native host:** keep IW4L as the renderer/simulation host and adapt guest mechanics or content into it. This is the selected route for the first Terminal demo.
2. **Windows host through CrossOver:** test a game-specific plugin inside an isolated task-owned bottle. This can extend the project to games with suitable Windows loaders without assuming they have native Mac ports.

CrossOver 26.2 was found installed on the development Studio. Steam shortcuts exist, but the referenced Steam bottle was not found in the default bottle locations during a read-only status check. No existing bottle was modified or launched.

CrossOver's graphics backends support different Direct3D versions. Base-game compatibility does not establish ReShade, shared-texture, loader or two-process compositor compatibility. CodeWeavers explicitly limits its game testing/support to base games.

Sources: [CrossOver 26 graphics settings](https://support.codeweavers.com/en_US/advanced-settings-in-crossover-mac-26), [mod support](https://support.codeweavers.com/en_US/mods-and-add-ons-with-crossover).

## Shared interface proposal

Give each integration a small adapter, and keep reusable rules independent of the game:

| Adapter capability | Why it is needed |
| --- | --- |
| Clock, session identity and ordered events | Drop duplicates/stale events and keep rewards/damage consistent. |
| Player pose, camera and input ownership | Avoid two controllers moving the player or fighting over the camera. |
| Coordinate conversion and nearby collision | Blocks, skaters and creatures agree about where surfaces are. |
| Entity lifecycle and damage | A gun, spell or explosion can affect objects originating in another module. |
| Mesh/material/animation presentation | Draw guest objects with correct depth, scale and lighting. |
| Save/load and teardown | Switching maps or restarting removes guest state cleanly. |

Each adapter declares which capabilities it actually supports. Use one canonical unit/axis convention at the interface and convert at the boundary. A model import does not implement its source game's behavior.

For separate processes, start with one cube and a camera transform, then verify depth/occlusion, collision, a damage event, latency and clean shutdown. Bind any control endpoint to the local machine and authenticate commands. Do not expose a generic game-command server publicly.

The first native build does not need an IPC service. Its mission and block rules already live in a separate Rust crate so adapters can feed them verified events later.

## Better than a visual overlay

The reusable feature is an interaction: Minecraft cover stops MW2 bullets, a confirmed skating trick earns a reward, and a dragon attack affects the same damage system. Validate those interactions rather than accepting an aligned screenshot as proof.

Use bounded nearby-world updates and one host renderer where practical. A rendered two-game passthrough consumes two renderer slots under the Studio's global cap; it cannot silently grow to four simultaneous engines.

## Expansion order

1. Finish the four-game Terminal slice and its reusable interaction boundaries.
2. Evaluate libsm64 as an additional movement module; its explicit embedding interface and Mac build route make it a concrete candidate.
3. Test one CrossOver host/loader/compositor combination in isolation before porting a whole mashup.
4. Add further game packs only after their adapter, local asset importer and release terms are verified.

Elden Ring is a future compatibility/asset-integration candidate, not a currently supported host. No Elden Ring game files or code were imported.
