> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1r2recon/01-game.md` (sha256 `7cd68da60d67e4f1`). Backlog R1 + R2's recon (save, CONTINUE, a memory that survives a kill), angle 1, THE GAME (the pinned decomp): a read-only Claude subagent's NOTE, never truth (the authoritative docs and the code win). Nothing in it was measured live. R1 + R2's build waits for the user's two save answers (`04` item 4).
> ⚠ **The adversary's verdict** (`2026-10-29-R1R2-recon-refute.md` section 2): nothing here was found WRONG. Two corrections: the save dialog's shape (a4) follows RAM that a `.ss1` carries (gSaveFileStatus, gDifferentSaveFile), not the cartridge on disk, as section 1.4 says and section 0 does not; and a6's write length is closed at about 133 frames or more (its C1: arithmetic over mGBA 0.10.2's source, not yet measured).
> ⚠ **MEASURED 2026-10-29** (`2026-10-29-R1R2-PROBE-REPORT.md`): a6's write takes 256-261 frames, not "about 133 frames or more" (only the lower bound holds), and a kill inside its first sector leaves no error page.

# R1 + R2 recon, angle 1: THE GAME (save, title, CONTINUE), read from the pinned decomp

A NOTE, never truth (CLAUDE.md: agent output is a note; the authoritative docs win until a claim is verified).
Written 2026-10-29 by a read-only recon agent. Nothing in the repo was edited; nothing was run except reads, greps
and `tools/decomp_lookup.py ask "save game continue"` (it found NO prior ruling on saving; its one hit, the lobby
fixture ruling `06:6125-6153`, is unrelated).

- Decomp: the PINNED clone `C:/Remote Projects/_decomp/pokeemerald` at `731ad5bf` (2026-10-01). Paths without a
  prefix are in that clone. Paths starting `ai_player/`, `sandbox-pokebot/` or `PROJECT KNOWLEDGE/` are in the repo.
- Tags: **[VERIFIED-decomp f:l]** read in the pinned clone; **[VERIFIED-code f:l]** read in the repo; **[DOC f:l]**
  quoted from a project doc; **[UNVERIFIED]** inference (each says what would prove it). Line numbers are 1-based.
- NAME CLASH: "R1"/"R2" here are the BACKLOG items, never the step-5 grader checks `R1.*`/`R5.*` in
  `ai_player/gates/rate_step5.py`.
- Scope (the task): the backlog's R1 + R2 entry [DOC `PROJECT KNOWLEDGE/ai-research-notes/2026-10-18-improvement-backlog.md:290-294`],
  its DP4 fold [DOC same file :378-379], DP1 + DP2 and L3 (a)-(b) [DOC same file :390-397]. The user's two open
  questions [DOC `PROJECT KNOWLEDGE/04-HANDOFF.md:61`: "when the AI saves, and may it reload to undo a loss"] are
  NOT decided here; §6 lists what each answer would change.

---

## 0. The answers in brief

**(a) The START menu's SAVE flow**
- a1. START opens the menu ONLY on the free overworld: `gMain.callback2 == CB2_Overworld`, field controls unlocked,
  the player not mid-step (on a forced-movement tile only when not moving), not at the Mach Bike's top speed, and no
  higher-priority event on that frame (a trainer's sight, an ON_FRAME map script, a step script, a wild encounter,
  a warp, an A interaction, a dive) [VERIFIED-decomp overworld.c:1438-1463; field_control_avatar.c:89-107, 133-187;
  bike.c:1022-1037]. Closing POKéDEX / POKéMON / BAG / POKéNAV / OPTION / the trainer card returns to the field WITH
  the start menu reopened [VERIFIED-decomp overworld.c:1670-1675; field_screen_effect.c:424-444; start_menu.c:709-713,
  739; grep: pokedex.c, party_menu.c, item_menu.c, pokenav.c use CB2_ReturnToFieldWithOpenMenu].
- a2. SAVE is an item of the NORMAL start menu only: `[POKéDEX] [POKéMON] BAG [POKéNAV] <player's name> SAVE OPTION
  EXIT` (bracketed items appear with their flags), so SAVE's position moves during the story; the cursor's INDEX is
  remembered between openings and reset only by a reboot [VERIFIED-decomp start_menu.c:83, 315-337, 511, 598-604;
  main.c:428-438].
- a3. The texts in order: "Would you like to save the game?" YES/NO (cursor on YES) -> one of {nothing | "There is
  already a saved file. / Is it okay to overwrite it?" (cursor on YES) | the 4-page "WARNING! ..." ending "Are you
  sure you want to save now / and overwrite the other save file?" (cursor on NO)} -> "SAVING... / DON'T TURN OFF THE
  POWER." -> "{PLAYER} saved the game." plus the save jingle -> the box closes BY ITSELF (after the jingle ends: 60
  frames, or at once while A is held) and the player is free again with the menu closed
  [VERIFIED-decomp start_menu.c:978-1134, 817-838; data/text/save.inc:1-29].
- a4. Which middle question appears depends on the CARTRIDGE, not on the place: none = the first save after NEW GAME
  on an empty or corrupt cart; "already a saved file" = every save of a CONTINUEd game and every later save of a
  session; WARNING (default NO) = the first save after NEW GAME on a cart that already holds a save
  [VERIFIED-decomp start_menu.c:1003-1061; new_game.c:139-155; save.c:872-891]. A blind A-mash therefore CANCELS the
  WARNING save [VERIFIED-decomp start_menu.c:1049-1054, 1063-1075].
- a5. NO, or B, at either question goes back to the start menu with NOTHING written [VERIFIED-decomp
  start_menu.c:1024-1028, 1070-1074, 823-827].
- a6. The flash write is ONE synchronous call on the first frame after "SAVING..." has finished printing:
  GAME_STAT_SAVED_GAME + 1, then all 14 sectors of the OTHER save slot (each erased, programmed byte by byte and
  verified, up to 3 tries). While it runs the main loop is stopped (no play-time count, no input, no soft-reset check);
  the VBlank interrupt keeps running (and advances the RNG) [VERIFIED-decomp start_menu.c:1086-1110; save.c:139-175,
  708-786; agb_flash.c:260-277; main.c:131-167, 340-366]. How many emulated frames the write takes in mGBA is NOT in
  the decomp [UNVERIFIED: my unchecked recollection of mGBA's flash timing suggests roughly a hundred frames or more;
  §8 P2 measures it].
- a7. A person presses: START; Up/Down until SAVE (read the cursor); A; A (YES); then A (YES) on "already a saved
  file", or Up then A on the WARNING (after A on each of its pages); then nothing. Text prints on its own; A/B only
  speeds it up [VERIFIED-decomp start_menu.c:593-637, 884-894, 902-909; menu.c:198-202, 1013-1041].
- a8. Other saves exist: the scripted save `special SaveGame` (the same dialog run from a script, VAR_RESULT 1 =
  saved) before Battle Tent / Frontier / Trainer Hill challenges, link play and secret-base battles; the Hall of
  Fame saves with NO prompt; the Battle Pyramid's REST saves and then soft-resets [VERIFIED-decomp
  start_menu.c:896-930, 194, 828-834; data/scripts/std_msgbox.inc:46-48; hall_of_fame.c:516-541;
  battle_pyramid.c:1439-1454].

**(b) The title screen and CONTINUE**
- b1. From power-on: the copyright screen (about 140 frames plus a fade, reads no input) -> the intro movie (any NEW
  key ends it, but only while no palette fade runs) -> the title (A/B/START/SELECT skips the logo animation; then a
  NEW A or START goes to the main menu) [VERIFIED-decomp intro.c:116-118, 1042-1058, 1072-1121; title_screen.c:684-828].
- b2. HAZARD at the title: holding B+SELECT+UP opens "Clear all save data areas?" (cursor on NO); B+SELECT+LEFT the
  clock reset (only when FLAG_SYS_RESET_RTC_ENABLE and VAR_RESET_RTC_ENABLE are set); B+SELECT the Berry fix program [VERIFIED-decomp
  title_screen.c:39-41, 788-803; clear_save_data_screen.c:80-107; event_data.c:156-162].
- b3. CONTINUE exists exactly when the save read AT BOOT is OK, or ERROR (one slot usable, the other broken): the menu is
  CONTINUE / NEW GAME / OPTION (MYSTERY GIFT before OPTION if enabled), with CONTINUE highlighted after any reboot
  [VERIFIED-decomp main_menu.c:172, 510-515, 625-692; intro.c:1146-1158].
- b4. The CONTINUE window shows PLAYER <name>, TIME <h:mm>, POKéDEX <caught> (only once the Pokédex is owned) and
  BADGES <n>; it shows NO location (the in-game save window does) [VERIFIED-decomp main_menu.c:2127-2186;
  start_menu.c:1332-1393].
- b5. Error pages can come first, each dismissed with A: "The save file is corrupted. The previous save file will be
  loaded." / "The save file has been erased due to corruption or damage." (then NO CONTINUE) / "The internal battery
  has run dry. ..." [VERIFIED-decomp main_menu.c:649-659, 694-738; strings.c:35-38].
- b6. Presses to reach the overworld: any key (movie), one press to skip the logo, A or START, [A per error page],
  A on CONTINUE; each a NEW press. The map fades in with its name pop-up and the controls stay locked until the
  fade-in ends [VERIFIED-decomp main_menu.c:884-899, 936-1068; overworld.c:1705-1752; field_screen_effect.c:289-296,
  404-420].

**(c) What a save stores and what CONTINUE restores**
- c1. A save is SaveBlock2 (name, gender, trainer ID, play time to the frame, options, Pokédex, the clock offset,
  the last berry update), SaveBlock1 (map and tile, warps, the party whole with PIDs, money, bag, PC items, ALL
  flags and vars incl. temporary ones, game stats, every object event incl. the player's facing, the 15 x 14
  metatiles around the player, weather, roamer, daycare, berry trees, TV, ...) and the PC boxes [VERIFIED-decomp
  include/global.h:508-542, 984-1078; save.c:55-73; load_save.c:160-206; fieldmap.c:391-404].
- c2. A normal CONTINUE puts back the map, the tile, the party (same PIDs), bag, boxes, flags and vars, options, the
  play time (it resumes counting from the saved value) and the people where they stood; the facing comes back
  through the player's saved movementDirection (the same as the facing in ordinary play [UNVERIFIED, §8 P5]) [VERIFIED-decomp
  overworld.c:597-601, 1705-1752; save.c:872-891; event_object_movement.c:1715-1796, 2361-2367;
  field_player_avatar.c:849-854; play_time.c:23-29].
- c3. NOT restored: the screen (always a fresh overworld, no menu); any script (the script engine is reset; the
  map's ON_LOAD, ON_RESUME and ON_RETURN_TO_FIELD scripts run, ON_TRANSITION does not); a battle (none can be
  saved); the RNG (not in the save: vanilla starts it at 0 at power-on and advances it every VBlank); the
  cartridge's hardware clock [VERIFIED-decomp overworld.c:1736, 2150, 2184, 860; fieldmap.c:69-77; main.c:94,
  108-110, 366].
- c4. CONTINUE CHANGES a few things: the roaming Latios/Latias moves, the Safari flag clears, the ambient cry and
  Cycling Road data reset, clock events run for the real time elapsed (daily flags, berries), and loading an OLDER
  slot resets Frontier win streaks [VERIFIED-decomp overworld.c:416-423, 1711-1713, 1725; clock.c:26-74].
- c5. Some saves CONTINUE elsewhere: after the Hall of Fame save the player wakes in their bedroom in Littleroot;
  link and Frontier saves use the "continue-game warp" [VERIFIED-decomp post_battle_event_funcs.c:36-41;
  overworld.c:1739-1745; load_save.c:134-158].
- c6. The save is read from flash ONCE per boot and CONTINUE uses that copy, so continuing the NEWEST save needs a
  reboot (power, or the soft reset A+B+START+SELECT) [VERIFIED-decomp intro.c:1146-1158; main.c:133-142, 428-438].

**(d) Failure modes**
- d1. Two slots (sectors 0-13 and 14-27). Each save writes the OTHER slot with a counter one higher, its 14 sectors
  rotated by one place. At boot a slot is OK only if all 14 sector ids carry a valid signature AND checksum;
  CONTINUE loads the OK slot with the higher counter [VERIFIED-decomp save.c:25-42, 139-209, 515-638].
- d2. Newest slot incomplete -> "The save file is corrupted. The previous save file will be loaded." and CONTINUE
  loads the previous save (Frontier streaks reset); both slots bad -> "The save file has been erased due to
  corruption or damage." and NEW GAME only [VERIFIED-decomp save.c:607-637; main_menu.c:649-659;
  overworld.c:1712-1713].
- d3. A write cut part way leaves the new slot with at least one sector id missing, so the game falls back to the
  previous save instead of mixing two saves [UNVERIFIED: derived from save.c:155-163, 185-187, 527-548; §8 P1
  proves it offline].
- d4. A soft reset cannot cut the write (it is checked once per main-loop pass; the write is inside one pass); a
  reset during the questions or while "SAVING..." prints aborts with nothing written; only power-off or a process
  kill can cut the write [VERIFIED-decomp main.c:131-142; start_menu.c:884-894, 1080-1110].
- d5. A kill that loses a write the emulator never flushed fails SILENTLY: the previous save loads with no message.
  The AI must check WHICH save it continued (TIME / BADGES / POKéDEX on the CONTINUE window; the counter in the .sav)
  [UNVERIFIED: inference; whether mGBA can lose it is the emulator angle].
- d6. The first save of a NEW GAME on a cart holding an old game leaves the OLD game in the other slot (only sectors
  28-31, the Hall of Fame, Trainer Hill and the recorded battle, are erased); a failed write there would CONTINUE the
  other game [VERIFIED-decomp save.c:752-760, 139-175; UNVERIFIED that it plays out live].
- d7. A real write failure (not expected in an emulator) shows the save-failed screen, retries, then returns to the
  title through a soft reset [VERIFIED-decomp save.c:766-786; save_failed_screen.c:159-163, 247-332; strings.c:1090-1095].

**(e) Where a save is impossible or unusual**
- e1. Impossible: in a battle, during any script or message, with any menu or screen open, mid-step
  [VERIFIED-decomp overworld.c:1445, 1461; field_control_avatar.c:95-107].
- e2. No SAVE item: the Safari Zone (RETIRE instead), the link rooms and the Union Room, the Battle Pike, the Battle
  Tower's multi partner room; the Battle Pyramid has REST (it saves, then the game resets) [VERIFIED-decomp
  start_menu.c:276-406, 194, 828-834].
- e3. Forced or scripted saves: the Hall of Fame (automatic), the Battle Tents and Frontier lobbies, Trainer Hill,
  link play (cable club, Berry Blender, link contests), secret-base battles, the Mystery Events house. A reset after
  such a save is caught by the lobby's map script ("didn't save before quitting") [VERIFIED-decomp grep of every
  `Common_EventScript_SaveGame` caller; data/maps/SlateportCity_BattleTentLobby/scripts.inc:15-31, 110-125].
- e4. Unusual but allowed: the Elite Four rooms (each room's ON_LOAD rebuilds its doors from the DEFEATED flag;
  [DOC `PROJECT KNOWLEDGE/06-DECISIONS-LOG.md:5765-5768`]), Trainer Hill, surfing, cycling and underwater (the
  avatar and the dive warps are rebuilt) [VERIFIED-decomp data/maps/EverGrandeCity_SidneysRoom/scripts.inc:1-23;
  overworld.c:1716-1734; field_player_avatar.c:873-886; data/maps/Route134/scripts.inc:1-7].
- e5. After the credits the game resets ITSELF (at THE END any key, or a long wait) -> title -> CONTINUE in the
  bedroom [VERIFIED-decomp credits.c:670-698].

**Cross-angle findings (outside the game angle, flagged)**
- x1. The AI's eyes give the start menu NO options and NO cursor while it takes input: the host reads them only while
  a task named `StartMenuTask` runs, but that task only BUILDS the menu and then becomes `Task_ShowStartMenu`; a
  reopened menu never runs `StartMenuTask` at all; the save dialog's YES/NO (run inside `Task_ShowStartMenu`) and the
  scripted save's `SaveGameTask` are in no eyes table [VERIFIED-code ai_player/host/eyes.py:217-225, 437, 502-505;
  ai_player/eyes/screens.py:216-235, 576-581; sandbox-pokebot/modules/tasks.py:25-32; VERIFIED-decomp task.c:139-153;
  start_menu.c:527-541, 589; field_screen_effect.c:424-431]. A test-side docstring already says so: "the eyes name the
  menu but build no cursor view of it, measured 2026-10-09" [VERIFIED-code ai_player/gates/make_step41_fixtures.py:171-174].
  => a save skill needs these eyes first.
- x2. Play time alone cannot order memory: after a reload play time resumes from the saved value, so a lost
  timeline and the new one share the same play times; the .sav also carries a per-save counter in every sector
  footer, and GAME_STAT_SAVED_GAME [VERIFIED-decomp play_time.c:23-63; overworld.c:1735; save.h:74-82;
  start_menu.c:1090; UNVERIFIED: the design consequence, §6.2].
- x3. The framework's emulator wrapper loads `current_state.ss1` at start whenever it exists (it is written on a
  clean close); after a kill a STALE one would skip the title and CONTINUE altogether [VERIFIED-code
  sandbox-pokebot/modules/libmgba.py:139-146; UNVERIFIED: whether such a file survives in an AI run's profile, and
  whether an mGBA state also carries the cartridge memory].

**The two open user questions (not decided here)**
- q1. WHEN the AI saves changes only the trigger and how much a kill can lose; the save skill is the same. Q2,
  reloading to undo a loss, decides whether a deliberate soft-reset skill exists and how losses are counted. Even
  under "No save-scum", a kill between a loss and the next save rolls the GAME back past the loss, so R2 must keep
  lessons apart from its mirror of the game state [UNVERIFIED: design inference from the verified facts above; §6.5].

---

## 1. (a) The SAVE flow, end to end

### 1.1 When START opens the menu
- The overworld input runs only while `gMain.callback2 == CB2_Overworld` (`CB1_Overworld`) and only when the field
  controls are not locked [VERIFIED-decomp overworld.c:1438-1463].
- START is registered only when the player stands still, or has just reached a tile's centre on a tile with no forced
  movement, and the speed is not `PLAYER_SPEED_FASTEST` [VERIFIED-decomp field_control_avatar.c:95-107]. Only the
  Mach Bike's top gear gives FASTEST; running and the Acro Bike do not block START [VERIFIED-decomp bike.c:1022-1037].
- `ProcessPlayerFieldInput` checks, in order: trainers who see the player, ON_FRAME map scripts, B to surface from a
  dive, step scripts, a wild encounter, arrow warps, A on what is in front, door warps, A to dive, and only then START
  [VERIFIED-decomp field_control_avatar.c:133-187]. => a START pressed on a frame where any of those fires is lost;
  the skill must SEE the menu open, never assume it.
- START plays SE_WIN_OPEN and calls `ShowStartMenu`: the people and the player freeze, the controls lock, and a task
  starts with `StartMenuTask` (it builds the menu over several frames, printing two items per frame) and then
  switches itself to `Task_ShowStartMenu`, which takes the input [VERIFIED-decomp field_control_avatar.c:182-187;
  start_menu.c:480-541, 561-591; task.c:139-153]. The menu takes input about 6 + ceil(items/2) frames after START
  [UNVERIFIED: counted from the state machine, not measured].
- Closing POKéDEX, POKéMON, BAG, POKéNAV, OPTION or the trainer card returns to the field with the START menu REOPENED: the menu
  is rebuilt by a field callback and `Task_ShowStartMenu` is created directly after the fade-in [VERIFIED-decomp
  overworld.c:1670-1675; start_menu.c:543-559; field_screen_effect.c:424-444].
- B or START closes the menu; A on POKéDEX does nothing while nothing has been seen; choosing SAVE starts no screen
  fade [VERIFIED-decomp start_menu.c:607-634].

### 1.2 The items and the cursor
- Normal menu: POKéDEX (FLAG_SYS_POKEDEX_GET), POKéMON (FLAG_SYS_POKEMON_GET), BAG, POKéNAV (FLAG_SYS_POKENAV_GET), the
  PLAYER item (it shows the player's NAME, `{PLAYER}`), SAVE, OPTION, EXIT [VERIFIED-decomp start_menu.c:182-197,
  315-337; strings.c:1510-1519]. SAVE is therefore the 3rd item in the truck, the 4th after the starter, up to the
  6th [UNVERIFIED: counted from those flags].
- The other menus: Safari Zone = RETIRE, POKéDEX, POKéMON, BAG, PLAYER, OPTION, EXIT; link and Union Room = no SAVE;
  Battle Pike = no SAVE; Battle Pyramid = POKéMON, BAG (the Pyramid bag), PLAYER, REST, RETIRE, OPTION, EXIT; multi
  partner room = no SAVE [VERIFIED-decomp start_menu.c:276-308, 339-406].
- The cursor `sStartMenuCursorPos` is an EWRAM index kept between openings; it changes only with Up/Down (wrapping
  round) and is cleared only when RAM is cleared by a reboot. Items appear as the story goes on, so a remembered index
  can point at a DIFFERENT item next time [VERIFIED-decomp start_menu.c:83, 511, 598, 604; menu.c:948-962;
  main.c:428-438; include/gba/syscall.h:4-12]. => read the cursor by the item's WORD.

### 1.3 The dialog, step by step (all in start_menu.c)
| # | callback | what the screen shows | input | next |
|---|----------|-----------------------|-------|------|
| 1 | `SaveStartCallback` -> `InitSave` (809-815, 877-882) | (the 15 x 14 map view is copied into the save block) | none | 2 |
| 2 | `SaveConfirmSaveCallback` (978-994) | start menu removed; the SAVE WINDOW top left: location name, PLAYER <name>, BADGES <n>, [POKéDEX <n>], TIME <h:mm> (1332-1393); message "Would you like to save the game?" | none until printed | 3 |
| 3 | `SaveYesNoCallback` (996-1001) | YES/NO, cursor on YES | | 4 |
| 4 | `SaveConfirmInputCallback` (1003-1032) | | A on YES -> by cart state (1.4); NO or B -> back to the start menu (823-827) | 5 or 8 |
| 5 | `SaveFileExistsCallback` (1035-1047) | "There is already a saved file. / Is it okay to overwrite it?" or the WARNING | none until printed (A per WARNING page) | 6 |
| 6 | `SaveConfirmOverwriteCallback` (1056-1061) / `...DefaultNoCallback` (1049-1054) | YES/NO, cursor on YES / on NO (WARNING) | | 7 |
| 7 | `SaveOverwriteInputCallback` (1063-1078) | | A on YES -> 8; NO or B -> back to the start menu | 8 |
| 8 | `SaveSavingMessageCallback` (1080-1084) | "SAVING... / DON'T TURN OFF THE POWER." | none | 9 when printed (884-894) |
| 9 | `SaveDoSaveCallback` (1086-1110) | THE WRITE (1.5); then "{PLAYER} saved the game." (or "Save error. / Please exchange the backup memory."); a 60-frame timer starts | none | 10 |
| 10 | `SaveSuccessCallback` (1112-1121) | when printed: SE_SAVE (the jingle) | | 11 |
| 11 | `SaveReturnSuccessCallback` (1123-1134) with `SaveSuccesTimer` (947-962) | after the jingle ends: 60 frames, or at once while A is HELD; the save window is removed | | 12 |
| 12 | `SaveCallback` SAVE_SUCCESS (828-834) | message cleared, people unfrozen, controls unlocked (Pyramid: soft reset); the task ends | | free overworld |
[VERIFIED-decomp: every row, start_menu.c at the lines given; texts data/text/save.inc:1-29, strings.c:1641-1644]

- READING BY WORDS: the game's ellipsis in "SAVING…" is ONE character, not three dots, and POKéDEX / POKéMON carry
  "é" [VERIFIED-decomp data/text/save.inc:10; strings.c:1510-1513]; a matcher must compare what the eyes decode.
  (In this note "..." stands for "…" for typing only.)
- The save window's TIME is drawn at step 2, the play time is SAVED at step 9: they differ by the dialog's length, so
  the saved h:mm can be one minute later than the window showed [VERIFIED-decomp start_menu.c:978-994 vs 1086-1110;
  main.c:165].

### 1.4 The three shapes of the dialog, by the cartridge's state
| shape | when | questions | write type |
|-------|------|-----------|------------|
| A | the save read at boot was EMPTY or CORRUPT, and this is the first save since NEW GAME | 1 ("Would you like...") | SAVE_OVERWRITE_DIFFERENT_FILE |
| B | the game was CONTINUEd, or any later save of the same session (also on a fresh cart) | 2, both on YES | SAVE_NORMAL |
| C | the save read at boot was OK or ERROR, and this is the first save since NEW GAME | "Would you like..." then the 4-page WARNING, cursor on NO | SAVE_OVERWRITE_DIFFERENT_FILE |
[VERIFIED-decomp start_menu.c:1003-1061, 1093-1101]
- Why: `gSaveFileStatus` is written only by `LoadGameSave` at boot, so it stays EMPTY all session after a first save
  on a fresh cart [VERIFIED-decomp save.c:872-891; grep: no other writer in src/]. `gDifferentSaveFile` is set by
  `NewGameInitData`, cleared at boot and after the first write [VERIFIED-decomp new_game.c:139-141, 149-155;
  intro.c:1152; start_menu.c:1093-1096].
- SAVE_OVERWRITE_DIFFERENT_FILE first ERASES sectors 28-31 (Hall of Fame, Trainer Hill, the recorded battle), then
  writes one slot like a normal save; the OTHER slot is untouched [VERIFIED-decomp save.c:752-760].
- The WARNING text is 4 pages: "WARNING!" | "There is a different game file that / is already saved." | "If you save
  now, the other file's / adventure, including items and / POKéMON, will be entirely lost." | "Are you sure you want
  to save now / and overwrite the other save file?" [VERIFIED-decomp data/text/save.inc:16-24].

### 1.5 The write itself
- `SaveDoSaveCallback` runs on the first call after the "SAVING..." text has finished printing (`RunSaveCallback`
  returns early while printer 0 is active). It increments GAME_STAT_SAVED_GAME, pauses a Pyramid challenge, and calls
  `TrySavingData` [VERIFIED-decomp start_menu.c:884-894, 1086-1101].
- `TrySavingData` -> `HandleSavingData(SAVE_NORMAL)`: the party and the people are copied into SaveBlock1, then
  `WriteSaveSectorOrSlot` raises the counter by one, moves the rotation by one and writes all 14 sectors of slot
  (counter mod 2): SaveBlock2 (1 sector), SaveBlock1 (4), the PC boxes (9) [VERIFIED-decomp save.c:55-73, 139-175,
  708-741, 766-786].
- Each sector: erase, program 4096 bytes one at a time, verify; up to 3 tries [VERIFIED-decomp agb_flash.c:260-277;
  agb_flash_mx.c:77-193]. A sector still bad -> `DoSaveFailedScreen` [VERIFIED-decomp save.c:775-785].
- All of it runs inside ONE main-loop pass: no play-time count (`PlayTimeCounter_Update` sits in the loop), no key
  read, no soft-reset check until it returns; the VBlank interrupt still runs `Random()` and the vblank counter
  [VERIFIED-decomp main.c:131-167, 340-366].
- Frames: the decomp cannot say how long mGBA takes [UNVERIFIED]. Everything else in the dialog is text: the delay is
  8, 4 or 1 frames per character (SLOW, MID, FAST, a saved option) and A/B speeds it up [VERIFIED-decomp menu.c:77-82,
  191-202, 481-488]. At MID, shape B is roughly 128 + 230 + 130 + 90 frames of text, plus the jingle, plus 60, plus
  the write [UNVERIFIED estimate: characters x 4; §8 P2]. At x1 an hour is 216,000 frames [DOC backlog :292].

### 1.6 What a person presses (one NEW press each, released in between)
- Shape A: START, cursor to SAVE, A, A (YES).
- Shape B: START, cursor to SAVE, A, A (YES), A (YES).
- Shape C: START, cursor to SAVE, A, A (YES), A to turn each WARNING page, Up (to YES), A.
- Then nothing: the box closes by itself; holding A closes it as soon as the jingle ends [VERIFIED-decomp
  start_menu.c:947-962, 1123-1134].
- The YES/NO does not wrap; B always means NO [VERIFIED-decomp menu.c:1013-1041].

### 1.7 The other ways the game saves
- `special SaveGame` (`Common_EventScript_SaveGame`): the same dialog from step 2 on, run by `SaveGameTask` inside a
  script; VAR_RESULT = 1 when saved, 0 when cancelled or failed [VERIFIED-decomp start_menu.c:896-930;
  data/scripts/std_msgbox.inc:46-48; data/specials.inc:112]. Callers: the 7 Frontier lobbies, the 3 Battle Tents,
  Trainer Hill, the contest lobby (LINK contests only), the cable club, the Berry Blender, secret-base battles, the
  Mystery Events house [VERIFIED-decomp grep `call Common_EventScript_SaveGame` in data/; e.g.
  data/maps/LilycoveCity_ContestLobby/scripts.inc:615-620].
- The Hall of Fame: "SAVING... DON'T TURN OFF THE POWER." with no question, `TrySavingData(SAVE_HALL_OF_FAME)` (a full
  slot plus the Hall of Fame sectors); `GameClear` set the continue-game warp to the player's bedroom first
  [VERIFIED-decomp hall_of_fame.c:516-541; save.c:718-736; post_battle_event_funcs.c:12-41].
- Link and Frontier saves (`SAVE_LINK`) rewrite SaveBlock2 and SaveBlock1 IN PLACE in the current slot (no counter
  increase, no double buffer) [VERIFIED-decomp save.c:742-751, 310-321; frontier_util.c:2421-2440]. Not a story path.
- The clock-reset screen saves too [VERIFIED-decomp reset_rtc_screen.c:708-720].

---

## 2. (b) The title screen and CONTINUE

### 2.1 Boot to the title
- `AgbMain` clears ALL RAM (non-modern build), identifies the flash; with no flash the main callback is NULL and
  the game never leaves a blank screen [VERIFIED-decomp main.c:94, 105-119]. (A wrong emulator save type would
  look like this [UNVERIFIED].)
- The copyright screen counts states 1-139 one per frame, then fades; it reads no input. At its end the save is
  READ: `LoadGameSave(SAVE_NORMAL)` sets `gSaveFileStatus`; an empty or corrupt save resets the options to default
  [VERIFIED-decomp intro.c:116-118, 1072-1121, 1146-1158].
- The intro movie ends on any new key while no palette fade runs [VERIFIED-decomp intro.c:1042-1058].
- The title: phases 1 and 2 (logo shine, banners) end early on a new A, B, START or SELECT (the skip carries over
  from phase 1 into phase 2); phase 3 takes a new A or START -> fade -> the main menu. Idle in phase 3 until the music
  ends -> back to the copyright screen [VERIFIED-decomp title_screen.c:684-828].
- Combos held in phase 3: B+SELECT+UP -> "Clear all save data areas?" YES/NO with the cursor on NO; YES erases all 32
  sectors ("Clearing data... Please wait."). B+SELECT+LEFT -> the clock reset, only if `CanResetRTC()`; B+SELECT ->
  the Berry fix program [VERIFIED-decomp title_screen.c:39-41, 788-803; clear_save_data_screen.c:80-107;
  save.c:99-109; event_data.c:156-162; strings.c:1769-1770].

### 2.2 The main menu
| save read at boot | first page (A) | items, top to bottom |
|-------------------|----------------|----------------------|
| OK | none | CONTINUE, NEW GAME, OPTION (MYSTERY GIFT before OPTION if enabled) |
| ERROR (one slot OK, the other broken; usually a cut newest write) | "The save file is corrupted. The / previous save file will be loaded." (shown even if the OK slot is the newer one) | CONTINUE, NEW GAME, OPTION |
| CORRUPT (both slots bad) | "The save file has been erased / due to corruption or damage." | NEW GAME, OPTION |
| EMPTY | none | NEW GAME, OPTION |
[VERIFIED-decomp main_menu.c:510-515, 625-692, 740-876; strings.c:24-36]
- Then, if the clock reports an error: "The internal battery has run dry. / The game can be played." | "However,
  clock-based events will / no longer occur." (A) [VERIFIED-decomp main_menu.c:705-738; strings.c:38].
- The cursor starts on the first item (CONTINUE when there is one): `sCurrItemAndOptionMenuCheck` lives in EWRAM,
  cleared at boot; it remembers the item only within one power-on (and points at OPTION when coming back from it)
  [VERIFIED-decomp main_menu.c:172, 672-690]. Up/Down do not wrap; B returns to the title [VERIFIED-decomp
  main_menu.c:884-927, 1109-1117].
- The CONTINUE window: row 1 "PLAYER" + the name (blue for a boy, red for a girl) and "TIME" + h:mm; row 2 "POKéDEX"
  + the caught count (Hoenn or National) only once the Pokédex is owned, and "BADGES" + n [VERIFIED-decomp
  main_menu.c:767-778, 2127-2186; strings.c:1362-1365]. No location, no party.
- A on CONTINUE -> fade -> `CB2_ContinueSavedGame` [VERIFIED-decomp main_menu.c:936-976, 1064-1068].

### 2.3 From CONTINUE to a free player
- `CB2_ContinueSavedGame`: music stops, the Safari flag clears, Frontier streaks reset if an OLDER slot loaded, the
  saved map header loads, dive/hole warps clear, the map's people get their scripts back (special loaders for the
  Pyramid and Trainer Hill floors), people unfreeze, clock events run, misc states update, the map is built FROM THE
  SAVE (`InitMapFromSavedGame`: the saved 15 x 14 view is put back, then ON_LOAD), the play time starts, the script
  engine resets, controls unlock [VERIFIED-decomp overworld.c:1705-1738; fieldmap.c:69-77, 433-470].
- No continue-game warp (normal saves) -> `CB2_ReturnToField` with `FieldCB_FadeTryShowMapPopup`: ON_RESUME and
  ON_RETURN_TO_FIELD scripts run, every saved person is re-spawned where they stood, the map name pops up, the screen
  fades in from black, and the controls stay locked until the weather fade-in ends (`Task_ExitNonDoor`)
  [VERIFIED-decomp overworld.c:1746-1752, 1625-1645, 1961-1985 (ReturnToFieldLocal), 2131-2152, 2180-2185;
  field_screen_effect.c:256-296, 404-420].
- On a door tile the player would walk one step down out of the door (`Task_ExitDoor`) [VERIFIED-decomp
  field_screen_effect.c:256-271, 317-364]; a person cannot normally stand still on a door tile, so this should not
  happen after a START-menu save [UNVERIFIED].
- With the continue-game warp (Hall of Fame, link, Frontier saves) -> the warp destination is loaded like a door warp
  (`CB2_LoadMap`, with ON_TRANSITION and the temp flags cleared) [VERIFIED-decomp overworld.c:1739-1745, 1572-1580,
  827-860].

---

## 3. (c) What a save stores, what CONTINUE restores, and what it does not

### 3.1 Stored (the 14 sectors of a slot)
- SaveBlock2 (sector id 0): player name, gender, `specialSaveWarpFlags` (bit 0 = the continue-game warp), trainer ID,
  play time (u16 hours, u8 minutes, seconds and frames, @0x0E-0x12), options (button mode, text speed, frame, sound,
  battle style, battle scene), the Pokédex (owned/seen and order), `localTimeOffset` @0x98, `lastBerryTreeUpdate`
  @0xA0, the encryption key, Frontier data [VERIFIED-decomp include/global.h:508-542].
- SaveBlock1 (sector ids 1-4): `pos` @0x00 (the tile), `location` @0x04 (map group, map number, warp id, x, y),
  `continueGameWarp`, `dynamicWarp`, `lastHealLocation` (whiteout/Teleport), `escapeWarp` (Dig/Escape Rope), saved
  music, weather, Flash level, the 15 x 14 `mapView`, the party count @0x234 and the party @0x238 (6 x 100 bytes, each
  starting with its PID), money, coins, the registered item, PC items, the five bag pockets, Pokéblocks, seen flags,
  trainer rematches, `objectEvents` @0xA30 (every person on the map incl. the player: position, facing, movement
  direction, the `isPlayer` bit), object templates, ALL flags @0x1270, ALL vars @0x139C (the temp ones too), game
  stats @0x159C, berry trees, secret bases, decorations, TV, outbreak, mail, daycare, the roamer @0x31DC, ...
  [VERIFIED-decomp include/global.h:581-588, 984-1078; include/global.fieldmap.h:194-250].
- The PC boxes (sector ids 5-13) [VERIFIED-decomp save.c:64-72].
- Money, coins, bag quantities and game stats are XOR-encrypted with SaveBlock2's key; the 48-byte Pokémon
  substructures are encrypted with PID ^ OTID; the PID itself is plain [VERIFIED-decomp load_save.c:274-293;
  overworld.c:447-465; UNVERIFIED: the Pokémon substructure encryption (not opened this session)].

### 3.2 What a normal CONTINUE puts back
| thing | how | tag |
|-------|-----|-----|
| map, tile | `LoadSaveblockMapHeader` from `location`; the player re-spawned from the saved object events | VERIFIED-decomp overworld.c:597-601; event_object_movement.c:1715-1796 |
| facing | the player's avatar transition turns them to the saved `movementDirection` (it sets the facing too) | VERIFIED-decomp field_player_avatar.c:849-886, 1373-1379; event_object_movement.c:1812-1818, 1867-1875, 2361-2367 |
| surfing / bike / underwater | the avatar state is rebuilt from the saved graphics id; the surf blob is re-created | VERIFIED-decomp field_player_avatar.c:873-893 |
| party (same PIDs), boxes, bag, money | copied whole at the write, copied back at boot | VERIFIED-decomp load_save.c:160-206; save.c:872-891 |
| flags, vars (incl. temp flags/vars, Strength's active flag) | in SaveBlock1; the temp clear runs only on warp/connection loads | VERIFIED-decomp event_data.c:39-48; overworld.c:798, 848 |
| people | re-spawned where they stood when saved | VERIFIED-decomp event_object_movement.c:1715-1796 |
| metatiles near the player | the saved 15 x 14 view is restored, then ON_LOAD runs | VERIFIED-decomp fieldmap.c:69-77, 391-404, 433-470 |
| play time | resumes counting from the saved value | VERIFIED-decomp overworld.c:1735; play_time.c:23-63 |
| options (text speed etc.) | in SaveBlock2 | VERIFIED-decomp include/global.h:518-524 |
| dive warps | ON_RESUME scripts set them again after they were cleared | VERIFIED-decomp overworld.c:1716, 2150; data/maps/Route134/scripts.inc:1-7 |

### 3.3 Not restored, or changed by CONTINUE
- The screen: always a fresh overworld; no menu, no message [VERIFIED-decomp overworld.c:1746-1752].
- A running script: none is resumed (`ScriptContext_Init`); ON_LOAD, ON_RESUME, ON_RETURN_TO_FIELD (and later
  ON_FRAME) run; ON_TRANSITION does not on this path [VERIFIED-decomp overworld.c:1736, 2150, 2184, 807/860 (only in
  the warp loaders); fieldmap.c:69-77]. A START-menu save can only happen with no script running (1.1), so nothing
  is lost; a SCRIPTED save is resumed by map scripts reading vars instead (e.g. the tent's CHALLENGE_STATUS_SAVING)
  [VERIFIED-decomp data/maps/SlateportCity_BattleTentLobby/scripts.inc:15-31].
- A battle: no battle state is ever saved (1.1).
- The RNG: not in the save. Vanilla (no BUGFIX) zeroes it with all RAM at power-on and advances it once per VBlank
  outside link/Frontier/recorded battles, plus every `Random()` call [VERIFIED-decomp main.c:94, 108-110, 228-236,
  364-366]. => after a reload, what happens next depends on the frame timing of the presses, not on a re-seed.
- The clock: the cartridge's hardware clock is not in the save; the in-game time = hardware clock - `localTimeOffset`.
  On CONTINUE `DoTimeBasedEvents` runs the day's updates (daily flags, Dewford trend, TV, weather, Pokérus, Mirage,
  Shoal Cave items, lottery) if the day changed, and grows berries by the minutes elapsed since `lastBerryTreeUpdate`
  (not inside a Pokémon Center) [VERIFIED-decomp rtc.c:290-309; clock.c:26-74; overworld.c:1725].
- Also on CONTINUE: the Safari flag clears; the ambient cry is re-chosen; the Cycling Road challenge resets; the
  roamer's location history updates and it MOVES; match-call counters reset; today's rival is put on TV
  [VERIFIED-decomp overworld.c:416-423, 1711, 1736-1749].
- If the OLDER slot loaded (status ERROR): Frontier win streaks reset [VERIFIED-decomp overworld.c:1712-1713].
- UI memory (the START cursor, the main-menu cursor) is cleared by the reboot that any CONTINUE needs (c6)
  [VERIFIED-decomp main.c:428-438].

---

## 4. (d) Failure modes

### 4.1 The two slots
- Layout: sectors 0-13 = slot 1, 14-27 = slot 2, 28-29 = Hall of Fame, 30 = Trainer Hill, 31 = the recorded battle;
  a sector is 4 KiB: 3968 data bytes, then a footer with `id` @0xFF4 (u16), `checksum` @0xFF6 (u16), `signature`
  @0xFF8 (u32 0x08012025), `counter` @0xFFC (u32); the .sav is 32 x 4 KiB = 128 KiB [VERIFIED-decomp save.c:25-42;
  include/save.h:6-30, 74-85].
- Each full save: counter + 1; slot = counter mod 2; the physical position of sector id i = (i + rotation) mod 14,
  the rotation + 1 per save [VERIFIED-decomp save.c:139-163, 177-209]. => saves alternate slots; the cartridge holds
  the NEWEST and the PREVIOUS save only.
- The checksum: the 32-bit sum of the data words over the sector's real data size (not all 3968 bytes), folded to 16
  bits [VERIFIED-decomp save.c:675-687, 533, 565].
- At boot (`GetSaveValidStatus`): a slot with no valid signature at all = EMPTY; with all 14 ids valid = OK (its
  counter = the counter of the last valid sector read); else ERROR. Both OK -> the higher counter (with a wrap rule
  for 0 / 0xFFFFFFFF); one OK -> it, status OK if the other is EMPTY, ERROR if the other is broken; none OK -> EMPTY if
  both empty, else CORRUPT. Then the chosen slot is copied sector by sector, skipping any sector whose signature or
  checksum is wrong [VERIFIED-decomp save.c:467-513, 515-638].

### 4.2 An interrupted write [UNVERIFIED: derived; §8 P1 proves it]
- The slot being written held the save from TWO saves ago, rotated 2 places behind. Writing ids 0..k of the new save
  overwrites the old ids 2..k+2; the old ids 0, 1 and k+3..13 survive. The slot then has ids {0..k, 0, 1, k+3..13}:
  ids k+1 and k+2 are missing for every k from 0 to 11, and id 13 for k = 12. Every cut therefore leaves the slot
  ERROR and the previous slot loads, with the "corrupted" page (from save.c:155-163, 185-187, 527-548).
- A cut inside a sector: the sector is erased first and programmed from byte 0 up, so its footer (the last 12 bytes)
  is still erased (signature 0xFFFFFFFF) unless the cut lands in the last few bytes [VERIFIED-decomp
  agb_flash_mx.c:156-193; include/save.h:74-82]. A cut in the last 4 bytes of the LAST sector could leave a complete
  slot with a garbled counter [UNVERIFIED; negligible window].

### 4.3 Resets
- The soft reset (A+B+START+SELECT held) is checked once per main-loop pass, unless `gSoftResetDisabled` (set only
  during link saves and link activities: trade, Berry Blender) [VERIFIED-decomp main.c:131-142; start_menu.c:1292-1306;
  save.c:986, 1048; grep: berry_blender.c:2781, trade.c:4412]. A reset before the write
  (the questions, "SAVING..." still printing) loses nothing and writes nothing; the write cannot be cut by it; a
  reset after the write is harmless [VERIFIED-decomp start_menu.c:884-894, 1080-1110].
- A power-off or a process kill CAN cut the write -> 4.2.

### 4.4 Silent fallback (the trap for R1's proof)
- If the newest save never reaches the .sav on disk (a kill before the emulator flushed it), the cartridge simply
  still holds the two older saves: CONTINUE loads the previous save with NO message [UNVERIFIED: inference from 4.1;
  the flush is the emulator angle]. => R1's proof must assert WHICH save loaded (§6.1), not just that one did.

### 4.5 NEW GAME over an old cart
- The first save of the new game writes slot (old counter + 1) mod 2 and erases only sectors 28-31; the other slot
  still holds the OLD game's newest save. A cut in that first write would CONTINUE the old game ("corrupted, the
  previous save file will be loaded") [VERIFIED-decomp save.c:752-760, 139-175, 607-623; UNVERIFIED live]. A deploy
  that starts every new game on a fresh, empty `.sav` (DP4's "new profile" [DOC backlog :378-379]) never meets this.

### 4.6 A real write failure
- After 3 tries a bad sector -> the save-failed screen: "Save failed. Checking the backup / memory... Please wait. /
  'Time required: about 1 minute'"; it wipes and retries up to 3 times; then "Save completed. / 'Game play cannot be
  continued. / Returning to the title screen.'" or "The backup memory is damaged, or / the internal battery has run
  dry. / You can still play, but not save."; A -> fade -> soft reset (normal saves) [VERIFIED-decomp
  save_failed_screen.c:159-163, 247-332; strings.c:1090-1095]. The in-dialog text "Save error. / Please exchange the
  backup memory." belongs to the same failure [VERIFIED-decomp start_menu.c:1103-1106; data/text/save.inc:26-29].

---

## 5. (e) Where a save is impossible or unusual

| place / moment | what the game does | tag |
|----------------|--------------------|-----|
| a battle | no START menu (callback2 is not the overworld) | VERIFIED-decomp overworld.c:1459-1463 |
| a script, a message box, a cutscene | controls locked: START ignored | VERIFIED-decomp overworld.c:1445 |
| walking between tiles; sliding on a forced-movement tile; Mach Bike top gear | START not registered | VERIFIED-decomp field_control_avatar.c:95-107 |
| the frame a trainer spots the player / an ON_FRAME or step script / an encounter / a warp starts | that event wins | VERIFIED-decomp field_control_avatar.c:133-187 |
| Safari Zone | no SAVE; RETIRE first | VERIFIED-decomp start_menu.c:288-291, 339-348 |
| cable-club rooms, Union Room, Battle Pike, Battle Tower multi partner room | no SAVE | VERIFIED-decomp start_menu.c:280-303 |
| Battle Pyramid | REST: "Your BATTLE PYRAMID quest will be / saved so that you may quit for now. / Is that okay?", then save + soft reset | VERIFIED-decomp start_menu.c:984-987, 828-834; battle_pyramid.c:1439-1454; data/maps/BattleFrontier_BattlePyramidFloor/scripts.inc:131-134 |
| Battle Tents, Frontier lobbies, Trainer Hill, link play, secret-base battles, Mystery Events house | the script ASKS for a save first | VERIFIED-decomp 1.7 |
| Hall of Fame | automatic save, no question; CONTINUE later wakes in the bedroom | VERIFIED-decomp hall_of_fame.c:516-541; post_battle_event_funcs.c:36-41 |
| the credits' THE END | any key -> soft reset -> title | VERIFIED-decomp credits.c:670-698 |
| Elite Four rooms | SAVE allowed; ON_LOAD rebuilds the doors from the DEFEATED flags ("merely RELOADING a post-victory save re-opens the door") | VERIFIED-decomp data/maps/EverGrandeCity_SidneysRoom/scripts.inc:1-23; DOC 06-DECISIONS-LOG.md:5765-5768 |
| Trainer Hill floors, Pyramid floors | allowed; the floor is rebuilt on CONTINUE | VERIFIED-decomp overworld.c:1717-1734 |
| underwater, surfing, on a bike, in the truck at the very start | allowed; avatar and dive warps rebuilt | VERIFIED-decomp 3.2 |
| a Pokémon Center | allowed; clock events skip inside it | VERIFIED-decomp clock.c:28 |

---

## 6. What these game facts mean for R1 + R2 (no decisions; for the design)

### 6.1 The proof "kill, CONTINUE, same PIDs and tile"
- What CONTINUE must reproduce, readable two ways: (i) in RAM after CONTINUE: the party PIDs, `location` +
  `pos`, the player's facing; (ii) offline in the `.sav`: the newest valid slot (4.1), SaveBlock1's first sector (id
  1): `pos` @0x00, `location` @0x04, party count @0x234, party @0x238 (PID = the first u32 of each 100 bytes), object
  events @0xA30 (the one with `isPlayer`, facing @+0x18); SaveBlock2 (id 0): play time @0x0E [VERIFIED-decomp
  include/global.h:508-517, 984-1001, 1018; include/global.fieldmap.h:194-250; include/save.h:74-82].
- VACUITY (rule 3 and 4 of SESSION DISCIPLINE): if the kill lost the newest write, the PREVIOUS save loads silently
  (4.4) and its PIDs and tile may ALSO match. The arm needs a party or tile CHANGE between the previous save and the
  tested save, and must assert the loaded save's counter (or its TIME h:mm and badges on the CONTINUE window) equals
  the tested save's [UNVERIFIED: design inference].
- "Same tile" is exact for a START-menu save (no warp on that path); after a Hall of Fame or link save it is NOT
  (c5) [VERIFIED-decomp overworld.c:1739-1752].

### 6.2 Stamping R2's memory
- Play time: hours, minutes, seconds, frames in SaveBlock2; counted once per main-loop pass from NEW GAME or
  CONTINUE; NOT counted during the flash write; shown as h:mm on the save window, the CONTINUE window and the trainer
  card [VERIFIED-decomp play_time.c:23-63; main.c:165; start_menu.c:1385-1390; main_menu.c:2142-2153;
  UNVERIFIED: the trainer card (not opened)].
- THE PROBLEM: after a reload the play time resumes from the saved value, so the lines a killed timeline wrote after
  the save and the lines the new timeline writes share play-time values. A play-time-only filter ("load memory not
  newer than the save") is right after ONE kill, but a SECOND kill-and-reload resurrects the first lost timeline's
  lines that fall below the second save's time, unless the first resume physically dropped them from the file
  [UNVERIFIED: logical consequence of play_time.c + overworld.c:1735; §8 P6 proves it]. Options for the design (not
  chosen here): truncate the file at each resume, or stamp each line with the save it descends from as well.
- What the game offers as a lineage key: the sector `counter` (u32, +1 per full save, in every footer, monotonic
  across slots) [VERIFIED-decomp save.c:155-159, 198-200]; GAME_STAT_SAVED_GAME (+1 per START-menu or scripted save,
  not per Hall of Fame or link save; XOR-encrypted in RAM) [VERIFIED-decomp start_menu.c:1090; overworld.c:447-459;
  include/constants/game_stat.h:4]. What a PERSON sees: TIME h:mm, BADGES, POKéDEX on the CONTINUE window (minute
  resolution, so two saves in one minute look alike) [VERIFIED-decomp main_menu.c:2127-2186]. Whether the host may use
  the hidden counter for its own bookkeeping (not for the AI's choices) is a design question (USER RULING 40's line is
  about what the AI acts on) [UNVERIFIED].
- L3 (a)-(b) keys mons by (PID, species): PIDs survive save and CONTINUE byte for byte (the party is copied whole) and
  the boxes ride in the same slot [VERIFIED-decomp load_save.c:160-178; save.c:64-72].

### 6.3 DP4 (the `.sav` is the durable copy)
- The cartridge itself keeps two saves (newest, previous); "keep the newest 10" can only be host copies
  [VERIFIED-decomp save.c:25-42, 155-163]. The framework already copies the `.sav` to `saves/<timestamp>.sav` on every
  savedata update callback [VERIFIED-code sandbox-pokebot/modules/libmgba.py:158-161, 243-256].
- A deploy "new game" on a NEW profile with an empty `.sav` gives shape A on the first save and never the WARNING
  (1.4) and never the old-game fallback (4.5) [VERIFIED-decomp start_menu.c:1008-1019].

### 6.4 R5's free screen vs the game's START gate
- `player_free` = OVERWORLD, no script, controls free, no menu, no text box, nothing waiting, position settled
  [VERIFIED-code ai_player/hands/dialogue.py:131-137]. The game additionally ignores START at Mach-Bike top gear and on
  any frame an earlier event fires (1.1). => after pressing START the save skill must read that the menu opened, and
  retry or give up within a bound [UNVERIFIED: design inference].

### 6.5 The two open user questions [DOC 04-HANDOFF.md:61]: what each answer would change (NOT decided)
**Q1. When does the AI save?**
- Any answer uses the same skill and the same constraints: only on a free overworld screen; never in the Safari
  Zone, link rooms, the Pike, the Pyramid (REST resets the game); the game asks no question about WHEN [VERIFIED-decomp
  1.1, §5].
- "Like a person at natural points" (before a gym leader or a boss, after a hard catch, at a Pokémon Center, before a
  long cave, before stopping): needs triggers read from the game (map, badges, party changes); more saves = less lost
  to a kill, at a few hundred frames each [UNVERIFIED: frame cost, §8 P2].
- "Only when stopping": a kill loses everything since the last stop; R2's rollback window is then a whole session.
- "Every N minutes of play": simple, but must tolerate "not now" (battle, script, Safari, link rooms, the Pike) and
  skip places where the item means something else (the Pyramid's REST resets the game).
- What changes in R2: only how far back memory may have to roll after a kill.
- Shape C exists only when a NEW GAME starts on a cart that already has a save; a fresh-profile deploy avoids it.
**Q2. May it reload a save to undo a loss?**
- If NO (the backlog's default "No save-scum" [DOC backlog :294]): a loss is a whiteout: half the money, the party
  healed, back to the last heal location; the boss stays unbeaten [VERIFIED-decomp overworld.c:358-366]. Reloads happen
  only to recover from crashes and kills. ⚠ Even then a kill landing between a loss and the next save rolls the GAME
  back past the loss, an involuntary undo. A person whose console crashed still REMEMBERS the loss: R2 then needs two
  kinds of memory, a mirror of the game state that rolls back to the save, and lessons (R11's per-fight losses, what
  failed) that do not [UNVERIFIED: design inference].
- If YES: the AI needs a deliberate soft-reset skill (A+B+START+SELECT held, accepted on any screen outside link
  saves) and the CONTINUE skill; a retry is not a replay (the RNG restarts at 0 and runs per VBlank, so the timing of
  presses changes the fight); the game's own counters (battles, saves; there is no whiteout counter) roll back with
  the save, so R11 and R13 would have to count reloaded losses outside the game, or a fitness reading only game
  counters would hide them [VERIFIED-decomp main.c:131-142, 94, 366; include/constants/game_stat.h:4-15; UNVERIFIED:
  the R11/R13 consequence]. It also has to say WHEN a reload is allowed (after the whiteout only, or mid-battle, which
  the game allows) and how many times per fight.
- Either way the CONTINUE skill is needed (kills, the credits' reset, the Pyramid's REST) [VERIFIED-decomp
  credits.c:670-698; battle_pyramid.c:1450-1454].

---

## 7. Cross-angle findings (outside angle 1; each needs its own owner)

- **x1. The eyes cannot see the START menu's items or cursor, nor the save dialog's YES/NO.** The host reads
  `sNumStartMenuActions`, `sCurrentStartMenuActions`, `sStartMenuCursorPos` only `if "StartMenuTask" in tasks`
  [VERIFIED-code ai_player/host/eyes.py:502-505]; `tasks` is keyed by each active task's CURRENT function symbol
  [VERIFIED-code ai_player/host/eyes.py:437; sandbox-pokebot/modules/tasks.py:25-32, 164-170]; `screens.read_ui` builds
  the start-menu view only for `StartMenuTask` [VERIFIED-code ai_player/eyes/screens.py:216-235, 576-581]. In the game
  `StartMenuTask` only builds the menu, then the same task becomes `Task_ShowStartMenu` (the input) [VERIFIED-decomp
  start_menu.c:527-541, 589; task.c:139-153]; a reopened menu never runs `StartMenuTask` [VERIFIED-decomp
  field_screen_effect.c:424-431]. The save dialog's YES/NO polls `sMenu` from inside `Task_ShowStartMenu` (gMenuCallback
  -> sSaveDialogCallback), a task not in `_SMENU_TASKS` [VERIFIED-code ai_player/host/eyes.py:217-225; VERIFIED-decomp
  start_menu.c:1003-1005, 1063-1065]; the scripted save runs `SaveGameTask` [VERIFIED-decomp start_menu.c:896-930].
  `view.py` does CLASSIFY `Task_ShowStartMenu` as the start menu [VERIFIED-code ai_player/eyes/view.py:410-416;
  ai_player/gates/test_eyes.py:397], and a test helper already works around the gap by reading the symbols itself:
  "the eyes name the menu but build no cursor view of it, measured 2026-10-09" [VERIFIED-code
  ai_player/gates/make_step41_fixtures.py:171-174]. => R1 needs: the start-menu view keyed on `Task_ShowStartMenu` (and
  its gMenuCallback / sSaveDialogCallback state), the save dialog's YES/NO via `sMenu`, the message text, and
  `SaveGameTask` for scripted saves.
- **x2. Play time is not a timeline key** (§6.2).
- **x3. The resume file can pre-empt CONTINUE.** The wrapper loads `current_state.ss1` at start whenever it exists
  [VERIFIED-code sandbox-pokebot/modules/libmgba.py:139-146] and writes it on a clean close [DOC backlog :291:
  "the resume file is written on a CLEAN close only (`libmgba.py:141`)"]. After a kill, an older `current_state.ss1`
  from an earlier clean close would resume a STALE emulator state instead of booting to the title [UNVERIFIED: whether
  any such file survives in an AI run's profile; whether an mGBA state also restores the cartridge memory and so
  could roll the `.sav` back].
- **x4. The mGBA flush question** ("does mGBA flush the save before a kill?" [DOC backlog :294]) is not answerable from
  the game. The game's part: the write ends inside "SAVING...", and at least the jingle plus 60 frames pass before the
  box closes (1.3 rows 10-11), so "the box has closed" is the earliest game-visible moment to treat the save as done
  [VERIFIED-decomp start_menu.c:1108, 1123-1134]; whether mGBA's file is current by then is the emulator angle
  [UNVERIFIED].

---

## 8. What would prove the UNVERIFIED claims (read-only design of probes; none was run)

- P1 (4.2, d3): OFFLINE, no emulator. Take two consecutive real `.sav` files of one game (the framework keeps every
  save in `saves/`); synthesise the cut write for k = 0..13 (newer slot's first k+1 rotated sectors over the older
  image), run a port of `GetSaveValidStatus` (save.c:515-638) on each, and assert ERROR + the previous slot every time.
  Fault arm: the same port with the rotation removed must show a k where the slot reads OK (mixed).
- P2 (a6, 1.5): one live run: log the frame the "SAVING..." text finishes and the frame "{PLAYER} saved the game."
  starts, with `gMain.vblankCounter1` vs main-loop passes; also the total dialog frames per shape at the fixture's
  text speed.
- P3 (4.4, x4): the emulator angle: a hard kill (Windows `taskkill /F`) at N frames after "SAVING..." starts, and N
  frames after the box closes;
  boot to the title; parse the `.sav` (newest counter) and read the CONTINUE window. Expected by the game: either the
  new save, or the previous one (with the "corrupted" page only when part of the slot reached the file).
- P4 (x1): a live look at the open START menu printing `look.ui` each frame (expected today: start_menu with no
  options after the build frames), and at the save YES/NO.
- P5 (c2 facing edge): save while the player faces a direction they did not last move in (turn in place), kill,
  CONTINUE, read the facing. Expected equal; the risk is `facingDirectionLocked` cases.
- P6 (6.2): a two-kill toy timeline on paper or in a unit test of the memory loader: save S1 (t=100), play to 150,
  kill; CONTINUE, play to 130, save S2, play to 160, kill; CONTINUE from S2 and list which lines a play-time-only filter
  keeps.
