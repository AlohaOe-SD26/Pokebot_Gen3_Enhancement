> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r5recon/03-game-facts.md` (sha256 `2fd9b03898bc8717`). R5's recon, angle 3, THE GAME (the pinned decomp): a read-only Claude subagent's NOTE, never truth (its own status line says so; the authoritative docs and the code win).
> **What the R5 build then MEASURED** (`2026-10-28-R5-BUILD-REPORT.md`; seed ledger #43, #45 and #49): the play loop ended a run "done" on the pass's look, whatever was on screen (this recon's reading of `mode.py:457-458`, confirmed); `ch1_clock` ends on a FREE screen (its `use` goal plays MOM's text out before the loop reads the mark); `ch2_dad` ends on a ONE-frame free read: DAD's warp to PETALBURG CITY frees the player for one frame and WALLY's tutorial (the city's ON_FRAME script) locks the controls on the next, which the game-facts note's section 4.3 (d) predicted. The AI's own `nav_free` reads that frame FREE, so a settle gated on it alone would not have run there.

# 03: THE GAME. What the pinned decomp says backlog R5 (a FREE-SCREEN precondition) depends on

Angle 3 of the R5 recon. Written 2026-10-28 by a READ-ONLY Claude subagent. **This is a NOTE, not truth.** The authoritative
docs win on any contradiction until a claim here is verified (CLAUDE.md, "their output is a note, never truth").

- **Source.** pret/pokeemerald at the PINNED commit `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` (`tools/decomp.pin:1`). The
  local clone is `C:/Remote Projects/_decomp/pokeemerald`, and its `git rev-parse HEAD` printed that same SHA this session.
  Every `data/…`, `src/…`, `include/…` and `asm/…` path below is in that clone. `py -3.12 tools/decomp_lookup.py ask` on
  "free screen / save / R5 / Wally tutorial" found **NO PRIOR RULING OR FACT** (exit 3). Its one `FLAG_BADGE01_GET`
  ruling hit is unrelated (06:8865, the A/B runner).
- **Tags.**
  - **VERIFIED-decomp**: read in the pinned source this session.
  - **VERIFIED-code**: read in this repo's code.
  - **DERIVED**: follows from the cited lines by reasoning. It was not measured.
  - **UNVERIFIED**: not checked; a live probe or the user is needed.
  - Nothing here was run in an emulator.
- **Name clash.** "R5" here is backlog item R5 (`PROJECT KNOWLEDGE/ai-research-notes/2026-10-18-improvement-backlog.md:325-326`,
  "R5. A FREE-SCREEN precondition"). It is NOT the step-5 grader checks named `R5.<NAME>`.

---------------------------------------------------------------------------------------------------------------------------

## 0. The answer in 12 points (the caveat is in the headline)

1. **ROXANNE: R5's premise is TRUE in the game.** `setflag FLAG_BADGE01_GET` (`data/maps/RustboroCity_Gym/scripts.inc:19`)
   runs while a text box is drawn. The TM39 "Obtained" message starts **in the same frame**. Then come **3 more messages
   and 5 more A/B presses**, and only after them `release` (:33) and `end` (:34). (VERIFIED-decomp; the frame grouping is
   DERIVED.)
2. **The chapter 1 end does NOT end mid-box in the game.** `ch1_pokedex` needs three flags:
   - Two of them flip mid-scene (`LittlerootTown_ProfessorBirchsLab/scripts.inc:537`, `:539`).
   - The third, `FLAG_ADVENTURE_STARTED` (`:510`), is followed only by non-waiting commands, then `releaseall` (:514) and
     `end` (:515).
   - So the milestone turns true in the frame the scene shuts down. (DERIVED from `src/script.c:71-125` and the
     `scrcmd.c` return values.)
3. **The chapter 2 end is the same.** `ch2_wally` (`VAR_PETALBURG_GYM_STATE >= 2`) is set at
   `data/maps/PetalburgCity_Gym/scripts.inc:90`. Only `releaseall` (:91) and `end` (:92) follow it.
4. **Other badge-1 milestones DO flip mid-scene:**
   - `ch2_dad`: `FLAG_HIDE_PETALBURG_CITY_WALLYS_MOM` at `PetalburgCity_Gym/scripts.inc:181`. A warp, the whole tutorial,
     a battle, a second warp, 6 messages and 21 presses still follow.
   - `ch1_birch`: `Route101/scripts.inc:218`, at the START of the bag scene.
   - `ch1_starter`: `Route101/scripts.inc:230`, before a warp.
   - `ch1_clock`: `data/scripts/players_house.inc:58`, before MOM's line.
   - `ch4_roxanne`. See the §3 table.
5. **What "free" is in the engine:** `callback2 == CB2_Overworld` and `sLockFieldControls == FALSE`.
   - A running script holds the lock from setup to shutdown (`src/script.c:228`, `:245`; it is released at `:233`).
   - **No script command releases it.** `src/scrcmd.c` contains no `UnlockPlayerFieldControls` call.
6. **`sFieldMessageBoxMode == 0` does NOT mean "no box".**
   - The mode returns to HIDDEN when the TEXT FINISHES PRINTING (`src/field_message_box.c:40-44`).
   - The frame stays drawn until `HideFieldMessageBox` runs (:131-136), which `closemessage`, `release` and `releaseall`
     call.
   - `end` alone never clears the box (`src/scrcmd.c:105-109`).
7. **One free read is not "settled".**
   - After a warp, the exit task releases the controls at the end of a frame (`src/field_screen_effect.c:414-419`).
   - On the very next frame, the input pass checks two things before anything else: a trainer who sees the player
     (`src/field_control_avatar.c:147`) and the map's ON_FRAME scripts (:150).
   - So, DERIVED: one inter-frame read can look free right before an arrival scene (WALLY's tutorial; the gym return
     scene). UNVERIFIED-live.
8. **The RAM addresses are already known and read.** The bot's Emerald symbol table
   (`sandbox-pokebot/modules/data/symbols/pokeemerald.sym`) holds:

   | symbol | address | sym line |
   |---|---|---|
   | `sGlobalScriptContextStatus` | `03000e38` | :782 |
   | `sLockFieldControls` | `03000f2c` | :785 |
   | `sFieldMessageBoxMode` | `020375bc` | :252 |
   | `sTextPrinters` | `020201b0` | :10 |

   The AI player already reads the first three (`ai_player/host/eyes.py:435`, `:453-454`). It requires them together in
   `player_free` (`ai_player/hands/dialogue.py:131-137`).
9. **A person cannot save during a script.**
   - START is read only while the controls are unlocked (`src/overworld.c:1445`; `src/field_control_avatar.c:182-186`).
   - Scripted saves (`special SaveGame`) exist only at facility lobbies, the contest lobby, the cable club, the berry
     blender, post-Champion secret-base battles, the Mystery Events house and Trainer Hill. None is on the badge-1 path.
10. **The save prompts.**
    - First: "Would you like to save the game?" (YES is preselected).
    - Then, depending on the cartridge state at boot:
      - straight to "SAVING…",
      - or "There is already a saved file. Is it okay to overwrite it?" (YES preselected),
      - or **"WARNING! There is a different game file…" with NO preselected**. This one appears on the first save of a
        NEW GAME started over an existing save.
    - Last: "{PLAYER} saved the game."
    - Details in §5.
11. **A milestone that is reached but not saved dies with a kill.**
    - `setflag` writes RAM save block 1 at once (`src/scrcmd.c:582-586` → `src/event_data.c:196-212`).
    - The cartridge copy changes only when `TrySavingData` runs (`src/start_menu.c:1086-1110`).
12. **Perception hazards for an AI save skill.** The decomp side is VERIFIED-decomp. The AI side is VERIFIED-code only and
    UNVERIFIED-live.
    - Once the START menu is drawn, its task is `Task_ShowStartMenu`, not `StartMenuTask` (`src/start_menu.c:527-531`).
      The AI's cursor reader keys on `StartMenuTask` only (`ai_player/host/eyes.py:502`).
    - The save's YES/NO creates no `Task_HandleYesNoInput` (`src/menu.c:1623-1645`; compare `src/script_menu.c:198-212`).
    - The START cursor index is remembered between openings (`src/start_menu.c:83`, `:511`). It can point at a different
      item once POKéDEX or POKéNAV is added (`:315-338`).

---------------------------------------------------------------------------------------------------------------------------

## 1. ROXANNE's victory script (ch4_roxanne), command by command

### 1.1 How the script gets back from the battle (VERIFIED-decomp)

- **The battle call.** `trainerbattle_single TRAINER_ROXANNE_1, …RoxanneIntro, …RoxanneDefeat,
  RustboroCity_Gym_EventScript_RoxanneDefeated, NO_MUSIC` (`RustboroCity_Gym/scripts.inc:5`). `NO_MUSIC = FALSE`
  (`asm/macros/event.inc:784`). With an event script and that value, the macro emits
  `TRAINER_BATTLE_CONTINUE_SCRIPT_NO_MUSIC` (`asm/macros/event.inc:788-797`).
- **Where the defeat script is stored.** `sContinueScriptBattleParams` (`src/battle_setup.c:175-186`) puts that 6th
  argument into `sTrainerABattleScriptRetAddr` (:184, "{&sTrainerABattleScriptRetAddr, TRAINER_PARAM_LOAD_VAL_32BIT}").
  The case is at `:1128-1131`.
- **During the battle.** `dotrainerbattle` (`src/scrcmd.c:1828-1832`) runs `BattleSetup_StartTrainerBattle`, which ends with
  `ScriptContext_Stop();` (`src/battle_setup.c:1324`). The script WAITS through the battle.
- **On a win.** `CB2_EndTrainerBattle` sets `CB2_ReturnToFieldContinueScriptPlayMapMusic` and runs
  `SetBattledTrainersFlags()` (`src/battle_setup.c:1340-1346`).
  - `FieldCB_ContinueScriptHandleMusic` locks the controls and fades in (`src/field_screen_effect.c:142-148`).
  - After the fade, `ScriptContext_Enable()` runs (`:133-140`).
  - `EventScript_EndTrainerBattle` then runs `gotobeatenscript` (`data/scripts/trainer_battle.inc:115-116`). That returns
    `sTrainerABattleScriptRetAddr` (`src/battle_setup.c:1424-1428`), which is `RoxanneDefeated`.
- **Her defeat text.** "So… I lost…" (`:187-197`) is the battle's lose text, loaded as `sTrainerADefeatSpeech`
  (`src/battle_setup.c:181`). It is shown inside the battle. (The battle-side display was not read: UNVERIFIED-detail.)

### 1.2 The post-battle script in order

`MSGBOX_DEFAULT` is `message NULL / waitmessage / waitbuttonpress / return` (`data/scripts/std_msgbox.inc:18-22`). It has
**no `closemessage`**, so its box stays drawn until something closes it. The macro is `loadword 0, \text` plus
`callstd \type` (`asm/macros/event.inc:1938-1941`), with `MSGBOX_DEFAULT = 4` (:1928).

**How presses are counted in this note.** Each `\p` and each `\l` inside a message waits for A or B:
- `\l` is "scroll up window text" (`charmap.txt:1087`); `#define CHAR_PROMPT_SCROLL 0xFA // waits for button press and
  scrolls dialog` (`include/constants/characters.h:175`).
- `\p` is "new paragraph" (`charmap.txt:1088`); `CHAR_PROMPT_CLEAR 0xFB` (:176).
- Both wait in `TextPrinterWaitWithDownArrow`, which checks `JOY_NEW(A_BUTTON | B_BUTTON)` unless autoscroll is on
  (`src/text.c:865-882`, via `:1102-1109`).
- `MSGBOX_DEFAULT` adds one more `waitbuttonpress` at the end.

So a message's presses = its `\p` count + its `\l` count + 1.

| # | where | command | what a person sees | waits for |
|---|---|---|---|---|
| 1 | `RustboroCity_Gym/scripts.inc:14` | `message RustboroCity_Gym_Text_ReceivedStoneBadge` | "{PLAYER} received the STONE BADGE / from ROXANNE." (:199-201) | — |
| 2 | :15 | `waitmessage` | | the text to print |
| 3 | :16 | `call Common_EventScript_PlayGymBadgeFanfare` = `playfanfare MUS_OBTAIN_BADGE` / `waitfanfare` (`data/event_scripts.s:718-721`) | the badge jingle | the fanfare (no press) |
| 4 | :17 | `msgbox …StoneBadgeInfoTakeThis, MSGBOX_DEFAULT` | "The STONE BADGE heightens the ATTACK…" / "…CUT outside of battle." / "Please take this with you, too." (3 pages, :203-208) | 3 presses |
| 5 | :18 | `setflag FLAG_DEFEATED_RUSTBORO_GYM` | (the row-4 box is still drawn) | — |
| 6 | **:19** | **`setflag FLAG_BADGE01_GET`** | (still drawn) | — |
| 7 | :20 | `setvar VAR_RUSTBORO_CITY_STATE, 1` | | — |
| 8 | :21 | `addvar VAR_PETALBURG_GYM_STATE, 1` | | — |
| 9 | :22-23 | `setvar VAR_0x8008, 1` / `call Common_EventScript_SetGymTrainers` → `settrainerflag TRAINER_JOSH / TOMMY / MARC` (`data/scripts/set_gym_trainers.inc:1-17`) | | — |
| 10 | :24 | `call_if_eq VAR_PETALBURG_GYM_STATE, 6, …ReadyPetalburgGymForBattle` (not taken at badge 1) | | — |
| 11 | :25 → :29 | `giveitem ITEM_TM_ROCK_TOMB` → `Std_ObtainItem` (`data/scripts/obtain_item.inc:4-8`): `additem`; the pocket is TM/HM, so `playfanfare MUS_OBTAIN_TMHM` (:42-45, :67-69); `message gText_ObtainedTheItem` (:52-53) | "Obtained the TM39!" (`data/text/obtain_item.inc:1-2`, "Obtained the {STR_VAR_2}!") | — |
| 12 | `obtain_item.inc:54` | `waitfanfare` | | the fanfare (no press) |
| 13 | `obtain_item.inc:55` | `msgbox gText_PutItemInPocket, MSGBOX_DEFAULT` | "{PLAYER} put away the TM39 / in the TMs & HMs POCKET." (`data/text/obtain_item.inc:7-9`; "TMs & HMs" is `src/strings.c:704`) | 1 press |
| 14 | :30 | `goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull` (not taken) | | — |
| 15 | :31 | `setflag FLAG_RECEIVED_TM_ROCK_TOMB` | | — |
| 16 | :32 | `msgbox RustboroCity_Gym_Text_ExplainRockTomb, MSGBOX_DEFAULT` | "That TECHNICAL MACHINE, TM39, / contains ROCK TOMB." … "so think before you use it." (4 pages, :210-218) | 4 presses |
| 17 | :33 | `release` → `HideFieldMessageBox()` (`src/scrcmd.c:1252-1264`) | the box is cleared | — |
| 18 | :34 | `end` → `StopScript` (`src/scrcmd.c:105-109`). The run loop then sets `CONTEXT_SHUTDOWN` and calls `UnlockPlayerFieldControls()` (`src/script.c:230-234`) | free | — |

- **TM39 is Rock Tomb.** `[ITEM_TM_ROCK_TOMB] = { .name = _("TM39"), .itemId = ITEM_TM39, …` (`src/data/items.h:3934-3937`).
- **Frame grouping (DERIVED).**
  - When a native wait succeeds, the script switches back to bytecode and returns at once (`src/script.c:83-87`): "if
    (ctx->nativePtr() == TRUE) ctx->mode = SCRIPT_MODE_BYTECODE; return TRUE;".
  - On the next frame, bytecode runs until a command returns TRUE (`:91-121`).
  - These all return FALSE (they do not wait): `setflag` (`scrcmd.c:582-586`), `message` (:1266-1274), `playfanfare`
    (:924-928), `additem` (:488-495), `callstd` (:246-254), plus `call`, `goto` and `setvar`.
  - ⇒ Rows 5-11 run **in one frame**: the frame after the A press that ends row 4. So `FLAG_BADGE01_GET` and the start of
    "Obtained the TM39!" happen in the same frame.
  - Rows 17-18 run in one frame after the last press.
- **Answer to the question.** Yes, a text box is open when `FLAG_BADGE01_GET` is set.
  - The frame drawn at row 4 is never closed before row 17. Each new `message` redraws into the same window 0
    (`src/field_message_box.c:25-46`, `:62-69`).
  - After the flag come **3 messages and 5 presses** (1 + 4), then `release` / `end`.
  - From the return to the field, the whole script takes 8 presses.
- **The backlog's citation still matches the code.** `ai_player/mode.py:457-458` reads `if milestone is None or index >
  target:` / `return self._play_end(hands, story, manager, runner, report, "done", f"{options.target} reached")`
  (VERIFIED-code). The recon note cites the same two lines as `mode.py:437-438` (`2026-10-15-ch34-recon/00-RECON-NOTE.md:378`).
  That is line drift.
- **Context, not re-checked here.** `2026-10-15-ch34-recon/08-verify-gaps.md:24` and §4 (`:140-150`) ruled Gap 4 "NOT REAL
  for chapter 4". Their reason: the badge is set inside a `talk` goal that plays to `nav_free` before the loop checks the
  target. That is a CODE claim. The game fact above is what makes it matter whenever any path reads the marks while this
  scene runs.
- **What this script sets up for after the milestone.**
  - `VAR_RUSTBORO_CITY_STATE = 1` arms the stolen-goods coord triggers at RUSTBORO (23, 20..24)
    (`data/maps/RustboroCity/map.json:342-378`; `RustboroCity/scripts.inc:231`).
  - They fire on a STEP, not on arrival. Rustboro's ON_FRAME table needs state 6 (`RustboroCity/scripts.inc:27-29`), and
    the gym has no ON_FRAME table.
  - The optional `ch4_gym_trainers` proof (TRAINER_JOSH, TRAINER_TOMMY) is also set by this script (row 9).

---------------------------------------------------------------------------------------------------------------------------

## 2. The AI's chapter ends: the marks it checks, and the script lines that set them

### 2.1 How the AI decides "done" (VERIFIED-code)

- **Where the proofs live.** `ai_player/knowledge/milestones.json`:
  - `ch1_pokedex` at :721-730: flags `RECEIVED_POKEDEX_FROM_BIRCH` 2276, `SYS_POKEDEX_GET` 2145, `ADVENTURE_STARTED` 116.
  - `ch2_dad` at :932.
  - `ch2_wally` at :982-992: variable `PETALBURG_GYM_STATE` number 16517, `at_least` 2.
  - `ch4_roxanne` at :1245-1252: `DEFEATED_RUSTBORO_GYM` 1264, `BADGE01_GET` 2151.
- **How they are read.** The same numbers are in `ai_player/eyes/view.py:380-390` (`MILESTONE_FLAGS`, `MILESTONE_VARS`),
  read from save block 1: flags at +0x1270, vars at +0x139C (`view.py:391-395`).
- **The decision chain.**
  - A milestone is done only when ALL its proofs hold (`ai_player/knowledge/story.py:82-88`).
  - The current milestone is the first non-optional one not done (`ai_player/brain/goals.py:927-942`).
  - The run ends "done" when that index passes the target (`mode.py:457-458`).
  - The default target is `ch1_pokedex` (`ai_player/options.py:220`, `DEFAULT_TARGET = "ch1_pokedex"`; env
    `AI_PLAYER_TARGET`, :219).
- **The decomp ids match** (VERIFIED-decomp):

  | constant | value | where |
  |---|---|---|
  | `FLAG_ADVENTURE_STARTED` | 0x74, "// RECEIVED Pokédex." | `include/constants/flags.h:136` |
  | `FLAG_SYS_POKEDEX_GET` | `SYSTEM_FLAGS + 0x1` = 0x861 (`SYSTEM_FLAGS` is 0x860) | `flags.h:1348-1351` |
  | `FLAG_RECEIVED_POKEDEX_FROM_BIRCH` | `SYSTEM_FLAGS + 0x84` = 0x8E4 | `flags.h:1507` |
  | `FLAG_HIDE_PETALBURG_CITY_WALLYS_MOM` | 0x2D8 | `flags.h:777` |
  | `FLAG_DEFEATED_RUSTBORO_GYM` | 0x4F0 | `flags.h:1319` |
  | `FLAG_BADGE01_GET` | `SYSTEM_FLAGS + 0x7` | `flags.h:1359` |
  | `VAR_PETALBURG_GYM_STATE` | 0x4085, "// 0-1: Wally tutorial, 2-6: 0-4 badges, 7: Defeated Norman, 8: Rematch Norman" | `include/constants/vars.h:153` |

- **Each of the four flags has exactly ONE setter.** A grep for `setflag FLAG_ADVENTURE_STARTED`,
  `…SYS_POKEDEX_GET`, `…RECEIVED_POKEDEX_FROM_BIRCH` and `…BADGE01_GET` over `data/` and `src/` gives 4 hits: the lines
  cited in §1 and §2.2.

### 2.2 The chapter 1 end: the POKéDEX (`data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc`)

**The trigger.** The ON_FRAME entry `map_script_2 VAR_BIRCH_LAB_STATE, 4, …GivePokedexEvent` (:100) starts the scene on its
own, on the first free frame inside the lab with state 4. State 4 is set by `Route103/scripts.inc:131` when the rival
leaves.

| where | command | what a person sees | presses |
|---|---|---|---|
| :145-147 | `lockall`; the player walks up 7 tiles (:150-158) | | |
| :500 | `msgbox …HeardYouBeatRivalTakePokedex` | "PROF. BIRCH: Oh, hi, {PLAYER}{KUN}!" … "this POKéDEX." (5 pages, 4 `\p` + 1 `\l`, :721-731) | 6 |
| :501 → :534-536 | `call …ReceivePokedex`: `playfanfare MUS_OBTAIN_ITEM`; `message …ReceivedPokedex`; `waitfanfare` | "{PLAYER} received the POKéDEX!" (:733-734) | 0 |
| **:537** | **`setflag FLAG_SYS_POKEDEX_GET`** | | |
| :538 | `special SetUnlockedPokedexFlags` | | |
| **:539** | **`setflag FLAG_RECEIVED_POKEDEX_FROM_BIRCH`** | | |
| :540-541 | `setvar VAR_CABLE_CLUB_TUTORIAL_STATE, 1`; `return` | | |
| :502 | `msgbox …ExplainPokedex` | "PROF. BIRCH: The POKéDEX is a high-tech…" (3 pages, 2 `\p` + 3 `\l`, :736-745) | 6 |
| :503 | `closemessage` | the box closes | |
| :504-505 | the rival walks over; the player turns | | |
| :506-508 → :517-523 or :525-531 | the rival's lines (by gender): msgbox "…You got a POKéDEX, too!" (2 pages, :753-757 / :774-778); `giveitem ITEM_POKE_BALL, 5`; msgbox "…catch them with POKé BALLS!" (3 pages, :759-765 / :780-786) | the give shows "Obtained the POKé BALLS!" (0 presses), then "…put away the POKé BALLS / in the POKé BALLS POCKET." (1 press) | 2 + 1 + 3 |
| :509 | `setvar VAR_BIRCH_LAB_STATE, 5` | | |
| **:510** | **`setflag FLAG_ADVENTURE_STARTED`**: the LAST proof mark | | |
| :511-513 | `setvar VAR_OLDALE_TOWN_STATE, 1` / `VAR_LITTLEROOT_RIVAL_STATE, 4` / `VAR_LITTLEROOT_TOWN_STATE, 3` | | |
| :514-515 | `releaseall`; `end` | free | |

- **The first two flags flip mid-scene.** `SYS_POKEDEX_GET` and `RECEIVED_POKEDEX_FROM_BIRCH` flip as the fanfare of
  "received the POKéDEX!" ends. Birch's explanation begins in the same frame. **5 messages and 12 presses** follow
  (6 + 2 + 0 + 1 + 3).
- **The third flag flips with the scene's end.** `ADVENTURE_STARTED` flips after the last press. Nothing after it waits:
  `releaseall` returns FALSE (`src/scrcmd.c:1240-1250`). So the box closes and the script shuts down in the same frame.
  ⇒ DERIVED: **the `ch1_pokedex` milestone (all three flags) can never read true while this scene's box is up.**
- **No follow-on scene in the lab.** The ON_FRAME table has no entry for state 5 (:98-103).
- **The next scene on the way out is a step trigger.** `VAR_LITTLEROOT_TOWN_STATE = 3` arms MOM's RUNNING SHOES coord
  triggers in LITTLEROOT at (8..11, 9) and (10..11, 2) (`data/maps/LittlerootTown/map.json:190`, `:226`; script
  `LittlerootTown/scripts.inc:418`; the shoes are `setflag FLAG_SYS_B_DASH` at :836).
  - A STEP onto those tiles starts the scene; arriving in town does not. Littleroot's ON_FRAME entries need
    `VAR_LITTLEROOT_INTRO_STATE` 1 or 2, or the dex upgrade (`LittlerootTown/scripts.inc:104-108`).
- **Note for the code angle.** `SYS_POKEDEX_GET` and `RECEIVED_POKEDEX_FROM_BIRCH` are also in the AI's novelty
  `STORY_FLAGS` (`view.py:362-364`). Any consumer of those two alone sees them flip mid-scene.

### 2.3 The chapter 2 end: WALLY's tutorial (three scripts, two warps)

**(a) Talking to DAD.** `PetalburgCity_Gym/scripts.inc`, `Norman` :101-119 → `BeginWallyTutorial` :141-191.
- `msgbox …DadYoureHereWithYourPokemon` (:112), then `closemessage` (:113).
- WALLY arrives, with msgboxes at :148-151, :156 and :161-163.
- :172 is WALLY's "{PLAYER}… Would you really come / with me?" (:1173-1175). It is `MSGBOX_DEFAULT`, **not** a
  yes/no. Then `closemessage` (:173).
- They walk out of the gym. :180 `removeobject` WALLY.
- **:181 `setflag FLAG_HIDE_PETALBURG_CITY_WALLYS_MOM`**: `ch2_dad`'s proof, set MID-CUTSCENE.
- :182 `setvar VAR_PETALBURG_GYM_STATE, 1`; :183 `setvar VAR_PETALBURG_CITY_STATE, 2`.
- :188 `warp MAP_PETALBURG_CITY, 15, 8`; :189 `waitstate`.
- Lines :190-191 (`release` / `end`) never run. The map load re-initialises the script context: `CB2_LoadMap` calls
  `ScriptContext_Init();` (`src/overworld.c:1572-1576`).

**(b) The catch.** Petalburg City's ON_FRAME `map_script_2 VAR_PETALBURG_CITY_STATE, 2, PetalburgCity_EventScript_WallyTutorial`
(`data/maps/PetalburgCity/scripts.inc:28`, script :32-55).
- `lockall`; `special SavePlayerParty`; `special LoadWallyZigzagoon`.
- WALLY and the player walk. The player's path is 8 down, 20 right, 2 up (:145-178).
- msgbox `Route102_Text_WatchMeCatchPokemon` (3 pages, 2 `\p` + 1 `\l` = 4 presses, `Route102/scripts.inc:76-82`).
- `special StartWallyTutorialBattle`. The special is marked `waitstate=1` (`data/specials.inc:176`). The battle is RALTS
  L5 with `BATTLE_TYPE_WALLY_TUTORIAL` (`src/battle_setup.c:480-487`).
- msgbox `WallyIDidIt` (:84-86); `applymovement LOCALID_PETALBURG_WALLY, …, MAP_PETALBURG_CITY` (:42-43).
- msgbox `LetsGoBack` (:88-90), then `closemessage`.
- :47 `setvar VAR_PETALBURG_CITY_STATE, 3`; :50 `special LoadPlayerParty`; :51 `setvar VAR_PETALBURG_GYM_STATE, 1`.
- :52 `warp MAP_PETALBURG_CITY_GYM, 4, 108`.

**Where the catch happens.**
- The script belongs to PETALBURG CITY, and its texts are named `Route102_Text_*`.
- Petalburg's layout is 30 tiles wide (`data/layouts/layouts.json:5-8`).
- From x=15, twenty steps east cross x=30, where the "right" connection to `MAP_ROUTE102` (offset 10) begins
  (`data/maps/PetalburgCity/map.json:22-24`).
- Crossing an edge runs `CameraMove` → `LoadMapFromCameraTransition` (`src/fieldmap.c:603-631`; `src/overworld.c:784-829`).
  That path calls no `ScriptContext_Init`, so the scene keeps running. It sets `pos.y -= connection->offset` for an east
  connection (`src/fieldmap.c:584-587`).
- ⇒ DERIVED: the catch happens on ROUTE 102's ground, and save block 1's map should read ROUTE102 during it, at about
  (5, 4) or (5, 5). **UNVERIFIED-live.** Whether the warp-exit task first steps the player out of a door shifts this by
  one tile.

**(c) Back in the gym.** ON_FRAME `map_script_2 VAR_PETALBURG_GYM_STATE, 1, …ReturnFromWallyTutorial` (:72-74, script :76-92).
- `lockall`.
- msgbox `DadSoDidItWorkOut` (1 page, :1177-1178); msgbox `WallyThankYouBye` (6 pages, :1180-1191); `closemessage`.
- WALLY walks out. :86 `setflag FLAG_HIDE_PETALBURG_CITY_WALLY`.
- :89 msgbox `DadGoCollectBadges` (8 pages, :1193-1209: "Head for RUSTBORO CITY beyond this / town.", "the GYM LEADER,
  ROXANNE.").
- **:90 `setvar VAR_PETALBURG_GYM_STATE, 2`**: `ch2_wally`'s proof and the LAST mark.
- :91 `releaseall`; :92 `end`.

**What this means.**
- `ch2_wally` reads true in the frame its scene shuts down, as in §2.2.
- `ch2_dad` reads true **before** 6 messages and 21 presses (4 + 1 + 1 + 1 + 6 + 8), one battle and two warps. The
  tutorial battle's own presses are not counted.
- Nothing starts on its own afterwards. The gym's ON_FRAME table needs state 1 (:72-74); Petalburg's needs CITY_STATE 2 or
  4 (`PetalburgCity/scripts.inc:27-30`).
- The next interruption heading west is SCOTT: coord triggers at PETALBURG (4, 10..13) while
  `VAR_SCOTT_PETALBURG_ENCOUNTER == 0` (`PetalburgCity/map.json:239-266`; `scripts.inc:486`). It is a step trigger.

---------------------------------------------------------------------------------------------------------------------------

## 3. Sweep: every badge-1 milestone proof, and what still runs after it is set (VERIFIED-decomp; "same frame" is DERIVED)

| milestone | proof (milestones.json) | setter | what follows before the scene ends | box up when it flips? |
|---|---|---|---|---|
| ch1_intro | `LITTLEROOT_INTRO_STATE >= 1` | `InsideOfTruck/scripts.inc:26` (boy, value 1) / `:39` (girl, value 2). A coord event | setflags, `setdynamicwarp`, `releaseall`, `end` (:27-35) | no |
| ch1_truck | `VISITED_LITTLEROOT_TOWN` | `LittlerootTown/scripts.inc:38` (ON_TRANSITION, during the map load) | Littleroot's ON_FRAME `StepOffTruck` (:104-106) then starts on the first free frame | no script yet; **a scene is about to start** |
| ch1_mom | `INTRO_STATE >= 4` | `data/scripts/players_house.inc:12` (after `closemessage` :11) | the player walks in; `waitmovement`; `releaseall` (:13-17) | no box; movement still running |
| ch1_clock | `SET_WALL_CLOCK` | `players_house.inc:58` | MOM comes upstairs: msgbox "How do you like your room" (:74), `closemessage`, MOM leaves, `releaseall` (:62-66) | **YES, 1 message follows** |
| ch1_rival_house | `LITTLEROOT_RIVAL_STATE >= 3` | `MaysHouse_2F/scripts.inc:68` / `BrendansHouse_2F/scripts.inc:69` (also the 1F paths `MaysHouse_1F:194` / `BrendansHouse_1F:161`) | setflags, `savebgm`, `fadedefaultbgm` (both return FALSE: `scrcmd.c:952-962`), `releaseall`, `end` | no (same frame) |
| ch1_birch | `RESCUED_BIRCH` | `Route101/scripts.inc:218` (with `SYS_POKEMON_GET` at :217) | it is the START of the bag script: fade, `special ChooseStarter` (:223), the battle, "You saved me" (:225), …, a warp to the lab (:236) | **YES: a whole scene follows** |
| ch1_starter | `SYS_POKEMON_GET` + `BIRCH_LAB_STATE >= 2` | `Route101:217` + `:230` | setvars, the warp (:236); then the lab's ON_FRAME state-2 `GiveStarterEvent` (`Lab:99`) | no box; **a warp and a scene follow** |
| ch1_lab | `BIRCH_LAB_STATE >= 3` | `Lab:134` (after YES at :126-127) | `releaseall`, `end` (:135-136) | no (same frame) |
| ch1_rival_route103 | `DEFEATED_RIVAL_ROUTE103` | `Route103/scripts.inc:133` | setvar, clearflag, `savebgm`, `fadedefaultbgm`, `releaseall`, `end` (:134-139) | no (same frame) |
| ch1_pokedex | 3 flags | `Lab:537`, `:539`, `:510` | §2.2 | the last mark: no |
| ch2_oldale | `VISITED_OLDALE_TOWN` | `OldaleTown/scripts.inc:7` (ON_TRANSITION) | — | n/a |
| ch2_route102 / ch2_petalburg | `VISITED_PETALBURG_CITY` | `PetalburgCity/scripts.inc:7` (ON_TRANSITION) | on the first visit, the step triggers `ShowGymToPlayer` at (8, 10..13) while CITY_STATE is 0 (`PetalburgCity/map.json:203-230`) | n/a |
| ch2_dad | `HIDE_PETALBURG_CITY_WALLYS_MOM` | `PetalburgCity_Gym:181` | §2.3 (a)-(c) | **YES: mid-cutscene, a warp pending** |
| ch2_wally | `PETALBURG_GYM_STATE >= 2` | `PetalburgCity_Gym:90` | `releaseall`, `end` | no (same frame) |
| ch3_route104 / ch3_woods | `PETALBURG_WOODS_STATE >= 1` | `PetalburgWoods/scripts.inc:92` | `releaseall`, `end` (:93-94) | no (same frame) |
| ch3_rustboro | `VISITED_RUSTBORO_CITY` | `RustboroCity/scripts.inc:7` (ON_TRANSITION) | — | n/a |
| ch4_gym_trainers (optional) | TRAINER_JOSH / TOMMY | a battle's end (`battle_setup.c:1344-1346`), or ROXANNE's `SetGymTrainers` (`set_gym_trainers.inc:13-17`) | on the ROXANNE path: §1 rows 10-18 | on the ROXANNE path: yes |
| ch4_roxanne | `DEFEATED_RUSTBORO_GYM` + `BADGE01_GET` | `RustboroCity_Gym:18-19` | §1 rows 7-18 | **YES: 3 messages** |

- **The pattern.** Vanilla scripts usually advance their state var or flag as the last command before `releaseall`/`end`.
- **The exceptions on the badge-1 path:** ch1_birch, ch1_starter, ch1_clock, ch2_dad and ch4_roxanne.
- **The `VISITED_*` flags** are set during a map load. On a camera crossing, `RunOnTransitionMapScript` runs at
  `src/overworld.c:807`. These scripts run in the separate immediate context (`src/script.c:265-270`), sometimes just
  before an arrival scene starts.

---------------------------------------------------------------------------------------------------------------------------

## 4. What a "free screen" is in the engine

### 4.1 The three state bytes (VERIFIED-decomp)

**`sGlobalScriptContextStatus`** (`src/script.c:17-21`, `:25`). It has three values:

- `CONTEXT_RUNNING` 0: a script runs, or waits in a native function. This covers `waitmessage`, `waitbuttonpress`,
  `waitmovement`, `delay`, `lock` and `lockall`; they call `SetupNativeScript` and return TRUE (`src/scrcmd.c:1311-1315`,
  `:1332-1336`, `:1202-1238`).
- `CONTEXT_WAITING` 1: after `waitstate` / `ScriptContext_Stop` (`scrcmd.c:143-147`; `script.c:250-253`). This covers
  battles (`battle_setup.c:1324`), warps, and specials marked `waitstate=1`.
- `CONTEXT_SHUTDOWN` 2: no script. After `end`, the run loop shuts the context down (`script.c:230-234`).
  `ScriptContext_Init` also sets it, on a new game, a whiteout, a map load and a continue (`src/overworld.c:1540`, `1561`,
  `1575`, `1736`).

**`sLockFieldControls`** (`script.c:28`, `:182-195`; `ArePlayerFieldControlsLocked` returns it).

- **Set by:**
  - `ScriptContext_RunScript`, on every frame it runs (`:228`);
  - `ScriptContext_SetupScript` (`:245`) and `ScriptContext_Enable` (`:259`);
  - `ShowStartMenu` (`src/start_menu.c:590`) and `DoWarp` (`src/field_screen_effect.c:486`);
  - the warp-exit callbacks (`:278`) and the post-battle callback (`:144`);
  - any input that started something (`src/overworld.c:1446-1450`).
- **Cleared at:**
  - script shutdown (`script.c:233`);
  - `CB2_LoadMap` (`overworld.c:1576`). The warp exit locks it again at once;
  - the end of the warp-exit tasks (`field_screen_effect.c:360`, `398`, `417`);
  - closing the START menu (`start_menu.c:1421-1427`) and finishing a save (`:828-833`).
- **No script command clears it.** `src/scrcmd.c` has no `UnlockPlayerFieldControls` call. `release` and `releaseall`
  only hide the box and unfreeze objects (`:1240-1264`).

**`sFieldMessageBoxMode`** (`src/field_message_box.c:9`; `include/field_message_box.h:6-9`: HIDDEN 0, UNUSED 1, NORMAL 2,
AUTO_SCROLL 3).

- It is NORMAL from `ShowFieldMessage` (:62-69) until the text printer finishes. Then `Task_DrawFieldMessage` sets it back
  to HIDDEN (:40-44: "if (RunTextPrintersAndIsPrinter0Active() != TRUE) { sFieldMessageBoxMode = FIELD_MESSAGE_BOX_HIDDEN;").
- **The dialogue frame stays on screen** until `HideFieldMessageBox` (:131-136), which `closemessage` (`scrcmd.c:1317-1321`),
  `release` and `releaseall` call.
- `waitmessage` waits for exactly this HIDDEN state (`IsFieldMessageBoxHidden`, :143-148). That is why the function name
  misleads: during the `waitbuttonpress` that ends every `MSGBOX_DEFAULT`, the mode is already 0.

**Text printers.**

- The game runs `sTextPrinters[32]` (`src/text.c:39`). Each has `active` at +0x1B and `state` at +0x1C
  (`include/text.h:94-95`).
- `RENDER_STATE_WAIT` 1, `CLEAR` 2 and `SCROLL_START` 3 (`text.h:36-42`) are the A/B waits inside a message (a `\p` or a
  `\l`).

### 4.2 The engine's own test for "the player can act" (VERIFIED-decomp)

- `CB1_Overworld` runs `DoCB1_Overworld` only when `gMain.callback2 == CB2_Overworld` (`src/overworld.c:1459-1463`).
- `DoCB1_Overworld` reads input only when `!ArePlayerFieldControlsLocked()` (:1445).
- Buttons are read only when the player stands still or is at a tile centre, and is not at top bike speed
  (`src/field_control_avatar.c:95-100`).
- `ProcessPlayerFieldInput` then checks, in order:
  1. a trainer who wants a battle (:147);
  2. the ON_FRAME map scripts (:150);
  3. step scripts, on a step (:159);
  4. A on a person or thing (:172);
  5. START (:182-186: "PlaySE(SE_WIN_OPEN); ShowStartMenu(); return TRUE;").
- Each frame, `callback1` runs before `callback2` (`src/main.c:188-195`). The script runs inside callback2's
  `OverworldBasic` (`overworld.c:1465-1467`).

### 4.3 What follows from it (DERIVED)

- **(a) Lock clear plus status SHUTDOWN means "no scene".** A running script holds the lock for its whole life.
- **(b) Box mode 0 is not "no box"** (§4.1).
- **(c) `end` alone leaves a box drawn** (`scrcmd.c:105-109` only calls `StopScript`). Vanilla scripts close the box with
  `release` / `releaseall` / `closemessage` first, and every badge-1 end script above does. Whether any vanilla script
  ends with a box left drawn on a free screen is UNVERIFIED.
- **(d) One free read is not "settled".**
  - The warp-exit task releases the controls at the END of a frame (`field_screen_effect.c:414-419`).
  - On the very next frame, callback1 checks trainers and ON_FRAME scripts before anything else
    (`field_control_avatar.c:147-151`).
  - Predicted: one inter-frame read looks free right before WALLY's tutorial (after the gym→Petalburg warp) and right
    before the gym's return scene. UNVERIFIED-live.
  - The bot met the same class at door exits: "there is a single frame where the game erroneously reports the player as
    controllable even though it's still in the exiting animation" (`sandbox-pokebot/modules/player.py:279-282`).
  - The AI already waits `SETTLE_FREE = 30` frames after a map change (`ai_player/mode.py:115`, `:475-480`).
- **(e) The map can change in the middle of a scene.** Walking over an edge loads the next map without touching the
  script (`fieldmap.c:603-631`; `overworld.c:784-829`). WALLY's tutorial does exactly this.

### 4.4 Who already reads what

**RAM symbols** (the bot's Emerald table, `sandbox-pokebot/modules/data/symbols/pokeemerald.sym`):

| symbol | address | sym line |
|---|---|---|
| `sTextPrinters` | 020201b0 | :10 |
| `sFieldMessageBoxMode` | 020375bc | :252 |
| `sSaveDialogCallback` | 0203761c | :287 |
| `sSaveDialogTimer` | 02037620 | :288 |
| `sStartMenuWindowId` | 0203cd8c | :640 |
| `sGlobalScriptContextStatus` | 03000e38 | :782 |
| `sGlobalScriptContext` | 03000e40 | :783 |
| `sImmediateScriptContext` | 03000eb8 | :784 |
| `sLockFieldControls` | 03000f2c | :785 |
| `IsFieldMessageBoxHidden` | 0809833c | :5871 |
| `ArePlayerFieldControlsLocked` | 08098e6c | :5916 |

**The AI player** (VERIFIED-code):
- `ai_player/host/eyes.py:435` reads `sFieldMessageBoxMode` into `text_box_open`.
- `:453` reads `sGlobalScriptContextStatus` into `script_running` (true when the status is not 2).
- `:454` reads `sLockFieldControls` into `controls_locked` (:457-460).
- The text printers drive the button-wait readings (`ai_player/eyes/view.py:436-447`).
- `player_free` = OVERWORLD ∧ ¬script_running ∧ ¬controls_locked ∧ no UI ∧ ¬text_box_open ∧ ¬waits_for_button ∧
  ¬settling (`ai_player/hands/dialogue.py:131-137`).
- `nav_free` adds ¬fading and a view (`ai_player/brain/navigator.py:245-247`).
- This conjunction already covers §4.3(b): the status is still RUNNING during the closing `waitbuttonpress`.

**The bot** (teaching material only):
- `get_global_script_context` reads `sGlobalScriptContext` (`sandbox-pokebot/modules/tasks.py:182-188`).
- Its `is_active` is the context's mode byte ≠ STOPPED (`tasks.py:100-102`; `struct ScriptContext`: `stackDepth` @0,
  `mode` @1, per `include/script.h:9-19`).
- `wait_for_no_script_to_run` loops on it (`sandbox-pokebot/modules/modes/util/tasks_scripts.py:150-155`).
- `is_waiting_for_input` checks the native `WaitForAorBPress`, or printer 0 in state 2 or 3 (`tasks.py:197-215`).
- `player_avatar_is_controllable` uses the player object's flags, not the lock (`modules/player.py:263-284`).
- No bot `.py` file reads `sLockFieldControls`.

---------------------------------------------------------------------------------------------------------------------------

## 5. Saving, as a person does it (VERIFIED-decomp unless marked)

### 5.1 When a person can save

- START opens only from `DoCB1_Overworld` with the controls unlocked (`src/overworld.c:1445`;
  `src/field_control_avatar.c:182-186`).
- A running script holds the lock (§4.1). ⇒ **A person cannot open START, and so cannot save, during any scene, text box
  or battle.**
- `ShowStartMenu` freezes the objects and locks the controls itself (`src/start_menu.c:581-591`).
- **The only in-script save** is `Common_EventScript_SaveGame` → `special SaveGame` (`data/scripts/std_msgbox.inc:46-48`;
  `src/start_menu.c:896-900`; `SaveGameTask` at :911-928 calls `ScriptContext_Enable()` when it finishes).
  - It has 34 call sites in `data/`, plus the special's own entry `def_special SaveGame, waitstate=1`
    (`data/specials.inc:112`):
    - the 7 Battle Frontier lobbies and the 3 Battle Tent lobbies;
    - the contest lobby;
    - the cable club (7 sites, e.g. `data/scripts/cable_club.inc:311`);
    - the berry blender (`data/scripts/berry_blender.inc:559`);
    - the secret-base trainer battles (10 sites, `data/scripts/secret_base.inc:307-613`). These are gated on
      `FLAG_SYS_GAME_CLEAR` (`:301`);
    - the Mystery Events house and Trainer Hill.
  - **None is on the badge-1 path.**

### 5.2 The menu

- **The normal START menu** (`src/start_menu.c:315-338`):
  - `POKéDEX` if `FLAG_SYS_POKEDEX_GET`;
  - `POKéMON` if `FLAG_SYS_POKEMON_GET`;
  - `BAG`;
  - `POKéNAV` if `FLAG_SYS_POKENAV_GET`;
  - `PLAYER` (shows the player's name);
  - `SAVE`, `OPTION`, `EXIT`.
  - The `SAVE` label is `gText_MenuSave[] = _("SAVE")` (`src/strings.c:1515`; `[MENU_ACTION_SAVE]` at `start_menu.c:189`).
    The AI mirrors the labels in `ai_player/eyes/screens.py:267`.
- **So SAVE moves:** it is the 3rd item before the starter, the 4th after it, the 5th after the POKéDEX (the ch1 end) and
  the 6th after the POKéNAV.
- **The cursor is remembered by INDEX.**
  - It is kept between openings in EWRAM `sStartMenuCursorPos` (`start_menu.c:83`) and passed back to `InitMenuNormal`
    (`:511`).
  - Nothing resets it when items are added. ⇒ DERIVED: after the POKéDEX appears, the remembered index points one item
    earlier than before.
  - A person reads the highlighted word.
- **Other menu shapes** (link, Union Room, Safari, Pike, Pyramid, multi-partner room) are built at `start_menu.c:276-312`.
  None is on the badge-1 path.

### 5.3 The dialog after A on SAVE

The chain is `StartMenuSaveCallback` (:721-729) → `SaveStartCallback` (:809-815) → `SaveCallback` (:817-838), which runs
`sSaveDialogCallback`.

1. **The confirm question.** `SaveConfirmSaveCallback` (:978-994) removes the START window and shows the save info window.
   - The info window shows the region name, `PLAYER`, `BADGES`, `POKéDEX` (only once `FLAG_SYS_POKEDEX_GET` is set) and
     `TIME` (`:1332`; labels at `src/strings.c:1641-1644`).
   - It prints **"Would you like to save the game?"** (`data/text/save.inc:2-3`).
2. **YES/NO, YES preselected.** `SaveYesNoCallback` (:996-1001) calls `DisplayYesNoMenuDefaultYes` (`src/menu.c:464-467`).
3. **The answer.** `SaveConfirmInputCallback` (:1003-1032).
   - **NO or B** → `SAVE_CANCELED` → back to the START menu (:823-827).
   - **YES** → the next step depends on two values:
     - `gSaveFileStatus` is the cartridge's state **at boot**: `LoadGameSave` sets it (`src/save.c:872-889`), called at
       boot (`src/intro.c:1147-1155`).
     - `gDifferentSaveFile` is FALSE at boot (`src/new_game.c:139-141` via `intro.c:1152`), TRUE after NEW GAME
       (`new_game.c:150-154`), and FALSE again after a save that started with it TRUE (`start_menu.c:1093-1096`).

   | situation | boot state | `gDifferentSaveFile` | what YES leads to |
   |---|---|---|---|
   | first save of a NEW GAME on an empty cartridge | EMPTY or CORRUPT | TRUE | straight to SAVING (:1010-1019) |
   | a later save in the same power-on | EMPTY or CORRUPT | FALSE | **"There is already a saved file. / Is it okay to overwrite it?"** (`save.inc:5-7`), YES preselected (`start_menu.c:1056-1061`) |
   | a CONTINUEd game, or a later save | OK | FALSE | the same "already a saved file" question, YES preselected |
   | first save of a NEW GAME started over an existing save | OK | TRUE | **"WARNING! / There is a different game file that / is already saved." / "If you save now, the other file's / adventure, including items and / POKéMON, will be entirely lost." / "Are you sure you want to save now / and overwrite the other save file?"** (`save.inc:16-24`), with **NO preselected** (`DisplayYesNoMenuWithDefault(1)`: `start_menu.c:1049-1054`; `menu.c:469-472`). **A blind A cancels the save.** |

   `TrySavingData` never updates `gSaveFileStatus` (`src/save.c:766-786`). An empty-at-boot cartridge therefore stays
   "EMPTY" all session, which is why its second save asks "already a saved file". (DERIVED.)
4. **The overwrite answer.** `SaveOverwriteInputCallback` (:1063-1078): YES saves; NO or B → `SAVE_CANCELED`.
5. **Saving.** **"SAVING… / DON'T TURN OFF THE POWER."** (`save.inc:9-11`; :1080-1084).
6. **The write.** `SaveDoSaveCallback` (:1086-1110):
   - it adds one to `GAME_STAT_SAVED_GAME` and runs `TrySavingData(SAVE_NORMAL)`, or `SAVE_OVERWRITE_DIFFERENT_FILE`;
   - it then shows **"{PLAYER} saved the game."** (`save.inc:13-14`) or "Save error. / Please exchange the / backup
     memory." (:26-29);
   - it starts a 60-frame timer (`SaveStartTimer`, :942-945).
7. **The close.** `SaveSuccessCallback` (:1112-1121) plays `SE_SAVE` once the text is done. `SaveReturnSuccessCallback`
   (:1123-1134) waits for that sound and then either 60 frames or **A held** (`SaveSuccesTimer`, :947-962).
8. **Back to free.** On `SAVE_SUCCESS` or `SAVE_ERROR`, the START menu closes completely and the controls are released
   (:828-833). The player is on a free screen again; no B press is needed.

### 5.4 What a save keeps

- A flag set by a script is written at once to RAM save block 1 (`setflag` → `FlagSet` → `&gSaveBlock1Ptr->flags[id / 8]`:
  `src/scrcmd.c:582-586`, `src/event_data.c:196-212`).
- The cartridge copy changes only at step 6.
- The script context is never saved. A CONTINUE starts it SHUTDOWN (`ScriptContext_Init` in `CB2_ContinueSavedGame`,
  `overworld.c:1736`).

### 5.5 Hazards for an AI save skill

The decomp side is VERIFIED-decomp. How the AI sees it is VERIFIED-code only, and **UNVERIFIED-live**.

- **The START menu task changes name once drawn.**
  - `StartMenuTask` runs only `InitStartMenuStep`, then switches to its follow-up (`start_menu.c:527-541`;
    `src/task.c:148-153`). The follow-up `Task_ShowStartMenu` is what runs `HandleStartMenuInput` (`start_menu.c:561-579`).
  - The AI's screen classifier knows both names (`ai_player/eyes/view.py:411-412`; gate `ai_player/gates/test_eyes.py:397`).
  - Its options/cursor reader keys on `"StartMenuTask"` only (`ai_player/host/eyes.py:502-505`; `ai_player/eyes/screens.py:228`).
  - For Emerald, the bot uses `start_menu_task = "Task_ShowStartMenu"` (`higher_level_actions.py:891`).
  - ⇒ The AI may classify an open START menu without reading its options or cursor.
- **The save's YES/NO is not a yes/no task.**
  - It is drawn by `CreateYesNoMenu`, which creates **no** task (`src/menu.c:1623-1645`). Its input is read inside the START
    menu task's callback (`start_menu.c:1005`, `:1065`, `switch (Menu_ProcessInputNoWrapClearOnChoose())`).
  - A script's `yesnobox`, by contrast, creates `Task_HandleYesNoInput` (`src/script_menu.c:198-212`).
  - The AI's `yes_no` kind is keyed on `Task_HandleYesNoInput` (`view.py:413`). ⇒ The save's YES/NO would read as
    "start_menu".
- **The bot's routine** (teaching only): `StartMenuNavigator("SAVE")`, then A until the START menu task ends. The one
  exception is `SaveOverwriteInputCallback`, where it presses Up and then A
  (`sandbox-pokebot/modules/modes/util/higher_level_actions.py:871-907`). Its docstring says "It will confirm everything,
  including when warned that there is already a different save file". That matches the NO default above.

---------------------------------------------------------------------------------------------------------------------------

## 6. What the facts imply for building R5 (inference for the builder; not a design ruling)

- **Where R5's premise holds.** "done mid-box" is real in the game for `ch4_roxanne` and for the mid-scene milestones
  (`ch1_birch`, `ch1_starter`, `ch1_clock`, `ch2_dad`). It is NOT real at the `ch1_pokedex` or `ch2_wally` ends.
  - ⇒ An R5 A/B at the chapter 1 or chapter 2 end would be **VACUOUS**: both arms end free.
  - The arms can differ at the chapter 4 end, or in a fault arm that ends the run on `ch2_dad`. (CLAUDE.md Tier 2(4):
    compute the discriminator.)
- **The game-side test for "free".** All of these must hold: `callback2 == CB2_Overworld` (the framework's OVERWORLD state;
  that mapping is UNVERIFIED here), the lock clear, and the status SHUTDOWN. They must hold for more than one frame with
  no input (§4.3d). The message-box byte alone is not enough.
- **Saving.** A save is possible only on that screen, and the START path cannot interrupt a scene.
  - Saving right after a chapter end, before walking, is clear of the next scenes: at the chapter 1, 2 and 4 ends they are
    step triggers (§1, §2.2, §2.3).
- **The first save of a NEW GAME can default to NO.** That depends on the cartridge's state at boot (§5.3).

---------------------------------------------------------------------------------------------------------------------------

## 7. UNVERIFIED and open

**For a live probe:**
1. The predicted single free inter-frame read before WALLY's tutorial (after the gym→Petalburg warp) and before the gym's
   return scene (§4.3d).
2. Save block 1's map and tile during the tutorial catch: ROUTE102 at about (5, 4) or (5, 5)? (§2.3 b)
3. What the framework's task list shows for an open START menu (`Task_ShowStartMenu`?), and what the AI's eyes report
   then and during the save YES/NO (§5.5).
4. Whether the AI harness boots with an empty flash or a previous `.sav`. This decides which prompt the first save shows,
   including the NO-default WARNING (§5.3).
5. Whether mGBA writes the `.sav` to disk at save time. This is R1's own open question
   (`2026-10-18-improvement-backlog.md:293`, "does mGBA flush the save before a kill?").

**For the user (gameplay):**
6. When should the AI save? After every milestone, at chapter ends, or as a person does (at a POKéMON CENTER, before a
   boss)? The game allows any free overworld moment, so this is a design choice.

**Not re-checked here:**
- The code claims in `08-verify-gaps.md` §4: the talk goal plays out before "done".
- That ROXANNE's lose text is printed inside the battle (only its loading, `battle_setup.c:181`, was read).
