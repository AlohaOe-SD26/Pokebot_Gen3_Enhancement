> ✅ **MEASURED 2026-10-29** (`07`; decision `06` 2026-10-29). Backlog R1 + R2's prerequisite: the TEST-SIDE probe `ai_player/gates/probe_save_kill.py` (in no lane; it needs the emulator, the ROM and a framework copy with `mgba/`) and its evidence `ai_player/evidence/2026-10-29-r1probe-PROBE.txt` (the build and fix rounds) and `2026-10-29-r1probe-FINAL.txt` (every check re-run on the committed text). VERBATIM below section 0: the build report (session scratch `s53/r1probe/build/BUILD-REPORT.md`, sha256 `039da52d78746e42`) with its FIX ROUND section; its FR7 supersedes the builder's sections where they differ. These are MEASUREMENTS on ONE fixture (`route101_south.ss1`), one trajectory replayed, at held-out kill offsets; what was NOT measured is in its §8 and FR8 (no power cut, no fourth save, one fixture, one text speed).

# R1 + R2's save/kill probe: what a save does in frames, and what a process kill leaves for the next process

## 00. The orchestrator's checks (2026-10-29, on the main checkout, the probe applied, uncommitted)

- **Applied to `main`** (6:16 AM): the worktree's two new files byte for byte, the probe (sha256 LF `1030c2bf92cc0a60`, 1,754 lines) and its evidence (579,685 bytes, sha256 LF `1462aaf66b0ba0ed`); no tracked file changed. On that text: the selftest PASS (24 cases) and each planted fault FAILS (6:17 AM); a held-out live run, below, 11 of 11 (6:18 AM).
- **The held-out offsets:** kill offsets that no earlier run used (KM-FIRST 1, 37, 233; KM-SECOND 0, 19, 111; KM-THIRD 1, 99, 240), plus ANON and K2, with my expectations written first (session scratch `s53/r1probe/verify2/PREREGISTER-heldout.txt`, written 6:18:12 AM by its file time, though its text says "about 6:27 AM", a misread clock). First run 6:18:19 to 6:19:17 AM: `graded 11, passed 11, failed []`, `children_alive []`; every FILE and GAME verdict is the one written down, ANON differs from K2, and M2's three writes took 257, 261 and 256 frames with the flush 16 frames after each, as in the earlier runs (a determinism check, not a replication).
- **The fix round's own review:** one independent reviewer (6:21 to 6:45 AM) returned KICK-BACK on one MINOR, wording only, with no measurement or verdict affected: "child A never reads the file's bytes" is false for the PROCESS, because the framework's flush backup (`libmgba.py`) reads the whole file at each flush (in the NOREAD arms once, at S1's flush, 735 frames before S2's write); its questions found no misfire of "+MIXED" (the loaded slot only), the expectations registered before the run, the default offsets computed from M2 at run time, MIXED's splice as claimed (its fault tree differs by one line), the builder's 21 arms unchanged and no unbounded wait, and two guards with no selftest case (its in-memory mutants "either slot" and "status guard dropped" passed the selftest).
- **The final round on `main`** (after that review): the wording fixed in the probe's docstring, two comments and two arms' `why` strings; `km_arms`' reasoning for KM-THIRD completed (the rotation moves two sectors, so every in-order cut leaves an id missing); two CONTROL selftest cases added (a slot NOT loaded made uneven: no suffix; a parity pointing at an EMPTY slot: NONE). The committed probe: 1,780 lines, sha256 LF `627dc2d7a3758943`. Re-run on it: the selftest PASS (26 cases), each of the four planted faults FAILS, and the review's two in-memory mutants each FAIL exactly their CONTROL case while the unmutated runner PASSES; every arm `graded 37, passed 37, failed []` with all four discriminators differing from K2 (6:50 to 6:53 AM); the held-out offsets again `graded 11, passed 11` (6:53 to 6:54 AM; the same trajectory replayed) (`ai_player/evidence/2026-10-29-r1probe-FINAL.txt`). Left as they are (review nits): KM-THIRD and K2-THIRD carry a `spec` attribution to the spec's general claims 4 and 5, though the spec has no third-save arm; FR2's "37 rows" counts parses (TRUNC has two: 36 rows); FR6's "claim 3 refuted" refutes the estimate, while its "or more" holds.
- **Pre-commit:** (on the committed probe text, 6:50 to 7:05 AM, before this text was written) `run_gates.py --quick` `ALL 141 ENFORCING GATES PASS` (+2 advisory probes; 839.8 s); `run_regression.py --quick` `REGRESSION: PASS (quick, 19 suites, 17.4 s wall)`; `regression_due.py`: units, revert_step5 and revert_safety_gates DUE on the new probe file (units and the safety gates also on `07`), so the full lane runs after the commit.

## 0. What it measured, in plain words (for R1 + R2's design; nothing here decides WHEN the AI saves)

- **One save's flash write takes 256 to 261 frames** (about 4.3 seconds of game time), not "about 133"; from START to a free screen the whole save takes 756 to 969 frames.
- **mGBA flushes the file 16 frames after the last write**, 66 frames BEFORE "{PLAYER} saved the game." is fully printed.
- **A process kill after the write is complete keeps the new save**, even before the flush and with the probe's own file reader switched off (K0, K1, KX, K1-NOREAD, KX-NOREAD; the framework's flush backup still read the file once, at the save before). This is what the NEXT process sees through the OS cache; a power cut was not tested.
- **A kill DURING the write:** a FIRST save on a fresh cart shows "The save file has been erased..." and offers NEW GAME only (nothing is kept); a later save shows "The save file is corrupted. The previous save file will be loaded." and CONTINUE loads the save before it.
- **EXCEPT the silent window:** a kill before the write's first sector is complete (its first 18 or 19 frames) in the first or second save of a fresh cart shows NO page at all: the first save leaves no save, the second loads the first silently. A third save has no such window (its first write breaks the oldest slot at once).
- **A `.ss1` with a bumped version magic gives a silent cold boot** (the framework ignores the core's `load_state` False).
- **For R1's design:** the AI's dialogue stall bound (`ai_player/hands/dialogue.py` STALL_FRAMES 300) has only about 1.15x headroom over a 261-frame write with nothing changing on screen, not the 2.3x the refute note computed from 133 (not yet measured with the AI's eyes).

---

# R1 + R2 prerequisite: `probe_save_kill.py` (build report)

Written 2026-10-29, 5:12 AM (Los Angeles) by the R1 probe builder. Worktree:
`C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/wf_af0d459e-08e-1` (HEAD `1fc0b8e7`). Nothing was
committed, staged or stashed. Every number below is copied from a saved file in this folder (`s53/r1probe/build/`),
named beside it. The measured runs: the selftest at 5:00:15 AM, M2 alone from 5:00:31 to 5:00:36 AM, every arm from
5:00:58 to 5:02:29 AM, and the four checks from 5:04:28 to 5:04:31 AM.

## 1. What was built

One new file, `ai_player/gates/probe_save_kill.py` (1,583 lines). It is test side and development only: it is not wired
into `run_gates.py` or the regression lane. Its pattern is `probe_end_screen.py`: `run` and `selftest` subcommands, a
FROZEN `--root` copy, one `PROBE {json}` line per arm plus `PROBE SUMMARY {json}`, the harness's own reads, and a selftest
that can FAIL and PASS. There is one more subcommand, `child`, the internal entry of the child processes.

- **Parent** (no emulator). For each arm it makes a fresh throwaway profile under `--out/<arm>/profile`, holding
  `metadata.yml` copied from `ai-step0-fixture` (read only) and an empty `current_save.sav`. It then runs the children
  one at a time, each with a timeout. At READY it kills child A with `psutil.Process(pid).kill()` on the PID it started,
  and only that PID. It parses the file (FILE verdict), deletes any `.ss1`, starts child B (GAME verdict), and checks at
  the end that no child is left alive.
- **Child A, the saver.** It runs `LibmgbaEmulator(is_test_run=False)`, so the save is file-backed, the atexit `.ss1`
  is written on a clean exit, and the `saves/` backup is copied. It loads `route101_south.ss1` and pins the clock
  (`pin_game_clock`, GAME_CLOCK 2026-10-14T10:00), then saves with test-side presses:
  1. START, then the cursor moved onto SAVE by reading `sStartMenuCursorPos` and `sCurrentStartMenuActions`.
  2. A, then A on YES at each question. Each question is read by its words through `play_harness.shown_pages`.
  3. No input until the box closes by itself.

  Between the two saves it walks one tile, choosing the direction from the framework's tile read. Every frame goes to
  `a_frames.jsonl` with these fields:
  - mGBA's `dirty` and `dirtAge` (the cffi `GBASavedata`);
  - both slots of `read_save_data()`;
  - both slots of the file, read through a second handle, and the file's size;
  - the `saves/` folder;
  - `sSaveDialogCallback` and `gMenuCallback` by symbol;
  - text printer 0 and the message pages;
  - the play time in RAM;
  - `probe_end_screen.game_screen()["free"]`.

  It also records a listener appended after the framework's own `savedataUpdated` callback.
- **Child B, the continuer.** It is a fresh file-backed process on the same profile, with the clock pinned and the
  framework's atexit `.ss1` unregistered. From power-on it presses START every 20 frames until a main-menu task exists.
  It reads each error page by its words, from text printer 7's own string (`printer_page`, below), and then the menu's
  `tMenuType`. If CONTINUE is offered it presses A on it, with the cursor read on CONTINUE. It then waits for a free
  overworld, held 10 frames, and takes the truth there: PIDs, map and tile by RAM, cross-checked by `hands_harness.truth`.
- **Verdicts.**
  - FILE is a port of `GetSaveValidStatus` (pinned decomp `src/save.c`). It gives EMPTY or CORRUPT, or the save that the
    loaded slot holds (S1, S2 or OTHER), with "+ERROR" when the other slot is broken. It also checks that all 14
    sector counters are equal.
  - GAME is "CORRUPTED PAGE + " or "ERASED PAGE + " when that page appeared, then "NEW GAME ONLY", or the save that
    CONTINUE gave.
  - A save is S1 or S2 only when the PIDs, the map, the tile and the play time all match. The play time comes from the
    boot read (exact to the VBlank); CLAUDE.md rule 3.
  - Each arm also carries the BUILD SPEC's own expectation (`spec_expected` / `matches_spec`). Disagreements are listed in
    the summary and are never graded away.

## 2. The selftest: PASS, and each planted fault FAILS

Outputs: `selftest.out`, `selftest-no_checksum.out`, `selftest-no_identity.out` and `selftest-ignore_pages.out`.
- The clean run gives `SELFTEST VERDICT: PASS`, `EXIT CODE 0` (20 cases).
- `--fault no_checksum` gives `SELFTEST VERDICT: FAIL (fault no_checksum: failed ['FAULT INPUT one data byte flipped:
  that slot is ERROR, the cart CORRUPT'])`, `EXIT CODE 1`.
- `--fault no_identity` gives `SELFTEST VERDICT: FAIL (fault no_identity: failed ['two saves: OK, the counter-2 slot
  loads, and it is S2', 'FAULT INPUT the file cut to 64 KB: ...: S2+ERROR', "FAULT INPUT a netted-out save ... is neither
  save"])`, `EXIT CODE 1`.
- `--fault ignore_pages` gives `SELFTEST VERDICT: FAIL (fault ignore_pages: failed ['a continuer that met the corrupted
  page and loaded S1', 'a continuer that met the erased page and no CONTINUE'])`, `EXIT CODE 1`.

## 3. M2, the timeline, measured FIRST (`M2-only.out`; replayed identically as the first arm of `ALL.out`)

Frame numbers are the emulator's count after the frame. The fixture loads at frame 66883.

| event | save 1 (one question) | save 2 (two questions, after one tile Up) |
|---|---|---|
| e1 START pressed | 66924 | 67723 |
| e2 "SAVING…" fully printed | 67238 | 68246 |
| e3 first flash write (`e3_dirty`; `e3_data`, the first changed byte) | 67238 (67238; 67239) | 68246 (68246; 68247) |
| e4 new slot complete in the emulator (= `e4_last_write`, = `e4_last_change`) | 67495 | 68507 |
| e5 "NICK saved the game." printed (= `e5_jingle`) | 67577 | 68589 |
| e6 flush: mGBA's callback (= `e6_saves`; `e6_size`) | 67511 (67511; 67511, 131072→131088) | 68523 (68523; no size change, stays 131088) |
| e7 the screen free, held 10 frames | 67680 | 68692 |
| derived: write e4−e3; flush e6−last write; free e7−e6; whole dialog e7−e1 | 257; 16; 169; 756 | 261; 16; 169; 969 |

Other facts from the same records:
- The sectors complete every 18 or 19 frames: save 1 at 67257 (id 0, e3+19) … 67495 (id 13); save 2 at 68264 … 68507.
- In the per-frame record (`runs/ALL/M2/a_frames.jsonl`, frames 67234-67240 and 67494-67512):
  - the play time stood still from 67237 to 67495 at [0,17,22,6]: the main loop is frozen during the write;
  - printer 0 was active at 67237 and idle at 67238, which is the frame mGBA's dirt first moved;
  - at 67511, mGBA's dirt cleared, the file size went to 131088, the `saves/` copy appeared and the listener fired, all
    on the same frame.
- The second-handle file read equalled the emulator's 128 KiB flash on every recorded frame of both saves
  (`file_neq_flash_frames` count 0). The new slot became complete in the file at e4, 16 frames before the flush.
- The truth read during the write equals the new slot's own bytes at e4, in the emulator and in the file
  (`slot_at_e4_*_equals_truth` true, both saves). Save 1 is PIDs ["550a9be6"], map [0,16], tile (11,19), play time
  [0,17,22,6]. Save 2 is the same PIDs and map, tile (11,18), play time [0,17,34,33].
- GAME_STAT_SAVED_GAME was 0 at the start and 1 in RAM during save 1's write. It rises before the write (refute note N6).
- KM offsets were chosen from this table (the probe's defaults: 2, a quarter, a half, three quarters, e4−e3−1):
  - `--km-first 2,64,128,192,256`, with 0, 3, 7, 10 and 13 sectors complete;
  - `--km-second 2,65,130,195,260`, with 0, 3, 7, 10 and 13 sectors complete.

## 4. Every arm (`ALL.out`, 5:00:58-5:02:29 AM; `ALL.summary.txt` is a read-only digest)

| arm | registered expectation (FILE / GAME) | FILE verdict | GAME verdict | pass | the spec's section-1 expectation |
|---|---|---|---|---|---|
| NOSAVE (discriminator) | EMPTY / NEW GAME ONLY | EMPTY | NEW GAME ONLY | true | matches |
| ANON (discriminator) | EMPTY / NEW GAME ONLY | EMPTY | NEW GAME ONLY | true | matches (GAME unspecified) |
| TRUNC (discriminator) | S2+ERROR / CORRUPTED PAGE + S2 | S2+ERROR | CORRUPTED PAGE + S2 | true | matches ("corrupt or erased") |
| KM-FIRST@2 | EMPTY / NEW GAME ONLY | EMPTY | NEW GAME ONLY | true | **DISAGREES**: the spec expected the erased page |
| KM-FIRST@64 | CORRUPT / ERASED PAGE + NEW GAME ONLY | CORRUPT | ERASED PAGE + NEW GAME ONLY | true | matches |
| KM-FIRST@128 | CORRUPT / ERASED PAGE + NEW GAME ONLY | CORRUPT | ERASED PAGE + NEW GAME ONLY | true | matches |
| KM-FIRST@192 | CORRUPT / ERASED PAGE + NEW GAME ONLY | CORRUPT | ERASED PAGE + NEW GAME ONLY | true | matches |
| KM-FIRST@256 | CORRUPT / ERASED PAGE + NEW GAME ONLY | CORRUPT | ERASED PAGE + NEW GAME ONLY | true | matches |
| KM-SECOND@2 | S1 / S1 | S1 | S1 | true | **DISAGREES**: the spec expected S2's slot torn and the corrupted page |
| KM-SECOND@65 | S1+ERROR / CORRUPTED PAGE + S1 | S1+ERROR | CORRUPTED PAGE + S1 | true | matches |
| KM-SECOND@130 | S1+ERROR / CORRUPTED PAGE + S1 | S1+ERROR | CORRUPTED PAGE + S1 | true | matches |
| KM-SECOND@195 | S1+ERROR / CORRUPTED PAGE + S1 | S1+ERROR | CORRUPTED PAGE + S1 | true | matches |
| KM-SECOND@260 | S1+ERROR / CORRUPTED PAGE + S1 | S1+ERROR | CORRUPTED PAGE + S1 | true | matches |
| K0 (S2.e4+0, frame 68507) | S2 / S2 | S2 | S2 | true | matches |
| K1 (S2.e4+8, frame 68515) | S2 / S2 | S2 | S2 | true | matches |
| K2 (S2.e4+40, frame 68547) | S2 / S2 | S2 | S2 | true | matches |
| KX (os._exit at 68515) | S2 / S2 | S2 | S2 | true | matches |
| CLEAN (sys.exit at 68547) | S2 / S2, a .ss1 left | S2 | S2 | true (`current_state.ss1` + `states/2026-10-29_05-02-21.ss1` left) | matches |
| ERASE28 (beyond the spec) | S1, sectors 28-31 erased | S1 | not run (no continuer) | true | n/a |
| M6 (bumped magic 0x01000008) | COLD BOOT (silent) | COLD BOOT (silent) | n/a | true | matches |
| M6-CONTROL (beyond the spec) | FIXTURE LOADED | FIXTURE LOADED | n/a | true | n/a |

`PROBE SUMMARY` reports `"graded": 21`, `"passed": 21` and `"failed": []`. Each discriminator differs from K2 (S2 / S2):

| discriminator | FILE, GAME |
|---|---|
| NOSAVE | EMPTY, NEW GAME ONLY |
| ANON | EMPTY, NEW GAME ONLY |
| TRUNC | S2+ERROR, CORRUPTED PAGE + S2 |

`spec_disagreements` lists KM-FIRST@2 and KM-SECOND@2. The summary also gives `children_alive` [] and
`descendants_alive` [], with 40 children. `alive_check.out` (read only, 5:03:05 AM) reports "VERDICT: NONE ALIVE": none
of the 80 PIDs the two summaries list is alive, and no process on this PC names `probe_save_kill.py`.

Details by arm. The page texts are the game's own, read from printer 7: `gText_SaveFileErased` "The save file has been
erased due to corruption or damage." and `gText_SaveFileCorrupted` "The save file is corrupted. The previous save file
will be loaded.".

- **Process control.** Every kill exited with code 15 (psutil's TerminateProcess). Every child whose descendants the
  parent listed had one `conhost.exe`, which the probe never killed and which was gone afterwards. KX's and ERASE28's
  savers exited before the listing ran, so none were seen for them.
- **K0 and K1 were killed, and KX ended by `os._exit`, BEFORE S2's flush.** At the stop, mGBA's dirty was 2 and only
  one flush had happened, yet the next process got S2. K2 and CLEAN stopped after the flush (dirty 0, two flushes).
- **ANON.** The emulator flash held S2 complete (`new_sectors_at_stop` 14) while the file stayed 0 bytes
  (`slot_at_e4_file_equals_truth` false).
- **TRUNC.** After the cut the slots were ["OK",2,14] and ["ERROR",1,2]. Child B saw gSaveFileStatus 255, then the
  corrupted page, then CONTINUE gave S2. mGBA grew the file back to 131072 bytes at child B's boot.
- **KM-FIRST.** At 64 and above, gSaveFileStatus was 2 (CORRUPT) and tMenuType 0. At 2, it was 0 (EMPTY) with no page.
- **KM-SECOND.** At 65 and above, gSaveFileStatus was 255 (ERROR), there was a page, and CONTINUE gave S1. At 2 it was 1
  (OK) with no page, and S1 loaded.
- **ERASE28.** At save 1's start, sectors 28-31 read "zero" in the file and in the emulator. After the save they read
  "erased".
- **M6.**
  - Bumped magic: `frame_after_init` 0, callback2 CB2_InitCopyrightScreenAfterBootup at 13 and MainCB2_Intro at 176, no
    overworld in 300 frames, no exception, and nothing printed beyond the normal header. The core's own
    `load_state` returned False, and the framework ignores it.
  - Control (unbumped): `frame_after_init` 66883, CB2_Overworld at 66884, and the core returned True.

## 5. The section-0 claims, against the measurement

1. **CONFIRMED.** The file is writable and its pages hold each written byte. mGBA's struct read FLASH1M, file-backed,
   mapMode 2 (MAP_WRITE) at boot and after the fixture load. The 0-byte file was grown to 131072 bytes and mapped. The
   second-handle read equalled the emulator's flash on every frame of both saves, including mid-write. Proven at frame
   granularity, through the OS cache; ANON is the control.
2. **CONFIRMED.** The flush comes 16 frames after the last write in both saves. The `saves/` copy appears on that same
   frame, and so does the first size change (131072→131088).
3. **REFUTED as an estimate; its lower bound holds.** The write spans 257 frames (save 1) and 261 frames (save 2), not
   "about 133". That is about 1.95× the arithmetic, at 18-19 frames per sector instead of 9.5.
4. **CONFIRMED for a process kill and `os._exit`.** K0 and K1 (killed) and KX (`os._exit`) ended before S2's flush, and
   K2 after it; all gave S2 in FILE and GAME. A power cut was not tested.
5. **PARTLY REFUTED.** The claim holds whenever at least one sector of the new slot was complete: 8 arms gave the erased
   page (first save) or the corrupted page plus S1 (second save). It is refuted for a kill inside the write's FIRST
   sector (e3+2, about 18 frames long):
   - First save: the slot is EMPTY. NEW GAME only, with no "erased" page.
   - Second save of a fresh cart (the target slot never written): status OK, and **S1 loads SILENTLY, with no page**.
6. **CONFIRMED, for `route101_south.ss1` only** (the other 17 fixtures were not run).
   - RAM after the load was gSaveFileStatus 0, gSaveCounter 0, gLastWrittenSector 0, gDifferentSaveFile 1.
   - The first save asked one question. It erased sectors 28-31 (ERASE28) and wrote counter 1 into the second slot, with
     id 0 at sector 15 and id 13 at sector 14.
   - The second save also asked "There is already a saved file. Is it okay to overwrite it?". One A with no cursor move
     took YES, and it wrote counter 2 into the first slot.
7. **CONFIRMED for a bumped header magic.** The result is a silent cold boot. A `.ss1` from another build or ROM was not
   tested.

The ⚠ note (a second handle sees the mapped bytes, flushed or not) is CONFIRMED. The file showed save 1 complete at
67495, 16 frames before the flush at 67511. So the FILE verdicts measure what the next process sees, never the disk.

## 6. The four checks, run in the worktree with `py -3.12 -B`

| check | output file | exit | last line |
|---|---|---|---|
| `check_purity.py` | `gate-check_purity.out` | 0 | `VERDICT: PASS` |
| `check_fairness.py` | `gate-check_fairness.out` | 0 | `PERSON-FAIR DATA DOOR: PASS (0 breaches)` |
| `call_census.py` | `gate-call_census.out` | 0 | `CALL-SITE CENSUS: PASS` |
| `tools/workflows/regression_due.py` | `gate-regression_due.out` | 1 | `5 of 5 suites due` |

- No check objected to the new file.
- `regression_due` names `probe_save_kill.py` as the change behind units, revert_step5 and revert_safety_gates. It also
  names `PROJECT KNOWLEDGE/07-CHANGELOG.md`, which differs between this worktree's HEAD and the evidence commit
  7d89fe07.
- rate_step5 and live_step5 were already due on older evidence. The lane was not run (the orchestrator runs it).

## 7. Deviations from the spec, and why

1. **Build root.** This worktree's `sandbox-pokebot/` has no `mgba/`, which git does not track. So every child imported
   the framework from the MAIN checkout's `sandbox-pokebot` (`AI_PLAYER_BUILD_ROOT`), read only, with `-B` and
   `PYTHONDONTWRITEBYTECODE=1`. A `find` after the runs listed nothing under it modified since 4:40 AM. In the whole main
   checkout, only the lane's `ai_player/evidence/2026-10-29-step52-REVERT.txt` and `REMOTE START/logs/session.lock`
   changed, and neither is mine.
2. **Profiles.** They live under `--out`, because `modules.profiles.load_profile` takes any folder holding a
   `metadata.yml`. No `ai-r1probe-*` profile was created under `sandbox-pokebot/profiles/`.
3. **Extra arms.** ERASE28 measures claim 6's erase, which no spec arm sees: an empty `.sav` is already 0xFF. Its `.sav`
   starts with sectors 28-31 zeroed instead of empty. M6-CONTROL is there so that M6 can tell the two outcomes apart.
4. **KM offsets.** There are five per family instead of "at least three": 2 (inside the first sector) and e4−e3−1 are
   added.
5. **KM expectations** were registered per offset, from M2's sector record. For offset 2 this differs from the spec's
   section-1 text. The measurement agreed with the registration, and both disagreements are reported, not tuned away.
6. **The GAME play time** comes from child B's boot read: the slot copied into RAM at power-on, before CONTINUE, which is
   exact. The map, tile and PIDs come from the held free overworld after CONTINUE. The play time there is recorded too
   (it has moved on).
7. **Child B pins the cartridge clock.** The spec names this only for child A; it is added here for determinism. Child B
   also unregisters the framework's atexit `.ss1`, so it leaves no state.
8. **The flush has a third mark beside the spec's two** (the `saves/` copy and the size): a probe listener appended to
   mGBA's `savedataUpdated` callbacks, after the framework's copy.
9. **M6 uses the framework's own startup auto-load** (`current_state.ss1` in the profile). The core's bool return is asked
   separately, after the observation.
10. **`e3` is the earlier of mGBA's dirt moving and the first changed byte.** On the development ANON arm, mGBA never
    cleans without a file. Its dirt stays set after the first save, which made save 2's `e3` fire on its first frame, so
    the data change is the fallback. In ANON, `e4_last_write` therefore reads 1 and means nothing.
11. **Line endings.** This checkout holds every committed file with CRLF, while the two new files are LF as written. The
    probe that ran has these identities (`hashes.out`):
    - sha256 (LF) `829ddbe048941e0546fc3ce048866e2cb9a67cfd311b36d44692cc23c779e87e`;
    - sha256 (CRLF) `61bc556a6b2d1d94d6f77b81a9f78cb3c14fe38ae03795f0a0567ae3ed7015ee`;
    - git blob `96283fc7ccf7c1ec711ef6b22b05e2b0271675c9`.

    The evidence file has these identities:
    - sha256 (LF) `fcba855f61ffbb512563c8340d24c9ec12e338354e85d28234fdc2cf262c4737`;
    - sha256 (CRLF) `cc6f5fe1069c52b10d94a60ad77fc05dcd1ec5a1e08ccb2db4564096397049ef`;
    - git blob `3f1151a04263a24095d0ff5ebb3ff740b4816b98`.

    Its code line reads digest `ba952a4c6e0c6189` (the probe as the one untracked file; the evidence folder is outside
    that scope).
12. **`printer_page`.** A finished text printer's `currentChar` stands one past the terminator, which is the next
    symbol's start. The probe therefore looks the string up from the byte before. `probe_eyes.printer_text` would look up
    the pointer itself; that is read from its code and was not run. This affects only the main menu's error pages.

## 7b. Development runs (not the evidence)

Three development runs came before the final frozen copy (`tree/final`, sha256 as above): `runs-dev1-m2.out`,
`runs-dev2.out` and `runs-dev3.out`, under `runs/dev*`. In dev3, all 21 graded arms also passed. They led to these
changes, each made before the final runs:
- `e5_jingle` must follow e4. `sSaveDialogCallback` still names the last dialog's SaveReturnSuccessCallback when the next
  save starts.
- ANON's save-2 `e3` falls back to the first changed byte. In dev3 the old rule read save 2's truth on its first frame.
- The descendants are listed and checked gone.
- Each arm carries the spec's own expectation, and the discriminators are checked against K2.
- More selftest cases, and the default KM offsets 2 and e4−e3−1.

`alive_check_final.out` (5:13:57 AM, read only) covers every summary, the development runs included: 163 PIDs, none
alive, and no process naming `probe_save_kill.py`.

## 8. What was NOT done

- No commit, add, stash or other git change, and no full regression lane or `run_gates.py`.
- No edit to the main checkout, the bot tuner's clone or its processes, `sandbox-pokebot/`, `custom-pokebot/`,
  `40cakes repo/`, `PROJECT KNOWLEDGE/` or `ai_player/README.md`. The README lists probes and does not list this one.
- M3, M4 and M5 were not built, as the spec says.
- Not run: the 17 other fixtures, a THIRD save, a power cut, another mGBA build's `.ss1`, a different text speed, and
  the AI's own eyes, hands or brain.
- The runs are one trajectory replayed: M2 alone and M2 in `ALL.out` gave identical frames. That is a determinism check,
  not a replication.

## 9. Open questions (for the orchestrator; nothing here is decided)

1. **The silent window.** A kill in the first ~18 frames of the write of the SECOND save of a fresh cart loses that save
   with NO error page (KM-SECOND@2). The offline cut model in the selftest says a 3rd or later save cut inside its first
   sector still gives ERROR and the corrupted page, because the erase destroys an old sector. That was not measured
   live. Does R1 need a live third-save arm?
2. **The write is 257-261 frames with no change on screen.** `ai_player/hands/dialogue.py` STALL_FRAMES is 300 (900 when
   the scene is named), so `advance` has about 1.15× headroom, not the 2.3× the refute note computed from 133. This was
   not measured with the AI's eyes.
3. **The flush comes BEFORE "saved the game." is fully printed** (e6 is 66 frames before e5, and 169 before the free
   screen). A save that waits for the free screen is flushed by then, as far as mGBA's `FlushViewOfFile` goes.
4. **Claim 6 holds only where gDifferentSaveFile is 1.** It is true for route101_south. Whether every fixture behaves the
   same was not measured live; the refute note's offline parse says the RAM values agree.
5. **TRUNC's 64 KB cut is exactly mGBA's 0xFF-fill threshold.** By `GBASavedataInitFlash`, the regrown half is zero-filled
   rather than 0xFF, which was not checked byte by byte. Either way it carries no signature.

---

## FIX ROUND (2026-10-29, 5:52 to 6:14 AM Los Angeles, by the R1 probe fixer)

The inputs were the adversarial review (one MINOR finding, F1, and eight INFO items, C1 to C8; `s53/r1probe/review/`) and
the held-out re-run (verdict AGREES; `s53/r1probe/rerun/`). Every number below is copied from a saved file under
`s53/r1probe/fix/`, named beside it. The sections above stand as the builder wrote them; where this round supersedes one,
FR7 says so. Nothing was committed, staged or stashed. The only git commands were reads (status, log, rev-parse, diff,
check-attr, config --get). Every status read after the first, a plain `git status` of the worktree at 5:43 AM, used
`--no-optional-locks`, so it could not refresh an index.

### FR1. F1: reproduced first, then fixed, then proved by a live A/B

**Reproduced at 5:53 AM, before any edit** (`F1-repro-before.out`). `f1_repro.py` builds its inputs from the builder's real
K2 file (`build/runs/ALL/K2/profile/current_save.sav`) with its own byte copies; no probe helper builds them. It hands
them to the PRE-fix probe, frozen as `fix/tree-before` (sha256 `829ddbe0…`, the probe the review read). The fixed column
is the same script on the final probe (`F1-repro-after.out`, sha256 `1030c2bf…`).

| input (real sectors of the K2 file) | game status, loaded slot, its counters | pre-fix FILE, an arm registered "S2" | fixed FILE, the same arm |
|---|---|---|---|
| A. slot 0 spliced: S2's ids 0, 1 and 11 (its last physical sector), S1's sectors for the other 11 ids | OK, 0, [1, 2] | `S2`, PASS | `S2+MIXED`, FAIL |
| B. one counter rewritten (id 7 of slot 0: 2 → 6) | OK, 0, [2, 6] | `S2`, PASS | `S2+MIXED`, FAIL |
| C. the last-written sector's counter torn (0xFFFFFF02) | OK, 0, [2, 0xffffff02] | `S2`, PASS | `S2+MIXED`, FAIL |
| D. control: the K2 file untouched | OK, 0, [2] | `S2`, PASS | `S2`, PASS |

The pre-fix probe computed `loaded_all14_counters_equal` False for A, B and C and graded none of it. So F1 is real.

**The fix** (`probe.diff` section 3 holds the whole change). `file_verdict` now appends "+MIXED" when the loaded slot is
the OK slot and its 14 sector counters are not all equal. The game itself never compares them: in the pinned decomp
(`src/save.c` 515-638 at 731ad5bf, read this round), a slot's counter is simply that of the last valid sector read. So
only this suffix can tell a mixed slot from a clean one.
- Selftest: the "unequal counters" case now also asserts the verdict (`S1+MIXED`); a new case runs arm MIXED's splice
  (`mix_slot`) on synthetic saves (`S2+MIXED`); a new planted fault, `ignore_counters`, drops the suffix.
- Live: a new discriminator arm, MIXED. It runs K2's script, then the parent splices S2's slot with S1's real sectors
  (`mix_slot`: ids 0, 1 and the last physical sector's id kept; every sector still valid). Registered before the run:
  FILE `S2+MIXED`, GAME `S2` with no page.

**Proved live at 6:06 AM.** The same two arms, MIXED and K2, ran on the final tree and on `fix/tree/fault-f1`, which is
the final tree with its one "+MIXED" line replaced by a never-true test (`make_fault.out`). That re-plants F1.

| run | MIXED: FILE / GAME / pass | K2: FILE / GAME / pass | MIXED differs from K2 | exit |
|---|---|---|---|---|
| `F1-live-fixed.out` (6:06:08 to 6:06:20 AM) | S2+MIXED / S2 / true | S2 / S2 / true | true | 0 |
| `F1-live-fault.out` (6:06:20 to 6:06:32 AM) | S2 / S2 / false | S2 / S2 / true | false | 1 |

In the fault run, MIXED's slot still read `loaded_all14_counters_equal` False. That is F1's defect exactly: the mix was
computed and not graded.

### FR2. The INFO items: re-confirmed on this round's runs, and the measurements made standing parts of the probe

C1, C2, C3 and C8 report refutations that failed, and hygiene. They ask for no change, and this round's runs re-confirm
them. C4 to C7 report measurements that the review made with a patched copy or a side script. This round makes each one a
standing arm or field of the probe, so that the committed evidence carries it. Their expectations were written down in
`PREREGISTER.txt` before the runs, and every one held.
- **C1, three readers agree** (`second-parse-ALL.txt`): on every arm of `ALL.out`, the framework's own parser (the review's
  verbatim copy), the probe's FILE verdict and child B's gSaveFileStatus agree on which save loads, or that none does. The
  framework's parser has no ERROR status; it names the newest valid slot. `parity_ok` was true on all 37 rows that have a
  file parse (`digest-ALL.txt`). On MIXED, both the framework's parser ("slot 0 counter 2 -> S2") and the game
  (status 1, no page, CONTINUE gave S2) miss the mix; only the probe's FILE verdict flags it.
- **C2, each kill lands on its reported frame and each child B boots cold** (`ALL.table.txt`, checks (a) and (b): "OK").
  Every READY frame equals the last frame of its `a_frames.jsonl`. Every child B had no `.ss1` at its start and frame 0
  after boot.
- **C3, the first-save shape and the per-frame claims** (`M2.timeline.txt`). Before save 1, RAM read gSaveFileStatus 0,
  gSaveCounter 0, gLastWrittenSector 0, gDifferentSaveFile 1. Save 1 asked one question; saves 2 and 3 asked two. The file
  equalled the flash on every recorded frame of all three saves (`file_neq_flash_frames` count 0). All four discriminators
  differ from K2 (`ALL.summary.txt`).
- **C4 became arms K1-NOREAD and KX-NOREAD.** Child A runs with `--noread` and never reads the file's bytes; it stats the
  size only. Both stopped at 68515 with mGBA's dirty 2 and one flush, which is before S2's flush at 68523. Both gave
  S2 / S2, and their rows read `noread` true (`digest-ALL.txt`, `ALL.table.txt`).
- **C5 put the first sector's edges among the default KM offsets.** `km_arms` reads them from M2's record: 18 and 19 for
  save 1, 17 and 18 for save 2.
  - KM-FIRST@18 gave EMPTY / NEW GAME ONLY, and @19 gave CORRUPT / ERASED PAGE + NEW GAME ONLY.
  - KM-SECOND@17 gave S1 / S1 (silent), and @18 gave S1+ERROR / CORRUPTED PAGE + S1.
- **C6 made M2 three saves and added arms KM-THIRD@0, 2, 17, 18, 64, 128, 192 and 255, plus K2-THIRD.** Every KM-THIRD
  offset gave S2+ERROR / CORRUPTED PAGE + S2, and K2-THIRD gave S3 / S3. At KM-THIRD@0 (frame 69258, S3's e3), the slot of
  S1 already read ERROR with 13 valid sectors: physical 17, which had held S1's id 2, no longer carried a signature
  (`digest-ALL.txt`, `ids_by_physical`).
- **C7 is a recorded field of TRUNC's row** (recorded, NOT graded). The regrown half, bytes 65536 to 131072 after child B,
  is all zero: `"fill": "zero"` (`digest-ALL.txt`).
- **C8, hygiene, for this round.**
  - `procs-after.txt` (6:07:00 AM) and `procs-final.txt` (6:12:59 AM): none of the 161 PIDs that this round's outputs
    list is alive, and no process names `probe_save_kill`; the tuner's 12 `pokebot.py` processes were alive and untouched.
    `procs-final-selfmatch.txt` is a first attempt at the final census. It matched its own shells: their command line
    named the probe's path, and they started in the same second. The census now skips its own process and its ancestors.
  - `touch-diff.out` (6:00:43 to 6:07:01 AM): the main checkout's 524 profile entries, its donor `ai-step0-fixture` (721
    files by size, mtime and sha256) and the worktree's profiles are unchanged. No `ai-r1probe-*` profile exists in the
    main checkout, the worktree or the tuner's clone. The status of the main checkout was clean in both snapshots.
  - `main-sandbox-newer.out`: 0 of 33,103 files under the main checkout's sandbox-pokebot are newer than the marker.
  - `worktree-newer.out`: the only file newer than the marker is the probe (6:01:31 AM).
  - The four lane evidence files that the session-start status showed as modified were committed in the main checkout by
    `58fb387d` at 5:51:02 AM, before this round's first run (read-only `git log`). That was not this round.

### FR3. The selftest (6:02:20 AM; `selftest.out` and `selftest-*.out`)

There are now 24 cases (the builder had 20). The clean run gives `SELFTEST VERDICT: PASS`, `EXIT CODE 0`. Each planted
fault gives FAIL, `EXIT CODE 1`:
- `no_checksum` fails 1 case;
- `no_identity` fails 5;
- `ignore_pages` fails 2;
- `ignore_counters` (new) fails 2, the two counter cases.

The new cases cover the unequal-counters verdict, MIXED's splice, a complete third save (`S3`), `fill_name`, and the KM
arms' registered expectations computed from a recorded M2. That last case covers the first sector's edges and the third
family.

### FR4. M2, now three saves (6:02:27 to 6:02:33 AM; `M2.out`, `M2.timeline.txt`)

| event | save 1 | save 2 | save 3 |
|---|---|---|---|
| e1 START pressed | 66924 | 67723 | 68735 |
| e2 "SAVING…" printed | 67238 | 68246 | 69258 |
| e3 (`e3_dirty`; `e3_data`) | 67238 (67238; 67239) | 68246 (68246; 68247) | 69258 (69258; 69258) |
| first sector complete | 67257 (e3+19) | 68264 (e3+18) | 69276 (e3+18) |
| e4 new slot complete | 67495 | 68507 | 69514 |
| e6 flush (= `e6_saves`; `e6_size`) | 67511 (67511; 67511) | 68523 (68523; none) | 69530 (69530; none) |
| e5 "saved the game." | 67577 | 68589 | 69597 |
| e7 free, held 10 frames | 67680 | 68692 | 69700 |
| write e4−e3; flush e6−last write; free e7−e6; dialog e7−e1 | 257; 16; 169; 756 | 261; 16; 169; 969 | 256; 16; 170; 965 |
| gaps between sector completions | 18 to 19 | 18 to 20 (one gap of 20: id 9 at 68431, id 10 at 68451) | 18 to 19 |

- Save 3's truth: PIDs ["550a9be6"], map [0,16], tile (11,17), play time [0,17,47,0]. Both walks went Up:
  (11,19) → (11,18) → (11,17).
- Saves 1 and 2 have events, sector frames and truths identical to the builder's M2 (the DETERMINISM lines). That is one
  trajectory replayed: a determinism check, never a replication.
- `M2-only.out` (6:00:51 AM, tree `fix/tree/final`) is a development run and not the evidence. Its probe differed from the
  final one in three lines of the selftest only (`tree-final2.txt`). That run showed that the third save's first sector
  completes at e3+18, so the selftest's synthetic record was corrected from 19 to 18.

### FR5. Every arm (6:03:04 to 6:06:00 AM; `ALL.out`, digested in `ALL.table.txt` and `ALL.summary.txt`)

The probe chose the default offsets itself from M2's record:
- KM-FIRST 2, 18, 19, 64, 128, 192, 256;
- KM-SECOND 2, 17, 18, 65, 130, 195, 260;
- KM-THIRD 0, 2, 17, 18, 64, 128, 192, 255.

`PROBE SUMMARY` reports `"graded": 37`, `"passed": 37`, `"failed": []` and `EXIT CODE 0`. All 21 of the builder's graded
arms kept the same FILE verdict, GAME verdict and pass (`compare-builder-ALL.txt`): only MIXED's FILE verdict carries
"+MIXED". M2's recorded, ungraded FILE moved from S2 to S3, because M2 now makes a third save.

| arm | FILE | GAME | pass |
|---|---|---|---|
| NOSAVE, ANON | EMPTY | NEW GAME ONLY | true |
| TRUNC | S2+ERROR | CORRUPTED PAGE + S2 | true |
| MIXED (new) | S2+MIXED | S2 | true |
| KM-FIRST@2, @18 | EMPTY | NEW GAME ONLY | true |
| KM-FIRST@19, @64, @128, @192, @256 | CORRUPT | ERASED PAGE + NEW GAME ONLY | true |
| KM-SECOND@2, @17 | S1 | S1 | true |
| KM-SECOND@18, @65, @130, @195, @260 | S1+ERROR | CORRUPTED PAGE + S1 | true |
| KM-THIRD@0, @2, @17, @18, @64, @128, @192, @255 (new) | S2+ERROR | CORRUPTED PAGE + S2 | true |
| K0, K1, K2, KX, CLEAN | S2 | S2 | true (CLEAN left a `.ss1`) |
| K1-NOREAD, KX-NOREAD (new) | S2 | S2 | true |
| K2-THIRD (new) | S3 | S3 | true |
| ERASE28 | S1 (sectors 28-31 went from zero to erased) | not run | true |
| M6 / M6-CONTROL | COLD BOOT (silent) / FIXTURE LOADED | n/a | true |

- Discriminators: NOSAVE, ANON, TRUNC and MIXED each differ from K2 (S2, S2).
- `spec_disagreements` lists exactly KM-FIRST@2, KM-FIRST@18, KM-SECOND@2 and KM-SECOND@17, as pre-registered.
- Children: 72, none alive and no descendant alive. The savers exited 0 (`os._exit`, clean exit) or 15 (the kill); the
  continuers and the M6 children exited 0.

### FR6. The section-0 claims after this round (what the measurement refutes, said plainly)

- **Claim 3 ("about 133 frames") is REFUTED as an estimate.** The writes take 257, 261 and 256 frames (`M2.timeline.txt`).
- **Claim 5 is PARTLY REFUTED, now with both edges measured.** On this trajectory:
  - A kill in a FIRST save's write before its first sector completes leaves no save and no "erased" page. This covers
    [e3, e3+18]: measured at e3+2 and e3+18, and M2's record shows no sector complete before e3+19.
  - A kill in the SECOND save of a fresh cart in [e3, e3+17] loads S1 SILENTLY, with status OK and no page.
  - The page appears from the first sector's completion on (e3+19 and e3+18).
  - For a THIRD save, the claim holds at every offset measured, 0 included: there is no silent window.
- **Claim 4 holds without the probe's own reader.** K1-NOREAD and KX-NOREAD, before the flush, gave S2. As before, this
  measures what the next process sees through the OS cache, not what reached the disk.

### FR7. Corrections to the sections above (the builder's text is left as written; these supersede it)

- **§1** "It also checks that all 14 sector counters are equal": this round GRADES it ("+MIXED", FR1). Before this round
  it was computed and reported only (review F1).
- **§3** "The sectors complete every 18 or 19 frames": that holds for saves 1 and 3. Save 2 has one 20-frame gap (FR4;
  the held-out re-run's note).
- **§5.5** "a kill inside the write's FIRST sector (e3+2, about 18 frames long)": the edges are exact, e3+18 / e3+19 for
  save 1 and e3+17 / e3+18 for save 2, and there is no window for a third save (FR6).
- **§7.11** identities: the probe now has 1,754 lines, sha256 (LF) `1030c2bf92cc0a60166e38a0f7658c371f22217aa686771abf6150045839c0da`,
  (CRLF) `d4c81aad9a9814ac1b7fc6fa42b69c40fb35408466d7df5a10e962228c06b807`, git blob
  `d5b8ab0d6ec0ca418014cbbb605e7bf7f0a6a1cb`. The evidence file, rewritten from this round's outputs, has 579,685 bytes,
  sha256 (LF) `1462aaf66b0ba0ed4351efa096f40e2f406922dd9331fd3b267bda73c357ef13`, (CRLF)
  `075e4390576914a273c7df0409c9fc949f6d742c17a62500707dd7da502e087b`, git blob `ef1905fe404adade31f4d9bbc91742bfc56d3d5c`
  (`hashes.out`). Its code line reads digest `3477e5aafee131a6` (`gate-provenance.out`). `evidence-check.txt` gives "ALL
  SECTIONS VERBATIM": 11 sections, each matching its quoted sha256 and size. The text is identical line for line once the
  sources' CRLF lines are folded to LF, as in the builder's file.
- **§6**, the four checks, re-run in the worktree at 6:07:28 to 6:07:31 AM:
  - `check_purity` exit 0, `VERDICT: PASS` (the probe stays "test side, not scanned");
  - `check_fairness` exit 0, `PERSON-FAIR DATA DOOR: PASS (0 breaches)`;
  - `call_census` exit 0, `CALL-SITE CENSUS: PASS`;
  - `regression_due` exit 1, `5 of 5 suites due`, the same five as before (`gate-*.out`).
- **§8** "Not run: … a THIRD save": a third save now runs (M2 and KM-THIRD / K2-THIRD).
- **§9.1** is answered by measurement: a third save's kill, even on the frame its write starts, gives the corrupted page
  and S2.
- **§9.5** is answered: the regrown half is zero-filled (FR2, C7).

### FR8. What this round did NOT do

- No git commit, add, stash, reset, checkout or restore, and no full regression lane or `run_gates.py`. Nothing in the
  main checkout, the tuner's clone, `sandbox-pokebot/`, `custom-pokebot/` or `40cakes repo/` was edited, and no profile
  was made outside `fix/runs/`.
- Still one fixture (route101_south) and one text speed. The fixture's party is one Pokemon and every save is on map
  [0,16], so the PIDs and the map never tell S1, S2 and S3 apart; only the tile and the play time do (the held-out re-run's
  caveat; the selftest's `no_identity` fault fails on exactly this).
- No fourth or later save, no power cut, no kill inside a frame (kills land between frames), no `.ss1` from another mGBA
  build, and no offsets between the measured ones. The window edges rest on the measured offsets plus M2's sector record.
- MIXED is a CRAFTED file: the parent splices it. The arm shows that the FILE check now sees a mixed slot and that the game
  loads one without any page. It does not show that a kill can produce one; in-order cuts cannot complete a mixed slot (the
  review's C1; the selftest's every in-order cut).
- The C1 to C3 and C8 re-confirmations rest on this round's single trajectory, the same one the builder, the review and
  the held-out re-run replayed.
- `probe.diff` holds the worktree's `git diff` (empty), its status, this round's change to the probe (section 3), and both
  new files in full (section 4).
