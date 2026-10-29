> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1r2recon/05-refute.md` (sha256 `33efdd35f58305a2`). Backlog R1 + R2's recon (save, CONTINUE, a memory that survives a kill), angle 5, THE ADVERSARY (it was told to find the errors in angles 1-4): a read-only Claude subagent's NOTE, never truth (the authoritative docs and the code win). Nothing in it was measured live. R1 + R2's build waits for the user's two save answers (`04` item 4).
> **Its own limits:** every closure here is a reading, an offline parse or arithmetic (C1's 133 frames is arithmetic over mGBA's source; C5 is an offline parse of the committed fixtures); none of section 8's probes was run. Its verdicts are a second note, not proof: where it and a note disagree, the cited source decides.
> ⚠ **MEASURED 2026-10-29** (`2026-10-29-R1R2-PROBE-REPORT.md`): C1's 133 frames is REFUTED (256-261 measured), so the dialogue stall bound's headroom is about 1.15x, not 2.3x; W1 holds (a torn FIRST save leaves no save), and the "erased" page shows only once the write's first sector is complete.

# R1 + R2 recon, ANGLE 5: THE ADVERSARY (errors found in notes 01-04)

A NOTE, never truth (`ai-research-notes/00-READ-THIS-FIRST.md`; CLAUDE.md: agent output is a note). Written 2026-10-29 by
a read-only adversarial recon agent whose job was to REFUTE notes `01-game.md`, `02-host.md`, `03-code.md`, `04-record.md`.
NAME CLASH: "R1"/"R2" are the BACKLOG items (save/CONTINUE; a memory that survives a kill), never the step-5 grader
checks `R1.*` / `R5.*` in `ai_player/gates/rate_step5.py`.

What was run (nothing that starts an emulator, a gate, a driver or a test; nothing written in the repo, the learner clone
or `sandbox-pokebot/`; `git status` at the end equals the start: only the running lane's evidence edits):
- reads and greps of this checkout at HEAD `7d89fe07` and of the PINNED decomp `C:/Remote Projects/_decomp/pokeemerald`
  at `731ad5b`;
- read-only `gh api` reads of mGBA's source at tag `0.10.2` (the version string inside the shipped `mgba.dll`);
- a byte search of `sandbox-pokebot/mgba/mgba.dll`; a size listing of every profile's `current_save.sav`;
- an OFFLINE parse (no emulator) of the 18 committed fixture states and two profiles' `current_state.ss1`, with a
  script I wrote in my scratchpad (`r1r2recon/tools05/ss1_flags.py`, outside the repo; run with `py -3.12 -I -B`);
- `py -3.12 -B tools/decomp_lookup.py ask "save scum reload soft reset"`: NO PRIOR RULING OR FACT FOUND.

TAGS
- **VERIFIED-code**: read by me in this checkout or the framework (path:line). Prefixed `mgba:` = mGBA 0.10.2 source read
  through `gh api` (path:line at that tag). Prefixed `disk:` = a listing, byte search or offline parse on this PC today.
- **VERIFIED-decomp**: read by me in the pinned clone (path:line).
- **DOC**: quoted from a project document (path:line).
- **UNVERIFIED**: inference; each says what would prove it.
Agreement between notes is not proof, and neither is my agreement with a note: each CONFIRMED below rests on the
citation I read, not on the note.

---

## 0. The answers in brief (WRONG items first)

### 0.1 WRONG (each with the correct fact; most load-bearing first)

- **W1. [04 §0 item 17, §5.3 trap 5] "a torn write should leave the older save loadable" is WRONG for the FIRST save of a
  playthrough, and today every proof run starts with an empty cart** (no AI profile has ever written a save: §3, A2 row).
  `--state` and `--fresh` delete `current_save.sav` [VERIFIED-code ai_player/host/launcher.py:196-198]; all 18 committed
  fixtures hold gSaveFileStatus=0 (EMPTY), gSaveCounter=0, gDifferentSaveFile=1 [VERIFIED-code disk: offline parse,
  §6.1]. A torn first save leaves one ERROR slot beside an EMPTY one, which is SAVE_STATUS_CORRUPT: "The save file has
  been erased due to corruption or damage." and NEW GAME only [VERIFIED-decomp src/save.c:625-637;
  src/main_menu.c:649-653]. The same fact sinks the record's fault arm that 04 quotes without comment, "a fault arm that
  kills before the save must resume EARLIER" [DOC ai-research-notes/2026-10-19-backlog-round2/03-ai-player.md:38]:
  before the first save there is nothing to resume.
  The proof needs a first save S1, a party AND tile change, then S2; the arm kills after S2 (expect S2), the fault arm
  kills before S2 (expect S1) [UNVERIFIED: design consequence].
- **W2. [03 §3.3 step 7] "Scripted saves (special SaveGame) exist only in Battle Frontier lobbies" is WRONG.** Story-
  reachable callers: the Battle Tents of Slateport, Verdanturf and Fallarbor, Trainer Hill, the Lilycove Contest Lobby
  (link contests) and the Mystery Events house; also the cable club, the Berry Blender and secret bases [VERIFIED-decomp
  data/maps/SlateportCity_BattleTentLobby/scripts.inc:111-125; VerdanturfTown_BattleTentLobby/scripts.inc:149;
  FallarborTown_BattleTentLobby/scripts.inc:148; TrainerHill_Entrance/scripts.inc:175;
  LilycoveCity_ContestLobby/scripts.inc:618; SootopolisCity_MysteryEventsHouse_1F/scripts.inc:90]. Note 01 §1.7 is right.
  It runs in `SaveGameTask` [VERIFIED-decomp src/start_menu.c:896-930], which no eyes table names.
- **W3. [04 §0 item 12; §3.6 notes on D-5] "GAME_STAT_SAVED_GAME, which every in-game save increments" is WRONG.** One
  site increments it, `SaveDoSaveCallback` [VERIFIED-decomp src/start_menu.c:1090], used by the START-menu save and by
  `special SaveGame`. The story's own Hall of Fame autosave increments GAME_STAT_ENTERED_HOF instead [VERIFIED-decomp
  src/save.c:724-726, called from src/hall_of_fame.c:526]; SAVE_LINK saves (src/battle_pike.c:714, battle_pyramid.c:937,
  frontier_util.c:2432, contest_util.c:619, link.c:466) and the mystery-event, mystery-gift and clock-reset saves
  (src/mystery_event_menu.c:263, mystery_gift_menu.c:880, reset_rtc_screen.c:709) increment nothing [VERIFIED-decomp grep].
  A told-save grader must leave the HoF autosave out. Note 01 §6.2 is right.
- **W4. [03 §8 Q2-YES; 04 §4.3 YES row and §0 item 13] "the game's own [loss] counters roll back with the save", so
  MAX_LOSSES and "every grader that reads the GAME's loss counters" undercount after a reload: WRONG premise.** The game
  keeps no single-player loss or whiteout counter [VERIFIED-decomp include/constants/game_stat.h:4-55; only
  LINK_BATTLE_LOSSES]. MAX_LOSSES counts the navigator's per-process `battle_log` [VERIFIED-code ai_player/mode.py:626-638;
  brain/goals.py:525-528; brain/navigator.py:719, 1054], which an in-game soft reset does not touch; the step-5 graders
  count "the game's (gBattleOutcome LOST)" from the harness's live samples of gBattleOutcome [VERIFIED-code
  ai_player/gates/rate_step5.py:32-33; gates/play_harness.py:22-27, 129-132], which a reload does not erase either. What
  resets is everything across a PROCESS boundary (a relaunch starts both at zero); what rolls back is the SAVED stats:
  GAME_STAT_SHOPPED (L5.SHOPPED), TOTAL/WILD/TRAINER_BATTLES, POKEMON_CAPTURES, SAVED_GAME [VERIFIED-code
  gates/play_harness.py:64-69]. Note 01 §6.5 states it correctly.
- **W5. [02 §2.4 step 1] "START → start menu → 'SAVE' (the eyes already name it: START_MENU_ACTIONS[5])" is WRONG as a
  build premise.** The table names it, but the view is built only while `StartMenuTask` runs [VERIFIED-code
  ai_player/host/eyes.py:502-505; eyes/screens.py:576-582], i.e. the menu's build frames; while the menu takes input the
  task is `Task_ShowStartMenu` [VERIFIED-decomp src/start_menu.c:527-531, 561-579], and a reopened menu never runs
  StartMenuTask [VERIFIED-decomp src/field_screen_effect.c:424-431]. The project measured it [VERIFIED-code
  ai_player/gates/make_step41_fixtures.py:171-174]. Notes 01 x1 and 03 §4.2 are right.
- **W6. [04 §0 item 5] own party PIDs "allowed", quoting "a person knows which of their own Pokemon they sent out" as
  [DOC 06:9434]: WRONG attribution.** Those words are a code comment [VERIFIED-code ai_player/eyes/observation.py:275-276];
  06:9434 (RULING 40) lists only what is NOT allowed, and no 06 entry rules own PIDs allowed [VERIFIED-code grep of 06].
  PID-as-identity rests on CLAUDE.md rule 3 and the code: a technical convention, fine for L3, but not a user ruling.
- **W7. [04 §0 item 6] "'Development may use saves' [DOC DD:381; 06:9254]": WRONG attribution.** The user's answer is only
  "Yes, for the official acceptance runs (including naming and clock setting)" [DOC 06-DECISIONS-LOG.md:9254]; the phrase
  exists only in the design draft's applied table [DOC ai-research-notes/2026-10-07-ai-player-v1-DESIGN-DRAFT.md:381] and
  nowhere in 06 [VERIFIED-code grep].
- **W8. [04 §0 item 4] "a state-write is 'a documented last-resort fallback' [DOC CLAUDE.md:256-258]" applied to the AI:
  WRONG scope.** That line is the STORY-BOT craft directive. The AI has no state-write fallback in play: the gate bans
  write_bytes, every load and reset [VERIFIED-code ai_player/gates/check_purity.py:536-550] and the instrument counts any
  load [VERIFIED-code ai_player/host/attribution.py:20-26, 178-182]. Launcher file handling BETWEEN processes is a
  different thing (02 A12).
- **W9. [03 §0 (d), §5] "A memory home outside the run directory means either widening FILE_WRITERS (a gate change) or the
  LAUNCHER copying files": WRONG as stated.** FILE_WRITERS pins which MODULES may write; its path text is a description
  [VERIFIED-code ai_player/gates/check_purity.py:598-603]; `RecordFile` writes into whatever directory it is given
  [VERIFIED-code ai_player/runlog.py:55-67, 76-84]. A persistent memory folder needs option plumbing, not a gate widening
  [UNVERIFIED that no other rule objects: plant a RecordFile at a non-run path in a COPY of the package, run
  check_purity.py on the copy]. 04's D-2 "RecordFile writes only <run_dir>/<name>" is true of today's call sites
  (ai_player/mode.py:294, 298), not of RecordFile.
- **W10. [02 A14, §4.6] "16 sites in 13 gate files hardcode <repo>/sandbox-pokebot": WRONG count** at 7d89fe07: 20 lines
  in 16 files; it missed gates/test_kb2.py:105-106, gates/test_world.py:138 and gates/warp_reads.py:204 [VERIFIED-code grep
  `"sandbox-pokebot"` over ai_player/gates/*.py]. "12 gates use resolve_build_root": CONFIRMED (12 files).
- **W11. [02 A15] "the frame counter restarts at 0 on every cold boot (so on every CONTINUE)": the parenthesis is WRONG**
  for a CONTINUE after an in-game soft reset (the credits' own reset, src/credits.c:694-697 VERIFIED-decomp; a person-like
  reload if ever allowed): mGBA's BIOS soft reset and RAM reset never touch it [VERIFIED-code mgba:src/gba/bios.c:37-60
  (_SoftReset), 62-188 (_RegisterRamReset), 447-451; the file never names frameCounter]; only GBAVideoReset zeroes it
  [VERIFIED-code mgba:src/gba/video.c:79]. 02's own M5 says this.

### 0.2 CLOSED: items the notes left UNVERIFIED that I settled without a live probe
- **C1. The mGBA flash write spans at least ~133 emulated frames, not one.** mGBA keeps each programmed byte busy for
  FLASH_PROGRAM_CYCLES = 650 cycles (30,000 per sector erase) and answers 0x5F meanwhile [VERIFIED-code
  mgba:src/gba/savedata.c:28-29, 378, 389-393, 771-773]; the game polls every byte until it reads back [VERIFIED-decomp
  src/agb_flash_mx.c:156-193; src/agb_flash_1m.c:51-84]. 14 x 4,096 bytes x 650 / 280,896 cycles a frame = 132.7 frames
  before any overhead [arithmetic; the exact count is UNVERIFIED-live, M2]. So 02's KM arm ("only if step 6 spans
  frames") is real and must be run; 01 a6's "a hundred frames or more" holds; at x1 the window is at least ~2.2 s.
- **C2. `sSaveDialogCallback` IS in the symbol table** (0x0203761C), with gMenuCallback, gSaveFileStatus, gSaveCounter,
  gLastWrittenSector and gDifferentSaveFile [VERIFIED-code sandbox-pokebot/modules/data/symbols/pokeemerald.sym:228,
  283-288, 978, 1011, 1015, 1019]. Resolves 03 U8; the bot already reads it [VERIFIED-code
  sandbox-pokebot/modules/modes/util/higher_level_actions.py:888-910].
- **C3. The shipped mgba.dll uses the mapped-file VFS:** it contains "VFileOpenFD" and none of "VFileFOpen", "r+b",
  "a+b", "w+b", the literals of the stdio path [VERIFIED-code disk: byte search of sandbox-pokebot/mgba/mgba.dll;
  mgba:src/util/vfs.c:17-41]. Strengthens 02 A1, which rested on CMakeLists and imports.
- **C4. The emulator frame counter is 0 at every cold boot and restored by a .ss1 load** [VERIFIED-code
  mgba:src/gba/video.c:79, 354; sandbox-pokebot/modules/libmgba.py:137, 141-146]. Resolves 03 §2.3 / U3.
- **C5. Every committed fixture is a raw mGBA 0.10.2 state** (0x61000 bytes, version 0x01000007 =
  mgba:src/gba/serialize.c:17-18, no extdata, so no cartridge data) **holding gSaveFileStatus=0, gSaveCounter=0,
  gLastWrittenSector=0, gDifferentSaveFile=1** [VERIFIED-code disk: offline parse, §6.1]. So the first save from any
  fixture asks ONE question then SAVING [VERIFIED-decomp src/start_menu.c:1008-1018], erases sectors 28-31 and writes
  counter 1 into the SECOND slot (sectors 14-27, id 0 at sector 15) [VERIFIED-decomp src/start_menu.c:1093-1096;
  src/save.c:139-209, 752-760]; the second save asks "There is already a saved file" (YES by default).
- **C6. 12 of the 14 AI-owned profiles hold a current_state.ss1 today** (all but ai-step01-http and ai-step01-signal):
  the stale-state hazard (01 x3, 02 A7, 03 H3, 04 trap 1) is live for any no-flag launch [VERIFIED-code disk: listing].

### 0.3 CONFIRMED (the load-bearing claims that survived)
- **01:** the START gate (a1); items and the remembered cursor (a2); texts and the self-closing box (a3); the three dialog
  shapes (a4, but see §2: the deciding values are RAM, carried by a .ss1); NO/B writes nothing (a5); one synchronous write
  with VBlank running (a6); CONTINUE iff the boot read was OK or ERROR (b3); the CONTINUE window (b4); the error pages
  (b5); one save read per boot (c6); two rotating slots, an in-order cut leaves ERROR (d1-d3); a soft reset cannot cut the
  write (d4); the scripted-save list (e3); GAME_STAT_SAVED_GAME's scope (§6.2); the eyes gap (x1); the stale .ss1 (x3).
- **02:** the save is a writable file mapping (A1, plus C3); the flush comes 16 frames after the last write, by
  FlushViewOfFile, with the `saves/` copy on that frame (A2); `.ss1` only at a clean close (A3); a torn slot falls back and
  a MIXED slot can load (A5; refined in §7); `.ss1` carries no cartridge data and is build-tied (A6); the split-brain
  logic (A7); the launcher facts (A8-A13); RecordFile's open-append-close (A15); the harness boots `is_test_run=True`.
- **03:** `_Memory`'s 38 fields and "not carried"; the world memory by last line with no guard; frame stamps; no START in
  play; play_intro picks NEW GAME by name; the start-menu and save-dialog eyes gaps; the purity names; the deadline guard
  has no brain hook; PIDs, and boxes without species; the 10.7 MB / 34-line world file (re-measured).
- **04:** no ruling on saving, CONTINUE or save-scum (06 grep, RULINGS.md grep, the lookup tool); the backlog items are
  candidates (BL:28); RULING 39's quote; R5's D1/D8; traps 1-4 and 7; the 06/08 quotes I spot-checked.

### 0.4 UNCHECKABLE without a live probe
- A process kill keeps the mapped pages (02 A4): 02's M1, WITH the KM arm (kill during "SAVING…") added.
- The exact write length, and whether `advance`'s 300-frame stall limit trips on it: M2 plus a live save under `advance`.
- The split-brain (02 A7: M4); soft-reset purity (02 M5).
- The words of the save-file error page as the eyes read them (N2): a TRUNC-arm boot logging `screen.text` every frame.
- The MIXED power-cut slot (02 A5) is checkable OFFLINE (a port of GetSaveValidStatus over synthetic images); §7 shows
  only "every other sector" patterns can complete a slot.

### 0.5 What NONE of the notes covered (a build needs each)
- **N1. During the ≥133-frame write the eyes show controls locked, no text, no menu** [VERIFIED-code
  ai_player/host/eyes.py:446-452, 702-739; hands/dialogue.py:103-104]: the skill cannot tell "saving" from "a scene
  plays"; `advance` has under 2.3x headroom before its 300-frame stall [VERIFIED-code hands/dialogue.py:62]; "saved" can
  be READ only while "{PLAYER} saved the game." prints. A skill that declares "saved" any earlier creates the silent
  fallback 01 d5 fears (rule 7: instrument the action).
- **N2. The save-file error pages print on window 7 = printer 7** [VERIFIED-decomp src/main_menu.c:2116-2119;
  src/text.c:297]; once printed the eyes return only printer 0's last message [VERIFIED-code
  ai_player/host/eyes.py:732-739], None at a fresh boot; the CONTINUE window prints instantly [VERIFIED-decomp
  src/main_menu.c:2138-2187, TEXT_SKIP_DRAW]. ⇒ Today the AI cannot notice, as a person would, that it continued an OLDER
  save or that its save was erased.
- **N3. The dialog shape and the slot written follow RAM carried in a .ss1** (gSaveFileStatus, gDifferentSaveFile,
  gSaveCounter, gLastWrittenSector: C5), not the .sav on disk. A launcher that swaps or restores a .sav must drop the
  .ss1 too (02 A7 is one case of this).
- **N4. A run can end INSIDE a save.** The soft wall-clock guard [VERIFIED-code ai_player/host/session.py:305-310], the
  brain's frame budget [VERIFIED-code ai_player/mode.py:965-978] and the hard kill do not wait for the dialog. A clean
  end then writes a .ss1 with mid-write RAM [VERIFIED-code sandbox-pokebot/modules/libmgba.py:159-160, 231-241] whose
  resume would finish the write, while a CONTINUE start (the .ss1 dropped) meets a torn slot: the previous save, or
  "erased" for a first save. The skill needs a frames-left gate; a planned stop must wait for the box to close.
- **N5. The launcher always runs `-s 0`** [VERIFIED-code ai_player/host/launcher.py:216]: wall-time exposure measured
  today does not transfer to the deploy's x1; state every window in frames.
- **N6. GAME_STAT_SAVED_GAME rises BEFORE the write and stays risen in RAM if the write fails or is torn**
  [VERIFIED-decomp src/start_menu.c:1090 vs 1093-1101]: a second-path grader reads it from the slot CONTINUE loaded
  (XOR the key, gates/play_harness.py:64-65), never from RAM before the kill.
- **N7. The record's proof wording is unrunnable from a fixture or a New Game** (W1, second half).

### 0.6 Conflicts between the notes that code cannot settle
- The memory stamp: 03 says it needs a 06 decision (fairness, RULING 40); 04 says it is Claude's technical call
  (RULING 39); 01 calls it a design question. A host-only bookkeeping stamp never read by deciding code is the
  technical reading; record the boundary in 06 either way.
- "No save-scum": 03 says impossible by construction (one button per pad action); 04 says a gate is needed. The CONTROLLER
  allows overlapping holds if two `hold` generators are stepped together [VERIFIED-code ai_player/host/controller.py:67-82;
  hands/pad.py:91-121], so the safety is a convention; CLAUDE.md rule 6 puts it in a gate.
- 04's kill sweep (0, 1, 15, 60, 300 frames after "saved the game.") never kills during the write, the one window where a
  process kill should tear the save (C1).

### 0.7 The two open user questions: what these findings add (nothing decided)
- **Q1, when the AI saves:** every answer pays the dialog plus ≥133 frames of write, needs a frames-left gate (N4) and the
  E1/E2 eyes first. "Only before a planned stop" is the answer most exposed to N4: the stop is when the deadline lands.
- **Q2, reload to undo a loss:** under YES, losses do not "roll back with the game" (W4): the per-process battle_log and
  the graders' live samples survive an in-game soft reset and reset only across processes. Under NO, a kill during
  "SAVING…" restores the PREVIOUS save (an involuntary undo, 01 q1) or, on the first save, leaves no save at all (W1).

---

## 1. How the checks were chosen
For each note I took the claims a build would rest on: the save flow's texts and frames, when the .sav reaches disk,
what CONTINUE restores, what the AI's memory holds and loses, and which rulings bind. I re-read each citation; where a
note cited nothing checkable I went to the source. A claim I could not check without a live run is listed in §8 with
the probe that would settle it.

---

## 2. Note 01 (the game), claim by claim

| claim | verdict | evidence |
|---|---|---|
| a1 START only on the free overworld; Mach top gear blocks it; earlier events win the frame | CONFIRMED | VERIFIED-decomp src/field_control_avatar.c:89-107, 133-187; src/bike.c:111, 1022-1035 |
| a2 SAVE's row moves with the flags; the cursor index is remembered | CONFIRMED | VERIFIED-decomp src/start_menu.c:83, 511, 598-604 |
| a3 texts in order; the box closes itself after SE_SAVE plus 60 frames, at once while A is HELD | CONFIRMED | VERIFIED-decomp data/text/save.inc:2-14; src/start_menu.c:947-962, 1086-1134 |
| a4 shape depends "on the CARTRIDGE, not on the place" | CONFIRMED with a correction | the deciding values are RAM: gSaveFileStatus (set only by LoadGameSave, src/save.c:872-891) and gDifferentSaveFile (src/new_game.c:139-154; start_menu.c:1093-1096). A .ss1 carries both from the session that captured it (C5; N3). 01 §1.4 says it precisely; the §0 summary does not |
| a5 NO or B writes nothing, back to the start menu | CONFIRMED | VERIFIED-decomp src/start_menu.c:817-838, 1024-1028, 1070-1074 |
| a6 one synchronous call after "SAVING…" printed; VBlank keeps running | CONFIRMED | VERIFIED-decomp src/start_menu.c:884-894, 1086-1110; src/agb_flash.c:82-104 (IME=1 while a byte is awaited) |
| a6 frames: "UNVERIFIED, roughly a hundred or more" | CLOSED: ≥133 | C1 |
| b3 CONTINUE iff OK or ERROR | CONFIRMED | VERIFIED-decomp src/main_menu.c:625-692 |
| b4 the CONTINUE window shows no location; b5 the error pages | CONFIRMED | VERIFIED-decomp src/main_menu.c:2127-2187, 649-659, 694-703 |
| c6 the save is read once per boot | CONFIRMED (one more caller: ReloadSave after a LINK error, src/reload_save.c:25 via src/link.c:1711; not a single-player path) | VERIFIED-decomp src/intro.c:1147-1159 |
| c3 the RNG is not re-seeded on CONTINUE | CONFIRMED (seeded only by naming in a New Game, link and BUGFIX paths) | VERIFIED-decomp src/naming_screen.c:701; src/main.c:211, 234; grep `SeedRng(` |
| d1-d3 two rotating slots; an in-order cut leaves the new slot ERROR | CONFIRMED (re-derived in §7) | VERIFIED-decomp src/save.c:139-209, 486-513, 515-638 |
| d4 a soft reset cannot cut the write | CONFIRMED | VERIFIED-decomp src/main.c:131-167 |
| d5 "a kill that loses a write the emulator never flushed fails SILENTLY" | CONFIRMED as a conditional, premise not expected for a process kill | the bytes go into the OS file mapping as written (02 A1, C3); a kill DURING the write gives the "corrupted" or "erased" page, not silence; silence needs a power cut or OS crash dropping every new page, or a skill that calls a save done before "saved the game." (N1) [UNVERIFIED-live: M1 + KM] |
| e2/e3 no SAVE in the Safari Zone, link rooms, Pike; scripted saves at tents, lobbies, Trainer Hill, link | CONFIRMED | §0 W2 citations |
| §6.2 GAME_STAT_SAVED_GAME: START-menu and scripted saves only | CONFIRMED | VERIFIED-decomp src/start_menu.c:1090 (the only increment, grep) |
| §6.5 no whiteout counter; saved counters roll back | CONFIRMED | VERIFIED-decomp include/constants/game_stat.h:4-55 |
| x1 the eyes see no start-menu cursor and no save yes/no | CONFIRMED | VERIFIED-code ai_player/host/eyes.py:217-225, 502-505; eyes/screens.py:576-582; VERIFIED-decomp src/start_menu.c:527-591, 1003-1005; src/menu.c:464-472 (CreateYesNoMenu: no task) |
| x3 the wrapper loads current_state.ss1 whenever it exists | CONFIRMED, live today in 12 of 14 AI profiles (C6) | VERIFIED-code sandbox-pokebot/modules/libmgba.py:141-146 |

---

## 3. Note 02 (the emulator and the host), claim by claim

| claim | verdict | evidence |
|---|---|---|
| A1 the .sav is opened r+ and mapped writable; each flash byte lands in the file's pages | CONFIRMED | VERIFIED-code sandbox-pokebot/modules/libmgba.py:124-137; mgba/vfs.py:90-109; mgba:src/gba/savedata.c:46-63 (mapMode MAP_WRITE), 261-288; mgba:src/util/vfs/vfs-fd.c:157-182 (the Windows map); C3 |
| A2 flush 16 frames after the last write, FlushViewOfFile only, RTC footer, savedataUpdated on that frame | CONFIRMED | VERIFIED-code mgba:include/mgba/internal/defines.h:9-29; mgba:src/gba/savedata.c:571-615; mgba:src/util/vfs/vfs-fd.c:246-281 (`_vfdSync`: FlushViewOfFile at 278, FlushFileBuffers only without a buffer at 280); mgba:src/gba/gba.c:887-922; libmgba.py:161, 243-256 |
| A2 495 x 131,072 and 13 x 131,088 byte .sav files; no AI profile ever synced | CONFIRMED | VERIFIED-code disk: listing (same counts; all 14 AI profiles 131,072 with an empty `saves/`) |
| A3 the .ss1 only at a clean close | CONFIRMED | VERIFIED-code libmgba.py:159-160, 201-241 |
| A4 a process kill keeps a save reported done | logic CONFIRMED; UNVERIFIED-live | M1 |
| A5 torn slot falls back; a MIXED slot can load (no counter check) | CONFIRMED; refined in §7 | VERIFIED-decomp src/save.c:515-570 |
| A6 .ss1 = flags 0 (no cartridge data); refused if too new / other game; silent on refusal | CONFIRMED (version 7, not the header comment's 6) | VERIFIED-code sandbox-pokebot/mgba/core.py:236-248; mgba:src/core/serialize.c:401, 505-535; mgba:src/gba/serialize.c:17-18, 85-100; mgba:src/gba/core.c:1199-1213 |
| A7 split-brain after a stale .ss1 | logic CONFIRMED; UNVERIFIED-live (M4) | VERIFIED-decomp src/save.c:139-209, 587-604 |
| A8-A13 the run command, profile files, endings, no CONTINUE path, purity, the locator | CONFIRMED | VERIFIED-code ai_player/__main__.py:55-64; host/launcher.py:81-118, 179-216, 351-431; host/lifecycle.py:138-185; host/attribution.py:891-907 |
| A14 "16 sites in 13 files" | WRONG (W10) | — |
| A15 frame counter "restarts at 0 ... so on every CONTINUE" | WRONG parenthesis (W11) | — |
| A15 RecordFile survives a kill line by line; the play loop cannot fsync | CONFIRMED | VERIFIED-code ai_player/runlog.py:55-89; gates/check_purity.py:598-603 |
| §2.2 the harness boots `is_test_run=True` (no .sav file) | CONFIRMED | VERIFIED-code ai_player/gates/probe_eyes.py:197 |
| §2.4 step 1 "the eyes already name it" | WRONG as a premise (W5) | — |
| §2.4 step 6 / §2.5 KM "only if step 6 spans frames" | CLOSED: it spans ≥133 frames, KM is required | C1 |
| §2.4 step 8 the flush lands before the box closes | CONFIRMED by arithmetic (≥17 characters of "{PLAYER} saved the game." at one or more frames each, plus SE_SAVE, plus 60 or the A hold, vs 16) | VERIFIED-decomp src/start_menu.c:1102-1134; UNVERIFIED-live (M2) |
| §5.2 probe child A on route101_south.ss1 | CONFIRMED usable, with expectations: shape A, counter 1 in slot 2; NOSAVE reads EMPTY with no CONTINUE; KM on the FIRST save gives "erased", not a fallback | C5; W1 |

---

## 4. Note 03 (our AI code), claim by claim

| claim | verdict | evidence |
|---|---|---|
| (a) `_Memory` has 38 fields; "this goal manager's own memory is not" carried | CONFIRMED | VERIFIED-code ai_player/brain/goals.py:407-496, 449 |
| (a) only the world memory crosses sessions, by the last line, `json.loads` unguarded | CONFIRMED | VERIFIED-code ai_player/world/memory.py:801-822, 864-871; mode.py:298, 389-393, 943-963 |
| (a) every stamp is the emulator frame; "restarts at 0 on CONTINUE: UNVERIFIED" | CONFIRMED; CLOSED by C4 | VERIFIED-code ai_player/host/eyes.py:355; world/memory.py:115, 778-792 |
| (b) no START in play; play_intro picks NEW GAME by name | CONFIRMED (menus.py:262 is a fault arm's keyboard START, immaterial) | VERIFIED-code ai_player/skills/intro.py:9, 81-82, 113-115; hands/menus.py:202, 262 |
| (c) start menu named but no view while it takes input; save yes/no and texts invisible after printing; info window instant | CONFIRMED | VERIFIED-code ai_player/eyes/view.py:409-416; host/eyes.py:446-452, 702-739; VERIFIED-decomp src/start_menu.c:1332-1392 (TEXT_SKIP_DRAW) |
| (c) `screens.py:228`'s comment "(runs HandleStartMenuInput)" is wrong | CONFIRMED | VERIFIED-decomp src/start_menu.c:527-531 |
| (c) U8 "sSaveDialogCallback in the symbol table: UNVERIFIED" | CLOSED: it is | C2 |
| (d) the purity names; only controller.py names the button functions | CONFIRMED | VERIFIED-code ai_player/gates/check_purity.py:536-556 |
| (d) save-scum out of reach "BY CONSTRUCTION" | CONFIRMED for the pad only; the controller permits overlapping holds | VERIFIED-code ai_player/host/controller.py:67-82; hands/pad.py:91-121 |
| (d) a memory home outside the run dir needs a gate change or launcher copies | WRONG as stated (W9) | — |
| (e) R5's settle, margin 2 frames, docstring names R1 | CONFIRMED | VERIFIED-code ai_player/mode.py:130, 137, 676-707 |
| (e) the deadline guard ends the run with no brain hook | CONFIRMED | VERIFIED-code ai_player/host/session.py:141-147, 305-310 |
| (f) PIDs for the party; boxes PID without species | CONFIRMED | VERIFIED-code ai_player/eyes/observation.py:209-239 |
| §3.3 step 7 scripted saves only in Frontier lobbies | WRONG (W2) | — |
| §3.5 H1 a .sav with no .ss1 walks into NEW GAME; NEW GAME gives no prompt | CONFIRMED | VERIFIED-code ai_player/mode.py:458-461, 488-495; VERIFIED-decomp src/main_menu.c:1058-1063 |
| §8 Q2-YES "MAX_LOSSES must count reloaded losses: the game's own counters roll back" | WRONG premise (W4) | — |
| world.jsonl 10,739,541 bytes / 34 lines | CONFIRMED | VERIFIED-code disk: wc |

---

## 5. Note 04 (the record), claim by claim

| claim | verdict | evidence |
|---|---|---|
| 1 no user ruling on saving, CONTINUE or save-scum | CONFIRMED | VERIFIED-code grep of 06 (save-scum, soft reset, reload, in-game save) and RULINGS.md; lookup tool exit "NO PRIOR RULING OR FACT FOUND" |
| 2 the backlog's R1 + R2 is a candidate; the questions asked 2026-10-28 5:27 PM | CONFIRMED | DOC improvement-backlog.md:28; 04-HANDOFF.md:61; 07-CHANGELOG.md:39032 |
| 3 RULING 39's split | quote CONFIRMED (DOC 06:9392-9393); the split is an inference | — |
| 4 "a state-write is a documented last-resort fallback" | WRONG scope (W8) | — |
| 5 own PIDs allowed, quoted from 06:9434 | WRONG attribution (W6) | — |
| 6 "Development may use saves" from 06:9254 | WRONG attribution (W7) | — |
| 8 R5 D1/D8; the HoF autosave then soft reset then CONTINUE | CONFIRMED | DOC 06:9858, 9864; VERIFIED-decomp src/hall_of_fame.c:526; src/credits.c:694-697; src/post_battle_event_funcs.c:36-41 |
| 12 / D-5 GAME_STAT_SAVED_GAME "every in-game save" | WRONG (W3) | — |
| 13 / §4.3 "graders that read the GAME's loss counters undercount" | WRONG premise (W4); also "a quit to the title" is not a separate mechanism: the only in-game ways back to the title are the soft reset and the credits (VERIFIED-decomp src/main.c:131-142; src/credits.c:694-697) | — |
| 17 / trap 5 "a torn write should leave the older save" | WRONG for the first save (W1); its kill sweep misses the write window (0.6) | — |
| traps 1-4, 7 (auto-loaded .ss1, NEW GAME pick, vacuity, continue warps, one process per profile) | CONFIRMED | VERIFIED-code libmgba.py:141-146; skills/intro.py:113-115; VERIFIED-decomp src/start_menu.c:1297 and src/save.c:1003 are LINK saves only, never START > SAVE (src/start_menu.c:1086-1110 sets no warp) |
| 16 held-out seeds registered first, a crash spends them | CONFIRMED | VERIFIED-code ai_player/gates/ledger.py:10-36 |
| quotes from 08 (8437, 21146, 4072) | CONFIRMED (spot-check) | DOC 08-MISTAKES.md at those lines |

---

## 6. Evidence produced for this note

### 6.1 The offline parse of the fixture states (read-only)
- Method: `r1r2recon/tools05/ss1_flags.py` reads a raw mGBA state (or the `gbAs` chunk of a PNG state), takes IWRAM at
  state offset 0x19000 and WRAM at 0x21000 [VERIFIED-code mgba:include/mgba/internal/gba/serialize.h:240-242], and reads
  the four symbols at their addresses [VERIFIED-code sandbox-pokebot/modules/data/symbols/pokeemerald.sym:228, 1011,
  1015, 1019].
- Result for all 18 files in `ai_player/gates/fixtures/*.ss1`: 397,312 bytes each, magic 0x01000007, no extdata;
  gSaveFileStatus=0, gSaveCounter=0, gLastWrittenSector=0, gDifferentSaveFile=1.
- Controls on the method: `sandbox-pokebot/profiles/ai-step5-play/current_state.ss1` (a PNG state) gives the same four
  values; `profiles/ai-step0-fresh/current_state.ss1` gives gDifferentSaveFile=0, so the reader distinguishes the flag
  [VERIFIED-code disk]. That the addresses match this ROM build is UNVERIFIED beyond the framework using the same table.

### 6.2 What the first and second saves from a fixture do (decomp, given 6.1)
- First save: EMPTY + gDifferentSaveFile → SaveSavingMessageCallback with no second question (start_menu.c:1008-1018);
  SAVE_OVERWRITE_DIFFERENT_FILE erases sectors 28-31, then gLastWrittenSector 0 → 1, gSaveCounter 0 → 1, slot 1 % 2 = the
  second slot, sector of id i = 14 + (i + 1) % 14 (save.c:139-209, 752-760); gDifferentSaveFile cleared (1093-1096).
- Second save in the same session: gSaveFileStatus is still EMPTY in RAM, gDifferentSaveFile FALSE → "There is already a
  saved file. / Is it okay to overwrite it?" with YES first (start_menu.c:1008-1013, 1035-1047, 1056-1061).
- After a cold boot with that cart: status OK, CONTINUE offered, every save asks "already a saved file".

### 6.3 mGBA reads (tag 0.10.2, read-only `gh api`)
savedata.c:28-29 (erase 30,000 / program 650 cycles), 46-63, 261-288, 368-393, 571-615, 763-774; defines.h:9-29;
gba.c:887-922; vfs-fd.c:157-197, 246-281; vfs.c:17-41; video.c:79, 187, 339, 354; bios.c:37-60, 62-188, 447-451 (no frameCounter anywhere in it);
serialize.c (gba) 17-18, 85-100; serialize.c (core) 401, 505-535; core.c (gba) 1199-1213; serialize.h 240-242.

---

## 7. Two derivations the notes asserted or left open

### 7.1 An in-order cut always leaves the new slot ERROR (01 d3, checked)
The written slot held the save from two saves ago, rotated 2 behind (save.c:153-163, 185-187). Writing ids 0..k
overwrites old ids 2..k+2 (mod 14); the slot then lacks ids k+1 and k+2 (id 13 for k = 12). A sector cut mid-program
has an erased footer (signature 0xFFFFFFFF) and counts as missing. So any cut gives ERROR (the "corrupted" page and the
previous save) or, with no previous save, CORRUPT (the "erased" page). A process kill on a mapped file gives exactly
this in-order prefix [UNVERIFIED-live: M1 + KM].

### 7.2 Which power-cut patterns can load a MIXED slot (02 A5, refined)
If only some 4 KB pages of the new save reach the disk, let Q be the written positions counted from the old rotation.
New ids are q - 2 (q in Q), old ids are q (q not in Q). All 14 ids are present iff q in Q implies q - 2 in Q, i.e. Q is
a union of the two cycles of "+2 mod 14": none, the 7 "even" positions, the 7 "odd" ones, or all. So a mixed slot
loads only when exactly every other sector arrived; it would then combine 7 sectors of the new save with 7 of the save
from two saves ago (for example SaveBlock2 from one, the party from the other) [derivation from VERIFIED-decomp
src/save.c:177-209, 515-570; UNVERIFIED: an offline port over synthetic images would prove it].

---

## 8. Probes that would settle what is still open (none was run)
- **M1 + KM (02 §5.2, extended):** kill at K-mid points INSIDE "SAVING…" (for example 10, 60, 120 frames after its text
  finished) as well as at K0/K1/K2. From a fixture the FIRST save's KM must give "erased" and no CONTINUE; a SECOND
  save's KM must give "corrupted" and the first save. A FILE parse and the game's CONTINUE judge each arm.
- **M2:** per frame, test-side: `sSaveDialogCallback`'s name (C2), printer 0's state, `GAME_STAT_SAVED_GAME`, the
  newest slot in `read_save_data()`; gives the write length and the stall headroom (N1).
- **N2 reader check:** boot a TRUNC profile and log `screen.text` and `screen.wait_reason` per frame through the error
  page: predicted text only while printer 7 prints, then None.
- **W9 gate check:** a COPY of the package with a RecordFile under a non-run directory, then `check_purity.py` on it.
- **§7.2 offline:** port GetSaveValidStatus (save.c:515-638), feed two real consecutive saves with every subset of the
  newer slot's sectors laid over the older image; expect OK only for the two parity halves.


---

## APPENDIX. The offline state parser, VERBATIM (session scratch `s53/r1r2recon/tools05/ss1_flags.py`, sha256 `41576d4eed32e824`, committed here by the orchestrating session so section 6.1's parse can be re-run: `py -3.12 -I -B ss1_flags.py <state files>`)

```python
"""Read-only: parse mGBA PNG states (.ss1) and print the save-related RAM flags of pokeemerald.

Addresses from sandbox-pokebot/modules/data/symbols/pokeemerald.sym; state layout from mGBA 0.10.2
include/mgba/internal/gba/serialize.h (IWRAM @0x19000, WRAM @0x21000, total 0x61000).
Nothing is written; each path given on the command line is only read.
"""
import pathlib
import struct
import sys
import zlib

IWRAM_OFF, WRAM_OFF = 0x19000, 0x21000
SYMS = {  # name: (address, size)
    "gSaveFileStatus": (0x03006210, 2),
    "gSaveCounter": (0x03006200, 4),
    "gLastWrittenSector": (0x030061F0, 2),
    "gDifferentSaveFile": (0x020322D4, 1),
}


def chunks(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    i = 8
    while i < len(data):
        n = struct.unpack(">I", data[i:i + 4])[0]
        kind = data[i + 4:i + 8]
        yield kind, data[i + 8:i + 8 + n]
        i += 12 + n


def ram(state, addr, size):
    if 0x03000000 <= addr < 0x03008000:
        off = IWRAM_OFF + (addr - 0x03000000)
    else:
        off = WRAM_OFF + (addr - 0x02000000)
    return int.from_bytes(state[off:off + size], "little")


def main(paths):
    for path in paths:
        data = pathlib.Path(path).read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            # a RAW mGBA state (versionMagic first, 0x61000 bytes, extdata would follow)
            kinds = [b"raw:" + data[:4].hex().encode() + (b"+extdata" if len(data) > 0x61000 else b"")]
            state = data[:0x61000]
        else:
            kinds = [k for k, _ in chunks(data)]
            raw = [d for k, d in chunks(data) if k == b"gbAs"]
            if not raw:
                print(path, "no gbAs chunk", kinds)
                continue
            state = zlib.decompress(raw[0])
        vals = {name: ram(state, a, s) for name, (a, s) in SYMS.items()}
        print(f"{pathlib.Path(path).name}: state={len(state):#x} gbAx={'yes' if b'gbAx' in kinds else 'no'} "
              + " ".join(f"{k}={v}" for k, v in vals.items()))


if __name__ == "__main__":
    main(sys.argv[1:])
```
