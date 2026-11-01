> **Filed 2026-10-31** by the orchestrating session: the report of the GRADED held-out driver for KI-128/KI-129 (`ai_player/gates/live_ki128.py` and its self-tests `test_live_ki128.py`; the spec's section 5), built by the workflow `ki128-heldout-driver`: a builder in a worktree on `a869af0c` (no live runs), an independent adversarial verifier (5 findings, 1 MAJOR: F1, the per-intent alternation reads a cross-intent ping-pong as clean), and a fixer who added K8.EDGE_WINDOW (at most 10 crossings of one edge in any 3,000 frames, intents ignored). The three sections follow VERBATIM.
> **The orchestrator's changes after the workflow:** K8.EDGE_WINDOW is REPORTED, not graded (`06` 2026-10-31: the graded bars are what the fix claims); the verifier's F3 is fixed (a world.jsonl held open no longer crashes the batch: its size is recorded first and the delete is retried); two self-tests were changed on purpose to the ruling; the self-tests joined `run_units.py`. Nothing has been registered or run: registration happens after the full lane passes, and is committed and pushed before the run.

## The builder's section

## KI-128 + KI-129 graded held-out driver: built and proven offline (nothing registered, nothing run live)

The driver for the spec's section 5 is ready to register and run. Nothing in this section is a held-out result: there was no live run and no registration, by order, and nothing was committed.

**Files**
- `ai_player/gates/live_ki128.py`: the driver, test side.
- `ai_player/gates/test_live_ki128.py`: its offline tests.

**Seeds**
- 5972-5977 are free: no ledger entry of any family names them (a unit test checks the ledger).
- The neighbours are taken: #79 used 5966-5971 and #69 used 5990.

**What the driver does**
- `register` writes one graded ledger entry. Its bounds field is the sha256 of `registered_numbers()`, which holds:
  - the BOUNDS TEXT and every constant;
  - the job list: CH2 Catcher 5972/5973, CH2T Story 5974/5975, CH2M Trainer 5976/5977;
  - the sha256 of the three r1base starts' end_state.ss1, world.jsonl and actions.jsonl;
  - the AI code's hash (ai_player/ outside gates/ and evidence/, CRLF read as LF);
  - the sha256 of the 9 files that grade the batch.
- `ledger.begin` therefore refuses a graded batch if any of the following changed after registration: a bound, a start file, the AI's code, or a grader file.
- `run` refuses before any run when any of these holds:
  - `--out` is inside the repo;
  - the G-3 import walk of the driver is not empty;
  - less than 40 GB is free;
  - a disposable profile `ai-ki128-ho-<seed>` already exists.
- Otherwise it launches the 6 runs, at most 3 at once:
  - each goes through the real launcher via `live_step5.run_arm`: target ch3_rustboro, 600,000 frames, 3,600 s;
  - each start's world.jsonl is passed whole as AI_PLAYER_WORLD, as A0 did.
- After each run, `check_purity` and `check_after_is_this_run` run. Then the world.jsonl is handled in this order:
  1. its size is recorded;
  2. its measures are streamed from it line by line;
  3. its last line is kept outside the repo;
  4. it is deleted.
- A disk guard kills the launcher if a world.jsonl passes 1.5 GB or free space drops under 30 GB.
- If a child crashes, the orchestrator still measures and deletes that run's world file and writes a row with no checks, which fails the batch as VACUOUS.
- At the end, one evidence file with a GRADED header is written and the ledger entry is finished with the verdict line.

**"Nothing new between" (fixed in the bounds text before registration)**
- An alternation is a run of consecutive crossings of one edge in one intent with no news between neighbours. An edge is the unordered pair of maps.
- News between two crossings is any of:
  - N1: a `[AI-WORLD] novelty at f<M>:` line between them in the log;
  - N2: a `MILESTONE <id> done` line between them;
  - N3: the world memory's `tiles_learned` rose between the world.jsonl lines that first hold the two crossings' transitions;
  - N4: the number of maps with visits rose between those two lines.
- A crossing with no world line gets no N3/N4 news (the strict reading).
- The bound: every alternation is at most 5 crossings.

**Offline proof**

| Check | Result |
|---|---|
| New unit tests | 45 tests OK |
| Test mutants (scratch `mutants.py`) | 25 of 25 caught; the control fails 0 of 45 |
| test_host (support root set to main) | 37 OK |
| check_purity | PASS |
| check_fairness | PASS, 0 breaches |
| check_paths | PASS, 47 files |
| call_census | PASS |
| check_grader_imports | PASS; the G-3 scan of the driver is empty and catches a planted brain import |
| ledger `--check` | 81 entries, PASS |

- The planted cases the task asked for all behave:
  - 6 crossings with nothing new between them read longest 6 and FAIL;
  - 7 crossings with news after the 2nd read alternations of 2 and 5 and PASS, once for each of N1-N4;
  - a woods exit at y 38 is not counted; one at y 30 from (14,5) or (15,5) is;
  - a 301,000,000-byte world file FAILS; 299,999,999 bytes PASSES;
  - a stale end state FAILS L5.THIS_RUN and so K8.THIS_RUN;
  - registering and then changing a bound or a start file is refused by `ledger.begin`.
- **Real data, read only:**
  - A0-1 (the old code): 2,425 edge crossings, 0 unmatched, longest alternation 65, no woods exit, world file 2,061,821,991 bytes. It would fail woods, alternation and size.
  - Round 2's Part-B development runs, read the strict way (only their last world line survives, so news is N1/N2 only): B longest 5 on S1 and S3; Bstop 5; none 62 and 63, equal to round 2's recorded E3. The 12 chapter 1-2 control runs: longest 1.
  - Round 1's long S2 and S3 read the woods exit as (14,5)->(10,30) at f572678 and (15,5)->(11,30) at f689171, with the log and the world memory agreeing.
- **Orchestrator dry run** (fake launches built from round 1's real S3 output, a temporary ledger and evidence folder, no emulator): 6 children, world files measured and deleted, ledger finished, OVERALL PASS.
  - A first attempt was refused by `ledger.begin` because a constant changed after registration: the refusal working end to end.

**Expected registration**
- On these exact bytes, `register` in main should print numbers sha256 `589a17e6cfc4f85b…`. Main's AI-code hash equals the worktree's, `017bbdb4…`.

**For you to decide**
- **B1 declaration.** The two graded checks that read the AI's logs (K8.WOODS, K8.ALTERNATION) are declared in a driver-local debt list. I did not add K8 rows to `grader_checks`/`b1_debt.json`, because `grader_checks.py` is hashed by rate_step5. If you want the global table, change it before registering.
- **Lane.** The test is not added to `run_units.py`.
- **regression_due.** Once committed, it will list `live_ki128.py` under ai_player/**.
- **Woods confirmation.** The game confirms a woods exit only through VISITED_RUSTBORO_CITY.
- **Where runs write.** The runs write profiles into main's sandbox, as A0 did; run them after the regression lane finishes.
- **Wall time** (estimated from A0's 311-357 frames/s): about 56-65 min if every run plays its full 600,000 frames; about 10-15 min if the runs stop at Rustboro as round 1's did.

## The verifier's section

## Independent adversarial verification: live_ki128 (the KI-128 + KI-129 graded held-out driver)

Nothing in the worktree was modified, and nothing was run live. Every script and output is in `scratchpad/s53/heldout/verify/`.

**Verdict:** the driver measures what its bounds text says, and it is hashed and gated correctly. But **one graded check is too weak to catch the failure it exists for (F1, MAJOR)**, and that needs a ruling before registration.

### (1) The woods check (y < 31)
- **It would not pass a run that skipped the woods.** On Route104 (decomp, pinned clone):
  - the only warps with y < 31 are the woods north pair at (10,30)/(11,30) and the flower shop at (5,18);
  - the flower shop can only be reached after the woods;
  - the connections are Rustboro (up), ROUTE105, which needs Surf (down), and Petalburg (right, at y 50 and below).
- **The three A0 runs** (about 2,300 crossings each): no y < 31 arrival.
- **It would not fail a run that did go through the woods.** The log line and the world.jsonl transition come from the same `Transition` object (`navigator.arrived`, `memory.describe`), so frame, tile and arrival are identical.
- **Round-1 runs, read by both readers:**
  - long S2: (14,5)->(10,30) at f572678;
  - long S3: (15,5)->(11,30) at f689171;
  - in both, `by_woods` is True in the log AND in the world memory.
- **Frame clock:** truth frames (L5.THIS_RUN: start 618180) and the AI's frames (first decision f618211) are on one clock, so `frame > start` is sound.
- **VISITED_RUSTBORO_CITY is a tracked mark** (milestones.json: 2169), so the game-confirmation and disagreement path is live.

### (2) The alternation reading
My own implementation, written from the bounds text, agreed with the driver exactly:

| Runs | Crossings | Longest alternation | Over 5 | Unmatched | Result |
|---|---|---|---|---|---|
| A0-1 | 2,425 | 65 | 51 | 0 | FAIL |
| A0-2 | 2,246 | 67 | 52 | 0 | FAIL |
| A0-3 | 2,343 | 64 | 48 | 0 | FAIL |
| Chapter 1-2 (6 runs) | 6-12 each | 1 | 0 | 0 | PASS |

Normal exploring is therefore not called a ping-pong.

**F1 (MAJOR): a real ping-pong can be read as clean.**
- Round 2's fault arm **Bstop** had the Part-B stop but not the honour. On S3 it crossed one edge **131 times in 10,000 frames**, with 25 stops and 31 intents. Per intent, the longest run is **5, so it PASSES**. The replicate run read 132 crossings, longest 5, PASS.
- **Every B run measured exactly 5**, which is Part B's own trigger (11 runs). So the graded check holds by construction for any code with the stop. It catches only "Part B absent": the none arms read 44-64.
- **Round 2 itself used D2w <= 10** (the most crossings of one edge in any 3,000-frame window):
  - B reads 5-8;
  - Bstop reads 17, 42, 33 and 43, plus 7 on one start;
  - none reads 44-65.
- **Recommendation:** register a cross-intent bound (D2w, or the no-news alternation with intents ignored) before registration, at least REPORTED.
- **Needs a ruling:** the spec's V2-1 wording is per-intent, so this is the orchestrator's or the user's call.

### (3) The bounds text and its hash
- `BOUNDS_TEXT`, every constant, the three start folders' file sha256, `ai_code_sha256` and 9 grader files are all in the numbers.
- On a temp ledger, `ledger.begin` refused each of these changes: WOODS_MIN, NORTH_Y, ALT_MAX, WORLD_MAX_BYTES, FRAMES, RUSTBORO_MIN, PARALLEL, GUARD_WORLD_BYTES, WOODS_NORTH_WARPS, an N3 `>` changed to `>=`, and an edit to navigator.py.
- **F2 (MINOR): two gaps in the hash.**
  - A change to `gates/probe_presses.py` alone **would proceed**, and it feeds check_purity, so it feeds K8.PURITY.
  - `sandbox-pokebot/plugins/custom_modes/ai_player_mode.py` (in FrozenTree's scope) and `modules/map_data.py` (the map keys) are not hashed.
- **Current numbers sha256:** 589a17e6cfc4f85bc895747036794c4e476f27a7df3512658ae60e388e69fa18 (bounds text sha256 e3e37a4b...). Taken with `--starts-from` the main sandbox: the default starts root resolves to the worktree's empty sandbox there, and that refuses.

### (4) The 300 MB size is read before deletion
- **The child path:** the size is read with `stat` before streaming, and again inside `measure_then_delete`, just before `unlink`.
- **The salvage path:** the same.
- **The launcher** deletes no world file.
- **F3 (MINOR):** a world.jsonl that another process still holds open makes `measure_then_delete` raise PermissionError (WinError 32, demonstrated). Neither salvage nor run_batch catches it, so the orchestrator would abort before grading: the seeds are spent, the ledger entry stays "started", and there is no evidence file.

### (5) Registration and seed reuse
On a temp ledger:
- a graded begin that was never registered: REFUSED;
- development on the registered seeds, or overlapping them: REFUSED;
- a second graded begin: REFUSED;
- re-registering after the start: REFUSED.

In run_batch, `begin` comes before any Popen. The real ledger (81 entries) names none of 5972-5977.

### NITs
- **F4:** `INTENT_LINE` requires an apostrophe, but intent names are printed with `repr`, which switches to double quotes when the name contains one (detour names). Observed in 0 of the 2,885 intent lines scanned.
- **F5:** a PowerShell failure in `leftover_processes` reads as "none left", and a timeout crashes the orchestrator before grading.

### Commands run (all read-only)
- `py -3.12 -B -m unittest ai_player.gates.test_live_ki128`: Ran 45 tests in 3.462 s, OK.
- `live_ki128.py bounds --starts-from ...`: printed the numbers above.
- `indep.py`: A0 x3, ch1-2 x6, the round-1 long runs, all round-2 live runs.
- `crossintent.py`, `bounds_mut.py`, `seed_reuse.py`, `locked_unlink.py`.

## The fixer's section

### Fix of verifier finding F1 (MAJOR): the alternation check could not see a ping-pong that runs across intents

**Verdict: F1 is confirmed and fixed. The fix adds a new graded check, K8.EDGE_WINDOW, which needs a ruling recorded in 06 before registration.**

**Reproduced first.** I ran the verifier's `crossintent.py` against the worktree driver on the real round 2 logs, and it gave the same numbers F1 reports:

| Run | Crossings | Intents | Edge stops | Per-intent longest (registered) | Intents ignored | D2w |
|---|---|---|---|---|---|---|
| partb-Bstop-S3 | 131 | 31 | 25 | 5 (PASS) | 131 | 42 |
| vpartb-Bstop-S3 | 132 | 31 | 26 | 5 (PASS) | 132 | 43 |
| vpartb-Bstop-S2 | 33 | 13 | 6 | 5 (PASS) | 33 | 33 |

- Every B, Bfix, Bpre and smoke-B run also reads exactly 5 per intent.
- So for any code with Part B's stop, K8.ALTERNATION holds by construction: Part B stops at 5, and a new intent restarts the count.

**The fix: a new check, K8.EDGE_WINDOW, graded.**
- **The rule:** in every run, at most 10 crossings of one edge within any 3000 frames, with intents ignored. This is round 2's own D2w <= 10 criterion.
- **How it is read:** from ai_player.log's edge MAP lines and their f<N> frames.
- **Strict:** a run with any crossing line that has no frame is not read, so the check is VACUOUS (a FAIL).
- **Reported beside it (information only):** the longest no-news alternation with intents pooled.
- **Registration:** the check is in the bounds text and in the registered numbers (edge_window_frames, edge_window_max, edge_window_kind), and it is declared as B1 debt.

**Real logs, read through the driver's own measure_run and grade_batch:**

| Logs | K8.ALTERNATION | K8.EDGE_WINDOW |
|---|---|---|
| A0 (3 runs) | FAIL: 65 / 67 / 64 | FAIL: 66 / 67 / 64 |
| chapter 1-2 r1base (6 runs) | PASS: 1 | PASS: at most 2 |
| round 2 none (5 runs) | not read (world files deleted) | FAIL: 65 / 64 / 57 / 44 / 65 |
| round 2 Bstop (5 runs) | not read (world files deleted) | FAIL: 17 / 42 / 7 / 33 / 43 (4 of 5 over) |
| round 2 B-family (14 runs) | not read (world files deleted) | PASS: 5 to 8 |
| round 2 chapter 1-2 control (12 runs) | not read (world files deleted) | PASS: at most 2 |
| round 1 long runs (4) | not read (world files deleted) | PASS: at most 1 |

**Tests**
- **Self-tests:** 55 tests, OK. The 10 new EdgeWindowTests include:
  - FAULT, the F1 shape (4 intents x 5 crossings): per-intent PASS, window 20 FAIL.
  - CONTROLS: Part B working reads 5; 40 crossings spread 400 frames apart read 8.
  - Boundary: 3000 frames reads 11 and FAILS; 3010 frames reads 10 and PASSES.
  - An unframed crossing makes the check VACUOUS.
- **Mutants:** 6 of 6 KILLED (window per intent, bound ignored, off by one, unframed runs read, edges pooled, check made REPORTED).

**Numbers sha256 in the worktree:** be76c976661a81b2ecdfefa43b4bd9906d405dae55238bbb67252ed6786eafcc (the bounds text: 2bfb3ab2...). Re-read it in main when registering.

**Open items**
- **Ruling needed:** GRADED or REPORTED, against the spec's per-intent V2-1 wording. Record it in 06 before registration.
- **Risk:** the shipped Part B read up to 8 against the bound of 10, but only in 10,000-frame runs. The held-out runs are 600,000 frames.
- **Known gap:** vpartb-Bstop-S1 reads 7 and still passes.
- **Not done:** no live runs, nothing committed.
