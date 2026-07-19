# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N — description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).
> Full future-idea catalog: `09-FEATURE-BRAINSTORM.md`.

## Now (active focus)
- [ ] #V — Post-promotion verification sweep: independent adversarial pass
      on the promoted features that only had builder self-verification (not
      an independent pass) — #8 global pathfinding, #12 shiny alerts, #18
      update notice, #20 cloud-sync, and the 2026-07-19 GUI polish (tabs /
      full-dex picker / XP bars / topmost dialogs). Interrupted twice by
      credit limits; run it against custom-pokebot before relying on the
      save-touching bits (cloud-sync ships off-by-default, so inert).

## Next (first wave — agreed direction 2026-07-19)
- [ ] #22 — ★ Watchdog / auto-recovery: detect "stuck" (no encounters N min,
      softlock, crash) → reload savestate / restart / safe-state + alert.
      Biggest 24/7 reliability win. (M)
- [ ] #9 — Hunt planner: pick a target species → GUI suggests best map/mode/
      method from the bot's encounter tables, one click to start. Leverages
      the now-built #8 global pathfinding. (M)
- [ ] #23 — Living-Dex / hunt-queue orchestrator: target list → auto-pick
      mode+location per species and move between hunts autonomously (uses
      #9 + #8). The "ultimate idle" payoff. (L)
- [ ] #25 — Pokémon detail + PC box viewer: click a party/box mon → full
      stats (IVs/nature/ability/moves); browse PC boxes with sprites. (M)
- [ ] #11 — Analytics suite: stats browser (sortable per-species table) +
      encounter-rate trend sparkline + phase history + a "luck meter"
      (actual vs binomial-expected shiny odds). (M)
- [ ] #27 — Battery-aware mode (ROG Ally): throttle speed/fps on low
      battery, pause on critical, resume on charge. (S-M)
- [ ] #28 — Polished mobile remote: phone-optimized web dashboard view to
      monitor 24/7 hunts (builds on the existing HTTP API). (M)

## Later / icebox (catalog in 09-FEATURE-BRAINSTORM.md; user re-orders/culls)
- [ ] #24 — Story auto-player (trainer/gym battler) — most ambitious, most
      transformative: progress the game to bootstrap a save to any hunt. (L)
- [ ] #26 — Theme system (selectable color themes; palette is centralized). (S-M)
- [ ] #29 — Box manager / auto-release by IV/nature/shiny filter (prevents
      full-box stalls in long hunts). (M)
- [ ] #13 — Macro composer v2: chain macros + repeat counts + conditions. (M-L)
- [ ] #14 — Profile manager UI (create/duplicate/rename/delete). (S-M)
- [ ] #15 — Config editor GUI (catch_block/battle/cheats + CCF builder). (M)
- [ ] #16 — PKHeX quick-export (.pk3 of any party/box mon). (S)
- [ ] #17 — Multi-instance manager (several profiles, aggregating board). (L)
- [ ] #19 — Stream overlay theme refresh (OBS overlay → dashboard style). (S-M)
- [ ] #6 — Idea backlog: everything else in 09-FEATURE-BRAINSTORM.md
      (egg-hatch optimizer, catch profiles, Nuzlocke, goals panel, log
      viewer, setup wizard, keybinding editor, shiny gallery, hunt-summary
      cards, cross-session history, stream chat, webhooks, crash-safe
      savestate ring, health monitor, scheduled hunts, gamepad-driven GUI,
      RNG manip, cheat presets, plugin loader UI).

## Promoted to custom 2026-07-19 (built; awaiting user in-game confirmation)
- [~] #3 — Custom automations + Patrol (v3 multi-map/global-nav). Awaiting
      user's in-game play-test.
- [~] #7 — Sandbox enhancement round (backup/restore + cloud, macros,
      multi-map Patrol, GUI pack) — built, adversarially verified (16-bug
      round), promoted.
- [~] #8 — Warp-aware global pathfinding — promoted; user cross-warp walk pending.
- [~] #10 — Gamepad + handheld menu-hide — promoted; user real-pad test pending.
- [~] #12 — Shiny alerts — promoted; user sees a live shiny fire it pending.
- [~] #18 — Auto-update notice — promoted; observe on a stale checkout pending.
- [~] #20 — Cloud save-sync v2 (off by default) — promoted; desktop↔Ally run pending.
- [~] #21 — Game cheat menu (+ tabbed GUI, full-dex sprite picker, XP bars,
      topmost dialogs) — promoted; user in-game effect test pending.

## Done
- [x] #1 — Vendor upstream 40Cakes/pokebot-gen3 (subtree @ 5dd898f8) (2026-07-17).
- [x] #2 — Deep documentation pass + Pokemon_Emerald_AI_Notes.md (2026-07-17).
- [x] #4 — install.py V2 (setup/update/heal + ROM handling) — "worked!" (2026-07-18).
- [x] #5 — Native dashboard GUI + handheld mode — "worked!" (2026-07-18).
