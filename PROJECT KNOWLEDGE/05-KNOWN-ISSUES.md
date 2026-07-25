# Known Issues — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Open problems only — when an issue is
> fixed, remove it here and record the fix in 07-CHANGELOG.md.
> Entry format below; KI numbers never get reused.

<!--
## KI-1 — <short title>   (opened YYYY-MM-DD, severity: high/med/low)
- **Symptom:** what goes wrong
- **Repro:** how to trigger it
- **Suspected cause:** best current theory
- **Workaround:** if any
-->

These are UPSTREAM bugs in pokebot-gen3 (found during the 2026-07-17 doc
verification pass). They exist identically in `40cakes repo/pokebot-gen3/`
(pristine — do not fix there) and `custom-pokebot/` (fix candidates; any
fix goes in DIVERGENCE-LOG).

## KI-1 — Upstream pokebot.spec (PyInstaller) is stale/broken   (opened 2026-07-17, severity: low)
- **Symptom:** `pokebot.spec` references `import.py` (file doesn't exist in
  the repo) and a repo-root `sprites/` dir (sprites actually live at
  `modules/web/static/sprites/`); a PyInstaller build would fail as-is.
- **Repro:** `pyinstaller pokebot.spec`.
- **Suspected cause:** spec never updated after upstream restructures;
  upstream releases are source ZIPs, so the spec is unexercised.
- **Workaround:** run from source (our normal path). Relevant to punch-list
  #4 only if we ever want packaged builds.

## KI-2 — Upstream `BattleStateSide.modified_stats()` raises TypeError   (opened 2026-07-17, severity: low)
- **Symptom:** `modules/battle_state.py:590` builds its stage-multiplier
  table from set literals (`{10, 40}`), which can't be indexed — calling
  `modified_stats()` raises `TypeError`. Zero callers in the repo (dead
  code), so nothing breaks today.
- **Workaround:** use `stats_modifiers` (battle_state.py:587) and apply
  multipliers yourself. Must be fixed in custom-pokebot before any custom
  battle brain relies on it.

## KI-3 — Upstream stale docstring names nonexistent battle opt-out   (opened 2026-07-17, severity: low)
- **Symptom:** `modules/modes/_interface.py:62` docstring tells mode
  authors to call `self.disable_default_battle_handler()` — that method
  doesn't exist anywhere. The real mechanism is returning
  `BattleAction.CustomAction` from `on_battle_started()`.
- **Workaround:** documented in `40cakes repo/DOCUMENTATION/03`; keep in
  mind when writing custom modes.

## KI-4 — Cloud-sync requires backups enabled (opened 2026-07-19, severity: low)
- **Symptom:** If `backups enabled: false` but `sync.enabled: true`, every
  clean exit logs "sync FAILED (backup could not be created)" — cloud-sync
  is built on the backup system. Honest failure, NOT data corruption.
- **Workaround:** enable backups when using cloud-sync. Fix candidate: a
  config-validation warning at load.

## KI-5 — Background git calls could wait on a credential prompt (opened 2026-07-19, severity: low)
- **Symptom:** cloud-sync/update-check git fetch/push could block up to its
  timeout if a remote interactively prompts for credentials.
- **Mitigation in place:** all such calls are timeout-bounded on daemon
  threads, so startup is never blocked. Fix candidate: set
  `GIT_TERMINAL_PROMPT=0` in the subprocess env.

## KI-6 — Tab bar overcrowds with 6 tabs — RESOLVED 2026-07-19 (sandbox)
- **Symptom:** Adding the Hunt tab (#9) made 6 tabs overflow the ~360px
  tool-column width — labels overlapped/truncated.
- **Fix (done):** tab bar wraps to two balanced rows when there are >4 tabs
  (3+3 for six), legible in both desktop and the handheld drawer
  (screenshots ki6_1/ki6_2). Gamepad focus-nav + tab persist unaffected.

## KI-7 — fly_to() checks the wrong badge for Emerald — ✅ FIXED 2026-07-24 (sandbox)
- **Fix:** RSE branch now gates on BADGE06_GET (Feather Badge) — the stock BADGE03 check
  was FR/LG's. Fixed ahead of Ch14's first Fly usage; DIVERGENCE-LOG entry due at
  promotion (upstream-file edit).

## (old text) KI-7 — fly_to() checks the wrong badge for Emerald (opened 2026-07-19, severity: low)
- **Symptom:** `modules/modes/util/higher_level_actions.py` fly_to() gates on
  BADGE03_GET (Dynamo) — correct for FR/LG but WRONG for Emerald, where Fly
  needs the Feather Badge (BADGE06). Inherited from upstream. Story-mode #24
  must not rely on fly_to as-is; fix when wiring Fly into story navigation.

## KI-8 — Mid-battle rotation execution can stall the party-menu switch (opened 2026-07-21, severity: med)
- **Symptom:** a mid-battle switch (`TurnAction.RotateLead`) into a weak/underlevelled bench
  hung the in-battle PARTY_MENU (Roxanne with Torchic vs Rock + an L6-7 bench → stuck, then
  Manual). `state=3` = PARTY_MENU.
- **Where:** `modules/battle_action_selection.py` `case TurnAction.RotateLead` →
  `scroll_to_party_menu_index(map_battle_party_index(index))` → `while get_game_state() ==
  PARTY_MENU: press A`. If the target is mis-mapped or the party-menu submenu default isn't
  "SHIFT", the scroll loop (`menuing.py`) or the A-press loop spins.
- **Mitigation (done):** the Story bot's trainer-battle strategy now ATTACKS through and never
  proactively rotates in a trainer/gym/E4 battle (`LevelUpTravelBattleStrategy.decide_turn`) —
  so it sidesteps this path. Faints are handled reactively by the after-faint chooser (which
  correctly excludes fainted/active/double-partner mons).
- **Proven fix pattern now exists (2026-07-22):** the after-faint SIBLING of this exact
  blind `while PARTY_MENU: press A` loop deadlocked deterministically in Ch9 and was fixed
  with a STATE-AWARE sweep (read cursor slot + party HP + active task — including
  `Task_HandleSelectionMenuInput`, the real Emerald popup task — and press the one button
  that advances, with press/release gaps; see `handle_fainted_pokemon` in
  `battle_handler.py`). When KI-8 is reproduced, port that same sweep to the RotateLead
  path in `battle_action_selection.py`.
- **Still open (for Fable):** any strategy that DOES rotate (e.g. SwapTrain in an unexpected
  double/trainer case) is exposed. Reproduce a live rotation into a specific slot and pin
  `map_battle_party_index` / the party-menu submenu handling. Good first target: the Slateport
  **Gabby & Ty DOUBLE battle** (§Ch8) — it also validates the after-faint double-battle fix.

## KI-9 — Training spin could silently stall (no encounters) — MITIGATED 2026-07-21
- **Symptom:** during pre-gym / pre-rival training, the grind `spin()` could end up where it
  can't trigger wild encounters (walked out of grass, trainer line-of-sight, bad respawn spot)
  and walk in place FOREVER — the level never reaches target, the stop-condition never fires, no
  whiteout, no derail → hard stall (harness-repro'd from `route116team.ss1`: stuck at Marshtomp
  L16 with no EXP for 20k+ frames). Position/RNG-dependent (a clean fresh run trains fine).
- **Mitigation (done):** `_story_spin` now has a **no-progress watchdog** — if the party gains
  no EXP for `_STORY_SPIN_NO_PROGRESS_FRAMES` (2400) consecutive OVERWORLD frames, it bails so
  the caller (`train_team`'s loop) **re-navigates to the grass and retries**, which un-sticks it.
  Overworld-only counting means a long single battle can't false-trigger it. VALIDATED: the same
  `route116team` run that hung before now trains past L16, beats Roxanne, and reaches the rival
  prep with all fixes. Bounded by `train_team`'s outer guard (500) → derail recovery if truly stuck.

## KI-10 — Post-sail whiteout can respawn the run on the MAINLAND (Dewford arc) — MITIGATED 2026-07-22
- **Scenario:** the Emerald whiteout respawn point is the last Poké Center USED. After the first
  Briney sail (Ch6), Mr. Briney leaves his cottage (FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY) and waits
  at his BOAT: vanilla re-sails happen by talking to him on the Route 104 beach (his Route104
  object is un-hidden by the sail script) or at the Dewford dock (12,9). If the bot whites out on
  the Dewford side BEFORE ever healing at the Dewford PC, it respawns at Rustboro's PC — and
  `sail_to_dewford`'s cottage leg (Leg 3-4) would knock on an EMPTY house.
- **Mitigation (done):** `deliver_stevens_letter` heals at the Dewford PC FIRST when starting
  from town, so from the moment the Dewford arc begins, whiteouts respawn IN Dewford (the
  Segment-6 whitelist also stops any Dewford-side resume from re-running the sail). Remaining
  edge: a whiteout in the sail leg itself (route trainers) before the first Dewford heal — rare
  (the leg heals before the rival and fights little), but if hit, the run derails to Manual at
  the cottage instead of re-sailing.
- **Proper fix (when Ch8 needs re-sailing anyway):** teach the sail leg to talk to BOAT-Briney —
  if `HIDE_BRINEYS_HOUSE_MR_BRINEY` is set, engage his Route 104 beach object (live local_id via
  `_talk_to_wandering_npc`-style lookup) instead of entering the house.

## KI-11 — Oceanic Museum entrance grunt-sealed at Devon-goods time — ✅ RESOLVED 2026-07-22
**RESOLUTION:** NOT a state bug — a missing STORY STEP. The museum grunts clear when you talk
to **Dock at Stern's Shipyard** (`SlateportCity_SternsShipyard_1F_EventScript_Dock` runs
`setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA`). User-supplied + decomp-confirmed; built into
`deliver_devon_goods_to_stern` (Shipyard→Dock→museum). The doc was wrong (had the museum
freely enterable) — corrected in §Ch8b. This is the motivating case for the /validate-docs
process. Original write-up kept below for reference.

- **Symptom:** `deliver_devon_goods_to_stern` cannot reach the museum. The doors are city
  warps (30,26)/(31,26); the ONLY tiles below them, (30,27)/(31,27), are occupied by two
  Team Aqua grunts (obj id 18/5, `SlateportCity_EventScript_AquaGrunt2/1`). The whole
  y=27 row from x=22-31 is a grunt wall (gap at x=27, but (27,26) above it is collision).
  So the museum is physically SEALED — navigate_to (interior or door tile) plan-fails, and
  a walk-into-door bumps the grunt forever.
- **What's verified (probes 2026-07-22):** all 11 outside grunts share hide-flag
  `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` (882). It is UNSET by default (confirmed on an
  INDEPENDENT fresh game at Rustboro AND on slateport.ss1), `VAR_SLATEPORT_CITY_STATE=0`,
  and the SlateportCity map.json has NO coord-trigger near the museum to reposition them
  (its only coord_event is the Battle Tent Scott scene at (10,13)). The 2F Stern-fight
  grunts are SEPARATE 2F objects (id 2-4 spawned at the stairs), not this outside crowd.
- **The contradiction:** vanilla canon = the museum IS enterable on the first (Devon-goods)
  visit, yet structurally it's sealed with flag 882 unset. Something clears/repositions the
  crowd that our static read isn't capturing (a map ON_TRANSITION/ON_FRAME script setting a
  var, an event on the Slateport dock arrival, or the flag being set earlier than found).
- **DO NOT guess a state-write** (setting flag 882 hides the crowd, but proving that matches
  vanilla's exact state at this point needs the mechanism first — house rule).
- **Fastest ground truth = the USER:** on a real first Slateport visit, are Aqua grunts
  blocking the Oceanic Museum doors, or is the entrance clear? Then either build the faithful
  trigger or document the state-write. `deliver_devon_goods_to_stern` (interior logic sound)
  stays defined but UNWIRED; frontier honestly = Slateport arrival.

## KI-14 ✅ FIXED 2026-07-23 (same day) — teach flow stranded the START MENU open → travel wedge → Manual
The Ch10b teach itself WORKED (the new compat picker chose Grovyle L29 on a Treecko run
— validation of #24-hm-learner on a non-Mudkip start). The failure is AFTER: the
teach's "hard menus-closed guarantee" B-mashes out of the BAG but its exit condition is
`game_state == OVERWORLD` — which is ALREADY true while the START MENU is open (the
start menu is an overworld state), so the loop exits with the menu still up
(`Task_ShowStartMenu` active, controllable=False). Then the Fallarbor travel wedges:
`wait_until_truly_controllable` presses nothing by design, and `_wait_until_cutscene_over`
— since the 2026-07-23 museum fix — only presses when a script is active or a text
printer waits, and an open MENU is neither → nobody ever closes the menu → 8000-frame
"cutscene did not end" derail → recovery hits the same wall → Manual at Mauville (32,15).
CLASS: a latent bug (menu left open, previously papered over by blind B-mash recovery)
EXPOSED by the museum fix making the presser conservative. FIXED (both halves, same
day): (a) the teach's hard-close loop breaks only when the overworld is MENU-FREE
(`_menu_task_active()` — Task_ShowStartMenu/ListMenuDummyTask/ChooseMonInput — plus
avatar controllable); (b) `_wait_until_cutscene_over` also presses B while a menu task
is open (B closes menus, can never start a dialogue → museum guarantee preserved).
PROVEN: story run rocksmash_got.ss1 → teach → Mauville → Rt 111 → 112 → Fiery Path →
Rt 113, 0 derails (ki14_run1); museum repro re-run clean.

## KI-15 (2026-07-23) — post-battle STORY-RESUME hang ✅ FIXED 2026-07-24 (pending batch validation)
**FIXED via three complementary changes, each proven on a captured state** (changelog
2026-07-23 "KI-15 FIXED" has the full detail; 08-MISTAKES 2026-07-24 has the two lessons
from failed intermediate designs):
1. `navigate_to` no-progress bail → `NavigationStuckError` after ~8 progress-free re-paths
   (walking.py; covers the ROUTE 104 `(5,6)↔(5,7)` oscillation; A/B: repro_navigate_stuck.py).
2. `_wait_until_cutscene_over` KEPT at its old museum-green behavior (parked waits = free;
   contract pinned by repro_cutscene_waiting_msg.py) — the wedge is reader-identical to a
   dialogue tail and both ignore B, so the rider cannot safely clear it (3 attempts failed).
3. The clearer: StoryMode run-loop nudge — waiting + no scripts + **position frozen** for
   240 frames → ONE A → 1200f cooldown. Only the wedge blocks movement, so only it matches.
   (A on the wedge clears it instantly — proven on `ki15_gotaway_wedge.ss1`; never
   A-mashes a live dialogue — `ki15_nurse_wedge.ss1` lesson.)
Faithful goods_recovered runs: previously-terminal wedge episodes now self-recover
(one 90k run crossed to Dewford/Granite Cave, 0 Manual). REMAINING: watch the overnight
fresh batches — if a lane still shows a 20k stall with `cb=ReturnFromBattleToOverworld`,
capture the state (probe_stuck_state.py / probe_press_variants.py are the tools) rather
than re-tuning thresholds blind.

### (superseded original diagnosis below, kept for the record)
## KI-15 (original) — post-battle STORY-RESUME hang after an inline battle ⚠ RE-DIAGNOSED 2026-07-23
> ‼ **The original write-up (an "after-faint PARTY_MENU chooser hang" with a 1-HP Wonder Guard
> Shedinja) was a MISDIAGNOSIS.** It was never supported by a log — `grep -r "SHEDINJA fainted"`
> across EVERY livetest run.log (current + archive) returns ZERO hits. The party/coords/stack
> cited (Marshtomp/Shedinja/Swellow/Poochyena/Ninjask at (7,9)) do not appear in any captured
> hang. A long repro session chasing the party-menu sweep (burn-injection, `faintrepro`) PROVED
> that sweep handles rapid back-to-back faints correctly (0 livelock over 5 successive faints).
> **Do NOT chase the party menu. The real bug is below.**

**Real symptom (from 3 CONFIRMED 20k-frame hangs — 002057/run05, archive/…-093125/run01,
archive/…-101814/run01).** After an INLINE battle (trainer or wild) fires during story
NAVIGATION or a scripted scene, the story flow fails to resume. All three share the same
post-battle stale reads: `state=OVERWORLD`, `cb=ReturnFromBattleToOverworld`,
`instr=BattleScript_PayDayMoneyAndPickUpItems`, `tasks=[]`, `bt='… gained … EXP'` / `'… won $…'`.
Two distinct manifestations observed:
  1. **Stuck cutscene-wait** (002057/run05, RUSTBORO, `return_devon_goods_and_get_pokenav`):
     `_wait_until_cutscene_over` rides forever. Its 8000-frame timeout RAISES, the caller's
     recovery retries, the retry re-hits the same state → raise/retry loop → 20k watchdog.
  2. **Navigator oscillation** (both archive hangs, ROUTE 104): after a trainer battle the
     player BOUNCES between two adjacent tiles `(5,6)↔(5,7)` — `navigate_to` re-paths back and
     forth and never advances.
**Frequency.** ~1/5 lanes; intermittent — needs a random battle to interrupt at a specific
navigation/scene moment. The HEALTHY version of the same scene rides fine.

**Why the existing phantom-script escape does NOT cover it** (`_wait_until_cutscene_over`,
early_game.py). The escape (added for the Route-111 Rock-Smash case) needs **600 CONSECUTIVE
`controllable=True` frames** while a script is active. Live trace of the real post-battle scene
(env `KI15_TRACE=<file>`, `story_harness.py goods_recovered.ss1 --driver story`) shows the
parked/multi-part state has `controllable` OSCILLATING (True for a stretch — phantom climbs to
~339 — then a long `controllable=False` stretch that RESETS phantom), so 600-consecutive is
never reached. NOTE the field-script `bytecode_pointer` DOES advance in the healthy multi-part
scene (so a naive "frozen-pointer" escape would need care not to fire on genuine long cutscenes).

**Repro status (2026-07-23).** Faithful `--driver story` runs from `goods_recovered.ss1` ride the
scene cleanly (no live permanent hang caught yet — the hang needs the rare battle-interrupt race).
Instrumentation is IN PLACE and env-gated (`KI15_TRACE`) inside `_wait_until_cutscene_over`
(reader profile + script pointers + escape/raise markers) — the tool to catch the live state next.
**NEXT STEPS (pick one; the fix is NOT to be guessed without catching the permanent state):**
  (a) Reproduce the ROUTE 104 `(5,6)↔(5,7)` navigator oscillation from a near-there save — the
      most concrete manifestation (2/3 hangs, identical tiles) — and fix the re-path bounce.
  (b) Catch the live cutscene-wait hang with `KI15_TRACE` set on a batch, capture the exact
      reader/pointer profile, and make `_wait_until_cutscene_over` escape it robustly (tolerate
      `controllable` oscillation; e.g. don't reset the parked counter on brief False blips, and
      turn the 8000 raise into a clean return when the state is the stale post-battle signature)
      WITHOUT false-firing on genuine long multi-part cutscenes (whose pointers advance).
Do NOT patch the battle handler for this — it is not a battle-handler bug.

## KI-16 ✅ FIXED 2026-07-23 (same day) — the wedge was _smash_rock returning before EventScript_SmashRock finished
**Symptom.** ALL 5 lanes resuming from `wattson_done.ss1` hang identically at frame f74383,
at Route 111 (18,99), in `travel_to_fallarbor` → `_enter_warp_by_navigation` (Fiery Path
south door) → navigate_to → follow_waypoints → ensure_facing_direction. A WILD BATTLE ends
right at (18,99) (`bt='MARSHTOMP gained 110 EXP'`), and the post-battle
ReturnFromBattleToOverworld transition leaves the avatar unable to move; the navigation
retry loops with no progress. NO safety net fires (not the story 18k watchdog, not the
follow_waypoints 20-frame timeout, not ensure_facing_direction) — the spin location is
elusive (bounding ensure_facing_direction / navigate_to did NOT catch it; reverted those).
**Scope.** SPECIFIC to the wattson_done save's state/RNG — FRESH runs pass travel_to_fallarbor
fine (Pass 1: 3/5 reached HEAT BADGE), and `rocksmash_taught.ss1` (a nearer post-Wattson
checkpoint) travels the same code cleanly end-to-end. So it is a NARROW post-battle navigator
robustness gap this particular save triggers, not a broad regression.
**REPRO (deterministic).** `story_harness.py wattson_done.ss1 --driver story --frames 120000`
→ HANG at f74383. Use it for a focused fix (the post-battle transition freeze class —
Bug 2 lineage; the real fix likely ensures the navigator waits for a truly-controllable
avatar after a mid-navigation battle, or prevents the wild encounter on that leg).
**WORKAROUND.** For milestone/continuing validation use `rocksmash_taught.ss1` (proven), not
wattson_done, until KI-16 is fixed. Consider regenerating wattson_done (may be a stale-state
artifact like the rocksmash_taught menu case).

## KI-17 (2026-07-24) — after-faint party-menu RESHOW freeze (severity: HIGH, 2/5 fresh lanes)
> ‼ This is the bug the original (later "re-diagnosed") KI-15 write-up was actually
> describing — the Shedinja/Ninjask/(7,9) party from that write-up appears verbatim in
> batch 20260724-004252/run04. It is REAL, distinct from the (fixed) KI-15 resume wedge,
> and now the top intermittent.
- **Symptom:** an inline wild battle where a mon faints opens the after-faint chooser;
  a replacement IS chosen (cursor on a living slot, action=1), and the game then freezes
  mid-transition back to battle: `state=PARTY_MENU`,
  `main_cb=CB2_SETUPRESHOWBATTLESCREENAFTERMENU`,
  tasks `Task_ReturnToChooseMonAfterText`+`Task_PrintAndWaitForText` (which never run —
  that CB2 doesn't pump tasks), `instr=BattleScript_FaintedMonTryChoose`. 20k-frame hang;
  `handle_fainted_pokemon`'s sweep presses A/B/Down to no effect (probed: the state is
  INPUT-IMMUNE, video on or off).
- **Evidence/states:** `saves/ki17_partymenu_wedge.ss1` (run05: Skitty 40HP alive,
  Taillow+Grovyle fainted) + `saves/ki17_partymenu_wedge2.ss1` (run04: the Shedinja
  party). ⚠ loaded states stay frozen — good repro material.
- **Suspected cause:** the ReshowBattleScreenAfterMenu state machine parks on one of its
  gfx-reload steps (or the savestate merely preserves a live race). NOT a renderer
  dependency (video=True doesn't advance it). Needs a decomp read of
  `CB2_SetUpReshowBattleScreenAfterMenu` / `gReshowState` — Gemini escalation drafted in
  `sandbox-pokebot/profiles/GEMINI-PROMPTS.md` (2026-07-24 entry).
- **Workaround:** none in-run yet; frequency ~2/5 fresh lanes at long horizons. The
  watchdog kills the run (no silent corruption). NEXT: decomp-verify what advances
  gReshowState; if it's waiting on a paletted/task resource our sweep's button timing
  starves, fix the sweep's press cadence; consider a bounded state-write fallback ONLY
  per the faithfulness rules (documented last resort).

## KI-18 — DOUBLE-battle replacement swap loops forever (user report, 2026-07-24) — HIGH

**Symptom.** In a double battle in Mauville Gym the bot reordered the party over and over —
Shedinja shuffling slot 0 ↔ slot 4 while Grovyle/Ninjask/Mightyena rotated — for ~23,000 frames,
`controllable=False`, until the mode dropped to Manual. A healthy **Beautifly L23 67/67** was
available the whole time and never came in.

**Evidence** (user log `7881406e-...20260724233227.log`):
```
party=['Grovyle L22 0/56', 'Ninjask L21 11/61', 'Mightyena L21 67/67',
       'Beautifly L23 67/67', 'Shedinja L20 1/1']
repeated [PARTY] slotN X -> Y reorderings, never resolving
stack: StoryMode._prepare_for_fight :1108 -> train_team early_game.py:1680 -> _story_spin
```
Grovyle is at **0 HP** (fainted), so this is the after-faint replacement path.

**HYPOTHESIS — NOT YET PROVEN.** A replacement picker written for SINGLE battles: in a double
battle TWO slots are already on the field, so the chosen mon can be one the party menu refuses
(already active / "NOT ABLE"), and the bot retries forever. Two existing comments in our own code
describe adjacent symptoms and should be read first:
* `story_mode.py:~185` — "rotating into a weak/underlevelled bench can HANG the in-battle
  party-menu switch (battle_action_selection.py — `while PARTY_MENU: press A`)" — the Roxanne hang.
* `story_mode.py:~1983` — "the party menu shows an incompatible mon as NOT ABLE and refuses the …"

Shedinja is a likely trigger: 1 max HP + Wonder Guard means one check can judge it unusable while
another still selects it.

**Do NOT patch on the hypothesis.** Reproduce first: force a double battle with a fainted lead
and Shedinja on the bench, and log (a) which function chooses the replacement, (b) what the party
menu reports for each slot, (c) which press sequence the swap driver issues. The single loop in
`battle_action_selection.py:132` (`while get_game_state() == GameState.PARTY_MENU`) is the prime
suspect for where it spins.

**Why HIGH:** it is a run-killer in a mandatory gym, and **Mossdeep gym 7 is a required DOUBLE
battle**, so this will block Ch15 as well as costing runs now.

## KI-19 — Route 111 training band was paired with a heal 2.2× farther than necessary (2026-07-24) — FIXED-PENDING-WIRING

`ROUTE111_OLD_LADYS_REST_STOP` (map `(18,1)`, door at ROUTE111 `(26,18)`) contains ONE NPC —
`Route111_OldLadysRestStop_EventScript_OldLady`, `flag_id=0` so always present and ungated — that
gives a **full HP + status + PP heal, repeatable**. PROVEN live: all four party members damaged to
1 HP with four different status conditions and spent PP, verified in memory, then fully restored;
repeated a second time with no change in behaviour. Static dump confirms **zero `bg_events`** — no
bed exists in that building.

**Distances from the Route 111 training tile (25,55):** rest stop **96 steps**, Fallarbor Poké
Center **213 steps**.

`training_areas.py` / `_training_area_heal_map()` currently pairs ROUTE111 with
`PokemonCenter.FallarborTown` because that was the only heal verifiable at the time. Re-pairing
needs a heal-at-NPC helper (the existing path is `heal_in_pokemon_center(PokemonCenter.X)`, which
assumes a Poké Center layout) — punch-list `#24-npcheal`.

## KI-20 — TRAPS confirmed against the decomp (2026-07-25) — read before building these systems

From `ai-research-notes/CLAUDE-VALIDATED-concepts-round2.md`. Each was verified by reading the
decomp, not recalled.

**‼ NEVER put an HM holder in the DAYCARE.** `ApplyDaycareExperience` calls
`DeleteFirstMoveAndGiveMoveToMon` with **no HM check and no prompt** — **move slot 1 is deleted
silently**. This is worse than the research note claimed (the note framed it as a normal
move-learn prompt). Any future daycare/training feature must refuse a mon holding an HM in slot 1,
and ideally refuse HM holders entirely. This is the single most destructive automated action found
so far: it strands a run with no error and no dialogue.

**`get_map_objects()` is not a room inventory.** `TrySpawnObjectEvents` only spawns objects inside
a CAMERA WINDOW, so the list is systematically incomplete just after a warp. `do_fortree_gym`
survives this only because it re-plans every tile; a comment now says so at the call site. Never
precompute a route from one object snapshot, and never read an empty list as "clear".

**Self-caught Pokémon NEVER disobey.** `IsMonDisobedient` (in `battle_util.c:3923`, *not*
battle_main.c) returns obedient before any badge logic unless `IsOtherTrainer(...)`. So the
"army" strategy needs **no** level cap; only in-game TRADES are capped (10/30/50/70).

**Encounter-rate corrections** (any XP-per-frame table built on the old numbers is wrong):
running shoes do **not** affect encounter rate at all — only the bike does (×0.8) — and the grass
rate constant is **20**, not 21. `Sweet Scent` bypasses Repel *and* the rate roll entirely
(flags=0) ⇒ a **guaranteed** encounter, which makes it the correct grinding primitive.

**Verified-correct, no action:** the Fortree "leave and re-enter resets it" recovery is right on
BOTH halves — gate orientations live on `VAR_TEMP_0..3` and are cleared twice over
(`ClearTempFieldEventData` plus `RotatingGate_InitPuzzle`), and NPC positions are restored by
`LoadObjEventTemplatesFromHeader` → `ResetObjectEvents`/`TrySpawnObjectEvents`. The user's reported
NPC-reset mechanic is real. Returning from a BATTLE is not a map load, which is precisely why the
parked-trainer case exists. Also verified: our `get_current_repel_level()` already reads the right
thing (`VAR_REPEL_STEP_COUNT`, first non-fainted non-egg member).

**Refuted:** the trainer AI does **not** switch on AI flags (no `AI_FLAG` references in
`battle_ai_switch_items.c`); real triggers are Perish Song / Wonder Guard / ability-absorbers /
Natural Cure, and it never switches while holding a super-effective move — so AI-baiting is less
reliable than the notes implied. Whiteout money is plainly `money / 2`
(`GetWhiteoutMoneyPenalty` does not exist). Shedinja does **not** need a spare Poké Ball, only a
free party slot.

## KI-21 — Decomp-verified facts that will otherwise cost the NEXT build phase (2026-07-25)

From `ai-research-notes/CLAUDE-VALIDATED-story-round1.md` (~65 claims ruled, every one citing a
fetched decomp file). These are the ones that would have produced mystery hangs.

**‼ 1. EVENT FLAGS ARE NOT ALL MONOTONIC — our resume gating assumes they are.**
`StoryMode._play` gates every segment on `_done("FLAG_NAME")`, which silently assumes a set flag
stays set. **It does not always.** Verified non-monotonic: `FLAG_DEFEATED_MAGMA_SPACE_CENTER` (the
rival's PokéNav call `clearflag`s it), the four Elite-Four member flags (wiped at the Hall of
Fame), the event legendaries, Shoal Cave (daily), the fan-club TM (weekly).
**New prevention rule: passing `audit_flag_names.py` proves a name is READABLE, not MONOTONIC.**
Any segment gated on one of those can re-run or be skipped wrongly. Audit the Ch14+ gates against
this list before building them. (Reassuring: `audit_flag_names.py` currently reports clean, so no
phantom name has leaked into shipped code.)

**‼ 2. FOUR OF EIGHT HMs ARE GIVEN BY A MAP-ENTRY `ON_FRAME_TABLE` TRIGGER, NOT BY TALKING.**
Surf, Strength and Dive fire on entering the map; **Fly is a coord trigger at ROUTE119 (25,31)/
(26,31) that starts `trainerbattle_no_intro` instantly.** Both Gemini generations said "talk to
NPC X" — **a bot that walks up and presses A waits forever.** Our code already handles the Fly
coord trigger (found the hard way in an earlier session), which is a good consistency check on
this ruling.

**‼ 3. A MANDATORY `multichoice` MENU LOOPS FOREVER ON THE WRONG ANSWER.**
`CaveOfOrigin_B1F`: **only index 2 ("Sky Pillar") advances.** Indices 0/1/3, the switch default
AND a B-press all `goto` back to the same prompt — **no counter, no timeout, no escape.** Three of
the four mandatory critical-path multichoice menus default to the WRONG option. All 49
`multichoice` sites were swept and the critical four tabled with correct indices — read that table
before building Ch14+, because this is a guaranteed hang otherwise, and it would look exactly like
the phantom-script wedges we already chased for days.

**4. HM07 Waterfall needs BOTH Maxie AND Archie** talked to at
`VAR_SOOTOPOLIS_CITY_STATE == 5` — the same state unlocks the Gym and every house door. Neither
note mentioned it. `VAR_SOOTOPOLIS_CITY_STATE` has **seven** states, not five; the complete
machine with every setter is in the validated file.

**5. "Missable" was largely invented.** Master Ball, TM Thief, TM Earthquake, the Magma Hideout
items, the unchosen fossil and the S.S. Tidal are **NOT** missable — building interrupts for them
is wasted work. What genuinely vanishes: **Aqua Hideout grunts at Badge 7**, **Magma grunts at the
Groudon cutscene**, and **each Trick House puzzle the moment it is cleared**.

**6. `src/field_move.c` does not exist** and ten cited C functions have zero hits. The real HM gate
is `party_menu.c:3725`. Treat any note's file path as a claim, not a location.

## KI-22 — Round-3 findings, incl. one that AMENDS an earlier "safe" rule (2026-07-25)

From `ai-research-notes/CLAUDE-VALIDATED-concepts-round3.md` (~50 claims, decomp-cited).

**‼ 1. AMENDS KI-20/round-1: "whiteout is the safe abort" is FALSE during the Elite Four.**
`DoWhiteOut` runs `EventScript_WhiteOut`, which is **not** a no-op: it clears **all four**
`FLAG_DEFEATED_ELITE_4_*` and resets `VAR_ELITE_4_STATE`. So a whiteout mid-gauntlet silently
un-does progress. Whiteout remains the safe abort for scripted legendary statics; it is NOT safe
during the E4. This compounds KI-21's non-monotonic-flag warning — the E4 flags are the clearest
example, and any Ch16 gating must not assume they stick.

**‼ 2. Timer Ball has a u8 overflow.** `u8 ballMultiplier = battleTurnCounter + 10` wraps at turn
246 to **0**, which bypasses the `> 40` clamp and feeds `odds = 0` into `16711680 / odds`. Never
throw a Timer Ball past ~turn 240 — relevant to any long legendary-catch loop, which is exactly
where a bot would rack up turns.

**3. Healing is a TABLE, not an inference** — `sHealLocations` has 22 entries, and `setrespawn`
lives in each Poké Center's **ON_TRANSITION**, so merely ENTERING the building moves the respawn
point. There are exactly **five** `Common_EventScript_OutOfCenterPartyHeal` sites, one of which is
**Route 111 Old Lady's Rest Stop** — now decomp-cited, vindicating the user against the first
Gemini round. This is what `#24-npcheal` should be built from.

**4. Dive needs TWO mechanisms.** Round 2 advised settling dive routes from `CONNECTION_DIVE`;
connections give 7 routes (not 4), but **`setdivewarp` is a separate script-level mechanism with
16 sites**, including Route 134 → the Sealed Chamber. A connection-only navigator would declare
the Sealed Chamber unreachable — i.e. round 2's own suggested method was incomplete.

**5. The impossible-without-event-data list (do NOT build hunts for these):** Mew, Deoxys, Lugia,
Ho-Oh, the Southern-Island Latias/Latios and the Soul Dew are unreachable, and **Jirachi does not
exist in Emerald at all** (zero scripts, zero encounter entries). All four event islands are closed
clusters (`connections: null`) with **no warp to them anywhere outside `LilycoveCity_Harbor`**. The
ticket-granting scripts ARE in the ROM but have **zero callers**, and
`ShouldDistributeEonTicket()` is commented `// Always returns FALSE`.

**6. An INJECTED Mew/Deoxys would disobey forever** at any level with all badges — the badge-8 and
own-OT escape hatches sit *inside* the block that gets skipped for non-fateful mons. Scripted
island legendaries use `seteventmon`, so they are fateful and obedient. (`IsMonDisobedient`,
`battle_util.c:3913`; `CalculatePlayerMonObedience` does not exist.)

**7. Mart inventories in the notes were the weakest data in either round** — six rows wrong
(Potion is not sold at every Mart; Hyper Potion/Revive not in Fallarbor; Full Heal not in
Mauville/Lavaridge; **Moomoo Milk is not purchasable anywhere**). All 19 prices were right. The
break-even for "walk to a free heal vs carry potions" is **¥14.0/HP before Fortree and ¥6.0/HP
after** — a flat ¥/HP model is off by 2.3×.
