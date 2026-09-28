# 2026-09-27 — USER RULING 20 Phase 2 (open the catch-4 fence): BUILD SPEC — a NOTE, not truth

- **Worktree:** `C:/Remote Projects/pokebot-wt-ch24`, branch `wt/restock`, HEAD `0ea034c3`.
- **Paths:** code is under `sandbox-pokebot/`, tools under `tools/story-dev/`.
- **Sources:** five recon reports and one refuter. Only claims the refuter confirmed, or that I read myself, are used. Everything else is marked UNVERIFIED.
- **Method:** nothing was edited and nothing was run.

**Already ruled, so not asked again** (from `06-DECISIONS-LOG.md`):
- Catches join the party up to 6 (06:7681-7682).
- Gym-TM recipients get no protection (06:7684-7686).
- Shedinja is RULING 22 (06:7655).
- The pre-gym-1 cap and faint bail are deferred to this phase (06:7546-7571).
- Weighting the level gap in the lead choice is ruled out (06:1239-1241; `team_policy.py:248-250`).

## 2. What stops catching today (confirmed)

| Gate | FILE:LINE | Stops when |
|---|---|---|
| G0 resource | `story_mode.py:1888` → `counter_hunt.py:448-479` | 1 ball or fewer (`:477`) |
| G1 pre-gym-1 target | `story_mode.py:1894-1899` | `battler_count >= party_target` (eggs excluded, `:2405`) |
| Target | `story_mode.py:2195` in `reset_per_run_state` (`:2101`) | `= 4`. Its only readers are `:2406` and `:4619` |
| G2 team loop | `early_game.py:2680-2718` | the party reaches its target (`:2701`, `:2715`); guard > 250 (`:2703`); a failed restock (`:2706-2711`). It has no "nothing admissible" exit |
| G3 dex fence | `story_mode.py:1902-1908` | after gym 1, the party is below 6. It returns before every later gate |
| Later gates | `:1909`, `:1917`, `:1924-1925`, `:1926`, `:1928`, `:1936`, `:1944-1947` | a hunt is armed; training; spare balls ≤ 10 (`:1635`); the PC is full; anyone is damaged; 2 or more attempts (`:1642`); more than 10 expected throws |
| Survival mode | `story_mode.py:3920-3938` | 3 or more defeats on the map. It flees before the dex branch |

**Balls are restocked only at 1 or fewer, and only at `RUSTBORO_MART`** (`early_game.py:2488`). The triggers:
- `early_game.py:2709`;
- `early_game.py:5046`;
- `counter_hunt.py:542`. This one is effectively dead: `story_mode.py:2818` checks `resource_blocker()` with no yield before `hunt()` at `:2850`.

Nothing restocks at the dex reserve.

## 3. Live evidence (`#27-batch0927`, 25 runs, refuter recount)

- **Party at badge 1:** 4 in 25 of 25 runs.
- **Before badge 1:** 93 attempts and 75 catches, all "-> party", exactly 3 per run.
- **After badge 1:** 37 attempts and 28 catches, all "-> box". **No dex catch at party 4 or 5.**
- **8-badge runs ending at party 5:** three (P2r3, P2r6, P4r2). With P2r2 (party 6), four such runs made no dex catch after badge 1.
- **Post-badge-1 verdicts at a full party**, deduplicated per species and reason (`story_mode.py:1654-1662`): admitted 36; reserve 153; training 99; not full strength 82; hunt armed 3.
- **223 party-size refusals happened at 10 balls or fewer.**
- **Nine of 25 runs** held 11 balls or fewer at badge 1.
- **Five of 25 never bought a ball:** P2r2, P2r5, P3r2, P3r3 and P4r4. P2r2 peaked at ₽85,951 with 5 balls or fewer.
- **Bails:** 10 in total, 6 on the reserve and 4 on a faint.
- **The HM spin at 1 ball derails, measured:** `P1-…-130030.log` f3503601 "Hunted for a Dive learner but never caught one (timeout/balls)", and once in `P3-…-112652.log`.
- **Not re-counted, so not used:** the per-lane split, a total of about 656 party-size refusals, zero expected-throws refusals, and 4.26 against 2.92 balls per catch.

## 4. Build order

**Step 0: fixtures. No code, and it blocks every live arm.**
- `saves/FIXTURES.md5` has no PINNED fixture before gym 1, and none with badges ≥ 1 and a known party below 6. I listed every PINNED row.
- `rustboro.ss1` and `gym1_done.ss1` exist but are unpinned. Copy each to a name no driver writes and check it with `--driver partypids`. Record PIDs, HP, balls, money, owned and badges in its row, then run `verify_fixtures.py --update`.
- Premises to confirm (UNVERIFIED):
  - `rustboro.ss1` holds a party of one, Mudkip L13 (`ai-research-notes/2026-09-27-pregym1-cap-RECON.md:62`).
  - `gym1_done.ss1` was captured after Roxanne was beaten "at 21 HP" (`12-STORYMODE-DESIGN.md:2572-2575`), so it is probably not at full HP.
- **The lever:** `--set-balls N` (`story_harness.py:32`, `:28140-28156`). Use it in every arm so the reserve cannot mask the flag.

**T. Telemetry (Phase 1 item 10). Log-only; no flag, on purpose, because every arm needs it.**
- **Sites:**
  - M5: `debug_logger.py:172`
  - M3: `:410-430`
  - M1: `story_mode.py:3750`, `:3785`, `:3894`, `:3992`
  - M2: `:2240`
  - M6: `early_game.py:2680-2718`
  - O3: `:2654`
  - M4: `badge_log.py:253-299`
- **Driver:** `storyresume` on `post_mtpyre.ss1` (PINNED), with `--set-balls 30`.
  - Party 6 and an empty box come from the `boxcatch` docstring (`story_harness.py:1678-1700`); UNVERIFIED by load.
- **Discriminator:** at 6/6 with 30 spare balls the fence already admits, so an unowned wild is caught.
  - Zero `[CATCH] start` lines means VACUOUS.
  - Count the "not at full strength" verdicts that come before the first heal.
- **Prediction:** each `start kind=dex` has exactly one `end`. When the catch succeeds, `dest=box`, the PID is new in the box, and `box` rises by 1.
- **Fault arm:** `POKEBOT_R20_FAULT_NOCATCHEND=1` suppresses M2. The grader must report "start without end".

**B. Restock at the reserve (Phase 1 item 8). Flag `POKEBOT_R20_BALL_RESTOCK`, default 0.**
- **The predicate:** a pure `ball_restock_plan(spare, badge7, center, money)`. It fires only when all of these hold:
  - spare ≤ 10 (`items.py:447-448`, Master Ball excluded);
  - not `BADGE07_GET`;
  - the centre is `RustboroCity`, the only proven stand;
  - money − cost ≥ a floor (₽2,500 is a judgement).
- **What it does:** buys 10 or 20 and logs O3.
- **Where it runs:** after the heal's stable-exit loop (`higher_level_actions.py:766-774`), guarded like the rotation piggyback (`:625-638`: `reraise_if_aborting`, `_piggyback_report`).
  - `buy_poke_balls` ends inside the mart (`early_game.py:2597-2612`), so it must walk out.
- The three mandatory triggers stay untouched.
- **Driver:** `storyresume` on the pinned Rustboro copy, with `--set-balls 5`.
- **Discriminator:** spare is 5 in both arms. The arms differ only if money at load ≥ floor + ₽2,000; otherwise the run is vacuous.
  - Control: `--set-balls 20`, where neither arm buys.
- **Prediction:** on, one `[BALLS-BUY]` at the first Rustboro heal; off, none.
- **Fault arm:** `POKEBOT_R20_FAULT_RESTOCKLATE=1` drops the badge-7 clause. A pure case with badge 7 must then go red.
- **Caveats:**
  - The heal is diverged upstream code, so this needs a DIVERGENCE-LOG entry.
  - It breaks the heal's "piggyback, do not detour" contract (`:617-624`).
  - Whether any caller assumes the player stands at the PC door afterwards is UNVERIFIED.
  - Any other mart first needs a live `probe_mart_reachable.py` stand.

**P2-a. Pre-gym-1 target of 6. Flag `POKEBOT_R20_TEAM6`.**
- **Change:**
  1. Set `:2195` to 6 when the flag is on.
  2. Add an egg bound: `:1897` also requires `party_slots_used < 6`, and `early_game.py:2701/:2715/:2717` get a raw-slot bound. This is defensive; the refuter says there is no egg source before Route 117 (UNVERIFIED).
  3. Add a logged "nothing admissible left" exit that reads the land table the way `story_mode.py:3450-3456` does.
- **First, a new gate** (the R-a gap): `probe_catch_team_target.py`. It builds `StoryMode()`, calls `reset_per_run_state()`, and asserts 4 with the flag off and 6 with it on, at both readers.
- **Driver:** `storyresume` on the pinned Rustboro copy, with `--set-balls 30` and `--frames`.
- **Discriminator:** both arms catch up to 4. They diverge only if, at 4, more than 1 ball remains and at least one unowned land species is left at Route 116 (11,7) (`early_game.py:2078`).
  - Compute that at load. I could not determine the species list.
- **Prediction:** off, `[CATCHTEAM] exit reason=target party=4`; on, `party=6` or `reason=none_left party=5`. No `guard` exit in either arm.
- **Fault arm:** `POKEBOT_R20_FAULT_TARGETLOOP=1` passes 6 to the fence but keeps `catch_starter_team(4)`. The new gate must go red, and the live on-arm must stop at 4.
- **Refuter:** this is not a clean re-run of `#24-partycap`. A party of 6 at badge 1 starts box-catching at once and drains the balls to 10.

**P2-a2. Pre-gym-1 faint bail and attempt cap. Flags `POKEBOT_R20_PREGYM_BAIL` and `POKEBOT_R20_PREGYM_CAP`.**
- **The bail:** at `:3992`, return a dex-only strategy that bails on a faint only.
  - `StoryDexCatchStrategy` also bails at 10 spare balls or fewer (`story_mode.py:102-105`, read), which is normal before Rustboro. A recon note gives about 6 balls at that point (pregym1 RECON:54-56).
  - Never edit `StoryCatchStrategy`: the shiny directive inherits from it (06:4920-4926).
- **The cap:** 2 or more. A cap of 1 was measured harmful (06:7546-7571), and the attempt counter is shared across gym 1 (`:3955`).
- **Proof:** pure cases first, in `probe_dexcatch_bail.py` and `probe_dexcatch_rate.py`.
  - No pinned fixture stages a faint. Whether `--inject-weak` (`story_harness.py:29`) can is UNVERIFIED.
- **Fault arm:** the existing `POKEBOT_DEXCATCH_FAULT_NOBAIL=1` (registry 29:143).

**P2-b. Open G3. Flag `POKEBOT_R20_OPENFENCE`.**
- **Change:** a keyword `open_fence: bool = False`. It needs the default, because a required argument crashes every probe `_call`.
  - When it is true, skip `:1902-1908` and fall through to `:1909-1947`, so every later gate still applies.
  - The reason at `:1948` becomes "joins the party" below 6; keep "goes to the PC box" at 6.
- **Driver:** `storyresume` on the pinned `gym1_done` copy, with `--set-balls 30`.
- **Discriminator:** party below 6 (to confirm), 30 spare balls, badge 1.
  - The HP is likely not full, so only encounters after the next heal can differ.
  - Grade: `[CATCH] start kind=dex` with `party=` below `6/6`: 0 when off, at least 1 when on.
- **Control:** `post_mtpyre.ss1` (party 6). Its verdicts must be identical in both arms.
- **Prediction:** off, every verdict is "runway"; on, at least one "joins the party" and a new party PID.
- **Fault arm:** `POKEBOT_R20_FAULT_OPENNORESERVE=1` skips the reserve for party joins. A pure case (party 4, spare 10) must then go red.

**P2-c. Hunt-armed first (the design's C17). Flag `POKEBOT_R20_HUNTFIRST`.**
- **Why:** the party path of `catch_confirmed` is species-blind (`counter_hunt.py:426-428`, used at `:599-604`). A pre-gym-1 catch during a counter hunt ends the spin, and the verdict at `:616` finds nothing.
- **Change:** move `:1909` above `:1894`. Leave `training` where it is (`early_game.py:2348`).
- **Proof:** a pure case (pre-gym-1, battlers 2, armed): admitted when off, refused when on.
- ⚠ The probe's own "C17" (`probe_dex_catch_fence.py:162`) is a trainer case, not this one.

**Batch (Phase 3):**
- **Arms:** A1 (all new flags off) against A2 (B, P2-a, P2-a2, P2-b and P2-c on), with T in both.
- **A0 cannot be built from flags:** Phase 1 ships always-on, with fault arms only (29:148-156).
- **Stratify by starter.** Compute n from the baseline before registering.

## 5. What breaks, and who covers it

| Risk | FILE:LINE | Cover |
|---|---|---|
| F1: counters in the box are never trained; the hopeless test ignores level (a Geodude of L11 or more with Rock Throw counts) | `story_mode.py:2903-2912`, `:2683-2713`, `:2037`; `counter_hunt.py:389` | NEW WORK (Phase 1 left H3) |
| F2: the heal's make-room deposit boxes the lead just chosen | leads at `:4924-4925`, `:5120-5124`, `:5174-5177`, `:5348-5349`, `:5495-5503`; victim `pc_trip.py:158-168` | NEW WORK: re-pick the lead after the heal. 06 accepted only H2 |
| F3: the HM hunt's `before` is taken before the walk, so a catch or spawn en route raises "(timeout/balls)" | `early_game.py:4993`, `:5050`, `:5054`, `:5056`, `:5068`, `:5074-5076` | NEW WORK: arm, walk, then snapshot identities, as `counter_hunt.py:558-580` does |
| F4: the RULING 21 swap-back refuses after an evolution | `pokemon_league.py:2235-2238`, `:2344-2352`; `story_mode.py:678-687` | NEW WORK (an increment-B bug) |
| KI-78: matching on PID only | `pc_trip.py:90-128`, `:535-551` | NEW WORK, before `#27-shedinjahunt` |
| No Shedinja at a full party | `counter_hunt.py:408-415` | RULING 22 |
| Ball drain | §3 | B |
| Pre-gym-1 catch losses | — | P2-a2 |
| The Route 116 spin with nothing left to catch | `early_game.py:2701-2718` | P2-a (3) |
| A pre-gym-1 hunt ended by an off-type catch | above | P2-c |
| Training and damage refusals (181) | `story_mode.py:1917`, `:1928` | OPEN, question 2 |
| An ambiguous "no money" raise | `early_game.py:5048` against `:2659-2661`, `:2668-2673` | NEW WORK, small |
| A fresh low-level catch leads a boss | `team_policy.py:291-297` | OPEN; the only lever left is party membership |

## 6. Gates that go red (keep every flag-off case as the regression arm)

- **R-a:** no gate asserts the target today. Add `probe_catch_team_target.py`.
- **`probe_dex_catch_fence.py`:**
  - C3 (`:131-132`) and `FAULT_MUST_BREAK` (`:170`) stay as the flag-off cases. Add flag-on cases.
  - Keep the reason substrings the cases match: "pre-gym-1" (`:118-119`, `:127-128`), "target" (`:120-121`, `:129-130`) and "PC box" (`:133-134`, `:158-159`).
- **`probe_dexcatch_rate.py`:** R2 (`:87-89`) and `fires_pre` (`:207-214`) must become conditional on the flag.
- **`probe_dexcatch_bail.py:78-81`:** it pins the `:3992` line and exactly one `StoryDexCatchStrategy()` site. Update it for P2-a2.
- **`lint_docs.py` R6 (`:307-320`):** every new flag needs a row in 29, in the same commit.
- **`audit_doc_citations.py`** (`run_gates.py:327`) will probably flag line drift. Fix it with `fix_doc_citations.py`.
- **`repro_heartbeat_emits.py:110`:** add `box=` and `badges=`.
- **Advisory only:** `probe_dexfence_opportunity.py:74`.
- **Unaffected:** four repro scripts whose stubs lack `_dex_catch_attempts` and always hit "fence errored": `repro_hm_move_replace_loop.py:281`, `repro_hm_replace_valve_forced.py:217`, `repro_ki65_unbound_party_index.py:415` and `repro_movelearn_fault_recovery.py:194`.

## 7. Telemetry to add first

- **Write every line through `_log_story_event(msg, CAT)`** (`story_mode.py:5888-5902`), with no tag inside `msg`.
- **Leave the existing `[DEXCATCH]` line alone.** It prints its tag twice, but nothing parses it.
- **Give each emit its own `try`.** The catch branches sit in `try/except: pass`, so a logging error would silently cancel a mandatory catch.
- **Never write `:L<digits>` in a field** (`analyze_endless_batch.py:93`).

```
M1 [CATCH] start kind=<team|dex|hm|counter|shiny> sp=<Name>#<dex> lv=<n> attempt=<n|-> badges=<n> party=<raw>/6 box=<n> spare=<n> exp_throws=<x.x|-> map=<g>,<n>
M2 [CATCH] end kind=<…> sp=<Name>#<dex> end=<caught|out_of_balls|bail|fled|foe_fled|lost|other> outcome=<BattleOutcome> thrown=<n> frames=<n> dest=<party|box|none|?> pid=<8HEX|-> party=<raw>/6 box=<n> spare=<n> badges=<n> bail=<slug|->
M3 [hb] … money=<n> box=<n> badges=<n>
M4 [BADGE] n=<1-8> party=<raw>/6 box=<n> owned=<n> spare=<n>
M5 run header env: every POKEBOT_* by prefix scan (today only POKEBOT_FODDER_RULE)
M6 [CATCHTEAM] exit reason=<target|none_left|guard|no_balls|abort> target=<n> party=<n> spare=<n> frames=<n> loops=<n>
O3 [BALLS-BUY] why=<mandatory|reserve> mart=<g>,<n> bought=<n> spare=<a>-><b> money=<a>-><b>
```

- **Where the values come from:**
  - `spare`: `number_of_balls_except_master_ball`. The heartbeat's `balls=` includes the Master Ball (`debug_logger.py:719-722`).
  - `box`: `counter_hunt._box_count()` (`:191`).
  - `badges`: `pc_trip.badge_count()` (`:72`).
  - `exp_throws`: `_expected_throws_for` (`story_mode.py:1665`).
- **M2 runs from `on_battle_ended`** (`:2240`) against a `_catch_ctx` that `reset_per_run_state` resets.
- **`thrown` can be off by 1** if Pickup adds a ball. Cross-check it against the next `balls=`.
- **Set `end=out_of_balls` explicitly at the flee;** never infer it from spare being 0.
- **Whether reads inside `on_battle_ended` already see the caught mon is UNVERIFIED.** Prove `dest` and `pid` on the T driver first.

## 8. Open questions for the user (06 checked; policy only)

1. **Money:** before badge 7, may the bot spend money on Poké Balls for Pokédex catches, and how much per run at most? The League basket costs ₽54,300 (`victory_road.py:440-449`), and RULING 18 keeps back ₽1,000 (`league_reserve.py:53`).
2. **"Always catching":** should catching still pause while a team member is hurt (82 refusals) or during a training grind (99)? The health check is a design choice (06:4920), not a ruling.
3. **Retries:** a species is attempted at most twice per run (`story_mode.py:1642`). Is that acceptable?

## 9. What the refuter killed

- **P4r1's restock** came from the Surf HM hunt, not from a counter hunt.
- **P2r2 ended at party 6**, not 5.
- **Batch-log line numbers are offset from the worktree:**
  - `story_mode.py` lines after 2222 sit 6 lower;
  - `counter_hunt.py` gained 70 lines at 326.
- **"Castform is declined at a full party" is wrong.** The decomp's `givemon` sends it to the PC, and B only declines the nickname. The comments at `early_game.py:7301-7302` and `:7371-7373` are wrong, and design item 9 needs no build.
- **"An L7 Geodude has Rock Throw" is wrong:** it learns it at L11.
- **The fence report missed lint R6.**
- **"C17 is defined nowhere" is wrong:** the probe has a different C17.
- **"Change (a) is exactly `#24-partycap`" is wrong.**
- **"Opening G3 plus a restock makes catching constant" is not supported:** training and damage refusals (181) outnumber reserve refusals (153).

**Could not determine:**
- the Route 116 species;
- whether 6 battlers are reachable before gym 1;
- the fixture premises;
- how often F1–F4 fire;
- which citations drift;
- whether a Gen 3 deposit compacts slot 0, which F2 depends on.
