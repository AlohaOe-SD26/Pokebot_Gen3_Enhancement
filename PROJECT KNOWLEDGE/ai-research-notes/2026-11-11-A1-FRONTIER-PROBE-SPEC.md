# A1: the wide frontier probe and the trainer's runner core: BUILD SPEC (2026-11-11, revised after review; amended 2026-11-13)

> **Claude's spec, NOT BUILT, a NOTE like every agent output.** Written read-only by a spec agent of session `2cb1657d`,
> revised the same day on an independent review's 21 findings (`2026-11-11-A1-FRONTIER-PROBE-SPEC-REVIEW.md` beside it; Review log at the end). Each code
> claim names a path and line, or a symbol whose line is in table 1.2; the builder re-reads it before relying on it.
> UNKNOWN = not checked. **Read at** `main` `10ceb4f7`, re-checked at `879b1fe3` (docs only since; no `ai_player/` code
> changed after `dc0a4e69`, the graded chapter-5 commit); `origin/wip/ch6-ch7` `18c3d51b`; `origin/wip/ch6-bp1`
> `c5146e53`; the learner clone `da2fb96a`; the decomp pin `731ad5b`.
> **Amended parts read at** `3caf9c47` (2026-11-13: the merged tree with the chapter-5 fix; Review log).
> **It replaces** the "A1" part of section 4 of `PROJECT KNOWLEDGE/ai-research-notes/2026-10-30-AI-TRAINER-DESIGN.md`
> (its decisions hold except as 1.3 says) and **keeps the order** in `06` 2026-11-11 (BP-1 round 2, P11-1, the chapter
> 6-7 merge, then A1; "Not a do-not-reopen ruling"; section 5 has the facts).

## 0. In plain words

- **Now:** the AI's graded frontier is the end of chapter 5 (6 of 6 New Game chains, ledger #101,
  `PROJECT KNOWLEDGE/ai-frontier.txt`). Chapters 6-7 (the sail to DEWFORD through BRAWLY) are merged
  on `main` at `1971e130`; the graded frontier is unchanged (a merge check is not a grade).
- **Two jobs:** (1) **measure** where the AI stops across chapters 1-7 on the merged code, as a ranked **blocker list**
  with a saved example of each, for the trainer to work down one skill build at a time; (2) **be the runner core** the
  learner's trainer (Phase A) calls as a subprocess. Nothing is built twice.
- **It reuses** `live_chain.py`'s leg pieces, `live_step5.run_arm` (the real launcher, gated per launch) and the lab's
  staging kit, and **adds** one test-side module, `ai_player/gates/frontier_probe.py`: a parallel job runner beside the
  bot tuner, end classes from files (D14), ranked blocker keys (D7), static-only experience (D16), a `--trainer` mode
  that writes no tracked file, disk caps (KI-129, KI-130). **Part 0 (GM, 3.15) is AI-side:** the play brain writes its
  goal memory at every end it controls and restores it at a `--state` start, so A1's test starts carry the emulator
  state, the world memory and the goal memory (`06` 2026-11-12 item 4).
- **WP1 (after the merge), 39 jobs in one batch:** **WP1a**, 9 New Game chains to `ch7_brawly`, one per personality ×
  starter (6 pairs never played as a New Game chain: `live_chain.PAIRS` is the diagonal, though `rate_step5.plan_of`
  cycled all 9 in sweeps), each leg carrying the goal snapshot; **WP1b**, 27 practice jobs (WP1a's 9 chapter-5 ends ×
  3 seeds, chapters 6-7; a pair whose chain missed uses its persona's G start, counted apart) and 3 planted-wall jobs
  (P2). About 4-5 h of machine time at 8 at once beside the tuner's 12 lanes (about 9 h if every L6 and L7 spends its
  whole budget; L6 is now 1,000,000 frames). Before it: part 0's live A/B (about 1-1.5 h), P1 (20-30 min: a wall at
  OLDALE TOWN that must rank first on the walled code and never appear on the real code), MC's first run (about 30-45
  min, on the A1 commit; it must read PASS) and one full regression lane (about 4.4 h, budgeted from upper-bound rows;
  the merge's own full lane gives the measured hours). About 11-13.5 h of machine time in all, about 22.5 h worst
  (6.2). Estimates.
- **Cost:** about 57-98 Mtok (central 76; estimates), above the design's 8-15 and the first draft's 38-65: part 0
  (GM), its verifier share, the amendments' rules and the extra live work add 19-33 (6.1). The graded chain driver it
  leans on cost 111.8 Mtok (`cost-ledger.jsonl`).

- **Not answered by A1 v1: whether the merge raises the chapter 1-5 miss RATE.** E0's diagnosis left it OPEN (2 of 3
  E0 L5 misses against 0 of 9 on main, p about 0.045 and confounded by start states: ledger #147 and the repo note
  `2026-11-13-CH5-SEARCH-LOOP-FIX.md` sections 4 and 10). It is a frequency question for many seeds (CLAUDE.md rule
  9); MC (2.4b) is a hard-break check and WP1a has 9 chains. It is filed as its own `03` item: a seeded batch of New
  Game chains to `ch5_rival_meet`, the pre-merge `main` (`934ddb7f`) against the merged tree, many seeds each, read as
  a rate.

## 1. What A1 is for, and what exists

### 1.1 The two outputs

1. **The blocker list, chapters 1-7, merged tree.** Per chapter: reach from the game; ranked keys (D7) with their share
   of judged legs and frames spent; up to 3 examples each (`end_state.ss1` + `world_last.jsonl` + zipped logs, enough to
   start the stop's region again through the launcher: one more trajectory, 2.4). The next skill build takes the top
   entry. Seen in development (never a rate):
   BRAWLY beats the Story party (P4-1, BP-1's subject); the dark GRANITE CAVE is slow (P11-1); churn at RUSTURF TUNNEL
   (KI-130; 497 MB `world.jsonl`, `control2-C-C2L4-6393` in `_ai_lab/s53/bp1r2/out/control2/results.json`); the 6 new
   pairs UNKNOWN. WP1's prediction file names these first.
2. **The runner core.** Phase A's `ai-agent/ai_trainer.py` (design D1, D5, D15, D17) runs `frontier_probe.py run
   --trainer` on a stage built from the AI code checkout's commit, `--out` outside the learner clone (3.3, 3.10), and
   reads the JSON records. Phase A adds only the planner (D15), the checkout updater (D1), retention (D11) and the wiring.

### 1.2 Reuse, never rebuild (the line numbers the other sections rely on)

`G/` = `ai_player/gates/`; `launcher` = `ai_player/host/launcher.py`; `LC` = `G/live_chain.py`.

| Piece | Where | A1's use |
|---|---|---|
| A gated leg through the real launcher | `G/live_step5.py` `Arm` :177-186; `run_arm` :439-509 (`--state` + `AI_PLAYER_WORLD` when `state_from` is in `carried`; output in `run.stdout`; `ensure_profile` without template :441; `driver_killed` at wall + 300 s :474-480; `run.earlier` :455-458); `check_after_is_this_run` :524-536 (mtime; frame = start + real_frames ± `FRAME_SLACK` 5; md5 differs) | unchanged, once per leg; freshness |
| Purity; env strip | `G/live_step2.py` `check_purity` :518; `clean_env` :324-328 (strips only `AI_PLAYER_*`) | as `run_chain` (:2218-2219) |
| Legs, proofs, reach | `LC` `legs_of` :404-445 (refuses an optional target :419-420); `FRAMES_BY_CHAPTER` :163; `WALL` :164; `PAIRS` :155; `proof_holds` :468-492 (a missing key is NOT held); `leg_reached` :1338-1344; `continue_after` :1444-1471; `custody_problems` :1394; `WORLD_SIZE_KIND` :176 (GRADED); `PURITY_IDS` :188; `run_chain` :2169-2268 (row :2227-2242) | 2.3, 3.6, T27 |
| Leg end; dead launch | `LC` `finish_leg` :2102-2156 (measure, keep the last line, DELETE `world.jsonl`); `launch_died` :1350-1364 | verbatim; INFRA |
| Disk guard | `LC` `guard_decision` :1481-1488 takes no thresholds (reads `GUARD_WORLD_BYTES` 1.5 GB, `GUARD_FREE_GB` 30, :178-179); `newest_world` :1491-1504; `safe_free` :2352 | `newest_world` only (3.12) |
| Scheduler; salvage | `LC` `schedule` :2471-2499 (a refused job goes to `not_started` for good); `salvage_leg` :2271-2289 (needs `job["profile"]`, `job["chain"]`, the leg keys of `not_run_row` :2062-2065); `salvage_chain` :2292-2320 (reads live_chain's `rows/<chain>.json`, `current_leg.json`) | `salvage_leg` only (3.4, 3.13) |
| Misc | `LC` `python_env_refused` :276, `child_env` :2406-2411, `end_sweep` :2711-2724, `chain_watchdog_seconds` :388-391, `STAGGER_SECONDS` :166, `untrusted_text` :2023, `NEW_MEMORY` :1198, R8 :2524-2526; `GRADER_GATES` :292 (holds `check_grader_imports.py`) → `GRADER_FILES` :363 → `registered_numbers()["grader_files"]` :1170 | reused; why G-3's file stays unchanged |
| Profiles | `launcher` `ensure_profile(build_root, name, template)` :158-189 (no template: `endless-P1-torchic`, else the first sorted profile with a `metadata.yml`, :173-180); `_PROFILE_NAME_RE` :119; `PACKAGE_ROOT` :95 | an explicit donor (3.4) |
| Exits, end reasons | `launcher` `WALL_CLOCK_EXIT` 124 :107, `GATE_REFUSED_EXIT` 7 :109, `NO_VERDICT_EXIT` 8 :111, `GATE_TIMEOUT_SECONDS` 180 :117, `_INVOLUNTARY` :271, `_HOST_CODES` :275-276, `_ran_out` :449-457, hard kill = "a stuck run" :499-502, `_classify_session` :548-557, `soft_deadline_margin` :714-719, `GateRun.findings` :741-742 ("FAIL" lines), the timeout text :760, `run_child` :848-904 (124 at :902); `ai_player/__main__.py` `_gate` :83-100 (`[AI-GATE]` lines :87-91), `_report_verdict` :103-132, `return GATE_REFUSED_EXIT` :148; `ai_player/mode.py` :1401 (`stopped: not finished within … frames`) | D14 (3.5) |
| Ledger | `G/ledger.py` `register` :116-144, `begin` :147-206 (development refused over an unplayed `registered` entry :181-185), `finish` :209-219, `--check` | 3.10 |
| Maps; truth | `G/rate_step5.py` `map_keys` :1827 (reads `MapRSE` as text, no framework import; `map_data.py` `OLDALE_TOWN` (0, 10) :804, `ROUTE104_MR_BRINEYS_HOUSE` (17, 0) :1054); `G/play_harness.py` `story_truth` :95-120, marks = the proofs of `knowledge/milestones.json` (`tracked()` :82-95) | 3.8; read only |
| G-3; AI facts | `G/check_grader_imports.py` `GRADERS` :32, `ALLOW` :37 (only `host.launcher`, `options.ENV_*`), `scan` :211; `ai_player/personality.py` `PERSONALITIES` :60; `ai_player/world/memory.py` (3.9); `ai_player/options.py` (3.11) | copied as constants, never imported (T30) |
| Lab kit | `_ai_lab/s53/ch6probe11/build_stage11.py`, `make_arm11.py`, `arms11.py` `child` (`carried = {"START": (state, world, [])}`, `state_from="START"`); `s53/bp1r2/seeds_free.py`. `_ai_lab/s53/` is lab, which the merge's cleanup may delete: the four files are kept, cmp-equal, in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` (`ch6probe11/`, `bp1r2/`; sha256 in its README.txt; this PC only, not git) | `stage` (3.3); seeds (2.5) |
| Zip check | `ai-agent/learner.py` `verify_archive` :1510 | NOT imported, A1's own choice (the runner must not depend on the learner clone; D17 forbids only the learner importing `ai_player`, and `G/live_step1.py` :247-248, :916 imports `ai-agent/scoring.py`) |

### 1.3 The 2026-10-30 design: what holds

| Design part | Now |
|---|---|
| §0, §2 "never played chapter 3", gap 1; "loader slice 1"; A1's old jobs, budgets, "8-15 Mtok"; "milestones stop at ch4_roxanne" | **Superseded or done:** A0 ran (07 2026-10-30); KI-128/129 graded (#82); chapter 5 graded from a New Game (#101); `knowledge/atlas.py` reads map ids and types; sections 2 and 6 here; 36 milestones on the merged `main` (28 before it). |
| §6 Q1; D2, D3, D4, D16 | **Hold** (Q1 = USER RULING 55). D3 also excludes the harness-placed I1, D1, D2 (2.1). |
| D7, D12 | **Changed** (for `06`, 4.4 item 8). D7 takes the LEG's chapter, and a leg that ends inside a long map-pair loop gets ONE LOOP key whatever its next milestone, class or end map (3.8). D12 stays `run_chain`'s leg rule, but every leg A1 starts from a kept state also carries the kept goal snapshot (part 0, GM, 3.15); the profile's `memory.jsonl` is still archived per leg. |
| D11, D13 | Per-batch caps and the band check here; retention, the 45 GB learner floor are Phase A. **Changed:** the AI store lives OUTSIDE the learner clone (3.10). |
| D14 classes | **Changed:** D14 made every missing verdict REFUSED. Here a gate TIMEOUT, `run_arm`'s driver kill and a launch dead before a frame are INFRA; the launcher's hard kill with no verdict is the new class HUNG, other missing verdicts NOT CLEAN, both counting toward the AI-only stop; CUT-WORLD and CLEAN-INVOLUNTARY added (3.5). For `06`. |
| D1 hourly checkout | **Phase A. Changed:** it builds a stage from the checkout's commit, never runs a checkout in place (3.3). |
| D5, D6, D8-D10, D15, D17 | Phase A or later. A1 leaves the tuner's 12 lanes alone, takes a fixed job list in D15's schema, builds D17's child allow-list. |
| §1 learner anchors | Same rules at `da2fb96a`: `other_bots_running` :574-584, `size_lanes` :593-603, the 8-lane wait :2123, `disk_guard` :1875-1897. |

## 2. The first wide probe

### 2.1 Starts

Each start file is COPIED into the stage and md5-checked; sources are never read in place or written. `GC` =
`C:/Remote Projects/_livechain/graded-ch5`, graded ledger #101's record, which `live_chain.py grade` must keep
re-grading unchanged.

| Id | Files | md5 `end_state.ss1` / world | Made by | Persona / starter |
|---|---|---|---|---|
| NG | none: `--fresh`, a real New Game | - | - | the 9 pairs |
| G1 | `GC/LC-S-6201/L5/end_state.ss1` + `world_last.jsonl` | `5cdc4f0e20e99f650de8d6d157d5afd2` / `4698f99b27a9971a8819b4436e8bf0d8` | #101 on `dc0a4e69`, `ch5_rival_meet` at frame 546,534 | Story / TREECKO |
| G2 | `GC/LC-S-6202/L5/` | `b241a855c44f5150b8393089c90bc8bb` / `48254060e4b119c029a3b409b601246b` | same, 843,387 | Story / TREECKO |
| G3 | `GC/LC-C-6203/L5/` | `6a53506de6ef7a9b1bce8f9836bc25fb` / `ad10200b32a63cc8780d22378faa5c96` | same, 698,222 | Catcher / TORCHIC |
| G4 | `GC/LC-C-6204/L5/` | `84247b70cd0e88783261a0459b442229` / `a6fd383f89b219ee87b9ac4fc2db2dcc` | same, 642,957 | Catcher / TORCHIC |
| G5 | `GC/LC-T-6205/L5/` | `eb1aa3704ff7b37c7283fd53da5f52ab` / `675d2df00dd2e0b515002e6f15e22a30` | same, 912,041 (no optional rival battle) | Trainer / MUDKIP |
| G6 | `GC/LC-T-6206/L5/` | `16f23af7d6bf76f6490520b23c6049c9` / `3987e9d13a57d07cd960d7b12e26fa22` | same, 881,797 | Trainer / MUDKIP |
| C1 | `_ai_lab/s53/ch5stops/out/probe/probe-C1/end_state.ss1` + `world.jsonl` | `e909e5377ae54457dfb13b9e17946648` / `a10e59061eff7e2782fb86bd16200b56` (`_ai_lab/MANIFEST.json`) | a development chapter-5 leg (seed 6021) from the 2026-11-01 chain probe's BADGE-1 end; mixed code (digest recorded from `s53/ch5stops`) | Story / TREECKO (expected) |
| C2 | `.../probe-C2/` | `6c9039355b86af9ffca529c618eda00f` / `49b7a8c888ec877ec4e674171ad72a43` | same | Catcher / TORCHIC (expected) |
| C3 | `.../probe-C3/` | `bbcc172f3b2d51e8b5a5e5c3c8eeb581` / `7059420eef7af06d7bc53c453628e82a` | same | Trainer / MUDKIP (expected) |

- The six G ends read `reached` and `RAN` in `L5/row.json`, at map `[0, 3]` = `RUSTBORO_CITY`. G starters come from
  `LC-*.job.json` (`"starter": "TREECKO"`). `probe-C*.job.json` names only the persona, so `stage` reads the C starter
  from the start truth's party (the TREECKO, TORCHIC or MUDKIP evolution line), records `starter_from: "truth_party"`,
  and refuses none or two lines.
- **Excluded:** I1, D1, D2 (each `*.build.json` says `played_by: "the AI's hands brains (goto, battle with talk_to …),
  test side"`: harness-placed fixtures under D3); the BADGE02 ends (only the optional `ch7_exp_share` follows, and
  `legs_of` refuses an optional target); C1L4 and C2L4 (chapter-4 ends the chains cover).
- **Goal memory (part 0, GM, 3.15).** None of G1-G6 or C1-C3 holds a goal snapshot (G1-G6's folders keep the state,
  the world line and the logs; C1-C3's the state and `world.jsonl`), so a job started from one is labelled
  `goal_memory: none` and counted apart. WP1b's practice starts are WP1a's own `ch5_rival_meet` ends (2.4: the same
  tree, all 9 pairs, snapshots carried). A pair whose WP1a chain ENDS without a reached L5 (it stopped before L5, or its
  L5 missed `ch5_rival_meet`) uses its persona's next unused G start (Story G1, G2; Catcher G3, G4; Trainer G5, G6;
  then C1-C3), with that start's own starter (`starter_from: job_file` for a G start, `truth_party` for a C start, as
  above), labelled `goal_memory: none` and `fallback_for: <pair>`, and counted apart, so chapters 6-7 are never left
  unmeasured.
- **Where the C starts are kept.** `_ai_lab/s53/` is lab that the merge's cleanup may delete. C1-C3's files (the
  table's `end_state.ss1` and `world.jsonl`, with `probe-C*.job.json` and `probe-C*.json`) are kept, md5-equal to the
  table, in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/ch5stops/out/probe/` (sha256 in the keep folder's
  root `README.txt`; this PC only, not git). G1-G6 stay in `C:/Remote Projects/_livechain/graded-ch5`, outside the lab.
- **Custody at stage time:** refused on an md5 that differs, a truth not holding `ch5_rival_meet`'s proof, a world file
  that is not JSON lines, or no readable starter. The read pages a go goal may quote (`run.earlier`) come from the
  start's kept `actions.jsonl` (G1-G6), else `[]`, counted.

### 2.2 Personas and starters

- **New Game chains:** all 9 pairs of the 3 personalities (Catcher, Story, Trainer) × the 3 starters. Chains so far
  played only `PAIRS`' diagonal (Story/TREECKO, Catcher/TORCHIC, Trainer/MUDKIP); the 6 others are D15's "under-sampled
  pairs". `STARTER` is set only on a fresh leg (`live_step5.play_env` :399-403).
- **Saved starts** keep their game's persona: it chose the name and gender, and a person does not change character
  mid-game. The starter is in the save.

### 2.3 Targets, legs and budgets

The target is the chapter's last milestone that is neither optional nor a waypoint, as `legs_of` picks it. L1-L5 come
from `FRAMES_BY_CHAPTER` and `WALL`; L6-L7 are NEW, in `frontier_probe`'s own table (never `live_chain`'s).

| Leg | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|---|---|---|---|---|---|---|---|
| Target | `ch1_pokedex` | `ch2_wally` | `ch3_rustboro` | `ch4_roxanne` | `ch5_rival_meet` | `ch6_dewford` | `ch7_brawly` |
| Frames | 330,000 | 330,000 | 600,000 | 900,000 | 600,000 | 1,000,000 | 1,200,000 |
| Wall (s) | 3,600 | 3,600 | 3,600 | 3,600 | 3,600 | 7,200 | 7,200 |

- **Why.** Probe 11 (#117 (was wip/ch6-ch7#111)): C2 and C3 reached BADGE02 in 195,229 and 194,349 frames with no raise; C1 lost to BRAWLY
  three times (`stuck: 3 battles lost` after 167,065; the CH6-CH7 report on `origin/wip/ch6-bp1`). BP-1 round 2's B2 arms
  took 612,596-666,141 frames from C1, the raise 450,784-464,737 of them (`bp1r2/out/ab2/results.json`). USER RULING
  55: "In training the budget is set generously, so it never cuts off real progress." At 349 frames/s (2.6), 1,200,000
  frames take 3,440 s and 1,000,000 take 2,865 s (3,333 s at 300 frames/s, where the lead lowers P): both walls are
  7,200 s.
- **The budget check, closed on 2026-11-13: L6 raised to 1,000,000 frames.** The boss-prep raise runs INSIDE L6: it
  plans for the next NAMED fight from the whole story (`brain/goals.py` :2177-2181 at `3caf9c47`; `load_story` loads
  every milestone, `knowledge/story.py` :152-153), and 8 of 8 measured runs from C1 made 0 raise goals after
  `ch6_dewford`. L6 (C1's start record, f746397, to `MILESTONE ch6_dewford`) took 500,515, 496,341 and 495,188 frames in
  BP-1 round 4's `ab4w-B4-C1-6414/6415/6416`, 395,755, 382,058 and 377,952 in `ab4g-6426/6427` and `ab4g2-6429`
  (ledger #131-#133, which that evidence file numbers #125-#127 as on `wip/ch6-bp1`; their raises ended at frames
  457,706, 460,630 and 450,262 of 450,000 in #131 and at battles 164, 164 and 163 of 160 in #132-#133:
  `ai_player/evidence/2026-11-11-bossprep-bp1r4-live.txt`, P-W5 and P-G6), and
  520,366 and 520,216 in the fix round's CH6_FIXED and CH6_UNFIXED (the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md`
  section 8 keeps their whole L6+L7 frames, 657,908 and 609,121), one trajectory each, each L6 read from its run's own
  log (lab, deleted after the merge): 5 of 8 over 80 % of 600,000, exactly the 5 whose raise ended on its frame bound
  (450,262-475,016 of 450,000). The derivation is in the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md` (section 2.1 and AM-16). A
  Catcher's budget is 550,000 frames (`brain/bossprep.py` :160): at the largest measured L6 over Story's 450,000
  (1.156) a Catcher L6 needs about 636,000 frames. 1,000,000 keeps both under 80 % (52 % and about 64 %). Set before
  WP1's prediction is hashed (USER RULING 55 (2), `06` :9963: "In training the budget is set generously, so it never
  cuts off real progress"). The optional `ch6_old_rod`, `ch7_flash`, `ch7_gym_trainers`,
  `ch7_exp_share` are reported, never targeted.

### 2.4 Batches

| Batch | When | Jobs | Legs |
|---|---|---|---|
| **P1**, the planted-wall proof | on the merged `main`, after GM's offline proofs | arms REAL and WALL-OLDALE (4.3), the 3 diagonal New Game chains each, the SAME 3 seeds in both arms, the goal snapshot carried in both | L1-L2, at most 12 legs |
| **MC**, the merge check (2.4b) | first on the A1 commit, PASS before WP1; then on every merge, from the tree under test | the 3 diagonal New Game chains, NO goal snapshot (E0's harness), 3 never-used seeds | L1-L5 (to the newest graded target), at most 15 legs |
| **GM**, part 0's live A/B (3.15 item 7) | after A1's runner exists, beside P1 | one diagonal New Game chain L1-L5 with GM (it makes the start), then arms GOALS-ON and GOALS-OFF from its L5 end on 2 seeds, L6 | 5 jobs, at most 9 legs |
| **WP1a**, the wide probe's chains | after the merge and GM | **J-N:** 9 chains, one per pair, L1-L7, each leg carrying the goal snapshot | 9 jobs, at most 9×7 = 63 legs |
| **WP1b**, practice and the cottage wall | as each WP1a chain's L5 ends | **J-F:** 27 practice jobs, WP1a's 9 `ch5_rival_meet` ends × 3 seeds, L6-L7, snapshots carried (a pair whose chain missed: the fallback start of 2.1, counted apart). **P2:** arm WALL-BRINEY on the first-seed J-F job of each diagonal pair (one per persona), L6 only | 30 jobs, at most 27×2 + 3 = 57 legs |

- **USER RULING 55 is met inside WP1:** chains and practice test one tree in one batch, and the AI reads no experience
  yet. **27 practice jobs:** D15's quota is 40 CLEAN ends at a chapter; WP1 gives up to 36 at each of chapters 6 and 7.
- **3 seeds per start, all distinct:** `ENV_CLOCK` "10:00" (`live_step5.py` :143) is the wall clock the AI SETS
  in its room; the cartridge's own clock reads the host's time in a launcher run (:142; design risk 9). Measured on the
  merged code (E0; the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md` section 3, beside this spec): the same code, saved
  start, seed and environment, with fresh profiles, replay move for move and then split by ONE frame at a warp onto an
  outdoor map, at a point no one can predict (the cause is suspected, not proven: "Cause NOT proven", that section);
  host load may move it (suggestive only: `e0diag/shadow/SHADOW.md` :83-84, 2 runs against 3; lab, deleted after the
  merge). So a rerun on one seed is a correlated near-replay, never an independent sample and never a replication
  (CLAUDE.md rule 8): identical results are a determinism check only, and a different result on the same seed is not
  evidence of a code difference. Seeds are spent per start and never repeated to sample it.
  **Order:** GM's chain and A/B (part 0's live proof), then WP1 as ONE batch (one ledger entry, seeds 6611-6646, one
  prediction file): WP1a's 9 chains first, then J-F interleaved by start, then P2. A WP1b job is SKIPPED (3.13: it keeps
  its place, and the ready jobs behind it launch) until its source chain's reached L5 record exists; when that chain
  ENDS without one, the job takes its fallback start at once (2.1). **Who carries a goal snapshot:** every A1 leg
  started from a kept state, except MC's (2.4b, E0's harness), GM's GOALS-OFF arm (3.15 item 7) and the labelled
  `goal_memory: none` starts. Any A1 number set beside #101, E0 or E0-2 (none of which carried one) names that
  difference or uses a labelled no-GM arm.

### 2.4b The merge check (MC): the chapter 1-5 check on every merge (it replaces E0)

`plan MC --first-seed N [--to <target>]`: the three diagonal New Game chains (`live_chain` `JOB_ORDER_3` :159) from
`--fresh` to the newest GRADED target (`PROJECT KNOWLEDGE/ai-frontier.txt`; today `ch5_rival_meet`), legs by
`FRAMES_BY_CHAPTER` and `WALL`, P = 3, run with the `frontier_probe.py` of the tree under test (on a merge, the merge
worktree), so its ledger entry and evidence land on the branch under test as E0's did (`a90c8e8f`, `19e9700c`). One
development ledger entry; the prediction hashed before the first launch.
- **Its first run is on A1's own commit, and it MUST read PASS before WP1.** Part 0 moves the play digest (3.15 item
  8), so E0-2's GO (ledger #148, on `3caf9c47`) does not cover A1's play code. That run uses the stage of the A1 commit,
  and WP1 does not start before it reads PASS. On every later merge MC runs as this section says.
- **E0's harness, exactly.** No goal snapshot is carried (`AI_PLAYER_GOALS` is never sent); the next leg is decided by
  `live_chain.continue_after` itself (its 300 MB cap included); the world guard is live_chain's: an MC leg's
  `world.jsonl` is cut only over `live_chain.GUARD_WORLD_BYTES` (1,500,000,000 bytes, :178), never at A1's
  1,000,000,000, and an MC job's profile budget, 1,750,000,000 bytes, sits above that cut (2.7, 3.12). So every MC leg
  continues or stops where E0's would (T27, T33). A1's floors (45 GB to start, 40 GB to abort) still apply: they
  protect the tuner and never decide play. No E0 or E0-2 leg came near a world cap (largest 275,942,646 bytes).
- **Seeds:** each merge takes the next 3 never-used seeds of the MC range `6701-6799`, checked FREE by A1's own seed
  check before the first launch (2.5; 3.10's `--ledger development`; T13). The range read FREE in 308 ledgers at 7:46
  PM 2026-11-13 (the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.6). Never a seed any entry names:
  6481-6483 (E0, ledger #147) and 6484-6486 (E0-2, ledger #148) are spent.
- **Reading (a hard-break check, NEVER a rate, `06` :10127).** PASS = every leg CLEAN-*, every `PURITY_IDS` check and
  L5.THIS_RUN passing, every chain reaching its target. Any HUNG, NOT CLEAN, REFUSED, freshness INFRA, CUT-WORLD or
  miss is a STOP. A miss's records (its key, or LOOP, 3.8) start the diagnosis, which is an A/B on the miss's own saved
  start (E0's method), never a reroll.
- **Its false-STOP rate is UNKNOWN.** With per-chain reach p on the tree under test, a 3-of-3 bar stops a good merge
  with probability 1 - p^3: 14 % at p = 0.95, 27 % at p = 0.9, 49 % at p = 0.8. p is not known: E0-2's 3 of 3 on
  `3caf9c47` (one trajectory per seed) bounds it only from below, at 0.37 (one-sided 95 %: 0.05^(1/3)); #101's 6 of 6
  ran main's `dc0a4e69`, and E0's 1 of 3 the unfixed merged `c25d2c40`: other trees, not pooled. One STOP's cost,
  measured once: from E0's STOP record (commit `a90c8e8f`, 8:19 AM, ledger #147) to E0-2's GO record (commit
  `19e9700c`, 7:42 PM, ledger #148) on 2026-11-13, about 11.4 hours, with a diagnosis, a shadow replay, a recon, a fix
  round and a fix-up (`07`'s merge entry; the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md`; their Mtok are not yet in
  `cost-ledger.jsonl`). The lead may relax the bar in `06`, knowingly: for example, a miss whose key already holds on
  the base tree's newest A1 report is a known blocker, recorded, not a STOP. E0 would still have stopped under that
  rule: long loops appeared in 0 of about 11 main paths (that note's section 10, "suggestive only"; from
  `e0diag/DIAGNOSIS.md` :267-269, lab, deleted after the merge).
- About 30-45 minutes (E0 41 min, E0-2 31 min). The merge run book's step E0 becomes `frontier_probe.py run` on the MC
  job list, and `06` records "Item 4's bridge retires" (4.4 item 8).

### 2.5 Seeds

- **One development ledger entry per batch**, one contiguous range. Seeds are shared on purpose (P1's two arms; P2 reuses
  its J-F seeds, as BP-1 round 2 did in #124-#127 (was wip/ch6-bp1#118-#121); a chain's legs), so a resume de-duplicates by `run_id`.
- **Proposed:** P1 `6601-6603`, GM's live A/B `6604-6606`, WP1 `6611-6646`, MC `6701-6799` (3 a merge,
  2.4b). Re-checked at 7:46 PM 2026-11-13: FREE for each of these ranges and for `2000000-2999999` in 308 ledgers
  (main 1, worktrees 11, others 296; the command and its output: the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md`,
  section 2.6); 6481-6483 are E0's (ledger #147) and 6484-6486 E0-2's (ledger #148). A1's own seed check (this
  section and 3.10's `--ledger development`, T13) checks every seed again before the first launch.
  At 10:40 AM 2026-11-11, `py -3.12 -B "C:/Remote
  Projects/_ai_lab/s53/bp1r2/seeds_free.py" 6461-6500 6501-6600 6601-6700` printed FREE in 188 ledgers (main, 10
  worktrees, the lab and others); the reviewer agreed on the 30 committed `ledger.json` of every ref.
- **Not a reservation:** BP-1 rounds 3-4 and P11 have since committed their seeds (the merged `ledger.json`'s
  entries #128-#146 name seeds in 6403-6454). **Re-check at build time**
  with that script (`s53/ch6/seeds_free.py` misses the lab and the learner clone); refuse any seed named by ANY entry,
  development included (live_chain R3). A1's own check lists every ledger it could not read and refuses
  unless each is a known non-ledger (on 2026-11-13 one truncated export,
  `_ai_lab/s53/mergeplan/review/exports/s2/ai_player/gates/ledger.json`, "Expecting value: line 115"; lab, deleted
  after the merge; `seeds_free.py` only skips it). `--trainer` uses only the D13 band.

### 2.6 CPU share beside the tuner

- **Measured:** the tuner's 12 lanes use 43-50% of 32 threads (design §1). An AI run gave 582-649 frames/s beside 3 AI
  runs (A0) and 349-398 beside about 13 (BP-1 round 2's `ab2` and `control2`, 08:51-09:13 on 2026-11-11: 612,596 f /
  1,754.4 s; 654,457 / 1,847.6; 666,141 / 1,675.7).
- **Rules:** P = 8, at most 12. **Singles cap (WAIT):** own launches plus other singles at most 16 (a single = a
  `pokebot.py` without `--endless-target`, the learner's `other_bots_running` rule), so `size_lanes` (`min(12, 32 − 4 −
  singles, RAM) // 4 × 4`) still gives 12 and the 8-lane wait never fires. **No start while `run_regression.py` runs
  (WAIT):** a full lane failed by a TIMEOUT under load (07 2026-10-31); `Get-CimInstance Win32_Process`. A 15 s stagger.
- The report gives frames/s per leg and per wave (P1 measures P = 6); under 300 in WP1's first wave, the lead lowers P,
  recorded. RAM 128 GB; per-run RAM UNMEASURED. Load may move a trajectory (suggestive only: decision stalls of
  100-700 ms came before a game-side split in 2 runs against 3, `e0diag/shadow/SHADOW.md` :83-84; stepping is
  synchronous, `hands/pad.py` `_count`, so load changes frames only through an unproven host-time effect,
  `e0diag/REFUTE.md` :256-258; both files lab, deleted after the merge). So frames/s stays per leg, no claim compares
  two arms' paths, and a lower P makes a leg faster, never a replay.

### 2.7 Disk (KI-129, KI-130, the learner's 25 GB floor)

- **Free** 53,218,197,504 bytes (53.2 GB) at 8:00 PM 2026-11-13 (`df -B1`; E0-2 began at
  53.6 GB). The learner's `disk_guard` stops the tuner under 25 GB (`min_free_gb`) and
  archives early under 40. **A1** refuses to start under 45 GB (D11's AI-only floor) and aborts under 40 (no launch,
  running launches killed, `ABORT.txt`, the entry ABORTED), so it never brings the learner near its stop.
- **Per leg:** a newest `world.jsonl` over 1,000,000,000 bytes (an MC job: over 1,500,000,000 bytes, live_chain's
  guard, 2.4b) is killed (CUT-WORLD); every finished one is measured,
  its last line kept, then deleted; over 300 MB (live_chain's graded cap) is reported. Measured: graded legs at most
  65.8 MB; chapters 6-7 24-97 MB; RUSTURF churn 497 MB; KI-130 774 MB; A0 / KI-129 (fixed) about 2 GB.
- **Transient** at worst 8 GB. **Out store** about 5 MB a leg (1.5 raw, 1 zipped logs,
  up to 3 of the AI's own kept files, 3.12), about 0.6 GB for WP1's 120 legs; **cap
  5,000,000,000 bytes**. **Stage:** 25.3 MB of code plus the copied starts (C worlds 91,544,456 + 13,599,098 +
  58,084,300 bytes, about 163 MB, `MANIFEST.json`; G files about 6 MB): about 0.2 GB for WP1, none copied for P1.
  Profiles are deleted per job; the main sandbox's 14 GB of old `profiles/` is not A1's.
- **Per-job budget.** A job's profile folder holds its legs' run folders (`profiles/<name>/ai_player_runs/`) and its
  memory files (`ai_player/memory.jsonl` and the `retired/` copies each `--state` leaves, launcher :205). It peaks at
  the leg in flight's `world.jsonl` (cut at 1,000,000,000 bytes) plus that leg's `actions.jsonl` (about 33 bytes a
  frame: 19,575,916 for E0 T L5's 600,000 frames, so about 40 MB for an L7), plus the finished legs' folders until the
  job's zip (about 164 MB of `actions.jsonl` for a 7-leg chain at full budgets, and about 0.6 MB of logs a leg), plus
  the memory files (up to 2,462,973 bytes each in E0's diagnosis profiles). `PROFILE_BUDGET_BYTES` = 1,250,000,000.
  An MC job (2.4b) keeps live_chain's world cut, 1,500,000,000 bytes, so its budget is `MC_PROFILE_BUDGET_BYTES` =
  1,750,000,000: the same 250 MB above its cut (an L1-L5 chain's `actions.jsonl` at full budgets is about 91 MB).
- **P fits the disk.** At start, P_fit = floor((free - `ABORT_FREE_GB` - out_estimate - stages - 2.0) / 1.25), with
  out_estimate 0.6 GB (the out store above, with the AI's own kept files) and stages 0.4 GB. The run uses min(P, P_fit),
  recorded, and refuses (exit 2) when P_fit < 1. At 53.2 GB: (53.2 - 40 - 0.6 - 0.4 - 2.0) / 1.25 = 8.2, so 8. An MC
  batch divides by 1.75 instead: 5 at 53.2 GB, above its P = 3.

### 2.8 Wall time

P1: about 1 job-hour, 20-30 min at P = 6. GM's live A/B: one chain L1-L5 and 4 L6 legs, about 1-1.5 h. MC: about
30-45 min at P = 3 (E0 41 min, E0-2 31 min). WP1: about 28 job-hours (WP1a 9 × 1.05 h: chapters 1-5 in 19.5-29.8 min a
chain in E0-2, then L6 and L7; WP1b 27 × 0.6 h; P2 3 × 0.65 h), so about 4-5 h at P = 8 with WP1b's wait for WP1a's
L5 ends and the tail, about 9 h if every L6 and L7 spends its whole budget (1,000,000 and 1,200,000 frames at 349
frames/s). The full regression lane (4.4 item 3): about 4.4 h, budgeted from upper-bound rows: its longest suite,
`revert_bossprep`, has a PROVISIONAL 15,931 s row, the next, `revert_p11`, 12,879 s (`run_regression_times.json`
calls both "upper bounds until measured alone"), and every other row is shorter (since `fa9f073d`, `revert_step5`
12,110 s, a side lane's kill time). A lane that only times out runs again (`06` 2026-11-12 item 3): about 9-10 h then.
The merge's own full lane (`07`'s merge entry) gives the measured hours, and A1's build plan reads them when it
starts.

## 3. The new code

### 3.1 Files

- **NEW:** `G/frontier_probe.py` (test side; the AI never imports it, T28); `G/test_frontier_probe.py` (4.1);
  `G/revert_frontier.py` with its mutant table (4.2).
- **CHANGED, one entry each:**
  - `G/run_units.py` `SUITES` (:42, like `test_live_chain` :102 on the merged tree);
  - `G/check_anchors.py` `RUNNERS` (:39-51: `"revert_frontier": ("MUTANTS", None)`), and `G/test_check_anchors.py`,
    whose CLI pin "9 of 9 runners" (:61-63) becomes 10 of 10;
  - `ai_player/README.md` ("Run it");
  - `G/ledger.json` (the band row, the batches' entries).
  `tools/workflows/suite_map.json` needs no entry: its `units` group covers `ai_player/**`. Whether `revert_frontier`
  also joins the full lane (`run_regression.py` `REVERTS` :207-213 plus a PROVISIONAL row in
  `run_regression_times.json`) is the lead's call; live_chain's mutants are not in the lane either. Part 0 (GM) lists
  its own AI-side files in 3.15.
- **NOT CHANGED:** `live_chain.py` (642 tests, 378 of 378 mutants killed, 07 2026-11-06); `check_grader_imports.py`,
  which is in `GRADER_GATES`, so adding the probe to its `GRADERS` would make the next graded live_chain run re-register
  (T28 calls its `scan` instead); `live_step5.py`, `launcher.py`, `ledger.py`, `ai-agent/*`. **AI play code changes
  ONLY in part 0 (GM, 3.15)**, AI-side and under its own proofs: `mode.py`, `game_memory.py`, `options.py` (the new
  `AI_PLAYER_GOALS`), the launcher side's `__main__.py` (its `--continue` refusal), their tests, and `check_purity.py`
  only if the build finds a pinned list that needs it (3.15 item 4). **So part 0 moves the play digest:** A1's live
  runs play code that E0-2 (ledger #148, on `3caf9c47`) never ran, and "a play change now would need a new live round"
  (`06` :10104). MC's first run, on the A1 commit's stage, is that round (3.15 item 8).

### 3.2 Command line

Every command is `py -3.12 -B ai_player/gates/frontier_probe.py ...`:

```
stage --commit SHA --stage DIR [--repo DIR] [--sandbox DIR] [--donor DIR] [--mutant oldale|briney] [--starts G1,...]
plan P1|GM|WP1|MC --first-seed N [--to T] > jobs.json   (pure; validates the env keys; MC sends no AI_PLAYER_GOALS)
run --jobs F --out DIR --stage ARM=DIR[,ARM=DIR] (--ledger development --prediction-file F | --trainer)
    [--parallel 8] [--deadline EPOCH] [--max-wait 7200] [--resume]
report DIR                                     (offline; from records.jsonl)
replay EXAMPLE --stage DIR --profile NAME [--seed N] [--frames F] [--code-tree DIR]
                                               (one leg again from a kept example: state, world line, goal
                                                snapshot when kept; one new trajectory, never a replication)
compare A.jsonl B.jsonl [--context N]          (offline; the first differing (frame, action), skipping 'say' and
                                                'world' records)
reserve-band [--ledger PATH]                   (once, after the merge, 3.10)
teardown --stage DIR                           (junctions unlinked FIRST)
child JOB.json                                 (internal; run from the stage)
```

Exits: 0 ran; 2 refused before any launch (no ledger write); 3 ABORTED by the disk guard; 4 harness ERROR after
`ledger.begin` (the entry finished as ERROR, live_chain's pattern); 5 an unguarded crash; 6 the AI-only stop.

### 3.3 The stage (the code root the children run)

The lab's `build_stage11.py` + `make_arm11.py`, promoted. A stage always lies outside every git work tree (3.10).

```
<stage>/code/ai_player/       git -C <repo> archive <commit> ai_player ':(exclude)ai_player/evidence'
<stage>/code/sandbox-pokebot  JUNCTION to <stage>/build
<stage>/build/                modules, plugins, mgba, roms = JUNCTIONS to <sandbox>; top-level files, profiles/*.yml|*.py
                              and cache/ COPIED; own logs/, profiles/, an empty .git
<stage>/build/profiles/       ai-fp-donor/metadata.yml from <donor> (default endless-P1-torchic; md5 kept);
                              ai-step0-fixture/ (the truth harness's profile, as build_stage11)
<stage>/starts/               <id>_end_state.ss1, <id>_world.jsonl, <id>_reads.jsonl: copies, md5-checked (2.1)
<stage>/manifest.json         repo, commit, mutant and its file, play digest (make_arm11 tree_digest(play_only=True)),
                              full digest, start md5s and starters, junction targets
```

- `--repo` defaults to the tool's checkout, `--sandbox` to its `sandbox-pokebot`. As `PACKAGE_ROOT` is the folder holding
  `ai_player/`, a child started from `<stage>/code` launches, gates and truth-reads against `<stage>/build`, never the
  main sandbox (the lab's trick, `arms11.py` `child`).
- `--mutant`: ONE anchored edit to the staged copy, refused unless the anchor hits exactly once; the manifest names the
  file and the edit's sha256.
- **The Phase A contract (decided here):** one stage per AI tree, `stage --repo "C:/Remote Projects/pokebot-ai-code"
  --commit <HEAD> --sandbox <checkout>/sandbox-pokebot --donor <profile>` (a fresh clone has no donor, design §7), never
  `--stage` at a checkout. A stage is immutable; D1's drain still precedes a fast-forward because `modules` and `plugins`
  are junctions into the checkout (the stage watch is the backstop). Whether that checkout holds `mgba` and `roms` is
  UNKNOWN: Phase A's setup smoke-tests one launch. Rejected: a work tree run in place under a `git status` check (it
  trusts every write of the AI's run to land in an ignored path; the stage is already built and tested).

### 3.4 One job, step by step (the child)

**The job dict:** `chain` (the job id), `profile` (`ai-fp-<batch>-<job>`, per `_PROFILE_NAME_RE`) and `legs` (`legs_of`
entries: `leg`, `chapter`, `target`, `proof`, `frames`, `wall`), the keys `salvage_leg` and `end_sweep` read; plus arm,
kind, start, persona, starter, seed.
1. Sanitize the environment (3.11); set `live_step5.PROFILE`.
2. `ensure_profile(build_root, profile, template="ai-fp-donor")`; no donor refuses the job (never `run_arm`'s silent
   fallback, which in the lab stages picked another job's profile).
3. `legs_of(target, staged milestones.json, {**FRAMES_BY_CHAPTER, 6: 1000000, 7: 1200000})`, walls from 2.3; a saved
   start keeps L6-L7.
4. Per leg: `STOP.txt`/`ABORT.txt` check; the `Arm` (fresh, the previous leg, or `"START"` in `carried`; its `env`
   carries `AI_PLAYER_GOALS` = the kept goal snapshot when the leg carries one, 3.15); `run_arm`;
   `judged(check_purity)`, `judged(check_after_is_this_run)` as `run_chain` does; the row; `finish_leg`; class (3.5);
   next unmet and key (3.8); experience (3.9); one line appended to `records.jsonl` under a lock; continue rule (3.6).
5. The job record; zip and verify (3.12); delete the profile (a leftover is named).

### 3.5 End classes (D14, from files; the first matching rule wins)

"Stop": the AI-only stop count (3.13). "Blk": in the blocker list when not reached. "Exp": experience written.

| # | Class | Rule | Stop | Blk | Exp |
|---|---|---|---|---|---|
| 1 | CUT-WORLD | the probe's guard killed the launch (its kill marker) for `world.jsonl` over 1 GB (an MC job: over 1,500,000,000 bytes, live_chain's guard, 2.4b), or for the job's profile folder over its budget (3.12) | resets | yes: "harness cut: world.jsonl over 1 GB (a churn, KI-129/KI-130)"; for an MC job "over 1.5 GB"; for the profile cut "profile folder over budget" | no |
| 2 | INFRA | a purity-gate TIMEOUT: exit 7 with "FAIL the purity gate did not finish within 180s" in `run.stdout` (an `[AI-GATE]` line); `run.driver_killed` (the launcher overran wall + 300 s, gate included); `launch_died`; a kill by the probe's ABORT; a leg salvaged by `salvage_leg` | neither | no | no |
| 3 | REFUSED | exit 7 with any other gate text; exit 2 with no verdict file (`cmd_run`'s refusals before a launch); the child's own refusal (profile, donor, start custody) | counts | no | no |
| 4 | HUNG | exit 124 with NO verdict file: the launcher's hard kill at the wall clock, which it reads as "a stuck run"; the soft deadline exists so a run merely out of time ends WITH its verdict (`soft_deadline_margin`) | counts | yes: "launcher hard kill at the wall clock, no verdict (a hung brain)" | no |
| 5 | NOT CLEAN | exit 8 (`NO_VERDICT_EXIT`: exit 0 with no certified CLEAN verdict); a verdict word other than `CLEAN`; any other exit with no verdict file | counts | no | no |
| 6 | INFRA | a `CLEAN` verdict whose L5.THIS_RUN fails (not fresh), or whose end truth cannot be read | neither | no | no |
| 7 | CLEAN-BUDGET | CLEAN, fresh, and a host end `wall-clock` (exit 124 WITH a verdict) or `frame-budget` (exit 4) per `_HOST_CODES`; or exit 0, `play: stopped:` and the verdict's `counters.real_frames` >= the leg's frames (the launcher's `_ran_out`, which `_classify_session` calls BUDGET) | resets | yes | yes |
| 8 | CLEAN-INVOLUNTARY | CLEAN, fresh, another `_INVOLUNTARY` host end (crash 2, parked-manual or abandoned 3, interrupted 130) | resets | yes | yes |
| 9 | CLEAN-CHOSEN | CLEAN, fresh, exit 0, and `play: done:`, `play: stuck:`, or `play: stopped:` with the budget NOT run out (the launcher's "its own choice") | resets | yes | yes |

- `frame-budget` is a budget end here though the launcher lists it in `_INVOLUNTARY`: that table answers whether a game
  may be CONTINUED (D12); A1 asks who ended the leg. **Judged legs** (the denominator) exclude REFUSED, NOT CLEAN, INFRA.
- **CUT-WORLD and HUNG** have no verdict and cannot pass L5.THIS_RUN. Their end map is the kept world tail's current map,
  else UNKNOWN; their next unmet is read on the end truth if the end state was written after the start with a new md5,
  else on the start truth (`next_unmet_from` says which).
- **Claim mismatch:** a CLEAN-CHOSEN `done: <target> reached` whose proof does NOT hold is `reached: false`,
  `claim_mismatch: true`, a blocker (D4's cross-check, Phase A test 5).

### 3.6 The continue rule (a chain's next leg)

The next leg runs only when: **C1** `leg_reached`; **C2** the class is CLEAN-* and every `PURITY_IDS` check PASS; **C3**
the world was measured and its kept last line parses; **C4** not guard-cut; **C5** custody (the next start's md5 equals
the kept `end_state.ss1`, its `world_in` sha256 the kept line's, its goal snapshot's sha256 the kept
`goals_last.jsonl`'s when one is carried (part 0), the env keys the allow-list); **C6** no `STOP.txt`. The
world size is REPORTED, not a condition (`WORLD_SIZE_KIND` GRADED stops a graded chain on a churn; a probe wants to see
what follows). `continue_after` is not used: its C5 (`custody_problems`) assumes a New Game first leg and its C3 grades
the 300 MB cap; T27 asserts the two differences: that cap, and the goal snapshot an
A1 leg carries (part 0). The one exception is MC: an MC job decides by `continue_after` itself (2.4b), its New Game
chains being the case that C5 assumes.

**A leg boundary is a session boundary.** The next leg starts with the end state, the kept world line and, with part 0,
the kept goal snapshot. Everything else restarts: the explorer's in-session marks (`WorldMemory.unreached`,
`cut_off`, `spent`, which are not in `world.jsonl`; and the fix round's session-only standing walls); `GOAL_RESET`;
and, without a snapshot (`goal_memory: none`), also `GOAL_KEEP`, the personality's draws, the battle mind and the loss
count. A chain is one game played in N sessions, not continuous play. `measures.stale` (3.7) measures the cost per
tile.

### 3.7 Records (schema_version 1; one JSON line each in `<out>/records.jsonl`)

- **A leg record:** `schema_version` 1; `record` "leg"; `run_id` `<batch>-<arm>-<job>-<leg>` (unique; a resume never
  writes one twice); `batch` {name, mode development|trainer, ledger, started}; `tree` {arm REAL|WALL-OLDALE|WALL-BRINEY,
  commit, play_digest, digest, mutant}; `job` {id, kind chain|practice, origin new_game|practice, persona, starter,
  starter_from job_file|truth_party|plan, seed, legs_planned, start {id, state_md5, world_md5, made_by, reads_carried}};
  `leg` {leg, chapter, target, frames, wall}; `launch` {exit, elapsed, fps, driver_killed, guard, env_keys,
  command_sha256}; `verdict` {word, exit_reason (untrusted, utf8-safe, at most 300 chars), real_frames}; `fresh` {ok,
  text}; `class`; `reached`; `claim_mismatch`; `truth` {before, after: {map, frame}}; `milestones_held`; `next_unmet`;
  `next_unmet_from` end|start; `next_unmet_unread`; `end_map` {pair, const}; `blocker` (null, or {key: [chapter,
  next_unmet, reason_norm, end_map_const, class], key_id: 12 hex of the key JSON's sha1}); `measures` {world_bytes,
  world_over_300mb, world_deleted, log, loop, k1_leads, stale}; `start_memory`; `bossprep`; `rides` (the next
  bullet); `experience` {written, fights, unclassified}; `kept` {folder, zip, zip_sha256,
  raw: end_state.ss1, world_last.jsonl and, when present, goals_last.jsonl and the AI's save and memory files, 3.12};
  `notes`.
- **The fields the 2026-11-13 amendments add:**
  - `start_memory` {`goal_memory` carried or none, `goals_sha256` (of the start's kept snapshot, carried or not; null
    without one), `losses_carried` (the carried snapshot's loss count, else 0), `fallback_for` (a WP1b fallback's
    pair, else null)} (3.15, 2.1).
  - `measures.loop` {pair, crossings, crossings_raise, share of the leg's transitions, window [first, last frame],
    window_share ((the pair's last crossing - its first) / the leg's frames; reported, never a rule), last_to_end
    (the frames from the last crossing to the leg's end, which condition (4) reads), pingpong_ends (`goal_end` records
    whose reason begins `stuck: ping-pong`),
    transitions_in_leg, maps_entered, keyed LOOP or flag or none} (3.8).
  - `measures.k1_leads` {count; per lead: goal map, lead map, first frame}, read from the `tell` records of the form
    `[AI-GOALS] <map> is somewhere it has not been: first to <lead>, a seasoned player's knowledge: ...`
    (`brain/goals.py` `WAY_IN` :875, `entry_lead` :878-906, the tell :3699 at `3caf9c47`), so a chapter-5 stop or LOOP
    says whether K1 fired.
  - `measures.stale` {`snapshot`: the yardstick, the start's kept `goals_last.jsonl`: `carried`, `kept` (present at
    the start but not carried: GM's GOALS-OFF arm, 3.15 item 7) or `none`; `item_errands`: the DISTINCT tiles of that
    snapshot's `tried_items` for which the leg has a `not picked up: no item ball where it lay at (x, y) any more`
    outcome (read by the `goal_end`'s key `item:<map>|x,y`); `item_outcomes`: those outcomes, counted;
    `gone_or_unreachable`: the same message for any other tile (the fix's E makes it fire for a ball merely out of
    reach, `goals.py` `_back_to_ball` :3367-3391); `item_errands` and `item_outcomes` are `unknown` only when the start
    has no snapshot at all (`snapshot: none`: G1-G6, C1-C3), and `gone_or_unreachable` then counts every such outcome;
    `memory_line`: the AI's `[AI-WORLD] memory from ...` line}.
  - `bossprep` (AI-written lines, reported, never a class): `acting` (Story and Catcher act; a Trainer only logs,
    `brain/bossprep.py` :156); `plan` {boss, trainee species, from L, target L, the option drawn} or
    `no plan (<why>)`; `raise_goals` (`goal` records of action `raise`) and `raise_battles` (`raise battle:` lines);
    `raise_end` (budget spent, target reached, trainee left, or still active at the leg's end); `boss_losses`
    (`a battle lost on the gym map (N so far` lines) and `other_losses`; `frames_from_plan`.
  - `rides` (from the world tail): the rides used in the leg (a `uses` delta against the start's line) and the ones
    found `closed`.
- **A job record:** {schema_version, record "job", job, legs_ran, stopped_at, stop_reason, reached_last,
  profile_deleted}. `report` refuses an unknown `schema_version` (exit 2): Phase A test 14.

### 3.8 The blocker key, clustering and the report (D7)

- **Next unmet milestone:** the first entry of the staged `milestones.json` (file order; optional entries and waypoints
  skipped) whose proof does not hold on the END truth's marks (`proof_holds`), or the start truth per 3.5. A proof whose
  mark the truth did not return goes to `next_unmet_unread`, never counted. The merged `milestones.json`
  holds chapters 6-7's marks (36 milestones; `play_harness.tracked()` reads `knowledge/milestones.json`).
- **The key:** `(leg chapter, next_unmet, reason_norm, end_map_const, class)`, or the LOOP key
  (below). `reason_norm` = `untrusted_text
  (exit_reason)` or the class's text, digit runs made `N`, whitespace collapsed, cut at 160 characters (`play: stuck: 3
  battles lost (MAX_LOSSES 3)` → `play: stuck: N battles lost (MAX_LOSSES N)`). A not-reached CLEAN-BUDGET leg
  whose `raise` goal is still ACTIVE at its end (a `goal` record with no `goal_end` after it in `actions.jsonl`) gets
  `reason_norm` `budget: a boss-prep raise still active` (the raise runs in L6, 2.3) and keeps its own key, never the
  LOOP key (its condition (5), below).
  `end_map_const` = the constant whose
  "group:number" in `rate_step5.map_keys()` is the end truth's `map`, else `UNKNOWN` (no framework import).
- **The loop signature** (every leg; from the kept `world_last.jsonl`, read as JSON with no AI import): its
  `transitions` (`[frame, source, target, how, by, tile, arrival, direction]`, `WorldMemory.to_dict` :916-917 at
  `3caf9c47`) newer than the start truth's frame (a carried prefix is the previous kept line's list). Per unordered map
  pair, count the crossings either way, edges and warps alike, maps named by the snapshot's `maps[key].const`.
  `crossings_raise` counts the crossings made while a `raise` goal is ACTIVE (after its `goal` record in
  `actions.jsonl`, before its `goal_end`). `measures.loop` (3.7) keeps the top pair, its window and the AI's own
  `stuck: ping-pong` goal ends.
- **The LOOP key (D7 changed):** `(leg chapter, "-", "loop", "<A>|<B>", "LOOP")`, A and B the top pair's map
  constants, sorted. It replaces the key above when ALL hold: (1) not reached; (2) the crossings less
  `crossings_raise` reach `LOOP_MIN_CROSSINGS` (40, both directions); (3) an end where time or space ran out:
  CLEAN-BUDGET, CLEAN-CHOSEN whose `reason_norm` begins `play: stuck: no progress`, or CUT-WORLD; (4) the loop runs
  into the leg's end: its last crossing lies at most `LOOP_END_FRAMES` (120,000 = `STORY_PATIENCE`, `mode.py` :112)
  frames before the leg's end; (5) no `raise` goal is ACTIVE at the leg's end (the raise comes first: such a leg keeps
  its own key, on a CLEAN-BUDGET end with the reason `budget: a boss-prep raise still active`, above). A leg that meets
  (1) and (2) but fails (3), (4) or (5) keeps its own key, its record says `measures.loop.keyed: "flag"`, and the
  report lists it in a "loops seen" table beside that key, so a different, discrete end (a battle-loss stop, a wedge, a
  crash), or a loop that ended long before a later end, is never hidden. LOOP is a key label, never a D14 class: the
  stop logic is unchanged, and the record keeps all five raw key values. Calibrated on E0's two loop legs (118 and 74
  crossings; last crossings 92,013 and 20 frames before their ends; their window shares, 0.60 and 0.82, are reported,
  never a rule); the other not-reached legs measured had 5 and 6 (BP-1 round 4's `ab4g-6426` and `-6427`, ledger
  #132), and BP-1's reached raise runs at most 20, 10 of them during a raise (the counts: the repo note
  `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.4). Both constants are pre-registered in the prediction file.
- **Churn:** a REACHED leg with `crossings - crossings_raise >= 40` goes in a "churn" table (count, frames in its
  window), never ranked (E0-2's T L3 reached with 92 crossings).
- **No live loop kill:** a leg runs to its own end (USER RULING 55; E0 T escaped its loop and beat the grunt).
- **Ranking** per (`tree.play_digest`, chapter) on the exact key; share = count / judged legs, excluded counts shown
  beside it; ties by key text. **Per blocker:** count, share, real frames (min, median, max), counts per persona ×
  starter, up to 3 examples newest first; for a chapter 6-7 key, the boss-prep breakdown (plan
  made, raise ended by its budget, trainee reached its target, a Trainer that only logged) and the battles lost carried
  in against lost in the leg (3.15). **Per chapter:** reach = reached / judged, frames/s, class counts with
  CLEAN-BUDGET apart from CLEAN-CHOSEN, and reach split by start kind: new game; chain leg with a goal snapshot; chain
  leg without; practice with a snapshot; practice world-only (`goal_memory: none`).
- **Files:** `<out>/blockers.json` and `blockers.md`, rebuilt by `report`, headed "DEVELOPMENT DATA, NEVER A GRADED
  PROOF; PROJECT KNOWLEDGE/ai-frontier.txt is the authority" (D4). Trees sharing an `--out` are ranked side by side.

### 3.9 The experience extract (D16; written, never read by the AI in A1)

**Static facts by ALLOW-LIST**, from the leg's kept `world_last.jsonl` (the `WorldMemory.to_dict` snapshot,
`ai_player/world/memory.py`), read as JSON with no AI import. The symbols are the citation; lines are given at
`3caf9c47` (the merged tree with the chapter-5 fix) and re-read at the final head before the build:
- **World:** `warps` as `{key: {to, arrival, direction, inferred}}`, dropping `uses`, `first`, `last`, `by` (the warp
  graph's doc :484; written :745-746, :755, :792); `connections` as `{source, target, direction, from, arrival, offset}`,
  dropping `by`, `frame`, de-duplicated; `landmarks`; `rides` as
  `{name: {from, to, arrival, who, gfx, tile, words, place, via}}`, dropping the per-game `first`, `last`, `uses` and
  `closed` (`record_ride` :588-598, `close_ride` :614-619; `brain/rides.py` :176-178 records the ride, whose `frame`
  `record_ride` does not keep); any other ride key is dropped AND listed in `unclassified`.
- **Per map** (`MapMemory.to_dict` :413): `key`, `name`, `const`, `tile_fields`; `tiles` with only the first 4 of
  the 7 compact fields (flags, ledge, elevation, behavior: `TileFact.compact` :216), never `seen_frame` or
  `seen_from`; the 7 names are hard-coded, and a map whose `tile_fields` (:417) differs is dropped and listed in
  `unclassified` (fail closed); `edges` (:426); `bumped` as `{tile|direction: {from, direction, slid}}`, `slid` only
  when present (a muddy slope that slides the player back, a static map fact: `learn_slide` :824-840), dropping
  `first`, `last`, `bumps` (:257, :420); any other bump key is dropped AND listed.
- **Per-game facts dropped:** per map `visits`, `closed`, `people`, `persons`, `met`, `items`, `arrivals`,
  `first_frame`; world `transitions`, `tiles_learned`, `news`, `heard`, `news_log`, `spoke`. **Any other key is dropped
  AND listed** in `unclassified`; the report prints a non-empty list, and T16 fails on one.
- **Fights** from the kept `actions.jsonl` (`live_step5.is_battle` :739-741, `battle_records` :744-747): per trainer
  battle, the foe as shown (the newest earlier `tell` "battle: a trainer battle against", `tells` :702-705;
  no other tell is read, so a K1 lead's tell, "... a seasoned player's knowledge: ...", never names a foe), the party as
  the AI saw it (the record's `party=[…]`, `arms11.py` `_PARTY`), outcome and map; wild battles counted met, won, lost,
  ran. Never the truth's fields (PIDs, experience): live hidden state (USER RULING 40).
- **Outputs:** `<out>/experience.jsonl`, a row per CLEAN-* leg {schema_version, run_id, tree, origin, chapter, leg,
  persona, starter, end {map, class, reached}, fights, wild, maps_sha256, unclassified}, `origin` `practice` for saved
  starts and `new_game` for chains (USER RULING 55); `<out>/experience_maps.json`, the deterministic UNION of the
  batch's static facts (first seen wins, conflicts listed; at most the 518 maps of `knowledge/world/maps.json`).

### 3.10 Modes, and where a batch may write

**Placement, both modes.** `--out` and every stage lie outside every git work tree (`git rev-parse
--is-inside-work-tree` fails from the nearest existing folder), ignored or not, and outside any `pokebot-learner` folder
(live_chain R8; the `--repo` and `--sandbox` junction targets too), else exit 2 before any ledger write. **So Phase A
keeps its AI store outside the learner clone** (for example `C:/Remote Projects/_ai_train/`) and copies the records it
keeps into the learner's `data/ai_runs.jsonl`, de-duplicated by `run_id` (D11). Rejected: `--out` in the clone's ignored
`ai-agent/data`: the bot's freeze watch (`x4_headless.py`, design §1) watches it, and one stray file aborts a bot cycle.

**`--ledger development`:** seeds one contiguous range, none named by any entry; `ledger.begin("story",
"frontier_probe", "development", first, last, bounds, tree)` BEFORE the first launch (`bounds` = the sha256 of
`jobs.json`, the prediction file, `frontier_probe.py` and every stage manifest; `tree` = the REAL arm's play digest); at
the end the evidence file `ai_player/evidence/<date>-a1-frontier-<batch>.txt` (header, leg lines, report, experience
counts, CPU and disk measures, the prediction file and its sha256), then `ledger.finish` "DEVELOPMENT, never graded: …"
(or ERROR, ABORTED).

**`--trainer`:** seeds in 2,000,000-2,999,999; `ledger.json` (READ ONLY) must hold the band row (family `story`, purpose
`development`, status `done`, first 2000000, last 2999999, note `AI trainer band`) and no overlapping `registered`
entry, else exit 2 (D13). It NEVER writes `ledger.json`, `ai_player/evidence/**` (no `provenance.snapshot_tree` with its
default folder, `provenance.py` :529), or a file `git ls-files` lists in the orchestrator's repository or the `--repo`.

**`reserve-band`** (once, after the merge; refused if a band row exists): `ledger.begin("story", "frontier_probe",
"development", 2000000, 2999999, <sha256 of the D13 text>, None, note="AI trainer band")`, then `ledger.finish(id,
"RESERVED: the AI trainer band (D13); never played by a session", None)`, then `py -3.12 -B ai_player/gates/ledger.py
--check` must exit 0. The session commits `ledger.json` by explicit path.

### 3.11 The child's environment (D17's allow-list)

- **At the child's start**, before any launcher import, every `AI_PLAYER_*` (`AI_PLAYER_BUILD_ROOT` included, as
  `arms11.py` pops it), every `POKEBOT_*` and every `PYTHON*` that `python_env_refused` refuses is removed from
  `os.environ`. `run_arm`'s `clean_env` strips only `AI_PLAYER_*`, so without this `POKEBOT_BOSSMODE_TOPUP` or
  `PYTHONPATH` would reach the launch.
- **A job's env** may name only these (`plan` and `run` refuse any other key, exit 2), lines in `ai_player/options.py`:
  `AI_PLAYER_BRAIN` :138 (always `play`), `AI_PLAYER_SEED` :163, `AI_PLAYER_PERSONALITY` :165, `AI_PLAYER_STARTER` :232
  (fresh legs only), `AI_PLAYER_TARGET` :228, `AI_PLAYER_CLOCK` :170 (always "10:00"), `AI_PLAYER_WORLD` :189.
  Part 0 adds an eighth key, `AI_PLAYER_GOALS` (its `options.py` line is new, beside `ENV_WORLD` :189): the
  kept goal snapshot, only on a leg that carries one (3.15), checked in custody by sha256 (C5); an MC job never sends
  it. `AI_PLAYER_CONTINUE` :247 is unused: A1 never continues a game (D12). `AI_PLAYER_MEMORY` :245 is never a job key:
  the launcher sets it itself (`__main__.py` :190), and `--state` archives the profile's memory file first (launcher
  :205), so without part 0 every `--state` leg begins a new goal memory. Every leg record states
  `start_memory.goal_memory`.
- **A planted wall is CODE in a staged copy, never an env switch.** The probe refuses every FAULT switch.

### 3.12 Disk caps and retention

- **A1's own** `frontier_probe.disk_decision(world_bytes, free_gb, out_bytes)`, constants `WORLD_CUT_BYTES =
  1_000_000_000`, `ABORT_FREE_GB = 40.0`, `START_FREE_GB = 45.0`, `OUT_CAP_BYTES = 5_000_000_000`,
  `PROFILE_BUDGET_BYTES = 1_250_000_000`; for an MC job (2.4b) the world cut `live_chain.GUARD_WORLD_BYTES`
  (1_500_000_000, read from live_chain, never copied) and `MC_PROFILE_BUDGET_BYTES` = that + 250_000_000
  (1_750_000_000) (the free-space values in
  `safe_free`'s unit). Strict comparisons: each boundary value passes.
- **Start:** refused when free < 45.0 on the drive of `--out` or a stage. **Each 5 s tick, in order:** free < 40.0 →
  ABORT; newest `world.jsonl` > 1,000,000,000 bytes → kill (CUT-WORLD); `--out` > 5,000,000,000 → DROP pending jobs;
  a running job's profile folder > 1,250,000,000 bytes → kill (CUT-WORLD's rule; reason "profile folder over budget").
  An MC job (2.4b) is cut by live_chain's world guard instead, newest `world.jsonl` > 1,500,000,000 bytes, and by its
  profile budget, > 1,750,000,000 bytes; never at 1,000,000,000 or 1,250,000,000.
- **A job's end:** zip the folder, verify it (`testzip()` is None; members and sizes equal the raw files), ONLY then
  delete the raw files but each leg's `end_state.ss1` and `world_last.jsonl` (the example; Phase A's pool state),
  and, copied into the leg's kept folder BEFORE the profile is deleted, each when present: `goals_last.jsonl` (part 0),
  the profile's `current_save.sav`, `ai_player/memory.jsonl` and `ai_player/launches.jsonl` (about 1-3 MB a leg; a
  memory file exists only once the AI has saved in that game, `game_memory.py` :16; an absent one is recorded). A
  failed zip keeps the raw folder, recorded. `end_sweep` re-deletes any leftover `world.jsonl`.
- **`teardown`** unlinks every junction FIRST (a recursive delete through one would delete the main sandbox's
  `modules/`), then deletes the stage. It prints the main sandbox's counts of `modules`, `plugins`, `mgba` and `roms`
  before and after (they must read unchanged). Before any delete, a junction scan of the stage folder must find none.
  This is the rule of the kit that staged the merged code (`stage_merge.py` :8-17 and `find_junctions.py` :1-6 from
  `_ai_lab/s53/mergeplan/`, `stage_diag.py` from `_ai_lab/s53/e0diag/`: lab; their copies are kept in
  `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/`, `scripts/` and `mergeplan/`, sha256 in its README.txt,
  this PC only, not git; E0's diagnosis and its shadow replay tore down every stage this way). It is stated here in
  full, so `stage` and `teardown` need only the 1.2 lab kit's `build_stage11.py` and `make_arm11.py` (3.3; kept copies,
  1.2) and this text.

### 3.13 The scheduler, stops, the stage watch, resume and the deadline

- **Scheduler:** A1's own loop of `schedule`'s shape (at most P, the stagger, `tick` after every pass), since `schedule`
  drops every job `may_start` refuses. The start check returns GO, WAIT, SKIP or DROP. **DROP** (to `not_started` with the
  reason, for good): the deadline; the `--out` cap; `STOP.txt`, `ABORT.txt`, the AI-only stop; a WAIT past `--max-wait`
  (default 7,200 s). **WAIT** (the job stays first in line, nothing launches this pass, re-checked next tick): the
  singles cap; a running `run_regression.py`; the disk reservation (free minus the sum, over running jobs, of the
  job's profile budget, 3.12, less its profile folder bytes, is under `ABORT_FREE_GB` + 2.0: so concurrency alone never
  ABORTs a batch). **SKIP** (per job, never global: the job keeps its place in line, the jobs behind it are checked in
  the same pass, so a ready one launches; re-checked next tick; no `--max-wait` clock runs while it waits on its
  dependency): a WP1b job whose source chain has no reached L5 record yet (2.4). When that chain ENDS without one (it
  stopped before L5, or its L5 missed `ch5_rival_meet`), the job takes its fallback start (2.1) at once. Only time in
  a WAIT counts toward `--max-wait`.
- **AI-only stop:** 5 legs in a row, by end time, of REFUSED, NOT CLEAN or HUNG: no new launch,
  `<out>/AI-ATTENTION.txt`, exit 6, NEVER the learner's `ATTENTION.md`. CLEAN-* or CUT-WORLD resets; INFRA does neither.
- **Stage watch:** each stage's digest every 60 s; the junctioned sandbox's tracked `modules/` and `plugins/` hashed at
  the start and every 10 min. A change writes `STOP.txt`: no new leg, running legs finish and say STOP (D1's drain).
- **Resume** (`--resume`): jobs with a job record are skipped; otherwise finished legs are kept, the leg in flight is
  salvaged (`salvage_leg`) as INFRA, later legs NOT RUN. **Keyed by `run_id`** (arm, job, leg), never the seed (shared
  on purpose, 2.5); no `run_id` written twice (Phase A's `adopt_unfinished`).
- **Deadline:** no launch when `now + wall + 300 + 2 × 600` would pass `--deadline` (`chain_watchdog_seconds`; Phase A
  test 7). A child alive past its job's summed watchdog is killed and salvaged. A Windows restart was pending on
  2026-11-11 (`tools/status.py`): WP1 starts after it, or with `--resume` ready.

### 3.14 What it must never do

Run without the real launcher, or use `play_harness` as the engine (D2). Start from a bot save or a harness-placed state
(D3). Move `ai-frontier.txt`; only a graded `live_chain` run does (D4). Import or be imported by AI play code (T28).
Write in `C:/Remote Projects/pokebot-learner`, `_livechain/graded-ch5` or the main sandbox's `profiles/`, or accept a
path under a folder named `pokebot-learner`. Edit `live_chain.py` or `check_grader_imports.py`.

### 3.15 Part 0 (GM): the goal memory a test start carries

`06` 2026-11-12 item 4 makes a test start "the emulator state PLUS the AI's world memory PLUS its goal memory". No
harness can give the third today: `--state` archives the profile's memory file (launcher :205), the launcher sets
`AI_PLAYER_MEMORY` itself (`__main__.py` :190), and the play brain refuses an existing memory file outside a continue
(`mode.py` :460). So part 0 is AI-side code, built and proven BEFORE A1's runner relies on it. Lines are at `3caf9c47`.

1. **The end snapshot.** At every end the play brain controls (`done`, `stuck`, `stopped`, the soft deadline) it appends
   ONE line to `<run_dir>/goals.jsonl` through `runlog.RecordFile` (the play side writes files only through `runlog.py`
   and the instrument, `check_purity.py` FILE_WRITERS :639-642): the save payload without its world (`game_memory.py`
   `build_payload` :447: `goals_part`, the personality, the battle mind, the registry, the loss count). A hard kill, or
   the probe's CUT-WORLD kill, leaves none; such a leg never continues (3.6 C2). The leg's end keeps the line as
   `goals_last.jsonl` beside `world_last.jsonl`.
2. **The restore, at a `--state` start given `AI_PLAYER_GOALS`** (a new `options.py` key beside `ENV_WORLD` :189):
   - RESTORED, as a continue restores them: every `GOAL_KEEP` field (`game_memory.py` :137-162: `tried_items`,
     `talked`, `pages`, `looked`, `scene_walls`, `fight_prep`, ...) except the two below; the personality
     (`restore_personality` :424: base, favourite, history, draws; another base is refused); the battle mind
     (`restore_battle` :441); the Pokemon registry (`MonRegistry`).
   - RESET: `GOAL_RESET` (:164-180), as in a continue; and R1's save fields `last_save` and `saved_for` (:160-161,
     `R1_NEW_FIELDS` :188). A `--state` start empties the cartridge (`__main__.py` :191: cart `empty`), so there is no
     AI save to remember; kept, they would make the save policy skip a due save for a save that is not there
     (`brain/saving.py` :150-155, the gap rule; :205-209, `before_leader`).
   - CARRIED: the loss count. One game has one loss count, as a continue keeps it (`mode.py` :796-797: "MAX_LOSSES
     counts across processes; new ones on top"). Each leg records `losses_carried`, and the report splits carried from
     in-leg losses (3.7, 3.8). Measured (one trajectory per chain): of 9 chapter 1-5 chains none would have ended a leg
     early, 2 would enter chapter 6 with 2 losses (#101's LC-S-6202, E0's LC-T-6483), and 1 of BP-1 round 4's 4 BRAWLY
     wins (`ab4g2-B4-C1-6429`, ledger #133) came on its third try (counted in the repo note
     `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.2). A1's BRAWLY numbers are therefore not BP-1's (0 carried, from
     C1): any comparison names this.
   - The world memory still comes only from `AI_PLAYER_WORLD`; the snapshot holds none.
   - REFUSED before play: `AI_PLAYER_GOALS` with `--continue` (D19's rule, as for `ENV_WORLD`: `options.py` :414-418,
     `__main__.py` :157-159), without `AI_PLAYER_WORLD`, or a file that is not one parseable line.
3. **Launcher side.** `child_env` (launcher :775-784) already passes every `AI_PLAYER_*` key (`UNTRUSTED_ENV` :116
   names only `PYTHON*` keys). Part 0 adds only the `--continue` refusal to `__main__.py`, a `LAUNCHER_FILES` file
   (`check_purity.py` :171).
4. **Purity and the graded driver.** If the build finds `check_purity.py` needs an edit (a pinned env name or writer
   list), that edit is part 0's, and live_chain's next graded run re-registers its grader files (`GRADER_GATES`
   :292-295 holds `check_purity.py`). The merge forces that re-registration anyway: `revert_step5.py`, also in
   `GRADER_GATES`, differs between `934ddb7f` and `3caf9c47` (blobs `20c48244` and `ad15e8f5`).
5. **Who carries a snapshot.** Every A1 leg started from a kept state carries the previous leg's (or the start's) kept
   snapshot (`start_memory.goal_memory: carried`). A start with none (G1-G6, C1-C3) runs with `goal_memory: none`,
   labelled and counted apart; a leg after a hard kill never runs (item 1). GM's GOALS-OFF arm (item 7) also runs with
   `goal_memory: none`, from a start that has one: that kept snapshot is still the yardstick of its stale errands
   (`measures.stale`, 3.7). MC never carries one (2.4b).
6. **Offline proofs, before any live run** (each with a mutant, 4.2): the P11-x repro as FAULT and CONTROL
   (`ai-research-notes/2026-11-12-P11-X-DETOUR-DIAGNOSIS.md` :51-58, beside this spec after the merge:
   `_remembered_ball` gives (17, 7) with a new goal memory and None with `tried_items = {"24:7|17,7"}`), so the restore
   switched off gives (17, 7) and on gives None; `last_save` and `saved_for` planted in a snapshot are absent after a
   `--state` restore and kept by a continue; a snapshot with 2 losses ends the run at its first new loss (MAX_LOSSES
   3); each refusal of item 2; the end line written at each end the brain controls and absent after a hard kill
   (stub). The purity gate, the quick gates and the DUE suites green.
7. **Live A/B** (after A1's runner exists, beside P1; plan `GM`, seeds 6604-6606). One diagonal New Game chain L1-L5 on
   seed 6604 makes the start. BEFORE any A/B launch the per-tile discriminator is computed offline on its L5 end: the
   tiles of the end snapshot's `tried_items` that are remembered item tiles (`MapMemory.items`) of a map the next leg
   starts on or crosses early (RUSTBORO_CITY, ROUTE116, ROUTE104), that is, tiles `_remembered_ball` offers with a new
   goal memory and not with the snapshot. With at least one, arms GOALS-ON and GOALS-OFF run L6 from that end on seeds
   6605 and 6606 (paired). The measure is `measures.stale.item_errands` (3.7), per tile, counted in BOTH arms against
   their common start's kept `goals_last.jsonl` (GOALS-ON carries it; GOALS-OFF keeps it but does not carry it):
   predicted 0 in every GOALS-ON leg and at least 1 in every GOALS-OFF leg. With none, the A/B is VACUOUS, is not run,
   and is reported so; the chain's earlier leg ends are tried the same way; with none anywhere, part 0 rests on item 6
   plus the live custody records, named as such.
8. **The play digest moves.** Part 0 is play code, so the A1 commit's play digest differs from that of the tree E0-2
   ran (ledger #148: `3caf9c47`), and "a play change now would need a new live round" (`06` :10104). That round is
   MC's first run (2.4b; build step 6): on the A1 commit's stage, it MUST read PASS before WP1. On every later merge MC
   runs as 2.4b says.

## 4. Tests and proof

### 4.1 Offline tests (`test_frontier_probe.py`)

Stub legs only, no emulator. Each guard has a FAULT that must fire and a CONTROL that must not; every FAULT is also shown
to FAIL on a copy with its guard removed (4.2). A test that plants a milestone puts it AFTER the real file's last
chapter (`test_live_chain.py` `case_no_budget` :487-493 on the merged tree: a chapter-6 milestone behind chapter 7 is
refused BACKWARDS).

| # | Guard | FAULT (must fire) | CONTROL (must not) |
|---|---|---|---|
| T1 | REFUSED | exit 7, gate text "FAIL ..."; exit 2, no verdict file | exit 2, CLEAN verdict, `crash`: CLEAN-INVOLUNTARY |
| T1b | gate timeout | exit 7, "FAIL the purity gate did not finish within 180s": INFRA; 5 never trip the stop | other gate text: REFUSED |
| T2 | budget ends | fresh, CLEAN: exit 4; exit 124 WITH a `wall-clock` verdict; exit 0 `play: stopped:` with `real_frames` = frames: CLEAN-BUDGET | `play: stopped:` at frames − 1: CLEAN-CHOSEN |
| T2b | missing verdict | exit 124, no verdict: HUNG, a blocker, 5 in a row trip the stop; exit 8, or exit 1 with no verdict: NOT CLEAN | `driver_killed` with no verdict; a `launch_died` row: INFRA, neither counting nor resetting |
| T3 | freshness | end state byte-identical to the start; frame off by over 5; mtime before the start: INFRA | a fresh state: a CLEAN class |
| T4 | NOT CLEAN | verdict `NOT CLEAN`, exit 0 | CLEAN |
| T5 | claim mismatch | `done: ch6_dewford reached`, proof false: not reached, mismatch, blocker | proof true: reached |
| T6 | clustering | one reason, other numbers: ONE key; two LOOP legs on one pair with other next milestones, classes (CLEAN-BUDGET, and CLEAN-CHOSEN `stuck: no progress`) and end maps: ONE LOOP key, count 2 | non-LOOP legs with another next milestone, class or end map: TWO |
| T7 | next unmet | `ch6_old_rod` (optional), `ch3_route104` (waypoint) never chosen; an absent mark listed UNREAD; a HUNG leg ending at its start: START truth | all marks present: the first unheld, `next_unmet_from: end` |
| T8 | ranking | two trees: the planted wall first on its own, absent on the other, its legs read by their records' `next_unmet` under their own key or a LOOP key alike; INFRA, REFUSED, NOT CLEAN never in the denominator | no blocker: empty list, excluded counts shown; a tree whose only LOOP key's records never name the wall's milestone shows no wall |
| T9 | env allow-list | `AI_PLAYER_FAULT_NO_HINTS=1`, `POKEBOT_BOSSMODE_TOPUP=1`, `PYTHONPATH=x` in the parent never reach the launch (`subprocess.Popen` replaced in `live_step5`); a job naming `AI_PLAYER_FAULT_*` refused by `plan` and `run` | the 8 keys arrive (`AI_PLAYER_GOALS` only on a leg that carries a snapshot, never on an MC job); the command line byte-identical |
| T10 | trainer writes nothing tracked | stub `--trainer` batch from a temp git repo (also `--repo`) with committed `ledger.json`, `evidence/`, `evidence/trees/`: `git status --porcelain --untracked-files=all` unchanged | development mode there shows changes; with `begin`, `finish`, `snapshot_tree` patched to raise, trainer passes, development raises |
| T11 | placement | either mode: `--out` or stage in a work tree (ignored or not) or a `pokebot-learner` folder, or no valid `manifest.json`: exit 2, no ledger write | outside every work tree: accepted |
| T12 | seed band | trainer seed outside the band; no band row; an overlapping `registered` entry; on a temp ledger, `register` inside the band raises `Refused`; a second `reserve-band` | inside: accepted; `register` outside: accepted; `reserve-band` writes one row `ledger.py --check` and the trainer accept |
| T13 | development seeds | a seed named by any entry: refused; `begin` before the first launch (order asserted) | fresh: one `begin`, one `finish` |
| T14 | disk | 44.99 GB at start: no launch, no ledger write; 39.99 GB: ABORT; world 1,000,000,001 bytes: CUT-WORLD; `--out` 5,000,000,001: pending DROPPED; a profile folder of 1,250,000,001 bytes: cut; P_fit 0: refused, exit 2; an MC job's world of 1,500,000,001 bytes or profile folder of 1,750,000,001: cut | at each boundary: 45.0 GB starts; 40.0 GB no abort; 1,000,000,000 bytes kept; `--out` 5,000,000,000 launches; a profile folder of 1,250,000,000 bytes kept; P_fit exactly 8 runs 8; an MC job's world of 1,000,000,001 and of 1,500,000,000 bytes kept, its profile folder of 1,750,000,000 kept; an older folder's world kills nothing |
| T15 | retention | a zip failing `testzip` keeps the raw folder; an AI file whose copy fails its size check is recorded, never silent | verified: raw deleted but `end_state`, `world_last`, `goals_last` and the AI's save and memory files when present (an absent one recorded); profile deleted |
| T16 | experience filter | `visits`, `items`, `people`, `persons`, `met`, `closed`, `arrivals`, `transitions`, `news`, `heard`, `news_log`, `spoke`, warps' `uses/first/last/by`, connections' `by/frame`, rides' `first/last/uses/closed`, bumped's `first/last/bumps`: absent; planted `rng_state`, a planted unknown ride key and a planted unknown bump key: dropped AND listed; other `tile_fields`: dropped, listed | allowed keys pass (rides' 9 static fields; `slid` kept); tiles have 4 fields; the merged tree's real fixture `gates/fixtures/ch5loop_tcap.world.jsonl` (4 maps of the AI's own memory) extracts with `unclassified` empty; a K1 tell ("... a seasoned player's knowledge: ...") before a battle record is never read as the fight's foe, and alone makes no fight |
| T17 | origin | saved start: `practice` | chain: `new_game` |
| T18 | continue rule | not reached, purity not clean, tail not kept, guard-cut, STOP: later legs NOT RUN, reason given | all hold: next leg from the kept state and line |
| T19 | start custody | md5 differs; truth lacks `ch5_rival_meet`; no starter line: REFUSED before launch | matching start runs, `starter_from` kept |
| T20 | donor | donor missing: REFUSED with the `LaunchError` text | present: marker names `ai-fp-donor` |
| T21 | stage watch | a staged file changed: `STOP.txt`, no new leg | unchanged: no STOP |
| T22 | AI-only stop | 5 in a row of REFUSED, NOT CLEAN, HUNG mixed: no launch, `AI-ATTENTION.txt`, exit 6, no `ATTENTION.md` | 4, then CLEAN-* or CUT-WORLD: reset; INFRA between: neither |
| T23 | schema | `schema_version` 2: exit 2 | 1 reads |
| T24 | resume | killed batch resumed: no `run_id` twice, in-flight leg INFRA | P1's two arms on 3 shared seeds both run in full; a finished batch launches nothing |
| T25 | deadline | wall plus margins past `--deadline`: not launched; a WAIT reaching it: DROPPED | far from it: launched |
| T26 | scheduler | 10 other singles, P = 8: at most 6 own launches, rest WAIT; others fall to 0 mid-run: all 8 start, `not_started` empty; `run_regression.py` running: WAIT, then start; the disk reservation short: WAIT; a WP1b job before its source chain's reached L5 record: SKIPPED, then started from that end; its chain ENDED without one: started from its fallback start at once, labelled; a WAIT past `--max-wait`: DROPPED with the reason | 0 others: 8 at once; a SKIPPED WP1b job first in line with a ready job behind it: that job launches in the same pass, and the SKIPPED job keeps its place; a SKIP longer than `--max-wait` (7,200 s): not DROPPED |
| T27 | graded-driver agreement | the known divergences, asserted: a reached, clean leg with a 500,000,000-byte world continues here, stops in `continue_after` (C3), record says why; a leg that carries a goal snapshot records `goal_memory: carried`, which `continue_after` never sends | worlds under 300 MB: `reached` and the decision equal `leg_reached` and `continue_after`, leg by leg; an MC job (2.4b) STOPS at the 500,000,000-byte leg exactly as `continue_after` does, and sends no `AI_PLAYER_GOALS` |
| T28 | imports | a planted `import ai_player.gates.frontier_probe` in a temp play module is found (AST walk, as `test_live_chain`'s ImportTests); `check_grader_imports.scan(root, ("ai_player.gates.frontier_probe",))` fails on a planted `from ai_player.personality import PERSONALITIES` in a temp probe copy | real tree: no importer; the scan clean; `GRADERS` unchanged |
| T29 | mutant staging | anchor hits 0 or 2 times: refused | once: the staged tree differs in exactly that file, named in the manifest |
| T30 | hard-coded copies | stub AI list with a 4th personality, or reordered tile fields: pin fails | 3 personalities equal `PERSONALITIES` as a set; 7 field names equal `to_dict()["tile_fields"]` (a test may import the AI) |
| T31 | LOOP key | two planted legs shaped like E0's merge into ONE LOOP key with count 2: 59 warp crossings each way, the last crossing 92,013 frames before a CLEAN-BUDGET end, next unmet `ch5_return_goods`, end ROUTE116; and 37 each way, the last crossing 20 frames before a CLEAN-CHOSEN `stuck: no progress` end, next unmet `ch5_rusturf_grunt`, end ROUTE104; a CUT-WORLD leg on the same pair joins it; the same counts cut from E0's kept L5 transitions give the same key (a committed fixture made by a script, sha256 recorded, from E0's L5 `world_last.jsonl` files, kept with their `row.json` and `ai_player.log` in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/e0-L5/`: sha256 in the keep folder's root `README.txt`, this PC only, not git; copied from `_ai_lab/s53/mergeplan/e0/runs/E0-6481`, lab, deleted after the merge; without them T31 runs on its planted legs only) | at each boundary (T14's form), on the first FAULT leg's shape: 40 crossings (20 each way): LOOP; a last crossing exactly 120,000 frames before the end: LOOP; 120,001 frames: its own key, flagged, even with a window share of 0.75 (above v2's dropped 0.5; at most 0.80 on a 600,000-frame leg with its last crossing 120,001 frames before the end; there is no share rule); 39 crossings: no LOOP; a reached leg with 118 crossings: churn table only; 60 crossings all during an ACTIVE raise: no LOOP; a `stuck: 3 battles lost` end after a loop: its own key, flagged; edge and warp crossings count alike; `pingpong_ends` counts only `goal_end` records beginning `stuck: ping-pong` |
| T32 | goal custody (part 0) | a next leg whose `AI_PLAYER_GOALS` file's sha256 differs from the kept `goals_last.jsonl`: REFUSED before launch; an MC job naming `AI_PLAYER_GOALS`: refused by `plan` | a carried snapshot arrives byte-identical, `goal_memory: carried`; a start with none runs, `goal_memory: none` |
| T33 | MC is E0's harness | an MC job whose next-leg decision differs from `continue_after`'s (a 500,000,000-byte world): fails; an MC leg cut by A1's 1,000,000,000-byte world rule: fails; an MC seed outside 6701-6799 or named by an entry: refused | an MC plan gives the 3 diagonal chains to the newest graded target, P = 3, no goal key; an MC job's world cut is `live_chain.GUARD_WORLD_BYTES` itself (read, never copied) and its profile budget lies above it |
| T34 | WP1b dependency and fallback | a WP1b job launched before its source chain's reached L5 record: fails; a fallback start taken while that chain still runs: fails; a missed chain's pair started from a G start without `fallback_for`: fails | a reached source: the job starts from that end with its snapshot; a source chain that ENDED without a reached L5: the persona's next unused G start at once, labelled, counted apart |
| T35 | stale and K1 measures | a "gone" outcome on a tile NOT in the snapshot's `tried_items` counted in `item_errands`: fails; a GOALS-OFF leg (its start's kept `goals_last.jsonl` present, not carried) whose `item_errands` reads `unknown`: fails; a K1 tell read as a fight's foe: fails | a tile in `tried_items` counted once however many outcomes; a GOALS-OFF leg with 2 "gone" outcomes on one tile of its start's kept `tried_items`: `item_errands` 1, `snapshot: kept`; a start with no snapshot (G1): `item_errands` `unknown`, `snapshot: none`; two K1 tells in the form `brain/goals.py` :3699 writes give `k1_leads.count` 2, lead ROUTE116 (the fixture: the 2 real tells of the fix round's C_FIX `actions.jsonl`, kept as `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/c-fix/C_FIX_actions.jsonl`: sha256 in the keep folder's root `README.txt`, this PC only, not git; copied from `_ai_lab/s53/fix5/runs/C_FIX/`, lab, deleted after the merge; without it, planted in that form) |
| T36 | boss-prep fields and the raise reason | a planted L6 leg ending CLEAN-BUDGET with a raise goal still ACTIVE, after 60 crossings made before the raise began, the last 100,000 frames before its end: reason `budget: a boss-prep raise still active`, its own key, never LOOP (3.8's condition (5)) | a raise that ended before the budget end: the leg's own reason; a Trainer leg: `acting` logged only, no raise counted |

Suite target under 60 s; Phase A runs some inside `test_agent.py`'s 600 s (design risk 11).

### 4.2 Mutants of the runner itself

`revert_frontier.py`: about 54 single-edit mutants, one per guard above: about 28 for the first draft's guards and
about 26 for the 2026-11-13 amendments' (part 0's own mutants, 3.15 item 6, sit with its AI-side tests). The
amendments' mutants: the LOOP bar `>=` → `>` at 40 crossings, and `<=` → `<` at the 120,000-frame end rule; warps not
counted (KI-128's blind spot); the raise exclusion removed; the raise precedence removed (an ACTIVE raise keyed LOOP);
reached legs labelled LOOP; the LOOP key keeping `next_unmet`; LOOP applied to a discrete end; rides' counters kept,
or an unknown ride key passed; MC deciding by A1's continue rule, sending `AI_PLAYER_GOALS`, or cut at A1's 1 GB
world rule; the profile budget `>` → `>=`; P_fit off by one; a dependency SKIP made a WAIT, or DROPPED by
`--max-wait`; the raise reason dropped; every "gone" outcome counted as stale; a GOALS-OFF leg's `item_errands` left
`unknown`; a K1 tell read as a foe; goal custody unchecked; L6 back to 600,000; a fallback start unlabelled, or taken
before its source chain ends.
The first draft's, for example: a hard kill with no verdict maps to
INFRA (the review's F1); `play: stopped:` with the budget run out maps to CLEAN-CHOSEN; the freshness check skipped;
`rng_state` allowed, or a warp's `uses` kept; the trainer calls `ledger.begin`; digits kept in `reason_norm`; optional
milestones not skipped; in `disk_decision`, `>` → `>=` at the world cut and the out cap, `<` → `<=` at the 40 GB abort
and the 45 GB floor; a WAIT drops the job; the stage watch removed; resume keyed by seed. Each names the test predicted to
catch it, and the prediction file is hashed BEFORE the first run (as BP-1 round 2's `revert_bossprep_hashed.py`). Every
anchor must hit exactly once; `check_anchors.py` (on the merged `main`, `RUNNERS` :39-51) reads this table too (3.1).

### 4.3 The live proof

**P1, the planted wall at OLDALE TOWN (FAULT and CONTROL, on the merged `main`, the goal snapshot carried in both
arms).** The anchor is picked, and its offline unit test run, on the final merged head: since the fix round's E,
`Navigator.walls` (`brain/navigator.py` :816-820 at `3caf9c47`) also holds the things seen standing this session
(`objects_now`), so the planted wall extends the wall set as that head builds it. P2's anchor follows the same rule.
Arms REAL (the stage at the commit) and
WALL-OLDALE (plus ONE anchored edit in the staged brain: the navigator's planner treats every tile of `OLDALE_TOWN`
(0, 10) as a wall, and no go goal targets it; the builder picks the anchor, and an offline unit test shows the mutated
planner finds no path into OLDALE while the real one does). Jobs: the 3 diagonal pairs × the same 3 seeds, L1-L2.
Predictions, hashed into the ledger entry's bounds BEFORE the run:
- **(a) FAULT:** on WALL-OLDALE at least 2 of 3 chains end L1 not reached with next unmet `ch1_rival_route103`, and the
  top chapter-1 key on that tree names it. Predicted form CLEAN-CHOSEN with a reason beginning `play: stuck:`. A
  CLEAN-BUDGET end, or a LOOP key whose legs' records all have next unmet `ch1_rival_route103`, still counts toward
  (a), reported as a miss of the form; "the top chapter-1 key names it" reads a LOOP key's records. Confirmed at
  decomp pin `731ad5b`:
  `VAR_BIRCH_LAB_STATE` 3 is set right after the starter (`LittlerootTown_ProfessorBirchsLab/scripts.inc` :132-134) and
  NO loops back to YES (:138-141), so `ch1_lab` holds before the ROUTE 103 trip.
- **(b) CONTROL:** on REAL no chapter-1 leg record ends not reached with next unmet `ch1_rival_route103`, under its own
  key or a LOOP key, and at least 2 of 3 chains reach `ch2_wally`.
- **(c) Reported:** paired arms on one seed replay until the FIRST of: the wall biting, or the game's own one-frame
  split at a warp onto an outdoor map (E0). The report says which came first. A `[watch] busy Nf` record that differs
  by one frame at a warp is a game split; an AI decision record naming an OLDALE plan or step is the wall. BP-1 round 2
  saw both (`ai_player/evidence/2026-11-11-bossprep-bp1r2-live-ab.txt` :61-67, which numbers them #119 and #121 as on
  `wip/ch6-bp1`): ledger #125's C and B decision
  streams were IDENTICAL in 3 of 3 pairs, and #127's C2L4 pair split at a map change at frame 617,525 (11 frames
  against 10), its next AI decisions the same one frame later. So a split need not happen, and it can. (c) never
  decides (a) or (b).
- **PASS** = (a) and (b). If (a) fails, the blocker list cannot see a wall, and A1 is not done.

**P2, the planted wall at MR. BRINEY's cottage (inside WP1).** WALL-BRINEY walls `ROUTE104_MR_BRINEYS_HOUSE` (17, 0)
and, since the house is entered only by its door warp on ROUTE104, every warp or door tile leading to (17, 0), including
those the start's memory knows; a unit test like OLDALE's shows no path from ROUTE104 through that warp. **Predicted:**
key (6, `ch6_briney_house`, `play: stuck: …`, -, CLEAN-CHOSEN) first at chapter 6 on that tree, a CLEAN-BUDGET form
counting as in P1 (`FLAG_MR_BRINEY_SAILING_INTRO` is set only inside the house, `Route104_MrBrineysHouse/scripts.inc`
:25, :32); a LOOP key whose records all name `ch6_briney_house` counts as well. **CONTROL:** no leg record of the 3
paired REAL jobs (WP1b's first-seed J-F job of each diagonal pair, or its fallback, 2.1) ends not reached with next
unmet `ch6_briney_house`, under any key, except an end `play: stuck: N battles lost` whose leg carried losses in
(`losses_carried` > 0, 3.15 item 2): such an end is reported apart, beside the CONTROL, and never read as the wall or
as its absence. **The discriminator, computed before the prediction is hashed:** the next unmet milestone at L6's end.
On WALL-BRINEY it stays `ch6_briney_house` in every case (the flag is set only inside the house). On REAL, L6's
1,000,000 frames (2.3) hold a Story raise (the largest measured L6 from C1: 520,366 frames) and a Catcher raise (its
550,000-frame budget × 1.156, the largest measured L6 over Story's 450,000: about 636,000 frames) with room to spare,
so a REAL leg that nothing blocks reaches `ch6_dewford`. On the spec's 600,000 frames a Catcher L6 could not fit, and
its CLEAN-BUDGET end with next unmet `ch6_briney_house` (the raise's goal records name that milestone) would read as
the wall: the CONTROL would not have discriminated. One more path ends a REAL L6 in the FAULT's form: the carried loss
count. A game that enters chapter 6 with 2 losses (2 of the 9 chapter 1-5 chains measured, 3.15 item 2) stops at its
first lost battle there (MAX_LOSSES 3), and a raise battle lost before the house leaves next unmet
`ch6_briney_house`. Measured: 0 battles lost before `ch6_dewford` in 8 of 8 runs from C1 (0 carried; all 8 of their
losses came after it, at BRAWLY's gym), so the path is possible and was not seen. This proves saved starts put a wall
in the right chapter.

**Trainer smoke (after the merge, needs the band row):** NG L1 and G3 L6, seeds 2,000,001-2,000,002, P = 2, outside every
work tree. **PASS:** the main checkout's `git status --porcelain --untracked-files=all` and `ledger.json`'s sha256
unchanged; nothing under `ai_player/evidence` newer than the start; both legs judged; records parse at version 1.

**WP1 CONTROLS** (in its prediction file): WP1a's diagonal J-N chains reach `ch5_rival_meet` in at least 2 of 3 (D15's
"chapters 1-5 did not regress", in development form). The prior is E0-2 on the merged and fixed head: "E0 VERDICT:
REACHED 3 of 3; legs ran 15, purity-clean 15; wall 31 min (cap 120); problems 0 -> GO" (the message of commit
`19e9700c`; ledger #148, `ai_player/evidence/2026-11-13-chain-heldout-dev-ch5_rival_meet-6484.txt`; one trajectory
per seed). It ran `3caf9c47`'s play code; part 0 moves A1's play digest (3.15 item 8), so MC's first run on the A1
commit must read PASS before WP1 starts. E0-2 and #101 (6 of 6 on `dc0a4e69`, main's code) carried no goal snapshot
and WP1a does: the report names that difference, and MC on the same tree (2.4b) is the like-for-like check. The fix
round's per-leg A/B (one trajectory per arm from saved starts) is mechanism evidence only. The prediction expects few
or no chapter-5 LOOP keys after E and K1 (the fix's arms from E0's starts crossed the woods pair once from T's start
and 0 times from C's: the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md` section 8; 0 from S's, `fix5/STATE.md`, lab,
deleted after the merge), and chapter-3 churn rows are possible (E0-2's T L3
reached with 92 crossings); at least 90% of legs run are judged;
experience `unclassified` empty. A miss is reported, never retuned (rule 8).

### 4.4 Definition of done for A1

0. Part 0 (GM): its offline proofs (3.15 item 6) pass before any A1 leg carries a snapshot, and its live
A/B (3.15 item 7) passes before WP1. 1. The offline suite green; the mutants CAUGHT as
predicted. 2. `run_regression.py --quick` and `run_gates.py` green.
3. The full regression lane passes on the commit (`suite_map.json` covers `ai_player/**`). 4. P1 PASSES; MC's first
run, on the A1 commit's stage (2.4b), read PASS before WP1, and its records parse. 5. The trainer
smoke PASSES. 6. WP1 ran (WP1a, then WP1b, 2.4); its chapters 1-7 blocker report with examples is in the
evidence, reach split by start kind (3.8). 7. P2 PASSES. 8. Docs: `07`;
`04` (the top blocker becomes the next skill build); `03` (with the chapter 1-5 miss-rate item of section 0);
`05` (a KI for each new blocker holding at least 2 runs, and for every LOOP key at 1 run: a loop that ends a leg is not
noise); `06` for the 1 GB cut and CUT-WORLD, HUNG and the missing-verdict rule (D14 changed), the continue
rule without the 300 MB cap, the WAIT/DROP scheduler, the Phase A contract (D1 and D11 changed), the persona of saved
starts, and six more: (i) D7 changed, the LOOP key and its end rule (3.8); (ii) D12 changed, part 0 (GM): A1's legs
carry the goal snapshot, `last_save` and `saved_for` reset at a `--state` start, the loss count carried, MC carries
none (3.15; rejected: A1 test-side only, with `06` 2026-11-12 item 4 NOT MET); (iii) MC replaces E0, "Item 4's bridge
retires", with its seed rule, its unknown false-STOP rate, live_chain's world cut, and its first run on A1's commit
read PASS before WP1 because part 0 moves the play digest (2.4b, 3.15 item 8); (iv) the disk rules: the per-job budget
and P_fit (2.7, 3.12, 3.13), and the per-job SKIP (3.13); (v) the L6 budget, 1,000,000 frames and 7,200 s (2.3);
(vi) cite the merge's `06` correction of USER RULING 55 (2)'s reason (the merge docs pass's entry "E0's STOP and
the fix-forward", DOCS-ADDENDUM G4: lab, deleted after the merge); write one only if it is absent (`06` :9963 gives "so
runs replay and can be checked"; E0 measured one-frame splits at outdoor warps, so a run replays only up to its first
such split); the decision (the frame budget is the session limit) stands and is not reopened. 9. Tier 1.
10. Commits by explicit path.

## 5. What needs the chapter 6-7 merge, and what could be built before it

**History once the merge lands:** every part is then built and run on the merged `main`. The order note below still
holds, and the L6/L7 budget check is closed (2.3).

- **Facts.** On `main` the probe can stage, run and judge chapters 1-5. The branches (`origin/wip/ch6-ch7` against
  `main`) hold chapters 6-7's milestones and proofs (`knowledge/milestones.json` +501, `extract_milestones.py`), the
  AI's eyes for them (`eyes/view.py` +188), the chapter-6 skill rounds (`brain/goals.py` +567, `brain/rides.py` new, …)
  and `check_anchors.py`. `live_chain.py` is not on `wip/ch6-ch7` (cut at `979754bf`); the merge joins them and redoes
  its full lane (04 queue item 4).
- **Can be BUILT before the merge:** the offline core (3.1-3.13, T1-T30 with stubs) and the mutants, without
  `check_anchors`. Re-integration: `run_units.py` changed on the branch (+4 lines), so a textual conflict is likely; the
  tests read milestone counts, never hard-code 28 (as `test_kb2` does); the mutant table joins `check_anchors`.
- **Can RUN before it:** P1. Its ledger entry adds one more shift to the merge's renumbering: keep it on the A1 branch
  and renumber at A1's merge, or run P1 after the merge.
- **NEEDS the merge:** WP1, P2, the band row and every ledger write on `main`, the trainer smoke, the L6/L7 budget check,
  `check_anchors` coverage, the merge's full lane.
- **The order.** `06` 2026-11-11 put A1 after the merge ("A1 built before the merge would have to be re-integrated"),
  to be revisited when the merge lands; this spec does not decide it. If the lead revisits it, the offline build can
  start in its own worktree on a branch off `main` (for example `wip/a1-frontier`), touching only 3.1's files, with no
  live run until BP-1 round 3 and P11-1 finish (up to 15 emulators now).

## 6. Cost, wall time and risks

### 6.1 Cost (Mtok, as whole items in `cost-ledger.jsonl`)

| Part | Mtok | Basis |
|---|---|---|
| Build (offline core, tests, mutants) | 20-30 | live-chain-driver 14.4; bp1-boss-prep-build 21.0; bp1-round2-raise 29.9; plus the scheduler loop, HUNG, `reserve-band` |
| Independent adversarial verifier | 5-10 | live-chain-check3 8.5, check5 2.5 |
| One fix round and its check | 8-15 | live-chain-round4 9.8 to round3b 15.6 |
| P1, trainer smoke, WP1 (orchestration, judging) | 3-6 | ch6-probe11 1.6 for 3 runs |
| Docs, Tier 1, Tier 2 | 2-4 | recent docs rows |
| Part 0, GM (AI-side code, offline FAULT and CONTROL, purity, gates) | 8-15 | the first amendments' estimate; R1 + R2's save and memory work is the nearest kind |
| The amendments' rules (LOOP and its end rule; boss-prep, rides, K1 and stale fields; MC's plan, seeds and world cut; the per-job disk budget; WP1b's SKIP; replay and compare; rides and `slid`; L6) | 5-9 | the first amendments' 4-8, plus this revision |
| GM's share of the verifier | 3-5 | the first amendments' estimate |
| The extra live work (GM's chain and A/B, MC's first run, WP1b's dependency, the full lane's watch) | 2-3 | ch6-probe11 1.6 for 3 runs |
| The extra `06` entries (4.4 item 8) and their Tier 1 | 1 | recent docs rows |
| **Total** | **57-98 (central 76)** | the sum of the parts: 38-65 above, plus 19-33 |

At most 2 fix rounds; a third goes to the lead. `live_chain` took 7 rounds and 111.8 Mtok because its graded mode needed
a full threat model; A1 has no graded mode, no import-closure hashing, and only live_chain's threats (a) and (b).

### 6.2 Wall time

Agent time about 13-20 h. Machine time about 11-13.5 h: GM's live A/B 1-1.5 h; P1 about 30 min; MC's first run about
30-45 min; the mutant run about 30 min; the trainer smoke about 15 min; WP1 4-5 h (about 9 h worst); the full lane
about 4.4 h (budgeted from upper-bound rows; about 9-10 h if it times out once and runs again; the merge's own lane
gives the measured hours); about 22.5 h worst in all. The report about 1 h. Calendar: about 3-4 days after the merge,
less if the offline build ran before it. Estimates.

### 6.3 Risks

1. **Ledger renumbering:** A1's entries follow the merge's renumbering (5). 2. **A fix-round tail:** scope, 2-round cap.
3. **CPU:** the probe WAITs while a full lane runs; the singles cap keeps the tuner's 12 lanes; USER RULING 54 gives the
   machine time to the AI. A gate timeout is INFRA; the gate's time per launch is UNMEASURED (P1 measures it). **New
   with HUNG:** a CPU-starved brain could miss its soft deadline (at most 30 s before the hard kill) and be classed HUNG
   against the AI; each HUNG record carries its frames/s, and if HUNG legs cluster at low rates the lead lowers P, never
   reclassifies after the fact.
4. **Disk:** KI-130's churn recurs (497 MB on 2026-11-11): the 1 GB cut, the 45/40 GB floors, the per-leg delete.
5. **A pending Windows restart** kills a running batch: restart first, or `--resume`.
6. **Mixed-tree starts:** C ends came from the chapter-5 stops code, G ends from `dc0a4e69`; the merged code loads their
   memory (`WorldMemory.from_dict` uses `.get` defaults, :935 at `3caf9c47`). Reach is split by start, and a start whose
   memory line reads "nothing (a new memory)" (`NEW_MEMORY`) is flagged.
7. **Practice is not the frontier** (D4; the report header). 8. **Key granularity:** the normalization changes only by a
   rule written before the next batch; raw examples are kept. 9. **Determinism (measured 2026-11-13):** the game is
   not fully deterministic under the launcher (a one-frame split at an outdoor warp; host-time RTC suspected, not
   proven). Identical results are a determinism check, never a replication. An example reproduces the REGION of a
   stop, not its path. A stop is diagnosed by an A/B on its own saved start (E0's method), never by re-rolling seeds.
   10. **Junctions:** a promotion or merge touching
   `sandbox-pokebot` mid-batch trips the stage watch (STOP). 11. **Weekly usage:** the cost is quoted whole so the lead
   can place it beside BP-1 round 3, P11-1 and the merge.

## 7. Open questions for the user

**None.** Each candidate is answered, and this revision's calls (HUNG, WAIT/DROP, the Phase A contract) are the lead's,
for `06`: practice then a New Game test (USER RULING 55; WP1 does both, `origin` keeps them apart); machine time (USER
RULING 54; the tuner keeps 12 lanes, USER RULING 38); what experience may hold (USER RULING 40: static only); whether the
probe plays (USER RULING 35: it only launches the AI); A1 before or after the merge (the lead's call, `06` 2026-11-11).

## Appendix: what this spec rests on (read 2026-11-11)

Design (D1 :110-117, D11 :147-153, D13 :156-160, D14 :161-168, D17 :187-193, Phase A tests :264-276); `04-HANDOFF.md`
:1-71; `07` 2026-10-30 to 2026-11-09; `06` USER RULINGS 54, 55 and the 2026-11-11 entries; `05` KI-129 to KI-133;
`cost-ledger.jsonl`. Code: table 1.2, `G/provenance.py` :515-560, `G/hands_harness.py` :136-230. Branches: `git log`,
`git diff --stat main...origin/wip/ch6-ch7 -- ai_player`, its `milestones.json` (36) and `world/memory.py`, and
`origin/wip/ch6-bp1`'s `2026-11-05-CH6-CH7-BUILD-REPORT.md`. Decomp `731ad5b` (`C:/Remote Projects/_decomp/pokeemerald`).
Learner clone `da2fb96a`: `learner.py`, `config.json`. Lab: `MANIFEST.json`, `s53/ch6probe11`, `s53/bp1r2` (scripts,
`STATE.md`, results), `s53/ch5stops/out/probe`, `s53/ch6stops{4,5,6}/build/starts`. `_livechain/graded-ch5` (job files,
rows, md5s). `tools/status.py` at 10:34 AM 2026-11-11 (tuner cycle ai0081, 12 lanes; 66 GB free; a restart pending).

## Review log

2026-11-11; the findings are in `2026-11-11-A1-FRONTIER-PROBE-SPEC-REVIEW.md`. Each was checked against the code before it was applied, and checked again
at `879b1fe3` after the usage-limit restart.

| Id | Held? (read at) | What changed |
|---|---|---|
| F1 | Held (launcher :499-502, :714-719, :902; design :164, :266) | HUNG added (counted, a blocker); other missing verdicts NOT CLEAN; INFRA only for the gate timeout, `driver_killed`, `launch_died`, ABORT kills, salvage; rules reordered so exit 8 applies (3.5, T2b, T22, 1.3, 4.4). |
| F2 | Held (`schedule` :2471-2499) | Own GO/WAIT/DROP loop with `--max-wait` (3.13); T26 extended; a mutant. |
| F3 | Held (design :111; R8 :2524-2526) | Phase A builds a stage per tree; `--out` and stages outside every work tree and `pokebot-learner` folder; the learner copies its records (1.3, 3.3, 3.10, T10, T11). A work tree run in place: rejected (3.3). |
| F4 | Held (:1481-1488, :178-179) | Own `disk_decision` (3.12); the mutants point at it. |
| F5 | Held | T14 boundary CONTROLs; 44.99/39.99 GB FAULTs. |
| F6 | Held (`mode.py` :1368; launcher :449-457, :548-557) | Budget-spent `play: stopped:` is CLEAN-BUDGET; P1(a) reworded; budget ends reported apart. |
| F7 | Held (`ALLOW` :37) | Hard-coded copies, pinned by T30. |
| F8 | Held (:292, :363, :1170) | G-3's file unchanged; T28 calls `scan`. |
| F9 | Held (`plan_of` :667-671) | Scoped to "as a New Game chain". |
| F10 | Held (`tracked` :82-95) | Cited in 3.8. |
| F11 | Held (:2292-2320, :2062) | `salvage_chain` not reused; job keys named (3.4). |
| F12 | Held (:1444-1471) | The 300 MB divergence is T27's FAULT. |
| F13 | Held | Resume keyed by `run_id` (2.5, 3.13, T24). |
| F14 | Held (decomp :25, :32) | Warps into (17, 0) walled, with a unit test (4.3). |
| F15 | Held (:1827) | End map via `map_keys`. |
| F16 | Held | Cost 38-65 equals its parts (the build row +2 for this revision); one wall time. |
| F17 | Held (`MANIFEST.json`) | The 163 MB of C worlds counted (2.7). |
| F18 | Held (`probe-C1.job.json`) | C starters from the truth's party, `starter_from` kept (2.1, T19). |
| F19 | Held (:147-206, :209-219) | `reserve-band` with `ledger.py --check` (3.10, T12). |
| F20 | Held (memory.py :666-676, :689-690, :712-714) | Warps and connections reduced to static fields (3.9, T16). |
| F21 | Held (`live_step1.py` :247-248, :916) | Stated as A1's own choice (1.2). |
| size | - | The revised file (83,533 bytes) was cut under 60,000 by tightening prose and citing each line once in 1.2. No rule, md5 or test was dropped; a few secondary citations were (for example `bp1r2/STATE.md` 09:22, the `07` line range, `early_prune_margin_gb`). Added on the second check: the gate-timeout text reaches `run.stdout` (`GateRun.findings` keeps "FAIL" lines, :741-742; `_gate` prints them, :87-91). |

The review's other notes (the order in `06`, seeds re-checked at build time, live work after the merge) were already in
2.5 and 5.

**2026-11-13: amended after the chapter 6-7 merge, E0 and E0-2** (the repo note
`2026-11-13-A1-SPEC-AMENDMENTS.md` beside this spec: 25 amendments, revised after an adversarial review of their first
draft and three re-checks of the revisions, every reason and its evidence there; the amended parts read at
`3caf9c47`). The main changes: part 0, GM (3.15), which moves the play digest; the LOOP key (3.8); L6 raised to
1,000,000 frames (2.3); MC replaces E0 as E0's harness exactly, its first run on A1's commit before WP1 (2.4b); WP1
split into WP1a and WP1b, with a per-job SKIP (2.4, 3.13); the per-job disk budget (2.7); the record's new fields
(3.7); T31-T36 (4.1). The file grew from 60,366 bytes to about 110 KB; a tightening pass is the lead's call.
