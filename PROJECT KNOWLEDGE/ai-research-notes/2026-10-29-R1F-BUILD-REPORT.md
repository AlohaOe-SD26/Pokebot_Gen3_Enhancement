> **Filed 2026-10-30** by the orchestrating session. Below section 0 are the hand-back sections of every agent of the
> workflows `r1f-build` (22.69 Mtok input-equivalent) and `r1f-fix2` (2.41 Mtok), verbatim, in run order (the harness refuses report files from
> subagents, so each returned its section). The spec: `2026-10-29-R1F-BUILD-SPEC.md` (its box holds the orchestrator's rulings
> 1-10). Decisions: `06` 2026-10-30; the change: `07` 2026-10-30; mistakes: `08` 2026-10-30.

# R1 + R2 FOLLOW-UP BUILD REPORT: the review's and the verification's open findings closed, a refused reset ends the game, and two new live arms (2026-10-29/30)

## 00. The orchestrator's checks and rulings

- **Two STOPs, both by the spec's own rules, each ruled on and resumed** (`06` 2026-10-30): stage 1 at step 3(b) (the
  reset-refusal harness's crash case: the default brain never raises) → rulings 8-10 (the case uses `AI_PLAYER_FAULT_RAISE=1`;
  `test_host` honours `AI_PLAYER_TEST_SUPPORT_ROOT`; two extra purity plants accepted); stage 2 at step 5 (CHAIN counted on 2 of
  6 development seeds: the AI healed and saved AGAIN at the Pokémon Center before going anywhere new) → rulings 11-13 (CHAIN's
  kill re-anchors on B's LATEST save; the checks follow the save C continues; CHAIN re-run: 6 of 6).
- **The verification's VR-1 (MINOR, test-only) closed in a second fix round** (`r1f-fix2`): the latch is now pinned ahead of
  EVERY other end `_on_frame` can reach (`interrupted` and an all-ends-due case), with 9 reorder mutants registered; an
  independent check built 32 reorders and every one fails. The final tree differs from the graded runs' tree
  (`d765751fcb18aad8`) in three test-side files only (`gates/test_host.py`, `gates/revert_r1.py`,
  `gates/run_regression_times.json`); the AI and host code are byte-identical (`provenance.py --compare`).
- **Applied to `main`** from the worktree `wf_810d6b51-d6f-1` (`s53/r1f/apply/apply_r1f.py`): 34 files sha256-checked;
  `ai_player/README.md` merged by hand (`main` had changed it since the worktree's base); 11 tree zips no new evidence names
  were left out.
- **On `main` before the commit:** `test_host` (whole) `Ran 37 tests ... OK`; `test_kb2` OK; `run_regression.py --quick`
  `REGRESSION: PASS (quick, 21 suites, 21.6 s wall)`; `ledger.py --check` 61 entries PASS; `run_gates.py --quick`: `ALL 141 ENFORCING GATES PASS  (875.8s total)   [+2 ADVISORY probe(s) — run, NOT gated]`;
  Tier 0 and Tier 1 (`07`). The full lane runs after the commit.

## 0. In plain words

- The gaps both reviews found in R1 + R2 are closed: more ways for the AI's code to dodge an exit are refused; if the AI ever
  presses the reset combination, the controller blocks it and the game ends for good (USER RULING 53); the fairness gate
  sees more ways of reading the play time; a damaged memory line is refused; a save no longer counts against the AI's
  curiosity limit.
- Two new live tests: the AI continues after a kill, plays on, saves again, is killed AGAIN and continues again, and its
  memory is exactly as of its newest save; and a continue that runs out of time can simply be retried.
- The proof: on 4 games it had never seen, every test passed (the new chain test counted on 3, its floor); a separate agent
  repeated it on 4 more and agreed; after the review's fixes it passed on 4 more, and a fresh agent agreed on 4 more.
- Left for the next item (U2's build): three small gate and budget findings, listed in `06`.

# Stage offline (builder; stop=True)

> Hand-back section, verbatim.

## Stage 1 (offline): the builder's report, stopped at step 3(b)

**Worktree:** `C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_810d6b51-d6f-1`, HEAD `f4412116`. Nothing is committed and no git writes were made. Every output named below is in `s53/r1f/build/s1-offline/`. Each output file starts with its command, its start and end time and its exit code. The part (a) diff is `stage1-partA.diff`.

### STOP: the spec's step 3(b) STOP rule fired
Step 3(b) says to measure the `reset_refusal` harness's two assumptions first, and to stop if either fails (`step3/b-measure.out`, 6:35 to 6:41 PM PT; script `measure_reset_refusal.py`):
- **A1 holds.** In a harness subprocess, `modules.context.context.emulator` takes a `SimpleNamespace` fake, and the real `Controller.tap("B")` presses through it (`[('press','B')]`).
- **A2 fails.** The spec's case (3) is `Session(RunOptions.from_env(), None)` with no `start()`, and `session.run()` driven with `next()`. With the harness's environment (`AI_PLAYER_*` stripped), `from_env()` picks the **default brain, `placeholder`**, which only calls `controls.wait(1)`.
  - Result: **2,000 steps, no exception, no button call, no verdict file.**
  - So case (3) and its CONTROL (b) ("case (3) with no latch ends `crash`/2") cannot happen as written, and mutant L16 would have no catching test.

Two other setups were measured for the respecification. They are reported only, not adopted:

| setup | result |
|---|---|
| `AI_PLAYER_BRAIN=watcher` | `crash`/2 at step 1 (`AttributeError: 'NoneType' object has no attribute 'is_emerald'`) |
| the existing fault switch `AI_PLAYER_FAULT_RAISE=1` | `crash`/2 at step 31 (`RuntimeError: AI_PLAYER_FAULT_RAISE: injected brain fault`) |

The second is deterministic and needs no emulator state. Choosing a setup is the orchestrator's call.

How the measurement ran: the Session imports `mgba` (through `host/attribution.py`), and the worktree has none. So the measurement used the MAIN checkout's `sandbox-pokebot` as a read-only build root (`PYTHONDONTWRITEBYTECODE=1`, working folder in scratch). A `find -newer` check over that folder found no file written.

### Step 2: every finding re-verified, with no difference
All 8 probes were re-run on a copy of the worktree's `ai_player`: `probe_gates`, `probe_readbook`, `probe_launches`, `scan_exit_forms`, `scan_except`, `mine/probe_plants_all`, `mine/probe_plants_pc` and `mine/scan_forms`. The old tree came from `git archive 67c73a0f`. `step2/compare.out` compares each output with the spec author's, after normalising temp paths: **all 8 SAME** (for example, `SAME  probe_gates.out (22 lines)`).

### Before the change: the anchor census
- `step3/anchors-baseline.out`: `900 anchors checked, 0 not exactly once`. That covers every anchor of revert_r1, revert_step5 and revert_safety_gates.
- It also lists every mutant whose anchor lies in a function this change edits:
  - census mutants C046-C059, C146, C156, C161, C172, C174, C196-C203, C229, C230, C264, C265, C270;
  - F009-F011, F018, F031-F033;
  - FX3, L1, L7, L9, S24, S25, S33, S39;
  - revert_step5's G147-G150, G152 and G313 (in `after_goal`).

### Part (a): purity D1, built and green
**`gates/check_purity.py`:**
- `PLAY_LOOP_EXIT_NAMES` gains `GeneratorExit`, `BaseException`, `BaseExceptionGroup`, `ExitStack` and `AsyncExitStack`. These are refused as a name (the existing `visit_Name` line, S40b's anchor, is unchanged), as an attribute (`contextlib.ExitStack`) and as an imported name.
- New rule-"b" checks, in play-loop files only:
  - `visit_ExceptHandler` refuses a bare `except:`.
  - `visit_Try`/`visit_TryStar` with `_check_finally` refuse a `return`, `yield`, `yield from` or `await` reached from a `finally` (a nested def, lambda or class is its own scope). They also refuse a `break` or `continue` there, unless it is inside the BODY of a loop nested in the `finally`.
  - `visit_FunctionDef`/`visit_AsyncFunctionDef` refuse `__exit__` and `__aexit__`.
- The docstring's rule (b) lists the new forms and says why.

**`gates/test_check_purity.py`:**
- FAULT: `EXIT_PROBES` gains X07-X18 (the spec's) plus X19 and X20.
- CONTROL: `EXIT_FORMS_CONTROL` (the mentions, `except ValueError:`, `def exit_menu`, and a `finally` holding a nested def with a return and a yield, and loops with their own break/continue) passes.

**`gates/revert_r1.py`:** mutants S40c, S40d, S40e, S40f and S40g, each predicting `PlayLoopExitTests.test_the_play_loop_cannot_exit`.

Checks (last lines verbatim):

| check | output file | last line |
|---|---|---|
| PlayLoopExitTests + ControlTests | `step3/a-purity-tests.out` | `Ran 4 tests in 34.394s` / `OK` |
| the whole `test_check_purity` | `step3/a-test_check_purity-full.out` | `Ran 30 tests in 285.023s` / `OK` |
| the purity gate on the real package | `step3/a-check_purity-cli.out` | `VERDICT: PASS` (no new rule fires on it, as section 1.1 measured) |
| `revert_r1.py S40c,S40d,S40e,S40f,S40g` | `step3/a-mutants.out` | `5 mutants CAUGHT as predicted, 0 REDUNDANT ALONE as predicted, of 5 run (473 defined)` / `OVERALL: PASS` |
| anchors after the change | `step3/a-anchors.out` | `905 anchors checked, 0 not exactly once` |

Which plants each mutant broke:
- S40c broke 7 plants (X07-X11, X16 and X19).
- S40d broke X12.
- S40e broke X13, X14, X18 and X20.
- S40f broke X15.
- S40g broke X17.

### Deviations from the spec, and why
1. **Two extra plants close aliases of the same forms.**
   - X19, `from contextlib import ExitStack as Stack`: without the import check, an alias evades both the name check and the attribute check.
   - X20, a `break` in the `else` of a loop nested in a `finally`: that `break` targets the OUTER loop and discards the exit. So only a nested loop's BODY owns its `break`/`continue`.
2. **The attribute and import checks use `PLAY_LOOP_EXIT_CLASSES`** (the exit names minus `exit` and `quit`). `.exit` and `.quit` are ordinary method names on other objects, and `sys.exit` is already rule (a)'s. S40c shrinks the base set, so it removes these from both checks too.
3. **The anchor census before the change was a static check** (each anchor exactly once), not a full `revert_r1` run, which takes about 917 s. The full run belongs once, after all parts.
4. **Found for later stages, not acted on.** The `reset_refusal` harness mutants (L15, L16 and the Session-wiring census mutants) run from `revert_r1`'s temp COPY. There, `test_host`'s `BUILD_ROOT` (`REPO/sandbox-pokebot`) does not exist, and `run_harness_raw` strips `AI_PLAYER_*`. Unless `test_host` takes `BUILD_ROOT` from `AI_PLAYER_TEST_SUPPORT_ROOT` (and passes it to the subprocess), those mutants cannot be caught even on the main checkout. `test_host:ControllerTogetherTests` itself does run in the worktree (`Ran 1 test ... OK`).

### What I did NOT do
- Parts (b) to (g) (controller latch, session, launcher row, fairness, read_book/read_launches, judge_end, D6, the live_r1 headline) were not started, because of the STOP.
- None of the closing checks ran: `call_census`, the full `revert_r1`, `revert_step5`, `revert_safety_gates`, the quick lane.
- `test_host` and `test_kb2` were NOT RUN in the worktree (orchestrator ruling 6), and the `reset_refusal` harness was not written.
- No live steps. No README, docs or `06` edits.
- One untracked by-product should not be committed: `ai_player/evidence/trees/fb388f63f919b88b.zip`, written by `revert_r1`'s `snapshot_tree` during the 5-mutant run.

# Stage offline-2 (builder; stop=False)

> Hand-back section, verbatim.

## Stage 1b (offline, continued): parts (b) to (g) and the closing checks

Everything offline is built and every closing check passed: call_census reports 0 MISSING with no new waiver, all 502 revert_r1 mutants did as predicted, revert_step5, revert_safety_gates and the quick lane passed. Nothing is committed.

Worktree `C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_810d6b51-d6f-1`, HEAD `f4412116`, changes uncommitted. Times below are Los Angeles time, 2026-10-29. Every output is under `s53/r1f/build/s1b-offline/` (subfolders `b/`, `c/`, `d/`, `e/`, `f/`, `g/`, `census/`, `close/`). The full diff is `close/worktree.diff`.

### What was built
- **(b) D2, the latch.**
  - `host/controller.py`: the held-button set is private (`_held`), and `held` (a frozenset) and `refused` are read-only properties. A refused combination sets `_refused`; from then on every `tap` and `hold` is refused before it touches a button, while `wait` still runs. The S39 line is byte-identical.
  - `host/session.py`: `_end_if_refused()` ends the run `reset-refused` with exit 9. It is checked first on every frame in `_on_frame`, and in `_steps` when the brain returns, crashes or exits by itself.
  - `host/launcher.py`: the END_CLASSES comment names `reset-refused` as NOT CLEAN. `_INVOLUNTARY` is unchanged.
  - `test_host` (ruling 9): BUILD_ROOT honours `AI_PLAYER_TEST_SUPPORT_ROOT`, and `run_harness_raw` passes that one variable on.
  - `ControllerTogetherTests` uses a fresh controller per case and gains a latch test and a held-set test (which includes purity plants).
  - New `ResetRefusalTests` run the `reset_refusal` harness, with case (3) using the fault switch `AI_PLAYER_FAULT_RAISE=1` (ruling 8).
  - `test_the_end_classes` gains two `reset-refused` rows, both NOT CLEAN.
  - Mutants L11, L12, L13, L15, L16, L17 and a new L18.
- **(c) D3:** RULE C in `check_fairness` also fires on:
  - the `'play_time'` constant (not as a dict display key, a docstring, f-string text, or getattr's own argument);
  - a match-class keyword `play_time=`;
  - `asdict` and `astuple`.

  A class pattern with positional sub-patterns is refused in all deciding code, as both RULE C and RULE A. The docstring records that `vars` and a non-constant `getattr` are left to the purity gate. Plants F2 to F12 with CONTROLs, a test for the two-gate cover, and mutants S46c to S46f.
- **(d) D4 and D7:** `read_book` refuses a non-ASCII header or middle line (the decoding is unchanged). `read_launches` turns a non-UTF-8 file into its refusal sentence. Two tests; mutants M14 and L14.
- **(e) D5:**
  - `EndJudgement` and `judge_end` count every continue they look through and name the newest reason, with no cap.
  - The FX3 and L7 lines are byte-identical.
  - `ContinueCheck` gains `looked_through`, and the CLI's CONTINUE line reports it.
  - New test `test_the_look_through_is_counted_and_told` and mutants FX8 and FX9.
  - C230 is regenerated as C230b; S33 and F014 are re-anchored.
- **(f) D6:** a save neither ends nor joins a curiosity row (`after_goal`) or a grader streak (`curiosity_streaks`, `aside_streaks`). Two tests; mutants V6a, V6b and V6c.
- **(g) V2-1 and V2-2:** the caveat counts the midpoint arm's passes and names its failing seeds. `verdict_line()` builds the one verdict line, which is both printed and written to `verdict.json` as `headline`. Selftest cases and the FAULT `caveat_passes_ignored`; `LiveR1HeadlineTests`; mutants LV1 and LV2.
- **Census:** 9 generated mutants, RF01 to RF09, with predictions recorded from their first run. No waiver was added.

### Checks (last line of each)
| check | result |
|---|---|
| full revert_r1 | `501 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as predicted, of 502 run (502 defined)` / `OVERALL: PASS` (7:29 to 7:47 PM). Control R0: 414 tests, none failing |
| revert_step5 | `400 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 402` / `OVERALL: PASS` |
| revert_safety_gates | `23 mutants CAUGHT as predicted, of 23` / `OVERALL: PASS` |
| quick lane | `REGRESSION: PASS (quick, 21 suites, 22.0 s wall)` |
| call_census | `33 sites; 0 MISSING` / `CALL-SITE CENSUS: PASS`; `census_waivers.json` unchanged |
| test_check_purity | 30 tests OK |
| test_safety_gates | 50 tests OK |
| test_host (run in the worktree, ruling 9) | 31 tests OK |
| test_battle | 107 tests OK |
| test_saving | 137 tests OK |
| test_goals | 256 tests OK |
| check_purity | `VERDICT: PASS` |
| check_fairness | `PASS (0 breaches)` |
| live_r1 selftest --all | `the clean run PASSES (32 cases) and 7 of 7 planted faults FAIL as they must -> PASS` |
| ruling 9 CONTROL | without the variable, BUILD_ROOT is REPO/sandbox-pokebot: True |
| main sandbox-pokebot | `paths newer than the marker: 0` (marker 6:52 PM, last check 7:59 PM) |

The process census showed no `run_regression.py` running before any step that used the main checkout's sandbox. Three hits at 7:58 PM were my own shell wrappers, whose command lines contain that word; I confirmed this at 7:59 PM.

### What I measured
- The harness cases end as follows:
  - Latched cases (`on_frame`, `caught`, `crash`, `returned`, `stray`) all end exit 9, `reset-refused`, with START never pressed.
  - CONTROL cases end as before:

    | CONTROL | end |
    |---|---|
    | `control_a` | no end |
    | `control_b` | 2, crash |
    | `control_returned` | 5, brain-returned |
    | `control_stray` | 2, stray-exit |
- The first M14 run was caught only by the header case. A bad byte in the session's `how` field is already refused by another line check, so that case could not show the new check working. I moved the case to the free-text `run_dir` field, and then all three cases were caught.

### Deviations from the spec, and why
1. **`Session.run` is unchanged.** The return, crash and stray-exit checks live in `_steps` instead. Any change to `run` makes call_census list every `.run(` call in the AI code as a site, matching by name (14 sites). Three are launcher `subprocess.run` calls that no unit test runs, so only waivers could close them, which ruling 5 forbids. The behaviour is the same: GeneratorExit passes through untouched, and the lifecycle's own exit is never replaced.
2. **`classify_end` is retired; `judge_end` replaces it.** The spec's thin 3-tuple wrapper would have no call site in the AI code, which the census reports as UNCALLED, again closable only by a waiver. S33 and F014 are re-anchored, and C230 is regenerated as C230b with the same predicted tests.
3. **Two extra harness cases, `returned` and `stray`, with CONTROLs, and mutant L18.** The spec's three cases did not cover the return and stray-exit call sites, so nothing would fail if those calls were deleted.
4. **Case (2) drives its frame through `session.guard.handle_frame`**, the path the framework uses, so the two guard-listener census sites (RF07, RF08) are caught.
5. **The support root is honoured whenever the variable is set**, as in test_battle and test_eyes, not only when the hook file is missing. The worktree has the hook but no `mgba`, so the narrower condition would not let test_host run here.
6. **Three test inputs changed so the fault half can actually fail:**
   - The non-ASCII header byte goes in the header's game string; as specified, it would read no_header on the old code too.
   - The middle-line cases use the session's `run_dir` field (see the M14 finding above).
   - The named-getattr plant builds its name (`'play' + '_time'`), because `FIELD = 'play_time'` now trips RULE C by itself.
7. **Name-collision census sites are closed by honest mutants, all caught.** Where more than six tests failed, the six shown in the runner's line are recorded as the prediction.
8. **The README is partly updated (part (k)):** the ruling-52 bullet, the unit counts, a follow-up paragraph, and KNOWN LIMITS trimmed to the two live arms still to build.

### What I did NOT do
- **Spec step 4 onward is not started:** the `live_r1` arms (CHAIN, CHAIN-OLD, CHAIN-R1-OLD, R2-RETRY, R2-RETRY-OLD), the SaveWatch tail fix and N-rule, the test-side reader, new registered numbers, the ledger and seeds, and every live run.
- **README:** the four "(a COPY)" rows in "Fault and control switches" belong to the live arms and are not written.
- **Not updated:** `run_regression_times.json`.
- **Not touched:** the 06/07 docs; no git writes.
- **Not run:** test_kb2 (ruling 6).

### For the commit
The untracked evidence to keep is `ai_player/evidence/2026-10-29-r1f-REVERT.txt`, `2026-10-29-r1f-step5-REVERT.txt` and their tree zip `evidence/trees/88f77fabb5f514c2.zip`. The other ten `evidence/trees/*.zip` files are snapshots from interim mutant runs and should not be committed.

# Stage live-dev (builder; stop=True)

> Hand-back section, verbatim.

## Stage 2 (live development): spec section 8 steps 4, 5 and 6 — STOPPED at step 5

**Result: STOP (spec section 8 step 5).** CHAIN counted on **2 of 6** development seeds. The rule is "STOP if CHAIN counts on fewer than 4 of 6".

Everything else passed in development:
- R2-RETRY counted and passed on 6 of 6.
- Every OLD arm showed its difference on every seed.
- `live_r1.py selftest --all` is green.
- Nothing was tuned: the AI's policy, the moments, `SAVE_MIN_MINUTES`, e4 and the watcher's rule are unchanged.

Started 8:01 PM. Last check 8:33 PM (Los Angeles time). Outputs are under `s53/r1f/build/s2-live-dev/`.

### Why CHAIN does not count on 4 seeds (the STOP)
On 5501, 5503, 5505 and 5506 the sequence was the same:
1. Child B's first save S3 was at the OLDALE POKEMON CENTER.
2. B then walked only maps it already knew (Oldale, Route 101, the Center).
3. B healed and pressed START for a second save **before** it stood on any map new to S3.

Rule N1 therefore recorded "a save began first" and B ran to its own end without being killed, as the spec says. Route 103 (0:18) was B's first new map, 2,948 to 18,919 frames after that second START.

Seed by seed (`analyze-rule-n.out`), second START vs first new map:

| seed | second START | first new map (0:18) |
|---|---|---|
| 5501 | 60,753 | 63,701 |
| 5503 | 25,690 | 45,123 |
| 5505 | 61,509 | 64,412 |
| 5506 | 33,644 | 36,583 |

On 5502 and 5504, B entered OLDALE_TOWN_MART (2:4) 919 and 913 frames after its e4, and rule N1 fired there.

**Report only, not adopted:** measured from B's LATEST save before its first new map, the same rule would be met on all 6 seeds (save k = 2, 1, 3, 1, 2, 2). But child C would then continue a later save, while CH1's difference exists only in B's FIRST save line. C3 would have to read that line by id. That is a respecification, and it is the orchestrator's decision.

### What was built (step 4)
**`live_r1.py`**
- The arms:
  - CHAIN, CHAIN-OLD and CHAIN-R1-OLD (`chain [--old ...] --from-row K-SILENT row`), on K-SILENT's frozen set (ruling 1). The known maps are child A's maps up to S1.e3 (ruling 3).
  - R2-RETRY and R2-RETRY-OLD (`r2 [--old] --from-row`).
- The functions behind them: `cmd_chain`, `cmd_r2`, `grade_chain` (C1-C6, with C4 reported only), `grade_r2` (R1-R3), `run_continue_child` and `freeze_profile`.
- Also updated: EXPECTED, COUNTING, discriminators (9 per seed; a side with no value is no difference) and registered_numbers. HELD_OUT is now (5551, 5554).
- **SaveWatch tail fix:** the memory tail starts at the frozen file's size, and a save line attaches only if its id is at least the frozen file's `next_save_id`.
- **Child B's maps** count from the held free arrival on, and rule `N<k>+<frames>` is implemented (`_rule_n`).
- **Test-side reader** (`memory_lines`, `rebuild_payload`): imports nothing from `ai_player`, and is stricter than the verification's port.
- **New planted faults (5):** chain_parent_ignored, chain_last_save_ignored, pre_maps_ignored, stale_line_attached, lookthrough_ignored.
- **New selftest cases:** the CH1, FX1 and FX3 edits equal revert_r1's; recorded rows from #57.

**`revert_r1.py`:** mutant CH1, anchored at `game_memory.py` (worktree line 742; ruling 2's text), predicted to be caught by `MemoryFileTests.test_rebuild_follows_the_parent_across_a_continue`.

**README:** the four "(a COPY)" rows (R2-STOP, CH1, FX1, FX3).

### Checks (verbatim last lines)
- Reader fault test: `READER FAULT TEST: real lines read RIGHT (317 of 317), FX1-built read WRONG (161 of 161 live; C-FX1 synthesized), CH1-built read WRONG (C-CH1 parent 2; C-base) -> PASS`
- revert_r1 CH1,LV1,LV2: `3 mutants CAUGHT as predicted, 0 REDUNDANT ALONE as predicted, of 3 run (503 defined)` / `OVERALL: PASS`
- Selftest: `SELFTEST: the clean run PASSES (51 cases) and 12 of 12 planted faults FAIL as they must -> PASS`
- test_saving: `Ran 137 tests in 7.890s` / `OK`
- Quick lane: `REGRESSION: PASS (quick, 21 suites, 20.5 s wall)`
- Ledger: `LEDGER ledger.json: 57 entries; well formed -> PASS` (#57 development 5501-5506, begun 8:06 PM before any run)
- Main sandbox-pokebot is unchanged: `paths newer than the marker: 0` (marker 8:06:11 PM, checked 8:31:19 PM). No run_regression.py was running at 8:04, 8:17 or 8:31 PM.

### What was measured (development #57)

**5(a), 30 jobs, 8:06-8:15 PM.** CONTROL, K-AFTER, K-INSIDE, K-SILENT and LAUNCH all counted and passed on 6 of 6.
- CONTINUE press to arrival: 115 frames (all 12 K-INSIDE and K-SILENT child Bs), 146 (K-AFTER), 162-191 (LAUNCH, the AI's own log).
- So **R2_STOP_ARRIVAL = 57**.

**5(b), CHAIN with the measuring caps.**
- Counted on 2 of 6 (5502, 5504), both PASS:

  | check | 5502 and 5504 |
  |---|---|
  | C1 | FILE S3 |
  | C3 | parent 1, not S2's 2; chain [3, 1]; last_save is itself; stamp = RAM truth |
  | C5 | KILLED, continued save 3 |
  | C6 | holds NEW_B_pre [0:10, 0:18, 2:2]; none of NEW_B_post [2:4] |

- Arrival to kill: 46,272 and 33,964 frames (75.5 s and 62.5 s).
- Pre-arrival maps `[187 '0:0', 199 '1:4']` appeared in every child B, and the arrival gating excluded all of them (the 5(b) STOP did not fire).
- No frozen line was ever attached.
- **CHAIN_B_FRAMES and CHAIN_B_TIMEOUT are NOT set (still PROVISIONAL 120,000 / 1,800).** The 2x rule would give 94,564 frames and 300 s; the OLD arms would get 92,746 frames and 300 s.

**5(c), 36 jobs.**
- R2-RETRY: 6 of 6 counted and passing. Step 1 stopped with `...did not reach a free overworld within 57 frames`, purity CLEAN. Step 2: KILLED, `looked through 1`, arrived at S2.
- R2-RETRY-OLD: 6 of 6 show (refused CHOSEN, memory byte-identical).
- CHAIN-OLD: 6 of 6 show (parent 2). CHAIN-R1-OLD: 6 of 6 show (last_save.id 1).
- Rehearsal of the existing arms on 5501-5502: K-FIRST, K-BETWEEN (rule new, not vacuous), K-INSIDE-OLD, K-SILENT-OLD and LAUNCH-OLD all count and pass or show. K-BETWEEN-MID counts 0 of 2 (vacuous, as before).
- The OLD B's press digest up to its save's e3 equals CHAIN's B on 5502 and 5504. That is one trajectory replayed, not a replication.
- C4: the restored last_save was **not exercised** on either counted seed (no `[AI-SAVE] no save for` line).
- Ruling-51 moments seen: POKEMON CENTER for every first save, then ch1_rival_route103 and ch1_pokedex.

### Deviations from the spec, and why
- **5(a) ran early, from a snapshot.** 5(a) used only existing arms, so I ran it from a byte-checked snapshot of the worktree (AI files digest b2c408f75f6e8d55) while step 4 was still being written, before the reader's fault test. 5(b) and 5(c) ran from a snapshot equal to the worktree's `live_r1.py` at 8:19 PM. All rows are re-graded with the final code.
- **Extra arms in 5(a):** K-SILENT and LAUNCH also ran on all six seeds (ruling 1; spec 5.5).
- **R2_STOP_ARRIVAL** also counts the K-SILENT child Bs among the measured arrivals. The value is unchanged, because K-INSIDE's 115 is the narrowest either way.
- **The OLD arms have their own constants**, `CHAIN_OLD_FRAMES` and `CHAIN_OLD_KILL`, rather than reusing CHAIN's.
- **Child B also reports `mode_sha`**, which CHAIN-R1-OLD's mutant check needs. A killed child's READY payload combines its launcher check, its file hashes and the ArrivalWatch record, because it prints no RESULT.
- **The reader is stricter than the verification's port** (a delete must find its key).
- **C6's "S1's restored set"** is B's own session line's restored_maps.
- **CH1's anchor line:** 742 in the worktree vs 734 in the spec. The text is the same, so the code wins on the line number only.
- **Ledger #57 is left "started"**, because the STOP came in the middle of step 5.

### What I did NOT do
- Did not set CHAIN_B_FRAMES, CHAIN_B_TIMEOUT or CHAIN_OLD_FRAMES (the STOP).
- Did not start step 7 (held-out 5551-5554).
- Did not run the full revert_r1, revert_step5 or revert_safety_gates; no AI or host code changed in this stage.
- Did not run test_host or test_kb2 in this stage.
- Did not update `run_regression_times.json`.

**By-product, do not commit:** `ai_player/evidence/trees/04c41375ba381951.zip`.

# Stage live-dev-2 (builder; stop=False)

> Hand-back section, verbatim.

### Stage 2b: CHAIN re-run under rulings 11-13 (development #57)

**Result:** CHAIN now counts and passes on all 6 development seeds (5501-5506). The step-5 STOP rule (fewer than 4 of 6) does not fire. The budgets are set, ledger #57 is finished and the selftest passes. All times are Los Angeles time, 8:38-8:53 PM.

**What I built** (only in `ai_player/gates/live_r1.py`; plus `ledger.json`, where #57 is now finished)

- **The kill rule, in the live watcher (ruling 11).** `SaveWatch._rule_n` now measures from child B's *latest* completed save, not only its first.
  - Until B steps onto a map new to that save, each save B completes moves the anchor to itself.
  - A START pressed since the anchor's e4 blocks that anchor (recorded as `blocked`). The rule then waits for B's next completed save.
  - The old behaviour (record "refused" and make B unkillable) is removed.
  - The kill record now carries the anchor, its e3 and e4, and the list of every anchor.
  - `presses_digest_e3` still measures to B's *first* save, which the determinism line with the OLD arms needs.
  - The kill spec string is still `N1+30`.
- **The grader (ruling 12).**
  - `replay_rule_n` works the rule out again from B's own record (its saves, its maps from the held arrival, its START presses), never from the watcher's state.
  - CHAIN counts only when:
    - that replay finds the rule met;
    - the watcher's kill names the same anchor, map and entry frame;
    - S_k's e4 comes before the kill, with no START since it;
    - NEW_B_pre is not empty.
  - **C1:** the frozen cart, re-read by the probe's parser, holds S_k by its truth, and no other save of B's.
  - **C3:** B's first line after the continue, read by id, has parent = S1's id and not S2's, and its stamp is the RAM truth. In addition (`chain_lines`):
    - every later B line chains to the B line before it;
    - every line rebuilds;
    - every rebuilt `last_save` holds its own id and stamp.
  - **C5:** child C's memory check is ok with class KILLED, C continued S_k's id, and C arrived at S_k's truth. S_k's line is found by identity: the one B line whose stamp equals S_k's RAM play time.
  - **C6:** NEW_B_pre and NEW_B_post are now cut at S_k's e3.
  - CHAIN-OLD and CHAIN-R1-OLD are unchanged (killed at B's first save's e4 + 40).
- **Selftest.**
  - New planted fault `n_rule_first_save`: the grader tries only B's first save, as before ruling 11.
  - Recorded cases: the four rows where the rule moved to a later save count, pass, and show C continuing that save's line.
  - Planted inputs, each of which must fail:
    - a START between S_k's e4 and the new map (not counted);
    - the watcher's anchor forced to save 1 (not counted);
    - S_k's truth one tile off (C1 fails);
    - a later B line chained to S1 (C3 fails);
    - a later B line that remembers B's first line as its last save (C3 fails).
  - A check that `CHAIN_BUDGET_BASE` equals CONTINUE_BUDGET + ARRIVAL_BUDGET.
  - The old `chain_refused` case is retired, because the rule no longer refuses.
- **Constants (2x the widest measured):**

| constant | value | from |
|---|---|---|
| `CHAIN_B_FRAMES` | 2020 + 2 × 63,812 = 129,644 | this re-run |
| `CHAIN_B_TIMEOUT` | max(300, 2 × 105.4) = 300 s | this re-run |
| `CHAIN_OLD_FRAMES` | 2020 + 2 × 45,363 = 92,746 | stage 2's OLD measurements |
| `CHAIN_OLD_TIMEOUT` (new) | 300 s | stage 2's OLD measurements |

  These are now in `registered_numbers`, along with the docstrings of the rule and of its replay.

**Checks before going live**

- `replay_rule_n` over stage 2's recorded CHAIN rows: `REPLAY ON STAGE 2's ROWS: 12 of 12 as expected -> PASS`. It names save k = 2, 1, 3, 1, 2, 2, which matches stage 2's own analysis.
- The live watcher's method, driven frame by frame over the same records: `WATCHER RULE SIMULATION: 6 of 6 the same as the replay -> PASS`.

**Live run (development #57).** No `run_regression.py` was running (process census at 8:45 PM and 8:51 PM). CHAIN ran from a snapshot of the worktree whose AI files are identical to stage 2's.
- `PLAN DONE: 6 jobs, exit codes not 0: none (08:48:18 PM, 114 s)`.
- `CHAIN counted on 6 seeds: [5501, 5502, 5503, 5504, 5505, 5506]`, all checks C1-C6 true.

| seed | save C continues (k) | its line id | new map at frame | arrival → kill (frames) | B / C wall (s) |
|---|---|---|---|---|---|
| 5501 | 2 | 4 | 0:18 at 63,701 | 63,088 | 104.3 / 5.0 |
| 5502 | 1 | 3 | 2:4 at 46,841 | 46,272 | 77.8 / 4.9 |
| 5503 | 3 | 5 | 0:18 at 45,123 | 44,552 | 77.7 / 6.1 |
| 5504 | 1 | 3 | 2:4 at 34,540 | 33,964 | 64.6 / 5.4 |
| 5505 | 2 | 4 | 0:18 at 64,412 | 63,812 | 105.4 / 5.9 |
| 5506 | 2 | 4 | 0:18 at 36,583 | 36,001 | 61.9 / 6.4 |

- Each earlier anchor was blocked by the START of B's next save at the Oldale Pokemon Center.
- The watcher agreed with the grader's replay on all six. No START came after S_k's e4 on any seed.
- The two maps B's RAM showed before its arrival (`0:0`, `1:4`) were excluded on every seed, and no frozen save line was attached.
- C4 (reported only): every first save was at a ruling-51 moment (the Oldale Pokemon Center). The restored `last_save` was **not exercised** on any seed.
- The same trajectory replays per seed, so this is one trajectory replayed, not a replication.

**Development verdict** (stage 2's rows plus these CHAIN rows, combined in a separate folder): `LIVE R1 VERDICT: INCONCLUSIVE ... (failing: none; below the floor: ['K-FIRST', 'K-BETWEEN', 'K-INSIDE-OLD', 'K-SILENT-OLD', 'LAUNCH-OLD']; discriminators that differ: 42 of 54)`.
- The only reason for INCONCLUSIVE is that the rehearsal arms ran on 2 seeds by design.
- CHAIN, CHAIN-OLD, CHAIN-R1-OLD, R2-RETRY and R2-RETRY-OLD each count on 6 of 6.
- All 12 CHAIN discriminator pairs differ (parent [1, 2]; rebuilt `last_save.id` [3, 1]), with identical presses digests up to B's first save's e3. The 12 pairs that do not differ are rehearsal pairs on seeds where those arms did not run.

**Closing checks (last lines verbatim)**

- Selftest: `SELFTEST: the clean run PASSES (64 cases) and 13 of 13 planted faults FAIL as they must -> PASS`. Under the new fault, exactly the four moved-anchor rows fail; the k=1 rows 5502 and 5504 still pass, which is the control.
- revert_r1 CH1, LV1, LV2: `3 mutants CAUGHT as predicted, 0 REDUNDANT ALONE as predicted, of 3 run (503 defined)` / `OVERALL: PASS`.
- test_saving: `Ran 137 tests in 7.680s` / `OK`.
- Quick lane: `REGRESSION: PASS (quick, 21 suites, 20.5 s wall)`.
- Mutant anchors: `936 anchors checked, 0 not exactly once`.
- Ledger: `FINISHED #57` / `LEDGER ledger.json: 57 entries; well formed -> PASS`.
- Main checkout's sandbox-pokebot: `paths newer than the marker: 0` (marker 8:45:50 PM, checked 8:53:03 PM).

**Deviations, and why**

- **Kill spec string:** it stays `N1+30` with the new meaning. Stage 2's two killed CHAIN rows have no anchor field, so the new grader no longer counts them; this stage's rows replace them, and stage 2's files were only read.
- **C1:** `identify` in `probe_save_kill.py` knows only S1-S3, and that file is shared and hashed, so I did not edit it. Instead C1 puts each of B's saves in turn in the "S3" place, and requires that no other save of B's matches the cart.
- **S_k's line:** found by identity (its stamp), not by position or by the watcher's attached line. The spec says the checks never read the attached line, and CLAUDE.md rule 3 forbids position.
- **The grader's own replay:** the ruling does not ask for it. The selftest's fault is planted in that replay, because the selftest grades recorded rows and cannot run the live watcher; the watcher itself was checked offline and live (it agreed on 6 of 6).
- **Two new constants:** `CHAIN_OLD_TIMEOUT` (the spec says only "as CHAIN's B") and `CHAIN_BUDGET_BASE`.
- **`CHAIN_B_FRAMES` is above the development cap:** 129,644 against the 120,000-frame measuring cap. The cap was never reached (the widest kill was at child frame 64,442).
- **OLD arms not re-run:** their kill rule did not change, so their constants come from stage 2's measurements.
- **Anchor count:** 936 now against 926 at stage 1b. This stage added no mutant, and none fails the exactly-once check.

**What I did NOT do**

- Not run: the full revert_r1, revert_step5, revert_safety_gates, call_census, test_host and test_kb2. No AI or host code changed in this stage; only `live_r1.py` (test side) and `ledger.json`.
- Step 7 (registering and running held-out seeds 5551-5554) is not started.
- `run_regression_times.json` is not updated.
- A by-product to leave out of the commit: `ai_player/evidence/trees/fabdd82d7b27d9da.zip` (from the revert_r1 run).

All evidence is in `s53/r1f/build/s2b-live-dev/`: `chain-run.out`, `measure-chain.out`, `dev-verdict.out`, `selftest-final.out`, `replay-old-rows.out`, `sim-watcher-rule.out`, `revert-ch1-lv.out`, `test_saving.out`, `quick-lane.out`, `anchors.out`, `ledger-finish.out`, `ledger-check.out`, `find-newer.out`, `census-2.out`; plus `dev/` and `combined/`.

# Stage graded (builder; stop=False)

> Hand-back section, verbatim.

## Stage 3 (graded): held-out #58, seeds 5551-5554

**Verdict:** `LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 2 of 4: vacuous; passed 2 of 2; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 34 of 36)`

This rests on three caveats:
- **CHAIN counted on only 3 of 4 seeds.** The floor is 3, so it passes, with no seed to spare.
- **C4's restored `last_save` was not exercised on any seed.**
- **"vacuous" in the line overstates.** It means K-BETWEEN-MID fell below the floor. The midpoint arm counted on 5551 and 5554 and **passed** on both; it was vacuous only on 5552 and 5553.

### What was done (spec section 8 step 7)
No code was changed in this stage.
1. **Lane census:** 0 lanes running at 8:57 PM.
2. **Seed check** (`seed-check-3.out`, which ends `SEEDS 5551-5554 USED ANYWHERE: 0 -> UNUSED: YES`):
   - Neither ledger has an entry or a text hit for 5551-5554.
   - The evidence folders have 12 text hits each, all counts under JSON keys (orchestrator ruling 7).
   - The build scratch has only the `HELD_OUT` declaration and `flash_reads` counts.
   - The classifier was fault-tested on planted uses before I relied on it.
3. **Selftest before registration:** `... (64 cases) and 13 of 13 planted faults FAIL as they must -> PASS`.
4. **Register:** `live_r1.py ledger register --first 5551 --last 5554` at 9:00:57 PM. Numbers sha256 `01ec32e2...333a`, covering R2_STOP_ARRIVAL 57, CHAIN_B_FRAMES 129,644, CHAIN_B_TIMEOUT 300 s, CHAIN_OLD_FRAMES 92,746, CHAIN_OLD_TIMEOUT 300 s and N_KILL_FRAMES 30.
5. **Begin:** `ledger begin --purpose graded` at 9:01:29 PM, with the same sha and tree `fabdd82d7b27d9da`.
6. **The plan:** one plan, 64 jobs (16 per seed), run from the worktree. It ran 9:01:35 to 9:11:51 PM and ended `PLAN DONE: 64 jobs, exit codes not 0: none (09:11:51 PM, 617 s)`.
7. **The verdict:** as above.
8. **Ledger:** `FINISHED #58`, then `LEDGER ledger.json: 58 entries; well formed -> PASS`.
9. **Selftest after the run:** PASS.
10. **Read-only checks:**
    - The main sandbox-pokebot has `paths newer than the marker: 0`.
    - The tree digest is the same before and after.
    - The only worktree writes are `ledger.json` and the evidence file.
11. **Evidence:** `ai_player/evidence/2026-10-29-r1f-HELDOUT.txt` (21 verbatim sections).

### Per-arm table
| arm | 5551 | 5552 | 5553 | 5554 | counted |
|---|---|---|---|---|---|
| CONTROL, K-AFTER, K-INSIDE, K-SILENT, K-FIRST, K-BETWEEN (new), LAUNCH, R2-RETRY | ok | ok | ok | ok | 4/4 each |
| K-INSIDE-OLD, K-SILENT-OLD, LAUNCH-OLD, R2-RETRY-OLD | shows | shows | shows | shows | 4/4 each |
| CHAIN | ok | ok | ok | not counted | 3/4 |
| CHAIN-OLD, CHAIN-R1-OLD | shows | shows | shows | shows (twin not counted) | 3/4 each |
| K-BETWEEN-MID (diagnostic) | ok | not counted | not counted | ok | 2/4 |

### Discriminators
34 of 36 differ.

On every seed where both arms counted:

| pair | values (NEW / OLD) |
|---|---|
| CHAIN / CHAIN-OLD, B's save line's parent | `[1, 2]` |
| CHAIN / CHAIN-R1-OLD, rebuilt `last_save.id` | `[3, 1]` |
| R2-RETRY / R2-RETRY-OLD, `memory_check.ok` | `[true, false]` (KILLED vs CHOSEN) |
| K-INSIDE / K-INSIDE-OLD and K-SILENT / K-SILENT-OLD, `continued_from` | `[1, 2]` |
| K-AFTER / K-INSIDE, FILE | `[S2, S1+ERROR]` |
| LAUNCH / LAUNCH-OLD, first look | `[UNKNOWN 0, OVERWORLD 66883]` |
| K-FIRST / CONTROL, FILE | `[CORRUPT, S6/S6/S5/S5]` |
| K-BETWEEN | NEW never restored |

- **The 2 that do not differ:** the two CHAIN pairs on 5554, where CHAIN did not count. They are listed and not expected to differ (spec 5.3).
- **Determinism:** 24 of 24 lines equal the CONTROL's. CHAIN's B presses digest equals its OLD arms' on every counted seed. This is one trajectory replayed, never a replication.

### CHAIN
**Counted seeds:**
- On each of 5551-5553, B's rule N anchored on save 3. Anchors 1 and 2 were blocked by the START of B's next save at the Oldale Center.
- C continued id 5. B was killed on Route 103 (0:18), with arrival-to-kill of 59,238, 85,447 and 94,918 frames.
- NEW_B_pre was `[0:10, 2:2]` and NEW_B_post `[0:18]` on all three, and the watcher agreed with the replay.

**5554 was not counted.** The AI's own unchanged play reached the run's target before rule N could be met:
- B saved at the Center (save 1).
- It then only re-walked maps it had already stood on before that save (Route 103 and the Mart were visited before save 1).
- It saved after the rival on ROUTE103 (save 2), which blocked anchor 1.
- It saved after the Pokedex in the lab (save 3), which blocked anchor 2.
- It then ended `play: done: ch1_pokedex reached` at 71,331 frames, before it stood on any map new to save 3.
- So B was never killed and child C never ran.

Nothing was tuned.

**Budgets:** the held-out spans were wider than development's (94,918 vs 63,812 frames; 192.0 vs 105.4 s). No budget was reached, but the margins against the registered values are only 1.37x (frames) and 1.56x (wall). A later re-run could hit CHAIN_B_FRAMES or the 300 s timeout.

### Ruling-51 moments seen live
- **CONTROL child A, 22 saves:** after ch1_lab 4, center (OLDALE_TOWN_POKEMON_CENTER_1F) 10, after ch1_rival_route103 4, after ch1_pokedex 4.
- **CHAIN-family child B, 20 saves:**
  - center 18: every B's first save.
  - after ch1_rival_route103 1 and after ch1_pokedex 1: both CHAIN-5554.
- No gym moment.

### C4
- On 5551-5553, B's first post-continue save began on a held free overworld screen at the Center, 6, 10 and 9 game minutes after S1.
- **The restored `last_save` was not exercised on any seed.** There is no `[AI-SAVE] no save for` line in any CHAIN-family B log, nor anywhere under the run's `runs/` folder.

### Deviations
- **Job count:** run_plan.py's docstring said 68 jobs. That was my miscount: the plan has 16 jobs per seed, and 64 ran.
- **Seed check:** it took three versions, all kept. The spec's "0 hits" holds for the ledger. The evidence has 12 count hits and no seed uses (ruling 7).
- **Note file:** the registration note went through `--note-file`.
- **Verdict wording:** the "vacuous" word comes from `between_caveat`, which adds it whenever the midpoint counted below the floor. I did not change it, because the run is graded on the registered code. A fix belongs to a fix round on 5571-5574.

### Not done
- No AI, gate, test or doc file was changed. Nothing was committed.
- Not re-run, because no code changed in this stage: revert_r1, revert_step5, revert_safety_gates, call_census, the unit suites, the quick lane and test_kb2.
- The independent re-run on 5561-5564 and the adversarial review are the orchestrator's.

# Adversarial review

> Hand-back section, verbatim.

## Adversarial review: R1 + R2 follow-up (worktree wf_810d6b51-d6f-1, HEAD f4412116), 9:29 to 9:41 PM

**Verdict: FINDINGS.** Two MINOR and five NIT findings. No MAJOR. The core D2 latch code is correct, but one guard it relies on has no fault test.

### What I did
I read the spec (sections 0-11), the five stage hand-backs, and the whole diff:
- **AI and host code:** controller, session, launcher, `__main__`, game_memory, goals.
- **Gates:** check_purity, check_fairness, rate_step5.
- **Tests and live driver:** test_host, test_saving, test_goals, revert_r1 and its census JSON, live_r1 (rule N, the watcher, the CHAIN and R2 graders, the selftest, the verdict line).

I ran only offline, copy-based checks. Each output was saved under `s53/r1f/build/review/` with its command, start and end times and exit code. I never edited the worktree, never touched the main checkout except to read it, and ran nothing live. Ledger #59 (the orchestrator's re-run on 5561-5564) started at 9:30 PM with 48 live_r1 processes, so I kept my load light.

### Checks run (verbatim last lines)
- **Provenance:** `working-tree digest sha256:fabdd82d7b27d9da over git diff HEAD (17 files, 229710 bytes)`. This is the same tree as #58's begin and end. [provenance-now.out]
- **Ledger against HEAD:** `HEAD entries 56 now 59 changed among HEAD's: [] new: [57, 58, 59]`. [ledger_cmp.out]
- **Purity alias plants on a copy (10 plants):** `violations outside the plants: 0`.
  - Every alias was refused by an existing rule, except `finally: raise` (RV-7) and the control.
  - [purity_plants.out]
- **Process census at 9:37:45 PM:** `run_regression.py processes: 0`. [census.out]
- **Mutant ORDER** (the latch check moved below the other ends in `_on_frame`), on copies, with the main sandbox-pokebot as support root:
  - CONTROL copy: `Ran 8 tests in 14.185s` / `OK`.
  - MUTANT copy: `Ran 8 tests in 14.537s` / `OK`. The mutant survives.
  - `main sandbox-pokebot paths newer than the marker: 0 []`. [order_mutant.out]
- **The failure ORDER would let through:** [order_scenario.out]
  - `abandoned  real   exit_code=9 exit_reason=reset-refused` against `abandoned  ORDER  exit_code=3 exit_reason=abandoned`.
  - `parked     real   exit_code=9 exit_reason=reset-refused` against `parked     ORDER  exit_code=3 exit_reason=parked-manual`.
  - `main sandbox-pokebot paths newer than the marker: 0 []`.

### Findings
- **RV-1 (MINOR).** The spec's "the next `_on_frame` checks the latch before `abandoned`" is not pinned by any test.
  - If that order is lost, the brain catches a refused reset, then main.py discards the mode (or the framework switches the bot mode). The run then ends abandoned or parked-manual, both INVOLUNTARY, so the launcher allows a continue: the reload ruling 52 forbids.
  - Fix: add `abandoned` and `parked` harness cases with CONTROLs, and register mutant ORDER in revert_r1.
- **RV-2 (MINOR).** The verdict line says `counted 2 of 4: vacuous; passed 2 of 2` (live_r1.py:2412: `': vacuous' if len(counted) < FLOOR`).
  - That is the headline class V2-1 and V2-2 were opened to fix, and no test covers 0 < counted < FLOOR.
  - Fix: `vacuous` only when counted is 0, otherwise `below the floor`. This needs fix-round seeds, or a known-caveat entry in 06.
- **RV-3 (NIT).** CHAIN's budgets were measured with 6 jobs at once and graded with 12.
  - Held-out child B took 192.0 s of the 300 s timeout and 94,918 of 129,644 frames.
  - Hitting a budget can only make CHAIN uncounted (INCONCLUSIVE), never a false PASS.
- **RV-4 (NIT).** `run_regression_times.json` was not updated (spec section 7).
- **RV-5 (NIT).** The D3 (d) rule also refuses the builtin self-match `case int(n)`, with a message that wrongly says it reads the play time. There are no uses today.
- **RV-6 (NIT).** README:811 still says U1 and U2 are open, but USER RULING 53 on main settled them (and also confirms D2's fail-closed answer).
- **RV-7 (NIT).** `finally: raise` is not refused by rule D1. It has no ruling-52 effect after D2.

### Places where the code and the spec differ (all were accepted by the stages; the code is right in each case)
- The D2 checks live in `_steps`, not `run`.
- `classify_end` was retired in favour of `judge_end`.
- C230 was regenerated as C230b.
- CHAIN was built on K-SILENT's set (ruling 1).
- The rule-N re-anchoring and the C1/C3/C5 checks follow S_k (rulings 11 and 12).

I found no path to a reload, no unregistered graded seed, no fairness breach and no change to the bot.

### What I did NOT do
- No live arms.
- No full revert_r1, revert_step5 or revert_safety_gates, and no quick lane (I kept CPU light while #59 runs).
- No edits to the worktree and no git writes.
- No test_kb2.
- I did not re-grade the #58 rows myself.

# Independent re-run, seeds 5561-5564 (ledger #59)

> Hand-back section, verbatim.

## Independent re-run of the live proof (#59, seeds 5561-5564)

I wrote none of the follow-up's code and changed no AI, gate, test or doc file. The tree under test is digest `fabdd82d7b27d9da`, the same tree #58 graded, unchanged before the run and after it. Every output I rely on is saved in `s53/r1f/build/rerun/` with its command, start and end time and exit code. All of it is copied verbatim into `ai_player/evidence/2026-10-29-r1f-RERUN.txt`.

### What was run, in order
1. **Lane census at 9:26 PM:** no `run_regression.py` or other lane process was running (`hygiene-start.out`).
2. **Seed check:** no entry or text in either ledger names 5561-5564, and no file or folder in the build scratch is named for them. The script's own last line says `UNUSED: NO`, because its classifier flagged 27 hits it could not classify. I read each of them in context (`seed-hits-context.out`):
   - frame counts in child B press logs (e.g. `[5562, "Up", ...]`);
   - two RATE evidence files (ruling 7);
   - the spec's own reservation of this range.
   None of them is a use of these seeds.
3. **Registration before any run:** `live_r1.py ledger register --first 5561 --last 5564` at 9:30:14 PM made entry #59, numbers sha256 `0281f7319b97df95...`. `ledger begin` followed at 9:30:15 PM with the same sha. The registered numbers equal #58's in every field except `seeds` (`numbers-diff.out`: `1 field(s) differ: ['seeds']`).
4. **The plan:** stage 3's `run_plan.py` with only the seeds changed (`PLAN DONE: 64 jobs, exit codes not 0: none (09:41:13 PM, 641 s)`), started 9:30:32 PM, at most 12 jobs at once.
5. **The registered verdict:** `LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 0 of 4: vacuous; passed 0 of 0; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 36 of 36)`. Every graded arm counted 4 of 4. All 24 determinism lines equal the CONTROL's (one trajectory per seed, replayed).
6. **Closing the ledger:** `FINISHED #59`, then `LEDGER ledger.json: 59 entries; well formed -> PASS`.

### My own instrument
Three scripts: `mine.py`, `my_facts.py` and `my_checks.py`. They import nothing from ai_player and never read live_r1's grade, notes, summaries or verdict. They are adapted from the R1 verification's parser and reader, and the reader is now strict: a delete must find its key, a set must go through objects, and any unknown op fails. They work from the raw outputs:
- the frozen `.sav` bytes, read with my own parser, which checks sector checksums;
- the frozen `memory.jsonl` files, with each save line rebuilt through its parent chain;
- the per-frame records each child B wrote while it played (saves with their e3/e4 frames, map changes, START presses, kill);
- `actions.jsonl`, `world.jsonl`, `purity.json` and `launches.jsonl`;
- my own sha256 of each mutant file, plus a check that the file actually holds the mutant's edit.

How each new check is computed:
- **Rule N** is replayed event by event. An anchor is set when a save completes, a START blocks it, and a map entry not in the known set meets it.
- **S_k's line** is found by identity: the one B line whose stamp matches S_k's RAM play time.
- **The S1 and S2 line ids** are found by identity against child A's truths.

**Fault test, run before I relied on it** (`fault_mine.py` on #58's seed 5551): `MY INSTRUMENT FAULT TEST: PASS (control clean True; 37 of 37 planted faults caught; missed: none)`. The planted faults cover:
- the parser: one flipped byte, an erased cart, no complete slot;
- the reader: CH1-built and FX1-built live lines read as CHAIN's, a later line re-parented to S1, a delete of a missing key;
- rule N: a START between S_k's e4 and the new map, the watcher's anchor forced to save 1, NEW_B_pre emptied;
- C1 (S_k one tile off), C2, C5 (C continued B's first line; C refused), C6 (a NEW_B_pre map missing; a NEW_B_post map present);
- the OLD arms' shows and mutant identity;
- R2-RETRY: step 1's launcher line, R1's words, R2's tile, R3 via a copied run folder with purity NOT CLEAN;
- R2-RETRY-OLD;
- 10 plants on the existing arms;
- 2 discriminator plants.

### What I measured on 5561-5564
- **Overall:** `MY VERDICT (5561-5564): PASS (failing: none; below the floor: none; my discriminators that differ: 36 of 36; checks BAD on counted arms: 0)`. Against the registered grader: `ARM-BY-ARM: 64 of 64 (arm, seed) cells AGREE`.
- **CHAIN, per seed** (anchor k and S_k's line id; new map at frame; kill frame; arrival-to-kill; B / C wall time):

  | seed | k (line id) | new map at | kill | arrival-to-kill | B / C wall |
  |---|---|---|---|---|---|
  | 5561 | 2 (4) | 0:18 at 55,113 | 55,143 | 54,571 | 135.2 / 8.8 s |
  | 5562 | 1 (3) | 2:4 at 37,764 | 37,794 | 37,200 | 96.4 / 7.1 s |
  | 5563 | 2 (4) | 0:18 at 62,232 | 62,262 | 61,650 | 126.6 / 5.1 s |
  | 5564 | 1 (3) | 2:4 at 50,194 | 50,224 | 49,614 | 91.5 / 4.7 s |

  The watcher's kill equals my replay's on 4 of 4. Each blocked anchor was blocked by the START of B's next save at the Oldale Pokemon Center.
- **C1-C6 all true on 4 of 4:**
  - **C1:** my parser reads B's frozen cart as holding S_k by its truth and no other B save.
  - **C3:** B's first post-continue line (id 3) has parent 1 = S1's id, not S2's id 2. Every line rebuilds, and every rebuilt `last_save` is the line itself.
  - **C5:** C was allowed (KILLED), continued S_k's line and arrived at S_k's truth.
  - **C6:** C's restore snapshot equals its session's restored maps and holds S1's set and NEW_B_pre. It holds none of NEW_B_post. ABANDONED was empty on all 4 seeds, so that half was vacuous on this run.
- **OLD arms:**
  - CHAIN-OLD: parent 2; the CH1 copy ran (`c28514c53d5cd0bb`, real file `5afdd8179e1e6d15`).
  - CHAIN-R1-OLD: rebuilt `last_save.id` is 1, not 3; the FX1 copy ran.
  - R2-RETRY-OLD: refused, class CHOSEN; memory file byte-identical by my own sha256.
- **R2-RETRY:** the reach conditions, R1, R2 and R3 all hold on 4 of 4.
- **Discriminators:** all 9 differ on each seed:
  - CHAIN / CHAIN-OLD parent: [1, 2]
  - CHAIN / CHAIN-R1-OLD `last_save.id`: [3, 1]
  - R2-RETRY / R2-RETRY-OLD `memory_check.ok`: [true, false]
- **Determinism:** CHAIN's B presses up to its first save's e3 are identical, press by press, to both OLD B arms' on 4 of 4 (892, 794, 367 and 1,144 presses). This is one trajectory replayed, not a replication.
- **Save moments seen:** CONTROL's child A saved 21 times: Pokemon Center 9, `ch1_lab` 4, `ch1_rival_route103` 4, `ch1_pokedex` 4. All 14 CHAIN-family child B saves were at the Pokemon Center.
- **C4:** the restored `last_save` was **not exercised** on any seed. No file under `runs/` holds an `[AI-SAVE] no save for` line.
- **Budgets:** CHAIN B used at most 61,650 of 129,644 frames and 135.2 of 300 s. The OLD B arms used at most 36,298 of 92,746 frames and 94.2 of 300 s.

### Do I agree with stage 3 on 5551-5554? Yes, on every arm
`MY VERDICT (5551-5554): PASS ... my discriminators that differ: 34 of 36`.
- **CHAIN:** counted 3 of 4. On 5554, my replay shows the START at 54,693 blocking anchor 1 and the START at 70,027 blocking anchor 2. B then ended with `play: done: ch1_pokedex reached` at 71,331 frames without rule N ever being met.
- **Per-row cells:** 62 of 64 agree. The other 2 are CHAIN-OLD-5554 and CHAIN-R1-OLD-5554, and they are a presentation difference, not a disagreement:
  - the registered per-row summary marks them counted, and `verdict_of` then drops them by the twin rule;
  - my instrument applies the twin rule while counting.
  Both give 3 of 4, and both find that the two arms showed their difference on 5554 as well.
- **Everything else matches stage 3's hand-back:** the per-seed CHAIN numbers, the C4 gaps (6, 10 and 9 game minutes) and C4 "not exercised".

### Deviations and where the spec differs from the code
- **CHAIN's base arm:** the spec's table builds CHAIN from K-INSIDE. Ruling 1 and the code use K-SILENT, and I graded K-SILENT's counting.
- **Minute-only stamps:** save lines carry `play_time` as [hours, minutes] only. So C3's "stamp = RAM truth" and C5's lookup of S_k's line by its stamp are minute-level checks. Each S_k matched exactly one line here. Two saves in the same game minute would make the lookup ambiguous; that did not happen on these seeds.
- **Ledger typo:** the verdict text stored in ledger #59 says the plan began at 9:30:52 PM. It began at 9:30:32 PM. I recorded the erratum in the evidence file and did not rewrite the ledger.

### What I did NOT do
- No code changes and no git writes.
- No unit suites, revert runs, census, quick lane or selftest: no code changed, so they were out of scope for this re-run. test_host and test_kb2 are not run here.
- I did not recompute the 24 determinism lines for the existing arms. Those are the registered grader's.
- No adversarial review.
- Only processes I started were involved, and none were left running.

# Fix round, seeds 5571-5574 (ledger #60)

> Hand-back section, verbatim.

## Fix round: the adversarial review's RV-1 and RV-2 (seeds 5571-5574, ledger #60)

**Result:** both findings were real and both are fixed. Every live arm was re-run on the new seeds (registered first), and the verdict is **PASS**. All the requested suites, reverts and the quick lane pass. No AI or host code changed: the fixes are on the test side only.

### Reproduced first (folder `s53/r1f/build/fix/`)
- **RV-1 reproduced:**
  - `repro-rv1-mutant.out`: the review's copy-based mutant ORDER passes all 8 ResetRefusalTests ('Ran 8 tests ... OK' on both copies). No test checked that the latch is looked at first.
  - `repro-rv1-scenario.out`: on the real code, abandoned and parked both end `exit_code=9 exit_reason=reset-refused`. Under ORDER they end `exit_code=3 exit_reason=abandoned` and `exit_code=3 exit_reason=parked-manual`. Both are INVOLUNTARY, so the launcher would allow a continue past the blocked reset.
- **RV-2 reproduced** (`repro-rv2.out`): `counted 2 of 4, both pass ... K-BETWEEN-MID counted 2 of 4: vacuous; passed 2 of 2`. #58's recorded rows give the same wording in the headline.

### What I changed (worktree only, uncommitted)
- **`ai_player/gates/test_host.py`** (RV-1):
  - New latched cases in the harness:
    - `abandoned`: set the latch, run `session.run()` one step, `close()` it (GeneratorExit, so the lifecycle notes abandoned), then call `_on_frame()`.
    - `parked`: set the latch, switch `context.bot_mode`, then call `_on_frame()`.
  - Both assert reset-refused/9; `abandoned` also asserts that `abandoned` was noted.
  - CONTROLs: `control_abandoned` (abandoned/3) and `control_parked` (parked-manual/3).
  - That is 3 new tests: ResetRefusalTests goes from 8 to 11 and test_host from 31 to 34.
- **`ai_player/gates/live_r1.py`** (RV-2):
  - `between_caveat` now builds `shortfall = ": vacuous" if not counted else (": below the floor" if len(counted) < FLOOR else "")`.
  - New selftest case: counted 2 of 4, both passing, reads 'below the floor'.
- **`ai_player/gates/test_saving.py`**: new test `LiveR1HeadlineTests.test_a_midpoint_counted_below_the_floor_is_not_called_vacuous`, with CONTROLs for counted 0 ('vacuous'), 3 and 4 (no word). test_saving goes from 137 to 138 tests.
- **`ai_player/gates/revert_r1.py`**:
  - Mutant **ORDER**: the latch check moves below the wall-clock end. It predicts the two new latched tests.
  - Mutant **LV3**: the old 'vacuous' rule. It predicts the new headline test.
  - Both CAUGHT: `revert-subset.out`, '7 mutants CAUGHT as predicted ... OVERALL: PASS'.
- **`ai_player/README.md`**:
  - The ruling-52 bullet now says the frame checks the latch FIRST.
  - The follow-up paragraph names the RV-2 wording.
  - The counts are now 138 tests and 505 mutants.
- **`ai_player/gates/ledger.json`**: entry #60, registered, begun and finished.
- **New file `ai_player/evidence/2026-10-29-r1f-FIXROUND.txt`**: 883,919 bytes, sha256 c39f5691...; 32 sections, each a saved output copied verbatim.

### The live round
- **Before registering:** process census showed 0 lane processes.
- **Seed check** (`seed-check.out`): no ledger entry names 5571-5574 (worktree 59 entries, main 56). I read every text hit in context:
  - frame counts in RATE and press logs (ruling 7);
  - the spec's own reservation of 5571-5574, and the re-run's copy of that reservation.
  - No file or folder is named for these seeds.
- **Registered and begun** (`ledger-register.out`, `ledger-begin.out`): 'SEED LEDGER: GRADED, HELD-OUT seeds 5571-5574 (ledger entry #60), REGISTERED 2026-10-29 21:57:08 ... (the same)'.
- **Plan:** 'PLAN DONE: 64 jobs, exit codes not 0: none (10:09:06 PM, 711 s)'.
- **Verdict:** 'LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 0 of 4: vacuous; passed 0 of 0; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 34 of 36)'.
- **Finish:** 'FINISHED #60'. Ledger check: 'LEDGER ledger.json: 60 entries; well formed -> PASS'.
- **Arms:**
  - 14 arms counted on 4 of 4: every graded arm except CHAIN and its two OLD twins.
  - CHAIN counted on 3 of 4 (5571, 5573, 5574), with C1-C6 all true; CHAIN-OLD and CHAIN-R1-OLD counted on 3 of 4 and showed their difference on all 4.
  - K-BETWEEN-MID counted 0 of 4.
  - 24 of 24 determinism lines equal the CONTROL's. That is one trajectory per seed, replayed, not a replication.
- **CHAIN-5572 did not count** (`inspect-chain-5572.out`), the same pattern as #58's 5554:
  - Child B saved 5 times. Anchors 1-4 were each blocked by the START of its next save.
  - Its play then ended 'play: done: ch1_pokedex reached' at 89,368 frames, before it stood on any map new to save 5.
  - So rule N was never met, and there was no kill and no child C. Nothing was tuned.
- **Measured** (`analyze-fixround.out`):

  | CHAIN seed | anchor | arrival to kill | B wall | C wall |
  |---|---|---|---|---|
  | 5571 | k=2 | 78,582 frames | 181.6 s | 8.5 s |
  | 5573 | k=2 | 72,097 frames | 148.9 s | 5.8 s |
  | 5574 | k=4 | 120,137 frames | 212.0 s | 5.7 s |

  - On 5574 that is 1.08x short of CHAIN_B_FRAMES 129,644, and 1.42x short of the 300 s timeout.
  - OLD B arms: at most 44,521 frames and 108.9 s.
  - Ruling-51 moments: CONTROL child A saves were lab 4, center 9, rival 4, pokedex 4. CHAIN-family child B saves were center 19, rival 1, pokedex 1.
  - C4's restored last_save was not exercised on any seed.
- **Main checkout's sandbox-pokebot:** 'paths newer than the marker: 0' (live marker and closing-check marker). Lane census was 0 after the run.

### Closing checks (after the fixes; last lines verbatim)
- **Unit suites:** test_check_purity 'Ran 30 tests ... OK'; test_safety_gates 'Ran 50 tests ... OK'; test_host 'Ran 34 tests ... OK' (in the worktree, ruling 9); test_battle 'Ran 107 ... OK'; test_saving 'Ran 138 ... OK'; test_goals 'Ran 256 ... OK'.
- **Gate CLIs:** check_purity 'VERDICT: PASS'; check_fairness 'PERSON-FAIR DATA DOOR: PASS (0 breaches)'.
- **call_census:** 'CALL-SITE CENSUS: PASS' (0 MISSING). It ran before registration, and no AI code changed after that.
- **revert_r1 (full):** '504 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as predicted, of 505 run (505 defined)' / 'OVERALL: PASS'. R0 CONTROL ran 418 tests.
- **revert_step5:** '400 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 402' / 'OVERALL: PASS'.
- **revert_safety_gates:** '23 mutants CAUGHT as predicted, of 23' / 'OVERALL: PASS'.
- **Quick lane:** 'REGRESSION: PASS (quick, 21 suites, 21.0 s wall)'. The same lane also passed before registration.
- **live_r1 selftest --all**, before and after the run: 'SELFTEST: the clean run PASSES (65 cases) and 13 of 13 planted faults FAIL as they must -> PASS'.
- **NOT RUN:** test_kb2 (ruling 6).

### Deviations and why
- **Mutant LV3 was added**, although RV-2's fix text asked only for a unit case. The new wording is a guard, and every guard gets a fault test.
- **I ran the fast offline checks before registering** (test_saving, test_host, the quick lane, call_census, the selftest), so a late error could not burn seeds 5571-5574. The slow reverts ran after the live round, so they could not slow the budgeted live children.
- **New evidence tags:** revert evidence went to new files, `2026-10-29-r1f-fix-REVERT.txt` and `2026-10-29-r1f-fix-step5-REVERT.txt`. Stage 1b's r1f files are kept, not overwritten.
- **My closing-check runner crashed once**, printing a U+FFFD line under cp1252, after phase 1. All of phase 1's child runs had already finished with their outputs saved. Phases 2-4 were then run with `--from-reverts` (`close-run-1.out` is the first run's console).
- **Tree digest:** the README edit came after the subset revert, but `provenance.py` excludes `*.md`. So the digest d765751fcb18aad8 is the same for the subset revert's tree, at registration, at begin and after the run.

### What I did NOT do
- No git writes.
- Nothing written in the main checkout or in the tuner's clone.
- `run_regression_times.json` was not updated.
- README's KNOWN LIMITS paragraph is still stale ('no live arm yet saves after a continue'). That is docs part (k), the orchestrator's.
- Untracked by-products to keep out of the commit: `evidence/trees/d765751fcb18aad8.zip` and the two r1f-fix revert evidence files.
- This round is not an independent verification: that uses 5581-5584.

# Verification of the fix round: independent re-run, seeds 5581-5584 (ledger #61)

> Hand-back section, verbatim.

## Independent verification of the fix round (#61, seeds 5581-5584)

I wrote none of the code and none of the fixes. All outputs are in `s53/r1f/build/verify-rerun/`, and the one evidence file is `ai_player/evidence/2026-10-29-r1f-VERIFY.txt` (sha256 0d2ae25c..., 35 sections).

**Verdict: AGREES.** The fixed code passes on new held-out seeds, both by the registered grader and by my own instrument. I also agree with the fix round's verdict on 5571-5574, arm by arm.

### Before any seed ran
- **No lanes running:** the process census found 0 lane processes (`hygiene-start.out`).
- **Seeds unused:** `seed-check.out` (its matchers fault-tested on plants) ends `SEEDS 5581-5584 USES: 2 -> UNUSED: NO`. Both uses are the same text: #60's note reserving these seeds for this verification (`ledger-hits.out`). No ledger range meets them, no file or folder is named for them, and no evidence file uses them as seeds. So the seeds are unused.
- **Tree:** the digest was d765751fcb18aad8, the fix round's tree. The registered numbers equal #60's except the seeds.
- **Registered first:** `ledger register` gave ENTRY #61 at 10:46:52 PM, and `ledger begin` at 10:46:53 PM said `no other entry of family 'story' names any of these seeds`.

### The run
- The same 64-job plan as #58, #59 and #60, with only the seeds changed. It ran from 10:47:34 PM to 10:57:57 PM: `PLAN DONE: 64 jobs, exit codes not 0: none`.
- **Registered verdict:** `LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 1 of 4: below the floor; passed 1 of 1; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 34 of 36)`
- **Ledger:** `FINISHED #61`, then `LEDGER ledger.json: 61 entries; well formed -> PASS`.

### My own instrument
I adapted the #59 re-runner's tools after reading them: a flash parser with sector checksums, a strict rebuilder for `memory.jsonl` chains, and a replay of rule N. My additions:
- a budget fact for each CHAIN-family arm, graded as a CHAIN reach condition;
- plants made generic so they work on any seed;
- new plants V1-V10.

**Fault-tested before use**, on #60's seed 5571: `MY INSTRUMENT FAULT TEST: PASS (control clean True; 47 of 47 planted faults caught; missed: none)`.

**Results on 5581-5584:**
- My grade: `MY VERDICT (5581-5584): PASS (failing: none; below the floor: none; my discriminators that differ: 34 of 36; checks BAD on counted arms: 0)`.
- Against the registered grader: 62 of 64 (arm, seed) cells agree.
  - The other 2 are CHAIN-OLD-5584 and CHAIN-R1-OLD-5584.
  - In the grader, the per-row `counted` flag is the arm's own reach, while `verdict_of` applies the twin rule. Both graders leave them out of the floor, so the verdict does not differ.
  - The same thing showed on #58's 5554 and #60's 5572.
- Discriminators are equal seed by seed (9, 9, 9 and 7 differ). The 2 that do not differ are the CHAIN pairs on 5584, where CHAIN did not count.

**Re-grade of #60's own outputs:** MY VERDICT PASS, 62 of 64 cells agree (the 2 others are the same twin presentation, on 5572), and 34 of 36 discriminators differ for both graders.

**My fault test of the two fixes** (`my_mutants.py`): it copies the worktree's `ai_player`, reads the ORDER and LV3 edits from `revert_r1.MUTANTS`, and applies each exactly once.
- CONTROL: ResetRefusalTests 11/11 ok, LiveR1HeadlineTests 3/3 ok.
- ORDER fails exactly the two RV-1 tests (`..._mode_is_discarded_...` and `..._mode_switched_...`).
- LV3 fails exactly `test_a_midpoint_counted_below_the_floor_is_not_called_vacuous`.
- Last line: `MY MUTANT CHECK OF RV-1 AND RV-2: PASS`.

### What I measured
- **Floors:** 14 arms counted 4/4. CHAIN, CHAIN-OLD and CHAIN-R1-OLD counted 3/4 (5581-5583, C1-C6 all true).
- **Why CHAIN-5584 did not count:**
  - B saved 5 times: at the OLDALE Pokemon Center three times, on ROUTE103, and in the lab.
  - Anchors 1-4 were each blocked by the START press of the next save.
  - B's own play then ended `play: done: ch1_pokedex reached` before it stood on a map new to save 5.
  - So rule N was never met; my replay and the watcher agree. This is the same shape as #60's 5572 and #58's 5554, and nothing was tuned.
- **Exercised for the first time:**
  - Rule N re-anchored on 5582: S_k was B's save 2 (line 4), C continued line 4, and the chain 4 -> 3 -> 1 checked out.
  - ABANDONED was non-empty (map 0:18) on 5581 and 5582, and C's restore held none of it.
  - The RV-2 wording "below the floor" appeared live, because the midpoint counted 1 of 4. The fix round had left this open.
- **Budgets:** CHAIN's narrowest margins were 2.25x on frames (129,644 / 57,553) and 2.11x on wall time (300 / 142.0 s), both on 5582. The OLD arms' narrowest were 2.38x and 2.96x. No run hit a budget. #60's 1.07-1.08x on 5574 (confirmed by my re-grade) did not recur.
- **C4:** B's first save on every counted CHAIN seed began on a held free overworld screen at the OLDALE Pokemon Center, 9, 8 and 11 game minutes after S1. The restored last_save was NOT exercised: no `[AI-SAVE] no save for` line anywhere.
- **Determinism:** CHAIN's B presses up to its first save's e3 equal the OLD arms' on every counted seed (717, 908 and 1055 presses). This is one trajectory replayed, not a replication.
- **Selftest after the run:** `SELFTEST: the clean run PASSES (65 cases) and 13 of 13 planted faults FAIL as they must -> PASS`. It runs on its own fixed case set, which does not include the new rows.
- **Read-only checks:** main's `sandbox-pokebot` had 0 paths newer than the marker. Lane census after: 0 lane processes and 0 of my processes alive. The tree digest after the run was still d765751fcb18aad8.

### Deviations from the spec
- Spec 5.1/5.2 says CHAIN, CHAIN-OLD and CHAIN-R1-OLD are built on K-INSIDE. The code builds them on K-SILENT, per ruling 1, so the code wins and that spec text is stale.

### What I did NOT do
- test_kb2 was not run (ruling 6).
- I did not re-run the full unit suites, revert_r1 (505 mutants), revert_step5, revert_safety_gates or the quick lane. Those figures are the fix round's own; I re-ran only ORDER and LV3, with my own runner.
- No AI, host or gate code was changed, and there was no git write. The only worktree writes are `ledger.json` (through the ledger commands) and the one evidence file.

# Verification of the fix round: adversarial review

> Hand-back section, verbatim.

### Adversarial review of the R1 + R2 follow-up fix round (stage verify-review, 10:44 PM to 10:48 PM, 2026-10-29)

**Scope:** the fix round's changes after the first review, which are RV-1 (test_host reset_refusal abandoned/parked cases, mutant ORDER) and RV-2 (live_r1 between_caveat wording, mutant LV3). The worktree was used read only. The only new files are copy-based mutants and outputs under `build/verify-review/`. No live arms were run. A process census at the start found no run_regression/live_r1/unittest process. Ledger #61 (5581-5584) was started by another stage while I worked, at 10:46:53 PM. I did not touch it.

**Verdict: FINDINGS (1 MINOR).**

**VR-1 (MINOR): RV-1's fix does not pin the latch ahead of `interrupted`.**
- `interrupted` is in launcher `_INVOLUNTARY` (launcher.py:263), so the launcher allows a continue after it.
- I built mutant ORDER-INT on a copy: `_end_if_refused()` moved to just after the `interrupted` finish (session.py:307-309), still above `abandoned`.
- It survives all 11 ResetRefusalTests.
- The concrete scenario (a refusal latched, then Ctrl+C reaching `_on_signal` before the next frame) ends:
  - `interrupted`/130 under the mutant;
  - `reset-refused`/9 on the real code.
- So the test suite still does not enforce spec 3(c)'s "first statement after frames_seen += 1".
- Fix: add a latched `interrupted` case and its CONTROL (interrupted/130), and register ORDER-INT. Ideally also add one case where all three other ends are due at once. This is test-only, so live_r1's hash and the graded seeds are unaffected.

**Checks run (verbatim last lines):**
- `py -3.12 -B order_int.py` (copy-based ORDER-INT plus scenario), `build/verify-review/order-int.out`, exit 0. Last line: `main sandbox-pokebot paths newer than the marker: 0 []`. The key lines:
  - `SCENARIO interrupt-after-refusal real exit_code=9 exit_reason=reset-refused`
  - `SCENARIO interrupt-after-refusal ORDER-INT exit_code=130 exit_reason=interrupted`
  - real copy: `Ran 11 tests in 13.428s / OK`
  - ORDER-INT copy: `Ran 11 tests in 13.164s / OK`
- `py -3.12 -B -m unittest -v ai_player.gates.test_saving.LiveR1HeadlineTests` (worktree), `build/verify-review/headline-tests.out`, exit 0. Last line: `OK` (Ran 3 tests).

**Confirmed sound:**
- RV-1's two new cases and their CONTROLs are real, and ORDER is caught by exactly its predicted tests.
- RV-2's wording rule, its test (counted 0/2/3/4) and LV3 are correct.
- The verdict line has a single source.
- The fix round changed only four gates files: the #58 and #60 tree snapshots differ in live_r1.py, revert_r1.py, test_host.py and test_saving.py only.
- #60 was registered before it ran, with a stable provenance digest.

**Noted but out of the fix round's scope (not graded as findings):**
- The latch lives only in memory. A launcher-level Ctrl+C (launcher.py:432) or a wall-clock hard kill landing in the one-frame window between a refused press and the next `_on_frame` is classed INVOLUNTARY or BUDGET with no record of the refusal. The original D2 design accepts that window.
- The CHAIN-5574 budget margin (1.08x on frames) and the stale README KNOWN LIMITS line were already reported as open in the hand-back.

**What I did NOT do:** run live arms, the full revert_r1, the selftest or the other suites (the hand-back reports them). I edited nothing in the worktree or the main checkout.

# Second fix (VR-1, test-only), workflow r1f-fix2

> Hand-back section, verbatim.

VR-1 (MINOR) is closed, and only test files changed this round (`host/session.py` is byte-identical). Comparing the tree snapshots, the code tree differs from the graded runs' tree (d765751fcb18aad8) in exactly three files: `gates/test_host.py`, `gates/revert_r1.py` and `gates/run_regression_times.json`. The final tree is 2b084b050f3297c0.

**Reproduced first.** On the unchanged ResetRefusalTests (11 tests), mutant ORDER-INT survived with no failing test, as the review said. Three other reorders I placed also survived:
- INT-FIRST: the interrupt check copied ahead of the latch.
- BUDGET-FIRST: the frame-budget check ahead of the latch. `frame-budget` is in the launcher's INVOLUNTARY list, so a continue would be allowed.
- WALL-FIRST: the wall-clock check ahead of the latch. `wall-clock` is a BUDGET end, so a continue would be allowed after a save.

ORDER-AB, ORDER-PARK, ORDER-BUDGET, AB-FIRST and PARK-FIRST were already caught. Output: `fix2/repro-before.out`.

**New tests** (four new harness cases in `harness_reset_refusal`, three new tests):
- `interrupted`: the latch, then `session._on_signal(2, None)`, then `_on_frame()`. Result: reset-refused/9. Its CONTROL, `control_interrupted`, ends interrupted/130.
- `all_due`: on the SAME frame as the latch, all five other ends are due at once: interrupted, abandoned, parked-manual, frame-budget (`AI_PLAYER_FRAMES=1` plus 601 pre-frames) and wall-clock (a deadline 3 s ahead, waited out within a bound). The harness reads each due flag from the session just before the frame. Result: reset-refused/9, all five due, 601/601 pre-frames.
- Its CONTROL, `control_all_due` (no latch): all five due, and the run ended interrupted/130. The test only requires that it ends in one of the five ends with that end's own exit code, so it does not fix which end is checked first.

**Registered in `revert_r1.py`.** Nine new mutants: ORDER-INT, ORDER-AB, ORDER-PARK, ORDER-BUDGET, INT-FIRST, AB-FIRST, PARK-FIRST, BUDGET-FIRST and WALL-FIRST. The existing ORDER now also predicts the interrupt test and the all-due test. The all-due test is the only one that catches BUDGET-FIRST and WALL-FIRST. Because every one of the five "X-FIRST" mutants is caught, each end is shown to be really due in that case, not only asserted. `fix2/same.out` proves the registered edits are byte-identical to the ones reproduced before the fix.

After the fix, a subset run (R0, ORDER, the nine new mutants, and L11/L15/L16/L18) gave "14 mutants CAUGHT as predicted, OVERALL: PASS". Each reorder failed exactly its predicted tests, and no CONTROL test failed under any mutant.

**RV-4.** The `revert_r1` entry in `run_regression_times.json` went from 917 to 1167. That is my own full `revert_r1` run alone, 1166.9 s with 514 mutants; the full lane's earlier run on f4412116 took 1153.7 s. The `_doc` text says where the number came from.

**Final runs on the final tree** (last lines verbatim; outputs under `scratchpad/s53/r1f/build/fix2/`):

| Run | Last line | Result |
|---|---|---|
| test_host (whole) | `OK` | Ran 37 tests |
| revert_r1 (full) | `evidence: ai_player\evidence\2026-10-29-r1f-fix2-REVERT.txt` | 513 mutants CAUGHT, 1 REDUNDANT ALONE (C306, as predicted), of 514; FROZEN TREE: PASS; OVERALL: PASS; 1169.3 s |
| Quick lane | `evidence: none written (--evidence writes it; --full always does)` | REGRESSION: PASS (quick, 21 suites, 20.9 s wall) |
| call_census | `CALL-SITE CENSUS: PASS` | PASS |

Nothing was written under the main checkout's `sandbox-pokebot`: the find-newer check reported 0 paths newer than the marker. There were no git writes, and nothing is committed.

**Worth knowing:**
- My first whole test_host run showed 13 false failures. I had launched it with `PYTHONPATH` set to the worktree, which made the mutant-copy tests load the worktree instead of their copy. The valid run calls `test_host.py` by its absolute path with the working directory in scratch: 37 OK. The bad run is kept as `test-host-PYTHONPATH-misrun.out`.
- The two all-due cases take about 3.2 s each because they wait for a real deadline. On a very loaded machine they would fail loudly, never pass by mistake; that did not happen in either full run with 6 workers.

# Second fix: the independent check

> Hand-back section, verbatim.

VR-1 fix round 2, independent check: PASS. Outputs are in C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/r1f/build/fix2-check/.

(1) CONTROL: on an unmutated copy of the worktree's ai_player, ResetRefusalTests passes 14/14 and the whole test_host.py runs 37 tests, OK.

(2) Reorders: I built 32 mutants of Session._on_frame, each in its own copy. They cover the latch moved below every end (AFTER-INT, which is ORDER-INT, then AB, MODE_READ, PARK, BUDGET, WALL and HEARTBEAT, so last), the latch made dead inside each end's if after its finish (6 mutants), each end's check moved ahead of the latch (5), 12 seeded random permutations, and the full reverse. Every one FAILS test_every_other_end_due_on_the_same_frame_still_ends_reset_refused. Every one whose order puts the interrupt ahead of the latch also FAILS test_a_refused_press_then_an_interrupt_ends_reset_refused. No control test fails under any mutant. Each failure reports another end where 9/reset-refused was expected, and across the set all five ends (interrupted/130, abandoned/3, parked-manual/3, frame-budget/4, wall-clock/124) were seen to fire. BUDGET-FIRST and WALL-FIRST are caught by the all-due test alone, as the fixer said. My first PARK-FIRST mutant was faulty (it read current_mode before assigning it); after I fixed the generator and re-ran it, it was caught with the controls passing.

(3) The finding's scenario, in my own script: the brain catches a refused A+START, then Ctrl+C reaches _on_signal, then the guard listener's frame arrives. The real code ends reset-refused/9. The no-refusal control ends interrupted/130, and the ORDER-INT fault arm ends interrupted/130.

Test-only: between the graded snapshot d765751fcb18aad8 and the fix snapshot 2b084b050f3297c0, only gates/test_host.py, gates/revert_r1.py and gates/run_regression_times.json changed. session.py sha256 57700aaa... is unchanged. No AI or host code, live_r1.py, check_purity.py or check_fairness.py was touched. find -newer found 0 new paths in sandbox-pokebot or the worktree, and I made no git writes.

Optional, not blocking: AFTER-WALL (ORDER-WALL) and latch-at-end are not registered in revert_r1, though both are caught today.
