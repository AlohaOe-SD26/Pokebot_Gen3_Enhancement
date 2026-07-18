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

- [ ] #7 — Sandbox enhancement round (user-directed 2026-07-18, in
      progress): `sandbox-pokebot/` (copy of custom, isolated) + its own
      `install_sandbox.py`; implementing: profile/save/savestate BACKUP
      system with local + cloud (GitHub/synced-folder) storage and restore,
      GUI upgrades (backup panel, party sprites, shiny log), macro
      record/replay system, multi-map Patrol. User reviews on return; only
      approved items get promoted into custom-pokebot.

## Later / icebox
- [ ] #6 — Additional custom features (collect ideas here as they come up).

## Done
- [x] #1 — Vendor upstream 40Cakes/pokebot-gen3 into this repo via git
      subtree at upstream commit 5dd898f8 (done 2026-07-17).
- [x] #2 — Deep documentation pass over the vendored codebase:
      `PROJECT KNOWLEDGE/CODEBASE/00–05` + `Pokemon_Emerald_AI_Notes.md`
      (done 2026-07-17).
- [x] #4 — Easy setup/install/update script: `install.py` V2 (robust
      7-step setup/update/heal + ROM handling + install.log; user-confirmed
      "worked!" 2026-07-18) (done 2026-07-18).
- [x] #5 — Total custom interface: native dashboard GUI (program's own
      window, `--classic-gui` fallback) + ROG Ally X handheld mode +
      opt-in browser dashboard; user-confirmed hands-on "worked!"
      (done 2026-07-18). v2 ideas continue under #7.
