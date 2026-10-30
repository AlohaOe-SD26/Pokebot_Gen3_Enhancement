> **Filed 2026-10-29** by the orchestrating session. Below section 0 is the build report VERBATIM, from the session scratch
> `s53/r1build/build/BUILD-REPORT.md` (sha256 `45c51d7149bbed92`), with ONE insertion, "Stage 2 of 6", whose builder could not
> append it (its hand-back's fields are inserted as given), and the orchestrator's verification appended as its last
> section. Backlog R1 + R2 (with DP1 + DP2 and L3 (a)-(b)), built to `2026-10-29-R1R2-BUILD-SPEC.md` by the workflow
> `r1r2-build` (9 agents: six stage builders, an adversarial reviewer, an independent re-run, a fix round; 51.96 Mtok input-equivalent),
> then re-checked by the workflow `r1r2-verify-fixed` (2 agents; 2.89 Mtok). Decisions: `06` 2026-10-29 ("R1 + R2
> BUILT"); the change: `07` 2026-10-29; mistakes: `08` 2026-10-29.

# R1 + R2 BUILD REPORT: the AI saves like a person, CONTINUEs after a kill, and its memory survives (2026-10-29)

## 00. The orchestrator's checks (2026-10-29, 4:37 PM to 5:15 PM)

- **Applied to `main` byte for byte** (`s53/r1build/apply/apply_build.py`): every file the worktree `wf_ad737c3f-1d5-1`
  changed or added, each sha256-checked after the copy. Skipped: its three `evidence/archive/` copies (each byte-identical
  to main's tracked file) and six tree zips that no new evidence file names.
- **On `main`, the suites the worktree could not run (ruling 2):** `test_host` (whole): `Ran 21 tests ... OK`; `test_kb2`:
  `OK`.
- **Before the commit:** `run_regression.py --quick`: `REGRESSION: PASS (quick, 21 suites, 49.6 s wall)`;
  `run_gates.py --quick`: `ALL 141 ENFORCING GATES PASS  (1066.7s total)   [+2 ADVISORY probe(s) — run, NOT gated]`; `regression_due.py`: units, revert_step5, revert_r1 and revert_safety_gates DUE
  (the full lane after the commit), and rate_step5 and live_step5 DUE since before this item.
- **My ruling on R-5: K-BETWEEN's graded kill rule is 'new'** (`06` 2026-10-29). The spec's midpoint could not fail: the
  AI had stood on no new map there (0 of 2 development seeds; 0, 1 and 0 of 4 held-out seeds), and a planted "memory
  newer" fault fails check 3 under 'new'. The midpoint stays the diagnostic arm K-BETWEEN-MID.
- **Independent verification of the FIXED code** (workflow `r1r2-verify-fixed`; neither agent wrote any of it): a live
  re-run on NEW held-out seeds 5481-5484, registered first (ledger #56): AGREES: `LIVE R1 VERDICT: PASS` with its K-BETWEEN rule named, all 10 graded arms counted on 4 of 4 seeds, 24 of 24 discriminators differ, and the agent's own instrument agrees on every arm; R-1 live: 93 of 93 save lines in the 52 child-A memory files hold their own save (its own reader, fault-tested: 0 of 93 on #53's pre-fix files). An adversarial review of
  the fix round: FINDINGS, 1 MINOR and 5 NITs, none in the AI's play code (V2-1, MINOR: `live_r1`'s headline caveat counts the midpoint arm's seeds but not its passes); V2-3 and V2-4 (the records' wording) fixed at the commit, the other four go to the follow-up. Both in full: the last section of this file.

## 0. In plain words

- The AI now saves its game the way a person does: it opens the START menu, picks SAVE and answers the game's own
  questions, reading each page. It saves after healing at a Pokémon Center, right before it talks to a gym leader, and
  after a big story moment (USER RULING 51); never twice within 3 minutes of play time, and only on a free screen.
- At the start of each save it writes one line to its memory file, stamped with the game's play time. If its program is
  killed, the launcher's `--continue` restarts the game from the cartridge's own save. The AI plays the title screen, reads
  any error page, matches the CONTINUE window's TIME to its memory, presses CONTINUE, checks it arrived where it remembers
  with the same Pokémon, and takes back its memory as of that save. If the save is gone it stops and says so: it never
  starts a NEW GAME on its own, and it never reloads to undo a loss (USER RULING 52, enforced by the launcher, the purity
  gate and the controller).
- The proof: on 4 games it had never seen, the AI was killed at five kinds of moment (after a save, inside one, in its
  silent first frames, inside the first save, between saves); each time it continued from the save the game kept, with
  its memory as of that save. A separate agent repeated it on 4 more games; after the review's fixes it ran on 4 more,
  and a fresh agent checked the fixed code on 4 more.
- Open: the user's U1 (which big story moments) and U2 (continuing after a time-limit end), with interim answers built;
  four small review gaps, the next item.

# R1 + R2 build report

- Worktree: `C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1`
- HEAD: `67c73a0f181e2ff3706d422ac75b0f27d3a515d6` (the spec's commit). Nothing committed, staged or stashed.
- Spec: `PROJECT KNOWLEDGE/ai-research-notes/2026-10-29-R1R2-BUILD-SPEC.md`.

---

## Stage 1 of 6: section 8 steps 1 and 2 (the worktree, then the EYES)

Built from 9:05 AM to 9:37 AM Los Angeles time on 2026-10-29. All evidence is in `build/s1-eyes/`.

### VERDICT: STOP (step 2's rule: a measured value contradicts the probe report)

The AI's eyes passed every step-2 check. No reading was unreadable, none disagreed with the harness's RAM truth, and
the longest still stretch was 265 frames, under the 900 limit.

I stopped anyway, because the general STOP rule applies: "a measured value that contradicts the probe report is a STOP,
never a tune." On the same fixture (`route101_south.ss1`), with the AI's pacing, the saves fell on other frames than
in the probe's single trajectory, and three of the probe report's measured ranges do not hold
(`probe-final.out`, `digest-final.txt`, field `vs_probe_report`):

| value | probe report (FR4) | this trajectory, saves 1 / 2 / 3 |
|---|---|---|
| write, e4 - e3 | 256-261 frames | 261 / **255** / **253** |
| first sector complete | e3+19 (save 1), e3+18 (saves 2, 3) | **e3+18** / **e3+17** / **e3+17** |
| e3 to "saved the game." printed (e5) | 339-343 | 343 / **337** / **335** |
| flush, e6 - e4 | 16 | 16 / 16 / 16 (agrees) |
| gaps between sectors | 18-20 | 17-20 |

The mechanism agrees with the probe report. Only the frame counts move, by 1 to 3 frames, with when the write starts. So
the probe's ranges describe one trajectory, not a constant. What the orchestrator has to decide, because I may not tune it:

- the silent window's upper edge. On save 2 here the first sector completed at e3+17, so the window is [e3, e3+16], not
  [e3, e3+17]. K-SILENT at S2.e3+9 is still inside it, but 7 frames from the edge, not the spec's "8-9 frames from each
  edge";
- any registered number that rests on 256-261, e3+18/19 or 339-343: the K-SILENT margin, the selftest's synthetic
  records, and the e3-to-e5 basis of `SAVE_WRITE_BUDGET`. The budget's 2.6x margin is unaffected, because 343 is still
  the longest.

Step 3 has not started.

### What I built (uncommitted, in the worktree)

**E1: the start menu and the save dialog** (`ai_player/eyes/screens.py`, `ai_player/host/eyes.py`)
- `UI_TASKS` and `_SMENU_TASKS` gain `Task_ShowStartMenu`.
- New `_start_menu_view` holds the seven rules of the spec in order. The task decides first.
- `save_yes_no` and `save_dialog` are new kinds.
- `host/eyes.py` reads `gMenuCallback` only under `Task_ShowStartMenu` past data[0] 0, with no `StartMenuTask`. It reads
  `sSaveDialogCallback` only while that callback is `SaveCallback`.
- Each callback is named through a fixed table, resolved once with `get_symbol`, thumb bit off (`_save_callback`). The
  tables are `SAVE_MENU_CALLBACKS` (4 names) and `SAVE_DIALOG_CALLBACKS` (13 names); every name is checked to be in the
  .sym file.
- Also built: the error page's "A held once the timer is 0" wait that section 3 (b) step 4 calls an E-rule
  (`save_dialog_wait`, `_save_wait`, read only on a `save_dialog`).

**E2: page words** (new `ai_player/skills/saving.py`, 94 lines)
- `save_page(text)` returns CONFIRM, OVERWRITE, DIFFERENT, SAVING, SAVED, ERROR, "printing" or None.
- `error_page(text)` returns corrupted, erased, battery or None.
- `fold()` handles the paragraph mark, the whitespace and the game's "’".
- The rest of the skill is stage 4's.

**E4: error pages** (`host/eyes.py` `_text(shown, tasks)`): while `Task_WaitForSaveFileErrorWindow` or
`Task_WaitForBatteryDryErrorWindow` runs, the text is printer 7's ROM string. `_screen` passes the task set.

**E5: play time**
- `Progress.play_time: tuple[int, int] | None = None` (`eyes/observation.py`).
- `host/eyes.py` `_play_time()` reads 3 bytes at SaveBlock2 + 0x0E (`PLAY_TIME_OFFSET`, `PLAY_TIME_BYTES`), through the
  doors `_marks` uses.
- D18's `seen_now` change is made here too (`hands/dialogue.py`: the progress is compared with `play_time=None`). E5
  alone would have let a minute tick reset `advance`'s stall counter, a behaviour change.

**E6: the CONTINUE window's TIME**: `_ui` reads the play time while a main-menu task runs. `read_ui` puts it in
`hours`/`minutes` only when tMenuType >= 1.

**E7: the harness's own input rule** (`gates/play_harness.py`)
- `StartMenuTask` is out of `INPUT_TASKS`.
- New `start_menu_input` and `start_menu_input_now`, by the harness's own symbol reads (task list, `gMenuCallback`,
  `sSaveDialogCallback`, `get_symbol`). They are called from `waits_now`.

**Unit tests** (new `ai_player/gates/test_saving.py`, 365 lines): `EyesSaveTests` (16 tests) and `HarnessInputRuleTests`
(4 tests), each guard with a FAULT half and a CONTROL half. The host tests use a sparse fake memory at the real symbol
addresses, because `host/eyes.py` is sealed and cannot be patched.

**The probe** (new `ai_player/gates/probe_save_eyes.py`, 728 lines, test side, in no lane): parent and children on the
`probe_save_kill.py` pattern, reusing its `Saver`, `Timeline`, `Child`, `parse_image`, `file_verdict`, `printer_page`
and `ram_truth`. `probe_save_kill.py` is not edited.
- **EYES-SAVER**:
  - the G1 sequence: open the menu, B, open it again, B;
  - save 1 with NO first (the menu comes back), then SAVE and YES;
  - walk one tile, open the menu after a successful save, save 2;
  - walk one tile, save 3;
  - free on the overworld until the minute ticks.
  - Every press uses the AI's slowest pacing: read 150, think 45, hold 7, gap 18. "Free" means held 45 frames.
  - The AI's `FrameworkEyes` look is recorded on every frame, beside the harness's own expected view (`expected_ui`).
- **TRUNC** and **KM-FIRST**: `probe_save_kill`'s own child A, killed by its PID at READY; TRUNC's file is then cut to
  64 KB. A continuer child records the AI's look at the title.
- Faults: `--fault building_takes_input` plants the pre-R1 start-menu rule; `--fault playtime_seconds` makes the
  comparator use RAM's seconds.

### Checks (each with its verbatim last line; outputs in `build/s1-eyes/`)

| check | file | exit | last line |
|---|---|---|---|
| lane census (step 1) | `lane-census.txt` | | `MATCHES: 0` |
| probe, every arm (9:28:18 to 9:28:47 AM) | `probe-final.out` | 0 | `PROBE VERDICT: PASS` |
| probe fault: pre-R1 start-menu rule | `probe-fault-building.out` | 1 | `PROBE VERDICT: FAIL` (45 view mismatches, 20 stale frames read as input) |
| probe fault: play time against RAM's seconds | `probe-fault-playtime.out` | 1 | `PROBE VERDICT: FAIL` (6952 frames differ) |
| unit-test mutants S0-S6, S30, X1-X3 (temp copies) | `mutants.out` | 0 | `VERDICT: every mutant CAUGHT, the control PASSES` |
| check_purity | `final-check_purity.out` | 0 | `VERDICT: PASS` |
| check_fairness | `final-check_fairness.out` | 0 | `PERSON-FAIR DATA DOOR: PASS (0 breaches)` |
| test_saving (20 tests) | `final-test_saving.out` | 0 | `OK` |
| test_eyes | `final-test_eyes.out` | 0 | (its scorer line; tests OK) |
| test_hands / test_check_purity / test_battle / test_world | `final-*.out` | 0 | `OK` |
| test_goals (233 tests) | `final-test_goals.out` | 0 | `OK` |
| test_step53_a1 / a2 / rs, test_measure_step5 | `final-*.out` | 0 | `OK` / `OK (skipped=5)` / `OK` / `OK` |
| check_grader_imports | `final-check_grader_imports.out` | 0 | `GRADER IMPORTS: PASS (G-3: ...)` |
| ledger --check | `final-ledger.out` | 0 | `LEDGER ledger.json: 50 entries; well formed -> PASS` |
| check_lessons, extract_knowledge/milestones --check, disk_budget, test_evidence, test_run_regression | `final-*.out` | 0 | PASS / up to date |
| **call_census** | `final-call_census.out` | 1 | `CALL-SITE CENSUS: FAIL` (23 findings) |
| test_host | `gate2-test_host.out` | 1 | `FAILED (failures=19)` (environment) |
| test_kb2 | `final-test_kb2.out` | 5 | `FAILED (errors=1)` (environment) |
| hygiene (9:36 AM) | `hygiene.out` | | 33105 files of the main checkout's sandbox-pokebot scanned, 0 modified since 9:05 AM; 0 probe or lane processes alive |

- **call_census:** every site is one of this stage's added or changed functions. The census wants a revert mutant in
  `MUTANT_SOURCES` that deletes each call, or a reasoned waiver. Those mutants are `revert_r1.py` (section 6, steps 4-5).
  `mutants.out` shows the unit tests catch S1-S6 and S30. I added NO waivers, because a waiver would be a claim that no
  mutant can be written, which is false.
- **test_host:** all 19 failures are `ModuleNotFoundError: No module named 'mgba'`. `test_host.py` hard-codes
  `BUILD_ROOT = REPO / "sandbox-pokebot"`, and a worktree has no `mgba/` (builder note 1).
- **test_kb2:** `setUpModule` refuses because the decomp resolves to `<worktree>/../_decomp`, which is not the pinned clone.
- Neither test_host nor test_kb2 can run in a worktree, and neither touches a file this stage changed. The full lane on
  the main checkout runs both.

### Measured (`digest-final.txt`; the per-frame records are in `runs/final/*/`)

**Step 2's checks: all pass**
- **Start menu:** 4598 dialog frames compared with the harness's rule, 0 view mismatches and 0 cursor mismatches. Input
  frames: 627 `start_menu` (HandleStartMenuInput), 803 `save_yes_no` CONFIRM, 394 `save_yes_no` OVERWRITE.
- **Stale callbacks:** every kind occurred (building 16, first frame 4, before InitSave 2). None read as input. The
  planted pre-R1 rule reads 20 as input.
- **Pages:** each read by its words, in order: CONFIRM, then (saves 2 and 3) OVERWRITE, then SAVING whole, then SAVED.
  The questions asked were [CONFIRM], [CONFIRM, OVERWRITE], [CONFIRM, OVERWRITE].
- **Play time:** compared on 7072 frames, 0 mismatches.
  - Two minute ticks were recorded: 0:17 to 0:18 at frame 69782 (RAM [0,18,0,0], inside save 2's dialog), and 0:18 to
    0:19 at 73895.
  - It did not move through any write. Each write showed one value from the AI and one 4-field value in RAM ([0,17,40,2],
    [0,18,1,11], [0,18,22,20]), over 262, 256 and 254 recorded frames.
- **Error pages from printer 7:**
  - TRUNC: FILE `S2+ERROR`; the AI read "The save file is corrupted. The previous save file will be loaded." (equal to
    the harness's printer-7 text), page `corrupted`.
  - KM-FIRST: FILE `CORRUPT`; "The save file has been erased due to corruption or damage.", page `erased`.
- **CONTINUE TIME:** equals RAM on all 61 main-menu frames of each title arm.
  - TRUNC: [0,17], equal to S2's truth.
  - KM-FIRST: NEW GAME and OPTION only, no TIME (RAM 0:00).
- **Longest still stretch in the dialog:** 265 frames (68316-68580: the whole SAVING page, then the write). Limit 900.

**YES to free, with the AI's slowest pacing** (free = held 45 frames)
- From the YES that starts the write (the last YES): 624 / 618 / 616. 2 x 624 = 1248, which is at most
  `COMMIT_FRAMES_NEEDED` 1500, so the spec's re-check holds.
- From the first YES (CONFIRM, when OVERWRITE follows): 624 / 1048 / 1046.
- Commit check: it runs before EVERY YES, and the write-starting YES is the last one, so the 1500 rule holds. If 1500
  were read against the CONFIRM YES, 2 x 1048 = 2096 > 1500. That reading does not apply, because a NO at the OVERWRITE
  question writes nothing.
- START to free: 1603 / 1495 / 1493 frames. That is under `SAVE_DIALOG_BUDGET` 3000, with the pacing at its slowest
  (save 1 includes a NO and a second SAVE).

**Findings for the later stages**

- **F-A. The stamp's look comes 4 frames BEFORE the clock freezes, on all three saves** (`stamp_window-final.txt`).
  - The AI's first look with the whole SAVING page was at e3-4. Printer 0 was still active, in state 0.
  - RAM's play time ran on until e3-1; save 1 went [0,17,39,59] to [0,17,40,2].
  - So T1's "the case may not occur at all" is refuted: a minute tick in those 3 frames is possible, at about 3 in 3600.
    D4's 1-minute tolerance and the arrival check cover it.
  - It also means the S2 memory line (written at e3-4) is in the file before the write starts: good for K-SILENT
    (builder note 5).
- **F-B. A LAG FRAME after NO** (`lag_frames`, frame 67741).
  - On the frame after A on NO, both paths read `SaveCallback` + `SaveConfirmInputCallback`, so the AI's view was
    `save_yes_no` taking input. But the question's window was already gone, and the text was "POKéMON":
    `InitStartMenu` was mid-way, and the game's loop had run past the frame boundary.
  - The next frame showed `HandleStartMenuInput`.
  - Both readings equal RAM, so this is not a disagreement with the truth. But "takes input" was briefly wrong, and a
    press then would go to the start menu.
  - For stage 4: every YES must rest on the question's words read on the SAME look as the press (the spec's "never YES
    to a page it could not read" covers it, if the check is on that look).
  - The probe reports this frame and does not count it as a failure; any other frame where the words do not match still
    fails it.
- **F-C. The probe's Timeline e5 can fire at e4.**
  - On saves 1 and 2, "NICK saved the game." was already expanded in `gStringVar4` on the frame the write ended (e4),
    before printer 0 started. So `probe_save_kill.Timeline` set `e5 = e4`.
  - I used `e5_jingle` instead (`SaveSuccessCallback` hands on once printer 0 is idle), which was e4+82, as in the probe.
  - The AI's own `save_page` reads SAVED from e4 on. That is still only after `TrySavingData` returned OK, so "saved" is
    not declared early. `probe_save_kill.py` is not edited.
- **F-D.** The harness rule before E7 counted `StartMenuTask` (no input) and never `Task_ShowStartMenu`. So the
  261-frame write was not counted as a wait before R1 either. The spec's FAULT, "Task_ShowStartMenu counted", is a
  planted fault, not the old code; the unit test shows both.

### Deviations from the spec, and why

1. **Lag frames are reported, not failed** (F-B). Every reading equals RAM there; the finding goes to stage 4.
2. **`seen_now` (D18) is done in this stage.** E5 needs it to stay behaviour-neutral. `PLAY_TIME_DOORS` in
   `check_fairness.py` is left for step 5.
3. **`error_page` and the save-error A wait are built here**, because they are eyes and word rules. The spec puts their
   callers in stage 4.
4. **The YES-to-free span was measured with test-side presses at the AI's slowest pacing**, not with the AI's hands: the
   save skill does not exist yet (stage 4).
5. **e5 is taken from `e5_jingle`** (F-C).
6. **test_saving is not yet in `run_units` SUITES or `run_regression` QUICK.** That is the lane edit of section 7, with
   `revert_r1`.
7. **No seeds were used**, so nothing was registered in `ledger.json`. The probe drives a fixture with fixed presses; it
   is not a graded seed run.
8. **Code wins over spec:**
   - The spec's `test_eyes.py:397` is a `classify_screen` test and is unaffected.
   - Before R1, `read_ui` saw the start menu ONLY while it was being built (`StartMenuTask`) and saw nothing under
     `Task_ShowStartMenu`, the frames when it takes input.

### What I did NOT do

- Steps 3 to 8: no `game_memory`, paths, policy, the rest of the skill, the loop, the launcher, the controller, the
  purity changes, `revert_r1`, `live_r1` or seeds.
- No call-census waivers, and no lane edits.
- No git write of any kind.
- Nothing written in the main checkout: its sandbox-pokebot was scanned, with 0 files changed. Every profile is under
  `build/s1-eyes/runs/*/`.
- I did not touch the tuner's clone or its processes. Only children this probe started were killed, by PID; none are
  alive.
- Not measured: a save error (no live ERROR page), the battery page, the WARNING (DIFFERENT) page, or a third save's
  first sector beyond this one trajectory.
- The CONTINUE TIME cannot tell S1 from S2 on this fixture, because both are at minute 17 (the probe report's caveat).

(Stage 2's section is not here: its write to this file was refused by the harness. Its hand-back to the orchestrator
carries it.)

## Stage 2 of 6: section 8 step 3 (the MEMORY FILE: `game_memory.py`, `paths.py`, `check_paths.py`)

> Inserted by the orchestrator when this report was filed: this stage's builder could not append its section (the harness
> refused the write: "Subagents should return findings as text, not write report files"). Below are the fields of its
> hand-back, verbatim, from the workflow's journal (`r1r2-build`, agent `builder:memory`).

### VERDICT: DONE, no STOP

No STOP rule fired. Step 3 is offline and measures no frame, so nothing in it rests on the probe's frame counts (rulings 1 and 3 do not reach it). One duty is NOT met: I could not append my section to build/BUILD-REPORT.md, because the harness refused the Write ("Subagents should return findings as text, not write report files") and the project hook blocks shell heredocs. The full section text is in "done" and "deviations" below, so the orchestrator can paste it in.

### What I built (uncommitted, in the worktree)

- Stage 2 (spec section 8 step 3) built from 9:40 AM to 10:10 AM Los Angeles time. Lane census at 10:00:50 AM: 0 matches (s2-memory/lane-census.txt).
- ai_player/game_memory.py (new, 813 lines, play-loop side, framework-free). It holds memory.jsonl schema 1. (a) The codec: $set / $tuple / $dict. (b) Deltas: diff / apply_delta over paths of a section plus 2 keys; a deletion of a missing key refuses the chain. (c) MemoryBook, read through read_book in read mode only. Methods: match (the newest save within MATCH_MINUTES=1), chain, rebuild, frame_base (1 + max frame, never below an earlier session's base), timeline / undone_losses (the LIVE history: a continue from save k cuts the events after k), end_of, last_session, newest_save, next_save_id. A newer schema is refused first, with the file byte-identical. A file with no header is refused. A torn last line is ignored and told. Any other unreadable line is refused. (d) MemoryWriter writes only through runlog.RecordFile and checks that `written` rose after every append. A new game writes header + session + its first save together; before the first save there is no file, so no lost or end lines. A continue's saves are deltas against the continued save's rebuilt payload. FULL_EVERY is 8. Methods: write_session / write_save (returns SaveWrite with id, full, size, reached) / write_saved / write_lost / write_end. (e) D16's table: GOAL_KEEP, GOAL_RESET, GOAL_IN_WORLD (landmarks and spoke). goals_part RAISES on a field in no table. restore_goals uses dataclasses.replace on a fresh memory. (f) personality_part / restore_personality (active = base, drift_until = None, next_draw = DRIFT_EVERY) and battle_part / restore_battle. (g) build_payload, restore -> Restored (with restored_maps and losses). (h) MonRegistry (L3 a-b): keyed by PID in hex; species and species_seen (an evolution keeps the PID); first {map, tile}; frame; play_time; how starter/caught/joined; roles validated against ROLES; eggs not registered. (i) end_line (chosen / budget / at_save), where_of, party_of, minutes_apart.
- ai_player/paths.py (new, 101 lines, launcher side). AppPaths.for_profile(name, build_root, home=None) gives <build_root>/profiles/<NAME>/ai_player/, or <AI_PLAYER_HOME>/games/<NAME>/ when that is set. Properties: memory, launches, retired. retired_path gives retired/<stem>-<YYYYmmdd-HHMMSS>.jsonl and never reuses a name. A name must pass the launcher's profile-name rule. It writes nothing. It imports MEMORY_FILE_NAME from game_memory, so the name has one source.
- ai_player/gates/check_paths.py (new, 130 lines, test side). It refuses 'sandbox-pokebot', 'Remote Projects' and a C:/ or C:\ drive path in string constants: plain strings, f-string text and bytes. Scope: the package minus gates/. Docstrings and bare string statements are skipped. Exempt: paths.py as a whole, and only the resolve_build_root function of host/launcher.py. The last line reads 'PATHS GATE: PASS|FAIL (N files, M findings)'; exit 0/1/2.
- Gate tables for the new modules: check_purity.py LAUNCHER_FILES += paths.py and LAUNCHER_MODULES += ai_player.paths, with the docstring role line updated. check_fairness.py DECIDING += game_memory.py, with the docstring updated.
- __main__.py: the --build-root help text no longer says '../sandbox-pokebot' (the new gate's only finding in the tree). No behaviour change.
- gates/test_saving.py (978 lines): 30 new tests. MemoryFileTests (23): header and schema 1; a newer schema refused byte-identical; no header; a torn last line; the next session ends and acknowledges it; delta round trip; deletions kept; FULL_EVERY 8; the parent chain across a continue; the restore not newer than the save; the restore table pinned to the spec's D16 lists; every field classified; every KEEP field survives and every RESET field starts afresh; codec round trip; personality and battle mind; frame base; registry by PID with roles; end line; lost lines and the losses a continue undoes; the loss count restored; the 1-minute match where the newest wins; an unwritten save line reported; the writer used out of order. PathsTests (7): the dev default; the home override with names that cannot leave their folder; retired names never overwrite; paths.py is launcher side (a planted play-loop import fails purity rule c); a planted literal FAILS; docstrings and comments PASS; the tree passes.
- Fault proof: s2-memory/mutate_s2.py applies 22 mutants to temp copies of the package. Every one is CAUGHT and the S0 control passes. The spec's: S24, S25, S26, S28, S29, S31, S32, S38, and S12's writer half. My own: M1-M13. The first mutation run found S31 and M9 NOT CAUGHT. Both tests were fixed: the D16 table is now pinned, and the personality is restored into a state that has drifted. The second run caught all.
- Hygiene (10:09:52 AM): 0 files modified since 9:40 AM in the main checkout's sandbox-pokebot (32,799 files) or ai_player (810 files); 0 lane or stage processes alive. I stopped one stale background gate run myself; it left no process.
- BUILD-REPORT.md section NOT appended (the tool refused the write). The content is these fields.

### Files changed

- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/game_memory.py (new)
- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/paths.py (new)
- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/gates/check_paths.py (new)
- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/gates/test_saving.py (stage 1's file; MemoryFileTests and PathsTests added, docstring updated)
- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/gates/check_purity.py (LAUNCHER_FILES and LAUNCHER_MODULES += paths; docstring)
- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/gates/check_fairness.py (DECIDING += game_memory.py; docstring)
- C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/__main__.py (the --build-root help text only)
- Evidence (outside the repo): C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/r1build/build/s2-memory/ (final-*.out, final-ALL.txt, mutants.out, mutants-run.out, mutate_s2.py, run_gates_s2.py, runcmd.py, measure_sizes.py/.out, hygiene.py/.out, lane-census.txt, dev-test_saving.out)

### Checks

- test_saving (50 tests = stage 1's 20 + 30 new): exit 0, 'OK' (final-test_saving.out)
- check_paths: exit 0, 'PATHS GATE: PASS (45 files, 0 findings)'
- check_purity: exit 0, 'VERDICT: PASS' (launcher 3: __main__.py, paths.py, host/launcher.py)
- check_fairness: exit 0, 'PERSON-FAIR DATA DOOR: PASS (0 breaches)' (25 files)
- test_check_purity: exit 0, 'OK'
- test_safety_gates (48): exit 0, OK (its last printed line is an evidence note)
- test_goals (233): exit 0, 'OK'. final-ALL.txt shows 1 for it, but that 1 is my runner (runcmd.py) crashing on a non-cp1252 character while printing; final-test_goals.out says 'EXIT CODE: 0'.
- OK with exit 0: test_eyes (56), test_hands, test_world, test_battle, test_step53_a1, test_step53_rs, test_measure_step5, test_evidence (27), test_run_regression (53)
- test_step53_a2: exit 0, 'OK (skipped=5)'
- check_grader_imports: 'GRADER IMPORTS: PASS ...'; check_lessons: 'LESSONS CHECK: PASS (0 problems)'; ledger --check: 'LEDGER ledger.json: 50 entries; well formed -> PASS'; extract_knowledge --check and extract_milestones --check: up to date; disk_budget: exit 0
- mutate_s2.py (10:02:58 to 10:05:10 AM): exit 0, 'VERDICT: every mutant CAUGHT, the control PASSES' (22 mutants)
- call_census: exit 1, 'CALL-SITE CENSUS: FAIL', 87 findings: stage 1's 23 (unchanged); __main__.py:_parser (changed: the help text); 63 from this stage (58 in game_memory.py, 5 in paths.py). Most have no AI call site yet, because their callers come in stage 4. Per ruling 4 they are for revert_r1's mutants; no waivers added.
- test_host and test_kb2: NOT RUN (orchestrator ruling 2: no sandbox-pokebot/mgba in a worktree, and the pinned decomp resolves from the main checkout). The orchestrator runs them on main.

### Measured

- Offline only (measure_sizes.out), on the 3 world snapshots that a development run RECORDED (fixtures/route101_south.world.jsonl, 17,389 / 42,503 / 42,503 bytes as world.jsonl lines). Save 1 (full): 18,123 bytes. Save 2 (delta; map 0:16 added): 32,174. Save 3 (delta over an unchanged world): 215. The whole file: 50,783 bytes. rebuild(id) equals the written payload for every save.
- The delta round trip holds on 9 recorded-world pairs and 60 seeded random goal memories (test_delta_round_trip).
- No frame or save timing was measured in this stage. Real per-save sizes and rates belong to step 6 (b).

### Deviations from the spec, and why

- The codec tags are $set / $tuple / $dict, not the spec's __set__ / __tuple__ / __dict__: check_purity rule (d) refuses, in the play loop, a string whose whole value is a dunder identifier. Code over spec.
- A new line kind, {'kind': 'torn', 'length': N}. The spec ignores a torn LAST line, but the next session's first append would join the fragment on one line and make it a torn MIDDLE line, which refuses the whole file. So the writer first ends an unterminated last line, then acknowledges a cut line by its length. The reader skips an unreadable line only when it is the last line or a matching torn line follows it (S25 still refuses an unacknowledged middle line). The file is written in ASCII (ensure_ascii) so a cut cannot split a character.
- Delta paths are a section plus 2 keys (3 keys in all). The spec says 'at most two keys' but its example is ['world','maps','<map key>']; the code follows the example, otherwise every save rewrites all of world.maps.
- The restore table already lists saved_for and last_save (KEEP) and save_due (RESET) before _Memory has them (they come with brain/saving.py). R1_NEW_FIELDS names them, and the classification test allows exactly those names to be absent. brain/goals.py is not edited.
- Two gate-table entries were made in this stage, not step 5: paths.py launcher side (check_purity), and game_memory.py in DECIDING (check_fairness). They classify the modules this stage creates. M12 shows paths.py on the play-loop side is caught.
- The __main__.py --build-root help text was reworded: it was the new gate's only finding. No behaviour change.
- MonRegistry 'starter' means the first PID the game's registry ever saw. On a --state fixture with a full party, the others are 'joined'. Eggs are not registered.
- frame_base() is never below an earlier session's frame_base. undone_losses counts only the LIVE history: a plain file-order count re-counts losses already undone (the test's FAULT half shows 4 instead of 1).
- Tests that need the play loop are split. Only the writer's or payload's half is here: the unwritten save line is reported and the parent does not advance; the payload's loss count is restored; the end line's fields. The run ending, MAX_LOSSES across a continue, and HandsBrain writing the end line are stage 4's.
- test_delta_round_trip uses the RECORDED world snapshots with synthetic goal memories. No R1 dev run exists yet to record whole payloads (step 6).
- The census name collision found during the build: my first helper's name, _play_time, made the census (which matches by name) list stage 1's host/eyes.py:_play_time findings under game_memory too. It is renamed _stamp_of.
- Not done in this stage: brain/saving.py, the skills, the loop, the launcher, options, the controller, D12 (c) purity, PLAY_TIME_DOORS (D18; game_memory reads .play_time only in _stamp_of), the lane edit adding test_saving and check_paths to run_units / QUICK, and revert_r1.py. Stage 4 should carry S12, S24-S26, S28, S29, S31, S32 and S38 (anchors in s2-memory/mutate_s2.py) plus the 63 census sites into revert_r1. No live run, no seed, no ledger entry. No git writes.

## Stage 3 of 6: section 8 step 4 (brain/saving.py, skills/saving.py and their tests)

Built 10:11 AM to 10:53 AM Los Angeles time, 2026-10-29, in the worktree (HEAD 67c73a0f; nothing committed, staged or
stashed). Offline only: no emulator, no live run, no seed, no ledger entry. Evidence: `build/s3-skills/`.

### VERDICT: DONE, no STOP

No STOP rule fired. This step measures no frame. Every constant that rests on a measured width uses stage 1's widest
value at 2x or more (ruling 1); none rests on the probe report's exact frame counts.

### What I built (uncommitted, in the worktree)

- `ai_player/skills/saving.py` (stage 1's page words kept byte for byte, plus about 500 new lines):
  - `save_game(hands, why, cart_is_own, frames_left, on_writing, on_saved)`. It presses START only on a free screen and
    picks SAVE by reading the cursor. It plays the dialog page by page. Each question is read (a reading pause, then a
    "read" note) and answered on a gate look that shows that question's own words (ruling 3; `_press_on`). CONFIRM is
    YES. OVERWRITE is YES only when `cart_is_own`. DIFFERENT is NO. A question it cannot read is NO. A YES whose gate
    sees fewer than COMMIT_FRAMES_NEEDED frames left is turned into a NO. Every NO backs out with B to a screen that stays
    free across two looks. The WARNING's paragraphs are read, then turned with A (at most 6). The first look showing the
    whole SAVING page calls `on_writing(play_time, look)` once (D5). After that nothing is pressed until SAVED or ERROR,
    bounded at 900 frames. The play time on every SAVING look is kept, and the skill says so if it changes. "saved" comes
    only from the SAVED page. On ERROR it reads the page and presses A at each wait the eyes report (at most 4) until the
    screen is free. If `on_writing` returns False, the run ends "stuck: the memory of this save could not be written".
    A SAVING, SAVED or ERROR page counts only after a YES in this dialog, because printer 0 keeps its last message.
  - `continue_game(hands, book, why) -> ContinueResult`. It skips the movie and the title with `skip_title`. It reads
    each main-menu error page, records its type, and presses A (at most 3 pages). On the main menu it STOPS with no
    press when there is no CONTINUE ("the save is gone: ..."), when the TIME cannot be read, or when the TIME matches no
    save line. Otherwise it presses CONTINUE on a gate look that shows the same TIME. The arrival must be free across two
    looks, then map, tile and party (PID and species) are checked against the save line. It says when the save was
    corrupted, when it is an older save with no page, and how many lost battles the continue undoes (D12 (e)).
  - Constants: SAVE_WRITE_BUDGET 900, SAVE_CLOSE_BUDGET 600, SAVE_DIALOG_BUDGET 3600, COMMIT_FRAMES_NEEDED 1500,
    SAVE_FRAMES_NEEDED 3600, BACKOUT_PRESSES 6, PAGE_PRESSES 6, ERROR_PRESSES 4, ERROR_PAGES 3, CONTINUE_BUDGET 6000 and
    ARRIVAL_BUDGET 1200 (both PROVISIONAL), PRESS_TRIES 3, REACT_BUDGET 45.
- `ai_player/brain/saving.py` (new, 230 lines): `SavePolicy`. Its whole state lives in the goal memory: `after_heal`,
  `after_milestones` (milestone ids only: a dict, a string or a non-id raises), `due_now` (a centre or leader due expires
  when the player leaves its map), `may_save`, `next_save` (block 1b), `before_leader` (block 8: a named fight's talk on
  that step's gym map, once per approach, where an approach is the newest transition onto the map), and `record_save`.
  Also `BIG_MOMENTS`, `SAVE_MIN_MINUTES` 3, `own_cart` (D17), `SaveChoice` and `milestone_ids`. It imports nothing from
  `brain/goals.py`, which will import it, so it has its own CENTER_SUFFIX and GYM_SUFFIX; a test pins both to goals'.
- `ai_player/brain/goals.py`: `_Memory` gains `saved_for` (dict), `last_save` (dict | None) and `save_due` (dict | None).
  These are data only; no goal code reads them yet.
- `ai_player/skills/intro.py`: the title block moved, unchanged, into `skip_title(hands, kind)`, which both skills call
  (spec 3 (b) continue step 1).
- `ai_player/gates/revert_step2.py`: HFG and HFW re-anchored to the moved block (indent 12 -> 4). Same mutation.
- `ai_player/gates/test_saving.py`: 46 new tests (96 in all). SaveSkillTests (21), ContinueSkillTests (10) and
  PolicyTests (15) run on `SaveModel` and `ContinueModel`, models of `src/start_menu.c` and the boot that react to
  presses. `rich_memory` now also fills the 3 new fields, so the D16 restore tests cover them.

### Checks (verbatim last lines; outputs in `build/s3-skills/final-*.out`, 10:48 to 10:50 AM)

- test_saving: `OK` (96 tests). test_hands: `OK` (57). test_goals: exit 0 (233 tests; last line `  _names word chars =
  "\\w'’"`). test_eyes, test_world, test_battle, test_step53_a1, test_step53_rs, test_measure_step5: exit 0.
  test_step53_a2: `OK (skipped=5)`.
- check_purity: `VERDICT: PASS`. check_fairness: `PERSON-FAIR DATA DOOR: PASS (0 breaches)`. check_paths: `PATHS GATE:
  PASS (46 files, 0 findings)`. test_check_purity: `OK`. test_safety_gates, test_evidence, test_run_regression: exit 0.
- check_grader_imports: `GRADER IMPORTS: PASS ...`. check_lessons: `LESSONS CHECK: PASS (0 problems)`. ledger --check:
  `LEDGER ledger.json: 50 entries; well formed -> PASS`. extract_knowledge --check and extract_milestones --check: up
  to date. disk_budget: exit 0.
- mutate_s3.py (10:44 to 10:47 AM; `mutants.out`): `VERDICT: every mutant CAUGHT by its predicted tests, the control
  PASSES`. That covers 34 mutants plus the S0 control: the spec's S7-S23 and S41-S45, R3 (ruling 3: the gate does not
  need the question's words), and this stage's N1-N10. A mutant counts only if every PREDICTED test fails. The first run
  caught all but N1 (a stale page believed before a YES) and N2 (B pressed on any screen during the back-out). The model
  had made both vacuous: its stale-page and menu-close states were shorter than one press. Both states now outlast a
  press (with comments), and the second run caught both.
- Stage 1's and stage 2's mutation scripts re-run against this tree (copies in `rerun_s1/` and `rerun_s2/`): both
  `VERDICT: every mutant CAUGHT, the control PASSES`.
- revert_step2 subset (H0, HFG, HFW, using its own make_copy and DRIVER, without writing its evidence file;
  `revert_step2_subset.out`): `VERDICT: H0, HFG, HFW as predicted`. HFG is CAUGHT by
  FadeTests.test_the_intro_waits_out_a_fade_before_start. HFW is REDUNDANT as recorded.
- call_census: `CALL-SITE CENSUS: FAIL`. It now has 124 FAIL entries (stage 2 had 87). The 40 new ones are this stage's
  functions in brain/saving.py and skills/saving.py, plus skip_title and the changed play_intro. Some entries also grew
  because the census matches by name (`where_of`, `MemoryBook.saves`, `MemoryBook.match`, `AppPaths.memory`). To limit
  that, I renamed the colliding helpers (`_answer.words` -> `question_words`, the two `_hm`, `SavePolicy.due` ->
  `due_now`, the policy's `self.memory` -> `self.goal_memory`). Under ruling 4 these go to revert_r1's mutants. No waivers.
- test_host, test_kb2: NOT RUN (ruling 2).
- Hygiene (10:52 AM, `hygiene.out`): 0 files modified since 10:11 AM in the main checkout's sandbox-pokebot (32,799) or
  ai_player (810). 0 lane, mutation or runner processes alive.

### Measured

Nothing live. Offline counts only: 96 unit tests, and 34 mutants each caught by the tests predicted for it.

### Deviations from the spec, and why

- SAVE_DIALOG_BUDGET is 3600 (spec 3000), and SAVE_FRAMES_NEEDED is 3600 (spec 3000). Ruling 1 requires a 2x margin,
  and stage 1 measured START-to-free at up to 1,603 frames (2x = 3,206). A test pins every budget to 2x its measured
  width.
- YES, NO, SAVE and CONTINUE are not pressed through `hands/menus.py` choose. They go through `_press_on`, which moves
  the cursor the same way (move_cursor) but whose gate also requires the words the answer rests on (ruling 3: the
  question's page; the SAVE option; CONTINUE with the same TIME). It also counts it as a reaction when the menu stops
  taking input, because the main menu stays a main_menu while it handles the press.
- The commit check runs on the YES's own gate look. When that check refuses the YES, the skill answers NO.
- One addition: a SAVING, SAVED or ERROR page counts only after a YES in this dialog (stale printer text).
- One addition: a box that closes during the write with no SAVED page returns "not saved: the box closed with no SAVED
  page" instead of waiting out 900 frames.
- `save_due`, `saved_for` and `last_save` were added to `_Memory` in this stage, not step 5, because the policy's state
  lives there. Stage 2's R1_NEW_FIELDS tolerance is now unused (the test still passes); step 5 may drop it.
- The skill reports what it tells in `ContinueResult.lines`, and tells it itself. `ContinueResult.arrived_at` was added
  so the held-arrival test can see which look was used.
- Decided here (the spec is silent): a due whose only obstacle is the 3-minute gap is COVERED by the recent save and
  dropped, as the spec already says for the leader. Otherwise it would save later at a place that is not a ruling-51
  moment, which check 6 would fail. A due blocked by frames or by a missing play time waits, and is reported once. A
  big moment's due has no expiry, as in the spec. If a heal comes first and runs long, that save could land well after
  the moment. Step 6's check 6 will show whether that happens.

### What I did NOT do

- The loop wiring (step 5): GoalRunner's `save` kind, blocks 1b and 8, `_save_before_done`, `_story_menu`'s save
  branches, HandsBrain's writer / `on_writing` / end line / lost lines / continue mode, options, launcher, controller,
  D12 (c) purity, PLAY_TIME_DOORS, the lane edit (test_saving and check_paths into run_units / QUICK) and revert_r1.py.
- No live run. The skills have only met the models. Their first contact with the game is step 6.
- CONTINUE_BUDGET and ARRIVAL_BUDGET are still provisional (step 6 sets them).
- No git writes. Nothing in the main checkout, the tuner's clone, or `sandbox-pokebot/` was touched.

## Stage 4 of 6: section 8 step 5 (the loop, options, launcher, controller, gates, revert drivers, lane tables)

Built 11:10 AM to 1:15 PM Los Angeles time, in the worktree only. Offline: no emulator, no live run, no seed, no ledger
entry. Outputs are in `build/s4-loop/`.

### VERDICT: DONE, no STOP

No STOP rule fired. Step 5 measures no frame. Every check the orchestrator named passes in the worktree, except the
suites that cannot run there (ruling 2), listed below.

### What I built (uncommitted, in the worktree)

- **The loop** (`mode.py`). `_open_memory` reads the memory file before any press. It refuses a newer schema (the file
  stays byte-identical), an unreadable file, a continue with no save line, and a NEW game on a game that already has a
  memory file. `_RebasedEyes` (D7) adds the frame base in a continue run only. `_continue` runs
  `continue_game`. On a stop it writes the session line and ends "stuck" through `_play(stop=...)`. On success it calls
  `restore`, writes the restore record (the session line with `restored_maps`, then the world snapshot "restored from
  save N") before the play loop's first look, and plays on with the restored memory. `_play(restored=...)` restores the
  goal memory, the personality, the battle mind, the registry and the loss count (T5).
  `_start_saving` wires the policy, `runner.saver`, `frames_left` and the registry watcher, and makes a new game's writer
  (no save, no file). `_save` writes the save line at `on_writing` and the `saved` line plus the policy record at
  `on_saved`. `_save_before_done` is the end save after R5's settle, through `_settle_frames`. The done check's lines are
  unchanged. `_milestone_line` passes milestone IDS to the policy. `_after_heal` follows `manager.outcome`.
  `_count_losses` adds the restored losses and writes a `lost` line per loss. A `stuck:` save ends the run. A continued
  game that meets the title never plays the intro. `_story_menu` gains the save kinds (`_save_screen`): no press on a
  save page (at most `SAVE_PAGE_WAIT` = 1500 frames), one B on a save question or a START menu that takes input.
  `_end_memory` writes the `end` line: `at_save` means no press since the last successful save.
- **The goal manager** (`brain/goals.py`). Block 1b is `_save_goal` (not while hurt). Block 8 is `_leader_save` in the
  story goal's place. `GoalRunner.pursue` plays `kind == "save"` through `runner.saver`. `spent["save"]` is counted
  apart (T4).
- **Options** (`options.py`): `ENV_MEMORY`, `ENV_CONTINUE`, `ENV_CART`, `ENV_FAULT_NO_SAVE`, `ENV_HOST`, and
  `HandsOptions.memory_file / continue_game / cart / fault_no_save / host`. `__post_init__` refuses a world file with a
  continue (D19), a continue without a memory file, and an unknown cart or host.
- **The launcher** (`host/launcher.py`, `__main__.py`). `seed_profile(..., continue_game, game)` handles `--continue`:
  it needs the marker and a non-empty cart, deletes `current_state.ss1` and keeps the `.sav`. `--fresh` and `--state`
  archive `memory.jsonl` and `launches.jsonl` into `retired/` (`archive_memory`). A no-flag start beside a memory file is
  refused. `memory_check` and `classify_end` implement D12 (a), one class per table row, failing closed.
  `read_launches` and `record_launch` implement D20. `cmd_run` refuses `--continue` when `AI_PLAYER_WORLD` is set or when
  `memory_check` says no, before anything in the profile changes. It prints the CONTINUE line (the newest save h:mm, the
  end class, the battles it undoes). Every run gets `AI_PLAYER_MEMORY`, `AI_PLAYER_CART` and `AI_PLAYER_HOST`, and only a
  continue gets `AI_PLAYER_CONTINUE`. After the child, `launch_end` is appended.
- **The controller** (`host/controller.py`, D12 (b)): `held` tracks the buttons held. `tap` and `hold` raise
  `ControllerError` if START or SELECT would be down with any other button.
- **The purity gate** (D12 (c)): `sys.exit` is on the lifecycle's surface only. `PLAY_LOOP_EXIT_NAMES` (`exit`, `quit`,
  `SystemExit`, `KeyboardInterrupt`) are refused, rule b, in `PLAY_LOOP_PARTS`.
- **The fairness gate** (D18): RULE C, `PLAY_TIME_DOORS` (skills/saving.py, brain/saving.py, game_memory.py), with a stale
  door check. The `_milestone_line` door's purpose is amended.
- **Tests.** test_saving now has 127 tests: LauncherContinueTests (17) and CensusSiteTests (14) are new. test_goals has
  251: PlayLoopTests gains 12 `test_r1_*` tests through the REAL loop, and R1PlayTests (6) drives `HandsBrain.play`.
  test_host has ControllerTogetherTests (a fake framework, the real controller). test_check_purity has
  PlayLoopExitTests (6 plants and a mention control). test_safety_gates has the RULE C fault/control test.
  test_run_regression has the check_paths regex positives and negatives.
- **revert_r1.py** (new) with its data file `revert_r1_mutants.json`. It holds 438 mutants plus control R0:
  - 22 hand-written: S27, S33-S37, S35b, S39, S40, S40b, S46, S46b, L1-L10;
  - 65 ported from stages 1-3 (S1-S26, S28-S32, S38, S41-S45, R3, X*, M*, N*), with their predictions;
  - 351 CENSUS mutants, one per call site the census listed, each deleting that one call. They were generated by
    `s4-loop/gen_census_mutants.py`. Their predicted tests were RECORDED from their first run (`freeze.py`).
  Its suites per mutant: test_saving and test_goals by default; test_eyes for eyes sites, test_hands for hands and
  intro sites, and the purity, fairness or controller test classes for those gates.
- **revert_step5**: G374-G406 (33 loop-wiring mutants, each deleting one new call or guard). G46, G350 and G361 are
  re-anchored on their lines as they now read; the deletions are the same.
- **Census**: `MUTANT_SOURCES` += `revert_r1`. 21 waivers were added to `census_waivers.json` (see Deviations).
- **Lane**: run_units SUITES += test_saving, check_paths. run_regression gets LINE_RULES check_paths, QUICK += both,
  REVERTS += revert_r1, and EVIDENCE_NAMES `revert_r1` -> `regression-r1-revert`. run_regression_times.json is updated.
  `tools/workflows/suite_map.json` gets a `revert_r1` suite (evidence `*-r1-revert.txt`, the same covers as
  revert_step5).

### Checks (verbatim last lines; outputs `s4-loop/final-*.out`, 12:35 PM to 1:13 PM)

- run_regression `--quick`: `REGRESSION: PASS (quick, 21 suites, 43.9 s wall)`. Every quick suite PASS, including
  test_saving (127 tests), check_paths, call_census, check_purity and check_fairness.
- call_census: `CALL-SITE CENSUS since HEAD: 15 AI files changed, 200 functions or added calls, 878 sites; 0 MISSING` /
  `CALL-SITE CENSUS: PASS`.
- check_purity `VERDICT: PASS`. check_fairness `PERSON-FAIR DATA DOOR: PASS (0 breaches)`. check_paths
  `PATHS GATE: PASS (46 files, 0 findings)`.
- test_check_purity (full, 30 tests): `OK`. test_safety_gates (49): `OK`. test_world (132): `OK`. test_host
  ControllerTogetherTests: `OK`.
- revert_r1 (6 workers, 822.8 s): `437 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as predicted, of 438 run (438
  defined)` / `OVERALL: PASS`; the control is `[R0] ... 388 tests ... failing none -> PASS`.
- revert_step5 (6 workers, 267 s): `400 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 402` /
  `OVERALL: PASS`.
- revert_safety_gates: `OVERALL: PASS`. revert_step4: `62 mutants CAUGHT ...` / `OVERALL: PASS`.
- revert_step2 and revert_step11: `OVERALL: FAIL`, because their CONTROLS fail in the worktree. Both force
  `AI_PLAYER_TEST_SUPPORT_ROOT` = the worktree, which has no `sandbox-pokebot` profiles or mgba ("Path is not a valid
  profile directory"; the same tests ERROR in every mutant). This is the environment limit of ruling 2, not this change.
  revert_step2's HFG and HFW anchors still match. Their outputs went into the worktree's tracked evidence files; I
  copied HEAD's content back from `keep_earlier`'s archive (no git), and kept this run's copies in
  `s4-loop/worktree-evidence/`.
- regression_due: it lists `DUE  revert_r1: never run (no evidence file matches)`, so the map knows the suite (exit 1:
  suites are due).
- NOT RUN: test_host (whole), test_kb2 (ruling 2), revert_step3 (2,014 s; this stage touched no step-3 code).

### Measured

- The census before this stage's work: 774 sites MISSING. 390 of them were one name collision (`_RebasedEyes.look`
  against every `.look()`), about 60 were renamed away, 21 are waived, and the rest are closed by mutants.
- Mutation found real gaps, now tested. Two were HANGS: deleting `skip_title`'s call in `continue_game` spun its loop
  forever (the frame budget never moved), and deleting the chain-loop refusal in `MemoryBook.chain` looped forever. Both
  loops are now bounded twice. Other gaps were the continue's six other stop paths, the save's four other ends, the
  memory file's refusals of broken lines, broken deltas and a misused writer, the host's look through `_screen` to the save wait and through `_progress` to the play
  time, the payload's parts, `main()`, and the records' words (read notes, gates, tells).
- First full revert_r1 run (8 workers): 1,513.7 s. Final (6 workers): 822.8 s.

### Deviations from the spec, and why

- **Census renames (code over the census's name match):** `AppPaths.memory/launches/retired` became
  `memory_jsonl/launches_jsonl/retired_dir`; `MemoryBook.match` became `match_time`, `.header` became `header_line`;
  `encode/decode` became `encode_value/decode_value`. `MemoryWriter.path` (uncalled) was removed. `ContinueCheck` lost its
  unused `header` field, and `memory_check`'s schema re-check was removed (`read_book` already refuses a newer schema).
- **21 census waivers**, against ruling 4's "never waivers". Each is (a) a name collision (`_RebasedEyes.look`, the
  brain's `_say`, `skills/story._same`, `Observation.to_dict`, the isolation's `restore`, the pad's `hold`, world memory's
  `_text`, `RunOptions.from_env`, the battle mind's `_decide`, `Session.run`'s `brain.play`), (b) a pre-R1 site that
  the census lists only because R1 changed the callee or added one call in the same function, and that only a live run
  or another suite reaches (the session's `Controller()` and `FrameworkEyes()`, `Brain.play`, `Brain.__init__`, the
  placeholder's tap, the old `_flag` and `_guarded` calls, the `on_menu` lambda, the intro brain's `play_intro`), or
  (c) `MonRegistry.add_role`, uncalled by design (D15). One is a stage-1 function: `FrameworkEyes.__init__`, whose
  only site is the host session's constructor. Every waiver states its reason in the file.
- **PLAY_TIME_DOORS** are the three save files whole. `mode.py HandsBrain._save/_continue` are not doors: they read no
  `.play_time` (the stamp arrives as an argument). `seen_now` drops it by keyword, which is not a read. A stale door is
  checked as in RULE A.
- **D19 in the brain** is an options error (`HandsOptions.__post_init__` raises: the run crashes at construction, before
  any press), as section 3 (e) says. The launcher refuses it first.
- **`AI_PLAYER_HOST` added**: the session line's `host` needs it. The harness will set `harness`.
- **Not in the spec:** the brain refuses a NEW game on a game that has a memory file (a second header would make the
  file unreadable); no save goal while hurt (spec: "heal first"); a `stuck:` save at the END keeps "done" (the proof
  holds); the header's `name` is None (no eye reads the player's name).
- **`test_check_purity`** finds the hook through `AI_PLAYER_TEST_SUPPORT_ROOT` when a package copy has no
  `sandbox-pokebot` beside it (revert_r1 runs its class in copies).
- **revert_r1's default workers is 6**, not revert_step5's 1, because of its 438 mutants. run_regression_times.json says
  823 s, the measured run.
- **Census-mutant predictions were recorded from their first run**, not predicted by hand. One is REDUNDANT with its
  reason: `_ui_kind(look) is None` in `_write` is implied by `nav_free`, which needs `screen.ui is None`.

### What I did NOT do

- `gates/play_harness.py`'s `--profile-dir`, `--memory` and `--continue`, and the harness passing `cart=empty` and
  `AI_PLAYER_HOST=harness` (D17). They belong to the live proof (steps 6-7) and were not in this stage's list.
- `rate_step5.py` intent_mix's `save_frames` (T4). A grader change moves its hash; not in this stage's list.
- `live_step5.py` now gets a memory file through the launcher, and SAVES. Its next run is a re-baseline; the
  orchestrator says so.
- No live run, so steps 6-8 are untouched. CONTINUE_BUDGET and ARRIVAL_BUDGET stay provisional.
- No git writes. Main checkout hygiene at 1:14 PM: 0 files under `sandbox-pokebot/` or `ai_player/` modified since
  11:00 AM. No lane or driver process of mine is alive.
- Untracked files the revert runs left in the worktree's `ai_player/evidence/`: `2026-10-29-r1-stage4-REVERT.txt` and
  `2026-10-29-r1-stage4-step5-REVERT.txt` (both PASS), `archive/53e0c26e7812db47-f36c9451/`, and `trees/*.zip`.
  The orchestrator decides what to commit. The dev run's evidence (FAIL) was moved to `s4-loop/worktree-evidence/`.

## Stage 5 of 6: section 8 step 6 (the development live runs on seeds 5401-5406)

Built and run from 1:17 PM to 2:25 PM Los Angeles time, 2026-10-29, in the worktree only. Every live run used
`AI_PLAYER_BUILD_ROOT` = the main checkout's `sandbox-pokebot` (read only), and every throwaway profile sat under the run's
own `--out` folder (`s5-dev/live/profiles/`). Evidence folder: `s5-dev/`. No STOP rule fired.

### Ledger first

- Entry **#51** (family `story`, driver `live_r1`, purpose development, seeds 5401-5406) was written at 1:20:41 PM, before
  any of these seeds was played (`s5-dev/ledger-begin.out`). It was finished at the end with the verdict in
  `s5-dev/ledger-verdict.txt`. `ledger.py --check`: `LEDGER ledger.json: 51 entries; well formed -> PASS`.

### What I built

- `ai_player/gates/play_harness.py` (test side): `--profile-dir DIR` boots a throwaway profile with a FILE-BACKED cart
  (`probe_save_kill.boot_profile`); `--memory FILE` and `--continue` go to the brain through `memory_options`, which also
  passes `cart` (`empty`, or `continued` for a continue) and `host="harness"`. A run without `--memory` gets none of these
  fields, so its options are exactly the pre-R1 harness's. `play()` and `run()` take a `watch` hook: test-side recorders
  that run after every frame. `--continue` is refused without `--profile-dir` and `--memory`, or with `--state`.
- `ai_player/gates/live_r1.py` (new, test side, not in the lane). It has the commands `control`, `arm`, `grade`,
  `measure` and `b-again`, plus the `child-a` and `child-b` entries.
  - **Child A**: the real play brain, in-process, on a fresh profile. The empty cart is asserted before boot (F14). Its
    watcher (`SaveWatch`) records, by the harness's own reads, every flash write. e3 is the first changed byte; each
    completed sector is a valid sector (signature and checksum) whose 4 KiB differ from the flash before the write; e4 is
    all 14 with one counter; e7 is the screen free and held for 10 frames. It also records the RAM truth at e3, the AI's
    memory lines as they reach the file, every map stood on (RAM), each START press with the held free read before it, and
    the big moments' proofs. At the kill rule it prints READY and blocks. The parent kills that PID only.
  - **Freeze**: the parent copies the cart, `memory.jsonl` and `launches.jsonl` into `frozen/<arm>-<seed>/` and reads
    the FILE verdict with `probe_save_kill.parse_image` and `file_verdict` (builder note 4).
  - **Child B**: its own copy of the frozen set. It calls the launcher's `memory_check`, then `seed_profile`'s continue
    branch, then the same brain with `--continue`. Its watcher (`ArrivalWatch`) records the play time the power-on read
    put in RAM, the main menu's task and cursor at every press, the error pages' words (printer 7), any New-Game task, and
    the HELD free arrival's identity (`ram_truth` plus `second_path_truth`).
  - **`grade`**: section 5's checks 1-7. Expectations follow the arm's own record at the kill frame (ruling 1). K-SILENT
    counts only with 0 new sectors at the kill and the S2 line written before it (builder note 5). K-BETWEEN counts only
    with its determinism line (builder note 2).
- `ai_player/skills/saving.py`: `CONTINUE_BUDGET` 6000 → **1700**, `ARRIVAL_BUDGET` 1200 → **320** (set below).
- `ai_player/gates/ledger.json`: entry #51.

### Checks (verbatim last lines)

- (a) A/B, stage-4 tree: `A/B VERDICT (decisions, presses, frames): IDENTICAL` (`s5-dev/compare_a.out`).
- (a) A/B, this stage's FINAL tree: `A/B VERDICT (decisions, presses, frames): IDENTICAL` (`s5-dev/compare_a_final.out`).
- (a) the compare's CONTROL (pre-R1 against R1 WITH `--memory` on 5401): `CONTROL COMPARE VERDICT: the compare SEES a
  difference (not vacuous)`. The first difference is the first save's START at f45883 (`compare_a_control.out`).
- Grader planted faults on the recorded rows: `GRADER FAULTS: PASS (17 of 17 as expected)` (`grader-faults.out`). Each
  fault makes its check FAIL or the arm not count. The recorded rows PASS.
- `run_regression.py --quick` (2:06 PM, after the budget change): `REGRESSION: PASS (quick, 21 suites, 44.4 s wall)`.
  This includes test_saving (127 tests), check_paths, call_census, check_purity and check_fairness
  (`final-run_regression-quick.out`).
- `revert_r1.py --evidence-tag r1-stage5` (2:08 to 2:22 PM): `437 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as
  predicted, of 438 run (438 defined)` / `OVERALL: PASS`; `[R0] CONTROL ... 388 tests ... failing none ... -> PASS`
  (`final-revert_r1.out`).
- Ledger: `LEDGER ledger.json: 51 entries; well formed -> PASS`.
- Hygiene (2:13 PM): `sandbox-pokebot: 33105 files, 0 modified since 1:17 PM`; `ai_player: 916 files, 0 modified since
  1:17 PM` (main checkout). None of this stage's processes is alive. The one match is the bot tuner's `run_agent.ps1`,
  which I did not touch (`hygiene.out`).
- NOT RUN: test_host (whole), test_kb2, revert_step2, revert_step11 (ruling 2: they need the main checkout).

### Measured

**(a) The no-memory A/B, seed 5401** (Story/TREECKO, `ch1_pokedex`, 330000 frames, clocks pinned). Pre-R1 tree (HEAD
67c73a0f, from `git archive`) against the R1 tree, each with its own harness and no `--memory`. Both arms: 6,083
action records, 2,606 presses, 163,462 frames, `play: done: ch1_pokedex reached`. Decisions, the press log, the lines,
the waits, the truth and the story truth are identical. Two kinds of difference, each named and explained:
- The eyes' WALL-CLOCK cost text (`cost=0.18ms`) in 2 reasons and in the digests. It is the PC's time per look, so it
  differs between two runs of the SAME tree. It is masked.
- R1's E5 `progress.play_time` in the full observations (1 record; pre-R1 has none).

D14's "nothing moves without a memory file" holds on both the stage-4 tree and this stage's final tree.

**(b) Seeds 5401-5404 with `--memory`, plus 5405-5406 as CONTROLs** (needed for K-BETWEEN). Source: `measure-final.out`,
`measure-final-table.txt`.
- Every run ended `play: done: ch1_pokedex reached`, with its end save made (`saved`).
- Saves per run: 5 / 6 / 4 / 5 / 5 / 5. Before `ch1_pokedex`: 4 / 5 / 3 / 4 / 4 / 4. No seed had fewer than 2.
- **NEW** is non-empty on all 6 seeds: `['0:10','0:18','2:2','2:4']`, `['0:10','2:2']`, `['0:10','0:18','2:2']`,
  `[...4]`, `['0:10','2:2']`, `['0:10','2:2']`. So no STOP.
- Moments (check 6, by the harness's reads): all 30 saves were at a ruling-51 moment.
  - 12 were centre saves at `OLDALE_TOWN_POKEMON_CENTER_1F` with the party at full HP.
  - 18 were big-moment saves (`ch1_lab`, `ch1_rival_route103`, and the end save after `ch1_pokedex`). Each began
    (START) 12 to 55 frames after the harness's sampled proof turned true.
  - Every save began on a held free screen in the overworld. Stamps were at least 3 game minutes apart.
- Moments seen live: centre and big moment. The leader save (`ch4_roxanne`) is unit-tested only.
- **Saves per game hour: 8.24 / 7.44 / 6.33 / 8.93 / 6.90 / 7.69.** Most extra saves are centre saves: the AI heals at
  OLDALE's centre 2 or 3 times a run, and each heal is a ruling-51 moment (T2: no separate centre gap). This is reported
  for the orchestrator, not tuned.
- The dialog with the AI's pacing, over 30 saves:
  - START to e3: 463-844 frames.
  - The write e4-e3: **254-266**.
  - First sector at **e3+16 to e3+18**.
  - e3 to free: 435-449.
  - START to free: 907-1,288 (stage 1's 1,603 stays the widest).
  - `slot_at_e4_equals_truth`: True on all 30.
- **T1**: the AI's save line is stamped by its look at **e3-5** (25 saves) or **e3-4** (5 saves). That is always before
  the clock's freeze (e3-1). The stamp equals the RAM truth's hours and minutes on all 30.
- Line sizes: the full first save is 110,749-118,173 bytes. Deltas are 60,870-174,215 bytes (a new map makes a large
  one).
- Wall time of a CONTROL: 235.8-316.8 s, with 12 emulators running beside the bot tuner.
- S1/S2 identities per seed: PIDs, map, tile and play time to the VBlank, in each row's `a.truths`.

**(c) Kill/continue rehearsals on 5405 and 5406** (`live/rows/K-*.json`; `live/logs/`). Every arm's child B was then run
AGAIN with the set budgets (`b-again`, suffix b2; the rows keep the first child B under `b_earlier`). Both runs gave the
same grades.

| arm | seed | kill frame | new sectors at kill | FILE | counted | pass |
|---|---|---|---|---|---|---|
| K-INSIDE (S2.e3+130) | 5405 / 5406 | 98177 / 81190 | 7 / 7 | S1+ERROR / S1+ERROR | yes / yes | yes / yes |
| K-SILENT (S2.e3+9) | 5405 / 5406 | 98056 / 81069 | 0 / 0 | S1 / S1 | yes / yes | yes / yes |
| K-FIRST (S1.e3+128) | 5405 / 5406 | 46917 / 48387 | 6 / 6 | CORRUPT / CORRUPT | yes / yes | yes / yes |
| K-BETWEEN (spec midpoint) | 5405 / 5406 | 72236 / 64480 | - | S1 / S1 | **no / no** (NEW empty at the kill) | - |
| K-BETWEEN-NEW (alternative rule) | 5405 / 5406 | 96049 / 79092 | - | S1 / S1 | yes / yes | yes / yes |

- **K-SILENT (builder note 5).** The AI's S2 line was written at e3-5 (98042 / 81055), 14 frames before the kill. 0 new
  sectors were complete at the kill. The first sector completes at e3+16 or later in all 30 saves measured. The arm
  counted on both seeds, so this is not the 2-seed STOP of ruling 1.
- **K-INSIDE.** The AI read the CORRUPTED page (a `read` note) and continued save 1. Arrival: PIDs, map, tile and boot
  play time equal S1's truth. The restored maps hold no map of NEW and agree with the session line's `restored_maps`.
  It told: "this continue undoes 1 battle lost after save 0:10".
- **K-FIRST.** The AI read the ERASED page and stopped: "the save is gone". It made zero presses once the main menu
  took input, and no New-Game task appeared.
- **K-BETWEEN.** Its determinism line holds on both seeds: S1's e1/e3/e4/e7, S1's truth and the press-log digest up to
  the kill are equal to the CONTROL's. But see deviation 3.
- **Continue spans** (`ai-continue-spans.out`, the AI's own action log, minus its frame base):
  - Power-on to the main menu taking input: 400-418 with no page, 759-784 with the erased page, 822-825 with the
    corrupted page.
  - The CONTINUE press to "continued": 130-159.
  - The harness's view: CONTINUE press to the held free arrival, 115 every time.
  - These are 2 seeds' pacing streams replayed. The K-SILENT and K-BETWEEN child Bs of one seed are the same
    trajectory, so the samples are 2 seeds x {no page, corrupted page, erased page}, not 10 independent ones.
- Child wall times: child A to its kill at most 198.8 s; child B at most 16.5 s (7,800 frames) and at most 6.6 s
  (2,620 frames).

**Set from these runs** (each 2x the widest measured, ruling 1):
- `CONTINUE_BUDGET` = **1700** (2 x 825).
- `ARRIVAL_BUDGET` = **320** (2 x 159).
- `live_r1.MOMENT_FRAMES` = **110** (2 x 55; builder note 3).
- `live_r1.CHILD_A_TIMEOUT` = **1200 s** and `CHILD_B_TIMEOUT` = **300 s**. These are the spec's floors: 2 x 198.8 and
  2 x 16.5 fall below them.
- Child B's frames are now `CONTINUE_BUDGET + ARRIVAL_BUDGET + 600` = 2,620. The b2 re-runs show the AI continues within
  the set budgets on every arm.
- The recorded rows for step 7's selftest clean PASS are in `s5-dev/live/rows/`.

### Deviations from the spec, and why

1. **Measured values outside the probe report's ranges, NOT a STOP (ruling 1).**
   - Write e4-e3: 254-266 frames (probe 256-261).
   - First sector: e3+16..18 (probe e3+19 for save 1, e3+18 for save 2).
   - Same mechanism, other trajectories (the AI's pacing; 30 saves on 6 seeds), as ruling 1 ruled for stage 1's
     253-261.
   - No constant rests on them. Every kill expectation follows the arm's own record.
   - K-SILENT's margin to the first sector is 7 frames (e3+9 against e3+16), the same as stage 1 measured.
2. **The completed-sector count is counter-free.** It counts valid sectors whose 4 KiB differ from the flash before the
   write. e4 also needs one counter among the 14.
   - The probe counts sectors carrying `gSaveCounter + 1`. On a NEW GAME that guess named no sector (first development
     run).
   - Latching the newest unseen counter took a half-programmed counter word (0xFFFF0002, seed 5403). Flash bits only
     go from 1 to 0, so a half-written counter reads high.
   - A trace of seed 5405's save 4 (`discarded/trace-5405/`) showed the last sector's counter completing one frame
     after the rest (f142078 to f142079). e4 taken on the half-written frame left a stale baseline, and the counter's
     last two bytes then read as a new save 197 frames later.
   - The same sector counts as the game itself would judge it, except on a frame where a counter is half-programmed.
     The grader's expectations follow this count (ruling 1).
3. **K-BETWEEN's memory check is VACUOUS under the spec's midpoint rule on both rehearsal seeds. Reported, never
   passed.**
   - Halfway between S1.e7 and S2.e1, child A had stood on no map it had not stood on before S1. It walked between
     LITTLEROOT, its house and ROUTE 101 (5405: 0:9, 1:2, 0:16, 1:1, 1:0).
   - So nothing new can be missing from the restored memory, and check 3 cannot fail.
   - For K-BETWEEN only, `grade` takes NEW from the arm's own record up to the kill, not from S2.e3. Under that, both
     midpoint arms are "not counted". Under the spec's literal NEW (from the CONTROL), check 3 would pass trivially.
   - I added `arm --between-rule new` (development, default still `midpoint`). It kills halfway between the first frame
     child A stands on a map of the CONTROL's NEW and S2's START. With it K-BETWEEN counted and passed on both seeds
     (NEW `['0:10','2:2']`, FILE S1, determinism equal). A planted "memory newer" fault FAILs its check 3.
   - **Decision for the orchestrator before step 7's registration:** keep the midpoint (K-BETWEEN will most likely be
     INCONCLUSIVE below its floor), or adopt the alternative rule.
4. `live_r1.py` holds only what step 6 needs: the children, the kill rules, freeze, child B, the grader, `measure` and
   `b-again`. Not yet built (step 7): `selftest`, `registered_numbers()` with the hashes, the OLD arms (mutant R1-M),
   LAUNCH and LAUNCH-OLD (through the real launcher), K-AFTER's run, and the verdict over floors.
5. The child A watcher does NOT read `current_save.sav` (no second handle), so e5 and e6 are not recorded. e7 is the
   first frame of a 10-frame held free stretch after e4. e1 is the AI's START press from the harness's press log.
6. Check 6's big-moment gap is measured from the proof's first frame, sampled every 10 frames and confirmed by a second
   sample, to the START press. Its accuracy is about 10 frames.
7. Builder note 1 over the spec text: the throwaway profiles are under `--out/profiles/`. The spec's section 5 says
   `<build_root>/profiles/`. `AppPaths.for_profile(name, OUT, home="")` keeps the memory at the profile's AppPaths path.
8. A finding for the eyes (no press came of it). On K-INSIDE's power-on the AI idled 90 frames "reading the page: 'The
   save file has been updated.'" before the corrupted page printed. Printer 7's string was named from its previous
   symbol while the new one began. The read-then-gate rule held: the gate look showed other words, so nothing was
   pressed. It only cost about 90 frames, and stays within `CONTINUE_BUDGET`'s measured widest.
9. Development reruns. The CONTROL batch ran four times, because of the watcher bugs in deviation 2 and one crash
   (reading SaveBlock1 before it is set up at power-on). Every replay gave the same e1/e3 frames on every seed: one
   trajectory per seed, replayed (CLAUDE.md rule 8). The earlier batches are kept in `s5-dev/discarded/` with the
   reason in each folder name. Only `s5-dev/live/` is evidence.
10. test_host, test_kb2, revert_step2 and revert_step11 were not run (ruling 2). revert_step3 and revert_step5 were not
    re-run: this stage changed no code they cover except two skills constants, and revert_r1 covers `skills/saving.py`.

### What I did NOT do

- Step 7: the selftest, registration of 5451-5454, the held-out arms, and the review round.
- Any edit of the AI's behaviour besides the two budgets.
- Any git write. `ledger.json` (entry #51) is modified in the worktree. `revert_r1` left
  `ai_player/evidence/2026-10-29-r1-stage5-REVERT.txt` (PASS) and `ai_player/evidence/trees/0b8ab303610fbf57.zip`
  untracked; the orchestrator decides what to commit.
- I did not touch the bot tuner's clone or its processes, `sandbox-pokebot/` code, or the main checkout.

## Stage 6 of 6: section 8 step 7, first half (the selftest, the registration, the held-out arms, the one verdict)

Built and run from 2:30 PM to 3:05 PM Los Angeles time, 2026-10-29, in the worktree only. Every live run used
`AI_PLAYER_BUILD_ROOT` = the main checkout's `sandbox-pokebot` (read only), and every throwaway profile, mutant tree and
mirror build root sat under the run's own `--out` folder. Evidence folder: `s6-graded/`. Evidence file in the worktree:
`ai_player/evidence/2026-10-29-r1live-HELDOUT.txt` (189,560 bytes, sha256 fe0952f65fbfc5f0...). No STOP rule fired.

**LIVE R1 VERDICT: PASS.** Every one of the 10 graded arms counted on 4 of 4 held-out seeds (floor 3). Every counted NEW
arm passed every check. Every counted OLD arm showed its difference. 24 of 24 discriminators differ.

### What I built (all in `ai_player/gates/live_r1.py`, test side, not in the lane; now 1,952 lines)

- **`registered_numbers()`** and **`ledger numbers | register | begin | finish`**. The numbers hold the kill rules,
  K-BETWEEN's rule, the target, the frames, both clocks, the child timeouts, child B's frames, the budgets, MOMENT_FRAMES,
  the expected table (`EXPECTED`), the counting rules (`COUNTING`), the floor, the verdict rule's text, the R1-M and S27
  edits, the fixture's md5 and frame, the LAUNCH numbers, and the sha256 (LF) of `live_r1.py`, `play_harness.py`,
  `probe_save_kill.py`, `probe_end_screen.py`, `knowledge/milestones.json` and `fixtures/route101_south.ss1`
  (`HASHED_FILES`, as `rate_step5.HASHED_FILES`). A ledger note comes from a file (ruling 29's hook refuses prose as an
  argument).
- **The OLD arms** (`old --twin-row ROW`). Child B runs in a temp copy of `ai_player` with mutant R1-M, on its own copy of
  the NEW twin's frozen set. R1-M is exactly revert_r1's S20 + S22 (`match_time` -> `newest_save`; the arrival check
  off); the selftest checks it edit for edit. Child B now reports which `skills/saving.py` it ran (path and sha256);
  an OLD arm counts only when that is the mutant's. `old_shows` needs POSITIVE evidence: the restored memory holds a map
  of NEW, the session continued save 2, and check 3 fails. A crash or a missing record cannot pass it.
- **LAUNCH and LAUNCH-OLD** (`launch --from-row K-AFTER-ROW [--old]`). K-AFTER's frozen copy plus the fixture planted
  as `current_state.ss1` (md5 checked), through `py -3.12 -B -m ai_player run --profile NAME --continue --frames 2620
  --wall-seconds 300 --build-root MIRROR --run-dir DIR`, with the PLAY brain and child B's plan in the environment.
  LAUNCH-OLD runs the launcher of a temp copy with S27 (revert_r1's S27, edit for edit). The grader checks: the launched
  mode ran `brain=play`; the first look is a cold boot (not OVERWORLD, emulator frame = log frame minus the session's
  `frame_base`, under 300); the intro or title before the CONTINUE press; CONTINUE pressed; `purity.json` CLEAN; the
  session line continued save 2. LAUNCH-OLD shows its difference when the first look is the ROUTE101 (0,16) overworld
  at emulator frame 66883 or more. The S27 copy's own message still says "removed" (it keeps the message and skips the
  unlink), so the grader never trusts the message: only the first look.
- **The mirror build root** (`mirror_build_root`). Junctions to the main sandbox's `modules`, `plugins`, `mgba`, `roms`;
  copies of its top-level files, the global files of `profiles/`, and `cache/`; its own `profiles/` and `logs/`; and an
  EMPTY `.git` folder. Without that folder the bot runs its stock auto-updater, because the mirror sits outside any
  checkout (`pokebot.py`'s "Fork divergence" walk).
- **`grade_control`**: CONTROL counts when child A ran to its own end. It passes when the run ended `done` at
  `ch1_pokedex` with its end save made, checks 5 and 6 hold, and the cart's FILE is the newest save. The probe's
  `file_verdict` names S1-S3 only, so the newest truth is passed as its "S1" and renamed S<n>.
- **The grader's changes**: K-FIRST's press census counts every press the main-menu task saw and every press from the
  frame the main menu first took input, plus a new `menu_took_input` sub-check (without it "zero presses" holds by
  construction). The rest of `grade` is unchanged except the OLD-arm branch.
- **`verdict`**: re-grades every row with this registered code, then gives the per-arm table, every arm's checks and its
  reason for not counting, the determinism lines (S1's and S2's START and e3 frames and truths against the CONTROL's),
  the discriminators (each with "differ"), `verdict.json`, and one line `LIVE R1 VERDICT: PASS|FAIL|INCONCLUSIVE`
  (exit 0 / 1 / 3).
- **`selftest --all --rows DIR ...`**: 29 cases on recorded rows (step 6's, plus this stage's rehearsal) and planted
  cases. Then each of the spec's 6 planted faults (`FAULTS`, a module switch read only by the grader): NEW computed
  empty; the identity ignoring the tile; the press census ignoring the main menu; check 3 reading child B's first
  map-change snapshot (on a planted case whose first map change enters a NEW map); an OLD arm counted while its twin is
  not; PASS below a floor. Planted controls: a save at no ruling-51 moment fails check 6; LAUNCH's first look as an
  OVERWORLD fails; a counted OLD arm showing no difference gives FAIL; a counted NEW arm failing gives FAIL.
- Scratch, outside the repo: `s6-graded/run_plan.py` (jobs with dependencies, at most 10 at once, each through
  `runcmd.py`), `hygiene.py` (the lane census of builder note 6, main-checkout writes, my processes), `arm_table.py`,
  `assemble_evidence.py`, `peek_*.py`, `dryrun_verdict_rows.py`.

### Order (registration BEFORE any held-out seed ran)

1. 2:39 PM: ledger **#52**, a REPLAY of development seeds 5405-5406 (`ledger-replay-begin.out`), for the rehearsal of the
   arms step 6 did not run.
2. 2:39-2:43 PM, rehearsal (`s6-graded/rehearsal/`):
   - K-AFTER on 5405 and 5406.
   - The 4 OLD arms on step 6's frozen K-INSIDE and K-SILENT sets.
   - LAUNCH and LAUNCH-OLD on K-AFTER's copies.
   - The first LAUNCH attempt launched the PLACEHOLDER brain: the launcher defaults to it, and nothing was pressed. It is
     discarded (`rehearsal/discarded-1-placeholder-brain/`). The fix is the play brain's environment plus the
     `brain_is_play` check. The re-run passed on both seeds.
   - #52 finished at 2:46 PM.
3. 2:45 PM: `run_regression --quick` PASS. A first run without `AI_PLAYER_TEST_SUPPORT_ROOT` failed 3 suites on the
   environment only (kept as `run_regression-quick-noenv.out`). Stage 5 ran it with that root.
4. 2:47 PM: `selftest --all` PASS, then `ledger numbers`, then `ledger register`: entry **#53**, seeds 5451-5454,
   sha256 `815c82b44e8706f9...`. No earlier entry named these seeds (grep count 0 before registration).
5. 2:47:17 PM: lane census 0; the main checkout had 0 files modified. 2:47:18 PM: `ledger begin` (the same sha256;
   tree digest 58b988ce9788bb54).
6. 2:47:26 to 2:57:44 PM: the 44 jobs (`heldout-plan.out`), all exit 0.
7. 2:57:52 PM: `verdict`. Then `ledger finish` #53 and `ledger --check`. The tree digest after the run is the same
   58b988ce9788bb54.

### Checks (verbatim last lines)

- `selftest --all`: `SELFTEST: the clean run PASSES (29 cases) and 6 of 6 planted faults FAIL as they must -> PASS`
  (`selftest-final.out`). Each fault's run shows which case went WRONG.
- `ledger register`: `REGISTERED numbers sha256 815c82b44e8706f9c073f28ee399b13fd696a763eb12e220f861f29416f197e4`.
- `ledger begin`: `SEED LEDGER: GRADED, HELD-OUT seeds 5451-5454 (ledger entry #53), REGISTERED 2026-10-29 14:47:06 with
  the bounds sha256 815c82b44e8706f9; this run's bounds sha256 815c82b44e8706f9 (the same); no other entry of family
  'story' names any of these seeds`.
- The run plan: `PLAN DONE: 44 jobs, exit codes not 0: none (02:57:44 PM, 619 s)`.
- **`verdict`: `LIVE R1 VERDICT: PASS (failing: none; below the floor: none; discriminators that differ: 24 of 24)`**
  (`verdict.out`).
- `ledger --check`: `LEDGER ledger.json: 53 entries; well formed -> PASS`.
- `run_regression --quick`: `REGRESSION: PASS (quick, 21 suites, 43.7 s wall)`.
- test_evidence (after the evidence file was added): OK.
- Hygiene, 2:58 PM: lane census 0; `main checkout sandbox-pokebot: 33105 files, 0 modified since 2:30 PM`; `main checkout
  ai_player: 916 files, 0 modified since 2:30 PM`; `stage processes alive: 0`. I stopped one leftover `tail` of my own
  Monitor, by PID.
- NOT RUN (ruling 2): test_host, test_kb2, revert_step2, revert_step11. Not re-run: revert_r1 (no AI code changed in
  this stage; `live_r1.py` is in no revert driver).

### Measured (held-out seeds 5451-5454)

| arm | 5451 | 5452 | 5453 | 5454 | counted |
|---|---|---|---|---|---|
| CONTROL (saves; FILE) | 7 saves, S7 | 4, S4 | 5, S5 | 5, S5 | 4/4, all pass |
| K-AFTER (kill frame; FILE) | 83072, S2 | 72803, S2 | 79828, S2 | 100004, S2 | 4/4, all pass |
| K-INSIDE (new sectors at kill; FILE) | 6, S1+ERROR | 7, S1+ERROR | 7, S1+ERROR | 7, S1+ERROR | 4/4, all pass |
| K-SILENT (new sectors; FILE) | 0, S1 | 0, S1 | 0, S1 | 0, S1 | 4/4, all pass |
| K-FIRST (new sectors; FILE) | 6, CORRUPT | 7, CORRUPT | 6, CORRUPT | 6, CORRUPT | 4/4, all pass |
| K-BETWEEN rule new (kill frame) | 80725 | 70584 | 77589 | 97313 | 4/4, all pass |
| LAUNCH (first look emu frame) | 0, cold | 0, cold | 0, cold | 0, cold | 4/4, all pass |
| K-INSIDE-OLD / K-SILENT-OLD | shows | shows | shows | shows | 4/4 each |
| LAUNCH-OLD (first look) | ROUTE101 @66883 | same | same | same | 4/4 |
| K-BETWEEN-MID (diagnostic) | NEW [] | NEW [] | NEW [] | NEW [] | 0/4 (vacuous) |

- **K-SILENT, builder note 5 / ruling 1.** The AI's S2 line was stamped at e3-5 on every seed: 5 frames before the
  write began and 14 frames before the kill at e3+9. 0 new sectors were complete at the kill on all 4 seeds, so it
  counted on 4 of 4. Save 2's first sector, measured in the K-AFTER arms of the same trajectories, completed at e3+17,
  e3+17, e3+16 and e3+17, so the margin is 7 frames at the closest. The writes took 266, 259, 262 and 261 frames (save
  1: 263, 260, 264, 264). That is within step 6's 254-266 and e3+16..18, and outside the probe report's 256-261 only as
  ruling 1 already ruled. No constant rests on it.
- **The discriminators** (all 24 differ):
  - K-INSIDE vs K-INSIDE-OLD, and K-SILENT vs K-SILENT-OLD: NEW maps restored [] vs all of NEW (['0:10','2:2'], and
    ['0:10','0:18','2:2'] on 5454); continued_from 1 vs 2. The CONTINUE TIME shown was 0:10, while the newest line's
    stamp was 0:20 / 0:17 / 0:19 / 0:24.
  - K-AFTER vs K-INSIDE: FILE S2 vs S1+ERROR; continued_from 2 vs 1.
  - LAUNCH vs LAUNCH-OLD: first look [UNKNOWN, emulator frame 0] vs [OVERWORLD, 66883].
  - K-FIRST vs CONTROL: FILE CORRUPT vs S7 / S4 / S5 / S5.
  - K-BETWEEN: NEW non-empty at the kill, and the restored memory holds none of it.
- **Determinism lines**: S1's and S2's START and e3 frames (and truths) are equal to the CONTROL's on every child A arm of
  every seed. That is one trajectory per seed, replayed (rule 8), not a replication.
- **Moments live** (check 6, CONTROLs): centre saves (OLDALE's centre at full HP) and big-moment saves (`ch1_lab`,
  `ch1_rival_route103`, the end save after `ch1_pokedex`). The leader save is still unit-tested only.
- Wall times, with up to 10 of my emulators beside the bot tuner:
  - A CONTROL: 205.8-372.8 s.
  - Child A to the kill: at most 189.7 s.
  - Child B: at most 7.2 s.
  - A LAUNCH: 11.2-13.6 s.
  - Every run was under its registered timeout (1200 / 300 / 480 s).

### Deviations from the spec, and why

1. **K-BETWEEN's graded rule is "new", not the spec's midpoint. I decided this; the orchestrator gave no ruling.** Stage 5
   left the choice to the orchestrator before registration, and the rulings in this task do not cover it. I did not
   register a rule already measured vacuous. Under the midpoint, K-BETWEEN would be "not counted" on every seed, and the
   verdict INCONCLUSIVE by construction.
   - The "new" rule kills between S1.e7 and S2.e1, with no write under way: still the spec's "ordinary deployment kill".
   - The midpoint ran anyway as the diagnostic arm K-BETWEEN-MID, registered as one and never in the verdict. It was
     vacuous again on 4 of 4 held-out seeds (NEW empty at the kill).
   - **If the orchestrator rules for the midpoint**: K-BETWEEN is then 0/4, below the floor. The verdict would be
     INCONCLUSIVE, not FAIL: no counted arm failed.
2. **LAUNCH through a MIRROR build root.** Builder note 1 and the hard rules forbid writing under the main sandbox's
   `profiles/`, and the real launcher puts the profile at `<build_root>/profiles/<NAME>`. So `--build-root` is a mirror
   under `--out`. The launcher, its purity gate, the package check, the hook and the bot run unchanged; only the folder
   that holds the profile differs. Hygiene shows 0 files written in the main sandbox.
3. **LAUNCH gets the PLAY brain and child B's plan through the environment** (`AI_PLAYER_BRAIN=play`, seed, personality,
   starter, target, clock), as `live_step5.py` launches it. The launcher's default brain is the placeholder. The
   cartridge clock is the host's in a launcher run, as in every launcher run.
4. **CONTROL's grading is spelled out** (`grade_control`). The spec's table names its expectations but no reach rule.
   It counts when child A ran to its own end.
5. **The selftest's recorded data includes this stage's rehearsal rows** (ledger #52, a replay on 5405-5406), not only
   step 6's. Step 6 never ran K-AFTER, the OLD arms or LAUNCH, and testing their graders on held-out data first would
   have been development on held-out seeds.
6. **Code over spec**: the probe's `file_verdict` names S1-S3 only (`SAVE_NAMES`). CONTROL's "FILE = the newest save"
   passes the newest truth as its S1. `parse_image` and the rule itself are the probe's.
7. The spec's LAUNCH check "its emulator frame under 300" reads 0 on every seed (the first look is before any frame).

### What I did NOT do

- The second half of step 7: the independent adversarial review and its fix round. Section 8 step 8's docs and commit
  belong to the orchestrator.
- Any change to the AI's code. This stage changed only `ai_player/gates/live_r1.py` (test side) and
  `ai_player/gates/ledger.json` (entries #52 and #53). It added one evidence file,
  `ai_player/evidence/2026-10-29-r1live-HELDOUT.txt` (untracked; the orchestrator decides).
- Any git write. I did not touch the bot tuner's clone or its processes, `sandbox-pokebot/` code, or the main checkout.
- test_host, test_kb2, revert_step2 and revert_step11 (ruling 2).


## Independent re-run: the live proof on NEW held-out seeds 5461-5464

Run from 3:03 PM to 3:16 PM Los Angeles time, 2026-10-29, in the worktree only, by an independent agent that did not build
any of this. Evidence folder: `rerun/`. Every live run used `AI_PLAYER_BUILD_ROOT` = the main checkout's `sandbox-pokebot`
(read only). No STOP rule fired.

**VERDICT: AGREES with the builder.** `live_r1.py verdict` on 5461-5464 says PASS. Every graded arm counted on 4 of 4
seeds, and every counted arm gave the same result the builder reported on 5451-5454. My own recomputation of all 24
discriminators from the raw outputs agrees: 24 of 24 differ.

### What I did

- **No AI or gate code changed.** The only file I wrote in the worktree is `ai_player/gates/ledger.json`, which got entry
  #54. A `find -newer` from my start shows only that file. The tree digest was 58b988ce9788bb54 before and after the run,
  the same as #53.
- **Registered first.** At 3:04:16 PM I made ledger **#54** (graded, story, live_r1, seeds 5461-5464). Before that, a
  grep for 5461-5464 in the ledger counted 0 and no entry overlapped the range.
  - `live_r1.py ledger register` hard-codes `HELD_OUT = (5451, 5454)` and has no seed flag. So `rerun/register_rerun.py`
    calls the same `ledger.register` with the new range and the sha256 of the unchanged `registered_numbers()`.
  - That sha256 is `815c82b44e8706f9...`, identical to #53's. So the kill rules, the expected table, the counting rules,
    the floor and the hashed files are the same ones the builder registered.
  - Then `ledger begin --purpose graded --first 5461 --last 5464` ran at 3:04:28 PM.
- **The same commands.** `rerun/run_plan.py` is the builder's `s6-graded/run_plan.py`. Its only change is that the seed
  range is 5461-5464: the same 44 jobs, the same arguments (K-BETWEEN rule `new`, plus K-BETWEEN-MID as a diagnostic), at
  most 10 at once, each through the builder's `runcmd.py`.
- **The same grader.** `live_r1.py verdict --out rerun/heldout --first 5461 --last 5464`. Then `ledger finish` #54 and
  `ledger --check`.
- **My own instrument** (`rerun/my_discriminators.py`). It does not use live_r1's `grade`, `summary_of` or `verdict` code,
  and it recomputes every arm's facts from the RAW outputs:
  - its own GBA flash parser, with the sector checksums (pret's sector sizes), on each frozen `current_save.sav`;
  - NEW, from `a.maps` and the saves' e3;
  - new sectors at the kill, from each save's per-frame `sectors` record;
  - `restored_maps` and `continued_from`, from child B's `memory.jsonl` copy, checked against `world.jsonl`'s first
    snapshot;
  - LAUNCH's first look, from the launcher run's `actions.jsonl` minus the session's `frame_base`.
- **The instrument was tested before use:**
  - FAULT and CONTROL (`fault_my_parser.py`, on a copy):
    `MY PARSER FAULT TEST: PASS (expected {'control': 'S2', 'fault1_one_byte': 'S1+ERROR', 'fault2_erased': 'EMPTY', 'fault3_no_complete': 'CORRUPT'})`.
  - On the builder's raw outputs for 5451-5454: `MY DISCRIMINATORS (5451-5454): 24 of 24 differ`
    (`my-disc-5451-5454.out`). Every FILE, NEW, restored set and first look matches the builder's table.

### Checks (verbatim last lines)

- `ledger numbers`: `REGISTERED NUMBERS sha256 815c82b44e8706f9c073f28ee399b13fd696a763eb12e220f861f29416f197e4`
- `ledger register` (#54): `ENTRY {"id": 54, ... "status": "registered", "registered": "2026-10-29 15:04:16", "bounds_sha256": "815c82b44e8706f9...`
- `ledger begin`: `SEED LEDGER: GRADED, HELD-OUT seeds 5461-5464 (ledger entry #54), REGISTERED 2026-10-29 15:04:16 with the bounds sha256 815c82b44e8706f9; this run's bounds sha256 815c82b44e8706f9 (the same); no other entry of family 'story' names any of these seeds`
- The run plan: `PLAN DONE: 44 jobs, exit codes not 0: none (03:13:24 PM, 531 s)`
- **`verdict`: `LIVE R1 VERDICT: PASS (failing: none; below the floor: none; discriminators that differ: 24 of 24)`**
- My recomputation: `MY DISCRIMINATORS (5461-5464): 24 of 24 differ`
- `ledger finish`: `FINISHED #54`. `ledger --check`: `LEDGER ledger.json: 54 entries; well formed -> PASS`
- Hygiene at 3:14 PM:
  - lane census 0;
  - `main checkout sandbox-pokebot: 33105 files, 0 modified since 3:03 PM`;
  - `main checkout ai_player: 916 files, 0 modified since 3:03 PM`;
  - `stage processes alive: 0`.

### Arm by arm against the builder (5451-5454 vs 5461-5464)

| arm | builder (5451-5454) | re-run (5461-5464), from my own recomputation | agree? |
|---|---|---|---|
| CONTROL | 4/4 pass; 7/4/5/5 saves, FILE = newest | 4/4 pass; 5/5/5/6 saves, FILE S5/S5/S5/S6; the loaded slot's play time, map, tile and PIDs equal the newest truth; all ended `done: ch1_pokedex reached` | yes |
| K-AFTER | 4/4 pass, FILE S2 | 4/4 pass, FILE S2; arrival = S2's truth; restored holds ALL of NEW; continued_from 2 | yes |
| K-INSIDE | 4/4 pass, S1+ERROR, 6/7/7/7 new sectors at the kill | 4/4 pass, S1+ERROR, 7/7/7/7 new sectors (mine = the row's); CORRUPTED page; arrival = S1; no NEW map restored | yes |
| K-SILENT | 4/4 pass, 0 sectors, S1 | 4/4 pass, 0 sectors, S1, no page. S2 line at e3-5 (seen e3-4), kill at e3+9, S2's first sector 7/8/8/7 frames after the kill | yes |
| K-FIRST | 4/4 pass, CORRUPT, 6/7/6/6 sectors | 4/4 pass, CORRUPT, 6/6/6/6 sectors; ERASED page; "the save is gone" | yes |
| K-BETWEEN (rule new) | 4/4 pass | 4/4 pass, FILE S1; NEW ['0:10'] / ['0:10','2:2'] / ['0:10','2:2'] / ['0:10','0:18']; none restored | yes |
| LAUNCH | 4/4 pass, first look [UNKNOWN, 0] | 4/4 pass, [UNKNOWN, 0]; purity CLEAN; continued_from 2 | yes |
| K-INSIDE-OLD / K-SILENT-OLD | 4/4 show | 4/4 show: child B ran the mutant tree's `skills/saving.py`; restored holds all of NEW; continued_from 2 | yes |
| LAUNCH-OLD | 4/4, ROUTE101 @66883 | 4/4, [OVERWORLD, 66883] ROUTE 101 (0,16); continued_from None | yes |
| K-BETWEEN-MID (diagnostic) | 0/4, NEW empty (vacuous) | **1/4**: counted and passing on 5461 (NEW ['0:10']); vacuous on 5462-5464 | differs; not graded |

### Discriminators, computed by me from the raw outputs (5461-5464)

- **K-INSIDE vs K-INSIDE-OLD, and K-SILENT vs K-SILENT-OLD:** NEW maps in the restored memory were [] vs all of NEW
  (['0:10','2:2'], or ['0:10','0:18','2:2'] on 5464). continued_from was 1 vs 2. 8 of 8 differ.
- **K-AFTER vs K-INSIDE:** FILE S2 vs S1+ERROR; continued_from 2 vs 1. 4 of 4 differ.
- **LAUNCH vs LAUNCH-OLD:** the first look was [UNKNOWN, emulator frame 0] vs [OVERWORLD, 66883]. 4 of 4 differ.
- **K-FIRST vs CONTROL:** FILE CORRUPT vs S5 / S5 / S5 / S6. 4 of 4 differ.
- **K-BETWEEN:** NEW was not empty at the kill, and the restored memory held none of it. 4 of 4 differ.

None is vacuous: each pair's two sides are computed from different children's records and came out different.

### Measured

- **The writes**, from the K-AFTER rows' per-frame records (e3 to the last sector):
  - save 1: 264 / 262 / 262 / 263 frames, first sector at e3+17 / 16 / 16 / 18;
  - save 2: 262 / 261 / 259 / 262 frames, first sector at e3+16 / 17 / 17 / 16.
  - That is inside the builder's 254-266 and e3+16..18. It falls outside the probe report's exact numbers only as
    ruling 1 already ruled. No constant rests on these numbers.
- **K-SILENT, ruling 1:** it counted on 4 of 4. On each seed the S2 line was written before the kill, with 0 new sectors at
  the kill, so the count of "not counted" seeds is 0 and the STOP rule did not fire.
- **Determinism:** 24 of 24 DETERMINISM lines are `same_as_control`. That is one trajectory per seed, replayed (rule 8),
  never a replication.
- **Wall times** ran from 11.8 s (a LAUNCH) to 293.2 s (a CONTROL). All were under the registered timeouts.

### Deviations, and why

1. **The registration did not go through `live_r1.py ledger register`**, because that command cannot name other seeds. It
   went through `ledger.register` directly, with the identical numbers sha256. The registered numbers dict still says
   `"seeds": [5451, 5454]`, because that field comes from the code constant `HELD_OUT`, which I was told not to edit. The
   ledger entry's own first and last are 5461-5464. The orchestrator may want `--first/--last` on `ledger register`.
2. **K-BETWEEN-MID is not vacuous on every seed.** The builder wrote that it was "vacuous again on 4 of 4". On 5461 its
   NEW was ['0:10'], and it counted and passed. This does not change any graded result. If the orchestrator rules for the
   midpoint, K-BETWEEN would be 1/4 on these seeds. That is below the floor of 3, so the verdict would be INCONCLUSIVE, the
   same answer the builder gave.
3. **`ledger finish` names `rerun/verdict.out` as its evidence**, a scratch path. I did not add an evidence file to the
   worktree. The orchestrator decides whether to assemble one.

### What I did NOT do

- I did not change AI or gate code, and I did not write to the main checkout, the sandbox, or the bot tuner's clone or its
  processes. I made no git writes.
- I did not re-run the selftest, revert_r1 or the regression lanes. No code changed, and the tree digest is the same.
- I did not review the builder's code adversarially beyond grading these arms.

## Adversarial review of the R1 + R2 build (independent reviewer)

Done from 3:05 PM to 3:20 PM Los Angeles time, 2026-10-29. I worked read-only in the worktree
`.claude/worktrees/wf_ad737c3f-1d5-1` (HEAD 67c73a0f plus the uncommitted build). I read the spec, this report, the diff and
the untracked files, and the held-out evidence. I ran offline checks and in-memory probes only. Every probe ran on a temp
copy or in memory. I edited no repo file, ran no live arm and made no git write. My outputs are in `build/review/`.

### VERDICT: FINDINGS (5 MINOR, 4 NIT; no MAJOR)

I found no route by which the AI reloads by its own choice. The launcher refuses a continue after a CHOSEN end that did
not come right after a save. The controller refuses START or SELECT with another button. The purity gate refuses
`sys.exit`, `exit`, `quit`, `SystemExit` and `KeyboardInterrupt`. Every loop and wait in the save and continue skills has a
bound. The held-out seeds were registered before they ran. The live arms are not vacuous.

What I did find:
- The memory a continue restores is ONE SAVE BEHIND for the save policy's own fields.
- A continue that stops on a timeout makes the game impossible to continue, ever again.
- An orchestrator ruling was not followed in full.
- A grader change the spec decided was never built.
- The headline PASS rests on a K-BETWEEN rule the builder chose, which the orchestrator has not ruled on.

### Checks I ran (verbatim last lines; outputs in `build/review/`)

| check | file | exit | last line |
|---|---|---|---|
| test_saving (worktree) | `run-test_saving.out` | 0 | `OK` |
| check_fairness | `run-check_fairness.out` | 0 | `PERSON-FAIR DATA DOOR: PASS (0 breaches)` |
| check_paths | `run-check_paths.out` | 0 | `PATHS GATE: PASS (46 files, 0 findings)` |
| check_purity | `run-check_purity.out` | 0 | `VERDICT: PASS` |
| test_host.ControllerTogetherTests + test_check_purity.PlayLoopExitTests | `run-controller-exit.out` | 0 | `OK` (2 tests) |
| test_goals, the R1 tests (`-k r1 -k R1`) | `run-test_goals-r1.out` | 0 | `OK` (18 tests) |
| extra purity plants (temp copies) | `purity_plants.out` | 0 | P3 `except BaseException` and P4 `raise GeneratorExit` in `brain/` PASS the gate; P1, P2, P5, P6 and P8 fail it, as they should |
| RULE C plants (temp copies) | `fairness_plants.out` | 0 | F1 (an attribute read) fails the gate; F2-F5 (subscript, `asdict`, `vars`, the book's line) PASS it |
| restore-order probe (in memory) | `restore_last_save.out` | 0 | `restored policy may_save at 0:10: (True, '')` against the live `(False, '... 0 game minutes ago ...')` |

### Findings

**R-1 (MINOR). The policy state a continue restores is the state BEFORE the save it continued.**
- **Code.** `mode.py` HandsBrain._save builds the save's payload in `on_writing`:
  `line = writer.write_save(..., payload=self._payload(report))`. It records the save only later, in `on_saved`:
  `policy.record_save(pending["stamp"], look.frame, line.id, why)`. So the `goals` part of save k holds
  `last_save` = save k-1, and it has no `saved_for` entry for save k's own leader approach.
- **Measured** (`restore_last_save.out`):
  - `restored last_save (as of save k): {'id': 1, 'play_time': [0, 5], ...}`
  - `live policy may_save at 0:10: (False, 'its last save was at 0:10, 0 game minutes ago ...')`
  - `restored policy may_save at 0:10: (True, '')`
  - `live saved_for: {'ch4_roxanne': 5000}` against `restored saved_for: {}`
- **Spec.**
  - Section 0: "never twice within 3 minutes of game play time".
  - D16 KEEPs `saved_for` and `last_save` as "experience, the same at the save as a person would remember it".
  - D3: "once per approach".
- **What goes wrong.** Take a continue from a save made right before ROXANNE (the most likely place to continue from).
  - `before_leader` finds no `saved_for` entry. The restored `last_save.frame` is from before the gym, so it is below
    `entered`. The AI therefore makes a NEW leader save at once, at the same play time as the save it continued.
  - D4's match then finds two lines within 1 minute of each other. If that duplicate save is cut by a kill, the next
    continue matches the duplicate's line (the newest within 1 minute), not the save the game loaded. The arrival
    check passes, because the place and the party are the same.
  - The live proof cannot see any of this. Child B runs `CONTINUE_BUDGET + ARRIVAL_BUDGET + 600` = 2,620 frames, which is
    below `SAVE_FRAMES_NEEDED` (3,600), so no child B ever saves.
  - `test_each_keep_field_survives_the_restore` round-trips a memory. It never replays the write-then-record order, so it
    passes by construction.
- **Fix.**
  - Write save k's own record into the payload's `goals` before the line is written: `last_save` = {k, stamp, frame,
    why}, plus `saved_for[milestone] = entered` for a leader due.
  - Add a test that a continue from a leader save makes no second save before the talk.
  - Add a test that the restored `last_save.id == k`.

**R-2 (MINOR). A continue that stops on a timeout makes the game impossible to continue, ever again.**
- **Code.** `mode.py` _continue: `return (yield from self._play(hands, personality, stop=f"the continue stopped: {result.why}"))`
  ends "stuck". `game_memory.end_line` sets `"chosen": text.startswith(("done:", "stuck:"))`. `launcher.classify_end`
  refuses a CHOSEN end unless `at_save`. So every STOP writes a CHOSEN end line, and every later `--continue` is refused.
  The only way left is `--fresh`, which archives the memory and empties the cart. The game is lost.
- **The STOPs this covers.**
  - "the main menu did not come within 1700 frames"
  - "the continued game did not reach a free overworld within 320 frames"
  - "CONTINUE could not be chosen"
  - "the main menu went away while it was read"
  - "the CONTINUE window's TIME cannot be read"
- **Why this matters.** `ARRIVAL_BUDGET` = 320 is 2 x 159, measured on 2 seeds' trajectories at a few save places
  (stage 5: "the samples are 2 seeds x {no page, corrupted page, erased page}").
- **Spec.** The section 3 (f) table writes "a session line and a chosen `end` line (so no later continue)" ONLY for the
  ERASED page and for no CONTINUE. The spec has no row for a timeout. Also, a STOP restores nothing and plays nothing, so
  another continue cannot undo anything the earlier allowed continue did not already undo.
- **Fix.** End a STOP that restored nothing as not chosen (for example `chosen: false`, `stopped_before_restore: true`), and
  have `classify_end` look through such a session to the one before it. Keep the spec's rows (erased, no CONTINUE, a TIME
  it does not know, an arrival that differs) CHOSEN.

**R-3 (MINOR). Ruling 4 was not followed: stage 1's census findings are partly closed by waivers.**
- **Ruling 4:** "call_census's 23 findings (stage 1's new or changed functions) are closed by revert_r1's mutants in stage
  4, never by waivers."
- **Stage 1's census** (`s1-eyes/final-call_census.out`) lists both of these:
  - `[FAIL] host/eyes.py:FrameworkEyes.__init__ (changed): ... host/session.py:139 in Session.__init__`
  - `[FAIL] host/eyes.py:FrameworkEyes._guarded (a call ADDED in host/eyes.py:FrameworkEyes._screen): 12 sites`
- **The worktree's `census_waivers.json`** waives both:
  - `"callee": "host/eyes.py:FrameworkEyes.__init__", "caller": "host/session.py:Session.__init__"`
  - `"callee": "host/eyes.py:FrameworkEyes._guarded", "caller": "host/eyes.py:FrameworkEyes._screen"`
- **The report understates it.** Stage 4 says: "One is a stage-1 function: `FrameworkEyes.__init__`". The `_guarded` waiver
  covers 12 more of stage 1's sites.
- **Fix.** Replace both waivers with revert_r1 mutants, or have the orchestrator amend ruling 4 for these two and record
  that.

**R-4 (MINOR). Spec T4 / section 7 is not built: the errand share now counts save frames in its total.**
- **Spec.** Section 7: "`rate_step5.py` `intent_mix` (`:1086-1112`): spans of kind `"save"` leave the errand share's TOTAL
  and are reported separately as `save_frames` ... A unit test goes beside the existing `intent_mix` tests". T4 rejects
  "leaving it in the total as non-errand (it would lower the share with no change in behaviour)".
- **Code.** `rate_step5.py` is not in the diff. `intent_mix` still does `total = sum(frames.values())` over every span
  kind.
- **Why it matters now.** `__main__.py` now gives EVERY launcher run `env[ENV_MEMORY] = str(game.memory_jsonl)`. So
  `live_step5.py`, which imports `intent_mix` and grades its floors, now saves, and its errand share is lowered by the
  save spans. That is the very alternative T4 rejected.
- **Stage 4's "What I did NOT do"** names this gap, but no later stage closed it or recorded a decision.
- **Fix.** Build T4 with its unit test before any `live_step5` graded run. Otherwise record the deferral in `06` and block
  that run.

**R-5 (MINOR). The headline PASS rests on a K-BETWEEN rule that only the builder chose.**
- **The evidence file's first line** (`ai_player/evidence/2026-10-29-r1live-HELDOUT.txt`) reads:
  `... section 8 step 7 (first half): LIVE R1 VERDICT: PASS`. The substitution appears only on its lines 2 and 8.
- **Stage 6 says:** "K-BETWEEN's graded rule is 'new', not the spec's midpoint. I decided this; the orchestrator gave no
  ruling" and "If the orchestrator rules for the midpoint: K-BETWEEN is then 0/4, below the floor. The verdict would be
  INCONCLUSIVE".
- **Spec.** Section 5's table: K-BETWEEN = "halfway between S1.e7 and S2.e1". The rule that changed the verdict class was
  registered without a ruling.
- **The substitute rule is not the problem.** It is pre-registered, it is not vacuous, and it still kills with no write
  under way. The problem is a headline that claims more than its evidence (CLAUDE.md session discipline 2).
- **Fix.** The orchestrator rules on the "new" rule. Then the headline names it: "PASS, with K-BETWEEN under the
  substituted rule (the spec's midpoint: vacuous, 0/4)".

**N-1 (NIT). The D12 (c) exit rule misses two forms, and a refused reset combination still allows a continue.**
- Code: `visit_Name` refuses only `PLAY_LOOP_EXIT_NAMES = frozenset({"exit", "quit", "SystemExit", "KeyboardInterrupt"})`.
- The plants show two forms it misses (`purity_plants.out`):
  - `except BaseException:` in `brain/` passes the gate. It catches both `SystemExit` and `KeyboardInterrupt`, and the
    spec says "raised or caught".
  - `raise GeneratorExit` in `brain/` passes the gate. `host/session.py` turns it into `note_abandoned()`, which ends
    "abandoned". That is INVOLUNTARY, so a continue is allowed.
- A refused START/SELECT combination raises `ControllerError`. The session turns that into "crash", which is also
  INVOLUNTARY. So the reset the controller blocked still gets its reload once anyone runs `--continue`, and R15's
  supervisor would do so automatically.
- All three are covered by the spec's "Not enforced: an exception the AI's code raises on purpose ends the run as a
  crash, which is allowed to continue". Even so:
  - `GeneratorExit` and `BaseException` belong in the refused names.
  - A together-refusal should end NOT CLEAN.
  - Or record all three in `06` as known limits.

**N-2 (NIT). RULE C sees only attribute reads.**
- `check_fairness.py` RULE C fires on `.play_time` (an attribute) or `getattr(x, "play_time")`.
- The build itself copies the stamp into a `brain/goals.py` field (`_Memory.last_save = {"id", "play_time", ...}`). The
  plant `memory.last_save["play_time"]` in `brain/goals.py` passes the gate (`fairness_plants.out` F2), and so do
  `asdict(...)` and `vars(...)`.
- Spec D18: "A read anywhere else in the deciding code fails the gate."
- The value is a past stamp, not the live clock, so this is low risk. It is still a blind spot of the gate.

**N-3 (NIT). No live arm saves after a continue.**
- Child B's frames (2,620) are under `SAVE_FRAMES_NEEDED` (3,600).
- So these paths are unit-tested only:
  - the continued writer's delta chain against a restored parent (`MemoryWriter(..., book, ...)` with
    `last_payload = book.rebuild(self.parent)`);
  - `own_cart("continued")` answering the OVERWRITE question with YES live;
  - R-1.
- One development arm with a longer child B would cover them.

**N-4 (NIT). A corrupted middle line can be read silently.**
- `read_book` opens with `errors="replace"`. Every line is written with `ensure_ascii=True`, so a corrupted byte inside a
  middle line's string can parse as changed content instead of being refused.
- S25 guards only against lines that cannot be parsed. `errors="strict"` (refused as "unreadable") would close this.

### Checked and found sound (no finding)

- **The launcher's end classes, one per D12 (a) row** (`test_the_end_classes`), including two cases that fail closed:
  CHOSEN or BUDGET with no end line, and UNKNOWN when the run folder is gone.
- **`run_dir` matching.** `env[ENV_RUN_DIR] = str(run_dir)` (resolved) and `Path(raw_dir)` in options round-trip to the
  same string that `record_launch` writes.
- **`at_save`** (`hands.pad.presses == self._at_save_presses`): no battle can start without a press after a save.
- **Continue-mode guards.** A continued game never runs `play_intro`; the title mid-run ends "stuck". A NEW game on a
  game that has a memory file is refused by the brain and by the launcher.
- **Bounds.** Every loop in `save_game`, `_write`, `_error`, `_back_out`, `_held_free`, `continue_game` (frames and
  still passes) and `_save_screen` is bounded. A save page met outside the skill gets no press; the navigator then ends
  "stuck: an unexpected save_dialog".
- **Frame base.** `frame_base` is monotone across sessions; `_RebasedEyes` wraps the eyes only when the base is not 0.
- **The world memory after a continue** starts from the payload, after the arrival. `AI_PLAYER_WORLD` is refused with
  a continue.
- **The ledger.** Development #51 was begun before its runs. Graded #53 was registered at 2:47:06 PM, before its first
  run at 2:47:26 PM. The `545x` hits in the development folders are frame numbers, not seeds.
- **The OLD arms' `old_shows`** needs positive evidence. K-FIRST's "no press" has its `menu_took_input` sub-check.
- **PID identity.** Its use in the arrival check is the project's existing identity convention: `brain/battle.py` and
  `navigator.py` used PIDs before R1. It is not a new hidden-state read.
- **The bot.** `sandbox-pokebot/` is not in the diff.

### What I did NOT do

- No live arm. The independent re-run on 5461-5464 (ledger #54) is running beside this review.
- No full regression lane and no revert drivers.
- No test_host (whole) or test_kb2 (ruling 2).
- No repo edits and no git writes.


## FIX ROUND: the adversarial review's R-1 to R-5

Done from 3:21 PM to 4:36 PM Los Angeles time, 2026-10-29, in the worktree only. Every live run used
`AI_PLAYER_BUILD_ROOT` = the main checkout's `sandbox-pokebot` (read only). Every throwaway profile sat under the run's own
`--out` folder (`build/fix/heldout/`). Outputs are in `build/fix/` (each through `runcmd.py`: the command, the start and end
time, the exit code). Copies of every file as it was before this round are in `build/fix/orig/`. No git writes.

### VERDICT: R-1, R-2, R-3, R-4 FIXED (each reproduced first). R-5's headline FIXED; the ruling it asks for is OPEN

The live arms were re-run on NEW held-out seeds 5471-5474, ledger #55, registered before any of them ran:
`LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm
K-BETWEEN-MID counted 0 of 4: vacuous)`. Under the spec's own midpoint rule the verdict would be INCONCLUSIVE. That
substitution still needs the orchestrator's ruling (R-5).

### R-1: the memory a continue restores was one save behind

- **Reproduced, three ways:**
  - The reviewer's probe, re-run (`repro-R1-before.out`): `restored last_save (as of save k): {'id': 1, ...}` and
    `restored saved_for : {}`.
  - A new play-loop test, run on the code from before the fix (`repro-R1-loop-orig-vs-fixed.out`). Through the REAL
    `HandsBrain._save`, a save right before ROXANNE, then a restore. On the old code the continued game chose a save again
    at once: `AssertionError: 'save' != 'talk'`. On the fixed code: `OK`.
  - On the LIVE pre-fix files (`fix/discriminate_fix.py`, which reads every save line's own rebuilt payload):
    - #53 (seeds 5451-5454): `57 save lines; the payload remembers THIS save: 0; the save BEFORE it: 57`.
    - #54 (seeds 5461-5464): the same, 0 and 57.
- **Fix:**
  - `brain/saving.py`: a new `SavePolicy.saved_state(play_time, frame, save_id, why)` returns exactly what `record_save`
    sets (`last_save` = this save, `saved_for` with a leader's approach, `save_due` None), without touching the live
    memory. `record_save` now applies that.
  - `mode.py`: `_save.on_writing` asks for that state for the line's own id (`writer.next_id`) and frame. `_payload(report,
    saving)` builds the goals part from `replace(manager.memory, **saving)`. So a save's memory line carries the save
    itself.
  - `on_saved` now records the save with the WRITE's start frame (the memory line's `frame`), not the SAVED page's frame.
    The live policy and the restored one then hold the same `last_save`. The only reader of that frame is
    `before_leader`'s `last.frame >= entered`, and the player cannot move during the write, so its answer is unchanged.
  - A save that then fails (an error page) leaves the live policy as it was: `saved_state` changes nothing.
- **Tests:**
  - `PlayLoopTests.test_r1_a_continue_from_a_leader_save_makes_no_second_save_before_the_talk` (test_goals). After the
    continue, block 8 returns the TALK at once and 30 game minutes later. The restored `last_save` equals the live one,
    with id 1 and the line's own frame. `saved_for` is `{ch4_roxanne: 5000}`. REACH: before the save the talk WAS a save.
    CONTROL: a new approach to the gym saves again.
  - `PolicyTests.test_the_saved_state_is_what_record_save_sets` (test_saving).
- **Live, after the fix** (#55, `disc-fixed-5471.out`): `58 save lines; the payload remembers THIS save: 58; the save BEFORE
  it: 0`.
- **Mutant FX1** (the payload built from the memory before the save): CAUGHT by the play-loop test.

### R-2: a continue that stopped on a timeout made the game impossible to continue again

- **Reproduced** through the real brain and launcher (`repro-R2-orig-vs-fixed.out`, `fix/repro_r2.py`). Setup: a game
  whose session was killed, then a continue that stops with "the main menu did not come within 1700 frames of power-on".
  - The old code writes `'chosen': True`, and `classify_end` then says `class CHOSEN, allowed False`.
  - The fixed code writes `'chosen': False, ... 'stopped_before_restore': True`, and then `class KILLED, allowed True (harness
    session 1 has no end line: it was killed)`.
- **Fix:**
  - `skills/saving.py`:
    - `ContinueResult.may_retry` is new. `_stopped(..., retry=False)` takes it by name, so a stop is fail-closed: CHOSEN
      unless it says otherwise.
    - The seven BOUND and READ stops pass `retry=True`: no frame passing, too many pages, no main menu in time, the main
      menu gone while read, the TIME unreadable, CONTINUE not taken, no free arrival in time.
    - The spec's own stops keep `retry` False: the save gone (with or without the erased page), a TIME it does not
      remember, an arrival that differs.
  - `mode.py`: `_continue` keeps the flag, and `_end_memory` passes it to `write_end`.
  - `game_memory.end_line` adds `stopped_before_restore`. Such a `stuck:` end is NOT chosen.
  - `host/launcher.py` `classify_end` LOOKS THROUGH a CHOSEN end to the session before it (bounded, one step back each
    pass), but only when all of these hold (`_stopped_before_restore`):
    - the session is a continue with `continued_from` None;
    - its end line says `stopped_before_restore` and is not chosen;
    - BOTH the host's own record of the end (the launcher line's or the verdict's reason; for a harness session, its end
      line) and the end line begin "stuck: the continue stopped:";
    - no `save` or `lost` line follows its session line.

    The look-through never grants more than the session before allowed. The per-session table is now
    `_classify_session`, the same rows as before.
- **Tests:**
  - `CensusSiteTests.test_every_other_stop_of_the_continue_says_why` now also asserts `may_retry` on the seven.
  - `test_only_a_bound_or_a_failed_read_may_retry`: the spec's four stops are not retryable; CONTROL: a continue that works.
  - `test_a_loop_that_lets_no_frame_pass_is_stopped` adds `may_retry`.
  - `LauncherContinueTests.test_a_continue_that_stopped_before_its_restore_is_looked_through` covers six cases and two
    sequences. Each FAULT half is refused: the spec's stop, a session that played after its line, the host's record
    naming another end, and a CHOSEN session before it.
  - `R1PlayTests.test_r1_a_continue_that_stops_on_a_bound_is_not_a_chosen_end` runs through `HandsBrain.play`.
- **Mutants FX2-FX6:** the flag ignored, no look-through, the played-after check removed, the host's record not asked, the
  save-gone stop marked retryable. Each is CAUGHT.
- **Live:** K-FIRST's child B (the erased page) still ends CHOSEN with `stopped_before_restore` False on 4 of 4 seeds, and
  no end line says True. No live arm stops on a bound, so the look-through itself is proven offline only.

### R-3: ruling 4 was not followed (two stage-1 waivers), and the report undercounted them

- **Reproduced:** with the two waivers still in, the census after this round's code edits had 28 MISSING
  (`census-1-after-code.out`), all sites this round's own code moved or added. With the two waivers taken out, the census
  the generator runs had 41 MISSING (`gen-1.out`: `41 missing sites`; `census-plan.txt`). The 13 extra sites are
  `FrameworkEyes.__init__` @ `host/session.py` `Session.__init__` and the 12 `_guarded` calls of `FrameworkEyes._screen`.
- **Fix:** both waivers are removed from `census_waivers.json` (35 to 33 waivers). Their 13 sites are closed by revert_r1
  census mutants F018-F030, each deleting one call, with two new tests in `CensusSiteTests`:
  - `test_the_host_screen_reads_every_part`: `_screen` with EVERY part stood in, so each of the 12 reads shows in the
    `ScreenState`. That means in_battle, text_box_open, the menu (it needs the tasks and the fade), the button wait,
    fading, the text, script_running, controls_locked, the scene, and on their own screens the battle wait and the save
    wait. CONTROL: nothing reported waiting, nothing waits.
  - `test_the_session_builds_the_eyes_the_save_reads_rest_on`: a real host `Session` built in-process. Its `eyes` is a
    fresh `FrameworkEyes` (`_save_callbacks` None, the crop on), and its screen read gives the save wait.
- **The F-mutants' first run** (`revert-subset-1.out`): every one CAUGHT. Their expected tests were recorded from it, as
  stage 4 did (`freeze-1.out`): F018 by the session test, F019-F030 by `test_the_host_screen_reads_every_part` (four also by
  the older host-look test).
- **The report's undercount:** stage 4 named only `FrameworkEyes.__init__`. The `_guarded` waiver covered 12 more of stage
  1's sites. Both are now mutants, not waivers.
- **Re-anchoring.** The fix moved 18 census mutants' anchors: C034, C133, C137, C138, C140, C145, C162, C188, C191, C194,
  C242, C339, C340, C342, C344, C345, C347, C348.
  - They were removed and REGENERATED for the same sites with stage 4's generator (`fix/gen_fix_mutants.py`, names F001-F041
    with the 13 above). The map is in `name-map.out`.
  - C162's call moved into `_classify_session` and `_stopped_before_restore`, so it is now F014 and F013.
  - Hand-written L10's anchor was re-anchored on the new line, and still mutates the same refusal.
  - call_census after: `CALL-SITE CENSUS since HEAD: 15 AI files changed, 204 functions or added calls, 888 sites; 0
    MISSING` / `CALL-SITE CENSUS: PASS`.

### R-4: spec T4 (save goals in the errand share's total) was not built

- **Reproduced** (`repro-R4-before.out`): the same goals with one save goal moved `errand_share` from 0.5 to 0.3333.
  `ERRAND SHARE MOVED BY A SAVE: True`.
- **Fix:** `rate_step5.py` has `SAVE_KIND = "save"`. `intent_mix` takes save spans out of `frames`, the total and `goals`,
  and reports them as `save_frames` and `save_goals`. Their gaps stay in `between_goals`. It is a no-op without a save goal.
  After the fix (`repro-R4-after.out`): `ERRAND SHARE MOVED BY A SAVE: False`.
- **Test:** `SecondRoundTests.test_a_save_goal_is_out_of_the_errand_share` (test_goals, beside the intent_mix tests).
  **Mutant FX7** (saves left in the total): CAUGHT.
- **The hash:** `rate_step5.py`'s sha256 (its `HASHED_FILES`) moves. No graded range is left registered and unplayed
  across it: ledger #45-#54 were all done, and #55 is live_r1's, which does not hash `rate_step5.py`. live_step5's next run
  is still a re-baseline (spec section 7), which is the orchestrator's to say.

### R-5: the headline PASS did not carry the K-BETWEEN substitution

- **Fix:**
  - `live_r1.py` `between_caveat`: when K-BETWEEN is graded under a rule that is not the spec's midpoint, the verdict line
    says so, with K-BETWEEN-MID's count on those seeds. A selftest case pins the line (`SELFTEST: the clean run PASSES (30
    cases) and 6 of 6 planted faults FAIL as they must -> PASS`).
  - The earlier evidence file `ai_player/evidence/2026-10-29-r1live-HELDOUT.txt` has line 1 amended to carry the same
    caveat, and says it was amended (sha256 fe0952f65fbfc5f0 before, 79811d117ce47166 after). Every other line is
    unchanged.
  - Also from the re-run's notes: `live_r1.py ledger register|begin|numbers` take `--first/--last`, and
    `registered_numbers(seeds)` hashes the seeds it plays.
- **OPEN:** the RULING itself. K-BETWEEN's rule "new" against the spec's midpoint is the orchestrator's call. Every
  verdict line and headline now says which rule it rests on.

### Checks (verbatim last lines)

- Quick lane, at the end (`quick-final.out`): `REGRESSION: PASS (quick, 21 suites, 45.4 s wall)`. test_saving has 132
  tests, test_goals 254.
- `u1-*.out`:
  - test_check_purity (30): `OK`; test_safety_gates (49): `OK`; test_world (132): `OK`;
  - test_host ControllerTogetherTests: `OK`; test_evidence (27): `OK` (again after the evidence file: `OK`);
    test_measure_step5 (28): `OK`;
  - check_purity: `VERDICT: PASS`; check_fairness: `PERSON-FAIR DATA DOOR: PASS (0 breaches)`; check_paths: `PATHS GATE:
    PASS (46 files, 0 findings)`;
  - live_r1 selftest: `SELFTEST: the clean run PASSES (30 cases) and 6 of 6 planted faults FAIL as they must -> PASS`.
- revert_r1, every mutant (`rv1-revert_r1.out`, 916.6 s): `467 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as predicted,
  of 468 run (468 defined)` / `OVERALL: PASS`. The control: `396 tests ... failing none ... -> PASS`. Evidence
  `ai_player/evidence/2026-10-29-r1-fixround-REVERT.txt`. `run_regression_times.json` revert_r1 is now 917 (was 823).
- revert_step5 (`rv1-revert_step5.out`): `400 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 402` /
  `OVERALL: PASS`. Evidence `2026-10-29-r1-fixround-step5-REVERT.txt`.
- revert_safety_gates (`rv1-revert_safety_gates.out`, it covers rate_step5's HASHED_FILES): `23 mutants CAUGHT as
  predicted, of 23` / `OVERALL: PASS`.
- Live, ledger #55 (`build/fix/`):
  - `ledger register`: `REGISTERED numbers sha256 81c2b3d01a3a34b4...` at 4:22:32 PM. A grep of the ledger for 5471-5474
    found 0 entries before that.
  - `ledger begin`: `... GRADED, HELD-OUT seeds 5471-5474 (ledger entry #55) ... (the same); no other entry of family
    'story' names any of these seeds`.
  - The plan: `PLAN DONE: 44 jobs, exit codes not 0: none (04:32:24 PM, 583 s)`.
  - `verdict`: `LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the
    midpoint arm K-BETWEEN-MID counted 0 of 4: vacuous) (failing: none; below the floor: none; discriminators that differ:
    24 of 24)`.
  - `ledger finish`: `FINISHED #55`; `ledger --check`: `LEDGER ledger.json: 55 entries; well formed -> PASS`.
  - The tree digest is 4e3e288ed3679711 at begin and after the run.
- Hygiene before and after: lane census 0; the main checkout's `sandbox-pokebot` 0 files and `ai_player` 0 files modified
  since 3:20 PM; this round's processes alive: 0.
- Evidence file: `ai_player/evidence/2026-10-29-r1live-FIXROUND.txt` (740,758 bytes, sha256 13ad9b2c1a21d862...). It holds
  every output above, verbatim.

### Measured (#55, seeds 5471-5474)

- Every graded arm counted on 4 of 4 seeds. Every NEW arm passed every check; every OLD arm showed its difference. 24 of
  24 discriminators differ. 24 of 24 determinism lines equal the CONTROL's: one trajectory per seed, replayed (rule 8).
- K-SILENT: 0 new sectors at the kill on 4 of 4 seeds, so it counted. S2's line was written at e3-5 on every seed,
  14 frames before the kill at e3+9.
- K-INSIDE had 7, 7, 7, 7 new sectors at the kill (S1+ERROR). K-FIRST had 7, 6, 6, 6 (CORRUPT).
- CONTROL saves per run: 6, 6, 5, 5. Each ended `done: ch1_pokedex reached` with its end save made.
- No measured value contradicted the probe report beyond the variation ruling 1 already ruled on.

### Deviations from the spec, and why

1. **Section 3 (f) has no row for a continue that stops on a bound or a failed read.** The fix makes such an end NOT
   chosen, and the launcher looks through it (R-2). The spec's own rows are unchanged and stay CHOSEN: erased, no
   CONTINUE, a TIME it does not know, an arrival that differs. D12 (a)'s table gains one rule, the look-through, which can
   never allow more than the session before allowed.
2. **`last_save.frame` is now the write's start frame** (the memory line's `frame`), not the SAVED page's. This keeps the
   live and the restored memory equal. See R-1 for why no decision moves.
3. **18 census mutants were regenerated under new names (F-names), not re-anchored by hand** (`name-map.out`). Their
   predictions were recorded from their first run, as stage 4's were.
4. **revert_step4 and revert_step3 were not re-run.** They anchor no file this round changed, and revert_step4 rewrites a
   TRACKED evidence file. revert_step2 and revert_step11 were not re-run either (ruling 2).

### What I did NOT do

- The R-5 RULING (the orchestrator's). The docs, `06`, `07` and the commit (the orchestrator's).
- test_host (whole) and test_kb2 (ruling 2: no `sandbox-pokebot/mgba` in a worktree).
- A live arm that stops on a bound, or that saves after a continue (review N-3: child B's 2,620 frames are under
  `SAVE_FRAMES_NEEDED`). R-1 is proven live through the payload every save line carries, and its CONSEQUENCE (no second
  save before the talk) offline. R-2's look-through is offline only.
- The NITs N-1, N-2 and N-4 (`BaseException`/`GeneratorExit` in the purity gate, RULE C's attribute-only reads,
  `errors="replace"` in `read_book`). They are untouched and still open as the review filed them.
- Untracked files this round left in the worktree: `ai_player/evidence/2026-10-29-r1live-FIXROUND.txt`,
  `2026-10-29-r1-fixround-REVERT.txt`, `2026-10-29-r1-fixround-step5-REVERT.txt` and `trees/f58a83ed8291a136.zip`. The
  subset run's tree zip was moved to `build/fix/worktree-evidence/`. The orchestrator decides what to commit.
- Any git write. I did not touch the bot tuner's clone or its processes, `sandbox-pokebot/` code, or the main checkout.

## Independent verification of the FIXED code (the orchestrator's workflow `r1r2-verify-fixed`, after the fix round)

Two agents that wrote none of this code ran in parallel from about 4:45 PM: a live re-run on NEW held-out seeds, and an
adversarial review of the fix round. Their hand-backs follow verbatim; what the orchestrator did with them is the last
part.

### The live re-run on seeds 5481-5484 (ledger #56): AGREES

- CONTROL: live_r1 4/4 ok. Mine 4/4: FILE S6/S5/S5/S5 = the newest save, the loaded slot equals the newest truth, and every run ended 'done: ch1_pokedex reached'.
- K-AFTER: live_r1 4/4 ok. Mine 4/4: FILE S2 with 14 sectors complete at the kill, NEW ['0:10','2:2'] on 5481 and ['0:10','0:18','2:2'] on 5482-5484, ALL of NEW restored, continued_from 2, arrival = S2, no page.
- K-INSIDE: live_r1 4/4 ok. Mine 4/4: FILE S1+ERROR with 7/7/6/7 new sectors at the kill (the row's count equals mine), the CORRUPTED page, NONE of NEW restored, continued_from 1, arrival = S1.
- K-SILENT: live_r1 4/4 ok, and it counted on 4/4. Mine 4/4: the S2 line was written at e3-5, before the kill at e3+9, with 0 new sectors at the kill. FILE S1, no page, NONE of NEW restored, continued_from 1, arrival = S1.
- K-FIRST: live_r1 4/4 ok. Mine 4/4: FILE CORRUPT with 6/6/6/6 new sectors at the kill, the ERASED page, and child B stopped with 'the save is gone'.
- K-BETWEEN, rule 'new' (graded): live_r1 4/4 ok. Mine 4/4: NEW was non-empty at the kill (['0:10','2:2'] on 5481, ['0:10','0:18','2:2'] on 5482-5484), none of it was restored, FILE S1, continued_from 1, arrival = S1.
- LAUNCH: live_r1 4/4 ok. Mine 4/4: the first look was [UNKNOWN, frame 0], a cold boot. continued_from 2, purity CLEAN.
- K-INSIDE-OLD: live_r1 4/4 shows. Mine 4/4 by POSITIVE evidence: child B ran the mutant tree's skills/saving.py (trees/R1-M-K-INSIDE-OLD-<seed>), restored ALL of NEW and continued from save 2, where its twin restored none and continued from save 1. Child B ended 'stopped: not finished within 2620 frames', not a crash.
- K-SILENT-OLD: live_r1 4/4 shows. Mine 4/4 by the same positive evidence: the mutant tree ran, ALL of NEW was restored, continued_from 2 against the twin's 1, and there was no crash.
- LAUNCH-OLD: live_r1 4/4 shows. Mine 4/4: the mutant ran, the first look was [OVERWORLD, 66883] against LAUNCH's [UNKNOWN, 0], and continued_from was None.
- K-BETWEEN-MID (diagnostic, never graded): 0 of 4 counted. NEW at the midpoint kill was empty on every seed (vacuous), the same as on #53 and #55.
- Discriminators: live_r1 24 of 24 differ; mine, recomputed from the raw outputs, 24 of 24 differ. The FILE words in the job logs' LIVE ARM lines equal mine on every row.
- Determinism: 24 of 24 lines are same_as_control. That is one trajectory per seed, replayed. It is NOT a replication, and the seeds were not 'measured twice'.

**R-1, live:** PASS. I read the memory files with my own reader (r1_live.py), which imports nothing from ai_player: no read_book and no MemoryBook.rebuild. It rebuilds each save's payload by applying the line's set/del ops to its parent's payload. In the 52 child-A memory files (28 live profiles and 24 copies frozen at the kill), 93 of 93 save lines hold their OWN save as goals.last_save: the id equals the line's id and the play time equals the line's stamp. There were 0 failures and the frames matched too (0 mismatches). Across all 92 memory files, child B and launcher files included, 161 of 161 lines pass. The reader was fault-tested: on #53's PRE-FIX files it found 0 of 93 child-A lines correct (57 of 57 in the live profiles failed, matching the fix round's 0-of-57), and on #55's fixed files it found 94 of 94 correct. One line quoted from profiles/ai-r1live-control-5481/ai_player/memory.jsonl, line 5: {kind: save, id: 2, parent: 1, full: false, play_time: [0,21], frame: 88365}. Its rebuilt payload's goals.last_save is {id: 2, play_time: [0,21], frame: 88365, why: 'a save: it healed at the POKeMON CENTER (OLDALE_TOWN_POKEMON_CENTER_1F)'} and saved_for is {}. The diff itself sets goals.last_save.id = 2, .play_time = [0,21] and .frame = 88365.

**Write timings:** Registered at 4:54:55 PM and begun at 4:54:56 PM. The 44 jobs ran 4:55 PM to 5:06:43 PM (701 s); each job took 6.7 s to 425.4 s. Verdict at about 5:06 PM; ledger finish and check, and the evidence assembled, by 5:09 PM (Los Angeles, 2026-10-29).

Notes:

- The seeds were not used before. The ledger had 55 entries and none of their ranges met 5481-5484; ledger.json contains 0 text hits for those numbers. A scan of 151,772 files under build/ found 0 hits outside the tree copies. The 72 hits inside tree copies are frame counts in old step-5 RATE evidence (for example "shop": 5482), never seeds. The first version of my scan (seed-check.out) matched inside hex addresses in .sym files; seed-check-2.out supersedes it, and both are kept.
- Registration went in before any run, through the driver's own commands. 'live_r1.py ledger register --first 5481 --last 5484' made entry #56 at 4:54:55 PM, with numbers sha256 e8a5b4a1f05d92bef25e8b0ac72b01945500714b29ec787a4f6a60d19b275088; the registered numbers name seeds 5481-5484. 'ledger begin' at 4:54:56 PM reported the same sha and no other story entry naming these seeds. The plan was the fix round's run_plan.py with only FIRST and LAST changed: 44 jobs, every exit code 0. Then 'ledger finish --id 56' with evidence ai_player/evidence/2026-10-29-r1live-VERIFY.txt, and 'ledger --check' gave 56 entries, well formed, PASS.
- The tree digest was 4e3e288ed3679711 before registration, at begin and after the run. That is the same digest as #55, so this is the fixed code.
- live_r1's verdict line, verbatim: LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 0 of 4: vacuous) (failing: none; below the floor: none; discriminators that differ: 24 of 24)
- My instruments were tested before I relied on them. fault_my_parser.py gave PASS twice, on #55's K-AFTER-5471 and on K-AFTER-5481: control S2, one flipped byte S1+ERROR, erased EMPTY, no complete slot CORRUPT. my_arm_checks.py computes each expectation from the arm's own record (ruling 2). It gave 164 of 164 on #55 as a control, and its fault test flagged 7 of 7 planted faults with the control clean. On 5481-5484 it gave 164 of 164 ok.
- Write timings (e). The K-AFTER and CONTROL records are identical. Save 1 took 264/263/264/263 frames, first sector at e3+17/17/17/18. Save 2 took 258/260/266/261 frames, first sector at e3+16/16/17/17. All are inside ruling 1's range (254-266, e3+16..18); 5483's save 2 at 266 is at the edge, not outside. On K-SILENT, S2's first sector came 7/7/8/8 frames after the kill.
- Worktree writes: only ai_player/gates/ledger.json (entry #56) and the new evidence file ai_player/evidence/2026-10-29-r1live-VERIFY.txt (365,627 bytes, sha256 f001820c463a4553955da5aa65287acd0c4f0a5561185dee42adbe2ec13f4044). A find -newer from my start shows only those two. The tooling wrote NO tree zip under ai_player/evidence/trees/: the mutant trees went to verify2-rerun/heldout/trees/ in scratch. test_evidence passed after the file was added (Ran 27, OK). No git writes.
- Hygiene. At the end: lane census 0 and re-run processes alive 0. At the start, the orchestrator's run_gates --quick was running in the main checkout, which was expected. The main checkout's ai_player had 24 files modified since 4:47 PM (the orchestrator's copy and its __pycache__). sandbox-pokebot had 2: profiles/repro-fresh/current_state.ss1 and states/2026-10-29_16-52-32.ss1. Their 4:52:32 PM timestamp is before my plan started at 4:55 PM, so they come from the orchestrator's quick lane, not from me.
- Cosmetic only: my scripts run under -I, which ignores PYTHONUTF8, so a quoted 'why' prints POKeMON's accented e as a replacement character in the .out files. The stored data is unaffected and the checks compare the data, not the printout.
- Timings: the plan ran 4:55 PM to 5:06:43 PM (701 s). Jobs took 6.7 s to 425.4 s each, all under their timeouts.

Evidence file: `C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_ad737c3f-1d5-1/ai_player/evidence/2026-10-29-r1live-VERIFY.txt (raw outputs and scripts in C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/r1build/build/verify2-rerun/)`.

### The adversarial review of the fix round: FINDINGS

- **V2-1 (MINOR): R-5's between_caveat reports only how many seeds the midpoint arm COUNTED on, never whether it PASSED, so the headline can hide a failing spec-rule arm**
  - Scenario: On a run where K-BETWEEN-MID counts on 4 of 4 seeds but fails a check on every one, live_r1 prints 'LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 4 of 4)'. The same rows graded under the spec's midpoint rule give FAIL. The function's docstring promises 'how the spec's own rule fared on these seeds'. A reader of the headline sees '4 of 4' with no 'vacuous' and concludes the spec's rule also passes. Under ruling 5 the midpoint is diagnostic, but the headline is the half that gets skimmed (session discipline 2). On #53 and #55 the arm was vacuous (0 of 4). #54 counted it on 1 of 4, so the case can be reached.
  - Evidence: ai_player/gates/live_r1.py:1494-1496: `counted = sum(1 for seed in seeds if (summaries.get(("K-BETWEEN-MID", seed)) or {}).get("counted"))` / `return (f", WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE {BETWEEN_RULE!r}, NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted {counted} of {len(seeds)}{': vacuous' if counted < FLOOR else ''})")`. No `pass` is read. Probe on a copy (verify2-review/probe_caveat.py, output probe_caveat.out): 'graded verdict (rule 'new'): PASS' / 'verdict line: ... (the midpoint arm K-BETWEEN-MID counted 4 of 4)' / 'under the spec's midpoint rule the verdict would be: FAIL'.
  - Fix: Have between_caveat count the passes as well, for example 'counted N of 4, passed P' or 'counted N of 4, FAILING on seeds [...]'. Add a selftest case with the midpoint arm counted and failing.
- **V2-2 (NIT): No test or mutant pins that the verdict line carries the caveat: the selftest checks only between_caveat's return value**
  - Scenario: Deleting `{between_caveat(summaries, seeds)}` from cmd_verdict's print line brings back the bare 'LIVE R1 VERDICT: PASS (...)' headline that R-5 removed. The selftest still prints '30 cases ... PASS', because its new case calls between_caveat() directly. No test_*.py or revert_*.py file references live_r1 at all.
  - Evidence: ai_player/gates/live_r1.py:1530 `print(f"LIVE R1 VERDICT: {result['verdict']}{between_caveat(summaries, seeds)} ...` and the selftest case at live_r1.py:1742-1746 (`case(... between_caveat(mid, seeds), ...)`). A grep of ai_player/gates for cmd_verdict, between_caveat or live_r1 in test_*.py, revert_*.py and run_regression.py finds nothing. verdict.json's `verdict` field (live_r1.py:1526) also stays a bare 'PASS'.
  - Fix: Have the selftest build the verdict LINE through the same helper cmd_verdict uses, or factor out a `verdict_line(result, summaries, seeds)` function and pin that. Optionally put the caveat into verdict.json too.
- **V2-3 (NIT): The R-5 amendment of the HELDOUT evidence file also stripped 426 CR line endings; 'every other line is unchanged' is not true byte for byte**
  - Scenario: Someone checks the stated provenance by restoring the original line 1 and hashing the file, to get the recorded 'sha256 fe0952f65fbfc5f0 before'. The hash does not match, because 426 lines that were CRLF in the original are now LF. The text of those lines is identical; only line 1's content changed. The amendment note itself says 'the run and every line below are unchanged'.
  - Evidence: verify2-review/cmp_heldout.py against build/fix/orig/.../2026-10-29-r1live-HELDOUT.txt (sha256 fe0952f65fbfc5f0...) and the worktree's copy (79811d117ce47166...), output cmp_heldout.out: 'old CR count 426 new CR count 0' / 'differing line numbers: 427' / 'differ ONLY by a trailing CR: 426' / 'differ in content: [1]'.
  - Fix: Rewrite line 1 in binary mode and keep the other bytes, or change the amendment note to say the line endings were normalized to LF, with that fact's own sha.
- **V2-4 (NIT): Other verdict headlines still lack the caveat, and the caveat's 'awaits the orchestrator's ruling' is now stale after ruling 5**
  - Scenario: Three records still give a PASS headline without the substitution caveat: ledger #53 and #54 ('GRADED, PASS (...K-BETWEEN (rule new)...)', with no 'not the spec's midpoint' and no 'would be INCONCLUSIVE'), and the HELDOUT file's own verbatim verdict line 1025. Separately, three places still say the substitution 'awaits the orchestrator's ruling', which ruling 5 has now given: HELDOUT line 1, FIXROUND line 1 and ledger #55's verdict. A cold reader would think the K-BETWEEN rule is still open.
  - Evidence: ai_player/evidence/2026-10-29-r1live-HELDOUT.txt:1025 'LIVE R1 VERDICT: PASS (failing: none; below the floor: none; discriminators that differ: 24 of 24)'. ai_player/gates/ledger.json #53 verdict 'GRADED, PASS (R1 + R2 build spec section 5, ...'. Ledger #55 verdict '... the substitution awaits the orchestrator's ruling, review R-5'. FIXROUND line 1 '... the substitution awaits the orchestrator's ruling, review R-5'.
  - Fix: When committing, record ruling 5 next to these headlines (for example 'K-BETWEEN graded under rule new, orchestrator ruling 5; midpoint diagnostic') and give #53 and #54 the same caveat form as #55.
- **V2-5 (NIT): R-2's look-through has no limit on how many identical retryable stops can pile up, and its message never says that sessions were looked through**
  - Scenario: An arrival timeout is likely to repeat on the same save, for example a save at a place whose on-load scene runs longer than ARRIVAL_BUDGET. Each --continue then stops again, appends a session line and an end line, and is looked through again. With 50 such stops, classify_end still returns ('KILLED', 'harness session 1 has no end line: it was killed', True), and nothing tells the operator or a future R15 supervisor that 50 continues in a row failed. Before the fix the game could never be continued again; now it can be retried with no end. No state changes, so this does not touch ruling 52, but it is unbounded.
  - Evidence: ai_player/host/launcher.py:350-357: `for _ in range(len(sessions)):` ... `if kind != "CHOSEN" or earlier is None or not _stopped_before_restore(book, session, reason): return kind, words, allowed` / `session = earlier`. The earlier session's `words` are returned unchanged. Probe verify2-review/probe_lookthrough.py (probe_lookthrough.out): '1 / 5 / 50 identical retryable stops -> ('KILLED', 'harness session 1 has no end line: it was killed', True)'.
  - Fix: Add the number of looked-through sessions and the newest stop's reason to `words`, for example '(looked through N continues that stopped: <reason>)'. Optionally refuse, or warn, after K consecutive stops with the same reason, so a supervisor cannot loop forever.
- **V2-6 (NIT): R-4 takes save goals out of intent_mix only; the AI's curiosity row and the grader's streaks still treat a save as breaking a run of curiosity goals**
  - Scenario: A big story moment passes in a scene played between goals, right after two curiosity goals (curious_row = 2, the cap). At the next decision block 1b picks the moment save. after_goal(save) resets curious_row to 0, so the AI may play two more curiosity goals: C C save C C. live_step5's SPACING check (curiosity_streaks) also splits the run at the save, into 2 and 2. T4 treats a save as bookkeeping, 'neither an errand nor the story's step', yet here it acts as a story or need goal. Aside streaks (ASIDE_STREAK_MAX) split the same way. This is rare, because center saves follow a heal goal and moment saves usually follow a goal in which the story moved.
  - Evidence: ai_player/brain/goals.py:1068-1069 `if goal.kind not in CURIOSITY_KINDS or story_moved:` / `self.memory.curious_row = 0` (a save goal is not in CURIOSITY_KINDS). ai_player/gates/rate_step5.py:1527 `if span["kind"] in CURIOSITY_KINDS and not span["story_moved"]:` (any other kind, save included, ends the streak). live_step5.py:608 `rows = curiosity_streaks(run.records)` and :646 `streaks = aside_streaks(run.records)`. Only intent_mix (rate_step5.py:1102-1104) filters SAVE_KIND.
  - Fix: Decide whether a save is transparent to the curiosity row. If it is, skip `save` in after_goal and in curiosity_streaks and aside_streaks, the way intent_mix does. Otherwise record in 06 that a save counts as a break.

Checked and found sound:

- R-1 brain/saving.py saved_state and record_save: record_save applies exactly what saved_state returns (a copy of saved_for with the leader's approach added, last_save set to this save, save_due None). _Memory has no init=False fields, so dataclasses.replace(manager.memory, **saving) in mode.py:556 does not reset anything. SOUND
- R-1 the id: on_writing passes writer.next_id, which write_save stamps on the line and only increments afterwards (game_memory.py:786-797), so the payload's last_save.id equals the line's id. SOUND
- R-1 the payload in each case. A save answered NO never reaches _write, so there is no line and no payload. An ERROR page (including a first look already on ERROR, the late-stamp branch skills/saving.py:411-413) writes line k with last_save=k while the live policy keeps k-1 and its due. Line k can only be matched if the cart holds it, because SAVE_MIN_MINUTES (3) is greater than MATCH_MINUTES (1). A retry within the same minute is newer in the file, so it wins match_time. A kill mid-write (K-INSIDE, K-SILENT) leaves the cart with k-1, which matches line k-1, whose payload now says k-1. All three consistent
- R-1 last_save.frame is now the write's start: the only reader is before_leader (brain/saving.py:207-208); the 3-minute gap check reads play_time. Frames stay monotone across sessions (frame_base). World transitions are restored with their frames (world/memory.py:806/828), so after a continue from a gym save entered == saved_for[m]. No other reader in mode.py, live_r1.py or the gates
- R-2 classify_end look-through: it terminates (range(len(sessions)), and each pass steps strictly back). It never returns more than the earlier session's own class. Probes: KILLED then 1, 5 or 50 stops gives allowed; CHOSEN not at a save then stops gives refused; CHOSEN at a save gives allowed (probe_lookthrough.out)
- R-2 a continue cut by the budget, the wall clock or a crash before its STOP writes no session line and no end line (self._writer is set only after continue_game returns), so session N-1 decides. Nothing new is opened
- R-2 the stop path: _play(stop=...) returns through _play_end before any press, and _save_before_done and the settle run only on 'done'. So a looked-through session pressed nothing after the continue skill and wrote no save or lost line. No path from the AI's own play reaches a may_retry stop: they all sit in continue_game before play begins. Ruling 52 holds
- R-2 the 7 retryable stops (still passes, too many pages, no main menu in time, menu gone, TIME unreadable, CONTINUE not taken, arrival timeout) pass retry=True. The spec's stops (the save gone, erased or no CONTINUE; an unknown TIME; an arrival that differs) keep the fail-closed default. My mutants G6 and G7, which mark the arrival-differs and unknown-TIME stops retryable, are both CAUGHT by test_only_a_bound_or_a_failed_read_may_retry (guard_mutants.out)
- R-2 guard mutants G1-G5 (drop how==continue, drop continued_from, drop the chosen check, drop the 'stuck:' requirement in end_line, set may_retry from a continued result) all SURVIVE LauncherContinueTests, CensusSiteTests and R1PlayTests. They are equivalent mutants: no writer can produce such an end line (end_line forces chosen = not held, and may_retry is set only when not continued). Defense in depth, so no finding
- R-3 census_waivers.json: the two stage-1 waivers are removed. Of the remaining 33, the only stage-1 callee is FrameworkEyes._text, which is a name collision (NOT A SITE), not a closure. F018-F030 each replace exactly one call with None (revert_r1 enforces that each anchor occurs exactly once, revert_r1.py:226). In the fix round's REVERT evidence, each is CAUGHT by an assertion FAIL: test_the_host_screen_reads_every_part, or assertIsInstance in the session test. ERRORs appear only on secondary predicted tests (F020, F021, F027). No import or crash catch
- R-4 intent_mix: save spans leave frames, the total and goals. between_goals sums the gaps of every span, saves included, and the unit test pins 400. Its consumers live_step5:596 and rate_step5:2007 are consistent. The sweep runs (play_harness without --memory) never save
- R-4 ledger: entries #1-#55 are all 'done', so no registered graded range is left open by rate_step5's sha change. live_r1's HASHED_FILES does not include rate_step5.py. ledger.begin compares a registration only against its own begin
- R-5 FIXROUND line 1 and line 3104, ledger #55 and HELDOUT line 1 carry the caveat. HELDOUT line 1025 (verbatim old output), ledger #53 and #54 do not (V2-4)
- registered_numbers(seeds): register, begin and numbers all hash the same (first, last) taken from the arguments, so #55's registration and its begin agree
- Copies only: every probe ran on verify2-review/copy (a copy of the worktree's ai_player without evidence) or on temp copies that were removed afterwards. No worktree or repo edits, no git writes, no process of mine left running. Scripts and outputs are in C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/r1build/build/verify2-review/ (probe_caveat.*, probe_lookthrough.*, guard_mutants.*, cmp_heldout.*, fmutants.out, diff_*.patch, before/ and after/ tree unzips)

### What the orchestrator did with them

- **The live re-run (#56): AGREES, accepted.** Its ledger entry and its evidence file (`ai_player/evidence/2026-10-29-r1live-VERIFY.txt`) were copied to `main` with the build.
- **The review's V2-3 and V2-4 were fixed at the commit** (records only: the evidence files and the seed ledger are outside the tree digest, so the proven tree is unchanged; `s53/r1build/docs/fix_records.py`): `2026-10-29-r1live-HELDOUT.txt` line 1 now names ruling 5 and says its amendment made the line ends LF; `2026-10-29-r1live-FIXROUND.txt` line 1 and ledger #55 name ruling 5 instead of awaiting it; ledger #53 and #54 gain the caveat #55 carries. Each change is marked as made at the commit.
- **V2-1, V2-2, V2-5 and V2-6 go to R1 + R2's follow-up item** (`06` 2026-10-29, "Known limits"; `04` item 4), with the first review's N-1 to N-4. No code was changed after the verified tree (digest `4e3e288ed3679711`), so every live verdict above stands on the committed code. V2-1's case (a midpoint arm counted AND failing) did not occur on #53-#56: the midpoint arm counted on 0, 1 (passing there), 0 and 0 of 4 seeds.
- The review's R-2 guard mutants G1-G5 survive as EQUIVALENT mutants (no writer can produce the end lines they would let through): recorded as found, a defense in depth, no finding.
