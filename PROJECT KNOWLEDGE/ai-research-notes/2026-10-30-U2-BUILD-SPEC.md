> **Filed 2026-10-30** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/u2/SPEC.md` (sha256 `668718365fdf661f`). USER RULING 53's U2 (`06` 2026-10-29) with the follow-up's deferred RV-3, RV-5 and RV-7. Made by the workflow `u2-spec` (5 agents, 8.26 Mtok): a designer, two adversarial critics (27 findings, 5 MAJOR), a reviser (its section 11), a cold-start check (could start: YES; one MAJOR gap: U2-TIME's window exists on only 2 of 22 recorded CONTROL seeds at the provisional margin).
> **The orchestrator's SCOPE CUT (it binds the build, `u2a-build`):** only U2a was built: the summary's parts 1, 2, 5, 6, 7 and 8 (the continue rule, the host-record rules, what a continue tells it drops, RV-7, RV-5, RV-3 without its time-save rule) and the live arms U2-BUDGET and U2-WALL with their OLD arms. Parts 3 and 4 (D6-D12: the time save, its two stages, the cut, the wall-pace knowledge) and U2-TIME are U2b, to be redesigned against measured play: the AI already saves at every centre heal and big moment, so a time save is rarely reachable to prove, and those parts carry most of the risk. `06` 2026-10-30 ("U2a BUILT").

# U2'S BUILD: A SESSION ENDED BY ITS TIME OR FRAME LIMIT MAY BE CONTINUED, AND THE AI SAVES BEFORE ITS TIME RUNS OUT (build spec, 2026-10-30, revised after two critic lenses)

> This spec builds USER RULING 53's U2 (`06` 2026-10-29) and `04-HANDOFF` NEXT ACTIONS item 4. It also takes in the follow-up's deferred RV-3, RV-5 and RV-7 (`06` 2026-10-30, "Deferred to U2's build").
>
> - **Base:** HEAD `417df790` (R1 + R2's follow-up). `f4412116` is R1 + R2's commit and `67c73a0f` the tree before R1 + R2.
> - **Anchors:** every `file:line` below was read at `417df790`. Every finding was checked against that code before anything was designed on it, and so was every critic's finding (section 11).
> - **Where the probes ran:** on an ARCHIVE of `417df790`'s `ai_player/` (`git archive`, session scratch `s53/u2/tree/`), and on the recorded rows of the follow-up's live rounds (`s53/r1f/build/{s2-live-dev,s3-graded,rerun,fix,verify-rerun}/`). None ran in the main checkout.
> - **The probe scripts** (each with its `.out` where one exists): `s53/u2/probe_judge.py`, `probe_rv57.py`, `scan_forms.py`, `measure_goals.py`, `measure_busy.py`, `measure_battle_share.py`, `review_proof/probe_matchas.py`, `rev_anchors.py`.
> - **Rulings in force:** USER RULINGS 35, 40, 41, 51, 52 and 53; the R1 + R2 build's orchestrator rulings 1-5; the follow-up's rulings 1-13.
> - ⛔ Do not re-ask U1, U2 or the reset question (ruling 53).

## 0. Summary

The item has ten parts.

1. **The continue rule (ruling 53, U2).** An end on the session's time or frame limit may be continued from the last save. Before this build it could be continued only when the end came right after a save. Two ends count as such a limit:
   - the brain's `play: stopped: ...`, which means its frame budget ran out;
   - the HOST's soft `wall-clock`.

   **What stays refused:**
   - **The launcher's hard kill** keeps the interim rule: it is allowed only when the end came right after a save (`at_save`). Ruling 53 reads "(not a crash and not a kill)", and a hard kill is the backstop for a run whose main thread stopped producing frames. A refused reset followed by a hang would end exactly that way (D1, D3a).
   - CHOSEN, unless at a save.
   - NOT CLEAN. `reset-refused` stays NOT CLEAN for good.
   - UNKNOWN.

   The harness path and the look-through follow the same table (section 2, D1-D5).
2. **A BUDGET end is judged by the HOST's record, as defence in depth (D2, D3, D3b).**
   - **`play: stopped:`** counts as BUDGET only when the instrument's own frame count reached the frame budget the launcher gave. The count is `purity.json` `counters.real_frames`; both numbers now go into the launcher's `launch_end` line. Measured: 40 of 40 genuine recorded stops have `real_frames` equal to the budget (2620). No early `stopped` end exists in any record, so the refusing side is proven only by unit FAULT rows (U5, U8).
   - **A host end reason** (`crash`, `wall-clock`, ...) counts only with the HOST's own exit code. The code is taken from the verdict's `facts.exit_code`, as the instrument wrote it. Today a brain that RETURNS the text `crash` (exit 0) is classed INVOLUNTARY and allowed (probed).
   - **A BUDGET end whose purity verdict is not CLEAN** is NOT CLEAN.
   - **A launcher run_dir is always judged by the launcher's line,** whatever the AI-written session line says about `host`.
   - **The limit, stated:** none of this makes a reload unreachable for a brain that wants one. Raising gives a real `crash`, which was already an accepted limit. Idling until the budget or the wall clock genuinely runs out also works. What this design guarantees is that such a reload costs the brain its whole remaining session, never nothing (section 9, KNOWN LIMITS).
3. **The AI saves before its time runs out (ruling 53: "so usually nothing is lost").** A fourth kind of save moment, `time`, is added to ruling 51's three by ruling 53. It has two stages. Each stage is made at most once per process. A stage is made only when:
   - the AI has something to lose since its last save (progress, a milestone, or a lost battle), and
   - a save still fits (at least `SAVE_FRAMES_NEEDED` frames left).

   The two stages:
   - **"nearly up":** made at `TIME_SAVE_FRAMES` frames left (`SAVE_FRAMES_NEEDED` + the measured reach from a due to a save started on a free screen). It covers a battle or a menu that is under way at that moment.
   - **"ends now":** made at `LAST_SAVE_FRAMES` frames left (`SAVE_FRAMES_NEEDED` + the measured cut-to-START lag).

   Both stages OBEY the 3-minute gap. Without the gap, two save stamps less than `MATCH_MINUTES` apart would make the save a continue loads ambiguous. That is the follow-up's known limit, which an exempt "ends now" would make reachable.

   **How the save is made:**
   - The time due lives in its OWN field, so a centre's, a moment's or a leader's due cannot overwrite it.
   - When a time due is pending and a save may start (the same predicate block 0 uses, including the goal's cooldown), the current goal is CUT at the next free overworld screen. The cut is checked after that look's `intent.done`. It counts as neither a failure nor a mark, in the play loop AND in the goal runner's own bookkeeping.
   - A failed time save consumes its stage.
   - The time save is chosen before HEAL (a hurt party is allowed).
   - The AI plays on after the save (it is never idle). A reached target is always checked first.
4. **The AI knows its wall limit (ruling 53: "wherever it knows the limit").**
   - `HandsOptions.wall_deadline` comes from the same `AI_PLAYER_WALL_DEADLINE` the session reads. That is the operator's session limit, not game state.
   - The brain's "frames left" is the smaller of two numbers: its frame budget left, and its wall time left at its own measured pace, divided by `PACE_SAFETY`.
   - Without a deadline (every harness run), nothing changes.
5. **Every continue logs what it drops (ruling 53).**
   - **What is dropped** is ONE set of sessions: those after the latest continue from that save, or after the save itself when nothing has continued from it yet. Frames, maps and lost battles are all counted over that same set.
   - **The launcher's sentence** (`ContinueCheck.dropped`, built inside `memory_check`) adds:
     - the frames from the HOST's count (`real_frames` per session);
     - the play time at the save and at the newest session's end (or "not recorded" when it has no end line);
     - the battles undone;
     - the maps first stood on after the save, read from each session's `world.jsonl` and named as the AI's own record.
   - **The AI's own after-arrival line and its session line's `dropped`** tell the frames it recorded (or "not recorded") and the battles undone. They tell NO play time and NO map: D19 says the memory of a continued game is its save's.
6. **RV-7.** The purity gate refuses a `raise` or an `assert` reached from a `finally` body in the play loop. Measured: zero uses.
7. **RV-5.** Fairness rule D3 (d) no longer refuses `case int(n)` / `case str(s)`. The exception covers the eleven self-matching builtins, with exactly one positional sub-pattern, where the name is bound nowhere in the module by any binding form. Such patterns read nothing. Every other positional class pattern stays refused.
8. **RV-3.**
   - CHAIN's and the OLD B arms' frame and wall budgets are re-measured with 12 parallel jobs in development #62.
   - They are then set at 2x the widest value measured in ANY round, using ONE measure: the formula's own arrival-to-kill.
   - New rule: no killed arm's budget may leave its widest measured kill within 2 x `TIME_SAVE_FRAMES` of the budget's end. Otherwise the time logic would steer that arm's play.
9. **The live proof.** Three new graded arms, each with an OLD arm:
   - **U2-BUDGET:** LAUNCH's real-launcher `play: stopped:` end, not at a save, then continued. OLD (mutant U0): refused.
   - **U2-WALL:** a real-launcher soft wall-clock end with no end line, then continued. OLD (U0): refused.
   - **U2-TIME:** a new game whose frame budget is set from its CONTROL's own record, so that the "nearly up" save must happen. The AI saves on a held free screen before the end, and the continue lands on that save. OLD (mutant T0): no time save, and the continue lands on the older save.

   The whole `live_r1` arm set is re-run on the final tree.
10. **Seeds:**
    - development #62: 5601-5606;
    - held-out: 5651-5654 (registered first);
    - independent re-run: 5661-5664;
    - fix round: 5671-5674;
    - verification after a fix round: 5681-5684;
    - spare: 5691-5694.

## 1. What and why (each part traced to what asks for it; each finding re-verified at `417df790`)

### 1.1 USER RULING 53's U2, and the interim in the code (verified)

- **The ruling** (`06` 2026-10-29, line 9912): "U2: YES. A play session that ends on its time or frame limit (not a crash and not a kill) may be continued from its last save, like a person who switches off without saving. The AI also saves before its time runs out wherever it knows the limit, so usually nothing is lost, and every such continue tells what it drops." It "changes R1 + R2's D12 (a): a BUDGET end becomes continuable, and the AI gains a save before its frame budget runs out."
- **How this spec reads "(not a crash and not a kill)":**
  - A crash and an outside kill were already continuable (INVOLUNTARY and KILLED). The parenthesis separates them from the new case; it does not refuse them.
  - The LAUNCHER's hard kill is a kill. It fires only when the soft deadline did not end the run, which means no frame reached the guard. That is a stuck main thread, not a person switching off, so it keeps the interim rule (D1, D3a).
  - This reading goes into `06`.
- **The interim, in the code:**
  - `host/launcher.py:255-261` names BUDGET "interim, pending the user's U2".
  - The harness branch is `:427`: `allowed = kind == "INVOLUNTARY" or at_save`.
  - The launcher's hard kill is `:434-436`: allowed = `at_save`. This row is checked BEFORE the line's `exit_reason`.
  - `wall-clock` and `play: stopped:` are BUDGET at `:454-455`. With no end line they are refused at `:458-460`; otherwise allowed = `at_save` at `:461`.
- **Probe** (`s53/u2/probe_judge.out`: `judge_end` on crafted files, on the archived tree):

  | case | class | allowed |
  |---|---|---|
  | launcher `play: stopped:`, end line not at a save | BUDGET | **False** |
  | the same, at a save | BUDGET | True |
  | soft `wall-clock`, no end line | BUDGET | **False** ("with no end line of the AI's (refused: fail closed)") |
  | the launcher's hard kill | BUDGET | **False** |
  | harness, `stopped`, not at a save | BUDGET | **False** |
  | `play: done:`, not at a save | CHOSEN | False |
  | `reset-refused` (exit 9) | NOT CLEAN | False |
  | run folder gone, no launcher line | UNKNOWN | False |

- **Why the soft wall clock is never continuable today:** `Session._on_frame` finishes the run as `wall-clock` from the guard (`host/session.py:322-327`), so the brain's `_end_memory` (`mode.py:651-661`) never writes an end line.

### 1.2 Findings while re-deriving the table (verified)

- **F-U2-1 (it matters once U2 is built): `play: stopped:` is the AI's own word.**
  - `Session.run` passes whatever the brain returns to `give_up(str(reason), EXIT_OK)` (`host/session.py:339-344`).
  - `HandsBrain` produces `stopped: not finished within N frames` only in `_bounded` (`mode.py:1341-1354`), but any brain code can return such a text early.
  - Under U2, BUDGET is allowed regardless of `at_save`, so an early "stopped" would buy a reload of everything since the last save.
  - **The host's own count tells them apart.** `purity.json` is written only by `lifecycle.finish`, and its counters cannot be written by the AI (gate rule f; `host/attribution.py:873-930`). Its `counters.real_frames`, over every recorded launcher verdict in `s53/r1f/build` and `s53/r1build/build`:
    - all 40 genuine `play: stopped: not finished within 2620 frames`: `real_frames` = 2620;
    - the 2 placeholder runs: 2620;
    - the two `crash` verdicts: `exit_code` 2.
  - The other recorded counts (1700 for the continues stopped at `CONTINUE_BUDGET`; 531-616 for R2-STOP) belong to `play: stuck: the continue stopped:` ends, which are CHOSEN anyway. **No early `play: stopped:` end exists in any record.** The refusing side is therefore unit-proven only (U5, U8).
  - The brain's own count agrees: `[AI-HANDS] ... frames=2620` on all 8 LAUNCH logs of #58 and #59.
- **F-U2-2 (pre-existing): a host end reason the BRAIN returns is believed.**
  - Probe rows: a launch line with `exit_reason "crash"` and `exit_code` 0 (a `give_up`, i.e. the brain's text) is classed **INVOLUNTARY and allowed**. `"wall-clock"` with code 0 at a save is BUDGET and allowed.
  - Host ends always carry their own codes (`host/lifecycle.py:86-94`; `host/session.py:194-397`). This is every `finish` call at HEAD:

    | reason | code |
    |---|---|
    | `crash` | 2 |
    | `stray-exit` | 2 |
    | `frame-budget` | 4 |
    | `parked-manual` | 3 |
    | `abandoned` | 3 |
    | `mode-restarted` | 3 |
    | `brain-returned` | 5 |
    | `isolation-lost` | 6 |
    | `refused-debug-mode` | 9 |
    | `refused-http-server` | 9 |
    | `_RESET_REFUSED` (`reset-refused`) | 9 |
    | `interrupted` | 130 |
    | `interrupted-unresponsive` | 130 |
    | `wall-clock` | 124 |

  - A brain's own reason always ends with code 0, or with 6 under a purity verdict that also replaces the reason (`host/lifecycle.py:160-163`).
  - The rule that closes this: **a host reason counts only with its host code.**
- **F-U2-3 (pre-existing): the verdict replaces the reason only for code 0.** `lifecycle.finish` turns the reason into `purity-breach`/`purity-unverified` only `if code == EXIT_OK and verdict != "CLEAN"` (`host/lifecycle.py:160-163`). A `wall-clock` finish (124) keeps its reason with a BREACH verdict. Under the interim, that end was refused (no end line). Under U2 it would be allowed. Closed by D3b.
- **F-U2-4 (pre-existing): the judgement branch is chosen by an AI-written field.**
  - `_classify_session` checks `session.get("host") == "harness"` first. The session line is written by AI-side code: `mode.py:471` `"host": getattr(options, "host", "launcher")`.
  - A launcher session whose line says `harness` would be judged by the AI's end line alone, even with a launcher line naming its `run_dir`. Closed by D4.
- **F-U2-5 (pre-existing): the hard-kill row comes before the verdict.**
  - `record_launch` keeps the verdict's `exit_reason` on a hard kill (`launcher.py:314-317`).
  - A process may stay alive up to `EXIT_WATCHDOG_SECONDS` (20 s, `host/attribution.py:267`) after its `finish`, while the launcher's soft-to-hard margin is `soft_deadline_margin` = min(30, max(5, 10%)) s (`launcher.py:521-527`).
  - So a `reset-refused` or `play: done:` verdict followed by a hard kill is judged "killed by the launcher". Closed by D3a.

### 1.3 "Save before its time runs out": what the brain has today (verified, measured)

- **Frames: it has them.**
  - `HandsBrain._frames_left` = `settings.frames - hands.pad.frames` (`mode.py:546-548`).
  - It reaches the policy through `manager.frames_left` (`mode.py:539` → `brain/goals.py:1411-1413` `_run_frames_left` → `SavePolicy.next_save`/`before_leader`) and the save skill's commit guard (`mode.py:593`).
  - It is exact at the stop (above).
- **Wall time: it does not have it.**
  - `AI_PLAYER_WALL_DEADLINE` (`options.py:97`, the SOFT deadline, set by `host/launcher.py:582-590` `child_env`) is read into `RunOptions.wall_deadline` (`options.py:303`) for the host guard only.
  - `HandsOptions` (`options.py:350-401`) has no deadline.
- **A trigger at decision points only cannot work.** Measured over the 10 CONTROL child A runs of #57 and #58 (`s53/u2/measure_goals.out`):
  - goals run up to 31,053 frames (train: median 15,843, p90 25,414); `go` runs to 22,155 and `talk` to 12,786;
  - the gaps between two goal decisions have median 1,323, p99 22,055 and max 31,053.
  - A margin covering a whole goal would be about 66k frames, lost at every session end. Hence the CUT (D9).
- **What the cut cannot interrupt:** a battle, a scene, a menu, and a skill's own free-screen steps that call neither `Navigator.run` nor `roam_train` (talk_to's facing and A presses, `_held_free` waits, the shop counter, a pick_up's last approach).
  - Battles are 31.3-46.5% of a run's frames (`s53/u2/measure_battle_share.out`).
  - The widest gap between two free action records is 6,646 frames (CONTROL-5554 f104532, a SHOP), and the widest battle stretch is 6,614 (`measure_busy.out`). These are the AI's ACTION-RECORD gaps: a PROXY for the reach, not the reach itself (D7).
  - The decision's pause is 14-45 frames, and `SETTLE_FREE` is 30.
  - A save goal takes 1,288-1,329 frames (47 saves).
- **Precedent for a cut:** `Navigator.roam_stop` (`brain/navigator.py:722`, asked on every free look in `skills/roam_train.py:275`) already lets the play brain stop a running roam.
- **Single due slot:** `_make_due` overwrites `goal_memory.save_due` ("the newest reason wins", `brain/saving.py:125-128`). `before_leader` re-makes a leader due whenever the slot holds another kind (`:210-213`). `due_now` expires a centre or leader due when the player leaves its map (`:137-140`).
- **The goal runner's own bookkeeping reacts to a walk's outcome:**
  - a `pick_up` that is neither "picked up" nor "interrupted" gives the ball up for good: `tried_items.add(key)`, `brain/goals.py:2139-2142`;
  - `_back_to_ball` does the same at `:2208`, `:2221`;
  - `item_tries` is counted at the walk's start (`:2130`).
  - `tried_items` and `item_tries` are GOAL_KEEP (`game_memory.py:130-131`), so a save payload carries them.

### 1.4 "Every continue logs what it dropped": what the files hold (verified)

- **`memory.jsonl`** (`game_memory.py:15-24`):
  - Only `save`, `saved`, `lost` and `end` lines carry `frame`. `session` lines carry `frame_base` and `run_dir`.
  - The `end` line (`end_line`, `:476-490`) carries `frame` only: no play time, no place.
  - `frame_base()` is "1 + the largest frame stamp in the file" (`:597-603`).
  - **After a soft wall clock or a hard kill there is no end line.** The newest stamp after a save can then be that save's own `saved` line, so "latest stamp − save frame" UNDERCOUNTS a whole session. The next session's `frame_base` also lands just past that stamp, so it OVERLAPS the dropped session's frame space.
  - ⇒ **Frames are NOT monotonic across sessions in exactly the ends U2 adds.** A drop count must be built per session, from the host's count where there is one.
- **`MemoryBook.timeline`/`undone_losses`** (`:605-631`) count the battles a continue undoes over the LIVE history: everything after k is cut at each continue from k. That is the one set the whole drop sentence must use (D13).
- **The launch records:**
  - `launches.jsonl` (`host/launcher.py:309-326`) holds `exit_code` (the PROCESS code), `hard_kill`, `interrupted` and `exit_reason`.
  - The run's `purity.json` holds `verdict`, the counters and `facts.exit_code` (the code the instrument wrote; a second thread's `finish` raises its own code, `lifecycle.py:142-147`).
  - The run's `world.jsonl` holds one snapshot per map change and one at the end (`mode.py:1336-1339`); each map has a `first_frame`. After a soft wall clock or a hard kill, the last map-change snapshot stands.
- **D19 (R1 + R2) forbids the AI's continue from reading a run's world file:** "a continued game's memory is its save's". Only the launcher side (`memory_check`, the operator line) may name the dropped maps.

### 1.5 RV-3 (verified on the recorded rows)

- `CHAIN_B_FRAMES` = `CHAIN_BUDGET_BASE` (2020) + 2 x 63,812 = 129,644, and `CHAIN_B_TIMEOUT` is 300 s (`gates/live_r1.py:154-161`).
  - The 63,812 is the formula's own measure: arrival → kill, widest over #57's six development seeds at 6 jobs.
  - `CHAIN_OLD_FRAMES` = 2020 + 2 x 45,363.
- Graded runs used 12 jobs at once.
  - The held-out spans were up to 94,918 frames, and the fix round's CHAIN child B reached 120,757 frames at the kill (5574, #60).
  - ⚠ The "120,757" was read in the report as a kill frame. The builder re-reads it IN THE FORMULA'S UNIT (arrival → kill) from the row before it is used (D14).
  - Walls reached 212.0 s (5574), 203.4 s (5572) and 192.0 s (#58).
- Hitting a budget only makes CHAIN INCONCLUSIVE, never a false PASS (review RV-3). But the next held-out round could lose CHAIN below its floor.
- **New since U2:** a budget is no longer a pure harness bound. Any arm whose kill comes within `TIME_SAVE_FRAMES` of its `--frames` now makes time saves and cuts (D14).

### 1.6 RV-5 (verified)

- `gates/check_fairness.py:434-441` refuses every `ast.MatchClass` that has positional `patterns`, under both RULE C and RULE A.
- **Plants** on copies (`s53/u2/probe_rv57.out`):
  - `case int(n):` and `case str(s):` both FAIL;
  - the positive control `case Progress(_, _, _, _, _, _, _, t)` FAILS;
  - `int = Progress` followed by `case int(t)` FAILS, and it must stay refused.
- **Binding forms that are not `ast.Name` stores also rebind a builtin's name.** `match type(p): case type() as int: ...` followed by `case int(t)` returns Progress's first field (`s53/u2/review_proof/probe_matchas.out`); `except E as int` binds likewise. Star imports are already refused by purity rule a (`check_purity.py:1120-1121`).
- **AST scan of `417df790`** (`scan_forms.out`, 46 AI-side files): zero class patterns, and zero bindings of a self-matching builtin's name in deciding code.

### 1.7 RV-7 (verified)

- `_check_finally` (`gates/check_purity.py:1233-1251`) refuses `return`, `break`/`continue`, `yield`/`yield from`/`await` in a `finally`. It does not refuse `raise` or `assert`.
- **Plants** (`probe_rv57.out`):
  - `finally: raise ValueError('replaced')` and a bare `finally: raise` both PASS the HEAD gate;
  - the positive control `finally: return 2` FAILS it ([b]);
  - the controls pass: a `raise` in the `try` body, and a `raise` in a def nested in a `finally`.
- A failing `assert` in a `finally` raises `AssertionError`, which REPLACES the exit in flight exactly as `raise` does.
- **Scan:** zero `raise` or `assert` reached from a `finally` body in the 30 play-loop files.

## 2. Decisions (each with the rejected alternative)

- **D1. The U2 table** (`_classify_session`; checked in this order):

  | how the session ended (whose record) | class | `--continue` | change |
  |---|---|---|---|
  | no verdict, no launcher line, run folder present | KILLED | allowed | — |
  | a launcher line names the `run_dir` (whatever the session's `host` says) | judged by the rows below | | NEW (D4) |
  | launcher line `interrupted` | INVOLUNTARY | allowed | — |
  | launcher line `hard_kill` WITH a verdict (`exit_reason` not None) | judged by its verdict, by the rows below | | NEW (D3a) |
  | launcher line `hard_kill` with no verdict | BUDGET ("killed by the launcher at its wall clock: a stuck run, a kill (USER RULING 53)") | refused unless `at_save` | unchanged |
  | `crash`, `frame-budget`, `parked-manual`, `abandoned`, `interrupted`, `interrupted-unresponsive`, each with its host code in the verdict | INVOLUNTARY | allowed | code now required (D3) |
  | `wall-clock` with verdict code 124 and verdict CLEAN (no end line needed) | BUDGET | **allowed** | was refused (no end line) or `at_save` |
  | a reason in `_HOST_CODES` with another verdict code (the brain's text) | NOT CLEAN | refused | NEW (D3) |
  | `play: stopped:`, the launch line's `real_frames` >= `frames`, verdict CLEAN (no end line needed) | BUDGET | **allowed** | was `at_save` |
  | `play: stopped:` that cannot be verified: fewer frames than its budget, a line without the counts, or the verdict-file path (it has no budget) | CHOSEN ("it stopped before its frame budget ran out: its own choice") | refused unless `at_save` | NEW (D2); a 417df790 line reads as before |
  | a BUDGET end whose verdict is not CLEAN | NOT CLEAN | refused | NEW (D3b) |
  | `play: done:` / `play: stuck:` | CHOSEN | refused unless `at_save`; refused with no end line | — |
  | `stray-exit`, `brain-returned`, `purity-*`, `isolation-lost`, `reset-refused`, `mode-restarted`, `refused-*`, anything else | NOT CLEAN | refused (permanent) | — |
  | run folder gone, no launcher line | UNKNOWN | refused | — |
  | harness (and NO launcher line names its `run_dir`), no end line | KILLED | allowed | — |
  | harness, end `chosen` or `stopped_before_restore` | CHOSEN | refused unless `at_save` | — |
  | harness, end `budget` | BUDGET | **allowed** | was `at_save` |
  | harness, any other end | INVOLUNTARY | allowed | — |

  - **The look-through** (`judge_end`, `:354-386`) is unchanged: only a CHOSEN continue that stopped before its restore is looked through.
  - **Every allowed BUDGET judgement's words** end "(USER RULING 53: a session ended by its time or frame limit may be continued from its last save)".
  - **Rejected:**
    - keeping `at_save` for the frame budget and the soft wall clock (ruling 53 replaces the interim);
    - allowing BUDGET only after a time save (that would refuse every session that ended in a long battle);
    - requiring an end line for `wall-clock` (the guard ends that run before the brain can write one);
    - allowing the hard kill always (a refused reset followed by a hang that makes no frames reaches only the hard kill, because `_end_if_refused` runs on frames and on the brain's own exits, `session.py:306, 373, 384`; `time` is allowed in every file, `check_purity.py:450`; and ruling 53 says "not a kill").
- **D2. A `play: stopped:` end is BUDGET only from the host's count (F-U2-1).**
  - `record_launch` gains a keyword `frames` (the `--frames` the launcher gave the child). The line gains `frames`, `real_frames` (the verdict's `counters.real_frames`), `verdict` (the verdict's `verdict`) and `verdict_code` (the verdict's `facts.exit_code`). Each is None without a verdict.
  - `_ran_out(line)` holds when both counts are ints and `real_frames >= frames`.
  - An unverifiable stop is judged as the brain's own choice (CHOSEN, refused unless `at_save`).
  - `LAUNCHES_SCHEMA` stays 1. The fields are additive, and a 417df790 line without them reads as unverifiable, which is exactly the interim. No regression.
  - **What it is:** DEFENCE IN DEPTH. It makes a reload through `stopped:` cost the whole frame budget. It does not make a reload unreachable (section 9, KNOWN LIMITS).
  - **Rejected:**
    - believing the reason text;
    - the AI's `end` line (its `budget` is computed from the same text);
    - a new host fact in `lifecycle.finish` (the instrument already counts the number);
    - NOT CLEAN for an unverified stop (it would end a game for good over a field an older launcher line lacks).
- **D3. A host reason counts only with its host exit code (F-U2-2).**
  - `_HOST_CODES` (private) maps each INVOLUNTARY or BUDGET host reason to its code.
  - **Both paths judge by the instrument's record:** the launch line's `verdict_code`, or `facts.exit_code` on the verdict-file path. The launch line's PROCESS `exit_code` is a cross-check that is REPORTED in the words when it differs, and never refuses on its own (a second thread's `finish` exits with its own code, `lifecycle.py:142-147`). A 417df790 line without `verdict_code` falls back to its process `exit_code`, which agrees in every measured case (soft wall clock 124, `evidence/2026-10-16-step01-T.txt:17-19`; crash 2).
  - `_INVOLUNTARY` keeps its tuple (mutant L13's anchor).
  - **The AST pin** (a unit test) covers EVERY `lifecycle.finish(<reason>, <code>)` and `lifecycle.crash` in `host/session.py` and `host/lifecycle.py`. It resolves Name constants (`_RESET_REFUSED`) and maps every reason either into `_HOST_CODES` or into an explicit NOT-CLEAN set (`stray-exit`, `brain-returned`, `isolation-lost`, `mode-restarted`, `refused-debug-mode`, `refused-http-server`, `reset-refused`). A new host end cannot be forgotten.
  - **Rejected:** leaving it (a forged `wall-clock` would be allowed under U2); judging by the process code (it can differ from the verdict's).
- **D3a. A hard kill is judged by the verdict first (F-U2-5).**
  - When the launch line has `hard_kill` and a verdict reason, the verdict's row decides. A NOT CLEAN or CHOSEN verdict keeps its class; a `wall-clock`/124 verdict of a lingering process is BUDGET by its own row.
  - Only a hard kill with NO verdict uses the hard-kill row, which keeps the interim (`at_save`).
  - **Rejected:** the row first, as at HEAD (a `reset-refused` verdict followed by a lingering process and a hard kill would be judged by the kill).
- **D3b. A BUDGET end needs a CLEAN verdict (F-U2-3).**
  - A `wall-clock` or a verified `stopped:` whose launch line's `verdict` (or the verdict file's) is not `CLEAN` is NOT CLEAN.
  - INVOLUNTARY rows are unchanged. A crash whose verdict is UNVERIFIED (e.g. 0 real frames) stays continuable; that is a pre-existing limit, stated in section 9.
  - **Rejected:** NOT CLEAN for every non-CLEAN host end (an early crash with 0 frames would end a game for good).
- **D4. The harness branch applies only when NO launcher line names the session's `run_dir` (F-U2-4).**
  - The in-process harness (`host: "harness"`) is the TEST host, with no lifecycle and no verdict, so BUDGET there is the end line's `budget`. That is the stated limit, as for FX5.
  - **Rejected:** trusting the session's `host` field first (it is AI-written); refusing harness BUDGET ends (U2-TIME exercises exactly this row).
- **D5. What does not change:**
  - CHOSEN (the deferred legendary exception of ruling 52 stays unbuilt);
  - NOT CLEAN, which is permanent (ruling 53's reset answer);
  - UNKNOWN; KILLED;
  - the look-through and its count;
  - `MAX_LOSSES` across processes.
  - R15's supervisor may now relaunch after a frame-budget or soft wall-clock end too (doc only; R15 is not built).
- **D6. The fourth moment: `time` (ruling 53 adds it to ruling 51's three).**
  - `DUE_KINDS` gains `"time"`. Its due lives in its OWN field, `goal_memory.time_due` (GOAL_RESET), not in the `save_due` slot. So `_make_due` (a centre, a moment, a leader) never overwrites it, and a time due never overwrites theirs.
  - Its place is ANY free overworld screen (the policy's `_blocker`). It never expires on leaving a map.
  - Any save satisfies it: `record_save`/`saved_state` clear `time_due` as well.
  - **Rejected:**
    - the single slot (a centre due made after "nearly up" would replace it and then expire unsaved, and the once-per-process flag would stop it being made again);
    - only at a Pokémon Center (the walk would eat the time);
    - a fourth moment without saying so (the README and `06` name ruling 53).
- **D7. The two stages and their margins.**
  - **When a stage may be made.** Each is made once per process (a GOAL_RESET flag), and only when all hold:
    - there is something to lose (D8);
    - `frames_left >= SAVE_FRAMES_NEEDED`. A due that can never be saved is never made, so a 2,620-frame child B or LAUNCH makes no due and logs nothing new.
  - **"nearly up"** is made when frames left <= `TIME_SAVE_FRAMES` = `SAVE_FRAMES_NEEDED` + `REACH_FRAMES`.
    - `REACH_FRAMES` = 2 x the widest REACH measured from the AI's own log in the development U2-TIME and U2-WALL rows. The reach is the frames from "a save is due: ... nearly up" to that save's START (due → cut, plus cut → START).
    - The busy-stretch proxy (`SaveWatch`'s busy recorder, the action-record gaps of 1.3) is a CROSS-CHECK: STOP if any measured reach exceeds 2 x the widest proxy.
    - PROVISIONAL value: 13,500 (2 x (6,646 + 45 + 30)), so `TIME_SAVE_FRAMES` is provisionally 17,100.
  - **"ends now"** is made when frames left <= `LAST_SAVE_FRAMES` = `SAVE_FRAMES_NEEDED` + `LAST_REACH_FRAMES`.
    - `LAST_REACH_FRAMES` = 2 x the widest cut-to-START lag measured on a free screen. PROVISIONAL value: 300.
  - **Both stages OBEY `SAVE_MIN_MINUTES`.** A recent save covers them: the stage is dropped and that is said (`_wait`).
    - Reason: a continue identifies the loaded save only by the CONTINUE window's H:MM, the NEWEST line within `MATCH_MINUTES` (`game_memory.py:564-570`). Save lines are written at the START of the write. Two stamps must be at least 2 x `MATCH_MINUTES` + 1 = 3 minutes apart, or a torn newer line (a kill mid-write) is chosen over the save the cart holds. The `skills/saving.py:606-608` stop is then CHOSEN and not retryable, which ends the game for good.
  - **Why two stages:** battles are 31-47% of a run's frames.
    - One late trigger would miss its save whenever a battle or a menu is under way.
    - One early trigger would always lose the play after it (about `TIME_SAVE_FRAMES` − 1,300 frames).
    - "ends now" adds a save exactly when "nearly up" did not save in the last 3 game minutes: it was covered by an earlier save, there was nothing to lose then, or its save came early.
  - **The price, stated (provisional arithmetic; measured live, step 7):** the play after the last save is at most about max(`TIME_SAVE_FRAMES` − a save's frames, 3 game minutes + `LAST_SAVE_FRAMES`) ≈ 15,800 frames (about 4.4 game minutes). It is usually much less when the session is free at its last moment. Every continue tells what it dropped (D13).
  - **Rejected:**
    - "ends now" exempt from the gap (the save-identity ambiguity above);
    - a single trigger, early or late;
    - a decision-point trigger with no cut;
    - repeated time saves every 3 minutes;
    - tuning the margins to make an arm pass (never: they are measured from the AI's own play, at 2x).
- **D8. "Something to lose" = an event after the last save point.**
  - **The events:**
    - an entry of `report["progress"]` (each carries `frame`, `mode.py:825`);
    - a milestone passed (`report["milestones"]`, each with `frame`, `:1036`);
    - a battle lost since the last save. The play brain keeps `report["losses_at_save"]`, set at `record_save` and, on a continue, to the restored losses; a battle was lost when `report["losses"]` is above it.
  - **The last save point** is `last_save["frame"]` of the policy's memory: restored on a continue, and None in a new game with no save (then: since the session's first look).
  - It is person-fair: on-screen progress and milestone ids only.
  - A lost battle counts ON PURPOSE. Otherwise a continue would undo it for free.
  - **Rejected:** frames since the save (it would save for nothing); the world memory's map count alone (it misses battles, levels, items and losses).
- **D9. The CUT, and its transparency.**
  - **The hook.** The `Navigator` gains `time_stop: Callable[[Observation], str | None] | None` and a latch `cut: str | None`.
    - `Navigator.run` asks `time_stop` on a FREE look, AFTER the new-changes block and AFTER `if intent.done(look): return "done: ..."` (`brain/navigator.py:1253`). A walk that arrived on that very look returns `done:`.
    - `roam_train` asks it beside `roam_stop` (`skills/roam_train.py:275`).
  - **When it fires.** It returns a reason only when block 0 WOULD choose the time save now. The predicate is the SAME as block 0's: a pending `time_due`, `SavePolicy.may_save`, AND `manager._allowed("save:time")` (the goal's cooldown). It needs at least `SAVE_FRAMES_NEEDED` frames left, so no 2,620-frame run ever cuts.
  - **The latch.** When it fires, `Navigator.cut` LATCHES the reason. Every later `run`/`roam_train` in the same goal returns `time: <reason>` at once. The play loop clears the latch after `pursue`.
  - **A failed time save consumes its stage.** A `save:time` goal whose outcome is not "saved" clears `time_due` and says so. The other stage may still be made. So nothing can cut goals while a save is cooling down.
  - **Never cut:** a battle, a scene, a menu (`nav.handle` plays it to its end), or the settle before "done" (D12 (c)).
  - **Transparent in the GOAL RUNNER.** Every runner path that marks something given up checks `nav.cut` and skips that bookkeeping on a cut. A walk ended by the cut is treated as an INTERRUPTION:
    - `pick_up`: no `tried_items.add`, and the cut walk is not counted in `item_tries`;
    - `_back_to_ball`;
    - the `budget` extension parser (`:2307`, which sees `time:`, not `budget`, so it does not extend);
    - every `blocked`/`exhausted`/`asked_rounds`/`scene_given_up` marker.
  - **Transparent in `_play`** (`mode.py:906-931`): `report["goals"]` records the goal with `ok` None and outcome "cut: ...", and its frames go to `manager.spent`. There is no `manager.outcome`, no `after_goal` and no `_after_heal`.
  - **Measured, not argued (step 3):** for each goal kind, every GOAL_KEEP field of `manager.memory`, and the world memory's markers, are diffed before and after a cut goal. STOP on any change that a battle interruption of the same goal would not make.
  - **Rejected:**
    - a `time_stop` predicate looser than block 0's (with `save:time` in cooldown, every goal would be cut at its first free look for 12 decisions: idle play);
    - closing the goal's generator from outside;
    - counting the cut as a failure;
    - cutting a battle.
- **D10. Where the time save is chosen.**
  - `next_goal` gains a block 0 before HEAL (`brain/goals.py:1205`): `self._save_goal(look, here_const, milestone, kinds=("time",))`, through `_allowed` and its cooldown. It is chosen while HURT.
  - Block 1b (`:1248-1254`, "never while hurt") is unchanged for ruling 51's three moments.
  - **Rejected:** the time save in block 1b (a hurt party would walk to a centre first while the time runs out).
- **D11. The wall limit: what the AI knows, and how.**
  - `HandsOptions.wall_deadline: float | None = None`, read by `from_env` from `ENV_WALL_DEADLINE`.
  - `HandsBrain` has CLASS-LEVEL defaults `_play_started = None` and `_wall_deadline = None`, and reads `getattr(self.options, "wall_deadline", None)`. The play-loop tests build the brain with `__new__` (`gates/test_goals.py:910-916`).
  - Its pace is `pad.frames / elapsed`, once `PACE_MIN_SECONDS` (2.0, provisional) have passed.
  - The wall part is `(deadline − time.time()) × pace / PACE_SAFETY`. `PACE_SAFETY` is 2, checked against the widest measured ratio of a run's overall pace to its slowest 5-second window at 12 jobs.
  - With no deadline, or before the pace is known, the wall part is unbounded.
  - `_frames_left` = min(budget left, wall part). The commit guard thereby also becomes wall-aware.
  - It is person-fair: the operator's session limit is not game state.
  - **Rejected:** not telling the brain; a host-to-brain callable (a new host door); the hard deadline.
- **D12. Interplay (each pinned by a test, section 4):**
  - (a) **The target check comes first** (`mode.py:829-838`, before `next_goal` at `:878`). A time save never turns a REACHED target into "stopped".
  - (b) **A pending time due is saved by `_save_before_done`** (`mode.py:604-630`). It reads `time_due` beside `due_now`, when the save fits `DONE_BUDGET_MARGIN`, and its frames go through `_settle_frames`.
  - (c) **The settle before "done" is never cut.** It reaches only `play_out` → `nav.handle` (`skills/story.py:148-156`), never `Navigator.run` or `roam_train`. Pinned by a FAULT (mutant T12: `play_out` consults `time_stop`) and a CONTROL.
  - (d) **A save never overruns the budget.** It never starts with fewer than `SAVE_FRAMES_NEEDED` frames left, and no YES is pressed with fewer than `COMMIT_FRAMES_NEEDED`.
  - (e) **The AI PLAYS ON after a time save** (RULING 37 Q6: never idle).
  - (f) **A save is transparent** to the curiosity row and the grader's streaks, and its spans leave the errand share.
  - **Its cost, stated:** a save's frames (about 1,300) can push a target past the budget, as any save can.
  - **Rejected:** putting the game down after the time save.
- **D13. What a continue tells it drops (ruling 53).**
  - **THE SET.** The sessions after the LATEST session whose `continued_from` is the save, or after the save's own line when nothing continued from it yet. These are the events that THIS continue undoes; earlier drops were told by earlier continues. Frames, maps and lost battles are all counted over this set. `lost` = `undone_losses`, which walks the same live history.
  - **The `end` line gains `play_time` and `where` of its last look** (`write_end(..., look)`, the stamp through `_stamp_of`). These are written for the launcher's sentence; the AI never reads them back.
  - **`MemoryBook.dropped_after(save_id) -> dict | None` (AI-readable, memory file only)** returns, per session in the set:
    - `frames`: the end line's `frame` minus that session's `frame_base` (for the save's own session, minus the save's `frame`), or None ("not recorded") when the session has NO end line;
    - `at_save`: the save's play time;
    - `at_end`: the play time from the NEWEST session's own end line, or None;
    - `lost`;
    - `sessions`.
    - It never derives frames from a later session's stamps.
  - **`memory_check` (launcher-side)** puts the drop in `ContinueCheck.dropped`, a new last field. It adds:
    - `host_frames`: per session, from its launch line's `real_frames` (the HOST's count). For the save's own session, minus the save's offset into it, `save.frame − frame_base`, with the frame-relation measured in step 2. None without a launch line.
    - `maps`: the map consts of each session's last `run_dir/world.jsonl` snapshot whose `first_frame` > the save's `frame` (for the save's own session) or that are new to that session. Named "(the AI's own record)"; "not known" without a world file, never "none".
  - `cmd_run` prints the drop.
  - **The AI's after-arrival line** (built in `_on_main_menu`, `skills/saving.py:618-621`) and its session line's `dropped` tell `frames` (or "not recorded") and `lost`. NO play time and NO map (D19; ruling 40).
  - Both schemas stay 1.
  - **Rejected:**
    - a cumulative frame count beside a live-history loss count (two different sets in one sentence);
    - "latest stamp − save frame" (it undercounts the very ends U2 adds);
    - play times in the AI's line (no door purpose; not on screen);
    - the AI reading a world file (D19).
- **D14. RV-3.**
  - Development #62 runs the whole plan at 12 jobs at once.
  - `CHAIN_B_FRAMES` = `CHAIN_BUDGET_BASE` + 2 x the widest ARRIVAL-TO-KILL ever measured (#57-#62, each row re-read in that unit). `CHAIN_B_TIMEOUT` = max(300, 2 x the widest wall). The same holds for `CHAIN_OLD_*`.
  - **New rule, enforced in `registered_numbers` and the selftest:** for every killed arm, budget − the widest measured kill frame (in the budget's own count) >= 2 x `TIME_SAVE_FRAMES`. Otherwise the arm's play would be steered by the time logic.
  - **Rejected:** development values only; "budgets can only make an arm uncounted" (no longer true since D7).
- **D15. RV-5.** Rule D3 (d) skips an `ast.MatchClass` only when all of these hold:
  - its `cls` is a bare `Name` in `SELF_MATCHING_BUILTINS` (`bool`, `bytearray`, `bytes`, `dict`, `float`, `frozenset`, `int`, `list`, `set`, `str`, `tuple`);
  - it has exactly ONE positional sub-pattern and no keyword patterns;
  - the module binds that name nowhere.

  The module pre-pass collects every binding form:
  - `ast.Name` Store/Del;
  - function and lambda parameters, including `*args`/`**kw`;
  - def and class names;
  - import aliases;
  - `ast.MatchAs.name`, `ast.MatchStar.name` and `ast.MatchMapping.rest`;
  - `ast.ExceptHandler.name`;
  - `global`/`nonlocal` declarations;
  - walrus targets.

  Star imports are already refused (purity rule a). A module that imports `builtins` gets no exception. The message drops "the play time" for the generic case.
  - **Rejected:** `__match_args__` (not knowable in an AST gate); `ast.Name`-only collection (`case type() as int` passes it).
- **D16. RV-7.** `_check_finally` also refuses an `ast.Raise` and an `ast.Assert` reached from a `finally` body. A nested def/lambda/class is its own scope, and a `raise` inside a `try` nested in the `finally` is refused too. Message: "a `raise` (or a failing `assert`) in a `finally` replaces the exit in flight".
  - **Rejected:** a bare `raise` only; leaving `assert` open.
- **D17. The live proof's shape.**
  - **U2-BUDGET** reuses LAUNCH's own end, a real-launcher `play: stopped:` that cannot be at a save (2,620 frames < 3,600). `cmd_launch` gains a freeze after its launcher run.
  - **U2-WALL** is its own real-launcher run, ending on the soft wall clock.
  - **U2-TIME** is a harness new game: only the harness's `SaveWatch` sees a held free screen and the flash write.
  - **Every continue step is `child_b`** (the REAL `memory_check` and `seed_profile`, then `ArrivalWatch`). `child_b` records `ContinueCheck.dropped` whole.
  - **Rejected:** a separate step 1 for U2-BUDGET; continuing through the launcher; a live hard-kill arm (the row is the interim's, unchanged, and unit-proven).
- **D18. Seeds.**
  - The ledger (61 entries) uses 1-1384, 5301-5304, 5351-5355, 5361-5365, 5401-5406, 5451-5484 (in tens), 5501-5506, 5551-5584 (in tens) and 9901-9933.
  - `git grep` at `417df790` finds the 56xx numbers only as line numbers and counts, never as a seed.
  - The ranges: development #62 5601-5606; held-out 5651-5654; re-run 5661-5664; fix round 5671-5674; verification 5681-5684; spare 5691-5694.
  - Each range is re-checked with the follow-up's seed classifier (`s53/r1f/build/s3-graded/seed_check3.py`) when it is registered.

## 3. The parts (file by file; anchors at `417df790`)

### (a) `ai_player/host/launcher.py` (D1-D4, D13)

- **The comment at `:255-261`:** BUDGET is no longer "interim". It names ruling 53, the host-record rule, and the hard kill's reading.
- **New private names:**
  - `_HOST_CODES` and `_HOST_NOT_CLEAN` beside `_INVOLUNTARY` (`:263`, which stays byte-identical);
  - `_ran_out(line)`.
- **`ContinueCheck`** (`:266-277`) gains `dropped: dict | None = None` as its last field.
- **`record_launch`** (`:309-326`) gains a keyword `frames: int | None = None`. The line gains `frames`, `real_frames`, `verdict` and `verdict_code`.
- **`_classify_session`** (`:416-461`), per D1:
  - it first looks for a launch line naming `run_dir`; the harness branch runs only without one;
  - the hard kill with a verdict reason falls through to the verdict rows (D3a);
  - the code check uses `verdict_code` (or `facts.exit_code`), with a process-code mismatch reported in the words;
  - D3b's CLEAN check;
  - the fail-closed "no end line" (`:458-460`) applies to CHOSEN only.
- **`memory_check`** (`:464-489`): after `undone` (`:485`) it builds `dropped` (the book's `dropped_after`, plus `host_frames` and `maps` from `dropped_maps`). Both returns carry it. **`:486-487` (`if not allowed:` / `return ContinueCheck(False,`) stay byte-identical (L7's anchor).**
- **New `dropped_maps(book, sessions) -> list | None`:** read-only, launcher-side.

### (b) `ai_player/__main__.py` (D2, D13)

- `:218`: `record_launch(game, run_dir, result, read_verdict(run_dir), frames=args.frames)`. S34 is re-anchored (section 6).
- `:169-176`: the state note adds the drop. For example: "this continue drops: session 3 (2,620 frames by the host's count; 2,598 by the AI's record), from play time 0:18 at save 2 to 0:19 at session 3's end, 0 battles lost (undone), maps first stood on after it: none (the AI's own record, ...world.jsonl)". Or: "... 'not recorded' (no end line: a wall-clock end)".

### (c) `ai_player/game_memory.py` (D13)

- **`end_line`** (`:476-490`) gains `look=None`, adding `"play_time"` and `"where"`. **`:486` `held = ...` stays byte-identical (FX2's anchor).**
- **`write_end`** (`:823-824`) passes `look`.
- **New `MemoryBook.dropped_after(save_id)`**, beside `undone_losses` (`:624-631`), over D13's SET.
- The module docstring's "frames are monotonic" premise is corrected for ends with no end line.
- `GOAL_RESET` (`:157-172`) gains `time_due`, `time_due_made` and `last_due_made`.

### (d) `ai_player/options.py` (D11)

- `HandsOptions` (`:350-401`) gains `wall_deadline: float | None = None`.
- `from_env` reads it from `ENV_WALL_DEADLINE`.
- `RunOptions` is unchanged.

### (e) `ai_player/brain/saving.py` (D6-D8)

- **`DUE_KINDS`** (`:58`) gains `"time"`.
- **New constants**, each with its measurement in a comment:
  - `REACH_FRAMES` (PROVISIONAL 13,500) and `TIME_SAVE_FRAMES`;
  - `LAST_REACH_FRAMES` (PROVISIONAL 300) and `LAST_SAVE_FRAMES`.
- **New `after_time(frames_left, since) -> bool`:**
  - it returns at once when `frames_left < SAVE_FRAMES_NEEDED` or `since` is empty;
  - "ends now" is checked first, then "nearly up";
  - it sets `goal_memory.time_due` (`{"kind": "time", "stage": ..., "why": ...}`) and the stage's flag, and says the line.
- **New `time_due_now(look, frames_left)`:** the pending time due, if any. A gap-covered due is dropped and said, through `_wait` (no exemption).
- **New `time_choice(look, frames_left) -> SaveChoice | None`:** key `save:time`. Block 0 and `time_stop` both use it.
- **New `time_failed(why)`:** clears `time_due` and says so.
- **`saved_state`/`record_save`:** `time_due` becomes None.
- **`_make_due`, `due_now`, `next_save` and `_blocker`:** unchanged.
- The module docstring names ruling 53's fourth moment.

### (f) `ai_player/brain/goals.py` (D9, D10)

- **`_Memory`** gains `time_due: dict | None = None`, `time_due_made: bool = False` and `last_due_made: bool = False` (GOAL_RESET).
- **`next_goal`:** block 0 before `# 1. HEAL` (`:1205`).
- **`_save_goal`** (`:1415-1423`) gains `kinds: tuple[str, ...] | None = None`. With `("time",)` it uses `time_choice`.
- **New `time_ready(look) -> str | None`** for `time_stop`: `time_choice` and `_allowed("save:time")`.
- **The runner's bookkeeping** (`:2125-2145`, `:2205-2222`, and every `tried_items`/`blocked`/`exhausted`/`asked_rounds`/`scene_given_up` marker; the builder lists them by grep in step 3): `if nav.cut: return outcome` before the marker, and the cut walk is not counted in `item_tries`.
- **A `save:time` goal not "saved"** → `saving.time_failed(...)` (in `_play`, beside the save goal's outcome).
- **Block 1b** (`:1252`) is unchanged.

### (g) `ai_player/brain/navigator.py` and `ai_player/skills/roam_train.py` (D9)

- **`Navigator.__init__`** (`:715-725` region): `self.time_stop = None` and `self.cut = None`.
- **`run`** (`:1194`):
  - its first statement after setup: if `self.cut`, return `f"time: {self.cut} ({self.summary()})"`;
  - after `if intent.done(look): return ...` (`:1253`), on `nav_free(look)` only: ask `time_stop`; if it gives a reason, latch it and return the same.
- **`roam_train`** (`:275`): beside `roam_stop`, the same check, returning `f"roam: time: {why}; {report.line()}"` with the latch set.

### (h) `ai_player/mode.py` (D8, D9, D11, D12, D13)

- **Class-level defaults:** `_play_started = None` and `_wall_deadline = None`. They are set in `play`.
- **`_frames_left`** (`:546-548`): min(budget left, `_wall_frames_left(hands)`).
- **New `_since_save(report) -> list[str]`** (D8), with `report["losses_at_save"]`.
- **`_start_saving`** (`:521-544`): `nav.time_stop = lambda look: self._time_stop(hands, report, look)`. The `_time_stop` method returns `manager.time_ready(look)` after `_time_check`.
- **New `_time_check(hands, report)`:** called once per pass of the play loop before `next_goal` (`:878`), and inside `_time_stop`.
- **In `_play` after `pursue`** (`:906`): `cut = nav.cut; nav.cut = None`. A cut takes D9's transparent path (skip `:916`, `:918`, `:930`). A `save:time` goal not saved → `time_failed`.
- **`_save_before_done`** (`:604-630`) also takes a pending `time_due`.
- **`_end_memory`** (`:651-661`): `write_end(..., look=last)`.
- **`_continue`** (`:481-519`): the session line gets `dropped` (frames or "not recorded", lost).

### (i) `ai_player/skills/saving.py` (D13)

- **`_on_main_menu`** (where `continue_game`'s result lines are built, `:618-625`): `dropped = book.dropped_after(record["id"])`. Its line: "this continue drops F frames of play after save k" (or "frames not recorded: the last session ended without its end line"), followed by the existing undone sentence. No play time and no map.
- **`ContinueResult`** gains `dropped: dict | None = None`.

### (j) `ai_player/gates/check_purity.py` (D16)

- **`_check_finally`** (`:1233-1251`): `ast.Raise` and `ast.Assert` → `_fail_exit`.
- The module docstring (`:72-78`) names them.

### (k) `ai_player/gates/check_fairness.py` (D15)

- `:434-441`: the self-matching-builtin exception, with the binding pre-pass of D15.
- The docstring (`:33-43`) says so.

### (l) `ai_player/gates/live_r1.py` (section 5; D14)

- **`HELD_OUT`** (`:113`) becomes `(5651, 5654)`.
- **Arms:** `ARMS_NEW` (`:124`) gains `U2-BUDGET`, `U2-WALL` and `U2-TIME`. `OLD_OF` (`:125`) gains `U2-BUDGET-OLD` (U0), `U2-WALL-OLD` (U0) and `U2-TIME-OLD` (T0).
- **`cmd_launch`** (`:1546-1633`): `row["frozen_after"] = freeze_profile(...)`.
- **`child_b`** (`:819`): records `check.dropped` in its row.
- **New functions:** `cmd_u2budget`, `cmd_u2wall`, `cmd_u2time`, `time_window(control_row)`, `grade_u2budget`, `grade_u2wall` and `grade_u2time`.
- **New constants:** `U2_OLD_EDITS`, `T0_EDITS`, `U2_TIME_OFFSET`, `U2_GAP_FRAMES`, `U2_WALL_SECONDS`, `U2_WALL_FRAMES`, `U2_WALL_TARGET` and `U2_TIMEOUT`.
- **`SaveWatch`** (`:384`) gains a BUSY recorder (the cross-check of D7).
- **The new arms are added to** `discriminators` (`:2329`), `registered_numbers` (`:2518`, with D14's rule) and `selftest` (`:2580`).
- **Re-set (D14):** `CHAIN_B_FRAMES`, `CHAIN_B_TIMEOUT`, `CHAIN_OLD_FRAMES` and `CHAIN_OLD_TIMEOUT` (`:154-170`).
- **New FAULTS:**
  - `u2_drop_ignored`: B1 skips the drop;
  - `u2_drop_self_graded`: B1 grades frames against the memory file instead of the host's count;
  - `u2_stop_unverified`;
  - `u2_time_free_ignored`;
  - `u2_time_window_first`;
  - `u2_wall_no_code`;
  - `u2_wall_stamp_only`: W2 matches the save by H:MM alone, without the content identity.

### (m) `ai_player/README.md`

- **"Saving and CONTINUE"** (`:752-829`) gains:
  - the U2 table and the hard kill's reading;
  - the time moment, its two stages, its own due field, the gap and why;
  - the cut and its transparency;
  - the wall knowledge;
  - the drop sentence and its ONE set;
  - the new arms;
  - RV-3, RV-5 and RV-7.

  KNOWN LIMITS is rewritten (section 9).
- **"Fault and control switches"** (`:699` region): the "(a COPY)" rows for U0 and T0.

## 4. Unit tests (a FAULT and a CONTROL for every guard)

| guard | test (file: class.method) | FAULT | CONTROL |
|---|---|---|---|
| D1 table | `test_saving: LauncherContinueTests.test_the_end_classes` (`:2092`; its `verdict` helper gains `exit_code` and `verdict`; its launch lines gain `exit_code`, `verdict_code`, `verdict`, `frames`, `real_frames`) | harness `budget` not at a save → allowed (U1 refuses); a verified launcher `stopped` not at a save → allowed (U2a refuses); `wall-clock` 124 CLEAN, no end line → allowed (U3 refuses); a hard kill with no verdict, not at a save → REFUSED (U4 allows) | CHOSEN not at a save → refused; CHOSEN with no end line → refused (L10 re-worded); `reset-refused` → NOT CLEAN; UNKNOWN; KILLED; INVOLUNTARY with codes → allowed; a hard kill at a save → allowed |
| D2 forged stop | `LauncherContinueTests.test_a_stop_before_the_budget_is_the_ais_own_choice` | `stopped` with `real_frames` 1700 of 2620 → CHOSEN, refused (U5 allows); `real_frames` == `frames` → BUDGET allowed (U8, `>`, refuses) | a 417df790 line without `frames` → refused unless at a save; at a save → allowed |
| D2 recorded | `LauncherContinueTests.test_the_launch_line_carries_the_counts` (through `record_launch` with a fake verdict) | U7 (fields not written) → a genuine stop reads as unverifiable, refused | a verdict-less child → all four fields None |
| D3 codes | `LauncherContinueTests.test_a_host_reason_needs_its_host_code` | `crash`, `wall-clock`, `abandoned` and `interrupted` with verdict code 0 → NOT CLEAN, refused (U6 allows); verdict code 124 with process code 0 (a second-thread finish) → judged by the verdict, mismatch told (U9, the process code, refuses) | each with its host code → its class |
| D3 pin | `LauncherContinueTests.test_the_host_codes_match_the_host` (AST over `host/session.py` and `host/lifecycle.py`, Name constants resolved) | a COPY of `session.py` with a planted `finish("new-end", EXIT_PARKED)` fails | the real files pass; every reason maps to `_HOST_CODES` or `_HOST_NOT_CLEAN` |
| D3a verdict first | `LauncherContinueTests.test_a_hard_kill_is_judged_by_its_verdict_first` | `hard_kill` with `exit_reason` `reset-refused` → NOT CLEAN; with `play: done:` not at a save → CHOSEN refused (U4b, the row first, judges it BUDGET) | `hard_kill` with a `wall-clock`/124 CLEAN verdict → BUDGET allowed; with no verdict → the hard-kill row |
| D3b clean | `LauncherContinueTests.test_a_budget_end_needs_a_clean_verdict` | `wall-clock` 124 with verdict BREACH → NOT CLEAN (U10 allows) | the same with CLEAN → allowed; a `crash` with UNVERIFIED → INVOLUNTARY (unchanged, stated) |
| D4 branch | `LauncherContinueTests.test_a_launcher_run_is_judged_by_its_line_whatever_host_says` | a session line `host: harness` whose `run_dir` a launch line names, end line `stopped:` and `real_frames` 1700 → CHOSEN, refused (U11, the host field first, allows) | a genuine harness session (no launch line) → the harness rows |
| D5 look-through | the existing `test_a_continue_that_stopped_before_its_restore_is_looked_through` and `test_the_look_through_is_counted_and_told` | unchanged | unchanged |
| D6 own field | `test_saving: SavePolicyTests.test_u2_a_time_due_survives_other_dues` | "nearly up", then a centre due that expires on leaving its map → the time due is still pending and saved (T15, the single slot, loses it); a time due never expires on leaving a map (T1x) | a centre due still expires; a save clears both |
| D7 stages | `SavePolicyTests.test_u2_the_two_time_stages` | at `TIME_SAVE_FRAMES` with progress → "nearly up" made once (T2 makes it twice); at `LAST_SAVE_FRAMES` with a save 1 game minute ago → "ends now" covered, dropped, said (T3, the exemption, makes the save) | more frames left → no due; nothing to lose → no due; fewer than `SAVE_FRAMES_NEEDED` left → no due and no line (T18 makes one) |
| D7 identity | `test_saving: MemoryFileTests.test_u2_two_saves_within_a_minute_are_never_made` | with T3 applied, two save lines 1 minute apart and the newer torn → `match_time` picks the torn line (the hazard shown) | without T3, the policy never makes the second save |
| D8 since | `test_goals: PlayLoopTests.test_u2_something_to_lose` | progress before `last_save.frame` only → no due (T9 makes one); a loss after the save (`losses` > `losses_at_save`) → a due | a continue with no progress → no due; a new game with progress and no save → a due |
| D9 cut | `test_world` (where `Navigator.run` is tested) `test_u2_the_cut_on_a_free_look_only` | `time_stop` gives a reason → `run` returns `time:` on the first FREE look, and a second `run` returns at once (T4 walks to its budget; T5, no latch, walks again); an intent done on the cut look → `done:` (T17, cut before `done`, returns `time:`) | `time_stop` None → unchanged; a battle on screen → played to its end before the cut |
| D9 roam | `test_u2_roam_stops_for_the_time` | `roam_train` returns `roam: time:` (T6 removes the check) | `roam_stop` behaviour unchanged |
| D9 transparent (loop) | `PlayLoopTests.test_u2_a_cut_goal_is_neither_failure_nor_mark` | a cut curiosity goal leaves `fails`, `exhausted`, `blocked` and `curious_row` as they were (T7 changes `fails`) | an uncut failed goal still counts |
| D9 transparent (runner) | `PlayLoopTests.test_u2_a_cut_pick_up_gives_nothing_up` | a cut `pick_up` and a cut `_back_to_ball` leave `tried_items` and `item_tries` unchanged (T16 adds the ball) | a non-cut unreachable walk still gives it up |
| D9 predicate | `PlayLoopTests.test_u2_no_cut_while_the_time_save_is_set_aside` | `save:time` in cooldown with a time due pending → no goal is cut (T14 cuts every goal) | out of cooldown → the cut |
| D9 failed | `PlayLoopTests.test_u2_a_failed_time_save_ends_its_stage` | a time save that fails (NO on a `kept` cart) → `time_due` cleared, said, no further cut (T13 keeps it) | a successful time save → recorded |
| D10 block 0 | `PlayLoopTests.test_u2_the_time_save_comes_before_heal` | a hurt party with a time due and `may_save` → goal `save:time` (T8 chooses `heal`) | a `center` due while hurt → heal first |
| D11 wall | `R1PlayTests.test_u2_frames_left_knows_the_wall` (a fake clock and pad) | deadline 10 s at pace 1000 → `_frames_left` = min(budget left, 5000) (T10 ignores the wall) | no deadline → budget left; before `PACE_MIN_SECONDS` → budget left; a brain built with `__new__` → budget left |
| D12 (a)/(b) | `PlayLoopTests.test_u2_a_reached_target_ends_done_and_saves_a_pending_time_due` | target proof true and a time due pending → "done", the end save made (T11 skips it) | no due → "done", no end save |
| D12 (c) | `PlayLoopTests.test_u2_the_settle_is_never_cut` | a pending time due during the settle → no `time:` outcome (T12, `play_out` consulting `time_stop`, is cut) | the same due IS cut on a free look in `Navigator.run` |
| D13 drop | `test_saving: MemoryFileTests.test_u2_dropped_after` | a wall-clock session (no end line) that played after the save → `frames` None "not recorded", never 0 (D1m says 0 / latest stamp); `at_end` from the newest session only (D5m takes an older end line); two continues from one save → only the newest session counted, for frames, maps AND lost alike (D6m, cumulative, counts both) | a continue right after a save, with an end line → frames 0 |
| D13 end line | `test_the_end_line_says_chosen_budget_and_at_save` (`:862`) extended | an end line carries `play_time` and `where` (D3m drops them) | an old end line without them reads (schema 1) |
| D13 host | `LauncherContinueTests.test_u2_the_drop_uses_the_hosts_count_and_names_the_maps_after_the_save` | `host_frames` = the launch line's `real_frames` (minus the save's offset in its own session); maps with `first_frame` <= the save's frame are not named (D2m names them); no world file → "not known" | a world file with one new map → named |
| D13 AI side | `R1PlayTests.test_u2_the_ais_continue_tells_the_drop_and_no_map` | the session line's `dropped` = the book's numbers (D4m drops it); no map const and no play time appears in the AI's line or session line | a continue with nothing after the save |
| D15 | `test_safety_gates: FairnessTests.test_the_play_time_is_read_only_through_its_doors` (`:477`) gains plants | each FAILS: `case Progress(_, ..., t)`; `int = Progress` then `case int(t)`; `def f(int): ... case int(t)`; `case type() as int` then `case int(t)`; `except E as int` then `case int(t)`; `case int(a, b)`; `case int(x=1)` (S46g, the rebinding check removed, passes `int = Progress`; S46h, only `ast.Name` collected, passes `case type() as int`) | `case int(n)`, `case str(s)` and `case tuple(t)` pass; the real package passes |
| D16 | `test_check_purity: PlayLoopExitTests.test_the_play_loop_cannot_exit` (extend `EXIT_PROBES`; X19 and X20 exist, `:795-797`) | X21 `finally: raise ValueError(...)` in `skills/`; X22 a bare `finally: raise` in `brain/`; X23 `finally: try: f() except OSError: raise` in `hands/`; X24 `finally: assert ok` in `world/`: each fails "b" (S40h, the Raise rule off; S40i, the Assert rule off) | a `raise` in the `try` body and in a def nested in a `finally` pass; the real package passes |

- **Every new test names its FAULT and CONTROL halves in its docstring.** `live_r1`'s selftest covers its new grader faults.
- **The existing tests that now run inside a time window must be re-confirmed (step 3).** These are every PlayLoopTest with a memory file and a budget <= `TIME_SAVE_FRAMES` (`test_goals.py:1326` frames 500, `:1344` 5000, `:1781` 4000, `:5045` 10,000, and any the builder's grep finds). Each one's assertions are re-derived under the new logic and said in the step-3 notes, never discovered as "unrelated" red.

## 5. The live proof

### 5.1 Arms (new; every existing arm runs unchanged)

| arm | built from | stop / kill | expectation (from the arm's OWN record) |
|---|---|---|---|
| **U2-BUDGET** | LAUNCH's `frozen_after` (its real-launcher continue of K-AFTER's set, ended `play: stopped: not finished within 2620 frames`) | none: `child_b` (REAL tree) continues it | `memory_check` allowed, class BUDGET; arrives at S2; the drop is told |
| **U2-BUDGET-OLD** | the same frozen set | `child_b` from mutant U0's tree (the interim table) | refused, class BUDGET; `memory.jsonl` byte-identical |
| **U2-WALL** | a copy of K-AFTER's frozen set in its own mirror build root | step 1: the REAL launcher `run --continue --frames U2_WALL_FRAMES --wall-seconds U2_WALL_SECONDS`, with `AI_PLAYER_TARGET` = `U2_WALL_TARGET` (`ch4_roxanne`, out of reach in the wall), ends on the soft wall clock; freeze. Step 2: `child_b` (REAL tree) | allowed, class BUDGET; arrives at the save the cart's FILE holds |
| **U2-WALL-OLD** | U2-WALL's frozen set after step 1 | step 2 only, from U0's tree | refused (no end line, fail closed), class BUDGET; memory byte-identical |
| **U2-TIME** | a NEW GAME on an empty cart (as CONTROL), same seed | child A' (REAL tree, harness, `SaveWatch` not killing) with `--frames F_T` from `time_window(CONTROL row)` (5.3); freeze; child C = `child_b` (REAL tree) | a "nearly up" save on a held free screen, complete before the end; the end `stopped`; C allowed (class BUDGET, harness row) and arriving at the newest completed save, its restore holding the map P that only the time save captured |
| **U2-TIME-OLD** | the same | child A' from mutant T0's tree (no time due ever), same `F_T`; then child C (REAL tree) | no START after S_k's e4; FILE = S_k; C continues S_k; its restore lacks P |

### 5.2 Checks (graded by the second path; the AI's own record only where named)

**U2-BUDGET counts when** LAUNCH counted on the seed (K-AFTER's FILE was S2, `grade_launch`), AND LAUNCH's own record shows all of:
- its launcher line's `exit_reason` starts `play: stopped: not finished within 2620 frames`, with `exit_code` 0, `verdict_code` 0, `verdict` CLEAN, and `real_frames` == `frames` == 2620 (the host's count; FAULT `u2_stop_unverified`);
- its session's `continued_from` is S2's id;
- its end line has `budget` True and `at_save` False;
- the frozen-after cart's sha256 equals K-AFTER's frozen cart's (no write, so the end was NOT right after a save);
- no `save` line follows LAUNCH's session line.

Checks:
- **B1 allowed:** `memory_check.ok`, class BUDGET, `looked_through` 0, and words carrying ruling 53's clause. The drop is graded in `ContinueCheck.dropped` (`child_b`'s row):
  - the set is exactly LAUNCH's session;
  - `host_frames` == LAUNCH's launch line `real_frames` (the HOST's count; FAULT `u2_drop_self_graded`);
  - the AI's `frames` agrees with `host_frames` within the boot offset measured in step 2 (reported);
  - `at_save` == S2's RAM play time (SaveWatch truth, K-AFTER's row);
  - `lost` 0;
  - `maps` names exactly the consts in LAUNCH's `world.jsonl` last snapshot that are new to that session, or "none".

  FAULT `u2_drop_ignored`.
- **B2 arrival:** `continued_from` = S2's id; the arrival (PIDs, map, tile, boot play time) = K-AFTER's S2 RAM truth; CONTINUE pressed, no NEW GAME, no page (`continue_facts`).
- **B3 the AI's word** (named as the AI's record): C's session `dropped` frames and lost equal `ContinueCheck.dropped`'s. This is a label check only.
- **U2-BUDGET-OLD `old_shows`:** U0's tree ran (`launcher_sha` = the mutant's); `memory_check` refused with class BUDGET; the frozen memory is byte-identical before and after.

**U2-WALL counts when** step 1's own record shows all of:
- its launcher line: `exit_reason` `wall-clock`, `verdict_code` 124 (FAULT `u2_wall_no_code`), `verdict` CLEAN, `hard_kill` False;
- its session continued S2;
- its memory file has NO end line for that session.

Development measures `hard_kill` with a wall-clock verdict (a process lingering past its finish) and STOPS if it occurs on 3 or more seeds.

Checks:
- **W1 allowed:** class BUDGET, with ruling 53's clause in the words. In `dropped`: the AI's `frames` is None ("not recorded"); `host_frames` == step 1's `real_frames` minus S2's offset where S2 is in the set; `at_end` is None.
- **W2 arrival:** `parse_image` on the frozen cart; the arrival (PIDs, map, tile, boot play time) = the FILE's loaded content (the game's data on both sides); CONTINUE pressed, no NEW GAME, no page.
  - When the FILE's counter is above K-AFTER's, `continued_from` is the save line whose stamp matches the FILE's play time AND whose `where` and `party` PIDs equal the FILE's content (identity, not H:MM alone; FAULT `u2_wall_stamp_only`).
  - The match must be unique: section 4's D7 identity test pins that save stamps are >= 3 minutes apart.
- **W3 reported, not graded:** whether the AI made a time save before the wall (the cart's counter rose, and its content = the AI's newest save line's `where`/`party`/stamp), with its `why`. Its wall pace is reported too.
- **U2-WALL-OLD `old_shows`:** U0 ran; refused, class BUDGET; memory byte-identical.

**U2-TIME counts when:**
- CONTROL counted on the seed;
- `time_window` found a valid window (5.3);
- child A' ended `stopped: not finished within F_T frames` (the harness's PLAY line, and its end line `budget` True), and the target's proof was never true in A''s record;
- **the determinism line:** A''s presses digest up to T equals CONTROL's (one trajectory, replayed; not a replication).

Checks:
- **T1 the time save:** a START in A''s `SaveWatch` record at a frame >= T (converted, 5.3).
  - It is on a HELD free overworld read by the harness (`probe_end_screen.game_screen`, `AFTER` frames free; FAULT `u2_time_free_ignored`).
  - Its e3 and e4 are complete before A''s last frame, with its RAM truth at e3.
  - The AI's line for it has `why` starting `a save: the session's time is nearly up` (the AI's word: the label only).
- **T2 the FILE:** the probe's parser on A''s frozen cart → the identity of the NEWEST completed save in A''s record.
- **T3 C allowed:** `memory_check.ok`, class BUDGET (the harness row). In `dropped`, the AI's `frames` == A''s HARNESS frames from that save's e3 to A''s end, within the measured offset (the harness's count, not the memory file), and `at_save` == the save's RAM play time.
- **T4 C's arrival** = that save's RAM truth (PIDs, map, tile, boot play time); CONTINUE pressed; no NEW GAME; no page.
- **T5 C's restore** (`restore_snapshot`, `:1036`) holds P's map (discriminated by U2-TIME-OLD) and agrees with C's session `restored_maps`.
- **T6 reported:**
  - whether an "ends now" save happened, or was covered by the gap (the AI's log);
  - the frames A' played after its last save;
  - the due → cut and cut → START lags;
  - whether the cut fell during a goal.
- **U2-TIME-OLD `old_shows`:**
  - T0's tree ran (`saving_sha` = the mutant's: T0 edits `brain/saving.py` only);
  - no START in A'-OLD's record after S_k's e4;
  - FILE = S_k's truth;
  - C's `continued_from` = S_k's line id;
  - C's restore lacks P's map.

### 5.3 U2-TIME's stop rule (from CONTROL's own record, anchored on the LATEST save; `08` 2026-10-29 and 2026-10-30)

`time_window(control_row)`:
1. For every completed save S_k of CONTROL child A (SaveWatch e3, e4), and for k = 0 (the run's first frame, with no gap):
   - P_k = the first frame after S_k's e4 at which A stands (RAM, `map_now`) on a map NOT in the maps A stood on up to S_k's e3;
   - T_k = max(P_k + `U2_TIME_OFFSET` (30), S_k.e3 + `U2_GAP_FRAMES` (14,400 = 4 game minutes));
   - F_k = T_k + `TIME_SAVE_FRAMES`.
2. Valid if, in CONTROL's record: there is no START in (S_k.e4, F_k]; the target's proof is not true before F_k; and F_k < A's last frame.
3. Choose the LATEST valid k (FAULT `u2_time_window_first`).
4. `F_T` = F_k − frame0. MEASURE that the harness's frame identity holds on development rows; STOP if the brain's pad frames and the harness's frames differ.
5. No valid window → U2-TIME does not count on that seed. This is recorded, never a pass.

### 5.4 Discriminators (12 per seed; reported, never in the verdict)

The existing 9 per seed, plus:
- U2-BUDGET / U2-BUDGET-OLD: `memory_check.ok` [True, False];
- U2-WALL / U2-WALL-OLD: `memory_check.ok` [True, False];
- U2-TIME / U2-TIME-OLD: C's `continued_from` [the time save's id, S_k's id].

### 5.5 Floors, verdict, OLD-arm counting

As today (`verdict_of`, `:2270`):
- every graded arm counts on at least `FLOOR` = 3 of 4 held-out seeds;
- an OLD arm counts only where its NEW twin counts;
- PASS needs every counted NEW arm passing and every counted OLD arm showing.

### 5.6 Budgets and timeouts: MEASURED in development first, then 2x the widest (orchestrator ruling 2)

| constant | development value (a measuring cap) | graded value |
|---|---|---|
| `REACH_FRAMES` (AI side) | provisional 13,500 | 2 x the widest due → START reach in the U2-TIME and U2-WALL development rows (the AI's log), rounded up; the busy proxy as a cross-check (D7) |
| `LAST_REACH_FRAMES` (AI side) | provisional 300 | 2 x the widest cut → START lag on a free screen |
| `PACE_SAFETY` (AI side) | 2 | 2, unless the widest measured ratio exceeds it: STOP |
| `CHAIN_B_FRAMES`, `CHAIN_B_TIMEOUT`, `CHAIN_OLD_*` (RV-3) | the measuring caps 250,000 frames and 900 s | `CHAIN_BUDGET_BASE` + 2 x the widest arrival-to-kill ever measured (#57-#62, one unit); max(300, 2 x the widest wall); and D14's rule budget − widest kill >= 2 x `TIME_SAVE_FRAMES` |
| U2-TIME child A' timeout | `CHILD_A_TIMEOUT` (1200 s) | max(1200, 2 x the widest A' wall) |
| `U2_WALL_SECONDS` | 240 (provisional: the launcher's soft-to-hard margin is then 24 s, above `EXIT_WATCHDOG_SECONDS` 20) | max(240, 2 x the widest launcher-start-to-arrival wall + 60 s of play) |
| `U2_WALL_FRAMES` | 400,000 | 400,000 (STOP if any development run ends on it) |
| `U2_TIMEOUT` (the parent's) | `U2_WALL_SECONDS` + 180 | the same |
| child C / `child_b` steps | 2,620 frames, `CHILD_B_TIMEOUT` | unchanged unless development measures more |

- All of them go into `registered_numbers` before the held-out registration.
- The AI-side constants are SET in the code and committed in the tree the registration hashes. They are never changed to make an arm count.

### 5.7 Seeds and the ledger (D18)

- **#62, development 5601-5606:** begun before its first run. The whole plan runs at 12 jobs at once.
- **#63, held-out 5651-5654:** registered (and `ledger begin` checked) BEFORE any of them runs. One plan of every arm and one verdict.
- **Later rounds:** the independent re-run uses 5661-5664. A fix round re-runs every arm on 5671-5674, registered first. Its verification uses 5681-5684.

## 6. Revert mutants (`gates/revert_r1.py` `MUTANTS`, `:59` on; census sites in `revert_r1_mutants.json`)

| name | rule broken | predicted test(s) | suites |
|---|---|---|---|
| U0 | every frame-budget and soft-wall row back to the interim (`at_save` only; refused with no end line); also the live U2-BUDGET-OLD and U2-WALL-OLD trees | `test_the_end_classes` | `test_saving` |
| U1 | the harness BUDGET row back to `at_save` | `test_the_end_classes` | `test_saving` |
| U2a | the verified `stopped` row back to `at_save` | `test_the_end_classes` | `test_saving` |
| U3 | `wall-clock` with no end line refused again | `test_the_end_classes` | `test_saving` |
| U4 | the hard kill with no verdict allowed always (the rejected design) | `test_the_end_classes` | `test_saving` |
| U4b | the hard-kill row before the verdict (HEAD's order) | `test_a_hard_kill_is_judged_by_its_verdict_first` | `test_saving` |
| U5 | `_ran_out` always True | `test_a_stop_before_the_budget_is_the_ais_own_choice` | `test_saving` |
| U6 | the host-code check skipped | `test_a_host_reason_needs_its_host_code` | `test_saving` |
| U7 | `record_launch` omits the four fields | `test_the_launch_line_carries_the_counts` | `test_saving` |
| U8 | `_ran_out` uses `>` | `test_a_stop_before_the_budget_is_the_ais_own_choice` | `test_saving` |
| U9 | the code judged by the process `exit_code`, not `verdict_code` | `test_a_host_reason_needs_its_host_code` | `test_saving` |
| U10 | D3b's CLEAN check skipped | `test_a_budget_end_needs_a_clean_verdict` | `test_saving` |
| U11 | the harness branch chosen by the session's `host` first | `test_a_launcher_run_is_judged_by_its_line_whatever_host_says` | `test_saving` |
| D1m | `dropped_after` reports the latest stamp (0) for a session with no end line | `test_u2_dropped_after` | `test_saving` |
| D2m | `dropped_maps` drops the `first_frame` filter | `test_u2_the_drop_uses_the_hosts_count_and_names_the_maps_after_the_save` | `test_saving` |
| D3m | `end_line` without `play_time` / `where` | `test_the_end_line_says_chosen_budget_and_at_save` | `test_saving` |
| D4m | the session line's `dropped` not written | `test_u2_the_ais_continue_tells_the_drop_and_no_map` | `test_saving` |
| D5m | `at_end` from the newest end line in the file, not the newest session's | `test_u2_dropped_after` | `test_saving` |
| D6m | the drop set is cumulative (every session after the save) | `test_u2_dropped_after` | `test_saving` |
| T0 | `after_time` returns False at its top (also the live U2-TIME-OLD tree) | `test_u2_the_two_time_stages` | `test_saving` |
| T1x | `time` expires on leaving a map | `test_u2_a_time_due_survives_other_dues` | `test_saving` |
| T2 | the "nearly up" once-flag removed | `test_u2_the_two_time_stages` | `test_saving` |
| T3 | "ends now" exempt from the gap (the rejected design) | `test_u2_the_two_time_stages`, `test_u2_two_saves_within_a_minute_are_never_made` | `test_saving` |
| T4 | `Navigator.run` ignores `time_stop` | `test_u2_the_cut_on_a_free_look_only` | the navigator's suite |
| T5 | the cut's latch removed | `test_u2_the_cut_on_a_free_look_only` | the navigator's suite |
| T6 | `roam_train`'s time check removed | `test_u2_roam_stops_for_the_time` | the navigator's suite |
| T7 | a cut goal goes through `manager.outcome` | `test_u2_a_cut_goal_is_neither_failure_nor_mark` | `test_goals` |
| T8 | block 0 removed | `test_u2_the_time_save_comes_before_heal` | `test_goals` |
| T9 | `_since_save` always non-empty | `test_u2_something_to_lose` | `test_goals` |
| T10 | `_frames_left` ignores the wall | `test_u2_frames_left_knows_the_wall` | `test_saving` |
| T11 | `_save_before_done` skips a `time` due | `test_u2_a_reached_target_ends_done_and_saves_a_pending_time_due` | `test_goals` |
| T12 | `play_out` consults `nav.time_stop` (the settle cut) | `test_u2_the_settle_is_never_cut` | `test_goals` |
| T13 | a failed time save keeps its due | `test_u2_a_failed_time_save_ends_its_stage` | `test_goals` |
| T14 | `time_stop` ignores `save:time`'s cooldown | `test_u2_no_cut_while_the_time_save_is_set_aside` | `test_goals` |
| T15 | the time due stored in the `save_due` slot | `test_u2_a_time_due_survives_other_dues` | `test_saving` |
| T16 | a cut `pick_up` gives the ball up | `test_u2_a_cut_pick_up_gives_nothing_up` | `test_goals` |
| T17 | the cut checked before `intent.done` | `test_u2_the_cut_on_a_free_look_only` | the navigator's suite |
| T18 | `after_time` makes a due with fewer than `SAVE_FRAMES_NEEDED` left | `test_u2_the_two_time_stages` | `test_saving` |
| S40h | `_check_finally`'s Raise rule off | `PlayLoopExitTests.test_the_play_loop_cannot_exit` | `test_check_purity:PlayLoopExitTests` |
| S40i | `_check_finally`'s Assert rule off | `PlayLoopExitTests.test_the_play_loop_cannot_exit` | `test_check_purity:PlayLoopExitTests` |
| S46g | D3 (d)'s rebinding check removed | `FairnessTests.test_the_play_time_is_read_only_through_its_doors` | `test_safety_gates:FairnessTests` |
| S46h | the binding pre-pass collects `ast.Name` only | `FairnessTests.test_the_play_time_is_read_only_through_its_doors` | `test_safety_gates:FairnessTests` |

- **Anchors that must not move** (revert_r1 requires each anchor exactly once, `revert_r1.py:226`):
  - L7's `    if not allowed:\n        return ContinueCheck(False,` (`launcher.py:486-487`);
  - FX3's look-through line;
  - FX5's `texts = ...` line;
  - S33's opening of `judge_end`;
  - L13's `_INVOLUNTARY` (`:263`);
  - FX2's `held = ...` (`game_memory.py:486`);
  - CH1's `self.parent` line (`game_memory.py:742`);
  - FX1's `mode.py` line;
  - S39's `_check_together` line.
- **RULE CHANGES and RE-ANCHORS (each with a name map):**
  - **L10** (`revert_r1.py:324-327`): its rule becomes "a CHOSEN end with no `end` line allowed (fail open)". It is re-anchored on the new CHOSEN-only no-end-line refusal, and its prediction is RE-DERIVED from its first run, not copied. U3 stays distinct (wall-clock refused again).
  - **S34** is re-anchored on `record_launch(..., frames=args.frames)`, with the same predicted test.
  - **Census F008 / F016** (`game_memory.py:824`, the `write_end` → `end_line` call) and **F017** (`mode.py:658`, `writer.write_end(outcome, at_save, last.frame, ...)`): their lines change with D13. They are regenerated with a name map and re-derived predictions.
  - **U4's old prediction is replaced:** the old interim U4 ("hard kill back to `at_save`") no longer applies, because the hard-kill row stays `at_save`.
- **Before the change,** the builder lists every hand-written and census mutant whose anchor lies in a function this change edits:
  - launcher: `_classify_session`, `memory_check`, `record_launch`;
  - memory file: `end_line`, `write_end`;
  - options: `HandsOptions`;
  - mode: `_frames_left`, `_start_saving`, `_play`, `_save_before_done`, `_end_memory`, `_continue`;
  - `_on_main_menu`;
  - `SavePolicy` `saved_state` / `record_save`;
  - goals: `next_goal`, `_save_goal`, the runner's pick-up paths;
  - navigator: `Navigator.__init__` / `run`;
  - `roam_train`; `play_out`;
  - gates: `_check_finally`, the D3 (d) rule.

  It then runs `revert_r1` once to confirm that every anchor still resolves. The same audit covers `revert_step3`/`revert_step4` (navigator and roam anchors) and `revert_step5` (`goals.py` around `next_goal` and the runner).
- **CALL-SITE CENSUS (orchestrator ruling 4):** every new or changed AI-side function's call sites are closed by generated census mutants, with predictions recorded from their first run. No waivers. `census_waivers.json` gains no entry. The functions:
  - launcher and memory file: `_classify_session`, `_HOST_CODES` use, `_ran_out`, `record_launch`, `dropped_maps`, `MemoryBook.dropped_after`, `end_line`, `write_end`;
  - save policy: `after_time`, `time_due_now`, `time_choice`, `time_failed`;
  - goals: `time_ready`, `_save_goal`;
  - mode: `_since_save`, `_time_check`, `_time_stop`, `_wall_frames_left`, `_frames_left`;
  - navigation: `Navigator.run`'s cut, `roam_train`.
- **The live edit constants:** `U2_OLD_EDITS` and `T0_EDITS` equal `MUTANTS["U0"][2]` and `MUTANTS["T0"][2]`; the selftest asserts it.

## 7. Regression lane and gates impact

- **Suites touched (no new suite):**
  - QUICK: `check_purity`, `check_fairness`, `test_goals`, `test_saving`, `call_census`;
  - units: `test_check_purity` (sharded), `test_safety_gates`, and the navigator's suite;
  - reverts: `revert_r1` (about 41 hand-written plus census; update `run_regression_times.json`), `revert_step3`, `revert_step4`, `revert_step5` and `revert_safety_gates`.
  - `test_host` is untouched and runs whole.
- **Behaviour change in the AI:**
  - the time saves and the cut within `TIME_SAVE_FRAMES` of a run's end (only with at least `SAVE_FRAMES_NEEDED` frames left);
  - the wall-aware frames left;
  - the end line's two fields;
  - the runner skips its give-up bookkeeping on a cut (only reachable after a cut).
- **Where trajectories stay unchanged:** wherever frames left stay above `TIME_SAVE_FRAMES` or below `SAVE_FRAMES_NEEDED`, and no wall deadline is near:
  - every CONTROL run (330,000-frame budget, ending "done" at 129k-180k);
  - every K arm's 2,620-frame child B and LAUNCH (fewer than `SAVE_FRAMES_NEEDED`: no due, no line);
  - R2-RETRY;
  - CHAIN B under D14's rule.

  The existing determinism lines stand, checked by a STOP in step 5.
- **`live_step5`'s next run** was already a RE-BASELINE and now also carries the time saves.
- The bot and the bot tuner are untouched.
- **Grader hashes:** `live_r1.py`'s sha moves (`HASHED_FILES`, `:194-196`). `rate_step5.py` is unchanged.
- **Gates:** `check_purity` and `check_fairness` must PASS on the real package. `HOST_EXPORTS` and `INSTRUMENT_SHA256` are unchanged; `attribution.py`, `lifecycle.py` and `session.py` are untouched.
- **Evidence:** `ai_player/evidence/<date>-u2-REVERT.txt`, `<date>-u2-live-DEV.txt` and `<date>-u2-live-HELDOUT.txt`, plus the re-run's and any fix round's.

## 8. Step order and STOP rules for the builder; size

1. **One worktree** off `417df790` (or newer `main` if the orchestrator says).
   - The main checkout, `sandbox-pokebot/` and the tuner's clone are READ ONLY. `AI_PLAYER_BUILD_ROOT` and `AI_PLAYER_TEST_SUPPORT_ROOT` = the MAIN checkout's `sandbox-pokebot` (read only).
   - Throwaway profiles live under the run's own `--out`.
   - No git writes and no commit.
   - Before any live step, take a process census (`run_regression`, `run_gates`, `revert_*`, `rate_step5`, `live_step5`, `live_r1`).
2. **Re-verify every finding on the worktree first** with the `s53/u2/` probes, including `review_proof/probe_matchas.py`. **STOP** if any result differs from section 1.
   - Grep that `_settle_before_done` reaches only `play_out` → `nav.handle` (D12 (c)).
   - MEASURE the frame relation between the AI's `end.frame − frame_base` and the host's `real_frames` on every recorded LAUNCH row (the boot offset D13 needs). **STOP** if it is not a constant within a few frames.
   - List the runner's give-up markers by grep (D9).
3. **Offline parts in this order,** each with its tests and mutants green before the next:
   - (a) RV-7;
   - (b) RV-5;
   - (c) the launcher table (D1-D4), `record_launch`'s fields, and the host-code pin;
   - (d) the end line, `dropped_after`, `dropped_maps`, `ContinueCheck.dropped`, `cmd_run`'s words, and the AI's continue line and session `dropped`;
   - (e) `HandsOptions.wall_deadline` and `_frames_left` (class-level defaults);
   - (f) `SavePolicy`'s time due (own field), block 0, the cut (navigator, `roam_train`, the play loop's and the runner's transparent paths, the failed-save rule);
   - (g) the README.
   - **MEASURE the cut's reach and its transparency first.** With a fake navigator returning `time:` from every `run`, drive `pursue` for each goal kind and record:
     - the frames and presses from the cut to `pursue`'s return;
     - the diff of every GOAL_KEEP field and the world memory's markers, against the same goal interrupted by a battle.
   - **STOP** if any goal kind presses a button after the cut other than to finish a battle, scene or menu already on screen, or changes a marker that the battle interruption does not.
   - Re-confirm every existing memory-file test with a budget <= `TIME_SAVE_FRAMES` (section 4).
   - Then run: `call_census` (0 MISSING, no new waiver); `revert_r1` (all CAUGHT as predicted); `revert_step3/4/5`; `revert_safety_gates`; the quick lane. **STOP** if a new gate rule fires on the real package.
4. **`live_r1.py`:** the arms, `time_window`, the busy recorder, the B1/W1/T3 host-count graders, LAUNCH's `frozen_after`, and the selftest faults. Fault-test `time_window` and the drop graders on recorded #58 rows before relying on them: a planted off-by-one save id and a FIRST-save anchor must give different answers.
5. **Development #62, seeds 5601-5606** (ledger first), the whole plan at 12 jobs at once:
   - (a) every existing arm with the busy recorder on. RV-3: record the arrival-to-kill frames and walls; set the budgets (D14 and its rule).
   - (b) U2-TIME and U2-TIME-OLD with the PROVISIONAL `TIME_SAVE_FRAMES`, and U2-WALL with the provisional `U2_WALL_SECONDS`. Record the due → START reaches, the cut → START lags, A''s wall, the pace ratios, and the launcher-start-to-arrival walls. Set the AI-side constants and timeouts at 2x. If `TIME_SAVE_FRAMES` changed, re-run U2-TIME and U2-TIME-OLD on all six.
   - (c) U2-BUDGET and U2-BUDGET-OLD on all six; the selftest's development rows.
   - **STOP and report** if any of these happens (never tune the AI's policy to the proof; never change `SAVE_MIN_MINUTES`, the moments or the margins to make an arm count):
     - U2-TIME's window is vacuous, or its time save is absent, on 3 or more of 6 seeds;
     - any time save starts on a screen the harness does not read as held free;
     - LAUNCH's end is ever at a save, or its `real_frames` differs from its `frames`;
     - U2-WALL ends other than `wall-clock`/124 CLEAN with `hard_kill` False on 3 or more seeds, or ends on `U2_WALL_FRAMES`;
     - any OLD arm fails to show where its twin counts;
     - any measured reach exceeds 2 x the widest busy proxy, or the proxy exceeds 3 x 6,646;
     - a pace ratio exceeds `PACE_SAFETY`;
     - any `[AI-SAVE] a save is due` line of kind `time` appears in a non-U2 arm;
     - an existing arm's determinism line breaks.
6. **`live_r1.py selftest --all` is green:** the clean run PASSES, and every planted fault, old and new, FAILS.
7. **The held-out round:**
   - run the seed classifier first (0 uses), then `ledger register --first 5651 --last 5654`, then `ledger begin`;
   - run the plan, then `verdict`, then `ledger finish` and `ledger --check`.

   **Hand back:**
   - the diff, the evidence and the numbers;
   - the drop sentences seen (host and AI);
   - whether each seed's U2-TIME made or covered an "ends now" save;
   - U2-WALL's W3;
   - the frames played after the last save (the price of D7, measured).
8. **Then the orchestrator** runs the independent re-run on 5661-5664 and an adversarial review. Any fix re-runs EVERY arm on 5671-5674, registered first; its verification uses 5681-5684.

**Size (estimate):**
- **AI and host code, about 400 lines:** launcher 120, `__main__` 12, `game_memory` 60, `options` 6, `mode` 80, `brain/saving` 60, `goals` 35, `navigator` 15, `roam_train` 6, `skills/saving` 12.
- **Gate rules, about 60 lines.**
- **Test side, about 2,300 lines:** unit tests 1,000; `live_r1.py` 1,050; `revert_r1.py` 250; census (generated).
- **Live wall:** about 20-25 minutes per plan at 12 parallel emulators, plus development's two passes. U2-WALL's step 1 now takes at least 240 s.

## 9. Out of scope, and KNOWN LIMITS

**Out of scope:**
- the legendary retry of ruling 52 (deferred; a CHOSEN end stays refused);
- a live hard-kill arm (the row is the interim's, unchanged and unit-proven);
- a live arm for a forged stop, a forged host reason or a forged `host` field (the judgement is a pure function of the files, unit-proven with FAULT and CONTROL);
- FX5's guard live;
- the gym-leader save live;
- repeated time saves every 3 minutes;
- putting the game down after a time save;
- a per-line checksum, and schema 2;
- telling the dropped maps or play times to the AI (D19, ruling 40).

**KNOWN LIMITS (README and `06`):**
- **D2/D3 are defence in depth, not a seal.** A brain that wants a reload can still get one:
  - by raising: a real `crash`, INVOLUNTARY (the accepted limit of R1 + R2's spec D12);
  - by idling with frames until its frame budget or the soft wall clock runs out.

  Each such route costs the whole remaining session, never nothing. A brain that blocks without frames reaches only the hard kill, which stays refused unless at a save. No AI code does any of this. The purity and fairness gates do not forbid `time.sleep` (`check_purity.py:450`).
- **A `crash` or other INVOLUNTARY host end whose verdict is not CLEAN stays continuable** (pre-existing; D3b covers BUDGET ends only).
- **A save's stamp is to the minute.** Save identity on a continue rests on the 3-minute gap, which every save, the time stages included, now obeys (D7).
- **The harness's BUDGET row rests on its end line** (D4: the test host).

## 10. Open questions

**Technical, all DECIDED here** (each goes to `06` with its rejected alternative): D1-D18, plus D3a and D3b. Specifically:
- the reading of ruling 53's "(not a crash and not a kill)": the launcher's hard kill keeps the interim (D1, D3a);
- the two time stages, both obeying the 3-minute gap, with the stated price (D7);
- the time save while hurt (D10);
- the host-record rules (D2, D3, D3a, D3b, D4). F-U2-2 to F-U2-5 are pre-existing and fixed here because the table is re-derived now; the orchestrator may split them out without changing D2;
- the wall knowledge (D11);
- the drop's one set, its host count, and the AI never told a map or a play time (D13).

**For the USER: none.**
- `06` was grepped (`grep -n -i "wall deadline\|time save\|budget save\|never idle\|not a kill\|hard kill"`).
- Ruling 53 answered U2 and left the design to Claude ("Approved, and proceed how you think we should proceed"). Its own words "(not a crash and not a kill)" decide the hard kill.
- Ruling 37 Q6 ("never idle") decides D12 (e).
- D7's price is a design value Claude owns under ruling 53, and it is reported live (step 7).

## 11. Revision log

| finding | lens | what was done | why (evidence at `417df790`) |
|---|---|---|---|
| U2R-1 | code-host | APPLIED: D13 rebuilt over one set of sessions, frames per session from its own end line or "not recorded", never from a later stamp; `host_frames` from `real_frames`; `at_end` from the newest session only; the "monotonic" sentence corrected (1.4); B1/W1/T3 graded against the host or harness count; D1m/D5m FAULTs | Only save/saved/lost/end lines carry `frame` (`game_memory.py:17-22`); `frame_base` = 1 + max stamp (`:597-603`); a soft wall clock leaves no end line (`session.py:322-327`) |
| U2R-2 | code-host | APPLIED: D9 extended to the goal runner (skip give-up markers on `nav.cut`, cut walk not counted in `item_tries`); step 3 diffs GOAL_KEEP and the world markers with a STOP; FAULT test and mutant T16 | `goals.py:2139-2142` and `:2221` add to `tried_items`; `tried_items`/`item_tries` are GOAL_KEEP (`game_memory.py:130-131`) |
| U2R-3 | code-host | APPLIED: `time_stop` uses block 0's own predicate (`_allowed("save:time")`); a failed time save consumes its stage; mutants T13, T14 with tests | `_save_goal` checks `_allowed` (`goals.py:1421`); `outcome` sets a 12-decision cooldown after 2 failures (`:1756-1767`) |
| U2R-4 | code-host | APPLIED: D2/D3 restated as defence in depth; the raise, idle-to-budget and idle-to-wall routes in KNOWN LIMITS; the hang route closed by keeping the hard kill's interim (see proof U2R-2) | `time` allowed everywhere (`check_purity.py:450`); `crash` INVOLUNTARY (`launcher.py:450-451`). A `time.sleep` blocks frames, so it reaches the hard kill, not `wall-clock` (`_on_frame` checks the deadline, `session.py:322`) |
| U2R-5 | code-host | APPLIED as D3a: a hard kill with a verdict is judged by its verdict; FAULT row (reset-refused + hard_kill → NOT CLEAN), mutant U4b | Hard-kill row first (`launcher.py:434-436`); the verdict reason kept (`:314-317`); `EXIT_WATCHDOG_SECONDS` 20 (`attribution.py:267`) against a 5-30 s margin (`launcher.py:521-527`) |
| U2R-6 | code-host | APPLIED: class-level defaults and `getattr` (D11, 3 (h)); step 3 re-confirms every memory-file test with a budget <= `TIME_SAVE_FRAMES` | `HandsBrain.__new__` with a SimpleNamespace `options` (`test_goals.py:910-916`); frames 500/5000/4000/10,000 at `:1326`, `:1344`, `:1781`, `:5045` |
| U2R-7 | code-host | APPLIED: L10 named as a rule change, re-anchored, prediction re-derived; F008/F016/F017 re-generated with a name map; U3 kept distinct | L10 at `revert_r1.py:324-327` is anchored on the no-end-line refusal |
| U2R-8 | code-host | APPLIED: `memory_check` (launcher-side) builds `dropped`, maps included; `child_b` records it; B1/W1 name the field they grade | `child_b` calls `memory_check` (`live_r1.py:838`), not `cmd_run` |
| U2R-9 | code-host | APPLIED: D13's ONE set (the sessions after the latest continue from the save), used for frames, maps and lost alike; D6m FAULT | `timeline` cuts after k at each continue from k (`game_memory.py:605-631`) |
| U2R-10 | code-host | APPLIED: the time due in its own field `time_due` (D6); mutants T15, T1x | `_make_due` overwrites the single slot (`saving.py:125-128`); `before_leader` re-makes it (`:210-213`); `due_now` expires centre/leader (`:137-140`) |
| U2R-11 | code-host | APPLIED: `REACH_FRAMES` set from the measured due → START reach in the AI's log; the busy proxy kept as a cross-check with a STOP | The proxy counts free skill steps that no cut can interrupt (1.3) |
| U2R-12 | code-host | APPLIED: `HASHED_FILES` `:194-196`; CH1 `:742`; the continue lines are in `_on_main_menu` (`:618-625`); new probes X21-X24 | Read at those lines |
| U2R-13 | code-host | APPLIED: D16 refuses `ast.Assert` too; plant X24, mutant S40i | `_check_finally` (`check_purity.py:1233-1251`) has no Assert case |
| U2R-14 | code-host | APPLIED: the cut is checked after `intent.done(look)` and the new-changes block; mutant T17 with a test | `intent.done` at `navigator.py:1253`, the look at `:1227` |
| U2R-15 | code-host | APPLIED: the launch line records `verdict_code`; the codes are judged by the instrument's record, the process code reported only; mutant U9 | A second thread's `finish` raises its own code (`lifecycle.py:142-147`); the line's `exit_code` is the process code (`launcher.py:315`) |
| U2R-1 | proof-rulings | APPLIED: "ends now" OBEYS the 3-minute gap (exemption dropped); D7's price re-stated; identity test, mutant T3 now the exemption; W2 matches by stamp AND content identity (FAULT `u2_wall_stamp_only`) | `match_time` picks the NEWEST line within `MATCH_MINUTES` (`game_memory.py:564-570`); lines are written at write START; `06` 2026-10-30 Known limits |
| U2R-2 | proof-rulings | APPLIED: the launcher's hard kill keeps the interim (`at_save`), read from ruling 53's "(not a crash and not a kill)"; U4 now tests the rejected "always allowed"; the reading goes into `06` | `_end_if_refused` runs only on frames and the brain's own exits (`session.py:306`, `:373`, `:384`); `mode.py:218-224` `_hang`; ruling 53 text, `06:9912` |
| U2R-3 | proof-rulings | APPLIED as D4: a launch line naming the `run_dir` always decides; FAULT/CONTROL, mutant U11 | The `host` field is AI-written (`mode.py:471`) and checked first (`launcher.py:420`) |
| U2R-4 | proof-rulings | APPLIED as D3b: the launch line records `verdict`; a BUDGET end with a non-CLEAN verdict is NOT CLEAN; mutant U10. Not widened to INVOLUNTARY (an early crash with 0 frames is UNVERIFIED and would end a game for good); stated as a limit | `lifecycle.py:160-163` replaces the reason only for code 0 |
| U2R-5 | proof-rulings | APPLIED: D15's pre-pass collects MatchAs/MatchStar/MatchMapping.rest, ExceptHandler, global/nonlocal and walrus targets; `import builtins` disables the exception; plants and mutant S46h. Star imports were already refused | `probe_matchas.out`; `check_purity.py:1120-1121` |
| U2R-6 | proof-rulings | APPLIED with code-host U2R-1: "not recorded" without an end line, never 0; frames graded against the host or harness count; the second reader kept as a label check (B3) | Same evidence as code-host U2R-1 |
| U2R-7 | proof-rulings | APPLIED with code-host U2R-10 (own field) | `saving.py:125-128` |
| U2R-8 | proof-rulings | APPLIED: D14's rule (budget − widest kill >= 2 x `TIME_SAVE_FRAMES`) in `registered_numbers` and the selftest; no due with fewer than `SAVE_FRAMES_NEEDED` left (mutant T18); STOP on a `time` due in a non-U2 arm | Under D7, a kill inside the window would make a time save |
| U2R-9 | proof-rulings | APPLIED: mutant T12 (`play_out` consults `time_stop`) with the settle test, and a CONTROL that the same due IS cut in `Navigator.run` | `play_out` reaches only `nav.handle` (`skills/story.py:148-159`) |
| U2R-10 | proof-rulings | APPLIED: play times only in the launcher's operator sentence; the AI's line and session `dropped` carry frames and battles only | No door purpose in `check_fairness.py:111-116`; ruling 40 |
| U2R-11 | proof-rulings | APPLIED: summary item 2 and 1.2 reworded; the refusing side is unit-proven (U5, U8) | 1700 and 531-616 belong to `play: stuck: the continue stopped:` ends (CHOSEN) |
| U2R-12 | proof-rulings | APPLIED: (a) U2-TIME-OLD from T0 (U0 for the other two); (b) `saving_sha`; (c) one measure, arrival-to-kill, re-read per row (the 243,534 figure withdrawn); (d) the pin covers every finish reason, Name constants resolved, NOT CLEAN reasons in `_HOST_NOT_CLEAN` | `live_r1.py:154-161` defines the budget on arrival → kill; the `session.py` finish calls listed in 1.2 |
