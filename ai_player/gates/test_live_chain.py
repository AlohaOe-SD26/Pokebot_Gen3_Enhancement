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
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import shutil
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
    write_stop, raise, die, wrong_species, wrong_ot."""

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
            (run.run_dir / "world.jsonl").write_bytes(body.encode("utf-8"))
            self.last_lines[arm.name] = (lines[2] + "\n").encode("utf-8")
        if plan.get("write_stop"):
            (Path(self.job["out"]) / "STOP.txt").write_text("moved\n", encoding="utf-8")
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
    return M.grade_batch(chains, jobs, 5, reach_min, frozen, list(leftover), {"most_running": 3})


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
JOB_S = {"chain": "LC-S-1", "starter": "TREECKO"}


def l1_row(**changes) -> dict:
    row = {"leg": "L1", "command": ["py", "run", "--fresh"], "env": {ENV_STARTER: "TREECKO"},
           "env_keys": list(LC.ENV_KEYS_FIRST), "world_in": None, "truth_before": None, "run_dir": "C:/x/r1",
           "truth_after": {"frame": 500, "state_md5": "m1"}, "kept_world": "C:/out/L1/world_last.jsonl",
           "kept_world_sha256": "s1"}
    row.update(changes)
    return row


def l2_row(**changes) -> dict:
    row = {"leg": "L2", "command": ["py", "run", "--state", str(Path("C:/x/r1") / "end_state.ss1")], "env": {},
           "env_keys": list(LC.ENV_KEYS_LATER), "world_in": "C:/out/L1/world_last.jsonl", "world_in_sha256": "s1",
           "truth_before": {"frame": 500, "state_md5": "m1"}}
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
    ok(M.custody_problems(l2_row(command=["py", "run", "--state", "C:/other/end_state.ss1"]), l1_row(), JOB_S, 1), "state")


def case_custody_wrong_world_sha(M, tmp):
    ok(M.custody_problems(l2_row(world_in_sha256="s2"), l1_row(), JOB_S, 1), "world sha")
    ok(M.custody_problems(l2_row(world_in_sha256=None), l1_row(kept_world_sha256=None), JOB_S, 1), "no sha either side")


def case_custody_wrong_world_path(M, tmp):
    ok(M.custody_problems(l2_row(world_in="C:/x/r1/world.jsonl"), l1_row(), JOB_S, 1), "the original world.jsonl")


def case_custody_l1_state(M, tmp):
    ok(M.custody_problems(l1_row(command=["py", "run", "--fresh", "--state", "C:/s.ss1"]), None, JOB_S, 0), "--state")
    ok(M.custody_problems(l1_row(command=["py", "run"]), None, JOB_S, 0), "no --fresh")


def case_custody_l1_world(M, tmp):
    ok(M.custody_problems(l1_row(world_in="C:/w.jsonl"), None, JOB_S, 0), "L1 with a world")
    ok(M.custody_problems(l1_row(truth_before={"frame": 1}), None, JOB_S, 0), "L1 with a start truth")


def case_custody_l1_starter(M, tmp):
    ok(M.custody_problems(l1_row(env={ENV_STARTER: "MUDKIP"}), None, JOB_S, 0), "another starter")


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
    chains, jobs = stopped_batch(1, {"L3": {"miss": True}})
    eq(by_id(grade(M, chains, jobs), "LC.REACH").status, "PASS", "5 of 6")
    ok(not M.chain_reaches(chains[1], 5), "the chain stopped at L3 does not reach")


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
def fake_repo(tmp: Path) -> Path:
    """The files registered_numbers hashes, copied into a temp tree (its AI code: one brain file)."""
    root = tmp / "repo"
    for rel in (*LC.GRADER_FILES, LC.MILESTONES):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, root / rel)
    (root / "ai_player" / "brain").mkdir(parents=True, exist_ok=True)
    (root / "ai_player" / "brain" / "goals.py").write_text("x = 1\n", encoding="utf-8")
    return root


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
    text = path.read_text(encoding="utf-8")
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
                   "ALREADY HELD", "UNREAD", "LC.MEMORY", "Route104", "goal manager's in-run memory starts again"):
        ok(needle in text, f"the bounds text says {needle!r}")


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
                 tree: FakeTree | None = None, clock=None, pre_spawn=None, tree_every: float = 10 ** 9) -> None:
        self.M, self.plans, self.alive = M, plans or {}, alive
        self.repo = tmp / "repo"
        self.build = self.repo / "sandbox-pokebot"
        (self.build / "profiles").mkdir(parents=True)
        self.out, self.ledger, self.evidence = tmp / "out", tmp / "ledger.json", tmp / "evidence"
        self.handles: list[FakeHandle] = []
        self.killed: list[int] = []
        self.tree = tree or FakeTree()
        self.pre_spawn = pre_spawn
        ticks = iter(range(10 ** 6))
        self.deps = M.Deps(spawn=self.spawn, free=free, git_state=lambda: {"head": "a", "origin": "a", "dirty": []},
                           leftover=lambda: [], g3=lambda: [], watch=lambda: self.tree, snapshot=lambda: None,
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
            finally:
                L5.PROFILE = saved
        handle = FakeHandle(runner, self.alive, pid=1000 + len(self.handles))
        self.handles.append(handle)
        return handle

    def register(self) -> None:
        legs = self.M.legs_of("ch5_rival_meet", self.M.load_milestones())
        found = self.M.registered_numbers("ch5", "ch5_rival_meet", (6201, 6206), 6, legs, REPO)
        self.M.register((6201, 6206), found, "test", path=self.ledger)

    def run(self, args: argparse.Namespace) -> tuple[int, str]:
        buffer = io.StringIO()
        with mock.patch.object(self.M, "ai_code_sha256", lambda repo=None: "0" * 64), contextlib.redirect_stdout(buffer):
            code = self.M.run_batch(args, self.deps)
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
    ok("3 of 3 reach ch2_wally." in evidence and hashlib.sha256(b"3 of 3 reach ch2_wally.").hexdigest() in evidence,
       "the prediction and its sha in the evidence")
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
    "run_batch": {"gather_facts", "run_refusal", "watch", "check", "seal", "begin", "finish", "schedule", "salvage_chain",
                  "end_sweep", "grade_batch", "guard_decision", "newest_world", "kill", "kill_tree", "keep_earlier"},
    "gather_facts": {"legs_of", "g3", "git_state", "seeds_named", "free"},
    "run_chain": {"child_refusal", "check_purity", "check_after_is_this_run", "finish_leg", "custody_problems",
                  "continue_after", "guard_mark", "stop_rest", "salvage_leg"},
    "finish_leg": {"stream_world_tail", "measure_then_delete", "read_log_counts"},
}


def case_wiring(M, tmp):
    source = Path(M.__file__).read_text(encoding="utf-8")
    for function, want in WIRING.items():
        missing = want - calls_in(source, function)
        ok(not missing, f"{function} no longer calls {sorted(missing)}")


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
WiringTests = _bind(type("WiringTests", (Base,), {}), ("wiring",))


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
    ("M11_original_world", "        carried.pop(arm_name, None)\n        if end_state is not None and end_state.is_file() "
                           "and row[\"kept_world\"]:\n            reads = [r for r in run.earlier + run.records if "
                           "r.get(\"decision\") == \"read\"]\n            carried[arm_name] = (end_state, "
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
    ("M59_no_finish", '    ledger.finish(entry["id"], verdict_line, reference,', '    _skip(entry["id"], verdict_line, reference,',
     ["wiring"]),
    ("M60_no_seal", '    _, frozen_line = tree.seal("PASS" if held else "FAIL")', '    _, frozen_line = (None, "skipped")',
     ["wiring"]),
    ("M61_no_refusal", "    refusal = run_refusal(args, facts)", "    refusal = None", ["wiring", "e2e_refusal_before_ledger"]),
    ("M62_no_purity", "        check_purity(run, None)\n", "        pass\n", ["wiring", "chain_control"]),
    ("M63_no_this_run", "        L5.check_after_is_this_run(run)\n", "        pass\n", ["wiring", "chain_control"]),
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
    ("M85_no_end_sweep", "    world_left = end_sweep(jobs, build_root)", "    world_left = []",
     ["wiring", "world_guard_kills"]),
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
