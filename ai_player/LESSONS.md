# The AI player's LESSONS (a living list)

Built 2026-10-15 (build step 5.2, G7) from the research note
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-15-ch34-recon/06-lessons-draft.md`, which is a NOTE: every line here was re-checked
against the code it names. `gates/check_lessons.py` (run by `run_units.py`) FAILS when a lesson's **Enforced** line names a
gate, test, mutant, bound or file that does not exist, or when an **Origin** quote is not found in the document it cites.
(Build step 5.3, A1-4) An **Enforced** line may name a step-5 grader CHECK by its id (`R5.*`, `L5.*`, the table in
`gates/grader_checks.py`), and it must be one that COUNTS in the verdict (GRADED or HONESTY). A REPORTED or DIAGNOSTIC check,
or a bound only such checks read, enforces nothing: it goes on the lesson's optional **Reported** line, which the checker
resolves the other way.

**How the list stays living.**
* **Add:** a new mistake (an `08-MISTAKES.md` entry, or a round's "found and fixed") adds a lesson here, or extends one, in
  the same commit: the rule, its Origin, and the gate that enforces it. A lesson with no gate is `PROSE ONLY` and must name
  the gate it **Needs**.
* **Enforce:** prose rules fail (CLAUDE.md session rule 6). Each lesson aims at a gate fault-tested both ways: it fails on
  the thing it guards, and stays silent on a mere mention.
* **Retire:** only when a gate makes the mistake impossible. Move the lesson to **Retired** with the date and the gate, and
  log the retirement in `08-MISTAKES.md`. Change a lesson only to prevent mistakes, never to ease a check.
* **Load:** paste the lessons that are `PROSE ONLY` or `PARTIAL` into every AI-player builder, verifier and reviewer prompt.
* **The gates' own proof:** `gates/revert_safety_gates.py` breaks each step-5.2 gate (or deletes the CALL that wires it in)
  in a copy; its tests must fail (mutants S1-S23, every one CAUGHT). This list's checker is mutated there too (S20-S22).

Status words: `GATED` (a named gate or test enforces it), `PARTIAL` (a gate covers part of it; **Needs** names the rest),
`PROSE ONLY` (no gate yet; **Needs** names one). Origin quotes are checked in `08` (`PROJECT KNOWLEDGE/08-MISTAKES.md`), `07`
(`07-CHANGELOG.md`), `06` (`06-DECISIONS-LOG.md`), `README` (`ai_player/README.md`), `REVIEW` (the step-5.1 review findings)
and `CLAUDE` (`CLAUDE.md`).

## A. Process: rounds, regression, evidence, commits

### PR-1. A fix round runs only for a FAILURE or a rule violation; weak proofs go to the next step's list.
- **Origin:** 2026-10-15, 06 "a fix round only for a FAILURE".
- **Status:** PROSE ONLY
- **Needs:** the workflow's refix stage runs only when the verifier's JSON has `all_pass:false` with a non-empty FAILURES list.
- **Retires:** when the workflow encodes it.

### PR-2. Run the suites of the code a step touched; the full regression at each CHAPTER boundary and before a promotion.
- **Origin:** 2026-10-15, 06 "the full regression of every step at a CHAPTER boundary".
- **Status:** PARTIAL
- **Enforced:** `gates/provenance.py::check_evidence` lists every top-level evidence file of another tree.
- **Needs:** `regression_due.py`: a map of suite to files, printing every suite whose newest evidence is on another tree.
- **Retires:** when that tool is in the chapter-boundary checklist.

### PR-3. State a result only for the tree its evidence file names.
- **Origin:** 2026-10-14, README "18 files" (a regression claimed while `rate_step4` ran without `--evidence`).
- **Status:** PARTIAL
- **Enforced:** `gates/provenance.py::check_evidence`, `gates/test_evidence.py::KeepEarlierTests`.
- **Needs:** `check_claims.py`: a README or `07` line naming a suite with PASS must cite an evidence file of the digest it names.
- **Retires:** when built and fault-tested.

### PR-4. Archive a run's evidence before cleaning anything it produced; a failed pass is kept, never overwritten.
- **Origin:** 2026-10-03, 08 "A SMOKE TEST'S DATA WAS CLEANED BEFORE ITS EVIDENCE WAS ARCHIVED".
- **Status:** GATED
- **Enforced:** `gates/provenance.py::keep_earlier`, `gates/provenance.py::snapshot_tree`, `gates/test_evidence.py::KeepEarlierTests`, `gates/test_evidence.py::SnapshotTests`.
- **Retires:** the prose for the ai_player drivers (kept for ad-hoc scripts).

### PR-5. Never change the tree a long driver runs on; the driver PROVES the tree did not move.
- **Origin:** 2026-10-03, 08 "A DOCS-ONLY COMMIT KILLED THE LEARNER'S 12-HOUR CYCLE"; the lessons draft's missing gate #1.
- **Status:** GATED (build step 5.2, G1)
- **Enforced:** `gates/provenance.py::FrozenTree`, `gates/provenance.py::watch`, `gates/test_safety_gates.py::FrozenTreeTests`, `gates/test_safety_gates.py::WiringTests`, `run_units:test_safety_gates`, `revert_safety_gates:S1`, `revert_safety_gates:S2`. Wired: `gates/rate_step5.py::run_one` (before and after every run), `gates/live_step5.py::main`, `gates/revert_step5.py::main`, `gates/run_units.py::main`; every other driver through the backstop in `gates/provenance.py::keep_earlier`.
- **Retires:** the prose, once a step has run on it with no false alarm.

### PR-6. Stage explicit paths and name every file in the commit; commit before a review that may mutate files; no destructive git.
- **Origin:** 2026-09-27, CLAUDE "Never discard uncommitted work with git" (a reviewer's `git checkout` deleted an uncommitted fix).
- **Status:** GATED
- **Enforced:** `.claude/hooks/block-blind-git-add.ps1`, `.claude/hooks/block_destructive_git.py`.
- **Retires:** no: the hooks are the enforcement; the prose is a pointer.

### PR-7. A reviewer's fix is a claim: one REAL launch before adopting an interpreter or launch flag.
- **Origin:** 2026-10-07, 08 "A REVIEWER'S `python -s` SUGGESTION BROKE THE AI PLAYER'S LAUNCH".
- **Status:** PARTIAL
- **Enforced:** `ai_player/host/launcher.py::check_package_resolution`.
- **Needs:** `run_units.py` runs live_step0's arm A (a real launch) whenever `host/launcher.py` or the hook changed.
- **Retires:** when wired.

### PR-8. Every evidence header carries a recomputable working-tree digest.
- **Origin:** 2026-10-08, 07 "AI player step 2.1" (the seed-9 replication ran on code that changed afterwards).
- **Status:** GATED
- **Enforced:** `gates/provenance.py::tree_digest`, `gates/test_evidence.py::SnapshotTests`.
- **Retires:** the prose (structural).

### PR-9. Doc and code text goes through the Write tool, never a shell-quoted string.
- **Origin:** 2026-10-01, 08 "#27-shellhook" (USER RULING 29, after five slips).
- **Status:** GATED
- **Enforced:** `.claude/hooks/block_shell_text.py`.
- **Retires:** the prose.

### PR-10. Before escalating to the user, `grep -i` the decisions log.
- **Origin:** 2026-08-23, CLAUDE "BEFORE ESCALATING ANYTHING TO THE USER".
- **Status:** PROSE ONLY
- **Needs:** none proposed (a judgement step).
- **Retires:** never.

### PR-11. Each round's "found and fixed" goes to `08` and to this list, not only to the README.
- **Origin:** 2026-10-15, 06 "step 5.2 = safety gates" (step 5.1's own lessons lived only in the README).
- **Status:** PROSE ONLY
- **Needs:** a `/wrapup` check: a new revert mutant whose description cites a review finding needs a matching `08` entry or lesson.
- **Retires:** when wired.

### PR-12. One format, one reader: every checker reads an evidence file's code line through the same function.
- **Origin:** 2026-10-15, REVIEW "reads only the first 12 lines" (two step-0 files whose command is a multi-line `-c` script had a digest for one checker and none for the other).
- **Status:** GATED (build step 5.2, G6)
- **Enforced:** `gates/provenance.py::code_digest`, `gates/prune_evidence.py::digest_of`, `gates/test_safety_gates.py::EvidenceReaderTests`, `revert_safety_gates:S17`, `revert_safety_gates:S18`, `revert_safety_gates:S19`.
- **Retires:** the prose.

### PR-13. A new local in a function never reuses a name the function already gives another meaning.
- **Origin:** 2026-10-15, README "Every text then ENDED the pushing stretch" (the harness's new flag named `new`, the name its count of new tiles already had).
- **Status:** PARTIAL
- **Enforced:** `gates/test_goals.py::GraderYieldTests` (its recorder test asserts the stretch's length, which caught it).
- **Needs:** an AST gate over the AI and the gate code that flags a local rebound to a value of another kind (a count, then a flag) inside one function.
- **Retires:** when that gate is in `run_units.py`.

### PR-14. A hash a committed file records is taken over text with its line ends made "\n", never over raw bytes.
- **Origin:** 2026-10-29, 08 "RECORDED ITS INPUTS' RAW-BYTE HASHES".
- **Status:** GATED (2026-10-29)
- **Enforced:** `ai_player/gates/extract_world.py::load_json`, `ai_player/gates/rate_step5.py::file_sha256`, `ai_player/gates/test_kb2.py::OutputsTests.test_input_hashes_do_not_depend_on_line_ends`.
- **Retires:** the prose, once every hash a committed file records goes through one helper.

### PR-15. A round checks the anchors of EVERY mutant runner, not only the ones it adds to.
- **Origin:** 2026-11-09, 08 "an OLDER mutant runner's anchor matched twice".
- **Status:** GATED (2026-11-09)
- **Enforced:** `gates/check_anchors.py`, `gates/test_check_anchors.py::FaultTests`, `run_units:check_anchors`.
- **Retires:** the prose.

### PR-16. A clean merge hunk is not a clean merge: run both sides' tests on the merged tree, and re-prove a semantic fix on the exact heads that merge.
- **Origin:** 2026-11-14, 08 "Clean merge hunks hid semantic conflicts twice".
- **Status:** PROSE ONLY
- **Needs:** a merge check in the repo that runs every suite on the staged merge tree and refuses the merge commit on a red one (the chapter 6-7 merge used the lab's `merge_gates.py` and `dry_merge.py`).
- **Retires:** when that check is in the repo and fault-tested.

### PR-17. Run `run_gates.py --quick` on a branch before each of its commits, not only the round's own gates.
- **Origin:** 2026-11-14, 08 "because `run_gates.py` was never run there".
- **Status:** PROSE ONLY
- **Needs:** a commit-time check that the quick gates read PASS on the tree being committed.
- **Retires:** when that check exists.

### PR-18. Push a branch before any quick-gate run on its new head.
- **Origin:** 2026-11-14, 08 "pushed only after them, so `preflight.py` read the branch AHEAD".
- **Status:** PROSE ONLY
- **Needs:** the quick-gate launcher refuses a head the remote does not have (or pushes it first).
- **Retires:** when the launcher checks it.

### PR-19. Before a full lane, compare EVERY revert driver's cap with its newest measured full-lane time.
- **Origin:** 2026-11-14, 08 "raised timing rows only for the two NEW revert drivers"; 2026-10-31, 08 "its MEASURED time in run_regression_times.json was ten days stale".
- **Status:** PROSE ONLY
- **Needs:** a gate in git that reads every driver's last full-lane time and flags a cap below it (an open item in `03`; the lab tool `lane_times.py` does it today, kept in `_ai_lab/keep/2026-11-13-a1-sources/checkers/`, not in git).
- **Retires:** when that gate does it and is fault-tested.

### PR-20. A done-test reads STATE, never a substring of a log that also describes the work.
- **Origin:** 2026-11-14, 08 "A done-test that searched a free-text log was met by lines that only mentioned it".
- **Status:** PROSE ONLY
- **Needs:** a gate that flags a doc instruction of the form "unless <a log> has a line containing <a marker>", and a check before any folder is offered for deletion that runs `find_junctions.py` on it.
- **Retires:** when both exist and are fault-tested.

## B. Proofs: property not label, call-deleting mutants, independent reads, held-out seeds, pre-registration

### PF-1. Grade the PROPERTY, never the label the code chose for itself.
- **Origin:** 2026-10-14, 08 "A CHECK THAT GRADES A REASON'S LABEL CANNOT SEE A STALL UNDER ANOTHER LABEL".
- **Status:** GATED
- **Enforced:** `ai_player/hands/waiting.py::WaitWatch`, `gates/play_harness.py::WaitRecorder`, `rate_step5:BOUNDS.AWAIT_MAX`, `rate_step5:PLANS.STALL1`, `rate_step5:PLANS.STALL2`, `rate_step5:PLANS.STALL3`.
- **Retires:** never (a principle). Chapters 3-4's new screens each need a STALL-style arm the second path is shown to see.

### PF-2. For every new hook, the mutant DELETES ITS CALL, not just its body.
- **Origin:** 2026-10-14, 08 "A FIX ASKED ONLY UNDER ANOTHER OPTION IS DEAD CODE"; the lessons draft's missing gate #3.
- **Status:** GATED (build step 5.2, G3)
- **Enforced:** `gates/call_census.py`, `gates/census_waivers.json`, `gates/test_safety_gates.py::CallCensusTests`, `run_units:call_census`, `revert_step5:G36`, `revert_step5:G46`, `revert_safety_gates:S7`, `revert_safety_gates:S8`, `revert_safety_gates:S9`. The gates' own wiring: `gates/test_safety_gates.py::WiringTests`, `revert_safety_gates:S2`, `revert_safety_gates:S3`.
- **Retires:** the prose, once a whole step has passed the census with no MISSING site.

### PF-3. A metric is a claim only once it FAILS its control, and the control must be able to fail.
- **Origin:** 2026-10-15, 08 "THE CONTROL COULD NOT FAIL" (a control made by deleting the behaviour proves only that the deletion works). Build step 5.2 measured two more ways a control cannot fail, both in development before any graded run: the LOAF control was productive in 80 % of its frames under the first yield rule (README "with the 8 tiles alone the LOAF control"), and a control that removes only the NEW mechanism stays inside the bound when OLDER code bounds the same thing (README "5.1's navigator already ended ONE stretch by its novelty window"). Measure every control's failure in development; a control embodies the DEFECT, with every bound on it removed.
- **Status:** PARTIAL (build step 5.2: the three curiosity controls). Corrected 2026-10-23 (build step 5.3, A1-4): only LOAF's and BLOCKED's checks COUNT in the verdict. The beeline's and CH2_OFF's share controls are REPORTED (5.2 P2) and GREEDY's spacing control is DIAGNOSTIC (5.3 A1-1, no game form), so those controls fail no counted check; they were listed as Enforced, which overstated them.
- **Enforced:** `rate_step5:PLANS.LOAF`, `rate_step5:PLANS.BLOCKED`, `rate_step5:BOUNDS.LOAF_FAILS_RUNS_MIN`, `rate_step5:BOUNDS.BLOCKED_HITS_MIN`, `R5.LOAF`, `R5.BLOCKED`, `gates/rate_step5.py::step52_verdicts`.
- **Reported:** (counted by no verdict) `rate_step5:BOUNDS.FREE_CONTROL_FAILS_MIN`, `rate_step5:BOUNDS.CH2_OFF_UNDER_MIN`, `rate_step5:BOUNDS.GREEDY_FAILS_MIN`, `R5.BEELINE_FAILS_FREE`, `R5.CH2_OFF_UNDER`, `R5.GREEDY` (the GREEDY plan still plays).
- **Needs:** a meta-test: every `BOUNDS` key declares its control and separation, or is labelled FLOOR or REPORTED.
- **Retires:** when the meta-test exists.

### PF-4. A fault arm must REACH the state it tests; grade only the runs that reached it, with a reach floor.
- **Origin:** 2026-10-14, README "503 never reached a third loss".
- **Status:** PARTIAL
- **Enforced:** `rate_step5:BOUNDS.LOSE3_REACH_MIN`, `revert_step5:G106`, `revert_step5:G219`.
- **Reported:** (counted by no verdict; the 5.3 re-sourcing fix round moved BLOCKED's reach, the AI's idle reasons, to the DIAGNOSTIC check named here, and the arm's graded check reads the game's push alone) `rate_step5:BOUNDS.BLOCKED_REACH_HITS`, `rate_step5:BOUNDS.BLOCKED_REACH_MIN`, `R5.BLOCKED_REACH`.
- **Needs:** every new fault plan declares its reach predicate and floor (with PF-3's meta-test).
- **Retires:** with PF-3.

### PF-5. Derive a check's parameters from the state the run reached (the rule that judged it), never from a default.
- **Origin:** 2026-10-14, README "taken from the BASE personality".
- **Status:** GATED
- **Enforced:** `revert_step5:G105`, `revert_step5:G120`, `revert_step5:G121`.
- **Retires:** the prose (CLAUDE.md rule 4 stays the general rule).

### PF-6. Independent ground truth: read the game by code the AI does not share.
- **Origin:** 2026-10-07, 07 "AI player step 1" (the eyes missed a text-printer state, found by behaviour).
- **Status:** GATED
- **Enforced:** `gates/extract_milestones.py`, `gates/verify_knowledge.py`, `gates/play_harness.py::StoryRecorder`.
- **Retires:** never (a principle).

### PF-7. Grade on HELD-OUT seeds: never used in development, never re-graded.
- **Origin:** 2026-10-15, README "NEW held-out seeds 801-820"; the lessons draft's missing gate #2 (`--first-seed` defaulted to development seed 1).
- **Status:** GATED (build step 5.2, G2)
- **Enforced:** `gates/ledger.py`, `gates/ledger.json`, `gates/rate_step5.py::registered_numbers`, `gates/test_safety_gates.py::LedgerTests`, `run_units:ledger_check`, `revert_safety_gates:S5`, `revert_safety_gates:S6`.
- **Retires:** when every sweep driver of a family writes the ledger (rate_step5 does; its successors must).

### PF-8. Pre-register bounds before any run; never loosen a bound to pass; a number set after observation is RE-REGISTERED and re-run as a replay.
- **Origin:** 2026-10-09, 07 "AI player step 4.1" (three numbers re-registered after observation).
- **Status:** GATED (build step 5.2, G2: a graded range runs only with the numbers' sha256 it was registered with)
- **Enforced:** `gates/ledger.py`, `gates/test_safety_gates.py::LedgerTests`, `revert_safety_gates:S4`.
- **Retires:** with PF-7.

### PF-9. Identical output across runs is a DETERMINISM check, never a replication; a live arm is one trajectory.
- **Origin:** 2026-10-15, REVIEW "LIVE ARMS ARE REPLAYS".
- **Status:** PARTIAL
- **Enforced:** `gates/ledger.py` (a sweep on seeds already played runs only as a REPLAY and says so).
- **Needs:** live_step5 compares each arm's `actions.jsonl` with the same arm's newest archived run and prints `REPLAYED`.
- **Retires:** when built.

### PF-10. A premise or after-state check must be able to FAIL.
- **Origin:** 2026-10-07, 07 "AI player step 0.1" (after-state checks could pass on the untouched seed).
- **Status:** PARTIAL
- **Enforced:** `gates/live_step0.py`.
- **Needs:** each new driver's premise conjunct, with a run pointed at its own output fixture.
- **Retires:** never (each driver needs its own).

### PF-11. A predicted-REDUNDANT mutant is a claim: run it.
- **Origin:** 2026-10-15, README "G86".
- **Status:** GATED
- **Enforced:** `gates/revert_step5.py::main`.
- **Retires:** the prose.

### PF-12. A unit-tested rule is not a chapter proof.
- **Origin:** 2026-10-15, REVIEW "CHAPTERS 3-4 HAVE NEVER BEEN PLAYED".
- **Status:** PROSE ONLY
- **Needs:** chapter 4's sweep grades BADGE01_GET by the game and REPORTS the gym trainers' flags; mutant G74 must lose the claim.
- **Retires:** when the chapter-4 arm passes.

### PF-13. An instrument's false alarm is first a finding about the instrument.
- **Origin:** 2026-10-15, README "STALL3".
- **Status:** GATED
- **Enforced:** `rate_step5:PLANS.STALL3`.
- **Retires:** never (a principle).

### PF-14. Never let the agent's own target be the quantity the grader measures; grade the OUTCOME the behaviour exists to produce.
- **Origin:** 2026-10-15, 08 "THE AI AIMED AT THE GRADER'S OWN QUANTITY"; REVIEW "THE CH2 FLOOR IS PARTLY THE AI'S OWN TARGET". Build step 5.2 removed the quota (README "No quota: boredom raises the odds, the dice decide"), grades curiosity by its YIELD and SPACING, and REPORTS the shares of frames 5.1's quotas aimed at (README "Graded by YIELD and SPACING, not by a share of frames"). ⚠ Measured in the same round: when development runs fell under the old share floor, the first move was to lower a personality TASTE (`bored_frames`) toward it, the very pattern this lesson forbids; it was restored. A share floor that is still graded invites that tuning every time a run falls under it.
- **Status:** PARTIAL (build step 5.2: the quota gone, the yield graded against LOAF, the shares reported). Corrected 2026-10-23 (build step 5.3, A1-4): SPACING is DIAGNOSTIC since 5.3 A1-1 (it has no game form), so curiosity is graded by its YIELD alone. A share of frames is REPORTED by its KIND (`grader_checks.CHECKS`), so the mutants that broke the old text match, `revert_step5` G266 (`p2_reported`'s call deleted) and G267 (its HELD line), are RETIRED with `p2_reported`. The same path's deletions are now caught by `test_step53_a1.py` and `test_goals.py` (below).
- **Enforced:** `ai_player/personality.py::Errands`, `revert_step5:G154`, `revert_step5:G155`, `R5.LOAF`, `R5.NO_LOAFING`, `gates/rate_step5.py::game_yield`, `gates/rate_step5.py::P2_REPORTED`, `gates/grader_checks.py::verdict_row`, `gates/test_step53_a1.py::TypedSweepTests`, `gates/test_goals.py::SecondRoundTests.test_the_shares_of_frames_are_reported_not_graded`.
- **Reported:** (counted by no verdict) `rate_step5:BOUNDS.SPACING_ROW_MAX`, `R5.SPACED`, `R5.CH1_INTENT_MIX`, `R5.CH1_FREE`, `R5.CH2_INTENT_MIX`, `R5.CH2_FREE`, and (the 5.3 re-sourcing fix round: the two loafing checks, still Enforced above, now read the game's longest unbroken stretch of pressing that brought nothing new, not a yield) `rate_step5:BOUNDS.YIELD_RATE_MIN`, `R5.CH1_YIELD`, `R5.CH2_YIELD`.
- **Needs:** a gate that refuses a brain constant or quota computed on a graded quantity (the errand share).
- **Retires:** when that gate exists.

### PF-15. A unit test that CALLS a hook does not prove play ever reaches it: instrument the action in a run.
- **Origin:** 2026-10-15, README "the action was never instrumented" (build step 5.2: a detour's give-up at a scene lived in its CHOICE, which a unit test called directly and the navigator never calls after a scene; both such detours of the next development sweep met the scene twice). CLAUDE "INSTRUMENT THE ACTION, NOT THE INPUT TO THE ACTION".
- **Status:** PROSE ONLY
- **Needs:** a sweep report, per new hook of the step, of how many runs ACTED on it (its action record, e.g. "a scene stopped the way there" in a detour's outcome), with zero flagged before the graded run.
- **Retires:** when the census (G3) has that sweep-side counterpart.

### PF-16. A check is developed on every plan it is graded on.
- **Origin:** 2026-10-15, README "the property was developed on the plans the development sweeps ran" (build step 5.2's graded sweep FAILED its pushing property in NOHINTS alone, 20 of 20 runs, a plan none of the round's ten development sweeps had played; every other plan was under the bound).
- **Status:** PROSE ONLY
- **Needs:** `rate_step5.py` refuses a GRADED run in which a check's plans include one that no DEVELOPMENT entry of the round names (the ledger's development entries carry their plans in the note).
- **Retires:** when that refusal is built and fault-tested.

### PF-17. A rule that ENDS a run (or a goal) is a claim about every state: develop it on the game's opening, not only on the stuck state it was built for.
- **Origin:** 2026-10-15, README "three of four CHAPTER-1 runs gave up inside the moving truck" (the out-of-ideas rule as first built, step52vdev1).
- **Status:** PARTIAL. Corrected 2026-10-23 (build step 5.3, A1-4): the out-of-ideas check (`R5.OUT_OF_IDEAS`) reads only the AI's own end reason and is DIAGNOSTIC since 5.3 A1-1, so its bound is reported, not counted. A run that gives up too early is counted by the POKéDEX reach rate.
- **Enforced:** `rate_step5:BOUNDS.CH1_REACHED_MIN`, `R5.CH1_REACHED`, `revert_step5:G317`.
- **Reported:** (counted by no verdict) `rate_step5:BOUNDS.OUT_OF_IDEAS_LED_MAX`, `R5.OUT_OF_IDEAS`.
- **Needs:** a unit test that plays every END rule of the play loop over the recorded opening of a run (the truck, the first house), and fails if one fires.
- **Retires:** when that test is in `test_goals.py`.

### PF-18. A sentence about what an instrument counted is a claim: read that instrument's own per-item verdict before writing it.
- **Origin:** 2026-10-16, the verifier's second round: the README said the footprints man's chat was "counted by both paths" and cited a reported figure that held no such chat; the GAME's path, the one that grades NO LOAFING, had credited all 20 as talks (README "PlaceRecorder compares WHOLE messages"). The AI's own record was the only path that said so.
- **Status:** PARTIAL (the two verdicts are now put side by side in every sweep)
- **Enforced:** `gates/rate_step5.py::step52_verdicts` (the reported line "THE TWO PATHS ON THE TALKS"), `gates/rate_step5.py::curiosity_rows`, `gates/test_goals.py::GraderYieldTests`, `revert_step5:G345`, `revert_step5:G346`, `gates/play_harness.py::PLACES_FILE` (each run's whole second-path record kept beside its action log, for a recount).
- **Needs:** a GRADED two-path agreement bound on each run's loafing verdict, as the pushing property has (set from a development measurement, pre-registered), and `check_claims.py` (PR-3) for the README's sentences.
- **Retires:** when that bound is graded.

### PF-19. A second path is independent of the AI, not of the framework: a framework read the eyes already found wrong is wrong for the harness too.
- **Origin:** 2026-10-16, the verifier's second round: the harness's two second paths asked the framework's `is_waiting_for_input`, which README "reads a finished script's leftover pointer as a wait" (a diagnostic replay: the player walked while it said a text waited, so the game's path counted none of 50 new tiles and no free time). The eyes had refused that leftover since build step 1 (07 "AI player step 1").
- **Status:** PARTIAL (this read fixed in both recorders)
- **Enforced:** `gates/play_harness.py::text_waits`, `gates/play_harness.py::text_waits_now`, `gates/test_goals.py::GraderYieldTests`, `revert_step5:G341`, `revert_step5:G342`, `revert_step5:G343`, `revert_step5:G344`.
- **Needs:** a table of every framework read the gates' second paths make, each checked against the states the eyes' live arms measured (`gates/live_step1.py` SW and the rest), with a unit test per trap.
- **Retires:** when that table exists and each row has its test.

### PF-20. A step list is DATA for `story_step`: run the real function on every map of the road before wiring it.
- **Origin:** 2026-11-05, 08 "correct as a LIST and wrong as DATA".
- **Status:** PARTIAL
- **Enforced:** `gates/test_goals.py::Chapter67Tests`, `revert_step5:G474`.
- **Needs:** a gate that runs `story_step` on every map of each milestone's road.
- **Retires:** with that gate.

### PF-21. A live judge follows a Pokémon by its PID and ends with a self-check against the game's identity read; a failed self-check gives no verdict.
- **Origin:** 2026-11-11, 08 "instead of by identity, and counted the wrong".
- **Status:** PROSE ONLY (the judges live in the lab)
- **Needs:** a judge helper in the repo with a planted-faint test.
- **Retires:** when the judges import it.

### PF-22. Before a live A/B, show the change's decide fires on the live intent's shape; FIX equal to FAULT frame for frame means the change never fired.
- **Origin:** 2026-11-14, 08 "FIX equaled FAULT frame for frame".
- **Status:** PROSE ONLY
- **Needs:** an A/B judge that counts the change's own decide lines in every FIX arm and calls a pair with none VACUOUS.
- **Retires:** when the A/B harness does it.

### PF-23. A static walk model models every one-way tile the project has measured, and refuses a map with a movement it does not model.
- **Origin:** 2026-11-14, 08 "although the project had already measured live that it only goes down".
- **Status:** GATED (2026-11-12, P11-2)
- **Enforced:** `gates/test_ways.py::ExtractorTests.test_the_muddy_slope_only_goes_down_on_foot`, `revert_p11:slope_two_way`, `revert_p11:model_slope_floor`.
- **Retires:** the prose, for the dark-cave extractor (a new walk model needs its own test).

### PF-24. A rule about what a person sees is measured on what the screen DRAWS, never on a box around the sprite.
- **Origin:** 2026-11-14, 08 "listed people the screen did not draw".
- **Status:** GATED (2026-11-07, chapter 6 round 9)
- **Enforced:** `gates/test_eyes.py::DarkTests.test_d4_a_tiles_light_and_a_sprites_drawn_pixels`, `run_units:test_eyes`.
- **Retires:** the prose, for the eyes' person rule.

### PF-25. Test a fix from a start BEFORE the loop too: an inference about a loop's state says nothing about whether a trajectory reaches it.
- **Origin:** 2026-11-14, 08 "said nothing about whether a trajectory reaches that state".
- **Status:** PROSE ONLY
- **Needs:** a fix round's A/B template with an arm from a start before the failure, beside the arm at it.
- **Retires:** when the template carries it.

### PF-26. Every merge plays chapters 1-5 from a New Game before it lands, not only the new chapters.
- **Origin:** 2026-11-14, 08 "found a search loop whose rules `main` already had".
- **Status:** PROSE ONLY
- **Needs:** MC, the chapter 1-5 merge check in A1's runner (A1's amendment AM-05, not applied yet: its first run MUST pass, later merges SHOULD run it).
- **Retires:** when MC runs on every merge.

## C. Play: never idle, no hidden information, bounded loops, patience

### PL-1. Never idle: no `AWAIT_MAX` frames while a screen waits for a press, whatever the reason.
- **Origin:** 2026-10-14, 08 "stood 600-1200 frames in front of a screen waiting for A".
- **Status:** GATED
- **Enforced:** `rate_step5:BOUNDS.AWAIT_MAX`, `revert_step5:G54`, `revert_step5:G55`, `revert_step5:G56`, `revert_step5:G57`, `revert_step5:G86`, `revert_step5:G117`, `revert_step5:G118`, `revert_step5:G134`, `revert_step5:G135`.
- **Retires:** never.

### PL-2. Scenes come first: settle after a map change; story skills give way to a waiting screen.
- **Origin:** 2026-10-14, 08 "A CHECK THAT GRADES A REASON'S LABEL" (the lab stall).
- **Status:** GATED
- **Enforced:** `ai_player/mode.py::SETTLE_FREE`, `revert_step5:G56`, `revert_step5:G57`.
- **Retires:** the prose.

### PL-3. A failure returns at once; never retry silently.
- **Origin:** 2026-10-08, 07 "AI player step 2.1".
- **Status:** GATED
- **Enforced:** `gates/revert_step2.py`.
- **Retires:** the prose.

### PL-4. Bound every loop: each errand has a frame budget, each `while True` a budget and a no-frame-passed cap.
- **Origin:** 2026-10-14, 07 "AI player step 5" (the verifier's "every `while True` has a bound").
- **Status:** PARTIAL
- **Enforced:** `ai_player/brain/navigator.py::STILL_DECISIONS`, `ai_player/mode.py::PLAY_PASSES_MAX`.
- **Needs:** an AST rule: any `while` in the AI code names its bound constant in an allowlist; a planted unbounded loop is refused.
- **Retires:** when built.

### PL-5. Patience counts from REAL progress (a milestone, a battle won, a level by PID, a new map, a catch, an item, a capped heal).
- **Origin:** 2026-10-15, README "PATIENCE".
- **Status:** GATED
- **Enforced:** `ai_player/mode.py::STORY_PATIENCE`, `ai_player/mode.py::HEAL_RESETS_MAX`, `revert_step5:G67`, `revert_step5:G68`, `revert_step5:G119`, `rate_step5:PLANS.PATIENCE`, `rate_step5:PLANS.PATIENCE_OLD`.
- **Retires:** never. Re-measure the training stints in chapter 4 (the longest yet).

### PL-6. No goal loops forever: cool down after `FAIL_LIMIT`, forget an unusable door, cap retries in danger.
- **Origin:** 2026-10-15, README "OLDALE's centre door, seen from ROUTE 102 across its right edge".
- **Status:** GATED
- **Enforced:** `ai_player/brain/goals.py::FAIL_LIMIT`, `revert_step5:G78`, `revert_step5:G96`, `revert_step5:G97`, `revert_step5:G127`, `revert_step5:G128`, `revert_step5:G129`.
- **Retires:** never.

### PL-7. No hidden information: only what is on screen and the hints the game's dialogue gives.
- **Origin:** 2026-10-14, 07 "AI player step 5" (step 5 shopped on FLAG_ADVENTURE_STARTED, healed on FLAG_RESCUED_BIRCH); the lessons draft's missing gate #4.
- **Status:** GATED (build step 5.2, G4) for the flags and the knowledge files; the piecemeal rules stay gated by their tests.
- **Enforced:** `gates/check_fairness.py`, `gates/check_fairness.py::FLAG_DOORS`, `gates/check_fairness.py::KNOWLEDGE_FIELDS`, `gates/test_safety_gates.py::FairnessTests`, `run_units:check_fairness`, `revert_safety_gates:S10`, `revert_safety_gates:S11`, `revert_safety_gates:S12`, `revert_safety_gates:S13`, `gates/test_battle.py::HiddenInfoTests`, `gates/warp_reads.py`.
- **Retires:** never as a principle.

### PL-8. Play like a person, never a speedrun (RULING 32).
- **Origin:** 2026-10-03, 07 "USER RULING 32".
- **Status:** PARTIAL. Corrected 2026-10-23 (build step 5.3, A1-4): the share floors (the curiosity the story did not need, the intent mix) are REPORTED since 5.2 P2, so "never a speedrun" is counted only by the time against the beeline; it was listed as Enforced by the floors, which overstated them. (Corrected again 2026-10-25, the 5.3 re-sourcing build: the battle-free time check is re-sourced to the game and still counts; the raw time check is REPORTED, because no control separates it on the development sweep.)
- **Enforced:** `R5.NO_SPEEDRUN_DICE` (since the 5.3 re-sourcing build, 2026-10-25: by the GAME's frames to the POKéDEX less its battle frames, paired with the beeline).
- **Reported:** (counted by no verdict) `rate_step5:BOUNDS.FREE_RUN_MIN`, `rate_step5:BOUNDS.MIX_MIN`, `R5.CH1_FREE`, `R5.CH1_INTENT_MIX`, and since the 5.3 re-sourcing build (the A2 decision addendum's row 25: CH1 slower in only 7 of 12 seeds, the battles' dice swing it) `R5.NO_SPEEDRUN`, `rate_step5:BOUNDS.SLOWER_THAN_BEELINE_MIN`.
- **Needs:** PF-14: the floor is partly the AI's own aim, so the separation from a control that CAN fail carries the claim.
- **Retires:** never.

### PL-9. Count outcomes where they happen: the report, the told count and the game agree.
- **Origin:** 2026-10-14, 08 "battles lost 0".
- **Status:** GATED
- **Enforced:** `revert_step5:G46`.
- **Retires:** the prose.

### PL-10. Identity, never a count or a slot (CLAUDE.md rule 3).
- **Origin:** 2026-10-15, README "the party's SUM".
- **Status:** GATED
- **Enforced:** `revert_step5:G119`, `gates/live_step4.py`.
- **Retires:** never.

### PL-11. Every printed reason must be TRUE ("looked at" a tile it never reached is false).
- **Origin:** 2026-10-15, REVIEW "detours are cosmetic".
- **Status:** PARTIAL (build step 5.2: a detour says "reached" or "not reached", checked against the game's position)
- **Enforced:** `revert_step5:G79`, `revert_step5:G80`, `revert_step5:G130`, `revert_step5:G177`, `revert_step5:G178`, `revert_step5:G215`, `revert_step5:G252`, `rate_step5:BOUNDS.ARRIVE_MIN`, `gates/rate_step5.py::curiosity_rows`.
- **Needs:** a log-consistency pass in the sweep grader ("WANTS" needs balls, "done" needs its proofs, a detour says "reached" or "not reached").
- **Retires:** when built.

### PL-12. Pressing that moves nothing is idling too: no long free stretch of presses with no new tile.
- **Origin:** 2026-10-15, REVIEW "the stall check cannot see pushing against a blocker". Build step 5.2's property found a real bug at once (README "114,121 frames of pressing with nothing new": scene walls of one milestone carried into the next).
- **Status:** GATED (build step 5.2)
- **Enforced:** `ai_player/hands/waiting.py::PushWatch`, `gates/play_harness.py::PlaceRecorder`, `rate_step5:BOUNDS.PUSH_MAX`, `rate_step5:PLANS.BLOCKED`, `revert_step5:G200`, `revert_step5:G204`, `revert_step5:G218`, `revert_step5:G220`, `revert_step5:G229`, `revert_step5:G258`, `revert_step5:G268`, `revert_step5:G272`, `revert_step5:G275`. (The AI's own record first MISSED its control's pushing: a run cut off by its frame budget never ended its last stretch, README "the AI's own record said 0-1,758"; the two paths' agreement check is what showed it, PF-13.)
- **Retires:** the prose, once a chapter-3 sweep has run under it.

### PL-13. A curiosity goal counts for what it YIELDS (tiles, an item, a catch, words never read, a talk only when it TOLD something new), not for its time or its label.
- **Origin:** 2026-10-15, REVIEW "it loafs, and every metric pays for it". The verifier's round: a talk was still credited by its label, README "60 NURSE RE-HEALS" (127 chats in all that heard nothing new, productive by both paths). The verifier's SECOND round (2026-10-16): the game's path compared WHOLE messages, README "PlaceRecorder compares WHOLE messages" (OLDALE's footprints man's talk, the last two pages of his own scene, was "new" 20 times by the game and never by the AI). Compare at the unit a person reads, the PAGE, never at a container of it.
- **Status:** GATED (build step 5.2; the talk since its verifier's round, by PAGE since its second round)
- **Enforced:** `ai_player/brain/goals.py::goal_yield`, `ai_player/hands/waiting.py::BattleClock`, `gates/rate_step5.py::game_yield`, `gates/play_harness.py::shown_pages`, `gates/play_harness.py::split_pages`, `gates/play_harness.py::PlaceRecorder`, `gates/test_goals.py::GraderYieldTests`, `rate_step5:BOUNDS.LOAF_FRAMES_MAX`, `rate_step5:PLANS.LOAF`, `revert_step5:G140`, `revert_step5:G143`, `revert_step5:G236`, `revert_step5:G238`, `revert_step5:G243`, `revert_step5:G250`, `revert_step5:G295`, `revert_step5:G309`, `revert_step5:G310`, `revert_step5:G311`, `revert_step5:G313`, `revert_step5:G325`, `revert_step5:G326` (a look round, a walk to SEE, is over once it has seen nothing new for `CURIOUS_NOVELTY` frames, battles or not: README "each battle's experience reset its novelty window"), `revert_step5:G333` (whole messages again), `revert_step5:G334`, `revert_step5:G335` (the page read's CALL deleted), `revert_step5:G336`, `revert_step5:G337` (the run's opening window credited to its first goal), `revert_step5:G338`, `revert_step5:G339`, `revert_step5:G340`.
- **Reported:** (counted by no verdict since the 5.3 re-sourcing: the yield rate's two checks are REPORTED, and its LOAF control's check reads the game's push, not a yield) `rate_step5:BOUNDS.YIELD_RATE_MIN`, `R5.CH1_YIELD`, `R5.CH2_YIELD`.
- **Retires:** the prose, once chapter 3's curiosity is graded the same way.

### PL-14. Someone who has just spoken to it in its own service talk or chat is never chatted with (the nurse who just healed it, the clerk); a scene's speaker may be, once.
- **Origin:** 2026-10-15, README "LOAFING CREDITED AS A TALK" (the verifier's round: the chat chooser left out only the story step's own person). Development: README "A SCENE's speaker is not remembered" (remembering every speaker had halved the chats with new words).
- **Status:** GATED (build step 5.2, the verifier's round)
- **Enforced:** `ai_player/brain/goals.py::SPOKE_REACH`, `ai_player/brain/goals.py::HEARD_KINDS`, `ai_player/brain/goals.py::GoalManager.notice`, `ai_player/brain/goals.py::GoalManager._chat_person`, `ai_player/world/memory.py::WorldMemory.to_dict`, `revert_step5:G292`, `revert_step5:G293`, `revert_step5:G294`, `revert_step5:G296`, `revert_step5:G297`, `revert_step5:G298`, `revert_step5:G299`, `revert_step5:G302`, `revert_step5:G320`, `revert_step5:G321`, `gates/test_goals.py::VerifierRound52Tests`.
- **Retires:** the prose, once chapter 3's chats are graded by the same yield.

### PL-15. A loop rule that holds for ONE intent must hold across goals: what ended an intent is remembered past it until something new is seen.
- **Origin:** 2026-10-15, README "The ping-pong rule ends one goal; nothing stops the next goal from looping through the same door." (98 goals in a row in NOHINTS seed 901).
- **Status:** GATED (build step 5.2, the verifier's round)
- **Enforced:** `ai_player/brain/navigator.py::Navigator._remember_pingpong`, `ai_player/brain/navigator.py::Navigator.ponged_now`, `ai_player/world/memory.py::WorldMemory.stamp`, `revert_step5:G277`, `revert_step5:G282`, `revert_step5:G283`, `revert_step5:G289`, `revert_step5:G308`, `revert_step5:G318`, `revert_step5:G319`, `revert_step5:G327`, `revert_step5:G328`, `revert_step5:G329`, `revert_step5:G330`, `revert_step5:G331`, `revert_step5:G332`, `ai_player/brain/goals.py::_scene_corners`, `rate_step5:BOUNDS.PUSH_MAX`. (Development found the same shape for a scene: one that turned a curiosity walk back once is blocked for curiosity past that walk, README "the look round some more after it walked OLDALE for 2,003 frames".)
- **Retires:** the prose, once every loop rule of the navigator (the novelty window, the scene count) is held past its intent too, or shown not to need it.

### PL-16. "Left to see" is only what it could get to: what its reach shows no way to, and a frontier stood on whose unseen side stays unseen, are out of a map's promise until the map or the story moves.
- **Origin:** 2026-10-15, README "OLDALE_TOWN_HOUSE1's two tiles behind its back wall" (the town's door to it kept "2 things left to see" for ever). Development: README "CH1 seed 1201 gave up in the rival's bedroom" (a mark from the milestone before).
- **Status:** GATED (build step 5.2, the verifier's round)
- **Enforced:** `ai_player/brain/navigator.py::Navigator.cut_off`, `ai_player/brain/navigator.py::Navigator._seen_out`, `ai_player/brain/navigator.py::Navigator.story_moved`, `ai_player/world/memory.py::WorldMemory.mark_cut_off`, `ai_player/world/memory.py::WorldMemory.forget_marks`, `revert_step5:G278`, `revert_step5:G279`, `revert_step5:G280`, `revert_step5:G281`, `revert_step5:G305`, `revert_step5:G306`, `revert_step5:G312`, `revert_step5:G314`, `revert_step5:G315`, `revert_step5:G316`, `revert_step5:G322`, `revert_step5:G323`, `revert_step5:G324`, `ai_player/world/memory.py::WorldMemory.mark_spent`.
- **Retires:** the prose, once a mark is tied to what made it (a scene, a person) instead of to the map's tile count.

### PL-17. With no lead, it heads for what is left anywhere it knows, and with nothing left anywhere it gives the run up; it never walks the same streets for the patience.
- **Origin:** 2026-10-15, README "THE NOHINTS PUSHING" (20 of 20 graded runs, 31,676-62,012 frames of pressing with nothing new by the AI's record).
- **Status:** GATED (build step 5.2, the verifier's round)
- **Enforced:** `ai_player/brain/goals.py::lost_intent`, `ai_player/brain/goals.py::lost_way`, `ai_player/brain/goals.py::worth_going`, `ai_player/brain/goals.py::shut_in`, `revert_step5:G284`, `revert_step5:G285`, `revert_step5:G286`, `revert_step5:G287`, `revert_step5:G288`, `revert_step5:G290`, `revert_step5:G291`, `revert_step5:G300`, `revert_step5:G301`, `revert_step5:G307`, `revert_step5:G317`, `rate_step5:BOUNDS.PUSH_MAX`, `R5.PUSHING`.
- **Reported:** (counted by no verdict since build step 5.3 A1-1, corrected 2026-10-23 in A1-4: the AI's own end reason is DIAGNOSTIC) `rate_step5:BOUNDS.OUT_OF_IDEAS_LED_MAX`, `R5.OUT_OF_IDEAS`.
- **Retires:** the prose, once chapters 3-4 are graded under it.

### PL-18. One free look is not a free screen: a run ends "done" only after what is on screen is played out and a pause finds it still free.
- **Origin:** 2026-10-29, 08 "ONE FREE LOOK IS NOT A FREE SCREEN".
- **Status:** GATED (backlog R5)
- **Enforced:** `ai_player/mode.py::DONE_SETTLE_ROUNDS`, `ai_player/mode.py::HandsBrain._settle_before_done`, `revert_step5:G347`, `revert_step5:G349`, `revert_step5:G352`, `revert_step5:G354`, `revert_step5:G355`.
- **Retires:** the prose.

### PL-19. Frames spent after the decision to end are budget-aware: the run's frame budget never turns a reached target into "stopped".
- **Origin:** 2026-10-29, 08 "turns a reached target into an unrecorded stop".
- **Status:** GATED (backlog R5's fix round)
- **Enforced:** `ai_player/mode.py::DONE_BUDGET_MARGIN`, `ai_player/mode.py::HandsBrain._settle_frames`, `revert_step5:G356`, `revert_step5:G357`, `revert_step5:G371`.
- **Retires:** the prose.

### PL-20. Read who is on the field at the battle's first ACTION MENU: the looks before it may still show the last battle's battler.
- **Origin:** 2026-11-14, 08 "where the game still shows the LAST battle's battler".
- **Status:** GATED (2026-11-09, BP-1)
- **Enforced:** `gates/test_bossprep.py::TraineeRuleTests.test_the_raise_watch`, `revert_bossprep:stale_lead`.
- **Retires:** the prose, for the raise watch.

### PL-21. A battle question's subject is read from the page that names it, kept apart, never from a window of recent pages.
- **Origin:** 2026-11-14, 08 "named a move's learner from a 40-page window".
- **Status:** GATED (2026-11-11, BP-1 round 2)
- **Enforced:** `gates/test_bossprep.py::LearnerTests.test_the_learner_named_by_its_page`, `gates/test_bossprep.py::LearnerKeptPageTests`, `revert_bossprep:no_learning_kept`, `revert_bossprep:learner_page_off`, `revert_bossprep:learning_any_move`.
- **Retires:** the prose, for the learner question.

### PL-22. A standing thing the AI saw stays a wall in its memory for the session, until it sees it gone.
- **Origin:** 2026-11-14, 08 "was a wall only while it was on screen".
- **Status:** GATED (2026-11-13, the chapter 5 search fix)
- **Enforced:** `gates/test_goals.py::StandingThingsTests`, `revert_step5:G691`, `revert_step5:G692`, `revert_step5:G697`.
- **Retires:** the prose.

## D. Environment: host clock, disk, deployment clone

### EN-1. A launcher run's cartridge clock is the HOST's: live arms differ by time of day and cannot be replayed.
- **Origin:** 2026-10-08, 07 "AI player step 3.1".
- **Status:** PARTIAL
- **Enforced:** `ai_player/gates/rate_step5.py::GAME_CLOCK` (sweeps pin it).
- **Needs:** the live evidence header records the host time at launch and the RTC the eyes read first.
- **Retires:** when built.

### EN-2. Sweeps fill %TEMP% and the disk.
- **Origin:** 2026-10-15, 06 "a disk budget with harness cleanup" (the lessons draft measured 24,355 `ai_*` folders in %TEMP%, about 18 GB, the disk 96 % full).
- **Status:** GATED (build step 5.2, G5)
- **Enforced:** `gates/disk_budget.py::preflight`, `gates/disk_budget.py::SweepFolders`, `gates/disk_budget.py::prune_runs`, `gates/test_safety_gates.py::DiskBudgetTests`, `run_units:disk_budget`, `revert_safety_gates:S14`, `revert_safety_gates:S15`, `revert_safety_gates:S16`.
- **Retires:** the prose; the leaked folders are deleted only on the user's or the coordinator's word (`disk_budget.py --temp --apply`).

### EN-3. A long-lived process never runs from the development checkout.
- **Origin:** 2026-10-03, 08 "THE 24/7 PROCESS RAN FROM THE DEVELOPMENT CHECKOUT".
- **Status:** GATED (structural: the learner's own clone)
- **Enforced:** `ai-agent/learner.py`.
- **Retires:** the learner half now; the same shape inside this checkout is PR-5.

### EN-4. The framework's dependencies live in the USER site-packages: never `python -s`.
- **Origin:** 2026-10-07, 08 "THE FRAMEWORK'S DEPENDENCIES LIVE IN THE USER".
- **Status:** GATED
- **Enforced:** `ai_player/host/launcher.py::check_package_resolution`, `gates/live_step0.py`.
- **Retires:** the prose.

### EN-5. The learner runs 8 lanes; back to 16 only when the AI player hands it something NEW to test (RULING 38).
- **Origin:** 2026-10-15, 06 "USER RULING 38".
- **Status:** GATED (config)
- **Enforced:** `ai-agent/config.json`.
- **Retires:** when the user rules again.

## Retired

None yet. A lesson moves here with the date, the gate that made the mistake impossible, and its `08` entry.
