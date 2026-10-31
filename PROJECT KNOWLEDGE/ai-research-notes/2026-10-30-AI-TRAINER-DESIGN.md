> **Filed 2026-10-30** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/trainer/SPEC.md` (sha256 `a5d9a6ae1fdb988e`). The AI TRAINER (USER RULING 54, `06` 2026-10-30): the 24/7 learner's machine time trains the AI PLAYER itself. Designed by the read-only workflow `ai-trainer-design` (3 agents, 3.01 Mtok; its row is in `cost-ledger.jsonl`): a designer who first read the learner and the AI player at `b5baea6b`, one adversarial critic (14 findings, 5 MAJOR) and a reviser who checked every finding against the code and the data (its section 7).
> **It is CLAUDE'S DESIGN, NOT BUILT, and like every agent output a NOTE:** each claim about the code is re-checked when its part is built. Its order (section 3, D0 and D10): A0, then A1, then the top blocker's skill build, then the trainer inside the learner (at the weekly reset), then skill builds by the blocker list, then U2b, then Phase B (R12), then Phase C.
> **A0's prediction is REGISTERED by the commit that files this note, before A0 runs** (section 4, A0): the runs end on ROUTE104 at y > 37, with the woods state 1 and the Rustboro flag clear; an arrival on ROUTE104 north at y < 31 refutes it. A0's result goes in `07`, never into this note.
> **P0 (section 4), the disk, is PARTLY answered** by a read-only scan (2026-10-30 5:13 PM): this session's OWN build scratch held about 41 GB by file size, in build-stage copies (the sandbox, the emulator and the run outputs builder agents played in) under the session's temp scratchpad (`s53/u2`, `s53/r1f`, `s53/r1build`). They were deleted at 5:22 PM and free disk rose from 61.4 to 77.4 GB (+16.0 GB), so the rest of that size was shared storage (hard links). Free disk had fallen from 91.4 to 57.8 GB over ai0049-ai0057, so the scratch explains about half. Still in `%TEMP%`: `ai_sweep_*` (7 folders, 4.9 GB), `aiagent-test-*` (7 folders, 3.6 GB; `test_agent.py` runs leave them) and `vrr4frtw` (5.3 GB, not identified).
> **⚠ STALE BELOW, superseded 2026-10-30 6 PM:** (1) section 0's and section 5's "25 GB stop around 2026-11-03" extrapolated that whole drain from about 58 GB free; after the freeing, free disk read 68.5 GB at 6:03 PM (5.7 GB of it in A0's three run folders, KI-129), and the rest of the drain is unidentified, so a session re-measures it (`tools/status.py`) before any batch. P0 gates DEPLOYING the trainer (Phase A), not A1, whose own runs must cap their `world.jsonl` (`04` queue item 4). (2) The week's usage was spent by A0, so the "this week" plans for A1 and the first skill build are superseded by `04`: they come after the weekly usage reset.
> **Its user question (section 6) is ANSWERED, USER RULING 55 (`06` 2026-10-31):** practice runs from the AI's own saves are allowed when they help learning, with practice memory kept apart, and **after a few practice runs the trainer must run a NEW GAME test** to check that the learning connects.

# THE AI TRAINER: design (USER RULING 54), at b5baea6b, revised after the critic

## 0. Summary (plain words first)

**Why the AI has not moved in two weeks.** The AI has never been asked to play chapter 3, not even once. No evidence file names a chapter-3 or chapter-4 goal, and the AI README still says "chapters 3 and 4 are still unplayed". The machine time went to the scripted bot's tuner, and the build time went to grading, saving and tuner housekeeping. A 2026-10-15 recon already predicted what would stop chapter 3, and the top item is still in the code: the AI treats Petalburg Woods as a building instead of a road (`ai_player/brain/goals.py:649`, `:672-719`). The cause was the order of the work, not a shortage of training or hardware.

**What the trainer does.** It points the 24/7 learner's machine time at the AI player itself (ruling 54). It has three parts:
- **It plays real AI games without stopping.** "Chain" games start from a real New Game and go chapter by chapter as far as the AI can. "Frontier" games start from the AI's own saves at the hardest chapter. Every run goes through the real launcher, with the purity check on every launch. Whether a run got through is read from the game itself, never from the AI's own words.
- **It writes a ranked blocker list** after each wave: where and why runs end, each blocker with the saved game where it happened, so a work session can reproduce it in minutes.
- **It keeps the AI's experience.** From every clean run it records what the AI saw and lived: the map links it walked, and the fights it won and lost, with its party. That is the raw material for the AI to "remember past games" (ruling 40), which is what the project means by "trained" (06:9507).

**What nonstop play can and cannot do, said plainly.**
- **The AI player does not change between code versions.** One code version played a thousand times plays the same, so after about 40 runs at a chapter its blocker list stops changing. The trainer therefore spends runs where they still say something new: every new code version, the chapter past the top wall, and personalities and starters that are under-sampled. When nothing new is left, it hands lanes back to the bot at the next cycle.
- **It cannot create a missing skill.** No number of runs makes the AI walk through the woods, play a double battle, or handle an evolution if the code cannot. Those come from skill builds. So the frontier moves at the speed of skill builds, and the trainer makes every build hit the real top blocker and get proven at volume.
- **So a fix must reach training fast.** The trainer runs the AI from its own code checkout, fast-forwarded within an hour of a push, instead of waiting up to 12 hours for the learner's cycle boundary.
- **The experience record becomes AI learning only when the AI reads it.** That reader is a skill build (the "past games" slice), and it is ordered by the blocker list like any other.

**Realistic pace (estimates; budget figures from `cost-ledger.jsonl`).**
- **Compute is not the limit.** At about 600 frames/s (measured), a chapter 1-2 leg takes 2.3-4.6 minutes. Eight AI lanes measure a new code version at one chapter (about 40 runs) in roughly 2-3 hours.
- **Budget is the limit.** The week was at 79% at 15:03 UTC today, which leaves roughly 50-65 Mtok until the next reset (inferred as about 2026-11-04). A whole item (spec, build, verify, fix) has cost 30-90 Mtok. Badge 1 (chapters 3-4) likely needs 4-6 items, or 120-540 Mtok, which is about 0.3-1.3 weeks of budget **counted from the reset**.
- That is why the order below spends this week's remainder on the measured top blocker, not on infrastructure.

**Order:**
1. **A0, today:** a no-code probe of chapter 3 from the AI's three chapter-2 saves (about 1-2 Mtok).
2. **A1, this week:** the wide probe. A parallel launcher driver, `ai_player/gates/frontier_probe.py`, runs about 24 chapter-3 runs and 12 New Game chains in about an hour. It gives the real blocker shares. It is ALSO the trainer's runner core, so nothing is built twice (about 8-15 Mtok).
3. **The first skill build:** at the top blocker A1 measures. It is predicted to be loader slice 1 (map connections from `maps.json`), the woods fix, with the recon's P5 A/B. It starts this week if the budget allows and otherwise at the reset.
4. **Phase A, at the reset:** the learner-integrated trainer, which runs nonstop, with the blocker list, the experience record and the fast code checkout.
5. **Next:** skill builds in the blocker list's order, then U2b, then Phase B (the AI's settings registry, R12, and tuning), then Phase C (the curriculum, the rest of the loader, milestones past chapter 4).

**One thing to fix whatever happens: disk.** Free disk is falling about 4 GB per cycle from something OUTSIDE the learner (the learner's own use is flat at about 10 GB). At that rate the learner stops itself at the 25 GB floor around 2026-11-03, and that stops the bot too. A session must find the source before Phase A deploys (see P0).

## 1. Recon (cited, b5baea6b unless noted)

- **The learner runs only the BOT.**
  - `plan_cycle` (`ai-agent/learner.py:956-983`) chooses bot genomes.
  - `batch_command` (`:986-989`) runs `tools/story-dev/x4_headless.py --build sandbox`.
  - `run_cycle`/`_run_batch` (`:992-1037`) wait out the 720-minute cycle.
  - `finish_cycle` (`:1040-1106`) parses the bot logs (`scoring.py:24-46`), then reports, consults, prunes and writes the ops row.
  - Nothing in `ai-agent/` launches `ai_player`. The learner imports only its own modules (`:83-87`).
- **Lanes.**
  - `size_lanes` (`:593-603`) takes the smallest of the cap, the CPU (threads − 4 − singles) and the RAM, rounded down to a multiple of 4.
  - The learner waits below 8 lanes (about `:2123`), so a 4-lane bot share needs that guard changed.
  - Any `pokebot.py` without `--endless-target` counts as a "single" (`:574-584`). That includes the AI launcher's child.
- **Deployment.**
  - The learner fast-forwards its clone between cycles (`update_checkout`, `:447-462`). It skips forever if the clone has a tracked change (`:452-453`).
  - It restarts into new learner code only if `test_agent.py` passes (600 s limit, `:465-470`).
  - `code_signature` covers only `ai-agent/*.py` (`:426-431`). So an `ai_player`-only push never runs `test_agent.py` before the long-lived learner uses it.
- **Clone status.** The clone is current at b5baea6b and running ai0058, started 4:34:56 PM with 12 lanes. The next boundary is about 4:35 AM on 2026-10-31.
- **What stops the WHOLE learner, bot included.** `ATTENTION.md` stops every cycle. It is written by a crash loop (`:2026-2033`), by fetched code that fails its tests (`:2058-2062`), and by `disk_guard` under `min_free_gb` 25 (`:1875-1897`).
- **Disk.**
  - Archive and delete touch only `runs/<tag>/batch` and `endless-<tag>-*` (`_ours`, `:1379-1385`), and `learner_gb` counts only `runs/` + `endless-ai*` (`:826-829`). **AI run folders are covered by NEITHER.**
  - **Measured trend (clone `data/ops.jsonl`):** free disk fell from 91.4 GB (end of ai0049) to 57.8 GB (end of ai0057) while `learner_gb` stayed at 9.2-10.1 GB. The source is not located: the main checkout's profiles hold 8.1 GB, and `%TEMP%` could not be sized within 60 s.
- **The bot's freeze watch** aborts a cycle on a new untracked file in its scope (`x4_headless.py:928-941`, `git status --porcelain --untracked-files=all`). AI profiles live under `sandbox-pokebot/profiles/*`, which is git-ignored (`sandbox-pokebot/.gitignore:12`; `git check-ignore` passes for `ai-train-*`).
- **Machine (measured 2026-10-30).** 32 threads and 128 GB RAM. 12 bot lanes average 43-50% CPU. The bot ranking has plateaued (0.376-0.400 ± 0.016-0.039).
- **Launching the AI.**
  - `ai_player/__main__.py:59-82,140-243`: the purity gate runs on every launch (exit 7), and the run must get a CLEAN verdict (`purity.json`) or exit 8.
  - `_report_verdict` returns the child's code whenever it is non-zero (`:116-117`). So a CLEAN budget end exits 4 (frame budget) or 124 (wall clock) (`launcher.py:275-276`). The end classes are listed at `launcher.py:270`.
  - `--state` archives the old memory and copies the start into `current_state.ss1` (`launcher.py:192-254`).
  - `--continue` after a `play: done:` end is a CHOSEN end and is refused unless that end was at a save (`launcher.py:257-290`).
  - The brain is chosen by environment variables: TARGET, STARTER, PERSONALITY, SEED, WORLD (`options.py:187,224-231`). There is no command line that lists the switches.
- **Profile donor.** `ensure_profile` copies `metadata.yml` from `endless-P1-torchic` (`launcher.py:102,158-186`). It exists in the clone, but `profiles/*` is ignored, so a FRESH checkout has no donor.
- **The reusable pattern** is `gates/live_step5.py:435-509`:
  - launch, copy the state, run `hands_harness truth`, and carry `world.jsonl` into the next leg with `--state` + `AI_PLAYER_WORLD`;
  - arms get 330,000 frames / 3,600 s (`:413-430`);
  - **the state-freshness check**, `check_after_is_this_run` (L5.THIS_RUN, `:524-536`), proves the graded state is the one THIS run wrote;
  - every live run is "a NEW trajectory on the host's clock" (`:405-410`).
  - `rate_step5.run_chain` (`:770-783`) chains legs in-process. `play_harness` can pin the clock (`--game-clock`) and can save checkpoints (`:379-381`), but gives no purity verdict.
- **Speed (measured).** The 6 live arms of 2026-10-30 ran 82,822-178,222 frames in 140-275 s (582-649 frames/s) beside 12 bot lanes. A run folder is 7-9 MB raw (of which `world.jsonl` is 7.0 MB) and about 1.1 MB zipped (about 8:1).
- **Milestones** stop at `ch4_roxanne`. The chapter packs and `campaign.json` cover all 24 chapters.
- **Seed ledger.**
  - `ledger.json` is TRACKED. `register` refuses a graded range that overlaps ANY entry of the same family (`ledger.py:116-129`).
  - `begin` refuses a development run on registered, unplayed graded seeds (`:180-184`). Graded AI sweeps use the family `story` (`rate_step5.py:155`).
- **Gap-1 code.** `OUTDOOR` (`goals.py:649`). `lead_toward` offers only outdoor maps (`:672-704`). `keeps_going` refuses a "back" target into a non-outdoor map (`:711-719`).
- **World memory** (`world/memory.py`) holds tiles, warps, connections, edges and bumps (static), plus items and people seen, visits, "news" and closed doors (per game).
- **Backlog items** (`2026-10-18-improvement-backlog.md`): R12 `:349-352`; A6 `:91-96`; R8+R9 `:312-316`; R6 `:286`; R7 `:353`; R11 `:347`; D1 `:155`; D2 `:162`; R13 inside B1 (`:212`). Bot saves as AI starts were REJECTED (P13, `:365`).
- **About 207** module-level UPPER_CASE constants sit in `mode.py`, `personality.py`, `brain/*` and `skills/*`. Examples: `STORY_PATIENCE 120_000` and `MAX_LOSSES 3` (`mode.py:110-111`), and `GO_FRAMES 9000` (`goals.py:257`).
- **Budget.** The week was at 79% (337 Mtok) at 15:03 UTC on 2026-10-30. The last reset was 2026-10-28, so the next is inferred as about 2026-11-04. Whole items so far: r1f 31.6, U2a 42.1, r1r2 87.8 Mtok.

## 2. Why the frontier is stuck

1. **It was never tried (measured).** There have been zero chapter-3/4 launches.
2. **The predicted run-stopper is still in the code (static, UNVERIFIED live).**
   - Recon gap 1: `OUTDOOR` leaves out PETALBURG_WOODS. `lead_toward`/`keeps_going` then send the AI back south and refuse the woods.
   - Expected end: `stuck: no progress…` on ROUTE104 south, with `PETALBURG_WOODS_STATE=1` and `FLAG_VISITED_RUSTBORO_CITY` clear.
   - Discriminator (00-RECON-NOTE.md:615): the arrival y on ROUTE104 is over 37 (south) rather than under 31 (north).
3. **What chapters 3-4 need that the AI lacks (static):**
   - the woods as a passage, and region-aware routing (gap 1);
   - a run that survives losing to ROXANNE: losses counted per fight, and training after a loss (gap 2, R11);
   - a first live evolution and move-learn (gap 3);
   - a way out of the trader's party menu, or of any unknown screen (gap 5, R6);
   - double battles: the Route 104 twins and the gym's double (gap 6). `_fight_double` is defined at `battle.py:1099` and has never been played live;
   - go-goal budgets sized for chapters 1-2 (gap 7, `GO_FRAMES 9000`);
   - memory carried across legs (gap 9; the chain method covers it).
4. **The fix for gap 1 has changed.** Ruling 40 allows static map knowledge. `knowledge/world/maps.json` (518 maps) knows that the woods join Route 104's two halves, but no loader reads it yet.
   - **Experience cannot make the FIRST crossing.** No run crosses the woods while `keeps_going` refuses them, so no past game remembers the crossing.
   - So gap 1 is a loader or code fix. Experience then makes any later success compound.

## 3. Decisions (each with what it rejects)

- **D0. Measure first, build infrastructure second.** A0 (no code), then A1 (the wide probe driver, which becomes the trainer's runner core), then the top blocker's skill build, then the learner-integrated trainer (Phase A) at the reset.
  - *Rejected:* building Phase A before any chapter-3 data while about 50-65 Mtok remain this week. It would spend the week on plumbing while the top blocker is already predicted and cheap to confirm.
  - This is Claude's sequencing call under ruling 54, which asked for progress first. The trainer is still built: it is moved behind one measurement and one fix, not dropped.
- **D1. The trainer is part of the existing learner process and cycle.** One lock, one watchdog, one park tool.
  - **It runs the AI from its own code checkout:** `C:/Remote Projects/pokebot-ai-code`, a plain clone of origin, set up once by a session.
    - About once an hour the learner fast-forwards it, but only when `origin/main` changed `ai_player/`.
    - It first drains: no new AI runs start, and it waits for the running ones to finish, because Python imports some modules lazily and a run must not mix code versions.
    - It then fast-forwards (ff-only, skipped if there are tracked changes) and starts the next wave on the new tree.
  - **Why:** a fix reaches training in about 1 hour instead of up to 12 (critic F1).
  - **Fallback:** if that checkout is missing or its update fails, AI runs use the deployment clone, and the tree digest is recorded either way.
  - *Rejected:* a second learner process or scheduled task, which needs new watchdog, backup and park paths. *Rejected:* running the AI only from the deployment clone (12-hour fix latency). *Rejected:* fast-forwarding while runs are live (mixed code versions).
- **D2. Every trainer run uses the real launcher.** The purity gate runs on every launch, and the run must get a CLEAN verdict. Anything else is counted as impure and left out.
  - *Rejected:* `play_harness` as the engine, because it gives no purity verdict.
- **D3. Starts are made by the AI only.**
  - Chain games build the pool from a real New Game. Each pool state carries its provenance: the tree digest, the seed, the chain id, and the game's marks.
  - Bot saves and fixtures are refused (P13; ruling 35).
  - *Rejected:* committing fixture states.
- **D4. Whether a run got through is read from the game,** with `hands_harness truth` on an end state that passed the freshness check (D14). The AI's `done:` text is kept only as a cross-check.
  - **The official frontier counts only real New Game chains.** The trainer writes `findings/AI-FRONTIER-CANDIDATE.md`. `ai-frontier.txt` moves only after a session's registered, held-out, graded proof.
  - *Rejected:* the trainer moving the frontier itself.
- **D5. Lanes: the AI first, the bot keeps what is left (ruling 54). The total stays at 12 in Phase A (ruling 38).**
  - Ruling 38's trigger for 16 lanes is "a knob or strategy of the AI's that the screen can measure", which is Phase B's knobs.
  - **Phase A:** canary cycle AI 4 + bot 8; then AI 8 + bot 4 (one bot strategy a cycle). The joint sizing replaces the bot's 8-lane minimum with 4 for the bot's share.
  - **At each cycle boundary the split is re-derived from need (D15):** if the AI's current tree is saturated and no `ai_player` push arrived, the next cycle gives the bot 8 and the AI 4.
  - **Phase B:** 16 in total (ruling 38's trigger), with the AI share sized by the arm plan.
  - *Rejected:* 16 now (it stretches ruling 38's trigger). *Rejected:* all 12 on the AI (the bot's corpus is the AI's teacher data, ruling 41, and the AI cannot use the volume yet, critic F1). *Rejected:* asking the user (ruling 54 already settled it, CLAUDE.md rule 11).
- **D6. No AI consult in Phase A.** Sessions read the blocker list through `tools/status.py`, at no Claude cost. In Phase B an AI consult may share the existing cap of 2 a day.
- **D7. The blocker key** is (chapter, the next milestone the game says is unmet, the AI's end reason with numbers stripped, the end map, the end class). Blockers are ranked by share of the CLEAN AI ends at that chapter on the current tree, with the frame distribution and 3 example runs kept raw.
  - *Rejected:* ranking by the AI's text alone (B1), or by frames.
- **D8. Phase B tunes only COMPETENCE settings that are not budgets.** The score is progress at the frontier as read from the game, with no frames term (rulings 41 and 32).
  - **Budget or patience settings** (for example `STORY_PATIENCE`, `GO_FRAMES`) are classed `budget` and are not tunable: raising them can only add reach, so a progress-only score would push them to the top of their range (critic F10).
  - A setting that wins only at its range edge is reported, never proposed (registered before the runs).
  - Person-likeness is a held-out grader, used at promotion only. The learner proposes, and a session commits after a registered held-out sweep.
  - *Rejected:* tuning taste settings. *Rejected:* putting person-likeness inside the ranking (Goodhart).
- **D9. The loader and the experience reader are ordered by data.**
  - Loader slice 1 (map connections from `maps.json` turned into passages) is the predicted first build, if A0/A1 confirm gap 1.
  - The "past games" slice (D16) and the loader's other slices come in the blocker list's order.
  - *Rejected:* the whole loader strictly after Phase B.
- **D10. Sequencing:** A0 → A1 → the top-blocker skill build → Phase A (at the reset) → skill builds by the blocker list → U2b → Phase B → Phase C. U2b improves long sessions but does not move the frontier.
  - *Rejected:* U2b before the first blocker fix.
- **D11. Disk: the AI store has its own retention and its own floor (critic F5).**
  - Every finished run folder is zipped and verified (O3's `verify_archive`), and only then is the raw copy deleted (about 1.1 MB per run zipped).
  - Raw copies are kept only for pool states (at most 50 per chapter) and examples (3 per blocker per tree).
  - Zips are kept per (tree, chapter) up to 200, plus all examples, under a total cap of 10 GB. The oldest tree's surplus is deleted first.
  - **An AI-only floor of 45 GB free** (above 25 + 15) stops the AI lanes FIRST and writes `findings/AI-ATTENTION.md`, never `ATTENTION.md`.
  - The AI folders are counted in `learner_gb` and in the ops row. Records go to a NEW `data/ai_runs.jsonl` (with `schema_version`); the bot's `runs.jsonl` and the consult digest never see AI rows.
  - *Rejected:* relying on `disk_guard`/`early_archive`, which cannot see AI folders. *Rejected:* keeping raw folders.
- **D12. Chapter starts** use live_step5's method: `--state end_state` + `AI_PLAYER_WORLD`. R2's `memory.jsonl` is archived per leg.
  - *Rejected:* `--continue` across chapters now (a `done` end is refused unless it was at a save). Long continued games come in Phase C.
- **D13. Seeds** come from a trainer band, 2,000,000-2,999,999.
  - Before deploying, a session commits ONE ledger row: family `story`, purpose `development`, status `done`, note "AI trainer band". `register` already refuses any graded range that overlaps a same-family entry (`ledger.py:126-129`), so no `ledger.py` change is needed.
  - Phase A tests a FAULT (a graded registration inside the band is refused) and a CONTROL (outside the band, it is accepted).
  - **The trainer never writes `ledger.json`** (it is tracked: one write would block every later fast-forward). At each cycle start it checks that the reserving row exists and that no registered range overlaps the band; if either fails, the AI lanes do not run.
  - *Rejected:* a check-only band (critic F11). *Rejected:* `ledger.begin` per run.
- **D14. A run's end is judged from its FILES, never from an exit code (critics F8, F9).**
  - Freshness is ported from L5.THIS_RUN: the end state was written after the start, frame == start + real_frames ± slack, and its md5 differs from the start.
  - The classes:
    - REFUSED: launcher exit 7/2, or a missing verdict;
    - NOT CLEAN;
    - INFRA: CLEAN but the state is not fresh;
    - CLEAN-CHOSEN;
    - CLEAN-BUDGET.
  - Only REFUSED and NOT CLEAN count toward the AI-only stop. INFRA is counted but kept out of the blockers and the pool. Both CLEAN classes feed the blockers.
- **D15. Spend runs by information, not by hardware (critic F1).**
  - Each free lane takes the first job that still says something new:
    1. the current tree's frontier chapter, until it has 40 CLEAN ends (blocker shares ±16 points at 95%);
    2. New Game chains on the current tree, until 12 have run (the CONTROL that chapters 1-2 did not regress, and the official count);
    3. depth: runs from any pool state PAST the top blocker (chapter k+1), so the next wall is measured before the current one is fixed;
    4. the personality × starter pairs with the fewest CLEAN runs on this tree;
    5. otherwise the lane idles and the cycle is marked "AI saturated on tree X".
  - **The output metric is "CLEAN runs on trees and chapters not yet measured", not runs per hour.**
  - *Rejected:* filling every lane all cycle on one tree (about 1,200 runs that say what the first 40 said).
- **D16. The AI's own experience is recorded from day one (critic F2, partly applied).**
  - From every CLEAN run, `data/ai_experience.jsonl` gets:
    - the static map facts the AI saw: warp links, connections with offsets, edges, and tiles;
    - every trainer or boss fight: the foe as shown on screen, the AI's party levels and species, and the outcome;
    - the end map and the end class.
  - Per-game facts (items and people seen, visits, "news", closed doors) are never kept.
  - The AI reads it only through the "past games" slice, a skill build with its own `KNOWLEDGE_FIELDS` classification (static knowledge only, ruling 40), purity and fairness coverage, a FAULT (memory off) and a CONTROL.
  - *Rejected (part of F2):* the experience memory as the gap-1 fix (it cannot make the first crossing, §2.4). *Rejected:* feeding a raw `world.jsonl` from another game in through `AI_PLAYER_WORLD` (it carries per-game facts).
- **D17. The learner never imports `ai_player` (critic F4).**
  - The trainer runs `frontier_probe` as a SUBPROCESS from the AI code checkout and reads its JSON record, the verdict file and the launcher's lines.
  - **The child environment is built from an ALLOW-LIST:**
    - the parent environment minus every `AI_PLAYER_*`, `POKEBOT_*` and `PYTHONPATH`;
    - plus only TARGET, STARTER, PERSONALITY, SEED, WORLD, CLOCK and MEMORY.
    - A FAULT or CONTROL switch added later can never leak in, because the list does not name it.
  - `test_agent.py` checks with the AST that no file in `ai-agent/` imports `ai_player`.
  - *Rejected:* in-process imports. They would bypass the restart rule, and a broken `ai_player` push could crash the learner into `ATTENTION`, stopping the bot.

## 4. Phases

### P0: before anything is deployed (a session task, about 1-2 Mtok)
- **Find what is eating about 4 GB of disk a cycle outside the learner,** and fix or report it. The suspects are `%TEMP%` (regression lanes and scratch), the main checkout's profiles and evidence, and anything else writing to C:.
- **Why:** at this rate the 25 GB floor stops the learner, bot included, around 2026-11-03. Ruling 50 forbids parking on Claude's own, so the space must come back.

### A0: a no-code chapter-3 probe (today, about 1-2 Mtok)
- **Starts:** three launcher runs from the AI's own chapter-2 ends: `sandbox-pokebot/profiles/ai-step5-play/ai_player_runs/20261030-{135558-CH2,135912-CH2T,140134-CH2M}/end_state.ss1` + `world.jsonl`.
- **Command:** `py -3.12 -m ai_player run --profile ai-ch3-probe-N --frames 600000 --wall-seconds 3600 --state <end_state>`, with `AI_PLAYER_BRAIN=play AI_PLAYER_TARGET=ch3_rustboro AI_PLAYER_WORLD=<world.jsonl>` and an unregistered seed.
- **Grading:** `hands_harness truth`, read only after the L5.THIS_RUN-style freshness check.
- **Prediction, registered before the runs:** recon gap 1. The run ends on ROUTE104 at y > 37, with woods state 1 and the Rustboro flag clear.
- **CONTROL:** the arrival on ROUTE104 north at y < 31 would refute it.

### A1: the wide probe and the trainer's runner core (this week, about 8-15 Mtok)
- **New file: `ai_player/gates/frontier_probe.py`** (test side; the AI never imports it). It takes a list of jobs, runs launcher legs in parallel and appends one JSON record per run.
  - **A job** is fresh or start state, target, personality, starter, seed and budget.
  - **Per run it does:** a disposable profile with an explicit `--template`; truth before; a launch exactly as `live_step5.run_arm`; the D14 freshness check and classification; truth after; the blocker key (D7); the D16 experience extract; then zip and verify.
  - **Modes:** `--ledger development`, which writes the ledger, for sessions in the main checkout. `--trainer` NEVER writes a tracked file, and its tests prove it.
  - **The record** has a `schema_version`.
- **The run:** in the main checkout, with 8 parallel workers beside the bot: 24 chapter-3 runs (3 chapter-2 ends × personalities × seeds) plus 12 New Game chains to chapter 2. That is about 1 hour of wall time.
- **Tests (offline):** each guard below has a FAULT and a CONTROL:
  - freshness: a seed-copy end state counts as INFRA;
  - classification: a CLEAN budget end (exit 4 or 124) is not REFUSED;
  - the env allow-list: an injected `AI_PLAYER_FAULT_*` never reaches the child;
  - `--trainer` writes no tracked file;
  - the blocker key: the same reason with different numbers falls into one cluster, and a different next milestone gives two;
  - the experience filter: a per-game field, such as items seen, never reaches the extract.
- **Proof:**
  - **CONTROL:** chapters 1-2 reached at the live arms' rate (3 of 3 on 2026-10-30).
  - **FAULT:** a planted-wall mutant (refuses OLDALE_TOWN) must make `stuck … OLDALE_TOWN` rank first; the real code must not show it. This proves the blocker list can see a wall.

### The first skill build (this week if the budget allows, else at the reset)
- **Steps, for whatever A1 ranks first:**
  1. reproduce it through the LAUNCHER from the example's `end_state` + `world.jsonl`; use `play_harness` (clock pinned) only after the launcher has shown it;
  2. classify it: missing skill, bug, or setting;
  3. build a GENERAL skill (D1 of the backlog) with its own FAULT, CONTROL and held-out proof;
  4. re-run A1 on the new tree.
- **Predicted:** loader slice 1, map connections to passages, with the recon's P5 A/B (the discriminator: arrival y on ROUTE104, A > 37 against B < 31).
  - It needs the `KNOWLEDGE_FIELDS` classification (ruling 40), purity and fairness coverage, and a fix for `_nearest_place`/`_grass_map` breaking ties by name.
  - About 30-60 Mtok as a whole item.

### Phase A: the AI plays nonstop inside the learner (at the reset, about 25-40 Mtok as a whole item)
**Parts**
- **One-time setup by a session:**
  - clone `C:/Remote Projects/pokebot-ai-code` from origin;
  - give it a donor `metadata.yml` profile, because `profiles/*` is ignored and a fresh clone has none;
  - smoke-test one launcher run from it;
  - commit the D13 ledger row.
- **`ai-agent/ai_trainer.py` (new):**
  - **Job planner:** D15's priorities over CHAIN jobs (fresh → ch1_pokedex → ch2_wally → ch3_rustboro → ch4_roxanne, stopping at the first failed leg) and FRONTIER/DEPTH jobs from the pool. The pool bootstraps itself with chains.
  - **Variety:** personalities and starters cycle; the seed is drawn from the band.
  - **Budgets per leg:** chapters 1-2 get 330k frames / 3,600 s; chapters 3-4 get 600k / 3,600 s, so the wall clock is never shorter than for chapters 1-2. A stuck run ends itself at `STORY_PATIENCE`.
  - **Runner:** waves of `frontier_probe --trainer` as subprocesses from the AI code checkout (D17). Records are appended to `data/ai_runs.jsonl`, de-duplicated by run id.
  - **Code-checkout updater:** D1 (hourly check, drain, fast-forward, a new tree, the quotas restart).
  - **Blocker report:** `findings/AI-TRAINER.md`, rewritten every hour and at cycle end, plus `data/ai_blockers.json`. Its header says "development data, never a graded proof; `ai-frontier.txt` is the authority". It lists the top 5 blockers per chapter for the current tree and the previous tree side by side (the before and after of every fix), plus "AI saturated" when D15 runs dry.
  - **Experience:** append the D16 extract to `data/ai_experience.jsonl`.
  - **Retention and floor:** D11.
  - **AI-only stop:** after 5 REFUSED or NOT CLEAN ends in a row, the AI lanes stop for the cycle and `findings/AI-ATTENTION.md` is written. The bot carries on.
- **`learner.py`:**
  - a config `ai` block: `enabled`, `lanes`, budgets, `seed_band`, `code_checkout`, caps, `ai_min_free_gb`;
  - joint sizing in `size_lanes`/`_loop_body`: the AI share is planned by need (D5, D15), and the bot's minimum becomes 4; `other_bots_running` skips `ai-train-*` profiles so they are not counted twice;
  - `run_cycle` starts `ai_trainer.run_lanes(deadline)` in a guarded thread beside `_run_batch`. No run starts if now + its wall clock would pass the deadline. Any exception in the AI thread is logged and only stops the AI;
  - `finish_cycle` joins the AI lanes and writes the report plus the ops-row AI fields (runs, CLEAN share, fps, CPU, AI GB);
  - `learner_bytes` includes the AI store;
  - `adopt_unfinished` records finished runs that were never recorded and launches none;
  - `cmd_status` gets one AI line.
- **`tools/status.py` `ai_lines`:** runs this cycle, reach per chapter as read from the game (current tree), the top 3 blockers, and the AI checkout's tree.
- **Also updated:** `ai-agent/README.md`, `config.json` and `test_agent.py`.

**Tests** (offline, inside `test_agent.py`, so total test time stays well under 600 s). Each guard has a FAULT that must fail and a CONTROL that must pass:
1. Classification comes from files (D14): a NOT CLEAN or missing verdict counts toward the stop, while a CLEAN budget end with exit 124 does not. Five in a row trip the AI-only stop; one CLEAN end in between resets the count.
2. The env allow-list (D17): an injected `AI_PLAYER_FAULT_NO_HINTS` or `POKEBOT_X` is absent from the child. The command line is compared byte for byte.
3. No imports (D17): the AST check fails on a planted `import ai_player` and passes on the real tree.
4. Start provenance: a bot-profile `.ss1` is refused; a chain-made state is accepted.
5. Reach comes from the game: the AI says `done` but the truth flag is clear → NOT reached, plus a mismatch line.
6. The seed band (D13): a missing reserving row, or an overlapping registration → no AI lanes. Also, the trainer's code never opens `ledger.json` for writing.
7. Deadline: no launch near the cycle end; a launch when far from it.
8. Writes: only allow-listed paths; `git check-ignore` holds for `ai-train-*`; neither checkout ever gets a tracked change.
9. Code checkout (D1): no fast-forward while a run is live; a fast-forward after the drain; a tracked change → skipped.
10. Disk (D11): under `ai_min_free_gb` the AI stops and writes `AI-ATTENTION.md`, never `ATTENTION.md`; a corrupt zip keeps the raw copy; the caps delete the oldest tree's surplus and never an example or pool state.
11. With `ai.enabled` false, the plan and the batch command are byte-identical to today, and `runs.jsonl` never gets an AI row.
12. Adoption after a kill writes no duplicate records.
13. Joint sizing and D15 saturation → the next cycle's split, with and without bot singles.
14. A `frontier_probe` record with an unknown newer `schema_version` → AI-only stop, not a crash.

**Proof** (in the main checkout or a scratch copy, before deploy):
- A 1-hour `ai-once --lanes 2` dry run: every run CLEAN or INFRA, never a mismatch.
- **CONTROL:** chains reach chapter 2 at A1's rate.
- **FAULT:** the A1 planted-wall mutant, placed in a scratch AI checkout, ranks first, and the real tree does not show it.
- **FAULT:** a pushed tree that fails purity trips the AI-only stop while the bot cycle completes.

**Deploy:** commit and push. The clone restarts at the next boundary once `test_agent.py` passes. The first cycle is the canary: AI 4 (fps, CPU and disk in the ops row). Then AI 8 + bot 4, by a config commit.

**What it gives the AI's progress:** blocker lists on every new tree within about 2-3 hours of a push; the next wall measured before the current one is fixed (depth jobs); a pool of AI-made chapter-3/4 starts (most of R8+R9); stuck saves as repro fixtures; and the AI's own experience record, ready for the "past games" slice.

### Next: skill builds by the blocker list
- In the list's order: doubles, evolution/move-learn, R11 with training after a loss, R6's unknown-screen default, gap 7's budgets, and the "past games" slice (D16). Each is a whole item of about 30-90 Mtok.
- **Each is proven twice:**
  - by its own FAULT, CONTROL and held-out sweep (the proof);
  - by the trainer's before/after share on the new tree (development evidence, never the proof).

### Phase B: R12, the AI's settings registry, and tuning (about 60-90 Mtok as a whole item)
**Parts**
- **`ai_player/knobs.py`:** name, default, range, kind (`competence` | `budget` | `taste` | `safety`), and why.
- **Read sites:** `mode.py`, `brain/*`, `skills/*` and `personality.py` change to `knobs.get(...)`.
- **Overrides:** a file named by `AI_PLAYER_KNOBS` (`options.py`), checked against the ranges and recorded in the verdict and the run card. Anything out of range is refused.
  - `safety` and `budget` knobs can never be overridden by an arm.
  - `taste` knobs may only be set by a personality file.
  - `AI_PLAYER_KNOBS` joins the D17 allow-list.
- **`gates/check_knobs.py`:** every default equals today's literal (AST); no grader bound is a knob, and the AI cannot import one.
- **`ai_trainer`:**
  - arms are vectors of competence settings: a screening design first, then Thompson sampling;
  - arms are paired: the same start, seed and personality across arms in a cycle;
  - the score is progress at the frontier, as read from the game;
  - an arm that wins only at its range edge is reported, never proposed (D8);
  - the output is a proposal file, never a default change.
- **Lanes:** 16 in total (ruling 38's trigger).

**Tests:**
- defaults equal the literals (FAULT: one changed default goes red);
- an out-of-range override is refused, and an in-range one is applied and recorded;
- a taste, safety or budget knob in an arm is refused;
- the grader-import gate stays green (FAULT: a planted import);
- the planner pairs its starts.

**Proof:**
- the full regression lane, plus the revert drivers that are due;
- one knob A/B with held-out seeds registered first (CONTROL: the default arm equals today's behaviour within noise);
- a promotion needs a registered held-out graded sweep, with the person-likeness checks, to PASS.

### Phase C: curriculum, loader, milestones
- **Curriculum.** The frontier chapter advances when the frontier reach rate passes the threshold AND at least M New Game chains reached that chapter. Older-tree starts are used only when same-tree starts are short. The trainer writes the frontier candidate, and a session promotes it after a graded proof.
- **Milestones for chapters 5+**, from `campaign.json` and the chapter packs, checked with `extract_milestones.py --verify`.
- **The rest of the loader** (trainers, bosses, items) and A6's `--priors`, with their keys classified.
- **Long-game lanes** that use `--continue` across chapters (BUDGET ends are allowed by ruling 53).
- **Tests:**
  - the frontier advances only when both conditions hold (FAULT: frontier-lane success alone does not advance it);
  - the pool refuses a state without provenance;
  - milestone `--verify` (FAULT: a wrong flag id).
- **Cost:** curriculum about 15-25 Mtok, milestones about 15 Mtok per 4 chapters, and the loader's remaining slices about 30-45 Mtok (all whole items).

### Throughout
- **Lanes:** D5 and D15.
- **Disk:** P0 and D11.
- **Pure and person-fair:** D2, D3, D14 and D17. A frontier lane's practice from a save is the developers' training; the frontier counts only New Game chains.
- **Claude usage:** no consult in Phase A, and every build is chosen by data.
- **The bot's default behaviour never changes.** Its share of lanes changes (ruling 54); its code does not.

## 5. Risks

1. **Disk is falling about 4 GB a cycle from outside the learner.** The 25 GB stop arrives around 2026-11-03 even without the trainer. Mitigation: P0, then D11's AI-only floor at 45 GB.
2. **CPU contention.** Mitigation: the 4-lane canary, with fps and CPU in the ops row.
3. **The freeze watch** is safe only while profiles stay ignored (test 8).
4. **The code checkout drains** idle lanes for up to one run's wall clock on each `ai_player` push. That is accepted: pushes come a few times a day, and the alternative is 12 hours.
5. **Chapter patches instead of general skills,** or tuning toward a grader. Mitigation: general skills (backlog D1), D8, and held-out promotion.
6. **Trainer numbers read as proof.** Mitigation: the report header, D4, and the per-tree split.
7. **Stale pool starts.** Mitigation: provenance, and preferring same-tree starts.
8. **R2's in-game memory is archived per leg** (D12). It is documented, and Phase C fixes it.
9. **Every launcher run is a new trajectory on the host's clock** (`live_step5.py:405-410`). An example reproduces the region, not the exact path. Mitigation: reproduce through the launcher first, then pin the clock in `play_harness`.
10. **An AI failure must never stop the bot.** Mitigation: D17 (no imports), guarded threads, the AI-only stop, and the AI-only disk floor, none of which write `ATTENTION.md`.
11. **`test_agent.py`'s 600 s budget.** Mitigation: offline tests only, and the time is measured in the Phase A proof.
12. **The frontier still depends on build budget.** The week has about 50-65 Mtok left. Mitigation: D0's order spends it on the top blocker; `status.py` shows that blocker, so even a short session can act.
13. **The AI code checkout is a second copy to keep healthy.** Mitigation: ff-only, never edited, a tracked change → skipped, and a fallback to the deployment clone.

## 6. Open questions for the user (06 grepped: rulings 31, 38, 40, 50, 52, 53, 54)

- The lane split is no longer asked. Ruling 54 says the machine time goes to the AI, and ruling 38 keeps 12 in total until the AI has knobs to test.
- **Q1. Practice from saves, and ruling 52.**
  - The trainer's frontier lanes would replay the hardest chapter many times from the AI's own chapter-start saves.
  - The official frontier would count only games begun with a real New Game.
  - What the AI learns in those practice runs (for example "ROXANNE beat my level-10 team") would go into its "past games" memory.
  - Is that the developers' training, which is allowed? Or is it too close to ruling 52's "never reload a save to undo a lost battle"?
  - **Default without an answer:** yes, it is allowed as training. The memory from practice runs is kept apart from New Game chains, so the past-games slice can be measured with it and without it.

## 7. Revision log (each critic finding checked against the code and data)

- **F1 (MAJOR): APPLIED, with a different fix.**
  - Confirmed: AI code reaches the clone only between cycles (`learner.py:447-462`), and the AI player does not change within a tree.
  - The fixes:
    - D15 spends runs by information: quotas per tree and chapter, depth jobs past the top wall, under-sampled pairs, then "saturated";
    - D5 re-derives the split at each boundary, so a saturated tree hands lanes back to the bot;
    - D1's hourly AI code checkout cuts fix latency from up to 12 hours to about 1 hour, so new trees, and with them new information, arrive far faster;
    - §0 now says plainly what nonstop play does not do.
  - Lanes are NOT simply idled as the critic suggested: the user asked for nonstop play, and the depth jobs and the experience record (D16) give the extra runs a use.
- **F2 (MAJOR): APPLIED IN PART.**
  - Confirmed: 06:9507 defines "trained" to include experience across games, and nothing in the draft kept it.
  - Added D16: the experience record from day one (static map facts and fights, per-game facts filtered out), plus a "past games" reader as a skill build with its own classification, FAULT and CONTROL.
  - **REBUTTED as the gap-1 fix:** `keeps_going` (`goals.py:711-719`) and `lead_toward` (`:672-704`) refuse the woods, so no run crosses them and no past game can remember the crossing. Loader slice 1 stays the gap-1 fix.
  - A raw `world.jsonl` cannot be carried across games: it holds items, people, visits and closed doors (`world/memory.py`).
- **F3 (MAJOR): APPLIED.**
  - Confirmed: 79% of the week was used by 15:03 UTC (`cost-ledger.jsonl`). A launcher chain runner already exists (`live_step5.run_arm`, `rate_step5.run_chain`).
  - New D0/D10 order: A0 → A1 (`gates/frontier_probe.py`, which is also the trainer's runner core, so it is not wasted) → the top-blocker build → Phase A at the reset.
- **F4 (MAJOR): APPLIED.**
  - Confirmed: `code_signature` covers only `ai-agent/*.py` (`:426-431`), and the crash and test-failure paths write `ATTENTION.md`, which stops the bot (`:2026-2033`, `:2058-2062`).
  - Fixed by D17: no in-process `ai_player` import (an AST test), a subprocess runner, and an env ALLOW-LIST instead of a deny-list read from `options.py`, so a new switch can never leak in.
  - `options.py` has no command that lists its switches, so the critic's `--list-switches` alternative would have needed new code.
- **F5 (MAJOR): APPLIED.**
  - Confirmed: `_ours` (`:1379-1385`) and `learner_bytes` (`:826-829`) never touch AI folders, and `disk_guard` writes `ATTENTION.md` (`:1875-1897`).
  - Fixed by D11: own retention and caps, an AI-only floor at 45 GB that never writes `ATTENTION.md`, AI GB counted in `learner_gb`, and the measured 1.1 MB per zipped run.
  - **Found while checking:** free disk is falling about 4 GB a cycle from OUTSIDE the learner (`ops.jsonl`; `learner_gb` flat). Added P0 and risk 1.
- **F6 (MINOR): APPLIED.** Costs are now quoted as whole items (30-90 Mtok, from the ledger). Badge 1 is 120-540 Mtok, about 0.3-1.3 weeks of budget, counted from the next reset (inferred about 2026-11-04). This week's remainder is about 50-65 Mtok.
- **F7 (MINOR): APPLIED.**
  - Confirmed at 06:9946 (ruling 54, machine time to the AI) and 06:9297 (ruling 38's trigger is an AI knob or strategy).
  - D5 now reads: the AI first, 12 in total in Phase A, 16 at Phase B, and the bot keeps the rest (at least 4). The draft's lane question is dropped (rule 11).
  - The citation of ruling 50 for the lane split is withdrawn.
- **F8 (MINOR): APPLIED.** Confirmed: `seed_profile` copies the start (`launcher.py:247-253`), and L5.THIS_RUN exists at `live_step5.py:524-536`. Ported as D14's freshness check; a stale state is INFRA, kept out of the blockers and the pool.
- **F9 (MINOR): APPLIED.** Confirmed: `__main__.py:116-117` and `_HOST_CODES` (`launcher.py:275-276`). D14 classifies from the verdict file, and only REFUSED or NOT CLEAN count toward the stop. Chapters 3-4 now get 3,600 s.
- **F10 (MINOR): APPLIED.** D8 adds the `budget` kind, which is never tunable, and an edge-of-range winner is reported and never proposed.
- **F11 (MINOR): APPLIED, simpler than proposed.**
  - Confirmed: `ledger.json` is tracked and a clone write would block fast-forwards (`learner.py:452-453`).
  - `register` already refuses any same-family overlap (`ledger.py:126-129`), so one committed `story`/development row reserves the band with no `ledger.py` change, plus a FAULT and CONTROL test.
  - The trainer never writes the ledger.
- **F12 (NIT): APPLIED.** The clone is at b5baea6b, running ai0058, with the next boundary about 4:35 AM on 2026-10-31.
- **F13 (NIT): APPLIED.** KI-112 is the bot harness's issue. Risk 9 now cites the host clock (`live_step5.py:405-410`), and repro goes through the launcher first, then `play_harness` with the clock pinned.
- **F14 (NIT): APPLIED.** `_fight_double` is defined at `battle.py:1099` (`:851` is the call). The ledger anchors are now `PURPOSES` `:46`, `register` `:116-129` and `begin`'s development refusal `:180-184`.
- **Also found while checking (not raised by the critic):**
  - A fresh checkout has no profile donor: `profiles/*` is ignored, and `ensure_profile` needs a `metadata.yml` (`launcher.py:158-186`). The Phase A setup provides one.
  - The bot's 8-lane minimum (`learner.py` about `:2123`) must become 4 for the bot's share in the joint sizing.
