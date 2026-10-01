# Modern Warfare 2 AI

Read README.md, docs/TERMINAL-PLAN.md, docs/SOURCES.md and HANDOFF.md before continuing.

- This repository currently contains planning and provenance only. Do not claim there is a playable game or an imported engine.
- The owner selected MW2's Terminal airport map as the first shared playground.
- Work on a task branch. Push it in the same session. Merging or pushing main needs explicit owner authorization.
- Inspect concurrent changes and process ownership before editing or launching anything.
- Review component licenses and preserve upstream provenance before importing code. UPSTREAMS.json records observations, not blanket reuse permission.
- Never commit proprietary game data, converted retail assets, credentials or local authentication stores.
- Keep original game installations read-only.
- All engine/GPU work runs on a verified Studio using the shared renderer-slot protocol; own only the instance started for this task.
- Verify actual runtime behavior and performance. Compilation or a screenshot does not establish gameplay acceptance.
- Maintain one rolling HANDOFF.md with verified state, next steps, blockers and remote branch.
