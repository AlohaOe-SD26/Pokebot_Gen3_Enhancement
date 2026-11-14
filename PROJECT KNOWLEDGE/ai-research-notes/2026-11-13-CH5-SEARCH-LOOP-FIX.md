# ⚠ NOTE, not a source of truth: the chapter 5 search loop, its diagnosis and its fix (E + K1). Fixed on its ONE decisive fixture (one trajectory per arm; each change alone reached there, neither shown necessary); the chapter 1-5 miss RATE is unmeasured.

2026-11-13, a lab notes agent (NOTE5; fixed after its fact check by NOTE5-FIX and after its delta re-check by
NOTE5-FIX2), from the lab record (deleted after the merge). A NOTE per `00-READ-THIS-FIRST.md`: 05's KI for this loop
points here (ADD G3); 01-05, 06 and 07 win on any contradiction. Nothing was re-measured; every number is quoted from the
file named beside it.

**Tags:** MEASURED (a run's files, or the real code replayed offline), READ (code or data), INFERRED (reasoned, not run).
**One trajectory** = one live run; an identical rerun is a determinism check, never a replication. **Names:** S3t =
`c25d2c40` (the merged tree E0 ran on); main = `934ddb7f`; `<E0c>` = `a90c8e8f`; `<FX>` = `3caf9c47`; `<E0c2>` =
`19e9700c`; `<S3t2>` = `fa9f073d`; WT = the merge worktree (`wip/ch67-merge`); "L4 start" = a chain's save after leg 4
(leg 5 runs to `ch5_rival_meet`); X = count of "MAP ROUTE104 -> PETALBURG_WOODS" lines in a leg's log; FA2 = S3t minus
the approach fix and `road_walk`; FA3 = FA2 minus the navigator road branch [DIAG 4]; S1, S2, S3 = the shadow probe's
three suspects, in section 4's order [SHA 1].

**Sources**, under `C:/Remote Projects/_ai_lab/s53/`: ADD `mergeplan/DOCS-ADDENDUM.md` (F = §1, G = §2); DIAG
`e0diag/DIAGNOSIS.md`; REF `e0diag/REFUTE.md`; SHA `e0diag/shadow/SHADOW.md`; REC `e0diag/shadow/RECOUNT.md`; MECH
`e0diag/fixplan/MECHANISM.md`; KNOW `e0diag/fixplan/KNOWLEDGE.md`; FIX `fix5/wf_result_w12ilk0ve.json` (verify =
VERIFY1); RB5 `fix5/STATE.md`; FXU `fix5/wf_result_wn1fpdzxq.json` (verify = VERIFY2); MP `mergeplan/STATE.md`. Section
0 = a file's Verdict or Headline.

## 1. Headline (with its caveat)

- **Found (MEASURED):** two weaknesses of rules main already had (that `main` had them is READ, not measured live): a cut tree, rock or item ball was a wall only while on
  screen [MECH 0], and a told walk to a map not found yet had no direction (`lead_toward` gave None for RUSTURF_TUNNEL)
  [KNOW 0].
- **Fixed on its decisive fixture (T's L4 start; one trajectory per arm; rate unmeasured):** E (a standing thing seen
  this session stays a wall) and K1 (a seasoned player's entry-map lead): `9d2f3fc5` plus the test-only `3caf9c47`, now
  in WT [MP].
- **Proof, and its limit:** on the one start that discriminates (T's L4), the unfixed code did not finish in 600,000
  frames; the fixed code reached `ch5_rival_meet` in 198,539 [FIX]. One trajectory per arm. A reach alone attributes
  nothing on that start (unrelated single changes reach too); the action checks do (section 3).
- **E0 again on three new seeds** (E0-2, MEASURED): REACHED 3 of 3, "problems 0 -> GO" [MP]. Three trajectories, not a
  rate.
- **Not proven:** the miss RATE (C's and S's starts reach unfixed too); that either change is NECESSARY (each alone
  reached on T); E on dark maps where it would act; K1 live outside chapter 5.

## 2. The miss (MEASURED: the run verdicts)

`E0 VERDICT: NOT REACHED (1 of 3 reached ch5_rival_meet); legs ran 15, purity-clean 15; wall 41 min (cap 120); problems 5
-> STOP` (HEAD S3t; seeds 6481-6483; ledger entry #147; the checker: STOP_CONFIRMED) [MP].

| chain | leg 5 | X |
|---|---|---|
| LC-S-6481 (Story) | reached | 0 [REF A3] |
| LC-C-6482 (Catcher) | "play: stuck: no progress for 120153 frames", 455296 of 600000 frames [MP] | 37 [DIAG 4] |
| LC-T-6483 (Trainer) | "play: stopped: not finished within 600000 frames" [MP] | 59 [DIAG 4] |

Both misses looped in ROUTE104 <-> PETALBURG_WOODS warp ping-pongs, looking for RUSTURF_TUNNEL, a map not in the AI's
memory [ADD F1]; `grep RUSTURF` in both L4 memories finds nothing [REF A7]. C stalled at `ch5_rusturf_grunt`. T looped
there (59 crossings), beat the grunt at f1257345 and ran out of its 600,000 frames before `ch5_rival_meet` [DIAG 4].

## 3. Non-determinism, and the decisive fixture

MEASURED: the same code from the same save, with fresh profiles, splits by one frame at warps onto outdoor maps ("busy
Nf") [REF A6].

| pair | identical moves | split |
|---|---|---|
| E0 T / S3t-T | 26009 | f1203126 "busy 18f" / f1203127 "busy 19f" |
| E0 C / S3t-C | 2777 | f557997 "busy 18f" / f557998 "busy 19f", leaving RUSTBORO's POKEMON CENTER |
| FA2-T r1 / r2 | 15581 | f1044304 / f1044303; ended at 62 / 57 crossings [REF B4] |

- Cause NOT proven. Suspect (INFERRED): the cartridge clock reads the host's time (`modules/libmgba.py` sets no clock
  override, READ) [DIAG 2]; no arm pinned the clock [REF C]. So a run from a save is one trajectory, a sample [DIAG 2].
- This refutes one REASON in 06 2026-10-31 (USER RULING 55, part 2: "so runs replay and can be checked"). The ruling
  stands on its other reasons. 06's entry "E0's STOP and the fix-forward" (ADD G4) carries the correction.
- **The decisive fixture: T's L4 start** (LC-T-6483 [DIAG 1]). The unfixed code replays E0's loop exactly to f1203126,
  all 59 crossings included [DIAG 2].
- **A reach alone does not attribute on T's start:** unrelated single changes reach too (S3t minus the approach fix: 1
  crossing; S3t minus the crossing fix: 3) [DIAG Verdict]. The action checks do (MEASURED [FIX build; RB5]): 0
  "unreachable" events at a woods frontier after both woods trees had been on screen (unfixed S3t-T: 80); 2 ROUTE116
  right steps against the unfixed 657; the first changed decision is E's, at f738135.
- **Its start files are KEPT** (copied from `mergeplan/e0/runs/E0-6481/LC-T-6483/L4/`, which goes with the lab) in
  `C:/Remote Projects/_ai_lab/keep/2026-11-13-ch5loop-T-L4/`, with a README.txt:
  - `end_state.ss1`, sha256 `90ae68112ff71a509fc7c5d8e374d1096a809931122443460b36494745f78cdb` (the emulator state);
  - `world_last.jsonl`, sha256 `630cc6f159ef8afe4e20c2db88a8b580485e1485769d4fbf3ce81aa2b06a67ee` (the AI's memory).
  - Kept on the user's PC only, not in git. With them the A/B could be re-run on that PC (not tried). It needs a staged
    sandbox and `ai_player/gates/live_step5.py` `run_arm` (line 439 at `c25d2c40` and `9d2f3fc5`, both ancestors of
    `fa9f073d`), which sets up the profile and env. Past the first one-frame split, a re-run is a new sample. The lab
    driver that called `run_arm` (`replay_leg.py`) and the lab staging kit (`stage_diag.py`) are kept too (section 12).
    The git fixture `ch5loop_tcap.world.jsonl` is the loop memory, not this start.
- C's and S's starts do not discriminate: unfixed S3t-C reached (one trajectory, replayed; 198,944 frames) [DIAG
  Verdict, 2, 4]; E0's own S leg reached (f592164) [REF A3].

## 4. The shadow replay: on E0 T's one trajectory, main's ROAD rule (the only one of three suspects that could act) picks the same destination at 154 of 154 burst decisions

- **Why.** REF judged DIAG's "No merged change makes the AI choose the loop" NOT_ENOUGH_EVIDENCE: arm FA3 removed code
  that cannot run in the loop (B1); E0's leg 5 missed 2 of 3 against 0 of 9 for main's earlier leg-5 runs (p about 0.045,
  confounded) (B3).
- **The probe** (MEASURED [SHA 1-3; REC 1-3]), logging only: at each decision inside two windows around the bursts
  (f1020000-f1065000, f1145000-f1195000; 204 decisions) it also computed main's pick for three suspects: S1 `road_walk`'s
  road cost, S2 the `in_map_walls` road branch, S3 KI-134's `route_to` by parts. Its run equals E0 T's leg 5: "IDENTICAL
  (frame, action) over the first 29492" (all moves); 0 arm errors.
- **Result:** in the two bursts (f1032970-f1045390, 66 decisions; f1152982-f1169480, 88): the same destination at 154 of
  154, on both draw streams, never a road. The tile-level differences (7 seeded, 5 on the real draws) are the other door
  of the same woods entrance, "back (10, 29)" against "back (11, 29)" [SHA 0, 3; REC 0].
- **Caveats** [REC 0, 4]: only S1 with S2, one unit, could act in the bursts (S2 = S1 by construction; S3's "0 of 154"
  is vacuous). "Same destination" is not "same loop": the two doors are different warps and the ping-pong rule counts
  each warp; no run with main's road rule in the loop was made [SHA 4; REC 5].
- **Before the bursts**, on E0's path (run 1 equals E0 to f896019): 2 destination-level differences by SHA's count (1 by
  REC's coarser test). idx 191 (f869129): main's rule, computed in the shadow, picked "the road up ... RUSTBORO_CITY";
  the merged code's real pick was "back ... PETALBURG_WOODS". idx 138 (f844753), KI-134's `route_to`: the merged code's
  south door against main's north door (DIAG split 3). Neither sequel was run [SHA 3-4; REC 3]; no arm removed KI-134
  [REF B2].
- **Code** (READ, not measured live [MECH 3]): every rule that makes the loop (the marks, `see_objects`, `back()`,
  `lead_toward`) is main's too: the merge did not write them. The merge's own road rule (S1, `road_walk`) also runs
  there, and picked main's destination at 154 of 154 (above) [ADD F2].

## 5. The mechanism, measured and read

**Engine 1: a standing thing was a wall only on screen** (READ: `MapMemory.objects_now` held the last look only, and
`Navigator.walls` read it). A frontier behind an off-screen tree was offered, walked to, and refused once the tree showed;
the per-intent `excluded` mark reset at the next intent [MECH 0-2]. MEASURED (`unreachables.py` [MECH 0]):

| run | woods-frontier and (37, 22) "unreachable" events with a cut tree on screen | all "unreachable" events, tree on screen |
|---|---|---|
| E0 T leg 5 | 106 of 106 | 107 of 178 |
| E0 C leg 5 | 90 of 90 | 108 of 153 |
| S3t-T | 106 of 106 (24 at (37, 22), 82 woods) | |
| FA2-T / MAIN-T | 112 of 112 / 10 of 10 | |

Trees: PETALBURG_WOODS (19, 10), (19, 11); ROUTE104 (35, 22), before the item ball at (37, 22); ROUTE116 (32, 10) [MECH
0].

**Engine 2: every way out read "seen all of", so the nearest door won** (MEASURED [MECH 0, 2]): 34 of 41 "back" decisions
in the tight burst read "seen all of" on both sides; `back()` looks one map ahead only. On the T capture memory with the
loop's marks rebuilt, the real `travel_intent.choose` picks a woods door in 200 of 200 seeds. **No brake** (READ): the
per-intent marks reset; the kept ping-pong is read only by `lost_intent`.

**The ROUTE116 heal flip is Engine 1** [MECH 4.(d)]: the tree at (32, 10) is on screen with the player at x = 39 (the
window's edge), not at x = 40. Live S3t-T: 656 of 656 right steps from x = 39 saw it; 656 of 656 left steps from x = 40
did not (MAIN-T 314 of 314, 313 of 313). Offline (`flip_sim.py`, the real `_next_step`, 200 seeds): 200 of 200 flip with
the tree on screen only, 0 of 200 with it remembered; main the same.

**The missing direction** (READ, MEASURED [KNOW 0; MECH 2]): RUSTURF_TUNNEL is `MAP_TYPE_UNDERGROUND` with no town prefix,
so `lead_toward` gave None; its lead line occurs 0 times in all 11 leg-5 logs. `maps.json` has the answer (ROUTE116's
warps (47, 8) and (65, 10)), and the T memory already held (47, 8) as an unused exit.

**Finding F** (MEASURED, `pocket_cut.py` [MECH 2, 4.F]): `cut_off` from RUSTBORO's south-east pocket (33, 59) reaches 36
tiles and cuts 21 of 21 promised items; from the city proper, 1033 tiles and 17 of 21. The mark is map-wide, and RUSTBORO
was not stood on again until f1198954: about 285,000 frames of "seen all of".

## 6. The fix: E and K1 (READ unless tagged [ADD F4; FIX build])

- **E** (`ai_player/world/memory.py`): `MapMemory.standing` maps a tile to (kind, frame last seen). `see_objects`
  remembers every non-person object; one is forgotten when a look SHOWS its tile empty (`View.tile` not None: on a dark
  map only the lit circle counts) or after `CLOSED_RETRY_FRAMES` = 36,000 frames unseen. `objects_now` = this look plus
  the remembered, so `Navigator.walls`, `standing_walls` and `stand_tiles` read one set. Never people (they walk); never
  saved by `to_dict` (KI-134 V-N5: a saved thing would outlive what made it). Offline: the woods' frontiers behind the
  trees, 19 offered -> 0 [FIX verify].
- **K1** (`ai_player/knowledge/atlas.py` `entry_maps`; `ai_player/brain/goals.py` `entry_lead`, `Lead`, `WAY_IN`):
  `entry_maps(const)` reads `maps.json` at map level only (`maps[].id`, `warps[].dest_map`, `connections[].map`; no
  coordinates; declared in `check_fairness.py`), e.g. RUSTURF_TUNNEL -> {ROUTE116, VERDANTURF_TOWN}. When
  `lead_toward`'s town-prefix rule finds no town, `entry_lead` gives the nearest VISITED OPEN entry map by
  `world_distance`; None while standing on an entry map, or when none was visited or reachable. The log says "a seasoned
  player's knowledge". On the entry map the search is the AI's own.
- **A person's play** (INFERRED; USER RULINGS 35, 40): someone who saw a tree block a path remembers it on turning round
  [MECH 4.E]; K1 is "the maps and their connections", which RULING 40 allows, and picks a MAP, never a tile [KNOW 5]; so
  the user was not asked [ADD G4]. VERIFY1's decomp scan (READ): no chapter 1-7 script removes a cut tree, rock, boulder
  or item ball while the player is elsewhere on the map [FIX verify].
- **Not KI-128's rejected route planner** (INFERRED; 06, 2026-10-31: "a route planner over map connections (larger, and
  not what the measured failure needed)"; size and need, not fairness [KNOW 3]): K1 names ONE map from one static fact;
  the walk there is the AI's own, over links it remembers (`world_distance` counts only the links in the AI's own
  memory, READ); it plans no path over the game's connection graph and aims at no warp [ADD G4].
- **K2 rejected** (aim at the entry warp) [KNOW 5]: it needs the warp's tile; on a lit map it walks straight to the door,
  too close to the beeline RULING 40 forbids (INFERRED); 5 of 5 reaching legs found the door themselves (MEASURED).
- **Blast radius, chapters 1-7** (MEASURED, VERIFY1's `k1_blast.py` [ADD F4]): only RUSTURF_TUNNEL -> ROUTE116 is
  live-reachable; GRANITE_CAVE_1F -> ROUTE106 only in a unit test; GRANITE_CAVE_STEVENS_ROOM -> None.
- **Not built:** E2 and (b), held back (the A/B did not need them); (a), (c), F, filed [ADD G4]. **Commits:** `9d2f3fc5`
  on `<E0c>` (14 files, 615 insertions, 17 deletions) [FIX]; `3caf9c47`, test-only (`test_goals.py`, `revert_step5.py`;
  119 insertions, 2 deletions) [FXU; RB5]; into WT by a fast-forward [MP]. **Why a fix-forward was allowed** [ADD G4;
  MP 10:59 AM]: the run book's Rollback row allows a fix-forward commit on `wip/ch67-merge` after `<E0c>`; 06 2026-11-12
  item 6 ("no fix-forward commit between the two merge commits") concerns the window between the two merge commits (the
  run book's steps S2 and S3, not section 4's suspects), which this is not: the fix came after both, on `<E0c>` (the
  lead's reading, MP 10:59 AM).

## 7. Tests and gates [FIX; FXU] (the table READ; the arms and gates MEASURED)

| tests | pin | fault arm |
|---|---|---|
| `test_goals.py` StandingThingsTests e1-e11 | e1 nothing offered behind a tree off screen; e2 `cut_off` cuts it with the tree off screen; e3 seen gone, forgotten; e4 expiry; e5 no people; e6 never saved; e7 dark map: only a lit tile shows a thing gone; e8 the ROUTE116 flip in miniature (E removed: "184 not less than or equal to 4"); e9 the real woods memory; fix-up: e10 expiry from the LAST sighting, e11 item balls | G691-G697; G704, G705 |
| EntryLeadTests k1-k7 | k1 `entry_maps` on the real `maps.json`; k2 ROUTE116 from the loop's real memory, None on ROUTE116; k3 None with no entry map stood on; k4 controls; k5 the walk goes to ROUTE116 first; fix-up: k6 the NEARER entry map, k7 the open-country filter decides | G698-G703; G706, G707 |
| `test_kb2.py` `test_k_f3f` | `entry_maps` reads exactly `{maps, id, warps, dest_map, connections, map}` | a planted `warp["x"]` fails rule B2 |

The fixture `ai_player/gates/fixtures/ch5loop_tcap.world.jsonl` (395,197 bytes) is the AI's own memory inside the loop,
regenerated byte for byte [FIX]. MEASURED:
- **Whole-change arms** [FXU]: E removed, "FAILED (failures=11)" (e1-e11). K1 removed, "FAILED (failures=1, errors=4)":
  k1, k2, k4, k6 ERROR (the missing import), k5 FAILS; k3 and k7 pass (None is the old answer; their fault arms are G700,
  G707).
- **Mutants** [FXU; RB5]: "[G0] CONTROL, the unchanged copy: 480 tests, failing none ... -> PASS"; "17 mutants CAUGHT as
  predicted, 0 REDUNDANT ALONE as predicted, of 703"; "OVERALL: PASS". VERIFY2's own 10, different in form: 7 CAUGHT; 3
  survive all 480 tests (section 11) [FXU].
- **Gates** [FIX; FXU]: "ANCHORS GATE: PASS (9 of 9 runners, 1818 mutants, 1843 edits, 0 not unique, 0 errors)" (1801
  before); "PERSON-FAIR DATA DOOR: PASS (0 breaches)"; check_purity "VERDICT: PASS"; the unit lane, 32 suites, "OVERALL:
  PASS (every suite exit 0)"; test_goals 462 -> 480 tests. The quick gates on WT: section 9.

## 8. The live A/B, the verifiers' arms, the attribution

MEASURED; one trajectory per arm; purity CLEAN in every FIX and VERIFY1 arm [FIX build; FIX verify; S L2's
`fix5/verify1/runs/SL2_FIX/purity.json`].

| start | code | reached | frames | note |
|---|---|---|---|---|
| T L4 | unfixed (S3t-T) | NO | 600,000 cap | X 59 [DIAG 4] |
| T L4 | fixed: T_FIX_1, _2 and VERIFY1's _3 | yes | 198,539 | X 1; identical over 8077 moves: one trajectory, replayed |
| T L4 | minus E (K1 alone) | yes | 331,643 | X 2; the flip kept (656 right steps; unfixed 657); first lead f831278 |
| T L4 | minus K1 (E alone) | yes | 198,539 | identical to the fixed run over 8077 moves |
| C L4 | fixed | yes | 142,810 | X 0; unfixed S3t-C reached too (198,944) |
| S L4 | fixed | yes | 89,825 | 0.92 of E0 S's own leg 5 (97,323) |
| CH6 probe-C1 -> ch7_brawly | unfixed / fixed | yes / yes | 609,121 / 657,908 | +8%, inside an earlier run's 595,957-672,384 |
| CH7 R106_C1 -> ch7_steven | unfixed / fixed | yes / yes | 35,589 / 35,589 | identical over 1380 moves: inert in the dark cave |

- **First changed decision** [FIX build]: T at f738135 (E, the ROUTE116 heal walk: "walk right: (40, 14) -> (41, 14)",
  the way round, where the unfixed run walked into the flip); S at f517652 (E, ROUTE116); C at f557124 (K1, in the
  Rustboro POKEMON CENTER).
- **VERIFY1's arms** (fixed code [FIX verify]): T L3 reached `ch3_rustboro` in 264,178 frames against E0's 331,537; E
  acted at f507800 in the woods with no tree on screen (E0 "target frontier (24, 11)", fix "target grass (6, 12)"). C L3,
  T L2 and S L2: no hard break.
- **Attribution, T's start only:** each change ALONE reached (one trajectory each); NEITHER is shown necessary. The
  pre-registered clause "noE and noK1 both reaching with X < 10 says neither change alone is needed on this start" came
  true, so "both needed" is REFUTED there [FIX build]; T_noK1 is the fixed trajectory itself (V1-N2) [FIX verify].
- **The mechanism note's inference** (INFERRED, MECH 4.0, 6: E alone would not end the loop STATE) stays untested: E's
  first change (f738135) came before the loop's first burst (f1032970 [DIAG 6]), and the run crossed once. A start
  inside the loop with E's memory cannot be made (session-only) [FIX verify]. Lesson: test a fix from the start before
  the loop too [ADD G6].

## 9. FX, E0-2 and after (MEASURED: the run and gate verdicts) [MP]

- 6:14 PM, the GO line on `3caf9c47` (fix round CONDITIONAL_PASS, fix-up PASS); 6:17 PM, FX1 fast-forwards WT. E0-2 ran
  7:08-7:39 PM on new seeds 6484-6486; its record is commit `19e9700c`, pushed at 7:43 PM.
- **The STAGE FX line** (7:44 PM; verbatim, wrapped here):

```text
STAGE FX DONE: <FX>=3caf9c472a942c6153898cfb3e2aba647ab625f9, <E0c2>=19e9700c2d4be78ddc9e539b52bee49f1ce5e478; FX gates:
MERGE GATES FX: PASS (18 of 18 pass; 888 s; outputs C:\Remote Projects\_ai_lab\s53\mergeplan\out\gates\FX) (its
py_compile row compiled nothing on the fast-forward, "no staged .py", while the FX checker's in-memory compile read 11 of
11, MP/verifyfx/), QUICK GATES qg-FX-2: PASS (143 gates; red only where main's own tree is red in a worktree:
probe_fly_disjunct.py, selftest_facts_ledger.py), qg-FX FAIL (preflight AHEAD only; the lead's amendment FX-A1),
REGRESSION: PASS (quick, 23 suites, 28.6 s wall); E0-2: E0 VERDICT: REACHED 3 of 3; legs ran 15, purity-clean 15; wall
31 min (cap 120); problems 0 -> GO, ledger entry #148; the stage is UP in WT; next: stage II with LANEHEAD =
19e9700c2d4be78ddc9e539b52bee49f1ce5e478 (or, on any STOP, the lead).
```

(The FX checker's NIT: the 11-of-11 compile is `MP/verifyfx/fx2/compile_E0c_E0c2.txt`, not `MP/verifyfx/`.)

- **The FX checker** (8:00 PM): "PASS_WITH_NOTES, ready for stage II (no MAJOR, no MINOR; NITs only)". It adds "K1's lead
  fired 3 times in LC-C-6485 L5 (RUSTURF_TUNNEL -> ROUTE116), 0 in S and T: one trajectory, no rate", and, for the lead,
  that "no mutant runner has run in full on the fix's code".
- **PRELANE** (MP 8:06 PM; RB5 from 8:07 PM): the lead took that test first. The three mutant drivers that name the
  fix's files were launched at 8:09 PM to run in full on the lab tree `fix5/verify2/w` at `<FX>`, before the lane:
  revert_step5, 704 entries (the G0 control and 703 mutants) [RB5 8:32 PM], `--workers 3`; revert_step3; revert_r1, 643
  entries, `--workers 2`. The lead's rule: all three OVERALL PASS -> stage II; a changed verdict -> the lead. Result
  (RB5 10:21-10:41 PM; MP 10:45 PM): all three exit 0 and "OVERALL: PASS", no verdict changed. revert_step5 "698
  mutants CAUGHT as predicted, 5 REDUNDANT ALONE as predicted, of 703" (the fix's G691-G707 each CAUGHT; 7783 s);
  revert_step3 "93 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as predicted (each with its reason), of 94" (8922 s);
  revert_r1 "637 mutants CAUGHT as predicted, 4 REDUNDANT ALONE as predicted, of 642 run (642 defined)" (8631 s).
  Every control PASS; "FROZEN TREE: PASS" for revert_step5 and revert_r1 (revert_step3 has no frozen-tree watch). One
  run per mutant, on `<FX>`, the three at once under the tuner's load. Stage II's lane started at 10:46 PM on `<S3t2>`.
- **II-A1** (the lead's amendment, MP 9:00 PM): a second timing-rows commit `<S3t2>` = `fa9f073d` on `<E0c2>` raised
  four rows of `ai_player/gates/run_regression_times.json` (revert_step5 3460 -> 12110, revert_r1 1167 -> 4085,
  revert_step3 2014 -> 7049, revert_safety_gates 326 -> 3456), because the side branches' own full lanes had run three
  of them to their old caps (TIMEOUT, 2026-11-11) and revert_safety_gates to 96 % of its 3600 s floor; it changes no
  play code, so E0-2's GO stands, and stage II's lane runs on `<S3t2>`, not on the LANEHEAD the STAGE FX line names.
- **Reading.** Three new seeds are three trajectories, not a rate. A pass of E0-2 does not by itself lift the first STOP
  (the fixture's A/B answers that), and the first STOP stays in the record [ADD G4, G5].

## 10. Not proven

- The chapter 1-5 miss RATE beyond E0-2's three seeds, and whether the merge raises it (long loops in 3 of about 9
  merged-code paths against 0 of about 11 main paths: suggestive only) [ADD F7; DIAG 8].
- That either change is NECESSARY (no attribution arms from C or S) [FIX build].
- E on dark maps where it would act: at the lit circle's edge (a tile lit, the sprite unseen: E forgets, the old
  behaviour); a remembered thing within one tile of a failed step's target reports "someone at" (navigator.py about line
  1081) [ADD F7; FIX].
- K1 live outside chapter 5. K1 has no promise check on the entry map: a poisoned ROUTE116 could cycle, bounded by the
  budget, `FAIL_LIMIT` and the stall detector; not seen [ADD F7].
- E's seen-gone forgetting and 36,000-frame expiry live (unit tests only); the non-quick ROM gates (not run in the lab)
  [ADD F7].
- The full mutant drivers on the fix's code: before the lane, only the three that name the fix's files (PRELANE, on a
  lab tree at `<FX>`, launched 8:09 PM; section 9: all three "OVERALL: PASS", one run per mutant, on `<FX>`, not `<S3t2>`);
  every other driver runs in full only in stage II's lane, on `<S3t2>` [MP 8:06 PM, 9:00 PM; ADD F7].
- The cause of the one-frame splits [REF C].

## 11. Follow-ups (OPEN, not built) and their evidence

| item | what | evidence |
|---|---|---|
| (a) | keep "unreached" until something NEAR the frontier is learned | READ and MEASURED: any new tile revived it: in the T loop (35, 31), 11 tiles from (37, 22). Alone it changes only "1 thing left" labels (4 of 41 back decisions) [MECH 4.(a), 4.0] |
| (b) | `lost_way` for a told walk to an unfound map when every neighbour reads "seen all of" | MEASURED (a prototype, offline): a woods door 200 of 200 -> the main road up 200 of 200 [MECH 4.(b)]; INFERRED: goals with no static entry can still ping-pong [KNOW 5] |
| (c) | a found ping-pong outlives the intent, keyed by the way | MEASURED (a sketch, offline): the road up 200 of 200, but 20 into RUSTBORO's pocket [MECH 4.(c)] |
| F | a pocket's `cut_off` poisons the whole map | MEASURED: 21 of 21 cut against 17 of 21; INFERRED: the right fix is a promise per map PART [MECH 4.F] |
| E2 | the explorer's reach by the planner's `in_map_walls` rule | MEASURED (offline), with E only: from ROUTE104 (11, 29) the frontier (37, 22) is still OFFERED, then refused at once (no longer after a walk of about 20 steps) [FIX verify V1-M3] |
| lead logging | log every lead decision, None included | READ: a None leaves no line; MEASURED: T_FIX_1's None is known only from "0 lead lines" [FIX build] |
| `heard_page` | may quote a page without the place's words | MEASURED (a count; the cause not investigated): "Milo put away the DEVON GOODS in the KEY ITEMS POCKET." quoted as the tunnel's page, 8 times in late T goals [KNOW 6] |
| `_Regions.landings` | route values only for road tiles that land in the route's own part | READ: a connection first hop gives EVERY road tile on that side the value, dead-end parts included [MECH 4.(b)] |
| V2-N1..N3 | K1's three unpinned choices | MEASURED (VERIFY2's mutants): survivors: a pick by link order (k6); an underground-only filter, leading AQUA_HIDEOUT_B2F -> AQUA_HIDEOUT_B1F, INDOOR (k7); the filter on the pick. None acts in chapters 1-7. The fix-up's "any pick that ignores the distance ... fails one of them" was argued, not measured [FXU verify] |
| **USER question (parked; do not answer here)** | may a seasoned player head for a story place BEFORE the game names it? | READ: RULING 40 superseded dialogue-only hints, but the code waits for the step's words; RULING 32: never a speedrun [ADD G2]; every E0 leg was told anyway [KNOW 3] |

## 12. Where the lab evidence was (deleted after the merge; copies kept in `_ai_lab/keep/`)

Under `C:/Remote Projects/_ai_lab/s53/`: `e0diag/` (notes, trees, runs incl. `s3t_Tcap`, scripts, the `clone`),
`fix5/` (patches, the 10 live arms, the verifiers' folders), `mergeplan/` (`e0/runs/E0-6481`, `E0-6484`). The lead's
ruling (MP 10:04 PM): "every folder under _ai_lab/s53/ is lab the cleanup may delete, only _ai_lab/keep/ is kept".
Git keeps the fix's two commits, E0-2's `19e9700c` and II-A1's `fa9f073d` (pushed on `wip/ch67-merge`), the tests,
mutants and fixture, and this note. Kept outside the lab (not deleted with it; on the user's PC only, not in git; each
folder's README.txt gives every kept file's sha256):
- T's L4 start files, in `C:/Remote Projects/_ai_lab/keep/2026-11-13-ch5loop-T-L4/` (section 3);
- kept by the lead for A1 (MP 10:04 PM), in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/`: E0's three L5
  legs (`world_last.jsonl`, `row.json` and `ai_player.log` of LC-C-6482, LC-S-6481 and LC-T-6483), C_FIX's
  `actions.jsonl`, and the lab scripts `stage_merge.py`, `stage_diag.py`, `replay_leg.py` and `compare_moves.py`.
