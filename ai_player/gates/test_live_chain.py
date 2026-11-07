"""UNIT PROOFS of the New Game chain held-out driver (`gates/live_chain.py`), on PLANTED run folders, rows and milestone
data, with a STUB launcher (no emulator, no live run). Test side.

    py -3.12 -B -m unittest ai_player.gates.test_live_chain

Every guard has a FAULT case that must fail or refuse and a CONTROL case that must pass (CLAUDE.md rule 6). The cases are
module-level functions `case_<name>(M, tmp)` taking the module under test: the TestCase classes call them with the real
`live_chain`, and MutantTests (spec section 10, decision D5: the mutants live IN this suite so they re-run on every lane)
call the named ones with a MUTATED copy of `live_chain.py` (one guard broken each) and require an AssertionError; its CONTROL
M0 loads the unmutated source the same way and passes every case any mutant names. (Critic CH-05) the copy is loaded from a
temp `ai_player/gates/live_chain.py` and its REPO, GATES and EVIDENCE_DIR are rebound to this tree's; `live_step5.PROFILE`, a
process global, is restored after every chain.
  LegsTests        the legs and budgets of ch5_rival_meet; the proofs pinned to the decomp's numbers (a second path); short
                   targets; an optional or waypoint chapter end skipped; refused targets, chapters and orders.
  ProofTests       flags, the VAR 7/8 boundary, a missing key, a trainer flag, an empty proof.
  ContinueTests    each of C1-C6 alone stops, naming both values; a failed deletion does NOT stop (critic CH-03).
  CustodyTests     a wrong start md5, frame, world sha or path, L1 from a state, with a world or another starter, an extra
                   environment key, an UNREAD start truth (N7).
  ChainRunTests    five legs through a stub: carried state and KEPT world, every world deleted; a miss at L2 stops with L3-L5
                   NOT RUN and two launches; stale state, truncated last line, guard marker, STOP.txt, the cap; an overshoot
                   still reaches (critic CH-12); the profile guard; a raising leg is salvaged.
  GradeTests       LC.REACH, PURITY, THIS_RUN, WORLD_SIZE, CUSTODY (every chain's L1 ran: CH-06), STARTER, MEMORY (CH-11),
                   FROZEN, LEFTOVER; REPORTED never counts; every check quotes its bound.
  DiskTests        301 MB measured and deleted; the stream never reads a whole file (N5: open().read() too); the guard's
                   boundaries; only the newest folder; a stat race (CH-14); salvage (CH-13); the end sweep.
  RefusalTests     R1-R9 (+ CH-08's build root, CH-15's replayed rehearsal seeds), each FAULT and CONTROL; --purpose required.
  LedgerTests      register then begin; changed budget, REACH_MIN, cap, milestones, AI code or grader refused; development.
  SchedulerTests   at most 3 at once (exactly 3), JOB_ORDER, the stagger, a chain not started.
  OrchestratorTests  whole batches with stub launches, a temp ledger and evidence: PASS; the dry run of spec section 14 (a
                   stop at L2 and a salvage); unregistered refused; development; the free-space ABORT (CH-07); the world
                   guard's kill; the watchdog; a frozen-tree move.
  WiringTests      (critic CH-01) the orchestrator and the child CALL their guards (a deleted call passes every test of
                   the guard it deletes).
  ImportTests, ReaderTests, TieTests: the G-3 walk; no AI file imports the driver (an AST scan, CH-17: a mention does not
  fire); the real log lines; the AI reads only the last line of a world file.
THE FIX ROUND (the verifier's V-01..V-09, 2026-11-05; each new or changed guard has a FAULT case, a CONTROL case and a
mutant in MUTANTS):
  OutTests         V-01: a non-empty --out (STOP.txt, ABORT.txt, any file) is refused BEFORE ledger.begin, graded and
                   development, the registration unspent; a missing or empty --out proceeds.
  RegradeTests     V-02: only the registered chains' rows count (a foreign row, a second row, a row of another identity);
                   every leg re-derived from the row's facts (a flipped continue flag, a weakened row proof, a renamed leg,
                   a swapped kept file never count; a stored custody problem still does); grade DIR prints what it
                   ignored and reads the marker files; the honest batch re-grades as it was graded.
  ClosureTests     V-03: every file of the import closure is hashed (drop one: red); the scan follows function-local,
                   except-block and relative imports and parent packages, and not a mention or the AI's own imports; the
                   data the grade reads is hashed; an edited decoder, symbol table or gates module is refused; a change
                   of line endings alone is accepted (by design).
  KindTests        V-04: one impure, one stale L5 leg or one wrong starter fails the BATCH; every check the bounds text
                   lists as GRADED is GRADED, and the converse.
  GuardTests       V-05: the watchdog's value and formula; the larger world size graded; the kept line outside the repo;
                   a partly overlapping development range refused; a leftover process read after the batch; git_state on
                   a scratch repository; the ABORT check before each leg; LC.STARTER's floor.
  PredictionTests  V-06: the registered prediction sha256 is the FILE's bytes'; a prediction that is not UTF-8 is refused.
  DeadLaunchTests  V-08: a launch that died before playing a frame is named in the row, the evidence and the ledger (and
                   still fails); a leg with no world file reads "no world file", never "not deleted".
THE SECOND FIX ROUND (the independent checker's C2-01..C2-07, 2026-11-05; same rule: FAULT, CONTROL, a mutant each):
  RegradeTests     C2-01: a row whose chain, pair, personality, starter, seed or profile is not the registered job's is
                   IGNORED like a second row, so its chain is ABSENT and the batch FAILS (from an impure original; a
                   starter-only mismatch); C2-03: custody re-derived over a stored [], grade DIR and the in-run grade by the
                   REGISTERED proofs, the evidence's per-chain line prints the RE-DERIVED reach; a kept line that is no
                   JSON object never counts.
  ClosureTests     C2-02: the closure starts from the files run by path (PATH_ROOTS) and the plugins loaded by name; every
                   path-built argv of the closure's files and the AI's code runs a root (an AST scan; a mention does not
                   count); every top-level framework name an import names is followed; edits of the purity gate, pokebot.py
                   and two plugins are refused; C2-05: else, finally, match, with and class-body imports are found;
                   register and a graded run are REFUSED (R12) while the closure has an unhashed file.
  GradeErrorTests  C2-07: an exception while grading or writing the evidence still FINISHES the ledger entry as ERROR (no
                   PASS or FAIL), exit 4, with the traceback in the evidence.
  (also) DeadLaunchTests C2-04: the dead launch named in LC.PURITY's and LC.THIS_RUN's texts and in the ledger verdict's own
                   clause; PredictionTests C2-06; GuardTests the verifier's V02 (an unread OT and TID never prove the
                   player's starter).
THE THIRD FIX ROUND (the independent check's C3-E01..E07, C3-G01..G06, C3-H01..H07 and the chains-run guard, 2026-11-05;
same rule: FAULT, CONTROL, a mutant each):
  OutTests         C3-E01, C3-G05: --out and the job files are made BEFORE ledger.begin; an --out under a file, on a
                   missing drive or with an invalid name is refused (R11) with the registration unspent; a batch the ledger
                   refuses removes what it made; the profile snapshots come before begin too.
  ChainGuardTests  an exception or a Ctrl+C WHILE THE CHAINS RUN kills the running chain processes and finishes the entry
                   as ERROR (the interrupt then goes on).
  UntrustedTests   C3-E02: the AI's world lines (a wrong type, a 100,000-deep line), its log, its verdict file and actions
                   are untrusted: a failed check of that leg, a GRADED batch (FAIL, exit 1), never the harness's ERROR.
  GradeErrorTests  C3-E03..E07: the ledger write retried (computed verdict first), a ledger that cannot be written said
                   (NOT finished, the command, exit 4) and finished by `finish-entry`; any exception type; both results
                   writes; a development error; results.error.json beside results.json; grade DIR on an ERROR batch and
                   its exit codes; exit 5 for an uncovered crash; an unprintable exception; a Ctrl+C while grading; the
                   ERROR evidence's marked lines and single bounds text.
  RegradeTests     C3-G01: each leg's own records name its registered job (a relabelled copy stays FAIL), no shared run
                   folder or kept file; C3-G02/G04: grade DIR's numbers verified against their sha256 and the ledger, a
                   missing record FAILS, a moved --out, a move seen only at the seal; C3-G03: each identity field alone;
                   C3-G06: a NOT RUN after a continuing leg, unexplained, fails custody.
  ClosureTests     C3-H01: CPython's resolution order, a package, an extension module or bytecode beside a closure module,
                   a forged __pycache__ file; C3-H02: script-folder shadows, PYTHONPATH and friends; C3-H04: every file
                   named; C3-H05: the AI's framework imports start the closure; C3-E06: a file that does not parse is named.
  WiringTests      C3-H03: the production Deps defaults.
THE FOURTH FIX ROUND (the fourth check's C4-E01..E07, C4-G01..G06, C4-H01..H08, 2026-11-06; same rule: FAULT (the finding's
own scenario), CONTROL, a mutant each; the check's surviving mutants re-anchored and pinned):
  C4ErrorTests     C4-E01: a world.jsonl that is a FOLDER, or one the OS refuses to open, is a failed check, in the chain
                   process and in the orchestrator's salvage (GRADED FAIL, never ERROR); C4-E02: --out claimed exclusively,
                   a second launch refused (R11) without touching the first's files; C4-E07: every folder prepare_out made
                   removed; C4-E03: a second Ctrl+C while the guard finishes (from the sweep, the ledger write, a kill) still
                   finishes the entry, SIGINT ignored meanwhile and a line printed first, and a computed verdict already
                   written is never overwritten; C4-E04: a lone surrogate written escaped; C4-E05: finish-entry writes only
                   this driver's ERROR verdict.
  C4GradingTests   C4-G01, C4-E06: grade DIR reads the ledger entry NOW and never reports better than it (numbers deleted,
                   seeds moved, rows forged, an ERROR or 'started' entry, a renumbered id); C4-G02: a planted stop file or a
                   deleted leg never turns FAIL into PASS; C4-G03: ABORTED and development said, with their exits; C4-G04:
                   the salvage exemption reads the orchestrator's events. (C4-G05 is pinned in GradeTests, RegradeTests.)
  C4HashingTests   C4-H01: .pyw beside a namespace package, the exact homes; C4-H03: names installed outside the
                   repository; C4-H04, C4-H06: the AI's caches and bytecode, code under evidence/; C4-H05: the closure
                   check falls through; C4-H07: the check's twelve surviving branches; C4-H08: the production bodies.
                   (C4-H02 is in ClosureTests' python_env_refused.)
THE FIFTH FIX ROUND (the fifth check's C5-01..C5-05, 2026-11-06; same rule: FAULT (the finding's own scenario), CONTROL,
a mutant each, check 5's surviving MY02 among them):
  C5Tests          C5-01: grade DIR never exits 0 for an edited graded FAIL folder (its numbers deleted, its seeds moved,
                   its purpose relabelled): the folder's own jobs are checked against its seeds with no numbers, and the
                   entry its recorded ledger id names must have its seeds and purpose (a renumbered ledger excepted);
                   C5-02: when results.error.json cannot be written either, the printed finish-entry command still works,
                   from the copy of the ERROR record in ledger.unfinished.json, under the same checks; C5-03: a folder ERROR
                   or ABORTED mark beside an entry finished with PASS or FAIL is a contradiction (FAIL, exit 1); C5-04:
                   SIGINT restored after the guard, pinned with a fresh sentinel handler; C5-05: an entry never begun or
                   with a verdict this driver never writes is UNVERIFIED.
The module's temp root is removed at exit as well as in tearDownModule, so a process that imports it outside unittest (a
probe, a mutant worker) leaves no livechain_test_* folder behind.
"""

from __future__ import annotations

import argparse
import ast
import atexit
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import string
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import ledger  # noqa: E402
from ai_player.gates import live_chain as LC  # noqa: E402
from ai_player.gates import live_step2 as L2  # noqa: E402
from ai_player.gates import live_step5 as L5  # noqa: E402
from ai_player.options import ENV_STARTER, ENV_TARGET  # noqa: E402

GATES = Path(__file__).resolve().parent
SOURCE = GATES / "live_chain.py"
LEDGER_AT_START = ledger.LEDGER.read_bytes() if ledger.LEDGER.is_file() else None
#: the TEST's own copy of the six counting purity ids (a mutant that drops one from the driver is still caught)
PURITY_SIX = ("L5.PURITY_GATE", "L5.PURITY_CLEAN", "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_BREACHES",
              "L5.PURITY_PACKAGE")
#: THE SECOND PATH of the proofs: the chapter ends' numbers from the PINNED decomp (731ad5b), hard-coded here, so a changed
#: proof in milestones.json turns LegsTests red. include/constants/flags.h:136 FLAG_ADVENTURE_STARTED 0x74, :279
#: FLAG_ENABLE_RIVAL_MATCH_CALL 0xFD, :1319 FLAG_DEFEATED_RUSTBORO_GYM 0x4F0, :1348 SYSTEM_FLAGS 0x860, :1351
#: FLAG_SYS_POKEDEX_GET +0x1, :1359 FLAG_BADGE01_GET +0x7, :1380 FLAG_VISITED_RUSTBORO_CITY +0x19, :1507
#: FLAG_RECEIVED_POKEDEX_FROM_BIRCH +0x84; include/constants/vars.h:110 VAR_RUSTBORO_CITY_STATE 0x405A (8: set with the flag
#: at data/maps/RustboroCity/scripts.inc:740-741), :153 VAR_PETALBURG_GYM_STATE 0x4085 ("0-1: Wally tutorial, 2-6: 0-4 badges")
SYSTEM_FLAGS = 0x860
DECOMP_PROOFS = {
    "ch1_pokedex": {"flags": {"RECEIVED_POKEDEX_FROM_BIRCH": SYSTEM_FLAGS + 0x84, "SYS_POKEDEX_GET": SYSTEM_FLAGS + 0x1,
                              "ADVENTURE_STARTED": 0x74}, "variables": {}, "trainers": {}},
    "ch2_wally": {"flags": {}, "variables": {"PETALBURG_GYM_STATE": {"number": 0x4085, "at_least": 2}}, "trainers": {}},
    "ch3_rustboro": {"flags": {"VISITED_RUSTBORO_CITY": SYSTEM_FLAGS + 0x19}, "variables": {}, "trainers": {}},
    "ch4_roxanne": {"flags": {"DEFEATED_RUSTBORO_GYM": 0x4F0, "BADGE01_GET": SYSTEM_FLAGS + 0x7}, "variables": {},
                    "trainers": {}},
    "ch5_rival_meet": {"flags": {"ENABLE_RIVAL_MATCH_CALL": 0xFD},
                       "variables": {"RUSTBORO_CITY_STATE": {"number": 0x405A, "at_least": 8}}, "trainers": {}},
}
LEGS5 = [("L1", "ch1_pokedex", 330000), ("L2", "ch2_wally", 330000), ("L3", "ch3_rustboro", 600000),
         ("L4", "ch4_roxanne", 900000), ("L5", "ch5_rival_meet", 600000)]
TID = 4242
_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="livechain_test_"))
# (the checker's hygiene note) a process that imports this module OUTSIDE unittest (a probe, a mutant worker) never runs
# tearDownModule, and its fake repository and batches (27 MB) were left in %TEMP%: the root is removed at exit as well
atexit.register(shutil.rmtree, _TEMP_ROOT, ignore_errors=True)


def tearDownModule() -> None:
    shutil.rmtree(_TEMP_ROOT, ignore_errors=True)
    now = ledger.LEDGER.read_bytes() if ledger.LEDGER.is_file() else None
    if now != LEDGER_AT_START:
        raise AssertionError("the REAL ledger.json changed while test_live_chain ran: a test forgot its temp ledger")


# ---------------------------------------------------------------------------------------------------- small helpers
def ok(condition, message: str = "assertion") -> None:
    if not condition:
        raise AssertionError(message)


def eq(a, b, message: str = "") -> None:
    if a != b:
        raise AssertionError(f"{message}: {a!r} != {b!r}")


def refused(M, fn, *args, **kwargs) -> str:
    """The Refusal's message; an AssertionError when the call is not refused or raises anything else."""
    try:
        fn(*args, **kwargs)
    except M.Refusal as error:
        return str(error)
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"raised {type(error).__name__}: {error}, not a Refusal") from None
    raise AssertionError(f"{getattr(fn, '__name__', fn)} was not refused")


def by_id(checks, check_id):
    return next(c for c in checks if c.id == check_id)


def ms(mid: str, chapter: int, flags=None, variables=None, trainers=None, optional=False, waypoint=None) -> dict:
    return {"id": mid, "chapter": chapter, "optional": optional, "waypoint": waypoint,
            "done": {"flags": flags or {}, "variables": variables or {}, "trainers": trainers or {}}}


def real_milestones() -> dict:
    return LC.load_milestones(REPO)


def snapshot(maps: int, tiles: int, warps: int = 1, connections: int = 1, transitions: int = 2) -> str:
    """One world.jsonl line as the AI writes it (WorldMemory.snapshot's shape, small)."""
    return json.dumps({"maps": {f"0:{i}": {"key": f"0:{i}", "name": f"MAP{i}", "visits": {"1,1": 1}} for i in range(maps)},
                       "warps": {f"{i}:1": {"to": "0:1"} for i in range(warps)},
                       "connections": [{"from": "0:0", "to": f"0:{i}"} for i in range(connections)],
                       "transitions": [[100 + i, "0:0", "0:1", "warp", "ai", [1, 1], [2, 2], None] for i in range(transitions)],
                       "tiles_learned": tiles}, separators=(",", ":"))


def held_marks(proof: dict) -> dict:
    marks = {name: 1 for name in proof["flags"]}
    marks.update({f"VAR_{name}": info["at_least"] for name, info in proof["variables"].items()})
    marks.update({f"TRAINER_{name}": 1 for name in proof["trainers"]})
    return marks


def unheld_marks(proof: dict) -> dict:
    marks = {name: 0 for name in proof["flags"]}
    marks.update({f"VAR_{name}": info["at_least"] - 1 for name, info in proof["variables"].items()})
    marks.update({f"TRAINER_{name}": 0 for name in proof["trainers"]})
    return marks


# ---------------------------------------------------------------------------------------------------- the stub launcher
class Stub:
    """A fake `live_step5.run_arm`: plants a run folder as run_arm leaves it (actions.jsonl, ai_player.log with the AI's
    memory line, a 3-snapshot world.jsonl, end_state.ss1) and returns a `live_step5.Run` with the truths it controls. The
    start truth of a leg is the truth this stub gave the state it is handed (as `truth_of` would read it). `plan[leg]`
    plants a fault: miss, stale, truncate, no_world, overshoot, unread_start, amnesia, wrong_counts, multichoice=N,
    write_stop, write_abort, raise, die, wrong_species, wrong_ot, dead (the launch dies before playing a frame, as the
    verifier's live V1 did: the gate line, exit code 1, no verdict file, no log, no world file, no end state); (the third fix
    round, C3-E02: the AI's output is untrusted) wrong_type_last_line (the world.jsonl's last line is valid JSON with
    "maps" a number), deep_line (a 100,000-deep MIDDLE line; the last line is a good snapshot), bad_verdict (the verdict
    file's real_frames is text and its exit_reason a number; one actions.jsonl record is no JSON object); (the fourth fix
    round) world_is_folder (C4-E01: world.jsonl is a FOLDER), lone_surrogate (C4-E04: the exit_reason holds a lone
    surrogate, which no UTF-8 write takes), die_before_launch (C4-G04: the chain process dies after naming the leg and
    before its launch makes a run folder)."""

    def __init__(self, job: dict, plan: dict | None = None) -> None:
        self.job = job
        self.plan = plan or {}
        self.calls: list[str] = []
        self.truths: dict[str, dict] = {}
        self.last_lines: dict[str, bytes] = {}
        self.marks: dict = {}
        self.stamp = 0
        self.proofs = {leg["target"]: leg["proof"] for leg in job["legs"]}
        self.order = [leg["target"] for leg in job["legs"]]

    def __call__(self, arm, build_root: Path, carried: dict):
        self.calls.append(arm.name)
        leg = arm.name.rsplit("-", 1)[1]
        plan = self.plan.get(leg, {})
        if plan.get("die_before_launch"):
            raise SystemExit("the child process died before its launch")
        target = arm.env[ENV_TARGET]
        run = L5.Run(arm)
        profile = Path(build_root) / "profiles" / L5.PROFILE
        self.stamp += 1
        run.run_dir = profile / "ai_player_runs" / f"20261105-{self.stamp:06d}-{arm.name}"
        run.run_dir.mkdir(parents=True)
        start = ["--fresh"]
        world_in = None
        if arm.state_from is not None:
            state, world, earlier = carried[arm.state_from]
            run.earlier = [r for r in earlier if r.get("decision") == "read"]
            run.world_in, run.start_state = world, state
            world_in = Path(world)
            start = ["--state", str(state)]
            run.before = None if plan.get("unread_start") else copy.deepcopy(self.truths.get(str(state)))
        run.command = ["py", "-m", "ai_player", "run", "--profile", L5.PROFILE, "--frames", str(arm.frames),
                       "--run-dir", str(run.run_dir), *start]
        run.started = time.time()
        if plan.get("dead"):
            run.stdout = f"[AI-GATE] exit=0 verdict=PASS package={L2.REPO / 'ai_player'}\n"
            run.exit_code, run.elapsed, run.verdict, run.after, run.state_mtime = 1, 3.8, None, None, None
            run.measures["harness_stop"] = L5.harness_stop(run)
            return run
        frames = 1000 + self.stamp
        # the AI's log: its pad outcome line, its memory line, any unexpected lines
        counts = None
        if world_in is not None and world_in.is_file() and not plan.get("amnesia"):
            last = [ln for ln in world_in.read_bytes().splitlines() if ln.strip()][-1]
            data = json.loads(last)
            counts = [len(data["maps"]), data["tiles_learned"], len(data["warps"]), len(data["connections"]),
                      len(data["transitions"])]
            if plan.get("wrong_counts"):
                counts[0] += 1
            memory = (f"[AI-WORLD] memory from the last snapshot of {world_in}: {counts[0]} maps (MAP0 1 tiles 0 bumped), "
                      f"{counts[1]} tiles learned, {counts[2]} warp links, {counts[3]} connections, {counts[4]} map changes; "
                      f"goal -; personality {self.job['personality']}")
        else:
            memory = ("[AI-WORLD] memory from nothing (a new memory): 0 maps (none), 0 tiles learned, 0 warp links, 0 "
                      f"connections, 0 map changes; goal -; personality {self.job['personality']}")
        log = [f"[AI-HANDS] outcome=done presses=10 frames={frames}", memory]
        log += ["[AI-HANDS] [AI-GOALS] goal go not done: stuck: an unexpected multichoice on screen"] * plan.get("multichoice", 0)
        run.ai_log = "\n".join(log) + "\n"
        (run.run_dir / "ai_player.log").write_text(run.ai_log, encoding="utf-8")
        run.records = [{"decision": "read", "frame": 1, "reason": f"a page of {arm.name}"}]
        (run.run_dir / "actions.jsonl").write_text(json.dumps(run.records[0]) + "\n", encoding="utf-8")
        # the world memory it leaves: grows from the one it was handed
        base = counts or [0, 0, 0, 0, 0]
        if not plan.get("no_world"):
            lines = [snapshot(base[0] + k, base[1] + 100 * k, base[2] + k, base[3] + 1, base[4] + 2 * k) for k in (1, 2, 3)]
            body = "\n".join(lines) + "\n\n"
            if plan.get("truncate"):
                body = "\n".join(lines[:2] + [lines[2][: len(lines[2]) // 2]]) + "\n"
            if plan.get("deep_line"):  # (C3-E02) json.loads raises RecursionError on it, not ValueError
                body = "\n".join([lines[0], "[" * 100000 + "]" * 100000, *lines[1:]]) + "\n"
            if plan.get("wrong_type_last_line"):  # (C3-E02) parses, but len() of its "maps" raises TypeError
                body = "\n".join([*lines, '{"maps": 3, "tiles_learned": 0, "warps": {}, "connections": [], '
                                          '"transitions": []}']) + "\n"
            if plan.get("world_is_folder"):  # (C4-E01) a world.jsonl of the wrong KIND: open() refuses a folder
                (run.run_dir / "world.jsonl").mkdir()
                (run.run_dir / "world.jsonl" / "inside.txt").write_bytes(body.encode("utf-8"))
            else:
                (run.run_dir / "world.jsonl").write_bytes(body.encode("utf-8"))
            self.last_lines[arm.name] = (lines[2] + "\n").encode("utf-8")
        if plan.get("write_stop"):
            (Path(self.job["out"]) / "STOP.txt").write_text("moved\n", encoding="utf-8")
        if plan.get("write_abort"):
            (Path(self.job["out"]) / "ABORT.txt").write_text("under 30 GB free\n", encoding="utf-8")
        if plan.get("raise"):
            raise RuntimeError("the launcher could not start")
        if plan.get("die"):
            raise SystemExit("the child process died")
        # the end state and its truth
        end = run.run_dir / "end_state.ss1"
        end.write_bytes(f"{arm.name}-{self.stamp}".encode())
        if not plan.get("miss"):
            self.marks.update(held_marks(self.proofs[target]))
            if plan.get("overshoot") and self.order.index(target) + 1 < len(self.order):
                self.marks.update(held_marks(self.proofs[self.order[self.order.index(target) + 1]]))
        marks = {**{k: v for t in self.order for k, v in unheld_marks(self.proofs[t]).items()}, **self.marks}
        start_frame = (run.before or {}).get("frame") or 0
        if arm.state_from is None:
            species = "Torchic" if plan.get("wrong_species") else arm.env[ENV_STARTER].title()
            self.party = ([["0000beef", species, 100, 5]], [["0000beef", 1 if plan.get("wrong_ot") else TID]])
        run.after = {"frame": start_frame + frames, "map": [0, 1], "state_md5": hashlib.md5(end.read_bytes()).hexdigest(),
                     "story": {"marks": marks, "stats": {}}, "party_exp": self.party[0], "party_ot": self.party[1],
                     "player_tid": TID}
        self.truths[str(end)] = copy.deepcopy(run.after)
        run.state_mtime = run.started - 100.0 if plan.get("stale") else run.started + 1.0
        reached = not plan.get("miss")
        run.verdict = {"verdict": "CLEAN", "counters": {"ai_presses": 20, "real_frames": frames,
                                                        **{k: 0 for k in L2.BREACH_COUNTERS}},
                       "facts": {"exit_code": 0, "exit_reason": f"play: done: {target} reached" if reached else
                                 "play: stuck: out of ideas", "package_root": str(L2.REPO)}}
        if plan.get("bad_verdict"):  # (C3-E02) the AI process's verdict file and action log, of the wrong shape
            run.verdict["counters"]["real_frames"] = "lots"
            run.verdict["facts"]["exit_reason"] = 7
            run.records.append([1, 2, 3])
        if plan.get("lone_surrogate"):  # (C4-E04) valid JSON text ("\ud800") that no UTF-8 write takes
            run.verdict["facts"]["exit_reason"] = json.loads('"play: done \\ud800"')
        run.stdout = f"[AI-GATE] exit=0 verdict=PASS package={L2.REPO / 'ai_player'}\n"
        run.exit_code = 0
        run.elapsed = 12.5
        run.measures["harness_stop"] = L5.harness_stop(run)
        if (run.run_dir / "world.jsonl").is_file():
            carried[arm.name] = (end, run.run_dir / "world.jsonl", run.earlier + run.records)
        return run


def chain_job(tmp: Path, to: str = "ch5_rival_meet", seed: int = 7001, pair: str = "S", out: Path | None = None,
              build: Path | None = None) -> dict:
    pairs = {p[0]: p for p in LC.PAIRS}
    return {"chain": f"LC-{pair}-{seed}", "pair": pair, "personality": pairs[pair][1], "starter": pairs[pair][2],
            "seed": seed, "profile": f"{LC.PROFILE_PREFIX}{seed}", "legs": LC.legs_of(to, real_milestones()),
            "out": str(out or tmp / "out"), "build_root": str(build or tmp / "build")}


def play(M, tmp: Path, plan: dict | None = None, job: dict | None = None, profile: str | None = None, pre=None):
    """One chain through `M.run_chain` with a stub; `live_step5.PROFILE` restored after (critic CH-05)."""
    job = job or chain_job(tmp)
    stub = Stub(job, plan)
    saved = L5.PROFILE
    L5.PROFILE = job["profile"] if profile is None else profile
    try:
        if pre is not None:
            pre(job)
        chain = M.run_chain(job, stub)
    finally:
        L5.PROFILE = saved
    return chain, stub, job


_BATCH: dict = {}


def healthy_batch(n: int = 6, plans: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Six (or n) chains' rows made by the REAL run_chain with the stub (cached; a deep copy each call), and their jobs."""
    key = (n, json.dumps(plans or {}, sort_keys=True))
    if key not in _BATCH:
        root = Path(tempfile.mkdtemp(prefix="batch_", dir=_TEMP_ROOT))
        jobs = LC.jobs_of(7101, 6)[:n]
        chains = []
        for job in jobs:
            full = {**job, "legs": LC.legs_of("ch5_rival_meet", real_milestones()), "out": str(root / "out"),
                    "build_root": str(root / "build")}
            chain, _, _ = play(LC, root, (plans or {}).get(job["chain"]), full)
            chains.append(chain)
        _BATCH[key] = (chains, LC.jobs_of(7101, 6))
    chains, jobs = _BATCH[key]
    return copy.deepcopy(chains), copy.deepcopy(jobs)


def grade(M, chains, jobs, reach_min: int = 5, frozen=(True, "ok"), leftover=()):
    """The batch grade as `run_batch` calls it: against the REGISTERED legs (V-02: every leg re-derived from its row)."""
    return M.grade_batch(chains, jobs, 5, reach_min, frozen, list(leftover), {"most_running": 3},
                         legs=LC.legs_of("ch5_rival_meet", real_milestones()))


def graded_ok(checks) -> dict:
    return {c.id: c.status for c in checks if c.kind == "GRADED"}


# ==================================================================================================== THE CASES
# ---------------------------------------------------------------------------------------------------- legs
def case_legs_real(M, tmp):
    legs = M.legs_of("ch5_rival_meet", real_milestones())
    eq([(leg["leg"], leg["target"], leg["frames"]) for leg in legs], LEGS5, "the legs of ch5_rival_meet")
    eq({leg["target"]: leg["proof"] for leg in legs}, DECOMP_PROOFS, "the proofs against the pinned decomp")


def case_legs_short(M, tmp):
    eq([leg["target"] for leg in M.legs_of("ch2_wally", real_milestones())], ["ch1_pokedex", "ch2_wally"], "ch2_wally")
    eq([leg["target"] for leg in M.legs_of("ch3_woods", real_milestones())], ["ch1_pokedex", "ch2_wally", "ch3_woods"],
       "ch3_woods")


SYNTH = {"milestones": [ms("a1", 1, {"F1": 1}), ms("a2", 1, {"F2": 2}),
                        ms("b1", 2, {"F4": 4}), ms("b_opt", 2, trainers={"T": 1300}, optional=True),
                        ms("c1", 3, {"F5": 5}), ms("c_wp", 3, {"F6": 6}, waypoint="ROUTE"),
                        ms("d1", 4, variables={"V": {"number": 16400, "at_least": 3}})]}


def case_synthetic_optional_end(M, tmp):
    legs = M.legs_of("d1", SYNTH, {1: 10, 2: 20, 3: 30, 4: 40})
    eq(legs[1]["target"], "b1", "chapter 2 ends at its last NON-optional milestone")


def case_waypoint_skipped(M, tmp):
    legs = M.legs_of("d1", SYNTH, {1: 10, 2: 20, 3: 30, 4: 40})
    eq(legs[2]["target"], "c1", "chapter 3's waypoint is skipped")
    eq([leg["frames"] for leg in legs], [10, 20, 30, 40], "each chapter's own budget")


def case_refused_targets(M, tmp):
    data = real_milestones()
    ok("no milestone" in refused(M, M.legs_of, "ch9_nowhere", data), "unknown")
    ok("OPTIONAL" in refused(M, M.legs_of, "ch5_rival_battle", data), "ch5_rival_battle is optional")
    ok("OPTIONAL" in refused(M, M.legs_of, "ch4_gym_trainers", data), "ch4_gym_trainers is optional")
    ok("WAYPOINT" in refused(M, M.legs_of, "ch2_route102", data), "ch2_route102 is a waypoint")


def case_no_budget(M, tmp):
    data = {"milestones": real_milestones()["milestones"] + [ms("ch6_x", 6, {"F": 1})]}
    ok("budget" in refused(M, M.legs_of, "ch6_x", data), "a chapter without a budget")


def case_backwards(M, tmp):
    data = {"milestones": [ms("a", 2, {"F": 1}), ms("b", 1, {"G": 2})]}
    ok("BACKWARDS" in refused(M, M.legs_of, "b", data), "chapters going backwards")


def case_empty_proof_refused(M, tmp):
    data = {"milestones": [ms("a", 1)]}
    ok("EMPTY" in refused(M, M.legs_of, "a", data), "an empty proof")


def case_leg_frames(M, tmp):
    legs = M.legs_of("ch2_wally", real_milestones())
    eq(M.parse_leg_frames("L1=30000", legs), {"L1": 30000}, "an override")
    eq(M.parse_leg_frames(None, legs), {}, "none")
    for bad in ("L9=1", "L1=0", "L1=x"):
        refused(M, M.parse_leg_frames, bad, legs)


# ---------------------------------------------------------------------------------------------------- proofs
P_FLAGS = {"flags": {"A": 1, "B": 2}, "variables": {}, "trainers": {}}
P_VAR = {"flags": {}, "variables": {"RUSTBORO_CITY_STATE": {"number": 16474, "at_least": 8}}, "trainers": {}}


def case_proof_flags(M, tmp):
    ok(M.proof_holds({"A": 1, "B": 1}, P_FLAGS)["held"], "all flags 1 hold")
    ok(not M.proof_holds({"A": 1, "B": 0}, P_FLAGS)["held"], "one flag 0 does not")


def case_var_boundary(M, tmp):
    ok(not M.proof_holds({"VAR_RUSTBORO_CITY_STATE": 7}, P_VAR)["held"], "VAR 7 does not hold")
    ok(M.proof_holds({"VAR_RUSTBORO_CITY_STATE": 8}, P_VAR)["held"], "VAR 8 holds")


def case_missing_key(M, tmp):
    found = M.proof_holds({"A": 1}, P_FLAGS)
    ok(not found["held"], "a missing key is not held")
    eq(found["missing"], ["B"], "it is listed as missing")
    ok(not M.proof_holds(None, P_VAR)["held"], "no marks at all hold nothing")


def case_trainer_flag(M, tmp):
    proof = {"flags": {}, "variables": {}, "trainers": {"GRUNT": 1296}}
    ok(M.proof_holds({"TRAINER_GRUNT": 1}, proof)["held"], "a defeated trainer holds")
    ok(not M.proof_holds({"TRAINER_GRUNT": 0}, proof)["held"], "an undefeated one does not")


def case_empty_proof_never_holds(M, tmp):
    ok(not M.proof_holds({"A": 1}, {"flags": {}, "variables": {}, "trainers": {}})["held"], "an empty proof")


# ---------------------------------------------------------------------------------------------------- the continuation rule
def base_row(tmp: Path, **changes) -> dict:
    kept = tmp / "kept" / "world_last.jsonl"
    kept.parent.mkdir(parents=True, exist_ok=True)
    kept.write_text(snapshot(2, 10) + "\n", encoding="utf-8")
    checks = [{"id": i, "kind": "GRADED", "status": "PASS"} for i in PURITY_SIX]
    checks += [{"id": "L5.PURITY_ENDED", "kind": "REPORTED", "status": "FAIL"},
               {"id": "L5.THIS_RUN", "kind": "GRADED", "status": "PASS"}]
    row = {"chain": "LC-S-1", "leg": "L2", "target": "ch2_wally", "status": "RAN", "checks": checks,
           "proof_after": {"held": True, "missing": [], "failing": [], "values": {"VAR_PETALBURG_GYM_STATE": 2}},
           "world_file": {"bytes": 5000, "deleted": True, "present": True},
           "measures": {"world": {"last_ok": True, "lines": 3, "bad_lines": 0}}, "kept_world": str(kept),
           "guard_killed": None, "custody": []}
    row.update(changes)
    return row


def stops(M, row, stop_seen=False, needle=""):
    go, why = M.continue_after(row, stop_seen)
    ok(not go, f"the chain should STOP ({needle}): {why}")
    ok(needle in why, f"the reason names {needle!r}: {why}")
    return why


def case_continue_control(M, tmp):
    go, why = M.continue_after(base_row(tmp), False)
    ok(go, f"every condition holds: {why}")


def case_continue_c1_proof(M, tmp):
    row = base_row(tmp, proof_after={"held": False, "missing": [], "failing": ["VAR_PETALBURG_GYM_STATE"],
                                     "values": {"VAR_PETALBURG_GYM_STATE": 1}})
    why = stops(M, row, needle="C1 ")
    ok("'VAR_PETALBURG_GYM_STATE': 1" in why, f"both values: {why}")


def case_continue_c1_this_run(M, tmp):
    row = base_row(tmp)
    next(c for c in row["checks"] if c["id"] == "L5.THIS_RUN")["status"] = "FAIL"
    ok("L5.THIS_RUN FAIL" in stops(M, row, needle="C1 "), "the stale state named")


def case_continue_c2(M, tmp):
    for check_id in PURITY_SIX:
        row = base_row(tmp)
        next(c for c in row["checks"] if c["id"] == check_id)["status"] = "FAIL"
        ok(f"{check_id} FAIL" in stops(M, row, needle="C2 "), f"{check_id} alone stops")


def case_continue_c3_at_cap(M, tmp):
    why = stops(M, base_row(tmp, world_file={"bytes": 300_000_000, "deleted": True}), needle="C3 ")
    ok("300000000" in why, why)
    go, _ = M.continue_after(base_row(tmp, world_file={"bytes": 299_999_999, "deleted": True}), False)
    ok(go, "299,999,999 bytes continue")


def case_continue_c3_unmeasured(M, tmp):
    stops(M, base_row(tmp, world_file={"bytes": None, "deleted": False}), needle="C3 ")


def case_continue_c3_last_line(M, tmp):
    stops(M, base_row(tmp, measures={"world": {"last_ok": False, "lines": 3, "bad_lines": 1}}), needle="C3 ")
    stops(M, base_row(tmp, kept_world=str(tmp / "nowhere.jsonl")), needle="C3 ")


def case_continue_c4(M, tmp):
    stops(M, base_row(tmp, guard_killed={"cause": "world", "text": "killed at 1.6 GB"}), needle="C4 ")


def case_continue_c5(M, tmp):
    stops(M, base_row(tmp, custody=["L2's start truth is not L1's end truth"]), needle="C5 ")


def case_continue_c6(M, tmp):
    stops(M, base_row(tmp), stop_seen=True, needle="C6 ")


def case_deletion_failure_continues(M, tmp):
    go, why = M.continue_after(base_row(tmp, world_file={"bytes": 5000, "deleted": False, "present": True}), False)
    ok(go, f"a world.jsonl the OS kept open is no stop (critic CH-03): {why}")


# ---------------------------------------------------------------------------------------------------- custody (pure)
#: (the third fix round, C3-G01) a complete registered job: every leg row below names it in its own records, so each FAULT
#: case adds exactly its own problem and the CONTROL reads []
JOB_S = {"chain": "LC-S-1", "starter": "TREECKO", "seed": 1, "personality": "Story", "profile": "ai-livechain-1"}
RUNS_S = "C:/b/sandbox-pokebot/profiles/ai-livechain-1/ai_player_runs"
IDENTITY_ENV = {"AI_PLAYER_SEED": "1", "AI_PLAYER_PERSONALITY": "Story"}


def l1_row(**changes) -> dict:
    row = {"leg": "L1", "arm": "LC-S-1-L1", "command": ["py", "run", "--profile", "ai-livechain-1", "--fresh"],
           "env": {ENV_STARTER: "TREECKO", **IDENTITY_ENV}, "env_keys": list(LC.ENV_KEYS_FIRST), "world_in": None,
           "truth_before": None, "run_dir": f"{RUNS_S}/r1", "truth_after": {"frame": 500, "state_md5": "m1"},
           "kept_world": "C:/out/L1/world_last.jsonl", "kept_world_sha256": "s1"}
    row.update(changes)
    return row


def l2_row(**changes) -> dict:
    row = {"leg": "L2", "arm": "LC-S-1-L2",
           "command": ["py", "run", "--profile", "ai-livechain-1", "--state", str(Path(f"{RUNS_S}/r1") / "end_state.ss1")],
           "env": dict(IDENTITY_ENV), "env_keys": list(LC.ENV_KEYS_LATER), "world_in": "C:/out/L1/world_last.jsonl",
           "world_in_sha256": "s1", "truth_before": {"frame": 500, "state_md5": "m1"}, "run_dir": f"{RUNS_S}/r2"}
    row.update(changes)
    return row


def case_custody_control(M, tmp):
    eq(M.custody_problems(l1_row(), None, JOB_S, 0), [], "L1")
    eq(M.custody_problems(l2_row(), l1_row(), JOB_S, 1), [], "L2")


def case_custody_wrong_md5(M, tmp):
    ok(M.custody_problems(l2_row(truth_before={"frame": 500, "state_md5": "OTHER"}), l1_row(), JOB_S, 1), "md5")


def case_custody_wrong_frame(M, tmp):
    ok(M.custody_problems(l2_row(truth_before={"frame": 501, "state_md5": "m1"}), l1_row(), JOB_S, 1), "frame")


def case_custody_wrong_state(M, tmp):
    ok(M.custody_problems(l2_row(command=["py", "run", "--profile", "ai-livechain-1", "--state", "C:/other/end_state.ss1"]),
                          l1_row(), JOB_S, 1), "state")


def case_custody_wrong_world_sha(M, tmp):
    ok(M.custody_problems(l2_row(world_in_sha256="s2"), l1_row(), JOB_S, 1), "world sha")
    ok(M.custody_problems(l2_row(world_in_sha256=None), l1_row(kept_world_sha256=None), JOB_S, 1), "no sha either side")


def case_custody_wrong_world_path(M, tmp):
    ok(M.custody_problems(l2_row(world_in=f"{RUNS_S}/r1/world.jsonl"), l1_row(), JOB_S, 1), "the original world.jsonl")


def case_custody_l1_state(M, tmp):
    ok(M.custody_problems(l1_row(command=["py", "run", "--profile", "ai-livechain-1", "--fresh", "--state", "C:/s.ss1"]),
                          None, JOB_S, 0), "--state")
    ok(M.custody_problems(l1_row(command=["py", "run", "--profile", "ai-livechain-1"]), None, JOB_S, 0), "no --fresh")


def case_custody_l1_world(M, tmp):
    ok(M.custody_problems(l1_row(world_in="C:/w.jsonl"), None, JOB_S, 0), "L1 with a world")
    ok(M.custody_problems(l1_row(truth_before={"frame": 1}), None, JOB_S, 0), "L1 with a start truth")


def case_custody_l1_starter(M, tmp):
    ok(M.custody_problems(l1_row(env={ENV_STARTER: "MUDKIP", **IDENTITY_ENV}), None, JOB_S, 0), "another starter")


def case_custody_env_keys(M, tmp):
    ok(M.custody_problems(l2_row(env_keys=list(LC.ENV_KEYS_LATER) + ["AI_PLAYER_FAULT_X"]), l1_row(), JOB_S, 1), "L2 key")
    ok(M.custody_problems(l1_row(env_keys=list(LC.ENV_KEYS_FIRST) + ["AI_PLAYER_FAULT_X"]), None, JOB_S, 0), "L1 key")


def case_custody_unread_start(M, tmp):
    found = M.custody_problems(l2_row(truth_before=None), l1_row(), JOB_S, 1)
    ok(any("UNREAD" in p for p in found), f"an unread start truth is UNREAD (N7): {found}")


# ---------------------------------------------------------------------------------------------------- one chain
def case_chain_control(M, tmp):
    chain, stub, job = play(M, tmp)
    eq([leg["status"] for leg in chain["legs"]], ["RAN"] * 5, "five legs ran")
    eq(stub.calls, [f"{job['chain']}-L{k}" for k in range(1, 6)], "five launches")
    ok(chain["reached_to"] and M.chain_reaches(chain, 5), "the chain reaches")
    for at, leg in enumerate(chain["legs"]):
        ok(leg["continue"], f"{leg['leg']} continues: {leg['why']}")
        eq(leg["custody"], [], f"{leg['leg']} custody")
        ok(not (Path(leg["run_dir"]) / "world.jsonl").exists(), f"{leg['leg']}'s world.jsonl DELETED")
        eq((leg["world_file"] or {}).get("deleted"), True, f"{leg['leg']} deleted")
        kept = Path(leg["kept_world"])
        eq(kept.read_bytes(), stub.last_lines[leg["arm"]], f"{leg['leg']} kept the LAST non-blank line, byte for byte")
        if at:
            prev = chain["legs"][at - 1]
            eq(leg["world_in"], prev["kept_world"], f"{leg['leg']}'s AI_PLAYER_WORLD is {prev['leg']}'s kept line")
            eq(leg["world_in_sha256"], prev["kept_world_sha256"], f"{leg['leg']}'s world sha")
            ok(str(Path(prev["run_dir"]) / "end_state.ss1") in leg["command"], f"{leg['leg']} from {prev['leg']}'s state")
            eq(sorted(leg["env_keys"]), sorted(LC.ENV_KEYS_LATER), f"{leg['leg']} env keys")
            ok(ENV_STARTER not in leg["env"], f"{leg['leg']} has no starter")
        else:
            eq(sorted(leg["env_keys"]), sorted(LC.ENV_KEYS_FIRST), "L1 env keys")
            eq(leg["env"][ENV_STARTER], "TREECKO", "L1's starter")
        ok(not [k for k in leg["env"] if "FAULT" in k], "no fault switch")
    rows = json.loads((Path(job["out"]) / "rows" / f"{job['chain']}.json").read_text(encoding="utf-8"))
    eq(len(rows["legs"]), 5, "the chain row on disk")


def case_chain_stops_on_miss(M, tmp):
    chain, stub, job = play(M, tmp, {"L2": {"miss": True}})
    eq(len(stub.calls), 2, "the stub was called exactly twice")
    eq([leg["status"] for leg in chain["legs"]], ["RAN", "RAN", "NOT RUN", "NOT RUN", "NOT RUN"], "L3-L5 NOT RUN")
    for leg in chain["legs"][2:]:
        ok("L2" in leg["reason"] and "C1 " in leg["reason"], f"the reason names L2 and C1: {leg['reason']}")
    eq(chain["stopped_at"], "L2", "stopped at L2")
    ok(not chain["reached_to"], "it does not reach")


def case_chain_stale_stops(M, tmp):
    chain, stub, _ = play(M, tmp, {"L1": {"stale": True}})
    eq(len(stub.calls), 1, "one launch")
    ok("L5.THIS_RUN FAIL" in chain["legs"][1]["reason"], chain["legs"][1]["reason"])


def case_truncated_last_line(M, tmp):
    chain, stub, _ = play(M, tmp, {"L1": {"truncate": True}})
    eq(len(stub.calls), 1, "a truncated last line stops the chain")
    ok("C3 " in chain["legs"][0]["why"], chain["legs"][0]["why"])


def case_chain_killed_marker(M, tmp):
    def pre(job):
        LC._write_json(Path(job["out"]) / job["chain"] / "L3.KILLED.json", {"cause": "world", "text": "planted"})
    chain, stub, _ = play(M, tmp, pre=pre)
    eq(len(stub.calls), 3, "stops after L3")
    ok("C4 " in chain["legs"][2]["why"], chain["legs"][2]["why"])


def case_stop_before_chain(M, tmp):
    def pre(job):
        Path(job["out"]).mkdir(parents=True, exist_ok=True)
        (Path(job["out"]) / "STOP.txt").write_text("moved\n", encoding="utf-8")
    chain, stub, _ = play(M, tmp, pre=pre)
    eq(stub.calls, [], "no leg launched")
    eq([leg["status"] for leg in chain["legs"]], ["NOT RUN"] * 5, "all NOT RUN")
    ok("changed mid-batch" in chain["legs"][0]["reason"], chain["legs"][0]["reason"])


def case_stop_during_leg(M, tmp):
    chain, stub, _ = play(M, tmp, {"L1": {"write_stop": True}})
    eq(len(stub.calls), 1, "STOP.txt seen at L1's end")
    ok("C6 " in chain["legs"][0]["why"] and not chain["legs"][0]["continue"], chain["legs"][0]["why"])


def case_world_over_cap(M, tmp):
    with mock.patch.object(M, "WORLD_MAX_BYTES", 500):
        chain, stub, _ = play(M, tmp)
    eq(len(stub.calls), 1, "a world over the cap stops the chain")
    ok("C3 " in chain["legs"][0]["why"] and "500" in chain["legs"][0]["why"], chain["legs"][0]["why"])


def case_deletion_failure_chain(M, tmp):
    def held_open(path):
        return {"bytes": path.stat().st_size, "deleted": False, "present": True}
    with mock.patch.object(M, "measure_then_delete", held_open):
        chain, stub, _ = play(M, tmp)
    eq(len(stub.calls), 5, "a failed deletion does not stop the chain (CH-03)")
    ok(chain["reached_to"], "it reaches")
    ok(any("could not be DELETED" in n for n in chain["legs"][0]["notes"]), chain["legs"][0]["notes"])


def case_overshoot_reaches(M, tmp):
    chain, stub, _ = play(M, tmp, {"L1": {"overshoot": True}})
    eq(len(stub.calls), 5, "an overshoot does not stop the chain (CH-12)")
    eq(chain["legs"][1]["already_held"], True, "L2 is marked ALREADY HELD")
    ok(chain["reached_to"], "the chain reaches")


def case_unread_start_stops(M, tmp):
    chain, stub, _ = play(M, tmp, {"L2": {"unread_start": True}})
    eq(len(stub.calls), 2, "an unread start truth stops at L2")
    ok("UNREAD" in chain["legs"][1]["why"], chain["legs"][1]["why"])
    eq((chain["legs"][1]["proof_before"] or {}).get("unread"), True, "proof_before UNREAD (N7)")


def case_profile_guard(M, tmp):
    for profile in (LC.MAIN_PROFILE, "some-other-profile"):
        chain, stub, _ = play(M, tmp / profile, profile=profile)
        eq(stub.calls, [], f"no launch with live_step5.PROFILE {profile}")
        eq([leg["status"] for leg in chain["legs"]], ["REFUSED"] * 5, "REFUSED rows")
    job = {**chain_job(tmp / "np"), "profile": "noprefix-7001"}
    chain, stub, _ = play(M, tmp / "np", job=job)
    eq(stub.calls, [], "a profile without the prefix")


def case_leg_error_salvaged(M, tmp):
    chain, stub, _ = play(M, tmp, {"L2": {"raise": True}})
    eq([leg["status"] for leg in chain["legs"]], ["RAN", "ERROR", "NOT RUN", "NOT RUN", "NOT RUN"], "an ERROR row")
    leg = chain["legs"][1]
    ok(not (Path(leg["run_dir"]) / "world.jsonl").exists(), "its world.jsonl measured and deleted")
    ok(isinstance(leg["world_file"]["bytes"], int), "measured")
    eq(leg["checks"], [], "no checks: purity and freshness read it as not judged")


# ---------------------------------------------------------------------------------------------------- the grader
def stopped_batch(chain_index: int, plan: dict) -> tuple[list[dict], list[dict]]:
    jobs = LC.jobs_of(7101, 6)
    return healthy_batch(6, {jobs[chain_index]["chain"]: plan})


def case_grade_control(M, tmp):
    chains, jobs = healthy_batch()
    checks = grade(M, chains, jobs)
    eq(set(graded_ok(checks).values()), {"PASS"}, f"every graded check: {graded_ok(checks)}")
    eq(M.batch_verdict(checks), "PASS", "the verdict")


def case_reach_5_of_6_pass(M, tmp):
    """5 of 6 reach. (The fourth check's C4-G05) the MOST LIKELY honest graded outcome, one chain missing one leg, is a
    full GRADED PASS: every graded check PASSES, LC.CUSTODY included (the legs NOT RUN after the miss follow a leg that
    did NOT continue), whether the miss is at L1, L3 or L4. The check's mutant C05 (the rule fires after any RAN leg)
    turned exactly this into FAIL."""
    chains, jobs = stopped_batch(1, {"L3": {"miss": True}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "PASS", "5 of 6")
    ok(not M.chain_reaches(chains[1], 5), "the chain stopped at L3 does not reach")
    for at in ("L1", "L3", "L4"):
        chains, jobs = stopped_batch(1, {at: {"miss": True}})
        checks = grade(M, chains, jobs)
        eq((M.batch_verdict(checks), by_id(checks, "LC.CUSTODY").status), ("PASS", "PASS"),
           f"one miss at {at}: a full GRADED PASS: {graded_ok(checks)}")


def case_reach_4_of_6_fails(M, tmp):
    chains, jobs = healthy_batch(6, {LC.jobs_of(7101, 6)[1]["chain"]: {"L3": {"miss": True}},
                                     LC.jobs_of(7101, 6)[4]["chain"]: {"L1": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "FAIL", "4 of 6")


def case_reach_5_rows_vacuous(M, tmp):
    chains, jobs = healthy_batch()
    eq(by_id(grade(M, chains[:5], jobs), "LC.REACH").status, "VACUOUS", "5 chain rows of 6")


def case_not_run_never_reached(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][4] = LC.not_run_row(jobs[0] | {"legs": []}, {**chains[0]["legs"][4]}, "NOT RUN", "planted")
    ok(not M.chain_reaches(chains[0], 5), "a NOT RUN last leg never reaches")


def case_purity_middle_fail(M, tmp):
    chains, jobs = healthy_batch()
    next(c for c in chains[2]["legs"][2]["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
    eq(by_id(grade(M, chains, jobs), "LC.PURITY").status, "FAIL", "a middle leg not clean")


def case_each_purity_id_fails(M, tmp):
    for check_id in PURITY_SIX:
        chains, jobs = healthy_batch()
        next(c for c in chains[0]["legs"][1]["checks"] if c["id"] == check_id)["status"] = "FAIL"
        eq(by_id(grade(M, chains, jobs), "LC.PURITY").status, "FAIL", f"{check_id} alone")


def case_purity_stopped_chain_pass(M, tmp):
    chains, jobs = stopped_batch(0, {"L2": {"miss": True}})
    eq(by_id(grade(M, chains, jobs), "LC.PURITY").status, "PASS", "NOT RUN legs are no purity sample")
    eq(by_id(grade(M, chains, jobs), "LC.THIS_RUN").status, "PASS", "nor THIS_RUN samples")


def case_purity_salvaged_vacuous(M, tmp):
    chains, jobs = healthy_batch()
    leg = chains[3]["legs"][4]
    leg.update({"status": "SALVAGED", "checks": []})
    checks = grade(M, chains, jobs)
    eq(by_id(checks, "LC.PURITY").status, "VACUOUS", "a salvaged leg is not judged")
    eq(by_id(checks, "LC.THIS_RUN").status, "VACUOUS", "nor fresh")
    eq(M.batch_verdict(checks), "FAIL", "VACUOUS fails")


def case_stale_middle_leg_fails(M, tmp):
    chains, jobs = healthy_batch()
    next(c for c in chains[1]["legs"][1]["checks"] if c["id"] == "L5.THIS_RUN")["status"] = "FAIL"
    eq(by_id(grade(M, chains, jobs), "LC.THIS_RUN").status, "FAIL", "a stale middle leg")


def case_world_exactly_cap_fails(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][2]["world_file"]["bytes"] = 300_000_000
    eq(by_id(grade(M, chains, jobs), "LC.WORLD_SIZE").status, "FAIL", "exactly 300,000,000 is not under")
    chains[0]["legs"][2]["world_file"]["bytes"] = 299_999_999
    eq(by_id(grade(M, chains, jobs), "LC.WORLD_SIZE").status, "PASS", "299,999,999")
    chains[0]["legs"][2]["world_file"]["bytes"] = None
    eq(by_id(grade(M, chains, jobs), "LC.WORLD_SIZE").status, "VACUOUS", "a ran leg not measured")


def case_custody_grade_fail(M, tmp):
    chains, jobs = healthy_batch()
    chains[5]["legs"][3]["custody"] = ["L4's start truth is not L3's end truth"]
    eq(by_id(grade(M, chains, jobs), "LC.CUSTODY").status, "FAIL", "a custody problem")


def case_refused_chain_fails_custody(M, tmp):
    chains, jobs = healthy_batch()
    job = {**jobs[5], "legs": LC.legs_of("ch5_rival_meet", real_milestones())}
    refused_row = LC.new_chain_row(job)
    LC.stop_rest(job, refused_row, 0, "REFUSED: planted", status="REFUSED")
    chains[5] = refused_row
    checks = grade(M, chains, jobs)
    eq(by_id(checks, "LC.REACH").status, "PASS", "5 of 6 still reach")
    eq(by_id(checks, "LC.CUSTODY").status, "FAIL", "but a chain whose L1 never ran fails custody (CH-06)")
    eq(M.batch_verdict(checks), "FAIL", "and the batch")


def case_starter_wrong_species(M, tmp):
    chains, jobs = stopped_batch(2, {"L1": {"wrong_species": True}})
    eq(by_id(grade(M, chains, jobs), "LC.STARTER").status, "FAIL", "a wrong species")


def case_starter_wrong_ot(M, tmp):
    chains, jobs = stopped_batch(2, {"L1": {"wrong_ot": True}})
    eq(by_id(grade(M, chains, jobs), "LC.STARTER").status, "FAIL", "a wrong OT")


def case_memory_counts(M, tmp):
    chains, jobs = stopped_batch(3, {"L3": {"wrong_counts": True}})
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "FAIL", "the AI's counts differ from the kept line")


def case_memory_amnesia(M, tmp):
    chains, jobs = stopped_batch(3, {"L2": {"amnesia": True}})
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "FAIL", "a leg that loaded nothing")


def case_memory_l1_not_new(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][0]["measures"]["log"]["memory"]["new"] = False
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "FAIL", "L1 said it loaded a memory")


def case_memory_missing_vacuous(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][1]["measures"]["log"]["memory"] = None
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "VACUOUS", "no memory line")


def case_memory_path(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][2]["measures"]["log"]["memory"]["path"] = "C:/somewhere/else/world.jsonl"
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "FAIL", "the right counts from another file")


def case_last_leg_must_continue(M, tmp):
    chains, _ = healthy_batch()
    ok(M.chain_reaches(chains[0], 5), "control")
    last = copy.deepcopy(chains[0])
    last["legs"][4]["continue"] = False
    ok(not M.chain_reaches(last, 5), "a last leg that failed C1-C6 (e.g. purity) does not reach (N2)")
    short = copy.deepcopy(chains[0])
    short["legs"] = short["legs"][:4]
    ok(not M.chain_reaches(short, 5), "four legs of five never reach")


def case_frozen_leftover(M, tmp):
    chains, jobs = healthy_batch()
    eq(M.batch_verdict(grade(M, chains, jobs, frozen=(False, "moved"))), "FAIL", "a frozen-tree move")
    eq(M.batch_verdict(grade(M, chains, jobs, leftover=["123 x"])), "FAIL", "a leftover process")
    eq(M.batch_verdict(grade(M, chains, jobs)), "PASS", "control")


def case_reported_never_counts(M, tmp):
    chains, jobs = healthy_batch()
    chains[1]["legs"][2]["measures"]["log"]["multichoice"] = 30000
    chains[2]["legs"][3]["outcome"] = "play: stuck: out of ideas"
    checks = M.grade_batch(chains, jobs, 5, 5, (True, "ok"), [],
                           {"profiles": {"problems": ["planted"], "text": "planted"}, "most_running": 3,
                            "optional": {"LC-S-1": {"ch5_rival_battle": False}}})
    eq(by_id(checks, "LC.MULTICHOICE").status, "FAIL", "30,000 multichoice lines read FAIL in their own line")
    eq(by_id(checks, "LC.MULTICHOICE").kind, "REPORTED", "REPORTED")
    eq(by_id(checks, "LC.OUTCOME").status, "FAIL", "an outcome DISAGREE")
    eq(by_id(checks, "LC.PROFILES").status, "FAIL", "a profiles problem")
    eq(M.batch_verdict(checks), "PASS", "REPORTED never counts")


def case_quotes(M, tmp):
    chains, jobs = healthy_batch()
    checks = grade(M, chains, jobs)
    ok("at least 5 of 6" in by_id(checks, "LC.REACH").text, by_id(checks, "LC.REACH").text)
    ok("300000000" in by_id(checks, "LC.WORLD_SIZE").text, "the cap quoted")
    lines = M.check_lines(checks)
    ok(any(line.startswith("B1 DEBT LC.MEMORY") for line in lines), "LC.MEMORY declared as B1 debt")


# ---------------------------------------------------------------------------------------------------- disk
def case_measure_301mb(M, tmp):
    path = tmp / "world.jsonl"
    with open(path, "wb") as handle:
        handle.truncate(301_000_000)
    record = M.measure_then_delete(path)
    ok(not path.exists(), "deleted after its size was recorded")
    eq(record["bytes"], 301_000_000, "the size")
    chains, jobs = healthy_batch()
    chains[0]["legs"][1]["world_file"]["bytes"] = record["bytes"]
    eq(by_id(grade(M, chains, jobs), "LC.WORLD_SIZE").status, "FAIL", "301 MB fails")
    stops(M, base_row(tmp, world_file={"bytes": record["bytes"], "deleted": True}), needle="C3 ")


def case_no_whole_read(M, tmp):
    path = tmp / "w" / "world.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes((snapshot(1, 1) + "\n\n" + snapshot(2, 5) + "\n" + snapshot(3, 9) + "\n\n").encode("utf-8"))
    real_open = open

    class NoWholeRead:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.handle.close()

        def __iter__(self):
            return iter(self.handle)

        def read(self, size=-1):
            if size is None or size < 0:
                raise RuntimeError("a whole-file read")
            return self.handle.read(size)

        def readlines(self, *args):
            raise RuntimeError("a whole-file read")

    def guarded_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        return NoWholeRead(handle) if Path(str(file)) == path else handle

    def refuse(*args, **kwargs):
        raise RuntimeError("a whole-file read")
    keep = tmp / "kept" / "world_last.jsonl"
    try:
        with mock.patch.object(Path, "read_text", refuse), mock.patch.object(Path, "read_bytes", refuse), \
                mock.patch("builtins.open", guarded_open):
            found = M.stream_world_tail(path, keep)
    except RuntimeError as error:
        raise AssertionError(f"stream_world_tail read the whole file: {error}") from None
    eq((found["lines"], found["bad_lines"], found["last_ok"]), (3, 0, True), "streamed")
    eq(keep.read_bytes(), (snapshot(3, 9) + "\n").encode(), "the last non-blank line kept")
    eq(found["counts"]["maps"], 3, "its counts")


def case_guard_decision(M, tmp):
    eq(M.guard_decision(1_500_000_001, 100.0), "world", "over the guard kills")
    eq(M.guard_decision(1_500_000_000, 100.0), None, "at the guard does not")
    eq(M.guard_decision(10, 29.9), "free", "29.9 GB free aborts")
    eq(M.guard_decision(10, 30.0), None, "30.0 does not")
    eq(M.guard_decision(None, None), None, "nothing read")


def case_guard_newest_only(M, tmp):
    runs = tmp / "runs"
    (runs / "20261105-000001-LC-S-1-L1").mkdir(parents=True)
    (runs / "20261105-000001-LC-S-1-L1" / "world.jsonl").write_bytes(b"x" * 50)
    (runs / "20261105-000002-LC-S-1-L2").mkdir()
    (runs / "20261105-000002-LC-S-1-L2" / "world.jsonl").write_bytes(b"x" * 10)
    eq(M.newest_world(runs), ("20261105-000002-LC-S-1-L2", 10), "ONLY the newest folder is read")
    eq(M.leg_of_folder("20261105-000002-LC-S-1-L2", "LC-S-1"), "L2", "its leg")


def case_stat_race(M, tmp):
    runs = tmp / "runs"
    (runs / "20261105-000001-LC-S-1-L1").mkdir(parents=True)
    (runs / "20261105-000001-LC-S-1-L1" / "world.jsonl").write_bytes(b"x")
    real_stat = Path.stat

    def racy(self, *args, **kwargs):
        if self.name == "world.jsonl":
            raise FileNotFoundError("deleted between the listing and the stat")
        return real_stat(self, *args, **kwargs)
    try:
        with mock.patch.object(Path, "stat", racy):
            found = M.newest_world(runs)
    except OSError as error:
        raise AssertionError(f"the guard crashed on a stat race (CH-14): {error}") from None
    eq(found, ("20261105-000001-LC-S-1-L1", None), "None, no crash")


def planted_folder(build: Path, profile: str, name: str, world: bool = True) -> Path:
    folder = build / "profiles" / profile / "ai_player_runs" / name
    folder.mkdir(parents=True)
    if world:
        (folder / "world.jsonl").write_text(snapshot(1, 1) + "\n" + snapshot(2, 2) + "\n", encoding="utf-8")
    (folder / "ai_player.log").write_text("[AI-WORLD] memory from nothing (a new memory): 0 maps (none), 0 tiles learned, "
                                          "0 warp links, 0 connections, 0 map changes\n", encoding="utf-8")
    return folder


def case_salvage_chain(M, tmp):
    job = chain_job(tmp)
    out, build = Path(job["out"]), Path(job["build_root"])
    planted_folder(build, job["profile"], f"20261105-000001-{job['chain']}-L1")
    l3 = planted_folder(build, job["profile"], f"20261105-000003-{job['chain']}-L3")
    LC._write_json(out / job["chain"] / "current_leg.json", {"leg": "L3", "arm": f"{job['chain']}-L3"})
    chain = LC.new_chain_row(job)
    chain["legs"] = [{"leg": "L1", "status": "RAN"}, {"leg": "L2", "status": "RAN"}]
    LC._write_json(out / "rows" / f"{job['chain']}.json", chain)
    found = M.salvage_chain(job, build, out, "a planted crash")
    eq([leg["status"] for leg in found["legs"]], ["RAN", "RAN", "SALVAGED", "NOT RUN", "NOT RUN"], "the rows")
    ok(not (l3 / "world.jsonl").exists(), "L3's world measured and deleted")
    ok(isinstance(found["legs"][2]["world_file"]["bytes"], int), "and its size recorded")
    eq(found["legs"][2]["checks"], [], "no checks (VACUOUS)")
    eq(found["stopped_at"], "L3", "stopped at L3")


def case_salvage_before_launch(M, tmp):
    job = chain_job(tmp)
    out, build = Path(job["out"]), Path(job["build_root"])
    l2 = planted_folder(build, job["profile"], f"20261105-000002-{job['chain']}-L2")
    LC._write_json(out / job["chain"] / "current_leg.json", {"leg": "L3", "arm": f"{job['chain']}-L3"})
    chain = LC.new_chain_row(job)
    chain["legs"] = [{"leg": "L1", "status": "RAN"}, {"leg": "L2", "status": "RAN"}]
    LC._write_json(out / "rows" / f"{job['chain']}.json", chain)
    found = M.salvage_chain(job, build, out, "died between legs")
    eq(found["legs"][2]["status"], "NOT RUN", "L3 never launched: NOT RUN, never L2's folder (CH-13)")
    ok((l2 / "world.jsonl").exists(), "L2's folder is not salvaged as L3's")


def case_end_sweep(M, tmp):
    job = chain_job(tmp)
    build = Path(job["build_root"])
    folder = planted_folder(build, job["profile"], f"20261105-000001-{job['chain']}-L1")
    left = M.end_sweep([job], build)
    ok(not (folder / "world.jsonl").exists(), "deleted by the end sweep")
    ok(left and "deleted by the end sweep" in left[0], left)


# ---------------------------------------------------------------------------------------------------- refusals (pure)
def run_args(**changes) -> argparse.Namespace:
    base = {"cmd": "run", "purpose": "graded", "run": "ch5", "first_seed": None, "to": None, "chains": None,
            "leg_frames": None, "prediction_file": None, "out": "C:/elsewhere/out", "build_root": None}
    base.update(changes)
    return argparse.Namespace(**base)


def dev_args(**changes) -> argparse.Namespace:
    return run_args(**{"purpose": "development", "run": None, "first_seed": 6041, "to": "ch2_wally", "chains": 3,
                       "prediction_file": "C:/elsewhere/prediction.txt", **changes})


def facts_of(graded: bool = True, **changes) -> dict:
    repo = Path("C:/R/repo")
    facts = {"repo": repo, "out": Path("C:/elsewhere/out"), "build_root": repo / "sandbox-pokebot",
             "default_build_root": repo / "sandbox-pokebot", "legs": [], "g3": [], "free": 80.0, "profiles_exist": [],
             "git": {"head": "a1", "origin": "a1", "dirty": []}, "named": [], "seeds": (6041, 6043)}
    facts.update(changes)
    return facts


def case_refusal_controls(M, tmp):
    eq(M.run_refusal(run_args(), facts_of()), None, "a graded batch as registered")
    eq(M.run_refusal(dev_args(), facts_of(False)), None, "a development batch")


def case_r1(M, tmp):
    ok((M.run_refusal(run_args(out="C:/R/repo/out"), facts_of(out=Path("C:/R/repo/out"))) or "").startswith("R1"), "R1")


def case_r2(M, tmp):
    ok((M.run_refusal(run_args(first_seed=6041), facts_of()) or "").startswith("R2"), "graded with a seed")
    ok((M.run_refusal(run_args(to="ch2_wally"), facts_of()) or "").startswith("R2"), "graded with --to")
    ok((M.run_refusal(run_args(run="ch9"), facts_of()) or "").startswith("R2"), "an unknown run")


def case_r2_build_root(M, tmp):
    facts = facts_of(build_root=Path("C:/R/repo/other-sandbox"))
    ok((M.run_refusal(run_args(), facts) or "").startswith("R2"), "graded in another build root (CH-08)")
    eq(M.run_refusal(dev_args(), {**facts, "named": []}), None, "a development batch may")


def case_r3(M, tmp):
    for missing in ("first_seed", "to", "prediction_file"):
        ok((M.run_refusal(dev_args(**{missing: None}), facts_of(False)) or "").startswith("R3"), f"without {missing}")
    ok((M.run_refusal(dev_args(), facts_of(False, prediction_error="empty")) or "").startswith("R3"), "empty prediction")


def case_r3_named(M, tmp):
    found = M.run_refusal(dev_args(), facts_of(False, named=[{"id": 86}]))
    ok((found or "").startswith("R3") and "86" in found, f"rehearsal seeds already played (CH-15): {found}")


def case_r4(M, tmp):
    ok((M.run_refusal(dev_args(), facts_of(False, legs_error="--to x is OPTIONAL")) or "").startswith("R4"), "R4")


def case_r5(M, tmp):
    ok((M.run_refusal(run_args(), facts_of(g3=["a brain import"])) or "").startswith("R5"), "R5")


def case_r6(M, tmp):
    ok((M.run_refusal(run_args(), facts_of(free=39.9)) or "").startswith("R6"), "39.9 GB")
    ok((M.run_refusal(run_args(), facts_of(free=None)) or "").startswith("R6"), "unreadable")
    eq(M.run_refusal(run_args(), facts_of(free=40.0)), None, "40.0 GB")


def case_r7(M, tmp):
    ok((M.run_refusal(run_args(), facts_of(profiles_exist=["ai-livechain-6201"])) or "").startswith("R7"), "R7")


def case_r8(M, tmp):
    learner = facts_of(out=Path("C:/Remote Projects/pokebot-learner/out"))
    ok((M.run_refusal(run_args(out=str(learner["out"])), learner) or "").startswith("R8"), "--out in the learner clone")
    outside = facts_of(build_root=Path("C:/elsewhere/sandbox"), default_build_root=Path("C:/elsewhere/sandbox"))
    ok((M.run_refusal(run_args(), outside) or "").startswith("R8"), "a build root outside the repository")


def case_r9(M, tmp):
    ok((M.run_refusal(run_args(), facts_of(git={"head": "a1", "origin": "b2", "dirty": []})) or "").startswith("R9"),
       "HEAD is not origin/main")
    ok((M.run_refusal(run_args(), facts_of(git={"head": None, "origin": None, "dirty": [], "error": "x"})) or "")
       .startswith("R9"), "git could not be read")


def case_r9_dirty(M, tmp):
    ok((M.run_refusal(run_args(), facts_of(git={"head": "a1", "origin": "a1", "dirty": [" M sandbox-pokebot/x.py"]}))
        or "").startswith("R9"), "a changed tracked file anywhere (CH-08)")


# ---------------------------------------------------------------------------------------------------- the ledger
_FAKE_REPO: dict = {}


def fake_repo(tmp: Path) -> Path:
    """The files registered_numbers hashes, copied ONCE per test process into a temp tree (its AI code: one brain file)
    and shared: a case that changes a file does it through `edited` (or `restored`), which puts the bytes back. (The fix
    round: V-03 made the hashed set 197 files and 10.7 MB, and the FIRST read of a freshly copied file costs about 0.9 s
    on this machine, measured, against 0.03 s warm: one copy per case had tripled the suite's time.)"""
    root = _FAKE_REPO.get("root")
    if root is None:
        root = _TEMP_ROOT / "fake_repo"
        for rel in (*LC.GRADER_FILES, LC.MILESTONES):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, root / rel)
        (root / "ai_player" / "brain").mkdir(parents=True, exist_ok=True)
        (root / "ai_player" / "brain" / "goals.py").write_text("x = 1\n", encoding="utf-8")
        _FAKE_REPO["root"] = root
    return root


@contextlib.contextmanager
def restored(path: Path):
    """Whatever the block writes to `path`, its bytes are put back after it (the shared fake repo stays as copied)."""
    original = path.read_bytes()
    try:
        yield
    finally:
        path.write_bytes(original)


def numbers(M, repo: Path, **dev) -> dict:
    legs = M.legs_of("ch5_rival_meet", M.load_milestones(repo))
    return M.registered_numbers("ch5", "ch5_rival_meet", (6201, 6206), 6, legs, repo, dev or None)


def case_register_begin(M, tmp):
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    found = numbers(M, repo)
    M.register((6201, 6206), found, "test", path=path)
    entry, lines = M.begin("graded", (6201, 6206), found, "tree", path=path)
    eq(entry["status"], "started", "the registered numbers begin")
    ok("GRADED, HELD-OUT seeds 6201-6206" in lines[0], lines[0])


def refused_after(M, tmp, change) -> None:
    tmp.mkdir(parents=True, exist_ok=True)
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    M.register((6201, 6206), numbers(M, repo), "test", path=path)
    with change(repo):
        changed = numbers(M, repo)
    try:
        M.begin("graded", (6201, 6206), changed, "tree", path=path)
    except ledger.Refused as error:
        ok("NOT the ones registered" in str(error), str(error))
        return
    raise AssertionError("a change after registration was not refused")


def case_changed_budget_refused(M, tmp):
    refused_after(M, tmp, lambda repo: mock.patch.dict(M.FRAMES_BY_CHAPTER, {5: 900000}))


def case_changed_reach_min_refused(M, tmp):
    refused_after(M, tmp, lambda repo: mock.patch.object(M, "REACH_MIN", 4))


def case_changed_cap_refused(M, tmp):
    refused_after(M, tmp, lambda repo: mock.patch.object(M, "WORLD_MAX_BYTES", 500_000_000))


@contextlib.contextmanager
def edited(path: Path, old: str, new: str):
    """`old` replaced by `new` once in `path` for the block; the original bytes are put back after it (`restored`)."""
    with restored(path):
        text = path.read_text(encoding="utf-8")
        ok(old in text, f"the edit's anchor {old!r} is in {path.name}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        yield


def case_changed_milestones_refused(M, tmp):
    refused_after(M, tmp, lambda repo: edited(repo / M.MILESTONES, '"at_least": 8', '"at_least": 7'))


def case_changed_ai_code_refused(M, tmp):
    refused_after(M, tmp, lambda repo: edited(repo / "ai_player" / "brain" / "goals.py", "x = 1", "x = 2"))


def case_changed_grader_refused(M, tmp):
    refused_after(M, tmp, lambda repo: edited(repo / "ai_player" / "gates" / "live_step5.py", "FRAME_SLACK = 5",
                                              "FRAME_SLACK = 50"))


def case_unregistered_refused(M, tmp):
    repo = fake_repo(tmp)
    try:
        M.begin("graded", (6201, 6206), numbers(M, repo), "tree", path=tmp / "ledger.json")
    except ledger.Refused:
        return
    raise AssertionError("an unregistered graded batch began")


def case_dev_on_registered_refused(M, tmp):
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    M.register((6201, 6206), numbers(M, repo), "test", path=path)
    try:
        M.begin("development", (6203, 6205), {"x": 1}, "tree", path=path)
    except ledger.Refused:
        return
    raise AssertionError("a development batch spent registered seeds")


def case_dev_numbers_prediction(M, tmp):
    repo = fake_repo(tmp)
    a = numbers(M, repo, chains=6, leg_frames_override={}, prediction_sha256="a" * 64)
    b = numbers(M, repo, chains=6, leg_frames_override={}, prediction_sha256="b" * 64)
    eq(a["prediction_sha256"], "a" * 64, "the prediction's sha is in the numbers")
    ok(ledger.numbers_sha256(a) != ledger.numbers_sha256(b), "a changed prediction changes the sha")


def case_real_ledger_seeds(M, tmp):
    eq(M.GRADED_RUNS["ch5"]["seeds"], (6201, 6206), "the registered run's seeds")
    named = M.seeds_named(6201, 6206)
    eq([e["id"] for e in named if e["driver"] != M.DRIVER], [], "no OTHER entry names 6201-6206 (CH-04)")


def case_bounds_needles(M, tmp):
    text = numbers(M, fake_repo(tmp))["bounds_text"]
    for needle in ("L1 ch1_pokedex, 330000 frames: RECEIVED_POKEDEX_FROM_BIRCH (2276) = 1",
                   "L2 ch2_wally, 330000 frames: VAR_PETALBURG_GYM_STATE (16517) >= 2",
                   "L5 ch5_rival_meet, 600000 frames: ENABLE_RIVAL_MATCH_CALL (253) = 1, VAR_RUSTBORO_CITY_STATE (16474) >= 8",
                   "(C1)", "(C2)", "(C3)", "(C4)", "(C5)", "(C6)", "at least 5 of the 6 chains", "300000000",
                   "ALREADY HELD", "UNREAD", "LC.MEMORY", "Route104", "goal manager's in-run memory starts again",
                   # (the fix round) V-03: exactly what is hashed, and the CRLF rule said as a rule
                   f"grader_files hashes, by path and content, exactly these {len(M.GRADER_FILES)} files and nothing "
                   f"else", "sandbox-pokebot/modules/data/symbols/pokeemerald.sym", "Not hashed: the ROM",
                   "a change of line endings alone is accepted BY DESIGN",
                   # V-02: only the registered rows count, re-derived
                   "Every check counts the REGISTERED chains only", "a stored flag can stop a chain but never continue one",
                   # V-08: the dead launch's rule, said and named
                   "harness: the launch died before playing a frame", "the reach tolerance does not cover it",
                   # V-09: what LC.CUSTODY can catch
                   "on a later leg they catch a regression of the harness only, never anything the AI does",
                   # (the second fix round) C2-01: an ignored row and its absent chain; C2-02: the starts of the closure;
                   # C2-05: the refusal; C2-07: the ERROR record
                   "starter, seed or profile is not the registered job's are each IGNORED and named with the reason, so a "
                   "registered chain whose row is ignored is ABSENT",
                   "of the files the harness and the launcher run by path (ai_player/gates/check_purity.py",
                   "of the plugins the framework loads by name in every leg",
                   # (the third fix round) C3-H04/H01/H02: every file named, the resolution, caches and shadows refused,
                   # the environment; C3-H05: the AI's framework imports start the closure; C3-H07: the CODE sentence
                   "Registration and a graded run are REFUSED (R12) while that scan finds a file this list does not hash "
                   "(every one named; a .pyw the closure reaches is one)", "each module resolved in CPython's order (a "
                   "package's __init__.py, then __init__.pyw, before a module X.py, then X.pyw)",
                   "a __pycache__ file CPython would load INSTEAD of its source that holds other code (of a closure file, or "
                   "of any .py file of the AI's under ai_player/ outside gates/)",
                   "an entry directly in the repository root, ai_player/gates or sandbox-pokebot that Python could import "
                   "instead of a module, its name compared without case",
                   "of the framework modules the AI's own files import (every absolute modules.* and plugins.* import",
                   "except *.md files, *.pyc files and __pycache__ folders",
                   # (the fourth fix round) C4-H01..H06 in the CODE sentence, C4-H05's limit, the THREAT MODEL
                   "unless the entry IS that module (exactly these: the folder ai_player at the root; in sandbox-pokebot the "
                   "folders modules and plugins and the files pokebot.py, requirements.py and updater.py",
                   "a module installed outside the repository (every folder on the interpreter's sys.path outside it, listed "
                   "when the scan runs, so a library's own imports are covered",
                   "a .pyc file of the AI's outside __pycache__",
                   "any Python code file (.py, .pyw, .pyc or an extension module) under ai_player/evidence/",
                   "a graded run is also refused while any environment variable starting with PYTHON is set other than "
                   "PYTHONIOENCODING, PYTHONUTF8, PYTHONDONTWRITEBYTECODE, PYTHONUNBUFFERED",
                   "it does not claim to stop code written to switch the grader off from inside its own process: the purity "
                   "gate and the clean, pushed tree (R9) are the defence there",
                   "THREAT MODEL: the driver guards against (a) honest-case harness defects",
                   "(c) edits of an --out folder after the run, which can never make the offline re-grade (grade DIR) report "
                   "a verdict better than the ledger's",
                   # C3-E02: the AI's output is untrusted; C3-G01: each leg's own records; C3-G06: statuses as stored
                   "Every file the AI writes (world.jsonl and its kept last line, ai_player.log, the verdict file and its "
                   "counters, actions.jsonl), of any content or kind, is UNTRUSTED",
                   "a folder where a file was meant, or a file the OS refuses to open (a world.jsonl is tried 3 times, 1 s "
                   "apart, first) fails the check of that leg",
                   "text that cannot be written as UTF-8 is kept escaped", "whose five counts (maps, tiles learned, warp links, connections, "
                   "map changes) can be read", "every leg that RAN must carry its REGISTERED job in its own harness records",
                   "no two legs of the counted rows may share a run folder or a kept file",
                   "Each leg's STATUS (RAN, NOT RUN, ...) is READ AS STORED",
                   "a NOT RUN leg after a leg whose re-derived continuation holds is a custody failure unless STOP.txt or "
                   "ABORT.txt is in --out",
                   # (the fourth fix round) C4-G04, C4-G02, C4-G06
                   "lists that chain as SALVAGED and the leg's reason is the salvage reason",
                   "Each counted row holds exactly the registered legs, in order",
                   "a row copied from another chain fails custody unless every one of these records is rewritten as well",
                   "beside a record that says it held, fails it",
                   # C3-E01, C3-E03, C3-E06, the chains-run guard: before begin; the stages; a hard kill only
                   "Every step that needs no chain (--out, the job files, the profile snapshots) runs before ledger.begin",
                   "while the chains run (every running chain process is killed first)",
                   "'ERROR (harness: <type>: <message> while <stage>; no PASS or FAIL; the seeds are spent)'",
                   "a failed ledger write is retried with the computed verdict before it falls back to ERROR",
                   "The entry stays 'started' only if this orchestrator process is killed hard (its window closed, "
                   "Ctrl+Break, a task kill), or if the ledger file cannot be written at all",
                   # (the fourth fix round) C4-E03, C4-E02, C4-E05, C4-G01..G03
                   "While the entry is being finished a second Ctrl+C is ignored (a line says so first)",
                   "a launch first claims --out by creating BATCH.claim.json there exclusively",
                   "give the command that finishes it, which writes only this ERROR verdict",
                   "The offline re-grade (grade DIR) reads the batch's ledger entry and never reports a verdict better than "
                   "it",
                   # (the third fix round's finish, 2026-11-06) the exemption R12 makes is registered with the rule
                   "and there the git-ignored folders mgba and profiles, which are not hashed",
                   "Not hashed: the ROM, the emulator's library (sandbox-pokebot/mgba)"):
        ok(needle in text, f"the bounds text says {needle!r}")
    doc = " ".join((M.__doc__ or "").split())
    ok("never anything the AI does" in (M.__doc__ or ""), "the docstring says LC.CUSTODY's limit too (V-09)")
    ok("still FINISHES the ledger entry, as \"ERROR (harness:" in doc, "the docstring says C2-07's rule too")
    for needle in ("5 = a harness crash the guard did not cover", "the only way the entry stays \"started\" is a HARD KILL "
                   "of this orchestrator process itself", "EXIT: 0 = PASS (graded: VERIFIED and the ledger says PASS; "
                   # (the fifth fix round) C5-01's MISMATCH is named among exit 1's verdicts
                   "development: labelled), 1 = FAIL, MISMATCH or UNVERIFIED, 2 = could not be graded, 3 = ABORTED",
                   "finish-entry DIR",
                   # (the fourth fix round) the THREAT MODEL, said in the docstring as in the bounds text
                   "THREAT MODEL", "It does NOT claim to stop code crafted to switch the grader off from inside its own "
                   "process", "a second Ctrl+C is ignored until the entry is written"):
        ok(needle in doc, f"the docstring says {needle!r}")
    run_doc = " ".join((M.run_batch.__doc__ or "").split())
    ok("The entry stays \"started\" only after a HARD KILL of this process" in run_doc, run_doc[-400:])
    ok("When the ledger cannot be written at all, the entry is NOT finished" in " ".join(M.finish_on_error.__doc__.split()),
       "finish_on_error's docstring says it")


# ---------------------------------------------------------------------------------------------------- the scheduler
class FakeHandle:
    """A child that is alive for `alive` polls, then runs `runner` (if any) and ends with its code."""

    def __init__(self, runner=None, alive: int = 2, pid: int = 1) -> None:
        self.runner, self.alive, self.pid, self.polls, self.code, self.killed = runner, alive, pid, 0, None, False

    def poll(self):
        if self.code is not None:
            return self.code
        if self.polls < self.alive:
            self.polls += 1
            return None
        self.code = self.runner() if self.runner else 0
        return self.code

    def kill_tree(self) -> None:
        self.killed = True
        self.code = -9


def scheduled(M, jobs, may=lambda job: (True, ""), parallel=None):
    sleeps: list = []
    plan = M.schedule(jobs, lambda job: FakeHandle(alive=3), lambda running: None,
                      M.PARALLEL if parallel is None else parallel, 15, sleeps.append, may, 5)
    return plan, sleeps


def case_scheduler_max_3(M, tmp):
    plan, _ = scheduled(M, LC.jobs_of(6201, 6))
    eq(plan["most_running"], 3, "never more than 3 at once, and exactly 3")


def case_scheduler_order_and_stagger(M, tmp):
    jobs = LC.jobs_of(6201, 6)
    plan, sleeps = scheduled(M, jobs)
    eq(plan["order"], ["LC-S-6201", "LC-C-6203", "LC-T-6205", "LC-S-6202", "LC-C-6204", "LC-T-6206"], "JOB_ORDER")
    eq(sleeps.count(15), 5, "15 s between starts")


def case_scheduler_may_start(M, tmp):
    plan, _ = scheduled(M, LC.jobs_of(6201, 6), may=lambda job: (job["seed"] != 6203, "planted"))
    eq([job["chain"] for job, _ in plan["not_started"]], ["LC-C-6203"], "a chain not started is recorded")


# ---------------------------------------------------------------------------------------------------- whole batches
class FakeTree:
    def __init__(self, move_at: int | None = None) -> None:
        self.calls, self.moves, self.move_at, self.stats = 0, [], move_at, {}

    @property
    def moved(self) -> bool:
        return bool(self.moves)

    def check(self, when: str) -> bool:
        self.calls += 1
        if self.move_at is not None and self.calls >= self.move_at:
            self.moves.append(f"{when}: 1 changed ['ai_player/brain/x.py']")
            return False
        return not self.moves

    def seal(self, verdict: str):
        self.check("at the verdict")
        return ("FAIL", "FROZEN TREE: FAIL - planted") if self.moves else (verdict, "FROZEN TREE: PASS - fake")


class Rig:
    """A whole batch with stub launches: a temp repo geometry, build root, out, ledger and evidence folder."""

    def __init__(self, M, tmp: Path, plans: dict | None = None, alive: int = 2, free=lambda path: 100.0,
                 tree: FakeTree | None = None, clock=None, pre_spawn=None, tree_every: float = 10 ** 9,
                 leftover=None, real_child: bool = False) -> None:
        self.M, self.plans, self.alive = M, plans or {}, alive
        #: (the third fix round, C3-E02) the stub child dies like a separate process: ANY exception ends it with exit 1
        #: (recorded in child_errors) instead of reaching the orchestrator, which a real `child` process cannot do
        self.real_child, self.child_errors = real_child, []
        self.repo = tmp / "repo"
        self.build = self.repo / "sandbox-pokebot"
        (self.build / "profiles").mkdir(parents=True)
        self.out, self.ledger, self.evidence = tmp / "out", tmp / "ledger.json", tmp / "evidence"
        self.handles: list[FakeHandle] = []
        self.killed: list[int] = []
        self.tree = tree or FakeTree()
        self.pre_spawn = pre_spawn
        ticks = iter(range(10 ** 6))
        # (C2-05) the closure scan is stubbed as "every file hashed" here (1.4 s a scan); ClosureTests drive the real one
        self.deps = M.Deps(spawn=self.spawn, free=free, git_state=lambda: {"head": "a", "origin": "a", "dirty": []},
                           leftover=leftover or (lambda: []), g3=lambda: [], closure=lambda: ([], 0, 0.0),
                           watch=lambda: self.tree, snapshot=lambda: None,
                           code_line=lambda: "fake code line", default_build_root=lambda: self.build,
                           kill=self.kill, sleep=lambda seconds: None, clock=clock or (lambda: float(next(ticks))),
                           ledger_path=self.ledger, evidence_dir=self.evidence, repo=self.repo, poll_seconds=0, stagger=0,
                           tree_every=tree_every)

    def kill(self, pid: int) -> list[int]:
        self.killed.append(pid)
        return [pid]

    def spawn(self, job: dict, job_path: Path, log_path: Path) -> FakeHandle:
        ok(job_path.is_file(), "the job file is written before the spawn")
        if self.pre_spawn is not None:
            self.pre_spawn(job)
        stub = Stub(job, self.plans.get(job["chain"]))

        def runner() -> int:
            saved = L5.PROFILE
            L5.PROFILE = job["profile"]
            try:
                self.M.run_chain(job, stub)
                return 0
            except SystemExit:
                return 1
            except Exception as error:  # noqa: BLE001
                if not self.real_child:
                    raise
                self.child_errors.append(f"{job['chain']}: {type(error).__name__}: {error}")
                return 1
            finally:
                L5.PROFILE = saved
        handle = FakeHandle(runner, self.alive, pid=1000 + len(self.handles))
        self.handles.append(handle)
        return handle

    def register(self) -> None:
        legs = self.M.legs_of("ch5_rival_meet", self.M.load_milestones())
        found = self.M.registered_numbers("ch5", "ch5_rival_meet", (6201, 6206), 6, legs, REPO)
        self.M.register((6201, 6206), found, "test", path=self.ledger)

    def run(self, args: argparse.Namespace, environ: dict | None = None) -> tuple[int, str]:
        """run_batch with the stubs; (C3-H02, C4-H02) the caller's PYTHON* variables are removed for the run (a graded
        run refuses every one PYTHON_ENV_ALLOWED does not list) unless `environ` sets them; the environment is restored
        after."""
        buffer = io.StringIO()
        with mock.patch.dict(os.environ, {}), \
                mock.patch.object(self.M, "ai_code_sha256", lambda repo=None: "0" * 64), contextlib.redirect_stdout(buffer):
            for name in [name for name in os.environ if name.upper().startswith("PYTHON")]:
                os.environ.pop(name, None)
            os.environ.update(environ or {})
            code = self.M.run_batch(args, self.deps)
        self.text = buffer.getvalue()
        return code, buffer.getvalue()

    def results(self) -> dict:
        return json.loads((self.out / "results.json").read_text(encoding="utf-8"))

    def entry(self) -> dict:
        return ledger.load(self.ledger)["entries"][-1]


def graded_rig(M, tmp, **kwargs) -> Rig:
    rig = Rig(M, tmp, **kwargs)
    with mock.patch.object(M, "ai_code_sha256", lambda repo=None: "0" * 64):
        rig.register()
    return rig


def case_e2e_graded_pass(M, tmp):
    rig = graded_rig(M, tmp)
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 0, f"exit 0 = PASS: {text[-2000:]}")
    results = rig.results()
    eq(results["verdict"], "PASS", "the verdict")
    eq(results["most_running"], 3, "at most 3 at once, and 3")
    eq(rig.entry()["status"], "done", "the ledger entry finished")
    ok(rig.entry()["verdict"].startswith("GRADED, PASS"), rig.entry()["verdict"])
    evidence = Path(results["evidence"]).read_text(encoding="utf-8")
    ok(evidence.startswith("LIVE CHAIN HELD-OUT - GRADED - VERDICT PASS"), evidence[:200])
    ok("BOUNDS TEXT (hashed into the registration):" in evidence, "the bounds text in the evidence")


def case_e2e_dry_run(M, tmp):
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp, plans={jobs[1]["chain"]: {"L2": {"miss": True}}, jobs[4]["chain"]: {"L3": {"die": True}}})
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"a salvaged leg is VACUOUS, so FAIL: {text[-1500:]}")
    results = rig.results()
    eq(results["most_running"], 3, "two waves of 3")
    eq(rig.entry()["status"], "done", "the ledger entry finished")
    ok("FAIL" in rig.entry()["verdict"], rig.entry()["verdict"])
    stopped = json.loads((rig.out / "rows" / f"{jobs[1]['chain']}.json").read_text(encoding="utf-8"))
    eq([leg["status"] for leg in stopped["legs"]], ["RAN", "RAN", "NOT RUN", "NOT RUN", "NOT RUN"], "stopped at L2")
    died = json.loads((rig.out / "rows" / f"{jobs[4]['chain']}.json").read_text(encoding="utf-8"))
    eq([leg["status"] for leg in died["legs"]], ["RAN", "RAN", "SALVAGED", "NOT RUN", "NOT RUN"], "salvaged at L3")
    eq(list(rig.build.glob("profiles/*/ai_player_runs/*/world.jsonl")), [], "every world.jsonl deleted")
    statuses = {c["id"]: c["status"] for c in results["checks"]}
    eq((statuses["LC.REACH"], statuses["LC.PURITY"]), ("FAIL", "VACUOUS"), "4 of 6 reach; the salvage not judged")
    evidence = Path(results["evidence"]).read_text(encoding="utf-8")
    ok("NOT RUN: [" in evidence and "the chain stopped at L2" in evidence, "NOT RUN legs printed with their reasons")


def case_e2e_unregistered_refused(M, tmp):
    rig = Rig(M, tmp)
    rig.ledger.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    before = rig.ledger.read_bytes()
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 2, f"refused: {text[-500:]}")
    ok("R10" in text, text[-500:])
    eq(rig.handles, [], "no chain was started")
    eq(rig.ledger.read_bytes(), before, "the ledger is unchanged")


def case_e2e_development(M, tmp):
    rig = Rig(M, tmp)
    prediction = tmp / "prediction.txt"
    prediction.write_text("3 of 3 reach ch2_wally.\n", encoding="utf-8")
    code, text = rig.run(dev_args(out=str(rig.out), prediction_file=str(prediction)))
    eq(code, 0, f"a development batch ran: {text[-1500:]}")
    entry = rig.entry()
    eq((entry["purpose"], entry["first"], entry["last"], entry["status"]), ("development", 6041, 6043, "done"),
       "the ledger entry: first..first+2 (N3)")
    ok(entry["verdict"].startswith("DEVELOPMENT, not graded, NO PASS (development: PASS"), entry["verdict"])
    evidence = Path(rig.results()["evidence"]).read_text(encoding="utf-8")
    # (V-06) the sha256 printed is the FILE's bytes' (so `sha256sum prediction.txt` matches), never the stripped text's
    file_sha = hashlib.sha256(prediction.read_bytes()).hexdigest()
    ok("3 of 3 reach ch2_wally." in evidence and f"sha256 of the file's bytes {file_sha}" in evidence,
       "the prediction and its file's sha256 in the evidence")
    ok(hashlib.sha256(b"3 of 3 reach ch2_wally.").hexdigest() not in evidence, "not the stripped text's sha256")
    ok(Path(rig.results()["evidence"]).name.endswith("chain-heldout-dev-ch2_wally-6041.txt"), rig.results()["evidence"])


def case_free_guard_aborts(M, tmp):
    reads = iter([100.0] + [25.0] * 10 ** 4)
    rig = graded_rig(M, tmp, free=lambda path: next(reads),
                     pre_spawn=lambda job: planted_folder(Path(job["build_root"]), job["profile"],
                                                          f"20261105-000000-{job['chain']}-L1"))
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 3, f"ABORTED by the harness (CH-07): {text[-1200:]}")
    eq(rig.results()["verdict"], "ABORTED (harness: disk)", "no PASS or FAIL")
    ok("ABORTED" in rig.entry()["verdict"], rig.entry()["verdict"])
    ok(rig.killed, "the running launchers were killed")
    ok((rig.out / "ABORT.txt").is_file(), "ABORT.txt")


def case_world_guard_kills(M, tmp):
    with mock.patch.object(M, "GUARD_WORLD_BYTES", 100):  # (hashed: registered and run under the same guard)
        rig = graded_rig(M, tmp, pre_spawn=lambda job: (planted_folder(Path(job["build_root"]), job["profile"],
                                                                       f"20261105-000000-{job['chain']}-L1")))
        code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"the guarded legs stop their chains: {text[-800:]}")
    ok(len(rig.killed) == 6, f"each chain's launcher killed once: {rig.killed}")
    marker = json.loads((rig.out / "LC-S-6201" / "L1.KILLED.json").read_text(encoding="utf-8"))
    eq(marker["cause"], "world", "the marker's cause")
    chain = json.loads((rig.out / "rows" / "LC-S-6201.json").read_text(encoding="utf-8"))
    ok("C4 " in chain["legs"][0]["why"], chain["legs"][0]["why"])
    eq(list(rig.build.glob("profiles/*/ai_player_runs/*/world.jsonl")), [], "the end sweep deleted the planted worlds")
    ok(any("deleted by the end sweep" in w for w in rig.results()["world_left"]), rig.results()["world_left"])


def case_watchdog(M, tmp):
    ticks = iter(range(10 ** 7))
    rig = graded_rig(M, tmp, alive=200, clock=lambda: 1.0e5 * next(ticks))  # each read 100,000 s later
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"watchdog kills are salvaged and fail: {text[-800:]}")
    ok(rig.handles and all(h.killed for h in rig.handles), "every chain past its watchdog was killed")
    ok((rig.out / "LC-S-6201" / "WATCHDOG.txt").is_file(), "WATCHDOG.txt")
    ok(any("watchdog" in e for e in rig.results()["events"]), rig.results()["events"])


def case_tree_move_tick(M, tmp):
    rig = graded_rig(M, tmp, tree=FakeTree(move_at=4), tree_every=0)
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"a moved tree fails: {text[-800:]}")
    ok(any("frozen tree moved" in e for e in rig.results()["events"]), f"the tick saw it: {rig.results()['events']}")
    first = json.loads((rig.out / "rows" / "LC-S-6201.json").read_text(encoding="utf-8"))
    ok(first["legs"][0]["status"] == "NOT RUN" and "changed mid-batch" in first["legs"][0]["reason"],
       f"a running chain launches no leg after the move: {first['legs'][0]}")


def case_e2e_refusal_before_ledger(M, tmp):
    rig = graded_rig(M, tmp)
    (rig.build / "profiles" / "ai-livechain-6201").mkdir()
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 2, f"refused: {text[-500:]}")
    ok("R7" in text, text[-500:])
    eq(rig.entry()["status"], "registered", "the ledger never began (the registration is not spent)")
    eq(rig.handles, [], "no chain was started")


def case_tree_move_stops(M, tmp):
    rig = graded_rig(M, tmp, tree=FakeTree(move_at=4))
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"a moved tree fails: {text[-800:]}")
    statuses = {c["id"]: c["status"] for c in rig.results()["checks"]}
    eq(statuses["LC.FROZEN"], "FAIL", "LC.FROZEN")
    ok((rig.out / "STOP.txt").is_file(), "STOP.txt written")
    ok(len(rig.handles) == 3, f"the chains after the move were not started: {len(rig.handles)}")


# ---------------------------------------------------------------------------------------------------- wiring (CH-01)
def calls_in(source: str, qualname: str) -> set[str]:
    """Every LIVE call (by name) inside one function and the functions nested in it (`call_census.live_calls`)."""
    from ai_player.gates.call_census import functions, live_calls

    names = [q for q in functions(source) if q == qualname or q.startswith(qualname + ".")]
    return {name for q in names for name, _, _ in live_calls(source, q)}


WIRING = {
    "run_batch": {"gather_facts", "run_refusal", "watch", "check", "seal", "begin", "schedule", "salvage_chain",
                  "end_sweep", "grade_batch", "guard_decision", "newest_world", "kill", "kill_tree", "keep_earlier",
                  # (the second fix round) C2-07's guard, C2-03's re-derived per-chain line
                  "finish_on_error", "registered_chains",
                  # (the third fix round) C3-E01 before begin, C3-E03 the retried finish, the chains-run guard
                  "prepare_out", "undo_out", "finish_entry", "stop_children", "main_profile_state", "run_folders",
                  # (the fourth fix round) C4-E03 the guard's interrupts, C4-G04 the orchestrator's own salvage record
                  "hold_interrupts", "note_interrupt", "salvaged_chains"},
    "gather_facts": {"legs_of", "g3", "git_state", "seeds_named", "free", "out_listing", "closure", "python_env_refused"},
    # (C2-05) the closure checked at registration and before a graded run; (C2-07) the ERROR record finishes the entry
    "register_run": {"closure_missing", "closure_refusal", "register"},
    "run_refusal": {"closure_refusal"},
    "finish_on_error": {"error_verdict", "finish_entry", "_write_json", "finish_command", "error_line", "entry_status",
                        "note_interrupt"},
    "finish_entry": {"finish", "entry_finished"},
    "finish_entry_cli": {"finish", "unfinished_problems"},
    "unfinished_problems": {"error_line"},
    # (the fourth fix round) C4-E02 the claim before the job files; C4-E04 every write UTF-8-safe; C4-H02 the environment
    "prepare_out": {"undo_out", "_write_json"},
    "_write_json": {"utf8_safe"},
    "untrusted_text": {"utf8_safe"},
    "child_env": {"python_env_refused"},
    # C4-H03, C4-H04, C4-H06: the installed names, the AI's caches and its evidence folder
    "toplevel_problems": {"outside_modules", "_importable"},
    "ai_problems": {"pycache_problems"},
    "verify_numbers": {"numbers_jobs_problems"},
    # (C2-02, C3-H05) the closure starts from the files run by path, the plugins loaded by name, the AI's framework imports
    "closure_scan": {"loaded_plugins", "ai_framework_imports", "_closure_imports", "_closure_file"},
    "grader_closure": {"closure_scan"},
    # (C3-H01, C3-H02) R12 also refuses another file in place of a hashed one
    "closure_missing": {"closure_scan", "resolution_problems", "pycache_problems", "toplevel_problems", "ai_problems"},
    "pycache_problems": {"_pyc_problem"},
    "run_chain": {"child_refusal", "check_purity", "check_after_is_this_run", "finish_leg", "custody_problems",
                  "continue_after", "guard_mark", "stop_rest", "salvage_leg", "launch_died", "judged"},
    "finish_leg": {"stream_world_tail", "measure_then_delete", "read_log_counts"},
    "stream_world_tail": {"world_counts", "_line_parses"},
    "custody_problems": {"leg_identity_problems"},
    # (the fix round, V-02) the grade counts the registered rows only, each re-derived from its own facts
    "grade_batch": {"registered_chains"},
    "registered_chains": {"rederived_chain", "shared_legs"},
    "rederived_chain": {"proof_holds", "leg_reached", "launch_died", "custody_problems", "kept_problem", "continue_after",
                        "chain_reaches", "kept_path"},
    "kept_problem": {"world_counts"},
    "regrade_dir": {"registered_rows", "guard_mark", "grade_batch", "verify_numbers", "find_entry", "ledger_result",
                    "salvaged_chains",
                    # (the fifth fix round) C5-01: the entry the folder's recorded id names
                    "recorded_problems"},
    "grade_dir": {"regrade_dir"},
    "child": {"run_chain", "python_env_refused"},
    "main": {"command"},
}


def case_wiring(M, tmp):
    source = Path(M.__file__).read_text(encoding="utf-8")
    for function, want in WIRING.items():
        missing = want - calls_in(source, function)
        ok(not missing, f"{function} no longer calls {sorted(missing)}")


def case_wiring_defaults(M, tmp):
    """(The third check's C3-H03) the PRODUCTION side effects a graded run uses (`Deps()`'s defaults; every test rig
    replaces them): R12's closure scan, R9's git facts, R5's G-3 walk, R6's free space, R2's build root, the leftover
    processes and the spawn of a chain process. A default switched off passed every other test."""
    deps = M.Deps()
    for name, want in (("closure", M.closure_missing), ("git_state", M.git_state), ("g3", M.g3_scan),
                       ("free", M.safe_free), ("default_build_root", M.default_build_root),
                       ("leftover", M.leftover_processes), ("spawn", M.spawn_child),
                       # (the fourth check's C4-H08) the rest: LC.FROZEN's watch, the snapshot, the code line, the kill
                       ("watch", M.watch_tree), ("snapshot", M.snapshot), ("code_line", M.code_line),
                       ("kill", M.kill_descendants)):
        ok(getattr(deps, name) is want, f"Deps().{name} is {getattr(deps, name)!r}, not {want.__name__}")


def case_wiring_bodies(M, tmp):
    """(The fourth check's C4-H08) the BODIES behind the production Deps, each of which a test rig replaces, so a body
    switched off passed every other test: watch_tree watches this repository's code (LC.FROZEN can fail), safe_free is the
    drive's real free space (R6 and the disk guard), g3_scan walks live_chain itself (R5), and leftover_processes finds a
    python process whose command line names the prefix (LC.LEFTOVER)."""
    tree = M.watch_tree()
    ok(Path(tree.repo) == REPO.resolve() and "ai_player/gates/live_chain.py" in tree.stats and tree.explicit,
       f"watch_tree watches this repository's code: {tree.repo}, {len(tree.stats)} files")
    from ai_player.gates.live_ki128 import free_gb
    ok(abs((M.safe_free(tmp) or -1.0) - free_gb(tmp)) < 1.0, f"safe_free is the real free space: {M.safe_free(tmp)}")
    seen: list = []
    with mock.patch("ai_player.gates.check_grader_imports.scan", lambda repo, names: seen.append((repo, names)) or []):
        eq(M.g3_scan(), [], "the G-3 walk's result")
    eq(seen, [(M.REPO, ("ai_player.gates.live_chain",))], "g3_scan walks live_chain itself")
    marker = f"{M.PROFILE_PREFIX}wiring-{os.getpid()}-{time.time_ns()}"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", marker], creationflags=flags,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        found = M.leftover_processes(marker)
    finally:
        sleeper.kill()
        sleeper.wait(timeout=30)
    ok(any(line.startswith(f"{sleeper.pid} ") for line in found), f"leftover_processes finds the python process: {found}")


# ==================================================================================================== THE FIX ROUND
# (the verifier's V-01..V-09, 2026-11-05) each new or changed guard: a FAULT case, a CONTROL case, and a mutant in MUTANTS
DEAD = "harness: the launch died before playing a frame"


# ---------------------------------------------------------------------------------------------------- V-01: --out
def case_r11_out_not_empty(M, tmp):
    for planted in (["STOP.txt"], ["ABORT.txt"], ["notes-of-an-earlier-batch.txt"], ["rows"]):
        for args, graded in ((run_args(), True), (dev_args(), False)):
            found = M.run_refusal(args, facts_of(graded, out_entries=planted))
            ok((found or "").startswith("R11") and planted[0] in found,
               f"{planted} ({'graded' if graded else 'development'}) is refused before the ledger: {found}")
    found = M.run_refusal(run_args(), facts_of(out_error="it exists and is not a folder"))
    ok((found or "").startswith("R11"), f"an --out that is a file: {found}")
    eq(M.run_refusal(run_args(), facts_of(out_entries=[])), None, "CONTROL: an empty --out (graded)")
    eq(M.run_refusal(dev_args(), facts_of(False, out_entries=[])), None, "CONTROL: an empty --out (development)")


def case_out_listing(M, tmp):
    eq(M.out_listing(tmp / "missing"), {"out_entries": []}, "CONTROL: a missing --out")
    (tmp / "empty").mkdir()
    eq(M.out_listing(tmp / "empty"), {"out_entries": []}, "CONTROL: an empty one")
    (tmp / "full" / "rows").mkdir(parents=True)
    (tmp / "full" / "STOP.txt").write_text("x", encoding="utf-8")
    eq(M.out_listing(tmp / "full"), {"out_entries": ["STOP.txt", "rows"]}, "every entry, a folder too")
    (tmp / "afile").write_text("x", encoding="utf-8")
    ok("not a folder" in M.out_listing(tmp / "afile").get("out_error", ""), "a file is no --out")


def case_e2e_out_not_empty_refused(M, tmp):
    for name in ("STOP.txt", "ABORT.txt", "notes-of-an-earlier-batch.txt"):
        rig = graded_rig(M, tmp / name.split(".")[0])
        rig.out.mkdir(parents=True)
        (rig.out / name).write_text("left by an earlier batch\n", encoding="utf-8")
        before = rig.ledger.read_bytes()
        code, text = rig.run(run_args(out=str(rig.out)))
        eq(code, 2, f"{name}: refused before any leg (V-01): {text[-600:]}")
        ok("R11" in text and name in text, f"{name}: {text[-600:]}")
        # (the fourth fix round) refused by the LISTING, which says why, before the claim's own check (C4-E02) would
        ok("exists and is NOT EMPTY" in text, f"{name}: refused by the listing: {text[-600:]}")
        eq((rig.entry()["status"], rig.entry().get("started")), ("registered", None),
           f"{name}: the registration is NOT spent (no 'started')")
        eq(rig.ledger.read_bytes(), before, f"{name}: the ledger is unchanged")
        eq(rig.handles, [], f"{name}: no chain was started")
        ok(not (rig.out / "results.json").exists(), f"{name}: no results")
    rig = Rig(M, tmp / "dev")
    rig.ledger.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    (rig.out / "rows").mkdir(parents=True)
    (rig.out / "rows" / "LC-S-6041.json").write_text("{}", encoding="utf-8")
    prediction = tmp / "prediction.txt"
    prediction.write_text("3 of 3 reach ch2_wally.\n", encoding="utf-8")
    before = rig.ledger.read_bytes()
    code, text = rig.run(dev_args(out=str(rig.out), prediction_file=str(prediction)))
    eq((code, "R11" in text), (2, True), f"a development batch too: {text[-600:]}")
    eq(rig.ledger.read_bytes(), before, "no development entry was begun")


def case_e2e_out_empty_proceeds(M, tmp):
    rig = graded_rig(M, tmp)
    rig.out.mkdir(parents=True)
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 0, f"CONTROL: an EMPTY --out proceeds (a missing one: e2e_graded_pass): {text[-800:]}")
    eq(rig.entry()["status"], "done", "the batch ran and finished its entry")


# ---------------------------------------------------------------------------------------------------- V-02: the regrade
def batch_with(plans_by_index: dict) -> tuple[list[dict], list[dict]]:
    """healthy_batch with a plan for the chains at these indexes of jobs_of(7101, 6)."""
    jobs = LC.jobs_of(7101, 6)
    return healthy_batch(6, {jobs[at]["chain"]: plan for at, plan in plans_by_index.items()})


def case_grade_batch_foreign_row(M, tmp):
    chains, jobs = batch_with({1: {"L2": {"miss": True}}, 2: {"L4": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "FAIL", "CONTROL: 4 of 6 reach")
    foreign = {**copy.deepcopy(chains[0]), "chain": "LC-S-6041"}
    checks = grade(M, chains + [foreign], jobs)
    reach = by_id(checks, "LC.REACH")
    eq((reach.status, M.batch_verdict(checks)), ("FAIL", "FAIL"), f"a passing row of ANOTHER chain never counts: {reach.text}")
    ok("LC-S-6041: not a registered chain of this batch" in reach.text, reach.text)
    honest, jobs = healthy_batch()
    eq(by_id(grade(M, honest, jobs), "LC.REACH").status, "PASS", "CONTROL: 6 of 6")
    twice = by_id(grade(M, honest + [copy.deepcopy(honest[0])], jobs), "LC.REACH")
    ok(twice.status != "PASS" and "2 rows for one registered chain" in twice.text,
       f"a registered chain with two rows counts neither: {twice.status} {twice.text[:400]}")


def case_grade_dir_foreign_row(M, tmp):
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp, plans={jobs[1]["chain"]: {"L2": {"miss": True}}, jobs[2]["chain"]: {"L4": {"miss": True}}})
    code, text = rig.run(run_args(out=str(rig.out)))
    eq((code, rig.results()["verdict"]), (1, "FAIL"), f"in-run: 4 of 6 reach: {text[-600:]}")
    eq(M.regrade_dir(rig.out)["verdict"], "FAIL", "CONTROL: the offline re-grade agrees")
    passing = json.loads((rig.out / "rows" / f"{jobs[0]['chain']}.json").read_text(encoding="utf-8"))
    # the verifier's P2: a passing row of another batch in rows/ (a reused --out) ...
    (rig.out / "rows" / "LC-S-6041.json").write_text(json.dumps({**passing, "chain": "LC-S-6041"}), encoding="utf-8")
    # ... and a passing row copied over a failing registered chain's file, its chain field unchanged
    (rig.out / "rows" / f"{jobs[1]['chain']}.json").write_text(json.dumps(passing), encoding="utf-8")
    found = M.regrade_dir(rig.out)
    eq(found["verdict"], "FAIL", f"neither row counts (P2 stays FAIL): {found['ignored']}")
    ok(any(i.startswith("rows/LC-S-6041.json: not a registered chain") for i in found["ignored"]), found["ignored"])
    ok(any(i.startswith(f"rows/{jobs[1]['chain']}.json: its chain field 'LC-S-6201'") for i in found["ignored"]),
       found["ignored"])
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        M.grade_dir(rig.out)
    printed = buffer.getvalue()
    ok("IGNORED: rows/LC-S-6041.json" in printed and "OFFLINE RE-GRADE (no ledger write): FAIL" in printed, printed[-800:])
    ok("READ AS STORED" in printed, "grade DIR names the flags it could not re-derive")


def case_regrade_honest(M, tmp):
    rig = graded_rig(M, tmp)
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 0, text[-600:])
    found = M.regrade_dir(rig.out)
    eq((found["verdict"], found["ignored"], found["markers"]), ("PASS", [], []), "CONTROL: the honest batch re-grades PASS")
    eq({c.id: c.status for c in found["checks"]}, {c["id"]: c["status"] for c in rig.results()["checks"]},
       "CONTROL: every check as it was graded in the run")


def case_flipped_continue_not_counted(M, tmp):
    chains, jobs = batch_with({0: {"L5": {"miss": True}}, 1: {"L5": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "FAIL", "CONTROL: 4 of 6 reach")
    for chain in chains[:2]:
        leg = chain["legs"][4]
        leg.update({"continue": True, "reached": True, "why": "C1-C6 held"})
        leg["proof_after"]["held"] = True
        chain["reached_to"] = True
    ok(LC.chain_reaches(chains[0], 5), "the stored flags now say it reaches")
    checks = grade(M, chains, jobs)
    reach = by_id(checks, "LC.REACH")
    eq((reach.status, M.batch_verdict(checks)), ("FAIL", "FAIL"), f"flipped flags over failing facts never count: {reach.text}")
    ok("its stored continue is True, the re-derived rule says no" in reach.text, reach.text)


def case_row_identity_mismatch(M, tmp):
    """(The checker's C2-01) a row whose identity is not the registered job's is IGNORED like a second row, so its chain is
    ABSENT and the batch FAILS. FROM AN IMPURE ORIGINAL (the checker's probe_identity): LC-S-7101's L5 fails purity, so the
    batch fails; filing LC-S-7102's clean row (the same pair) as LC-S-7101, only its chain field renamed, must not grade
    the impure leg away."""
    chains, jobs = healthy_batch()
    leg = chains[0]["legs"][4]
    next(c for c in leg["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
    leg["continue"] = False  # what run_chain writes on a C2 stop
    checks = grade(M, chains, jobs)
    eq((M.batch_verdict(checks), by_id(checks, "LC.REACH").status, by_id(checks, "LC.PURITY").status),
       ("FAIL", "PASS", "FAIL"), "CONTROL: the honest rows, graded as before: 5 of 6 reach, LC-S-7101's L5 impure")
    chains[0] = {**copy.deepcopy(chains[3]), "chain": jobs[0]["chain"]}  # LC-S-7102's clean row filed as LC-S-7101
    checks = grade(M, chains, jobs)
    reach, custody = by_id(checks, "LC.REACH"), by_id(checks, "LC.CUSTODY")
    eq(M.batch_verdict(checks), "FAIL", f"a row of another identity never counts: {graded_ok(checks)}")
    ok(f"{jobs[0]['chain']}: its row is not the registered job's" in reach.text
       and "its seed 7102 is not the registered 7101" in reach.text, f"IGNORED and named with why: {reach.text[:900]}")
    eq((reach.status, reach.n), ("VACUOUS", 5), f"the chain is ABSENT: 5 rows of the 6 registered: {reach.text[:300]}")
    ok(custody.status == "FAIL" and f"not: ['{jobs[0]['chain']}']" in custody.text,
       f"LC.CUSTODY: the registered chain's L1 never ran: {custody.text[:400]}")
    # the earlier direction too: a passing row filed over a failing registered chain
    chains, jobs = batch_with({3: {"L2": {"miss": True}}, 4: {"L2": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "FAIL", "CONTROL: 4 of 6 reach")
    chains[3] = {**copy.deepcopy(chains[0]), "chain": jobs[3]["chain"]}  # LC-S-7101's row filed as LC-S-7102 (same pair)
    checks = grade(M, chains, jobs)
    reach = by_id(checks, "LC.REACH")
    eq(M.batch_verdict(checks), "FAIL", f"a row with another chain's seed and profile never counts: {reach.text[:600]}")
    ok("its seed 7101 is not the registered 7102" in reach.text, reach.text)


def case_row_starter_mismatch(M, tmp):
    """(C2-01) a row whose STARTER alone is not the registered job's, with a party that agrees with that starter (so a
    LC.STARTER over the row's own field would pass), is IGNORED: LC.STARTER judges the REGISTERED starter, never the
    row's. CONTROL: the honest batch passes."""
    chains, jobs = healthy_batch()
    eq(M.batch_verdict(grade(M, chains, jobs)), "PASS", "CONTROL: the honest batch passes")
    chains[0]["starter"] = "MUDKIP"
    chains[0]["legs"][0]["truth_after"]["party_exp"][0][1] = "Mudkip"
    checks = grade(M, chains, jobs)
    reach = by_id(checks, "LC.REACH")
    eq(M.batch_verdict(checks), "FAIL", f"a row of another starter never counts: {graded_ok(checks)}")
    ok("its starter 'MUDKIP' is not the registered 'TREECKO'" in reach.text, reach.text[:800])


def weaken_l5(M, row: dict) -> None:
    """A row's L5 as a forger would leave it: its own proof lowered (VAR 7, no flag), held on its marks, flags flipped."""
    leg = row["legs"][4]
    leg["proof"] = {"flags": {}, "variables": {"RUSTBORO_CITY_STATE": {"number": 0x405A, "at_least": 7}}, "trainers": {}}
    leg["proof_after"] = M.proof_holds(leg["truth_after"]["marks"], leg["proof"])
    ok(leg["proof_after"]["held"], "the row's own (weakened) proof holds on its marks")
    leg.update({"continue": True, "reached": True, "why": "C1-C6 held"})
    row.update({"reached_to": True, "stopped_at": None, "stop_reason": None})


def case_regrade_custody_stored_empty(M, tmp):
    """(The checker's C2-03, its C15b) custody is RE-DERIVED, not read: a row that STORED custody [] for an L2 whose
    --state is not L1's end state fails LC.CUSTODY, and its chain stops at L2."""
    chains, jobs = healthy_batch()
    eq(by_id(grade(M, chains, jobs), "LC.CUSTODY").status, "PASS", "CONTROL: the honest custody")
    leg = chains[0]["legs"][1]
    at = leg["command"].index("--state")
    leg["command"][at + 1] = str(Path(leg["command"][at + 1]).parent.parent / "another-run" / "end_state.ss1")
    eq(leg["custody"], [], "the row stored no custody problem")
    checks = grade(M, chains, jobs)
    custody = by_id(checks, "LC.CUSTODY")
    eq((custody.status, M.batch_verdict(checks)), ("FAIL", "FAIL"), f"re-derived custody: {custody.text[:700]}")
    ok("L2 started from --state" in custody.text, custody.text[:700])
    ok(f"{jobs[0]['chain']} at L2" in by_id(checks, "LC.REACH").text, "and its chain stops at L2 (C5)")


def case_grade_dir_registered_proof(M, tmp):
    """(C2-03, the checker's C17) grade DIR judges each row by the REGISTERED legs' proofs (results.json's legs), never
    the row's own: two rows whose L5 proof was weakened on disk, with their flags flipped, still miss."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp, plans={jobs[0]["chain"]: {"L5": {"miss": True}}, jobs[1]["chain"]: {"L5": {"miss": True}}})
    code, text = rig.run(run_args(out=str(rig.out)))
    eq((code, M.regrade_dir(rig.out)["verdict"]), (1, "FAIL"), f"CONTROL: 4 of 6 reach, in-run and offline: {text[-400:]}")
    for job in jobs[:2]:
        path = rig.out / "rows" / f"{job['chain']}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        weaken_l5(M, row)
        path.write_text(json.dumps(row), encoding="utf-8")
    found = M.regrade_dir(rig.out)
    reach = by_id(found["checks"], "LC.REACH")
    eq((found["verdict"], reach.status), ("FAIL", "FAIL"), f"the registered proof decides: {reach.text[:700]}")


def case_e2e_row_proof_weakened_in_run(M, tmp):
    """(C2-03, the checker's C18) the IN-RUN grade judges by the registered legs too: two rows rewritten on disk after
    their chains ended (a weakened L5 proof, flipped flags), which run_batch reads back, still miss."""
    jobs = LC.jobs_of(6201, 6)

    def tamper() -> list[str]:  # (run_batch reads the leftover processes right after the chains, before the rows)
        for job in jobs[:2]:
            path = rig.out / "rows" / f"{job['chain']}.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            weaken_l5(M, row)
            path.write_text(json.dumps(row), encoding="utf-8")
        return []
    rig = graded_rig(M, tmp, plans={jobs[0]["chain"]: {"L5": {"miss": True}}, jobs[1]["chain"]: {"L5": {"miss": True}}},
                     leftover=tamper)
    code, text = rig.run(run_args(out=str(rig.out)))
    statuses = {c["id"]: c["status"] for c in rig.results()["checks"]}
    eq((code, statuses["LC.REACH"]), (1, "FAIL"), f"4 of 6 reach: the rows' own proofs never count: {text[-600:]}")


def case_e2e_evidence_rederived_reach(M, tmp):
    """(C2-03) the evidence's per-chain line prints the RE-DERIVED reach LC.REACH counted, not the row's stored flag: a
    kept last line rewritten after its chain ended stops that chain by the re-derived rule while its row still says
    reached. CONTROL: an untouched chain reads the same both ways."""
    jobs = LC.jobs_of(6201, 6)

    def tamper() -> list[str]:
        kept = rig.out / jobs[0]["chain"] / "L5" / "world_last.jsonl"
        kept.write_bytes(kept.read_bytes().replace(b'"tiles_learned":', b'"tiles_learned": '))
        return []
    rig = graded_rig(M, tmp, leftover=tamper)
    code, text = rig.run(run_args(out=str(rig.out)))
    row = json.loads((rig.out / "rows" / f"{jobs[0]['chain']}.json").read_text(encoding="utf-8"))
    ok(row["reached_to"], f"the row on disk still says reached: {text[-400:]}")
    lines = Path(rig.results()["evidence"]).read_text(encoding="utf-8").splitlines()
    line = next(found for found in lines if found.startswith(f"  {jobs[0]['chain']} ("))
    ok("reached ch5_rival_meet False (re-derived; the row stored True)" in line, line)
    other = next(found for found in lines if found.startswith(f"  {jobs[1]['chain']} ("))
    ok("reached ch5_rival_meet True (re-derived)" in other, f"CONTROL: an untouched chain: {other}")


def case_kept_file_not_json(M, tmp):
    """(The checker's C13) the kept last line must still be a JSON OBJECT when re-read: a kept file that is not one, filed
    with its own sha256 (the stored last_ok still True), never counts."""
    chains, jobs = batch_with({1: {"L2": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "PASS", "CONTROL: 5 of 6 reach")
    last = chains[0]["legs"][4]
    forged = tmp / "not_an_object.jsonl"  # (a new file: the cached batch's own files are never touched)
    forged.write_bytes(b"[1, 2, 3]\n")
    last["kept_world"], last["kept_world_sha256"] = str(forged), hashlib.sha256(forged.read_bytes()).hexdigest()
    reach = by_id(grade(M, chains, jobs), "LC.REACH")
    eq(reach.status, "FAIL", f"a kept line that is no JSON object never counts: {reach.text[:600]}")
    ok("its kept last line is not a JSON object" in reach.text, reach.text[:800])


def case_kept_file_swapped(M, tmp):
    chains, jobs = batch_with({1: {"L2": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "PASS", "CONTROL: 5 of 6 reach")
    last = chains[0]["legs"][4]
    swapped = tmp / "swapped_world_last.jsonl"  # (a new file: the cached batch's own files are never touched)
    swapped.write_bytes(Path(last["kept_world"]).read_bytes().replace(b'"tiles_learned":', b'"tiles_learned": '))
    last["kept_world"] = str(swapped)
    reach = by_id(grade(M, chains, jobs), "LC.REACH")
    eq(reach.status, "FAIL", f"a kept line that is not the one the row measured never counts: {reach.text[:600]}")
    ok("its kept last line's sha256 is not the row's" in reach.text, reach.text)


def case_row_proof_weakened(M, tmp):
    chains, jobs = batch_with({0: {"L5": {"miss": True}}, 1: {"L5": {"miss": True}}})
    for chain in chains[:2]:
        leg = chain["legs"][4]
        leg["proof"] = {"flags": {}, "variables": {"RUSTBORO_CITY_STATE": {"number": 0x405A, "at_least": 7}}, "trainers": {}}
        leg["proof_after"] = M.proof_holds(leg["truth_after"]["marks"], leg["proof"])
        leg.update({"continue": True, "reached": True})
        ok(leg["proof_after"]["held"], "the row's own (weakened) proof holds on its marks")
    reach = by_id(grade(M, chains, jobs), "LC.REACH")
    eq(reach.status, "FAIL", f"the REGISTERED leg's proof decides, never the row's own: {reach.text[:600]}")


def case_row_leg_names_checked(M, tmp):
    chains, jobs = batch_with({1: {"L2": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "PASS", "CONTROL: 5 of 6 reach")
    chains[0]["legs"][4]["target"] = "ch9_elsewhere"
    reach = by_id(grade(M, chains, jobs), "LC.REACH")
    eq(reach.status, "FAIL", f"a leg the row names otherwise is not the registered leg: {reach.text[:600]}")
    ok("is not the registered L5 ch5_rival_meet" in reach.text, reach.text)


def case_grade_dir_marker_on_disk(M, tmp):
    rig = graded_rig(M, tmp)
    code, text = rig.run(run_args(out=str(rig.out)))
    eq((code, M.regrade_dir(rig.out)["verdict"]), (0, "PASS"), f"CONTROL: no marker: {text[-400:]}")
    for chain in ("LC-S-6201", "LC-C-6203"):
        LC._write_json(rig.out / chain / "L3.KILLED.json", {"cause": "world", "text": "planted after the batch"})
    found = M.regrade_dir(rig.out)
    eq((found["verdict"], len(found["markers"])), ("FAIL", 2),
       f"a disk guard's marker file stops its leg even when the row has none: {found['markers']}")


# ---------------------------------------------------------------------------------------------------- V-03: the hash
#: the test's OWN list of the data the grade reads (a second path: MEASURED 2026-11-05 by an audit hook on `open` while
#: modules.memory, game, pokemon_party and pokemon were imported in a throw-away process, plus the two symbol tables
#: modules/game.py loads for Emerald and the gates' own data), and the AI's plugin
DATA_REQUIRED = ("sandbox-pokebot/modules/data/symbols/pokeemerald.sym",
                 "sandbox-pokebot/modules/data/symbols/patches/pokeemerald.sym",
                 "sandbox-pokebot/modules/data/species.json", "sandbox-pokebot/modules/data/types.json",
                 "sandbox-pokebot/modules/data/moves.json", "sandbox-pokebot/modules/data/natures.json",
                 "sandbox-pokebot/modules/data/abilities.json", "sandbox-pokebot/modules/data/items.json",
                 "ai_player/gates/fixtures/item_flags.json", "ai_player/gates/b1_debt.json",
                 "ai_player/gates/grader_waivers.json", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py")
#: the files the verifier named in the grade's import path (V-03): the scan must find every one (it is not vacuous)
CLOSURE_NAMED = ("ai_player/gates/live_chain.py", "ai_player/gates/live_step5.py", "ai_player/gates/play_harness.py",
                 "ai_player/gates/hands_harness.py", "ai_player/gates/probe_eyes.py", "ai_player/gates/disk_budget.py",
                 "ai_player/gates/check_grader_imports.py", "ai_player/gates/window.py",
                 "ai_player/gates/probe_save_kill.py", "ai_player/gates/probe_end_screen.py",
                 "ai_player/gates/revert_step5.py", "sandbox-pokebot/modules/pokemon.py", "sandbox-pokebot/modules/game.py",
                 "sandbox-pokebot/modules/pokemon_party.py", "sandbox-pokebot/modules/memory.py")


_CLOSURE: dict = {}


def real_closure(M) -> list[str]:
    """M.grader_closure(REPO): computed once for the real module (1.4 s a scan); a mutant's copy always computes its own."""
    if M is not LC:
        return M.grader_closure(REPO)
    if "real" not in _CLOSURE:
        _CLOSURE["real"] = M.grader_closure(REPO)
    return list(_CLOSURE["real"])


def plant(root: Path, rel: str, text: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def case_grader_files_cover_closure(M, tmp):
    closure = real_closure(M)
    eq([rel for rel in closure if rel not in M.GRADER_FILES], [],
       "files the grade imports or runs that the registration does not hash (add them to GRADER_GATES, GRADER_SANDBOX or "
       "GRADER_BOT)")
    eq([rel for rel in M.GRADER_FILES if not (REPO / rel).is_file()], [], "listed files that do not exist")
    eq(len(M.GRADER_FILES), len(set(M.GRADER_FILES)), "no file is listed twice (the bounds text counts them)")


def case_closure_not_vacuous(M, tmp):
    closure = real_closure(M)
    eq([rel for rel in CLOSURE_NAMED if rel not in closure], [], "the scan finds every file the verifier named")
    eq([rel for rel in closure if not rel.startswith(("ai_player/gates/", "sandbox-pokebot/"))], [],
       "the AI's own modules are never followed (they are hashed whole, as ai_code_sha256)")


def case_closure_scan_planted(M, tmp):
    root = tmp / "repo"

    def put(rel: str, text: str) -> None:
        plant(root, rel, text)
    put("ai_player/gates/__init__.py", "")
    # (the checker's C2-05, its C30) every statement body an import can sit in: else (of try, if and for), finally,
    # with, match and a class body, besides the module level, a function and an except block
    put("ai_player/gates/live_chain.py", '"""It never imports ai_player.gates.mentioned."""\n'
                                         "# from ai_player.gates import commented\n"
                                         "from ai_player.gates import top\nfrom ai_player.brain import goals\n"
                                         "try:\n    import json\nexcept ImportError:\n"
                                         "    from ai_player.gates import fallback\n"
                                         "else:\n    from ai_player.gates import in_try_else\n"
                                         "finally:\n    from ai_player.gates import in_finally\n"
                                         "if json:\n    pass\nelse:\n    from ai_player.gates import in_if_else\n"
                                         "for _ in ():\n    pass\nelse:\n    from ai_player.gates import in_for_else\n"
                                         "with open(__file__) as handle:\n    from ai_player.gates import in_with\n"
                                         "match handle:\n    case _:\n        from ai_player.gates import in_match\n\n\n"
                                         "class Holder:\n    from ai_player.gates import in_class\n\n\n"
                                         "def later():\n    from ai_player.gates.inner import x\n    return x\n")
    planted = ("in_try_else", "in_finally", "in_if_else", "in_for_else", "in_with", "in_match", "in_class")
    for name in planted:
        put(f"ai_player/gates/{name}.py", "")
    put("ai_player/gates/top.py", "import modules.pkg.sub\n")
    put("ai_player/gates/inner.py", "from modules.rel import y\n")
    put("ai_player/gates/fallback.py", "")
    put("ai_player/gates/mentioned.py", "")
    put("ai_player/gates/commented.py", "")
    put("ai_player/brain/goals.py", "from modules.ai_only import z\n")
    put("sandbox-pokebot/modules/pkg/__init__.py", "")
    put("sandbox-pokebot/modules/pkg/sub.py", "")
    put("sandbox-pokebot/modules/rel.py", "from .sibling import w\n")
    put("sandbox-pokebot/modules/sibling.py", "")
    put("sandbox-pokebot/modules/ai_only.py", "")
    with mock.patch.object(M, "PATH_ROOTS", ()):
        found = M.grader_closure(root)
    eq(found, sorted(["ai_player/gates/__init__.py", "ai_player/gates/fallback.py", "ai_player/gates/inner.py",
                      "ai_player/gates/live_chain.py", "ai_player/gates/top.py",
                      *(f"ai_player/gates/{name}.py" for name in planted),
                      "sandbox-pokebot/modules/pkg/__init__.py", "sandbox-pokebot/modules/pkg/sub.py",
                      "sandbox-pokebot/modules/rel.py", "sandbox-pokebot/modules/sibling.py",
                      # (the third fix round, C3-H05) the AI's framework import STARTS the closure; its own file is never in it
                      "sandbox-pokebot/modules/ai_only.py"]),
       "a function-local import, one in an except, else, finally, with, match or class body, a relative one and a parent "
       "package are followed, and the framework module an AI file imports; a mention in a docstring or a comment is not, "
       "and the AI's own file is not")


def case_closure_starts(M, tmp):
    """(The checker's C2-02) the closure STARTS from the files the harness and the launcher run by path (PATH_ROOTS) and
    from the plugins the framework loads by name: each is in it and hashed (the purity gate, pokebot.py with the
    requirements and updater it imports, every plugins/*.py, plugins/custom_modes/__init__.py, every custom mode not
    starting with _), and nothing of the AI's own package outside gates/ is."""
    closure = real_closure(M)
    eq([rel for rel in M.PATH_ROOTS if not (REPO / rel).is_file()], [], "every file run by path exists")
    eq([rel for rel in M.PATH_ROOTS if rel not in closure], [], "every file run by path starts the closure")
    plugins = sorted(p.relative_to(REPO).as_posix() for p in (REPO / "sandbox-pokebot" / "plugins").iterdir()
                     if p.name.endswith(".py"))
    modes = sorted(p.relative_to(REPO).as_posix() for p in (REPO / "sandbox-pokebot" / "plugins" / "custom_modes").glob("*.py")
                   if not p.name.startswith("_"))
    ok(len(plugins) >= 8 and len(modes) >= 6, f"the folders the loaders read are not empty: {plugins} {modes}")
    eq([rel for rel in [*plugins, "sandbox-pokebot/plugins/custom_modes/__init__.py", *modes] if rel not in closure], [],
       "every plugin the framework loads by name, with the custom modes' package")
    for rel in ("ai_player/gates/check_purity.py", "sandbox-pokebot/pokebot.py", "sandbox-pokebot/requirements.py",
                "sandbox-pokebot/updater.py", "sandbox-pokebot/plugins/custom_modes_loader.py",
                "sandbox-pokebot/plugins/game_cheats_plugin.py", M.PLUGIN):
        ok(rel in closure and rel in M.GRADER_FILES, f"{rel}: in the closure and hashed")
    eq([rel for rel in closure if rel.startswith("ai_player/") and not rel.startswith("ai_player/gates/")], [],
       "the AI's own modules are never followed")


def case_closure_starts_planted(M, tmp):
    """(C2-02) on a planted tree: the closure follows a file run by path and every plugin the loaders import by name, with
    its parent packages (the custom modes' __init__.py is reached ONLY that way here, as Python runs it), through the
    framework's top-level names (pokebot, requirements, updater, plugins, modules); it never follows what the loaders
    skip (a name not ending in .py, a custom mode starting with _), nor the git-ignored profiles folder."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/__init__.py")
    plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    plant(root, "ai_player/gates/check_purity.py", "from ai_player.gates import gate_helper\n")
    plant(root, "ai_player/gates/gate_helper.py")
    plant(root, "sandbox-pokebot/pokebot.py", "from requirements import check\nfrom updater import run\n"
                                              "from profiles.customcatchfilters import custom_catch_filters\n")
    plant(root, "sandbox-pokebot/requirements.py")
    plant(root, "sandbox-pokebot/updater.py", "import modules.helper\n")
    for name in ("helper", "from_plugin", "from_mode", "never"):
        plant(root, f"sandbox-pokebot/modules/{name}.py")
    plant(root, "sandbox-pokebot/plugins/loaded_plugin.py", "from modules import from_plugin\n")
    plant(root, "sandbox-pokebot/plugins/notes.txt", "import modules.never\n")
    plant(root, "sandbox-pokebot/plugins/custom_modes/__init__.py")
    plant(root, "sandbox-pokebot/plugins/custom_modes/mode_a.py", "import modules.from_mode\n")
    plant(root, "sandbox-pokebot/plugins/custom_modes/_private.py", "import modules.never\n")
    plant(root, "sandbox-pokebot/profiles/customcatchfilters.py")
    with mock.patch.object(M, "PATH_ROOTS", ("ai_player/gates/check_purity.py", "sandbox-pokebot/pokebot.py")):
        found = M.grader_closure(root)
    eq(found, ["ai_player/gates/__init__.py", "ai_player/gates/check_purity.py", "ai_player/gates/gate_helper.py",
               "ai_player/gates/live_chain.py", "sandbox-pokebot/modules/from_mode.py",
               "sandbox-pokebot/modules/from_plugin.py", "sandbox-pokebot/modules/helper.py",
               "sandbox-pokebot/plugins/custom_modes/__init__.py", "sandbox-pokebot/plugins/custom_modes/mode_a.py",
               "sandbox-pokebot/plugins/loaded_plugin.py", "sandbox-pokebot/pokebot.py", "sandbox-pokebot/requirements.py",
               "sandbox-pokebot/updater.py"],
       "the starts by path and by name, their imports and parent packages; never notes.txt, _private.py, never.py or "
       "profiles/")
    with mock.patch.object(M, "PATH_ROOTS", ()):
        eq([rel for rel in M.grader_closure(root) if rel.endswith(("check_purity.py", "pokebot.py"))], [],
           "CONTROL: a file run by path is in the closure only as a start (no import reaches these)")


# ---------------------------------------------------------------------------------------------------- C2-02: runs by path
#: the first element of a Python argv besides `sys.executable` (a launcher or interpreter named by its program name)
PYTHONS = ("py", "py.exe", "python", "python.exe", "python3", "pythonw", "pythonw.exe")
#: (C2-02) path-built argvs of the scanned code that start NO file the closure must start from, each with WHY. EXACT: an
#: entry the scan no longer finds fails the test too (a stale exemption is a hole)
PATH_RUN_EXEMPT = {
    ("ai_player/gates/revert_step5.py", "run_step5_tests.py"):
        "revert_step5 writes it from its own DRIVER constant into a throw-away copy, so the generator is what is hashed",
    ("sandbox-pokebot/modules/endless_x4.py", "*args"):
        "a frozen bundle (is_bundled_app()): sys.executable is the bot itself and there is no script",
    ("sandbox-pokebot/modules/gui/emulator_controls.py", "tools/story-dev/endless_runs.py"):
        "a button of the Tk emulator controls: a leg runs headless (host/launcher.py bot_command passes -hl), so no "
        "button is pressed",
}


def _is_python(node) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == "executable" and isinstance(node.value, ast.Name) \
            and node.value.id == "sys":
        return True
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.lower() in PYTHONS


class PathEval:
    """A SECOND PATH (test side): a small static evaluator of the path expressions an argv names its script by. It reads
    constants, `__file__`, Path(...)/str(...)/os.fspath(...), .resolve(), .parent, .parents[k], .name, `a / b`, a
    conditional's two branches and a name's assignments in its function (then the enclosing ones, then the module). A
    parameter, or a call it cannot see through, is an UNKNOWN base: the parts joined after it are kept as a suffix and
    resolved against the repository and the build root. What it cannot read is UNRESOLVED, which fails (never a pass)."""

    def __init__(self, repo: Path, path: Path, tree: ast.Module) -> None:
        self.repo, self.path = repo, path
        self.parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        self.bound: dict = {}  # scope -> name -> [value expression, or None for a binding it cannot read]
        for node in ast.walk(tree):
            targets: list[tuple[ast.AST, ast.AST | None]] = []
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    targets += ([(target, node.value)] if isinstance(target, ast.Name) else
                                [(t, None) for t in ast.walk(target) if isinstance(t, ast.Name)])
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and isinstance(node.target, ast.Name):
                targets.append((node.target, node.value))
            elif isinstance(node, (ast.AugAssign, ast.For, ast.AsyncFor, ast.comprehension)):
                targets += [(t, None) for t in ast.walk(node.target) if isinstance(t, ast.Name)]
            elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                targets += [(t, None) for t in ast.walk(node.optional_vars) if isinstance(t, ast.Name)]
            for target, value in targets:
                self.bound.setdefault(self.scope(target), {}).setdefault(target.id, []).append(value)

    def scope(self, node):
        node = self.parent.get(node)
        while node is not None and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            node = self.parent.get(node)
        return node

    @staticmethod
    def params(func) -> set[str]:
        a = func.args
        return {x.arg for x in (*a.posonlyargs, *a.args, *a.kwonlyargs, *(v for v in (a.vararg, a.kwarg) if v))}

    def lookup(self, name: str, scope, depth: int) -> list:
        while True:
            values = (self.bound.get(scope) or {}).get(name)
            if values is not None:
                return [v for value in values for v in (self.eval(value, scope, depth + 1) if value is not None
                                                        else [("unknown",)])]
            if scope is None or name in self.params(scope):
                return [("unknown",)]
            scope = self.scope(scope)

    def eval(self, node, scope, depth: int = 0) -> list:
        if depth > 25:
            return [("unknown",)]
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [("str", node.value)]
        if isinstance(node, ast.Name):
            return [("path", self.path)] if node.id == "__file__" else self.lookup(node.id, scope, depth)
        if isinstance(node, ast.IfExp):
            return self.eval(node.body, scope, depth + 1) + self.eval(node.orelse, scope, depth + 1)
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name in ("str", "Path", "PurePath", "fspath") and len(node.args) == 1 and not node.keywords:
                return self.eval(node.args[0], scope, depth + 1)
            if isinstance(func, ast.Attribute) and name in ("resolve", "absolute") and not node.args:
                return self.eval(func.value, scope, depth + 1)
            return [("unknown",)]
        if isinstance(node, ast.Attribute) and node.attr in ("parent", "name"):
            out = []
            for value in self.eval(node.value, scope, depth + 1):
                if value[0] == "path":
                    out.append(("path", value[1].parent) if node.attr == "parent" else ("str", value[1].name))
                elif value[0] == "suffix" and node.attr == "name":
                    out.append(("str", value[1][-1]))
                else:
                    out.append(("unknown",))
            return out
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents" \
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            return [("path", v[1].parents[node.slice.value]) if v[0] == "path" else ("unknown",)
                    for v in self.eval(node.value.value, scope, depth + 1)]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            out = []
            for left in self.eval(node.left, scope, depth + 1):
                for right in self.eval(node.right, scope, depth + 1):
                    if right[0] != "str":
                        out.append(("unknown",))
                    elif left[0] == "path":
                        out.append(("path", left[1] / right[1]))
                    elif left[0] == "suffix":
                        out.append(("suffix", (*left[1], right[1])))
                    elif left[0] == "str":
                        out.append(("suffix", (left[1], right[1])))
                    else:
                        out.append(("suffix", (right[1],)))
            return out
        return [("unknown",)]


def path_runs(M, repo: Path, rel: str) -> list[tuple[int, str, str]]:
    """Every script a Python argv display ([sys.executable or "py"/"python", flags..., SCRIPT, ...]) in `rel` runs, from
    its SYNTAX (a mention in a comment or a string is no argv): (line, kind, key), kind "file" (key: the repository-relative
    file), "module" (a `-m` module of the repository) or "unresolved" (key: the expression). `-c` code and `-m` modules
    outside the repository (pip, ai_player: the AI's code) start nothing the closure must start from."""
    tree = ast.parse((repo / rel).read_bytes())
    displays = [node for node in ast.walk(tree)
                if isinstance(node, (ast.List, ast.Tuple)) and node.elts and _is_python(node.elts[0])]
    if not displays:
        return []
    evaluator = PathEval(repo, repo / rel, tree)
    found: list[tuple[int, str, str]] = []
    for node in displays:
        at, script = 1, None
        while at < len(node.elts):
            element = node.elts[at]
            if isinstance(element, ast.Constant) and isinstance(element.value, str) and element.value.startswith("-"):
                if element.value in ("-m", "-c"):
                    script = (element.value, node.elts[at + 1] if at + 1 < len(node.elts) else None)
                    break
                at += 2 if element.value in ("-X", "-W") else 1
                continue
            script = ("script", element)
            break
        if script is None or script[0] == "-c":
            continue
        kind, expr = script
        if kind == "-m":
            name = expr.value if isinstance(expr, ast.Constant) and isinstance(expr.value, str) else None
            module = M._closure_file(repo, name) if name else None
            if name is None:
                found.append((node.lineno, "unresolved", f"-m {ast.unparse(expr) if expr is not None else ''}"))
            elif module is not None:
                found.append((node.lineno, "module", module.relative_to(repo).as_posix()))
            continue
        if isinstance(expr, ast.Starred):
            found.append((node.lineno, "unresolved", ast.unparse(expr)))
            continue
        for value in evaluator.eval(expr, evaluator.scope(node)):
            if value[0] == "path":
                try:
                    found.append((node.lineno, "file", Path(os.path.normpath(value[1])).relative_to(repo).as_posix()))
                except ValueError:
                    found.append((node.lineno, "unresolved", str(value[1])))
            elif value[0] in ("suffix", "str"):
                joined = "/".join(value[1]) if value[0] == "suffix" else value[1]
                hits = [base + joined for base in ("", "sandbox-pokebot/") if (repo / (base + joined)).is_file()]
                found.append((node.lineno, "file", hits[0]) if len(hits) == 1 else (node.lineno, "unresolved", joined))
            else:
                found.append((node.lineno, "unresolved", ast.unparse(expr)))
    return found


def path_run_problems(M, repo: Path, files: list[str]) -> tuple[list[str], set, set]:
    """(C2-02) Over `files`: (each script run by path that is not a closure ROOT (M.PATH_ROOTS), the PATH_RUN_EXEMPT keys
    found, every (file, script) found). A file that runs ITSELF is in the closure already; the AI's own code (ai_player/
    outside gates/ and evidence/) is hashed whole (ai_code_sha256)."""
    problems: list[str] = []
    used, seen = set(), set()
    for rel in files:
        for line, kind, key in path_runs(M, repo, rel):
            seen.add((rel, key))
            if kind in ("file", "module") and (key == rel or key in M.PATH_ROOTS or (
                    key.startswith("ai_player/") and not key.startswith(("ai_player/gates/", "ai_player/evidence/")))):
                continue
            if (rel, key) in PATH_RUN_EXEMPT:
                used.add((rel, key))
                continue
            problems.append(f"{rel}:{line} runs {key} ({kind}) by path, and it is no closure root (PATH_ROOTS)")
    return problems, used, seen


def ai_code(repo: Path) -> list[str]:
    """The AI's own code, the launcher among it (ai_player/ outside gates/ and evidence/)."""
    return sorted(p.relative_to(repo).as_posix() for p in (repo / "ai_player").rglob("*.py")
                  if p.relative_to(repo / "ai_player").parts[0] not in ("gates", "evidence") and "__pycache__" not in p.parts)


def case_path_runs_are_roots(M, tmp):
    """(C2-02) every script a path-built argv of the HARNESS (the closure's files) or the LAUNCHER (the AI's code) runs is
    a closure root, the file itself, the AI's own code or an exact, explained exemption. Not vacuous: the scan sees the
    launcher run the purity gate and pokebot.py and live_step5 run the truth harness."""
    problems, used, seen = path_run_problems(M, REPO, [*real_closure(M), *ai_code(REPO)])
    eq(problems, [], "a script the harness or the launcher runs by path that the closure does not start from")
    eq(sorted(set(PATH_RUN_EXEMPT) - used), [], "every exemption is still found (a stale one is a hole)")
    for want in (("ai_player/host/launcher.py", "ai_player/gates/check_purity.py"),
                 ("ai_player/host/launcher.py", "sandbox-pokebot/pokebot.py"),
                 ("ai_player/gates/live_step5.py", "ai_player/gates/play_harness.py")):
        ok(want in seen, f"the scan sees {want[0]} run {want[1]}: {sorted(seen)}")


def case_path_run_scan_planted(M, tmp):
    """(C2-02) the scan on a planted file: FAULT, a script run by path that is no root goes red (the closure's starts are
    patched); CONTROL, the same script listed as a root does not; a mention in a docstring or a comment, a `-c`, a `-m`
    of the AI's code and a file that runs itself never count; a parameter base is resolved by its suffix."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py",
          '"""It never runs subprocess.run([sys.executable, str(GATES / "mentioned.py")])."""\n'
          "# subprocess.run([sys.executable, str(GATES / 'commented.py')])\n"
          "import subprocess\nimport sys\nfrom pathlib import Path\n\nGATES = Path(__file__).resolve().parent\n\n\n"
          "def a():\n    subprocess.run([sys.executable, str(GATES / 'evil.py')])\n\n\n"
          "def b():\n    subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), 'child'])\n\n\n"
          "def c():\n    subprocess.run([sys.executable, '-m', 'ai_player', 'run'])\n\n\n"
          "def d():\n    subprocess.run([sys.executable, '-c', 'print(1)'])\n\n\n"
          "def e(root):\n    script = root / 'ai_player' / 'gates' / 'rooted.py'\n    subprocess.run([sys.executable, str(script)])\n\n\n"
          "def f(build_root):\n    return ['py', '-3.12', str(build_root / 'pokebot.py'), 'x']\n")
    for rel in ("ai_player/gates/evil.py", "ai_player/gates/rooted.py", "ai_player/gates/mentioned.py",
                "ai_player/gates/commented.py", "sandbox-pokebot/pokebot.py"):
        plant(root, rel)
    roots = ("ai_player/gates/rooted.py", "sandbox-pokebot/pokebot.py")
    with mock.patch.object(M, "PATH_ROOTS", roots):
        problems, _, seen = path_run_problems(M, root, ["ai_player/gates/live_chain.py"])
    eq(len(problems), 1, f"FAULT: exactly the unlisted script: {problems}")
    ok("ai_player/gates/evil.py" in problems[0], problems[0])
    eq(sorted(key for _, key in seen), ["ai_player/gates/evil.py", "ai_player/gates/live_chain.py",
                                        "ai_player/gates/rooted.py", "sandbox-pokebot/pokebot.py"],
       "found: the root, the suffix behind a parameter, the file itself; never a mention, a -c or the AI's -m")
    with mock.patch.object(M, "PATH_ROOTS", (*roots, "ai_player/gates/evil.py")):
        problems, _, _ = path_run_problems(M, root, ["ai_player/gates/live_chain.py"])
    eq(problems, [], "CONTROL: the same script listed as a root")


def tops_of(M, repo: Path, files: list[str]) -> set[str]:
    """(A SECOND PATH, test side: ast.walk, not the driver's statement walk) every top-level name an absolute import of
    `files` names."""
    tops: set[str] = set()
    for rel in files:
        for node in ast.walk(ast.parse((repo / rel).read_bytes())):
            if isinstance(node, ast.Import):
                tops.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                tops.add(node.module.split(".")[0])
    return tops


def case_closure_toplevel_names(M, tmp):
    """(C2-02, moved into the driver by the third fix round, C3-H02: R12's `toplevel_problems`) every top-level name of the
    framework an import of the closure names is FOLLOWED (a CLOSURE_ROOTS prefix) or a declared exemption
    (TOPLEVEL_NOT_FOLLOWED, EXACT: each is imported by a closure file, found by a second path). FAULT (planted): pokebot.py
    importing a new top-level module beside it, and a gates file importing a sibling bare, are each named; CONTROL: the
    real tree (whatever git-ignored folders it holds, the emulator's mgba among them on the main checkout)."""
    tops = tops_of(M, REPO, real_closure(M))
    eq(M.toplevel_problems(REPO, M.closure_scan(REPO)["tops"]), [], "an entry of a script folder that shadows a module")
    eq(sorted(name for _, name in M.TOPLEVEL_NOT_FOLLOWED if name not in tops), [],
       "every exemption names a module a closure file imports (a stale exemption is a hole)")
    eq(sorted(n for n in tops - {p.split(".")[0] for p, _ in M.CLOSURE_ROOTS}
              if (REPO / "sandbox-pokebot" / f"{n}.py").is_file() and ("sandbox-pokebot", n) not in M.TOPLEVEL_NOT_FOLLOWED),
       [], "a top-level module of sandbox-pokebot a closure file imports that is neither followed nor exempt")
    root = tmp / "repo"
    plant(root, "sandbox-pokebot/pokebot.py", "import modules.main\nfrom newtop import thing\n")
    plant(root, "sandbox-pokebot/newtop.py")
    plant(root, "ai_player/gates/live_chain.py", "import window\n")
    plant(root, "ai_player/gates/window.py")
    problems = M.toplevel_problems(root, tops_of(M, root, ["sandbox-pokebot/pokebot.py", "ai_player/gates/live_chain.py"]))
    eq(len(problems), 2, f"FAULT: both named: {problems}")
    ok("sandbox-pokebot/newtop.py" in " ".join(problems) and "ai_player/gates/window.py" in " ".join(problems), problems)


def case_changed_path_run_refused(M, tmp):
    """(C2-02) after registration, an edit of the purity gate, of pokebot.py, or of a plugin the framework loads by name is
    REFUSED by ledger.begin (the checker's probe_unhashed edits; each was accepted before this round)."""
    for name, rel in (("gate", "ai_player/gates/check_purity.py"), ("pokebot", "sandbox-pokebot/pokebot.py"),
                      ("loader", "sandbox-pokebot/plugins/custom_modes_loader.py"),
                      ("cheats", "sandbox-pokebot/plugins/game_cheats_plugin.py")):
        refused_after(M, tmp / name, lambda repo, rel=rel: edited(repo / rel, "import ", "import  "))


def unlisted_import(repo: Path):
    """(C2-05) the planted fault: live_chain.py in the fake repository imports a gates file GRADER_FILES does not list
    (created for the block, removed after; live_chain.py's bytes restored)."""
    @contextlib.contextmanager
    def block():
        helper = plant(repo, "ai_player/gates/unlisted_helper.py", "x = 1\n")
        try:
            with edited(repo / "ai_player" / "gates" / "live_chain.py", "from ai_player.gates import ledger  # noqa: E402",
                        "from ai_player.gates import ledger  # noqa: E402\n"
                        "from ai_player.gates import unlisted_helper  # noqa: E402,F401"):
                yield
        finally:
            helper.unlink(missing_ok=True)
    return block()


def case_closure_enforced_register(M, tmp):
    """(The checker's C2-05) `register` is REFUSED (R12), naming the file, with the ledger's bytes unchanged, while the
    grader's import closure finds a file GRADER_FILES does not hash. CONTROL: the same tree without that import
    registers."""
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    path.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    before = path.read_bytes()
    buffer = io.StringIO()
    with unlisted_import(repo), contextlib.redirect_stdout(buffer):
        code = M.register_run("ch5", None, repo=repo, path=path)
    eq(code, 2, f"refused: {buffer.getvalue()[-600:]}")
    ok("R12" in buffer.getvalue() and "ai_player/gates/unlisted_helper.py" in buffer.getvalue(), buffer.getvalue()[-600:])
    eq(path.read_bytes(), before, "the ledger is unchanged")
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = M.register_run("ch5", None, repo=repo, path=path)
    eq(code, 0, f"CONTROL: a tree whose whole closure is hashed registers: {buffer.getvalue()[-600:]}")
    eq(ledger.load(path)["entries"][-1]["status"], "registered", "registered")


def case_closure_enforced_run(M, tmp):
    """(C2-05) a GRADED run is refused (R12) BEFORE ledger.begin while the closure has a file GRADER_FILES does not hash:
    the registration stays unspent, the ledger's bytes unchanged, no chain started. CONTROL: the real tree's closure is
    hashed whole."""
    repo = fake_repo(tmp)
    rig = graded_rig(M, tmp / "rig")
    rig.deps.closure = lambda: M.closure_missing(repo)
    before = rig.ledger.read_bytes()
    with unlisted_import(repo):
        code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 2, f"refused: {text[-600:]}")
    ok("R12" in text and "ai_player/gates/unlisted_helper.py" in text, text[-600:])
    eq((rig.entry()["status"], rig.ledger.read_bytes() == before, rig.handles), ("registered", True, []),
       "the registration is not spent and no chain started")
    missing, size, _ = M.closure_missing(REPO)
    eq(missing, [], f"CONTROL: the real tree's closure ({size} files) is hashed whole")


def case_grader_data_hashed(M, tmp):
    eq([rel for rel in DATA_REQUIRED if rel not in M.GRADER_FILES], [], "the data the grade reads is hashed")


def case_changed_decoder_refused(M, tmp):
    refused_after(M, tmp / "pokemon", lambda repo: edited(repo / "sandbox-pokebot/modules/pokemon.py", "import ",
                                                          "import  "))
    refused_after(M, tmp / "sym", lambda repo: edited(repo / "sandbox-pokebot/modules/data/symbols/pokeemerald.sym",
                                                      " ", "  "))
    refused_after(M, tmp / "gates", lambda repo: edited(repo / "ai_player/gates/disk_budget.py", "import ", "import  "))


def case_crlf_only_accepted(M, tmp):
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    M.register((6201, 6206), numbers(M, repo), "test", path=path)
    target = repo / "ai_player" / "gates" / "live_step5.py"
    with restored(target):
        data = target.read_bytes()
        lf = data.replace(b"\r\n", b"\n")
        changed = lf.replace(b"\n", b"\r\n") if data == lf else lf
        ok(changed != data, "the line endings really changed")
        target.write_bytes(changed)
        entry, _ = M.begin("graded", (6201, 6206), numbers(M, repo), "tree", path=path)
    eq(entry["status"], "started", "CONTROL (by design): a change of line endings alone is not refused")


# ---------------------------------------------------------------------------------------------------- V-04: what counts
def case_verdict_impure_l5_fails(M, tmp):
    chains, jobs = healthy_batch()
    leg = chains[0]["legs"][4]
    next(c for c in leg["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
    leg["continue"] = False  # what run_chain writes on a C2 stop
    checks = grade(M, chains, jobs)
    eq((by_id(checks, "LC.REACH").status, by_id(checks, "LC.PURITY").status), ("PASS", "FAIL"), "5 of 6 reach; L5 impure")
    eq(M.batch_verdict(checks), "FAIL", "one impure leg fails the BATCH, even with 5 of 6 reaching")


def case_verdict_stale_l5_fails(M, tmp):
    chains, jobs = batch_with({0: {"L5": {"stale": True}}})
    checks = grade(M, chains, jobs)
    eq((by_id(checks, "LC.REACH").status, by_id(checks, "LC.THIS_RUN").status), ("PASS", "FAIL"),
       "5 of 6 reach; one L5 stale")
    eq(M.batch_verdict(checks), "FAIL", "one stale leg fails the BATCH")


def case_verdict_wrong_starter_fails(M, tmp):
    chains, jobs = batch_with({0: {"L1": {"wrong_species": True}}})
    checks = grade(M, chains, jobs)
    eq((by_id(checks, "LC.REACH").status, by_id(checks, "LC.STARTER").status), ("PASS", "FAIL"),
       "6 of 6 reach; one wrong starter")
    eq(M.batch_verdict(checks), "FAIL", "a wrong starter fails the BATCH")


def graded_ids(bounds: str) -> set[str]:
    """The ids the bounds text lists between 'GRADED (' and 'REPORTED ('."""
    lines = bounds.splitlines()
    start = next(at for at, line in enumerate(lines) if line.startswith("GRADED ("))
    end = next(at for at, line in enumerate(lines) if line.startswith("REPORTED ("))
    return {found.group(1) for line in lines[start + 1:end] if (found := re.match(r"(LC\.[A-Z_]+)", line))}


def case_graded_kinds_match_bounds(M, tmp):
    chains, jobs = healthy_batch()
    listed = graded_ids(M.bounds_text("ch5_rival_meet", LC.legs_of("ch5_rival_meet", real_milestones()), jobs, 5))
    ok({"LC.REACH", "LC.PURITY", "LC.THIS_RUN", "LC.STARTER", "LC.CUSTODY", "LC.MEMORY", "LC.FROZEN",
        "LC.LEFTOVER"} <= listed, f"the bounds text's GRADED list: {sorted(listed)}")
    kinds = {c.id: c.kind for c in grade(M, chains, jobs)}
    eq(sorted(i for i in listed if kinds.get(i) != "GRADED"), [], "every check the bounds text lists as GRADED is GRADED")
    eq(sorted(i for i, kind in kinds.items() if kind == "GRADED" and i not in listed), [], "and every GRADED one is listed")


# ---------------------------------------------------------------------------------------------------- V-05: guards
def case_watchdog_value(M, tmp):
    legs = M.legs_of("ch5_rival_meet", real_milestones())
    eq(M.chain_watchdog_seconds(legs), 25800, "ch5: 5 x (3,600 + 300 + 2 x 600) + 300, as the docstring says")
    eq(M.chain_watchdog_seconds([{"wall": 100.0}, {"wall": 50.0}]), 3450, "per leg: wall + 300 + 2 x 600; then + 300")
    ok("each leg's wall + 300 s + two 600 s truth reads, + 300 s" in M.bounds_text("ch5_rival_meet", legs,
                                                                                   LC.jobs_of(6201, 6), 5), "registered")


def case_world_grew_larger_graded(M, tmp):
    def plant(name: str) -> tuple[Path, int]:
        run_dir = tmp / name
        run_dir.mkdir(parents=True)
        (run_dir / "world.jsonl").write_text(snapshot(1, 1) + "\n" + snapshot(2, 5) + "\n", encoding="utf-8")
        return run_dir, (run_dir / "world.jsonl").stat().st_size
    run_dir, first = plant("steady")
    row: dict = {"notes": []}
    M.finish_leg(row, run_dir, tmp / "kept_steady")
    eq((row["world_file"]["bytes"], row["notes"]), (first, []), "CONTROL: a file that did not grow is graded at its size")
    run_dir, first = plant("grew")
    real = M.measure_then_delete

    def grows(path):  # the AI's process wrote 4,096 more bytes between the first size and the deletion
        with open(path, "ab") as handle:
            handle.write(b" " * 4096)
        return real(path)
    row = {"notes": []}
    with mock.patch.object(M, "measure_then_delete", grows):
        M.finish_leg(row, run_dir, tmp / "kept_grew")
    eq(row["world_file"]["bytes"], first + 4096, "the LARGER size is graded")
    ok(any("the larger is graded" in note for note in row["notes"]), row["notes"])
    row.update({k: v for k, v in base_row(tmp).items() if k in ("chain", "leg", "target", "status", "checks", "proof_after",
                                                                 "guard_killed", "custody")})
    with mock.patch.object(M, "WORLD_MAX_BYTES", first + 1):
        go, why = M.continue_after(row, False)
    ok(not go and "C3 " in why, f"under the cap at first and over it at its deletion: the chain stops: {why}")


def case_kept_outside_repo(M, tmp):
    """The kept last line is written under --out, which R1 keeps outside the repository (case_r1), and never beside the
    run in the chain's profile (the build root, inside the repository). (Whether this test's own temp --out lies outside
    the repository is the runner's environment, not the driver's: the external mutant runner puts TEMP in its copy.)"""
    chain, _, job = play(M, tmp)
    out, build = Path(job["out"]).resolve(), Path(job["build_root"]).resolve()
    for leg in chain["legs"]:
        kept = Path(leg["kept_world"]).resolve()
        eq(kept, (out / job["chain"] / leg["leg"] / "world_last.jsonl").resolve(), f"{leg['leg']}: under --out")
        ok(not kept.is_relative_to(build) and not kept.is_relative_to(Path(leg["run_dir"]).resolve()),
           f"{leg['leg']}'s kept last line is not in the profiles or its run folder: {kept}")
    ok((M.run_refusal(run_args(out="C:/R/repo/out"), facts_of(out=Path("C:/R/repo/out"))) or "").startswith("R1"),
       "and R1 refuses an --out inside the repository")


def case_dev_partial_overlap_refused(M, tmp):
    path = tmp / "ledger.json"
    ledger.begin("story", "live_chain", "development", 6041, 6043, "x" * 64, "tree", path=path)
    for first, last in ((6042, 6044), (6040, 6041), (6043, 6050), (6038, 6048)):
        eq([e["first"] for e in M.seeds_named(first, last, path)], [6041], f"{first}-{last} overlaps 6041-6043")
    for first, last in ((6044, 6046), (6038, 6040)):
        eq(M.seeds_named(first, last, path), [], f"CONTROL: {first}-{last} does not")
    rig = Rig(M, tmp / "rig")
    shutil.copy2(path, rig.ledger)
    prediction = tmp / "prediction.txt"
    prediction.write_text("2 of 3.\n", encoding="utf-8")
    before = rig.ledger.read_bytes()
    code, text = rig.run(dev_args(first_seed=6042, out=str(rig.out), prediction_file=str(prediction)))
    eq(code, 2, f"6042-6044 overlaps 6041-6043 at two seeds: refused (CH-15): {text[-500:]}")
    ok("R3" in text and "would replay" in text, text[-500:])
    eq(rig.ledger.read_bytes(), before, "the ledger is unchanged")


def case_e2e_leftover_reported(M, tmp):
    reads: list[bool] = []

    def leftover() -> list[str]:
        reads.append(len(rig.handles) == 6 and all(h.code is not None for h in rig.handles))
        return ["4242 C:\\Python312\\python.exe -B live_chain.py child ai-livechain-6201.job.json"]
    rig = graded_rig(M, tmp, leftover=leftover)
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"a process left after the batch fails it: {text[-600:]}")
    eq(reads, [True], "read ONCE, after every chain ended")
    results = rig.results()
    ok(results["leftover"] and "ai-livechain-6201" in results["leftover"][0], results["leftover"])
    eq({c["id"]: c["status"] for c in results["checks"]}["LC.LEFTOVER"], "FAIL", "LC.LEFTOVER")
    evidence = Path(results["evidence"]).read_text(encoding="utf-8")
    ok(any(line.startswith("leftover processes: ") and "ai-livechain-6201.job.json" in line
           for line in evidence.splitlines()), "named in the evidence")


def short_scratch() -> Path:
    """A new folder with a SHORT path for throw-away git repositories, removed by the caller (`remove_tree`). MEASURED
    2026-11-05: under the external mutant runner's deep TEMP (it nests TEMP in its copy) git fails on Windows' path
    limit: object files past 260 characters ("Filename too long"), and a push, whose local receive-pack runs inside the
    bare repository, past the working folder's limit even with core.longpaths ("not a git repository: '.'"). So: this
    process's temp folder when its path is short, else the user's own temp folder."""
    for base in (Path(tempfile.gettempdir()), Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "Temp"):
        if base.is_dir() and len(str(base.resolve())) <= 100:
            return Path(tempfile.mkdtemp(prefix="lc_git_", dir=base))
    return Path(tempfile.mkdtemp(prefix="lc_git_"))


def remove_tree(path: Path) -> None:
    """shutil.rmtree that also removes git's READ-ONLY object files (Windows refuses to delete them as they are); a file
    that still cannot be removed is left (a stray temp file never fails the case it served)."""
    def writable_then_retry(func, name, exc):
        try:
            os.chmod(name, 0o700)
            func(name)
        except OSError:
            pass
    shutil.rmtree(path, onexc=writable_then_retry)


def case_git_state_scratch(M, tmp):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    def git(cwd: Path, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                               "-c", "core.autocrlf=false", *args], cwd=str(cwd), capture_output=True, check=True,
                              text=True, env=env).stdout.strip()
    base = short_scratch()
    try:
        origin, work = base / "origin.git", base / "work"
        git(base, "init", "-q", "--bare", "-b", "main", str(origin))
        git(base, "init", "-q", "-b", "main", str(work))
        (work / "t.txt").write_bytes(b"a\n")
        git(work, "add", "t.txt")
        git(work, "commit", "-q", "-m", "c1")
        git(work, "remote", "add", "origin", str(origin))
        git(work, "push", "-q", "origin", "main")
        with mock.patch.dict(os.environ, env, clear=True):
            clean = M.git_state(work)
            (work / "t.txt").write_bytes(b"bb\n")
            tracked = M.git_state(work)
            (work / "t.txt").write_bytes(b"a\n")
            (work / "u.txt").write_bytes(b"u\n")
            untracked = M.git_state(work)
        git(work, "add", "u.txt")
        git(work, "commit", "-q", "-m", "c2")
        with mock.patch.dict(os.environ, env, clear=True):
            ahead = M.git_state(work)
    finally:
        remove_tree(base)
    eq((clean["head"] == clean["origin"], clean["dirty"], clean.get("error")), (True, [], None),
       f"CONTROL: clean and pushed: {clean}")
    ok(any("t.txt" in line for line in tracked["dirty"]), f"a changed TRACKED file is dirty: {tracked}")
    eq(untracked["dirty"], [], f"an UNTRACKED file is not (--untracked-files=no): {untracked}")
    ok(ahead["head"] and ahead["head"] != ahead["origin"], f"a commit not pushed: HEAD is not origin/main: {ahead}")


def case_abort_before_leg(M, tmp):
    def pre(job):
        Path(job["out"]).mkdir(parents=True, exist_ok=True)
        (Path(job["out"]) / "ABORT.txt").write_text("under 30 GB free\n", encoding="utf-8")
    chain, stub, _ = play(M, tmp / "before", pre=pre)
    eq(stub.calls, [], "ABORT.txt before L1: no leg is launched")
    ok(all("ABORTED by the harness" in leg["reason"] for leg in chain["legs"]), chain["legs"][0]["reason"])
    chain, stub, _ = play(M, tmp / "during", {"L2": {"write_abort": True}})
    eq(len(stub.calls), 2, "ABORT.txt written during L2: L3 is never launched (the pre-leg check)")
    eq([leg["status"] for leg in chain["legs"]], ["RAN", "RAN", "NOT RUN", "NOT RUN", "NOT RUN"], "L3-L5 NOT RUN")
    ok("ABORTED by the harness" in chain["legs"][2]["reason"], chain["legs"][2]["reason"])


def case_starter_floor(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][0]["truth_after"]["party_exp"] = []
    eq(by_id(grade(M, chains, jobs), "LC.STARTER").status, "PASS", "CONTROL: 5 of 6 chains judged (the floor is 5)")
    chains[1]["legs"][0]["truth_after"]["party_exp"] = []
    checks = grade(M, chains, jobs)
    eq(by_id(checks, "LC.STARTER").status, "VACUOUS", "4 chains judged: under the floor of 5")
    eq(M.batch_verdict(checks), "FAIL", "a VACUOUS starter check fails the batch")


def case_starter_unread_ot_and_tid(M, tmp):
    """(The verifier's V02, a narrow gap that predated the fix rounds) a lead whose owner (OT) AND the player's TID were both
    unread (None == None) is never proved the player's own: LC.STARTER fails. CONTROL: grade_control (both read)."""
    chains, jobs = healthy_batch()
    after = chains[0]["legs"][0]["truth_after"]
    after["party_ot"], after["player_tid"] = [], None
    starter = by_id(grade(M, chains, jobs), "LC.STARTER")
    eq(starter.status, "FAIL", f"an unread OT and an unread TID prove nothing: {starter.text[:500]}")


# ---------------------------------------------------------------------------------------------------- V-06: the prediction
def case_prediction_sha_file_bytes(M, tmp):
    rig = Rig(M, tmp)
    prediction = tmp / "prediction.txt"
    prediction.write_bytes(b"3 of 3 reach ch2_wally.\n")
    code, text = rig.run(dev_args(out=str(rig.out), prediction_file=str(prediction)))
    eq(code, 0, text[-600:])
    file_sha = hashlib.sha256(prediction.read_bytes()).hexdigest()
    legs = M.legs_of("ch2_wally", M.load_milestones())
    with mock.patch.object(M, "ai_code_sha256", lambda repo=None: "0" * 64):
        want = M.registered_numbers(None, "ch2_wally", (6041, 6043), 3, legs, M.repo_root(),
                                    {"chains": 3, "leg_frames_override": {}, "prediction_sha256": file_sha})
    eq(rig.entry()["bounds_sha256"], ledger.numbers_sha256(want), "the ledger holds the FILE's sha256 (sha256sum matches)")


def case_prediction_not_utf8_refused(M, tmp):
    """(The checker's C2-06, its C70) a prediction file that is not UTF-8 is REFUSED (R3) before the ledger, never a crash:
    no entry begun, the ledger's bytes unchanged, no chain started. CONTROL: prediction_sha_file_bytes (UTF-8 runs)."""
    rig = Rig(M, tmp)
    rig.ledger.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    prediction = tmp / "prediction.txt"
    prediction.write_bytes(b"\xff\xfe 3 of 3 \x80\n")
    before = rig.ledger.read_bytes()
    try:
        code, text = rig.run(dev_args(out=str(rig.out), prediction_file=str(prediction)))
    except UnicodeDecodeError as error:
        raise AssertionError(f"a prediction that is not UTF-8 CRASHED the driver: {error}") from None
    eq(code, 2, f"refused: {text[-500:]}")
    ok("R3" in text and "cannot be read as UTF-8" in text, text[-500:])
    eq((rig.ledger.read_bytes() == before, rig.handles), (True, []), "no entry begun, no chain started")


# ---------------------------------------------------------------------------------------------------- C2-07: the guard
ERROR_OF = "ERROR (harness: {kind}: {message} {stage}; no PASS or FAIL; the seeds are spent)"
GRADING = "while grading"


def errored_run(M, rig: Rig, target: str, error: Exception) -> tuple[int, str]:
    """`rig.run` with `M.<target>` raising `error`: an exception that ESCAPES run_batch (the entry left 'started') is a
    FAILED case here, never a broken one."""
    try:
        with mock.patch.object(M, target, side_effect=error):
            return rig.run(run_args(out=str(rig.out)))
    except Exception as escaped:  # noqa: BLE001
        raise AssertionError(f"the harness's exception escaped run_batch and left the entry started: {escaped!r}") from None


def case_grade_error_finishes_entry(M, tmp):
    """(The checker's C2-07) an exception while GRADING still FINISHES the ledger entry, with a named verdict that is neither
    PASS nor FAIL, exit 4, and writes the evidence with the traceback and results.json. CONTROL: e2e_graded_pass."""
    rig = graded_rig(M, tmp)
    code, text = errored_run(M, rig, "grade_batch", RuntimeError("a planted fault"))
    entry = rig.entry()
    want = ERROR_OF.format(kind="RuntimeError", message="a planted fault", stage=GRADING)
    eq((code, entry["status"]), (4, "done"), f"exit 4 and the entry FINISHED: {text[-900:]}")
    ok(entry["verdict"].startswith(f"GRADED, {want}: live chain held-out"), entry["verdict"])
    evidence = Path(entry["evidence"] or "")
    ok(evidence.is_file(), f"the evidence is written: {entry['evidence']}")
    body = evidence.read_text(encoding="utf-8")
    ok(body.startswith(f"LIVE CHAIN HELD-OUT - GRADED - VERDICT {want}"), body[:400])
    ok("Traceback (most recent call last)" in body and "RuntimeError: a planted fault" in body, body[:2000])
    ok(body.rstrip().splitlines()[-1] == f"LEDGER: entry #{entry['id']} FINISHED with this verdict", body[-300:])
    # (the third fix round, C3-E05) the error record is results.error.json, with what grade DIR needs
    record = json.loads((rig.out / M.RESULTS_ERROR).read_text(encoding="utf-8"))
    eq((record["verdict"], record["stage"], record["ledger_finished"]), (want, "grading", True), "results.error.json")
    eq(record["numbers_sha256"], ledger.numbers_sha256(record["numbers"]), "it carries the registered numbers")


def case_evidence_error_finishes_entry(M, tmp):
    """(C2-07) an exception while WRITING THE EVIDENCE finishes the entry too, keeping what was built before it; and when
    no evidence file can be written at all (its folder is a file), the entry is STILL finished, its verdict saying so."""
    rig = graded_rig(M, tmp / "partial")
    code, text = errored_run(M, rig, "leg_lines", OSError("a planted fault in the evidence"))
    entry = rig.entry()
    want = ERROR_OF.format(kind="OSError", message="a planted fault in the evidence", stage="while writing the evidence")
    eq((code, entry["status"]), (4, "done"), f"exit 4 and the entry FINISHED: {text[-900:]}")
    ok(entry["verdict"].startswith(f"GRADED, {want}"), entry["verdict"])
    body = Path(entry["evidence"] or "").read_text(encoding="utf-8") if Path(entry["evidence"] or "").is_file() else ""
    ok("OSError: a planted fault in the evidence" in body and "checks (registered in the bounds text below" in body,
       f"the traceback and what was built before the error: {body[:1500]}")
    # (the third fix round, C3-E07) every embedded unfinished line is marked, and the bounds text is printed ONCE
    lines = body.splitlines()
    at = next(i for i, line in enumerate(lines) if line.startswith("what the harness had built before the error"))
    embedded = lines[at + 1:lines.index("", at + 1)]
    ok(embedded and all(line.startswith("UNFINISHED| ") for line in embedded), f"marked: {embedded[:3]}")
    ok(any(line == "UNFINISHED| VERDICT: PASS" for line in embedded) and not any(line == "VERDICT: PASS" for line in lines),
       "the unfinished build's own verdict line is marked, never bare")
    eq(lines.count(M.BOUNDS_HEADING), 1, "the bounds text is in the evidence once")
    rig = graded_rig(M, tmp / "nowhere")
    (tmp / "nowhere" / "evidence-is-a-file").write_text("x", encoding="utf-8")
    rig.deps.evidence_dir = tmp / "nowhere" / "evidence-is-a-file"
    code, text = errored_run(M, rig, "grade_batch", RuntimeError("a planted fault"))
    entry = rig.entry()
    eq((code, entry["status"], entry["evidence"]), (4, "done", None), f"finished with no evidence file: {text[-600:]}")
    ok("; no evidence file (" in entry["verdict"], f"the verdict says the evidence is missing: {entry['verdict']}")


# ---------------------------------------------------------------------------------------------------- V-08: a dead launch
def case_launch_died_rule(M, tmp):
    def row(world=None, log_lines=None, **stop):
        found = {"status": "RAN", "harness_stop": {"by": "other", "cause": "exit code 1", "real_frames": None, **stop}}
        if world is not None:
            found["world_file"] = world
        if log_lines is not None:
            found["measures"] = {"log": {"lines": log_lines}}
        return found
    ok((M.launch_died(row()) or "").startswith(DEAD), "exit code 1, no verdict file, no log, no world file: named")
    ok((M.launch_died(row(log_lines=0, world={"bytes": None, "deleted": False, "present": False})) or "").startswith(DEAD),
       "an empty log and no world file: named")
    ok((M.launch_died(row(by="harness", real_frames=0)) or "").startswith(DEAD), "killed with no trace of play: named")
    eq(M.launch_died(row(real_frames=5000)), None, "CONTROL: a launch that played frames and then crashed")
    eq(M.launch_died(row(by="harness", world={"bytes": 1_600_000_000, "deleted": True, "present": True})), None,
       "CONTROL: killed MID-PLAY by the guard or the wall clock (no verdict file, but a world file): not named")
    eq(M.launch_died(row(log_lines=40)), None, "CONTROL: the AI's log has lines (it started): not named")
    eq(M.launch_died(row(by="ai", cause="the AI exited by itself (exit code 0)")), None, "CONTROL: the AI's own exit")
    eq(M.launch_died({"status": "NOT RUN", "harness_stop": None}), None, "CONTROL: a leg never launched")
    # (the checker's C61) the rule reads the harness's STOP RECORD: a leg that ran with none has unknown exit facts
    eq(M.launch_died({"status": "RAN", "harness_stop": None, "measures": {"log": {"lines": 0}}}), None,
       "CONTROL: a RAN leg with no stop record is never named (its exit facts are unknown)")


def case_dead_launch_named(M, tmp):
    chain, stub, _ = play(M, tmp / "dead", {"L1": {"dead": True}})
    eq(len(stub.calls), 1, "the dead launch stops its chain")
    first = chain["legs"][0]
    ok((first.get("harness") or "").startswith(DEAD), f"the chain row NAMES it: {first.get('harness')}")
    ok(DEAD in chain["stop_reason"] and DEAD in chain["legs"][1]["reason"], chain["stop_reason"])
    eq({c["id"]: c["status"] for c in first["checks"]}["L5.THIS_RUN"], "FAIL", "it RAN: THIS_RUN still fails (kept)")
    control, _, _ = play(M, tmp / "control")
    eq([leg.get("harness") for leg in control["legs"]], [None] * 5, "CONTROL: legs that played are never named")


def case_e2e_dead_launch_evidence(M, tmp):
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp, plans={jobs[0]["chain"]: {"L1": {"dead": True}}})
    code, text = rig.run(run_args(out=str(rig.out)))
    eq(code, 1, f"the registered rule is kept: a dead launch fails the batch: {text[-600:]}")
    results = rig.results()
    statuses = {c["id"]: c["status"] for c in results["checks"]}
    eq((statuses["LC.REACH"], statuses["LC.PURITY"], statuses["LC.THIS_RUN"]), ("PASS", "FAIL", "FAIL"), "5 of 6 reach")
    lines = Path(results["evidence"]).read_text(encoding="utf-8").splitlines()
    ok(DEAD in lines[0] and "LC-S-6201 L1" in lines[0], f"the evidence's first line names it: {lines[0]}")
    ok(any(line.startswith(DEAD) and f"LC-S-6201 L1: {DEAD}" in line for line in lines), "and its own line")
    ok(any(line.strip().startswith(DEAD) for line in lines if line.startswith("      ")), "and the leg's block")
    ok(DEAD in rig.entry()["verdict"], f"and the ledger's verdict: {rig.entry()['verdict'][:300]}")
    # (the checker's C2-04) each place on its own: the ledger verdict's OWN clause (LC.REACH's stop reason quotes the
    # text too, so DEAD alone passed with the clause removed: C66), and LC.PURITY's and LC.THIS_RUN's lists (C64, C65)
    ok(f"; {DEAD}: ['LC-S-6201 L1']: live chain held-out" in rig.entry()["verdict"],
       f"the ledger verdict's own dead-launch clause: {rig.entry()['verdict'][:400]}")
    texts = {c["id"]: c["text"] for c in results["checks"]}
    ok(f"LC-S-6201 L1: {DEAD}" in texts["LC.PURITY"], f"LC.PURITY's failing list names it: {texts['LC.PURITY'][:600]}")
    ok(f"LC-S-6201 L1 FAIL ({DEAD})" in texts["LC.THIS_RUN"], f"LC.THIS_RUN's list names it: {texts['LC.THIS_RUN'][:600]}")
    world = next(c for c in results["checks"] if c["id"] == "LC.WORLD")["text"]
    ok("LC-S-6201 L1 no world file" in world and "not deleted after its leg: none" in world, world[:600])
    ok(any("world.jsonl: no world file" in line for line in lines), "the leg's world line")


def case_world_line_no_file(M, tmp):
    chains, jobs = healthy_batch()
    chains[0]["legs"][4]["world_file"] = {"bytes": None, "deleted": False, "present": False}
    chains[1]["legs"][4]["world_file"] = {"bytes": 5000, "deleted": False, "present": True}
    # (the checker's C62) a world file that is THERE but was not measured is no "no world file": it is not deleted
    chains[2]["legs"][4]["world_file"] = {"bytes": None, "deleted": False, "present": True}
    world = by_id(grade(M, chains, jobs), "LC.WORLD").text
    ok(f"{chains[0]['chain']} L5 no world file" in world, world[:600])
    ok(f"{chains[2]['chain']} L5 no world file" not in world, f"a present, unmeasured file is not 'no world file': {world[:900]}")
    ok(f"not deleted after its leg: ['{chains[1]['chain']} L5', '{chains[2]['chain']} L5']" in world,
       f"CONTROL: a file the OS kept open, measured or not, is still listed as not deleted: {world[:900]}")


# ==================================================================================================== THE THIRD FIX ROUND
# (the independent check's C3-E01..E07, C3-G01..G06, C3-H01..H07 and the chains-run guard, 2026-11-05) each new or changed
# guard: a FAULT case, a CONTROL case, and a mutant in MUTANTS
def guarded_run(rig: Rig, args: argparse.Namespace | None = None, environ: dict | None = None) -> tuple[int, str]:
    """`rig.run`; an exception that ESCAPES run_batch is a FAILED case here (its entry would be left 'started')."""
    try:
        return rig.run(args or run_args(out=str(rig.out)), environ)
    except Exception as escaped:  # noqa: BLE001
        raise AssertionError(f"the harness's exception escaped run_batch: {escaped!r}") from None


def evidence_text(rig: Rig) -> str:
    found = sorted(rig.evidence.glob("*.txt")) if rig.evidence.is_dir() else []
    return found[-1].read_text(encoding="utf-8") if found else ""


def dev_rig(M, tmp: Path, **kwargs) -> tuple[Rig, argparse.Namespace]:
    rig = Rig(M, tmp, **kwargs)
    rig.ledger.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    prediction = tmp / "prediction.txt"
    prediction.write_text("3 of 3 reach ch2_wally.\n", encoding="utf-8")
    return rig, dev_args(out=str(rig.out), prediction_file=str(prediction))


def missing_drive() -> Path | None:
    return next((Path(f"{c}:/") for c in reversed(string.ascii_uppercase) if not Path(f"{c}:/").exists()), None)


# ---------------------------------------------------------------------------------------------------- C3-E01: --out first
def case_out_listing_unmakeable(M, tmp):
    """(C3-E01) an --out that does not exist and can never be made is R11's before anything: a FILE above it (a typo), no
    folder above it at all (a missing drive). CONTROL: a new folder under one that exists."""
    (tmp / "notes.txt").write_text("x", encoding="utf-8")
    ok("above it is not a folder" in M.out_listing(tmp / "notes.txt" / "out" / "deeper").get("out_error", ""),
       "a file above --out")
    drive = missing_drive()
    if drive is not None:
        ok("no folder above it exists" in M.out_listing(drive / "lc" / "out").get("out_error", ""), "a missing drive")
    eq(M.out_listing(tmp / "fresh" / "out"), {"out_entries": []}, "CONTROL: a folder that can be made")


def case_e2e_out_unmakeable_refused(M, tmp):
    """(C3-E01, the checker's S5) a graded run whose --out cannot be created or written is REFUSED (R11, exit 2) BEFORE
    ledger.begin: the ledger's bytes unchanged, the entry still 'registered', no chain started, nothing made. Under a file
    and on a missing drive the listing refuses it; an invalid name only fails when it is MADE (prepare_out). CONTROL:
    e2e_graded_pass and e2e_out_empty_proceeds."""
    (tmp / "notes.txt").write_text("a file where a folder was meant\n", encoding="utf-8")
    cases = {"under_a_file": tmp / "notes.txt" / "out", "invalid_name": tmp / "out?1"}
    if missing_drive() is not None:
        cases["missing_drive"] = missing_drive() / "lc" / "out"
    for label, out in cases.items():
        rig = graded_rig(M, tmp / label)
        before = rig.ledger.read_bytes()
        code, text = guarded_run(rig, run_args(out=str(out)))
        eq(code, 2, f"{label}: refused: {text[-500:]}")
        ok("REFUSED: R11" in text and "cannot be created" in text, f"{label}: {text[-500:]}")
        eq((rig.entry()["status"], rig.ledger.read_bytes() == before, rig.handles), ("registered", True, []),
           f"{label}: the registration is NOT spent")
    ok(not any(p.name.startswith("out?") for p in tmp.iterdir()), "nothing made for the invalid name")


def case_e2e_out_undone_on_ledger_refusal(M, tmp):
    """(C3-E01) --out and the job files are made BEFORE ledger.begin, so a batch the LEDGER refuses (R10) removes them
    again: a missing --out is not left behind, an empty one is left empty (else R11 would refuse it next time)."""
    for label, pre in (("missing", False), ("empty", True)):
        rig = Rig(M, tmp / label)
        rig.ledger.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
        if pre:
            rig.out.mkdir(parents=True)
        code, text = guarded_run(rig)
        eq(code, 2, f"{label}: refused by the ledger: {text[-400:]}")
        ok("R10" in text, text[-400:])
        if pre:
            eq(sorted(p.name for p in rig.out.iterdir()), [], "an EMPTY --out is left empty")
        else:
            ok(not rig.out.exists(), "the --out made before ledger.begin is removed again")


def case_e2e_steps_before_begin(M, tmp):
    """(C3-E01, C3-G05) every step that needs no chain runs BEFORE ledger.begin: every job file is on disk and both profile
    snapshots (main_profile_state, run_folders) were taken when begin is called. CONTROL: the batch passes."""
    rig = graded_rig(M, tmp)
    calls: list[str] = []
    seen: dict = {}
    real_begin, real_main, real_folders = M.begin, M.main_profile_state, M.run_folders

    def begin(*args, **kwargs):
        seen.update({"job_files": sorted(p.name for p in rig.out.glob("*.job.json")), "calls": list(calls)})
        return real_begin(*args, **kwargs)
    with mock.patch.object(M, "begin", begin), \
            mock.patch.object(M, "main_profile_state", lambda b: calls.append("main_profile_state") or real_main(b)), \
            mock.patch.object(M, "run_folders", lambda b: calls.append("run_folders") or real_folders(b)):
        code, text = guarded_run(rig)
    eq(code, 0, f"CONTROL: the batch passes: {text[-400:]}")
    eq(len(seen.get("job_files") or []), 6, f"every job file is written before ledger.begin: {seen}")
    ok({"main_profile_state", "run_folders"} <= set(seen.get("calls") or []), f"the snapshots come before begin: {seen}")


# ---------------------------------------------------------------------------------------------------- the chains-run guard
def case_chains_error_finishes_entry(M, tmp):
    """(The chains-run guard) an exception WHILE THE CHAINS RUN (here the disk guard's free-space read raises with three
    chains running) kills every running chain process, deletes their world files (the end sweep) and FINISHES the entry as
    ERROR 'while the chains ran', exit 4, with the evidence naming what the guard did and results.error.json. And the
    checker's S6: the very first spawn raising (nothing running) ends the same way. CONTROL: e2e_graded_pass."""
    reads = {"n": 0}

    def free(path):
        reads["n"] += 1
        if reads["n"] == 2:  # (read 1: gather_facts; read 2: the first tick, three chains running)
            raise RuntimeError("a planted fault in the disk guard")
        return 100.0
    rig = graded_rig(M, tmp / "tick", alive=50, free=free,
                     pre_spawn=lambda job: planted_folder(Path(job["build_root"]), job["profile"],
                                                          f"20261105-000000-{job['chain']}-L1"))
    code, text = guarded_run(rig)
    entry = rig.entry()
    want = ERROR_OF.format(kind="RuntimeError", message="a planted fault in the disk guard", stage="while the chains ran")
    eq((code, entry["status"]), (4, "done"), f"exit 4 and the entry FINISHED: {text[-700:]}")
    ok(entry["verdict"].startswith(f"GRADED, {want}"), entry["verdict"])
    eq(len(rig.handles), 3, "three chains were running")
    ok(all(handle.killed for handle in rig.handles), "every running chain process was killed")
    eq(list(rig.build.glob("profiles/*/ai_player_runs/*/world.jsonl")), [], "their world files were deleted")
    body = evidence_text(rig)
    ok("the guard: LC-S-6201: its process (pid 1000) was still running: killed" in body, body[:1500])
    eq(json.loads((rig.out / M.RESULTS_ERROR).read_text(encoding="utf-8"))["stage"], "chains", "results.error.json")
    rig = graded_rig(M, tmp / "spawn")
    rig.deps.spawn = lambda job, job_path, log_path: (_ for _ in ()).throw(OSError(24, "Too many open files"))
    code, text = guarded_run(rig)
    eq((code, rig.entry()["status"]), (4, "done"), f"the first spawn raising: {text[-500:]}")
    ok("while the chains ran" in rig.entry()["verdict"], rig.entry()["verdict"])


def case_chains_interrupt_finishes_entry(M, tmp):
    """(The chains-run guard, C3-E06) a Ctrl+C (KeyboardInterrupt) while the chains run: the running chain processes are
    killed and the entry FINISHED as ERROR, and only then does the interrupt stop the process."""
    calls = {"n": 0}
    rig = graded_rig(M, tmp, alive=50)

    def sleep(seconds):
        calls["n"] += 1
        if calls["n"] == 6:
            raise KeyboardInterrupt()
    rig.deps.sleep = sleep
    try:
        rig.run(run_args(out=str(rig.out)))
        raise AssertionError("the interrupt did not stop the process")
    except KeyboardInterrupt:
        pass
    entry = rig.entry()
    eq(entry["status"], "done", "the entry is FINISHED before the interrupt goes on")
    ok(entry["verdict"].startswith("GRADED, ERROR (harness: KeyboardInterrupt: no message while the chains ran"),
       entry["verdict"])
    ok(rig.handles and all(handle.killed for handle in rig.handles), "the running chain processes were killed")


# ---------------------------------------------------------------------------------------------------- C3-E02: the AI's data
def case_world_counts_untrusted(M, tmp):
    """(C3-E02) a world line the AI wrote never makes the harness raise: a wrong-typed field, a deeply nested line, a list,
    bytes that are not UTF-8, a number too long for int() and a float are each a FAILED line (None, why); the stream
    counts a bad MIDDLE line and keeps going. CONTROL: the AI's own snapshot shape is read."""
    good = snapshot(2, 10).encode()
    eq(M.world_counts(good)[0], {"maps": 2, "tiles": 10, "warps": 1, "connections": 1, "transitions": 2}, "CONTROL")
    for label, raw in (("maps a number", b'{"maps": 3}'), ("tiles as text", b'{"tiles_learned": "many"}'),
                       ("tiles a float", b'{"tiles_learned": 1e400}'), ("warps a list", b'{"warps": [1]}'),
                       ("a list", b"[1, 2]"), ("deep", b"[" * 100000 + b"]" * 100000), ("not utf-8", b"\xff\xfe{"),
                       ("a 5000-digit count", b'{"tiles_learned": ' + b"9" * 5000 + b"}"), ("a bool", b'{"tiles_learned": true}')):
        counts, why = M.world_counts(raw)
        ok(counts is None and why, f"{label}: a failed line, not {counts}")
    world = tmp / "world.jsonl"
    world.write_bytes(good + b"\n" + b"[" * 100000 + b"]" * 100000 + b"\n" + good + b"\n")
    found = M.stream_world_tail(world, tmp / "kept.jsonl")
    eq((found["lines"], found["bad_lines"], found["last_ok"]), (3, 1, True), "a deep MIDDLE line is one bad line")
    world.write_bytes(good + b"\n" + b'{"maps": 3, "tiles_learned": 0}\n')
    found = M.stream_world_tail(world, tmp / "kept2.jsonl")
    eq((found["last_ok"], found["counts"]), (False, None), "a wrong-typed LAST line: last_ok False")


def case_e2e_untrusted_world_fails_not_errors(M, tmp):
    """(C3-E02, the checker's arms C-E) the AI's world.jsonl with a valid-JSON last line of the wrong type, and another leg's
    with a 100,000-deep middle line, inside a batch that FAILS (two chains miss at L2): the batch is GRADED, FAIL, exit 1,
    NEVER the harness's ERROR. The chain processes behave as separate processes (any exception ends one, exit 1) and none
    died; the wrong-typed chain STOPS at that leg by C3, the deep-line leg continues (its last line is good)."""
    jobs = LC.jobs_of(6201, 6)
    plans = {jobs[0]["chain"]: {"L2": {"miss": True}}, jobs[3]["chain"]: {"L2": {"miss": True}},
             jobs[1]["chain"]: {"L3": {"wrong_type_last_line": True}}, jobs[2]["chain"]: {"L2": {"deep_line": True}}}
    rig = graded_rig(M, tmp, plans=plans, real_child=True)
    code, text = guarded_run(rig)
    entry = rig.entry()
    eq(code, 1, f"GRADED, FAIL, never the harness's ERROR: {entry.get('verdict')}: {text[-700:]}")
    eq(rig.results()["verdict"], "FAIL", "results.json")
    ok(entry["verdict"].startswith("GRADED, FAIL") and "ERROR" not in entry["verdict"], entry["verdict"][:300])
    eq(rig.child_errors, [], "no chain process died")
    wrong = json.loads((rig.out / "rows" / f"{jobs[1]['chain']}.json").read_text(encoding="utf-8"))
    eq(wrong["stopped_at"], "L3", f"the wrong-typed leg stops its chain: {wrong['stop_reason']}")
    ok("C3 its world.jsonl's last line did not parse" in wrong["stop_reason"], wrong["stop_reason"])
    deep = json.loads((rig.out / "rows" / f"{jobs[2]['chain']}.json").read_text(encoding="utf-8"))
    world = (deep["legs"][1].get("measures") or {}).get("world") or {}
    eq((world.get("bad_lines"), deep["reached_to"]), (1, True), "the deep line is counted only (the leg is measured)")


def case_log_untrusted(M, tmp):
    """(C3-E02) the AI's log: a memory line with a count longer than int() reads is an UNREADABLE memory line (no counts:
    LC.MEMORY fails that leg), and a log that cannot be read to its end keeps its count, marked: neither raises."""
    try:
        found = M.log_counts(["[AI-HANDS] outcome=done presses=1 frames=1",
                              "[AI-WORLD] memory from nothing (a new memory): " + "9" * 5000 + " maps (none), 0 tiles "
                              "learned, 0 warp links, 0 connections, 0 map changes"])
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"the AI's memory line raised: {error!r}") from None
    ok(found["memory"] is not None and found["memory"]["counts"] is None and found["memory"].get("unreadable"),
       f"an unreadable memory line: {found['memory']}")
    log = tmp / "ai_player.log"
    log.write_text("one\ntwo\n", encoding="utf-8")
    real_open = open

    def broken(file, *args, **kwargs):
        if str(file) == str(log):
            raise PermissionError(13, "held by another program")
        return real_open(file, *args, **kwargs)
    try:
        with mock.patch("builtins.open", broken):
            read = M.read_log_counts(log)
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"an unreadable log raised: {error!r}") from None
    ok(read is not None and "could not be read" in (read.get("error") or ""), f"an unreadable log: {read}")
    chains, jobs = healthy_batch()
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "PASS", "CONTROL: every memory line read")
    chains[0]["legs"][2]["measures"]["log"]["memory"] = found["memory"]
    eq(by_id(grade(M, chains, jobs), "LC.MEMORY").status, "FAIL", "an unreadable memory line fails LC.MEMORY")


def case_chain_bad_verdict(M, tmp):
    """(C3-E02) the AI process's verdict file with values of the wrong type (real_frames as text, exit_reason a number)
    and an action record that is no object: the chain process does NOT raise; the checks that could not judge it are
    MISSING (they fail), noted, and the chain stops at that leg. CONTROL: chain_control."""
    try:
        chain, stub, _ = play(M, tmp, {"L2": {"bad_verdict": True}})
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"the chain process raised on the AI's verdict file: {error!r}") from None
    eq(len(stub.calls), 2, "the chain stopped at L2")
    leg = chain["legs"][1]
    ok(any("could not judge the AI's output" in note for note in leg["notes"]), leg["notes"])
    ok(not leg["continue"] and "L5.THIS_RUN MISSING" in leg["why"], leg["why"])
    eq(leg["outcome"], "7", "the AI's exit_reason kept as text")


def case_kept_line_wrong_shape(M, tmp):
    """(C3-E02) a kept last line that IS a JSON object but whose counts cannot be read (maps a number), filed with its own
    sha256, never counts. CONTROL: 5 of 6 reach."""
    chains, jobs = batch_with({1: {"L2": {"miss": True}}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "PASS", "CONTROL: 5 of 6 reach")
    forged = tmp / "wrong_shape.jsonl"
    forged.write_bytes(b'{"maps": 3, "tiles_learned": 0}\n')
    last = chains[0]["legs"][4]
    last["kept_world"], last["kept_world_sha256"] = str(forged), hashlib.sha256(forged.read_bytes()).hexdigest()
    try:
        reach = by_id(grade(M, chains, jobs), "LC.REACH")
    except Exception as error:  # noqa: BLE001 - (the fourth fix round) the grade reads the AI's bytes: it never raises
        raise AssertionError(f"a kept line of the wrong shape raised in the grade: {error!r}") from None
    eq(reach.status, "FAIL", f"a kept line whose counts cannot be read never counts: {reach.text[:500]}")
    ok("its kept last line is not a JSON object whose five counts can be read" in reach.text, reach.text[:900])


# ---------------------------------------------------------------------------------------------------- C3-E03: the ledger
def case_ledger_finish_transient_retried(M, tmp):
    """(C3-E03) a ledger write that fails ONCE (another program held it) is retried with the COMPUTED verdict: the entry is
    'done' with PASS, exit 0."""
    rig = graded_rig(M, tmp)
    real, verdicts = ledger.finish, []

    def flaky(entry_id, verdict, evidence, path=ledger.LEDGER):
        verdicts.append(verdict)
        if len(verdicts) == 1:
            raise PermissionError(13, "held open by another program")
        return real(entry_id, verdict, evidence, path=path)
    with mock.patch.object(ledger, "finish", flaky):
        code, text = guarded_run(rig)
    eq((code, rig.entry()["status"]), (0, "done"), f"retried: {text[-500:]}")
    ok(rig.entry()["verdict"].startswith("GRADED, PASS") and len(verdicts) == 2, f"{verdicts}")


def case_ledger_finish_computed_unwritable(M, tmp):
    """(C3-E03, C3-E04's E08) the computed verdict cannot be written in any try while the ERROR verdict can: the entry is
    'done' with ERROR 'while writing the ledger', exit 4; the COMPLETE results.json is kept and the error record sits
    beside it (results.error.json)."""
    rig = graded_rig(M, tmp)
    real = ledger.finish

    def refuse_computed(entry_id, verdict, evidence, path=ledger.LEDGER):
        if "ERROR (harness:" not in verdict:
            raise PermissionError(13, "held open by another program")
        return real(entry_id, verdict, evidence, path=path)
    with mock.patch.object(ledger, "finish", refuse_computed):
        code, text = guarded_run(rig)
    entry = rig.entry()
    eq((code, entry["status"]), (4, "done"), f"finished as ERROR: {text[-600:]}")
    ok(entry["verdict"].startswith("GRADED, ERROR (harness: LedgerUnwritten:") and "while writing the ledger" in
       entry["verdict"], entry["verdict"][:300])
    ok("checks" in rig.results() and rig.results()["verdict"] == "PASS", "the complete results.json is kept")
    eq(json.loads((rig.out / M.RESULTS_ERROR).read_text(encoding="utf-8"))["stage"], "ledger", "results.error.json")


def case_ledger_unwritable_not_finished(M, tmp):
    """(C3-E03, the checker's S1/S8) a ledger that cannot be written AT ALL: exit 4 (never 1), the entry still 'started',
    and the evidence's last line, results.error.json and the output say it is NOT finished, with the exact command; that
    command then finishes it, and refuses a second time."""
    rig = graded_rig(M, tmp)
    with mock.patch.object(ledger, "finish", side_effect=PermissionError(13, "held open by another program")):
        code, text = guarded_run(rig)
    eq((code, rig.entry()["status"]), (4, "started"), f"not finished, said: {text[-600:]}")
    command = M.finish_command({"out": rig.out.resolve(), "ledger_path": rig.ledger})
    last = evidence_text(rig).rstrip().splitlines()[-1]
    ok("is NOT FINISHED" in last and command in last, f"the evidence's last line: {last}")
    ok(f"is NOT FINISHED" in text and command in text, text[-700:])
    record = json.loads((rig.out / M.RESULTS_ERROR).read_text(encoding="utf-8"))
    eq((record["ledger_finished"], record["finish_command"]), (False, command), "results.error.json says so")
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = M.main(["finish-entry", str(rig.out), "--ledger", str(rig.ledger)])
    eq((code, rig.entry()["status"]), (0, "done"), buffer.getvalue())
    ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness: LedgerUnwritten:"), rig.entry()["verdict"][:200])
    with contextlib.redirect_stdout(io.StringIO()):
        eq(M.main(["finish-entry", str(rig.out), "--ledger", str(rig.ledger)]), 2, "an entry already done is refused")


# ---------------------------------------------------------------------------------------------------- C3-E04: the edges
def case_grade_error_any_exception(M, tmp):
    """(C3-E04, its E01) the guard is not limited to some exception types: a KeyError and a TypeError while grading each
    finish the entry as ERROR, exit 4."""
    for kind in (KeyError("legs"), TypeError("object of type 'int' has no len()")):
        rig = graded_rig(M, tmp / type(kind).__name__)
        code, text = errored_run(M, rig, "grade_batch", kind)
        eq((code, rig.entry()["status"]), (4, "done"), f"{type(kind).__name__}: {text[-400:]}")
        ok(rig.entry()["verdict"].startswith(f"GRADED, ERROR (harness: {type(kind).__name__}:"), rig.entry()["verdict"])


def case_results_write_error_both_paths(M, tmp):
    """(C3-E04, its E03) results.json cannot be written (the normal path) and neither can results.error.json (the error
    path): the entry is still FINISHED as ERROR 'while writing results.json', exit 4, and the output says the error record
    is missing."""
    rig = graded_rig(M, tmp)
    real = M._write_json

    def failing(path, data):
        if Path(path).name in ("results.json", M.RESULTS_ERROR):
            raise OSError("a planted fault: the disk is full")
        return real(path, data)
    with mock.patch.object(M, "_write_json", failing):
        code, text = guarded_run(rig)
    eq((code, rig.entry()["status"]), (4, "done"), text[-500:])
    ok("while writing results.json" in rig.entry()["verdict"], rig.entry()["verdict"])
    ok(f"{M.RESULTS_ERROR} could not be written" in text, text[-800:])


def case_error_evidence_any_exception(M, tmp):
    """(C3-E04, its E04) the error path's evidence fails with an exception that is no OSError (keep_earlier raising
    ValueError): the entry is still FINISHED, its verdict saying the evidence is missing."""
    rig = graded_rig(M, tmp)
    with mock.patch("ai_player.gates.provenance.keep_earlier", side_effect=ValueError("a planted fault")):
        code, text = errored_run(M, rig, "grade_batch", RuntimeError("a planted fault in grading"))
    eq((code, rig.entry()["status"]), (4, "done"), text[-400:])
    ok("; no evidence file (ValueError" in rig.entry()["verdict"], rig.entry()["verdict"])


def case_dev_error_labelled(M, tmp):
    """(C3-E04, its E06/E07) a DEVELOPMENT batch whose harness raises: exit 4 (never 0, 'ran') and a verdict that reads as
    no pass ('DEVELOPMENT, not graded, NO PASS (development: ERROR ...')."""
    rig, args = dev_rig(M, tmp)
    with mock.patch.object(M, "grade_batch", side_effect=RuntimeError("a planted fault")):
        code, text = guarded_run(rig, args)
    eq((code, rig.entry()["status"]), (4, "done"), text[-400:])
    ok(rig.entry()["verdict"].startswith("DEVELOPMENT, not graded, NO PASS (development: ERROR (harness: RuntimeError"),
       rig.entry()["verdict"])


def case_dev_unhashed_printed(M, tmp):
    """(C3-E04's E22, C3-H06) a DEVELOPMENT batch whose closure has an unhashed file is NOT refused: it runs, prints the
    file as NOT hashed and exits 0. (A graded run is refused: closure_enforced_run.)"""
    rig, args = dev_rig(M, tmp)
    rig.deps.closure = lambda: (["sandbox-pokebot/plugins/zz_new_plugin.py"], 232, 0.1)
    code, text = guarded_run(rig, args)
    eq(code, 0, f"not refused: {text[-500:]}")
    eq(rig.entry()["status"], "done", "the development batch ran")
    ok("1 NOT hashed (a development batch is not refused): ['sandbox-pokebot/plugins/zz_new_plugin.py']" in text,
       text[:900])


# ---------------------------------------------------------------------------------------------------- C3-E05: grade DIR
def case_grade_dir_error_batch(M, tmp):
    """(C3-E05) grade DIR on a batch that ended in ERROR says so and exits 4, never crashes: while grading (no results.json:
    it re-grades from results.error.json's numbers) and while writing the ledger (the complete results.json kept)."""
    rig = graded_rig(M, tmp / "grading")
    errored_run(M, rig, "grade_batch", RuntimeError("a planted fault"))
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = M.grade_dir(rig.out, rig.ledger)
    eq(code, 4, buffer.getvalue()[-600:])
    ok("this batch ended in ERROR" in buffer.getvalue() and "NUMBERS: VERIFIED" in buffer.getvalue(), buffer.getvalue()[:900])
    rig = graded_rig(M, tmp / "ledger")
    real = ledger.finish
    with mock.patch.object(ledger, "finish", lambda i, v, e, path=ledger.LEDGER: (
            real(i, v, e, path=path) if "ERROR (harness:" in v else (_ for _ in ()).throw(OSError("held")))):
        guarded_run(rig)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        code = M.grade_dir(rig.out, rig.ledger)
    eq(code, 4, buffer.getvalue()[-600:])
    ok("OFFLINE RE-GRADE (no ledger write): PASS" in buffer.getvalue(), "its rows re-grade, as information")


def case_grade_dir_exit_codes(M, tmp):
    """(C3-E05, C3-G04) grade DIR's exit: 0 on PASS, 1 on FAIL, 2 when there is nothing to grade."""
    rig = graded_rig(M, tmp / "pass")
    guarded_run(rig)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        eq(M.grade_dir(rig.out, rig.ledger), 0, buffer.getvalue()[-400:])
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "fail", plans={jobs[0]["chain"]: {"L2": {"miss": True}}, jobs[1]["chain"]: {"L2": {"miss": True}}})
    guarded_run(rig)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        eq(M.grade_dir(rig.out, rig.ledger), 1, buffer.getvalue()[-400:])
    (tmp / "empty").mkdir()
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        eq(M.grade_dir(tmp / "empty"), 2, buffer.getvalue())
    ok("CANNOT GRADE" in buffer.getvalue(), buffer.getvalue())


# ---------------------------------------------------------------------------------------------------- C3-E06, C3-E07
class Unprintable(Exception):
    def __str__(self):
        raise ValueError("str() of this exception fails")


def case_main_crash_exit_5(M, tmp):
    """(C3-E06) an exception no guard covers exits 5 ('harness crash'), never 1 (FAIL); before ledger.begin it leaves the
    ledger untouched (a crash in the refusal checks)."""
    try:
        with mock.patch.object(M, "run_batch", side_effect=RuntimeError("a planted crash")), \
                contextlib.redirect_stdout(io.StringIO()) as buffer:
            code = M.main(["run", "--purpose", "graded", "--run", "ch5", "--out", str(tmp / "out")])
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"the crash escaped main: {error!r}") from None
    eq(code, 5, buffer.getvalue()[-400:])
    ok("HARNESS CRASH (exit 5)" in buffer.getvalue(), buffer.getvalue()[-400:])
    rig = graded_rig(M, tmp / "before")
    before = rig.ledger.read_bytes()
    rig.deps.g3 = lambda: (_ for _ in ()).throw(RuntimeError("a planted crash before begin"))
    try:
        rig.run(run_args(out=str(rig.out)))
        raise AssertionError("the crash did not reach main")
    except RuntimeError:
        pass
    eq((rig.ledger.read_bytes() == before, rig.entry()["status"]), (True, "registered"), "the ledger is untouched")


def case_unprintable_error(M, tmp):
    """(C3-E06) an exception whose str() raises still gives a named ERROR verdict (a safe repr), exit 4, entry done."""
    rig = graded_rig(M, tmp)
    code, text = errored_run(M, rig, "grade_batch", Unprintable())
    eq((code, rig.entry()["status"]), (4, "done"), text[-400:])
    ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness: Unprintable: Unprintable() while grading"),
       rig.entry()["verdict"])


def case_grading_interrupt(M, tmp):
    """(C3-E06, the checker's S4) a Ctrl+C while grading FINISHES the entry as ERROR, then stops the process."""
    rig = graded_rig(M, tmp)
    try:
        with mock.patch.object(M, "grade_batch", side_effect=KeyboardInterrupt()):
            rig.run(run_args(out=str(rig.out)))
        raise AssertionError("the interrupt did not stop the process")
    except KeyboardInterrupt:
        pass
    eq(rig.entry()["status"], "done", "finished before the interrupt goes on")
    ok("KeyboardInterrupt" in rig.entry()["verdict"] and "while grading" in rig.entry()["verdict"], rig.entry()["verdict"])


def case_closure_parse_error_named(M, tmp):
    """(C3-E06) a closure file that does not parse is NAMED (its repository path): the scan's SyntaxError says it; a
    registration and a graded run are REFUSED (R12) naming it, the ledger untouched."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    plant(root, "sandbox-pokebot/plugins/broken_plugin.py", "def (:\n")
    try:
        M.closure_scan(root)
        raise AssertionError("a file that does not parse was scanned")
    except SyntaxError as error:
        eq(error.filename, "sandbox-pokebot/plugins/broken_plugin.py", "the error names the file")
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    path.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    broken = plant(repo, "sandbox-pokebot/plugins/zz_broken.py", "def (:\n")
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            code = M.register_run("ch5", None, repo=repo, path=path)
        rig = graded_rig(M, tmp / "rig")
        rig.deps.closure = lambda: M.closure_missing(repo)
        run_code, text = guarded_run(rig)
    except SyntaxError as error:
        raise AssertionError(f"a closure file that does not parse crashed the registration: {error!r}") from None
    finally:
        broken.unlink()
    eq(code, 2, buffer.getvalue()[-400:])
    ok("R12" in buffer.getvalue() and "sandbox-pokebot/plugins/zz_broken.py" in buffer.getvalue(), buffer.getvalue()[-400:])
    eq(json.loads(path.read_text(encoding="utf-8"))["entries"], [], "nothing registered")
    eq((run_code, rig.entry()["status"]), (2, "registered"), text[-400:])
    ok("R12" in text and "sandbox-pokebot/plugins/zz_broken.py" in text, text[-400:])


def case_evidence_write_error_bounds_once(M, tmp):
    """(C3-E07) the evidence write itself fails once, AFTER the bounds text was appended: the ERROR evidence embeds what
    was built, every line marked 'UNFINISHED| ', cut before its bounds text, and prints the bounds text ONCE."""
    rig = graded_rig(M, tmp)

    class FailOnce(type(Path())):
        failed: list = []

        def write_text(self, *args, **kwargs):
            if not FailOnce.failed:
                FailOnce.failed.append(1)
                raise OSError("a planted fault writing the evidence")
            return super().write_text(*args, **kwargs)
    real = M.evidence_path
    with mock.patch.object(M, "evidence_path", lambda *a: FailOnce(real(*a))):
        code, text = guarded_run(rig)
    eq((code, rig.entry()["status"]), (4, "done"), text[-400:])
    ok("while writing the evidence" in rig.entry()["verdict"], rig.entry()["verdict"])
    lines = evidence_text(rig).splitlines()
    eq(lines.count(M.BOUNDS_HEADING), 1, "the bounds text once")
    at = next(i for i, line in enumerate(lines) if line.startswith("what the harness had built before the error"))
    embedded = lines[at + 1:lines.index("", at + 1)]
    ok(len(embedded) > 20 and all(line.startswith("UNFINISHED| ") for line in embedded), embedded[:3])
    ok("UNFINISHED| VERDICT: PASS" in embedded, "the unfinished verdict line is marked")


# ---------------------------------------------------------------------------------------------------- C3-G01: each leg
def case_leg_identity_each_field(M, tmp):
    """(C3-G01) every leg that ran names its REGISTERED job in its own records: changing ONE of its environment's seed, its
    personality, its command's --profile, its arm or its run folder (or dropping the folder) is named, and fails
    LC.CUSTODY. CONTROL: the honest leg."""
    chains, jobs = healthy_batch()
    job, leg = jobs[0], chains[0]["legs"][1]
    eq(M.leg_identity_problems(leg, job), [], "CONTROL: the honest leg")
    changes = (("seed", lambda r: r["env"].__setitem__("AI_PLAYER_SEED", "7102"), "environment seed '7102'"),
               ("personality", lambda r: r["env"].__setitem__("AI_PLAYER_PERSONALITY", "Catcher"), "personality 'Catcher'"),
               ("profile", lambda r: r["command"].__setitem__(r["command"].index("--profile") + 1, "ai-livechain-7102"),
                "--profile 'ai-livechain-7102'"),
               ("arm", lambda r: r.__setitem__("arm", "LC-S-7102-L2"), "arm 'LC-S-7102-L2'"),
               ("run folder", lambda r: r.__setitem__("run_dir", r["run_dir"].replace("ai-livechain-7101", "ai-livechain-7102")),
                "run folder"),
               ("no run folder", lambda r: r.__setitem__("run_dir", None), "run folder None"),
               # (the fourth check's C4-G05: its mutant C03) the right profile folder, but not profiles/<profile>/ai_player_runs
               ("run folder outside ai_player_runs",
                lambda r: r.__setitem__("run_dir", r["run_dir"].replace("ai_player_runs", "other_runs")), "run folder"))
    for label, change, needle in changes:
        row = copy.deepcopy(leg)
        change(row)
        found = M.leg_identity_problems(row, job)
        ok(len(found) == 1 and needle in found[0], f"{label}: {found}")
        rows = copy.deepcopy(chains)
        change(rows[0]["legs"][1])
        eq(by_id(grade(M, rows, jobs), "LC.CUSTODY").status, "FAIL", f"{label}: LC.CUSTODY")


def relabel(chains: list[dict], src: int, dst: int, jobs: list[dict]) -> dict:
    row = copy.deepcopy(chains[src])
    for key in ("chain", "seed", "profile"):
        row[key] = jobs[dst][key]
    return row


def case_relabelled_copy_stays_fail(M, tmp):
    """(C3-G01, the checker's G2/G2b) a clean row of ANOTHER chain of the same pair, filed over an impure one with its
    chain, seed and profile labels renamed, never counts: its legs' own records name the other job. In grade_batch, IN-RUN
    (rows rewritten after the chains ended) and in grade DIR. CONTROL: the impure batch FAILS."""
    chains, jobs = healthy_batch()
    leg = chains[0]["legs"][4]
    next(c for c in leg["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
    leg["continue"] = False
    eq(M.batch_verdict(grade(M, chains, jobs)), "FAIL", "CONTROL: LC-S-7101's L5 impure")
    chains[0] = relabel(chains, 3, 0, jobs)
    checks = grade(M, chains, jobs)
    custody = by_id(checks, "LC.CUSTODY")
    eq((M.batch_verdict(checks), custody.status), ("FAIL", "FAIL"), f"the relabelled copy never counts: {graded_ok(checks)}")
    ok("environment seed '7102' is not the registered '7101'" in custody.text, custody.text[:700])
    run_jobs = LC.jobs_of(6201, 6)
    by = {j["chain"]: j for j in run_jobs}

    def tamper() -> list[str]:
        for dst, src in ((run_jobs[0]["chain"], "LC-S-6202"), (run_jobs[1]["chain"], "LC-C-6204")):
            row = json.loads((rig.out / "rows" / f"{src}.json").read_text(encoding="utf-8"))
            row.update({key: by[dst][key] for key in ("chain", "seed", "profile")})
            (rig.out / "rows" / f"{dst}.json").write_text(json.dumps(row), encoding="utf-8")
        return []
    rig = graded_rig(M, tmp, plans={run_jobs[0]["chain"]: {"L5": {"miss": True}}, run_jobs[1]["chain"]: {"L5": {"miss": True}}},
                     leftover=tamper)
    code, text = guarded_run(rig)
    eq((code, rig.results()["verdict"]), (1, "FAIL"), f"in-run: {text[-500:]}")
    eq(M.regrade_dir(rig.out, rig.ledger)["verdict"], "FAIL", "grade DIR agrees")


def case_shared_legs_never_count(M, tmp):
    """(C3-G01) two counted legs that share a run folder, or a kept file (filed with its sha256), never both count: each
    fails LC.CUSTODY, named. CONTROL: the honest batch passes."""
    chains, jobs = healthy_batch()
    eq(M.batch_verdict(grade(M, chains, jobs)), "PASS", "CONTROL")
    for key in ("run_dir", "kept_world"):
        rows = copy.deepcopy(chains)
        l4, l5 = rows[0]["legs"][3], rows[0]["legs"][4]
        l5[key] = l4[key]
        if key == "kept_world":
            l5["kept_world_sha256"] = l4["kept_world_sha256"]
        custody = by_id(grade(M, rows, jobs), "LC.CUSTODY")
        eq(custody.status, "FAIL", f"{key}: {custody.text[:500]}")
        ok(f"L5's {key} is also {jobs[0]['chain']} L4's" in custody.text, custody.text[:900])


# ---------------------------------------------------------------------------------------------------- C3-G02, C3-G04
def results_of(rig: Rig) -> dict:
    return json.loads((rig.out / "results.json").read_text(encoding="utf-8"))


def write_results(rig: Rig, data: dict) -> None:
    (rig.out / "results.json").write_text(json.dumps(data), encoding="utf-8")


def case_grade_dir_numbers_verified(M, tmp):
    """(C3-G02, the checker's G5) grade DIR takes the legs, jobs and reach floor from results.json's NUMBERS, verified
    against their own sha256 and the ledger's registration: editing results.json's own reach_min, jobs or legs changes
    nothing (the two-miss batch stays FAIL); editing the numbers fails their sha256; editing the numbers and their sha256
    together fails against the ledger. CONTROL: the batch, in place."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp, plans={jobs[0]["chain"]: {"L5": {"miss": True}}, jobs[1]["chain"]: {"L5": {"miss": True}}})
    guarded_run(rig)
    original = results_of(rig)
    found = M.regrade_dir(rig.out, rig.ledger)
    eq(found["verdict"], "FAIL", "CONTROL: 4 of 6")
    ok(found["numbers"].startswith("VERIFIED") and "ledger entry #1 registered" in found["numbers"], found["numbers"])
    for label, edit in (("reach_min 0", lambda d: d.update(reach_min=0)),
                        ("jobs without the two misses", lambda d: d.update(jobs=d["jobs"][2:], reach_min=4)),
                        ("legs' L5 proof weakened", lambda d: d["legs"][4].update(proof={"flags": {}, "variables": {
                            "RUSTBORO_CITY_STATE": {"number": 0x405A, "at_least": 7}}, "trainers": {}}))):
        data = copy.deepcopy(original)
        edit(data)
        write_results(rig, data)
        eq(M.regrade_dir(rig.out, rig.ledger)["verdict"], "FAIL", f"{label}: results.json's own copy is never used")
    data = copy.deepcopy(original)
    data["numbers"]["reach_min"] = 0
    write_results(rig, data)
    found = M.regrade_dir(rig.out, rig.ledger)
    ok(found["verdict"] == "FAIL" and found["numbers"].startswith("MISMATCH"), f"numbers edited: {found['numbers']}")
    found = M.regrade_dir(rig.out, None)  # (with no ledger to check: their own sha256 alone refuses them)
    ok(found["verdict"] == "FAIL" and "is not the numbers_sha256 recorded beside them" in found["numbers"], found["numbers"])
    data["numbers_sha256"] = ledger.numbers_sha256(data["numbers"])
    write_results(rig, data)
    found = M.regrade_dir(rig.out, rig.ledger)
    ok(found["verdict"] == "FAIL" and "is not the bounds sha256 the ledger registered" in found["numbers"], found["numbers"])
    found = M.regrade_dir(rig.out, None)
    eq((found["verdict"], found["final"], found["exit"]), ("PASS", "UNVERIFIED", 1),
       "(C4-G01) with no ledger to check, a consistent forgery re-grades PASS from its own numbers, but it is UNVERIFIED: a "
       "graded folder no ledger entry verifies never exits 0")
    write_results(rig, original)


def case_grade_dir_missing_records(M, tmp):
    """(C3-G02, the checker's G5b) a results.json whose frozen-tree or leftover record is missing grades that check FAIL;
    it is never dropped. An older folder with no numbers is graded and printed UNVERIFIED."""
    rig = graded_rig(M, tmp)
    guarded_run(rig)
    original = results_of(rig)
    for key, check_id in (("frozen", "LC.FROZEN"), ("leftover", "LC.LEFTOVER")):
        data = copy.deepcopy(original)
        data[key] = None
        write_results(rig, data)
        found = M.regrade_dir(rig.out, rig.ledger)
        eq((found["verdict"], {c.id: c.status for c in found["checks"]}.get(check_id)), ("FAIL", "FAIL"), f"{key} null")
    data = {k: v for k, v in original.items() if k != "numbers"}
    write_results(rig, data)
    found = M.regrade_dir(rig.out, rig.ledger)
    ok(found["verdict"] == "PASS" and found["numbers"].startswith("UNVERIFIED (no numbers)"), found["numbers"])


def case_grade_dir_moved_out(M, tmp):
    """(C3-G04, the checker's probe_moved_out) an honest --out MOVED after its batch re-grades PASS: a kept line whose
    stored path is gone is read from out/<chain>/<leg>/world_last.jsonl (its sha256 still the row's)."""
    rig = graded_rig(M, tmp / "batch")
    guarded_run(rig)
    moved = tmp / "archive" / "out-moved"
    moved.parent.mkdir()
    shutil.move(str(rig.out), str(moved))
    found = M.regrade_dir(moved, rig.ledger)
    eq(found["verdict"], "PASS", f"{[c.text[:300] for c in found['checks'] if c.status != 'PASS'][:2]}")


class SealTree(FakeTree):
    """(C3-G02's G20) a frozen-tree watch that sees the move ONLY at the seal (the last check)."""

    def seal(self, verdict: str):
        self.moves.append("at the verdict: 1 changed ['ai_player/brain/x.py']")
        return ("FAIL", "FROZEN TREE: FAIL - planted at the seal")


def case_grade_dir_frozen_at_seal(M, tmp):
    """(C3-G02, the checker's G20) a tree move seen only at the seal fails LC.FROZEN in the run, and grade DIR re-grades it
    FAIL too (it reads the recorded watch, never assumes it)."""
    rig = graded_rig(M, tmp, tree=SealTree())
    code, text = guarded_run(rig)
    eq((code, {c["id"]: c["status"] for c in rig.results()["checks"]}["LC.FROZEN"]), (1, "FAIL"), text[-400:])
    found = M.regrade_dir(rig.out, rig.ledger)
    eq((found["verdict"], {c.id: c.status for c in found["checks"]}["LC.FROZEN"]), ("FAIL", "FAIL"), "grade DIR")


# ---------------------------------------------------------------------------------------------------- C3-G03, C3-G06
def case_row_identity_each_field(M, tmp):
    """(C3-G03) EACH of the six identity fields alone: a row whose field is not the registered job's is IGNORED (its chain
    ABSENT: LC.REACH VACUOUS with 5 rows) and named. CONTROL: the honest batch passes."""
    honest, jobs = healthy_batch()
    eq(M.batch_verdict(grade(M, honest, jobs)), "PASS", "CONTROL")
    for key, value in (("chain", "LC-S-7999"), ("pair", "C"), ("personality", "Catcher"), ("starter", "TORCHIC"),
                       ("seed", 7102), ("profile", "ai-livechain-7102")):
        rows = copy.deepcopy(honest)
        rows[0][key] = value
        checks = grade(M, rows, jobs)
        reach = by_id(checks, "LC.REACH")
        eq((M.batch_verdict(checks), reach.status, reach.n), ("FAIL", "VACUOUS", 5), f"{key}: {reach.text[:400]}")
        ok("is not the registered" in reach.text or "not a registered chain" in reach.text, f"{key} named: {reach.text[:600]}")


def case_not_run_after_continuing_leg(M, tmp):
    """(C3-G06, the checker's G6) a stored NOT RUN after a leg whose re-derived continuation holds, with no STOP.txt or
    ABORT.txt in --out and no salvage reason, fails LC.CUSTODY: an impure last leg rewritten as NOT RUN stays FAIL, in
    grade_batch and IN-RUN. CONTROLS: the same stop explained by STOP.txt, or by the orchestrator's salvage reason."""
    chains, jobs = healthy_batch()
    leg = chains[0]["legs"][4]
    next(c for c in leg["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
    leg["continue"] = False
    eq(M.batch_verdict(grade(M, chains, jobs)), "FAIL", "CONTROL: the impure L5")
    legs = LC.legs_of("ch5_rival_meet", real_milestones())

    def hidden(reason: str, stop_files=(), salvaged=()) -> list:
        rows = copy.deepcopy(chains)
        rows[0]["legs"][4] = M.not_run_row({**jobs[0]}, leg, "NOT RUN", reason)
        return M.grade_batch(rows, jobs, 5, 5, (True, "ok"), [], {"most_running": 3}, legs=legs, stop_files=stop_files,
                             salvaged=salvaged)
    checks = hidden("the chain stopped at L4: planted")
    custody = by_id(checks, "LC.CUSTODY")
    eq((M.batch_verdict(checks), custody.status), ("FAIL", "FAIL"), f"a hidden leg: {graded_ok(checks)}")
    ok(f"{jobs[0]['chain']} L5: NOT RUN after L4, whose re-derived continuation holds" in custody.text, custody.text[:800])
    eq(by_id(hidden("the code under test changed mid-batch (STOP.txt)", ["STOP.txt"]), "LC.CUSTODY").status, "PASS",
       "CONTROL: STOP.txt in --out explains it")
    # (the fourth check's C4-G05: its mutant C06) ABORT.txt explains it as well: the disk guard's abort stops every chain
    eq(by_id(hidden("the batch was ABORTED by the harness (disk: free space)", ["ABORT.txt"]), "LC.CUSTODY").status, "PASS",
       "CONTROL: ABORT.txt in --out explains it")
    salvage = "the chain's process ended (it ended without its chain row; see out/x.child.log)"
    eq(by_id(hidden(salvage, salvaged=[jobs[0]["chain"]]), "LC.CUSTODY").status, "PASS",
       "CONTROL: the salvage reason explains it when the orchestrator recorded that salvage (C4-G04)")
    eq(by_id(hidden(salvage), "LC.CUSTODY").status, "FAIL",
       "FAULT (C4-G04): the salvage reason with no salvage the orchestrator recorded explains nothing")
    run_jobs = LC.jobs_of(6201, 6)

    def hide() -> list[str]:
        path = rig.out / "rows" / f"{run_jobs[0]['chain']}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        last = row["legs"][4]
        next(c for c in last["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
        row["legs"][4] = M.not_run_row({**run_jobs[0]}, last, "NOT RUN", "the chain stopped at L4: planted")
        path.write_text(json.dumps(row), encoding="utf-8")
        return []
    rig = graded_rig(M, tmp, leftover=hide)
    code, text = guarded_run(rig)
    eq((code, rig.results()["verdict"]), (1, "FAIL"), f"in-run: {text[-500:]}")


# ---------------------------------------------------------------------------------------------------- C3-H01..H05: R12
def case_closure_resolution_planted(M, tmp):
    """(C3-H01) on a planted tree: CPython's order (a package's __init__.py before X.py) and every module the closure follows
    that Python could import from a file the scan did not read is named: a module beside its package, an extension module
    or a sourceless .pyc beside a closure file, a module with no source, a package whose __init__ is bytecode. CONTROL: a
    namespace folder beside a module, and the same tree without the plants."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/__init__.py")
    plant(root, "ai_player/gates/live_chain.py", "from ai_player.gates import helper\nimport modules.memory\nimport modules.game\n"
                                                 "import modules.ghost\nimport modules.pkgx\nimport modules.plain\n")
    plant(root, "ai_player/gates/helper.py")
    plant(root, "sandbox-pokebot/modules/__init__.py")
    for name in ("memory", "game", "pkgx", "plain"):
        plant(root, f"sandbox-pokebot/modules/{name}.py")
    (root / "sandbox-pokebot" / "modules" / "plain").mkdir()  # a namespace folder: CPython still imports plain.py
    with mock.patch.object(M, "PATH_ROOTS", ()):
        clean = M.closure_scan(root)
    eq(M.resolution_problems(root, clean["modules"]), [], "CONTROL: the tree without the plants")
    plant(root, "sandbox-pokebot/modules/memory/__init__.py")
    plant(root, "sandbox-pokebot/modules/game.cp312-win_amd64.pyd")
    plant(root, "sandbox-pokebot/modules/ghost.pyc")
    plant(root, "sandbox-pokebot/modules/pkgx/__init__.pyc")
    plant(root, "ai_player/gates/helper.pyc")
    with mock.patch.object(M, "PATH_ROOTS", ()):
        scan = M.closure_scan(root)
    ok("sandbox-pokebot/modules/memory/__init__.py" in scan["closure"] and "sandbox-pokebot/modules/memory.py" not in
       scan["closure"], f"CPython's order: the package first: {scan['closure']}")
    found = M.resolution_problems(root, scan["modules"])
    for rel in ("sandbox-pokebot/modules/memory.py:", "sandbox-pokebot/modules/game.cp312-win_amd64.pyd:",
                "sandbox-pokebot/modules/ghost.pyc:", "sandbox-pokebot/modules/pkgx/ (__init__.pyc):",
                "ai_player/gates/helper.pyc:"):
        ok(any(problem.startswith(rel) for problem in found), f"{rel} named: {found}")
    eq(len(found), 5, f"exactly the plants: {found}")


def case_pycache_planted(M, tmp):
    """(C3-H01, the checker's C1) a __pycache__ file CPython would load INSTEAD of a closure file (its header holds the
    source's mtime and size) holding other code is named (check_purity's rule (e), reused). CONTROLS: a genuine cache, a
    stale one (its header does not match: never loaded) and another interpreter's."""
    import importlib._bootstrap_external as ext

    root = tmp / "repo"
    source = plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    plant(root, "ai_player/gates/__init__.py")
    cache = root / "ai_player" / "gates" / "__pycache__"
    cache.mkdir()
    st = source.stat()
    tag = sys.implementation.cache_tag

    def pyc(text: str, mtime: int) -> bytes:
        return bytes(ext._code_to_timestamp_pyc(compile(text, str(source), "exec", dont_inherit=True), mtime, st.st_size))
    target = cache / f"live_chain.{tag}.pyc"
    for label, data, want in (("genuine", pyc("x = 1\n", int(st.st_mtime)), False),
                              ("stale", pyc("x = 2\n", int(st.st_mtime) - 100), False),
                              ("forged", pyc("x = 2\n", int(st.st_mtime)), True)):
        target.write_bytes(data)
        found = M.pycache_problems(root, [source])
        eq(bool(found), want, f"{label}: {found}")
    ok("holds different code" in found[0] and f"ai_player/gates/__pycache__/live_chain.{tag}.pyc" in found[0], found)
    ok(any(f"live_chain.{tag}.pyc" in problem for problem in M.closure_missing(root)[0]), "and R12 (closure_missing) has it")
    target.rename(cache / "live_chain.cpython-311.pyc")
    eq(M.pycache_problems(root, [source]), [], "CONTROL: another interpreter's cache is never loaded by this one")


def case_resolution_enforced_register(M, tmp):
    """(C3-H01, the checker's A2) a registration and a graded run are REFUSED (R12) while a package folder sits beside a
    hashed closure module (modules/memory/ beside memory.py), naming it; the ledger untouched. CONTROL: removed, it
    registers (closure_enforced_register)."""
    repo, path = fake_repo(tmp), tmp / "ledger.json"
    path.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    package = plant(repo, "sandbox-pokebot/modules/memory/__init__.py")
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            code = M.register_run("ch5", None, repo=repo, path=path)
        rig = graded_rig(M, tmp / "rig")
        rig.deps.closure = lambda: M.closure_missing(repo)
        run_code, text = guarded_run(rig)
    finally:
        shutil.rmtree(package.parent)
    eq(code, 2, buffer.getvalue()[-500:])
    ok("R12" in buffer.getvalue() and "sandbox-pokebot/modules/memory.py: a module named like the package" in
       buffer.getvalue(), buffer.getvalue()[-700:])
    eq((run_code, rig.entry()["status"]), (2, "registered"), text[-400:])
    ok("sandbox-pokebot/modules/memory/__init__.py" in text, text[-700:])


def case_toplevel_planted(M, tmp):
    """(C3-H02, the checker's B1-B3) an entry of a script folder that would run INSTEAD of a module is named: a standard
    library name at the repository root, in ai_player/gates and in sandbox-pokebot (a .py and an extension module), a
    package named like a module a closure file imports. CONTROLS: the framework's own names, the declared exemptions, a
    namespace folder named like the library (it never replaces a regular module), and names nothing imports."""
    root = tmp / "repo"
    for rel in ("random.py", "ai_player/gates/argparse.py", "sandbox-pokebot/argparse.py",
                "ai_player/gates/zipfile.cp312-win_amd64.pyd", "sandbox-pokebot/yaml/__init__.py",
                "ai_player/__init__.py", "sandbox-pokebot/modules/__init__.py", "sandbox-pokebot/pokebot.py",
                "sandbox-pokebot/profiles/x.yml", "sandbox-pokebot/mgba/__init__.py", "sandbox-pokebot/json/readme.txt",
                "tools/helper.py", "notes.txt", "ai_player/gates/ledger.py"):
        plant(root, rel)
    tops = {"yaml", "modules", "pokebot", "profiles", "mgba", "ai_player", "argparse", "json", "ledger_x"}
    found = M.toplevel_problems(root, tops)
    want = ["ai_player/gates/argparse.py", "ai_player/gates/zipfile.cp312-win_amd64.pyd", "random.py",
            "sandbox-pokebot/argparse.py", "sandbox-pokebot/yaml"]
    eq(sorted(problem.split(":")[0] for problem in found), want, f"exactly the shadows: {found}")
    plant(root, "ai_player/gates/live_chain.py", "import argparse\n")
    ok(any(problem.startswith("random.py:") for problem in M.closure_missing(root)[0]), "and R12 (closure_missing) has it")


#: the emulator's library as the main checkout holds it (listed 2026-11-06, read only): a package with its compiled
#: _pylib, its DLLs and a __pycache__ (the files' contents do not matter to any rule; their names and kinds do)
MGBA_LAYOUT = ("__init__.py", "_pylib.pyd", "core.py", "image.py", "gba.py", "mgba.dll", "SDL2.dll",
               "__pycache__/__init__.cpython-312.pyc", "__pycache__/core.cpython-312.pyc")


def case_toplevel_mgba_exempt(M, tmp):
    """(The full regression lane of 2026-11-06 on d1a853bc, where test_closure_toplevel_names failed because the lane's
    tree had the emulator installed) sandbox-pokebot/mgba, the emulator's library, exists wherever the emulator is
    installed (the main checkout always): git-ignored and unhashed BY DESIGN, it is exempt BY NAME, in sandbox-pokebot
    only. CONTROL: its real layout planted and imported the way the framework imports it (modules/libmgba.py,
    modules/gui/glfw.py) is named by no rule of R12 (`closure_missing`: resolution, __pycache__, top-level shadows).
    FAULTS: an unknown top-level name beside it that a closure file imports is still named, and so is the name mgba in
    the other script folders (a package at the repository root, a module in ai_player/gates)."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "import modules.libmgba\nimport modules.gui.glfw\n")
    plant(root, "sandbox-pokebot/modules/__init__.py")
    plant(root, "sandbox-pokebot/modules/libmgba.py",
          "import mgba.core\nimport mgba.image\nfrom mgba._pylib import ffi, lib\nfrom mgba.gba import GBA\n")
    plant(root, "sandbox-pokebot/modules/gui/__init__.py")
    plant(root, "sandbox-pokebot/modules/gui/glfw.py", "import mgba.image\n")
    for rel in MGBA_LAYOUT:
        plant(root, f"sandbox-pokebot/mgba/{rel}")
    scan = M.closure_scan(root)
    ok("mgba" in scan["tops"] and (root / "sandbox-pokebot" / "mgba" / "__init__.py").is_file(),
       f"not vacuous: a closure file imports mgba, and mgba is a package beside them: {sorted(scan['tops'])}")
    problems = [entry for entry in M.closure_missing(root)[0] if ": " in entry]  # "path: why" (an unhashed file has none)
    eq(problems, [], "CONTROL: a present sandbox-pokebot/mgba is named by no rule of R12")
    eq(M.toplevel_problems(root, scan["tops"]), [], "CONTROL: the top-level rule itself")
    # FAULTS: an unknown top-level name beside it, and mgba in the other script folders
    plant(root, "sandbox-pokebot/modules/libmgba.py", "import mgba.core\nimport mgbx\n")
    plant(root, "sandbox-pokebot/mgbx/__init__.py")
    plant(root, "mgba/__init__.py")
    plant(root, "ai_player/gates/mgba.py")
    found = M.toplevel_problems(root, M.closure_scan(root)["tops"])
    eq(sorted(problem.split(":")[0] for problem in found), ["ai_player/gates/mgba.py", "mgba", "sandbox-pokebot/mgbx"],
       f"FAULT: exactly the unknown name and mgba outside sandbox-pokebot: {found}")
    ok(all(not entry.startswith("sandbox-pokebot/mgba:") for entry in M.closure_missing(root)[0]),
       "and R12 still does not name sandbox-pokebot/mgba itself")


def case_python_env_refused(M, tmp):
    """(C3-H02, the checker's E2) a graded run is REFUSED (R12) while PYTHONPATH (or PYTHONHOME, PYTHONSTARTUP) is set, the
    ledger untouched; every chain process's environment (and so the truth reads') drops them, and the chain process clears
    them at start. CONTROL: a development batch runs. (The fourth check's C4-H02) EVERY PYTHON* variable but the four of
    PYTHON_ENV_ALLOWED: PYTHONPYCACHEPREFIX (another cache folder), PYTHONCASEOK (even set to nothing: Python reads only that
    it is there) and PYTHONUSERBASE (another user site-packages) are refused too and dropped from the chain processes;
    CONTROL: the four allowed ones set, a graded run proceeds and the chain processes keep them."""
    refused_names = {"PYTHONPATH": str(tmp), "PYTHONHOME": str(tmp), "PYTHONSTARTUP": str(tmp),
                     "PYTHONPYCACHEPREFIX": str(tmp), "PYTHONCASEOK": "", "PYTHONUSERBASE": str(tmp)}
    for name, value in refused_names.items():
        rig = graded_rig(M, tmp / name)
        before = rig.ledger.read_bytes()
        code, text = guarded_run(rig, environ={name: value})
        eq((code, rig.ledger.read_bytes() == before), (2, True), f"{name}: {text[-400:]}")
        ok("REFUSED: R12" in text and name in text, text[-400:])
    allowed = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    eq(set(allowed), set(M.PYTHON_ENV_ALLOWED), "the allow-list is exactly these four")
    rig = graded_rig(M, tmp / "allowed")
    code, text = guarded_run(rig, environ=allowed)
    eq((code, rig.entry()["status"]), (0, "done"), f"CONTROL: the four allowed ones set, a graded run proceeds: {text[-400:]}")
    rig, args = dev_rig(M, tmp / "dev")
    eq(guarded_run(rig, args, environ={"PYTHONPATH": str(tmp)})[0], 0, "CONTROL: a development batch runs")
    with mock.patch.dict(os.environ, {**refused_names, **allowed, "LC_OTHER": "1"}):
        env = M.child_env()
        eq(([k for k in refused_names if k in env], env.get("LC_OTHER"), {k: env.get(k) for k in allowed}),
           ([], "1", allowed), "the chain processes' environment: every refused one dropped, the allowed ones kept")
        job = tmp / "job.json"
        job.write_text(json.dumps({"chain": "LC-S-1", "profile": "ai-livechain-1"}), encoding="utf-8")
        seen: dict = {}
        with mock.patch.object(M, "run_chain", lambda j: seen.update(env=dict(os.environ)) or {"legs": []}), \
                contextlib.redirect_stdout(io.StringIO()):
            M.child(job)
        eq([k for k in refused_names if k in seen["env"]], [], "the chain process clears them")


def case_closure_refusal_names_all(M, tmp):
    """(C3-H04) R12 names EVERY file (13 planted plugins: all 13)."""
    files = [f"sandbox-pokebot/plugins/zz_{i:02d}.py" for i in range(13)]
    text = M.closure_refusal(files)
    eq([f for f in files if f not in text], [], text)


def case_closure_ai_starts_planted(M, tmp):
    """(C3-H05, the checker's probe_ai_door) an absolute modules.* import of the AI's own file STARTS the closure: the
    framework module only the AI imports is in it (and so hashed or refused); the AI's file itself is not, and neither is
    an import of ai_player/evidence or the gates' own folder walked as AI code. CONTROL: without that import it is not."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    plant(root, "ai_player/host/eyes.py", "x = 1\n")
    plant(root, "ai_player/evidence/note.py", "import modules.never\n")
    for name in ("__init__", "zz_door", "never"):
        plant(root, f"sandbox-pokebot/modules/{name}.py")
    with mock.patch.object(M, "PATH_ROOTS", ()):
        eq([rel for rel in M.grader_closure(root) if "zz_door" in rel or "never" in rel], [], "CONTROL: no AI import")
        plant(root, "ai_player/host/eyes.py", "from modules.zz_door import DOOR\n")
        found = M.grader_closure(root)
    ok("sandbox-pokebot/modules/zz_door.py" in found and "sandbox-pokebot/modules/__init__.py" in found, found)
    ok("ai_player/host/eyes.py" not in found and "sandbox-pokebot/modules/never.py" not in found, found)


# ==================================================================================================== THE FOURTH FIX ROUND
# (the fourth check's C4-E01..E07, C4-G01..G06, C4-H01..H08, 2026-11-06) each new or changed guard: a FAULT case (the
# finding's own scenario), a CONTROL case, and a mutant in MUTANTS
def run_capturing(rig: Rig, args: argparse.Namespace | None = None) -> tuple[object, str]:
    """run_batch as `Rig.run` runs it, its output kept even when it RAISES: (its exit code, or what it raised; the output).
    A KeyboardInterrupt is caught here: the cases below inspect it."""
    buffer = io.StringIO()
    with mock.patch.dict(os.environ, {}), mock.patch.object(rig.M, "ai_code_sha256", lambda repo=None: "0" * 64), \
            contextlib.redirect_stdout(buffer):
        for name in [name for name in os.environ if name.upper().startswith("PYTHON")]:
            os.environ.pop(name, None)
        try:
            result: object = rig.M.run_batch(args or run_args(out=str(rig.out)), rig.deps)
        except BaseException as error:  # noqa: BLE001 - the case inspects it (a KeyboardInterrupt among them)
            result = error
    return result, buffer.getvalue()


def grade_dir_out(M, out: Path, ledger_path) -> tuple[int, str]:
    """`grade DIR` on `out`: (its exit code, its output)."""
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        code = M.grade_dir(out, ledger_path)
    return code, buffer.getvalue()


# ---------------------------------------------------------------------------------------------------- C4-E01: the KIND
def case_world_kind_untrusted(M, tmp):
    """(C4-E01) `finish_leg` on the AI's run folder NEVER raises, whatever KIND its files are: a world.jsonl that is a
    FOLDER is NOT MEASURED (no size, a note; the leg fails C3); one the OS refuses to open is read again, then NOT
    MEASURED (its size still recorded and the file deleted; the leg fails C3); a small file that cannot be copied is a
    note. CONTROL: a regular world file is measured, kept and deleted."""
    def run_dir(name: str, world: bool = True) -> Path:
        folder = tmp / name
        folder.mkdir()
        if world:
            (folder / "world.jsonl").write_text(snapshot(1, 1) + "\n" + snapshot(2, 4) + "\n", encoding="utf-8")
        (folder / "ai_player.log").write_text("[AI-HANDS] outcome=done\n", encoding="utf-8")
        return folder

    def finished(folder: Path, keep: str) -> dict:
        row: dict = {"notes": []}
        try:
            M.finish_leg(row, folder, tmp / keep)
        except Exception as error:  # noqa: BLE001
            raise AssertionError(f"finish_leg raised on the AI's {folder.name}: {error!r}") from None
        return row
    row = finished(run_dir("control"), "keep_control")
    ok(row["measures"]["world"]["last_ok"] and isinstance(row["world_file"]["bytes"], int) and row["world_file"]["deleted"]
       and Path(row["kept_world"]).is_file(), f"CONTROL: measured, kept, deleted: {row['world_file']}")
    folder = run_dir("folder", world=False)
    (folder / "world.jsonl").mkdir()
    (folder / "world.jsonl" / "inside.txt").write_text(snapshot(1, 1) + "\n", encoding="utf-8")
    row = finished(folder, "keep_folder")
    eq((row["measures"]["world"], row["world_file"]["bytes"], row["world_file"]["present"]), (None, None, True),
       f"a FOLDER named world.jsonl is NOT MEASURED: {row['world_file']}")
    ok(any("not a regular file" in note for note in row["notes"]), row["notes"])
    stops(M, base_row(tmp, measures=row["measures"], world_file=row["world_file"], kept_world=row["kept_world"]),
          needle="C3 its world.jsonl was not measured")
    locked = run_dir("locked")
    real_open = open

    def refuse(file, *args, **kwargs):
        if Path(str(file)) == locked / "world.jsonl":
            raise PermissionError(13, "the file is held by another process")
        return real_open(file, *args, **kwargs)
    with mock.patch.object(M, "WORLD_READ_PAUSE_SECONDS", 0), mock.patch("builtins.open", refuse):
        row = finished(locked, "keep_locked")
    ok(row["measures"]["world"] is None and any(f"could not be read in {M.WORLD_READ_TRIES} tries" in note
                                                for note in row["notes"]), row["notes"])
    ok(isinstance(row["world_file"]["bytes"], int) and row["world_file"]["deleted"],
       f"its size is still recorded and it is deleted: {row['world_file']}")
    stops(M, base_row(tmp, measures=row["measures"], world_file=row["world_file"], kept_world=row["kept_world"]),
          needle="C3 its world.jsonl's last line did not parse")
    with mock.patch.object(M.shutil, "copy2", side_effect=PermissionError(13, "held")):
        row = finished(run_dir("copy"), "keep_copy")
    ok(any("could not be copied" in note for note in row["notes"]), row["notes"])


def case_e2e_world_folder_graded(M, tmp):
    """(C4-E01, the check's W1) a world.jsonl that is a FOLDER, in a batch that FAILS (two chains miss at L2): GRADED, FAIL,
    exit 1, never the harness's ERROR, and no chain process died; a chain process that DIES with a folder world.jsonl is
    salvaged by the orchestrator the same way (its finish_leg runs there). CONTROL: the same leg writing no world file."""
    jobs = LC.jobs_of(6201, 6)
    misses = {jobs[0]["chain"]: {"L2": {"miss": True}}, jobs[3]["chain"]: {"L2": {"miss": True}}}
    for label, extra in (("control", {jobs[1]["chain"]: {"L3": {"no_world": True}}}),
                         ("folder", {jobs[1]["chain"]: {"L3": {"world_is_folder": True}}}),
                         ("folder_and_dies", {jobs[2]["chain"]: {"L3": {"world_is_folder": True, "die": True}}})):
        rig = graded_rig(M, tmp / label, plans={**misses, **extra}, real_child=True)
        code, text = guarded_run(rig)
        verdict = rig.entry().get("verdict") or ""
        eq((code, rig.child_errors), (1, []), f"{label}: GRADED FAIL, no chain process died: {verdict[:300]}")
        ok(verdict.startswith("GRADED, FAIL") and "ERROR" not in verdict, f"{label}: {verdict[:300]}")
    row = json.loads((rig.out / "rows" / f"{jobs[2]['chain']}.json").read_text(encoding="utf-8"))
    eq(row["legs"][2]["status"], "SALVAGED", "the dead chain's L3 is salvaged by the orchestrator")
    ok(any("not a regular file" in note for note in row["legs"][2]["notes"]), row["legs"][2]["notes"])


# ---------------------------------------------------------------------------------------------------- C4-E02, C4-E07: --out
def case_out_second_launch_refused(M, tmp):
    """(C4-E02, the check's RACE) a launch CLAIMS --out (BATCH.claim.json, created exclusively) before it writes anything
    there: a second launch of the same graded run whose own listing came before the first's prepare_out (so it saw an
    empty --out) is REFUSED (R11, exit 2) with the ledger untouched and removes nothing of the first's: the first launch's
    six job files are intact and its batch PASSES. On its own: a second prepare_out on a claimed --out is refused even
    before the first wrote any job file. CONTROL: a single launch (e2e_graded_pass)."""
    out = tmp / "unit" / "out"
    M.prepare_out(out, {})
    message = refused(M, M.prepare_out, out, {"LC-S-1.job.json": {"x": 1}})
    ok(message.startswith("R11") and "CLAIMED by another launch" in message, message)
    eq(sorted(os.listdir(out)), [M.OUT_CLAIM], "the first launch's claim is intact, and the second wrote nothing")
    rig = graded_rig(M, tmp / "a")
    second = Rig(M, tmp / "b")
    second.deps.ledger_path = rig.ledger
    seen: dict = {}

    def launch_second(job: dict) -> None:
        if seen:
            return
        before = rig.ledger.read_bytes()
        with mock.patch.object(M, "out_listing", lambda path: {"out_entries": []}):
            code, text = second.run(run_args(out=str(rig.out)))
        seen.update(code=code, text=text, ledger=rig.ledger.read_bytes() == before,
                    jobs=sorted(p.name for p in rig.out.glob("*.job.json")))
    rig.pre_spawn = launch_second
    code, text = guarded_run(rig)
    eq((seen.get("code"), seen.get("ledger")), (2, True),
       f"the second launch is refused, the ledger untouched: {seen.get('text', '')[-500:]}")
    ok("REFUSED: R11" in seen["text"] and "CLAIMED by another launch" in seen["text"], seen["text"][-500:])
    eq(len(seen["jobs"]), 6, f"the first launch's job files are intact: {seen['jobs']}")
    eq((code, rig.entry()["status"]), (0, "done"), f"the first launch's batch PASSES: {text[-500:]}")


def case_out_written_after_listing(M, tmp):
    """(C4-E02) once claimed, --out must hold ONLY the claim: a file another process wrote after the listing (here a
    STOP.txt a stale listing missed) refuses the launch (R11, exit 2), the ledger untouched, and that file is left as it
    was (the claim is removed). CONTROL: e2e_out_empty_proceeds."""
    rig = graded_rig(M, tmp)
    rig.out.mkdir(parents=True)
    (rig.out / "STOP.txt").write_text("left by another process\n", encoding="utf-8")
    before = rig.ledger.read_bytes()
    with mock.patch.object(M, "out_listing", lambda path: {"out_entries": []}):
        code, text = guarded_run(rig)
    eq((code, rig.ledger.read_bytes() == before, rig.handles), (2, True, []), text[-500:])
    ok("REFUSED: R11" in text and "no longer empty" in text, text[-500:])
    eq(sorted(os.listdir(rig.out)), ["STOP.txt"], "only that file is left: the claim made is removed")


def case_out_undo_edges(M, tmp):
    """(C4-E07, the check's N01, N02, N05) prepare_out removes EVERYTHING it made: an invalid last part under MISSING
    parents leaves no parent behind; the 3rd job file failing leaves --out as it was (a missing one gone, an empty one
    empty); ledger.begin raising something other than a refusal (PermissionError) leaves --out removed and escapes
    run_batch (main's exit 5), the ledger untouched. CONTROL: e2e_out_undone_on_ledger_refusal."""
    message = refused(M, M.prepare_out, tmp / "np2" / "deeper" / "x?y", {})
    ok(message.startswith("R11") and not (tmp / "np2").exists(), f"no parent folder left behind: {message}")
    real = M._write_json
    for label, pre in (("missing", False), ("empty", True)):
        out = tmp / label / "out"
        if pre:
            out.mkdir(parents=True)
        calls = {"n": 0}

        def third_fails(path, data):
            calls["n"] += 1
            if calls["n"] == 3:
                raise OSError("a planted fault: the disk is full")
            return real(path, data)
        with mock.patch.object(M, "_write_json", third_fails):
            message = refused(M, M.prepare_out, out, {f"LC-S-{i}.job.json": {"i": i} for i in range(6)})
        ok(message.startswith("R11"), message)
        if pre:
            eq(sorted(os.listdir(out)), [], f"{label}: an EMPTY --out is left empty")
        else:
            ok(not (tmp / label).exists(), f"{label}: the --out (and the folder above it) made here are removed")
    rig = graded_rig(M, tmp / "begin")
    before = rig.ledger.read_bytes()
    with mock.patch.object(M, "begin", side_effect=PermissionError(13, "the ledger is held open")):
        result, text = run_capturing(rig)
    ok(isinstance(result, PermissionError), f"the raise escapes run_batch (main exits 5): {result!r}")
    ok(not rig.out.exists() and rig.ledger.read_bytes() == before, f"--out removed, the ledger untouched: {text[-300:]}")


# ---------------------------------------------------------------------------------------------------- C4-E03: Ctrl+C twice
def _guard_rig(M, tmp: Path) -> Rig:
    """A graded batch whose disk guard raises (RuntimeError) with three chains running: the chains-run guard's case."""
    reads = {"n": 0}

    def free(path):
        reads["n"] += 1
        if reads["n"] == 2:
            raise RuntimeError("a planted fault in the disk guard")
        return 100.0
    return graded_rig(M, tmp, alive=50, free=free,
                      pre_spawn=lambda job: planted_folder(Path(job["build_root"]), job["profile"],
                                                           f"20261105-000000-{job['chain']}-L1"))


def case_guard_second_interrupt(M, tmp):
    """(C4-E03, the check's W3) a SECOND Ctrl+C while the guard finishes the entry: from the end sweep (1), from the ledger
    write itself (2), while killing a chain (3): each time the entry is still FINISHED as ERROR, the other chains are still
    killed and the interrupt goes on after; the guard printed its line FIRST, SIGINT was IGNORED while it ran and the
    handler is restored after. (4) an end sweep that raises an ordinary exception (the check's N03) also leaves the entry
    finished, exit 4. CONTROL: chains_interrupt_finishes_entry (one Ctrl+C)."""
    import signal
    handler = signal.getsignal(signal.SIGINT)
    want = ERROR_OF.format(kind="RuntimeError", message="a planted fault in the disk guard", stage="while the chains ran")
    try:
        rig = _guard_rig(M, tmp / "sweep")
        seen: list = []

        def sweep(jobs, build_root):
            seen.append(signal.getsignal(signal.SIGINT))
            raise KeyboardInterrupt()
        with mock.patch.object(M, "end_sweep", sweep):
            result, text = run_capturing(rig)
        ok(isinstance(result, KeyboardInterrupt), f"(1) the interrupt goes on after the finish: {result!r}")
        eq(rig.entry()["status"], "done", f"(1) a Ctrl+C from the end sweep: the entry is still FINISHED: {text[-600:]}")
        ok(rig.entry()["verdict"].startswith(f"GRADED, {want}"), rig.entry()["verdict"])
        eq(seen, [signal.SIG_IGN], "(1) while the guard ran, Ctrl+C was IGNORED")
        ok(signal.getsignal(signal.SIGINT) is handler, "(1) and the handler is restored after")
        first = text.find("[LC] the harness stopped (RuntimeError while the chains ran)")
        ok(0 <= first < text.find("LEDGER: entry #"), f"(1) the guard's line comes first: {text[:900]}")
        rig = graded_rig(M, tmp / "write", alive=50)
        calls = {"sleep": 0, "finish": 0}

        def sleep(seconds):
            calls["sleep"] += 1
            if calls["sleep"] == 6:
                raise KeyboardInterrupt()
        rig.deps.sleep = sleep
        real_finish = M.finish_entry

        def finish(*args, **kwargs):
            calls["finish"] += 1
            if calls["finish"] == 1:
                raise KeyboardInterrupt()
            return real_finish(*args, **kwargs)
        with mock.patch.object(M, "finish_entry", finish):
            result, text = run_capturing(rig)
        ok(isinstance(result, KeyboardInterrupt), f"(2) {result!r}")
        eq(rig.entry()["status"], "done", f"(2) a Ctrl+C from the ledger write: FINISHED: {text[-600:]}")
        ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness: KeyboardInterrupt"), rig.entry()["verdict"])
        rig = _guard_rig(M, tmp / "kill")
        spawn = rig.spawn

        def spawn_first_interrupts(job, job_path, log_path):
            handle = spawn(job, job_path, log_path)
            if len(rig.handles) == 1:
                def interrupted() -> None:
                    raise KeyboardInterrupt()
                handle.kill_tree = interrupted
            return handle
        rig.deps.spawn = spawn_first_interrupts
        result, text = run_capturing(rig)
        ok(isinstance(result, KeyboardInterrupt), f"(3) {result!r}")
        eq(rig.entry()["status"], "done", f"(3) a Ctrl+C while killing a chain: FINISHED: {text[-600:]}")
        ok(len(rig.handles) == 3 and all(handle.killed for handle in rig.handles[1:]), "(3) the other chains are killed")
        rig = _guard_rig(M, tmp / "raise")
        with mock.patch.object(M, "end_sweep", side_effect=RuntimeError("a planted fault in the sweep")):
            result, text = run_capturing(rig)
        eq((result, rig.entry()["status"]), (4, "done"), f"(4) an end sweep that raises: {text[-600:]}")
        ok("the end sweep could not run: RuntimeError: a planted fault in the sweep" in evidence_text(rig), "(4) named")
    finally:
        signal.signal(signal.SIGINT, handler)


def case_error_finish_retried(M, tmp):
    """(C3-E03, kept by the fourth round's loop) the ERROR verdict's ledger write is retried like the computed one: a ledger
    that refuses the computed verdict every time and the ERROR verdict twice (a lock another writer holds) still ends
    'done' with ERROR, exit 4. CONTROL: ledger_finish_computed_unwritable."""
    rig = graded_rig(M, tmp)
    real, tried = ledger.finish, []

    def flaky(entry_id, verdict, evidence, path=ledger.LEDGER):
        if "ERROR (harness:" not in verdict:
            raise PermissionError(13, "held open by another program")
        tried.append(verdict)
        if len(tried) <= 2:
            raise PermissionError(13, "held open by another program")
        return real(entry_id, verdict, evidence, path=path)
    with mock.patch.object(ledger, "finish", flaky):
        code, text = guarded_run(rig)
    eq((code, rig.entry()["status"], len(tried)), (4, "done", 3), f"the ERROR write retried: {text[-500:]}")
    ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness: LedgerUnwritten:"), rig.entry()["verdict"][:200])


def case_guard_after_finish_keeps_verdict(M, tmp):
    """(C4-E03) a Ctrl+C that comes right AFTER the computed verdict was written (as the ledger write returns): the guard
    writes nothing over it: the entry stays 'done' with its computed PASS, no ERROR record is left beside results.json,
    and the interrupt goes on. CONTROL: e2e_graded_pass."""
    rig = graded_rig(M, tmp)
    real_finish = M.finish_entry

    def finish_then_interrupt(entry_id, verdict, *args, **kwargs):
        why = real_finish(entry_id, verdict, *args, **kwargs)
        if "ERROR (harness:" not in verdict:
            raise KeyboardInterrupt()
        return why
    with mock.patch.object(M, "finish_entry", finish_then_interrupt):
        result, text = run_capturing(rig)
    ok(isinstance(result, KeyboardInterrupt), repr(result))
    eq(rig.entry()["status"], "done", text[-400:])
    ok(rig.entry()["verdict"].startswith("GRADED, PASS"), f"the computed verdict stands: {rig.entry()['verdict'][:200]}")
    ok(not (rig.out / M.RESULTS_ERROR).exists(), "no ERROR record beside the finished batch")
    ok("was already FINISHED with the batch's computed verdict" in text, text[-500:])


# ---------------------------------------------------------------------------------------------------- C4-E04, C4-E05
def case_lone_surrogate_graded(M, tmp):
    """(C4-E04, the check's W2) a lone surrogate in the AI's exit_reason (two chains' L3, every leg reaching): no chain
    process dies, the batch is GRADED PASS (6 of 6), and the leg's outcome is kept ESCAPED, in the row file and in the
    chain's own row; `_write_json` writes any str. CONTROL: e2e_graded_pass."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "batch", real_child=True, plans={jobs[0]["chain"]: {"L3": {"lone_surrogate": True}},
                                                               jobs[1]["chain"]: {"L3": {"lone_surrogate": True}}})
    code, text = guarded_run(rig)
    eq((code, rig.child_errors), (0, []), f"no chain process died, PASS: {(rig.entry().get('verdict') or '')[:300]}")
    ok(rig.entry()["verdict"].startswith("GRADED, PASS"), rig.entry()["verdict"][:300])
    row = json.loads((rig.out / "rows" / f"{jobs[0]['chain']}.json").read_text(encoding="utf-8"))
    eq(row["legs"][2]["outcome"], "play: done \\ud800", "kept ESCAPED in the row file")
    chain, _, _ = play(M, tmp / "one", {"L3": {"lone_surrogate": True}})
    eq(chain["legs"][2]["outcome"], "play: done \\ud800", "and in the chain's own row (untrusted_text)")
    path = tmp / "any.json"
    try:
        M._write_json(path, json.loads('{"a": "x\\ud800", "\\udcff": ["\\ud800"], "n": 1}'))
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"_write_json raised on text UTF-8 cannot take: {error!r}") from None
    eq(json.loads(path.read_text(encoding="utf-8")), {"a": "x\\ud800", "\\udcff": ["\\ud800"], "n": 1},
       "_write_json escapes what UTF-8 cannot take, keys too")


def case_finish_entry_only_error(M, tmp):
    """(C4-E05, the check's F1) finish-entry writes ONLY this driver's own ERROR verdict, rebuilt from results.error.json:
    a hand-edited PASS in ledger.unfinished.json, a PASS in both files, results.error.json naming other numbers or saying
    the ledger WAS finished, and no results.error.json (with, since the fifth check's C5-02, no copy of its record in
    ledger.unfinished.json either) are each REFUSED (exit 2, the ledger untouched). CONTROL: the files as the guard wrote
    them finish the entry. (The copy alone: finish_entry_without_error_record.)"""
    rig = graded_rig(M, tmp)
    with mock.patch.object(ledger, "finish", side_effect=PermissionError(13, "held open by another program")):
        code, _ = guarded_run(rig)
    eq((code, rig.entry()["status"]), (4, "started"), "the ledger could not be written")
    paths = {"unfinished": rig.out / M.UNFINISHED, "record": rig.out / M.RESULTS_ERROR}
    original = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in paths.items()}
    data, record = original["unfinished"], original["record"]
    passing = M.error_line("GRADED", True, "PASS", record["to"], record["seeds"], record["numbers_sha256"])
    attacks = {"a hand-edited PASS": ({**data, "verdict": "GRADED, PASS: live chain held-out (EDITED BY HAND)"}, record),
               "a PASS in both files": ({**data, "verdict": passing}, {**record, "verdict": "PASS"}),
               "other numbers": (data, {**record, "numbers_sha256": "0" * 64}),
               "the ledger said finished": (data, {**record, "ledger_finished": True}),
               "no results.error.json and no copy": ({k: v for k, v in data.items() if k != "error_record"}, None)}
    for label, (unfinished, error_record) in attacks.items():
        paths["unfinished"].write_text(json.dumps(unfinished), encoding="utf-8")
        if error_record is None:
            paths["record"].unlink()
        else:
            paths["record"].write_text(json.dumps(error_record), encoding="utf-8")
        before = rig.ledger.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            code = M.main(["finish-entry", str(rig.out), "--ledger", str(rig.ledger)])
        eq((code, rig.ledger.read_bytes() == before), (2, True), f"{label}: REFUSED: {buffer.getvalue()[-400:]}")
    for name, path in paths.items():
        path.write_text(json.dumps(original[name]), encoding="utf-8")
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        code = M.main(["finish-entry", str(rig.out), "--ledger", str(rig.ledger)])
    eq((code, rig.entry()["status"]), (0, "done"), f"CONTROL: {buffer.getvalue()[-400:]}")
    ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness: LedgerUnwritten:"), rig.entry()["verdict"][:200])


# ---------------------------------------------------------------------------------------------------- C4-G01..G04, C4-E06
def case_grade_dir_never_better_than_ledger(M, tmp):
    """(C4-G01; the threat model's (c)) grade DIR reads the batch's ledger entry NOW and never reports better than it, on a
    FAIL batch (two L5 misses): (A) its numbers deleted and results.json's reach_min 0: the ledger's FAIL, never exit 0;
    (B) its numbers moved to seeds 9001-9006 with reach_min 0 and the sha256 recomputed: MISMATCH (its jobs are not those
    seeds'), never VERIFIED, never exit 0; (C) its rows forged so the re-grade PASSES (the missed L5s' stored truths
    rewritten as held): the ledger's FAIL wins, exit 1. On a PASS batch: (D) with no ledger, and with its numbers deleted:
    UNVERIFIED, exit 1; (E) results.json's ledger id changed: the entry is still found (by its seeds and bounds sha256: a
    merged ledger renumbers entries), VERIFIED, exit 0. CONTROLS: both folders in place (exit 1, exit 0)."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "fail", plans={jobs[0]["chain"]: {"L5": {"miss": True}}, jobs[1]["chain"]: {"L5": {"miss": True}}})
    guarded_run(rig)
    original = results_of(rig)
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    eq(code, 1, f"CONTROL: the FAIL batch in place: {text[-300:]}")
    data = {key: value for key, value in original.items() if key != "numbers"}
    data["reach_min"] = 0
    write_results(rig, data)
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "GRADE DIR VERDICT: GRADED: FAIL" in text, f"(A) never exit 0: {text[-400:]}")
    data = copy.deepcopy(original)
    data["seeds"] = data["numbers"]["seeds"] = [9001, 9006]
    data["numbers"]["reach_min"] = 0
    data["numbers_sha256"] = ledger.numbers_sha256(data["numbers"])
    write_results(rig, data)
    found = M.regrade_dir(rig.out, rig.ledger)
    ok(found["numbers"].startswith("MISMATCH") and "are not one per seed of 9001-9006" in found["numbers"], found["numbers"])
    eq(found["exit"], 1, "(B) never exit 0")
    write_results(rig, original)
    for job in jobs[:2]:
        path = rig.out / "rows" / f"{job['chain']}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        last = row["legs"][4]
        last["truth_after"]["marks"].update(held_marks(last["proof"]))
        last["continue"], last["reached"], row["reached_to"] = True, True, True
        path.write_text(json.dumps(row), encoding="utf-8")
    found = M.regrade_dir(rig.out, rig.ledger)
    eq((found["verdict"], found["final"], found["exit"]), ("PASS", "FAIL", 1), "(C) rows forged to PASS: the ledger's FAIL")
    rig = graded_rig(M, tmp / "pass")
    guarded_run(rig)
    original = results_of(rig)
    eq(grade_dir_out(M, rig.out, rig.ledger)[0], 0, "CONTROL: the PASS batch in place exits 0")
    eq(M.regrade_dir(rig.out, None)["final"], "UNVERIFIED", "(D) a graded folder with no ledger: UNVERIFIED")
    write_results(rig, {key: value for key, value in original.items() if key != "numbers"})
    found = M.regrade_dir(rig.out, rig.ledger)
    eq((found["verdict"], found["final"], found["exit"]), ("PASS", "UNVERIFIED", 1), "(D) its numbers deleted")
    write_results(rig, {**original, "ledger": 99})
    found = M.regrade_dir(rig.out, rig.ledger)
    eq((found["final"], (found["entry"] or {}).get("id"), found["numbers"].split(":")[0]), ("PASS", 1, "VERIFIED"),
       f"(E) a renumbered id: {found['numbers']}")
    write_results(rig, original)


def case_grade_dir_error_states(M, tmp):
    """(C4-E06, the check's G1) grade DIR knows an ERROR batch from its LEDGER ENTRY, read NOW, as well as from
    results.error.json: (a) a batch whose ERROR was written to the ledger exits 4 with results.error.json removed; (b) a
    batch whose ledger could not be written (entry 'started') exits 4, says the entry is NOT finished, and exits 4 with
    results.error.json removed (an entry still 'started' has no verdict); after finish-entry its line says the entry IS
    finished (read now, not the stale ledger_finished); (c) with no ledger given, results.error.json alone exits 4. (The
    sixth check's C6-04) in (a) with results.error.json beside its ERROR entry, in (b) beside its 'started' entry and
    after finish-entry, no contradiction is said (`no_contradiction`)."""
    rig = graded_rig(M, tmp / "error")
    real = ledger.finish
    with mock.patch.object(ledger, "finish", lambda i, v, e, path=ledger.LEDGER: (
            real(i, v, e, path=path) if "ERROR (harness:" in v else (_ for _ in ()).throw(OSError("held")))):
        guarded_run(rig)
    ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness:"), rig.entry()["verdict"][:200])
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 4 and "this batch ended in ERROR" in text, f"(a) the entry's ERROR, with the file: {text[-500:]}")
    no_contradiction(M, rig.out, rig.ledger, text, "(a) the entry's ERROR beside results.error.json")
    (rig.out / M.RESULTS_ERROR).unlink()
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 4 and "this batch ended in ERROR" in text, f"(a) the entry's ERROR, without the file: {text[-500:]}")
    rig = graded_rig(M, tmp / "unwritten")
    with mock.patch.object(ledger, "finish", side_effect=PermissionError(13, "held open by another program")):
        guarded_run(rig)
    eq(rig.entry()["status"], "started", "the ledger could not be written")
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 4 and "NOT finished (it is 'started')" in text, f"(b) {text[-500:]}")
    no_contradiction(M, rig.out, rig.ledger, text, "(b) the entry 'started' beside results.error.json")
    record = rig.out / M.RESULTS_ERROR
    saved = record.read_bytes()
    record.unlink()
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 4 and "is still 'started': no verdict was ever written" in text, f"(b) without the file: {text[-500:]}")
    record.write_bytes(saved)
    eq(M.regrade_dir(rig.out, None)["final"], "ERROR", "(c) with no ledger, results.error.json alone")
    with contextlib.redirect_stdout(io.StringIO()):
        eq(M.main(["finish-entry", str(rig.out), "--ledger", str(rig.ledger)]), 0, "finish-entry")
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 4 and "its ledger entry is finished (read now)" in text, f"(b) read NOW after finish-entry: {text[-500:]}")
    no_contradiction(M, rig.out, rig.ledger, text, "(b) after finish-entry")


def no_contradiction(M, out: Path, ledger_path, text: str, label: str) -> None:
    """(The sixth check's C6-04, its mutant MZ1) an HONEST ERROR, ABORTED or STARTED batch is never said to contradict
    its ledger entry: not in grade DIR's output, not in regrade_dir's "contradiction"."""
    ok("CONTRADICTS" not in text, f"{label}: a contradiction said: {text[-600:]}")
    eq(M.regrade_dir(out, ledger_path)["contradiction"], "", f"{label}: regrade_dir's contradiction")


def case_grade_dir_planted_stop_and_deleted_leg(M, tmp):
    """(C4-G02, the check's S and T) a stop file or a missing leg never turns a FAIL into PASS: (a) an impure L5 rewritten as
    NOT RUN with a STOP.txt planted beside a frozen record that says the tree held: LC.FROZEN FAILS (the STOP.txt explains
    the leg, but the batch writes one only when the tree moved); (b) the impure L5 DELETED from the row's legs: LC.CUSTODY
    FAILS (the row's legs are not the registered legs). grade DIR on an honest PASS folder: a planted ABORT.txt beside
    its entry FINISHED with PASS contradicts it (the fifth check's C5-03: said, exit 1, never 0 or 3) and, with no ledger
    given, is the folder's own ABORTED mark (final ABORTED); a planted STOP.txt FAILS LC.FROZEN (exit 1), a clean L5
    deleted from its row file FAILS (exit 1). CONTROLS: the honest batch passes; in place, the folder exits 0."""
    chains, jobs = healthy_batch()
    eq(M.batch_verdict(grade(M, copy.deepcopy(chains), jobs)), "PASS", "CONTROL")
    legs = LC.legs_of("ch5_rival_meet", real_milestones())
    leg = chains[0]["legs"][4]
    next(c for c in leg["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
    rows = copy.deepcopy(chains)
    rows[0]["legs"][4] = M.not_run_row({**jobs[0]}, leg, "NOT RUN", "the chain stopped at L4: planted")
    checks = M.grade_batch(rows, jobs, 5, 5, (True, "ok"), [], {"most_running": 3}, legs=legs, stop_files=["STOP.txt"])
    eq((M.batch_verdict(checks), by_id(checks, "LC.FROZEN").status, by_id(checks, "LC.CUSTODY").status),
       ("FAIL", "FAIL", "PASS"), "(a) a planted STOP.txt beside a frozen record that held fails LC.FROZEN")
    rows = copy.deepcopy(chains)
    del rows[0]["legs"][4]
    checks = M.grade_batch(rows, jobs, 5, 5, (True, "ok"), [], {"most_running": 3}, legs=legs)
    custody = by_id(checks, "LC.CUSTODY")
    eq((M.batch_verdict(checks), custody.status), ("FAIL", "FAIL"), f"(b) a deleted leg: {graded_ok(checks)}")
    ok("are not the registered legs" in custody.text, custody.text[:700])
    rig = graded_rig(M, tmp / "dir")
    guarded_run(rig)
    eq(grade_dir_out(M, rig.out, rig.ledger)[0], 0, "CONTROL: the honest folder in place")
    (rig.out / "ABORT.txt").write_text("", encoding="utf-8")
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "THE FOLDER CONTRADICTS ITS LEDGER ENTRY" in text and "this batch was ABORTED" not in text,
       f"a planted ABORT.txt beside a finished PASS: {text[-400:]}")
    eq(M.regrade_dir(rig.out, None)["final"], "ABORTED", "with no ledger, a planted ABORT.txt is the folder's own mark")
    (rig.out / "ABORT.txt").unlink()
    (rig.out / "STOP.txt").write_text("", encoding="utf-8")
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "[FAIL] LC.FROZEN" in text, f"a planted STOP.txt: {text[-400:]}")
    (rig.out / "STOP.txt").unlink()
    path = rig.out / "rows" / f"{LC.jobs_of(6201, 6)[0]['chain']}.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    del row["legs"][4]
    path.write_text(json.dumps(row), encoding="utf-8")
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "[FAIL] LC.CUSTODY" in text, f"a deleted leg: {text[-400:]}")


def case_grade_dir_aborted_and_development(M, tmp):
    """(C4-G03, the check's A; its mutants C06, C08) grade DIR on an honest ABORTED graded batch (in-run exit 3) says
    ABORTED and exits 3, never PASS; its rows' re-grade is the in-run one (LC.CUSTODY PASS: ABORT.txt explains the legs
    it stopped); with ABORT.txt removed and results.json saying PASS, the ledger entry still says ABORTED (exit 3). A
    development batch re-grades labelled DEVELOPMENT, not graded (exit 0 for its PASS); a development batch that ended in
    ERROR exits 4. (The sixth check's C6-04) the honest ABORTED batch and the development ERROR batch are said to
    contradict nothing (`no_contradiction`)."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "aborted", plans={jobs[5]["chain"]: {"L4": {"write_abort": True}}})
    code, text = guarded_run(rig)
    eq((code, rig.results()["verdict"]), (3, "ABORTED (harness: disk)"), f"in-run: {text[-400:]}")
    in_run = {c["id"]: c["status"] for c in rig.results()["checks"]}
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 3 and "this batch was ABORTED by the harness" in text and "GRADE DIR VERDICT: GRADED: ABORTED" in text,
       f"grade DIR: {text[-500:]}")
    no_contradiction(M, rig.out, rig.ledger, text, "an honest ABORTED batch (ABORT.txt, its entry ABORTED)")
    regraded = {c.id: c.status for c in M.regrade_dir(rig.out, rig.ledger)["checks"]}
    eq((in_run["LC.CUSTODY"], regraded["LC.CUSTODY"]), ("PASS", "PASS"),
       "the re-grade's custody is the in-run one: ABORT.txt explains the legs it stopped")
    (rig.out / "ABORT.txt").unlink()
    write_results(rig, {**results_of(rig), "verdict": "PASS"})
    eq(grade_dir_out(M, rig.out, rig.ledger)[0], 3, "the ledger entry still says ABORTED")
    dev, args = dev_rig(M, tmp / "dev")
    eq(guarded_run(dev, args)[0], 0, "a development batch ran")
    code, text = grade_dir_out(M, dev.out, dev.ledger)
    ok(code == 0 and "GRADE DIR VERDICT: DEVELOPMENT, not graded: PASS" in text, f"labelled development: {text[-400:]}")
    dev, args = dev_rig(M, tmp / "dev_error")
    with mock.patch.object(M, "grade_batch", side_effect=RuntimeError("a planted fault")):
        eq(guarded_run(dev, args)[0], 4, "a development batch that ended in ERROR")
    code, text = grade_dir_out(M, dev.out, dev.ledger)
    ok(code == 4 and "GRADE DIR VERDICT: DEVELOPMENT, not graded: ERROR" in text, f"{text[-400:]}")
    no_contradiction(M, dev.out, dev.ledger, text, "an honest development ERROR batch")


def case_salvage_exemption_needs_record(M, tmp):
    """(C4-G04, the check's V) the salvage reason explains a NOT RUN leg after a continuing leg only for a chain the
    orchestrator's OWN events say it salvaged. CONTROL: an honest salvage (a chain process that dies after naming L3 and
    before its launch): L3-L5 NOT RUN with the salvage reason, the event recorded, LC.CUSTODY PASS, the batch PASSES (5 of
    6), and grade DIR agrees. FAULT: a hidden impure L5 whose stored reason reads like a salvage, rewritten in-run through
    the tamper hook with no salvage recorded: LC.CUSTODY FAILS, in-run and in grade DIR."""
    run_jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "honest", plans={run_jobs[0]["chain"]: {"L3": {"die_before_launch": True}}})
    code, text = guarded_run(rig)
    row = json.loads((rig.out / "rows" / f"{run_jobs[0]['chain']}.json").read_text(encoding="utf-8"))
    eq([leg["status"] for leg in row["legs"]], ["RAN", "RAN", "NOT RUN", "NOT RUN", "NOT RUN"], "salvaged before L3")
    ok(row["legs"][2]["reason"].startswith(M.SALVAGE_REASON), row["legs"][2]["reason"])
    ok(any(str(e).startswith(f"{run_jobs[0]['chain']}{M.SALVAGE_EVENT}") for e in rig.results()["events"]),
       rig.results()["events"])
    statuses = {c["id"]: c["status"] for c in rig.results()["checks"]}
    eq((code, statuses["LC.CUSTODY"]), (0, "PASS"), f"CONTROL: an honest, recorded salvage: {text[-600:]}")
    eq(M.regrade_dir(rig.out, rig.ledger)["final"], "PASS", "CONTROL: grade DIR reads the same events")

    def hide() -> list[str]:
        path = attack.out / "rows" / f"{run_jobs[0]['chain']}.json"
        found = json.loads(path.read_text(encoding="utf-8"))
        last = found["legs"][4]
        next(c for c in last["checks"] if c["id"] == "L5.PURITY_CLEAN")["status"] = "FAIL"
        found["legs"][4] = M.not_run_row({**run_jobs[0]}, last, "NOT RUN", "the chain's process ended (planted)")
        path.write_text(json.dumps(found), encoding="utf-8")
        return []
    attack = graded_rig(M, tmp / "attack", leftover=hide)
    code, text = guarded_run(attack)
    custody = {c["id"]: c["status"] for c in attack.results()["checks"]}["LC.CUSTODY"]
    eq((code, custody), (1, "FAIL"), f"FAULT: a salvage reason with no salvage recorded: {text[-500:]}")
    eq(M.regrade_dir(attack.out, attack.ledger)["final"], "FAIL", "FAULT: and grade DIR")


# ---------------------------------------------------------------------------------------------------- C4-H01..H08: R12
def case_closure_pyw_planted(M, tmp):
    """(C4-H01, the check's N3, N3b, N3d) a .pyw beside a NAMESPACE package of the framework runs in its place (a module
    FILE wins over a namespace folder): sandbox-pokebot/modules.pyw, plugins.pyw and modules/web.pyw are each named by
    R12, as closure files the registration does not hash, and the first two as top-level shadows of their folders (only
    the FOLDER is their home); a package whose only __init__ is a .pyw is followed into. CONTROL: the tree without the
    three is named by nothing."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "import modules.web.http\nimport modules.pw\nimport plugins.a_plugin\n")
    plant(root, "sandbox-pokebot/modules/web/http.py")
    plant(root, "sandbox-pokebot/modules/pw/__init__.pyw", "import modules.from_pyw\n")
    plant(root, "sandbox-pokebot/modules/from_pyw.py")
    plant(root, "sandbox-pokebot/plugins/a_plugin.py")
    planted = ("sandbox-pokebot/modules.pyw", "sandbox-pokebot/plugins.pyw", "sandbox-pokebot/modules/web.pyw")
    with mock.patch.object(M, "PATH_ROOTS", ()):
        control = M.grader_closure(root)
        ok({"sandbox-pokebot/modules/pw/__init__.pyw", "sandbox-pokebot/modules/from_pyw.py"} <= set(control),
           f"a package whose __init__ is a .pyw is followed into: {control}")
        with mock.patch.object(M, "GRADER_FILES", tuple(control)):
            eq(M.closure_missing(root)[0], [], "CONTROL: nothing is named")
            for rel in planted:
                plant(root, rel, "x = 1\n")
            found = M.closure_missing(root)[0]
    eq([rel for rel in planted if rel not in found], [], f"each .pyw is a closure file the registration does not hash: {found}")
    for rel in planted[:2]:
        ok(any(problem.startswith(f"{rel}: a module named like") for problem in found), f"{rel}: a top-level shadow: {found}")


def case_toplevel_installed_planted(M, tmp):
    """(C4-H03, the check's N7, N7b) a script-folder entry named like a module installed OUTSIDE the repository (one a
    closure library imports: pydantic's typing_extensions, ...) runs in its place and is named; so is a folder without
    __init__ beside an installed NAMESPACE package of that name (ruamel here: its portions merge, the script folder's
    first); `outside_modules` lists the standard library's and site-packages' top-level names when the scan runs;
    (C4-H02) a name differing only in case from the library's (a root Random.py, which PYTHONCASEOK would import) is
    named; a standard-library name this platform does not install (pwd on Windows, which getpass imports) is named by
    the standard library's list. CONTROL: none of them planted, and a namespace folder named like an installed REGULAR
    package (it never replaces one)."""
    installed = M.outside_modules(tmp / "repo")
    stdlib = {name.lower() for name in sys.stdlib_module_names}
    libraries = sorted(name for name, kind in installed.items()
                       if name not in stdlib and kind in ("module", "package") and not name.startswith("_"))
    ok(len(libraries) >= 3 and "json" in installed, f"the installed names are listed: {sorted(installed)[:20]}")
    first = "typing_extensions" if "typing_extensions" in libraries else libraries[0]
    second = "annotated_types" if "annotated_types" in libraries and first != "annotated_types" else \
        next(name for name in libraries if name != first)
    regular = "pydantic" if installed.get("pydantic") == "package" else \
        next(name for name in libraries if installed[name] == "package" and name not in (first, second))
    namespaces = sorted(name for name, kind in installed.items() if kind == "folder" and not name.startswith("_"))
    namespace = "ruamel" if "ruamel" in namespaces else namespaces[0]
    absent = sorted(name for name in stdlib if name not in installed and name.isidentifier() and not name.startswith("_"))
    missing = "pwd" if "pwd" in absent else absent[0]
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    plant(root, f"{regular}/readme.txt", "a namespace folder")
    eq(M.toplevel_problems(root, set()), [], f"CONTROL: nothing planted ({regular}/ is a namespace folder)")
    plant(root, f"sandbox-pokebot/{first}.py", "x = 1\n")
    plant(root, f"ai_player/gates/{second}.py", "x = 1\n")
    plant(root, "Random.py", "x = 1\n")
    plant(root, f"{namespace}/yaml.py", "x = 1\n")
    plant(root, f"{missing}.py", "x = 1\n")
    found = sorted(problem.split(":")[0] for problem in M.toplevel_problems(root, set()))
    eq(found, sorted(["Random.py", f"ai_player/gates/{second}.py", f"sandbox-pokebot/{first}.py", namespace,
                      f"{missing}.py"]), f"exactly the shadows: {found}")


def case_ai_problems_planted(M, tmp):
    """(C4-H04, C4-H06; the check's N4, N4b and probe_evidence) R12 names, in the AI's own package: a __pycache__ file
    CPython would load INSTEAD of one of the AI's .py files that holds other code (ai_player/__init__.py,
    host/launcher.py: the grader imports them before any check), a .pyc of the AI's outside __pycache__, and ANY Python
    code file under ai_player/evidence/ (.py, .pyw, .pyc, an extension module, in a subfolder too). CONTROLS: a genuine
    cache, a stale one, and the evidence folder's text, JSON and zip files."""
    import importlib._bootstrap_external as ext

    root = tmp / "repo"
    init = plant(root, "ai_player/__init__.py", "x = 1\n")
    launcher = plant(root, "ai_player/host/launcher.py", "y = 2\n")
    plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    for rel in ("ai_player/evidence/2026-11-06-x.txt", "ai_player/evidence/results.json", "ai_player/evidence/archive/a/b.zip"):
        plant(root, rel, "text")
    tag = sys.implementation.cache_tag

    def pyc(source: Path, text: str, shift: int = 0) -> bytes:
        st = source.stat()
        return bytes(ext._code_to_timestamp_pyc(compile(text, str(source), "exec", dont_inherit=True),
                                                int(st.st_mtime) + shift, st.st_size))
    caches = {init: root / "ai_player" / "__pycache__" / f"__init__.{tag}.pyc",
              launcher: root / "ai_player" / "host" / "__pycache__" / f"launcher.{tag}.pyc"}
    for path in caches.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    caches[init].write_bytes(pyc(init, "x = 1\n"))
    caches[launcher].write_bytes(pyc(launcher, "y = 3\n", -100))
    eq(M.ai_problems(root), [], "CONTROL: a genuine and a stale cache, the evidence's text, JSON and zip files")
    caches[init].write_bytes(pyc(init, "x = 2\n"))
    caches[launcher].write_bytes(pyc(launcher, "y = 3\n"))
    planted = ("ai_player/zz_probe.pyc", "ai_player/evidence/zz_brain.py", "ai_player/evidence/archive/x/m.pyw",
               "ai_player/evidence/c.pyc", "ai_player/evidence/e.cp312-win_amd64.pyd")
    for rel in planted:
        plant(root, rel, "x = 1\n")
    found = sorted(problem.split(":")[0] for problem in M.ai_problems(root))
    eq(found, sorted([*planted, f"ai_player/__pycache__/__init__.{tag}.pyc", f"ai_player/host/__pycache__/launcher.{tag}.pyc"]),
       f"exactly the plants: {found}")
    ok(any(problem.startswith(f"ai_player/__pycache__/__init__.{tag}.pyc:") for problem in M.closure_missing(root)[0]),
       "and R12 (closure_missing) has them")


def case_run_refusal_falls_through(M, tmp):
    """(C4-H05) R12's closure check RETURNS a refusal only when it has one: whatever closure_refusal returns for a list, the
    checks after it still run (R9 here). CONTROL: a closure entry is R12."""
    facts = facts_of(closure_missing=["sandbox-pokebot/plugins/zz.py"], git={"head": "a1", "origin": "b2", "dirty": []})
    ok((M.run_refusal(run_args(), facts) or "").startswith("R12"), "CONTROL: a closure entry is R12")
    with mock.patch.object(M, "closure_refusal", lambda missing: None):
        ok((M.run_refusal(run_args(), facts) or "").startswith("R9"), "a None from the closure check never skips R9")


def case_resolution_branches_planted(M, tmp):
    """(C4-H07: the check's R03, R04 survived) a package the closure follows whose ONLY __init__ is bytecode (with no
    source anywhere, it would run unhashed), and an extension module beside a closure module whose stem differs in CASE
    (mixed.cp312-win_amd64.pyd beside Mixed.py: CPython's finder compares without case on Windows) are each named.
    CONTROL: the tree without them."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "import modules.Mixed\nimport modules.pkgz\n")
    plant(root, "sandbox-pokebot/modules/Mixed.py")
    (root / "sandbox-pokebot" / "modules" / "pkgz").mkdir(parents=True)
    with mock.patch.object(M, "PATH_ROOTS", ()):
        eq(M.resolution_problems(root, M.closure_scan(root)["modules"]), [], "CONTROL")
        plant(root, "sandbox-pokebot/modules/pkgz/__init__.pyc")
        plant(root, "sandbox-pokebot/modules/mixed.cp312-win_amd64.pyd")
        found = M.resolution_problems(root, M.closure_scan(root)["modules"])
    for rel in ("sandbox-pokebot/modules/pkgz/__init__.pyc:", "sandbox-pokebot/modules/mixed.cp312-win_amd64.pyd:"):
        ok(any(problem.startswith(rel) for problem in found), f"{rel} named: {found}")


def case_pycache_branches_planted(M, tmp):
    """(C4-H07: the check's R06, R07 survived) a forged cache whose NAME differs in case (Live_Chain.<tag>.pyc: CPython
    loads it on Windows, the check's N10) is named; a GENUINE optimized cache (.opt-1.pyc of a source holding an assert)
    is not, because it is compared with the source compiled at ITS optimization level. CONTROL: pycache_planted."""
    import importlib._bootstrap_external as ext

    root = tmp / "repo"
    source = plant(root, "ai_player/gates/live_chain.py", "assert True\nx = 1\n")
    cache = root / "ai_player" / "gates" / "__pycache__"
    cache.mkdir()
    st, tag = source.stat(), sys.implementation.cache_tag

    def pyc(text: str, optimize: int = 0) -> bytes:
        return bytes(ext._code_to_timestamp_pyc(compile(text, str(source), "exec", dont_inherit=True, optimize=optimize),
                                                int(st.st_mtime), st.st_size))
    (cache / f"live_chain.{tag}.opt-1.pyc").write_bytes(pyc("assert True\nx = 1\n", optimize=1))
    eq(M.pycache_problems(root, [source]), [], "CONTROL: a genuine optimized cache")
    (cache / f"Live_Chain.{tag}.pyc").write_bytes(pyc("x = 2\n"))
    found = M.pycache_problems(root, [source])
    ok(len(found) == 1 and found[0].startswith(f"ai_player/gates/__pycache__/Live_Chain.{tag}.pyc:"), found)


def case_toplevel_branches_planted(M, tmp):
    """(C4-H07: the check's T03, T04, T06, T07, T08, T10 survived; C4-H01's exact homes) each entry Python imports INSTEAD
    of a module is named: a .pyw and a sourceless .pyc named like the library (gates/argparse.pyw, a root json.pyc), a
    PACKAGE named like the library in gates (gates/json/, the check's S06), a private library name (gates/_hashlib.py,
    S07), the framework's names OUTSIDE their exact home (a root modules.py, S08; a root profiles.py, S10;
    sandbox-pokebot/mgba.py, a file and not the exempt folder; sandbox-pokebot/modules.pyw beside its home folder; a
    sandbox-pokebot/pokebot package beside its home file). CONTROL: the homes and the exempt folders themselves."""
    root = tmp / "repo"
    for rel in ("ai_player/__init__.py", "sandbox-pokebot/modules/x.py", "sandbox-pokebot/plugins/p.py",
                "sandbox-pokebot/pokebot.py", "sandbox-pokebot/requirements.py", "sandbox-pokebot/updater.py",
                "sandbox-pokebot/mgba/__init__.py", "sandbox-pokebot/profiles/x.yml", "ai_player/gates/live_chain.py"):
        plant(root, rel)
    tops = {"modules", "plugins", "pokebot", "requirements", "updater", "mgba", "profiles", "ai_player", "argparse", "json"}
    eq(M.toplevel_problems(root, tops), [], "CONTROL: the homes and the exempt folders")
    planted = ["ai_player/gates/argparse.pyw", "json.pyc", "ai_player/gates/json/__init__.py", "ai_player/gates/_hashlib.py",
               "modules.py", "profiles.py", "sandbox-pokebot/mgba.py", "sandbox-pokebot/modules.pyw",
               "sandbox-pokebot/pokebot/__init__.py"]
    for rel in planted:
        plant(root, rel)
    found = sorted(problem.split(":")[0] for problem in M.toplevel_problems(root, tops))
    eq(found, sorted(["ai_player/gates/argparse.pyw", "json.pyc", "ai_player/gates/json", "ai_player/gates/_hashlib.py",
                      "modules.py", "profiles.py", "sandbox-pokebot/mgba.py", "sandbox-pokebot/modules.pyw",
                      "sandbox-pokebot/pokebot"]), f"exactly the plants: {found}")


def case_ai_starts_branches_planted(M, tmp):
    """(C4-H07: the check's A02, A03 survived) the AI's `from modules import zz_from` (the imported NAME is the module) and
    an absolute import in one of the AI's .pyw files each START the closure. CONTROL: without them neither is in it."""
    root = tmp / "repo"
    plant(root, "ai_player/gates/live_chain.py", "x = 1\n")
    for name in ("__init__", "zz_from", "zz_pyw"):
        plant(root, f"sandbox-pokebot/modules/{name}.py")
    with mock.patch.object(M, "PATH_ROOTS", ()):
        eq([rel for rel in M.grader_closure(root) if "zz_" in rel], [], "CONTROL")
        plant(root, "ai_player/host/eyes.py", "from modules import zz_from\n")
        plant(root, "ai_player/host/door.pyw", "import modules.zz_pyw\n")
        found = M.grader_closure(root)
    ok("sandbox-pokebot/modules/zz_from.py" in found and "sandbox-pokebot/modules/zz_pyw.py" in found, found)


# ---------------------------------------------------------------------------------------------------- the fifth check: C5-01
def case_grade_dir_edited_fail_folder(M, tmp):
    """(The fifth check's C5-01, its DR) grade DIR never exits 0 for an EDITED graded FAIL folder (two L5 misses; the
    ledger says 'GRADED, FAIL'): (1) the check's own ATTACK, four edits to results.json (its numbers deleted, its seeds
    moved to 9001-9006, which no entry names, reach_min 0, its purpose relabelled 'development'): MISMATCH by its own jobs
    and by the entry its recorded id names, exit 1 (it exited 0); (the sixth check's C6-01) its entry is found by the
    seeds its jobs bind, so the verdict is the ledger's GRADED: FAIL; (2) the same with the recorded ledger id removed too:
    the folder's own jobs (LC-*-6201..6206) are not one per seed of 9001-9006, MISMATCH, exit 1; (3) its seeds and numbers
    kept, only the purpose relabelled: the entry its recorded id names (its own) is graded: MISMATCH, and on an honest
    PASS folder relabelled the same way, exit 1, never 0. (The sixth check's C6-01, its SEEDSTR) (4) five edits: the
    seeds written as STRINGS ["6201", "6206"], the recorded id one no entry has, the numbers deleted, the purpose
    'development', reach_min 0: MISMATCH (not two int seeds), the entry found by the jobs' int seeds, GRADED: FAIL, exit 1
    (it exited 0); (5) the same with the numbers KEPT (their seeds strings too, reach_min 0, numbers_sha256 recomputed):
    MISMATCH, GRADED: FAIL, exit 1 (it exited 0); (6) the honest PASS folder's results.json seeds written as FLOATS
    [6201.0, 6206.0] beside int numbers: MISMATCH (never equal by value only), exit 1. CONTROLS: both folders as written
    (exit 1, exit 0); (4)'s edits with INT seeds: no MISMATCH from the seeds, the ledger's GRADED: FAIL, exit 1; an honest
    DEVELOPMENT folder with its numbers deleted (its jobs are its seeds'), graded against its ledger and against one with
    no entry for it (as the real R2 is), still exits 0, labelled development."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "fail", plans={jobs[0]["chain"]: {"L5": {"miss": True}}, jobs[3]["chain"]: {"L5": {"miss": True}}})
    guarded_run(rig)
    original = results_of(rig)
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "GRADE DIR VERDICT: GRADED: FAIL" in text and "MISMATCH" not in text,
       f"CONTROL: the FAIL folder as written: {text[-300:]}")
    attack = {key: value for key, value in original.items() if key != "numbers"}
    attack.update(seeds=[9001, 9006], reach_min=0, purpose="development")
    write_results(rig, attack)
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "NUMBERS: MISMATCH" in text and "jobs ['LC-S-6201'" in text and "not one per seed of 9001-9006" in text
       and "names ledger entry #1, whose purpose is 'graded', not the folder's 'development'" in text
       and "LEDGER (read now): entry #1, graded" in text and "GRADE DIR VERDICT: GRADED: FAIL; exit 1" in text,
       f"(1) the check's ATTACK: {text[-1200:]}")
    write_results(rig, {key: value for key, value in attack.items() if key != "ledger"})
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "NUMBERS: MISMATCH (no numbers)" in text and "not one per seed of 9001-9006" in text,
       f"(2) and the recorded id removed: {text[-900:]}")
    write_results(rig, {**original, "purpose": "development"})
    found = M.regrade_dir(rig.out, rig.ledger)
    ok(found["numbers"].startswith("MISMATCH") and "whose purpose is 'graded', not the folder's 'development'" in
       found["numbers"] and found["exit"] == 1, f"(3) the purpose relabelled: {found['numbers']}")
    # (the sixth check's C6-01, its SEEDSTR) the seeds written as strings, the recorded id one no entry has
    edits = {"ledger": 99999, "purpose": "development", "reach_min": 0}  # (MISMATCH re-grades FAIL: no suffix then)
    met = "LEDGER (read now): entry #1 (results.json names #99999"  # its own entry, found by the seeds its jobs bind
    no_numbers = {key: value for key, value in original.items() if key != "numbers"}
    write_results(rig, {**no_numbers, **edits, "seeds": [6201, 6206]})
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "MISMATCH" not in text and met in text and "GRADE DIR VERDICT: GRADED: FAIL" in text,
       f"CONTROL: (4)'s edits with int seeds: {text[-700:]}")
    write_results(rig, {**no_numbers, **edits, "seeds": ["6201", "6206"]})
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "NUMBERS: MISMATCH (no numbers)" in text and "own seeds ['6201', '6206'] are not two int seeds" in text
       and met in text and "GRADE DIR VERDICT: GRADED: FAIL; exit 1" in text,
       f"(4) SEEDSTR, the numbers deleted: {text[-900:]}")
    numbers_of = {**original["numbers"], "seeds": ["6201", "6206"], "reach_min": 0}
    write_results(rig, {**original, **edits, "numbers": numbers_of, "numbers_sha256": ledger.numbers_sha256(numbers_of),
                        "seeds": ["6201", "6206"]})
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "NUMBERS: MISMATCH" in text and "the numbers' seeds ['6201', '6206'] are not two int seeds" in text
       and met in text and "GRADE DIR VERDICT: GRADED: FAIL; exit 1" in text, f"(5) SEEDSTR, the numbers kept: {text[-900:]}")
    eq(rig.entry()["verdict"][:len("GRADED, FAIL")], "GRADED, FAIL", "the ledger still says FAIL")
    rig = graded_rig(M, tmp / "pass")
    guarded_run(rig)
    original = results_of(rig)
    eq(grade_dir_out(M, rig.out, rig.ledger)[0], 0, "CONTROL: the PASS folder as written")
    write_results(rig, {**original, "purpose": "development"})
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "GRADE DIR VERDICT: GRADED: FAIL" in text and "whose purpose is 'graded'" in text,
       f"(3) a PASS folder relabelled development: {text[-600:]}")
    write_results(rig, {**original, "seeds": [6201.0, 6206.0]})
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "NUMBERS: MISMATCH" in text
       and "the batch's seeds [6201.0, 6206.0] are not two int seeds equal to the numbers' [6201, 6206]" in text,
       f"(6) the PASS folder's seeds written as floats: {text[-700:]}")
    write_results(rig, original)
    dev, args = dev_rig(M, tmp / "dev")
    eq(guarded_run(dev, args)[0], 0, "a development batch ran")
    write_results(dev, {key: value for key, value in results_of(dev).items() if key != "numbers"})
    code, text = grade_dir_out(M, dev.out, dev.ledger)
    ok(code == 0 and "GRADE DIR VERDICT: DEVELOPMENT, not graded: PASS" in text and "MISMATCH" not in text,
       f"CONTROL: a development folder with no numbers: {text[-500:]}")
    empty = tmp / "empty_ledger.json"
    empty.write_text(json.dumps({"what": "t", "entries": []}), encoding="utf-8")
    code, text = grade_dir_out(M, dev.out, empty)
    ok(code == 0 and "DEVELOPMENT, not graded (unconfirmed: no ledger entry): PASS" in text,
       f"CONTROL: and with no entry for it: {text[-500:]}")


def case_recorded_entry_rules(M, tmp):
    """(C5-01) `recorded_problems`, rule by rule, on a planted ledger (#1 the folder's own graded entry, #2 an entry of
    another driver as the real R0's recorded #86 is after the merge, its seeds meeting the folder's, #3 another
    live_chain batch whose seeds MEET the folder's, as only a merged ledger holds; (the sixth check's C6-02) #4 another
    live_chain batch whose seeds never meet the folder's, as the next registration is to R2's recorded #100; #5-#8 its
    neighbours: 6195-6201 and 6206-6210 touch the folder's 6201-6206 at one seed, 6195-6200 and 6207-6210 do not).
    FAULTS: the recorded id names a live_chain entry whose seeds meet the folder's and differ (only the seeds are named:
    #1 for a folder of 6201-6203; #5 and #6, each touching at one seed); the folder's own entry with another purpose (only
    the purpose); another batch's id (#3) while the folder's seeds' entry was met WITHOUT its bounds sha256. CONTROLS (no
    problem): its own entry; an id of no entry; an entry of another driver; another batch's id explained by the folder's
    entry met by its seeds AND bounds sha256 under another id (a renumbered ledger); (C6-02) a live_chain entry whose
    seeds never meet the folder's (#4, #7, #8, and #1 for a folder of 9001-9006), with or without the folder's own entry;
    no ledger given."""
    path = tmp / "ledger.json"
    own = {"id": 1, "driver": M.DRIVER, "first": 6201, "last": 6206, "purpose": "graded", "status": "done",
           "bounds_sha256": "a" * 64, "verdict": "GRADED, FAIL (failing: LC.REACH): planted"}

    def other(entry_id: int, first: int, last: int) -> dict:
        return {"id": entry_id, "driver": M.DRIVER, "first": first, "last": last, "purpose": "graded", "status": "done",
                "bounds_sha256": "b" * 64}
    path.write_text(json.dumps({"what": "t", "entries": [
        own, {"id": 2, "driver": "ch5stops_smoke", "first": 6001, "last": 6001, "purpose": "development", "status": "done"},
        other(3, 6204, 6209), {**other(4, 7001, 7006), "status": "registered"}, other(5, 6195, 6201), other(6, 6206, 6210),
        other(7, 6195, 6200), other(8, 6207, 6210)]}), encoding="utf-8")

    def problems(entry_id, seeds, purpose, entry=None, sha="a" * 64, ledger_path=path) -> list[str]:
        return M.recorded_problems(ledger_path, {"ledger": entry_id, "seeds": seeds, "purpose": purpose}, seeds, sha, entry)
    eq(problems(1, [6201, 6206], "graded", own), [], "CONTROL: its own entry")
    found = problems(1, [6201, 6206], "development", own)
    ok(len(found) == 1 and "whose purpose is 'graded', not the folder's 'development'" in found[0], found)
    found = problems(1, [6201, 6203], "graded")
    ok(len(found) == 1 and "for seeds [6201, 6206], not the folder's [6201, 6203]" in found[0], found)
    eq(problems(99, [9001, 9006], "graded"), [], "CONTROL: an id of no entry")
    eq(problems(2, [6001, 6003], "development"), [], "CONTROL: an entry of another driver (a renumbered ledger)")
    eq(problems(3, [6201, 6206], "graded", own), [], "CONTROL: the folder's entry met by its seeds and bounds sha256")
    found = problems(3, [6201, 6206], "graded", own, sha="c" * 64)
    ok(len(found) == 1 and "#3, a live_chain entry for seeds [6204, 6209]" in found[0], f"no sha256 to explain it: {found}")
    eq(problems(1, [6201, 6206], "development", ledger_path=None), [], "CONTROL: no ledger given")
    # (the sixth check's C6-02) another live_chain batch's entry: its seeds never meet the folder's
    eq(problems(1, [9001, 9006], "development"), [], "CONTROL: #1's seeds never meet the folder's 9001-9006")
    eq(problems(4, [6201, 6206], "development"), [], "CONTROL: #4 (7001-7006), the folder's own entry absent")
    eq(problems(4, [6201, 6206], "graded", own, sha="c" * 64), [], "CONTROL: #4, the folder's entry met without its sha256")
    for entry_id, span in ((7, [6195, 6200]), (8, [6207, 6210])):
        eq(problems(entry_id, [6201, 6206], "graded"), [], f"CONTROL: #{entry_id} ({span}) never meets 6201-6206")
    for entry_id, span in ((5, [6195, 6201]), (6, [6206, 6210])):
        found = problems(entry_id, [6201, 6206], "graded")
        ok(len(found) == 1 and f"#{entry_id}, a live_chain entry for seeds {span}, not the folder's [6201, 6206]" in found[0],
           f"#{entry_id} touches the folder's seeds at one seed: {found}")


# ---------------------------------------------------------------------------------------------------- C5-02
def case_finish_entry_without_error_record(M, tmp):
    """(The fifth check's C5-02, its probe5c: a regression of the C4-E05 fix) the ledger AND results.error.json cannot be
    written (a full disk fails the larger file first): exit 4, the entry 'started', ledger.unfinished.json written and no
    results.error.json; the command the guard PRINTED, run as printed with the ledger writable again, FINISHES the entry
    with this driver's ERROR verdict, rebuilt from the copy of the ERROR record that ledger.unfinished.json carries.
    FAULTS (each REFUSED, exit 2, the ledger untouched): that copy edited to a PASS (in both lines), to other numbers, or
    removed. CONTROL: ledger_unwritable_not_finished (results.error.json written, the same command)."""
    rig = graded_rig(M, tmp)
    real = M._write_json

    def full_disk(path, data):
        if Path(path).name == M.RESULTS_ERROR:
            raise OSError(28, "No space left on device")
        return real(path, data)
    with mock.patch.object(ledger, "finish", side_effect=PermissionError(13, "held open by another program")), \
            mock.patch.object(M, "_write_json", full_disk):
        code, text = guarded_run(rig)
    eq((code, rig.entry()["status"]), (4, "started"), f"neither could be written: {text[-600:]}")
    eq(((rig.out / M.UNFINISHED).is_file(), (rig.out / M.RESULTS_ERROR).exists()), (True, False), "only the unfinished file")
    printed = re.search(r'Finish it by hand, from the repository: py -3\.12 ai_player/gates/live_chain\.py finish-entry '
                        r'"([^"]+)"(?: --ledger "([^"]+)")?', text)
    ok(printed is not None and printed.group(2), f"the guard printed the command: {text[-900:]}")
    argv = ["finish-entry", printed.group(1), "--ledger", printed.group(2)]
    path = rig.out / M.UNFINISHED
    data = json.loads(path.read_text(encoding="utf-8"))
    ok(isinstance(data.get("error_record"), dict), f"{M.UNFINISHED} carries a copy of the ERROR record: {sorted(data)}")
    copy_of = data["error_record"]
    passing = M.error_line("GRADED", True, "PASS", copy_of["to"], copy_of["seeds"], copy_of["numbers_sha256"])
    for label, edited in (("a PASS in the copy", {**data, "verdict": passing, "error_record": {**copy_of, "verdict": "PASS"}}),
                          ("other numbers", {**data, "error_record": {**copy_of, "numbers_sha256": "0" * 64}}),
                          ("the copy removed", {k: v for k, v in data.items() if k != "error_record"})):
        path.write_text(json.dumps(edited), encoding="utf-8")
        before = rig.ledger.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            code = M.main(argv)
        eq((code, rig.ledger.read_bytes() == before), (2, True), f"{label}: REFUSED: {buffer.getvalue()[-400:]}")
    path.write_text(json.dumps(data), encoding="utf-8")
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        code = M.main(argv)
    eq((code, rig.entry()["status"]), (0, "done"), f"the printed command finishes it: {buffer.getvalue()[-500:]}")
    ok(rig.entry()["verdict"].startswith("GRADED, ERROR (harness: LedgerUnwritten:"), rig.entry()["verdict"][:200])


# ---------------------------------------------------------------------------------------------------- C5-03
def case_grade_dir_contradiction(M, tmp):
    """(The fifth check's C5-03, its AB) a folder ERROR or ABORTED mark beside an entry FINISHED with PASS or FAIL is a
    CONTRADICTION (in a run they never meet): grade DIR says the folder contradicts its ledger entry and grades FAIL, exit
    1, never ABORTED (3) or ERROR (4): on a FAIL batch, an ABORT.txt planted, a results.error.json planted, results.json's
    verdict edited to ABORTED; on a PASS batch, an ABORT.txt planted (exit 1, never 0 or 3). CONTROLS: the FAIL batch as
    written (no contradiction said); an honest ABORTED and an honest ERROR batch, whose entries say so, are no
    contradiction (grade_dir_aborted_and_development, grade_dir_error_states: `no_contradiction`). (The sixth check's
    C6-04, its mutant MZ3) the verdict line says why: 'GRADED: FAIL (the folder contradicts its finished ledger entry)'."""
    jobs = LC.jobs_of(6201, 6)
    rig = graded_rig(M, tmp / "fail", plans={jobs[0]["chain"]: {"L5": {"miss": True}}, jobs[3]["chain"]: {"L5": {"miss": True}}})
    guarded_run(rig)
    original = results_of(rig)
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 1 and "CONTRADICTS" not in text, f"CONTROL: {text[-300:]}")

    def contradicted(label: str, out: Path, ledger_path: Path) -> None:
        code, text = grade_dir_out(M, out, ledger_path)
        ok(code == 1 and "THE FOLDER CONTRADICTS ITS LEDGER ENTRY" in text and "GRADED: FAIL" in text
           and "this batch was ABORTED" not in text and "this batch ended in ERROR" not in text, f"{label}: {text[-700:]}")
        ok("GRADE DIR VERDICT: GRADED: FAIL (the folder contradicts its finished ledger entry)" in text,
           f"{label}: the verdict line says why: {text[-300:]}")
    (rig.out / M.ABORT_FILE).write_text("", encoding="utf-8")
    contradicted("FAIL + ABORT.txt", rig.out, rig.ledger)
    (rig.out / M.ABORT_FILE).unlink()
    (rig.out / M.RESULTS_ERROR).write_text(json.dumps({
        **original, "verdict": "ERROR (harness: OSError: planted while grading; no PASS or FAIL; the seeds are spent)",
        "stage": "grading", "ledger_finished": True}), encoding="utf-8")
    contradicted("FAIL + results.error.json", rig.out, rig.ledger)
    (rig.out / M.RESULTS_ERROR).unlink()
    write_results(rig, {**original, "verdict": "ABORTED (harness: disk)"})
    contradicted("FAIL + results.json's verdict ABORTED", rig.out, rig.ledger)
    rig = graded_rig(M, tmp / "pass")
    guarded_run(rig)
    (rig.out / M.ABORT_FILE).write_text("", encoding="utf-8")
    contradicted("PASS + ABORT.txt", rig.out, rig.ledger)
    found = M.regrade_dir(rig.out, rig.ledger)
    eq((found["verdict"], found["final"], found["entry_word"]), ("PASS", "FAIL", "PASS"), "the rows and the entry PASS")


# ---------------------------------------------------------------------------------------------------- C5-04
def case_guard_sigint_restored(M, tmp):
    """(The fifth check's C5-04: M280 survived the full runner only by test order) with a FRESH sentinel SIGINT handler
    installed first, a guard that RETURNS (an exception while grading: exit 4) and a guard that RE-RAISES (a Ctrl+C while
    grading) each finish the entry with SIGINT IGNORED (SIG_IGN) while they run, and leave the SENTINEL installed after.
    The handler found at the start is restored in finally."""
    import signal
    original = signal.getsignal(signal.SIGINT)

    def sentinel(signum, frame):  # a handler no other code installs
        raise KeyboardInterrupt()
    try:
        for label, error in (("returns", RuntimeError("a planted fault in grading")), ("reraises", KeyboardInterrupt())):
            signal.signal(signal.SIGINT, sentinel)
            rig = graded_rig(M, tmp / label)
            during: list = []
            real_stop = M.stop_children

            def stop(handles, interrupts=None, real_stop=real_stop):
                during.append(signal.getsignal(signal.SIGINT))
                return real_stop(handles, interrupts)
            with mock.patch.object(M, "grade_batch", side_effect=error), mock.patch.object(M, "stop_children", stop):
                result, text = run_capturing(rig)
            ok(result == 4 if label == "returns" else isinstance(result, KeyboardInterrupt), f"({label}) {result!r}")
            eq(rig.entry()["status"], "done", f"({label}) the entry is finished: {text[-400:]}")
            eq(during, [signal.SIG_IGN], f"({label}) SIGINT was IGNORED while the guard ran")
            after = signal.getsignal(signal.SIGINT)
            ok(after is sentinel, f"({label}) the sentinel handler is restored after the guard: {after!r}")
    finally:
        signal.signal(signal.SIGINT, original)


# ---------------------------------------------------------------------------------------------------- C5-05
def case_grade_dir_entry_unbegun_or_unreadable(M, tmp):
    """(The fifth check's C5-05, its probe5d and mutant MY02) an honest graded PASS folder graded against its ledger AS IT
    WAS BEFORE THE RUN (its entry 'registered', never begun; the same bounds sha256) is UNVERIFIED ('its ledger entry was
    never begun'), exit 1; against an entry whose verdict this driver never writes (UNREADABLE), UNVERIFIED, exit 1.
    CONTROL: against the ledger as the run left it, PASS, exit 0."""
    rig = graded_rig(M, tmp)
    registered = tmp / "ledger_registered.json"
    shutil.copy2(rig.ledger, registered)
    guarded_run(rig)
    code, text = grade_dir_out(M, rig.out, rig.ledger)
    ok(code == 0 and "GRADE DIR VERDICT: GRADED: PASS" in text, f"CONTROL: {text[-300:]}")
    code, text = grade_dir_out(M, rig.out, registered)
    ok(code == 1 and "GRADED: UNVERIFIED (its ledger entry was never begun)" in text, f"REGISTERED: {text[-400:]}")
    data = ledger.load(rig.ledger)
    data["entries"][-1]["verdict"] = "GRADED, MAYBE: a verdict this driver never writes"
    unreadable = tmp / "ledger_unreadable.json"
    unreadable.write_text(json.dumps(data), encoding="utf-8")
    code, text = grade_dir_out(M, rig.out, unreadable)
    ok(code == 1 and "GRADED: UNVERIFIED (its ledger entry has a verdict this driver never writes)" in text,
       f"UNREADABLE: {text[-400:]}")


# ---------------------------------------------------------------------------------------------------- the sixth check
def case_grade_dir_other_live_chain_entry(M, tmp):
    """(The sixth check's C6-02, its R2NEXT and OTHERLEDGER; C6-03, its probe6b and mutant MZ2) an HONEST development
    batch (seeds 6041-6043; its results.json names #1, its own entry) graded against a ledger that is not the one it ran
    with never re-grades FAIL. FAULTS, each exit 0, PASS, no MISMATCH (round 5 gave exit 1): (C6-02) its own entry absent
    and the id it records naming ANOTHER live_chain batch whose seeds never meet its own (a graded registration of
    6201-6206, as the next entry is to the real R2's recorded #100; a development batch begun on 6301-6303), with its
    numbers kept and deleted (R2 has none); (C6-03) a MERGED ledger: its own entry renumbered #2 (the same seeds and
    bounds sha256) and #1 another live_chain batch, whose seeds MEET its own (6043-6045: only the renumbered exemption
    clears it) or never meet them (7001-7003): its entry #2 is found, the recorded #1 is no mismatch. CONTROLS: its own
    ledger (exit 0); the recorded id naming another driver's entry (exit 0); an empty ledger (exit 0); and a live_chain
    entry whose seeds MEET its own and differ, with its own entry absent: MISMATCH, exit 1."""
    dev, args = dev_rig(M, tmp / "dev")
    eq(guarded_run(dev, args)[0], 0, "a development batch ran")
    own = dev.entry()
    original = results_of(dev)
    eq((own["id"], own["first"], own["last"], original["ledger"]), (1, 6041, 6043, 1), "its own entry #1, as recorded")

    def planted(name: str, *entries: dict) -> Path:
        path = tmp / f"{name}.json"
        path.write_text(json.dumps({"what": "t", "entries": list(entries)}), encoding="utf-8")
        return path

    def batch(entry_id: int, first: int, last: int, purpose: str, status: str) -> dict:
        return {**own, "id": entry_id, "first": first, "last": last, "purpose": purpose, "status": status,
                "bounds_sha256": "b" * 64, "verdict": own["verdict"] if status == "done" else None}

    def honest(label: str, path: Path, confirmed: bool) -> str:
        code, text = grade_dir_out(M, dev.out, path)
        verdict = (f"GRADE DIR VERDICT: DEVELOPMENT, not graded{'' if confirmed else ' (unconfirmed: no ledger entry)'}: "
                   f"PASS; exit 0")
        ok(code == 0 and verdict in text and "MISMATCH" not in text, f"{label}: {text[-800:]}")
        return text
    nxt = {"the next graded registration (6201-6206)": planted("next_graded", batch(1, 6201, 6206, "graded", "registered")),
           "a development batch begun (6301-6303)": planted("next_dev", batch(1, 6301, 6303, "development", "started"))}
    for numbers_kept in (True, False):
        write_results(dev, original if numbers_kept else {k: v for k, v in original.items() if k != "numbers"})
        for label, path in nxt.items():
            honest(f"(C6-02) #1 is {label}; numbers {'kept' if numbers_kept else 'deleted'}", path, confirmed=False)
    write_results(dev, original)
    text = honest("(C6-03) merged: #1 another live_chain batch MEETING its seeds, its own entry #2",
                  planted("merged_meet", batch(1, 6043, 6045, "development", "done"), {**own, "id": 2}), confirmed=True)
    ok("LEDGER (read now): entry #2 (results.json names #1: matched by its seeds and bounds sha256)" in text, text[-800:])
    honest("(C6-03) merged: #1 another live_chain batch apart from its seeds, its own entry #2",
           planted("merged_apart", batch(1, 7001, 7003, "development", "done"), {**own, "id": 2}), confirmed=True)
    honest("CONTROL: its own ledger", dev.ledger, confirmed=True)
    honest("CONTROL: #1 another driver's entry",
           planted("other_driver", {**batch(1, 6041, 6041, "development", "done"), "driver": "ch5stops_other"}),
           confirmed=False)
    honest("CONTROL: an empty ledger", planted("empty"), confirmed=False)
    code, text = grade_dir_out(M, dev.out, planted("meets", batch(1, 6043, 6045, "development", "done")))
    ok(code == 1 and "names ledger entry #1, a live_chain entry for seeds [6043, 6045], not the folder's [6041, 6043]" in
       text, f"CONTROL: #1 meets its seeds and differs, its own entry absent: {text[-800:]}")


def case_seed_rules(M, tmp):
    """(The sixth check's C6-01) the seed rules are TYPE-STRICT (`type(seed) is int`, never int()): `seed_pair` takes two
    int seeds, first to last, and nothing else ("6201", 6201.0, true, backwards, one seed, three, a string, None);
    `job_seed_range` takes the jobs' seeds as ints, one per seed of a contiguous range (FAULTS: a seed written "6205", a
    gap, a repeat, no jobs, not a list); `numbers_jobs_problems` (FAULTS) seeds as strings or floats, a job's seed as a
    string, jobs with a gap whose seeds name their ends; and through grade DIR, an honest development folder (numbers
    deleted) with one job's seed written as a string: MISMATCH, never exit 0. CONTROLS: int seeds and jobs_of's jobs give
    the range and no problem; the folder as written exits 0."""
    eq(M.seed_pair([6201, 6206]), [6201, 6206], "CONTROL: two ints")
    for value in (["6201", "6206"], [6201.0, 6206.0], [True, 6206], [6206, 6201], [6201], [6201, 6206, 6207], "6201", None):
        eq(M.seed_pair(value), None, f"no seed pair: {value!r}")
    jobs = LC.jobs_of(6201, 6)
    eq(M.job_seed_range(jobs), ([6201, 6206], ""), "CONTROL: jobs_of's jobs")
    stringed = copy.deepcopy(jobs)
    stringed[2]["seed"] = str(stringed[2]["seed"])
    gap = [job for job in copy.deepcopy(jobs) if job["seed"] != 6203]
    repeat = copy.deepcopy(jobs)
    repeat[1]["seed"] = repeat[0]["seed"]
    for label, bad, needle in (("a seed written as a string", stringed, "are not all ints"),
                               ("a gap", gap, "not one per seed of a contiguous range"),
                               ("a repeat", repeat, "not one per seed of a contiguous range"),
                               ("no jobs", [], "it has no jobs"), ("not a list", {"jobs": jobs}, "not a list")):
        span, why = M.job_seed_range(bad)
        ok(span is None and needle in why, f"{label}: {span} {why!r}")
    eq(M.numbers_jobs_problems({"seeds": [6201, 6206], "jobs": jobs, "chains": 6}), [], "CONTROL: the numbers' jobs")
    for label, numbers_of, needle in (
            ("seeds as strings", {"seeds": ["6201", "6206"], "jobs": jobs, "chains": 6}, "are not two int seeds"),
            ("seeds as floats", {"seeds": [6201.0, 6206.0], "jobs": jobs, "chains": 6}, "are not two int seeds"),
            ("a job's seed as a string", {"seeds": [6201, 6206], "jobs": stringed, "chains": 6}, "bind no seed range"),
            ("a gap, the seeds its ends", {"seeds": [6201, 6206], "jobs": gap, "chains": 5}, "bind no seed range")):
        found = M.numbers_jobs_problems(numbers_of)
        ok(any(needle in problem for problem in found), f"{label}: {found}")
    dev, args = dev_rig(M, tmp / "dev")
    eq(guarded_run(dev, args)[0], 0, "a development batch ran")
    data = {key: value for key, value in results_of(dev).items() if key != "numbers"}
    write_results(dev, data)
    eq(grade_dir_out(M, dev.out, dev.ledger)[0], 0, "CONTROL: the folder, its numbers deleted")
    data["jobs"][1]["seed"] = str(data["jobs"][1]["seed"])
    write_results(dev, data)
    code, text = grade_dir_out(M, dev.out, dev.ledger)
    ok(code == 1 and "NUMBERS: MISMATCH (no numbers)" in text and "bind no seed range" in text,
       f"a job's seed written as a string: {text[-800:]}")


# ==================================================================================================== THE TESTCASES
class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="t_", dir=_TEMP_ROOT))
        self.profile = L5.PROFILE

    def tearDown(self) -> None:
        L5.PROFILE = self.profile  # (critic CH-05) a process global the chains set
        shutil.rmtree(self.tmp, ignore_errors=True)

    def case(self, fn) -> None:
        fn(LC, self.tmp)


def _bind(cls, names):
    for name in names:
        fn = globals()[f"case_{name}"]
        setattr(cls, f"test_{name}", lambda self, fn=fn: self.case(fn))
    return cls


LegsTests = _bind(type("LegsTests", (Base,), {}), ("legs_real", "legs_short", "synthetic_optional_end", "waypoint_skipped",
                                                   "refused_targets", "no_budget", "backwards", "empty_proof_refused",
                                                   "leg_frames"))
ProofTests = _bind(type("ProofTests", (Base,), {}), ("proof_flags", "var_boundary", "missing_key", "trainer_flag",
                                                     "empty_proof_never_holds"))
ContinueTests = _bind(type("ContinueTests", (Base,), {}), (
    "continue_control", "continue_c1_proof", "continue_c1_this_run", "continue_c2", "continue_c3_at_cap",
    "continue_c3_unmeasured", "continue_c3_last_line", "continue_c4", "continue_c5", "continue_c6",
    "deletion_failure_continues"))
CustodyTests = _bind(type("CustodyTests", (Base,), {}), (
    "custody_control", "custody_wrong_md5", "custody_wrong_frame", "custody_wrong_state", "custody_wrong_world_sha",
    "custody_wrong_world_path", "custody_l1_state", "custody_l1_world", "custody_l1_starter", "custody_env_keys",
    "custody_unread_start"))
ChainRunTests = _bind(type("ChainRunTests", (Base,), {}), (
    "chain_control", "chain_stops_on_miss", "chain_stale_stops", "truncated_last_line", "chain_killed_marker",
    "stop_before_chain", "stop_during_leg", "world_over_cap", "deletion_failure_chain", "overshoot_reaches",
    "unread_start_stops", "profile_guard", "leg_error_salvaged"))
GradeTests = _bind(type("GradeTests", (Base,), {}), (
    "grade_control", "reach_5_of_6_pass", "reach_4_of_6_fails", "reach_5_rows_vacuous", "not_run_never_reached",
    "purity_middle_fail", "each_purity_id_fails", "purity_stopped_chain_pass", "purity_salvaged_vacuous",
    "stale_middle_leg_fails", "world_exactly_cap_fails", "custody_grade_fail", "refused_chain_fails_custody",
    "starter_wrong_species", "starter_wrong_ot", "memory_counts", "memory_amnesia", "memory_l1_not_new",
    "memory_missing_vacuous", "memory_path", "last_leg_must_continue", "frozen_leftover", "reported_never_counts",
    "quotes"))
DiskTests = _bind(type("DiskTests", (Base,), {}), (
    "measure_301mb", "no_whole_read", "guard_decision", "guard_newest_only", "stat_race", "salvage_chain",
    "salvage_before_launch", "end_sweep"))
RefusalTests = _bind(type("RefusalTests", (Base,), {}), (
    "refusal_controls", "r1", "r2", "r2_build_root", "r3", "r3_named", "r4", "r5", "r6", "r7", "r8", "r9", "r9_dirty"))
LedgerTests = _bind(type("LedgerTests", (Base,), {}), (
    "register_begin", "changed_budget_refused", "changed_reach_min_refused", "changed_cap_refused",
    "changed_milestones_refused", "changed_ai_code_refused", "changed_grader_refused", "unregistered_refused",
    "dev_on_registered_refused", "dev_numbers_prediction", "real_ledger_seeds", "bounds_needles"))
SchedulerTests = _bind(type("SchedulerTests", (Base,), {}), ("scheduler_max_3", "scheduler_order_and_stagger",
                                                             "scheduler_may_start"))
OrchestratorTests = _bind(type("OrchestratorTests", (Base,), {}), (
    "e2e_graded_pass", "e2e_dry_run", "e2e_unregistered_refused", "e2e_refusal_before_ledger", "e2e_development",
    "free_guard_aborts", "world_guard_kills", "watchdog", "tree_move_stops", "tree_move_tick"))
WiringTests = _bind(type("WiringTests", (Base,), {}), ("wiring", "wiring_defaults"))
# (the fix round, the verifier's V-01..V-09)
OutTests = _bind(type("OutTests", (Base,), {}), ("r11_out_not_empty", "out_listing", "e2e_out_not_empty_refused",
                                                 "e2e_out_empty_proceeds",
                                                 # (the third fix round) C3-E01, C3-G05
                                                 "out_listing_unmakeable", "e2e_out_unmakeable_refused",
                                                 "e2e_out_undone_on_ledger_refusal", "e2e_steps_before_begin"))
RegradeTests = _bind(type("RegradeTests", (Base,), {}), (
    "grade_batch_foreign_row", "grade_dir_foreign_row", "regrade_honest", "flipped_continue_not_counted",
    "row_identity_mismatch", "kept_file_swapped", "row_proof_weakened", "row_leg_names_checked",
    "grade_dir_marker_on_disk",
    # (the second fix round) C2-01, C2-03, the checker's C13
    "row_starter_mismatch", "regrade_custody_stored_empty", "grade_dir_registered_proof",
    "e2e_row_proof_weakened_in_run", "e2e_evidence_rederived_reach", "kept_file_not_json",
    # (the third fix round) C3-G01..G04, C3-G06
    "leg_identity_each_field", "relabelled_copy_stays_fail", "shared_legs_never_count", "grade_dir_numbers_verified",
    "grade_dir_missing_records", "grade_dir_moved_out", "grade_dir_frozen_at_seal", "row_identity_each_field",
    "not_run_after_continuing_leg"))
ClosureTests = _bind(type("ClosureTests", (Base,), {}), (
    "grader_files_cover_closure", "closure_not_vacuous", "closure_scan_planted", "grader_data_hashed",
    "changed_decoder_refused", "crlf_only_accepted",
    # (the second fix round) C2-02, C2-05
    "closure_starts", "closure_starts_planted", "path_runs_are_roots", "path_run_scan_planted",
    "closure_toplevel_names", "changed_path_run_refused", "closure_enforced_register", "closure_enforced_run",
    # (the third fix round) C3-H01, C3-H02, C3-H04, C3-H05, C3-E06's named file
    "closure_resolution_planted", "pycache_planted", "resolution_enforced_register", "toplevel_planted",
    "python_env_refused", "closure_refusal_names_all", "closure_ai_starts_planted", "closure_parse_error_named",
    # (the third fix round's finish, 2026-11-06) the full regression lane's failure: sandbox-pokebot/mgba present
    "toplevel_mgba_exempt"))
KindTests = _bind(type("KindTests", (Base,), {}), ("verdict_impure_l5_fails", "verdict_stale_l5_fails",
                                                   "verdict_wrong_starter_fails", "graded_kinds_match_bounds"))
GuardTests = _bind(type("GuardTests", (Base,), {}), (
    "watchdog_value", "world_grew_larger_graded", "kept_outside_repo", "dev_partial_overlap_refused",
    "e2e_leftover_reported", "git_state_scratch", "abort_before_leg", "starter_floor",
    # (the second fix round) the verifier's V02
    "starter_unread_ot_and_tid"))
PredictionTests = _bind(type("PredictionTests", (Base,), {}), ("prediction_sha_file_bytes", "prediction_not_utf8_refused"))
DeadLaunchTests = _bind(type("DeadLaunchTests", (Base,), {}), ("launch_died_rule", "dead_launch_named",
                                                               "e2e_dead_launch_evidence", "world_line_no_file"))
# (the second fix round) C2-07: the harness's exception after the chains still finishes the ledger entry
GradeErrorTests = _bind(type("GradeErrorTests", (Base,), {}), (
    "grade_error_finishes_entry", "evidence_error_finishes_entry",
    # (the third fix round) C3-E03..E07
    "ledger_finish_transient_retried", "ledger_finish_computed_unwritable", "ledger_unwritable_not_finished",
    "grade_error_any_exception", "results_write_error_both_paths", "error_evidence_any_exception", "dev_error_labelled",
    "dev_unhashed_printed", "grade_dir_error_batch", "grade_dir_exit_codes", "main_crash_exit_5", "unprintable_error",
    "grading_interrupt", "evidence_write_error_bounds_once"))
# (the third fix round) the chains-run guard; C3-E02: the AI's output is untrusted
ChainGuardTests = _bind(type("ChainGuardTests", (Base,), {}), ("chains_error_finishes_entry",
                                                               "chains_interrupt_finishes_entry"))
UntrustedTests = _bind(type("UntrustedTests", (Base,), {}), (
    "world_counts_untrusted", "e2e_untrusted_world_fails_not_errors", "log_untrusted", "chain_bad_verdict",
    "kept_line_wrong_shape"))
# (the fourth fix round, 2026-11-06) the fourth check's three lenses: errors, grading, hashing
C4ErrorTests = _bind(type("C4ErrorTests", (Base,), {}), (
    "world_kind_untrusted", "e2e_world_folder_graded", "out_second_launch_refused", "out_written_after_listing",
    "out_undo_edges", "guard_second_interrupt", "guard_after_finish_keeps_verdict", "error_finish_retried",
    "lone_surrogate_graded", "finish_entry_only_error"))
C4GradingTests = _bind(type("C4GradingTests", (Base,), {}), (
    "grade_dir_never_better_than_ledger", "grade_dir_error_states", "grade_dir_planted_stop_and_deleted_leg",
    "grade_dir_aborted_and_development", "salvage_exemption_needs_record"))
C4HashingTests = _bind(type("C4HashingTests", (Base,), {}), (
    "closure_pyw_planted", "toplevel_installed_planted", "ai_problems_planted", "run_refusal_falls_through",
    "resolution_branches_planted", "pycache_branches_planted", "toplevel_branches_planted", "ai_starts_branches_planted",
    "wiring_bodies"))
# (the fifth fix round, 2026-11-06) the fifth check's C5-01..C5-05
C5Tests = _bind(type("C5Tests", (Base,), {}), (
    "grade_dir_edited_fail_folder", "recorded_entry_rules", "finish_entry_without_error_record", "grade_dir_contradiction",
    "guard_sigint_restored", "grade_dir_entry_unbegun_or_unreadable"))
# (the sixth fix round, 2026-11-06) the sixth check's C6-01 and C6-02 (and C6-03's merged ledger)
C6Tests = _bind(type("C6Tests", (Base,), {}), ("grade_dir_other_live_chain_entry", "seed_rules"))


class PurposeTests(unittest.TestCase):
    def test_purpose_has_no_default(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as caught:
            LC.main(["run", "--out", "C:/elsewhere/out", "--run", "ch5"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--purpose", err.getvalue())


class ImportTests(Base):
    def test_the_driver_takes_no_value_from_the_ai(self) -> None:
        from ai_player.gates.check_grader_imports import GRADERS, scan

        self.assertEqual(scan(REPO, ("ai_player.gates.live_chain",)), [])
        self.assertIn("ai_player.gates.live_chain", GRADERS, "the lane's G-3 CLI walks the driver")

    def test_the_walk_sees_an_ai_import_planted_in_the_driver(self) -> None:
        from ai_player.gates.check_grader_imports import scan

        root = self.tmp / "copy"
        for path in (REPO / "ai_player").rglob("*.py"):
            rel = path.relative_to(REPO)
            if rel.parts[1] == "evidence" or "__pycache__" in rel.parts:
                continue
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, root / rel)
        driver = root / "ai_player" / "gates" / "live_chain.py"
        driver.write_text(driver.read_text(encoding="utf-8").replace(
            "from ai_player.gates import ledger  # noqa: E402",
            "from ai_player.gates import ledger  # noqa: E402\nfrom ai_player.brain.goals import open_way  # noqa: E402", 1),
            encoding="utf-8")
        self.assertTrue(scan(root, ("ai_player.gates.live_chain",)))

    @staticmethod
    def importers(root: Path) -> list[str]:
        """(CH-17) every file of the AI's package (ai_player/ outside gates/ and evidence/) whose SYNTAX imports a module
        named live_chain: an AST scan of *.py only, so a mention in a comment, a docstring or a document never fires."""
        found = []
        for path in (root / "ai_player").rglob("*.py"):
            rel = path.relative_to(root / "ai_player")
            if rel.parts[0] in ("gates", "evidence") or "__pycache__" in rel.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                         [node.module or ""] + [a.name for a in node.names] if isinstance(node, ast.ImportFrom) else [])
                if any("live_chain" in name for name in names):
                    found.append(rel.as_posix())
        return found

    def test_no_ai_file_imports_the_driver(self) -> None:
        self.assertEqual(self.importers(REPO), [])

    def test_a_planted_import_is_caught_and_a_mention_is_not(self) -> None:
        root = self.tmp / "ai"
        (root / "ai_player").mkdir(parents=True)
        mode = root / "ai_player" / "mode.py"
        mode.write_text('"""It never imports live_chain."""\n# from ai_player.gates import live_chain\nx = 1\n',
                        encoding="utf-8")
        (root / "ai_player" / "README.md").write_text("live_chain is the held-out", encoding="utf-8")
        self.assertEqual(self.importers(root), [], "a mention in a comment, a docstring or a document")
        mode.write_text(mode.read_text(encoding="utf-8") + "from ai_player.gates import live_chain\n", encoding="utf-8")
        self.assertEqual(self.importers(root), ["mode.py"])


class ReaderTests(unittest.TestCase):
    REAL = [
        "[AI-HANDS] [AI-GOALS] goal go not done: stuck: an unexpected multichoice on screen",
        "[AI-HANDS] [AI-GOALS] goal talk not done: stuck: an unexpected multichoice while the person at (7, 5) talked",
        "[AI-HANDS] the battle: an unexpected yes_no on screen",
        "[AI-HANDS] flee: an unexpected party in the battle",
        "[AI-HANDS] intro: an unexpected naming on screen",
        "[AI-WORLD] memory from the last snapshot of C:\\Remote Projects\\Pokebot_Gen3_Enhancement\\sandbox-pokebot\\profiles"
        "\\ai-chain-probe-1\\ai_player_runs\\20261101-012501-C1L1\\world.jsonl: 12 maps (OLDALE_TOWN 768 tiles 0 bumped, "
        "ROUTE101 832 tiles 0 bumped), 5015 tiles learned, 27 warp links, 13 connections, 47 map changes; goal -; "
        "personality Story (weights Weights(frontier=1.0))",
    ]

    def test_real_lines_are_read(self) -> None:
        found = LC.log_counts(self.REAL)
        self.assertEqual(found["multichoice"], 2)
        self.assertEqual(found["unexpected"], {"multichoice": 2, "yes_no": 1, "party": 1, "naming": 1})
        self.assertEqual(found["forms"]["multichoice while the person"], 1)
        self.assertEqual(found["forms"]["party in the battle"], 1)
        memory = found["memory"]
        self.assertTrue(memory["path"].endswith("20261101-012501-C1L1\\world.jsonl"))
        self.assertEqual(memory["counts"], {"maps": 12, "tiles": 5015, "warps": 27, "connections": 13, "transitions": 47})
        fresh = LC.parse_memory_line("[AI-WORLD] memory from nothing (a new memory): 0 maps (none), 0 tiles learned, 0 "
                                     "warp links, 0 connections, 0 map changes; goal -")
        self.assertTrue(fresh["new"])
        self.assertIsNone(fresh["path"])


class TieTests(Base):
    def test_the_ai_reads_only_the_last_line(self) -> None:
        """The AI's own reader (`world.memory.read_world`, imported by this TEST only) on a 3-snapshot world.jsonl and on
        the kept last line gives the same memory: the deleted file can be replaced by its last line (F8)."""
        from ai_player.world.memory import read_world

        world = self.tmp / "world.jsonl"
        world.write_text(snapshot(1, 1) + "\n" + snapshot(2, 5) + "\n" + snapshot(3, 9) + "\n\n", encoding="utf-8")
        keep = self.tmp / "kept.jsonl"
        LC.stream_world_tail(world, keep)
        self.assertEqual(read_world(world).snapshot(), read_world(keep).snapshot())

        def merging(path):  # FAULT: a reader that merged every line would not be served by the last line alone
            merged: dict = {}
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    for key, value in json.loads(line)["maps"].items():
                        merged.setdefault(key, value)
            return merged
        self.assertEqual(len(merging(world)), 3)
        self.assertEqual(len(merging(keep)), 3)  # the last line holds every map: the merge equals it here...
        first_only = self.tmp / "first.jsonl"
        first_only.write_text(snapshot(3, 9) + "\n" + snapshot(1, 1) + "\n", encoding="utf-8")
        kept_first = self.tmp / "kept_first.jsonl"
        LC.stream_world_tail(first_only, kept_first)
        self.assertNotEqual(len(merging(first_only)), len(merging(kept_first)))  # ...and differs when it does not

    def test_every_graded_runs_chapters_have_a_budget(self) -> None:
        for run in LC.GRADED_RUNS.values():
            for leg in LC.legs_of(run["to"], real_milestones()):
                self.assertIn(leg["chapter"], LC.FRAMES_BY_CHAPTER)


# ==================================================================================================== THE MUTANTS (D5)
def _prepare_after_begin() -> tuple[str, str]:
    """(The third fix round, C3-E01) the mutant that makes --out and the job files AFTER ledger.begin: its anchor is the
    source from the prepare_out call to the entry's ctx update, its replacement the same two parts swapped (computed
    from the source, so it follows the code)."""
    text = SOURCE.read_text(encoding="utf-8")
    a = text.index("    try:\n        made = prepare_out(")
    b = text.index("    # (the checkers' C2-07, C3-E03..E07) what the ERROR record needs")
    c = text.index('    ctx.update({"entry_id": entry["id"], "ledger_lines": ledger_lines})\n')
    return text[a:c], text[b:c] + text[a:b]


#: (id, anchor in live_chain.py (exactly once), replacement, [cases that must FAIL on it])
MUTANTS = [
    ("M01_reach_min", "GRADED, len(reached) >= reach_min,", "GRADED, len(reached) >= reach_min - 1,", ["reach_4_of_6_fails"]),
    ("M02_overshoot_stops", 'ok = this_run == PASS and bool(after.get("held"))',
     'ok = this_run == PASS and bool(after.get("held")) and not (row.get("proof_before") or {}).get("held")',
     ["overshoot_reaches"]),
    ("M03_var_gt", "isinstance(v, int) and v >= need", "isinstance(v, int) and v > need", ["var_boundary"]),
    ("M04_missing_held", "        if value is None:\n            missing.append(key)\n",
     "        if value is None:\n            pass\n", ["missing_key"]),
    ("M05_no_stop_on_c1", "    if not reached:\n        why.append(", "    if False:\n        why.append(",
     ["chain_stops_on_miss", "continue_c1_proof"]),
    ("M06_not_run_sampled", 'RAN = ("RAN", "SALVAGED", "ERROR")', 'RAN = ("RAN", "SALVAGED", "ERROR", "NOT RUN")',
     ["purity_stopped_chain_pass"]),
    ("M07_purity_id_dropped", '"L5.PURITY_BREACHES",\n              "L5.PURITY_PACKAGE")', '"L5.PURITY_BREACHES")',
     ["each_purity_id_fails", "continue_c2"]),
    ("M08_this_run_last_only", '_status(leg, "L5.THIS_RUN")) for chain, leg in ran]',
     '_status(leg, "L5.THIS_RUN")) for chain, leg in ran[-1:]]', ["stale_middle_leg_fails"]),
    ("M09_cap_gt_grade", "for name, size in measured if size >= WORLD_MAX_BYTES]",
     "for name, size in measured if size > WORLD_MAX_BYTES]", ["world_exactly_cap_fails"]),
    ("M09b_cap_gt_continue", "WORLD_SIZE_KIND == GRADED and size >= WORLD_MAX_BYTES:",
     "WORLD_SIZE_KIND == GRADED and size > WORLD_MAX_BYTES:", ["continue_c3_at_cap"]),
    ("M10_no_delete", "            world_file = measure_then_delete(world_path)\n",
     '            world_file = {"bytes": size_first, "deleted": True, "present": True}\n', ["chain_control"]),
    # (re-anchored in the third fix round: the record filter, C3-E02)
    ("M11_original_world", "        carried.pop(arm_name, None)\n        if end_state is not None and end_state.is_file() "
                           "and row[\"kept_world\"]:\n            # (C3-E02) actions.jsonl is the AI's: a record that is not "
                           "a JSON object is no page it read\n            reads = [r for r in run.earlier + run.records if "
                           "isinstance(r, dict) and r.get(\"decision\") == \"read\"]\n            carried[arm_name] = (end_state, "
                           "Path(row[\"kept_world\"]), reads)\n", "        pass\n", ["chain_control"]),
    ("M12_custody_md5", "    elif after.get(\"state_md5\") is None or (before.get(\"frame\"), before.get(\"state_md5\")) != "
                        "(after.get(\"frame\"),", "    elif False and (before.get(\"frame\"), before.get(\"state_md5\")) != "
                                                 "(after.get(\"frame\"),", ["custody_wrong_md5", "custody_wrong_frame"]),
    ("M13_starter_field", "ok = str(lead[1]).upper() == chain.get(\"starter\")", "ok = str(lead[1]).upper() == "
                                                                                  "str(lead[1]).upper()",
     ["starter_wrong_species"]),
    ("M14_optional_end", "if m[\"chapter\"] == chapter and not m.get(\"optional\") and m.get(\"waypoint\") is None]",
     "if m[\"chapter\"] == chapter and m.get(\"waypoint\") is None]", ["synthetic_optional_end"]),
    ("M14b_waypoint_end", "if m[\"chapter\"] == chapter and not m.get(\"optional\") and m.get(\"waypoint\") is None]",
     "if m[\"chapter\"] == chapter and not m.get(\"optional\")]", ["waypoint_skipped"]),
    ("M15_r1", "    if out == repo or out.is_relative_to(repo):", "    if False:", ["r1"]),
    ("M16_r2", "        if given or args.run not in GRADED_RUNS:", "        if False:", ["r2"]),
    ("M17_r7", '    if facts.get("profiles_exist"):', "    if False:", ["r7"]),
    ("M18_free_floor", "    if free is None or free < FREE_MIN_GB:", "    if free is None:", ["r6"]),
    ("M19_child_guard", "    refusal = child_refusal(job, L5.PROFILE)", "    refusal = None", ["profile_guard"]),
    ("M20_parallel", "PARALLEL = 3", "PARALLEL = 4", ["scheduler_max_3", "e2e_graded_pass"]),
    ("M21_reported_counted", "    return typed_verdict(checks, waivers={})",
     "    return typed_verdict(checks, waivers={}) if all(c.status == PASS for c in checks if c.kind == REPORTED) "
     "else 'FAIL'", ["reported_never_counts"]),
    ("M22_grader_files_unhashed", '"grader_files": {name: text_sha256(repo / name) for name in GRADER_FILES}}',
     '"grader_files": {}}', ["changed_grader_refused"]),
    ("M22b_ai_code_unhashed", '"ai_code_sha256": ai_code_sha256(repo),', '"ai_code_sha256": None,',
     ["changed_ai_code_refused"]),
    ("M23_guard_threshold", "    if world_bytes is not None and world_bytes > GUARD_WORLD_BYTES:", "    if False:",
     ["guard_decision", "world_guard_kills"]),
    ("M23b_guard_ge", "world_bytes > GUARD_WORLD_BYTES:", "world_bytes >= GUARD_WORLD_BYTES:", ["guard_decision"]),
    ("M24_no_not_run_rows", "        chain[\"legs\"].append(not_run_row(job, leg, status, reason))", "        pass",
     ["chain_stops_on_miss"]),
    ("M25_r8", "    if learner:", "    if False:", ["r8"]),
    ("M26_guard_max_all", "        return folders[-1], (runs / folders[-1] / \"world.jsonl\").stat().st_size\n",
     "        return folders[-1], max((runs / f / \"world.jsonl\").stat().st_size for f in folders if "
     "(runs / f / \"world.jsonl\").is_file())\n", ["guard_newest_only"]),
    ("M27_last_ok_ignored", '    if not world.get("last_ok"):', "    if False:", ["truncated_last_line",
                                                                                "continue_c3_last_line"]),
    ("M28_whole_read", '    with open(path, "rb") as handle:\n        for raw in handle:',
     "    if True:\n        for raw in path.read_bytes().splitlines(True):", ["no_whole_read"]),
    ("M29_c2_ignored", "    if wrong:\n        why.append(f\"C2", "    if False:\n        why.append(f\"C2", ["continue_c2"]),
    ("M30_c4_ignored", '    if row.get("guard_killed"):', "    if False:", ["continue_c4", "chain_killed_marker"]),
    ("M31_c5_ignored", '    if row.get("custody"):', "    if False:", ["continue_c5", "unread_start_stops"]),
    ("M32_c6_ignored", "    if stop_seen:", "    if False:", ["continue_c6", "stop_during_leg"]),
    ("M33_pre_leg_stop", "            if (out / name).is_file():", "            if False:", ["stop_before_chain"]),
    ("M34_custody_l1_state", '        if "--state" in command:\n            problems.append("L1 started from --state")',
     '        if False:\n            problems.append("L1 started from --state")', ["custody_l1_state"]),
    ("M35_custody_world_sha", '    if row.get("world_in_sha256") is None or row.get("world_in_sha256") != '
                              'prev.get("kept_world_sha256"):', "    if False:", ["custody_wrong_world_sha"]),
    ("M36_custody_env_keys", "    if keys != ENV_KEYS_LATER:", "    if False:", ["custody_env_keys"]),
    ("M37_unlaunched_ignored", 'GRADED, not unlaunched and not custody_bad,', 'GRADED, not custody_bad,',
     ["refused_chain_fails_custody"]),
    ("M38_memory_counts", '        if kept is None or said.get("counts") != kept:', "        if False:",
     ["memory_counts"]),
    ("M39_deletion_stops", '    if row.get("guard_killed"):\n',
     '    if not (row.get("world_file") or {}).get("deleted"):\n        why.append("C3 not deleted")\n'
     '    if row.get("guard_killed"):\n', ["deletion_failure_continues", "deletion_failure_chain"]),
    ("M40_free_no_abort", '            if cause == "free" and not state["aborted"]:', "            if False:",
     ["free_guard_aborts"]),
    ("M41_world_no_kill", "            if cause is not None and leg is not None:", "            if False:",
     ["world_guard_kills"]),
    ("M42_salvage_any_folder", 'if p.is_dir() and p.name.endswith(f"-{arm_name}"))', "if p.is_dir())",
     ["salvage_before_launch"]),
    ("M43_stat_race", "    try:\n        return folders[-1], (runs / folders[-1] / \"world.jsonl\").stat().st_size\n"
                      "    except OSError:\n        return folders[-1], None\n",
     "    return folders[-1], (runs / folders[-1] / \"world.jsonl\").stat().st_size\n", ["stat_race"]),
    ("M44_dev_named", '        if named:\n            return (f"R3', '        if False:\n            return (f"R3',
     ["r3_named"]),
    ("M45_r9_head", '        if git.get("error") or not git.get("head") or git.get("head") != git.get("origin"):',
     "        if False:", ["r9"]),
    ("M46_r9_dirty", '        if git.get("dirty"):', "        if False:", ["r9_dirty"]),
    ("M47_graded_build_root", '        if Path(facts["default_build_root"]) != build_root:', "        if False:",
     ["r2_build_root"]),
    ("M48_r5", '    if facts.get("g3"):', "    if False:", ["r5"]),
    ("M49_r4", '    if facts.get("legs_error"):', "    if False:", ["r4"]),
    ("M50_r3", "        if missing:\n            return f\"R3", "        if False:\n            return f\"R3", ["r3"]),
    ("M51_empty_proof", '        if not (proof["flags"] or proof["variables"] or proof["trainers"]):', "        if False:",
     ["empty_proof_refused"]),
    ("M52_waypoint_target", '    if target.get("waypoint") is not None:', "    if False:", ["refused_targets"]),
    ("M53_optional_target", '    if target.get("optional"):', "    if False:", ["refused_targets"]),
    ("M54_backwards", '        if b["chapter"] < a["chapter"]:', "        if False:", ["backwards"]),
    ("M55_no_budget", "        if chapter not in budgets:", "        if False:", ["no_budget"]),
    ("M56_watchdog", '            if now - started.get(job["chain"], now) > watchdog and',
     "            if False and", ["watchdog"]),
    ("M57_tree_no_stop", '            if not tree.check("during the batch") and not (out / STOP_FILE).is_file():',
     "            if False:", ["tree_move_tick"]),
    ("M57b_tree_no_start_check", '        if tree.moved or not tree.check(f"before {job[\'chain\']}"):', "        if False:",
     ["tree_move_stops"]),
    ("M58_no_begin", "        entry, ledger_lines = begin(args.purpose, seeds,", "        entry, ledger_lines = _skip(args.purpose, seeds,",
     ["wiring"]),
    # (re-anchored in the third fix round: the finish is retried through finish_entry, C3-E03)
    ("M59_no_finish", '        why = finish_entry(entry["id"], verdict_line, reference, ctx["ledger_path"], deps.sleep)',
     '        why = _skip(entry["id"], verdict_line, reference, ctx["ledger_path"], deps.sleep)', ["wiring"]),
    ("M60_no_seal", '    _, frozen_line = tree.seal("PASS" if held else "FAIL")', '    _, frozen_line = (None, "skipped")',
     ["wiring"]),
    ("M61_no_refusal", "    refusal = run_refusal(args, facts)", "    refusal = None", ["wiring", "e2e_refusal_before_ledger"]),
    # (re-anchored in the third fix round: each check of the AI's output is `judged`, C3-E02)
    ("M62_no_purity", '        judged(lambda: check_purity(run, None), "the purity checks", run.notes)\n', "        pass\n",
     ["wiring", "chain_control"]),
    ("M63_no_this_run", '        judged(lambda: L5.check_after_is_this_run(run), "L5.THIS_RUN", run.notes)\n', "        pass\n",
     ["wiring", "chain_control"]),
    ("M64_no_custody", '        row["custody"] = custody_problems(row, prev, job, index)', '        row["custody"] = []',
     ["wiring"]),
    ("M65_r3_run_given", '        if args.run is not None:\n            return "R3', '        if False:\n            return "R3',
     ["r3_run_given"]),
    ("M66_this_run_ignored", "    ok = this_run == PASS and bool(after.get(\"held\"))", "    ok = True and bool(after.get(\"held\"))",
     ["continue_c1_this_run", "chain_stale_stops"]),
    ("M67_starter_ot_ignored", 'and owner.get(lead[0]) == after.get("player_tid")', "and True", ["starter_wrong_ot"]),
    ("M68_memory_path_ignored", '        if _norm(said.get("path")) != _norm(leg.get("world_in")):', "        if False:",
     ["memory_path"]),
    ("M69_memory_l1_ignored", '            if not said.get("new"):', "            if False:", ["memory_l1_not_new"]),
    ("M74_flag_any_value", '    for name in proof.get("flags") or {}:\n        one(name, lambda v: v == 1)',
     '    for name in proof.get("flags") or {}:\n        one(name, lambda v: v >= 0)', ["proof_flags"]),
    ("M74b_trainer_any_value", '        one(f"TRAINER_{name}", lambda v: v == 1)', '        one(f"TRAINER_{name}", lambda v: True)',
     ["trainer_flag"]),
    ("M75_custody_l1_starter", '        if env.get(ENV_STARTER) != job.get("starter"):', "        if False:",
     ["custody_l1_starter"]),
    ("M76_custody_state", "    if state is None or want is None or _norm(state) != _norm(want):", "    if False:",
     ["custody_wrong_state"]),
    ("M77_custody_world_path", '    if _norm(row.get("world_in")) != _norm(prev.get("kept_world")):', "    if False:",
     ["custody_wrong_world_path"]),
    ("M78_custody_l1_world", '        if row.get("world_in") is not None:', "        if False:", ["custody_l1_world"]),
    ("M81_reach_ignores_continue", 'all(leg.get("status") == "RAN" and leg.get("continue")',
     'all(leg.get("status") == "RAN"', ["last_leg_must_continue"]),
    ("M82_reach_ignores_count", "    return len(legs) == legs_wanted and legs_wanted > 0 and", "    return legs_wanted > 0 and",
     ["last_leg_must_continue"]),
    ("M83_abort_exit", "    if aborted:\n        return 3\n", "", ["free_guard_aborts"]),
    # (the third fix round: run_batch's guard calls end_sweep too, so WIRING's name check no longer sees this one)
    ("M85_no_end_sweep", "    world_left = end_sweep(jobs, build_root)", "    world_left = []", ["world_guard_kills"]),
    ("M86_leftover_ignored", 'checks.append(_check("LC.LEFTOVER", GRADED, not leftover,',
     'checks.append(_check("LC.LEFTOVER", GRADED, True,', ["frozen_leftover"]),
    ("M87_frozen_ignored", 'checks.append(_check("LC.FROZEN", GRADED, bool(frozen[0]),',
     'checks.append(_check("LC.FROZEN", GRADED, True,', ["frozen_leftover"]),
    ("M88_starter_grade_ignored", 'checks.append(_check("LC.STARTER", GRADED, not wrong_starters,',
     'checks.append(_check("LC.STARTER", GRADED, True,', ["starter_wrong_species", "starter_wrong_ot"]),
    ("M89_custody_rows_ignored", 'GRADED, not unlaunched and not custody_bad,', 'GRADED, not unlaunched,',
     ["custody_grade_fail"]),
    ("M90_purity_grade_ignored", 'checks.append(_check("LC.PURITY", GRADED, not bad and judged == len(ran),',
     'checks.append(_check("LC.PURITY", GRADED, judged == len(ran),', ["purity_middle_fail", "each_purity_id_fails"]),
    ("M92_profile_prefix_ignored", '    if not str(job.get("profile", "")).startswith(PROFILE_PREFIX):', "    if False:",
     ["profile_guard"]),
    ("M94_c3_unmeasured", '        why.append("C3 its world.jsonl was not measured")', "        pass",
     ["continue_c3_unmeasured"]),
    # ------------------------------------------------------------------ the fix round (the verifier's V-01..V-09)
    # V-01: a non-empty --out is refused before ledger.begin
    ("M95_out_not_empty_ignored", "    if entries:\n        return (f\"R11:", "    if False:\n        return (f\"R11:",
     ["r11_out_not_empty"]),
    ("M96_out_unmeasured", '    facts.update(out_listing(facts["out"]))', '    facts.update({"out_entries": []})',
     ["e2e_out_not_empty_refused"]),
    ("M97_out_not_a_folder_ok", '    if facts.get("out_error"):', "    if False:", ["r11_out_not_empty"]),
    ("M98_out_listing_blind", '        return {"out_entries": sorted(p.name for p in out.iterdir())}',
     '        return {"out_entries": []}', ["out_listing"]),
    # V-02: only the registered rows count, each re-derived from its own facts
    # (re-anchored in the fourth fix round: grade_batch passes the salvaged chains, C4-G04)
    ("M99_raw_rows_graded", "    chains, ignored, rederived = registered_chains(chains, jobs, legs, stop_files, kept_root, salvaged)",
     "    _, ignored, rederived = registered_chains(chains, jobs, legs, stop_files, kept_root, salvaged)",
     ["grade_batch_foreign_row", "flipped_continue_not_counted"]),
    # (re-anchored in the second fix round: registered_chains' comprehension became a loop, C2-01)
    ("M100_unregistered_counted",
     '    return kept, ignored, [note for chain in kept for note in chain.get("rederived") or []]',
     '    kept += [c for c in chains if c.get("chain") not in registered]\n'
     '    return kept, ignored, [note for chain in kept for note in chain.get("rederived") or []]',
     ["grade_batch_foreign_row"]),
    ("M101_duplicates_counted", "        if len(found) != 1:\n            continue\n",
     "        if not found:\n            continue\n", ["grade_batch_foreign_row"]),
    # (the second fix round: a mis-identified row is ignored BEFORE re-derivation, C2-01, so the stored continue plays
    # no part in row_identity_mismatch any more)
    ("M102_stored_continue_trusted", '            leg["continue"] = stored and not problems', '            leg["continue"] = stored',
     ["flipped_continue_not_counted", "kept_file_swapped", "row_proof_weakened", "row_leg_names_checked"]),
    ("M103_identity_ignored", '        wrong = [f"its {key} {found[0].get(key)!r} is not the registered {job.get(key)!r}" for '
                              'key in IDENTITY\n                 if found[0].get(key) != job.get(key)]', "        wrong = []",
     ["row_identity_mismatch", "row_starter_mismatch"]),
    ("M104_kept_not_reread", "            kept = kept_problem(leg, path)", "            kept = None", ["kept_file_swapped"]),
    ("M105_row_proof_used", '            proof = want["proof"] if want is not None else (leg.get("proof") or {})',
     '            proof = leg.get("proof") or {}', ["row_proof_weakened"]),
    ("M106_leg_names_unchecked", '            if legs is not None and (want is None or (leg.get("leg"), leg.get("target")) != '
                                 '(want["leg"], want["target"])):', "            if False:", ["row_leg_names_checked"]),
    ("M107_stored_custody_dropped", '            leg["custody"] = list(dict.fromkeys([*(leg.get("custody") or []), '
                                    '*custody_problems(leg, prev, job, index),',
     '            leg["custody"] = list(dict.fromkeys([*custody_problems(leg, prev, job, index),', ["custody_grade_fail"]),
    ("M108_grade_dir_reads_all", "        if path.stem not in names:", "        if False:", ["grade_dir_foreign_row"]),
    ("M109_chain_field_unchecked", '        if not isinstance(row, dict) or row.get("chain") != path.stem:',
     "        if not isinstance(row, dict):", ["grade_dir_foreign_row"]),
    ("M110_marker_files_ignored", '            if mark is not None and not leg.get("guard_killed"):', "            if False:",
     ["grade_dir_marker_on_disk"]),
    # V-03: the grader files are the import closure, and the data the grade reads
    ("M111_closure_top_level_only", "    named: set[str] = set()\n    for node in _statements(_parse(repo, path).body):",
     "    named: set[str] = set()\n    for node in _parse(repo, path).body:", ["closure_scan_planted", "closure_not_vacuous"]),
    ("M139_closure_skips_except_blocks", '        for name in ("body", "orelse", "finalbody", "handlers", "cases"):',
     '        for name in ("body", "orelse", "finalbody", "cases"):', ["closure_scan_planted"]),
    ("M112_closure_relative_unresolved", '            if node.level:\n                parts = package.split(".")',
     '            if False:\n                parts = package.split(".")', ["closure_scan_planted"]),
    ("M113_closure_no_parents", '        out.update(".".join(parts[:k]) for k in range(1, len(parts) + 1))',
     "        out.add(name)", ["closure_scan_planted"]),
    ("M114_pokemon_unhashed", '"pokedex.py", "pokemon.py", "pokemon_party.py",', '"pokedex.py", "pokemon_party.py",',
     ["grader_files_cover_closure", "changed_decoder_refused"]),
    ("M115_disk_budget_unhashed", '"check_grader_imports.py", "check_purity.py", "disk_budget.py", "grader_checks.py",',
     '"check_grader_imports.py", "check_purity.py", "grader_checks.py",',
     ["grader_files_cover_closure", "changed_decoder_refused"]),
    ("M116_symbols_unhashed", 'GRADER_DATA = ("sandbox-pokebot/modules/data/symbols/pokeemerald.sym",\n',
     "GRADER_DATA = (\n", ["grader_data_hashed", "changed_decoder_refused"]),
    # V-04: what the bounds text lists as GRADED is GRADED (and counts in the verdict)
    ("M117_purity_kind_reported", 'checks.append(_check("LC.PURITY", GRADED,', 'checks.append(_check("LC.PURITY", REPORTED,',
     ["verdict_impure_l5_fails", "graded_kinds_match_bounds"]),
    ("M118_this_run_kind_reported", 'checks.append(_check("LC.THIS_RUN", GRADED,',
     'checks.append(_check("LC.THIS_RUN", REPORTED,', ["verdict_stale_l5_fails", "graded_kinds_match_bounds"]),
    ("M119_starter_kind_reported", 'checks.append(_check("LC.STARTER", GRADED,', 'checks.append(_check("LC.STARTER", REPORTED,',
     ["verdict_wrong_starter_fails", "graded_kinds_match_bounds"]),
    ("M120_reach_kind_reported", 'checks.append(_check("LC.REACH", GRADED,', 'checks.append(_check("LC.REACH", REPORTED,',
     ["graded_kinds_match_bounds"]),
    ("M121_custody_kind_reported", 'checks.append(_check("LC.CUSTODY", GRADED,', 'checks.append(_check("LC.CUSTODY", REPORTED,',
     ["graded_kinds_match_bounds", "refused_chain_fails_custody"]),
    ("M122_memory_kind_reported", 'checks.append(_check("LC.MEMORY", GRADED,', 'checks.append(_check("LC.MEMORY", REPORTED,',
     ["graded_kinds_match_bounds"]),
    ("M123_frozen_kind_reported", 'checks.append(_check("LC.FROZEN", GRADED,', 'checks.append(_check("LC.FROZEN", REPORTED,',
     ["graded_kinds_match_bounds", "frozen_leftover"]),
    ("M124_leftover_kind_reported", 'checks.append(_check("LC.LEFTOVER", GRADED,',
     'checks.append(_check("LC.LEFTOVER", REPORTED,', ["graded_kinds_match_bounds", "frozen_leftover"]),
    # V-05: the guards no test protected
    ("M125_watchdog_formula", '    return int(sum(leg["wall"] + LEG_MARGIN_SECONDS + 2 * TRUTH_SECONDS for leg in legs) + 300)',
     '    return int(sum(leg["wall"] for leg in legs) + 300)', ["watchdog_value"]),
    ("M126_first_size_graded", '            world_file["bytes"] = max(sizes)', '            world_file["bytes"] = size_first',
     ["world_grew_larger_graded"]),
    ("M127_kept_in_profile", 'measures["world"] = stream_world_tail(world_path, keep / "world_last.jsonl")',
     'measures["world"] = stream_world_tail(world_path, run_dir / "world_last.jsonl")', ["kept_outside_repo"]),
    ("M128_overlap_first_only", 'if e["first"] <= last and first <= e["last"]]', 'if e["first"] == first]',
     ["dev_partial_overlap_refused"]),
    ("M129_leftover_unread", "    left_procs = deps.leftover()", "    left_procs = []", ["e2e_leftover_reported"]),
    ("M130_git_dirty_unread", '"dirty": [ln for ln in git("status", "--porcelain", "--untracked-files=no").splitlines() '
                              'if ln.strip()]}', '"dirty": []}', ["git_state_scratch"]),
    ("M131_abort_not_checked_before_leg",
     '                          (ABORT_FILE, "the batch was ABORTED by the harness (disk: free space)")):',
     "                          ):", ["abort_before_leg"]),
    ("M132_starter_floor_zero", "not wrong_starters, len(judged_starters), reach_min, (GAME,),",
     "not wrong_starters, len(judged_starters), 0, (GAME,),", ["starter_floor"]),
    # V-06: the prediction's sha256 is the file's bytes'
    ("M133_prediction_stripped", '            facts["prediction_sha256"] = hashlib.sha256(raw).hexdigest()',
     '            facts["prediction_sha256"] = hashlib.sha256(raw.strip()).hexdigest()',
     ["e2e_development", "prediction_sha_file_bytes"]),
    # V-08: a launch that died before playing a frame is NAMED (and still fails); a leg with no world file says so
    ("M134_dead_never_named", '    if (row.get("status") != "RAN" or not stop or stop.get("by") == "ai" or stop.get("real_frames") or '
                              'log.get("lines")\n            or not no_world_file(row)):', "    if True:",
     ["launch_died_rule", "dead_launch_named"]),
    ("M142_dead_ignores_the_log", ' or stop.get("real_frames") or log.get("lines")\n', ' or stop.get("real_frames")\n',
     ["launch_died_rule"]),
    ("M143_dead_ignores_the_world_file", "            or not no_world_file(row)):", "            or False):",
     ["launch_died_rule"]),
    ("M135_dead_row_unnamed", '        row["harness"] = launch_died(row)\n', '        row["harness"] = None\n',
     ["dead_launch_named"]),
    ("M136_no_world_file_as_undeleted",
     '                 if not no_world_file(leg) and not (leg.get("world_file") or {}).get("deleted")]',
     '                 if not (leg.get("world_file") or {}).get("deleted")]', ["world_line_no_file"]),
    ("M137_no_world_file_unsaid", '              + ("no world file" if no_world_file(leg) else',
     '              + ("no world file" if False else', ["world_line_no_file"]),
    ("M140_evidence_dead_unnamed",
     '    died_rows = [(c["chain"], leg["leg"], launch_died(leg)) for c in chains for leg in c["legs"] if launch_died(leg)]',
     "    died_rows = []", ["e2e_dead_launch_evidence"]),
    ("M141_leg_line_no_file_unsaid", '("      world.jsonl: no world file (the leg wrote none)" if no_world_file(leg) else',
     '("      world.jsonl: no world file (the leg wrote none)" if False else', ["e2e_dead_launch_evidence"]),
    # V-09: the bounds text says what LC.CUSTODY can catch
    ("M138_custody_limit_unsaid",
     '"AI_PLAYER_*): on a later leg they catch a regression of the harness only, never anything the AI does.",',
     '"AI_PLAYER_*).",', ["bounds_needles"]),
    # ------------------------------------------------------------------ the second fix round (the checker's C2-01..C2-07)
    # C2-01: a row whose identity is not the registered job's is IGNORED (its chain absent), never graded
    ("M144_identity_starter_unchecked", 'IDENTITY = ("chain", "pair", "personality", "starter", "seed", "profile")',
     'IDENTITY = ("chain", "pair", "personality", "seed", "profile")', ["row_starter_mismatch"]),
    ("M145_mismatched_row_counted", '                           f"so the chain is ABSENT")\n            continue\n',
     '                           f"so the chain is ABSENT")\n', ["row_identity_mismatch", "row_starter_mismatch"]),
    ("M181_ignored_rule_unsaid",
     'f"starter, seed or profile is not the registered job\'s are each IGNORED and named with the reason, so a registered "',
     'f"starter, seed or profile is not the registered job\'s never count, so a registered "', ["bounds_needles"]),
    # C2-02: the closure starts from the files run by path and the plugins loaded by name, through the framework's names
    # (the third fix round: live_chain's pycache_problems now IMPORTS check_purity, so closure_starts still finds it)
    ("M146_check_purity_not_a_root",
     'PATH_ROOTS = ("ai_player/gates/check_purity.py",  # host/launcher.py run_gate: L5.PURITY_GATE\n', "PATH_ROOTS = (\n",
     ["path_runs_are_roots", "bounds_needles"]),
    ("M147_pokebot_not_a_root", '              "sandbox-pokebot/pokebot.py")  # host/launcher.py bot_command',
     "              )  # host/launcher.py bot_command", ["path_runs_are_roots"]),
    ("M148_plugins_not_loaded",
     '        names = [f"plugins.{p.name[:-3]}" for p in sorted((repo / PLUGINS_DIR).iterdir()) if p.name.endswith(".py")]',
     "        names = []", ["closure_starts", "closure_starts_planted"]),
    ("M149_custom_modes_not_loaded",
     '    names += [f"plugins.custom_modes.{p.stem}" for p in sorted((repo / CUSTOM_MODES_DIR).glob("*.py"))\n'
     '              if not p.name.startswith("_")]', "    names += []", ["closure_starts", "closure_starts_planted"]),
    ("M150_private_modes_loaded", '              if not p.name.startswith("_")]', "              if True]",
     ["closure_starts_planted"]),
    ("M151_plugin_parents_unfollowed", '        for k in range(1, len(parts) + 1):\n            follow(".".join(parts[:k]))',
     "        follow(name)", ["closure_starts_planted"]),
    ("M152_framework_names_unfollowed",
     '                 ("requirements", "sandbox-pokebot/requirements"), ("updater", "sandbox-pokebot/updater"))',
     "                 )", ["closure_starts", "closure_starts_planted", "closure_toplevel_names"]),
    # (re-anchored in the fourth fix round: each source suffix, .py then .pyw, C4-H01)
    ("M153_module_files_unresolved",
     '                 *(base.parent / f"{base.name}{suffix}" for suffix in SOURCE_SUFFIXES)):', "                 ):",
     ["closure_starts", "closure_starts_planted"]),
    ("M155_framework_files_unhashed", '                *(f"sandbox-pokebot/{name}" for name in GRADER_BOT), *GRADER_DATA)',
     "                *GRADER_DATA)", ["grader_files_cover_closure", "changed_path_run_refused", "grader_data_hashed"]),
    # C2-05: every statement body an import can sit in is scanned; the closure is enforced at registration and the run
    ("M156_scan_skips_finally", '        for name in ("body", "orelse", "finalbody", "handlers", "cases"):',
     '        for name in ("body", "orelse", "handlers", "cases"):', ["closure_scan_planted"]),
    ("M157_scan_skips_orelse", '        for name in ("body", "orelse", "finalbody", "handlers", "cases"):',
     '        for name in ("body", "finalbody", "handlers", "cases"):', ["closure_scan_planted"]),
    ("M158_scan_skips_match", '        for name in ("body", "orelse", "finalbody", "handlers", "cases"):',
     '        for name in ("body", "orelse", "finalbody", "handlers"):', ["closure_scan_planted"]),
    ("M169_register_closure_unchecked", "    refusal = closure_refusal(missing)\n    if refusal is not None:",
     "    refusal = closure_refusal(missing)\n    if False:", ["closure_enforced_register"]),
    # (re-anchored in the fourth fix round: the closure refusal falls through when it is empty, C4-H05)
    ("M170_run_closure_unchecked", "    if closure:\n        return closure\n", "    if False:\n        return closure\n",
     ["closure_enforced_run"]),
    ("M171_closure_unmeasured",
     '    facts["closure_missing"], facts["closure_size"], facts["closure_seconds"] = deps.closure()',
     '    facts["closure_missing"], facts["closure_size"], facts["closure_seconds"] = [], 0, 0.0', ["closure_enforced_run"]),
    ("M172_closure_refusal_silent", "    if not missing:\n        return None\n", "    if True:\n        return None\n",
     ["closure_enforced_register", "closure_enforced_run"]),
    ("M173_closure_missing_empty", '    missing = [rel for rel in scan["closure"] if rel not in GRADER_FILES]',
     "    missing = []", ["closure_enforced_register", "closure_enforced_run"]),
    ("M182_closure_rule_unsaid", "Registration and a graded run are REFUSED (R12) while that scan finds a ",
     "Registration and a graded run may run while that scan finds a ", ["bounds_needles"]),
    # C2-03: custody, grade DIR and the in-run grade re-derive by the REGISTERED legs; the evidence prints the re-derived
    # reach; a kept line must still be a JSON object (the checker's C15b, C17, C18, C13)
    ("M159_stored_reach_printed", "                rederived = chain_reaches(row, len(legs))",
     "                rederived = stored", ["e2e_evidence_rederived_reach"]),
    ("M160_custody_called_discarded",
     '            leg["custody"] = list(dict.fromkeys([*(leg.get("custody") or []), *custody_problems(leg, prev, job, index),',
     '            leg["custody"] = list(dict.fromkeys([*(leg.get("custody") or []), '
     '*[p for p in custody_problems(leg, prev, job, index) if False],', ["regrade_custody_stored_empty"]),
    ("M161_grade_dir_without_legs", '"optional": rep.get("optional"), "most_running": source.get("most_running")}, legs=legs,',
     '"optional": rep.get("optional"), "most_running": source.get("most_running")},', ["grade_dir_registered_proof"]),
    ("M162_run_batch_without_legs",
     '"main_profile": main, "optional": optional, "most_running": plan["most_running"]}, legs=legs,',
     '"main_profile": main, "optional": optional, "most_running": plan["most_running"]},',
     ["e2e_row_proof_weakened_in_run"]),
    ("M163_kept_json_unchecked", '    return None if counts is not None else f"its kept last line is not a JSON object whose five '
                                 'counts can be read ({why})"', "    return None", ["kept_file_not_json"]),
    # C2-04: the dead launch named in LC.PURITY's and LC.THIS_RUN's lists and in the ledger verdict's own clause; the
    # rule reads the stop record; a present, unmeasured world file is no "no world file" (the checker's C64-C66, C61, C62)
    ("M164_purity_list_unnamed", '+ (f"{DEAD_LAUNCH}; " if leg.get("harness") else "") + ", ".join(wrong))',
     '+ ", ".join(wrong))', ["e2e_dead_launch_evidence"]),
    ("M165_this_run_list_unnamed",
     '    dead = {(chain.get("chain"), leg.get("leg")) for chain, leg in ran if leg.get("harness")}', "    dead = set()",
     ["e2e_dead_launch_evidence"]),
    ("M166_ledger_verdict_unnamed", "if failing and not aborted else ''}{died_text}: live chain \"",
     "if failing and not aborted else ''}: live chain \"", ["e2e_dead_launch_evidence"]),
    ("M167_dead_without_stop_record", 'or not stop or stop.get("by") == "ai" or stop.get("real_frames")',
     'or stop.get("by") == "ai" or stop.get("real_frames")', ["launch_died_rule"]),
    ("M168_no_world_ignores_present", '    return world.get("bytes") is None and not world.get("present")',
     '    return world.get("bytes") is None', ["world_line_no_file"]),
    # C2-06: a prediction that is not UTF-8 is refused, never a crash (the checker's C70)
    ("M174_prediction_not_utf8_crashes", "        except (OSError, UnicodeDecodeError) as error:",
     "        except OSError as error:", ["prediction_not_utf8_refused"]),
    # C2-07: an exception after the chains still finishes the ledger entry, named ERROR, with the evidence it can write
    ("M175_grade_error_unguarded", "        exit_code = finish_on_error(error, traceback.format_exc(), ctx)", "        raise",
     ["grade_error_finishes_entry", "evidence_error_finishes_entry"]),
    ("M176_error_entry_unfinished", '    why = finish_entry(ctx["entry_id"], verdict_line, reference, Path(ctx["ledger_path"]), '
                                    'ctx.get("sleep") or time.sleep)', '    why = "skipped"',
     ["grade_error_finishes_entry", "evidence_error_finishes_entry"]),
    ("M177_error_evidence_unwritten",
     '        evidence.write_text("\\n".join(lines) + "\\n", encoding="utf-8", errors="backslashreplace")',
     "        pass", ["grade_error_finishes_entry"]),
    ("M178_error_verdict_unnamed",
     '    return (f"ERROR (harness: {type(error).__name__}: {safe_text(error) or \'no message\'} "\n'
     '            f"{STAGES.get(stage, \'while \' + stage)}; no PASS or FAIL; the seeds are spent)")', '    return "FAIL"',
     ["grade_error_finishes_entry"]),
    ("M179_error_rule_unsaid", "\"results.json or the ledger, the ledger entry is still FINISHED, as 'ERROR (harness: <type>: "
                               "<message> while \"", "\"results.json or the ledger, the ledger entry is still finished (\"",
     ["bounds_needles"]),
    # the verifier's V02: an unread OT and an unread TID (None == None) never prove the player's own starter
    ("M180_starter_tid_unread_ok", ' \\\n        and after.get("player_tid") is not None', "", ["starter_unread_ot_and_tid"]),
    # ------------------------------------------------------------------ the third fix round (the check's C3-*, 2026-11-05)
    # C3-E01, C3-G05: --out and the job files before ledger.begin; R11 refuses an --out that cannot be made
    ("M183_out_under_a_file_ok", '                if not parent.is_dir():\n',
     "                if False:\n", ["out_listing_unmakeable"]),
    ("M184_out_missing_drive_ok",
     '        return {"out_error": "it cannot be created: no folder above it exists (a missing drive?)"}',
     '        return {"out_entries": []}', ["out_listing_unmakeable"]),
    ("M185_out_error_raw", '        raise Refusal(f"R11: --out {out} cannot be created or written',
     '        raise\n        raise Refusal(f"R11: --out {out} cannot be created or written', ["e2e_out_unmakeable_refused"]),
    ("M186_prepare_after_begin", *_prepare_after_begin(), ["e2e_out_unmakeable_refused", "e2e_steps_before_begin"]),
    ("M187_out_not_undone", "    for path in sorted(made, key=lambda p: len(p.parts), reverse=True):",
     "    for path in []:", ["e2e_out_undone_on_ledger_refusal"]),
    ("M265_job_files_after_begin", '            made += [path, path.with_name(path.name + ".tmp")]\n            _write_json(path, data)\n',
     '            made += [path]\n', ["e2e_steps_before_begin"]),
    # the chains-run guard
    ("M188_chains_unguarded",
     '    try:\n        for line in ledger_lines:\n            print(f"[LC] {line}", flush=True)\n'
     '        plan = schedule(jobs, spawn, tick, PARALLEL, stagger, deps.sleep, may_start, deps.poll_seconds)\n',
     '    for line in ledger_lines:\n        print(f"[LC] {line}", flush=True)\n'
     '    plan = schedule(jobs, spawn, tick, PARALLEL, stagger, deps.sleep, may_start, deps.poll_seconds)\n    try:\n',
     ["chains_error_finishes_entry"]),
    ("M189_children_not_killed", '            ctx["guard_notes"] = stop_children(handles, ctx.setdefault("interrupts", []))',
     '            ctx["guard_notes"] = []', ["chains_error_finishes_entry"]),
    ("M190_guard_not_base", "    except BaseException as error:  # noqa: BLE001 - (C2-07, the chains-run guard)",
     "    except Exception as error:  # noqa: BLE001 - (C2-07, the chains-run guard)",
     ["chains_interrupt_finishes_entry", "grading_interrupt"]),
    ("M191_interrupt_swallowed", "            raise  # (C3-E06) a Ctrl+C still stops the process", "            pass  #",
     ["chains_interrupt_finishes_entry", "grading_interrupt"]),
    ("M192_no_sweep_after_kill", '                ctx["guard_notes"] += end_sweep(jobs, build_root)',
     '                ctx["guard_notes"] += []', ["chains_error_finishes_entry"]),
    # C3-E02: the AI's output is untrusted (M193 restores `except ValueError` in the line parse, as the check asked)
    ("M193_world_line_value_error_only",
     "    except Exception:  # noqa: BLE001 - (C3-E02) untrusted: a deeply nested line raises RecursionError, not ValueError",
     "    except ValueError:", ["e2e_untrusted_world_fails_not_errors"]),
    # (the fourth fix round: in a leg, finish_leg's own guard (C4-E01) now also catches what world_counts lets through,
    # so this guard is told apart where nothing else catches: the grade's re-read of a kept line)
    ("M194_world_counts_value_error_only",
     "    except Exception as error:  # noqa: BLE001 - (C3-E02) the AI's output is untrusted: any failure is a failed line",
     "    except ValueError as error:", ["kept_line_wrong_shape"]),
    ("M195_world_types_unchecked", "        if wrong:\n            return None, f\"its {', '.join(wrong)} have the wrong",
     "        if False:\n            return None, f\"its {', '.join(wrong)} have the wrong", ["world_counts_untrusted"]),
    ("M196_tiles_type_unchecked", "        if isinstance(tiles, bool) or not isinstance(tiles, int):", "        if False:",
     ["world_counts_untrusted"]),
    ("M197_judged_reraises",
     "    except Exception as error:  # noqa: BLE001 - the AI's output is untrusted: a failed read is a failed check\n",
     "    except Exception as error:  # noqa: BLE001 - the AI's output is untrusted: a failed read is a failed check\n"
     "        raise\n", ["chain_bad_verdict"]),
    ("M198_memory_line_unguarded",
     '            try:\n                out["memory"] = parse_memory_line(line)\n'
     "            except Exception as error:  # noqa: BLE001 - (C3-E02) the AI's log is untrusted\n",
     '            out["memory"] = parse_memory_line(line)\n            if False:\n                error = None\n',
     ["log_untrusted"]),
    ("M199_log_read_unguarded",
     "    except Exception as error:  # noqa: BLE001 - (C3-E02) an unreadable log is a failed read of that leg, not a crash",
     "    except ZeroDivisionError as error:", ["log_untrusted"]),
    ("M200_kept_object_only", "    counts, why = world_counts(data)",
     "    counts, why = (json.loads(data) if isinstance(json.loads(data), dict) else None), 'not an object'",
     ["kept_line_wrong_shape"]),
    ("M201_records_unfiltered", 'if isinstance(r, dict) and r.get("decision") == "read"]', 'if r.get("decision") == "read"]',
     ["chain_bad_verdict"]),
    ("M202_outcome_raw", '"outcome": untrusted_text(dig(run.verdict, "facts", "exit_reason")),',
     '"outcome": ((run.verdict or {}).get("facts") or {}).get("exit_reason"),', ["chain_bad_verdict"]),
    # C3-E03: the ledger write retried, and a ledger that cannot be written said, with the command that finishes it
    ("M203_finish_not_retried", "FINISH_TRIES = 3", "FINISH_TRIES = 1", ["ledger_finish_transient_retried"]),
    ("M204_computed_failure_ignored", "        if why is not None:\n            raise LedgerUnwritten(",
     "        if False:\n            raise LedgerUnwritten(", ["ledger_finish_computed_unwritable", "ledger_unwritable_not_finished"]),
    # (the fourth fix round: the guard's write is in a loop that catches a second Ctrl+C (C4-E03), so a raw write is told
    # apart by finish_entry's own retries: error_finish_retried)
    ("M205_error_finish_unguarded",
     '    why = finish_entry(ctx["entry_id"], verdict_line, reference, Path(ctx["ledger_path"]), ctx.get("sleep") or time.sleep)',
     '    why = ledger.finish(ctx["entry_id"], verdict_line, reference, path=Path(ctx["ledger_path"]))',
     ["error_finish_retried"]),
    ("M206_not_finished_unsaid", "f\"LEDGER: entry #{ctx['entry_id']} is NOT FINISHED (it is still 'started')",
     "f\"LEDGER: entry #{ctx['entry_id']} FINISHED (it is still 'started')", ["ledger_unwritable_not_finished"]),
    ("M207_unfinished_file_unwritten", '            _write_json(ctx["out"] / UNFINISHED, {"entry_id"',
     '            (lambda *a: None)(ctx["out"] / UNFINISHED, {"entry_id"', ["ledger_unwritable_not_finished"]),
    ("M208_finish_cli_status_unchecked",
     '    if entry is None or entry.get("status") != "started" or [entry.get("first"), entry.get("last")] != data.get("seeds"):',
     "    if entry is None:", ["ledger_unwritable_not_finished"]),
    # C3-E04: the guard's breadth, the error path's own guards, a development error
    ("M209_guard_some_types", "    except BaseException as error:  # noqa: BLE001 - (C2-07, the chains-run guard)",
     "    except (RuntimeError, OSError) as error:  # noqa: BLE001 - (C2-07, the chains-run guard)",
     ["grade_error_any_exception"]),
    ("M210_error_results_unguarded",
     "    except BaseException as third:  # noqa: BLE001 - the ledger and the evidence are the record",
     "    except ZeroDivisionError as third:", ["results_write_error_both_paths"]),
    ("M211_error_evidence_oserror_only",
     "    except BaseException as second:  # noqa: BLE001 - the entry is still finished; the verdict line says the evidence "
     "is missing", "    except OSError as second:", ["error_evidence_any_exception"]),
    ("M212_dev_error_exits_0", "        note_interrupt(ctx, sixth)\n    return 4\n",
     "        note_interrupt(ctx, sixth)\n    return 4 if ctx[\"graded\"] else 0\n", ["dev_error_labelled"]),
    ("M213_dev_error_unlabelled", "{shown if graded else 'NO PASS (development: ' + shown + ')'}: live chain \"",
     "{shown}: live chain \"", ["dev_error_labelled"]),
    ("M214_r12_dev_too", '    closure = closure_refusal(facts.get("closure_missing") or []) if graded else None',
     '    closure = closure_refusal(facts.get("closure_missing") or [])', ["dev_unhashed_printed"]),
    # C3-E05: the error record beside results.json; grade DIR on an ERROR batch and its exit codes
    ("M215_error_record_over_results", 'RESULTS_ERROR = "results.error.json"', 'RESULTS_ERROR = "results.json"',
     ["ledger_finish_computed_unwritable"]),
    # (re-anchored in the fourth fix round: grade DIR's exit is its worst verdict's, C4-G01..G03, C4-E06)
    ("M216_grade_dir_exit_always_0", '    return found["exit"]', "    return 0", ["grade_dir_exit_codes"]),
    ("M217_error_batch_unsaid",
     # (the fifth fix round) re-anchored: the folder's ERROR mark is kept in `marks` first (C5-03)
     '        marks["ERROR"] = f"{RESULTS_ERROR} says {error_record.get(\'verdict\')} (stage {error_record.get(\'stage\')})"',
     "        pass", ["grade_dir_error_states"]),
    # C3-E06: exit 5, a safe repr, the named file
    ("M218_crash_not_exit_5", "    except Exception:  # noqa: BLE001 - (C3-E06) a crash is never the FAIL code",
     "    except ZeroDivisionError:", ["main_crash_exit_5"]),
    ("M219_error_text_unsafe", "{safe_text(error) or 'no message'} \"", "{str(error)[:300] or 'no message'} \"",
     ["unprintable_error"]),
    ("M220_parse_unnamed", "    return ast.parse(path.read_bytes(), filename=name)", "    return ast.parse(path.read_bytes())",
     ["closure_parse_error_named"]),
    ("M221_run_scan_error_crashes",
     "    except Exception as error:  # noqa: BLE001 - (C3-E06) a file that does not parse is named, never a crash",
     "    except ZeroDivisionError as error:", ["closure_parse_error_named"]),
    ("M222_register_scan_error_crashes",
     "    except Exception as error:  # noqa: BLE001 - (C3-E06) refused, naming the file, never a crash",
     "    except ZeroDivisionError as error:", ["closure_parse_error_named"]),
    # C3-E07: the ERROR evidence's marked lines, its single bounds text, the stage
    ("M223_unfinished_unmarked",
     '                 *([f"UNFINISHED| {line}" for line in built] or ["UNFINISHED| (nothing yet)"]), "",',
     '                 *(built or ["(nothing yet)"]), "",', ["evidence_error_finishes_entry", "evidence_write_error_bounds_once"]),
    ("M224_bounds_twice", "            if line == BOUNDS_HEADING:  # (C3-E07) the bounds text is printed ONCE, below\n",
     "            if False:\n", ["evidence_write_error_bounds_once"]),
    ("M225_stage_unnamed", '        ctx["stage"] = "evidence"', '        ctx["stage"] = "grading"',
     ["evidence_error_finishes_entry", "evidence_write_error_bounds_once"]),
    # C3-G01: each leg that ran names its registered job; no two counted legs share a run folder or a kept file
    ("M226_leg_seed_unchecked", '    if env.get(ENV_SEED) != str(job.get("seed")):', "    if False:",
     ["leg_identity_each_field", "relabelled_copy_stays_fail"]),
    ("M227_leg_personality_unchecked", '    if env.get(ENV_PERSONALITY) != job.get("personality"):', "    if False:",
     ["leg_identity_each_field"]),
    ("M228_leg_profile_unchecked", "    if profile != job.get(\"profile\"):\n        problems.append(f\"{name}'s command's",
     "    if False:\n        problems.append(f\"{name}'s command's", ["leg_identity_each_field"]),
    ("M229_leg_arm_unchecked", "    if row.get(\"arm\") != f\"{job.get('chain')}-{name}\":", "    if False:",
     ["leg_identity_each_field"]),
    ("M230_leg_run_dir_unchecked",
     '    if len(parts) < 4 or parts[-4:-1] != ["profiles", str(job.get("profile")).lower(), "ai_player_runs"]:',
     "    if False:", ["leg_identity_each_field"]),
    ("M231_leg_identity_off", "    problems: list[str] = leg_identity_problems(row, job)", "    problems: list[str] = []",
     ["leg_identity_each_field", "relabelled_copy_stays_fail"]),
    ("M232_shared_legs_off", "    shared = shared_legs(counted)", "    shared = {}", ["shared_legs_never_count"]),
    # C3-G02, C3-G04: grade DIR's numbers verified, a missing record FAILS, a moved --out, the seal (the check's G20)
    ("M233_numbers_ignored", '    if numbers is not None:\n        prefix = numbers.get("profile_prefix") or PROFILE_PREFIX',
     '    if False:\n        prefix = numbers.get("profile_prefix") or PROFILE_PREFIX', ["grade_dir_numbers_verified"]),
    ("M234_numbers_sha_unchecked", '    if sha != source.get("numbers_sha256"):', "    if False:", ["grade_dir_numbers_verified"]),
    ("M235_ledger_unchecked", '    elif entry.get("bounds_sha256") == sha:', "    elif True:", ["grade_dir_numbers_verified"]),
    ("M236_frozen_assumed", "    frozen = (tuple(frozen) if isinstance(frozen, list) and len(frozen) == 2 else",
     '    frozen = ((True, "assumed") if True else', ["grade_dir_frozen_at_seal", "grade_dir_missing_records"]),
    ("M237_leftover_missing_dropped", '        leftover = [f"the leftover-process record',
     '        leftover = [] and [f"the leftover-process record', ["grade_dir_missing_records"]),
    ("M238_moved_out_unread", "    if kept_root is not None and chain:", "    if False:", ["grade_dir_moved_out"]),
    # C3-G03: each of the six identity fields (the check's G01-G03 survived)
    ("M239_identity_no_profile", 'IDENTITY = ("chain", "pair", "personality", "starter", "seed", "profile")',
     'IDENTITY = ("chain", "pair", "personality", "starter", "seed")', ["row_identity_each_field"]),
    ("M240_identity_no_personality", 'IDENTITY = ("chain", "pair", "personality", "starter", "seed", "profile")',
     'IDENTITY = ("chain", "pair", "starter", "seed", "profile")', ["row_identity_each_field"]),
    ("M241_identity_no_pair", 'IDENTITY = ("chain", "pair", "personality", "starter", "seed", "profile")',
     'IDENTITY = ("chain", "personality", "starter", "seed", "profile")', ["row_identity_each_field"]),
    # C3-G06: a NOT RUN after a continuing leg, unexplained, fails custody (and an explained one does not)
    ("M242_hidden_leg_allowed",
     '    custody_bad += [problem for chain in chains for problem in chain.get("custody_chain") or []]',
     "    custody_bad += []", ["not_run_after_continuing_leg"]),
    ("M243_hidden_leg_unseen",
     '              and not stops and not (by_salvage and str(leg.get("reason") or "").startswith(SALVAGE_REASON))):',
     "              and False):", ["not_run_after_continuing_leg"]),
    ("M244_stop_file_ignored",
     '              and not stops and not (by_salvage and str(leg.get("reason") or "").startswith(SALVAGE_REASON))):',
     '              and not (by_salvage and str(leg.get("reason") or "").startswith(SALVAGE_REASON))):',
     ["not_run_after_continuing_leg"]),
    # C3-H01: CPython's resolution order, files beside a closure module, a __pycache__ file loaded instead
    ("M245_closure_old_order",
     '    for path in (*(base / f"__init__{suffix}" for suffix in SOURCE_SUFFIXES),\n'
     '                 *(base.parent / f"{base.name}{suffix}" for suffix in SOURCE_SUFFIXES)):',
     '    for path in (*(base.parent / f"{base.name}{suffix}" for suffix in SOURCE_SUFFIXES),\n'
     '                 *(base / f"__init__{suffix}" for suffix in SOURCE_SUFFIXES)):', ["closure_resolution_planted"]),
    ("M246_resolution_unrefused",
     '    problems = [*resolution_problems(repo, scan["modules"]), *pycache_problems(repo, scan["paths"]),',
     '    problems = [*pycache_problems(repo, scan["paths"]),', ["resolution_enforced_register"]),
    ("M247_resolution_blind", "    cache: dict = {}\n    problems: list[str] = []\n\n    def rel(",
     "    return []\n    cache: dict = {}\n    problems: list[str] = []\n\n    def rel(", ["closure_resolution_planted"]),
    ("M248_pycache_unrefused",
     '    problems = [*resolution_problems(repo, scan["modules"]), *pycache_problems(repo, scan["paths"]),',
     '    problems = [*resolution_problems(repo, scan["modules"]),', ["pycache_planted"]),
    ("M249_pycache_blind", "            if problem:\n                problems.append(f\"{(cache / name)",
     "            if False:\n                problems.append(f\"{(cache / name)", ["pycache_planted"]),
    ("M250_bytecode_beside_ok", '(low == stem + ".pyc" or low.endswith(EXTENSION_SUFFIXES))',
     "low.endswith(EXTENSION_SUFFIXES)", ["closure_resolution_planted"]),
    ("M251_extension_beside_ok", '(low == stem + ".pyc" or low.endswith(EXTENSION_SUFFIXES))', '(low == stem + ".pyc")',
     ["closure_resolution_planted"]),
    # C3-H02: the script folders' shadows, PYTHONPATH and friends
    ("M252_toplevel_unrefused", '                *toplevel_problems(repo, scan["tops"]), *ai_problems(repo)]',
     "                *ai_problems(repo)]", ["toplevel_planted"]),
    # (the fourth fix round: since C4-H03 the installed names include the standard library's folder, so only a stdlib name
    # this platform does not install tells this rule apart: toplevel_installed_planted's pwd)
    ("M253_stdlib_unchecked", "            elif low in stdlib:", "            elif False:", ["toplevel_installed_planted"]),
    ("M254_namespace_flagged",
     '            if kind == "folder" and low in stdlib:  # a namespace folder never replaces a regular (library) module\n',
     "            if False:\n", ["toplevel_planted"]),
    ("M255_python_env_unrefused", '    if graded and facts.get("python_env"):', "    if False:", ["python_env_refused"]),
    ("M256_child_env_unfiltered", "    return {k: v for k, v in os.environ.items() if not python_env_refused(k)}",
     "    return dict(os.environ)", ["python_env_refused"]),
    ("M257_child_keeps_env", "        os.environ.pop(name, None)", "        pass", ["python_env_refused"]),
    # C3-H03: the production Deps defaults (the check's H10, H11 survived)
    ("M259_deps_closure_noop", "    closure: Callable[[], tuple[list[str], int, float]] = closure_missing",
     "    closure: Callable[[], tuple[list[str], int, float]] = lambda: ([], 0, 0.0)", ["wiring_defaults"]),
    ("M260_deps_git_clean", "    git_state: Callable[[], dict] = git_state",
     '    git_state: Callable[[], dict] = lambda: {"head": "a", "origin": "a", "dirty": []}', ["wiring_defaults"]),
    ("M261_deps_spawn_noop", "    spawn: Callable = spawn_child", "    spawn: Callable = lambda *a: None", ["wiring_defaults"]),
    # C3-H04: every file named; C3-H05: the AI's framework imports start the closure
    ("M262_refusal_first_12", "does not hash: {missing}: list an ", "does not hash: {missing[:12]}: list an ",
     ["closure_refusal_names_all"]),
    ("M263_ai_starts_off", "    for name in sorted(ai_framework_imports(repo)):", "    for name in []:",
     ["closure_ai_starts_planted", "closure_scan_planted"]),
    ("M264_ai_starts_from_evidence", '        if rel.parts[0] in ("gates", "evidence") or "__pycache__" in rel.parts:\n'
                                     "            continue\n        for node in _statements",
     '        if "__pycache__" in rel.parts:\n            continue\n        for node in _statements',
     ["closure_ai_starts_planted"]),
    # (the third fix round's finish, 2026-11-06) the full regression lane: sandbox-pokebot/mgba is exempt by name, and
    # only in sandbox-pokebot
    ("M266_mgba_exemption_dropped", '    ("sandbox-pokebot", "mgba"):\n', '    ("sandbox-pokebot", "mgba_dropped"):\n',
     ["toplevel_mgba_exempt", "toplevel_planted"]),
    ("M267_exemption_any_folder", "or (is_dir and (rel, low) in exempt):",
     "or (is_dir and low in {name for _, name in exempt}):", ["toplevel_mgba_exempt"]),
    ("M268_exemption_unsaid",
     '"the git-ignored folders mgba and profiles, which are not hashed: see below), and any .py, .pyw, .pyc, extension "',
     '"nothing more), and any .py, .pyw, .pyc, extension "', ["bounds_needles"]),
    # ------------------------------------------------------------------ the fourth fix round (the check's C4-*, 2026-11-06)
    # C4-E01: the AI's world.jsonl of the wrong KIND, or one the OS refuses to open, is a failed check, never the harness's
    ("M269_world_read_unguarded",
     "                except Exception as error:  # noqa: BLE001 - (C4-E01) the AI's file: a failed read is a failed check",
     "                except ZeroDivisionError as error:", ["world_kind_untrusted"]),
    ("M270_world_kind_unchecked",
     "        if os.path.isfile(world_path):  # (C4-E01) os.path never raises; a folder named world.jsonl is no world file",
     "        if os.path.lexists(world_path):", ["world_kind_untrusted"]),
    ("M271_copy_unguarded",
     "                except Exception as error:  # noqa: BLE001 - (C4-E01) a copy is a record, never the grade's input",
     "                except ZeroDivisionError as error:", ["world_kind_untrusted"]),
    # C4-E02: --out claimed exclusively; once claimed it holds the claim only; a refused launch removes only its own
    ("M273_out_claim_not_exclusive", "            handle = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)",
     "            handle = os.open(claim, os.O_CREAT | os.O_WRONLY)", ["out_second_launch_refused"]),
    ("M274_out_emptiness_unchecked", "        if others:\n            raise OutTaken(", "        if False:\n            raise OutTaken(",
     ["out_written_after_listing"]),
    ("M275_out_taken_not_undone", "    except OutTaken as error:\n        undo_out(made)\n",
     "    except OutTaken as error:\n        pass\n", ["out_written_after_listing"]),
    # C4-E07 (the check's N01, N02, N05): what prepare_out made, removed on every failure
    ("M276_out_parents_not_undone",
     "        made += sorted((p for p in (out, *out.parents) if not p.exists()), key=lambda p: len(p.parts))\n",
     "        pass\n", ["out_undo_edges"]),
    ("M277_prepare_failure_not_undone",
     "    except Exception as error:  # noqa: BLE001 - any failure to make or write --out is R11's, before the ledger\n"
     "        undo_out(made)\n",
     "    except Exception as error:  # noqa: BLE001 - any failure to make or write --out is R11's, before the ledger\n"
     "        pass\n", ["out_undo_edges"]),
    ("M278_begin_raise_not_undone",
     "        undo_out(made)  # (ledger.begin writes the ledger last and atomically: on a raise the entry was not begun)\n",
     "        pass\n", ["out_undo_edges"]),
    # C4-E03: a second Ctrl+C while the guard finishes (the check's N03 among them)
    ("M279_sigint_not_ignored", "        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)",
     "        previous = signal.getsignal(signal.SIGINT)", ["guard_second_interrupt", "guard_sigint_restored"]),
    # (the fifth check's C5-04) guard_sigint_restored installs a fresh sentinel first, so this is caught in any test order
    ("M280_sigint_not_restored",
     "            signal.signal(signal.SIGINT, previous if previous is not None else signal.default_int_handler)",
     "            pass", ["guard_second_interrupt", "guard_sigint_restored"]),
    ("M281_guard_line_unprinted", '        print(f"[LC] the harness stopped ({type(error).__name__}',
     '        (lambda *a, **k: None)(f"[LC] the harness stopped ({type(error).__name__}', ["guard_second_interrupt"]),
    ("M282_sweep_interrupt_escapes",
     "                except BaseException as sweep:  # noqa: BLE001 - (C4-E03) a sweep that raises never leaves 'started'",
     "                except Exception as sweep:  # noqa: BLE001", ["guard_second_interrupt"]),
    ("M283_sweep_error_escapes",
     "                except BaseException as sweep:  # noqa: BLE001 - (C4-E03) a sweep that raises never leaves 'started'",
     "                except ZeroDivisionError as sweep:  # noqa: BLE001", ["guard_second_interrupt"]),
    ("M284_finish_interrupt_escapes", "        except BaseException as late:  # noqa: BLE001\n            note_interrupt(ctx, late)",
     "        except ZeroDivisionError as late:  # noqa: BLE001\n            note_interrupt(ctx, late)", ["guard_second_interrupt"]),
    ("M285_kill_interrupt_escapes",
     "        except BaseException as error:  # noqa: BLE001 - (C4-E03) a second Ctrl+C never stops the guard",
     "        except Exception as error:  # noqa: BLE001 - (C4-E03) a second Ctrl+C never stops the guard",
     ["guard_second_interrupt"]),
    ("M286_interrupt_swallowed", '        if ctx.get("interrupts"):\n            raise KeyboardInterrupt(',
     "        if False:\n            raise KeyboardInterrupt(", ["guard_second_interrupt"]),
    ("M287_finished_entry_overwritten",
     '    if ctx.get("finished") or entry_status(ctx["entry_id"], Path(ctx["ledger_path"])) == "done":', "    if False:",
     ["guard_after_finish_keeps_verdict"]),
    # C4-E04: text that cannot be written as UTF-8 is escaped before any write
    ("M288_untrusted_text_raw",
     "    return None if value is None else utf8_safe(value) if isinstance(value, str) else safe_text(value, 200)",
     "    return value if value is None or isinstance(value, str) else safe_text(value, 200)", ["lone_surrogate_graded"]),
    ("M289_write_json_raw", "    text = json.dumps(utf8_safe(data), ensure_ascii=False", "    text = json.dumps(data, ensure_ascii=False",
     ["lone_surrogate_graded"]),
    # C4-E05: finish-entry writes only this driver's own ERROR verdict, rebuilt from results.error.json
    ("M290_finish_any_verdict", "    problems = unfinished_problems(data, record, entry, where)\n    if problems:",
     "    problems = []\n    if problems:", ["finish_entry_only_error", "finish_entry_without_error_record"]),
    ("M291_error_form_unchecked", "    if not ERROR_FORM.fullmatch(shown):", "    if False:", ["finish_entry_only_error"]),
    ("M292_rebuilt_unchecked", '    if not (verdict == rebuilt or verdict.startswith(rebuilt + "; no evidence file (")):',
     "    if False:", ["finish_entry_only_error"]),
    ("M293_record_unchecked", "        if record.get(key) != want:", "        if False:", ["finish_entry_only_error"]),
    # C4-G01..G03, C4-E06: grade DIR reads the ledger entry NOW and never reports better than it
    ("M294_ledger_fail_ignored", '    if word in ("PASS", "FAIL"):\n        candidates.append(word)',
     "    if False:\n        candidates.append(word)", ["grade_dir_never_better_than_ledger"]),
    ("M295_ledger_error_ignored", '    elif word in ("ERROR", "ABORTED"):', "    elif False:",
     ["grade_dir_error_states", "grade_dir_aborted_and_development"]),
    ("M296_ledger_started_ignored", '    if word == "STARTED":', "    if False:", ["grade_dir_error_states"]),
    ("M297_graded_unverified_passes", '(purpose == "graded" and not is_verified)', "(False)",
     ["grade_dir_never_better_than_ledger"]),
    ("M298_abort_file_ignored",
     '    if (out / ABORT_FILE).is_file() or str(source.get("verdict") or "").startswith("ABORTED"):', "    if False:",
     ["grade_dir_planted_stop_and_deleted_leg"]),
    ("M299_purpose_always_graded", '    purpose = (entry or {}).get("purpose") or source.get("purpose") or "graded"',
     '    purpose = "graded"', ["grade_dir_aborted_and_development"]),
    ("M300_entry_by_id_only",
     '    for match in (lambda e: e.get("id") == entry_id and e.get("bounds_sha256") == sha,\n'
     '                  lambda e: e.get("bounds_sha256") == sha and e.get("status") != "registered",\n'
     '                  lambda e: e.get("bounds_sha256") == sha, lambda e: e.get("id") == entry_id,\n'
     '                  lambda e: e.get("status") != "registered", lambda e: True):',
     '    for match in (lambda e: e.get("id") == entry_id,):', ["grade_dir_never_better_than_ledger"]),
    ("M301_numbers_jobs_unchecked", "    problems += numbers_jobs_problems(numbers)", "    problems += []",
     ["grade_dir_never_better_than_ledger"]),
    # C4-G02: a stop file beside a clean frozen record, a row whose legs are not the registered ones
    ("M302_stop_beside_frozen_ok", "    if frozen is not None and frozen[0] and STOP_FILE in stop_files:", "    if False:",
     ["grade_dir_planted_stop_and_deleted_leg"]),
    ("M303_row_legs_unchecked", '        if have != want or len(have) != len(out.get("legs") or []):', "        if False:",
     ["grade_dir_planted_stop_and_deleted_leg"]),
    # C4-G04: the salvage exemption reads the orchestrator's own events
    ("M304_salvage_text_trusted", '    by_salvage = job["chain"] in set(salvaged)', "    by_salvage = True",
     ["salvage_exemption_needs_record", "not_run_after_continuing_leg"]),
    ("M305_in_run_salvage_unrecorded", "                             stop_files=stop_files, salvaged=salvaged)",
     "                             stop_files=stop_files, salvaged=())", ["salvage_exemption_needs_record"]),
    ("M306_regrade_salvage_unread", '    salvaged = salvaged_chains(source.get("events"))', "    salvaged = []",
     ["salvage_exemption_needs_record"]),
    # C4-G05: the check's surviving C05, C06, C08 and C03, pinned
    ("M307_rule_after_any_ran", 'prev.get("status") == "RAN" and prev.get("continue")\n', 'prev.get("status") == "RAN"\n',
     ["reach_5_of_6_pass"]),
    ("M308_abort_does_not_explain", "              and not stops and not", "              and STOP_FILE not in stops and not",
     ["not_run_after_continuing_leg", "grade_dir_aborted_and_development"]),
    ("M309_regrade_stop_files_dropped",
     "stop_files=[name for name in (STOP_FILE, ABORT_FILE) if (out / name).is_file()], kept_root=out,\n",
     "stop_files=[], kept_root=out,\n", ["grade_dir_aborted_and_development"]),
    ("M310_run_dir_any_profile_folder",
     '    if len(parts) < 4 or parts[-4:-1] != ["profiles", str(job.get("profile")).lower(), "ai_player_runs"]:',
     '    if len(parts) < 4 or parts[-3] != str(job.get("profile")).lower():', ["leg_identity_each_field"]),
    # C4-H01: a .pyw, the exact homes
    ("M311_closure_pyw_skipped", '                 *(base.parent / f"{base.name}{suffix}" for suffix in SOURCE_SUFFIXES)):',
     '                 *(base.parent / f"{base.name}{suffix}" for suffix in (".py",))):', ["closure_pyw_planted"]),
    ("M312_closure_init_pyw_skipped", '    for path in (*(base / f"__init__{suffix}" for suffix in SOURCE_SUFFIXES),',
     '    for path in (*(base / f"__init__{suffix}" for suffix in (".py",)),', ["closure_pyw_planted"]),
    ("M313_homes_any_kind",
     "            if (rel, entry.name.lower(), is_dir) in homes or (is_dir and (rel, low) in exempt):",
     '            if (rel, low) in {(r, n.split(".")[0]) for r, n, _ in homes} or (is_dir and (rel, low) in exempt):',
     ["closure_pyw_planted", "toplevel_branches_planted"]),
    ("M314_homes_any_folder",
     "            if (rel, entry.name.lower(), is_dir) in homes or (is_dir and (rel, low) in exempt):",
     '            if low in {n.split(".")[0] for _, n, _ in homes} or (is_dir and (rel, low) in exempt):',
     ["toplevel_branches_planted"]),
    ("M315_exempt_any_kind", "or (is_dir and (rel, low) in exempt):", "or ((rel, low) in exempt):",
     ["toplevel_branches_planted"]),
    ("M316_profiles_exempt_anywhere", "or (is_dir and (rel, low) in exempt):",
     'or (is_dir and (rel, low) in exempt) or low == "profiles":', ["toplevel_branches_planted"]),
    # C4-H02: every PYTHON* variable but the allow-list; names compared without case
    ("M317_python_env_old_three", '    return upper.startswith("PYTHON") and upper not in PYTHON_ENV_ALLOWED',
     '    return upper in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")', ["python_env_refused"]),
    ("M318_python_env_allowlist_ignored", '    return upper.startswith("PYTHON") and upper not in PYTHON_ENV_ALLOWED',
     '    return upper.startswith("PYTHON")', ["python_env_refused"]),
    ("M319_names_with_case", "            low, is_dir = name.lower(), entry.is_dir()", "            low, is_dir = name, entry.is_dir()",
     ["toplevel_installed_planted"]),
    # C4-H03: the names installed outside the repository
    ("M320_installed_ignored",
     '            elif low in installed and (kind != "folder" or installed[low] == "folder"):', "            elif False:",
     ["toplevel_installed_planted"]),
    ("M321_installed_namespace_flagged",
     '            elif low in installed and (kind != "folder" or installed[low] == "folder"):',
     "            elif low in installed:", ["toplevel_installed_planted"]),
    # C4-H04, C4-H06: the AI's caches and bytecode, Python code under evidence/
    ("M322_ai_problems_off", '                *toplevel_problems(repo, scan["tops"]), *ai_problems(repo)]',
     '                *toplevel_problems(repo, scan["tops"])]', ["ai_problems_planted"]),
    ("M323_evidence_code_ok",
     '                if low.endswith((*SOURCE_SUFFIXES, ".pyc")) or low.endswith(EXTENSION_SUFFIXES):', "                if False:",
     ["ai_problems_planted"]),
    ("M324_ai_bytecode_ok", '            elif low.endswith(".pyc"):\n                problems.append(f"{rel}: bytecode of the AI',
     '            elif False:\n                problems.append(f"{rel}: bytecode of the AI', ["ai_problems_planted"]),
    ("M325_ai_caches_unjudged", "    return problems + pycache_problems(repo, sources)", "    return problems",
     ["ai_problems_planted"]),
    # C4-H05: an empty closure check never skips the checks after it
    ("M326_closure_none_skips_rest", "    if closure:\n        return closure\n", "    if graded:\n        return closure\n",
     ["run_refusal_falls_through", "r9"]),
    # C4-H07: the check's twelve surviving branches, pinned (R03, R04, R06, R07, T03, T04, T06, T07, A02, A03; its T08
    # and T10 are M314 and M316 on the exact homes)
    ("M327_sourceless_init_ok", 'for n in inits if not n.lower().endswith(".py")]', "for n in inits if False]",
     ["resolution_branches_planted"]),
    ("M328_opaque_with_case", "    stem = stem.lower()\n    found = []", "    found = []", ["resolution_branches_planted"]),
    ("M329_cache_name_case", '            source = sources.get(match["stem"].lower()) if match else None',
     '            source = sources.get(match["stem"]) if match else None', ["pycache_branches_planted"]),
    ("M330_cache_opt_ignored", 'problem = _pyc_problem(cache / name, source, int(match["opt"] or 0))',
     "problem = _pyc_problem(cache / name, source, 0)", ["pycache_branches_planted"]),
    ("M331_pyw_not_module", '    for suffix in (*SOURCE_SUFFIXES, ".pyc"):', '    for suffix in (".py", ".pyc"):',
     ["toplevel_branches_planted"]),
    ("M332_pyc_not_module", '    for suffix in (*SOURCE_SUFFIXES, ".pyc"):', "    for suffix in SOURCE_SUFFIXES:",
     ["toplevel_branches_planted"]),
    ("M333_package_as_folder", '        return ("package" if inits else "folder"), name', '        return "folder", name',
     ["toplevel_branches_planted"]),
    ("M334_private_names_skipped",
     'if kind is None or not name.isidentifier() or (name.startswith("__") and name.endswith("__")):',
     'if kind is None or not name.isidentifier() or name.startswith("_"):', ["toplevel_branches_planted"]),
    ("M335_ai_from_names_off",
     '                found = [node.module, *(f"{node.module}.{alias.name}" for alias in node.names if alias.name != "*")]',
     "                found = [node.module]", ["ai_starts_branches_planted"]),
    ("M336_ai_pyw_off", '    for path in sorted([*root.rglob("*.py"), *root.rglob("*.pyw")]):',
     '    for path in sorted(root.rglob("*.py")):', ["ai_starts_branches_planted"]),
    # C4-H08: the production wiring (the check's W01, W02, W04-W07) and the rest of Deps
    ("M337_watch_nothing", "    return watch(REPO, explicit=True)", '    return watch(REPO / "zz_nothing_here", explicit=True)',
     ["wiring_bodies"]),
    ("M338_deps_kill_noop", "    kill: Callable[[int], list] = kill_descendants", "    kill: Callable[[int], list] = lambda pid: []",
     ["wiring_defaults"]),
    ("M339_leftover_never_matches", "f\"-like '*{prefix}*' }}", "f\"-like '*{prefix}zz_never*' }}", ["wiring_bodies"]),
    ("M340_free_always_plenty", "        return free_gb(path)", "        return 999.0", ["wiring_bodies"]),
    ("M341_g3_scans_nothing", '    return scan(REPO, ("ai_player.gates.live_chain",))', "    return scan(REPO, ())",
     ["wiring_bodies"]),
    ("M342_deps_snapshot_none", "    snapshot: Callable[[], object] = snapshot", "    snapshot: Callable[[], object] = lambda: None",
     ["wiring_defaults"]),
    ("M343_deps_watch_other", "    watch: Callable[[], object] = watch_tree", "    watch: Callable[[], object] = lambda: None",
     ["wiring_defaults"]),
    ("M344_deps_code_line_other", "    code_line: Callable[[], str] = code_line", '    code_line: Callable[[], str] = lambda: "x"',
     ["wiring_defaults"]),
    # (the fifth fix round, 2026-11-06) C5-01: the folder's own jobs against its seeds, the entry its recorded id names
    ("M345_own_jobs_unchecked", '        if own:\n            return None, own, f"MISMATCH (no numbers)',
     '        if False:\n            return None, own, f"MISMATCH (no numbers)', ["grade_dir_edited_fail_folder"]),
    ("M346_recorded_entry_unread", "    if recorded:  # (the fifth check's C5-01)", "    if False:  # (the fifth check's C5-01)",
     ["grade_dir_edited_fail_folder"]),
    ("M347_recorded_seeds_unchecked", '    if [named.get("first"), named.get("last")] != list(seeds):', "    if False:",
     ["recorded_entry_rules"]),
    ("M348_recorded_purpose_unchecked", '    if named.get("purpose") != source.get("purpose"):', "    if False:",
     ["recorded_entry_rules", "grade_dir_edited_fail_folder"]),
    ("M349_recorded_any_driver", '    if named is None or named.get("driver") != DRIVER:', "    if named is None:",
     ["recorded_entry_rules"]),
    ("M350_renumbered_not_exempt",
     '    if ledger_path is None or (entry is not None and entry.get("id") != entry_id and entry.get("bounds_sha256") == sha):',
     "    if ledger_path is None:", ["recorded_entry_rules"]),
    ("M351_renumbered_without_sha", 'entry.get("id") != entry_id and entry.get("bounds_sha256") == sha):',
     'entry.get("id") != entry_id):', ["recorded_entry_rules"]),
    # C5-02: finish-entry rebuilds from ledger.unfinished.json's copy when results.error.json could not be written
    ("M352_unfinished_copy_unread", '    if record is None and isinstance(data.get("error_record"), dict):', "    if False:",
     ["finish_entry_without_error_record"]),
    ("M353_unfinished_copy_unwritten", '"error_record": {key: record[key] for key in REBUILD_KEYS}})', '"error_record": None})',
     ["finish_entry_without_error_record"]),
    # C5-03: a folder mark beside a finished PASS or FAIL is a contradiction, graded FAIL
    ("M354_contradiction_never", 'if word in ("PASS", "FAIL") and marks else "")', 'if False else "")',
     ["grade_dir_contradiction", "grade_dir_planted_stop_and_deleted_leg"]),
    ("M355_contradiction_passes", '    if contradiction:\n        candidates.append("FAIL")',
     '    if False:\n        candidates.append("FAIL")', ["grade_dir_contradiction", "grade_dir_planted_stop_and_deleted_leg"]),
    ("M356_contradicted_error_reported", '    if "ERROR" in marks and not contradiction:', '    if "ERROR" in marks:',
     ["grade_dir_contradiction"]),
    ("M357_contradicted_abort_reported", '    if "ABORTED" in marks and not contradiction:', '    if "ABORTED" in marks:',
     ["grade_dir_contradiction"]),
    # C5-05: an entry never begun, or with a verdict this driver never writes, never gives PASS (M358 is check 5's MY02)
    ("M358_registered_entry_passes",
     '    if final == "PASS" and (word in ("REGISTERED", "UNREADABLE") or (purpose == "graded" and not is_verified)):',
     '    if final == "PASS" and (word in () or (purpose == "graded" and not is_verified)):',
     ["grade_dir_entry_unbegun_or_unreadable"]),
    ("M359_unreadable_entry_passes", 'word in ("REGISTERED", "UNREADABLE") or', 'word in ("REGISTERED",) or',
     ["grade_dir_entry_unbegun_or_unreadable"]),
    # (the sixth fix round, 2026-11-06) C6-01: the entry looked up by the seeds the rows bind, the seed rules type-strict
    ("M360_lookup_by_recorded_seeds",
     '    seeds = bound or seed_pair((raw.get("seeds") if isinstance(raw, dict) else None) or source.get("seeds")) or []',
     '    seeds = list((raw.get("seeds") if isinstance(raw, dict) else None) or source.get("seeds") or [])',
     ["grade_dir_edited_fail_folder"]),
    ("M361_seed_pair_coerced", "    pair = [seed for seed in value if type(seed) is int]", "    pair = [int(seed) for seed in value]",
     ["grade_dir_edited_fail_folder", "seed_rules"]),
    ("M362_job_seeds_coerced", "    strict = [seed for seed in seeds if type(seed) is int]",
     "    strict = [int(seed) for seed in seeds]", ["seed_rules"]),
    ("M363_jobs_not_contiguous", "    if sorted(strict) != list(range(min(strict), max(strict) + 1)):", "    if False:",
     ["seed_rules"]),
    ("M364_batch_seeds_by_value",
     '    if seed_pair(source.get("seeds")) is None or source.get("seeds") != seeds:  # (C6-01)',
     '    if source.get("seeds") != seeds:  # (C6-01)', ["grade_dir_edited_fail_folder"]),
    ("M365_seeds_type_unchecked", "    if given is None:\n        problems.append(", "    if False:\n        problems.append(",
     ["grade_dir_edited_fail_folder", "seed_rules"]),
    # C6-02: a live_chain entry whose seeds never meet the folder's is another batch's, no MISMATCH
    ("M366_other_batch_mismatched",
     "    if len(seeds) == 2 and type(first) is int and type(last) is int and (last < seeds[0] or first > seeds[1]):",
     "    if False:", ["grade_dir_other_live_chain_entry", "recorded_entry_rules"]),
    ("M367_every_batch_ignored",
     "    if len(seeds) == 2 and type(first) is int and type(last) is int and (last < seeds[0] or first > seeds[1]):",
     "    if True:", ["recorded_entry_rules", "grade_dir_edited_fail_folder"]),
    ("M368_touching_low_ignored", "(last < seeds[0] or first > seeds[1])", "(last <= seeds[0] or first > seeds[1])",
     ["recorded_entry_rules"]),
    ("M369_touching_high_ignored", "(last < seeds[0] or first > seeds[1])", "(last < seeds[0] or first >= seeds[1])",
     ["recorded_entry_rules"]),
    # C6-03: the renumbered-ledger exemption cut at regrade_dir's call site (check 6's MZ2)
    ("M370_recorded_without_entry", "recorded = recorded_problems(ledger_path, source, seeds, sha, entry, ",
     "recorded = recorded_problems(ledger_path, source, seeds, sha, None, ", ["grade_dir_other_live_chain_entry"]),
    # C6-04: a contradiction said for an honest ERROR, ABORTED or STARTED batch (check 6's MZ1); the verdict line's
    # reason unsaid (its MZ3)
    ("M371_contradiction_any_word", 'if word in ("PASS", "FAIL") and marks else "")',
     'if word in ("PASS", "FAIL", "ERROR", "ABORTED", "STARTED") and marks else "")',
     ["grade_dir_error_states", "grade_dir_aborted_and_development"]),
    ("M372_contradiction_reason_unsaid",
     'why_not = "the folder contradicts its finished ledger entry" if contradiction else ""', 'why_not = ""',
     ["grade_dir_contradiction"]),
]


def case_r3_run_given(M, tmp):
    ok((M.run_refusal(dev_args(run="ch5"), facts_of(False)) or "").startswith("R3"), "a development batch naming --run")


RefusalTests.test_r3_run_given = lambda self: self.case(case_r3_run_given)


def load_module(tmp: Path, name: str, anchor: str | None, replacement: str | None):
    """`live_chain.py` (with `anchor` replaced exactly once) loaded from a temp `ai_player/gates/live_chain.py`, its REPO,
    GATES and EVIDENCE_DIR rebound to this tree's (critic CH-05). RAISES RuntimeError when the anchor is not unique."""
    text = SOURCE.read_text(encoding="utf-8")
    if anchor is not None:
        count = text.count(anchor)
        if count != 1:
            raise RuntimeError(f"mutant {name}: anchor found {count} times: {anchor!r}")
        text = text.replace(anchor, replacement)
    path = tmp / name / "ai_player" / "gates" / "live_chain.py"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"live_chain_mut_{name}", path)
    module = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    sys.modules[spec.name] = module  # dataclasses read the module's namespace while the class is made
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved
        sys.modules.pop(spec.name, None)
    module.REPO, module.GATES, module.EVIDENCE_DIR = REPO, GATES, REPO / "ai_player" / "evidence"
    return module


def run_case(module, case: str, tmp: Path) -> str:
    """'PASS', 'FAIL' (an AssertionError) or 'BROKEN: <error>' (anything else)."""
    saved = L5.PROFILE
    folder = Path(tempfile.mkdtemp(prefix=f"{case[:20]}_", dir=tmp))
    try:
        globals()[f"case_{case}"](module, folder)
        return "PASS"
    except AssertionError:
        return "FAIL"
    except Exception as error:  # noqa: BLE001
        return f"BROKEN: {type(error).__name__}: {error}"
    finally:
        L5.PROFILE = saved


class MutantTests(unittest.TestCase):
    """Each mutant breaks ONE guard of live_chain.py; every case it names must FAIL (an AssertionError) on it. M0, the
    unmutated source loaded the same way, passes every case any mutant names."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mut_", dir=_TEMP_ROOT))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_M00_control_the_unmutated_copy_passes_every_named_case(self) -> None:
        module = load_module(self.tmp, "M00", None, None)
        names = sorted({case for _, _, _, cases in MUTANTS for case in cases})
        results = {case: run_case(module, case, self.tmp) for case in names}
        self.assertEqual({k: v for k, v in results.items() if v != "PASS"}, {})

    def test_every_case_a_mutant_names_exists(self) -> None:
        for name, _, _, cases in MUTANTS:
            for case in cases:
                self.assertIn(f"case_{case}", globals(), f"{name} names {case}")

    def test_mutant_ids_are_unique(self) -> None:
        names = [m[0] for m in MUTANTS]
        self.assertEqual(len(names), len(set(names)))


def _mutant_test(name: str, anchor: str, replacement: str, cases: list[str]):
    def test(self: MutantTests) -> None:
        module = load_module(self.tmp, name, anchor, replacement)
        results = {case: run_case(module, case, self.tmp) for case in cases}
        broken = {k: v for k, v in results.items() if v.startswith("BROKEN")}
        self.assertEqual(broken, {}, f"{name}: a broken copy, not a caught mutant")
        survived = [case for case, status in results.items() if status != "FAIL"]
        self.assertEqual(survived, [], f"{name} SURVIVED {survived}: these cases passed on the mutated driver")
    return test


for _name, _anchor, _replacement, _cases in MUTANTS:
    setattr(MutantTests, f"test_{_name}", _mutant_test(_name, _anchor, _replacement, _cases))


if __name__ == "__main__":
    unittest.main()
