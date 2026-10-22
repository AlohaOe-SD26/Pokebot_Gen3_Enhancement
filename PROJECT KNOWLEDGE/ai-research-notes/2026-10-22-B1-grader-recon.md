# B1 + N8 grader recon (2026-10-22): the step-5 grader's data path, check by check

> A NOTE, not truth. One read-only recon agent at HEAD `f31dd6d1`. Tags: READ (source read), MEASURED (command run),
> INFERRED (reasoned), UNKNOWN. All file:line refer to `ai_player/gates/rate_step5.py` (R), `ai_player/gates/live_step5.py`
> (L), `ai_player/gates/play_harness.py` (H), `ai_player/brain/goals.py` (G), `ai_player/mode.py` (M),
> `ai_player/personality.py` (P) unless named. No rate_*/live_* driver was run and the ledger was not written.

## 0. Bottom line

- Of the 67 checks in the newest graded sweep, 15 are forced PASS. 7 come through `P2_REPORTED`, and 8 are written
  `(True, ...)` directly. That leaves 52 graded (MEASURED: `grep "^  \[PASS\]"` on `evidence/2026-10-16-step52-RATE.txt`
  gives 67 and `[FAIL]` gives 0; forced rows #4,14,15,28,29,31,33,42,43,46,51,53,65,66,67).
- **Graded and GAME-only (no AI input):** 9 checks.
  - CH1 reached and first try; CH1 and CH2 whiteouts; the recorder saw every battle; NOTRAIN mechanism.
  - NOTRAIN effect; NOHINTS slower; WALLY reached.
  - Instrument-health rows: places read, waits read.
- **Every curiosity check takes its WINDOWS from the AI's log**, even where the values are the game's.
  - Spans come from `goal_spans(actions)`. Kinds, `story_moved`, the drop flag and the detour's place come from the AI's
    END record.
  - Frames are aligned by the AI's first record frame (`offset`, R:1323).
- **The AI computes the grader's own yield rule.** `goals.py` YIELD_TILES_MIN 8 / YIELD_TILE_RATE 20 at G:571-572 are the
  same formula as R:915. The AI uses it to decide whether a goal is done (M:530).
  - The sweep says the two paths "agree in 717 of 717 goals" (row #51).
- **The ledger sha does not cover the AI constants the grader imports.** `registered_numbers` (R:2035-2041) hashes none of
  ERRANDS, ERRAND_KINDS, ASIDE or MAX_LOSSES.
  - So editing `personality.ERRANDS.train_min_steps` moves the TRAINED bound without changing the registered sha
    (READ + INFERRED).

## 1. The checks (rate_step5) — bound, quantity, inputs

Data sources (READ):
- `run_one` (R:526-578) parses the harness's `PLAY` json (`data`) and the AI's `actions.jsonl`.
- `data` holds (H:694-721):
  - **GAME:** `story` = StoryRecorder.result (H:208-211: changes, battles, steps, captures, item_flags, blips);
    `story_truth` = end marks/stats/items (H:716); `truth` = hands_harness.truth (H:715); `waits_game` = WaitRecorder
    (H:287-292); `places` = PlaceRecorder (H:514-519: new_tiles, stays, moves, texts, battles, push).
  - **HARNESS:** `frames` (the loop count, H:676-695); `presses` (HarnessControls).
  - **AI:** `report` = `brain.play_report`; `reason` = the brain's stop string; `lines`; `world_file` = the AI's
    world.jsonl.
- Tag key: G = GAME/harness recorder; A = AI (actions.jsonl, world.jsonl, report, reason, AI constants).

| # | Check (label, line) | Bound (name = value, line) | Quantity (quoted) | Inputs |
|---|---|---|---|---|
| 1 | CH1 POKéDEX reached, R:1449 | CH1_REACHED_MIN 0.8 :302 | `ch1["reached"] >= BOUNDS["CH1_REACHED_MIN"] * n`; `reached = bool(end.get("RECEIVED_POKEDEX_FROM_BIRCH"))` R:1409 | G: story_truth.marks |
| 2 | CH1 first try, R:1451 | CH1_FIRST_TRY_MIN 0.8 :303 | `trainer_before = rival["stats"]["trainer_battles"] - starter_mark[...]` R:1291; `first = ... == 1` R:1429 | G: StoryRecorder.changes[].stats |
| 3 | CH1 TRAINED by the game, R:1457 | CH1_WILD_WON_MIN 3 :312; CH1_TRAIN_STEPS_MIN 60 :320; CH1_TRAIN_STEPS_SHARE 0.9 :321; plus `ERRANDS.train_min_steps` (AI, R:602-605) | `trained_by_game`: `game_train_steps >= train_steps_min_run(row) and game_train_won >= ...` R:629-630; AND `r["train_steps_before_rival"] < train_steps_min_run(r)` fails R:1456 | G: StoryRecorder.steps (`steps_counted` H:602), StoryRecorder.battles. A: the WINDOWS `training_windows(actions)` R:680-705 (goal records, `decide "roam N"`, roam metrics); `offset` R:1323; `rival_judge` (AI end note `fight_prep.judged_by`) R:1344; `rival_actives` (goal extra `active`) R:1404; `train_steps_before_rival` = AI roam metrics steps R:1298; P.ERRANDS |
| 4 | CH1 (reported) wild won anywhere, R:1467 | none (forced True) | — | G |
| 5 | CH1 spins, R:1480 | CH1_SPIN_MAX 0.02 :326; CH1_SPINS_PER_SEED 5 :327 | `pooled = spins / steps`; spins/steps = `sum(extra.spins/steps)` of AI `roam`/`metrics` records R:1299-1300 | A only |
| 6 | CH1 catch-all idle, R:1484 | literal 0 | `generic = count(decision=="watch" and reason startswith GENERIC_BUSY)` R:1301 | A only (a check of the AI's reason labels) |
| 7 | CH1 whiteouts, R:1485 | CH1_WHITEOUTS_MAX 2 :325 | `lost = [b ... outcome == 2]` R:1317 | G: StoryRecorder.battles |
| 8 | CH1 REST RULE, R:1490 | literal 0 breaches, >=1 occasion | `roam_breaches(actions)` R:732-762: `hp = extra["party_hp_end"]`, `heal_below = ERRANDS[active].heal_below` | A only: AI world/battle records, AI goal `active`, P.ERRANDS (import R:738) |
| 9 | recorder saw every battle end, R:1500 | literal 0..1 | `game_stats.total_battles - battles_ended` | G (instrument) |
| 10 | ALL PLANS losses report == told == game, R:1509 | literal equality | `losses_ai == losses_told == losses_game` | A: `report.losses`, tell lines; G: battles outcome 2 |
| 11 | NOTRAIN mechanism, R:1518 | NOTRAIN_WILD_LESS True :328 (the key is NOT read; the code uses `b < a`) | the sums of `wild_won_before_rival` (R:1315: `since < b["f"] <= rival_frame`) | G |
| 12 | TRAINED check tells training from none, R:1526 | as #3 | `trained_by_game(r)` for the NOTRAIN rows | as #3 (AI windows) |
| 13 | NOTRAIN effect, level paired, R:1548 | NOTRAIN_LEVEL_PAIRED_MIN 0.5 :331; literal -2 | `level_at_rival = max(row[1] for row in rival["party"])` R:1305-1306 (the `party_now()` decoder at the mark change, H:199) | G |
| 14,15 | NOTRAIN HP share; first-try rate, R:1553, 1559 | none (forced True) | — | G |
| 16 | DEADREST, R:1565 | literal >0 vs 0 | `rest_breaches`, `roam_low_ends` | A only |
| 17 | NOHINTS slower, R:1573 | NOHINTS_SLOWER True :332 (the key is NOT read) | reached count, or the sum of `dex_frame` (the change frame) | G |
| 18 | STOP, R:670 (`stop_verdicts`) | STOP_WITHIN 6000 :298; STOP_REASON :295 | `r["reason"] == STOP_REASON and losses_game==1 and losses_told==1 and losses_ai==1 and 0<=after<=STOP_WITHIN` R:651-652 | A: `reason`, report, tells; G: `first_loss_f`, losses; H: frames |
| 19 | STOPDEAD, R:670 | same | R:654-655 | same |
| 20 | STALL PROPERTY, R:1823 | AWAIT_MAX 300 :342 | `await_ai_max >= bound or await_game_max >= bound` R:1822 | A: `await` records R:765-771; G: WaitRecorder.longest R:1395 |
| 21 | the stall's second path read, R:1828 | none | `await_game_samples` | G |
| 22-24 | STALL1/2/3, R:1836 | STALL_ARM_HITS_MIN 1 :345 | both paths `>= bound` R:1835 | A+G |
| 25 | two paths agree (stall), R:1845 | none | `(ai>=b) != (game>=b)` | A vs G |
| 26 | ASIDE comes back, R:1851 | ASIDE_STREAK_MAX 10800 :407 | `aside_streaks(actions)` R:1076-1096, keyed by `brain.goals.ASIDE` (import R:1081) | A only |
| 27 | GO goal after its page, R:1859 | literal | `told_before(actions)` R:1201-1221: AI `read` records vs AI go-goal reasons | A only |
| 28 | INTENT MIX CH1, R:1873 | MIX_MIN 0.30 :348; CURIOSITY_MIN 0.06 :351 | `intent_mix` R:816-854 | A spans; G unproductive set; ERRAND_KINDS import R:827. **forced (P2)** |
| 29 | FREE CH1, R:1889 | FREE_RUN_MIN 0.02 :381; FREE_MEAN_MIN 0.05 :383 | `mix.free_share` | **forced (P2)** |
| 30 | SEED DIVERGENCE, R:1896 | DIV_GOALS_MIN 0.30 :355; DIV_TILES_MIN 0.30 :356 | `goals = edit_distance(_sequence)/longest`; `tiles = 1 - |a&b|/|a|b|` R:1165-1167 | A: `goal_sequence(actions)` R:1063; `visited_tiles(world_file)` R:1138-1150 (AI world.jsonl `visits`) |
| 31 | ERRANDS_OFF moves mix, R:1909 | MIX_DROP_MIN 0.04 :358 | the curiosity_share drop | **forced (P2)** |
| 32 | ERRANDS_OFF moves divergence, R:1914 | none (`>`) | `div_on.goals_mean > div_off.goals_mean` | A |
| 33 | BEELINE fails curiosity, R:1921 | FREE_CONTROL_FAILS_MIN 0.8 :386 | — | **forced (P2)** |
| 34 | OFF THE BEELINE, R:1931 | OFF_SEEDS_MIN 0.6 :391; OFF_RATIO_MIN 1.3 :392 | `off_beeline` R:1178-1198 on `_tiles` | A: world.jsonl visits |
| 35 | ERRANDS DIFFER BY SEED, R:1942 | CUR_DIV_MIN 0.5 :402 | `sequence_divergence(.., "curious_sequence")`; `curiosity_sequence(actions)` R:1099-1111 | A only |
| 36 | NO SPEEDRUN (time), R:1961 | SLOWER_THAN_BEELINE_MIN 1.0 :363; DEX_FRAMES_MAX 300000 :365 | `outside = dex_frame - needs(a)` R:1950; `ratio = sum x / sum y` | G: dex_frame; A: needs = the AI's spans of NEED_KINDS (R:1058-1060) |
| 37 | NO SPEEDRUN without the dice, R:1979 | NOBATTLE_RATIO_MIN 1.02 :398; NOBATTLE_SEEDS_MIN 0.6 :399 | `time_to_dex` R:1028-1055: `end` = the AI's tell "MILESTONE ... done at f"; `battle` from the AI digests `digest.split(" ")[1:2] == ["battle"]`; `outside_nb = end - begin - need - battle` | A only |
| 38 | LOSE3, R:2003 | LOSE3_REACH_MIN 0.6 :410; `mode.MAX_LOSSES` (import R:1992); STOP_WITHIN | `row[4] >= MAX_LOSSES`; `reason == want and ai==told==game==MAX_LOSSES` R:2000-2002 | A: reason, report, tells; G: losses, last_loss_f |
| 39 | PATIENCE, R:2015 | PATIENCE_REACHED_MIN 0.8 :370; SMALL_PATIENCE 40000 :195 | reached (G); `train_span` from the AI train spans R:1337-1338 | G+A |
| 40 | PATIENCE_OLD, R:2022 | PATIENCE_OLD_STOPS_MIN 0.8 :371 | `reason.startswith("play: stuck: no progress for")`, `last_goal == "train"` | A |
| 41 | CH2 WALLY, R:1762 | CH2_REACHED_MIN 0.8 :423 | `wally` R:1387-1388 (end marks) | G |
| 42 | CH2 intent mix, R:1770 | MIX_MIN | — | **forced (P2)**; in #34 the old bound "did NOT hold" (row #42) |
| 43 | CH2 free, R:1777 | FREE_RUN_MIN | — | **forced (P2)** |
| 44 | CH2 A NEW PLACE IS NEW, R:1780 | literal | `new_place_draws(actions, known_maps(world_in))` R:1224-1245 | A only (AI draw labels vs the AI's start world memory) |
| 45 | CH2 whiteouts, R:1784 | CH2_WHITEOUTS_MAX 2 :425 | `losses_game` | G |
| 46 | CH2_OFF under floor, R:1789 | CH2_OFF_UNDER_MIN 0.6 :428 | — | **forced (P2)** |
| 47 | CH2 NOBATTLE, R:1800 | CH2_NOBATTLE_RATIO_MIN 1.15 :432; CH2_NOBATTLE_SEEDS_MIN 0.7 :433 | `time_wally = time_to_dex(actions, CH2_TARGET, since_start=True)` R:1389 | A only |
| 48,49 | CURIOSITY BY YIELD CH1/CH2, R:1627 | YIELD_RATE_MIN 0.6 :450; YIELD_TILES 8 :861; YIELD_TILE_RATE 20 :866; SEEING :867; YIELD_SLACK 30 :870 | `rate = made/seeing`, the sums of `seeing_productive`/`seeing_frames` R:1362-1363 = **AI span frames** where `game_yield(...)["productive"]` R:886-917: `seen = tiles >= YIELD_TILES and (kind not in SEEING or tiles*1000 >= YIELD_TILE_RATE*walking)`; a detour also `and there` R:973 | G: PlaceRecorder new_tiles/stays/texts/battles, StoryRecorder captures/item_flags, `position_at` (moves). A: spans `goal_spans(actions)` R:951; kind; `story_moved`; `mine.get("dropped")` R:956; the detour `place` R:968; `offset` |
| 50 | NO LOAFING, R:1636 | LOAF_FRAMES_MAX 4000 :457 | `loafing_frames = sum(row["walking"] ... if not row["game"])` R:924; `walking = end - start - battle` R:914 | G: battle stretches and productive; A: span bounds |
| 51 | (reported) yield agree, R:1643 | forced | `yield_agree` | A vs G |
| 52 | LOAF control, R:1650 | LOAF_FAILS_RUNS_MIN 1 :464; YIELD_RATE_MIN | as #48/#50 on LOAF | as #48 |
| 53 | (reported) ERRANDS_OFF, R:1657 | forced | — | — |
| 54 | CURIOSITY SPACED, R:1663 | SPACING_ROW_MAX 3 :471 | `curiosity_streaks(actions)` R:978-992 (the goal kinds in a row) | A only |
| 55 | GREEDY, R:1671 | GREEDY_FAILS_MIN 0.5 :474 | as #54 | A only |
| 56 | DETOURS ARRIVE, R:1681 (forced FAIL at R:1690 when there are none) | ARRIVE_MIN 0.5 :480 | `placed = d[3]` (the AI's chosen place), `there = d[5]` (`game_reached`) | A: place; G: `position_at(places, stop+YIELD_SLACK)` R:970 |
| 57 | DETOUR'S WORD TRUE, R:1686 | literal | `bool(said) != bool(game)` | A (`reason startswith "reached"`) vs G |
| 58 | PUSHING PROPERTY, R:1695 | PUSH_MAX 4000 :491 | `push_ai >= bound or push_game >= bound` | A: `push_ai` R:995-1000 (end extra.pushes, push records); G: PlaceRecorder.push.longest R:1353 |
| 59 | two paths agree (push), R:1701 | none | — | A vs G |
| 60 | BLOCKED, R:1708 | BLOCKED_REACH_HITS 3 :495; BLOCKED_HITS_MIN 1 :496; BLOCKED_REACH_MIN 0.1 :497 | `person_blocks` R:1003-1016 (the AI idle reasons "someone stands in the way") + both push paths | A reach, A+G push |
| 61 | PLACE LEFT IS NO NEW PLACE, R:1716 | literal | `new_place_left_before` R:1259-1275 | A: draw labels, `map_keys(world_file)`; G: PlaceRecorder.stays |
| 62 | ASK STEP, R:1719 | literal | `"to ask at" in reason and "nothing was said" in reason` R:1372-1373 | A only |
| 63 | THE GAME'S PLACES read, R:1722 | none | `places_samples` | G |
| 64 | OUT OF IDEAS ONLY WITH NO LEAD, R:1726 | OUT_OF_IDEAS_LED_MAX 0 :504 | `"out of ideas" in data.reason` R:1379 | A only |
| 65-67 | (reported) R:1732, 1736, 1743 | forced | — | — |

Bounds that no check reads: NOTRAIN_WILD_LESS (:328) and NOHINTS_SLOWER (:332). Both are `True`, and the code hardcodes
the comparison (READ, R:1518, R:1573).

### live_step5 checks (step 5.2's, inside `check_hands`, L:381-414, + L:431/453-479)

Every one reads the AI's own record. A launcher run has no second path while it plays (READ L:56, L:382-383, L:408-409).
- **NO LOAFING (L:389):** `curiosity_rows(run.records, {}, 0)` (L:384) with EMPTY game data. The verdict uses
  `row["ai"]` (the AI's `goal_yield.productive`) and `walking_ai`, giving `loaf = sum(row["walking_ai"] ... if not
  row["ai"])` (L:387). The bound is LOAF_FRAMES_MAX. All inputs are AI.
- **CURIOSITY SPACED (L:399):** `curiosity_streaks(run.records)` against SPACING_ROW_MAX. All inputs are AI.
- **PUSHING (L:404):** `push_ai(run.records) < PUSH_MAX`. All inputs are AI.
- **ASK STEP (L:412):** AI goal reasons.
- **A NEW PLACE IS NEW (L:474):** the AI's draws vs the AI's start world memory, plus its own `world` transition records
  (L:470-473). All inputs are AI.
- **Reported notes, not checks:** the intent mix and free share (L:421-430); detours (L:407-409).
- **Also every arm (5.1, AI only):** the STALL property from the AI's `await` records only (L:368-376); told_before
  (L:378); asides (L:433-437).
- **GAME checks in live (end state through `truth_of`, H `truth` mode H:730-737):**
  - CH1: proofs L:594, name/gender L:596, starter OT L:603, balls L:607, told wild == GAME_STAT_WILD_BATTLES L:634.
  - CH2: WALLY L:655, captures + new PIDs L:664, heals L:668, item flags L:670.
- **AI checks in live CH1:** TRAINED from the AI's roam reports + battle records (L:623), rest rule L:529, own report
  L:554/562, spins L:641; overall pooled spins and rest occasions L:769-781.

## 2. A game-read equivalent for each AI input

| AI input | Already recorded by the harness? | If not, what a recorder would read |
|---|---|---|
| Curiosity goal SPANS/kinds (#28-29, 48-57) | NO. Goals are the AI's intent; no recorder records them. The game VALUES over any window exist: PlaceRecorder new_tiles/stays/texts/battles/moves (H:416-423, 517-519), StoryRecorder captures/item_flags (H:161-162) | A grade with no AI windows would have to pool over game windows instead (the whole run, or between story-mark changes from StoryRecorder.changes). INFERRED |
| Frame alignment `offset` (R:1323) | NO. It assumes the AI's first record frame equals the recorder's frame 0 | The harness could stamp the recorder frame into the play loop. UNKNOWN whether pad frames == loop count is checked in-process (live checks pad frames == real_frames through purity, L:10-11) |
| Training windows (#3, #12) | NO. The game's steps/battles are recorded (StoryRecorder.steps H:202-206, battles H:174-176); "won anywhere" is reported (#4) and NOTRAIN satisfies it (R:304-307) | A game proxy would need the metatile behaviour under the player (tall grass) per sample: a NEW read in PlaceRecorder. INFERRED |
| Roam step/spin reports (#3, #5) | Partly: PlaceRecorder.moves = [frame, "g:n", x, y] at each position change (H:448-449) | Spins could be recomputed from moves. Sampling every 10 frames (H:393) and running at 8 frames a tile (H:106-108) can skip a tile: INFERRED |
| Party HP at battle ends (#8, #16) | NO. StoryRecorder stores `party_now()` only at a MARK change (H:199); battle ends carry stats only (H:175-176) | `party_now()` (H:120-128) at each outcome change. The roam windows stay AI |
| Visited tiles (#30, #34) | YES: PlaceRecorder.moves (H:448-449) in `places.json` (H:693); seen tiles in `seen_tiles.json` (H:690-691) | — (the same sampling caveat as above) |
| Goal / curiosity sequences (#30 goals, #32, #35) | NO (AI decisions) | The order of maps entered (`stays`, H:446-447) is the nearest game analog. INFERRED |
| time_to_dex milestone frame + battle frames (#37, #47) | YES: the dex/WALLY frame from StoryRecorder.changes (R:1286, 1345); battle stretches in PlaceRecorder.battles (H:480-486) | The NEED spans are AI. used_pokecenter is read (H:56) but kept only at mark/battle samples, so it needs a timeline like `captures` (H:179-181) |
| Await (#20-25), push (#58-60) | YES: WaitRecorder (H:239-292), PlaceRecorder.push (H:487-512) | — |
| Detour place (#56-57) | The position is GAME (`position_at`, R:927-934); the CHOSEN place is AI | — |
| Draw labels "a new place, X" (#44, #61), ASK reasons (#62), out of ideas (#64), GENERIC_BUSY (#6), told_before (#27) | NO. These grade the honesty of the AI's own words | told_before would need each page's TEXT with its first frame. PlaceRecorder keeps only `texts = [first, last, unseen]` (H:478) and a page SET (H:692) |
| Stop reasons / losses_ai (#10, 18-19, 38, 40) | NO (the AI's loop is the subject) | — |
| map_keys (const -> key) from the AI's world.jsonl (R:1248-1256) | NO | The map constants exist in the framework's map tables (UNKNOWN which module) |

## 3. Forced PASS / (reported) sites and the verdict computation (READ, each re-read)

- **R:1467** `out.append((True, f"CH1 (reported): wild battles WON anywhere ...`
- **R:1553** `out.append((True, f"NOTRAIN (reported, not bounded): the HP share ...`
- **R:1559** `out.append((True, f"NOTRAIN (reported, not bounded): the rival beaten at the first try ...`
- **R:1592-1594** `P2_REPORTED = ("THE INTENT MIX (CH1)", "CURIOSITY THE STORY DID NOT NEED (CH1", "ERRANDS_OFF MOVES THE INTENT MIX", "THE BEELINE FAILS THE CURIOSITY BOUND", "CH2: THE INTENT MIX", "CH2: CURIOSITY THE STORY DID NOT NEED", "CH2_OFF (the beeline control's chapter 2)")`
- **R:1597-1601** `return [(True, f"(reported, 5.2 P2: ... the old bound {'HELD' if ok else 'did NOT hold'}) {text}") if text.startswith(P2_REPORTED) else (ok, text) for ok, text in results]`.
  - It is applied by `return p2_reported(out)` at R:1581.
- **R:1643** `out.append((True, f"(reported) the AI's own word on its curiosity's yield agrees ...`
- **R:1657** `out.append((True, f"(reported) ERRANDS_OFF, the beeline: ...`
- **R:1690** `out.append((False, "DETOURS THAT ARRIVE: no detour in the real code's runs (the check is vacuous)"))`.
  - ⚠ This is a forced **FAIL**, not a PASS: the A2-P7 list mislabels it.
- **R:1732** `out.append((True, f"(reported) NOHINTS (no hint ever used) ended 'out of ideas' ...`
- **R:1736** `out.append((True, f"(reported) the chats the GAME says told it nothing new ...`
- **R:1743** `out.append((True, f"(reported) THE TWO PATHS ON THE TALKS ...`
- **Verdict:**
  - R:2171 `results = verdicts(summary, rows)`.
  - R:2174 `verdict = "PASS" if results and all(ok for ok, _ in results) else "FAIL"`.
  - R:2176 `verdict, frozen_line = _TREE.seal(verdict)`.
  - R:2182 `say(f"VERDICT: {verdict} (...ledger #{entry['id']})")`.
  - R:2187 `seed_ledger.finish(entry["id"], verdict, ...)`.
  - Exit R:2191.
  - Untyped: each check is a `(bool, str)` tuple. "Reported" status exists only as a TEXT PREFIX, and `p2_reported`
    matches it with `text.startswith` (READ).
- **live_step5:**
  - L:190-191 `return bool(self.checks) and all(ok for ok, _ in self.checks)`.
  - L:781 `passed = all(run.passed for run in results) and not left and pooled_ok and rest_ok and len(results) == len(arms)`.
  - L:783 `overall, frozen_line = tree.seal(...)`.
  - L:791 `[LIVE5] OVERALL ...`.
  - The reported items there are `run.notes`, not checks (L:408, 421, 427).

## 4. AI constants that equal or target a grader bound (READ)

- **`G:340 YIELD_TILES_MIN = 8` and `G:346 YIELD_TILE_RATE = 20`** equal R:861 and R:866.
  - Used at G:571-572 `seen = made["tiles"] >= YIELD_TILES_MIN and (goal.kind not in SEEING_KINDS or made["tiles"] * 1000 >= YIELD_TILE_RATE * walking)`.
  - That sets `made["productive"]` (G:573).
  - Role: M:530 `if goal.kind in CURIOSITY_KINDS and not made["productive"]: ok = False` (the goal fails).
  - G:1059-1066: a productive goal resets `curious_since` (boredom). An unproductive one counts `memory.idle` and may mark
    the map exhausted.
- **`G:337 CURIOUS_ROW_MAX = 2`** sits one under SPACING_ROW_MAX 3 (R:471; the comment at R:465-467 says so).
  - Used at G:993 `return not self.errands_off and self.memory.curious_row < CURIOUS_ROW_MAX` and G:1246 `items = self.memory.curious_row < CURIOUS_ROW_MAX`.
- **`G:299 LOOK_DEBT = 2`.** G:1270-1272: `if self.memory.passed_new >= LOOK_DEBT: odds = max(odds, CURIOUS_ODDS_CAP)`.
  - The FREE_RUN_MIN derivation cites it (R:377-381), but that bound is forced (P2).
- **`G:304 STORY_ASIDE_FRAMES = 6000` and `G:255 LOOK_AROUND_FRAMES = 2400`** make up ASIDE_STREAK_MAX
  10800 = 6000 + 2400 + 2400 (R:403-407).
  - Used at G:1415 `left = STORY_ASIDE_FRAMES - (look.frame - began)`.
- **`P:153-161 ERRANDS`** (train_min_steps Story 80 / Catcher 100 / Trainer 150; heal_below 0.6 / 0.5 / 0.45).
  - The AI uses them at G:1290 `short = level < target or prep["steps"] < errands.train_min_steps` and at G:1086/1183
    (heal_below).
  - The grader takes its training bound as 0.9x of them (R:602-605) and its rest threshold directly (R:738, R:758).
- **`G:279 ERRAND_KINDS` and `G:282 CURIOSITY_KINDS`.** The grader imports ERRAND_KINDS (R:827) and keeps its own copy
  of CURIOSITY_KINDS (R:1021). `test_goals.py:2647-2648` asserts the two copies agree.
- **`G:277 ASIDE = "aside:"`**: imported at R:1081.
- **`M:105 MAX_LOSSES = 3`**: imported at R:1992, used at M:607.
- **`M:104 STORY_PATIENCE`**: rewritten by the EXTRA_EDITS anchor (R:198-199).
- **live_step5 imports** (L:101-106): `hands.dialogue.GENERIC_BUSY`, `options.ENV_*`, and
  `personality.choose_gender/choose_name/pick_personality`. It also calls R's `train_steps_min` for PREDICTED (L:127-129),
  so ERRANDS reaches the live bounds too.
- **R:299 `GENERIC_BUSY` is a literal COPY** of `hands/dialogue.py:73`.
- **The full grader import list** (MEASURED with `grep -n "from ai_player\."`): R:553 launcher (env only), R:602, R:738
  (⚠ not in the brief's list), R:827, R:1081, R:1992.
- **`registered_numbers` (R:2035-2041) includes none of these AI values** (READ).

## 5. How a graded sweep runs today

- **CLI** (R:2054-2069):
  - `--purpose development|graded|replay` and `--first-seed` are required.
  - `--seeds 12`, `--workers 8`, `--frames 300000`, `--target ch1_pokedex`, `--evidence-tag step52`.
  - `--plans` defaults to all 18 (R:2055-2056).
  - `--register` with `--purpose graded` writes `ledger.register(...)` and plays nothing (R:2081-2092).
- **The ledger** (`ledger.py:6-24`, READ):
  - A graded run must match a registered range, with `numbers_sha256(registered_numbers(...))` equal (R:2080, 2102).
  - Overlaps are refused. The entry is written at start ("started") and finished with the verdict + evidence.
- **Guards before the run:**
  - Disk: `preflight` needs 30 GB free (R:2094-2097). C: has 113.4 GB free now (MEASURED).
  - Frozen tree: `watch` (R:2100).
- **Each run:** a `play_harness.py` subprocess with a 7,200 s timeout (R:556). Chapter-2 runs chain in the same worker
  (R:581-594). Phase 2 is STOP/STOPDEAD (R:2152-2164).
- **Newest graded sweep, #34 (MEASURED from ledger.json and the evidence):**
  - Seeds 941-960 (20), all 18 plans, frames 300000; 260 runs (`grep -c "seed [0-9]*: {"` = 260).
  - Started 2026-10-16 01:31:53, ended 04:03:38: **2 h 31 m 45 s** wall.
  - #23 (921-940): 21:42:55 to 23:33:53, 1 h 51 m.
  - The summed run seconds over 245 rows are 65,562 s, with the longest run 530 s. That is a mean of about 7.2
    concurrent, consistent with the default 8 workers.
  - The worker count actually passed is UNKNOWN: the evidence has no workers line.
  - `--keep-runs` was used (evidence: "all 260 KEPT ... 2201 MB").
- **CPU:** 32 logical CPUs (MEASURED `nproc`); the tuner has `max_lanes: 12` (MEASURED, learner `config.json:5`).
  - With 8 sweep workers that is 20 emulator processes. No measurement of a sweep beside 12 lanes exists: during #34 the
    learner's clone was still on 8 lanes (`07-CHANGELOG.md:38099`: "Its clone is at `75c2080a` (8 lanes). It
    fast-forwards ... (12 lanes) at the next cycle (about 2:28 PM)").
  - Whether a batch was running at 01:31-04:03 is UNKNOWN.
- **Profile:** the harness boots `ai-step0-fixture` (`hands_harness.py:41`) under this checkout's `sandbox-pokebot`
  (`launcher.py:82`, `:114`).
  - The learner runs from its own clone, so the profile dirs are not shared (INFERRED).
  - live_step5 uses profile `ai-step5-play` (L:110) and runs arms in sequence (L:751).

## 6. The comparison target

- `ai_player/evidence/2026-10-16-step52-RATE.txt`, line 373: `VERDICT: PASS (GRADED, seeds 941-960, ledger #34)`.
  - Tree `7c385bbd906e0866` (HEAD 75c2080a + uncommitted diff, line 3).
  - Bounds sha `53ca1f74fdde6b0e31a342a225375dc2f4f82ccfb72adb5cbd228bffc4400620`.
  - 67 PASS / 0 FAIL (MEASURED).
- The prior FAIL is #22 (901-920); #23 (921-940) PASSed. Both share the evidence name `2026-10-15-step52-RATE.txt`
  (ledger.json).
- Carried open items from that round (`07-CHANGELOG.md:38069-38077`, READ):
  - (1) LESSONS overstates the P2 bounds.
  - (2) Loafing separates only when pooled: one CH1 seed at 13.1% vs LOAF 13.7%.
  - (3) GOODHART on the yield thresholds.
  - (6) CH2 at 1.181 vs 1.15.

## On the ALREADY ESTABLISHED items

- **B1 import half:** the claim is about the AI importing the grader, and it is not contradicted. The grader importing the
  AI is a separate gap: there are 5 sites, and R:738 is missing from the brief's list.
- **The A2-P7 forced-PASS list:** R:1690 is a forced FAIL, not a PASS (READ).
