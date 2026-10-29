> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1r2recon/02-host.md` (sha256 `69a118b9318d91af`). Backlog R1 + R2's recon (save, CONTINUE, a memory that survives a kill), angle 2, THE EMULATOR AND THE HOST: a read-only Claude subagent's NOTE, never truth (the authoritative docs and the code win). Nothing in it was measured live. R1 + R2's build waits for the user's two save answers (`04` item 4).
> ⚠ **The adversary found WRONG here** (`2026-10-29-R1R2-recon-refute.md` section 0.1): W5, section 2.4 step 1's "the eyes already name it" (the start menu has a view only while it is being built, never while it takes input); W10, A14's count (20 lines in 16 files, not 16 sites in 13); W11, A15's "(so on every CONTINUE)" (an in-game soft reset keeps mGBA's frame counter). Closed: section 2.4 step 6 spans about 133 frames or more, so the kill-during-SAVING arm (KM) is required (its C1). A4, that a process kill keeps a finished save, is logic only until probe M1 runs.

# R1 + R2 recon, angle 2: THE EMULATOR AND THE HOST (2026-10-29)

A NOTE, never truth (`ai-research-notes/00-READ-THIS-FIRST.md`). Read-only recon for backlog items R1 + R2 (with DP1, DP2,
L3 (a)-(b) and the "Folded into" R1 + R2 + DP4 line) of `PROJECT KNOWLEDGE/ai-research-notes/2026-10-18-improvement-backlog.md`
(lines 290-294, 378-379, 390-399). NAME CLASH: "R1"/"R2" here are BACKLOG items, not the step-5 grader's `R5.<NAME>` / `R1.*`
checks in `ai_player/gates/rate_step5.py`.

What was run: nothing that starts an emulator, a gate, a driver or a test. Only: file reads and greps; read-only `gh api`
reads of mGBA's source at git tag `0.10.2` (piped through grep/sed, nothing saved); byte searches of the shipped DLL and of
the committed fixtures; read-only listings of profile folders and file sizes; two `tools/decomp_lookup.py ask` queries
("save scum reload save": NO PRIOR RULING OR FACT FOUND; "current_save.sav": only `06:612-622`, separate profiles per lane).
No file was written except this note.

TAGS
- **VERIFIED-code**: read in this repo (path:line; `sandbox-pokebot/` paths are the framework, `ai_player/` the AI).
- **VERIFIED-decomp**: read in the pinned clone `C:/Remote Projects/_decomp/pokeemerald` at `731ad5bf` (path:line).
- **VERIFIED-mgba**: read in mGBA's source at tag `0.10.2` through `gh api repos/mgba-emu/mgba/contents/<path>?ref=0.10.2`.
  The shipped `sandbox-pokebot/mgba/mgba.dll` contains the string `0.10.2` and imports `CreateFileMappingW`, `MapViewOfFile`,
  `FlushViewOfFile`, `FlushFileBuffers` and `UnmapViewOfFile` (byte search), which fits that source; that the DLL was built
  from exactly this tag, unpatched, is itself UNVERIFIED.
- **VERIFIED-disk**: a read-only listing or byte search on this PC on 2026-10-29.
- **DOC**: quoted from a project document or a code comment.
- **UNVERIFIED**: inference; each one says what would prove it.

---------------------------------------------------------------------------------------------------------------------------

## 0. The answers in brief

**(a) The emulator: how the battery save reaches disk**
- **A1. On every flash write, by memory mapping; not periodically and not at close.** The framework opens
  `<profile>/current_save.sav` read-write and hands it to mGBA before the first reset [VERIFIED-code
  `sandbox-pokebot/modules/libmgba.py:124-133`, `sandbox-pokebot/mgba/vfs.py:90-109`]. mGBA 0.10.2 maps that file with a
  shared writable view (on Windows `CreateFileMapping(PAGE_READWRITE)` + `MapViewOfFile(FILE_MAP_WRITE)`), so each byte the
  game programs into flash lands straight in the file's own pages in the OS file cache [VERIFIED-mgba
  `src/gba/savedata.c:46-63,261-288`, `src/util/vfs/vfs-fd.c:157-182`, `CMakeLists.txt:222`].
- **A2. mGBA's explicit flush is late and partial.** At the first frame end more than 15 frames after the last flash
  write, mGBA calls `FlushViewOfFile` (never `FlushFileBuffers` on that path) and appends a 16-byte RTC footer. On that same
  frame end its `savedataUpdated` callback fires, and the framework copies the file to
  `<profile>/saves/<YYYY-MM-DD_HH-MM-SS>.sav` [VERIFIED-mgba `include/mgba/internal/defines.h:9-29`, `savedata.c:571-615`,
  `vfs-fd.c:270-280`, `src/gba/gba.c:887-922`; VERIFIED-code `libmgba.py:161,243-256`]. On disk, the 13 profiles that ever
  synced hold 131,088-byte `.sav` files, the other 495 hold 131,072 bytes, and none of the 14 ai_player-owned profiles has
  ever synced a save [VERIFIED-disk].
- **A3. "Written on a clean close only" is true of the RESUME STATE, not of the `.sav`.** At a normal interpreter exit,
  an `atexit` hook writes `current_state.ss1` (and a copy in `states/`). At the next start that file is loaded if it is
  present [VERIFIED-code `libmgba.py:141-146,159-160,201-241`; a console close also calls it, `sandbox-pokebot/pokebot.py:217-224`].
  The `.sav` needs no close step, because it is the mapped file.
- **A4. A process kill should not lose a save the game reported done; a power cut can.** When "{PLAYER} saved the game."
  starts printing, all 14 sectors are already in the mapped pages, and those pages belong to the OS, not to the process
  [VERIFIED-decomp `src/start_menu.c:1086-1110`; mapping as in A1]. That a TerminateProcess leaves them in the file is the
  claim to MEASURE [UNVERIFIED-live]. A power cut or an OS crash can lose them. Before mGBA's flush (16+ frames later, which
  is milliseconds at the AI's unthrottled speed) nothing has been forced to disk, and the flush never empties the drive's own
  cache [VERIFIED-mgba `vfs-fd.c:270-280`; the loss itself is UNVERIFIED and cannot be tested safely on this PC]. So "does
  mGBA flush before a kill?" is the wrong question for a process kill and the right one for a power cut.
- **A5. A torn save mostly falls back to the previous save.** The game writes each save into the OTHER of two 14-sector
  slots, in one call made right after "SAVING… DON'T TURN OFF THE POWER." finishes printing. At boot it uses the valid slot
  with the higher counter. If a slot is half-written, the game says "The save file is corrupted. The previous save file will
  be loaded." and CONTINUE loads the previous save. If the FIRST save is half-written, the game says "The save file has been
  erased due to corruption or damage." and there is no CONTINUE [VERIFIED-decomp `start_menu.c:884-894,1080-1110`,
  `src/save.c:139-209,515-637,708-783`, `src/main_menu.c:641-671`]. The game never checks that a slot's 14 sectors share one
  counter, so a slot where only some whole 4 KB pages reached disk could load as a MIXED save [VERIFIED-decomp
  `save.c:486-512,527-541`; the outcome UNVERIFIED].
- **A6. The `.ss1` is a machine snapshot tied to the emulator build.** It is a PNG screenshot that carries a
  zlib-compressed mGBA state in a `gbAs` chunk. It is saved with flags 0, so it holds RAM and CPU but NOT the cartridge save
  [VERIFIED-code `libmgba.py:201-229,360-375`, `mgba/core.py:235-248`; VERIFIED-mgba `src/core/serialize.c:401-410`]. mGBA
  refuses a state from a newer serializer, from another game or from another ROM size, and only warns about another ROM
  revision [VERIFIED-mgba `src/gba/serialize.c:90-135`; the message strings are in the shipped DLL, VERIFIED-disk]. The
  framework ignores a refused load while mGBA's log is silenced, so a bad `.ss1` becomes a SILENT cold boot [VERIFIED-code
  `libmgba.py:117,367-375`].
- **A7. A hazard the backlog does not name: a stale `.ss1` next to a newer `.sav`.** After a kill, the profile still holds
  the `.ss1` from the last clean close. A resume with no flag loads it. The old RAM's save counter then writes an OLDER
  save into a slot, after which CONTINUE can pick either slot ("split-brain") [VERIFIED-code
  `ai_player/host/launcher.py:187-188`, `libmgba.py:141-146`; VERIFIED-decomp `save.c:155-163,185-187,587-603`; the outcome
  is UNVERIFIED].

**(b) The host**
- **A8. How a run starts.** The command is `py -3.12 -m ai_player run --profile NAME [--frames N] [--wall-seconds S]
  [--fresh | --state PATH] [--build-root DIR] [--template-profile NAME] [--run-dir DIR]`. It runs the purity gate (exit 7 on
  a FAIL), builds the profile from a donor's `metadata.yml`, seeds it and forces `http.yml` off. It then starts
  `pokebot.py NAME -m "AI Player" -s 0 -na -hl` with no console, stdin DEVNULL, and a soft and a hard wall clock
  [VERIFIED-code `ai_player/__main__.py:51-70,125-198`, `host/launcher.py:145-216,302-311,375-431`]. `--fresh` deletes the
  `.ss1` and the `.sav` (title screen, New Game). `--state` installs a fixture `.ss1` and deletes the `.sav`. Neither flag
  means "what the profile holds", which in practice is the last clean close's `.ss1` [VERIFIED-code `launcher.py:179-209`].
- **A9. Where a profile's files live.** All of them are in `<build_root>/profiles/<NAME>/`, inside the framework folder,
  next to 500+ bot profiles. Per-run AI files go to `ai_player_runs/<YYYYmmdd-HHMMSS>/` in that folder unless `--run-dir`
  is given [VERIFIED-code `__main__.py:147`; full list in §3.2].
- **A10. How a run ends.** Through the lifecycle it ends with a verdict and exit 0, 2, 3, 4, 5, 6, 9, 124 (soft) or 130.
  Through the launcher's TerminateProcess it ends without one: 124 (hard) or 130 (Ctrl+C at the launcher). Exits 7 and 8 are
  the launcher's own [VERIFIED-code `host/lifecycle.py:48-58`, `launcher.py:94-98,351-431`]. The `.ss1` is NOT refreshed
  after a hard kill, a launcher Ctrl+C, the interrupt watch (it ends with `os._exit` at once), the ran-after-finish
  tripwire, or a shutdown held past 20 s [VERIFIED-code `host/attribution.py:463-473,891-907,954-975`,
  `host/session.py:234-258`]. The profiles `ai-step01-http` and `ai-step01-signal` hold no `.ss1` [VERIFIED-disk].
- **A11. Nothing supports starting from a `.sav` and choosing CONTINUE.** No launcher mode keeps the `.sav` while dropping
  the `.ss1`. The play brain treats a title screen with no marks as a New Game, and the intro skill chooses NEW GAME
  [VERIFIED-code `ai_player/mode.py:456-462,488-497`, `skills/intro.py:113-115`, `host/eyes.py:279`]. Three pieces are ready
  to reuse. The eyes already name CONTINUE for each menu type and recognise the corrupt-save windows [VERIFIED-code
  `eyes/screens.py:258-267,310-311`]. The framework cold-boots a `.sav` when no `.ss1` exists [DOC
  `tools/story-dev/livetest.py:247-251`: a bot lane "resumed an old save" on a fresh boot]. The framework also has a sector
  parser [VERIFIED-code `sandbox-pokebot/modules/save_data.py:139-200`].
- **A12. Purity decides where R1's host work can happen.** During a run, a state load, `load_save`, `load_save_game` or
  `reset` is a BREACH, a callback added after install counts as `instrument_tampered`, and the cartridge save is outside the
  audited sinks [VERIFIED-code `attribution.py:25-26,144-148,179-180,250-255,775-778,1383-1388`; plant arms
  `gates/live_step0.py:2260-2262`]. So swapping or reloading a `.sav` must happen BETWEEN processes, in the launcher. An
  in-game save, and a soft reset by held buttons, are the game's own code.

**(c) DP1 / DP2 ground truth**
- **A13. How the framework is found.** The launcher takes `--build-root`, else `AI_PLAYER_BUILD_ROOT`, else
  `<folder containing ai_player>/sandbox-pokebot` [VERIFIED-code `launcher.py:81-82,113-118`]. The hook finds the AI from
  `AI_PLAYER_PACKAGE_ROOT`, else three folders up [VERIFIED-code
  `sandbox-pokebot/plugins/custom_modes/ai_player_mode.py:45-48`]. The backlog's `launcher.py:89,145-165` is the DONOR rule,
  not the locator.
- **A14. AI-owned user data exists per RUN only.** The one cross-run memory is a `world.jsonl` path that a DRIVER passes in
  `AI_PLAYER_WORLD` [VERIFIED-code `options.py:178-180`, `gates/live_step5.py:450-462,497-507`]. No file carries a
  `schema_version`, and no `AppPaths` or `AI_PLAYER_HOME` exists [VERIFIED-code: 0 grep hits in `ai_player/`, `ai-agent/` and
  `tools/`]. 12 gates use `resolve_build_root`; 16 sites in 13 gate files hardcode `<repo>/sandbox-pokebot` [VERIFIED-code,
  §4.6].
- **A15. Two constraints on R2's file.** In the play loop only `runlog.py` and the instrument may write files, and `os` and
  `shutil` are on no surface, so the play loop cannot fsync [VERIFIED-code `gates/check_purity.py:85-90,600-603`].
  `RecordFile` opens the file, appends one line and closes it; that survives a process kill but not a power cut
  [VERIFIED-code `ai_player/runlog.py:55-89`]. The emulator's frame counter restarts at 0 on every cold boot (so on every
  CONTINUE) and is restored by a `.ss1` load, so it cannot order memory across a CONTINUE. The game's play time in
  SaveBlock2 (bytes 0x0E-0x12) can [VERIFIED-mgba `src/gba/video.c:79,339,354`; VERIFIED-decomp `include/global.h:514-517`].

**(d) What to measure before building**
- **A16. Five measurements.**
  - M1: does a `.sav` survive TerminateProcess at K0 (the frame the save call returned), at K1 (8 frames later, before
    mGBA's flush) and at K2 (40 frames later, after it)? Judge it two ways: a second-path parse of the file, AND the game's own
    CONTINUE in a fresh process (same party PIDs, map, tile and play time).
  - M2: the frame counts from "SAVING…" printed to the last flash write, then to "saved the game", then to mGBA's flush,
    then to the dialog closing.
  - M3: a save made inside a launcher run keeps the verdict CLEAN.
  - M4: does the split-brain of A7 happen?
  - M5, only if the user allows reloads: does an in-game soft reset keep purity? mGBA's BIOS soft reset does not touch its
    frame counter [VERIFIED-mgba `src/gba/bios.c:38-50,447-449`], so `modules/main.py:119-132` should not rebuild the
    listeners [UNVERIFIED-live].

  The existing harness boot cannot run M1, because it uses `is_test_run=True` and so never maps a `.sav` [VERIFIED-code
  `gates/probe_eyes.py:185-201`, `libmgba.py:127-133`; VERIFIED-mgba `savedata.c:276-278,572-574`]. The probe sketch is in §5.

**(e) The user's two open questions (not decided here)**
- **A17. What each answer changes.**
  - WHEN the AI saves decides three things: how much a kill can lose, how fast `saves/` grows (one 128 KB copy per save,
    with no retention today), and whether the soft deadline must warn the brain before it ends the run (today the guard ends
    the run on the deadline frame, VERIFIED-code `session.py:305-310`).
  - WHETHER IT MAY RELOAD: "no" (the backlog's default) needs CONTINUE only when a process starts. "Yes, as a person" needs
    M5, a mid-run rollback of memory to the reloaded save's play time, and a rule for the defeat ledger. "Yes, by the
    emulator" is a purity breach by design (§6).

---------------------------------------------------------------------------------------------------------------------------

## 1. Sources and how far each was read

- The framework's mGBA wrapper: `sandbox-pokebot/modules/libmgba.py`, read in full (653 lines). It is byte-identical to
  `custom-pokebot/modules/libmgba.py` and `40cakes repo/pokebot-gen3/modules/libmgba.py`, so this is upstream code
  [VERIFIED-disk, `diff -q`].
- The Python binding: `sandbox-pokebot/mgba/core.py` and `vfs.py`, read in full. `__init__.py` was read as well.
- mGBA C source at tag 0.10.2, the parts read: `src/gba/savedata.c` (init, mask, flash init, clean, RTC write),
  `include/mgba/internal/defines.h` (the clean rule), `src/gba/gba.c` (`GBAFrameEnded`), `src/util/vfs.c` (`VFileOpen`),
  `src/util/vfs/vfs-fd.c` (Windows map, unmap, sync), `CMakeLists.txt` (which VFS goes into the Windows build),
  `src/core/serialize.c` (state save and load), `src/gba/core.c` (`_GBACoreSavedataRestore`), `src/gba/serialize.c`
  (state checks), `src/gba/video.c` (frame counter) and `src/gba/bios.c` (soft reset).
- The AI host: `ai_player/host/launcher.py`, `lifecycle.py`, `session.py`, `ai_player/__main__.py`, `options.py` and
  `runlog.py`, read in full. `host/attribution.py` and `host/eyes.py` were read in the parts cited.
- The decomp: `src/start_menu.c` (the save dialog), `src/save.c` (writing, slot choice, loading),
  `include/save.h`, `include/global.h`, `src/main_menu.c`, `src/intro.c`, `src/new_game.c`, `src/main.c`,
  `src/overworld.c`, `src/play_time.c`, `data/text/save.inc` and `include/constants/game_stat.h`.
- Project docs: the backlog lines above; `2026-10-19-backlog-round3/02-deployment.md` (DP1-DP13 in their original D1-D13
  form); `04-HANDOFF.md:61` (the two unanswered questions); `06-DECISIONS-LOG.md:2220-2248` (an earlier ruling on resuming
  the BOT after a power loss, see §6).

---------------------------------------------------------------------------------------------------------------------------

## 2. (a) The emulator in detail

### 2.1 The open and the mapping
- `LibmgbaEmulator.__init__` loads the ROM. If the run is not a test run, it creates an empty `current_save.sav` when the
  file is missing, opens it with `mgba.vfs.open_path(path, "r+")`, calls `core.load_save(...)`, and then calls
  `core.reset()` [VERIFIED-code `libmgba.py:119-138`]. The comment there says why: "libmgba needs a save file to be loaded,
  or otherwise it will not save anything to disk" (`libmgba.py:124-125`).
- `open_path` turns "r+" into `O_RDWR` and calls the C function `VFileOpen` [VERIFIED-code `mgba/vfs.py:90-109`]. In
  0.10.2, `VFileOpen` uses stdio only when `USE_VFS_FILE` is defined [VERIFIED-mgba `src/util/vfs.c:17-41`]. The Windows
  build compiles `vfs-fd.c` plus `vfs-w32.c` [VERIFIED-mgba `CMakeLists.txt:222`], and the root CMakeLists does not define
  `USE_VFS_FILE` (grep, 0 hits).
- `GBASavedataInit` sets `mapMode = MAP_WRITE` [VERIFIED-mgba `savedata.c:46-63`]. For Emerald (Flash 1M),
  `GBASavedataInitFlash` grows a short file to 131,072 bytes, maps it with that mode, and fills any new part with 0xFF
  [VERIFIED-mgba `savedata.c:261-288`]. That explains why every AI profile's never-saved `.sav` is exactly 131,072 bytes
  [VERIFIED-disk].
- On Windows, `_vfdMap` with `MAP_WRITE` calls `CreateFileMapping(PAGE_READWRITE)` and `MapViewOfFile(FILE_MAP_WRITE)`
  [VERIFIED-mgba `vfs-fd.c:157-182`]. ⇒ The flash the game sees IS the file's page cache. No per-write `write()` call
  exists, and no timer exists.

### 2.2 When mGBA forces it out, and the framework's copy
- Every flash write sets `dirty |= NEW` [VERIFIED-mgba `savedata.c:389,521,756,766`]. At each frame end, `GBAFrameEnded`
  calls `GBASavedataClean(frameCounter)` [VERIFIED-mgba `gba.c:887-889`]. `mSavedataClean` ages the dirt. It returns true
  once `frameCount - dirtAge > 15` (`mSAVEDATA_CLEANUP_THRESHOLD 15`), where `dirtAge` is the frame of the last frame end
  that saw a new write [VERIFIED-mgba `defines.h:9-29`]. ⇒ The flush comes 16 frames after the LAST write of a burst.
- On that frame, `GBASavedataClean` calls `vf->sync(data, size)` and then `GBASavedataRTCWrite` [VERIFIED-mgba
  `savedata.c:571-590`]. The Windows sync, with a buffer, is `FlushViewOfFile(buffer, size)` and nothing else (it also stamps
  the file's times). `FlushFileBuffers` runs only when no buffer is passed [VERIFIED-mgba `vfs-fd.c:246-281`].
  `FlushViewOfFile` starts writing the dirty pages out but does not flush the drive's cache [UNVERIFIED: the Windows API
  documentation, from memory].
- The RTC footer: 16 bytes at offset 131,072. Writing past the end unmaps and remaps the view [VERIFIED-mgba
  `savedata.c:592-615`]. ⇒ A `.sav` that has been synced at least once is 131,088 bytes. The size histogram of all 508
  `current_save.sav` files is 495 × 131,072 and 13 × 131,088 [VERIFIED-disk]. The profiles with 131,088 bytes are exactly
  the ones with `saves/` copies, for example `Nick - Emerald` (17 copies) and `endless-s14-*` (1 each) [VERIFIED-disk].
- The callback: `GBAFrameEnded` calls each `savedataUpdated` callback when `wasDirty && !dirty`, which is the frame the
  clean ran [VERIFIED-mgba `gba.c:887-922`]. The binding forwards it [VERIFIED-code `mgba/core.py:96-99,108-147,165-166`].
  The framework registered `backup_current_save_game` on it [VERIFIED-code `libmgba.py:159-161`]. That function copies
  `current_save.sav` to `saves/<YYYY-MM-DD_HH-MM-SS>.sav`, with no retention, at one-second name resolution (two syncs in
  the same second overwrite one copy) [VERIFIED-code `libmgba.py:243-256`]. ⇒ The `saves/` copy is a ready-made "the save
  reached the file and mGBA flushed it" signal that can be watched from OUTSIDE the process.
- With `is_test_run=True`, none of this happens. No file is opened [VERIFIED-code `libmgba.py:127-133`]. mGBA then keeps
  the flash in anonymous memory and `GBASavedataClean` returns at once [VERIFIED-mgba `savedata.c:276-278,572-574`]. Every
  existing harness boots that way [VERIFIED-code `gates/probe_eyes.py:185-201`, used by `hands_harness.py`,
  `play_harness.py`, `probe_end_screen.py`].

### 2.3 The clean close, and what writes the `.ss1`
- `shutdown()` calls `create_save_state()`. That writes `states/<YYYY-MM-DD_HH-MM-SS>.ss1` first and then
  `current_state.ss1` [VERIFIED-code `libmgba.py:201-241`]. `shutdown()` is registered with `atexit` [VERIFIED-code
  `libmgba.py:159-160`] and called from the Windows console-close handler [VERIFIED-code `pokebot.py:217-224`]. An AI child
  has no console (`CREATE_NO_WINDOW`, `launcher.py:377`), so in practice only `atexit` applies [UNVERIFIED that the
  console-close path can never fire for it].
- The headless frontend that AI runs use never calls `os._exit`: it builds the emulator and runs `main_loop()`
  [VERIFIED-code `sandbox-pokebot/modules/gui/headless.py:17-31`]. `SystemExit` passes through `main.py` [VERIFIED-code
  `sandbox-pokebot/modules/main.py:174-175`]. So a lifecycle exit on the main thread reaches `atexit`. The hook's
  `_report_listeners_at_exit` runs first, then `shutdown()`, then `pokebot.on_exit` (which does not pause: stdin is DEVNULL)
  [VERIFIED-code `ai_player_mode.py:77-81`, `pokebot.py:23-47`; the order is Python's LIFO `atexit` rule].
- At close, the `.sav` needs nothing. If mGBA's core is deinitialised, `_vfdUnmap` flushes the view again [VERIFIED-mgba
  `vfs-fd.c:184-196`, `savedata.c:66-71`]. Whether `ffi.gc(native, native.deinit)` runs at interpreter exit is UNVERIFIED,
  and it does not matter for a process kill (§2.5).

### 2.4 The game's side: when a save is "done" (the timeline the AI will read)
1. START → start menu → "SAVE" (the eyes already name it: `START_MENU_ACTIONS[5]`, VERIFIED-code `eyes/screens.py:267`).
   `InitSave` points the dialog at `SaveConfirmSaveCallback` [VERIFIED-decomp `start_menu.c:877-882`].
2. "Would you like to save the game?" with YES/NO, default YES [VERIFIED-decomp `start_menu.c:978-1001`; text
   `data/text/save.inc:2-3`].
3. After YES there are three branches, decided by RAM. (a) A New Game's first save goes straight to step 4, because
   `gDifferentSaveFile` is TRUE after New Game [`src/new_game.c:150-154`] and the flash is EMPTY. (b) Any later save asks
   "There is already a saved file. Is it okay to overwrite it?", default YES. (c) A New Game started over an existing save
   asks "WARNING! There is a different game file that is already saved. … entirely lost …", default NO [VERIFIED-decomp
   `start_menu.c:1003-1078`, `save.inc:5-24`; `gDifferentSaveFile` is cleared at boot, `new_game.c:139-141`, `intro.c:1152`].
4. "SAVING…\nDON'T TURN OFF THE POWER." [VERIFIED-decomp `start_menu.c:1080-1084`, `save.inc:9-11`]. The next callback
   runs only once text printer 0 is idle [VERIFIED-decomp `start_menu.c:884-894`].
5. `SaveDoSaveCallback` calls `IncrementGameStat(GAME_STAT_SAVED_GAME)` (stat 0) and then `TrySavingData(SAVE_NORMAL)`.
   `SAVE_OVERWRITE_DIFFERENT_FILE` also erases the Hall of Fame sectors [VERIFIED-decomp `start_menu.c:1086-1110`,
   `include/constants/game_stat.h:4`, `save.c:744-751`].
6. `HandleSavingData` → `WriteSaveSectorOrSlot(FULL_SAVE_SLOT)`. This increments `gSaveCounter` and writes all 14 sectors
   into slot `gSaveCounter % 2` (the OTHER slot), each with id, checksum, signature `0x08012025` and counter [VERIFIED-decomp
   `save.c:139-209,708-756`, `include/save.h:5-30,74-82`]. This is one call. Whether it spans more than one EMULATED frame
   under mGBA's flash timing is UNVERIFIED (M2).
7. "{PLAYER} saved the game." Then SE_SAVE after the text, then a 60-frame timer (or A held) before the box closes
   [VERIFIED-decomp `start_menu.c:942-967,1102-1134`, `save.inc:13-14`].
8. mGBA: the bytes from step 6 are in the file's pages as they are written. The flush, the RTC footer and the framework's
   `saves/` copy come 16 frames after the last write (§2.2). EXPECTED: the flush lands while step 7's box is still on screen,
   because text, sound effect and the timer add up to far more than 16 frames, so a FREE screen after the dialog implies
   "flushed" [UNVERIFIED; M2 measures it].

### 2.5 Can a kill lose a save the game reported done?

| What ends the process | Writes from step 6 | What CONTINUE shows next time |
|---|---|---|
| TerminateProcess (the launcher's hard wall clock, a launcher Ctrl+C, `taskkill /F`, a crash) after step 7 began | expected KEPT: the dirty pages belong to the OS mapping, not to the process [UNVERIFIED-live, M1] | the new save |
| `os._exit` (the exit watchdog, the interrupt watch, the tripwire) after step 7 | the same as TerminateProcess [UNVERIFIED-live] | the new save |
| A kill DURING step 6 (only possible if step 6 spans frames, or inside one native call) | the new slot is partly written | "The save file is corrupted. The previous save file will be loaded." and then the previous save; for a first-ever save, "…erased…" and no CONTINUE [VERIFIED-decomp `save.c:515-637`, `main_menu.c:641-671`] |
| A power cut or OS crash before the OS wrote the pages out | lost or partial | the previous save, the corrupt message, or (A5) a mixed slot [UNVERIFIED] |
| A power cut after mGBA's `FlushViewOfFile` | most likely kept; the drive cache was never flushed [UNVERIFIED] | the new save, most likely |

- "Coherence" assumption: on Windows, a `ReadFile` of a file that another process has mapped sees the same cache pages.
  So a parent process reading the `.sav` while the child is paused already sees the new bytes. That shows "in the OS
  cache", not "on the platter" [UNVERIFIED Windows behaviour, recalled; M1 relies on it only for a timeline, never for a
  verdict].
- The bot's earlier user ruling asks for "pick up where it left off … during sudden power loss" (§6). If the same is wanted
  for the AI, the power-cut row is the one that needs a host action, for example a `FlushFileBuffers` (Python
  `os.fsync` on a second handle) after the `saves/` copy appears. That fsync could only run in the launcher or in a gated
  writer, never in the play loop (A15) [UNVERIFIED design option].

### 2.6 The split-brain hazard (A7), worked through
- Session 1 ends clean at play time T0 with `current_state.ss1`, whose RAM holds `gSaveCounter = c`. Session 2 resumes
  from it, saves at T1 (slot (c+1)%2, counter c+1) and at T2 (slot c%2, counter c+2), and is then hard-killed, so no new
  `.ss1` is written. Session 3 starts with no flag. The framework loads the STALE `.ss1` (RAM at T0, counter c)
  [VERIFIED-code `launcher.py:187-188`, `libmgba.py:141-146`]. The AI replays from T0, and its first save writes counter
  c+1 into slot (c+1)%2, overwriting T1 [VERIFIED-decomp `save.c:155-163,185-187`]. Flash now holds T2 (c+2) and T0'
  (c+1). The next CONTINUE picks the higher counter, which is T2: session 2's progress, NOT the save the AI just made
  [VERIFIED-decomp `save.c:587-603`]. The outcome is UNVERIFIED-live (M4).
- The same stale load means R2's "memory not newer than its save" must compare against what the game ACTUALLY resumed
  from (a `.ss1`'s RAM or a `.sav`), never against the host's idea of the last save [UNVERIFIED design consequence].

### 2.7 The `.ss1`: what it is and why it is tied to the build
- Format: a PNG of the screen with a custom `gbAs` chunk holding `zlib(core.save_state())` [VERIFIED-code
  `libmgba.py:201-229`]. `save_state()` = `mCoreSaveStateNamed(core, vf, 0)` [VERIFIED-code `mgba/core.py:243-248`]. With
  flags 0 there is no `SAVESTATE_SAVEDATA`, so the cartridge flash is NOT inside it [VERIFIED-mgba `serialize.c:401-410`,
  `include/mgba/core/serialize.h:24-29`]. It holds the machine (CPU, RAM, I/O, video, the frame counter) and the save
  chip's command state, not its content.
- Tied to the build: `GBADeserialize` refuses a state whose version is newer than this build's ("Invalid or too new
  savestate"), a different game id or title, or a different ROM size. It only WARNS for a different ROM CRC (another
  revision) or a different BIOS [VERIFIED-mgba `src/gba/serialize.c:90-135`; all these strings are in the shipped DLL,
  VERIFIED-disk]. ⇒ An older mGBA cannot load a newer mGBA's state, so the `.ss1` follows the emulator binary, while the
  `.sav` is the game's own sector format (plus mGBA's 16-byte footer). That is DP4's point ("the `.sav` is the durable
  copy", DOC `02-deployment.md:66-71`).
- Silent failure: `load_save_state` ignores the bool `load_state` returns [VERIFIED-code `libmgba.py:367-375`,
  `mgba/core.py:235-237`], and `mgba.log.silence()` hides mGBA's warning [VERIFIED-code `libmgba.py:117`]. ⇒ A refused
  `.ss1` gives a normal cold boot to the title screen, which today's play brain would answer with NEW GAME (§3.4)
  [UNVERIFIED that the machine is left untouched after a refusal].
- A niche case that can be ruled out today: a state that DID carry savedata would mask the `.sav` when loaded with flags
  0. mGBA would put the state's flash image in memory, with writeback on the next clean [VERIFIED-mgba `core.c:1199-1213`,
  `savedata.c:102-128,571-578`]. Until that clean, a kill would lose writes, and after it the file's other slot would hold
  the state's image. The framework's own states carry none (flags 0). 0 of the 18 committed fixture `.ss1` files has a
  `gbAx` chunk [VERIFIED-disk], and the importer splits savedata out into the `.sav` [VERIFIED-code
  `sandbox-pokebot/modules/save_import.py:109-135`].

---------------------------------------------------------------------------------------------------------------------------

## 3. (b) The host side in detail

### 3.1 How a run starts
1. `cmd_run`: it checks `--frames` and `--wall-seconds`, then `resolve_build_root`, then `_gate` (the purity gate in a
   subprocess on this package and the hook; a FAIL exits 7 unless `--allow-ungated`) [VERIFIED-code
   `__main__.py:73-90,125-138`, `launcher.py:272-289`].
2. `ensure_profile` copies `metadata.yml` from `--template-profile`, else `endless-P1-torchic`, else the first profile
   (sorted) that has one, else errors. It writes `http.yml` and the `.ai_player_profile` marker [VERIFIED-code
   `launcher.py:84-89,145-176`]. That is DP1's "a profile needs a donor" (T2 in `02-deployment.md:23-25`).
3. `seed_profile`:
   - with no flag, it leaves the profile alone;
   - with `--fresh` or `--state`, it requires the marker and deletes `current_state.ss1`, `current_save.sav` and
     `states/*.ss1`;
   - with `--state`, it then copies the fixture to `current_state.ss1`.

   It never touches `saves/` [VERIFIED-code `launcher.py:179-209`]. ⇒ After R1, `--fresh` would delete a playthrough's
   only live `.sav` without a copy (DP4's "never a silent `--fresh` wipe"). Only the framework's `saves/` copies would
   survive.
4. `force_http_off` (every run, owned profiles only), the run folder, then `child_env`: `AI_PLAYER_FRAMES`,
   `AI_PLAYER_RUN_DIR`, `AI_PLAYER_PACKAGE_ROOT`, `AI_PLAYER_WALL_DEADLINE`, `PYTHONUTF8=1`, the rest of the environment
   minus `UNTRUSTED_ENV` [VERIFIED-code `launcher.py:133-142,302-311`, `__main__.py:142-153`]. The brain's own switches
   (`AI_PLAYER_BRAIN`, `_SEED`, `_TARGET`, `_STARTER`, `_PERSONALITY`, `_WORLD`, about 24 FAULT/CONTROL switches) reach it
   through that environment [VERIFIED-code `options.py:129-242`].
5. `check_package_resolution` (the child must import THIS `ai_player`), then `run_child`: `pokebot.py NAME -m "AI Player"
   -s 0 -na -hl`, cwd = the build root, stdin DEVNULL, `CREATE_NO_WINDOW`, polling every 0.5 s against the hard deadline
   [VERIFIED-code `launcher.py:212-238,375-431`]. `-s 0` = unthrottled [VERIFIED-code `pokebot.py:113-118`].
6. In the child: `pokebot.py` runs `run_launch_sync()` (cloud save-sync; per-profile opt-in, OFF by default) before any
   emulator exists, then the headless frontend [VERIFIED-code `pokebot.py:205-212`,
   `sandbox-pokebot/modules/cloud_sync.py:187-208`, `headless.py:17-31`]. If a user turned sync on for an AI profile, a
   newer cloud `.sav` could replace the local one before boot [UNVERIFIED as a real risk; default off].
7. The boot: the emulator opens the `.sav` and resets. If `current_state.ss1` exists it loads that, otherwise the game
   boots: the intro, then `LoadGameSave(SAVE_NORMAL)` READS THE FLASH ONCE, then the title [VERIFIED-code
   `libmgba.py:124-146`; VERIFIED-decomp `intro.c:1147-1159`]. The flash is read only at power-on or a soft reset, so a
   `.sav` swap must happen before the process starts. The mode starts on the title screen
   (`is_selectable_from_title_screen` True), and the session installs isolation and the instrument in the hook's
   constructor [VERIFIED-code `ai_player_mode.py:72-86`, `session.py:171-204`].

### 3.2 Where a profile's files live (`<build_root>/profiles/<NAME>/`)
- Written by the launcher: `metadata.yml` (the ROM binding), `http.yml` (forced off on every run) and
  `.ai_player_profile` (the marker) [VERIFIED-code `launcher.py:133-176`].
- Written by the framework: `current_save.sav` (mapped, §2.1), `current_state.ss1` and `states/<ts>.ss1` (at clean
  close), `saves/<ts>.sav` (at each mGBA flush), `screenshots/` (on request) [VERIFIED-code
  `libmgba.py:126,143,202-227,252-256,541-550`], `stats.db` [VERIFIED-code `main.py:58`; VERIFIED-disk in `ai-step5-play`],
  and `badge-log.json` [DOC `main.py:109-117` comment; not seen in `ai-step5-play`].
- Written by the AI, per run: `ai_player_runs/<YYYYmmdd-HHMMSS>/` holds `ai_player.log` and `actions.jsonl` (`RunLog` /
  `RecordFile`), `world.jsonl` (a full snapshot line at every map change and at the end), `purity.json` (the instrument) and
  `stdout.txt` (the launcher's transcript) [VERIFIED-code `__main__.py:147,175`, `runlog.py:22-24,55-65`,
  `mode.py:96,293-296`, `session.py:163`, `options.py:248`]. The live drivers add `end_state.ss1` there and evidence in
  `ai_player/evidence/` [VERIFIED-code `live_step5.py:497-507,953`].
- Sizes for scale (one CH2M run in `ai-step5-play`): `world.jsonl` 6.7 MB, `actions.jsonl` 2.1 MB, and a `.ss1` of
  31-33 KB [VERIFIED-disk].

### 3.3 How a run ends, and what each ending leaves

| Ending | Exit | Verdict file | `.ss1` refreshed | Flash writes so far |
|---|---|---|---|---|
| The brain gives up, crash, parked, frame budget, brain returned, isolation lost or breach, soft wall clock, Ctrl+C in a console | 0/2/3/4/5/6/124/130 | yes | yes (`atexit`), if shutdown takes under 20 s | kept |
| Refused (debug mode or HTTP on) | 9 | yes | no when the HTTP thread holds shutdown and the watchdog `os._exit`s after 20 s (`lifecycle.py:40-43` DOC; `ai-step01-http` has no `.ss1`, VERIFIED-disk) | kept |
| The interrupt watch ends a stuck run | 130 | yes | NO: it finishes off the main thread, so the watchdog `os._exit`s at once (`attribution.py:891-907`, `session.py:234-258`) | kept (expected) |
| Ran after finish (tripwire) | 6 | rewritten as BREACH | NO (`os._exit`, `attribution.py:954-975`) | kept (expected) |
| The launcher's hard wall clock | 124 | NO | NO; the previous `.ss1` stays STALE | kept (expected, M1) |
| Ctrl+C reaching the launcher | 130 | NO | NO; stale | kept (expected, M1) |
| A reboot, power cut or OS crash | — | NO | NO; stale | may be lost (§2.5) |

[VERIFIED-code `lifecycle.py:9-58,138-185`, `launcher.py:94-98,351-431`, `__main__.py:93-122,176-198`;
`kill_tree` uses `psutil.Process.kill()`, which is TerminateProcess on Windows, UNVERIFIED but standard.]

### 3.4 Is there any path from a `.sav` to CONTINUE? No.
- The launcher has no mode that keeps `current_save.sav` and removes `current_state.ss1`, and none that seeds a profile
  from a `.sav` file [VERIFIED-code `launcher.py:179-209`]. The only `.sav` code anywhere in `ai_player/` is that delete and
  the purity layer's refusal of `load_save_game` [VERIFIED-code grep: `launcher.py:93,196`, `check_purity.py:544`,
  `attribution.py:179`].
- The play brain: on a look with no marks and no player, "the title screen: a New Game (nothing is saved yet)" sets
  milestone 0, and `play_intro` runs [VERIFIED-code `mode.py:456-462,488-497`]. The intro chooses "NEW GAME" on the main
  menu [VERIFIED-code `skills/intro.py:9,113-115`]. The eyes give no player or progress on `TITLE_SCREEN` or `MAIN_MENU`
  [VERIFIED-code `host/eyes.py:279,369-380`], so a `.sav` boot today walks into NEW GAME. At the first save that New Game
  would then meet the default-NO "WARNING! … different game file …" (§2.4 step 3c).
- What already helps:
  - The eyes map `Task_HandleMainMenuInput` to `main_menu` and know the options per `tMenuType` (CONTINUE first when a
    save exists) [VERIFIED-code `eyes/screens.py:229-230,258-264`; VERIFIED-decomp `main_menu.c:641-671`].
  - The eyes treat the corrupt-save and battery windows as "wait for A" [VERIFIED-code `eyes/screens.py:310-311`].
  - The CONTINUE screen shows the player's name, play time, Pokédex count and badges, which a person can read
    [VERIFIED-decomp `main_menu.c:2137-2184`].
  - CONTINUE restores the saved map and position unless a continue-warp is set; a warp is used after the Hall of Fame and
    in some Battle Frontier saves [VERIFIED-decomp `src/overworld.c:1705-1745`, `start_menu.c:1297`].
  - Prior art: "a 'fresh' boot with a save present CONTINUES it" (a bot lane "reached the frontier in 7 min by resuming an
    old save") [DOC `tools/story-dev/livetest.py:247-251`].
- The teacher: the bot's `save_the_game` reads the hidden `sSaveDialogCallback` and always confirms an overwrite,
  including the "different file" warning [VERIFIED-code `sandbox-pokebot/modules/modes/util/higher_level_actions.py:870-910`].
  The bot saves only after a catch, when `battle.save_after_catching` is set [VERIFIED-code
  `sandbox-pokebot/modules/modes/_listeners.py:270-287`]. "The story bot NEVER SAVES" [DOC
  `sandbox-pokebot/modules/story/pokemon_league.py:1600-1603`]. So the teacher offers no person-like saving policy.

### 3.5 Purity rules that bind R1's host design
- Counted as LOADS (breach counters): `emulator.load_save_state`, `load_save_game` and `reset`; the core's `load_state`,
  `load_state_slot`, `load_save`, `load_temporary_save`, `load_raw_state`, `load_patch` and `reset` [VERIFIED-code
  `attribution.py:25-26,179-180,250-255`]. Plant arms XL, XN and XS prove a rewind or a `load_save_game` is caught
  [VERIFIED-code `live_step0.py:2260-2262`].
- A state load restores the frame counter, which can go backwards. `main.py` then rebuilds the listeners, so the run ends
  with `isolation-lost` [VERIFIED-code `main.py:119-132`, `session.py:278-284`; VERIFIED-mgba `video.c:354`].
- The core's callback lists are snapshotted at install and checked before every frame. A new `savedata_updated` callback
  added mid-run counts as `instrument_tampered` [VERIFIED-code `attribution.py:191-194,775-778,1383-1388`]. The framework's
  own backup callback was registered before install, so it is allowed.
- The sinks do not audit the cartridge save [VERIFIED-code `attribution.py:144-148`]. So "the AI saved" must be graded by
  a second path: the `.sav` itself, the `saves/` copy, or `GAME_STAT_SAVED_GAME` (SaveBlock1 `gameStats` @0x159C, XOR the
  key in SaveBlock2 @0xAC; the offsets are already in `gates/play_harness.py:65-66`, VERIFIED-code).
- ⇒ R1's host work divides cleanly. BETWEEN processes, the launcher may choose, copy, rotate or validate `.sav` files and
  drop a stale `.ss1`. INSIDE a run, only the game's own code touches the save: the start-menu save and a held-button soft
  reset.

---------------------------------------------------------------------------------------------------------------------------

## 4. (c) DP1 / DP2 ground truth: every path builder

### 4.1 Locating the framework and the package
- `launcher.py:81-82` (`ENV_BUILD_ROOT`, `PACKAGE_ROOT = parents[2]`); `launcher.py:113-118` `resolve_build_root`
  (requires `pokebot.py`); `__main__.py:61` (help: "default: ../sandbox-pokebot") [VERIFIED-code].
- `launcher.py:255-256` hook path `<build_root>/plugins/custom_modes/ai_player_mode.py`; `launcher.py:272-281` the gate at
  `<package_root>/ai_player/gates/check_purity.py`, given `--build-root` explicitly. The gate's own default is
  `PACKAGE_DIR.parent / "sandbox-pokebot"` [VERIFIED-code `check_purity.py:148`]. ⇒ The gate ships with the program (DOC
  `02-deployment.md:117-118`).
- The hook: `AI_PLAYER_PACKAGE_ROOT`, else `Path(__file__).resolve().parents[3]` [VERIFIED-code
  `ai_player_mode.py:45-48`]. The session checks `LOADED_FROM = parents[2]` [VERIFIED-code `session.py:86,178-184`]. The
  instrument records `framework_root` from `modules.memory.__file__` [VERIFIED-code `attribution.py:275-277,699`].

### 4.2 Profiles
- `launcher.py:145-176` (under the build root; the donor chain with `PREFERRED_TEMPLATE = "endless-P1-torchic"` at :89),
  `:179-209` (seed and delete), `:133-142` (`http.yml`). The framework resolves the NAME under its own `profiles/`
  [VERIFIED-code `pokebot.py:142-144`].

### 4.3 AI-owned run data (play loop and launcher)
- The run folder: `__main__.py:147` (default inside the profile), `:149-151` (a stale verdict is removed), `:175`
  (`stdout.txt`); `launcher.py:308` (`AI_PLAYER_RUN_DIR`); `options.py:84,279-290,376-377` [VERIFIED-code].
- Files: `runlog.py:22-24,27-33,55-65` (`ai_player.log`, `actions.jsonl`); `mode.py:96,293-296,960-963` (`world.jsonl`);
  `session.py:163` + `options.py:248` (`purity.json`, written by the instrument) [VERIFIED-code].
- Cross-run input: `AI_PLAYER_WORLD` is any path, read by `read_world` (its LAST line, with no guard against a torn last
  line) [VERIFIED-code `options.py:178-180,393-416`, `world/memory.py:864-871`]. Today a DRIVER chains runs by copying the
  clean-close `.ss1` to `<run_dir>/end_state.ss1` and passing the run's `world.jsonl` [VERIFIED-code
  `live_step5.py:450-462,497-507`]. The goal manager's `_Memory` is NOT carried [VERIFIED-code `brain/goals.py:406-474`,
  with its own comment at `:447-450`; a second `_Memory` is in `brain/battle.py:668`].
- No per-PLAYTHROUGH folder for AI files exists. R2's `memory.jsonl` would be the first one [VERIFIED-code: nothing
  matches].

### 4.4 Knowledge (read-only, shipped)
- Package-relative: `knowledge/story.py:28`, `knowledge/facts.py:37`, `personality.py:228` [VERIFIED-code]. This is DP1's
  KNOWLEDGE class and already location-independent.

### 4.5 Version fields today
- None. `purity.json` keys: counters, facts, finish, origins, pid, verdict, written_by. `actions.jsonl` records: action,
  decision, digest, extra, frame, observation, reason. A `world.jsonl` snapshot: maps, warps, connections, transitions,
  tiles_learned, news, heard, news_log, and optionally landmarks and spoke [VERIFIED-disk; VERIFIED-code
  `world/memory.py:801-817`].
- The world reader is tolerant: `.get()` defaults, plus in-place upgrades of older memories [VERIFIED-code
  `world/memory.py:823-852`]. That is DP2's "migrate older" half without a version number, and without "refuse newer".
- Stamps: actions and world transitions carry EMULATOR frames. Those restart at 0 on each cold boot and jump to a
  state's value on a `.ss1` load (A15), so they cannot order memory across sessions.

### 4.6 Gates (test side)
- They use `launcher.resolve_build_root` (12): `inspect_state`, `live_step0`-`live_step5`, `make_step41_fixtures`,
  `make_step4_fixtures`, `make_trainer_fixture`, `probe_eyes`, `rate_step5` [VERIFIED-code grep].
- They hardcode `<repo>/sandbox-pokebot` (16 sites, 13 files): `check_purity.py:148`, `disk_budget.py:37` (PROFILES,
  bypassing the resolver), `extract_knowledge.py:40`, `extract_milestones.py:52`, `live_step1.py:302,418,440`,
  `live_step2.py:433,466`, `live_step3.py:1075`, `rate_step3.py:504`, `rate_step5.py:1799`, `test_eyes.py:70`,
  `test_host.py:61`, `test_battle.py:95`, `test_hands.py:89` [VERIFIED-code]. Several of these read the bot's DATA files
  (teaching material) rather than user data.
- Fixed profile names: `ai-step0-fixture` (`hands_harness.py:41`, `exit_looks.py:39`, `game_answer.py:86`);
  `ai-step0-fresh` and `ai-step0-cheats` (`live_step0.py:2240-2273`); `ai-step3-world`, `ai-step4-battle`, `ai-step5-play`
  (`live_step3.py:469`, `live_step4.py:187`, `live_step5.py:137`) [VERIFIED-code].
- Evidence goes to `<repo>/ai_player/evidence` (`live_step0.py:308`, `live_step1.py:255`, `live_step2.py:176`,
  `live_step3.py:462`, `live_step4.py:185`, `live_step5.py:136`, `disk_budget.py:38`) [VERIFIED-code].

### 4.7 What DP1 meets that the backlog does not say [UNVERIFIED design notes]
- The durable truth (DP4: the `.sav`) is a FRAMEWORK-owned file at a framework-chosen path,
  `<build_root>/profiles/<NAME>/current_save.sav`. An `AppPaths` "user data" class either has to point the framework's
  profile folder into user data, or the launcher has to copy `.sav` files in and out between processes. The play loop
  cannot do either (A12, A15).
- The `saves/` folder already keeps EVERY flushed save, with no retention (§2.2). DP4's "keep the newest 10" is a prune of
  that folder, or a rotation of its own.
- A profile name is a path segment checked by `^[A-Za-z0-9_.-]+$` [VERIFIED-code `launcher.py:106,151-152`].

---------------------------------------------------------------------------------------------------------------------------

## 5. (d) What must be MEASURED before R1 is built, with probe sketches (nothing below was written or run)

### 5.1 The measurements and what would prove each one

| # | Question | Proof | If false |
|---|---|---|---|
| M1 | A TerminateProcess at K0, K1 or K2 after the save call returns leaves the new save in `current_save.sav` | the parent's second-path parse of the file shows the new slot (all 14 sectors valid, one counter, play time = the K0 truth), AND a fresh child's CONTINUE gives the K0 party PIDs, map, tile and play time | a kill loses saves: R1 must make a durability step, for example a launcher-side fsync after the `saves/` copy appears |
| M2 | The timeline of §2.4 in frames: "SAVING…" printed (e2) → first write (e3) → last write (e4) → "saved the game" (e5) → mGBA flush (e6, the `saves/` copy appears and the file becomes 131,088 bytes) → box closed and screen free (e7) | per-frame records in the saver child | if e7 < e6, a "save then stop at once" can end before the flush (harmless for a kill per M1, not for a power cut) |
| M3 | A start-menu save inside a real launcher run keeps the verdict CLEAN (the backup callback writes a file inside a frame) | a launcher run whose brain saves (needs R1's skill, or a plant arm) and `purity.json` CLEAN | R1 needs an instrument change (a reviewed gate change, rule g) |
| M4 | The split-brain of §2.6 | P2 below: which play time the next CONTINUE loads | if it never happens, the stale-`.ss1` rule is hygiene, not a fix |
| M5 | Only if reloads are allowed: a held A+B+START+SELECT soft reset in a launcher run gives no frame-counter drop, no listener rebuild and a CLEAN verdict | in-process: `get_frame_count()` across the reset; then a launcher run with the four buttons held through the controller | a person-like reload needs a host change before it can be pure |
| M6 | `.ss1` refusal: a state from another build or ROM falls back to a SILENT cold boot | load a deliberately corrupted `.ss1` (a fixture whose header magic is bumped), check the first look is the title | if the load errors loudly instead, A6's "silent" is wrong |

### 5.2 Probe P1, `probe_save_kill.py` (sketch; TEST SIDE)
Written in the style of `gates/probe_end_screen.py`: `run` / `selftest` subcommands, a FROZEN `--root` copy of the tree,
one `PROBE {json}` line, the harness's own reads (never the AI's eyes), and a selftest that must both FAIL and PASS. Unlike
every existing probe it needs TWO processes, because a kill cannot be observed from inside. The drivers already run and
kill children [VERIFIED-code `live_step5.py:468-479`, `launcher.py:351-372`].

- **Parent** (no emulator). It makes a throwaway owned profile `ai-r1-probe-<arm>` (with `ensure_profile` and the marker)
  and empties its `.ss1`, `.sav`, `states/` and `saves/`. It launches child A, reads its JSON lines, and at the arm's kill
  point calls `psutil.Process(pid).kill()` (what `kill_tree` does) or, in arm KX, lets the child `os._exit`. It then parses
  the file, deletes any `.ss1`, and launches child B.
- **Child A, the saver.**
  - It boots WITH a file-backed save, `LibmgbaEmulator(profile, cb, is_test_run=False)`, not `probe_eyes.boot`, which
    uses `is_test_run=True` (§2.2). That also registers the framework's `saves/` copy, plus an `atexit` hook that a kill
    skips.
  - It loads a FREE overworld fixture through `emulator.load_save_state(bytes)` (for example
    `gates/fixtures/route101_south.ss1`, already the free fixture of `probe_end_screen.py`; it has no `gbAx` chunk), and
    pins the cartridge clock (`hands_harness.pin_game_clock`) so CONTINUE's time-based events match.
  - It saves with TEST-SIDE presses: START, the cursor read to "SAVE", A, then YES on each prompt read by its words. The
    measurement must not depend on R1's unbuilt skill.
  - Every frame it records:
    - (i) `dirty` and `dirtAge` of the save, through `emulator._core._native.memory.savedata` (the path `read_save_data`
      already uses, `libmgba.py:395`; whether the cffi cdef exposes those two fields is UNVERIFIED, and the fallback is
      comparing `read_save_data()` frame to frame);
    - (ii) the newest valid slot of `read_save_data()`;
    - (iii) the file's size and newest valid slot, read through a second handle;
    - (iv) whether `saves/` holds a file;
    - (v) the message pages (`play_harness.shown_pages`) and the dialog callback symbol (test side may read it);
    - (vi) SaveBlock2's play time from RAM.
  - At K0 (the in-emulator new slot is complete) it records TRUTH: party PIDs, map, x and y, play time, and
    `GAME_STAT_SAVED_GAME`, by the harness's own readers (`hands_harness.truth` style). It runs to the arm's kill frame,
    prints `READY {...}` and then BLOCKS, so the kill lands with no frame in flight.
- **Parent, after the kill.** It reads `current_save.sav` and parses both slots by the decomp layout: footer id u16
  @0xFF4, checksum u16 @0xFF6, signature u32 @0xFF8 = 0x08012025, counter u32 @0xFFC; the checksum is the sum of LE u32
  words over the sector's chunk size, folded `(c >> 16) + c` to u16; the chunk sizes are `_section_sizes` [VERIFIED-decomp
  `include/save.h:74-82`, `save.c:675-687`; VERIFIED-code `sandbox-pokebot/modules/save_data.py:139-200`]. It also checks
  that all 14 counters of the newest slot are EQUAL, which the game itself never checks (A5). From the slot it reads play
  time (SB2 0x0E-0x12), party PIDs (SB1 0x238 + 100·i, personality at +0) and position (SB1 0x00 and 0x04)
  [VERIFIED-decomp `global.h:508-517,984-1001`].
- **Child B, the continuer** (a fresh process, same profile, no `.ss1`). It boots cold and reads `tMenuType` and any error
  window by its text. It chooses CONTINUE with test-side presses, waits for a free overworld (`probe_end_screen.game_screen`),
  then reads TRUTH with the same readers.
- **Verdicts for each arm.** FILE: the newest on-disk slot is the K0 save. GAME: child B's PIDs, map, x, y and play time
  (to the VBlank) equal child A's K0 truth.
- **Arms.** K0 (kill at the save call's return), K1 (+8 frames, before the flush), K2 (+40, after the flush, with the
  `saves/` copy present), KM (mid-save, only if M2 shows the save call spans frames), KX (`os._exit` instead of
  TerminateProcess), CLEAN (`sys.exit`; the control, which must also leave a `.ss1`).
- **Discriminator FIRST** (CLAUDE.md Tier 2 (4); LESSONS PF-10).
  - NOSAVE (a kill before SAVE is chosen) must read FILE = empty, with no CONTINUE in child B. This proves "saved" is not
    true by construction.
  - ANON (child A with `is_test_run=True`, anonymous flash) must read FILE = empty. This proves the file check really reads
    the file.
  - TRUNC (the parent cuts the file to 64 KB before child B) must make the GAME say corrupt or erased. This proves child B
    reports the game's own judgement.
- **What P1 cannot prove:** that a save survives a power cut. That needs a virtual machine with a hard power-off, outside
  this PC's safe reach.

### 5.3 Probe P2 (the split-brain, M4)
In a throwaway profile:
1. Run a clean session to T0, so a `.ss1` is written.
2. Start a no-flag resume, save at T1 and at T2, then TerminateProcess.
3. Start another no-flag resume. Check that it starts at T0 (its first look's play time).
4. Save at T0', then cold boot (delete the `.ss1`) and CONTINUE.
5. Which play time loads, T2 or T0'?

§2.6 predicts T2. Each step is a launcher-level action plus the same parent-side `.sav` parse; the saves use test-side
presses or R1's skill.

### 5.4 Probe P3 (soft-reset purity, M5; only if the user allows reloads)
- (1) In-process: `get_frame_count()` before and after holding A+B+START+SELECT on a free fixture must not decrease. mGBA's
  `_SoftReset` touches CPU registers only, and the frame counter is reset only in `GBAVideoReset` [VERIFIED-mgba
  `bios.c:38-50`, `video.c:79`]. The game reboots through the intro, then `LoadGameSave`, then the title [VERIFIED-decomp
  `src/main.c:135-141,428-437`, `intro.c:1147-1159`].
- (2) A launcher run where the brain (a plant, as in `live_step0`) holds the four buttons through the controller must keep
  `isolation_lost = 0` and `foreign_loads = 0` and end CLEAN.

### 5.5 The cheapest first measurement
- M2 alone needs only child A's per-frame records, with no kill. It also answers whether step 6 spans frames (the KM arm),
  and it gives R1 a frame budget for one save dialog at unthrottled speed.

---------------------------------------------------------------------------------------------------------------------------

## 6. The user's two open questions: what each answer changes on the host and emulator side (NOT decided)

Asked on 2026-10-28 at 5:27 PM and still unanswered: "when the AI saves, and may it reload to undo a loss" [DOC
`04-HANDOFF.md:61`]. Context: for the BOT, the user asked to "continue where it left off in the event that the bot gets
turned off during sudden power loss OR I turn it off" (USER RULING B, 2026-08-14) [DOC `06-DECISIONS-LOG.md:2236-2248`].
That ruling covers the bot, not the AI. Whether it extends to the AI is the user's call.

**Q1. When does the AI save?** Every option needs the stale-`.ss1` rule (§2.6) and treats the `.sav` as the truth.
- **Only before a planned stop (done or session end).** The brain must see the end coming. Today the soft deadline is
  enforced by the GUARD on the deadline frame, with no brain turn [VERIFIED-code `session.py:305-310`]. The frame bounds
  are the brain's `_bounded` and the session's cap [VERIFIED-code `mode.py:965-978`, `session.py:299-304`]. R5's settle
  already reserves `DONE_BUDGET_MARGIN` [VERIFIED-code `mode.py:699-704`], and a save dialog adds M2's frames on top. A
  hard kill loses the whole session.
- **At a person's moments (after a heal, before a boss, after a milestone).** The kill exposure is the time since the last
  such moment. Every save is a free-screen detour (R5) and adds one copy of about 128 KB to `saves/`, which has no
  retention [VERIFIED-code `libmgba.py:243-256`]. DP4's "keep the newest 10" becomes needed early.
- **Periodically.** The same as above, plus a clock. It must be the GAME's play time or frames, not the wall clock, because
  the run is unthrottled [VERIFIED-code `launcher.py:216` `-s 0`].
- **Never by itself (only when the user stops it).** R1 then shrinks to CONTINUE plus the resume rule, and every kill
  loses everything since the last stop.

**Q2. May the AI reload a save to undo a loss?**
- **No (the backlog's default, "No save-scum").** CONTINUE happens only at process start. R2's "memory not newer than its
  save" is applied only when a session starts. The defeat ledger (R11) counts every loss. No new purity question arises.
- **Yes, the way a person does it** (hold A+B+START+SELECT, then CONTINUE) [VERIFIED-decomp `main.c:135-141,428-437`,
  `intro.c:1147-1159`]. This needs:
  - M5 (purity of a soft reset);
  - a MID-RUN memory rollback (R2's stamp then filters memory inside a session, not only at start);
  - a ruling on what the AI may remember of the undone attempt (RULING 40 allows remembering past GAMES; whether an undone
    fight counts is the user's call);
  - the defeat ledger still counting the undone loss;
  - graded runs saying that a reload happened (R8 + R9 / L11: "counts only from the AI's own chain").
- **Yes, through the emulator** (a state load or `load_save_game`). This is a purity BREACH by design (plant arms XL, XN
  and XS). It would need a sanctioned door in the pinned instrument, and it reads as contrary to RULING 35's "the AI plays
  the game itself" [UNVERIFIED reading; ask].

---------------------------------------------------------------------------------------------------------------------------

## 7. Corrections to the backlog's evidence lines

- "the resume file is written on a CLEAN close only (`libmgba.py:141`)": line 141 is the comment at the LOAD site. The
  writer is `shutdown()` at `libmgba.py:231-241`, registered with `atexit` at `:159-160`. The statement holds for the
  `.ss1`. It does NOT hold for the `.sav`, which reaches the file on every write (A1, A3).
- "`_Memory` is not carried (`brain/goals.py:62`)": `_Memory` is at `brain/goals.py:406-474`, and the "not carried" fact
  is in its own comment at `:447-450` [VERIFIED-code]. Line 62 today is docstring text.
- "a profile needs a donor (`launcher.py:89,145-165`)": that is right for the DONOR. The LOCATOR is `launcher.py:113-118`
  (A13).
- "UNVERIFIED first: does mGBA flush the save before a kill?": for a process kill, mGBA does not need to flush (A4). For a
  power cut, its flush is `FlushViewOfFile` only, about 16 frames after the last write (A2).
- DP4's "keep the newest 10": the framework already keeps EVERY flushed save, with no retention (§2.2).

## 8. Not checked here (other angles, or needing a live run)

- Whether the shipped `mgba.dll` is unpatched 0.10.2; whether `ffi.gc` deinit runs at exit; whether the cffi cdef exposes
  `savedata.dirty`; Windows' read-through-mapping coherence; whether psutil's kill is TerminateProcess.
- The number of emulated frames step 6 takes (M2); the length of the save dialog at the AI's speed; power-cut behaviour.
- The words-reading save and CONTINUE skills, R2's schema and stamp source (whether reading exact play time from RAM is
  person-fair under RULING 40), and L3's roles: other angles. Host fact for them: the LAUNCHER can read a `.sav`'s play time
  and `GAME_STAT_SAVED_GAME` between processes, outside the AI's perception (§3.5, §5.2).
