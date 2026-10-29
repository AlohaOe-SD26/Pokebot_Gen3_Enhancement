> **Filed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1build/SPEC.md` (sha256 `93fd778440e1db39`). Backlog R1 + R2's build spec (with DP1 + DP2 and L3 (a)-(b)), unblocked by USER RULINGS 51 and 52 (`06` 2026-10-29). Made by the workflow `r1r2-build-spec` (7.97 Mtok input-equivalent, `cost-ledger.jsonl`): a designer; three adversarial critics (game and host truth, 13 findings; rulings, purity and person-fairness, 10 with 2 MAJOR; proof and safety, 18 with 4 MAJOR); a reviser, whose section 11 logs what it did with each finding; and a cold-start check (could it start with no human input: YES; six MINOR gaps, the builder notes just below). Its section 10 asks the user U1 and U2; the build does not wait for either answer.
> **Builder notes (the cold-start check's six gaps; they bind the build):** (1) a worktree has no `sandbox-pokebot/mgba/` (untracked): set `AI_PLAYER_BUILD_ROOT` to the MAIN checkout's `sandbox-pokebot`, read only, as `probe_save_kill.py` did, and make every throwaway profile under the run's own `--out` folder, never under `<build_root>/profiles/`; (2) K-BETWEEN's kill frame comes from an earlier run of the SAME seed, so its arm records a determinism line (the trajectory up to the kill equals that run's) or it does not count; (3) check 6's "within the frames of one decision" gets a number, set from step 6 (b)'s measurements BEFORE the held-out seeds are registered; (4) the silent window was measured on `route101_south.ss1` only: every live arm reads the FILE verdict with the probe's own parser (`probe_save_kill.parse_image`), never assumes it; (5) K-SILENT counts only if the AI's S2 memory line was written BEFORE the kill and the kill lands before the write's first sector completes; step 6 measures the line's frame against e3, and if it comes too late the arm is vacuous: STOP and report it as a finding, never a pass; (6) "confirm no lane is running" means a process census for `run_regression`, `run_gates`, `revert_*`, `rate_step5` and `live_step5`.

# R1 + R2: THE AI SAVES LIKE A PERSON, CONTINUES AFTER A KILL, AND ITS MEMORY SURVIVES (build spec, 2026-10-29)

> Status: SPEC, REVISED. The draft (`s53/r1build/SPEC-draft.md`, about 8:20 AM Los Angeles) was reviewed by three
> adversarial critics (`s53/r1build/critique-{game-host,rulings-purity,proof-safety}.md`, 8:33 to 8:45 AM). This revision
> was written 2026-10-29 at about 8:50 AM. Every finding was checked against the code and the pinned decomp before it was
> applied or rebutted; the "Revision log" (section 11) lists each one.
> Backlog items R1 + R2 with DP1 + DP2 and L3 (a)-(b) (`ai-research-notes/2026-10-18-improvement-backlog.md:290-302`,
> `:402-410`; "The order" step 6: "DP1 + DP2 and L3 (a)-(b) land WITH R1 + R2, before its first memory file").
> Unblocked by USER RULINGS 51 and 52 (session scratch `s53/r1build/rulings51-52.md`; they go into `06` after the lane).
> MEASURED input: `ai-research-notes/2026-10-29-R1R2-PROBE-REPORT.md` (sections 00, 0, FR2-FR8; FR7 supersedes the
> builder's sections). The five recon files `2026-10-29-R1R2-recon-{game,host,code,record,refute}.md` are NOTES: where a
> note disagrees with the code or the probe, the code and the measurement win, and this spec says which.
> Every `file:line` below was read on 2026-10-29 at HEAD `f36c9451` (decomp: `C:/Remote Projects/_decomp/pokeemerald`).
> The builder re-reads each anchor before editing.

## 0. Summary

The AI learns to save its game through the game's own START → SAVE → YES dialog, reading each page by its words. It
saves at the three moments of USER RULING 51: after healing at a POKéMON CENTER, right before it talks to a gym leader,
and after a big story moment. It never saves mid-battle, mid-scene or on a screen that is not free, and never twice within
3 minutes of game play time. At the start of each save's flash write it appends one line to `memory.jsonl` (a full memory,
or a delta from the save before it), stamped with the game's play time in hours and minutes. When a run is KILLED, the
operator restarts it with the launcher's new `--continue`: the `.ss1` is dropped, the cartridge save is kept, and the AI
plays the title screen itself. It reads any error page by its words, reads the CONTINUE window's TIME, picks the save
record with that time, presses CONTINUE, and checks that the place and the party it arrives with are the ones it
remembers. Then it restores its memory AS OF THAT SAVE, never newer. If the save is gone it STOPS and says so; it never
starts a NEW GAME on its own. The ruling-52 exception (a stationary legendary's failed catch) is NOT built.

**What enforces USER RULING 52, by name (and what does not):**
- the LAUNCHER refuses `--continue` unless the last run ended without the AI choosing it (killed, crashed, parked or
  interrupted), or it ended right after a save. It decides from the host's own records: the run's verdict file, which only `lifecycle.finish` writes, and a new launcher-owned
  `launches.jsonl`. The AI's own `end` line only adds whether the end came right after a save (D12 (a));
- the PURITY GATE refuses `sys.exit`, `exit`, `quit`, `SystemExit` and `KeyboardInterrupt` in every play-loop file (D12 (c));
  its existing ban on loads, resets and save states in the play loop stands;
- the CONTROLLER refuses START or SELECT held together with any other button, so no reset or erase combination can be
  pressed (D12 (b));
- a whiteout is played on (D12 (d)).
- **Not enforced:** an exception the AI's code raises on purpose ends the run as a `crash`, which is allowed to continue.
  No gate can refuse every `raise`. The continue then TELLS how many lost battles it undoes (D12 (e)).
- **Interim, pending the user (U2):** a run that ended on its frame budget or its wall clock may be continued only if it
  ended right after a save.

## 1. What and why (each part traced to what asks for it)

- **Save and CONTINUE by the game's own screens, read by their words** (backlog R1 + R2 "What": "`save_game` and
  CONTINUE read by their words, saving only on a free screen (R5)", `:292-294`). No skill saves today: no code presses
  START in the overworld (recon-code §0 (b), by grep; `skills/intro.py:114` presses only NEW GAME).
- **When it saves = RULING 51 (option A):** "at a Pokémon Center, before a gym leader, and after a big story moment".
  Rejected by the user: B (every milestone) and C (only chapter ends).
- **Never reloads to undo a loss = RULING 52;** the legendary exception is deferred. The technical reading in the rulings
  file (Claude's call): a CONTINUE after an external kill is not a reload; the AI never ends or restarts its own process;
  "a CONTINUE happens only when the host restarts a killed run" (`rulings51-52.md:8`); memory goes back to the save,
  never newer.
- **A memory that survives a kill** (R2): today only the world memory crosses processes, by the LAST line of a file
  (`world/memory.py:864-871` `read_world`; `mode.py:942` `_start_world`). The goal manager's memory is not carried
  (`brain/goals.py:449`). The resume `.ss1` is written on a clean close only (probe report §0; `libmgba.py:159-160`).
  Backlog: "one `memory.jsonl` (full lines plus deltas) stamped with play time, so a resume loads memory NOT NEWER than its
  save" (`:293-294`).
- **DP1 + DP2** (`:402-406`): one `AppPaths`, a `schema_version` on every user-data file, a NEWER file refused
  byte-identical. `memory.jsonl` is the first persisted AI file, so its path and schema are fixed now.
- **L3 (a)-(b)** (`:407-410`): every Pokemon by PID and species, with ROLES as fields "in R2's memory schema from its first
  line".
- **R5 is the precondition** (built 2026-10-29: `mode.py:480-487`, `_settle_before_done` `:676-754`; its D8 handed the
  save call site to R1, `2026-10-28-R5-BUILD-SPEC.md` D8).
- **The measured facts this design rests on** (probe report §0, §3, FR2, FR4, FR5):
  - one save's flash write takes 256-261 frames, with nothing changing on screen and the main loop frozen. The play time
    stood still from 67237 to 67495 at [0,17,22,6] (§3 "Other facts"). From START to a free screen took 756-969 frames;
    from the first flash write (e3) to the SAVED page (e5), 339-343 (FR4);
  - mGBA flushes the file 16 frames after the last write. A process kill after the write keeps the new save, even before
    the flush (K0, K1, KX, the NOREAD arms);
  - a kill inside the write loses that save. On a fresh cart's FIRST save, nothing is left: the "erased" page and NEW GAME
    only from e3+19 on, and no page at all before that (KM-FIRST@18 vs @19, FR2 `:387`). On the SECOND save, the game falls
    back to the first: the "corrupted" page from e3+18 on, and SILENTLY with no page in [e3, e3+17] (KM-SECOND@0, @2, @17
    silent; @18 the page; FR2 `:388`, FR5 `:462-463`). A THIRD save has no silent window;
  - a `.ss1` with a bumped version magic gives a silent cold boot (M6). A cold boot's first callback is the copyright
    screen (frame 13), then the intro (frame 176) (§4 M6).
  The silent window is why the memory cannot trust the error page. The save the game loaded must be identified by what
  the CONTINUE screen and the arrival show (D4).

## 2. Decisions (each with the rejected alternative; all go to `06` with the build)

- **D1. The game's own dialogs, pressed by the AI.** Save = START → SAVE → YES (and YES to "There is already a saved
  file..." when the cartridge's save is its own, D17). Continue = title → CONTINUE. Rejected: any framework save state or
  load (`check_purity.py:544-547` bans `load_save_state`, `load_save`, `reset`, `create_save_state` in the play loop;
  recon-refute W8: the AI has no state-write fallback).
- **D2. A save is a GOAL KIND, `"save"`, chosen by the goal manager** (`GoalManager.next_goal`, `brain/goals.py:1159`).
  It inherits for free the play loop's free-screen precondition (`mode.py:504-516`: play-out first; `SETTLE_FREE`), the
  thinking pause and the "screen changed while it decided" second look (`mode.py:532-547`, LESSONS PL-18: one free look is
  not a free screen), the goal record and the failure cooldown (`manager.outcome`, `FAIL_LIMIT` 2, `COOLDOWN_DECISIONS` 12,
  `brain/goals.py:238-239`). Plus ONE more call site: a save that is DUE when the run ends "done" is made after R5's settle
  (section 3 (d)). Rejected: a save hook inside `_settle_before_done` only (it misses centres and leaders); a timer
  autosave (neither of the user's options).
- **D3. The three moments, defined from what the AI sees and knows (ruling 40 allows static game knowledge):**
  - *At a POKéMON CENTER:* a `heal` goal that returned "healed" (`brain/goals.py:2111-2114`) on a map whose const ends in
    `POKEMON_CENTER_1F` (`CENTER_SUFFIX`, `:235`) makes a save DUE. The due expires when the player leaves that map unsaved.
    Checked at block 1b of `next_goal`, right after HEAL (`:1184-1226`) and before "# 2. SHOP" (`:1227`).
  - *Before a gym leader (REVISED, finding m2):* checked in block 8, STORY (`:1351`), AFTER heal (1), train (5) and the
    other errands have had their turn. The rule: the story goal about to be returned is a `talk` step of a milestone whose
    fight is NAMED (`Milestone.fight_named`, `knowledge/story.py:78`), and the player stands on that milestone's gym map
    (`is_gym`, `brain/goals.py:319`). If no save was made since the player last ENTERED that gym map (the newest
    `world.transitions` entry onto it), a `save` goal is returned in its place. So the AI saves right before it walks up to
    the leader, once per approach. If it leaves to train or heal and comes back, it saves again before the talk. A save
    made within `SAVE_MIN_MINUTES` before the talk (a centre save just before, say) counts as that save. Today this is
    `ch4_roxanne` only (`milestones.json`: maps `RUSTBORO_CITY_GYM`, named). `ch2_dad`'s gym talk has no fight, and the
    rival's named fight is on no gym map. Rejected: due on entering the gym map and spent once per milestone (the draft):
    the AI then left to train and fought the leader with no save before her (`brain/goals.py:1284-1296` TRAIN comes after
    any block 1b).
  - *After a big story moment:* passing one of `BIG_MOMENTS = ("ch1_lab", "ch1_rival_route103", "ch1_pokedex",
    "ch2_wally", "ch3_woods", "ch4_roxanne")`. In order: the starter is the player's; the first win over the rival; the
    POKéDEX from PROF. BIRCH; the end of WALLY's catching tutorial; saving the DEVON researcher from the TEAM AQUA GRUNT in
    PETALBURG WOODS (a GREAT BALL as thanks: `milestones.json` `ch3_woods`, decomp `data/maps/PetalburgWoods/scripts.inc:343-349`);
    the STONE BADGE. Each is registered where the loop already tells every passed milestone (`HandsBrain._milestone_line`,
    `mode.py:653-675`), and only milestone IDS reach `brain/saving.py` (D18). A constant in `brain/saving.py`, with a test
    that every id exists in `knowledge/milestones.json`. Rejected: a new key in `milestones.json` (its extractor
    `extract_milestones.py --check`, its `--verify` and `check_fairness.py` RULE B's classification would all change;
    per-milestone data belongs to L1 + L2's generator, backlog `:407-410`).
- **D4. The memory's clock is the game's PLAY TIME in hours and minutes,** the value the game writes into the save and
  shows again on the CONTINUE window (`src/main_menu.c` `MainMenu_FormatSavegameTime`, `:2147-2152`: `playTimeHours` and
  `playTimeMinutes` only). The save info window shows the same TIME when it opens (`src/start_menu.c:1385-1388`, drawn once
  with the CONFIRM question), so the stamp can be at most a minute after the TIME on screen. The stamp is read on the FIRST
  look that shows the whole "SAVING… DON'T TURN OFF THE POWER." page. The CONTINUE match is the NEWEST record (by file
  order) whose stamp is within 1 minute of the CONTINUE window's TIME, then VERIFIED on arrival by map, tile and party
  (PID, species). Newest wins: after a continue to an older save, a record of an abandoned branch can lie within a minute
  of a new one, but the abandoned record is always OLDER in the file (finding N2, game-host). The tolerance exists because
  the first full-page look can be one frame before the write freezes the clock. The probe measured printer 0 active at
  67237 and idle at 67238, with the clock already still from 67237 (§3), so the case may not occur at all. The arrival
  check catches anything else. Rejected: the full counter with seconds and VBlanks (never on screen: RULING 40's line on
  live hidden state; it would need a user ruling); the emulator frame counter (0 at every cold boot: recon-refute C4; not
  a game clock); trusting the error page alone (the measured silent window loads S1 with NO page).
- **D5. The save line is appended at the START of the write** (the first full SAVING look), append-only, never
  rewritten. A short `saved` line follows when "{PLAYER} saved the game." is read; nothing depends on it. Rejected:
  writing after "saved the game.". A kill in [e4, e5) (82 frames measured) would then leave a save the memory does not
  know, and the next continue would falsely STOP. K-AFTER (e4+40) tests this live, and mutant S10 offline. Also rejected:
  writing before the last YES (the stamp would not be the written value).
- **D6. `memory.jsonl` format (schema 1):** `header`, `session`, `save` (full, or a delta from its PARENT save), `saved`,
  `lost` and `end` lines (section 3 (c)). A full payload when the save has no parent or `FULL_EVERY = 8` deltas follow the
  last full line in its chain; otherwise a delta: a depth-2 dict diff against the parent's rebuilt payload. A torn LAST line
  is ignored (and told); any other unreadable line refuses the file. Rejected: a whole memory per line, as `world.jsonl`
  does (by chapter 2 one line is about 0.3 MB: 10,739,541 bytes in 34 lines, recon-code §0 (a), measured with wc); one file
  per save (DP1: one file per game).
- **D7. Frames across a cold boot: a FRAME BASE.** In a continue run the brain wraps its eyes so that every look's `frame`
  is the emulator's frame plus `1 + the largest frame stamp in memory.jsonl` (`_RebasedEyes` in `mode.py`, framework-free,
  `dataclasses.replace` on the frozen `Observation`). Every carried stamp then stays in the past. Without it a carried stamp
  is in the FUTURE after a cold boot. For example, a door found closed is retried only when
  `frame - info["frame"] >= CLOSED_RETRY_FRAMES` (`world/memory.py:788`, 36,000 frames, `:115`), which a counter restarted
  at 0 would not reach for that long. The base is 0 in every run that is not a continue, so every existing log and grader
  is unchanged (T6). Rejected: shifting each stored stamp (every frame field of `WorldMemory` and `_Memory` would have to
  be listed; one missed is a silent bug).
- **D8. DP1: `ai_player/paths.py`, `AppPaths`.** The memory of a game lives beside the cartridge save it describes (one
  playthrough = one save = one memory: round-3 deployment D4, `2026-10-19-backlog-round3/02-deployment.md:66`). The dev
  default is `<build_root>/profiles/<NAME>/ai_player/` (`memory.jsonl` and `launches.jsonl`); with `AI_PLAYER_HOME` set,
  `<AI_PLAYER_HOME>/games/<NAME>/`. The launcher resolves it and passes `AI_PLAYER_MEMORY`; the harness's `--memory FILE`
  is ALWAYS that profile's `AppPaths` path in the live proof (finding G6). A new gate, `gates/check_paths.py`, refuses the
  literals `sandbox-pokebot`, `Remote Projects`, `C:/` and `C:\\` in string constants outside the dev resolver
  (`host/launcher.py` `resolve_build_root`, `:113-118`, and `paths.py`), skipping docstrings and comments. Its scope is the
  package minus `gates/`; the test side's 20 lines in 16 files (recon-refute W10) are a listed known limit for a later pass.
  Rejected: the run directory (a new one per process: `__main__.py` `cmd_run`, `run_dir`); the repo (user data in git).
- **D9. DP2: `schema_version` 1 in the header line** of `memory.jsonl` and of `launches.jsonl`. A NEWER version is refused
  with the file left byte-identical (by the launcher before the child starts, and by the brain on read). No older version
  exists, so no migration is built; the rule for v2 (copy to a backup, then migrate forward only) is recorded in `06`.
  Rejected: a version on every line (the file is the unit, and a v2 program migrates the file before appending).
- **D10. `--fresh` and `--state` ARCHIVE an existing memory file** (and `launches.jsonl`), renamed into
  `<game dir>/retired/<name>-<YYYYmmdd-HHMMSS>.jsonl`, never deleted or rewritten. A start with NO flag on a profile that
  holds a memory file is REFUSED: it would load the last clean close's `.ss1` beside a newer cartridge save, the split-brain
  of recon-host A7 and recon-refute N3. Rejected: keeping today's silent "resuming whatever the profile already holds"
  (`launcher.py:187-188`) for AI games.
- **D11. `--continue` (launcher):** requires the marker (`PROFILE_MARKER`, `launcher.py:86`), `current_save.sav` and a
  valid memory file with at least one save line, and passes D12 (a). It refuses when `AI_PLAYER_WORLD` is set (D19). It
  DELETES `current_state.ss1`: the cartridge is the truth, and a `.ss1` is tied to the build and carries RAM (M6's silent
  cold boot, recon-host A6). It keeps the `.sav` and sets `AI_PLAYER_CONTINUE=1`. The AI then plays the title itself.
  Rejected: resuming from the `.ss1` (not a person's way, and split-brain). A memory file with no `.sav` is a plain launcher
  refusal (T7).
- **D12. RULING 52 in code, not prose (CLAUDE.md rule 6):**
  - (a) **The launcher's continue rule.** It classifies how the NEWEST session of the memory file ended, from three
    records, in this order of trust:
    1. `launches.jsonl` (launcher-owned; D20): the line for that session's `run_dir`, written by the launcher after its
       child exited. It holds the exit code, whether the LAUNCHER hard-killed the child at its wall clock, and the verdict
       file's `exit_reason`;
    2. else `<run_dir>/purity.json` `facts.exit_reason` (written only by `lifecycle.finish`, `host/lifecycle.py:168-176`;
       an external kill leaves none);
    3. the AI's own `end` line, which supplies `at_save` (the last thing the run did was a successful save).

    | how the session ended | class | `--continue` |
    |---|---|---|
    | no verdict file and no launcher line (killed from outside: the operator, the OS, a power cut; or a harness child killed by the live proof) | KILLED | allowed |
    | `crash`, `frame-budget` (the AI's steps starved), `parked-manual`, `abandoned`, `interrupted`, `interrupted-unresponsive` | INVOLUNTARY | allowed |
    | the brain's reason `play: done: ...` or `play: stuck: ...` | CHOSEN | refused unless `at_save` |
    | `play: stopped: ...` (the frame budget, `mode.py:976-977`), `wall-clock` (soft), or the launcher's hard kill at the wall clock | BUDGET | refused unless `at_save` (interim; U2) |
    | `stray-exit`, `brain-returned`, `purity-breach`, `purity-unverified`, `isolation-lost` | NOT CLEAN | refused |
    | the session names a `run_dir` that no longer exists and no launcher line names it | UNKNOWN | refused ("cannot tell a kill from a chosen end") |
    | CHOSEN or BUDGET with no `end` line (an exception before the AI wrote it) | — | refused (fail closed) |

    A harness session (`host: "harness"`, the in-process test side, which has no lifecycle) is classified by its `end`
    line alone: chosen or budget and not `at_save` → refused; no `end` line → KILLED. Every refusal is the launcher's
    existing "cannot start" path (`cmd_run`, exit 2) with a plain sentence naming the class and the session.
    Rejected: the draft's "a kill, a crash, the wall clock or the frame budget leaves no chosen end" (finding M1). A frame
    budget or wall-clock end is a clean, routine end (`__main__.py:55-56` defaults 3000 frames and 600 s), not a kill; it
    would have undone every battle lost since the last save at every session boundary. Also rejected: deciding only from
    the AI-written `end` line (finding M2: it fails OPEN, because a missing line reads as a kill).
  - (b) **The controller refuses START or SELECT held together with any other button** (`host/controller.py`: it tracks
    the buttons it holds; a `hold` or `tap` that would make such a set raises `ControllerError`). Every reset or erase
    combination needs SELECT: the soft reset A+B+START+SELECT (`src/main.c:135-137`); the title's clear-save, RTC and berry
    combos all include B+SELECT (`src/title_screen.c:39-41`). B held with a direction (running, once MOM gives the RUNNING
    SHOES: `src/field_player_avatar.c:658`) stays allowed. Nothing holds two buttons today (`hands/pad.py:91-121`: every
    press is one hold). Rejected: one button at a time (the draft; findings G8 and m1): it would forbid running forever,
    and a later running feature would have to weaken a ruling-52 guard. Also rejected: enumerating the forbidden sets
    (m1's fix): the SELECT/START rule covers every one of them with one test.
  - (c) **The purity gate** (`check_purity.py`): `sys.exit` narrows from `ANY_FILE` (`:428-431`) to the lifecycle and the
    launcher files (the only users: `host/lifecycle.py:185`, `__main__.py:213`). The builtin names `exit`, `quit`,
    `SystemExit` and `KeyboardInterrupt` are refused in every play-loop file (`brain/`, `skills/`, `hands/`, `world/`,
    `eyes/`, `mode.py`, `personality.py`, `game_memory.py`, `options.py`), raised or caught. `os.abort`, `os.kill` and
    `os._exit` are already off the play loop's `os` surface (`:417-425`). The existing ban on loads, resets and save states
    in the play loop stands (`:544-547`). A FAULT plant and a CONTROL (a mention in a docstring or comment does not fire)
    go into `test_check_purity.py`.
  - (d) A whiteout is played on, as today (`mode.py:633-634`: "it goes on from where the game put it").
  - (e) **Every loss is on the record, and every continue tells what it undoes.** The brain appends a `lost` line at each
    battle `_count_losses` counts (`mode.py:627-638`). Before allowing a continue, the launcher prints "this continue undoes
    N battles lost after save h:mm (the last run ended: <class>)". The AI tells the same after its arrival, from the `lost`
    lines that follow the save it continued. The loss count is part of each save's payload, so `MAX_LOSSES` counts across
    processes as of the save (T5).
  - Rejected: refusing only when a battle was lost since the last save. That is the most precise reading of the ruling's
    words, but it would allow a continue after a CHOSEN end with no loss in it. That case is the deferred legendary
    exception ("ran out of balls, reload"), which must not be built. It remains open for BUDGET ends only, as U2.
- **D13. The stall bound is not on the save's path (REVISED, finding F6).** `advance` returns `menu:<kind>` BEFORE its
  stall counter whenever a ui is on screen (`hands/dialogue.py:206-208` before `:222-230`). E1 gives every save stage a ui,
  so `STALL_FRAMES` (300) is never consulted for a save page. The 261-frame write cannot trip it. The draft's "named scene,
  900" (its E3, its test and its mutant R3) is WITHDRAWN: it protected a path that is never reached. The path that IS
  reached is the play loop meeting a save ui outside the skill: `play_out` → `advance` → `menu:save_dialog` → the
  navigator's `on_menu` (`brain/navigator.py:1094-1097`) → `_story_menu` (`mode.py:640`). `_story_menu` gains the save
  kinds (section 3 (d)): it never presses during a save page, and it closes a start menu or a save question the AI did not
  mean to leave open.
- **D14. Saving is ON for the play brain whenever a memory file is given:** every launcher `play` run gets one; the
  in-process harness only with `--memory`. `AI_PLAYER_FAULT_NO_SAVE=1` is the pre-R1 CONTROL. A run without a memory file
  behaves exactly as before R1: the step-6 A/B (section 8) MEASURES that claim. Rejected: saving in the harness by default
  (every graded sweep's trajectory and its errand share, `rate_step5.py:1086-1112`, would move without a decision to
  re-baseline).
- **D15. L3 (a)-(b): a Pokemon registry keyed by PID** (hex). Each entry holds its current species, every species seen
  for that PID (evolution keeps the PID), where it was first seen in the party (`{"map", "tile"}`, the same keys as a save
  line's `where`; never `x`, `y` or `state`, which `check_fairness.py` RULE B2 refuses in dicts the deciding code reads),
  when (`frame`, `play_time`), how it came (`starter`, `caught`, `joined`), and `roles: []`. The vocabulary is `ROLES =
  ("lead", "hm_carrier", "counter", "catch_helper", "spare")`, each role `{"role", "for": <boss name or null>, "until":
  <boss name or null>}`. No role is ASSIGNED in this build (that is L3 (c)-(d), the PC skill). Pokemon seen only in a PC
  box are not registered (`StoredMon` has no species: `eyes/observation.py:229-239`).
- **D16. What a continue restores, field by field** (section 3 (c), table): identity and experience are kept; per-process
  loop guards and clocks are reset. Every `_Memory` field (`brain/goals.py:407-496`) must be classified KEEP or RESET in a
  table, and an unclassified field FAILS a test (the pattern of `check_fairness.py` RULE B).
- **D17. Whose save is on the cartridge (NEW, finding G3).** Which question the game asks is decided by RAM, not by the
  cart. `gDifferentSaveFile` is FALSE after any save (`src/start_menu.c:1096`) and after a boot or CONTINUE
  (`src/new_game.c:141`). It is set TRUE only by NEW GAME (`:154`). A `.ss1` restores both it and `gSaveFileStatus` from
  RAM, while `--state` and `--fresh` EMPTY the cart (`launcher.py:196-198`). So a `--state` run from a state taken after a
  save (live_step5's CH2: `gates/live_step5.py:461`) asks "There is already a saved file" on its first save, over an empty
  cart. The launcher therefore TELLS the brain what the cart held when the run began, `AI_PLAYER_CART`:
  - `empty`: `--fresh` or `--state` emptied it, so every save on it since was made by this run;
  - `continued`: `--continue`, so its save is this game's (the TIME match and the arrival verify it);
  - `kept`: no flag.
  The in-process harness passes `empty`: its emulator is `is_test_run=True` (`gates/probe_eyes.py:197`), with no file
  behind the cart (the builder re-checks that it boots with no save). With `--profile-dir`, it passes `empty` only after
  asserting the profile's `current_save.sav` is absent or empty, else `kept`. With `--continue` it passes `continued`.
  OVERWRITE is answered YES only when the cart is `empty` or `continued`, or this run has already saved. Otherwise the AI
  answers NO ("a saved file it does not know"). Rejected: `--state` runs never save (the draft's live_step5 claim would then
  be false; and a fixture start is the most common dev start); the draft's `own_save_known` (true only with a memory
  record, so CH2 answered NO at every save moment, each a failed goal).
- **D18. The play time and the milestone ids reach only the save code (NEW, findings m5 and N1-rulings).**
  `check_fairness.py`'s `FLAG_DOORS` purpose for `HandsBrain._milestone_line` (`:82-83`) adds "and the save after a big
  story moment (USER RULING 51): only milestone ids reach `brain/saving.py`". A new allowlist, `PLAY_TIME_DOORS` (RULE A's
  pattern), names the only readers of `.play_time`: `skills/saving.py`, `brain/saving.py`, `game_memory.py`,
  `mode.py` `HandsBrain._save`/`_continue`, and `hands/dialogue.py` `seen_now` (which drops it). A read anywhere else in
  the deciding code fails the gate. `seen_now` compares `look.progress` whole (`hands/dialogue.py:121`), and a minute
  tick would reset `advance`'s stall counter, so it compares `dataclasses.replace(progress, play_time=None)`. The play time
  is not on the screen the AI watches; a person sees it on the trainer card, the save window and CONTINUE. Rejected: a
  play time every deciding module may read (a live clock with only prose limiting it, CLAUDE.md rule 6).
- **D19. A continued game's memory is its save's, and nothing else's (NEW, finding m4).** `AI_PLAYER_WORLD` (`options.py:393`)
  loads the LAST snapshot of a `world.jsonl` (`mode.py:942`), which is exactly the pre-R2 rule. In continue mode it is
  REFUSED by the launcher ("the memory of a continued game is its save's") and by the brain (an end before any press). The
  harness parser refuses `--world-in` with `--continue`. Rejected: ignoring it and telling (an ignored option is how a
  graded arm silently measures the wrong thing).
- **D20. `launches.jsonl` (NEW, finding M2): the launcher's own record of how each child ended,** beside `memory.jsonl`
  (D8). It has a `header` line with `schema_version` 1, then one `{"kind": "launch_end", "run_dir", "exit_code",
  "hard_kill": bool, "interrupted": bool, "exit_reason": <purity.json's, or null>, "ended"}` line per child, appended by
  `cmd_run` after `run_child` returns (`launcher.py:375-431` `run_child`, `ChildResult.killed`). If the launcher itself is killed it
  writes nothing, which correctly reads as KILLED. Rejected: the verdict file alone (a launcher hard kill and an external
  kill both leave none, so an AI that hung until the hard kill would read as killed).

## 3. The parts

### (a) EYES: what the AI recognises, and how (within the purity contract)

All reads go through doors `host/eyes.py` already has: `read_symbol`, `context.emulator.read_bytes`, the task list, and
the two symbol doors. `get_symbol` resolves a fixed table of names once (`_callback_name`, `host/eyes.py:462-480`), and
`get_symbol_name` names a function pointer (`_battle_menus`, `:554`). `gMenuCallback` and `sSaveDialogCallback` are named
like `_callback_name` names `gMain.callback2`: a fixed table of the save's function addresses, resolved once with
`get_symbol`, thumb bit off. No new door, nothing written. Symbols checked present in
`sandbox-pokebot/modules/data/symbols/pokeemerald.sym` (2026-10-29): `sStartMenuCursorPos` `:283`, `sNumStartMenuActions`
`:284`, `sCurrentStartMenuActions` `:285`, `sSaveDialogCallback` `:287`, `sSaveDialogTimer` `:288`, `gMenuCallback` `:978`,
and the functions `Task_ShowStartMenu` `:6333`, `HandleStartMenuInput` `:6335`, `StartMenuSaveCallback` `:6341`,
`SaveStartCallback` `:6349`, `SaveCallback` `:6350`, `SaveConfirmInputCallback` `:6366`, `SaveOverwriteInputCallback`
`:6370`, `SaveDoSaveCallback` `:6372`, `SaveSuccessCallback` `:6373`, `SaveReturnSuccessCallback` `:6374`,
`SaveErrorCallback` `:6375`, `SaveReturnErrorCallback` `:6376`, `Task_WaitForSaveFileErrorWindow` `:2718`.

- **E1. The START menu and the save dialog: THE TASK DECIDES FIRST (REVISED, finding G1).** Neither callback is ever
  cleared. `gMenuCallback` is written only at `src/start_menu.c:571, 616, 726, 780, 812, 826, 843, 851, 862`, and a B close
  leaves it `HandleStartMenuInput` (`:629-634`). A NO leaves `sSaveDialogCallback` at an input callback (`:1024-1028`,
  `:1070-1074`). A stale value must never read as "takes input".
  - `eyes/screens.py` `UI_TASKS` (`:216`) gets `"Task_ShowStartMenu": "start_menu"`; `host/eyes.py` `_SMENU_TASKS`
    (`:217`) gets it too (the save's yes/no is polled through `sMenu`).
  - `host/eyes.py` `_ui` (`:482`) reads `raw["start_menu"]` when `StartMenuTask` OR `Task_ShowStartMenu` runs. Under
    `Task_ShowStartMenu` it also reads the task's `data[0]`, `raw["menu_callback"]` (`gMenuCallback` named) and, ONLY when
    that is `SaveCallback`, `raw["save_callback"]` (`sSaveDialogCallback` named).
  - `read_ui` (`eyes/screens.py:576-582`), in this order:
    1. `StartMenuTask` runs (the menu is being BUILT) → `MenuView("start_menu", options, cursor, accepts_input=False)`,
       whatever `gMenuCallback` says. Today this view reads True; nothing in the AI opens the menu, so no behaviour moves.
       The builder checks `gates/test_eyes.py:397` and every `start_menu` use.
    2. `Task_ShowStartMenu` with `data[0] == 0` (its first frame, before case 0 sets `gMenuCallback`, `:566-573`) → the
       same view, not accepting.
    3. `Task_ShowStartMenu` and `menu_callback == "HandleStartMenuInput"` → `MenuView("start_menu", options, cursor,
       accepts_input=True)`.
    4. `menu_callback` is `"StartMenuSaveCallback"` or `"SaveStartCallback"` (the two frames before `InitSave` sets
       `sSaveDialogCallback`, `:809-815`, `:877-881`) → `MenuView("save_dialog", accepts_input=False)`.
    5. `menu_callback == "SaveCallback"` and `save_callback` is `"SaveConfirmInputCallback"` or
       `"SaveOverwriteInputCallback"` → `MenuView("save_yes_no", YES_NO, cursor=_s8(menu[2]), accepts_input=True)`. It is
       its own kind, NOT `"yes_no"`, so a scene's answer rules (`skills/story.py` `answer_question`, the navigator's
       `menu:yes_no` branch) can never answer it.
    6. `menu_callback == "SaveCallback"`, any other save callback → `MenuView("save_dialog", accepts_input=False)`. Its
       presence makes `shown` true (`host/eyes.py:451`), so `text` is printer 0's last message, the page's WORDS (`_text`,
       `:732-737`). A paragraph break that waits for A is still reported by the text-printer wait
       (`screen.waits_for_button`).
    7. any other `menu_callback` (an item's fade) → `MenuView("start_menu", accepts_input=False)`.
- **E2. The save dialog's pages, by their words** (`data/text/save.inc:2-29`). The skill classifies `page_text(text)`
  (whitespace and the paragraph mark folded) into: `CONFIRM` "Would you like to save the game?"; `OVERWRITE` "There is
  already a saved file. Is it okay to overwrite it?"; `DIFFERENT` (starts "WARNING!"; three paragraph breaks before its
  question, "Are you sure you want to save now and overwrite the other save file?", `:16-24`); `SAVING` "SAVING… DON'T TURN
  OFF THE POWER." (full) or a prefix of it (printing); `SAVED` `^.+ saved the game\.$`; `ERROR` starts "Save error." (one
  paragraph break, `:26-29`). A function `save_page(text) -> str | None` in `skills/saving.py`.
- **E3. (withdrawn: D13.)**
- **E4. The main menu's error pages** (`src/main_menu.c:649-660`: `gText_SaveFileErased` for CORRUPT,
  `gText_SaveFileCorrupted` for ERROR; and `:723-737`: `gText_BatteryRunDry` under `Task_WaitForBatteryDryErrorWindow`). All
  three are printed on window 7 by printer 7 (`CreateMainMenuErrorWindow` `:2116-2119`). Today the eyes read only printer 0
  once a page has printed (`host/eyes.py:732-737`; recon-refute N2). `_text` takes the task names: while
  `Task_WaitForSaveFileErrorWindow` OR `Task_WaitForBatteryDryErrorWindow` runs (both already TASK_WAITS waits for A,
  `eyes/screens.py:310-311`), the last message is PRINTER 7's ROM string. `_rom_string` already handles a finished printer
  that points one past its EOS (`host/eyes.py:306-314`; the probe's `printer_page` note, report §7.12).
- **E5. The game's play time, H:MM only.** `Progress.play_time: tuple[int, int] | None = None`
  (`eyes/observation.py:249-259`; a default, so every positional construction stays valid) = `gSaveBlock2Ptr` + 0x0E, u16
  hours, and + 0x10, u8 minutes (`include/global.h:514-515`). It is read with the two doors `_marks` uses
  (`host/eyes.py:323-331`): constants `PLAY_TIME_OFFSET = 0x0E`, `PLAY_TIME_BYTES = 3`. Seconds (0x11) and VBlanks (0x12)
  are never read. Who may read it: D18.
- **E6. The CONTINUE window's TIME:** the main menu's view (`read_ui`, `eyes/screens.py:554-560`) carries `hours` and
  `minutes` (existing `MenuView` fields, used by the clock) when `tMenuType >= 1`, read by `_ui` from SaveBlock2 as in E5.
  The boot read has already copied the loaded slot into RAM (probe report §1 "Child B"; `MainMenu_FormatSavegameTime` draws
  exactly these two fields).
- **E7. The test side's twin** (`gates/play_harness.py:403-408` `INPUT_TASKS` lists `StartMenuTask` as an input task):
  replace it with the precise rule, by the harness's OWN symbol reads, never the AI's eyes. The start menu takes input only
  under `Task_ShowStartMenu` with `gMenuCallback == HandleStartMenuInput`; the save's yes/no only under `SaveCallback`
  with one of the two input callbacks. A unit FAULT/CONTROL and a mutant prove it (section 4, section 6 S30). Otherwise the
  261-frame write could be counted as "a screen waiting for a press with none", 1.15x under the graders' `AWAIT_MAX` 300
  (`rate_step5.py:445`, `:1995`).

### (b) HANDS / SKILLS: `skills/saving.py` (new, framework-free)

Constants (each from a measured number; the builder re-checks them in the eyes probe, step 2 of section 8):
- `SAVE_WRITE_BUDGET = 900`: from the first full SAVING look to the SAVED page. That is 2.6x the longest measured e3-to-e5
  (343, FR4; finding N1, game-host).
- `SAVE_CLOSE_BUDGET = 600`: from the SAVED page to a free screen (measured e5→e7 103 frames, FR4).
- `SAVE_DIALOG_BUDGET = 3000`: START to free again (measured 756-969 with test-side presses; the AI's reading and
  thinking pauses add a few hundred more).
- `COMMIT_FRAMES_NEEDED = 1500` (= `SAVE_WRITE_BUDGET + SAVE_CLOSE_BUDGET`; NEW, finding F10): no YES is pressed with fewer
  frames left in the run's budget. Step 2 re-checks that it is at least 2x the longest measured "YES to free" with the AI's
  pacing. `_bounded` (`mode.py:965-978`) closes a skill at the budget, and a skill closed mid-write tears the save; the
  YES is the only press that can start a write.
- `SAVE_FRAMES_NEEDED = 3000`: the policy starts no save with fewer frames left (a coarse filter; the commit check is the
  guard).
- `BACKOUT_PRESSES = 6`, `PAGE_PRESSES = 6` (paragraph pages turned inside one dialog), `ERROR_PRESSES = 4`.

**`save_game(hands, why, cart_is_own: bool, frames_left: Callable[[], int], on_writing, on_saved) ->
Generator[..., str]`** returns `"saved"` or `"not saved: <why>"`, or `"stuck: <why>"` when the dialog could not be closed or
a write never ended (the loop then ends the run). `cart_is_own` is D17's rule. Every step is bounded, and every press has a
gate that names what the eyes said.
1. Precondition: `nav_free` on a fresh look (`brain/navigator.py:245-247`); otherwise return without a press.
2. START, gated "the player is free on the overworld: START opens the menu". `wait_for_ui(hands, "start_menu", why)`
   (`hands/menus.py:75`, 600 frames). Not open → return "not saved: the menu did not open" (no further press; whatever
   opened is the loop's to play).
3. `"SAVE"` not in the menu's options (a place with no SAVE) → BACK OUT (step 7). Else `choose(hands, "start_menu", "SAVE",
   why)` (`hands/menus.py:120`: the cursor is READ, A only on it, the reaction checked).
4. The dialog loop, at most `SAVE_DIALOG_BUDGET` frames, one look per frame:
   - `ui.kind == "save_yes_no"` and it takes input → read the page first (`hands.pad.idle(reading_frames)`, then a note
     "read"):
     - `CONFIRM` → YES;
     - `OVERWRITE` → YES only if `cart_is_own`, else NO, result "not saved: a saved file it does not know";
     - `DIFFERENT` → NO, result "not saved: another game's save" (never overwrite another game; its yes/no opens on NO,
       `DisplayYesNoMenuWithDefault(1)`, `:1037-1053`);
     - anything else → NO, result "not saved: an unread question" (never YES to a page it could not read).
     Before every YES: `frames_left() >= COMMIT_FRAMES_NEEDED`, else NO, result "not saved: too few frames left in the run
     to finish a save". YES and NO are `choose(..., "save_yes_no", ...)` (cursor read).
     **Every NO goes on to step 7 (REVISED, findings G4 and F3).** A NO reopens the START menu, and it takes input
     (`SaveCallback` on SAVE_CANCELED: `InitStartMenu(); gMenuCallback = HandleStartMenuInput;`, `src/start_menu.c:823-827`).
     The skill returns its result only once the screen is free again.
   - `ui.kind == "save_dialog"` and the eyes say a text printer waits for a button, before any SAVING page (REVISED,
     finding G2: the WARNING's three paragraph breaks) → read the page, then A, gated "a paragraph of the save dialog's
     page waits; A only turns the page". At most `PAGE_PRESSES`. The WARNING's yes/no then opens.
   - page `SAVING` and complete, the first time → read `look.progress.play_time`; call `on_writing(play_time, look)` ONCE
     (the brain appends the save line, D5). A partial SAVING page (still printing) is waited out with no press.
   - from that look on, no press of any kind until the SAVED or ERROR page, or `SAVE_WRITE_BUDGET`. If the budget runs out,
     return "stuck: the save did not finish within 900 frames" with still no press ("DON'T TURN OFF THE POWER"); the loop
     ends the run, and nothing is left for `play_out`.
   - page `SAVED` → `on_saved(look)`; wait with no press for `nav_free` held over two looks a decision pause apart (PL-18),
     at most `SAVE_CLOSE_BUDGET`; return "saved" (or "saved; the box did not close within 600 frames"). "Saved" is declared
     ONLY on the SAVED page (recon-refute N1; CLAUDE.md rule 7: instrument the action).
   - page `ERROR` (REVISED, finding G2) → A at each wait the eyes report, at most `ERROR_PRESSES`, until the screen is
     free. The first wait is the page's paragraph break, while `SaveErrorCallback` waits for printer 0 (`:1136-1145`). The
     second is `SaveReturnErrorCallback` once `sSaveDialogTimer` is 0 (E-rule: that callback with the timer at 0 reads as a
     wait for A; `SaveErrorTimer` `:964-976` takes `JOY_HELD(A_BUTTON)`). Return "not saved: the game said: <words>".
   - otherwise: `hands.pad.busy(busy_reason(look))`.
5. Every look on the SAVING page through the write is kept. The skill asserts that the play time it read did not change
   during the write; if it did, it TELLS it ("the stamp may not be the written value"). Tested (section 4), mutant S11.
6. Budget exhausted without SAVED, before SAVING appeared → "not saved: ..." with what was last on screen, then step 7.
7. BACK OUT (any NO, any failure while the START menu or the save yes/no TAKES INPUT; never once SAVING has appeared): B,
   gated on that look, until `nav_free` held over two looks, at most `BACKOUT_PRESSES`. A B on the yes/no is NO
   (`MENU_B_PRESSED`, `:1024-1028`); a B on the menu closes it (`:629-634`). Still not free → "stuck: the dialog could not be
   closed" (the loop ends the run: it is not left to `play_out`).

**`continue_game(hands, book, why) -> Generator[..., ContinueResult]`** (`book` is the open memory file, section (c)).
Bounded by `CONTINUE_BUDGET` from power-on to the main menu and `ARRIVAL_BUDGET` from the CONTINUE press to a held free
overworld. Provisional values are 6000 and 1200; both are set in step 6 from the AI's OWN measured continues (development
rehearsals), at 2x the longest seen (finding F4: the probe's continuer pressed START every 20 frames with no reading
pauses, probe report §1 "Child B").
1. The intro movie and title are skipped with START exactly as `play_intro` does (`skills/intro.py:100-112`). That block
   moves into a helper `skip_title(hands, kind)` that both skills call (no behaviour change for the intro).
2. A main-menu error page (E4) is READ (note "read" with its words), classified `corrupted` / `erased` / `battery` /
   other, and acknowledged with A when the eyes say it waits. At most 3 pages.
3. On the main menu (`ui.kind == "main_menu"`, taking input):
   - `"CONTINUE"` not in its options → STOP: return `stopped("the save is gone: " + <the erased page's words, or "the main
     menu offers no CONTINUE">)`. No press on the main menu. Never NEW GAME.
   - CONTINUE offered: `time = (ui.hours, ui.minutes)`; `record = book.match(time)` (the newest save line within 1 minute,
     D4). None → STOP: "the game holds a save the AI does not remember making (TIME h:mm; its saves: ...)". Else
     `choose(hands, "main_menu", "CONTINUE", ...)` (cursor read).
4. Arrival: a look with `nav_free`, then the decision pause and a second free look (PL-18), within `ARRIVAL_BUDGET`. Then
   VERIFY: `player.map_const == record.where.map`, `(x, y) == record.where.tile`, and the party's `(pid, species)` list
   equals the record's. A mismatch → STOP: "the save it continued is not the one it remembers: <both>". It never plays on
   with a memory that does not match the game.
5. Return `continued(record, page)`. The brain restores (section (c)) and tells "continued the save of h:mm (MAP x,y)". It
   adds "the game said the save was corrupted: it continues the save before it" for the `corrupted` page, or "the game
   continued an OLDER save than its last, with no page" when the record is not the newest. It also adds the D12 (e)
   sentence when `lost` lines follow that save.

### (c) R2: THE MEMORY FILE: `ai_player/game_memory.py` (new, framework-free, play-loop side)

- **Writing:** only through `runlog.RecordFile(directory, "memory.jsonl")` (`runlog.py:55-89`: each record opened,
  appended, closed; a kill keeps every finished line). After each append the writer checks that `RecordFile.written` rose.
  A save line that did not reach the file is TOLD, and the run ends `stuck: the memory of this save could not be written`
  right after the save completes: a save the memory does not know would stop the next continue (test and mutant S12).
- **Reading:** `open(path, "r", encoding="utf-8")` only (`check_purity.py` allows a constant read mode, as `read_world`
  uses, `world/memory.py:864-871`). The whole file is read once at play start.
- **Lines** (one JSON object each; `frame` is the brain's rebased frame, D7):
  - `{"kind": "header", "schema_version": 1, "game": "<profile>|<created ISO time>", "identity": {"seed", "personality",
    "favourite", "starter", "gender", "name"}}`: written with the FIRST save line of a game (no save, no file).
  - `{"kind": "session", "n", "started", "how": "new game"|"continue", "host": "launcher"|"harness", "run_dir", "cart":
    "empty"|"continued"|"kept", "frame_base", "continued_from": <save id>|null, "page": <the error page's words>|null,
    "verified": <the arrival check>, "restored_maps": [<map keys of the restored world memory>]|null, "losses": <restored
    count>}`. It is written at the session's FIRST save, or at a continue's restore (before the first post-continue look),
    or at a STOP.
  - `{"kind": "save", "id", "parent": <save id>|null, "full": bool, "play_time": [h, m], "frame", "where": {"map",
    "tile"}, "party": [{"pid": "<hex>", "species"}], "why": "<the moment>", "memory": <payload or delta>}`
  - `{"kind": "saved", "id", "frame"}`, `{"kind": "lost", "frame", "play_time", "where", "after_save": <save id>|null}`
    (D12 (e)), and `{"kind": "end", "session", "reason", "chosen": bool, "budget": bool, "at_save": bool, "frame"}`.
- **The payload:** `{"world": WorldMemory.to_dict() (world/memory.py:801-816), "goals": the KEEP fields of _Memory,
  "personality": {"base", "favourite", "history", "draws"}, "battle": {"wishes", "met", "wild_met"}, "mons": <registry,
  D15>, "losses": <report["losses"] at the save>}`. `_Memory`'s sets and tuple keys go through a small tagged JSON codec
  (`{"__set__": [...]}`, `{"__tuple__": [...]}`, `{"__dict__": [[key, value], ...]}` for non-string keys), proven by a
  round-trip test on a memory with every KEEP field non-default.
- **Deltas:** `{"set": [[path, value], ...], "del": [path, ...]}`, with paths as JSON lists of at most two keys
  (`["world", "maps", "<map key>"]`, `["goals", "talked"]`); a value at depth 2 is replaced whole. `rebuild(save_id)` follows
  `parent` back to a full line and applies the deltas forward. After a continue from save k, the next save's parent is k,
  so lines of an abandoned branch are never on a chain again, and the file is never rewritten.
- **The restore table (D16),** each row KEEP or RESET with its reason. The builder fills the remaining fields the same way;
  an unclassified field fails `test_every_goal_memory_field_is_classified`.
  - KEEP (experience, the same at the save as a person would remember it): `talked`, `tried_items`, `item_tries`,
    `catch_maps`, `chat_drawn`, `asked_rounds`, `fight_prep`, `sightings`, `pages`, `looked`, `detoured`, `seen_levels`,
    `last_map`, `no_balls`, `home_heals`, `scene_walls`, `again`, `break_stops`, `exhausted`, `blocked`, `center_looked`,
    `explored`, the new `saved_for`, `last_save`. (`landmarks` and `spoke` ride in the world memory, as today:
    `mode.py:389-393`.)
  - RESET (per-process loop guards, clocks and reports): `fails`, `cooldown`, `decisions`, `known_before` (recomputed at the
    session's first decision, `brain/goals.py:1162-1164`), `aside_from`, `passed_new`, `spent`, `curious_since`,
    `curious_row`, `idle`, `decided_with_party`, `danger_again`, `hearing`, `lost_end`, the new `save_due`.
  - `PersonalityState`: keep `base`, `favourite`, `history`, `draws`; set `active = base`, `drift_until = None`,
    `next_draw = DRIFT_EVERY` (drift counts the navigator's per-process steps, `personality.py:194-212`). `BattleMind`: keep
    `wishes`, `met`, `wild_met`. `report["losses"]` starts at the payload's `losses` (T5). The navigator's `battle_log`
    stays per process (recon-refute W4); `_count_losses` counts new losses on top of the restored count.
- **The frame base** (D7): `1 + max(frame of every line)`; `HandsBrain` wraps the eyes it is given when the base is not 0.
- **The registry (L3 a-b, D15):** updated by a hands watcher from every look with a party. Its `how` is `starter` for the
  first Pokemon of the game, `caught` when the battle log's last outcome is "caught" as it first appears, else `joined`.
  It is written in every save's payload.
- **The restore record (NEW, finding F2):** right after a successful restore and BEFORE the first post-continue look, the
  brain writes (a) the `session` line with `restored_maps`, and (b) a `world.jsonl` snapshot through `_save_world("restored
  from save <id>")` (`mode.py:960-963`). The live proof grades the memory the brain ACTS on from these two records, never
  from a later snapshot (CLAUDE.md rule 7).

### (d) POLICY: `ai_player/brain/saving.py` (new, framework-free, deciding code)

- `SavePolicy` holds no state of its own (its state is `_Memory.save_due`, `saved_for`, `last_save`). It answers:
  `after_heal(goal, ok, here_const)`, `after_milestones(passed_ids)` (ids only, D18), `before_leader(look, world,
  milestone, step, story_goal)`, and `may_save(look, frames_left) -> (bool, why)`.
- **Due** (D3): the newest reason wins, and one save satisfies every due. The centre due expires on leaving the centre
  map. The leader rule is checked in block 8 (D3).
- **May save** (every condition must hold, else the reason is told once per due):
  - `look.progress.play_time` was read (else "the play time is not read");
  - the play time is at least `SAVE_MIN_MINUTES` (3) past `last_save.play_time`;
  - at least `SAVE_FRAMES_NEEDED` (3000) frames are left in the run's budget (`_bounded`'s counter, which the brain
    exposes as `frames_left`);
  - the decision look is free: the goal machinery's own checks (`mode.py:504-516`, `:532-547`). In battle, in a scene,
    with a box or a menu up, or on the frame of an arrival (`SETTLE_FREE`), no goal is chosen at all.
- **Order in `next_goal`:** 1. HEAL (a hurt party heals first: a person heals at the centre, then saves there); then the new
  1b. SAVE for a centre or big-moment due; then the rest unchanged, with the leader check inside 8. STORY.
- **The end save:** in `_play`, inside the first `if milestone is None or index > target:` block, as its LAST line after
  `yield from self._settle_before_done(...)` (`mode.py:480-485`), a new `yield from self._save_before_done(...)` saves if a
  save is due, `report["settle"]["free"]` is true and the budget allows. The end record (`_end_screen`, `:775-792`) gains
  `saved_at_end`. The done check's two lines stay byte-identical (mutant G226's anchor, `revert_step5.py:1010-1013`); the
  builder re-runs every R5 mutant whose anchor is in that block and shows each still mutates and is CAUGHT.
- **At most:** one save per due, no two within 3 game minutes, and a failed save goal falls under
  `FAIL_LIMIT`/`COOLDOWN_DECISIONS` like any goal.
- `GoalRunner.pursue` (`brain/goals.py:1789`) handles `kind == "save"` by calling `runner.saver(goal)`, which the play brain
  sets to its `_save(hands, goal.reason)` (the memory file is the brain's). A skill result that starts `stuck:` ends the
  run through `_play_end` "stuck". The report gets `report["saves"]` and a `spent["save"]` key (graders: section 7, T4).
- **The save ui outside the skill** (`_story_menu`, `mode.py:640`; D13): `save_dialog` → wait with no press, at most
  `SAVE_WRITE_BUDGET + SAVE_CLOSE_BUDGET`, then report it unhandled; `save_yes_no` → B (NO), told; a `start_menu` that takes
  input → B (close it), told. Each is bounded and logged. With the skill as specified these should never fire; they are
  the loop's guard against a skill bug, and the loop never presses A on a save page.

### (e) HOST: restart, CONTINUE, the `.ss1`, and ruling 52

- `__main__.py` `_parser` (`:51-70`): `--continue` joins the `--fresh | --state` mutually exclusive group (`:58-60`).
- `host/launcher.py`:
  - `seed_profile(profile_dir, state, fresh, continue_game)` (`:179-209`) gains the continue branch (D11) and the archive
    (D10);
  - a new `memory_check(game_dir) -> (ok, header, why)` reads `memory.jsonl` and `launches.jsonl` read-only (version,
    save lines, D12 (a)'s classification, the D12 (e) count);
  - `cmd_run` adds `AI_PLAYER_MEMORY` (from `AppPaths`) and `AI_PLAYER_CART` (D17) for every run, and `AI_PLAYER_CONTINUE=1`
    for `--continue`. It prints `[AI-RUN] state: CONTINUE (current_state.ss1 removed; memory <path>, its newest save h:mm;
    the last run ended: <class>; this continue undoes N battles lost after that save)`. After `run_child` returns, it
    appends the `launch_end` line (D20).
  - Every refusal is the existing "cannot start" path (`cmd_run`, exit 2) with a plain sentence.
- `options.py`: `ENV_MEMORY = "AI_PLAYER_MEMORY"`, `ENV_CONTINUE = "AI_PLAYER_CONTINUE"`, `ENV_CART = "AI_PLAYER_CART"`,
  `ENV_FAULT_NO_SAVE = "AI_PLAYER_FAULT_NO_SAVE"`; `HandsOptions.memory_file`, `.continue_game`, `.cart`, `.fault_no_save`.
  `continue_game` together with `world_in` is an options error (D19).
- `mode.py`:
  - `HandsBrain.play` (`:302-334`): with a memory file, open it first (refuse a newer schema: end "stuck: the memory file was
    written by a newer program"). In continue mode the personality is the header's (passed as the forced choice to
    `pick_personality`, `:310`), `_start_world` is NOT called before the skill (`:314-315`), and the eyes are wrapped with
    the frame base.
  - `_skill` for `play` in continue mode runs `continue_game` first. A stop ends the run through `_play_end` "stuck" (so
    the end record and the `end` line are written). Success → `_start_world(..., restored world)`, the restore record
    (section (c)), and `_play(..., restored=...)`, which sets `manager.memory`, the personality state, the battle mind, the
    registry and `report["losses"]` from the payload. The title branch (`mode.py:488-496`) never runs `play_intro` in
    continue mode.
  - The `end` line is written in `HandsBrain.play` after the outcome, for every play-brain run with a memory file:
    `chosen` = the outcome starts `done:` or `stuck:`; `budget` = it starts `stopped:`; `at_save` = the last thing the run
    did was a successful save. The `lost` line is written in `_count_losses`.
- `host/controller.py`: D12 (b).
- `gates/check_purity.py`: D12 (c); the new modules in its tables (section 7).
- **What is done with the `.ss1`:** `--continue` deletes `current_state.ss1`. `states/*.ss1` (never auto-loaded,
  `launcher.py:200-204`) are left. The framework still writes one at a clean exit (`libmgba.py:159-160`), but it is never
  read for an AI game: a no-flag start is refused (D10) and `--continue` deletes it.
- **Who restarts a killed run:** the operator (or a future supervisor, narrowed in section 9) runs `py -3.12 -m ai_player
  run --profile NAME --continue ...`. Nothing in the package starts a process (`subprocess` is a launcher-side library only:
  `check_purity.py:472` `LAUNCHER_LIBRARIES`).

### (f) What the AI does on each title outcome

| the title shows | the AI | memory |
|---|---|---|
| CONTINUE, TIME = its newest save (within 1 minute) | CONTINUE; verify the arrival; play on | as of its newest save |
| the CORRUPTED page, then CONTINUE | reads the page (note), A; CONTINUE; verify; tells "the previous save was loaded" | as of THAT older save (matched by TIME) |
| CONTINUE with an older TIME and no page (the measured silent window) | CONTINUE; verify; tells "an older save than its last, with no page" | as of that older save |
| the ERASED page, then NEW GAME only | reads it; A; STOPS "the save is gone: <words>" | unchanged; a session line and a chosen `end` line (so no later continue) |
| no CONTINUE, no page (a first save cut in its first sector) | STOPS "the save is gone: the main menu offers no CONTINUE" | the same |
| CONTINUE, TIME matches no record | STOPS "a save it does not remember making" | unchanged |
| the arrival differs from the record | STOPS "not the save it remembers" | unchanged |

Never a silent NEW GAME. No stop path presses anything once the main menu takes input; a unit test counts the presses.
The A on an error page is pressed while `Task_WaitForSaveFileErrorWindow` runs, before the main menu takes input, and is
not in that count (finding N1, proof).

## 4. Unit tests (a FAULT and a CONTROL for every guard)

New file `ai_player/gates/test_saving.py` (offline, seconds; in the quick lane), using the fake-screen seams of
`test_goals.py` (`_LoopHands`/`_LoopPad` `:776-827`, `_ScriptEyes` `:1584`) and synthetic task dicts for `read_ui`.

- `EyesSaveTests`:
  - `test_start_menu_takes_input_under_task_show_start_menu` (F: `Task_ShowStartMenu` unknown, no view; C: kind, options,
    cursor, accepts True);
  - `test_start_menu_building_takes_no_input`, and `test_a_stale_callback_never_reads_as_input` (finding G1): a stale
    `HandleStartMenuInput` under `StartMenuTask`, a stale `SaveCallback` under `Task_ShowStartMenu` with `data[0] == 0`,
    and a stale input `save_callback` under `StartMenuSaveCallback` and `SaveStartCallback` each read as not accepting
    (C: the fresh values read as accepting);
  - `test_save_question_is_a_save_yes_no_with_its_cursor` (both callbacks, cursor 0 and 1);
  - `test_save_pages_are_a_save_dialog_that_takes_no_input`; `test_a_scene_yes_no_is_not_the_save_yes_no`;
  - `test_main_menu_carries_the_continue_windows_time` (C: type 0 has none);
  - `test_save_page_words` and `test_error_page_words` (each page, the WARNING with its paragraph marks folded, the
    battery page; a prefix of SAVING is "printing"; other text is None);
  - `test_the_error_window_is_read_from_printer_7` (F: printer 0's stale text under `Task_WaitForSaveFileErrorWindow` and
    under `Task_WaitForBatteryDryErrorWindow`; C: printer 7's string);
  - `test_the_play_time_is_not_in_seen_now` (a minute tick leaves `seen_now` equal; C: a money change does not).
- `SaveSkillTests`:
  - `test_start_only_on_a_free_screen` (F: a scene, no press; C: free, START);
  - `test_each_question_read_before_yes`;
  - `test_overwrite_yes_only_when_the_cart_is_its_own` (F: `kept` and no save this run → NO; C: `empty`, `continued`, or
    saved earlier this run → YES);
  - `test_the_warnings_pages_are_turned_then_no` (three paragraph waits each get one A after reading; then NO; then B on
    the menu; the screen free at return);
  - `test_an_unread_question_is_never_answered_yes`;
  - `test_every_no_backs_out_to_a_free_screen` (findings G4, F3: after each NO path, the START menu reopened by the fake
    screen is closed with B; the return comes only on a free screen; the B presses are counted);
  - `test_no_yes_with_too_few_frames_left` (finding F10: `frames_left() == COMMIT_FRAMES_NEEDED` → YES;
    `COMMIT_FRAMES_NEEDED - 1` → NO, backed out);
  - `test_the_write_is_waited_out_with_no_press` (300 unchanged frames: no press, no stuck);
  - `test_a_write_that_never_ends_is_bounded` (900, still no press, the result `stuck:`);
  - `test_the_stamp_is_the_full_saving_pages_play_time` (F: a partial page, no call yet);
  - `test_the_save_line_is_written_at_the_start_of_the_write` (finding F8, D5: the fake game is cut between the SAVING
    page and the SAVED page; the line is already in the file. F: with the line at SAVED, it is not);
  - `test_the_play_time_is_checked_through_the_write` (finding F8: F, a play time that changes during the write is told;
    C, a still one is not);
  - `test_saved_only_on_the_saved_page` (F: the box closes with no SAVED page, not saved);
  - `test_a_save_error_is_read_and_closed` (finding G2: two waits, two As, a free screen, "not saved: the game said: Save
    error. Please exchange the backup memory.");
  - `test_back_out_with_b_only_while_it_takes_input` (C: never a press once SAVING appeared);
  - `test_no_save_without_save_on_the_menu`.
- `ContinueSkillTests`:
  - `test_continue_only_on_a_time_match` (F: no match → STOP, zero presses once the main menu takes input);
  - `test_never_new_game` (no CONTINUE: STOP, zero presses); `test_the_erased_page_is_read_and_stops`;
  - `test_the_corrupted_page_continues_the_older_save`; `test_a_silent_older_save_is_found_by_its_time`;
  - `test_the_arrival_is_verified` (F: tile, map or a PID differs → STOP; C: equal → continued);
  - `test_the_arrival_is_a_held_free_screen` (one free frame then a scene is not an arrival);
  - `test_one_minute_tolerance_and_the_newest_wins`, including an abandoned-branch record within a minute of a newer one
    (the newer, later in the file, wins; finding N2, game-host);
  - `test_the_continue_tells_the_losses_it_undoes` (two `lost` lines after the matched save → the sentence names 2).
- `MemoryFileTests`:
  - `test_the_header_is_the_first_line_with_schema_1`; `test_a_newer_schema_is_refused_byte_identical`;
    `test_no_header_is_refused`; `test_a_torn_last_line_is_ignored` (C: a torn middle line is refused);
  - `test_delta_round_trip` (apply(parent, diff(parent, child)) == child on payloads recorded from a dev run);
    `test_full_every_8`; `test_rebuild_follows_the_parent_across_a_continue` (S1, S2 abandoned, S3 with parent S1);
  - `test_the_restore_is_not_newer_than_the_save`; `test_every_goal_memory_field_is_classified` (F: a field added
    unclassified fails); `test_each_keep_field_survives_the_restore` (finding F8: every KEEP field non-default before,
    equal after); `test_goal_memory_round_trip`; `test_the_frame_base_exceeds_every_stamp`;
  - `test_mons_by_pid_and_species_with_roles` (evolution keeps the PID; an unknown role is refused; `where` has only
    `map` and `tile`);
  - `test_the_end_line_says_chosen_budget_and_at_save`; `test_a_lost_line_per_loss`;
    `test_the_loss_count_is_restored` (restored 2, one more loss with `MAX_LOSSES` 3 ends the run);
  - `test_an_unwritten_save_line_ends_the_run` (F: `written` did not rise → the run ends stuck; C: it rose).
- `PolicyTests`:
  - `test_due_after_a_heal_at_a_center` (C: MOM's heal, none); `test_the_center_due_expires_on_leaving`;
  - `test_due_after_each_big_moment` (C: `ch1_truck`, none); `test_big_moment_ids_exist`;
    `test_after_milestones_receives_ids_only` (finding m5);
  - `test_a_save_right_before_the_leader` (finding m2: the story goal is the leader talk on the gym map → a save goal in
    its place. C: `ch2_dad`'s gym talk and the rival's named fight, none. Enter, save, leave to train, return → a second
    save before the talk. A centre save within 3 minutes before → no second save);
  - `test_three_game_minutes_between_saves` (F: 2, refused; C: 3, allowed); `test_no_save_without_play_time`;
    `test_no_save_without_frames_left`.
- `LauncherContinueTests` (no emulator: temp profile folders):
  - `test_continue_removes_the_ss1_and_keeps_the_sav`; `test_continue_refused_without_memory`, `_without_a_sav`,
    `_on_a_foreign_profile`, `_with_a_world_file_set` (D19);
  - `test_the_end_classes` (finding M1/M2, one case per row of D12 (a)'s table: no verdict → allowed; `crash` → allowed;
    `play: done:` not at a save → refused, at a save → allowed; `play: stopped:` not at a save → refused (F: the draft's
    rule allowed it), at a save → allowed; `wall-clock` and the launcher's hard kill → refused; `stray-exit` →
    refused; a missing `run_dir` → refused; a CHOSEN reason with no `end` line → refused; a harness session with no
    `end` line → allowed);
  - `test_the_launcher_writes_its_launch_end_line` (exit code, `hard_kill`, the verdict's reason);
  - `test_fresh_archives_the_memory` (never deletes); `test_no_flag_start_refused_when_memory_exists` (finding F8);
  - `test_a_newer_memory_is_refused_byte_identical`; `test_every_run_gets_the_memory_path_and_the_cart`;
  - `test_the_cart_is_told` (`--fresh`/`--state` → `empty`, `--continue` → `continued`, no flag → `kept`).
- `PathsTests`: `test_dev_default_is_beside_the_cartridge`, `test_home_override`; and the gate:
  `test_the_gate_fails_on_a_planted_literal` (F) and `test_the_gate_ignores_docstrings_and_comments` (C),
  `test_the_tree_passes`.
- `HarnessInputRuleTests` (E7, finding F7): a synthetic task/callback record of the 261-frame write under
  `Task_ShowStartMenu` + `SaveCallback` + `SaveDoSaveCallback` is NOT counted as waiting for a press (F: the old rule with
  `Task_ShowStartMenu` counted as input → 261 frames counted); `HandleStartMenuInput` and the two yes/no callbacks ARE
  counted (C); a stale `HandleStartMenuInput` under `StartMenuTask` is not.
- `gates/test_host.py`: `test_start_or_select_never_with_another_button` (F: A held + a tap of START, and B held + SELECT,
  raise `ControllerError`; C: B held + Up, the run; one button after another).
- `gates/test_check_purity.py`: `test_the_play_loop_cannot_exit` (F: a planted `sys.exit()`, `raise SystemExit`, `exit()`,
  and `except KeyboardInterrupt` in `brain/` each fail; C: the same words in a docstring or comment pass; `host/lifecycle.py`
  keeps its `sys.exit`).
- `gates/check_fairness.py`'s own tests: `PLAY_TIME_DOORS` (F: a planted `.play_time` read in `brain/goals.py` fails; C: a
  docstring mention passes; the listed doors pass).
- `gates/test_goals.py` `PlayLoopTests` (the loop wiring): `test_a_save_goal_after_a_center_heal`;
  `test_no_save_goal_while_hurt`; `test_a_save_before_the_leader_on_each_approach`; `test_the_end_save_when_due` (C: too few
  frames left, no save, said); `test_continue_mode_never_plays_the_intro`; `test_the_end_line`;
  `test_fault_no_save_is_the_old_loop`; `test_a_save_dialog_met_by_the_loop_gets_no_press` (finding F6: the loop meets
  a mid-write `save_dialog` for 300 or more unchanged frames: zero presses, and the run is not ended before the screen
  frees); `test_a_start_menu_left_open_is_closed` (C: one B, told).
- Purity (`check_purity.py`) and fairness (`check_fairness.py`) stay green. The new modules are entered in the gate's
  tables (play-loop side: `game_memory.py`, `skills/saving.py`, `brain/saving.py`; launcher side: `paths.py`). Fairness
  `DECIDING` (`check_fairness.py:56`) gains `game_memory.py`.

## 5. The live proof ("kill, CONTINUE, same PIDs and tile")

**Instrument choice (CLAUDE.md rule 9):** this is a CORRECTNESS question, so a targeted driver with paired arms, not a
sweep. A new TEST-SIDE driver, `gates/live_r1.py` (not in the lane), is built on the probe's parent/child pattern and
helpers (`probe_save_kill.py`: `boot_profile` file-backed, `Timeline` for e3/e4, `parse_image` + `file_verdict` for the
FILE verdict, `printer_page`, `ram_truth`, the PID-only `psutil` kill, the alive census).
- **Child A** is the REAL brain in-process. `play_harness.py` gains `--profile-dir DIR` (file-backed boot), `--memory FILE`
  (ALWAYS the profile's `AppPaths` path) and `--continue`. It starts from a NEW GAME on a throwaway marker profile
  `ai-r1live-<arm>-<seed>` under `<build_root>/profiles/`.
- **The fresh cart is asserted (finding F14):** before child A boots, the driver checks that the profile has no
  `current_save.sav` or an empty one, and no `current_state.ss1`. Otherwise the arm is refused, not run. The silent window
  exists only in a fresh cart's first two saves (probe §0), and a cart holding a save would show the WARNING (D17).
- Child A runs with the cartridge clock pinned (`--game-clock 2026-10-14T10:00 --clock 10:00`, as R5 and the probe),
  target `ch1_pokedex`, and `--frames 330000`. A test-side per-frame watcher finds each save's e3 and e4 (the probe's
  `Timeline`). At the arm's frame it prints READY and blocks (bounded by `BLOCK_SECONDS` 120, `probe_save_kill.py:151`),
  and the parent kills that PID.
- **At the kill, the parent FREEZES the profile (findings G6, F12):** it copies `current_save.sav`, `memory.jsonl` and
  `launches.jsonl` (if present) into `frozen/<arm>-<seed>/` before any child B runs. Every child B runs on its OWN copy of
  that frozen set. So no child B can change what another reads, and LAUNCH sees the cart and memory exactly as the kill
  left them.
- **Child B** is the AI continuing: in-process, the same brain, with the launcher's `seed_profile` continue branch and
  `memory_check` called first, so the arrival is read by a SECOND PATH (`ram_truth` on a held free overworld). It stops
  at its held free arrival plus 600 frames: `--frames` = `CONTINUE_BUDGET + ARRIVAL_BUDGET + 600` (finding F13).
- **Timeouts (finding F13):** the child A timeout is 2x the longest wall time step 6 measured to that arm's kill point
  (never under 1200 s); the child B timeout is 2x step 6's longest continue (never under 300 s). Both are registered
  numbers.

**The arms, the discriminator computed from the probe's numbers before any run** (FR4: write 256-261 frames; the first
sector complete at e3+19 for save 1 and e3+18 for save 2; flush at e4+16):

| arm | kill at | why that frame | FILE expected | what the AI must show |
|---|---|---|---|---|
| CONTROL | none | PF-17 | the newest save | every save at a ruling-51 moment (check 6); the run ends `done` at `ch1_pokedex` with its end save |
| K-AFTER | S2.e4 + 40 | 24 frames after the flush, inside D5's [e4, e5) (probe K2: S2 / S2) | S2 | no page; CONTINUE; arrival = S2's truth; restored = save 2 |
| K-INSIDE | S2.e3 + 130 | 6-7 of 14 sectors done (KM-SECOND@130: S1+ERROR) | S1+ERROR | reads the CORRUPTED page; CONTINUE; arrival = S1's truth; restored = save 1 |
| K-SILENT | S2.e3 + 9 | inside the silent window [e3, e3+17], between the measured silent offsets @2 and @17 (FR5 `:462`) and 8-9 frames from each edge, so the AI's S2 line (written at about e3) is in the file first (finding G7) | S1 | NO page; matches S1 by TIME; arrival = S1; restored = save 1 |
| K-FIRST | S1.e3 + 128 | 6-7 sectors of the FIRST save (KM-FIRST@128: CORRUPT) | CORRUPT | reads the ERASED page; STOPS "the save is gone"; zero presses once the main menu takes input |
| K-BETWEEN | halfway between S1.e7 and S2.e1 (finding N3, proof) | the ordinary deployment kill: no write under way | S1 | no page; CONTINUE; arrival = S1; restored = save 1; memory has nothing newer |
| LAUNCH | K-AFTER's frozen copy, plus a stale `route101_south.ss1` planted as `current_state.ss1` | the real launcher drops the `.ss1` | S2 | through `-m ai_player run --continue`: the first look is a COLD BOOT (finding G5): not OVERWORLD, its emulator frame (log frame minus `frame_base`, T6) under 300, then the intro or title before any CONTINUE; CONTINUE; purity CLEAN; its session line names save 2 |
| LAUNCH-OLD | the same, with mutant S27 (`--continue` keeps the `.ss1`) (finding N2, proof) | the OLD half measured through the real launcher, not borrowed from the probe | S2 | the first look is the ROUTE101 overworld at an emulator frame of 66883 or more (the fixture loaded) |
| K-INSIDE-OLD | K-INSIDE's frozen copy, child B with mutant R1-M | the A/B on the SAME killed cart and memory | S1+ERROR | memory NEWER than the save: check (3) FAILS |
| K-SILENT-OLD | K-SILENT's frozen copy, child B with mutant R1-M (finding G7) | the A/B of D4's TIME match itself: here no page tells the AI anything | S1 | memory NEWER than the save: check (3) FAILS |

Mutant R1-M is "restore the newest save line, with no TIME match and no arrival check" (the pre-R2 rule of `read_world`),
applied to child B only, in a temp tree, the way `revert_step5.py` applies mutants. Because every OLD arm reuses its NEW
twin's frozen copy, it needs no extra New Game.

**Graded, per arm, by the second path only:**
1. The FILE verdict of the frozen `.sav` equals the table (the REACH floor, PF-4: an arm whose file does not show it is
   reported, not counted).
2. At child B's held free arrival, the party's PIDs, the map and the tile equal child A's truth recorded at the loaded
   save's e4 (the probe's `slot_at_e4_*_equals_truth`). The play time read at child B's boot equals that save's.
3. **The memory check:** `NEW` = the maps child A first stood on (its RAM record) after S1.e3 and before S2.e3. The world
   memory child B restored is the `world.jsonl` snapshot written at the restore ("restored from save <id>", section (c);
   finding F2), and it must agree with the session line's `restored_maps`. It must contain NO map of `NEW` in K-INSIDE,
   K-SILENT and K-BETWEEN, and ALL of `NEW` in K-AFTER.
4. The action log: CONTINUE pressed by the AI with its cursor gate; no NEW GAME press in any arm; the page's words in a
   `read` note for K-INSIDE and K-FIRST; for K-FIRST, zero presses once `ui.kind == "main_menu"` takes input (finding N1,
   proof).
5. At the moment each of child A's saves began, the harness's own free read (`probe_end_screen.game_screen()["free"]`,
   held) was true and no battle ran; consecutive stamps are at least 3 game minutes apart.
6. **(NEW, finding F11 (b)) Each of child A's saves happened at a ruling-51 moment, by the harness's own reads:** a map
   whose const ends `POKEMON_CENTER_1F` with every party member at full HP; or the gym map of a named leader's milestone
   with the next script the leader's; or within the frames of one decision after a `BIG_MOMENTS` milestone's proof turned
   true (read from `knowledge/milestones.json`'s proofs with the harness's own flag reads). No save anywhere else.
7. **The precondition of the A/B (finding G7):** for K-INSIDE and K-SILENT, S2's `save` line is in `memory.jsonl` with a
   `frame` below the kill frame. Otherwise the arm is reported, not counted (without that line, "the newest record" and
   "the TIME match" give the same answer and the arm would prove nothing about D4).

`NEW` must not be empty: compute it on every development seed first. A seed with an empty `NEW` is not counted for
K-AFTER, K-INSIDE, K-SILENT, K-BETWEEN and their OLD twins (reported).

**Counting, floors and the one verdict (finding F1):**
- An arm COUNTS on a seed when its reach conditions hold: (1) passed, `NEW` not empty where (3) needs it, (7) held where it
  applies, and child A reached the kill point. An OLD arm counts on a seed only when its NEW twin counts there. LAUNCH and
  LAUNCH-OLD count when K-AFTER's FILE verdict was S2 on that seed.
- **Floors:** every arm must count on at least 3 of the 4 held-out seeds.
- **VERDICT: PASS** when every arm meets its floor, every counted NEW arm passes all its checks, and every counted OLD arm
  FAILS check (3) (LAUNCH-OLD: shows the fixture's overworld first). **FAIL** when any counted NEW arm fails any check, or
  any counted OLD arm does not show the difference it exists for (the check cannot see the defect it was built to catch).
  **INCONCLUSIVE** when nothing failed but an arm is below its floor; it is never reported as a PASS.
- **Determinism lines (finding N4, proof):** for each seed, S1's and S2's e3 frames and truths are printed for every child
  A arm and compared. A difference is reported, and each arm is still graded on its own child A's truths. Every arm of one
  seed replays the same New Game up to its kill: one trajectory per seed, replayed (CLAUDE.md rule 8), never "measured
  twice".

**`live_r1.py selftest` (finding F4):** planted faults, each shown to FAIL, plus a clean PASS on recorded data from step 6.
The faults: `NEW` computed empty; the identity compare ignoring the tile; the press census ignoring the main menu; check
(3) reading child B's first map-change snapshot instead of the restore snapshot, on a planted case where child B's first
map change enters a `NEW` map (F2); an OLD arm graded as counted while its NEW twin is not; the verdict rule returning PASS
below a floor.

**Seeds and the ledger (finding F5):** family `story`, driver `live_r1` (`gates/ledger.json`; its newest entries are
#45-#50, seeds 5351-5365, all done). Development: 5401-5406, one development entry (`ledger.begin` with purpose
development) written BEFORE they are played. Held-out graded: 5451-5454, ONE graded entry covering every arm, made with
`ledger.register` (`ledger.py:116`) BEFORE any of them runs, then `ledger.begin` at the run's start and `ledger.finish`
with the one verdict. `live_r1.registered_numbers()` holds: the kill rules (K-AFTER e4+40, K-INSIDE e3+130, K-SILENT e3+9,
K-FIRST e3+128, K-BETWEEN the midpoint rule), the target, the frames, both clocks, the child timeouts and child B's
frames, the expected table, the counting rules and floors, and the sha256 of `live_r1.py`, `play_harness.py` and the
`probe_save_kill.py` helpers it imports (as `rate_step5.py:2877` `HASHED_FILES` does).

## 6. Revert mutants

New driver `gates/revert_r1.py` (the `revert_step5.py` pattern, `:1700-1740`). Its DRIVER runs `test_saving.py`,
`test_check_purity.py`'s new test, the fairness test and the named `test_host` test. Each mutant must be CAUGHT by its
predicted tests:
- S0 control.
- Eyes: S1 `Task_ShowStartMenu` out of `UI_TASKS`; S2 the save's yes/no read as `"yes_no"`; S3 the callback decides
  before the task (G1); S4 no CONTINUE window time; S5 the error window read from printer 0 (F8, E4); S6 the play time kept
  in `seen_now` (D18).
- The save skill: S7 START without the free check; S8 OVERWRITE answered YES on a `kept` cart with no save this run; S9 the
  WARNING answered YES; S10 the save line written at the SAVED page (D5, F8); S11 the write-time play-time assert removed
  (F8); S12 `written` unchecked (F8); S13 an A pressed on the SAVING page; S14 the stamp from a partial SAVING page; S15
  "saved" when the box closes; S16 a NO returns without backing out (F3); S17 no commit check before YES (F10); S18 the
  WARNING's paragraphs not turned (G2); S19 one A on the save error (G2).
- Continue: S20 CONTINUE on the newest record (no TIME match); S21 NEW GAME when there is no CONTINUE; S22 no arrival
  check; S23 one free look taken as arrival.
- The memory file: S24 a newer schema accepted; S25 a torn middle line ignored; S26 deltas drop their deletions; S28
  rebuild from the newest line, not the parent chain; S29 frame base 0; S31 one KEEP field reset (F8); S32 the loss count
  not restored (T5).
- Launcher and host: S27 `--continue` keeps the `.ss1` (also LAUNCH-OLD); S33 the end classes collapsed to the draft's
  "no chosen end line → allowed" (M1, M2); S34 the launcher's `launch_end` line not written (M2); S35 `AI_PLAYER_WORLD`
  accepted in continue mode (m4); S36 `--fresh` deletes the memory; S37 a no-flag start allowed with a memory file (F8);
  S38 the paths gate reads docstrings (its CONTROL must fail: a gate with false positives); S39 the controller allows
  SELECT with another button (G8); S40 the purity gate allows `sys.exit` in `brain/` (M2).
- Policy: S41 the centre due never expires; S42 no minimum gap; S43 the leader rule for any named fight; S44 the leader
  save spent once per milestone, not per approach (m2); S45 `after_milestones` given the marks, not the ids (m5).
- Test side: S30 E7's harness rule counts `Task_ShowStartMenu` as input (F7), caught by `HarnessInputRuleTests`.

Loop-wiring mutants G374 and up in `revert_step5.py`, each deleting one new call (PF-2), CAUGHT by the `PlayLoopTests`
above: the save goal, the end save, the continue branch, the restore, the restore record, the `end` line, the `lost` line,
the registry watcher, and `_story_menu`'s save branches (the loop pressing A on a `save_dialog`: F6). Re-anchor any
existing mutant whose anchor text moves, and show it still mutates the same thing.

## 7. Regression lane and gates impact

- `run_units.py` `SUITES` and `run_regression.py` `QUICK` (`:205-215`): add `test_saving` and `check_paths`; `REVERTS`
  (`:201`) adds `revert_r1`; update `run_regression_times.json` and the suite map that `tools/workflows/regression_due.py`
  reads.
- `check_purity.py`: the new modules in its tables; D12 (c)'s narrowed `sys.exit` and refused names; the pinned `__all__`
  of `host/launcher.py` (new names) and of any host module whose `__all__` changes (`host/controller.py` keeps its four
  names); no new play-loop file writer (`RecordFile` only; `launches.jsonl` is written by the launcher side); `json` on
  `game_memory.py`'s surface; `paths.py` launcher side. `call_census.py`: cover the new call sites or add reasoned waivers.
- `check_fairness.py`: `DECIDING` += `game_memory.py`; the `_milestone_line` door's purpose amended and `PLAY_TIME_DOORS`
  added (D18); no knowledge file changes.
- `test_eyes.py:397` and any `start_menu` expectation: re-check (E1 makes the building menu non-accepting).
- **Graders (not in the lane), decided now (T4; finding F7):**
  - `rate_step5.py` `intent_mix` (`:1086-1112`): spans of kind `"save"` leave the errand share's TOTAL and are reported
    separately as `save_frames`. A save is the player's bookkeeping, neither an errand nor the story's step. `ERRAND_KINDS`
    (`:373-374`, and `brain/goals.py:279`) are unchanged. It is a no-op for every run without a memory file. A unit test
    goes beside the existing `intent_mix` tests. The change moves `rate_step5.py`'s hash (`HASHED_FILES`), so no graded
    range may be left registered and unplayed across it; today none is (ledger #45-#50 done).
  - `rate_step5.py` `AWAIT_MAX` 300 (`:445`) and `await_game_long` (`:1995`): with E7's precise rule the write is not a
    wait for a press (`HarnessInputRuleTests`). The builder re-runs `test_measure_step5.py` and `test_step53_*`.
  - `live_step5.py` runs the real launcher (`:7`), so it now gets a memory file and SAVES. CH2's `--state` start gets
    `cart=empty`, so its OVERWRITE question is answered YES (D17). Its next run is therefore a RE-BASELINE, not comparable
    with earlier graded runs. The orchestrator says so when it is next run.
- The probe (`probe_save_kill.py`) is NOT edited. A new development probe, `gates/probe_save_eyes.py` (step 2 below), is not
  in the lane.
- Before the commit: `regression_due.py`, every due revert driver under about 20 minutes, `run_gates.py --quick`; then the
  full lane by the orchestrator (no edit under `ai_player/`, `06`, `07`, `08` or `CLAUDE.md` while it runs).

## 8. Step order and STOP rules for the builder; size

1. Work in a worktree; the main checkout and the bot tuner's clone are read only. Confirm no lane is running.
2. **Eyes first, then MEASURE them:** E1, E2, E4-E7, then `gates/probe_save_eyes.py` (development). It drives the probe's
   test-side saver (`probe_save_kill.Saver`) on `route101_south.ss1` for three saves, and records the AI's OWN
   `FrameworkEyes` look every frame. It adds the stale-callback sequences G1 names: open the menu, close it with B, open
   it again; SAVE, answer NO, SAVE again, answer YES; open the menu after a successful save. Its continuer runs on a TRUNC
   and a KM-FIRST profile, recording the AI's looks at the title. It must show:
   - the start menu's view taking input with the right cursor, and NOT taking input on every stale-callback frame;
   - the save yes/no with its cursor, and each page's words;
   - both error pages' words from printer 7;
   - **(finding F9) the AI's `play_time` and the CONTINUE `(hours, minutes)` equal to the harness's own RAM truth on every
     recorded frame, including a frame where the minute ticks; and the play time unchanged through each write;**
   - the YES-to-free span with the AI's pacing (for `COMMIT_FRAMES_NEEDED`).
   **STOP** if any of these is unreadable or disagrees with the harness's truth, or if a still stretch in the dialog exceeds
   900 frames: re-derive the bound from the record, never guess.
3. `game_memory.py`, `paths.py`, `check_paths.py` and their tests (offline).
4. `brain/saving.py`, `skills/saving.py` and their tests.
5. The loop (`mode.py`, `brain/goals.py`), `options.py`, the launcher (with `launches.jsonl`), the controller, the purity
   and fairness changes, the gate tables; the unit suites and both revert drivers green.
6. **Development live runs on 5401-5406** (the ledger entry first):
   - (a) **The no-memory A/B (finding F11 (a)):** on seed 5401, the in-process harness without `--memory` on the pre-R1
     tree (HEAD before the build) and on the R1 tree. The action logs must be identical (decisions, presses, frames), or
     each difference is named and explained. **STOP** on any unexplained difference: D14's "nothing moves without a memory
     file" is then false.
   - (b) On 5401-5404, with `--memory`: measure the saves per run, their moments (check 6), the dialog's frames with the
     AI's pacing, line sizes, the saves per game hour (T2), how often the stamp's look comes before the clock freezes (T1),
     and compute `NEW` and the S1/S2 identities per seed.
   - (c) **Kill/continue rehearsals (finding F4):** K-INSIDE, K-SILENT, K-FIRST and K-BETWEEN with their child Bs, on 5405
     and 5406, with `live_r1.py`'s grader run on them. From these, set `CONTINUE_BUDGET` and `ARRIVAL_BUDGET` (2x the
     longest AI continue seen), the child timeouts, and the recorded data for the selftest's clean PASS.
   - **STOP** and report if fewer than 2 saves happen before `ch1_pokedex` on 2 or more seeds, or `NEW` is empty on 2 or
     more: pick another target with the orchestrator (for example `ch2_wally`); do not tune the policy to the proof.
   - **Ruling-51 coverage, said plainly (finding F11 (c)):** the big-moment saves are exercised live on this target. A
     centre save is exercised live only if a run heals at a centre before `ch1_pokedex`; the leader save (`ch4_roxanne`) is
     proven by unit tests only. The hand-back reports which moments were seen live.
7. `live_r1.py selftest` green. Then `register` 5451-5454 with `registered_numbers()`, run section 5's arms, and report the
   one verdict. Then an independent adversarial review and a fix round (any fix re-runs the affected arms on NEW seeds,
   registered first).
8. Hand back: the diff, the evidence files, the numbers. The orchestrator writes the docs, `06` (D1-D20, the rulings'
   technical reading as refined by D12, and the narrowing of R7 and R15, section 9), `07`, and commits.
- **STOP rules throughout:** a measured value that contradicts the probe report → stop and report, never tune; a recon
  claim the code contradicts → the code wins, say where; no `git add -A`, no destructive git, no commit; never touch
  `sandbox-pokebot/` code, `custom-pokebot/`, `40cakes repo/`, the probe, or the tuner's clone and processes; never change
  the BOT's behaviour.
- **Size (an estimate, against the backlog's "300 + 200"):** new AI and host code about 1,550 lines (eyes 130, skills
  360, policy 120, memory file 320, loop and goals 200, launcher, options, paths and controller 300, purity and fairness
  rules 60, gate tables 60). Test side about 2,600 lines (unit tests 1,350, `live_r1.py` 750 with its selftest,
  `revert_r1.py` 300, `check_paths.py` 90, `probe_save_eyes.py` 200, harness changes 80). The backlog's figure predates the
  measured save timing, the silent window, DP1 + DP2, L3, and ruling 52's enforcement. This is the honest size of the
  smallest design that meets them.

## 9. Out of scope (and what was cut)

- RULING 52's exception (a save in front of a stationary legendary, reloaded after running out of Poké Balls): deferred by
  the user until the AI fully works. No code path, no switch. D12 (a) refuses a continue after a CHOSEN end, which is
  exactly that reload, so building it later is a deliberate change to D12 with its own user-approved rule.
- **R7 and R15 are NARROWED by ruling 52 (finding m6; the orchestrator updates the backlog lines with the `06` entry):**
  - R7's get-unstuck ladder loses its rung "quit and CONTINUE from its own save" (`2026-10-19-backlog-round2/03-ai-player.md:141`):
    a chosen quit followed by a continue is a reload, and D12 (a) refuses it in code.
  - R15's supervisor (`2026-10-18-improvement-backlog.md:353`, "relaunches from its save on benign exits") may relaunch
    only after the KILLED and INVOLUNTARY classes of D12 (a), never after a CHOSEN end, a NOT CLEAN end, or (until U2 is
    answered) a BUDGET end. "Benign" by exit code is not the rule: exit 0 includes `done:` and `stopped:`.
  - recon-record `:513` already named both.
- L3 (c)-(d): assigning roles, boxing by role, the PC skill; Pokemon seen only in a box.
- R8 + R9 (AI-made states, checkpoints), R6 (unknown screens), R11 (a defeat ledger; the `lost` lines are its raw record,
  not R11).
- Cut from this design, each with its reason in section 2: migrating an older memory schema (none exists, D9); a save timer;
  the full play-time counter; rewriting stamps across a cold boot (D7); a supervisor that restarts killed runs by itself;
  a soft-wall-deadline guard on saving (the brain is not told the deadline, `host/session.py:305-310`. A save cut by it
  leaves the previous save and its memory, and the run's BUDGET end then refuses a continue unless the user rules
  otherwise in U2); replacing `world.jsonl` (the graders read it).
- A power cut, an OS crash, another text speed, a fourth save: not measured by the probe (FR8) and not claimed.

## 10. Open questions

**Technical: all DECIDED in this revision (each goes to `06` with its rejected alternative):**
- **T1. The stamp: one look, a 1-minute tolerance, and the arrival check.** Rejected: two agreeing looks after the page
  completes. That delays the line by a frame into the write, shrinks the K-SILENT margin, and buys nothing the arrival
  check does not give: the probe saw the clock already still on the frame before the printer went idle (§3). Step 6 (b)
  records how often the first look precedes the freeze, and step 2 checks the stamp against RAM truth (F9).
- **T2. `SAVE_MIN_MINUTES = 3` for every moment; no separate centre gap.** Ruling 51 names the centre itself, so a
  personality that heals more often saves more often, as a person who visits more centres would. Step 6 (b) reports saves
  per game hour. Rejected: a longer centre gap now (no measurement asks for it, and it would make centre saves rarer than
  the ruling's words).
- **T3. `BIG_MOMENTS`:** the list in D3 stands, with the user's U1 open; it is one constant.
- **T4. The errand share leaves `save` out of its total** (section 7). Rejected: counting `save` as an errand (it would
  inflate the errand share by about 1,000 frames a save, which the intent mix was never meant to measure); leaving it in
  the total as non-errand (it would lower the share with no change in behaviour).
- **T5. The loss count is carried in the save payload** (`losses`), so `MAX_LOSSES` counts across processes as of the
  save; the navigator's `battle_log` stays per process. Rejected: a per-process reset (every kill would hand the AI a fresh
  allowance of losses: a guard that weakens with each kill).
- **T6. Frames:** the frame base is 0 except in a continue run, and every continue run's `session` line records it (and
  the `[AI-HANDS]` start line prints it). A grader comparing the AI's frames with the emulator's subtracts it; `live_r1.py`
  does. Rejected: logging both frames on every record (every grader's parser would change for a field only continue runs
  need).
- **T7. `--continue` with a memory file but no `.sav` is a plain launcher refusal** naming the missing file. Rejected:
  running it so the AI reads the title (the same STOP, a boot later, and a missing `.sav` is a disk or operator error the
  launcher can name exactly).
- **T8. The end save's place:** inside the first `if milestone is None or index > target:` block, as its last line (section
  3 (d)); the done check stays byte-identical; the R5 mutants anchored in that block are re-run and shown CAUGHT.

**User (goals and design only; the build does not wait for either answer):**
- **U1.** "After a big story moment": the build will save after getting the starter, after the first win over the rival,
  after receiving the POKéDEX, at the end of WALLY's catching tutorial, after saving the DEVON researcher from the TEAM
  AQUA GRUNT in PETALBURG WOODS (he gives a GREAT BALL as thanks), and after winning the STONE BADGE. Is that the right
  list, or would you save after other moments too (or skip some of these)? The list is one constant that is easy to change.
- **U2.** When a play session ends because its time limit or frame limit ran out (not a crash or a kill), should the next
  session be allowed to continue from the last save, undoing whatever happened after it, a lost battle included? Until you
  answer, the build says NO unless the session ended right after a save, and every continue tells how many lost battles it
  undoes.

## 11. Revision log

Every finding was checked against the code or the decomp before it was applied or rebutted. IDs as the critics gave them;
where two critics used the same id, the lens is named.

| finding | verified | what was done |
|---|---|---|
| G1 | yes: `src/start_menu.c:566-573`, `:629-634`, `:809-815`, `:823-827`, `:877-881`; no write clears either callback | E1 rewritten: the task decides first, `data[0]` checked, `save_yes_no` only under `SaveCallback`; `test_a_stale_callback_never_reads_as_input`; mutant S3; step 2 records the stale cases live |
| G2 | yes: `data/text/save.inc:16-29` (`\p`), `start_menu.c:884-894`, `:1136-1159` | step 4: paragraph pages turned with A (bounded), the WARNING answered NO, the error path presses until free; tests for both; mutants S18, S19 |
| G3 | yes: `start_menu.c:1010-1022`, `:1096`, `new_game.c:141,154`, `launcher.py:196-198`, `live_step5.py:461` | D17 (the cart told by the launcher; YES on `empty`/`continued`/saved this run); `test_the_cart_is_told`; section 7 corrected for CH2 |
| G4 | yes: `start_menu.c:823-827` | every NO backs out to a free screen (step 4, step 7); `test_every_no_backs_out_to_a_free_screen`; mutant S16 |
| G5 | yes: probe report §4 M6 (copyright at 13, intro at 176) | LAUNCH's first look is a COLD BOOT by a pre-registered rule |
| G6 | yes | the profile FROZEN at the kill; each child B on its own copy; `--memory` is the profile's `AppPaths` path (D8) |
| G7 | yes: FR4 (e2 = e3 = 67238) | K-SILENT moved to e3+9 (8-9 frames from each edge, between the measured silent @2 and @17); check (7) grades the S2 line before the kill; K-SILENT-OLD added |
| G8 | yes: `src/main.c:135-137`, `src/title_screen.c:39-41`, `field_player_avatar.c:658` | D12 (b): START or SELECT never with another button; B + a direction allowed; test and mutant S39 |
| G9 | yes: `milestones.json` `ch3_woods`; `PetalburgWoods/scripts.inc:315-316,343-349` | D3 and U1 describe the woods correctly |
| N1 (game-host) | yes: FR4 e3→e5 339-343 | the margin is stated as 2.6x of e3→e5; value unchanged |
| N2 (game-host) | yes | D4 says "newest wins; an abandoned record is always older"; the case added to the tolerance test |
| N3 (game-host) | yes: `main_menu.c:723-737`, `eyes/screens.py:310` | E4 reads printer 7 under both error tasks; test; mutant S5 |
| N4 (game-host) | yes: `host/eyes.py:472` uses `get_symbol`, `:554` `get_symbol_name`; `.sym:6376` | section 3 (a)'s door sentence corrected; `SaveReturnErrorCallback` added to the list |
| M1 | yes: `mode.py:976-977`, `host/session.py:327`, `__main__.py:55-56` | D12 (a): a BUDGET class, refused unless at a save (interim); `lost` lines and the "undoes N battles" sentence (D12 (e)); `test_the_end_classes`; mutant S33; U2 put to the user |
| M2 | yes: `check_purity.py:428-431`; `host/session.py:322-333`; `host/lifecycle.py:138-185` (purity.json `exit_reason`) | D12 (a) classifies from the verdict file and the new launcher-owned `launches.jsonl` (D20), failing closed; D12 (c) purity rule; §0 names what enforces what. **Partly rebutted:** a deliberate `raise` still ends the run as `crash`, which stays allowed (no gate can refuse every raise); it is stated as a limit and told by D12 (e) |
| m1 | yes (the same as G8) | D12 (b) as G8. **Partly rebutted:** the fix is the SELECT/START rule instead of enumerating sets; it covers every listed set with one test |
| m2 | yes: `brain/goals.py:1284-1296` after block 1b; story at `:1351` | the leader save moved into block 8, once per approach to the gym; test; mutant S44 |
| m3 | yes (the same as G9) | as G9 |
| m4 | yes: `mode.py:942`, `options.py:393` | D19: refused in continue mode by the launcher, the brain and the harness parser; test; mutant S35 |
| m5 | yes: `check_fairness.py:82-83` | D18: the door's purpose amended; `test_after_milestones_receives_ids_only`; mutant S45 |
| m6 | yes: round2 `03-ai-player.md:141`, backlog `:353` | section 9 narrows R7 and R15; the orchestrator updates the backlog with `06` |
| N1 (rulings) | yes: `start_menu.c:1385-1388` | D4's wording corrected; D18's `PLAY_TIME_DOORS` and `seen_now` exclusion (it also removes the trajectory risk F11 named) |
| N2 (rulings) | yes: `developer_keys()` | D15 fixes `where` to `{"map", "tile"}`; tested |
| F1 | yes: R5 spec `:97`; ledger #49 | counting rules, a floor of 3 of 4 for every arm, and one PASS / FAIL / INCONCLUSIVE rule (section 5) |
| F2 | yes: `mode.py:949` (snapshots on a map change), `world/memory.py:626-632` | the restore record (section 3 (c)); check (3) grades it; a selftest case for a first map change into `NEW` |
| F3 | yes: `start_menu.c:823-827`; `navigator.py:1094-1097`; `mode.py:104` | as G4, plus `_story_menu` closes a menu left open (D13) |
| F4 | yes: probe report §1 Child B; §2 selftest | step 6 (c) kill/continue rehearsals set the continue budgets; `live_r1.py selftest` with planted faults |
| F5 | yes: `ledger.py:116` `register`, `:147` `begin` | one graded entry for 5451-5454 via `register`; `registered_numbers()` defined (section 5) |
| F6 | yes: `hands/dialogue.py:206-208` before `:222-230` | D13 rewritten and E3 withdrawn (with its test and mutant); `_story_menu` save branches; `test_a_save_dialog_met_by_the_loop_gets_no_press`; a loop-wiring mutant |
| F7 | yes: `play_harness.py:403-408`; `rate_step5.py:445`, `:1995` | `HarnessInputRuleTests` (F/C); mutant S30; section 7 lists the await graders and live_step5 |
| F8 | yes | tests and mutants for D5 (S10), the write-time assert (S11), `written` (S12), printer 7 (S5), the no-flag refusal (S37), a KEEP field (S31); the coarse `SAVE_FRAMES_NEEDED` replaced as the guard by the commit check (S17) |
| F9 | yes: probe report §1 Verdicts, §3 | step 2 compares the AI's play time and CONTINUE TIME with RAM truth on every frame, a minute tick included; STOP on a difference |
| F10 | yes: `hands/menus.py:63-67`, `:120-140` | `COMMIT_FRAMES_NEEDED` checked before every YES (the only press that starts a write); boundary test; mutant S17 |
| F11 | yes: `hands/dialogue.py:121`; spec moments | (a) the no-memory A/B in step 6 (a), with a STOP; (b) check 6 grades each save's moment by the harness's reads; (c) the live coverage of each moment stated. **Partly rebutted:** no STOP when no centre save is seen. The proof's question is kill/continue correctness; the moment rules are unit-tested with a FAULT and a CONTROL each; and a STOP would push the target to a later chapter for a rule whose wiring the big-moment saves already exercise live |
| F12 | yes (the same as G6) | as G6 |
| F13 | yes: `probe_save_kill.py:151`, `:1751` | child timeouts set from step 6's measurements, child B's stop point and frames defined, registered |
| F14 | yes: probe §0, §1; `new_game.c:154` | a fresh cart asserted before child A; the arm refused otherwise |
| N1 (proof) | yes: `main_menu.c:649-652` | the press census counts from the main menu taking input; the error page's A is outside it |
| N2 (proof) | yes | LAUNCH-OLD added (mutant S27 through the real launcher) |
| N3 (proof) | yes | K-BETWEEN added (the ordinary kill between saves) |
| N4 (proof) | yes | determinism lines per seed, reported |
| designer T1-T7 and the end-save question | — | decided in section 10 (T1-T8), each with its rejected alternative |
