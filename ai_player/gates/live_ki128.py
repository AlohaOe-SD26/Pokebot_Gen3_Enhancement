"""THE GRADED HELD-OUT of KI-128 + KI-129 (build spec `PROJECT KNOWLEDGE/ai-research-notes/2026-10-31-KI128-KI129-BUILD-SPEC.md`
section 5, with the disk rule of its section 6). TEST SIDE: the AI never imports this module.

    py -3.12 ai_player/gates/live_ki128.py bounds [--starts-from DIR]
        print the BOUNDS TEXT, the registered numbers and their sha256 (read only)
    py -3.12 ai_player/gates/live_ki128.py register [--starts-from DIR] [--note-file F]
        pre-register seeds 5972-5977 as GRADED in `gates/ledger.json` with that sha256 (BEFORE any run; commit and push it)
    py -3.12 ai_player/gates/live_ki128.py run --out DIR [--build-root DIR] [--starts-from DIR]
        the graded batch: 6 launcher runs, at most 3 at once; one evidence file; the ledger entry finished with the verdict
        exit 0 = PASS, 1 = FAIL, 2 = refused before any run
    py -3.12 ai_player/gates/live_ki128.py run --out DIR --purpose development --first-seed N [--frames F]
        a rehearsal on development seeds N..N+5 (never graded; the evidence and the ledger say so)
    py -3.12 ai_player/gates/live_ki128.py grade DIR          offline: re-grade a batch's rows (no ledger write)
    py -3.12 ai_player/gates/live_ki128.py read RUN_DIR [--start-frame N]
        offline, READ ONLY: one run folder's measures (its ai_player.log and world.jsonl streamed; nothing deleted)
    `child JOB.json` is the internal entry of one run's process.

WHAT IT GRADES (registered: `BOUNDS_TEXT` below is hashed into the ledger registration, with every constant, the sha256 of
the start files, of the AI's code and of the files that grade it, so `ledger.begin` refuses a graded run on any other
numbers, start, AI code or grader). The AI code under test is frozen at the commit the registration names (rounds 1 and 2:
KI-128, KI-129 Part A, KI-129 Part B). The starts are A0's ORIGINAL starts: the r1base CH2, CH2T and CH2M ends (2026-10-30,
`sandbox-pokebot/profiles/ai-step5-play/ai_player_runs/20261030-{135558-CH2,135912-CH2T,140134-CH2M}`) with their world
memories, each with its chain's personality (Catcher, Story, Trainer), times 2 seeds; target ch3_rustboro; 600,000 frames
and 3,600 s each; at most 3 in parallel, each in its own NEW disposable profile (`ai-ki128-ho-<seed>`).

HOW EACH BOUND IS READ (the bounds text says it exactly; here, why):
  * purity and freshness are `live_step2.check_purity` and `live_step5.check_after_is_this_run`, as every live driver;
  * the woods exit is read from the AI's log (`[AI-WORLD] MAP ... -> ROUTE104 at (x, y): the warp at (u, v)`), checked
    against the AI's world memory (its transitions, a second record written by other code) and CONFIRMED by the game where
    the game can say anything: VISITED_RUSTBORO_CITY at the end (the game keeps no record of a past warp);
  * "no same-edge alternation over 5 within any intent" (V2-1's wording, before registration): an alternation is a run
    of crossings of ONE edge, in one intent, with NOTHING NEW seen between neighbours, and "nothing new" is read from four
    records the bounds text names (the AI's told novelty lines, its milestone lines, the world memory's tiles_learned and
    its count of visited maps at each crossing). Crossings with news between them are no ping-pong (B-C1), so one intent
    may cross one edge more than 5 times in all (B-F1 seed 3: 7, with news after the 2nd);
  * that per-intent bound holds BY CONSTRUCTION for any code with Part B's stop (it stops at 5, and a new intent restarts
    the count), so K8.EDGE_WINDOW (verifier F1, added before registration) reads the ping-pong carried ACROSS intents:
    at most 10 crossings of one edge within any 3,000 frames, intents ignored (round 2's own D2w criterion). On round 2's
    logs it fails the none arms and 4 of 5 Bstop fault runs, and passes every B run and every chapter 1-2 and long run;
    the longest no-news alternation with intents ignored is reported beside it (information);
  * every world.jsonl is measured BEFORE it is deleted (section 6: it is streamed, never read whole, its last line kept
    outside the repo, then deleted; actions.jsonl, ai_player.log, purity.json and end_state.ss1 are kept).
The three graded checks that read the AI's log are declared as such (`AI_INPUT_DEBT`, printed as B1 DEBT lines in the
evidence): spec section 5 registers them as reads of the AI's transition lines, and no game record of a past warp exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import ledger  # noqa: E402
from ai_player.gates.grader_checks import (  # noqa: E402
    AI, FAIL, GAME, GRADED, HARNESS, PASS, REPORTED, VACUOUS, Check, status_of, verdict as typed_verdict,
)

GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
FAMILY = "story"
DRIVER = "live_ki128"
#: the held-out's seeds (checked at build time: no ledger entry named any of 5972-5977; the spec's example 5961-5966
#: overlaps development seeds 5960-5965 and 5966-5971)
SEEDS = (5972, 5977)
TARGET = "ch3_rustboro"
FRAMES = 600000
WALL = 3600.0
PARALLEL = 3
STAGGER_SECONDS = 15
FREE_MIN_GB = 40.0
#: section 5: every world.jsonl UNDER 300 MB (decimal megabytes)
WORLD_MAX_BYTES = 300_000_000
#: the disk guard during the batch (a run past it has its launcher killed; it then fails the size bound anyway)
GUARD_WORLD_BYTES = 1_500_000_000
GUARD_FREE_GB = 30.0
WOODS_MIN = 5
RUSTBORO_MIN = 4
ALT_MAX = 5
#: K8.EDGE_WINDOW (added before registration by the held-out verifier's F1): the most crossings of ONE edge, intents
#: IGNORED, whose frames lie within EDGE_WINDOW_FRAMES of each other; bound <= EDGE_WINDOW_MAX. This is round 2's own D2w
#: criterion (2026-10-31-KI129B-BUILD-REPORT.md, vpartb Q2: "D2w <= 10"). WHY: the per-intent K8.ALTERNATION holds by
#: construction for any code with Part B's stop (Part B stops at 5 crossings, and a new intent restarts the count), so it
#: cannot see a ping-pong carried ACROSS intents: the Bstop fault arm crossed one edge 131 times in 31 intents and read 5.
#: GRADED pending the ruling the F1 fix asks for (V2-1's spec wording is per-intent); REPORTED is the one-word alternative.
EDGE_WINDOW_FRAMES = 3000
EDGE_WINDOW_MAX = 10
EDGE_WINDOW_KIND = REPORTED  # the orchestrator's ruling (06 2026-10-31): information; the graded bars are what the fix claims
PROFILE_PREFIX = "ai-ki128-ho-"
#: the woods' NORTH warps (decomp `data/maps/PetalburgWoods/map.json`: warps 0 and 1 at (14,5)/(15,5) to Route104 warps 2/3
#: at (10,30)/(11,30); the spec's K-C6 checked them on the pinned clone)
WOODS_NORTH_WARPS = ((14, 5), (15, 5))
NORTH_Y = 31
#: chain -> (the r1base run folder, the chain's personality)
STARTS = {"CH2": ("20261030-135558-CH2", "Catcher"), "CH2T": ("20261030-135912-CH2T", "Story"),
          "CH2M": ("20261030-140134-CH2M", "Trainer")}
START_FILES = ("end_state.ss1", "world.jsonl", "actions.jsonl")
#: (chain, offset from the first seed) in launch order: one run of each chain in the first three
JOB_ORDER = (("CH2", 0), ("CH2T", 2), ("CH2M", 4), ("CH2", 1), ("CH2T", 3), ("CH2M", 5))
#: the purity checks of `live_step2.check_purity` that COUNT (L5.PURITY_ENDED is REPORTED: a run may end on its budget)
PURITY_IDS = ("L5.PURITY_GATE", "L5.PURITY_CLEAN", "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_BREACHES",
              "L5.PURITY_PACKAGE")
#: the files whose code grades this batch (hashed into the registration)
GRADER_FILES = ("ai_player/gates/live_ki128.py", "ai_player/gates/live_step5.py", "ai_player/gates/live_step2.py",
                "ai_player/gates/grader_checks.py", "ai_player/gates/play_harness.py", "ai_player/gates/hands_harness.py",
                "ai_player/gates/probe_eyes.py", "ai_player/gates/rate_step5.py", "ai_player/gates/provenance.py")
#: the graded checks that read an AI input, declared (the B1 rule of `grader_checks`), each with why the spec grades it so
AI_INPUT_DEBT = {
    "K8.WOODS": {"ai_input": "log MAP lines (ai_player.log) and its world memory's transitions (world.jsonl)",
                 "plan": "spec section 5 registers the woods exit as read from the AI's transition lines, CONFIRMED by the "
                         "game where possible (VISITED_RUSTBORO_CITY); the game keeps no record of a past warp"},
    "K8.ALTERNATION": {"ai_input": "log MAP, intent, novelty and MILESTONE lines and its world memory's tiles_learned",
                       "plan": "spec section 5 (V2-1) registers the alternation bound as read from the AI's logs; an edge "
                               "crossing has no game record"},
    "K8.EDGE_WINDOW": {"ai_input": "log MAP lines (their edge crossings and frames)",
                       "plan": "round 2's D2w criterion, added before registration (verifier F1): the cross-intent "
                               "ping-pong the per-intent K8.ALTERNATION cannot see; an edge crossing has no game record"},
}

EDGE_WINDOW_TEXT = f"""K8.EDGE_WINDOW{' (information, never counted)' if EDGE_WINDOW_KIND == REPORTED else ''}: in every \
run, at most {EDGE_WINDOW_MAX} crossings of one edge within any {EDGE_WINDOW_FRAMES} frames, INTENTS IGNORED (round 2's \
D2w criterion, 2026-10-31-KI129B-BUILD-REPORT.md; added before registration because the per-intent K8.ALTERNATION cannot \
see a ping-pong carried across intents). Read from ai_player.log: every CROSSING line as K8.ALTERNATION defines it, its \
EDGE the unordered pair of maps and its frame N from '(<actor>, f<N>)'; per edge, the most crossings whose frames lie \
within {EDGE_WINDOW_FRAMES} of each other (the last minus the first <= {EDGE_WINDOW_FRAMES}). Bound: that number <= \
{EDGE_WINDOW_MAX} for every edge. A run with any crossing line without a frame is not read by this check (strict). Also \
reported per run (information): the longest no-news alternation with intents ignored (K8.ALTERNATION's rule over one \
pooled intent)."""

BOUNDS_TEXT = f"""KI-128 + KI-129 GRADED HELD-OUT, build spec 2026-10-31-KI128-KI129-BUILD-SPEC.md section 5 (disk rule: section 6). \
Driver ai_player/gates/live_ki128.py.
CODE: the AI's files (ai_player/ outside gates/ and evidence/, no *.md, no __pycache__) are hashed into these numbers \
(ai_code_sha256, line endings normalised: CRLF read as LF), as are the files that grade the batch (grader_files): a \
graded run on any other AI code or grader is refused by ledger.begin. The ledger entry also records the \
provenance digest at begin, and the frozen-tree watch must see no change during the batch.
SEEDS: the registered range (numbers 'seeds'), 6 runs. JOBS in launch order (chain, personality, seed offset): \
{', '.join(f'{c} {STARTS[c][1]} +{o}' for c, o in JOB_ORDER)}; at most {PARALLEL} at once, {STAGGER_SECONDS} s apart.
STARTS: A0's original starts, the r1base chapter-2 ends {', '.join(v[0] for v in STARTS.values())} (each folder's \
end_state.ss1 as --state, its whole world.jsonl as AI_PLAYER_WORLD, its actions.jsonl's 'read' records as the pages read \
before); each file's sha256 is in these numbers.
EACH RUN: the real launcher through live_step5.run_arm: brain play, target {TARGET}, {FRAMES} frames, {WALL:g} s wall \
clock, in its own NEW profile {PROFILE_PREFIX}<seed> under the build root (refused if it exists).
DISK: refused under {FREE_MIN_GB:g} GB free on the build root's drive before the batch. During it, a run whose \
world.jsonl passes {GUARD_WORLD_BYTES} bytes, or with under {GUARD_FREE_GB:g} GB free, has its launcher killed (recorded). \
After each run its world.jsonl's size is recorded, its measures are streamed from it line by line (never a whole-file \
read), its last line is saved outside the repo, and then it is DELETED.
GRADED (every one must PASS; each counts the runs it could read, floor 6; a VACUOUS check fails; no waivers):
K8.PURITY: on every launch the counting purity checks of live_step2.check_purity ({', '.join(PURITY_IDS)}) all PASS. \
L5.PURITY_ENDED is reported only.
K8.THIS_RUN: every run's L5.THIS_RUN (live_step5.check_after_is_this_run) PASSES.
K8.WOODS: at least {WOODS_MIN} of the 6 runs REACH ROUTE104 NORTH BY THE WOODS: (a) in the AI's log ai_player.log the \
FIRST line '[AI-WORLD] MAP <A> -> ROUTE104 at (x, y): ...' with y < {NORTH_Y} has A = PETALBURG_WOODS and reads 'the warp \
at (14, 5)' or 'the warp at (15, 5)'; AND (b) the world memory agrees: the first transition in world.jsonl made in this run \
(frame > the start state's frame) into ROUTE104 with an arrival y < {NORTH_Y} is a warp from PETALBURG_WOODS at (14, 5) or \
(15, 5). The GAME confirms where it can: VISITED_RUSTBORO_CITY set at the end (there is no land route from ROUTE104 south \
to RUSTBORO_CITY without the woods' north warps, Surf not being available). A run whose game shows VISITED_RUSTBORO_CITY \
but which does not count by (a) and (b) is an instrument disagreement and FAILS this check.
K8.ALTERNATION: no same-edge alternation over {ALT_MAX} within any intent, in every run. Read from ai_player.log in line \
order: an INTENT runs from one '[AI-WORLD] intent ' line to the next (lines before the first form an intent of their \
own). A CROSSING is a line '[AI-WORLD] MAP <A> -> <B> at (x, y): the <up|down|left|right> edge ... (<actor>, f<N>)'; its \
EDGE is the unordered pair of maps (A, B). Between two consecutive crossings c and d of one edge in one intent there is \
NEWS when any of: (N1) a line '[AI-WORLD] novelty at f<M>:' lies between them in the log (the AI's told novelty: a story \
flag, a new Pokemon, more items, experience, new words); (N2) a line 'MILESTONE <id> done' lies between them; (N3) the \
world memory's tiles_learned in the first world.jsonl line holding d's transition (its frame, both maps, how \
'connection') is greater than in the first line holding c's (a new tile seen); (N4) the number of maps with visits in \
those two lines rose (a new map). A crossing with no world line gets no N3/N4 news (strict) and is counted as unmatched in \
the check's text. An ALTERNATION is a maximal sequence of consecutive crossings of one edge in one intent with no news \
between any two neighbours; its LENGTH is its number of crossings. Bound: every alternation's length <= {ALT_MAX}. \
(Crossings with news between them are no ping-pong, B-C1: an intent may cross one edge more than {ALT_MAX} times in all.)
{EDGE_WINDOW_TEXT + chr(10) if EDGE_WINDOW_KIND == GRADED else ''}K8.WORLD_SIZE: every run's world.jsonl, measured before its deletion, is under {WORLD_MAX_BYTES} bytes (300 MB).
K8.FROZEN: the frozen-tree watch (provenance.FrozenTree) saw no change of the code under test from the batch's start to \
its verdict.
K8.LEFTOVER: no python process whose command line names {PROFILE_PREFIX} is left after the batch.
REPORTED (information, never counted): K8.RUSTBORO: RUSTBORO_CITY visited by the game's truth (VISITED_RUSTBORO_CITY = 1 \
at the end) in at least {RUSTBORO_MIN} of 6 (ROUTE104 north has trainers; other blockers are A1's to measure). K8.ENDED: who \
ended each run (the harness's own stop record). Per run: map changes of both kinds, edge crossings, the longest \
alternation, the woods exit, the AI's outcome claim beside the game's flag.
{EDGE_WINDOW_TEXT + chr(10) if EDGE_WINDOW_KIND == REPORTED else ''}VERDICT: PASS iff every GRADED check PASSES. Nothing is tuned to a grader (B1): a miss is reported, never re-run on new \
seeds."""


# ====================================================================== registration
def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(path: Path) -> str:
    """A tracked file's sha256 with CRLF read as LF: git checks the same commit out with either line ending (measured
    2026-10-31: a worktree's ai_player/ files were CRLF and the main checkout's LF, 29 files, identical otherwise), and
    the code under test is the same either way."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def ai_code_sha256(repo: Path = REPO) -> str:
    """The AI's code as it plays: every file under `ai_player/` outside `gates/` and `evidence/`, without `*.md` and
    bytecode, by relative path and content (sorted; line endings normalised, `text_sha256`). A graded run is refused
    when it differs from the registration."""
    root = repo / "ai_player"
    digest = hashlib.sha256()
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")
        if parts[0] in ("gates", "evidence") or "__pycache__" in parts or path.suffix in (".md", ".pyc"):
            continue
        files.append((rel, path))
    for rel, path in sorted(files):
        digest.update(rel.encode("utf-8") + b"\0" + bytes.fromhex(text_sha256(path)))
    return digest.hexdigest()


def default_starts_root(build_root: Path | None = None) -> Path:
    if build_root is None:
        from ai_player.host import launcher
        build_root = launcher.resolve_build_root(None)
    return Path(build_root) / "profiles" / "ai-step5-play" / "ai_player_runs"


def start_files(starts_root: Path) -> dict[str, dict[str, Path]]:
    return {chain: {name: Path(starts_root) / folder / name for name in START_FILES}
            for chain, (folder, _) in STARTS.items()}


def jobs_of(first: int) -> list[dict]:
    return [{"chain": chain, "personality": STARTS[chain][1], "seed": first + offset,
             "name": f"KI128-{chain}-{first + offset}", "profile": f"{PROFILE_PREFIX}{first + offset}"}
            for chain, offset in JOB_ORDER]


def registered_numbers(seeds: tuple[int, int] = SEEDS, starts_root: Path | None = None, repo: Path = REPO,
                       frames: int = FRAMES) -> dict:
    """Everything the batch is graded by, hashed into its ledger registration (`numbers_sha256`). RAISES `SystemExit` when
    a start file is missing (nothing can be registered or run without it)."""
    starts_root = Path(starts_root) if starts_root is not None else default_starts_root()
    files = start_files(starts_root)
    missing = [str(p) for chain in files.values() for p in chain.values() if not p.is_file()]
    if missing:
        raise SystemExit(f"REFUSED: start files missing: {missing}")
    return {"family": FAMILY, "driver": DRIVER, "seeds": list(seeds), "bounds_text": BOUNDS_TEXT, "target": TARGET,
            "frames": frames, "wall": WALL, "parallel": PARALLEL, "stagger_seconds": STAGGER_SECONDS,
            "free_min_gb": FREE_MIN_GB, "world_max_bytes": WORLD_MAX_BYTES, "guard_world_bytes": GUARD_WORLD_BYTES,
            "guard_free_gb": GUARD_FREE_GB, "woods_min": WOODS_MIN, "rustboro_min": RUSTBORO_MIN, "alt_max": ALT_MAX,
            "edge_window_frames": EDGE_WINDOW_FRAMES, "edge_window_max": EDGE_WINDOW_MAX, "edge_window_kind": EDGE_WINDOW_KIND,
            "woods_north_warps": [list(w) for w in WOODS_NORTH_WARPS], "north_y": NORTH_Y, "purity_ids": list(PURITY_IDS),
            "jobs": [{k: j[k] for k in ("chain", "personality", "seed")} for j in jobs_of(seeds[0])],
            "starts": {chain: {"folder": STARTS[chain][0],
                               **{name: file_sha256(path) for name, path in chain_files.items()}}
                       for chain, chain_files in files.items()},
            "ai_code_sha256": ai_code_sha256(repo),
            "grader_files": {name: text_sha256(repo / name) for name in GRADER_FILES}}


def register(seeds: tuple[int, int], numbers: dict, note: str = "", path: Path = ledger.LEDGER) -> dict:
    """Pre-register the graded range with the numbers' sha256 (`ledger.register`; refused when any entry names the seeds)."""
    return ledger.register(FAMILY, DRIVER, seeds[0], seeds[1], ledger.numbers_sha256(numbers), note=note, path=path)


def begin(purpose: str, seeds: tuple[int, int], numbers: dict, tree: str | None, note: str = "",
          path: Path = ledger.LEDGER) -> tuple[dict, list[str]]:
    """A batch STARTS (`ledger.begin`): a graded one is refused unless registered with THESE numbers' sha256."""
    return ledger.begin(FAMILY, DRIVER, purpose, seeds[0], seeds[1], ledger.numbers_sha256(numbers), tree, note=note,
                        path=path)


def seeds_named(first: int, last: int, path: Path = ledger.LEDGER) -> list[dict]:
    """Every ledger entry, of ANY family, whose range overlaps first..last."""
    return [e for e in ledger.load(path).get("entries", []) if e["first"] <= last and first <= e["last"]]


# ====================================================================== the readers (pure; unit-tested on planted text)
MAP_LINE = re.compile(
    r"\[AI-WORLD\] MAP (?P<src>\S+) -> (?P<dst>\S+) at \((?P<ax>-?\d+), (?P<ay>-?\d+)\): "
    r"(?:the (?P<dir>up|down|left|right) edge(?: from \((?P<ex>-?\d+), (?P<ey>-?\d+)\))?|"
    r"the warp at \((?P<wx>-?\d+), (?P<wy>-?\d+)\))"
    r"(?: \((?P<actor>[^(),]*), f(?P<frame>\d+)\))?(?:; (?P<known>\d+) tiles of it known)?")
INTENT_LINE = re.compile(r"\[AI-WORLD\] intent '")
NOVELTY_LINE = re.compile(r"\[AI-WORLD\] novelty at f(?P<frame>\d+):")
MILESTONE_LINE = re.compile(r"MILESTONE (?P<id>\S+) done")


def parse_log(lines: Iterable[str]) -> dict:
    """The AI's log, in line order: its MAP lines (edge crossings and warps, each with its intent), its intents, novelty and
    milestone lines. JSON-able."""
    out: dict = {"lines": 0, "intents": 0, "maps": [], "novelty": [], "milestones": [], "edge_stops": 0, "warp_stops": 0}
    intent = 0
    for number, line in enumerate(lines):
        out["lines"] += 1
        if INTENT_LINE.search(line):
            intent += 1
            out["intents"] += 1
            continue
        found = MAP_LINE.search(line)
        if found:
            g = found.groupdict()
            edge = g["dir"] is not None
            out["maps"].append({"line": number, "intent": intent, "src": g["src"], "dst": g["dst"],
                                "arrive": [int(g["ax"]), int(g["ay"])], "kind": "edge" if edge else "warp",
                                "dir": g["dir"],
                                "depart": ([int(g["wx"]), int(g["wy"])] if not edge else
                                           ([int(g["ex"]), int(g["ey"])] if g["ex"] is not None else None)),
                                "actor": g["actor"], "frame": int(g["frame"]) if g["frame"] else None,
                                "known": int(g["known"]) if g["known"] else None})
            continue
        found = NOVELTY_LINE.search(line)
        if found:
            out["novelty"].append({"line": number, "frame": int(found["frame"])})
            continue
        found = MILESTONE_LINE.search(line)
        if found:
            out["milestones"].append({"line": number, "id": found["id"]})
        if "ping-pong: the edge" in line and "goal" in line:
            out["edge_stops"] += 1
        if "ping-pong: the warp" in line and "goal" in line:
            out["warp_stops"] += 1
    return out


def read_log_file(path: Path) -> dict:
    with open(path, encoding="utf-8", errors="replace") as handle:
        return parse_log(handle)


def first_north_log(log: dict) -> dict | None:
    """The FIRST MAP line arriving on ROUTE104 with y < NORTH_Y, and whether it is the woods' north warp."""
    for entry in log["maps"]:
        if entry["dst"] == "ROUTE104" and entry["arrive"][1] < NORTH_Y:
            by_woods = (entry["src"] == "PETALBURG_WOODS" and entry["kind"] == "warp"
                        and tuple(entry["depart"] or ()) in WOODS_NORTH_WARPS)
            return {**entry, "by_woods": by_woods}
    return None


def stream_world(path: Path, keep_last: Path | None = None) -> dict:
    """ONE PASS over a world.jsonl, line by line (never a whole-file read): for each transition the (tiles_learned, maps
    with visits) of the FIRST line holding it, keyed "frame|src|dst|how"; every transition as recorded; the line count, the
    unreadable lines, the size; the LAST line written to `keep_last` when given."""
    index: dict[str, list[int]] = {}
    transitions: list[list] = []
    seen: set[tuple] = set()
    lines = bad = 0
    previous = 0
    last: bytes | None = None
    size = path.stat().st_size
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                bad += 1
                continue
            lines += 1
            last = raw
            listed = data.get("transitions") or []
            tiles = int(data.get("tiles_learned") or 0)
            visited = sum(1 for memory in (data.get("maps") or {}).values() if memory.get("visits"))
            fresh = listed[previous:] if len(listed) >= previous else listed
            for t in fresh:
                key = (t[0], t[1], t[2], t[3], tuple(t[5] or ()), tuple(t[6] or ()))
                if key in seen:
                    continue
                seen.add(key)
                transitions.append(t)
                index.setdefault(f"{t[0]}|{t[1]}|{t[2]}|{t[3]}", [tiles, visited])
            previous = len(listed)
    if keep_last is not None and last is not None:
        keep_last.parent.mkdir(parents=True, exist_ok=True)
        keep_last.write_bytes(last)
    return {"bytes": size, "lines": lines, "bad_lines": bad, "index": index, "transitions": transitions,
            "last_line_bytes": len(last or b"")}


def map_key_table() -> dict[str, str]:
    """Map const -> memory key ("group:number"), by the framework's MapRSE enum (`rate_step5.map_keys`, test side)."""
    from ai_player.gates.rate_step5 import map_keys
    return map_keys()


def first_north_world(world: dict, start_frame: int, keys: dict[str, str]) -> dict | None:
    """The first transition made in THIS run (frame > start_frame) into ROUTE104 with an arrival y < NORTH_Y, and whether it
    is a warp from the woods' north warps."""
    route, woods = keys.get("ROUTE104"), keys.get("PETALBURG_WOODS")
    for t in sorted((t for t in world["transitions"] if t[0] > start_frame), key=lambda t: t[0]):
        if t[2] == route and t[6] and t[6][1] < NORTH_Y:
            return {"frame": t[0], "src": t[1], "dst": t[2], "how": t[3], "depart": t[5], "arrive": t[6],
                    "by_woods": t[1] == woods and t[3] == "warp" and tuple(t[5] or ()) in WOODS_NORTH_WARPS}
    return None


def alternations(log: dict, world: dict | None, keys: dict[str, str]) -> dict:
    """THE ALTERNATION RULE of the bounds text: per intent and edge, the maximal runs of consecutive crossings with no news
    (N1-N4) between neighbours. Returns the longest, every run over ALT_MAX, the unmatched crossings, and counts."""
    index = (world or {}).get("index") or {}
    novelty = [n["line"] for n in log["novelty"]]
    milestones = [m["line"] for m in log["milestones"]]

    def world_at(c: dict) -> list[int] | None:
        src, dst = keys.get(c["src"]), keys.get(c["dst"])
        if c["frame"] is None or src is None or dst is None:
            return None
        return index.get(f"{c['frame']}|{src}|{dst}|connection")

    def news(a: dict, b: dict) -> list[str]:
        why = []
        if any(a["line"] < n < b["line"] for n in novelty):
            why.append("N1 novelty line")
        if any(a["line"] < m < b["line"] for m in milestones):
            why.append("N2 milestone line")
        wa, wb = world_at(a), world_at(b)
        if wa is not None and wb is not None:
            if wb[0] > wa[0]:
                why.append(f"N3 tiles_learned {wa[0]} -> {wb[0]}")
            if wb[1] > wa[1]:
                why.append(f"N4 maps visited {wa[1]} -> {wb[1]}")
        return why

    crossings = [m for m in log["maps"] if m["kind"] == "edge"]
    unmatched = [c for c in crossings if world_at(c) is None]
    groups: dict[tuple, list[dict]] = {}
    for c in crossings:
        groups.setdefault((c["intent"], "|".join(sorted((c["src"], c["dst"])))), []).append(c)
    runs: list[dict] = []
    for (intent, edge), items in groups.items():
        start = 0
        for at in range(1, len(items) + 1):
            if at == len(items) or news(items[at - 1], items[at]):
                runs.append({"intent": intent, "edge": edge, "length": at - start,
                             "frames": [c["frame"] for c in items[start:at]][:12]})
                start = at
    longest = max(runs, key=lambda r: r["length"], default=None)
    return {"crossings": len(crossings), "unmatched": len(unmatched), "runs": len(runs),
            "max": longest["length"] if longest else 0, "max_at": longest,
            "over": [r for r in runs if r["length"] > ALT_MAX][:20],
            "over_count": sum(1 for r in runs if r["length"] > ALT_MAX)}


def edge_window(log: dict) -> dict:
    """K8.EDGE_WINDOW's measure (the bounds text): per edge, INTENTS IGNORED, the most crossings whose frames lie within
    EDGE_WINDOW_FRAMES of each other (last - first <= EDGE_WINDOW_FRAMES). Crossing lines without a frame are counted
    ('unframed'); the grader does not read a run that has any."""
    crossings = [m for m in log["maps"] if m["kind"] == "edge"]
    unframed = sum(1 for c in crossings if c["frame"] is None)
    edges: dict[str, list[int]] = {}
    for c in crossings:
        if c["frame"] is not None:
            edges.setdefault("|".join(sorted((c["src"], c["dst"]))), []).append(c["frame"])
    best = {"max": 0, "edge": None, "frames": []}
    per_edge: dict[str, int] = {}
    for edge, frames in edges.items():
        frames.sort()
        start = top = 0
        top_at = (0, 0)
        for at, frame in enumerate(frames):
            while frames[start] < frame - EDGE_WINDOW_FRAMES:
                start += 1
            if at - start + 1 > top:
                top, top_at = at - start + 1, (start, at + 1)
        per_edge[edge] = top
        if top > best["max"]:
            best = {"max": top, "edge": edge, "frames": frames[top_at[0]:top_at[1]][:40]}
    return {"crossings": len(crossings), "unframed": unframed, "max": best["max"], "max_edge": best["edge"],
            "max_frames": best["frames"], "window": EDGE_WINDOW_FRAMES,
            "over": sorted((e for e, n in per_edge.items() if n > EDGE_WINDOW_MAX), key=lambda e: -per_edge[e])[:20],
            "per_edge": dict(sorted(per_edge.items(), key=lambda kv: -kv[1])[:12])}


def pooled_alternation(log: dict, world: dict | None, keys: dict[str, str]) -> dict:
    """K8.ALTERNATION's rule with every crossing in ONE pooled intent (information, reported beside K8.EDGE_WINDOW)."""
    return alternations({**log, "maps": [{**m, "intent": 0} for m in log["maps"]]}, world, keys)


def measure_run(run_dir: Path, start_frame: int, keys: dict[str, str], keep_last: Path | None = None) -> dict:
    """One run's measures from its ai_player.log and world.jsonl (streamed). Never deletes anything."""
    measures: dict = {"log": None, "north_log": None, "world": None, "north_world": None, "alternation": None,
                      "edge_window": None, "alternation_pooled": None}
    log_path, world_path = run_dir / "ai_player.log", run_dir / "world.jsonl"
    log = read_log_file(log_path) if log_path.is_file() else None
    world = stream_world(world_path, keep_last) if world_path.is_file() else None
    if log is not None:
        edges = [m for m in log["maps"] if m["kind"] == "edge"]
        measures["log"] = {"lines": log["lines"], "intents": log["intents"],
                           "map_changes": {"edge": len(edges), "warp": len(log["maps"]) - len(edges)},
                           "novelty_lines": len(log["novelty"]), "milestones": [m["id"] for m in log["milestones"]],
                           "edge_stops": log["edge_stops"], "warp_stops": log["warp_stops"]}
        measures["north_log"] = first_north_log(log)
        measures["edge_window"] = edge_window(log)
    if world is not None:
        new = [t for t in world["transitions"] if t[0] > start_frame]
        by_how: dict[str, int] = {}
        for t in new:
            by_how[t[3]] = by_how.get(t[3], 0) + 1
        measures["world"] = {"bytes": world["bytes"], "lines": world["lines"], "bad_lines": world["bad_lines"],
                             "last_line_bytes": world["last_line_bytes"], "new_transitions": len(new),
                             "new_by_how": by_how}
        measures["north_world"] = first_north_world(world, start_frame, keys)
    if log is not None and world is not None:
        measures["alternation"] = alternations(log, world, keys)
        pooled = pooled_alternation(log, world, keys)
        measures["alternation_pooled"] = {k: pooled[k] for k in ("crossings", "runs", "max", "max_at", "over_count",
                                                                 "unmatched")}
    return measures


def measure_then_delete(world_path: Path) -> dict:
    """Section 6: the world.jsonl's size is RECORDED, then the file is DELETED. Returns {bytes, deleted}."""
    if not world_path.is_file():
        return {"bytes": None, "deleted": False, "present": False}
    size = world_path.stat().st_size
    # (the held-out's verifier, F3) a file another process still holds open cannot be deleted on Windows: the size is
    # already recorded, so the batch goes on to its verdict and the leftover file is reported, never a crash
    for _ in range(5):
        try:
            world_path.unlink()
            break
        except OSError:
            time.sleep(2.0)
    return {"bytes": size, "deleted": not world_path.exists(), "present": True}


# ====================================================================== the grader (pure; unit-tested on planted rows)
def _check(check_id: str, kind: str, ok: bool, n: int | None, floor: int | None, inputs: Iterable[str], text: str) -> Check:
    return Check(check_id, kind, status_of(ok, n, floor), n, floor, frozenset(inputs), f"{check_id}: {text}",
                 debt=AI_INPUT_DEBT)


def game_north(row: dict) -> bool:
    """The game shows the woods' north side passed: VISITED_RUSTBORO_CITY set at the end and not at the start."""
    after = (row.get("truth_after") or {}).get("marks") or {}
    before = (row.get("truth_before") or {}).get("marks") or {}
    return after.get("VISITED_RUSTBORO_CITY") == 1 and before.get("VISITED_RUSTBORO_CITY") != 1


def woods_counted(row: dict) -> bool:
    m = row.get("measures") or {}
    return bool((m.get("north_log") or {}).get("by_woods") and (m.get("north_world") or {}).get("by_woods"))


def _north_text(entry: dict | None) -> str:
    if not entry:
        return "none"
    return (f"{entry.get('src')}->{entry.get('dst')} {tuple(entry.get('depart') or ())}->{tuple(entry.get('arrive') or ())} "
            f"f{entry.get('frame')} ({'the woods north warp' if entry.get('by_woods') else 'NOT the woods north warp'})")


def grade_batch(rows: list[dict], expected: int = 6, frozen: tuple[bool, str] | None = None,
                leftover: list[str] | None = None) -> list[Check]:
    """THE GRADED BOUNDS of `BOUNDS_TEXT` over a batch's rows (one per run). `frozen` = (the watch held, its line);
    `leftover` = the processes found after the batch. Every check quotes both values."""
    checks: list[Check] = []
    # K8.PURITY
    judged, bad = 0, []
    for row in rows:
        statuses = {c["id"]: c["status"] for c in row.get("checks") or [] if c["id"] in PURITY_IDS}
        if statuses:
            judged += 1
        wrong = [f"{i} {statuses.get(i, 'MISSING')}" for i in PURITY_IDS if statuses.get(i) != PASS]
        if statuses and wrong:
            bad.append(f"{row['name']}: {', '.join(wrong)}")
    checks.append(_check("K8.PURITY", GRADED, judged >= expected and not bad, judged, expected, (HARNESS,),
                         f"purity CLEAN on every launch: {judged - len(bad)} of {judged} launches with every counting "
                         f"purity check PASS (want {expected} of {expected}); failing: {bad or 'none'}"))
    # K8.THIS_RUN
    fresh = [(row["name"], c["status"]) for row in rows for c in row.get("checks") or [] if c["id"] == "L5.THIS_RUN"]
    stale = [f"{name} {status}" for name, status in fresh if status != PASS]
    checks.append(_check("K8.THIS_RUN", GRADED, len(fresh) >= expected and not stale, len(fresh), expected,
                         (HARNESS, GAME), f"L5.THIS_RUN PASS on {len(fresh) - len(stale)} of {len(fresh)} runs (want "
                                          f"{expected} of {expected}); not: {stale or 'none'}"))
    # K8.WOODS
    read = [row for row in rows if (row.get("measures") or {}).get("log") and (row.get("measures") or {}).get("world")]
    counted = [row for row in read if woods_counted(row)]
    confirmed = [row for row in counted if game_north(row)]
    disagree = [row["name"] for row in read if game_north(row) and not woods_counted(row)]
    lines = []
    for row in read:
        m = row["measures"]
        lines.append(f"{row['name']}: log {_north_text(m.get('north_log'))}; world {_north_text(m.get('north_world'))}; "
                     f"game VISITED_RUSTBORO_CITY {((row.get('truth_after') or {}).get('marks') or {}).get('VISITED_RUSTBORO_CITY')}"
                     f" ({'confirms' if game_north(row) else 'cannot confirm'})")
    checks.append(_check("K8.WOODS", GRADED, len(counted) >= WOODS_MIN and not disagree, len(read), expected, (AI, GAME),
                         f"ROUTE104 north (y < {NORTH_Y}) reached by the warp from PETALBURG_WOODS (14|15, 5), the log AND "
                         f"the world memory agreeing: {len(counted)} of {len(read)} runs (bound: at least {WOODS_MIN} of "
                         f"{expected}); the game confirms {len(confirmed)} of them; the game shows Rustboro where the "
                         f"instruments do not: {disagree or 'none'}; per run: {' | '.join(lines) or 'none read'}"))
    # K8.ALTERNATION
    alts = [(row["name"], row["measures"]["alternation"]) for row in read if row["measures"].get("alternation")]
    over = [f"{name}: {a['over_count']} over, longest {a['max']} ({(a['max_at'] or {}).get('edge')} in intent "
            f"{(a['max_at'] or {}).get('intent')}, frames {(a['max_at'] or {}).get('frames')})" for name, a in alts if a["max"] > ALT_MAX]
    longest = max((a["max"] for _, a in alts), default=0)
    checks.append(_check("K8.ALTERNATION", GRADED, len(alts) >= expected and not over, len(alts), expected, (AI,),
                         f"the longest same-edge alternation in one intent (crossings with nothing new between) is "
                         f"{longest} over {len(alts)} runs (bound: <= {ALT_MAX} in every run); runs over: {over or 'none'}; "
                         f"per run (crossings, alternations, longest, unmatched): "
                         + "; ".join(f"{name} {a['crossings']}/{a['runs']}/{a['max']}/{a['unmatched']}" for name, a in alts)))
    # K8.EDGE_WINDOW (intents ignored; a run with an unframed crossing is not read)
    windows = [(row["name"], (row.get("measures") or {}).get("edge_window"), (row.get("measures") or {}).get("alternation_pooled"))
               for row in rows if (row.get("measures") or {}).get("edge_window")]
    unframed = [f"{name} {w['unframed']}" for name, w, _ in windows if w["unframed"]]
    framed = [(name, w, p) for name, w, p in windows if not w["unframed"]]
    wide = [f"{name}: {w['max']} on {w['max_edge']} (frames {w['max_frames'][:12]}); edges over: {w['over']}"
            for name, w, _ in framed if w["max"] > EDGE_WINDOW_MAX]
    checks.append(_check("K8.EDGE_WINDOW", EDGE_WINDOW_KIND, len(framed) >= expected and not wide, len(framed), expected,
                         (AI,), f"{'(information, never counted) ' if EDGE_WINDOW_KIND == REPORTED else ''}the most "
                                f"crossings of one edge within any {EDGE_WINDOW_FRAMES} frames, intents ignored, is "
                                f"{max((w['max'] for _, w, _ in framed), default=0)} over {len(framed)} runs (bound: <= "
                                f"{EDGE_WINDOW_MAX} in every run); runs over: {wide or 'none'}; not read (a crossing "
                                f"without a frame): {unframed or 'none'}; per run (crossings, most in a window, the "
                                f"longest no-news alternation with intents ignored, information): "
                                + "; ".join(f"{name} {w['crossings']}/{w['max']}/{(p or {}).get('max')}" for name, w, p in windows)))
    # K8.WORLD_SIZE
    sizes = [(row["name"], (row.get("world_file") or {}).get("bytes")) for row in rows]
    measured = [(name, size) for name, size in sizes if isinstance(size, int)]
    big = [f"{name} {size}" for name, size in measured if size >= WORLD_MAX_BYTES]
    checks.append(_check("K8.WORLD_SIZE", GRADED, len(measured) >= expected and not big, len(measured), expected,
                         (HARNESS,), f"every world.jsonl, measured before its deletion, under {WORLD_MAX_BYTES} bytes: "
                                     f"{', '.join(f'{n} {s}' for n, s in measured) or 'none measured'}; at or over: "
                                     f"{big or 'none'}; not measured: {[n for n, s in sizes if not isinstance(s, int)] or 'none'}"))
    if frozen is not None:
        checks.append(_check("K8.FROZEN", GRADED, bool(frozen[0]), 1, 1, (HARNESS,), f"the frozen-tree watch: {frozen[1]}"))
    if leftover is not None:
        checks.append(_check("K8.LEFTOVER", GRADED, not leftover, 1, 1, (HARNESS,),
                             f"python processes naming {PROFILE_PREFIX} after the batch: {leftover or 'none'} (want none)"))
    # REPORTED
    visited = [row["name"] for row in rows if ((row.get("truth_after") or {}).get("marks") or {}).get("VISITED_RUSTBORO_CITY") == 1]
    truths = sum(1 for row in rows if (row.get("truth_after") or {}).get("marks"))
    checks.append(_check("K8.RUSTBORO", REPORTED, len(visited) >= RUSTBORO_MIN, truths, None, (GAME,),
                         f"(information, never counted) RUSTBORO_CITY visited by the game's truth in {len(visited)} of "
                         f"{truths} runs (registered secondary: at least {RUSTBORO_MIN} of {expected}): {visited or 'none'}"))
    ended = [f"{row['name']} {(row.get('harness_stop') or {}).get('by')} ({(row.get('harness_stop') or {}).get('cause')}, "
             f"{(row.get('harness_stop') or {}).get('real_frames')} frames)" for row in rows]
    checks.append(_check("K8.ENDED", REPORTED, all((row.get("harness_stop") or {}).get("by") == "ai" for row in rows),
                         len(rows), None, (HARNESS,), f"(information, never counted) who ended each run: {'; '.join(ended)}"))
    return checks


def batch_verdict(checks: list[Check]) -> str:
    """PASS iff every GRADED check PASSES (no waivers: a VACUOUS check fails)."""
    return typed_verdict(checks, waivers={})


def check_lines(checks: list[Check]) -> list[str]:
    lines = [f"  [{c.status}] {c.id} {c.kind} n/floor {'-' if c.n is None else c.n}/{'-' if c.floor is None else c.floor} "
             f"inputs {'+'.join(sorted(c.inputs))}: {c.text}" for c in checks]
    for c in checks:
        if c.id in AI_INPUT_DEBT:
            lines.append(f"B1 DEBT {c.id} ({c.status}): reads the AI's {AI_INPUT_DEBT[c.id]['ai_input']}; why: "
                         f"{AI_INPUT_DEBT[c.id]['plan']}")
    return lines


# ====================================================================== one run (the child process)
def _truth_subset(truth: dict | None) -> dict | None:
    if not truth:
        return None
    story = truth.get("story") or {}
    return {"frame": truth.get("frame"), "map": truth.get("map"), "state_md5": truth.get("state_md5"),
            "marks": story.get("marks"), "stats": story.get("stats")}


def check_rows(checks) -> list[dict]:
    return [{"id": c.id, "kind": c.kind, "status": c.status, "n": c.n, "floor": c.floor, "text": c.text} for c in checks]


def child(job_path: Path) -> int:
    job = json.loads(job_path.read_text(encoding="utf-8"))
    from ai_player.gates import live_step5 as L5
    from ai_player.gates.live_step2 import check_purity

    L5.PROFILE = job["profile"]
    out = Path(job["out"])
    keep = out / job["name"]
    keep.mkdir(parents=True, exist_ok=True)
    earlier = []
    for line in Path(job["start_actions"]).read_text(encoding="utf-8").splitlines():
        try:
            earlier.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    arm = L5.Arm(job["name"], f"chapter 3 from {job['chain']}'s own end, {job['personality']}, seed {job['seed']}",
                 job["frames"], float(job["wall"]), L5.play_env(job["personality"], None, TARGET), seed=job["seed"],
                 fresh=False, state_from="START")
    carried = {"START": (Path(job["start_ss1"]), Path(job["start_world"]), earlier)}
    run = L5.run_arm(arm, Path(job["build_root"]), carried)
    check_purity(run, None)
    L5.check_after_is_this_run(run)
    start_frame = int((run.before or {}).get("frame") or 0)
    row = {**{k: job[k] for k in ("name", "chain", "personality", "seed", "profile")},
           "exit": run.exit_code, "elapsed": round(run.elapsed or 0, 1), "run_dir": str(run.run_dir),
           "command": run.command, "harness_stop": run.measures.get("harness_stop"),
           "truth_before": _truth_subset(run.before), "truth_after": _truth_subset(run.after),
           "outcome": ((run.verdict or {}).get("facts") or {}).get("exit_reason"),
           "verdict_file": (run.verdict or {}).get("verdict"), "counters": (run.verdict or {}).get("counters"),
           "gate_line": next((ln for ln in run.stdout.splitlines() if ln.startswith("[AI-GATE]")), None),
           "checks": check_rows(run.checks), "notes": list(run.notes), "start_frame": start_frame,
           "guard_killed": (out / f"{job['name']}.KILLED.txt").is_file()}
    measures, world_file = {}, {"bytes": None, "deleted": False, "present": False}
    if run.run_dir is not None and run.run_dir.is_dir():
        world_path = run.run_dir / "world.jsonl"
        # section 6: the size is RECORDED before anything else touches the file (the 300 MB bound is read from it)
        size_first = world_path.stat().st_size if world_path.is_file() else None
        measures = measure_run(run.run_dir, start_frame, map_key_table(), keep / "world_last.jsonl")
        world_file = measure_then_delete(world_path)
        if world_file.get("present") and size_first is not None and world_file["bytes"] != size_first:
            row["notes"].append(f"world.jsonl grew between its first size {size_first} and its deletion "
                                f"{world_file['bytes']}: the larger is graded")
            world_file["bytes"] = max(world_file["bytes"], size_first)
        for name in ("actions.jsonl", "ai_player.log", "purity.json", "end_state.ss1", "stdout.txt"):
            if (run.run_dir / name).is_file():
                shutil.copy2(run.run_dir / name, keep / name)
    row["measures"], row["world_file"] = measures, world_file
    (out / "rows").mkdir(parents=True, exist_ok=True)
    (out / "rows" / f"{job['name']}.json").write_text(json.dumps(row, ensure_ascii=False, indent=1, default=str),
                                                      encoding="utf-8")
    north = (measures.get("north_log") or {})
    print(f"[{job['name']}] exit {run.exit_code} {run.elapsed:.0f}s map {(run.after or {}).get('map')} woods "
          f"{north.get('by_woods')} f{north.get('frame')} alternation max {(measures.get('alternation') or {}).get('max')} "
          f"edge window max {(measures.get('edge_window') or {}).get('max')} "
          f"world {world_file.get('bytes')} bytes deleted {world_file.get('deleted')}", flush=True)
    return 0


# ====================================================================== the batch (the orchestrator)
def leftover_processes() -> list[str]:
    """Python processes whose command line names this batch's profiles (the launcher, the framework, the truth reads of
    a state under one of them). Never any other process: the bot tuner's lanes run beside this driver."""
    done = subprocess.run(["powershell", "-NoProfile", "-Command",
                           "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine "
                           f"-like '*{PROFILE_PREFIX}*' }} | ForEach-Object {{ \"$($_.ProcessId) $($_.CommandLine)\" }}"],
                          capture_output=True, timeout=60)
    return [line.strip()[:200] for line in done.stdout.decode(errors="replace").splitlines() if line.strip()]


def free_gb(path: Path) -> float:
    return shutil.disk_usage(str(path)).free / 1e9


def kill_descendants(pid: int) -> list[int]:
    """Kill every DESCENDANT of `pid` (the launcher under a child), never `pid` itself: the child then records and measures."""
    import psutil

    try:
        family = psutil.Process(pid).children(recursive=True)
    except psutil.Error:
        return []
    killed = []
    for proc in family:
        try:
            proc.kill()
            killed.append(proc.pid)
        except psutil.Error:
            pass
    return killed


def salvage(job: dict, build_root: Path, out: Path) -> dict | None:
    """A run whose child left NO row (it crashed, or was killed with it): its newest run folder's world.jsonl is still
    measured and DELETED (the disk rule holds whatever happened), and a row is written with NO checks, so the purity and
    freshness bounds read it as not judged (VACUOUS, which fails). None when the run left no folder at all."""
    runs = build_root / "profiles" / job["profile"] / "ai_player_runs"
    folders = sorted(p for p in runs.iterdir() if p.is_dir()) if runs.is_dir() else []
    if not folders:
        return None
    run_dir = folders[-1]
    world_path = run_dir / "world.jsonl"
    size_first = world_path.stat().st_size if world_path.is_file() else None
    measures = measure_run(run_dir, 0, map_key_table(), out / job["name"] / "world_last.jsonl")
    world_file = measure_then_delete(world_path)
    if size_first is not None and world_file.get("bytes") is not None:
        world_file["bytes"] = max(world_file["bytes"], size_first)
    row = {**{k: job[k] for k in ("name", "chain", "personality", "seed", "profile")}, "exit": None, "elapsed": None,
           "run_dir": str(run_dir), "checks": [], "measures": measures, "world_file": world_file, "salvaged": True,
           "truth_before": None, "truth_after": None, "harness_stop": None, "start_frame": None,
           "notes": ["NO CHILD ROW: salvaged by the orchestrator (the child crashed or was killed); its world.jsonl was "
                     "measured and deleted; the start frame is unknown, so its world transitions are read from frame 0"]}
    (out / "rows").mkdir(parents=True, exist_ok=True)
    (out / "rows" / f"{job['name']}.json").write_text(json.dumps(row, ensure_ascii=False, indent=1, default=str),
                                                      encoding="utf-8")
    return row


def run_batch(args) -> int:
    from ai_player.gates.check_grader_imports import scan
    from ai_player.gates.provenance import keep_earlier, line_digest, provenance, snapshot_tree, watch
    from ai_player.host import launcher

    out = Path(args.out).resolve()
    if out.is_relative_to(REPO):
        print(f"REFUSED: --out {out} is inside the repository; the summaries live outside it (section 6)")
        return 2
    build_root = Path(args.build_root).resolve() if args.build_root else launcher.resolve_build_root(None)
    starts_root = Path(args.starts_from) if args.starts_from else default_starts_root(build_root)
    graded = args.purpose == "graded"
    if graded and (args.first_seed not in (None, SEEDS[0]) or args.frames not in (None, FRAMES)):
        print(f"REFUSED: a graded batch plays the registered seeds {SEEDS[0]}-{SEEDS[1]} and {FRAMES} frames")
        return 2
    first = SEEDS[0] if graded else args.first_seed
    if first is None:
        print("REFUSED: a development batch needs --first-seed (6 seeds no graded registration names)")
        return 2
    seeds = (first, first + 5)
    frames = FRAMES if graded else (args.frames or FRAMES)
    problems = scan(REPO, ("ai_player.gates.live_ki128",))
    print(f"[KI128] grader imports (G-3 walk of this driver): {'PASS' if not problems else problems}", flush=True)
    if problems:
        return 2
    free = free_gb(build_root)
    print(f"[KI128] free on the build root's drive: {free:.1f} GB (floor {FREE_MIN_GB:g})", flush=True)
    if free < FREE_MIN_GB:
        print(f"REFUSED: {free:.1f} GB free, under the {FREE_MIN_GB:g} GB floor (section 6)")
        return 2
    jobs = jobs_of(first)
    taken = [j["profile"] for j in jobs if (build_root / "profiles" / j["profile"]).exists()]
    if taken:
        print(f"REFUSED: the disposable profiles {taken} exist under {build_root / 'profiles'}: each run needs a NEW one")
        return 2
    numbers = registered_numbers(seeds, starts_root, REPO, frames)
    sha = ledger.numbers_sha256(numbers)
    print(f"[KI128] numbers sha256 {sha} (seeds {seeds[0]}-{seeds[1]}, {args.purpose})", flush=True)
    code = provenance(REPO)
    print(f"[KI128] code: {code}", flush=True)
    tree = watch(REPO, explicit=True)
    kept = snapshot_tree(REPO)
    print(f"[KI128] frozen-tree watch: {len(tree.stats)} files; tree kept: {kept}", flush=True)
    try:
        entry, ledger_lines = begin(args.purpose, seeds, numbers, line_digest(code),
                                    note=f"KI-128 + KI-129 held-out (spec 2026-10-31 section 5), {args.purpose}, driver "
                                         f"ai_player/gates/live_ki128.py, numbers sha256 {sha[:16]}, free {free:.1f} GB")
    except ledger.Refused as error:
        print(f"REFUSED by the ledger: {error}")
        return 2
    for line in ledger_lines:
        print(f"[KI128] {line}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    began = time.strftime("%Y-%m-%d %H:%M:%S")
    files = start_files(starts_root)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    pending = []
    for job in jobs:
        job = {**job, "frames": frames, "wall": WALL, "out": str(out), "build_root": str(build_root),
               "start_ss1": str(files[job["chain"]]["end_state.ss1"]), "start_world": str(files[job["chain"]]["world.jsonl"]),
               "start_actions": str(files[job["chain"]]["actions.jsonl"])}
        path = out / f"{job['name']}.job.json"
        path.write_text(json.dumps(job, indent=1), encoding="utf-8")
        pending.append((job, path))
    running: list = []
    not_run: list[str] = []
    guard_events: list[str] = []
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    while pending or running:
        while pending and len(running) < PARALLEL:
            job, path = pending.pop(0)
            if tree.moved or not tree.check(f"before {job['name']}"):
                not_run.append(job["name"])
                print(f"[KI128] {job['name']}: NOT RUN, the code under test changed mid-batch", flush=True)
                continue
            log = open(out / f"{job['name']}.child.log", "w", encoding="utf-8")
            proc = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "child", str(path)],
                                    cwd=str(REPO), env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
            running.append((job, proc, log))
            print(f"[KI128] {job['name']} started ({time.strftime('%H:%M:%S')}), pid {proc.pid}", flush=True)
            time.sleep(STAGGER_SECONDS)
        for item in list(running):
            job, proc, log = item
            runs = build_root / "profiles" / job["profile"] / "ai_player_runs"
            worlds = list(runs.glob("*/world.jsonl")) if runs.is_dir() else []
            big = max((w.stat().st_size for w in worlds if w.exists()), default=0)
            now_free = free_gb(build_root)
            marker = out / f"{job['name']}.KILLED.txt"
            if proc.poll() is None and not marker.exists() and (big > GUARD_WORLD_BYTES or now_free < GUARD_FREE_GB):
                killed = kill_descendants(proc.pid)
                event = (f"{job['name']}: the disk guard killed the launcher at {time.strftime('%H:%M:%S')} (world.jsonl "
                         f"{big} bytes, {now_free:.1f} GB free; pids {killed})")
                marker.write_text(event + "\n", encoding="utf-8")
                guard_events.append(event)
                print(f"[KI128] {event}", flush=True)
            if proc.poll() is not None:
                log.close()
                running.remove(item)
                print(f"[KI128] {job['name']} child exit {proc.returncode} ({time.strftime('%H:%M:%S')})", flush=True)
        time.sleep(5)
    left = leftover_processes()
    print(f"[KI128] leftover processes: {left or 'none'}", flush=True)
    rows = []
    for job in jobs:
        row_path = out / "rows" / f"{job['name']}.json"
        if row_path.is_file():
            rows.append(json.loads(row_path.read_text(encoding="utf-8")))
            continue
        print(f"[KI128] {job['name']}: NO ROW (not run or crashed: see {out / (job['name'] + '.child.log')})", flush=True)
        salvaged = salvage(job, build_root, out) if job["name"] not in not_run else None
        if salvaged is not None:
            rows.append(salvaged)
            print(f"[KI128] {job['name']}: salvaged, world.jsonl {salvaged['world_file']}", flush=True)
    held = tree.check("after the batch")
    overall_before_seal = "PASS" if held else "FAIL"
    _, frozen_line = tree.seal(overall_before_seal)
    checks = grade_batch(rows, len(jobs), (held and not tree.moves, frozen_line), left)
    result = batch_verdict(checks)
    failing = [c.id for c in checks if c.kind == GRADED and c.status != PASS]
    label = ledger.label(args.purpose)
    woods = next(c for c in checks if c.id == "K8.WOODS")
    alt = next(c for c in checks if c.id == "K8.ALTERNATION")
    window = next(c for c in checks if c.id == "K8.EDGE_WINDOW")
    rust = next(c for c in checks if c.id == "K8.RUSTBORO")
    verdict_line = (f"{label}, {result if graded else 'NO PASS (development: ' + result + ' by the registered rules)'}"
                    f"{' (failing: ' + ', '.join(failing) + ')' if failing else ''}: KI-128 + KI-129 held-out, seeds "
                    f"{seeds[0]}-{seeds[1]}, numbers sha256 {sha[:16]}; {len(rows)} of {len(jobs)} runs; "
                    f"{woods.text.split(': ', 1)[1][:220]}; {alt.text.split(': ', 1)[1][:160]}; {window.text.split(': ', 1)[1][:160]}; "
                    f"{rust.text.split(': ', 1)[1][:140]}")
    stamp = time.strftime("%Y-%m-%d")
    evidence = EVIDENCE_DIR / f"{stamp}-ki128-heldout{'' if graded else '-dev'}.txt"
    keep_earlier(evidence)
    head = (f"KI-128 + KI-129 HELD-OUT - {'GRADED' if graded else 'DEVELOPMENT, NOT GRADED, NO PASS'} - VERDICT {result}"
            f"{' (failing: ' + ', '.join(failing) + ')' if failing else ''} (build spec "
            f"2026-10-31-KI128-KI129-BUILD-SPEC.md section 5; driver ai_player/gates/live_ki128.py)")
    text = [head, f"date: {began} -> {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}",
            *ledger_lines, f"numbers sha256: {sha} (seeds {seeds[0]}-{seeds[1]}; {args.purpose})",
            f"build root: {build_root}   starts: {starts_root}   out: {out}   free at start: {free:.1f} GB",
            f"frozen tree: {frozen_line}", f"leftover processes: {left or 'none'}",
            f"not run: {not_run or 'none'}   disk guard: {guard_events or 'never fired'}",
            f"VERDICT: {result}", "checks (registered in the bounds text below; each quotes both values):",
            *check_lines(checks), "", "per run:"]
    for row in rows:
        m = row.get("measures") or {}
        text.append(f"  {row['name']} ({row['personality']}, seed {row['seed']}): exit {row['exit']}, {row['elapsed']} s, "
                    f"stop {json.dumps(row.get('harness_stop'), ensure_ascii=False)}")
        text.append(f"    outcome (the AI's claim): {row.get('outcome')!r}; game VISITED_RUSTBORO_CITY "
                    f"{((row.get('truth_after') or {}).get('marks') or {}).get('VISITED_RUSTBORO_CITY')}; map "
                    f"{(row.get('truth_before') or {}).get('map')} -> {(row.get('truth_after') or {}).get('map')}")
        text.append(f"    log: {json.dumps(m.get('log'), ensure_ascii=False)}")
        text.append(f"    woods: log {_north_text(m.get('north_log'))}; world {_north_text(m.get('north_world'))}")
        text.append(f"    world: {json.dumps(m.get('world'), ensure_ascii=False)}; file {json.dumps(row.get('world_file'))}")
        alt_m = m.get("alternation") or {}
        text.append(f"    alternation: crossings {alt_m.get('crossings')}, alternations {alt_m.get('runs')}, longest "
                    f"{alt_m.get('max')} at {json.dumps(alt_m.get('max_at'))}, over {alt_m.get('over_count')}, unmatched "
                    f"{alt_m.get('unmatched')}")
        win_m, pool_m = m.get("edge_window") or {}, m.get("alternation_pooled") or {}
        text.append(f"    edge window ({EDGE_WINDOW_FRAMES} frames, intents ignored): most {win_m.get('max')} on "
                    f"{win_m.get('max_edge')} (frames {win_m.get('max_frames')}), unframed {win_m.get('unframed')}, per "
                    f"edge {json.dumps(win_m.get('per_edge'))}; no-news alternation with intents ignored (information): "
                    f"longest {pool_m.get('max')} at {json.dumps(pool_m.get('max_at'))}")
        text.append(f"    run dir: {row.get('run_dir')}; kept: {out / row['name']}; notes: {row.get('notes') or 'none'}")
    text += ["", "BOUNDS TEXT (hashed into the registration):", BOUNDS_TEXT]
    evidence.write_text("\n".join(text) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps({"began": began, "ended": time.strftime("%Y-%m-%d %H:%M:%S"),
                                                  "purpose": args.purpose, "seeds": list(seeds), "numbers_sha256": sha,
                                                  "ledger": entry["id"], "frozen": [held, frozen_line], "leftover": left,
                                                  "not_run": not_run, "guard": guard_events, "verdict": result,
                                                  "checks": check_rows(checks)}, indent=1, default=str), encoding="utf-8")
    reference = (str(evidence.relative_to(REPO)).replace("\\", "/") if evidence.resolve().is_relative_to(REPO)
                 else str(evidence))
    ledger.finish(entry["id"], verdict_line, reference)
    print(f"[KI128] evidence: {evidence}", flush=True)
    for line in check_lines(checks):
        print(f"[KI128] {line.strip()}", flush=True)
    print(f"[KI128] OVERALL {result} ({label}); ledger #{entry['id']} finished", flush=True)
    return 0 if result == "PASS" else 1


def grade_dir(out: Path) -> int:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "rows").glob("*.json"))]
    results = json.loads((out / "results.json").read_text(encoding="utf-8")) if (out / "results.json").is_file() else {}
    frozen = tuple(results["frozen"]) if results.get("frozen") else None
    checks = grade_batch(rows, 6, frozen, results.get("leftover"))
    for line in check_lines(checks):
        print(line)
    print(f"OFFLINE RE-GRADE (no ledger write): {batch_verdict(checks)} over {len(rows)} rows")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("bounds")
    p.add_argument("--starts-from")
    p = sub.add_parser("register")
    p.add_argument("--starts-from")
    p.add_argument("--note-file")
    p = sub.add_parser("run")
    p.add_argument("--out", required=True)
    p.add_argument("--build-root")
    p.add_argument("--starts-from")
    p.add_argument("--purpose", choices=("graded", "development"), default="graded")
    p.add_argument("--first-seed", type=int)
    p.add_argument("--frames", type=int)
    p = sub.add_parser("grade")
    p.add_argument("dir")
    p = sub.add_parser("read")
    p.add_argument("run_dir")
    p.add_argument("--start-frame", type=int, default=0)
    p = sub.add_parser("child")
    p.add_argument("job")
    args = parser.parse_args()
    if args.cmd == "child":
        return child(Path(args.job))
    if args.cmd == "bounds":
        numbers = registered_numbers(SEEDS, Path(args.starts_from) if args.starts_from else None)
        print(BOUNDS_TEXT)
        print(json.dumps({k: v for k, v in numbers.items() if k != "bounds_text"}, indent=1))
        print(f"BOUNDS TEXT sha256 {hashlib.sha256(BOUNDS_TEXT.encode('utf-8')).hexdigest()}")
        print(f"REGISTERED NUMBERS sha256 {ledger.numbers_sha256(numbers)}")
        return 0
    if args.cmd == "register":
        named = [e for e in seeds_named(*SEEDS) if not (e["driver"] == DRIVER and e["status"] == "registered")]
        if named:
            print(f"REFUSED: ledger entries already name seeds {SEEDS[0]}-{SEEDS[1]}: {[e['id'] for e in named]}")
            return 2
        numbers = registered_numbers(SEEDS, Path(args.starts_from) if args.starts_from else None)
        note = (Path(args.note_file).read_text(encoding="utf-8").strip() if args.note_file else
                "KI-128 + KI-129 graded held-out (build spec 2026-10-31 section 5), driver ai_player/gates/live_ki128.py: "
                "registered BEFORE any run; the bounds field is the sha256 of registered_numbers() (the bounds text, the "
                "constants, the start files', the AI code's and the grader files' sha256)")
        print(BOUNDS_TEXT)
        entry = register(SEEDS, numbers, note)
        print(f"REGISTERED numbers sha256 {ledger.numbers_sha256(numbers)}")
        print("ENTRY " + json.dumps(entry, ensure_ascii=False))
        return 0
    if args.cmd == "run":
        return run_batch(args)
    if args.cmd == "grade":
        return grade_dir(Path(args.dir))
    if args.cmd == "read":
        run_dir = Path(args.run_dir)
        measures = measure_run(run_dir, args.start_frame, map_key_table())
        print(json.dumps(measures, indent=1, default=str))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
