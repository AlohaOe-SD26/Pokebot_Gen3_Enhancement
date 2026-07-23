# Punch List â€” Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N â€” description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).
> Full future-idea catalog: `09-FEATURE-BRAINSTORM.md`.

## Now (active focus)
- [ ] #V â€” Post-promotion verification sweep: independent adversarial pass
      on the promoted features that only had builder self-verification (not
      an independent pass) â€” #8 global pathfinding, #12 shiny alerts, #18
      update notice, #20 cloud-sync, and the 2026-07-19 GUI polish (tabs /
      full-dex picker / XP bars / topmost dialogs). Interrupted twice by
      credit limits; run it against custom-pokebot before relying on the
      save-touching bits (cloud-sync ships off-by-default, so inert).

## Next (user-set order 2026-07-19: #30 â†’ #31 â†’ #32, THEN the first wave below)
> #30/#31/#32 are BUILT + ADVERSARIALLY VERIFIED in sandbox (clean pass:
> money cheat byte-safe 56/56, GUI nav 28/28, no code bugs). AWAITING USER
> OK to promote to custom. In-game confirms still pending (filled-slot
> composites, hover with real stats, money effect, controller feel on Ally).
- [ ] #30 â€” Handheld & GUI refinements (user-specified 2026-07-19):
      (a) Persistent "Handheld Mode" button â€” move it out of the Play/
      Controls tab into an always-visible header (in the drawer: right of
      the "TOOLS" text; desktop: a header row above the tabs) so it shows on
      every tab.
      (b) Handheld menu relocation â€” in handheld mode the Tk top menu
      (Emulator/Profile/View/Help) must NOT appear at all (even with the
      drawer open; reverses the earlier "menu shows with drawer" behavior
      for handheld). Surface those commands as buttons/sections inside the
      PLAY tab instead. Desktop keeps the normal menu bar.
      (c) Left Party Section â€” a vertical party strip to the LEFT of the
      emulator video, in BOTH desktop and handheld: 6 slots, 1 mon/row.
      Empty slot = PokÃ© Ball sprite; filled slot = the mon's sprite
      composited over its caught-ball sprite (ball BEHIND, from
      `pokemon.poke_ball`; ball art at sprites/items/<Ball>.png).
      (d) Hover stats â€” hovering (mouse) over a Left Party slot shows ALL
      that mon's stats (level/IVs/nature/ability/moves/â€¦) in a tooltip;
      SAME hover-stats on the Party tab rows; must also be reachable via the
      gamepad-GUI navigation (#32).
- [ ] #31 â€” Adjustable money cheat: in the CHEATS card, a money entry
      pre-filled with the character's CURRENT money (read live), editable to
      any value, + a "Lock" toggle that freezes money at the typed value
      (on = keep re-applying that exact value; off = stop). Refines the
      existing Max/Infinite money.
- [ ] #32 â€” â˜… Gamepad-driven GUI navigation (roadmap F2, PRIORITIZED by
      user to come right after #30/#31): drive the dashboard with the ROG/
      Xbox controller (D-pad/stick move focus across tabs/cards/buttons/
      party, A activates, incl. triggering the party hover-stats). Distinct
      from the existing in-GAME gamepad input (Manual mode).

## Adjustments (user-requested 2026-07-19)
- [x] #36 â€” Left Party balls enlarged 52â†’104px (ball visible behind mon)
      (ce66eb78).
- [x] #37 â€” Party hover tooltip restyled PokÃ©mon-themed (type badges, IV
      grid, moves, sprite) (ce66eb78).
- [x] #38 â€” Gamepad GUI-nav gated to drawer-open only (no more gameplay
      interruption) (ce66eb78).
- [x] #39 â€” Auto-DECLINE new move learning (default `new_move: cancel`;
      seam for future move-intelligence at
      DefaultBattleStrategy.which_move_should_be_replaced) (25fac025).
      User's placed battle.yml also set to cancel.
- [x] #40 â€” Catch-ball allowlist (d5573234): "CATCH BALLS" card (checkbox+
      icon per ball) filters catch.py::_get_best_poke_ball; catch_balls.yml
      global+per-profile; default protects Master Ball. Live-verified on the
      real save. (Live catch in a real battle still pending.)
- [~] #36b â€” Party balls enlarged further to 140px (~2.7Ã—); reads clearly
      behind smaller mons, big sprites (Celebi/Sceptile) still partly cover.
      Capped by column height â€” could go scrollable for a true 5Ã— if the
      user wants. (d5573234)
- [x] #S â€” User's real save placed: "Nick - Emerald" (progressed) +
      "-restored" + global configs into custom/sandbox profiles/
      (gitignored). LIVE TEST on real party running.

## User rulings + new round (2026-07-19)
- [x] RULINGS: Latias+Latios BOTH obtainable (218/386); Surskit unobtainable
      (c2707bad).
- [x] #46 â€” Hover tooltip ball ~3Ã— (fixed thumbnail no-op bug) (c2707bad).
- [x] #47 â€” Opportunistic catch: any SHINY (even owned) caught (c2707bad).
- [x] PROMOTE-2 â€” whole batch promoted to custom w/ extensive intent docs
      (DIVERGENCE-LOG aâ€“i + DOCUMENTATION/05-hunting-and-livingdex.md);
      live-verified on the real save; 29b9aae5.
- [ ] #24 â€” STORY-MODE BOT (design-first, multi-pass/triple-check): play
      from a fresh save (user-set name; Oak intro/gender/name; Littleroot
      start) OR continue existing; goal = beat Elite 4 + complete the game
      (eventually pokedex); CHUNKED into chapters; must build+maintain a
      team; enumerate EVERY key event/interaction/item/requirement to
      progress + how to obtain progression items. Design â†’ 12-STORYMODE-
      DESIGN.md, several verification passes before building.
      - PROGRESS (2026-07-20): a fresh game auto-plays through **GYM 1 (Stone
        Badge)** â€” introâ†’starterâ†’first battleâ†’PokÃ©dexâ†’trainâ†’rivalâ†’Petalburgâ†’
        Dad/Wallyâ†’Route104â†’Petalburg Woods (Aqua scene)â†’Rustboroâ†’Roxanne.
        Legs 1-2 promoted to custom; legs 3-4 + Gym 1 in sandbox (awaiting
        testâ†’promote). Fixed the Woods-door stall (ML-9) in BOTH builds. NEXT:
        Chapter 4 (deliver Devon Goods â†’ Rusturf Tunnel â†’ Dewford / Gym 2).
        Low-pri OPEN: chapters.py Ch2 completion-flag bug.
- [~] #24-move â€” SMART MOVE-LEARNING (user 2026-07-20): DONE â€” Story strategy
      `which_move_should_be_replaced` override keeps every PokÃ©mon combat-capable
      (never trades a damaging move for a status move), preserves type coverage,
      and skips no-gain moves; overrides the stock `new_move: cancel` decline.
      In both builds, unit-verified. REMAINING (folds into #24-team): status-move
      UTILITY ranking (value Sleep Powder/heal over Growl) rather than treating
      all status moves as equal.
- [~] #24-resume â€” RESUME-FROM-ANYWHERE (user 2026-07-20): v1 DONE â€” segmented
      flag-gated run() resumes from a fresh game / resumed save / hand-played
      state, skipping finished segments (fixed the "thinks I need Wally"
      mis-detection via the HIDE_PETALBURG_CITY_WALLYS_MOM flag). REMAINING:
      finer per-STEP resume with each step self-locating from any tile; FAST
      travel (Fly/Teleport/Escape Rope when available, gated by HMs/badges/items
      per #42); title-screen-with-save auto-Continue; reliable completion flags
      for chapters past Gym 1. Design Â§RS.
- [ ] #24-autosave â€” AUTO CHAPTER SAVE-STATE (sandbox testing aid; user
      2026-07-20). After each scripted chapter/segment completes in StoryMode
      (SANDBOX ONLY), auto-save a save state named by chapter into `states/` so
      chapters can be tested/resumed fast. TOGGLE in the Play tab, DEFAULT ON,
      safely toggleable on/off even while the bot runs (the story generator reads
      the flag at SEGMENT BOUNDARIES, so flipping it never interrupts). Implement
      by hooking the segment boundaries already in `StoryMode.run()` (Â§RS).
      **APPLY ONLY AFTER the user green-lights the current story build** (it
      touches run()); until then this is a note. Save quickly at a boundary
      (get_save_state + write) â€” negligible one-frame pause.
- [x] #24-loadpage â€” LOAD-STATE POPUP PAGINATION (user 2026-07-20): DONE both
      builds. `load_state_window.py` now shows 5 states/page and lazily renders
      only the current page's thumbnails (Prev/Next + arrow/PageUp-Down + page
      label; nav auto-hidden for one page). Fixes the slow-open with a full
      `states/` folder (was decoding up to 128 PNGs at once).
- [ ] #24-defeat â€” DEFEAT RESPONSE (user 2026-07-20; design Â§DR). What the bot
      does when it LOSES a battle, as a settings-popup choice:
      (A) "Reload save state" = today's watchdog behaviour, made a toggle; verify
      the resume-after-reload rough edges (the segmented resume Â§RS already fixes
      most â€” the old run() stranded the bot on any restart; also ensure watchdog
      snapshots are CLEAN OVERWORLD states, never mid-battle/scene).
      (B) "Play through & retry" = ride out the whiteout â†’ respawn (PokÃ© Center /
      early houses) â†’ recalc position + story segment (Â§RS) â†’ MATCHUP ASSESS (avg
      enemy vs own level, team size, type/move coverage) â†’ train/adjust team
      (#24-team) if outmatched â†’ escalate on repeated loss â†’ retry. Mode B = Â§RS +
      matchup gate + #24-team, one engine. Sub-parts: a small matchup scorer;
      whiteout ride-out; failure/attempt tracking per objective.
- [~] #24-evo â€” EVOLUTION policy (user 2026-07-20): CURRENT (sandbox+custom) =
      ALLOW ALL evolutions (`should_allow_evolution â†’ True`, overriding the stock
      `stop_evolution`) â€” fixes the Lv16 evolve+move-learn hang and strengthens
      the team. POPUP options to add (#24-ui): **allow all (default on) / random
      evolution / no evolution**. Robustness the bot must have (verify): RECOGNIZE
      when an evolution happens, navigate the evolution CUTSCENE, and handle the
      accept/deny of a new move + deleting an old one to replace it (uses the
      stock evolveâ†’learn path + `which_move_should_be_replaced`). "Random" mode =
      per-PokÃ©mon coin-flip whether to evolve (organic team variety, ties #24-team).
- [ ] #24-team â€” ORGANIC TEAM-BUILDING / helper acquisition (user 2026-07-20;
      design in 12-STORYMODE-DESIGN Â§TB). Bot builds a team to beat gyms/trainers
      but decides to catch "helpers" ORGANICALLY: a rising "recruit urge" that
      grows with failed/struggled battles (increasing re-rolls/odds), weighted by
      real team gaps (type matchup vs the fight, team type-diversity, move
      coverage), pulling candidates from the obtainability+reachability data
      (#41/#42). Random/human-like, not a min-maxer. Needed for Torchic-vs-Roxanne
      and later type-hard gyms; implement when a gym requires it.
- [ ] #24-shops â€” MAP SHOPS AS REACHED (user 2026-07-21; planning doc Â§4). Each mart
      has its own layout AND stock/order; the buy code is already shop-agnostic
      (universal task-driven flow + `_mart_item_row` reads stock live). So map each
      shop's ENTRY facts (mart map, clerk-approach tile, facing) when first reached,
      verify live, add an Atlas row. SPECIAL: **Lilycove Department Store** is
      MULTI-FLOOR (per-floor shop + stock, elevator nav); the **Elite Four PokÃ©
      Center** has a shop + mart; Slateport stalls / TM sellers use non-standard
      menus. Do NOT map all shops up front (unreachable â†’ can't verify).
- [ ] #24-pc â€” PC / BOX TEAM MANAGEMENT (user 2026-07-21; planning doc Â§4b). Advanced
      team development via the PokÃ©mon Storage PC: store / move / withdraw PokÃ©mon
      (and items). Map PC access points (every PokÃ© Center + player's-house PC) and
      the PC UI (Deposit/Withdraw/Move, box navigation, partyâ†”box swaps, item
      storage). Enables swapping in a better-matched mon per gym and parking
      over-levelled/redundant catches. Build when a fight needs it; ties #24-team /
      Â§7 matchup awareness. PokÃ© Centers are otherwise near-identical (generic code
      handles them) â€” only map PC/layout exceptions (e.g. the E4 PokÃ© Center).
- [x] #24-resume â€” SEGMENT 1 RESUME BUG FIXED (2026-07-21). Pre-PokÃ©dex
      recovery/resume re-ran the scripted intro from the truck â†’ derail loop
      ("stuck after respawn"). Split Segment 1: scripted intro gated on
      `_has_starter()`; trainâ†’rivalâ†’PokÃ©dex resumable + flag-gated. Derail budget
      hardened (monotonic party `_progress_sig`; patient recovery). Verified in
      harness. Sandbox (early_game.py, story_mode.py). See CHANGELOG/MISTAKES 07-21.
- [x] #24-freeze â€” OLDALE PC FREEZE **FIXED** (user 2026-07-21). Root cause (from the
      user's real-bot debug log's generator call stack): heal returned while the
      overworld was transiently non-controllable â†’ healâ†’go-to-rival navigate choked â†’
      derail â†’ re-heal â†’ endless heal/leave/re-enter loop â†’ Manual. FIX:
      heal_in_pokemon_center waits for a STABLE controllable overworld after the exit
      warp. Downstream: StoryCatchStrategy flees instead of Manual when out of balls.
      Validated route103â†’Rustboroâ†’Route116 catching, 0 derails/Manual. Old note below
      kept for history.
      ~~POST-BATTLE TRANSITION FREEZE (the likely real "stuck at Oldale PC").~~ After a training battle (flee/level-up/move-learn, e.g.
      Mudkip Water Gun @L10) the return-to-overworld transition leaves the overworld
      non-controllable while the bot acts (navigate / walk to the Oldale nurse) â†’ can
      hard-freeze (nurse heal dialogue never starts). REAL (harness == real
      main_loop), timing/starter-sensitive (default starter "random"; Treecko passed,
      Mudkip hits it). Offline repro hampered by save-state reload artifacts. NEXT:
      user validates on real PC (force `starter: mudkip`, fresh game) and reports;
      then decide a deeper "settle before acting" fix (heal_in_pokemon_center nurse
      interaction + story navigations) vs a training-flow workaround.
- [x] #24-debuglog â€” DEBUG LOGGING TOGGLE (user 2026-07-21). Opt-in "Debug Logging"
      in the Run (bot-mode) menu (both GUIs), default off â†’ `modules/debug_logger.py`
      writes an extensive structured log to `<profile>/debug-logs/` (event stream +
      stuck dumps with the generator call stack). For diagnosing Bug #2 (#24-freeze)
      from a shared real-bot log. Built + validated in sandbox. See CHANGELOG 07-21.
- [x] #24-swaptrain â€” SWAP-TRAINING **DONE** (user 2026-07-21). Fixes the
      under-levelled-mon training loop: `SwapTrainBattleStrategy` switches a trainee
      that's â‰¥2 levels below the wild foe to the strongest team-mate turn 1 (shares
      XP, no fainting/heal-churn). Gated around `train_team`. Validated Poochyena
      L4â†’L7, 0 heals/faints. Commit ef812c0e.
- [ ] #24-trainmap â€” AREA-APPROPRIATE TRAINING (user 2026-07-21, Option 1). Groundwork
      landed: `modules/story/training_areas.py` maps early-game grass to wild level
      ranges + `best_training_grass(level)`. TODO: wire `train_team` to route an
      under-levelled mon to the best REACHABLE area for FULL XP (progressing upward as
      it levels), with swap-train (#24-swaptrain) as the anywhere fallback. Needs: fill
      the PENDING_GRASS spin tiles as maps are reached (Route 102/104/Woods), and
      cross-map routing to/from the training area. Efficiency layer â€” not blocking.
      ‼ LAVARIDGE HAS NO REACHABLE TRAINING GRASS (two-way sweep 2026-07-23,
      `tools/story-dev/jaggedgrass_probe.py`): Jagged Pass cannot be re-entered from
      the town (one-way ledges) and Route 112's lower grass has no return path. So
      Segment 11d (Flannery) preps with a Water lead + heal and NO grind; a L29-31
      team wins but is marginal (one whiteout in validation run 11). First concrete
      customer for this item.
- [ ] #24-ui â€” STORY-BOT PRE-RUN SETTINGS POPUP (user 2026-07-20). A popup/menu
      shown BEFORE the Story bot runs to set: player name; starter nickname mode
      (none / defined / random); starter choice (specific / random); + other
      settings TBD. Front-end for the existing `<profile>/story.yml`
      (character_name/gender/starter/starter_nickname already read by
      modules/story/config.py). WORK ON THIS ONLY AFTER the bot is finished and
      tested 100% (user directive). Popup also hosts the #24-autosave toggle
      (auto chapter save-state, default on) and the #24-defeat "Defeat response"
      section (Reload-save-state vs Play-through-and-retry + sub-toggles).

## Living-Dex deepening (user-requested 2026-07-19; DESIGN-FIRST, no cutting corners)
- [ ] #41 â€” Obtainability model: classify every species â€” wild / evolution
      (method+from) / in-game trade / gift / static / roamer / event â€” so the
      Living Dex knows trade-evolutions and evolve-only / trade-only mons
      (must obtain pre-evo + evolve, or manual trade), not just "no wild â†’
      skip". (design: 11-LIVINGDEX-DESIGN.md)
- [ ] #42 â€” Reachability/requirement gating: hunt + living-dex must skip a
      target when the area/encounter needs a capability the player lacks
      (Surf/Cut/Rock Smash/Dive/Waterfall HMs, the right fishing rod, badges
      for HM use, story-flag area access). Read owned HMs/rods/badges/flags
      from the save.
- [x] #43 â€” Living Dex OPPORTUNISTIC catching: catch ANY wanted-uncaught
      species en route (target only drives travel); live-dex-driven
      advancement; 22/22 units (a8840769).
- [x] #44 â€” Party ball rework: strip now clean mon sprites (no ball
      backdrop); caught ball moved to the hover tooltip as an icon+name row.
      Live-verified on the real save (9c2b1f94).
- [x] #41-evo/#42-easy â€” obtainability (evolution) + capability gating
      built (ceb7343e; 30/30 units; live save read Old/Good/Super Rod;
      panel shows 128 wild/147 evolve/102 special-trade). obtainability.py
      + capabilities.py.
- [x] #41-research â€” compiled + fact-checked Emerald obtainability lists
      (gift 7/static 8/roamer 1/event 6/breeding 3/special 1/unobtainable 79;
      in-game trades rescue nothing). Census sums to 386; "show both"
      denominators exposed (217/386 obtainable without trading). 16/16 units.
      modules/data/emerald_obtainability.json + obtainability.py. Fact-check
      report + citations: 11-LIVINGDEX-DESIGN.md (Phase #41-research). REMAINING
      for full #41: wire living_dex_mode target selection to plan_for's gate +
      route gift/static/roamer to reset modes; auto-evolve helper.
- [ ] #42-hard â€” HM-gated cross-map reachability in the nav graph (v2).
- [ ] #45 â€” (FUTURE, with story-mode bot #24) enumerate story instances the
      bot can automate, and let hunt/living-dex progress the story to unlock
      areas/capabilities needed for dex completion.

## Now-ish (user-added 2026-07-19, ahead of first wave)
- [ ] #33 â€” GUI fixes (in sandbox): Left Party Section ALWAYS visible in
      both modes regardless of drawer state; unified open/close â€” PokÃ©ball
      opens the side tool menu + a Close/Hide collapses it in BOTH handheld
      AND desktop (desktop can hide tools to see more emulator).
- [ ] #34 â€” Living POKÃ‰DEX tab: search all Emerald species; caught mark +
      shinies-caught count (from stats.db) + full dex info (types/abilities/
      base stats/dex#/category/flavor) + learnable moves (level-up/TM/HM/
      tutor/egg) â€” offline Bulbapedia. Needs battle sprite + dex artwork.
      RESEARCH-FIRST (see 10-DEX-RESEARCH.md): inventory bot data â†’ gap-fill
      â†’ fact-check â†’ THEN build.
- [ ] #35 â€” ITEM-DEX tab: search all items; total-collected-historically +
      currently-held counters + item info + map locations + used/held/
      dropped-by PokÃ©mon. Needs item sprite + inventory image. Same
      research-first flow as #34 (10-DEX-RESEARCH.md).

## First wave (after #30-#32 + #33-#35 â€” agreed direction 2026-07-19)
- [ ] #22 â€” â˜… Watchdog / auto-recovery: BUILT IN SANDBOX 2026-07-19
      (c7d25305; encounter-stall + drop-to-Manual + frame-freeze detection,
      bounded recovery ladder [re-assert â†’ savestate-reload w/ safety backup
      â†’ give up to Manual], overworld-gated, alerts, GUI status line; 17/17
      self-tests + recovery-path safety confirmed). Remaining: live-hunt
      softlock recovery needs a progressed save; independent adversarial
      pass to bundle with the batch verification before promotion.
- [ ] #9 â€” Hunt planner: v1 + v2 BUILT IN SANDBOX 2026-07-19 (6141d96f,
      4df17747). Encounter index from ROM (132 species/805 locations,
      19/19 fact-check); Hunt tab shows ranked locations + mode; v2 adds an
      encounter-tile finder + "Hunt (Custom)" mode = one-click travel (via
      global nav) + hunt. KI-6 tab overcrowding FIXED (two-row tab bar).
      REMAINING: live navigate+hunt on a progressed save; Rock Smash has no
      auto-tile finder (degrades to manual). Independent adversarial pass at
      promotion time.
- [ ] #23 â€” Living-Dex orchestrator: v1 BUILT IN SANDBOX 2026-07-19
      (34c5f461; living_dex.py target derivation + "Living Dex (Custom)"
      mode: travelâ†’huntâ†’catch-first-uncaughtâ†’advance; catch-intent verified;
      16/16 units + real-ROM fact-check 132 targets). REMAINING: live
      autonomous run needs a progressed save; screenshot harness needs a fix
      after #33 layout change; independent adversarial pass at promotion.
- [ ] #25 â€” PokÃ©mon detail + PC box viewer: click a party/box mon â†’ full
      stats (IVs/nature/ability/moves); browse PC boxes with sprites. (M)
- [ ] #11 â€” Analytics suite: v1 BUILT IN SANDBOX 2026-07-19 (8094bb05;
      analytics.py + ANALYTICS card in Stats tab: encounter-rate sparkline,
      luck meter [actual vs binomial 1/8192, Ïƒ/z/verdict], sortable+
      filterable stats browser w/ sprites; 26/26 units). REMAINING:
      meaningful values need a populated stats.db (real hunt); independent
      pass at promotion.
- [ ] #27 â€” Battery-aware mode (ROG Ally): throttle speed/fps on low
      battery, pause on critical, resume on charge. (S-M)
- [ ] #28 â€” Polished mobile remote: phone-optimized web dashboard view to
      monitor 24/7 hunts (builds on the existing HTTP API). (M)

## Later / icebox (catalog in 09-FEATURE-BRAINSTORM.md; user re-orders/culls)
- [ ] #24 â€” Story auto-player (trainer/gym battler) â€” most ambitious, most
      transformative: progress the game to bootstrap a save to any hunt. (L)
- [ ] #26 â€” Theme system (selectable color themes; palette is centralized). (S-M)
- [ ] #29 â€” Box manager / auto-release by IV/nature/shiny filter (prevents
      full-box stalls in long hunts). (M)
- [ ] #13 â€” Macro composer v2: chain macros + repeat counts + conditions. (M-L)
- [ ] #14 â€” Profile manager UI (create/duplicate/rename/delete). (S-M)
- [ ] #15 â€” Config editor GUI (catch_block/battle/cheats + CCF builder). (M)
- [ ] #16 â€” PKHeX quick-export (.pk3 of any party/box mon). (S)
- [ ] #17 â€” Multi-instance manager (several profiles, aggregating board). (L)
- [ ] #19 â€” Stream overlay theme refresh (OBS overlay â†’ dashboard style). (S-M)
- [ ] #6 â€” Idea backlog: everything else in 09-FEATURE-BRAINSTORM.md
      (egg-hatch optimizer, catch profiles, Nuzlocke, goals panel, log
      viewer, setup wizard, keybinding editor, shiny gallery, hunt-summary
      cards, cross-session history, stream chat, webhooks, crash-safe
      savestate ring, health monitor, scheduled hunts, gamepad-driven GUI,
      RNG manip, cheat presets, plugin loader UI).

## Promoted to custom 2026-07-19 (built; awaiting user in-game confirmation)
- [~] #3 â€” Custom automations + Patrol (v3 multi-map/global-nav). Awaiting
      user's in-game play-test.
- [~] #7 â€” Sandbox enhancement round (backup/restore + cloud, macros,
      multi-map Patrol, GUI pack) â€” built, adversarially verified (16-bug
      round), promoted.
- [~] #8 â€” Warp-aware global pathfinding â€” promoted; user cross-warp walk pending.
- [~] #10 â€” Gamepad + handheld menu-hide â€” promoted; user real-pad test pending.
- [~] #12 â€” Shiny alerts â€” promoted; user sees a live shiny fire it pending.
- [~] #18 â€” Auto-update notice â€” promoted; observe on a stale checkout pending.
- [~] #20 â€” Cloud save-sync v2 (off by default) â€” promoted; desktopâ†”Ally run pending.
- [~] #21 â€” Game cheat menu (+ tabbed GUI, full-dex sprite picker, XP bars,
      topmost dialogs) â€” promoted; user in-game effect test pending.

## Done
- [x] #1 â€” Vendor upstream 40Cakes/pokebot-gen3 (subtree @ 5dd898f8) (2026-07-17).
- [x] #2 â€” Deep documentation pass + Pokemon_Emerald_AI_Notes.md (2026-07-17).
- [x] #4 â€” install.py V2 (setup/update/heal + ROM handling) â€” "worked!" (2026-07-18).
- [x] #5 â€” Native dashboard GUI + handheld mode â€” "worked!" (2026-07-18).
- [ ] #24-sanity â€” SELF-CORRECTION / SANITY-CHECK (user 2026-07-20; design Â§SC).
      Story mode must never get permanently derailed: re-validate at every segment
      boundary (did the completion flag actually set? else retry/skip-ahead),
      handle out-of-place execution (self-locate), handle non-monotonic progress
      (reload/blackout moving backward), detect mid-run derailment (expected vs
      actual segment) and re-sync, bounded retries + escalation (ties Â§DR/#24-team),
      stall watch as last resort (Watchdog #22). Unifies Â§RS + Â§DR + #24-team into
      one state-machine engine. Also bounds the Treecko-Lv16 "stuck but not stopped"
      loop class.
- [~] #24-textread â€” DIALOGUE AWARENESS: read on-screen text to drive interactions
      (user 2026-07-20; design Â§DA). FEASIBILITY CONFIRMED (decode_string of
      gDisplayedStringBattle / gStringVar4 reads exact text). STARTED: move-learn
      now uses text-driven detection (both builds) â€” UNIVERSAL (matches generic
      phrases + reads the offered move dynamically, not hardcoded to any move).
      â˜… ROOT CAUSE of the Lv16 hang FOUND & FIXED (ML-13): the Emerald battle Yes/No
      has no task and was detected only by a fragile script-offset; when it stayed
      `Unknown` the old code pressed nothing (is_waiting_for_input gate) â†’ froze.
      `handle_move_replacement_dialogue` rewritten fully text/task-driven;
      `handle_evolution_scene` hand-off hardened. PROVEN by fault-injection A/B on
      both builds (old stalls ~10.6k frames & fails to learn; fix resolves in 394 &
      learns Pursuit + evolves). Faithful repro harness: scratchpad/repro_movelearn.py.
      Still want the user's real-32Ã— confirmation. FULL SYSTEM (next big build):
      Reader (normalized current text + menu/cursor) -> Classifier (text -> interaction
      type) -> Responder (type + story progress + config -> answer; multi-valid
      decisions like fossil/starter = random). Gather conversation dumps {exact text,
      speaker, valid answers, how to answer} from runtime logging + pokeemerald script
      data; build a response table. Subsumes fragile scripted-scene ride-outs; robust
      + deterministic vs flaky task-state. Backstops: no-progress watchdog + advance-
      plain-text-with-A so nothing hard-freezes.

- [ ] #24-interrupt â€” INTERRUPTION INTELLIGENCE (user 2026-07-22): the bot should
      KNOW when its current task was interrupted and by WHAT (training spin â†’
      trainer sight-line battle; navigation â†’ PokÃ©Nav call ring; heal walk â†’
      scripted scene; etc.) and resume the task accordingly instead of relying on
      the generic derail/retry loop. Today large parts are handled implicitly
      (battle listeners resume travel; _ride_out_scripted_scene; the derail
      recovery re-runs _play) â€” this item is the DELIBERATE design pass: a small
      "current intent" state (what am I doing + resume point) + an interruption
      classifier, so recovery is targeted rather than re-derived. Design first
      (fits the decision-brain seam in doc 13 Â§future).
- [ ] #24-movelock â€” BATTLE ENGINE: move-blocking/locking effects (user
      2026-07-22): Disable (last move unusable), Encore (locked INTO a move for
      N turns), and kin (Taunt â€” status moves blocked; Torment â€” can't repeat;
      Imprison; Choice-item lock later). The turn chooser (get_strongest_move_
      against / move_is_usable) currently ignores these volatile statuses, so a
      blocked move can be selected â†’ wasted turns (the game refuses the input).
      Fix: read the battler's volatile status/disable struct and filter the
      usable-move set; if EVERYTHING is blocked, Struggle happens naturally.
      Validate vs a Roxanne/Brawly-era Disable user (e.g. wild Whismur has none â€”
      find a story trainer with Disable/Encore, or fault-inject the volatile
      struct in the harness).

- [ ] #24-ch8b-museum â€” Oceanic Museum entry gating (KI-11): resolve how the
      Aqua crowd clears so Stern is reachable; then Devon Goods â†’ Stern
      (deliver_devon_goods_to_stern is built). BLOCKS Ch8b/Ch9.
- [x] #24-evo-trainstall (FIXED 2026-07-22: interrupt-safe _rotate_lead_safely + _yield_bounded; proven on evostall.ss1; same fix covers the user's 110k-frame Joey stall) â€” `train_team`/`_story_spin` can hang right AFTER a
      trainee EVOLVES mid-training (batch run02 2026-07-22: Grovyle evolved +
      learned Fury Cutter on Route 116, then the spin never resumed â†’ 20k-frame
      HANG). Repro save: tools/story-dev/saves/evostall.ss1. Likely the
      post-evolution return-to-overworld transition isn''t ridden out before the
      next spin action (cf. the move-learn / dock-arrival family). Prove + fix.
- [ ] #24-freshbatch-rustboro â€” batch run03 (fresh game) 2026-07-22 played
      extensively but HUNG in Rustboro (11,3)=(5,3) area after ~450k frames
      (Torchic start, 4-mon team). Under-investigated; capture a repro from the
      run03 log if it recurs in a future batch.


- [x] #24-pokenav-faithful (RESOLVED 2026-07-22: the user ran VIDEO OFF — the renderer-gated fallback fired exactly as designed; keep video off on the weaker test PC, the fallback covers it) — WATCH ITEM (user fresh-run log 2026-07-22 13:24): the
      PokéNav Match-Call tutorial took the STATE-WRITE FALLBACK on a real-GUI run
      (video on) — the faithful play-through previously worked on this hardware.
      By design the fallback is legal (never hang), but check why the faithful
      path didn''t engage (timing? renderer-gate read?) next time it recurs.
- [ ] #24-train-efficiency — the same run spent ~240k frames on the pre-rival
      level-floor (L10) and ~200k on the Brawly band (L15) with swap-training.
      Bounded + productive, but slow. Related: an ABRA catch (Teleport-only, can''t
      attack) rode along the whole run at L7 — confirm battler-slot exclusion is
      airtight and consider skipping Abra-class catches for team slots, or routing
      lows to level-matched grass (#24-trainmap).

- [x] #24-wattson-strength — DONE 2026-07-22 (KI-13 resolved): 0-power move-learn
      guard + Segment 9c prep (Route 117 (31,16) band 20-24) + aftermath-quiet
      riding → run 14 beat Wattson end-to-end; `wattson_done.ss1` verified.
      Residual (folded into #24-movelock): audit the evolution-scene learn flow
      that dropped Marshtomp''s Mud Shot at L16 (moot for Wattson, still a
      move-quality gap).


- [ ] #24-npc-talk-speed — Briney talk-dance polish (user log review 2026-07-22):
      BOTH user-observed oddities are the same subsystem, `_talk_to_wandering_npc`
      (observe a patrol lap -> park beside the route -> face-tap on transit):
      (a) cottage Briney (~3,600 frames of visible maneuvering before the talk at
      (6,2) in Route104_MrBrineysHouse), and (b) post-Brawly "erratic movement
      right of the gym" = the DOCK Briney ambush near (12,9) (~5-7k frames across
      four transient stucks at sail_to_slateport's dock-talk step; it completed
      and sailed — slow, not broken). FIX DESIGN: add a `known_spot` fast-path —
      navigate STRAIGHT to the recorded successful parking tile per NPC (extract
      the exact tiles from validated-run debug logs), wait bounded (~1 lap) for
      the NPC to transit adjacent, face-tap+A; on one failure fall back to the
      full observe-then-park. Keeps the proven adaptive path as the safety net.

- [ ] #24-hm-slaves — HM CARRIER ARCHITECTURE (user directive 2026-07-22 night):
      HMs are infinite-use but unremovable without the Lilycove MOVE DELETER
      (free; the Heart Scale is for Fallarbor''s Move RELEARNER — different NPC).
      Near-term policy: Marshtomp carries Rock Smash + later Strength (learns
      both; physical-type moves suit its Attack — a working mule, not a dead
      slot). Longer-term: dedicated HM slave(s) (Zigzagoon: Cut/Rock Smash/
      Strength/Surf) parked in the POKEMON PC — which requires PC deposit/
      withdraw MACHINERY (party-slot management UI flow) built BEFORE the
      Surf-era chapters (~Ch13+, Route 118 gate). Also: some moves are
      overworld-usable from the party menu (Dig, Teleport, Flash, Sweet Scent)
      — useful shortcuts (Teleport-to-PC, Dig-out-of-caves) worth wiring into
      travel logic once carriers exist.

- [ ] #24-knowledge-base — DEEP GAME KNOWLEDGE BASE (user directive 2026-07-22
      night): per-chapter, during mapping: route items (visible + HIDDEN, both
      in decomp map.jsons), puzzles, secrets, legendary unlock chains + catch
      strategies (Regis braille gates, Sky Pillar/Rayquaza, Groudon/Kyogre story
      beats), gym rosters. Machine layer: the bot''s modules/data already holds
      full species/moves/learnsets/TM-compat — the MOVE-PRIORITY SYSTEM v2
      (#24-movelock: STAB + type coverage + Gen3 physical/special-BY-TYPE
      stat-matching + utility ranking) should QUERY it, not hand-author lists.

- [ ] #24-event-pokemon — EVENT LEGENDARIES, endgame (user directive 2026-07-22
      night): Deoxys (Birth Island via AURORATICKET), Mew (Faraway Island via
      OLD SEA MAP), Jirachi (external event), Latios/Latias roamer choice + the
      EON TICKET (Southern Island second Lati). These need event-only items that
      vanilla distributed via Mystery Gift / e-Reader — the bot must obtain them
      in a way that LOOKS earned and stays quasi-canon (user framing): candidate
      mechanisms to discuss LATER — Mystery Gift spoofing (emulating the
      distribution the game natively supports — most authentic), a scripted
      "delivery man" trigger, or a direct bag write (last resort). Same
      plan/map/test loop as story chapters + a design discussion with the user
      on the acquisition theater BEFORE building. Endgame content — schedule
      after the main story skeleton reaches the Elite Four.

- [x] #24-hm-learner — HM TEACH VALIDATION + LEARNER ACQUISITION (user report
      2026-07-23, DONE same day): Segment 10b used to teach the HIGHEST-LEVEL mon,
      which loops in the party menu (NOT ABLE) whenever that mon can't learn the
      HM. Now: `hm_learner_slot(item)` picks the best COMPATIBLE party mon;
      `ensure_hm_learner(item)` hunts + catches an accessible learner species when
      the party has none (grounds derived live from ROM encounter tables ×
      TM/HM learnsets — nothing hardcoded, works for every future HM);
      `teach_hm_move` hard-fails truthfully on an incompatible target. A/B-proven
      (repro_hm_learner.py + the hmtest harness driver: fault-injected
      "nobody compatible" → hunted Route 117 → caught Poochyena → taught it).
      Feeds directly into #24-hm-slaves (the acquisition half now exists).

- [ ] #24-provisions — HEALING-ITEM PROVISIONING + STRATEGIC HEALING (user
      directive 2026-07-23): alongside Poké Balls, buy POTIONS (the best tier
      available at the local mart — Potion→Super→Hyper→Full Restore as the
      frontier advances) and keep a sensible stock; then use them with intent:
      in-battle healing when a sweep is worth saving, between-battle healing in
      places with no PC (Victory Road, THE ELITE FOUR — vanilla players stock up
      at the League mart precisely for this). Extends the buy-at-mart machinery
      (shop-agnostic `_mart_item_row` already reads stock live). Design note:
      gate on money reserve like balls; a heal-item strategy layer slots into
      the battle strategies where flee/switch decisions already live. NOT urgent
      (the fight→train→retry loop carries the mid-game) — required before the E4.

- [ ] #24-tms — TM ACQUISITION + USAGE (user directive 2026-07-23): TMs arrive as
      gym rewards (TM39 Roxanne, TM08 Brawly...), ground items, and mart stock;
      the bot should track what's in the bag, know single-use vs HM reuse, and
      teach them via the SAME validated teach flow (teach_hm_move already takes
      any TM item + hm_learner_slot generalizes — the missing piece is the
      DECISION layer: which TM to which mon, driven by the move-priority system
      (#24-movelock v2) and later the per-Pokémon profiles (#24-pokeprofiles)).

- [ ] #24-pokeprofiles — PER-POKÉMON BATTLE PROFILES, deep-research program (user
      directive 2026-07-23): build a detailed profile for EVERY Emerald-obtainable
      species (217 + evolution lines; census in emerald_obtainability.json):
      goal moveset(s) with priority order, how each move is obtained (level-up /
      TM+where / HM / tutor), training plan (when to evolve, what to delay),
      battle role (sweeper/wall/HM mule), and priority tiers so the bot knows
      WHICH mon to invest in. Execution model per the user: OVERNIGHT AUTONOMOUS
      RESEARCH in batches (10-20 species — tune for accuracy over speed), with
      self-generated Gemini assistant prompts BOTH when stuck AND routinely for
      cross-referencing/verification of my own conclusions; results verified
      against modules/data (learnsets/TM-compat are already in the bot) before
      being written. Output doubles as the reference layer for the sibling
      Pokémon Emerald AI project (Pokemon_Emerald_AI_Notes.md). Prereq for the
      full #24-tms decision layer and the "proper battling" endgame; schedule
      after the story skeleton is deeper.

- [ ] #24-economy — CASHFLOW MAINTENANCE (user directive 2026-07-23, extends the
      planning doc's money-reality note): keep a healthy balance for balls +
      potions + TMs across the whole run — trainer payouts (the main income; no
      Vs Seeker in Emerald), Amulet Coin when obtainable, selling vendor trash
      (Nuggets/Pearls/Stardust from Pickup — Zigzagoon/Linoone party slot is a
      passive income engine), and mart budgeting against the reserve. Design
      with #24-provisions; both consult one Resource Ledger (doc 13 spec).

- [ ] #24-trainersweep — EXHAUST UNFOUGHT ROUTE TRAINERS BEFORE GRINDING (from the
      2026-07-23 boss-training discussion + Gemini consult): before any wild-grass
      escalation, sweep the one-time optional trainers reachable at the current
      frontier (Wattson stage: Route 111 south Winstrate family, Route 110 cycling
      road + surface leftovers, Route 117, Trick House puzzle 1-2) — big one-time
      XP+money a faithful player takes first. Needs: per-route trainer tables
      (decomp object events, sight-lines), a "fought yet?" check (trainer flags —
      readable), and routing. Later: PokéNav Match Call REMATCHES (255-step trigger,
      call answering, scaled teams) as the true repeatable mid-game XP engine.

- [ ] #24-gemini-org — "COMPANY-STYLE" GEMINI ORCHESTRATION (user 2026-07-23, timing
      left to the agent → deferred to a quiet/overnight slot): formalize the ad-hoc
      multi-agent consult pattern (design-critique agent + adversarial agent worked
      well for the sufficiency gate) into reusable roles (researcher / critic /
      verifier / synthesizer) with standard prompts, cross-checking rules, and when
      to escalate models (3.1-pro vs flash). Candidate first use: the #24-pokeprofiles
      overnight batches. Refine WITH Gemini agents when picked up.

- [ ] #24-rare-catch — RARITY-TIERED OPPORTUNISTIC CATCHING (user 2026-07-23, future):
      extend the catch branch beyond team-building phases: RARE species (low
      encounter-slot %, version exclusives, one-shot statics) should be caught on
      sight when NOT yet owned, in ANY phase (training, traveling) — party room +
      spare balls permitting, same gating style as the HM-learner hunt. An ULTRA-RARE
      tier (the user's example: a MALE Skitty — a 2%-slot species × 25% male gender
      roll) is attempted on EVERY encounter, shiny-style, even if the species is
      already owned. Needs: a rarity classifier (encounter-table slot % from the ROM
      data × gender-ratio math — all derivable, no hand lists), tier thresholds to
      agree with the user, and integration ordering vs the shiny branch (shiny stays
      first). Pairs with #43 opportunistic catching + the Living-Dex orchestrator.
