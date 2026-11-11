# Adversarial review of the A1 build spec (2026-11-11)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`): the independent review of `2026-11-11-A1-FRONTIER-PROBE-SPEC.md`, filed beside it; the spec's Review log says how each finding was applied.

Reviewed: `C:/Remote Projects/_ai_lab/s53/a1spec/2026-11-11-A1-FRONTIER-PROBE-SPEC.md`.
Read-only review by a fresh agent. Nothing was edited, committed, run live or launched. Code was read on `main` at
`10ceb4f7` (the main checkout is on `main`, clean), and on `origin/wip/ch6-ch7` (`18c3d51b`) and `origin/wip/ch6-bp1`
(`c5146e53`) with `git show`. The learner clone was read at `da2fb96a`. The decomp was read at pin `731ad5b`.

**Verdict: READY WITH FIXES.** The citations are unusually accurate. Three design-level contradictions must be fixed
before a builder starts, because the tests as specified would pin each of them in place.

## What checked out (no error found)

- **The 12 G-start md5s** (`_livechain/graded-ch5/LC-*/L5/{end_state.ss1,world_last.jsonl}`) match the table, recomputed.
  Every `L5/row.json` reads `RAN`, `reached True`, map `[0, 3]`, with the stated frames. LC-T-6205 has
  `DEFEATED_RIVAL_RUSTBORO` 0, as stated.
- **The 6 C-start md5s and sizes** match `_ai_lab/MANIFEST.json` (C1's world is 91,544,456 bytes). The I1, D1 and D2
  `played_by` texts are as quoted.
- **The live_chain line citations hold:** PAIRS :155, FRAMES_BY_CHAPTER :163, WALL :164, STAGGER :166, WORLD_SIZE_KIND
  :176, PURITY_IDS :188, python_env_refused :276, chain_watchdog_seconds :388, legs_of :404 (the optional refusal at
  :419-420), proof_holds :468, NEW_MEMORY :1198, stream_world_tail :1233, leg_reached :1338, launch_died :1350,
  custody_problems :1394, guard_decision :1481, newest_world :1491, untrusted_text :2023, finish_leg :2102, run_chain
  :2169, salvage_leg :2271, salvage_chain :2292, child_env :2406, schedule :2471 and end_sweep :2711.
- **The other code citations hold:** the live_step5 lines (Arm :177, play_env :399, run_arm :439 with ensure_profile and
  no template at :441, the kill at :477, check_after_is_this_run :524, tells :702, is_battle :739, battle_records :744),
  the launcher lines (:95, :102, :107, :109, :111, :119, :158, :270-276, :760), the options ENV_* lines, PERSONALITIES
  :60, the memory.py lines (and rides at :892 on the branch), MapRSE (0,10) and (17,0), and the learner's :574-603,
  :2123, :1875-1897 and config values.
- **live_chain.py and test_live_chain.py are absent** on both branches, and the merge base is `979754bf`.
  `check_anchors.py` exists only on the branch. The branches change none of `live_step5.py`, `launcher.py` or
  `play_harness.py`, so those citations survive the merge. `run_units.py` gets +4 lines on ch6-ch7 and +6 on bp1.
- **The measured numbers hold:**
  - BP-1 round 2's B2 rows are 612,596 f / 1,754.4 s, 654,457 / 1,847.6 and 666,141 / 1,675.7, which is 349-398 f/s.
  - control2-C-C2L4-6393's world.jsonl is 496,665,474 bytes.
  - The live-chain cost rows sum to 111.807 Mtok over 10 workflows.
  - `git archive main ai_player ':(exclude)ai_player/evidence'` is 25,323,520 bytes, and maps.json holds 518 maps.
  - `git log dc0a4e69..main -- ai_player` (evidence and ledger excluded) is empty.
- **Seeds:** 6601-6603, 6611-6646 and the D13 band are named by no entry in any of the 30 `ai_player/gates/ledger.json`
  files in every local and remote ref (git show). This confirms the spec's 188-ledger check, but only for committed
  refs. BP-1 round 3 and P11-1 have not committed their entries yet.
- **The arithmetic holds:**
  - legs: 9×7 + 27×2 + 3 = 120;
  - singles cap: 32 − 4 − 16 = 12, then // 4 × 4 = 12;
  - T26: 16 − 10 = 6;
  - 1.2M / 349 = 3,438 s;
  - WP1: about 19.35 job-hours / 8 = 2.4 h, plus the tail.
- **The spec's open decomp check, now closed:** `VAR_BIRCH_LAB_STATE` 3 is set in the lab right after the starter
  (`LittlerootTown_ProfessorBirchsLab/scripts.inc:132-134`). The NO branch loops until YES (:138-141), so `ch1_lab`
  always holds before the ROUTE 103 trip, and P1(a)'s next unmet milestone `ch1_rival_route103` is right.
  `FLAG_MR_BRINEY_SAILING_INTRO` is set only inside the house (`Route104_MrBrineysHouse/scripts.inc:25,32`), so P2's
  predicted `ch6_briney_house` is right.

## Findings

### MAJOR

**F1. A missing verdict is classed INFRA.** This contradicts D14 and Phase A test 1, and it hides a hung AI.
- Spec 3.5, INFRA row: "no verdict file and not CUT-WORLD (for example `run_arm`'s own kill past wall + 300 s ...)".
  T2's CONTROL: "exit 124 with no verdict gives INFRA".
- **Design D14** (`2026-10-30-AI-TRAINER-DESIGN.md`:164): "REFUSED: launcher exit 7/2, or a missing verdict".
- **Phase A test 1** (:266): "a NOT CLEAN or missing verdict counts toward the stop".
- **The launcher's own reading:**
  - `launcher.py` :264 and :499-502 judge a hard kill with no verdict as "a stuck run".
  - `soft_deadline_margin` :714-719 explains that the soft deadline exists so that a run that merely ran out of time
    ends WITH its verdict. "The HARD kill stays as the backstop for a run that is truly stuck."
- **The table contradicts itself.** NOT CLEAN lists "exit 8 (NO_VERDICT_EXIT)". But exit 8 with no verdict file matches
  the INFRA row first ("first match wins"), so that part of the NOT CLEAN row can never apply.
- **Section 1.3 does not declare it.** It says D14 "Holds, refined", and lists only CUT-WORLD, CLEAN-INVOLUNTARY and the
  gate timeout.
- **Effect:** a brain stuck in a loop (exit 124, no verdict) never appears in the blocker list, never counts toward the
  AI-only stop, and drops out of the denominator.
- **Fix:**
  - A missing verdict with an exit other than the gate timeout or the probe's own CUT-WORLD kill counts toward the stop
    (REFUSED, or a new class HUNG that counts and is listed).
  - Only `run_arm`'s driver kill (`run.driver_killed`) and `launch_died` stay INFRA.
  - Change T2's CONTROL to match, and declare the change in 1.3 and `06`.

**F2. `schedule`'s `may_start` drops a refused job for good.** So the singles cap and the regression rule would silently
remove WP1 jobs.
- The spec: "Scheduler ... `live_chain.schedule` :2471-2499 | reused; A1's `may_start` adds the singles cap and the
  deadline", and rules 2 and 3 in 2.6.
- **In the code**, `schedule` does: `ok, why = may_start(job); if not ok: not_started.append((job, why)); continue`. The
  job is never retried.
  - That is right for the deadline and for the 5 GB `--out` cap.
  - It is wrong for a temporary condition: other singles above the cap, or a `run_regression.py` that is running.
- **T26 cannot see it.** "With 10 other singles and P = 8: at most 6 own launches at once" also passes when jobs 7-8 are
  dropped.
- **Fix:** split `may_start` into DROP (the deadline, the out cap, abort or stop) and WAIT (singles, regression). A WAIT
  keeps the job pending and re-checks it next tick. This needs a wrapper around `schedule`, or A1's own loop.
- **Add to T26:** with the 10 others falling to 0 mid-run, all 8 jobs eventually start, and `not_started` is empty.

**F3. The `--trainer` path rules refuse Phase A's own layout.** Job 2, "Nothing is built twice", fails as written.
- **The stage.**
  - The spec (3.3): "Phase A points `--stage` at the AI code checkout instead (D1)." 1.1: "runs `frontier_probe.py run
    --trainer` ... from the AI's own code checkout".
  - But 3.10 requires "every stage [is] outside every git work tree, OR inside one and git-ignored there ... with no
    tracked file under them".
  - D1's checkout, `C:/Remote Projects/pokebot-ai-code`, is "a plain clone of origin". It is a work-tree root with tracked
    files, so T11 refuses it.
- **The `--out` folder.**
  - 3.10 says "The learner's `ai-agent/data` is such a place."
  - But 3.14 says "Refuse any path under a folder named `pokebot-learner` (live_chain R8)". The learner's data is under
    `C:/Remote Projects/pokebot-learner/ai-agent/data` (CLAUDE.md: "The learner's data lives THERE"), as does D11's AI
    store.
- **Fix:** define the Phase A contract now.
  - Either allow a stage that is a whole work tree whose tracked files the run never writes, checked by `git status
    --porcelain` before and after (Phase A test 8 is "neither checkout ever gets a tracked change").
  - Or have the learner pass a `--out` outside the clone and copy the records itself.
  - Make 3.10, 3.14 and T11 agree.

### MINOR

**F4. `guard_decision` takes no thresholds.**
- The spec: "a newest world.jsonl over 1,000,000,000 bytes: kill that launch (`guard_decision` with these thresholds)".
- `live_chain.guard_decision(world_bytes, free)` (:1481-1488) reads the module constants `GUARD_WORLD_BYTES =
  1_500_000_000` and `GUARD_FREE_GB = 30.0` (:178-179).
- "Reused" with 1 GB and 40 GB therefore means rebinding live_chain's globals or rewriting the function. Then 4.2's
  mutant "`>` becomes `>=` at 1 GB" lives in live_chain.py, which A1 may not edit.
- **Fix:** A1 writes its own 5-line decision with its own constants. Name it, and test it against `guard_decision`'s
  shape.

**F5. T14 cannot catch the mutant it is named for.** The spec: "`>` becomes `>=` at 1 GB".
- **T14's values:** FAULT 1,000,000,001 (killed), CONTROL 999,999,999 (not killed).
- **Under the mutant:** 1,000,000,001 >= 1e9 is still killed, and 999,999,999 is still spared. Both arms give the same
  result, so the mutant survives.
- The same holds for 40.1 against the 40 GB abort and 4.9 against the 5 GB out cap. Only 45.0 is a boundary value.
- **Fix:** add exactly 1,000,000,000 (no kill), 40.0 (no abort, since the rule is "under") and 5,000,000,000 (whichever
  side the rule names).

**F6. `play: stopped:` is the brain's budget end, but the spec classes it as an AI choice.**
- The spec: "CLEAN-CHOSEN | CLEAN, fresh, exit 0 (the AI ended it: `done:`, `stuck:` or `stopped:`)" and "CLEAN-BUDGET
  | ... `frame-budget` (exit 4) or `wall-clock` (124)".
- **In the code:**
  - `mode.py:1368` returns "stopped: not finished within {frames} frames", which exits 0.
  - The launcher calls that BUDGET when the host's count reached the budget (`launcher.py` :261-266, `_ran_out` :449).
  - The launcher puts the host's `frame-budget` in `_INVOLUNTARY` (:271).
- **Effect:** almost every budget end lands in CLEAN-CHOSEN, and CLEAN-BUDGET stays nearly empty. The key's class field
  then mislabels them.
- **P1(a) is also incoherent.** It reads "class CLEAN-CHOSEN (or CLEAN-BUDGET); reason beginning `play: stuck:`". A
  budget end's reason is never `play: stuck:`.
- **Fix:** class `stopped:` with real_frames >= frames as CLEAN-BUDGET (the launcher's `_ran_out` rule), and reword
  P1(a).

**F7. G-3 forbids two of the sources the spec names.**
- The spec adds `frontier_probe` to `GRADERS` (`check_grader_imports.py` :32). It also names `personality.PERSONALITIES`
  (2.2) and `TileFact.compact` (3.9) as sources.
- G-3's `ALLOW` (:37) admits only `host.launcher` and `options.ENV_*`. An import of `ai_player.personality` or
  `ai_player.world.memory` by frontier_probe fails the gate.
- **Fix:** say "hard-code the 3×3 pairs, like `live_chain.PAIRS`, and the 4 tile fields, with a test pinning them
  against the AI's" (a test may import them).

**F8. "Not changed: live_chain.py ... and its registered import-closure hash" is false.**
- `check_grader_imports.py` is one of live_chain's `GRADER_GATES` (:292). It is hashed into
  `registered_numbers()["grader_files"]` (:1170).
- Adding `frontier_probe` to its `GRADERS` therefore changes every future live_chain registration's numbers sha. It is
  harmless for #101, whose numbers are recorded, but it is a new registration.
- **Fix:** say so, or do not add it to `GRADERS` and give `frontier_probe` its own scan call.

**F9. A headline overclaims.**
- 0: "6 of those 9 pairs have never been played". The writer's summary repeats it.
- `rate_step5.py:671` cycles all 9 pairs: `PERSONALITIES[index % 3], STARTERS[(index + index // 3) % 3]`.
- 2.2 scopes it correctly ("The graded and development chains so far played only the diagonal").
- **Fix:** "never played as a New Game chain past chapter 2" (CLAUDE.md rule 2).

**F10. The source of the marks is mis-cited.**
- The spec: "On `main`, chapters 6-7's marks do not exist (`ai_player/eyes/view.py` `MILESTONE_FLAGS` :380 ends at
  chapter 5)".
- The truth's marks come from `play_harness.tracked()` (:82-95), which reads `knowledge/milestones.json`. view.py is the
  AI's eyes. The conclusion (marks come with the merge) still holds.

**F11. `salvage_chain` cannot be reused as is.**
- The spec: "A crashed chain's legs salvaged | `live_chain.salvage_leg`, `salvage_chain` | reused".
- `salvage_chain` reads `out/rows/<chain>.json` and `out/<chain>/current_leg.json` (live_chain's layout), and
  `schedule` needs `job["chain"]`. A1 writes `records.jsonl`.
- **Fix:** reuse `salvage_leg` only (as 3.13 already does), or write those two files too.

**F12. T27 contradicts a difference the spec chose, and it has no FAULT arm.**
- T27: "a New Game chain stops at the same leg as `live_chain.run_chain`". But 3.6 drops C3's 300 MB cap, so a leg with a
  world of 300 MB to 1 GB continues in A1 and stops in live_chain.
- T27's FAULT column is "-", contrary to "Each guard has a FAULT that must fire".
- **Fix:** exclude that input, or assert the known difference as the FAULT.

**F13. "No seed is ever launched twice" (3.13, T24) is wrong.**
- P1's two arms share seeds, P2 reuses its J-F jobs' seeds, and every leg of a chain uses one seed.
- **Fix:** key resume dedup on `run_id` / (arm, job, leg).

**F14. P2's wall has no offline test, and "every tile a wall" may not block a door.**
- MR. BRINEY's house is entered through a door warp on ROUTE104. Treating the house map's tiles as walls does not by
  itself stop a step onto the door.
- Only OLDALE gets the offline unit test ("the mutated planner finds no path into OLDALE").
- **Fix:** specify the same unit test for WALL-BRINEY (no path through the warp).

### NIT

**F15. `MapRSE((group, num)).name` imports `modules.map_data`.** That module pulls in `modules.context`, `modules.map`,
`modules.memory` and `modules.pokemon`. `rate_step5.map_keys` (:1827) already reads MapRSE as text, so `report` and the
offline tests stay framework-free.

**F16. The cost and time totals do not match their parts.**
- The cost parts sum to 18+5+8+3+2 = 36 and 28+10+15+6+4 = 63, not "about 40-65".
- 0 says "about 3-4 hours", while 2.8 says "about 3-3.5 h".

**F17. The stage size leaves out the C-start world copies.** "Stage: about 25 MB of code per arm" does not count the
C-start world copies of 91.5 + 13.6 + 58.1 MB, about 163 MB per stage.

**F18. The C starts' starters have no stated source.** `probe-C{1,2,3}.job.json` name the persona but no starter. The
table's TREECKO/TORCHIC/MUDKIP and the record's `job.starter` field need a stated source, for example the truth's party.

**F19. How the D13 band row is written is not specified.** For example, `ledger.begin("story", ..., "development",
2000000, 2999999, ..., note="AI trainer band")` then `finish`.

**F20. The experience allow-list filters unevenly.** It keeps `warps` and `connections` whole, though they carry
per-game counts and frames (warp entries hold `uses`, `first`, `last` and `by`). `bumped` is stripped of exactly those.
This is not hidden state, only uneven filtering.

**F21. One stated rule does not exist in the code.** "`ai_player` must not import `ai-agent` either" is not a rule today:
`live_step1.py:247-248,916` imports `ai-agent/scoring.py`.

## Rulings 35 and 40

No path found that gives the AI live hidden state or bot code.
- The experience extract is write-only in A1, and its party digest is screen data (`Grovyle:L19 53/53`).
- AI_PLAYER_WORLD is the same game's own memory, and the reads carried are the AI's own.
- Truth fields (marks, next unmet) stay in the harness records.
- The planted walls are test-side mutants in staged copies.

## Trying to begin the build

1. **The order.** `06` 2026-11-11 (DECISIONS :10077-10078) puts A1 after the chapter 6-7 merge. That is the lead's call,
   not a do-not-reopen ruling. BP-1 round 3 and P11-1 are running now (04:66). So only the offline core could start now,
   in its own worktree off `main` (`wip/a1-frontier`), and only if the lead revisits the order.
2. **Fix F1-F3 in the spec first.** These are lead decisions, with no user question.
3. **The files I would open:**
   - `ai_player/gates/live_chain.py`: `legs_of` :404, `proof_holds` :468, `leg_reached` :1338, `custody_problems`
     :1394, `continue_after` :1444, `guard_decision` :1481, `finish_leg` :2102, `run_chain` :2169, `salvage_leg` :2271,
     `schedule` :2471;
   - `ai_player/gates/test_live_chain.py`: the stub `run_leg` and the ImportTests;
   - `ai_player/gates/live_step5.py` :177-536;
   - `ai_player/host/launcher.py` :95-189, :262-276, :449-535, :700-760;
   - `ai_player/__main__.py` :83-135;
   - `ai_player/gates/ledger.py`;
   - `ai_player/gates/check_grader_imports.py`;
   - `_ai_lab/s53/ch6probe11/{build_stage11,make_arm11,arms11}.py`.
4. **The first three things I would do:**
   1. Write `test_frontier_probe.py` T1-T3 and T6-T8 against stubbed `live_step5.Run` objects, with F1 and F6 resolved.
   2. Write `frontier_probe.classify` / `next_unmet` / `blocker_key` / `continue_ok` until those pass.
   3. Port `stage` from build_stage11 and make_arm11 (git archive, junctions, donor `ai-fp-donor`, manifest).

**Could I start right now with no human input?** For the offline core, yes, technically. Every code input exists, the
citations check out, and the P1 discriminator is computed: WALL against REAL on the same seeds, next unmet
`ch1_rival_route103` by the decomp. But it should not start before F1-F3 are fixed, because T2, T11 and T26 would encode
the defects. It also conflicts with the binding order unless the lead revisits it.

For live work, no:
- P1 needs `frontier_probe` committed.
- WP1, P2 and the trainer smoke need the merge, and the merge waits for BP-1 round 3 and P11-1.
- The trainer smoke also needs the D13 band row.
- The L6/L7 budget check needs those rounds' final runs.
- The seeds must be checked free again at build time.
