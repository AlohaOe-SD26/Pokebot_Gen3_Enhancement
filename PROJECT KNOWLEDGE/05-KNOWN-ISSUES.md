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

## ‼ HOW TO READ THIS FILE (re-audited against code 2026-07-27)

**Only KI-1 … KI-5 are upstream bugs.** They exist identically in
`40cakes repo/pokebot-gen3/` (pristine — do not fix there) and in our forks (fix
candidates; any fix goes in DIVERGENCE-LOG). *The paragraph that used to sit here
claimed ALL entries were upstream bugs — it was written when the file held five, and
was wrong for the other eighteen.*

**Everything from KI-6 onward is OUR OWN story-bot / fork code**, and the active copy
is **`sandbox-pokebot/`** (not `custom-pokebot/`). KI-23/KI-24 concern
`modules/story/region_reach.py` and `modules/story/counter_plan.py`, which are ours and
have no upstream equivalent.

**Numbering:** IDs are **not contiguous** — there is no KI-12 and no KI-13 in this file.
23 distinct IDs across 25 headings (KI-1 and KI-15 each appear twice).

**Status re-audit 2026-07-27.** Every entry was checked against `sandbox-pokebot/`.
Entries proven fixed are now marked `✅ FIXED` in their heading with the fixing
`file:line`, and their superseded diagnostic bodies are collapsed under a
`<details>`-style "superseded" marker rather than deleted, because several were
proposing work that is already shipped:

| entry | why it was dangerous | proof of fix |
|---|---|---|
| KI-18 | body said *"Do NOT patch on the hypothesis. Reproduce first"* — it WAS proven and patched | `modules/battle_handler.py:475-501` (`_on_field` exclusion, KI-18-labelled) |
| KI-17 | body said *"Workaround: none in-run yet"* + prescribed a decomp read that is done | `modules/battle_handler.py:508-528` (`post_gap=24`; never gamble an A) |
| KI-16 | heading said FIXED, body still said *"use this repro for a focused fix"* | `modules/story/early_game.py:4434-4470` (`_rock_present()` world-judged) |
| KI-24 | body read as an open architectural bug; KI-24b already declares it fixed | `story_mode.py:553` and `:606` both call `region_reach.is_map_reachable` |
| KI-11 | body said `deliver_devon_goods_to_stern` stays **UNWIRED** — it is wired | `modules/story/early_game.py:3397-3412` (Shipyard → Dock leg) |
| KI-7 | a duplicate "(old text)" block restated the fixed bug as live | `modules/modes/util/higher_level_actions.py:59` (`BADGE06_GET`) |

**✅ RESOLVED — USER RULING 2026-07-29 (`#doc-policy-05`, option A):** entries fixed in
`sandbox-pokebot/` but not yet promoted to `custom-pokebot/` are **RETAINED here and marked
`✅ FIXED` with the fixing `file:line`**, because they are still open *for the production
copy* and deletion would lose the only promotion-owed signal. They are removed only once
promoted. This overrides the "remove it here" instruction in the file header above for the
sandbox-fixed case.

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

## KI-23 — Winona: the boss-attempt strategy cannot converge without a TYPE ANSWER (2026-07-25)

**Evidence: the user's overnight ENDLESS RESET session (2 runs) + my 5 cold-start runs.**

**Run 1 — 198 Winona attempt-messages, 41 losses, 41 whiteouts, NEVER won.** The last ~567,000
frames were spent entirely inside the Fortree gym sequence (the message never changed across 159
consecutive 3,600-frame heartbeat dumps), cycling: challenge → lose → whiteout → recover →
re-enter. Party at the end: **Sceptile L42, Loudred L39, Mightyena L36, Shedinja L29, Ninjask L28,
Zigzagoon L11.**

**Run 2 — 37 attempts, 32 losses, then WON** (`FortreeCity_Gym_EventScript_WinonaDefeated` +
`Common_EventScript_PlayGymBadgeFanfare` in the final dump; the log ends mid-fanfare). Party:
**Swampert L41**, Swellow L39, Vigoroth L32, Mightyena L18, Castform L26.

**Root cause — not levels, TYPES.** Winona is Swablu/Tropius/Pelipper/Skarmory/Altaria
(L29-33). Run 1's party at L42/L39/L36 was *far* above her levels and still lost 41 times,
because it had **no super-effective answer**: Sceptile (Grass) is resisted by Flying and shredded
by it; Ninjask (Bug/**Flying**) and Shedinja (Bug/Ghost, 1 HP) are worse; Loudred and Mightyena are
neutral. Nothing Electric, Rock or Ice — and Altaria is **4× weak to Ice**. Run 2 won not by
matchup either, but by brute-forcing with a bulky Swampert.

**So the boss-as-training-vehicle strategy has a failure mode we had not seen: it does not
converge when the team has no type answer.** It is not "slow" there — it is a genuine infinite
loop bounded only by the whiteout cap, and levelling further does not help. This is the same
economics as Norman (KI: 35 whiteouts) but worse, because Flying resists the common early types.

**What the fix needs (this is `#24-counters`, and it is exactly the user's stated goal of
"counters after failure and learning"):**
1. **Detect non-convergence** — N consecutive losses to the same boss with no downward trend in
   the boss's surviving mons means the plan is wrong, not under-levelled. Cheap signal: KOs
   scored per attempt is flat/zero.
2. **Then change the PLAN, not the level** — identify a type the boss is weak to, and go CATCH
   one. Against Winona: any Electric (Route 110 Voltorb/Magnemite, Mauville area) or an Ice move.
   `training_areas.py` already knows where species live; the missing piece is
   "what type do I need and where do I get it".
3. Keep the existing escalation for the case where the team DOES have an answer and is merely
   under-levelled — that path demonstrably works (my run1 won Badge 6 cold-start).

**Cross-run confirmation:** my 5 runs show the same shape elsewhere — 2 of 5 died on the whiteout
cap (`#24-whiteout`), and my successful run took 80 whiteouts. Attrition is not a side-effect; it
IS the dominant cost of the current strategy.

### STATUS 2026-07-30 — all three parts of "what the fix needs" are now BUILT (live validation owed)
1. **Detect non-convergence** — `_boss_plan_is_hopeless` (phase 1, 2026-07-25). DONE.
2. **Change the PLAN, not the level** — `counter_plan` names the target (phase 1) and
   `counter_hunt` + `StoryMode._counter_ladder` now TRAVEL, CATCH and TRAIN it (phase 2,
   2026-07-30). `repro_counter_hunt.py`, 15 checks, ALL PASS.
   ‼ The note above says "any Electric (Route 110 Voltorb/Magnemite, Mauville area)". The
   planner's own answer from the real Winona-era save is **Electrike @ ROUTE118 (29,15),
   L24-26, 30%** — a verified spin tile. Trust the planner's measured output over this
   prose; it reads the ROM's encounter tables and prices the grind.
3. **Keep the existing escalation** where the team DOES have an answer — untouched; the
   ladder only runs once `_boss_plan_is_hopeless` is already True.

‼ **STILL OPEN — this KI is NOT closed.** Nothing yet proves a run actually catches a
counter and converts it into a win; that needs a live batch. And the regression to watch for
is the mirror of the original bug: with a counter in the party `_boss_plan_is_hopeless` stops
firing, so a boss that used to stop honestly could LOOP instead. The per-run bound
(`_counter_hunts`, one hunt per boss per run) is what prevents it.

## KI-24 — `calculate_path` cannot prove LONG-RANGE reachability; our gates under-report it (2026-07-25)

**Found while validating the counter-catch planner.** From the correct Winona-era save
(`devon_scope_got.ss1`, verified: ROUTE120 (13,16), BADGE05_GET, `_party_can_surf()==True`),
`_training_area_allowed` reports **zero** reachable counters for Winona's types — including
Route 118 Electrike, which is the real answer to her.

**It is not a Surf gate and not an in-game obstacle.** The ROM's `MapConnections` give a genuine,
warp-free, edge-connected chain `ROUTE120 ↔ FORTREE_CITY ↔ ROUTE119 ↔ ROUTE118` — exactly what
`calculate_path` documents itself as supporting. Yet it fails on every hop, **and it also fails on
a same-map walk inside ROUTE119 alone** (y=5 → y=135, no map crossing at all). A same-map failure
rules out map-crossing as the cause.

**Most likely cause — already documented in this project.** Routes 118/119/120 are the
**dual-elevation bridge** maps: `calculate_path` reads those bridges as WALLS. That is precisely
why `_hold_walk_route()` (held-input walking) exists and why `_leave_route120_north_bridge` is
hand-written. A long north-south Route 119 path must cross them, so the planner declares it
impossible. (KI-20's camera-window `get_map_objects()` limitation may compound it, but the bridge
class alone explains a same-map failure.)

**Consequence — this is a REAL limitation in shipped gating, not just in the new planner.**
`_training_area_allowed` and therefore `best_training_area` use tile-level `calculate_path` as
their reachability oracle. On exactly the maps with the best mid-game training bands (115/118/119/
121) that oracle says "unreachable" for reasons that are artefacts of the pathfinder. The
conservative `allow=None` fallback is no better — it proposed **Magma Hideout Geodude** and
**Shoal Cave Spheal** as answers to a Fortree gym, i.e. across the region.

**The fix is architectural, and it is `#24-regionreach`:** reachability at REGION scale should be
answered from the **map-connection graph plus HM/badge gates**, not from tile-level pathing.
"Can I get to Route 118 from Fortree?" is a connectivity question; tile pathing is only correct
for the final leg once we are on the map. The ROM connection data is available and was
hand-verified during this investigation. Doing this would also retire the `AREA_PREREQ`
`"region"` hack that Route 111 currently needs.

**Prevention rule:** a reachability oracle must be sound for the SCALE it is asked about. Using a
tile pathfinder to answer a cross-region question inherits every one of its blind spots as a false
"no", and false negatives are invisible — nothing errors, the option is simply never proposed.

## KI-24b — region reachability BUILT; hop count alone is too coarse to rank by (2026-07-25)

`modules/story/region_reach.py` now answers reachability from the ROM's own `MapConnections` +
warps (never a hand-written table), with capability gates and — the point of the module —
`why_unreachable()` reasons that distinguish **"no connection path"** from **"needs Surf at
A↔B"** from **"reachable but N hops away (limit M)"**. The oracle itself is proven: ROUTE118 is
reachable from ROUTE120 at the Winona moment, where tile-level `calculate_path` said it was not.

**✅ SCOPE — KI-24 is now fixed for BOTH consumers (2026-07-25).** `region_reach` is wired into
`_counter_area_allowed` (counter-candidate selection, `counter_plan.find_counter_candidates`) AND,
as of 2026-07-25, into `_training_area_allowed` (training-area selection, passed as `allow=` to
`best_training_area`). Tile-level `calculate_path` no longer answers any region-scale question in
the story bot.

**The measured effect on the training predicate** (`repro_counter_plan.py`, same Winona-era live
position, same candidate list, ONLY the predicate changed):

| `_training_area_allowed` | reachable flags over the 10 Winona candidates |
|---|---|
| before (`calculate_path`) | `[False × 10]` — every candidate rejected; KI-24 in the raw |
| after (`region_reach`) | `[True × 5, False × 5]` — incl. **Route 118 Electrike: reachable** |

**How it landed, and the test bug it exposed.** The first attempt FAILED
`tools/story-dev/repro_fodder_grass.py` case 5 (`L31 team in Fallarbor`: expected `SKIP GRIND`,
got `RELOCATE to ROUTE111 L19-22`) and was reverted rather than forced. Investigating the failure
showed the TEST was wrong, not the change — see 08-MISTAKES 2026-07-25 (partial mock). `_stand_at()`
patched only `modules.map.get_map_data_for_current_position`, while the predicate's `calculate_path`
branch read `modules.player.get_player_location`, which stayed live. So case 5 had been asserting a
verdict for a position it never simulated — it was really asking about `(PETALBURG_CITY, (7,6))`.

Proof the re-baseline was a TEST fix and not a behaviour change: with `_stand_at()` repaired and
`story_mode.py` **untouched**, the ORIGINAL `calculate_path` code also answers
`RELOCATE to ROUTE111`, and cases 1-4 are unchanged. Three independent sources agree Route 111 is
reachable from Fallarbor — `calculate_path` succeeds from `(14,7)`, `region_reach` measures 2 hops,
and `training_areas.py`'s own comment says so.

**✅ The sibling repro that went red is fixed — `tools/story-dev/repro_counter_plan.py`.** Its
primary assertions never failed; what failed was a non-vacuity scaffold asserting that a
deliberately WIDE type set contained at least one `False`. **That scaffold was relying on the
bug** — it existed only because the Winona set was vacuously all-`False` under the pre-KI-24
predicate, and it inverted the moment the false negatives went away (the wide set now returns
`[True × 25]`). Per user ruling 2026-07-25 the non-vacuity check MOVED to where non-vacuity now
genuinely lives: the Winona set itself, asserted to span BOTH branches, which is the property the
sort proof actually needs. The wide set is still sorted as a larger-sample check.

This was the SECOND test in one day found to be asserting something that depended on a defect
(case 5 was the first) — see the 08-MISTAKES pattern entry for the shape and the prevention rule.

**‼ But the cost model I assumed is wrong, and the measurement says so.** Measured hops from
ROUTE120 on the Winona-era save:

| target | hops |
|---|---|
| FORTREE_CITY | 1 |
| ROUTE119 | 2 |
| **LILYCOVE_CITY** | **2** |
| **ROUTE118** (the real Winona answer) | **3** |
| MOSSDEEP_CITY | 4 |
| PACIFIDLOG_TOWN | 10 |

I expected "the answer is a handful of hops, the far cities are many". **Lilycove is CLOSER than
Route 118 by this metric**, and Mossdeep is one hop further. Because a single ROM connection can
span an entire sea route, uniform 1-hop weighting compresses "same landmass cluster" (1-4) and
only separates the genuinely far-flung (Pacifidlog, 10).

**So hop count is a usable FILTER but not a usable RANK.** `max_hops=4` cuts Pacifidlog-class
targets while keeping the Fortree/119/118 cluster, and that is how it should be used — as a
sanity bound, with `counter_plan`'s existing criteria (type coverage → verified tile →
encounter rate → level fit) doing the actual ranking.

**Next, if finer granularity is ever needed (`#24-edgecost`):** weight each edge by the source
map's traversal length rather than a flat 1, or price travel in FRAMES so it composes with
`training_areas.estimate_frames_to_level`. Both are real work; neither is needed until hop
count demonstrably mis-ranks something.

**Also still open:** `KNOWN_GATES` holds only THREE hand-verified edges (`region_reach.py:81-91`) —
DEWFORD_TOWN↔ROUTE106 and DEWFORD_TOWN↔ROUTE107 (both `surf`), plus EVER_GRANDE_CITY↔VICTORY_ROAD_1F
(`waterfall`, added 2026-07-26 because Victory Road's L38-42 Hariyama otherwise ranked #1 as a
counter candidate). *(This line said "only one entry" until re-counted 2026-07-27.)* So
edges whose requirement cannot be derived from ROM data currently read as UNGATED — i.e. this
oracle now fails OPEN where the old one failed CLOSED. That is the safer direction for a
*planner* (a wrong "yes" costs a wasted walk that navigation will fail recoverably; a wrong "no"
is invisible) but it must be grown before this gates anything irreversible.

**Prevention rule:** when you introduce a cost metric, MEASURE it against known-good and
known-bad cases before trusting it to rank. "Reachable" was a boolean that hid a cost; "hops" is
a cost that hides map size. Each fix exposed the next assumption — check the numbers, don't
reason about them.

---

# Added 2026-07-27 — open issues found by a code audit, previously unlisted

## KI-25 — `_lead_best_matchup` is purely DEFENSIVE; it benches the only mon that can win (opened 2026-07-27, severity: HIGH)
- **Symptom:** before a type-countered fight the bot leads a mon that merely *survives* the
  foe's STAB, regardless of whether it can deal damage. Measured in bundle
  `20260726-231412`: P2 led **Whismur L15** into the Route 110 rival **13 times in one run**
  while **Marshtomp L24** sat in slot 2. P3 led Zigzagoon L16 with Grovyle L22 benched.
- **Cause (exact line):** `modules/story/early_game.py:1587`
  ```python
  best = min(slots, key=lambda i: (_incoming(party[i]), -party[i].level))
  ```
  `_incoming()` (`:1566-1583`) returns only the foe's worst-case STAB multiplier *against*
  the candidate. Nothing in the key considers the candidate's offence. The only capability
  filter, `_battler_slots()` (`:1651-1659`), requires merely *any* move with
  `base_power > 0` — not one that can hurt **this** foe.
- **‼ Live consequence — the Flannery segment does not do what its own comment says.**
  `plugins/custom_modes/story_mode.py:2519-2531`: the comment states the plan is *"a WATER
  lead (all four of her mons are 2x to Water)"*, but the call is
  `_lead_best_matchup(["Fire"])`, which ranks by *resisting* Fire. Water, Fire, Rock and
  Dragon all resist Fire equally (0.5×) and the tie-break is `-level` — so a higher-level
  Combusken/Numel leads instead of the Water mon the comment asks for.
- **Also:** a 1-HP Wonder Guard Shedinja scores `0.0` incoming vs Norman (Normal→Ghost) and
  is therefore *chosen*, then dies to Slaking's Faint Attack (Dark) — the model reads only
  the ace's STAB types, never movepools. Observed in P4, bundle `20260726-231412`.
- **NOT the old `train_team` lead-restore bug** (fixed 2026-07-26, repro still green): the
  matchup call runs *afterwards* and overrides the restore.
- **Workaround:** none. Design options and the tradeoffs are in `03-PUNCH-LIST.md`
  `#24-leadpolicy` — **needs a user ruling**, since benching a 4×-weak mon is sometimes
  exactly right.

## KI-26 — the Route 110 rival has no attempt cap and no fight prep (opened 2026-07-27, severity: HIGH)
- **Symptom:** repeated identical losses at ROUTE 110 (34,56) with no adaptation. The code's
  own note records the worst case: `plugins/custom_modes/story_mode.py:744` — *"Measured
  worst case before this existed: 25 whiteouts on ROUTE110 in a single run."*
- **Cause:** Segment 9a (`story_mode.py:2335-2363`) is only
  `heal_in_pokemon_center` → `_lead_best_matchup([ace_type])` →
  `travel_route110_and_fight_rival()` → `_guard(...)`. **No `_prepare_for_fight`, no
  `train_team`, no attempt counter.** Every other combat segment has prep: Roxanne `:2122`,
  Brawly `:2279`, Wattson `:2377-2395`, Norman `:2581`, Winona `:2707`, and the Rustboro
  rival `:2177-2225` additionally has an escalating level floor and `RIVAL_MAX_ATTEMPTS = 3`.
  Route 110 and Wally (`:2366`) are the only combat segments without.
- **The only thing bounding it today** is `SURVIVAL_WHITEOUT_THRESHOLD = 3` (`:745`), which
  is a *wild-battle flee* heuristic, not a rival-attempt cap.
- **‼ Do NOT just add a cap.** In bundle `20260726-231412`, P2 lost there **13 times and
  then went on to reach Fortree** — a cap at 6 would have killed a recovering run. Adding
  prep needs a Route 110 training-grass tile, which is a game fact to probe or read from the
  decomp, never recall. See `03-PUNCH-LIST.md` `#24-route110cap`.

## KI-27 — hard hang at the Weather Institute, with the global watchdog itself wedged (opened 2026-07-27, severity: HIGH)
- **Symptom:** bundle `20260727-063751`, P3 run 1: `state=3 controllable=False`, position
  frozen at **ROUTE 119(32,1) (10,10)**, for **27 million frames / ~6.5 h** — and **not one
  STUCK dump fired in that entire stretch**, so the no-progress watchdog never saw it.
- **Last known stack:** `do_weather_institute` → `_ride_out_all_scenes`
  (`modules/story/early_game.py:5548`).
- **Partially mitigated 2026-07-27:** `_run_with_frame_budget()` now bounds the *run*
  (`story_mode.py:2866`), so the lane derails and the batch continues. **This truncates the
  symptom; it does not fix the hang, and it does not explain why the watchdog was silent.**
- **Next step:** wait for a post-fix batch to see whether it recurs and how often before
  spending time on it. Tracked as `#24-weatherinstitute-hang`.

## KI-28 — training LIVELOCKS that no progress detector can catch (opened 2026-07-27, severity: MED)
- **Symptom:** a run spins/heals indefinitely without reaching its level floor. Bundle
  `20260727-063751`: P1 run 7 = **19.9M frames** on Route 103 + Oldale heals; P2 run 35 =
  **13.4M frames** on Route 116.
- **Why KI-9's watchdog cannot help:** these produce real encounters, real battles and real
  healing trips — they are *busy*, just not progressing. A "nothing happened for N frames"
  detector is blind to them by construction. Only a resource budget catches them.
- **Contributing cause:** the training target is pursued regardless of whether local wilds
  can deliver it. Route 103's wilds are L2-3; Route 116's are L6-7.
- **Mitigated 2026-07-27** by the per-run frame budget (bounds the waste to one run).
  **Not fixed:** a target the local grass cannot deliver should be detected and abandoned.
  Tracked as `#24-grindconverge`.

## KI-29 — P4 broke the 1:1 losses:whiteouts canary twice (opened 2026-07-27, severity: LOW — watch item)
- **Symptom:** bundle `20260727-063751`, lane P4: run 1 logged **39 whiteouts vs 38 losses**,
  and run 8's sequence *opens* with a whiteout before any loss (`WLW`). Across three bundles
  the ratio had been exactly 1:1 in every other lane (no potion layer exists, so every loss
  becomes exactly one whiteout).
- **Most likely cause:** a whiteout event crossing a run boundary rather than poison damage —
  2 events out of 52. The per-run reset added 2026-07-27 (`reset_per_run_state`, which clears
  `_whiteout_pending`) may already cover it.
- **Action:** RE-CHECK on the first post-fix batch before investigating. Do not chase yet.

## KI-30 — a duplicate `Stone` badge is recorded on run 1 of every batch (opened 2026-07-29, severity: LOW)
- **Symptom:** in the newest bundle (`20260729-062040`), after correctly segmenting the
  cumulative badge log by batch, **run 1 of ALL FOUR lanes** shows `['Stone','Stone',
  'Knuckle', …]`. Every other run in every lane is clean — correct order, no duplicates, no
  gaps. It is exactly one extra `Stone`, only ever on run 1.
- **Cause: HYPOTHESISED, NOT PROVEN.** Most likely the batch-start boundary: at process
  start the emulator still holds the PREVIOUS session's save (Stone already earned) and the
  poll records it before the hard reset wipes the flags. `reset_for_new_run`'s adjacent-race
  branch (`badge_log.py`) makes the mode ADOPT main.py's boundary rather than count a second
  one, which is correct for the index but does not stop a pre-reset poll from recording.
- **‼ Do not fix on this hypothesis.** It has not been reproduced. The repro would be:
  start a batch from a profile whose save already holds BADGE01, and assert no badge is
  recorded before the first `[MAP]` of the new game.
- **Impact:** inflates run 1's badge count by one in every batch. It does not affect run
  grouping, gym order, or any other run. Harmless to the bot; misleading to an analyst.
- **Related:** the analysis-method trap that made this *look* far worse than it is —
  `run_index` restarts per process, so grouping a cumulative badge log by index across days
  merges batches. See `14-AGENT-PLAYBOOK.md` §2c.

## KI-31 — the fodder-grass gate compares the WRONG TWO QUANTITIES (opened 2026-07-29, severity: MED)
- **Symptom (user report 2026-07-29):** the bot trains in grass next to the objective even
  when those wilds are far below the team — "severely below level 5" — so XP per battle is
  near worthless. Norman is the 5th gym but sits in the STARTING region, which makes it the
  sharpest case.
- **Cause.** `_prepare_for_fight` relocates only when
  `local_max + FODDER_LEVEL_GAP < team_max_now` (`story_mode.py:1420`, `FODDER_LEVEL_GAP = 12`
  at `:715`). That compares the **wild** level to the **team** level — but the project's own
  measured model says XP per battle does not depend on the team at all:
  `xp_per_battle = 50.2 × wild_level / 7` (`training_areas.py`, calibrated against a real
  83-event probe). **XP is proportional to the WILD level, full stop.**
- **Measured cost** (real `TRAINING_GRASS` bands, team standing on Route 102 L3-5):

  | team level | relocates? | xp/battle here | best reachable band | speedup forgone |
  |---|---|---|---|---|
  | 10 | no | 35.9 | 8 | 1.6× |
  | 15 | **no** | 35.9 | 14 | **2.8×** |
  | 20 | yes | 35.9 | 22 | 4.4× |
  | 25+ | yes | 35.9 | 28 | 5.6× |

  The failure window is **teams at or below L17** — the gate needs `local_max + 12 <
  team_max`, so with L5 wilds it is False *at* 17 and first fires at **L18**. (Stated as
  "below 17" in the first draft; a repro assertion caught the off-by-one.) From L18 up it
  works correctly.
- **‼ DO NOT "just fix" THE CONSTANT.** The conservatism is DELIBERATE.
  `tools/story-dev/repro_fodder_grass.py` states it: *"WATTSON / ROXANNE / an early team ->
  UNCHANGED 'train locally' (the whole point of the conservative gap: proven-good prep must
  not move)"*. Teams at L10-17 are exactly Roxanne/Brawly/Wattson, so any fix moves prep that
  currently works.
- **‼ AND THE GOVERNING TEST CANNOT RUN ON THE DEV BOX.** `repro_fodder_grass.py` loads a real
  ROM + `saves/norman_done.ss1` and needs `mgba`. It is one of the 5 environmental failures
  here. **This change must be validated on the machine that runs the batches.**
- **‼ STATUS UPDATE 2026-07-29 (later): `xp_rate` IS NOW THE DEFAULT (user directive).**
  The user launches the bot by **double-clicking `install_sandbox.py`**, which cannot set an
  environment variable — so an env-var-only switch meant the intended rule never actually ran.
  Requiring a shell to get the intended behaviour is a broken interface, so the default was
  flipped. Every launch path (double-click, GUI, CLI, x4 lane) now agrees, and
  `POKEBOT_FODDER_RULE=legacy` is the documented way back for an A/B.
  ‼ **The governing test `repro_fodder_grass.py` STILL has not been run on any machine** — it
  needs a real ROM + save state. The arms provably differ only for teams at/below L17 and only
  at boss prep, and every run names its rule in the log header, so the blast radius is bounded
  and attributable — but this is a **user-directed default, not a validated one**. If early
  prep regresses, set `POKEBOT_FODDER_RULE=legacy`.
- **STATUS 2026-07-29 (earlier): the decision is a PURE, FLAGGED function.**
  `training_areas.local_patch_is_fodder()` holds both rules behind `FODDER_RULE`, which
  defaults to `"legacy"`. A repro proves the extracted legacy path reproduces the old inline
  expression across all 1,800 `(local_max, team_max)` combinations, and that the two rules
  disagree on **exactly L5-L17 and nowhere else** — so flipping the flag cannot disturb prep
  from L18 up. `tools/story-dev/repro_fodder_rule.py`.
  **To run the A/B — NO CODE EDIT NEEDED (2026-07-29):** set the env var
  `POKEBOT_FODDER_RULE=xp_rate` before launching. It normalises case/whitespace and REFUSES
  an unknown value loudly (a typo silently falling back to `legacy` would invalidate the
  experiment). Every run header prints `Story: training-relocation rule = …`, so a bundle is
  attributable after the fact.
  ‼ Do NOT hand-edit the constant on the batch machine: `install.py`'s self-healing runs
  `git checkout -- <drifted>` and can revert it.
  On the machine with `mgba`, also run `repro_fodder_grass.py` before and after and compare
  the WATTSON/ROXANNE rows — those are what the flag changes. Only then consider changing the
  default.
- **Proposed rule (implemented, OFF by default):** replace the gap test with a frame-saving
  test built from the existing pure model — relocate when
  `estimate_frames_to_level(mon, target, local_max) − estimate_frames_to_level(mon, target,
  better_hi)` is a large win (e.g. the better area at least HALVES the estimated grind, which
  by the model means `better_hi ≥ 2 × local_max`). This needs no new constant and no travel
  measurement.
  ‼ Travel cost remains **unmeasured** — `story_mode.py:576` says so explicitly — which is why
  the proposal is deliberately conservative and only fires on large wins.
- **Related:** `train_team` (`early_game.py:1738`) never consults `best_training_area` at all;
  its `grass` is a caller-supplied constant. Both belong to `#24-trainmap+`.

## KI-32 — the stall detector was STRUCTURALLY BLIND to any in-battle wedge — ✅ FIXED 2026-07-29
- **Symptom:** user log `20260729-122709`. A mid-battle rotation wedged the PARTY MENU in
  Fortree Gym; the run then held `state=3 controllable=False` at one fixed position for
  **~280,000 frames** and emitted **ZERO stuck dumps** — no generator call stack, the single
  most useful artefact the logger produces.
- **Cause:** `modules/debug_logger.py` stall detection did
  `if st.get("battle_active"): _stall_frames = 0` on EVERY in-battle frame. The intent was
  sound (a battle legitimately holds still mid-turn and during the EXP fill, so the 300-frame
  overworld threshold would false-trigger every turn) but the implementation meant **no
  in-battle wedge could ever be reported, however long it lasted.**
- **Same shape as KI-27** (Weather Institute): the guard could not fire on the thing it was
  guarding. A guard must not share its subject's failure mode.
- **Fix:** a battle now gets a much LARGER threshold, not an exemption —
  `_BATTLE_STALL_DUMP_AFTER = 18_000` (5 min at 60fps, ~60× the overworld threshold and
  ~2 orders of magnitude above the longest legitimate quiet stretch). Overworld sensitivity
  unchanged at 300.
- **Repro:** `tools/story-dev/repro_battle_stall_blindspot.py` — proves a frozen battle now
  dumps, a healthy/changing battle never does, 300/3,000/10,000-frame in-battle quiet is not
  disturbed, the overworld path is unchanged, and a long wedge re-dumps periodically.

## KI-33 — a mid-battle rotation can still wedge the PARTY MENU (opened 2026-07-29, severity: HIGH)
- **Symptom:** the wedge KI-32 made visible. From `20260729-122709`, inside a Fortree Gym
  trainer battle:
  ```
  f1791402 [BATTLE] started
  f1793385 [PARTY] slot0 Marshtomp:L35 -> Castform:L25   <- rotation applied
  f1793407 [PARTY] slot0 Castform:L25 -> Marshtomp:L35   <- reverted 22 frames later
  f1799232 [PARTY] slot0 Marshtomp:L35 -> Castform:L25   <- applied again
  f1800001 [hb] state=3 (PARTY_MENU) controllable=False  <- wedged until stopped
  ```
  Apply → revert → apply, then a permanent `PARTY_MENU`. The run had already cleared five
  gyms and won 310 battles; this ended it.
- **This is the open half of KI-8.** KI-8 records the same
  `TurnAction.RotateLead → scroll_to_party_menu_index → while PARTY_MENU: press A` hazard and
  says the Story bot "sidesteps this path" because its trainer strategy never proactively
  rotates. **Something rotated anyway** — so either the strategy did rotate, or the after-faint
  chooser ran. Which one is NOT yet established.
- **Aggravating factor:** the mon rotated IN was **Castform L25**, against Winona's L29-33
  line-up, while **Marshtomp L35** was rotated out — the defensive-only lead selection of
  KI-25 choosing badly under pressure.
- **Next step (needs the emulator):** capture a save state at the wedge and drive
  `TurnAction.RotateLead` into a specific slot to establish whether the stall is in
  `map_battle_party_index`, the submenu default not being "SHIFT", or the after-faint chooser.
  KI-8's "Proven fix pattern now exists" note is the starting point.
- **Bounded, not fixed:** the per-run frame budget would have ended this run at 3.5M frames
  (it was at 2.78M when stopped), and KI-32 now makes it *diagnosable*. Neither prevents it.

## KI-34 — the after-faint chooser LIVELOCKS when its candidate filter and the game disagree (opened 2026-07-29, severity: HIGH)
- **User report:** *"noticed an error with I think p2 or p3 where they were training with a
  skitty and an Abra in the team in a double battle but had issues selecting the Abra."*
  Confirmed in P2 of bundle `20260729-172342`, and **this is the first production catch by the
  KI-32 in-battle stall fix** — without it the log would again have been silent.
- **Evidence (71 in-battle STUCK dumps, f652,238 → f862,238 = 210,000 frames):**
  ```
  game_state=3 (PARTY_MENU)  controllable=False
  battle: active=True  instr=BattleScript_FaintedMonTryChoose
  battle_text='MARSHTOMP fainted!'
  party=['Marshtomp L27 0/76', 'Skitty L15 41/41', 'Poochyena L12 0/32', 'Abra L7 21/21']
  -> handle_battle @ battle_handler.py:264
  -> handle_fainted_pokemon @ battle_handler.py:532 / :537
  ```
- **It is a LIVELOCK, not a hang.** Across all 71 dumps the **party never changes** — no
  replacement is ever sent out — but the menu state *cycles*:
  `Task_ReturnToChooseMonAfterText + Task_PrintAndWaitForText` ×57,
  `Task_HandleChooseMonInput` ×10, `Task_HandleSelectionMenuInput` ×3, and the stack alternates
  between the two `yield` sites at `:532`/`:537`. The bot is pressing buttons and the game is
  responding; the *outcome* never occurs.
- **‼ Its 6,000-frame bound does not bound anything.** `handle_fainted_pokemon` ends with
  `if frames > 6000: return` — but the dispatcher re-enters it with `frames = 0`.
  210,000 / 6,000 ≈ **35 re-entries**. This is verbatim the playbook rule
  *"bound the OUTCOME, not just the frames — a bounded loop re-entered by its dispatcher is
  still infinite."*
- **Two candidate mechanisms — NOT yet distinguished, and the dump cannot separate them:**
  1. **`alive_slots` is EMPTY.** If this is a DOUBLE battle whose actives are Skitty(1) and
     Abra(3), then `_on_field = {1,3}`; slots 0 and 2 are fainted, so the KI-18 exclusion
     leaves **no candidate at all**. Every branch then either dismisses text or walks the
     cursor, and A is never pressed — matching "issues selecting the Abra" exactly.
  2. **Text-branch starvation.** The `Task_PrintAndWaitForText` /
     `Task_ReturnToChooseMonAfterText` branch is checked FIRST and was active in 57 of 71
     samples, so it can starve the `cursor not in alive_slots → "Down"` branch: A dismisses
     the text, the cursor is still on a fainted slot, A re-selects it, the text returns.
     KI-17's `post_gap = 24` was meant to prevent this; 24 frames may be insufficient.
- **‼ INSTRUMENTED 2026-07-29 — the next occurrence will name its own cause.**
  `handle_fainted_pokemon` now emits, via `debug_logger.event(category="BATTLE")`:
  * on entry — `[FAINT-CHOOSER] alive_slots=… on_field=… party=[(slot, species, hp)…]`, with an
    explicit **`‼ NO ELIGIBLE REPLACEMENT — cannot succeed`** when `alive_slots` is empty. That
    one line separates mechanism (a) from (b).
  * on give-up — `[FAINT-CHOOSER] GAVE UP after N frames … presses={…} cursors_seen=[…]`.
    The press histogram is what distinguishes *pressing the wrong thing* from *pressing
    nothing* (playbook §7); the state trace alone cannot.
  Counted per iteration, emitted once, so it cannot flood a log.
- **‼ DIAGNOSED 2026-07-30 by that instrumentation — mechanism (b), and (a) is REFUTED.**
  Overnight batch `20260730-062818`, 7,539 chooser entries and 3,978 give-ups:
  * **`alive_slots` was NEVER empty — 0 of 7,539.** So the KI-18 on-field exclusion is NOT
    starving the candidate set. **Mechanism (a) is dead.**
  * **`presses={'A': 289}` — A and NOTHING ELSE**, every time. No `Down`, no `B`, no `(none)`.
  * **`cursors_seen=[1]` — a SINGLE position for the whole 6,002 frames**, and that position
    **is in `alive_slots`**. The cursor is parked on a living, eligible mon.
  So: the cursor is already correct, the bot presses A ~289 times, and the menu never advances.
  It is not choosing wrongly and not failing to find a candidate — **its A-presses are not
  being accepted**, and the printer-task branch (`Task_PrintAndWaitForText` /
  `Task_ReturnToChooseMonAfterText`) keeps re-arming, so it never reaches any other branch.
  KI-17's `post_gap = 24` is insufficient for this case.
- **Where:** `MAUVILLE CITY(10,0)` — the Mauville Gym — in **3,975 of 3,975** located give-ups,
  and `on_field` carries TWO slots, i.e. a **DOUBLE battle**. Exactly the user's original report.
- **‼ Scale, and why it matters more than it looks:** P3 alone burned **23,857,950 frames** in
  3,975 give-ups (**~7.8 complete runs' worth**) — and P3 completed only **5 badge-earning runs
  overnight against P2's 19.** The livelock, not difficulty, is what cost that lane its night.
  P1 1, P2 0, P4 2 — it is **99.9% concentrated in P3/Treecko**, because Treecko has no Ground
  answer to Wattson, loses repeatedly, and every loss is another after-faint chooser roll.
- **‼ ROOT CAUSE FOUND 2026-07-30 — USER OBSERVATION + CODE, and it invalidates my reading of
  my own instrumentation.** The user, watching the screen: *"the bot is selecting a live pokemon
  in the pokeparty, but its one that is already in the field (cannot select an already active
  pokemon to swap out)"*.
  That is impossible if `alive_slots` is correct — and it is correct, **in its own index space.
  The comparison is not.** There are TWO party index spaces:
  * **regular party order** — what `get_party()` returns;
  * **in-battle party-menu order** — what the party MENU uses, which diverges from the regular
    order once mons have been switched in and out. `BattleState.map_battle_party_index()`
    (`battle_state.py:332`) exists solely to convert between them, and its docstring says so:
    *"the order in the party menu might be different from what `get_party()` returns so we'd
    have to scroll to a different index."*

  `handle_fainted_pokemon` uses BOTH SPACES AND COMPARES THEM DIRECTLY:
  | line | value | space |
  |---|---|---|
  | `battle_handler.py:474` | `party_in_menu = get_party()` | **regular** |
  | `battle_handler.py:~504` | `alive_slots` built by enumerating that party | **regular** |
  | `battle_handler.py:530` | `cursor = get_party_menu_cursor_pos(...)["slot_id"]` (reads `gPartyMenu.slotId`) | **in-battle menu** |
  | `battle_handler.py:548-549` | `cursor in alive_slots` / `cursor not in alive_slots` | **‼ mixed** |

  ‼ **The same function already knows better**: its PRIMARY path maps correctly at
  `battle_handler.py:443-444` (`if index_needs_mapping: new_lead_index =
  battle_state.map_battle_party_index(new_lead_index)`). Only the RECOVERY SWEEP — the loop that
  actually wedges — skips the mapping.
- **Why this explains every observation at once:** once the orders diverge (i.e. after switches
  and faints — exactly a double battle late in a fight), menu-slot *n* is a different mon than
  party-slot *n*. The sweep concludes "cursor is on a living, eligible mon", presses A, and the
  game **refuses because that mon is on the field** — which re-arms
  `Task_PrintAndWaitForText`, so the loop takes the dismiss-text branch again. Hence exactly
  what was logged: `presses={'A': 289}`, **cursor static**, and a `cursor in alive_slots` test
  that was TRUE and meaningless. It is worst in P3 because that lane faints most, so its orders
  diverge most.
- **‼ LESSON (logged in 08-MISTAKES):** I instrumented the VALUES but not their UNITS. Two
  integers from different coordinate systems compared as if interchangeable — and the log I
  added made the wrong comparison look verified.
- **FIXED 2026-07-30.** Two changes in `modules/battle_handler.py`:
  1. **Convert before comparing.** `alive_slots_menu = {map_battle_party_index(i) ...}` and every
     cursor test now uses the MENU-order set — matching what the primary path and
     `battle_action_selection.py:124/199` already did. The entry log prints BOTH sets with their
     units and flags `[orders DIVERGE]`.
  2. **Bound the OUTCOME, not the frames.** `FAINT_CHOOSER_GIVEUP_LIMIT = 3` per battle
     (counter reset in `handle_battle`); on exceeding it the run gets a RECOVERABLE derail via
     `battle_fault.request_mode_recovery()`, which makes `handle_battle` and `BattleListener`
     short-circuit so `StoryMode` claims it and the endless loop starts the next run.
     It never RAISES from battle code — on this flat controller stack that would reach
     `main_loop` and force Manual.
- **Repro:** `tools/story-dev/repro_faint_chooser_index_space.py` — builds a diverged battle
  party order and proves the OLD test calls menu slot 1 selectable while the NEW test correctly
  rejects it as on-field: the user's observation, reproduced as arithmetic.

## KI-36 — the per-run frame budget CANNOT fire while a battle handler is on the stack (opened 2026-07-30, severity: HIGH)
- **Symptom:** in `20260730-062818`, P3 run `235303` ran for **25,632,106 frames** — five times
  the 5,000,000 cap — and the batch reported **`frame-cap=0`**. The budget never fired.
- **Cause, and it is a defect in the KI-27 fix itself.** `_run_with_frame_budget` is a
  **generator wrapper**: it can only check the budget when the story generator is stepped. But
  the controller stack is **FLAT** (`02-ARCHITECTURE.md`) — `main_loop` advances only the TOP
  generator. In that run the stack was
  `['StoryEndlessResetMode.run', 'TrainerApproachListener.handle_trainer_approach', 'BattleListener.fight']`
  in **8,022 of ~8,200 samples**, so `BattleListener.fight` was on top and the story generator —
  with my budget wrapper — **was never advanced at all.**
- **‼ So the budget is blind to precisely the failure class it was built for.** Every wedge we
  have (KI-17, KI-33, KI-34) is inside a battle handler.
- **Why KI-32's stall dumps still worked:** `modules/debug_logger.py` is driven by a **per-frame
  listener** from `modules/main.py`, not by a generator, so it keeps sampling regardless of what
  is on top of the stack. We therefore have **diagnosis without termination**.
- **PARTIALLY FIXED 2026-07-30 — a net, not the complete fix.** `modules/debug_logger.py`
  already ticks every frame as a per-frame LISTENER (exactly why its stall dumps fired when the
  budget did not), so the thing that NOTICES a wedge now also ENDS one: at
  `_BATTLE_STALL_FAULT_AFTER = 60_000` frames of byte-identical in-battle state (>3x the dump
  threshold, ~16 min at 60fps) it calls `battle_fault.request_mode_recovery()` once.
  LIMITATION, STATED: this only works while **debug logging is ON**. It is a net for batch runs
  (which always enable it), not a general watchdog. **A stack-independent budget in `main_loop`
  remains the complete fix and is still OPEN.**
- **Relationship to existing entries.** Same family as **KI-33** (Fortree, 2026-07-29) and
  **KI-17** — all three are `BattleScript_FaintedMonTryChoose` +
  `Task_ReturnToChooseMonAfterText`/`Task_PrintAndWaitForText`. KI-17 is currently marked
  ✅ FIXED; **it is not fixed for the multi-faint case.** KI-33's open question ("strategy or
  after-faint chooser?") is hereby **answered: the after-faint chooser.**
- **Not fixed.** Bounded only by the per-run frame budget, which would end the run at 3.5M.

## KI-35 — a SUCCESSFUL run now uses 87% of the per-run frame budget (opened 2026-07-29, severity: MED)
- **Symptom:** the single run in `20260729-151635` **completed** — six gym leaders beaten
  including Winona (`FortreeCity_Gym_EventScript_WinonaDefeated` + badge fanfare), 462 battles
  won — and consumed **3,058,007 frames**. `MAX_FRAMES_PER_RUN = 3_500_000`.
  That is **14% headroom**, not the "~1.5x" its own comment claims (written when the deepest
  run was ~2.24M).
- **Risk:** the in-run frame budget added 2026-07-27 (KI-27 fix) will start terminating
  **successful** runs and reporting them as wedged. A slightly unluckier run — a few more heal
  round trips, one extra failed gym attempt — trips it.
- **Why runs got longer, measured in the same log:** **78 heal round trips** in one run
  (Route 116↔Rustboro ×34, Dewford↔Granite Cave ×29, Route 117↔Mauville ×15). With no potion
  layer every HP dip is a full walk to a Poké Center and back. This is `#24-provisions`, and
  it is now the dominant cost of a run — more than any gym's difficulty.
- **✅ FIXED 2026-07-29: `MAX_FRAMES_PER_RUN` 3,500,000 → 5,000,000.** Restores ~1.6x over the
  deepest observed run (3,117,110), re-deriving the constant from measured data rather than
  guessing — the same "~1.5x the deepest completed run" rule the original comment used.
  ‼ Raising it is cheaper than it used to be: since KI-32 an in-battle wedge produces a STUCK
  dump after 18,000 frames, so the cap is no longer the only thing that NOTICES a hang, just
  the thing that ENDS one — a wedge is now diagnosed ~270x sooner than the cap fires.
  Expect to raise it again as content grows; re-derive from the deepest COMPLETED run.


## KI-37 — a listener above the mode can STARVE it, so a handed-over battle fault is never claimed (opened 2026-07-30, severity: HIGH — CAUSED BY THE KI-34 FIX)
- **Symptom:** user log `20260730-081347` (`Story (DEBUG - RESET)`, build `4f1e02f9`).
  `handle_fainted_pokemon` did its job — 3 give-ups, then a correct hand-over at f1,797,401:
  `[FAINT-CHOOSER] handing a recoverable derail to the mode`. **Nothing claimed it.** The run
  then sat at `state=3 controllable=False` on ROUTE 117 for **1,182,000 frames** until the user
  stopped it by hand. KI-36's 60,000-frame net ALSO fired and was ALSO unclaimed.
- **Contrast, same build, sibling log `20260730-074518` (`ENDLESS RESET`):** the identical
  hand-over was claimed **one frame later** — `f902223 [STORY] DERAIL #1: Story: battle handler
  gave up — after-faint chooser could not send a mon out after 3 attempts (KI-34)`. So the
  channel works; something specific starved the mode in the other run.
- **Cause.** `TrainerApproachListener.handle_trainer_approach` was:
  ```python
  while get_global_script_context().is_active:
      context.emulator.press_button("B")
      yield
  ```
  An **unbounded loop with no fault check**. When a battle wedges, the trainer script never
  clears, so this listener sits on TOP of the controller stack pressing B for ever — and the
  MODE, the only thing that can consume the fault and derail, is never advanced. The stack at
  the wedge was `['StoryDebugResetMode.run', 'TrainerApproachListener.handle_trainer_approach']`
  with **no battle handler at all**: the fault had already short-circuited it, exactly as
  designed.
- **‼ `BattleListener` ALREADY HAD THIS EXACT GUARD**, ~110 lines above in the same file, with a
  comment naming the identical hazard: *"this would press B forever while the MODE — the only
  thing that can recover — is starved of frames."* The sibling listener simply never mirrored
  it. Third instance of that shape (KI-18's driver, KI-34's recovery sweep, now this).
- **This is a deadlock the fix created**, and `battle_fault.py`'s own docstring predicted it:
  *"An unconsumed fault would be far worse than a Manual drop."*
- **✅ FIXED 2026-07-30:** `handle_trainer_approach` now returns when `battle_fault_pending()`,
  popping back to the mode. Asserted in `repro_faint_chooser_index_space.py`.
- **‼ FOLLOW-UP, STILL OPEN:** audit **every** listener that can sit above the mode for the same
  omission, and bound their loops. A per-frame, stack-independent recovery (KI-36's complete
  fix) would make this class impossible rather than requiring each listener to remember.

## KI-38 — 3 residual after-faint give-ups remain; the text fallback has now EARNED its place (opened 2026-07-30, severity: MED)
- **The KI-34 index fix works and the diagnosis is CONFIRMED.** `[orders DIVERGE]` appears in
  both logs with concrete evidence — `alive_slots=[1, 2, 3](party-order) -> [0, 2, 3](menu-order)`
  — and give-ups fell from **3,975 in one lane to 3 per run.**
- **But 3 remain**, with a new press profile: `presses={'Down': 3, 'A': 273}` and
  `cursors_seen=[0, 2, 3, 7](menu-order)` against `alive_slots=[2](party) -> [0](menu)` in a
  FOUR-mon party. Two things are unexplained and the data cannot separate them:
  1. **cursor 7 in a 4-mon party** — almost certainly the party menu's CANCEL entry. If the
     cursor walks past the target onto CANCEL, `"Down"` may never bring it back.
  2. **273 A-presses with the cursor reportedly reaching 0**, the mapped target — so either the
     target is still wrong, or A on it is being refused for a reason we do not read.
- **‼ The user's proposed TEXT-DETECTION FALLBACK (`#24-menutext`) is now justified by
  evidence**, exactly as predicted when it was deferred: reading the game's own refusal message
  distinguishes "wrong target" from "right target, refused" and is strictly more general than
  any index reasoning. **The exact string must be read from the pokeemerald decomp, never
  recalled.**
- **Also worth instrumenting:** log the cursor AND the target on each press, not just the sets,
  so a press can be attributed to a position.

## KI-39 — The bot has NO cross-map overworld route planning; long journeys are hand-coded (2026-07-30)

**This is the root cause behind every "unreachable counter destination", and it is much
bigger than `#24-counters`.** It is also the direct answer to the user's question *"is there
a way to get the bot to map to already traveled locations?"* — today, no.

### Measured, from `rocksmash_taught.ss1` (standing in MAUVILLE_CITY (32,15))
| destination | `calculate_path` |
|---|---|
| ROUTE117 (31,16) — directly connected | **OK, 72 waypoints** |
| ROUTE110 (12,60) — joined through a gate BUILDING (a warp) | FAIL |
| ROUTE116 (11,7) — several maps west | FAIL |
| ROUTE111 (25,55) — same map, other side of the Go-Goggles desert | FAIL |

### Why `navigate_to_anywhere` does not rescue it
It branches on REGION, and a region is the connected component over direct N/S/E/W map
connections. Measured: `region_of(MAUVILLE_CITY) == region_of(ROUTE111) ==
region_of(ROUTE116) == region_of(LAVARIDGE_TOWN) == region_of(FALLARBOR_TOWN) == **0**`.
**The whole Hoenn overworld is ONE region.** So for any overworld→overworld trip the
same-region branch is taken, the warp planner is never consulted, and the entire journey is
handed to `calculate_path` — which only spans directly-connected maps. The warp route often
EXISTS and is simply never asked for: `graph.plan(MAUVILLE → FIERY_PATH)` returns a valid
one-warp edge (ROUTE112 (11,36) → FIERY_PATH), yet the navigation fails at 255 frames because
leg 1 — *walk to that warp tile* — is itself a multi-map journey `calculate_path` cannot plan.

### Why nobody noticed
The story chapters hand-code their long journeys leg by leg (`_hold_walk_route` exists
precisely to "bridge the planner can't cross"). Every long trip the bot makes today was
written out by hand, so the generic capability was never exercised — and its absence looks
exactly like "that destination is unreachable".

### Consequences to hold in mind
* A counter hunt only reaches destinations a leg or two away. FIERY_PATH (18,19) arrives in
  2,922 frames from **Lavaridge**, but Norman is fought at **Petalburg** — so even the one
  rung measured "live" is probably inert at the moment it actually fires. Expect the counter
  chain to stop honestly far more often than it hunts.
* `#24-dexhunt`, `#24-pc` (box trips), `#24-catchcap` and the whole team/PC-reserve plan all
  assume the bot can travel to a known place on request. **They are gated on this.**

### What the fix looks like (NOT built)
A cross-map journey planner: BFS the map-connection graph **plus** warp edges to produce an
ordered leg list, then execute leg by leg with `navigate_to`, re-planning from the real
position after each leg (the shape `navigate_to_anywhere` already uses for cross-region
routes — it just never gets to use it). Needs: the desert/elevation splits expressed as
sub-map partitions (Route 111 north vs south are the same map but not mutually walkable),
capability gates (Surf/Fly/Go-Goggles), and a frame budget per leg.

‼ **Do not "fix" this by adding gateway waypoints.** Tried and refuted 2026-07-30: a gateway
in the same region is routed by the same broken same-region branch, so it fails identically.
Fallarbor PC, Lavaridge PC and Fiery Path were all tried as gateways from Mauville; every
leg failed at 255 frames (`probe_counter_gateway.py`).

## KI-40 — Runs stopped FINISHING and the global watchdog fires ~77x more often (2026-07-30, UNATTRIBUTED)

**Measured**, bundle `20260730-204036` (build `ffb062ce`, 4 lanes, ~3h11m) vs bundle
`20260730-062818` (build `21b587f1`, ~13h):

| metric | `21b587f1` | `ffb062ce` |
|---|---|---|
| runs reaching `finished` | 29 of 60 run-ends (48%) | **0 of 30** |
| `global watchdog — nothing progressed` | 5 (~0.4/h) | **94 (~29.5/h)** |
| dominant run-end reason | `boss: N losses…` (22) | **global watchdog (23 of 30)** |

**Not environmental:** RUN HEADERs are identical — Python 3.13.7, same ROM, `speed=0
video=True audio=False`, fodder rule `xp_rate`. **Not an instrument change:** the watchdog
message and its 18,000-frame bound are unchanged since `88a0e307`, present in both builds.

**Observed wedge sites:** `training N battler(s) to Lv 31 in ROUTE117` (stage 9, map (10,0)),
and the `Rock Smash teach skipped → Fallarbor travel not applicable → Meteor Falls scene
already done` sequence (stage 11, map (24,12)). In both, recovery re-enters the same step and
the watchdog fires again — derail #2, #3, #5 on the identical step.

**‼ ATTRIBUTION IS OPEN.** The bundles are 16 commits apart. Ten are prior-session work
(KI-34, KI-35, KI-36, KI-37 fixes); four are mine and touch production code (`5229e780`,
`f74fab6c`, `31647da3`, `06807942`). The `21b587f1` bundle is the already-reviewed
`20260730-062818` batch, i.e. it predates ALL of them. **Do not blame or clear either group
from this data.**

**Refuted already:** that `_counter_ladder`'s `_note_training_unreachable` calls poison the
training-area picker. Only 2 blacklist events came from the ladder; `ROUTE111 (25,55)`
dominates in both builds (14 new / 24 old) and is the training picker's own doing.

**THE EXPERIMENT THAT SETTLES IT (do this before any more long batches):** ~1 hour on
`d7d493d8` and ~1 hour on `ffb062ce`, same lanes and settings, comparing **watchdog fires per
hour** and **finish rate**. `d7d493d8` is the last build the handoff records as
live-validated — but note that validation was *"no unrecovered errors"* and never checked
finish rate, so it may not be a clean baseline either. If `d7d493d8` is clean, bisect my four
commits; if it is not, the cause is in the KI-34/35/36/37 work.

### KI-40 — ATTRIBUTED 2026-07-30 by controlled A/B. The 2026-07-30 counter-chain work is CLEARED.

Baseline arm run on the user's machine: bundle `20260730-214525`, build **`d7d493d8`**
(detached HEAD via tag `baseline/ki40`), launch `212123`, ~24 min, 4 lanes.

| build | window | watchdog fires | **per hour** | runs `finished` |
|---|---|---|---|---|
| `21b587f1` (pre-KI-34/35/36/37) | ~13 h | 5 | **0.4** | 29 of 60 |
| **`d7d493d8` (baseline arm)** | ~0.4 h | 8 | **~20** | **0 of 2** |
| `ffb062ce` (counter-chain work) | ~3.2 h | 94 | **~29.5** | 0 of 30 |

**`d7d493d8` already wedges at ~50× the old rate**, in the same order of magnitude as
`ffb062ce`. The discrimination required was "≈0 or ≈30 per hour"; it came back ≈20.
⇒ **The regression entered between `21b587f1` and `d7d493d8`** — i.e. in the
**KI-34 / KI-35 / KI-36 / KI-37** work (`00db4a81`, `4f1e02f9`, `d7d493d8`), NOT in the
2026-07-30 counter-chain or menu commits.

‼ **This also corrects the handoff.** `d7d493d8` was recorded as live-validated — but that
validation was *"no unrecovered errors"*, and it never checked **finish rate**. On the
finish-rate metric `d7d493d8` is badly broken, and that went unnoticed for a full day of work
built on top of it. **A "clean" verdict is only as good as the metric it was measured on.**

**The wedge is the TARGETED-TRAINING path, in both builds:**
* `d7d493d8`: `Taillow is the answer to this gym but needs Lv 18 — targeted top-up of just
  that mon` → wedge. Stage 7 (Brawly), map (3,3) = DEWFORD_TOWN_GYM.
* `ffb062ce`: `prepping — training 3 battler(s) to Lv 31 in ROUTE117` → wedge. Stage 9,
  map (10,0); also the Rock Smash→Fallarbor→Meteor Falls sequence at map (24,12).
In both, recovery re-enters the identical step and the watchdog fires again (derail #2, #3,
#5 on the same step), so the step itself never becomes completable.

**Leading hypothesis — the mode is being STARVED, not stuck.** The watchdog reports "nothing
progressed for 18,000 frames", which is what a listener sitting above the mode produces.
`04-HANDOFF` Rule 2 already warns: *"Every listener that can sit above the mode must honour
`battle_fault_pending()` and be bounded… `BattleListener` and `TrainerApproachListener` now
do; **others are UNAUDITED**."* The window's diff is +143 lines in `battle_handler.py` and
+21 in `_listeners.py`. **Audit every remaining listener next**; a training spin walks in
grass and is exactly where listener traffic is heaviest.

**Next step is DIAGNOSIS, not more batches** — the remaining suspect set is 3 commits and the
symptom is reproducible in-run. A further 1-hour arm on `00db4a81` or `4f1e02f9` would bisect
it if reading the diffs does not.

### KI-40 → ROOT-CAUSED 2026-07-30: it is **KI-38**, and KI-38 is not "residual" — it is the dominant run-killer

`05-KNOWN-ISSUES`/`04-HANDOFF` describe KI-38 as *"3 residual after-faint give-ups"*. That
figure came from one sample. Measured across both A/B arms it is the thing ending the runs.

**The STUCK dump (baseline `d7d493d8`, P2, f623813) is unambiguous:**
```
message='Story: entering Dewford Gym to challenge Brawly...'
game_state=3  controllable=False
battle: active=True  instr=BattleScript_FaintedMonTryChoose
tasks=['Task_HandleChooseMonInput']            <- the after-faint party menu is OPEN
party=['Taillow L19 0/48', 'Marshtomp L17 55/55', 'Nincada L10 0/28', 'Whismur L17 51/51']
controllers=['StoryEndlessResetMode.run']      <- ‼ NO battle handler on the stack
===== DUMP [STUCK — 111000 frames no progress] =====
```
Two healthy mons (Marshtomp 55/55, Whismur 51/51) were available to send in. Nothing was
driving the battle: the faint chooser had already given up and left the menu open.

**Rates (`GAVE UP` / hour), stable across builds:** baseline `d7d493d8` 9 in ~0.4 h ≈ **22/h**;
`ffb062ce` 75 in ~3.2 h ≈ **23/h**. Faults handed to the mode: 5 and 48 respectively.
‼ **`NO ELIGIBLE REPLACEMENT` = 0 in BOTH.** The chooser always had a valid, living target and
still failed to select it. This is not a "no legal move" case; it is a selection bug.

**Why KI-34's fix made the SYMPTOM worse while being correct in itself.** `4f1e02f9` added
`FAINT_CHOOSER_GIVEUP_LIMIT = 3` to bound an unbounded re-entry (previously ~35 re-entries /
210,000 frames per battle). The bound works — but on giving up it leaves **the battle still
active with the menu open**, hands a fault to the mode, and the mode's recovery (B-ride,
re-orient, resume) cannot answer an in-battle party menu. So recovery re-enters the same step
and wedges again — derail #2, #3, #5 on the identical step. Before the limit, the handler span
forever inside one battle (wasteful, but it stayed on the stack and could still succeed, which
is why `21b587f1` still finished 48% of its runs). **The limit converted a slow leak into a
hard stop.** Both the index-space fix and the bound are right; what is missing is a
give-up path that RESOLVES the battle instead of abandoning it.

**Therefore the fix must be one of:**
1. ‼ **Make the chooser actually select** — `#24-menutext`, already named in the handoff as
   the resolver: read the party-menu text so the bot knows what the cursor is on, instead of
   inferring from indices. **The string MUST come from the decomp.** KI-38's own evidence
   (`presses={'Down': 3, 'A': 273}`, `cursors_seen=[0,2,3,7]` in a 4-mon party, where 7 is
   probably CANCEL) says the cursor model is wrong, which no amount of retrying fixes.
2. **Make the give-up SAFE** — on give-up, drive the battle to a resolved state rather than
   returning with the menu open. A fault the mode cannot act on is worse than no fault.
3. **Interim mitigation only:** raise `FAINT_CHOOSER_GIVEUP_LIMIT`. This trades a hard wedge
   for the old slow leak; it keeps KI-34's index-space fix (which is correct and unrelated).
   Cheap to try, one constant, and it should restore something like the 48% finish rate —
   but it is a mitigation, not a fix, and it must not be mistaken for one.

## ‼ KI-39 — CORRECTED AND LARGELY RESOLVED 2026-07-31. Read this before the section above.

**The KI-39 entry above states the cause wrongly, and the handoff repeated it.** The claim
was *"`calculate_path` only spans directly-connected maps"* and *"the bot has NO cross-map
overworld route planning"*. Both are false. Measured live from `rocksmash_taught.ss1`
(Mauville 32,15) with the SAME `calculate_path` the production path uses
(`tools/story-dev/probe_journey_legs.py`, `probe_journey_why.py`, `probe_journey_walls.py`):

* `map_path.py` assigns **every** edge-connected map a global offset and a shared `level`,
  and its own docstring says it "supports paths across several maps, but only if they are
  connected". Mauville, Routes 110/111/112/116/117 and Verdanturf are **all level 459** — so
  `calculate_path` was trying, and failing at TILE level, not refusing to plan.
* Partial reachability proves it: **ROUTE110 17/125 tiles reachable, ROUTE111 11/173,
  ROUTE117 22/41, VERDANTURF 14/23.** A planner that could not cross maps would score 0.

### The four blocked trips had FOUR DIFFERENT causes. Only one was route planning.

| trip | measured cause | status |
|---|---|---|
| Mauville → **ROUTE116** | Verdanturf declares a North map CONNECTION to Route 116, so the union-find merges them into one region — but **0 of 40 sampled Route 116 tiles are walkable from Verdanturf**, while the RUSTURF_TUNNEL door at VERDANTURF (8,1) is. The real link is a **warp inside one region**, and `WarpGraph.plan()` returns `[]` for any same-region pair. **This is the genuine KI-39.** | **FIXED** (see below) |
| Mauville → **ROUTE110** (12,60) | reachable strip ends at y≈20 (column 12); the rest is behind the cycling-road gate structures — same warp-inside-a-region class | fixed in kind; specific tile still needs the gates |
| Mauville → **ROUTE112 / FIERY_PATH** | the **Rock Smash twin-rocks choke on ROUTE111 at (18,101)**. Column-by-column probe: reachable y≥102, blocked y≤101 across columns 17–20. Route 112 scores **0/76**, and Fiery Path's only two doors are both on Route 112. | **NOT a planner problem** — see KI-41 |
| Mauville → **ROUTE111** (25,55) | the Go-Goggles desert. Genuinely gated; the south strip is reachable, the north is not. | correct refusal |

### The fix that shipped
`WarpGraph.warp_candidates()` — warp planning at **MAP** granularity instead of REGION
granularity, so a warp route can be returned even when start and goal share a region. The
map-level adjacency is now kept (it was previously consumed by the union-find and discarded);
`CACHE_VERSION` 1→2 so stale caches rebuild rather than silently loading a degraded graph.
`navigate_to_anywhere` now (1) asks `calculate_path` whether a plain walk works — unchanged
fast path if yes — and only then (2) asks for warp candidates and **validates each one's
first leg with `calculate_path` before committing**, remembering warps it has taken so a
re-plan cannot ping-pong.

‼ Also fixed in the same change: `navigate_to_anywhere`'s "did the warp fire?" test compared
**regions**. A warp between two maps of the same region — exactly the class this makes
plannable — leaves the region unchanged, so a *working* warp would have been reported as
`"Warp at … did not trigger (locked or event-gated?)"`. It compares maps now.

### Proof
* `tools/story-dev/repro_journey_planner.py` — 27 checks, no emulator, pins the whole
  topology including the two traps below.
* `tools/story-dev/probe_journey_live.py` (+ `story_harness.py --driver journey`) — live
  fault-injected A/B in the faithful harness:
  **OLD arm `arrived=False map=MAUVILLE_CITY`** (never left the starting map) vs
  **NEW arm `arrived=True map=ROUTE116`, 33,725 frames**, walking Mauville → Route 117 →
  Verdanturf → Rusturf Tunnel → Route 116.

### Two traps found while building it, both pinned by the repro
1. **The progress filter must be NON-INCREASING, not strictly decreasing.** The phantom
   Verdanturf→Route116 connection puts the target 1 hop away, so *nothing* can be strictly
   closer and a strict filter drops the very warp that works.
2. **Banning the previous answer produces junk candidates.** Verdanturf→Route116 offered the
   BATTLE TENT LOBBY and the MART as candidates 5 and 6 — real routes (walk in, walk out,
   then take the tunnel) that make no progress. Harmless only while an earlier candidate
   validates, which is not a guarantee.

### ‼ What this does NOT fix — correct the handoff's expectations
The handoff said `#24-journey` *"unblocks the thing that is killing runs"*. **It does not.**
The counter the ladder names is Machop @ FIERY_PATH, and measured after the fix: a warp route
to FIERY_PATH **is** found (2 candidates, both ROUTE112 doors) and **neither first leg is
walkable**, because of the Rock Smash choke. The planner was never the blocker there — see
**KI-41**, which is now the thing standing between the counter chain and acting.

## KI-41 — The Mauville→Route 112 corridor is sealed by a ROCK SMASH rock the planner treats as permanent (2026-07-31)

**Measured** from `rocksmash_taught.ss1` (Mauville 32,15), `probe_journey_walls.py`:
ROUTE111 column-by-column reachability, y from 139 (south, next to Mauville) northward —

```
x=17  ##########.........######.....#####..#............   last reachable y=102
x=18  #########..........#######....#####..#............   last reachable y=102, y=101 BLOCKED
x=19  ##########......#..##..####...#########...........   last reachable y=101, y=100 BLOCKED
x=20  ...####.###.#..##.###..##.###.#########...........   last reachable y=101, y=100 BLOCKED
```

The intermittent bands further south are the corridor's **one-way ledges** (they only
descend, so northbound approach is fragmented); the hard floor at **y≈100–101** is the
twin-rocks choke. `modules/story/early_game.py`'s `travel_lavaridge_to_petalburg` docstring
already names it: *"smash the twin-rocks choke from the NORTH side … column 18 needs only the
(18,101) rock"*, and notes the rocks **RESPAWN on map reload**.

**Consequences**
* ROUTE112 is **0/76** sampled tiles reachable from Mauville. FIERY_PATH's only two doors are
  ROUTE112 (11,36) and (22,10), so **Fiery Path is unreachable from Mauville** until that
  rock is smashed — and Fiery Path's Machop is the counter `#24-counters` names for Norman.
* The story only gets past it because `travel_to_fallarbor` / `travel_lavaridge_to_petalburg`
  hand-code a `_smash_rock` at exactly that coordinate. **Nothing generic does.**

**Why the planner cannot see it.** `calculate_path` models a Rock-Smash rock via
`dynamic_collision_flag` / `dynamic_object_id`, i.e. as an obstacle that *is* impassable right
now. That is CORRECT — the bot genuinely cannot walk through it — but it means every generic
"can I get there?" answer is a NO that a single field-move would turn into a YES.

**Shape of the fix (NOT built).** When a journey leg fails, ask whether a smashable rock
(or a cuttable tree) sits on the blocked corridor, and if the party has the move and badge,
clear it and re-plan. `_smash_rock` already exists and is idempotent. The rock coordinates
must come from map data or the decomp, never from memory. ‼ Bound it: a rock that respawns
must not become an infinite smash-and-retry loop.
