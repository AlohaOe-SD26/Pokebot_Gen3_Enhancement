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

THE R1 + R2 FOLLOW-UP'S ARMS (its spec, `s53/r1f/SPEC.md` section 5, with the orchestrator's rulings 1-3 of 2026-10-29):
  * CHAIN (N-3): on a COPY of K-SILENT's frozen set (the cart holds S1 while S2's line, the abandoned branch, is the NEWEST
    save line of the memory file), a child B of the REAL tree continues S1 and plays on, with a `SaveWatch` of its own
    (its memory tail starts at the frozen file's size, and a save line attaches only with an id of at least the frozen
    file's `next_save_id`: the frozen S1 and S2 lines are never taken for B's save). It is killed by rule `N1+30`
    (orchestrator ruling 11, 2026-10-29: the rule counts from B's LATEST completed save, not only its first): 30 frames
    after the first frame on which it stands on a map NEW to its latest completed save S_k (in neither the K-SILENT child
    A's maps up to S1.e3 nor its own maps from its held free arrival to S_k's e3), with no START pressed since S_k's e4.
    Each save B completes before such a map RE-ANCHORS the rule on itself. WHY: the AI's own unchanged play heals at
    OLDALE and saves again before it walks anywhere new, and the first-save-only rule met that on 2 of 6 development
    seeds (a target must come from the state the run REACHED, CLAUDE.md rule 4). Child C (REAL tree) then continues B's
    frozen set, i.e. S_k. Graded by `grade_chain` (checks C1-C6, ruling 12), with rule N re-derived from B's record
    (`replay_rule_n`): B's FIRST post-continue save line is read BY ID from B's frozen memory file with this module's OWN
    reader (`rebuild_payload`, no `ai_player` import), its parent must be S1's id (B's `continued_from`), never S2's, and
    every later B line must chain to the B line before it.
  * CHAIN-OLD (mutant CH1, `CH1_EDITS`: a continued writer chains to the NEWEST save line) and CHAIN-R1-OLD (mutant FX1:
    a save line's `goals` built from the state BEFORE the save), each child B killed at its own first save's e4 + 40.
  * R2-RETRY (R-2): the REAL launcher continues K-AFTER's frozen copy from a COPY whose only edit is the arrival bound
    (`R2_STOP_EDITS`), so the continue STOPS on that bound; the next continue (`child_b`, the REAL tree) must be allowed,
    looking through the stopped one, and arrive at S2. R2-RETRY-OLD runs that next continue on mutant FX3 (no
    look-through): refused, class CHOSEN, the memory file byte-identical.
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
#: the held-out graded seeds (the R1 + R2 follow-up's spec section 5.6: #58), registered BEFORE any of them runs
HELD_OUT = (5551, 5554)
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
ARMS_NEW = ("CONTROL", "K-AFTER", "K-INSIDE", "K-SILENT", "K-FIRST", "K-BETWEEN", "LAUNCH", "CHAIN", "R2-RETRY")
OLD_OF = {"K-INSIDE-OLD": "K-INSIDE", "K-SILENT-OLD": "K-SILENT", "LAUNCH-OLD": "LAUNCH", "CHAIN-OLD": "CHAIN",
          "CHAIN-R1-OLD": "CHAIN", "R2-RETRY-OLD": "R2-RETRY"}
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
# ------------------------------------------------------------------ the R1 + R2 follow-up's arms (CHAIN, R2-RETRY)
#: (spec D11; orchestrator ruling 2) CHAIN-OLD's mutant CH1: a continued writer chains its first save to the NEWEST save
#: line (on K-SILENT's set the abandoned S2), with the rebuild of its base (the next line) following that parent. The same
#: edit as revert_r1's CH1 (the selftest checks it).
CH1_EDITS = (("game_memory.py",
              "        self.parent: int | None = continued if book is not None and isinstance(continued, int) else None\n",
              "        self.parent: int | None = book.newest_save()['id'] if book is not None and isinstance(continued, int) "
              "else None  # MUTANT CH1\n"),)
#: CHAIN-R1-OLD's mutant: revert_r1's FX1 (a save line's goals built from the policy's state BEFORE the save), edit for edit
FX1_EDITS = (("mode.py", "        goals = goals_part(replace(manager.memory, **saving))\n",
              "        goals = goals_part(manager.memory)  # MUTANT FX1\n"),)
#: R2-RETRY-OLD's mutant: revert_r1's FX3 (the launcher never looks through a continue that stopped before its restore)
FX3_EDITS = (("host/launcher.py",
              "        if kind != \"CHOSEN\" or earlier is None or not _stopped_before_restore(book, session, reason):\n",
              "        if True:  # MUTANT FX3\n"),)
#: (spec D8) rule N's frame offset: the kill is this many frames after the rule is met (a fixed offset, not a budget)
N_KILL_FRAMES = 30
#: the frame budgets' base: `skills/saving.py` CONTINUE_BUDGET 1700 + ARRIVAL_BUDGET 320 (the selftest checks the sum)
CHAIN_BUDGET_BASE = 2020
#: (spec section 5.5; orchestrator rulings 5 and 13) CHAIN's child B frames and wall time, SET at 2x the widest measured
#: in development #57 step 5 (b) re-run under ruling 11 (s53/r1f/build/s2b-live-dev/measure-chain.out; measuring caps
#: 120,000 frames and 1,800 s, never reached): arrival -> kill 33,964-63,812 frames on all six seeds (5505 widest, anchored
#: on B's save 2), child B wall 61.9-105.4 s, so frames = 2020 + 2 x 63,812 and the timeout = max(300, 2 x 105.4) = 300 s
CHAIN_B_FRAMES = CHAIN_BUDGET_BASE + 2 * 63812
CHAIN_B_TIMEOUT = 300
#: (spec section 5.5; orchestrator rulings 5 and 13) the OLD B arms' frames and wall time (killed at their own first save's
#: e4 + 40), SET at 2x the widest measured in development #57 step 5 (c) (s53/r1f/build/s2-live-dev/measure-chain.out):
#: arrival -> kill 15,755-45,363 frames over all 12 OLD child Bs (both OLD arms, 5501-5506), wall 39.5-105.4 s, so
#: frames = 2020 + 2 x 45,363 and the timeout = max(300, 2 x 105.4) = 300 s
CHAIN_OLD_FRAMES = CHAIN_BUDGET_BASE + 2 * 45363
CHAIN_OLD_TIMEOUT = 300
#: the OLD B arms' kill: child B's OWN first save's e4 + 40 (orchestrator ruling 3)
CHAIN_OLD_KILL = "S1.e4+40"
#: (spec D9, section 5.5) R2-RETRY step 1's arrival bound in its COPY: floor(the narrowest arrival measured in development /
#: 2). SET by development #57 step 5 (a) (s53/r1f/build/s2-live-dev/measure-arrivals.out): the CONTINUE press to the held
#: free arrival was 115 frames (K-INSIDE, K-SILENT child Bs, all six seeds), 146 (K-AFTER child Bs) and 162-191 (LAUNCH,
#: the AI's own log, its think pause included); floor(115 / 2) = 57
R2_STOP_ARRIVAL: int | None = 57
#: the R2-STOP copy's ONE edit (`skills/saving.py` ARRIVAL_BUDGET)
R2_STOP_EDITS = (("skills/saving.py", "ARRIVAL_BUDGET = 320\n",
                  f"ARRIVAL_BUDGET = {R2_STOP_ARRIVAL}  # R2-STOP COPY (live_r1.py R2-RETRY step 1)\n"),)
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
    "caveat_passes_ignored": "the verdict line's caveat counts the midpoint arm's seeds but ignores whether they PASSED",
    "chain_parent_ignored": "CHAIN's check C3 skips the save line's parent (read as B's continued_from)",
    "chain_last_save_ignored": "CHAIN's check C3 skips the rebuilt goals.last_save (read as the line's own id and stamp)",
    "pre_maps_ignored": "CHAIN's check C6 skips NEW_B_pre (the maps B stood on before its save)",
    "stale_line_attached": "child B's memory tail starts at 0 and attaches any save line (the frozen S2 line graded as B's)",
    "lookthrough_ignored": "R2-RETRY's check R1 skips the look-through's words (the count and the stopped continue's reason)",
    "n_rule_first_save": "CHAIN's grader re-derives rule N from B's FIRST save only, never re-anchoring on a later save (the "
                         "rule before orchestrator ruling 11)",
}
#: (selftest) the follow-up's recorded DEVELOPMENT rows (#57, seeds 5501-5506: s53/r1f/build/s2-live-dev/dev/rows, and
#: CHAIN re-run under orchestrator ruling 11 in s53/r1f/build/s2b-live-dev/dev/rows) the selftest grades: CHAIN counted
#: and passing (anchored on B's first save, and RE-ANCHORED on a later one), the OLD arms showing, R2-RETRY and its OLD arm
SELFTEST_ROWS = {"chain_pass": ("CHAIN-5502", "CHAIN-5504", "CHAIN-5501", "CHAIN-5503", "CHAIN-5505", "CHAIN-5506"),
                 "chain_reanchored": ("CHAIN-5501", "CHAIN-5503", "CHAIN-5505", "CHAIN-5506"),
                 "chain_old": ("CHAIN-OLD-5502", "CHAIN-R1-OLD-5502", "CHAIN-OLD-5504", "CHAIN-R1-OLD-5504"),
                 "r2_pass": ("R2-RETRY-5501", "R2-RETRY-5502"), "r2_old": ("R2-RETRY-OLD-5501", "R2-RETRY-OLD-5502")}


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
    """A kill rule: `F<frame>`, `S<save>.<event>+<frames>`, or (R1 + R2 follow-up, spec D8 as amended by orchestrator
    ruling 11) `N<save>+<frames>`: the first frame after the LATEST completed save's e4 (save k or a later one) on a map
    NEW to that save, with no START since that e4, then `frames` more."""
    if not spec or spec == "none":
        return None
    if spec.startswith("F"):
        return ("F", int(spec[1:]))
    if spec.startswith("N"):
        # (orchestrator ruling 11) save k is where rule N STARTS: it re-anchors on each later completed save (`_rule_n`)
        save, _, offset = spec[1:].partition("+")
        if not save.isdigit() or not offset.isdigit():
            raise ValueError(f"bad kill {spec!r}")
        return ("N", int(save), int(offset))
    head, _, offset = spec.partition("+")
    save, _, event = head.partition(".")
    if not save.startswith("S") or event not in ("e1", "e3", "e4", "e7"):
        raise ValueError(f"bad kill {spec!r}")
    return ("S", int(save[1:]), event, int(offset or 0))


def chain_tail_start(frozen_size: int) -> int:
    """(spec part (j), code-host F4) Where a continued child's memory tail starts: the frozen file's size, so the frozen
    set's own lines (child A's S1 and S2) are never read as this child's."""
    return 0 if FAULT == "stale_line_attached" else int(frozen_size)


def attaches(line: dict, min_id: int) -> bool:
    """(code-host F4, the second guard) A save line attaches to a save of THIS child only with an id of at least the frozen
    file's `next_save_id`."""
    return FAULT == "stale_line_attached" or (isinstance(line.get("id"), int) and line["id"] >= min_id)


def tail_attach(path: Path, frozen_size: int, min_id: int) -> list[dict]:
    """The save lines a continued child's watcher attaches, reading `path` as its tail does (`chain_tail_start`,
    `attaches`): the selftest replays a recorded file through it."""
    tail = MemoryTail(path, chain_tail_start(frozen_size))
    return [line for line in tail.poll(0) if line.get("kind") == "save" and attaches(line, min_id)]


class MemoryTail:
    """The memory file's lines as they reach it (test side: a read of the file, never the AI's objects). `start` (R1 + R2
    follow-up, code-host F4): the byte offset it starts at (a continued child: the frozen file's size)."""

    def __init__(self, path: Path, start: int = 0) -> None:
        self.path, self.size, self.buffer, self.lines = path, int(start), b"", []

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
    """Child A's per-frame watcher (module docstring). (R1 + R2 follow-up) Also a CONTINUED child B's (CHAIN and its OLD
    arms): `tail_start` and `min_line_id` keep the frozen set's lines off B's saves (code-host F4); `arrival` (the child's
    `ArrivalWatch`) gates the maps rule N counts to those from the held free arrival on (a continued game's RAM location
    before the load is not a map it stood on); `known` is the `--known-maps` set; `extra` joins the READY payload (the
    child's launcher check, its tree's file hashes, and the ArrivalWatch's record, since a killed child prints no RESULT)."""

    def __init__(self, context, controls, memory: Path, kill: str | None, record: Path, tail_start: int = 0,
                 min_line_id: int = 0, arrival=None, known: set | None = None, extra: dict | None = None) -> None:
        self.arrival_watch, self.known_file = arrival, set(known or ())
        self.extra = extra
        self.min_line_id = min_line_id
        self.stale_lines: list[dict] = []
        self.arrived: int | None = None
        self.maps_pre_arrival: list[list] = []
        self.maps_from_arrival: list[list] = []
        self.n_rule: dict | None = None
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
        self.memory = MemoryTail(memory, tail_start)
        self.memory_start = tail_start
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
            if self.arrival_watch is not None:
                (self.maps_from_arrival if self.arrived is not None else self.maps_pre_arrival).append([f, key])
        # (a continued child) the maps from the HELD free arrival on: the map at the arrival frame, then every change
        if self.arrival_watch is not None and self.arrived is None and self.arrival_watch.arrival is not None:
            self.arrived = self.arrival_watch.arrival["f"]
            at = [entry for entry in self.maps if entry[0] <= self.arrived]
            later = [entry for entry in self.maps if entry[0] > self.arrived]
            self.maps_pre_arrival = [entry for entry in self.maps_pre_arrival if entry[0] < self.arrived]
            self.maps_from_arrival = ([[self.arrived, at[-1][1]]] if at else []) + later
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
            if line.get("kind") == "save" and not attaches(line, self.min_line_id):
                self.stale_lines.append(line)  # (code-host F4) a frozen line: never this child's save
                continue
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
        elif kill[0] == "N":
            reached = self._rule_n(f, kill)
        else:
            _, index, event, offset = kill
            save = self.saves[index - 1] if len(self.saves) >= index else None
            reached = save is not None and event in save and save[event] is not None and f - save[event] >= offset
        if not reached:
            return
        # the save the kill is measured from: save k for `S`; for `N` the rule's ANCHOR (B's latest completed save when the
        # rule was met, orchestrator ruling 11). `first` is save k itself (the OLD arms' and CHAIN's first post-continue
        # save), whose e3 the determinism line's presses digest is taken to
        first = self.saves[kill[1] - 1] if kill[0] in ("S", "N") and len(self.saves) >= kill[1] else None
        cur = self.saves[self.n_rule["anchor"] - 1] if kill[0] == "N" else first
        if self.arrival_watch is not None:
            payload = {**(self.extra or {}), **self.arrival_watch.result(), "save_watch": self.result()}
        else:
            payload = self.result()
        payload["kill"] = {"spec": self.kill_spec, "frame": f,
                           "new_sectors_at_kill": None if cur is None or "e4" in cur else cur["new_now"],
                           "write_complete_at_kill": None if cur is None else "e4" in cur,
                           "presses_digest": presses_digest(self.controls.log, f),
                           "status_at_kill": self.parse["status"]}
        if first is not None and first.get("e3") is not None:
            # (CHAIN's OLD arms' determinism line) the presses up to this child's FIRST save's e3
            payload["kill"]["presses_digest_e3"] = presses_digest(self.controls.log, first["e3"])
        if cur is not None and cur.get("e4") is not None:
            payload["kill"]["starts_since_e4"] = sum(1 for s in self.starts if s["f"] is not None and s["f"] > cur["e4"])
        if self.n_rule is not None:
            payload["kill"].update({k: self.n_rule.get(k) for k in ("entered", "new_map", "known_size", "anchor",
                                                                    "anchor_e3", "anchor_e4", "anchors")})
            if cur is not None and cur.get("e3") is not None:
                payload["kill"]["presses_digest_anchor_e3"] = presses_digest(self.controls.log, cur["e3"])
        self.record.flush()
        print("READY " + json.dumps(payload, ensure_ascii=False), flush=True)
        for _ in range(int(BLOCK_SECONDS / 0.25)):
            time.sleep(0.25)
        print("NOT KILLED: the parent never killed this child; it ends itself (exit 5)", flush=True)
        os._exit(5)

    def _rule_n(self, f: int, kill: tuple) -> bool:
        """(spec D8 as amended by orchestrator ruling 11, rule `N<k>+<frames>`) The rule's ANCHOR is the LATEST save, from
        save k on, whose e4 this watcher saw. Met at the first frame after the anchor's e4 on which the player stands
        (RAM) on a map not in `known` (the `--known-maps` set plus every map this watcher recorded from the held free
        arrival up to the ANCHOR's e3), with no START pressed since the anchor's e4; reached `frames` frames later.
        Until such a map is entered, every save that completes RE-ANCHORS the rule on itself. A START pressed since the
        anchor's e4 BLOCKS that anchor (recorded in `blocked`: a write may be under way, so no kill measures from it);
        the rule then waits for the next completed save. Every anchor is recorded in `anchors`. The grader re-derives
        all of this from the record (`replay_rule_n`) and requires the same anchor, map and frame."""
        _, index, offset = kill
        done = [s for s in self.saves[index - 1:] if s.get("e4") is not None]
        if not done or self.arrived is None:
            return False
        rule = self.n_rule
        if rule is None or (rule["entered"] is None and rule["anchor"] != done[-1]["save"]):
            save = done[-1]
            mine = sorted({key for frame, key in self.maps_from_arrival if frame <= save["e3"]})
            anchors = list((rule or {}).get("anchors") or []) + [{"save": save["save"], "e3": save["e3"],
                                                                  "e4": save["e4"], "at": f}]
            rule = self.n_rule = {"anchor": save["save"], "anchor_e3": save["e3"], "anchor_e4": save["e4"],
                                  "known": sorted(self.known_file | set(mine)), "b_pre": mine, "entered": None,
                                  "new_map": None, "blocked": None, "anchors": anchors}
            rule["known_size"] = len(rule["known"])
        if rule["entered"] is None:
            started = [s["f"] for s in self.starts if s["f"] is not None and s["f"] > rule["anchor_e4"]]
            if started:
                if rule["blocked"] is None:
                    rule["blocked"] = {"start_at": started[0], "at": f}
                    rule["anchors"][-1]["blocked"] = rule["blocked"]
                return False
            key = map_now(self.emulator)
            if key is None or key in rule["known"]:
                return False
            rule.update(entered=f, new_map=key, const=map_const(key))
            rule["anchors"][-1].update(entered=f, new_map=key)
        return f - rule["entered"] >= offset

    def result(self) -> dict:
        saves = []
        for save in self.saves:
            item = {k: v for k, v in save.items() if k != "start"}
            item["start"] = save.get("start")
            if save.get("sectors"):
                item["first_sector"] = min(save["sectors"].values())
            saves.append(item)
        out = {"saves": saves, "truths": {f"S{s['save']}": s["truth"] for s in self.saves},
               "maps": self.maps, "starts": self.starts, "proof_first": self.proof_first,
               "memory_lines": self.memory.lines, "flash_reads": self.flash_reads, "frames": self.frames,
               "at_start": self.at_start}
        if self.arrival_watch is not None:
            out.update({"arrived": self.arrived, "maps_pre_arrival": self.maps_pre_arrival,
                        "maps_from_arrival": self.maps_from_arrival, "stale_lines": self.stale_lines,
                        "min_line_id": self.min_line_id, "tail_start": self.memory_start, "n_rule": self.n_rule,
                        "known_file": sorted(self.known_file)})
        return out


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

    import ai_player.game_memory as memory_module
    import ai_player.host.launcher as launcher_module
    import ai_player.mode as mode_module

    profile = Path(args.profile_dir)
    game = AppPaths.for_profile(profile.name, profile.parent.parent, home="")
    # (R1 + R2 follow-up) the frozen memory file as it is before anything of this child: its size (the SaveWatch tail's
    # start) and its next save id (the attach guard), read test side
    frozen_size = game.memory_jsonl.stat().st_size if game.memory_jsonl.exists() else 0
    frozen_next = next_save_id(memory_lines(game.memory_jsonl)) if game.memory_jsonl.exists() else 1
    memory_before = hashlib.sha256(game.memory_jsonl.read_bytes()).hexdigest() if game.memory_jsonl.exists() else None
    check = memory_check(game)

    def sha(module) -> dict:
        return {"file": str(Path(module.__file__).resolve()),
                "sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()[:16]}

    out = {"memory_check": {"ok": check.ok, "why": check.why, "end_class": check.end_class, "undone": check.undone,
                            "newest": (check.newest or {}).get("id"),
                            "looked_through": getattr(check, "looked_through", None)},
           # WHICH continue skill this child ran (an OLD arm's mutant copy, or the tree under test): its file and sha256
           "skills_saving": sha(saving_skill),
           # (R1 + R2 follow-up) the launcher, the memory module and the play loop this child imported (an OLD arm's mutant)
           "launcher_sha": sha(launcher_module), "memory_sha": sha(memory_module), "mode_sha": sha(mode_module),
           "frozen_memory": {"size": frozen_size, "next_save_id": frozen_next, "sha256_before": memory_before}}
    if not check.ok:
        out["refused"] = check.why
        out["frozen_memory"]["sha256_after_check"] = hashlib.sha256(game.memory_jsonl.read_bytes()).hexdigest() \
            if game.memory_jsonl.exists() else None
        print("RESULT " + json.dumps(out, ensure_ascii=False), flush=True)
        return 0
    out["seed_profile"] = seed_profile(profile, None, False, continue_game=True, game=game)
    out["ss1_at_boot"] = (profile / "current_state.ss1").exists()
    personality, starter = plan_of(args.seed)
    watchers: list = []
    known = set(json.loads(Path(args.known_maps).read_text(encoding="utf-8"))) if args.known_maps else set()

    def watch(controls):
        from modules.context import context

        watcher = ArrivalWatch(context, controls)
        watchers.append(watcher)
        if not args.kill:
            return [watcher]
        # (CHAIN, CHAIN-OLD, CHAIN-R1-OLD) this child's own saves and its kill, after the arrival watcher each frame
        saves = SaveWatch(context, controls, game.memory_jsonl, args.kill, Path(args.record),
                          tail_start=chain_tail_start(frozen_size), min_line_id=frozen_next, arrival=watcher,
                          known=known, extra=out)
        watchers.append(saves)
        return [watcher, saves]

    if args.kill and not (args.record and args.maps_from_arrival):
        raise SystemExit("child-b --kill needs --record and --maps-from-arrival (rule N counts maps from the arrival on)")
    frames = args.frames or CONTINUE_BUDGET + ARRIVAL_BUDGET + 600
    result = play_harness.run(None, args.seed, frames, personality, starter, TARGET, set(), GAME_CLOCK, WALL_CLOCK,
                              None, Path(args.run_dir), None, 30, profile_dir=profile, memory=game.memory_jsonl,
                              continue_game=True, watch=watch)
    Path(args.play_json).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    out.update(watchers[0].result() if watchers else {})
    if len(watchers) > 1:
        out["save_watch"] = watchers[1].result()  # the kill rule was never reached: the child ran to its own end
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
    run = run_continue_child(ctx, row, frozen, suffix, root)
    row["child_b"], row["b"], row["b_memory"], row["b_run"] = run["child"], run["result"], run["memory"], run["run_dir"]


def run_continue_child(ctx: dict, row: dict, frozen: Path, suffix: str, root: Path = REPO, extra: list | None = None,
                       timeout: float = CHILD_B_TIMEOUT, killable: bool = False) -> dict:
    """A continuing child (`child-b`) on its OWN copy of `frozen` (never changed: every child copies it). `extra`: more
    `child-b` flags (CHAIN's `--kill`, `--record`, `--known-maps`, `--maps-from-arrival`, `--frames`); `killable`: the
    child may print READY at its kill point, and is then killed by ITS PID. Returns the child's record, its RESULT (or
    READY) payload, its memory file's lines (without payloads), its run folder, profile and game folder."""
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
           "--run-dir", str(folder / f"{suffix}_run"), "--play-json", str(folder / f"{suffix}_play.json")] + list(extra or [])
    began = time.monotonic()
    b = Child(cmd, ctx["env"], root, folder / f"child_{suffix}.out", row["arm"], f"child {suffix.upper()}")
    word, result = b.wait_for(("READY", "RESULT", "ABORT") if killable else ("RESULT", "ABORT"), timeout)
    child = {"pid": b.pid, "word": word, "seconds": round(time.monotonic() - began, 1), "cmd_tail": list(extra or [])}
    if word == "READY":
        child["kill"] = b.kill()
        child["exit"] = child["kill"]["exit_code"]
    else:
        child["exit"] = b.finish(120)
    child["alive_after"] = b.proc.poll() is None
    memory = memory_lines(game.memory_jsonl) if game.memory_jsonl.exists() else []
    return {"child": child, "result": result, "memory": [{k: v for k, v in line.items() if k != "memory"} for line in memory],
            "run_dir": str(folder / f"{suffix}_run"), "profile": str(profile), "game_dir": str(game.game_dir),
            "memory_sha256_after": hashlib.sha256(game.memory_jsonl.read_bytes()).hexdigest()
            if game.memory_jsonl.exists() else None}


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


# ------------------------------------------------------------------ the TEST-SIDE memory reader (R1 + R2 follow-up)
# A port of the verification's `r1_live.py` (s53/r1build/build/verify2-rerun, fault-tested there: 0 of 93 save lines on
# #53's pre-fix files, 94 of 94 on #55's). It imports NOTHING from `ai_player`: the grade of B's save line must not rest on
# the code it grades (`game_memory.read_book` / `MemoryBook.rebuild`). Stricter than that port: every deletion must find
# its key, and a path must go through objects only (the writer's own `apply_delta` rule), so a wrong base fails loudly.
def memory_lines(path: Path) -> list[dict]:
    """Every line of a memory file, parsed (test side). An unparsable LAST line (a kill's cut) is left out; an unparsable
    line anywhere else raises ValueError."""
    raw = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").split("\n")]
    out = []
    for index, text in enumerate(raw):
        if not text.strip():
            continue
        try:
            out.append(json.loads(text))
        except ValueError:
            if index < len(raw) - 1 and any(rest.strip() for rest in raw[index + 1:]):
                raise
    return out


def next_save_id(lines: list[dict]) -> int:
    """1 + the largest save line id (1 for none): the id the next save of a continue gets."""
    return 1 + max((line["id"] for line in lines if line.get("kind") == "save" and isinstance(line.get("id"), int)),
                   default=0)


def _delta_apply(parent: dict, delta: dict) -> dict:
    if not isinstance(delta, dict) or set(delta) - {"set", "del"} or not isinstance(delta.get("set", []), list) \
            or not isinstance(delta.get("del", []), list):
        raise ValueError(f"not a delta: keys {sorted(delta) if isinstance(delta, dict) else type(delta).__name__}")
    child = json.loads(json.dumps(parent))
    for path in delta.get("del") or []:
        if not isinstance(path, list) or not path:
            raise ValueError(f"a del op that is not a path: {path!r:.120}")
        node = child
        for key in path[:-1]:
            node = node.get(key) if isinstance(node, dict) else None
        if not isinstance(node, dict) or path[-1] not in node:
            raise ValueError(f"a del of {path} its base does not hold")
        del node[path[-1]]
    for op in delta.get("set") or []:
        if not (isinstance(op, list) and len(op) == 2 and isinstance(op[0], list) and op[0]):
            raise ValueError(f"a set op that is not [path, value]: {op!r:.120}")
        node = child
        for key in op[0][:-1]:
            node = node.get(key) if isinstance(node, dict) else None
        if not isinstance(node, dict):
            raise ValueError(f"a set at {op[0]} goes through a value that is not an object")
        node[op[0][-1]] = json.loads(json.dumps(op[1]))
    return child


def rebuild_payload(lines: list[dict], save_id: int) -> tuple[dict | None, str | None, list[int]]:
    """(spec part (j)) Save `save_id`'s payload, rebuilt test side: its line found BY ID, then its chain followed by
    `parent` to a full line, each delta applied in order. Returns (payload, None, chain ids newest first) or (None, why,
    the chain so far)."""
    saves = {line["id"]: line for line in lines if line.get("kind") == "save" and isinstance(line.get("id"), int)}
    chain: list[int] = []
    line = saves.get(save_id)
    if line is None:
        return None, f"no save line with id {save_id}", chain
    for _ in range(len(saves) + 1):
        chain.append(line["id"])
        if line.get("full"):
            break
        parent = line.get("parent")
        if parent not in saves:
            return None, f"save {line['id']}'s parent {parent!r} has no line", chain
        line = saves[parent]
    else:
        return None, f"save {save_id}'s chain loops", chain
    try:
        payload = json.loads(json.dumps(saves[chain[-1]]["memory"]))
        for sid in reversed(chain[:-1]):
            payload = _delta_apply(payload, saves[sid]["memory"])
    except (ValueError, KeyError, TypeError) as error:
        return None, f"a delta failed: {error}", chain
    return payload, None, chain


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


# ------------------------------------------------------------------ the R1 + R2 follow-up's arms: CHAIN and R2-RETRY
def freeze_profile(ctx: dict, label: str, profile: Path, game_dir: Path) -> dict:
    """A continued child's cart, memory and launches as its kill (or its end) left them (G6, F12: before any later child)."""
    frozen = ctx["out"] / "frozen" / label
    frozen.mkdir(parents=True)
    copied = {}
    for source in (profile / "current_save.sav", game_dir / "memory.jsonl", game_dir / "launches.jsonl"):
        if source.exists():
            shutil.copy2(source, frozen / source.name)
            copied[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    return {"dir": str(frozen), "files": copied, "ss1": sorted(p.name for p in profile.glob("*.ss1"))}


def continue_facts(b: dict) -> dict:
    """A continuing child's main-menu record, as `grade`'s check 4 reads it: CONTINUE pressed, no NEW GAME, no page."""
    presses = b.get("presses") or []
    on_menu = [p for p in presses if p[2] and p[2][0] == "Task_HandleMainMenuInput"]
    new_game = [p for p in on_menu if p[1] == "A" and (p[2][2] != 0 or (p[2][1] or 0) < 1)] + \
        [["task", t] for t in b.get("new_game_tasks") or []]
    return {"continue_pressed": any(p[1] == "A" and p[2][2] == 0 and (p[2][1] or 0) >= 1 for p in on_menu),
            "no_new_game": not new_game, "no_page": not b.get("pages")}


def same_identity(arrival: dict, boot: dict | None, truth: dict) -> dict:
    """The arrival (PIDs, map, tile) and the boot read's play time against a save's RAM truth, key by key."""
    same = {k: (arrival or {}).get(k) == truth.get(k) for k in ("pids", "map", "pos")}
    same["play_time_at_boot"] = (boot or {}).get("play_time") == truth.get("play_time")
    return same


def mutant_ran(row: dict, child: dict) -> bool:
    """An OLD arm's child imported its mutant copy: the mutated file's sha256 (the child's own record) is the copy's."""
    mutant = row.get("mutant") or {}
    key = {"CHAIN-OLD": ("memory_sha", "game_memory.py"), "CHAIN-R1-OLD": ("mode_sha", "mode.py"),
           "R2-RETRY-OLD": ("launcher_sha", "host/launcher.py")}.get(row.get("arm"))
    if key is None or not mutant.get("sha256"):
        return False
    ran = ((child or {}).get(key[0]) or {}).get("sha256")
    return ran is not None and ran == mutant["sha256"].get(key[1])


def cmd_chain(args) -> int:
    """CHAIN, CHAIN-OLD, CHAIN-R1-OLD (the follow-up spec section 5.1; orchestrator rulings 1-3): on a COPY of K-SILENT's
    frozen set, child B (the REAL tree, or the OLD arm's mutant copy) continues S1 with its own SaveWatch; CHAIN kills it
    by rule `N1+N_KILL_FRAMES` (re-anchored on B's latest completed save, ruling 11), the OLD arms at its own first save's
    e4 + 40; CHAIN's child C (the REAL tree) then continues B's frozen set (B's latest save S_k)."""
    ctx = ctx_of(args)
    source = Path(args.from_row)
    ks = json.loads(source.read_text(encoding="utf-8"))
    if ks.get("arm") != "K-SILENT":
        raise SystemExit("CHAIN runs on K-SILENT's row (orchestrator ruling 1)")
    name = args.old or "CHAIN"
    seed = ks["seed"]
    a = ks.get("a") or {}
    saves = a.get("saves") or []
    row: dict = {"arm": name, "name": name, "seed": seed, "ks_row": str(source), "ks": ks, "started": now()}
    if (ks.get("child_a") or {}).get("word") != "READY" or not ks.get("frozen") or len(saves) < 2:
        row["result"] = "NOT RUN: K-SILENT's child A did not reach its kill"
    else:
        frozen = Path(ks["frozen"]["dir"])
        lines = memory_lines(frozen / "memory.jsonl")
        # (orchestrator ruling 3) the known set: the K-SILENT child A's maps up to S1.e3
        known = sorted({key for frame, key in a.get("maps") or [] if frame <= saves[0]["e3"]})
        edits = {"CHAIN-OLD": CH1_EDITS, "CHAIN-R1-OLD": FX1_EDITS}.get(name)
        root = REPO
        if edits:
            root, row["mutant"] = mutant_tree(ctx["out"], f"{name}-{seed}", edits)
        kill = CHAIN_OLD_KILL if edits else f"N1+{N_KILL_FRAMES}"
        frames = CHAIN_OLD_FRAMES if edits else CHAIN_B_FRAMES
        timeout = CHAIN_OLD_TIMEOUT if edits else CHAIN_B_TIMEOUT
        folder = ctx["out"] / "runs" / f"{name}-{seed}"
        folder.mkdir(parents=True, exist_ok=True)
        known_file = folder / "known_maps.json"
        known_file.write_text(json.dumps(known), encoding="utf-8")
        row["chain"] = {"known_maps": known, "kill": kill, "frames": frames, "timeout": timeout,
                        "frozen_next_save_id": next_save_id(lines),
                        "frozen_memory_size": (frozen / "memory.jsonl").stat().st_size,
                        "frozen_save_ids": [line["id"] for line in lines if line.get("kind") == "save"],
                        "s1_id": (saves[0].get("line") or {}).get("id"), "s2_id": (saves[1].get("line") or {}).get("id")}
        run = run_continue_child(ctx, row, frozen, "b", root,
                                 ["--kill", kill, "--record", str(folder / "b_flash.jsonl"), "--known-maps", str(known_file),
                                  "--maps-from-arrival", "--frames", str(frames)], timeout, killable=True)
        row["child_b"], row["b"], row["b_memory"], row["b_run"] = run["child"], run["result"], run["memory"], run["run_dir"]
        if run["child"]["word"] == "READY":
            row["frozen_b"] = freeze_profile(ctx, f"{name}-B-{seed}", Path(run["profile"]), Path(run["game_dir"]))
            bsaves = ((row["b"] or {}).get("save_watch") or {}).get("saves") or []
            # (orchestrator ruling 12) the FILE against S1 and EACH of B's saves by its truth; the grader re-reads the cart
            row["file_b"] = chain_file(Path(row["frozen_b"]["dir"]) / "current_save.sav", (a.get("truths") or {}).get("S1"),
                                       bsaves)
            if name == "CHAIN":
                c = run_continue_child(ctx, row, Path(row["frozen_b"]["dir"]), "c", REPO)
                row["child_c"], row["c"], row["c_memory"], row["c_run"] = c["child"], c["result"], c["memory"], c["run_dir"]
        row["grade"] = grade_chain(row)
    row["ended"] = now()
    out = ctx["out"] / "rows" / f"{name}-{seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    g = row.get("grade") or {}
    print("LIVE ARM " + json.dumps({"arm": name, "seed": seed, "counted": g.get("counted"), "pass": g.get("pass"),
                                    "old_shows": g.get("old_shows"), "checks": g.get("checks"), "result": row.get("result"),
                                    "b_word": (row.get("child_b") or {}).get("word"),
                                    "kill": ((row.get("b") or {}).get("kill") or {}), "row": str(out)},
                                   ensure_ascii=False), flush=True)
    return 0


def chain_line(row: dict) -> dict:
    """(check C3, and the OLD arms' difference) Child B's save line, read BY ID (the frozen file's `next_save_id` before
    B) from B's FROZEN memory file by this module's own reader, its payload rebuilt through its chain."""
    chain = row.get("chain") or {}
    want = chain.get("frozen_next_save_id")
    frozen = (row.get("frozen_b") or {}).get("dir")
    path = Path(frozen) / "memory.jsonl" if frozen else None
    if path is None or not path.exists() or want is None:
        return {"exists": False, "why": "no frozen memory file of child B"}
    lines = memory_lines(path)
    line = next((x for x in lines if x.get("kind") == "save" and x.get("id") == want), None)
    if line is None:
        return {"exists": False, "id": want, "why": f"no save line with id {want} in B's frozen memory"}
    payload, error, ids = rebuild_payload(lines, want)
    last = ((payload or {}).get("goals") or {}).get("last_save") if payload is not None else None
    session = next((x for x in reversed(lines) if x.get("kind") == "session"), None)
    out = {"exists": True, "id": want, "parent": line.get("parent"), "full": line.get("full"),
           "play_time": line.get("play_time"), "frame": line.get("frame"), "why": line.get("why"),
           "rebuild_error": error, "chain": ids, "last_save": last,
           "continued_from": (session or {}).get("continued_from"),
           "restored_maps": (session or {}).get("restored_maps")}
    if FAULT == "chain_parent_ignored":
        out["parent"] = out["continued_from"]
    if FAULT == "chain_last_save_ignored":
        out["last_save"] = {"id": want, "play_time": line.get("play_time"), "frame": line.get("frame")}
    return out


def chain_lines(row: dict) -> dict:
    """(check C3's chain half and C5's target, orchestrator ruling 12) EVERY save line of child B's own in B's FROZEN memory
    file (an id of at least the frozen file's `next_save_id`), oldest first, each rebuilt by this module's own reader:
    its parent, its stamp, whether it rebuilds, and its rebuilt `goals.last_save`."""
    chain = row.get("chain") or {}
    want = chain.get("frozen_next_save_id")
    frozen = (row.get("frozen_b") or {}).get("dir")
    path = Path(frozen) / "memory.jsonl" if frozen else None
    if path is None or not path.exists() or want is None:
        return {"lines": [], "why": "no frozen memory file of child B"}
    lines = memory_lines(path)
    session = next((x for x in reversed(lines) if x.get("kind") == "session"), None)
    mine = sorted((x for x in lines if x.get("kind") == "save" and isinstance(x.get("id"), int) and x["id"] >= want),
                  key=lambda x: x["id"])
    out: list[dict] = []
    for line in mine:
        payload, error, ids = rebuild_payload(lines, line["id"])
        last = ((payload or {}).get("goals") or {}).get("last_save") if payload is not None else None
        item = {"id": line["id"], "parent": line.get("parent"), "play_time": line.get("play_time"),
                "rebuild_error": error, "chain": ids, "last_save": last}
        if FAULT == "chain_parent_ignored":
            item["parent"] = out[-1]["id"] if out else (session or {}).get("continued_from")
        if FAULT == "chain_last_save_ignored":
            item["last_save"] = {"id": line["id"], "play_time": line.get("play_time"), "frame": line.get("frame")}
        out.append(item)
    return {"lines": out, "first_id": want, "continued_from": (session or {}).get("continued_from"),
            "newest_save_id": next_save_id(lines) - 1}


def chain_file(cart: Path, s1_truth: dict | None, bsaves: list[dict]) -> dict:
    """(check C1, orchestrator ruling 12) B's frozen cart by the probe's own parser, identified by truth against S1 and
    against EACH of B's saves in turn (the probe names three saves at most, so each B save takes the "S3" place):
    `by_save` maps B's save (the watcher's index) to its verdict, "S3" meaning the cart holds that save."""
    image = parse_image(cart.read_bytes()) if cart.exists() else None
    by_save = {str(s["save"]): file_verdict(image, {"S1": s1_truth, "S3": s["truth"]}) for s in bsaves if s.get("truth")}
    return {"s1": file_verdict(image, {"S1": s1_truth}), "by_save": by_save, "cart": str(cart), "parse": brief(image)}


def replay_rule_n(sw: dict, known_file, spec: str | None) -> dict:
    """(orchestrator rulings 11-12) Rule N RE-DERIVED BY THE GRADER from child B's record, never from the watcher's state:
    B's saves (e3, e4), its maps from the held free arrival (each change with its frame) and its START presses. Each
    completed save from save k on is the anchor until the next one completes; it is MET at the first map change after its
    e4 (and before the next save's e4) onto a map in neither `known_file` nor B's maps up to its e3, when no START came
    after its e4 at or before that frame. Returns the first anchor met (its save, e3, e4, the map, the frame, the kill
    frame) or why none was. (FAULT n_rule_first_save: only the first save is tried, the rule before ruling 11.)"""
    kill = parse_kill(spec) if spec else None
    if not kill or kill[0] != "N":
        return {"met": False, "why": f"not a rule-N kill: {spec!r}", "tried": []}
    _, first, offset = kill
    maps = [m for m in sw.get("maps_from_arrival") or [] if isinstance(m, list) and len(m) == 2]
    saves = [s for s in sw.get("saves") or [] if (s.get("save") or 0) >= first and s.get("e3") is not None
             and s.get("e4") is not None]
    if FAULT == "n_rule_first_save":
        saves = saves[:1]
    starts = sorted(s["f"] for s in sw.get("starts") or [] if s.get("f") is not None)
    tried: list[dict] = []
    if sw.get("arrived") is None:
        return {"met": False, "why": "no held free arrival", "tried": tried}
    for i, save in enumerate(saves):
        until = saves[i + 1]["e4"] if i + 1 < len(saves) else None
        known = set(known_file) | {key for frame, key in maps if frame <= save["e3"]}
        new = next(([frame, key] for frame, key in maps if frame > save["e4"] and (until is None or frame < until)
                    and key not in known), None)
        start = next((f for f in starts if f > save["e4"] and (new is None or f <= new[0])), None)
        tried.append({"save": save["save"], "e4": save["e4"], "new_map": new, "start_first": start})
        if new is not None and start is None:
            return {"met": True, "anchor": save["save"], "e3": save["e3"], "e4": save["e4"], "entered": new[0],
                    "new_map": new[1], "kill_at": new[0] + offset, "known": sorted(known), "tried": tried}
    return {"met": False, "why": "no completed save was followed by a map new to it before a START or the next save",
            "tried": tried}


def chain_maps(row: dict, anchor: int | None = None) -> dict:
    """(spec section 5.2, as orchestrator ruling 12 amends it) NEW_B_pre, NEW_B_post, ABANDONED and the known set, from
    the K-SILENT child A's record and child B's own: its maps from the held free arrival on, cut at the e3 of save
    `anchor` (CHAIN: S_k, the save C continues; the OLD arms: B's first save)."""
    a = (row.get("ks") or {}).get("a") or {}
    sw = (row.get("b") or {}).get("save_watch") or {}
    kill = (row.get("b") or {}).get("kill") or {}
    saves = sw.get("saves") or [{}]
    s3 = next((s for s in saves if s.get("save") == anchor), {}) if anchor is not None else saves[0]
    e3, killed = s3.get("e3"), kill.get("frame")
    a_pre = set((row.get("chain") or {}).get("known_maps") or [])
    first: dict[str, int] = {}
    for frame, key in sw.get("maps_from_arrival") or []:
        first.setdefault(key, frame)
    b_pre = sorted(key for key, frame in first.items() if e3 is not None and frame <= e3)
    known = a_pre | set(b_pre)
    post = sorted(key for key, frame in first.items() if e3 is not None and killed is not None and e3 < frame <= killed
                  and key not in known)
    return {"b_pre": b_pre, "NEW_B_pre": sorted(set(b_pre) - a_pre), "NEW_B_post": post,
            "ABANDONED": sorted(set(new_maps(a)) - set(b_pre)), "known": sorted(known),
            "maps_pre_arrival": sw.get("maps_pre_arrival"), "arrived": sw.get("arrived"),
            "cut_at_save": s3.get("save"), "cut_e3": e3}


def grade_chain(row: dict) -> dict:
    """CHAIN's checks C1-C6, and CHAIN-OLD's / CHAIN-R1-OLD's difference (the follow-up spec section 5.2, as orchestrator
    rulings 11-12 amend it). CHAIN COUNTS when K-SILENT counted on this seed (re-graded here), rule N re-derived from B's
    record (`replay_rule_n`) is met from B's latest completed save S_k, S_k's e4 came before the kill with no START since
    it, the watcher's own kill is that rule's (same anchor, map and entry frame), and NEW_B_pre (cut at S_k's e3) is not
    empty. Its checks follow S_k: C1 the cart holds S_k by its truth; C3 B's FIRST post-continue line (by id) chains to
    S1 and not S2, and every later B line to the one before; C5 C continued S_k; C6 C's restore. An OLD arm counts when
    K-SILENT counted, its child B was killed after its first save's e4, and it ran its mutant copy (its twin CHAIN must
    count too: `verdict_of`)."""
    name = row["arm"]
    ks = row.get("ks") or {}
    ks_grade = grade(ks) if ks.get("a") and ks.get("b_run") else None
    ks_counted = bool(ks_grade and ks_grade["counted"])
    a = ks.get("a") or {}
    chain = row.get("chain") or {}
    b = row.get("b") or {}
    sw = b.get("save_watch") or {}
    kill = b.get("kill") or {}
    s3 = (sw.get("saves") or [{}])[0]
    e4_first = s3.get("e4") is not None and kill.get("frame") is not None and s3["e4"] < kill["frame"]
    ready = (row.get("child_b") or {}).get("word") == "READY"
    line = chain_line(row)
    maps = chain_maps(row)
    checks: dict = {}
    notes: dict = {"ks_counted": ks_counted, "ks_why": None if ks_grade is None else ks_grade.get("checks"),
                   "kill": kill, "b_word": (row.get("child_b") or {}).get("word"), "c3": line, "maps": maps,
                   "stale_lines": [x.get("id") for x in sw.get("stale_lines") or []],
                   "s3": {k: s3.get(k) for k in ("e1", "e3", "e4", "e7")}}
    s1_id, s2_id = chain.get("s1_id"), chain.get("s2_id")
    if name in ("CHAIN-OLD", "CHAIN-R1-OLD"):
        ran = mutant_ran(row, b)
        counted = ks_counted and ready and e4_first and ran
        if name == "CHAIN-OLD":
            shows = line.get("exists") is True and line.get("parent") == s2_id and s2_id is not None
        else:
            last = line.get("last_save") or {}
            shows = line.get("exists") is True and line.get("rebuild_error") is None and last.get("id") != line.get("id")
        notes.update(mutant_ran=ran, mutant=(row.get("mutant") or {}).get("edits"),
                     presses_digest_e3=kill.get("presses_digest_e3"))
        return {"checks": checks, "notes": notes, "counted": counted, "pass": None, "old_shows": bool(shows)}
    truths = a.get("truths") or {}
    # (orchestrator rulings 11-12) rule N re-derived from B's record (the grader's path): its anchor S_k is the save C
    # continues; the watcher's own kill must be that same anchor, map and frame
    replay = replay_rule_n(sw, chain.get("known_maps") or [], kill.get("spec"))
    anchor = replay.get("anchor") if replay["met"] else None
    sk = next((s for s in sw.get("saves") or [] if s.get("save") == anchor), {}) if anchor is not None else {}
    sk_truth = sk.get("truth") or {}
    watcher_agrees = bool(replay["met"]) and kill.get("anchor") == anchor and kill.get("entered") == replay["entered"] \
        and kill.get("new_map") == replay["new_map"] and kill.get("frame") is not None and kill["frame"] >= replay["kill_at"]
    starts_since = sum(1 for s in sw.get("starts") or [] if s.get("f") is not None and sk.get("e4") is not None
                       and sk["e4"] < s["f"] <= (kill.get("frame") or 0))
    sk_e4_before = sk.get("e4") is not None and kill.get("frame") is not None and sk["e4"] < kill["frame"]
    maps = chain_maps(row, anchor if anchor is not None else 1)
    notes["maps"] = maps
    notes["rule_n"] = {"replay": {k: v for k, v in replay.items() if k != "known"}, "watcher_agrees": watcher_agrees,
                       "starts_since_sk_e4": starts_since, "sk_e4_before_kill": sk_e4_before,
                       "watcher_anchors": kill.get("anchors")}
    notes["s_k"] = {"save": anchor, **{k: sk.get(k) for k in ("e1", "e3", "e4", "e7")}}
    # S_k's line, by IDENTITY: the one B line in B's frozen file whose stamp is S_k's RAM truth play time
    lines_b = chain_lines(row)
    sk_stamp = list(sk_truth["play_time"][:2]) if sk_truth.get("play_time") else None
    sk_matches = [x for x in lines_b["lines"] if sk_stamp is not None and x.get("play_time") == sk_stamp]
    sk_line = sk_matches[0] if len(sk_matches) == 1 else None
    sk_id = (sk_line or {}).get("id")
    notes["s_k"].update(id=sk_id, stamp=sk_stamp, lines_matching_its_stamp=[x["id"] for x in sk_matches],
                        b_line_ids=[x["id"] for x in lines_b["lines"]], newest_save_id=lines_b.get("newest_save_id"))
    # C1: the probe's parser on B's frozen cart (re-read here), by truth: it holds S_k, and no other save of B's
    bsaves = sw.get("saves") or []
    cart = Path((row.get("frozen_b") or {}).get("dir") or "") / "current_save.sav"
    file_b = chain_file(cart, truths.get("S1"), bsaves) if row.get("frozen_b") and cart.exists() else \
        (row.get("file_b") if isinstance((row.get("file_b") or {}).get("by_save"), dict) else {"by_save": {}})
    by_save = file_b.get("by_save") or {}
    checks["C1_file"] = anchor is not None and by_save.get(str(anchor)) == "S3" \
        and not any(str(v).startswith("S3") for k, v in by_save.items() if k != str(anchor))
    notes["C1"] = {"s_k": anchor, "by_save": by_save, "s1": file_b.get("s1")}
    # C2: B continued S1, and arrived at S1's truth
    session_b = next((x for x in reversed(row.get("b_memory") or []) if x.get("kind") == "session"), None)
    same = same_identity(b.get("arrival") or {}, b.get("boot"), truths.get("S1") or {}) if truths.get("S1") else {}
    checks["C2_continued_s1"] = session_b is not None and session_b.get("continued_from") == s1_id and bool(same) \
        and all(same.values())
    notes["C2"] = {"continued_from": (session_b or {}).get("continued_from"), "s1_id": s1_id, "same": same}
    # C3: the chain (by the test-side reader)
    last = line.get("last_save") or {}
    stamp_truth = (s3.get("truth") or {}).get("play_time")
    c3 = {"exists": line.get("exists") is True,
          "parent_is_continued_from": line.get("parent") == line.get("continued_from") == s1_id,
          "parent_not_s2": line.get("parent") != s2_id,
          "rebuilds": line.get("exists") is True and line.get("rebuild_error") is None,
          "last_save_is_own": last.get("id") == line.get("id") and last.get("play_time") == line.get("play_time"),
          "stamp_is_ram_truth": stamp_truth is not None and line.get("play_time") == list(stamp_truth[:2])}
    # (orchestrator ruling 12) the WHOLE post-continue chain, oldest first: the first is B's first line (by id); every
    # later line's parent is the B line before it; every line rebuilds; every rebuilt last_save is its own id and stamp
    chained = lines_b["lines"]
    c3.update({"first_b_line_is_the_one_read_by_id": bool(chained) and chained[0]["id"] == line.get("id"),
               "later_lines_chain_to_the_one_before": bool(chained) and all(
                   chained[i]["parent"] == chained[i - 1]["id"] for i in range(1, len(chained))),
               "every_line_rebuilds": bool(chained) and all(x["rebuild_error"] is None for x in chained),
               "every_last_save_is_own": bool(chained) and all(
                   (x["last_save"] or {}).get("id") == x["id"] and (x["last_save"] or {}).get("play_time") == x["play_time"]
                   for x in chained),
               "s_k_line_found": sk_id is not None})
    checks["C3_chain"] = all(c3.values())
    notes["C3"] = c3
    notes["C3_lines"] = [{k: x.get(k) for k in ("id", "parent", "play_time", "rebuild_error", "chain")}
                         | {"last_save_id": (x.get("last_save") or {}).get("id")} for x in chained]
    # C4 (REPORTED, never graded): a held free start at a ruling-51 moment, 3+ game minutes after S1; the restored
    # last_save at work only where B's OWN log says so (the AI's own record, named as such)
    s1_stamp = ((a.get("saves") or [{}])[0].get("line") or {}).get("play_time")
    gap = (line["play_time"][0] * 60 + line["play_time"][1]) - (s1_stamp[0] * 60 + s1_stamp[1]) \
        if line.get("play_time") and s1_stamp else None
    told = [str(r.get("reason")) for r in b_actions(Path(row["b_run"])) if r.get("decision") == "tell"
            and str(r.get("reason", "")).startswith("[AI-SAVE] no save for")] if row.get("b_run") else []
    mark = f"its last save was at {s1_stamp[0]}:{s1_stamp[1]:02d}" if s1_stamp else None
    notes["C4"] = {"held_free": (s3.get("start") or {}).get("held_free"), "overworld": (s3.get("start") or {}).get("overworld"),
                   "moment": moment_of(s3, sw.get("proof_first") or {}) if s3 else None, "gap_minutes": gap,
                   "restored_last_save": "exercised" if mark and any(mark in t for t in told) else "not exercised",
                   "ai_lines": told[:4]}
    # C5: child C's continue: of S_k (orchestrator ruling 12), its id and its truth
    c = row.get("c") or {}
    check_c = c.get("memory_check") or {}
    session_c = next((x for x in reversed(row.get("c_memory") or []) if x.get("kind") == "session"), None)
    same_c = same_identity(c.get("arrival") or {}, c.get("boot"), sk_truth) if sk_truth else {}
    facts_c = continue_facts(c)
    checks["C5_c_continued_sk"] = check_c.get("ok") is True and check_c.get("end_class") == "KILLED" \
        and session_c is not None and session_c.get("continued_from") == sk_id and sk_id is not None \
        and bool(same_c) and all(same_c.values()) and all(facts_c.values())
    notes["C5"] = {"memory_check": check_c, "continued_from": (session_c or {}).get("continued_from"), "s_k_id": sk_id,
                   "same": same_c, **facts_c}
    # C6: C's restore holds S1's restored set and NEW_B_pre (graded); NONE of NEW_B_post nor ABANDONED (a consistency
    # check with no registered mutant: reported, a failure of it still a FAIL, never cited as proof)
    snapshot, reason = restore_snapshot(Path(row["c_run"])) if row.get("c_run") else (None, None)
    restored = sorted((snapshot or {}).get("maps", {}).keys()) if snapshot else None
    agree = session_c is not None and restored is not None and sorted(session_c.get("restored_maps") or []) == restored
    s1_set = (session_b or {}).get("restored_maps") or []
    must = list(s1_set) + ([] if FAULT == "pre_maps_ignored" else maps["NEW_B_pre"])
    c6 = {"agree": agree, "holds_s1_and_new_b_pre": restored is not None and bool(s1_set) and all(m in restored for m in must),
          "none_of_new_b_post (consistency, no mutant)": restored is not None and not any(m in restored for m in maps["NEW_B_post"]),
          "none_of_abandoned (consistency, no mutant)": restored is not None and not any(m in restored for m in maps["ABANDONED"])}
    checks["C6_memory"] = all(c6.values())
    notes["C6"] = {**c6, "restore_reason": reason, "restored_maps": restored, "s1_restored_maps": s1_set}
    # (orchestrator ruling 11) counts: K-SILENT counted, B was killed (READY), rule N met on B's record with S_k's e4
    # before the kill and no START since it, the watcher's kill is that rule's, and NEW_B_pre (cut at S_k's e3) not empty
    counted = ks_counted and ready and bool(replay["met"]) and watcher_agrees and sk_e4_before and starts_since == 0 \
        and bool(maps["NEW_B_pre"])
    return {"checks": checks, "notes": notes, "counted": counted, "pass": counted and all(checks.values()) if counted else None}


def r2_want() -> str:
    """Step 1's exit reason (the launcher's record) as the R2-STOP copy's arrival bound words it."""
    return (f"play: stuck: the continue stopped: the continued game did not reach a free overworld within "
            f"{R2_STOP_ARRIVAL} frames")


def cmd_r2(args) -> int:
    """R2-RETRY (the follow-up spec section 5.1; D9, D10): step 1 is the REAL launcher's `run --continue` of K-AFTER's
    frozen copy, in a mirror build root, from the R2-STOP COPY (its only edit: the arrival bound), so the continue STOPS
    on that bound; its cart, memory and launches are frozen; step 2 is `child_b` (the REAL tree) on a copy of them.
    `--old`: R2-RETRY-OLD, step 2 only, on R2-RETRY's frozen set, from the FX3 copy."""
    from ai_player.paths import AppPaths
    from ai_player.skills.saving import CONTINUE_BUDGET

    ctx = ctx_of(args)
    source = Path(args.from_row)
    base = json.loads(source.read_text(encoding="utf-8"))
    if args.old:
        if base.get("arm") != "R2-RETRY":
            raise SystemExit("R2-RETRY-OLD runs on R2-RETRY's row")
        name, seed = "R2-RETRY-OLD", base["seed"]
        row = {"arm": name, "name": name, "seed": seed, "twin_row": str(source), "started": now()}
        for key in ("kafter_file", "s2_line_id", "s2_truth", "step1", "frozen_step1", "stop_arrival"):
            row[key] = base.get(key)
        if not base.get("frozen_step1"):
            row["result"] = "NOT RUN: R2-RETRY's step 1 left no frozen set"
        else:
            frozen = Path(base["frozen_step1"]["dir"])
            row["frozen_memory_sha256"] = hashlib.sha256((frozen / "memory.jsonl").read_bytes()).hexdigest()
            root, row["mutant"] = mutant_tree(ctx["out"], f"FX3-{seed}", FX3_EDITS)
            run = run_continue_child(ctx, row, frozen, "b", root)
            row["child_b"], row["b"], row["b_memory"], row["b_run"] = run["child"], run["result"], run["memory"], run["run_dir"]
            row["memory_sha256_after"] = run["memory_sha256_after"]
            row["grade"] = grade_r2(row)
    else:
        if base.get("arm") != "K-AFTER":
            raise SystemExit("R2-RETRY runs on K-AFTER's row")
        if R2_STOP_ARRIVAL is None:
            raise SystemExit("R2_STOP_ARRIVAL is not set: development step 5 (a) sets it before R2-RETRY runs")
        name, seed = "R2-RETRY", base["seed"]
        saves = (base.get("a") or {}).get("saves") or []
        row = {"arm": name, "name": name, "seed": seed, "kafter_row": str(source),
               "kafter_file": (base.get("file") or {}).get("verdict"),
               "s2_line_id": (saves[1].get("line") or {}).get("id") if len(saves) > 1 else None,
               "s2_truth": ((base.get("a") or {}).get("truths") or {}).get("S2"), "stop_arrival": R2_STOP_ARRIVAL,
               "started": now()}
        if (base.get("child_a") or {}).get("word") != "READY" or not base.get("frozen"):
            row["result"] = "NOT RUN: K-AFTER's child A did not reach its kill"
        else:
            mirror = mirror_build_root(ctx, f"{name}-{seed}")
            profile_name = f"ai-r1live-r2-retry-{seed}"
            profile = make_profile(mirror, profile_name, ctx["donor"])
            game = AppPaths.for_profile(profile_name, mirror, home="")
            game.game_dir.mkdir(parents=True)
            for item in Path(base["frozen"]["dir"]).iterdir():
                shutil.copy2(item, profile / item.name if item.name.endswith(".sav") else game.game_dir / item.name)
            root, row["mutant"] = mutant_tree(ctx["out"], f"R2-STOP-{seed}", R2_STOP_EDITS)
            folder = ctx["out"] / "runs" / f"{name}-{seed}"
            folder.mkdir(parents=True, exist_ok=True)
            run_dir = folder / "step1_run"
            frames = CONTINUE_BUDGET + R2_STOP_ARRIVAL + 600
            cmd = [sys.executable, "-B", "-m", "ai_player", "run", "--profile", profile_name, "--continue", "--frames",
                   str(frames), "--wall-seconds", str(LAUNCH_WALL), "--build-root", str(mirror), "--run-dir", str(run_dir)]
            log = folder / "step1_launcher.out"
            import subprocess

            from ai_player.options import ENV_BRAIN, ENV_CLOCK, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET

            personality, starter = plan_of(seed)
            env = child_env(mirror)
            env.update({ENV_BRAIN: "play", ENV_SEED: str(seed), ENV_PERSONALITY: personality, ENV_TARGET: TARGET,
                        ENV_CLOCK: WALL_CLOCK})
            if starter:
                env[ENV_STARTER] = starter
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
            actions = b_actions(run_dir)
            press = next((r for r in actions if r.get("decision") == "continue the saved game"
                          and str(r.get("action", "")).startswith("press A") and "CONTINUE" in str(r.get("reason", ""))),
                         None)
            purity = json.loads((run_dir / "purity.json").read_text(encoding="utf-8")) \
                if (run_dir / "purity.json").is_file() else None
            launches = [json.loads(x) for x in game.launches_jsonl.read_text(encoding="utf-8").splitlines() if x.strip()] \
                if game.launches_jsonl.exists() else []
            row["step1"] = {"cmd": cmd, "cwd": str(root), "pid": proc.pid, "exit": code, "killed": killed,
                            "seconds": round(time.monotonic() - began, 1), "log": str(log), "run_dir": str(run_dir),
                            "frames": frames, "lines": [x for x in text.splitlines() if x.startswith(
                                ("[AI-RUN]", "[AI-GATE]", "[AI-START]", "[AI-EXIT]"))],
                            "continue_press": (press or {}).get("reason"), "continue_press_frame": (press or {}).get("frame"),
                            "purity": (purity or {}).get("verdict"),
                            "purity_exit_reason": ((purity or {}).get("facts") or {}).get("exit_reason"),
                            "launches": launches,
                            "memory_after": [{k: v for k, v in x.items() if k != "memory"}
                                             for x in memory_lines(game.memory_jsonl)] if game.memory_jsonl.exists() else []}
            row["frozen_step1"] = freeze_profile(ctx, f"{name}-step1-{seed}", profile, game.game_dir)
            run = run_continue_child(ctx, row, Path(row["frozen_step1"]["dir"]), "b", REPO)
            row["child_b"], row["b"], row["b_memory"], row["b_run"] = run["child"], run["result"], run["memory"], run["run_dir"]
            row["grade"] = grade_r2(row)
    row["ended"] = now()
    out = ctx["out"] / "rows" / f"{name}-{seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    g = row.get("grade") or {}
    print("LIVE ARM " + json.dumps({"arm": name, "seed": seed, "counted": g.get("counted"), "pass": g.get("pass"),
                                    "old_shows": g.get("old_shows"), "checks": g.get("checks"), "result": row.get("result"),
                                    "step1_exit": (row.get("step1") or {}).get("exit"),
                                    "memory_check": (row.get("b") or {}).get("memory_check"), "row": str(out)},
                                   ensure_ascii=False), flush=True)
    return 0


def grade_r2(row: dict) -> dict:
    """R2-RETRY's checks R1-R3 and R2-RETRY-OLD's difference (the follow-up spec section 5.2). Both COUNT when K-AFTER's
    FILE was S2 and step 1 stopped on its arrival bound: the launcher's line for step 1's run folder has the R2-STOP
    copy's stop as its `exit_reason`; step 1's session continued nothing, its end line says stopped before its restore and
    not chosen, no `save` or `lost` line follows it, and its action log shows the CONTINUE press. The OLD arm also needs
    its FX3 copy to have run (its twin R2-RETRY must count too: `verdict_of`)."""
    step1 = row.get("step1") or {}
    want = (f"play: stuck: the continue stopped: the continued game did not reach a free overworld within "
            f"{row.get('stop_arrival')} frames")
    line = next((x for x in reversed(step1.get("launches") or []) if x.get("kind") == "launch_end"
                 and x.get("run_dir") == step1.get("run_dir")), None)
    reason = str((line or {}).get("exit_reason") or "")
    memory = step1.get("memory_after") or []
    sessions = [x for x in memory if x.get("kind") == "session"]
    session = sessions[-1] if sessions else None
    end = next((x for x in memory if x.get("kind") == "end" and session is not None and x.get("session") == session.get("n")),
               None)
    at = next((i for i, x in enumerate(memory) if x is session), None)
    played = [x for x in memory[at + 1:] if x.get("kind") in ("save", "lost")] if at is not None else []
    reach = {"kafter_file_s2": row.get("kafter_file") == "S2", "stop_is_registered": row.get("stop_arrival") == R2_STOP_ARRIVAL,
             "launcher_line_is_the_arrival_stop": line is not None and reason.startswith(want),
             "session_continued_nothing": session is not None and session.get("how") == "continue"
             and session.get("continued_from") is None,
             "end_stopped_before_restore": end is not None and end.get("stopped_before_restore") is True
             and not end.get("chosen"), "played_nothing": at is not None and not played,
             "continue_pressed_in_ram": bool(step1.get("continue_press"))}
    notes = {"reach": reach, "step1_reason": reason, "want": want, "step1_session": session, "step1_end": end}
    b = row.get("b") or {}
    check = b.get("memory_check") or {}
    counted = all(reach.values())
    if row["arm"] == "R2-RETRY-OLD":
        ran = mutant_ran(row, b)
        same = row.get("frozen_memory_sha256") is not None and row.get("frozen_memory_sha256") == \
            (b.get("frozen_memory") or {}).get("sha256_before") == row.get("memory_sha256_after")
        shows = ran and check.get("ok") is False and check.get("end_class") == "CHOSEN" and same
        notes.update(mutant_ran=ran, memory_check=check, memory_byte_identical=same)
        return {"checks": {}, "notes": notes, "counted": counted and ran, "pass": None, "old_shows": bool(shows)}
    words = str(check.get("why") or "")
    told = FAULT == "lookthrough_ignored" or ("looked through 1 " in words and reason in words and bool(reason))
    checks = {"R1_allowed": check.get("ok") is True and check.get("end_class") == "KILLED" and told}
    session_b = next((x for x in reversed(row.get("b_memory") or []) if x.get("kind") == "session"), None)
    truth = row.get("s2_truth") or {}
    same = same_identity(b.get("arrival") or {}, b.get("boot"), truth) if truth else {}
    facts = continue_facts(b)
    checks["R2_arrival"] = session_b is not None and session_b.get("how") == "continue" \
        and session_b.get("continued_from") == row.get("s2_line_id") and row.get("s2_line_id") is not None \
        and bool(same) and all(same.values()) and all(facts.values())
    checks["R3_step1_clean"] = step1.get("purity") == "CLEAN"
    notes.update(memory_check=check, continued_from=(session_b or {}).get("continued_from"), same=same, **facts)
    return {"checks": checks, "notes": notes, "counted": counted, "pass": counted and all(checks.values()) if counted else None}


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
    elif name in ("CHAIN", "CHAIN-OLD", "CHAIN-R1-OLD"):
        g = grade_chain(row)
    elif name in ("R2-RETRY", "R2-RETRY-OLD"):
        g = grade_r2(row)
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
    if name in ("CHAIN-OLD", "CHAIN-R1-OLD", "R2-RETRY-OLD") and not g["notes"].get("mutant_ran"):
        s.update(counted=False, why="its child did not run the mutant copy (the mutated file's sha256 differs)")
    if not s["counted"] and "why" not in s and name in ("CHAIN", "CHAIN-OLD", "CHAIN-R1-OLD"):
        s["why"] = ("its reach conditions do not hold (K-SILENT counted; CHAIN: rule N met on B's record from its latest "
                    "completed save S_k, S_k's e4 before the kill, no START since it, the watcher's kill that rule's, "
                    "NEW_B_pre not empty; the OLD arms: B's first save's e4 before the kill, the mutant ran)")
    if not s["counted"] and "why" not in s and name in ("R2-RETRY", "R2-RETRY-OLD"):
        s["why"] = ("its reach conditions do not hold (K-AFTER's FILE S2; step 1 stopped on its arrival bound, continued "
                    f"nothing, played nothing; the CONTINUE pressed): {g['notes'].get('reach')}")
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
        # (the R1 + R2 follow-up, spec section 5.3) every pair is expected to differ on each seed where BOTH arms count;
        # a pair on a seed where one did not count is listed, not expected to differ
        chain = get("CHAIN").get("notes") or {}
        for old, key, what in (("CHAIN-OLD", "parent", "B's save line's parent"),
                               ("CHAIN-R1-OLD", "last_save_id", "the rebuilt goals.last_save.id")):
            other = get(old).get("notes") or {}

            def read(notes: dict, key: str = key):
                c3 = notes.get("c3") or {}
                return c3.get("parent") if key == "parent" else (c3.get("last_save") or {}).get("id")
            both = bool(get("CHAIN").get("counted")) and bool(get(old).get("counted"))
            found.append({"seed": seed, "pair": f"CHAIN / {old} ({what})", "values": [read(chain), read(other)],
                          "own_id": (chain.get("c3") or {}).get("id"),
                          "presses digest to e3 (one trajectory, replayed)": [(chain.get("kill") or {}).get(
                              "presses_digest_e3"), other.get("presses_digest_e3")],
                          # a side with no value (its child never froze a save line) is no difference: vacuous
                          "both_counted": both, "differ": None not in (read(chain), read(other))
                          and read(chain) != read(other)})
        r2, r2old = get("R2-RETRY").get("notes") or {}, get("R2-RETRY-OLD").get("notes") or {}
        values = [(r2.get("memory_check") or {}).get("ok"), (r2old.get("memory_check") or {}).get("ok")]
        found.append({"seed": seed, "pair": "R2-RETRY / R2-RETRY-OLD (memory_check.ok)", "values": values,
                      "classes": [(r2.get("memory_check") or {}).get("end_class"),
                                  (r2old.get("memory_check") or {}).get("end_class")],
                      "both_counted": bool(get("R2-RETRY").get("counted")) and bool(get("R2-RETRY-OLD").get("counted")),
                      "differ": None not in values and values[0] != values[1]})
    return found


def between_caveat(summaries: dict, seeds) -> str:
    """(R1 fix round, review R-5: the headline carries the caveat, CLAUDE.md session discipline 2) When K-BETWEEN is graded
    under a kill rule that is not the spec's midpoint, the verdict line says so, with how the spec's own rule fared on these
    seeds (its diagnostic arm K-BETWEEN-MID). Empty under the spec's rule. (R1 + R2 follow-up, spec part (j): the
    verification's V2-1 and V2-2) It says how many of the midpoint's COUNTED seeds PASSED and names the failing ones: a
    count alone read as "the spec's rule was only vacuous" on a run where it counted and FAILED."""
    if BETWEEN_RULE == "midpoint":
        return ""
    mid = {seed: summaries.get(("K-BETWEEN-MID", seed)) or {} for seed in seeds}
    counted = [seed for seed in seeds if mid[seed].get("counted")]
    passed = [seed for seed in counted if mid[seed].get("pass")]
    if FAULT == "caveat_passes_ignored":  # (selftest only) the planted grader fault
        passed = list(counted)
    failing = [seed for seed in counted if seed not in passed]
    # (R1 + R2 follow-up fix round, the adversarial review's RV-2) 'vacuous' only when the midpoint counted on NO seed; a
    # count above 0 but under the floor is 'below the floor' (on #58 it counted 2 of 4 and passed both: not vacuous)
    shortfall = ": vacuous" if not counted else (": below the floor" if len(counted) < FLOOR else "")
    return (f", WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE {BETWEEN_RULE!r}, NOT THE SPEC'S MIDPOINT (the midpoint "
            f"arm K-BETWEEN-MID counted {len(counted)} of {len(seeds)}{shortfall}; "
            f"passed {len(passed)} of {len(counted)}{f'; FAILING on seeds {failing}' if failing else ''}; orchestrator "
            f"ruling 5)")


def verdict_line(result: dict, summaries: dict, seeds, found: list[dict]) -> str:
    """(R1 + R2 follow-up, spec part (j): V2-1) THE verdict line, built in ONE place, so the line printed and the
    `headline` in `verdict.json` are the same text and the caveat cannot be dropped from one of them (CLAUDE.md session
    discipline 2: the headline carries the caveat)."""
    return (f"LIVE R1 VERDICT: {result['verdict']}{between_caveat(summaries, seeds)} (failing: "
            f"{result['failing'] or 'none'}; below the floor: {result['below_floor'] or 'none'}; discriminators that "
            f"differ: {sum(1 for d in found if d['differ'])} of {len(found)})")


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
    headline = verdict_line(result, summaries, seeds, found)
    payload = {"verdict": result, "headline": headline, "summaries": {f"{n}-{s}": v for (n, s), v in summaries.items()},
               "discriminators": found}
    (out / "verdict.json").write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"PER ARM {json.dumps({n: {k: p[k] for k in ('counted', 'failed', 'floor_met')} for n, p in result['per_arm'].items()})}")
    print(headline)
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
    "CHAIN": f"a COPY of K-SILENT's frozen set (orchestrator ruling 1); child B (REAL tree) continues S1, kill N1+"
             f"{N_KILL_FRAMES} (orchestrator ruling 11: from B's LATEST completed save S_k, re-anchored on each save B "
             "completes before a map new to it; then a map new to S_k, no START since its e4); C1 FILE S_k by its truth; "
             "C2 B continued S1 and arrived at S1's truth; C3 B's FIRST post-continue save line (by id, the test-side "
             "reader) has parent = S1's id, not S2's, its stamp = the RAM truth at its e3, and every B line (oldest first) "
             "chains to the one before, rebuilds, and its goals.last_save is itself; C5 child C (REAL tree) allowed "
             "(KILLED), continued S_k, arrived at S_k's truth, CONTINUE, no NEW GAME, no page; C6 C's restore holds S1's "
             "restored maps and NEW_B_pre (cut at S_k's e3), and (consistency, no mutant) none of NEW_B_post nor "
             "ABANDONED; C4 reported only",
    "CHAIN-OLD": f"another COPY of K-SILENT's set, child B on mutant CH1, kill {CHAIN_OLD_KILL} (B's own first save): "
                 "shows B's save line's parent = S2's id (the abandoned line)",
    "CHAIN-R1-OLD": f"another COPY, child B on mutant FX1, kill {CHAIN_OLD_KILL}: shows B's save line's rebuilt "
                    "goals.last_save.id is not its own id (C3 can fail)",
    "R2-RETRY": f"K-AFTER's frozen copy in a mirror build root; step 1 the REAL launcher --continue from the R2-STOP copy "
                f"(ARRIVAL_BUDGET {R2_STOP_ARRIVAL}) stops on its arrival bound; step 2 child_b (REAL tree): R1 allowed, "
                "class KILLED, its words 'looked through 1' and step 1's reason; R2 continued S2 and arrived at S2's truth, "
                "CONTINUE, no NEW GAME, no page; R3 step 1's purity CLEAN",
    "R2-RETRY-OLD": "R2-RETRY's frozen set after step 1, step 2 from the FX3 copy: refused, class CHOSEN, the memory file "
                    "byte-identical",
}
COUNTING = ("an arm COUNTS on a seed when (1) its FILE equals the expectation from its own record, NEW is not empty where "
            "check 3 needs it, check 7 holds where it applies, child A reached the kill (K-SILENT: 0 new sectors at it; "
            "K-BETWEEN: its determinism line); an OLD arm only when its NEW twin counts there and its child B ran the "
            "mutant copy; LAUNCH and LAUNCH-OLD when K-AFTER's FILE was S2; CONTROL when child A ran to its own end; "
            "CHAIN when K-SILENT counted, rule N re-derived from B's record is met from B's latest completed save S_k, "
            "S_k's e4 came before the kill with no START since it, the watcher's kill is that rule's, and NEW_B_pre is "
            "not empty (CHAIN-OLD and CHAIN-R1-OLD: K-SILENT counted, B killed after its "
            "first save's e4, the mutant ran); R2-RETRY and R2-RETRY-OLD when K-AFTER's FILE was S2 and step 1 stopped "
            "on its arrival bound (the launcher's line), continued nothing, played nothing, and pressed CONTINUE")


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
            # (the R1 + R2 follow-up's arms)
            "ch1_edits": CH1_EDITS, "fx1_edits": FX1_EDITS, "fx3_edits": FX3_EDITS, "r2_stop_edits": R2_STOP_EDITS,
            "r2_stop_arrival": R2_STOP_ARRIVAL, "r2_step1_frames": CONTINUE_BUDGET + (R2_STOP_ARRIVAL or 0) + 600,
            "chain_b_frames": CHAIN_B_FRAMES, "chain_b_timeout": CHAIN_B_TIMEOUT, "chain_old_frames": CHAIN_OLD_FRAMES,
            "chain_old_kill": CHAIN_OLD_KILL, "chain_old_timeout": CHAIN_OLD_TIMEOUT,
            "chain_budget_base": CHAIN_BUDGET_BASE, "n_kill_frames": N_KILL_FRAMES, "rule_n": SaveWatch._rule_n.__doc__,
            "rule_n_replay": replay_rule_n.__doc__,
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
    # 2b. (the R1 + R2 follow-up) the new arms: their mutants are revert_r1's, edit for edit (spec D11)
    for name, edits in (("CH1", CH1_EDITS), ("FX1", FX1_EDITS), ("FX3", FX3_EDITS)):
        case(f"the live {name} edit is revert_r1's {name}, edit for edit", [tuple(e) for e in edits],
             [tuple(e) for e in MUTANTS[name][2]])
    # recorded development rows (#57): CHAIN counted and passing; its OLD arms show their difference
    for key in SELFTEST_ROWS["chain_pass"]:
        g = grade_chain(need(key))
        case(f"recorded {key}: counted and passing (C1-C6)", [g["counted"], g["pass"]], [True, True])
    # (orchestrator ruling 11) rule N RE-ANCHORED on a later save of B's: C continues THAT save, not B's first
    from ai_player.skills.saving import ARRIVAL_BUDGET, CONTINUE_BUDGET

    case("CHAIN_BUDGET_BASE is CONTINUE_BUDGET + ARRIVAL_BUDGET", CHAIN_BUDGET_BASE, CONTINUE_BUDGET + ARRIVAL_BUDGET)
    for key in SELFTEST_ROWS["chain_reanchored"]:
        g = grade_chain(need(key))
        sk = (g["notes"].get("s_k") or {})
        case(f"recorded {key}: rule N re-anchored on B's save {sk.get('save')} (not its first): counted and passing, and "
             f"C continued that save's line (id {sk.get('id')}), not B's first line",
             [g["counted"], g["pass"], (sk.get("save") or 0) > 1,
              g["notes"]["C5"].get("continued_from") == sk.get("id") != (g["notes"].get("c3") or {}).get("id")],
             [True, True, True, True])
    for key in SELFTEST_ROWS["chain_old"]:
        row = need(key)
        g = grade_chain(row)
        case(f"recorded {key}: the mutant ran, it counts on K-SILENT's reach, and it SHOWS its difference",
             [g["counted"], g["notes"]["mutant_ran"], g["old_shows"]], [True, True, True])
    for key in SELFTEST_ROWS["r2_pass"]:
        g = grade_r2(need(key))
        case(f"recorded {key}: counted and passing (R1-R3)", [g["counted"], g["pass"]], [True, True])
    for key in SELFTEST_ROWS["r2_old"]:
        g = grade_r2(need(key))
        case(f"recorded {key} (FX3): the mutant ran and it SHOWS the refusal (CHOSEN, the file byte-identical)",
             [g["counted"], g["notes"]["mutant_ran"], g["old_shows"]], [True, True, True])
    # planted cases on the new arms (FAULT INPUT: the grader must see each)
    chain_key = SELFTEST_ROWS["chain_pass"][0]
    temp = Path(tempfile.mkdtemp(prefix="live_r1_selftest_"))
    try:
        # (code-host F4) the memory tail of a continued child: B's frozen file replayed through `tail_attach`
        row = need(chain_key)
        memory = Path(row["frozen_b"]["dir"]) / "memory.jsonl"
        attached = tail_attach(memory, row["chain"]["frozen_memory_size"], row["chain"]["frozen_next_save_id"])
        case(f"{chain_key}'s frozen B memory replayed through the tail: the first save line attached is B's own "
             f"(id {row['chain']['frozen_next_save_id']}), never the frozen S1 or S2",
             attached[0]["id"] if attached else None, row["chain"]["frozen_next_save_id"])
        # C3: B's save line chained to S2 (CH1's line) must FAIL the parent half
        planted = copy.deepcopy(row)
        folder = temp / "parent"
        folder.mkdir()
        lines = [json.loads(x) for x in memory.read_text(encoding="utf-8").splitlines() if x.strip()]
        for line in lines:
            if line.get("kind") == "save" and line["id"] == row["chain"]["frozen_next_save_id"]:
                line["parent"] = row["chain"]["s2_id"]
        (folder / "memory.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        planted["frozen_b"] = {**planted["frozen_b"], "dir": str(folder)}
        case("FAULT INPUT B's save line chained to S2 (CH1's line): C3 FAILS", grade_chain(planted)["checks"]["C3_chain"],
             False)
        # C3: B's save line whose goals.last_save is save 1's (FX1's line) must FAIL the last_save half
        planted = copy.deepcopy(row)
        folder = temp / "last_save"
        folder.mkdir()
        lines = [json.loads(x) for x in memory.read_text(encoding="utf-8").splitlines() if x.strip()]
        for line in lines:
            if line.get("kind") == "save" and line["id"] == row["chain"]["frozen_next_save_id"]:
                ops = [op for op in line["memory"]["set"] if op[0][:2] != ["goals", "last_save"]]
                line["memory"]["set"] = ops + [[["goals", "last_save", "id"], row["chain"]["s1_id"]]]
        (folder / "memory.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        planted["frozen_b"] = {**planted["frozen_b"], "dir": str(folder)}
        case("FAULT INPUT B's save line remembers save 1 as its last save (FX1's line): C3 FAILS",
             grade_chain(planted)["checks"]["C3_chain"], False)
        # C6: child C's restore misses a map of NEW_B_pre (the snapshot and the session line agree on it) must FAIL
        planted = copy.deepcopy(row)
        drop = grade_chain(row)["notes"]["maps"]["NEW_B_pre"][0]
        folder = temp / "c_run"
        folder.mkdir()
        source = Path(row["c_run"])
        shutil.copy2(source / "actions.jsonl", folder / "actions.jsonl")
        snapshots = [json.loads(x) for x in (source / "world.jsonl").read_text(encoding="utf-8").splitlines()]
        for snapshot in snapshots:
            snapshot.get("maps", {}).pop(drop, None)
        (folder / "world.jsonl").write_text("".join(json.dumps(s) + "\n" for s in snapshots), encoding="utf-8")
        planted["c_run"] = str(folder)
        for line in planted["c_memory"]:
            if line.get("kind") == "session" and isinstance(line.get("restored_maps"), list):
                line["restored_maps"] = [m for m in line["restored_maps"] if m != drop]
        case(f"FAULT INPUT child C's restore misses {drop} of NEW_B_pre: C6 FAILS", grade_chain(planted)["checks"]["C6_memory"],
             False)
        # (orchestrator rulings 11-12) planted cases on a RE-ANCHORED row (its clean grade is a case above)
        re_key = SELFTEST_ROWS["chain_reanchored"][0]
        row = need(re_key)
        # (the planted values come from the watcher's RECORD, so a grader fault cannot change where they are planted)
        rec = row["b"]["kill"]
        sk = {"save": rec["anchor"], "e4": rec["anchor_e4"], "b_line_ids": grade_chain(row)["notes"]["s_k"]["b_line_ids"]}
        # a START between S_k's e4 and the new map (a write may be under way): the rule is not met, the arm NOT counted
        planted = copy.deepcopy(row)
        planted["b"]["save_watch"]["starts"].append({"f": (sk["e4"] + rec["entered"]) // 2, "held_free": True})
        case(f"FAULT INPUT {re_key}: a START between S_k's e4 and the new map: NOT counted", grade_chain(planted)["counted"],
             False)
        # the watcher's kill names B's FIRST save as its anchor while the record re-anchored: NOT counted
        planted = copy.deepcopy(row)
        planted["b"]["kill"]["anchor"] = 1
        case(f"FAULT INPUT {re_key}: the watcher's anchor (save 1) is not the rule's (save {sk['save']}): NOT counted",
             grade_chain(planted)["counted"], False)
        # S_k's RAM truth one tile off: the cart no longer holds S_k by its truth (C1 FAILS)
        planted = copy.deepcopy(row)
        for save in planted["b"]["save_watch"]["saves"]:
            if save.get("save") == sk["save"]:
                save["truth"]["pos"] = [save["truth"]["pos"][0] + 1, save["truth"]["pos"][1]]
        case(f"FAULT INPUT {re_key}: S_k's truth one tile off: C1 FAILS", grade_chain(planted)["checks"]["C1_file"], False)
        # a LATER B line chained to S1 (the continued save) instead of the B line before it: C3 FAILS
        b_ids = sk["b_line_ids"]
        re_memory = Path(row["frozen_b"]["dir"]) / "memory.jsonl"
        for label, edit in (("chained to S1 instead of the B line before it",
                             lambda line: line.update(parent=row["chain"]["s1_id"])),
                            ("remembering B's first line as its last save",
                             lambda line: line["memory"].update(set=[op for op in line["memory"].get("set") or []
                                                                     if op[0][:2] != ["goals", "last_save"]]
                                                                + [[["goals", "last_save", "id"], b_ids[0]]]))):
            planted = copy.deepcopy(row)
            folder = temp / f"later-{len(cases)}"
            folder.mkdir()
            lines = [json.loads(x) for x in re_memory.read_text(encoding="utf-8").splitlines() if x.strip()]
            for line in lines:
                if line.get("kind") == "save" and len(b_ids) > 1 and line["id"] == b_ids[1]:
                    edit(line)
            (folder / "memory.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
            planted["frozen_b"] = {**planted["frozen_b"], "dir": str(folder)}
            case(f"FAULT INPUT {re_key}: B's line {b_ids[1] if len(b_ids) > 1 else None} {label}: C3 FAILS",
                 grade_chain(planted)["checks"]["C3_chain"], False)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    # R1: the next continue allowed but its words say nothing of the look-through must FAIL
    planted = copy.deepcopy(need(SELFTEST_ROWS["r2_pass"][0]))
    check = planted["b"]["memory_check"]
    check["why"] = str(check.get("why", "")).split(" (looked through")[0]
    case("FAULT INPUT step 2's words do not tell the look-through: R1 FAILS", grade_r2(planted)["checks"]["R1_allowed"], False)
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
         f"K-BETWEEN-MID counted 0 of 4: vacuous; passed 0 of 0; orchestrator ruling 5)")
    # (R1 + R2 follow-up, V2-2) the midpoint COUNTED on all four seeds and FAILED on every one: the caveat must say so
    mid_failing = {**table(), **{("K-BETWEEN-MID", seed): {"counted": True, "pass": False} for seed in seeds}}
    case("the verdict line names the midpoint arm's FAILING seeds (counted 4, passed 0)",
         between_caveat(mid_failing, seeds), "" if BETWEEN_RULE == "midpoint" else
         f", WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE {BETWEEN_RULE!r}, NOT THE SPEC'S MIDPOINT (the midpoint arm "
         f"K-BETWEEN-MID counted 4 of 4; passed 0 of 4; FAILING on seeds {list(seeds)}; orchestrator ruling 5)")
    # (fix round, RV-2) the midpoint counted on 2 of 4 (under the floor) and PASSED both: 'below the floor', never 'vacuous'
    mid_some = {**table(), **{("K-BETWEEN-MID", seed): ({"counted": True, "pass": True} if seed in (seeds[0], seeds[-1])
                                                        else {"counted": False}) for seed in seeds}}
    case("the verdict line calls a midpoint counted on 2 of 4 'below the floor', not 'vacuous'",
         between_caveat(mid_some, seeds), "" if BETWEEN_RULE == "midpoint" else
         f", WITH K-BETWEEN UNDER THE SUBSTITUTED KILL RULE {BETWEEN_RULE!r}, NOT THE SPEC'S MIDPOINT (the midpoint arm "
         f"K-BETWEEN-MID counted 2 of 4: below the floor; passed 2 of 2; orchestrator ruling 5)")
    # (V2-1) the verdict LINE itself carries the caveat (built by verdict_line, the one place both outputs use)
    line = verdict_line(verdict_of(mid_failing, seeds), mid_failing, seeds, [])
    case("the verdict LINE (verdict_line) carries the caveat", between_caveat(mid_failing, seeds) in line
         and line.startswith("LIVE R1 VERDICT: "), True)
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
        grader = grade_control if row["arm"] == "CONTROL" else grade_launch if row["arm"].startswith("LAUNCH") else \
            grade_chain if row["arm"].startswith("CHAIN") else grade_r2 if row["arm"].startswith("R2-RETRY") else grade
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
    p = sub.add_parser("chain", help="CHAIN (or --old CHAIN-OLD / CHAIN-R1-OLD) on a K-SILENT row")
    p.add_argument("--from-row", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--old", choices=("CHAIN-OLD", "CHAIN-R1-OLD"))
    p.add_argument("--build-root")
    p = sub.add_parser("r2", help="R2-RETRY on a K-AFTER row (or --old: R2-RETRY-OLD on an R2-RETRY row)")
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
    # (CHAIN and its OLD arms) the child's own SaveWatch and its kill
    p.add_argument("--kill")
    p.add_argument("--record")
    p.add_argument("--known-maps")
    p.add_argument("--maps-from-arrival", action="store_true")
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
    if args.cmd == "chain":
        return cmd_chain(args)
    if args.cmd == "r2":
        return cmd_r2(args)
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
