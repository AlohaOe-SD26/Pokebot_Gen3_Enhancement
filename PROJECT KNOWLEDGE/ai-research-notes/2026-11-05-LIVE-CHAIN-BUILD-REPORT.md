# `live_chain.py`, the GRADED New Game chain held-out driver: build report (2026-11-05 to 06, MERGED 2026-11-06, nothing graded yet)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). It collects the `live-chain-driver` workflow's own
> outputs: the spec (`2026-11-05-LIVE-CHAIN-BUILD-SPEC.md`), an adversarial critic, the builder (worktree
> `wf_213590e7-d34-3`, saved as branch `wip/live-chain`, commit `b4c3e949`) and an independent verifier (CONDITIONAL
> PASS). Sections 4-17 add the fix rounds, checks 2-7, the full lane and the merge (`07` 2026-11-06 records it). No graded seed (6201-6206) was registered or run.
> The rehearsals' evidence is `ai_player/evidence/2026-11-05-chain-heldout-dev-ch2_wally-{6041,6044,6047}.txt` on that
> branch; the verifier's own live check (seeds 6058-6060) was registered only in its copy of the ledger.

## 1. The builder's report

I built `live_chain.py` and its tests in the worktree, and all three development rehearsals came out as predicted except one clause of the R1 prediction (below). Nothing is committed, nothing is registered, and no graded seed (6201-6206) was touched.

**Worktree:** `C:\Remote Projects\Pokebot_Gen3_Enhancement\.claude\worktrees\wf_213590e7-d34-3` (base `cbbb3ec5`; final tree digest `472a3acc15365178`)

### Files
- **New:** `ai_player/gates/live_chain.py` (1,828 lines), `ai_player/gates/test_live_chain.py` (1,951 lines).
- **Modified:**
  - `check_grader_imports.py`: `GRADERS` now includes `ai_player.gates.live_chain`. The command-line check prints PASS for all three graders.
  - `run_units.py`: the `test_live_chain` suite is registered.
  - `test_safety_gates.py`: WiringTests now lists the calls `live_chain.run_batch` and `run_chain` must make (critic CH-01).
  - `ledger.json`: three development entries, #86-#88.
- **Untracked evidence:** `ai_player/evidence/2026-11-05-chain-heldout-dev-ch2_wally-{6041,6044,6047}.txt` and `ai_player/evidence/trees/{c9803bf8d3b54e81,472a3acc15365178}.zip`.

### Tests and mutants
- **The suite:** 223 tests, all OK, in about 30-39 s. That misses the spec's 10 s target, and the suite is not in the `--quick` lane (neither is `test_live_ki128`).
  - The tests cover legs, proofs, the continuation rule, custody, single chains, the grader, disk handling, refusals, the ledger, the scheduler, whole batches and wiring.
  - Whole batches run through `run_batch` with stub launches, a temporary ledger and a temporary evidence folder. They cover:
    - a graded PASS;
    - the spec's dry run: one chain stopped at L2, one salvaged, two waves with at most 3 at once;
    - an unregistered run refused, and a refusal before the ledger that leaves the registration unspent;
    - a development batch;
    - the free-space abort, the world-size kill, the watchdog, and a tree move seen both at chain start and during a check.
- **In-suite mutants:** 95 entries in `MutantTests`, each breaking one guard; every named case fails on its mutant. A control copy, loaded the same way but unmutated, passes every named case.
- **Independent proof through the real runner:** `s53/livechain/mutants_external.py` copies `ai_player/`, mutates `live_chain.py`, and runs the 16 non-mutant test classes (129 tests) with `py -m unittest`.
  - Result: the unmutated copy fails 0 of 129, and **91 of 91 mutants are killed**. The list of killing tests per mutant is in `mutants_external.json`.
  - This ran on tree `c9803bf8`. Two text-only edits to printed lines came after it, and neither touches a mutant's anchor.
- **Which tests kill which mutant (examples):**
  - M01 (reach floor minus 1): `reach_4_of_6_fails`
  - M02 (stop when a proof already held at the start): `overshoot_reaches`
  - M05 (no stop on C1): `chain_stops_on_miss`, which counts exactly 2 launches
  - M10 (world file not deleted): `chain_control`
  - M11 (next leg handed the original world file): `chain_control`
  - M20 (`PARALLEL = 4`): `scheduler_max_3`, `e2e_graded_pass`
  - M26 (guard reads the largest file in any folder): `guard_newest_only`
  - M28 (whole-file read): `no_whole_read`
  - M39 (the spec's original C3, deletion required): `deletion_failure_*`
  - M40 (no abort on low disk): `free_guard_aborts`
  - M58-M64 and M85 (a guard call deleted): `wiring`, plus whole-batch tests
- **Other lanes:**
  - The full unit lane passes 29 of 29 suites on the final tree, with the frozen tree unchanged. My first lane run failed only `test_kb2`, because `POKEBOT_DECOMP` was not set.
  - `run_regression.py --quick` passes 21 suites in 22.7 s. Its "is a live driver running?" check refused the first attempt, because it matched my own shell command, which named `live_chain.py`.
  - `check_purity`, `check_fairness` (0 breaches), `call_census` (0 missing), `check_paths` and `ledger.py --check` (88 entries) all pass.

### Rehearsals (from the evidence files; each prediction's sha256 was in the ledger before the run)

| Run | Ledger, seeds, tree | Verdict by the registered rules | Detail |
|---|---|---|---|
| R0 | #86, 6041-6043, `c9803bf8` | **PASS**, as predicted | 3 of 3 reach `ch2_wally`. 6 of 6 legs pass purity, THIS_RUN, custody and memory. L1 used 137,119 / 129,170 / 157,641 real frames, L2 76,614 / 90,491 / 136,693. Largest world file 6,026,048 bytes, all deleted. Starter 3 of 3, at most 3 at once, no leftover processes, 0 unexpected-multichoice lines, every AI exit claim agrees with the game. |
| R1 | #87, 6044-6046, `472a3acc`, `--leg-frames L1=30000` | **FAIL**: `LC.REACH` 0 of 3 | Each L1 ran exactly 30,000 frames and the AI exited by itself (exit 0). Purity and THIS_RUN pass 3 of 3. World files of 560,126 / 549,779 / 305,242 bytes, all deleted. L2 was not run in 3 of 3, each reason naming L1 and C1, and each profile holds only one run folder. |
| R0b | #88, 6047-6049, final tree `472a3acc` | **PASS**, as predicted | L1 used 134,695 / 151,391 / 138,747 real frames, L2 80,997 / 145,991 / 137,510. Largest world file 7,473,716 bytes. Every check passes. |

**R1's prediction was wrong on one clause.** I predicted only `LC.REACH` would fail, but `LC.STARTER` was also VACUOUS (0 of 0 chains, floor 2): after 30,000 frames no chain had a party yet. The grader behaved correctly; the prediction was wrong.

I re-ran R0 on new seeds (R0b) because of the two text-only edits after R0. I also checked `grade` and `read --truth` on these outputs.

On the final tree, the graded numbers for `ch5` hash to `c742bfd82395cc18…` (bounds text `7c8b0696…`). That value will change after the merge, so the lead has to re-read it at registration.

### Critic findings
- **CH-01, applied:** wiring tests (in my suite and in `test_safety_gates`), call-deleting mutants, and whole-batch tests that check the ledger begins and finishes.
- **CH-02, partly applied; the rest needs the lead:**
  - The churn itself is AI code and is not on this base, so I did not fix it.
  - I added a one-word switch, `WORLD_SIZE_KIND = GRADED`. It is hashed into the registration, and setting it to REPORTED also stops an oversized world file from ending a chain.
  - `LC.WORLD` reports bytes and snapshot lines for every leg.
  - On the data, the 774 MB run started *on* Route 116. None of the 6 chapter-5 chain-end legs passed 300 MB (largest 91.5 MB). The critic's point about the wide uncertainty still stands.
  - The ruling (D2), and putting the chance of a churn FAIL into the graded prediction, are yours.
- **CH-03, applied:** a chain continues if its world file was measured (and under the cap while the cap is graded) and its last line parsed and was kept. A failed deletion is recorded, retried by the end sweep, and never stops a chain.
- **CH-04, applied:** the real-ledger test ignores this driver's own entries, as `live_ki128` does.
- **CH-05, applied:** the mutated copy is loaded from a temp `ai_player/gates/` path with `REPO`, `GATES` and `EVIDENCE_DIR` rebound, and no default argument captures `REPO`. `L5.PROFILE` is restored after every chain and every test.
- **CH-06, applied:** `LC.CUSTODY` now also requires every registered chain's L1 to have run.
- **CH-07, applied:** low free space aborts the batch: every running launcher is killed, `ABORT.txt` is written, the verdict is `ABORTED (harness: disk)` in the ledger, and the exit code is 3. A world-size kill still stops only its own chain (C4).
- **CH-08, applied:**
  - The graded git check now requires the whole tracked tree clean (`--untracked-files=no`).
  - The grader files now include the framework's party and memory decoders, the plugin, `b1_debt.json` and `grader_waivers.json`.
  - A graded run is refused in any build root other than the one the truth harness reads.
- **CH-09, applied:**
  - The decomp confirms the Route 104 and Briney sites. The bounds text now prints where the game sets the L5 proof.
  - I read the game's truth on all six chapter-5 chain-end saves (#91 probe-C1..3, #94 vprobe-C1..3). `ENABLE_RIVAL_MATCH_CALL` = 1 and the VAR = 8 in 6 of 6. `DEFEATED_RIVAL_RUSTBORO` is 1,1,1,1,1,0.
  - So "6 of 6 by the game" now holds for the flag as well. I did not edit F12 in the scratch spec.
- **CH-10, applied:** `LC.PROFILES` is now REPORTED and checks real folder listings. `LC.MAIN_PROFILE` also records the state file's time and hash.
- **CH-11, applied:** `LC.MEMORY` is GRADED, declared as B1 debt. It checks that the AI's memory line names the right file and that its five counts match the kept line. Before building it, I confirmed the rule on 9 of 9 real chain-probe legs; it then held on 12 rehearsal legs.
- **CH-12, applied:** the check that a proof was not already true now applies to the whole chain. A leg whose target already held at its start is marked ALREADY HELD and the chain goes on.
- **CH-13 and CH-14, applied:** salvage only takes the folder named for the leg that was running, and the guard survives a file deleted mid-check.
- **CH-15, applied:** a development seed range already in any ledger entry is refused.
- **CH-16, applied:** the bounds text calls REACH_MIN a pre-registered prior and states that it assumes independent chains.
- **CH-17, applied:** the import check is a syntax scan of `*.py` files, with a test that a mention in a comment or document does not trigger it.
- **CH-18, applied as text:** the bounds text and the docstring state that the goal manager resets and the harness picks each leg's target. They also name the rejected one-process alternative. A `06` decision entry is left to you.
- **N1, not done:** `SPEC` cites `PROJECT KNOWLEDGE/ai-research-notes/2026-11-05-LIVE-CHAIN-BUILD-SPEC.md`, which does not exist. The scratch spec needs copying there before registration.
- **N2-N7, applied:** a chain reaches only if every leg, the last included, passed C1-C6. A 3-chain range is first..first+2. The memory cost is now measured (12.97 / 14.61 MB action logs). The whole-read test also blocks `open().read()`. Multichoice is counted as lines, by kind and form. A later leg's unread start is UNREAD.

**Spec deviations to know about:**
- The kill marker is `<leg>.KILLED.json` and records the cause.
- I added a reported check, `LC.CONCURRENCY`.
- `--chains` defaults to 3 for development runs.
- The B1 DEBT line now names `LC.MEMORY` instead of saying "none".

### Not done
- No commit, no registration, no graded run.
- R2 (New Game to `ch5_rival_meet`) needs the chapter-5 code, which is not on this base.
- No independent adversarial verifier was run on this build.
- Documentation (`04`/`06`/`07`) is not updated.
- **Merge conflict to resolve:** my ledger entries #86-#88 reuse ids that the ch5-stops worktree also used (#86-#95), so the ledger needs merging by hand.

The staging pieces are removed: the mgba junction, the copied configs, cache, logs, the fixture profile and the nine rehearsal profiles. The main sandbox's mgba file count is unchanged (44 before and after). The kept copies of every leg (36 MB) are in `…/scratchpad/s53/livechain/out/{R0,R1,R0b}`, alongside the predictions, logs, the mutant runner and `stage.py`.

## 2. The independent verifier's report

**Verdict: CONDITIONAL PASS.** I found no way for the in-run grade to read PASS without the game's proof. The disk rule, stopped-chain rows and profile isolation all held up, live and in code. Before registering, fix V-01 (it spends the graded seeds) and close the test gaps in V-04 and V-05. Do V-03 too if the registration is to cover what decides LC.STARTER and the truth reads.

I worked only on a copy at `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/chainheld/verify/repo`. The worktree's `git status` and file times are the same as when I started.

### What I re-ran
- **Suite:** `py -3.12 -B -m unittest ai_player.gates.test_live_chain` gives 223 OK in 30 s. The 91 built-in mutants are all killed and the unmutated control passes every named case.
- **Hash:** `live_chain.py bounds --run ch5` gives `c742bfd82395cc18…` (bounds text `7c8b06969f6bd689…`), the same as the builder's.
- **Grader import check:** `check_grader_imports.py` passes.
- **Neighbouring suites:** `test_live_ki128` plus `test_safety_gates` has 9 failures in my copy. All are in `LessonsTests` and fail only because the copy has no PROJECT KNOWLEDGE folder. `WiringTests` passes.
- **My own 44 mutants** (`verify/my_mutants.py`, results in `my_mutants.json`), each run against all 121 cases: 24 killed, 20 survived. Ten survivors are equivalent or covered by another guard (V02, V04, V05, V27, V33, V37, V38, V40, V42, and V10 except at one edge). The other ten are in V-04 and V-05.
- **One live development batch:**
  - Command: `run --purpose development --first-seed 6058 --to ch1_pokedex --chains 3`, in a build root staged inside the copy. The prediction's sha was in the copy's ledger entry #89 before any leg ran.
  - Results: LC-C-6059 reached ch1_pokedex in 146,656 real frames and LC-T-6060 in 138,483. Their world files (6,633,184 and 5,272,414 bytes) were measured, streamed, kept (the kept line's sha matches the row) and deleted. Starter 2 of 2; at most 3 at once; no leftover processes. `read --truth` on the C-6059 leg confirms ch1_pokedex holds.
  - Prediction: **my prediction (3 of 3, PASS) was wrong.** My copy has no `.git` above it, so the sandbox's own auto-updater ran in chain S-6058's first launch and crashed on its "Download now?" prompt. The driver graded this correctly: THIS_RUN FAIL, purity VACUOUS, verdict FAIL.
  - Seeds: 6058-6060 are now played (two real trajectories) but recorded only in my copy's ledger. Treat them as used.

### Answers to (a)–(g)
- **(a) PASS without the game's proof:**
  - The in-run grade cannot do it. A leg counts only when L5.THIS_RUN passes and every proof mark is present and satisfied on the leg's end state. A chain counts only when every leg ran and continued, the last included. Legs that were NOT RUN, REFUSED or SALVAGED never count.
  - The proofs match the pinned decomp (731ad5b): RustboroCity/scripts.inc:740-741 and :808-809, Route104 :50, :99 and :184, Route104_MrBrineysHouse :78.
  - The offline `grade DIR` can read PASS (V-02).
- **(b) Vacuous or satisfied by construction:** no graded bound is vacuous. LC.CUSTODY's checks on later legs hold by construction in normal flow (V-09).
- **(c) Registration hash:** every constant in `live_chain.py`, the AI code, untracked AI files and the listed grader files are covered. Several files the grade depends on are not (V-03).
- **(d) Tests fail when a guard is removed:** mostly, but ten of my mutants survive (V-04, V-05).
- **(e) Disk rule deletes only what it measured:** yes. The size is taken before deletion, the larger size is kept, and only `world.jsonl` files are deleted (only in the chain's profiles, plus the end sweep, which measures first). Confirmed live.
- **(f) Stopped chain:** later legs are written as NOT RUN with the reason, are left out of every sample, and the chain fails. Shown by the tests, the builder's R1 evidence and my V1 run.
- **(g) Touching anything outside its profiles:** I compared file listings before and after the live batch (`verify/touch_snapshot.py`). The main sandbox, its fixture and `ai-step5-play` profiles, the main ledger, the worktree ledger and the main evidence folder are unchanged.
  - Outside its three profiles, the batch wrote only the expected records (the copy's ledger and evidence file, and the `out-V1` folder).
  - The framework also created three empty files in the build root's `logs/` folder. These files already exist in the main sandbox.
  - The crash log and `.last-update-check` were caused by my missing `.git`, not by the driver.
  - The truth harness boots `ai-step0-fixture` read-only.
  - A later leg's `--state` start moves the earlier leg's game memory into the profile's `retired/` folder and empties the cartridge save (`launcher.py:195-252`). So only the savestate and the world line carry over between legs, as the bounds text says.

### Findings

**V-01 — MAJOR — `run_batch` does not refuse a `--out` folder holding an earlier batch's files.** A leftover `STOP.txt` or `ABORT.txt` lets the ledger begin, which spends the held-out seeds, and then no leg is launched.
- Evidence: `py -3.12 -B verify/probes.py <copy>`, case P3: a graded rig with a stale `out/STOP.txt` gives `exit 1; refused: False; ledger entry status done; verdict FAIL; LC-S-6201 L1 NOT RUN`.
- Cause: `run_batch` only calls `out.mkdir(..., exist_ok=True)`, and `run_chain`'s pre-leg check (lines 1016-1022) reads `out/STOP.txt` and `out/ABORT.txt`. A stale ABORT.txt gives "ABORTED" with the seeds also spent.
- Fix: in `run_refusal`, before `ledger.begin`, refuse unless `--out` is missing or empty. Add a test that plants a `STOP.txt` and checks the refusal and that the registration is not spent. This changes the hash, so do it before registering.

**V-02 — MINOR — `grade DIR` re-grades every `rows/*.json` file, not only the registered chains, so it can read PASS on a failing batch.**
- Evidence: P3's sibling, case P2. A graded rig with 2 of 6 chains missing reads `in-run: exit 1, FAIL, REACH FAIL` and `grade DIR before: FAIL over 6 chains`. After one copied passing row (`LC-S-6041.json`) is added: `PASS over 7 chains`, with LC.REACH "5 of 6 … reached ['LC-C-6204', 'LC-S-6041', …]".
- Cause: `grade_batch` builds `reached` from every chain row, not from the registered jobs. `chain_reaches` also trusts the stored `continue` flag.
- Fix: in `grade_dir`, keep only the chains in `results["jobs"]` and print any extra row. In `grade_batch`, count `reached` only for registered jobs. Optionally re-derive `leg_reached` and `continue_after` from the row's facts.

**V-03 — MINOR — some files the grade depends on are not hashed, though the registered bounds text says "a graded run on any other … grader is refused".**
- Evidence: P1 registers, edits one file, then calls `begin`. It is NOT refused for:
  - `modules/pokemon.py`, the real species and original-trainer decoder behind LC.STARTER. `pokemon_party.py` only lists the party slots.
  - `modules/game.py`, which loads the symbol table every truth read uses, and the table itself, `modules/data/symbols/pokeemerald.sym`. (I located the table in the code; I did not edit it in P1.)
  - `gates/disk_budget.py`, `gates/check_grader_imports.py` and `gates/window.py`.
  - A change of line endings only (CRLF), which is by design.

  It is refused for: `STAGGER_SECONDS`, `Deps.poll_seconds`, `pokemon_party.py`, and a new untracked AI file.
- `verify/closure.py` (an import scan) also lists `probe_save_kill.py`, `probe_end_screen.py` and `revert_step5.py` in the grading import path and not hashed.
- The frozen-tree watch covers only `ai_player/` and the plugin.
- Fix: add these files to `GRADER_FILES`, or build the list from the import scan and test that every gates module it finds is hashed. Correct the sentence in the bounds text either way.

**V-04 — MINOR — the suite does not pin that LC.PURITY, LC.THIS_RUN and LC.STARTER count in the verdict.** Changing any of them to REPORTED passes all 121 cases.
- Evidence: `verify/kind_demo.py`:
  - One chain's L5 impure (5 of 6 reach): the real driver gives FAIL; mutant V24 gives **PASS**.
  - One L5 leg stale: real FAIL; V22 **PASS**.
  - A wrong starter: real FAIL; V25 **PASS**.
- Fix: three grade tests asserting the batch verdict is FAIL for each case. Also a test that every check the bounds text lists as GRADED comes out of `grade_batch` as GRADED.

**V-05 — MINOR — other guards that no test protects** (mutants survive every case):
- V31: the watchdog cut to `sum(wall)+300` gives 18,300 s instead of 25,800 s, which would kill healthy chains.
- V08: the "if the file grew, the larger size is graded" rule.
- V34: the kept last line written inside the profile, although the bounds text says outside the repo.
- V35: the critic's CH-15 overlap refusal reduced to an exact first-seed match.
- V28: `left_procs = []`, so leftover processes are never read. No full-batch test plants one.
- V19: `git_state` is never called by a test. My check on a scratch repo with an origin shows it works: clean gives `dirty: []`, a changed tracked file gives `['M t.txt']`, and untracked files are ignored.
- V10: the ABORT check before each leg (the only guard if free space recovers).
- V01: the LC.STARTER floor.

Fix: one test per item.

**V-06 — NIT — the registered prediction sha256 is of the text after `.strip()`, not of the file's bytes.** So `sha256sum prediction.txt` never matches the ledger or the evidence. Measured: R0 file `996de6b4…` vs registered `d5aac0f4…`; R1 `58914734…` vs `e40b69e7…`; R0b `ebd500b9…` vs `19ab8759…`; V1 `da06dc1b…` vs `1955a349…`. Fix: hash the bytes, or label it "sha256 of the stripped text".

**V-07 — NIT — the builder's report says "95 entries in MutantTests".** The class has 94 methods: 91 mutants plus 3 meta tests.

**V-08 — NIT, for a ruling — a launch that dies before playing a frame fails the graded batch.** It makes LC.PURITY VACUOUS, LC.THIS_RUN FAIL, LC.WORLD_SIZE VACUOUS and LC.MEMORY VACUOUS even when LC.REACH passes. The 1-in-6 reach tolerance therefore does not cover a crashed launch, whereas low disk gives ABORTED. V1 showed this: REACH PASS 2 of 3, verdict FAIL. It matches the bounds text ("every leg that ran"), so it needs a ruling rather than a fix. Separately, LC.WORLD prints "deleted False / not deleted after its leg" for a leg that never had a world file (cosmetic).

**V-09 — NIT — LC.CUSTODY's checks on later legs hold by construction.** They compare the truth of one file read twice, the sha of the same kept file, and the env keys of `sent`. `sent` is a dict `run_chain` rebuilds itself, not the environment `run_arm` actually passes (which also inherits every non-`AI_PLAYER_` variable). These checks catch harness regressions only, never anything the AI does. Fix: say so in the bounds text.

Items the builder already flagged and I confirm: the build spec path in `SPEC` (N1) does not exist; the ledger ids #86-#88 collide with the ch5-stops worktree; and `WORLD_SIZE_KIND` (D2) needs the lead's ruling.

Everything is in `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/chainheld/verify/`:
- **Scripts:** `probes.py`, `my_mutants.py`, `kind_demo.py`, `closure.py`, `git_state_probe.py`, `touch_snapshot.py`
- **Results:** `my_mutants.json`, `my_mutants.log`, `touch_before.json`, `touch_after.json`
- **Live batch:** `prediction_V1.txt`, `V1.log`, `out-V1/`; its evidence file is at `repo/ai_player/evidence/2026-11-05-chain-heldout-dev-ch1_pokedex-6058.txt`

## 3. The critic's findings (on the spec, before the build; the builder applied or rebutted each, section 1)

**Adversarial review of the `live_chain.py` build spec: 3 MAJOR, 15 MINOR, 7 NIT**

I checked every claim the spec makes about the code against `live_ki128.py`, `live_step5.py`, `ledger.py`, `play_harness.py`, `memory.py`/`mode.py`, `milestones.json`, `provenance.py` and `test_safety_gates.py`, and against the pinned decomp (731ad5b). Facts F1–F15 hold as written, with two exceptions: F12 is incomplete (CH-09), and the "6 of 6 by the game" claim for chapter 5 rests partly on the AI's own lines (CH-09).

---

**CH-01 (MAJOR): nothing tests that the orchestrator actually calls its guards.**
- **Spec:** every guard "has a FAULT and a CONTROL test" (§7, §9). R1–R10 are tested through the pure `run_refusal`, FROZEN and LEFTOVER "on planted tuples", and the scheduler through `schedule()` with fake spawn and poll. M15–M18 mutate refusals inside `run_refusal`, and M20 mutates the `PARALLEL` constant.
- **Code:** `test_safety_gates.py` WiringTests exists for exactly this gap: "the census's own lesson: a guard whose call is deleted passes every test of the guard". Its `WANT` lists `rate_step5.py`, `live_step5.py`, `revert_*` and `run_units.py`. It does not list `live_ki128` and will not list `live_chain`.
- **How it goes wrong:** a mutant of `run_batch` survives every planned test if it does any of these:
  - drops the `ledger.begin` or `ledger.finish` call;
  - drops `tree.check` / `seal`, or the STOP.txt writer;
  - drops the `run_refusal` call or the free-space check;
  - calls `schedule(..., parallel=6)`.
  The worst one is a graded batch that runs unregistered.
- **Fix:**
  - Add `("live_chain.py", "run_batch"): {"watch", "check", "seal", "begin", "finish", "run_refusal", "schedule", "free_gb"}` to WiringTests.
  - Add `("live_chain.py", "run_chain"): {"check_purity", "check_after_is_this_run", "measure_then_delete", "stream_world_tail", "continue_after"}`.
  - Add MutantTests entries that delete each of those calls.

**CH-02 (MAJOR): the known, unfixed Route 116 churn makes LC.WORLD_SIZE a likely FAIL, and the spec's numbers never price it.**
- **Spec:** "The unfixed churn trajectory (774 MB in 200k frames) fails it, as it should." The REACH_MIN power analysis allows one miss. LC.WORLD_SIZE allows none ("every leg that RAN").
- **Data:** `2026-11-05-CH5-STOPS-BUILD-REPORT.md`:
  - line 69: "Seed 6016 … wrote a 774 MB world.jsonl";
  - line 272: Route 116 breaks "C2 85, C3 63 … It is churn".
  - On the new code, about 9 distinct trajectories went through Route 116: the 3 C2 grunt seeds plus the 6 chain-end L5 runs. One of them passed 300 MB. The largest healthy leg (91.5 MB) is already 3× the others.
- **What it means:** at 1 in 9 per leg, P(at least one of 6 graded L5 legs ≥ 300 MB) ≈ 1 − (8/9)^6 ≈ 0.5. The 95% interval on 1/9 is about 0.003–0.48, so the data cannot support the bound either way.
  - A churn leg is a REACH miss and a batch FAIL at the same time, so "one miss allowed" never applies to the most likely miss.
  - Graded seeds 6201–6206 would be spent on a coin flip over an out-of-scope bug.
- **Fix:** fix the Route 116 after-battle break churn before registering. Failing that, register the estimated P(FAIL from churn) in the prediction and get the lead's explicit ruling (D2) before seeds are spent. Also have R2 report every L5 world size and snapshot count.

**CH-03 (MAJOR): C3's "and was deleted" turns a Windows file-deletion failure into an AI FAIL.**
- **Spec C3:** "measured, was under 300,000,000 bytes and was deleted". But §6.3(c) says deletion is "5 tries, 2 s apart; a failure is recorded, never a crash".
- **Code (`live_ki128.measure_then_delete`):** "(the held-out's verifier, F3) a file another process still holds open cannot be deleted on Windows: the size is already recorded, so the batch goes on to its verdict and the leftover file is reported". In `live_ki128`, K8.WORLD_SIZE reads only `world_file.bytes`.
- **How it goes wrong:** an antivirus or indexer handle on a freshly written 10–90 MB file stops the chain. That is a REACH miss caused by the OS, not by the AI — a FAIL that should PASS.
- **Fix:**
  - Remove "deleted" from C3; report it in LC.WORLD and let the end sweep retry.
  - Disk stays safe: each leg is under 300 MB and the in-run guard still covers the large case.
  - Add a FAULT test: deletion fails, and the chain continues with a recorded note.

---

**CH-04 (MINOR): a planned test goes red the moment the lead registers.**
- **Spec §9.8:** "No entry of the real ledger names 6201-6206".
- **Precedent (`test_live_ki128.py:607-610`):** it excludes the driver's own entries: `[e["id"] for e in named if e["driver"] != K.DRIVER] == []`.
- **Fix:** use the precedent's form.

**CH-05 (MINOR): MutantTests that load one temp file get the wrong `REPO`.**
- **Spec §10:** "The mutated source is written to a temp file and loaded with `importlib.util.spec_from_file_location`… `REPO` is on `sys.path`, so its imports resolve."
- **Code:** each module computes `REPO = Path(__file__).resolve().parents[2]`. In a single temp file that is the temp folder's grandparent.
- **How it goes wrong:**
  - R1 ("--out inside the repository"), R8, `ai_code_sha256(REPO)`, `registered_numbers`, `GATES` and `EVIDENCE_DIR` are all wrong in every mutant. The control M0 would error, or its cases would silently test the temp folder.
  - Writing the copy inside `ai_player/` instead would move FrozenTree for any batch running at the same time.
- **Fix:** follow `revert_safety_gates.make_copy` (copy the `ai_player` tree into a temp root), or rebind `M.REPO`, `M.GATES` and `M.EVIDENCE_DIR` right after loading. Restore `L5.PROFILE` in tearDown; it is a process global shared across mutants.

**CH-06 (MINOR): a chain that never ran is only a REACH miss, so a driver defect can hide inside a PASS.**
- **Spec:** a REFUSED child gives "row status REFUSED, no leg run". LC.CUSTODY, PROFILES, PURITY and THIS_RUN all sample "legs that RAN". REACH allows 5 of 6.
- **How it goes wrong:** a profile-guard refusal or a pre-launch death in one chain still allows a PASS on 5 of 6, with no graded check failing.
- **Fix:** add a GRADED rule that every registered chain's L1 RAN, with floor 6 of 6 (for example inside LC.CUSTODY), plus a FAULT test for a planted REFUSED row.

**CH-07 (MINOR): a free-space guard kill becomes an AI FAIL.**
- **Spec:** "or free space is under GUARD_FREE_GB (30) … kills the descendants … (C4) stops the chain". The `live_ki128` loop applies `now_free < GUARD_FREE_GB` to every running job.
- **Measured:** C: has 81 GB free and is 96% full. The 24/7 learner (12 lanes) writes to the same drive.
- **How it goes wrong:** a neighbour's disk use kills healthy legs. The result is a FAIL with the seeds spent.
- **Fix:** record the kill cause. A world-size kill stays a C4 stop. A free-space kill aborts the batch as `ABORTED (harness: disk)` in `ledger.finish`, with no PASS/FAIL. Test both causes.

**CH-08 (MINOR): the registered code identity leaves out the framework, and truth reads ignore `--build-root`.**
- **Spec:** CODE covers `ai_code_sha256` (ai_player only) plus `GRADER_FILES`. R9 checks only `git status --porcelain -- ai_player`.
- **Code:**
  - `play_harness` reads the party through `modules.pokemon_party` and `modules.memory`. Those are sandbox-pokebot framework files that decide LC.STARTER and run the emulator the AI plays on.
  - FrozenTree's `HOOK_SCOPE` covers `ai_player` plus one plugin file; `ai_code_sha256` covers neither the plugin nor the framework.
  - `probe_eyes.boot` calls `resolve_build_root()` with no argument. So truth reads always use the default sandbox, even when `--build-root` points elsewhere.
- **Precedent:** `rate_step5.HASHED_FILES` already hashes `sandbox-pokebot/modules/map_data.py`.
- **Fix:**
  - R9 should require the whole tracked tree clean (`git status --porcelain --untracked-files=no`).
  - Add the decoder files (`modules/pokemon_party.py`, `modules/memory.py`) and the plugin to `GRADER_FILES`.
  - Refuse a graded `--build-root` that is not `resolve_build_root()`.

**CH-09 (MINOR): F12 is incomplete, and the dev "by the game" claim partly reads the AI's own lines.**
- **Spec F12:** the setflag/setvar "appear together at `data/maps/RustboroCity/scripts.inc:740-741` and `:808-809`".
- **Decomp (731ad5b):**
  - `Route104/scripts.inc:50` sets VAR_RUSTBORO_CITY_STATE 8 (the Route 104 rival trigger).
  - `:99` and `:184` set FLAG_ENABLE_RIVAL_MATCH_CALL (the Route 104 May/Brendan encounter).
  - `Route104_MrBrineysHouse/scripts.inc:78` (sailing to Dewford) sets VAR 8 with no flag.
- **What it means:**
  - The proof means "met the rival in Rustboro or on Route 104". The bounds text should say so.
  - "In all 6 runs the game showed VAR_RUSTBORO_CITY_STATE 8" does not imply the flag, because the Briney sail sets VAR 8 alone. For the 3 VPROBE runs the flag came from "each verifier run's told milestone line", which is the AI's claim.
- **Fix:** before citing "6 of 6 by the game", read ENABLE_RIVAL_MATCH_CALL on VPROBE's `end_state.ss1` files with the harness truth. Correct F12.

**CH-10 (MINOR): LC.PROFILES holds by construction and is oversold.**
- **Spec:** "the only proofs that the batch played what was registered … no write outside the six profiles".
- **Code:** `run.run_dir = profile_dir / "ai_player_runs" / ...`, where `profile_dir = launcher.ensure_profile(build_root, PROFILE)`. That is the same `L5.PROFILE` the child guard already checks. It cannot see a write anywhere else, and LC.MAIN_PROFILE lists only run folders.
- **Fix:** demote it to REPORTED, or measure something real: every profile's run-folder listing plus the `ai-step5-play` `current_state.ss1` mtime and md5, before and after.

**CH-11 (MINOR): nothing graded proves the AI loaded the carried memory.**
- **Spec:** the bounds text says each later leg starts "from … the world memory it left", but LC.MEMORY is REPORTED. Custody check 3 only shows the env var pointed at the right file.
- **Code (`mode.py:1319-1320`):** `read_world(options.world_in)`. The only evidence of the load is the AI's `[AI-WORLD] memory from …` line.
- **How it goes wrong:** an options bug that drops `AI_PLAYER_WORLD` gives amnesiac legs, a PASS, and a registered text that misdescribes the test.
- **Fix:** grade LC.MEMORY with a declared `AI_INPUT_DEBT` entry (as `live_ki128` does), or say in the bounds text that the load is unverified.

**CH-12 (MINOR): an overshoot by one leg fails the chain.**
- **Spec C1:** "the proofs did NOT all hold on the state it started from".
- **How it goes wrong:** if leg k-1's AI misses its own "done" and plays on into leg k's target, leg k fails C1 and the chain stops, even though the game reached the target in this chain.
- **Fix:** either apply the non-vacuity test at chain level (the proof did not hold at the New Game start) and mark the leg "ALREADY REACHED", or register "an overshoot stops the chain" in the bounds text. Test whichever is chosen.

**CH-13 (MINOR): salvage can attach the wrong run folder to a leg.**
- **Code (`live_ki128.salvage`):** `run_dir = folders[-1]`.
- **How it goes wrong:** if the child dies between legs (after writing `current_leg.json`, before the launcher makes its folder), the newest folder is leg k-1's, already measured. A naive port writes a SALVAGED row for leg k that points at leg k-1's folder.
- **Fix:** match the folder-name suffix to `current_leg.json`'s arm name. If none matches, write "NOT RUN (process ended before launch)" and keep the chain VACUOUS-failing.

**CH-14 (MINOR): the orchestrator can crash on a stat race.**
- **Code (`live_ki128` run loop):** `big = max((w.stat().st_size for w in worlds if w.exists()), default=0)`. This is an exists/stat race while the child deletes the file. The chain design deletes about 30 files per batch.
- **How it goes wrong:** an orchestrator crash leaves the ledger entry "started" with no verdict and the graded seeds spent.
- **Fix:** catch `OSError` around every stat in the poll, and add a test with a file deleted between listing and stat.

**CH-15 (MINOR): the ledger does not stop rehearsals reusing seeds.**
- **Code (`ledger.begin`, development):** `reserved = [e for e in family_entries if e["status"] == "registered" and _overlap(e, first, last)]`. Already-played development ranges are not refused.
- **How it goes wrong:** a rehearsal reusing 6041 replays R0's L1–L2 trajectories (CLAUDE.md rule 8) and would read as more samples.
- **Fix:** in `live_chain`, refuse a development range that `seeds_named()` finds in any entry. FAULT and CONTROL tests.

**CH-16 (MINOR): "the numbers support it" overclaims for REACH_MIN 5 of 6.**
- **Spec:** "This was the lead's prior, and the numbers support it."
- **Reality:**
  - The binomial table is the bar's power, not support.
  - There are 0 unbroken new-code New Game → ch5 chains. Legs 1–4 ran on `ef3a5712`.
  - Chains come in pairs (2 seeds per personality and starter), so they are not independent.
- **Fix:** call it a pre-registered prior. Say the iid assumption, and that R2's result must be read before registration without moving the bar.

**CH-17 (MINOR): the ImportTests text grep will fire on doc mentions.**
- **Spec §9.10:** "No file of the AI's package (`ai_player/` outside `gates/` and `evidence/`) contains the text `live_chain`".
- **How it goes wrong:** `*.md` files under `ai_player/` (README, notes) are not excluded. A doc mention fails the gate, which breaks CLAUDE.md rule 6.
- **Fix:** an AST import scan over `*.py` only, plus a CONTROL test where a mention in a comment or docstring does not fire.

**CH-18 (MINOR): the chain does not test the AI connecting chapters by itself.**
- **Spec F9 and §3:** every leg is a new process with a reset goal manager and a harness-chosen `AI_PLAYER_TARGET`.
- **USER RULING 55 (`06`, line 9962):** a New Game test "to check that what was learned connects".
- **How it goes wrong:** the chapter boundary — where in-run state would carry over — is exactly where the harness steps in. A PASS says nothing about the AI moving from ch k's end to ch k+1 by itself.
- **Fix:** record this as a decision with the rejected alternative: one process with `--to ch5_rival_meet`, about 2.76M frames, wall about 3 h. Or add it as a REPORTED single-process arm. At minimum, the bounds text should state the reset.

---

**NIT findings**
- **N1:** BOUNDS_TEXT cites "build spec s53/chainheld/SPEC.md", a scratch path that disappears with the session. Copy the spec to `PROJECT KNOWLEDGE/ai-research-notes/` before registering and cite that.
- **N2:** "A chain reaches iff every leg continued and the LAST leg REACHED" leaves open whether C2–C6 apply to the last leg. Define it explicitly (C1 only, or C1–C6).
- **N3:** with `--chains 3`, the ledger range must be first..first+2. `live_ki128`'s `(first, first + 5)` would spend 3 extra seeds.
- **N4:** the "known limit" RAM risk can be measured instead of guessed. The 2 GB-world churn runs at `sandbox-pokebot/profiles/ai-ch3-probe-{1,2}` have `actions.jsonl` of 12.97 MB and 14.61 MB and `ai_player.log` under 1 MB. Cite these.
- **N5:** the whole-file-read FAULT test only patches `read_text`/`read_bytes`, so `open().read()` escapes it. Patch `open` to return a handle whose argument-less `read()` raises.
- **N6:** LC.MULTICHOICE counts log lines, not events. One stop may be logged several times, and the flee form "an unexpected … in the battle" is counted too.
- **N7:** the "None counts as not held" rule should apply to L1 only. For leg k > 1, a failed start-truth read should be "UNREAD". THIS_RUN and custody happen to catch it today.

## 4. The fix round (the builder, 2026-11-05)

I fixed every finding in the worktree `wf_213590e7-d34-3` (HEAD `3dd088d6`).
- Only `ai_player/gates/live_chain.py` and `ai_player/gates/test_live_chain.py` changed.
- Nothing was committed, staged, registered or played live, and no graded seed was touched.
- I applied the lead's decisions as given: the dead-launch rule stays and is now named (V-08), and `WORLD_SIZE_KIND` stays GRADED at 300 MB (D2).

**The real counts (V-07).**
- `MutantTests` has **143 methods: 140 mutants and 3 meta tests** (the M00 control, "every named case exists", "ids are unique").
- Before this round it had 94 (91 mutants and 3 meta tests), not the 95 the build report said.
- The suite is **308 tests** (was 223): 165 outside `MutantTests` (36 new) and 143 inside it (49 new mutants).

### Per finding

**V-01 (MAJOR): fixed.** A batch now refuses a used `--out` before `ledger.begin`.
- **Change:**
  - `gather_facts` lists `--out` (new `out_listing`).
  - `run_refusal` adds refusal **R11**. It refuses an `--out` that exists and is not empty (any entry, a folder included), is not a folder, or cannot be listed. This applies to graded and development batches, so the registration stays unspent.
- **FAULT tests:**
  - `OutTests.test_r11_out_not_empty`: STOP.txt, ABORT.txt, an unrelated file and a folder, for graded and development batches, plus an `--out` that is a file.
  - `OutTests.test_e2e_out_not_empty_refused`: three graded batches, each with one of those files planted. Each gives exit 2 and R11; the entry stays `registered` with no `started`, the ledger bytes are unchanged, and no chain starts. A development batch with an old `rows/` file also gives exit 2 and no entry.
  - `OutTests.test_out_listing`.
- **CONTROL tests:** `OutTests.test_e2e_out_empty_proceeds` (an empty `--out` gives PASS) and `OrchestratorTests.test_e2e_graded_pass` (a missing `--out`).
- **Mutants:** M95-M98.
- **`verify/probes.py` P3 on the final tree:** `exit 2; refused: True; ledger entry status registered; verdict -; LC-S-6201 L1 RAN`. It was `exit 1; refused: False; ledger entry status done; verdict FAIL; LC-S-6201 L1 NOT RUN`. The last field is now the planted row file, not a run.

**V-02: fixed.** Only the registered chains count, and every leg is re-derived from its own row.
- **Change: which rows count.** `grade_batch(..., legs=)` grades only the registered jobs, one row each (`registered_chains`). These rows never count, and each is named in LC.REACH's text:
  - a row of an unregistered chain;
  - a second row of a registered chain;
  - a row whose chain, pair, personality, starter, seed or profile is not the registered job's.
- **Change: what is re-derived.** For each leg that ran, `rederived_chain` recomputes from the row's own facts:
  - its proof, from `truth_after.marks` against the REGISTERED leg's proof (never the row's own);
  - its reach (L5.THIS_RUN and that proof);
  - its custody (`custody_problems` against the registered job, joined to any problem the row stored);
  - its kept last line, re-read from the file (present, a JSON object, sha256 equal to the row's).

  A leg continues only if its stored flag AND the re-derived rule both say so. Every disagreement is listed in LC.REACH's text.
- **Change: `grade DIR`.** It now runs through `regrade_dir`:
  - it reads each registered chain only from `rows/<chain>.json`, and only if that file's own `chain` field names it;
  - it prints every other file as `IGNORED`;
  - it joins disk-guard marker files found on disk to their legs;
  - it prints what it re-derived and what it read as stored.
- `run_batch` passes the registered legs too, so the in-run grade follows the same rule. The rule is in the bounds text, under LC.REACH.
- **Values that could not be re-derived.** These are read as stored. A stored value can stop a chain, never continue one.

  | Value | Why it is not re-derived |
  |---|---|
  | L5.THIS_RUN status | Its inputs (the end state's write time against the launch start, and the frame bounds) are not in the row. |
  | Purity check statuses | Their inputs are the launch's verdict file, counters and gate line. A copy of `purity.json` sits beside the row, but re-running `check_purity` offline was not built. |
  | The world file's measured size | The file is deleted by design, so the measurement is its only record. |
  | C6 (STOP.txt seen at a leg's end) | No row records when STOP.txt appeared. |
  | Each leg's status | It is the harness's own record of what it launched. |
  | The disk guard's mark | The row's copy is used, and `grade DIR` also reads the marker files on disk. |
- **FAULT tests:**
  - `RegradeTests.test_grade_dir_foreign_row`: P2's case, plus a passing row copied over a failing registered chain's file. Both stay FAIL, and both files print as IGNORED.
  - `test_grade_batch_foreign_row`: a foreign row, and a second row of one chain.
  - `test_flipped_continue_not_counted`: `continue`, `reached` and `proof_after.held` flipped to true over two L5 misses. The result is still 4 of 6, FAIL.
  - `test_row_identity_mismatch`, `test_row_proof_weakened`, `test_row_leg_names_checked`, `test_kept_file_swapped`, `test_grade_dir_marker_on_disk`.
  - `GradeTests.test_custody_grade_fail`: a stored custody problem still counts.
- **CONTROL tests:** `test_regrade_honest` (`grade DIR` on an honest PASS batch gives PASS, nothing ignored, and every check's status equal to the in-run grade), `GradeTests.test_grade_control`, `OrchestratorTests.test_e2e_graded_pass`.
- **Mutants:** M99-M110.
- **P2 on the final tree:** with the extra row, `FAIL over the 6 rows of the 6 registered chains (1 row file(s) IGNORED)`, LC.REACH 4 of 6. Before the fix it read `PASS over 7 chains`.

**V-03: fixed.** `GRADER_FILES` is now built from an import-closure scan.
- **Change: the scan.** `grader_closure` follows every import statement of `live_chain.py`, at module level or inside a function (except blocks included), with relative imports resolved and parent packages' `__init__.py` included. It follows them through `ai_player/gates` and `sandbox-pokebot/modules`. The AI's own modules are not followed; they are hashed whole, as `ai_code_sha256`.
- **What it finds: 185 files.**
  - 19 gates files. `disk_budget.py`, `check_grader_imports.py`, `window.py`, `probe_save_kill.py`, `probe_end_screen.py` and `revert_step5.py` are all really imported and are now all hashed.
  - 166 sandbox modules, including `pokemon.py`, `game.py`, `pokemon_party.py` and `memory.py`.
- **Hashed on top of the closure:**
  - The AI's plugin.
  - 11 data files:
    - the two Emerald symbol tables `game.py` loads;
    - the six tables the party decoder opens when it is imported (species, types, moves, natures, abilities, items), found with an audit hook on `open`;
    - `item_flags.json`, `b1_debt.json` and `grader_waivers.json`.
- **In total:** 197 files, 10.7 MB, about 40 ms to hash.
- **The bounds text** now names exactly what is hashed and what is not (the ROM, the emulator's library, every other file). It also says that a change of line endings alone is accepted BY DESIGN.
- **Why the full closure.** A static scan cannot tell which function-local imports run when the truth is read, so a narrower list could leave part of a decoder unhashed. The cost is that any framework or story-bot commit between registration and the graded run means registering again. That is one command on the same unplayed range, which `ledger.register` allows. The rejected alternative was following module-level imports only.
- **FAULT tests:**
  - `ClosureTests.test_grader_files_cover_closure`: drop one file from the list and it fails.
  - `test_grader_data_hashed`.
  - `test_changed_decoder_refused`: editing `pokemon.py`, the `.sym` or `disk_budget.py` after registration is refused.
  - `test_closure_scan_planted`: the scan finds a function-local import, one in an except block, a relative import and a parent package. It does not count a docstring mention, a comment, or the AI's own imports.
  - `test_closure_not_vacuous`: it finds the 15 files the verifier named.
- **CONTROL tests:** `test_crlf_only_accepted` (by design) and `LedgerTests.test_register_begin`.
- **Mutants:** M111-M116 and M139.
- **P1 on the final tree:** refused for every edit, including `pokemon.py`, `game.py`, `disk_budget.py`, `check_grader_imports.py` and `window.py`, which were not refused before. Not refused for a CRLF-only change, by design.
- **`verify/closure.py`:** all 138 files it finds are HASHED.

**V-04: fixed.**
- **FAULT tests:**
  - `KindTests.test_verdict_impure_l5_fails`: REACH PASS (5 of 6), PURITY FAIL, verdict FAIL.
  - `test_verdict_stale_l5_fails`.
  - `test_verdict_wrong_starter_fails`.
  - `test_graded_kinds_match_bounds`: the GRADED ids parsed from the bounds text equal `grade_batch`'s GRADED kinds, in both directions.
- **CONTROL test:** `GradeTests.test_grade_control`.
- **Mutants:** M117-M124, each flipping one GRADED check to REPORTED.
- **`kind_demo.py` on the final tree:** the real driver gives FAIL in all three cases:
  - impure: `original ('FAIL', {'LC.REACH': 'PASS', 'LC.PURITY': 'FAIL', ...})`
  - stale: `('FAIL', {... 'LC.THIS_RUN': 'FAIL' ...})`
  - wrong starter: `('FAIL', {... 'LC.STARTER': 'FAIL'})`

  The demo's own mutants still read PASS; that is what the demo exists to show. The suite now kills those exact mutations: M117-M119, and the verifier's own V22, V24 and V25 when re-run.

**V-05: fixed.** Each item now has a FAULT test, a CONTROL and a mutant. All tests are in `GuardTests`.

| Item | Test | What it checks | Mutant |
|---|---|---|---|
| V31 | `test_watchdog_value` | Pins 25,800 s for ch5, and the formula (walls of 100 s and 50 s give 3,450 s). | M125, V31's own mutation (18,300 s) |
| V08 | `test_world_grew_larger_graded` | The file grows 4,096 bytes before its deletion: the larger size is graded and noted, and it stops a chain whose cap lies between the two. CONTROL: an unchanged file is graded at its size. | M126 |
| V34 | `test_kept_outside_repo` | Every kept line is at `out/<chain>/<leg>/world_last.jsonl`, never in the profiles or the run folder, and R1 refuses an `--out` inside the repository. | M127 |
| V35 | `test_dev_partial_overlap_refused` | Four partial overlaps of 6041-6043 are found and an e2e batch on 6042-6044 is refused (R3). CONTROL: two adjacent ranges are not. | M128 |
| V28 | `test_e2e_leftover_reported` | A planted leftover is read once, after every chain ended, and it fails LC.LEFTOVER. | M129 |
| V19 | `test_git_state_scratch` | A scratch repository with a bare origin: clean, a changed tracked file, an untracked file, an unpushed commit. | M130 |
| V10 | `test_abort_before_leg` | ABORT.txt before L1, and ABORT.txt written during L2, which means L3 is never launched. | M131 |
| V01 | `test_starter_floor` | 4 chains judged gives VACUOUS and FAIL. CONTROL: 5 judged gives PASS. | M132 |

**The verifier's own 44 mutants, re-run on the final tree** against all 157 cases (from a copy, so its recorded results are untouched):
- The control's non-PASS cases: `{}`.
- 35 killed, 9 survived. Before this round it was 24 killed and 20 survived.
- All 11 it reported as unprotected are now killed: V01, V08, V10, V19, V22, V24, V25, V28, V31, V34, V35.
- The 9 survivors (V02, V04, V05, V27, V33, V37, V38, V40, V42) are all among the ten it classed as equivalent or covered by another guard.

**V-06: fixed.** The prediction's hash is now of the file's bytes.
- **Change:**
  - The registered `prediction_sha256` is the sha256 of the prediction FILE's bytes, so `sha256sum` matches it.
  - The evidence prints "sha256 of the file's bytes".
  - A prediction file that is not UTF-8 is refused with R3 instead of crashing the driver.
  - Earlier ledger entries are left as they are.
- **Tests:** `PredictionTests.test_prediction_sha_file_bytes` (the ledger's bounds sha256 equals the numbers recomputed with the file's sha256) and `OrchestratorTests.test_e2e_development`, updated.
- **Mutant:** M133.

**V-07:** see the counts at the top of this section.

**V-08: fixed, following the ruling (the rule stays; the dead launch is now named).**
- **Change: the rule.** `launch_died` names a leg that RAN when the run's own exit facts show all four: no exit by the AI, no frame counted, no line of the AI's log, and no world file. That is what the verifier's live V1 left.
- **Why all four.** A launch killed mid-play by the disk guard or the wall clock also leaves no verdict file, so `real_frames` alone would misname it. Its log and world file show it played, so it is not named. I caught and fixed this in my own first version before the final runs.
- **Change: where it is named.** The text "harness: the launch died before playing a frame (...)" appears:
  - in the row's `harness` field and its `why`, in the chain's `stop_reason` and in the later NOT RUN reasons;
  - in the evidence's first line, in a line of its own, and in the leg's block;
  - in the ledger's verdict line;
  - in LC.PURITY's and LC.THIS_RUN's failing lists.
- The bounds text and the docstring state the rule.
- **Change: no world file.** LC.WORLD and the leg's world line say "no world file" for a leg that never had one, instead of "deleted False / not deleted after its leg".
- **FAULT tests:** `DeadLaunchTests.test_launch_died_rule`, `test_dead_launch_named`, `test_e2e_dead_launch_evidence` (REACH PASS 5 of 6, PURITY and THIS_RUN FAIL, exit 1, named everywhere), `test_world_line_no_file`.
- **CONTROL tests (in the same cases):** a launch that played frames and then crashed, one killed mid-play, a log with lines, the AI's own exit and a never-launched leg are not named. A world file the OS kept open is still listed as not deleted.
- **Mutants:** M134-M137 and M140-M143.

**V-09: fixed.**
- **Change:** the bounds text's LC.CUSTODY line and both docstrings say plainly that these checks read only the harness's own records, and that on a later leg they catch a harness regression, never anything the AI does.
- **Test:** `LedgerTests.test_bounds_needles` (the bounds-text and docstring needles).
- **Mutant:** M138.

**D2:** unchanged. **N1:** the `SPEC` path now exists and is tracked (it came in with the merge of main).

### Checks on the final tree
- **`test_live_chain`:** 308 tests OK (76 s quiet, 115 s under load).
- **The external runner** (its class list updated): `CONTROL M00: ran 165, failed none`, `MUTANTS: 140 of 140 killed by the real runner; survived: none`.
- **The gates:**
  - `check_purity`, `check_fairness`, `call_census`, `check_paths` and `check_grader_imports` all PASS.
  - `ledger.py --check`: PASS, 99 entries.
  - `extract_milestones.py --verify`: OVERALL PASS.
- **`bounds --run ch5`:** REGISTERED NUMBERS sha256 `2304cd25d93733f8fd4d7c6523167486dd3a65e6a0f4bca8a89bf4a5b2b692a1`, BOUNDS TEXT sha256 `f01ba1ccf943cb85f07c6dff3470a31391b9038e2324c0cec45b2384032ffd38` (was `c742bfd8...` / `7c8b0696...`).
- **`run_units.py`:** 25 of 29 suites pass and the frozen tree PASSES, but OVERALL reads FAIL.
- **`run_regression.py --quick`:** 18 of 21 pass, the frozen tree PASSES, and it reads FAIL.
- **Why those two lanes fail.** The failing suites are `test_host`, `test_eyes`, `test_hands` and `test_saving`. Every failure is `No module named 'mgba'` or "Path is not a valid profile directory". This worktree no longer has the builder's staged `mgba` junction or fixture profile, and I did not restage them because that links into the main checkout. These failures are independent of my change:
  - none of the four suites' import closures reaches either changed file;
  - a clean `git archive` export of HEAD fails the same suites.

  **Re-run both lanes with the staging in place before registering.**

### Notes
- **Suite run time** went from about 30 s to about 76 s. Two things keep it there:
  - The closure scan walks statements only.
  - The ledger tests share one fake repository and restore any file they change. The first read of a freshly copied file costs about 0.9 s on this machine, so one copy per case had tripled the time.
- **Two of my tests first failed only in the external runner's deeply nested copy.** Both are fixed:
  - `git_state_scratch` hit Windows' path limit, so its scratch repositories now go in a short temp folder and are removed afterwards.
  - `kept_outside_repo` had asserted something about the environment instead of what the driver controls.
- **Side effects I undid.**
  - My one-off data audit imported the sandbox config, which wrote nine git-ignored default profile files into the worktree's `sandbox-pokebot/profiles`. The unit lane's `test_host` wrote them again later.
  - I removed exactly those nine both times (untracked, and written during this session). No test imports a sandbox module.
- **Left in the system temp.** The permission classifier denied removing my runs' leftover temp folders, so 50 `livechain_test_*`, 47 `vm_*`, 3 `kind_*` and 4 `lc_git_*` folders remain. The four `lc_git_*` are from two runs I stopped mid-test, and some of the others predate my session.
- **Where things are:** my scripts and logs are in `s53/chainheld/fix/`, and the unit lane's evidence is `fix/final/units-evidence.txt`.

## 5. The independent check of the fix round (the checker, 2026-11-05)

**Verdict: CONDITIONAL PASS.** I found no MAJOR, and V-01 to V-05 are closed, each with command output below.
- The fix leaves two MINOR gaps, and both must be fixed or ruled on before the GRADED registration:
  - **C2-01:** a mis-filed row is still graded by every check except LC.REACH, although the registered bounds text says such a row never counts.
  - **C2-02:** the import scan cannot see `check_purity.py`, the program that decides L5.PURITY_GATE, or the files every leg runs by path.
- Fixing either one changes the numbers sha256.
- Neither blocks the development rehearsal.

**Where I worked.**
- I worked on a copy of the worktree, `check2/repo`, with no `.git` and inside no repository. `check2/` = `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/chainheld/check2/`.
- The worktree's `live_chain.py`, `test_live_chain.py` and `ledger.json` have the same sha256, mtime and size at the end as at the start. `git status` still lists only the two modified files.
- In the copy, `live_chain.py bounds --run ch5` reproduces the fix round's hashes: BOUNDS TEXT `f01ba1cc…` and REGISTERED NUMBERS `2304cd25…`.

### The verifier's tools, re-run on the copy
- **`verify/probes.py`:**
  - P1 refuses all nine edits. Only the CRLF-only change is accepted, by design.
  - P2: `FAIL over the 6 rows of the 6 registered chains (1 row file(s) IGNORED)`, LC.REACH 4 of 6.
  - P3: `exit 2; refused: True; ledger entry status registered; verdict -`. Its last field is the planted row file, not a run.
- **`verify/kind_demo.py`:** the real driver gives FAIL in all three cases. The demo's own mutants still read PASS, which is what the demo exists to show.
- **`verify/closure.py`:** 138 HASHED, none unhashed.
- **The verifier's 44 mutants:** I ran a copy of `verify/my_mutants.py` as `check2/verifier_mutants.py`, against all 157 cases.
  - The control's non-PASS set is `{}`; 35 are killed and 9 survive.
  - All 11 the verifier called unprotected are now killed: V01, V08, V10, V19, V22, V24, V25, V28, V31, V34, V35.
  - The 9 survivors and why each survives:
    - V04 and V33: another guard gives the same outcome.
    - V37 and V38: the floor gives the same outcome.
    - V40: an unread end truth fails THIS_RUN anyway.
    - V42: each arm has one run folder.
    - V05: equivalent for real truths, since every truth read sets `state_md5`.
    - V02 and V27: narrow gaps that predate this fix: the OT and the TID both unread at once, and a tree move between the last tick and the verdict.

### My own mutants
I wrote 44 mutants of the guards the fix added or changed. Each ran through the real runner on a fresh copy: all 23 non-mutant test classes, 165 tests. The control ran 165 tests with none failing. **32 were killed and 12 survived.**

| Finding | Killed | Survived |
|---|---|---|
| V-01 | C01-C05 | none |
| V-02 | C10, C10b, C11, C14, C15 (killed only by WiringTests), C16, C21 | C12, C13 (equivalent), C15b, C17, C18 (equivalent) |
| V-03 | C33-C37 | C30 |
| V-04 | C40-C42 | none |
| V-05 | C50-C59 | none |
| V-06 | none | C70 |
| V-08 | C60, C63 | C61 (equivalent), C62, C64, C65, C66 |

### Checks on real data (no emulator)
- **`check2/regrade_real.py`** re-grades the four real `--out` folders with the fixed code: the builder's R0, R0b and R1, and the verifier's V1.
  - The verdicts are PASS, PASS, FAIL and FAIL, the same as in-run.
  - No check's status differs, except V1's REPORTED LC.WORLD (FAIL to PASS, from the V-08 wording).
  - Every kept line still hashes to its row's sha256. That includes the six L1 lines handed to L2 as `AI_PLAYER_WORLD`, so the AI does not change its input memory, and the in-run re-read of kept lines does not fail honest chains.
- **`check2/dead_real.py`:** the new rule names V1's real dead launch (LC-S-6058 L1) and none of the 18 real legs that played.

### Findings
- **C2-01 MINOR: an identity-mismatched row is kept.**
  - `registered_chains` (`:984`) keeps it, and its legs feed LC.PURITY, THIS_RUN, CUSTODY, STARTER and MEMORY. The bounds text (`:426`) says it "never counts".
  - `check2/probe_identity.py` starts from a batch whose LC-S-7101 L5 is impure, so the verdict is FAIL. Replacing that row with LC-S-7102's clean row, with only the chain field renamed, turns the verdict to PASS ("30 of 30 judged legs").
  - The fix's own `test_row_identity_mismatch` asserts LC.REACH only. My mutant C12, which drops the identity carry the docstring promises for LC.STARTER, survives.
  - In-run rows cannot be mis-filed by the harness, so this affects `grade DIR` and the registered text, not the in-run verdict.
  - **Fix:** ignore such a row as `registered_chains` already ignores a second row, and assert the batch verdict in the test.
- **C2-02 MINOR: files run by path are not hashed.**
  - `check2/probe_unhashed.py` registers, edits one file, then calls `ledger.begin`. It is not refused for `ai_player/gates/check_purity.py`, `sandbox-pokebot/pokebot.py`, `plugins/custom_modes_loader.py` or `plugins/game_cheats_plugin.py`. The control, `live_step5.py`, is refused.
  - Why `check_purity.py` matters: the launcher runs it by path (`launcher.py:748`), and its exit code is the `[AI-GATE] … verdict=PASS` line that L5.PURITY_GATE requires. As a gates file, `ai_code_sha256` skips it.
  - Every leg's `pokebot.py` `load_plugins()` imports every top-level plugin with `__import__`.
  - The bounds text is truthful ("every other file" is not hashed), and the hashed runtime counters still catch bot calls and foreign writes.
  - **Fix:** also start the scan from the files run by path, and hash the plugins.
- **C2-03 NIT: two of V-02's re-derivations are unpinned.**
  - C15b discards `custody_problems`' result and survives. C17, `grade DIR` without the registered legs, survives.
  - The evidence's per-chain "reached" (`:1982`) uses the stored row.
- **C2-04 NIT: V-08's naming is partly unpinned.**
  - C64 and C65 survive: the LC.PURITY and LC.THIS_RUN lists are not asserted.
  - C66 survives: the test's "ledger verdict names it" is also satisfied by LC.REACH's stop reason. `check2/probe_dead_verdict.py` finds the text 2 times in the real verdict and still 1 time with the mutant.
- **C2-05 NIT: the scan's test gaps.**
  - C30 (skip `else:` blocks) survives, although the walker itself is right: `ast.walk` and `_statements` both find 5,944 imports in 369 files.
  - The closure rule is enforced only by a unit test, never at registration.
- **C2-06 NIT: the non-UTF-8 prediction refusal is unpinned.** It works (`check2/probe_prediction.py`: exit 2, R3, ledger unchanged), but C70 survives.
- **C2-07 NIT: no exception guard after the batch.** `run_batch` has 0 `try:` blocks between the batch's end and `ledger.finish`, and `kept_problem`'s `read_bytes` is unguarded. An exception there leaves the entry `started` with no verdict.

### Test runs in the copy (POKEBOT_DECOMP set)
- **`test_live_chain`:** `Ran 308 tests in 76.173s`, `OK`. That is 165 tests plus 143 in MutantTests (140 mutants and 3 meta tests), so V-07's counts are right.
- **`run_units.py`:** 24 of 29 suites exit 0, including `test_live_chain` (308 OK), `test_kb2` (123 OK) and `test_safety_gates` (50 OK).
  - FROZEN TREE PASS: 29 checks of 205 files, files digest `34c01abc45e1fdbd`, the same as the fix round's.
  - OVERALL FAIL, on five suites:

    | Suite | Result |
    |---|---|
    | test_host | 35 failures |
    | test_eyes | 7 errors |
    | test_hands | 1 failure, 2 errors |
    | test_saving | 7 errors |
    | test_evidence | 1 failure, 1 error |

  - I ran each failing suite on its own. Every failure is one of three causes:
    - `No module named 'mgba'`;
    - "Path is not a valid profile directory";
    - `git rev-parse` failing, because my copy has no `.git`. This accounts for test_evidence's 2 and test_hands' 1, the only differences from the fix round's run.
  - None of the five suites mentions `live_chain`.
- **`run_regression.py --quick`:** 17 of 21 PASS. The 4 FAILs are the same suites. FROZEN TREE PASS. `REGRESSION: FAIL (quick, 21 suites, 20.9 s wall)`.
- **`extract_milestones.py --verify`:** `[VERIFY] OVERALL PASS`.

### Notes
- **R11 and the rehearsal:** R11 refuses any `--out` that exists and is not empty, so the rehearsal's `--out` must be new or empty. Do not put the prediction file in it.
- **Left in `%TEMP%` by this check:**
  - 16 `livechain_test_*` folders. 7 of them are 27 MB each: the verifier's mutant workers and probes import the test module outside unittest, so `tearDownModule` never runs.
  - 1 `kind_*` and 1 `vm_control_*`.
  - I did not delete them.
- **Nothing else changed:** no commit, stage, registration, emulator run or live leg was made.

## 6. The second fix round (the builder, 2026-11-05)

I fixed C2-01 to C2-07 in the worktree `lc-c2` (branch `wip/live-chain-c2`, HEAD `7ddd624e`).
- I also fixed the verifier's V02 and the temp-folder leak. V27 is equivalent; the reason is below.
- Only `ai_player/gates/live_chain.py` and `ai_player/gates/test_live_chain.py` changed.
- Nothing was committed, staged, registered or played live, and no emulator ran.

**The counts.**
- `MutantTests` has 181 methods: 178 mutants and 3 meta tests (was 143). 38 mutants are new (M144-M153, M155-M182; M154 is unused), and M100, M101, M103 and M115 were re-anchored.
- The suite is 364 tests (was 308): 183 outside `MutantTests` (18 new) and 181 inside it.
- It runs in 153 s (was 76 s). The M00 control alone takes 35 s, and each closure-scan mutant takes 2-5 s.

**The new hashes.** BOUNDS TEXT sha256 `2848a7b0…` (was `f01ba1cc…`); REGISTERED NUMBERS sha256 `e600c5d6…` (was `2304cd25…`).

### Per finding

| Finding | Change | FAULT tests | Mutants |
|---|---|---|---|
| C2-01 | A row whose chain, pair, personality, starter, seed or profile is not the job's is IGNORED like a second row and named with its reason, so its chain is ABSENT (LC.CUSTODY's "L1 ran" fails, LC.REACH reads VACUOUS). The bounds text says so. | `test_row_identity_mismatch` (from an impure original: FAIL), `test_row_starter_mismatch` | M103, M144, M145, M181 |
| C2-02 | The closure also starts from the files run by path (`PATH_ROOTS`: check_purity.py, hands_harness.py, play_harness.py, probe_presses.py, sandbox-pokebot/pokebot.py) and from the plugins the framework loads by name (`loaded_plugins`), and follows plugins, pokebot, requirements and updater. 231 files; 242 hashed (was 197). | `test_closure_starts`, `test_closure_starts_planted`, `test_path_runs_are_roots`, `test_path_run_scan_planted`, `test_closure_toplevel_names`, `test_changed_path_run_refused` | M146-M153, M155 |
| C2-03 | Custody, `grade DIR` and the in-run grade are re-derived against the registered legs, and the evidence's per-chain line prints the re-derived reach. | `test_regrade_custody_stored_empty`, `test_grade_dir_registered_proof`, `test_e2e_row_proof_weakened_in_run`, `test_e2e_evidence_rederived_reach`, `test_kept_file_not_json` | M159-M163 |
| C2-04 | Each place that names a dead launch is asserted, including the ledger verdict's own clause. | `test_e2e_dead_launch_evidence`, `test_launch_died_rule`, `test_world_line_no_file` | M164-M168 |
| C2-05 | Imports under else, finally, with, match and a class body are planted. `register` and a graded run are refused (R12) while the closure holds a file that is not hashed; a development batch only prints them. | `test_closure_scan_planted`, `test_closure_enforced_register`, `test_closure_enforced_run` | M156-M158, M169-M173, M182 |
| C2-06 | A prediction file that is not UTF-8 is refused (R3), now pinned. | `test_prediction_not_utf8_refused` | M174 |
| C2-07 | An exception after the chains end FINISHES the ledger entry as `ERROR (harness: <type>: <message> while grading; no PASS or FAIL; the seeds are spent)`, writes the evidence with the traceback and results.json, and exits 4. | `test_grade_error_finishes_entry`, `test_evidence_error_finishes_entry` | M175-M179 |
| V02 | An unread OT and an unread TID together fail LC.STARTER. | `test_starter_unread_ot_and_tid` | M180 |

**The CONTROLs.**
- The honest identity is graded as before.
- The real tree's closure is hashed whole, and its path runs are all roots.
- A mention, a `-c` or a self-run does not count.
- A UTF-8 prediction runs.
- An honest batch is unchanged.

**What the new closure starts revealed.** Before this round the closure already missed modules that import `pokebot` and `plugins.*`.

**The scan's cost.** About 1.4 s for 231 files, paid at registration and at the graded run.

**V27 is equivalent.** `FrozenTree.check` returns False only after recording a move, and LC.FROZEN reads `held and not tree.moves` after `seal()` checks again.

**Hygiene.**
- An `atexit` hook now removes the test module's temp root.
- In an A/B, the previous round's module left one folder and this round's left none.

### Checks on the final tree
- **`test_live_chain`:** 364 tests OK.
- **The external runner:** `CONTROL M00: ran 183, failed none`, `MUTANTS: 178 of 178 killed`.
- **Mutant re-runs:**
  - The checker's twelve mutants, with C12 split into C12a and C12b: 13 of 13 killed.
  - The verifier's 44 mutants: 36 killed and 8 survived. The survivors are V04, V05, V27, V33, V37, V38, V40 and V42, all classed equivalent or covered before.
- **The gates:** check_purity, check_fairness, call_census, check_paths and check_grader_imports PASS. `ledger.py --check` PASS (99 entries); `extract_milestones.py --verify` OVERALL PASS.
- **Real data:** `regrade_real.py` re-grades R0, R0b, R1 and V1 with unchanged verdicts and no row ignored.
- **The probes:** `probe_unhashed.py` refuses all four edits it was not refusing before, and `probe_identity.py` now reads FAIL.

### Notes (open, outside this round)
- An exception WHILE the chains run (schedule, spawn, tick) still leaves the entry "started"; guarding that needs the running children killed.
- The sandbox's `.gitignore` ignores `plugins/*` except nine names. A private plugin would have run unseen in every leg; R12 now refuses it. Before registering, `git status --short --ignored sandbox-pokebot/plugins` should list nothing new.
- The framework's configuration (`sandbox-pokebot/*.yml` and the per-machine `profiles/`, including the `customcatchfilters.py` copy) is not hashed, and the bounds text says so.

## 7. Check 3 (three checkers: grading, errors, hashing, 2026-11-05)

Three independent checkers, one lens each, on the second fix round's tree. Their reports follow as written.

### Check 3 - grading and re-derivation (2026-11-05)

**Verdict: CONDITIONAL PASS.** I found no MAJOR.
- C2-01, C2-03, C2-04 and V02 are closed as stated.
- Two MINOR gaps remain, and both should be fixed or ruled on before the graded registration:
  - **C3-G01:** a row relabelled from another chain still counts. With rows rewritten after the chains end, this turns an in-run FAIL into GRADED, PASS.
  - **C3-G02:** grade DIR trusts results.json for its legs, jobs, reach_min, frozen and leftover.
- Fixing C3-G01 changes the numbers sha256.
- Four NITs follow.

**Where I worked.**
- A copy of `lc-c2` at d1a853bc, without .git, in `check3/grading/repo`.
- The worktree is unchanged at the end: HEAD d1a853bc, `git status` empty, and live_chain.py and test_live_chain.py hash to `365d2cd2…` and `7c91367c…`, as at the start.
- No commit, no real ledger, no emulator.
- The full module on the copy: `Ran 364 tests in 412.195s OK`.

#### The controls (real data, the new code)
`regrade_real.py` (regrade_real.log):

| Out | In-run | Re-grade | Ignored | Status differences |
|---|---|---|---|---|
| R0 | PASS | PASS | none | none |
| R0b | PASS | PASS | none | none |
| R1 | FAIL | FAIL | none | none |
| R2 (3 chains to ch5_rival_meet) | PASS | PASS | none | none |
| V1 | FAIL | FAIL | none | LC.WORLD (REPORTED) FAIL to PASS, the known V-08 wording |

- Every kept line still matches its row's sha256.
- On R2, each chain's re-derived reach is True and nothing was re-derived against its stored flags.
- `dead_real.py`: launch_died names only V1's LC-S-6058 L1, and none of the 32 other RAN legs.

#### The verdict paths
I ran `probes_grading.py` G8 and `probes_grading2.py` P with stub launches and a temp ledger.

| Case | Ledger line starts | Exit |
|---|---|---|
| Honest batch | `GRADED, PASS` | 0 |
| Two misses | `GRADED, FAIL (failing: LC.REACH)` | 1 |
| A leftover process | `GRADED, FAIL (failing: LC.LEFTOVER)` | 1 |
| An impure leg | `GRADED, FAIL (failing: LC.PURITY)` | 1 |
| A tree move seen only at the seal | `GRADED, FAIL (failing: LC.FROZEN)` | 1 |
| The free-space guard | `GRADED, ABORTED (harness` | 3 |
| An error while grading | `GRADED, ERROR (harness: ...` | 4 |
| Development | `DEVELOPMENT, not graded, NO PASS (...)` | 0 |

- No case gave PASS with a GRADED check not PASS.
- `batch_verdict` uses no waivers, and PASS needs every GRADED check PASS.
- One more outcome exists: an exception between `ledger.begin` and the first chain leaves the entry "started" with no verdict (C3-G05).

#### What held (attacks that failed)
- **Each identity field alone** (chain, pair, personality, starter, seed, profile, and seed as text) gives FAIL, with LC.REACH VACUOUS n 5 and the row named (G1).
- **Stored custody [] over a broken hand-off** gives LC.CUSTODY FAIL in all 9 variants (G4).
- **An impure leg with a stored continue True** gives FAIL (P).
- **LC.STARTER's V02 variants** (unread TID, unread OT, both, lead not in the OT list, OT as text, another OT, starter second) each give FAIL. Two chains with no party give VACUOUS (S).
- **A forged kept file with its own sha256** passes only when 6 stored fields are rewritten together (F). That is the documented trust model: stored facts are read as stored.

#### Findings

| Id | Severity | What |
|---|---|---|
| C3-G01 | MINOR | Another chain's row, relabelled on chain, seed and profile, counts. In-run, through the builder's own tamper hook: control `GRADED, FAIL`, attack `GRADED, PASS`, exit 0. The row's own records name the other chain (env seed '7102', `--profile ai-livechain-7102`, a shared run_dir). A leg-level check finds 0 problems on the 33 real RAN legs and 30 on the copy. |
| C3-G02 | MINOR | grade DIR takes legs, jobs, reach_min, frozen and leftover from results.json without checking them. On copies of real batches, R1 with `reach_min 0` and V1 with the dead chain's job removed both re-grade PASS. A null leftover drops LC.LEFTOVER (8 GRADED checks, PASS). G20 survives. |
| C3-G03 | NIT | Profile, personality and pair can each be dropped from IDENTITY with every test green (G01-G03 survive). Each is enforced today. |
| C3-G04 | NIT | grade DIR on a moved --out re-grades an honest PASS as FAIL, because the kept paths are absolute. On the ERROR path's results.json it raises `KeyError: 'legs'`. It exits 0 on FAIL. |
| C3-G05 | NIT | `run_folders` or `main_profile_state` raising after `ledger.begin` escapes, and the entry stays "started". The docstring names only "while the chains run". |
| C3-G06 | NIT | A stored NOT RUN after a leg whose re-derived continue is True hides an impure last leg: GRADED, PASS. This is inside the documented READ AS STORED model (a direct status flip does the same), but "a stored flag can stop a chain but never continue one" reads as more of a safety rule than it is. |

#### Mutants
- I wrote 20 of my own (G01-G50) and ran each through the real runner over all 24 non-mutant classes (183 tests). The M00 control failed none.
- **Killed 8:** G04, G11, G12 (both by WiringTests only), G15, G21, G30, G40 and G42.
- **Survived 12.**
  - Not equivalent: G01, G02 and G03 (C3-G03), and G20 (C3-G02).
  - Equivalent:
    - G05: the harness writes ints.
    - G10: C6 needs a tree move, which fails LC.FROZEN.
    - G13: no RAN leg ever follows a non-RAN leg.
    - G14: a SALVAGED or ERROR leg fails LC.CUSTODY.
    - G31 and G32: every real L1 party is the starter alone (11 of 11).
    - G41: an unlaunched L1 fails LC.CUSTODY.
    - G50: the stored harness field is launch_died's own result.

#### Files (all in `check3/grading/`)
- **Scripts:** regrade_real.py, probes_grading.py, probes_grading2.py, proto_leg_identity.py, probe_moved_out.py, probe_unguarded.py, dead_real.py, my_mutants_g3.py.
- **Logs:** regrade_real.log, probes_1.log, probes_2.log, probes_3.log, proto_leg_identity.log, probe_moved_out.log, probe_unguarded.log, dead_real.log, my_mutants_g3.log and .json, suite_full.log, grade_R1.out.

### Check 3 - error paths, refusal order and the whole run (2026-11-05)

**Verdict: FAIL.** Two MAJOR findings must be fixed before the graded registration. Both fixes change live_chain.py, so they change the numbers sha256.

- **C3-E01:** a typo in --out spends the graded registration.
- **C3-E02:** the AI's own world.jsonl can turn a FAIL into the harness's ERROR.

C2-07 holds for any single exception between the chains' end and the ledger's finish. C2-06 is closed.

**Where I worked.**
- I worked on a copy of lc-c2 at d1a853bc, without .git, in check3/errors/repo. check3/errors/ = C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/chainheld/check3/errors/.
- At the end, the worktree's live_chain.py, test_live_chain.py and ledger.json have the same sha256 as at the start (365d2cd2..., 7c91367c..., 3f52c9fb...). `git status` there is clean.
- The copy's own ledger.json is unchanged ('99 entries; well formed -> PASS').
- No commit, no stage, no registration in a real ledger, no emulator.

**Baseline checks.**
- test_live_chain in the copy: `Ran 364 tests in 297.874s`, `OK`.
- The real --out folders re-graded with the new code (regrade_real.py):

  | Folder | In-run verdict | Re-grade verdict | Notes |
  |---|---|---|---|
  | R0 | PASS | PASS | no status differs |
  | R0b | PASS | PASS | no status differs |
  | R1 | FAIL | FAIL | no status differs |
  | R2 | PASS | PASS | `ignored []`, no status differs |
  | V1 | FAIL | FAIL | LC.WORLD (reported only) FAIL to PASS, as in check 2 |

### The C2-07 guard under injection
- **The probe.** probe_inject.py wraps every function in live_chain's module, plus ledger.finish, keep_earlier, Path.write_text, Path.mkdir, os.replace, the tree's check and seal, and deps.leftover. It raises RuntimeError on exactly the n-th call after the chains end.
- **The full sweep** (pass scenario): 1401 injections over 40 names. 1400 behave as claimed:
  - exit 4;
  - the entry is 'done';
  - the verdict reads 'GRADED, ERROR (harness: RuntimeError: planted ...)', never PASS or FAIL;
  - the evidence is headed 'VERDICT ERROR' and holds the traceback;
  - results.json says ERROR.
- **The sampled sweeps:** development 134 of 135, dry-run 160 of 161, missing row 163 of 164.
- **The one exception everywhere** is check_lines#2. It is the print loop after ledger.finish (:2166). The entry is already done with its true verdict, and the same call already succeeded at :2131, so it cannot fail on its own.
- **The ledger write itself:**
  - A single failure is handled: ledger.finish#1, os.replace#2 and write_text#3 each end 'done' ERROR, exit 4.
  - A persistent failure is not. That is C3-E03.
- **Before the chains.** Every orchestrator step between ledger.begin and the try escapes and leaves the entry 'started'.
  - The docstring acknowledges only "while the chains run".
  - The steps out.mkdir, main_profile_state, run_folders, the job file and chain_watchdog_seconds come before the chains. Only out.mkdir is reachable in practice (C3-E01).

### Fault scenarios (probe_scenarios.py)

| Case | Result |
|---|---|
| S1: ledger.json write fails every time (PermissionError) | escapes; entry **started**; evidence says "the ledger entry is finished" (C3-E03) |
| S2: a stale ledger.json.lock appears mid-batch | escapes (Refused); entry **started**; same false sentence |
| S3: grade_batch raises once | exit 4, done, ERROR, evidence with the traceback; grade DIR on that --out then raises KeyError 'legs' (C3-E05) |
| S4: KeyboardInterrupt while grading | escapes; **started**; no evidence (C3-E06) |
| S5: --out under a file | R11 passes; begin; mkdir FileExistsError; **started**; the same registration is then refused by R10 for good (C3-E01) |
| S6: the first spawn raises | **started** (the acknowledged chains-running gap) |
| S7: str(error) raises | error_verdict raises; **started** (C3-E06) |
| S8: S1 through sys.exit | process exit **1**, the documented FAIL code |

### The AI's world memory (probe_ai_world.py)
- The stub child dies like a real process (any exception means exit 1). Two chains miss at L2, so the batch should FAIL.

| Arm | Change | Result |
|---|---|---|
| A | none (CONTROL) | FAIL, 4 of 6 |
| B | LC-C-6203 L3's last line truncated (CONTROL) | FAIL, 3 of 6: that chain stops by C3, as designed |
| C | that last line is {"maps": 3} | **ERROR (harness: TypeError ...)**, exit 4 |
| D | that last line has "tiles_learned": "many" | **ERROR (ValueError ...)** |
| E | one 100,000-deep middle line | **ERROR (RecursionError ...)** |

- So an AI defect makes the batch "no PASS or FAIL; the seeds are spent", and the verdict blames the harness (C3-E02).

### Refusals and their order (probe_refusals.py)
- **34 real attempts, all as claimed.** Each refused one has exit 2, the right id first, ledger bytes unchanged, no --out created, no chain, no evidence. The cases:
  - graded: R1, R11 (STOP.txt in --out; --out is a file), R8 (out under pokebot-learner; build root outside the repo), R2 (unknown --run; --first-seed given; another build root), R5, R12, R9 (HEAD not origin/main; dirty; git failed), R6 (5 GB; None), R7, R10 (never registered; other numbers);
  - development: R3 (no prediction file; empty; not UTF-8; missing on disk; --run given; seeds named in the ledger), R4, R11, R1.
- **Pairs read the order:** R11 before R12, R12 before R9, R7 before R10. A development batch on registered graded seeds is refused by R3 before R10.
- **CONTROLs:** a graded and a development batch run; a development batch with an unhashed closure file runs, printed only.
- **A closure file that does not parse** fails closed: a SyntaxError before begin, ledger unchanged. But it exits 1 and names "<unknown>" instead of the file (C3-E06).

### The whole run (probe_e2e.py)
**Graded, on a scratch ledger:**
- `register_run("ch5")` runs the real closure scan: '231 files, every one hashed (scan 3.37 s)'. It prints REGISTERED e600c5d6..., the builder's number.
- run_batch exits 0. The ledger reads 'GRADED, PASS: ... 6 of 6 (bound: at least 5 of 6)'.
- The evidence head and the SEED LEDGER line read right.
- The numbers sha256 is the same in the run, the registration and the ledger.
- grade DIR: PASS, with 18 of 18 statuses equal to the in-run grade.
- ledger.check: well formed. The same registration run again is refused (R7).

**Development**, 3 chains to ch5_rival_meet, seeds 9101-9103:
- exit 0; the ledger reads 'DEVELOPMENT, not graded, NO PASS (development: PASS by the registered rules)';
- the evidence is 2026-11-05-chain-heldout-dev-ch5_rival_meet-9101.txt;
- the prediction file's sha256 is in the evidence and in the ledger note;
- grade DIR: PASS.

### Exit codes

| Code | Meaning | Observed |
|---|---|---|
| 0 | graded PASS, or a development batch that ran | yes |
| 1 | graded FAIL | yes, but also every uncaught exception (C3-E06) |
| 2 | refused | yes, every refusal |
| 4 | ERROR | yes, graded and development |

grade DIR always exits 0, even for R1's FAIL (C3-E05).

### Temp hygiene (hyg_probe.py)
- The child ran with a private TEMP. Its livechain_test_* root is gone after exit.
- Every sentinel survives: a file beside the root, another run's root, and a folder linked INTO the root by a junction.
- A system-temp census shows 75 livechain_test_* folders, all from before this check. None of my roughly 40 processes left one.

### My mutants (my_mutants_c3e.py, 183 tests each)
- 22 mutants: 13 killed and 9 survived.
- Killed: E02, E09-E14, E16-E21.
- Survived:
  - E05 and E15 are equivalent: keep_earlier is a no-op outside the real evidence folder, and in a real run it is a no-op on the run's own file.
  - E01, E03, E04, E06, E07, E08 and E22 are real test gaps (C3-E04).

### Findings
- **C3-E01 MAJOR:** R11 never checks that --out can be created, and mkdir runs after ledger.begin. A file-parent, missing-drive or invalid-name --out spends the graded seeds with no verdict. This is outside C2-07's stated scope and is not acknowledged. Fix: create --out and the job files before begin, and refuse with R11 when that fails.
- **C3-E02 MAJOR:** stream_world_tail catches ValueError only and computes the last line's counts outside any try. A malformed AI world line makes the whole batch a harness ERROR instead of a FAIL. Fix: treat any parse or type error as last_ok False.
- **C3-E03 MINOR:** a persistent ledger-write failure leaves 'started' and exits 1, while the evidence, both docstrings and the hashed bounds text say the entry is finished.
- **C3-E04 NIT:** the guard's breadth, the ledger write's place inside it, the error path's own guards, the development error path and R12's development behaviour are unpinned.
- **C3-E05 NIT:** the stub results.json overwrites the complete one; grade DIR crashes on an ERROR batch and always exits 0.
- **C3-E06 NIT:** a KeyboardInterrupt while grading, or an exception whose str() raises, still leaves 'started'; uncaught exceptions exit 1, the FAIL code.
- **C3-E07 NIT:** the ERROR evidence embeds the unfinished build's 'VERDICT PASS' lines and the bounds text twice, and always says "while grading".

**Left behind:** only my own folder, check3/errors/: the repo copy, the probes, the logs, and 17 kept injection folders in inj_work/ for the records that were not as claimed.

### Check 3 - hashing (2026-11-05)

**Verdict: CONDITIONAL PASS.**
- I found no MAJOR.
- C2-02 and C2-05 are closed for every file the scan reaches. R9, R11 and R12 do what their tests say.
- Three MINOR gaps remain in what is hashed and what is refused. Each one lets a file run in a graded leg or in the grader with no hash and no refusal. They should be fixed, or ruled on, before the graded registration. Each fix changes the numbers sha256.

**Where I worked.**
- I worked on a copy of lc-c2 at d1a853bc, with no .git: `check3/hashing/repo`, plus a second copy, `repo_plant`, for planting.
- Every plant was removed afterwards. `repo_plant`'s file list ends equal to `repo`'s.
- The worktree is untouched: `git status` is empty, HEAD is d1a853bc, and live_chain.py's sha256 is unchanged.
- `bounds --run ch5` reproduces BOUNDS TEXT 2848a7b0… and NUMBERS e600c5d6….

**What holds.**
- **The closure.** It has exactly the 231 code files of GRADER_FILES (20 + 193 + 18), plus 11 data files: 242, as the CODE sentence says. Nothing is missing and nothing is extra.
- **The AI's code.** The 198 framework files the AI's own imports reach are all in the closure.
- **Path runs.** Every path-built argv is a PATH_ROOT, the file itself, `-m ai_player`, a `-c`, or a listed exemption.
- **C2-02.** The earlier probe now refuses all four edits.
- **R12 on main** (read-only, f4fa0d6f):
  - Ignored files under plugins/: only the two `__pycache__/` folders.
  - Of the 1,470 module names the scan follows, none resolves differently on main. An honest graded run would not be refused.
  - What runs there and is not hashed: the profiles folder (*.yml, `customcatchfilters.py`, which equals the template), mgba/, and CPython's caches. The bounds text declares all of these except the caches.
- **CRLF.** 27 GRADER files differ in raw bytes between main and the worktree, and only one differs in text (a real branch change). The AI-code sha256 is equal. `test_crlf_only_accepted` kills the raw-hash mutant.
- **Scan cost.** 2.2 s at 72% CPU load and about 3.0 s at 100% load; the builder measured 1.4 s on a quieter machine.
- **Real data.** R2 re-grades PASS with no row ignored. R0, R0b, R1 and V1 are unchanged.

**What still runs unhashed and unrefused** (`probe_resolution.log`):

| Case | Planted file | What Python runs | R12 | ledger.begin | Test's top-level rule |
|---|---|---|---|---|---|
| A1 | ignored `plugins/watchdog_plugin/__init__.py` | the package, in every leg | silent | accepts | silent |
| A2 | untracked `modules/memory/__init__.py` | the package, in every leg | silent | accepts | silent |
| A3 | untracked `ai_player/gates/ledger/__init__.py` | the grader's ledger (CLI prints PLANTED) | silent | accepts | silent |
| C1 | forged `gates/__pycache__/ledger.cpython-312.pyc` | the forged code (CLI prints PLANTED) | silent | accepts | silent |
| B1 | untracked `ai_player/gates/argparse.py` | the grader and the purity gate (still PASS) | silent | accepts | flags it (test only) |
| B2 | untracked `sandbox-pokebot/argparse.py` | every leg; the purity gate still PASS | silent | accepts | flags it (test only) |
| B3 | untracked `random.py` at the repository root | the grader (live_chain.py puts the root first) | silent | accepts | silent |
| E2 | `PYTHONPATH` folder with argparse.py | the grader and the truth harness | silent | accepts | n/a |

Controls:
- A new ignored plugin is refused by R12.
- An edited plugin is refused by ledger.begin.
- A `json.py` in sandbox-pokebot fails the purity gate.

**Findings**
- **C3-H01 (MINOR).** `_closure_file` looks for `X.py` before `X/__init__.py`, which is the reverse of Python's order. It also ignores cached and sourceless bytecode. Fix: follow Python's order, and refuse at R12 a same-named package, a .pyd, or a mismatched .pyc beside a closure module.
- **C3-H02 (MINOR).** Library-name shadows in the script folders are not checked by R12. The test-only `toplevel_problems` misses the repository root. PYTHONPATH is not refused for the grader or the truth harness. Fix: enforce the shadow rule at R12 for ai_player/gates, sandbox-pokebot and the root, and refuse PYTHONPATH and PYTHONHOME.
- **C3-H03 (MINOR).** `Deps.closure` and `Deps.git_state` defaults are unpinned. Mutants H10 and H11 switch off the production R12 and R9 at a graded run, and all 183 tests stay green. Fix: assert the Deps defaults in WiringTests.
- **C3-H04 (NIT).** The bounds text says '(each named)', but the refusal names at most 12. With 13 missing files, 12 are named.
- **C3-H05 (NIT).** A framework module that only the AI imports is never hashed. Today none escapes; a future door would.
- **C3-H06 (NIT).** 'A development batch only prints them' is unpinned (H07 survives).
- **C3-H07 (NIT).** The CODE sentence says 'no *.md, no __pycache__'. The code also skips every *.pyc. The purity gate refuses such a file at run time, so the batch would FAIL, not PASS.

**My mutants.** 26 mutants through the real runner (183 tests each; the control fails none): 23 killed, 3 survived (H07, H10, H11), all reported above.

**Tools and logs** (all in `check3/hashing/`): `probe_resolution.py`, `probe_ai_door.py`, `probe_small.py`, `probe_pyc_gate.py`, `main_r12.py`, `main_overlay.py`, `trace_grader_imports.py`, `ai_roots.py`, `argv_scan.py`, `my_mutants_h.py`, and their .log files.

**Nothing else changed:** no commit, no real ledger write, no emulator.

## 8. The third fix round (the builder, 2026-11-06)

A second builder finished this round. The first builder was cut off by a usage limit before it returned its report. Its edits were complete and uncommitted in the worktree lc-c2 (branch wip/live-chain-c2, HEAD d1a853bc), and only its external mutant runner had not finished. The second builder:
- checked those edits against every finding;
- fixed the regression lane's new failure (mgba);
- re-ran every check on the final bytes.

Scratch: s53/chainheld/c3fin/. The first builder's scratch is c3fix/.

### What changed, per finding

Every row has a FAULT test, a CONTROL and mutants. All are killed by the external runner.

| Id | What the code does now | Tests (FAULT / CONTROL) | Mutants |
|---|---|---|---|
| C3-E01 (MAJOR), C3-G05 | --out and every job file are made BEFORE ledger.begin (prepare_out). R11 refuses an --out under a file, on a missing drive, or with an invalid name: exit 2, ledger bytes unchanged, entry 'registered', nothing left behind. A ledger refusal also removes what was made. | out_listing_unmakeable, e2e_out_unmakeable_refused, e2e_out_undone_on_ledger_refusal / e2e_steps_before_begin | M183-M187, M265 |
| C3-RUN | The chains' run is guarded. On any exception, every running chain process is killed, the end sweep deletes their world files, and the entry is finished as ERROR 'while the chains ran' (exit 4). Ctrl+C is re-raised after the finish. The only ways an entry stays 'started': a hard kill of the orchestrator, or a ledger that cannot be written at all (then the output says so). | chains_error_finishes_entry, chains_interrupt_finishes_entry / e2e_graded_pass | M188-M192 |
| C3-E02 (MAJOR) | Every file the AI writes is untrusted (sites listed below). A bad line or value fails the leg, so the batch is GRADED, never ERROR. | e2e_untrusted_world_fails_not_errors (Stub plans wrong_type_last_line and deep_line: FAIL, exit 1), world_counts_untrusted, log_untrusted, chain_bad_verdict, kept_line_wrong_shape | M193 (restores 'except ValueError'), M194-M202 |
| C3-E03 | The ledger write is retried 3 times, the computed verdict first. If the ledger cannot be written at all: exit 4, and the evidence, results.error.json, stdout and ledger.unfinished.json say NOT FINISHED and give the command 'finish-entry DIR'. | ledger_finish_transient_retried, ledger_finish_computed_unwritable, ledger_unwritable_not_finished | M203-M208 |
| C3-E04 | Guard breadth, the error path's own guards, and a development batch's ERROR (exit 4, 'NO PASS (development: ERROR'). | grade_error_any_exception, results_write_error_both_paths, error_evidence_any_exception, dev_error_labelled / dev_unhashed_printed | M209-M214 |
| C3-E05 | results.error.json is written beside a complete results.json. grade DIR says 'this batch ended in ERROR' (exit 4). Its exits: 0 PASS, 1 FAIL, 2 nothing to grade. | grade_dir_error_batch, grade_dir_exit_codes | M215-M217 |
| C3-E06 | An uncaught exception exits 5. The stage is named and the error repr is safe. A KeyboardInterrupt finishes the entry, then re-raises. The parse names the file, and a scan error is R12. | main_crash_exit_5, unprintable_error, grading_interrupt, closure_parse_error_named | M218-M222 |
| C3-E07 | Embedded unfinished lines are prefixed 'UNFINISHED\| '. The bounds text is printed once. The stage is named. | evidence_write_error_bounds_once, evidence_error_finishes_entry | M223-M225 |
| C3-G01 | Each RAN leg must name its registered job: seed, personality, --profile, arm, and a run folder under profiles/<profile>. No two counted legs may share a run folder or a kept file. | leg_identity_each_field, relabelled_copy_stays_fail, shared_legs_never_count / real R0..V1: 0 problems | M226-M232 |
| C3-G02 | results.json carries the numbers. grade DIR verifies them against their sha256 and the ledger's bounds. A missing frozen or leftover record is FAIL. An older folder is printed UNVERIFIED. G20 is killed. | grade_dir_numbers_verified, grade_dir_missing_records, grade_dir_frozen_at_seal | M233-M237 |
| C3-G03 | All six identity fields are looped. | row_identity_each_field | M239-M241 |
| C3-G04 | A moved --out is read from out/<chain>/<leg>/world_last.jsonl. | grade_dir_moved_out | M238 |
| C3-G06 | An unexplained NOT RUN after a continuing leg fails custody. Statuses are read as stored (bounds text). | not_run_after_continuing_leg / STOP.txt and salvage controls; real data: none | M242-M244 |
| C3-H01 | CPython's resolution order. A package, extension module or sourceless .pyc beside a closure module is refused. So is a __pycache__ file that would load other code (check_purity rule (e), reused). | closure_resolution_planted, pycache_planted, resolution_enforced_register | M245-M251 |
| C3-H02 | The top-level shadow rule moved into live_chain and now covers the repository root. A graded run is refused while PYTHONPATH, PYTHONHOME or PYTHONSTARTUP is set; child processes drop them. | toplevel_planted, python_env_refused, toplevel_mgba_exempt | M252-M257, M266-M268 |
| C3-H03 | The production Deps defaults are pinned. | wiring_defaults | M259-M261 |
| C3-H04 / H05 / H06 / H07 | R12 names every file. The AI's modules.* and plugins.* imports start the closure. Development batches print unhashed files and are not refused. The CODE sentence is true. | closure_refusal_names_all, closure_ai_starts_planted, dev_unhashed_printed, bounds_needles | M262-M264, M214 |

C3-E02 sites (every reader of an AI-written file):
- world.jsonl, each line: `_line_parses`.
- Its last line: `world_counts`.
- The kept last line at grading: `kept_problem`.
- ai_player.log: `log_counts` (memory line) and `read_log_counts` (the file).
- The verdict file and its counters: `judged` around the purity and THIS_RUN checks; `dig` and `untrusted_text` for exit_reason.
- actions.jsonl: non-object records are filtered out.

Fix 4 and fix 5 disagreed on 'ledger.finish raising once'. Fix 4 governs:
- A single failure is retried with the computed verdict: 'done' PASS, exit 0.
- 'done' ERROR with exit 4 is pinned for a computed verdict that can never be written.

### The regression lane's failure (d1a853bc, test_live_chain, 2 failures)

- **Cause.** d1a853bc's test-side rule flagged sandbox-pokebot/mgba. That folder exists wherever the emulator is installed, which is always the case on the main checkout. It is the emulator's library: git-ignored, and unhashed by design.
- **Reproduced.** The worktree was copied with a fake mgba package laid out like main's real one. On that copy, d1a853bc's rule gives exactly the lane's three lines. The final code gives none (reproduce_lane.log).
- **Fix.**
  - mgba is exempt by name in live_chain's TOPLEVEL_NOT_FOLLOWED, with that reason. The exemption applies only in sandbox-pokebot.
  - The bounds text was wrong: it said only the framework's own names are spared. It now also names 'in sandbox-pokebot only, its git-ignored mgba and profiles, which are not hashed'.
- **Tests.** New case toplevel_mgba_exempt:
  - CONTROL: the real mgba layout, imported the way libmgba.py and glfw.py import it, gets no R12 entry.
  - FAULT: an unknown package beside it is still named, and so is mgba at the repository root and in ai_player/gates.
- **Mutants.** M266 (exemption dropped), M267 (exemption in any folder), M268 (the bounds clause removed).
- **The whole module in the copy with mgba:** 'Ran 493 tests in 524.818s', OK.
- **The main checkout, read only.** Every rule was run on it: R12 TOTAL 0 and run_refusal None for a graded ch5 run. mgba and profiles read EXEMPT. These are not refused: cache, logs, backups, scratchpad, the *.yml files, the root's __pycache__ and *.log files, install.py, install_sandbox.py and tools. The purity gate on main's ai_player passes. ai_code_sha256 is the same for main and the worktree.

### Checks on the final tree

- unittest, worktree: 'Ran 493 tests in 510.275s', OK.
- External runner, 26 classes: 'CONTROL M00: ran 227, failed none' and 'MUTANTS: 263 of 263 killed by the real runner; survived: none'.
- The checkers' survivors:
  - errors: 8 of 9 killed. E15 is left, which the checker classed equivalent.
  - grading: G01, G02, G03 and G20 killed. 8 equivalents are left.
  - hashing: 3 of 3 killed.
- Gates: check_purity, check_fairness, call_census, check_paths, check_grader_imports, ledger --check (99 entries) and extract_milestones --verify all PASS.
- The verifier's tools:
  - probes.py: 9 edits refused, a CRLF-only change accepted, an extra row IGNORED, a used --out refused with the entry 'registered'.
  - kind_demo.py: the original driver gives FAIL in all three scenarios.
  - closure.py: 139 files, all hashed.
- Real data:

| Folder | In-run | Re-grade | grade DIR exit |
|---|---|---|---|
| R0 | PASS | PASS | 0 |
| R0b | PASS | PASS | 0 |
| R1 | FAIL | FAIL | 1 |
| R2 | PASS | PASS | 0 |
| V1 | FAIL | FAIL | 1 |

  V1's reported-only LC.WORLD reads FAIL in-run and PASS on re-grade, as in round 2.
- New hashes: BOUNDS TEXT 5af3dc4092b916def90120ceefaf40c950569c995d500607af7be88e7e6d2603; REGISTERED NUMBERS 73d20fc76bc1a7381c90f653d5df8ee40bbf3a1405fbad7d73b23b4e28861175 (242 hashed files).
- git status --short: ' M ai_player/gates/live_chain.py', ' M ai_player/gates/test_live_chain.py'. Nothing is committed; HEAD is still d1a853bc.

### Not done

- No commit, no registration, no live leg.
- run_units and run_regression were not run. The full lane must be re-run on the committed tree, in a worktree with the emulator.
- E15 and the 8 grading equivalents are left as the checkers classed them.
- The 2,300 injections ran on the first builder's bytes. This session changed only strings and tests.

## 9. Check 4 (three checkers: grading, errors, hashing, 2026-11-06)

Three independent checkers, one lens each, on the third fix round's tree (82cebfd9). Their reports follow as written. Their findings were fixed in round 4 (section 10).

### Check 4 - grading (2026-11-06)

**Verdict: CONDITIONAL PASS.** No MAJOR. C3-G01 to C3-G06 are each closed as stated.
- The in-run graded path held every attack I tried, except one NIT inside the READ AS STORED trust model.
- Three MINOR gaps remain. All three are in the offline `grade DIR`, the same class as C3-G02.
- Two of the fixes I suggest (C4-G06's sentence, and any change to the bounds text) change the numbers sha256. They should be made or ruled on before the graded registration.

**Where I worked.**
- A copy of `lc-c2` without .git, in `check4/grading/repo`.
- live_chain.py hashes to `da4a97ef…` and test_live_chain.py to `214a102f…`, the builder's final bytes.
- `bounds --run ch5` on the copy gives BOUNDS TEXT `5af3dc40…` and REGISTERED NUMBERS `73d20fc7…`, the builder's values.
- At the end the worktree is unchanged: HEAD d1a853bc, the same two ` M` files, the same two hashes.
- No commit, no real ledger, no emulator.

#### Real-data controls (the new code)
`regrade_real.py` and `grade_dir_real.py` (the CLI, my copy's ledger, read only):

| Out | In-run | Re-grade | grade DIR exit | RAN legs | Identity problems | Shared | Unexplained NOT RUN |
|---|---|---|---|---|---|---|---|
| R0 | PASS | PASS | 0 | 6 | 0 | none | none |
| R0b | PASS | PASS | 0 | 6 | 0 | none | none |
| R1 | FAIL | FAIL | 1 | 3 | 0 | none | none |
| R2 | PASS | PASS | 0 | 15 | 0 | none | none |
| V1 | FAIL | FAIL | 1 | 3 | 0 | none | none |

- Every folder prints `NUMBERS: UNVERIFIED (no numbers)`.
- No kept line mismatches its row's sha256.
- Every status matches the in-run one, except V1's reported-only LC.WORLD (FAIL in-run, PASS on re-grade), as before.

#### The round-2 probes, re-run
- **G1:** each identity field alone gives FAIL, LC.REACH VACUOUS n 5, and the row named.
- **G2:** the relabelled copy gives FAIL, with LC.CUSTODY failing. In round 2 it gave PASS.
- **G2b, in-run:** exit 1, `GRADED, FAIL (failing: LC.REACH, LC.CUSTODY)`.
- **G4:** all 9 broken hand-offs still give FAIL.
- **G5:** every results.json edit now gives FAIL.
- **G5b:** a null leftover now gives LC.LEFTOVER FAIL.
- **G6:** the hidden NOT RUN leg gives exit 1, `GRADED, FAIL (failing: LC.CUSTODY)`.
- **probe_unguarded:** run_folders and main_profile_state now fail before `ledger.begin`, so the entry stays 'registered'. schedule gives exit 4 and the entry finishes as ERROR.
- **New probes:**
  - A moved honest --out re-grades PASS, exit 0.
  - A FAIL batch's grade DIR exits 1.
  - An ERROR batch's grade DIR exits 4 and does not crash.
- **LC.STARTER (V02):** all variants still FAIL, and two chains without a party give VACUOUS.

#### Findings

| Id | Severity | What |
|---|---|---|
| C4-G01 | MINOR | grade DIR's numbers check can be bypassed two ways. (A) Deleting `numbers` falls back to results.json's own reach_min: exit 0, PASS on an in-run FAIL batch. (B) Moving the numbers' seeds to 9001-9006 with reach_min 0 and the sha256 recomputed prints `NUMBERS: VERIFIED ...; NOT checked against the ledger`, exit 0, PASS. results.json's `ledger` entry id is never used. |
| C4-G02 | MINOR | grade DIR escapes the forged-stop rule two ways. An empty STOP.txt or ABORT.txt planted in --out (while frozen reads True) re-grades the hidden impure L5 PASS, exit 0. So does deleting the impure L5 from the row's legs list: PASS, exit 0, with `NUMBERS: VERIFIED`. In-run the deleted leg is salvaged and the batch FAILS. |
| C4-G03 | MINOR | grade DIR never reads a batch's ABORTED verdict or its purpose. An honest ABORTED batch (in-run exit 3) re-grades `PASS`, exit 0, with no line naming the abort. R2, a development batch, re-grades `PASS` with no development label. |
| C4-G04 | NIT | In-run, a hidden leg whose stored reason reads "the chain's process ended" gives exit 0, GRADED PASS, although the orchestrator's events record no salvage. This is inside READ AS STORED, but the events could be checked. |
| C4-G05 | NIT | Mutant C05 (the rule fires after any RAN leg) survives all 227 tests, yet turns an honest 5-of-6 batch from PASS into FAIL. case_reach_5_of_6_pass asserts only LC.REACH. C06 and C03 also survive. |
| C4-G06 | NIT | The bounds sentence "a row copied from another chain never counts" overclaims. A copy with 42 fields rewritten and 5 kept files copied gives PASS (the trust model). |

#### Mutants
31 mutants plus a control, each run through the real runner over 26 classes (227 tests). The M00 control failed none.
- **Killed 15**, among them G01, G02, G03 and G20, the round-2 survivors.
- **Survived 16:**
  - The 8 round-2 equivalents.
  - 4 new equivalents: C01, C04, C07 and C11.
  - 4 that are not equivalent:
    - C05, reported as C4-G05.
    - C06, which shows C4-G03.
    - C03, reported as C4-G05.
    - C08, which affects only an ABORTED folder.

#### Files (all in `check4/grading/`)
- **Scripts:** copy_tree.py, regrade_real.py, grade_dir_real.py, grade_dir_r2_full.py, probes_grading.py, probes_grading2.py, probe_unguarded.py, probes_c4.py, probes_c4b.py, probe_deep_copy.py, probe_c05.py, my_mutants_c4.py.
- **Logs:** regrade_real_old.log, grade_dir_real.log, grade_dir_r2_full.log, probes_1_rerun.log, probes_2_rerun.log, probe_unguarded.log, probes_c4.log, probes_c4b.log, probe_deep_copy.log, probe_c05.log, my_mutants_c4.log and .json.
- **Bounds output:** bounds_c4.txt.
- probes_1_rerun.log ends at G7, which crashes: its old probe expects results.json on the ERROR path. Probe E in probes_c4.py replaces it.
- The copy `repo/` is left in place for a re-run.

### Check 4 - errors (2026-11-06)

**Scope.** Error paths, refusal order and untrusted AI data.

- **What was checked.** A copy of the lc-c2 worktree with the builder's final bytes (live_chain.py sha256 da4a97ef..., test_live_chain.py 214a102f...), in s53/chainheld/check4/errors/repo.
- **What was not done.** No commit, no staging, no registration, no emulator.
- **Probes.** All in check4/errors/:
  - probe_c4.py, with logs probe_c4.log, probe_c4_b.log and probe_c4_c.log.
  - kill_release.py, exit_codes.py, grade_real.py and time_window.py.
  - mut4.py, with mut4.log.
  - Check 3's probes, re-run against my copy from old/: scen.log, probe_refusals.log, probe_e2e.log, inj_pre_pass.log and inj_post_dry.log.

**Verdict: FAIL.** There are two MAJOR findings:
- C4-E01: an AI-written world.jsonl that is a folder still turns a graded FAIL into ERROR.
- C4-E02: moving the --out writes before ledger.begin lets a second launch delete the first launch's job files. The honest batch is then GRADED FAIL on the held-out seeds. This is a regression of this round.

#### Closed (re-run on the final bytes)

| Id | Evidence |
|---|---|
| C3-E01 | --out under a file is refused R11, the ledger is unchanged and the entry stays 'registered'. The same registration then runs with a good --out. A missing drive and an invalid name are refused too. Refusals: 34 of 34 as claimed. |
| C3-E02 | Check 3's arms C, D and E now give GRADED FAIL, exit 1, and no chain-process crash. Round 2 gave ERROR. |
| C3-E03 | When the ledger is never writable: exit 4, entry 'started'. The evidence's last line, results.error.json and stdout all say NOT FINISHED and give the finish-entry command; ledger.unfinished.json is written. The command then finishes the entry. A real process exits 4. |
| C3-E04 | Check 3's survivors R01, R03-R08 and R22 are killed by the real runner (227 tests; the control fails none). R15 survives; it is equivalent. |
| C3-E05 | results.error.json is written beside a complete results.json. grade DIR on an ERROR batch exits 4. Real data: R0, R0b and R2 exit 0 PASS; R1 and V1 exit 1 FAIL. |
| C3-E06 | Ctrl+C or an unprintable exception while grading: the entry is 'done' ERROR and the stage is named. The closure-scan error names the file. Process exit codes: a crash gives 5, Ctrl+C 0xC000013A, a refusal 2. |
| C3-E07 | The bounds text appears once in the ERROR evidence, and all 223 embedded lines are marked 'UNFINISHED\| '. |
| C3-RUN | A spawn that raises gives ERROR 'while the chains ran', exit 4. Ctrl+C during the chains kills the children, runs the sweep and finishes the entry. The pre-window injection sweep (249 injections): none left 'started', none escaped. |

#### New findings

- **C4-E01 (MAJOR): a world.jsonl that is a FOLDER gives the harness's ERROR.**
  - **Reproduction.** In a batch whose honest verdict is FAIL, one leg's world.jsonl is replaced by a folder: 'returned 4', 'GRADED, ERROR (harness: PermissionError ... world.jsonl ... while grading'. The control, where the same leg writes no world file, gives GRADED FAIL, exit 1.
  - **Cause.**
    - finish_leg gates on stat(), which a folder passes. stream_world_tail's open() then raises.
    - finish_leg runs outside run_chain's try, so the chain process dies.
    - The salvage in the orchestrator calls finish_leg again and raises the same error inside the guard.
  - **What it refutes.** C3-E02's 'every reader' claim, and the hashed sentence '... never the harness: the batch is still graded'.
  - **Fix.** Measure only when is_file() is true, and guard finish_leg's measuring and copying against OSError. Add an e2e test with a Stub plan 'world_is_folder'.
- **C4-E02 (MAJOR): a second launch of the same graded run deletes the first launch's job files.**
  - **Reproduction.** Launch B's own facts are gathered before launch A's prepare_out: 'out_entries []', no refusal.
    - B overwrites A's job files, is refused by the ledger (R10), and its undo_out deletes them.
    - A's six chains die with FileNotFoundError. A is 'GRADED, FAIL ... 0 of 6'.
  - **The window.** At least 3.7 s on the copy (closure scan 3.10 s and the G-3 walk 0.62 s), plus the git fetch and the snapshot.
  - **Why it is a regression.** At d1a853bc the writes came after begin, so a launch refused by the ledger wrote nothing.
  - **Fix.** Claim --out exclusively (O_EXCL). undo_out then removes only what this process created.
- **C4-E03 (MINOR): a second Ctrl+C inside the guard leaves the entry 'started'.**
  - **Reproduction.** The entry stays 'started', with no evidence, no results.error.json and no ledger.unfinished.json.
  - **Why it happens.** The guard is silent for 10 s with one world file still held open. With real processes, the first delete after a kill fails with WinError 32 (5 of 5 trials), so measure_then_delete waits 2 s per running leg before anything is printed.
    - Every step of the guard catches Exception only.
    - Mutant N03 (an end sweep that raises escapes the guard) survives.
  - **False text.** The bounds text, the module docstring and run_batch's docstring all say that only a hard kill or an unwritable ledger leaves 'started'.
  - **Fix.** Ignore SIGINT while the guard runs, and print one line first.
- **C4-E04 (MINOR): a lone surrogate in exit_reason crashes the chain process.**
  - **Reproduction.** json.loads of '\\ud800' leads to a UnicodeEncodeError in the row.json write. Legs that met every rule are salvaged, and the batch flips PASS (6 of 6, the control) to FAIL (4 of 6).
  - **Fix.** Escape in untrusted_text, or write rows with ensure_ascii=True.
- **C4-E05 (MINOR): finish-entry writes any verdict.**
  - **Reproduction.** A hand-edited 'GRADED, PASS' in ledger.unfinished.json was written to the 'started' entry: exit 0, and ledger.check says the ledger is well formed.
  - **Fix.** Accept only this driver's ERROR verdict, rebuilt from results.error.json.
- **C4-E06 (MINOR): grade DIR reads ERROR from results.error.json only.**
  - **Reproduction.** Without that file, an ERROR batch re-grades PASS with exit 0, while its NUMBERS line says it matched 'the bounds sha256 ledger entry #1 registered' (an entry whose verdict is ERROR). After finish-entry, the ledger status it prints ('NOT finished') is stale.
  - **Fix.** Read the entry's status and verdict from the ledger.
- **C4-E07 (NIT): prepare_out's undo misses edges.**
  - **Reproduction.** On an invalid name under a missing parent, prepare_out leaves the parent folders mkdir created. Mutants N01 and N05 (the undo on a part-way failure, and on a begin raise other than Refused) survive.
  - **Effect.** The seeds stay unspent.

#### Mutants
- Real runner: 11 of 15 killed.
- Survivors: R15 (equivalent), N01, N03 and N05 (filed above).

#### Not done
- The full 2,300-injection sweeps: only sampled pre-window and post-window (dry) sweeps ran.
- No test of a real double Ctrl+C in a console.
- The race was simulated in one process. Launch B's facts came from its own real gather_facts call, timed between A's gather and A's prepare_out.

### Check 4 - hashing (2026-11-06)

**Verdict: CONDITIONAL PASS.** I found no MAJOR.

**What is closed:**
- Every finding of my lens: C3-H01 to C3-H07, the mgba exemption, the read-only check on main, and CRLF.
- An honest graded run on the MAIN checkout as it is today is not refused by any rule.
- R2 still re-grades PASS.

**What remains:** six MINOR gaps, each a file or environment variable that runs unhashed code in a graded leg, in the truth harness or in the grader, with R12 and ledger.begin silent. Each needs a deliberate plant or an operator's environment variable, the class the round-2 check also rated MINOR. Fix them, or rule on them, before the graded registration. Every code fix changes the numbers sha256. Two NITs are test-only.

**Where I worked.**
- Copies of lc-c2 (d1a853bc plus the uncommitted round 3, without .git): check4/hashing/repo, and repo_plant for plants.
- Every plant was removed. repo_plant's file list equals repo's (tree_diff.py). Both copies gained sandbox-pokebot/profiles/*.yml, which the framework writes at start when my truth-harness runs boot; that folder is git-ignored and exempt.
- The worktree is untouched: status ' M live_chain.py', ' M test_live_chain.py', HEAD d1a853bc, sha256 da4a97ef... and 214a102f....
- On main I used read-only git only (--no-optional-locks, no fetch). Its status is empty before and after.
- `bounds --run ch5` on my copy reproduces BOUNDS TEXT 5af3dc40... and NUMBERS 73d20fc7... (242 files).

**What holds:**
- **The round-2 probes, re-run.** These are refused by R12, and the CLI refuses at R12:
  - A1, A2, A3 (a package beside a module);
  - C1 (a forged cache); N9 (an unchecked hash pyc); N10 (a case-variant cache name);
  - B1, B2, B2c, B3 (library shadows);
  - K1 (a new plugin); K3 (all 13 named); D1 (the AI's door module);
  - E2 (PYTHONPATH).

  K2 (a one-byte edit) is refused by ledger.begin. C2-02's probe still refuses all four edits.
- **CRLF.** K4: flipping memory.py and ledger.py to the other line ending is accepted. On main, 27 GRADER files differ in raw bytes and 1 in text.
- **Main** (main_check4.log):
  - The real gather_facts with read-only Deps, and the branch's .py files overlaid from my copy.
  - All R12 parts are 0, and 228 caches were judged.
  - Free 56.3 GB, no ai-livechain profiles, HEAD == origin/main e4cd1617, nothing dirty, no PYTHON* set.
  - 'run_refusal -> None'. ai_code_sha256 is 864bb2dc on both.
- **mgba.** A fake mgba/ package plus a planted mgba.py: the package wins, so nothing beyond the library loads. mgba at the root and in gates is refused.
- **Real data.** R0, R0b and R2 re-grade PASS (exit 0); R1 and V1 re-grade FAIL (exit 1).

**What still runs unhashed and unrefused.** Run from my plant copy. "R9" means R12 passed, because the copy has no .git.

| Case | Plant or variable | What runs it | R12 | ledger.begin |
|---|---|---|---|---|
| N3 | `sandbox-pokebot/modules.pyw` (modules/ is a namespace folder) | the real truth harness, and every leg | silent | accepts |
| N3b, N3d | `plugins.pyw`, `modules/web.pyw` | every leg | silent | accepts |
| N1 | PYTHONPYCACHEPREFIX plus a forged ledger cache under it | the grader CLI (refused only at R9) | silent | accepts |
| N2 | PYTHONCASEOK=1 plus `Random.py` at the root | the grader CLI | silent | accepts |
| N12 | PYTHONUSERBASE with a .pth | the grader CLI | silent | accepts |
| N7, N7b | `sandbox-pokebot/typing_extensions.py`, `gates/annotated_types.py` (imported by pydantic) | the real truth harness | silent | accepts |
| N4, N4b | a forged `ai_player/__pycache__/__init__` (or `options`) cache | the grader CLI and the truth harness; the purity gate fails it only at launch | silent | accepts |
| N5 | a gates/argparse.py that switches R12 off | the grader (R12 and R9 skipped; stopped at R10 only because nothing was registered) | bypassed | reached |
| evidence | `ai_player/evidence/zz_brain.py`, imported by the AI and changed after registration | every leg; the purity gate PASSES | silent | accepts |

Controls:
- N3c: modules.py is refused.
- N2c: no PYTHONCASEOK, so Random.py does not run.
- N1c: the variable alone.
- B1: a passive argparse.py is refused.
- In the evidence probe, the same change in a hashed AI file is refused.

**Findings**
- **C4-H01 (MINOR).** _closure_file and _opaque_names ignore .pyw, and TOPLEVEL_HOMES exempts by name. A .pyw replaces the namespace packages modules, plugins, modules/web and modules/built_in_plugins. The bounds text's 'other than that module itself' is false for such a file.
- **C4-H02 (MINOR).** PYTHON_ENV misses PYTHONPYCACHEPREFIX (the AI's own launcher already strips it), PYTHONCASEOK (the top-level names are compared with case) and PYTHONUSERBASE. PYTHONSTARTUP never runs for a script (startup_probe.log).
- **C4-H03 (MINOR).** Library-internal imports are not checked. The truth harness loads 13 third-party names that R12 never looks for (trace_site.log).
- **C4-H04 (MINOR).** The caches of the 8 to 16 AI modules that grader processes import are judged by no R12 rule (ai_in_grader.log).
- **C4-H05 (MINOR).** R12 runs after live_chain's imports, so a shadow that acts can switch it off. run_refusal's `return closure_refusal(...)` also skips R9, R6 and R7 if that call ever returns None.
- **C4-H06 (MINOR).** ai_code_sha256 skips evidence/, but the purity gate judges a .py there as play code, and the AI may import it. AI code there can change after registration without a refusal.
- **C4-H07 (NIT, test-only).** 12 load-bearing branches of the resolution, top-level and AI-start rules are unpinned. The fault behind each one is shown refused by the real code and loaded by CPython; the most important is a root modules.py, which the truth harness ran in place of the framework.
- **C4-H08 (NIT, test-only).** Deps' watch, kill and snapshot defaults, and the bodies of free, leftover and g3, are unpinned. In production, LC.FROZEN, the disk guard's kill, LC.LEFTOVER, R5 and R6 could go vacuous with every test green.

**Mutants** (mutants4.py, the real runner: 26 classes, 227 tests; X00 failed none). 28 of 48 are killed. The 20 survivors:
- 12 are C4-H07: R03, R04, R06, R07, T03, T04, T06, T07, T08, T10, A02, A03.
- 6 are C4-H08: W01, W02, W04, W05, W06, W07.
- 2 I class as equivalent today: T09 and R08.

Logs: check4/hashing/{probe4_*.log, probe_evidence.log, main_check4.log, trace_site.log, ai_in_grader.log, fileless.log, startup_probe.log, probe_small4.log, probe_unhashed4.log, regrade_real4.log, mutants4_main.log, mutants4_h07.log, bounds4.txt}.

**Not done:**
- No commit, registration, emulator or live leg.
- I did not re-run the builder's M245 to M268 or the 2,300 injections.
- The truth-harness demonstrations stop at 'No module named mgba', because my copy has no emulator. Every PLANTED line printed before that point, during the framework's imports.

## 10. The fourth fix round (2026-11-06; commit cd11bde4)

The round-4 builder was cut off by a usage limit during its final runs, so it wrote no report. Its work was committed as found (cd11bde4) and its final runs were finished by a script: 592 tests OK in the worktree and in a copy with a fake mgba; the external runner killed 337 of 338 mutants (M280_sigint_not_restored survived; pinned in round 5). The round also wrote the driver's threat model into its docstring and its hashed bounds text: it guards against honest-case harness defects, accidental contamination, and edits of an --out folder after the run, which must never make grade DIR report a verdict better than the ledger's; it does NOT stop code crafted to switch the grader off from inside its own process (C4-H05), where the purity gate and R9 are the defense.

**What the code does now, per check-4 finding.** This list is CHECK 5's inventory (an independent checker reading the round-4 code), not the builder's own words:

- **C4-G01** (closed per check 5): regrade_dir finds the batch's ledger entry NOW by its seeds (id and bounds sha256 preferred: find_entry). verify_numbers says VERIFIED only when that entry's bounds_sha256 equals the numbers' sha256, and numbers_jobs_problems requires one job per seed, named LC-<pair>-<seed>. The final verdict is the worst of the rows' re-grade and the entry's verdict; a graded folder that no entry verifies is UNVERIFIED, exit 1. FAULT tests: C4GradingTests.grade_dir_never_better_than_ledger, RegradeTests.grade_dir_numbers_verified. CONTROL: the honest folder in the same tests exits 0.
- **C4-G02** (closed per check 5): grade_batch fails LC.FROZEN when STOP.txt is in --out beside a frozen record that says the tree held. rederived_chain puts any counted row whose (leg, target) list is not exactly the registered one into custody_chain, so LC.CUSTODY fails. FAULT test: C4GradingTests.grade_dir_planted_stop_and_deleted_leg (mutants M302, M303 killed). CONTROL: the same test's honest batch passes, and the folder in place exits 0.
- **C4-G03** (closed per check 5): regrade_dir reads ABORTED from ABORT.txt, from results.json's verdict or from the ledger entry, and exits 3. The purpose comes from the entry (else results.json's, marked unconfirmed). The verdict line is labelled 'DEVELOPMENT, not graded'. FAULT test: C4GradingTests.grade_dir_aborted_and_development (M295, M298, M299, M308, M309 killed). CONTROL: real R2 still PASS, labelled.
- **C4-G04** (closed per check 5): The salvage exemption needs the orchestrator's own record. In-run it uses salvaged_chains(events) from memory. grade DIR uses results.json's or results.error.json's events. The stored reason text alone no longer explains a stop. FAULT test: C4GradingTests.salvage_exemption_needs_record, with an honest recorded salvage as its CONTROL (M304, M305, M306 killed).
- **C4-G05** (closed per check 5): Pins: case_reach_5_of_6_pass asserts a full GRADED PASS with LC.CUSTODY PASS for one miss at L1, L3 and L4 (M307 = check 4's C05, killed). not_run_after_continuing_leg has an ABORT.txt control (M308 = C06, killed). leg_identity_each_field has the profile-folder FAULT (M310 = C03, killed).
- **C4-G06** (closed per check 5): The hashed bounds sentence now states its condition: 'so a row copied from another chain fails custody unless every one of these records is rewritten as well (the rows are trusted as the harness wrote them)'. Text only. The deep copy still passes, as the trust model documents.
- **C4-E01** (closed per check 5): finish_leg never raises. It measures world.jsonl only when os.path.isfile is true, tries it 3 times 1 s apart, and records a NOTE for every failed read, measure, delete or copy (a leg not measured fails C3). read_log_counts, kept_problem and read_leg use os.path checks and broad excepts. salvage_leg calls the same finish_leg. FAULT tests: C4ErrorTests.world_kind_untrusted, e2e_world_folder_graded (M269, M270, M271 killed). CONTROL: the same leg writing no world file.
- **C4-E02** (closed per check 5): prepare_out creates BATCH.claim.json with O_CREAT|O_EXCL, then requires --out to hold nothing else. An OutTaken is R11 (exit 2, before ledger.begin), and undo_out removes only this call's own files (rmdir only for an empty folder). FAULT tests: C4ErrorTests.out_second_launch_refused, out_written_after_listing (M273, M274, M275 killed). CONTROL: e2e_graded_pass and e2e_out_empty_proceeds.
- **C4-E03** (closed per check 5): The guard calls hold_interrupts first. It prints one line, then sets SIGINT to SIG_IGN until the entry is written. stop_children, the end sweep, every finish_on_error step and the ledger write catch BaseException, note it, and finish (the write is tried twice). An entry already 'done' is never overwritten. The interrupt is raised again afterwards. FAULT tests: C4ErrorTests.guard_second_interrupt, guard_after_finish_keeps_verdict, error_finish_retried (M279, M281-M287 killed). CONTROL: chains_interrupt_finishes_entry. M280 survives in the full runner: see C5-04.
- **C4-E04** (closed per check 5): utf8_safe escapes any str that cannot be encoded (values and dict keys). untrusted_text, safe_text and _write_json use it, and the evidence writes use errors='backslashreplace'. FAULT test: C4ErrorTests.lone_surrogate_graded (M288, M289, my MY09 killed). CONTROL: e2e_graded_pass.
- **C4-E05** (closed per check 5): finish-entry writes the verdict only when unfinished_problems is empty. It rebuilds the driver's ERROR line (error_line) from results.error.json and the entry, requires ERROR_FORM, and requires the same id, seeds, numbers sha256 and ledger_finished False. FAULT test: C4ErrorTests.finish_entry_only_error (M290-M293 killed). CONTROL: GradeErrorTests.ledger_unwritable_not_finished. It introduced the regression C5-02.
- **C4-E06** (closed per check 5): ledger_result reads the entry's status and verdict NOW. STARTED counts as ERROR, an ERROR verdict counts as ERROR, and the printed line reads the entry's status (no longer results.error.json's ledger_finished). FAULT test: C4GradingTests.grade_dir_error_states (M295, M296, my MY10 killed).
- **C4-E07** (closed per check 5): prepare_out records every missing parent BEFORE mkdir, so a failure part-way removes them too. FAULT test: C4ErrorTests.out_undo_edges (the 3rd write fails; ledger.begin raises), with M276, M277, M278 killed. CONTROL: e2e_out_undone_on_ledger_refusal.
- **C4-H01** (closed per check 5): _closure_file tries __init__.py, __init__.pyw, X.py, X.pyw, so a .pyw the closure reaches joins it and R12 names it. TOPLEVEL_HOMES exempts exactly the folder or file that IS the module. FAULT test: C4HashingTests.closure_pyw_planted (M311-M314 killed).
- **C4-H02** (closed per check 5): python_env_refused refuses every PYTHON* variable except PYTHONIOENCODING, PYTHONUTF8, PYTHONDONTWRITEBYTECODE and PYTHONUNBUFFERED (R12, even when set to nothing). child_env and child() drop the rest. Script-folder names are compared without case. FAULT tests: ClosureTests.python_env_refused (M317, M318 killed), C4HashingTests.toplevel_installed_planted (M319 killed). CONTROL: the four allowed ones set, a graded run proceeds.
- **C4-H03** (closed per check 5): outside_modules lists every importable entry of every sys.path folder outside the repository (plus builtins). toplevel_problems refuses a module or package with such a name, and a namespace folder only beside an installed namespace folder. FAULT test: C4HashingTests.toplevel_installed_planted (M320, M321 killed). CONTROL: main is not refused.
- **C4-H04** (closed per check 5): ai_problems (in closure_missing, so before ledger.begin) runs pycache_problems over every .py of ai_player outside gates/ and evidence/. FAULT test: C4HashingTests.ai_problems_planted (M322, M325 and my MY07 killed).
- **C4-H05** (closed per check 5): This is now a stated limit (threat-model sentence in the bounds text and the docstring). run_refusal no longer returns closure_refusal's None, so R9, R6 and R7 still run. FAULT test: C4HashingTests.run_refusal_falls_through (M326 killed). CONTROL: a closure entry is R12.
- **C4-H06** (closed per check 5): ai_problems refuses any .py, .pyw, .pyc or extension module under ai_player/evidence/ (R12). FAULT test: C4HashingTests.ai_problems_planted (M323 killed). CONTROL: main has 825 evidence files and none is code.
- **C4-H07** (closed per check 5): Each listed branch is pinned by a planted FAULT case in C4HashingTests: resolution_branches_planted, pycache_branches_planted, toplevel_branches_planted, ai_starts_branches_planted (M314, M316, M327-M336 killed).
- **C4-H08** (closed per check 5): wiring_defaults now also covers watch, snapshot, code_line and kill. wiring_bodies checks the production bodies of watch_tree, leftover_processes, safe_free and g3_scan.

## 11. Check 5 (one checker, scoped to the round-4 diff, 2026-11-06)

**Verdict: CONDITIONAL PASS.** All 21 check-4 findings are closed by their own probes. The honest 6-of-6 and 5-of-6 batches are GRADED PASS, and grade DIR agrees with the ledger. The main checkout is not refused. Two MINOR gaps should be fixed before the graded registration, because live_chain.py's bytes go into the numbers sha256: C5-01 and C5-02. There are three NITs (test pins and one reporting rule).

### What was checked

- **Code:** worktree lc-c2 at cd11bde4, copied without .git to check5/repo, plus a plant copy, check5/repo_plant. Hashes: live_chain.py c213893380540342, test_live_chain.py 5a56a7e390681ed3.
- **Bounds:** `bounds --run ch5` on the copy gives bounds text sha256 505d746d..., numbers sha256 ce91e535.... These equal c4fix/bounds_final.txt.
- **Untouched:** the worktree, the main checkout and the learner were not changed (git status clean in both checkouts).
- **Progress file:** check5/STATE.md. Logs are in check5/logs/.

### 1. Closure of check 4's findings (each probe re-run on the copy)

| Finding | Was | Now (probe line) |
|---|---|---|
| G01 numbers bypass | exit 0 PASS | A: exit 1; B: exit 1 'MISMATCH: the numbers' jobs ... not one per seed of 9001-9006' |
| G02 planted stop, deleted leg | exit 0 | STOP.txt: exit 1, LC.FROZEN FAIL; ABORT.txt: exit 3; L5 deleted: LC.CUSTODY FAIL, exit 1 |
| G03 ABORTED, development | exit 0 PASS | exit 3 'this batch was ABORTED'; R0 'DEVELOPMENT, not graded: PASS' |
| G04 salvage text | exit 0 PASS | exit 1 'GRADED, FAIL (failing: LC.CUSTODY)' |
| G05 5-of-6 pin | C05 survived | M307 killed; e2e 5-of-6 at L1, L3, L5 all PASS |
| G06 wording | claim too wide | the bounds sentence states its condition |
| E01 world.jsonl a folder | exit 4 ERROR | exit 1 GRADED FAIL, no chain crash |
| E02 second launch | A FAIL, six crashes | B exit 2 R11; A's job files intact; A PASS |
| E03 second Ctrl+C | entry 'started' | entry 'done' ERROR; first line after 0.0 s |
| E04 lone surrogate | FAIL by a crash | PASS 6 of 6, no crash |
| E05 edited PASS finished | finished | REFUSED, entry still 'started' |
| E06 ERROR from the ledger | exit 0 | exit 4; the status line read now |
| E07 parents left | left behind | removed |
| H01 .pyw beside namespace | unrefused | named by R12 |
| H02 PYTHON* variables | only 3 refused | PYCACHEPREFIX and USERBASE refused; Random.py named without CASEOK |
| H03 library names | unrefused | typing_extensions and annotated_types named |
| H04 AI __pycache__ | not refused | refused at R12 before ledger.begin |
| H05 hostile shadow | R9 skipped | out of model (stated); R9 now fires |
| H06 evidence code | not refused | named by R12 |
| H07, H08 pins | survived | M314, M316, M327-M344 killed |

### 2. The survivor M280

- It is **not equivalent**. It survives the full runner only because of test order.
- Run alone, guard_second_interrupt kills it.
- With a sentinel handler installed first, the real code restores the sentinel and M280 leaves SIG_IGN.
- The missing pin is described in C5-04.

### 3. The round-4 diff: regressions and claims

**Honest batches.** 6-of-6, and 5-of-6 with the miss at L1, L3 or L5:
- in-run exit 0;
- all nine GRADED checks PASS: LC.REACH, LC.PURITY, LC.THIS_RUN, LC.WORLD_SIZE, LC.CUSTODY, LC.STARTER, LC.MEMORY, LC.FROZEN, LC.LEFTOVER;
- the ledger says 'GRADED, PASS';
- grade DIR exits 0 with the same nine PASS.

**Other honest paths:**
- A relaunch on the same --out after an R10 refusal: PASS.
- A development batch with an unwritable ledger, then finish-entry: accepted.
- The real folders re-grade as before: R0, R0b and R2 PASS (R2 'unconfirmed'); R1 and V1 FAIL. The ledger is unchanged.

**Main checkout (read only, with a real launch's sys.path):**
- closure_missing(MAIN) is [] (5.2 s).
- 662 installed names; none collides with a script-folder entry.

**PYTHON* variables on this machine:**
- Bash: none.
- PowerShell tool: PYTHONIOENCODING (allowed).
- User and Machine scopes: none.
- Learner tasks: run_agent.ps1 sets none; watchdog.ps1 sets PYTHONIOENCODING (allowed).
- No false refusal.

**Findings:**
- **C5-01 MINOR.** A graded FAIL folder with four edits to results.json gives grade DIR exit 0: the numbers deleted, the seeds moved to 9001-9006, the purpose 'development', reach_min 0. The output says 'DEVELOPMENT, not graded (unconfirmed: no ledger entry): PASS'. The controls exit 1. This breaks threat-model sentence (c) in spirit; the docstring allows it.
- **C5-02 MINOR (a regression of the C4-E05 fix).** The ledger and results.error.json are both unwritable, as on a full disk. The printed finish-entry command is then REFUSED, and the entry stays 'started'. The control (only the ledger fails) finishes, exit 0.
- **C5-03 NIT.** A planted ABORT.txt or results.error.json turns a ledger FAIL into grade DIR exit 3 or 4, with no contradiction said.
- **C5-04 NIT.** M280's pin is order-dependent.
- **C5-05 NIT.** The 'entry never begun' branch is unpinned (MY02).

No MAJOR. No honest batch got a wrong verdict, an ERROR or a refusal. No new race was found: the claim is taken by O_EXCL before anything is written, and undo removes only empty folders it made.

### 4. Mutants

- My 12 mutants: 9 killed (MY04 by the suite dying), 2 equivalent (MY01, MY11), 1 not equivalent and unpinned (MY02).
- The check-4 runner: 337 of 338 killed. M280 is the exception (C5-04).

### What to do before registration

1. Fix C5-01: check the folder's own jobs and rows against its seeds when the numbers are missing, and check the recorded ledger id.
2. Fix C5-02: let finish-entry rebuild the ERROR verdict from ledger.unfinished.json, or print the direct ledger.finish line.
3. Add the C5-04 and C5-05 pins.
4. Re-run the module, the runner, and `bounds --run ch5` (the numbers sha256 will change).

## 12. The fifth fix round (the builder, 2026-11-06)

**Result.** All five findings of check 5 are fixed in the worktree lc-c2 (branch wip/live-chain-c2, on top of cd11bde4). Nothing is committed and nothing is staged. Each fix has a FAULT test built from the finding's own scenario, a CONTROL, and mutants. The real runner kills all 353 mutants, including M280, which survived round 4. The changes are in live_chain.py and test_live_chain.py.

**Final bytes:**
- live_chain.py: sha256 fbe3b711... (CRLF only)
- test_live_chain.py: sha256 eb0551c5... (CRLF only)
- bounds --run ch5: the bounds text sha256 is unchanged, 505d746d.... The numbers sha256 is now a6e52209ee546e98f6a5723b763e56cb2e7a5346b034619595749ab68902ba2f (it was ce91e535...). The only cause is live_chain.py's own grader-file hash.

### What changed

- **C5-01 (MINOR).** grade DIR no longer exits 0 for an edited graded FAIL folder.
  - With no numbers, the folder's own jobs are still checked against its own seeds and chain count.
  - New `recorded_problems`: the ledger entry that results.json's recorded id names is read now. If it is a live_chain entry, it must have the folder's seeds and purpose. Otherwise the result is MISMATCH (graded FAIL, exit 1).
  - Two exceptions, both needed for real data:
    - An entry of another driver. After the ledger merge, R0, R0b, R1 and V1 name #86, #88, #87 and #89, which are now other drivers' entries.
    - An id explained by the folder's own entry, met by its seeds and bounds sha256 under another id (a renumbered ledger).
  - The check's attack now gives exit 1, with both reasons printed. An unconfirmed development folder (like R2) still exits 0 by its re-grade. The optional third fix was not done, because R2 must keep its result.
- **C5-02 (MINOR, the regression).** I chose the first option. ledger.unfinished.json now carries "error_record", a copy of the results.error.json fields that finish-entry rebuilds from. When results.error.json is missing, finish-entry uses that copy under the same checks:
  - this driver's ERROR form;
  - the rebuilt verdict line;
  - the same entry id, seeds and numbers sha256, with ledger_finished false.

  The command the guard prints now works when results.error.json could not be written: the entry is finished as ERROR. An edited copy is refused, whether it says PASS, names other numbers, or is removed.
- **C5-03 (NIT).** A folder ERROR or ABORTED mark beside an entry finished with PASS or FAIL is now a contradiction. The marks are results.error.json, ABORT.txt, or ABORTED in results.json's verdict. grade DIR prints "THE FOLDER CONTRADICTS ITS LEDGER ENTRY ... (edited after the run?)" and grades FAIL (exit 1), never ABORTED (3) or ERROR (4). Honest ABORTED and ERROR batches are unchanged.
- **C5-04 (NIT).** New test guard_sigint_restored. It installs a fresh sentinel SIGINT handler, then runs a guard that returns (exit 4) and one that re-raises. For each it checks SIGINT is ignored during the guard and the sentinel is back after. M280 is now killed in the full runner whatever the test order.
- **C5-05 (NIT).** New test grade_dir_entry_unbegun_or_unreadable. An entry that was never begun, or whose verdict this driver never writes, gives UNVERIFIED, exit 1. Check 5's MY02 is now M358, and a companion M359 covers the unreadable branch.

**Other test changes:**
- finish_entry_only_error: the "no results.error.json" attack now also removes the copy.
- grade_dir_planted_stop_and_deleted_leg: a planted ABORT.txt beside a PASS entry now expects the contradiction (exit 1). With no ledger given, it expects ABORTED.
- M217 and M290 have new anchors.
- One docstring check in bounds_needles now uses the new exit-1 wording.

### Checks on the final bytes

- **unittest, worktree:** Ran 613 tests, OK, exit 0.
- **unittest, fake-mgba copy:** Ran 613 tests, OK, exit 0.
- **External runner** (a c5fix copy, with C5Tests added to its class list):
  - control: ran 257, failed none;
  - 353 of 353 mutants killed, none survived;
  - M280 is killed by C5Tests.test_guard_sigint_restored.
- **The seven gates:** check_purity, check_fairness, call_census, check_paths, check_grader_imports, ledger --check and extract_milestones --verify all PASS.
- **Check 5's probes, re-run:**

| Probe | Before | Now |
|---|---|---|
| DR attack | exit 0 | exit 1 |
| probe5c FAULT | printed command refused (exit 2); entry stayed 'started' | printed command runs (exit 0); entry 'done' |
| AB, planted ABORT.txt | exit 3 | exit 1 (contradiction) |
| AB, planted results.error.json | exit 4 | exit 1 (contradiction) |
| SIG | real code restores the sentinel; M280 leaves SIG_IGN | the same, now pinned by a test |
| probe5d | real exit 1; MY02 exit 0 | the same, now pinned (M358) |

- **Real re-grades:** R0 exit 0, R0b 0, R1 1, R2 0 (unconfirmed), V1 1. These are the same as round 4, and the ledger is unchanged.

### Notes

- **A second set of full runs.** The first set of final runs failed two tests: a docstring check caught my wording change. I stopped the mutant runner, fixed the test, and ran both suites and the runner once more. The first logs are kept as `*.first-run.log`.
- **Next steps:** commit the two files on wip/live-chain-c2, have an independent check of this diff, and register the new numbers sha256 before the graded run.

## 13. Check 6 (one checker, the round-5 diff, 2026-11-06)

**Verdict: FAIL.** The round-5 diff has one MAJOR regression (C6-02). It is small to fix, but it will turn the real honest folder R2 from PASS into FAIL as soon as the next live_chain entry is registered, and registering one is the next planned step.

All five of check 5's findings are closed by their own probes. Honest batches are unaffected:
- 6 of 6, and 5 of 6 with the miss at L1, L3 or L5: in-run exit 0 and grade DIR exit 0, the same verdict both ways.
- An ERROR at every stage (the chains, grading, the evidence, results.json, the ledger with the ERROR written, an unwritable ledger followed by finish-entry), a development ERROR and an honest ABORTED batch: the same exits as cd11bde4's code. The contradiction and MISMATCH words do not appear in any of them.

**What I worked on.** A copy of lc-c2's working tree in check6/repo, the same bytes as the builder's: live_chain.py fbe3b711..., test_live_chain.py eb0551c5.... cd11bde4's live_chain.py was taken with `git show` for comparison. No ledger was written except temporary copies. No emulator was used. The worktree is unchanged: HEAD is cd11bde4, with the same two modified files.

### Check 5's findings, re-run

| Finding | Probe line now | Status |
|---|---|---|
| C5-01 | DR 'ATTACK ... grade DIR exit 1', NUMBERS MISMATCH (own jobs, and the entry the recorded id names) | closed for its attack; the class is still open: C6-01 |
| C5-02 | probe5c FAULT: 'the printed command, run: exit 0; FINISHED ... GRADED, ERROR (harness: LedgerUnwritten ...)', 'the entry now: done' | closed |
| C5-03 | AB: a planted ABORT.txt or results.error.json gives 'GRADED: FAIL (the folder contradicts its finished ledger entry); exit 1' | closed |
| C5-04 | SIG: real code 'the sentinel (restored)', M280 'SIG_IGN'; the full runner: 'M280_sigint_not_restored: exit 1 ... [C5Tests.test_guard_sigint_restored]' | closed |
| C5-05 | probe5d: real 'exit 1 ... UNVERIFIED (its ledger entry was never begun)', MY02 'exit 0'; now pinned as M358 | closed |

Real folders against the copy's ledger: R0 exit 0, R0b 0, R1 1, R2 0 and V1 1, the same as round 4. The ledger was unchanged.

### Findings

- **C6-02 (MAJOR, a regression).**
  - R2's results.json names ledger #100. The worktree's ledger has 99 entries, and new ids are max+1.
  - With a temp ledger copy that also holds a live_chain registration as #100, R2 gives 'DEVELOPMENT, not graded (unconfirmed: no ledger entry): FAIL; exit 1' and 'MISMATCH: results.json names ledger entry #100, a live_chain entry for seeds [6201, 6206], not the folder's [6050, 6052]'.
  - cd11bde4's code gives exit 0 on the same ledger. With #100 as another driver's entry, the result is exit 0.
  - The general case: an honest development batch graded against a ledger whose recorded id is another live_chain batch gives FAIL (R4 gave PASS). This breaks the docstring's 'a ledger that is not the one it ran with ... by its re-grade'.
  - Fix: count only a named entry whose seeds overlap the folder's job seeds, or use C6-01's unified fix.
- **C6-01 (MINOR, the C5-01 class).**
  - The attack is five edits to results.json: seeds as strings ["6201", "6206"], a recorded id that names no entry, the numbers deleted, purpose development, reach_min 0. The result is grade DIR exit 0, 'DEVELOPMENT, not graded ... PASS', while the ledger says FAIL. With the numbers kept and their sha recomputed, the result is also exit 0.
  - The cause: find_entry compares the seeds as lists, while the jobs check int()s them.
  - Controls exit 1: int seeds, the id kept, and a graded label.
  - Fix: take the folder's seed range from its jobs' int seeds (type-strict), and require 'seeds' to equal it exactly.
- **C6-03 (NIT).**
  - Cutting the renumbered exemption at regrade_dir's call site (mutant MZ2) survives the full runner.
  - On a merged ledger it is not equivalent: the real code exits 0 and the mutant exits 1 with MISMATCH.
- **C6-04 (NIT).**
  - Mutant MZ1 says the contradiction for honest ERROR, ABORTED or STARTED batches. Mutant MZ3 drops the reason from the verdict line. Both survive the full runner.
  - Under MZ1 the honest batches print 'THE FOLDER CONTRADICTS ITS LEDGER ENTRY ... (edited after the run?)', and their exit codes do not change.
  - The CONTROLS that the test docstring claims assert only exit codes.

### Mutants (check6/mut6.py, the real runner's way, all 30 classes)

- Control: ran 257, none failed.
- M280: killed.
- MZ4 (finish-entry prefers the copy): killed by finish_entry_only_error.
- MZ1, MZ2 and MZ3 survived. probe6b shows that none of them is equivalent.

### Out of this check's scope

finish-entry can finish ANOTHER driver's 'started' entry with a live_chain ERROR line, from a crafted folder (probe6 FOREIGN). A 'done' entry is refused. cd11bde4 behaves the same through results.error.json, so this is not a round-5 regression, and the verdict written is always ERROR.

### Next steps

1. Fix C6-02 and C6-01 in live_chain.py. This changes the numbers sha256.
2. Add the FAULT and CONTROL cases, and the pins for C6-03 and C6-04.
3. Re-check.
4. Only then register. Until C6-02 is fixed, registering #100 flips R2.

Evidence is in check6/logs: probe5*.log, probe6_seedstr.log, probe6_r2_err.log, probe6_other.log, mut6.log and probe6b.log. Progress is in check6/STATE.md.

## 14. The sixth fix round (the builder, 2026-11-06)

**Result.** Check 6's four findings are fixed: C6-02 (MAJOR), C6-01 (MINOR), and C6-03 and C6-04 (NIT).
- Each new guard has a FAULT test and a CONTROL, and has mutants in test_live_chain.MUTANTS (M360 to M372, 366 in all).
- The real runner kills every mutant: 'CONTROL M00: ran 259, failed none'; 'MUTANTS: 366 of 366 killed by the real runner; survived: none'.
- Nothing is committed: the worktree lc-c2 has the two files modified on top of 91d97c15.

### What changed in live_chain.py

There are two new helpers, and the lookup now starts from the rows:
- **seed_pair(value)**: two seeds that are `type(seed) is int`, first to last, and nothing else. "6201", 6201.0 and true never count.
- **job_seed_range(jobs)**: the range the folder's ROWS bind. That is the seeds of the jobs whose rows grade DIR counts: ints, one per seed, contiguous.
- **regrade_dir** looks up the ledger entry by that range, not by the seeds results.json records.
- **numbers_jobs_problems** no longer int()s anything. The recorded seeds must be two ints and must equal the jobs' range, else MISMATCH.
- **verify_numbers** requires results.json's seeds to be two ints exactly equal to the numbers' seeds.
- **recorded_problems** has one new rule (C6-02): a live_chain entry whose seeds never meet the folder's range belongs to another batch, so it gives no MISMATCH.

The bounds text is unchanged ('BOUNDS TEXT sha256 505d746d...'). The numbers sha256 moved, as expected, to **31f5ac0e983b09326cfa0ed5ba9e92ef4d01628f5215d32c3e22897325ccc90a**. The graded registration must use this value.

### The findings

| Finding | Fix | FAULT test, now | Mutants (real runner) |
|---|---|---|---|
| C6-02 MAJOR | lookup by the jobs' range; ignore another batch's entry whose seeds never meet it | an honest development batch against a ledger whose recorded #1 is the next graded registration (6201-6206) or a development begin: exit 0, PASS, no MISMATCH (round 5: FAIL) | M366, M367, M368, M369, M360 killed |
| C6-01 MINOR | the type-strict seed rules | SEEDSTR, numbers deleted and numbers kept: 'MISMATCH ... are not two int seeds', 'GRADED: FAIL; exit 1' (round 5: exit 0); floats: MISMATCH | M360 to M365 killed |
| C6-03 NIT | test only | merged ledger: own entry renumbered #2, recorded #1 another live_chain batch that MEETS its seeds: exit 0, 'entry #2 (results.json names #1 ...)' | M370 (check 6's MZ2) killed |
| C6-04 NIT | test only | no_contradiction on honest ERROR (finished and 'started'), ABORTED and development ERROR batches; the verdict line carries the contradiction reason | M371 (MZ1) and M372 (MZ3) killed |

The CONTROLS:
- Check 5's attack (jobs 6201-6206, seeds 9001-9006) still gives exit 1, now labelled GRADED: FAIL, because entry #1 is found by the jobs.
- With int seeds and the id changed, there is no MISMATCH and the ledger's GRADED: FAIL.
- An entry that meets the folder's seeds and differs is still a MISMATCH, and an entry touching at one seed counts as meeting.

### The real scenario (read only)

| Ledger | R0 | R0b | R1 | R2 | V1 |
|---|---|---|---|---|---|
| (a) the worktree's (99 entries) | 0 | 0 | 1 | 0 (no entry, PASS) | 1 |
| (b) a copy of wf_213590e7's (100) | 0 | 0 | 1 | 0 (its #100 found) | 1 |
| (c) (b) + #101 graded registration 6201-6206 | 0 | 0 | 1 | 0 | 1 |
| (d) extra: (a) + #100 the same registration | 0 | 0 | 1 | 0 | 1 |

- 'RESULT: every exit as expected'.
- The folders and both real ledgers are unchanged.
- V1 is in chainheld/verify/out-V1, not livechain/out.

### Checks on the final bytes

- **Suites:** in the worktree, 'Ran 628 tests in 480.196s OK'. In a copy with a fake mgba, 'Ran 628 tests in 481.834s OK'.
- **Probes:**
  - probe6 SEEDSTR: both attacks give 'grade DIR exit 1'.
  - probe6 R2NEXT: R2 gives exit 0 with #100 as the next graded registration or as a development begin.
  - probe6 ERRSTAGES: 'R5-only words: none'.
  - probe6b: MZ2 on check 6's non-overlapping merged ledger now exits 0, the same as the real code. The C6-02 rule clears it, so the pin uses an overlapping batch.
- **Gates:** check_purity, check_fairness, call_census, check_paths, check_grader_imports, ledger --check and extract_milestones --verify all PASS, exit 0.

### Not done, and notes

- **Registration:** not made. It must use 31f5ac0e....
- **Next:** re-check this round independently before registering.
- **Outside scope, not fixed:** grade DIR's LEDGER line says 'matched by its seeds and bounds sha256' even when the sha did not match. The verdict is unaffected.
- **Residual:** an overlapping live_chain entry with the folder's own entry absent is still a MISMATCH. This only happens when seeds were spent in two ledgers that were never merged.

Evidence is in c6fix/: STATE.md, logs/final_probe6.log, logs/final_probe6b.log, logs/final_ab6.log, regrade_real.log, gates_final.log, bounds_final.txt, suite_wt.log, suite_mgba_copy.log and mutants_external.log.

## 15. Check 7 (one checker, the round-6 diff, 2026-11-06)

**Verdict: CONDITIONAL PASS.**
- All four of check 6's findings are closed by their own probes.
- The round-6 diff causes no regression. Every honest batch, every real folder and every ERROR or ABORTED stage gets the same exit as under round 5's code, or the corrected one for R2.
- One MINOR gap remains (C7-01). It predates round 6, and it is in the class that C6-01 named.
- **The condition:** decide C7-01 before the graded registration. Fixing it changes live_chain.py, and so the numbers sha256 again.

**What I worked on.**
- A copy of lc-c2's working tree in check7/repo, with the builder's bytes: live_chain.py 3cc63b76... and test_live_chain.py 893b65d1....
- Round 5's live_chain.py, from check6/repo, as live_chain_r5.py. It equals 91d97c15's file apart from line endings.
- No real ledger was written: only temporary copies. No emulator was used.
- The worktree is unchanged: HEAD 91d97c15, the same two modified files with the same sha256. The worktree's and wf_213590e7's ledgers are unchanged as well.

### Check 6's findings, re-run

| Finding | Probe line now (R6 = final code, R5 = round 5) | Status |
|---|---|---|
| C6-01 | SEEDSTR, both attacks: R6 'grade DIR exit 1', 'GRADED: FAIL; exit 1' ('are not two int seeds'); R5 exit 0 | closed (the class is not: C7-01) |
| C6-02 | R2NEXT with #100 a graded registration of 6201-6206: 'R6 R2: exit 0 ... PASS'; R5 exit 1 MISMATCH. OTHERLEDGER: R6 exit 0, R5 exit 1 | closed |
| C6-03 | merged ledger, #1 at 6043-6045: REAL exit 0, M370 exit 1 MISMATCH; at 7001-7003 both exit 0, so the overlapping pin is the right one | closed |
| C6-04 | REAL 'contradiction line: none' on the honest STARTED, ERROR and ABORTED batches; M371 says CONTRADICTS; M372 drops the reason | closed |

The whole module on the final bytes: 'Ran 628 tests in 476.684s' 'OK'. 628 = 259 + 3 + 366 MutantTests, so M360 to M372 are each killed by the cases they name.

`bounds --run ch5` gives 'BOUNDS TEXT sha256 505d746d...' and 'REGISTERED NUMBERS sha256 31f5ac0e983b0932...', the same as the builder's.

### Regression attack on the round-6 diff

- **Honest batches** (probe7 HONEST, R6 beside R5): graded 6 of 6, graded 5 of 6 with the miss at L1, L3 or L5, development 3 of 3 and 2 of 3, and 6-chain development 6 of 6 and 5 of 6.
  - Every one exits 0 in-run and 0 in grade DIR against its own ledger.
  - Each arm also matches R5 with the numbers deleted, and against the worktree's ledger.
  - The changed functions are called only by grade DIR, never in-run.
- **ERROR and ABORTED stages** (probe7 ERRSTAGES): the chains, grading, the evidence, results.json, the ledger with the ERROR written, an unwritable ledger followed by finish-entry, a development ERROR and an honest ABORTED batch. Every exit equals R5's, and every stage shows 'words: none'.
- **The real folders** (probe7 R2NEXT), against each ledger:
  - the worktree's ledger;
  - that ledger plus #100 as a graded registration, as a development begin, or as another driver's entry;
  - a copy of wf_213590e7's ledger (R2 meets its own #100);
  - that copy plus '#101 live_chain GRADED registered 6201-6206 (31f5ac0e)'.

  R0 exits 0, R0b 0, R1 1, R2 0 and V1 1 every time. The folders and both real ledgers are unchanged.
- **Edits of a FAIL folder:**
  - C7-01 (SUBSET): edits to results.json only reach exit 0. R5 gives the same exit.
  - C7-02 (MOVE2): only a rewrite of the whole folder gains from the new never-meet rule. Round 5 also gave exit 0 there once the recorded id was edited.

### Findings

- **C7-01 (MINOR, not a regression).**
  - The edits: trim a graded FAIL folder's jobs in results.json to the contiguous subset without the misses (6205-6206), set seeds [6205, 6206], chains 2, reach_min 2, delete the numbers, set the purpose to development, and set the id to 99999.
  - The result is 'DEVELOPMENT, not graded (unconfirmed: no ledger entry): PASS; exit 0' on R6 and on R5, while the ledger says GRADED, FAIL. The variant with the numbers kept also exits 0.
  - Controls exit 1: the recorded id kept (MISMATCH), the purpose kept graded (UNVERIFIED), and the folder unedited.
  - The cause: an entry is found only when its seeds equal the jobs' range exactly, and the jobs are a results.json field.
  - Fix: when no entry matches exactly, take a live_chain entry whose seeds MEET the jobs' range as the folder's entry, and say MISMATCH. R2 meets nothing, so it keeps exit 0.
  - Rated MINOR like C5-01 and C6-01, because the exit-0 label is never a GRADED label. The task's literal scale would read MAJOR.
- **C7-02 (NIT).**
  - A FAIL folder rewritten throughout (every file name and every seed in its text) to 9001-9006, with the recorded id kept, gives R6 exit 0 and R5 exit 1.
  - With the id edited, both exit 0, so round 6 adds no new capability.
  - This is C6-02's accepted trade-off. A docstring line could say so.
- **C7-03 (NIT).**
  - My four mutants survive the real runner. The control ran 259 tests, none failed; 0 of 4 mutants were killed.
  - None is equivalent:
    - MX1 (the lookup range taken from results.json's own jobs, not the numbers' jobs): REAL exits 1 and MX1 exits 0 on a dishonest folder.
    - MX2 (a repeated seed allowed): case_seed_rules' 'a repeat' fixture also leaves a gap, so it never tests a repeat on its own.
    - MX3 (only the first seed compared): exit 0 instead of 1.
    - MX4 (the two-seed guard removed): exit 2 instead of 1.
  - The fix is tests only.

### Notes

- The builder already noted that the LEDGER line says 'matched by its seeds and bounds sha256' whenever the recorded id differs. SEEDSTR's numbers-kept attack shows it beside a sha that did not match. The verdict is unaffected, so I did not raise it as a finding.
- In HONEST, a numbers-less development stub on 6041-6043, graded against the worktree's ledger, meets the real R0 entry for the same seeds and reads confirmed. This is the known residual of seeds spent in two ledgers, and R5 behaves the same.

### Next steps

1. Decide C7-01: fix it, with FAULT cases and mutants, or record it as an accepted residual. A fix moves the numbers sha256, so the registration must wait for it.
2. Add the C7-03 tests. They are tests only.
3. If live_chain.py changes, recompute the registered numbers sha256 and re-check that diff narrowly before registering.

Evidence is in check7/:
- logs/: probe7_subset_move.log, probe7_move2.log, probe7.out, probe7b.out, probe7c.log, mut7.out, suite.log and bounds.txt;
- mut7.json;
- STATE.md (progress).

## 16. The seventh fix round (the builder, 2026-11-06)

**Scope.** Check 7's C7-01 (MINOR), C7-02 (NIT) and C7-03 (NIT), plus round 6's own wording note on the LEDGER line. Only `ai_player/gates/live_chain.py` and `test_live_chain.py` changed, in worktree lc-c2 on top of 08abca66.
- Nothing was committed or staged, and no real ledger was written.
- The final bytes are live_chain.py 3e859409... and test_live_chain.py 4c297596... (CRLF only).

**What changed in the code.**
- **C7-01, how grade DIR finds a folder's ledger entry.**
  - `find_entry` first looks for a live_chain entry whose seeds equal the folder's range, as before.
  - When there is none, it now takes the live_chain entries whose seeds **meet** that range. An entry whose seeds are not ints is skipped instead of crashing. The old preference order picks one.
  - In `regrade_dir`, an entry found this way is the folder's entry: its verdict bounds the result and its purpose sets the label.
  - Grade DIR adds a MISMATCH: "the folder's jobs bind [a, b], not ledger entry #N's [c, d]".
  - When nothing meets the range, grade DIR prints "no live_chain entry names or meets seeds ...".
  - The docstrings now say the JOBS bind the range, not the rows on disk.
- **C7-02, docstring only.** `recorded_problems` now says that the never-meet exemption gives up the recorded id as a tripwire for a folder rewritten wholesale to unspent seeds.
- **Wording.** The LEDGER line now says only what matched: "matched by its seeds" or "by seeds that meet the folder's [a, b]", then "and bounds sha256" or ", not its bounds sha256".
- **The numbers.** The bounds text is unchanged (sha256 505d746d...). The registered numbers sha256 moved to **f2ec69fcdf7b2991...**.

**Tests.**
- A new class, C7Tests, has two cases:
  - `grade_dir_subset_folder`. FAULTS:
    - the four SUBSET variants (numbers deleted or kept, id changed or removed), each now exit 1 'GRADED: FAIL';
    - the subset 6206 alone;
    - a development PASS batch trimmed to 6042-6043, now exit 1.

    CONTROLS:
    - the folder as written;
    - the subset with the id kept;
    - the development batch against its own ledger, exit 0;
    - the same batch against a ledger whose only entry is the adjacent next batch, exit 0.
  - `find_entry_meets`, a unit test of the edges, of exact before meeting, and of another driver's entry or seeds that are not ints.
- `grade_dir_edited_fail_folder` has a new arm (7) for MX1: the top-level jobs trimmed or moved, plus a control. It also has the wording needles.
- `seed_rules` adds:
  - a repeat with no gap;
  - the seeds [6041, 6044] beside jobs 6041-6043;
  - the jobs and the seeds both unreadable with a live_chain id, which must exit 1, not 2.
- MUTANTS adds M373-M384, which include check 7's MX1-MX4. There are now 378.

**Results on the final bytes.**

| Check | Result |
|---|---|
| Suite, worktree | 'Ran 642 tests in 462.426s' 'OK' |
| Suite, copy with fake mgba | 'Ran 642 tests in 466.751s' 'OK' |
| External runner | 'CONTROL M00: ran 261, failed none'; 'MUTANTS: 378 of 378 killed by the real runner; survived: none' |
| probe7 SUBSET | every attack exits 1 GRADED: FAIL (R6 and R5: exit 0) |
| probe7 MOVE2 | same as R6 (the accepted trade-off) |
| probe7 R2NEXT | R0 0, R0b 0, R1 1, R2 0, V1 1 in all six ledgers |
| mut7 (MX1-MX4) | 'MUTANTS: 4 of 4 killed; survived: none' |
| regrade3, arms a-d | 'RESULT: every exit as expected'; the folders and both real ledgers unchanged |
| Gates | all PASS |

**Residuals and next steps.**
- **C7-02 (accepted).** A folder rewritten wholesale to unspent seeds, with its recorded id kept, still exits 0.
- **Several meeting entries.** They can only occur in a merged ledger or for a cross-batch range. The MISMATCH makes the result at least FAIL, but an ERROR or ABORTED on an entry that was not picked is not reported.
- **Honest folders against a foreign ledger.** If another batch's seeds overlap the folder's range there, the folder now reads MISMATCH instead of unconfirmed. This only makes the verdict stricter.
- **Next steps:**
  1. Commit the round.
  2. Run its narrow check (check 8).
  3. Make the graded registration with f2ec69fc....

The evidence is in s53/chainheld/c7fix/: STATE.md, final_checks.out, final_runs.out, gates_final.log, regrade_real.log, mutants_external.log, mutants_external.json, logs/final_probe7*.log, logs/final_ab7*.log and logs/final_mut7.log.

## 17. The lead's re-check, the full lane, and the merge (2026-11-06)

**No eighth checker.** Round 7's diff was narrow (one lookup rule, one docstring, mutant pins), so under the stopping rule the lead re-ran check 7's own probes instead of commissioning a new check.
- A fresh copy of the final tree (16,681 files; `live_chain.py` 3e859409..., `test_live_chain.py` 4c297596..., the same bytes as the worktree's) ran `probe7.py`, `probe7b.py` and `probe7c.py`, byte-identical to check 7's (compared with `cmp`), on the stub rig (temp ledgers only, no emulator, no real ledger written), 52 s each.
- **SUBSET (C7-01):** all three attacks now exit 1, "GRADED: FAIL" (round 5's code beside it: exit 0 in all three). Every control exits 1 in both.
- **MOVE:** every arm exits 1 in both codes.
- **MOVE2 (C7-02):** a FAIL folder deep-moved to the unspent seeds 9001-9006 with its recorded id kept exits 0 on the final code (round 5's: 1). This is the accepted trade-off that `recorded_problems`' docstring states. A deep move that meets entry #1 (6204-6209) still exits 1.
- **R2NEXT (C6-02):** the real rehearsal folders re-grade R0 0, R0b 0, R1 1, R2 0, V1 1, against the worktree's ledger, against that ledger plus the next entries, and against a copy of `wip/live-chain`'s ledger plus a graded registration of 6201-6206.
- **probe7b:** the merged-ledger arm (the folder's own entry renumbered #2): a #1 whose seeds never meet the folder's (7001-7003) exits 0, and one that meets them (6043-6045) exits 1 with "NUMBERS: MISMATCH".
- **probe7c:** beside each of check 7's four mutants, the final code fails every attack and fault (exit 1). MX3's mutant still passes its fault (exit 0) and MX4's still crashes (exit 2, IndexError), as check 7 found. MX1's mutant now exits 1, because round 7's jobs-bind MISMATCH catches the trimmed jobs. Round 7 pinned all four as M381-M384, and the external runner killed them (378 of 378).

**The full regression lane, first run: FAIL (3 of 35 suites, on `59a7d560`, evidence kept in `afcde809`).**
- `test_safety_gates` and `revert_safety_gates`'s S0 control failed in `WiringTests.test_each_driver_calls_its_guards_where_they_belong (driver='live_chain.py')` with "['finish']". That suite keeps a second, shorter wiring list, which still wanted `run_batch` to call `ledger.finish`; round 3 had moved that call into `finish_entry`, which retries it (C3-E03). The seven fix rounds ran `test_live_chain` only.
- `test_kb2` failed because the lane runner, rewritten for this lane, set no `POKEBOT_DECOMP`, and a worktree has no `../_decomp`. The 11-05 lane had set it.
- **The fix (`b0e6c289`):** the list wants `finish_entry` in `run_batch` and `finish` in `finish_entry`. Proof (scratch `wiring_fault.py`): the CONTROL passes, three FAULTS (each call deleted in turn) fail, and the old list reproduces the lane's failure on the current code. The re-run sets `POKEBOT_DECOMP` to the pinned clone (731ad5bf). The case is in `08` (2026-11-06).

**The full regression lane, second run: PASS (`bf36ac8c`).** On HEAD `b0e6c289`: 35 of 35 suites, frozen tree PASS (40 checks of 205 files), 5,274 s.
- Unit suites: `test_live_chain` 642 tests, `test_safety_gates` 50, `test_kb2` 123, `test_goals` 324, `test_check_purity` 30.
- Mutant runners: `revert_step5` 465 mutants, `revert_r1` 566, `revert_safety_gates` 23, `revert_step3` 94, `revert_step4` 62, `revert_step2` 44, `revert_step11` 14.
- The graded and ROM suites are NOT-RUN by design: they run deliberately.
- The runner moved the failed lane's evidence to `ai_player/evidence/archive/53e0c26e7812db47-59a7d560/`. Its content matches `afcde809`'s byte for byte, apart from line endings.

**Merged to `main`** with the docs (`07` 2026-11-06). Next: register seeds 6201-6206 with the numbers sha256 `f2ec69fc...`, commit and push, then the graded run. A miss is never re-run.
