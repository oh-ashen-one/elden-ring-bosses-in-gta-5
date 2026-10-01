# Modern Warfare 2 AI

Read README.md, gta/README.md, docs/CROSSOVER-BACKLOG.md and HANDOFF.md before continuing. Terminal documents describe an older, preserved prototype.

- The vendored runtime builds on Apple Silicon; a setup app and tested rule modules exist. Retail gameplay and the combined mission are not verified. Read HANDOFF.md before claiming more.
- On 2026-10-01 the owner prioritized GTA V × Elden Ring: bosses damaged by GTA firearms and helicopter weapons. Read docs/CROSSOVER-BACKLOG.md. Earlier Terminal work is preserved in the backlog.
- Work on a task branch. Push it in the same session. Merging or pushing main needs explicit owner authorization.
- Inspect concurrent changes and process ownership before editing or launching anything.
- Review component licenses and preserve upstream provenance before importing code. UPSTREAMS.json records observations, not blanket reuse permission.
- Never commit proprietary game data, converted retail assets, credentials or local authentication stores.
- Keep original game installations read-only.
- All engine/GPU work runs on a verified Studio using the shared renderer-slot protocol; own only the instance started for this task.
- After the 2026-10-01 computer crash, GTA requires exclusive GPU use, with no other renderer. This Studio's active shared lock lives at `/Users/midir/sm2-n1/_scratch/gpu`, not `~/.cache/gpu-slot`. Use `gta/tools/launch_owner.py`; never use the old local `owner_launch.py` helper. Verify the actual protocol location live. Keep GTA at 1920×1080 windowed with VSync for now. An emergency PAUSED marker blocks launch; an explicit coordinator reservation for Hari's GTA test is supported without lifting that pause or touching other processes.
- Hari owns gameplay and subjective/performance testing. Standing instruction (2026-10-01): after installing a GTA patch, open GTA V Legacy for him without another permission request. Verify host, desktop, process ownership and the shared renderer cap first. Never interrupt unsaved gameplay to install; never automate tutorial/combat input or relaunch repeatedly after a crash. Elden Ring launches still require a separate request.
- Verify actual runtime behavior and performance. Compilation or a screenshot does not establish gameplay acceptance.
- Maintain one rolling HANDOFF.md with verified state, next steps, blockers and remote branch.
