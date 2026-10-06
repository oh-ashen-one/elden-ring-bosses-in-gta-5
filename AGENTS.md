# Elden Ring Bosses in GTA 5

Read README.md, gta/README.md, docs/CROSSOVER-BACKLOG.md and HANDOFF.md before continuing. The public repository is `oh-ashen-one/elden-ring-bosses-in-gta-5` (renamed from `modern-warfare-2-ai`). Terminal documents/runtime describe an older, preserved prototype; GTA is the active product.

- Active product: GTA V Story Mode with locally imported Elden Ring bosses. The vendored Terminal runtime is preserved legacy work. Read HANDOFF.md for exact verification scope.
- On 2026-10-01 the owner prioritized GTA V × Elden Ring: bosses damaged by GTA firearms and helicopter weapons. Read docs/CROSSOVER-BACKLOG.md. Earlier Terminal work is preserved in the backlog.
- Work on a task branch. Push it in the same session. Merging or pushing main needs explicit owner authorization.
- Inspect concurrent changes and process ownership before editing or launching anything.
- Review component licenses and preserve upstream provenance before importing code. UPSTREAMS.json records observations, not blanket reuse permission.
- Never commit proprietary game data, converted retail assets, credentials or local authentication stores.
- Keep original game installations read-only.
- All engine/GPU work runs on a verified Studio using the shared renderer-slot protocol; own only the instance started for this task.
- After the 2026-10-01 computer crash, GTA requires exclusive GPU use, with no other renderer. This Studio's active shared lock lives at `/Users/midir/sm2-n1/_scratch/gpu`, not `~/.cache/gpu-slot`. Use `gta/tools/launch_owner.py`; never use the old local `owner_launch.py` helper. Verify the actual protocol location live. Keep GTA at 1920×1080 windowed with VSync for now. An emergency PAUSED marker blocks launch; an explicit coordinator reservation for Hari's GTA test is supported without lifting that pause or touching other processes.
- Latest authority (2026-10-06): Hari declared the project complete and explicitly authorized publishing all project code to the main public repository. This authorizes merging the pending task and making `main` the public default for this release. It does not authorize unrelated project changes. Keep GTA closed; the owner reserved gameplay testing. Do not infer new rendered evidence from publication approval.
- Verify actual runtime behavior and performance. Compilation or a screenshot does not establish gameplay acceptance.
- Maintain one rolling HANDOFF.md with verified state, next steps, blockers and remote branch.
