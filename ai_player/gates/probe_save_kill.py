"""R1 + R2 PREREQUISITE PROBE (TEST SIDE, development; never the AI's code): a save's timeline in frames, and what a
PROCESS KILL does to it.

    py -3.12 -B probe_save_kill.py run --root ROOT --fixtures DIR --out DIR [--build-root DIR] [--arms NAME,...]
                                       [--km-first N,...] [--km-second N,...] [--km-third N,...] [--after K]
                                       [--child-timeout SECONDS]
    py -3.12 -B probe_save_kill.py selftest [--fault no_checksum|no_identity|ignore_pages|ignore_counters]
    `run` prints one `PROBE {json}` line per arm and a last `PROBE SUMMARY {json}` line; `selftest` prints
    `SELFTEST {json}` and `SELFTEST VERDICT: PASS|FAIL` (exit 0 / 1). `child` is the internal entry of the child processes.

WHY (backlog R1 + R2: "UNVERIFIED first: does mGBA flush the save before a kill?"; the recon NOTES
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-29-R1R2-recon-{host,game,refute}.md`, read, never measured): before the AI
player saves its game and CONTINUES it, these are MEASURED, whatever the user rules on WHEN it saves: how long one save
takes in frames, when mGBA forces the save out to `current_save.sav`, and what a process kill at each point leaves for the
NEXT process. A kill cannot be observed from inside the process it kills, so the probe is a PARENT (no emulator) and
children:
  * child A, the SAVER, boots the framework's emulator WITH A FILE-BACKED SAVE (`LibmgbaEmulator(is_test_run=False)`; every
    other harness boots `is_test_run=True`, `probe_eyes.boot`, whose flash lives in anonymous memory and never reaches a
    file) on a THROWAWAY profile the parent made under `--out` (`modules.profiles.load_profile` takes any folder holding a
    `metadata.yml`; the ROM binding is copied from `hands_harness.PROFILE`'s, never written there), loads the free fixture
    `route101_south.ss1`, pins the cartridge clock (`hands_harness.pin_game_clock`, as `probe_end_screen.py` does) and SAVES
    WITH TEST-SIDE PRESSES: START; the cursor put on SAVE by reading `sStartMenuCursorPos` / `sCurrentStartMenuActions`
    (RAM by symbol); A; A on YES at each question, each READ BY ITS WORDS (`play_harness.shown_pages`, the harness's own
    decode of the message buffer); then NO input until the box closes by itself. A second save follows the same way after
    the player walks ONE tile (so the two saves differ in tile and play time; a third save, where an arm asks for one,
    walks one more). EVERY frame it records: mGBA's own `dirty` / `dirtAge` of the save (the cffi struct `GBASavedata`),
    both slots of the emulator's flash (`read_save_data`) and of the FILE read through a second handle (not with
    `--noread`, arms *-NOREAD: then the PROBE in child A never reads the file's bytes, only its size; the framework's
    own flush backup, `libmgba.py`, still reads the whole file at each flush, S1's included), the file's size, the
    `saves/` folder (the framework's backup copy), the save dialog's callback by symbol (`sSaveDialogCallback`) and
    `gMenuCallback`, text printer 0, the message pages, the play time in RAM, and the harness's free read
    (`probe_end_screen.game_screen`). At the arm's frame it prints `READY {json}`
    and BLOCKS (no frame in flight), or `os._exit`s (arm KX), or exits normally (arm CLEAN: the framework's atexit `.ss1`).
  * the PARENT kills child A at READY with `psutil.Process(pid).kill()` on the PID it started (NEVER by process name: the
    bot tuner runs pokebot processes 24/7), parses the FILE by the decomp's layout (FILE verdict), deletes any `.ss1` and
    starts
  * child B, the CONTINUER, a fresh process on the same profile: from power-on (START every 20 frames until the main menu's
    task exists), every error page READ BY ITS WORDS (text printer 7's own string: `printer_page`), the menu's `tMenuType`,
    CONTINUE when offered (the cursor read on it), then the harness's truth on a held free overworld (GAME verdict).

THE TIMELINE (M2), each event the emulator's frame count read after the frame it was first seen in:
  e1 START pressed; e2 "SAVING…" fully printed (the dialog's callback is SaveDoSaveCallback, printer 0 idle); e3 the first
  flash write (`e3_dirty`: mGBA's own mark, its `dirty` / `dirtAge`, moved; `e3_data`: the first changed byte; e3 is the
  earlier); e4 the new slot complete in the emulator's flash (all 14 sectors valid with the new counter; `e4_last_write`
  = mGBA's `dirtAge` + 1, `e4_last_change` = the last changed byte); e5 "{PLAYER} saved the game." fully printed
  (`e5_jingle`: the callback moved on to SaveReturnSuccessCallback); e6 the flush: mGBA's `savedataUpdated` callback (a
  listener the probe appends after the framework's backup copy), `e6_saves` the `saves/` folder changed, `e6_size` the
  file's size changed; e7 the screen FREE and held `--after` frames. (mGBA's `dirtAge` is its frame counter at the frame's
  END, one less than the count the emulator reports after that frame: `src/gba/video.c` calls GBAFrameEnded before it
  increments the counter; hence the + 1.)
  ⚠ A file mapping and an ordinary read of the same file share the system cache, so the second-handle read sees the mapped
  bytes as soon as they are written, flushed or not: the file's slots are therefore NOT a flush mark (e6 is), and the FILE
  verdict after a kill measures what the NEXT PROCESS sees, never what reached the disk. A power cut is out of reach.

THE ARMS (each a fresh profile under `--out`; expectations registered here, before any run):
  M2 (no kill; THREE saves), then the discriminators NOSAVE (kill with the cursor on SAVE, before A), ANON (child A with
  `is_test_run=True`, K2's script), TRUNC (K2's script, then the parent cuts the file to 64 KB before child B), MIXED (K2's
  script, then the parent splices S2's slot with S1's sectors, `mix_slot`: every sector still valid, two counters in the
  slot: the FILE check must say "+MIXED"; the game, which never compares the counters, is expected to load S2);
  KM-FIRST@N, KM-SECOND@N and KM-THIRD@N (a kill N frames after e3 of the first, second or third save; N defaults to 2,
  the first sector's last incomplete frame and the frame it completes (the edges of the silent window), a quarter, a
  half and three quarters of M2's e4 - e3, and e4 - e3 - 1, and for the third save also 0; for the first two saves the
  expectation comes from M2's record of how many sectors of the new slot were complete at e3 + N: none leaves that slot
  EMPTY, one or more leaves it ERROR; a third save writes into the FIRST save's slot, whose sector its erase destroys
  first, so every N expects S2+ERROR); K0 / K1 / K2 (a kill at e4, e4 + 8, e4 + 40 of the second save); KX (`os._exit`
  at K1's frame); CLEAN (a normal exit at K2's frame: a `.ss1` must be left); K1-NOREAD / KX-NOREAD (K1 / KX with the
  probe in child A never reading the file: the probe's own second handle is not what keeps the save; the framework's
  flush backup still reads it once, at S1's flush, 735 frames before S2's write); K2-THIRD (a kill 40 frames after a
  THIRD save's e4: the control for KM-THIRD); ERASE28 (one save from a `.sav` whose sectors 28-31 hold 0x00: are they
  erased?); M6 (a fixture `.ss1` with its version magic bumped, auto-loaded as `current_state.ss1`: a silent cold boot?)
  and M6-CONTROL (the same file unbumped).
  ERASE28, M6-CONTROL, the extra KM offsets (2, the first sector's edges, e4 - e3 - 1) and, from the 2026-10-29 review
  round, MIXED, KM-THIRD, K2-THIRD and the two NOREAD arms are beyond the build spec; each answers a claim of the spec's
  section 0, or a reviewer's question, that the spec's own arms leave unmeasured.
  FILE verdict: the game's own status of the file (a port of `GetSaveValidStatus`, `src/save.c`, pinned decomp 731ad5b):
  EMPTY, CORRUPT, or the save its loaded slot holds (S1 / S2 / S3 / OTHER), with "+ERROR" when the other slot is broken
  and "+MIXED" when the loaded slot's 14 sector counters are not all EQUAL (the build spec's "all 14 sectors valid and
  their counters EQUAL"; the game itself never compares them).
  GAME verdict: "CORRUPTED PAGE + " / "ERASED PAGE + " when the game showed that page, then "NEW GAME ONLY" or the save
  CONTINUE gave. A save is S1, S2 or S3 only when the party's PIDs AND the map AND the tile AND the play time (to the
  VBlank) all equal that save's truth (CLAUDE.md rule 3: identity, never position or count).

THE SELFTEST (offline; it must be able to FAIL and to PASS): the slot parser on synthetic images (a valid slot; one byte
flipped; unequal counters; an empty image; two slots; a torn slot; the counter wrap; a truncated file; every in-order cut
of a third save, the recon's section 7.1; a second save cut inside its first sector; arm MIXED's splice; a complete third
save), the verdict functions on recorded results (an empty file and no CONTINUE against "S2" FAILS, against "EMPTY"
PASSES; a netted-out save; a corrupted page; an erased page), the KM arms' registered expectations from a recorded M2
(`km_arms`), and `fill_name`. `--fault` plants a bug (the checksum skipped, identity by PIDs alone, the pages ignored, the
counters ignored): the selftest must then say FAIL.

WHAT IT CANNOT PROVE: that a save survives a power cut (the OS cache, not the platter); anything about the AI's own eyes,
hands or brain (none is used: the presses and the reads are the harness's).
"""

from __future__ import annotations

import argparse
import array
import json
import os
import queue
import random
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ------------------------------------------------------------------ the save layout (pinned decomp 731ad5b)
#: `include/save.h`: a 4 KiB sector is 3968 data bytes and a footer: id u16 @0xFF4, checksum u16 @0xFF6, signature u32
#: @0xFF8 (SECTOR_SIGNATURE 0x08012025), counter u32 @0xFFC; slot 1 = sectors 0-13, slot 2 = 14-27, 28-31 special
SECTOR_SIZE = 0x1000
SECTORS_PER_SLOT = 14
FLASH_SIZE = 32 * SECTOR_SIZE
SIGNATURE = 0x08012025
FOOT_ID, FOOT_CHECKSUM, FOOT_SIGNATURE, FOOT_COUNTER = 0xFF4, 0xFF6, 0xFF8, 0xFFC
ALL_IDS = (1 << SECTORS_PER_SLOT) - 1
#: `src/save.c` sSaveSlotLayout (SAVEBLOCK_CHUNK of SaveBlock2, SaveBlock1 x4, PokemonStorage x9): the bytes each sector id
#: carries and its checksum covers (`CalculateChecksum(data, size)`: the u32 sum of size/4 words, folded to 16 bits); the
#: same numbers as the framework's `modules/save_data.py` `_section_sizes`
CHUNK_SIZES = (3884, 3968, 3968, 3968, 3848, 3968, 3968, 3968, 3968, 3968, 3968, 3968, 3968, 2000)
#: `include/global.h` struct SaveBlock2: playTimeHours u16 @0x0E, minutes @0x10, seconds @0x11, vblanks @0x12;
#: encryptionKey @0xAC. struct SaveBlock1: pos (s16 x, s16 y) @0x00, location (s8 group, s8 number, ...) @0x04,
#: playerPartyCount @0x234, playerParty[6] @0x238 (100 bytes each, personality u32 first), gameStats[] @0x159C
SB2_PLAY_TIME, SB2_KEY = 0x0E, 0xAC
SB1_POS, SB1_LOCATION, SB1_PARTY_COUNT, SB1_PARTY, SB1_GAME_STATS = 0x00, 0x04, 0x234, 0x238, 0x159C
MON_SIZE = 100
#: `src/start_menu.c` MENU_ACTION_SAVE; `src/main_menu.c` HAS_SAVED_GAME (tMenuType, the main menu task's data[0])
MENU_ACTION_SAVE = 5
HAS_SAVED_GAME = 1
#: `include/text.h` struct TextPrinter (0x24 bytes): currentChar u32 @0, active @0x1B, state @0x1C
PRINTER_SIZE, PRINTER_ACTIVE, PRINTER_STATE = 0x24, 0x1B, 0x1C
#: the main menu's tasks (`src/main_menu.c`), the error pages' tasks among them
MAIN_MENU_TASKS = ("Task_MainMenuCheckSaveFile", "Task_WaitForSaveFileErrorWindow", "Task_MainMenuCheckBattery",
                   "Task_WaitForBatteryDryErrorWindow", "Task_DisplayMainMenu", "Task_HandleMainMenuInput")
ERROR_TASKS = ("Task_WaitForSaveFileErrorWindow", "Task_WaitForBatteryDryErrorWindow")
#: the save dialog's callbacks that take a YES/NO (`src/start_menu.c`)
INPUT_CALLBACKS = ("SaveConfirmInputCallback", "SaveOverwriteInputCallback")
FIXTURE = "route101_south.ss1"
#: arm M6: a raw mGBA state starts with its version magic (0x01000007 for mGBA 0.10.2, `src/gba/serialize.c`); this one is
#: "too new" (`GBADeserialize` refuses a magic above its own)
BUMPED_MAGIC = 0x01000008
TRUNC_BYTES = 0x10000
DEFAULT_AFTER = 10
SETTLE_FRAMES = 30
BLOCK_SECONDS = 120
IDENTITY_KEYS = ("pids", "map", "pos", "play_time")
#: the saves an arm can make, in the order `identify` tries them
SAVE_NAMES = ("S1", "S2", "S3")
#: M2 makes three saves, so that the KM-THIRD offsets come from a measured timeline like the other two families'
M2_SAVES = 3
STOP_EVENTS = ("menu", "e1", "e2", "e3", "e4", "e5", "e6", "e7")
FAULTS = ("no_checksum", "no_identity", "ignore_pages", "ignore_counters")
assert array.array("I").itemsize == 4, "the checksum reads 32-bit words"


class ProbeAbort(RuntimeError):
    """A bounded wait ran out, or the game showed something the probe does not handle: the child ends with ABORT."""


def _u16(data, at: int) -> int:
    return int.from_bytes(bytes(data[at:at + 2]), "little")


def _s16(data, at: int) -> int:
    return int.from_bytes(bytes(data[at:at + 2]), "little", signed=True)


def _u32(data, at: int) -> int:
    return int.from_bytes(bytes(data[at:at + 4]), "little")


# ------------------------------------------------------------------ the parser (offline; the selftest's subject)
def sector_checksum(data: bytes, size: int) -> int:
    """`src/save.c` CalculateChecksum: the u32 sum of the first `size` / 4 little-endian words, folded `(c >> 16) + c`."""
    words = array.array("I")
    words.frombytes(bytes(data[:size - size % 4]))
    if sys.byteorder != "little":
        words.byteswap()
    total = sum(words) & 0xFFFFFFFF
    return ((total >> 16) + total) & 0xFFFF


def read_sector(image: bytes, physical: int) -> tuple[bytes, bool]:
    """The 4 KiB of sector `physical`, and whether the image holds all of it. Bytes past the image's end read as 0xFF (no
    signature): mGBA grows a short `.sav` (0xFF below 64 KB; zeros from 64 KB, `GBASavedataInitFlash`), and neither fill
    carries a signature, so a missing sector counts as absent either way."""
    start = physical * SECTOR_SIZE
    raw = bytes(image[start:start + SECTOR_SIZE])
    present = len(raw) == SECTOR_SIZE
    if not present:
        raw += b"\xff" * (SECTOR_SIZE - len(raw))
    return raw, present


def parse_slot(image: bytes, slot: int, fault: str | None = None) -> dict:
    """One slot as `GetSaveValidStatus` (`src/save.c`) judges it: EMPTY when no sector has the signature, OK when all 14
    sector ids are valid (signature AND checksum), else ERROR; its counter is the counter of the LAST valid sector read (the
    game's own rule, which never compares the 14 counters: `counters_equal` is this probe's extra check, which
    `file_verdict` grades as "+MIXED"). A sector whose id is 14 or more is counted invalid (the game would index past its
    table there). `sectors`: [physical, id, signature ok, valid, counter] each."""
    signature_seen = False
    valid = 0
    counter = None
    sectors = []
    for index in range(SECTORS_PER_SLOT):
        physical = slot * SECTORS_PER_SLOT + index
        raw, _present = read_sector(image, physical)
        sid, checksum = _u16(raw, FOOT_ID), _u16(raw, FOOT_CHECKSUM)
        has_signature = _u32(raw, FOOT_SIGNATURE) == SIGNATURE
        count = _u32(raw, FOOT_COUNTER)
        good = False
        if has_signature:
            signature_seen = True
            if sid < SECTORS_PER_SLOT:
                good = fault == "no_checksum" or sector_checksum(raw, CHUNK_SIZES[sid]) == checksum
        if good:
            valid |= 1 << sid
            counter = count
        sectors.append([physical, sid if has_signature else None, int(has_signature), int(good),
                        count if has_signature else None])
    status = "OK" if valid == ALL_IDS else ("ERROR" if signature_seen else "EMPTY")
    good_counters = sorted({s[4] for s in sectors if s[3]})
    return {"slot": slot, "status": status, "counter": counter, "valid": bin(valid).count("1"),
            "signatures": sum(s[2] for s in sectors), "counters": good_counters,
            "counters_equal": len(good_counters) == 1 if good_counters else None, "sectors": sectors}


def save_status(slots: list[dict]) -> tuple[str, int | None]:
    """The bottom of `GetSaveValidStatus` (`src/save.c`): the game's status and the counter it picks (gSaveCounter); the
    slot it then loads is that counter % 2 (`CopySaveSlotData`)."""
    one, two = slots
    if one["status"] == "OK" and two["status"] == "OK":
        c1, c2 = one["counter"], two["counter"]
        if (c1 == 0xFFFFFFFF and c2 == 0) or (c1 == 0 and c2 == 0xFFFFFFFF):
            return "OK", (c2 if (c1 + 1) & 0xFFFFFFFF < (c2 + 1) & 0xFFFFFFFF else c1)
        return "OK", (c2 if c1 < c2 else c1)
    if one["status"] == "OK":
        return ("ERROR" if two["status"] == "ERROR" else "OK"), one["counter"]
    if two["status"] == "OK":
        return ("ERROR" if one["status"] == "ERROR" else "OK"), two["counter"]
    if one["status"] == "EMPTY" and two["status"] == "EMPTY":
        return "EMPTY", None
    return "CORRUPT", None


def slot_content(image: bytes, slot: dict) -> dict | None:
    """What a slot holds that identifies a save: the play time (SaveBlock2, sector id 0), the map, the tile and the party's
    PIDs (SaveBlock1's first chunk, sector id 1). None when either sector is not valid."""
    by_id = {s[1]: s[0] for s in slot["sectors"] if s[3]}
    if 0 not in by_id or 1 not in by_id:
        return None
    sb2, _ = read_sector(image, by_id[0])
    sb1, _ = read_sector(image, by_id[1])
    count = sb1[SB1_PARTY_COUNT]
    return {"play_time": [_u16(sb2, SB2_PLAY_TIME), sb2[SB2_PLAY_TIME + 2], sb2[SB2_PLAY_TIME + 3], sb2[SB2_PLAY_TIME + 4]],
            "map": [sb1[SB1_LOCATION], sb1[SB1_LOCATION + 1]], "pos": [_s16(sb1, SB1_POS), _s16(sb1, SB1_POS + 2)],
            "pids": [f"{_u32(sb1, SB1_PARTY + i * MON_SIZE):08x}" for i in range(min(count, 6))]}


def parse_image(image: bytes | None, fault: str | None = None) -> dict:
    """The whole `.sav` image as the game would judge it at boot, plus the probe's extra checks (module docstring)."""
    image = image or b""
    slots = [parse_slot(image, 0, fault), parse_slot(image, 1, fault)]
    status, counter = save_status(slots)
    loaded = None if counter is None else counter % 2
    chosen = next((s["slot"] for s in slots if s["status"] == "OK" and s["counter"] == counter), None)
    special = [read_sector(image, physical) for physical in range(28, 32)]
    return {"size": len(image), "status": status, "counter": counter, "loaded_slot": loaded,
            "parity_ok": loaded is None or loaded == chosen,
            "loaded": slot_content(image, slots[loaded]) if loaded is not None else None,
            "loaded_all14_counters_equal": (loaded is not None and slots[loaded]["valid"] == SECTORS_PER_SLOT
                                            and bool(slots[loaded]["counters_equal"])),
            "slots": slots,
            "sectors_28_31": ["absent" if not present else "erased" if raw == b"\xff" * SECTOR_SIZE
                              else "zero" if raw == b"\x00" * SECTOR_SIZE else "data" for raw, present in special]}


def brief(parse: dict | None) -> dict | None:
    """A parse without the per-sector lists (what a PROBE line carries)."""
    if parse is None:
        return None
    return {**{k: v for k, v in parse.items() if k != "slots"},
            "slots": [{k: v for k, v in s.items() if k != "sectors"} for s in parse["slots"]],
            "ids_by_physical": {str(s["slot"]): [x[1] for x in s["sectors"]] for s in parse["slots"]}}


def new_ids(parse: dict | None, counter: int | None) -> list[int]:
    """The sector ids valid with `counter` in either slot (a save being written: which of its sectors are complete)."""
    if parse is None or counter is None:
        return []
    return sorted({s[1] for slot in parse["slots"] for s in slot["sectors"] if s[3] and s[4] == counter})


def mix_slot(image: bytes, parse: dict) -> tuple[bytes, dict]:
    """Arm MIXED's input (review finding F1, 2026-10-29), made from REAL sectors: each sector of the loaded slot replaced,
    byte for byte, by the OTHER slot's sector of the same id, except ids 0 and 1 (SaveBlock2's and SaveBlock1's first
    chunks: the play time, map, tile and party, the identity) and the id in the loaded slot's LAST physical sector (whose
    counter the game takes as the slot's, `parse_slot`). A sector's checksum covers only its own data, wherever it sits, so
    every sector stays valid: the game still says OK and loads this slot as the same save, while its 14 counters are now
    two. Returns the new image (same length) and what moved: [id, from physical, to physical] each."""
    loaded = parse["slots"][parse["loaded_slot"]]
    other = parse["slots"][1 - parse["loaded_slot"]]
    source = {s[1]: s[0] for s in other["sectors"] if s[3]}
    keep = {0, 1, loaded["sectors"][-1][1]}
    out = bytearray(image)
    moved = []
    for physical, sid, _signed, good, _counter in loaded["sectors"]:
        if good and sid not in keep and sid in source:
            src = source[sid] * SECTOR_SIZE
            out[physical * SECTOR_SIZE:(physical + 1) * SECTOR_SIZE] = bytes(image[src:src + SECTOR_SIZE])
            moved.append([sid, source[sid], physical])
    return bytes(out), {"kept_ids": sorted(k for k in keep if k is not None), "moved": moved}


def fill_name(data: bytes) -> str:
    """What a stretch of a file holds: "absent" (no bytes), "erased" (all 0xFF), "zero" (all 0x00), else "data"."""
    if not data:
        return "absent"
    if data.count(0xFF) == len(data):
        return "erased"
    if data.count(0) == len(data):
        return "zero"
    return "data"


# ------------------------------------------------------------------ the verdicts (offline; the selftest's subject)
def identify(state: dict | None, truths: dict, fault: str | None = None) -> str:
    """"S1" / "S2" / "S3" when `state` has that save's party PIDs AND map AND tile AND play time; "NONE" without a state;
    else "OTHER". (FAULT no_identity: the PIDs alone, the netted-out save that rule 3 forbids.)"""
    if not state:
        return "NONE"
    keys = ("pids",) if fault == "no_identity" else IDENTITY_KEYS
    for name in SAVE_NAMES:
        truth = truths.get(name)
        if truth and all(state.get(key) == truth.get(key) for key in keys):
            return name
    return "OTHER"


def file_verdict(parse: dict | None, truths: dict, fault: str | None = None) -> str:
    """The FILE verdict (module docstring): "NO FILE", EMPTY or CORRUPT, else the save the loaded slot holds (`identify`),
    with "+ERROR" when the other slot is broken and "+MIXED" when the loaded slot's 14 sector counters are not all EQUAL.
    The build spec's FILE judgement is "all 14 sectors valid and their counters EQUAL"; the game itself never compares
    them (it keeps the last valid sector's, `parse_slot`), so a slot spliced from two saves, or one whose counter a cut
    left half-programmed, still loads, and only this suffix tells it from a clean save. (Review finding F1, 2026-10-29:
    the check was computed and reported, `loaded_all14_counters_equal`, and never graded. FAULT ignore_counters drops
    it.) The check reads the LOADED slot only (the counter's parity), and only when that slot's status is OK: unequal
    counters in the other slot add nothing, and a parity that points at an EMPTY slot reads NONE with no suffix (the
    selftest's two CONTROL cases, added 2026-10-29 after the fix round's review)."""
    if parse is None:
        return "NO FILE"
    if parse["status"] in ("EMPTY", "CORRUPT"):
        return parse["status"]
    verdict = identify(parse["loaded"], truths, fault)
    if parse["status"] != "OK":
        verdict += "+ERROR"
    loaded = parse["slots"][parse["loaded_slot"]]
    if fault != "ignore_counters" and loaded["status"] == "OK" and not loaded["counters_equal"]:
        verdict += "+MIXED"
    return verdict


def page_tag(pages: list[dict], fault: str | None = None) -> str:
    if fault == "ignore_pages":
        return ""
    words = " ".join(str(p.get("text") or "") for p in pages).lower()
    tag = ""
    if "corrupted" in words:
        tag += "CORRUPTED PAGE + "
    if "erased" in words:
        tag += "ERASED PAGE + "
    if "battery" in words:
        tag += "BATTERY PAGE + "
    return tag


def game_verdict(result: dict | None, truths: dict, fault: str | None = None) -> str:
    """The continuer's result as the game showed it (module docstring). The play time is the BOOT READ's (the slot the game
    copied into RAM at power-on, exact to the VBlank); the map, tile and PIDs are the free overworld's after CONTINUE."""
    if not result or result.get("abort"):
        return f"NO RESULT ({(result or {}).get('abort', 'no line')})"
    tag = page_tag(result.get("pages") or [], fault)
    if not result.get("continue_offered"):
        return tag + "NEW GAME ONLY"
    after = result.get("after")
    if not after:
        return tag + "CONTINUE NOT REACHED"
    state = {"pids": after["pids"], "map": after["map"], "pos": after["pos"],
             "play_time": (result.get("boot") or {}).get("play_time")}
    return tag + identify(state, truths, fault)


# ------------------------------------------------------------------ the selftest (offline)
def plant_slot(image: bytearray, slot: int, counter: int, rotation: int, seed: int, content: dict | None = None,
               ids: range | None = None) -> None:
    """Write a save into `slot` as `HandleWriteSector` does (`src/save.c`): sector id i at physical
    slot * 14 + (i + rotation) % 14, the buffer zeroed, `size` data bytes, then id, checksum, signature, counter; `ids`
    limits it to a PREFIX (a write cut after those ids)."""
    rng = random.Random(seed)
    for sid in (ids if ids is not None else range(SECTORS_PER_SLOT)):
        size = CHUNK_SIZES[sid]
        data = bytearray(rng.getrandbits(8) for _ in range(size))
        if content and sid == 0:
            hours, minutes, seconds, vblanks = content["play_time"]
            data[SB2_PLAY_TIME:SB2_PLAY_TIME + 5] = hours.to_bytes(2, "little") + bytes([minutes, seconds, vblanks])
        if content and sid == 1:
            data[SB1_POS:SB1_POS + 4] = (content["pos"][0].to_bytes(2, "little", signed=True)
                                         + content["pos"][1].to_bytes(2, "little", signed=True))
            data[SB1_LOCATION:SB1_LOCATION + 2] = bytes(content["map"])
            data[SB1_PARTY_COUNT] = len(content["pids"])
            for i, pid in enumerate(content["pids"]):
                data[SB1_PARTY + i * MON_SIZE:SB1_PARTY + i * MON_SIZE + 4] = int(pid, 16).to_bytes(4, "little")
        sector = bytearray(SECTOR_SIZE)
        sector[:size] = data
        sector[FOOT_ID:FOOT_ID + 2] = sid.to_bytes(2, "little")
        sector[FOOT_CHECKSUM:FOOT_CHECKSUM + 2] = sector_checksum(bytes(data), size).to_bytes(2, "little")
        sector[FOOT_SIGNATURE:FOOT_SIGNATURE + 4] = SIGNATURE.to_bytes(4, "little")
        sector[FOOT_COUNTER:FOOT_COUNTER + 4] = counter.to_bytes(4, "little")
        physical = slot * SECTORS_PER_SLOT + (sid + rotation) % SECTORS_PER_SLOT
        image[physical * SECTOR_SIZE:(physical + 1) * SECTOR_SIZE] = sector


def selftest(fault: str | None) -> dict:
    s1 = {"pids": ["a1b2c3d4", "0badf00d"], "map": [0, 16], "pos": [11, 19], "play_time": [3, 7, 21, 40]}
    s2 = {"pids": ["a1b2c3d4", "0badf00d"], "map": [0, 16], "pos": [11, 18], "play_time": [3, 7, 29, 5]}
    s3 = {"pids": ["a1b2c3d4", "0badf00d"], "map": [0, 16], "pos": [11, 17], "play_time": [3, 7, 41, 52]}
    truths = {"S1": s1, "S2": s2, "S3": s3}
    cases: list[dict] = []

    def case(name: str, got, expected) -> None:
        cases.append({"case": name, "expected": expected, "got": got, "ok": got == expected})

    blank = bytes([0xFF]) * FLASH_SIZE
    case("an erased (0xFF) image reads EMPTY", parse_image(blank, fault)["status"], "EMPTY")
    case("a zero-filled image reads EMPTY", parse_image(bytes(FLASH_SIZE), fault)["status"], "EMPTY")
    case("a 0-byte file reads EMPTY", parse_image(b"", fault)["status"], "EMPTY")
    first = bytearray(blank)
    plant_slot(first, 1, 1, 1, seed=11, content=s1)  # a first save from a fixture: counter 1, the SECOND slot, rotation 1
    parsed = parse_image(bytes(first), fault)
    case("a valid first save: OK, the second slot loads, 14 sectors with one counter",
         [parsed["status"], parsed["loaded_slot"], parsed["loaded_all14_counters_equal"]], ["OK", 1, True])
    case("a valid first save: id 0 sits at sector 15, id 13 at sector 14",
         [parsed["slots"][1]["sectors"][1][1], parsed["slots"][1]["sectors"][0][1]], [0, 13])
    case("a valid first save decodes the planted identity", parsed["loaded"], s1)
    case("a valid first save is S1 (FILE)", file_verdict(parsed, truths, fault), "S1")
    flipped = bytearray(first)
    flipped[(14 + (5 + 1) % 14) * SECTOR_SIZE + 100] ^= 0x01  # one data byte of sector id 5
    parsed = parse_image(bytes(flipped), fault)
    case("FAULT INPUT one data byte flipped: that slot is ERROR, the cart CORRUPT",
         [parsed["slots"][1]["status"], parsed["status"]], ["ERROR", "CORRUPT"])
    uneven = bytearray(first)
    at = (14 + (7 + 1) % 14) * SECTOR_SIZE + FOOT_COUNTER  # sector id 7's counter: outside the checksum
    uneven[at:at + 4] = (6).to_bytes(4, "little")
    parsed = parse_image(bytes(uneven), fault)
    case("FAULT INPUT unequal counters: the game still says OK, the probe flags it, and the FILE verdict grades it "
         "(S1+MIXED)",
         [parsed["status"], parsed["slots"][1]["counters_equal"], parsed["loaded_all14_counters_equal"],
          file_verdict(parsed, truths, fault)], ["OK", False, False, "S1+MIXED"])
    both = bytearray(first)
    plant_slot(both, 0, 2, 2, seed=22, content=s2)  # the second save: counter 2, the FIRST slot, rotation 2
    parsed = parse_image(bytes(both), fault)
    case("two saves: OK, the counter-2 slot loads, and it is S2", [parsed["status"], parsed["loaded_slot"],
                                                                   file_verdict(parsed, truths, fault)], ["OK", 0, "S2"])
    # the fix round's review (2026-10-29): "+MIXED" reads the LOADED slot only, and only an OK one. CONTROL 1: the slot
    # NOT loaded (S1's) made uneven the way the FAULT INPUT above makes the loaded one: no suffix
    other_uneven = bytearray(both)
    at = (14 + (7 + 1) % 14) * SECTOR_SIZE + FOOT_COUNTER  # S1's sector id 7's counter: outside the checksum
    other_uneven[at:at + 4] = (6).to_bytes(4, "little")
    parsed = parse_image(bytes(other_uneven), fault)
    case("CONTROL unequal counters in the slot NOT loaded: S2 loads and the FILE verdict has no suffix (S2)",
         [parsed["status"], parsed["loaded_slot"], parsed["slots"][1]["counters_equal"],
          file_verdict(parsed, truths, fault)], ["OK", 0, False, "S2"])
    # CONTROL 2: a counter-1 save in the FIRST slot, so the counter's parity points at the second slot, which is EMPTY:
    # nothing to identify, and no suffix
    odd = bytearray(blank)
    plant_slot(odd, 0, 1, 1, seed=66, content=s1)
    parsed = parse_image(bytes(odd), fault)
    case("CONTROL the counter's parity points at an EMPTY slot: nothing loads and the FILE verdict has no suffix (NONE)",
         [parsed["status"], parsed["loaded_slot"], parsed["slots"][1]["status"], parsed["parity_ok"],
          file_verdict(parsed, truths, fault)], ["OK", 1, "EMPTY", False, "NONE"])
    # review finding F1: a slot whose 14 sectors are all valid but come from TWO saves (arm MIXED's splice: S2's ids 0, 1
    # and its last physical sector's id 11 kept, S1's sectors of the other 11 ids copied in) loads as S2 in the game
    mixed, how = mix_slot(bytes(both), parse_image(bytes(both)))
    parsed = parse_image(mixed, fault)
    case("FAULT INPUT arm MIXED's splice of two saves: the game still says OK and loads S2's identity; the FILE verdict "
         "says S2+MIXED",
         [parsed["status"], parsed["loaded_slot"], parsed["slots"][0]["counters"], how["kept_ids"], len(how["moved"]),
          file_verdict(parsed, truths, fault)], ["OK", 0, [1, 2], [0, 1, 11], 11, "S2+MIXED"])
    third_done = bytearray(both)
    plant_slot(third_done, 1, 3, 3, seed=55, content=s3)  # a third save, complete: counter 3, the SECOND slot, rotation 3
    parsed = parse_image(bytes(third_done), fault)
    case("a third save complete: OK, the counter-3 slot loads, and it is S3",
         [parsed["status"], parsed["loaded_slot"], file_verdict(parsed, truths, fault)], ["OK", 1, "S3"])
    torn = bytearray(first)
    plant_slot(torn, 0, 2, 2, seed=22, content=s2, ids=range(6))  # the second save cut after ids 0-5
    parsed = parse_image(bytes(torn), fault)
    case("FAULT INPUT the second save torn: ERROR, the first save loads (S1+ERROR)",
         [parsed["status"], file_verdict(parsed, truths, fault)], ["ERROR", "S1+ERROR"])
    wrap = bytearray(blank)
    plant_slot(wrap, 1, 0xFFFFFFFF, 1, seed=33)
    plant_slot(wrap, 0, 0, 2, seed=44)
    case("the counter wrap: 0 beats 0xFFFFFFFF", parse_image(bytes(wrap), fault)["counter"], 0)
    parsed = parse_image(bytes(both)[:TRUNC_BYTES], fault)
    case("FAULT INPUT the file cut to 64 KB: the first slot whole, sectors 14-15 left: S2+ERROR",
         [parsed["slots"][1]["status"], parsed["slots"][1]["valid"], file_verdict(parsed, truths, fault)],
         ["ERROR", 2, "S2+ERROR"])
    # recon 2026-10-29 section 7.1 (an in-order cut leaves the new slot ERROR): a THIRD save written into the slot that
    # holds the first one, cut after ids 0..k for every k (k = -1: inside its FIRST sector, none complete); the sector
    # after the cut erased and half-programmed (its footer still erased), as a kill mid-sector leaves it
    cuts = []
    for k in range(-1, SECTORS_PER_SLOT):
        third = bytearray(both)
        plant_slot(third, 1, 3, 3, seed=55, ids=range(k + 1))
        if k + 1 < SECTORS_PER_SLOT:
            physical = SECTORS_PER_SLOT + (k + 1 + 3) % SECTORS_PER_SLOT
            third[physical * SECTOR_SIZE:(physical + 1) * SECTOR_SIZE] = bytes(200) + b"\xff" * (SECTOR_SIZE - 200)
        parsed = parse_image(bytes(third), fault)
        cuts.append(f"{parsed['slots'][1]['status']}/{parsed['loaded_slot']}")
    case("every in-order cut of a third save, even inside its first sector: ERROR and the second save loads, until the "
         "14th id completes it", cuts, ["ERROR/0"] * SECTORS_PER_SLOT + ["OK/1"])
    # ... whereas the SECOND save of a fresh cart writes into a slot that was never written: cut inside its first sector,
    # that slot has no signature at all (EMPTY), so the first save loads with NO error (the silent case)
    early = bytearray(first)
    early[2 * SECTOR_SIZE:3 * SECTOR_SIZE] = bytes(200) + b"\xff" * (SECTOR_SIZE - 200)  # id 0's sector (rotation 2)
    parsed = parse_image(bytes(early), fault)
    case("the second save cut inside its first sector: that slot EMPTY, the first save loads with status OK (S1)",
         [parsed["slots"][0]["status"], parsed["status"], file_verdict(parsed, truths, fault)], ["EMPTY", "OK", "S1"])
    # the verdicts on recorded results
    nothing = {"pages": [], "continue_offered": False, "boot": {}, "after": None}
    case("a verdict: FILE EMPTY + no CONTINUE against the expectation S2 FAILS",
         [file_verdict(parse_image(blank, fault), truths, fault), game_verdict(nothing, truths, fault)] == ["S2", "S2"],
         False)
    case("a verdict: FILE EMPTY + no CONTINUE against the expectation EMPTY PASSES",
         [file_verdict(parse_image(blank, fault), truths, fault), game_verdict(nothing, truths, fault)]
         == ["EMPTY", "NEW GAME ONLY"], True)
    netted = {"pages": [], "continue_offered": True, "boot": {"play_time": s2["play_time"]},
              "after": {"pids": s2["pids"], "map": s2["map"], "pos": s1["pos"]}}
    case("FAULT INPUT a netted-out save (S2's PIDs and play time on S1's tile) is neither save",
         game_verdict(netted, truths, fault), "OTHER")
    corrupted = {"pages": [{"text": "The save file is corrupted. The previous save file will be loaded."}],
                 "continue_offered": True, "boot": {"play_time": s1["play_time"]},
                 "after": {"pids": s1["pids"], "map": s1["map"], "pos": s1["pos"]}}
    case("a continuer that met the corrupted page and loaded S1", game_verdict(corrupted, truths, fault),
         "CORRUPTED PAGE + S1")
    erased = {"pages": [{"text": "The save file has been erased due to corruption or damage."}], "continue_offered": False}
    case("a continuer that met the erased page and no CONTINUE", game_verdict(erased, truths, fault),
         "ERASED PAGE + NEW GAME ONLY")
    case("fill_name: no bytes, all 0xFF, all 0x00, anything else", [fill_name(b""), fill_name(b"\xff" * 64),
                                                                    fill_name(bytes(64)), fill_name(b"\x00\xff")],
         ["absent", "erased", "zero", "data"])
    # the KM arms' registered expectations, from a recorded M2 (the numbers of the 2026-10-29 trajectory: the first
    # sector completes at e3 + 19, e3 + 18 and e3 + 18 in saves 1, 2 and 3; the writes span 257, 261 and 256 frames)
    recorded = {"saves": []}
    for index, e3, span, edge in ((1, 1000, 257, 19), (2, 2000, 261, 18), (3, 3000, 256, 18)):
        frames = {str(i): e3 + edge + round(i * (span - edge) / 13) for i in range(SECTORS_PER_SLOT)}
        recorded["saves"].append({"save": index, "events": {"e3": e3, "e4": e3 + span}, "sector_complete_frames": frames})
    case("km_arms: the default offsets (the first sector's edges among them) and each one's registered expectation",
         [[arm.name, arm.saves, arm.stop, arm.expect_file, arm.expect_game] for arm in km_arms(recorded, None, None, None)],
         [["KM-FIRST@2", 1, "S1.e3+2", "EMPTY", "NEW GAME ONLY"],
          ["KM-FIRST@18", 1, "S1.e3+18", "EMPTY", "NEW GAME ONLY"],
          ["KM-FIRST@19", 1, "S1.e3+19", "CORRUPT", "ERASED PAGE + NEW GAME ONLY"],
          ["KM-FIRST@64", 1, "S1.e3+64", "CORRUPT", "ERASED PAGE + NEW GAME ONLY"],
          ["KM-FIRST@128", 1, "S1.e3+128", "CORRUPT", "ERASED PAGE + NEW GAME ONLY"],
          ["KM-FIRST@192", 1, "S1.e3+192", "CORRUPT", "ERASED PAGE + NEW GAME ONLY"],
          ["KM-FIRST@256", 1, "S1.e3+256", "CORRUPT", "ERASED PAGE + NEW GAME ONLY"],
          ["KM-SECOND@2", 2, "S2.e3+2", "S1", "S1"],
          ["KM-SECOND@17", 2, "S2.e3+17", "S1", "S1"],
          ["KM-SECOND@18", 2, "S2.e3+18", "S1+ERROR", "CORRUPTED PAGE + S1"],
          ["KM-SECOND@65", 2, "S2.e3+65", "S1+ERROR", "CORRUPTED PAGE + S1"],
          ["KM-SECOND@130", 2, "S2.e3+130", "S1+ERROR", "CORRUPTED PAGE + S1"],
          ["KM-SECOND@195", 2, "S2.e3+195", "S1+ERROR", "CORRUPTED PAGE + S1"],
          ["KM-SECOND@260", 2, "S2.e3+260", "S1+ERROR", "CORRUPTED PAGE + S1"],
          ["KM-THIRD@0", 3, "S3.e3+0", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@2", 3, "S3.e3+2", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@17", 3, "S3.e3+17", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@18", 3, "S3.e3+18", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@64", 3, "S3.e3+64", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@128", 3, "S3.e3+128", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@192", 3, "S3.e3+192", "S2+ERROR", "CORRUPTED PAGE + S2"],
          ["KM-THIRD@255", 3, "S3.e3+255", "S2+ERROR", "CORRUPTED PAGE + S2"]])
    return {"fault": fault, "cases": cases, "ok": all(c["ok"] for c in cases),
            "failed": [c["case"] for c in cases if not c["ok"]]}


# ------------------------------------------------------------------ the children's shared reads (framework on the path)
def boot_profile(profile_dir: Path, file_backed: bool):
    """`probe_eyes.boot`, but on the throwaway profile FOLDER and, unless `file_backed` is False, with the framework's
    file-backed save (`LibmgbaEmulator(is_test_run=False)`: it opens `current_save.sav` read-write, maps it, registers its
    atexit `.ss1` and its `saves/` backup copy, and auto-loads a `current_state.ss1` that exists)."""
    from ai_player.host.launcher import resolve_build_root

    build_root = resolve_build_root()
    if str(build_root) not in sys.path:
        sys.path.insert(0, str(build_root))
    from modules.context import context
    from modules.game import set_rom
    from modules.libmgba import LibmgbaEmulator
    from modules.profiles import load_profile

    profile = load_profile(profile_dir)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)
    context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=not file_backed)
    context.audio = False
    context.video = False
    context.emulation_speed = 0
    return context


def sym_u(name: str, size: int, offset: int = 0) -> int:
    from modules.memory import read_symbol

    return int.from_bytes(bytes(read_symbol(name, offset, size)), "little")


def fn_name(pointer: int) -> str | None:
    from modules.game import get_symbol_name_before

    return get_symbol_name_before(pointer & ~1, pretty_name=True) if pointer else None


def save_flags() -> dict:
    """The game's save bookkeeping in RAM (`src/save.c`, `src/new_game.c`; recon note refute C5)."""
    return {"gSaveFileStatus": sym_u("gSaveFileStatus", 2), "gSaveCounter": sym_u("gSaveCounter", 4),
            "gLastWrittenSector": sym_u("gLastWrittenSector", 2), "gDifferentSaveFile": sym_u("gDifferentSaveFile", 1),
            "gDamagedSaveSectors": sym_u("gDamagedSaveSectors", 4)}


def ram_truth(emulator) -> dict:
    """The harness's own read of what a save holds, from RAM by symbol (the same fields `slot_content` reads from a slot):
    the party's PIDs (`gPlayerParty`, each personality u32 unencrypted), SaveBlock1's map and tile, SaveBlock2's play time,
    GAME_STAT_SAVED_GAME (XOR the key), and the save bookkeeping."""
    from modules.memory import read_symbol

    sb1, sb2 = sym_u("gSaveBlock1Ptr", 4), sym_u("gSaveBlock2Ptr", 4)
    pos = bytes(emulator.read_bytes(sb1 + SB1_POS, 4))
    location = bytes(emulator.read_bytes(sb1 + SB1_LOCATION, 2))
    play = bytes(emulator.read_bytes(sb2 + SB2_PLAY_TIME, 5))
    count = sym_u("gPlayerPartyCount", 1)
    party = bytes(read_symbol("gPlayerParty", 0, MON_SIZE * 6))
    key = _u32(bytes(emulator.read_bytes(sb2 + SB2_KEY, 4)), 0)
    saved = _u32(bytes(emulator.read_bytes(sb1 + SB1_GAME_STATS, 4)), 0) ^ key
    return {"pids": [f"{_u32(party, i * MON_SIZE):08x}" for i in range(min(count, 6))],
            "map": [location[0], location[1]], "pos": [_s16(pos, 0), _s16(pos, 2)],
            "play_time": [_u16(play, 0), play[2], play[3], play[4]], "GAME_STAT_SAVED_GAME": saved, **save_flags()}


def second_path_truth(context) -> dict:
    """The same identity by the harness's OTHER reader (`hands_harness.truth`: the framework's party decoder)."""
    from ai_player.gates.hands_harness import truth

    full = truth(context)
    party = full.get("party_exp")
    return {"pids": [p[0] for p in party] if isinstance(party, list) else party, "map": full.get("map"),
            "pos": full.get("pos")}


def printer_page(index: int) -> dict:
    """What text printer `index` shows, by the harness's reads: its own `currentChar`, the symbol table, the framework's
    decoder. While it prints: the printed part; once done: the whole string. A finished printer's pointer stands one PAST
    the string's terminator (`src/text.c` RenderText moves it before it reads EOS), which is the NEXT symbol's start, so
    a finished string is looked up from the byte before the pointer (`probe_eyes.printer_text` looks up the pointer
    itself, which would name the next symbol here: read from its code, not run)."""
    from modules.context import context
    from modules.game import decode_string, get_symbol, get_symbol_name_before
    from modules.memory import read_symbol

    raw = bytes(read_symbol("sTextPrinters", index * PRINTER_SIZE, PRINTER_SIZE))
    current, active, state = _u32(raw, 0), raw[PRINTER_ACTIVE], raw[PRINTER_STATE]
    out = {"printer": index, "active": active, "state": state, "symbol": None, "text": None, "done": None}
    if not current:
        return out
    done = bytes(context.emulator.read_bytes(current - 1, 1))[0] == 0xFF
    name = get_symbol_name_before(current - 1 if done else current, pretty_name=True)
    if not name:
        return out
    start = get_symbol(name)[0]
    end = current - 1 if done else current
    if not 0 <= end - start <= 0x400:
        return {**out, "symbol": name, "done": done}
    return {**out, "symbol": name, "done": done,
            "text": decode_string(bytes(context.emulator.read_bytes(start, end - start))) if end > start else ""}


def main_menu_task() -> tuple[str | None, int | None, int | None]:
    """The main menu's task by name (`MAIN_MENU_TASKS`) and its data[0] (tMenuType) and data[1] (tCurrItem)."""
    from modules.memory import read_symbol
    from modules.tasks import TaskList

    tasks = TaskList(read_symbol("gTasks"))
    for name in MAIN_MENU_TASKS:
        task = tasks[name]
        if task is not None:
            return name, task.data_value(0), task.data_value(1)
    return None, None, None


def callback2_name() -> str | None:
    from modules.memory import read_symbol

    return fn_name(_u32(read_symbol("gMain", 0x04, 4), 0))


def saves_listing(folder: Path) -> list:
    """[count, newest mtime_ns, total bytes] of the framework's `saves/` copies (empty folder or none: [0, 0, 0])."""
    try:
        entries = [e for e in os.scandir(folder) if e.is_file()]
    except OSError:
        return [0, 0, 0]
    return [len(entries), max((e.stat().st_mtime_ns for e in entries), default=0), sum(e.stat().st_size for e in entries)]


# ------------------------------------------------------------------ child A, the saver
class Stop:
    """`S<save>.<event>[+frames]`: stop N frames after that save's event; `S<save>.menu`: with the cursor on SAVE, before
    A. Parsed from `--stop`; None runs every save to its end."""

    def __init__(self, text: str) -> None:
        head, _, offset = text.partition("+")
        save, _, event = head.partition(".")
        if not save.startswith("S") or event not in STOP_EVENTS:
            raise ValueError(f"bad --stop {text!r}")
        self.text, self.save, self.event, self.offset = text, int(save[1:]), event, int(offset or 0)

    def reached(self, index: int, events: dict, frame: int) -> bool:
        return (index == self.save and self.event in events and self.event != "menu"
                and frame - events[self.event] >= self.offset)


class Timeline:
    """One save's events (module docstring, THE TIMELINE), updated from each frame's record."""

    def __init__(self, index: int, expected_counter: int, start: dict, after: int) -> None:
        self.index, self.expected_counter, self.after = index, expected_counter, after
        self.events: dict[str, int] = {}
        self.start = start
        self.sector_frames: dict[int, int] = {}
        self.last_change: int | None = None
        self.free_since: int | None = None
        self.questions: list[dict] = []
        self.eq_false_frames: list[int] = []
        self.truth: dict | None = None
        self.slot_at_e4: dict | None = None
        self.notes: list[str] = []

    def update(self, rec: dict, pages: list[str]) -> None:
        f, events = rec["f"], self.events
        if "e3_dirty" not in events and [rec["d"], rec["age"]] != self.start["dirt"]:
            events["e3_dirty"] = f
        if "e3_data" not in events and rec["changed_since_start"]:
            events["e3_data"] = f
        if "e3" not in events and ("e3_dirty" in events or "e3_data" in events):
            # the first write by mGBA's own mark (its dirt moved), else by the first changed byte: with no file
            # (`is_test_run=True`, arm ANON) mGBA never cleans, so its dirt stays set from the first save on and never
            # moves again (MEASURED on the development ANON arm: the second save's e3 read its first frame)
            events["e3"] = f
        if ("e2" not in events and rec["cb"] == "SaveDoSaveCallback" and not rec["p0"][0]
                and any("SAVING" in page for page in pages)):
            events["e2"] = f
        for sid in rec["new"]:
            self.sector_frames.setdefault(sid, f)
        if "e4" not in events and len(rec["new"]) == SECTORS_PER_SLOT:
            events["e4"] = f
        if rec["changed"] and "e5" not in events:
            self.last_change = f
        if not rec["eq"] and rec["fil"][0] is not None:
            self.eq_false_frames.append(f)
        if ("e5" not in events and "e4" in events and not rec["p0"][0]
                and any("saved the game" in page for page in pages)):
            events["e5"] = f
            events["e4_last_write"] = rec["age"] + 1
            events["e4_last_change"] = self.last_change
        if "e5_jingle" not in events and "e4" in events and rec["cb"] == "SaveReturnSuccessCallback":
            # (after e4 only: `sSaveDialogCallback` keeps naming the LAST dialog's callback after the box closed, so the
            # next save's first frames still read SaveReturnSuccessCallback, measured on the development M2)
            events["e5_jingle"] = f
        if "e6" not in events and rec["fl"] > self.start["flushes"]:
            events["e6"] = f
        if "e6_saves" not in events and rec["sv"][:2] != self.start["saves"][:2]:
            events["e6_saves"] = f
        if "e6_size" not in events and rec["fil"][0] is not None and rec["fil"][0] != self.start["size"]:
            # (no file read this frame, `--noread`: no size mark either; the listener and the `saves/` copy still mark it)
            events["e6_size"] = f
        if "e5" in events and "e7" not in events:
            if rec["free"]:
                self.free_since = f if self.free_since is None else self.free_since
                if f - self.free_since >= self.after:
                    events["e7"] = self.free_since
            else:
                self.free_since = None

    def result(self) -> dict:
        ev = self.events
        derived = {}
        if "e3" in ev and "e4" in ev:
            derived["write_frames_e4_minus_e3"] = ev["e4"] - ev["e3"]
        if "e4_last_write" in ev and "e6" in ev:
            derived["flush_after_last_write_e6_minus_e4_last_write"] = ev["e6"] - ev["e4_last_write"]
        if "e6" in ev and "e7" in ev:
            derived["box_free_after_flush_e7_minus_e6"] = ev["e7"] - ev["e6"]
        if "e1" in ev and "e7" in ev:
            derived["whole_dialog_e7_minus_e1"] = ev["e7"] - ev["e1"]
        if self.truth and self.slot_at_e4:
            # the RAM truth read during the write against the new slot's own bytes at e4 (both paths, the same save?)
            for side in ("emulator", "file"):
                if self.slot_at_e4.get(side) is None:
                    continue  # (`--noread`: child A never read the file, so it has no file side to compare)
                loaded = (self.slot_at_e4.get(side) or {}).get("loaded") or {}
                derived[f"slot_at_e4_{side}_equals_truth"] = all(loaded.get(k) == self.truth.get(k) for k in IDENTITY_KEYS)
        return {"save": self.index, "expected_counter": self.expected_counter, "events": dict(ev), "derived": derived,
                "sector_complete_frames": {str(k): v for k, v in sorted(self.sector_frames.items())},
                "questions": self.questions, "truth": self.truth, "slot_at_e4": self.slot_at_e4,
                "file_neq_flash_frames": {"count": len(self.eq_false_frames), "first": self.eq_false_frames[:5]},
                "start": self.start, "notes": self.notes}


class Saver:
    """Child A (module docstring)."""

    def __init__(self, args) -> None:
        self.args = args
        self.context = boot_profile(args.profile, file_backed=not args.anon)
        self.emulator = self.context.emulator
        self.save_path = Path(args.profile) / "current_save.sav"
        self.saves_dir = Path(args.profile) / "saves"
        self.stop = Stop(args.stop) if args.stop else None
        #: arms *-NOREAD (review C4, 2026-10-29): the PROBE in child A never reads the file's bytes (its size only, by
        #: stat), so its own second handle cannot be what keeps a save for the next process. The framework's flush
        #: backup (`libmgba.py`) still reads the whole file at each flush: in these arms once, at S1's flush.
        self.noread = bool(args.noread)
        self.flushes = 0
        self.flush_frames: list[int] = []
        self.emulator._core._callbacks.savedata_updated.append(self._on_flush)  # noqa: SLF001 - test side
        self.record = open(args.record, "w", encoding="utf-8", buffering=1)
        self.prev_flash: bytes | None = None
        self.prev_file: bytes | None = None
        self.emu_parse: dict | None = None
        self.file_parse: dict | None = None
        self.prev_pages: list[str] | None = None
        self.pages: list[str] = []
        self.counter: int | None = None
        self.start_flash: bytes | None = None
        self.timeline: Timeline | None = None
        self.result: dict = {"anon": bool(args.anon), "noread": self.noread, "saves": []}

    def _on_flush(self) -> None:
        """mGBA's `savedataUpdated` (the frame its clean ran: `src/gba/gba.c` GBAFrameEnded), after the framework's copy."""
        self.flushes += 1
        self.flush_frames.append(self.emulator.get_frame_count())

    def savedata(self) -> dict:
        from mgba import ffi

        data = self.emulator._core._native.memory.savedata  # noqa: SLF001 - test side: mGBA's own save bookkeeping
        return {"type": int(data.type), "file_backed": data.vf != ffi.NULL, "mapMode": int(data.mapMode),
                "dirty": int(data.dirty), "dirtAge": int(data.dirtAge)}

    # one frame, and everything recorded after it
    def frame(self, press: str | None = None, phase: str = "") -> dict:
        if press:
            self.emulator.press_button(press)
        self.emulator.run_single_frame()
        return self.observe(press, phase)

    def observe(self, press: str | None, phase: str) -> dict:
        from ai_player.gates.play_harness import shown_pages
        from ai_player.gates.probe_end_screen import game_screen
        from modules.memory import read_symbol

        emulator = self.emulator
        f = emulator.get_frame_count()
        bookkeeping = self.savedata()
        flash = bytes(emulator.read_save_data())
        changed = self.prev_flash is not None and flash != self.prev_flash
        if self.emu_parse is None or flash != self.prev_flash:
            self.emu_parse = parse_image(flash)
        self.prev_flash = flash
        data = None
        if not self.noread:
            try:
                data = self.save_path.read_bytes()  # a SECOND HANDLE on the file mGBA has mapped
            except OSError:
                data = None
        if data != self.prev_file or (self.file_parse is None and data is not None):
            self.file_parse = parse_image(data) if data is not None else None
        self.prev_file = data
        try:
            pages = shown_pages()
        except Exception as error:  # noqa: BLE001 - a record, then the reads go on
            pages = [f"(unreadable: {type(error).__name__})"]
        self.pages = pages
        printer = bytes(read_symbol("sTextPrinters", PRINTER_ACTIVE, 2))
        sb2 = sym_u("gSaveBlock2Ptr", 4)
        play = bytes(emulator.read_bytes(sb2 + SB2_PLAY_TIME, 5))
        rec = {"f": f, "ph": phase, "in": press, "d": bookkeeping["dirty"], "age": bookkeeping["dirtAge"],
               "cb": fn_name(sym_u("sSaveDialogCallback", 4)), "mcb": fn_name(sym_u("gMenuCallback", 4)),
               "p0": [printer[0], printer[1]], "free": bool(game_screen()["free"]),
               "emu": ([self.emu_parse["status"]]
                       + [[s["status"], s["counter"], s["valid"]] for s in self.emu_parse["slots"]]),
               "new": new_ids(self.emu_parse, self.counter), "changed": changed,
               "changed_since_start": self.start_flash is not None and flash != self.start_flash,
               "fil": ([len(data), self.file_parse["status"]]
                       + [[s["status"], s["counter"], s["valid"]] for s in self.file_parse["slots"]]
                       + [new_ids(self.file_parse, self.counter)]) if data is not None else [None],
               "eq": data is not None and data[:FLASH_SIZE] == flash, "sv": saves_listing(self.saves_dir),
               "fl": self.flushes, "pt": [_u16(play, 0), play[2], play[3], play[4]]}
        if pages != self.prev_pages:
            rec["pg"] = pages
            self.prev_pages = pages
        self.record.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if self.timeline is not None:
            self.timeline.update(rec, pages)
            if self.timeline.truth is None and "e3" in self.timeline.events:
                # the save's TRUTH: RAM during the write (the main loop, and with it the play-time counter, is held
                # inside SaveDoSaveCallback until the write returns: `src/main.c`, `src/start_menu.c`)
                self.timeline.truth = ram_truth(emulator)
            if self.timeline.slot_at_e4 is None and "e4" in self.timeline.events:
                self.timeline.slot_at_e4 = {"emulator": brief(self.emu_parse), "file": brief(self.file_parse)}
            self.check_stop(rec)
        return rec

    def check_stop(self, rec: dict) -> None:
        if self.stop is not None and self.timeline is not None and self.stop.reached(self.timeline.index,
                                                                                      self.timeline.events, rec["f"]):
            self.stop_here(rec)

    def until(self, test, frames: int, what: str, phase: str) -> dict:
        """Frames with no input until `test(record)` holds (bounded: else ProbeAbort)."""
        for _ in range(frames):
            rec = self.frame(phase=phase)
            if test(rec):
                return rec
        raise ProbeAbort(f"{what}: not within {frames} frames (save {self.timeline.index if self.timeline else '-'})")

    def wait(self, frames: int, phase: str) -> dict:
        rec = {}
        for _ in range(frames):
            rec = self.frame(phase=phase)
        return rec

    # the run
    def load_fixture(self) -> None:
        from ai_player.gates.hands_harness import pin_game_clock
        from ai_player.gates.probe_end_screen import game_screen
        from ai_player.gates.rate_step5 import GAME_CLOCK

        emulator = self.emulator
        boot = {"savedata_at_boot": self.savedata(), "file_size_at_boot": self.size_now(), "noread": self.noread}
        fixture = Path(self.args.fixtures) / FIXTURE
        emulator.load_save_state(fixture.read_bytes())
        pin_game_clock(emulator, GAME_CLOCK)
        boot.update({"fixture": str(fixture), "frame_after_load": emulator.get_frame_count(), "game_clock": GAME_CLOCK,
                     "savedata_after_load": self.savedata(), "flags_after_load": save_flags()})
        self.wait(SETTLE_FRAMES, "settle")
        held = [game_screen()["free"] for _ in range(1)]
        for _ in range(self.args.after):
            held.append(self.frame(phase="settle")["free"])
        if not all(held):
            raise ProbeAbort(f"the fixture's screen is not free after {SETTLE_FRAMES} frames: {held}")
        boot["truth_at_start"] = ram_truth(emulator)
        self.result["boot"] = boot

    def size_now(self) -> int | None:
        try:
            return self.save_path.stat().st_size
        except OSError:
            return None

    def menu_open(self) -> bool:
        from modules.memory import read_symbol
        from modules.tasks import TaskList

        return ("Task_ShowStartMenu" in TaskList(read_symbol("gTasks"))
                and fn_name(sym_u("gMenuCallback", 4)) == "HandleStartMenuInput")

    def do_save(self, index: int) -> None:
        from modules.memory import read_symbol

        flags = save_flags()
        self.counter = flags["gSaveCounter"] + 1
        self.start_flash = bytes(self.emulator.read_save_data())
        bookkeeping = self.savedata()
        try:
            file_now = None if self.noread else parse_image(self.save_path.read_bytes())
        except OSError:
            file_now = None
        emulator_now = parse_image(self.start_flash)
        start = {"frame": self.emulator.get_frame_count(), "flags": flags, "flushes": self.flushes,
                 "saves": saves_listing(self.saves_dir), "size": self.size_now(), "truth": ram_truth(self.emulator),
                 "dirt": [bookkeeping["dirty"], bookkeeping["dirtAge"]],
                 "emulator_status": emulator_now["status"], "emulator_sectors_28_31": emulator_now["sectors_28_31"],
                 "file_status": file_now["status"] if file_now else None,
                 "file_sectors_28_31": file_now["sectors_28_31"] if file_now else None}
        timeline = self.timeline = Timeline(index, self.counter, start, self.args.after)
        self.result["saves"].append(timeline)
        # e1: START, on a free screen; the menu must OPEN (an event can win the frame: recon game note 1.1)
        for attempt in range(3):
            rec = self.frame(press="Start", phase=f"S{index}.start")
            timeline.events.setdefault("e1", rec["f"])
            try:
                self.until(lambda r: self.menu_open(), 120, "the start menu takes input", f"S{index}.menu")
                break
            except ProbeAbort:
                timeline.notes.append(f"START attempt {attempt + 1} opened no menu")
                timeline.events.pop("e1", None)
                self.wait(30, f"S{index}.retry")
        else:
            raise ProbeAbort("START opened no menu in 3 attempts")
        # the cursor onto SAVE by reading the menu (`sStartMenuCursorPos`, `sCurrentStartMenuActions`)
        moves = []
        for _ in range(12):
            count = sym_u("sNumStartMenuActions", 1)
            actions = list(bytes(read_symbol("sCurrentStartMenuActions", 0, 9)))[:count]
            cursor = sym_u("sStartMenuCursorPos", 1)
            if MENU_ACTION_SAVE not in actions:
                raise ProbeAbort(f"no SAVE in the start menu: actions {actions}")
            target = actions.index(MENU_ACTION_SAVE)
            if cursor == target:
                break
            button = "Down" if cursor < target else "Up"
            moves.append([cursor, target, button])
            self.frame(press=button, phase=f"S{index}.cursor")
            self.wait(6, f"S{index}.cursor")
        else:
            raise ProbeAbort("the cursor never reached SAVE")
        timeline.questions.append({"menu": {"actions": actions, "cursor": cursor, "save_at": target, "moves": moves}})
        if self.stop is not None and self.stop.save == index and self.stop.event == "menu":
            self.stop_here(self.observe(None, f"S{index}.menu-stop"))
        self.wait(4, f"S{index}.menu")
        self.frame(press="A", phase=f"S{index}.choose-save")
        # the questions: A on YES only when the question's words are read; anything else ends the child
        answered = 0
        for _ in range(1500):
            rec = self.frame(phase=f"S{index}.questions")
            if rec["cb"] in ("SaveDoSaveCallback", "SaveSavingMessageCallback"):
                break
            if rec["cb"] == "SaveConfirmOverwriteDefaultNoCallback" or any("WARNING" in p for p in self.pages):
                raise ProbeAbort(f"the WARNING (a different game file) appeared: {self.pages}")
            if rec["cb"] in INPUT_CALLBACKS and not rec["p0"][0]:
                expected_words = ("Would you like to save the game?" if rec["cb"] == "SaveConfirmInputCallback"
                                  else "There is already a saved file")
                if not any(expected_words in page for page in self.pages):
                    raise ProbeAbort(f"{rec['cb']} with pages {self.pages}: not the question expected")
                self.wait(3, f"S{index}.questions")
                pressed = self.frame(press="A", phase=f"S{index}.yes")
                timeline.questions.append({"callback": rec["cb"], "pages": list(self.pages), "asked_at": rec["f"],
                                           "yes_at": pressed["f"]})
                answered += 1
                self.until(lambda r: r["cb"] not in INPUT_CALLBACKS, 60, "the YES taken", f"S{index}.questions")
        else:
            raise ProbeAbort("the dialog never reached SAVING")
        # no input until the box closes by itself and the screen is free, held
        self.until(lambda r: "e7" in timeline.events, 4000, "the box closed and the screen free", f"S{index}.saving")
        timeline.truth_after = ram_truth(self.emulator)
        if not self.args.anon and "e6" not in timeline.events:
            self.until(lambda r: "e6" in timeline.events, 600, "the flush", f"S{index}.flush")
            timeline.notes.append("the flush came after the free screen")

    def walk_one_tile(self) -> dict:
        """One tile with test-side presses: the first direction whose next tile is passable, outside tall grass, not a
        warp; held until the player object starts the step, then released; then the screen free, held 30 frames."""
        from ai_player.gates.probe_end_screen import game_screen
        from modules.map import get_map_data
        from modules.player import get_player_avatar

        avatar = get_player_avatar()
        group, number = avatar.map_group_and_number
        x, y = avatar.local_coordinates
        tried = []
        for button, (dx, dy) in (("Up", (0, -1)), ("Left", (-1, 0)), ("Right", (1, 0)), ("Down", (0, 1))):
            try:
                tile = get_map_data((int(group), int(number)), (x + dx, y + dy))
                ok = tile.collision == 0 and not tile.has_encounters and tile.tile_type == "Normal"
                tried.append([button, tile.collision, tile.has_encounters, str(tile.tile_type)])
            except Exception as error:  # noqa: BLE001 - off the map: not this way
                tried.append([button, f"{type(error).__name__}"])
                continue
            if not ok:
                continue
            self.emulator.hold_button(button)
            try:
                for _ in range(40):
                    self.frame(phase="walk")
                    if tuple(get_player_avatar().local_coordinates) != (x, y):
                        break
            finally:
                self.emulator.release_button(button)
            for _ in range(300):
                if self.frame(phase="walk")["free"] and all(self.frame(phase="walk")["free"] for _ in range(30)):
                    break
            else:
                raise ProbeAbort("the screen did not come free after the walk")
            now = tuple(get_player_avatar().local_coordinates)
            if now == (x + dx, y + dy):
                return {"from": [x, y], "to": list(now), "button": button, "tried": tried,
                        "sb1_pos": ram_truth(self.emulator)["pos"], "free": game_screen()["free"]}
            tried.append([button, "did not move there", list(now)])
        raise ProbeAbort(f"no direction walked one tile: {tried}")

    def snapshot(self, rec: dict | None) -> dict:
        return {"frame": self.emulator.get_frame_count(), "record": rec, "savedata": self.savedata(),
                "file_size": self.size_now(), "saves": saves_listing(self.saves_dir), "flushes": self.flushes,
                "flush_frames": self.flush_frames, "emulator_flash": brief(self.emu_parse), "file": brief(self.file_parse),
                "flags": save_flags()}

    def payload(self) -> dict:
        out = dict(self.result)
        out["saves"] = [t.result() if isinstance(t, Timeline) else t for t in out["saves"]]
        for t, item in zip(self.result["saves"], out["saves"]):
            if isinstance(t, Timeline):
                item["truth_after"] = getattr(t, "truth_after", None)
        out["truths"] = {f"S{t.index}": t.truth for t in self.result["saves"] if isinstance(t, Timeline) and t.truth}
        return out

    def stop_here(self, rec: dict | None) -> None:
        """The arm's frame: report, then end as the arm says. Never returns."""
        payload = self.payload()
        payload["stop"] = {"spec": self.stop.text if self.stop else None, "end": self.args.end, **self.snapshot(rec)}
        if self.timeline is not None:
            payload["stop"]["new_sectors_at_stop"] = len(new_ids(self.emu_parse, self.counter))
        self.finish("READY", payload)

    def finish(self, word: str, payload: dict) -> None:
        self.record.flush()
        print(f"{word} " + json.dumps(payload, ensure_ascii=False), flush=True)
        if self.args.end == "kill":
            for _ in range(int(BLOCK_SECONDS / 0.25)):
                time.sleep(0.25)
            print("NOT KILLED: the parent never killed this child; it ends itself (exit 5)", flush=True)
            os._exit(5)
        if self.args.end == "exit":
            os._exit(0)  # arm KX: no atexit hook runs (the framework's `.ss1` is never written)
        self.record.close()
        sys.exit(0)  # a normal exit: atexit runs the framework's shutdown (`create_save_state`: the `.ss1`)

    def run(self) -> None:
        self.load_fixture()
        for index in range(1, self.args.saves + 1):
            if index > 1:
                walks = self.result.setdefault("walks", [])
                walks.append(self.walk_one_tile())
                self.result["walk"] = walks[0]  # (the walk between S1 and S2, as before a third save existed)
            self.do_save(index)
        self.timeline = None
        self.finish("RESULT", {**self.payload(), "end": self.snapshot(None)})


# ------------------------------------------------------------------ child B, the continuer
def continuer(args) -> dict:
    import atexit

    from ai_player.gates.hands_harness import pin_game_clock
    from ai_player.gates.probe_end_screen import game_screen
    from ai_player.gates.rate_step5 import GAME_CLOCK

    profile = Path(args.profile)
    out: dict = {"ss1_at_start": (profile / "current_state.ss1").exists(), "pages": [], "presses": []}
    context = boot_profile(profile, file_backed=True)
    emulator = context.emulator
    atexit.unregister(emulator.shutdown)  # the continuer leaves no `.ss1` (test side; it changes nothing it measures)
    pin_game_clock(emulator, GAME_CLOCK)
    out["frame_after_boot"] = emulator.get_frame_count()
    record = open(args.record, "w", encoding="utf-8", buffering=1)

    def step(press: str | None = None, note: dict | None = None) -> int:
        if press:
            emulator.press_button(press)
            out["presses"].append([emulator.get_frame_count() + 1, press])
        emulator.run_single_frame()
        f = emulator.get_frame_count()
        record.write(json.dumps({"f": f, "in": press, "cb2": callback2_name(), **(note or {})}) + "\n")
        return f

    # (1) power-on to the main menu: START every 20 frames until one of its tasks exists, never after
    for i in range(4000):
        if main_menu_task()[0] is not None:
            break
        step("Start" if i % 20 == 10 else None)
    else:
        raise ProbeAbort("no main menu within 4000 frames of power-on")
    out["main_menu_at"] = emulator.get_frame_count()
    # (2) the error pages (each read by its words when fully printed, then A), then the menu's own input task
    answered: dict[str, int] = {}
    seen_status: list[int] = []
    for _ in range(3000):
        name, data0, data1 = main_menu_task()
        status = sym_u("gSaveFileStatus", 2)
        if not seen_status or seen_status[-1] != status:
            seen_status.append(status)
        note = {"task": name, "d0": data0, "d1": data1, "status": status}
        if name in ERROR_TASKS:
            page = printer_page(7)
            note["p7"] = [page["active"], page["state"], page["symbol"]]
            key = f"{name}:{page['symbol']}"
            if not page["active"]:
                if key not in answered:
                    out["pages"].append({"task": name, "symbol": page["symbol"], "text": page["text"],
                                         "frame": emulator.get_frame_count()})
                    answered[key] = emulator.get_frame_count()
                if emulator.get_frame_count() - answered[key] in (5, 65, 125):
                    step("A", note)
                    continue
            elif page["state"] in (2, 3):  # a page break inside the text waits for A
                pause_key = f"{key}:pause:{page['text']}"
                if pause_key not in answered:
                    out["pages"].append({"task": name, "symbol": page["symbol"], "text": page["text"], "partial": True,
                                         "frame": emulator.get_frame_count()})
                    answered[pause_key] = emulator.get_frame_count()
                if emulator.get_frame_count() - answered[pause_key] in (5, 65):
                    step("A", note)
                    continue
        elif name == "Task_HandleMainMenuInput":
            out["menu_type"], out["menu_cursor"] = data0, data1
            break
        step(None, note)
    else:
        raise ProbeAbort("the main menu never took input")
    out["status_seen"] = seen_status
    out["boot_status"] = seen_status[-1] if seen_status else None
    out["boot"] = ram_truth(emulator)  # what the power-on read copied into RAM (`LoadGameSave`), before CONTINUE
    out["continue_offered"] = out["menu_type"] is not None and out["menu_type"] >= HAS_SAVED_GAME
    if not out["continue_offered"]:
        record.close()
        return out
    if out["menu_cursor"] != 0:
        raise ProbeAbort(f"the cursor is on item {out['menu_cursor']}, not CONTINUE")
    for _ in range(5):
        step()
    out["continue_pressed_at"] = step("A")
    # (3) CONTINUE to a free overworld, held
    free_since = None
    for _ in range(4000):
        f = step()
        if game_screen()["free"]:
            free_since = f if free_since is None else free_since
            if f - free_since >= args.after:
                break
        else:
            free_since = None
    else:
        raise ProbeAbort("CONTINUE gave no free overworld within 4000 frames")
    out["free_at"] = free_since
    out["after"] = ram_truth(emulator)
    out["after_second_path"] = second_path_truth(context)
    out["callback2_at_free"] = callback2_name()
    record.close()
    return out


# ------------------------------------------------------------------ the M6 child
def m6_child(args) -> dict:
    import atexit

    from ai_player.gates.probe_end_screen import game_screen

    profile = Path(args.profile)
    state = (profile / "current_state.ss1").read_bytes()
    out: dict = {"state_magic": f"{_u32(state, 0):08x}", "state_bytes": len(state)}
    try:
        context = boot_profile(profile, file_backed=True)  # the framework's own auto-load (`libmgba.py` LibmgbaEmulator)
    except Exception as error:  # noqa: BLE001 - "silent" is the question: a raise is the answer then
        out["raised"] = f"{type(error).__name__}: {error}"
        return out
    out["raised"] = None
    emulator = context.emulator
    atexit.unregister(emulator.shutdown)
    out["frame_after_init"] = emulator.get_frame_count()
    names: list[list] = []
    overworld_at = None
    for _ in range(args.m6_frames):
        emulator.run_single_frame()
        name = callback2_name()
        if not names or names[-1][1] != name:
            names.append([emulator.get_frame_count(), name])
        if overworld_at is None and game_screen()["overworld"]:
            overworld_at = emulator.get_frame_count()
            out["overworld_truth"] = ram_truth(emulator)
    out["callback2_changes"] = names[:20]
    out["overworld_at"] = overworld_at
    # the core's own answer for the same bytes, asked AFTER the observation (the framework ignores it)
    import mgba.vfs

    vfile = mgba.vfs.VFile.fromEmpty()
    vfile.write(state, len(state))
    vfile.seek(0, whence=0)
    out["core_load_state_returned"] = bool(emulator._core.load_state(vfile))  # noqa: SLF001 - test side
    return out


def child(args) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    try:
        if args.role == "saver":
            Saver(args).run()
            return 0
        result = continuer(args) if args.role == "continuer" else m6_child(args)
        print("RESULT " + json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    except ProbeAbort as error:
        print("ABORT " + json.dumps({"abort": str(error)}, ensure_ascii=False), flush=True)
        os._exit(3)


# ------------------------------------------------------------------ the parent
class Arm:
    def __init__(self, name: str, saves: int = 2, stop: str | None = None, end: str = "kill", anon: bool = False,
                 trunc: int | None = None, expect_file: str | None = None, expect_game: str | None = None,
                 expect_ss1: bool = False, role: str = "saver", continuer: bool = True, prefill: bool = False,
                 bump: bool = False, why: str = "", spec: tuple | None = None, mix: bool = False,
                 noread: bool = False) -> None:
        self.name, self.saves, self.stop, self.end, self.anon, self.trunc = name, saves, stop, end, anon, trunc
        self.expect_file, self.expect_game, self.expect_ss1 = expect_file, expect_game, expect_ss1
        self.role, self.continuer, self.prefill, self.bump, self.why = role, continuer, prefill, bump, why
        #: MIXED: the parent splices the file before child B (`mix_slot`); NOREAD: the probe in child A never reads the
        #: file's bytes (the framework's flush backup still does)
        self.mix, self.noread = mix, noread
        #: what the BUILD SPEC's section 1 expects, (FILE verdicts accepted, GAME verdicts accepted), None = says nothing;
        #: a verdict ending in "*" accepts any ending. Reported beside the registered expectation, never in its place:
        #: where the measurement and the spec disagree, the spec's section-0 claim is the finding.
        self.spec = spec


def spec_match(verdict: str | None, accepted: tuple | None) -> bool | None:
    if accepted is None:
        return None
    return any(verdict == a or (a.endswith("*") and str(verdict).startswith(a[:-1])) for a in accepted)


SPEC_S2 = (("S2",), ("S2",))
#: the fixed arms and their expectations (the KM arms are made from M2: `km_arms`)
FIXED_ARMS = {
    "NOSAVE": Arm("NOSAVE", 1, "S1.menu", expect_file="EMPTY", expect_game="NEW GAME ONLY",
                  why="discriminator: killed with the cursor on SAVE, before A", spec=(("EMPTY",), ("NEW GAME ONLY",))),
    "ANON": Arm("ANON", 2, "S2.e4+40", anon=True, expect_file="EMPTY", expect_game="NEW GAME ONLY",
                why="discriminator: K2's script with is_test_run=True (anonymous flash): the FILE check must read the file",
                spec=(("EMPTY",), None)),
    "TRUNC": Arm("TRUNC", 2, "S2.e4+40", trunc=TRUNC_BYTES, expect_file="S2+ERROR", expect_game="CORRUPTED PAGE + S2",
                 why="discriminator: K2's script, then the file cut to 64 KB (S2's slot whole, S1's slot keeps 2 sectors): "
                     "the game must say corrupt", spec=(None, ("CORRUPTED PAGE + *", "ERASED PAGE + *"))),
    "MIXED": Arm("MIXED", 2, "S2.e4+40", mix=True, expect_file="S2+MIXED", expect_game="S2",
                 why="discriminator for the FILE check's counters (review F1): K2's script, then S2's slot spliced with "
                     "S1's sectors (mix_slot: all 14 still valid, two counters): the FILE verdict must flag it; the game, "
                     "which never compares the counters, is expected to load S2 with no page"),
    "K0": Arm("K0", 2, "S2.e4+0", expect_file="S2", expect_game="S2", why="kill on the frame S2's slot completes",
              spec=SPEC_S2),
    "K1": Arm("K1", 2, "S2.e4+8", expect_file="S2", expect_game="S2", why="kill 8 frames after, before the flush",
              spec=SPEC_S2),
    "K2": Arm("K2", 2, "S2.e4+40", expect_file="S2", expect_game="S2", why="kill 40 frames after, after the flush",
              spec=SPEC_S2),
    "KX": Arm("KX", 2, "S2.e4+8", end="exit", expect_file="S2", expect_game="S2",
              why="os._exit at K1's frame (no atexit hook)", spec=SPEC_S2),
    "CLEAN": Arm("CLEAN", 2, "S2.e4+40", end="clean", expect_file="S2", expect_game="S2", expect_ss1=True,
                 why="a normal exit at K2's frame: the control that leaves a .ss1", spec=SPEC_S2),
    "K1-NOREAD": Arm("K1-NOREAD", 2, "S2.e4+8", noread=True, expect_file="S2", expect_game="S2",
                     why="K1 with the probe in child A never reading current_save.sav (review C4; the framework's "
                         "flush backup still reads it once, at S1's flush): the probe's own second handle is not what "
                         "keeps a pre-flush save", spec=SPEC_S2),
    "KX-NOREAD": Arm("KX-NOREAD", 2, "S2.e4+8", end="exit", noread=True, expect_file="S2", expect_game="S2",
                     why="KX with the probe in child A never reading current_save.sav (review C4)", spec=SPEC_S2),
    "K2-THIRD": Arm("K2-THIRD", 3, "S3.e4+40", expect_file="S3", expect_game="S3",
                    why="a THIRD save complete and flushed, killed 40 frames after its e4: the control for KM-THIRD "
                        "(review C6)", spec=(("S3",), ("S3",))),
    "ERASE28": Arm("ERASE28", 1, None, end="exit", expect_file="S1", continuer=False, prefill=True,
                   why="one save from a .sav whose sectors 28-31 hold 0x00: the first save's SAVE_OVERWRITE_DIFFERENT_FILE "
                       "must erase them (recon claim 6)"),
    "M6": Arm("M6", role="m6", bump=True, continuer=False, why="a fixture .ss1 with its magic bumped, auto-loaded"),
    "M6-CONTROL": Arm("M6-CONTROL", role="m6", continuer=False, why="the same .ss1 unbumped, auto-loaded"),
}
ORDER = ("M2", "NOSAVE", "ANON", "TRUNC", "MIXED", "KM-FIRST", "KM-SECOND", "KM-THIRD", "K0", "K1", "K2", "KX", "CLEAN",
         "K1-NOREAD", "KX-NOREAD", "K2-THIRD", "ERASE28", "M6", "M6-CONTROL")
#: the discriminators (build spec section 1; CLAUDE.md Tier 2 (4)): each must DIFFER from K2, or it proves nothing
DISCRIMINATORS = ("NOSAVE", "ANON", "TRUNC", "MIXED")


def km_arms(m2: dict | None, first: list[int] | None, second: list[int] | None,
            third: list[int] | None = None) -> list[Arm]:
    """KM-FIRST@N, KM-SECOND@N and KM-THIRD@N: a kill N frames after e3 of that save. N defaults to 2 (inside the first
    sector), the first sector's last incomplete frame and the frame it completes (M2's record: the edges of the window in
    which a cut leaves the new slot with no signed sector, review C5, 2026-10-29), a quarter, half and three quarters of
    M2's [e3, e4), and its last frame e4 - 1 (13 sectors done); the third save adds 0, the frame its write starts. For the
    first two saves the expectation follows M2's record of the sectors complete at e3 + N. A third save writes into the
    slot that holds the FIRST: erasing its first target sector already destroys one of that slot's sectors, and its
    rotation is two sectors on from the first save's, so until its last sector every in-order cut leaves at least one id
    missing (with no shift a cut would leave a whole MIXED slot instead): a cut anywhere in [e3, e4) leaves that slot
    ERROR and the second save loads (the selftest's every in-order cut; measured by the review with a patched copy, C6;
    the fix round's review read M2's record ERROR on all 256 frames of the third write): every N expects S2+ERROR and
    the corrupted page."""
    arms = []
    saves = {s["save"]: s for s in ((m2 or {}).get("saves") or [])}
    for index, wanted, family in ((1, first, "KM-FIRST"), (2, second, "KM-SECOND"), (3, third, "KM-THIRD")):
        save = saves.get(index)
        if not save or "e3" not in save["events"] or "e4" not in save["events"]:
            continue
        e3, e4 = save["events"]["e3"], save["events"]["e4"]
        span = e4 - e3
        frames = list(save["sector_complete_frames"].values())
        defaults = {2, span // 4, span // 2, (3 * span) // 4, span - 1}
        if frames:
            edge = min(frames) - e3
            defaults |= {edge - 1, edge}
        if index >= 3:
            defaults.add(0)
        offsets = wanted or sorted(defaults)
        for n in offsets:
            if not 0 <= n < span:
                continue
            complete = sum(1 for frame in frames if frame <= e3 + n)
            if index == 1:
                expect = ("CORRUPT", "ERASED PAGE + NEW GAME ONLY") if complete else ("EMPTY", "NEW GAME ONLY")
                spec = (("EMPTY", "CORRUPT"), ("ERASED PAGE + NEW GAME ONLY",))  # "FILE no valid slot; the erased page"
            elif index == 2:
                expect = ("S1+ERROR", "CORRUPTED PAGE + S1") if complete else ("S1", "S1")
                spec = (("S1+ERROR",), ("CORRUPTED PAGE + S1",))  # "S1 valid, S2's slot torn; the corrupted page, S1"
            else:
                expect = ("S2+ERROR", "CORRUPTED PAGE + S2")
                spec = (("S2+ERROR",), ("CORRUPTED PAGE + S2",))  # claim 5: "the previous save then loads", the page
            arms.append(Arm(f"{family}@{n}", index, f"S{index}.e3+{n}", expect_file=expect[0], expect_game=expect[1],
                            why=f"kill {n} frames after e3 of save {index}; M2: {complete} of 14 sectors of the new slot "
                                f"complete at e3+{n} (e4-e3 = {span})", spec=spec))
    return arms


class Child:
    """A child process of the probe, its output pumped into a log and a queue. Killed only by ITS OWN PID."""

    def __init__(self, cmd: list[str], env: dict, cwd: Path, log: Path, arm: str, role: str) -> None:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        self.started = time.time()
        self.proc = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, creationflags=flags)
        self.pid, self.arm, self.role, self.log = self.proc.pid, arm, role, log
        self.lines: queue.Queue = queue.Queue()
        self.tail: list[str] = []
        #: the child's own descendants, seen while it ran (on Windows a console process gets a `conhost.exe` helper,
        #: MEASURED on the development arms): never killed by the probe, checked GONE after the child ended
        self.descendants: dict[int, str] = {}
        threading.Thread(target=self._pump, daemon=True).start()

    def note_descendants(self) -> None:
        import psutil

        try:
            for process in psutil.Process(self.pid).children(recursive=True):
                try:
                    self.descendants[process.pid] = process.name()
                except psutil.Error:
                    self.descendants[process.pid] = "?"
        except psutil.Error:
            pass

    def descendants_alive(self, seconds: float = 10.0) -> list[list]:
        """The descendants noted while the child ran that are STILL alive after up to `seconds` (bounded, never killed)."""
        import psutil

        deadline = time.monotonic() + seconds
        while True:
            alive = []
            for pid, name in self.descendants.items():
                try:
                    if psutil.Process(pid).status() != psutil.STATUS_ZOMBIE:
                        alive.append([pid, name])
                except psutil.Error:
                    pass
            if not alive or time.monotonic() >= deadline:
                return alive
            time.sleep(0.25)

    def _pump(self) -> None:
        with open(self.log, "a", encoding="utf-8", errors="replace") as handle:
            for raw in iter(self.proc.stdout.readline, b""):
                text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                handle.write(text + "\n")
                handle.flush()
                self.tail = (self.tail + [text[:300]])[-8:]
                self.lines.put(text)
        self.lines.put(None)

    def wait_for(self, words: tuple[str, ...], seconds: float) -> tuple[str, dict]:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is None:
                return "EOF", {"tail": self.tail, "exit": self.proc.poll()}
            for word in words:
                if line.startswith(word + " "):
                    self.note_descendants()
                    return word, json.loads(line[len(word) + 1:])
        return "TIMEOUT", {"tail": self.tail}

    def kill(self) -> dict:
        import psutil

        process = psutil.Process(self.pid)
        self.note_descendants()
        began = time.monotonic()
        process.kill()  # TerminateProcess on THIS child's PID only (psutil: the exit code is 15)
        code = self.proc.wait(timeout=60)
        return {"killed_pid": self.pid, "descendants_before_kill": [[p, n] for p, n in self.descendants.items()],
                "exit_code": code, "seconds_to_exit": round(time.monotonic() - began, 3),
                "descendants_alive_after": self.descendants_alive()}

    def finish(self, seconds: float) -> int | None:
        try:
            return self.proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            self.kill()
            return None


def child_env(build_root: Path) -> dict:
    from ai_player.host.launcher import ENV_BUILD_ROOT, UNTRUSTED_ENV

    env = {k: v for k, v in os.environ.items() if k not in UNTRUSTED_ENV and not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1", "COLUMNS": "20000",
                ENV_BUILD_ROOT: str(build_root)})
    return env


def ss1_files(profile: Path) -> dict:
    states = profile / "states"
    return {"current_state.ss1": (profile / "current_state.ss1").exists(),
            "states": sorted(p.name for p in states.glob("*.ss1")) if states.is_dir() else []}


def run_arm(arm: Arm, ctx: dict) -> dict:
    out_dir: Path = ctx["out"] / arm.name.replace("@", "_at_")
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists: a fresh --out is needed (nothing is reused)")
    profile = out_dir / "profile"
    profile.mkdir(parents=True)
    shutil.copy2(ctx["donor"], profile / "metadata.yml")
    save = profile / "current_save.sav"
    if arm.prefill:
        image = bytearray([0xFF]) * FLASH_SIZE
        image[28 * SECTOR_SIZE:32 * SECTOR_SIZE] = bytes(4 * SECTOR_SIZE)
        save.write_bytes(bytes(image))
    else:
        save.write_bytes(b"")
    fixture = ctx["fixtures"] / FIXTURE
    script = ctx["root"] / "ai_player" / "gates" / "probe_save_kill.py"
    base = [sys.executable, "-B", str(script), "child", "--profile", str(profile), "--fixtures", str(ctx["fixtures"]),
            "--after", str(ctx["after"])]
    row: dict = {"arm": arm.name, "why": arm.why, "stop": arm.stop, "end": arm.end,
                 "expected": {"file": arm.expect_file, "game": arm.expect_game, "ss1_left": arm.expect_ss1},
                 "spec_expected": {"file": arm.spec[0], "game": arm.spec[1]} if arm.spec else None}
    if arm.role == "m6":
        data = fixture.read_bytes()
        if arm.bump:
            data = BUMPED_MAGIC.to_bytes(4, "little") + data[4:]
        (profile / "current_state.ss1").write_bytes(data)
        a = Child(base + ["--role", "m6", "--record", str(out_dir / "m6_frames.jsonl"), "--m6-frames", "300"],
                  ctx["env"], ctx["root"], out_dir / "child_m6.out", arm.name, "m6")
        ctx["children"].append(a)
        word, result = a.wait_for(("RESULT", "ABORT"), ctx["timeout"])
        row["child"] = {"pid": a.pid, "word": word, "exit": a.finish(60)}
        row["m6"] = result
        cold = (word == "RESULT" and result.get("raised") is None and result.get("frame_after_init") == 0
                and result.get("overworld_at") is None)
        loaded = (word == "RESULT" and result.get("raised") is None and (result.get("frame_after_init") or 0) > 0
                  and result.get("overworld_at") == (result.get("frame_after_init") or 0) + 1)
        row["verdict"] = "COLD BOOT (silent)" if cold else "FIXTURE LOADED" if loaded else "NEITHER"
        row["expected"] = {"m6": "COLD BOOT (silent)" if arm.bump else "FIXTURE LOADED"}
        row["pass"] = row["verdict"] == row["expected"]["m6"]
        return row
    # child A
    cmd = (base + ["--role", "saver", "--record", str(out_dir / "a_frames.jsonl"), "--saves", str(arm.saves),
                   "--end", arm.end] + (["--stop", arm.stop] if arm.stop else []) + (["--anon"] if arm.anon else [])
           + (["--noread"] if arm.noread else []))
    a = Child(cmd, ctx["env"], ctx["root"], out_dir / "child_a.out", arm.name, "saver")
    ctx["children"].append(a)
    word, result = a.wait_for(("READY", "RESULT", "ABORT"), ctx["timeout"])
    row["child_a"] = {"pid": a.pid, "word": word}
    if word == "READY" and arm.end == "kill":
        row["child_a"]["kill"] = a.kill()
        row["child_a"]["exit"] = row["child_a"]["kill"]["exit_code"]
    else:
        row["child_a"]["exit"] = a.finish(120)
    row["child_a"]["alive_after"] = a.proc.poll() is None
    if word not in ("READY", "RESULT") or (arm.stop is not None and word != "READY"):
        row["child_a"]["detail"] = result if word != "RESULT" else "RESULT where the arm's stop should have printed READY"
        row["pass"] = False
        row["file"] = row["game"] = {"verdict": f"NOT RUN (child A ended with {word}, not its stop)"}
        return row
    truths = result.get("truths") or {}
    row["truths"] = truths
    row["saver"] = {k: result.get(k) for k in ("boot", "walk", "walks", "stop", "end", "anon", "noread")}
    row["saves"] = result.get("saves")
    # FILE: the parent's parse of current_save.sav, after child A is gone
    row["ss1_after_a"] = ss1_files(profile)
    data = save.read_bytes() if save.exists() else None
    parse = parse_image(data) if data is not None else None
    row["file_after_a"] = {"size": len(data) if data is not None else None, "parse": brief(parse)}
    if arm.trunc is not None and data is not None:
        os.truncate(save, arm.trunc)
        data = save.read_bytes()
        parse = parse_image(data)
        row["file_after_trunc"] = {"size": len(data), "parse": brief(parse)}
    if arm.mix and parse is not None:
        if parse["status"] == "OK" and all(s["status"] == "OK" for s in parse["slots"]):
            spliced, row["mix"] = mix_slot(data, parse)
            save.write_bytes(spliced)
            data = save.read_bytes()
            parse = parse_image(data)
            row["file_after_mix"] = {"size": len(data), "parse": brief(parse)}
        else:
            row["mix"] = {"skipped": f"not two OK slots to splice: status {parse['status']}, slots "
                                     f"{[s['status'] for s in parse['slots']]}"}
    row["file"] = {"verdict": file_verdict(parse, truths), "status": parse["status"] if parse else None,
                   "loaded": parse["loaded"] if parse else None,
                   "loaded_all14_counters_equal": parse["loaded_all14_counters_equal"] if parse else None,
                   "sectors_28_31": parse["sectors_28_31"] if parse else None}
    saves_dir = profile / "saves"
    row["saves_dir"] = sorted([p.name, p.stat().st_size] for p in saves_dir.glob("*")) if saves_dir.is_dir() else []
    ss1_left = row["ss1_after_a"]["current_state.ss1"]
    for path in [profile / "current_state.ss1"] + sorted((profile / "states").glob("*.ss1")):
        if path.exists():
            path.unlink()
    row["ss1_deleted_before_b"] = True
    ok_ss1 = ss1_left == arm.expect_ss1
    if not arm.continuer:
        row["game"] = {"verdict": "NOT RUN (no continuer in this arm)"}
        ok_erase = (not arm.prefill) or row["file"]["sectors_28_31"] == ["erased"] * 4
        row["pass"] = row["file"]["verdict"] == arm.expect_file and ok_ss1 and ok_erase
        return row
    # GAME: child B
    b = Child(base + ["--role", "continuer", "--record", str(out_dir / "b_frames.jsonl")], ctx["env"], ctx["root"],
              out_dir / "child_b.out", arm.name, "continuer")
    ctx["children"].append(b)
    word_b, result_b = b.wait_for(("RESULT", "ABORT"), ctx["timeout"])
    row["child_b"] = {"pid": b.pid, "word": word_b, "exit": b.finish(120)}
    row["child_b"]["alive_after"] = b.proc.poll() is None
    row["game"] = {"verdict": game_verdict(result_b if word_b in ("RESULT", "ABORT") else None, truths),
                   "pages": result_b.get("pages"), "boot_status": result_b.get("boot_status"),
                   "status_seen": result_b.get("status_seen"), "menu_type": result_b.get("menu_type"),
                   "continue_offered": result_b.get("continue_offered"), "boot": result_b.get("boot"),
                   "after": result_b.get("after"), "after_second_path": result_b.get("after_second_path"),
                   "ss1_at_start": result_b.get("ss1_at_start"), "abort": result_b.get("abort")}
    row["file_after_b"] = {"size": save.stat().st_size if save.exists() else None}
    if arm.trunc is not None and save.exists():
        # what child B's mGBA grew the cut file back with (BUILD-REPORT open question 5; recorded, NOT graded)
        grown = save.read_bytes()[:FLASH_SIZE]
        row["file_after_b"]["regrown"] = {"from": arm.trunc, "to": len(grown), "fill": fill_name(grown[arm.trunc:])}
    row["pass"] = (row["file"]["verdict"] == arm.expect_file and row["game"]["verdict"] == arm.expect_game and ok_ss1)
    if arm.spec:
        row["matches_spec"] = {"file": spec_match(row["file"]["verdict"], arm.spec[0]),
                               "game": spec_match(row["game"]["verdict"], arm.spec[1])}
    return row


def run(args) -> int:
    from ai_player.host.launcher import ENV_BUILD_ROOT, resolve_build_root

    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    build_root = Path(args.build_root or os.environ.get(ENV_BUILD_ROOT) or resolve_build_root()).resolve()
    from ai_player.gates.hands_harness import PROFILE

    ctx = {"root": root, "out": out, "fixtures": args.fixtures.resolve(), "after": args.after,
           "timeout": args.child_timeout, "donor": build_root / "profiles" / PROFILE / "metadata.yml",
           "env": child_env(build_root), "children": []}
    wanted = [a.strip() for a in (args.arms or ",".join(ORDER)).split(",") if a.strip()]
    began = time.time()
    print("PROBE START " + json.dumps({"root": str(root), "out": str(out), "build_root": str(build_root),
                                       "fixtures": str(ctx["fixtures"]), "arms": wanted, "after": args.after,
                                       "started": time.strftime("%Y-%m-%d %I:%M:%S %p")}), flush=True)
    rows = []
    m2 = None
    if any(w.startswith("KM") for w in wanted) or "M2" in wanted:
        m2_row = run_arm(Arm("M2", M2_SAVES, None, end="clean", expect_ss1=True, continuer=False,
                             why=f"the timeline of {M2_SAVES} saves, no kill (a clean exit after the last is free)"), ctx)
        m2_row["expected"] = {"file": f"S{M2_SAVES} (recorded, not graded)", "ss1_left": True}
        m2_row["pass"] = None
        m2 = {"saves": m2_row.get("saves")}
        print("PROBE " + json.dumps(m2_row, ensure_ascii=False), flush=True)
        rows.append(m2_row)
    arms: list[Arm] = []
    for name in wanted:
        if name == "M2":
            continue
        if name in ("KM-FIRST", "KM-SECOND", "KM-THIRD"):
            arms += [a for a in km_arms(m2, args.km_first, args.km_second, args.km_third) if a.name.startswith(name + "@")]
        elif name in FIXED_ARMS:
            arms.append(FIXED_ARMS[name])
        else:
            raise SystemExit(f"unknown arm {name!r}: {ORDER}")
    for arm in arms:
        row = run_arm(arm, ctx)
        print("PROBE " + json.dumps(row, ensure_ascii=False), flush=True)
        rows.append(row)
    time.sleep(1.0)
    children = [{"pid": c.pid, "arm": c.arm, "role": c.role, "exit": c.proc.poll(), "alive": c.proc.poll() is None,
                 "descendants_seen": [[p, n] for p, n in c.descendants.items()],
                 "descendants_alive": c.descendants_alive(2.0)} for c in ctx["children"]]
    graded = [r for r in rows if r.get("pass") is not None]
    verdicts = {r["arm"]: [(r.get("file") or {}).get("verdict"), (r.get("game") or {}).get("verdict")] for r in rows}
    # (spec section 1, CLAUDE.md Tier 2 (4)) each discriminator must DIFFER from K2, or the arm it matches proves nothing
    discriminators = {name: {"file_game": verdicts[name], "K2": verdicts.get("K2"),
                             "differs_from_K2": verdicts.get("K2") is not None and verdicts[name] != verdicts["K2"]}
                      for name in DISCRIMINATORS if name in verdicts}
    summary = {"arms": [[r["arm"], r.get("file", {}).get("verdict") if "file" in r else r.get("verdict"),
                         r.get("game", {}).get("verdict") if "game" in r else None, r.get("pass")] for r in rows],
               "graded": len(graded), "passed": sum(1 for r in graded if r["pass"]),
               "failed": [r["arm"] for r in graded if not r["pass"]], "discriminators": discriminators,
               # where the measured verdict is not what the BUILD SPEC's section 1 expected (a finding about the spec's
               # section-0 claims, reported, never tuned away: the registered expectation is what `pass` grades)
               "spec_disagreements": [[r["arm"], verdicts[r["arm"]], r["spec_expected"], r["matches_spec"]]
                                      for r in rows if r.get("matches_spec") and False in r["matches_spec"].values()],
               "children": children,
               "children_alive": [c["pid"] for c in children if c["alive"]],
               "descendants_alive": [d for c in children for d in c["descendants_alive"]],
               "seconds": round(time.time() - began, 1), "ended": time.strftime("%Y-%m-%d %I:%M:%S %p")}
    print("PROBE SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if (not summary["failed"] and not summary["children_alive"] and not summary["descendants_alive"]
                 and all(d["differs_from_K2"] for d in discriminators.values())) else 1


def offsets(text: str | None) -> list[int] | None:
    return [int(x) for x in text.split(",")] if text else None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("run", "selftest", "child"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--build-root")
    parser.add_argument("--arms")
    parser.add_argument("--km-first", type=offsets)
    parser.add_argument("--km-second", type=offsets)
    parser.add_argument("--km-third", type=offsets)
    parser.add_argument("--after", type=int, default=DEFAULT_AFTER)
    parser.add_argument("--child-timeout", type=float, default=600.0)
    parser.add_argument("--fault", choices=FAULTS)
    # the child's own
    parser.add_argument("--role", choices=("saver", "continuer", "m6"))
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--saves", type=int, default=2)
    parser.add_argument("--stop")
    parser.add_argument("--end", choices=("kill", "exit", "clean"), default="kill")
    parser.add_argument("--anon", action="store_true")
    parser.add_argument("--noread", action="store_true")
    parser.add_argument("--m6-frames", type=int, default=300)
    args = parser.parse_args()
    if args.mode == "selftest":
        result = selftest(args.fault)
        print("SELFTEST " + json.dumps(result, ensure_ascii=False), flush=True)
        print(f"SELFTEST VERDICT: {'PASS' if result['ok'] else 'FAIL'}"
              + (f" (fault {args.fault}: failed {result['failed']})" if args.fault else ""), flush=True)
        return 0 if result["ok"] else 1
    if args.mode == "child":
        if args.role is None or args.profile is None or args.record is None:
            parser.error("child needs --role, --profile and --record")
        return child(args)
    if args.fixtures is None or args.out is None:
        parser.error("run needs --fixtures and --out")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
