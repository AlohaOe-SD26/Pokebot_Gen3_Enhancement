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
- [x] RULINGS: Latias+Latios BOTH obtainable (218/386); Surskit unobtainable
      (c2707bad).
- [x] #46 — Hover tooltip ball ~3× (fixed thumbnail no-op bug) (c2707bad).
- [x] #47 — Opportunistic catch: any SHINY (even owned) caught (c2707bad).
- [x] PROMOTE-2 — whole batch promoted to custom w/ extensive intent docs
      (DIVERGENCE-LOG a–i + DOCUMENTATION/05-hunting-and-livingdex.md);
      live-verified on the real save; 29b9aae5.
- [ ] #24 — STORY-MODE BOT (design-first, multi-pass/triple-check): play
      from a fresh save (user-set name; Oak intro/gender/name; Littleroot
      start) OR continue existing; goal = beat Elite 4 + complete the game
      (eventually pokedex); CHUNKED into chapters; must build+maintain a
      team; enumerate EVERY key event/interaction/item/requirement to
      progress + how to obtain progression items. Design → 12-STORYMODE-
      DESIGN.md, several verification passes before building.
      - PROGRESS (2026-07-20): a fresh game auto-plays through **GYM 1 (Stone
        Badge)** — intro→starter→first battle→Pokédex→train→rival→Petalburg→
        Dad/Wally→Route104→Petalburg Woods (Aqua scene)→Rustboro→Roxanne.
        Legs 1-2 promoted to custom; legs 3-4 + Gym 1 in sandbox (awaiting
        test→promote). Fixed the Woods-door stall (ML-9) in BOTH builds. NEXT:
        Chapter 4 (deliver Devon Goods → Rusturf Tunnel → Dewford / Gym 2).
        Low-pri OPEN: chapters.py Ch2 completion-flag bug.
- [~] #24-move — SMART MOVE-LEARNING (user 2026-07-20): DONE — Story strategy
      `which_move_should_be_replaced` override keeps every Pokémon combat-capable
      (never trades a damaging move for a status move), preserves type coverage,
      and skips no-gain moves; overrides the stock `new_move: cancel` decline.
      In both builds, unit-verified. REMAINING (folds into #24-team): status-move
      UTILITY ranking (value Sleep Powder/heal over Growl) rather than treating
      all status moves as equal.
- [~] #24-resume — RESUME-FROM-ANYWHERE (user 2026-07-20): v1 DONE — segmented
      flag-gated run() resumes from a fresh game / resumed save / hand-played
      state, skipping finished segments (fixed the "thinks I need Wally"
      mis-detection via the HIDE_PETALBURG_CITY_WALLYS_MOM flag). REMAINING:
      finer per-STEP resume with each step self-locating from any tile; FAST
      travel (Fly/Teleport/Escape Rope when available, gated by HMs/badges/items
      per #42); title-screen-with-save auto-Continue; reliable completion flags
      for chapters past Gym 1. Design §RS.
- [ ] #24-autosave — AUTO CHAPTER SAVE-STATE (sandbox testing aid; user
      2026-07-20). After each scripted chapter/segment completes in StoryMode
      (SANDBOX ONLY), auto-save a save state named by chapter into `states/` so
      chapters can be tested/resumed fast. TOGGLE in the Play tab, DEFAULT ON,
      safely toggleable on/off even while the bot runs (the story generator reads
      the flag at SEGMENT BOUNDARIES, so flipping it never interrupts). Implement
      by hooking the segment boundaries already in `StoryMode.run()` (§RS).
      **APPLY ONLY AFTER the user green-lights the current story build** (it
      touches run()); until then this is a note. Save quickly at a boundary
      (get_save_state + write) — negligible one-frame pause.
- [x] #24-loadpage — LOAD-STATE POPUP PAGINATION (user 2026-07-20): DONE both
      builds. `load_state_window.py` now shows 5 states/page and lazily renders
      only the current page's thumbnails (Prev/Next + arrow/PageUp-Down + page
      label; nav auto-hidden for one page). Fixes the slow-open with a full
      `states/` folder (was decoding up to 128 PNGs at once).
- [ ] #24-defeat — DEFEAT RESPONSE (user 2026-07-20; design §DR). What the bot
      does when it LOSES a battle, as a settings-popup choice:
      (A) "Reload save state" = today's watchdog behaviour, made a toggle; verify
      the resume-after-reload rough edges (the segmented resume §RS already fixes
      most — the old run() stranded the bot on any restart; also ensure watchdog
      snapshots are CLEAN OVERWORLD states, never mid-battle/scene).
      (B) "Play through & retry" = ride out the whiteout → respawn (Poké Center /
      early houses) → recalc position + story segment (§RS) → MATCHUP ASSESS (avg
      enemy vs own level, team size, type/move coverage) → train/adjust team
      (#24-team) if outmatched → escalate on repeated loss → retry. Mode B = §RS +
      matchup gate + #24-team, one engine. Sub-parts: a small matchup scorer;
      whiteout ride-out; failure/attempt tracking per objective.
- [~] #24-evo — EVOLUTION policy (user 2026-07-20): CURRENT (sandbox+custom) =
      ALLOW ALL evolutions (`should_allow_evolution → True`, overriding the stock
      `stop_evolution`) — fixes the Lv16 evolve+move-learn hang and strengthens
      the team. POPUP options to add (#24-ui): **allow all (default on) / random
      evolution / no evolution**. Robustness the bot must have (verify): RECOGNIZE
      when an evolution happens, navigate the evolution CUTSCENE, and handle the
      accept/deny of a new move + deleting an old one to replace it (uses the
      stock evolve→learn path + `which_move_should_be_replaced`). "Random" mode =
      per-Pokémon coin-flip whether to evolve (organic team variety, ties #24-team).
- [ ] #24-team — ORGANIC TEAM-BUILDING / helper acquisition (user 2026-07-20;
      design in 12-STORYMODE-DESIGN §TB). Bot builds a team to beat gyms/trainers
      but decides to catch "helpers" ORGANICALLY: a rising "recruit urge" that
      grows with failed/struggled battles (increasing re-rolls/odds), weighted by
      real team gaps (type matchup vs the fight, team type-diversity, move
      coverage), pulling candidates from the obtainability+reachability data
      (#41/#42). Random/human-like, not a min-maxer. Needed for Torchic-vs-Roxanne
      and later type-hard gyms; implement when a gym requires it.
- [ ] #24-shops — MAP SHOPS AS REACHED (user 2026-07-21; planning doc §4). Each mart
      has its own layout AND stock/order; the buy code is already shop-agnostic
      (universal task-driven flow + `_mart_item_row` reads stock live). So map each
      shop's ENTRY facts (mart map, clerk-approach tile, facing) when first reached,
      verify live, add an Atlas row. SPECIAL: **Lilycove Department Store** is
      MULTI-FLOOR (per-floor shop + stock, elevator nav); the **Elite Four Poké
      Center** has a shop + mart; Slateport stalls / TM sellers use non-standard
      menus. Do NOT map all shops up front (unreachable → can't verify).
- [ ] #24-pc — PC / BOX TEAM MANAGEMENT (user 2026-07-21; planning doc §4b). Advanced
      team development via the Pokémon Storage PC: store / move / withdraw Pokémon
      (and items). Map PC access points (every Poké Center + player's-house PC) and
      the PC UI (Deposit/Withdraw/Move, box navigation, party↔box swaps, item
      storage). Enables swapping in a better-matched mon per gym and parking
      over-levelled/redundant catches. Build when a fight needs it; ties #24-team /
      §7 matchup awareness. Poké Centers are otherwise near-identical (generic code
      handles them) — only map PC/layout exceptions (e.g. the E4 Poké Center).
- [x] #24-resume — SEGMENT 1 RESUME BUG FIXED (2026-07-21). Pre-Pokédex
      recovery/resume re-ran the scripted intro from the truck → derail loop
      ("stuck after respawn"). Split Segment 1: scripted intro gated on
      `_has_starter()`; train→rival→Pokédex resumable + flag-gated. Derail budget
      hardened (monotonic party `_progress_sig`; patient recovery). Verified in
      harness. Sandbox (early_game.py, story_mode.py). See CHANGELOG/MISTAKES 07-21.
- [x] #24-freeze — OLDALE PC FREEZE **FIXED** (user 2026-07-21). Root cause (from the
      user's real-bot debug log's generator call stack): heal returned while the
      overworld was transiently non-controllable → heal→go-to-rival navigate choked →
      derail → re-heal → endless heal/leave/re-enter loop → Manual. FIX:
      heal_in_pokemon_center waits for a STABLE controllable overworld after the exit
      warp. Downstream: StoryCatchStrategy flees instead of Manual when out of balls.
      Validated route103→Rustboro→Route116 catching, 0 derails/Manual. Old note below
      kept for history.
      ~~POST-BATTLE TRANSITION FREEZE (the likely real "stuck at Oldale PC").~~ After a training battle (flee/level-up/move-learn, e.g.
      Mudkip Water Gun @L10) the return-to-overworld transition leaves the overworld
      non-controllable while the bot acts (navigate / walk to the Oldale nurse) → can
      hard-freeze (nurse heal dialogue never starts). REAL (harness == real
      main_loop), timing/starter-sensitive (default starter "random"; Treecko passed,
      Mudkip hits it). Offline repro hampered by save-state reload artifacts. NEXT:
      user validates on real PC (force `starter: mudkip`, fresh game) and reports;
      then decide a deeper "settle before acting" fix (heal_in_pokemon_center nurse
      interaction + story navigations) vs a training-flow workaround.
- [x] #24-debuglog — DEBUG LOGGING TOGGLE (user 2026-07-21). Opt-in "Debug Logging"
      in the Run (bot-mode) menu (both GUIs), default off → `modules/debug_logger.py`
      writes an extensive structured log to `<profile>/debug-logs/` (event stream +
      stuck dumps with the generator call stack). For diagnosing Bug #2 (#24-freeze)
      from a shared real-bot log. Built + validated in sandbox. See CHANGELOG 07-21.
- [ ] #24-ui — STORY-BOT PRE-RUN SETTINGS POPUP (user 2026-07-20). A popup/menu
      shown BEFORE the Story bot runs to set: player name; starter nickname mode
      (none / defined / random); starter choice (specific / random); + other
      settings TBD. Front-end for the existing `<profile>/story.yml`
      (character_name/gender/starter/starter_nickname already read by
      modules/story/config.py). WORK ON THIS ONLY AFTER the bot is finished and
      tested 100% (user directive). Popup also hosts the #24-autosave toggle
      (auto chapter save-state, default on) and the #24-defeat "Defeat response"
      section (Reload-save-state vs Play-through-and-retry + sub-toggles).

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
- [ ] #24-sanity — SELF-CORRECTION / SANITY-CHECK (user 2026-07-20; design §SC).
      Story mode must never get permanently derailed: re-validate at every segment
      boundary (did the completion flag actually set? else retry/skip-ahead),
      handle out-of-place execution (self-locate), handle non-monotonic progress
      (reload/blackout moving backward), detect mid-run derailment (expected vs
      actual segment) and re-sync, bounded retries + escalation (ties §DR/#24-team),
      stall watch as last resort (Watchdog #22). Unifies §RS + §DR + #24-team into
      one state-machine engine. Also bounds the Treecko-Lv16 "stuck but not stopped"
      loop class.
- [~] #24-textread — DIALOGUE AWARENESS: read on-screen text to drive interactions
      (user 2026-07-20; design §DA). FEASIBILITY CONFIRMED (decode_string of
      gDisplayedStringBattle / gStringVar4 reads exact text). STARTED: move-learn
      now uses text-driven detection (both builds) — UNIVERSAL (matches generic
      phrases + reads the offered move dynamically, not hardcoded to any move).
      ★ ROOT CAUSE of the Lv16 hang FOUND & FIXED (ML-13): the Emerald battle Yes/No
      has no task and was detected only by a fragile script-offset; when it stayed
      `Unknown` the old code pressed nothing (is_waiting_for_input gate) → froze.
      `handle_move_replacement_dialogue` rewritten fully text/task-driven;
      `handle_evolution_scene` hand-off hardened. PROVEN by fault-injection A/B on
      both builds (old stalls ~10.6k frames & fails to learn; fix resolves in 394 &
      learns Pursuit + evolves). Faithful repro harness: scratchpad/repro_movelearn.py.
      Still want the user's real-32× confirmation. FULL SYSTEM (next big build):
      Reader (normalized current text + menu/cursor) -> Classifier (text -> interaction
      type) -> Responder (type + story progress + config -> answer; multi-valid
      decisions like fossil/starter = random). Gather conversation dumps {exact text,
      speaker, valid answers, how to answer} from runtime logging + pokeemerald script
      data; build a response table. Subsumes fragile scripted-scene ride-outs; robust
      + deterministic vs flaky task-state. Backstops: no-progress watchdog + advance-
      plain-text-with-A so nothing hard-freezes.
