"""A1, THE FRONTIER PROBE AND THE TRAINER'S RUNNER CORE (build spec `PROJECT KNOWLEDGE/ai-research-notes/2026-11-11-A1-
FRONTIER-PROBE-SPEC.md`, amended 2026-11-13). TEST SIDE: the AI never imports this module (test_frontier_probe T28), and
it takes no value from the AI's code (`check_grader_imports.scan` on it is clean: the AI facts it needs are COPIED here as
constants and pinned by T30).

WHAT IT IS FOR. (1) MEASURE where the AI stops across chapters 1-7, as a RANKED BLOCKER LIST with a kept example of each,
for the trainer to work down one skill build at a time; (2) BE THE RUNNER CORE that the learner's trainer (Phase A) calls as
a subprocess (`run --trainer`). Nothing is built twice: every leg is `live_step5.run_arm` (the real launcher, the purity
gate on every launch), judged by `live_step2.check_purity` and `live_step5.check_after_is_this_run`, measured and ended by
`live_chain.finish_leg`, salvaged by `live_chain.salvage_leg`; legs come from `live_chain.legs_of`; an MC job decides its
next leg by `live_chain.continue_after` itself. `live_chain.py`, `live_step5.py`, `launcher.py`, `ledger.py`,
`check_grader_imports.py` and `ai-agent/*` are NOT CHANGED by A1.

    py -3.12 -B ai_player/gates/frontier_probe.py stage --commit SHA --stage DIR [--repo DIR] [--sandbox DIR] [--donor DIR]
            [--mutant NAME] [--starts G1,...] [--g-root DIR] [--c-root DIR]
        build ONE stage (the code root the children run) outside every git work tree: the commit's ai_player by `git
        archive` (evidence excluded), a build root whose modules, plugins, mgba and roms are JUNCTIONS to the sandbox, the
        donor profile `ai-fp-donor`, the starts COPIED and custody-checked (md5, the start truth holding ch5_rival_meet's
        proof, a world file of JSON lines, one starter line), and manifest.json (play digest, digest, md5s, junctions)
    py -3.12 -B ai_player/gates/frontier_probe.py plan P1|GM|WP1|MC --first-seed N [--to T] > jobs.json
        the batch's job list (pure; every job's env is EMPTY: the probe sets every launch key itself, and `plan` and `run`
        refuse a job env naming any key; MC sends no AI_PLAYER_GOALS)
    py -3.12 -B ai_player/gates/frontier_probe.py run --jobs F --out DIR --stage ARM=DIR[,ARM=DIR]
            (--ledger development --prediction-file F | --trainer) [--parallel 8] [--deadline EPOCH] [--max-wait 7200]
            [--resume]
        the batch: at most P jobs at once beside the bot tuner (GO, WAIT, SKIP, DROP), each job a child process of its
        stage's own copy of this file; the disk guard, the stage watch, the AI-only stop, the deadline; records.jsonl;
        the report; in development mode one ledger entry and the evidence file, in trainer mode NOTHING tracked written
    py -3.12 -B ai_player/gates/frontier_probe.py report DIR          the blocker report from DIR/records.jsonl (offline)
    py -3.12 -B ai_player/gates/frontier_probe.py replay EXAMPLE --stage DIR --profile NAME [--seed N] [--frames F]
            [--code-tree DIR]
        ONE leg again from a kept example (its state, world line and goal snapshot when kept): one NEW trajectory, never
        a replication (CLAUDE.md rule 8: the game splits by one frame at an outdoor warp, measured 2026-11-13)
    py -3.12 -B ai_player/gates/frontier_probe.py compare A.jsonl B.jsonl [--context N]
        the first differing (frame, action) of two action logs, skipping 'say' and 'world' records (offline)
    py -3.12 -B ai_player/gates/frontier_probe.py reserve-band [--ledger PATH]     the AI trainer band row (once)
    py -3.12 -B ai_player/gates/frontier_probe.py teardown --stage DIR             junctions unlinked FIRST, then deleted
    `child JOB.json` is the internal entry of one job (run from its stage).

EXIT CODES: 0 ran; 2 refused before any launch (no ledger write); 3 ABORTED by the disk guard; 4 harness ERROR after
ledger.begin (the entry finished as ERROR); 5 an unguarded crash; 6 the AI-only stop (5 legs in a row of REFUSED, NOT
CLEAN or HUNG: no new launch, <out>/AI-ATTENTION.txt, never the learner's ATTENTION.md).

DEVELOPMENT DATA, NEVER A GRADED PROOF: `PROJECT KNOWLEDGE/ai-frontier.txt` is the authority, and only a graded
`live_chain` run moves it (D4). Practice from saves is not the frontier. A rerun on one seed is a correlated near-replay,
never an independent sample: identical results are a determinism check only.

ONE DEVIATION FROM THE SPEC'S TEXT, said here: 3.12 zips a job's kept files at the JOB's end; this module zips each leg's
logs at that LEG's end (verified, then the raw logs deleted; the example files kept raw), so every leg record carries its
own zip and sha256, and a killed job leaves at most its in-flight leg unzipped.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import traceback
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import ledger  # noqa: E402
from ai_player.gates import live_chain as LC  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_CLOCK, ENV_GOALS, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET, ENV_WORLD,
)

GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
FAMILY = "story"
DRIVER = "frontier_probe"
SPEC = "PROJECT KNOWLEDGE/ai-research-notes/2026-11-11-A1-FRONTIER-PROBE-SPEC.md"
SCHEMA_VERSION = 1
HEADER = "DEVELOPMENT DATA, NEVER A GRADED PROOF; PROJECT KNOWLEDGE/ai-frontier.txt is the authority"

# ====================================================================== the legs (2.3): L6-L7 are A1's OWN, never live_chain's
#: frames per chapter: chapters 1-5 are live_chain's FRAMES_BY_CHAPTER (read, never copied); 6 and 7 are new here (2.3: L6
#: raised to 1,000,000 on 2026-11-13, "In training the budget is set generously, so it never cuts off real progress")
LEG_FRAMES: dict[int, int] = {**LC.FRAMES_BY_CHAPTER, 6: 1_000_000, 7: 1_200_000}
#: the wall clock per chapter (s): live_chain's WALL for 1-5, 7,200 s for 6 and 7 (1,200,000 frames at 349 frames/s take
#: 3,440 s)
LEG_WALL: dict[int, float] = {**{chapter: float(LC.WALL) for chapter in LC.FRAMES_BY_CHAPTER}, 6: 7200.0, 7: 7200.0}
#: the target of the whole probe and of a practice job (chapters 6-7)
PROBE_TO = "ch7_brawly"
CHAPTER5_END = "ch5_rival_meet"
#: a saved start (chapters 1-5 already played) keeps the legs from this chapter on (2.3, 3.4 step 3)
PRACTICE_FROM = 6

# ====================================================================== the disk (2.7, 3.12)
WORLD_CUT_BYTES = 1_000_000_000
ABORT_FREE_GB = 40.0
START_FREE_GB = 45.0
OUT_CAP_BYTES = 5_000_000_000
PROFILE_BUDGET_BYTES = 1_250_000_000
#: an MC job keeps live_chain's world cut (`live_chain.GUARD_WORLD_BYTES`, READ at every use, never copied) and its
#: profile budget lies this far above it (2.7: 1,750,000,000 bytes today)
MC_PROFILE_MARGIN_BYTES = 250_000_000
#: P fits the disk (2.7): P_fit = floor((free - ABORT_FREE_GB - OUT_ESTIMATE_GB - STAGES_GB - P_MARGIN_GB) / per job)
OUT_ESTIMATE_GB = 0.6
STAGES_GB = 0.4
P_MARGIN_GB = 2.0
PER_JOB_GB = 1.25
MC_PER_JOB_GB = 1.75
#: the disk reservation's margin above the abort floor (3.13: concurrency alone never ABORTs a batch)
RESERVE_MARGIN_GB = 2.0
#: live_chain's graded world cap, REPORTED here (3.6: the world size is never a condition of an A1 leg)
WORLD_REPORT_BYTES = LC.WORLD_MAX_BYTES

# ====================================================================== the scheduler (2.6, 3.13)
P_DEFAULT = 8
P_MAX = 12
MC_PARALLEL = 3
#: own launches plus other singles at most this many (a single = a pokebot.py without --endless-target: the learner's
#: `other_bots_running` rule), so the tuner's `size_lanes` keeps its 12 lanes
SINGLES_CAP = 16
MAX_WAIT_SECONDS = 7200
TICK_SECONDS = 5.0
STAGE_WATCH_SECONDS = 60.0
SANDBOX_WATCH_SECONDS = 600.0
#: the deadline margin of one leg: run_arm's margin over the wall clock and two truth reads (`chain_watchdog_seconds`)
LEG_MARGIN_SECONDS = LC.LEG_MARGIN_SECONDS + 2 * LC.TRUTH_SECONDS
#: the AI-only stop: this many legs in a row, by end time, of a counting class
STOP_STREAK = 5
GO, WAIT, SKIP, DROP = "GO", "WAIT", "SKIP", "DROP"

# ====================================================================== the end classes (3.5, D14 changed)
CUT_WORLD = "CUT-WORLD"
INFRA = "INFRA"
REFUSED = "REFUSED"
HUNG = "HUNG"
NOT_CLEAN = "NOT CLEAN"
CLEAN_BUDGET = "CLEAN-BUDGET"
CLEAN_INVOLUNTARY = "CLEAN-INVOLUNTARY"
CLEAN_CHOSEN = "CLEAN-CHOSEN"
CLASSES = (CUT_WORLD, INFRA, REFUSED, HUNG, NOT_CLEAN, CLEAN_BUDGET, CLEAN_INVOLUNTARY, CLEAN_CHOSEN)
CLEAN_CLASSES = (CLEAN_BUDGET, CLEAN_INVOLUNTARY, CLEAN_CHOSEN)
#: the AI-only stop's count ("Stop": counts) and what resets it; INFRA does neither
STOP_CLASSES = (REFUSED, NOT_CLEAN, HUNG)
RESET_CLASSES = (*CLEAN_CLASSES, CUT_WORLD)
#: in the blocker list when not reached ("Blk")
BLOCKER_CLASSES = (CUT_WORLD, HUNG, *CLEAN_CLASSES)
#: never in the judged denominator
EXCLUDED_CLASSES = (REFUSED, NOT_CLEAN, INFRA)
CUT_TEXT = "harness cut: world.jsonl over 1 GB (a churn, KI-129/KI-130)"
CUT_TEXT_MC = "harness cut: world.jsonl over 1.5 GB (a churn, KI-129/KI-130)"
CUT_PROFILE_TEXT = "harness cut: profile folder over budget"
HUNG_TEXT = "launcher hard kill at the wall clock, no verdict (a hung brain)"
RAISE_TEXT = "budget: a boss-prep raise still active"
#: (3.8) the reason a key keeps: digit runs made N, whitespace collapsed, cut here
REASON_CUT = 160

# ====================================================================== the loop key (3.8, D7 changed)
#: both pre-registered in the prediction file; calibrated on E0's two loop legs (118 and 74 crossings)
LOOP_MIN_CROSSINGS = 40
#: = STORY_PATIENCE (`mode.py`): the loop must run into the leg's end
LOOP_END_FRAMES = 120_000

# ====================================================================== the AI's facts, COPIED (T30 pins them to the AI's code)
#: `ai_player/personality.py` PERSONALITIES (as a set)
PERSONALITIES = ("Catcher", "Story", "Trainer")
#: (persona, starter) of `live_chain.PAIRS`' diagonal first, then the 6 pairs never played as a New Game chain (2.2)
STARTERS = ("TREECKO", "TORCHIC", "MUDKIP")
STARTER_LINES = {"TREECKO": ("Treecko", "Grovyle", "Sceptile"), "TORCHIC": ("Torchic", "Combusken", "Blaziken"),
                 "MUDKIP": ("Mudkip", "Marshtomp", "Swampert")}
#: `MapMemory.to_dict()["tile_fields"]` (`ai_player/world/memory.py`): a map whose list differs is dropped (fail closed)
TILE_FIELDS = ("flags (b blocked, w water, g grass, e encounters, d door, p warp)", "ledge", "elevation", "behavior",
               "seen_frame", "seen_from_x", "seen_from_y")
#: how many of them are static map facts (flags, ledge, elevation, behavior; never when or from where it was seen)
TILE_STATIC = 4
#: part 0's snapshot file (`game_memory.GOALS_FILE_NAME`) and its kind (`game_memory.SNAPSHOT_KIND`)
GOALS_FILE = "goals.jsonl"
GOALS_KIND = "goals"
#: boss preparation's acting personalities (`brain/bossprep.py` ACTING): a Trainer only logs its plan
BOSSPREP_ACTING = ("Story", "Catcher")
#: the knowledge's map count (`knowledge/world/maps.json`): the experience union holds at most this many maps
MAX_MAPS = 518

# ====================================================================== the environment (3.11, D17's allow-list)
#: the ONLY keys a job's environment may name (AI_PLAYER_GOALS only on a leg that carries a snapshot, never on MC)
ENV_ALLOWED = (ENV_BRAIN, ENV_SEED, ENV_PERSONALITY, ENV_STARTER, ENV_TARGET, ENV_CLOCK, ENV_WORLD, ENV_GOALS)
#: the child removes these from its own environment before any launcher import (`run_arm`'s `clean_env` strips only
#: AI_PLAYER_*: without this POKEBOT_BOSSMODE_TOPUP or PYTHONPATH would reach the launch)
STRIPPED_PREFIXES = ("AI_PLAYER_", "POKEBOT_")

# ====================================================================== seeds and the ledger (2.5, 3.10)
TRAINER_BAND = (2_000_000, 2_999_999)
BAND_NOTE = "AI trainer band"
BAND_TEXT = ("D13 (2026-10-30 AI trainer design): the seed band 2,000,000-2,999,999 is the AI trainer's own; its runs are "
             "development, never graded, and write no ledger entry of their own; no session plays it")
BAND_VERDICT = "RESERVED: the AI trainer band (D13); never played by a session"
MC_SEEDS = (6701, 6799)
#: every ledger a development seed is checked against (2.5: refuse a seed ANY entry names; the lab's copies included)
SEED_LEDGER_GLOBS = ("C:/Remote Projects/Pokebot_Gen3_Enhancement/ai_player/gates/ledger.json",
                     "C:/Remote Projects/Pokebot_Gen3_Enhancement/.claude/worktrees/*/ai_player/gates/ledger.json",
                     "C:/Remote Projects/_ai_lab/**/ledger.json",
                     "C:/Remote Projects/pokebot-learner/ai_player/gates/ledger.json")
#: a file named ledger.json that is no ledger (2.5: the truncated export of 2026-11-13), listed and allowed
KNOWN_NON_LEDGERS = ("_ai_lab/s53/mergeplan/review/exports/s2/ai_player/gates/ledger.json",)

# ====================================================================== files of a batch's --out
STOP_FILE = LC.STOP_FILE
ABORT_FILE = LC.ABORT_FILE
ATTENTION_FILE = "AI-ATTENTION.txt"
RECORDS = "records.jsonl"
EXPERIENCE = "experience.jsonl"
EXPERIENCE_MAPS = "experience_maps.json"
BATCH_FILE = "batch.json"
EVENTS = "events.jsonl"
PROFILE_PREFIX = "ai-fp-"
DONOR = "ai-fp-donor"
#: the files of a leg's kept folder: the EXAMPLE (kept raw: the next leg's start and Phase A's pool state) ...
EXAMPLE_FILES = ("end_state.ss1", "world_last.jsonl", "goals_last.jsonl")
#: ... the AI's own files, copied from the profile when present (3.12) ...
AI_FILES = (("current_save.sav", "current_save.sav"), ("ai_player/memory.jsonl", "memory.jsonl"),
            ("ai_player/launches.jsonl", "launches.jsonl"))
#: ... and the logs, zipped and verified, then deleted raw
LOG_FILES = ("actions.jsonl", "ai_player.log", "purity.json", "stdout.txt", GOALS_FILE, "row.json")

# ====================================================================== the starts (2.1)
GRADED_CH5 = Path("C:/Remote Projects/_livechain/graded-ch5")
KEPT_C = Path("C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/ch5stops/out/probe")
#: id -> where it is, its md5s (state / world), its persona; G starters from the job file, C starters from the truth's party
STARTS = {
    "G1": {"root": "g", "path": "LC-S-6201", "md5": "5cdc4f0e20e99f650de8d6d157d5afd2",
           "world_md5": "4698f99b27a9971a8819b4436e8bf0d8", "persona": "Story"},
    "G2": {"root": "g", "path": "LC-S-6202", "md5": "b241a855c44f5150b8393089c90bc8bb",
           "world_md5": "48254060e4b119c029a3b409b601246b", "persona": "Story"},
    "G3": {"root": "g", "path": "LC-C-6203", "md5": "6a53506de6ef7a9b1bce8f9836bc25fb",
           "world_md5": "ad10200b32a63cc8780d22378faa5c96", "persona": "Catcher"},
    "G4": {"root": "g", "path": "LC-C-6204", "md5": "84247b70cd0e88783261a0459b442229",
           "world_md5": "a6fd383f89b219ee87b9ac4fc2db2dcc", "persona": "Catcher"},
    "G5": {"root": "g", "path": "LC-T-6205", "md5": "eb1aa3704ff7b37c7283fd53da5f52ab",
           "world_md5": "675d2df00dd2e0b515002e6f15e22a30", "persona": "Trainer"},
    "G6": {"root": "g", "path": "LC-T-6206", "md5": "16f23af7d6bf76f6490520b23c6049c9",
           "world_md5": "3987e9d13a57d07cd960d7b12e26fa22", "persona": "Trainer"},
    "C1": {"root": "c", "path": "probe-C1", "md5": "e909e5377ae54457dfb13b9e17946648",
           "world_md5": "a10e59061eff7e2782fb86bd16200b56", "persona": "Story"},
    "C2": {"root": "c", "path": "probe-C2", "md5": "6c9039355b86af9ffca529c618eda00f",
           "world_md5": "49b7a8c888ec877ec4e674171ad72a43", "persona": "Catcher"},
    "C3": {"root": "c", "path": "probe-C3", "md5": "bbcc172f3b2d51e8b5a5e5c3c8eeb581",
           "world_md5": "7059420eef7af06d7bc53c453628e82a", "persona": "Trainer"},
}
#: a pair whose WP1a chain missed takes its persona's next start (2.1): its G starts, then its C start
FALLBACKS = {"Story": ("G1", "G2", "C1"), "Catcher": ("G3", "G4", "C2"), "Trainer": ("G5", "G6", "C3")}
#: the planted walls of P1 and P2 (4.3): each ONE anchored edit to a staged copy (`apply_mutant`; `stage --mutant NAME`
#: refuses a name not listed here; the arms WALL-OLDALE and WALL-BRINEY are the stages built with `oldale` and `briney`).
#: Picked on wip/a1 a999429f (build plan step 5; its `ai_player/brain` and `ai_player/world` are main's), each with its
#: offline planner test (T39, T40: the walled copy finds no way in, the real one does, on the AI's own kept memory). Each
#: wall's facts are maps.json's (`ai_player/knowledge/world/maps.json`); `walls` keeps them, and T39/T40 assert they still
#: are the file's.
_OLDALE = "OLDALE_TOWN"
#: the maps a walk enters OLDALE TOWN from, and the side of each it lies past (maps.json: every connection whose `map` is
#: MAP_OLDALE_TOWN): ROUTE101's up, ROUTE102's right, ROUTE103's down
_OLDALE_INTO = {"ROUTE101": "up", "ROUTE102": "right", "ROUTE103": "down"}
_BRINEY = "ROUTE104_MR_BRINEYS_HOUSE"
#: every warp or door tile leading into MR. BRINEY's cottage (maps.json: every warp whose `dest_map` is
#: MAP_ROUTE104_MR_BRINEYS_HOUSE): ROUTE104's door at (17, 50), the only way in (the start memories' one link to 17:0)
_BRINEY_DOORS = (("ROUTE104", 17, 50),)
MUTANTS: dict[str, dict] = {
    # spec 4.3 P1: "the navigator's planner treats every tile of OLDALE_TOWN (0, 10) as a wall, and no go goal targets
    # it". The edit is in `step_from`, the planner's ONE step: under `astar` (the walk), `distances` (every reach: the
    # explorer's targets, `cut_off`, the parts of maps `route_to` and `region_hops` search) and `_Regions.landings`'
    # crossing of an edge. So a step refused there walls OLDALE for the walk, for every target and for every route or hop
    # into it, seen tiles and unseen ones alike (`Navigator.walls`, :816-820, holds the CURRENT map's seen tiles only, and
    # `route_to` plans every other map round `standing_walls`). Walled: on OLDALE every tile not past an edge seen crossed;
    # on a map that borders it every tile past the edge toward it once that edge was seen crossed, and past ROUTE101's up
    # edge always (a map's own coordinates begin at 0, so y < 0 is past its up edge before any crossing: how a New Game
    # first comes to OLDALE). Not walled: a down or right edge never crossed (the AI's data holds no map size).
    "oldale": {
        "file": "ai_player/brain/navigator.py",
        "anchor": "    nxt = moved(xy, direction)\n    if nxt in walls:\n        return None\n",
        "replacement": (
            "    nxt = moved(xy, direction)\n"
            "    # A1's planted wall WALL-OLDALE (frontier_probe.py MUTANTS['oldale'], spec 4.3 P1): a staged copy only\n"
            f"    side = {_OLDALE_INTO!r}.get(memory.const)\n"
            "    edge = memory.edges.get(side) if side is not None else None\n"
            f"    if (memory.const == {_OLDALE!r} and not memory.outside(nxt)) or (side == \"up\" and nxt[1] < 0) or (\n"
            "            edge is not None and (nxt[1] <= edge if side == \"up\" else nxt[1] >= edge if side == \"down\"\n"
            "                                  else nxt[0] <= edge if side == \"left\" else nxt[0] >= edge)):\n"
            "        return None\n"
            "    if nxt in walls:\n"
            "        return None\n"),
        "walls": {"map": _OLDALE, "into": _OLDALE_INTO},
    },
    # spec 4.3 P2: "WALL-BRINEY walls ROUTE104_MR_BRINEYS_HOUSE (17, 0) and, since the house is entered only by its door
    # warp on ROUTE104, every warp or door tile leading to (17, 0), including those the start's memory knows". A door is
    # used only by pressing into it from a stand tile, and `_approaches` is the one place that stand is found for both the
    # explorer's exit targets (`candidates`) and the warp hops of `route_to` and `region_hops` (`_Regions.landings`). It
    # keys on the TILE, so a link the start's memory holds there is walled exactly as a door only seen. Not walled: the
    # house's own tiles (no way reaches them but the door); `skills/story.py` enter_door, which walks to a door by a
    # POKeMON CENTER's or a MART's look only
    "briney": {
        "file": "ai_player/brain/explore.py",
        "anchor": "    fact = memory.fact(exit_tile)\n    asked = exit_press(fact.behavior) if fact is not None else None\n",
        "replacement": (
            "    fact = memory.fact(exit_tile)\n"
            "    # A1's planted wall WALL-BRINEY (frontier_probe.py MUTANTS['briney'], spec 4.3 P2): a staged copy only\n"
            f"    if (memory.const, int(exit_tile[0]), int(exit_tile[1])) in {_BRINEY_DOORS!r}:\n"
            "        return []\n"
            "    asked = exit_press(fact.behavior) if fact is not None else None\n"),
        "walls": {"map": _BRINEY, "doors": _BRINEY_DOORS},
    },
}
LINKS = ("modules", "plugins", "mgba", "roms")


class Refusal(Exception):
    """A batch, a stage, a plan or a job the probe refuses: the message says why."""


# ====================================================================== small helpers
def utf8_safe(value: object) -> object:
    return LC.utf8_safe(value)


def untrusted(value: object, limit: int = 300) -> str | None:
    """A value the AI wrote, kept as text, utf8-safe, at most `limit` characters (None stays None)."""
    text = LC.untrusted_text(value)
    return None if text is None else text[:limit]


def md5_of(path: Path) -> str | None:
    try:
        digest = hashlib.md5()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def sha256_of(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def key_id(key: list) -> str:
    """12 hex of the key JSON's sha1 (3.7)."""
    return hashlib.sha1(json.dumps(list(key), ensure_ascii=True).encode("utf-8")).hexdigest()[:12]


def write_json(path: Path, data) -> None:
    """`data` as JSON, written whole (a temp file, then os.replace), every str made writable as UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(utf8_safe(data), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(temp, path)


def read_json(path: Path) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def last_line_of(path: Path) -> bytes | None:
    """The last non-blank line of a file, streamed (never a whole-file read), or None."""
    last = None
    try:
        with open(path, "rb") as handle:
            for raw in handle:
                if raw.strip():
                    last = raw
    except OSError:
        return None
    return last


def last_parsed_object(path: Path) -> dict | None:
    """The last line of a world file that parses as a JSON object (a line cut by a kill is skipped), streamed."""
    keep: list[bytes] = []
    try:
        with open(path, "rb") as handle:
            for raw in handle:
                if raw.strip():
                    keep = (keep + [raw])[-2:]
    except OSError:
        return None
    for raw in reversed(keep):
        try:
            data = json.loads(raw)
        except Exception:  # noqa: BLE001 - the AI's file is untrusted
            continue
        if isinstance(data, dict):
            return data
    return None


def parse_object(raw: bytes | str | None) -> dict | None:
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001 - the AI's file is untrusted
        return None
    return data if isinstance(data, dict) else None


@contextlib.contextmanager
def locked(path: Path, wait: float = 60.0):
    """An exclusive lock file beside `path` (O_CREAT | O_EXCL), as `ledger._locked`."""
    lock = path.with_name(path.name + ".lock")
    began = time.monotonic()
    while True:
        try:
            handle = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() - began > wait:
                raise Refusal(f"{lock} is held for over {wait:.0f} s")
            time.sleep(0.05)
    try:
        os.write(handle, f"{os.getpid()}\n".encode())
        os.close(handle)
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def read_records(out: Path) -> list[dict]:
    """Every record of `<out>/records.jsonl` that parses (an unreadable line is skipped)."""
    path = Path(out) / RECORDS
    found: list[dict] = []
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                data = parse_object(line)
                if data is not None:
                    found.append(data)
    except OSError:
        return []
    return found


def append_record(out: Path, record: dict, name: str = RECORDS) -> bool:
    """ONE line appended to `<out>/<name>` under a lock. A record whose `run_id` (a leg) or `job` (a job record) is already
    there is NOT written again (a resume never writes one twice): False."""
    path = Path(out) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(utf8_safe(record), ensure_ascii=False, default=str)
    with locked(path):
        if name == RECORDS:
            for old in read_records(out):
                if old.get("record") == record.get("record") == "leg" and old.get("run_id") == record.get("run_id"):
                    return False
                if old.get("record") == record.get("record") == "job" and old.get("job") == record.get("job"):
                    return False
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return True


# ====================================================================== the end classes (3.5)
def _host_codes() -> tuple[set[int], set[int]]:
    """(the budget ends' codes: wall-clock and frame-budget, per `launcher._HOST_CODES`; the other involuntary ends' codes:
    crash 2, parked-manual or abandoned 3, interrupted 130)."""
    from ai_player.host import launcher

    budget = {launcher._HOST_CODES["wall-clock"], launcher._HOST_CODES["frame-budget"]}
    other = {code for reason, code in launcher._HOST_CODES.items()
             if reason in launcher._INVOLUNTARY and reason != "frame-budget"}
    return budget, other


def gate_timeout_text() -> str:
    from ai_player.host import launcher

    return f"FAIL the purity gate did not finish within {launcher.GATE_TIMEOUT_SECONDS}s"


def ran_out(frames: object, real: object) -> bool:
    """The launcher's `_ran_out`: the frame budget really ran out by the host's count (both whole numbers, real >= frames)."""
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (frames, real)):
        return False
    return frames > 0 and real >= frames


def classify(f: dict) -> tuple[str, str]:
    """THE END CLASS of a leg, from files (3.5, D14 changed; the first matching rule wins). `f`: guard ("world" or
    "profile": the probe's guard killed the launch, CUT-WORLD; "abort": the disk guard's ABORT killed it), salvaged, refusal
    (the child's own: profile, donor, custody), exit, stdout, verdict (the verdict file or None), driver_killed, launch_died,
    fresh (L5.THIS_RUN PASS), end_truth (read), frames (the leg's budget), mc. Returns (class, why).
    One clarification of the table, said: a REFUSAL (exit 7, or exit 2 with no verdict file) is judged before `launch_died`,
    because a launch the gate refused also played no frame and would otherwise read as a dead launch (INFRA, never counted)."""
    from ai_player.host import launcher

    guard = f.get("guard")
    if guard == "world":
        return CUT_WORLD, CUT_TEXT_MC if f.get("mc") else CUT_TEXT
    if guard == "profile":
        return CUT_WORLD, CUT_PROFILE_TEXT
    code = f.get("exit")
    stdout = str(f.get("stdout") or "")
    verdict = f.get("verdict") if isinstance(f.get("verdict"), dict) else None
    if code == launcher.GATE_REFUSED_EXIT and gate_timeout_text() in stdout:
        return INFRA, "a purity-gate TIMEOUT (the gate did not finish in time): the harness, not the AI"
    if f.get("driver_killed"):
        return INFRA, "run_arm's driver killed the launcher (it overran its wall clock + 300 s)"
    if guard == "abort":
        return INFRA, "the disk guard's ABORT killed the launch"
    if f.get("salvaged"):
        return INFRA, f"salvaged by the orchestrator ({f.get('salvaged')})"
    if f.get("refusal"):
        return REFUSED, f"refused by the child: {f.get('refusal')}"
    if code == launcher.GATE_REFUSED_EXIT:
        return REFUSED, "the purity gate refused the launch (exit 7)"
    if code == 2 and verdict is None:
        return REFUSED, "the launcher refused before a launch (exit 2, no verdict file)"
    if f.get("launch_died"):
        return INFRA, str(f.get("launch_died"))
    if code == launcher.WALL_CLOCK_EXIT and verdict is None:
        return HUNG, HUNG_TEXT
    if code == launcher.NO_VERDICT_EXIT:
        return NOT_CLEAN, "exit 8: the launcher saw no certified CLEAN verdict"
    if verdict is not None and verdict.get("verdict") != "CLEAN":
        return NOT_CLEAN, f"the verdict file reads {untrusted(verdict.get('verdict'), 40)!r}, not CLEAN"
    if verdict is None:
        return NOT_CLEAN, f"exit {code} with no verdict file"
    if not f.get("fresh") or not f.get("end_truth"):
        return INFRA, ("a CLEAN verdict whose state is not this run's (L5.THIS_RUN fails)" if not f.get("fresh")
                       else "a CLEAN verdict whose end truth cannot be read")
    facts = verdict.get("facts") if isinstance(verdict.get("facts"), dict) else {}
    counters = verdict.get("counters") if isinstance(verdict.get("counters"), dict) else {}
    reason = facts.get("exit_reason") if isinstance(facts.get("exit_reason"), str) else ""
    budget_codes, other_codes = _host_codes()
    if code in budget_codes:
        return CLEAN_BUDGET, f"a host budget end (exit {code})"
    if code == 0 and reason.startswith("play: stopped:") and ran_out(f.get("frames"), counters.get("real_frames")):
        return CLEAN_BUDGET, "play: stopped: with the frame budget run out (the launcher's _ran_out)"
    if code in other_codes:
        return CLEAN_INVOLUNTARY, f"an involuntary host end (exit {code})"
    if code == 0 and reason.startswith(("play: done:", "play: stuck:", "play: stopped:")):
        return CLEAN_CHOSEN, "its own choice (done, stuck, or stopped before its budget ran out)"
    return NOT_CLEAN, f"a CLEAN verdict with an end no class names (exit {code}, {untrusted(reason, 80)!r})"


# ====================================================================== the next unmet milestone (3.8)
def milestone_proof(milestone: dict) -> dict:
    """A milestone's proof as `live_chain.legs_of` builds a leg's."""
    done = milestone.get("done") or {}
    return {"flags": {k: int(v) for k, v in (done.get("flags") or {}).items()},
            "variables": {k: {"number": int(v["number"]), "at_least": int(v["at_least"])}
                          for k, v in (done.get("variables") or {}).items()},
            "trainers": {k: int(v) for k, v in (done.get("trainers") or {}).items()}}


def next_unmet(marks: dict | None, data: dict) -> dict:
    """The first milestone of the staged `milestones.json` (file order; optional ones and waypoints skipped) whose proof does
    not hold on `marks`; a proof whose mark the truth did not return is UNREAD (listed, never counted). `held`: every
    milestone whose proof holds (optional ones included: they are reported, never targeted)."""
    found: str | None = None
    unread: list[str] = []
    held: list[str] = []
    if marks is None:
        return {"next": None, "unread": [], "held": []}
    for milestone in data.get("milestones") or []:
        proof = milestone_proof(milestone)
        if not (proof["flags"] or proof["variables"] or proof["trainers"]):
            continue
        result = LC.proof_holds(marks, proof)
        if result["held"]:
            held.append(milestone["id"])
            continue
        if milestone.get("optional") or milestone.get("waypoint") is not None:
            continue
        if result["missing"]:
            if found is None:
                unread.append(milestone["id"])
            continue
        if found is None:
            found = milestone["id"]
    return {"next": found, "unread": unread, "held": held}


def end_written(before: dict | None, after: dict | None, written: bool) -> bool:
    """The end state was written by this run after its start, with a new md5 (3.5: the next unmet is read on it)."""
    if not after or not written:
        return False
    return (before or {}).get("state_md5") != after.get("state_md5")


def truth_for_next(before: dict | None, after: dict | None, written: bool) -> tuple[dict | None, str]:
    """(the truth the next unmet is read on, "end" | "start" | "none")."""
    if end_written(before, after, written):
        return after, "end"
    if before:
        return before, "start"
    return None, "none"


# ====================================================================== the key (3.8)
def reason_norm(text: str | None) -> str:
    """Digit runs made N, whitespace collapsed, cut at REASON_CUT characters."""
    value = re.sub(r"\d+", "N", str(text or ""))
    return re.sub(r"\s+", " ", value).strip()[:REASON_CUT]


def raise_windows(records: Iterable[dict]) -> tuple[list[list], bool]:
    """The boss-prep RAISE goals of a leg's action log: [[its goal record's frame, its goal_end's frame or None]], and
    whether one is still ACTIVE at the leg's end (a `goal` record of action `raise` with no `goal_end` after it)."""
    windows: list[list] = []
    open_at: int | None = None
    for record in records:
        if not isinstance(record, dict):
            continue
        frame = record.get("frame") if isinstance(record.get("frame"), int) else None
        decision = record.get("decision")
        if decision == "goal":
            if open_at is not None:
                windows.append([open_at, frame])
                open_at = None
            if record.get("action") == "raise" and frame is not None:
                open_at = frame
        elif decision == "goal_end" and open_at is not None:
            windows.append([open_at, frame])
            open_at = None
    active = open_at is not None
    if active:
        windows.append([open_at, None])
    return windows, active


def _in_windows(frame: int, windows: list[list]) -> bool:
    return any(start <= frame and (end is None or frame <= end) for start, end in windows)


def leg_transitions(world: dict | None, start_frame: int | None) -> list[list]:
    """The world tail's transitions NEWER than the start truth's frame (a carried prefix is the previous kept line's)."""
    start = start_frame if isinstance(start_frame, int) else -1
    out = []
    for item in (world or {}).get("transitions") or []:
        if (isinstance(item, list) and len(item) >= 3 and isinstance(item[0], int) and not isinstance(item[0], bool)
                and item[0] > start):
            out.append(item)
    return out


def map_name(world: dict | None, key: object) -> str:
    """A map's const by the snapshot's own `maps[key].const`, else its key."""
    entry = ((world or {}).get("maps") or {}).get(str(key))
    const = entry.get("const") if isinstance(entry, dict) else None
    return str(const) if const else str(key)


def loop_measure(world: dict | None, start_frame: int | None, end_frame: int | None, leg_frames: int | None,
                 records: Iterable[dict]) -> dict:
    """THE LOOP SIGNATURE (3.8): per unordered map pair, the crossings either way (edges and warps alike) of the leg's own
    transitions; `crossings_raise` the ones made while a raise goal was ACTIVE. Keeps the top pair (most crossings outside a
    raise, then most crossings, then by name), its window, the frames from its last crossing to the leg's end, the AI's own
    `stuck: ping-pong` goal ends, and whether a raise is still active at the end."""
    records = [r for r in records if isinstance(r, dict)]
    windows, active = raise_windows(records)
    transitions = leg_transitions(world, start_frame)
    pairs: dict[str, dict] = {}
    for item in transitions:
        a, b = map_name(world, item[1]), map_name(world, item[2])
        if a == b:
            continue
        name = "|".join(sorted((a, b)))
        entry = pairs.setdefault(name, {"crossings": 0, "crossings_raise": 0, "first": item[0], "last": item[0]})
        entry["crossings"] += 1
        if _in_windows(item[0], windows):
            entry["crossings_raise"] += 1
        entry["first"] = min(entry["first"], item[0])
        entry["last"] = max(entry["last"], item[0])
    pingpong = sum(1 for r in records if r.get("decision") == "goal_end"
                   and str(r.get("reason") or "").startswith("stuck: ping-pong"))
    entered = len({map_name(world, item[2]) for item in transitions})
    out = {"pair": None, "crossings": 0, "crossings_raise": 0, "share": 0.0, "window": None, "window_share": None,
           "last_to_end": None, "pingpong_ends": pingpong, "transitions_in_leg": len(transitions), "maps_entered": entered,
           "raise_active_at_end": active, "keyed": "none", "churn": False}
    if not pairs:
        return out
    name, top = sorted(pairs.items(), key=lambda kv: (-(kv[1]["crossings"] - kv[1]["crossings_raise"]),
                                                       -kv[1]["crossings"], kv[0]))[0]
    played = (end_frame - start_frame) if isinstance(end_frame, int) and isinstance(start_frame, int) else None
    span = played if played and played > 0 else leg_frames
    out.update({"pair": name, "crossings": top["crossings"], "crossings_raise": top["crossings_raise"],
                "share": round(top["crossings"] / len(transitions), 4), "window": [top["first"], top["last"]],
                "window_share": round((top["last"] - top["first"]) / span, 4) if span else None,
                "last_to_end": (end_frame - top["last"]) if isinstance(end_frame, int) else None})
    return out


def loop_keyed(loop: dict | None, reached: bool, klass: str, reason: str) -> str:
    """"LOOP" when ALL of 3.8's five hold; "flag" when (1) and (2) hold and (3), (4) or (5) fails (the leg keeps its own
    key, listed under "loops seen"); else "none"."""
    if reached or not loop or not loop.get("pair"):
        return "none"
    if loop["crossings"] - loop["crossings_raise"] < LOOP_MIN_CROSSINGS:
        return "none"
    end_ok = klass in (CLEAN_BUDGET, CUT_WORLD) or (klass == CLEAN_CHOSEN and reason.startswith("play: stuck: no progress"))
    near = isinstance(loop.get("last_to_end"), int) and loop["last_to_end"] <= LOOP_END_FRAMES
    if end_ok and near and not loop.get("raise_active_at_end"):
        return "LOOP"
    return "flag"


def blocker_of(chapter: int, nxt: str | None, reason: str, end_const: str | None, klass: str, reached: bool,
               loop: dict | None) -> dict | None:
    """The leg's blocker (None when reached or not a blocker class): the exact key (chapter, next unmet, reason, end map,
    class) or the LOOP key (chapter, "-", "loop", "<A>|<B>", "LOOP"); the five raw values are always kept."""
    if reached or klass not in BLOCKER_CLASSES:
        return None
    raw = [chapter, nxt or "-", reason, end_const or "UNKNOWN", klass]
    if (loop or {}).get("keyed") == "LOOP":
        key = [chapter, "-", "loop", loop["pair"], "LOOP"]
    else:
        key = list(raw)
    return {"key": key, "key_id": key_id(key), "raw": raw}


# ====================================================================== the AI's own measures (3.7)
K1_TELL = re.compile(r"\[AI-GOALS\] (?P<goal>\S+) is somewhere it has not been: first to (?P<lead>[^,]+), "
                     r"a seasoned player's knowledge")
GONE = re.compile(r"^not picked up: no item ball where it lay at \((?P<x>-?\d+), (?P<y>-?\d+)\) any more")
TRAINER_TELL = "battle: a trainer battle against "
PARTY = re.compile(r"party=\[([^\]]*)\]")
WHERE = re.compile(r" (?P<name>[A-Z][A-Z .0-9'-]+)\((?P<group>\d+),(?P<number>\d+)\) xy=")
PLAN_LINE = re.compile(r"\[AI-BOSSPREP\] (?P<boss>[^:]+): the plan: raise (?P<species>\S+) \([0-9a-f]+\) from "
                       r"L(?P<level>\d+) to L(?P<target>\d+) as the one who leads \([^)]*\); (?P<how>[^;]*);")
NO_PLAN_LINE = re.compile(r"\[AI-BOSSPREP\] (?P<boss>[^:]+): no plan \((?P<why>[^)]*)\)")
MEMORY_PREFIX = "[AI-WORLD] memory from "


def tells(records: Iterable[dict]) -> list[dict]:
    return [r for r in records if isinstance(r, dict) and r.get("decision") == "tell"]


def k1_leads(records: Iterable[dict]) -> dict:
    """K1's leads (3.7): the AI's tells of the form `[AI-GOALS] <map> is somewhere it has not been: first to <lead>, a
    seasoned player's knowledge: ...` (`brain/goals.py` WAY_IN, entry_lead): their count, and per lead its goal map, lead
    map and first frame."""
    count = 0
    leads: dict[tuple[str, str], int | None] = {}
    for record in tells(records):
        hit = K1_TELL.search(str(record.get("reason") or ""))
        if hit is None:
            continue
        count += 1
        pair = (hit["goal"], hit["lead"].strip())
        if pair not in leads:
            leads[pair] = record.get("frame") if isinstance(record.get("frame"), int) else None
    return {"count": count, "leads": [{"goal": goal, "lead": lead, "first": first}
                                      for (goal, lead), first in leads.items()]}


def tried_items_of(snapshot: dict | None) -> set[str] | None:
    """The tiles of a goal snapshot's `tried_items` ("<map key>|x,y"), or None for no snapshot."""
    if not isinstance(snapshot, dict):
        return None
    goals = ((snapshot.get("memory") or {}).get("goals") or {}) if isinstance(snapshot.get("memory"), dict) else {}
    value = goals.get("tried_items") if isinstance(goals, dict) else None
    if isinstance(value, dict) and len(value) == 1:
        value = next(iter(value.values()))
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value if isinstance(item, str)}


def losses_of(snapshot: dict | None) -> int:
    memory = (snapshot or {}).get("memory") if isinstance(snapshot, dict) else None
    value = memory.get("losses") if isinstance(memory, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def gone_outcomes(records: Iterable[dict]) -> list[str | None]:
    """The tiles ("<map key>|x,y", from the `goal_end`'s key `item:<map>|x,y`) of every `not picked up: no item ball where
    it lay at (x, y) any more` outcome."""
    out: list[str | None] = []
    for record in records:
        if not isinstance(record, dict) or record.get("decision") != "goal_end":
            continue
        if not GONE.match(str(record.get("reason") or "")):
            continue
        extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
        key = extra.get("key") if isinstance(extra.get("key"), str) else None
        out.append(key[len("item:"):] if key and key.startswith("item:") else None)
    return out


def stale_measure(mode: str, tried: set[str] | None, records: Iterable[dict], memory_line: str | None) -> dict:
    """`measures.stale` (3.7): `mode` is the yardstick snapshot's ("carried", "kept": present at the start but not carried,
    or "none"); `item_errands` the DISTINCT tiles of its `tried_items` with a "gone" outcome in the leg, `item_outcomes`
    those outcomes counted, `gone_or_unreachable` the same message on any other tile; both are "unknown" only when the
    start has no snapshot at all (then every such outcome is counted as `gone_or_unreachable`)."""
    tiles = gone_outcomes(records)
    if mode == "none" or tried is None:
        return {"snapshot": "none", "item_errands": "unknown", "item_outcomes": "unknown",
                "gone_or_unreachable": len(tiles), "memory_line": memory_line}
    inside = [tile for tile in tiles if tile is not None and tile in tried]
    return {"snapshot": mode, "item_errands": len(set(inside)), "item_outcomes": len(inside),
            "gone_or_unreachable": len(tiles) - len(inside), "memory_line": memory_line}


def memory_line_of(log_text: str | None) -> str | None:
    for line in str(log_text or "").splitlines():
        if MEMORY_PREFIX in line:
            return line.strip()[:600]
    return None


def bossprep_fields(records: list[dict], log_text: str | None, persona: str, end_frame: int | None) -> dict:
    """Boss preparation as the AI wrote it (3.7; reported, never a class): who acts, the plan (or `no plan (<why>)`), the
    raise goals and raise battles, how the raise ended, the battles lost on the gym map and elsewhere."""
    plan: object = None
    plan_frame = None
    for record in tells(records):
        reason = str(record.get("reason") or "")
        hit = PLAN_LINE.search(reason)
        if hit is not None:
            plan = {"boss": hit["boss"].strip(), "trainee": hit["species"], "from": int(hit["level"]),
                    "target": int(hit["target"]), "option": hit["how"].strip()[:120]}
            plan_frame = record.get("frame") if isinstance(record.get("frame"), int) else None
            continue
        hit = NO_PLAN_LINE.search(reason)
        if hit is not None and plan is None:
            plan = f"no plan ({hit['why']})"
    lines = str(log_text or "").splitlines()
    told = [str(r.get("reason") or "") for r in tells(records)]
    texts = lines if lines else told
    _, active = raise_windows(records)
    raise_end = None
    if active:
        raise_end = "still active at the leg's end"
    elif any("the raise ends, budget spent" in line for line in texts):
        raise_end = "budget spent"
    elif any("the raise is done" in line for line in texts):
        raise_end = "target reached"
    elif any("is no longer in the party" in line for line in texts):
        raise_end = "trainee left"
    boss_losses = sum(1 for line in texts if "a battle lost on the gym map (" in line)
    lost = sum(1 for r in records if _is_battle(r) and (r.get("extra") or {}).get("outcome") == "lost")
    return {"acting": "acts" if persona in BOSSPREP_ACTING else "logs only", "plan": plan,
            "raise_goals": sum(1 for r in records if isinstance(r, dict) and r.get("decision") == "goal"
                               and r.get("action") == "raise"),
            "raise_battles": sum(1 for line in texts if "[AI-BOSSPREP] raise battle:" in line), "raise_end": raise_end,
            "boss_losses": boss_losses, "other_losses": max(0, lost - boss_losses),
            "frames_from_plan": (end_frame - plan_frame) if isinstance(end_frame, int) and isinstance(plan_frame, int)
            else None}


def rides_delta(start_world: dict | None, end_world: dict | None) -> dict:
    """The rides used in the leg (a `uses` delta against the start's line) and the ones found closed (3.7)."""
    before = (start_world or {}).get("rides") if isinstance((start_world or {}).get("rides"), dict) else {}
    after = (end_world or {}).get("rides") if isinstance((end_world or {}).get("rides"), dict) else {}
    used = {}
    for name, ride in after.items():
        if not isinstance(ride, dict):
            continue
        old = before.get(name) if isinstance(before.get(name), dict) else {}
        try:
            delta = int(ride.get("uses") or 0) - int(old.get("uses") or 0)
        except (TypeError, ValueError):
            continue
        if delta > 0:
            used[name] = delta
    closed = sorted(name for name, ride in after.items() if isinstance(ride, dict) and ride.get("closed"))
    return {"used": used, "closed": closed}


# ====================================================================== the experience extract (3.9, D16)
#: the world's per-game keys, dropped silently; any OTHER key is dropped AND listed
WORLD_DROPPED = ("transitions", "tiles_learned", "news", "heard", "news_log", "spoke")
MAP_DROPPED = ("visits", "closed", "people", "persons", "met", "items", "arrivals", "first_frame")
WARP_KEPT = ("to", "arrival", "direction", "inferred")
WARP_DROPPED = ("uses", "first", "last", "by")
CONNECTION_KEPT = ("source", "target", "direction", "from", "arrival", "offset")
CONNECTION_DROPPED = ("by", "frame")
RIDE_KEPT = ("from", "to", "arrival", "who", "gfx", "tile", "words", "place", "via")
RIDE_DROPPED = ("first", "last", "uses", "closed")
BUMP_KEPT = ("from", "direction")
BUMP_DROPPED = ("first", "last", "bumps")


def _filtered(item: dict, kept: tuple, dropped: tuple, where: str, unclassified: list[str]) -> dict:
    out = {}
    for name, value in item.items():
        if name in kept:
            out[name] = value
        elif name not in dropped:
            unclassified.append(f"{where}.{name}")
    return out


def extract_static(world: dict | None) -> tuple[dict, list[str]]:
    """THE STATIC FACTS of a world tail, by ALLOW-LIST (3.9): warps, connections, landmarks, rides, and per map its key,
    name, const, tile fields, tiles (4 of 7 compact fields), edges and bumps; every per-game fact dropped; any key no list
    names dropped AND listed in `unclassified` (fail closed). Read as JSON, with no AI import."""
    unclassified: list[str] = []
    out: dict = {"maps": {}, "warps": {}, "connections": [], "landmarks": {}, "rides": {}}
    world = world if isinstance(world, dict) else {}
    for name, value in world.items():
        if name == "maps" and isinstance(value, dict):
            for key, entry in sorted(value.items()):
                if not isinstance(entry, dict):
                    unclassified.append(f"maps.{key}")
                    continue
                if list(entry.get("tile_fields") or []) != list(TILE_FIELDS):
                    unclassified.append(f"maps.{key} (its tile_fields differ: dropped)")
                    continue
                kept = {"key": entry.get("key"), "name": entry.get("name"), "const": entry.get("const"),
                        "tile_fields": list(TILE_FIELDS[:TILE_STATIC]), "tiles": {}, "edges": {}, "bumped": {}}
                for field_name, field_value in entry.items():
                    if field_name in ("key", "name", "const", "tile_fields"):
                        continue
                    if field_name == "tiles" and isinstance(field_value, dict):
                        kept["tiles"] = {xy: list(fact[:TILE_STATIC]) for xy, fact in sorted(field_value.items())
                                         if isinstance(fact, list)}
                    elif field_name == "edges" and isinstance(field_value, dict):
                        kept["edges"] = dict(field_value)
                    elif field_name == "bumped" and isinstance(field_value, dict):
                        for bump, info in sorted(field_value.items()):
                            if not isinstance(info, dict):
                                continue
                            item = _filtered(info, (*BUMP_KEPT, "slid"), BUMP_DROPPED, f"maps.{key}.bumped.{bump}",
                                             unclassified)
                            kept["bumped"][bump] = item
                    elif field_name not in MAP_DROPPED:
                        unclassified.append(f"maps.{key}.{field_name}")
                out["maps"][key] = kept
        elif name == "warps" and isinstance(value, dict):
            out["warps"] = {key: _filtered(link, WARP_KEPT, WARP_DROPPED, f"warps.{key}", unclassified)
                            for key, link in sorted(value.items()) if isinstance(link, dict)}
        elif name == "connections" and isinstance(value, list):
            seen = set()
            for item in value:
                if not isinstance(item, dict):
                    continue
                kept = _filtered(item, CONNECTION_KEPT, CONNECTION_DROPPED, "connections[]", unclassified)
                text = json.dumps(kept, sort_keys=True)
                if text not in seen:
                    seen.add(text)
                    out["connections"].append(kept)
        elif name == "landmarks" and isinstance(value, dict):
            out["landmarks"] = dict(sorted(value.items()))
        elif name == "rides" and isinstance(value, dict):
            out["rides"] = {key: _filtered(ride, RIDE_KEPT, RIDE_DROPPED, f"rides.{key}", unclassified)
                            for key, ride in sorted(value.items()) if isinstance(ride, dict)}
        elif name not in WORLD_DROPPED:
            unclassified.append(name)
    return out, sorted(set(unclassified))


def _is_battle(record: object) -> bool:
    """`live_step5.is_battle` (the navigator's record of a battle its battler played)."""
    if not isinstance(record, dict):
        return False
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    return record.get("decision") == "world" and "kind" in extra and "outcome" in extra


def fights_of(records: Iterable[dict]) -> tuple[list[dict], dict]:
    """Per trainer battle: the foe as shown (the newest earlier tell `battle: a trainer battle against ...`; no other tell
    is read, so a K1 lead's tell never names a foe), the party as the AI saw it (the record's `party=[...]`), the outcome and
    the map; wild battles counted. Never the truth's fields (PIDs, experience): live hidden state (USER RULING 40)."""
    fights: list[dict] = []
    wild = {"met": 0, "won": 0, "lost": 0, "ran": 0, "caught": 0, "other": 0}
    foe = None
    for record in records:
        if not isinstance(record, dict):
            continue
        reason = str(record.get("reason") or "")
        if record.get("decision") == "tell" and reason.startswith(TRAINER_TELL):
            foe = reason[len(TRAINER_TELL):][:120]
            continue
        if not _is_battle(record):
            continue
        extra = record.get("extra") or {}
        digest = str(record.get("digest") or "")
        party = PARTY.search(digest)
        where = WHERE.search(digest)
        if extra.get("kind") == "trainer":
            fights.append({"foe": foe, "party": party.group(1)[:200] if party else None,
                           "outcome": untrusted(extra.get("outcome"), 20),
                           "map": f"{where['group']}:{where['number']}" if where else None})
            foe = None
        elif extra.get("kind") == "wild":
            wild["met"] += 1
            outcome = extra.get("outcome")
            wild[outcome if outcome in ("won", "lost", "ran", "caught") else "other"] += 1
    return fights, wild


# ====================================================================== the environment (3.11)
def sanitize_environ(environ: dict | None = None) -> list[str]:
    """Remove every AI_PLAYER_* (AI_PLAYER_BUILD_ROOT included), every POKEBOT_* and every PYTHON* that
    `live_chain.python_env_refused` refuses from `environ` (default: this process's). Returns the names removed."""
    environ = os.environ if environ is None else environ
    removed = sorted(name for name in list(environ) if name.upper().startswith(STRIPPED_PREFIXES)
                     or LC.python_env_refused(name))
    for name in removed:
        environ.pop(name, None)
    return removed


def env_problems(env: dict | None, mc: bool = False) -> list[str]:
    """A job's environment keys against D17's allow-list (3.11): any other key (a FAULT switch, a POKEBOT_* or PYTHON*
    variable) is refused; AI_PLAYER_GOALS is never an MC job's."""
    problems = []
    for name in sorted(env or {}):
        if name not in ENV_ALLOWED:
            problems.append(f"the environment key {name} is not on the allow-list {list(ENV_ALLOWED)}")
    if mc and ENV_GOALS in (env or {}):
        problems.append(f"an MC job never sends {ENV_GOALS} (E0's harness, 2.4b)")
    return problems


# ====================================================================== the disk (3.12)
def world_cut(mc: bool = False) -> int:
    """The world cut: A1's 1,000,000,000 bytes, or for an MC job live_chain's own guard, READ now (never copied)."""
    return LC.GUARD_WORLD_BYTES if mc else WORLD_CUT_BYTES


def profile_budget(mc: bool = False) -> int:
    return LC.GUARD_WORLD_BYTES + MC_PROFILE_MARGIN_BYTES if mc else PROFILE_BUDGET_BYTES


def disk_decision(world_bytes: int | None, free_gb: float | None, out_bytes: int | None,
                  profile_bytes: int | None = None, mc: bool = False) -> str | None:
    """THE disk rule (3.12; strict comparisons: each boundary value passes), in order: "abort" (free under ABORT_FREE_GB),
    "cut-world" (the newest world.jsonl over the cut), "drop" (--out over its cap: the pending jobs are dropped),
    "cut-profile" (the job's profile folder over its budget), or None. The tick asks it about ONE measurement at a time,
    in the tick's own order (the free space; each running job's newest world.jsonl; --out; each job's profile folder), so
    every comparison of the running batch is made here and nowhere else (verifier round 1, F1: the tick had its own)."""
    if free_gb is not None and free_gb < ABORT_FREE_GB:
        return "abort"
    if world_bytes is not None and world_bytes > world_cut(mc):
        return "cut-world"
    if out_bytes is not None and out_bytes > OUT_CAP_BYTES:
        return "drop"
    if profile_bytes is not None and profile_bytes > profile_budget(mc):
        return "cut-profile"
    return None


def start_refusal(free_gb: float | None) -> str | None:
    """A batch never starts under START_FREE_GB free on the drive of --out or a stage (D11's AI-only floor)."""
    if free_gb is None:
        return "the free space could not be read"
    if free_gb < START_FREE_GB:
        return f"{free_gb:.2f} GB free, under the {START_FREE_GB:g} GB start floor"
    return None


def p_fit(free_gb: float, mc: bool = False) -> int:
    """How many jobs fit the disk at once (2.7): floor((free - 40 - 0.6 - 0.4 - 2.0) / 1.25), an MC batch / 1.75."""
    per = MC_PER_JOB_GB if mc else PER_JOB_GB
    room = free_gb - ABORT_FREE_GB - OUT_ESTIMATE_GB - STAGES_GB - P_MARGIN_GB
    return math.floor(round(room / per, 6))


def parallel_of(asked: int, free_gb: float, mc: bool = False) -> tuple[int, str | None]:
    """(min(P, P_fit), None) or (0, why) when P_fit < 1 (refused, exit 2)."""
    fit = p_fit(free_gb, mc)
    if fit < 1:
        return 0, f"P_fit {fit} at {free_gb:.2f} GB free: no job fits the disk"
    return min(asked, fit, P_MAX), None


def leg_fits(now: float, leg: dict, deadline: float | None) -> bool:
    """No launch when now + wall + 300 + 2 x 600 would pass the deadline (3.13)."""
    return deadline is None or now + float(leg["wall"]) + LEG_MARGIN_SECONDS <= deadline


def job_watchdog_seconds(job: dict) -> int:
    """A child alive past this is killed and salvaged (`live_chain.chain_watchdog_seconds` of its legs)."""
    return LC.chain_watchdog_seconds(job.get("legs") or [])


# ====================================================================== the continue rule (3.6) and custody (C5)
def purity_wrong(row: dict) -> list[str]:
    statuses = {c["id"]: c["status"] for c in row.get("checks") or [] if c.get("id") in LC.PURITY_IDS}
    return [f"{i} {statuses.get(i, 'MISSING')}" for i in LC.PURITY_IDS if statuses.get(i) != LC.PASS]


def continue_rule(row: dict, klass: str, stop_seen: bool, carries_goals: bool = False) -> tuple[bool, str]:
    """THE CONTINUE RULE of an A1 leg (3.6): C1 `leg_reached`; C2 a CLEAN-* class and every PURITY_IDS check PASS; C3 the
    world measured and its kept last line parsing (and, in a job that carries goal snapshots, the snapshot kept: a
    soft-deadline or killed end writes none); C4 not guard-cut; C5 custody (checked before the leg's launch, kept in
    `row["custody"]`); C6 no STOP.txt. The world SIZE is reported, never a condition (live_chain's 300 MB cap is not)."""
    why: list[str] = []
    reached, text = LC.leg_reached(row)
    if not reached:
        why.append(f"C1 {row.get('target')} not reached: {text}")
    if klass not in CLEAN_CLASSES:
        why.append(f"C2 the class is {klass}, not CLEAN-*")
    wrong = purity_wrong(row)
    if wrong:
        why.append(f"C2 purity not clean: {', '.join(wrong)}")
    size = (row.get("world_file") or {}).get("bytes")
    world = (row.get("measures") or {}).get("world") or {}
    if not isinstance(size, int):
        why.append("C3 its world.jsonl was not measured")
    if not world.get("last_ok"):
        why.append(f"C3 its world.jsonl's last line did not parse ({world.get('lines')} lines, {world.get('bad_lines')} bad)")
    elif not row.get("kept_world") or not Path(row["kept_world"]).is_file():
        why.append("C3 its last line was not kept")
    if carries_goals and not row.get("kept_goals"):
        why.append("C3 no goal snapshot was kept (a soft-deadline or killed end writes none): the next leg could not carry "
                   "one")
    if row.get("guard_killed"):
        why.append(f"C4 the probe's guard killed it ({(row.get('guard_killed') or {}).get('text')})")
    if row.get("custody"):
        why.append(f"C5 custody: {'; '.join(row['custody'])}")
    if stop_seen:
        why.append("C6 the code under test changed mid-batch (STOP.txt)")
    return not why, "; ".join(why) if why else "C1-C6 held"


def custody_problems(start: dict, env: dict, mc: bool = False) -> list[str]:
    """C5, BEFORE a leg's launch (3.6; T19, T32): the start state's md5 is the kept one's, the world line's sha256 the kept
    line's, the goal snapshot's sha256 the kept `goals_last.jsonl`'s when one is carried (part 0), and the environment keys
    the allow-list's (an MC job never sends AI_PLAYER_GOALS). `start`: state, state_md5, world, world_sha256, goals,
    goals_sha256, carry."""
    problems = []
    for key in ("state", "world"):
        if not start.get(key):
            problems.append(f"the leg has no start {key} (an unresolved or unknown start)")
    if start.get("state") is not None:
        now = md5_of(Path(start["state"]))
        if now is None or now != start.get("state_md5"):
            problems.append(f"the start state {start['state']} has md5 {now}, not the kept {start.get('state_md5')}")
    if start.get("world") is not None:
        now = sha256_of(Path(start["world"]))
        if now is None or now != start.get("world_sha256"):
            problems.append(f"the world line {start['world']} has sha256 {now}, not the kept {start.get('world_sha256')}")
    if start.get("carry"):
        given = env.get(ENV_GOALS)
        now = sha256_of(Path(given)) if given else None
        if not given or now is None or now != start.get("goals_sha256"):
            problems.append(f"the goal snapshot {given} has sha256 {now}, not the kept goals_last.jsonl's "
                            f"{start.get('goals_sha256')}")
    elif ENV_GOALS in env:
        problems.append(f"{ENV_GOALS} is set on a leg that carries no goal snapshot")
    problems += env_problems(env, mc)
    return problems


# ====================================================================== the scheduler's start check (3.13)
DISCRIMINATOR_MAPS = ("RUSTBORO_CITY", "ROUTE116", "ROUTE104")


def discriminator_tiles(world: dict | None, snapshot: dict | None) -> list[str]:
    """GM's per-tile discriminator (3.15 item 7), offline on a chain's L5 end: the tiles of the end snapshot's
    `tried_items` that are remembered item tiles (`MapMemory.items`) of a map the next leg starts on or crosses early: the
    tiles `_remembered_ball` offers with a new goal memory and not with the snapshot. Empty: the A/B is VACUOUS."""
    tried = tried_items_of(snapshot) or set()
    tiles = []
    for key, entry in ((world or {}).get("maps") or {}).items():
        if isinstance(entry, dict) and entry.get("const") in DISCRIMINATOR_MAPS:
            for xy in entry.get("items") or {}:
                if f"{key}|{xy}" in tried:
                    tiles.append(f"{key}|{xy}")
    return sorted(tiles)


def run_id_of(batch: str, chain: str, leg: str) -> str:
    return f"{batch}-{chain}-{leg}"


def start_from_record(record: dict, out: Path) -> dict | None:
    """The start a practice job takes from its source chain's REACHED leg end (its kept folder and the record's hashes)."""
    kept = record.get("kept") or {}
    folder = Path(kept.get("folder") or "")
    if not kept.get("folder") or not kept.get("state_md5") or not kept.get("world_sha256"):
        return None
    job = record.get("job") or {}
    return {"kind": "chain_end", "id": record.get("run_id"), "folder": str(folder),
            "state": str(folder / "end_state.ss1"), "state_md5": kept.get("state_md5"),
            "world": str(folder / "world_last.jsonl"), "world_sha256": kept.get("world_sha256"),
            "goals": str(folder / "goals_last.jsonl") if kept.get("goals_sha256") else None,
            "goals_sha256": kept.get("goals_sha256"), "reads": str(folder / "reads.jsonl"),
            "made_by": record.get("run_id"), "persona": job.get("persona"), "starter": job.get("starter"),
            "starter_from": job.get("starter_from"), "fallback_for": None}


def stage_start(stage: Path, manifest: dict, start_id: str, fallback_for: str | None = None) -> dict | None:
    """A start the stage copied (G1-G6, C1-C3), with the manifest's md5s, persona and starter; None when not staged."""
    info = (manifest.get("starts") or {}).get(start_id)
    if not isinstance(info, dict):
        return None
    folder = Path(stage) / "starts"
    return {"kind": "stage", "id": start_id, "folder": str(folder),
            "state": str(folder / f"{start_id}_end_state.ss1"), "state_md5": info.get("state_md5"),
            "world": str(folder / f"{start_id}_world.jsonl"), "world_sha256": info.get("world_sha256"),
            "goals": None, "goals_sha256": None, "reads": str(folder / f"{start_id}_reads.jsonl"),
            "made_by": info.get("made_by"), "persona": info.get("persona"), "starter": info.get("starter"),
            "starter_from": info.get("starter_from"), "fallback_for": fallback_for}


def dependency_of(job: dict, legs_by_id: dict[str, dict], ended: set[str], out: Path,
                  stages: dict[str, tuple[Path, dict]]) -> tuple[str, object] | None:
    """A job that waits on its source chain (WP1b, P2, GM's A/B): ("ready", its start), ("skip", why) while the source
    chain runs without a reached L5 record, or, once that chain ENDED without one (it stopped before L5, or its L5
    missed), ("ready", its FALLBACK start) at once, labelled `fallback_for` (2.1), or ("drop", why) when it has none. A GM
    A/B job is dropped as VACUOUS when its source's end holds no discriminating tile (3.15 item 7). None: no dependency."""
    dep = job.get("depends_on")
    if not dep:
        return None
    source, leg = dep["chain"], dep.get("leg", "L5")
    record = legs_by_id.get(run_id_of(job["batch"], source, leg))
    if record is not None and record.get("reached"):
        start = start_from_record(record, out)
        if start is None:
            return "drop", f"the source {source} {leg}'s kept files are not all recorded"
        if job.get("discriminator"):
            tiles = discriminator_tiles(parse_object(last_line_of(Path(start["world"]))),
                                        parse_object(last_line_of(Path(start["goals"]))) if start.get("goals") else None)
            if not tiles:
                return "drop", (f"VACUOUS: the source {source} {leg}'s end holds no discriminating tile (3.15 item 7): the "
                                f"A/B is not run")
            start["discriminator"] = tiles
        return "ready", start
    missed = record is not None and not record.get("reached")
    if source in ended or missed:
        fallback = job.get("fallback")
        if not fallback:
            return "drop", f"its source chain {source} ended without a reached {leg}"
        ids = list(fallback["starts"])
        start_id = ids[int(fallback.get("slot", 0)) % len(ids)]
        stage_dir, manifest = stages.get(job["stage"], (None, None))
        start = stage_start(stage_dir, manifest, start_id, fallback["for"]) if stage_dir is not None else None
        if start is None:
            return "drop", f"its source chain {source} missed and its fallback start {start_id} is not on the stage"
        return "ready", start
    return "skip", f"waiting for its source chain {source}'s reached {leg} record"


def start_check(job: dict, view: dict) -> tuple[str, str]:
    """GO, WAIT, SKIP or DROP for one pending job (3.13; pure: `view` holds what the orchestrator measured). DROP for good:
    STOP.txt, ABORT.txt, the AI-only stop, the --out cap, the deadline, a WAIT past --max-wait, a dependency that can never
    resolve. SKIP (per job, it keeps its place, no --max-wait clock): a dependency not resolved yet. WAIT (the job stays
    first in line and nothing launches this pass): the singles cap, a running run_regression.py, the disk reservation."""
    for flag, why in (("stop", "STOP.txt: the code under test changed mid-batch"),
                      ("abort", "ABORT.txt: the disk guard aborted the batch"),
                      ("ai_stop", f"the AI-only stop ({ATTENTION_FILE})"),
                      ("out_over", f"--out is over its cap of {OUT_CAP_BYTES} bytes")):
        if view.get(flag):
            return DROP, why
    legs = job.get("legs") or []
    if legs and not leg_fits(view["now"], legs[0], view.get("deadline")):
        return DROP, (f"the deadline: {legs[0]['leg']}'s wall {legs[0]['wall']:g} s + {LEG_MARGIN_SECONDS} s would pass "
                      f"--deadline {view.get('deadline')}")
    dependency = view.get("dependency")
    if dependency is not None:
        state, info = dependency
        if state == "skip":
            return SKIP, str(info)
        if state == "drop":
            return DROP, str(info)
    reasons = []
    if view.get("own_running", 0) + view.get("singles_others", 0) + 1 > SINGLES_CAP:
        reasons.append(f"the singles cap: {view.get('own_running', 0)} own + {view.get('singles_others', 0)} other singles "
                       f"+ this one > {SINGLES_CAP}")
    if view.get("regression"):
        reasons.append("run_regression.py is running")
    reserve = view.get("reserve_gb")
    if reserve is None or reserve < ABORT_FREE_GB + RESERVE_MARGIN_GB:
        reasons.append(f"the disk reservation: {reserve} GB after the running jobs' budgets, under "
                       f"{ABORT_FREE_GB + RESERVE_MARGIN_GB:g}")
    if reasons:
        if view.get("waited", 0.0) >= view.get("max_wait", MAX_WAIT_SECONDS):
            return DROP, f"a WAIT past --max-wait ({view.get('max_wait', MAX_WAIT_SECONDS):g} s): {'; '.join(reasons)}"
        return WAIT, "; ".join(reasons)
    return GO, ""


def ai_stop_streak(records: Iterable[dict]) -> int:
    """The AI-only stop's count (3.13): the trailing run, by end time, of leg records of REFUSED, NOT CLEAN or HUNG; CLEAN-*
    or CUT-WORLD resets it; INFRA does neither."""
    legs = sorted((r for r in records if isinstance(r, dict) and r.get("record") == "leg"),
                  key=lambda r: (r.get("ended") or 0, r.get("run_id") or ""))
    streak = 0
    for record in legs:
        klass = record.get("class")
        if klass in STOP_CLASSES:
            streak += 1
        elif klass in RESET_CLASSES:
            streak = 0
    return streak


# ====================================================================== the plan (2.4, 2.4b)
PAIR_CODES = {"Story": "S", "Catcher": "C", "Trainer": "T"}
STARTER_CODES = {"TREECKO": "TRE", "TORCHIC": "TOR", "MUDKIP": "MUD"}
#: the 9 pairs, the diagonal (live_chain's PAIRS) first, then the 6 never played as a New Game chain
ALL_PAIRS = (("Story", "TREECKO"), ("Catcher", "TORCHIC"), ("Trainer", "MUDKIP"), ("Story", "TORCHIC"),
             ("Story", "MUDKIP"), ("Catcher", "TREECKO"), ("Catcher", "MUDKIP"), ("Trainer", "TREECKO"),
             ("Trainer", "TORCHIC"))
DIAGONAL = ALL_PAIRS[:3]
FRONTIER_FILE = "PROJECT KNOWLEDGE/ai-frontier.txt"
FRONTIER_TARGET = re.compile(r"AI frontier:[^`]*`(?P<id>[a-z0-9_]+)`")


def pair_code(persona: str, starter: str) -> str:
    return f"{PAIR_CODES[persona]}{STARTER_CODES[starter]}"


def legs_for(to: str, data: dict, mc: bool = False, from_chapter: int = 1) -> list[dict]:
    """The legs to `to` by `live_chain.legs_of` (refused targets refused there): an MC job's by live_chain's own budgets
    (FRAMES_BY_CHAPTER, WALL: E0's harness exactly), every other job's by A1's table (L6 1,000,000 frames, L7 1,200,000,
    7,200 s each); a saved start keeps the legs from `from_chapter` on."""
    try:
        legs = LC.legs_of(to, data, LC.FRAMES_BY_CHAPTER if mc else LEG_FRAMES)
    except LC.Refusal as error:
        raise Refusal(str(error)) from None
    out = []
    for leg in legs:
        if leg["chapter"] < from_chapter:
            continue
        out.append({**leg, "wall": float(LC.WALL) if mc else LEG_WALL[leg["chapter"]]})
    if not out:
        raise Refusal(f"no leg from chapter {from_chapter} to {to}")
    return out


def frontier_target(repo: Path | None = None) -> str:
    """The newest GRADED target (`PROJECT KNOWLEDGE/ai-frontier.txt`, its first milestone id): MC's default --to."""
    text = ((repo or REPO) / FRONTIER_FILE).read_text(encoding="utf-8")
    hit = FRONTIER_TARGET.search(text)
    if hit is None:
        raise Refusal(f"{FRONTIER_FILE} names no milestone in backticks after 'AI frontier:'")
    return hit["id"]


def make_job(batch: str, arm: str, stage: str, kind: str, persona: str, starter: str, seed: int, legs: list[dict],
             start: dict, goals: str, mc: bool = False, env: dict | None = None, **extra) -> dict:
    code = pair_code(persona, starter)
    chain = f"{arm}-{'N' if kind == 'chain' else 'F'}-{code}-{seed}"
    job = {"batch": batch, "chain": chain, "arm": arm, "stage": stage, "kind": kind,
           "origin": "new_game" if kind == "chain" else "practice", "persona": persona, "personality": persona,
           "starter": starter, "starter_from": "plan" if kind == "chain" else start.get("starter_from", "plan"),
           "pair": code, "seed": int(seed), "profile": f"{PROFILE_PREFIX}{batch}-{chain}", "legs": legs, "start": start,
           "goals": goals, "mc": mc, "env": dict(env or {}), "depends_on": None, "fallback": None, "discriminator": False}
    job.update(extra)
    return job


def plan_jobs(batch: str, first: int, data: dict, to: str | None = None, env: dict | None = None,
              repo: Path | None = None) -> list[dict]:
    """THE JOB LIST of a batch (2.4, 2.4b; pure, and every job's env is checked: it must be EMPTY, so `env` given here is
    always refused, a FAULT switch with its own message):
      P1   REAL and WALL-OLDALE, the 3 diagonal New Game chains, the SAME 3 seeds in both arms, L1-L2, snapshots carried
      GM   one diagonal New Game chain L1-L5 (it makes the start), then GOALS-ON and GOALS-OFF from its L5 end on 2 seeds,
           L6 (dropped as VACUOUS when its end holds no discriminating tile)
      WP1  WP1a: 9 New Game chains, one per pair, L1-L7; WP1b: 27 practice jobs (the 9 L5 ends x 3 seeds, L6-L7,
           interleaved by start; a missed chain's pair takes its persona's fallback start, labelled); P2: WALL-BRINEY on
           the first-seed practice job of each diagonal pair, L6 only
      MC   the 3 diagonal New Game chains to the newest graded target (`ai-frontier.txt`), live_chain's legs, P = 3, NO goal
           snapshot (E0's harness exactly), seeds in 6701-6799"""
    new_game = {"kind": "new_game", "id": "NG"}
    jobs: list[dict] = []
    if batch == "P1":
        legs = legs_for(to or "ch2_wally", data)
        for offset, (persona, starter) in enumerate(DIAGONAL):
            for arm in ("REAL", "WALL-OLDALE"):
                jobs.append(make_job(batch, arm, arm, "chain", persona, starter, first + offset, legs, new_game,
                                     "carry", env=env))
    elif batch == "GM":
        persona, starter = DIAGONAL[0]
        chain = make_job(batch, "REAL", "REAL", "chain", persona, starter, first, legs_for(CHAPTER5_END, data), new_game,
                         "carry", env=env)
        jobs.append(chain)
        legs = legs_for("ch6_dewford", data, from_chapter=PRACTICE_FROM)
        for offset in (1, 2):
            for arm, goals in (("GOALS-ON", "carry"), ("GOALS-OFF", "off")):
                jobs.append(make_job(batch, arm, "REAL", "practice", persona, starter, first + offset, legs,
                                     {"kind": "pending", "id": f"{chain['chain']}-L5"}, goals, env=env,
                                     depends_on={"chain": chain["chain"], "leg": "L5"}, discriminator=True))
    elif batch == "WP1":
        chains = {}
        legs_chain = legs_for(to or PROBE_TO, data)
        for offset, (persona, starter) in enumerate(ALL_PAIRS):
            job = make_job(batch, "REAL", "REAL", "chain", persona, starter, first + offset, legs_chain, new_game, "carry",
                           env=env)
            chains[(persona, starter)] = job
            jobs.append(job)
        legs_practice = legs_for(to or PROBE_TO, data, from_chapter=PRACTICE_FROM)
        seed = first + len(ALL_PAIRS)
        firsts = {}
        for slot in range(3):
            for persona, starter in ALL_PAIRS:
                source = chains[(persona, starter)]
                job = make_job(batch, "REAL", "REAL", "practice", persona, starter, seed, legs_practice,
                               {"kind": "pending", "id": f"{source['chain']}-L5"}, "carry", env=env,
                               depends_on={"chain": source["chain"], "leg": "L5"},
                               fallback={"for": pair_code(persona, starter), "starts": list(FALLBACKS[persona]),
                                         "slot": slot})
                jobs.append(job)
                if slot == 0:
                    firsts[(persona, starter)] = job
                seed += 1
        legs_p2 = legs_for("ch6_dewford", data, from_chapter=PRACTICE_FROM)
        for persona, starter in DIAGONAL:
            twin = firsts[(persona, starter)]
            jobs.append(make_job(batch, "WALL-BRINEY", "WALL-BRINEY", "practice", persona, starter, twin["seed"], legs_p2,
                                 dict(twin["start"]), "carry", env=env, depends_on=dict(twin["depends_on"]),
                                 fallback=dict(twin["fallback"]), twin=twin["chain"]))
    elif batch == "MC":
        target = to or frontier_target(repo)
        legs = legs_for(target, data, mc=True)
        for offset, (persona, starter) in enumerate(DIAGONAL):
            jobs.append(make_job(batch, "REAL", "REAL", "chain", persona, starter, first + offset, legs, new_game, "never",
                                 mc=True, env=env))
    else:
        raise Refusal(f"no batch {batch!r}: P1, GM, WP1 or MC")
    problems = jobs_problems(jobs)
    if problems:
        raise Refusal("; ".join(problems[:6]))
    return jobs


def jobs_problems(jobs: list[dict]) -> list[str]:
    """What `plan` and `run` refuse in a job list (exit 2): an environment key off the allow-list (a FAULT switch, a
    POKEBOT_* or PYTHON* variable), AI_PLAYER_GOALS on an MC job, ANY key at all (a job's env must be empty: the probe
    sets every launch key itself; fix round 5), a profile name the launcher refuses or that is not the
    probe's, a chain id twice, an MC seed outside 6701-6799, an MC job that carries goals."""
    from ai_player.host import launcher

    problems: list[str] = []
    seen: set[str] = set()
    for job in jobs:
        name = job.get("chain")
        for problem in env_problems(job.get("env") or {}, bool(job.get("mc"))):
            problems.append(f"{name}: {problem}")
        # (fix round 5) a job's env must be EMPTY: run_job derives every launch key itself and never sends job["env"], so
        # an allowed key there would pass and be silently dropped
        for key in sorted(k for k in (job.get("env") or {}) if k in ENV_ALLOWED):
            problems.append(f"{name}: {key} is set by the probe itself: a job's env is never sent")
        profile = str(job.get("profile") or "")
        if not launcher._PROFILE_NAME_RE.match(profile) or not profile.startswith(PROFILE_PREFIX):
            problems.append(f"{name}: the profile {profile!r} is not a probe profile the launcher accepts")
        if name in seen:
            problems.append(f"{name}: the job id is given twice")
        seen.add(name)
        if job.get("mc"):
            if not MC_SEEDS[0] <= int(job.get("seed") or 0) <= MC_SEEDS[1]:
                problems.append(f"{name}: an MC seed {job.get('seed')} outside {MC_SEEDS[0]}-{MC_SEEDS[1]}")
            if job.get("goals") != "never":
                problems.append(f"{name}: an MC job carries no goal snapshot (goals 'never')")
        if not job.get("legs"):
            problems.append(f"{name}: no legs")
    return problems


# ====================================================================== placement and seeds (3.10, 2.5)
def inside_work_tree(path: Path) -> bool:
    """`git rev-parse --is-inside-work-tree` from the nearest existing folder (an ignored folder of a work tree is inside)."""
    probe = Path(path).resolve()
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    if probe.is_file():
        probe = probe.parent
    try:
        done = subprocess.run(["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"], capture_output=True,
                              text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return True  # cannot tell: fail closed
    return done.returncode == 0 and done.stdout.strip() == "true"


def at_or_under(path: Path, root: Path) -> bool:
    """`path` IS `root` or lies under it: a PATH test (both resolved, case-folded as Windows compares them), so a sibling
    whose name merely begins with the root's name is NOT under it."""
    a, b = os.path.normcase(str(Path(path).resolve())), os.path.normcase(str(Path(root).resolve()))
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def placement_problems(path: Path, what: str, work_tree: Callable[[Path], bool] = inside_work_tree) -> list[str]:
    """--out and every stage lie outside every git work tree, ignored or not, outside any pokebot-learner folder, and
    neither at nor under `GRADED_CH5` (3.14: A1 reads the graded chapter 1-5 chains' starts there and never writes there;
    verifier round 3, N7)."""
    resolved = Path(path).resolve()
    problems = []
    if "pokebot-learner" in (part.lower() for part in resolved.parts):
        problems.append(f"{what} {resolved} lies in a folder named pokebot-learner: the learner clone is never touched")
    if at_or_under(resolved, Path(GRADED_CH5)):
        problems.append(f"{what} {resolved} lies at or under {GRADED_CH5}: the graded chapter 1-5 chains are never written "
                        f"(3.14)")
    if work_tree(resolved):
        problems.append(f"{what} {resolved} lies inside a git work tree (ignored or not): a batch writes outside every one")
    return problems


def default_seed_ledgers(extra: Iterable[Path] = ()) -> list[Path]:
    import glob

    paths: list[Path] = [Path(p) for p in extra]
    for pattern in SEED_LEDGER_GLOBS:
        paths += [Path(p) for p in glob.glob(pattern, recursive=True)]
    out, seen = [], set()
    for path in paths:
        key = os.path.normcase(os.path.abspath(str(path)))
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def seeds_named(first: int, last: int, paths: Iterable[Path], ignore: tuple[tuple[str, int], ...] = ()
                ) -> tuple[list[str], list[str], list[str]]:
    """(every entry of every ledger that names a seed of first-last, every ledger that could not be read and is not a
    KNOWN non-ledger, every KNOWN non-ledger that could not be read). 2.5: the check LISTS every ledger it could not read
    and refuses unless each is a known non-ledger, so `run` refuses the second list and lists the third (its NOTE lines and
    batch.json's `known_non_ledgers`; verifier round 2, R2-M2: it was skipped unlisted). `ignore`: (ledger path, entry id)
    pairs to skip (a resumed batch's own entry)."""
    hits, unreadable, known = [], [], []
    ignored = {(os.path.normcase(os.path.abspath(p)), i) for p, i in ignore}
    for path in paths:
        try:
            entries = json.loads(Path(path).read_text(encoding="utf-8"))["entries"]
        except Exception as error:  # noqa: BLE001 - listed, and refused unless a known non-ledger
            text = str(path).replace("\\", "/")
            item = f"{path}: {type(error).__name__}"
            if any(text.endswith(name) for name in KNOWN_NON_LEDGERS):
                known.append(item)
            else:
                unreadable.append(item)
            continue
        norm = os.path.normcase(os.path.abspath(str(path)))
        for entry in entries:
            try:
                if (norm, entry["id"]) in ignored:
                    continue
                if entry["first"] <= last and first <= entry["last"]:
                    hits.append(f"{path} #{entry['id']} ({entry.get('purpose')}, {entry['first']}-{entry['last']})")
            except (KeyError, TypeError):
                unreadable.append(f"{path}: an entry without first/last")
    return hits, unreadable, known


def seed_span(jobs: list[dict]) -> tuple[int, int] | None:
    """(first, last) when the jobs' seeds are ONE contiguous range (shared seeds allowed), else None."""
    seeds = sorted({int(job["seed"]) for job in jobs})
    if not seeds or seeds != list(range(seeds[0], seeds[-1] + 1)):
        return None
    return seeds[0], seeds[-1]


def band_row(data: dict) -> dict | None:
    for entry in data.get("entries") or []:
        if (entry.get("family") == FAMILY and entry.get("purpose") == "development" and entry.get("status") == "done"
                and entry.get("first") == TRAINER_BAND[0] and entry.get("last") == TRAINER_BAND[1]
                and entry.get("note") == BAND_NOTE):
            return entry
    return None


def trainer_problems(seeds: Iterable[int], data: dict) -> list[str]:
    """--trainer (D13): every seed inside the band, the band row present, no overlapping `registered` entry."""
    seeds = sorted(set(int(s) for s in seeds))
    problems = [f"the trainer seed {s} lies outside the band {TRAINER_BAND[0]}-{TRAINER_BAND[1]}" for s in seeds
                if not TRAINER_BAND[0] <= s <= TRAINER_BAND[1]]
    if band_row(data) is None:
        problems.append("the ledger holds no band row (reserve-band, once, after the merge)")
    if seeds:
        for entry in data.get("entries") or []:
            if entry.get("status") == "registered" and entry.get("first", 0) <= seeds[-1] and seeds[0] <= entry.get("last", -1):
                problems.append(f"a registered entry #{entry.get('id')} overlaps the trainer's seeds")
    return problems


def reserve_band(path: Path | None = None) -> dict:
    """The AI trainer band row, ONCE (3.10): begin + finish on 2,000,000-2,999,999, then the ledger's own check. Refused
    when a band row exists."""
    path = Path(path or ledger.LEDGER)
    if band_row(ledger.load(path)) is not None:
        raise Refusal("the ledger already holds the band row: reserve-band runs once")
    entry, _ = ledger.begin(FAMILY, DRIVER, "development", TRAINER_BAND[0], TRAINER_BAND[1], text_sha256(BAND_TEXT),
                            None, note=BAND_NOTE, path=path)
    ledger.finish(entry["id"], BAND_VERDICT, None, path=path)
    problems = ledger.check(ledger.load(path))
    if problems:
        raise Refusal(f"the ledger's check fails after the band row: {problems}")
    return entry


# ====================================================================== the stage (3.3, 3.12)
def tree_digest(root: Path, play_only: bool = False) -> str:
    """The lab kit's `make_arm11.tree_digest`: every file under `root` but caches, evidence, .pyc and .ss1 (and with
    `play_only` the test side, any path through `gates`), by relative path and content."""
    digest = hashlib.sha256()
    files = sorted(x for x in Path(root).rglob("*") if x.is_file() and "__pycache__" not in x.parts
                   and "evidence" not in x.parts and x.suffix not in (".pyc", ".ss1")
                   and not (play_only and "gates" in x.parts))
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def stage_code_digest(stage: Path) -> str:
    return tree_digest(Path(stage) / "code" / "ai_player")


def sandbox_tracked_digest(sandbox: Path) -> str:
    """The junctioned sandbox's modules/ and plugins/, hashed (the git-tracked files when the sandbox is in a work tree)."""
    sandbox = Path(sandbox)
    names: list[str] = []
    try:
        done = subprocess.run(["git", "-C", str(sandbox), "ls-files", "--", "modules", "plugins"], capture_output=True,
                              text=True, timeout=120)
        if done.returncode == 0:
            names = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        names = []
    if not names:
        names = sorted(p.relative_to(sandbox).as_posix() for folder in ("modules", "plugins")
                       for p in (sandbox / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    digest = hashlib.sha256()
    for name in sorted(names):
        path = sandbox / name
        digest.update(name.encode() + b"\0" + (hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b"-"))
    return digest.hexdigest()


def make_junction(target: Path, link: Path) -> None:
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def is_link(path: Path) -> bool:
    return os.path.islink(path) or bool(getattr(os.path, "isjunction", lambda _p: False)(path))


def find_links(root: Path) -> list[str]:
    """Every junction or symbolic link under `root`, WITHOUT following any (the kept kit's `find_junctions.scan`)."""
    found: list[str] = []
    stack = [Path(root)]
    while stack:
        here = stack.pop()
        try:
            entries = list(os.scandir(here))
        except OSError as why:
            found.append(f"UNREADABLE {here}: {why}")
            continue
        for entry in entries:
            try:
                if entry.is_junction() or entry.is_symlink():
                    found.append(entry.path)
                elif entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
            except OSError as why:
                found.append(f"UNREADABLE {entry.path}: {why}")
    return found


def sandbox_counts(sandbox: Path) -> dict:
    return {name: (sum(1 for _ in (Path(sandbox) / name).rglob("*")) if (Path(sandbox) / name).is_dir() else None)
            for name in LINKS}


def apply_mutant(code_root: Path, name: str, mutant: dict) -> dict:
    """ONE anchored edit to the staged copy (3.3), refused unless the anchor hits EXACTLY once; the line endings of the file
    are kept. Returns {name, file, anchor_sha256, edit_sha256}."""
    path = Path(code_root) / mutant["file"]
    raw = path.read_bytes().decode("utf-8")
    anchor, new = mutant["anchor"], mutant["replacement"]
    if "\r\n" in raw:
        anchor, new = anchor.replace("\r\n", "\n").replace("\n", "\r\n"), new.replace("\r\n", "\n").replace("\n", "\r\n")
    hits = raw.count(anchor)
    if hits != 1:
        raise Refusal(f"the mutant {name}'s anchor hits {hits} times in {mutant['file']}: it must hit exactly once")
    path.write_bytes(raw.replace(anchor, new, 1).encode("utf-8"))
    return {"name": name, "file": mutant["file"], "anchor_sha256": text_sha256(mutant["anchor"]),
            "edit_sha256": text_sha256(mutant["anchor"] + "\0" + mutant["replacement"])}


def archive_code(repo: Path, commit: str, target: Path) -> None:
    """`git -C <repo> archive <commit> ai_player ':(exclude)ai_player/evidence'`, extracted into `target` (3.3)."""
    import io
    import tarfile

    done = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", commit, "ai_player",
                           ":(exclude)ai_player/evidence"], capture_output=True, timeout=600)
    if done.returncode != 0:
        raise Refusal(f"git archive {commit} failed: {done.stderr.decode('utf-8', 'replace')[:300]}")
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
        tar.extractall(target, filter="data")


def start_sources(start_id: str, g_root: Path, c_root: Path) -> dict:
    info = STARTS[start_id]
    if info["root"] == "g":
        base = Path(g_root) / info["path"] / "L5"
        return {"state": base / "end_state.ss1", "world": base / "world_last.jsonl", "actions": base / "actions.jsonl",
                "job": Path(g_root) / f"{info['path']}.job.json", "made_by": f"graded ledger #101, {info['path']} L5"}
    base = Path(c_root) / info["path"]
    return {"state": base / "end_state.ss1", "world": base / "world.jsonl", "actions": None,
            "job": Path(c_root) / f"{info['path']}.job.json", "made_by": f"the chapter-5 stops probe, {info['path']}"}


def world_lines_ok(path: Path) -> bool:
    """Every non-blank line of a world file parses as a JSON object (streamed)."""
    try:
        with open(path, "rb") as handle:
            lines = 0
            for raw in handle:
                if not raw.strip():
                    continue
                lines += 1
                if parse_object(raw) is None:
                    return False
        return lines > 0
    except OSError:
        return False


def starter_of_party(truth: dict | None) -> tuple[str | None, str]:
    """The starter of a C start, from its truth's party: exactly ONE of the three evolution lines (none or two refused)."""
    party = (truth or {}).get("party_exp") or []
    species = {str(member[1]) for member in party if isinstance(member, list) and len(member) > 1}
    lines = [starter for starter, names in STARTER_LINES.items() if species & set(names)]
    if len(lines) != 1:
        return None, f"the party {sorted(species)} holds {len(lines)} starter lines, not one"
    return lines[0], ""


def start_custody(start_id: str, files: dict, truth: dict | None, data: dict) -> tuple[dict, list[str]]:
    """Stage-time custody of one start (2.1): the md5s of the table, the truth holding ch5_rival_meet's proof, a world file
    of JSON lines, ONE readable starter (a G start's job file, a C start's truth party). Returns (the manifest's entry,
    the problems)."""
    info = STARTS[start_id]
    problems = []
    state_md5, world_md5 = md5_of(files["state"]), md5_of(files["world"])
    if state_md5 != info["md5"]:
        problems.append(f"{start_id}: end_state.ss1 md5 {state_md5}, not the table's {info['md5']}")
    if world_md5 != info["world_md5"]:
        problems.append(f"{start_id}: the world file md5 {world_md5}, not the table's {info['world_md5']}")
    proof = next((milestone_proof(m) for m in data.get("milestones") or [] if m.get("id") == CHAPTER5_END), None)
    marks = ((truth or {}).get("story") or {}).get("marks")
    if proof is None or not LC.proof_holds(marks, proof)["held"]:
        problems.append(f"{start_id}: the start truth does not hold {CHAPTER5_END}'s proof")
    if not world_lines_ok(files["world"]):
        problems.append(f"{start_id}: the world file is not JSON lines")
    starter, starter_from = None, None
    if info["root"] == "g":
        job = read_json(files["job"]) if files.get("job") else None
        starter = job.get("starter") if isinstance(job, dict) and job.get("starter") in STARTERS else None
        starter_from = "job_file"
        if starter is None:
            problems.append(f"{start_id}: its job file names no starter")
    else:
        starter, why = starter_of_party(truth)
        starter_from = "truth_party"
        if starter is None:
            problems.append(f"{start_id}: {why}")
    entry = {"state_md5": state_md5, "world_md5": world_md5, "world_sha256": sha256_of(files["world"]),
             "persona": info["persona"], "starter": starter, "starter_from": starter_from, "made_by": files["made_by"],
             "truth": {"map": (truth or {}).get("map"), "frame": (truth or {}).get("frame")}}
    return entry, problems


def build_stage(stage: Path, commit: str, repo: Path, sandbox: Path, donor: Path, mutant: str | None,
                starts: list[str], g_root: Path = GRADED_CH5, c_root: Path = KEPT_C,
                truth: Callable[[Path], dict | None] | None = None, archive: Callable = archive_code,
                free: Callable[[Path], float | None] = LC.safe_free,
                work_tree: Callable[[Path], bool] = inside_work_tree) -> dict:
    """THE STAGE (3.3): refused when it exists, lies in a work tree or a pokebot-learner folder, under 45 GB free, with an
    unknown mutant or start; else built, the starts custody-checked (a refusal deletes nothing it did not make: the stage is
    torn down junctions first), and manifest.json written."""
    stage = Path(stage).resolve()
    if stage.exists():
        raise Refusal(f"{stage} exists: a stage is built once and never reused")
    problems = placement_problems(stage, "the stage", work_tree)
    for what, path in (("the repo", repo), ("the sandbox", sandbox)):
        if "pokebot-learner" in (part.lower() for part in Path(path).resolve().parts):
            problems.append(f"{what} {path} lies in a folder named pokebot-learner")
    refusal = start_refusal(free(stage.parent if stage.parent.exists() else Path(stage.anchor)))
    if refusal:
        problems.append(refusal)
    if mutant is not None and mutant not in MUTANTS:
        problems.append(f"no mutant {mutant!r} ({sorted(MUTANTS) or 'none built yet'})")
    unknown = [s for s in starts if s not in STARTS]
    if unknown:
        problems.append(f"unknown starts {unknown} (of {sorted(STARTS)})")
    if not (Path(donor) / "metadata.yml").is_file():
        problems.append(f"the donor {donor} has no metadata.yml")
    if problems:
        raise Refusal("; ".join(problems))
    sandbox = Path(sandbox).resolve()
    before = sandbox_counts(sandbox)
    code, build, starts_dir = stage / "code", stage / "build", stage / "starts"
    code.mkdir(parents=True)
    try:
        archive(Path(repo), commit, code)
        (build / "profiles").mkdir(parents=True)
        make_junction(build, code / "sandbox-pokebot")
        junctions = {"code/sandbox-pokebot": str(build)}
        for name in LINKS:
            make_junction(sandbox / name, build / name)
            junctions[f"build/{name}"] = str(sandbox / name)
        for entry in sandbox.iterdir():
            if entry.is_file():
                shutil.copy2(entry, build / entry.name)
        for entry in (sandbox / "profiles").iterdir() if (sandbox / "profiles").is_dir() else []:
            if entry.is_file() and entry.suffix in (".yml", ".py"):
                shutil.copy2(entry, build / "profiles" / entry.name)
        if (sandbox / "cache").is_dir():
            shutil.copytree(sandbox / "cache", build / "cache")
        (build / "logs").mkdir()
        (build / ".git").mkdir()
        (build / "profiles" / DONOR).mkdir()
        shutil.copy2(Path(donor) / "metadata.yml", build / "profiles" / DONOR / "metadata.yml")
        fixture = sandbox / "profiles" / "ai-step0-fixture" / "metadata.yml"
        if fixture.is_file():
            (build / "profiles" / "ai-step0-fixture").mkdir()
            shutil.copy2(fixture, build / "profiles" / "ai-step0-fixture" / "metadata.yml")
            (build / "profiles" / "ai-step0-fixture" / ".ai_player_profile").write_text(
                "A1 frontier probe stage: the truth harness's profile\n", encoding="utf-8")
        starts_dir.mkdir()
        data = json.loads((code / "ai_player" / "knowledge" / "milestones.json").read_text(encoding="utf-8"))
        manifest_starts, problems = {}, []
        reader = truth or _default_truth
        for start_id in starts:
            files = start_sources(start_id, g_root, c_root)
            missing = [str(p) for key, p in files.items() if key in ("state", "world") and not Path(p).is_file()]
            if missing:
                problems.append(f"{start_id}: missing {missing}")
                continue
            shutil.copy2(files["state"], starts_dir / f"{start_id}_end_state.ss1")
            shutil.copy2(files["world"], starts_dir / f"{start_id}_world.jsonl")
            reads = []
            if files.get("actions") and Path(files["actions"]).is_file():
                reads = [line for line in Path(files["actions"]).read_text(encoding="utf-8").splitlines()
                         if (parse_object(line) or {}).get("decision") == "read"]
            (starts_dir / f"{start_id}_reads.jsonl").write_text("".join(f"{line}\n" for line in reads), encoding="utf-8")
            copied = {**files, "state": starts_dir / f"{start_id}_end_state.ss1",
                      "world": starts_dir / f"{start_id}_world.jsonl"}
            entry, found = start_custody(start_id, copied, reader(copied["state"]), data)
            entry["reads"] = len(reads)
            manifest_starts[start_id] = entry
            problems += found
        if problems:
            raise Refusal("start custody: " + "; ".join(problems))
        made = apply_mutant(code, mutant, MUTANTS[mutant]) if mutant is not None else None
        manifest = {"schema_version": SCHEMA_VERSION, "made": time.strftime("%Y-%m-%d %H:%M:%S"), "repo": str(repo),
                    "commit": commit, "mutant": made, "play_digest": tree_digest(code / "ai_player", play_only=True),
                    "digest": tree_digest(code / "ai_player"), "sandbox": str(sandbox),
                    "sandbox_counts_before": before, "donor": {"path": str(donor),
                                                               "md5": md5_of(Path(donor) / "metadata.yml")},
                    "junctions": junctions, "starts": manifest_starts}
        write_json(stage / "manifest.json", manifest)
        return manifest
    except BaseException:
        with contextlib.suppress(Exception):
            teardown(stage, sandbox)
        raise


def _default_truth(state: Path) -> dict | None:
    from ai_player.gates import live_step5 as L5

    truth, _ = L5.truth_of(Path(state))
    return truth


def manifest_problems(stage: Path) -> tuple[dict | None, list[str]]:
    """A stage's manifest.json, and why it is not a valid one (exit 2 at `run`)."""
    data = read_json(Path(stage) / "manifest.json")
    if not isinstance(data, dict):
        return None, [f"{stage}: no valid manifest.json"]
    missing = [key for key in ("schema_version", "commit", "play_digest", "digest", "starts") if key not in data]
    if missing or data.get("schema_version") != SCHEMA_VERSION:
        return None, [f"{stage}: manifest.json lacks {missing} or has schema {data.get('schema_version')!r}"]
    return data, []


def teardown(stage: Path, sandbox: Path | None = None) -> dict:
    """Unlink every junction FIRST (a recursive delete through one would delete the main sandbox's `modules/`), check a
    second scan finds none, THEN delete the stage; the sandbox's counts of modules, plugins, mgba and roms before and
    after (they must read unchanged)."""
    stage = Path(stage)
    manifest = read_json(stage / "manifest.json") or {}
    sandbox = Path(sandbox or manifest.get("sandbox") or stage)
    before = sandbox_counts(sandbox)
    unlinked = []
    for link in sorted(find_links(stage), key=len, reverse=True):
        if link.startswith("UNREADABLE"):
            continue
        try:
            os.rmdir(link)
        except OSError:
            os.unlink(link)
        unlinked.append(link)
    left = find_links(stage)
    if left:
        raise Refusal(f"teardown refused: the stage still holds links {left[:5]}: nothing deleted")
    shutil.rmtree(stage, ignore_errors=False)
    after = sandbox_counts(sandbox)
    return {"unlinked": unlinked, "before": before, "after": after, "unchanged": before == after}


# ====================================================================== one job (3.4: the child)
def copy_file(source: Path, target: Path) -> None:
    """A copy (its own name, so a test can make one fail its size check: T15)."""
    shutil.copy2(source, target)


def keep_ai_files(profile_dir: Path, keep: Path) -> dict:
    """The AI's own files of this leg (3.12), copied into the leg's kept folder BEFORE the profile is deleted, each when
    present: `current_save.sav`, `ai_player/memory.jsonl`, `ai_player/launches.jsonl`. An absent one is recorded "absent";
    a copy whose size is not the source's, or that fails, is recorded, never silent."""
    out = {}
    keep.mkdir(parents=True, exist_ok=True)
    for relative, name in AI_FILES:
        source = Path(profile_dir) / relative
        if not source.is_file():
            out[name] = "absent"
            continue
        try:
            copy_file(source, keep / name)
            want, got = source.stat().st_size, (keep / name).stat().st_size
            out[name] = "kept" if want == got else f"size check FAILED: {got} bytes, the source {want}"
        except OSError as error:
            out[name] = f"copy FAILED: {type(error).__name__}: {LC.safe_text(error, 200)}"
    return out


def verify_zip(path: Path, sizes: dict[str, int]) -> str | None:
    """None when the zip tests clean (`testzip()` is None) and its members and sizes equal the raw files'."""
    try:
        with zipfile.ZipFile(path) as kept:
            bad = kept.testzip()
            if bad is not None:
                return f"testzip names {bad}"
            got = {info.filename: info.file_size for info in kept.infolist()}
    except (OSError, zipfile.BadZipFile) as error:
        return f"the zip cannot be read: {type(error).__name__}"
    if got != sizes:
        return f"its members and sizes {got} are not the raw files' {sizes}"
    return None


def zip_logs(keep: Path, names: Iterable[str] = LOG_FILES) -> dict:
    """The leg's logs into `<keep>/logs.zip`, VERIFIED, and only then the raw logs deleted; a failed zip keeps them."""
    keep = Path(keep)
    members = [name for name in names if (keep / name).is_file()]
    target = keep / "logs.zip"
    sizes = {name: (keep / name).stat().st_size for name in members}
    try:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as made:
            for name in members:
                made.write(keep / name, name)
    except OSError as error:
        return {"zip": None, "zip_sha256": None, "verified": False, "problem": f"{type(error).__name__}", "raw": members}
    problem = verify_zip(target, sizes)
    if problem is not None:
        return {"zip": str(target), "zip_sha256": sha256_of(target), "verified": False, "problem": problem,
                "raw": members}
    for name in members:
        with contextlib.suppress(OSError):
            (keep / name).unlink()
    return {"zip": str(target), "zip_sha256": sha256_of(target), "verified": True, "problem": None, "members": members}


def profile_refusal(job: dict, profile: str, build_root: Path) -> str | None:
    """The child plays only in its job's NEW profile, a probe profile, never the donor or the main one."""
    name = str(job.get("profile") or "")
    if not name.startswith(PROFILE_PREFIX) or name == DONOR:
        return f"the job's profile {name!r} is not a probe profile ({PROFILE_PREFIX}*, never {DONOR})"
    if profile != name:
        return f"live_step5.PROFILE is {profile!r}, not this job's {name!r}"
    if (Path(build_root) / "profiles" / name).exists():
        return f"the profile {name} exists before the job (a leftover): a job plays in a NEW profile"
    return None


def legs_refusal(job: dict) -> str | None:
    """The job's legs must be the ones the STAGED code's milestones give (a plan made from another tree than the stage
    would target, budget or prove another leg): each leg, chapter, target, frame budget, wall and proof equal."""
    legs = job.get("legs") or []
    if not legs:
        return "the job has no legs"
    try:
        want = legs_for(legs[-1]["target"], load_staged_milestones(), bool(job.get("mc")), legs[0]["chapter"])
    except (Refusal, KeyError, TypeError) as error:
        return f"the job's legs cannot be re-derived from the staged milestones: {error}"
    fields = ("leg", "chapter", "target", "frames", "wall", "proof")
    got = [{k: leg.get(k) for k in fields} for leg in legs]
    if got != [{k: leg.get(k) for k in fields} for leg in want]:
        return "the job's legs are not the ones the staged milestones give (a plan made from another tree?)"
    return None


def delete_profile(build_root: Path, profile: str, sleep: Callable[[float], None] = time.sleep) -> tuple[bool, str | None]:
    path = Path(build_root) / "profiles" / profile
    if not profile.startswith(PROFILE_PREFIX) or profile == DONOR:
        return False, f"{path} (not a probe profile: never deleted)"
    for attempt in range(5):
        if not path.exists():
            break
        try:
            shutil.rmtree(path)
        except OSError:
            sleep(2.0 if attempt < 4 else 0.0)
    return (not path.exists()), (str(path) if path.exists() else None)


def stop_seen(out: Path) -> str | None:
    for name, why in ((STOP_FILE, "the code under test changed mid-batch (STOP.txt)"),
                      (ABORT_FILE, "the batch was ABORTED by the disk guard (ABORT.txt)"),
                      (ATTENTION_FILE, f"the AI-only stop ({ATTENTION_FILE})")):
        if (Path(out) / name).is_file():
            return why
    return None


def read_reads(path: str | Path | None) -> list[dict]:
    if not path or not Path(path).is_file():
        return []
    reads = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        record = parse_object(line)
        if record is not None and record.get("decision") == "read":
            reads.append(record)
    return reads


_MAP_CONSTS: dict[str, str] | None = None


def const_of_key(key: str | None, world: dict | None = None) -> str | None:
    """A map key ("group:number") to its constant: the world snapshot's own `maps[key].const`, else `rate_step5.map_keys`
    (the framework's MapRSE read as text, no framework import)."""
    global _MAP_CONSTS
    if not key:
        return None
    entry = ((world or {}).get("maps") or {}).get(key)
    if isinstance(entry, dict) and entry.get("const"):
        return str(entry["const"])
    if _MAP_CONSTS is None:
        try:
            from ai_player.gates.rate_step5 import map_keys

            _MAP_CONSTS = {value: const for const, value in map_keys().items()}
        except Exception:  # noqa: BLE001 - a missing table names no map: UNKNOWN
            _MAP_CONSTS = {}
    return _MAP_CONSTS.get(key)


def end_map_of(klass: str, after: dict | None, world: dict | None) -> dict:
    """CUT-WORLD and HUNG: the kept world tail's current map (its last transition's target), else UNKNOWN; every other
    class: the end truth's map."""
    key = None
    if klass not in (CUT_WORLD, HUNG) and isinstance((after or {}).get("map"), list) and len(after["map"]) == 2:
        key = f"{after['map'][0]}:{after['map'][1]}"
    if key is None:
        transitions = [t for t in (world or {}).get("transitions") or [] if isinstance(t, list) and len(t) >= 3]
        key = str(transitions[-1][2]) if transitions else None
    pair = [int(x) for x in key.split(":")] if key and re.fullmatch(r"\d+:\d+", key) else None
    return {"pair": pair, "const": const_of_key(key, world) or "UNKNOWN"}


def end_frame_of(written: bool, after: dict | None, records: list[dict], world: dict | None,
                 start_frame: int | None) -> int | None:
    if written and isinstance((after or {}).get("frame"), int):
        return after["frame"]
    frames = [r.get("frame") for r in records if isinstance(r, dict) and isinstance(r.get("frame"), int)]
    frames += [t[0] for t in leg_transitions(world, start_frame)]
    return max(frames) if frames else None


def base_record(job: dict, leg: dict, index: int) -> dict:
    start = job.get("start") or {}
    return {"schema_version": SCHEMA_VERSION, "record": "leg", "run_id": run_id_of(job["batch"], job["chain"], leg["leg"]),
            "batch": job.get("batch_info") or {"name": job["batch"]}, "tree": job.get("tree") or {"arm": job.get("stage")},
            "job": {"id": job["chain"], "arm": job.get("arm"), "kind": job.get("kind"), "origin": job.get("origin"),
                    "mc": bool(job.get("mc")), "persona": job.get("persona"), "starter": job.get("starter"),
                    "starter_from": job.get("starter_from"), "seed": job.get("seed"),
                    "legs_planned": [item["leg"] for item in job.get("legs") or []],
                    "start": {"id": start.get("id"), "kind": start.get("kind"), "state_md5": start.get("state_md5"),
                              "world_sha256": start.get("world_sha256"), "made_by": start.get("made_by"),
                              "reads_carried": None}},
            "leg": {"leg": leg["leg"], "chapter": leg["chapter"], "target": leg["target"], "frames": leg["frames"],
                    "wall": leg["wall"], "index": index},
            "launch": None, "verdict": None, "fresh": None, "class": None, "class_why": None, "reached": False,
            "claim_mismatch": False, "truth": {"before": None, "after": None}, "milestones_held": [], "next_unmet": None,
            "next_unmet_from": "none", "next_unmet_unread": [], "end_map": {"pair": None, "const": "UNKNOWN"},
            "blocker": None, "measures": {}, "start_memory": None, "bossprep": None, "rides": None,
            "experience": {"written": False, "fights": 0, "unclassified": []}, "kept": None,
            "continue": {"go": False, "why": None, "live_chain": None}, "custody": [], "notes": [], "ended": None}


def refused_record(job: dict, leg: dict, index: int, why: str, start_memory: dict | None = None) -> dict:
    record = base_record(job, leg, index)
    record.update({"class": REFUSED, "class_why": f"refused by the child: {why}", "custody": [why],
                   "start_memory": start_memory, "ended": time.time()})
    record["continue"] = {"go": False, "why": f"REFUSED before the launch: {why}", "live_chain": None}
    return record


def job_record(job: dict, ran: list[str], stopped_at: str | None, stop_reason: str | None, reached_last: bool,
               deleted: bool, leftover: str | None, not_run: list[str]) -> dict:
    return {"schema_version": SCHEMA_VERSION, "record": "job", "job": job["chain"], "batch": job["batch"],
            "arm": job.get("arm"), "kind": job.get("kind"), "mc": bool(job.get("mc")),
            "legs_planned": [leg["leg"] for leg in job.get("legs") or []], "legs_ran": ran, "not_run": not_run,
            "stopped_at": stopped_at,
            "stop_reason": stop_reason, "reached_last": reached_last, "profile_deleted": deleted, "leftover": leftover,
            "ended": time.time()}


def leg_start(job: dict, index: int, prev: dict | None) -> dict:
    """Where leg `index` starts: a New Game (L1 of a chain), its job's resolved start (a stage start or a source chain's
    kept end), or the previous leg's end (its state, its KEPT world line, its kept goal snapshot). Says whether the leg
    carries the snapshot (3.15 item 5: every leg from a kept state, except MC's, GOALS-OFF's and a start with none)."""
    policy = job.get("goals", "carry")
    if index == 0:
        start = dict(job.get("start") or {})
        if start.get("kind") == "new_game":
            return {"fresh": True, "carry": False, "mode": "none", "snapshot": None, "goals_sha256": None,
                    "reads": [], "fallback_for": None}
        out = {"fresh": False, "state": start.get("state"), "state_md5": start.get("state_md5"),
               "world": start.get("world"), "world_sha256": start.get("world_sha256"), "goals": start.get("goals"),
               "goals_sha256": start.get("goals_sha256"), "reads": read_reads(start.get("reads")),
               "fallback_for": start.get("fallback_for")}
    else:
        out = {"fresh": False, **{k: prev[k] for k in ("state", "state_md5", "world", "world_sha256", "goals",
                                                       "goals_sha256", "reads")}, "fallback_for": None}
    has = bool(out.get("goals")) and Path(out["goals"]).is_file()
    out["snapshot"] = parse_object(last_line_of(Path(out["goals"]))) if has else None
    out["carry"] = has and policy == "carry"
    out["mode"] = "carried" if out["carry"] else ("kept" if has else "none")
    return out


def run_job(job: dict, run_leg: Callable | None = None, before_leg: Callable | None = None) -> dict:
    """ONE JOB (3.4), its legs one after another in this process, each through `run_leg` (live: `live_step5.run_arm`; the
    tests pass a stub). Every leg that launched, or was refused before its launch, gets ONE record in records.jsonl; the job
    gets one job record; the profile is deleted at the end (a leftover is named). `before_leg(index, leg, start, env)` is
    a test hook, called right before a leg's custody check."""
    from ai_player.gates import live_step5 as L5
    from ai_player.gates.live_step2 import check_purity
    from ai_player.host import launcher

    run_leg = run_leg or L5.run_arm
    out = Path(job["out"])
    build_root = Path(job["build_root"])
    legs = job["legs"]
    mc = bool(job.get("mc"))
    chain = job["chain"]
    ran: list[str] = []
    stopped_at, stop_reason, reached_last = None, None, False
    refusal = profile_refusal(job, L5.PROFILE, build_root) or legs_refusal(job)
    if refusal is None:
        try:
            launcher.ensure_profile(build_root, job["profile"], template=DONOR)
        except launcher.LaunchError as error:
            refusal = f"the donor profile: LaunchError: {error}"
    if refusal is not None:
        append_record(out, refused_record(job, legs[0], 0, refusal))
        not_run = [leg["leg"] for leg in legs[1:]]
        path = build_root / "profiles" / str(job.get("profile"))
        deleted, leftover = (True, None)
        if refusal.startswith("the profile ") and path.exists():
            deleted, leftover = False, f"{path} (it existed before the job: named, never deleted by it)"
        elif path.exists():
            deleted, leftover = delete_profile(build_root, job["profile"])
        record = job_record(job, [legs[0]["leg"]], legs[0]["leg"], f"REFUSED: {refusal}", False, deleted, leftover,
                            not_run)
        append_record(out, record)
        return record
    prev: dict | None = None
    prev_row: dict | None = None
    lc_job = {"chain": chain, "seed": job["seed"], "personality": job["persona"], "starter": job["starter"],
              "profile": job["profile"]}
    for index, leg in enumerate(legs):
        why = stop_seen(out)
        if why is None and not leg_fits(time.time(), leg, job.get("deadline")):
            why = f"the deadline {job.get('deadline')} leaves no room for {leg['leg']}"
        if why is not None:
            stopped_at, stop_reason = leg["leg"], why
            break
        start = leg_start(job, index, prev)
        fresh = start["fresh"]
        arm_name = f"{chain}-{leg['leg']}"
        env = L5.play_env(job["persona"], job["starter"] if fresh else None, leg["target"])
        if start["carry"]:
            env[ENV_GOALS] = str(start["goals"])
        sent = {ENV_BRAIN: "play", ENV_SEED: str(job["seed"]), **env}
        if not fresh:
            sent[ENV_WORLD] = str(start["world"])
        start_memory = {"goal_memory": "carried" if start["carry"] else "none",
                        "goals_sha256": start.get("goals_sha256") if start.get("goals") else None,
                        "losses_carried": losses_of(start["snapshot"]) if start["carry"] else 0,
                        "fallback_for": start.get("fallback_for")}
        if before_leg is not None:
            before_leg(index, leg, start, sent)
        problems = env_problems(sent, mc) if fresh else custody_problems(start, sent, mc)
        if problems:
            append_record(out, refused_record(job, leg, index, "custody: " + "; ".join(problems), start_memory))
            ran.append(leg["leg"])
            stopped_at, stop_reason = leg["leg"], "REFUSED before the launch: custody: " + "; ".join(problems)
            break
        arm = L5.Arm(arm_name, f"A1 {job['batch']} {chain} {leg['leg']}: chapter {leg['chapter']} to {leg['target']} "
                               f"({job['persona']}, {job['starter']}, seed {job['seed']})",
                     int(leg["frames"]), float(leg["wall"]), env, seed=int(job["seed"]), fresh=fresh,
                     state_from=None if fresh else "START")
        carried = {} if fresh else {"START": (Path(start["state"]), Path(start["world"]), start["reads"])}
        write_json(out / chain / "current_leg.json", {"leg": leg["leg"], "arm": arm_name,
                                                      "started": time.strftime("%Y-%m-%d %H:%M:%S")})
        ran.append(leg["leg"])
        try:
            run = run_leg(arm, build_root, carried)
        except Exception as error:  # noqa: BLE001 - a crashed leg is salvaged (INFRA), its world measured and deleted
            reason = f"the leg raised {type(error).__name__}: {LC.safe_text(error, 300)}"
            row = LC.salvage_leg({**job, "personality": job["persona"]}, leg, build_root, out, arm_name, reason, "ERROR")
            append_record(out, salvaged_record(job, leg, index, row, reason, start_memory))
            stopped_at, stop_reason = leg["leg"], f"INFRA: {reason}"
            break
        try:
            record, row, nxt = judge_leg(job, leg, index, run, start, start_memory, prev_row, lc_job, check_purity, L5)
        except Exception as error:  # noqa: BLE001 - the harness failed to judge it: INFRA, never the AI's
            reason = f"judging the leg raised {type(error).__name__}: {LC.safe_text(error, 300)}"
            row = LC.salvage_leg({**job, "personality": job["persona"]}, leg, build_root, out, arm_name, reason, "ERROR")
            append_record(out, salvaged_record(job, leg, index, row, reason, start_memory))
            stopped_at, stop_reason = leg["leg"], f"INFRA: {reason}"
            break
        append_record(out, record)
        if record["reached"]:
            reached_last = index == len(legs) - 1
        if not record["continue"]["go"]:
            stopped_at, stop_reason = leg["leg"], record["continue"]["why"]
            break
        prev, prev_row = nxt, row
    not_run = [leg["leg"] for leg in legs if leg["leg"] not in ran]
    LC.end_sweep([job], build_root)
    deleted, leftover = delete_profile(build_root, job["profile"])
    record = job_record(job, ran, stopped_at, stop_reason, reached_last, deleted, leftover, not_run)
    append_record(out, record)
    return record


def judge_leg(job: dict, leg: dict, index: int, run, start: dict, start_memory: dict, prev_row: dict | None,
              lc_job: dict, check_purity: Callable, L5) -> tuple[dict, dict, dict]:
    """One launched leg judged from FILES: purity and freshness as `run_chain` judges them; the live_chain row (so
    `finish_leg`, `launch_died`, `leg_reached`, `continue_after` and an MC job's `custody_problems` read it as their own);
    the class; the next unmet milestone and the key; the measures; the experience; the kept example and its zip; the
    continue decision. Returns (the record, the row, what the next leg starts from)."""
    out = Path(job["out"])
    mc = bool(job.get("mc"))
    notes: list[str] = []
    LC.judged(lambda: check_purity(run, None), "the purity checks", run.notes)
    LC.judged(lambda: L5.check_after_is_this_run(run), "L5.THIS_RUN", run.notes)
    sent = {ENV_BRAIN: "play", ENV_SEED: str(run.arm.seed), **run.arm.env}
    if run.world_in is not None:
        sent[ENV_WORLD] = str(run.world_in)
    before, after = LC._truth_subset(run.before), LC._truth_subset(run.after)
    fresh_leg = start["fresh"]
    proof_before = (LC.proof_holds(before.get("marks"), leg["proof"]) if before
                    else None if fresh_leg else {"unread": True, "held": None})
    row = {"chain": job["chain"], "leg": leg["leg"], "chapter": leg["chapter"], "target": leg["target"],
           "proof": leg["proof"], "frames": leg["frames"], "wall": leg["wall"], "arm": run.arm.name, "status": "RAN",
           "reason": None, "exit": run.exit_code, "elapsed": round(run.elapsed or 0, 1),
           "run_dir": str(run.run_dir) if run.run_dir else None, "command": [str(c) for c in run.command],
           "env": sent, "env_keys": sorted(sent), "world_in": str(run.world_in) if run.world_in else None,
           "world_in_sha256": sha256_of(Path(run.world_in)) if run.world_in and Path(run.world_in).is_file() else None,
           "start_state": str(run.start_state) if run.start_state else None, "truth_before": before,
           "truth_after": after, "proof_before": proof_before,
           "proof_after": LC.proof_holds((after or {}).get("marks"), leg["proof"]) if after else
           {"held": False, "missing": ["(no end truth)"], "failing": [], "values": {}},
           "checks": LC.check_rows(run.checks), "harness_stop": run.measures.get("harness_stop"),
           "outcome": LC.untrusted_text(LC.dig(run.verdict, "facts", "exit_reason")),
           "gate_line": next((ln for ln in run.stdout.splitlines() if ln.startswith("[AI-GATE]")), None),
           "notes": list(run.notes)}
    row["reached"] = LC.leg_reached(row)[0]
    keep = out / job["chain"] / leg["leg"]
    marker = LC.guard_mark(out, job["chain"], leg["leg"])
    parsed_tail = None
    if marker and run.run_dir is not None and (Path(run.run_dir) / "world.jsonl").is_file():
        parsed_tail = last_parsed_object(Path(run.run_dir) / "world.jsonl")
    LC.finish_leg(row, run.run_dir, keep)
    row["harness"] = LC.launch_died(row)
    row["guard_killed"] = marker if marker and marker.get("cause") in ("world", "profile") else None
    run_dir = Path(run.run_dir) if run.run_dir else None
    goals_sha = None
    if run_dir is not None and (run_dir / GOALS_FILE).is_file():
        try:
            shutil.copy2(run_dir / GOALS_FILE, keep / GOALS_FILE)
            last = last_line_of(run_dir / GOALS_FILE)
            if last is not None:
                (keep / "goals_last.jsonl").write_bytes(last if last.endswith(b"\n") else last + b"\n")
                goals_sha = sha256_of(keep / "goals_last.jsonl")
        except OSError as error:
            notes.append(f"the goal snapshot could not be kept: {type(error).__name__}")
    row["kept_goals"] = str(keep / "goals_last.jsonl") if goals_sha else None
    reads = [r for r in list(run.earlier) + list(run.records) if isinstance(r, dict) and r.get("decision") == "read"]
    keep.mkdir(parents=True, exist_ok=True)
    (keep / "reads.jsonl").write_text("".join(json.dumps(utf8_safe(r), ensure_ascii=False) + "\n" for r in reads),
                                      encoding="utf-8")
    profile_dir = Path(job["build_root"]) / "profiles" / job["profile"]
    ai_files = keep_ai_files(profile_dir, keep)
    end_state = run_dir / "end_state.ss1" if run_dir is not None else None
    state_md5 = md5_of(end_state) if end_state is not None and end_state.is_file() else None
    # --- the class
    verdict = run.verdict if isinstance(run.verdict, dict) else None
    statuses = {c["id"]: c["status"] for c in row["checks"]}
    fresh = statuses.get("L5.THIS_RUN") == LC.PASS
    facts = {"guard": (marker or {}).get("cause"), "exit": run.exit_code, "stdout": run.stdout, "verdict": verdict,
             "driver_killed": bool(getattr(run, "driver_killed", False)), "launch_died": row["harness"], "fresh": fresh,
             "end_truth": after is not None, "frames": leg["frames"], "mc": mc}
    klass, class_why = classify(facts)
    # --- custody: an MC job's is live_chain's own (E0's harness); an A1 leg's was checked before its launch
    row["custody"] = LC.custody_problems(row, prev_row, lc_job, index) if mc else []
    # --- the next unmet milestone and the key
    data = load_staged_milestones()
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    truth, truth_from = truth_for_next(before, after, written)
    unmet = next_unmet((truth or {}).get("marks") if truth else None, data)
    records = [r for r in run.records if isinstance(r, dict)]
    world = parse_object((keep / "world_last.jsonl").read_bytes()) if (keep / "world_last.jsonl").is_file() else None
    if world is None and parsed_tail is not None:
        world = parsed_tail
        notes.append("the kept world line did not parse (a kill cut it): the measures read the last line that did")
    start_frame = (before or {}).get("frame") if before else (0 if fresh_leg else None)
    end_frame = end_frame_of(end_written(before, after, written), after, records, world, start_frame)
    reason_text = LC.untrusted_text(LC.dig(verdict, "facts", "exit_reason")) if verdict else None
    reached = bool(row["reached"])
    claim = (klass == CLEAN_CHOSEN and reason_text == f"play: done: {leg['target']} reached"
             and not (row.get("proof_after") or {}).get("held"))
    loop = None
    try:
        loop = loop_measure(world, start_frame, end_frame, leg["frames"], records)
    except Exception as error:  # noqa: BLE001 - the AI's files are untrusted: a failed measure is a note
        notes.append(f"the loop measure failed: {type(error).__name__}")
    class_text = {CUT_WORLD: class_why, HUNG: HUNG_TEXT}.get(klass)
    reason = reason_norm(reason_text or class_text or class_why)
    if not reached and klass == CLEAN_BUDGET and (loop or {}).get("raise_active_at_end"):
        reason = RAISE_TEXT
    if loop is not None:
        loop["keyed"] = loop_keyed(loop, reached, klass, reason)
        loop["churn"] = reached and loop["crossings"] - loop["crossings_raise"] >= LOOP_MIN_CROSSINGS
    end_map = end_map_of(klass, after, world)
    blocker = blocker_of(leg["chapter"], unmet["next"], reason, end_map["const"], klass, reached, loop)
    # --- the record
    counters = (verdict or {}).get("counters") if isinstance((verdict or {}).get("counters"), dict) else {}
    real = counters.get("real_frames") if isinstance(counters.get("real_frames"), int) else None
    record = base_record(job, leg, index)
    record["job"]["start"]["reads_carried"] = len(start.get("reads") or [])
    this_run = next((c for c in run.checks if getattr(c, "id", None) == "L5.THIS_RUN"), None)
    record.update({
        "launch": {"exit": run.exit_code, "elapsed": round(run.elapsed or 0, 1),
                   "fps": round(real / run.elapsed, 1) if real and run.elapsed else None,
                   "driver_killed": bool(getattr(run, "driver_killed", False)), "guard": marker,
                   "env_keys": sorted(sent), "command_sha256": text_sha256(json.dumps([str(c) for c in run.command])),
                   "started": run.started},
        "verdict": {"word": untrusted((verdict or {}).get("verdict"), 40) if verdict else None,
                    "exit_reason": untrusted(reason_text, 300), "real_frames": real},
        "fresh": {"ok": fresh, "text": LC.safe_text(getattr(this_run, "text", None), 400) if this_run else None},
        "class": klass, "class_why": class_why, "reached": reached, "claim_mismatch": bool(claim),
        "truth": {"before": {"map": before.get("map"), "frame": before.get("frame")} if before else None,
                  "after": {"map": after.get("map"), "frame": after.get("frame")} if after else None},
        "milestones_held": unmet["held"], "next_unmet": unmet["next"], "next_unmet_from": truth_from,
        "next_unmet_unread": unmet["unread"], "end_map": end_map, "blocker": blocker,
        "measures": {"world_bytes": (row.get("world_file") or {}).get("bytes"),
                     "world_over_300mb": isinstance((row.get("world_file") or {}).get("bytes"), int)
                     and row["world_file"]["bytes"] >= WORLD_REPORT_BYTES,
                     "world_deleted": (row.get("world_file") or {}).get("deleted"),
                     "log": (row.get("measures") or {}).get("log"), "loop": loop, "k1_leads": k1_leads(records),
                     "stale": stale_measure(start["mode"], tried_items_of(start.get("snapshot")), records,
                                            memory_line_of(run.ai_log)),
                     "frames": {"start": start_frame, "end": end_frame}},
        "start_memory": start_memory,
        "bossprep": bossprep_fields(records, run.ai_log, job["persona"], end_frame),
        "rides": rides_delta(parse_object(last_line_of(Path(start["world"]))) if start.get("world") else None, world),
        "custody": row["custody"], "notes": [*row.get("notes", []), *notes]})
    # --- the experience (CLEAN-* only)
    if klass in CLEAN_CLASSES and world is not None:
        static, unclassified = extract_static(world)
        write_json(keep / "static.json", static)
        fights, wild = fights_of(records)
        append_record(out, {"schema_version": SCHEMA_VERSION, "run_id": record["run_id"], "tree": record["tree"],
                            "origin": job.get("origin"), "chapter": leg["chapter"], "leg": leg["leg"],
                            "persona": job["persona"], "starter": job["starter"],
                            "end": {"map": end_map["const"], "class": klass, "reached": reached}, "fights": fights,
                            "wild": wild, "maps_sha256": text_sha256(json.dumps(static, sort_keys=True)),
                            "unclassified": unclassified}, EXPERIENCE)
        record["experience"] = {"written": True, "fights": len(fights), "unclassified": unclassified}
    # --- the continue decision
    stop_now = (out / STOP_FILE).is_file()
    lc_go, lc_why = LC.continue_after(row, stop_now)
    if mc:
        go, why = lc_go, lc_why
    else:
        go, why = continue_rule(row, klass, stop_now, carries_goals=job.get("goals", "carry") == "carry")
        if go and not lc_go:
            notes.append(f"live_chain's continue_after would stop here ({lc_why}): A1 reports the world size, never "
                         f"stops on it (3.6)")
    if row["harness"]:
        why = f"{row['harness']}; {why}"
    record["continue"] = {"go": go, "why": why, "live_chain": {"go": lc_go, "why": lc_why}}
    # --- the kept example, the logs zipped (verified first)
    LC._write_json(keep / "row.json", row)
    zipped = zip_logs(keep)
    world_sha = row.get("kept_world_sha256")
    record["kept"] = {"folder": str(keep), "zip": zipped.get("zip"), "zip_sha256": zipped.get("zip_sha256"),
                      "zip_verified": zipped.get("verified"), "zip_problem": zipped.get("problem"),
                      "raw": sorted(p.name for p in keep.iterdir() if p.is_file() and p.name != "logs.zip"),
                      "state_md5": state_md5, "world_sha256": world_sha, "goals_sha256": goals_sha, "ai_files": ai_files}
    record["notes"] = [*record["notes"], *[n for n in notes if n not in record["notes"]]]
    record["ended"] = time.time()
    nxt = {"state": str(end_state) if end_state is not None else None, "state_md5": state_md5,
           "world": row.get("kept_world"), "world_sha256": world_sha,
           "goals": str(keep / "goals_last.jsonl") if goals_sha else None, "goals_sha256": goals_sha,
           "reads": reads}
    return record, row, nxt


_STAGED_MILESTONES: dict | None = None


def load_staged_milestones() -> dict:
    """The milestones.json of the code this process runs (in a child: the STAGE's own copy)."""
    global _STAGED_MILESTONES
    if _STAGED_MILESTONES is None:
        _STAGED_MILESTONES = LC.load_milestones(REPO)
    return _STAGED_MILESTONES


def salvaged_record(job: dict, leg: dict, index: int, row: dict, reason: str, start_memory: dict | None = None) -> dict:
    """A leg whose launch raised, or whose child died, salvaged (`live_chain.salvage_leg`): INFRA, its world measured and
    deleted, no check made."""
    record = base_record(job, leg, index)
    world = (row.get("world_file") or {})
    record.update({"class": INFRA, "class_why": f"salvaged: {reason}", "start_memory": start_memory,
                   "measures": {"world_bytes": world.get("bytes"), "world_deleted": world.get("deleted"),
                                "world_over_300mb": isinstance(world.get("bytes"), int)
                                and world["bytes"] >= WORLD_REPORT_BYTES},
                   "kept": {"folder": str(Path(job["out"]) / job["chain"] / leg["leg"]), "run_dir": row.get("run_dir")},
                   "notes": list(row.get("notes") or []), "ended": time.time()})
    record["continue"] = {"go": False, "why": f"INFRA: salvaged ({reason})", "live_chain": None}
    return record


def child(job_path: Path) -> int:
    """`child JOB.json`: one job, run from its STAGE (this file's own copy there, so every import is the stage's code)."""
    sanitize_environ()
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    from ai_player.gates import live_step5 as L5

    L5.PROFILE = job["profile"]
    record = run_job(job)
    print(f"[{job['chain']}] legs {record['legs_ran']} stopped at {record['stopped_at']}: {record['stop_reason']}",
          flush=True)
    return 0


# ====================================================================== the batch (3.13: the orchestrator)
def folder_bytes(path: Path) -> int:
    """The bytes of every file under `path` (links never followed; a file gone mid-walk counts 0)."""
    total = 0
    for root, folders, files in os.walk(path, followlinks=False):
        folders[:] = [f for f in folders if not is_link(Path(root) / f)]
        for name in files:
            with contextlib.suppress(OSError):
                total += os.stat(os.path.join(root, name), follow_symlinks=False).st_size
    return total


def python_processes() -> list[str]:
    """The command lines of every process running pokebot.py or run_regression.py (the singles cap and the lane WAIT)."""
    try:
        done = subprocess.run(["powershell", "-NoProfile", "-Command",
                               "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*pokebot.py*' -or "
                               "$_.CommandLine -like '*run_regression.py*' -or $_.CommandLine -like '*frontier_probe.py*' } "
                               "| ForEach-Object { $_.CommandLine }"], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    return [line.strip() for line in done.stdout.decode(errors="replace").splitlines() if line.strip()]


def singles_of(commands: Iterable[str]) -> int:
    """Other singles: pokebot.py processes without --endless-target that are not this probe's (`ai-fp-` profiles)."""
    return sum(1 for c in commands if "pokebot.py" in c and "--endless-target" not in c and PROFILE_PREFIX not in c)


def regression_running(commands: Iterable[str]) -> bool:
    return any("run_regression.py" in c for c in commands)


def child_env() -> dict[str, str]:
    """A child's environment: this one's without every AI_PLAYER_*, POKEBOT_* and refused PYTHON* variable (the child
    strips them again itself, before any launcher import)."""
    env = {k: v for k, v in os.environ.items()
           if not (k.upper().startswith(STRIPPED_PREFIXES) or LC.python_env_refused(k))}
    env.update({"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


class ChildProcess:
    """One job's child: `py -B <stage>/code/ai_player/gates/frontier_probe.py child JOB.json`, cwd the stage's code root,
    its output in `<out>/logs/<chain>.child.log`."""

    def __init__(self, job: dict, job_path: Path, log_path: Path) -> None:
        stage = Path(job["stage_dir"])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = open(log_path, "w", encoding="utf-8")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        script = stage / "code" / "ai_player" / "gates" / "frontier_probe.py"
        self.proc = subprocess.Popen([sys.executable, "-B", str(script), "child", str(job_path)], cwd=str(stage / "code"),
                                     env=child_env(), stdout=self.log, stderr=subprocess.STDOUT, creationflags=flags)
        self.pid = self.proc.pid

    def poll(self) -> int | None:
        code = self.proc.poll()
        if code is not None and not self.log.closed:
            self.log.close()
        return code

    def kill_tree(self) -> None:
        from ai_player.gates.live_ki128 import kill_descendants

        kill_descendants(self.pid)
        with contextlib.suppress(OSError):
            self.proc.kill()


def spawn_child(job: dict, job_path: Path, log_path: Path) -> ChildProcess:
    return ChildProcess(job, job_path, log_path)


def _kill_descendants(pid: int) -> list:
    from ai_player.gates.live_ki128 import kill_descendants

    return kill_descendants(pid)


def _snapshot(repo: Path) -> object:
    """`provenance.snapshot_tree` of the orchestrator's repository, into THAT repository's evidence/trees (never another's)."""
    from ai_player.gates.provenance import snapshot_tree

    return snapshot_tree(repo, Path(repo) / "ai_player" / "evidence" / "trees")


@dataclass
class Deps:
    """The orchestrator's side effects, injected (the tests run whole batches with stub children, a temp ledger, a temp
    evidence folder, planted free space, planted process lists and planted file sizes)."""
    spawn: Callable = spawn_child
    free: Callable[[Path], float | None] = LC.safe_free
    processes: Callable[[], list[str]] = python_processes
    kill: Callable[[int], list] = _kill_descendants
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    now: Callable[[], float] = time.time
    folder_bytes: Callable[[Path], int] = folder_bytes
    newest_world: Callable[[Path], tuple] = LC.newest_world
    work_tree: Callable[[Path], bool] = inside_work_tree
    stage_digest: Callable[[Path], str] = stage_code_digest
    sandbox_digest: Callable[[Path], str] = sandbox_tracked_digest
    seed_ledgers: Callable[[Path], list[Path]] = lambda path: default_seed_ledgers([path])
    snapshot: Callable[[Path], object] = _snapshot
    ledger_path: Path | None = None
    evidence_dir: Path | None = None
    repo: Path | None = None
    poll_seconds: float = TICK_SECONDS
    stagger: float | None = None
    stage_every: float = STAGE_WATCH_SECONDS
    sandbox_every: float = SANDBOX_WATCH_SECONDS
    events: list = field(default_factory=list)


def parse_stages(text: str) -> dict[str, Path]:
    stages = {}
    for part in str(text or "").split(","):
        name, _, folder = part.partition("=")
        if not name.strip() or not folder.strip():
            raise Refusal(f"--stage {text!r}: ARM=DIR[,ARM=DIR]")
        stages[name.strip()] = Path(folder.strip()).resolve()
    return stages


def event(out: Path, deps: Deps, text: str) -> None:
    deps.events.append(text)
    with contextlib.suppress(Exception):
        append_record(out, {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "event": text}, EVENTS)
    print(f"[A1] {text}", flush=True)


def write_marker(out: Path, chain: str, leg: str, cause: str, text: str) -> bool:
    marker = Path(out) / chain / f"{leg}.KILLED.json"
    if marker.exists():
        return False
    write_json(marker, {"cause": cause, "text": text})
    return True


def salvage_job(job: dict, out: Path, why: str) -> dict:
    """A job whose child ended without its job record (it died, was killed, or a resumed batch finds it unfinished): its
    finished legs are kept, the leg in flight is salvaged (`live_chain.salvage_leg`: INFRA, its world measured and
    deleted), the later legs NOT RUN; then its job record and its profile deleted."""
    records = read_records(out)
    have = {r.get("run_id") for r in records if r.get("record") == "leg"}
    current = read_json(Path(out) / job["chain"] / "current_leg.json")
    build_root = Path(job["build_root"])
    ran, not_run = [], []
    stopped_at, stop_reason = None, f"the job's process ended ({why})"
    for index, leg in enumerate(job["legs"]):
        if run_id_of(job["batch"], job["chain"], leg["leg"]) in have:
            ran.append(leg["leg"])
            continue
        if isinstance(current, dict) and current.get("leg") == leg["leg"] and stopped_at is None:
            row = LC.salvage_leg({**job, "personality": job["persona"]}, leg, build_root, Path(out), current["arm"],
                                 f"the job's process ended during this leg ({why})")
            if row.get("status") != "NOT RUN":
                append_record(out, salvaged_record(job, leg, index, row, why))
                ran.append(leg["leg"])
            else:
                not_run.append(leg["leg"])
            stopped_at = leg["leg"]
            continue
        not_run.append(leg["leg"])
        if stopped_at is None:
            stopped_at = leg["leg"]
    LC.end_sweep([job], build_root)
    deleted, leftover = delete_profile(build_root, job["profile"])
    record = job_record(job, ran, stopped_at, stop_reason, False, deleted, leftover, not_run)
    append_record(out, record)
    return record


def bounds_of(jobs_raw: bytes, prediction_raw: bytes | None, manifests: dict[str, dict]) -> tuple[str, dict]:
    """The development entry's bounds (3.10): the sha256 of jobs.json, the prediction file, frontier_probe.py and every
    stage manifest, hashed together."""
    parts = {"jobs.json": hashlib.sha256(jobs_raw).hexdigest(),
             "prediction": hashlib.sha256(prediction_raw).hexdigest() if prediction_raw is not None else None,
             "frontier_probe.py": sha256_of(Path(__file__)),
             "manifests": {name: text_sha256(json.dumps(m, sort_keys=True)) for name, m in sorted(manifests.items())}}
    return text_sha256(json.dumps(parts, sort_keys=True)), parts


def run_refusals(args, deps: Deps, jobs: list | None, stages: dict[str, Path], manifests: dict[str, dict],
                 out: Path, mode: str) -> list[str]:
    """Every refusal judged BEFORE any launch and any ledger write (exit 2)."""
    problems: list[str] = []
    if jobs is None:
        return ["--jobs is not a JSON list of jobs"]
    if not jobs:
        # an EMPTY list is refused here, before --out is made (verifier round 3, N4: it crashed after the mkdir, exit 5)
        return ["--jobs holds no job (an empty list): nothing to run"]
    if int(args.parallel) < 1:
        # (fix round 5, V4-N3, MAJOR by impact) P under 1 admits no job, so the scheduler would wait forever: refused here,
        # before --out is made, any ledger write or any launch
        problems.append(f"--parallel {args.parallel} is under 1: no job could ever start (the scheduler would never end)")
    problems += jobs_problems(jobs)
    for name, stage in stages.items():
        problems += placement_problems(stage, f"the stage {name}", deps.work_tree)
        for what in ("repo", "sandbox"):
            target = (manifests.get(name) or {}).get(what)
            if target and "pokebot-learner" in (part.lower() for part in Path(target).parts):
                problems.append(f"the stage {name}'s {what} {target} lies in a folder named pokebot-learner")
    problems += placement_problems(out, "--out", deps.work_tree)
    for job in jobs:
        if job.get("stage") not in stages:
            problems.append(f"{job.get('chain')}: its stage {job.get('stage')!r} is not given (--stage {sorted(stages)})")
    if not args.resume and out.exists() and any(out.iterdir()):
        problems.append(f"--out {out} exists and is not empty (give a new folder, or --resume a batch)")
    if args.resume and not (out / BATCH_FILE).is_file():
        problems.append(f"--resume: {out} holds no {BATCH_FILE}")
    if args.resume:
        alive = [c for c in deps.processes() if "frontier_probe.py" in c and " child " in f" {c} " and str(out) in c]
        if alive:
            problems.append(f"--resume while {len(alive)} child process(es) of this --out still run")
    for name, stage in stages.items():
        free = deps.free(stage)
        refusal = start_refusal(free)
        if refusal:
            problems.append(f"the stage {name}'s drive: {refusal}")
    return problems


def run_batch(args, deps: Deps | None = None) -> int:
    """THE BATCH (3.13). Exit 0 ran, 2 refused before any launch, 3 ABORTED, 4 ERROR after ledger.begin, 6 the AI-only
    stop."""
    deps = deps or Deps()
    mode = "trainer" if args.trainer else "development"
    out = Path(args.out).resolve()
    ledger_path = Path(deps.ledger_path or ledger.LEDGER)
    evidence_dir = Path(deps.evidence_dir or EVIDENCE_DIR)
    try:
        jobs_raw = Path(args.jobs).read_bytes()
        jobs = json.loads(jobs_raw)
        jobs = jobs if isinstance(jobs, list) and all(isinstance(j, dict) for j in jobs) else None
    except (OSError, ValueError) as error:
        print(f"REFUSED: --jobs {args.jobs}: {error}", flush=True)
        return 2
    try:
        stages = parse_stages(args.stage)
    except Refusal as error:
        print(f"REFUSED: {error}", flush=True)
        return 2
    manifests, problems = {}, []
    for name, stage in stages.items():
        manifest, found = manifest_problems(stage)
        problems += found
        if manifest is not None:
            manifests[name] = manifest
    problems += run_refusals(args, deps, jobs, stages, manifests, out, mode)
    free = deps.free(out if out.exists() else out.parent if out.parent.exists() else Path(out.anchor))
    refusal = start_refusal(free)
    if refusal:
        problems.append(f"--out's drive: {refusal}")
    mc_batch = bool(jobs) and all(job.get("mc") for job in jobs)
    parallel, why = parallel_of(int(args.parallel), free or 0.0, mc_batch) if free is not None else (0, "no free space")
    if why:
        problems.append(why)
    if mc_batch:
        parallel = min(parallel, MC_PARALLEL)
    prediction_raw = None
    entry_id = None
    known: list[str] = []
    old = read_json(out / BATCH_FILE) if args.resume else None
    if jobs:
        if mode == "development":
            if not args.prediction_file:
                problems.append("development mode needs --prediction-file")
            else:
                try:
                    prediction_raw = Path(args.prediction_file).read_bytes()
                    if not prediction_raw.decode("utf-8").strip():
                        problems.append("the prediction file is empty")
                except (OSError, UnicodeDecodeError) as error:
                    problems.append(f"the prediction file cannot be read as UTF-8 text: {error}")
            span = seed_span(jobs)
            if span is None:
                problems.append("development seeds must be ONE contiguous range")
            else:
                ignore = ()
                if isinstance(old, dict) and old.get("entry_id") is not None:
                    ignore = ((str(ledger_path), int(old["entry_id"])),)
                    entry_id = int(old["entry_id"])
                hits, unreadable, known = seeds_named(span[0], span[1], deps.seed_ledgers(ledger_path), ignore)
                problems += [f"a seed of {span[0]}-{span[1]} is named: {hit}" for hit in hits[:8]]
                problems += [f"a ledger could not be read: {item}" for item in unreadable[:8]]
                for item in known:
                    print(f"NOTE: a known non-ledger could not be read (allowed, 2.5): {item}", flush=True)
        else:
            try:
                data = ledger.load(ledger_path)
            except (OSError, ValueError) as error:
                data = {"entries": []}
                problems.append(f"the ledger cannot be read: {error}")
            problems += trainer_problems([job["seed"] for job in jobs], data)
    if isinstance(old, dict) and old.get("jobs_sha256") != hashlib.sha256(jobs_raw).hexdigest():
        problems.append("--resume with another jobs.json than the batch's")
    if problems:
        for problem in problems:
            print(f"REFUSED: {problem}", flush=True)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    batch_name = jobs[0]["batch"]
    started = old.get("started") if isinstance(old, dict) else time.strftime("%Y-%m-%d %H:%M:%S")
    bounds, parts = bounds_of(jobs_raw, prediction_raw, manifests)
    if mode == "development" and entry_id is None:
        real = manifests.get("REAL") or next(iter(manifests.values()))
        deps.snapshot(Path(deps.repo or REPO))
        span = seed_span(jobs)
        try:
            entry, _ = ledger.begin(FAMILY, DRIVER, "development", span[0], span[1], bounds, real.get("play_digest"),
                                    note=f"A1 frontier probe {batch_name}, {len(jobs)} jobs, P {parallel}, prediction sha256 "
                                         f"{(parts['prediction'] or '-')[:16]}, {free:.1f} GB free", path=ledger_path)
        except ledger.Refused as error:
            print(f"REFUSED by the ledger: {error}", flush=True)
            return 2
        entry_id = entry["id"]
    facts = {"batch": batch_name, "mode": mode, "started": started, "entry_id": entry_id, "ledger": str(ledger_path),
             "jobs_sha256": hashlib.sha256(jobs_raw).hexdigest(), "bounds_sha256": bounds, "bounds": parts,
             "parallel": parallel, "parallel_asked": int(args.parallel), "free_gb": free,
             "stages": {name: str(path) for name, path in stages.items()}, "deadline": args.deadline,
             "max_wait": args.max_wait, "resumed": bool(args.resume), "known_non_ledgers": known,
             # (fix round 6, V6-1) every PLANNED MC chain and its legs, so the merge check counts a job DROPPED before its
             # launch (it writes no leg and no job record) as a chain that did not run, never as no chain
             "mc_planned": {job["chain"]: [leg["leg"] for leg in job.get("legs") or []] for job in jobs if job.get("mc")}}
    write_json(out / BATCH_FILE, facts)
    try:
        result = drive(jobs, out, stages, manifests, facts, args, deps)
        report = write_report(out)
        if mode == "development":
            evidence = write_evidence(out, facts, result, report, evidence_dir, args.prediction_file, prediction_raw)
            verdict = finish_verdict(result, report)
            ledger.finish(entry_id, verdict, evidence.relative_to(Path(deps.repo or REPO)).as_posix()
                          if evidence.is_relative_to(Path(deps.repo or REPO)) else str(evidence), path=ledger_path)
    except BaseException as error:  # noqa: BLE001 - after the entry began, any exception finishes it as ERROR
        text = f"ERROR (harness: {type(error).__name__}: {LC.safe_text(error, 300)}; no blocker report)"
        print(text, flush=True)
        traceback.print_exc()
        if mode == "development" and entry_id is not None:
            with contextlib.suppress(Exception):
                ledger.finish(entry_id, text, None, path=ledger_path)
        if not isinstance(error, Exception):
            raise
        return 4
    if result["aborted"]:
        return 3
    if result["ai_stop"]:
        return 6
    return 0


def finish_verdict(result: dict, report: dict) -> str:
    """The development entry's verdict. An MC batch's names the merge check's READING, PASS or STOP (2.4b names both: a
    hard-break check, never a rate; verifier round 3, N7), first, so the ledger line says it."""
    legs = report.get("legs", 0)
    reached = report.get("reached", 0)
    mc = report.get("mc")
    reading = ""
    if mc:
        problems = "; ".join(str(p) for p in mc.get("problems") or [])
        reading = (f"THE MERGE CHECK (MC, 2.4b, a hard-break check, never a rate) reads {mc['reading']} over "
                   f"{mc['chains']} chains{': ' + problems[:400] if problems else ''}; ")
    if result["aborted"]:
        return f"ABORTED (disk: under {ABORT_FREE_GB:g} GB free): {reading}{legs} legs ran, {reached} reached; " \
               "DEVELOPMENT, never graded"
    stop = "; the AI-only stop" if result["ai_stop"] else ""
    return (f"DEVELOPMENT, never graded: {reading}{legs} legs ran, {reached} reached, classes {report.get('classes')}; "
            f"{len(report.get('blockers') or [])} blocker keys{stop}; the report is blockers.json")


def write_evidence(out: Path, facts: dict, result: dict, report: dict, evidence_dir: Path, prediction_file,
                   prediction_raw: bytes | None) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    path = evidence_dir / f"{stamp}-a1-frontier-{facts['batch']}.txt"
    n = 2
    while path.exists():
        path = evidence_dir / f"{stamp}-a1-frontier-{facts['batch']}-{n}.txt"
        n += 1
    lines = [f"A1 FRONTIER PROBE, batch {facts['batch']} ({facts['mode']}): {HEADER}",
             f"ledger entry #{facts['entry_id']}; bounds sha256 {facts['bounds_sha256']}; started {facts['started']}",
             f"stages {facts['stages']}; P {facts['parallel']} (asked {facts['parallel_asked']}, {facts['free_gb']} GB free)",
             f"prediction file {prediction_file} sha256 "
             f"{hashlib.sha256(prediction_raw).hexdigest() if prediction_raw is not None else '-'}", ""]
    for record in read_records(out):
        if record.get("record") == "leg":
            lines.append(f"LEG {record.get('run_id')}: {record.get('class')} reached {record.get('reached')} next unmet "
                         f"{record.get('next_unmet')} key {(record.get('blocker') or {}).get('key')} fps "
                         f"{(record.get('launch') or {}).get('fps')}")
    lines += ["", f"not started: {result['not_started']}", f"most jobs at once: {result['most_running']}",
              f"free space: {facts['free_gb']} GB at the start, {LC.safe_free(out)} GB at the end",
              f"events: {result['events'][-50:]}", "",
              json.dumps({k: v for k, v in report.items() if k != "examples"}, indent=1, default=str)[:200000], "",
              "PREDICTION:", (prediction_raw or b"").decode("utf-8", "replace")]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def drive(jobs: list[dict], out: Path, stages: dict[str, Path], manifests: dict[str, dict], facts: dict, args,
          deps: Deps) -> dict:
    """The scheduler loop (3.13): `schedule`'s shape (at most P, the stagger, a tick after every pass) with GO, WAIT, SKIP
    and DROP; then every job that ended without its job record is salvaged; the end sweep."""
    stage_info = {name: (stages[name], manifests[name]) for name in stages}
    stagger = LC.STAGGER_SECONDS if deps.stagger is None else deps.stagger
    max_wait = float(args.max_wait if args.max_wait is not None else MAX_WAIT_SECONDS)
    records = read_records(out)
    finished = {r.get("job") for r in records if r.get("record") == "job"}
    started_any = {r.get("job", {}).get("id") for r in records if r.get("record") == "leg"}
    pending: list[dict] = []
    for job in jobs:
        if job["chain"] in finished:
            continue
        build = stage_info[job["stage"]][0] / "build"
        full = {**job, "out": str(out), "build_root": str(build), "stage_dir": str(stage_info[job["stage"]][0])}
        if args.resume and (job["chain"] in started_any or (out / job["chain"] / "current_leg.json").is_file()):
            salvage_job(full, out, "the batch was resumed")
            event(out, deps, f"{job['chain']}: resumed: its finished legs kept, the leg in flight salvaged as INFRA")
            continue
        pending.append(full)
    sandbox_marks = {name: deps.sandbox_digest(Path(manifest.get("sandbox") or stages[name]))
                     for name, manifest in manifests.items()}
    state = {"aborted": False, "ai_stop": False, "out_over": False, "last_stage": deps.clock(),
             "last_sandbox": deps.clock(), "last_pass": None}
    running: list[tuple[dict, object, float]] = []
    not_started: list[tuple[str, str]] = []
    waited: dict[str, float] = {}
    most = 0
    try:
        while pending or running:
            now_clock = deps.clock()
            delta = 0.0 if state["last_pass"] is None else max(0.0, now_clock - state["last_pass"])
            state["last_pass"] = now_clock
            records = read_records(out)
            legs_by_id = {r.get("run_id"): r for r in records if r.get("record") == "leg"}
            ended = {r.get("job") for r in records if r.get("record") == "job"} | {chain for chain, _ in not_started}
            commands: list[str] | None = None
            skipped = 0
            index = 0
            idle_at_start = not running
            launched = 0
            while index < len(pending) and len(running) < facts["parallel"]:
                job = pending[index]
                dependency = dependency_of(job, legs_by_id, ended, out, stage_info)
                if commands is None and (dependency is None or dependency[0] == "ready"):
                    commands = deps.processes()  # once a pass, and only for a job that could start (no PowerShell per SKIP)
                free = deps.free(out)
                reserve = None if free is None else free - sum(
                    max(0, profile_budget(bool(j.get("mc"))) - deps.folder_bytes(Path(j["build_root"]) / "profiles" /
                                                                                j["profile"])) / 1e9
                    for j, _, _ in running)
                view = {"now": deps.now(), "deadline": args.deadline, "stop": (out / STOP_FILE).is_file(),
                        "abort": state["aborted"] or (out / ABORT_FILE).is_file(),
                        "ai_stop": state["ai_stop"] or (out / ATTENTION_FILE).is_file(), "out_over": state["out_over"],
                        "dependency": dependency, "own_running": len(running),
                        "singles_others": singles_of(commands or []), "regression": regression_running(commands or []),
                        "reserve_gb": reserve,
                        "waited": waited.get(job["chain"], 0.0), "max_wait": max_wait}
                verdict, why = start_check(job, view)
                if verdict == SKIP:
                    skipped += 1
                    index += 1
                    continue
                if verdict == DROP:
                    pending.pop(index)
                    not_started.append((job["chain"], why))
                    event(out, deps, f"{job['chain']}: DROPPED ({why})")
                    continue
                if verdict == WAIT:
                    waited[job["chain"]] = waited.get(job["chain"], 0.0) + delta
                    break
                if dependency is not None:
                    start = dependency[1]
                    if start.get("persona") and start["persona"] != job["persona"]:
                        pending.pop(index)
                        not_started.append((job["chain"], f"its start {start['id']} is a {start['persona']}'s"))
                        continue
                    job["start"] = start
                    if start.get("kind") == "stage":
                        job["starter"], job["starter_from"] = start.get("starter"), start.get("starter_from")
                pending.pop(index)
                manifest = stage_info[job["stage"]][1]
                job.update({"tree": {"arm": job["stage"], "commit": manifest.get("commit"),
                                     "play_digest": manifest.get("play_digest"), "digest": manifest.get("digest"),
                                     "mutant": manifest.get("mutant")},
                            "batch_info": {"name": facts["batch"], "mode": facts["mode"], "ledger": facts["entry_id"],
                                           "started": facts["started"]},
                            "deadline": args.deadline, "watchdog_seconds": job_watchdog_seconds(job)})
                job_path = out / "jobs" / f"{job['chain']}.job.json"
                write_json(job_path, job)
                handle = deps.spawn(job, job_path, out / "logs" / f"{job['chain']}.child.log")
                running.append((job, handle, deps.clock()))
                most = max(most, len(running))
                launched += 1
                event(out, deps, f"{job['chain']}: started ({len(running)} running)")
                if pending:
                    deps.sleep(stagger)
            tick(running, out, stages, manifests, sandbox_marks, state, deps)
            for item in list(running):
                job, handle, _ = item
                if handle.poll() is None:
                    continue
                running.remove(item)
                if not any(r.get("record") == "job" and r.get("job") == job["chain"] for r in read_records(out)):
                    why = "killed by its watchdog" if (out / job["chain"] / "WATCHDOG.txt").is_file() else \
                        "it ended without its job record"
                    salvage_job(job, out, why)
                    event(out, deps, f"{job['chain']}: salvaged ({why})")
            if pending and idle_at_start and not launched and not running and skipped == len(pending):
                # nothing ran in this whole pass and every pending job waits on a dependency: none can ever resolve
                for job in pending:
                    not_started.append((job["chain"], "its dependency can never resolve (nothing runs)"))
                    event(out, deps, f"{job['chain']}: DROPPED (its dependency can never resolve)")
                pending = []
            if pending or running:
                deps.sleep(deps.poll_seconds)
    except BaseException:
        # (as live_chain's chains-run guard) an exception or a Ctrl+C while the jobs run kills every running child
        for _job, handle, _ in running:
            with contextlib.suppress(Exception):
                handle.kill_tree()
        raise
    for job in jobs:
        build = stage_info[job["stage"]][0] / "build"
        LC.end_sweep([{**job, "build_root": str(build)}], build)
    return {"most_running": most, "not_started": not_started, "aborted": state["aborted"], "ai_stop": state["ai_stop"],
            "events": list(deps.events)}


def tick(running: list, out: Path, stages: dict[str, Path], manifests: dict[str, dict], sandbox_marks: dict,
         state: dict, deps: Deps) -> None:
    """One tick (3.12, 3.13), in order: the stage watch (each stage's digest every 60 s, the junctioned sandbox's modules/
    and plugins/ every 10 min: a change writes STOP.txt); free under ABORT_FREE_GB: ABORT (ABORT.txt, every running launch
    killed); each running job's newest world.jsonl over its cut: killed (CUT-WORLD); --out over its cap: the pending jobs
    DROPPED; a job's profile folder over its budget: killed; a child past its watchdog: killed (then salvaged); the AI-only
    stop. Every disk comparison is `disk_decision`'s (one measurement per call)."""
    now = deps.clock()
    if now - state["last_stage"] >= deps.stage_every:
        state["last_stage"] = now
        for name, stage in stages.items():
            if deps.stage_digest(stage) != manifests[name].get("digest") and not (out / STOP_FILE).is_file():
                (out / STOP_FILE).write_text(f"the stage {name} changed ({stage})\n", encoding="utf-8")
                event(out, deps, f"STOP: the stage {name}'s code changed")
    if now - state["last_sandbox"] >= deps.sandbox_every:
        state["last_sandbox"] = now
        for name, manifest in manifests.items():
            sandbox = Path(manifest.get("sandbox") or stages[name])
            if deps.sandbox_digest(sandbox) != sandbox_marks.get(name) and not (out / STOP_FILE).is_file():
                (out / STOP_FILE).write_text(f"the sandbox {sandbox} changed (modules/ or plugins/)\n", encoding="utf-8")
                event(out, deps, f"STOP: the junctioned sandbox {sandbox} changed")
    free = deps.free(out)
    if disk_decision(None, free, None) == "abort" and not state["aborted"]:
        state["aborted"] = True
        (out / ABORT_FILE).write_text(f"under {ABORT_FREE_GB:g} GB free: {free}\n", encoding="utf-8")
        event(out, deps, f"ABORT: {free} GB free, under {ABORT_FREE_GB:g}: every running launch is killed")
        for job, handle, _ in running:
            if handle.poll() is None:
                current = read_json(out / job["chain"] / "current_leg.json")
                if isinstance(current, dict) and current.get("leg"):
                    write_marker(out, job["chain"], current["leg"], "abort", f"the disk guard's ABORT at {free} GB free")
                deps.kill(handle.pid)
    alive = [(job, handle, started) for job, handle, started in running if handle.poll() is None]
    legs_now = {}
    for job, handle, _ in alive:
        mc = bool(job.get("mc"))
        profile = Path(job["build_root"]) / "profiles" / job["profile"]
        name, size = deps.newest_world(profile / "ai_player_runs")
        leg = legs_now[job["chain"]] = LC.leg_of_folder(name, job["chain"])
        if leg is not None and disk_decision(size, None, None, mc=mc) == "cut-world":
            if write_marker(out, job["chain"], leg, "world", f"world.jsonl {size} bytes over {world_cut(mc)}"):
                deps.kill(handle.pid)
                event(out, deps, f"{job['chain']} {leg}: CUT-WORLD (world.jsonl {size} bytes over {world_cut(mc)})")
    if not state["out_over"] and disk_decision(None, None, deps.folder_bytes(out)) == "drop":
        state["out_over"] = True
        event(out, deps, f"--out over its cap of {OUT_CAP_BYTES} bytes: the pending jobs are DROPPED")
    for job, handle, started in alive:
        mc = bool(job.get("mc"))
        leg = legs_now.get(job["chain"])
        held = deps.folder_bytes(Path(job["build_root"]) / "profiles" / job["profile"])
        if leg is not None and disk_decision(None, None, None, held, mc=mc) == "cut-profile":
            if write_marker(out, job["chain"], leg, "profile", f"profile folder {held} bytes over {profile_budget(mc)}"):
                deps.kill(handle.pid)
                event(out, deps, f"{job['chain']} {leg}: CUT-WORLD (profile folder {held} bytes over {profile_budget(mc)})")
        if now - started > float(job.get("watchdog_seconds") or job_watchdog_seconds(job)) \
                and not (out / job["chain"] / "WATCHDOG.txt").exists():
            handle.kill_tree()
            (out / job["chain"]).mkdir(parents=True, exist_ok=True)
            (out / job["chain"] / "WATCHDOG.txt").write_text("past its watchdog\n", encoding="utf-8")
            event(out, deps, f"{job['chain']}: its watchdog killed its process tree")
    if not state["ai_stop"]:
        records = read_records(out)
        streak = ai_stop_streak(records)
        if streak >= STOP_STREAK:
            state["ai_stop"] = True
            legs = sorted((r for r in records if r.get("record") == "leg"), key=lambda r: (r.get("ended") or 0))[-streak:]
            (out / ATTENTION_FILE).write_text(
                f"THE AI-ONLY STOP: {streak} legs in a row of REFUSED, NOT CLEAN or HUNG; no new launch.\n"
                + "".join(f"  {r.get('run_id')}: {r.get('class')} ({r.get('class_why')})\n" for r in legs),
                encoding="utf-8")
            event(out, deps, f"the AI-only stop: {streak} legs in a row ({ATTENTION_FILE})")


# ====================================================================== the report (3.8, D7)
class SchemaRefused(Exception):
    """A records.jsonl holding a record of a schema this reader does not know (`report` exits 2)."""


START_KINDS = ("new game", "chain leg with a goal snapshot", "chain leg without", "practice with a snapshot",
               "practice world-only")


def start_kind(record: dict) -> str:
    job = record.get("job") or {}
    carried = (record.get("start_memory") or {}).get("goal_memory") == "carried"
    if job.get("origin") == "new_game":
        if (record.get("leg") or {}).get("index") == 0:
            return "new game"
        return START_KINDS[1] if carried else START_KINDS[2]
    return START_KINDS[3] if carried else START_KINDS[4]


def leg_frames_played(record: dict) -> int | None:
    real = (record.get("verdict") or {}).get("real_frames")
    if isinstance(real, int):
        return real
    frames = (record.get("measures") or {}).get("frames") or {}
    if isinstance(frames.get("start"), int) and isinstance(frames.get("end"), int):
        return frames["end"] - frames["start"]
    return None


def names_milestone(blocker: dict, milestone: str) -> bool:
    """Does a ranked blocker name `milestone`: its key's next unmet, or (a LOOP key) any of its records' own next unmet."""
    return blocker["key"][1] == milestone or milestone in (blocker.get("next_unmet_of_records") or {})


def build_report(out: Path) -> dict:
    """THE BLOCKER REPORT from `<out>/records.jsonl` alone (offline). Ranked per (tree.play_digest, chapter) on the exact
    key: share = count / judged legs (REFUSED, NOT CLEAN and INFRA excluded, their counts shown beside); ties by the key's
    text. Raises `SchemaRefused` on a record of an unknown schema_version."""
    records = read_records(out)
    unknown = [r for r in records if r.get("record") in ("leg", "job") and r.get("schema_version") != SCHEMA_VERSION]
    if unknown:
        raise SchemaRefused(f"{len(unknown)} record(s) of schema_version {sorted({str(r.get('schema_version')) for r in unknown})}"
                            f": this reader knows {SCHEMA_VERSION}")
    legs = [r for r in records if r.get("record") == "leg"]
    classes: dict[str, int] = {}
    for record in legs:
        classes[record.get("class")] = classes.get(record.get("class"), 0) + 1
    groups: dict[tuple[str, int], list[dict]] = {}
    for record in legs:
        digest = str((record.get("tree") or {}).get("play_digest"))
        groups.setdefault((digest, (record.get("leg") or {}).get("chapter")), []).append(record)
    trees: dict[str, dict] = {}
    flat: list[dict] = []
    for (digest, chapter), group in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        judged = [r for r in group if r.get("class") not in EXCLUDED_CLASSES]
        excluded: dict[str, int] = {}
        for record in group:
            if record.get("class") in EXCLUDED_CLASSES:
                excluded[record["class"]] = excluded.get(record["class"], 0) + 1
        keyed: dict[str, list[dict]] = {}
        for record in judged:
            blocker = record.get("blocker")
            if blocker and not record.get("reached"):
                keyed.setdefault(blocker["key_id"], []).append(record)
        ranked = []
        for kid, members in keyed.items():
            key = members[0]["blocker"]["key"]
            frames = sorted(f for f in (leg_frames_played(r) for r in members) if isinstance(f, int))
            pairs: dict[str, int] = {}
            names: dict[str, int] = {}
            for record in members:
                job = record.get("job") or {}
                label = f"{job.get('persona')}/{job.get('starter')}"
                pairs[label] = pairs.get(label, 0) + 1
                raw = (record.get("blocker") or {}).get("raw") or []
                if len(raw) > 1:
                    names[str(raw[1])] = names.get(str(raw[1]), 0) + 1
            newest = sorted(members, key=lambda r: r.get("ended") or 0, reverse=True)[:3]
            entry = {"tree": digest, "chapter": chapter, "key": key, "key_id": kid, "count": len(members),
                     "share": round(len(members) / len(judged), 4) if judged else None,
                     "real_frames": {"min": frames[0], "median": statistics.median(frames), "max": frames[-1]}
                     if frames else None,
                     "pairs": pairs, "next_unmet_of_records": names,
                     "examples": [{"run_id": r.get("run_id"), "folder": (r.get("kept") or {}).get("folder"),
                                   "zip": (r.get("kept") or {}).get("zip")} for r in newest]}
            if isinstance(chapter, int) and chapter >= 6:
                entry["bossprep"] = {
                    "plan_made": sum(1 for r in members if isinstance((r.get("bossprep") or {}).get("plan"), dict)),
                    "raise_ended_by_budget": sum(1 for r in members if (r.get("bossprep") or {}).get("raise_end")
                                                 == "budget spent"),
                    "trainee_reached_target": sum(1 for r in members if (r.get("bossprep") or {}).get("raise_end")
                                                  == "target reached"),
                    "trainer_only_logged": sum(1 for r in members if (r.get("bossprep") or {}).get("acting")
                                               == "logs only"),
                    "losses_carried_in": sum(int((r.get("start_memory") or {}).get("losses_carried") or 0)
                                             for r in members),
                    "losses_in_leg": sum(int((r.get("bossprep") or {}).get("boss_losses") or 0)
                                         + int((r.get("bossprep") or {}).get("other_losses") or 0) for r in members)}
            ranked.append(entry)
        ranked.sort(key=lambda e: (-e["count"], json.dumps(e["key"])))
        by_kind: dict[str, list[int]] = {kind: [0, 0] for kind in START_KINDS}
        for record in judged:
            cell = by_kind[start_kind(record)]
            cell[1] += 1
            cell[0] += 1 if record.get("reached") else 0
        real = sum(r["verdict"]["real_frames"] for r in group
                   if isinstance((r.get("verdict") or {}).get("real_frames"), int) and (r.get("launch") or {}).get("elapsed"))
        elapsed = sum(float((r.get("launch") or {}).get("elapsed") or 0) for r in group
                      if isinstance((r.get("verdict") or {}).get("real_frames"), int))
        counts: dict[str, int] = {}
        for record in group:
            counts[record.get("class")] = counts.get(record.get("class"), 0) + 1
        chapter_report = {
            "legs": len(group), "judged": len(judged), "excluded": excluded,
            "reached": sum(1 for r in judged if r.get("reached")),
            "reach": round(sum(1 for r in judged if r.get("reached")) / len(judged), 4) if judged else None,
            "frames_per_second": round(real / elapsed, 1) if elapsed else None, "classes": counts,
            "reach_by_start_kind": {kind: {"reached": cell[0], "judged": cell[1]} for kind, cell in by_kind.items()
                                    if cell[1]},
            "blockers": ranked,
            "loops_seen": [{"run_id": r.get("run_id"), "key": (r.get("blocker") or {}).get("key"),
                            "pair": ((r.get("measures") or {}).get("loop") or {}).get("pair"),
                            "crossings": ((r.get("measures") or {}).get("loop") or {}).get("crossings"),
                            "crossings_raise": ((r.get("measures") or {}).get("loop") or {}).get("crossings_raise")}
                           for r in group if ((r.get("measures") or {}).get("loop") or {}).get("keyed") == "flag"],
            "churn": [{"run_id": r.get("run_id"), "pair": r["measures"]["loop"].get("pair"),
                       "crossings": r["measures"]["loop"].get("crossings"),
                       "window_frames": (r["measures"]["loop"]["window"][1] - r["measures"]["loop"]["window"][0])
                       if r["measures"]["loop"].get("window") else None}
                      for r in group if ((r.get("measures") or {}).get("loop") or {}).get("churn")]}
        trees.setdefault(digest, {})[str(chapter)] = chapter_report
        flat += ranked
    experience = read_records_named(out, EXPERIENCE)
    batch = read_json(Path(out) / BATCH_FILE)
    return {"header": HEADER, "legs": len(legs), "reached": sum(1 for r in legs if r.get("reached")), "classes": classes,
            "trees": trees, "blockers": flat, "experience_rows": len(experience),
            "experience_unclassified": sorted({u for row in experience for u in row.get("unclassified") or []}),
            "mc": mc_reading(records, batch.get("mc_planned") if isinstance(batch, dict) else None)}


def mc_reading(records: list[dict], plan: dict | None = None) -> dict | None:
    """THE MERGE CHECK'S READING (2.4b; a hard-break check, NEVER a rate): PASS when every MC job ran every planned leg,
    each CLEAN-*, fresh, continuing by `continue_after` (purity, custody, the world), and its last leg reached its target.
    Any HUNG, NOT CLEAN, REFUSED, freshness INFRA, CUT-WORLD, a leg not run or a miss is a STOP. None: no MC job.
    `plan` (batch.json's `mc_planned`, {chain: [legs]}): every PLANNED MC chain counts, so a job DROPPED before its launch
    (the --out cap, STOP.txt, --max-wait, the deadline; it writes no leg and no job record) is a STOP, never a PASS over
    the chains that happened to start (fix round 6, V6-1)."""
    legs = [r for r in records if r.get("record") == "leg" and (r.get("job") or {}).get("mc")]
    jobs = {r.get("job"): r for r in records if r.get("record") == "job" and r.get("mc")}
    planned_jobs = {str(k): list(v or []) for k, v in plan.items()} if isinstance(plan, dict) else {}
    if not legs and not jobs and not planned_jobs:
        return None
    by_job: dict[str, list[dict]] = {}
    for record in legs:
        by_job.setdefault(record["job"]["id"], []).append(record)
    problems: list[str] = []
    ids = sorted(set(by_job) | set(jobs) | set(planned_jobs))
    for job_id in ids:
        members = by_job.get(job_id) or []
        if not members and job_id not in jobs:
            problems.append(f"{job_id}: DROPPED, not run (no leg and no job record)")
            continue
        planned = (members[0]["job"].get("legs_planned") if members else None) or (jobs.get(job_id) or {}).get(
            "legs_planned") or planned_jobs.get(job_id) or []
        have = {r["leg"]["leg"]: r for r in members}
        for leg in planned:
            record = have.get(leg)
            if record is None:
                problems.append(f"{job_id} {leg}: not run")
            elif record.get("class") not in CLEAN_CLASSES:
                problems.append(f"{job_id} {leg}: {record.get('class')}")
            elif not (record.get("fresh") or {}).get("ok"):
                problems.append(f"{job_id} {leg}: not fresh (L5.THIS_RUN)")
            elif not (record.get("continue") or {}).get("go"):
                problems.append(f"{job_id} {leg}: {(record.get('continue') or {}).get('why')}")
        last = have.get(planned[-1]) if planned else None
        if last is None or not last.get("reached"):
            problems.append(f"{job_id}: did not reach its target")
    return {"reading": "PASS" if not problems else "STOP", "chains": len(ids),
            "problems": sorted(set(problems))}


def read_records_named(out: Path, name: str) -> list[dict]:
    path = Path(out) / name
    found = []
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                data = parse_object(line)
                if data is not None:
                    found.append(data)
    except OSError:
        return []
    return found


def experience_union(out: Path) -> dict:
    """The deterministic UNION of the batch's static facts (3.9): legs in run_id order, the first seen wins, conflicts
    listed; at most MAX_MAPS maps."""
    folders = {r.get("run_id"): (r.get("kept") or {}).get("folder") for r in read_records(out) if r.get("record") == "leg"}
    union: dict = {"maps": {}, "warps": {}, "connections": [], "landmarks": {}, "rides": {}}
    conflicts: list[str] = []
    seen_connections: set[str] = set()
    for row in sorted(read_records_named(out, EXPERIENCE), key=lambda r: str(r.get("run_id"))):
        folder = folders.get(row.get("run_id"))
        static = read_json(Path(folder) / "static.json") if folder else None
        if not isinstance(static, dict):
            continue
        for section in ("maps", "warps", "landmarks", "rides"):
            for key, value in (static.get(section) or {}).items():
                if section == "maps" and key not in union["maps"] and len(union["maps"]) >= MAX_MAPS:
                    conflicts.append(f"maps.{key}: over {MAX_MAPS} maps, dropped")
                    continue
                if key not in union[section]:
                    union[section][key] = value
                elif union[section][key] != value:
                    conflicts.append(f"{section}.{key} ({row.get('run_id')})")
        for item in static.get("connections") or []:
            text = json.dumps(item, sort_keys=True)
            if text not in seen_connections:
                seen_connections.add(text)
                union["connections"].append(item)
    return {"schema_version": SCHEMA_VERSION, "header": HEADER, "static": union, "conflicts": conflicts}


def report_markdown(report: dict) -> str:
    lines = [f"# {report['header']}", "", f"{report['legs']} legs, {report['reached']} reached; classes "
                                          f"{report['classes']}", ""]
    if report.get("mc"):
        mc = report["mc"]
        lines += [f"MERGE CHECK (MC, a hard-break check, never a rate): {mc['reading']} over {mc['chains']} chains; "
                  f"problems {mc['problems'] or 'none'}", ""]
    for digest, chapters in report["trees"].items():
        lines.append(f"## tree (play digest) {digest[:16]}")
        for chapter, cell in sorted(chapters.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0):
            lines.append(f"### chapter {chapter}: reach {cell['reached']} of {cell['judged']} judged ({cell['reach']}); "
                         f"excluded {cell['excluded']}; frames/s {cell['frames_per_second']}; classes {cell['classes']}")
            lines.append(f"reach by start kind: {cell['reach_by_start_kind']}")
            lines.append("| # | key | count | share | real frames | pairs |")
            lines.append("|---|---|---|---|---|---|")
            for rank, blocker in enumerate(cell["blockers"], 1):
                lines.append(f"| {rank} | {blocker['key']} | {blocker['count']} | {blocker['share']} | "
                             f"{blocker['real_frames']} | {blocker['pairs']} |")
            if cell["loops_seen"]:
                lines.append(f"loops seen (own keys, flagged): {cell['loops_seen']}")
            if cell["churn"]:
                lines.append(f"churn (reached, never ranked): {cell['churn']}")
            lines.append("")
    if report["experience_unclassified"]:
        lines.append(f"EXPERIENCE UNCLASSIFIED (dropped and listed): {report['experience_unclassified']}")
    return "\n".join(lines) + "\n"


def write_report(out: Path) -> dict:
    report = build_report(out)
    write_json(Path(out) / "blockers.json", report)
    (Path(out) / "blockers.md").write_text(report_markdown(report), encoding="utf-8")
    write_json(Path(out) / EXPERIENCE_MAPS, experience_union(out))
    return report


# ====================================================================== compare and replay (AM-11, from E0's kit)
def load_moves(path: Path) -> list[dict]:
    """What the AI DID: records with a frame, whose decision is not 'say' or 'world' and whose action is not 'say'."""
    moves = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            record = parse_object(line)
            if record is None or record.get("frame") is None or record.get("decision") in ("say", "world") \
                    or record.get("action") == "say":
                continue
            moves.append(record)
    return moves


def compare_moves(a: list[dict], b: list[dict], context: int = 3) -> tuple[int | None, str]:
    """(the index of the first differing (frame, action), the text); None when identical over the shorter."""
    def show(record: dict) -> str:
        return (f"{record.get('frame')} [{str(record.get('decision'))[:60]}] {record.get('action')} | "
                f"{str(record.get('reason'))[:160]}")
    n = min(len(a), len(b))
    for i in range(n):
        if (a[i].get("frame"), a[i].get("action")) != (b[i].get("frame"), b[i].get("action")):
            lines = [f"moves A {len(a)} B {len(b)}; FIRST DIFFERENT MOVE at index {i}"]
            lines += [f"  A[{j}] {show(a[j])}" for j in range(max(0, i - context), min(n, i + context + 1))]
            lines += [f"  B[{j}] {show(b[j])}" for j in range(max(0, i - context), min(n, i + context + 1))]
            return i, "\n".join(lines)
    return None, (f"moves A {len(a)} B {len(b)}; IDENTICAL (frame, action) over the first {n} (a determinism check, never "
                  f"a replication)")


def replay_arm(example: Path, record: dict, profile: str, seed: int | None, frames: int | None, L5) -> tuple[object, dict]:
    """The arm and the carried start of ONE new leg from a kept example (its end state, world line and goal snapshot when
    kept), as `run_chain` hands a leg over: one new trajectory."""
    example = Path(example)
    missing = [name for name in ("end_state.ss1", "world_last.jsonl") if not (example / name).is_file()]
    if missing:
        raise Refusal(f"the example {example} lacks {missing}")
    job, leg = record.get("job") or {}, record.get("leg") or {}
    env = L5.play_env(job.get("persona"), None, leg.get("target"))
    # an MC example is replayed as MC plays it, E0's harness: its kept snapshot is never sent (2.4b; verifier round 3, N7)
    if (example / "goals_last.jsonl").is_file() and not job.get("mc"):
        env[ENV_GOALS] = str(example / "goals_last.jsonl")
    arm = L5.Arm(f"replay-{record.get('run_id')}", f"A1 replay of {record.get('run_id')} (one new trajectory)",
                 int(frames or leg.get("frames")), float(leg.get("wall") or LEG_WALL.get(leg.get("chapter"), LC.WALL)), env,
                 seed=int(seed if seed is not None else job.get("seed")), fresh=False, state_from="EXAMPLE")
    return arm, {"EXAMPLE": (example / "end_state.ss1", example / "world_last.jsonl", read_reads(example / "reads.jsonl"))}


def replay(example: Path, stage: Path, profile: str, seed: int | None = None, frames: int | None = None,
           code_tree: Path | None = None, run_leg: Callable | None = None) -> int:
    """`replay`: ONE leg again from a kept example, through the real launcher on the stage's build root, in a NEW profile
    (refused when it exists); `--code-tree` selects the AI code (the launch's cwd, as E0's `replay_leg.py`; default the
    stage's own code root, the code the batch ran). The environment is sanitized before any launcher import."""
    sanitize_environ()
    from ai_player.gates import live_step5 as L5

    example = Path(example).resolve()
    out = example.parents[1]
    record = next((r for r in read_records(out) if r.get("record") == "leg"
                   and Path(str((r.get("kept") or {}).get("folder") or "")).resolve() == example), None)
    if record is None:
        raise Refusal(f"no leg record in {out / RECORDS} keeps {example}")
    if not profile.startswith(PROFILE_PREFIX) or profile == DONOR:
        raise Refusal(f"the replay's profile {profile!r} must be a NEW probe profile ({PROFILE_PREFIX}*)")
    build = Path(stage) / "build"
    if (build / "profiles" / profile).exists():
        raise Refusal(f"the profile {profile} exists: a replay plays in a NEW profile")
    arm, carried = replay_arm(example, record, profile, seed, frames, L5)
    from ai_player.host import launcher

    launcher.ensure_profile(build, profile, template=DONOR)
    L5.PROFILE = profile
    L5.REPO = Path(code_tree).resolve() if code_tree is not None else (Path(stage) / "code").resolve()
    run = (run_leg or L5.run_arm)(arm, build, carried)
    print(f"[A1 replay] {record.get('run_id')}: exit {run.exit_code}, {round(run.elapsed or 0, 1)} s, run folder "
          f"{run.run_dir}: one new trajectory, never a replication", flush=True)
    return 0


# ====================================================================== the command line
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="frontier_probe.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage")
    stage.add_argument("--commit", required=True)
    stage.add_argument("--stage", required=True)
    stage.add_argument("--repo", default=str(REPO))
    stage.add_argument("--sandbox", default=None)
    stage.add_argument("--donor", default=None)
    stage.add_argument("--mutant", default=None)
    stage.add_argument("--starts", default="")
    stage.add_argument("--g-root", default=str(GRADED_CH5))
    stage.add_argument("--c-root", default=str(KEPT_C))
    plan = sub.add_parser("plan")
    plan.add_argument("batch", choices=("P1", "GM", "WP1", "MC"))
    plan.add_argument("--first-seed", type=int, required=True)
    plan.add_argument("--to", default=None)
    run = sub.add_parser("run")
    run.add_argument("--jobs", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--stage", required=True)
    group = run.add_mutually_exclusive_group(required=True)
    group.add_argument("--ledger", choices=("development",))
    group.add_argument("--trainer", action="store_true")
    run.add_argument("--prediction-file", default=None)
    run.add_argument("--parallel", type=int, default=P_DEFAULT)
    run.add_argument("--deadline", type=float, default=None)
    run.add_argument("--max-wait", type=float, default=MAX_WAIT_SECONDS)
    run.add_argument("--resume", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("out")
    replay_cmd = sub.add_parser("replay")
    replay_cmd.add_argument("example")
    replay_cmd.add_argument("--stage", required=True)
    replay_cmd.add_argument("--profile", required=True)
    replay_cmd.add_argument("--seed", type=int, default=None)
    replay_cmd.add_argument("--frames", type=int, default=None)
    replay_cmd.add_argument("--code-tree", default=None)
    compare = sub.add_parser("compare")
    compare.add_argument("a")
    compare.add_argument("b")
    compare.add_argument("--context", type=int, default=3)
    band = sub.add_parser("reserve-band")
    band.add_argument("--ledger", default=None)
    down = sub.add_parser("teardown")
    down.add_argument("--stage", required=True)
    child_cmd = sub.add_parser("child")
    child_cmd.add_argument("job")
    return parser


def command(args) -> int:
    if args.command == "child":
        return child(Path(args.job))
    if args.command == "plan":
        try:
            jobs = plan_jobs(args.batch, args.first_seed, LC.load_milestones(REPO), args.to)
        except Refusal as error:
            print(f"REFUSED: {error}", file=sys.stderr, flush=True)
            return 2
        print(json.dumps(jobs, indent=1))
        return 0
    if args.command == "run":
        return run_batch(args)
    if args.command == "report":
        try:
            report = write_report(Path(args.out))
        except SchemaRefused as error:
            print(f"REFUSED: {error}", flush=True)
            return 2
        print(report_markdown(report))
        return 0
    if args.command == "compare":
        _, text = compare_moves(load_moves(Path(args.a)), load_moves(Path(args.b)), args.context)
        print(text)
        return 0
    if args.command == "reserve-band":
        try:
            entry = reserve_band(Path(args.ledger) if args.ledger else None)
        except (Refusal, ledger.Refused) as error:
            print(f"REFUSED: {error}", flush=True)
            return 2
        print(f"RESERVED: ledger entry #{entry['id']} {TRAINER_BAND[0]}-{TRAINER_BAND[1]} ({BAND_NOTE}); the ledger's own "
              f"check passes; commit ledger.json by its explicit path", flush=True)
        return 0
    if args.command == "teardown":
        try:
            result = teardown(Path(args.stage))
        except Refusal as error:
            print(f"REFUSED: {error}", flush=True)
            return 2
        print(f"TEARDOWN: {len(result['unlinked'])} junction(s) unlinked first, then the stage deleted; the sandbox's "
              f"counts before {result['before']} after {result['after']}: "
              f"{'unchanged' if result['unchanged'] else 'CHANGED'}", flush=True)
        return 0 if result["unchanged"] else 1
    if args.command == "replay":
        try:
            return replay(Path(args.example), Path(args.stage), args.profile, args.seed, args.frames,
                          Path(args.code_tree) if args.code_tree else None)
        except Refusal as error:
            print(f"REFUSED: {error}", flush=True)
            return 2
    if args.command == "stage":
        sandbox = Path(args.sandbox) if args.sandbox else Path(args.repo) / "sandbox-pokebot"
        donor = Path(args.donor) if args.donor else sandbox / "profiles" / "endless-P1-torchic"
        starts = [s for s in args.starts.split(",") if s]
        try:
            manifest = build_stage(Path(args.stage), args.commit, Path(args.repo), sandbox, donor, args.mutant, starts,
                                   Path(args.g_root), Path(args.c_root))
        except Refusal as error:
            print(f"REFUSED: {error}", flush=True)
            return 2
        print(f"STAGE {args.stage}: commit {manifest['commit']}, play digest {manifest['play_digest'][:16]}, digest "
              f"{manifest['digest'][:16]}, mutant {manifest['mutant']}, starts {sorted(manifest['starts'])}", flush=True)
        return 0
    return 2


CRASH_EXIT = 5


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return command(args)
    except Exception:  # noqa: BLE001 - an unguarded crash: exit 5
        traceback.print_exc()
        return CRASH_EXIT


if __name__ == "__main__":
    sys.exit(main())
