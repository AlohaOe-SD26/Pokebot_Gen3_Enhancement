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

## Later / icebox (future development — agent-recommended 2026-07-18,
## ordered by my suggested priority; user re-orders/culls at will)
- [ ] #21 — Game cheat menu: BUILT IN SANDBOX + adversarially verified
      2026-07-18 (game_cheats.py + CHEATS card; actions: heal/max-level/
      perfect-IVs/max-friendship/max-money/item-pack/max-balls/rare-candy;
      toggles: infinite money, auto-heal, force-wild-species, guaranteed-
      shiny-wild. 32+15+77 checks green; nickname-preservation bug fixed).
      Remaining: user's in-game effect test on a real save; then promote.
- [ ] #8 — Warp-aware global pathfinding: BUILT IN SANDBOX 2026-07-18
      (warp_graph.py + navigate_to_anywhere + Patrol v3; 23/23 checks vs
      the real ROM — full Emerald graph extracted: 518 maps, 1268 warp
      edges). Remaining: user's real-save cross-warp walk, then promote.
      Unlocks #9 hunt planner; noted for the Emerald AI project.
- [ ] #9 — Hunt planner: pick a target species → GUI suggests best
      map/mode/method from the bot's own encounter tables, one click to
      configure + start the hunt. Pairs with #8. (M)
- [ ] #10 — Gamepad/controller support: BUILT IN SANDBOX 2026-07-18
      (XInput → Manual-mode inputs, Back+Start toggles the drawer; 19/19
      stubbed-pad unit tests). Remaining: user's real-pad test on the
      Ally, then promote.
- [ ] #11 — Analytics suite: stats browser window (sortable per-species
      table from stats.db) + encounter-rate trend sparkline in the GUI +
      per-phase history view. (M)
- [ ] #12 — Shiny alerts: BUILT IN SANDBOX 2026-07-18 (toast + async
      ding + optional auto-pause via alerts.yml; 21-check battery + real
      toast fired). Remaining: user sees a real in-game shiny fire it,
      then promote.
- [ ] #13 — Macro composer v2: chain macros + repeat counts + simple
      conditions (e.g. "until party full", "until item count"), building
      toward a no-code automation builder on the mode framework. (M-L)
- [ ] #14 — Profile manager UI: create/duplicate/rename/delete profiles
      + per-profile quick settings from the dashboard. (S-M)
- [ ] #15 — Config editor GUI: form-based editing of catch_block/battle/
      cheats YAML + a guided customcatchfilters builder. (M)
- [ ] #16 — PKHeX quick-export: one-click .pk3 of any party/box mon from
      the GUI (upstream already writes pk3s on shinies). (S)
- [ ] #17 — Multi-instance manager: run several profiles at once with an
      aggregating dashboard (multi-process; big but very "idle-game"). (L)
- [ ] #18 — Auto-update notice: BUILT IN SANDBOX 2026-07-18 (non-blocking
      launch check; Status-card line + event-log entry; live-verified via
      forced-behind run). Remaining: user observes it on a genuinely
      stale checkout, then promote.
- [ ] #19 — Stream overlay theme refresh: restyle the OBS overlay to the
      dashboard's design language. (S-M)
- [ ] #20 — Cloud save-sync v2: BUILT IN SANDBOX 2026-07-18 (exit-push +
      safe pre-emulator launch-apply + conflict protection with
      import-as-new-profile; 23/23 two-machine battery over a real git
      remote; two data-safety bugs caught and fixed pre-commit).
      Remaining: user's real desktop↔Ally run, then promote.
- [ ] #6 — Additional custom features (collect new ideas here).

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
