> **Filed 2026-10-30** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/u2b/SPEC.md` (sha256 `cf13f88e30b4b75f`). U2b, the save before the limit (USER RULING 53; deferred from U2a by the scope cut, `06` 2026-10-30), REDESIGNED FROM MEASURED PLAY by the workflow `u2b-design` (3 agents, 5.73 Mtok): a designer that first measured 102 recorded sessions offline (the play a limit end would drop; scripts and outputs in session scratch `s53/u2b/measure/`), one adversarial critic (11 findings, 2 MAJOR) and a reviser (its section 11; every finding confirmed and applied). It supersedes the U2 spec's D6-D12 (`2026-10-30-U2-BUILD-SPEC.md`). **One question is open for the user** (its section 10): the AI saves before its FRAME budget runs out, not before a wall-clock limit (which would make runs depend on the PC's speed); the recommendation is to run sessions on the frame budget with the clock as a backstop. The build is not started: it waits for the weekly usage to reset.

# U2b: THE AI SAVES BEFORE ITS FRAME BUDGET RUNS OUT (build spec, 2026-10-30, measured first; revised after review)

> Base: HEAD `d66f6b90`. Every anchor below was read on `git archive d66f6b90 ai_player` (session scratch `s53/u2b/tree/`). Every number comes from recorded runs, offline. The draft's scripts and outputs are in `s53/u2b/measure/`, the critic's in `s53/u2b/critic/`, and the revision's in `s53/u2b/revise/`. The parsers passed 41 planted checks (`selftest_u2b.py`) before any real number was read.
> Rulings in force: USER RULING 53 (`06` 2026-10-29), 51, 52, 40, 37 Q6 ("never idle"), and `06` 2026-10-30 "U2a BUILT" (the scope cut).
> The U2 spec's D6-D12 were the starting point. Kept: the save happens at a goal decision, obeys the 3-minute gap, never cuts the settle, and the target check comes first. Dropped: the cut, the two stages, the separate `time_due` field, the once-per-process flags and the wall-pace knowledge. Section 2 says why for each.
> ⚠ **The headline caveat: no recorded session has ever ended on its frame budget.** All 70 CONTROL runs and all 6 `live_step5` runs ended "done" on their target. The 26 U2-WALL step-1 runs ended on the wall clock, which U2b does not see (D8). Every benefit number below is therefore a HYPOTHETICAL: a frame-budget end placed on the recorded trajectories. U2b helps only sessions whose binding limit is their frame budget, and the README tells operators to run them that way. Whether that meets ruling 53's "before its time runs out" is put to the user (section 10). The build does not wait for the answer, because a wall-aware save could only be added on top of this one.

## 0. Summary

- **Is a save before the limit worth building? Yes, for sessions that end on their frame budget.** Ruling 53 asks for it, and the gain is large wherever saves are sparse. It does nothing for a wall-clock end.
  - **Chapter 1:** the AI already saves densely, with 4.3 regular saves per new game and a median of 21,517 frames between them. A time save there is near neutral: for a hypothetical budget end in the last 20%, the mean drop goes from 9,458 to 9,026 frames.
  - **Chapter 2** (only 3 runs, so the evidence is thin): saves are sparse, with 4 regular saves in 3 runs. A budget end in the last 20% would drop a mean of 65,252 frames (about 18 minutes of play). With U2b that falls to 10,204 (max 13,532), and the trigger fires on 98% of those ends.
  - **The 26 U2-WALL continue trajectories, read as if their limit had been a frame budget:** the last-20% mean goes from 18,006 to 10,345.
  - **What has really happened:** the 26 real wall-clock ends dropped a mean of 24,678 frames (median 25,119, max 59,502; about 7 minutes of play). U2b does NOT change those (D8). Each such continue already tells what it drops (U2a).
- **The design is one stateless trigger and no cut.** At a goal decision, AFTER the HEAL block and after block 1b, the goal manager chooses a `save` goal of kind `time` when all of these hold:
  - frames left <= `TIME_SAVE_FRAMES` = 14,400 (`SAVE_FRAMES_NEEDED` 3,600 + 3 x 3,600 frames);
  - the session has gained something since its last save (an AI progress item, a milestone passed or a battle lost);
  - the existing policy may save: the play time is read, 3 whole game minutes have passed since the last save, at least 3,600 frames are left, and the screen is free;
  - the key `save:time` is not cooling down.

  There is no due field, no stage, no latch and no wall knowledge. That comes to about 75 lines of AI code. The launcher gains one operator note when the wall clock may end a session before its frame budget.
- **The live proof** reuses U2-WALL's step 1, a real-launcher continue from K-AFTER's S2, as the CONTROL trajectory.
  - Rule W picks the latest decision d where the trigger must fire, with a lag-safe gap. U2B-TIME re-runs the same continue with `--frames F_T = (d - frame_base) + 14,400 - 10`, so it ends `play: stopped:`. It must land on a time save, and its OLD twin (mutant T0) on S_k.
  - On recorded data, rule W finds a window on 9 of 26 U2-WALL records at today's 240-second wall (by round 1/6, 3/4, 2/4, 3/4, 0/4, 0/4: none in the newest two rounds) and on 2 of 3 chapter-2 records.
  - U2-WALL's wall is therefore raised to 600 s, to reach chapter 2. A two-seed 600-s smoke run comes before development, and development has a STOP rule.

## 1. Measured (each number with its source)

### 1.0 Data

- **102 sessions:**
  - 70 harness CONTROL new games to `ch1_pokedex` (rounds #51-#67, 70 distinct seeds). All ended "play: done".
  - 26 real-launcher U2-WALL step-1 continues from S2 that ended on the soft wall clock (exit 124).
  - 3 `live_step5` chapter-1 launcher new games and 3 chapter-2 launcher runs (the 2026-10-30 re-baseline). All 6 ended "done" on their target, under 330,000 frames and 3,600 s.
  - **None of the 102 ended on its frame budget** (`critic/ends.py`; the evidence files `ai_player/evidence/2026-10-30-r1base-*.txt`).
- **Not used:**
  - K-* arms (CONTROL replayed up to a kill);
  - CHAIN B/C (killed, or 2,620 frames);
  - LAUNCH (2,620 frames);
  - pre-R1 sweeps (no saves).
- **The drop at a cut frame f** = f − e3 of the latest save whose write was COMPLETE (e4 <= f). The end save before "done" is excluded, because a limit end has none. A continued or chapter-2 session starts AT a save.
- **Quantile convention:** `v[int(p·n)]`, which gives the upper middle for an even n. Where a true median differs, it is given.
- **Frames vs play time:** "minutes" in this spec are frames / 3,600. The game's own play time runs SLOWER than emulator frames, by about 310 frames across each save plus up to 1.43% of the frames between saves (303 consecutive CONTROL save pairs, harness truth h:m:s:f; the lag is 297-558 frames over intervals of 10k-20k frames and 1,297 at most, at 75,563 frames; `revise/playtime_lag.py`).
- **Cross-checks** (`load_sessions.py`):
  - the AI's progress tells equal its report on 76 of 76 runs;
  - losses and milestones agree on every run;
  - harness e3 − memory save frame = 4-5 on all 373 saves;
  - a U2-WALL record's first action frame = `frame_base` on 26 of 26, and its last action frame is 1-56 frames before `frame_base + real_frames`.

### 1.1 (a) Gaps between REGULAR saves (end saves before "done" excluded; `revise/gaps_regular.py`)

| family | regular saves per session | start → first save | save → save: median / p90 / max | last regular save → end |
|---|---|---|---|---|
| CONTROL ch1 (70) | 4.33 | median 46,434 (ch1_lab) | 21,517 / 38,939 / 75,563 (n=233) | median 15,515 (to the done end) |
| U2-WALL (26) | 4.04 | median 20,098 | 15,411 / 26,138 / 41,023 (n=79) | mean 24,678, median 25,119, max 59,502 (the wall end) |
| ch1 launcher (3) | 4.33 | 45,809 mean | 24,881 / 51,253 / 51,253 (n=10) | 15,412 median |
| ch2 launcher (3) | 1.33 | 21,312 / 22,112 / 53,863 | one gap only: 32,189 | 89,777 / 28,521 / 95,076 (to the done end) |

- Only centre heals saved between the POKéDEX and WALLY in chapter 2.

### 1.2 (b) Drop at a uniformly random cut, today

- **CONTROL:**
  - mean 13,808, median 11,416, p90 28,536, max 75,805 frames;
  - 32.6% of a new game's frames come before its first save, where the whole game would be lost.
- **Other families:**
  - U2-WALL: mean 11,879, p90 23,906;
  - ch1 launcher: mean 14,440, p90 30,552;
  - chapter 2: mean 33,358, median 25,720, p90 75,277, max 95,057.

### 1.3 (c) The last 20% of a session, today

One value per quantity; these are `simulate2_u2b.py`'s baselines, and `measure_u2b.py`'s own grid differs by at most 38 frames.

- CONTROL: mean 9,458, p90 15,664.
- U2-WALL: mean 18,006, p90 33,627, max 59,438.
- ch1 launcher: mean 9,276, p90 15,230.
- Chapter 2: mean 65,252, p90 88,989, max 94,989.
- **The 26 real wall ends, at their own last frame:** mean 24,678, median 25,119, p90 39,886, max 59,502. 24 of the 26 dropped more than 3,600 frames, and 16 more than 18,000.

### 1.4 (d) What the dropped stretch holds (share of cuts)

- **Random cut, CONTROL:** items 29%, levels 25%, new maps 24%, battles won 20%, milestones 3%, battles lost 2%, nothing at all 46%.
- **Random cut, chapter 2:** maps 84%, items 59%, catches 59%, levels 58%, milestones 56%, nothing 12%.
- **Last 20%:**
  - CONTROL: items 62%, maps 28%, milestones 11%, nothing 27%;
  - U2-WALL: maps 59%, milestones 51%, catches 49%, nothing 20%;
  - chapter 2: maps 100%, milestones 94%, nothing 0%.
- **The 26 wall ends:** a new map in 18, a catch in 17, a milestone in 16, an item in 14, a level in 11, a battle lost in 0, nothing in 3.

### 1.5 (e) Free screens and decisions in the last 20%

- **Free overworld records:**
  - gaps: median 8 frames, p99 1,221-2,468, max 8,292;
  - from a random frame to the next free record: p90 1,910-2,873, p99 <= 5,264.
- **Goal decisions**, from a random frame to the next one (CONTROL / U2-WALL / ch2):
  - p90 7,528 / 8,328 / 10,024;
  - p99 9,689 / 13,581 / 12,077;
  - max 12,232 / 16,771 / 12,317.
  - These are LOWER bounds: the measure stops at the session's end when no decision follows (`measure_u2b.py:174`), and each chapter-2 run ends about 12,300 frames after its last decision, inside WALLY's scene.

### 1.6 Save lags and pace

- **A save goal's lags** (303 regular CONTROL save goals, harness truth): decision → START 30 frames (max 45); → write start median 813 (max 862); → complete median 1,072 (max 1,122).
- **Pace:** harness 456 fps median; U2-WALL launcher 367-600 fps; `live_step5` launcher 582-649 fps.
- **How sessions end:** every recorded configuration except U2-WALL ends on its TARGET, long before its frame budget:
  - CONTROL played at most 195,885 of 330,000 frames;
  - `live_step5` chapter 1 played at most 178,222 of 330,000, and chapter 2 at most 148,939.
  - `live_step5`'s 330,000 frames under a 3,600-s wall would bind before the wall at any pace above 92 fps.

### 1.7 The trigger on the recorded trajectories (HYPOTHETICAL budget ends)

Scripts: `simulate2_u2b.py`, `worse_u2b.py` and `revise/sim_lag.py`. The budget end E sweeps the last 20% of each session on a 100-frame grid. The model:
- the trigger fires at the first decision with E − d <= M and E − d >= 3,600 that passes the gap and something-to-lose checks;
- it writes at d + 862 and completes at d + 1,122;
- later recorded saves shift by 1,330 frames and are COVERED when they fall within 3 game minutes of it.

**Last 20% of all 102 sessions (26,716 cuts), decisions, after HEAL:**

| M | U2b mean | p90 | max | worse cuts (mean / max) | net gain per cut |
|---|---|---|---|---|---|
| (today) | 12,526 | 23,123 | 94,989 | | |
| 9,000 | 9,685 | 15,649 | 94,989 | 439 (3,889 / 7,790) | +2,842 |
| 10,800 | 9,356 | 15,071 | 94,989 | 841 (4,463 / 9,566) | +3,170 |
| 12,600 | 9,267 | 14,773 | 56,438 | 1,288 (4,769 / 11,224) | +3,259 |
| **14,400** | **9,318** | **14,605** | **56,438** | 1,740 (4,887 / 12,776) | +3,208 |
| 17,100 | 9,516 | 15,171 | 56,438 | 2,450 (5,171 / 15,827) | +3,011 |

- **By family at M = 14,400 (mean, today → U2b):**
  - chapter 2: 65,252 → 10,204 (max 13,532; fires 98%);
  - U2-WALL trajectories: 18,006 → 10,345;
  - CONTROL: 9,458 → 9,026;
  - ch1 launcher: never fires.
- **Chapter 2 at M = 12,600:** 8,751 (max 13,357), also firing on 98%. At 10,800 it fires on only 91%, and its max stays 94,989.
- **No decision in the window** at M = 14,400: 2.4% of all cuts (CONTROL 1.7%, U2-WALL 4.2%, ch1 launcher 9.3%).
- **Sensitivity to the play-time lag (1.0):**
  - with a play time that runs slower as measured, M = 14,400 gives a pooled mean of 9,462 (CONTROL 9,219), and U2-WALL and chapter 2 are unchanged;
  - M = 12,600 gives 9,403.
  - The conclusions hold.
- **Counterfactual only:** if each of the 26 wall ends had been a frame-budget end at the same frame, the trigger fires on 15 and is worse on 0, and the mean goes from 24,678 to 11,061. U2b gives none of this to a real wall end (D8).
- **BEFORE HEAL** (the old D10) is worse:
  - 40% of its fires came at a heal decision;
  - it has 4,665 worse cuts against 1,288 after HEAL (M = 12,600);
  - it is net −503 frames per cut on ch1 launcher games.
- **The CUT** (a free-screen trigger, before HEAL, M = 12,600): last-20% mean 9,123, p90 12,628, max 32,157, but it is worse on 47% of cuts.

### 1.8 Where the live window exists (`revise/lengths_and_w.py`)

Rule W (section 5), M = 14,400, lag-safe gap (d − S_k's write start >= 12,100 frames):

| host | window exists on |
|---|---|
| U2-WALL step-1 records (240 s) | **9 of 26** (by round 1/6, 3/4, 2/4, 3/4, 0/4, 0/4); a new map P on 7 of the 9 |
| chapter-2 launcher records | **2 of 3** (CH2, CH2M; P on both) |
| the draft's extrapolated gap (+0.5 minute) | 12 of 26, and 3 of 3 |
| harness CONTROL (rejected) | 29 of 70 (5 of 70 with a new map), under the draft's rule |

- On each window, the decision before d is 45-11,212 frames earlier, so the 10-frame pad keeps d the first decision in the window.
- The newest 8 records (#66, #67) have no window. Their sessions saved more often (4-6 saves), and the cause is not known. For the same seed, a longer record keeps every window a shorter one has, because determinism holds up to the old end. That says nothing about new seeds, hence the 600-s smoke (step 4b).
- **Determinism:** U2-WALL 5601's smoke and plan runs pressed the same 1,281 presses up to frame 170,988, under different load. One trajectory, replayed.
- **A second time save** in the window is possible on 3 of the 11 windows (5662, 5664, 5672), for 7-38% of the unknown stamp-second phases (the critic's model, `critic/second_save.py`, re-run on the lag-safe windows). The graders accept it (F2).

## 2. Decisions (each with the rejected alternative)

- **D1. Build the time save, for frame-budget ends.**
  - Ruling 53 asks the AI to "save before its time runs out". Where saves are sparse (chapter 2 onward, which is most of the game, ruling 41), a budget end in a session's last 20% would lose a mean of 18 minutes of play, and U2b cuts that to about 3. In chapter 1 it is near neutral.
  - This rests on 3 chapter-2 runs and on hypothetical budget ends, because no recorded run ended on its budget. It is worth building because it is cheap (about 75 AI lines), deterministic and provable.
  - **Rejected:**
    - not building it (ruling 53);
    - justifying it with the 26 wall ends (U2b does not see the wall).
- **D2. One trigger, at goal decisions, with no cut.**
  - The cut buys about 200 frames on the mean, but it is worse on 47% of cuts and needs the whole old D9 machinery: a navigator latch, runner give-up markers and the T12-T17 mutants.
  - **Rejected:**
    - the old D9 cut;
    - a trigger on free screens without a cut (impossible: the play loop decides only at decisions).
- **D3. AFTER HEAL, as block 1c right after block 1b.** The block is not gated by `hurt`.
  - When a heal goal is chosen, the heal at a centre makes a centre save, or the next decision saves.
  - Placed after 1b, a centre's or a moment's due that may save keeps its own label, and the time save takes only what 1b leaves. 1b is skipped while hurt, so a hurt party with no heal goal still gets the time save.
  - Measured: before HEAL, 40% of fires came at heal decisions, and it was worse 3.6x as often.
  - **Rejected:**
    - before HEAL (the old D10);
    - inside block 1b (gated by `hurt`);
    - between HEAL and 1b (the draft): a due's save would be labelled "time".
- **D4. `TIME_SAVE_FRAMES` = 14,400 = `SAVE_FRAMES_NEEDED` + 3 x 3,600.**
  - On the recorded data the pooled mean is flat from 10,800 to 14,400 (9,356 / 9,267 / 9,318), and 12,600 is slightly better in sample: chapter 2 has a mean of 8,751 against 10,204, and there are 1,288 worse cuts against 1,740.
  - 14,400 is chosen for robustness. Its 10,800-frame decision window covers the p90 wait to the next goal decision in all three families (7,528 / 8,328 / 10,024), while 12,600's 9,000-frame window misses chapter 2's p90. Those waits are lower bounds. The p99 is covered in one family of three.
  - A missed window costs the whole drop (tens of thousands of frames in chapter 2); a worse cut costs a mean of 4,887. The in-sample price of 14,400 over 12,600 is about 50 frames on the pooled mean.
  - **Rejected:**
    - 12,600 (in sample better, but thin on the tail: 3 chapter-2 runs);
    - 17,100 (2,450 worse cuts);
    - two stages (the old D7);
    - tuning M to make an arm pass (never).
- **D5. Stateless: no `time_due` field, no once-per-process flag.**
  - The trigger is recomputed at each decision. A recent save covers it through the gap (said once, through a GOAL_RESET `time_told` field). A failed time save goes through the existing `_allowed`/`outcome` cooldown (key `save:time`).
  - **At most two time saves fit in one window.** The gap compares WHOLE minutes (`saving.py:152`), so a second one can follow about 2-3 real minutes after the first. The graders accept one or two (F2).
  - Two time saves are at least 3 whole minutes apart, so save identity on a continue (`MATCH_MINUTES` 1) holds.
  - **Rejected:** the old D6 field and its flags.
- **D6. "Something gained"** = the play report's counts since the last save: `len(report["progress"])`, `len(report["milestones"])` and `report["losses"]`, against `report["since_save"]`.
  - The baseline is reset in `on_saved`. On a continue it starts at (0, 0, restored losses).
  - It never reads frames, so there is no frame-space mix-up after a continue.
  - **Rejected:**
    - frames since the save;
    - comparing frame stamps across sessions;
    - the key name `at_save`, which already names the end line's bool and the drop's play time (F11).
- **D7. `SAVE_MIN_MINUTES` is obeyed, with no exemption.** The gap is also the save-identity rule.
  - Measured cost: the time save covers a later centre or moment save in 1,740 of 26,716 late cuts, by a mean of 4,887 frames.
  - **Rejected:**
    - exempting the time save;
    - letting a later moment ignore the gap.
- **D8. The wall clock stays unknown to the brain; the frame budget is the limit U2b serves; the launcher tells the operator when the wall may come first.**
  - Giving the brain the wall (the old D11: deadline × measured pace / `PACE_SAFETY`) would make its choices depend on machine load. The time save's moment would then differ between replays of one trajectory, the live arm could not be predicted from a record, and every determinism check after the window would be void.
  - Converting the wall into a frame budget at a fixed safe pace would end sessions with up to about a third of their wall time unused.
  - A wall end stays continuable (U2a) and tells its drop.
  - **The operator convention (README):** give a session its frame budget as the real limit, and the wall clock as a backstop of at least 2x the expected time at the slowest measured pace.
  - **The launcher's note:** when `frames > (wall_seconds − soft margin) × PACE_NOTE_FPS` (300, under the slowest measured 367), the launcher prints `[AI-RUN] note: the wall clock may end this session before its frame budget; the AI saves before its frame budget only`.
  - **This narrows ruling 53's wording, and it is put to the user (section 10).** A wall-aware save (U2c) would plug into `_run_frames_left` alone.
  - **Rejected:**
    - the old D11, now;
    - the fixed-pace conversion;
    - claiming the wall ends as U2b's benefit (F1).
- **D9. Interplay:**
  - The target check (`mode.py:829-838`) comes before `next_goal` (`:881`), and R5's settle and `_save_before_done` (`:606-632`) never reach `next_goal`. So a reached target always ends "done", and the settle is never interrupted.
  - No save starts with fewer than 3,600 frames left, and no YES is pressed under `COMMIT_FRAMES_NEEDED`.
  - The AI plays on after a time save (ruling 37 Q6), pinned by a test and mutant T10.
  - **The pre-existing limit, made more likely by U2b (F7):**
    - A "done" end whose due is gap-covered gets no end save, so it is not `at_save`, and its CHOSEN end is refused a continue (`launcher.py:483-485`).
    - With U2b, this also happens when the target is reached within 3 game minutes after a time save, which means within the last 14,400 frames of the budget.
    - For a target at a uniformly random point of its budget, the chance is at most 14,400 / budget: 4.4% at 330,000 frames. No recorded run came within 134,000 frames of its budget, so the data cannot measure it.
    - It is kept as a known limit, pinned by a test.
  - **Rejected:**
    - letting the done end count as `at_save` after a time save (a chosen end would then be continuable while dropping the target's play: a reload, ruling 52);
    - an end save inside the gap (save identity);
    - putting the game down after the time save.
- **D10. The live proof's host is U2-WALL's step 1**, a real-launcher continue that is deterministic up to its end, lengthened to 600 s. Its window is chosen with a lag-safe gap and a 10-frame pad.
  - **Rejected:**
    - the harness CONTROL (29 of 70, and only 5 with a new map);
    - a fixed-budget run with no recorded control;
    - the critic's 10,800-frame "certain" gap (play time runs slower than frames, 1.0);
    - the draft's +0.5-minute extrapolation (3 of 12 windows sat inside its error).
- **D11. The open NITs `06` assigned to "the next item"** (U2a verification N1-N3) are folded in, each with a FAULT and a CONTROL:
  - N1: the V2 test also pins the base term when the save's session is not the newest;
  - N2: V3's sentence says "unreadable" when the verdict file exists but cannot be read;
  - N3: a non-dict `facts` is refused with words, not an AttributeError.
  - **Rejected:** deferring them again (the live plan re-runs every arm anyway).

## 3. Parts (anchors at `d66f6b90`)

### (a) `ai_player/brain/saving.py`

- **New constant** `TIME_SAVE_FRAMES = SAVE_FRAMES_NEEDED + SAVE_MIN_MINUTES * 3600`, beside `SAVE_MIN_MINUTES` (`:54`). Its comment carries section 1.7's numbers and the caveat that they are hypothetical budget ends. Add it to `__all__` (`:37`).
- **New `SavePolicy.before_limit(look, frames_left, gained: list[str]) -> SaveChoice | None`**, after `before_leader` (`:192-221`). It returns None in each of these cases:
  - `frames_left > TIME_SAVE_FRAMES`;
  - `gained` is empty;
  - `_blocker` (`:144-160`) gives `gap`: told once through `goal_memory.time_told`, "no time save: its last save ... covers it";
  - `_blocker` gives any other code (`frames`, `busy`, `play_time`).

  Otherwise it returns `SaveChoice("time", f"a save: the session's frame budget is nearly up ({frames_left} frames left; since its last save: {', '.join(gained)})", "save:time", None)`.
- `DUE_KINDS` (`:58`), `_make_due`, `due_now`, `next_save` and `record_save` (`:238`) are UNCHANGED.
- The module docstring names ruling 53's fourth moment, its rule, and that it serves the frame budget only (D8).

### (b) `ai_player/brain/goals.py`

- **`_Memory`** (`:407`) gains `time_told: str | None = None`, as GOAL_RESET.
- **`GoalManager.__init__`** (`:933`, beside `frames_left`): `self.gained: Callable[[], list[str]] | None = None`.
- **`next_goal`:** a new block **1c** right after block 1b's `return saving` (`:1254`), before `# 2. SHOP` (`:1255`): `timed = self._time_save(look, milestone)`; return it if not None. It is NOT gated by `hurt`.
- **New `_time_save`** beside `_save_goal` (`:1415-1423`):
  - None without `saving` or `gained`;
  - otherwise `choice = self.saving.before_limit(look, self._run_frames_left(), self.gained())`, through `_allowed(choice.key)` (`:1753`);
  - returns `Goal("save", choice.reason, milestone.id, key=choice.key)`.

### (c) `ai_player/mode.py`

- **The report** (`:761-768`): after the restored losses, `report["since_save"] = {"progress": 0, "milestones": 0, "losses": report["losses"]}`.
- **`on_saved`** (`:584-592`): set `report["since_save"]` to the current three counts.
- **New `_gained(report) -> list[str]`:** "N progress item(s)", the milestone ids passed, "N battle(s) lost", each since `since_save`.
- **`_start_saving`** (`:523-546`): `manager.gained = lambda: self._gained(report)`, beside `manager.frames_left` (`:541`).
- `_save_before_done`, `_settle_before_done` and `_bounded` are UNCHANGED.

### (d) `ai_player/game_memory.py`

- `GOAL_RESET` gains `time_told`, which `test_every_goal_memory_field_is_classified` (`gates/test_saving.py:753`) forces.

### (e) `ai_player/README.md`

- Under "Saving and CONTINUE" (`:752`):
  - the time save and its rule;
  - its measured price and benefit, labelled as hypothetical budget ends;
  - the operator convention (D8);
  - the known limits (section 9).

### (f) `ai_player/__main__.py` / `host/launcher.py` (D8 note; D11 N2, N3)

- **The note:** in `cmd_run` after the argument checks (`__main__.py:136-141`), `wall_note(frames, wall_seconds) -> str | None` (in `host/launcher.py`, beside `soft_deadline_margin` `:714`). It uses `PACE_NOTE_FPS = 300` and prints the D8 line when it applies.
- **N2:** the V3 sentence names "unreadable" when the file exists but `read_verdict` fails.
- **N3:** a non-dict `facts` is refused with words.

### (g) `ai_player/gates/live_r1.py`

- **Constants** (`:220-226`):
  - `U2_WALL_SECONDS` 240 → 600 (provisional; development sets it);
  - `U2_WALL_FRAMES` 400,000 → 1,000,000, so that frames left at the wall end stay >= 2 x `TIME_SAVE_FRAMES` (649 fps x 600 s = 389k);
  - `U2_TIMEOUT` follows.
- **New:**
  - `rule_w(u2wall_row)` (section 5);
  - the arms `U2B-TIME` (`cmd_u2btime`, after `cmd_u2wall` `:2550`) and `U2B-TIME-OLD` (mutant T0);
  - `grade_u2btime` and the discriminators;
  - `registered_numbers` (`:3081`) rules: every arm's budget minus its widest measured end >= 2 x `TIME_SAVE_FRAMES`, or < `SAVE_FRAMES_NEEDED` (LAUNCH's 2,620).
- `ARMS_NEW` (`:145`) and `OLD_OF` (`:147`) gain the arms. `HELD_OUT` (`:134`) becomes (5751, 5754).

### (h) `ai_player/gates/revert_r1.py`

- `MUTANTS` (`:70`) gains T0-T10, LN1 and LW1-LW6 (section 6). Census sites go in `revert_r1_mutants.json`.

## 4. Tests (a FAULT and a CONTROL per guard; each docstring names both halves)

| guard | test (suite) | FAULT (must fail) | CONTROL |
|---|---|---|---|
| the margin | `PolicyTests.test_time_save_only_inside_the_margin` (`test_saving`, class `:1916`) | `frames_left = TIME_SAVE_FRAMES + 1` → no choice (T1 removes the check; T1b `<` for `<=`) | `= TIME_SAVE_FRAMES` → kind `time` |
| something gained | `test_time_save_needs_something_gained` | `gained=[]` → None (T3) | `["1 progress item"]` → choice |
| the gap | `test_time_save_obeys_the_gap` | a save 2 whole game minutes ago → None, told once (T5 exempts `time`) | 3 minutes → choice |
| too few frames | `test_time_save_never_with_too_few_frames` | 3,599 → None (T2 skips `_blocker`) | 3,600 → choice |
| a free screen | `test_time_save_only_on_a_free_screen` | a busy look → None | a free look → choice |
| after HEAL | `NextGoalTests.test_time_save_comes_after_heal` (`test_goals`) | hurt (share < `heal_below`) with a known centre inside the window → `heal` (T4: the block before HEAL returns save) | hurt with share < `heal_below`, NO fainted Pokemon, no `needs_rest` and NO heal place (not `must_rest`, so no `find_center`) → `save:time` (T4b gates it by hurt) |
| a due keeps its label | `test_time_save_yields_to_a_due` | a centre due that may save, inside the window → key `save:center` (T4c: block 1c before 1b) | no due → `save:time` |
| cooldown | `test_time_save_cools_down` | two failures → no `save:time` for 12 decisions (T6 bypasses `_allowed`) | after the cooldown → chosen |
| baseline reset | `PlayLoopTests.test_gained_resets_at_a_save` (`:830`) | a centre save >= 3 whole game minutes before the deciding look and nothing since → no time save. The test ASSERTS `_blocker` returns `(None, "")` at that look, so the gap cannot mask T7 (`on_saved` keeps the old baseline) | a map gained since → a time save |
| continue baseline | `test_gained_on_a_continue` | restored losses 2, nothing new, the look >= 3 whole minutes after the restored `last_save` (and `_blocker` asserted None) → no time save (T8 counts restored losses) | one new loss → time save |
| plays on | `PlayLoopTests.test_plays_on_after_a_time_save` | a time save in the window, then the loop must choose its next goal and end `stopped` on its budget (T10: the loop ends or idles after a `save:time` outcome) | the same run → a goal after the save, end reason `stopped: not finished within N frames` |
| target first / settle | `test_target_inside_the_window_ends_done` | reached inside the window → "done", no `time` save (T9: `_save_before_done` consults `before_limit`) | the same run without the target → a time save |
| the known done-limit (pin) | `test_done_soon_after_a_time_save_is_not_at_save` | a target reached 2 whole minutes after a time save → "done", no end save, the told reason names the gap, the end line `at_save` False | 3 whole minutes after → the end save is made and `at_save` True |
| the operator note | `test_host: test_wall_note` | frames 1,000,000, wall 600 → the note (LN1 removes it) | frames 330,000, wall 3,600 → no note |
| N1 / N2 / N3 | `test_host` / `test_game_memory` | N1: the base term with the save's session not the newest; N2: an unreadable verdict file → "unreadable"; N3: `facts` a list → refusal words | each one's current CONTROL |

- **The rule-W grader, the U2B-TIME grader and the drop grader get selftest faults:**
  - `u2b_window_first`: rule W picks the first window, not the latest;
  - `u2b_window_ignores_saves`: a save starting inside the window;
  - `u2b_gap_extrapolated`: the +0.5-minute gap, not the lag-safe 12,100 frames;
  - `u2b_no_pad`: F_T without the 10-frame pad;
  - `u2b_exactly_one`: a grader that fails on two time saves;
  - `u2b_file_ignored`, `u2b_drop_self_graded` and `u2b_determinism_skipped`.

  Each is planted on the recorded s53 U2-WALL rows. Rule W must reproduce 9 of 26 (and 2 of 3 on the chapter-2 rows) on them, and a two-save plant (a second time-save line 9,300 frames after d) must PASS.
- **Re-derive (never discover as red)** every memory-file test whose budget is <= 14,400:
  - `test_goals.py:1326` (500), `:1344` (5,000), `:1364` (`limit + DONE_BUDGET_MARGIN`), `:1781` (4,000) and `:5077` (10,000);
  - **`R1PlayTests.play`** (`:2042-2046`, default 5,000, memory file, 12 callers in class `:2019`);
  - every caller of the `__new__` builder (`:910-916`) that passes `frames`;
  - and any hit of `grep -n "frames=" gates/test_*.py` with a value <= 14,400 or a variable.

  Each one's first decision has nothing gained, but later decisions may have.

## 5. Live proof

- **U2-WALL step 1 runs unchanged except its wall (600 s).** Its grading (W1-W3) is unchanged. It now prints the D8 note.
- **Rule W (U2-WALL's step-1 record → the window).** Take the LATEST goal decision d where all of these hold:
  - the goal at d is not a save, a heal or `find_center`;
  - the decision before d is more than 20 frames earlier;
  - S_k is the latest save complete by d (the continued S2 counts, at `frame_base`);
  - **d − S_k's write start >= 12,100 frames** (3 x 3,600 + 1,300, the widest measured play-time lag, 1.0). Then the whole-minute gap holds for every unknown stamp second;
  - something was gained since S_k;
  - no save line's write start − 900 lies in (d, d + 14,400 + 2,000];
  - the record extends past d + 16,400.

  Then **F_T = (d − frame_base) + 14,400 − 10** (pad frames). At d the AI sees about 14,390 frames left, and at the decision before d more than 14,400. P (a map first stood on after S_k, at or before d) is reported, and graded where it exists.
- **U2B-TIME procedure:**
  1. A copy of K-AFTER's frozen set goes in its own mirror build root.
  2. The REAL launcher runs `run --continue --frames F_T --wall-seconds U2B_WALL_SECONDS` with target `ch4_roxanne`. Then freeze.
  3. `child_b` runs from the REAL tree.

  U2B-TIME-OLD is the same from mutant T0's tree.
- **It counts when:**
  - U2-WALL counted and rule W found a window;
  - the launch line says `play: stopped: not finished within F_T frames`, with `real_frames == F_T`, verdict CLEAN, `verdict_code` 0 and no `hard_kill`;
  - the determinism line holds: the presses (frame, action) up to d equal U2-WALL step 1's.
- **The checks:**
  - **TS1 (the AI's word, the label only):** ONE OR TWO save lines after d, and EVERY save line after d is a time save: its `why` begins "a save: the session's frame budget is nearly up", its frame − base lies in [F_T − 14,400, F_T − 3,600 + 900], and it has its `saved` line. Two time saves must have stamps at least 3 whole minutes apart.
  - **TS2 (the game's data):** `parse_image` of the frozen cart. The newest counter = S_k's + the number of time saves, and the loaded H:MM, map, tile and PIDs equal the NEWEST time save's line.
  - **TS3:** `memory_check` is allowed, class BUDGET, with ruling 53's words. `continued_from` = the newest time save's id, and the arrival = the FILE's content (CONTINUE pressed, no NEW GAME, no page).
  - **TS4 (the host's count):** `dropped.host_frames` == `real_frames` − (the newest time save's frame − base). Only the equality is graded; the upper bound already follows from TS1.
  - **TS5:** where P exists, the restore holds P.
- **OLD shows:**
  - T0's tree ran (`saving_sha`);
  - no save line after S_k;
  - FILE = S_k;
  - C's `continued_from` = S_k's id;
  - P is absent where P exists.
- **Discriminators** (2 per seed, reported): `continued_from` [the newest time save's id, S_k's id]; the FILE counter [> k, == k].
- **Windows shown on recorded data:** 9 of 26 U2-WALL records at 240 s (by round 1/6, 3/4, 2/4, 3/4, 0/4, 0/4); 2 of 3 chapter-2 records.
- **Floors:**
  - a window on at least 2 of the 4 held-out seeds;
  - U2B-TIME counts and passes TS1-TS5 on EVERY held-out seed with a window;
  - OLD shows on every seed where its twin counts.

  Fewer windows means the verdict is BELOW THE FLOOR (reported, never PASS).
- **Seeds** (all FREE in `ledger.json`'s 67 entries):
  - 600-s smoke: 5791-5792;
  - development #68: 5701-5706;
  - held-out #69: 5751-5754 (registered first);
  - re-run: 5761-5764;
  - fix round: 5771-5774;
  - verification: 5781-5784;
  - spare: 5793-5794.

## 6. Mutants (`revert_r1.py`)

| mutant | rule broken | predicted catch |
|---|---|---|
| T0 | `before_limit` returns None (also the live OLD tree) | the margin CONTROL |
| T1 / T1b | margin check removed / `<` for `<=` | the margin FAULT / CONTROL |
| T2 | `_blocker` skipped for `time` | too-few-frames FAULT |
| T3 | gained ignored | gained FAULT |
| T4 / T4b / T4c | block 1c before HEAL / gated by `hurt` / before 1b | after-HEAL FAULT / CONTROL / due-label FAULT |
| T5 | the gap exempted | gap FAULT |
| T6 | `_allowed` bypassed | cooldown FAULT |
| T7 | baseline not reset in `on_saved` | baseline FAULT |
| T8 | restored losses counted as gained | continue FAULT |
| T9 | `_save_before_done` consults `before_limit` | target FAULT |
| T10 | the play loop ends after a `save:time` outcome | plays-on FAULT |
| LN1 | the launcher's wall note never printed | wall-note FAULT |
| LW1-LW6 | rule W first-not-latest, saves ignored, determinism skipped, extrapolated gap, no pad, exactly-one grader | the selftest faults |

## 7. Lane impact

- **Unchanged by construction** (re-confirmed in step 2): every existing arm and run keeps frames left > 14,400 at its end, or < 3,600.
  - CONTROL / K-*: 330,000 frames against ends of at most 195,885.
  - CHAIN B: 242,294 frames against kills of at most 120,137.
  - CHAIN-OLD: 145,938 frames against kills of at most 71,959.
  - LAUNCH / U2-BUDGET / child C: 2,620 frames.
  - U2-WALL: 1,000,000 frames.
  - `live_step5`: 330,000 frames against at most 178,222 played.
- **U2-WALL and any run with frames > wall × 300** print the new `[AI-RUN] note:` line. `live_r1` collects `[AI-RUN]` lines into its evidence lists (`:1700`, `:2242`, `:2406`), and step 2 confirms that no grader counts or matches them.
- **Lane runtime:**
  - `test_saving`, `test_goals` and `test_host` gain about 17 tests (seconds);
  - `revert_r1` gains about 20 mutants (about 3% more);
  - the live plan gains 2 launcher runs and 2 continues per seed, after the 600-s U2-WALL: about +8-12 min of plan wall, plus the smoke (about 12 min).
- **The bot tuner is untouched** (`ai-agent/` does not import `ai_player`).

## 8. Step order, STOP rules, size

1. **Set up:** one worktree off `d66f6b90` (or newer `main`); the main checkout, `sandbox-pokebot` and the tuner clone are read-only; no git writes. Take a process census before any live step.
2. **Re-verify on the worktree:**
   - re-run `selftest_u2b.py`, `measure_u2b.py`, `revise/lengths_and_w.py` and `revise/playtime_lag.py` (the same numbers);
   - grep every play-brain reader of the budget (`mode.py:541`, `:548-550`, `:595`, `:622`, `:1134`, `:1348`; `:205`, `:251` and `:408` are not the play brain);
   - grep `live_r1` for any grader that counts or matches `[AI-RUN]` lines.
   - **STOP** if another budget reader exists, if a grader would read the note, or if any `rate_step5` or `live_step5` plan both saves (a memory file) AND can end within 14,400 frames of its budget.
3. **Offline, in order:**
   - (a) the policy and its tests;
   - (b) block 1c and its tests;
   - (c) the counters and their tests, then re-derive section 4's existing tests;
   - (d) the launcher note and N1-N3;
   - (e) the README.
   - Then: mutants all CAUGHT as predicted; `call_census` 0 MISSING with no new waiver; the quick lane; `run_gates --quick`.
   - **STOP** if a gate fires on the real package.
4. **`live_r1`:** rule W, the arms, the graders, the selftest faults, and `registered_numbers`' rule. Rule W must give 9 of 26 (and 2 of 3) on the recorded s53 rows before it is relied on.
   - **4b. The 600-s smoke:** U2-WALL step 1 at 600 s on seeds 5791 and 5792, then rule W on them. Report each window (d, F_T, P, the gap in frames) and the frames reached.
   - **STOP and report** if neither has a window. Only an orchestrator ruling may then change the wall or the host.
5. **Development #68 (5701-5706)**, the whole plan at 12 jobs.
   - **STOP and report** (never tune the AI, `TIME_SAVE_FRAMES`, `SAVE_MIN_MINUTES` or the moments) if any of these happens:
     - rule W finds a window on fewer than 3 of 6 seeds;
     - a time-save line appears in any non-U2B arm;
     - a determinism line breaks;
     - U2B-TIME ends other than `stopped` / F_T / CLEAN;
     - TS1 is absent where the window exists (a FAIL, reported);
     - an OLD arm fails to show where its twin counts.
   - Then set `U2_WALL_SECONDS` and `U2B_WALL_SECONDS` at 2x the widest measured value.
6. **`selftest --all` is green.**
7. **Held-out #69:** run the seed classifier, register, begin, run the plan, take the verdict, finish, and check the ledger.
8. **The orchestrator's rounds:** re-run 5761-5764 with an adversarial review; a fix round on 5771-5774; its verification on 5781-5784.

**Size:**
- AI code about 75 lines (`saving` 35, `goals` 18, `mode` 22); launcher about 25; README 50.
- Tests about 420 lines; `live_r1` about 480; `revert_r1` about 170.
- **Cost estimate:** about 0.55x U2a (26.99 Mtok over 8 agents), so about 13-17 Mtok. Most of it is the live rounds.

## 9. Out of scope, and known limits

**Out of scope:**
- the cut (the old D9);
- two stages (the old D7);
- a `time_due` field (the old D6);
- the wall deadline in the brain (the old D11; it would be U2c if the user wants it, section 10);
- putting the game down after the save;
- telling the AI maps or play times (D19, ruling 40);
- the legendary retry (ruling 52, deferred);
- V4 (NIT: ledger #65's free-text start time; `06` already records the correct time).

**Known limits (README and `06`):**
- **A wall-clock end is not anticipated:** no time save, and the continue tells its drop. The 26 recorded wall ends dropped a mean of 24,678 frames. Operators who want the save make the frame budget the binding limit (D8, and the launcher's note).
- The benefit is measured on hypothetical frame-budget ends. Chapter 2's rests on 3 runs.
- The play after a time save is lost: at most about 13,600 frames (max 13,532 measured in chapter 2). Every continue tells it (U2a).
- No goal decision falls in the 10,800-frame window on 2.4% of late budget ends. Those keep today's drop.
- In chapter 1 the save is near neutral, and in 1,740 of 26,716 late cuts it covers a later centre or moment save (mean +4,887 frames).
- A "done" end within 3 game minutes after a time save gets no end save and cannot be continued (D9): at most 14,400 / budget for a uniformly placed target, pinned by a test.

## 10. Open questions for the user

- **One, non-blocking (D8).** In plain words: "When the AI plays a session, two limits can stop it: a game-time budget (how much play it gets) or a clock time on your PC. U2b makes it save shortly before its game-time budget runs out, and the launcher will warn whenever the clock might stop a session first. It will NOT save before a clock-time limit, because its play would then depend on how fast your PC happens to run, and its runs could no longer be replayed and checked. Is running sessions on the game-time budget (with the clock only as a safety backstop) acceptable, or do you want a follow-up (U2c) that also saves before a clock-time limit, at that cost? My recommendation: the game-time budget." The build proceeds either way: U2c would only add on top.
- `06` was grepped for "time save", "save before its time", "before the limit", "wall deadline", "session length", "never idle" and "U2b". Ruling 53 left the design to Claude, and its Consequences line reads "a save before its frame budget runs out". But the user's approved words are "before its time runs out", so the narrowing is asked, not assumed.

## 11. Revision log

| id | verdict | what was done | evidence (re-run in this session) |
|---|---|---|---|
| F1 (MAJOR) | CONFIRMED | Every benefit number is restated as a hypothetical frame-budget end. The 26 wall ends are moved out of the Summary's benefit, out of D1 and out of D4 (only "what really happened" and a labelled counterfactual remain). 1.6's "ends on its frame budget" is corrected to "ends on its target". D8 is rewritten: frame budget only, the operator convention, a launcher note, and the narrowing put to the user (section 10). The headline caveat is added. | `critic/ends.py` re-run: 70 CONTROL `play: done`; 26 `wall-clock code=124`; the 6 `live_step5` runs ended done (their memory files carry the "before putting the game down" save, `critic/recompute.py`). `06:9906` (the user's words "before its time runs out"); `06:9910` ("wherever it knows the limit") and the Consequences line ("frame budget") are Claude's. The wall deadline reaches only `host/session.py:322`. |
| F2 (MAJOR) | CONFIRMED | TS1 accepts one or two time saves, and every save line after d must be one. TS2-TS4 follow the newest. The discriminator becomes counter > k vs == k. Selftest fault `u2b_exactly_one` and mutant LW6 added. D5 states why two can occur. | `saving.py:152-153` compares whole minutes. `critic/second_save.py` re-run: possible on 4 of 15 draft windows; on the lag-safe windows 3 of 11 (5662, 5664, 5672; `revise/check_revise.py`). |
| F3 (MINOR) | CONFIRMED, with a correction | Rule W's gap is made lag-safe: d − S_k >= 12,100 frames. The critic's 10,800 is NOT certain, because the game's play time runs slower than emulator frames (about 310 per save + up to 1.43%; max lag 1,297). Windows go 12 → 9 of 26 and 3 → 2 of 3. Fault `u2b_gap_extrapolated` / LW4 added. | `revise/playtime_lag.py` (303 harness-truth save pairs); `critic/by_round.py`: 5605 at 3.15, 5606 at 3.24 and CH2T at 3.22 extrapolated minutes all drop out. |
| F4 (MINOR) | CONFIRMED | Step 4b, a 600-s smoke on 5791-5792 with a STOP, before development. The rate is reported with its per-round split everywhere, and "a lower bound" is limited to the same seed. The development STOP is set to fewer than 3 of 6 windows, and the held-out floor to a window on at least 2 of 4 with every windowed seed passing. | Rounds: 1/6, 3/4, 2/4, 3/4, 0/4, 0/4 (lag-safe). The newest 8 records have no window (4-6 saves each); the cause is unknown. |
| F5 (MINOR) | CONFIRMED, and wider | The chapter-2 row is recomputed with end saves excluded and each kind labelled. The CONTROL and ch1-launcher rows had the same flaw (`measure_u2b.py` prints "done saves INCLUDED") and are recomputed too: CONTROL between saves 18,807 → 21,517 median (n 303 → 233); 5.3 → 4.33 regular saves per run. The centre/moment gap split, which included end saves, is dropped. | `critic/recompute.py` and `revise/gaps_regular.py` re-run: ch2 first 21,312 / 22,112 / 53,863; save → save 32,189; to the end 89,777 / 28,521 / 95,076. |
| F6 (MINOR) | CONFIRMED | The T7 and T8 FAULT setups put the look at least 3 whole minutes after the save's stamp and ASSERT `_blocker` returns `(None, "")`. | `saving.py:150-155`; `last_save` is GOAL_KEEP and restored on a continue. |
| F7 (MINOR) | CONFIRMED; kept as a limit | The frequency is stated honestly (at most 14,400 / budget; 4.4% at 330k; unmeasurable on the data). Pin test added. Counting the done end as `at_save` is rejected (a chosen end continuable while dropping play is a reload, ruling 52). | `launcher.py:483-485`; `_save_before_done` uses `may_save` (`mode.py:622`); `at_save` = no press since the last successful save (`mode.py:659`). |
| F8 (MINOR) | CONFIRMED | `test_plays_on_after_a_time_save` and mutant T10 added. | No listed test or mutant covered ruling 37 Q6 after a time save. |
| F9 (MINOR) | CONFIRMED | `R1PlayTests.play` (default 5,000, 12 callers), `:1364`, the `__new__` builder's callers, and a grep rule are added to the re-derive list. | `test_goals.py:2042-2046` builds `HandsBrain(BrainSettings(frames=5000))` with `memory_file`. |
| F10 (NIT) | CONFIRMED | (1) The p99 is covered in "one of three". (2) "Halves" is removed with the wall-end argument. (3) The true median 25,119 is given and the convention stated. (4) One value per quantity (simulate2's). (5) The wait p99s are labelled lower bounds. | `measure_u2b.out`; `measure_u2b.py:174`; `critic/recompute.py` (median 25,119). |
| F11 (NIT) | CONFIRMED | TS4 keeps only the equality. The report key is renamed `since_save`. T4b's CONTROL is pinned to share < `heal_below`, with no fainted Pokemon and no `needs_rest`. | `goals.py:1202-1246` (`must_rest` → `find_center` when no heal place); `game_memory.py:501`, `:684`. |
| R1 (reviser) | NEW | F_T = (d − base) + 14,400 − 10, and rule W requires the previous decision > 20 frames before d, so the trigger fires at d despite a ±1-frame offset between look frames and pad frames. | `load_sessions.py` CHECK: first action frame − base = 0 on 26 of 26; end − last action frame >= 1. The previous decision before d was 45-11,212 frames earlier on the 11 windows. |
| R2 (reviser) | NEW | Block 1c is placed after 1b, not before it, so a due that may save keeps its own label. Test T4c added. | `goals.py:1248-1255`. The simulation is unaffected (a decision that is already a save is skipped in both orders). |
| R3 (reviser) | NEW | The simulation's play-time model was re-run with the measured lag. The pooled mean is 9,318 → 9,462, CONTROL 9,026 → 9,219, and U2-WALL and chapter 2 are unchanged. The conclusions hold. | `revise/sim_lag.py`. |
| R4 (reviser) | NEW | `06` 2026-10-30 assigned the U2a NITs N1-N3 to "the next item", and the draft omitted them. They are folded in as D11, with tests. V4 is left out of scope, with its reason. | `06` 2026-10-30 "U2a's verification findings V1-V3 fixed" → "Open (NITs, the next item's)". |
