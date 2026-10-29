> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r5recon/01-code-map.md` (sha256 `a3feb9a4c5ddf4cd`). R5's recon, angle 1, OUR CODE: a read-only Claude subagent's NOTE, never truth (its own status line says so; the authoritative docs and the code win).
> **What the R5 build then MEASURED** (`2026-10-28-R5-BUILD-REPORT.md`; seed ledger #43, #45 and #49): the play loop ended a run "done" on the pass's look, whatever was on screen (this recon's reading of `mode.py:457-458`, confirmed); `ch1_clock` ends on a FREE screen (its `use` goal plays MOM's text out before the loop reads the mark); `ch2_dad` ends on a ONE-frame free read: DAD's warp to PETALBURG CITY frees the player for one frame and WALLY's tutorial (the city's ON_FRAME script) locks the controls on the next, which the game-facts note's section 4.3 (d) predicted. The AI's own `nav_free` reads that frame FREE, so a settle gated on it alone would not have run there.

# R5 recon, angle 1 (OUR CODE): how an AI-player run ends, and how a milestone switches goals

**Status: a NOTE, not truth** (CLAUDE.md: a subagent's output is a note). Read-only recon, 2026-10-28. Nothing was run: no
emulator, no driver, no test, no gate. Code read at `main` HEAD `f9474661` (working tree clean); `ai_player/mode.py` was last
changed in `c4c3ce8a` (2026-10-16), so the backlog's line numbers (2026-10-18) still match. Decomp: the PINNED clone
(`731ad5bf`, `tools/decomp.pin`) at `C:/Remote Projects/_decomp/pokeemerald`, read with `tools/decomp_lookup.py` and plain reads.

**Name clash.** "R5" here is the backlog item (the free-screen precondition, `2026-10-18-improvement-backlog.md:325-326`).
It is NOT the step-5 grader checks `R5.<NAME>` (`gates/rate_step5.py`).

Tags: **VERIFIED-code** (read here, quoted), **VERIFIED-decomp** (read in the pinned clone), **UNVERIFIED** (inference or a
claim not checked here).

---

## 0. The answer first (the headline carries the caveat)

1. **No guard exists. VERIFIED-code.** The run's "done" end does not look at the screen. It is checked on the pass's look
   (`mode.py:433` `look = hands.look()`) BEFORE the loop plays what is on screen (`mode.py:475` `if not nav_free(look):`).
   No frame passes between the two, and `_play_end` presses nothing. So the screen at "done" is whatever that look showed.
2. **But for the two GRADED chapter ends, that screen is free anyway, by the game's own script order. VERIFIED-decomp;
   the live frame UNVERIFIED.** `ch1_pokedex`'s last proof, `FLAG_ADVENTURE_STARTED`, and `ch2_wally`'s,
   `VAR_PETALBURG_GYM_STATE, 2`, are each set a few non-waiting commands before `releaseall` (section 5). A script's
   commands run in one loop until one waits, and `releaseall` hides the box. So the first look that shows the proof
   already shows the box gone and the script ended.
3. **For badge 1 the flag DOES flip before TM39's text (VERIFIED-decomp), yet the normal route still ends on a free
   screen (VERIFIED-code).** `RustboroCity_Gym/scripts.inc:18-19` set `FLAG_DEFEATED_RUSTBORO_GYM` and `FLAG_BADGE01_GET`;
   `:29` `giveitem ITEM_TM_ROCK_TOMB` and `:32` `msgbox RustboroCity_Gym_Text_ExplainRockTomb` come after. But ROXANNE is
   fought inside a `talk` goal, and `talk_to` ends with `play_out`. `play_out` returns `None` only `if nav_free(look)`
   (`skills/story.py:154-155`), so the TM39 text is pressed through before the goal returns. Only then does the play loop
   read the marks. The adversarial note `2026-10-15-ch34-recon/08-verify-gaps.md:24` already ruled
   `| Gap 4: "done" while a box is still up | **NOT REAL for chapter 4** |`. I re-read that route on today's code and it
   still holds.
   ⇒ **The backlog's R5 evidence line, "the run ends 'done' mid-box" (`improvement-backlog.md:325-326`, from
   `00-RECON-NOTE.md:375-383`), repeats the recon's claim without the verifier's refutation.** On today's code, R5 is
   real for four reasons:
   - (a) nothing GUARDS it;
   - (b) the residual early-return routes (section 3.3) can still end "done" with a screen up;
   - (c) R1's save needs a free screen;
   - (d) a chained chapter starts from the raw emulator state of the frame the brain returned (section 8.4).
4. **The goal switch after a milestone already waits for a free screen. VERIFIED-code.** The next goal is chosen only on a
   look that passed `nav_free` and the `SETTLE_FREE` window (`mode.py:475-494`; LESSONS PL-2, GATED). "Done" is the one
   boundary that skips that order.
5. **The AI never saves. VERIFIED-code (by absence).** No play-loop code opens the START menu or chooses SAVE. A run is
   resumable only through the framework's `atexit` state file, which is written on a CLEAN exit
   (`sandbox-pokebot/modules/libmgba.py:141`, `:160`). The launcher's hard kill skips it.
6. **Hard constraints on any R5 edit:**
   - `live_step5.py:350` compares the end reason by EXACT string (`reason == f"{run.arm.brain}: done: {target} reached"`).
   - Mutant G226 anchors on the exact text of `mode.py:457-458` (`revert_step5.py:1010-1015`). A non-unique or missing
     anchor raises (`revert_step5.py:1536-1537`).
   - 36 mutant edits anchor on `mode.py` text in all (`grep -c "(MODE, " revert_step5.py`).
   - `_play_end` is a plain function, not a generator (`mode.py:647`), so it cannot settle the screen.
   - A census waiver covers `_play_end`'s call sites (`gates/census_waivers.json:8-9`).
   - Settle frames count against the run's frame budget (`mode.py:806-813`).

---

## 1. The end of a run, end to end (brain -> host -> framework -> driver)

| Step | Where | What (quote) |
|---|---|---|
| The play loop returns its reason | `mode.py:457-458` | `if milestone is None or index > target:` / `return self._play_end(hands, story, manager, runner, report, "done", f"{options.target} reached")` |
| `_play_end` reports, presses nothing | `mode.py:647-682` | Closes the wait and push watchers' open stretches (`waits.finish()`, `pushes.wind_up()`), tells and notes the end record, and `return f"{kind}: {why}"` (`:682`) |
| The skill's frame bound hands it back | `mode.py:802-815` | `except StopIteration as done:` / `return str(done.value)`. No frame passes |
| `HandsBrain.play` closes | `mode.py:303-318` | `hands.pad.finish()` (`:304`, only flushes a log record, `hands/pad.py:165-167`), `last = hands.look()` (`:305`), recorded WHOLE: `decision="end" ... full=True` (`:306`), the world snapshot `self._save_world("the end of the run")` (`:308`), `return f"{options.brain}: {outcome}"` (`:318`) |
| The host exits | `host/session.py:324-327` | `reason = yield from self._steps(self.brain.play(...))` then `self.lifecycle.give_up(str(reason), EXIT_OK)` |
| | `host/lifecycle.py:138-185` | Writes the verdict file, then `sys.exit(code)` (`:185`) |
| The framework saves the emulator state on the way out | `sandbox-pokebot/modules/libmgba.py:141-146`, `:160`, `:231-241` | `# Whenever the emulator closes, it stores the current state in current_state.ss1.`, `atexit.register(self.shutdown)`, and `shutdown` -> `self.create_save_state()` |
| The live driver keeps that state | `ai_player/gates/live_step5.py:497-501` | `state = profile_dir / launcher.STATE_FILE` ... `shutil.copy2(state, keep)` (as `end_state.ss1`) |
| The in-process harness saves its own | `ai_player/gates/play_harness.py:951-953` | `save_end.write_bytes(emulator.get_save_state())`, at the frame the brain returned (its loop `break`s on `StopIteration` before `run_single_frame`, `:878-884`) |

⇒ **Whatever is on screen at "done" is exactly what the next chained run starts inside** (section 8.4). The `decision: "end"`
record of `actions.jsonl` also holds the full last observation of that frame (`mode.py:305-306`).

---

## 2. One pass of the play loop, in order (`mode.py:419-548`)

| # | Lines | What happens | Frames pass? |
|---|---|---|---|
| 1 | 421-425 | The no-frame-passed bound -> `stuck` | no |
| 2 | 430-432 | `_count_losses` -> `stuck` at `MAX_LOSSES` (3, `:105`) | no |
| 3 | **433** | `look = hands.look()`: the ONE look the pass decides on | no |
| 4 | 435-440 | The milestone index from the marks (`manager.milestone`); unchanged while the marks are unread (`last`); index 0 on the title screen | no |
| 5 | 441-443 | Story reloaded for the player's gender | no |
| 6 | 444-449 | **Milestone changed:** `_milestone_line` logs each milestone passed (`:624-645`), resets `changed_at` and `heals_counted`, and calls `nav.story_moved()` (`navigator.py:767-778`) | no |
| 7 | 451-456 | Real progress resets the patience | no |
| 8 | **457-458** | **DONE: `index > target` -> `_play_end(... "done" ...)`. The screen is not consulted.** | no |
| 9 | 459-467 | The intro: `play_intro`, and `stuck` on a second intro or one that did not reach the truck | yes (the intro) |
| 10 | 471-474 | `STORY_PATIENCE` (120,000 frames, `:104`) -> `stuck`, *"checked on EVERY pass, not only when the player is free"* (`:468`) | no |
| 11 | **475-481** | **Not free -> `play_out` the screen.** On a stop that is not a lost battle: one `pad.busy` frame, then `continue` | yes |
| 12 | 482-487 | Within `SETTLE_FREE` (30, `:115`) frames of a map change -> `pad.busy`, then `continue` | yes |
| 13 | 488-493 | Drift step; the scene between two goals is credited to the story | no |
| 14 | **494** | **`goal = manager.next_goal(look, world, milestone, index)`: reached only on a free, settled look** | no |
| 15 | 498-501 | `give_up` (out of ideas) -> `stuck` | no |
| 16 | 502-518 | The thinking pause; a scene that began meanwhile DROPS the goal and `continue`s (`:505-518`) | yes |
| 17 | 519-547 | `runner.pursue(goal, milestone, index, current)` (`:522`); its yield, accounting, `moved_story = current(after) != index` (`:540`) | yes (the goal) |
| 18 | 548 | `PLAY_PASSES_MAX` -> `stuck` | |

`current` (`mode.py:412-413`) is the milestone index of any look:
`manager.milestone(seen, visited)[0] if seen.progress is not None and seen.progress.marks else last[0]`. The goal runner
receives it so it can tell when the story moved (section 6).

---

## 3. The "done" path in detail

### 3.1 What decides it (VERIFIED-code)
- `GoalManager.milestone` (`brain/goals.py:927-940`) returns the first REQUIRED milestone whose proofs do not all hold.
  `if milestone.optional: continue` skips the gym trainers. A waypoint counts once the AI `visited` that map.
  `return len(self.story.milestones), None` when every proof holds.
- The proofs are flags and vars read from save block 1 every look (`host/eyes.py:323-331` `_marks`, `:1037-1048`
  `_progress`). They are not read while the save blocks may be moving (`host/eyes.py:371-379`).
- `Milestone.done` (`knowledge/story.py:82-88`) returns None when a proof was not read, and the loop then keeps `last`.
- The target index comes from `story.index(options.target)` (`mode.py:395`). The target is `AI_PLAYER_TARGET`, default
  `ch1_pokedex` (`options.py:219-220`).
- `milestone is None` is the "every milestone proven" case. For the last target, `ch4_roxanne` (index 19), it coincides
  with `index > target`.

### 3.2 What the screen can be at that moment
- The decision uses `look` from `:433` and nothing about `look.screen`. **No frame passes** from `:433` to `:458`
  (`:434-456` contain no `yield`).
- **The screen can therefore be any screen on which the marks already pass the target:** a text box, a fade, a battle,
  a menu. Whether that happens depends on WHEN the proof flips relative to the screen (section 5) and on which skill
  handed control back to the loop top (3.3).

### 3.3 How the loop top is reached with a screen that is NOT free (each is a route to "done mid-screen" when the target's proof has already flipped)
- **(a) `play_out` gave up.** At `mode.py:476-481`, after a stop, the loop waits ONE frame (`hands.pad.busy("waiting for
  the screen to settle after a stop")`) and `continue`s. `play_out` stops on any `handle` stop:
  - `"stuck: a scene: <advance outcome>"` (`navigator.py:1098`);
  - `"stuck: an unexpected <menu> on screen"` (`:1094-1097`);
  - `"stuck: a scene that did not end"` after `SCENE_TURNS = 8` (`:241`, `:1099`);
  - `"stuck: {SCENE_ROUNDS} scenes and battles in a row"` (`skills/story.py:63`, `:159`).
  
  `advance` itself returns `"stuck:..."` after `STALL_FRAMES = 300` unchanged frames (`hands/dialogue.py:62`, `:227-231`).
- **(b) A goal returned mid-screen.**
  - `talk_to` returns `f"talked; then {stop}"` or `"interrupted ...: {stop}"` with whatever `play_out`'s stop left up
    (`skills/story.py:165-167`, `:171-174`, `:179-183`, `:185-186`). This is the verifier's "residual (low)"
    (`08-verify-gaps.md:148-149`).
  - **Walk goals** (`go`, `look_around`, `follow`, `find`, `explore`, `find_center`, `seek`, the walk to the grass) end
    through `Navigator.run`, which checks the goal's stop BEFORE the screen: `if intent.done(look):` /
    `return f"done: {intent.name} ..."` / `if not nav_free(look):` (`navigator.py:1253-1255`). Their stop includes
    `moved_on` (section 6).
  - `handle` returns right after the battler (`navigator.py:1049-1067`), so a walk's next top look can be the
    post-battle screen.
  - `handle` returns after `settle` once *"the map HAS changed"* (`navigator.py:942-955`, break at `:950-951`), so a walk's
    next top look can be a fade.
- **(c) The thinking-pause drop.** It `continue`s with a scene up (`mode.py:505-518`). This does not end "done" by
  itself: that scene has not been played yet, so its flags have normally not flipped.
- **(d) The intro.** It ends "in the truck" (`skills/intro.py:90-94`), a scene. This matters only for a target of
  `ch1_intro`.

### 3.4 The chapter-4 route, re-checked on today's code (VERIFIED-code)
1. The `talk` step: `_story_step_goal`, *"use / talk: on its map, find what LOOKS like what it names"*
   (`goals.py:1475-1479`).
2. `GoalRunner._pursue`'s `use`/`talk`/`chat` branch calls `talk_to` (`goals.py:2046-2057`).
3. `talk_to` calls `play_out` (`skills/story.py:185-186`).
4. `play_out` loops `nav.handle` until `nav_free` (`:152-158`).
5. `handle` plays ROXANNE's battle (the battler), returns None (`navigator.py:1067`), then plays the post-battle script
   through `advance(..., lambda l: nav_free(l) or in_battle(l), ...)` (`:1082`). `advance` presses A on every waiting page
   (`hands/dialogue.py:209-221`), so the badge text, TM39's text and its explanation are all pressed through.
6. Only after `nav_free` does the goal return, and only on the NEXT pass's look (`mode.py:433`) is
   `index > target` read.

⇒ The badge's normal route ends "done" on a free screen. **UNVERIFIED live:** the AI has never reached ROXANNE
(the frontier is chapter 2, `PROJECT KNOWLEDGE/ai-frontier.txt`).

### 3.5 One adjacent risk on the same route (UNVERIFIED live; it does not end the run mid-box)
- The badge fanfare is 340 frames: `[FANFARE_OBTAIN_BADGE] = { MUS_OBTAIN_BADGE, 340 }` (decomp `src/sound.c:43`), run by
  `Common_EventScript_PlayGymBadgeFanfare` (`data/event_scripts.s:718-720`) BEFORE the flags
  (`RustboroCity_Gym/scripts.inc:16`).
- `advance`'s stall limit is 300 frames unless the eyes NAME the scene (`hands/dialogue.py:125-128`). No fanfare is named:
  `SCENE_CALLBACKS`, `SCENE_TASKS` and `SCENE_STATES` (`eyes/screens.py:334-398`) list no fanfare task.
- So a false `"stuck:reading along: a text is printing"` may fire about 300 frames into the badge fanfare, if nothing in
  `seen_now` (`hands/dialogue.py:116-122`) changes during it.
- Consequence:
  - `talk_to` returns `"talked; then stuck: ..."` before the flags flip.
  - The next pass is not free, and `play_out` plays the rest: the flags flip, the TM39 text is pressed, and "done" follows
    on a free screen.
  - After the flags, the TM fanfare is 220 frames (`src/sound.c:41`), under 300.
  - Not an R5 failure; worth one line in R5's development.

---

## 4. Every other end of a run, and what the screen can be there

| End | Where | Reason text | Screen at that moment |
|---|---|---|---|
| No frame passed for `STILL_PASSES_MAX` passes | `mode.py:421-425` | `stuck: N passes ... let no frame pass` | Anything |
| `MAX_LOSSES` | `mode.py:430-432` | `stuck: 3 battles lost (MAX_LOSSES 3)` | `handle` returns `"stuck: the battle was lost ..."` right after the battler (`navigator.py:1058-1059`), so likely mid-whiteout. UNVERIFIED live |
| Intro twice / intro failed | `mode.py:461-462`, `:465-466` | `stuck: the New Game intro again` / the intro's outcome | Title or intro screens |
| Patience | `mode.py:471-474` | `stuck: no progress for N frames ...` | Anything (deliberately checked on non-free screens too, `:468-470`) |
| Out of ideas (`give_up` goal) | `mode.py:498-501` | `stuck: <goal.reason>` | Free (it is chosen on a free look) |
| `PLAY_PASSES_MAX` | `mode.py:548` | `stuck: 100000 passes ...` | Anything |
| The skill's frame budget | `mode.py:812-813` | `stopped: not finished within N frames` | Anything. `_play_end` is NOT called (`skill.close()`, `:815`), so no end record from the play loop; the end look is still recorded at `:305-306` |
| Host ends | `host/session.py:287-319`; `host/lifecycle.py:9-25` | `interrupted`, `parked-manual`, `frame-budget`, `wall-clock`, `isolation-lost`, `crash` | Anything; each ends with `sys.exit`, so the framework's `atexit` state is still written |
| Launcher HARD kill | `host/launcher.py:406-414` (`kill_tree`, `:351-372`, psutil `kill` / `taskkill /F`) | exit 124, no verdict | **No `atexit`, so `current_state.ss1` is not written by this run** (inference from `atexit`; UNVERIFIED as measured) |

---

## 5. Chapter ends against the game's script: when each proof flips (decomp `731ad5bf`)

Milestone proofs: `ai_player/knowledge/milestones.json` (printed here from the file):
- `ch1_pokedex`: `RECEIVED_POKEDEX_FROM_BIRCH`, `SYS_POKEDEX_GET`, `ADVENTURE_STARTED`
- `ch2_wally`: `PETALBURG_GYM_STATE >= 2`
- `ch3_rustboro`: `VISITED_RUSTBORO_CITY`
- `ch4_roxanne`: `DEFEATED_RUSTBORO_GYM`, `BADGE01_GET`

Graded targets: `ch1_pokedex` (`options.py:220`) and `CH2_TARGET = "ch2_wally"` (`rate_step5.py:192`).

| Target (index) | Last proof set at | What follows it in the script | Screen at "done" today |
|---|---|---|---|
| `ch1_pokedex` (9) | `LittlerootTown_ProfessorBirchsLab/scripts.inc:510` `setflag FLAG_ADVENTURE_STARTED` (the POKéDEX flags at `:537`, `:539`, earlier, inside `ReceivePokedex`) | `:511-513` three `setvar`s, `:514` `releaseall`, `end` | **Free, by script order.** VERIFIED-decomp; the eyes' reading on that frame is UNVERIFIED |
| `ch2_wally` (14) | `PetalburgCity_Gym/scripts.inc:90` `setvar VAR_PETALBURG_GYM_STATE, 2` (after `:89` `msgbox PetalburgCity_Gym_Text_DadGoCollectBadges`, already answered) | `:91` `releaseall`, `end` | **Free, by script order** (same caveat) |
| `ch3_rustboro` (17) | `RustboroCity/scripts.inc:6-7` `RustboroCity_OnTransition:` / `setflag FLAG_VISITED_RUSTBORO_CITY` (a map-transition script) | No text. The ON_FRAME table fires only at `VAR_RUSTBORO_CITY_STATE, 6` (`:27-28`), not on the first visit | **Arrival.** A walk's `moved_on` stop fires on the first look after the map change, and "done" comes before any `SETTLE_FREE` wait. Mid-step, or mid-fade if entered by a warp. UNVERIFIED live |
| `ch4_roxanne` (19) | `RustboroCity_Gym/scripts.inc:18-19` (after `:17` `msgbox ..._StoneBadgeInfoTakeThis`) | `:25` `goto ..._GiveRockTomb` -> `:29` `giveitem ITEM_TM_ROCK_TOMB` (TM fanfare + texts) -> `:32` `msgbox ..._ExplainRockTomb` -> `:33` `release` | **Mid-script in the GAME; free in OUR loop** (section 3.4) |

**Why "free by script order" holds (VERIFIED-decomp):**
- Script commands run in one `while (1)` loop until one returns TRUE (waits) (`src/script.c:91-116`).
- When the script ends, `sGlobalScriptContextStatus = CONTEXT_SHUTDOWN;` and `UnlockPlayerFieldControls();` run in the
  same call (`src/script.c:230-234`).
- `ScrCmd_releaseall` calls `HideFieldMessageBox();` (`src/scrcmd.c:1240-1244`), which sets
  `sFieldMessageBoxMode = FIELD_MESSAGE_BOX_HIDDEN;` (`src/field_message_box.c:131-135`).

**Support from the graders (VERIFIED-code, measured by them):** `rate_step5.py:1290-1292` says *"A run the AI ends AT its
target can end before the recorder confirms the change (measured on the A2 smoke, CH2 seed 1303)"*. So a chapter-2 run
really ends within the recorder's 30-frame sampling period of the var flip.

**Proofs that flip MID-scene (not targets today, but milestone switches):**
- `ch2_dad`: `setflag FLAG_HIDE_PETALBURG_CITY_WALLYS_MOM` (`PetalburgCity_Gym/scripts.inc:181`) comes before
  `warp MAP_PETALBURG_CITY, 15, 8` (`:188`), and WALLY's tutorial follows.
- The town visits are set in ON_TRANSITION scripts: `OldaleTown/scripts.inc:5-7`, `PetalburgCity/scripts.inc:7`,
  `LittlerootTown/scripts.inc:38`.
- Not checked here: `ch1_mom`, `ch1_clock`, `ch1_rival_house`, `ch1_birch`, `ch1_starter`, `ch1_lab` (UNVERIFIED).

**Later gyms ("the same shape holds for every gym", `2026-10-19-backlog-round2/03-ai-player.md:128`):**
- **Dewford, VERIFIED-decomp.** `setflag FLAG_BADGE02_GET` (`DewfordTown_Gym/scripts.inc:151`) comes before
  `call DewfordTown_Gym_EventScript_GiveBulkUp` (`:157`) and the Match Call registration (`:158-163`). That registration
  has `closemessage` / `delay 30` inside the still-running script (`:158-159`, `:163-164`). ⇒ A "free" test built on
  "no text box" alone would fire there. It must include the script and controls state, as `player_free` does.
- **The other six gyms: line order only, UNVERIFIED as execution order.** The badge `setflag` line precedes the first
  `giveitem ITEM_TM` line in Mauville (94 < 115), Lavaridge 1F (62 < 82), Petalburg (369 < 394), Fortree (34 < 52),
  Mossdeep (66 < 93) and Sootopolis 1F (97 < 118).
- `VAR_SCOTT_STATE` is no milestone mark (`08-verify-gaps.md:146-147`), so it can end nothing.

---

## 6. How a milestone switches goals today (VERIFIED-code)

- **Detection.** Every pass (`mode.py:435-449`), from the marks. On a change:
  - the MILESTONE lines are logged (`_milestone_line`, `:624-645`);
  - the patience restarts (`changed_at`, `:446`);
  - `nav.story_moved()` forgets the ping-pongs and the cut-off marks (`navigator.py:767-778`).
- **A goal in progress when the story moves.**
  - Walk-type goals stop through `moved_on = lambda look: current(look) != index` (`goals.py:1882`). It is used in:
    - `walk_done` (`:1899-1901` `if moved_on(look):` / `return True`);
    - `find_center` (`:2021`, `:2027`);
    - `seek` (`:2043-2044`);
    - the walk to the grass (`:2084`);
    - `_back_to_ball`, *"not picked up: the story moved on on the way"* (`:2152-2153`).
  - `talk`, `use`, `chat`, `heal`, `shop` and the roams do not watch the milestone; a talk plays its conversation out to
    free (`skills/story.py:185-186`).
- **After the goal.** `moved_story = current(after) != index` (`mode.py:540`) feeds the accounting only
  (`manager.spent`, `manager.after_goal`, `:541-546`).
- **The switch itself.** The next decision is made only after:
  - (i) the screen is free (`mode.py:475-481`);
  - (ii) `SETTLE_FREE` frames have passed since a map change (`:482-487`, *"the screen must stay free this many frames
    before a goal is chosen"*, `:112-113`);
  - (iii) the decision's thinking pause shows no new scene (`:504-518`).
  
  This is LESSONS PL-2, GATED (`ai_player/LESSONS.md:249-253`).
- **Per-milestone memory switches by key.** Nothing is cleared: `fight_prep`, `exhausted`, `blocked`, `asked_rounds` and
  `scene_walls` are keyed by milestone id (`goals.py:421-423`, `:467-472`, `:446`).
- **No chapter concept exists in play code.** `Milestone.chapter` (`knowledge/story.py:64`) has no reader outside
  `gates/`. Grep for `.chapter` in `ai_player` (excluding `gates/`) finds nothing.
- ⇒ **R5's "post-milestone goal switch" already has its free-screen precondition, except for "done".** A "goal switch at a
  chapter end" (heal, then save, instead of ending) does not exist: the run simply ends.

---

## 7. Perception of "a free screen": the predicates, what they read, and how far to trust them

The eyes' screen fields come from `host/eyes.py:427-460` `_screen`:
- `game_state`: the framework's `get_game_state().name` (`:430`).
- `text_box_open`: `sFieldMessageBoxMode != 0` (`:435`, `:457`).
- `fading`: the `gPaletteFade` active bit (`:448-449`).
- `script_running`: `sGlobalScriptContextStatus != SCRIPT_CONTEXT_SHUTDOWN` (2, `eyes/view.py:455`) (`:453`, `:459`).
- `controls_locked`: `sLockFieldControls` (`:454`, `:460`).
- `waits_for_button`: `_waits_for_button` (`:742-756`, a script's `waitbuttonpress` or a text printer's WAIT, CLEAR or
  SCROLL_START state), then `task_wait` (`:439-441`).
- `ui`: the active tasks (`:437`, `:450`).

| Predicate | Where | Definition (quote) | Use for R5 |
|---|---|---|---|
| `player_free` | `hands/dialogue.py:131-137` | `screen.game_state == "OVERWORLD" and not screen.script_running and not screen.controls_locked and screen.ui is None and not screen.text_box_open and not screen.waits_for_button and player is not None and not player.settling` | It IS the backlog's "no text box, controls unlocked, the overworld" |
| `nav_free` | `brain/navigator.py:245-247` | `return player_free(look) and not look.screen.fading and look.view is not None` | **The loop's free test; the natural R5 predicate** |
| `is_scene` | `navigator.py:258-263` | script, lock, wait, box or ui | What `handle` treats as a scene |
| `awaits_press` | `hands/dialogue.py:236-245` | a wait or an input-taking menu | "Never idle" (PL-1) |
| `busy_reason` | `hands/dialogue.py:89-113` | Names what plays; the catch-all `GENERIC_BUSY` (`:73`) | Log reason only |
| `Navigator.settle` | `navigator.py:942-955` | Breaks on `nav_free` OR a wait OR a ui OR a battle OR *"the map HAS changed"* | **NOT a free settle: do not reuse it for R5** |
| `SETTLE_FREE` | `mode.py:115`, `:482-487` | 30 free frames after a map change, before a goal | Applies to goal choice only, not to "done" |
| `WorldMemory.observe` "settled" | `world/memory.py:618-619` | Player read, not settling, OVERWORLD, not fading, a view | **Position-learning only: ignores text, script and lock. Not a free test** |
| `settled_position` | `eyes/view.py:333-341` | Object tile == save-block tile, else None (*"6 frames of CHANGE_MAP, measured"*) | Behind `player.settling` |

**Reliability notes (from the code's own docstrings; not re-measured here):**
- A part the eyes cannot read becomes None and is reported in `problems` (`host/eyes.py:416-424` `_guarded`). For the
  screen this defaults toward "free":
  - `status is not None and status != SHUTDOWN` makes `script_running` False;
  - `bool(locked)` makes `controls_locked` False;
  - `... or 0` makes `text_box_open` False.
  
  Inference, UNVERIFIED that it happens. `player` is None while the save blocks move (`:371-379`), which makes
  `nav_free` False on those frames.
- `script_waits_for_button` refuses a finished script's leftover native pointer. Both the mode check and the status check
  are needed, *"neither is load-bearing alone; together they are"* (`eyes/view.py:462-470`, measured by
  `gates/live_step1.py` arm SW).
- `text` can be stale: `with no printer active, "the last message" can be an OLD one when a menu opens with no message of
  its own (the start menu): text is what was printed last, not proof it is still drawn` (`host/eyes.py:716-717`). Do not
  use `text is None` as "free".
- No named scene covers the fanfares (section 3.5).

**Unknown-screen handling today (VERIFIED-code):**
- `advance` stops WITHOUT pressing on any menu: `return f"menu:{ui.kind}"` (`hands/dialogue.py:206-208`).
- `handle` hands that menu to `on_menu` (`navigator.py:1094-1097`). The play brain wires
  `nav.on_menu = lambda kind, why: self._story_menu(...)` (`mode.py:367`). `_story_menu` (`mode.py:611-622`) knows only
  `choose_starter`, `clock`, `mart_buy` and `mart_menu`; anything else gives
  `"stuck: an unexpected {kind} on screen"`.
- The loop then replays `play_out` each pass until `STORY_PATIENCE`.
- With a target already passed, this is route 3.3(a): "done" with that menu up.

---

## 8. Saving and carry-over, today (the R1 + R2 context)

### 8.1 The AI never saves (VERIFIED-code, by absence)
- No play-loop file presses START in the overworld. The only `press("Start", ...)` is the title screen's
  (`skills/intro.py:111`).
- No skill chooses `SAVE`.
- The eyes can READ the start menu, its cursor and its actions:
  - `eyes/screens.py:228` `"StartMenuTask": "start_menu"`;
  - `START_MENU_ACTIONS` `:266-267` (with `"SAVE"`);
  - `:576-580`;
  - `host/eyes.py:502-505`.
- `hands/menus.py:120` `choose(hands, kind, option, why)` exists. Both are unused for saving.
- The intro always chooses NEW GAME: `skills/intro.py:113-115` `choose(hands, "main_menu", "NEW GAME", "a new game")`.
  (`:9` is the docstring line the backlog cites.)

### 8.2 The purity gate forbids every non-press save
- `STATE_CHANGING_NAMES` (`ai_player/gates/check_purity.py:537-550`) includes `"create_save_state"`,
  `"load_save_state"`, `"load_save_game"` and `"write_bytes"`. Rule (b) refuses naming any of them in a play-loop file.
- Rule (f) lets only `runlog.py` and the instrument write files.
- ⇒ An AI save must be START -> SAVE -> the yes/no prompts, played by the AI's own presses. Any new memory file goes
  through `runlog.RecordFile`.

### 8.3 What the framework and the launcher do
- `current_state.ss1` is written by `atexit` on a clean exit (`sandbox-pokebot/modules/libmgba.py:141-146`, `:160`,
  `:231-241`).
- Every in-game save is copied to `saves/` (`:161` `savedata_updated`, `:243-255`).
- The cartridge save is opened `"r+"` through mGBA's virtual file system (`:126-133`). Whether it is flushed to disk before
  a kill is UNVERIFIED (the backlog says the same).
- The launcher has three start modes (`host/launcher.py:179-209`):
  - `--fresh` deletes `current_state.ss1` and `current_save.sav`;
  - `--state` copies a fixture over `current_state.ss1`;
  - neither: *"resuming whatever the profile already holds"* (`:187-188`).

### 8.4 How chapters are chained today
- **The harness:** `begin = ["--state", start["_end_state"], "--world-in", start["_world"]]` (`rate_step5.py:715`), and
  `run_chain` (`:767-780`) only when chapter 1 reached the POKéDEX.
- **The live driver:** the CH1 arm's profile `current_state.ss1`, copied to `end_state.ss1`, then `--state` plus
  `AI_PLAYER_WORLD` (`live_step5.py:451-462`, `:497-507`).
- Both start chapter N+1 from the emulator state of the frame chapter N's brain returned. **A "done" with a box up would
  start the next chapter inside that box.**

### 8.5 Memory carried
- The WORLD memory is carried. It is appended to `world.jsonl` at every map change (`mode.py:786` `on_map_change`) and at
  the end (`:307-308`), and read from the LAST line (`world/memory.py:864-871`, a bare `json.loads(last)`; a torn last line
  would raise, UNVERIFIED as observed). It carries `landmarks` and `spoke` (`world/memory.py:812-815`).
- **The goal manager's memory is NOT carried:**
  - *"(the memory is carried between sessions, `AI_PLAYER_WORLD`; this goal manager's own memory is not)"*
    (`brain/goals.py:447-450`);
  - a fresh `self.memory = _Memory()` per run (`:917`);
  - only `landmarks` and `spoke` are handed in (`mode.py:372`, `:376`).
  
  (The backlog's cite `brain/goals.py:62` is a docstring line about `known_before`, not this evidence.)
- Records are appended open-write-close per line, *"so a killed process leaves every record it finished"*
  (`ai_player/runlog.py:55-58`, `:76-84`). There is no fsync.

---

## 9. Drivers, gates and graders that touch a run's end

**Unit level (suite `units`, `tools/workflows/suite_map.json`):**
- `gates/test_goals.py` `PlayLoopTests` (`:827-1043`) drives the REAL `HandsBrain._play` with stand-ins:
  - `_LoopHands` (`:798-825`): the screen may be a function of the pad's frames;
  - a stand-in `GoalRunner` (`:858-886`);
  - a stand-in `play_out` that NEVER frees: `return "stuck: a screen that does not end"` after `PER_SCREEN = 5000` frames
    (`:836`, `:888-892`).
- `ProductiveWiringTests.test_the_play_loop_ends_when_its_target_is_reached` (`:3706-3711`) builds a FREE look past the
  target and asserts `reason == "done: ch1_pokedex reached"` and `pursued == []`.
- A text-box look for a test already exists:
  `replace(free, screen=replace(free.screen, text_box_open=True, waits_for_button=True, script_running=True, text=...))`
  (`:1006-1007`).

**Mutants (suite `revert_step5`):**
- G226 "the play loop does not end when its target is reached": its anchor is the exact text of `mode.py:457-458`
  (`revert_step5.py:1010-1015`).
- G227 covers `MAX_LOSSES` and G228 the patience (`:1016-1027`).
- The other four ends are waived (`census_waivers.json:8-9`): *"reached by no unit test, only by the live and sweep runs"*.
- A mutant anchor must be unique: `raise SystemExit(f"mutant anchor not unique ...")` (`revert_step5.py:1536-1537`).

**Sweep (`rate_step5.py`, GRADED, writes the seed ledger; never a routine regression, `suite_map.json` `_warning`) and
harness:**
- `play_harness.py` records who ended the run (`harness_stop`, `:911`), the frame equality (`:894-897`) and the end
  state (`:951-953`).
- `rate_step5.py` reads the GAME's end marks (`end = (data.get("story_truth") or {}).get("marks")`, `:1865`):
  - `"reached": bool(end.get("RECEIVED_POKEDEX_FROM_BIRCH"))` (`:2008`);
  - `"wally": bool(end.get("HIDE_PETALBURG_CITY_WALLYS_MOM"))` (`:1973`), with the var's change (`:1926`);
  - `frames_to_mark` with `at_end` (`:1288-1298`).
- The `harness_stop` and the end marks are what `R5.CH1_REACHED` and `R5.CH2_WALLY` (`:2071`, `:2518`) grade on.

**Live (`live_step5.py`, the real launcher):**
- `L5.PURITY_OUTCOME` (HONESTY): the reason must equal `"<brain>: done: <target> reached"` exactly (`:342-350`), judged
  both ways against the game's proof (`:353-367`).
- `L5.PURITY_ENDED` is REPORTED from the harness stop (`:326-339`).
- The end state is read by `truth_of` (`:502`).

**Nobody checks the screen at the end.** Grep of `ai_player/` and `tools/workflows/` for an end-screen check finds none.
`hands_harness.truth` reads `game_state` but no script, lock or box field (`gates/hands_harness.py:136-149`).
- The verifier's advice for an end-screen check: *"Keep it as a guard, never as evidence. Gap 4 needs its own fault arm
  (end the run inside the talk)"* (`08-verify-gaps.md:263`).
- A no-op passes such a check; on today's code it passes *"BY CONSTRUCTION"* (`:150`).

---

## 10. The rules an R5 change must keep

**LESSONS (`ai_player/LESSONS.md`):**
- PL-1, never idle (`:243-247`): a settle must PRESS through waiting text (`play_out` / `advance`), not watch it.
- PL-2, scenes first (`:249-253`, GATED by `SETTLE_FREE`, G56, G57).
- PL-3, *"A failure returns at once; never retry silently"* (`:255`): decide what "done" does when the screen will not
  free, and say it in the reason.
- PL-4, bound every loop (`:261-266`).
- PF-2: every new hook's mutant DELETES ITS CALL, enforced by the call census (`:121-125`; `gates/call_census.py:1-27`
  lists a changed function's sites, which must be covered or waived).
- PF-10: an after-state check must be able to FAIL (`:174-179`).
- PF-12: a unit-tested rule is not a chapter proof (`:187-191`).
- PF-17: a rule that ENDS a run is a claim about every state; develop it on the opening too (`:219-225`).
- PF-19: a harness's second path must not reuse a framework read the eyes found wrong (`:234-239`).

**Purity (`gates/check_purity.py` header):**
- (a) imports only `from ai_player.x import Name` with `Name` in `__all__`.
- (b) no state-changing names.
- (c) `mode.py` may not import `ai_player.host`; the play loop may not import `gates`.
- (f) file writes only through `runlog.py`.

**Fairness (`gates/check_fairness.py:73-87` `FLAG_DOORS`):**
- Marks may be read only in the listed functions: `GoalManager.milestone`, `HandsBrain._play`, `_play.current`,
  `_milestone_line` and `marks_of`.
- A new helper that reads `.marks` (for example "is the target still reached after settling?") needs a reviewed door. A
  helper that only reads the screen needs none.

**Graders and anchors:**
- The exact end string (`live_step5.py:350`).
- G226's anchor (`revert_step5.py:1010-1015`) and the other `mode.py`-anchored edits (`grep -n "(MODE, " revert_step5.py`:
  36 hits, G226's included).
- `_play_end`'s census waiver (`census_waivers.json:8-9`) names its call sites as "unchanged since step 5". Changing
  them re-opens the census.

**Never change the BOT's default behaviour** (CLAUDE.md). R5 is AI-only code; nothing in `sandbox-pokebot/` is needed.

---

## 11. Where R5 would touch (a map for the builder, not a design)

- **The one site.** `mode.py:457-458`. Today the order is: done (`:457`), then patience (`:471`), then free -> `play_out`
  (`:475`). Two shapes are possible; each is a choice for the builder:
  - **(i) Play the screen out, then end.** When `index > target` and `not nav_free(look)`, `yield from play_out(...)`
    first, then end "done" on a free look.
    - If `play_out` returns a stop with the screen still up, PL-3 asks for a reason that says so. But the HONESTY check
      wants exactly `done: <target> reached` whenever the game's proof holds (`live_step5.py:357`:
      `and so is a proof under a stop reason ("stuck" while the game shows the target)`, after "a lie").
    - ⇒ The reason string for "reached but the screen never freed" needs a ruling or a grader change.
  - **(ii) Move the done check below `:475-487`.** Then patience (`:471`) can end a reached-but-stuck screen "stuck", and
    `SETTLE_FREE` also applies to "done" (it would cover the ch3 arrival case). This reorders mutants G226 and G228's
    anchored text.
- **`_play_end` cannot settle.** It is not a generator (`mode.py:647`, `-> str`). Making it one changes all 8
  `return self._play_end(...)` sites (`:424`, `:432`, `:458`, `:462`, `:466`, `:472`, `:501`, `:548`), their mutant
  anchors and the census waiver.
- **A `settle_to_free` helper.** No such name exists anywhere in the code (grep). `nav_free` plus `play_out` is already
  "play the screen until free, bounded" (`skills/story.py:148-159`). A new helper must be in its module's `__all__`
  (purity rule a), get a call-deleting mutant (PF-2), and be told every look like the others (`hands.watchers`).
- **The frame budget.** Settle frames come out of `settings.frames` (`mode.py:806-813`). A target reached in the last
  frames could become `stopped: not finished within N frames`, which `L5.PURITY_OUTCOME` reads as no claim.
- **Test seams that exist today:**
  - `PlayLoopTests.run_loop` with a screen function and a patched `play_out` (`test_goals.py:838-900`, `:888-892`);
  - the text-box look (`:1006-1007`);
  - `ch1_through("ch2_oldale")` for a look past `ch1_pokedex` (`:3708`).
  
  The FAULT half is today's behaviour: "done" at once with `screens == []`.
- **A natural live or harness arm for "done while not free" does not exist for chapters 1-2** (both end free by script
  order, section 5). Two candidates, both UNVERIFIED:
  - a harness run with `--target ch2_oldale` or `ch3_rustboro` (proof set ON_TRANSITION, "done" on arrival);
  - an injected early `play_out` return inside the badge talk, which is the verifier's "end the run inside the talk".
  
  `play_harness.py --checkpoints` (`:986`) saves a state at every mark change, a way to build such a fixture from the
  AI's own run.

---

## 12. UNVERIFIED, and questions only a live probe or the user can answer

1. On the exact frame `ADVENTURE_STARTED` (ch1) or `VAR_PETALBURG_GYM_STATE = 2` (ch2) first reads set, do the eyes
   already read `nav_free`? (A live look at the frame of the flip; one probe each.)
2. Does `advance`'s 300-frame stall fire during the 340-frame badge fanfare (does any `seen_now` field change during
   `waitfanfare`)? The same for Dewford's Match Call `delay 30` plus fanfare.
3. Is the cartridge save (`current_save.sav`, mGBA's `r+` file) flushed before a kill? (R1's question, unchanged.)
4. A user ruling, if R5 settles before "done": when the target's proof holds but the screen never frees, is the run
   "done" (the game's truth, HONESTY-safe) or "stuck" (PL-3)? **No prior ruling exists (CLAUDE.md rule 11 checked).**
   `py -3.12 tools/decomp_lookup.py ask "done free screen mid-box save R5 settle"` printed
   `NO PRIOR RULING OR FACT FOUND`. A grep of `06-DECISIONS-LOG.md` for free screen, mid-box, "box is still up",
   `settle_to_free`, "Gap 4" and "done while" found only `06:7345`, the STORY BOT's unrelated "Gap 4" (the plateau
   walk-off), a name clash. The both-ways outcome rule itself comes from the step-5.3 re-sourcing build
   (`live_step5.py:354-359`, "item 12: the A2 decision addendum's row 18").
5. Should "free" for a chapter end include the `SETTLE_FREE` window after a map change, as goal choice does? It matters
   for an ON_TRANSITION proof (ch3_rustboro): "done" on arrival, before any arrival scene could begin. This is a design
   choice.
6. The other gyms' badge-before-TM order is line order only (section 5); execution order needs each script read.
