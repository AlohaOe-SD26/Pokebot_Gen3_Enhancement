# BUILD SPEC: `ai_player/gates/live_chain.py`, the GRADED New Game chain held-out (USER RULING 55)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). This is the build spec the `live-chain-driver` workflow
> gave its builder on 2026-11-05, kept verbatim because `ai_player/gates/live_chain.py` cites it (`SPEC`). The build
> deviated from it where `2026-11-05-LIVE-CHAIN-BUILD-REPORT.md` says (the critic's findings, the spec deviations,
> the verifier's findings and their fix round); the code and that report win over this text.


Written 2026-11-05 against main `cbbb3ec5` (the chapter-5 stops build, worktree `wf_5eff42ad-346-4`, is being merged
today). This is a SPEC. Nothing here has been built or run. The builder does NOT register and does NOT run graded seeds:
the lead registers seeds 6201-6206 after the merge, commits and pushes the registration, and then runs it (section 12).

---------------------------------------------------------------------------------------------------------------------------

## 0. What it is, in one paragraph

`live_chain.py` is a test-side driver. It plays **6 unbroken chains**: 3 personality/starter pairs times 2 seeds. Each
chain starts from a **real New Game** and plays **one leg per chapter**. Each leg starts from the save state AND the world
memory that the previous leg left. Each leg targets its chapter's end milestone, and the last leg targets `--to`.
The first graded use is `--to ch5_rival_meet`, which gives 5 legs: `ch1_pokedex`, `ch2_wally`, `ch3_rustboro`,
`ch4_roxanne` and `ch5_rival_meet`. Every leg goes through the real launcher (`live_step5.run_arm`), so purity is checked on
every launch. What a leg reached is read **from the game** on the state it left (the harness's `truth`, at the save-block
numbers in `milestones.json`). That read is freshness-checked by `L5.THIS_RUN`. A chain that misses a leg **stops**: it
fails, and its later legs are **NOT RUN**, with a row that says why. The batch is pre-registered in the seed ledger,
following `live_ki128.py`'s pattern: `BOUNDS_TEXT`, every constant, the legs and their proofs, the AI code's sha256 and
the grader files' sha256 are all hashed into the registration, so `ledger.begin` refuses a graded run on other numbers or
other code. The disk rule is `live_ki128`'s section 6, extended to chains (section 6 below).

---------------------------------------------------------------------------------------------------------------------------

## 1. Facts this spec rests on (read on 2026-11-05; re-check any marked ⚠ after the merge)

| # | Fact | Where it was read |
|---|---|---|
| F1 | `live_ki128.py` structure: `bounds`/`register`/`run`/`grade`/`read`/`child`. `registered_numbers()` hashes `BOUNDS_TEXT`, the constants, the start files, `ai_code_sha256()` and `GRADER_FILES`. `run_batch` runs at most 3 jobs, staggers them 15 s apart, runs a disk guard, measures and deletes `world.jsonl` (`measure_then_delete`, which retries 5 x 2 s), salvages a crashed child, writes one evidence file and calls `ledger.finish`. `grade_batch` returns typed `Check`s, and `batch_verdict` uses no waivers. | `ai_player/gates/live_ki128.py` (1,053 lines) |
| F2 | `test_live_ki128.py` has 55 tests on planted logs, worlds and rows. It is registered in `run_units.py` (`"test_live_ki128": ([...], 2)`). | `test_live_ki128.py`, `run_units.py:89-91` |
| F3 | **live_ki128's mutants were never put in a revert suite.** Its build report records "Test mutants (scratch `mutants.py`) 25 of 25 caught; the control fails 0 of 45", and its verifier recorded "Mutants: 6 of 6 KILLED". Both live in scratch. No revert driver names `live_ki128`. | `PROJECT KNOWLEDGE/ai-research-notes/2026-10-31-KI128-HELDOUT-DRIVER-REPORT.md` lines 58 and 211; `grep live_ki128 ai_player/gates/revert_*.py` returns no hit |
| F4 | `ledger.register` refuses any range that overlaps another entry of the family. `ledger.begin` refuses: a graded run that is unregistered, a run whose numbers sha differs from the registration, an overlap, and a development run on registered seeds. | `ai_player/gates/ledger.py:116-206` |
| F5 | **Seeds 6201-6206 are unused.** Neither the main ledger (85 entries) nor any of the six worktree ledgers names them. **Development seeds 6041-6060 are also unused** in all of them. | read with py over `ai_player/gates/ledger.json` and `.claude/worktrees/*/ai_player/gates/ledger.json` |
| F6 | `run_arm(arm, build_root, carried)` uses the module global `L5.PROFILE` (default `"ai-step5-play"`). A continuing arm sets `--state <carried state>` and `AI_PLAYER_WORLD=<carried world>`, reads `truth_before` from the state, copies the profile's `current_state.ss1` to `<run_dir>/end_state.ss1`, reads `truth_after`, and adds `carried[arm.name] = (end_state, <run_dir>/world.jsonl, earlier + records)` **only if world.jsonl exists**. It reads `actions.jsonl` and `ai_player.log` whole into memory. Its own timeout is `wall + 300` s. `truth_of` has a 600 s timeout. | `live_step5.py:435-508` |
| F7 | `L5.THIS_RUN` requires three things: the profile's state file was written after the run started, the end frame equals the start frame plus `real_frames` (within ±5), and the end md5 differs from the start md5. **Within a chain the profile is reused**, so a leg that writes no state would otherwise be graded on the previous leg's state. This check catches that. | `live_step5.py:524-536` |
| F8 | **The AI reads only the LAST line of `AI_PLAYER_WORLD`** (`read_world`: "The memory a run left: the LAST line of its world.jsonl"). So the deleted `world.jsonl` can be replaced by a file that holds only its last line, with no change to what the AI receives. | `ai_player/world/memory.py:864-871`; `mode.py:1314-1320` |
| F9 | The goal manager's own in-run memory is NOT carried between sessions. Only the world memory and the read pages are carried. | `ai_player/brain/goals.py:450`. A leg boundary resets it, the same as in the development chain probe. |
| F10 | The harness `truth` reads flags and vars at the numbers `milestones.json` names (`play_harness.tracked()`). Each number is decomp-checked by `extract_milestones.py --verify`. The marks are keyed by flag name, `VAR_<name>` and `TRAINER_<name>`. | `play_harness.py:68-120` |
| F11 | **Milestones (main, 28):** each has `chapter`, `optional` and `waypoint`. The proofs of the chapter ends are: `ch1_pokedex` RECEIVED_POKEDEX_FROM_BIRCH 2276, SYS_POKEDEX_GET 2145, ADVENTURE_STARTED 116; `ch2_wally` VAR_PETALBURG_GYM_STATE 16517 >= 2; `ch3_rustboro` VISITED_RUSTBORO_CITY 2169; `ch4_roxanne` DEFEATED_RUSTBORO_GYM 1264, BADGE01_GET 2151; `ch5_rival_meet` ENABLE_RIVAL_MATCH_CALL 253, VAR_RUSTBORO_CITY_STATE 16474 >= 8. The optional ones are `ch4_gym_trainers`, `ch5_goods_employee` and `ch5_rival_battle` (DEFEATED_RIVAL_RUSTBORO 211). The waypoints are `ch1_intro`, `ch2_route102` and `ch3_route104`. The worktree's diff to `milestones.json` changes only `looks.aqua_member` and one `ch5_rusturf_grunt` step. No proof changes. ⚠ re-read after the merge. | `ai_player/knowledge/milestones.json`; `git diff cbbb3ec5` in the worktree |
| F12 | The pinned decomp (`C:/Remote Projects/_decomp/pokeemerald`, HEAD `731ad5b`) gives the same numbers: FLAG_ENABLE_RIVAL_MATCH_CALL 0xFD=253, VAR_RUSTBORO_CITY_STATE 0x405A=16474, VAR_PETALBURG_GYM_STATE 0x4085=16517, FLAG_ADVENTURE_STARTED 0x74=116, FLAG_DEFEATED_RUSTBORO_GYM 0x4F0=1264, SYSTEM_FLAGS 0x860 (+1, +7, +0x19 and +0x84 give 2145, 2151, 2169 and 2276). `setflag FLAG_ENABLE_RIVAL_MATCH_CALL` + `setvar VAR_RUSTBORO_CITY_STATE, 8` appear together at `data/maps/RustboroCity/scripts.inc:740-741` and `:808-809`. | grep of `include/constants/flags.h`, `vars.h` and the map scripts |
| F13 | The "unexpected multichoice" stop is a line in the AI's log: `stuck: an unexpected multichoice on screen` (`brain/navigator.py:1158`). `mode.py:1308` has a talk form, `stuck: an unexpected <kind> while the person at <tile> talked`. The chapter-5 stop builds counted `ai_log.count("an unexpected multichoice on screen")`. | `s53/ch5stops/arms.py:114` |
| F14 | `check_grader_imports.GRADERS = (rate_step5, live_step5)`; `ALLOW` lets a grader take `ai_player.host.launcher` and the `ai_player.options` `ENV_*` names. `rate_step5.HASHED_FILES` does NOT include `check_grader_imports.py`. | `check_grader_imports.py:31-36`; `rate_step5.py:2894-2913` |
| F15 | `revert_safety_gates.py`'s DRIVER is hard-wired to `test_safety_gates`. It splits test ids on `"test_safety_gates."`, and its subject is the G1-G7 safety gates. `revert_step5` and `revert_r1` mutate the **AI package** and run AI-side suites. | `revert_safety_gates.py:154-165` |

### Development data the numbers come from

Chain probe (ledger #83, 2026-11-01, HEAD `ef3a5712`, seeds 5983-5985, evidence `ai_player/evidence/2026-11-01-chain-probe.txt`).
Each row gives real frames used / budget, elapsed seconds and world.jsonl bytes:

| Chain | L1 ch1_pokedex (330k) | L2 ch2_wally (330k) | L3 ch3_rustboro (600k) | L4 ch4_roxanne (900k) |
|---|---|---|---|---|
| 1 Story/TREECKO | 142,362 · 233.6 s · 7.1 MB | 103,422 · 180.0 s · 8.7 MB | 164,160 · 281.6 s · 12.0 MB | 85,108 · 180.4 s · 18.0 MB |
| 2 Catcher/TORCHIC | 147,727 · 242.3 s · 4.7 MB | 121,489 · 222.6 s · 5.4 MB | 174,320 · 303.7 s · 9.2 MB | 32,337 · 69.9 s · 2.4 MB |
| 3 Trainer/MUDKIP | 154,815 · 258.0 s · 6.2 MB | 135,368 · 243.8 s · 8.9 MB | 252,319 · 437.1 s · 20.2 MB | 49,350 · 97.1 s · 4.9 MB |

Every leg reached its target by the game. Purity was CLEAN 12 of 12 and L5.THIS_RUN PASSED 12 of 12. A chapter-3/4 world.jsonl
holds 26-41 snapshot lines of 0.65-0.78 MB each (measured on C1L4 and C3L3).

Chapter 5 from the three BADGE-1 chain ends, on the NEW code (the ch5-stops build):

| Run | Budget | C1 Story | C2 Catcher | C3 Trainer |
|---|---|---|---|---|
| builder probe #91 (seeds 6021-6023) | 900k | 251,345 f · 495.6 s · 91.5 MB | 158,697 f · 299.8 s · 13.6 MB | 220,692 f · 422.7 s · 58.1 MB |
| verifier VPROBE (seeds 6121-6123) | 600k | 172,781 f · 392 s · 43.2 MB | 215,704 f · 492 s · 58.9 MB | 167,204 f · 333 s · 15.6 MB |

In all 6 runs the game showed VAR_RUSTBORO_CITY_STATE 8. The flag ENABLE_RIVAL_MATCH_CALL was in the builder's checks and in each
verifier run's told milestone line. The unexpected-multichoice count was 0 in all 6. In VPROBE C3, DEFEATED_RIVAL_RUSTBORO was 0
(the optional `ch5_rival_battle`). That proves the target does not need the rival battle.

The new-code A/B CONTROL (#90, seeds 6031-6036, A and B identical, `s53/ch5stops/out/control/`) gives:

| Leg | Budget | Real frames | World.jsonl | Multichoice |
|---|---|---|---|---|
| L1 from a New Game | 330k | 126,079 / 147,398 / **164,417** | 4.8-5.5 MB | 0 |
| L3 from the chain probe's L2 ends | 600k | 156,821 / 137,820 / 215,049 | 10.1-15.0 MB | 0 |

**The pathological data point.** In the chapter-5 grunt batch (#89), seed 6016, which started on Route 116, wrote a
**774,013,568-byte** world.jsonl in 200,000 frames. That is the "after-battle break churn", and it is NOT fixed. The KI-129 runs
on the old code wrote about 2 GB each.

**What has NOT been measured.** No single unbroken New Game -> `ch5_rival_meet` chain has run on ONE code version. Legs 1-4 ran
on `ef3a5712`. The chapter-5 legs ran on the new code from those old-code ends. The A/B CONTROL (#90) found the new code's
decision records identical on chapter-1 and chapter-3 legs (6 of 6 pairs). That is evidence, not a chain. See rehearsal R2 in
section 12.

---------------------------------------------------------------------------------------------------------------------------

## 2. The legs, derived from `milestones.json`

```
legs_of(to, data) -> list[Leg]          # pure; data = the parsed milestones.json
  ms = data["milestones"] in FILE ORDER
  REFUSE unless the chapters in file order never decrease
  target = the milestone with id == to                      REFUSE if none
  REFUSE if target.optional                                 (an optional milestone may never be needed)
  REFUSE if target.waypoint is not None                     (its proof is a LATER milestone's: ch2_route102 is
                                                             VISITED_PETALBURG_CITY, so the AI stops on ROUTE102 while
                                                             the game proof is still false)
  for c in 1 .. target.chapter:
      if c == target.chapter: leg target = to
      else: leg target = the LAST milestone of chapter c in file order with optional == false and waypoint == null
            REFUSE if chapter c has none
      frames = FRAMES_BY_CHAPTER[c]                           REFUSE if missing (a chapter needs its OWN registered budget)
      proof  = target's "done" (flags, variables {number, at_least}, trainers)
  name the legs L1..Ln
```

On today's file, `legs_of("ch5_rival_meet")` gives L1 `ch1_pokedex` 330,000, L2 `ch2_wally` 330,000, L3 `ch3_rustboro` 600,000,
L4 `ch4_roxanne` 900,000 and L5 `ch5_rival_meet` 600,000. These are exactly the legs used so far. The "last non-optional,
non-waypoint" rule picks `ch4_roxanne` over `ch4_gym_trainers` (optional, and earlier anyway). It also keeps a future chapter-6
target from making chapter 5's leg `ch5_rival_battle` (optional, and last in the file).

Other examples:
- `legs_of("ch2_wally")` gives 2 legs (the rehearsals use this).
- `legs_of("ch3_woods")` gives 3 legs, and L3 targets `ch3_woods`.
- `ch5_rival_battle`, `ch2_route102` and an unknown id are each REFUSED.

`FRAMES_BY_CHAPTER = {1: 330000, 2: 330000, 3: 600000, 4: 900000, 5: 600000}`. A future `--to` in chapter 6 is refused until a
chapter-6 budget is added. That edit changes the grader hash, so it needs a new registration.

**How a leg reads "reached".** It uses the harness truth's marks on the state the leg left. A proof holds iff every flag
equals 1, every `VAR_<name>` is >= its `at_least` and every `TRAINER_<name>` equals 1. **A missing key is NOT held**: it is
reported as "missing", never defaulted. Reading the proof numbers from the AI-side `milestones.json` follows the
`play_harness` precedent (F10). It has a second path: the test file pins the 5 chapter-end proofs to the pinned decomp's
constants (F12), so a changed proof in `milestones.json` turns a test red. That file is also hashed into the registration
(section 5).

---------------------------------------------------------------------------------------------------------------------------

## 3. Chains, seeds, jobs

```
PAIRS     = (("S", "Story", "TREECKO"), ("C", "Catcher", "TORCHIC"), ("T", "Trainer", "MUDKIP"))
JOB_ORDER = (("S", 0), ("C", 2), ("T", 4), ("S", 1), ("C", 3), ("T", 5))   # 6 chains: one of each pair in the first wave
JOB_ORDER_3 = (("S", 0), ("C", 1), ("T", 2))                                # development --chains 3 only
GRADED_RUNS = {"ch5": {"seeds": (6201, 6206), "to": "ch5_rival_meet"}}      # one row per graded registration
```

- A chain has **one seed, used by every leg** (the chain-probe precedent). Graded: S 6201, 6202; C 6203, 6204; T 6205, 6206.
- Chain names are `LC-<pair>-<seed>`, for example `LC-S-6201`. Leg arm names are `<chain>-L<k>`. Run folders are unique
  inside a profile because `run_arm` names them `<time>-<arm name>`.
- **Profiles:** each chain has its own NEW profile, `ai-livechain-<seed>`, under `<build root>/profiles`. All legs of the
  chain share it. The batch is refused if any of the six profiles exists.
- **Concurrency:** a chain plays its legs one after another in one child process. At most `PARALLEL = 3` chains run at
  once, so at most 3 launcher runs run at once. Children start `STAGGER_SECONDS = 15` apart. Six chains make two waves.
- **The environment each leg gets** (from `live_step5.play_env` and run_arm). `clean_env` strips the caller's `AI_PLAYER_*`.
  | Leg | Variables |
  |---|---|
  | every leg | `AI_PLAYER_BRAIN=play`, `AI_PLAYER_SEED=<chain seed>`, `AI_PLAYER_PERSONALITY`, `AI_PLAYER_TARGET=<leg target>`, `AI_PLAYER_CLOCK=10:00` |
  | L1 only | `AI_PLAYER_STARTER` |
  | L2+ only | `AI_PLAYER_WORLD` |

  Nothing else is passed: no `AI_PLAYER_FAULT_*` and no memory file. The registered key set is a constant. A test asserts it
  for each leg.

---------------------------------------------------------------------------------------------------------------------------

## 4. One chain (the child): flow, custody, the continuation rule, early stop

`child JOB.json` plays one chain. `run_chain(job, run_leg=_real_run_leg)` receives `run_leg` as an argument (dependency
injection), so the tests drive it with a stub and no emulator.

```
REFUSE (row status REFUSED, no leg run) unless L5.PROFILE == job.profile, job.profile starts with PROFILE_PREFIX,
       and job.profile != "ai-step5-play"
carried = {}; prev = None
for leg in legs:
    if out/STOP.txt exists:                     -> this and later legs NOT RUN ("the code under test changed mid-batch")
    write out/<chain>/current_leg.json {leg, arm name, started}
    world_in = prev.kept_world (L2+) ; record world_in_sha256 = file_sha256(world_in)     (custody)
    arm = Arm(f"{chain}-{leg.name}", ..., leg.frames, WALL, play_env(personality, starter if L1 else None, leg.target),
              seed=chain seed, fresh=(L1), state_from=(None if L1 else prev arm name))
    run = run_leg(arm, build_root, carried)        # live: L5.run_arm
    check_purity(run, None); L5.check_after_is_this_run(run)
    row = leg row (section 8): truth subsets (frame, map, md5, marks, party_exp, party_ot, player_tid), proof before/after,
          reached, checks, harness_stop, the AI's outcome claim, command, env keys, world_in path + sha, run_dir
    world: size_first = stat; m = stream_world_tail(world.jsonl, keep=out/<chain>/<leg>/world_last.jsonl)
           (one pass, line by line: bytes, lines, bad lines, LAST non-blank line, last_ok = it parsed, its sha256, its
           maps-visited and tiles_learned); then measure_then_delete(world.jsonl); bytes = max(size_first, at deletion)
    log:   counts of "an unexpected <kind>" lines by kind, the multichoice count, and the "[AI-WORLD] memory from ..." line
    copy actions.jsonl, ai_player.log, purity.json, end_state.ss1, stdout.txt to out/<chain>/<leg>/
    carried[arm.name] = (run_dir/end_state.ss1, out/<chain>/<leg>/world_last.jsonl, earlier + records)   # replaces F6's path
    (go, why) = continue_after(row)
    write the row (out/<chain>/<leg>/row.json) and the chain row (out/rows/<chain>.json) after EVERY leg
    if not go: mark every later leg NOT RUN (reason f"the chain stopped at {leg.name}: {why}"); break
    prev = this leg
```

### Custody (graded as LC.CUSTODY)

Custody proves that each leg started from what the bounds say:

- **L1** ran with `--fresh`, with no `--state` and no `AI_PLAYER_WORLD`. Its `truth_before` is None and its env carried the
  chain's starter.
- **Leg k > 1** passes three tests:
  1. Its command holds `--state <leg k-1's end_state.ss1>` and no `--fresh`.
  2. Its `truth_before` (frame, state_md5) equals leg k-1's `truth_after` (frame, state_md5).
  3. The sha256 of its `AI_PLAYER_WORLD` file equals the sha256 of leg k-1's kept last line. That kept line is the
     byte-for-byte last non-blank line of leg k-1's world.jsonl, written by the stream that measured it.

For a correct driver these hold by construction. The check exists for a driver bug, such as starting leg k from the wrong state
or another chain's state, or passing the full or the wrong world file. That is why it has FAULT tests (section 9).

### THE CONTINUATION RULE (registered word for word in the bounds)

A chain CONTINUES after a leg iff all six conditions hold:

- **C1** The leg REACHED its target. That needs three things: its L5.THIS_RUN PASSED, every proof of its target holds on the
  state it left, and the proofs did NOT all hold on the state it started from. A fresh boot holds none. This last clause is
  CLAUDE.md session rule 4: the check must assert something the run did not already satisfy.
- **C2** Every counting purity check of the launch PASSED (`PURITY_IDS`, the same six as live_ki128).
- **C3** The leg's world.jsonl was measured, was **under 300,000,000 bytes** and was deleted. Its last line also parsed and
  was kept. If the last line is unparseable, the AI's `read_world` would raise on the original file, so the kept line is not
  "the memory the leg left".
- **C4** The disk guard did not kill the leg: `out/<chain>/<leg>.KILLED.txt` is absent.
- **C5** Custody held.
- **C6** `out/STOP.txt` is absent (the frozen tree had not moved).

**Otherwise the CHAIN STOPS.** It FAILS: it did not reach `--to`. Every later leg gets a row
`{status: "NOT RUN", reason: "the chain stopped at L<k>: <which of C1-C6 failed and both values>"}`. A NOT RUN leg is never
launched, and it is in **no** check's sample. It is not a purity sample, not a THIS_RUN sample and never "reached". The
evidence prints every NOT RUN leg with its reason.

Why stop on C2 and C3 too, and not only on C1: either failure already fails the batch. Playing on would spend up to hours of
emulator time and more disk on a verdict that is already FAIL. This is decision D3 in section 13. The alternative is to
continue those chains for information.

**A chain whose child dies** (a crash, or the orchestrator's chain watchdog, section 6) is SALVAGED by the orchestrator. The
leg that was running gets a row with no checks, so its purity and THIS_RUN read VACUOUS. Its world.jsonl is measured and
deleted. The legs after it are NOT RUN with the reason "the chain's process ended (see out/<chain>.child.log)".

---------------------------------------------------------------------------------------------------------------------------

## 5. The graded bounds (proposed numbers, with reasons)

### Constants (all hashed into the registration)

| Constant | Value | Why |
|---|---|---|
| `FRAMES_BY_CHAPTER` | 1: 330,000 · 2: 330,000 · 3: 600,000 · 4: 900,000 · 5: 600,000 | These are the probes' budgets, kept so the held-out is comparable with the development data. Headroom over the most any leg used: L1 330k / 164,417 (the new-code control) = 2.01x; L2 2.44x; L3 600k / 252,319 = 2.38x; L4 900k / 85,108 = 10.6x; L5 600k / 251,345 = 2.39x. The verifier's 600k L5 reached 3 of 3. |
| `WALL` | 3,600 s per leg | This was the probes' value. The longest leg took 495.6 s, a 7.3x margin. At the slowest rate seen (507 frames/s, C1 L5), 900k frames take about 1,775 s. A wall-clock stop is still recorded as the harness's (LC.ENDED). |
| `CHAINS`, `PARALLEL`, `STAGGER_SECONDS` | 6 · 3 · 15 | As the task asks, and as in live_ki128. |
| `REACH_MIN` | **5 of 6** | This was the lead's prior, and the numbers support it. If p is the true per-chain reach rate, P(at least 5 of 6) is 0.97 at p = 0.95, 0.89 at p = 0.90, 0.66 at p = 0.80, 0.36 at p = 0.67 and 0.11 at p = 0.50. So the bar separates "reliable" from "a coin flip" with one miss allowed. A bar of 6 of 6 would fail a p = 0.9 AI 47% of the time. The development data is 3 of 3 full chains through chapter 4 and 6 of 6 chapter-5 legs, from 3 starts. Development `--chains 3` uses chains - 1 = 2 of 3 (one miss allowed). |
| `WORLD_MAX_BYTES` | **300,000,000 per leg** (decimal) | This is the live_ki128 precedent. The largest healthy chain leg was 91.5 MB, so the cap is 3.3x that. The unfixed churn trajectory (774 MB in 200k frames) fails it, as it should. At a chapter-5 snapshot of about 1 MB, 300 MB is about 300 map changes in one leg, against 15-100 in healthy legs. Decision D2 below concerns the margin. |
| `GUARD_WORLD_BYTES`, `GUARD_FREE_GB` | 1,500,000,000 · 30.0 | Same as live_ki128. The guard is disk safety. It is not the graded bound. |
| `FREE_MIN_GB` | 40.0 | Same as live_ki128. The worst transient is 3 legs x 1.5 GB guard = 4.5 GB. |
| `CHAIN_WATCHDOG_SECONDS` | sum over legs of (WALL + 300 + 2 x 600) + 300 = **25,800 s** for 5 legs | This is run_arm's own timeout plus two truth reads per leg. A chain past it is killed and salvaged. |
| `PROFILE_PREFIX` | `ai-livechain-` | |
| `PURITY_IDS` | `L5.PURITY_GATE, L5.PURITY_CLEAN, L5.PURITY_PRESSES, L5.PURITY_FRAMES, L5.PURITY_BREACHES, L5.PURITY_PACKAGE` | live_ki128's set. `L5.PURITY_ENDED` is reported only, because a leg may end on its budget. |

### GRADED (every one must PASS; a VACUOUS check fails; no waivers)

| Id | Inputs | Rule | n / floor |
|---|---|---|---|
| **LC.REACH** | game + harness | At least REACH_MIN of the chains reach `--to`. A chain reaches iff every leg continued and the LAST leg REACHED (C1) its target. That is the game's proof on the state it left, which was not held at its start and has L5.THIS_RUN PASS. | chain rows / 6 |
| **LC.PURITY** | harness | On every leg that RAN, every `PURITY_IDS` check PASSES. | legs judged / legs that ran (and >= 6) |
| **LC.THIS_RUN** | harness + game | On every leg that RAN, L5.THIS_RUN PASSES. | same |
| **LC.WORLD_SIZE** | harness | On every leg that RAN, the world.jsonl, measured before deletion, is **under** 300,000,000 bytes. If the file grew between the first stat and the deletion, the larger size is graded. | legs measured / legs that ran |
| **LC.CUSTODY** | harness + game | Every leg that RAN started from what the bounds say (section 4). | legs that ran / legs that ran |
| **LC.STARTER** | game | For every chain whose L1 left a party, the party's first Pokemon is the chain's registered starter and its OT is the player's (`party_exp[0]`, `party_ot`, `player_tid`, as `grade_CH1` reads them). | such chains / REACH_MIN |
| **LC.PROFILES** | harness | Every leg that RAN has its `run_dir` directly under `<build root>/profiles/<its chain's profile>/ai_player_runs/`. | legs that ran / legs that ran |
| **LC.FROZEN** | harness | The frozen-tree watch saw no change from the batch's start to its verdict. | 1 / 1 |
| **LC.LEFTOVER** | harness | No python process whose command line names `ai-livechain-` is left after the batch. | 1 / 1 |

**The lead's prior.** The lead asked for reach >= 5 of 6, purity on every leg, THIS_RUN on every leg and the world cap. Those are
LC.REACH, LC.PURITY, LC.THIS_RUN and LC.WORLD_SIZE. **LC.CUSTODY, LC.STARTER and LC.PROFILES are ADDITIONS, proposed as GRADED.**
They are the only proofs that the batch played what was registered: each leg from the previous one's state and memory, the three
starters, and no write outside the six profiles. All three read the game or the harness only. If the lead disagrees, demote
them to REPORTED with one word each (decision D1).

**B1:** no graded check reads the AI's own record. `AI_INPUT_DEBT = {}`, and the evidence prints "B1 DEBT: none".

### REPORTED (information, never counted)

| Id | What | Source |
|---|---|---|
| LC.PROGRESS | Per chain: the legs reached, where it stopped and why. Per leg: real frames / budget (the highest share across chains is flagged as the budget's headroom) and elapsed / wall. | harness + game |
| **LC.MULTICHOICE** | **Per leg: the count of `an unexpected multichoice` lines in ai_player.log (the navigator's "on screen" form and the talk form). Beside it, every `an unexpected <kind>` count by kind and the first such line (300 chars).** The evidence head flags any leg > 0. Baseline: 0 in all six chain-end chapter-5 legs; 30,000 per run on the old code's forced-menu arms (#87). | AI's log (F13). The AI's own text, so REPORTED. |
| LC.OUTCOME | Per leg: the AI's exit claim ("play: done: <target> reached" or a stop reason) beside the game's proof, marked "agree" or "DISAGREE". | AI's verdict facts + game. Honesty is information here; step 5's arms grade it. |
| LC.ENDED | Per leg: `harness_stop` (by ai / harness / other, cause, real_frames). | harness |
| LC.OPTIONAL | At each chain's last leg that ran: the optional milestones' proofs for chapters up to the target's (`ch4_gym_trainers`, `ch5_goods_employee`, `ch5_rival_battle`). | game |
| LC.WORLD | Per leg: bytes, lines, bad lines, last-line bytes, deleted or not. Per chain: total bytes written. Any world.jsonl still present after the end sweep. | harness |
| LC.MEMORY | Per leg k > 1: whether the AI's `[AI-WORLD] memory from the last snapshot of <path>: N maps ..., T tiles learned` line names the kept file, and whether its N and T equal the kept line's own counts. | AI's log, so REPORTED. |
| LC.MAIN_PROFILE | Whether the run-folder listing of `<build root>/profiles/ai-step5-play/ai_player_runs` is unchanged from start to verdict. | harness |

**VERDICT:** PASS iff every GRADED check PASSES. **When a chain stops early**, it fails LC.REACH, and its later legs are NOT RUN,
printed as such, and in no other check's sample. One stopped chain still allows a PASS. Two do not.

### Draft `BOUNDS_TEXT`

The builder generates this from the constants and from `legs_of`. The tests assert its needles.

```
LIVE CHAIN GRADED HELD-OUT (USER RULING 55: the New Game test), build spec s53/chainheld/SPEC.md. Driver
ai_player/gates/live_chain.py.
CODE: the AI's files (ai_player/ outside gates/ and evidence/, no *.md, no __pycache__; CRLF read as LF) are hashed into
these numbers (ai_code_sha256), knowledge/milestones.json among them and also as milestones_sha256, as are the files that
grade the batch (grader_files): a graded run on any other AI code, milestone data or grader is refused by ledger.begin. The
frozen-tree watch must see no change from the batch's start to its verdict.
TARGET ch5_rival_meet. LEGS, one per chapter, derived from milestones.json (chapters 1-4: the LAST milestone of the chapter in
file order that is neither optional nor a waypoint; chapter 5: the target), each with its frame budget, a 3600 s wall clock
and the GAME's proof of its target (save block 1 at the numbers named, read by the harness's truth on the state the leg left):
  L1 ch1_pokedex, 330000 frames: RECEIVED_POKEDEX_FROM_BIRCH (2276) = 1, SYS_POKEDEX_GET (2145) = 1, ADVENTURE_STARTED (116) = 1
  L2 ch2_wally, 330000 frames: VAR_PETALBURG_GYM_STATE (16517) >= 2
  L3 ch3_rustboro, 600000 frames: VISITED_RUSTBORO_CITY (2169) = 1
  L4 ch4_roxanne, 900000 frames: DEFEATED_RUSTBORO_GYM (1264) = 1, BADGE01_GET (2151) = 1
  L5 ch5_rival_meet, 600000 frames: ENABLE_RIVAL_MATCH_CALL (253) = 1, VAR_RUSTBORO_CITY_STATE (16474) >= 8
CHAINS: 6 on the registered seeds, one seed per chain for all its legs; in launch order (personality, starter, seed offset):
Story TREECKO +0, Catcher TORCHIC +2, Trainer MUDKIP +4, Story TREECKO +1, Catcher TORCHIC +3, Trainer MUDKIP +5; at most 3
chains at once, 15 s apart; each chain in its own NEW profile ai-livechain-<seed> under the build root (refused if it exists).
EACH LEG: the real launcher through live_step5.run_arm, brain play, the chain's personality and seed, target the leg's; L1 from
a REAL New Game (--fresh, the chain's starter); each later leg from the end state the previous leg left (--state) and the
world memory it left (AI_PLAYER_WORLD = that leg's world.jsonl's LAST line, kept outside the repo; the AI reads only the last
line), with the pages read in the earlier legs.
A LEG REACHES its target iff its L5.THIS_RUN PASSES, every proof of its target holds on the state it left, and they did not
all hold on the state it started from (a fresh boot holds none); a mark the truth did not return is not held.
A CHAIN CONTINUES after a leg iff (C1) the leg reached its target, (C2) every counting purity check of its launch PASSED,
(C3) its world.jsonl was measured under 300000000 bytes and deleted and its last line parsed and was kept, (C4) the disk
guard did not kill it, (C5) its custody held, (C6) the frozen tree had not moved. Otherwise the chain STOPS: it fails, and
every later leg is NOT RUN (a row says so, with the reason) and is in no check's sample.
DISK: refused under 40 GB free on the build root's drive. During the batch a leg whose world.jsonl passes 1500000000 bytes,
or with under 30 GB free, has its launcher killed (recorded; its chain stops); a chain past 25800 s is killed and salvaged.
After each leg, before the next starts, its world.jsonl's size is recorded, it is streamed line by line (never a whole-file
read), its last line is written outside the repo, and it is DELETED.
GRADED (every one must PASS; a VACUOUS check fails; no waivers):
LC.REACH: at least 5 of the 6 chains reach ch5_rival_meet (every leg continued; the last leg reached its target).
LC.PURITY: on every leg that ran, the counting purity checks of live_step2.check_purity (L5.PURITY_GATE, L5.PURITY_CLEAN,
L5.PURITY_PRESSES, L5.PURITY_FRAMES, L5.PURITY_BREACHES, L5.PURITY_PACKAGE) all PASS. L5.PURITY_ENDED is reported only.
LC.THIS_RUN: every leg that ran: L5.THIS_RUN (live_step5.check_after_is_this_run) PASSES.
LC.WORLD_SIZE: every leg that ran: its world.jsonl, measured before its deletion, is under 300000000 bytes (300 MB).
LC.CUSTODY: every leg that ran started as above: L1 from --fresh with the chain's starter and no world memory; each later leg
from --state of the previous leg's end state, its start truth (frame, md5) equal to the previous leg's end truth, and an
AI_PLAYER_WORLD file whose sha256 equals the previous leg's kept last line's.
LC.STARTER: every chain whose first leg left a party: its first Pokemon is the chain's registered starter, the player's own (OT).
LC.PROFILES: every leg that ran wrote its run folder under its own chain's profile.
LC.FROZEN: the frozen-tree watch saw no change of the code under test from the batch's start to its verdict.
LC.LEFTOVER: no python process whose command line names ai-livechain- is left after the batch.
REPORTED (information, never counted): LC.PROGRESS (per chain the legs reached; per leg real frames of the budget, seconds of
the wall), LC.MULTICHOICE (per leg the 'an unexpected multichoice' lines of ai_player.log, and every 'an unexpected <kind>'
by kind), LC.OUTCOME (the AI's exit claim beside the game's proof), LC.ENDED (who ended each leg, the harness's own record),
LC.OPTIONAL (the optional milestones' proofs at each chain's end), LC.WORLD (bytes per leg and chain), LC.MEMORY (the AI's
memory line against the kept line), LC.MAIN_PROFILE (ai-step5-play's run folders unchanged).
VERDICT: PASS iff every GRADED check PASSES. Nothing is tuned to a grader (B1): a miss is reported, never re-run on new seeds.
```

### `registered_numbers()` (sha256 = the ledger's `bounds_sha256`)

`{family "story", driver "live_chain", run "ch5", seeds [6201, 6206], to, bounds_text, legs [{leg, chapter, target, frames, wall,
proof}], jobs [{chain, pair, personality, starter, seed}], parallel, stagger_seconds, reach_min, chains, free_min_gb,
world_max_bytes, guard_world_bytes, guard_free_gb, chain_watchdog_seconds, profile_prefix, purity_ids, env_keys,
milestones_sha256, ai_code_sha256, grader_files {path: text_sha256}}`.

`GRADER_FILES` is `live_chain.py, live_ki128.py` (its helpers are imported, section 8), plus `live_step5.py, live_step2.py,
grader_checks.py, play_harness.py, hands_harness.py, probe_eyes.py, probe_presses.py, rate_step5.py, provenance.py, ledger.py,
fixtures/item_flags.json`. `item_flags.json` is in the list because the truth reads it.

Development numbers add `{"purpose": "development", "chains", "leg_frames_override", "prediction_sha256"}`. So a development
ledger entry's bounds field covers its registered prediction.

---------------------------------------------------------------------------------------------------------------------------

## 6. The disk rule (live_ki128 section 6, extended to chains)

1. **Before the batch:** refuse under `FREE_MIN_GB = 40` free on the build root's drive. Refuse an `--out` inside the
   repository. Summaries, kept last lines and copies live outside it.
2. **During the batch:** the orchestrator polls every 5 s. For each running chain it stats only the **newest** run folder
   of the chain's profile. That folder is named by time, so the newest is the current leg, and its name ends `-L<k>`.
   - If that world.jsonl is over `GUARD_WORLD_BYTES` (1.5 GB), or free space is under `GUARD_FREE_GB` (30), the orchestrator
     kills the **descendants** of that chain's child: the current leg's launcher and emulator, never the child itself
     (`kill_descendants`). It writes `out/<chain>/<leg>.KILLED.txt` and records the event.
   - The child then measures and deletes as usual, sees the marker (C4) and stops the chain.
   - Only the newest folder is read, so a world.jsonl whose earlier deletion failed (left over in an older folder) cannot
     kill a healthy later leg.
   - **The chain watchdog:** a child alive past `CHAIN_WATCHDOG_SECONDS` has its whole tree killed and is salvaged.
3. **After each leg, inside the child, BEFORE the next leg starts:**
   - (a) Record the size.
   - (b) Stream the file once, line by line, never a whole-file read: its measures, the sha256 of its last non-blank line,
     and whether that line parses. Write the line to `out/<chain>/<leg>/world_last.jsonl`, outside the repo.
   - (c) **DELETE** world.jsonl (5 tries, 2 s apart; a failure is recorded, never a crash).
   - (d) The next leg's `AI_PLAYER_WORLD` is the kept last line (F8).
   - Kept per leg: `actions.jsonl, ai_player.log, purity.json, end_state.ss1, stdout.txt, world_last.jsonl, row.json`. About
     5 MB per leg on the development data, plus a 0.65-1 MB snapshot line.
4. **After the batch:** the orchestrator sweeps the six profiles for any world.jsonl still present. It retries the deletion
   and reports what it could not delete (LC.WORLD). It prints the `--out` folder's total size.
   - **The profiles are kept** (about 20 MB each once world.jsonl is gone). Deleting them is the lead's call after reading.
     The driver never deletes a profile (decision D6).
5. **Salvage:** a chain whose child left no row for its running leg gets that leg's world.jsonl measured and deleted, and a
   row with no checks (VACUOUS), exactly as live_ki128's `salvage`. The start frame is that leg's truth_before frame if
   recorded, else 0.
6. Nothing large enters the repository. The evidence file is text. `ledger.json` gets one entry.

**Known limit, not fixed here:** run_arm reads `actions.jsonl` and `ai_player.log` whole into memory (F6). A churn leg with a
huge actions log could use a lot of RAM. live_step5 is a shared grader file, so its change belongs to another item.

---------------------------------------------------------------------------------------------------------------------------

## 7. Subcommands and refusals

```
py -3.12 ai_player/gates/live_chain.py bounds (--run ch5 | --to ID [--chains 3|6])
    print BOUNDS_TEXT, the legs table, the numbers (without the text) and both sha256s (read only)
py -3.12 ai_player/gates/live_chain.py register --run ch5 [--note-file F]
    pre-register GRADED_RUNS["ch5"]'s seeds with registered_numbers()'s sha256 (BEFORE any run; the lead commits and pushes it)
py -3.12 ai_player/gates/live_chain.py run --purpose graded --run ch5 --out DIR [--build-root DIR]
py -3.12 ai_player/gates/live_chain.py run --purpose development --first-seed N --to ID --prediction-file F --out DIR
        [--chains 3|6] [--leg-frames L1=F[,L2=F...]] [--build-root DIR]
    exit 0 = PASS (graded) / ran (development), 1 = FAIL, 2 = refused before any leg
py -3.12 ai_player/gates/live_chain.py grade DIR      offline re-grade of a batch's rows (no ledger write)
py -3.12 ai_player/gates/live_chain.py read RUN_DIR [--start-frame N] [--truth]
    one leg folder, READ ONLY: its log counts, its memory line, its world.jsonl streamed (never kept, never deleted);
    --truth also runs the harness truth on its end_state.ss1 and prints every chapter-end proof
child JOB.json   internal: one chain
```

**`--purpose` has NO default** (live_ki128's default was graded). A builder, a test or a slip of the hand then cannot start a
graded batch by omission. The ledger also refuses an unregistered graded run.

**The development rehearsal mode** (`--purpose development`) can stop at any allowed milestone (`--to ch2_wally`). It can run
3 chains (`JOB_ORDER_3`), and `--leg-frames` can override a leg's budget. The override is for the live early-stop fault arm,
R1 in section 12. A prediction file is required: its sha256 goes into the development numbers, so it is the ledger entry's
bounds field and is registered before the runs. The text is printed in the evidence. The verdict line reads
`DEVELOPMENT, not graded: NO PASS (<verdict> by the registered rules)`, using `ledger.label`. The evidence is named
`<date>-chain-heldout-dev-<to>.txt`.

**Refusals (all checked before `ledger.begin`, exit 2; each has a FAULT and a CONTROL test):**

| # | Refused when | Why |
|---|---|---|
| R1 | `--out` resolves inside the repository | disk rule |
| R2 | graded with `--first-seed`, `--to`, `--chains` or `--leg-frames` given, or `--run` not in GRADED_RUNS | the registered numbers |
| R3 | development without `--first-seed`, `--to` or `--prediction-file` | every development batch is registered and predicted |
| R4 | `--to` is unknown, optional, a waypoint, or in a chapter without a budget | `legs_of` |
| R5 | the G-3 scan of `ai_player.gates.live_chain` finds an AI import | B1/G-3 |
| R6 | under 40 GB free | disk |
| R7 | any of the batch's profiles exists | a NEW profile each |
| R8 | the build root or `--out` lies inside a folder named `pokebot-learner`, or the build root is not under this repository | the learner clone is never touched |
| R9 | **graded only:** HEAD is not `origin/main` after a fetch, or `git status --porcelain -- ai_player` shows anything but untracked `ai_player/evidence/` files | the evidence must name a pushed commit, as the chain probe did |
| R10 | the ledger refuses (`ledger.Refused`) | registration |

---------------------------------------------------------------------------------------------------------------------------

## 8. Module layout (for the builder)

Pure functions are unit-tested on planted data. The orchestrator's pieces take their side effects as arguments
(`run_leg`, `spawn`, `poll`, `now`, `free`, `ledger_path`, `evidence_dir`).

- **Constants:** sections 3 and 5. `BOUNDS_TEXT` is generated by a function, `bounds_text(to, legs, chains)`, so development and
  graded use one generator. `AI_INPUT_DEBT = {}`.
- **Imports from `live_ki128`** (test side; its readers are covered by its 55 tests): `file_sha256, text_sha256,
  ai_code_sha256, measure_then_delete, kill_descendants, free_gb`. live_ki128.py is then in GRADER_FILES. Copying them
  instead would duplicate code; this is decision D7.
- `legs_of(to, data)`, `proof_holds(marks, proof) -> {"held": bool, "missing": [...], "values": {...}}`,
  `leg_reached(row)`, `continue_after(row) -> (bool, why)`, `custody(rows_of_chain) -> [problems]`,
  `stream_world_tail(path, keep)`, `log_counts(text_or_path)`, `guard_decision(world_bytes, free_gb) -> str | None`,
  `run_refusal(args, env) -> str | None`, `jobs_of(first, chains)`, `registered_numbers(...)`, `register(...)`, `begin(...)`,
  `run_chain(job, run_leg)`, `salvage_chain(job, build_root, out)`, `schedule(jobs, spawn, poll, parallel, stagger)`
  (it returns the most chains it ever had running; the tests read it), `grade_batch(chains, expected, frozen, leftover,
  reach_min)`, `batch_verdict`, `check_lines`, `run_batch(args, ...)`, `grade_dir`, `read_leg`, `main`.
- **Leg row:** `leg, chapter, target, proof, frames, wall, status (RAN | NOT RUN | REFUSED | SALVAGED), reason, exit, elapsed,
  run_dir, command, env_keys, world_in, world_in_sha256, truth_before, truth_after` (frame, map, state_md5, marks, stats,
  party_exp, party_ot, player_tid), `proof_before, proof_after, reached, checks, harness_stop, outcome, gate_line,
  measures {log: {lines, unexpected: {kind: n}, multichoice, first_unexpected, memory_line}, world: {bytes, lines,
  bad_lines, last_ok, last_sha256, last_bytes, maps_visited, tiles_learned}}, world_file {bytes, deleted, present},
  kept_world, kept_world_sha256, guard_killed, continue, why, notes`.
- **Chain row** `out/rows/<chain>.json`: `chain, pair, personality, starter, seed, profile, legs [...], reached_to,
  stopped_at, stop_reason`.
- **Evidence** `ai_player/evidence/<date>-chain-heldout.txt` (`keep_earlier`). It holds, in order:
  - the head line, `LIVE CHAIN HELD-OUT - GRADED - VERDICT <x> (failing: ...)`;
  - date, code, the ledger lines, the numbers sha, the build root, out and free space, the frozen line, leftovers, NOT RUN,
    the guard events, and any leg with LC.MULTICHOICE > 0;
  - the checks (each quoting both values) and `B1 DEBT: none`;
  - per chain, a progress line, then per leg: status, target, proof before -> after, reached, frames / budget, s / wall,
    stop, purity, THIS_RUN, custody, world bytes and deleted, the unexpected-line counts, the outcome claim against the
    game, the memory line and the run dir;
  - the BOUNDS TEXT.
- `out/results.json`: began, ended, purpose, run, to, chains, seeds, numbers sha, ledger id, frozen, leftover, not_run,
  guard events, verdict, checks. **`ledger.finish(entry, verdict_line, evidence_rel)`.**
- **Frozen tree:** the orchestrator holds the watch (`provenance.watch`) and checks it every 60 s and after the batch. It
  writes `out/STOP.txt` on the first move, and children check for that file before each leg (C6). It seals the verdict.
  `snapshot_tree` is kept, as in live_ki128.

---------------------------------------------------------------------------------------------------------------------------

## 9. Test plan: `ai_player/gates/test_live_chain.py` (offline, no emulator, target under 10 s)

Every guard has a **FAULT** case that must fail or refuse and a **CONTROL** case that must pass, as CLAUDE.md session rule 6
requires. Every test that touches a ledger uses a temp path. **`tearDownModule` asserts the real `ledger.json`'s bytes are
unchanged**, so a test that forgot its temp ledger turns the suite red. The cases are written as module-level functions
`case_<name>(M, tmp)` that take the module under test. The TestCase methods call them with the real `live_chain`, and the
mutants in section 10 call them with a mutated copy.

1. **LegsTests.**
   - CONTROL: `legs_of("ch5_rival_meet", real)` equals the 5 legs and budgets of section 2.
   - CONTROL: the proofs equal the pinned decomp's numbers, hard-coded in the test with their citations (`731ad5b
     include/constants/flags.h:136,279,1319,1351,1359,1380,1507; vars.h:110,153`). A changed proof in `milestones.json` turns
     this red, which gives the second path.
   - CONTROL: `ch2_wally` gives 2 legs, and `ch3_woods` gives 3.
   - FAULT: in a synthetic chapter whose last milestone is optional, the leg is the last NON-optional one.
   - FAULT: a waypoint is skipped.
   - REFUSED: unknown id, `ch5_rival_battle`, `ch4_gym_trainers`, `ch2_route102`, a synthetic chapter 6 (no budget), and
     file order that goes backwards in chapter.
2. **ProofTests.**
   - All flags at 1 holds. One flag at 0 does not.
   - `VAR_RUSTBORO_CITY_STATE` 7 does not hold and 8 holds (the boundary).
   - A missing key is not held and is listed as missing.
   - A trainer flag is checked.
   - A proof that already held at the start gives NOT reached (vacuous). A fresh-boot `truth_before` of None counts as not
     held.
   - A stale THIS_RUN gives not reached, even when the marks hold.
3. **ContinueTests.** For each of C1-C6, that condition alone false STOPS, with its reason naming both values (FAULT). All six
   true continues (CONTROL).
4. **ChainRunTests.** These use a stub `run_leg` that writes planted run folders (end_state, a multi-line world.jsonl,
   actions, a log, a verdict) and returns `L5.Run` objects with planted truths.
   - CONTROL: 5 legs RAN. Leg k's carried state is leg k-1's end_state. Leg k's `AI_PLAYER_WORLD` is leg k-1's
     `world_last.jsonl`, and its bytes equal the original file's last non-blank line. Every world.jsonl is deleted.
   - **FAULT:** leg 2 misses its proof. Then legs 3-5 are NOT RUN, each reason names L2 and C1, **and the stub was called
     exactly twice**.
   - FAULT: leg 1's state mtime precedes its start (THIS_RUN FAIL), so the chain stops.
   - FAULT: a truncated last world line (C3, last_ok false) stops the chain.
   - FAULT: a KILLED marker for L3 stops it at L3 (C4).
   - FAULT: `STOP.txt` written before L2 means L2-L5 are NOT RUN with the code-changed reason.
   - FAULT: a world over the cap stops the chain (C3).
   - **ENV:** L1's env holds the starter, and L2+ do not. No `AI_PLAYER_FAULT_*` appears. The key set equals `ENV_KEYS`.
   - **Profile guard:** with `L5.PROFILE = "ai-step5-play"`, or a name without the prefix, the child REFUSES and the stub is
     called 0 times (FAULT). The prefix passes (CONTROL).
   - **Read-only `read`:** `read_leg` on a planted folder leaves world.jsonl in place.
5. **GradeTests** (planted chain rows).
   - REACH: 5 of 6 PASS. 4 of 6 FAIL. 5 rows are VACUOUS. A chain stopped at L3 counts as not reaching. NOT RUN legs never
     count as reached.
   - PURITY: one middle leg FAIL gives FAIL. Each `PURITY_ID` failing alone gives FAIL (subTest). A chain stopped at L2 whose
     ran legs are clean gives PASS, so NOT RUN legs are not samples. A SALVAGED ran leg gives VACUOUS.
   - THIS_RUN: a stale middle leg gives FAIL. All fresh gives PASS.
   - WORLD_SIZE: exactly 300,000,000 gives FAIL. 299,999,999 gives PASS. A ran leg that was not measured gives VACUOUS.
   - CUSTODY: a wrong start md5 gives FAIL, and so does a wrong start frame. A wrong world sha gives FAIL. L1 with `--state`
     gives FAIL, and so does L1 with a world. CONTROL passes.
   - STARTER: a wrong species gives FAIL, and so does a wrong OT. CONTROL passes.
   - PROFILES: a run_dir under `ai-step5-play` gives FAIL. CONTROL passes.
   - FROZEN and LEFTOVER each have a fault and a control.
   - **REPORTED never counts:** a leg with 30,000 multichoice lines gives LC.MULTICHOICE "FAIL" in its line while the batch
     verdict stays PASS. LC.OPTIONAL with `DEFEATED_RIVAL_RUSTBORO` 0 changes nothing. An LC.OUTCOME DISAGREE changes nothing.
   - Every check quotes its bound: "at least 5 of 6", "300000000", "B1 DEBT: none".
6. **DiskTests.**
   - `measure_then_delete` on a sparse 301 MB file records the bytes and deletes the file. That leg then fails WORLD_SIZE
     and stops its chain.
   - `stream_world_tail` never reads a whole file. With `Path.read_text` and `Path.read_bytes` patched to raise, it still
     streams (CONTROL). A mutant that reads the whole file raises (FAULT).
   - `guard_decision`: 1,500,000,001 bytes kills and 1,500,000,000 does not. 29.9 GB free kills and 30.0 does not.
   - The guard reads only the newest run folder. A planted 2 GB world in an older folder does not kill (FAULT for the
     max-over-all mutant).
   - `salvage_chain` measures and deletes, writes a no-check row (VACUOUS), and the later legs are NOT RUN.
   - The end sweep deletes a leftover world.jsonl and reports it.
7. **RefusalTests** (pure `run_refusal`, with a fake git and a fake free function). R1-R10 each have a FAULT and a CONTROL.
   `--purpose` missing is an argparse error. Graded with dirty `ai_player/` or with HEAD ahead of `origin/main` is refused.
8. **LedgerTests** (temp ledger).
   - Register, then begin with the same numbers: OK.
   - Each of these is refused by `begin`: a changed leg budget, a changed `REACH_MIN`, a changed `WORLD_MAX_BYTES`, a changed
     `milestones.json` (a temp repo copy) and changed AI code.
   - An unregistered graded run is refused. A development run on registered seeds is refused.
   - The development numbers include the prediction sha, and a changed prediction changes the sha.
   - **No entry of the real ledger names 6201-6206, and `GRADED_RUNS["ch5"]` is (6201, 6206).**
   - The bounds text contains every leg line and each C1-C6.
9. **SchedulerTests.** With a fake spawn and poll, 6 chains never have more than **3** running, and the observed maximum is
   exactly 3. The launch order is JOB_ORDER. The stagger is applied.
10. **ImportTests.**
    - The G-3 scan of `ai_player.gates.live_chain` is empty (CONTROL). A brain import planted in a copy is caught (FAULT).
    - **No file of the AI's package** (`ai_player/` outside `gates/` and `evidence/`) contains the text `live_chain`
      (CONTROL). A copy with a planted `from ai_player.gates import live_chain` in `mode.py` is caught (FAULT).
11. **ReaderTests** (real lines): the navigator's multichoice line, the talk form, the battle and intro forms by kind, and
    the memory line (`[AI-WORLD] memory from the last snapshot of <path>: 32 maps (...), 17617 tiles learned, ...`).
12. **TieTests.**
    - **The AI reads only the last line.** `ai_player.world.memory.read_world` on a 3-snapshot planted world.jsonl and on its
      kept `world_last.jsonl` gives equal `snapshot()` dicts. This TEST imports the AI's reader; the driver never does.
    - FAULT: a planted reader that merges every line gives different dicts.
    - `FRAMES_BY_CHAPTER` covers every chapter that `legs_of` can return for `GRADED_RUNS`.

Register the suite in `run_units.py`: `"test_live_chain": ([str(GATES / "test_live_chain.py")], 2)`. Add
`"ai_player.gates.live_chain"` to `check_grader_imports.GRADERS`, so the lane's G-3 CLI walks it on every run.
`check_grader_imports.py` is not in `rate_step5.HASHED_FILES` (F14), so no registration moves. live_ki128 relied on its own
refusal and test only. The builder confirms the CLI still prints PASS.

---------------------------------------------------------------------------------------------------------------------------

## 10. Mutants: keep them in the TEST FILE (decision D5)

**Recommendation:** add a `MutantTests` class in `test_live_chain.py`, NOT a revert-suite registration. The reasons:

1. **The subject is wrong for every revert suite.** `revert_step5` and `revert_r1` mutate the AI package and prove that
   AI-side suites catch it. `live_chain` is not AI code, and those suites never import it (F15). `revert_safety_gates`
   is hard-wired to `test_safety_gates` and to G1-G7 (F15). Registering there means rewriting its DRIVER's module split,
   which would couple a lane revert suite to one held-out driver.
2. **The precedent is live_ki128** (F3). Its mutants were scratch-only (25 of 25 caught, the control failing 0 of 45; the
   verifier's 6 of 6 killed), and that was enough for a ONE-SHOT driver. **live_chain is reusable**: it will be edited for
   every later chapter, so its mutants must re-run on every lane, not only in a scratch folder that is later lost. A
   `MutantTests` class inside the suite that `run_units` already runs gives that durability, at a cost of seconds and with
   no revert-suite change.
3. **How it works.**
   - Each mutant is `(name, anchor, replacement, [case names that must fail])`, as in `revert_safety_gates.make_copy`. The
     anchor must occur **exactly once** in `live_chain.py`, or the test errors.
   - The mutated source is written to a temp file and loaded with `importlib.util.spec_from_file_location` as
     `live_chain_mut_<name>`. `REPO` is on `sys.path`, so its imports resolve.
   - Each named case is run against it, and the test asserts it raises `AssertionError`. Any other exception is reported
     as "broken copy" and fails the test.
   - **CONTROL M0:** the unmutated source, loaded the same way, passes every case that any mutant names. This proves the
     loader itself is not what fails.

**The mutants** (anchors are chosen at build time; each breaks one guard):

| Id | Breaks | A case that must fail |
|---|---|---|
| M1 | `>= REACH_MIN` becomes `>= REACH_MIN - 1` | 4 of 6 FAIL |
| M2 | the not-held-at-start clause is deleted | vacuous start |
| M3 | var `>=` becomes `>` | the VAR 8 boundary |
| M4 | a missing mark defaults to held | missing key |
| M5 | the chain does not stop on C1 | stub called twice |
| M6 | NOT RUN legs are counted in the purity sample | stopped-chain purity |
| M7 | one `PURITY_ID` is dropped | each-id subTest |
| M8 | THIS_RUN reads only the last leg | stale middle leg |
| M9 | the world cap `>=` becomes `>` | exactly 300 MB |
| M10 | the `measure_then_delete` call is deleted | world deleted |
| M11 | the next leg's world is the original world.jsonl | custody world path |
| M12 | the custody md5 comparison is deleted | wrong start md5 |
| M13 | the starter check compares the wrong field | wrong species |
| M14 | the optional filter in `legs_of` is deleted | synthetic optional chapter end |
| M15 | refusal R1 (out in the repo) is deleted | R1 fault |
| M16 | refusal R2 (graded with a dev seed) is deleted | R2 fault |
| M17 | refusal R7 (existing profile) is deleted | R7 fault |
| M18 | the free floor is deleted | R6 fault |
| M19 | the child profile guard is deleted | default-profile refusal |
| M20 | `PARALLEL` becomes 4 | scheduler max 3 |
| M21 | LC.MULTICHOICE becomes GRADED | the REPORTED-never-counts case |
| M22 | `legs` is dropped from `registered_numbers` | changed budget refused |
| M23 | the guard threshold check is deleted | `guard_decision` |
| M24 | NOT RUN rows are not written | the rows exist |
| M25 | refusal R8 (learner clone) is deleted | R8 fault |
| M26 | the guard reads the max over all folders | old 2 GB folder |
| M27 | `last_ok` is ignored in C3 | truncated last line |
| M28 | `stream_world_tail` uses `read_bytes` | the no-whole-read patch |

The builder ALSO runs one independent adversarial verifier: a fresh agent, not a fork, that writes its own mutants. This is
project practice; live_ki128's verifier found the K8.EDGE_WINDOW gap.

---------------------------------------------------------------------------------------------------------------------------

## 11. What it must NOT do, and how each is enforced

| Must not | Enforced by |
|---|---|
| **Import anything into the AI**, or change what the AI plays with | The driver is under `ai_player/gates/`, which `ai_code_sha256` excludes. ImportTests (10) assert that no AI file names `live_chain`. The G-3 scan covers the other direction: the driver takes no AI value (R5, plus `check_grader_imports.GRADERS`). The env passed is exactly `ENV_KEYS` (ChainRunTests ENV). No fault or test switch is ever set. |
| **Touch the learner clone** (`C:/Remote Projects/pokebot-learner`) | R8 refuses a build root or out under any folder named `pokebot-learner`, and the build root must be under this repository. The driver names no path of the clone. `leftover_processes` matches only `ai-livechain-`, so it never names the tuner's lanes. The driver kills only descendants of children it started (`kill_descendants` of its own child PIDs). |
| **Write to the main sandbox profile** | Read here as `ai-step5-play`, `live_step5.PROFILE`'s default: the profile `run_arm` writes when the global is not re-pointed. More broadly, the driver writes to no profile but its own six. The child guard (R-child, test 4) refuses unless `L5.PROFILE` is the job's prefixed profile. LC.PROFILES (graded) proves every run folder's home. LC.MAIN_PROFILE (reported) shows `ai-step5-play` unchanged. |
| **Run graded seeds itself** (the builder) | `--purpose` has no default. A graded run is refused unless registered (ledger), unless HEAD is `origin/main` with a clean `ai_player/` (R9), and unless it has exactly `--run ch5`. The tests never use the real ledger, and `tearDownModule` checks its bytes. **The builder must not run `register`, and must not run `run --purpose graded`.** The rehearsals use development seeds 6041-6060 only. |
| Write large files into the repo | R1, plus the disk rule. |
| Kill anything but its own runs | The guard kills only a chain child's descendants. The watchdog kills only a chain child's tree. |

---------------------------------------------------------------------------------------------------------------------------

## 12. Rehearsals (development) and the lead's registration procedure

**Rehearsals.** Each runs on development seeds, with a prediction file written and registered (by sha256, through the
development numbers) BEFORE the run:

| Run | Seeds | Command | Prediction (draft) | Cost |
|---|---|---|---|---|
| **R0 plumbing** (required) | 6041-6046 | `--to ch2_wally --chains 6` | 6 of 6 reach `ch2_wally`. 12 of 12 legs: purity CLEAN, THIS_RUN PASS, custody PASS. Every world.jsonl measured, under 300 MB (the development maximum on these legs was 8.9 MB), deleted, and its last line kept. LC.STARTER 6 of 6. Concurrency maximum exactly 3. 0 leftovers. Multichoice 0 on every leg. Verdict by the registered rules: PASS. | 2 waves of about 8-9 min, so about 20-30 min |
| **R1 early-stop fault arm** (required) | 6047-6049 | `--to ch2_wally --chains 3 --leg-frames L1=30000` | 3 of 3 L1 legs end at their 30,000-frame budget without `ch1_pokedex` (it took 126k-164k frames in development). Who ends the leg is recorded by LC.ENDED: most likely the AI's own bound (exit 0, `by: ai`), as the old code's 30,000-frame menu arms ended, or else the session's frame budget (exit 4). THIS_RUN PASS and purity CLEAN 3 of 3. **L2 NOT RUN 3 of 3**, with reasons naming L1 and C1. LC.REACH FAIL (0 of 3). Verdict FAIL. This is the live proof of the early-stop path. Short 30,000-frame arms passed THIS_RUN in the chapter-5 menu batches. | about 3 min |
| **R2 full dress** (recommended) | 6050-6052 (6053-6055 optional) | `--to ch5_rival_meet --chains 3` | 3 of 3 reach `ch5_rival_meet`, and every graded check PASSES. Leg frames fall within the development ranges in section 1. Multichoice 0. **This is the first unbroken New Game -> chapter 5 chain on ONE code version** (section 1). | about 25-30 min |

The bounds in section 5 are fixed BEFORE R2. If R2 fails a bound, the answer is a code fix and a new development round. It is
never a looser bound (the user's rule). Seeds 6056-6060 stay spare.

**Who runs what.** The builder runs R0 and R1 on its build tree, on development seeds only (section 14). The lead does
everything below. The builder does none of steps 4-6.

1. Merge the chapter-5 stops build and this driver to main, with R0's and R1's evidence. The lane is green
   (`run_regression.py --full`), and the Tier 0 and Tier 1 doc checks pass.
2. Run R2, if approved (D8), on the merged code, and commit its evidence. An independent adversarial verifier reviews the
   driver, and its findings are fixed. If that changes the driver, R0 is re-run on spare seeds from 6056-6060.
3. Run `py -3.12 ai_player/gates/extract_milestones.py --verify` on the merged `milestones.json`, and keep its PASS line for
   the note. Run `py -3.12 ai_player/gates/ledger.py --check` after the merge, since the worktree added entries #86-#91.
4. Run `py -3.12 ai_player/gates/live_chain.py bounds --run ch5`, then read the legs and the numbers.
5. Run `py -3.12 ai_player/gates/live_chain.py register --run ch5 --note-file <note>`. Stage `ai_player/gates/ledger.json`
   by its explicit path, commit, and push. That is the registration commit.
6. On that pushed commit: `py -3.12 ai_player/gates/live_chain.py run --purpose graded --run ch5 --out <outside the repo>`.
   Do this after any regression lane has finished. The bot tuner may run beside it, as it did during the chain probe.
   - Typical wall time is about 50-60 min: two waves of about 25 min per chain (development chain sums were 1,140-1,460 s).
   - The worst case is about 14 h (2 x the 25,800 s watchdog).
   - The verdict is in the evidence file and in ledger entry `done`. A miss is reported and never re-run on new seeds.

---------------------------------------------------------------------------------------------------------------------------

## 13. Decisions for the lead (each with a recommendation), and known limits

| # | Decision | Recommendation |
|---|---|---|
| D1 | LC.CUSTODY, LC.STARTER and LC.PROFILES go beyond the prior. Should they be GRADED or REPORTED? | **GRADED.** They prove that the run is the one registered, and they read only the game or the harness. |
| D2 | `WORLD_MAX_BYTES` at 300 MB (3.3x the largest healthy leg; the live_ki128 precedent), or 500 MB (5.5x, still under the 774 MB churn)? The churn defect (b) is unfixed, so any chain that hits it fails the batch. A healthy leg 3.3x the largest seen would also fail. | **300 MB.** It keeps the precedent and sits near the middle between healthy (91.5 MB) and churn (774 MB). Snapshot lines grow with each chapter, so a later chapter's registration should revisit the cap. |
| D3 | Stop a chain on a purity or world-size failure (C2/C3), or play on for information? | **Stop.** The verdict is already FAIL, and playing on spends hours of emulation and more disk. |
| D4 | LC.OUTCOME (the AI's claim against the game): REPORTED, or HONESTY (graded)? | **REPORTED.** The held-out measures reaching, and the step-5 arms grade honesty. |
| D5 | Mutants in the test file (section 10), or a revert-suite registration? | **In the test file.** |
| D6 | Keep the six profiles after the batch (about 20 MB each without world.jsonl)? | **Keep.** Deletion is a separate, explicit act. |
| D7 | Import live_ki128's helpers (putting it in GRADER_FILES), or copy them? | **Import.** |
| D8 | Full-dress rehearsal R2 before registering? | **Yes**, for the reason in section 1. |

**Known limits** (stated in the evidence, not hidden):

- Legs are separate launcher sessions. The game state and the world memory are carried exactly (custody), but the goal
  manager's in-run memory restarts at each leg (F9). This matches the development chain.
- The legs hand the game over by savestate. They do not save through the game, and USER RULING 51's saving is not part of
  this test.
- run_arm loads whole action logs into memory (section 6).
- The world cap is per leg, and later chapters' snapshot lines are larger (D2).

---------------------------------------------------------------------------------------------------------------------------

## 14. The builder's definition of done

1. `ai_player/gates/live_chain.py` and `ai_player/gates/test_live_chain.py` exist as specified. The suite passes. The CONTROL
   M0 passes, and **every mutant M1-M28 fails its named cases** (counted in the test output).
2. `run_units.py` and `check_grader_imports.GRADERS` have their new entries (section 9). `check_grader_imports.py` prints
   PASS. `check_purity`, `check_fairness`, `check_paths`, `call_census` and `ledger.py --check` pass.
3. **An orchestrator dry run** with stub launches, a temporary ledger and a temporary evidence folder exercises 6 chains: one
   is stopped at L2 by a planted miss, and one is salvaged. It shows 2 waves, at most 3 at once, NOT RUN rows, world files
   measured and deleted, the ledger finished, and the verdict computed. live_ki128 did the same.
4. `live_chain.py bounds --run ch5` prints the legs of section 2, and the build report records the numbers sha256 for the
   tree it was built on. That sha will differ after the merge, because `ai_code_sha256` changes. The lead re-reads it at
   registration.
5. **R0 and R1 are run on development seeds** with registered predictions, and their evidence is committed (R2 if the lead
   approves). **Nothing graded is registered or run.**
6. A build report lists the files, the tests, the mutant table, the rehearsal results against their predictions, and the
   decisions D1-D8 as built.
