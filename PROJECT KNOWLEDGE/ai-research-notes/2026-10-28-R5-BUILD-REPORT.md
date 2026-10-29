> ✅ **BUILT 2026-10-29** (`07`; decisions `06` 2026-10-29). VERBATIM below section 00: the build report (session scratch `s53/r5/build/BUILD-REPORT.md`, sha256 `2a22435939059779`), with its FIX ROUND section, then two appendices copied from the workflow's result. Section 00 is the orchestrator's own checks on `main`.

## 00. The orchestrator's checks (2026-10-29, on the main checkout, R5 applied, uncommitted)

- **Applied to `main`** (12:01 AM, `s53/r5/apply_r5.py`): the worktree's 5 modified files written with main's own line ends, the 6 new files byte for byte (the free read, three evidence files, the kept trees `29a5dc81286162ff` and `07ea150c30288b24`); NOT the worktree's `2736e5bb787f9e67.zip` and `f0165b791500bbd3.zip` (no record names them). `git diff` in main equals the worktree's `git diff HEAD`, LF-normalised (95,735 bytes each). `provenance.py`: working-tree digest `07ea150c30288b24`, the fix round's final tree.
- **The fast checks on main** (12:04 AM): `test_goals` `Ran 233 tests` OK; check_purity `VERDICT: PASS`; check_fairness `PASS (0 breaches)`; call_census `19 sites; 0 MISSING` PASS; ledger `48 entries; well formed -> PASS`.
- **R5's revert mutants, SERIALLY** (G0, G226-G228, G347-G373, one worker, 106 s, 12:05-12:07 AM): `[G0] CONTROL ... 233 tests, failing none -> PASS`; `30 mutants CAUGHT as predicted, 0 REDUNDANT ALONE as predicted, of 369`; `FROZEN TREE: PASS`; `OVERALL: PASS`. Every registry's anchors (the fix round's `anchor_check.py`, pointed at main): `edits checked: 420` / `PROBLEMS: none`. The committed free read's selftest from main: `SELFTEST VERDICT: PASS` (5 cases).
- **The live A/B RE-RUN on the FINAL tree** (the first A/B ran on `29a5dc81286162ff`, before the fix round changed the settle). Scripts `s53/r5/ab2/`, made from the first A/B's by `ab2_setup.py`; the driver and the free read byte-identical to #45's. The grader's control reads `played_out` (the fix round's name for `settled`); its selftest gained 3 synthetic cases for that field and reads replay #48's runs (both arms on the final tree): `SELFTEST VERDICT: PASS (15 of 15 cases)`. Trees by `revert_step5.make_copy`: `TREES OK` (OLD differs from NEW only by G347's line in mode.py; NEW identical to main's `ai_player/`). Seeds 5361-5365 overlapped no entry in any of the four ledgers (main's and the three worktrees') before or after.
- **Ledger #49 and #50 REGISTERED 12:08:11 AM, begun with the same bounds sha256, runs launched 12:08:20 AM; all 9 ended exit 0 by 12:16:49 AM.** `VERDICT: PASS: 4 of 4 seeds counted (floor 3): OLD ended done NOT free and NEW done FREE with the exact reason on every counted seed; the PF-17 control passed`. Per seed (OLD frames / NEW frames, NEW settle): 5361 Trainer/TREECKO 274,966 / 285,943 (played 2, paused 103); 5362 Story/MUDKIP 194,544 / 205,522 (2, 106); 5363 Catcher/TREECKO 292,566 / 303,551 (2, 78); 5364 Trainer/TORCHIC 210,041 / 221,063 (2, 97); every NEW `passed` [`ch2_wally`], ending in PETALBURG CITY GYM (map 8, 1); every OLD at PETALBURG CITY (15, 9), not held free, input not taken, while the AI's `nav_free` read it free. Control 5365 Story/TREECKO `ch1_pokedex`: 142,878 frames, held free, input taken, played 0, paused 35, `played_out` False. `ledger --check`: 50 entries PASS. Evidence `ai_player/evidence/2026-10-29-r5ab2-AB.txt` (39 sections, verbatim).
- **Not re-run by me:** the full `revert_step5` (the fix round ran it on the same tree digest: 367 + 2 of 369) and the full regression lane (it runs after the commit, as the 2026-10-23 rule in `08` sets).

# R5 build report: a free screen before "done" (builder; 2026-10-28, 8:58 PM to 9:55 PM Los Angeles time)

The worktree is `C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ab039e6b-79e-1`, at HEAD `714084b0`. Nothing
is committed. The diff is `r5.diff` (`git diff HEAD`; 5 files, 345 insertions and 11 deletions). Every number below is copied
from a saved file in `s53/r5/build/`, and each one is named.

## 0. Headline (the caveat is in it)

**The spec's settle alone would NOT have fixed the only natural not-free "done" that the probe found.**

- **What the probe found.** On the pre-R5 tree, both `AI_PLAYER_TARGET=ch2_dad` runs from a real New Game (development seeds
  5301 and 5302) ended `play: done: ch2_dad reached` on a ONE-frame free read: the warp exit after DAD's scene.
  - On the next frame, WALLY's tutorial was running: script status 0, controls locked 1.
  - The game took no input there.
  - **The AI's own `nav_free` read that end frame as FREE.** The spec's settle runs only `if ... not nav_free(look)`, so
    it would have ended these runs at the same frame.
- **What I added for it.** The build adds the decision's pause and a second look before "done" (§5, deviation 1). It goes
  against D4 ("no new busy/idle wait") and U1 CONTROL ("no frame passes"). It sits behind its own test and its own mutant
  (G349), so it can be stripped.
- **What it changes, on development checks only (no held-out seed).**
  - From the probe's own end states, the pre-R5 tree ends at once, NOT free.
  - The R5 tree plays out the tutorial and ends free, with the exact same reason string.
  - On free ends (`ch1_clock`, `ch1_pokedex`), R5 adds only the pause, of 16 to 26 frames.
- **The checks all pass.**
  - test_goals: 224 tests OK.
  - Purity, fairness, the call census and the ledger check: PASS.
  - The R5 mutants G347-G351 and G226/G227/G228: all CAUGHT.
  - The full `revert_step5`: 345 CAUGHT plus 2 REDUNDANT as predicted, of 347.
  - `revert_safety_gates`: 23 of 23 caught.
- **The one failure is the worktree, not R5.** `run_units` reads OVERALL FAIL, and only on `test_kb2`. Two causes, both of
  the worktree's environment:
  1. no decomp at its default path relative to a worktree;
  2. git's CRLF checkout of `campaign_skeleton.json`.

  A copy with that file's LF bytes passes all 118 of its tests (§3).
- **NOT done:** the held-out live A/B, the full regression lane, any doc, and any commit (§6).

## 1. Step 1: the fixture probe (on the PRE-R5 code, before any edit)

The detail is in `probe/PROBE-CONCLUSION.md`, and every run is tabulated in `probe/SUMMARY.txt`.

- **How a run was launched.** `probe/probe_end_screen.py run` runs the play brain in-process, the way
  `ai_player/gates/play_harness.py` `play` does:
  - from `--fresh`, a REAL New Game: the AI plays the intro itself;
  - with the cartridge clock pinned to `rate_step5.GAME_CLOCK` (the spec's "host clock pinned": only the in-process harness
    can pin it; the launcher reads the host clock);
  - with the personality and starter of `rate_step5.plan_of`;
  - on a FROZEN copy of the pre-R5 `ai_player/` (`probe/tree_pre/`; `diff -rq` showed it identical to the worktree before
    any edit). The worktree could then be edited while the runs played.
- **Seeds.** Development seeds 5301-5304 were written in the worktree's seed ledger BEFORE the first run, as entry #43
  (`probe/ledger_begin.out`, 9:04 PM). The entry was closed with its verdict (`probe/ledger_finish.out`). Seed 5304 was not
  played.
- **The harness's free read.** It never calls the AI's `nav_free` (PF-19). FREE means all of: `gMain.callback2 ==
  CB2_Overworld`, `sGlobalScriptContextStatus == 2`, `sLockFieldControls == 0`, `sFieldMessageBoxMode == 0` and text printer
  0 inactive.
  - It is read on the end frame and on 10 more frames with no input. `free_held` means free on all 11.
  - A behavioural check confirms each verdict: a direction tapped in a throwaway copy of the frame turns the player only when
    the game takes input.
- **The read can FAIL and PASS.** `probe/selftest.out` ends `SELFTEST VERDICT: PASS`, exit 0, over five cases:
  - `clock_room.ss1`: free, and turned;
  - the "The clock is stopped" box: NOT free (status 0, lock 1, box 2, printer active), not turned;
  - MOM's box WITH `FLAG_SET_WALL_CLOCK` = 1: NOT free, not turned;
  - the same scene played out: free, and turned;
  - `route101_south.ss1`: free, and turned.

**The discriminator, per seed, pre-R5** (verbatim from `probe/SUMMARY.txt`):

```
ch1_clock_5301: seed 5301 target ch1_clock (Trainer/TORCHIC) | reason 'play: done: ch1_clock reached' | frames 16485 | free_at_return True free_held True first_not_free None | input True | AI nav_free at end True | at return: status 2 lock 0 box 0 cb2 CB2_Overworld
ch1_clock_5302: seed 5302 target ch1_clock (Story/TREECKO) | reason 'play: done: ch1_clock reached' | frames 16329 | free_at_return True free_held True first_not_free None | input True | AI nav_free at end True | at return: status 2 lock 0 box 0 cb2 CB2_Overworld
ch2_dad_5301: seed 5301 target ch2_dad (Trainer/TORCHIC) | reason 'play: done: ch2_dad reached' | frames 251736 | free_at_return True free_held False first_not_free 1 | input False | AI nav_free at end True | at return: status 2 lock 0 box 0 cb2 CB2_Overworld | next change: frame +1 status 0 lock 1
ch2_dad_5302: seed 5302 target ch2_dad (Story/TREECKO) | reason 'play: done: ch2_dad reached' | frames 199479 | free_at_return True free_held False first_not_free 1 | input False | AI nav_free at end True | at return: status 2 lock 0 box 0 cb2 CB2_Overworld | next change: frame +1 status 0 lock 1
```

**Fixture verdict: `ch2_dad` is NOT vacuous (2 of 2 seeds); `ch1_clock` is vacuous (2 of 2).**

- **Why `ch1_clock` ends free.** The clock is set inside a `use` goal whose `play_out` presses through MOM's text before the
  loop reads the mark.
- **What happens at `ch2_dad`.**
  1. The world memory logs the scene's warp `PETALBURG_CITY_GYM -> PETALBURG_CITY` at f251697 and f199440.
  2. "done" comes 39 frames later.
  3. `probe/runs/ch2_dad_5302/film.out` shows frame +1 with status 0 and lock 1. The screenshots `film/after_*.png` show
     WALLY's walk.
- **The decomp agrees.** `data/maps/PetalburgCity/scripts.inc`: `PetalburgCity_OnFrame` / `map_script_2
  VAR_PETALBURG_CITY_STATE, 2, PetalburgCity_EventScript_WallyTutorial`. This confirms 03-game-facts §4.3 (d) live.
- I stopped at the first non-vacuous target, as instructed: `ch1_birch` and `ch1_starter` were not run. No plant was
  needed.

## 2. Step 2: what was built (`ai_player/mode.py`, plus the gates)

| Spec | Where (line numbers in the worktree) | What |
|---|---|---|
| D2 | `mode.py:465-470` | `if milestone is None or index > target:` then `yield from self._settle_before_done(hands, nav, look, options.target, report)`, placed BEFORE the done check. The done check's two lines (`:471-472`) are byte-identical to HEAD `:457-458` (`cmp`, line ends normalized), and G226's anchor still occurs exactly once. |
| D3, D4 | `_settle_before_done`, `mode.py:661-707`; bound `DONE_SETTLE_ROUNDS = 6`, `:128` | At most 6 rounds. Not free: `play_out(hands, nav, f"{target} reached: what is on screen first")`, then `_count_losses`, then a fresh look; still busy ends the settle (PL-3, no retry). Free: the decision's pause (`hands.pad.idle(hands.pad.think_frames(), "deciding to stop here, ...")`, deviation 1), then a fresh look. The run ALWAYS goes on to the unchanged `done` line. An unsettled end is SAID: a `[AI-GOALS] ... reached, but the screen did not free ...` tell, `hands.note("end_screen", "not free", <busy_reason>, {target, stop, frame, played})`, and `report["settle"] = {played, paused, frames, stop, free}`. |
| D5 | `_end_screen`, `:709-724`; `_play_end`, `:729`, `:753-756`, `:769` | Every end reads one fresh `hands.look()` FIRST (same frame, before the wait and push watchers close). `report["end_screen"] = {free (nav_free), held_by (busy_reason or None), frame}`, plus for "done" `{settled (played > 0), settle_frames, paused, settle_stop}`. It goes into the end tell line (`the screen at the end free/NOT free (...)`) and into the `end` note's extra. No grader check was added. |
| D6, D7, D8 | (no code) | D6: settle frames count against `settings.frames`. D7: the existing play-out before `next_goal` is untouched, asserted by U3 CONTROL. D8: no save. |

**Tests** (`ai_player/gates/test_goals.py`, PlayLoopTests).

`run_loop` gains `settle=` (`:842`, `:893-896`): a stand-in for `play_out(hands, nav, why)` that may free the screen, lose a
battle or stop. Without it, the old stand-in runs, so every existing test is unchanged.

The "pre-R5" column is from `pre_r5_tests.out`: the new tests run against the pre-R5 `mode.py`.

| Test | Spec | Asserts | Caught by (mutant) | Pre-R5 |
|---|---|---|---|---|
| `test_r5_done_plays_out_the_screen_first` | U1 FAULT | box up at done: `play_out` called once with R5's why; reason exactly `done: ch1_pokedex reached`; end free and settled; in the end note; no `end_screen` note | G347 | FAIL |
| `test_r5_done_on_a_free_screen_plays_nothing_out` | U1 CONTROL (modified, deviation 1) | `play_out` NOT called, 0 presses, pad frames == the pause only; free; settled False | G348, G349 | FAIL (0 != 3) |
| `test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so` | U2 FAULT | stop with the box up: reason still exact; played once; one tell with the stop; one `end_screen` note; end NOT free, `held_by == busy_reason` | G347 | FAIL |
| `test_r5_a_box_before_the_target_is_the_loops_own_and_the_loop_goes_on` | U3 CONTROL (D7) | box up at the target's own milestone: the loop's play-out (its why), first goal after it, no `settle`, no "done" | none (a control) | PASS (as a control must) |
| whole file | U4 | 224 tests OK | | |
| `test_r5_every_end_records_its_screen` | U5 | patience end: NOT free with `held_by`, no settle fields, in the end note; MAX_LOSSES end: free | G348 | ERROR (no `end_screen`) |
| `test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen` | extra (the measured case) | free on the end frame, a scene from frame +1: played once, two pauses, end free and settled | G347, G349 | FAIL |
| `test_r5_the_settle_is_bounded` | extra (PL-4) | free after each play-out, busy after each pause: exactly 6 play-outs, then done NOT free, said | G351 | ERROR (no constant) |
| `test_r5_a_battle_the_settle_lost_is_counted` | extra | a loss inside the settle: `report["losses"] == 1`, told, no "the loop counted" line | G350 | FAIL |

**Mutants** (`revert_step5.py:1036-1065`, after G228). Each one deletes a call or guards it off (PF-2):

| Mutant | Edit | Result |
|---|---|---|
| G347 | the settle's call becomes `pass` | CAUGHT |
| G348 | `_end_screen`'s call becomes `{}` | CAUGHT |
| G349 | the pause and the second look become `break` | CAUGHT |
| G350 | the settle's `_count_losses` call becomes `pass` | CAUGHT |
| G351 | `for _ in range(DONE_SETTLE_ROUNDS)` becomes `while True` | CAUGHT |

All edit anchors in `revert_step5`, `revert_safety_gates` and `rate_step5.EXTRA_EDITS` still occur exactly once, so no
mutant was re-anchored. G226 and G228 mutate the same text as before.

**Census.** 0 MISSING. `_settle_before_done` (one site) is covered by G347, and `_end_screen` (one site) by G348.
`_play_end`'s eight sites are covered by G226/G227/G228 or by the existing waiver. I EXTENDED that waiver's reason in
`census_waivers.json` with one R5 sentence; the 5.2 text was kept.

## 3. Step 3: the checks, verbatim

The full outputs are `build/<name>.out`; the extract below is `build/results_block.txt`, copied from them by
`results_block.py`. Tree digest `sha256:29a5dc81286162ff` (`run_units`' suite lines and `provenance()`; the ledger is
outside the digest). The frozen-tree seal of each revert run reads PASS.

```
test_goals            py -3.12 ai_player/gates/test_goals.py                exit=0  "Ran 224 tests in 1.842s" / "OK"
check_purity          py -3.12 ai_player/gates/check_purity.py              exit=0  "VERDICT: PASS"
check_fairness        py -3.12 ai_player/gates/check_fairness.py            exit=0  "PERSON-FAIR DATA DOOR: PASS (0 breaches)"
call_census           py -3.12 ai_player/gates/call_census.py --verbose     exit=0  "CALL-SITE CENSUS since HEAD: 1 AI files changed, 6 functions or added calls, 14 sites; 0 MISSING" / "CALL-SITE CENSUS: PASS"
ledger_check          py -3.12 ai_player/gates/ledger.py --check            exit=0  "LEDGER ledger.json: 43 entries; well formed -> PASS"
revert_r5_mutants     py -3.12 ai_player/gates/revert_step5.py G0,G226,G227,G228,G347,G348,G349,G350,G351 --workers 4
                      exit=0  "[G0] CONTROL, the unchanged copy: 224 tests, failing none (ran the copy: True) -> PASS"
                              G226, G227, G228, G347, G348, G349, G350, G351 each "-> CAUGHT"
                              "8 mutants CAUGHT as predicted, 0 REDUNDANT ALONE as predicted, of 347" / "OVERALL: PASS"
revert_step5_all      py -3.12 ai_player/gates/revert_step5.py <all 348 names> --workers 8      exit=0 (251 s)
                              "345 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 347" (G62, G186: pre-existing)
                              "FROZEN TREE: PASS - ... (349 checks of 184 files, files digest a813b45287d8e507)" / "OVERALL: PASS"
revert_safety_gates   py -3.12 ai_player/gates/revert_safety_gates.py --workers 4               exit=0 (236 s)
                              "23 mutants CAUGHT as predicted, of 23" / "OVERALL: PASS"
regression_due        py -3.12 tools/workflows/regression_due.py            exit=1  "5 of 5 suites due" (units, revert_step5,
                              revert_safety_gates, rate_step5, live_step5)
run_units             py -3.12 ai_player/gates/run_units.py                 exit=1 (429 s)  "OVERALL: FAIL": every suite exit 0
                              but "== test_kb2: ... exit 5" ("Ran 0 tests" "FAILED (errors=1)")
test_kb2 (decomp set) POKEBOT_DECOMP=<pinned clone> py -3.12 ai_player/gates/test_kb2.py   exit=1  "Ran 118 tests"
                              "FAILED (failures=1)": OutputsTests.test_committed_files_equal_a_fresh_extraction, bosses.json
                              "483b246e125de9a0..." != "5fef31477f5b33fa..."
kb2_lf_check          py -3.12 build/kb2_lf_check.py <worktree> <decomp>    exit=0  "campaign_skeleton.json: 13877 bytes
                              sha256 5fef31477f5b33fa (99 CRLF line ends) -> 13778 bytes sha256 483b246e125de9a0 (LF only)"
                              "Ran 118 tests in 181.376s" / "OK" / "test_kb2 in the LF copy: exit=0"
```

**Why `test_kb2` fails here (environment, not R5).**

- **No decomp at the default path.** `extract_world.resolve_decomp` defaults to `<repo>/../_decomp/pokeemerald`. From a
  worktree that is `.claude/worktrees/_decomp`, which does not exist: exit 5. Setting `POKEBOT_DECOMP` fixes it.
- **A CRLF checkout changes one hash.** `git ls-files --eol` reads `i/lf w/crlf` for `ai_player/gates/campaign_skeleton.json`.
  The worktree's file hashes to `5fef3147…`; the main checkout's file, and `knowledge/world/bosses.json`, record
  `483b246e…`.
- **The proof.** `kb2_lf_check.py` copies the R5 tree, puts that one file back to LF, and gets 118 tests OK.
- **A first `kb2_lf_check` attempt** errored on a missing `sandbox-pokebot/modules/data` in the copy. Its output was
  overwritten by the rerun (the script now copies that folder).
- The other two DUE suites, `rate_step5` and `live_step5`, are a graded sweep and the live launcher, not revert drivers.
  They were NOT run.

## 4. Development A/B on the natural fixture (beyond the task; NOT the live proof)

These are all development seeds, all in-process with the clock pinned (`probe/SUMMARY.txt`):

| Run | Start | Frames | End free (held) | Took input | Settle |
|---|---|---|---|---|---|
| devab old 5301 | `runs/ch2_dad_5301/end_state.ss1` + world | 0 | **False** (+1: status 0, lock 1) | no | none |
| devab old 5302 | `runs/ch2_dad_5302/end_state.ss1` + world | 0 | **False** (+1: status 0, lock 1) | no | none |
| devab new 5301 | same | 10,997 | **True** | yes | played 2, paused 112 |
| devab new 5302 | same | 11,078 | **True** | yes | played 2, paused 102 |
| arms new ch1_clock 5301 | New Game | 16,502 (OLD 16,485 + 17) | True | yes | played 0 |
| arms new ch1_clock 5302 | New Game | 16,345 (OLD 16,329 + 16) | True | yes | played 0 |
| arms old ch1_pokedex 5303 | New Game | 125,964 | True | yes | none |
| arms new ch1_pokedex 5303 | New Game | 125,990 (+26) | True | yes | played 0 |

- **Every run's reason** is exactly `play: done: <target> reached`.
- **Why NEW played out twice.**
  1. The first pause found WALLY's tutorial.
  2. The tutorial's own warp back to the gym freed the player for one frame before the gym's ON_FRAME return scene
     (`PetalburgCity_Gym_OnFrame`). The second pause found it: 03-game-facts §4.3 (d)'s other prediction, seen live.
  3. The third pause found the gym free. The end state has `VAR_PETALBURG_GYM_STATE` = 2.
- **A replay, not a replication.** Each OLD/NEW pair is one trajectory, replayed (CLAUDE.md rule 8). The NEW and OLD frame
  counts match exactly until the pause.

## 5. Deviations from the spec, and why

1. **The decision's pause and a second look before "done", on EVERY done end** (`_settle_before_done`; G349). This goes
   against D4 ("no new busy/idle wait") and U1 CONTROL ("NO frame passes"). Why:
   - **The measurement.** The ONLY natural not-free "done" that the probe found is a ONE-frame free read that the AI's
     own `nav_free` passes, so a settle gated on `not nav_free(look)` never runs there (`probe/SUMMARY.txt`, ch2_dad rows).
   - **The pause is the loop's existing decision protocol, not idling.** Every goal already takes it and re-looks (the
     thinking pause, `mode.py` `_play`). PL-1 forbids idling while a screen WAITS FOR A PRESS; the pause happens on a
     FREE screen, and a scene that begins during it is pressed through by `play_out`.
   - **The cost.** 16 to 26 frames on a free end (measured: 17, 16, 26).
   - **The CONTROL that changed.** U1 CONTROL now asserts that ONLY the pause passes (pad frames == `think_frames()`,
     no press, no play-out).
2. **The settle is a helper called whenever the target is reached.** The spec's sketch put the `nav_free` test inline. With
   the helper, `_play` gains ONE call that one mutant (G347) deletes, so the census needs no new waiver; the helper owns the
   free test.
3. **Three hooks beyond the spec's two mutants.**
   - `_count_losses` after each play-out (G350). The settle can play a battle after the pass's own count, and
     `_play_end`'s comment claimed "no battle in between". That comment was updated.
   - The `DONE_SETTLE_ROUNDS` bound (G351, PL-4).
   - The pause itself (G349).
4. **The census waiver** for `_play_end` was EXTENDED with an R5 sentence, not replaced.
5. **The full `revert_step5` was run with an explicit list of all 348 names.** That way it wrote no file into
   `ai_player/evidence/` and archived none (an unfiltered run would have moved the tracked `2026-10-28-step52-REVERT.txt`
   to the archive). It still wrote two kept-tree zips through `snapshot_tree`. They are untracked by-products:
   - `ai_player/evidence/trees/2736e5bb787f9e67.zip`: the 9:22 PM intermediate tree, `DONE_SETTLE_ROUNDS` 4;
   - `ai_player/evidence/trees/29a5dc81286162ff.zip`: the final tree.

   They are NOT in `r5.diff`.
6. **The probe used the in-process harness, not the launcher.** The spec asks for the clock pinned, which only the harness
   can do.
7. **Environment set up in the worktree** (all gitignored, none in the diff).
   - I copied, as reads of the main checkout, `sandbox-pokebot/mgba/` and
     `sandbox-pokebot/profiles/ai-step0-fixture/{metadata.yml,http.yml,.ai_player_profile}`.
   - The framework then wrote its default profile `*.yml` files into the worktree's `sandbox-pokebot/profiles/`.
8. **The ledger.** Entry #43 sits in the worktree's `ai_player/gates/ledger.json` (in `r5.diff`). Its `evidence` field
   names this session's scratch.

## 6. What I did NOT do

- **The live proof.** No held-out seeds were registered or played: no live A/B and no PF-17 held-out control. The
  development stand-ins are in §4.
- **The full regression lane.** I did not run `run_regression.py --full`, `rate_step5` or `live_step5`.
- **Probes.** I did not probe `ch1_birch` or `ch1_starter`, built no plant, and never ran the real launcher.
- **Docs.** I touched no doc: README, LESSONS, 04, 06, 07, 08, the backlog and the recon notes are untouched.
- **Git.** No commit, add, stash or other destructive git.
- **The protected areas.** Nothing in the main checkout, the learner clone, `sandbox-pokebot/` code, `custom-pokebot/` or
  `40cakes repo/` was edited. The bot's behaviour is unchanged.

## 7. Open questions (for the orchestrator)

1. **Accept deviation 1?** The alternatives:
   - **(a) A map-change window.** Measured: the free frame came 39 frames after the warp's transition, which is more than
     `SETTLE_FREE` 30, so the window would need a new constant. It keeps "no frame passes" for ends far from a warp.
   - **(b) Strip it** (delete G349's text). Then the natural `ch2_dad` fixture does not discriminate: both arms end on the
     one free frame, and the A/B needs the harness plant of spec §4.
2. **The live A/B.**
   - **Fixture:** `AI_PLAYER_TARGET=ch2_dad` from a REAL New Game. One in-process run took 268.7 s and 349.3 s (199,479
     and 251,736 frames).
   - **Discriminator:** the harness's HELD free read (over more than one frame) or the input check. A single-frame read,
     and the AI's `nav_free`, call the OLD end free (the PF-19 trap).
   - **Expected:** OLD `free_held` False; NEW True; reason exact in both.
   - **The OLD arm** is G347 applied in a temp tree. It deletes the whole settle, pause included.
3. **Commit the probe?** Should `probe/probe_end_screen.py` (the RAM free read, its selftest and the input check) become a
   committed gate for that proof?
4. **The meaning of "done" for an intermediate target.** With R5, a `ch2_dad` run ends after WALLY's tutorial and DAD's
   speech (ch2_wally is reached too), and its reason is still `done: ch2_dad reached`. I believe that is right (a person
   cannot stop mid-scene), but it is the orchestrator's ruling.
5. **Worktree traps for `test_kb2`.** The default decomp path, and the CRLF checkout changing `campaign_skeleton.json`'s
   hash, will fail `test_kb2` in any `.claude/worktrees/*` run of the units or the full lane unless `POKEBOT_DECOMP` is set
   and the file is LF. A candidate KI.
6. **Not explained:** the end-frame screenshot of both `ch2_dad` runs is black (frame +1 shows the city). It is not used as
   evidence.

## FIX ROUND (R5's fix round, 2026-10-28, 10:59 PM to about midnight Los Angeles time; the last check ended 11:54 PM)

Inputs: the independent mutant sweep (`sweep/R5-SWEEP-TABLE.txt`: 56 run, 43 caught, 13 survived), the adversarial review
(verdict FIX, findings R5-F1 to R5-F7) and the live A/B (`ab/AB-REPORT.md`: PASS). Everything this round wrote is in
`s53/r5/fix/`, and every number below is copied from a saved file there, which is named. Nothing is committed or staged.

### F0. Headline (the caveat is in it)

**Every review finding and all 13 sweep survivors are fixed and pinned. Each fix has a FAULT arm, a registered revert
mutant that brings the old behaviour back, and a CONTROL. The fix round DID change R5 logic that the live A/B tested.**

- **What changed in the settle.** Its frames now go through a budget guard (`_settle_frames`, R5-F1), and it now stops on
  a MAX_LOSSES-th loss (R5-F5). Its record also gained fields, and `settled` was renamed `played_out` (R5-F6).
- **On the A/B's measured path, the trajectory is byte-identical.** I replayed seed 5301 from the probe's saved
  `ch2_dad_5301` state (ledger #48, a replay, not a measurement), with both arms on the fixed tree. Each arm's end state has
  the same md5 as #44's arm. The NEW arm again took 10,997 frames, played out 2 screens and paused 112 frames.
- **The held-out A/B was not re-run.** Whether to re-run it is the orchestrator's call. If it is re-run, the grader
  `ab/ab_summary.py` must be updated and re-registered: its control reads `end_screen.settled`, which is now `played_out`.

### F1. The review's findings: what was done

Each fix below has three parts:

- a FAULT arm: a test that fails on the old behaviour;
- a revert mutant that brings that behaviour back. Each one is registered in `revert_step5.py`, and in the final re-run
  all of them are CAUGHT (§F4);
- a CONTROL that passes.

| Finding | The fix (worktree file) | FAULT arm (test) / revert mutant | CONTROL |
|---|---|---|---|
| **R5-F1** (MINOR) The frame budget could cut a reached target into an unrecorded "stopped". | `mode.py`: `_settle_frames` hands on the settle's frames (its play-out and its pause), one per `yield`, as `_bounded` counts them, while more than `DONE_BUDGET_MARGIN` = 2 frames of `settings.frames` are left. At the margin it closes the work and the settle stops: `report["settle"]["budget"]` True, the stop is `the run's frame budget ran out (N frames)`, a tell, and an `end_screen` note "budget". The run ends exactly `done: <target> reached`, with its end record. `run_loop` gained `frames=`, which drives the loop through the REAL `HandsBrain._bounded`. | `test_r5_the_frame_budget_never_cuts_a_reached_target_short_of_its_end` (budget 500, a 2000-frame play-out): G356, the play-out handed on unguarded (the build's code), gives "stopped: not finished within 500 frames". `test_r5_the_frame_budget_cuts_the_decisions_pause_too`: G357, the pause unguarded. G371: the cut is not said. | The same play-out with budget 5000 is played out to its end and ends free, with nothing said of a budget. |
| **R5-F2** (MINOR) No test pinned the three rounds the measured chain takes. | `test_goals.py`: the measured chain. The screen is free for one frame, then WALLY's tutorial; it is played out; the warp back is free for one frame, then the gym's scene; it is played out; then free. | `test_r5_the_measured_ch2_dad_chain_takes_three_rounds` asserts 2 play-outs, 3 pauses and a FREE end. G354 (`DONE_SETTLE_ROUNDS = 2`) ends it NOT free. | `test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen` (one scene: 2 rounds suffice). |
| **R5-F3** (MINOR) Nothing committed could detect a live regression; the ledger cited session scratch. | (a) `ai_player/gates/probe_end_screen.py`: the harness-side HELD free read, its 5-case selftest and its `run` mode, committed BYTE-IDENTICAL (sha256 `d5c6095b…`, the free read that #43-#47's runs used and that #45's registered numbers hash). (b) Three evidence files, assembled VERBATIM from the scratch with each file's sha256: `ai_player/evidence/2026-10-28-r5probe-PROBE.txt` (#43; its code line names the pre-R5 tree `53e0c26e7812db47`), `…-r5ab-AB.txt` (#44-#47; tree `29a5dc81286162ff`; it holds the A/B's report, SUMMARY, tables, every run's probe.out, and the driver, grader and run script whose hashes #45 registered) and `…-r5fix-REPLAY.txt` (#48; the fixed tree `07ea150c30288b24`). (c) The ledger's `evidence` fields for #43-#48 point at them. | The committed selftest, run IN PLACE from the worktree: `SELFTEST VERDICT: PASS`, 5 of 5 cases (2 NOT free, among them MOM's box with FLAG_SET_WALL_CLOCK set, and 3 free), each confirmed by a tapped direction (`fix/selftest_committed/selftest.out`). | provenance's own reader (`code_fields`) reads each file's code line as the tree its ledger entries name: PROBE `53e0c26e7812db47` ← #43; AB `29a5dc81286162ff` ← #44-#47; REPLAY `07ea150c30288b24` ← #48 (`fix/evidence_digests.out`). |
| **R5-F4** (NIT) The census never traces calls inside a new function. | RV1 is registered as G352 (the settle's `play_out` call deleted) and RV2 as G353 (the not-free tell and note deleted). The census lists the new function `_settle_frames`'s two sites as COVERED (G352 for the play-out, G349 for the pause). | G352 and G353, CAUGHT. | G0. |
| **R5-F5** (NIT) A MAX_LOSSES-th loss inside the settle was ignored. | Chosen and pinned: the settle ENDS AT ONCE on its count's MAX_LOSSES stop. There is no pause and no further play-out: the run fights no battle past the cap, as rate_step5's R5.LOSE3 ("no game loss past it") asks. Its stop is the MAX_LOSSES reason, and the run still ends `done: <target> reached` (D3). | `test_r5_the_last_allowed_loss_inside_the_settle_ends_it`: G358, the stop not heard (the build's code), plays out 6 times. G350, re-anchored, is caught there too. | `test_r5_a_battle_the_settle_lost_is_counted`: one loss, under the cap, and the settle goes on to its pause. |
| **R5-F6** (NIT) Naming: `settled`, a stale milestone list, and the pause's cost. | `settled` is renamed `played_out` (the end record, the end line, the tests). The milestones the story passed while the settle played (read by the loop's own `current`, through `self._passed_between`) go into `report["settle"]["passed"]`, the end record and the end line, and are told. `report["milestones"]` and the MILESTONE lines, which the graders read, are untouched. The pause is `Pacing.think`, 14-45 frames (`hands/pad.py:53`). The build's "16 to 26" were three measurements (17, 16, 26; the PF-17 control paused 44). | `test_r5_the_settle_names_the_milestones_its_screens_passed`: G359 (the read deleted), G372 (the tell deleted), G373 (the reader not set). | U1 CONTROL: `passed` is []. |
| **R5-F7** (NIT) #43 reported R5-tree runs, and deviation 1 was unratified. | #43's verdict is reworded to its own tree's runs. #47 is written: a REPLAY entry for the builder's five R5-tree runs on seeds 5301-5303, recorded AFTER THE FACT, as its note says. Its note names the two superseded runs on the intermediate tree `2736e5bb787f9e67` and does not count them. `ledger --check`: 48 entries, PASS. Deviation 1 is kept. The amendment of D4 and U1 in 06 is the orchestrator's (§F7). | (a record, no mutant) | |

### F2. The sweep's 13 survivors: each is now caught

- **The tests.** Each survivor got the assertion that its sweep probe used (`sweep/survivor_probes.py`). The assertions
  were added to the existing R5 tests where the scenario was the same; otherwise they are in a new test.
- **The registered mutants.** Each survivor is now a registered revert mutant, CAUGHT in §F4.
- **The re-run.** The fix sweep re-ran all 56 survivors' rows, re-anchored. In the table, "first failing" is copied from
  `fix/sweep/caught_review.txt`.

| Survivor | What it broke | Now caught by (test: the assertion) | Revert mutant |
|---|---|---|---|
| S04 | no settle when no milestone is read (every required one passed) | `test_r5_every_milestone_passed_a_box_is_played_out_first` (with a reach floor: the goal manager reads milestone None on that look): `screens == [R5_WHY]` | G355 |
| S23 | `DONE_SETTLE_ROUNDS` 2 | `test_r5_the_measured_ch2_dad_chain_takes_three_rounds`: two play-outs, a free end | G354 |
| S26 | `report["settle"]["frames"]` always 0 | U1 FAULT: `== 200 + pause`; U1 CONTROL: `== pause` | G362 |
| S27 | `report["settle"]["free"]` always True | U2: `assertIs(..., False)` | G363 |
| S35 | the SAID tell and note lose what holds the screen | U2: the told line ends `held by: <busy_reason>`, and the note's reason is the same | G364 |
| S37 | `_end_screen` reads `hands.last` | `test_r5_a_stuck_end_reads_the_screen_as_it_is_at_the_end`: a MAX_LOSSES end after the loop's play-out freed the screen reads FREE | G360 |
| S40 | `end_screen["frame"]` None | `test_r5_the_end_record_carries_the_end_frame`: `== 1000 + pad frames` | G365 |
| S45 | `end_screen["settle_frames"]` 0 | U1 FAULT: `== 200 + pause` | G366 |
| S46 | `end_screen["paused"]` 0 | U1 CONTROL: `== pause` | G367 |
| S53 | the `end_screen` note loses target, frame and played | U2: `("ch1_pokedex", boxed.frame, 1)` | G368 |
| S54 | the told line's own words dropped (`(None)`) | the bounded test: `(a scene still plays)` | G369 |
| S55 | the end LINE says `NOT free` without what holds it | U2: `NOT free (<busy_reason>)` in the end line | G370 |
| S56 | the end record read AFTER the watchers close | `test_r5_the_end_look_closes_the_wait_record`: the wait record reaches the end look (`longest == 100`). Its CONTROL: a done end's last look is at the end's frame, so the end look adds nothing there (`(1300, 300)` in either order). R5's order is kept ON PURPOSE, and the comment in `_play_end` says why. | G361 |

### F3. Did a fix change the R5 logic that the live A/B tested? YES, and on the A/B's path the trajectory is the same

**What changed in `_settle_before_done`:**

- **Its frames.** The play-out and the pause are handed on through `_settle_frames` (R5-F1), not `yield from`. Both are
  driven one frame per `yield`, as `_bounded` drives them.
- **Its stops.** It now stops on the frame budget's margin (R5-F1) and on a MAX_LOSSES-th loss inside it (R5-F5).
- **Its `paused`.** It counts the frames that passed, not the pause drawn. They are the same unless the budget cut it.
- **Its record.** `report["settle"]` gained `budget` and `passed`. The end record renamed `settled` to `played_out` and
  gained `passed`. The end line gained the passed milestones (R5-F6).

`_play` gained one statement before its loop (`self._passed_between = lambda ...`, with its comment). The done check's two
lines are byte-identical, and so is the settle's call line: G226 and G347 are unchanged. The settle's signature is
unchanged too, so the A/B's recording wrapper (`ab_probe.py`) still fits it, and replay #48 used that wrapper as it is.

**The determinism REPLAY** (ledger #48, a replay of development seed 5301; CLAUDE.md rule 8: one trajectory, replayed):

- **What it ran.** #44's design: seed 5301 from the probe's saved `ch2_dad_5301` end state and world memory, through the
  A/B's own driver `ab/ab_probe.py`, unchanged. Both arms ran on frozen copies of the FIXED tree, made by
  `revert_step5.make_copy` (`fix/replay/make_fix_trees.out`: "NEW_FIX vs the worktree's ai_player/: IDENTICAL";
  "OLD_FIX_G347 vs NEW_FIX: differ in ['mode.py']").
- **The result** (`fix/replay/compare_replay.out`): "TRAJECTORY KEYS (reason, frames, end frame, end state md5, map,
  position, the held free read, the input check, the loop top and its state): ALL THE SAME in both arms".
  - NEW: 10,997 frames, end state md5 `c31ea9d86a9d74c2736f8b85631c58bf`, END held free, input taken.
  - OLD: 0 frames, md5 `149f4d37160fbf55f2e66203fdfe0c79`, END not held free.
  - NEW's settle record: `{"played": 2, "paused": 112, "frames": 10997, "stop": null, "free": true, "budget": false,
    "passed": ["ch2_wally"]}`. Its end record: `played_out: true`.
- **What it shows.** The fix's changes are off the A/B's measured path, or in its records only. The `passed` field shows
  the live settle passing ch2_wally, the builder's Q4, now visible in the record.
- **What it does NOT show.** It is not a re-run of the held-out A/B. It does not cover the PF-17 control (`ch1_pokedex`,
  a REAL New Game) on the fixed tree. Neither was run. The budget and MAX_LOSSES paths have NO live run; they are unit
  tests only.

### F4. The final re-run, SERIALLY (11:28 PM to 11:55 PM)

The checks ran one at a time, each after the last had ended, under `fix/final_runs.py`. Each output is saved verbatim as
`fix/final/NN-<name>.out`. The lines below are copied from those files by `fix/results_block.py` (into
`fix/results_block.txt`).

```
01 test_goals              exit=0  "Ran 233 tests in 1.752s" / "OK"
02 check_purity            exit=0  "VERDICT: PASS"
03 check_fairness          exit=0  "PERSON-FAIR DATA DOOR: PASS (0 breaches)"
04 call_census --verbose   exit=0  "CALL-SITE CENSUS since HEAD: 1 AI files changed, 8 functions or added calls, 19 sites; 0 MISSING"
                                   "CALL-SITE CENSUS: PASS"
05 ledger --check          exit=0  "LEDGER ledger.json: 48 entries; well formed -> PASS"
06 provenance (before)     exit=0  "... working-tree digest sha256:07ea150c30288b24 over git diff HEAD (4 files, 79599 bytes) and 1
                                   untracked files ..."
07 the fix sweep           exit=0  75 rows: {"CONTROL PASS (predicted CONTROL)": 1, "CAUGHT (predicted CAUGHT)": 73,
                                   "SURVIVED (predicted SURVIVED)": 1}; predictions held 75 of 75; "S01-S56: 56 of 56 CAUGHT;
                                   SURVIVED overall: ['N15']"; "worktree_unchanged": true
08 N15's probe             exit=0  "N15 EQUIVALENCE PROBE: BOTH close the cut play-out AT the cut, before the end note: no
                                   difference observable"
09 revert_step5 G0,G226,G227,G228,G347-G373 --workers 1   exit=0
                                   "[G0] CONTROL, the unchanged copy: 233 tests, failing none (ran the copy: True) -> PASS"
                                   "30 mutants CAUGHT as predicted, 0 REDUNDANT ALONE as predicted, of 369"
                                   "FROZEN TREE: PASS - ... (32 checks of 185 files, files digest 93921ed008b593dd)" / "OVERALL: PASS"
10 anchor_check            exit=0  "edits checked: 420; revert_step5 mutants 370 (G0 included)" / "PROBLEMS: none"
11 regression_due          exit=1  "5 of 5 suites due" (units, revert_step5, revert_safety_gates, rate_step5, live_step5)
12 run_units (POKEBOT_DECOMP set)  exit=1  "OVERALL: FAIL": every suite "exit 0" but "== test_kb2: ... exit 1" ("Ran 118 tests
                                   in 179.154s" / "FAILED (failures=1)")
13 revert_step5 <all 370 names> --workers 8   exit=0
                                   "367 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 369" (G62, G186: pre-existing)
                                   "FROZEN TREE: PASS - ... (371 checks of 185 files, files digest 93921ed008b593dd)" / "OVERALL: PASS"
14 revert_safety_gates --workers 4   exit=0  "23 mutants CAUGHT as predicted, of 23" / "FROZEN TREE: PASS" / "OVERALL: PASS"
15 kb2_lf_check (the builder's)  exit=0  "campaign_skeleton.json: 13877 bytes sha256 5fef31477f5b33fa (99 CRLF line ends) ->
                                   13778 bytes sha256 483b246e125de9a0 (LF only)" / "Ran 118 tests in 179.058s" / "OK" /
                                   "test_kb2 in the LF copy: exit=0"
16 provenance (after)      exit=0  "... working-tree digest sha256:07ea150c30288b24 ..." (the tree did not move)
17 test_kb2 alone (POKEBOT_DECOMP set)  exit=1  "FAIL: test_committed_files_equal_a_fresh_extraction
                                   (__main__.OutputsTests.test_committed_files_equal_a_fresh_extraction)" ... ": bosses.json" /
                                   "Ran 118 tests in 178.686s" / "FAILED (failures=1)"
```

**What the re-run shows.**

- **Every revert mutant this round added is CAUGHT: G352-G373, 22 in all.**
  - G349 and G350 were re-anchored and are caught again. G347, G348, G351 and G226-G228 are unchanged and caught.
  - Every sweep mutant is caught: S01-S56, the review's RV3, RV5 and RV6, and N01-N14. N15 survived, as pre-registered
    before its first run, and its probe shows it is equivalent here.
- **The only failure is `test_kb2`, and it is the builder's environmental cause.**
  - Git's CRLF checkout of `campaign_skeleton.json` turns the hash `bosses.json` records (`483b246e…`, the LF bytes) into
    `5fef3147…`.
  - With `POKEBOT_DECOMP` set, the other cause is gone: all 118 tests ran.
  - In the LF copy, all 118 pass.
- **What was not run.** The DUE `rate_step5` and `live_step5` are a graded sweep that writes the seed ledger and the live
  launcher, not revert drivers. Neither was run.
- **The counts.** test_goals: 233 tests, the builder's 224 plus 9 new. revert_step5: 369 mutants, the builder's 347 plus
  22 new.
- **Development runs, before the final ones.** They are in `fix/`: `test_goals_dev1.out`, `revert_r5_dev1.out`,
  `check_purity_dev1.out`, `check_fairness_dev1.out`, `call_census_dev1.out` and `call_census_dev2.out`, and the sweep's
  `*_dev1*` files. `call_census_dev1.out` found 1 MISSING: the pre-existing site of `current`, counted because the fix
  round added two calls of that closure. A waiver now covers it; it says so, and the two new calls are covered by G373.
- **Kept-tree zips.** Step 09 wrote `ai_player/evidence/trees/07ea150c30288b24.zip`, the final tree, at 11:31:51 PM.

### F5. For the commit (the orchestrator's): stage these EXPLICIT paths

| Path | Status | What it is |
|---|---|---|
| `ai_player/mode.py` | M | the code |
| `ai_player/gates/test_goals.py` | M | 233 tests |
| `ai_player/gates/revert_step5.py` | M | G347-G373: G349 and G350 re-anchored, G352-G373 new; 369 mutants in all |
| `ai_player/gates/census_waivers.json` | M | the `_play_end` waiver extended by one sentence; one new waiver for `current`'s pre-existing site |
| `ai_player/gates/ledger.json` | M | #43 reworded; #44-#46 evidence repointed; #47 and #48 new |
| `ai_player/gates/probe_end_screen.py` | new | the held free read |
| `ai_player/evidence/2026-10-28-r5probe-PROBE.txt` | new | evidence |
| `ai_player/evidence/2026-10-28-r5ab-AB.txt` | new | evidence |
| `ai_player/evidence/2026-10-28-r5fix-REPLAY.txt` | new | evidence |
| `ai_player/evidence/trees/29a5dc81286162ff.zip` | new | the A/B's tree, which #44-#47 name |
| `ai_player/evidence/trees/07ea150c30288b24.zip` | new | the fixed tree, which #48 names (written by this round's final revert runs; see §F4) |

**Do NOT stage** these, because no committed record names them:

- `ai_player/evidence/trees/2736e5bb787f9e67.zip`: the builder's intermediate `DONE_SETTLE_ROUNDS`-4 tree.
- `ai_player/evidence/trees/f0165b791500bbd3.zip`: this round's own first development tree, at 11:11 PM.

I deleted neither: both are untracked by-products.

### F6. What this round did NOT do (said plainly)

- **No re-run of the held-out live A/B, or of its PF-17 control, on the fixed tree.** That is the orchestrator's call (§F3).
  If they are re-run, `ab_summary.py`'s control criterion reads `end_screen.settled`, which is now `played_out`, so the
  grader must change and be re-registered on new held-out seeds.
- **No full regression lane.** I did not run `run_regression.py --full`, `rate_step5` (graded, writes the seed ledger) or
  `live_step5` (the launcher). They are DUE: `fix/final/11-regression_due.out`.
- **No live run of the new paths.** The frame budget's cut and a MAX_LOSSES-th loss inside the settle are proven in the
  unit harness only.
  - S37's live consequence is not measured. In the harness, the stand-in play-out takes no look.
  - N15's equivalence is shown in CPython only (`fix/sweep/n15_probe.py`).
- **The optional half of R5-F4 was not done.** The census still does not trace calls inside an added function. Changing it
  widens a shared gate for every later round: every call inside every new function would need a mutant or a waiver. That
  needs its own fault test in `revert_safety_gates` and a ruling.
- **The free read is not wired into any lane.** It is committed as a runnable TOOL with a selftest, not as a gate in
  `run_units` or the regression lane. It needs the emulator and the ROM. Adding a suite changes the lane, which is the
  orchestrator's decision.
- **Docs.** No doc was edited: README, LESSONS, 04, 06, 07, 08, the backlog and the recon notes are untouched. The 06 text
  is proposed in §F7.
- **Git.** No git commit, add, stash, reset, checkout of paths, clean or restore. Git was used only read-only (`status`,
  `diff`, `ls-files`, `show`, `rev-parse`, `diff --no-index` for the r5.diff).
- **Protected areas.** Nothing was edited in the main checkout, the bot tuner's clone or its processes, `sandbox-pokebot/`
  code, `custom-pokebot/` or `40cakes repo/`. The bot's default behaviour is unchanged.
- **`test_kb2` in the worktree still fails on the CRLF checkout of `campaign_skeleton.json`.** This is the environment, not
  R5: `fix/final/12-run_units.out` and `fix/final/15-kb2_lf_check.out`. It was not fixed: changing the line ends of a
  tracked file is not this round's to do.

### F7. Proposed text for 06 (the orchestrator's to write; nothing here is recorded yet)

1. **D4 and U1 AMENDED: ratify build deviation 1 (the review's R5-F7).**
   - D4: "Press, never idle while a screen waits (PL-1). The settle plays a screen that is not free out with `play_out`. On
     a FREE look it takes the loop's own decision pause (`Pacing.think`, 14-45 frames) and one more look before 'done':
     one free look is not a free screen."
   - U1 CONTROL: "on a free look that stays free nothing is pressed or played out, and only that pause passes."
   - Why: the pause is the ONLY thing that discriminated in the live A/B. On all 4 of #45's loop tops, the AI's `nav_free`
     read the screen free. Stripping the pause (the build report's Q1 (b)) reduces NEW to OLD by code.
   - Cost: one pause per "done" end. Measured: 17, 16 and 26 frames on the development runs, 44 on the PF-17 control.
2. **D6 REWRITTEN (R5-F1).**
   - "The settle's frames count against `settings.frames`, and the settle never lets the brain's bound cut a reached
     target. It hands its frames on (`_settle_frames`) only while more than `DONE_BUDGET_MARGIN` (2) frames are left. At
     that margin it stops and says so (a tell and an `end_screen` note 'budget'; `report.settle.budget` True), and the run
     ends exactly 'done: <target> reached' with its end record."
   - Rejected: the build's "a budget end reads stopped: not finished within N frames, reported, not hidden". It was NOT
     reported: there was no end record, no end note and no "done" line. And `live_step5`'s HONESTY check reads that stop
     over a proof that holds as a lie (`review/probe_budget_settle.out`).
3. **A new D9 (R5-F5).**
   - "A MAX_LOSSES-th loss inside the settle ends the settle at once: no pause, no further play-out. Its stop is the
     MAX_LOSSES reason, and the run ends 'done: <target> reached' (D3)."
   - Rejected:
     - fighting on to the settle's bound (the build's code), which allows a game loss past the cap and puts R5.LOSE3 off;
     - ending "stuck", which breaks HONESTY.
   - OPEN, and unreachable on today's targets: `rate_step5`'s R5.LOSE3_WORD (and R5.STOP, in its MAX_LOSSES-1 copy)
     expects the stop string whenever the game recorded the capped loss. A capped loss inside a settle would read "done"
     there. No grader was changed. Rule on it if a STOP or LOSE3 plan ever reaches a settle.
4. **D5 AMENDED (R5-F6).**
   - The end record's `settled` is renamed `played_out`. It is True only when the settle PLAYED a screen out; the pause
     alone is not one.
   - A "done" end also records `passed`, the milestones the story passed while the settle played. A `ch2_dad` run's settle
     passes ch2_wally (replay #48).
   - `report["milestones"]` and the MILESTONE lines are unchanged, because graders read them.
   - The builder's Q4 (what "done" means for an intermediate target) is still the orchestrator's ruling. It is now visible in
     `passed`.
5. **The end look's order (the sweep's S56), pinned ON PURPOSE.**
   - R5 reads the end screen BEFORE the wait and push watchers close (`test_r5_the_end_look_closes_the_wait_record`, G361).
     Frames that passed after the loop's last look, with a box waiting for a press, reach the wait record.
   - On a "done" end, the settle's last look is at the end's frame, so nothing is added there.

### F8. Where everything is

- **`build/r5.diff`, rewritten.** It is 581,278 bytes (`fix/write_diff.out`), in two parts:
  - `git diff HEAD` of the 5 tracked files: 883 insertions and 12 deletions;
  - the 4 new text files as `/dev/null` patches: `probe_end_screen.py` and the three evidence files.

  The 4 kept-tree zips are binary and not in it. The builder's r5.diff is kept as `fix/before_fix/r5_build_version.diff`.
  The worktree's five files before this round, with their sha256s, are in `fix/before_fix/`.
- **The fix sweep.** Its files are in `fix/sweep/`:
  - `r5_sweep_fix.py`, composed from `sweep_head.py`, the re-anchored and new mutants, by `compose_sweep.py`;
  - `results.json` and `raw/`;
  - `caught_review.txt`, each mutant's failing tests and the assertion that caught it;
  - `n15_probe.py`.
- **The replay.** Its files are in `fix/replay/`: the trees, both arms' `probe.out`, `compare_replay.out`, and the ledger's
  begin and finish outputs.
- **The ledger and the evidence.** The ledger corrections come from `fix/fix_ledger.py` (`fix/ledger_correct.out`). The
  evidence assembly comes from `fix/assemble_evidence.py` and `fix/assemble_replay_evidence.py`. The committed free read's
  selftest run is in `fix/selftest_committed/`.


## APPENDIX A. The adversarial review's findings, VERBATIM (the workflow's result; review ran about 10:25 PM to 10:47 PM, 2026-10-28)

Verdict: **FIX**.

### R5-F1 (MINOR): If the frame budget runs out during the settle, a reached target ends as an unrecorded "stopped" run, and live_step5's HONESTY check fails. D6's "reported, not hidden" is false.

- **Scenario:** The target's proof holds on the pass's look, so the settle starts (mode.py:470). Fewer frames are left in settings.frames than the settle needs: up to 45 frames (Pacing.think) on a free end, about 11,000 at ch2_dad. _bounded (mode.py:890-901) closes the skill generator in the middle of the settle and returns "stopped: not finished within N frames". _play_end never runs, so the run writes no end_screen, no report["settle"] (written only after the loop, mode.py:700), no "end" note, and no line saying the target was reached. The host's frame cap is frames + grace (host/session.py:166), so the brain's own bound fires first and exits 0, which counts as "by: ai". outcome_claim then reads False while the game's proof holds, and check_outcome (live_step5.py:342-372) records "they DISAGREE (a lie)". D3 rejected ending "stuck" for exactly this reason. Before R5 this end could not happen at this point: done returned with no frame passing.
- **Evidence:** Probe on copies, through the REAL _play loop and the REAL HandsBrain._bounded (budget 500, play-out 2000 frames): .../s53/r5/review/probe_budget_settle.py and its output .../s53/r5/review/probe_budget_settle.out. On the R5 copy: "END REASON: 'stopped: not finished within 500 frames'"; "report['end_screen']: ABSENT"; "report['settle']: ABSENT"; "'end' notes: NONE"; "told lines naming the target as reached: NONE"; "live_step5 L5.PURITY_OUTCOME with the game's proof HOLDING: Check('L5.PURITY_OUTCOME', HONESTY, FAIL ...". On copy_old (R5 + G347, the A/B's OLD arm): "END REASON: 'done: ch1_pokedex reached'" and L5.PURITY_OUTCOME PASS. Both runs exit 0. Exposure on today's graded targets (ch1_pokedex, ch2_wally) is the pause only, 14-45 frames (hands/pad.py:53), out of 300,000-330,000-frame budgets. That is rare but silent.
- **Fix:** Make the settle budget-aware. Before each round and each pause, compare self.settings.frames - hands.pad.frames with a margin. When it is under the margin, stop the settle and SAY so (a tell plus an end_screen note "budget"), then end "done". Alternatively, record report["settle"] = {started, target} before the first yield, and have play() turn a budget stop that comes after the done decision into the exact done string plus a told line. Add a PlayLoopTests case driven through _bounded (the probe is a template). Rewrite D6 in 06 with the true consequence.

### R5-F2 (MINOR): No test pins the number of settle rounds the measured case needs. DONE_SETTLE_ROUNDS = 2 passes all 224 tests but would break the graded A/B.

- **Scenario:** A later tidy-up lowers DONE_SETTLE_ROUNDS from 6 to 2. Every unit test stays green. On the measured ch2_dad end, round 1's pause finds WALLY's tutorial and round 2 plays it out. Round 2's pause then finds DAD's gym text printing, and with 2 rounds the loop exits there. The run ends "done" NOT free: the same class of failure the A/B graded OLD on. The comment at mode.py:122-128 says "The measured case took THREE", but test_r5_the_settle_is_bounded reads the constant, and no test models a three-round chain.
- **Evidence:** Ad-hoc mutants, each applied to a fresh copy with the anchor occurring once, then test_goals run: .../s53/r5/review/mutant_runs.py; output .../s53/r5/review/mutant_runs.out. RV4 (DONE_SETTLE_ROUNDS = 2): "NOT CAUGHT (every test passes); exit 0; ran 224". RV4b (= 1): CAUGHT by test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen. The measured round count comes from the A/B's saved action logs (.../s53/r5/review/settle_rounds.py; output .../s53/r5/review/settle_rounds.out): every NEW run has exactly 3 pauses. For seed 5351: pause 1 at 226470 is followed by "busy 471f ... a scene plays"; pause 2 at 233034 by "busy 81f reading along: a text is printing"; pause 3 at 237586 by the end line. Seeds 5352-5354 show the same pattern. That RV4 would fail the A/B on 4 of 4 seeds is DERIVED from these saved logs and the loop's code. I did not replay it live.
- **Fix:** Add a PlayLoopTests case that models the measured chain: free for one frame, then a scene; the play-out ends on a one-frame-free warp exit, then a second scene, then free. Assert 3 rounds, 2 play-outs and a free end. Register a mutant 'DONE_SETTLE_ROUNDS = 2' predicted CAUGHT.

### R5-F3 (MINOR): Nothing in the repo can detect a live regression of the measured failure. The end record is blind to it, and ledger rows #43-#46 cite session-scratch evidence.

- **Scenario:** After the commit, end_screen.free is the AI's own single-frame nav_free. It read True on all 4 OLD ends that the game held NOT free. The harness-side held free read (probe_end_screen.py and its 5-case selftest), the A/B driver ab_probe.py and the grader ab_summary.py exist only in this session's scratch. The committed ledger rows' evidence fields point at "session scratch s53/r5/...", which no later session can open. Together with F2, a regression of the measured case would pass every committed gate and leave no readable trace.
- **Evidence:** SUMMARY.txt (.../s53/r5/ab/SUMMARY.txt): each OLD row reads "free_held False ... AI nav_free at end: report True" (AB-REPORT CAVEAT 2). The ledger rows (.../s53/r5/review/ledger_tail_copy.out) for #43-#46 carry evidence "session scratch s53/r5/...". BUILD-REPORT section 7 Q3 (commit the probe?) is still open. Kept trees are tracked in the repo: git ls-files ai_player/evidence/trees lists 64 zips. The worktree holds two untracked zips: 29a5dc81286162ff (the tree that #44-#46 name) and 2736e5bb787f9e67 (an intermediate DONE_SETTLE_ROUNDS-4 tree; every builder gate ran on files digest a813b45287d8e507, the final tree).
- **Fix:** Before the commit: commit the held free read and its selftest as a gate, or at least the A/B driver, grader and SUMMARY.txt under ai_player/evidence. Point the ledger evidence fields at committed paths. Stage 29a5dc81286162ff.zip and NOT 2736e5bb787f9e67.zip, by explicit path.

### R5-F4 (NIT): The call census never inspects calls inside a NEW function, so the settle's play_out, tell and note calls have no registered mutant

- **Scenario:** call_census.py:375 traces added calls only when `qualname in old and status == "changed"`, so every call inside _settle_before_done and _end_screen is skipped. Build deviation 2 relied on this ("the census needs no new waiver"). The census therefore reports 0 MISSING while the core play_out call and the 'said' tell and note have no mutant. The tests do catch these deletions.
- **Evidence:** Builder's census (.../s53/r5/build/call_census.out): 6 findings, none for play_out, tell, note or busy_reason inside the settle. My ad-hoc mutants (.../s53/r5/review/mutant_runs.out): RV1 (the settle's play_out deleted) CAUGHT by 5 tests; RV2 (the tell and note deleted) CAUGHT by 2 tests; RV3 (the settle's guard removed) CAUGHT, including the U3 control; RV5 (retry after a stop) CAUGHT; RV6 (end record read before the settle) CAUGHT.
- **Fix:** Register RV1 and RV2 as revert_step5 mutants (for example G352 and G353). Optionally, make the census treat every call inside an added function as an added call.

### R5-F5 (NIT): A MAX_LOSSES-th loss inside the settle is ignored, the settle can fight on, and no test covers it

- **Scenario:** The settle discards _count_losses' stop (mode.py:689). A third loss inside the settle does not end the settle: it can play up to its remaining rounds, and the run ends "done". That agrees with D3, since the proof holds. But in a STOP-plan copy (MAX_LOSSES 1), a loss inside a settle would end "done", while R5.STOP (rate_step5.py:915, STOP_REASON at :348) and R5.LOSE3_WORD (:2829) expect the stop string. Today's ch1_pokedex settles are only a pause, so this is not reachable now.
- **Evidence:** RV7 (the settle breaks off on that stop): "NOT CAUGHT (every test passes); exit 0; ran 224" (.../s53/r5/review/mutant_runs.out).
- **Fix:** Rule on the intended behaviour in 06, and add a unit test that pins it.

### R5-F6 (NIT): End-record wording: `settled` means "played something out", the milestone list goes stale, and the cost is understated

- **Scenario:** D5 asked for "whether the settle ran". With deviation 1 the settle always runs on a done end (the pause), so the builder redefined `settled` as played > 0, and a NOT-free end carries settled True (U2 asserts it). The settle can play past later milestones: the A/B's NEW ends are at VAR_PETALBURG_GYM_STATE 2, which is ch2_wally, yet the end line lists milestones only up to ch2_dad. The build report gives the free-end cost as "16 to 26 frames", but Pacing.think is (14, 45) and the PF-17 control paused 44.
- **Evidence:** .../s53/r5/ab/end_marks.txt (NEW ends: VAR_PETALBURG_GYM_STATE 2, map [8, 1]); .../s53/r5/ab/SUMMARY.txt (control: paused 44); hands/pad.py:53; mode.py:722 (settled=bool(settle.get("played"))).
- **Fix:** Rename the field to played_out, or document what it means. Record or say the milestones passed during the settle (builder Q4). Use 14-45 frames in the docs.

### R5-F7 (NIT): Ledger #43 reports R5-tree runs on already-played seeds without a replay entry; deviation 1 is load-bearing and needs an explicit ruling

- **Scenario:** #43's verdict reports R5-tree runs on seeds 5301-5303 (devab new, arms new) under an entry whose tree is the pre-R5 digest 53e0c26e7812db47. ledger.py:19 says such runs are replays, "written and reported as a replay"; the A/B did this for #44. Separately, deviation 1 (the pause) contradicts D4 and the U1 CONTROL, but it is the ONLY thing that discriminated. If it is stripped (BUILD-REPORT Q1 option b), the NEW arm reduces to OLD by code on all 4 held-out seeds.
- **Evidence:** .../s53/r5/review/ledger_tail_copy.out (the #43 text); .../s53/r5/ab/runs/new_ch2_dad_5351/hook.json and .../s53/r5/ab/extra.txt ("AI nav_free on its look True" on every NEW loop top); .../s53/r5/review/revert_r5_mutants_copy.out (G349 CAUGHT).
- **Fix:** Add a replay entry for those runs, or reword #43. Ratify deviation 1 in 06 by amending D4 and U1, and keep the pause.

### R5-R0 (INFO): What held under review, and what this review did NOT do (review ran about 10:25 PM to 10:47 PM LA, 2026-10-28)

- **Scenario:** These are checks that found NO defect, plus the limits of this review.
- **Evidence:** HELD. test_goals passes on a byte-identical copy: "Ran 224 tests", "OK", exit 0 (.../review/test_goals_copy.out). Independent revert_step5 run of G0, G226-G228 and G347-G351 on the copy: "8 mutants CAUGHT as predicted", FROZEN TREE PASS, files digest a813b45287d8e507 (the same as the builder's), exit 0 (.../review/revert_r5_mutants_copy.out). All 36 pre-existing mode.py mutant anchors occur once and sit in the same function before and after R5, so none moved; G226 still mutates the done check, and the 5 new anchors are unique (.../review/anchor_check.out). The 24 rate_step5.EXTRA_EDITS and 23 revert_safety_gates edits occur once (.../review/extra_edits_check.out). Fairness and purity pass on the copy, with no new .marks read (.../review/check_fairness_copy.out, .../review/check_purity_copy.out). ledger --check: "46 entries; well formed -> PASS" (.../review/ledger_check_copy.out). The A/B is not vacuous: it counted 4 of 4 seeds, the loop-top states are byte-identical, and NEW reaches a free end only by pressing through (no await over 150 frames). The exact done strings are unchanged. NOT DONE: no emulator run (the live effect of RV4 is derived, not replayed); no full regression lane; no run_units, rate_step5, live_step5 or revert_safety_gates; only the 9 named revert_step5 mutants; no re-run of the A/B, its grader or the free-read selftest; the decomp facts were not re-verified. Nothing was edited in the worktree, the main checkout (git status clean) or the tuner clone. Git was used read-only (status, diff --stat, show, ls-files, check-ignore, config --get).

## APPENDIX B. The independent mutant sweep's survivors, VERBATIM (the workflow's result)

56 run, 43 caught, 13 survived. Each survivor is now caught (FIX ROUND F2 above):

- S04 (mode.py:465) the settle is SKIPPED when milestone is None (`if milestone is not None and index > target`). No test reaches milestone None. ch4_roxanne (badge 1) is the last required milestone, and GoalManager.milestone returns (len, None) once all are passed, so a badge-1 run ends through exactly this branch (code reading, not run live). Probe p04: the unchanged code plays the box out first, the mutant does not ([] != [R5_WHY]).
- S23 (mode.py:128) DONE_SETTLE_ROUNDS 6 -> 2. The tests pin only >= 2 (S24's value 1 is caught). The measured ch2_dad end needed 3 rounds; that is the builder's development measurement, not re-measured here. Probe p23, a unit-harness model of that chain: at 2 the run ends 'done' on a screen NOT free (held by 'watching: a scene plays').
- S26 (mode.py:700) report['settle']['frames'] is always 0. No test reads it (probe p26: 0 != 203).
- S27 (mode.py:701) report['settle']['free'] is always True. No test reads it (probe p27: True is not False).
- S35 (mode.py:703) in the settle's told line and end_screen note, what holds the screen becomes None (busy_reason not called). Only _end_screen's held_by is tested (probe p35: None != 'watching: a scene plays ...').
- S37 (mode.py:717) _end_screen reads hands.last instead of a fresh hands.look(). After a play-out that ends the run at MAX_LOSSES and frees the screen, the end is recorded as NOT free (probe p37). Shown only in the unit harness, whose stand-in play_out takes no looks.
- S40 (mode.py:719) end_screen['frame'] is None. No test reads it (probe p40: None != 1003).
- S45 (mode.py:722) end_screen['settle_frames'] is 0. No test reads it (probe p45: 0 != 203).
- S46 (mode.py:723) end_screen['paused'] is 0. No test reads it (probe p46: 0 != 3).
- S53 (mode.py:706) the end_screen note's target, frame and played are dropped (only its stop is tested). Probe p53: (None, None, None) instead of ('ch1_pokedex', 1000, 1).
- S54 (mode.py:704) the told line's fallback wording is dropped: an unsettled end with no play-out stop says '(None)' instead of '(a scene still plays)' (probe p54).
- S55 (mode.py:754) the end LINE says 'NOT free' without what holds the screen. The tests check only the 'NOT free' text (probe p55).
- S56 (mode.py:729) the end record is read AFTER the wait and push watchers close (R5 reads it first). The order is not pinned: probe p56's 100-frame wait for a press is recorded as 0. The flip side, not measured live: R5's order lets the end look extend the graded wait record, which the pre-R5 code had no end look to do.
