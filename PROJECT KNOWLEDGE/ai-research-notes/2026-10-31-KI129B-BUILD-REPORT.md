> **Filed 2026-10-31** by the orchestrating session: the report of ROUND 2 of `2026-10-31-KI128-KI129-BUILD-SPEC.md` (KI-129 Part B, and the round-1 verifier's V1), built by the workflow `ki129b-build`: a builder in a worktree on `17ed7794`; an independent adversarial verifier (6 findings, 1 MAJOR: V2-1); a fixer who fixed V2-1 (an edge's "nothing new" window now slides). The three sections follow VERBATIM (subagents cannot write report files). Applied to `main` byte for byte (sha256) by the session's `apply_r2.py`: 18 files copied, 9 skipped on purpose (revert files and archives main's lane already rewrote, the worktree's own archives, and three tree zips nothing on main names); the verifier's two ledger entries were added as #80 and #81.
> **The headline:** on the old loop-prone code (818d3706) Part B cut the edge crossings from 171 and 198 to 11 and 14; on round 1's code and on the chapter 1-2 control it changed nothing (identical records: a determinism check). V2-1's fix is proven offline (two new FAULT tests fail on the pre-fix tree; 425 revert_step5 mutants PASS). DEVELOPMENT runs only; the graded held-out (the spec's section 5) is next.

## The builder's section

## KI-129 Part B and V1: both built and proven offline; the live A/B is development only

**Short version:** Part B and V1 are built. Every new guard fails on 17ed7794 and passes now, and all 9 new mutants are caught. Live, on the A0 code (818d3706) where the loop happens, Part B cut the PETALBURG|ROUTE104 crossings from 171 and 198 to 11 and 14. On round 1's code (PAW) it changed nothing: every record was identical on S1-S3 and on the six chapter 1-2 arms. Two of the registered predictions failed in part (P2b and P3, below); they are recorded, not retuned. Nothing here is graded, and each arm on each start is one trajectory.

### What was built
**Part B** (`brain/navigator.py`, `brain/explore.py`) follows spec section 4.1:
1. **Counting.** An edge crossing is counted under `src|edge:dir`, with the same 3-use and "nothing new since the 2nd use" stop as warps. It counts only when `ponged` is set, so the earlier brains behave as before.
2. **Both sides remembered.** `_remember_edge_pingpong` keeps both sides of the edge, each with `(stamp, frame)`.
3. **`edge_ponged`.** It checks that the stamp is unchanged and that fewer than `PONG_REST = NOVELTY_WINDOW` frames have passed.
4. **The drop.** `candidates.add` drops a ponged road, except a target of kind `route`.
5. **The fallback.** It is named, not changed.

**Grader change.** The live_step3 and rate_step3 STUCK graders now read `...ping-pong: the warp `. Their old prefix also matched the new edge text, so the answer to the spec's "confirm the regex does not match" is that it did match until this change.

**V1** (`gates/check_fairness.py`). In maps.json, the `warps[]` leaves (x, y, elevation, dest_map, dest_warp_id) and the `connections[]` leaves (dir, map, offset) are now each classified on their own. The containers are marked without a subtree.

`census_waivers.json` has 2 new waivers, each with its reason:
- **`candidates.add`:** the census matches the nested `add` by name, so its 40 "sites" are really `set.add` calls.
- **`summary`:** it only formats the counts at the end of an outcome's text.

### Offline (worktree)
| Check | Result |
|---|---|
| test_goals | 279 OK |
| test_world | 132 OK |
| test_kb2 | 122 OK (217.6 s) |
| test_host | 37 OK (47.6 s) |
| check_fairness | PASS (0 breaches) |
| call_census | 0 MISSING |

**Fault arm on 17ed7794** (`fault_arm.py`):
- KI129PartBTests: 7 failures, all at the setup check: the run ends "stuck: nothing new ... 3007 frames", so there is no edge stop. The controls B-C1 and B-C2 pass.
- B-C1 and B-C2 walks: the hashes over trail, transitions and records are identical to 17ed7794's.
- V1: `test_v1` fails with `'maps[].connections' != 'maps[].connections[].dir'`.
- V1 plants: keys planted under `warps[]` (`script`, `secret_door`) and under `connections[]` (`flag`) give no breach on 17ed7794 and each FAIL on the fix ("1 UNCLASSIFIED key paths").

**Corners measured and written into the tests:**
- **The rule's wording.** On seed 3, the first intent sees new tiles after its 2nd crossing, so that intent is not a ping-pong and makes 84 crossings in both codes. Its next intent stops at the third crossing. This is the warp rule's own wording.
- **B-F2's fixture.** With the crop on, a wander shows new border tiles. That counts as news, so the edge is rightly an option again. B-F2 therefore uses the CROP fault, where nothing new can be seen once both maps are walked.
- **B-F3's house half pins the named fallback; it does not test the drop.** Under the mutants it still passes, because `not_back_to_seen_all` already drops a way back to a map seen all of. The house=False half is the FAULT half.

### Mutants
| Driver | Result |
|---|---|
| revert_step5 (full) | 421 CAUGHT + 2 REDUNDANT of 423, PASS |
| revert_r1 | 555 + 1 of 556, PASS |
| revert_safety_gates | 23 of 23, PASS |

- **New Part B mutants G419-G427** are all CAUGHT: uses not counted, only the source side kept, `edge_ponged` blind, the `add()` guard deleted, route not exempt, the expiry deleted, the stamp not compared, the remember call deleted, and the novelty clause deleted.
- **V1 gate mutants:**
  - **Subtree again:** making `warps` or `connections` a subtree again fails `test_v1`, while check_fairness PASSes. That PASS is the hole V1 closes.
  - **Unclassified leaf:** leaving `dest_warp_id` unclassified fails both.

### Live A/B (spec section 4.4)
All runs are DEVELOPMENT. They used one stage built with round 1's method. The arms were: none = 818d3706, B = 818d3706 + Part B (patch applied cleanly), Bstop = B without the honour, PAW = 17ed7794, PAWB = 17ed7794 + Part B.

Before the runs, I ran KI129PartBTests against each arm's code: B and PAWB 7/7; Bstop fails exactly the three honour tests; PAW and none fail all 7.

The starts were re-derived read-only from the A0 folders, and their sha256 equal round 1's. Predictions were written before each batch, and each sha256 is in the ledger. Every launch was purity CLEAN, and every world.jsonl was summarised and then deleted.

**partb** (ledger #77; seeds S1 5914, S2 5915, S3 5916; 10,000 frames). D2 counts crossings of the start's edge, D2w is the most crossings in any 3,000-frame window, and E3 is the most crossings of one edge within one intent.

| Arm | S1: D2 / D2w / E3 / stops | S3: D2 / D2w / E3 / stops |
|---|---|---|
| none | 171 / 65 / 62 / 0 | 198 / 64 / 63 / 0 |
| B | 11 / 6 / 5 / 2 | 14 / 8 / 5 / 2 |
| Bstop | 22 / 17 / 5 / 3 | 131 / 42 / 5 / 25 |

- **PAWB vs PAW on S1-S3:** 0 edge stops. Decide records are identical (28, 17 and 9), and so are all records (540, 564 and 488, 0 differing). This is one trajectory replayed, a determinism check.
- **B vs Bstop:** the first differing decision is the drop itself.
  - **S1:** at f490928, B goes into PETALBURG_CITY_HOUSE1 while Bstop takes the road back to ROUTE104.
  - **S3:** at f618855, B takes "back (11,39) ... PETALBURG_WOODS" (F1's fallback) while Bstop takes the road back to PETALBURG.

**Prediction verdicts:**
- **Held:** P0, P1, P2a, P2c, P2d (as decisions: B S3 chose the woods back 3 times but never arrived within 10,000 frames) and P4.
- **P2b failed in part.** "D2 ≤ 1/5 of none" held. "D2w ≤ 5" failed: 6 on S1 and 8 on S3.
  - On S3, the go goal's lead from PETALBURG is "travel to ROUTE104", and its `route` target is exempt from the drop (F6), so it crossed straight back after each stop (f618641 → f618763 and f625112 → f625215).
  - On S1, the walk returned by a route crossing after PONG_REST and then started a new ping-pong, which stopped after 5 crossings.
- **P3 failed in part.** It held on S3 (131 ≥ 66, 25 stops) and failed on S1 (22 < 57). B and Bstop on S1 are the same trajectory until f490874. The first stop sent both into a 6,600-frame catch roam on ROUTE102, so on S1 the stop, not the drop, accounts for most of the reduction.

**Chapter 1-2 control** (ledger #78; PAW vs PAWB on the six r1base arms; seeds 5960-5965):
- The decide records are identical on all 6 arms (145, 266, 202, 190, 110 and 223).
- 0 records differ, and the marks, frames and final maps are the same.
- There were 0 edge stops.
- The most crossings of one edge in one intent was 1 in every run, so the control shows Part B is inert on chapter 1-2 play; it does not exercise the rule.

### Clean-up
- The stage was deleted with its junctions unlinked first.
- The main sandbox's linked folders kept the same file counts (4391, 40, 43, 2), and 0 new main-sandbox paths appeared after 15:19.
- C: had 67 GB free.

### Evidence
These files are in `ai_player/evidence/`:
- `2026-10-31-ki129b-offline.txt`
- `2026-10-31-ki129b-smoke.txt`
- `2026-10-31-ki129b-partb.txt`
- `2026-10-31-ki129b-control.txt`
- the regenerated `2026-10-31-step52-REVERT.txt` and `2026-10-31-r1-REVERT.txt`, both on digest 4e0510336ea695b9

All the scripts are in the scratchpad's `s53/fix2/scripts/`.

### Decision for you
An explore goal that ends in an edge ping-pong now ends "not done", the same as a warp ping-pong does. Before Part B it ended "stuck: nothing new", which counted as done. `goal_yield`'s productivity rule already overrides "done" for curiosity goals, so the effect is small, but it is a change.

## The verifier's section

## Verifier report: KI-129 Part B + V1 (worktree wf_63863050-725-1, HEAD 17ed7794, digest 4e0510336ea695b9)

**Verdict:** Part B and V1 hold up offline and live against the spec. I could not refute any of the builder's numbers.

There are two gaps worth acting on before the held-out round:
- **V2-1 (MAJOR):** the stop inherits the warp rule's "nothing new since the 2nd use". If anything new is seen after an edge's second same-side crossing, that edge can loop until the novelty window ends. The builder's own test asserts 84 crossings in one intent with Part B on. This conflicts with section 5's graded bar "no same-edge alternation over 5 within any intent".
- **V2-2 (MINOR):** V1 closed the cited plant, but not the class. A key planted below a leaf still passes RULE B.

### Environment
- Read only on the worktree: the provenance digest is 4e0510336ea695b9 and the `git status` md5 is 36fec2b0, both before and after my work.
- My copies are `s53/fix2/verify/new` (the worktree) and `verify/base`, which is 17ed7794 from MY `git archive`. Supporting folders, plus ai-agent/knowledge.py and map_data.py, were copied in.
- Settings: PYTHONUTF8=1, AI_PLAYER_TEST_SUPPORT_ROOT set to the main checkout, POKEBOT_DECOMP set to the pinned clone.
- Scripts are in `s53/fix2/vscripts/`.

### 1. Diff against the spec and the rulings
- **Section 4.1 steps 1-5:** all implemented as specified.
  - Edge counting is gated on `ponged is not None`. B-C2 needs that gate, and my mutant VM1 (gate removed) fails B-C2.
  - Both sides are kept as (stamp, frame).
  - `edge_ponged` checks the stamp and PONG_REST = NOVELTY_WINDOW.
  - The drop happens in `add()`, with routes exempt and a getattr fallback for stub navigators.
  - The fallback is named and left unchanged.
- **Rulings 35/40 and D1:** this is AI-player navigator code. It uses only the AI's own crossings, memory and novelty, and existing constants. There is no place, no route script and no hidden state. Compliant.
- **The grader regex the spec said to confirm:** it DID match the new text, so the builder narrowed `live_step3` grade_STUCK and `rate_step3` STUCK to `'explore: stuck: ping-pong: the warp '`. A repo-wide grep finds no other consumer.

### 2. Offline (my copy)
| Command | Result |
|---|---|
| test_goals | Ran 279 tests in 6.880s OK |
| test_world | Ran 132 tests in 44.472s OK |
| test_kb2 | Ran 122 tests in 220.510s OK |
| test_host | Ran 37 tests in 46.074s OK |
| check_fairness | PERSON-FAIR DATA DOOR: PASS (0 breaches) |
| call_census (worktree, read only) | 8 functions or added calls, 67 sites, 0 MISSING, PASS |
| regression_due (worktree, read only) | 6 of 6 suites due (2 of them only unproven) |

**FAULT tree (17ed7794 + the new test files):** `KI129PartBTests` + `VerifierRound52Tests` gave `FAILED (failures=7)`.
- B-F1 (seeds 1 and 2), B-F1 corner, B-F2, B-F3 (house True and False) and B-C3 fail.
- Each fails at the setup: `stuck: nothing new ... for 3007 frames` (the corner: 3000 frames, at f3650).
- B-C1 and B-C2 pass.
- test_v1 on base fails with `'maps[].connections' != 'maps[].connections[].dir'`.

**Plants (plants.py):**
- On base, warps[].script, warps[].secret_door and connections[].flag all PASS (no breach).
- On the fix, each FAILs with '1 UNCLASSIFIED key paths [...]'.
- A key planted below a leaf PASSes on BOTH trees (V2-2): `warps[].dest_map.script`, `connections[].offset.flag`, `trainers[].x.script`.

### 3. Mutants
- **G0 + G419-G427 + my own (vmutants.py):** G0 279 tests, failing none. G419-G427 are each CAUGHT with all their predicted tests failing.
- **My own mutants:**

| Mutant | Result |
|---|---|
| VM1: counting for the earlier brains | caught by B-C2 |
| VM2: far side kept by the same side | caught by B-F1 and 4 more |
| VM3: `<=` PONG_REST | caught by B-F2 |
| VM4: edge_to = source | caught by B-F1 and 4 more |
| VM5: edge_ponged looks up the opposite side | caught by B-F2, B-F3, B-C3 |
| VM8: 2 uses for edges | caught by B-C1, B-F1 seed 1, the corner |
| VM6: `exit_tile is None` clause deleted | equivalent, as I predicted |
| VM7: stop frame = last crossing | equivalent: the stop can only fire at the 3rd crossing (V2-1) |

- **revert_step5 full (--workers 6):** `421 mutants CAUGHT as predicted, 2 REDUNDANT ALONE as predicted, of 423`, FROZEN TREE PASS, OVERALL: PASS.
- **revert_r1 (--workers 8):** `555 ... 1 REDUNDANT ... of 556`, OVERALL: PASS (16:42 to 17:07).
- **revert_safety_gates (--workers 6):** `23 mutants CAUGHT as predicted, of 23`.
  - OVERALL: FAIL in my copy, only because the S0 control fails `LessonsTests.test_the_real_lessons_list_passes`.
  - That test passes when run directly in verify/new (`Ran 1 test ... OK`).
  - This is the same environment symptom round 1's verifier saw. The builder's in-worktree run passed.
  - Not a finding, but its cause is unexplained.

### 4. Live (DEVELOPMENT, never graded)
**Setup**
- **Starts:** re-derived by me with a tail-read (vstarts.py). The sha256 equals the builder's for all 6 starts.
- **Stage:** `s53/fix2/verify-stage`. Arm digests: none 16a130f4, B ac348b0c, Bstop e6b40930, PAW fa2edfb6, PAWB 4fb6bbc9, all equal to the builder's. My B arm used my own difflib patch, and every hunk applied.
- **Predictions:** written before each batch; their sha256 are in the ledger.
- **Every launch:** purity CLEAN, 10,000 or 330,000 frames, the AI exited by itself, world.jsonl deleted after its summary.

**vpartb (ledger #79, seeds S1 5918, S2 5919, S3 5920)**

| Arm | S1 D2 / D2w / E3 / stops | S2 | S3 |
|---|---|---|---|
| none | 57 / 57 / 57 / 0 | 44 / 44 / 44 / 0 | 202 / 65 / 64 / 0 |
| B | 11 / 6 / 5 / 2 | 5 / 5 / 5 / 1 | 18 / 6 / 5 / 3 |
| Bstop | 12 / 7 / 5 / 2 | 33 / 33 / 5 / 6 | 132 / 43 / 5 / 26 |

- Q1 failed on S2 (none's D2 was 44 against the predicted >= 50). It is still non-vacuous (>= 15).
- Q2 to Q5 held:
  - B: E3 <= 5, at least 1 stop, D2 <= 1/3 of none's, D2w <= 10.
  - Bstop beat B on 2 of 3 starts.
  - No intent had more than 5 crossings.
- **Replicates the builder:** on S1, B and Bstop are the same trajectory until decision #35 at f492070, so the STOP does the work there. The DROP is load-bearing on S2 (33 against 5) and S3 (132 against 18). S2 is new information: the builder did not run B on S2.
- **B S3:** the F1 fallback 'back (10,39) -> PETALBURG_WOODS' was chosen 4 times (618855, 621921, 624270, 627694), with no woods arrival in 10,000 frames. This is the base code without KI-128, matching the builder's 3.

**vcontrol2 (ledger #80):**
- PAW vs PAWB on CH2T (seed 5921, 85,134 frames) and CH1C (seed 5924, 130,260 frames).
- Decide records 86/86 and 208/208 identical. All records 2664 and 5278, 0 differing. Same marks and maps.
- 0 edge stops; E3 was 2 and 1.
- Part B is inert here: one trajectory replayed, a determinism check.

**Clean-up**
- The stage was deleted with 9 junctions unlinked first. The linked folders' counts are unchanged (modules 4391, plugins 40, mgba 43, roms 2) before and after each batch and the delete.
- 0 world.jsonl files are left under verify; verify/live is 24 MB.
- C: had 64 GB free at the first batch start and 65 GB at the end.
- The builder's stage is also gone.

### 5. Evidence headlines against bodies
- **ki129b-partb:** headline 'NO PASS'. The body reports P2b and P3 as FAILED IN PART, with their mechanisms read at the records. Consistent.
- **ki129b-control:** 'NO PASS: HELD', with a non-vacuity note that the counter never neared firing. Consistent.
- **ki129b-offline:** its numbers match my reruns. Its 'MEASURED CORNERS' section openly documents the 84-crossing intent, but neither the headline nor the spec's section 5 bar carries that caveat (V2-1).
- **step52-REVERT and r1-REVERT:** the code digest is 4e0510336ea695b9, equal to the worktree's current provenance. The verdict lines are 421+2/423 and 555+1/556, OVERALL PASS.
- **Leave out of the commit:** trees/a3729c1b749c1775.zip, which nothing references.

### Findings
- **V2-1 MAJOR:** the edge stop cannot fire after news has followed the 2nd same-side crossing (an 84-crossing intent, asserted by the test). This conflicts with section 5's graded bound.
- **V2-2 MINOR:** V1's residual: leaf entries are subtree True.
- **V2-3 MINOR:** the explore-goal done/not-done change has never been exercised.
- **V2-4 NIT:** the '*' census waiver also covers the 7 real add() sites, permanently.
- **V2-5 NIT:** memory is keyed by side, which affects ROUTE111 left and ROUTE124 right.
- **V2-6 NIT:** the builder's development seeds 5960-5965 overlap the spec's example held-out seeds.

## The fixer's section

## V2-1 (MAJOR): an edge ping-pong could run to the novelty window: FIXED

**The finding was correct.** In `navigator.py run()`, warps and edges shared one stop test, `len(frames) >= PINGPONG_USES and novelty.last <= frames[1]`. `frames[1]` is fixed and `novelty.last` only grows. So once anything new was seen after an edge's 2nd same-side crossing, that edge could never stop in that intent.

I measured it on the pre-fix tree:
- `bf1_probe.py`, seed 3: "stuck: nothing new ... the last at f649", **84 crossings**.
- A town and a route wider than the view (`v21/probe.py`), crossed at x 3, 12, 21, 30, 37, then 12 more times at x 37: new tiles until crossing 10 (f1157), then nothing new. Result: **17 crossings**, 8 of them at or after the last news, ending "stuck: nothing left to try". 17ed7794 gives the same.

**The fix (edges only; warps unchanged).** An edge now stops when `novelty.last <= frames[-2]`: nothing new since the same-side crossing before the last. A sliding window replaces the fixed one. The message now reads "... since its crossing before the last".
- With strict alternation, a back-and-forth with nothing new between is now at most 5 crossings after the last news.
- Seed 3 stops after 7 crossings in all, its window starting at the news (f649).
- The wide walk stops at crossing 12, with 3 crossings at or after the last news and both sides kept.
- Deleting the edge branch's `continue` is an equivalent mutant, because frames[1] <= frames[-2].

**The section 5 bar.** "No same-edge alternation over 5 within any intent" cannot hold literally under any rule that keeps B-C1 (crossings with news between them are no ping-pong): seed 3 crosses 7 times in one intent. Before registration, I re-worded the bar in the worktree's spec as a run of crossings with nothing new between them. The held-out build must name how that is read from the logs. **This needs the orchestrator's acceptance.**

### Offline (test_goals `KI129PartBTests`, now 9 tests)
- **Changed on purpose:** the seed-3 corner test. It asserted 84 crossings; it now asserts the edge stop, at most 7 crossings, and the window at f649.
- **New FAULT test (the verifier's case):** news arrives after the 3rd same-side crossing, then the walk must stop within 5 crossings of the last news, with planned crossings left over.
  - It fails on the pre-fix tree ("stuck: nothing left to try ... 17 decisions") and on 17ed7794.
- **New CONTROL:** 5 crossings with news between them, then walks on the same map seeing nothing new. Result: no stop, and identical to `ponged` None.
- **Fault arms:**
  - Pre-fix tree: FAILED (failures=2), exactly the two FAULT tests; every control passes.
  - 17ed7794: FAILED (failures=8).
  - The fix: OK.

### Mutants (revert_step5)
- Full run: 423 CAUGHT and 2 REDUNDANT as predicted, of 425; OVERALL PASS.
  - G427, re-anchored on the edge line: caught.
  - G428 (frames[1] again): caught by both FAULT tests.
  - G429 (frames[-1], the verifier's VM7): caught by B-C1, B-C1b and the FAULT test.
- VM7 on the pre-fix tree was also caught (failures=3), so I could not reproduce "VM7 survives".
- revert_r1: 555 CAUGHT and 1 REDUNDANT, of 556; PASS. It took about 30 minutes, over the 20-minute guide.
- revert_safety_gates: 23 of 23; PASS.

### Live A/B (development, ledger #79, seeds 5966-5971, prediction sha256 42d8b9fe... registered first)
Bpre vs Bfix ran on 818d3706 with 4 runs each (S1 and S3, 2 seeds each). PAWBpre vs PAWBfix ran on 17ed7794 with 2 runs each. All runs were 10,000 frames.
- 12 of 12 purity CLEAN; every world.jsonl was summarised and then deleted.
- Every B run had E3 5, 1 edge stop and over5 0.
- Decide records were identical in all 6 pairs. The only differing records were the stop's text, at the same frames.
- PAWB: 0 edge stops; all records identical.

**The V2-1 condition did not arise live** (my registered prior). So the live arm shows only that nothing else changed. It is not a demonstration of the fix, and identical records are one trajectory replayed, not a replication. The stage was deleted, and the main sandbox's linked folders are intact (4391/40/43/2 files).

### Gates
- test_goals 281 OK, test_world 132 OK, test_host 37 OK, test_kb2 122 OK.
- check_fairness PASS (0 breaches); call_census PASS; lint_docs PASS; audit_doc_consistency PASS.
- regression_due: 6 of 6 due. The three revert drivers above pass. run_regression --full, rate_step5 and live_step5 were not run.

### For the orchestrator
- **Ledger collision:** the verifier's #79/#80 (seeds 5918-5924) are not in the worktree's ledger, whose new entry is also #79. The free-seed list was stale: 5918-5921 and 5960-5965 are taken.
- **Do not stage** `trees/17e92a07653a943c.zip` (an intermediate tree from the filtered mutant run).
- **Evidence:** `ai_player/evidence/2026-10-31-ki129b-v21.txt`.
