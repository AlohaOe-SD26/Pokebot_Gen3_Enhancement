# `live_chain.py`, the GRADED New Game chain held-out driver: build report (2026-11-05, nothing graded yet)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). It collects the `live-chain-driver` workflow's own
> outputs: the spec (`2026-11-05-LIVE-CHAIN-BUILD-SPEC.md`), an adversarial critic, the builder (worktree
> `wf_213590e7-d34-3`, saved as branch `wip/live-chain`, commit `b4c3e949`) and an independent verifier (CONDITIONAL
> PASS). The driver is on `main` only once `07` records its merge. No graded seed (6201-6206) was registered or run.
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
