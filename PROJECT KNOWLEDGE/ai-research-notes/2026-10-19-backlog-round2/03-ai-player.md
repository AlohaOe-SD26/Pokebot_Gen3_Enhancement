# Backlog round 2, angle 3: the AI PLAYER's robustness toward the WHOLE game (2026-10-19)

A NOTE, not truth. It adds to `2026-10-18-improvement-backlog.md` (A1-A6, B1-B6, C1-C2, D1-D3, E1-E3) and repeats none of it.
Every item names the evidence it stands on. Citations were read on the 2026-10-19 working copy; two claims are marked
ESTIMATE (a projection, not a measurement) and one UNVERIFIED (a live behaviour nobody has tried).

## The one finding behind most of these

Everything the AI player has is sized and proven for chapters 1-2, run as a batch of short games on an unthrottled emulator.
The goal (USER RULING 41, and the vision's "regular speed x1", `01` line 21-30) is one game, played in real time, for a very
long stretch, with nobody watching. At x1 a single hour is 216,000 frames, while the AI's whole patience is 120,000 frames
(`mode.py:104`, "33 minutes"). So the questions that were optional for a 30-minute test run (does it survive a crash, does it
save, what does it do when stuck, can anyone see what it did) are the ones that decide whether it is deployable.

## Order and dependencies

R3 -> R4 and R6 (cheap, additive, unlock the rest); R1 + R2 together (a save is only half a resume); R7, R8 and R15 need R1,
R2 and R3. R13 is a paragraph of design, to write before the AI-player tuner mode exists.

## A. High value per token

**R1. The AI SAVES the game itself (START menu, SAVE) and RESUMES from its own save (title screen, CONTINUE).** Priority A.
- **Evidence:**
  - No skill saves or continues. A search of `ai_player/` finds only the label tuples: `eyes/screens.py:260-267`
    (`MAIN_MENU_OPTIONS` rows with CONTINUE, and `START_MENU_ACTIONS` "SAVE"). `skills/intro.py:9` assumes "NEW GAME ... on a
    fresh save it is the first of two", and `mode.py:438` says "nothing is saved yet".
  - The framework's only resume file is written when the emulator CLOSES CLEANLY: `libmgba.py:141` ("Whenever the emulator closes,
    it stores the current state in `current_state.ss1`") and `:241`. A power cut or a hard kill leaves the last clean-close state,
    or none. The tuner already lost a whole cycle that way (backlog E2, ai0031, 2026-10-17).
  - `host/launcher.py:90-93` already knows `current_save.sav`: "A fresh boot with one present CONTINUES it".
- **What:** (1) a `save_game` skill that opens START, reads the cursor on SAVE, answers the overwrite question by its words, and
  waits for the "saved" text; (2) an intro branch that reads the main menu and picks CONTINUE when it is there, then settles on
  the overworld; (3) a "when to save" rule by personality (after a Center heal, after a badge, before a gym, before a long route;
  a careful archetype saves more); (4) a rule that saving is allowed only on a free overworld screen (see R5).
- **Benefit:** a crash, a Windows update or a power cut costs minutes of play instead of the run. It is also what a person does, so
  it is faithful ("a state-write is a documented last-resort fallback", `CLAUDE.md`). It is the base of R2, R7, R8 and R15.
- **Cost / risk:** medium. Proof: live arm = play to a Center, save, KILL the process, relaunch with only the `.sav`, CONTINUE,
  assert the same party PIDs, map and tile (identity, not counts); a fault arm that kills before the save must resume EARLIER.
  UNVERIFIED: whether mGBA flushes the cartridge save to `current_save.sav` before a kill; measure that first. Risk of
  save-scumming: forbid reloading to undo a loss (a resume is for crashes only), and say so in `LESSONS.md`.

**R2. Persist the goal manager's memory, and make `world.jsonl` incremental.** Priority B (it makes R1 a real resume).
- **Evidence:**
  - Only the WORLD memory is carried: `brain/goals.py:62` and `:431-450` say "the memory is carried between sessions,
    `AI_PLAYER_WORLD`; this goal manager's own memory is not". `_Memory` holds `talked`, `tried_items`, `fight_prep`, `no_balls`,
    `exhausted`, `seen_levels`, `home_heals` and more (`goals.py:407-470`). A resumed AI would re-talk, re-try
    balls it gave up on, and forget how far its fight preparation got.
  - `mode.py:786,797` appends a FULL snapshot of the world at every map change. MEASURED: `gates/fixtures/route101_south.world.jsonl`
    lines are 17,389 / 42,503 / 42,503 bytes at 889 tiles learned (about 48 bytes a tile).
  - ESTIMATE, not measured: a whole game is tens of thousands of tiles and thousands of map changes, so the file grows with
    (snapshots x tiles), plausibly gigabytes. Nobody has run a long game to see.
- **What:** one `memory.jsonl` through the existing `RecordFile` (no new file writer for the purity gate, `runlog.py` docstring): a
  full line now and then, deltas between, both memories in it, a version field, and a loader that restores both. Stamp each line
  with the game's own play-time or save counter, so a resume picks the newest memory NOT NEWER than the save it loaded (a memory
  that "remembers" a gift the save lost is the one inconsistent state this design creates).
- **Benefit:** resume is exact, and the disk stays bounded. **Cost:** medium (a serialiser for `_Memory`, a kill-and-resume unit
  test). **Risk:** a field missed in the serialiser. The test: fuzz the kill frame, resume, compare the two memories field by field.

**R3. Typed outcomes: a coded failure taxonomy, instead of control flow on message text.** Priority A.
- **Evidence:**
  - Control flow reads message prefixes: `brain/goals.py:558,566,1966,2010-2011,2016,2057-2099,2241,2299` use
    `outcome.startswith("done"/"budget"/"stuck: nothing"/"picked up"/"not picked up: interrupted"/DOOR_UNUSABLE)`. 31 gate sites
    match the same strings (`gates/live_step3.py:742` is a regex on a stuck message). Rewording a reason (a `LESSONS` PL-11 fix)
    can change behaviour with no test failing.
  - About 15 distinct `stuck:` literals sit in `brain/navigator.py:1059-1343`, and `_play_end(kind, why)` (`mode.py:647`) knows
    only the kinds `stuck` and `done`. "What stops runs" is therefore a regex job on prose each time.
- **What:** `ai_player/outcomes.py` with a small enum (STUCK_NOTHING_NEW, STUCK_PINGPONG, STUCK_UNKNOWN_SCREEN, STUCK_NO_TARGET,
  LOST_BATTLES, BUDGET, DONE ...) and one `classify(text)` table; the end record, `[AI-EXIT]` and R4 carry the code. A gate (AST)
  fails when a returned `"stuck: ..."` literal has no code. Migrate the `startswith` branches to codes one file at a time.
- **Benefit:** wording can change safely, and every later question ("what ended the last 50 runs?") is a one-line count. The tuner
  and R7's ladder branch on the code. **Cost:** small if additive first. **Risk:** low; the mutant is "reword a reason" and the
  classifier test must fail instead of the behaviour.

**R4. A `run_card.json` written at every AI run's end.** Priority A (needs R3).
- **Evidence:** the tuner reads an AI run only through scorer lines copied from the bot (`memory_log.py:7-40`,
  `ai-agent/scoring.py parse_log`). The human-likeness measures live in the `end` note and the log line (`mode.py:665-681`: waits,
  pushes, idle, spent, losses) and, for grading, in the harness's second path (`rate_step5.game_yield`). Nothing machine-readable
  summarises one run. Backlog A1/A2 do this for suites and the status screen, not for the AI's own runs.
- **What:** a 2 KB file: coded end (R3), the frontier (furthest milestone, frames), share of frames by goal kind, waits and pushes,
  losses BY NAMED FIGHT, party by PID, personality and seed, tree digest, whether the clock was pinned (B6), wall seconds.
- **Benefit:** A1's frontier line, D3, the tuner and a human all read one file; no agent reads a log. **Cost:** small.
  **Risk:** Goodhart (B1, R13): the card REPORTS; graders keep their own thresholds out of the AI's reach.

**R6. An unknown-screen default policy, plus a SCREEN WISHLIST.** Priority A.
- **Evidence:**
  - Any menu kind that is not in `_story_menu`'s three cases ends the whole run: `brain/navigator.py:1092-1099` ("stuck: an
    unexpected X on screen") and `mode.py:611-622`. The recon's Gap 5 (the Rustboro trader's YES opens a party menu) is exactly
    this and was "replayed until STORY_PATIENCE".
  - Known unhandled screens already: the level-up stats box ("a stats box the AI cannot read yet", `README.md` ~2835), the
    evolution scene (B cancels it, recon Gap 3), the "Delete a move?" prompt. Later chapters add many (PC, nickname, TM/HM teach,
    berry blender, contests, trades, Name Rater, daycare, Secret Base, Frontier).
- **What:** (a) a person-fair default ladder: read the words, decline a yes/no it has no plan for, B out of a menu, a small
  ALLOW-LIST of screens where B is harmful (evolution: A only); (b) every time the default fires, append the screen's fingerprint
  (menu kind, task id, the words) to `screen_wishlist.jsonl`; (c) `screen_wishlist.py` prints unhandled screens by frequency.
- **Benefit:** a run-ender becomes a prioritised to-do list, and the batch finds the next screen to build without an agent
  fan-out (backlog A5's chapter pack can list the expected ones). **Cost:** small-medium. **Risk:** B on some screens is wrong
  (the allow-list is data and each entry gets a fixture); the default must never press A on a purchase or a trade.

**R8. STUCK-TO-FIXTURE: a rolling checkpoint ring, so a failure reproduces in minutes.** Priority A (needs R2, R3).
- **Evidence:** a stuck verdict today costs the whole run again (`NOHINTS`: one stretch open for 59,204 frames, found only in a
  20-run sweep, `README.md` "Step 5.2, the verifier's round"); `CLAUDE.md` rule 9 (a long batch "has resolved nothing four times
  running"); fixtures are hand-built by `gates/make_*.py` (2,161 lines). A `.ss1` is a PNG (the screen) with the state inside
  (`libmgba.py:201-229`), about 0.34 MB (`gates/fixtures`: 6.8 MB for 20), so a ring is cheap.
- **What:** the HOST side (the instrument writes files, not the AI) saves a state every N game minutes into the run folder, keeps
  the last 3, with R2's memory beside it and the pinned clock. On a bad end (an R3 code, a crash) the entry from before the stuck
  stretch is copied out as `stuck-<code>-<date>.ss1`, and `replay_from.py` re-runs the AI from it as an A/B.
- **Benefit:** hours to minutes per failure, and every fixture is a REAL failure, which is the regression suite that matters.
  **Cost:** medium. **Risk:** `get_screenshot` is a look-ahead the purity instrument counts (`host/attribution.py:38,187`), so the
  call must be made where the instrument allows it; saving a state costs frames (measure); disk goes through B4's factory.

**R9. CHAPTER-CHAIN checkpoints, made only by the AI's own presses.** Priority A.
- **Evidence:** recon Gap 9 ("a chapter-3 run started from a bot save has never 'heard' DAD", `goals.py:999-1002`);
  `rival_rustboro.build.json` shows a fixture sourced from `tools/story-dev/saves/fresh_rivalprep.ss1` (a bot save); the sweeps
  already chain the grader's `seen_tiles.json` and `seen_texts.json`, but the AI's own memory is handed over by hand
  (`AI_PLAYER_WORLD`).
- **What:** when a chapter's graded run passes, the harness writes `checkpoints/chN-end/` (state, R2 memory, build.json with the tree
  digest and clock) and chapter N+1's sweeps start from the set of those, several seeds and starters wide. A chapter never starts
  from a bot save again.
- **Benefit:** later-chapter tests begin where the AI can really be (including its real weak parties, which a bot's strong team hides,
  which is the Gap 2 / Roxanne question), and chapter 5+ needs no new bot-derived fixtures. **Cost:** small-medium (the
  `build.json` machinery exists). **Risk:** staleness after a code change: each checkpoint carries a digest and is rebuilt when the
  chapter's proof is re-run (PR-3).

## B. Correctness

**R5. A FREE-SCREEN precondition at every boundary: "done" never means "mid-scene".** Priority B.
- **Evidence:** recon Gap 4: `FLAG_BADGE01_GET` is set before TM39's text and `VAR_SCOTT_STATE` before SCOTT's lines; the run ends
  at `mode.py:457-458` (`_play_end(... "done" ...)`) with no check that the box is gone. The same shape holds for every gym.
- **What:** one `settle_to_free(hands)` helper (no text box, controls unlocked, the overworld), called before a run ends "done",
  before a goal switch after a milestone flips, and before R1's save; the chapter-end check asserts it.
- **Benefit:** a chained chapter does not start inside a text box, and saving is safe. **Cost:** small. **Risk:** low; its fault arm
  is a fixture where the flag flips with a box up.

**R7. A GET-UNSTUCK LADDER for deployed play, while the graders keep the strict give-up.** Priority B (needs R1, R3).
- **Evidence:** `LESSONS.md` PL-6/PL-17 ("with nothing left anywhere it gives the run up"); `goals.py:1360` `give_up`; `mode.py:471-472`
  ends the run after `STORY_PATIENCE`; `host/lifecycle.py` turns a give-up into process exit. For an art piece that is looked at "from
  time to time" (`01` line 21) a process that has quietly exited after 33 minutes without news is the worst result.
  The 5.2 NOHINTS arm: 98 goals in a row ended "stuck: ping-pong".
- **What:** a fixed, bounded ladder, each rung person-fair, logged with its R3 code, with its own planted-stuck fault arm:
  clear the screen (R6) -> wait for the people in the way -> walk back to the last Center -> talk to everyone in reach and read signs
  (a person asks) -> leave by a different door -> heal and save (R1) -> quit and CONTINUE from its own save -> only then give up, with
  a stuck fixture (R8). Deploy mode only (`--patience=deploy`); the graded mode keeps today's strict end.
- **Benefit:** a stuck AI keeps being watchable. **Cost:** medium-large. **Risk:** a ladder hides bugs from the graders. So the
  rung that freed each run is REPORTED (R4), and a rate of rung 7 above a bound fails the sweep.

**R10. A REGION-AWARE world graph (map components), as a prerequisite, not a chapter-3 patch.** Priority B. SHARPENS D1.
- **Evidence:** recon Gap 1 (VERY HIGH): the planner treats each map as one node (`explore.py:174-203`, `goals.py:435-452`), `OUTDOOR`
  excludes PETALBURG_WOODS (`goals.py:432`), and `_nearest_place` / `_grass_map` break ties by NAME (`goals.py:1160-1180`, `:1624-1640`).
  D1 names "passage navigation" for chapter 3 only. UNVERIFIED: that later maps repeat the shape (water, ledge or cave splits); the
  bot's Area Atlases are the place to check before sizing it.
- **What:** the graph's nodes are components of the tiles the AI has walked; exits and edge crossings attach to a component; ties
  break by walking distance, never by name. Build it once, with chapter 3's A/B as its proof.
- **Benefit:** no per-map workaround for each split map. **Cost:** medium. **Risk:** the planner is hot code; the unit grid model
  (`test_world.py`) plus chapters 1-2's sweeps must stay green.

**R11. A DEFEAT LEDGER: losses become lessons, per named fight, not a run-ending counter.** Priority B.
- **Evidence:** `MAX_LOSSES = 3` counts across chapters 1-4 (`mode.py:105`, recon Gap 2); the bot's own walls repeat the shape
  (KI-118 Norman, KI-122 Tate & Liza; the Champion rate flat at 13-17 %, backlog C2). A person loses to a boss several times.
- **What:** a persisted `fight_ledger` (R2): per named fight, losses, the party and levels at each loss, what changed. It drives
  "train a step more", "lead with the counter-type", "buy healing", "catch something of that type". In deploy mode the whole-run cap
  is replaced by per-fight escalation with a long cooldown.
- **Benefit:** the same mechanism serves ROXANNE and the eighth gym; build once. **Cost:** medium. **Risk:** a ledger that
  rewards loafing (R13): the escalation must be graded by the game's own level and badge counters.

**R12. An AI KNOB REGISTRY: the prerequisite to tuning the AI.** Priority B (SHARPENS D2).
- **Evidence:** about 129 module-level numeric constants in the AI (a count of simple `NAME = number` lines: `goals.py` 29,
  `navigator.py` 20, `battle.py` 15, `explore.py` 10, `mode.py` 10 ...); `README.md` "Known limits" lists about 15 as "taste, not
  measured from people" (`HUNT_FRUITLESS`, `BESIDE`, `YIELD_TILE_RATE`, `CURIOUS_ODDS_CAP`, `PERSON_BLOCK_HITS`, `BALANCE_MIN_FRAMES`,
  `AGAIN_MAX`, `DANGER_RETRIES`, `END_SLACK` ...). The only environment hooks are run settings and about 20 `AI_PLAYER_FAULT_*`
  test switches, so no taste constant can be tuned. `#28-trainer-autonomy` (2) wants the learner tuning the AI at 16 lanes.
- **What:** `ai_player/knobs.py`: name, default, range, the behaviour and the measure it trades, "taste" or "measured", read once
  from an override file; a gate that proves every default equals today's literal (so registering changes no behaviour); D2's
  personality weights become entries.
- **Benefit:** the tuner can move the AI without Claude editing code; each knob documents its own trade. **Cost:** small-medium.
  **Risk:** a knob changing a graded bound by the back door; the grader's bounds are never knobs (B1).

**R13. The AI tuner's fitness is a HELD-OUT judge, never the AI's own grader.** Priority B. SHARPENS B1 and C2. Cost: a design paragraph.
- **Evidence:** `08` 2026-10-15 ("THE AI AIMED AT THE GRADER'S OWN QUANTITY ... A BEELINE FIX BECAME LOAFING"); `LESSONS.md` PF-14;
  5.2's AI uses the grader's own yield thresholds. One developer found that exploit in days; a tuner running 12-16 lanes of
  games a cycle against any fixed metric will find the next one by construction.
- **What:** before the AI-player tuner mode is built, write the rule: fitness = progress READ FROM THE GAME (milestone and badge
  counters, by PID/flag) plus a human-likeness floor from a rotating judge whose thresholds the tuner and the AI cannot read; the
  top strategy is re-graded by the strict gate every week.
- **Benefit:** prevents a month of tuning toward a loophole. **Risk:** none (it is a rule written first).

## C. Nice to have

**R14. A PROGRESS PAGE for the user: a static page built from a run folder, no emulator.** Priority C.
- **Evidence:** the user's stated purpose: "an art piece I can look at from time to time to see its progress" (`01` line 21). Today
  the record is `ai_player.log`, `actions.jsonl` and `world.jsonl` and a non-programmer cannot read them.
- **What:** `make_progress_page.py <run>` writes one HTML file: the milestone timeline with real x1 time, the map trail (from the
  world memory's transitions), party by species and level over time, battles and whiteouts, the share of time by goal kind, the
  personality, the R4 card. Keyframes for free: a `.ss1` is a PNG of the screen (`libmgba.py:201-229`), so R8's ring is also a
  picture strip. Optional later: a press log plus a pinned clock to replay a stretch on demand (needs B6; UNVERIFIED that the action
  log records every press).
- **Benefit:** the deliverable can be looked at. **Cost:** small-medium, no emulator, no agent after it is built. **Risk:** none.

**R15. A DEPLOYMENT SUPERVISOR with a crash-loop breaker.** Priority C (needs R1, R2, R3).
- **Evidence:** the AI exits with a code for every ending (`host/lifecycle.py:48-60`: 2 crash, 3 parked, 4 starved, 6 purity, 124 wall
  clock) and nothing relaunches it; the tuner's autostart works (backlog E3) but only for the tuner.
- **What:** a small loop: launch, read the verdict, relaunch from the save and memory for the benign codes, stop and alert when the
  same code recurs at the same frame twice (a crash loop), and refuse to run when disk is low (B4).
- **Benefit:** weeks of x1 play survive reboots. **Cost:** small. **Risk:** a supervisor that masks a real defect; hence "same
  code, same frame, twice means stop".

## Considered and not added

- `regression_due.py` (a map of suite to files, `LESSONS.md` PR-2): a SHARPENING of A2 (the regression is skipped today because it is
  expensive: "The regression of steps 0-4 was not re-run", `README.md` Known limits of step 5.2). Fold it into `run_regression.py`.
- Budgets as data from recorded runs (recon Gap 7): chapter-3 scoped and already in the recon's fix list.
- `check_fairness.py` (recon Gap 14): already built (`gates/check_fairness.py` exists).

## Suggested order after the reset

R3 and R4 (small, additive) -> R6 -> R1 + R2 (one step, one live kill-and-resume proof) -> R5 -> R9 -> R8 -> R12 and R13 (before the
tuner mode) -> R7, R10, R11 with chapters 3-4 -> R14, R15.
