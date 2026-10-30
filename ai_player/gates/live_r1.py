"""R1 + R2 LIVE PROOF DRIVER (TEST SIDE, not in the lane; never the AI's code): the AI SAVES through the game's own dialog,
is KILLED, and CONTINUES its own save, graded by the harness's own reads (build spec 2026-10-29 section 5).

    py -3.12 -B live_r1.py control --seed N --out DIR [--frames F] [--build-root DIR]
    py -3.12 -B live_r1.py arm --arm NAME --seed N --out DIR [--between-from CONTROL_ROW] [--frames F] [--build-root DIR]
    py -3.12 -B live_r1.py grade ROW.json ...                     (offline: re-grade recorded rows)
    py -3.12 -B live_r1.py measure --out DIR                       (offline: step 6 (b)'s numbers over the CONTROL rows)
    `child-a` and `child-b` are the internal entries of the child processes.

WHY A PARENT AND CHILDREN (the probe's pattern, `gates/probe_save_kill.py`): a kill cannot be observed from inside the
process it kills. So:
  * CHILD A is the REAL play brain, in-process (`play_harness.run` with `--profile-dir`: a FILE-BACKED cartridge save on a
    throwaway profile under `--out/profiles/`, never under the build root's; builder note 1), from a NEW GAME on an
    EMPTY cart (asserted before it boots: no save, no `.ss1`, finding F14), the cartridge clock pinned, with `--memory`
    (always the profile's `AppPaths` path). A test-side per-frame watcher (`SaveWatch`) records each save's flash write
    from the emulator's own flash (e3: the first changed byte; the sectors complete with the new counter, each at its
    frame; e4: all 14), the RAM truth at e3 (`probe_save_kill.ram_truth`: PIDs, map, tile, play time), the AI's memory
    lines as they reach the file, every map the player stands on (RAM), every START press with the harness's own HELD
    free read before it (`probe_end_screen.game_screen`) and the big moments' proofs (`knowledge/milestones.json`, the
    harness's flag reads). At the arm's frame it prints READY and BLOCKS (no frame in flight); the parent kills ITS PID.
  * At the kill the parent FREEZES the cart and the memory (findings G6, F12) and reads the FILE verdict with the probe's
    own parser (`parse_image` + `file_verdict`, builder note 4).
  * CHILD B is the AI continuing: its own copy of the frozen set, the launcher's `memory_check` and `seed_profile`
    continue branch first, then the same brain with `--continue` for `CONTINUE_BUDGET + ARRIVAL_BUDGET + 600` frames. Its
    watcher (`ArrivalWatch`) reads, by the harness: the play time the power-on read copied into RAM, the main menu's task
    and cursor at every press, the error pages' words (printer 7), and the HELD free arrival's identity.

KILL POINTS AND EXPECTATIONS (spec section 5; ORCHESTRATOR RULING 1, 2026-10-29): no constant rests on the probe's exact
frame counts. Every expectation that depends on how far a write has got follows the NEW-SECTOR COUNT the arm's OWN
per-frame record shows AT the kill frame (`expected_file`). K-SILENT counts only if its record shows the AI's S2 memory
line written BEFORE the kill AND no new sector complete AT it (builder note 5); K-BETWEEN only with its determinism line
(builder note 2: the presses up to the kill and S1's events and truth equal the earlier CONTROL run's of the same seed).

GRADED, per arm, by the second path only (spec section 5's checks 1-7, `grade`). Development constants that step 6 sets
from its own measurements are marked PROVISIONAL below.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.probe_save_kill import (  # noqa: E402
    BLOCK_SECONDS, IDENTITY_KEYS, SECTORS_PER_SLOT, Child, brief, child_env, file_verdict, new_ids, parse_image,
)

TARGET = "ch1_pokedex"
FRAMES_A = 330000
GAME_CLOCK = "2026-10-14T10:00"
WALL_CLOCK = "10:00"
#: the HELD free read: this many more frames free, no input needed (the probe's `--after`)
AFTER = 10
#: the frames after a START press during which the watcher reads the flash every frame (a dialog's START to free was
#: 1,603 frames at the AI's slowest pacing, stage 1; 2x and more)
ACTIVE_FRAMES = 4000
#: outside a dialog, the flash is still read this often (a write with no START before it would be seen)
IDLE_FLASH_EVERY = 60
#: the big moments' proofs are sampled this often (the harness's `StoryRecorder` samples every 30)
PROOF_EVERY = 10
#: (spec section 5) the kill rules: `S<save>.<event>+<frames>` (the event's frame read from the arm's OWN record), or the
#: K-BETWEEN midpoint rule, computed from an earlier CONTROL run of the same seed
KILLS = {"K-AFTER": "S2.e4+40", "K-INSIDE": "S2.e3+130", "K-SILENT": "S2.e3+9", "K-FIRST": "S1.e3+128",
         "K-BETWEEN": "between"}
#: SET from step 6's measured wall times (spec F13: 2x the longest, never under 1200 / 300 s): child A to its kill point
#: took at most 198.8 s (K-INSIDE, 12 emulators running beside the bot tuner) and a whole CONTROL at most 316.8 s; child B
#: at most 16.4 s. Both floors apply.
CHILD_A_TIMEOUT = 1200
CHILD_B_TIMEOUT = 300
#: (builder note 3) check 6's "within the frames of one decision" after a big moment's proof turned true, SET from step 6
#: (b): on seeds 5401-5406 the 18 big-moment saves began (START) 12 to 55 frames after the harness's sampled proof turned
#: true (`measure`, s53/r1build/build/s5-dev); 2x the widest is 110 (ORCHESTRATOR RULING 1's margin)
MOMENT_FRAMES = 110
#: (D3) the big moments (= `brain/saving.py` BIG_MOMENTS; read from the AI's module ONLY to name them, never to grade)
BIG_MOMENTS = ("ch1_lab", "ch1_rival_route103", "ch1_pokedex", "ch2_wally", "ch3_woods", "ch4_roxanne")
CENTER_SUFFIX = "POKEMON_CENTER_1F"
KNOWLEDGE = REPO / "ai_player" / "knowledge" / "milestones.json"

# ------------------------------------------------------------------ step 7: the held-out run (spec section 5)
#: the held-out graded seeds (spec section 5 "Seeds and the ledger"), registered BEFORE any of them runs
HELD_OUT = (5451, 5454)
#: (spec section 5 "Floors") every graded arm must COUNT on at least this many of the 4 held-out seeds
FLOOR = 3
#: K-BETWEEN's GRADED kill rule. The spec's literal midpoint (halfway between S1.e7 and S2.e1) was measured VACUOUS on both
#: rehearsal seeds (step 6 (c), 5405 and 5406): at the midpoint child A had stood on no map it had not stood on before S1,
#: so check 3 could not fail. "new" kills halfway between the first frame child A stands on a map of its CONTROL's NEW and
#: S2's START: still between the saves with no write under way (the spec's "ordinary deployment kill"), and check 3 can
#: fail there. The midpoint still runs as the DIAGNOSTIC arm K-BETWEEN-MID (reported, never in the verdict).
BETWEEN_RULE = "new"
#: the graded arms (spec section 5's table). An OLD arm is graded by the difference it exists to show, and counts on a seed
#: only when its NEW twin counts there.
ARMS_NEW = ("CONTROL", "K-AFTER", "K-INSIDE", "K-SILENT", "K-FIRST", "K-BETWEEN", "LAUNCH")
OLD_OF = {"K-INSIDE-OLD": "K-INSIDE", "K-SILENT-OLD": "K-SILENT", "LAUNCH-OLD": "LAUNCH"}
GRADED_ARMS = ARMS_NEW + tuple(OLD_OF)
DIAGNOSTIC_ARMS = {"K-BETWEEN-MID": "K-BETWEEN under the spec's literal midpoint rule: reported, never in the verdict"}
#: mutant R1-M (spec section 5): "restore the newest save line, with no TIME match and no arrival check" (the pre-R2 rule
#: of `read_world`), applied to child B only, in a temp tree. The SAME edits as revert_r1's S20 and S22 (the selftest
#: checks it), so the live A/B's OLD half is the mutant the unit lane catches.
R1M_EDITS = (("skills/saving.py", "    record = book.match_time(time)\n", "    record = book.newest_save()\n"),
             ("skills/saving.py", "    if seen != remembered:\n", "    if False:\n"))
#: mutant S27 (spec section 6; LAUNCH-OLD): `--continue` keeps the `.ss1`. The same edit as revert_r1's S27.
S27_EDITS = (("host/launcher.py", "        if had:\n            dropped.unlink()\n",
              "        if False:\n            dropped.unlink()\n"),)
#: LAUNCH's stale state: the fixture planted as `current_state.ss1` (the probe's and live_step3's route101_south.ss1)
FIXTURE = REPO / "ai_player" / "gates" / "fixtures" / "route101_south.ss1"
FIXTURE_MD5 = "81bf318a1532c5364f60064530f9984b"
#: LAUNCH-OLD: with the fixture loaded the first look is ROUTE101 (map 0:16) at an emulator frame of this or more
FIXTURE_FRAME = 66883
FIXTURE_MAP = "(0,16)"
#: LAUNCH: a COLD BOOT's first look is at an emulator frame under this (finding G5)
COLD_BOOT_FRAMES = 300
#: the launcher's wall clock for LAUNCH and LAUNCH-OLD (2,620 frames headless; the bot's start-up included), and the
#: parent's own timeout over it (the gate and the launcher's start-up)
LAUNCH_WALL = 300
LAUNCH_TIMEOUT = LAUNCH_WALL + 180
#: the build root's folders a LAUNCH mirror links (read only); everything else in the mirror is its own
MIRROR_LINKS = ("modules", "plugins", "mgba", "roms")
#: the files the registered numbers hash (as `rate_step5.HASHED_FILES`): the driver and grader, the harness, the probe's
#: helpers it imports, the screen read, the proofs check 6 reads, and LAUNCH's fixture
HASHED_FILES = ("ai_player/gates/live_r1.py", "ai_player/gates/play_harness.py", "ai_player/gates/probe_save_kill.py",
                "ai_player/gates/probe_end_screen.py", "ai_player/knowledge/milestones.json",
                "ai_player/gates/fixtures/route101_south.ss1")
#: (selftest only) the planted grader fault this process runs with; None in every real run
FAULT: str | None = None
FAULTS = {
    "new_empty": "NEW computed empty",
    "tile_ignored": "the identity compare ignores the tile",
    "menu_census_ignored": "the press census ignores the main menu",
    "first_map_change": "check 3 reads child B's first map-change snapshot, not the restore snapshot",
    "old_without_twin": "an OLD arm graded as counted while its NEW twin is not",
    "floor_ignored": "the verdict rule returns PASS below a floor",
}


def plan_of(seed: int) -> tuple[str, str]:
    from ai_player.gates.rate_step5 import plan_of as plan

    return plan(seed)


def now() -> str:
    return time.strftime("%Y-%m-%d %I:%M:%S %p")


# ------------------------------------------------------------------ the harness's own reads (child side)
def _sym(name: str, size: int, offset: int = 0) -> int:
    from modules.memory import read_symbol

    return int.from_bytes(bytes(read_symbol(name, offset, size)), "little")


def blocks_moving() -> bool:
    """gMain.vblankCallback NULL: the save blocks may be moving this frame (`play_harness.story_truth`'s guard)."""
    return _sym("gMain", 4, 0x0C) == 0


def map_now(emulator) -> str | None:
    """SaveBlock1's map (group:number) by RAM, None while the save blocks may move."""
    if blocks_moving():
        return None
    sb1 = _sym("gSaveBlock1Ptr", 4)
    if not sb1:
        return None  # before the game set its save blocks up (power-on)
    location = bytes(emulator.read_bytes(sb1 + 0x04, 2))
    return f"{location[0]}:{location[1]}"


def map_const(key: str | None) -> str | None:
    """The framework's name of a map (`modules.map_data.get_map_enum`), e.g. OLDALE_TOWN_POKEMON_CENTER_1F."""
    if key is None:
        return None
    from modules.map_data import get_map_enum

    group, number = (int(v) for v in key.split(":"))
    try:
        return get_map_enum((group, number)).name
    except Exception:  # noqa: BLE001 - an unknown map: named by its numbers
        return None


def proofs() -> dict[str, dict]:
    """The big moments' proofs from `knowledge/milestones.json` (decomp-checked): flag numbers, var numbers with their
    least value, trainer flag numbers."""
    data = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    out = {}
    for milestone in data["milestones"]:
        if milestone["id"] in BIG_MOMENTS:
            done = milestone["done"]
            out[milestone["id"]] = {"flags": list(done["flags"].values()) + list(done["trainers"].values()),
                                    "vars": [[info["number"], info["at_least"]] for info in done["variables"].values()]}
    return out


def proof_now(emulator, wanted: dict[str, dict]) -> dict[str, bool] | None:
    """Which proofs hold now, by the harness's own reads of SaveBlock1's flags and vars (None while the blocks move)."""
    if blocks_moving():
        return None
    sb1 = _sym("gSaveBlock1Ptr", 4)
    if not sb1:
        return None
    flags = bytes(emulator.read_bytes(sb1 + 0x1270, 300))
    variables = bytes(emulator.read_bytes(sb1 + 0x139C, 0x200))
    out = {}
    for name, proof in wanted.items():
        ok = all((flags[n // 8] >> (n % 8)) & 1 for n in proof["flags"])
        for number, least in proof["vars"]:
            at = 2 * (number - 0x4000)
            ok = ok and int.from_bytes(variables[at:at + 2], "little") >= least
        out[name] = ok
    return out


def presses_digest(log: list[list], upto: int) -> str:
    """The sha256 of the harness's press log (frame, button, kind, frames) up to and including frame `upto`: the
    determinism line's trajectory (builder note 2)."""
    rows = [entry[:4] for entry in log if entry[0] is not None and entry[0] <= upto]
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()[:16] + f"/{len(rows)}"


def parse_kill(spec: str | None):
    if not spec or spec == "none":
        return None
    if spec.startswith("F"):
        return ("F", int(spec[1:]))
    head, _, offset = spec.partition("+")
    save, _, event = head.partition(".")
    if not save.startswith("S") or event not in ("e1", "e3", "e4", "e7"):
        raise ValueError(f"bad kill {spec!r}")
    return ("S", int(save[1:]), event, int(offset or 0))


class MemoryTail:
    """The memory file's lines as they reach it (test side: a read of the file, never the AI's objects)."""

    def __init__(self, path: Path) -> None:
        self.path, self.size, self.buffer, self.lines = path, 0, b"", []

    def poll(self, frame: int) -> list[dict]:
        try:
            size = self.path.stat().st_size
        except OSError:
            return []
        if size <= self.size:
            return []
        with open(self.path, "rb") as handle:
            handle.seek(self.size)
            self.buffer += handle.read(size - self.size)
        self.size = size
        new = []
        while b"\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\n", 1)
            if not raw.strip():
                continue
            try:
                line = json.loads(raw)
            except ValueError:
                line = {"kind": "(unreadable)", "length": len(raw)}
            record = {k: v for k, v in line.items() if k not in ("memory", "payload")}
            record["seen_at"] = frame
            record["bytes"] = len(raw)
            new.append(record)
        self.lines += new
        return new


class SaveWatch:
    """Child A's per-frame watcher (module docstring)."""

    def __init__(self, context, controls, memory: Path, kill: str | None, record: Path) -> None:
        self.context, self.emulator, self.controls = context, context.emulator, controls
        self.kill_spec = kill
        self.kill = parse_kill(kill)
        self.record = open(record, "w", encoding="utf-8", buffering=1)
        self.flash = bytes(self.emulator.read_save_data())
        self.parse = parse_image(self.flash)
        self.baseline = self.flash
        self.baseline_counters = self._counters()
        self.idle_counter = _sym("gSaveCounter", 4)
        self.dirt = self._dirt()
        self.saves: list[dict] = []
        self.cur: dict | None = None
        self.free_since: int | None = None
        self.ring: collections.deque = collections.deque(maxlen=AFTER + 6)
        self.maps: list[list] = []
        self.starts: list[dict] = []
        self.seen_presses = 0
        self.active_until = -1
        self.memory = MemoryTail(memory)
        self.wanted = proofs()
        self.proof_first: dict[str, int] = {}
        self.proof_pending: dict[str, int] = {}
        self.flash_reads = 0
        self.last_read = -1
        self.saves_pending_line: dict | None = None
        self.frames = 0
        self.at_start = {"flash": brief(self.parse)["status"], "size": len(self.flash), "frame": self.emulator.get_frame_count()}

    def _trace(self, f: int) -> None:
        span = os.environ.get("LIVE_R1_TRACE", "")
        if not span:
            return
        first, _, last = span.partition("-")
        if not int(first) <= f <= int(last):
            return
        flash = bytes(self.emulator.read_save_data())
        before = getattr(self, "_trace_prev", None)
        self._trace_prev = flash
        if before is None:
            return
        changed = []
        for p in range(len(flash) // 0x1000):
            a, b = before[p * 0x1000:(p + 1) * 0x1000], flash[p * 0x1000:(p + 1) * 0x1000]
            if a != b:
                offsets = [i for i in range(0x1000) if a[i] != b[i]]
                changed.append([p, offsets[0], offsets[-1], len(offsets), b[0xFF4:0x1000].hex()])
        self.record.write(json.dumps({"trace": f, "dirt": self._dirt(), "changed": changed}) + "\n")

    def _counters(self) -> set:
        """The counters of every valid sector of the flash as last parsed."""
        return {s[4] for s in self._valid()}

    def _valid(self) -> list[list]:
        """Every valid sector of the flash as last parsed: [physical, id, signature, valid, counter]."""
        return [s for slot in self.parse["slots"] for s in slot["sectors"] if s[3]]

    def _changed_physical(self) -> set[int]:
        size = 0x1000
        return {p for p in range(2 * SECTORS_PER_SLOT)
                if self.flash[p * size:(p + 1) * size] != self.baseline[p * size:(p + 1) * size]}

    def _rewritten(self) -> list[int]:
        """The sector ids this write has COMPLETED: valid now, and their physical sector rewritten since the baseline."""
        changed = self._changed_physical()
        return sorted({s[1] for s in self._valid() if s[0] in changed})

    def _dirt(self) -> list[int]:
        data = self.emulator._core._native.memory.savedata  # noqa: SLF001 - test side: mGBA's own save bookkeeping
        return [int(data.dirty), int(data.dirtAge)]

    def after_frame(self) -> None:
        from ai_player.gates.play_harness import party_now
        from ai_player.gates.probe_end_screen import game_screen
        from ai_player.gates.probe_save_kill import ram_truth

        emulator = self.emulator
        f = emulator.get_frame_count()
        self.frames += 1
        try:
            screen = game_screen()
            free, overworld = bool(screen["free"]), bool(screen["overworld"])
        except Exception:  # noqa: BLE001
            free, overworld = False, False
        self.ring.append((f, free))
        # the presses since the last frame: a START begins a dialog (its look was the frame the press logs)
        log = self.controls.log
        while self.seen_presses < len(log):
            entry = log[self.seen_presses]
            self.seen_presses += 1
            if entry[1] == "Start":
                pressed = entry[0]
                before = [ok for frame, ok in self.ring if frame is not None and pressed is not None
                          and pressed - AFTER <= frame <= pressed]
                key = map_now(emulator)
                try:
                    party = party_now()
                except Exception:  # noqa: BLE001
                    party = None
                self.starts.append({"f": pressed, "held_free": len(before) == AFTER + 1 and all(before),
                                    "free_frames": len(before), "overworld": overworld, "map": key,
                                    "const": map_const(key), "party": party, "presses_before": self.seen_presses - 1})
                self.active_until = (pressed or f) + ACTIVE_FRAMES
        # the map the player stands on (RAM)
        key = map_now(emulator)
        if key is not None and (not self.maps or self.maps[-1][1] != key):
            self.maps.append([f, key])
        # the big moments' proofs (confirmed by a second sample)
        if self.frames % PROOF_EVERY == 0:
            held = proof_now(emulator, {k: v for k, v in self.wanted.items() if k not in self.proof_first})
            for name, ok in (held or {}).items():
                if ok and name in self.proof_pending:
                    self.proof_first[name] = self.proof_pending.pop(name)
                elif ok:
                    self.proof_pending[name] = f
                else:
                    self.proof_pending.pop(name, None)
        # the memory file's lines, the frame each was first seen
        for line in self.memory.poll(f):
            if line.get("kind") == "save" and self.cur is not None and "line" not in self.cur:
                self.cur["line"] = line
            elif line.get("kind") == "save":
                self.saves_pending_line = line
        # (development) LIVE_R1_TRACE="first-last": every frame in that range, which bytes of which sector changed
        self._trace(f)
        # the flash: every frame inside a dialog or a write, on mGBA's own write mark, else every IDLE_FLASH_EVERY
        dirt = self._dirt()
        if self.cur is not None or f <= self.active_until or dirt != self.dirt or f % IDLE_FLASH_EVERY == 0:
            self._flash(f, ram_truth)
        self.dirt = dirt
        if self.cur is not None and "e4" in self.cur and "e7" not in self.cur:
            if free:
                self.free_since = f if self.free_since is None else self.free_since
                if f - self.free_since >= AFTER:
                    self.cur["e7"] = self.free_since
                    # the baseline for the next write: the flash NOW (a change between e4 and here is recorded, never
                    # taken for a new save)
                    flash = bytes(emulator.read_save_data())
                    self.cur["flash_changed_after_e4"] = flash != self.baseline
                    self.baseline = self.flash = flash
                    self.parse = parse_image(flash)
                    self.baseline_counters = self._counters()
                    self.cur = None
            else:
                self.free_since = None
        elif self.cur is None:
            self.idle_counter = _sym("gSaveCounter", 4)
        self._check_kill(f)

    def _flash(self, f: int, ram_truth) -> None:
        self.flash_reads += 1
        previous, self.last_read = self.last_read, f
        flash = bytes(self.emulator.read_save_data())
        if flash != self.flash:
            self.flash = flash
            self.parse = parse_image(flash)
        if self.cur is None and flash != self.baseline:
            index = len(self.saves) + 1
            start = next((s for s in reversed(self.starts) if s["f"] is not None and s["f"] <= f), None)
            # e3 is EXACT only when the frame before was read too (the flash then still equalled the baseline)
            exact = previous == f - 1
            self.cur = {"save": index, "counter": self.idle_counter + 1, "e3": f, "e3_exact": exact,
                        "e1": start["f"] if start else None, "start": start, "truth": ram_truth(self.emulator),
                        "sectors": {}, "new_now": 0}
            pending = self.saves_pending_line
            if pending is not None and (start is None or pending.get("frame", -1) >= (start["f"] or 0)):
                self.cur["line"] = pending
            self.saves_pending_line = None
            self.saves.append(self.cur)
        cur = self.cur
        if cur is not None and "e4" not in cur:
            # THE NEW SECTORS: valid sectors (signature and checksum, the game's own test, `parse_slot`) whose 4 KiB differ
            # from the flash before this write. Counter-free, because a counter cannot be predicted here: the first
            # development run guessed `gSaveCounter + 1` read before the write (the probe's rule on a loaded state) and on
            # a NEW GAME it named no sector at all (0 new sectors through a whole write); the second took the newest
            # counter no earlier sector carried and on seed 5403 latched 0xFFFF0002, a sector whose counter word was
            # still being programmed (flash bits only go 1 -> 0, so a half-written counter reads HIGH), and missed e4.
            ids = self._rewritten()
            counters = sorted({s[4] for s in self._valid() if s[1] in ids and s[0] in self._changed_physical()})
            if counters:
                cur["counter"] = counters[0]
                cur["counters_seen"] = sorted(set(cur.get("counters_seen", [])) | set(counters))
            for sid in ids:
                cur["sectors"].setdefault(str(sid), f)
            cur["new_now"] = len(ids)
            # e4: all 14 rewritten AND one counter among them. A sector's counter word is programmed over two frames, and
            # half-programmed it still reads valid (MEASURED, seed 5405 save 4: the last sector's counter read 0xFFFF0004
            # at f142078 and 4 at f142079); e4 taken at the half-written frame left a stale baseline, and the counter's
            # last two bytes then read as a NEW save 197 frames later
            if len(ids) == SECTORS_PER_SLOT and len(counters) == 1:
                cur["e4"] = f
                loaded = self.parse.get("loaded") or {}
                cur["slot_at_e4_equals_truth"] = all(loaded.get(k) == cur["truth"].get(k) for k in IDENTITY_KEYS)
                cur["slot_at_e4"] = {k: loaded.get(k) for k in IDENTITY_KEYS}
                self.baseline = self.flash
                self.baseline_counters = self._counters()
            self.record.write(json.dumps({"f": f, "save": cur["save"], "new": len(ids),
                                          "status": self.parse["status"]}) + "\n")

    def _check_kill(self, f: int) -> None:
        kill = self.kill
        if kill is None:
            return
        if kill[0] == "F":
            reached = f >= kill[1]
        else:
            _, index, event, offset = kill
            save = self.saves[index - 1] if len(self.saves) >= index else None
            reached = save is not None and event in save and save[event] is not None and f - save[event] >= offset
        if not reached:
            return
        payload = self.result()
        cur = self.saves[kill[1] - 1] if kill[0] == "S" else None
        payload["kill"] = {"spec": self.kill_spec, "frame": f,
                           "new_sectors_at_kill": None if cur is None or "e4" in cur else cur["new_now"],
                           "write_complete_at_kill": None if cur is None else "e4" in cur,
                           "presses_digest": presses_digest(self.controls.log, f),
                           "status_at_kill": self.parse["status"]}
        self.record.flush()
        print("READY " + json.dumps(payload, ensure_ascii=False), flush=True)
        for _ in range(int(BLOCK_SECONDS / 0.25)):
            time.sleep(0.25)
        print("NOT KILLED: the parent never killed this child; it ends itself (exit 5)", flush=True)
        os._exit(5)

    def result(self) -> dict:
        saves = []
        for save in self.saves:
            item = {k: v for k, v in save.items() if k != "start"}
            item["start"] = save.get("start")
            if save.get("sectors"):
                item["first_sector"] = min(save["sectors"].values())
            saves.append(item)
        return {"saves": saves, "truths": {f"S{s['save']}": s["truth"] for s in self.saves},
                "maps": self.maps, "starts": self.starts, "proof_first": self.proof_first,
                "memory_lines": self.memory.lines, "flash_reads": self.flash_reads, "frames": self.frames,
                "at_start": self.at_start}


class ArrivalWatch:
    """Child B's per-frame watcher (module docstring): the boot read, the main menu at every press, the pages' words,
    the held free arrival."""

    def __init__(self, context, controls) -> None:
        self.context, self.emulator, self.controls = context, context.emulator, controls
        self.menu: tuple | None = None
        self.menu_input_from: int | None = None
        self.boot: dict | None = None
        self.pages: list[dict] = []
        self.page_keys: set = set()
        self.presses: list[list] = []
        self.seen_presses = 0
        self.overworld_from: int | None = None
        self.free_since: int | None = None
        self.candidate: dict | None = None
        self.arrival: dict | None = None
        self.first_look: dict | None = None
        self.frames = 0
        self.new_game_tasks: list[list] = []

    def after_frame(self) -> None:
        from ai_player.gates.probe_end_screen import game_screen
        from ai_player.gates.probe_save_kill import (
            ERROR_TASKS, main_menu_task, printer_page, ram_truth, second_path_truth,
        )
        from modules.memory import read_symbol
        from modules.tasks import TaskList

        emulator = self.emulator
        f = emulator.get_frame_count()
        self.frames += 1
        if self.first_look is None:
            screen = game_screen()
            self.first_look = {"f": f, "overworld": screen["overworld"], "callback2": screen["callback2"]}
        # presses since the last frame, with the main menu as the harness read it on the look before
        log = self.controls.log
        while self.seen_presses < len(log):
            entry = log[self.seen_presses]
            self.seen_presses += 1
            self.presses.append([entry[0], entry[1], self.menu])
        if self.arrival is None:
            name, data0, data1 = main_menu_task()
            self.menu = (name, data0, data1, f)
            if name == "Task_HandleMainMenuInput" and self.menu_input_from is None:
                self.menu_input_from = f
                self.boot = ram_truth(emulator)  # what the power-on read copied into RAM (`LoadGameSave`)
                self.boot["menu_type"], self.boot["cursor"] = data0, data1
            if name in ERROR_TASKS:
                page = printer_page(7)
                key = (name, page.get("symbol"))
                if not page["active"] and key not in self.page_keys:
                    self.page_keys.add(key)
                    self.pages.append({"task": name, "symbol": page.get("symbol"), "text": page.get("text"), "f": f})
            tasks = TaskList(read_symbol("gTasks"))
            births = [t for t in ("Task_NewGameBirchSpeech_Init", "Task_NewGameBirchSpeechSub_InitPokeBall")
                      if tasks[t] is not None]
            if births:
                self.new_game_tasks.append([f, births])
            screen = game_screen()
            if screen["overworld"] and self.menu_input_from is not None:
                self.overworld_from = self.overworld_from or f
                if screen["free"]:
                    if self.free_since is None:
                        self.free_since = f
                        self.candidate = {"f": f, **ram_truth(emulator), "second_path": second_path_truth(self.context)}
                    elif f - self.free_since >= AFTER:
                        self.arrival = self.candidate
                else:
                    self.free_since, self.candidate = None, None

    def result(self) -> dict:
        return {"boot": self.boot, "menu_input_from": self.menu_input_from, "pages": self.pages, "presses": self.presses,
                "overworld_from": self.overworld_from, "arrival": self.arrival, "first_look": self.first_look,
                "frames": self.frames, "new_game_tasks": self.new_game_tasks}


# ------------------------------------------------------------------ the children
def child_a(args) -> int:
    from ai_player.gates import play_harness

    profile = Path(args.profile_dir)
    personality, starter = plan_of(args.seed)
    watchers: list = []

    def watch(controls):
        from modules.context import context

        watcher = SaveWatch(context, controls, Path(args.memory), args.kill, Path(args.record))
        watchers.append(watcher)
        return [watcher]

    result = play_harness.run(None, args.seed, args.frames, personality, starter, TARGET, set(), GAME_CLOCK, WALL_CLOCK,
                              None, Path(args.run_dir), None, 30, profile_dir=profile, memory=Path(args.memory),
                              watch=watch)
    Path(args.play_json).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    out = watchers[0].result() if watchers else {}
    out["play"] = {k: result.get(k) for k in ("reason", "frames", "seconds", "presses", "personality", "starter")}
    out["play"]["saves"] = (result.get("report") or {}).get("saves")
    out["play"]["end_save"] = (result.get("report") or {}).get("end_save")
    out["play"]["lines_save"] = [line for line in result.get("lines") or [] if "[AI-SAVE]" in line]
    print("RESULT " + json.dumps(out, ensure_ascii=False), flush=True)
    return 0


def child_b(args) -> int:
    from ai_player.gates import play_harness
    from ai_player.host.launcher import memory_check, seed_profile
    from ai_player.paths import AppPaths
    from ai_player.skills.saving import ARRIVAL_BUDGET, CONTINUE_BUDGET

    import ai_player.skills.saving as saving_skill

    profile = Path(args.profile_dir)
    game = AppPaths.for_profile(profile.name, profile.parent.parent, home="")
    check = memory_check(game)
    out = {"memory_check": {"ok": check.ok, "why": check.why, "end_class": check.end_class, "undone": check.undone,
                            "newest": (check.newest or {}).get("id")},
           # WHICH continue skill this child ran (an OLD arm's mutant copy, or the tree under test): its file and sha256
           "skills_saving": {"file": str(Path(saving_skill.__file__).resolve()),
                             "sha256": hashlib.sha256(Path(saving_skill.__file__).read_bytes()).hexdigest()[:16]}}
    if not check.ok:
        out["refused"] = check.why
        print("RESULT " + json.dumps(out, ensure_ascii=False), flush=True)
        return 0
    out["seed_profile"] = seed_profile(profile, None, False, continue_game=True, game=game)
    out["ss1_at_boot"] = (profile / "current_state.ss1").exists()
    personality, starter = plan_of(args.seed)
    watchers: list = []

    def watch(controls):
        from modules.context import context

        watcher = ArrivalWatch(context, controls)
        watchers.append(watcher)
        return [watcher]

    frames = args.frames or CONTINUE_BUDGET + ARRIVAL_BUDGET + 600
    result = play_harness.run(None, args.seed, frames, personality, starter, TARGET, set(), GAME_CLOCK, WALL_CLOCK,
                              None, Path(args.run_dir), None, 30, profile_dir=profile, memory=game.memory_jsonl,
                              continue_game=True, watch=watch)
    Path(args.play_json).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    out.update(watchers[0].result() if watchers else {})
    out["frames_budget"] = frames
    out["play"] = {k: result.get(k) for k in ("reason", "frames", "seconds", "presses")}
    out["play"]["lines_save"] = [line for line in result.get("lines") or [] if "[AI-SAVE]" in line or "continue:" in line]
    print("RESULT " + json.dumps(out, ensure_ascii=False), flush=True)
    return 0


# ------------------------------------------------------------------ the parent
def make_profile(out: Path, name: str, donor: Path) -> Path:
    from ai_player.host.launcher import PROFILE_MARKER

    profile = out / "profiles" / name
    if profile.exists():
        raise SystemExit(f"{profile} exists: a fresh --out (or arm) is needed (nothing is reused)")
    profile.mkdir(parents=True)
    shutil.copy2(donor, profile / "metadata.yml")
    (profile / PROFILE_MARKER).write_text("live_r1 throwaway profile\n", encoding="utf-8")
    return profile


def fresh_cart(profile: Path) -> dict:
    """(finding F14) The cart child A boots: an EMPTY `current_save.sav`, no `.ss1` (else the arm is refused)."""
    save = profile / "current_save.sav"
    save.write_bytes(b"")
    states = list(profile.glob("*.ss1")) + list((profile / "states").glob("*.ss1"))
    ok = save.stat().st_size == 0 and not states
    return {"ok": ok, "sav_bytes": save.stat().st_size, "ss1": [str(p) for p in states]}


def ctx_of(args) -> dict:
    from ai_player.gates.hands_harness import PROFILE
    from ai_player.host.launcher import ENV_BUILD_ROOT, resolve_build_root

    build_root = Path(args.build_root or os.environ.get(ENV_BUILD_ROOT) or resolve_build_root()).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return {"out": out, "build_root": build_root, "donor": build_root / "profiles" / PROFILE / "metadata.yml",
            "env": child_env(build_root), "script": Path(__file__).resolve()}


def run_child_a(ctx: dict, tag: str, seed: int, kill: str, frames: int) -> tuple[dict, Path]:
    out = ctx["out"]
    from ai_player.paths import AppPaths

    name = f"ai-r1live-{tag.lower()}-{seed}"
    profile = make_profile(out, name, ctx["donor"])
    cart = fresh_cart(profile)
    folder = out / "runs" / f"{tag}-{seed}"
    folder.mkdir(parents=True)
    row: dict = {"arm": tag, "seed": seed, "kill": kill, "profile": str(profile), "folder": str(folder), "fresh_cart": cart,
                 "started": now()}
    if not cart["ok"]:
        row["refused"] = f"the cart is not fresh: {cart}"
        return row, profile
    game = AppPaths.for_profile(name, out, home="")
    cmd = [sys.executable, "-B", str(ctx["script"]), "child-a", "--profile-dir", str(profile), "--memory",
           str(game.memory_jsonl), "--seed", str(seed), "--frames", str(frames), "--kill", kill, "--record",
           str(folder / "a_flash.jsonl"), "--run-dir", str(folder / "a_run"), "--play-json", str(folder / "a_play.json")]
    began = time.monotonic()
    a = Child(cmd, ctx["env"], REPO, folder / "child_a.out", tag, "child A")
    word, result = a.wait_for(("READY", "RESULT", "ABORT"), CHILD_A_TIMEOUT)
    row["child_a"] = {"pid": a.pid, "word": word, "seconds": round(time.monotonic() - began, 1)}
    if word == "READY":
        row["child_a"]["kill"] = a.kill()
        row["child_a"]["exit"] = row["child_a"]["kill"]["exit_code"]
    else:
        row["child_a"]["exit"] = a.finish(120)
    row["child_a"]["alive_after"] = a.proc.poll() is None
    row["a"] = result
    return row, profile


def freeze(ctx: dict, row: dict, profile: Path) -> Path:
    """(G6, F12) The cart and the memory as the kill left them, before any child B."""
    from ai_player.paths import AppPaths

    frozen = ctx["out"] / "frozen" / f"{row.get('name', row['arm'])}-{row['seed']}"
    frozen.mkdir(parents=True)
    game = AppPaths.for_profile(profile.name, ctx["out"], home="")
    copied = {}
    for source in (profile / "current_save.sav", game.memory_jsonl, game.launches_jsonl):
        if source.exists():
            shutil.copy2(source, frozen / source.name)
            copied[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    row["frozen"] = {"dir": str(frozen), "files": copied,
                     "ss1_after_a": sorted(p.name for p in profile.glob("*.ss1"))}
    return frozen


def run_child_b(ctx: dict, row: dict, frozen: Path, suffix: str = "b", root: Path = REPO) -> None:
    """Child B on its OWN copy of the frozen set. `root`: the tree whose `ai_player` child B runs (an OLD arm's mutant
    copy; REPO otherwise)."""
    from ai_player.paths import AppPaths

    name = f"ai-r1live-{row.get('name', row['arm']).lower()}-{suffix}-{row['seed']}"
    profile = make_profile(ctx["out"], name, ctx["donor"])
    game = AppPaths.for_profile(name, ctx["out"], home="")
    game.game_dir.mkdir(parents=True)
    for item in frozen.iterdir():
        target = profile / item.name if item.name.endswith(".sav") else game.game_dir / item.name
        shutil.copy2(item, target)
    folder = ctx["out"] / "runs" / f"{row.get('name', row['arm'])}-{row['seed']}"
    folder.mkdir(parents=True, exist_ok=True)
    script = root / "ai_player" / "gates" / "live_r1.py"
    cmd = [sys.executable, "-B", str(script), "child-b", "--profile-dir", str(profile), "--seed", str(row["seed"]),
           "--run-dir", str(folder / f"{suffix}_run"), "--play-json", str(folder / f"{suffix}_play.json")]
    began = time.monotonic()
    b = Child(cmd, ctx["env"], root, folder / f"child_{suffix}.out", row["arm"], "child B")
    word, result = b.wait_for(("RESULT", "ABORT"), CHILD_B_TIMEOUT)
    row["child_b"] = {"pid": b.pid, "word": word, "exit": b.finish(120), "seconds": round(time.monotonic() - began, 1)}
    row["child_b"]["alive_after"] = b.proc.poll() is None
    row["b"] = result
    memory = [json.loads(line) for line in game.memory_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()] \
        if game.memory_jsonl.exists() else []
    row["b_memory"] = [{k: v for k, v in line.items() if k != "memory"} for line in memory]
    row["b_run"] = str(folder / f"{suffix}_run")


def expected_file(arm: str, a: dict) -> tuple[str | None, str]:
    """(ORCHESTRATOR RULING 1) The FILE the kill must leave, from the arm's OWN record at the kill frame."""
    kill = a.get("kill") or {}
    new = kill.get("new_sectors_at_kill")
    if arm == "K-FIRST":
        return ("CORRUPT" if new else "EMPTY"), f"{new} new sector(s) of save 1 complete at the kill"
    if arm in ("K-INSIDE", "K-SILENT"):
        return ("S1+ERROR" if new else "S1"), f"{new} new sector(s) of save 2 complete at the kill"
    if arm == "K-BETWEEN":
        return "S1", "no write under way at the kill"
    if arm == "K-AFTER":
        return "S2", "save 2's write complete at the kill"
    return None, "no kill"


def restore_snapshot(run_dir: Path) -> tuple[dict | None, str | None]:
    """(check 3, finding F2) The world memory the continued brain ACTS on: the `world.jsonl` snapshot written at the
    restore ("restored from save <id>"), found by its place among the run's world snapshots in the action log."""
    actions = run_dir / "actions.jsonl"
    world = run_dir / "world.jsonl"
    if not actions.exists() or not world.exists():
        return None, None
    index, reason = -1, None
    wanted = "a map change" if FAULT == "first_map_change" else "restored from save"
    for line in actions.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("decision") == "world" and record.get("action") == "snapshot":
            index += 1
            if str(record.get("reason", "")).startswith(wanted):
                reason = record["reason"]
                break
    else:
        return None, None
    lines = world.read_text(encoding="utf-8").splitlines()
    return (json.loads(lines[index]) if index < len(lines) else None), reason


def b_actions(run_dir: Path) -> list[dict]:
    path = run_dir / "actions.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def new_maps(a: dict) -> list[str]:
    """`NEW`: the maps child A first stood on (its RAM record) after S1.e3 and before S2.e3. In K-BETWEEN, whose child A
    is killed BEFORE S2 begins, the end of the window is the kill frame: what it stood on after its save and before the
    kill is exactly what a memory restored as of S1 must not hold (spec: "memory has nothing newer")."""
    saves = a.get("saves") or []
    kill = (a.get("kill") or {}).get("frame")
    if FAULT == "new_empty" or not saves or (len(saves) < 2 and kill is None):
        return []
    e3_1 = saves[0]["e3"]
    e3_2 = saves[1]["e3"] if len(saves) > 1 else kill
    first: dict[str, int] = {}
    for frame, key in a.get("maps") or []:
        first.setdefault(key, frame)
    return sorted(key for key, frame in first.items() if e3_1 <= frame < e3_2)


def grade(row: dict) -> dict:
    """Spec section 5's checks 1-7 for one arm's row, by the second path only. Each check: True / False / None (not
    applicable), with its evidence. An OLD arm's row (K-INSIDE-OLD, K-SILENT-OLD) is graded as its NEW twin, on the twin's
    child A and frozen set, and also says whether it shows the difference it exists for (`old_shows`: the memory the mutant
    child B restored holds a map of NEW, i.e. it is NEWER than the save the game loaded)."""
    old = row["arm"] if row["arm"] in OLD_OF else None
    arm, a, b = OLD_OF.get(row["arm"], row["arm"]), row.get("a") or {}, row.get("b") or {}
    checks: dict = {}
    notes: dict = {}
    truths = a.get("truths") or {}
    saves = a.get("saves") or []
    kill = a.get("kill") or {}
    expected, why = expected_file(arm, a)
    verdict = row.get("file", {}).get("verdict")
    checks["1_file"] = verdict == expected if expected else None
    notes["1_file"] = {"verdict": verdict, "expected": expected, "because": why}
    target = {"K-INSIDE": "S1", "K-SILENT": "S1", "K-BETWEEN": "S1", "K-AFTER": "S2"}.get(arm)
    arrival = (b.get("arrival") or {})
    if target and target in truths:
        truth = truths[target]
        keys = ("pids", "map") if FAULT == "tile_ignored" else ("pids", "map", "pos")
        same = {k: arrival.get(k) == truth.get(k) for k in keys}
        boot = (b.get("boot") or {}).get("play_time")
        same["play_time_at_boot"] = boot == truth.get("play_time")
        checks["2_identity"] = all(same.values())
        notes["2_identity"] = {"target": target, "same": same, "arrival": {k: arrival.get(k) for k in ("pids", "map", "pos")},
                               "truth": {k: truth.get(k) for k in IDENTITY_KEYS}, "boot_play_time": boot}
    else:
        checks["2_identity"] = None
    new = new_maps(a)
    notes["NEW"] = new
    snapshot, reason = restore_snapshot(Path(row["b_run"])) if row.get("b_run") else (None, None)
    session = next((line for line in reversed(row.get("b_memory") or []) if line.get("kind") == "session"), None)
    restored = sorted((snapshot or {}).get("maps", {}).keys()) if snapshot else None
    if arm in ("K-INSIDE", "K-SILENT", "K-BETWEEN", "K-AFTER"):
        agree = session is not None and restored is not None and sorted(session.get("restored_maps") or []) == restored
        if arm == "K-AFTER":
            ok = bool(new) and restored is not None and all(m in restored for m in new)
        else:
            ok = bool(new) and restored is not None and not any(m in restored for m in new)
        checks["3_memory"] = ok and agree
        notes["3_memory"] = {"restore_reason": reason, "restored_maps": restored, "session_restored_maps":
                             (session or {}).get("restored_maps"), "agree": agree, "continued_from":
                             (session or {}).get("continued_from"),
                             "s_line_ids": {f"S{s['save']}": (s.get("line") or {}).get("id") for s in saves}}
        want_id = (saves[0].get("line") or {}).get("id") if target == "S1" and saves else \
            (saves[1].get("line") or {}).get("id") if target == "S2" and len(saves) > 1 else None
        checks["3_restored_save"] = session is not None and session.get("continued_from") == want_id
    else:
        checks["3_memory"] = None
    # 4: the action log: CONTINUE pressed with its gate; no NEW GAME; the page read; K-FIRST: no press on the main menu
    presses = b.get("presses") or []
    on_menu = [p for p in presses if p[2] and p[2][0] == "Task_HandleMainMenuInput"]
    new_game = [p for p in on_menu if p[1] == "A" and (p[2][2] != 0 or (p[2][1] or 0) < 1)] + \
        [["task", t] for t in b.get("new_game_tasks") or []]
    # (K-FIRST, finding N1) the press census from the main menu on: every press the main menu's task saw, and every press
    # at or after the frame the main menu first took input
    menu_from = b.get("menu_input_from")
    census = [p for p in presses if (p[2] and p[2][0] == "Task_HandleMainMenuInput")
              or (menu_from is not None and p[0] is not None and p[0] >= menu_from)]
    if FAULT == "menu_census_ignored":
        census = []
    actions = b_actions(Path(row["b_run"])) if row.get("b_run") else []
    # the page's words must be in a `read` note (`hands.note("read", "text", words)`), not merely told
    reads = [r for r in actions if r.get("decision") == "read"]
    words = " ".join(str(r.get("reason", "")) for r in reads).lower()
    told = " ".join(str(r.get("reason", "")) for r in actions).lower()
    four = {"no_new_game": not new_game}
    if arm == "K-FIRST":
        four["menu_took_input"] = menu_from is not None  # else "zero presses on it" would hold by construction
        four["no_press_on_menu"] = not census
        four["page_read"] = "erased" in words
        four["stopped"] = "save is gone" in str((b.get("play") or {}).get("reason", "")) or "save is gone" in told
    else:
        four["continue_pressed"] = any(p[1] == "A" and p[2][2] == 0 and (p[2][1] or 0) >= 1 for p in on_menu)
        if arm == "K-INSIDE":
            four["page_read"] = "corrupted" in words
        if arm in ("K-SILENT", "K-BETWEEN", "K-AFTER"):
            four["no_page"] = not b.get("pages")
    checks["4_actions"] = all(four.values())
    notes["4_actions"] = {**four, "menu_presses": on_menu[:6], "census_presses": census[:6], "pages": b.get("pages"),
                          "read_records": len(reads),
                          "continue_time_read": [r.get("reason") for r in reads if str(r.get("reason", "")).startswith(
                              "CONTINUE TIME")]}
    # 5: each of child A's saves began on a held free screen, no battle; consecutive stamps >= 3 game minutes apart
    starts = [s.get("start") or {} for s in saves]
    stamps = [(s.get("line") or {}).get("play_time") for s in saves]
    gaps = [(b2[0] * 60 + b2[1]) - (a2[0] * 60 + a2[1]) for a2, b2 in zip(stamps, stamps[1:]) if a2 and b2]
    checks["5_free_and_gap"] = bool(saves) and all(s.get("held_free") and s.get("overworld") for s in starts) and \
        all(g >= 3 for g in gaps)
    notes["5_free_and_gap"] = {"held_free": [s.get("held_free") for s in starts], "stamps": stamps, "gaps": gaps}
    # 6: each save at a ruling-51 moment (by the harness's reads)
    moments = [moment_of(s, a.get("proof_first") or {}) for s in saves]
    checks["6_moments"] = bool(saves) and all(m["moment"] is not None for m in moments)
    notes["6_moments"] = moments
    # 7: (K-INSIDE, K-SILENT) S2's save line in the memory file with a frame below the kill frame
    if arm in ("K-INSIDE", "K-SILENT"):
        line = (saves[1].get("line") if len(saves) > 1 else None) or {}
        frozen_ids = row.get("frozen_save_lines") or []
        checks["7_s2_line_first"] = bool(line) and line.get("frame", 10 ** 9) < (kill.get("frame") or -1) and \
            line.get("id") in frozen_ids
        notes["7_s2_line_first"] = {"line_frame": line.get("frame"), "line_seen_at": line.get("seen_at"),
                                    "kill_frame": kill.get("frame"), "frozen_save_line_ids": frozen_ids,
                                    "e3": saves[1]["e3"] if len(saves) > 1 else None}
    else:
        checks["7_s2_line_first"] = None
    reach = checks["1_file"] is True and (checks["7_s2_line_first"] is not False)
    if arm == "K-SILENT":
        reach = reach and kill.get("new_sectors_at_kill") == 0
    if arm in ("K-INSIDE", "K-SILENT", "K-BETWEEN", "K-AFTER"):
        reach = reach and bool(new)
    if arm == "K-BETWEEN":
        reach = reach and bool((row.get("determinism") or {}).get("same"))
    counted = bool(reach)
    graded = {k: v for k, v in checks.items() if v is not None and k not in ("1_file", "7_s2_line_first")}
    out = {"checks": checks, "notes": notes, "counted": counted,
           "pass": counted and all(graded.values()) if counted else None}
    if old is not None:
        # the difference an OLD arm exists for, by POSITIVE evidence (never by a crash or a missing record): child B
        # restored a memory that holds a map of NEW, and its session line says it continued save 2's line
        s2_id = (saves[1].get("line") or {}).get("id") if len(saves) > 1 else None
        holds = sorted(m for m in new if restored is not None and m in restored)
        out["old_shows"] = bool(holds) and session is not None and session.get("continued_from") == s2_id \
            and checks.get("3_memory") is False
        out["pass"] = None
        notes["old"] = {"mutant": "R1-M", "twin": arm, "NEW_in_restored": holds, "continued_from":
                        (session or {}).get("continued_from"), "S2_line_id": s2_id}
    return out


def grade_control(row: dict) -> dict:
    """The CONTROL arm (spec section 5's table, PF-17): no kill. It COUNTS when child A ran to its own end (not a timeout or
    a crash). It passes when the run ended `done` at the target with its end save made, every save began on a held free
    screen at least 3 game minutes after the last (check 5) at a ruling-51 moment (check 6), and the cart's FILE verdict
    is the newest save (by the probe's parser)."""
    a = row.get("a") or {}
    play = a.get("play") or {}
    saves = a.get("saves") or []
    sub = grade({**row, "arm": "CONTROL", "b": {}, "b_run": None})
    checks = {"done_at_target": play.get("reason") == f"play: done: {TARGET} reached",
              "end_save_made": (play.get("end_save") or {}).get("saved") is True,
              "5_free_and_gap": sub["checks"]["5_free_and_gap"], "6_moments": sub["checks"]["6_moments"]}
    file = row.get("file") or control_file(row)
    checks["1_file_newest"] = bool(saves) and (file or {}).get("verdict") == f"S{len(saves)}"
    counted = (row.get("child_a") or {}).get("word") == "RESULT"
    notes = {"reason": play.get("reason"), "end_save": play.get("end_save"), "file": file, "saves": len(saves),
             "5_free_and_gap": sub["notes"]["5_free_and_gap"], "6_moments": sub["notes"]["6_moments"],
             "NEW": new_maps(a)}
    return {"checks": checks, "notes": notes, "counted": counted, "pass": all(checks.values()) if counted else None}


def control_file(row: dict) -> dict | None:
    """The CONTROL's FILE verdict: its profile's cart after child A's own end, by the probe's parser and its `file_verdict`
    rule. The probe names saves S1-S3 only (`SAVE_NAMES`) and a CONTROL makes 4-6, so the NEWEST save's truth is passed as
    the probe's "S1" and the answer renamed S<n>: the cart holds the newest save exactly when the probe's rule finds it."""
    path = Path(row.get("profile") or "") / "current_save.sav"
    truths = (row.get("a") or {}).get("truths") or {}
    if not row.get("profile") or not path.is_file() or not truths:
        return None
    newest = f"S{len(truths)}"
    parse = parse_image(path.read_bytes())
    verdict = file_verdict(parse, {"S1": truths[newest]})
    return {"verdict": newest + verdict[2:] if verdict.startswith("S1") else verdict, "newest": newest,
            "parse": brief(parse)}


def moment_of(save: dict, proof_first: dict) -> dict:
    """(check 6) The ruling-51 moment a save began at, by the harness's reads: a POKéMON CENTER's ground floor with the
    party at full HP; or after a big moment's proof turned true (the frames since, against MOMENT_FRAMES)."""
    start = save.get("start") or {}
    e1 = save.get("e1")
    const = start.get("const") or ""
    party = start.get("party") or []
    full = bool(party) and all(m and m[2] == m[3] for m in party)
    if const.endswith(CENTER_SUFFIX) and full:
        return {"moment": "center", "const": const}
    before = sorted(((frame, name) for name, frame in proof_first.items() if e1 is not None and frame <= e1), reverse=True)
    if before:
        frame, name = before[0]
        gap = e1 - frame
        within = MOMENT_FRAMES is None or gap <= MOMENT_FRAMES
        return {"moment": f"after {name}" if within else None, "since_proof": gap, "const": const, "full_hp": full}
    if const.endswith("GYM"):
        return {"moment": "gym (leader: unit-tested only)", "const": const}
    return {"moment": None, "const": const, "full_hp": full}


def file_of(ctx: dict, row: dict, frozen: Path) -> None:
    data = (frozen / "current_save.sav").read_bytes() if (frozen / "current_save.sav").exists() else None
    parse = parse_image(data) if data is not None else None
    truths = (row.get("a") or {}).get("truths") or {}
    row["file"] = {"verdict": file_verdict(parse, truths), "parse": brief(parse)}
    memory = frozen / "memory.jsonl"
    lines = [json.loads(x) for x in memory.read_text(encoding="utf-8").splitlines() if x.strip()] if memory.exists() else []
    row["frozen_save_lines"] = [line["id"] for line in lines if line.get("kind") == "save"]


def cmd_control(args) -> int:
    ctx = ctx_of(args)
    row, _profile = run_child_a(ctx, "CONTROL", args.seed, "none", args.frames)
    if row["child_a"]["word"] == "RESULT":
        row["file"] = control_file(row)
        row["grade"] = grade_control(row)
    row["ended"] = now()
    out = ctx["out"] / "rows" / f"CONTROL-{args.seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    a = row.get("a") or {}
    print("LIVE CONTROL " + json.dumps({"seed": args.seed, "word": row["child_a"]["word"],
                                        "reason": (a.get("play") or {}).get("reason"),
                                        "saves": [[s["save"], s.get("e1"), s["e3"], s.get("e4"), s.get("e7"),
                                                   (s.get("line") or {}).get("id")] for s in a.get("saves") or []],
                                        "NEW": new_maps(a), "seconds": row["child_a"]["seconds"],
                                        "file": (row.get("file") or {}).get("verdict"),
                                        "counted": (row.get("grade") or {}).get("counted"),
                                        "pass": (row.get("grade") or {}).get("pass"), "row": str(out)}),
          flush=True)
    return 0 if row["child_a"]["word"] == "RESULT" else 1


def cmd_arm(args) -> int:
    ctx = ctx_of(args)
    arm = args.arm
    determinism = None
    if arm == "K-BETWEEN":
        earlier = json.loads(Path(args.between_from).read_text(encoding="utf-8"))
        saves = earlier["a"]["saves"]
        if earlier["seed"] != args.seed or len(saves) < 2:
            raise SystemExit("K-BETWEEN needs a CONTROL row of the SAME seed with two saves")
        frame = (saves[0]["e7"] + saves[1]["e1"]) // 2
        if args.between_rule == "new":
            # (step 6 (c) finding, development) the spec's midpoint fell, on both rehearsal seeds, before child A stood on
            # any map it had not stood on before S1: NEW was EMPTY at the kill and check 3 could not fail. This rule kills
            # halfway between the first frame child A stands on a map of the CONTROL's NEW and S2's START
            first: dict[str, int] = {}
            for at, key in earlier["a"]["maps"]:
                first.setdefault(key, at)
            if not new_maps(earlier["a"]):
                raise SystemExit("K-BETWEEN (rule new) needs a CONTROL row whose NEW is not empty: NOT RUN")
            entered = min(first[key] for key in new_maps(earlier["a"]))
            frame = (entered + saves[1]["e1"]) // 2
        kill = f"F{frame}"
        determinism = {"from": args.between_from, "frame": frame, "S1": {k: saves[0].get(k) for k in ("e1", "e3", "e4", "e7")},
                       "S1_truth": saves[0]["truth"]}
        play = json.loads((Path(earlier["folder"]) / "a_play.json").read_text(encoding="utf-8"))
        determinism["presses_digest"] = presses_digest(play["game_reads"]["presses"]["log"], frame)
    else:
        kill = KILLS[arm]
    name = args.tag or arm
    row, profile = run_child_a(ctx, name, args.seed, kill, args.frames)
    row["arm"], row["name"] = arm, name
    if determinism is not None:
        determinism["rule"] = args.between_rule
    if row["child_a"]["word"] != "READY":
        row["result"] = f"NOT RUN: child A ended {row['child_a']['word']}, not at its kill"
    else:
        frozen = freeze(ctx, row, profile)
        file_of(ctx, row, frozen)
        if determinism is not None:
            a = row["a"]
            mine = {"S1": {k: a["saves"][0].get(k) for k in ("e1", "e3", "e4", "e7")}, "S1_truth": a["saves"][0]["truth"],
                    "presses_digest": a["kill"]["presses_digest"]}
            determinism["this"] = mine
            determinism["same"] = (mine["S1"] == determinism["S1"] and mine["S1_truth"] == determinism["S1_truth"]
                                   and mine["presses_digest"] == determinism["presses_digest"])
            row["determinism"] = determinism
        run_child_b(ctx, row, frozen)
        row["grade"] = grade(row)
    row["ended"] = now()
    out = ctx["out"] / "rows" / f"{name}-{args.seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    g = row.get("grade") or {}
    print("LIVE ARM " + json.dumps({"arm": arm, "seed": args.seed, "kill": kill, "file": (row.get("file") or {}).get("verdict"),
                                    "counted": g.get("counted"), "pass": g.get("pass"), "checks": g.get("checks"),
                                    "b_reason": ((row.get("b") or {}).get("play") or {}).get("reason"),
                                    "row": str(out)}, ensure_ascii=False), flush=True)
    return 0


# ------------------------------------------------------------------ step 7: the OLD arms (mutant R1-M) and LAUNCH
def file_sha256(path: Path) -> str:
    """A file's sha256 with its line ends made "\\n" (`rate_step5.file_sha256`'s rule: another checkout hashes the same)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def mutant_tree(out: Path, name: str, edits) -> tuple[Path, dict]:
    """A temp copy of this tree's `ai_player` with `edits` applied (the `revert_r1.make_copy` pattern: each anchor must
    occur exactly once). Returns its root and what it is (the edits, the edited files' sha256)."""
    root = out / "trees" / name
    if root.exists():
        raise SystemExit(f"{root} exists: a fresh --out (nothing is reused)")
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence"))
    files = {}
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old[:120]!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return root, {"root": str(root), "edits": [list(e) for e in edits], "sha256": files}


def cmd_old(args) -> int:
    """An OLD arm (K-INSIDE-OLD, K-SILENT-OLD): child B with mutant R1-M, on ITS OWN copy of the NEW twin's frozen set
    (the A/B on the SAME killed cart and memory; no extra New Game)."""
    ctx = ctx_of(args)
    twin_path = Path(args.twin_row)
    twin = json.loads(twin_path.read_text(encoding="utf-8"))
    name = {"K-INSIDE": "K-INSIDE-OLD", "K-SILENT": "K-SILENT-OLD"}[twin["arm"]]
    row = {"arm": name, "name": name, "seed": twin["seed"], "twin_row": str(twin_path), "started": now()}
    for key in ("a", "file", "frozen", "frozen_save_lines"):
        row[key] = twin.get(key)
    if (twin.get("child_a") or {}).get("word") != "READY" or not twin.get("frozen"):
        row["result"] = f"NOT RUN: the twin's child A ended {(twin.get('child_a') or {}).get('word')}, not at its kill"
    else:
        root, mutant = mutant_tree(ctx["out"], f"R1-M-{name}-{twin['seed']}", R1M_EDITS)
        row["mutant"] = mutant
        run_child_b(ctx, row, Path(twin["frozen"]["dir"]), root=root)
        ran = ((row.get("b") or {}).get("skills_saving") or {}).get("sha256")
        row["mutant_ran"] = ran is not None and ran == mutant["sha256"].get("skills/saving.py")
        row["grade"] = grade(row)
    row["ended"] = now()
    out = ctx["out"] / "rows" / f"{name}-{row['seed']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    g = row.get("grade") or {}
    print("LIVE ARM " + json.dumps({"arm": name, "seed": row["seed"], "mutant_ran": row.get("mutant_ran"),
                                    "counted": g.get("counted"), "old_shows": g.get("old_shows"),
                                    "checks": g.get("checks"), "result": row.get("result"),
                                    "b_reason": ((row.get("b") or {}).get("play") or {}).get("reason"), "row": str(out)},
                                   ensure_ascii=False), flush=True)
    return 0


def mirror_build_root(ctx: dict, name: str) -> Path:
    """(builder note 1) A build root of this run's OWN, so the REAL launcher's profile lives under `--out`, never under the
    main checkout's `<build_root>/profiles/`: the framework's code folders are JUNCTIONS to the build root (read: nothing
    writes bytecode, PYTHONDONTWRITEBYTECODE), and its top-level files, the global configs of `profiles/` and the cache
    are COPIES (`modules.runtime.get_base_path` is the folder holding `modules/`, so the mirror's own `profiles/`, `logs/`
    and `cache/` are the ones written)."""
    import _winapi

    source = ctx["build_root"]
    root = ctx["out"] / "buildroots" / name
    if root.exists():
        raise SystemExit(f"{root} exists: a fresh --out (nothing is reused)")
    (root / "profiles").mkdir(parents=True)
    for folder in MIRROR_LINKS:
        _winapi.CreateJunction(str(source / folder), str(root / folder))
    for entry in source.iterdir():
        if entry.is_file():
            shutil.copy2(entry, root / entry.name)
    for entry in (source / "profiles").iterdir():
        if entry.is_file():
            shutil.copy2(entry, root / "profiles" / entry.name)
    if (source / "cache").is_dir():
        shutil.copytree(source / "cache", root / "cache")
    (root / "logs").mkdir(exist_ok=True)
    # an EMPTY `.git` folder: the bot runs its stock auto-updater unless a `.git` exists at its base path or an ancestor
    # (`pokebot.py` "Fork divergence"), and this mirror sits outside any checkout. `modules/version.py` reads `.git/HEAD`
    # under a suppress, so an empty folder only leaves the version "dev"
    (root / ".git").mkdir()
    return root


def kill_tree(proc) -> list[list]:
    """Kill a process and every descendant, by PID (only processes this parent started)."""
    import psutil

    try:
        parent = psutil.Process(proc.pid)
        family = parent.children(recursive=True) + [parent]
    except psutil.Error:
        return []
    killed = []
    for p in family:
        try:
            killed.append([p.pid, p.name()])
            p.kill()
        except psutil.Error:
            pass
    return killed


def cmd_launch(args) -> int:
    """LAUNCH / LAUNCH-OLD (spec section 5): K-AFTER's frozen copy plus the stale fixture planted as `current_state.ss1`,
    continued through the REAL launcher (`-m ai_player run --continue`). LAUNCH-OLD runs the launcher of a copy with mutant
    S27 (`--continue` keeps the `.ss1`)."""
    from ai_player.paths import AppPaths
    from ai_player.skills.saving import ARRIVAL_BUDGET, CONTINUE_BUDGET

    ctx = ctx_of(args)
    source = Path(args.from_row)
    kafter = json.loads(source.read_text(encoding="utf-8"))
    if kafter["arm"] != "K-AFTER":
        raise SystemExit("LAUNCH runs on K-AFTER's row")
    name = "LAUNCH-OLD" if args.old else "LAUNCH"
    seed = kafter["seed"]
    saves = (kafter.get("a") or {}).get("saves") or []
    row = {"arm": name, "name": name, "seed": seed, "kafter_row": str(source),
           "kafter_file": (kafter.get("file") or {}).get("verdict"),
           "s2_line_id": (saves[1].get("line") or {}).get("id") if len(saves) > 1 else None, "started": now()}
    if (kafter.get("child_a") or {}).get("word") != "READY" or not kafter.get("frozen"):
        row["result"] = "NOT RUN: K-AFTER's child A did not reach its kill"
    else:
        mirror = mirror_build_root(ctx, f"{name}-{seed}")
        profile_name = f"ai-r1live-{name.lower()}-{seed}"
        profile = make_profile(mirror, profile_name, ctx["donor"])
        game = AppPaths.for_profile(profile_name, mirror, home="")
        game.game_dir.mkdir(parents=True)
        frozen = Path(kafter["frozen"]["dir"])
        for item in frozen.iterdir():
            shutil.copy2(item, profile / item.name if item.name.endswith(".sav") else game.game_dir / item.name)
        fixture = FIXTURE.read_bytes()
        if hashlib.md5(fixture).hexdigest() != FIXTURE_MD5:
            raise SystemExit(f"{FIXTURE} is not the registered fixture (md5 {FIXTURE_MD5})")
        (profile / "current_state.ss1").write_bytes(fixture)
        row["planted"] = {"mirror": str(mirror), "profile": str(profile), "ss1_md5": FIXTURE_MD5,
                          "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                                    for p in (profile / "current_save.sav", game.memory_jsonl) if p.exists()}}
        root = REPO
        if args.old:
            root, row["mutant"] = mutant_tree(ctx["out"], f"S27-{seed}", S27_EDITS)
        folder = ctx["out"] / "runs" / f"{name}-{seed}"
        folder.mkdir(parents=True, exist_ok=True)
        run_dir = folder / "launch_run"
        frames = CONTINUE_BUDGET + ARRIVAL_BUDGET + 600
        cmd = [sys.executable, "-B", "-m", "ai_player", "run", "--profile", profile_name, "--continue", "--frames",
               str(frames), "--wall-seconds", str(LAUNCH_WALL), "--build-root", str(mirror), "--run-dir", str(run_dir)]
        log = folder / "launcher.out"
        import subprocess

        from ai_player.options import ENV_BRAIN, ENV_CLOCK, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET

        # the PLAY brain with child B's plan, as `live_step5.py` launches it (the launcher passes these through; the
        # cartridge clock is the host's, as in every launcher run)
        personality, starter = plan_of(seed)
        env = child_env(mirror)
        env.update({ENV_BRAIN: "play", ENV_SEED: str(seed), ENV_PERSONALITY: personality, ENV_TARGET: TARGET,
                    ENV_CLOCK: WALL_CLOCK})
        if starter:
            env[ENV_STARTER] = starter
        row["env"] = {k: v for k, v in env.items() if k.startswith("AI_PLAYER_")}
        began = time.monotonic()
        with open(log, "wb") as handle:
            proc = subprocess.Popen(cmd, cwd=str(root), env=env, stdout=handle, stderr=subprocess.STDOUT)
            try:
                code = proc.wait(LAUNCH_TIMEOUT)
                killed = []
            except subprocess.TimeoutExpired:
                killed = kill_tree(proc)
                code = proc.wait(60)
        text = log.read_text(encoding="utf-8", errors="replace")
        row["launch"] = {"cmd": cmd, "cwd": str(root), "pid": proc.pid, "exit": code, "killed": killed,
                         "seconds": round(time.monotonic() - began, 1), "log": str(log), "run_dir": str(run_dir),
                         "frames": frames, "lines": [x for x in text.splitlines()
                                                     if x.startswith(("[AI-RUN]", "[AI-GATE]", "[AI-START]", "[AI-EXIT]"))]}
        row["memory_after"] = [{k: v for k, v in json.loads(x).items() if k != "memory"}
                               for x in game.memory_jsonl.read_text(encoding="utf-8").splitlines() if x.strip()] \
            if game.memory_jsonl.exists() else []
        row["grade"] = grade_launch(row)
    row["ended"] = now()
    out = ctx["out"] / "rows" / f"{name}-{seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    g = row.get("grade") or {}
    print("LIVE ARM " + json.dumps({"arm": name, "seed": seed, "exit": (row.get("launch") or {}).get("exit"),
                                    "counted": g.get("counted"), "pass": g.get("pass"), "old_shows": g.get("old_shows"),
                                    "checks": g.get("checks"), "first_look": (g.get("notes") or {}).get("first_look"),
                                    "result": row.get("result"), "row": str(out)}, ensure_ascii=False), flush=True)
    return 0


def grade_launch(row: dict) -> dict:
    """LAUNCH: the first look is a COLD BOOT (not OVERWORLD, its emulator frame = log frame minus the session's
    `frame_base` under COLD_BOOT_FRAMES), then the intro or the title before any CONTINUE; CONTINUE pressed; the run's
    purity verdict CLEAN; its session line continued save 2. LAUNCH-OLD shows its difference when the first look is the
    fixture's ROUTE101 overworld at an emulator frame of FIXTURE_FRAME or more. Both COUNT when K-AFTER's FILE was S2."""
    launch = row.get("launch") or {}
    run_dir = Path(launch["run_dir"]) if launch.get("run_dir") else None
    actions = b_actions(run_dir) if run_dir else []
    first = next((r for r in actions if r.get("decision") == "start"), None)
    sessions = [line for line in row.get("memory_after") or [] if line.get("kind") == "session"]
    session = sessions[-1] if sessions else None
    base = (session or {}).get("frame_base")
    screen = ((first or {}).get("observation") or {}).get("screen") or {}
    emu = first["frame"] - base if first and first.get("frame") is not None and base is not None else None
    at = next((i for i, r in enumerate(actions) if r.get("decision") == "continue the saved game"
               and str(r.get("action", "")).startswith("press A") and "CONTINUE" in str(r.get("reason", ""))), None)
    before = actions[:at] if at is not None else []
    title = any(t in str(r.get("digest") or "") for r in before for t in (" title", "ui=intro_movie", "ui=title"))
    verdict = None
    if run_dir is not None and (run_dir / "purity.json").is_file():
        verdict = json.loads((run_dir / "purity.json").read_text(encoding="utf-8")).get("verdict")
    # the launched mode played the PLAY brain (a placeholder brain presses nothing: every check below would be vacuous)
    brain = any(" brain=play " in line for line in launch.get("lines") or [] if line.startswith("[AI-START] mode="))
    checks = {"brain_is_play": brain,
              "cold_boot_first_look": screen.get("game_state") not in (None, "OVERWORLD") and emu is not None
              and 0 <= emu < COLD_BOOT_FRAMES,
              "title_before_continue": title, "continue_pressed": at is not None, "purity_clean": verdict == "CLEAN",
              "session_continued_save_2": session is not None and session.get("how") == "continue"
              and row.get("s2_line_id") is not None and session.get("continued_from") == row.get("s2_line_id")}
    notes = {"first_look": {"log_frame": (first or {}).get("frame"), "frame_base": base, "emulator_frame": emu,
                            "game_state": screen.get("game_state"), "digest": (first or {}).get("digest")},
             "continue_press": actions[at].get("reason") if at is not None else None, "purity": verdict,
             "session": session, "launcher_exit": launch.get("exit"), "kafter_file": row.get("kafter_file")}
    counted = row.get("kafter_file") == "S2" and bool(launch)
    out = {"checks": checks, "notes": notes, "counted": counted, "pass": all(checks.values()) if counted else None}
    if row["arm"] == "LAUNCH-OLD":
        out["old_shows"] = brain and screen.get("game_state") == "OVERWORLD" and emu is not None and emu >= FIXTURE_FRAME \
            and FIXTURE_MAP in str((first or {}).get("digest") or "")
        out["pass"] = None
    return out


# ------------------------------------------------------------------ step 7: the one verdict
def load_row(out: Path, name: str, seed: int) -> dict | None:
    path = out / "rows" / f"{name}-{seed}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def summary_of(name: str, row: dict | None) -> dict:
    """One arm on one seed: counted / pass / old_shows, re-graded by THIS (registered) code, with why it does not count."""
    if row is None:
        return {"counted": False, "pass": None, "why": "no row (the arm did not run)"}
    if row.get("result"):
        return {"counted": False, "pass": None, "why": row["result"]}
    if name == "CONTROL":
        g = grade_control(row)
    elif name in ("LAUNCH", "LAUNCH-OLD"):
        g = grade_launch(row)
    else:
        g = grade(row)
    s = {"counted": g["counted"], "pass": g.get("pass"), "old_shows": g.get("old_shows"), "checks": g["checks"],
         "notes": g["notes"]}
    rule = (row.get("determinism") or {}).get("rule")
    if name == "K-BETWEEN" and rule != BETWEEN_RULE:
        s.update(counted=False, why=f"its kill rule is {rule!r}, not the registered {BETWEEN_RULE!r}")
    if name == "K-BETWEEN-MID" and rule != "midpoint":
        s.update(counted=False, why=f"its kill rule is {rule!r}, not the midpoint")
    if name in ("K-INSIDE-OLD", "K-SILENT-OLD") and not row.get("mutant_ran"):
        s.update(counted=False, why="child B did not run the R1-M copy (its skills/saving.py sha256 differs)")
    if not s["counted"] and "why" not in s:
        s["why"] = "its reach conditions do not hold (FILE, NEW, check 7, K-SILENT's 0 sectors, or the determinism line)"
    return s


def verdict_of(summaries: dict, seeds) -> dict:
    """(spec section 5 "Counting, floors and the one verdict") PASS: every graded arm counts on >= FLOOR seeds, every
    counted NEW arm passes every check, and every counted OLD arm shows its difference. FAIL: a counted NEW arm fails a
    check, or a counted OLD arm does not show its difference. INCONCLUSIVE: nothing failed but an arm is below its floor
    (never reported as a PASS). An OLD arm counts on a seed only when its NEW twin counts there."""
    per = {}
    for name in GRADED_ARMS:
        counted, passed, failed, why = [], [], [], {}
        for seed in seeds:
            s = summaries.get((name, seed)) or {"counted": False, "why": "no row"}
            ok_count = bool(s.get("counted"))
            if name in OLD_OF and FAULT != "old_without_twin":
                twin = summaries.get((OLD_OF[name], seed)) or {}
                if ok_count and not twin.get("counted"):
                    why[seed] = f"its NEW twin {OLD_OF[name]} does not count on this seed"
                ok_count = ok_count and bool(twin.get("counted"))
            if not ok_count:
                why.setdefault(seed, s.get("why", "not counted"))
                continue
            counted.append(seed)
            good = s.get("old_shows") if name in OLD_OF else s.get("pass")
            (passed if good else failed).append(seed)
        per[name] = {"counted": counted, "passed": passed, "failed": failed, "not_counted": why,
                     "floor_met": len(counted) >= FLOOR}
    failing = {n: p["failed"] for n, p in per.items() if p["failed"]}
    below = [n for n, p in per.items() if not p["floor_met"]]
    if failing:
        word = "FAIL"
    elif below and FAULT != "floor_ignored":
        word = "INCONCLUSIVE"
    else:
        word = "PASS"
    return {"verdict": word, "per_arm": per, "failing": failing, "below_floor": below, "floor": FLOOR,
            "seeds": list(seeds)}


def determinism_lines(out: Path, seeds) -> list[dict]:
    """(finding N4) For each seed: S1's and S2's e1/e3 frames and RAM truths for every child A arm, against the CONTROL's.
    One trajectory per seed, replayed up to each kill (CLAUDE.md rule 8): a difference is reported, and each arm is still
    graded on its own child A's truths."""
    lines = []
    child_a_arms = ("CONTROL", "K-AFTER", "K-INSIDE", "K-SILENT", "K-FIRST", "K-BETWEEN", "K-BETWEEN-MID")
    for seed in seeds:
        rows = {name: load_row(out, name, seed) for name in child_a_arms}
        def events(row):
            saves = ((row or {}).get("a") or {}).get("saves") or []
            return {f"S{s['save']}": {"e1": s.get("e1"), "e3": s["e3"], "truth": {k: s["truth"].get(k) for k in
                                                                                   IDENTITY_KEYS}} for s in saves[:2]}
        control = events(rows["CONTROL"])
        for name, row in rows.items():
            if row is None or name == "CONTROL":
                continue
            mine = events(row)
            differ = [key for key in mine if key in control and mine[key] != control[key]]
            lines.append({"seed": seed, "arm": name, "events": {k: [v["e1"], v["e3"]] for k, v in mine.items()},
                          "same_as_control": not differ, "differ": differ})
    return lines


def discriminators(out: Path, seeds, summaries: dict) -> list[dict]:
    """Every discriminator, computed per seed from the arms' own records, and whether its two sides DIFFER (an A/B whose
    sides cannot differ is vacuous: reported, never passed)."""
    found = []
    for seed in seeds:
        get = lambda n: summaries.get((n, seed)) or {}  # noqa: E731
        for new, old in (("K-INSIDE", "K-INSIDE-OLD"), ("K-SILENT", "K-SILENT-OLD")):
            a, b = get(new).get("notes") or {}, get(old).get("notes") or {}
            nm = a.get("NEW") or []
            left = sorted(m for m in nm if m in ((a.get("3_memory") or {}).get("restored_maps") or []))
            right = sorted(m for m in nm if m in ((b.get("3_memory") or {}).get("restored_maps") or []))
            shown = (a.get("4_actions") or {}).get("continue_time_read")
            stamps = (a.get("5_free_and_gap") or {}).get("stamps")
            found.append({"seed": seed, "pair": f"{new} / {old}", "NEW": nm,
                          "NEW maps restored": [left, right],
                          "continued_from": [(a.get("3_memory") or {}).get("continued_from"),
                                             (b.get("3_memory") or {}).get("continued_from")],
                          "CONTINUE TIME shown / the save stamps": [shown, stamps],
                          "differ": bool(nm) and left != right})
        aft, ins = get("K-AFTER").get("notes") or {}, get("K-INSIDE").get("notes") or {}
        found.append({"seed": seed, "pair": "K-AFTER / K-INSIDE (the kill after the write vs inside it)",
                      "FILE": [(aft.get("1_file") or {}).get("verdict"), (ins.get("1_file") or {}).get("verdict")],
                      "continued_from": [(aft.get("3_memory") or {}).get("continued_from"),
                                         (ins.get("3_memory") or {}).get("continued_from")],
                      "differ": (aft.get("1_file") or {}).get("verdict") != (ins.get("1_file") or {}).get("verdict")})
        la, lo = get("LAUNCH").get("notes") or {}, get("LAUNCH-OLD").get("notes") or {}
        fa, fo = la.get("first_look") or {}, lo.get("first_look") or {}
        found.append({"seed": seed, "pair": "LAUNCH / LAUNCH-OLD (the .ss1 dropped vs kept)",
                      "first look (state, emulator frame)": [[fa.get("game_state"), fa.get("emulator_frame")],
                                                             [fo.get("game_state"), fo.get("emulator_frame")]],
                      "differ": [fa.get("game_state"), fa.get("emulator_frame")] != [fo.get("game_state"),
                                                                                     fo.get("emulator_frame")]})
        first, control = get("K-FIRST").get("notes") or {}, get("CONTROL").get("notes") or {}
        found.append({"seed": seed, "pair": "K-FIRST / CONTROL (the first save's write cut vs complete)",
                      "FILE": [(first.get("1_file") or {}).get("verdict"), ((control.get("file") or {}).get("verdict"))],
                      "differ": (first.get("1_file") or {}).get("verdict") != (control.get("file") or {}).get("verdict")})
        between = get("K-BETWEEN").get("notes") or {}
        found.append({"seed": seed, "pair": "K-BETWEEN (NEW at the kill vs the restored memory)",
                      "NEW": between.get("NEW"), "restored_maps": (between.get("3_memory") or {}).get("restored_maps"),
                      "differ": bool(between.get("NEW"))})
    return found


def between_caveat(summaries: dict, seeds) -> str:
    """(R1 fix round, review R-5: the headline carries the caveat, CLAUDE.md session discipline 2) When K-BETWEEN is graded
    under a kill rule that is not the spec's midpoint, the verdict line says so, with how the spec's own rule fared on these
    seeds (its diagnostic arm K-BETWEEN-MID). Empty under the spec's rule."""
    if BETWEEN_RULE == "midpoint":
        return ""
    counted = sum(1 for seed in seeds if (summaries.get(("K-BETWEEN-MID", seed)) or {}).get("counted"))
    return (f", WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE {BETWEEN_RULE!r}, NOT THE SPEC'S MIDPOINT (the midpoint "
            f"arm K-BETWEEN-MID counted {counted} of {len(seeds)}{': vacuous' if counted < FLOOR else ''})")


def cmd_verdict(args) -> int:
    out = Path(args.out).resolve()
    seeds = list(range(args.first, args.last + 1))
    summaries = {(name, seed): summary_of(name, load_row(out, name, seed))
                 for seed in seeds for name in GRADED_ARMS + tuple(DIAGNOSTIC_ARMS)}
    result = verdict_of(summaries, seeds)
    print(f"LIVE R1 ARMS (seeds {seeds[0]}-{seeds[-1]}; floor {FLOOR} of {len(seeds)}; K-BETWEEN rule {BETWEEN_RULE!r})")
    for name in GRADED_ARMS + tuple(DIAGNOSTIC_ARMS):
        cells = []
        for seed in seeds:
            s = summaries[(name, seed)]
            good = s.get("old_shows") if name in OLD_OF else s.get("pass")
            cells.append(f"{seed}:{'-' if not s['counted'] else ('ok' if good else 'BAD')}")
        tag = "DIAGNOSTIC" if name in DIAGNOSTIC_ARMS else (
            "floor met" if result["per_arm"][name]["floor_met"] else "BELOW FLOOR")
        counted = sum(1 for seed in seeds if summaries[(name, seed)]["counted"]) if name in DIAGNOSTIC_ARMS else \
            len(result["per_arm"][name]["counted"])
        print(f"  {name:<14} counted {counted}/{len(seeds)} {tag:<11} " + " ".join(cells))
    for (name, seed), s in sorted(summaries.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print("ARM " + json.dumps({"arm": name, "seed": seed, "counted": s["counted"], "pass": s.get("pass"),
                                   "old_shows": s.get("old_shows"), "why": s.get("why"), "checks": s.get("checks")},
                                  ensure_ascii=False))
    for line in determinism_lines(out, seeds):
        print("DETERMINISM " + json.dumps(line))
    found = discriminators(out, seeds, summaries)
    for item in found:
        print("DISCRIMINATOR " + json.dumps(item, ensure_ascii=False))
    payload = {"verdict": result, "summaries": {f"{n}-{s}": v for (n, s), v in summaries.items()},
               "discriminators": found}
    (out / "verdict.json").write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"PER ARM {json.dumps({n: {k: p[k] for k in ('counted', 'failed', 'floor_met')} for n, p in result['per_arm'].items()})}")
    print(f"LIVE R1 VERDICT: {result['verdict']}{between_caveat(summaries, seeds)} (failing: {result['failing'] or 'none'}; "
          f"below the floor: {result['below_floor'] or 'none'}; discriminators that differ: "
          f"{sum(1 for d in found if d['differ'])} of {len(found)})")
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}[result["verdict"]]


# ------------------------------------------------------------------ step 7: registration (spec section 5)
#: (spec section 5's table) each arm's kill, FILE expectation and what the AI must show; FILE follows the arm's OWN record
#: at the kill (ORCHESTRATOR RULING 1)
EXPECTED = {
    "CONTROL": "no kill; FILE = the newest save; every save at a ruling-51 moment (check 6) and on a held free screen 3+ "
               "game minutes after the last (check 5); the run ends done at ch1_pokedex with its end save made",
    "K-AFTER": "S2.e4+40; FILE S2; no page; CONTINUE; arrival = S2's truth; restored = save 2 and holds ALL of NEW",
    "K-INSIDE": "S2.e3+130; FILE S1+ERROR if a new sector of save 2 is complete at the kill (else S1); the CORRUPTED page "
                "read; CONTINUE; arrival = S1; restored = save 1 and holds NO map of NEW; S2's line in the file first",
    "K-SILENT": "S2.e3+9; counts only with 0 new sectors at the kill and S2's line written before it; FILE S1; no page; "
                "TIME match; arrival = S1; restored = save 1 and holds NO map of NEW",
    "K-FIRST": "S1.e3+128; FILE CORRUPT if a new sector of save 1 is complete at the kill (else EMPTY); the ERASED page "
               "read; stops 'the save is gone'; the main menu took input and saw zero presses",
    "K-BETWEEN": f"rule {BETWEEN_RULE!r} from the same seed's CONTROL, with the determinism line; FILE S1; no page; arrival "
                 "= S1; restored = save 1 and holds NO map of NEW (NEW up to the kill)",
    "LAUNCH": "K-AFTER's frozen copy + the fixture as current_state.ss1, through -m ai_player run --continue: the first "
              "look a cold boot (not OVERWORLD, emulator frame < 300), the intro or title before CONTINUE, CONTINUE, purity "
              "CLEAN, the session line continued save 2",
    "K-INSIDE-OLD": "K-INSIDE's frozen copy, child B with R1-M: shows the restored memory holds a map of NEW (newer than "
                    "the save), continued_from = save 2, check 3 FAILS",
    "K-SILENT-OLD": "K-SILENT's frozen copy, child B with R1-M: the same difference as K-INSIDE-OLD",
    "LAUNCH-OLD": "LAUNCH with mutant S27: the first look is the ROUTE101 overworld (0,16) at an emulator frame >= 66883",
}
COUNTING = ("an arm COUNTS on a seed when (1) its FILE equals the expectation from its own record, NEW is not empty where "
            "check 3 needs it, check 7 holds where it applies, child A reached the kill (K-SILENT: 0 new sectors at it; "
            "K-BETWEEN: its determinism line); an OLD arm only when its NEW twin counts there and its child B ran the "
            "mutant copy; LAUNCH and LAUNCH-OLD when K-AFTER's FILE was S2; CONTROL when child A ran to its own end")


def registered_numbers(seeds: tuple[int, int] = HELD_OUT) -> dict:
    """Everything the held-out run is graded by (spec section 5), hashed into its ledger registration: `ledger.begin`
    refuses the run when any of it changed after `register`. `seeds`: the held-out range (first, last); (R1 fix round)
    `ledger register|begin --first --last` name it, so a re-run on NEW seeds registers the seeds it plays."""
    from ai_player.skills.saving import ARRIVAL_BUDGET, CONTINUE_BUDGET

    return {"family": "story", "driver": "live_r1", "seeds": list(seeds), "target": TARGET, "frames_a": FRAMES_A,
            "game_clock": GAME_CLOCK, "wall_clock": WALL_CLOCK, "kills": KILLS, "between_rule": BETWEEN_RULE,
            "diagnostic": DIAGNOSTIC_ARMS, "child_a_timeout": CHILD_A_TIMEOUT, "child_b_timeout": CHILD_B_TIMEOUT,
            "child_b_frames": CONTINUE_BUDGET + ARRIVAL_BUDGET + 600, "continue_budget": CONTINUE_BUDGET,
            "arrival_budget": ARRIVAL_BUDGET, "moment_frames": MOMENT_FRAMES, "after": AFTER, "proof_every": PROOF_EVERY,
            "active_frames": ACTIVE_FRAMES, "idle_flash_every": IDLE_FLASH_EVERY, "big_moments": BIG_MOMENTS,
            "expected": EXPECTED, "graded_arms": GRADED_ARMS, "old_of": OLD_OF, "floor": FLOOR, "counting": COUNTING,
            "verdict_rule": verdict_of.__doc__, "r1m_edits": R1M_EDITS, "s27_edits": S27_EDITS,
            "fixture_md5": FIXTURE_MD5, "fixture_frame": FIXTURE_FRAME, "fixture_map": FIXTURE_MAP,
            "cold_boot_frames": COLD_BOOT_FRAMES, "launch_wall": LAUNCH_WALL, "launch_timeout": LAUNCH_TIMEOUT,
            "files": {name: file_sha256(REPO / name) for name in HASHED_FILES}}


def cmd_ledger(args) -> int:
    from ai_player.gates import ledger
    from ai_player.gates.provenance import line_digest, provenance

    seeds = (args.first or HELD_OUT[0], args.last or HELD_OUT[1])
    numbers = registered_numbers(seeds)
    sha = ledger.numbers_sha256(numbers)
    # the note comes from a FILE (USER RULING 29: prose never passes through a shell-quoted argument)
    args.note = Path(args.note_file).read_text(encoding="utf-8").strip() if args.note_file else None
    if args.action == "numbers":
        print(json.dumps(numbers, indent=1, default=str))
        print(f"REGISTERED NUMBERS sha256 {sha}")
        return 0
    if args.action == "register":
        entry = ledger.register("story", "live_r1", seeds[0], seeds[1], sha, note=args.note or
                                "R1 + R2 build spec section 5: the live proof's held-out arms (graded)")
        print(f"REGISTERED numbers sha256 {sha}")
        print("ENTRY " + json.dumps(entry))
        return 0
    if args.action == "begin":
        code = provenance(REPO)
        print(code)
        entry, lines = ledger.begin("story", "live_r1", args.purpose, seeds[0], seeds[1], sha, line_digest(code),
                                    note=args.note or "")
        for line in lines:
            print(line)
        print("ENTRY " + json.dumps(entry))
        return 0
    if args.action == "finish":
        ledger.finish(args.id, Path(args.verdict_file).read_text(encoding="utf-8").strip(), args.evidence)
        print(f"FINISHED #{args.id}")
        return 0
    return 2


# ------------------------------------------------------------------ step 7: the selftest (finding F4)
def selftest(rows_dirs: list[Path]) -> dict:
    """The grader and the verdict rule on RECORDED rows (step 6's rehearsals and step 7's rehearsal of the new arms) and
    on PLANTED cases built from them. Clean: every case as expected. Each planted FAULT (`FAULTS`, set in the module's
    FAULT) must make at least one case come out wrong."""
    import copy
    import tempfile

    rows: dict[str, dict] = {}
    for folder in rows_dirs:
        for path in sorted(Path(folder).glob("*.json")):
            row = json.loads(path.read_text(encoding="utf-8"))
            rows[f"{row.get('name', row['arm'])}-{row['seed']}"] = row
    cases: list[dict] = []

    def case(name: str, got, expected) -> None:
        cases.append({"case": name, "expected": expected, "got": got, "ok": got == expected})

    def need(key: str) -> dict:
        if key not in rows:
            raise SystemExit(f"selftest: the recorded row {key} is missing from {rows_dirs}")
        return rows[key]

    # the mutants of the live A/B are the unit lane's (revert_r1's S20 + S22, and S27)
    from ai_player.gates.revert_r1 import MUTANTS  # its import loads revert_r1_mutants.json (S20, S22)

    s20 = [tuple(e) for e in MUTANTS["S20"][2]] + [tuple(e) for e in MUTANTS["S22"][2]]
    case("R1-M is revert_r1's S20 + S22, edit for edit", [tuple(e) for e in R1M_EDITS], s20)
    case("LAUNCH-OLD's mutant is revert_r1's S27, edit for edit", [tuple(e) for e in S27_EDITS],
         [tuple(e) for e in MUTANTS["S27"][2]])
    # 1. recorded arms (step 6 (c)): counted and passing
    for key in ("K-INSIDE-5405", "K-INSIDE-5406", "K-SILENT-5405", "K-SILENT-5406", "K-FIRST-5405", "K-FIRST-5406",
                "K-BETWEEN-NEW-5405", "K-BETWEEN-NEW-5406", "K-AFTER-5405"):
        g = grade(need(key))
        case(f"recorded {key}: counted and passing", [g["counted"], g["pass"]], [True, True])
    for key in ("K-BETWEEN-5405", "K-BETWEEN-5406"):
        g = grade(need(key))
        case(f"recorded {key} (the spec's midpoint): NOT counted (NEW empty at the kill: vacuous)",
             [g["counted"], g["notes"]["NEW"]], [False, []])
    for key in ("CONTROL-5405", "CONTROL-5406"):
        g = grade_control(need(key))
        case(f"recorded {key}: counted and passing (FILE = the newest save)", [g["counted"], g["pass"]], [True, True])
    for key in ("K-INSIDE-OLD-5405", "K-SILENT-OLD-5405"):
        row = need(key)
        g = grade(row)
        case(f"recorded {key} (R1-M): its twin's reach, the mutant ran, and it SHOWS the difference (check 3 FAILS)",
             [g["counted"], bool(row.get("mutant_ran")), g["old_shows"], g["checks"]["3_memory"]], [True, True, True, False])
    g = grade_launch(need("LAUNCH-5405"))
    case("recorded LAUNCH-5405: counted and passing (a cold boot, the title, CONTINUE, CLEAN, save 2)",
         [g["counted"], g["pass"]], [True, True])
    g = grade_launch(need("LAUNCH-OLD-5405"))
    case("recorded LAUNCH-OLD-5405 (S27): SHOWS the fixture's overworld first", [g["counted"], g["old_shows"]], [True, True])
    # 2. planted cases (FAULT INPUT: the grader must see each)
    planted = copy.deepcopy(need("K-SILENT-5405"))
    planted["b"]["arrival"]["pos"] = [planted["b"]["arrival"]["pos"][0] + 1, planted["b"]["arrival"]["pos"][1]]
    case("FAULT INPUT the arrival one tile off: check 2 FAILS", grade(planted)["checks"]["2_identity"], False)
    planted = copy.deepcopy(need("K-FIRST-5405"))
    menu_from = planted["b"]["menu_input_from"]
    planted["b"]["presses"].append([menu_from + 40, "Down", [None, None, None, menu_from + 40]])
    case("FAULT INPUT K-FIRST pressed Down after the main menu took input: check 4 FAILS",
         grade(planted)["checks"]["4_actions"], False)
    planted = copy.deepcopy(need("K-INSIDE-5405"))
    temp = Path(tempfile.mkdtemp(prefix="live_r1_selftest_"))
    try:
        source = Path(planted["b_run"])
        shutil.copy2(source / "actions.jsonl", temp / "actions.jsonl")
        snapshots = [json.loads(x) for x in (source / "world.jsonl").read_text(encoding="utf-8").splitlines()]
        reasons = [json.loads(x).get("reason") for x in (source / "actions.jsonl").read_text(encoding="utf-8").splitlines()
                   if json.loads(x).get("decision") == "world" and json.loads(x).get("action") == "snapshot"]
        change = reasons.index("a map change")
        new = new_maps(planted["a"]) or ["0:10"]
        snapshots[change]["maps"][new[0]] = snapshots[change]["maps"].get(new[0]) or {}
        (temp / "world.jsonl").write_text("".join(json.dumps(s) + "\n" for s in snapshots), encoding="utf-8")
        planted["b_run"] = str(temp)
        case("FAULT INPUT child B's first map change ENTERS a NEW map (F2): check 3 reads the RESTORE snapshot and passes",
             grade(planted)["checks"]["3_memory"], True)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    planted = copy.deepcopy(need("CONTROL-5405"))
    first = planted["a"]["saves"][0]
    first["start"] = {**(first.get("start") or {}), "const": "ROUTE101"}
    planted["a"]["proof_first"] = {}
    case("FAULT INPUT a save at no ruling-51 moment: CONTROL's check 6 FAILS",
         grade_control(planted)["checks"]["6_moments"], False)
    planted = copy.deepcopy(need("LAUNCH-5405"))
    temp = Path(tempfile.mkdtemp(prefix="live_r1_selftest_"))
    try:
        source = Path(planted["launch"]["run_dir"])
        lines = (source / "actions.jsonl").read_text(encoding="utf-8").splitlines()
        first_look = json.loads(lines[0])
        first_look["observation"]["screen"]["game_state"] = "OVERWORLD"
        (temp / "actions.jsonl").write_text("\n".join([json.dumps(first_look)] + lines[1:]) + "\n", encoding="utf-8")
        shutil.copy2(source / "purity.json", temp / "purity.json")
        planted["launch"]["run_dir"] = str(temp)
        case("FAULT INPUT LAUNCH's first look is an OVERWORLD: the cold-boot check FAILS",
             grade_launch(planted)["checks"]["cold_boot_first_look"], False)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    # 3. the verdict rule on planted summaries (4 seeds)
    seeds = (1, 2, 3, 4)

    def table(over: dict | None = None) -> dict:
        over = over or {}
        out = {}
        for name in GRADED_ARMS:
            for seed in seeds:
                out[(name, seed)] = {"counted": True, "pass": True if name not in OLD_OF else None,
                                     "old_shows": True if name in OLD_OF else None}
        for (name, seed), value in over.items():
            out[(name, seed)] = {**out[(name, seed)], **value}
        return out

    case("CONTROL every arm counted and good on 4 seeds: PASS", verdict_of(table(), seeds)["verdict"], "PASS")
    got = verdict_of(table({("K-FIRST", 3): {"counted": False}, ("K-FIRST", 4): {"counted": False}}), seeds)
    case("FAULT INPUT K-FIRST counts on 2 of 4 (below the floor): INCONCLUSIVE, never PASS", got["verdict"], "INCONCLUSIVE")
    got = verdict_of(table({("K-INSIDE", 4): {"counted": False}}), seeds)
    case("FAULT INPUT K-INSIDE does not count on seed 4: K-INSIDE-OLD does not count there either",
         got["per_arm"]["K-INSIDE-OLD"]["counted"], [1, 2, 3])
    got = verdict_of(table({("K-SILENT-OLD", 2): {"old_shows": False}}), seeds)
    case("FAULT INPUT a counted OLD arm shows no difference: FAIL", got["verdict"], "FAIL")
    got = verdict_of(table({("LAUNCH", 1): {"pass": False}}), seeds)
    case("FAULT INPUT a counted NEW arm fails a check: FAIL", got["verdict"], "FAIL")
    # (R1 fix round, review R-5) the verdict line names K-BETWEEN's substituted rule and how the spec's midpoint fared
    mid = {**table(), **{("K-BETWEEN-MID", seed): {"counted": False} for seed in seeds}}
    case(f"the verdict line carries K-BETWEEN's rule {BETWEEN_RULE!r} and the midpoint's vacuity (0 of 4)",
         between_caveat(mid, seeds), "" if BETWEEN_RULE == "midpoint" else
         f", WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE {BETWEEN_RULE!r}, NOT THE SPEC'S MIDPOINT (the midpoint arm "
         f"K-BETWEEN-MID counted 0 of 4: vacuous)")
    bad = [c for c in cases if not c["ok"]]
    return {"cases": cases, "failed": len(bad), "verdict": "PASS" if not bad else "FAIL"}


def cmd_selftest(args) -> int:
    global FAULT
    dirs = [Path(d) for d in args.rows]
    runs = [None] + list(FAULTS) if args.all else [args.fault]
    results = {}
    for fault in runs:
        FAULT = fault
        try:
            result = selftest(dirs)
        finally:
            FAULT = None
        results[fault] = result
        print(f"==== SELFTEST {'(clean)' if fault is None else 'FAULT ' + fault + ': ' + FAULTS[fault]}")
        for c in result["cases"]:
            if fault is None or not c["ok"]:
                print(f"  [{'ok' if c['ok'] else 'WRONG'}] {c['case']}: got {json.dumps(c['got'])}"
                      + ("" if c["ok"] else f", expected {json.dumps(c['expected'])}"))
        print(f"SELFTEST VERDICT{'' if fault is None else ' (fault ' + fault + ')'}: {result['verdict']} "
              f"({len(result['cases']) - result['failed']} of {len(result['cases'])} cases as expected)")
    if not args.all:
        return 0 if results[args.fault]["verdict"] == "PASS" else 1
    clean = results[None]["verdict"] == "PASS"
    caught = [f for f in FAULTS if results[f]["verdict"] == "FAIL"]
    ok = clean and len(caught) == len(FAULTS)
    print(f"SELFTEST: the clean run {'PASSES' if clean else 'FAILS'} ({len(results[None]['cases'])} cases) and "
          f"{len(caught)} of {len(FAULTS)} planted faults FAIL as they must"
          + ("" if len(caught) == len(FAULTS) else f" (NOT caught: {[f for f in FAULTS if f not in caught]})")
          + f" -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


#: the GBA's frame rate (59.7275 frames a second): game hours from frames
FPS = 59.7275


def measure_row(row: dict) -> dict:
    """Step 6 (b)'s numbers for one CONTROL row (spec section 8 step 6 (b)): the saves, their moments (check 6), the
    dialog's frames with the AI's pacing, the line sizes, the saves per game hour (T2), T1 (the stamp's look against the
    clock's freeze at e3 - 1, and the stamp against the RAM truth's hours and minutes), NEW and the S1/S2 identities."""
    a = row.get("a") or {}
    play = a.get("play") or {}
    saves = a.get("saves") or []
    proof_first = a.get("proof_first") or {}
    pokedex = proof_first.get(TARGET)
    out_saves = []
    for save in saves:
        line = save.get("line") or {}
        truth = save.get("truth") or {}
        stamp = line.get("play_time")
        moment = moment_of(save, proof_first)
        out_saves.append({
            "save": save["save"], "id": line.get("id"), "why": line.get("why"), "e1": save.get("e1"), "e3": save["e3"],
            "e3_exact": save.get("e3_exact"), "e4": save.get("e4"), "e7": save.get("e7"),
            "start_to_e3": save["e3"] - save["e1"] if save.get("e1") is not None else None,
            "write_e4_minus_e3": save["e4"] - save["e3"] if save.get("e4") else None,
            "first_sector_minus_e3": save["first_sector"] - save["e3"] if save.get("first_sector") else None,
            "e3_to_free_e7": save["e7"] - save["e3"] if save.get("e7") else None,
            "start_to_free_e7": save["e7"] - save["e1"] if save.get("e7") and save.get("e1") is not None else None,
            "line_frame_minus_e3": line["frame"] - save["e3"] if "frame" in line else None,
            "line_seen_minus_e3": line["seen_at"] - save["e3"] if "seen_at" in line else None,
            "T1_stamp_look_before_freeze": line["frame"] < save["e3"] - 1 if "frame" in line else None,
            "T1_stamp_equals_truth_hm": stamp == (truth.get("play_time") or [None, None])[:2] if stamp else None,
            "stamp": stamp, "truth_play_time": truth.get("play_time"), "line_bytes": line.get("bytes"),
            "full": line.get("full"), "slot_at_e4_equals_truth": save.get("slot_at_e4_equals_truth"),
            "held_free_at_start": (save.get("start") or {}).get("held_free"), "map_at_start": (save.get("start") or {}).get("const"),
            "moment": moment, "before_target": pokedex is None or save["e3"] < pokedex})
    frames = play.get("frames") or 0
    hours = frames / FPS / 3600 if frames else None
    s12 = {f"S{s['save']}": {k: s["truth"].get(k) for k in IDENTITY_KEYS} for s in saves[:2]}
    return {"seed": row["seed"], "reason": play.get("reason"), "frames": frames, "seconds": play.get("seconds"),
            "child_a_seconds": (row.get("child_a") or {}).get("seconds"), "saves": out_saves, "saves_n": len(saves),
            "saves_before_target": sum(1 for s in out_saves if s["before_target"]),
            "game_hours": round(hours, 3) if hours else None,
            "saves_per_game_hour": round(len(saves) / hours, 2) if hours else None,
            "NEW": new_maps(a), "identities": s12, "proof_first": proof_first, "end_save": play.get("end_save"),
            "flash_reads": a.get("flash_reads"), "watched_frames": a.get("frames")}


def continue_numbers(row: dict) -> dict:
    """Step 6 (c)'s numbers for one arm: child B's frames from power-on (the emulator's, by the harness) to the main menu
    taking input, to the CONTINUE press, to the HELD free arrival; the press-to-arrival span; both children's wall times;
    child A's frame at the kill."""
    b = row.get("b") or {}
    press = next((p[0] for p in b.get("presses") or [] if p[1] == "A" and p[2] and p[2][0] == "Task_HandleMainMenuInput"),
                 None)
    arrival = (b.get("arrival") or {}).get("f")
    return {"arm": row["arm"], "seed": row["seed"], "menu_input_from": b.get("menu_input_from"), "continue_press": press,
            "arrival": arrival, "press_to_arrival": arrival - press if arrival is not None and press is not None else None,
            "b_frames_run": b.get("frames"), "child_a_seconds": (row.get("child_a") or {}).get("seconds"),
            "child_b_seconds": (row.get("child_b") or {}).get("seconds"), "kill_frame": ((row.get("a") or {}).get("kill")
                                                                                         or {}).get("frame")}


def cmd_measure(args) -> int:
    rows = sorted(Path(args.out).glob("rows/CONTROL-*.json"))
    out = [measure_row(json.loads(path.read_text(encoding="utf-8"))) for path in rows]
    for item in out:
        print("MEASURE " + json.dumps(item, ensure_ascii=False), flush=True)
    for path in sorted(Path(args.out).glob("rows/K-*.json")):
        print("CONTINUE " + json.dumps(continue_numbers(json.loads(path.read_text(encoding="utf-8")))), flush=True)
    return 0


def cmd_b_again(args) -> int:
    """(development) Run child B again on ITS OWN fresh copy of an arm's FROZEN set (the frozen set is never changed: every
    child B copies it), e.g. after a child-B-side fix; the row keeps the earlier child B under `b_earlier`."""
    path = Path(args.row)
    row = json.loads(path.read_text(encoding="utf-8"))
    ctx = ctx_of(argparse.Namespace(build_root=args.build_root, out=str(path.parents[1])))
    earlier = {key: row.pop(key) for key in ("child_b", "b", "b_memory", "b_run", "grade") if key in row}
    row.setdefault("b_earlier", []).append(earlier)
    run_child_b(ctx, row, Path(row["frozen"]["dir"]), suffix=args.suffix)
    row["grade"] = grade(row)
    path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    g = row["grade"]
    print("LIVE ARM " + json.dumps({"arm": row["arm"], "seed": row["seed"], "b": args.suffix,
                                    "file": (row.get("file") or {}).get("verdict"), "counted": g.get("counted"),
                                    "pass": g.get("pass"), "checks": g.get("checks"),
                                    "b_reason": ((row.get("b") or {}).get("play") or {}).get("reason")}, ensure_ascii=False))
    return 0


def cmd_grade(args) -> int:
    for path in args.rows:
        row = json.loads(Path(path).read_text(encoding="utf-8"))
        grader = grade_control if row["arm"] == "CONTROL" else grade_launch if row["arm"].startswith("LAUNCH") else grade
        row["grade"] = grader(row)
        print("GRADE " + json.dumps({"arm": row["arm"], "seed": row["seed"], **row["grade"]}, ensure_ascii=False))
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("control", "arm"):
        p = sub.add_parser(name)
        p.add_argument("--seed", type=int, required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--frames", type=int, default=FRAMES_A)
        p.add_argument("--build-root")
        if name == "arm":
            p.add_argument("--arm", required=True, choices=sorted(KILLS))
            p.add_argument("--between-from")
            p.add_argument("--between-rule", choices=("midpoint", "new"), default=BETWEEN_RULE)
            p.add_argument("--tag", help="(development) the row's name instead of the arm's (a variant of an arm)")
    p = sub.add_parser("old")
    p.add_argument("--twin-row", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--build-root")
    p = sub.add_parser("launch")
    p.add_argument("--from-row", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--old", action="store_true")
    p.add_argument("--build-root")
    p = sub.add_parser("verdict")
    p.add_argument("--out", required=True)
    p.add_argument("--first", type=int, default=HELD_OUT[0])
    p.add_argument("--last", type=int, default=HELD_OUT[1])
    p = sub.add_parser("ledger")
    p.add_argument("action", choices=("numbers", "register", "begin", "finish"))
    p.add_argument("--purpose", default="graded", choices=("graded", "development", "replay"))
    p.add_argument("--first", type=int)
    p.add_argument("--last", type=int)
    p.add_argument("--note-file")
    p.add_argument("--id", type=int)
    p.add_argument("--verdict-file")
    p.add_argument("--evidence")
    p = sub.add_parser("selftest")
    p.add_argument("--rows", nargs="+", required=True, help="folders of recorded rows (step 6's and step 7's rehearsals)")
    p.add_argument("--fault", choices=sorted(FAULTS))
    p.add_argument("--all", action="store_true", help="the clean run, then each planted fault")
    p = sub.add_parser("grade")
    p.add_argument("rows", nargs="+")
    p = sub.add_parser("measure")
    p.add_argument("--out", required=True)
    p = sub.add_parser("b-again")
    p.add_argument("--row", required=True)
    p.add_argument("--suffix", required=True)
    p.add_argument("--build-root")
    p = sub.add_parser("child-a")
    for flag in ("--profile-dir", "--memory", "--kill", "--record", "--run-dir", "--play-json"):
        p.add_argument(flag, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--frames", type=int, required=True)
    p = sub.add_parser("child-b")
    for flag in ("--profile-dir", "--run-dir", "--play-json"):
        p.add_argument(flag, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--frames", type=int, default=0)
    args = parser.parse_args()
    if args.cmd == "child-a":
        return child_a(args)
    if args.cmd == "child-b":
        return child_b(args)
    if args.cmd == "control":
        return cmd_control(args)
    if args.cmd == "arm":
        return cmd_arm(args)
    if args.cmd == "old":
        return cmd_old(args)
    if args.cmd == "launch":
        return cmd_launch(args)
    if args.cmd == "verdict":
        return cmd_verdict(args)
    if args.cmd == "ledger":
        return cmd_ledger(args)
    if args.cmd == "selftest":
        return cmd_selftest(args)
    if args.cmd == "measure":
        return cmd_measure(args)
    if args.cmd == "b-again":
        return cmd_b_again(args)
    return cmd_grade(args)


if __name__ == "__main__":
    sys.exit(main())
