# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N — description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).

## Now (active focus)
- (queue up next: #3)

## Next
- [ ] #3 — Custom automations/bots: design doc + first custom bot mode
      (build on the BotMode/plugin extension points mapped in #2).
- [ ] #4 — Easy setup/install/update script (reference:
      `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md`; must reconcile the
      installer-as-codebase pattern with this repo being git-based —
      decision to record in 06-DECISIONS-LOG when designed).

## Later / icebox
- [ ] #5 — Total custom interface (evaluate: extend the bot's HTTP API +
      build a new frontend vs. replace the Tkinter GUI).
- [ ] #6 — Additional custom features (collect ideas here as they come up).

## Done
- [x] #1 — Vendor upstream 40Cakes/pokebot-gen3 into this repo via git
      subtree at upstream commit 5dd898f8 (done 2026-07-17).
- [x] #2 — Deep documentation pass over the vendored codebase:
      `PROJECT KNOWLEDGE/CODEBASE/00–05` + `Pokemon_Emerald_AI_Notes.md`
      (done 2026-07-17).
