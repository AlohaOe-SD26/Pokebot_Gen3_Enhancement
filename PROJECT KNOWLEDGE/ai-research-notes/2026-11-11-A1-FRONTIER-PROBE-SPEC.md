# A1: the wide frontier probe and the trainer's runner core: BUILD SPEC (2026-11-11, revised after review)
> ⚠ **AMENDMENTS PENDING (2026-11-14):** apply `2026-11-13-A1-SPEC-AMENDMENTS.md` (beside this file) before building (`04-HANDOFF.md`, queue item 4). Whoever applies them empties this line only AFTER the last block (an early delete moves every line the checkers' table names).
> **Claude's spec, NOT BUILT, a NOTE like every agent output.** Written read-only by a spec agent of session `2cb1657d`,
> revised the same day on an independent review's 21 findings (`2026-11-11-A1-FRONTIER-PROBE-SPEC-REVIEW.md` beside it; Review log at the end). Each code
> claim names a path and line, or a symbol whose line is in table 1.2; the builder re-reads it before relying on it.
> UNKNOWN = not checked. **Read at** `main` `10ceb4f7`, re-checked at `879b1fe3` (docs only since; no `ai_player/` code
> changed after `dc0a4e69`, the graded chapter-5 commit); `origin/wip/ch6-ch7` `18c3d51b`; `origin/wip/ch6-bp1`
> `c5146e53`; the learner clone `da2fb96a`; the decomp pin `731ad5b`.
> **It replaces** the "A1" part of section 4 of `PROJECT KNOWLEDGE/ai-research-notes/2026-10-30-AI-TRAINER-DESIGN.md`
> (its decisions hold except as 1.3 says) and **keeps the order** in `06` 2026-11-11 (BP-1 round 2, P11-1, the chapter
> 6-7 merge, then A1; "Not a do-not-reopen ruling"; section 5 has the facts).

## 0. In plain words

- **Now:** the AI's graded frontier is the end of chapter 5 (6 of 6 New Game chains, ledger #101,
  `PROJECT KNOWLEDGE/ai-frontier.txt`). Chapters 6-7 (the sail to DEWFORD through BRAWLY) are on branches, merged next.
- **Two jobs:** (1) **measure** where the AI stops across chapters 1-7 on the merged code, as a ranked **blocker list**
  with a saved example of each, for the trainer to work down one skill build at a time; (2) **be the runner core** the
  learner's trainer (Phase A) calls as a subprocess. Nothing is built twice.
- **It reuses** `live_chain.py`'s leg pieces, `live_step5.run_arm` (the real launcher, gated per launch) and the lab's
  staging kit, and **adds** one test-side module, `ai_player/gates/frontier_probe.py`: a parallel job runner beside the
  bot tuner, end classes from files (D14), ranked blocker keys (D7), static-only experience (D16), a `--trainer` mode
  that writes no tracked file, disk caps (KI-129, KI-130).
- **WP1 (after the merge), 39 jobs:** 9 New Game chains to `ch7_brawly`, one per personality × starter (6 pairs never
  played as a New Game chain: `live_chain.PAIRS` is the diagonal, though `rate_step5.plan_of` cycled all 9 in sweeps);
  27 practice jobs (9 chapter-5 ends × 3 seeds, chapters 6-7); 3 planted-wall jobs. About 3-3.5 h of machine time at 8
  at once beside the tuner's 12 lanes (6.5 h worst). First, P1 (20-30 min) plants a wall at OLDALE TOWN that must rank
  first on the walled code and never appear on the real code.
- **Cost:** 38-65 Mtok (central 50), above the design's 8-15; the graded chain driver it leans on cost 111.8 Mtok
  (`cost-ledger.jsonl`).

## 1. What A1 is for, and what exists

### 1.1 The two outputs

1. **The blocker list, chapters 1-7, merged tree.** Per chapter: reach from the game; ranked keys (D7) with their share
   of judged legs and frames spent; up to 3 examples each (`end_state.ss1` + `world_last.jsonl` + zipped logs, enough to
   replay the stop through the launcher). The next skill build takes the top entry. Seen in development (never a rate):
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
| Exits, end reasons | `launcher` `WALL_CLOCK_EXIT` 124 :107, `GATE_REFUSED_EXIT` 7 :109, `NO_VERDICT_EXIT` 8 :111, `GATE_TIMEOUT_SECONDS` 180 :117, `_INVOLUNTARY` :271, `_HOST_CODES` :275-276, `_ran_out` :449-457, hard kill = "a stuck run" :499-502, `_classify_session` :548-557, `soft_deadline_margin` :714-719, `GateRun.findings` :741-742 ("FAIL" lines), the timeout text :760, `run_child` :848-904 (124 at :902); `ai_player/__main__.py` `_gate` :83-100 (`[AI-GATE]` lines :87-91), `_report_verdict` :103-132, `return GATE_REFUSED_EXIT` :148; `ai_player/mode.py` :1368 (`stopped: not finished within … frames`) | D14 (3.5) |
| Ledger | `G/ledger.py` `register` :116-144, `begin` :147-206 (development refused over an unplayed `registered` entry :181-185), `finish` :209-219, `--check` | 3.10 |
| Maps; truth | `G/rate_step5.py` `map_keys` :1827 (reads `MapRSE` as text, no framework import; `map_data.py` `OLDALE_TOWN` (0, 10) :804, `ROUTE104_MR_BRINEYS_HOUSE` (17, 0) :1054); `G/play_harness.py` `story_truth` :95-120, marks = the proofs of `knowledge/milestones.json` (`tracked()` :82-95) | 3.8; read only |
| G-3; AI facts | `G/check_grader_imports.py` `GRADERS` :32, `ALLOW` :37 (only `host.launcher`, `options.ENV_*`), `scan` :211; `ai_player/personality.py` `PERSONALITIES` :60; `ai_player/world/memory.py` (3.9); `ai_player/options.py` (3.11) | copied as constants, never imported (T30) |
| Lab kit | `_ai_lab/s53/ch6probe11/build_stage11.py`, `make_arm11.py`, `arms11.py` `child` (`carried = {"START": (state, world, [])}`, `state_from="START"`); `s53/bp1r2/seeds_free.py` | `stage` (3.3); seeds (2.5) |
| Zip check | `ai-agent/learner.py` `verify_archive` :1510 | NOT imported, A1's own choice (the runner must not depend on the learner clone; D17 forbids only the learner importing `ai_player`, and `G/live_step1.py` :247-248, :916 imports `ai-agent/scoring.py`) |

### 1.3 The 2026-10-30 design: what holds

| Design part | Now |
|---|---|
| §0, §2 "never played chapter 3", gap 1; "loader slice 1"; A1's old jobs, budgets, "8-15 Mtok"; "milestones stop at ch4_roxanne" | **Superseded or done:** A0 ran (07 2026-10-30); KI-128/129 graded (#82); chapter 5 graded from a New Game (#101); `knowledge/atlas.py` reads map ids and types; sections 2 and 6 here; 28 milestones on `main`, 36 on `wip/ch6-ch7`. |
| §6 Q1; D2, D3, D4, D7, D12, D16 | **Hold** (Q1 = USER RULING 55). D3 also excludes the harness-placed I1, D1, D2 (2.1); D7 takes the LEG's chapter; D12 is `run_chain`'s. |
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
| Frames | 330,000 | 330,000 | 600,000 | 900,000 | 600,000 | 600,000 | 1,200,000 |
| Wall (s) | 3,600 | 3,600 | 3,600 | 3,600 | 3,600 | 3,600 | 7,200 |

- **Why.** Probe 11 (#117 (was wip/ch6-ch7#111)): C2 and C3 reached BADGE02 in 195,229 and 194,349 frames with no raise; C1 lost to BRAWLY
  three times (`stuck: 3 battles lost` after 167,065; the CH6-CH7 report on `origin/wip/ch6-bp1`). BP-1 round 2's B2 arms
  took 612,596-666,141 frames from C1, the raise 450,784-464,737 of them (`bp1r2/out/ab2/results.json`). USER RULING
  55: "In training the budget is set generously, so it never cuts off real progress." At 349 frames/s (2.6), 1,200,000
  frames take 3,440 s: the wall is 7,200 s.
- **At build time:** if a final BP-1 round 3 or P11-1 run that reached its target used over 80% of a leg's frames, raise
  that budget before WP1's prediction is hashed. The optional `ch6_old_rod`, `ch7_flash`, `ch7_gym_trainers`,
  `ch7_exp_share` are reported, never targeted.

### 2.4 Batches

| Batch | When | Jobs | Legs |
|---|---|---|---|
| **P1**, the planted-wall proof | can run on `main`'s code (5) | arms REAL and WALL-OLDALE (4.3), the 3 diagonal New Game chains each, the SAME 3 seeds in both arms | L1-L2, at most 12 legs |
| **WP1**, the wide probe | after the merge | **J-N:** 9 chains, one per pair, L1-L7. **J-F:** 27 practice jobs, G1-G6 and C1-C3 × 3 seeds, L6-L7. **P2:** arm WALL-BRINEY on the first-seed J-F jobs of G1, G3, G5 (one per persona), L6 only | 39 jobs, at most 9×7 + 27×2 + 3 = 120 legs |

- **USER RULING 55 is met inside WP1:** chains and practice test one tree in one batch, and the AI reads no experience
  yet. **27 practice jobs:** D15's quota is 40 CLEAN ends at a chapter; WP1 gives up to 36 at each of chapters 6 and 7.
- **3 seeds per start:** the clock is pinned (`ENV_CLOCK` "10:00", `live_step5.py` :143), so one start on one seed is
  one trajectory replayed (CLAUDE.md rule 8). **Order:** J-N chains, then J-F interleaved by start, then P2.

### 2.5 Seeds

- **One development ledger entry per batch**, one contiguous range. Seeds are shared on purpose (P1's two arms; P2 reuses
  its J-F seeds, as BP-1 round 2 did in #124-#127 (was wip/ch6-bp1#118-#121); a chain's legs), so a resume de-duplicates by `run_id`.
- **Proposed:** P1 `6601-6603`, WP1 `6611-6646`. At 10:40 AM 2026-11-11, `py -3.12 -B "C:/Remote
  Projects/_ai_lab/s53/bp1r2/seeds_free.py" 6461-6500 6501-6600 6601-6700` printed FREE in 188 ledgers (main, 10
  worktrees, the lab and others); the reviewer agreed on the 30 committed `ledger.json` of every ref.
- **Not a reservation:** BP-1 round 3 (6403-6430) and P11-1 (6431-6460) have not committed. **Re-check at build time**
  with that script (`s53/ch6/seeds_free.py` misses the lab and the learner clone); refuse any seed named by ANY entry,
  development included (live_chain R3). `--trainer` uses only the D13 band.

### 2.6 CPU share beside the tuner

- **Measured:** the tuner's 12 lanes use 43-50% of 32 threads (design §1). An AI run gave 582-649 frames/s beside 3 AI
  runs (A0) and 349-398 beside about 13 (BP-1 round 2's `ab2` and `control2`, 08:51-09:13 on 2026-11-11: 612,596 f /
  1,754.4 s; 654,457 / 1,847.6; 666,141 / 1,675.7).
- **Rules:** P = 8, at most 12. **Singles cap (WAIT):** own launches plus other singles at most 16 (a single = a
  `pokebot.py` without `--endless-target`, the learner's `other_bots_running` rule), so `size_lanes` (`min(12, 32 − 4 −
  singles, RAM) // 4 × 4`) still gives 12 and the 8-lane wait never fires. **No start while `run_regression.py` runs
  (WAIT):** a full lane failed by a TIMEOUT under load (07 2026-10-31); `Get-CimInstance Win32_Process`. A 15 s stagger.
- The report gives frames/s per leg and per wave (P1 measures P = 6); under 300 in WP1's first wave, the lead lowers P,
  recorded. RAM 128 GB; per-run RAM UNMEASURED.

### 2.7 Disk (KI-129, KI-130, the learner's 25 GB floor)

- **Free** 66 GB at 10:34 AM 2026-11-11. The learner's `disk_guard` stops the tuner under 25 GB (`min_free_gb`) and
  archives early under 40. **A1** refuses to start under 45 GB (D11's AI-only floor) and aborts under 40 (no launch,
  running launches killed, `ABORT.txt`, the entry ABORTED), so it never brings the learner near its stop.
- **Per leg:** a newest `world.jsonl` over 1,000,000,000 bytes is killed (CUT-WORLD); every finished one is measured,
  its last line kept, then deleted; over 300 MB (live_chain's graded cap) is reported. Measured: graded legs at most
  65.8 MB; chapters 6-7 24-97 MB; RUSTURF churn 497 MB; KI-130 774 MB; A0 / KI-129 (fixed) about 2 GB.
- **Transient** at worst 8 GB. **Out store** about 2.5 MB a leg (1.5 raw, 1 zipped logs), 0.3 GB for 120 legs; **cap
  5,000,000,000 bytes**. **Stage:** 25.3 MB of code plus the copied starts (C worlds 91,544,456 + 13,599,098 +
  58,084,300 bytes, about 163 MB, `MANIFEST.json`; G files about 6 MB): about 0.2 GB for WP1, none copied for P1.
  Profiles are deleted per job; the main sandbox's 14 GB of old `profiles/` is not A1's.

### 2.8 Wall time

P1: about 1 job-hour, 20-30 min at P = 6. WP1: about 19 job-hours (J-N 9 × 0.9 h, from #101's 17-28 min a chain for
chapters 1-5 at P = 3 plus 10-30 min for 6-7; J-F 27 × 0.4 h; P2 3 × 0.15 h), so 3-3.5 h at P = 8 with the tail, 6.5 h
if every L7 spends its whole budget.

## 3. The new code

### 3.1 Files

- **NEW:** `G/frontier_probe.py` (test side; the AI never imports it, T28); `G/test_frontier_probe.py` (4.1);
  `G/revert_frontier.py` with its mutant table (4.2).
- **CHANGED, one entry each:** `G/run_units.py` `SUITES` (:42, like `test_live_chain` :94);
  `tools/workflows/suite_map.json`; `ai_player/README.md` ("Run it"); after the merge only, `G/ledger.json` (the band
  row, the batches' entries).
- **NOT CHANGED:** `live_chain.py` (642 tests, 378 of 378 mutants killed, 07 2026-11-06); `check_grader_imports.py`,
  which is in `GRADER_GATES`, so adding the probe to its `GRADERS` would make the next graded live_chain run re-register
  (T28 calls its `scan` instead); `live_step5.py`, `launcher.py`, `ledger.py`, AI play code, `ai-agent/*`.

### 3.2 Command line

Every command is `py -3.12 -B ai_player/gates/frontier_probe.py ...`:

```
stage --commit SHA --stage DIR [--repo DIR] [--sandbox DIR] [--donor DIR] [--mutant oldale|briney] [--starts G1,...]
plan P1|WP1 --first-seed N > jobs.json        (pure; validates the env keys)
run --jobs F --out DIR --stage ARM=DIR[,ARM=DIR] (--ledger development --prediction-file F | --trainer)
    [--parallel 8] [--deadline EPOCH] [--max-wait 7200] [--resume]
report DIR                                     (offline; from records.jsonl)
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
3. `legs_of(target, staged milestones.json, {**FRAMES_BY_CHAPTER, 6: 600000, 7: 1200000})`, walls from 2.3; a saved
   start keeps L6-L7.
4. Per leg: `STOP.txt`/`ABORT.txt` check; the `Arm` (fresh, the previous leg, or `"START"` in `carried`); `run_arm`;
   `judged(check_purity)`, `judged(check_after_is_this_run)` as `run_chain` does; the row; `finish_leg`; class (3.5);
   next unmet and key (3.8); experience (3.9); one line appended to `records.jsonl` under a lock; continue rule (3.6).
5. The job record; zip and verify (3.12); delete the profile (a leftover is named).

### 3.5 End classes (D14, from files; the first matching rule wins)

"Stop": the AI-only stop count (3.13). "Blk": in the blocker list when not reached. "Exp": experience written.

| # | Class | Rule | Stop | Blk | Exp |
|---|---|---|---|---|---|
| 1 | CUT-WORLD | the probe's guard killed the launch for `world.jsonl` over 1 GB (its kill marker) | resets | yes: "harness cut: world.jsonl over 1 GB (a churn, KI-129/KI-130)" | no |
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
the kept `end_state.ss1`, its `world_in` sha256 the kept line's, the env keys the allow-list); **C6** no `STOP.txt`. The
world size is REPORTED, not a condition (`WORLD_SIZE_KIND` GRADED stops a graded chain on a churn; a probe wants to see
what follows). `continue_after` is not used: its C5 (`custody_problems`) assumes a New Game first leg and its C3 grades
the 300 MB cap; T27 asserts that cap is the only difference.

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
  world_over_300mb, world_deleted, log}; `experience` {written, fights, unclassified}; `kept` {folder, zip, zip_sha256,
  raw: end_state.ss1 and world_last.jsonl}; `notes`.
- **A job record:** {schema_version, record "job", job, legs_ran, stopped_at, stop_reason, reached_last,
  profile_deleted}. `report` refuses an unknown `schema_version` (exit 2): Phase A test 14.

### 3.8 The blocker key, clustering and the report (D7)

- **Next unmet milestone:** the first entry of the staged `milestones.json` (file order; optional entries and waypoints
  skipped) whose proof does not hold on the END truth's marks (`proof_holds`), or the start truth per 3.5. A proof whose
  mark the truth did not return goes to `next_unmet_unread`, never counted. On `main` there are no chapter 6-7 marks
  (`play_harness.tracked()` reads `knowledge/milestones.json`, which ends at chapter 5 there); they come with the merge.
- **The key:** `(leg chapter, next_unmet, reason_norm, end_map_const, class)`. `reason_norm` = `untrusted_text
  (exit_reason)` or the class's text, digit runs made `N`, whitespace collapsed, cut at 160 characters (`play: stuck: 3
  battles lost (MAX_LOSSES 3)` → `play: stuck: N battles lost (MAX_LOSSES N)`). `end_map_const` = the constant whose
  "group:number" in `rate_step5.map_keys()` is the end truth's `map`, else `UNKNOWN` (no framework import).
- **Ranking** per (`tree.play_digest`, chapter) on the exact key; share = count / judged legs, excluded counts shown
  beside it; ties by key text. **Per blocker:** count, share, real frames (min, median, max), counts per persona ×
  starter, up to 3 examples newest first. **Per chapter:** reach = reached / judged, frames/s, class counts with
  CLEAN-BUDGET apart from CLEAN-CHOSEN.
- **Files:** `<out>/blockers.json` and `blockers.md`, rebuilt by `report`, headed "DEVELOPMENT DATA, NEVER A GRADED
  PROOF; PROJECT KNOWLEDGE/ai-frontier.txt is the authority" (D4). Trees sharing an `--out` are ranked side by side.

### 3.9 The experience extract (D16; written, never read by the AI in A1)

**Static facts by ALLOW-LIST**, from the leg's kept `world_last.jsonl` (the `WorldMemory.to_dict` snapshot,
`ai_player/world/memory.py` :801-816), read as JSON with no AI import:
- **World:** `warps` as `{key: {to, arrival, direction, inferred}}`, dropping `uses`, `first`, `last`, `by` (:666-676,
  :712-714); `connections` as `{source, target, direction, from, arrival, offset}`, dropping `by`, `frame` (:689-690),
  de-duplicated; `landmarks`; `rides` (on `wip/ch6-ch7` only, :892 there).
- **Per map** (`MapMemory.to_dict` :375-389): `key`, `name`, `const`, `tile_fields`; `tiles` with only the first 4 of
  the 7 compact fields (flags, ledge, elevation, behavior: `TileFact.compact` :214-217), never `seen_frame` or
  `seen_from`; the 7 names are hard-coded, and a map whose `tile_fields` (:379-380) differs is dropped and listed in
  `unclassified` (fail closed); `edges` (:859-861); `bumped` as `{tile|direction: {from, direction}}`, dropping `first`,
  `last`, `bumps` (:725-727).
- **Per-game facts dropped:** per map `visits`, `closed`, `people`, `persons`, `met`, `items`, `arrivals`,
  `first_frame`; world `transitions`, `tiles_learned`, `news`, `heard`, `news_log`, `spoke`. **Any other key is dropped
  AND listed** in `unclassified`; the report prints a non-empty list, and T16 fails on one.
- **Fights** from the kept `actions.jsonl` (`live_step5.is_battle` :739-741, `battle_records` :744-747): per trainer
  battle, the foe as shown (the newest earlier `tell` "battle: a trainer battle against", `tells` :702-705), the party as
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
  `AI_PLAYER_MEMORY` :245 and `AI_PLAYER_CONTINUE` :247 are unused: A1 never continues a game (D12).
- **A planted wall is CODE in a staged copy, never an env switch.** The probe refuses every FAULT switch.

### 3.12 Disk caps and retention

- **A1's own** `frontier_probe.disk_decision(world_bytes, free_gb, out_bytes)`, constants `WORLD_CUT_BYTES =
  1_000_000_000`, `ABORT_FREE_GB = 40.0`, `START_FREE_GB = 45.0`, `OUT_CAP_BYTES = 5_000_000_000` (free space in
  `safe_free`'s unit). Strict comparisons: each boundary value passes.
- **Start:** refused when free < 45.0 on the drive of `--out` or a stage. **Each 5 s tick, in order:** free < 40.0 →
  ABORT; newest `world.jsonl` > 1,000,000,000 bytes → kill (CUT-WORLD); `--out` > 5,000,000,000 → DROP pending jobs.
- **A job's end:** zip the folder, verify it (`testzip()` is None; members and sizes equal the raw files), ONLY then
  delete the raw files but each leg's `end_state.ss1` and `world_last.jsonl` (the example; Phase A's pool state). A
  failed zip keeps the raw folder, recorded. `end_sweep` re-deletes any leftover `world.jsonl`.
- **`teardown`** unlinks every junction FIRST (a recursive delete through one would delete the main sandbox's
  `modules/`), then deletes the stage.

### 3.13 The scheduler, stops, the stage watch, resume and the deadline

- **Scheduler:** A1's own loop of `schedule`'s shape (at most P, the stagger, `tick` after every pass), since `schedule`
  drops every job `may_start` refuses. The start check returns GO, WAIT or DROP. **DROP** (to `not_started` with the
  reason, for good): the deadline; the `--out` cap; `STOP.txt`, `ABORT.txt`, the AI-only stop; a wait past `--max-wait`
  (default 7,200 s). **WAIT** (the job stays first in line, nothing launches this pass, re-checked next tick): the
  singles cap; a running `run_regression.py`.
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

## 4. Tests and proof

### 4.1 Offline tests (`test_frontier_probe.py`)

Stub legs only, no emulator. Each guard has a FAULT that must fire and a CONTROL that must not; every FAULT is also shown
to FAIL on a copy with its guard removed (4.2).

| # | Guard | FAULT (must fire) | CONTROL (must not) |
|---|---|---|---|
| T1 | REFUSED | exit 7, gate text "FAIL ..."; exit 2, no verdict file | exit 2, CLEAN verdict, `crash`: CLEAN-INVOLUNTARY |
| T1b | gate timeout | exit 7, "FAIL the purity gate did not finish within 180s": INFRA; 5 never trip the stop | other gate text: REFUSED |
| T2 | budget ends | fresh, CLEAN: exit 4; exit 124 WITH a `wall-clock` verdict; exit 0 `play: stopped:` with `real_frames` = frames: CLEAN-BUDGET | `play: stopped:` at frames − 1: CLEAN-CHOSEN |
| T2b | missing verdict | exit 124, no verdict: HUNG, a blocker, 5 in a row trip the stop; exit 8, or exit 1 with no verdict: NOT CLEAN | `driver_killed` with no verdict; a `launch_died` row: INFRA, neither counting nor resetting |
| T3 | freshness | end state byte-identical to the start; frame off by over 5; mtime before the start: INFRA | a fresh state: a CLEAN class |
| T4 | NOT CLEAN | verdict `NOT CLEAN`, exit 0 | CLEAN |
| T5 | claim mismatch | `done: ch6_dewford reached`, proof false: not reached, mismatch, blocker | proof true: reached |
| T6 | clustering | one reason, other numbers: ONE key | other next milestone, class or end map: TWO |
| T7 | next unmet | `ch6_old_rod` (optional), `ch3_route104` (waypoint) never chosen; an absent mark listed UNREAD; a HUNG leg ending at its start: START truth | all marks present: the first unheld, `next_unmet_from: end` |
| T8 | ranking | two trees: the planted wall first on its own, absent on the other; INFRA, REFUSED, NOT CLEAN never in the denominator | no blocker: empty list, excluded counts shown |
| T9 | env allow-list | `AI_PLAYER_FAULT_NO_HINTS=1`, `POKEBOT_BOSSMODE_TOPUP=1`, `PYTHONPATH=x` in the parent never reach the launch (`subprocess.Popen` replaced in `live_step5`); a job naming `AI_PLAYER_FAULT_*` refused by `plan` and `run` | the 7 keys arrive; the command line byte-identical |
| T10 | trainer writes nothing tracked | stub `--trainer` batch from a temp git repo (also `--repo`) with committed `ledger.json`, `evidence/`, `evidence/trees/`: `git status --porcelain --untracked-files=all` unchanged | development mode there shows changes; with `begin`, `finish`, `snapshot_tree` patched to raise, trainer passes, development raises |
| T11 | placement | either mode: `--out` or stage in a work tree (ignored or not) or a `pokebot-learner` folder, or no valid `manifest.json`: exit 2, no ledger write | outside every work tree: accepted |
| T12 | seed band | trainer seed outside the band; no band row; an overlapping `registered` entry; on a temp ledger, `register` inside the band raises `Refused`; a second `reserve-band` | inside: accepted; `register` outside: accepted; `reserve-band` writes one row `ledger.py --check` and the trainer accept |
| T13 | development seeds | a seed named by any entry: refused; `begin` before the first launch (order asserted) | fresh: one `begin`, one `finish` |
| T14 | disk | 44.99 GB at start: no launch, no ledger write; 39.99 GB: ABORT; world 1,000,000,001 bytes: CUT-WORLD; `--out` 5,000,000,001: pending DROPPED | at each boundary: 45.0 GB starts; 40.0 GB no abort; 1,000,000,000 bytes kept; `--out` 5,000,000,000 launches; an older folder's world kills nothing |
| T15 | retention | a zip failing `testzip` keeps the raw folder | verified: raw deleted but `end_state`, `world_last`; profile deleted |
| T16 | experience filter | `visits`, `items`, `people`, `persons`, `met`, `closed`, `arrivals`, `transitions`, `news`, `heard`, `news_log`, `spoke`, warps' `uses/first/last/by`, connections' `by/frame`: absent; planted `rng_state`: dropped AND listed; other `tile_fields`: dropped, listed | allowed keys pass; tiles have 4 fields |
| T17 | origin | saved start: `practice` | chain: `new_game` |
| T18 | continue rule | not reached, purity not clean, tail not kept, guard-cut, STOP: later legs NOT RUN, reason given | all hold: next leg from the kept state and line |
| T19 | start custody | md5 differs; truth lacks `ch5_rival_meet`; no starter line: REFUSED before launch | matching start runs, `starter_from` kept |
| T20 | donor | donor missing: REFUSED with the `LaunchError` text | present: marker names `ai-fp-donor` |
| T21 | stage watch | a staged file changed: `STOP.txt`, no new leg | unchanged: no STOP |
| T22 | AI-only stop | 5 in a row of REFUSED, NOT CLEAN, HUNG mixed: no launch, `AI-ATTENTION.txt`, exit 6, no `ATTENTION.md` | 4, then CLEAN-* or CUT-WORLD: reset; INFRA between: neither |
| T23 | schema | `schema_version` 2: exit 2 | 1 reads |
| T24 | resume | killed batch resumed: no `run_id` twice, in-flight leg INFRA | P1's two arms on 3 shared seeds both run in full; a finished batch launches nothing |
| T25 | deadline | wall plus margins past `--deadline`: not launched; a WAIT reaching it: DROPPED | far from it: launched |
| T26 | scheduler | 10 other singles, P = 8: at most 6 own launches, rest WAIT; others fall to 0 mid-run: all 8 start, `not_started` empty; `run_regression.py` running: WAIT, then start; past `--max-wait`: DROPPED with the reason | 0 others: 8 at once |
| T27 | graded-driver agreement | the known divergence, asserted: a reached, clean leg with a 500,000,000-byte world continues here, stops in `continue_after` (C3), record says why | worlds under 300 MB: `reached` and the decision equal `leg_reached` and `continue_after`, leg by leg |
| T28 | imports | a planted `import ai_player.gates.frontier_probe` in a temp play module is found (AST walk, as `test_live_chain`'s ImportTests); `check_grader_imports.scan(root, ("ai_player.gates.frontier_probe",))` fails on a planted `from ai_player.personality import PERSONALITIES` in a temp probe copy | real tree: no importer; the scan clean; `GRADERS` unchanged |
| T29 | mutant staging | anchor hits 0 or 2 times: refused | once: the staged tree differs in exactly that file, named in the manifest |
| T30 | hard-coded copies | stub AI list with a 4th personality, or reordered tile fields: pin fails | 3 personalities equal `PERSONALITIES` as a set; 7 field names equal `to_dict()["tile_fields"]` (a test may import the AI) |

Suite target under 60 s; Phase A runs some inside `test_agent.py`'s 600 s (design risk 11).

### 4.2 Mutants of the runner itself

`revert_frontier.py`: about 28 single-edit mutants, one per guard above. For example: a hard kill with no verdict maps to
INFRA (the review's F1); `play: stopped:` with the budget run out maps to CLEAN-CHOSEN; the freshness check skipped;
`rng_state` allowed, or a warp's `uses` kept; the trainer calls `ledger.begin`; digits kept in `reason_norm`; optional
milestones not skipped; in `disk_decision`, `>` → `>=` at the world cut and the out cap, `<` → `<=` at the 40 GB abort
and the 45 GB floor; a WAIT drops the job; the stage watch removed; resume keyed by seed. Each names the test predicted to
catch it, and the prediction file is hashed BEFORE the first run (as BP-1 round 2's `revert_bossprep_hashed.py`). Every
anchor must hit exactly once; after the merge, `check_anchors.py` (on `wip/ch6-ch7` only) reads this table too.

### 4.3 The live proof

**P1, the planted wall at OLDALE TOWN (FAULT and CONTROL, on `main`'s code).** Arms REAL (the stage at the commit) and
WALL-OLDALE (plus ONE anchored edit in the staged brain: the navigator's planner treats every tile of `OLDALE_TOWN`
(0, 10) as a wall, and no go goal targets it; the builder picks the anchor, and an offline unit test shows the mutated
planner finds no path into OLDALE while the real one does). Jobs: the 3 diagonal pairs × the same 3 seeds, L1-L2.
Predictions, hashed into the ledger entry's bounds BEFORE the run:
- **(a) FAULT:** on WALL-OLDALE at least 2 of 3 chains end L1 not reached with next unmet `ch1_rival_route103`, and the
  top chapter-1 key on that tree names it. Predicted form CLEAN-CHOSEN with a reason beginning `play: stuck:`; a
  CLEAN-BUDGET end still counts toward (a), reported as a miss of the form. Confirmed at decomp pin `731ad5b`:
  `VAR_BIRCH_LAB_STATE` 3 is set right after the starter (`LittlerootTown_ProfessorBirchsLab/scripts.inc` :132-134) and
  NO loops back to YES (:138-141), so `ch1_lab` holds before the ROUTE 103 trip.
- **(b) CONTROL:** on REAL no chapter-1 key names `ch1_rival_route103`, and at least 2 of 3 chains reach `ch2_wally`.
- **(c) Reported:** with the pinned clock the paired arms replay identically until the wall bites (BP-1 round 2's C and
  B decision streams were IDENTICAL in 3 of 3 pairs, `bp1r2/STATE.md` 08:22); the first differing decision record
  should name an OLDALE plan or step.
- **PASS** = (a) and (b). If (a) fails, the blocker list cannot see a wall, and A1 is not done.

**P2, the planted wall at MR. BRINEY's cottage (inside WP1).** WALL-BRINEY walls `ROUTE104_MR_BRINEYS_HOUSE` (17, 0)
and, since the house is entered only by its door warp on ROUTE104, every warp or door tile leading to (17, 0), including
those the start's memory knows; a unit test like OLDALE's shows no path from ROUTE104 through that warp. **Predicted:**
key (6, `ch6_briney_house`, `play: stuck: …`, -, CLEAN-CHOSEN) first at chapter 6 on that tree, a CLEAN-BUDGET form
counting as in P1 (`FLAG_MR_BRINEY_SAILING_INTRO` is set only inside the house, `Route104_MrBrineysHouse/scripts.inc`
:25, :32). **CONTROL:** the 3 paired REAL J-F jobs never show it. This proves saved starts put a wall in the right
chapter.

**Trainer smoke (after the merge, needs the band row):** NG L1 and G3 L6, seeds 2,000,001-2,000,002, P = 2, outside every
work tree. **PASS:** the main checkout's `git status --porcelain --untracked-files=all` and `ledger.json`'s sha256
unchanged; nothing under `ai_player/evidence` newer than the start; both legs judged; records parse at version 1.

**WP1 CONTROLS** (in its prediction file): the diagonal J-N chains reach `ch5_rival_meet` in at least 2 of 3 (#101 was 6
of 6 on `dc0a4e69`; D15's "chapters 1-5 did not regress", in development form); at least 90% of legs run are judged;
experience `unclassified` empty. A miss is reported, never retuned (rule 8).

### 4.4 Definition of done for A1

1. The offline suite green; the mutants CAUGHT as predicted. 2. `run_regression.py --quick` and `run_gates.py` green.
3. The full regression lane passes on the commit (`suite_map.json` covers `ai_player/**`). 4. P1 PASSES. 5. The trainer
smoke PASSES. 6. WP1 ran; its chapters 1-7 blocker report with examples is in the evidence. 7. P2 PASSES. 8. Docs: `07`;
`04` (the top blocker becomes the next skill build); `03`; `05` (a KI for each new blocker holding at least 2 runs); `06`
for the 1 GB cut and CUT-WORLD, HUNG and the missing-verdict rule (D14 changed), the continue rule without the 300 MB
cap, the WAIT/DROP scheduler, the Phase A contract (D1 and D11 changed), and the persona of saved starts. 9. Tier 1.
10. Commits by explicit path.

## 5. What needs the chapter 6-7 merge, and what could be built before it

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
| **Total** | **38-65 (central 50)** | the sum of the parts |

At most 2 fix rounds; a third goes to the lead. `live_chain` took 7 rounds and 111.8 Mtok because its graded mode needed
a full threat model; A1 has no graded mode, no import-closure hashing, and only live_chain's threats (a) and (b).

### 6.2 Wall time

Build 5-8 h of agent time; P1 about 30 min; trainer smoke about 15 min; WP1 3-3.5 h of machine time (6.5 h worst); the
report about 1 h. Calendar: about 1.5-2 days after the merge, less if the offline build ran before it.

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
   memory (`WorldMemory.from_dict` uses `.get` defaults, :919 on the branch). Reach is split by start, and a start whose
   memory line reads "nothing (a new memory)" (`NEW_MEMORY`) is flagged.
7. **Practice is not the frontier** (D4; the report header). 8. **Key granularity:** the normalization changes only by a
   rule written before the next batch; raw examples are kept. 9. **Determinism:** paired arms on one seed replay;
   identical results are a determinism check, never a replication. 10. **Junctions:** a promotion or merge touching
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
