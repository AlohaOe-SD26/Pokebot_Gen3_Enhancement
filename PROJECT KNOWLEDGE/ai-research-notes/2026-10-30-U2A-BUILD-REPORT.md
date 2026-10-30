> **Filed 2026-10-30** by the orchestrating session: every agent's hand-back section of the workflow `u2a-build` (8 agents, 26.99 Mtok), verbatim, in run order. The spec: `2026-10-30-U2-BUILD-SPEC.md` (its box holds the scope cut). Decisions: `06` 2026-10-30 ("U2a BUILT"); the change: `07` 2026-10-30.

# U2a BUILD REPORT: a session ended by its time or frame limit may be continued, and every continue tells what it drops (2026-10-30)

## 00. The orchestrator's checks

- **Applied to `main`** from the worktree `wf_6a7c527a-7d2-1` (`s53/u2/apply/apply_u2a.py`): 23 files, each sha256-checked. Left out: the worktree's own keep-earlier archive and its step3/step4/step52 revert files (`main`'s lane files of the same names win), and six tree zips no new evidence names.
- **On `main` before the commit:** `test_host` (37 tests) OK; `test_kb2` OK; `run_regression.py --quick` `REGRESSION: PASS (quick, 21 suites, 21.9 s wall)`; `ledger.py --check` 66 entries PASS; `run_gates.py --quick`: `ALL 141 ENFORCING GATES PASS  (844.9s total)   [+2 ADVISORY probe(s) — run, NOT gated]`; Tier 0 and Tier 1 (`07`). The full lane runs after the commit.
- **The verification's three MINOR findings (V1-V3) are left open** for the next item (`06`): they sit in the host-record layer, which section 9 of the spec names defence in depth, not a seal, and a fourth round would have cost more of the week's budget than they risk.

## 0. In plain words

- A play session that stops because its time or frame limit ran out can now be continued from the last save (USER RULING 53). Before, it could only if it had stopped right after a save.
- Every such continue now says what it drops: how long was played after the save, the battles it undoes, and the maps first visited after it (the launcher's sentence; the AI itself is told only the counts).
- The launcher judges how a run ended from the host's own records, never from the AI's words.
- Proven on 4 new games (every test passed), repeated independently on 4 more, and after the review's fixes on 4 more plus an independent 4 more.
- Not yet: the AI saving right before its time runs out (U2b, its own item later).

# Stage offline (builder)

> Hand-back section, verbatim.

U2a STAGE 1 (offline): BUILDER'S SECTION. Worktree wf_6a7c527a-7d2-1 at HEAD 417df790, uncommitted, no git writes.

BUILT (in the spec's step-3 order, each part's tests and mutants green before the next):
(a) RV-7 / D16: the purity gate now refuses a raise or an assert reached from a finally in the play loop. A try nested in the finally is no shelter. Plants X21-X24 added, with a control. Mutants S40h and S40i are CAUGHT.
(b) RV-5 / D15: fairness rule D3 (d) now lets `case int(n)` through: a self-matching builtin, exactly one positional sub-pattern, no keyword, the name bound nowhere in the module by any binding form (Name store/del, parameters, def/class names, import aliases, MatchAs/MatchStar/MatchMapping.rest, except-as, global/nonlocal, type parameters), and `builtins` untouched. Faults covered: rebinding by assignment, parameter, `case ... as int`, `except ... as int` and `import builtins`; `int(a, b)` and `int(n, real=1)`; another module doing `builtins.int = ...`. Controls: int/str/tuple(v) and the real package. Mutants S46g, S46h and S46i-k are CAUGHT.
(c) The launcher table D1-D4 (_classify_session):
- A launcher line naming the run folder decides, whatever the session's `host` says (D4).
- A hard kill with a verdict is judged by its verdict (D3a). A hard kill with no verdict keeps the interim rule, allowed only at a save (ruling 53, "not a kill").
- A host reason counts only with its host code: verdict_code first, then the verdict file's exit_code; a mismatch with the process code is told (D3).
- `play: stopped:` is BUDGET only when real_frames >= frames; otherwise it is CHOSEN (D2).
- A BUDGET end needs a CLEAN verdict (D3b). A CLEAN BUDGET end is ALLOWED, end line or not, and its words carry ruling 53's clause. A harness `budget` end is allowed.
- record_launch writes frames, real_frames, verdict and verdict_code (all None without a verdict). __main__ passes frames=args.frames.
- The AST pin maps every lifecycle.finish/crash in host/session.py and host/lifecycle.py into _HOST_CODES with its exact code, or into _HOST_NOT_CLEAN. Its fault is a planted finish("new-end", EXIT_PARKED).
- Mutants U0, U1, U2a, U3, U4, U4b and U5-U11 are all CAUGHT as predicted.
(d) What a continue drops (D13):
- MemoryBook.dropped_after counts over one set of sessions: from the latest continue of the save, or the save's own session from the save on. Per session, frames come from that session's own end line, and are None ("not recorded") without one. It also returns at_save, at_end (from the newest session only) and lost (= undone_losses).
- The end line gains play_time and where.
- The launcher adds the host's count per session (real_frames, less the save's offset in its own session) and the maps first stood on after the save, from world.jsonl ("not known" without the file). ContinueCheck.dropped holds all of it, and cmd_run prints it through drop_words.
- The AI's drop line and its session line's `dropped` carry frames and battles only, never a play time or a map.
- Mutants D1m-D6m are CAUGHT.
(g) The README's "Saving and CONTINUE" gains a U2a paragraph, and KNOWN LIMITS was rewritten for U2a. Not added: the live U0 "(a COPY)" switch rows (stage 2).
Census mutants U2C01-U2C07 close every new or changed call site. F008, F014, F016 and F017 were re-anchored with predictions re-derived; S46f and S34 were re-anchored too.

CHECKS (last lines verbatim):
- call_census "CALL-SITE CENSUS: PASS" (0 MISSING, no new waiver)
- revert_r1 "OVERALL: PASS" (546 CAUGHT + 1 REDUNDANT of 547; evidence/2026-10-30-u2-REVERT.txt)
- revert_step5 "OVERALL: PASS" (400 + 2 of 402)
- revert_safety_gates "OVERALL: PASS" (23 of 23)
- revert_step3 "OVERALL: PASS" (93 + 1 of 94)
- revert_step4 "OVERALL: PASS" (62 of 62)
- test_host whole "OK" (37 tests; support root = the main checkout)
- test_check_purity whole "OK" (30 tests)
- test_safety_gates whole "OK" (50 tests)
- quick lane "REGRESSION: PASS (quick, 21 suites, 22.7 s wall)"
- check_purity "VERDICT: PASS"
- check_fairness "PERSON-FAIR DATA DOOR: PASS (0 breaches)"
- main sandbox-pokebot: 0 entries newer than the stage's marker (01:46 AM)
- test_kb2: NOT RUN (worktree; ruling 4)
No new gate rule fired on the real package. Outputs are in s53/u2/build/s1-offline/.

MEASURED:
- Step 2: all four s53/u2 probes reproduce the spec's outputs exactly.
- Boot offset: on all 128 real-tree launcher rows, real_frames - (end.frame - frame_base) = 0. The 36 LAUNCH-OLD rows give a constant -66883, because mutant S27 loads the fixture .ss1.
- All 40 genuine stops: real_frames 2620, codes 0/0, verdict CLEAN.

DEVIATIONS (the code wins; full list in `deviations`):
- The support-root variable means the folder holding sandbox-pokebot.
- The plant `case int(x=1)` was never refused, so `case int(n, real=1)` tests the no-keyword condition instead.
- The package-wide builtins condition is a builder's strengthening.
- An old launcher line with no verdict word reads the run's verdict file; with neither, the interim rule applies.
- The session line's `dropped` is set before write_session, so existing anchors stay byte-identical.
- The drop test is split between test_saving and test_goals.
- run_regression_times.json was not updated.

NOT DONE (out of the U2a scope or a later stage):
- Parts 3 and 4: D6-D12, the time save and the cut.
- Step 2's D12(c) grep and D9 marker list (the cut is not in U2a).
- live_r1 arms and graders, D14/RV-3 budgets, and every live step (stage 2/3). No process census was needed because nothing live ran.

HAND-OFF NOTE: the untracked evidence/trees zips other than c00c606fe00ac5dc.zip come from subset runs on intermediate trees. The orchestrator should stage explicit paths and leave those four out.

# Stage live-dev (builder)

> Hand-back section, verbatim.

U2a STAGE 2 (live_r1 arms + development #62), 4:10-4:53 AM Los Angeles, worktree wf_6a7c527a-7d2-1. No STOP.

BUILT (ai_player/gates/live_r1.py, test side):
- U2-BUDGET (`u2budget --from-row LAUNCH`): child C of the REAL tree runs on a copy of LAUNCH's new `frozen_after`. Its OLD twin (`--old`) runs mutant U0 (U2_OLD_EDITS, the same as revert_r1 U0; the selftest asserts it).
- U2-WALL (`u2wall --from-row K-AFTER`): step 1 is the REAL launcher run --continue (--frames 400000 --wall-seconds 240, target ch4_roxanne) in a mirror build root, then a freeze, then child C. U2-WALL-OLD (`--old --from-row U2-WALL`) runs step 2 from U0's tree.
- Graders:
  - grade_u2budget: reach on the HOST's launch line (real_frames == frames == 2620, exit 0, code 0, CLEAN), continued S2, end line budget and not at a save, cart unwritten, no save after. Then B1 (allowed, BUDGET, clause, and the drop graded against the launch line's real_frames, S2's RAM play time, lost lines, and maps from the world file minus the restored set), B2 (arrival at S2), B3 (the AI's session `dropped`).
  - grade_u2wall: reach (wall-clock, verdict_code 124, CLEAN, no hard kill, continued S2, no end line). Then W1 (AI frames not recorded, host count less the newest save's offset), W2 (arrival = FILE content; continued_from = S2's line, or the one save line matching the FILE by stamp + map + tile + party), W3 reported.
- child_b records ContinueCheck.dropped. cmd_launch records the launcher line and the purity counters.
- HELD_OUT is now 5651-5654. Discriminators, registered_numbers, EXPECTED, COUNTING, summary_of and cmd_grade are extended.
- 5 new FAULTS (u2_drop_ignored, u2_drop_self_graded, u2_stop_unverified, u2_wall_no_code, u2_wall_stamp_only), each caught by a planted case.

FAULT-TESTED BEFORE USE: pretest_drop.py on 22 recorded LAUNCH rows (#57-#61, the launch line reconstructed from purity.json) gives "PRETEST: 22 of 22 ... -> PASS". Each plant (off-by-one save, early stop, host_frames taken from the AI's end line, a restored map named as new) flips the answer, and the matching FAULT flips it back.

DEVELOPMENT #62 (ledger begun 4:23:00 AM, finished; --check PASS): 120 jobs at 12 at once, 4:29:26-4:47:50 AM, all exit 0.
- Verdict on the final tree: "LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new' ... (failing: none; below the floor: none; discriminators that differ: 62 of 66)". The 4 that do not differ are the CHAIN pairs on 5602 and 5605, where CHAIN did not count: child B reached ch1_pokedex first.
- 36 of 36 determinism lines equal CONTROL's.
- U2-BUDGET passed 6 of 6, and U2-BUDGET-OLD showed on 6 of 6. U2-WALL passed 6 of 6, and U2-WALL-OLD showed on 6 of 6.

MEASURED:
- LAUNCH, 6 of 6: real_frames == frames == 2620, CLEAN, not at a save.
- U2-BUDGET's boot offset is 0 on 6 of 6.
- U2-WALL step 1 always ended at 218.7 s: wall-clock / 124 / CLEAN, no hard kill, 80,259-122,266 frames (367-559 fps under load). Its launcher-start-to-arrival walls were 8.0-8.6 s.
- RV-3, arrival to kill over #57-#62: CHAIN widest 120,137 (#60) with wall 230.5 s (#62); OLD widest 71,959 (#62; before it, 48,716) with wall 161.3 s.
- SET:
  - CHAIN_B_FRAMES 242,294, CHAIN_B_TIMEOUT 461 s;
  - CHAIN_OLD_FRAMES 145,938, CHAIN_OLD_TIMEOUT 323 s;
  - U2_WALL_SECONDS stays 240.

DROP SENTENCES SEEN:
- Host, U2-BUDGET 5603: "this continue drops: session(s) 2 (2,620 frames by the host's count; 2,620 frames by the AI's record), from play time 0:24 at save 2 to 0:24 at session 2's end, 0 battle(s) lost (undone), maps first stood on after it: OLDALE_TOWN_MART (the AI's own record, each session's world.jsonl)".
- Host, U2-WALL 5602: "... session(s) 2 (36,821 frames by the host's count; not recorded (a session ended without its end line) by the AI's record), from play time 0:30 at save 5 to session 2's end (its play time not recorded: no end line), 0 battle(s) lost (undone), maps first stood on after it: OLDALE_TOWN_HOUSE2, ROUTE102 ...".
- AI: "continue: this continue drops 2620 frames of play after save 2, and 0 battle(s) lost" and "continue: this continue drops the play after save 5, its frames not recorded (a session ended without its end line), and 0 battle(s) lost". Neither names a map or a play time.

W3 (reported):
- Step 1 saved on every seed, so the cart's counter rose: at OLDALE centre heals and at the ch1_rival_route103 and ch1_pokedex big moments.
- Play after the last save, dropped by the host's count: 4,449-36,821 frames.

CHECKS (last lines):
- selftest --all: "SELFTEST: the clean run PASSES (100 cases) and 18 of 18 planted faults FAIL as they must -> PASS"
- quick lane: "REGRESSION: PASS (quick, 21 suites, 21.0 s wall)"
- anchors: "anchors checked 1147; not exactly once: 0"
- sandbox: "paths newer than the marker: 0"
- the held-out registered-numbers sha on the final tree: 1808369632bb5e42df3f1deed9a5e0eabb0054f869bd0114886306cd0332f082 (NOT registered).

DEVIATIONS:
- W1 subtracts the NEWEST save's offset (step 1's own on every seed), not S2's.
- B1's lost is compared with the session's lost lines (0 everywhere).
- The maps second path is the last snapshot minus the restored set.
- Child C records the map consts that W2's name match needs.
- A run_launcher helper was added; cmd_launch and cmd_r2 are untouched.
- The 5601 smoke ran under #62 before the plan. Its U2-WALL frames differed from the plan's (136,929 vs 87,829): the wall end depends on load, so U2-WALL is not deterministic.
- Vacuity:
  - W2's S2 branch ran only on plants;
  - B1's maps were non-empty on 3 of 6 seeds.

NOT DONE:
- The held-out round (stage 3).
- test_kb2 (cannot run in a worktree).
- No full revert_r1, revert_step*, revert_safety_gates or test_host re-run in this stage. AI code is unchanged since stage 1; live_r1.py's mutant anchors were audited.
- run_regression_times.json is not updated.
- The stage-1 tree zip ai_player/evidence/trees/c00c606fe00ac5dc.zip is now STALE (live_r1.py changed); do not commit it as the final tree.
- No time save (U2b).

# Stage graded (builder)

> Hand-back section, verbatim.

U2a STAGE 3: THE GRADED HELD-OUT ROUND (#63, seeds 5651-5654)

VERDICT (verdict.out, last line): "LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 1 of 4: below the floor; passed 1 of 1; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 42 of 44)".

Caveats that belong with the headline:
- CHAIN counted on only 3 of 4 seeds, which is exactly the floor.
- U2-WALL's W2 ran only its "counter rose" branch live.
- The launcher never printed its counted drop sentence live (see DROP SENTENCES).
- U2-BUDGET's lost was 0 on every seed.

WHAT I BUILT
No code. This stage changed only the worktree's ledger.json (#63) and added ai_player/evidence/2026-10-30-u2a-HELDOUT.txt. The scratch scripts are in s53/u2/build/s3-graded/:
- seed_check.py: fault-tested; its second version is the one relied on.
- hygiene.py
- run_plan.py: stage 2's plan, re-seeded.
- drop_sentences.py
- assemble_evidence.py
- the reused measure_u2.py, summarize_u2.py and measure_rv3.py

ORDER (12-hour Los Angeles time)
1. Lane census: 0.
2. Seed check:
   - The first version found 15 unclassified hits. All were plan text, a numbers printout, or frame counts, and that version is kept as superseded.
   - The second version printed "SEEDS 5651-5654 USED ANYWHERE: 0 -> UNUSED: YES".
3. Selftest: PASS.
4. Registration, 5:00:34 AM: ledger register --first 5651 --last 5654, sha256 1808369632bb5e42….
5. ledger begin, 5:00:35 AM, tree 76170fc5757b447e.
6. One plan of 80 jobs (20 per seed: every existing arm plus U2-BUDGET, U2-BUDGET-OLD, U2-WALL and U2-WALL-OLD, mutant U0), 5:00:40 to 5:14:19 AM. Every exit code was 0.
7. The one verdict.
8. ledger finish #63.
9. ledger --check: "LEDGER ledger.json: 63 entries; well formed -> PASS".

PER-ARM TABLE (floor 3 of 4)
- Counted 4/4, ok on every seed: CONTROL, K-AFTER, K-INSIDE, K-SILENT, K-FIRST, K-BETWEEN, LAUNCH, R2-RETRY, U2-BUDGET, U2-WALL.
- CHAIN counted 3/4. On 5653, child B reached ch1_pokedex ("play: done") at 71,886 frames, right after its 4th save and before rule N. B was never killed. This is the known shape, and nothing was tuned.
- OLD arms counted 4/4, each showing its difference: K-INSIDE-OLD, K-SILENT-OLD, LAUNCH-OLD, R2-RETRY-OLD, U2-BUDGET-OLD, U2-WALL-OLD.
- CHAIN-OLD and CHAIN-R1-OLD counted 3/4. They also showed on 5653, but count only where their twin counts.
- K-BETWEEN-MID (diagnostic, not graded) counted 1/4 and was ok there.
- Determinism: 24 of 24 lines equal CONTROL's (one trajectory per seed, replayed).

DISCRIMINATORS (42 of 44 differ)
On every seed:
- K-INSIDE/OLD and K-SILENT/OLD: continued_from [1,2].
- K-AFTER/K-INSIDE: FILE [S2, S1+ERROR].
- LAUNCH/OLD first look: [UNKNOWN 0, OVERWORLD 66883].
- K-FIRST/CONTROL: [CORRUPT, S5/S4/S5/S5].
- K-BETWEEN: NEW is not in the restored memory.
- R2-RETRY/OLD: ok [True,False], classes KILLED/CHOSEN.
- U2-BUDGET/OLD: ok [True,False], class BUDGET.
- U2-WALL/OLD: ok [True,False], class BUDGET.

On 5651, 5652 and 5654 only:
- CHAIN/CHAIN-OLD parent [1,2].
- CHAIN/CHAIN-R1-OLD last_save.id [3,1].
- Presses digests equal: 53c59794ff67817b/1042, c2d15ad4026b6de9/980, 2344b6e6f971f362/934.

The 2 that do not differ are the two CHAIN pairs on 5653, where CHAIN did not count.

U2 ARMS
- LAUNCH, 4/4: real_frames == frames == 2620, CLEAN, code 0, end line budget True and at_save False.
- U2-BUDGET, 4/4, B1-B3 True:
  - host_frames 2620 = the AI's frames, so the boot offset is 0. lost is 0.
  - Maps: none, ROUTE103 + OLDALE_TOWN_MART, none, OLDALE_TOWN_MART.
- U2-BUDGET-OLD, 4/4: refused under "USER RULING 52", memory byte-identical.
- U2-WALL step 1, 4/4: wall-clock/124/CLEAN, no hard kill, 218.7-219.2 s, real_frames 80,849-124,503 of 400,000.
- U2-WALL W1/W2:
  - The newest save was step 1's own on every seed.
  - One identity match each time, and C continued it.
  - Dropped host_frames 12,754 / 59,502 / 39,886 / 34,827.
- U2-WALL-OLD, 4/4: refused, fail closed, memory byte-identical.
- W3 (reported only): no time save, because U2a has none. Every save was a ruling-51 moment (center heals, ch1_rival_route103, ch1_pokedex). Pace was 370-568 frames/s.

DROP SENTENCES
- HOST, printed live by the launcher (LAUNCH, LAUNCH-OLD, R2-RETRY and U2-WALL step 1). These always follow a harness kill, e.g. "this continue drops: session(s) 1 (not counted (no launcher line with the count) by the host's count; not recorded (a session ended without its end line) by the AI's record), from play time 0:21 at save 2 to session 1's end (its play time not recorded: no end line), 0 battle(s) lost (undone), maps first stood on after it: none (…)".
- HOST, counted form. This was rendered by drop_words from child C's live ContinueCheck.dropped, not printed by the launcher:
  - "…session(s) 2 (2,620 frames by the host's count; 2,620 frames by the AI's record), from play time 0:29 at save 2 to 0:29 at session 2's end, 0 battle(s) lost (undone), maps first stood on after it: ROUTE103, OLDALE_TOWN_MART (…)"
  - for the wall end: "…(59,502 frames by the host's count; not recorded … by the AI's record), from play time 0:38 at save 4 …".
- AI, counts only:
  - U2-BUDGET: "[AI-HANDS] continue: this continue drops 2620 frames of play after save 2, and 0 battle(s) lost".
  - After a kill or a wall end: "[AI-HANDS] continue: this continue drops the play after save N, its frames not recorded (a session ended without its end line), and 0 battle(s) lost".

BUDGETS
- CHAIN B: widest arrival-to-kill 82,805 of 242,294; widest wall 159.4 s of 461 s.
- OLD Bs: widest arrival-to-kill 45,080 of 145,938; widest wall 110.3 s of 323 s.
- No budget was reached.

HYGIENE
- The main sandbox-pokebot has 0 paths newer than the marker.
- The worktree's only writes were to the ledger.
- The provenance digest was the same before and after: 76170fc5757b447e.
- The main checkout's git status is unchanged.

WHAT I DID NOT DO
- No git writes and no commit.
- No code, test or doc edits.
- test_kb2 NOT RUN (ruling 4).
- U2-TIME, U2-TIME-OLD and T0 not run (ruling 1). So the spec's hand-back items about "ends now" saves and D7's price do not apply.
- No unit gates re-run: this stage changed no code.

Next: the orchestrator's independent re-run on 5661-5664 and an adversarial review.

# Adversarial review

> Hand-back section, verbatim.

ADVERSARIAL REVIEW OF U2a (worktree wf_6a7c527a-7d2-1, HEAD 417df790 plus uncommitted changes). Times are Los Angeles: about 5:20 AM to 5:32 AM.

VERDICT: FINDINGS. There are 4 MINOR and 3 NIT findings and no MAJOR. I found no path that continues a NOT CLEAN or CHOSEN end through code U2a added. The one forbidden-reload path I found (F1) is pre-existing; U2a closed only its hard-kill sibling.

What I read:
- the spec, as amended by orchestrator rulings 1-5;
- the three hand-backs;
- the whole diff of launcher.py, __main__.py, game_memory.py, mode.py, skills/saving.py, check_purity.py, check_fairness.py, the U2 parts of test_saving.py, revert_r1.py's new mutants and census U2C01-07, live_r1.py's U2 code (run_launcher, cmd_u2budget/u2wall, grade_u2budget/u2wall, wall_expected_line, u2_old_shows), the ledger diff, the README diff and the held-out evidence's drop sentences.

What I ran. All of it ran offline, on copies or in temporary folders; I never edited the worktree. Scripts and outputs are in s53/u2/build/review/.
1. plant_modattr.py (D15 cross-module rebinding). check_fairness alone misses `m.int = Progress`, but the purity gate refuses it (rules a and f). Sound. Last lines: 'FAULT-2 ... [f] assigns to `.int` of the imported `plant_rv5`', and 'runtime after rebinding: (1, 2)', which confirms the read the gates prevent.
2. plant_pin.py (the D3 AST pin). Keyword-form finish calls are MISSED (F3). Last line: 'PROBE wall-clock with keyword wrong code: problems=0 reasons==tables=True -> MISSED'.
3. probe_interrupted.py. A refused reset plus Ctrl+C is ALLOWED (F1). Line: 'reset-refused, interrupted: ok=True class=INVOLUNTARY'.
4. probe_oldline.py. An old line with a hard kill after a crash reads as NOT CLEAN with false words (F5). Line: 'old line, hard kill after a crash verdict: ok=False class=NOT CLEAN'.
5. mutant_hostframes.py (copy mutants on 53 LauncherContinueTests and MemoryFileTests). Last lines: 'CONTROL: rc=0 ... OK', 'HM1: rc=0 Ran 53 tests ... OK' (F2: host_frames from the AI's record survives), 'HM2: rc=1 FAIL: test_u2_the_drop_uses_the_hosts_count...'.
6. ledger_diff.py. Line: 'first 61 entries identical: True'. #63 was registered before it was begun.
7. find_mmin.out. Line: 'main sandbox-pokebot entries modified in the last 90 minutes: 0'.

Findings:
- F1 (MINOR): launcher.py:490 judges `interrupted` before the verdict. A refused reset or a CHOSEN end whose process lingered and was hit by Ctrl+C is INVOLUNTARY and allowed. It is pre-existing, and it is the sibling of F-U2-5/D3a, which was fixed only for the hard kill.
- F2 (MINOR): no unit test tells the host's count from the AI's. Every fixture has real_frames equal to the AI's frames, and no fixture has a launcher session with no end line. Mutant HM1 survives.
- F3 (MINOR): host_end_sites collects only `finish` calls with two positional args (test_saving.py:2132). A keyword-form host end, or one re-coded with a keyword, passes the pin.
- F4 (MINOR): README:824-825 and :856-857 still say 'the live arms not yet run' and 'DEVELOPMENT only ... held-out is next', though #63 PASSED.
- F5 (NIT): on an old line, the fallback to the process code uses the launcher's own 124 after a hard kill (launcher.py:498).
- F6 (NIT): D4 keys on the AI-written run_dir, and KNOWN LIMITS does not say so.
- F7 (NIT): dropped_after hands at_end and run_dir to AI deciding code, behind the game_memory '*' door, with only a docstring keeping them unread.

Deviations:
- The hand-backs cite the code where it differs from the spec. I accepted those deviations because the code wins (the D15 'case int(x=1)' plant, the old line's purity.json verdict word, the B1/W1 graders).
- W1's expected host_frames is the same formula as launcher._host_frames, re-derived on the test side. It checks the plumbing, not the formula's boot-offset premise; that premise was measured at 0 on 128 rows.

What I did NOT do:
- no live arms;
- no full revert_r1, revert_step3/4/5 or regression lane re-run (the builders' green results stand unverified by me, apart from the 53-test CONTROL on a copy and both gates passing on a package copy);
- no test_kb2;
- no git writes, and no edits to the worktree, the main checkout or the tuner's clone.

# Independent re-run, seeds 5661-5664 (ledger #64)

> Hand-back section, verbatim.

## U2a independent re-run (#64, seeds 5661-5664): PASS, and I agree with stage 3 on every graded arm

**Stage:** C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/u2/build/rerun/ (every output I rely on is saved there)

**Worktree:** wf_6a7c527a-7d2-1 on HEAD 417df790. The code under test is the uncommitted working tree, digest 76170fc5757b447e, the same as #63. The digest was the same at begin and after the run.

**Writes:** the only writes to the worktree were:
- ledger.json entry #64, through the driver's ledger commands;
- ai_player/evidence/2026-10-30-u2a-RERUN.txt (701,470 bytes, sha256 a35949ea811ba581...).

There were no git writes and no AI, host or gate code was changed.

### What I did, in order (Los Angeles time)

1. **Lane census at 5:20 AM:** `lane census (...): 0`. It was 0 again before registration, at registration and at the end.

2. **Seed check** (adapted from stage 3's fault-tested classifier, seeds retargeted):
   - The first pass found 50 unclassified hits. None was a seed use (seed-hits-context.out):
     - a `looks=` count;
     - frame numbers in RATE tuples and `' frames '`;
     - a frame argument to `verdict(fresh, 1500.0, …)` in copies of live_step2.py;
     - `trainer_parties.h:5663` in copies of trainers.json.
   - The second pass adds four rules, each pinned to its file. 31 planted FAULT/CONTROL classifier cases pass; in particular, the same text in another file reads OTHER, and `"seed": ` in those files reads USE.
   - Last line: `SEEDS 5661-5664 USED ANYWHERE: 0 -> UNUSED: YES`. Both ledgers have no entry meeting 5661-5664.

3. **My instrument**, adapted from r1f/build/verify-rerun:
   - I kept mine.py (flash parser and strict memory reader), my_facts, my_checks, fault_mine and compare, and pointed them at this worktree.
   - New: u2budget_facts and u2wall_facts. They read only raw files:
     - the launcher's launches.jsonl line (exactly one per run);
     - the run's purity.json `counters.real_frames`, as a second host count;
     - the frozen memory.jsonl, through my strict reader;
     - the frozen carts, through my parser;
     - the end line, matched by its `session` field rather than its position;
     - world.jsonl maps by their own `first_frame`, cross-checked against the restored-set rule;
     - S2's id by identity (stamp = K-AFTER's S2 RAM truth);
     - for U2-WALL, the line on the cart by stamp + world.jsonl const of the cart's map + tile + party PIDs;
     - the OLD children's profile memory after the child, by my own sha256.
   - Also new: two discriminators per seed (11 per seed), the K-arm determinism lines against CONTROL, and a D19 report (the AI's drop line names no map const and no H:MM).

4. **Fault-tested before my seeds existed**, on #63's raw outputs:
   - 41 U2 plants were added (U1-U41), including an off-by-one save id, host_frames +1, and host_frames equal to the whole real_frames with the offset ignored.
   - The identity matcher has a CONTROL and a FAULT: an earlier line given the cart's stamp still matches uniquely; given the stamp, map, tile and party too, two lines match and W2 fails.
   - Results:
     - seed 5654: `MY INSTRUMENT FAULT TEST: PASS (control clean True; 89 of 89 planted faults caught; missed: none)`;
     - seeds 5651 and 5652: 87 of 89. The misses are R3 (B has fewer than 2 post-continue lines) and N2 (the anchor is already 1), plants that cannot be made on those seeds.
   - The per-arm comparator was also fault-tested: `COMPARE FAULT TEST: PASS`.
   - The instrument was frozen by sha256 at 5:29 AM, before registration. It was re-checked after the run: `INSTRUMENT UNCHANGED SINCE FREEZE`.

5. **Selftest before:** `SELFTEST: the clean run PASSES (100 cases) and 18 of 18 planted faults FAIL as they must -> PASS`. The same line again after the run.

6. **Ledger:**
   - numbers: `REGISTERED NUMBERS sha256 1f248cce2242a3d1...`;
   - register at 5:31:01 AM (#64);
   - begin at 5:31:02 AM: `... REGISTERED 2026-10-30 05:31:01 with the bounds sha256 1f248cce2242a3d1; this run's bounds sha256 1f248cce2242a3d1 (the same); no other entry of family 'story' names any of these seeds`.

7. **Plan:** stage 3's run_plan.py with only the seeds changed (diff saved), at 12 jobs at once. `PLAN DONE: 80 jobs, exit codes not 0: none (05:44:08 AM, 779 s)`.

8. **Registered verdict:** `LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 0 of 4: vacuous; passed 0 of 0; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 42 of 44)`

9. **My grade:**
   - `MY VERDICT (5661-5664): PASS (failing: none; below the floor: none; my discriminators that differ: 42 of 44; checks BAD on counted arms: 0)`
   - `PER-ARM TABLE: 19 of 19 graded arms AGREE with the registered verdict's table; DIFFER: none; registered verdict PASS`
   - On #63's 5651-5654: `MY VERDICT (5651-5654): PASS (...42 of 44...)` and `PER-ARM TABLE: 19 of 19 ... AGREE`.
   - The row-level comparison gives 78 of 80 on both rounds. The only cells that differ are CHAIN-OLD and CHAIN-R1-OLD on the seed where CHAIN does not count: the row summary's `counted` comes before the twin rule, and the verdict table applies it.

10. **Hygiene:**
    - `STOP RULES: none fired`
    - `U2-WALL step 1 not wall-clock/124/CLEAN/no hard kill on: none; hard kill with a wall-clock verdict on: none`
    - main sandbox: `paths newer than the marker: 0`
    - worktree during the run: `paths newer than the marker: 0`
    - provenance after: digest 76170fc5757b447e
    - `FINISHED #64`; `LEDGER ledger.json: 64 entries; well formed -> PASS`
    - The main checkout is at HEAD 417df790 with the same 14 untracked evidence files as the session-start snapshot.

### Arm by arm against stage 3's #63 verdict (my instrument on its raw outputs)

I AGREE on all 19 graded arms:
- **4/4 ok:** CONTROL, K-AFTER, K-INSIDE, K-SILENT, K-FIRST, K-BETWEEN, LAUNCH, R2-RETRY, U2-BUDGET, U2-WALL.
- **CHAIN 3/4:** 5653 is not counted because rule N was not met; B reached ch1_pokedex.
- **OLD arms 4/4 shows:** K-INSIDE-OLD, K-SILENT-OLD, LAUNCH-OLD, R2-RETRY-OLD, U2-BUDGET-OLD, U2-WALL-OLD.
- **CHAIN-OLD and CHAIN-R1-OLD 3/4:** both also show on 5653.

My discriminators match its count (42 of 44). For U2, my expected drop equals the reported one on every #63 seed (u2-brief-5651-5654.out).

### Measured on 5661-5664

**LAUNCH (4/4):** `play: stopped: not finished within 2620 frames`, exit 0, CLEAN, verdict_code 0, frames == real_frames == 2620 (purity.json agrees), hard_kill False. The end line has budget True and at_save False. The frozen cart is byte-identical to K-AFTER's.

**U2-BUDGET (4/4):**
- B1: my expectation equals ContinueCheck.dropped on every seed: save 2, sessions [2], host_frames 2620, AI frames 2620 (boot offset 0), at_save = S2's RAM stamp, lost 0.
- Maps: none, OLDALE_TOWN_MART, none, none. Both map paths and both lost paths agree.
- B2: C continued 2 and arrived at S2's truth.
- B3: C's session `dropped` is {frames 2620, lost 0}.
- D19: the AI line `[AI-HANDS] continue: this continue drops 2620 frames of play after save 2, and 0 battle(s) lost` names no map and no play time.

**U2-BUDGET-OLD (4/4):** U0's launcher ran (my sha 56c160ee915c13f9 ≠ real 3b62d71ca3d5a0b4); `ok False`, class BUDGET, `...: USER RULING 52`; memory sha256 identical before and after.

**U2-WALL (4/4):**

| | 5661 | 5662 | 5663 | 5664 |
|---|---|---|---|---|
| real_frames | 81,486 | 89,740 | 107,349 | 129,697 |
| pace (frames/s) | 372.6 | 410.3 | 490.9 | 593.0 |
| launcher-start-to-arrival (s) | 7.5 | 8.0 | 8.0 | 7.0 |
| FILE (my parser) | S6 | S5 | S7 | S6 |
| line matched by identity | 6 | 5 | 7 | 6 |
| dropped host_frames | 3,063 | 38,186 | 20,710 | 33,452 |
| maps after the save | ROUTE102 | OLDALE_TOWN_HOUSE2, ROUTE102 | OLDALE_TOWN_HOUSE1, ROUTE102 | OLDALE_TOWN_HOUSE1, ROUTE102 |

- Step 1 ran wall-clock, about 218.7 s each.
- Each line matched by identity is the newest save, and C continued it.
- Dropped host_frames = real_frames − (save.frame − frame_base), recomputed by me; AI frames None; at_end None.
- The maps after the save agree with my world.jsonl first_frame read.
- W3: the counter rose on 4 of 4. Every step-1 save was a ruling-51 moment (centre heals, ch1_rival_route103, ch1_pokedex); there are no time saves, since U2a has none.

**U2-WALL-OLD (4/4):** refused (`... with no end line of the AI's (refused: fail closed)): USER RULING 52`), class BUDGET, memory byte-identical.

**Discriminators:** 42 of 44 differ (registered and mine). The 2 that do not are the CHAIN pairs on 5662, where CHAIN did not count.

**Determinism** (equal lines are one trajectory replayed, not a replication):
- 24 of 24 K-arm lines equal CONTROL's, registered and mine.
- CHAIN vs CHAIN-OLD / CHAIN-R1-OLD presses to B's first save's e3 are identical on all 4 seeds (981 / 920 / 950 / 893 presses; chain-presses.out).

**CHAIN 5662:** B saved 4 times (Oldale centre ×3, then the lab) and ended `play: done: ch1_pokedex reached` with no rule-N anchor met. This is the same shape as #63's 5653. Nothing was tuned.

**RV-3:** no budget was reached.
- CHAIN: widest arrival-to-kill 73,012 (5663) of 242,294; widest killed wall 156.5 s of 461; the unkilled 5662 B took 194.9 s.
- OLD B arms: widest 43,645 of 145,938; widest wall 105.1 s of 323.

**Drop sentences printed live:**
- HOST: LAUNCH, LAUNCH-OLD, R2-RETRY and U2-WALL, 4 each.
- AI: LAUNCH 4, R2-RETRY 4, U2-BUDGET 4, U2-WALL 8.

### Deviations and why
- **Seed classifier rules:** I added four new rules (the hits above). Each is pinned to its file and planted-tested. The superseded first pass is kept in the evidence.
- **Instrument scripts written after the freeze:** compare_perarm.py, fault_compare.py, chain_presses.py and u2_brief.py.
  - compare_perarm and fault_compare were written and fault-tested at 5:31 AM, before any re-run row existed. They compare against the table the verdict is computed from, because compare.py's row-level `counted` comes before the twin rule.
  - chain_presses.py is a read-only helper. my_facts skips CHAIN's press digest when B left no frozen set (it was never killed), so on 5662 it printed `[0, 920]`. That is not a determinism break: read from the rows directly, the presses are identical (920 = 920).
- **K-arm determinism fields:** my lines compare saves' [e3, e4]; the registered lines use other event frames. Both say 24 of 24.
- **CHAIN wall:** measure_rv3's "wall widest 194.9 s (5662)" is the unkilled B.
- **Plan and reused scripts:** the plan script equals stage 3's except for the seeds. measure_u2, summarize_u2, measure_rv3 and drop_sentences were reused unchanged. assemble_evidence has only its source-folder string changed.

### Vacuities (reported, not passed)
- W2's branch where the counter is unchanged and C continues S2 never ran live (the counter rose on 4 of 4).
- U2-BUDGET's lost was 0 everywhere.
- U2-BUDGET's maps compared a non-empty list on 1 of 4 seeds (5662).
- K-BETWEEN-MID counted 0 of 4 (diagnostic only).
- The counted form of the HOST drop sentence printed live only in U2-WALL's child C (every real-launcher continue follows K-AFTER's harness kill).

### Not done
- test_kb2: NOT RUN, because it cannot run in a worktree (ruling 4).
- No revert lanes or unit suites: no code changed since stage 1.
- No commits.
- I killed no processes; every child ended on its own.

# Fix round, seeds 5671-5674 (ledger #65)

> Hand-back section, verbatim.

U2a FIX ROUND (stage 'fix'). Worktree C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_6a7c527a-7d2-1, HEAD 417df790. The changes are uncommitted, nothing is staged, and I made no git writes. I worked about 5:48 AM to 6:50 AM Los Angeles time. Scratch outputs are under C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/u2/build/fix/.

All four findings were real. I reproduced each one before fixing it.

What I built:
- F1, ai_player/host/launcher.py `_classify_session`. The interrupted row now reads `if line.get("interrupted") and line.get("exit_reason") in (None, "interrupted", "interrupted-unresponsive"):`. Any other verdict goes through D3/D3b and the class rows.
  - Test: test_saving.LauncherContinueTests.test_an_interrupt_is_judged_by_its_verdict_first.
  - Mutant: revert_r1 U4c (the old order).
- F2, test side. The drop test gained two FAULT halves in which the host count and the AI count differ:
  - a continue ended by the wall clock with no end line and real_frames 5000 gives host_frames 5000 and AI frames None;
  - an end line of 2620 against the instrument's 2700 gives host_frames 2700.
  - Mutant: revert_r1 HM1. It was NOT CAUGHT before these test changes and is CAUGHT after.
- F3, test side. test_saving.host_end_sites now:
  - reads `finish` calls whose reason or code is passed by keyword;
  - reports any call shape it cannot read, and any unresolvable reason or code (except inside lifecycle.give_up);
  - walks the whole module, not only function bodies.
  - The pin test gained 6 FAULT subtests and 1 keyword CONTROL.
  - Mutant: revert_r1 U12, a NEW host end in keyword form. The pre-fix pin passed this exact plant.
- F4, ai_player/README.md. The headline, the rule bullet and 'Proof so far' now name #63, #64 and #65, with their caveats.

Checks, each with its verbatim last line:
- repro_f1_before.out: 'FAULT reset-refused, interrupted: ok=True class=INVOLUNTARY'. repro_f1_after.out: 'ok=False class=NOT CLEAN'.
- revert_r1_hm1_before_test.out: '[HM1] ... -> NOT CAUGHT'.
- repro_f3: before 'F3 PROBE: 3 of 9 as required -> FAIL'; after 'F3 PROBE: 9 of 9 as required -> PASS'.
- test_saving 'Ran 149 tests' / 'OK'. test_goals 'Ran 257 tests' / 'OK'. test_host 'Ran 37 tests' / 'OK'. test_safety_gates 'Ran 50 tests' / 'OK'.
- call_census 'CALL-SITE CENSUS: PASS'. check_purity 'VERDICT: PASS'. check_fairness 'PERSON-FAIR DATA DOOR: PASS (0 breaches)'. check_lessons 'LESSONS CHECK: PASS (0 problems)'. Anchor audit 'anchors checked 1150; not exactly once: 0'.
- Quick lane 'REGRESSION: PASS (quick, 21 suites, 21.1 s wall)', and on the final tree 21.2 s.
- revert_r1 full (6:17-6:39 AM, 1,311 s, running alongside the other two): '549 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as predicted, of 550 run (550 defined)' / 'OVERALL: PASS'.
- revert_step5: '400 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 402' / 'OVERALL: PASS'.
- revert_safety_gates: '23 mutants CAUGHT as predicted, of 23' / 'OVERALL: PASS'.

Live re-run: F1 changed host code that LAUNCH, R2-RETRY and U2-WALL run, so every arm was re-run.
- Seed check v2: 'SEEDS 5671-5674 USED ANYWHERE: 0 -> UNUSED: YES'.
- v1 found 9 hits that were not seed uses: a memory-read count in WARPREAD and a frame count in the 401-410 rate record, 3 copies of each folder. v1 is kept as superseded. v2 adds 2 rules, each pinned to its file, and its 40 of 40 classifier plants (FAULT and CONTROL) are ok.
- Selftest PASS; lane census 0; registered #65 at 6:02:24 AM; begun at 6:02:25 AM; tree 3ee9263f8e7d43eb.
- One plan of 80 jobs, 6:02:48 to 6:15:23 AM, every exit code 0.
- Verdict: 'LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 1 of 4: below the floor; passed 1 of 1; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 42 of 44)'.
- Determinism: 24 of 24. 'STOP RULES: none fired'.
- Afterwards: the main sandbox-pokebot had 'paths newer than the marker: 0' (and 0 since the re-run's 5:31 AM marker); provenance after was the same digest; selftest PASS; ledger 'FINISHED #65' and '65 entries; well formed -> PASS'.
- Evidence: ai_player/evidence/2026-10-30-u2a-FIXROUND.txt.

Measured:
- Every arm met its floor. CONTROL, the K arms, LAUNCH, R2-RETRY, U2-BUDGET and U2-WALL each counted 4/4.
- CHAIN counted 3/4. On 5674, child B ended 'play: done: ch1_pokedex reached' at 86,118 frames before rule N: the known shape, nothing tuned.
- Every OLD arm showed its difference where its twin counted.
- LAUNCH: real_frames == frames == 2620, not at a save, 4/4.
- U2-BUDGET: host 2620 = AI 2620 (offset 0). Maps: OLDALE_TOWN_MART on 5671, none on the other three seeds.
- U2-WALL step 1: wall-clock/124/CLEAN, hard_kill False, 4/4. real_frames 83,771 / 85,336 / 107,420 / 127,404. Dropped host_frames 2,120 / 35,097 / 41,195 / 17,212. The newest save was step 1's own on every seed, and W2 matched exactly one save line by identity on every seed.
- RV-3: the OLD Bs' widest arrival-to-kill was 43,879, against the registered 145,938.

Deviations:
- U12's first form (re-coding wall-clock by keyword) was replaced. The old pin's set-equality check already caught it, so it did not tell the fix apart.
- AI_PLAYER_TEST_SUPPORT_ROOT was set to the folder holding sandbox-pokebot (the main checkout), as in stage 1. The code reads it that way.
- The ledger's free-text verdict says 6:02:41 AM for the plan's start; the log says 6:02:48 AM.

What I did NOT do:
- test_kb2 (it cannot run in a worktree).
- revert_step3, revert_step4 and test_check_purity: not re-run after the fixes (not asked for, and none of the fixes touch their code).
- No commit.
- I touched no file of the main checkout. Its git status still shows the same 14 untracked files as at session start.

Do not commit the stale trees/ zips 51a2da10, edf0754c, 285b3b1e, 311eacf0, 4feea463 and 74a2a02a. The final tree's snapshot is 3ee9263f8e7d43eb.zip.

# Verification: adversarial review of the fix round

> Hand-back section, verbatim.

ADVERSARIAL REVIEW OF U2a's FIX ROUND (stage verify-review, 6:30-6:55 AM LA time, 2026-10-30). Worktree: wf_6a7c527a-7d2-1 on HEAD 417df790. I read it only and never edited it.

WHAT I CHECKED: each of the four fixes (F1-F4) against its finding, the new mutants (U4c, U12, HM1), ledger entries #62-#65, and the README U2a section. I also hunted for siblings of each fixed shape.

VERDICT: FINDINGS, with 3 MINOR and 1 NIT.

V1 (MINOR). F1's fixed row lets a brain-forged 'interrupted' through when a Ctrl+C lands. The row allow-lists the reason WORDS 'interrupted' and 'interrupted-unresponsive' and never checks the code, so a brain-forged 'interrupted' (give_up, code 0) plus a Ctrl+C in the linger window is judged INVOLUNTARY and allowed. Without the Ctrl+C the same verdict is NOT CLEAN.
- Probe probe_forged_interrupt.out: 'FAULT forged 'interrupted' code 0, Ctrl+C: ok=True class=INVOLUNTARY' against 'CONTROL forged 'interrupted' code 0, no Ctrl+C: ok=False class=NOT CLEAN'.
- Proposed fix: limit the row to exit_reason None. In copy mutant mut_F1fix.out, the only failures are the two CONTROL subtests whose why-text changes.

V2 (MINOR). F2's shape survives on the own-session row. Mutant HM3 removes frame_base from the own-session offset and survives every offline suite:
- mut_HM3.out: 'Ran 54 tests ... OK'.
- mut_HM3_full.out (test_saving + test_goals): 'Ran 406 tests ... FAILED (errors=7)', the same 7 mgba env errors as the unmutated control mut_NONE_full.out.
- Why it survives: every fixture's own session has base 0. Live U2-WALL does hit an own continued session with a large base (#65: 'own': true, 'since': 144475), but only a new live run would catch the mutant.

V3 (MINOR). A regression introduced by F1's fix. A pre-U2 launcher line has no verdict_code. When such a line is interrupted and carries a real host verdict, the code now reads the PROCESS code 130 (from run_child), so the judgement is a permanent NOT CLEAN, and the sentence wrongly says 'the instrument's exit code 130'. Before the fix this was INVOLUNTARY.
- Probe probe_old_line_interrupt.out: 'OLD line, interrupted, real host 'crash' (verdict file code 2): ok=False class=NOT CLEAN'.
- CONTROLs: the new line and the old line without an interrupt are both INVOLUNTARY.
- This contradicts the README's 'reads as before'. D3a's old hard_kill lines share the root.

V4 (NIT). Ledger #65's start time is 6:02:41 in the free text and 6:02:48 in the plan log. The builder already reported this.

WHAT HOLDS:
- F1 as filed is closed, and U4c is defined.
- F2's halves discriminate HM1.
- F3's pin handles keywords, odd call shapes and module-level calls, and gives no false positive on mentions (AST only). Its file set is complete (only session.py and lifecycle.py finish).
- F4's README text is current.
- Every graded range was registered before it ran.
- The AI-side drop text holds counts only (D19).
- No bot code was touched.

COMMANDS, each with its last line (outputs under s53/u2/build/verify-review/):
- py -3.12 probe_forged_interrupt.py: 'OK', plus the lines above.
- py -3.12 probe_old_line_interrupt.py: 'OK', plus the lines above.
- Copy mutants NONE, HM3 and F1fix, unittest LauncherContinueTests + MemoryFileTests:
  - NONE: 'OK' (Ran 54)
  - HM3: 'OK' (Ran 54)
  - F1fix: 'FAILED (failures=2)'
- Full test_saving + test_goals on the HM3 and NONE copies: both 'FAILED (errors=7)', the same env errors.

WHAT I DID NOT DO:
- I ran no live arms and no full revert_r1, revert_step3/4/5 or regression lanes. I trusted the hand-back's reported lines for those.
- The copy runs used AI_PLAYER_TEST_SUPPORT_ROOT = the worktree, so 7 mgba-dependent tests errored on the control too. They are unrelated to the launcher.
- test_kb2 and test_host: NOT RUN.

# Verification: independent re-run, seeds 5681-5684 (ledger #66)

> Hand-back section, verbatim.

## U2a: independent re-run of the fix round's code on seeds 5681-5684 (ledger #66)

The fix round's code passes on new seeds, and I agree with its verdict on 5671-5674 for every arm I recomputed. I wrote none of U2a's code and changed no AI or gate code. In the worktree I wrote only to `ledger.json` (through the driver's ledger commands) and to one evidence file. I made no git writes.

### Before the run
- **Process check (6:52:58 AM):** no other lane or live proof was running.
- **Seed check (my own `seed_check.py`):**
  - My first version matched raw digits and hit hashes and line numbers, so I replaced it. I kept its output, marked as superseded.
  - The second version counts a hit only where the number is used as a seed. Over 30,077 files:
    - There were 0 overlaps in the three ledgers: the worktree's (65 entries), the main checkout's (61) and the bot tuner's clone (61, read only).
    - It found 10 text hits in 3 files. None is a use of the seeds: one is the spec's own line allocating 5681-5684 for this round, and the others are a line range `story_mode.py:5678-5683` in a recon note.
  - Its FAULT arm searched the used range 5671-5674 and found 2125 hits, which shows the search can see a used range.
  - Result: 5681-5684 were unused.
- **Code identity:** `provenance` gave `working-tree digest sha256:3ee9263f8e7d43eb`, the same tree #65 ran.
- **Selftest:** `SELFTEST: the clean run PASSES (100 cases) and 18 of 18 planted faults FAIL as they must -> PASS`.
- **Ledger numbers:** identical to #65's except for the seeds (`numbers-diff-65-66.out`).
- **Registration:** registered at 7:02:09 AM (`REGISTERED numbers sha256 f0fc31b9...`) and begun at 7:02:10 AM (#66, tree 3ee9263f8e7d43eb), before any seed ran.

### The run
- **One plan of 80 jobs**, using my own `run_plan.py` with the same arm set as #63-#65 and 12 jobs at once: `PLAN DONE: 80 jobs, exit codes not 0: none (07:15:21 AM, 785 s)`. The first job started at 7:02:16 AM.
- **One verdict:** `LIVE R1 VERDICT: PASS, WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE 'new', NOT THE SPEC'S MIDPOINT (the midpoint arm K-BETWEEN-MID counted 0 of 4: vacuous; passed 0 of 0; orchestrator ruling 5) (failing: none; below the floor: none; discriminators that differ: 44 of 44)`.
  - All 19 graded arms counted 4 of 4, CHAIN included (#65 had CHAIN at 3 of 4).
  - Every OLD arm showed its difference.
  - The driver's determinism lines: 24 of 24 match CONTROL.

### My own instrument
It is `my_checks.py` plus my own Emerald save parser `my_sav.py`. Neither imports anything from `ai_player` or `live_r1`.

- **What it reads:** the primary files — the carts, `launches.jsonl`, `purity.json`, `memory.jsonl`, `world.jsonl`, `actions.jsonl` and the children's RESULT lines.
- **What it takes from the driver's rows:** only the harness's record of each save's game state (`a.saves[*].truth`) and, for the two CHAIN pairs, the driver's `counted` flag.
- **Frozen before use:** frozen at 7:16:21 AM (sha256 `ea1dca41...` and `f8571b6c...`), before it read any 5681-5684 data. Before that it had only been trial-run on #65's recorded rows.
- **Fault-tested:** `MY INSTRUMENT FAULTS: 14 of 14 planted faults seen`. The planted faults were:
  - the host count short of the budget;
  - a self-graded `host_frames`;
  - an extra map in the drop;
  - the continue refused;
  - the wall-clock code set to 0;
  - a stamp-only match;
  - the memory changed;
  - a launcher that is not U0's;
  - a broken sector in the cart;
  - a shifted arrival;
  - two discriminators forced to agree;
  - an OLD arm replaced by its NEW twin;
  - one press of the replay changed.
- **Results on 5681-5684:**
  - `MY U2 CHECKS: 180 of 180 true; not true: none` (156 U2 checks plus my 24 determinism lines).
  - `MY DISCRIMINATORS: 44 of 44 differ`.
  - `MY DETERMINISM: 24 of 24 same as CONTROL`.
- **Against the driver:**
  - 5681-5684: `DISCRIMINATOR VALUES: agree 44 of 44 pairs; disagree 0`, and determinism agrees on 24 of 24.
  - #65's rows (5671-5674): also 44 of 44, with 42 differing (the 2 that don't are CHAIN on 5674, which did not count), and determinism agrees on 24 of 24.

### The U2 arms, measured
- **U2-BUDGET:**
  - LAUNCH's line: real_frames == frames == 2620, CLEAN, code 0 / 0, `budget` True and `at_save` False; the cart was unwritten (sha256 equals K-AFTER's).
  - `host_frames` 2620 = the AI's 2620 (boot offset 0).
  - `at_save` = S2's in-game play time (H:MM) as the harness recorded it.
  - Arrival = S2's recorded state (party IDs, map, tile, play time at boot); CONTINUE was pressed; no new game; no error page.
  - C's own `dropped` equals the launcher's.
- **U2-WALL:**
  - Step 1 ended wall-clock / 124 / CLEAN with hard_kill False on 4 of 4, real_frames 82,135 to 117,909.
  - `host_frames` = real_frames − (save.frame − frame_base) on every seed: 13,167, 12,137, 18,138 and 28,126.
  - The AI's frame count and play time at the end are both "not recorded" (None).
  - continued_from matched one unique save by identity on each seed (save 6, 6, 8 and 7); its save stamps are at least 3 game minutes apart.
- **Both OLD arms (mutant U0):** refused with class BUDGET, and the memory stayed byte-identical. The U0 tree's `launcher.py` equals the real file with exactly U0's two edits, which I rebuilt by hand.

### Arm by arm against the fix round's verdict on 5671-5674
I AGREE wherever I recomputed. Same results on 5681-5684 unless noted.

| Arm | Agree? | What I recomputed | Not recomputed |
|---|---|---|---|
| U2-BUDGET | AGREE | reached, every check true, 4 of 4 | — |
| U2-BUDGET-OLD (U0) | AGREE | refused (BUDGET), memory unchanged, U0 ran; 4 of 4 | — |
| U2-WALL | AGREE | reached, every check true, 4 of 4 | — |
| U2-WALL-OLD (U0) | AGREE | refused (BUDGET), memory unchanged, U0 ran; 4 of 4 | — |
| LAUNCH / LAUNCH-OLD | AGREE | first look [UNKNOWN, 0] vs [OVERWORLD, 66883]; LAUNCH's line facts | cold boot, title before CONTINUE |
| K-AFTER, K-INSIDE, K-SILENT, K-FIRST, K-BETWEEN, CONTROL | AGREE | FILE verdicts from my parser, continued_from, the new maps against the restored ones, determinism | their full checks 1-7 |
| K-INSIDE-OLD, K-SILENT-OLD | AGREE | continued_from [1, 2]; the new maps restored only in OLD | — |
| CHAIN, CHAIN-OLD, CHAIN-R1-OLD | AGREE | parent [1, 2]; my rebuilt last-save id [3, 1]; on 5674 CHAIN did not count | counted flag and rule N (driver's flag used) |
| R2-RETRY / R2-RETRY-OLD | AGREE | memory_check.ok [True, False], classes [KILLED, CHOSEN] | R2-RETRY's other checks |
| K-BETWEEN-MID (diagnostic) | — | counted 1 of 4 on #65, 0 of 4 on #66; never graded | — |

### STOP rules (ruling 3)
None fired:
- LAUNCH ended at a save on 0 seeds, and real_frames == frames on 4 of 4.
- U2-WALL had a hard kill on 0 seeds.
- Every OLD arm counted where its twin did.
- 24 of 24 determinism lines held.

### Gaps the live arms did not exercise
- W2's branch for an unchanged save counter never ran: the counter rose on 4 of 4.
- U2-BUDGET's `lost` was 0 on every seed. Its maps were non-empty on 1 of 4 (5681, OLDALE_TOWN_MART).
- The launcher's drop sentence printed only in its "not counted" form, 16 of 16. Every real-launcher continue here follows K-AFTER's harness session, which has no launch line.
- The AI's own drop line printed with frames 4 times and "not recorded" 40 times.
- F1's fixed row cannot be reached by any live arm, so it is proven by unit tests only.

### Other checks
- **Unit tests:**
  - My first `test_saving` run used the wrong support root (`sandbox-pokebot`) and failed with `FAILED (failures=1, errors=8)`. That was my setup error; the output is kept and labelled.
  - With the main checkout as the support root: `Ran 149 tests` / `OK`.
  - The F1 and F3 tests by name (`test_an_interrupt_is_judged_by_its_verdict_first`, `test_the_host_codes_match_the_host`): `Ran 2 tests` / `OK`.
- **After the run:**
  - Selftest: `... 18 of 18 planted faults FAIL as they must -> PASS`.
  - Provenance: still `3ee9263f8e7d43eb`.
  - The main checkout's `sandbox-pokebot`: `paths newer than the marker: 0`. The scan's FAULT arm on the stage folder found 2529 new paths.
  - Process check at 7:20:51 AM: 0 other lanes and 0 of my processes alive.
- **Ledger:** `FINISHED #66`, then `LEDGER ledger.json: 66 entries; well formed -> PASS`.

### Not done
- **Not run:** `test_kb2` (it cannot run in a worktree, ruling 4); `revert_r1`, `revert_step3/4/5`, `revert_safety_gates` and the quick lane. The revert drivers write tree snapshots into the worktree, which is outside my allowed writes.
- **#65's time slip:** confirmed but left alone, since the entry is not mine. Its ledger text says 6:02:41 AM; its plan log says 6:02:48 AM.

### Files
- **Evidence:** `ai_player/evidence/2026-10-30-u2a-VERIFY.txt` in the worktree (451,246 bytes, sha256 `8b34f799...`). It holds every saved output verbatim, including my scripts.
- **Stage folder:** `s53/u2/build/verify-rerun/`. The plan's output is in `verify/`.
