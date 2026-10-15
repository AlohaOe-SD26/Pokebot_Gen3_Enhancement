# AI player: a LIVING LESSONS list (DRAFT for the coordinator, 2026-10-15)

> **This is a NOTE, not a source of truth** (CLAUDE.md, the research-notes rule). It was written by a research subagent
> during a running full regression and is READ-ONLY with respect to the code. Nothing here was run against the AI. Each
> claim is marked **VERIFIED** (read in our code or docs, with the file:line) or **UNVERIFIED**. The 08/07/README/06
> citations are this checkout's working tree on 2026-10-15.
>
> **Person-fairness (USER RULINGS 35-37):** every coordinate, flag name and route in this folder is for the DEVELOPERS
> (proof design and expectations). None of it may be fed to the AI as a hint. Lesson PL-7 and missing gate #4 exist to
> make that mechanical.

## How the list stays "living" (the user's 2026-10-15 directive, `06` USER RULING 38 entry)

* **Status of each lesson:** `GATED` (named gate, test or mutant; the prose is only a pointer), `PARTIAL` (a gate covers
  part of it), or `PROSE ONLY` (with a concrete gate proposal). `RETIRED` lessons move to a "Retired" section with the date
  and the gate that made them impossible. They are never deleted; `08` keeps the history.
* **Add:** at every round's end (`/wrapup`), each "Found and fixed" bullet of the round adds a lesson or extends one. A
  lesson needs the mistake that earned it, with its date.
* **Retire:** only when a gate exists AND has been fault-tested both ways (CLAUDE.md SESSION DISCIPLINE rule 6: it fails
  when the guarded thing breaks, and it does not fire on mere mentions). Change a lesson only to prevent mistakes, never to
  ease a check (the user: "free to update ... only if they ensure no mistakes happen").
* **Load:** paste the ACTIVE lessons (`PROSE ONLY` and `PARTIAL`) into every AI-player builder, verifier and reviewer
  prompt. **VERIFIED gap:** neither `.claude/skills/story-drive/SKILL.md` nor `unlazy/SKILL.md` mentions `ai_player`
  (0 hits each), so today no skill carries these lessons into an AI-player round.
* **VERIFIED doc gap:** `08-MISTAKES.md` has nothing after 2026-10-14 (its last entry is at `08:23856`). Step 5.1's own
  lessons live only in `ai_player/README.md:856-1237`: the bound taken from the base personality, LOSE3's vacuous run, a
  result claimed for another tree, the OLDALE door across the map edge, and the known-gym-door walk that skipped its stops.
  They are folded in below. The coordinator should append them to `08`.

---

## A. PROCESS: fix rounds, regression, evidence, commits

**PR-1. A fix round runs only for a FAILURE or a rule violation; weak proofs go onto the next step's list.**
* Earned by: step 5's second round ran 1.5-2 h with nothing failed, and step 5.1 took about 15 h. VERIFIED, `06` entry
  "2026-10-15 — The AI player's development rounds".
* Enforced: PROSE ONLY (the decision, plus the workflow script).
* Gate proposal: the workflow's refix stage runs only when the verifier's JSON has `all_pass:false` with a non-empty
  FAILURES list.
* Retire: when the workflow encodes it.

**PR-2. Run the suites of the code a step touched (and every earlier step's suites for a shared file it changed). Run the
full regression at each CHAPTER boundary and before any promotion.**
* Earned by: 10+ hours per step when everything was re-run (VERIFIED `07:37929`), and the 5.1 rule violation (PR-3).
* Enforced: PARTIAL. `provenance.py --check-evidence` lists every top-level evidence file of another tree (VERIFIED
  `ai_player/gates/provenance.py:192-201`), but nothing maps a suite to the files it covers.
* Gate proposal: `regression_due.py`. A map of suite to files exercised, and `provenance.py --compare <tree of the
  suite's newest evidence> <now>`, print every suite that is STALE. The chapter-boundary checklist must show it empty.
* Retire: when that tool is in the checklist.

**PR-3. State a result only for the tree its evidence file names.**
* Earned by:
  * 5.1 round 1 (2026-10-14): a regression was claimed on `c450adc` while `rate_step4` had run without `--evidence`,
    leaving 18 files of another tree. VERIFIED, `README:881-888`.
  * The step-5 verifier: "two round-2 claims ... have no evidence file". VERIFIED, scratchpad `step5_findings.md:11`.
* Enforced: PARTIAL. The evidence side is a gate (`--check-evidence`); the README/`07` sentence side is PROSE.
* Gate proposal: `check_claims.py`. Every README/`07` line that names a suite with PASS must cite an evidence file, and
  that file's `code:` digest must equal the digest the sentence names. Plant a mismatch as the fault test.
* Retire: when built and fault-tested.

**PR-4. Archive a run's evidence before cleaning anything it produced. Failed passes are kept, never overwritten.**
* Earned by: the 2026-10-03 smoke test (`08:23818`).
* Enforced: GATED for the graded drivers. Before writing, each calls `keep_earlier`, which moves the older file to
  `evidence/archive/<digest>/` (VERIFIED: `rate_step5.py:1521`, `live_step5.py:614`, `revert_step5.py:741`,
  `run_units.py:93`). Each tree is kept as a zip by `snapshot_tree` (`provenance.py:146`).
* Retire: the prose for ai_player drivers now. Keep it for ad-hoc scripts.

**PR-5. Never change the tree a long driver is running on. A driver must PROVE the tree did not move.** ⭐ MISSING GATE #1
* Earned by:
  * 2026-10-03: a docs commit killed learner cycle ai0002 (`08:23833`).
  * Today: this research runs under an instruction not to touch `ai_player/` because a regression "fingerprints" it.
* VERIFIED gap:
  * `rate_step5.py` prints `provenance(REPO)` ONCE, at the start (`:1460`).
  * It starts every run as a fresh subprocess that imports the live tree (`:366`).
  * It writes the evidence at the end (`:1520-1522`) with no re-check.
  * So an edit mid-sweep is graded under the start digest, silently. A grep found no mid-run digest re-check in any
    `ai_player/gates/*.py`.
* Enforced: PROSE ONLY (instructions to agents).
* Gate proposal: in `provenance.py`, add `FrozenTree(start_digest)`.
  * Every graded driver (rate/live/revert/run_units) calls `.check()` before each job submit and before writing evidence.
  * On a change, the evidence's verdict becomes `INVALID: tree moved <a> -> <b>` with exit 3.
  * Fault test: touch a file in a copy mid-run; the verdict must be INVALID.
* Retire: when wired into all four driver kinds and fault-tested.

**PR-6. Stage explicit paths and name every file in the commit. Commit before any review that may mutate files. No
destructive git.**
* Earned by: CLAUDE.md rules 1 and 1b (2026-08-13; 2026-09-27, a reviewer's `git checkout` deleted an uncommitted fix).
* Enforced: GATED by `.claude/hooks/block-blind-git-add.ps1` and `block_destructive_git.py`, with their selftests
  (VERIFIED, the files exist in `.claude/hooks/` and `tools/story-dev/`).
* Why it is acute here: a round touches hundreds of evidence files at once (the session's `git status` lists ~100+
  modified `ai_player/evidence/*.txt`).
* Retire: no. The hooks are the enforcement; the prose shrinks to a pointer.

**PR-7. A reviewer's fix is a claim: one REAL launch before adopting any interpreter or launch flag.**
* Earned by: `python -s`, 2026-10-07 (`08:23849`).
* Enforced: PARTIAL. `check_package_resolution` (VERIFIED `ai_player/host/launcher.py:225`) covers the shadowing risk.
  The "one real launch" is PROSE.
* Gate proposal: `run_units.py` runs live_step0 arm A (a real launcher start, about 1 min) whenever `host/launcher.py` or
  the hook file differs from the last kept tree.
* Retire: when wired.

**PR-8. Every evidence header carries a recomputable working-tree digest.**
* Earned by: step 2's seed-9 replication ran on code that changed afterwards (VERIFIED `07:37848`; `provenance.py:11-16`).
* Enforced: GATED by `provenance.py` (sha256 of `git diff HEAD` plus untracked files), `--check-evidence`, and
  `test_evidence.py` SnapshotTests.
* Retire: the prose (structural).

**PR-9. Doc and code text goes through the Write tool, never a shell-quoted string.**
* Earned by: five slips, `08:23633-23665` (2026-10-01).
* Enforced: GATED by `.claude/hooks/block_shell_text.py` and `selftest_shell_text_hook.py`.
* Retire: the prose.

**PR-10. Before escalating to the user, `grep -i` `06-DECISIONS-LOG.md`.**
* Earned by: CLAUDE.md rule 11. The AI player now rests on RULINGS 32-38, all in `06:9112-9300`.
* Enforced: PROSE ONLY. No gate is proposed (a judgement step).

**PR-11. Each round's "found and fixed" goes to `08` as well as the README.**
* Earned by: the VERIFIED gap above (no `08` entry for step 5.1).
* Enforced: PROSE ONLY.
* Gate proposal: a `/wrapup` check. A new `G<n>` mutant in `revert_step5.py` (or its successor) whose description cites
  a verifier or review finding needs a matching `08` entry or lessons line.
* Retire: when wired.

---

## B. PROOFS: property not label, call-deleting mutants, independent reads, held-out seeds, pre-registration, no-op arms

**PF-1. Grade the PROPERTY, never the label the code chose for itself.**
* Earned by:
  * 2026-10-14 (`08:23856`): the idle check counted only the catch-all reason, while 600-1,200-frame stalls ran under
    named reasons.
  * Step 3.2 (VERIFIED `07:37901`): the reversal metric counted only A-B-A turns, so laps scored 0.
* Enforced: GATED.
  * `WaitWatch` (`ai_player/hands/waiting.py:32`) and the game-side `WaitRecorder` (`gates/play_harness.py:230`).
  * `AWAIT_MAX` 300 (`rate_step5.py:232`); the two paths must agree run by run.
  * STALL1, STALL2 and STALL3 must FAIL it.
* Gap: a launcher (live) run has only the AI's own record (VERIFIED `README:1222`). Chapters 3-4 bring new input screens
  (the woods scene, the DEVON researcher, the gym), which the second path must be shown to see (a STALL-style fault arm
  on one of them).
* Retire: never as a principle.

**PF-2. For every new hook, the mutant DELETES ITS CALL, not just its body.** ⭐ MISSING GATE #3
* Earned by: 2026-10-14. `battle_rest` was asked only `if self.battle_limit is not None` (G36); losses were counted on
  the main path only (G46). VERIFIED `revert_step5.py:192`, `:234`; `08:23863-23864`.
* Enforced: CASE BY CASE (G36, G46, G55 `revert_step5.py:273`). There is no census, so a new hook with a body-only mutant
  passes review.
* Gate proposal: `revert_step5.py --call-census`.
  * For every function added or changed in `brain/`, `skills/`, `hands/` or `mode.py` since the last kept tree
    (`provenance --compare`), list its call sites by AST.
  * Each needs a mutant whose edit anchor contains that call (removes it or guards it off), or a written REDUNDANT
    reason.
  * Fault test: add an uncalled-hook plant; the census must list it.
* Retire: when the census is part of `revert_step5` (or its step-6 successor).

**PF-3. A metric is a claim only once it FAILS its control (the no-op or beeline arm).**
* Earned by: the 5.1 verifier, 2026-10-14. ERRANDS_OFF met the intent-mix floor 10 of 10, and the beeline met the seed
  divergence (VERIFIED `README:890-911`).
* Enforced: GATED for today's metrics. In the `rate_step5` verdicts the beeline must fail the curiosity check in at least
  80 % of runs, and CH2_OFF must fall under the floor (19 of 20, `README:1191`). Nothing obliges a NEW metric to do the
  same.
* Gate proposal: a meta-test in `test_goals.py`. Every `BOUNDS` key declares `control_plan` plus a separation bound, or is
  labelled `FLOOR` or `REPORTED`. A planted unlabelled key must fail.
* Retire: when the meta-test exists.

**PF-4. A fault arm must REACH the state it tests. Grade only the runs that reached it, with a reach-rate floor.**
* Earned by: LOSE3 seed 503, which never reached a third loss (2026-10-14, VERIFIED `README:985-994`); CLAUDE.md rule 4.
* Enforced: GATED for LOSE3 (`LOSE3_REACH_MIN` 0.6, `rate_step5.py:300`; G106). PATIENCE reports "N of N reached". For a
  new fault arm it is PROSE.
* Gate proposal: fold it into PF-3's meta-test. Every fault plan declares its reach predicate and floor.

**PF-5. Derive a check's parameters from the state the run actually reached (whose rule judged it), never from a
default.**
* Earned by: the training bound was taken from the BASE personality while runs 506 and 516 had drifted (2026-10-14,
  VERIFIED `README:975-984`).
* Enforced: GATED. `judged_by` is logged; G105, G120, G121.
* Retire: the prose (keep CLAUDE.md rule 4 as the general rule).

**PF-6. Independent ground truth: read the game by code the AI does not share (raw save-block flags, the framework's
reads, pret's decomp), never with the AI's own constants.**
* Earned by:
  * Step 1: the eyes missed text-printer state 1, found by BEHAVIOUR under an A press (VERIFIED `07:37823`).
  * Step 3.1: the crop check shared the eyes' constants (VERIFIED `07:37882`, `:37893`).
* Enforced: GATED. The `live_step*` checks use the framework's reads; `extract_milestones.py --verify` and `--plant` check
  against pret.
* Retire: never (a principle).

**PF-7. Grade on HELD-OUT seeds: never used in development, and never re-graded after they failed.** ⭐ MISSING GATE #2
* Earned by: the 5.1 rounds, which moved 401-410 to 501-520 to 601-620 to 701-720 to 801-820 because the earlier seeds'
  results were known (VERIFIED `rate_step5.py:65-78`).
* VERIFIED gaps:
  * The held-out record is a docstring.
  * `--first-seed` defaults to **1** (`rate_step5.py:1443`), a development seed: a graded sweep with default arguments
    plays development seeds and says nothing.
* Enforced: PROSE ONLY.
* Gate proposal: `ai_player/gates/seed_ledger.jsonl`, committed.
  * Each sweep appends {seed range, purpose dev/graded, tree digest, `BOUNDS` sha256, `PREDICTED` sha256}.
  * In graded mode (`--evidence`), `rate_*` REFUSES a seed range that overlaps any earlier entry, and refuses a `BOUNDS`
    hash that differs from the entry registered before the run.
  * Fault tests: overlapping seeds, and a changed bound.
* Retire: when the ledger is enforced by `rate_step5` and its successors.

**PF-8. Pre-register bounds and predictions before any run. Never loosen a bound to pass. A number set after
observation is labelled RE-REGISTERED and re-run as a replay.**
* Earned by:
  * Step 4: held-out FAILs were left in the evidence, not loosened (VERIFIED `07:37919`).
  * Step 4.1: three numbers were re-registered after observation (VERIFIED `07:37951`).
  * 5.1: the CH2T floor was not re-bounded (VERIFIED `README:1049`).
* Enforced: PARTIAL. `rate_step5` prints `BOUNDS` into the evidence header at the start (VERIFIED `:1459`), which proves
  them for that sweep. Changing a bound and re-running the same seeds is caught only by the PF-7 ledger.
* Retire: with PF-7.

**PF-9. Identical output across runs is a DETERMINISM check, never a replication. A live arm is one trajectory.**
* Earned by: CH2T was pre-registered from an in-process run that was the same trajectory (5.1 round 1), and five of six
  arms ended on the same frame on two trees (round 2). VERIFIED `README:849`, `:1197`; CLAUDE.md rule 8.
* Enforced: PROSE ONLY (README caveats).
* Gate proposal: `live_step5` (and step 6's live driver) compares each arm's end frame and `actions.jsonl` sha256 with
  the same arm in the newest archived evidence, and prints `REPLAYED <tree>` in that arm's verdict line.
* Retire: when built.

**PF-10. A premise or after-state check must be able to FAIL.**
* Earned by: step 0's review, "after-state checks can pass on the untouched seed" (VERIFIED `07:37789`); `08:23756`.
* Enforced: GATED for A2 and W2 (md5 != seed, frames advanced). For new drivers it is PROSE (story-drive's "point the
  driver at its own OUTPUT fixture").
* Retire: never (each new driver needs its own premise conjunct).

**PF-11. A predicted-REDUNDANT mutant is a claim: run it.**
* Earned by: G86, first registered REDUNDANT ALONE, was in fact CAUGHT (VERIFIED `README:851`; `revert_step5.py:397`).
* Enforced: GATED. `revert_step5` runs every mutant and checks its prediction (`:706-734`).
* Retire: the prose.

**PF-12. A unit-tested rule is not a chapter proof.**
* Earned by: "optional gym trainers" and "ROXANNE by her badge alone" are unit-only. No save holds the badge with the gym
  trainers unbeaten (VERIFIED `README:1181-1185`, `:1206-1208`).
* Enforced: PROSE ONLY.
* Gate proposal: chapter 4's sweep grades BADGE01_GET by the game, and REPORTS the JOSH and TOMMY flags (never requires
  them). A fault arm makes the trainers mandatory again (mutant G74) and must lose the claim.
* Retire: when the chapter-4 arm passes.

**PF-13. An instrument's false alarm is first a finding about the instrument.**
* Earned by: the second path read a stale printer state as a 510-frame wait at a battle's opening (VERIFIED
  `README:750-753`). The fix was the controller condition, with STALL3 to prove the reads are not blind (`README:958-968`).
* Enforced: GATED (STALL3, and the two paths agreeing 213 of 213).

---

## C. PLAY: never idle, no hidden information, bounded loops, patience

**PL-1. Never idle (RULING 37 Q6): no stretch of `AWAIT_MAX` frames while a screen waits for a press, whatever the
reason.**
* Earned by: the two step-5 stalls (2026-10-14), and the nurse stall in dev2 seed 42 (`README:1137-1140`).
* Enforced: GATED. PF-1, plus G54-G57, G86, G117, G118, G134, G135.

**PL-2. Scenes come first.** Settle `SETTLE_FREE` (30) frames after a map change (VERIFIED `mode.py:113`). Story skills
`give_way` to a waiting screen.
* Earned by: the lab stall (2026-10-14).
* Enforced: GATED (G56, G57, G117, G118).

**PL-3. A failure returns at once. Never retry silently.**
* Earned by: the GIRL choice failed in every intro, and a silent re-choose hid it (VERIFIED `07:37868`, step 2.1).
* Enforced: GATED. Step 2.1's revert proof: "sub-skill failures returned at once".

**PL-4. Bound every loop:** each errand has a frame budget, and a `while True` needs both a budget and a "no frame
passed" cap.
* Earned by: the step-5 verifier's "every `while True` ... has a frame/attempt bound" (VERIFIED `mode.py:114`).
* VERIFIED state:
  * One `while True` remains in AI code, `brain/navigator.py:1131`. It is bounded by `intent.budget` (`:1132`) and
    `STILL_DECISIONS` 50 (`:1137`, `:242`).
  * The play loop is a `for` over `PLAY_PASSES_MAX` (`mode.py:119`).
* Enforced: PROSE plus review. There is no static check.
* Gate proposal: an AST rule in `check_purity.py`. Any `while` in `brain/`, `skills/`, `hands/`, `world/` or `mode.py`
  must be in an allowlist naming its bound constant. A planted unbounded loop must be refused.
* Retire: when built.

**PL-5. Patience counts from REAL progress.** That means a milestone, battles won, one Pokemon's level by PID, a new map,
a catch, an item, or a heal (capped at `HEAL_RESETS_MAX` 3, `mode.py:108`). Failing goals still stop.
* Earned by: review #2 (2026-10-14), and "a level gained was the party's SUM" (5.1 round 2, G119).
* Enforced: GATED (G67, G68, G119; the PATIENCE and PATIENCE_OLD arms).
* Chapter-4 note: the training stints before ROXANNE are the longest yet. PATIENCE showed stints of 58k-96k frames
  against `STORY_PATIENCE` 120,000 (`mode.py:102`; `README:1191`). Re-measure them in chapter 4.

**PL-6. No goal loops forever.**
* What the AI does:
  * A story goal cools down after `FAIL_LIMIT`, for N decisions OR `STORY_ASIDE_FRAMES`.
  * A door it cannot use is forgotten.
  * Retries in danger are capped.
  * A walk is extended when battles ate its budget.
* Earned by: review #5; CH2's 10 looks round; the OLDALE door past the edge (dev1 seeds 33, 36, 37, 38;
  `README:1125-1131`).
* Enforced: GATED (G78, G96, G97, G127-G129; `ASIDE_STREAK_MAX`).

**PL-7. No hidden information. Hints only at the level of the dialogue and signs.** ⭐ MISSING GATE #4
* Earned piecemeal:
  * Foe HP as the bar, only the moves seen, every person an "npc" (`test_eyes.py:748`, `:763`; step 1.1).
  * Map edges: the +50 coordinate shift (`test_world.py:686`; step 3.1).
  * Exits by visible behaviour, with `warp_reads.py` scanning against 444 ROM warp arrays (`07:37892`).
  * No catch rate (`test_battle.py:611`); no base stats (4.1).
  * Fight levels only for NAMED fights (G72).
  * No invisible flags for errands (G12, G76, G77).
  * Whole words actually read (G30), each step's own words or a visit (G69, G70).
* VERIFIED gaps:
  * Milestone flags reach the brain as a plain dict, `progress.marks` (`brain/goals.py:381`; `mode.py:395`, `:417`,
    `:587`). Any errand can read any mark, which is exactly how step 5 shopped on FLAG_ADVENTURE_STARTED and healed
    on FLAG_RESCUED_BIRCH (`brain/goals.py:13-18`, `:811`, `:1149`).
  * `knowledge/milestones.json` holds 2 x/y pairs (the clock's `measured` entries). The AI code has no `["x"]` or
    `.get("x")` read today (grep over `brain/`, `knowledge/`, `skills/`, `mode.py`, `personality.py`: 0 hits).
    Nothing stops one.
  * Chapter 3-4 recon (this folder) is full of developer coordinates.
* Enforced: PIECEMEAL GATES; there is no general door.
* Gate proposal: `check_fairness.py` (or new `check_purity` rules).
  * (a) `.marks` is read only inside an allowlist: the milestone detection in `GoalManager` and `mode.py`'s progress.
  * (b) No AI module subscripts the knowledge keys `x`, `y`, `measured` or `decomp`.
  * (c) The knowledge files the AI loads pass a schema allowlist.
  * Fault plants: an errand keyed on a mark, and a coordinate read. Each must be refused. A docstring that mentions
    `.marks` must NOT be refused.
* Retire: never as a principle; the per-case prose can shrink once the gate exists.

**PL-8. Play like a person, never a speedrun (RULING 32).**
* Enforced: GATED by the `rate_step5` BOUNDS:
  * curiosity the story did not need, in every run;
  * off the beeline;
  * no speedrun without the grass's dice;
  * chapter 2's floor, with CH2_OFF under it.
* Caveat: the BALANCE makes the floor partly the AI's own aim (VERIFIED `README:1209-1217`). The separation checks
  (PF-3) carry the claim, not the floor.

**PL-9. Count outcomes where they happen: the report, the told count and the game agree.**
* Earned by: 2026-10-14, "battles lost 0" over two whiteouts.
* Enforced: GATED (G46; "losses agree 210 of 210").

**PL-10. Identity, never a count or a slot (CLAUDE.md rule 3).** A catch is a NEW PID with the player's OT; a level is
gained by PID; SHIFT carries the chosen PID.
* Earned by: step 1.1 (Wally's tutorial Ralts), 4.1, and 5.1 round 2 (the party's SUM).
* Enforced: GATED (`live_step4` CATCH, G119).

**PL-11. Every printed reason must be TRUE.** Examples: it "WANTS" a species before it has a ball; a milestone "done" on
a waypoint; DAD as a "chat".
* Earned by: the step-5 verifier, and 5.1 round 2.
* Enforced: CASE BY CASE (G79, G80, G130).
* Gate proposal: a log-consistency pass in the sweep grader.
  * A "WANTS" line needs balls > 0 at that frame.
  * A "done" line needs its proofs to hold, or a WAYPOINT or OPTIONAL label.
  * A chat target must not be the current step's person.
* Retire: when built.

---

## D. ENVIRONMENT: host clock, temp folders, deployment clone

**EN-1. A launcher run's cartridge clock is the HOST's. Live arms differ by time of day and cannot be replayed.**
* Earned by: step 3.1 (VERIFIED `07:37898`); CH1C diverged on the same code (`README:875-877`).
* Enforced: sweeps GATED, pinned by `--game-clock` (`rate_step5.py:110`, `:358`). Live runs are PROSE (VERIFIED
  `live_step5.py:99`; `host/launcher.py` has no RTC option).
* Gate proposal: the live evidence header records the host's local time at launch and the RTC the eyes read at the first
  look, so "did not replay" can be attributed. Do not pin the RTC through a write: purity forbids writes.

**EN-2. Sweeps fill %TEMP% and the disk.** ⭐ MISSING GATE #5
* VERIFIED measurements, 2026-10-15:
  * `C:\Users\Ripto\AppData\Local\Temp` has 26,738 top-level folders, 24,355 of them `ai_*` (1,806 modified today).
  * `ai_step5_*`: 1,543 folders, 12,379,412 KiB (about 11.8 GiB, about 8 MB a run: `actions.jsonl` ~2 MB, `world.jsonl`
    ~4 MB, an end state).
  * `ai_rate3_*`: about 5.5 GiB.
  * C: is 96 % used, 76 GB free (`df`).
  * The brief's "5,423 folders / 12 GB" matches the `ai_step5_*` size, not my folder count.
* VERIFIED causes:
  * `rate_step5.run_one` makes a `mkdtemp` per run (`rate_step5.py:352`) and never removes it. Its only cleanup removes
    the package copies (`:1509-1511`).
  * `rate_step3.py:498` is the same: its only `rmtree` (`:847`) removes the copy root.
* Enforced: NOTHING.
* Gate proposal:
  * (a) Each sweep writes under ONE root, `%TEMP%/ai_sweep_<digest>_<stamp>/`, and deletes it after grading. A chapter-2
    chain deletes its chapter-1 end state once the chain ends. Opt in with `--keep-runs`.
  * (b) A preflight refuses to start when free disk is under (runs x 10 MB + 20 GB).
  * (c) `run_units.py` prints the size of `%TEMP%/ai_*` and WARNs above 5 GB.
  * Deleting the existing folders is the coordinator's or the user's call. This note deleted nothing.
* Retire: when (a) and (b) are fault-tested.

**EN-3. A long-lived process never runs from the development checkout. List every abort trigger as the guard measures
it.**
* Earned by: 2026-10-03 (`08:23833`).
* Enforced: STRUCTURAL. The learner runs from `C:/Remote Projects/pokebot-learner` and fast-forwards between cycles.
* Retire: the learner half now. The same shape inside this checkout is PR-5.

**EN-4. The framework's dependencies live in the USER site-packages: never `python -s`.**
* Earned by: 2026-10-07.
* Enforced: GATED, by a comment beside `bot_command` and live_step0's real launches (PR-7).

**EN-5. The learner runs 8 lanes now; back to 16 only when the AI player hands it something NEW to test. A plateau is no
reason to scale up (RULING 38).**
* Enforced: config. VERIFIED `ai-agent/config.json:4-5` `"max_lanes": 8`, with the trigger written beside it.

**EN-6. CPU contention.** Sweeps default to 8 workers (VERIFIED `rate_step5.py:1444`) alongside the learner's lanes.
* UNVERIFIED: no incident of a wall clock firing under load was found.
* Proposal: the evidence header records the learner's running lane count, so a timing outlier can be attributed.

---

## ⭐ The 5 most valuable gates still missing (ranked)

1. **FROZEN-TREE WATCH (PR-5).** A graded verdict over code that changed mid-run is the one failure that silently
   poisons every other proof. Today's only defence is an instruction to agents.
2. **SEED + BOUNDS LEDGER (PF-7, PF-8).** It enforces "held-out" and "pre-registered" mechanically. The default
   `--first-seed 1` is a development seed today.
3. **CALL-SITE CENSUS (PF-2).** The 2026-10-14 dead-fix class (G36, G46) is caught only when a reviewer happens to look.
4. **PERSON-FAIR DATA DOOR (PL-7).** Chapters 3-4 bring the most developer-only data yet (coordinates, trainer
   positions, the woods' scene). `progress.marks` is an open dict today.
5. **TEMP/DISK BUDGET (EN-2).** About 18 GB has already leaked, and the disk is 96 % full while the learner and the
   sweeps write.

Runners-up, in order: `check_claims.py` (PR-3), the replay detector (PF-9), the `while`-loop allowlist (PL-4), the BOUNDS
control meta-test (PF-3, PF-4), `regression_due.py` (PR-2), and chapter 4's badge-alone arm (PF-12).

## Retired (none yet in this draft)

The candidates whose PROSE can retire now, because a structure enforces them: PR-4 (for the drivers), PR-8, PR-9, PF-5,
PF-11, and EN-3's learner half. The coordinator decides; record each retirement in `08`.
