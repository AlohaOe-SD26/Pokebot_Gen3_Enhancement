# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N — description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).

## Now (active focus)
- [ ] #3 — WIP (user confirmation 2026-07-18): custom-automations framework
      + "Patrol (Custom)" built and verified through real-import discovery;
      user has NOT yet play-tested Patrol in-game. Remaining: user runs
      Patrol on a grassy map with a patrol.yml and confirms behavior.

## Next

- [ ] #5 — Total custom interface: NATIVE dashboard GUI built per user
      direction (the program's own window; `--classic-gui` = stock) with
      resizable layout + ROG Ally X handheld mode (fullscreen, Pokéball
      drawer, F11/H/Esc). Machine-verified on a live ROM run; user approved
      from screenshots. **FLAGGED TO REVIEW: awaiting the user's hands-on
      visual test** (esp. on the Ally + with a progressed save for
      party/KPI panels). Browser dashboard demoted to opt-in remote
      viewing. Later v2: trend charts, shiny log browser, API additions.

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
