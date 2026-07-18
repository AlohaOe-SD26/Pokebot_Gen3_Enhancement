# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N — description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).

## Now (active focus)
- [ ] #3 — Custom automations/bots: framework + first custom mode BUILT
      (custom_modes drop-in loader + "Patrol (Custom)" waypoint-loop mode,
      structurally smoke-tested 2026-07-17). REMAINING: live verification on
      a machine with Python 3.11+, deps, a ROM and a profile — then mark
      done.

## Next

- [ ] #5 — Total custom interface: v1 web dashboard BUILT (served at
      /static/custom-ui/ via the bot's HTTP API; mock-tested + screenshot-
      verified 2026-07-17). REMAINING: live verification with ROM +
      http.yml enabled; then v2 (API additions: savestates/screenshot/
      pause endpoints, auth, trend charts, shiny log browser).

## Later / icebox
- [ ] #6 — Additional custom features (collect ideas here as they come up).

## Done
- [x] #1 — Vendor upstream 40Cakes/pokebot-gen3 into this repo via git
      subtree at upstream commit 5dd898f8 (done 2026-07-17).
- [x] #2 — Deep documentation pass over the vendored codebase:
      `PROJECT KNOWLEDGE/CODEBASE/00–05` + `Pokemon_Emerald_AI_Notes.md`
      (done 2026-07-17).
- [x] #4 — Easy setup/install/update script: `install.py` (git-driven
      install/update/heal, tested incl. fresh-clone + heal + deps on this
      machine; design in 06-DECISIONS-LOG) (done 2026-07-17).
