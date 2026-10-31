> **Filed 2026-10-31** by the orchestrating session: the report of ROUND 1 of `2026-10-31-KI128-KI129-BUILD-SPEC.md` (KI-128 and KI-129 Part A), built by the workflow `ki128-ki129a-build`: a builder in a worktree, then an independent adversarial verifier (4 findings, 0 MAJOR; no fix round). Both sections follow VERBATIM (subagents cannot write report files). Applied to `main` byte for byte (sha256) by the session's `apply_r1.py`: 71 files copied, 2 skipped on purpose (the builder's LEAVE OUT: an intermediate tree's zip and its archive); the verifier's ledger entries #73-#75 were added.
> **The headline: all 3 long development runs from A0's end states reached RUSTBORO CITY** (the builder's S2 and S3, seeds 5922 and 5923; the verifier's S1, seed 5944), and the chapter 1-2 control's decisions were identical with and without the fix. These are DEVELOPMENT runs, one trajectory each; the graded held-out (the spec's section 5) is still to run, and Part A's live necessity is shown only offline (the verifier's V2).

## The builder's section

## KI-128 + KI-129 Part A: built, offline-proven, live-proven (DEVELOPMENT only, nothing graded)

All three batches are development runs; none is graded. The worktree `wf_94ccdf92-1e1-1` sits on HEAD 818d3706 with uncommitted changes, and nothing was committed. Times below are this PC's clock (Los Angeles), 2026-10-31.

**Headline, with its caveat.**
- KI-128 is what changed the first event on all three A0 starts. The spec's mechanism (Part A decides S1/S3, and KI-128 alone loops) was refuted live:
  - on S1 and S3, W (KI-128 alone) walked into the woods at its very first decision;
  - Part A alone helped S1, and on S3 it made things worse: a new loop on OLDALE|ROUTE103, the critic's F5.
- PAW reached RUSTBORO CITY in both long runs. Each is one trajectory, so this is a sample of 2, not a rate.
- On the 6 chapter 1-2 arms, PAW made exactly the same decisions as none.

### 1. KI-128 (spec section 1)
**What was built**
- **`knowledge/atlas.py`** is the loader. It reads only `maps[].id` and `maps[].map_type`, with a cache. `open_map` returns True for ROUTE, TOWN, CITY and OCEAN_ROUTE, False for any other type, and None for a map the atlas does not hold.
- **`goals.open_way`** is used only at :679, :691, :696 and :719. The six errand sites keep OUTDOOR, and the OUTDOOR comment was fixed.
- **`check_fairness.py`:**
  - `LOADERS["knowledge/atlas.py"]` is added.
  - `KNOWLEDGE_FIELDS["world/maps.json"]` covers every path. Recount: 58 distinct key paths, plus 1,043 children of `_files`, which the meta subtree `_*` covers. `trainers[].elevation` is classified AI (the spec does not list it).
  - `schema_problems` and `_sources` walk only the world files a loader names.
  - B1 now knows `maps.json`.
- **Deviation 1, measured.** Walking maps.json literally makes `developer_keys` lose `x` and `y`, because maps.json's AI coordinates count as "elsewhere". That weakens B2 on the milestones' measured coordinates. `developer_keys` therefore does not let a world file's AI names excuse a name. The mutant without this rule fails test_safety_gates G4: `["'measured'"] != ["'measured'", "'x'"]`.
  - Developer-only keys now: decomp, flag, label, line, measured, note, object, ref, script, shared_events_map, shared_scripts_map, state, taught_by, x, y.
- **`_reader`.** maps.json has its own `MAPS_READER`; the shared READER is unchanged.
  - **Deviation 2.** events.json, items_gifts.json and the 48 chapter packs record maps.json's sha256, so they were re-pinned.
  - `extract_world --check`, extract_items/extract_events `--check` and `make_chapter_pack --all --check` all PASS.
  - The diffs are only `_reader` and that sha line.
- **test_kb2:**
  - Both named tests were changed on purpose. The allowlist comes from LOADERS, and the bosses.json fault fixture is kept.
  - New tests: K-F3 (planted flag/script read, B1 naming maps.json, an unclassified maps.json key; docstring mentions do not fire) and K-C6 (pinned decomp: PetalburgWoods is MAP_TYPE_ROUTE, warps (14,5)/(15,5) to Route104 warps 2/3 at (10,30)/(11,30)).
- **Blast radius** (`blast_radius.py`): 19 maps become open, including PETALBURG_WOODS and EVER_GRANDE_CITY. No regex-open map is closed.

### 2. KI-129 Part A (spec section 2)
- The new `navigator.in_map_walls` is shared by `_next_step` (no behaviour change; G272/G273 still CAUGHT) and `cut_off`.
- On the committed real-memory fixture (A0-1's ROUTE104, 3 warps, 1 PETALBURG connection), from (39,63):
  - **818d3706** cuts [] and promise stays 6.
  - **Part A** cuts (32,42),(33,43),(33,44),(33,45),(33,46),(33,47) and promise goes 6 -> 0.
  - From (33,45), nothing is cut (P-C1).
- `candidates` is unchanged, as the spec says. Live, this means the pocket targets are still offered and fail one by one.

### 3. Offline proof
- **Gates and tests:**

| Gate | Result |
|---|---|
| test_goals | 272 OK |
| test_kb2 | 121 OK |
| test_host | 37 OK |
| run_units | OVERALL PASS |
| check_purity | PASS |
| check_fairness | PASS |
| call_census | PASS (after G414-G418 and tests K-F7/K-F8/K-F9) |

- **FAULT at 818d3706:** K-F1, K-F2, K-F6, K-F7, K-F8, P-F1 and P-F2 fail with the expected lines; with 818d3706's check_fairness, the three kb2 tests fail.
- **K-F5 on A0-1 and A0-3:**
  - at 818d3706: `'ROUTE104'`, `[False, False]`;
  - with the fix: `None`, `[True, True]`;
  - the Briney control stays `[False]`.
- **Mutant drivers:**

| Driver | Result |
|---|---|
| revert_step5 (full) | 412 CAUGHT + 2 REDUNDANT as predicted, of 414; PASS |
| revert_safety_gates | 23/23; PASS |
| revert_r1 | 555 + 1 of 556; PASS |
| loader-reads-.flag mutant | check_fairness FAIL (B2, atlas.py:38) |

- **New mutants G407-G418:** the spec's (:691, :696, :719, open_map None, cut_off without edge walls), plus :679, :1217 (which shows K-C5 is not vacuous) and the 5 census call deletions.
- **regression_due:** the drivers passed, but it still lists all 6 suites DUE. Only `run_regression --full` writes the evidence names it reads; that was not run.

### 4. Live proof (spec 3.2-3.4)
**How the runs were made**
- One stage, `s53/fix/stage`, using live_r1's mirror method: junctions to the main sandbox, read only.
- Four arm trees (818d3706 zip + overlay), checked by tree digest:

| Arm | Digest |
|---|---|
| none | 16a130f4 |
| PA | af9a118c |
| W | dcb93398 |
| PAW | 3c9cf424 |

- The driver is `s53/fix/build/fx_probe.py`: live_step5.run_arm, a purity gate per launch, a disk guard (never fired), and after each run a streamed summary followed by deleting world.jsonl.
- Purity was CLEAN on all 30 launches. The main sandbox had 0 new paths, and C: stayed at 64.7 GB free or more.
- The stage was deleted, junctions unlinked first. The main sandbox's linked folders kept the same file counts: modules 4391, plugins 40, mgba 43, roms 2.

**Predictions, registered before each batch** (sha256 in the ledger bounds; not committed, see stops):
- smoke: 12:42 PM, ledger #69
- factorial: 12:44 PM, `3da176e4…`, ledger #70
- long: 12:55 PM, `5c35b758…`, ledger #71
- control: written 12:56 PM, run at 1:00 PM, `a4faa23c…`, ledger #72

**Factorial (10k frames).** D1 = a back/route/door decision naming the woods among the first 20 on ROUTE104; D2 = crossings of the start's edge.

| Arm | S1 | S2 | S3 |
|---|---|---|---|
| none | D2 196 | D2 30 | D2 194 |
| PA | D1 True, D2 0, woods via the fallback (-44.5), after 6 failed pocket targets | records identical to none (one trajectory replayed) | "first to ROUTE103", then 157 OLDALE\|ROUTE103 crossings |
| W | D1 True, D2 0: woods back (-45.45) at the first decision | D2 1; "first to PETALBURG_WOODS" told 2 times | D1 True, D2 0 |
| PAW | D1 True, D2 0 | identical to W | D1 False as defined, D2 0, into the woods |

Failed predictions, kept as information:
- **none S2, D2 ≥ 100:** got 30. The loop started 8,151 frames in, after a pick_up and a catch roam.
- **PA S3, "as S1":** wrong. F5 had predicted it offline.
- **W S1 and W S3, "as none":** wrong. F2's offline figure assumed the pockets were already excluded.
- **D1-as-defined for W/PAW S2 and PAW S3:** False. Their first decision was "route (10,39): it leads toward the goal", the woods door, but the reason does not name the woods.

Vacuity rule: it fired on S1 (no PA-vs-W difference), so S1 got no long run. S2 and S3 differ.

**Long PAW (300k cap, seeds 5922/5923):**
- Both runs reached RUSTBORO CITY and the AI ended itself with "done: ch3_rustboro reached":

| Run | Frames used | Woods exit (first ROUTE104 y < 31) | Rustboro at | E2 | E3 (max same-edge in one intent) |
|---|---|---|---|---|---|
| S2 | 37,599 | (14,5) -> (10,30) at f572678 | f592439 | 0 | 1 |
| S3 | 95,974 | (15,5) -> (11,30) at f689171 | f714136 | 0 | 1 |

- On S3 the woods' grunt scene (ch3_woods) was done at f639165 on the way.
- E1 held 2 of 2, E2 held (0 and 0), E3 held.

**Control (12 runs, 330k):**
- Every decide record is identical, none vs PAW, in all 6 arms (141, 217, 244, 185, 82, 223 records). The marks and real frames match, and all 12 runs reached their target.
- The only record differences are not decisions:
  - 3 world "say" lines (CH1C 1, CH1M 2) where a printed dict's two keys come out in the opposite order (string hash order between processes);
  - the eyes' wall-clock `cost=N.NNms`, which is normalised. Before normalising, it was CH1T's only difference: 2 records, 1.40 vs 1.44 ms.
- This is a determinism check (one trajectory replayed per arm), not a replication.

### 5. Things the orchestrator should know
- **New observation:** in W/PAW S2, the go to the woods ended "done" on ROUTE104. It was followed by item-ball pick_up attempts at (29,53) that ended "interrupted on the way: played out". This did not block the long run.
- **PAW S3:** the long run walked from the woods' east exit into the ROUTE104 strip at (33,42). The strip is reachable from inside the woods, which is consistent with Part A's cut.
- **Evidence files:**
  - KI-128 batches: `ai_player/evidence/2026-10-31-ki128-{factorial,long,control}.txt`
  - revert drivers: `2026-10-31-step52-REVERT.txt` and `2026-10-31-r1-REVERT.txt`, with their kept tree `trees/8530f8418710f32a.zip`
  - **Do not stage:** `trees/5c19e31dddbb9026.zip` and `archive/5c19e31dddbb9026-818d3706/` (an intermediate tree's killed run).
- **Scratch:** scripts in `s53/fix/build/`; per-run summaries, actions, logs and last world lines in `s53/fix/live/`; starts with sha256 in `s53/fix/starts/manifest.json`.

## The verifier's section

## Verifier report: KI-128 + KI-129 Part A (worktree wf_94ccdf92-1e1-1, uncommitted against 818d3706)

**Verdict: the build does what it claims, offline and live.** I found two MINOR problems and two NITs, and nothing MAJOR:
- **V1:** RULE B does not refuse a new key added under `warps[]` or `connections[]` in maps.json.
- **V2:** Part A is shown to be needed only by the offline tests; no live run measured it.
- **V3, V4:** two NITs (the rate_step5 BLOCKED arm, and a B1 corner case).

I did not modify the worktree:
- `git status --short` gives 73 lines both before and after my work.
- The provenance digest of `ai_player/` is still `sha256:8530f8418710f32a`, the same digest as both revert evidence files (`vscripts/wt_digest.py`).

All my scripts are in `s53/fix/vscripts/`. Outputs are in `s53/fix/verify/out/` and `s53/fix/verify/live/`.

### 1. The diff against the spec and the rulings
**R35 (no bot code in the AI's play).**
- `knowledge/atlas.py` reads only `ai_player/knowledge/world/maps.json`. That file is generated from the pinned decomp by `gates/extract_world.py`, not by the bot.
- No bot import was added.

**R40 / R45 (static map knowledge only).**
- `open_map` reads only `maps[].id` and `maps[].map_type`.
- `open_way` is `OUTDOOR.match or open_map(...) is True`. It reads no flags and no live state.

**D1 (general, no scripted route).**
- No map name appears in brain logic; names occur only in comments.

**The four gap-1 sites, and the errand sites.**
- `lead_toward` uses `open_way` at the goal site, the "look on from here" return and the eligible-leads check; `keeps_going` uses it too.
- The errand sites keep `OUTDOOR`.

**Part A.**
- `in_map_walls` is shared by `_next_step` and by `cut_off(target_tile=None)`.

**Blast radius, measured independently** (`vscripts/kc3_consts.py`):
- 19 maps become open (EVER_GRANDE_CITY, PETALBURG_WOODS, the 6 SAFARI_ZONE maps, and so on), and 0 regex-open maps are closed.
- K-C3, derived by me from the six r1base runs' last world lines: 20 distinct consts, and `open_way != OUTDOOR` on none of them.

**Fairness gate classification** (`vscripts/maps_keys.py`):
- maps.json has 1101 key paths, all of them classified.
- The developer-only keys become `decomp, flag, label, line, measured, note, object, ref, script, shared_events_map, shared_scripts_map, state, taught_by, x, y`, so x and y stay refused.
- The builder's choice to leave world files' AI names out of "elsewhere" is stricter than the spec's literal wording, and it keeps x and y refused. I agree with it.

### 2. Offline tests
Environment: my copy at `verify/new`, with PYTHONUTF8=1, AI_PLAYER_TEST_SUPPORT_ROOT set to the main checkout and POKEBOT_DECOMP set to the pinned clone. Commands are run through `vscripts/run_tests.py`.

| Command | Result |
|---|---|
| `-m unittest ai_player.gates.test_goals` | `Ran 272 tests in 2.384s OK` |
| `-m unittest ai_player.gates.test_kb2` | `Ran 121 tests in 198.181s OK` |
| `ai_player/gates/test_host.py` | `Ran 37 tests in 45.498s OK` |
| `check_fairness.py` | `PERSON-FAIR DATA DOOR: PASS (0 breaches)` |
| `extract_world.py --check` | `CHECK OK: 4 files identical to a fresh extraction` |
| `tools/make_chapter_pack.py --all --check` | `CHECK: PASS` |

**`run_units.py`: OVERALL FAIL in my copy, and only because of the environment.**
- Every suite exits 0 except `test_evidence`, which has 1 failure and 1 error: `git rev-parse ... returned non-zero exit status 128`, because the copy has no .git.
- The passing suites include test_safety_gates, call_census PASS, check_fairness PASS, LESSONS PASS, test_kb2 and test_saving.
- FROZEN TREE digest `0c010be9f0d4698c`, the same as the builder's.

**FAULT arms**, built from my own `git archive` of 818d3706 (`vscripts/make_arm.py`):
- **f_brain** (HEAD goals.py and navigator.py): K-F1 `'ROUTE104' is not None`, K-F2 `False is not true`, K-F6 `None != 'ROUTE104'`, K-F7 `['travel to RUSTBORO_CITY'] != [...WOODS..., ...]`, K-F8 `('wander', None) != ('back', (11, 38))`, P-F1 `Lists differ: [] != [(32, 42), ... (33, 47)]`, P-F2 `'ROUTE104' != 'PETALBURG_WOODS'`. These are the builder's quoted lines.
  - K-C1, K-C5, K-F4, K-F9 and P-C1 pass.
  - K-C2, K-C3 and K-C4 error on the base, as expected: they import `open_way`, which does not exist there.
- **f_nav** (only Part A reverted): only P-F1 and P-F2 fail.
- **f_cf** (HEAD check_fairness):
  - `ImportError: cannot import name 'knowledge_files'`
  - K-F3 `"'script'" not found in ...`
  - name test `{} != {'knowledge/atlas.py': {...}}`

**Mutants**
- `revert_step5.py` with `G0,G22,G23,G272,G273,G306,G407..G418` and `--workers 4`: all 17 named mutants are CAUGHT.
- G0 initially failed one test (`BossLevelTests`) because my copy lacked `ai-agent/knowledge.py`. After I copied that file in, a re-run gives `[G0] ... failing none -> PASS`.

**My own gate mutants** (`vscripts/gate_mutants.py`):

| Mutant | check_fairness result |
|---|---|
| Control | PASS |
| M1 atlas reads `entry.get("flag")` (the spec's mutant) | FAIL (1 breach) |
| M2 atlas reads `trainers[].script` | FAIL |
| M3 `brain/explore.py` names maps.json | FAIL |
| M5 unclassified key under `trainers[]` | FAIL |
| M6 brain subscripts `["shared_scripts_map"]` | FAIL |
| **M4 unclassified key under `warps[]`** | **PASS (finding V1)** |

**Other drivers**
- `revert_safety_gates.py`: `23 mutants CAUGHT as predicted, of 23`. Its S0 control failed `LessonsTests.test_the_real_lessons_list_passes` in my temporary copy, which lacks the repo's documents. test_safety_gates passes inside run_units.
- `tools/workflows/regression_due.py`, run in the worktree (read only): `6 of 6 suites due (2 of them only unproven)`, as the builder reported.

### 3. Live replication (DEVELOPMENT, never graded)
**Setup**
- **Stage:** `s53/fix/verify-stage/`, built by my `vscripts/vbuild_stage.py` from my own `git archive` of 818d3706.
- **Arm digests:** none 16a130f4d2230a4c, PA af9a118ca144fc34, W dcb9339891c7506a, PAW 3c9cf424c771ecd8. They equal the builder's and were unchanged before and after every batch.
- **Starts:** re-derived by tail-read from the A0 and r1base folders (`vscripts/check_starts.py`). All last world lines and end_state.ss1 files equal the builder's saved copies.
- **Disk:** 61.9 GB free before the first batch, 74.1 GB at the end. At most 3 runs ran in parallel.
- **world.jsonl:** each run's file was summarised, its last line kept, and then deleted. `verify/live` holds 30 MB and 0 world.jsonl files.
- **Two instruments per run:** the action log's MAP lines, and the world memory's own new transitions.
- **Predictions:** written before each batch, and their sha256 are the ledger bounds.

**Factorial `vprobe.py run vfact` (ledger #73, seeds 5941/5942/5943, 10,000 frames, all purity CLEAN):**

| Arm | S1 | S2 | S3 |
|---|---|---|---|
| none | no woods; D2 61, then left for ROUTE102 at f485871 | no woods; D2 188 | no woods; D2 191 (world: 192) |
| PA | woods at f485011 (back (11,39)) | identical to none: 1532 = 1532 records | 'first to ROUTE103', then OLDALE\|ROUTE103 159 times (world: 160) |
| W | woods at f483237; first decision 'back (11, 39) ... PETALBURG_WOODS' | woods at f557587; 'first to PETALBURG_WOODS' told 3 times; D2 1 | woods at f619235 |
| PAW | woods at f483253 ('route (10,39)') | identical to W: 719 = 719 records | woods at f619251 |

- All registered predictions held except "the two instruments agree on every run".
- That one failed by 1 crossing on none S3 and PA S3. `vscripts/offbyone.py` shows the extra crossing is at f628180, the run's very last frame. The world memory recorded it but no log line was written, so it is an edge effect of the instrument, not a behaviour difference.

**Long runs `vlong` (ledger #74, seed 5944, start S1, which the builder skipped):**
- **PAW, 300,000-frame cap:** purity CLEAN.
  - The AI stopped by itself at 81,003 frames on map [0, 3], RUSTBORO_CITY.
  - E1 held: `MAP PETALBURG_WOODS -> ROUTE104 at (10, 30): the warp at (14, 5)` at f555840.
  - E2 held: 0 'first to ROUTE104' tells on the woods.
  - E3 held: at most 1 crossing of the same edge in one intent, over 22 intents.
- **W, 60,000-frame cap:** entered the woods at f490065, did the woods scene, and then explored the woods' grass until the cap. It never reached y < 31.
  - My weak E1 prediction for W failed.
  - That miss carries no information: PAW needed 73,722 frames to reach y < 31, more than W's cap (finding V2).

**Control `vcontrol` (ledger #75, CH2T, seed 5951):**
- none and PAW are identical: decide records 101 = 101, all records 3037 = 3037.
- Same 94,264 frames, same final map [8, 1], both stopped by themselves, both purity CLEAN.

**Clean-up**
- The main sandbox has `count: 0` paths newer than my 14:04:17 marker. The scan's fault arm on the stage's profiles found 289 new paths, so the scan does detect writes.
- The stage was deleted by `vscripts/vdelete_stage.py`: 8 junctions unlinked first.
- The main sandbox's linked-folder file counts are unchanged: modules 4391, plugins 40, mgba 43, roms 2.

### 4. Evidence files: headlines against bodies
- **factorial:** headline 'DEVELOPMENT, NOT GRADED, NO PASS'. The body reports each failed prediction honestly (none S2 D2, PA S3, W S1 and S3, and D1 as defined) and says plainly that Part A was not measured as load-bearing. The headline is consistent.
- **long:** headline 'NO PASS'. E1, E2 and E3 are HELD on 2 of 2 runs, and the body notes S1 was not run and that 2 runs are "a sample of 2, not a rate". Consistent.
- **control:** "HELD WITH A MEASURED EXCEPTION". The only differences are dict key order in printed 'say' lines and wall-clock costs in milliseconds; the decide records are identical. Consistent.
- **step52-REVERT and r1-REVERT:** each `code:` line gives digest 8530f8418710f32a. That equals the worktree's current digest (ledger.json, evidence/ and *.md are excluded by provenance.EXCLUDED). The OVERALL PASS lines match the claims: 412 + 2 of 414, and 555 + 1 of 556.

### What I did not do
- I did not run run_regression --full, rate_step5 or live_step5. I did not run Part B or the graded held-out (both out of scope).
- My ledger entries are in the verify copy's ledger.json (see ledger_entries). The worktree's ledger was not touched.
