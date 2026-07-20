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

## Next (user-set order 2026-07-19: #30 → #31 → #32, THEN the first wave below)
> #30/#31/#32 are BUILT + ADVERSARIALLY VERIFIED in sandbox (clean pass:
> money cheat byte-safe 56/56, GUI nav 28/28, no code bugs). AWAITING USER
> OK to promote to custom. In-game confirms still pending (filled-slot
> composites, hover with real stats, money effect, controller feel on Ally).
- [ ] #30 — Handheld & GUI refinements (user-specified 2026-07-19):
      (a) Persistent "Handheld Mode" button — move it out of the Play/
      Controls tab into an always-visible header (in the drawer: right of
      the "TOOLS" text; desktop: a header row above the tabs) so it shows on
      every tab.
      (b) Handheld menu relocation — in handheld mode the Tk top menu
      (Emulator/Profile/View/Help) must NOT appear at all (even with the
      drawer open; reverses the earlier "menu shows with drawer" behavior
      for handheld). Surface those commands as buttons/sections inside the
      PLAY tab instead. Desktop keeps the normal menu bar.
      (c) Left Party Section — a vertical party strip to the LEFT of the
      emulator video, in BOTH desktop and handheld: 6 slots, 1 mon/row.
      Empty slot = Poké Ball sprite; filled slot = the mon's sprite
      composited over its caught-ball sprite (ball BEHIND, from
      `pokemon.poke_ball`; ball art at sprites/items/<Ball>.png).
      (d) Hover stats — hovering (mouse) over a Left Party slot shows ALL
      that mon's stats (level/IVs/nature/ability/moves/…) in a tooltip;
      SAME hover-stats on the Party tab rows; must also be reachable via the
      gamepad-GUI navigation (#32).
- [ ] #31 — Adjustable money cheat: in the CHEATS card, a money entry
      pre-filled with the character's CURRENT money (read live), editable to
      any value, + a "Lock" toggle that freezes money at the typed value
      (on = keep re-applying that exact value; off = stop). Refines the
      existing Max/Infinite money.
- [ ] #32 — ★ Gamepad-driven GUI navigation (roadmap F2, PRIORITIZED by
      user to come right after #30/#31): drive the dashboard with the ROG/
      Xbox controller (D-pad/stick move focus across tabs/cards/buttons/
      party, A activates, incl. triggering the party hover-stats). Distinct
      from the existing in-GAME gamepad input (Manual mode).

## Adjustments (user-requested 2026-07-19)
- [x] #36 — Left Party balls enlarged 52→104px (ball visible behind mon)
      (ce66eb78).
- [x] #37 — Party hover tooltip restyled Pokémon-themed (type badges, IV
      grid, moves, sprite) (ce66eb78).
- [x] #38 — Gamepad GUI-nav gated to drawer-open only (no more gameplay
      interruption) (ce66eb78).
- [x] #39 — Auto-DECLINE new move learning (default `new_move: cancel`;
      seam for future move-intelligence at
      DefaultBattleStrategy.which_move_should_be_replaced) (25fac025).
      User's placed battle.yml also set to cancel.
- [x] #40 — Catch-ball allowlist (d5573234): "CATCH BALLS" card (checkbox+
      icon per ball) filters catch.py::_get_best_poke_ball; catch_balls.yml
      global+per-profile; default protects Master Ball. Live-verified on the
      real save. (Live catch in a real battle still pending.)
- [~] #36b — Party balls enlarged further to 140px (~2.7×); reads clearly
      behind smaller mons, big sprites (Celebi/Sceptile) still partly cover.
      Capped by column height — could go scrollable for a true 5× if the
      user wants. (d5573234)
- [x] #S — User's real save placed: "Nick - Emerald" (progressed) +
      "-restored" + global configs into custom/sandbox profiles/
      (gitignored). LIVE TEST on real party running.

## User rulings + new round (2026-07-19)
- [ ] RULINGS: Latias/Latios → make BOTH obtainable (bot detects which the
      save has, does either). Surskit → stays unobtainable (confirmed).
- [ ] #46 — Hover tooltip: make the caught-ball icon ~3× larger.
- [ ] #47 — Opportunistic catching: also catch an already-OWNED species if
      it is SHINY (currently catches uncaught wanted species; ensure shiny-
      of-owned is also caught).
- [ ] PROMOTE-2: promote the whole sandbox batch (since f0b275f3) into
      custom with EXTENSIVE intent-level documentation; then BACKUP
      everything (git tag milestone + note).
- [ ] #24 — STORY-MODE BOT (design-first, multi-pass/triple-check): play
      from a fresh save (user-set name; Oak intro/gender/name; Littleroot
      start) OR continue existing; goal = beat Elite 4 + complete the game
      (eventually pokedex); CHUNKED into chapters; must build+maintain a
      team; enumerate EVERY key event/interaction/item/requirement to
      progress + how to obtain progression items. Design → 12-STORYMODE-
      DESIGN.md, several verification passes before building.

## Living-Dex deepening (user-requested 2026-07-19; DESIGN-FIRST, no cutting corners)
- [ ] #41 — Obtainability model: classify every species — wild / evolution
      (method+from) / in-game trade / gift / static / roamer / event — so the
      Living Dex knows trade-evolutions and evolve-only / trade-only mons
      (must obtain pre-evo + evolve, or manual trade), not just "no wild →
      skip". (design: 11-LIVINGDEX-DESIGN.md)
- [ ] #42 — Reachability/requirement gating: hunt + living-dex must skip a
      target when the area/encounter needs a capability the player lacks
      (Surf/Cut/Rock Smash/Dive/Waterfall HMs, the right fishing rod, badges
      for HM use, story-flag area access). Read owned HMs/rods/badges/flags
      from the save.
- [x] #43 — Living Dex OPPORTUNISTIC catching: catch ANY wanted-uncaught
      species en route (target only drives travel); live-dex-driven
      advancement; 22/22 units (a8840769).
- [x] #44 — Party ball rework: strip now clean mon sprites (no ball
      backdrop); caught ball moved to the hover tooltip as an icon+name row.
      Live-verified on the real save (9c2b1f94).
- [x] #41-evo/#42-easy — obtainability (evolution) + capability gating
      built (ceb7343e; 30/30 units; live save read Old/Good/Super Rod;
      panel shows 128 wild/147 evolve/102 special-trade). obtainability.py
      + capabilities.py.
- [x] #41-research — compiled + fact-checked Emerald obtainability lists
      (gift 7/static 8/roamer 1/event 6/breeding 3/special 1/unobtainable 79;
      in-game trades rescue nothing). Census sums to 386; "show both"
      denominators exposed (217/386 obtainable without trading). 16/16 units.
      modules/data/emerald_obtainability.json + obtainability.py. Fact-check
      report + citations: 11-LIVINGDEX-DESIGN.md (Phase #41-research). REMAINING
      for full #41: wire living_dex_mode target selection to plan_for's gate +
      route gift/static/roamer to reset modes; auto-evolve helper.
- [ ] #42-hard — HM-gated cross-map reachability in the nav graph (v2).
- [ ] #45 — (FUTURE, with story-mode bot #24) enumerate story instances the
      bot can automate, and let hunt/living-dex progress the story to unlock
      areas/capabilities needed for dex completion.

## Now-ish (user-added 2026-07-19, ahead of first wave)
- [ ] #33 — GUI fixes (in sandbox): Left Party Section ALWAYS visible in
      both modes regardless of drawer state; unified open/close — Pokéball
      opens the side tool menu + a Close/Hide collapses it in BOTH handheld
      AND desktop (desktop can hide tools to see more emulator).
- [ ] #34 — Living POKÉDEX tab: search all Emerald species; caught mark +
      shinies-caught count (from stats.db) + full dex info (types/abilities/
      base stats/dex#/category/flavor) + learnable moves (level-up/TM/HM/
      tutor/egg) — offline Bulbapedia. Needs battle sprite + dex artwork.
      RESEARCH-FIRST (see 10-DEX-RESEARCH.md): inventory bot data → gap-fill
      → fact-check → THEN build.
- [ ] #35 — ITEM-DEX tab: search all items; total-collected-historically +
      currently-held counters + item info + map locations + used/held/
      dropped-by Pokémon. Needs item sprite + inventory image. Same
      research-first flow as #34 (10-DEX-RESEARCH.md).

## First wave (after #30-#32 + #33-#35 — agreed direction 2026-07-19)
- [ ] #22 — ★ Watchdog / auto-recovery: BUILT IN SANDBOX 2026-07-19
      (c7d25305; encounter-stall + drop-to-Manual + frame-freeze detection,
      bounded recovery ladder [re-assert → savestate-reload w/ safety backup
      → give up to Manual], overworld-gated, alerts, GUI status line; 17/17
      self-tests + recovery-path safety confirmed). Remaining: live-hunt
      softlock recovery needs a progressed save; independent adversarial
      pass to bundle with the batch verification before promotion.
- [ ] #9 — Hunt planner: v1 + v2 BUILT IN SANDBOX 2026-07-19 (6141d96f,
      4df17747). Encounter index from ROM (132 species/805 locations,
      19/19 fact-check); Hunt tab shows ranked locations + mode; v2 adds an
      encounter-tile finder + "Hunt (Custom)" mode = one-click travel (via
      global nav) + hunt. KI-6 tab overcrowding FIXED (two-row tab bar).
      REMAINING: live navigate+hunt on a progressed save; Rock Smash has no
      auto-tile finder (degrades to manual). Independent adversarial pass at
      promotion time.
- [ ] #23 — Living-Dex orchestrator: v1 BUILT IN SANDBOX 2026-07-19
      (34c5f461; living_dex.py target derivation + "Living Dex (Custom)"
      mode: travel→hunt→catch-first-uncaught→advance; catch-intent verified;
      16/16 units + real-ROM fact-check 132 targets). REMAINING: live
      autonomous run needs a progressed save; screenshot harness needs a fix
      after #33 layout change; independent adversarial pass at promotion.
- [ ] #25 — Pokémon detail + PC box viewer: click a party/box mon → full
      stats (IVs/nature/ability/moves); browse PC boxes with sprites. (M)
- [ ] #11 — Analytics suite: v1 BUILT IN SANDBOX 2026-07-19 (8094bb05;
      analytics.py + ANALYTICS card in Stats tab: encounter-rate sparkline,
      luck meter [actual vs binomial 1/8192, σ/z/verdict], sortable+
      filterable stats browser w/ sprites; 26/26 units). REMAINING:
      meaningful values need a populated stats.db (real hunt); independent
      pass at promotion.
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
