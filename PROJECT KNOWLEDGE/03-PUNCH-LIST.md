# Punch List â€” Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N â€” description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).
> Full future-idea catalog: `09-FEATURE-BRAINSTORM.md`.

## Now (active focus)
- [ ] **#24 — STORY AUTO-PLAYER.** The only active work. A cold start reaches
      **Badge 6 (Winona) = end of built content** (38 maps, ~2.48M frames, 0 derails).
      Sub-items live in `## Story bot (#24) — open backlog` below; the current order is:
      1. `#24-whiteout` (attrition dominates; the successful run still took 80)
      2. `#24-counters` phase 2 (the chain NAMES a counter; acting on it isn't built)
      3. `#24-regionreach` gate table + the blocked training-gate switch (KI-24b)
      (`#24-movelearn-recovery` — DONE 2026-07-25, see Done below.)
      Next unbuilt chapters: **Mt. Pyre**, then the **Magma hideout**.
- [ ] #V â€” Post-promotion verification sweep (PARKED behind #24): independent adversarial pass
      on the promoted features that only had builder self-verification (not
      an independent pass) â€” #8 global pathfinding, #12 shiny alerts, #18
      update notice, #20 cloud-sync, and the 2026-07-19 GUI polish (tabs /
      full-dex picker / XP bars / topmost dialogs). Interrupted twice by
      credit limits; run it against custom-pokebot before relying on the
      save-touching bits (cloud-sync ships off-by-default, so inert).

- [ ] #24-x4 — **ENDLESS LOOP ×4** (user request 2026-07-26): four independent
      `Story (ENDLESS RESET)` bots at once, one process + profile + starter each
      (P1 torchic / P2 mudkip / P3 treecko / P4 random), tiled 2×2 in the
      dashboard's video area, looping forever and restarting independently.
      A TEST INSTRUMENT — it exists to raise the rate of reviewable failure data
      and guarantee starter coverage.
      **Phase 1 BUILT in sandbox (2026-07-26), tests green, LIVE RUN NOT YET DONE**
      — this dev box has no `mgba`, so nothing involving a real emulator has been
      exercised. See 04-HANDOFF for the exact live confirms the user must run.
      **Phase 2a DONE 2026-07-26** — the party strip / party tab / hover tooltip
      follow the focused lane (`modules/remote_party.py` rebuilds stand-ins from the
      lane's status blob; the renderer is unchanged). Live confirm still owed.
      **#24-x4-logs DONE 2026-07-26** — `Emulator > Park x4 & Collect Logs...`
      (batch-only menu item): parks every lane, bundles all four lanes' logs into
      one verified zip under `profiles/x4 LOGS/`, archives the originals to each
      profile's `debug-logs/Old/` only AFTER the zip verifies. Added the
      parent->child command channel that phase 2b will reuse. Live confirm owed.
      Phase 2b (agreed with the user, NOT built): the watch/CONTROL toggle — click a
      tile then drive it, forwarding `press_button`/`hold_button`/`release_button`
      over a per-lane input pipe (`modules/libmgba.py` already exposes exactly that
      surface, so the channel is strings, not input-model surgery).
- [ ] #24-badges — **TRAINER-CARD / BADGE CASE overlay** (user request 2026-07-26):
      a Bag-icon button under the 6th party slot opens an overlay to the right laid
      out like the in-game badge case — 8 badges, black silhouette until earned —
      and hovering/clicking one shows that gym leader's details plus THE TEAM THAT
      BEAT THEM. User said it may be tabled; the UI is tabled, the capture is NOT.
      **DONE:** `modules/badge_log.py` records the party at the instant each
      `BADGE0N_GET` flag flips, to `<profile>/badge-log.json`, re-arming on emulator
      reset so every run of an x4 batch is captured. Shipped first because it can
      only record badges earned AFTER it is on — waiting would have thrown away
      every x4 run's badge data (06-DECISIONS-LOG).
      **UI DONE 2026-07-26** — Bag button under the 6th ball + the 2x4 badge-case
      overlay (silhouette until earned, hover/click for leader detail + the team
      that won). Leader table decomp-verified in `modules/badge_case.py`; the 8th
      leader is JUAN, not Wallace (that error shipped first — 08-MISTAKES).
      Live confirm owed. **REMAINING:** real Bag artwork (the icon is PIL-drawn;
      the repo ships none); and choosing WHICH run's team to show when a badge has
      many recorded wins — currently the latest, with a count of the rest.
- [ ] #24-badges-live — **Make the badge case LIVE, like the party strip**
      (user request 2026-07-26). Today `_badge_case_source()` already reads the
      FOCUSED x4 lane, so opening the Bag after clicking P3's tile shows P3 — but
      the contents are a SNAPSHOT taken in `open_badge_case()` and cached in
      `_badge_case_entries_cache`. Two consequences to fix:
        (a) clicking a different tile while the case is OPEN does not switch it —
            `_x4_click` refreshes the party (`_refresh_party` + `_refresh_party_strip`)
            but not the case;
        (b) it does not tick over as badges are earned during a run.
      Wanted: the case tracks focus changes and refreshes on a cadence, the way the
      party strip does off `_refresh_sidebar`.
      ‼ Design constraint that produced the snapshot in the first place: the entries
      come from `badge_log.read_log()`, i.e. a DISK READ of `badge-log.json`, and
      `_show_badge_detail` runs on every hover — a naive "just read it live" turns
      mouse movement into file I/O. Refresh on focus-change and on the KPI/sidebar
      cadence (or when the lane's published badge set changes), NOT per hover.
      Cheap seam available: lanes already publish `badges` in their status blob, so
      "has anything changed?" is answerable without touching the disk.
      Assets are NOT a blocker: all 8 Hoenn badge sprites already exist at
      `modules/web/static/sprites/badges/` (Stone, Knuckle, Dynamo, Heat, Balance,
      Feather, Mind, Rain). The only missing art is a Bag icon.

## Under discussion (user 2026-07-26, NOT agreed scope — see `19-TEAM-BUILDING-DISCUSSION.md`)
> ‼ Do NOT start these. Each has open questions that must be answered with the user first;
> the design note records them. Promote to the active list once resolved.
- [ ] #24-gymtrainers — **Battle gym/town trainers BEFORE grinding wild, at every gym.**
      Raised for Dewford (bot trains in the cave; user says it should be on "the second
      floor" AND should clear the island + gym trainers first for XP and money). Directly
      attacks the #1 failure in batch `20260726-181825`: attrition, not gym leaders (P2
      whited out 41× on Route 110 and derailed). ‼ Open: WHICH floor (Granite Cave 1F/B1F/
      B2F); always vs only-when-underlevelled; town-wide vs arc-wide trainer scope.
      **ANSWERED 2026-07-26: train on Granite Cave B1F AND B2F; fight trainers ALWAYS.**
      ‼ **ALL FACTS NOW DECOMP-VERIFIED** (see `19-TEAM-BUILDING-DISCUSSION.md` §8) and the
      spin tiles are recorded in `training_areas.py` PENDING_GRASS: **B1F (3,18) L9-11**,
      **B2F (28,17) L10-12**, neither gated by any HM/item/flag. B1F's 62 cracked-floor
      tiles are all UNREACHABLE ON FOOT (north of an unclimbable muddy slope).
      ‼ **BLOCKED ON ONE THING:** `_CAVE_EXITS` / `_CAVE_ENTRANCES` are SINGLE-HOP tables,
      and B1F/B2F are 2-3 hops deep from Route 106. Promoting them without making that
      threading chain-aware breaks the post-training HEAL — the global navigator cannot
      cross warp levels, and that exact failure already dropped two real-hardware runs to
      Manual (2026-07-22). **Next step: make cave entry/exit chain-aware, then promote,
      then validate live.** Deliberately NOT done blind — this is navigation code.
      ‼ **PRIORITY NOTE:** this spot only fires after ≥2 Brawly losses, and batch
      `20260726-201838` had 2-3 Dewford losses in the whole batch. Runs are dying at
      MAUVILLE (Wattson) and PETALBURG (Norman), not Dewford. Worth doing because the user
      asked and the data is now free, but it is not where the failures are.
- [ ] #24-partyvariety — **Fill the party and vary what is caught; PC deposit/withdraw.**
      ‼ **ROOT CAUSE FOUND (recon 2026-07-26) — it is not emergent, it is two conditions.**
      `_should_catch` (`story_mode.py:899-937`) requires `not BADGE01_GET` AND
      `len(party) < _catch_team_target` where **`_catch_team_target = 4`** (`:811`). So the
      bot catches FOUR mons before the Stone Badge and then never catches again for the
      rest of the run. Part 1 is nearly a one-line change.
      ‼ **PC automation ALREADY EXISTS and is unused:** `modules/pokemon_storage.py` (full
      box READ) + `modules/modes/util/pc_interaction.py` (804 lines: withdraw / deposit /
      release), whose only consumer is `daycare.py`. `#24-pc`'s "map the PC UI" is already
      done — what is missing is navigation to a PC and a keep/box POLICY. The shiny path
      already proves party-full→box works (`story_mode.py:1456-1482`).
      ‼ **CONFIRMED ONE ITEM WITH `#24-counters` PHASE 2** — the counter chain currently
      diagnoses and then RAISES `BotModeError` (`story_mode.py:1309-1313`); that raise is
      the seam where fetching would hook in, and `HM_CATCH_TARGET_DEX` (`:1485-1511`) is a
      working "catch species X on sight" primitive to reuse. Blocked on counter tiles being
      mapped (every candidate has `tile: None`).
      Also: **dead weight is invisible by construction** — `_battler_slots()` only asks
      "not an egg, has a move with base_power > 0", so a L5 CASCOON in a L24 party passes,
      and `_prepare_for_fight` then excludes it from training. Cheap first win: bench or
      deposit anything more than N levels below the lead.
- [ ] #24-personality — **A two-axis bot "personality" (user answer 2026-07-26).** The
      user wants BOTH testing-diversity and competence, selected by a personality that
      swings and drifts during play so it looks organic. Recommendation in the design
      note: TWO axes (`curiosity` = what it collects/fields, `caution` = how much risk it
      takes), because one axis forces "more varied" to also mean "more reckless".
      Drift should be EVENT-DRIVEN (whiteout -> caution up; clean streak -> caution down),
      not a random walk. ‼ TRAP: "cautious" must NOT mean "grind longer" — P2 whited out
      41x on Route 110 while training, so that loop would worsen the dominant failure.
      Must be a pure function of (seed, events) so it is testable without an emulator, and
      the rolled values must reach the logs so personality can be correlated with outcome.
- [ ] #24-favourite — **Roll a "favourite" species per run.** Prefer to catch/keep it,
      unless it is a disadvantage for the fight about to be entered. Cheap run-to-run
      variance that is independent of the RNG decorrelation already in place.
      **ANSWERED 2026-07-26:** "disadvantage" = a TYPE CHECK, applied to gym leaders /
      rival / Wally / Elite Four, PLUS reactively when a trainer keeps beating the bot
      (hang that off the existing `_defeat_counts`, `story_mode.py:813`). TWO favourites
      per run: one regular, one LEGENDARY. Pool = anything obtainable in Emerald —
      ‼ derive it from `modules/obtainability.py` + `emerald_obtainability.json`, never a
      hand-written list, and check whether that model counts event-only species (Mew,
      Deoxys, Jirachi, Ho-Oh, Lugia) as obtainable. Honest note: every Hoenn legendary is a
      late-game static, and the frontier is ~Badge 3, so the legendary favourite will do
      NOTHING for run diversity yet — build it, log it, expect nothing from it for now.
      ‼ The rival / Wally / E4 rosters are NOT yet decomp-verified (gym leaders are, in
      `modules/badge_case.py`); they need that before the type check can use them.
      Still open: preference strength; per-run vs per-lane (recommend per run).

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
      - PROGRESS (2026-07-24 overnight): fresh runs auto-play through GYM 4
        (Heat Badge) organically (3/5 lanes, batch 20260724-004252). Ch12
        BUILT + WIRED (Segment 12a/b/c: Lavaridge-Petalburg direct route,
        Wanda-wall smashes, sign-script gym doors, Norman, auto Surf handoff,
        teach Surf) - live-iterating from flannery_done (travel proven, gym
        chain walking). KI-15 FIXED (3 proven fixes); KI-17 opened (after-
        faint reshow freeze, 2 states captured, Gemini-diagnosed DMA race,
        sweep hardened per the analysis - validation pending).
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
- [~] #24-trainmap â€” AREA-APPROPRIATE TRAINING (user 2026-07-21, Option 1).
      **ROUTING HALF DONE (2026-07-24):** `modules/story/training_areas.py` carries
      `TRAINING_GRASS` (10 areas with VERIFIED spin tiles + level bands), `AREA_PREREQ`
      (surf/region gates), `best_training_area(team_level, min_wild_max=, allow=)` and
      `estimate_frames_to_level()`. `_prepare_for_fight` calls it with the
      `_training_area_allowed` reachability predicate and RELOCATES via
      `_goto_training_area` (warp-aware), healing at the PC nearest THAT area — this is
      what stopped the Norman fodder grind. Swap-train (#24-swaptrain) remains the
      anywhere fallback.
      **REMAINING: the `PENDING_GRASS` spin tiles** — Route 104, Petalburg Woods,
      Rusturf Tunnel and Granite Cave 1F still have `None` tiles, so they can never be
      proposed. Fill each as the map is reached (two-way sweep from a real story anchor,
      per the Route 111/114 lesson: same-map connectivity does NOT imply the story can
      get there), then move the entry into `TRAINING_GRASS`.
      Related: `#24-regionreach` (the reachability predicate itself), `#24-watertrain`,
      `#24-healverify`.
      ‼ **NOW ENFORCED IN CODE — see `training_areas.NO_RETURN_GROUNDS`** (2026-07-26).
      This paragraph is history; the table is the authority, and both training pickers
      refuse those maps before any reachability check. It was moved into code because
      this prose was re-derived from scratch by a probe cycle on 2026-07-26 (08-MISTAKES).
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

## Story bot (#24) — open backlog
> Two groups: the PRIORITY block was added 2026-07-25 by the doc audit (these IDs were
> referenced all over the changelog/handoff but had no punch-list entry at all). The rest
> were sitting under `## Done` while still open (`- [ ]`) and were moved here the same
> day — not reworded, only relocated.

### Priority block (added 2026-07-25 — previously referenced but unlisted)
- [~] **#24-whiteout — MEASURED 2026-07-25; half fixed, half is now `#24-counters` phase 2.**
      ‼ It is **not** attrition in the general sense. Census of all 5 night5 runs (~128
      losses; losses:whiteouts are 1:1 — no potion/revive layer exists, so a loss always
      whites out): **~83% of losses are GYM LEADERS** — `PETALBURG_CITY_GYM` 38 (Norman),
      `MAUVILLE_CITY_GYM` 24 (Wattson), `FORTREE_CITY_GYM` 20 (Winona),
      `LAVARIDGE_TOWN_GYM_1F` 18 (Flannery), ROUTE110 10, Dewford+Rustboro 6. Travel and
      wild encounters are noise by comparison.
      **What boss-as-training-vehicle actually delivers** (run3, Norman, traced): 27
      attempts / **508,000 frames** (~19k each) / **+2-4 levels total** / **KOs flat at
      1-2 of 4 for all 27** / a L15 Shroomish carried untrained the whole way.
      **DONE:** the plateau detector was **power-blind** and could never have fired on
      Norman — its "we have an answer" veto accepted **Rock Smash (20 power)**, the HM
      the bot must carry, because Fighting is 2.0x vs Normal. Now requires
      `base_power x effectiveness x STAB >= CREDIBLE_ANSWER_POWER` (60). A/B on the real
      party: `(False, []) -> (True, ['Fighting'])`. Its silent `except` now warns.
      (Note the night5 logs PRE-DATE the whole counter chain — 07:36 vs 09:47-13:27 — so
      those 27 attempts had no guard at all, and would still have had none without this.)
      **LIVE-CONFIRMED 2026-07-25** (batch `20260725-194810`, 5 fresh lanes): the guard
      fired on Norman at **exactly 6 losses** in 2 runs (was 27), Petalburg-gym losses
      38 -> 14 batch-wide, and **1/5 reached the frontier** (baseline 0/5).
      **✅ TRAVEL ATTRITION FIXED 2026-07-26 — SURVIVAL MODE.** run01 lost **25 times on
      ROUTE110** (largest single cluster, 31 of 66 batch-wide). Root cause was NOT training:
      with no `train_team` session, `on_battle_started` falls through to
      `LevelUpTravelBattleStrategy`, which fights every wild to level the lead and "flees only
      at low HP, which the training loop covers by healing" — but a TRAVEL leg has no training
      loop and so never heals. After `SURVIVAL_WHITEOUT_THRESHOLD` (3) defeats on a map, wild
      battles there are FLED. Narrow by design and asserted in `repro_survival_mode.py` (7
      cases): wild only (trainers are un-fleeable, boss path untouched), never during
      `train_team`, per-map. On the real run01 state it flees — 22 of those 25 whiteouts
      would not have happened.
      **REMAINING:** the bot now STOPS with a named counter instead of grinding forever.
      Actually travelling/catching/training it is `#24-counters` phase 2 — the two items
      are the same problem from opposite ends. Also still unbuilt: a potions/healing
      layer (`#24-provisions`) so a loss is not automatically a whiteout, and benching
      dead-weight party members (a L15 in a L30+ team is a free loss).
- [ ] **#24-pokenav-faithful — the FAITHFUL PokéNav tutorial is being skipped 8 runs out of 9.**
      Measured across the user's real-hardware logs (2026-07-26): ONE run played it faithfully
      ("PokéNav Match-Call tutorial (calling Mr. Stone)... done (called Mr. Stone)"), the other
      EIGHT fell back to "clearing the forced PokéNav Match-Call tutorial (state-write to vanilla
      end-state)". Not a breakage — the fallback reproduces vanilla's exact end-state and never
      hangs, so runs continue — but the standing faithfulness directive makes the state-write a
      LAST RESORT, and it has quietly become the norm on real hardware where the renderer IS on
      (which is the condition the faithful path needs). The 1 success proves the faithful path
      still works, so this is a trigger/stall-detection question, not a dead feature.
      Start by logging WHY the fallback fired (renderer state, which stall bound tripped) —
      today nothing records the reason, so the choice is invisible.
- [ ] **#24-npcheal — heal at an NPC, not only at a Poké Center.** Re-pair the Route 111
      training band to `ROUTE111_OLD_LADYS_REST_STOP` (decomp-cited: a full, ungated,
      repeatable heal — **96 steps vs 213** to Fallarbor). Blocked on a heal-at-NPC
      helper: every current heal path assumes a Poké Center layout (KI-19).
- [~] **#24-counters — CATCH A TYPE COUNTER when the boss plan cannot converge (KI-23).**
      **Phase 1 DONE (2026-07-25):** `_boss_plan_is_hopeless` detects non-convergence
      (6 losses + flat KOs + nothing hitting the boss's `ace_types` for ≥2.0), computes
      the needed types from the real type chart, and `counter_plan.find_counter_candidates`
      ranks catch targets over the whole-game encounter index, gated by
      `_counter_area_allowed` → `region_reach`. Proven from the Winona-era save: it names
      **Electrike on ROUTE118 (29,15), L24-26, 30% — REACHABLE**, where the old predicate
      returned zero. Fail-safe in all three planner outcomes (`repro_counter_wiring.py`).
      **Phase 2 NOT STARTED:** actually travelling to the target, catching it, and training
      it. Today the bot converts an unbounded loop into a bounded stop that NAMES the fix;
      acting on it is the next step and needs a live run to validate, not a repro.
      **SPEC + ECONOMICS: `12-STORYMODE-DESIGN.md` §CC2 (+ its 2026-07-26 update).**
      Blocker #2 (ranking) is CLOSED — candidates now sort by ESTIMATED COST (frames to
      find + frames to train to the team's level) instead of encounter rate; measured
      effect on the real save: Machop/Jagged Pass 75,949 vs Makuhita/Granite Cave 315,260,
      i.e. the old order preferred the 4.2x more expensive option.
      ‼ **REMAINING BLOCKERS, in order:**
      (1) **Tiles** — every candidate has `tile: None`; no counter map has a verified spin
          tile, so there is nothing to path to. Field work (two-way sweeps from a real
          story anchor). `GRANITE_CAVE_1F (35,11)` already sits in `PENDING_GRASS`;
          FIERY_PATH is the better target (on the Ch10 route, traversable both ways,
          unlike Jagged Pass's one-way ledges).
      (3) **Victory Road / E4 gate must enter `KNOWN_GATES`** — and cost ranking made this
          MORE urgent: Hariyama L38-42 is already above the team, so its training cost is
          ~0 and it ranks #1 the moment anything calls it reachable. Only the `max_hops=4`
          distance bound kept it out of the live answer, which is luck, not a gate.
      (4) Exclude story interiors (`GRANITE_CAVE_STEVENS_ROOM` is proposed as a hunting
          ground).
      ‼ **Value check before building:** priced against the measured cost of the current
      behaviour (run05 lost to Norman 21x ~ 399,000 frames; run3 27x = 508,000), a Machop
      costs 98,877 and a Makuhita 363,982 — but the only counter the LIVE predicate
      accepted was the Makuhita, i.e. ~9% better than doing nothing. **Phase 2's value is
      gated by reachability, not ranking** — widen reachability first or it buys little.
- [~] **#24-regionreach — region-scale reachability oracle.** ‼ **A WRONG *YES* COST 2 OF 5
      LIVE RUNS (2026-07-25) — now bounded.** `_training_area_allowed`'s cost model said a
      wrong yes "costs ONE wasted walk, fails RECOVERABLY and loudly"; in batch
      `20260725-194810` it cost the RUN, twice, because the picker is DETERMINISTIC and every
      derail re-picked the same unreachable ROUTE111 (25,55) from Mauville (that tile is
      FALLARBOR-SIDE ONLY — north of the Go-Goggles desert — while `is_map_reachable` is
      correctly True for the map). FIXED generally, not per-tile: new
      `UnreachableDestinationError(BotModeError)` + `StoryMode._training_unreachable`, keyed
      `(standing map, target map, tile)` so a directional ground survives elsewhere
      (`repro_training_unreachable.py`, 5 cases). This bounds EVERY future `KNOWN_GATES` gap
      to one wasted walk — which is the point of (a) below.
      **BUILT + PROVEN**
      (`modules/story/region_reach.py`, `repro_region_reach.py`): a graph from the ROM's own
      `MapConnections` + warps, capability gates, and `why_unreachable()` reasons that keep
      "no connection path" / "needs Surf at A↔B" / "reachable but N hops away" as three
      distinct facts. **STILL OPEN:**
      (a) **`KNOWN_GATES` must GROW** — it holds ONE hand-verified entry (Dewford's two sea
      edges), so any gate not derivable from ROM data reads as UNGATED. This oracle fails
      OPEN where the old one failed CLOSED; that is the right direction for a planner but
      must be grown before it gates anything irreversible.
      (b) ~~Only one caller is wired~~ **DONE 2026-07-25 — BOTH callers now use it.**
      `_training_area_allowed` was switched off `calculate_path`; the Winona candidate list
      went from `[False × 10]` to `[True × 5, False × 5]` (Route 118 Electrike reachable).
      Landing it exposed a partial-mock bug in `repro_fodder_grass._stand_at()` that had been
      giving false confidence to every training-logic change for two days (see 08-MISTAKES).
      (c) ~~`repro_counter_plan.py:200` red~~ **RESOLVED 2026-07-25 (user ruling):** the
      non-vacuity check moved off the wide type set (where it required an unreachable entry to
      exist, and so inverted when the predicate was fixed) onto the WINONA set, asserted to
      span both branches — the property the sort proof actually needs. Full repro suite 5/5.
- [ ] #24-edgecost — finer travel cost than a flat 1-hop edge (**DEFERRED**). Uniform
      weighting compresses "same landmass cluster" (1-4 hops) — measured from ROUTE120,
      Lilycove (2) reads as CLOSER than Route 118 (3), the actual answer — because one ROM
      connection can span a whole sea route. If finer granularity is ever needed: weight
      each edge by the source map's traversal length, or price travel in FRAMES so it
      composes with `training_areas.estimate_frames_to_level`. **Not needed until hop count
      demonstrably mis-ranks something** — today `max_hops` is only ever a filter (KI-24b).
- [ ] #24-fortreelive — close the Fortree Kecleon-chokepoint proof properly. The current
      evidence is a strong FAULT-INJECTION proof (flag 969 injected → (25,8) walkable), not
      a live post-flush save. Capture a checkpoint keyed on flag 969 and re-run §6/7
      WITHOUT injection to close it. Residual verification debt only — the live playthrough
      already sets the flag first via `get_devon_scope`.

### Moved out of `## Done` (still open)
- [ ] #24-sanity â€” SELF-CORRECTION / SANITY-CHECK (user 2026-07-20; design Â§SC).
      Story mode must never get permanently derailed: re-validate at every segment
      boundary (did the completion flag actually set? else retry/skip-ahead),
      handle out-of-place execution (self-locate), handle non-monotonic progress
      (reload/blackout moving backward), detect mid-run derailment (expected vs
      actual segment) and re-sync, bounded retries + escalation (ties Â§DR/#24-team),
      stall watch as last resort (Watchdog #22). Unifies Â§RS + Â§DR + #24-team into
      one state-machine engine. Also bounds the Treecko-Lv16 "stuck but not stopped"
      loop class.
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
- [ ] #24-freshbatch-rustboro â€” batch run03 (fresh game) 2026-07-22 played
      extensively but HUNG in Rustboro (11,3)=(5,3) area after ~450k frames
      (Torchic start, 4-mon team). Under-investigated; capture a repro from the
      run03 log if it recurs in a future batch.
- [ ] #24-train-efficiency — the same run spent ~240k frames on the pre-rival
      level-floor (L10) and ~200k on the Brawly band (L15) with swap-training.
      Bounded + productive, but slow. Related: an ABRA catch (Teleport-only, can''t
      attack) rode along the whole run at L7 — confirm battler-slot exclusion is
      airtight and consider skipping Abra-class catches for team slots, or routing
      lows to level-matched grass (#24-trainmap).
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
- [ ] #24-provisions — HEALING-ITEM PROVISIONING + STRATEGIC HEALING (user
      directive 2026-07-23): alongside Poké Balls, buy POTIONS (the best tier
      available at the local mart — Potion→Super→Hyper→Full Restore as the
      frontier advances) and keep a sensible stock; then use them with intent:
      in-battle healing when a sweep is worth saving, between-battle healing in
      places with no PC (Victory Road, THE ELITE FOUR — vanilla players stock up
      at the League mart precisely for this). Extends the buy-at-mart machinery
      (shop-agnostic `_mart_item_row` already reads stock live). Design note:
      gate on money reserve like balls; a heal-item strategy layer slots into
      the battle strategies where flee/switch decisions already live.
      !!! PRIORITY RAISED 2026-07-26 (user directive) - AND THE DATA AGREES EMPHATICALLY.
      The old note said "NOT urgent (the fight/train/retry loop carries the mid-game)".
      Batch 20260726-201838 refutes it: LOSSES AND WHITEOUTS ARE 1:1 IN EVERY LANE --
      P1 27 losses / 27 whiteouts, P2 43/44, P3 10/10, P4 12/12. With no potion or revive
      layer, EVERY battle loss becomes a full whiteout: respawn at the last Center, walk
      all the way back, re-fight. A heal-item layer is the single change that breaks that
      1:1, converting the most expensive failure in the game (whiteout + travel) into the
      cheapest (one turn spent on a Potion).
      Build order: (1) BUY -- extend the existing mart machinery, gate on a money reserve
      as Poke Balls already do; (2) USE IN BATTLE -- a heal threshold in the battle-strategy
      layer where flee/switch already decide; (3) USE BETWEEN BATTLES where there is no PC.
      Steps 1+2 alone should measurably cut whiteouts, and that is a DIRECTLY MEASURABLE
      hypothesis: compare whiteouts-per-loss before and after.
      Money is not the blocker -- the Dewford arc alone has 4,924 PokeDollars on foot that
      the bot currently walks past (19-TEAM-BUILDING-DISCUSSION.md 8.2), and the Lilycove
      Dept Store 2F sells up to MAX POTION + Revive (Aqua-hideout recon 2026-07-26). NOT urgent
      (the fight→train→retry loop carries the mid-game) — required before the E4.
- [ ] #24-grasswander - ORGANIC MOVEMENT WHILE TRAINING (user request 2026-07-26).
      Today the bot trains by SPINNING IN PLACE - `spin()`
      (`modules/modes/util/higher_level_actions.py:158`) turns on the spot, wrapped by
      `_story_spin` (`early_game.py:124`) for the whiteout-abort and no-progress watchdog.
      The user wants it to WANDER the grass with human-like movement, mixing in occasional
      spins, so training looks organic instead of robotic.
      !! THIS IS THE SAFE PLACE TO PUT RANDOM MOVEMENT, and the risk profile is INVERTED
      versus travel meandering (#24-meander):
        * On a TRAVEL leg, extra steps mean more wild encounters, which means more battles,
          more damage and more whiteouts. Our dominant failure is travel attrition, so
          meandering there is actively dangerous.
        * While TRAINING, extra steps mean more encounters - which is the entire POINT.
          Wandering costs nothing we did not already want.
      SEAM ALREADY PROVEN: `run_in_circle` (`modules/modes/util/walking.py:706`) shows
      `follow_waypoints` accepts an ARBITRARY waypoint generator. A bounded random-walk
      generator drops straight into that seam - no pathfinder change at all.
      MUST PRESERVE (all three already exist and all three have scar tissue behind them):
        * the whiteout abort in `_story_spin`, or a mid-training whiteout spins forever;
        * the no-EXP-progress watchdog, which is what un-sticks a bot that wandered out of
          the grass - it already handles exactly this failure and must keep working;
        * the leftover-script clear, since an active script SUPPRESSES wild encounters.
      REAL RISKS to bound:
        * wandering OUT of the encounter region (watchdog catches it, but wasted frames);
        * wandering into a TRAINER SIGHT CONE next to the training patch - an unwanted,
          unfleeable battle;
        * hazard tiles - ledges (one-way, drops you out of the area) and Granite Cave B1F
          cracked floors. Confine the walk to a verified safe tile set, not "anywhere
          walkable".
      !! VERIFY FIRST, DO NOT ASSUME: does turning in place generate encounters at the same
      rate as stepping? If spinning is already step-equivalent, wandering is neutral on
      training speed and purely cosmetic; if stepping is faster, wandering is a genuine
      throughput WIN as well. Check `CheckForWildBattle` / the field state machine in the
      decomp before designing around either answer - this decides whether the feature pays
      for itself or merely looks nicer.
      Design sketch: a seeded bounded random walk over the region's MB_CAVE / tall-grass
      tiles, biased to stay near the centre, with occasional in-place spins and short
      pauses; region supplied by the caller (we already derive safe tile sets - see the
      Granite Cave work in `19-TEAM-BUILDING-DISCUSSION.md` 8.1).
- [ ] #24-items - GROUND + HIDDEN ITEM PICKUP (user request 2026-07-26). The bot walks
      past every item ball and every hidden item in the game. Two mechanisms, handled
      differently:
        (a) VISIBLE ITEM BALLS - real object events at a known tile; pickup is "navigate
            there, press A". The Ch14 recon alone found Carbos (Route121 55,10), Revive
            (60,10), Zinc (38,13), Max Potion (MtPyre Exterior 27,15), TM48 (19,40), Sea
            Incense, Lax Incense, TM30 - all on routes the bot already walks. The Aqua
            hideout holds a MASTER BALL (B1F 15,9) + Nugget, behind a solved warp path.
        (b) HIDDEN ITEMS - no object event; need the ITEMFINDER and a press on the exact
            tile. Requires the Itemfinder in the bag plus a per-map coordinate table from
            the decomp (`hiddenitem` script commands in data/maps/*/scripts.inc).
      !! SYNERGY, and the reason to build this alongside #24-provisions: many ground items
      ARE Potions and Revives, so pickup directly feeds the layer that breaks the
      loss->whiteout 1:1. Do (a) first: navigation + a press, reuses everything that exists.
      !! CORRECTED by later recon (22-CAPABILITY-RECON.md C1): PICKUPS ARE SAFE. Item balls
      (finditem/Std_FindItem) and hidden items both call checkitemspace FIRST; on a full bag
      the ball STAYS with its flag unset, so the pickup is simply retryable. No bag guard is
      needed for pickup logic.
      The strand vector is GIFT scenes only - giveitem/Std_ObtainItem calls additem with NO
      pre-check, sets VAR_RESULT=FALSE and prints nothing, and 38 sites never test it.
      Those are concentrated in KEY ITEMS (cap 30) and TM/HM (cap 64) - including EVERY HM
      (Cut, Flash, Strength, Rock Smash, Surf, Fly, Dive, Waterfall) and the Magma Emblem.
      The general Items pocket has NO unchecked story grant on the path, so stockpiling
      Potions cannot strand a run. Rule: keep KEY ITEMS and TM/HM headroom before gift scenes.
      !! The ITEMFINDER IS NOT REQUIRED to COLLECT a hidden item - only to detect one
      (field_control_avatar.c:346-353 checks the flag alone). The bot can harvest hidden
      items straight from a coordinate table without ever obtaining it.
      On-path healing already mapped: REVIVE at Route117 (9,1) and Route109 (16,23, hidden),
      MAX REVIVE at Petalburg (19,2), Hyper Potions on Route118/119, plus Rare Candies on
      Granite Cave B2F (29,4) and Route110 (26,47).
      Open: detour for items, or only collect what is on the existing path? Recommend
      on-path only first, then let the `curiosity` personality axis price the detour
      (19-TEAM-BUILDING-DISCUSSION.md 5).
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
- [ ] #24-hm-multi — TEACH AN HM TO ADDITIONAL APPLICABLE MONS (user 2026-07-23,
      future): after the primary teach, consider teaching the HM to OTHER party mons
      when it is a genuine upgrade over one of their current moves ("if they are
      present and if it is a higher priority over their current moves" — the user's
      framing). NOTE the research nuance before building: per the graded pokeprofiles
      registry, Rock Smash-class HMs are an HM TAX (weak move, undeletable without
      the Lilycove Move Deleter) — "applicable" must mean "the decision layer says
      it beats a current move" (#24-tms/#24-movelock), not merely "compatible", or
      we poison battlers' movesets. Strength (80BP) is the counter-example where
      multi-teach genuinely pays. Build after the TM decision layer exists.
- [ ] #24-flannery-grind (OBSERVATION, not a bug — 2026-07-23 milestone run): from the
      Lavaridge milestone (weak fixed team L29), Flannery took 3 boss-training whiteouts
      (L29→L32) before the win — grass-less gym + tanky Torkoal + optimistic sufficiency
      gate + team re-solves the trapdoor maze each retry (~22k frames/solve). Working as
      designed (reactive net ground out the win, 0 derails), but slow FROM A WEAK
      milestone team; a real fresh run arrives stronger. If it proves annoying later:
      a stronger prep floor for grass-less tanky-ace gyms, or full-team survivability
      in the sufficiency gate (consult flagged Torkoal's bulk+Sunny Day). Low priority.
- [ ] #24-rivalcap — `_rival_attempts` (story_mode.py §5c) increments on every _play
  re-entry, not on actual lost rival battles — a derail-y stretch near the rival can
  burn the 3-attempt budget without fighting once (seen on the goods_recovered thin-team
  save 2026-07-24). Key the counter on a genuine battle loss.
- [ ] #24-watertrain — WATER training tiles (user 2026-07-24): once Surf is obtained AND
      taught, surf encounters become a viable training band (level + typing permitting).
      Extend training_areas with water tiles + a "needs surf" prereq (the AREA_PREREQ
      mechanism already exists) and teach the picker to consider them.
- [ ] #24-healverify — re-verify the Surf-gated heal-centre pairings (Routes 115/118/119/121)
      from a POST-Surf checkpoint; repro_fodder_grass.py currently marks them PENDING because
      no pre-Surf save can path a water route. Route 119 (21,109) reached NO Poké Center.

## Done
- [x] **#24-movelearn-recovery — DONE 2026-07-25. The #1 open item; killed 2 of 5
      cold-start runs (~f1.55M each).** ‼ The filed diagnosis ("the recovery scope is
      the bug, not the move-learn logic") was only the LAST of four links — fixing just
      it would have produced a dead run with a nicer log line. Real chain, from the
      captures `saves/movelearn_hmwedge_{quickattack,slash}.ss1`: Combusken carries
      Rock Smash (an HM **and** its weakest move); a stray A from the "unrecognised
      text" branch answered YES to a prompt the bot had decided to DECLINE; a cursor
      read while the summary screen was still animating in was stale, so A landed on the
      HM slot; the game replied with `Task_HandleInputCantForgetHMsMoves`, **a symbol
      nothing in the codebase referenced**, misreported as the Yes/No; and the handler
      then sat in an UNBOUNDED "screen still opening" branch pressing **nothing for
      6,000 frames**. Fixed: `LearnMoveState.CantForgetHM` checked first; a branch that
      dismisses the refusal AND strikes the refused slot off; no A on an untrusted
      cursor; the wait bounded; and `modules/battle_fault.py` — an OPT-IN channel
      (`handles_battle_faults`) that carries a battle fault to the mode instead of
      raising across the controller stack, so it costs one DERAIL. A/B: WEDGED at
      f23,400 → RESOLVED at f258 / f224, movesets correctly unchanged; stock modes
      verified unchanged. Repros: `repro_movelearn_hm_wedge.py`,
      `repro_movelearn_fault_recovery.py` (3 arms).
- [x] **#24-fortreebadge — SATISFIED 2026-07-25: BADGE 6 WON from a cold start.** Filed
      2026-07-24 when the isolated Fortree drive lost to Winona and whited out — it called
      `do_fortree_gym()` directly with whatever party the save carried, and battle prep
      (lead selection + heal) is the CALLER's job. Confirmed the right way, by a full
      run rather than a gate fix: a fresh title-screen run reached the **Feather Badge =
      end of built content** (38 maps, ~2.48M frames, 0 derails).
- [x] **#24-fortreegates — DONE 2026-07-24: the Fortree Gym rotating-gate puzzle is
      solved LIVE.** `modules/story/fortree_gates.py` is a port of the decomp's
      `src/rotating_gate.c`, validated **4/4** against the emulator. Includes the
      parked-trainer escape: a trainer standing on the path is cleared by RESETTING the
      room (exit + re-enter forces the documented gate reset), not by waiting.
- [x] **#24-harness-savepath — DONE 2026-07-25: stall snapshots are per-run AND
      per-stall.** Two defects in one line. (a) The no-progress auto-save wrote a single
      shared `saves/midstuck.ss1`, so concurrent runs overwrote each other and the
      artifact belonged to no particular failure — that is precisely why the move-learn
      stall had no clean repro, and why one earlier investigation burned effort on a
      `midstuck.ss1` that was a whiteout state from a different map. (b) It fired ONCE
      per run, but a run usually stalls several times and the first stall is typically a
      recoverable hiccup — the interesting capture was the one never taken. Snapshots now
      land in `tools/story-dev/saves/stalls/`, which unblocked `#24-movelearn-recovery`.
- [x] **#24-harness-finish — DONE 2026-07-25: a SUCCESSFUL run no longer reports as a
      hang.** The first cold-start Badge 6 run reached the end of built content at
      f2,483,319, printed "end of built content — handing to manual", and then correctly
      stopped doing anything — so the harness's frame-based no-progress detector fired
      20,000 frames later and the log ended `HANG CONFIRMED`. `compare_runs.py` inherited
      the false signal and classified it `no-path` (a transient, recovered "Could not find
      a path" earlier in the log). The one run that worked looked like the worst kind of
      failure. Both tools now check the bot's own end-of-content message before calling a
      stop a hang.
- [x] #1 â€” Vendor upstream 40Cakes/pokebot-gen3 (subtree @ 5dd898f8) (2026-07-17).
- [x] #2 â€” Deep documentation pass + Pokemon_Emerald_AI_Notes.md (2026-07-17).
- [x] #4 â€” install.py V2 (setup/update/heal + ROM handling) â€” "worked!" (2026-07-18).
- [x] #5 â€” Native dashboard GUI + handheld mode â€” "worked!" (2026-07-18).
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

- [x] #24-evo-trainstall (FIXED 2026-07-22: interrupt-safe _rotate_lead_safely + _yield_bounded; proven on evostall.ss1; same fix covers the user's 110k-frame Joey stall) â€” `train_team`/`_story_spin` can hang right AFTER a
      trainee EVOLVES mid-training (batch run02 2026-07-22: Grovyle evolved +
      learned Fury Cutter on Route 116, then the spin never resumed â†’ 20k-frame
      HANG). Repro save: tools/story-dev/saves/evostall.ss1. Likely the
      post-evolution return-to-overworld transition isn''t ridden out before the
      next spin action (cf. the move-learn / dock-arrival family). Prove + fix.
- [x] #24-pokenav-faithful (RESOLVED 2026-07-22: the user ran VIDEO OFF — the renderer-gated fallback fired exactly as designed; keep video off on the weaker test PC, the fallback covers it) — WATCH ITEM (user fresh-run log 2026-07-22 13:24): the
      PokéNav Match-Call tutorial took the STATE-WRITE FALLBACK on a real-GUI run
      (video on) — the faithful play-through previously worked on this hardware.
      By design the fallback is legal (never hang), but check why the faithful
      path didn''t engage (timing? renderer-gate read?) next time it recurs.
- [x] #24-wattson-strength — DONE 2026-07-22 (KI-13 resolved): 0-power move-learn
      guard + Segment 9c prep (Route 117 (31,16) band 20-24) + aftermath-quiet
      riding → run 14 beat Wattson end-to-end; `wattson_done.ss1` verified.
      Residual (folded into #24-movelock): audit the evolution-scene learn flow
      that dropped Marshtomp''s Mud Shot at L16 (moot for Wattson, still a
      move-quality gap).


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

### #24-endlessruns — ENDLESS DEBUG-RESET RUNS (user request, 2026-07-25)

**CLI form: DONE** — `tools/story-dev/endless_runs.py`, smoke-tested.
```
py -3.12 tools/story-dev/endless_runs.py                 # 10 runs, treecko
py -3.12 tools/story-dev/endless_runs.py --count 0       # INFINITE (Ctrl-C)
py -3.12 tools/story-dev/endless_runs.py --count 25 --starters all
```
Back-to-back FRESH runs, unthrottled, debug logging on, appending one row per run to
`tools/story-dev/endless-runs/LEDGER.md` (depth reached · outcome · frames · wall-clock · log).

**Failsafes — each exists because of a failure actually observed 2026-07-24/25:**
* `--run-timeout` (wall clock, default 5400s): the harness's watchdogs are FRAME-based, so a
  wedged emulator process advances no counter and fires nothing. Only an external wall-clock
  bound catches that.
* `--stall-timeout` (default 600s): kills a run whose LOG STOPS GROWING. A run can burn frames
  forever while making zero progress — the 2,000,000-frame fodder grind looked alive throughout.
* **A fresh profile per run, metadata COPIED from a template.** "FRESH boot from title" still
  loads the profile's battery save, which once produced three worthless runs that reported as
  fresh while starting in Fortree with a L39 party. ‼ metadata.yml must be COPIED, not
  synthesised — it carries the ROM reference, and a hand-written one makes every run die
  instantly with "Could not find ROM ``".
* **One bad run never aborts the batch** — every outcome is recorded and the loop continues.
* **Zero frames is never reported as success.** The first cut scraped a 5-second ROM-not-found
  death as `clean-finish`; an overnight batch of those would have read as green.

**`#24-endlessruns-gui` — DONE 2026-07-25, and it shipped as something better than the plan
above.** The plan was a menu item that shells out to this CLI module. That was built first and
FAILED in the user's hands: the dialogs appeared and nothing happened, because "endless debug
reset runs" means *this emulator*, not a separate headless harness.

So it shipped instead as **a real in-process bot mode: `Story (ENDLESS RESET)`**
(`StoryEndlessResetMode`, `plugins/custom_modes/story_mode.py`) — it simply loops
`Story (DEBUG - RESET)`'s `run()`, so every iteration is a hard reset → forced NEW GAME → play,
back to back in the running emulator. In BOTH builds. Count comes from the GUI's
"Endless Debug-Reset Runs…" item (`ENDLESS_RESET_TARGET`, default 10, `0` = forever).

In-process failsafes beyond the CLI's: a `BotModeError` in run 3 is SWALLOWED so runs 4..N still
happen; a hard 3.5M-frame-per-run cap (StoryMode's own watchdog can't catch a wedged watchdog);
the bot mode is re-asserted after every run because a derail can call `set_manual_mode()`; and
the batch's emulation speed + video settings are captured once and restored each run — the first
cut restored `bot_mode` but not the speed, so run 1 ran unthrottled and every run after it
crawled at 1× (user-reported, fixed in `aadad944`).

The CLI form above is NOT superseded — it keeps the fresh-profile-per-run and wall-clock/log-growth
failsafes that an in-process mode cannot have, and remains the right tool for a scripted batch.
