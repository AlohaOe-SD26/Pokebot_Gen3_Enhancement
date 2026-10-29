> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1r2recon/03-code.md` (sha256 `277d56ba09503df8`). Backlog R1 + R2's recon (save, CONTINUE, a memory that survives a kill), angle 3, OUR AI CODE (`ai_player/`): a read-only Claude subagent's NOTE, never truth (the authoritative docs and the code win). Nothing in it was measured live. R1 + R2's build waits for the user's two save answers (`04` item 4).
> ⚠ **The adversary found WRONG here** (`2026-10-29-R1R2-recon-refute.md` section 0.1): W2, section 3.3 step 7 (scripted saves are not only in Battle Frontier lobbies: the three Battle Tents, Trainer Hill, the Contest Lobby and more); W4, section 8 Q2-YES's premise (the game keeps no single-player loss counter; MAX_LOSSES and the graders count per process, so an in-game reload erases neither); W9, section 0 (d) and section 5 (a memory folder outside the run directory needs option plumbing, not a gate change). Closed: U8 (`sSaveDialogCallback` is in the symbol table, its C2) and U3 (the frame counter is 0 at a cold boot and restored by a `.ss1` load, its C4).

# R1 + R2 recon, ANGLE 3: OUR AI CODE (`ai_player/`): save, CONTINUE, a memory that survives a kill

## 0. The answers in brief

A NOTE, never truth (2026-10-29, a read-only recon; nothing was run). Tags: **VERIFIED-code** (read; repo path:line, the framework
under `sandbox-pokebot/`), **VERIFIED-decomp** (the pinned clone at `731ad5bf`), **DOC** (quoted from a project doc), **UNVERIFIED**
(inference; section 9 says what would prove it). "R1"/"R2" are BACKLOG items, not `rate_step5.py`'s `R5.*`/`R1.*` checks. Method: section 1.

**(a) What the play brain keeps across a run, and what a CONTINUE after a kill needs.**
- Its mind is per PROCESS: `GoalManager._Memory` (38 fields, `brain/goals.py:407-496`), `PersonalityState` (`personality.py:172-219`,
  drift counted on the navigator's per-process `stats.steps`, `mode.py:517`, `brain/navigator.py:622-623`), `BattleMind` (catch wishes,
  species met: `brain/battle.py:700-730`), the navigator (`battle_log`, which `MAX_LOSSES` counts: `brain/navigator.py:719`,
  `mode.py:626-638`), `GoalRunner`'s lists (`brain/goals.py:1783-1787`), the run `report` and the PID level peaks (`mode.py:417-421`,
  `:593-600`), and six seeded streams `<seed>:choices/pacing/story/drift/battle/goals` (`mode.py:306-307`, `:377-381`, `:387`).
  **VERIFIED-code.**
- Only the WORLD memory crosses sessions: the whole memory is appended as one line to `<run_dir>/world.jsonl` at every map change
  and at the end (`mode.py:298`, `:323-324`, `:948-949`, `:960-963`), and a later run reads the LAST line of the file `AI_PLAYER_WORLD`
  names (`options.py:178-180`, `mode.py:943`, `world/memory.py:864-871`). Of the goal manager only `landmarks` and `spoke` ride along
  (`mode.py:389`, `:393`; `world/memory.py:812-815`); the goal manager's own memory "is not" carried (`brain/goals.py:447-450`).
  Not saved even in the world memory: `pids`, `unreached`, `cut_off`, `spent`, the current position (`world/memory.py:801-816` vs
  `:444-493`). **VERIFIED-code.** By chapter 2 one snapshot line is about 0.3 MB (a CH2T run: 10,739,541 bytes in 34 lines,
  `sandbox-pokebot/profiles/ai-step5-play/ai_player_runs/20261014-205941-CH2T/world.jsonl`). **VERIFIED (measured with wc).**
- Every stamp is the EMULATOR frame counter (`host/eyes.py:355`; "frames since the start of this emulation session",
  `sandbox-pokebot/modules/libmgba.py:258-262`), never the game's play time. **VERIFIED-code.** Whether it restarts at 0 on a CONTINUE
  boot is **UNVERIFIED**; if it does, carried frame stamps are compared across sessions (`world/memory.py:778-792`, `mode.py:513-514`).
- For a person-like CONTINUE: RESTORE identity (the seed, or the drawn personality + favourite + drift: with no `AI_PLAYER_SEED` the
  seed comes from the clock, `mode.py:293`, so a relaunch draws a NEW personality and favourite, `mode.py:310`, `:377-379`) and
  experience (world memory, `seen_levels`, `no_balls`, `home_heals`, chats, `BattleMind.wishes`/`met`); CUT AT THE SAVE every fact the
  game rolls back (`fight_prep`, `tried_items`, losses in `battle_log`, milestones and milestone-keyed marks); RESET loop guards and
  clocks. The field list is **VERIFIED-code**; the three-way split is **UNVERIFIED** (design inference, section 2.4).

**(b) Skills to build on, and what CONTINUE replaces.**
- Building blocks: `player_free`/`nav_free` (`hands/dialogue.py:131-137`, `brain/navigator.py:245-247`), `talk`'s museum-greeter gate
  (`hands/dialogue.py:248-295`), `wait_for_ui`, `move_cursor` and `choose` by READING the cursor (`hands/menus.py:75-168`),
  `answer_yes_no` (`:171-173`), `advance` (A only on the eyes' waits, "menu:<kind>" on a menu, a stall detector:
  `hands/dialogue.py:174-233`), `play_out` (`skills/story.py:148-159`). **VERIFIED-code.**
- No skill presses START in the overworld (START only at the title, `skills/intro.py:111`, and on the keyboard, `hands/menus.py:202`);
  no save skill, no CONTINUE skill. **VERIFIED-code (by absence, grep).**
- `play_intro` (`skills/intro.py:79-139`): draws gender and name (`:81-86`), skips the movie and title with START when they take input
  (`:100-112`, `:142-154`), chooses NEW GAME **by name** (`:113-115`), then gender, keyboard, the name question, and stops in the truck.
  CONTINUE keeps `:100-112` and replaces the draws, the NEW GAME choice, the naming steps and the `in_truck` end. **VERIFIED-code**
  (the replacement plan is **UNVERIFIED**).
- ⚠ HAZARD: a profile holding a `.sav` and no `.ss1` would start a NEW GAME today: the title look has no player, so the loop picks
  `ch1_intro` and `play_intro` (`mode.py:458-461`, `:488-496`), and `choose(..., "NEW GAME")` finds it by name in
  ("CONTINUE", "NEW GAME", "OPTION") (`eyes/screens.py:260-265`, `hands/menus.py:133-137`); Emerald starts Birch's speech with no
  prompt (`src/main_menu.c:1058-1063`). **VERIFIED-code + VERIFIED-decomp**; not observed live.

**(c) The eyes.**
- READ today: the intro movie, the title, and the main menu with its options by `tMenuType` (CONTINUE included) and its cursor
  (`eyes/screens.py:229-231`, `:258-265`, `:554-560`, `:591-595`), the save-error and battery waits (`:310-311`). **VERIFIED-code.**
  The CONTINUE variant is untested (only `("NEW GAME", "OPTION")` is: `gates/test_hands.py:593`). **VERIFIED-code.**
- ⚠ The START menu is NAMED (`screen.menu`, `eyes/view.py:409-416`) but has **no cursor view while it takes input**: the view is built
  only while `StartMenuTask` runs (`eyes/screens.py:228`, `:576-582`; `host/eyes.py:502-505`), and that task only DRAWS the menu, then
  switches to `Task_ShowStartMenu`, which runs `HandleStartMenuInput` (`src/start_menu.c:527-541`, `:561-579`, `:593-637`;
  `src/task.c:139-153`). **VERIFIED-decomp.** The project measured it on 2026-10-09: "the eyes name the menu but build no cursor
  view of it" (`ai_player/gates/make_step41_fixtures.py:172-174`). **VERIFIED-code.** This CONTRADICTS the R5 code recon §8.1.
- The SAVE dialog runs inside that same task (`gMenuCallback = SaveCallback`, its own `sSaveDialogCallback` states:
  `src/start_menu.c:721-838`, `:877-894`, `:978-1160`), and its yes/no has no task of its own (`src/menu.c:464-472`, `:1211-1217`).
  So the eyes give it no yes/no view; the question is readable only WHILE printer 0 prints it (`src/start_menu.c:902-909`,
  `host/eyes.py:719-731`) and then reads None (`host/eyes.py:451-452`); the info window (LOCATION, PLAYER, BADGES, POKéDEX,
  TIME) is drawn instantly and never readable (`src/start_menu.c:1332-1392`). **VERIFIED-code + VERIFIED-decomp**; live **UNVERIFIED**.
- PLAY TIME is in no Observation (`eyes/observation.py:248-260`); nothing is read on TITLE_SCREEN/MAIN_MENU (`host/eyes.py:279`,
  `:371`). Its bytes (SaveBlock2 +0x0E, `include/global.h:514-517`) are reachable through the door `_marks` already uses
  (`host/eyes.py:323-331`). **VERIFIED-code + VERIFIED-decomp.**
- Missing for R1: E1 the start menu under `Task_ShowStartMenu`; E2 the save yes/no; E3 the save texts after printing; E4 play time
  (if the design needs it); E5 the CONTINUE window's info; E6 the test side's twin list (`gates/play_harness.py:403-408` lists
  `StartMenuTask`, not `Task_ShowStartMenu`). **VERIFIED-code** (the list); the fixes are **UNVERIFIED**.

**(d) Purity and person-fairness.**
- Save and CONTINUE must be the game's own START -> SAVE and title -> CONTINUE, pressed by the AI: rule (b) refuses
  `load_save_state`, `load_save_game`, `load_save`, `reset`, `create_save_state`, `write_bytes` in the play loop
  (`gates/check_purity.py:537-549`); the button functions may be named only in `host/controller.py` (`INPUT_NAMES`,
  `gates/check_purity.py:551-556`). **VERIFIED-code.**
- Files: only `runlog.py` and the instrument write (`gates/check_purity.py:600-603`); elsewhere `open` only in a constant read mode
  (`:614`, `:1256-1274`); the launcher side may write (`:858`). So `memory.jsonl` = a `RecordFile` in `<run_dir>` (each record
  opened, written, closed: a kill keeps finished lines, `runlog.py:55-89`); a "continue" start (drop `current_state.ss1`, keep
  `current_save.sav`) is a LAUNCHER change (only `--fresh`/`--state` exist: `host/launcher.py:179-209`, `__main__.py:59-60`).
  **VERIFIED-code.**
- Fairness: PL-7 "only what is on screen" (`LESSONS.md:286-290`), gate G4 (`gates/check_fairness.py:13-19`, `:56`, `:73-87`, `:90`)
  and RULING 40: "anything the screen does not show NOW" is not allowed (06:9420-9450). **DOC.** Play time IS on screen as H:MM in the
  save info window, the CONTINUE window and the trainer card (`src/menu.c:2129-2133`, `src/main_menu.c:2142-2153`;
  **VERIFIED-decomp**); seconds and frames never are. So reading H:MM while it is shown is fair; the full counter as a BOOKKEEPING
  stamp (never a decision input) follows the own-PID identity precedent (`eyes/observation.py:221`) but needs a `06` decision.
  **UNVERIFIED** (that the user accepts it).
- Save-scumming is out of reach today BY CONSTRUCTION, not by a gate: every press and hold goes through the pad as ONE `Controls`
  action driven to its end (`hands/pad.py:91-120`; `host/controller.py:72-82`), so the soft reset (A+B+START+SELECT held,
  `src/main.c:135-142`) and the title's clear-save and RTC combos (`src/title_screen.c:39-41`, `:788-799`) cannot be pressed. The
  `Controls` protocol (`mode.py:142-152`) would not stop code that interleaved two `hold` generators. **VERIFIED-code + VERIFIED-decomp.**

**(e) The R5 settle and where a save decision can live.**
- `_settle_before_done` (`mode.py:676-754`) plays out what is on screen, pauses and looks again (`DONE_SETTLE_ROUNDS` 6, measured 3 for
  `ch2_dad`: `mode.py:122-130`) and never lets the budget cut a reached target (`_settle_frames`, `DONE_BUDGET_MARGIN` 2:
  `mode.py:131-137`, `:756-772`). Its docstring names R1: "a save (backlog R1) is possible only on a free screen" (`mode.py:682-683`).
  R5 built no save ("D8. R5's third call site (before a save) is R1's: R5 adds no save", `2026-10-28-R5-BUILD-SPEC.md:60`).
  **VERIFIED-code; DOC.**
- Two places: (1) the END, after the settle, only if `report["settle"]["free"]` and the budget leaves the save's frames (about
  1,000-1,300 frames, **UNVERIFIED** estimate; a 2-frame margin is far too small) (`mode.py:480-487`); (2) a DECISION point between
  goals (`mode.py:517-523`), after the play-out (`:504-510`) and `SETTLE_FREE` (`:511-516`) checks and with the thinking pause and
  the "screen changed while it decided" guard (`:531-547`): a goal kind "save" from `GoalManager.next_goal` (`brain/goals.py:1159`).
  NOT at a goal's end: a goal can hand back mid-screen, and the next pass plays it out first (`:504-510`). Triggers (a milestone
  passed `mode.py:467-472`; a known fight next `brain/goals.py:1175`, `:1189-1190`) only mark a save as due. **VERIFIED-code** (the
  anchors); the placement is **UNVERIFIED** (design).
- A deploy stop cannot save today: the brain is not told the soft wall deadline (`mode.py:164-172`, `host/session.py:141-147`) and the
  guard ends the process at it with no brain hook (`host/session.py:305-310`; Ctrl+C at `:290-292`). **VERIFIED-code.**

**(f) L3 (a)-(b): identity today.**
- PIDs are read for the party (`MonSummary.slot/species/pid/ot_id`, `eyes/observation.py:209-227`; `host/eyes.py:983-1000`), the PC
  boxes (`StoredMon` box/slot/pid/ot_id/is_egg, NO species: `eyes/observation.py:229-239`; `host/eyes.py:1007-1021`) and the AI's own
  battlers (`eyes/observation.py:275-277`). They are used as identity by the battle decider (`brain/battle.py:753`, `:775-782`,
  `:1300-1396`, `:1423`), the party pick (`skills/battle.py:459-487`), level gains (`mode.py:593-600`), news and novelty
  (`world/memory.py:765-769`, `brain/navigator.py:524-611`) and ownership by visible OT id (`memory_log.py:78-86`). **VERIFIED-code.**
- No ROLE concept and no PC skill exist in the deciding code. **VERIFIED-code (by absence, grep).**
- A role field hooks into a per-PID record (pid, species recorded while the mon is seen in the party or at the catch, how it came,
  roles with an expiry named by a boss from the AI-visible `trainers` of `milestones.json`, `gates/check_fairness.py:110-113`), read by
  the lead and replacement choice (`brain/battle.py:1302-1396`), the training target (`brain/goals.py:510`, `:1501`, `:1693`), the catch
  helper (`brain/battle.py:1155-1208`), an HM carrier test (`MonSummary.moves`; field moves in `PARTY_MENU_ACTIONS`,
  `eyes/screens.py:291-296`) and the future PC skill. **VERIFIED-code** (the hooks); the schema is **UNVERIFIED** (design).

**The two open user questions** (asked 2026-10-28, unanswered, `04-HANDOFF.md:61`): section 8 lists what each answer changes in
`ai_player/`. Nothing here decides them.

---

## 1. How this was done, and what was not

- For backlog items R1 + R2 (+ DP1, DP2, L3 (a)-(b)): `PROJECT KNOWLEDGE/ai-research-notes/2026-10-18-improvement-backlog.md`, the
  R1 + R2 entry, DP1 + DP2, L3 and the round-3 "Folded into" line (R1 + R2 + DP4). Written by a read-only Claude recon subagent.
- Tree read: HEAD `7d89fe07` (the working tree held only a running regression lane's evidence edits; I wrote nothing in the repo).
- Decomp: the PINNED clone `C:/Remote Projects/_decomp/pokeemerald` at `731ad5bf`. `tools/decomp_lookup.py ask "save game continue"`
  found one unrelated ruling (06:6125, the lobby fixture). `06` has NO ruling on when the AI saves or on save-scumming (grep).
  Related but for the BOT: 2026-08-14 RULING B (06:2237-2252) calls "pick up where it left off" after a power loss "a
  RESUME/DURABILITY capability (a named profile's save resumed after power loss or a deliberate shutdown, at the user's
  intervention)", separate from per-run behaviour. **DOC.**
- Nothing was run: no emulator, gate, driver or test. One read-only `find | wc` measured existing `world.jsonl` files.
- Agreement with other angles' notes is not proof; each UNVERIFIED claim names its proof in section 9.
- Read in full or in the relevant parts: `mode.py`, `brain/goals.py` (`_Memory`, `GoalManager`, `GoalRunner`), `brain/battle.py`
  (`BattleMind`), `brain/navigator.py` (`Navigator`, `nav_free`, the scene handler), `personality.py`, `options.py`, `world/memory.py`,
  `eyes/screens.py`, `eyes/view.py`, `eyes/observation.py`, `host/eyes.py`, `host/controller.py`, `host/launcher.py`,
  `host/lifecycle.py`, `host/session.py`, `hands/menus.py`, `hands/dialogue.py`, `hands/pad.py`, `skills/intro.py`, `skills/story.py`,
  `runlog.py`, `memory_log.py`, `gates/check_purity.py`, `gates/check_fairness.py`, `LESSONS.md` section C, README "The purity
  contract", `sandbox-pokebot/modules/libmgba.py`, `sandbox-pokebot/modules/clock.py`, the hook
  `sandbox-pokebot/plugins/custom_modes/ai_player_mode.py`.
- The decomp files read: `src/start_menu.c`, `src/main_menu.c`, `src/overworld.c`, `src/play_time.c`, `src/main.c`, `src/intro.c`,
  `src/new_game.c`, `src/menu.c`, `src/task.c`, `src/title_screen.c`, `src/script.c`, `src/field_control_avatar.c`,
  `include/global.h`, `data/text/save.inc`, `data/scripts/std_msgbox.inc`.
- NOT covered (other angles): whether mGBA flushes `current_save.sav` before a kill; mGBA's savestate flags; the deploy layout.

---

## 2. (a) The play brain's state across a run

### 2.1 Inventory (all VERIFIED-code)

| What | Where | Persisted between sessions? |
|---|---|---|
| The run seed | `mode.py:293` (`AI_PLAYER_SEED`, else `time.time_ns() % 1_000_000_007`); logged `mode.py:311-313`, first record `:317-318` | only in logs |
| Streams | `<seed>:choices`, `<seed>:pacing` (`mode.py:306-307`); `:story`, `:drift`, `:battle` (`:377-381`); `:goals` (`:387`) | no: a new `random.Random` per process |
| Base personality | `pick_personality`, the FIRST draw of `choices` unless `AI_PLAYER_PERSONALITY` (`mode.py:310`, `personality.py:84-90`) | no (re-drawn from the seed) |
| Favourite species, starter | first and second draws of `story` (`mode.py:379-380`, `personality.py:233-235`) | no (re-drawn) |
| Drift | `PersonalityState` base/active/drift_until/next_draw/history/draws (`personality.py:177-188`); stepped by `nav.stats.steps` (`mode.py:517`), a per-navigator counter (`brain/navigator.py:622-623`, `:671`) | no |
| Goal manager memory | `_Memory` (`brain/goals.py:407-496`): talked, tried_items, item_tries, catch_maps, chat_drawn, fails, cooldown, decisions, asked_rounds, landmarks, fight_prep, sightings, pages, looked, detoured, seen_levels, last_map, no_balls, home_heals, scene_walls, known_before, aside_from, passed_new, spent, again, break_stops, curious_since, curious_row, exhausted, blocked, idle, center_looked, explored, decided_with_party, danger_again, spoke, hearing, lost_end | only `landmarks`, `spoke` (shared with the world memory, `mode.py:389`, `:393`) |
| Goal runner | roams, picked, heals, shopping (`brain/goals.py:1783-1787`); `picked`/`shopping`/`heals` feed the patience counts (`mode.py:606-607`) | no |
| Navigator | `battle_log` (`brain/navigator.py:716-719`), `battle_outcomes` (`:698`), `stats` (`:671`), scene walls/turned/given_up (`:652-670`), `ponged` (`:729`), entry, recent, plan, people_tries | no |
| Battle decider | `wishes` species -> wish to catch, drawn once per species from `<seed>:battle` (`brain/battle.py:711`, `:810-812`); `met`, `wild_met` (rarity cue, `:729-730`, `:1249-1250`); per-battle `_Memory` (`:668-692`) | no |
| Report | `report` (`mode.py:417-421`), later `settle`, `end_screen` (`:737-738`, `:802`); `progress` with PID peaks (`:440`, `:593-600`); `changed_at` patience (`:439`) | no |
| Watchers | `WaitWatch`, `PushWatch`, `BattleClock` (`mode.py:400-410`): report only | no |
| Action log | `<run_dir>/actions.jsonl` (`mode.py:294`; records `memory_log.py:98-113`: frame, digest, decision, action, reason, extra) | per run; survives a kill line by line (`runlog.py:55-58`) |
| World memory | `WorldMemory` (`world/memory.py:444-493`), `MapMemory` (`:249-273`) | YES, by file (2.2) |

`MAX_LOSSES` (3) counts `battles_lost(nav.battle_log)` per RUN (`mode.py:105`, `:626-638`; `brain/goals.py:525-528`), so a relaunch
starts at 0 losses. **VERIFIED-code.**

### 2.2 What crosses sessions today (VERIFIED-code)

- Written: the WHOLE world memory as one JSON line (`world/memory.py:801-821`) appended to `<run_dir>/world.jsonl` at every map change
  (the navigator's `on_map_change`, `mode.py:948-949`, `:960-963`) and at the run's end (`mode.py:323-324`). No snapshot at any other
  moment: a kill loses what was learned since the last map change. No `schema_version` (`grep` finds none in `ai_player/`).
- Read: only when `AI_PLAYER_WORLD` names a file (`options.py:178-180`, `:393`, `:416`; `mode.py:943-945`): its LAST non-blank line,
  `json.loads` with no guard (`world/memory.py:864-871`). A torn last line would raise at the next start (**UNVERIFIED** as observed;
  `RecordFile` writes a whole line per open/close, `runlog.py:76-84`, so a tear needs a kill mid-write).
- Carried inside it: maps (tiles with `seen_frame`/`seen_from`, visits, bumps, closed doors with their frame and news count, people,
  persons, met, items, edges, arrivals: `world/memory.py:375-389`), warps, connections, transitions, `tiles_learned`, `news`, `heard`,
  `news_log`, `landmarks`, `spoke` (`:801-816`). NOT carried: `pids` (`:459`), `unreached` (`:465`), `cut_off` (`:472`), `spent` (`:477`),
  `reopened` (`:487`), the current map and tile (`_last`, `:493`), `looks` (`:451`).
- How chapters chain today: the emulator STATE of the previous run's clean exit plus its `world.jsonl` (`gates/live_step5.py:449-462`,
  `:497-509`). The AI's in-game save plays no part anywhere.
- Size: about 0.3 MB per snapshot line by chapter 2 (the measurement in section 0 (a)). The backlog's "full lines plus deltas"
  answers this.
- A clean exit is what leaves the resume state the harnesses chain from: `gates/live_step5.py:497-503` copies the profile's
  `current_state.ss1` after the run (written by `atexit`, `sandbox-pokebot/modules/libmgba.py:159-160`, `:231-241`).

### 2.3 The clocks

- Emulator frames: `context.emulator.get_frame_count()` stamps every Observation (`host/eyes.py:355`); the framework calls it "the
  number of frames since the start of this emulation session" (`sandbox-pokebot/modules/libmgba.py:258-262`). `pad.frames` counts the
  brain's own frames per process (`hands/pad.py:76`). **VERIFIED-code.**
- Frame stamps that a carried memory compares with the current frame: a closed door is retried once `frame - info["frame"] >=
  CLOSED_RETRY_FRAMES` (`world/memory.py:778-792`); "taking in the new place" waits while `0 <= look.frame - arrived < SETTLE_FREE`
  with `arrived` the LAST carried transition's frame (`mode.py:513-514`). If the counter restarts at 0 after a CONTINUE boot
  (**UNVERIFIED**; a fresh boot does start at frame 0: `host/eyes.py:356-359`), both compare across sessions: a door closed late in
  the last session is not retried by time until the new session passes the old frame plus 36,000.
- The game's own clock: `playTimeHours/Minutes/Seconds/VBlanks` in SaveBlock2 (`include/global.h:514-517`). `PlayTimeCounter_Update`
  runs once per main-loop pass while RUNNING (`src/main.c:165`, `src/play_time.c:36-63`), started by `CB2_NewGame` and
  `CB2_ContinueSavedGame` (`src/overworld.c:1539`, `:1735`), reset only by a New Game (`src/new_game.c:165`). **VERIFIED-decomp.**
  ⇒ it rolls back WITH the game at a CONTINUE, which makes it the natural stamp for "not newer than the save". But after a reload
  the same play-time values are lived again on another branch, so a stamp alone is ambiguous across reloads: each line also needs an
  EPOCH (for example the number of CONTINUEs). **UNVERIFIED** (design).
- The framework already has `get_play_time()` (SaveBlock2 +0x0E, 5 bytes: `sandbox-pokebot/modules/clock.py:43-66`), but
  `modules.clock` is not an eyes door (`host/eyes.py:103-113`); the same bytes are one `read_symbol("gSaveBlock2Ptr")` plus
  `read_bytes` away, the pattern of `_marks` (`host/eyes.py:323-331`), and must not be read while the save blocks may be moving
  (`host/eyes.py:371-379`). **VERIFIED-code.**

### 2.4 What a CONTINUE after a kill would need (classification UNVERIFIED, fields VERIFIED-code)

The game itself restores the party, bag, money, badges, Pokédex, flags and position; the eyes read them fresh after CONTINUE
(`host/eyes.py:371-386`). Only the AI's own mind is at stake. A person who comes back keeps who they are and what they know; the
game has lost what happened since the save.

- RESTORE (identity): the seed, or the drawn base personality + favourite + drift state (`active`, `drift_until`, `history`) and a
  step count that survives the process. Without `AI_PLAYER_SEED` a relaunch draws a new personality and favourite (`mode.py:293`,
  `:310`, `:379`). With the same seed the base and favourite come back (first draws), but the `choices` stream then shifts: a New
  Game spends two draws on gender and name (`skills/intro.py:81-82`) that a CONTINUE does not.
- RESTORE (experience a person keeps): the world memory (already by file); `seen_levels` (`brain/goals.py:437`), `no_balls` (`:442`),
  `home_heals` (`:444`), `talked`/`chat_drawn`/`asked_rounds` (`:410`, `:414`, `:418`; else it re-chats: PL-13/14 graders count that),
  `BattleMind.wishes`/`met`/`wild_met` (`brain/battle.py:711`, `:729-730`).
- CUT AT THE SAVE (the game rolled these back): `fight_prep` (`brain/goals.py:423`: training after the save is undone, levels are lower
  again), `tried_items`/`item_tries` (`:411-412`: an item picked after the save is back in its ball), every loss in `battle_log`
  after the save (a whiteout that never happened), the report's milestones, R11's ledger rows, and milestone-keyed marks for
  milestones the save has not reached (`exhausted` `:469`, `blocked` `:472`, `scene_walls` `:446`, `detoured` `:434`, `again` `:459`,
  `break_stops` `:461`).
- RESET (loop guards and clocks): `fails`, `cooldown`, `decisions` (`:415-417`), `aside_from` (`:452`), `danger_again` (`:484`),
  `curious_since`/`curious_row` (`:464-466`), `lost_end` (`:496`), `hearing` (`:492`), `known_before` (recomputed at the first decision,
  `brain/goals.py:1162-1164`), `pages`/`sightings` (frame-stamped, `:426-429`), the navigator's ping-pong and walls, the patience clock.
- A design fork the backlog's rule hides: "a resume loads memory NOT NEWER than its save" (backlog R1 + R2) also drops map tiles and
  words the AI saw after the save, which a person would remember. With no save-scum the only reloads are kills, so the simple rule
  costs little; with save-scum it would erase exactly the lesson of the loss (section 8). **UNVERIFIED** (design).
- Replay ("a seed replays the AI's CHOICES, not the game's RNG": backlog D2 + DP5, **DOC**) needs each stream's state at the save
  (`random.Random.getstate()` is plain data) or a per-epoch reseed `f"{seed}:{epoch}:{stream}"`. Whether `getstate`/`setstate` pass
  the purity gate's surface rules is **UNVERIFIED**.
- The proof "kill, CONTINUE, same PIDs and tile": record `look.party` PIDs and `player` map/x/y on the free look right before START,
  compare with the first `nav_free` look after CONTINUE. Caveat: a set continue-game warp moves the player
  (`src/overworld.c:1739-1746`); the Hall of Fame sets one to the Littleroot bedroom (06:5682-5694, **DOC**). Pick a save with none.

---

## 3. (b) Skills to build on, and the New Game path CONTINUE replaces

### 3.1 Building blocks (VERIFIED-code)

- `player_free` (`hands/dialogue.py:131-137`): overworld, no script, controls free, no ui, no field box, no wait, position settled.
  `nav_free` adds no fade and a view (`brain/navigator.py:245-247`). START may be pressed only on such a look: the game opens the
  START menu only with the field controls unlocked, the player at a tile's centre or still, and not at top speed (a Mach Bike at full
  speed ignores it) (`src/overworld.c:1445-1447`, `src/field_control_avatar.c:94-100`, `:182-187`; **VERIFIED-decomp**).
- `talk` (`hands/dialogue.py:248-295`): the pattern for "press only when free, verify the game reacted, hand the screen back if a scene
  began" (`give_way`). A save skill's first press needs the same shape.
- `wait_for_ui(hands, kind, why)` (`hands/menus.py:75-84`); `move_cursor` (`:87-111`: one press toward the target, look again);
  `choose` (`:120-168`: by option NAME or index, A only when the look right before shows the cursor on it, verified by the menu
  reacting); `answer_yes_no` (`:171-173`). The docstring already knows "the start menu remembers its last row
  (`sStartMenuCursorPos`)" (`:5-11`).
- `advance(hands, until, why)` (`hands/dialogue.py:174-233`): reads each page, presses A only when the eyes say the game waits, returns
  "menu:<kind>" without pressing, "stuck:" after `STALL_FRAMES` 300 unchanged frames (900 for a named scene, `:62-63`).
- `play_out` (`skills/story.py:148-159`) and the navigator's scene handler (`brain/navigator.py:1080-1100`): a menu the play brain's
  `on_menu` does not know ends the run "stuck: an unexpected <kind> on screen" (`:1094-1097`); `_story_menu` knows only
  `choose_starter`, `clock`, `mart_buy`/`mart_menu` (`mode.py:640-651`).

### 3.2 The New Game path today (`skills/intro.py`, VERIFIED-code)

1. `:81-86` gender and name drawn from `hands.choices`, told and noted. CONTINUE: no draws (the name is in the save).
2. `:89-98` up to `INTRO_MENU_STEPS` (60) rounds of `advance(hands, in_truck, why)`; "done" only in the truck (`:61-65`). CONTINUE's
   end: a free overworld look with a party.
3. `:100-112` intro movie / title: wait until it takes input (`:142-154`), think, START. KEEP for CONTINUE.
4. `:113-115` main menu: `choose(hands, "main_menu", "NEW GAME", "a new game")`. CONTINUE: choose "CONTINUE"; if the menu offers no
   CONTINUE (the save erased or empty) STOP and say so, never fall back to NEW GAME (PL-3; DP4 "never a silent --fresh wipe").
5. `:116-136` gender, keyboard, "So it's NAME?". Not met on CONTINUE; any yes/no there is unexpected.
6. The play loop's intro guard: one intro per run, else "stuck: the New Game intro again" (`mode.py:490-491`), and the outcome must
   start "in the truck" (`:494-495`). CONTINUE needs its own pair.

### 3.3 The save dialog as the game runs it (VERIFIED-decomp, `src/start_menu.c` unless named)

1. START on free field controls: `ShowStartMenu` -> `CreateStartMenuTask(Task_ShowStartMenu)` (`:581-591`, `:533-541`); `StartMenuTask`
   draws the menu over several frames (`InitStartMenuStep`, `:480-517`), then `SwitchTaskToFollowupFunc` (`:527-531`; `src/task.c:148-153`).
2. `Task_ShowStartMenu` sets `gMenuCallback = HandleStartMenuInput` and calls it every frame (`:561-579`). Up/Down move the cursor; A
   picks the item's callback (no fade for SAVE); START or B closes (`:593-637`). Items of a normal game: POKéDEX and POKéMON only once
   obtained, BAG, POKéNAV once obtained, PLAYER, SAVE, OPTION, EXIT (`:315-337`): SAVE's row varies, so choose it by NAME.
3. SAVE -> `StartMenuSaveCallback` -> `SaveStartCallback` (`InitSave`: `SaveMapView`, `sSaveDialogCallback = SaveConfirmSaveCallback`)
   -> `SaveCallback` (`:721-729`, `:809-838`, `:877-894`). The whole dialog runs inside the same task.
4. `SaveConfirmSaveCallback`: the start menu window closes, the info window opens, "Would you like to save the game?"
   (`:978-994`; `data/text/save.inc:2-3`). `SaveYesNoCallback`: a yes/no opening on YES (`:996-1001`; `src/menu.c:464-467`).
5. YES -> `SaveFileExistsCallback` unless the cartridge is EMPTY/CORRUPT and `gDifferentSaveFile` is set (then straight to SAVING);
   NO or B -> back to the start menu (`:1003-1033`, `:823-827`). `gDifferentSaveFile` is TRUE from a New Game until its first save
   (`src/new_game.c:154`, cleared `:1094-1096` of start_menu.c) and FALSE after a boot (`src/new_game.c:139-141` via
   `src/intro.c:1152`). So: a New Game's first save on an empty cartridge asks nothing more; every save after a CONTINUE asks "There is
   already a saved file. Is it okay to overwrite it?" (default YES); a New Game over another game's save shows a 4-page WARNING whose
   yes/no opens on NO (`:1035-1078`; `data/text/save.inc:5-7`, `:16-24`).
6. "SAVING… DON'T TURN OFF THE POWER." (`:1080-1084`); `TrySavingData` runs synchronously in one callback, then "{PLAYER} saved the
   game." or "Save error. Please exchange the backup memory." (`:1086-1110`; `data/text/save.inc:9-14`, `:26-29`); SE_SAVE plays
   (`:1112-1121`); the dialog closes when the sound stops and a 60-frame timer runs out, or A is held (`:1123-1134`, `:947-962`); the
   controls unlock and the task ends (`:828-835`, `:575-576`).
7. Scripted saves (`special SaveGame` -> `SaveGameTask`, `:896-930`) exist only in Battle Frontier lobbies
   (`data/scripts/std_msgbox.inc:46-48`); the story's only automatic save is the Hall of Fame's (06:5682-5694, **DOC**).

Implied skill (UNVERIFIED design): on a free look, START (gate: `player_free`); `wait_for_ui("start_menu")` (needs E1); `choose(...,
"SAVE")`; read the question (E2/E3); `answer_yes_no(True)`; the overwrite question: YES only for "There is already a saved file",
NO and stop for the WARNING (another game's adventure); `advance` until `player_free`; outcome "saved" only if "saved the game." was
READ; any other ending said and returned at once (PL-3). Rough cost: four messages at the default speed, the sound, the 60-frame
timer, the AI's reading and thinking pauses: about 1,000-1,300 frames (**UNVERIFIED** estimate; the first live save measures it).

### 3.4 The CONTINUE path as the game runs it (VERIFIED-decomp)

- At boot the save is LOADED into RAM before the title (`src/intro.c:1147-1160`). The title takes START/A (`Task_TitleScreenPhase3`).
- `Task_MainMenuCheckSaveFile` sets `tMenuType` from `gSaveFileStatus` (`src/main_menu.c:625-691`): OK -> CONTINUE, NEW GAME, OPTION
  (+ MYSTERY GIFT when enabled); CORRUPT -> an "erased" window waiting for A, then NEW GAME, OPTION only; ERROR -> a "corrupted" window,
  then CONTINUE offered; EMPTY -> NEW GAME, OPTION. The error windows wait in `Task_WaitForSaveFileErrorWindow` (`:694-703`), a wait the
  eyes know (`eyes/screens.py:311`). The cursor starts on item 0 unless coming back from OPTION (`:672-689`).
- The CONTINUE window shows the player, the Pokédex, TIME as H:MM and the badges (`src/main_menu.c:2142-2153`).
- A on CONTINUE -> `CB2_ContinueSavedGame` (`src/main_menu.c:1064-1068`; `src/overworld.c:1705-1750`): play time restarts counting;
  the continue-game warp if set (`CB2_LoadMap`), else back to the saved spot with the map-name popup.

### 3.5 Hazards in today's code

- H1 NEW GAME on a profile with a `.sav` and no `.ss1` (section 0 (b)). **VERIFIED-code + decomp; not observed live.**
- H2 After the Hall of Fame the credits end in a soft reset to the title (06:5682-5694, **DOC**). Today's loop would meet "title" in
  `play_out` and end "stuck: an unexpected title on screen" (`brain/navigator.py:1094-1097`, `mode.py:640-651`), unless the target
  was already reached. **VERIFIED-code chain; UNVERIFIED live.** A CONTINUE skill serves this tail too.
- H3 After a KILL no new `current_state.ss1` is written (it is written only by `atexit` -> `shutdown` -> `create_save_state`:
  `sandbox-pokebot/modules/libmgba.py:159-161`, `:231-241`), and a relaunch without `--state`/`--fresh` resumes from the last CLEAN
  exit's `.ss1` if one exists (`:141-145`; `host/launcher.py:187-188`), not from the newer in-game save. A CONTINUE start must delete
  the `.ss1`. Whether loading an old `.ss1` also restores old cartridge data inside the core (mGBA `load_state` with default flags,
  `libmgba.py:367-375`) and can later overwrite a newer `.sav` is **UNVERIFIED** (other angle).
- H4 `--state` empties the cartridge save file (`host/launcher.py:196-198`, `:206-209`): a fixture-seeded run has no AI-made `.sav` until
  the AI saves, so a CONTINUE proof must use a `.sav` the AI wrote itself (or a pinned `.sav`).
- H5 A clean exit (`sys.exit`, `host/lifecycle.py:182-185`) still writes `current_state.ss1` through `atexit`, so after the AI starts
  saving there are TWO resume copies; DP4 says the `.sav` is the durable truth (`02-deployment.md:66-71`, **DOC**).

---

## 4. (c) The eyes on these screens

### 4.1 Read today (VERIFIED-code)

- `intro_movie` (TITLE_SCREEN with tasks, `eyes/screens.py:591-595`), `title` (`Task_TitleScreenPhase3`, `:231`, `:559-560`), `main_menu`
  (`Task_HandleMainMenuInput`, `Task_HighlightSelectedMainMenuItem`: `:229-230`; options by `tMenuType` = task data[0], cursor `tCurrItem` =
  data[1], input only under `Task_HandleMainMenuInput`: `:554-558`, `:258-265`; `src/main_menu.c:616-617`). Every task's 32 data bytes
  are read every look (`host/eyes.py:437`).
- Waits: the save-file error and battery windows (`eyes/screens.py:310-311`). Scenes: "the main menu" (`:378-380`), "the opening"
  (`:387`), "the map loading" (`:344-350`). `CB2_ContinueSavedGame` is not in `SCENE_CALLBACKS`, but its first call replaces itself
  with `CB2_LoadMap` or (through `CB2_ReturnToField`) `CB2_ReturnToFieldLocal` (`src/overworld.c:1739-1750`, `:1625-1636`), both named,
  so at most one look meets it (if the framework still reports `MAIN_MENU` then, `eyes/screens.py:388` names it: **UNVERIFIED**).
- Nothing else in TITLE_SCREEN/MAIN_MENU: no player, party, bag or progress (`host/eyes.py:279`, `:371`). Good for fairness: the
  whole save is already in RAM there (3.4).
- After CONTINUE: everything as on any overworld look, including party PIDs and the tile (`host/eyes.py:371-386`).

### 4.2 The START menu: named, not readable (the contradiction)

- `eyes/screens.py:228` maps `"StartMenuTask": "start_menu"` with the comment "(runs HandleStartMenuInput)"; `host/eyes.py:502-505`
  reads `sStartMenuCursorPos` and `sCurrentStartMenuActions` only `if "StartMenuTask" in tasks`; `read_ui` builds the view only for it
  (`eyes/screens.py:576-582`). **VERIFIED-code.**
- In the decomp `StartMenuTask` never runs `HandleStartMenuInput`: it draws and then becomes `Task_ShowStartMenu` (3.3 steps 1-2).
  **VERIFIED-decomp.** The bot (teaching material) waits on `Task_ShowStartMenu` everywhere
  (`sandbox-pokebot/modules/modes/util/items.py:53`, `:280`; `modules/story/pokemon_league.py:330`). **VERIFIED-code.**
- Effect: while the start menu takes input, `screen.menu == "start_menu"` (`eyes/view.py:409-416`, tested only for the menu NAME:
  `gates/test_eyes.py:397`) but `screen.ui` is None; the controls are locked (`src/start_menu.c:590`, `src/script.c:182-185`), so
  `busy_reason` says "a scene plays" (`hands/dialogue.py:103-104`) and `advance` would report STUCK after 300 frames. During the few
  init frames a view exists and claims `accepts_input` True (the `MenuView` default, `eyes/observation.py:307`). The project
  measured the gap on 2026-10-09 (`gates/make_step41_fixtures.py:172-174`: "the eyes name the menu but build no cursor view of it");
  its fixture maker reads the cursor test-side instead (`:191-197`).
- ⚠ The R5 code recon (`2026-10-28-R5-recon-code.md` §8.1) says "The eyes can READ the start menu, its cursor and its actions". That
  was read from the table without the task switch; the two citations above refute it.

### 4.3 The save dialog (VERIFIED-code + VERIFIED-decomp; live UNVERIFIED)

- The yes/no: no task of its own; the cursor is in `sMenu` (`CreateYesNoMenu` -> `InitMenuInUpperLeftCornerNormal`, polled by
  `Menu_ProcessInputNoWrapClearOnChoose`: `src/menu.c:464-472`, `:1211-1217`). The eyes read `sMenu` only for the tasks in `_SMENU_TASKS`
  (`host/eyes.py:217-225`, `:487-488`), and `read_ui` finds no listed task: no view.
- The texts: `ShowSaveMessage` expands into `gStringVar4` and prints with printer 0 (`src/start_menu.c:902-909`, `src/menu.c:198-202`).
  `_text` returns the printed part while the printer is active (`host/eyes.py:719-731`); afterwards only when `shown`, i.e. a wait, a
  ui or the field box (`:451-452`), and none holds (the field box mode is set only by `src/field_message_box.c`). So the question
  vanishes from the eyes exactly when the yes/no appears. "{PLAYER} saved the game." is readable only while it prints.
- The info window: LOCATION, PLAYER, BADGES, POKéDEX, TIME, printed with `TEXT_SKIP_DRAW` (`src/start_menu.c:1332-1392`): no active
  printer, and `gStringVar4` is then overwritten by the question. Not readable. (README's own limit: "the start menu opened with no
  message shows an old one", README:3509-3513, **DOC**.)

### 4.4 Play time (VERIFIED-code + VERIFIED-decomp)

- Not in `Progress` (`eyes/observation.py:248-260`) nor anywhere in the Observation. Shown on screen only as H:MM
  (`src/menu.c:2129-2133`, `src/main_menu.c:2142-2153`). Available bytes: SaveBlock2 +0x0E..+0x12 (`include/global.h:514-517`).

### 4.5 Missing for R1 (UNVERIFIED designs; anchors VERIFIED)

- E1 START menu view: `Task_ShowStartMenu` active and `gMenuCallback` (`src/start_menu.c:78`) named `HandleStartMenuInput` through
  the step-3 door `get_symbol_name` (`host/eyes.py:105`, used at `:554`); cursor and actions from the statics already read
  (`:503-505`; `sStartMenuCursorPos` is `EWRAM_DATA static`, `src/start_menu.c:83`, and readable by name today).
- E2 save yes/no view: `gMenuCallback` = `SaveCallback` and `sSaveDialogCallback` (`EWRAM_DATA static`, `src/start_menu.c:88`) named
  `SaveConfirmInputCallback` or `SaveOverwriteInputCallback`; cursor `sMenu[2]`. That `sSaveDialogCallback` is in the symbol table is
  **UNVERIFIED** (the `sStartMenuCursorPos` precedent says likely).
- E3 the question after printing: follows from E2 (`shown` becomes True, printer 0's message is returned, `host/eyes.py:732-738`).
- E4 play time, only if the memory stamp uses it (section 5).
- E5 the CONTINUE window's player, H:MM, Pokédex and badges (instant printers; a save-block read in MAIN_MENU limited to these four).
- E6 the test side: `gates/play_harness.py:403-408` (the second path that grades waits) lists `StartMenuTask`, not
  `Task_ShowStartMenu`; no unit test builds a start-menu view; none builds a main menu with CONTINUE (`gates/test_hands.py:593`).
- Knock-on of E1/E2 (**UNVERIFIED**): a start menu with a ui changes `player_free`, `awaits_press` (WaitWatch counts it as a wait for
  a press, `hands/dialogue.py:236-245`) and makes `advance` return "menu:start_menu", which every caller except the save skill treats
  as unexpected (`skills/intro.py:137-138`, `brain/navigator.py:1094-1097`). Today nothing opens it, so the change is quiet until R6.

---

## 5. (d) Purity and person-fairness for save and CONTINUE

- Presses only (README "The purity contract" 1(b), README:474-498, **DOC**; `gates/check_purity.py:537-556`, **VERIFIED-code**). The
  instrument counts every load, write and frame door at run time (README §3, **DOC**). An in-game save and a CONTINUE are presses;
  any emulator state load or save in the play loop is a breach.
- The hook already starts the AI at the title screen (`sandbox-pokebot/plugins/custom_modes/ai_player_mode.py:72-75`), so a CONTINUE
  boot starts where a New Game does. **VERIFIED-code.**
- Files (`gates/check_purity.py:600-603`, `:614`, `:858`, `:1256-1274`; `runlog.py:55-89`, **VERIFIED-code**): the play loop can append
  `memory.jsonl` lines only through `RecordFile` in `<run_dir>`, and read an earlier file only in read mode (as `read_world` does).
  A memory home outside the run directory (DP1's `AI_PLAYER_HOME`) means either widening `FILE_WRITERS` (a gate change) or the
  LAUNCHER copying files between runs (the launcher side may write). Neither `AppPaths` nor `schema_version` exists (`grep`).
- Person-fairness (PL-7, `LESSONS.md:286-290`; G4, `gates/check_fairness.py:13-19`; RULING 40, 06:9420-9450, **DOC**):
  - Choosing CONTINUE from the menu is what a person sees: fair. Reading the save's CONTENT before CONTINUE (party, place, flags,
    all in RAM since boot, `src/intro.c:1147-1160`) is seeing through the menu; today's eyes refuse it (`host/eyes.py:279`, `:371`).
  - Play time: H:MM while shown (save info window, CONTINUE window, trainer card) is fair. The full counter (seconds, frames) is not on
    screen: RULING 40 bans "anything the screen does not show NOW" (**DOC**). As a bookkeeping STAMP only (never read by deciding code),
    it would follow the own-PID precedent (`eyes/observation.py:221`: the PID, never shown, is the identity). That needs a `06` decision.
    **UNVERIFIED** (the user's view). A clock-free alternative: write a "saved" marker when "{PLAYER} saved the game." is READ, and match
    a CONTINUE to the newest marker by what the CONTINUE window and the first look show (H:MM, place, PIDs). It fails if the in-game
    save completed but the file was not flushed before the kill (the other angle's question); the play-time compare catches that.
  - G4 RULE A refuses `FLAG_`/`VAR_` names in deciding code (`gates/check_fairness.py:90`): memory lines should name milestones by
    their AI-visible ids (`milestones[].id`, classified AI at `gates/check_fairness.py:118`), never by flag.
- Save-scumming is out of reach today by construction of the pad, not by a gate (section 0 (d)). If the user allows reloads, the pad must hold
  several buttons, which also makes the title's CLEAR-SAVE combo (B + SELECT + UP, `src/title_screen.c:39`, `:788`) reachable: a new
  hazard to gate.

---

## 6. (e) The R5 settle, and where a save decision can live

- What R5 guarantees (VERIFIED-code, `mode.py:676-754`): at most `DONE_SETTLE_ROUNDS` (6) rounds of "play out a busy screen
  (`play_out`), count its losses, look"; on a free look, the decision's pause and one more look (one free look is not a free screen,
  PL-18, `LESSONS.md:357-361`); every frame through `_settle_frames`, which stops `DONE_BUDGET_MARGIN` (2) frames before the budget
  (PL-19, `LESSONS.md:363-367`); `report["settle"]` = played, paused, frames, stop, free, budget, passed (`:737-738`); a screen that did
  not free is SAID (`:749-754`). The measured case: DAD's warp frees the player for ONE frame before WALLY's tutorial locks it, and it
  took three pauses (`mode.py:122-130`, `:688-693`).
- Why that matters for a save: START pressed on that one free frame would land on a screen about to lock. A save skill must keep the
  `talk`-style gate (press only on `player_free`, verify the menu opened within a budget, hand the screen back otherwise).
- Place 1, the END (`mode.py:480-487`): after `_settle_before_done`, only when `report["settle"]["free"]` and more than the save's own
  frames are left; otherwise SAY "not saved: <why>". The end reason must stay exactly "done: <target> reached" (the HONESTY check in
  `gates/live_step5.py`, per `mode.py:694-696`); the save's result belongs in the end record (`_play_end`, `mode.py:832-844`).
  The "stuck" ends (`mode.py:794`) have no settle; saving there would need one first. **UNVERIFIED** (design).
- Place 2, BETWEEN GOALS (`mode.py:517-523`): the loop has already played out a busy screen (`:504-510`) and waited `SETTLE_FREE` after
  a map change (`:511-516`); a "save" goal then gets the thinking pause and the "screen changed while it decided" drop (`:531-547`) like
  any goal, a logged reason, and `manager.outcome`/`spent`. Touch points: the kind lists `STORY_KINDS`/`ERRAND_KINDS`/`CURIOSITY_KINDS`
  (`brain/goals.py:276-282`; the graders mirror `CURIOSITY_KINDS`), `spent` counts any kind not in `ERRAND_KINDS` as story time
  (`:972-981`), so the intent-mix grader would see save frames as story unless listed. **VERIFIED-code** (anchors); impact
  **UNVERIFIED**.
- NOT at a goal's end: `runner.pursue` can return with a scene on screen (R5 recon), and nothing after it checks the screen before the
  next pass (`mode.py:551-576`); the next pass plays it out first (`:504-510`). "At a goal's end" therefore means "at the next decision".
- Triggers that only mark a save as DUE: a milestone passed (`mode.py:467-472`); a known fight next (`brain/goals.py:1175`, next to the
  heal-before-fight rule `:1189-1190`); a heal done; a personality knob for how often (an `Errands` field, `personality.py:116-150`, an
  R12 knob). The goal manager then chooses it at a free decision. **UNVERIFIED** (design).
- A deploy stop: give the brain the soft deadline (`BrainSettings` has none, `mode.py:164-172`) or a STOP notice, so it saves at the
  next free decision before `host/session.py:305-310` ends the process. **VERIFIED-code** (the gap).

---

## 7. (f) L3 (a)-(b): where the AI identifies its Pokemon, and what a role hooks into

- Identity sources (VERIFIED-code):
  - party: `MonSummary(slot, species, dex, level, hp, max_hp, status, types, moves, pid, ot_id, is_egg, experience, stats)`
    (`eyes/observation.py:209-227`), decoded by the AI's own `eyes/party.py` (`host/eyes.py:960-1000`); a torn slot makes the whole
    party None (`:960-978`);
  - boxes: `StoredMon(box, slot, pid, ot_id, is_egg)`, from the unencrypted header only: NO species (`eyes/observation.py:229-239`,
    `host/eyes.py:1007-1021`);
  - battle: `BattleMon.pid` for the AI's own battlers only (`eyes/observation.py:275-277`, `host/eyes.py:1098`);
  - ownership: visible OT id equal to the player's (`memory_log.py:78-86`); a catch is logged with species and PID
    (`memory_log.py:280-285`), and the game boxes a catch itself when the party is full (its `dest=box`).
- Identity users (VERIFIED-code): `BattleMind` sent/refused/shift_to/unusable_owners by PID (`brain/battle.py:716-727`, `:753`,
  `:775-782`), `better_member`/`replacement`/`_shift` (`:1302-1423`), `user` lookups by PID (`:994`, `:1108`, `:1212`); the party pick
  maps PID -> slot by reading the list (`skills/battle.py:459-487`); level gains by PID (`mode.py:593-600`); news of a new PID
  (`world/memory.py:765-769`, not persisted); navigator novelty, PIDs and experience by PID (`brain/navigator.py:524-611`).
- Absent (VERIFIED-code, grep over brain/, skills/, hands/, world/, mode.py, personality.py): any role, preference with an expiry,
  boxing decision, deposit or withdraw. The favourite is a SPECIES (`personality.py:233-235`), the catch wish is per SPECIES
  (`brain/battle.py:711`).
- What a role field hooks into (UNVERIFIED design, DECIDE EARLY per the backlog):
  - a per-PID record in R2's memory from its first line: `pid` (hex), `species` (recorded while seen in the party or at the catch,
    since the box shows none), `how` (starter, caught at MAP, gift), `first_seen` (play time + epoch), `roles` = list of
    {`role`: lead | hm:<MOVE> | counter:<BOSS> | catch_helper | spare, `until`: {`boss`: <name>} or null, `why`};
  - readers: the lead and replacement choice (`brain/battle.py:1302-1396`), the training target (`strongest_level`
    `brain/goals.py:510`, `fight_levels` `:1501`, `prep` `:1693`), the catch helper (`_catch`, `_catch_status` `brain/battle.py:1155-1208`),
    an HM carrier test (`MonSummary.moves`; the party menu's field moves `eyes/screens.py:291-296`), and L3 (c)-(d)'s PC skill;
  - boss names come from the AI-visible `trainers` of `milestones.json` (`gates/check_fairness.py:110-113`), so the field passes G4;
  - a preference expires with its boss (backlog L3: KI-122's unscoped `_hunted_counter_pids`, **DOC**); a role keyed by a boss the
    save has not beaten is "game-coupled" and is cut at the save like `fight_prep` (2.4).

---

## 8. The two open user questions: what each answer would change in `ai_player/` (no decision taken)

Asked 2026-10-28 5:27 PM and unanswered (`04-HANDOFF.md:61`, **DOC**); the backlog's default is "No save-scum" (R1 + R2 entry, **DOC**).

**Q1. When does the AI save?** (each option UNVERIFIED design; anchors VERIFIED-code)
- "Only when it stops": a save after the R5 settle (`mode.py:480-487`) plus a stop notice for deploy (section 6). A kill then loses the
  whole session: the memory cut falls at the session start. Smallest change; no new goal kind; no grader change.
- "Like a person, at natural points" (after a badge or milestone, on reaching a new town, after a heal, before a gym or boss): a "save"
  goal kind in `GoalManager.next_goal`, a `skills/save.py`, triggers marking it due (section 6), the kind lists and the intent-mix
  graders (`brain/goals.py:276-282`, `gates/rate_step5.py`) updated, so step-5 grading must be re-run. A kill loses at most one stretch.
- "Every N minutes of play": needs a clock that survives sessions (E4 play time; `pad.frames` restarts per process, `hands/pad.py:76`).
- "By personality" (a cautious archetype saves more): an `Errands` field (`personality.py:116-150`), an R12 knob, cycled with DP5.
- Any answer: E1-E3 eyes work, the save skill, the overwrite rule (YES to "already a saved file", NO to the WARNING), and a "saved"
  marker in `memory.jsonl`.

**Q2. May it reload a save to undo a loss?**
- NO (the default):
  - No reload code; reloads come only from kills and crashes (the host relaunch, R15). Keep the one-action-at-a-time pad: it makes a
    soft reset and the title's clear-save combo impossible (section 5); today that is by construction, and a gate could pin it.
  - `MAX_LOSSES` (`mode.py:105`), `battles_lost` (`brain/goals.py:525-528`) and R11's ledger stay game-true; the graders' "the AI's
    battles lost == the game's" check keeps holding.
  - The "not newer than the save" cut applies to kills only, where it costs little.
- YES:
  - A reload path: an in-game soft reset (a multi-button hold in the pad and `Controls`: `hands/pad.py:91-120`, `mode.py:142-152`,
    `host/controller.py:58-82`, the purity gate's pinned controller surface) then CONTINUE, or a host relaunch the brain requests (a
    new exit reason; R15).
  - The memory must split LESSONS that survive a reload (why it lost: the foe's team and levels seen, the defeat ledger) from
    game-coupled facts cut at the save. Otherwise the retry either repeats the mistake or forgets everything (R11 + L7 "a loss must
    change something").
  - The loop needs a "CONTINUE again" guard beside "the New Game intro again" (`mode.py:490-491`).
  - `MAX_LOSSES` must count reloaded losses: the game's own counters roll back with the save. The step-5 graders that compare the AI's
    losses with the game's need the AI's ledger and the host's reload log instead.
  - Fair to a person, who can soft-reset, but it changes what a Champion rate means: every reload must be reported (R13's fitness).
  - R7's get-unstuck ladder could gain a "reload" rung (deploy only).

---

## 9. What would prove the UNVERIFIED claims (none of this was run)

- U1 (the START menu view gap): in the in-process harness on any free-overworld fixture, press START test-side and log per frame
  `screen.menu`, `screen.ui`, the task names and `gMenuCallback`'s name. Predicted: a `start_menu` ui only on the few `StartMenuTask`
  frames, None while `Task_ShowStartMenu` runs. Refuted if a cursor view shows during input.
- U2 (the save dialog's invisibility): continue U1 test-side through SAVE: predicted text while each message prints, None at both
  yes/nos, no ui.
- U3 (frame counter): log `get_frame_count()` on the first look after a boot with a `.sav` and no `.ss1` (predicted small) and after
  a `.ss1` load (predicted the state's value), or read mGBA's video serialization.
- U4 (a save's cost): the first live save's frames from START to `player_free`.
- U5 (H1, the NEW GAME hazard): an in-process run on a `.sav` boot stopped at the main menu, recording the choice (never let it save).
- U6 (the CONTINUE main menu view): the same boot, the `main_menu` options and cursor (predicted ("CONTINUE", "NEW GAME", "OPTION"),
  cursor 0).
- U7 (`getstate`/`setstate` under the purity gate): a plant in a COPY of the package, then `check_purity.py` on the copy.
- U8 (`sSaveDialogCallback` in the symbol table): `get_symbol("sSaveDialogCallback")` test-side.
- U9 (H2, after the credits): a chapter-24 tail fixture driven to the title with the play brain; predicted "stuck: an unexpected title".

---

## 10. Corrections to earlier notes

- `2026-10-28-R5-recon-code.md` §8.1: "The eyes can READ the start menu, its cursor and its actions" is refuted for the menu WHILE IT
  TAKES INPUT (section 4.2: the decomp's task switch, and the project's own measured comment in `make_step41_fixtures.py:172-174`).
  Its other §8 claims (no skill saves; the purity rules; the launcher's modes; the world memory carry) agree with this note.
- `eyes/screens.py:228`'s comment "(runs HandleStartMenuInput)" is wrong per `src/start_menu.c:527-579`.
- The backlog's citations: `skills/intro.py:9` is the docstring line "the main menu NEW GAME ..." (the R5 recon said the same);
  `libmgba.py:141` is `sandbox-pokebot/modules/libmgba.py`'s comment over the startup `.ss1` load, while the WRITE is `shutdown`
  via `atexit` (`:159-161`, `:231-241`); "`_Memory` is not carried (`brain/goals.py:62`)" is better cited as `brain/goals.py:447-450`
  ("the memory is carried between sessions, `AI_PLAYER_WORLD`; this goal manager's own memory is not").
