"""UNIT PROOFS of A1's frontier probe (`gates/frontier_probe.py`, spec `2026-11-11-A1-FRONTIER-PROBE-SPEC.md` 4.1: T1-T36;
T37 and T38 are fix round 5's: --parallel under 1 and a job's env, each refused), on PLANTED facts, rows, records, run folders and milestone data, with STUB launches (no emulator, no live run). Test side.

    py -3.12 -B ai_player/gates/test_frontier_probe.py         (or: py -3.12 -B -m unittest ai_player.gates.test_frontier_probe)

Every guard has a FAULT case that must fire and a CONTROL case that must not (CLAUDE.md rule 6). The cases are module-level
functions `case_<name>(M, tmp)` taking the module under test, so a MUTATED copy of `frontier_probe.py` (`load_module`: one
guard removed) can run the same case and must FAIL it (the build's B2.3 table and `revert_frontier.py`). A test that plants a
milestone puts it AFTER the real file's last chapter (chapter 8): `legs_of` refuses chapters that go backwards.
"""

from __future__ import annotations

import ast
import atexit
import copy
import hashlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import frontier_probe as FP  # noqa: E402
from ai_player.gates import ledger  # noqa: E402
from ai_player.gates import live_chain as LC  # noqa: E402
from ai_player.gates import live_step2 as L2  # noqa: E402
from ai_player.gates import live_step5 as L5  # noqa: E402
from ai_player.options import ENV_GOALS, ENV_STARTER, ENV_TARGET, ENV_WORLD  # noqa: E402

GATES = Path(__file__).resolve().parent
SOURCE = GATES / "frontier_probe.py"
FIXTURES = GATES / "fixtures"
LEDGER_AT_START = ledger.LEDGER.read_bytes() if ledger.LEDGER.is_file() else None


def _retry_writable(function, name, _info) -> None:
    """rmtree's error hook: a path it could not delete (git makes `.git/objects` files READ-ONLY, and T10's and T11's temp
    repositories hold them) gets its read-only bit cleared and is deleted once more; a path still in the way stays."""
    try:
        os.chmod(name, stat.S_IWRITE)
        function(name)
    except OSError:
        pass


def remove_tree(path: Path) -> None:
    """The suite's temp root removed WHOLE, read-only files included (verifier round 3, N5: `ignore_errors=True` left every
    run's root in %TEMP%, its repositories' read-only objects in it)."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_retry_writable)
    else:  # pragma: no cover - the project runs 3.12
        shutil.rmtree(path, onerror=_retry_writable)


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="a1fp_test_"))
atexit.register(remove_tree, _TEMP_ROOT)
#: the LF sha256 of the two real-data fixtures (`make_a1_fixtures.py`, their .build.json)
LOOPS_SHA256 = "2491379ea22a3b1895025d01b86837bd7a402f8ab8a0e2fbb25aeeb1ed99e90d"
TELLS_SHA256 = "80dc799c8469ed2e19b2492491f939efeb4e48197180a59c65b8e5f3e82365ee"


def tearDownModule() -> None:
    remove_tree(_TEMP_ROOT)
    now = ledger.LEDGER.read_bytes() if ledger.LEDGER.is_file() else None
    if now != LEDGER_AT_START:
        raise AssertionError("the REAL ledger.json changed while test_frontier_probe ran: a test forgot its temp ledger")


# ---------------------------------------------------------------------------------------------------- small helpers
def ok(condition, message: str = "assertion") -> None:
    if not condition:
        raise AssertionError(message)


def eq(a, b, message: str = "") -> None:
    if a != b:
        raise AssertionError(f"{message}: {a!r} != {b!r}")


def refused(M, fn, *args, **kwargs) -> str:
    try:
        fn(*args, **kwargs)
    except M.Refusal as error:
        return str(error)
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"raised {type(error).__name__}: {error}, not a Refusal") from None
    raise AssertionError(f"{getattr(fn, '__name__', fn)} was not refused")


_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        _DATA = LC.load_milestones(REPO)
    return copy.deepcopy(_DATA)


def md5(path: Path) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def proof_of(mid: str) -> dict:
    return FP.milestone_proof(next(m for m in data()["milestones"] if m["id"] == mid))


def marks_through(last: str | None) -> dict:
    """Every milestone proof up to and including `last` held (file order), every later one not held (a variable takes the
    largest at_least of the held ones, else one under the smallest)."""
    milestones = data()["milestones"]
    ids = [m["id"] for m in milestones]
    ok(last is None or last in ids, f"no milestone {last}")
    upto = -1 if last is None else ids.index(last)
    marks: dict = {}
    for milestone in milestones:
        proof = FP.milestone_proof(milestone)
        for name in proof["flags"]:
            marks[name] = 0
        for name in proof["trainers"]:
            marks[f"TRAINER_{name}"] = 0
        for name, info in proof["variables"].items():
            marks[f"VAR_{name}"] = min(marks.get(f"VAR_{name}", info["at_least"] - 1), info["at_least"] - 1)
    for milestone in milestones[:upto + 1]:
        proof = FP.milestone_proof(milestone)
        for name in proof["flags"]:
            marks[name] = 1
        for name in proof["trainers"]:
            marks[f"TRAINER_{name}"] = 1
        for name, info in proof["variables"].items():
            marks[f"VAR_{name}"] = max(marks[f"VAR_{name}"], info["at_least"])
    return marks


def held_ids(marks: dict) -> list[str]:
    return [m["id"] for m in data()["milestones"] if LC.proof_holds(marks, FP.milestone_proof(m))["held"]]


def facts(**changes) -> dict:
    """The facts `classify` reads: a CLEAN, fresh leg that chose to end (exit 0, `play: done:`), by default."""
    out = {"guard": None, "salvaged": None, "refusal": None, "exit": 0, "stdout": "[AI-GATE] exit=0 verdict=PASS",
           "verdict": {"verdict": "CLEAN", "facts": {"exit_code": 0, "exit_reason": "play: done: ch1_pokedex reached"},
                       "counters": {"real_frames": 1000}},
           "driver_killed": False, "launch_died": None, "fresh": True, "end_truth": True, "frames": 330000, "mc": False}
    out.update(changes)
    return out


def verdict(reason: str = "play: done: ch1_pokedex reached", real: int = 1000, word: str = "CLEAN") -> dict:
    return {"verdict": word, "facts": {"exit_code": 0, "exit_reason": reason}, "counters": {"real_frames": real}}


def leg_record(run_id: str, klass: str, ended: float = 0.0, **changes) -> dict:
    record = {"schema_version": 1, "record": "leg", "run_id": run_id, "class": klass, "ended": ended,
              "reached": False, "leg": {"leg": "L1", "chapter": 1, "index": 0}, "job": {"origin": "new_game"},
              "tree": {"play_digest": "TREE"}, "blocker": None, "measures": {}, "start_memory": {}}
    record.update(changes)
    return record


def transitions(pair: tuple[str, str], each_way: int, last_frame: int, step: int = 100, how: str = "warp") -> list:
    """`each_way` crossings A->B and B->A alternating, the last one at `last_frame`."""
    out = []
    total = 2 * each_way
    for i in range(total):
        frame = last_frame - (total - 1 - i) * step
        a, b = (pair[0], pair[1]) if i % 2 == 0 else (pair[1], pair[0])
        out.append([frame, a, b, how, "ai", [1, 1], [2, 2], "up"])
    return out


def world_of(trans: list, consts: dict | None = None, **extra) -> dict:
    keys = sorted({t[1] for t in trans} | {t[2] for t in trans})
    consts = consts or {}
    maps = {key: {"key": key, "name": key, "const": consts.get(key, key), "tile_fields": list(FP.TILE_FIELDS),
                  "tiles": {}} for key in keys}
    return {"maps": maps, "warps": {}, "connections": [], "transitions": trans, "tiles_learned": 1, **extra}


# ---------------------------------------------------------------------------------------------------- the stub launcher
GATE_LINE = f"[AI-GATE] exit=0 verdict=PASS package={L2.REPO / 'ai_player'}"


class Stub:
    """A fake `live_step5.run_arm`: plants the run folder as run_arm leaves it (actions.jsonl, ai_player.log, world.jsonl,
    end_state.ss1, goals.jsonl) and returns a `live_step5.Run` whose truths it controls. A leg's start truth is the truth
    this stub (or the test, `truths`) gave the state's CONTENT (as `truth_of` would read it). `plan[leg]` plants: miss,
    reason, exit, word, no_verdict, real, stale, frame_off, same_md5, no_world, truncate, transitions, consts, records, log,
    goals (False: no snapshot; or {"losses", "tried"}), marks, end_map, no_end_truth, driver_killed, stdout, breach, raise,
    after (a callable(run) run last), before (a callable(arm) run first)."""

    def __init__(self, job: dict, plan: dict | None = None) -> None:
        self.job = job
        self.plan = plan or {}
        self.calls: list[str] = []
        self.arms: list = []
        self.carried: list = []
        self.truths: dict[str, dict] = {}
        self.stamp = 0
        self.order = [m["id"] for m in data()["milestones"] if not m.get("optional") and m.get("waypoint") is None]

    def __call__(self, arm, build_root: Path, carried: dict):
        leg = arm.name.rsplit("-", 1)[1]
        plan = self.plan.get(leg, {})
        self.calls.append(arm.name)
        self.arms.append(arm)
        self.carried.append({k: tuple(str(x) if isinstance(x, Path) else x for x in v[:2]) for k, v in carried.items()})
        if plan.get("before"):
            plan["before"](arm)
        if plan.get("raise"):
            raise RuntimeError("the launcher could not start")
        run = L5.Run(arm)
        profile = Path(build_root) / "profiles" / L5.PROFILE
        self.stamp += 1
        run.run_dir = profile / "ai_player_runs" / f"20261114-{self.stamp:06d}-{arm.name}"
        run.run_dir.mkdir(parents=True)
        start = ["--fresh"]
        carried_transitions: list = []
        if arm.state_from is not None:
            state, world, earlier = carried[arm.state_from]
            run.earlier = [r for r in earlier if r.get("decision") == "read"]
            run.world_in, run.start_state = Path(world), Path(state)
            start = ["--state", str(state)]
            run.before = copy.deepcopy(self.truths.get(md5(state)))
            last = FP.parse_object(FP.last_line_of(Path(world)))
            carried_transitions = list((last or {}).get("transitions") or [])
        run.command = ["py", "-m", "ai_player", "run", "--profile", L5.PROFILE, "--frames", str(arm.frames),
                       "--run-dir", str(run.run_dir), *start]
        run.started = time.time()
        start_frame = (run.before or {}).get("frame") or 0
        frames = int(plan.get("real", 1000 + self.stamp))
        target = arm.env[ENV_TARGET]
        miss = bool(plan.get("miss"))
        log = [f"[AI-HANDS] outcome=done presses=10 frames={frames}",
               "[AI-WORLD] memory from nothing (a new memory): 0 maps (none), 0 tiles learned, 0 warp links, 0 "
               "connections, 0 map changes; goal -", *plan.get("log", [])]
        run.ai_log = "\n".join(log) + "\n"
        (run.run_dir / "ai_player.log").write_text(run.ai_log, encoding="utf-8")
        run.records = [{"decision": "read", "frame": start_frame + 1, "reason": f"a page of {arm.name}"},
                       *copy.deepcopy(plan.get("records", []))]
        (run.run_dir / "actions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in run.records), encoding="utf-8")
        if not plan.get("no_world"):
            trans = carried_transitions + list(plan.get("transitions", [[start_frame + 5, "0:1", "0:2", "warp", "ai",
                                                                         [1, 1], [2, 2], "up"]]))
            last = json.dumps(world_of(trans, plan.get("consts"), **plan.get("world_extra", {})), separators=(",", ":"))
            body = json.dumps({"maps": {}, "transitions": []}) + "\n" + last + "\n"
            if plan.get("truncate"):
                body = json.dumps({"maps": {}, "transitions": []}) + "\n" + last[: len(last) // 2] + "\n"
            (run.run_dir / "world.jsonl").write_text(body, encoding="utf-8")
        if plan.get("goals", True) is not False:
            goals = plan.get("goals") if isinstance(plan.get("goals"), dict) else {}
            line = {"kind": "goals", "schema_version": 1, "end": "done: x", "frame": start_frame + frames,
                    "memory": {"goals": {"tried_items": {"$set": sorted(goals.get("tried", []))}}, "personality": {},
                               "battle": {}, "mons": {}, "losses": int(goals.get("losses", 0))}}
            (run.run_dir / "goals.jsonl").write_text(json.dumps({"kind": "goals", "early": True}) + "\n"
                                                     + json.dumps(line) + "\n", encoding="utf-8")
        end = run.run_dir / "end_state.ss1"
        if plan.get("same_md5") and run.start_state is not None:
            end.write_bytes(Path(run.start_state).read_bytes())
        else:
            end.write_bytes(f"{arm.name}-{self.stamp}-{time.time()}".encode())
        if "marks" in plan:
            marks = plan["marks"]
        elif miss:
            index = self.order.index(target)
            marks = marks_through(self.order[index - 1] if index else None)
        else:
            marks = marks_through(target)
        offset = int(plan.get("frame_off", 0))
        run.after = None if plan.get("no_end_truth") else {
            "frame": start_frame + frames + offset, "map": plan.get("end_map", [0, 3]), "state_md5": md5(end),
            "story": {"marks": marks, "stats": {}}, "party_exp": [["0000beef", "Treecko", 100, 5]],
            "party_ot": [["0000beef", 1]], "player_tid": 1}
        if run.after is not None:
            self.truths[md5(end)] = copy.deepcopy(run.after)
        run.state_mtime = run.started - 100.0 if plan.get("stale") else run.started + 1.0
        reason = plan.get("reason", f"play: done: {target} reached" if not miss else "play: stuck: out of ideas")
        counters = {"ai_presses": 20, "real_frames": frames, **{k: 0 for k in L2.BREACH_COUNTERS}}
        if plan.get("breach"):
            counters[L2.BREACH_COUNTERS[0]] = 1
        run.verdict = None if plan.get("no_verdict") else {
            "verdict": plan.get("word", "CLEAN"), "counters": counters,
            "facts": {"exit_code": 0, "exit_reason": reason, "package_root": str(L2.REPO)}}
        run.stdout = plan.get("stdout", GATE_LINE + "\n")
        run.exit_code = int(plan.get("exit", 0))
        run.elapsed = 12.5
        run.driver_killed = bool(plan.get("driver_killed"))
        run.measures["harness_stop"] = L5.harness_stop(run)
        if plan.get("after"):
            plan["after"](run)
        return run


def donor(build: Path) -> None:
    (build / "profiles" / FP.DONOR).mkdir(parents=True, exist_ok=True)
    (build / "profiles" / FP.DONOR / "metadata.yml").write_text("rom: test\n", encoding="utf-8")


def job_of(M, tmp: Path, to: str = "ch2_wally", persona: str = "Story", starter: str = "TREECKO", seed: int = 7001,
           kind: str = "chain", start: dict | None = None, goals: str = "carry", mc: bool = False, arm: str = "REAL",
           batch: str = "T", from_chapter: int = 1, with_donor: bool = True) -> dict:
    legs = M.legs_for(to, data(), mc=mc, from_chapter=from_chapter)
    job = M.make_job(batch, arm, "REAL", kind, persona, starter, seed, legs, start or {"kind": "new_game", "id": "NG"},
                     goals, mc=mc)
    build = tmp / "build"
    build.mkdir(parents=True, exist_ok=True)
    if with_donor:
        donor(build)
    job.update({"out": str(tmp / "out"), "build_root": str(build), "stage_dir": str(tmp / "stage"),
                "tree": {"arm": "REAL", "commit": "c0ffee", "play_digest": "PLAY", "digest": "ALL", "mutant": None},
                "batch_info": {"name": batch, "mode": "development", "ledger": None, "started": "now"}, "deadline": None})
    return job


def play(M, job: dict, plan: dict | None = None, before_leg=None, stub: Stub | None = None):
    """One job through `M.run_job` with a stub; `live_step5.PROFILE` restored after."""
    stub = stub or Stub(job, plan)
    saved = L5.PROFILE
    L5.PROFILE = job["profile"]
    try:
        record = M.run_job(job, stub, before_leg)
    finally:
        L5.PROFILE = saved
    return record, stub, [r for r in M.read_records(Path(job["out"])) if r.get("record") == "leg"]


def planted_start(M, tmp: Path, stub_truths: dict, last: str = "ch5_rival_meet", goals: dict | None = None,
                  name: str = "S1", world: dict | None = None) -> dict:
    """A kept chain end (as a WP1b job takes it): end_state.ss1, world_last.jsonl and, unless goals is False, a goal
    snapshot, with the truth registered for the stub."""
    folder = tmp / "starts" / name
    folder.mkdir(parents=True, exist_ok=True)
    state = folder / "end_state.ss1"
    state.write_bytes(f"start {name} {time.time()}".encode())
    world_file = folder / "world_last.jsonl"
    world_file.write_text(json.dumps(world or world_of([[100, "0:3", "0:19", "connection", "ai", [1, 1], [2, 2], "down"]]),
                                     separators=(",", ":")) + "\n", encoding="utf-8")
    goals_file = None
    if goals is not False:
        goals = goals or {}
        goals_file = folder / "goals_last.jsonl"
        goals_file.write_text(json.dumps({"kind": "goals", "schema_version": 1, "end": "done: x", "frame": 5000,
                                          "memory": {"goals": {"tried_items": {"$set": sorted(goals.get("tried", []))}},
                                                     "personality": {}, "battle": {}, "mons": {},
                                                     "losses": int(goals.get("losses", 0))}}) + "\n", encoding="utf-8")
    stub_truths[md5(state)] = {"frame": 5000, "map": [0, 3], "state_md5": md5(state),
                               "story": {"marks": marks_through(last), "stats": {}}}
    return {"kind": "chain_end", "id": name, "folder": str(folder), "state": str(state), "state_md5": md5(state),
            "world": str(world_file), "world_sha256": M.sha256_of(world_file),
            "goals": str(goals_file) if goals_file else None,
            "goals_sha256": M.sha256_of(goals_file) if goals_file else None, "reads": str(folder / "reads.jsonl"),
            "made_by": "planted", "persona": "Story", "starter": "TREECKO", "starter_from": "plan", "fallback_for": None}


def practice_job(M, tmp: Path, plan: dict | None = None, last: str = "ch5_rival_meet", goals: dict | None = None,
                 to: str = "ch7_brawly", goals_policy: str = "carry", persona: str = "Story", before_leg=None,
                 world: dict | None = None):
    """A practice job (L6-L7 or as `to` says) from a planted chain end, played through the stub."""
    job = job_of(M, tmp, to=to, persona=persona, kind="practice", goals=goals_policy, from_chapter=6)
    stub = Stub(job, plan)
    job["start"] = planted_start(M, tmp, stub.truths, last, goals, world=world)
    return play(M, job, plan, before_leg, stub)


def by_leg(records: list[dict]) -> dict:
    return {r["leg"]["leg"]: r for r in records}


# ==================================================================================================== THE CASES
# ---------------------------------------------------------------------------------------------------- T1, T1b: REFUSED
def case_t1_refused(M, tmp):
    eq(M.classify(facts(exit=7, stdout="[AI-GATE] FAIL rule (a) import", verdict=None))[0], M.REFUSED, "exit 7, other text")
    eq(M.classify(facts(exit=2, verdict=None, launch_died="(it also died)"))[0], M.REFUSED, "exit 2 with no verdict file")
    eq(M.classify(facts(refusal="the donor profile: LaunchError"))[0], M.REFUSED, "the child's own refusal")


def case_t1_control(M, tmp):
    crash = facts(exit=2, verdict=verdict("crash"))
    eq(M.classify(crash)[0], M.CLEAN_INVOLUNTARY, "exit 2 with a CLEAN verdict, crash")


def case_t1b_gate_timeout(M, tmp):
    text = M.gate_timeout_text()
    eq(text, "FAIL the purity gate did not finish within 180s", "the launcher's own timeout text")
    leg = facts(exit=7, stdout=f"[AI-GATE] exit=2 verdict=FAIL\n[AI-GATE] {text}\n", verdict=None)
    eq(M.classify(leg)[0], M.INFRA, "a gate TIMEOUT")
    records = [leg_record(f"r{i}", M.classify(leg)[0], i) for i in range(5)]
    eq(M.ai_stop_streak(records), 0, "five gate timeouts never trip the AI-only stop")


def case_t1b_control(M, tmp):
    eq(M.classify(facts(exit=7, stdout="[AI-GATE] FAIL rule (b) a bot import\n", verdict=None))[0], M.REFUSED,
       "other gate text")


# ---------------------------------------------------------------------------------------------------- T2, T2b: budget, missing verdict
def case_t2_budget(M, tmp):
    eq(M.classify(facts(exit=4, verdict=verdict("frame-budget")))[0], M.CLEAN_BUDGET, "exit 4")
    eq(M.classify(facts(exit=124, verdict=verdict("wall-clock")))[0], M.CLEAN_BUDGET, "exit 124 WITH a verdict")
    eq(M.classify(facts(verdict=verdict("play: stopped: not finished within 330000 frames", 330000)))[0], M.CLEAN_BUDGET,
       "stopped with the budget run out")


def case_t2_control(M, tmp):
    eq(M.classify(facts(verdict=verdict("play: stopped: not finished", 329999)))[0], M.CLEAN_CHOSEN,
       "stopped one frame before its budget")


def case_t2b_missing_verdict(M, tmp):
    hung = facts(exit=124, verdict=None)
    eq(M.classify(hung)[0], M.HUNG, "exit 124 with no verdict")
    ok(M.blocker_of(1, "ch1_lab", M.reason_norm(M.HUNG_TEXT), "ROUTE101", M.HUNG, False, None) is not None, "HUNG blocks")
    eq(M.ai_stop_streak([leg_record(f"h{i}", M.HUNG, i) for i in range(5)]), 5, "5 HUNG in a row")
    eq(M.classify(facts(exit=8, verdict=None))[0], M.NOT_CLEAN, "exit 8")
    eq(M.classify(facts(exit=1, verdict=None))[0], M.NOT_CLEAN, "exit 1 with no verdict")


def case_t2b_control(M, tmp):
    eq(M.classify(facts(exit=-9, verdict=None, driver_killed=True))[0], M.INFRA, "driver_killed")
    eq(M.classify(facts(exit=1, verdict=None, launch_died="harness: the launch died before playing a frame"))[0], M.INFRA,
       "launch_died")
    stream = [leg_record(f"h{i}", M.HUNG, i) for i in range(4)] + [leg_record("i", M.INFRA, 5)]
    eq(M.ai_stop_streak(stream), 4, "INFRA does not count")
    eq(M.ai_stop_streak(stream + [leg_record("h5", M.HUNG, 6)]), 5, "INFRA does not reset")
    with mock.patch.object(M, "judge_leg", mock.Mock(side_effect=RuntimeError("a harness bug"))):
        try:
            record, stub, records = play(M, job_of(M, tmp, to="ch2_wally", seed=7099), {})
        except RuntimeError as error:
            raise AssertionError(f"a harness failure while judging a leg crashed the job ({error}): it must be an INFRA "
                                 f"record") from None
    eq((len(stub.calls), records[0]["class"], record["not_run"]), (1, M.INFRA, ["L2"]),
       "a harness failure while judging a leg is INFRA (salvaged), never a crash of the job")


# ---------------------------------------------------------------------------------------------------- T3, T4: freshness, NOT CLEAN
def case_t3_freshness(M, tmp):
    for i, plan in enumerate(({"stale": True}, {"frame_off": 6}, {"same_md5": True})):
        job = job_of(M, tmp / f"f{i}", seed=7100 + i)
        _, _, records = play(M, job, {"L2": plan})
        eq(by_leg(records)["L2"]["class"], M.INFRA, f"a state not this run's ({plan})")
        eq(by_leg(records)["L2"]["fresh"]["ok"], False, f"L5.THIS_RUN fails ({plan})")


def case_t3_control(M, tmp):
    _, _, records = play(M, job_of(M, tmp), {})
    eq([r["class"] for r in records], [M.CLEAN_CHOSEN, M.CLEAN_CHOSEN], "fresh states")
    eq(by_leg(records)["L2"]["fresh"]["ok"], True, "L2 fresh")


def case_t4_not_clean(M, tmp):
    eq(M.classify(facts(verdict=verdict(word="NOT CLEAN")))[0], M.NOT_CLEAN, "a verdict NOT CLEAN, exit 0")


def case_t4_control(M, tmp):
    eq(M.classify(facts())[0], M.CLEAN_CHOSEN, "CLEAN")


# ---------------------------------------------------------------------------------------------------- T5: claim mismatch
def case_t5_claim(M, tmp):
    _, _, records = practice_job(M, tmp, {"L6": {"miss": True, "reason": "play: done: ch6_dewford reached"}},
                                 to="ch6_dewford")
    record = by_leg(records)["L6"]
    eq((record["class"], record["reached"], record["claim_mismatch"]), (M.CLEAN_CHOSEN, False, True), "a false claim")
    ok(record["blocker"] is not None, "a claim mismatch is a blocker")


def case_t5_control(M, tmp):
    _, _, records = practice_job(M, tmp, {}, to="ch6_dewford")
    record = by_leg(records)["L6"]
    eq((record["reached"], record["claim_mismatch"], record["blocker"]), (True, False, None), "a true claim")


# ---------------------------------------------------------------------------------------------------- T6: clustering
def case_t6_clustering(M, tmp):
    a = M.blocker_of(6, "ch6_dewford", M.reason_norm("play: stuck: 3 battles lost (MAX_LOSSES 3)"), "ROUTE104",
                     M.CLEAN_CHOSEN, False, None)
    b = M.blocker_of(6, "ch6_dewford", M.reason_norm("play: stuck: 2 battles lost (MAX_LOSSES 30)"), "ROUTE104",
                     M.CLEAN_CHOSEN, False, None)
    eq(a["key_id"], b["key_id"], "one reason, other numbers: ONE key")
    eq(a["key"][2], "play: stuck: N battles lost (MAX_LOSSES N)", "digits made N")
    loop = {"pair": "PETALBURG_WOODS|ROUTE104", "crossings": 118, "crossings_raise": 0, "last_to_end": 92013,
            "raise_active_at_end": False}
    one = M.blocker_of(5, "ch5_return_goods", "play: stopped: not finished within N frames", "ROUTE116", M.CLEAN_BUDGET,
                       False, {**loop, "keyed": M.loop_keyed(loop, False, M.CLEAN_BUDGET, "play: stopped")})
    loop2 = {**loop, "crossings": 74, "last_to_end": 20}
    reason2 = "play: stuck: no progress for N frames"
    two = M.blocker_of(5, "ch5_rusturf_grunt", reason2, "ROUTE104", M.CLEAN_CHOSEN, False,
                       {**loop2, "keyed": M.loop_keyed(loop2, False, M.CLEAN_CHOSEN, reason2)})
    eq(one["key"], two["key"], "two LOOP legs on one pair: ONE LOOP key")
    eq(one["key"], [5, "-", "loop", "PETALBURG_WOODS|ROUTE104", "LOOP"], "the LOOP key")
    out = tmp / "out6"
    for i, blocker in enumerate((one, two)):
        M.append_record(out, leg_record(f"T-L{i}", M.CLEAN_BUDGET, i, blocker=blocker,
                                        leg={"leg": "L5", "chapter": 5, "index": 4}))
    report = M.build_report(out)
    cell = report["trees"]["TREE"]["5"]
    eq([(b["key"], b["count"]) for b in cell["blockers"]], [(one["key"], 2)], "count 2 under one key")


def case_t6_control(M, tmp):
    base = M.blocker_of(6, "ch6_dewford", "play: stuck: N battles lost", "ROUTE104", M.CLEAN_CHOSEN, False, None)
    for other in (M.blocker_of(6, "ch7_steven", "play: stuck: N battles lost", "ROUTE104", M.CLEAN_CHOSEN, False, None),
                  M.blocker_of(6, "ch6_dewford", "play: stuck: N battles lost", "ROUTE104", M.CLEAN_BUDGET, False, None),
                  M.blocker_of(6, "ch6_dewford", "play: stuck: N battles lost", "DEWFORD_TOWN", M.CLEAN_CHOSEN, False,
                               None)):
        ok(other["key_id"] != base["key_id"], f"another next milestone, class or end map: TWO keys ({other['key']})")


# ---------------------------------------------------------------------------------------------------- T7: next unmet
def case_t7_next_unmet(M, tmp):
    marks = marks_through("ch6_dewford")
    marks["RECEIVED_OLD_ROD"] = 0
    eq(M.next_unmet(marks, data())["next"], "ch7_steven", "the optional ch6_old_rod is never chosen")
    marks = marks_through("ch2_wally")
    eq(M.next_unmet(marks, data())["next"], "ch3_woods", "the waypoint ch3_route104 is never chosen")
    marks = marks_through("ch2_wally")
    del marks["VAR_PETALBURG_WOODS_STATE"]
    found = M.next_unmet(marks, data())
    ok("ch3_woods" in found["unread"] and found["next"] != "ch3_woods", f"an absent mark is UNREAD: {found}")
    before = {"frame": 10, "state_md5": "aaa", "marks": marks_through("ch5_rival_meet")}
    eq(M.truth_for_next(before, {"frame": 10, "state_md5": "aaa", "marks": {}}, True)[1], "start",
       "a HUNG leg ending at its start (the same md5)")
    eq(M.truth_for_next(before, {"frame": 99, "state_md5": "bbb"}, False)[1], "start", "an end state not written by it")
    # a HUNG leg's END MAP is the kept world tail's current map (3.5; verifier round 3, R3-M4 c: no case read it), part of
    # its key: the tail's last transition enters 0:2 (ROUTE102) while its end truth reads [0, 3] (RUSTBORO_CITY)
    hung = job_of(M, tmp / "hung", to="ch1_pokedex", seed=7801)
    _, _, records = play(M, hung, {"L1": {**TAIL_LEG, "exit": 124, "no_verdict": True, "miss": True}})
    eq((records[0]["class"], records[0]["end_map"], (records[0]["blocker"] or {}).get("key", [None] * 5)[3]),
       (M.HUNG, {"pair": [0, 2], "const": "ROUTE102"}, "ROUTE102"), "a HUNG leg's end map: the kept world tail's, in its key")
    # a CUT-WORLD leg's END MAP likewise (verifier round 4, V4-M2: the HUNG arm pinned only the HUNG half, and CUT_WORLD
    # dropped from the rule passed every case): a leg the WORLD GUARD killed (no verdict, exit 1, its kill marker) ends
    # on its kept tail's ROUTE102, in its key, never on its end truth's RUSTBORO_CITY
    cut = job_of(M, tmp / "cut", to="ch1_pokedex", seed=7805)
    _, _, records = play(M, cut, {"L1": {**TAIL_LEG, "no_verdict": True, "exit": 1, "miss": True,
                                         "after": guard_after(Path(cut["out"]), cut["chain"])}})
    eq((records[0]["class"], records[0]["end_map"], (records[0]["blocker"] or {}).get("key", [None] * 5)[3]),
       (M.CUT_WORLD, {"pair": [0, 2], "const": "ROUTE102"}, "ROUTE102"),
       "a CUT-WORLD leg's end map: the kept world tail's, in its key")


#: a leg whose kept world tail ends on ROUTE102 (0:2) while its end truth reads RUSTBORO_CITY ([0, 3]): T7's end-map arms
TAIL_LEG = {"end_map": [0, 3], "transitions": [[10, "0:3", "0:2", "warp", "ai", [1, 1], [2, 2], "up"]],
            "consts": {"0:3": "RUSTBORO_CITY", "0:2": "ROUTE102"}}


def case_t7_control(M, tmp):
    found = M.next_unmet(marks_through("ch4_roxanne"), data())
    eq(found["next"], "ch5_stolen_goods", "the first unheld")
    eq(found["unread"], [], "all marks present")
    before = {"frame": 10, "state_md5": "aaa"}
    eq(M.truth_for_next(before, {"frame": 99, "state_md5": "bbb"}, True)[1], "end", "next_unmet_from: end")
    # every other class reads the END TRUTH's map (3.5): a CLEAN leg with the same files ends on RUSTBORO_CITY
    clean = job_of(M, tmp / "clean", to="ch1_pokedex", seed=7802)
    _, _, records = play(M, clean, {"L1": {**TAIL_LEG, "miss": True}})
    eq((records[0]["class"], records[0]["end_map"], (records[0]["blocker"] or {}).get("key", [None] * 5)[3]),
       (M.CLEAN_CHOSEN, {"pair": [0, 3], "const": "RUSTBORO_CITY"}, "RUSTBORO_CITY"),
       "a CLEAN leg's end map: its end truth's, in its key")


# ---------------------------------------------------------------------------------------------------- T8: ranking
def ranked_out(M, tmp, legs: list[tuple]) -> dict:
    out = tmp / f"rank{len(list(tmp.iterdir()))}"
    for i, (tree, klass, nxt, reason, end, keyed, pair) in enumerate(legs):
        loop = {"pair": pair, "crossings": 50, "crossings_raise": 0, "last_to_end": 10, "raise_active_at_end": False,
                "keyed": keyed} if pair else None
        blocker = M.blocker_of(1, nxt, reason, end, klass, False, loop)
        M.append_record(out, leg_record(f"{tree}-{i}", klass, i, blocker=blocker, tree={"play_digest": tree},
                                        verdict={"real_frames": 1000 + i}))
    return M.build_report(out)


def case_t8_ranking(M, tmp):
    wall = "ch1_rival_route103"
    report = ranked_out(M, tmp, [
        ("WALL", M.CLEAN_CHOSEN, wall, "play: stuck: out of ideas", "OLDALE_TOWN", "none", None),
        ("WALL", M.CLEAN_CHOSEN, wall, "play: stuck: out of ideas", "OLDALE_TOWN", "none", None),
        ("WALL", M.CLEAN_BUDGET, wall, "play: stopped", "ROUTE103", "LOOP", "ROUTE101|ROUTE103"),
        ("WALL", M.CLEAN_CHOSEN, "ch1_lab", "play: stuck: x", "ROUTE101", "none", None),
        ("WALL", M.INFRA, wall, "x", "ROUTE101", "none", None), ("WALL", M.REFUSED, wall, "x", "ROUTE101", "none", None),
        ("WALL", M.NOT_CLEAN, wall, "x", "ROUTE101", "none", None),
        ("REAL", M.CLEAN_BUDGET, "ch1_lab", "play: stopped", "ROUTE101", "LOOP", "LITTLEROOT_TOWN|ROUTE101")])
    wall_cell, real_cell = report["trees"]["WALL"]["1"], report["trees"]["REAL"]["1"]
    top = wall_cell["blockers"][0]
    ok(M.names_milestone(top, wall), f"the planted wall first on its own tree: {top['key']}")
    ok(any(M.names_milestone(b, wall) for b in wall_cell["blockers"] if b["key"][4] == "LOOP"),
       "its LOOP-keyed leg read by its record's next_unmet")
    eq(wall_cell["judged"], 4, "INFRA, REFUSED and NOT CLEAN never in the denominator")
    counts = [b["count"] for b in wall_cell["blockers"]]
    eq(counts, sorted(counts, reverse=True), "ranked by count, most first")
    eq(top["share"], round(2 / 4, 4), "share = count / judged")
    eq(wall_cell["excluded"], {M.INFRA: 1, M.REFUSED: 1, M.NOT_CLEAN: 1}, "excluded counts shown")
    ok(not any(M.names_milestone(b, wall) for b in real_cell["blockers"]), "absent on the other tree")
    # the REACH SPLIT BY START KIND (3.8, DoD 4.4 item 6; verifier round 3, N3), through run_job and build_report: a chain
    # whose L2 CARRIES the goal snapshot counts it as "chain leg with a goal snapshot", its L1 as "new game"
    job = job_of(M, tmp / "kind", seed=7811)
    play(M, job, {})
    kinds = M.build_report(Path(job["out"]))["trees"]["PLAY"]
    eq((kinds["1"]["reach_by_start_kind"], kinds["2"]["reach_by_start_kind"]),
       ({"new game": {"reached": 1, "judged": 1}}, {"chain leg with a goal snapshot": {"reached": 1, "judged": 1}}),
       "a carried chain leg: 'chain leg with a goal snapshot'")


def case_t8_control(M, tmp):
    out = tmp / "none"
    M.append_record(out, leg_record("a", M.CLEAN_CHOSEN, 0, reached=True))
    M.append_record(out, leg_record("b", M.INFRA, 1))
    cell = M.build_report(out)["trees"]["TREE"]["1"]
    eq((cell["blockers"], cell["excluded"]), ([], {M.INFRA: 1}), "no blocker: an empty list, excluded counts shown")
    report = ranked_out(M, tmp, [("REAL", M.CLEAN_BUDGET, "ch1_lab", "play: stopped", "ROUTE101", "LOOP",
                                  "LITTLEROOT_TOWN|ROUTE101")])
    ok(not any(M.names_milestone(b, "ch1_rival_route103") for b in report["trees"]["REAL"]["1"]["blockers"]),
       "a tree whose only LOOP key's records never name the wall's milestone shows no wall")
    # a GOALS-OFF chain's L2 carries no snapshot: "chain leg without", never "with a goal snapshot" (3.8; round 3, N3)
    job = job_of(M, tmp / "kind", seed=7812, goals="off")
    play(M, job, {})
    eq(M.build_report(Path(job["out"]))["trees"]["PLAY"]["2"]["reach_by_start_kind"],
       {"chain leg without": {"reached": 1, "judged": 1}}, "a GOALS-OFF chain leg: 'chain leg without'")


# ---------------------------------------------------------------------------------------------------- T9: the env allow-list
class FakePopen:
    """`subprocess.Popen` replaced in live_step5's launch: records the command and the environment, plays nothing."""
    seen: list[dict] = []

    def __init__(self, command, cwd=None, env=None, **kwargs) -> None:
        FakePopen.seen.append({"command": [str(c) for c in command], "env": dict(env or {}), "cwd": cwd})
        self.returncode = 0
        self.pid = 424242

    def communicate(self, timeout=None):
        return b"", None

    def poll(self):
        return 0

    def kill(self):
        return None


def child_through_real_run_arm(M, job: dict, tmp: Path, truths: dict, stub_l1: Stub | None = None) -> list[dict]:
    """The CHILD's path (`child JOB.json`: the env sanitized, then `run_job` with the REAL `run_arm`), Popen replaced.
    `stub_l1`: L1 is played by that Stub (its end state, world line and goal snapshot kept as a real leg's), every later leg
    by the real run_arm, so a NON-FRESH leg's launch is seen (verifier round 3, N7)."""
    path = tmp / f"{job['chain']}.job.json"
    path.write_text(json.dumps(job), encoding="utf-8")
    FakePopen.seen = []
    saved = L5.PROFILE
    planted = {"AI_PLAYER_FAULT_NO_HINTS": "1", "POKEBOT_BOSSMODE_TOPUP": "1", "PYTHONPATH": "x",
               "AI_PLAYER_BUILD_ROOT": "elsewhere"}
    real = L5.run_arm

    def run_arm(arm, build_root, carried):
        return (stub_l1 if stub_l1 is not None and arm.name.endswith("-L1") else real)(arm, build_root, carried)
    try:
        with mock.patch.dict(os.environ, planted), mock.patch.object(L5.subprocess, "Popen", FakePopen), \
                mock.patch.object(L5, "truth_of", lambda state: (copy.deepcopy(truths.get(md5(state))), "")), \
                mock.patch.object(L5, "run_arm", run_arm), redirect_stdout(io.StringIO()):
            M.child(path)
    finally:
        L5.PROFILE = saved
    return list(FakePopen.seen)


def launch_command(job: dict, leg: dict, seen: dict, start: list[str]) -> list[str]:
    """The launcher command `run_arm` builds for this arm (`live_step5.run_arm`), with the run folder it chose."""
    run_dir = seen["command"][seen["command"].index("--run-dir") + 1]
    return [sys.executable, "-m", "ai_player", "run", "--profile", job["profile"], "--frames", str(leg["frames"]),
            "--wall-seconds", f"{float(leg['wall']):g}", "--build-root", job["build_root"], "--run-dir", run_dir, *start]


def case_t9_env(M, tmp):
    job = job_of(M, tmp / "ng", to="ch1_pokedex", seed=7201)
    seen = child_through_real_run_arm(M, job, tmp, {})
    eq(len(seen), 1, "one launch")
    env = seen[0]["env"]
    for name in ("AI_PLAYER_FAULT_NO_HINTS", "POKEBOT_BOSSMODE_TOPUP", "PYTHONPATH", "AI_PLAYER_BUILD_ROOT"):
        ok(name not in env, f"{name} from the parent reached the launch")
    eq(sorted(k for k in env if k.startswith("AI_PLAYER_")),
       sorted(["AI_PLAYER_BRAIN", "AI_PLAYER_SEED", "AI_PLAYER_PERSONALITY", "AI_PLAYER_STARTER", "AI_PLAYER_TARGET",
               "AI_PLAYER_CLOCK"]), "a fresh leg's keys")
    eq(seen[0]["command"], launch_command(job, job["legs"][0], seen[0], ["--fresh"]), "the command line, byte for byte")
    msg = refused(M, M.plan_jobs, "P1", 6601, data(), None, {"AI_PLAYER_FAULT_NO_HINTS": "1"})
    ok("AI_PLAYER_FAULT_NO_HINTS" in msg, f"plan refuses a FAULT key: {msg}")
    jobs = M.plan_jobs("P1", 6601, data())
    jobs[0]["env"] = {"AI_PLAYER_FAULT_NO_HINTS": "1"}
    ok(any("AI_PLAYER_FAULT_NO_HINTS" in p for p in M.jobs_problems(jobs)), "run refuses a FAULT key (jobs_problems)")
    # the ORCHESTRATOR's strip too (3.11; verifier round 1's V15, a NIT until round 3): the environment every child is
    # started with (`child_env`, ChildProcess's Popen env) holds none of the parent's AI_PLAYER_*, POKEBOT_* or PYTHONPATH
    planted = {"AI_PLAYER_FAULT_NO_HINTS": "1", "POKEBOT_BOSSMODE_TOPUP": "1", "PYTHONPATH": "x",
               "AI_PLAYER_BUILD_ROOT": "elsewhere"}
    with mock.patch.dict(os.environ, planted):
        env = M.child_env()
    eq(sorted(name for name in planted if name in env), [], "child_env strips the parent's variables")
    # (fix round 3's sweep, N6) a job with no legs is refused by plan and run (jobs_problems)
    jobs = M.plan_jobs("P1", 6601, data())
    jobs[0]["legs"] = []
    ok(any(p.endswith(": no legs") for p in M.jobs_problems(jobs)), "a job with no legs: refused (jobs_problems)")


def case_t9_control(M, tmp):
    stub_truths: dict = {}
    job = job_of(M, tmp / "pr", to="ch6_dewford", kind="practice", from_chapter=6, seed=7202)
    job["start"] = planted_start(M, tmp / "pr", stub_truths, goals={"tried": []})
    seen = child_through_real_run_arm(M, job, tmp, stub_truths)
    eq(len(seen), 1, "one launch")
    keys = sorted(k for k in seen[0]["env"] if k.startswith("AI_PLAYER_"))
    eq(keys, sorted(["AI_PLAYER_BRAIN", "AI_PLAYER_SEED", "AI_PLAYER_PERSONALITY", "AI_PLAYER_TARGET", "AI_PLAYER_CLOCK",
                     "AI_PLAYER_WORLD", "AI_PLAYER_GOALS"]), "a carried leg's 7 keys (the 8 less the starter)")
    eq(seen[0]["env"][ENV_GOALS], job["start"]["goals"], "the carried snapshot is the kept one")
    eq(seen[0]["command"], launch_command(job, job["legs"][0], seen[0], ["--state", job["start"]["state"]]),
       "the command line, byte for byte")
    # an MC chain's NON-FRESH leg (verifier round 2's NIT, round 3's N7: a fresh L1, the line here before, sends no
    # AI_PLAYER_GOALS in any job, so it proved nothing): L1 played by the stub KEEPS a goal snapshot, which a carrying
    # chain's L2 would send; the MC chain's L2, launched through the real run_arm from L1's kept end, sends none
    mc = job_of(M, tmp / "mc", to="ch2_wally", seed=6701, mc=True, goals="never")
    stub = Stub(mc, {})
    seen = child_through_real_run_arm(M, mc, tmp / "mc", stub.truths, stub_l1=stub)
    l1 = by_leg([r for r in M.read_records(Path(mc["out"])) if r.get("record") == "leg"])["L1"]
    ok(l1["kept"]["goals_sha256"] and l1["continue"]["go"], f"the MC chain's L1 kept a goal snapshot and went on: "
                                                              f"{l1['kept']['goals_sha256']}, {l1['continue']}")
    eq(len(seen), 1, "the MC chain's L2 launched through the real run_arm")
    ok("--state" in seen[0]["command"] and ENV_WORLD in seen[0]["env"], "L2 is a non-fresh leg (its start state and line)")
    ok(ENV_GOALS not in seen[0]["env"], "an MC chain's non-fresh L2 never sends AI_PLAYER_GOALS")
    # the orchestrator's strip keeps every other variable, and sets the child's two Python ones (3.11)
    with mock.patch.dict(os.environ, {"A1FP_HARMLESS": "kept"}):
        env = M.child_env()
    eq((env.get("A1FP_HARMLESS"), env.get("PYTHONUTF8"), env.get("PYTHONDONTWRITEBYTECODE")), ("kept", "1", "1"),
       "child_env keeps a variable off the strip list")


# ---------------------------------------------------------------------------------------------------- batch harness
class InProcessChild:
    """A stub child: runs the job in THIS process at spawn time (`run_job` with a Stub launcher), so it is done at once."""

    def __init__(self, M, job: dict, plan: dict | None, log: list | None = None) -> None:
        if log is not None:
            log.append(("spawn", job["chain"]))
        saved = L5.PROFILE
        L5.PROFILE = job["profile"]
        stub = Stub(job, plan)
        if job.get("start", {}).get("kind") in ("chain_end", "stage"):
            state = Path(job["start"]["state"])
            stub.truths[md5(state)] = {"frame": 5000, "map": [0, 3], "state_md5": md5(state),
                                       "story": {"marks": marks_through("ch5_rival_meet"), "stats": {}}}
        try:
            M.run_job(job, stub)
        finally:
            L5.PROFILE = saved
        self.pid = 0

    def poll(self):
        return 0

    def kill_tree(self):
        return None


class TimedChild:
    """A stub child that runs for `passes` polls, then writes its records (`on_end(job)`) and its job record and ends."""

    def __init__(self, M, job: dict, passes: int = 2, on_end=None, code: int = 0, die: bool = False) -> None:
        self.M, self.job, self.passes, self.on_end, self.code, self.die = M, job, passes, on_end, code, die
        self.pid = 7
        self.done = False

    def poll(self):
        if self.done:
            return self.code
        self.passes -= 1
        if self.passes > 0:
            return None
        self.done = True
        if self.on_end is not None:
            self.on_end(self.job)
        if not self.die:
            self.M.append_record(Path(self.job["out"]), self.M.job_record(self.job, [], None, None, True, True, None, []))
        return self.code

    def kill_tree(self):
        self.passes = 1


def fake_stage(M, tmp: Path, name: str = "REAL", starts: dict | None = None) -> Path:
    stage = tmp / f"stage-{name}"
    (stage / "build" / "profiles").mkdir(parents=True, exist_ok=True)
    donor(stage / "build")
    (stage / "starts").mkdir(exist_ok=True)
    manifest = {"schema_version": 1, "commit": "c0ffee", "play_digest": f"PLAY-{name}", "digest": f"ALL-{name}",
                "mutant": None, "sandbox": str(tmp / "sandbox"), "starts": {}}
    for start_id, info in (starts or {}).items():
        state = stage / "starts" / f"{start_id}_end_state.ss1"
        state.write_bytes(f"{start_id} state".encode())
        world = stage / "starts" / f"{start_id}_world.jsonl"
        world.write_text(json.dumps(world_of([[100, "0:3", "0:19", "connection", "ai", [1, 1], [2, 2], "down"]])) + "\n",
                         encoding="utf-8")
        manifest["starts"][start_id] = {"state_md5": md5(state), "world_sha256": M.sha256_of(world), **info}
    (stage / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return stage


def band_ledger(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"what": "test", "entries": [
        {"id": 1, "family": "story", "driver": "frontier_probe", "purpose": "development", "first": 2000000,
         "last": 2999999, "status": "done", "registered": None, "bounds_sha256": "x", "tree": None, "started": "t",
         "ended": "t", "verdict": "RESERVED", "evidence": None, "note": "AI trainer band"}]}), encoding="utf-8")
    return path


def batch_args(jobs_path: Path, out: Path, stages: dict[str, Path], trainer: bool = True, prediction: Path | None = None,
               **changes) -> SimpleNamespace:
    args = SimpleNamespace(jobs=str(jobs_path), out=str(out), stage=",".join(f"{k}={v}" for k, v in stages.items()),
                           trainer=trainer, ledger=None if trainer else "development",
                           prediction_file=str(prediction) if prediction else None, parallel=8, deadline=None,
                           max_wait=7200, resume=False)
    for key, value in changes.items():
        setattr(args, key, value)
    return args


class Clock:
    """The batch's planted clock: each sleep moves it at least 1 s. Past `limit` sleeps it FAILS (an AssertionError): a
    scheduler whose bound was removed (a WAIT never DROPPED, a WAIT clock that never runs, a dependency that can never
    resolve) fails its case instead of hanging the suite (verifier round 3, R3-M2: W12 and W41 hung T26 for 600 s)."""

    def __init__(self, limit: int = 2000) -> None:
        self.t = 1000.0
        self.limit, self.sleeps = limit, 0

    def __call__(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps += 1
        if self.sleeps > self.limit:
            raise AssertionError(f"the scheduler slept past {self.limit} passes: a loop that never ends (a removed bound?)")
        self.t += max(seconds, 1.0)


def batch_deps(M, tmp: Path, plans: dict | None = None, free=100.0, processes=(), spawn=None, log: list | None = None,
               limit: int = 2000, **changes):
    clock = Clock(limit)

    def default_spawn(job, job_path, log_path):
        return InProcessChild(M, job, (plans or {}).get(job["chain"]), log)

    free_fn = free if callable(free) else (lambda path: free)
    procs = processes if callable(processes) else (lambda: list(processes))
    deps = M.Deps(spawn=spawn or default_spawn, free=free_fn, processes=procs, kill=lambda pid: [pid],
                  sleep=clock.sleep, clock=clock, now=time.time, work_tree=lambda path: False,
                  stage_digest=lambda stage: f"ALL-{Path(stage).name.split('stage-', 1)[1]}",
                  sandbox_digest=lambda sandbox: "SANDBOX", seed_ledgers=lambda path: [path],
                  snapshot=lambda repo: None, ledger_path=tmp / "ledger.json", evidence_dir=tmp / "repo" / "evidence",
                  repo=tmp / "repo", poll_seconds=0.0, stagger=0.0, events=[])
    for key, value in changes.items():
        setattr(deps, key, value)
    return deps


def write_jobs(tmp: Path, jobs: list[dict], name: str = "jobs.json") -> Path:
    path = tmp / name
    path.write_text(json.dumps(jobs), encoding="utf-8")
    return path


def p1_batch(M, tmp: Path, trainer: bool = True, first: int = 2000001):
    jobs = M.plan_jobs("P1", first, data())
    stages = {"REAL": fake_stage(M, tmp, "REAL"), "WALL-OLDALE": fake_stage(M, tmp, "WALL-OLDALE")}
    return jobs, stages


def run_quiet(M, args, deps) -> int:
    from contextlib import redirect_stderr

    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return M.run_batch(args, deps)


def run_text(M, args, deps) -> tuple[int, str]:
    """`run_batch`'s exit and what it printed (its REFUSED and NOTE lines; stderr dropped)."""
    from contextlib import redirect_stderr

    printed = io.StringIO()
    with redirect_stdout(printed), redirect_stderr(io.StringIO()):
        code = M.run_batch(args, deps)
    return code, printed.getvalue()


def refusal_of(M, args, deps) -> tuple[int, str]:
    """`run_text` for a batch that must be REFUSED: an exception out of run_batch (an unguarded crash, `main`'s exit 5) FAILS
    the case as an AssertionError naming it, never as a crash of the suite (a refusal is exit 2, 3.2)."""
    try:
        return run_text(M, args, deps)
    except Exception as error:  # noqa: BLE001
        raise AssertionError(f"run_batch CRASHED instead of refusing: {type(error).__name__}: {error}") from None


# ---------------------------------------------------------------------------------------------------- T10: the trainer writes nothing tracked
def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "-c",
                           "commit.gpgsign=false", "-c", "core.autocrlf=false", *args], capture_output=True, text=True,
                          timeout=120)
    if done.returncode != 0:
        raise AssertionError(f"git {args}: {done.stderr[:300]}")
    return done.stdout


def temp_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "ai_player" / "gates").mkdir(parents=True)
    (repo / "ai_player" / "evidence" / "trees").mkdir(parents=True)
    band_ledger(repo / "ai_player" / "gates" / "ledger.json")
    (repo / "ai_player" / "evidence" / "old.txt").write_text("old evidence\n", encoding="utf-8")
    (repo / "ai_player" / "evidence" / "trees" / "old.zip").write_bytes(b"zip")
    git(tmp, "init", "-q", str(repo))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a temp repository")
    return repo


def status(repo: Path) -> str:
    return git(repo, "status", "--porcelain", "--untracked-files=all")


def repo_deps(M, tmp: Path, repo: Path, **changes):
    deps = batch_deps(M, tmp, **changes)
    deps.repo, deps.ledger_path, deps.evidence_dir = repo, repo / "ai_player" / "gates" / "ledger.json", \
        repo / "ai_player" / "evidence"
    deps.snapshot = M._snapshot
    return deps


def case_t10_trainer(M, tmp):
    repo = temp_repo(tmp)
    before = status(repo)
    jobs, stages = p1_batch(M, tmp)
    code = run_quiet(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stages), repo_deps(M, tmp, repo))
    eq(code, 0, "the trainer batch ran")
    eq(status(repo), before, "git status --porcelain --untracked-files=all unchanged")
    boom = mock.Mock(side_effect=RuntimeError("must not be called"))
    with mock.patch.object(M.ledger, "begin", boom), mock.patch.object(M.ledger, "finish", boom):
        deps = repo_deps(M, tmp, repo)
        deps.snapshot = boom
        eq(run_quiet(M, batch_args(write_jobs(tmp, jobs, "j2.json"), tmp / "out2", stages), deps), 0,
           "the trainer passes with begin, finish and snapshot_tree raising")


def case_t10_control(M, tmp):
    repo = temp_repo(tmp)
    before = status(repo)
    jobs = M.plan_jobs("P1", 7601, data())
    stages = {"REAL": fake_stage(M, tmp, "REAL"), "WALL-OLDALE": fake_stage(M, tmp, "WALL-OLDALE")}
    prediction = tmp / "prediction.txt"
    prediction.write_text("P1 predicted\n", encoding="utf-8")
    code = run_quiet(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stages, trainer=False, prediction=prediction),
                     repo_deps(M, tmp, repo))
    eq(code, 0, "the development batch ran")
    ok(status(repo) != before, "development mode writes its entry and evidence")
    boom = mock.Mock(side_effect=RuntimeError("raised"))
    with mock.patch.object(M.ledger, "begin", boom):
        deps = repo_deps(M, tmp, repo)
        deps.snapshot = boom
        try:
            run_quiet(M, batch_args(write_jobs(tmp, M.plan_jobs("P1", 7701, data()), "j3.json"), tmp / "out3", stages,
                                    trainer=False, prediction=prediction), deps)
        except RuntimeError:
            return
    raise AssertionError("development did not raise with begin and snapshot_tree raising")


# ---------------------------------------------------------------------------------------------------- T11: placement
def case_t11_placement(M, tmp):
    repo = temp_repo(tmp)
    (repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    ledger_path = band_ledger(tmp / "ledger.json")
    start = ledger_path.read_bytes()
    jobs, stages = p1_batch(M, tmp)
    path = write_jobs(tmp, jobs)
    real_tree = {"work_tree": M.inside_work_tree}
    prediction = tmp / "p.txt"
    prediction.write_text("x\n", encoding="utf-8")
    dev_path = write_jobs(tmp, M.plan_jobs("P1", 7601, data()), "dev.json")
    learner = fake_stage(M, tmp / "lr", "REAL")
    manifest = json.loads((learner / "manifest.json").read_text(encoding="utf-8"))
    manifest["sandbox"] = str(tmp / "pokebot-learner" / "sandbox-pokebot")
    (learner / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    # VALID stages (each manifest.json reads) inside the temp work tree, one in a plain folder and one in a git-IGNORED
    # folder, so only the placement check can refuse them (verifier round 1, F2: the stage planted before had no manifest,
    # so manifest_problems refused it whatever its placement)
    tracked, ignored = fake_stage(M, repo / "tracked", "REAL"), fake_stage(M, repo / "ignored", "REAL")
    eq([M.manifest_problems(stage)[1] for stage in (tracked, ignored)], [[], []], "both planted stages are valid stages")
    git(repo, "check-ignore", "-q", str(ignored / "manifest.json"))  # raises unless git ignores it: the arm is real
    (tmp / "empty-stage").mkdir(exist_ok=True)
    wrong: list[str] = []
    for name, out, stage_map in (("--out in a work tree", repo / "tracked" / "out", stages),
                                 ("--out in an ignored folder of a work tree", repo / "ignored" / "out", stages),
                                 ("a stage whose sandbox lies in a pokebot-learner folder", tmp / "o5",
                                  {**stages, "REAL": learner}),
                                 ("--out in a pokebot-learner folder", tmp / "pokebot-learner" / "out", stages),
                                 ("a stage in a work tree", tmp / "o3", {**stages, "REAL": tracked}),
                                 ("a stage in an ignored folder of a work tree", tmp / "o6", {**stages, "REAL": ignored}),
                                 ("a stage without a manifest", tmp / "o4", {**stages, "REAL": tmp / "empty-stage"})):
        for mode, jobs_path, extra in (("trainer", path, {}), ("development", dev_path,
                                                               {"trainer": False, "prediction": prediction})):
            ledger_path.write_bytes(start)  # every arm from the same ledger, in its own --out: one arm never refuses the next
            code = run_quiet(M, batch_args(jobs_path, out / mode, stage_map, **extra), batch_deps(M, tmp, **real_tree))
            written = ledger_path.read_bytes() != start
            if code != 2 or written:
                wrong.append(f"{name} ({mode}): exit {code}{', a ledger write' if written else ''}")
    eq(wrong, [], "every placement FAULT refused (exit 2) with no ledger write")
    # verifier round 3 (N1, N4, N7): a job whose stage is not given; an EMPTY job list (refused BEFORE --out is made); --out
    # or a stage AT or UNDER the graded chapter 1-5 folder (3.14; a temp folder stands in for GRADED_CH5): each refused by
    # run_batch (exit 2) with no ledger write and no launch, its REFUSED line naming why
    graded = tmp / "graded-ch5"
    under = fake_stage(M, graded / "st", "REAL")
    spawned: list = []
    with mock.patch.object(M, "GRADED_CH5", graded):
        for name, jobs_path, out, stage_map, why in (
                ("a job whose stage is not given", path, tmp / "o7", {"REAL": stages["REAL"]},
                 "its stage 'WALL-OLDALE' is not given"),
                ("an empty job list", write_jobs(tmp, [], "empty.json"), tmp / "o8", stages, "--jobs holds no job"),
                ("--out under the graded folder", path, graded / "out", stages, "lies at or under"),
                ("--out AT the graded folder", path, graded, stages, "lies at or under"),
                ("a stage under the graded folder", path, tmp / "o9", {**stages, "REAL": under}, "lies at or under")):
            ledger_path.write_bytes(start)
            made = out.exists()
            code, text = refusal_of(M, batch_args(jobs_path, out, stage_map), batch_deps(M, tmp, log=spawned))
            eq((code, ledger_path.read_bytes() == start, spawned), (2, True, []),
               f"{name}: refused, no ledger write, no launch")
            ok("REFUSED: " in text and why in text, f"{name}: the refusal names it: {text[-400:]}")
            ok(made or not out.exists(), f"{name}: --out never made")
    # (fix round 3's bounded sweep of the refusal family, N6) a --stage not in the ARM=DIR form, a --jobs file that is not a
    # JSON list, and a stage whose manifest.json is of another schema: each refused, exit 2, no ledger write, no launch
    other_schema = fake_stage(M, tmp / "schema", "REAL")
    manifest = json.loads((other_schema / "manifest.json").read_text(encoding="utf-8"))
    manifest["schema_version"] = 2
    (other_schema / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    not_list = tmp / "dict.json"
    not_list.write_text(json.dumps({"jobs": []}), encoding="utf-8")
    for name, args, why in (
            ("a --stage with no ARM=DIR", batch_args(path, tmp / "o10", stages, stage="REAL"), "ARM=DIR"),
            ("a --jobs file that is not a JSON list", batch_args(not_list, tmp / "o11", stages), "is not a JSON list of jobs"),
            ("a stage manifest of another schema", batch_args(path, tmp / "o12", {**stages, "REAL": other_schema}),
             "has schema 2")):
        ledger_path.write_bytes(start)
        code, text = refusal_of(M, args, batch_deps(M, tmp, log=spawned))
        eq((code, ledger_path.read_bytes() == start, spawned), (2, True, []), f"{name}: refused, no ledger write, no launch")
        ok("REFUSED: " in text and why in text, f"{name}: the refusal names it: {text[-400:]}")


def case_t11_control(M, tmp):
    band_ledger(tmp / "ledger.json")
    jobs, stages = p1_batch(M, tmp)
    eq(run_quiet(M, batch_args(write_jobs(tmp, jobs), tmp / "outside" / "out", stages),
                 batch_deps(M, tmp, work_tree=M.inside_work_tree)), 0, "outside every work tree: accepted")
    # the graded-folder check is a PATH check (verifier round 3, N7): a sibling of the graded folder, and one whose name
    # merely BEGINS with the graded folder's name, are accepted
    graded = tmp / "graded-ch5"
    with mock.patch.object(M, "GRADED_CH5", graded):
        eq([M.placement_problems(p, "--out", lambda path: False)
            for p in (tmp / "graded-ch4" / "out", tmp / "graded-ch5-other" / "out")], [[], []],
           "a sibling of the graded folder, and graded-ch5-other: accepted")


# ---------------------------------------------------------------------------------------------------- T12: the seed band
def case_t12_band(M, tmp):
    data_band = json.loads(band_ledger(tmp / "l1.json").read_text(encoding="utf-8"))
    ok(M.trainer_problems([1999999], data_band), "a trainer seed outside the band")
    ok(M.trainer_problems([2000001], {"entries": []}), "no band row")
    registered = copy.deepcopy(data_band)
    registered["entries"].append({"id": 2, "family": "story", "purpose": "graded", "first": 2000001, "last": 2000002,
                                  "status": "registered"})
    ok(M.trainer_problems([2000001], registered), "an overlapping registered entry")
    path = band_ledger(tmp / "l2.json")
    try:
        ledger.register("story", "x", 2000010, 2000020, "b", path=path)
    except ledger.Refused:
        pass
    else:
        raise AssertionError("register inside the band was accepted")
    path3 = tmp / "l3.json"
    M.reserve_band(path3)
    refused(M, M.reserve_band, path3)
    # THE WIRING (verifier round 3, R3-M1 b: the lines above call trainer_problems alone): run_batch itself refuses a
    # --trainer batch with a seed outside the band, or whose ledger holds no band row: exit 2, no ledger write, no launch
    stages = {"REAL": fake_stage(M, tmp, "REAL")}
    for i, (name, first, band, why) in enumerate((
            ("a seed outside the band", 1999999, True, "REFUSED: the trainer seed 1999999 lies outside the band"),
            ("no band row", 2000001, False, "REFUSED: the ledger holds no band row"))):
        arm = tmp / f"wired{i}"
        arm.mkdir()
        if band:
            band_ledger(arm / "ledger.json")
        else:
            (arm / "ledger.json").write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
        start = (arm / "ledger.json").read_bytes()
        jobs = [job for job in M.plan_jobs("P1", first, data()) if job["stage"] == "REAL"][:1]
        spawned: list = []
        code, text = refusal_of(M, batch_args(write_jobs(arm, jobs), arm / "out", stages), batch_deps(M, arm, log=spawned))
        eq((code, (arm / "ledger.json").read_bytes() == start, spawned), (2, True, []),
           f"{name}: refused by run_batch, no ledger write, no launch")
        ok(why in text, f"{name}: the refusal names it: {text[-400:]}")


def case_t12_control(M, tmp):
    data_band = json.loads(band_ledger(tmp / "l1.json").read_text(encoding="utf-8"))
    eq(M.trainer_problems([2000001, 2000002], data_band), [], "inside the band: accepted")
    # the wiring's CONTROL (verifier round 3, R3-M1 b): a --trainer batch inside the band, its ledger holding the band row,
    # runs through run_batch (exit 0) and never writes the ledger
    stages = {"REAL": fake_stage(M, tmp, "REAL")}
    arm = tmp / "wired"
    arm.mkdir()
    band_ledger(arm / "ledger.json")
    start = (arm / "ledger.json").read_bytes()
    jobs = [job for job in M.plan_jobs("P1", 2000001, data()) if job["stage"] == "REAL"][:1]
    spawned: list = []
    eq((run_quiet(M, batch_args(write_jobs(arm, jobs), arm / "out", stages), batch_deps(M, arm, log=spawned)),
        (arm / "ledger.json").read_bytes() == start, spawned), (0, True, [("spawn", jobs[0]["chain"])]),
       "inside the band with its row: run, the ledger never written")
    path = band_ledger(tmp / "l2.json")
    ledger.register("story", "x", 7000, 7001, "b", path=path)
    path3 = tmp / "l3.json"
    entry = M.reserve_band(path3)
    entries = ledger.load(path3)["entries"]
    eq(len(entries), 1, "reserve-band writes one row")
    eq((entries[0]["status"], entries[0]["note"], entries[0]["verdict"]), ("done", M.BAND_NOTE, M.BAND_VERDICT), "the row")
    eq(ledger.check(ledger.load(path3)), [], "ledger.py --check passes")
    eq(M.trainer_problems([2000001], ledger.load(path3)), [], "the trainer accepts")
    eq(entry["id"], 1, "the entry")


# ---------------------------------------------------------------------------------------------------- T13: development seeds
def case_t13_seeds(M, tmp):
    path = tmp / "ledger.json"
    path.write_text(json.dumps({"what": "", "entries": [
        {"id": 9, "family": "story", "driver": "x", "purpose": "development", "first": 7602, "last": 7602,
         "status": "done"}]}), encoding="utf-8")
    start = path.read_bytes()
    jobs = M.plan_jobs("P1", 7601, data())
    stages = {"REAL": fake_stage(M, tmp, "REAL"), "WALL-OLDALE": fake_stage(M, tmp, "WALL-OLDALE")}
    prediction = tmp / "p.txt"
    prediction.write_text("x\n", encoding="utf-8")
    code = run_quiet(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stages, trainer=False, prediction=prediction),
                     batch_deps(M, tmp))
    eq(code, 2, "a seed named by an entry")
    eq(path.read_bytes(), start, "no ledger write")
    order: list = []
    real_begin = ledger.begin

    def begin(*args, **kwargs):
        order.append(("begin", None))
        return real_begin(*args, **kwargs)
    path.write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
    with mock.patch.object(M.ledger, "begin", begin):
        code = run_quiet(M, batch_args(write_jobs(tmp, jobs, "j2.json"), tmp / "out2", stages, trainer=False,
                                       prediction=prediction), batch_deps(M, tmp, log=order))
    eq(code, 0, "fresh seeds ran")
    eq(order[0][0], "begin", f"begin BEFORE the first launch: {order[:3]}")
    # the seed check's two refusals no case reached before (verifier round 2, R2-M2; 2.5, 3.10): a seed ledger that
    # cannot be read and is NOT a known non-ledger, and seeds that are not ONE contiguous range; each refused (exit 2)
    # with no ledger write and no launch, its REFUSED line naming why
    path.write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
    start = path.read_bytes()
    broken = tmp / "elsewhere" / "ai_player" / "gates" / "ledger.json"
    broken.parent.mkdir(parents=True)
    broken.write_text('{"what": "", "entries": [', encoding="utf-8")  # cut off mid-file: not JSON
    spawned: list = []
    code, text = run_text(M, batch_args(write_jobs(tmp, jobs, "j3.json"), tmp / "out3", stages, trainer=False,
                                        prediction=prediction),
                          batch_deps(M, tmp, log=spawned, seed_ledgers=lambda own: [own, broken]))
    eq((code, path.read_bytes() == start, spawned), (2, True, []),
       "an unreadable ledger that is no known non-ledger: refused, no ledger write, no launch")
    ok(f"REFUSED: a ledger could not be read: {broken}: JSONDecodeError" in text, f"the refusal names it: {text[-500:]}")
    gap = [job for job in jobs if job["seed"] != 7602]
    eq(sorted({job["seed"] for job in gap}), [7601, 7603], "the planted seeds")
    code, text = run_text(M, batch_args(write_jobs(tmp, gap, "j4.json"), tmp / "out4", stages, trainer=False,
                                        prediction=prediction), batch_deps(M, tmp, log=spawned))
    eq((code, path.read_bytes() == start, spawned), (2, True, []),
       "seeds 7601 and 7603 (not ONE contiguous range): refused, no ledger write, no launch")
    ok("REFUSED: development seeds must be ONE contiguous range" in text, f"the refusal names it: {text[-500:]}")
    # development mode needs --prediction-file (3.10; verifier round 3, N1): without one, refused (exit 2), no ledger
    # write, no launch
    code, text = refusal_of(M, batch_args(write_jobs(tmp, jobs, "j5.json"), tmp / "out5", stages, trainer=False),
                            batch_deps(M, tmp, log=spawned))
    eq((code, path.read_bytes() == start, spawned), (2, True, []),
       "development mode with no --prediction-file: refused, no ledger write, no launch")
    ok("REFUSED: development mode needs --prediction-file" in text, f"the refusal names it: {text[-500:]}")
    # (fix round 3's sweep, N6) a prediction file holding only white space: refused, no ledger write, no launch
    blank = tmp / "blank.txt"
    blank.write_text("  \n", encoding="utf-8")
    code, text = refusal_of(M, batch_args(write_jobs(tmp, jobs, "j6.json"), tmp / "out6", stages, trainer=False,
                                          prediction=blank), batch_deps(M, tmp, log=spawned))
    eq((code, path.read_bytes() == start, spawned), (2, True, []), "an empty prediction file: refused, no ledger write")
    ok("REFUSED: the prediction file is empty" in text, f"the refusal names it: {text[-500:]}")


def case_t13_control(M, tmp):
    path = tmp / "ledger.json"
    path.write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
    jobs = M.plan_jobs("P1", 7601, data())
    stages = {"REAL": fake_stage(M, tmp, "REAL"), "WALL-OLDALE": fake_stage(M, tmp, "WALL-OLDALE")}
    prediction = tmp / "p.txt"
    prediction.write_text("x\n", encoding="utf-8")
    # a seed ledger that cannot be read at a path ending in the KNOWN non-ledger (2.5: the export cut off on 2026-11-13)
    # is LISTED (a NOTE line, batch.json's known_non_ledgers) and ALLOWED (verifier round 2, R2-M2's CONTROL)
    known = tmp.joinpath(*M.KNOWN_NON_LEDGERS[0].split("/"))
    known.parent.mkdir(parents=True)
    known.write_text('{"what": "", "entries": [', encoding="utf-8")
    code, text = run_text(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stages, trainer=False, prediction=prediction),
                          batch_deps(M, tmp, seed_ledgers=lambda own: [own, known]))
    eq(code, 0, "ran beside a known non-ledger that cannot be read")
    ok(f"NOTE: a known non-ledger could not be read (allowed, 2.5): {known}: JSONDecodeError" in text,
       f"the known non-ledger is listed: {text[:500]}")
    eq(json.loads((tmp / "out" / M.BATCH_FILE).read_text(encoding="utf-8")).get("known_non_ledgers"),
       [f"{known}: JSONDecodeError"], "and listed in batch.json")
    entries = ledger.load(path)["entries"]
    eq([(e["first"], e["last"], e["status"], e["purpose"]) for e in entries], [(7601, 7603, "done", "development")],
       "one begin, one finish")
    ok(entries[0]["verdict"].startswith("DEVELOPMENT, never graded"), entries[0]["verdict"])


# ---------------------------------------------------------------------------------------------------- T14: the disk
def tick_job(M, tmp: Path, mc: bool = False) -> dict:
    job = job_of(M, tmp, to="ch1_pokedex", mc=mc, seed=6701 if mc else 7301, goals="never" if mc else "carry")
    job["watchdog_seconds"] = 10 ** 9
    return job


class Running:
    pid = 99

    def poll(self):
        return None

    def kill_tree(self):
        return None


def one_tick(M, tmp: Path, job: dict, world=None, profile=0, free=100.0, out_bytes=0):
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    killed: list = []
    folder = f"20261114-000001-{job['chain']}-L1"

    def sizes(path):
        return out_bytes if Path(path) == out else profile
    deps = batch_deps(M, tmp, free=free, kill=lambda pid: killed.append(pid) or [pid],
                      newest_world=lambda runs: (folder, world), folder_bytes=sizes)
    state = {"aborted": False, "ai_stop": False, "out_over": False, "last_stage": deps.clock(),
             "last_sandbox": deps.clock(), "last_pass": None}
    M.tick([(job, Running(), deps.clock())], out, {}, {}, {}, state, deps)
    marker = LC.guard_mark(out, job["chain"], "L1")
    return state, marker, killed


def disk_batch(M, tmp: Path, free_at_tick: float = 100.0, out_bytes: int = 0,
               spawn_raises: bool = False, mc: bool = False) -> SimpleNamespace:
    """Two plain jobs at P 1 through the REAL `run_batch` in development mode (a temp ledger and evidence folder; stub
    children that end at their third poll, or at their next poll once killed, then with no job record): the TICK of the
    pass that launched the first job reads `free_at_tick` GB free while the second job is still PENDING (every other free
    reading is 100.0 GB, so the disk reservation never holds the second job), and --out's size reads `out_bytes`
    throughout. `spawn_raises`: the first launch raises, after `ledger.begin` (a harness error). The guard's TERMINAL
    consequences (verifier round 2, R2-M1; 2.7, 3.2): who launched, who was dropped and why, who was killed, the exit and
    the entry's verdict. `mc`: the two jobs are MC jobs (the first two of an MC plan, seeds 6741-6742; fix round 5)."""
    (tmp / "ledger.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp / "ledger.json").write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
    jobs = M.plan_jobs("MC", 6741, data(), to="ch1_pokedex")[:2] if mc else plain_jobs(M, 2, first=7601)
    stages = {"REAL": fake_stage(M, tmp, "REAL")}
    prediction = tmp / "p.txt"
    prediction.write_text("x\n", encoding="utf-8")
    out = (tmp / "out").resolve()
    seen = SimpleNamespace(spawned=[], killed=[], handles={}, dip=None, out_reads=[], result=None)
    in_tick = {"now": False, "used": False}
    real_tick, real_drive = M.tick, M.drive

    def tick(running, *rest):
        in_tick["now"] = bool(running) and not in_tick["used"]  # the first tick that has a running job
        try:
            return real_tick(running, *rest)
        finally:
            in_tick["used"] = in_tick["used"] or in_tick["now"]
            in_tick["now"] = False

    def free(path):
        if in_tick["now"]:
            seen.dip = (free_at_tick, list(seen.spawned))
            return free_at_tick
        return 100.0

    def sizes(path):
        if Path(path).resolve() == out:
            seen.out_reads.append((out_bytes, len(seen.spawned)))
            return out_bytes
        return 0

    def spawn(job, job_path, log_path):
        if spawn_raises:
            raise RuntimeError("a planted harness failure after ledger.begin")
        seen.spawned.append(job["chain"])
        handle = TimedChild(M, job, passes=3)
        handle.pid = 100 + len(seen.spawned)
        seen.handles[handle.pid] = handle
        return handle

    def kill(pid):
        seen.killed.append(pid)
        seen.handles[pid].die = True  # a killed child writes no job record: the orchestrator salvages it
        seen.handles[pid].kill_tree()
        return [pid]

    def drive(*args, **kwargs):
        seen.result = real_drive(*args, **kwargs)
        return seen.result
    deps = batch_deps(M, tmp, spawn=spawn, free=free, kill=kill, folder_bytes=sizes)
    args = batch_args(write_jobs(tmp, jobs), out, stages, trainer=False, prediction=prediction, parallel=1, max_wait=30)
    with mock.patch.object(M, "tick", tick), mock.patch.object(M, "drive", drive):
        seen.code = run_quiet(M, args, deps)
    entries = ledger.load(tmp / "ledger.json")["entries"]
    seen.entry = entries[0] if len(entries) == 1 else {"verdict": f"{len(entries)} entries"}
    seen.verdict = str(seen.entry.get("verdict") or "")
    seen.chains = [job["chain"] for job in jobs]
    seen.dropped = dict((seen.result or {}).get("not_started") or [])
    seen.out = out
    return seen


def case_t14_disk(M, tmp):
    eq(M.start_refusal(44.99) is not None, True, "44.99 GB at start")
    eq(M.disk_decision(None, 39.99, None), "abort", "39.99 GB")
    eq(M.disk_decision(1_000_000_001, 50.0, None), "cut-world", "a world of 1,000,000,001 bytes")
    eq(M.disk_decision(None, 50.0, 5_000_000_001), "drop", "--out 5,000,000,001")
    eq(M.disk_decision(None, 50.0, 0, 1_250_000_001), "cut-profile", "a profile folder of 1,250,000,001 bytes")
    eq(M.parallel_of(8, 44.0)[0], 0, "P_fit 0: refused")
    eq(M.disk_decision(1_500_000_001, 50.0, None, mc=True), "cut-world", "an MC world of 1,500,000,001")
    eq(M.disk_decision(None, 50.0, 0, 1_750_000_001, mc=True), "cut-profile", "an MC profile folder of 1,750,000,001")
    state, marker, killed = one_tick(M, tmp / "a", tick_job(M, tmp / "a"), free=39.99)
    ok(state["aborted"] and killed, "the tick ABORTS at 39.99 GB and kills the running launch")
    _, marker, killed = one_tick(M, tmp / "b", tick_job(M, tmp / "b"), world=1_000_000_001)
    eq((marker or {}).get("cause"), "world", "the tick cuts a 1,000,000,001-byte world")
    state, _, _ = one_tick(M, tmp / "c", tick_job(M, tmp / "c"), out_bytes=5_000_000_001)
    ok(state["out_over"], "the tick drops the pending jobs over the --out cap")
    _, marker, _ = one_tick(M, tmp / "d", tick_job(M, tmp / "d"), profile=1_250_000_001)
    eq((marker or {}).get("cause"), "profile", "the tick cuts a profile folder of 1,250,000,001 bytes")
    _, marker, _ = one_tick(M, tmp / "e", tick_job(M, tmp / "e", mc=True), profile=1_750_000_001)
    eq((marker or {}).get("cause"), "profile", "the tick cuts an MC profile folder of 1,750,000,001 bytes")
    _, marker, killed = one_tick(M, tmp / "g", tick_job(M, tmp / "g", mc=True), world=1_500_000_001)
    eq(((marker or {}).get("cause"), bool(killed)), ("world", True),
       "the tick cuts an MC world of 1,500,000,001 bytes (live_chain's own guard, 3.12)")
    # THE CLASS of a leg the probe's guard killed (3.5: the kill marker is judged before any verdict rule). A killed launch
    # leaves no verdict file (exit 1 here): without its marker that end is the AI's own NOT CLEAN, which counts toward the
    # AI-only stop (T14's CONTROL); with a world or profile marker it is CUT-WORLD (it resets the stop), with the disk
    # guard's ABORT marker INFRA (neither counts nor resets). Verifier round 1, F3: no case read the class before.
    killed_end = {"no_verdict": True, "exit": 1}
    four = [leg_record(f"n{i}", M.NOT_CLEAN, float(i)) for i in range(4)]
    arms = (("world", False, (M.CUT_WORLD, M.CUT_TEXT)), ("profile", False, (M.CUT_WORLD, M.CUT_PROFILE_TEXT)),
            ("world", True, (M.CUT_WORLD, M.CUT_TEXT_MC)), ("abort", False, (M.INFRA, "the disk guard's ABORT killed the launch")))
    for i, (cause, mc, want) in enumerate(arms):
        eq(M.classify(facts(guard=cause, mc=mc, exit=1, verdict=None)), want, f"classify: a {cause} kill marker (MC {mc})")
        job = job_of(M, tmp / f"k{i}", to="ch1_pokedex", seed=(6708 if mc else 7310 + i), mc=mc,
                     goals="never" if mc else "carry")
        _, _, records = play(M, job, {"L1": {**killed_end, "after": guard_after(Path(job["out"]), job["chain"], cause)}})
        eq((records[0]["class"], records[0]["class_why"]), want, f"a leg the {cause} guard killed (MC {mc})")
        eq(M.ai_stop_streak(four + [{**records[0], "ended": 9.0}]), 4 if want[0] == M.INFRA else 0,
           f"a leg the {cause} guard killed: {'INFRA neither counts nor resets' if want[0] == M.INFRA else 'CUT-WORLD resets'} "
           f"the AI-only stop")
    band = band_ledger(tmp / "ledger.json").read_bytes()
    _, stages = p1_batch(M, tmp / "f")
    prediction = tmp / "p.txt"
    prediction.write_text("x\n", encoding="utf-8")
    spawned: list = []
    eq(run_quiet(M, batch_args(write_jobs(tmp, M.plan_jobs("P1", 7601, data())), tmp / "fout", stages, trainer=False,
                               prediction=prediction), batch_deps(M, tmp, free=44.99, log=spawned)), 2,
       "44.99 GB at start: refused")
    eq(((tmp / "ledger.json").read_bytes(), spawned), (band, []), "no launch, no ledger write")
    # THE BATCH'S ENDS, through the real run_batch (verifier round 2, R2-M1: the lines above stop at the tick's flags).
    # 2.7: an abort is no launch, the running launches killed, ABORT.txt, the entry ABORTED; 3.2: exit 3 ABORTED, exit 4
    # a harness ERROR after ledger.begin; 2.7 and 3.13: --out over its cap DROPS the pending jobs
    a = disk_batch(M, tmp / "ba", free_at_tick=39.99)
    first, second = a.chains
    eq(a.dip, (39.99, [first]), "the tick read 39.99 GB with the second job still pending")
    eq(a.spawned, [first], "39.99 GB: the pending job is never launched")
    ok(a.dropped.get(second, "").startswith("ABORT.txt"), f"the pending job DROPPED by the ABORT: {a.dropped}")
    ok((a.out / M.ABORT_FILE).is_file(), "ABORT.txt written")
    eq(a.killed, [101], "the running launch killed")
    eq(a.code, 3, "an ABORTED batch exits 3")
    ok(a.verdict.startswith("ABORTED"), f"the entry is finished ABORTED: {a.verdict!r}")
    # (fix round 5, verifier round 4's V4-N1 = H02) an ABORTED MC batch's entry names the merge check's reading, as
    # finish_verdict writes it; the CONTROL beside it: an aborted batch that is not MC names none
    amc = disk_batch(M, tmp / "bamc", free_at_tick=39.99, mc=True)
    eq((amc.code, amc.spawned, amc.killed), (3, [amc.chains[0]], [101]), "an MC batch ABORTED by the disk tick")
    ok(amc.verdict.startswith(f"ABORTED (disk: under 40 GB free): {MC_READS} STOP over ")
       and f"{amc.chains[0]} L1: not run" in amc.verdict, f"an ABORTED MC entry names its reading: {amc.verdict!r}")
    ok(MC_READS not in a.verdict and "MERGE CHECK" not in a.verdict,
       f"an ABORTED batch that is not MC names no merge-check reading: {a.verdict!r}")
    b = disk_batch(M, tmp / "bb", out_bytes=5_000_000_001)
    ok((5_000_000_001, 1) in b.out_reads, f"--out read 5,000,000,001 bytes with the second job pending: {b.out_reads}")
    eq(b.spawned, [b.chains[0]], "--out over its cap: the pending job is never launched")
    ok(b.dropped.get(b.chains[1], "").startswith("--out is over its cap"), f"DROPPED by the cap: {b.dropped}")
    eq(b.killed, [], "the cap drops the pending jobs and kills no running one")
    c = disk_batch(M, tmp / "bc", spawn_raises=True)
    eq(c.code, 4, "a harness error after ledger.begin exits 4")
    ok(c.verdict.startswith("ERROR (harness: RuntimeError"), f"the entry is finished as ERROR: {c.verdict!r}")
    # (fix round 3's sweep, N6) the start floor drive by drive: the free space unreadable; ONLY a stage's drive under 45 GB;
    # ONLY --out's drive under 45 GB: each refused (exit 2), no ledger write, no launch (the 44.99 GB arm above lowers both)
    jobs = [job for job in M.plan_jobs("P1", 2000001, data()) if job["stage"] == "REAL"][:1]
    stages = {"REAL": fake_stage(M, tmp / "fl", "REAL")}
    spawned = []
    for i, (name, free, why) in enumerate((
            ("the free space unreadable", lambda path: None, "REFUSED: the stage REAL's drive: the free space could not be read"),
            ("a stage's drive under 45 GB", lambda path: 44.99 if "stage-" in str(path) else 100.0,
             "REFUSED: the stage REAL's drive: 44.99 GB free"),
            ("--out's drive under 45 GB", lambda path: 100.0 if "stage-" in str(path) else 44.99,
             "REFUSED: --out's drive: 44.99 GB free"))):
        code, text = refusal_of(M, batch_args(write_jobs(tmp, jobs, f"floor{i}.json"), tmp / f"floor{i}", stages),
                                batch_deps(M, tmp, free=free, log=spawned))
        eq((code, (tmp / "ledger.json").read_bytes(), spawned), (2, band, []), f"{name}: refused, no ledger write, no launch")
        ok(why in text, f"{name}: the refusal names it: {text[-400:]}")


def case_t14_control(M, tmp):
    # the TICK at every boundary FIRST: it asks disk_decision about each measurement (verifier round 1, F1), so a boundary
    # broken there fails HERE, on the code a batch runs, before the unit lines below
    state, marker, killed = one_tick(M, tmp / "a", tick_job(M, tmp / "a"), world=1_000_000_000, profile=1_250_000_000,
                                     free=40.0, out_bytes=5_000_000_000)
    ok(not state["aborted"] and not state["out_over"] and marker is None and not killed, "every boundary passes")
    for i, (name, world, profile) in enumerate((("an MC world of 1,000,000,001 bytes (over A1's cut)", 1_000_000_001, 0),
                                                ("an MC world of 1,500,000,000 bytes", 1_500_000_000, 0),
                                                ("an MC profile folder of 1,750,000,000 bytes", None, 1_750_000_000))):
        _, marker, killed = one_tick(M, tmp / f"mc{i}", tick_job(M, tmp / f"mc{i}", mc=True), world=world, profile=profile)
        ok(marker is None and not killed, f"the tick keeps {name}")
    eq(M.start_refusal(45.0), None, "45.0 GB starts")
    eq(M.disk_decision(None, 40.0, None), None, "40.0 GB no abort")
    eq(M.disk_decision(1_000_000_000, 50.0, None), None, "1,000,000,000 kept")
    eq(M.disk_decision(None, 50.0, 5_000_000_000), None, "--out 5,000,000,000 launches")
    eq(M.disk_decision(None, 50.0, 0, 1_250_000_000), None, "a profile folder of 1,250,000,000 kept")
    eq(M.p_fit(53.0), 8, "P_fit exactly 8")
    eq(M.parallel_of(8, 53.0), (8, None), "P_fit 8 runs 8")
    eq(M.disk_decision(1_000_000_001, 50.0, None, mc=True), None, "an MC world of 1,000,000,001 kept")
    eq(M.disk_decision(1_500_000_000, 50.0, None, mc=True), None, "an MC world of 1,500,000,000 kept")
    eq(M.disk_decision(None, 50.0, 0, 1_750_000_000, mc=True), None, "an MC profile folder of 1,750,000,000 kept")
    # no kill marker: the same killed-looking end (exit 1, no verdict file) is the AI's own NOT CLEAN, never CUT-WORLD or
    # INFRA (so the marker, not the end's shape, is what T14's FAULT classes)
    eq(M.classify(facts(exit=1, verdict=None)), (M.NOT_CLEAN, "exit 1 with no verdict file"), "no marker: NOT CLEAN")
    job = job_of(M, tmp / "k", to="ch1_pokedex", seed=7320)
    _, _, records = play(M, job, {"L1": {"no_verdict": True, "exit": 1}})
    eq(records[0]["class"], M.NOT_CLEAN, "a leg with no kill marker keeps its own class")
    runs = tmp / "runs"
    (runs / "20261114-000001-X-L1").mkdir(parents=True)
    (runs / "20261114-000001-X-L1" / "world.jsonl").write_bytes(b"x" * 10)
    (runs / "20261114-000002-X-L2").mkdir()
    eq(LC.newest_world(runs), ("20261114-000002-X-L2", None), "an older folder's world kills nothing")
    # THE BATCH at the boundaries (verifier round 2, R2-M1): the tick reads 40.0 GB free and --out at 5,000,000,000 bytes
    # with the second job still pending: no ABORT and no DROP, every job launches, exit 0, the entry a DEVELOPMENT one
    c = disk_batch(M, tmp / "bc", free_at_tick=40.0, out_bytes=5_000_000_000)
    eq(c.dip, (40.0, [c.chains[0]]), "the tick read 40.0 GB with the second job still pending")
    ok((5_000_000_000, 1) in c.out_reads, f"--out read 5,000,000,000 bytes with the second job pending: {c.out_reads}")
    eq((c.spawned, c.dropped, c.killed, (c.out / M.ABORT_FILE).exists(), c.code), (c.chains, {}, [], False, 0),
       "every job launched, none dropped or killed, no ABORT.txt, exit 0")
    ok(c.verdict.startswith("DEVELOPMENT, never graded"), f"the entry is a DEVELOPMENT one: {c.verdict!r}")


# ---------------------------------------------------------------------------------------------------- T15: retention
def case_t15_retention(M, tmp):
    def bad_zip(path, sizes):
        return "testzip names actions.jsonl"
    with mock.patch.object(M, "verify_zip", bad_zip):
        _, _, records = play(M, job_of(M, tmp / "z", to="ch1_pokedex"), {})
    kept = records[0]["kept"]
    ok(not kept["zip_verified"] and (Path(kept["folder"]) / "actions.jsonl").is_file(), "a failed zip keeps the raw logs")

    def short_copy(source, target):
        Path(target).write_bytes(Path(source).read_bytes()[:-1])

    def plant(arm):
        profile = tmp / "c" / "build" / "profiles" / L5.PROFILE
        (profile / "current_save.sav").write_bytes(b"cartridge save")
    with mock.patch.object(M, "copy_file", short_copy):
        _, _, records = play(M, job_of(M, tmp / "c", to="ch1_pokedex"), {"L1": {"before": plant}})
    ok(str(records[0]["kept"]["ai_files"]["current_save.sav"]).startswith("size check FAILED"),
       f"a copy failing its size check is recorded: {records[0]['kept']['ai_files']}")
    # THE REAL verify_zip DECIDES (verifier round 3, R3-M1 c: the first arm above replaces it whole): the zip zip_logs
    # wrote is DAMAGED on disk, then handed to the module's own verify_zip, three ways: a member's CRC-32 wrong (its data
    # still reads: testzip names it), a member missing, a member of another size (members and sizes differ). Each: not
    # verified, the raw logs kept, the problem the real verify_zip wrote recorded
    real = M.verify_zip
    for i, (name, damage, word) in enumerate((("a damaged CRC", damage_crc, "testzip names"),
                                              ("a member missing", drop_member, "members and sizes"),
                                              ("a member of another size", resize_member, "members and sizes"))):
        def damaged(path, sizes, damage=damage):
            damage(Path(path))
            return real(path, sizes)
        with mock.patch.object(M, "verify_zip", damaged):
            _, _, records = play(M, job_of(M, tmp / f"d{i}", to="ch1_pokedex", seed=7330 + i), {})
        kept = records[0]["kept"]
        ok(not kept["zip_verified"] and (Path(kept["folder"]) / "actions.jsonl").is_file(), f"{name}: the raw logs kept")
        ok(word in str(kept["zip_problem"]), f"{name}: the real verify_zip names it: {kept['zip_problem']}")


def damage_crc(path: Path) -> None:
    """A REAL corrupt zip: the first member's CRC-32 in the central directory flipped (its data still inflates; the CRC
    check at its end fails, so `testzip` names it)."""
    raw = bytearray(path.read_bytes())
    at = raw.find(b"PK\x01\x02")
    raw[at + 16] ^= 0xFF
    path.write_bytes(bytes(raw))


def rewrite_zip(path: Path, change) -> None:
    """The zip at `path` written again, its members (name, bytes) changed by `change` (every CRC right)."""
    with zipfile.ZipFile(path) as old:
        members = [(info.filename, old.read(info.filename)) for info in old.infolist()]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as new:
        for name, body in change(members):
            new.writestr(name, body)


def drop_member(path: Path) -> None:
    rewrite_zip(path, lambda members: members[:-1])


def resize_member(path: Path) -> None:
    rewrite_zip(path, lambda members: [(name, body + b"x" if i == 0 else body) for i, (name, body) in enumerate(members)])


def case_t15_control(M, tmp):
    def plant(arm):
        profile = tmp / "build" / "profiles" / L5.PROFILE
        (profile / "current_save.sav").write_bytes(b"cartridge save")
        (profile / "ai_player").mkdir(exist_ok=True)
        (profile / "ai_player" / "memory.jsonl").write_text("{}\n", encoding="utf-8")
    job = job_of(M, tmp, to="ch1_pokedex")
    record, _, records = play(M, job, {"L1": {"before": plant}})
    folder = Path(records[0]["kept"]["folder"])
    ok(records[0]["kept"]["zip_verified"], "the zip verified")
    for name in ("actions.jsonl", "ai_player.log", "row.json", "goals.jsonl"):
        ok(not (folder / name).exists(), f"the raw {name} deleted")
    for name in ("end_state.ss1", "world_last.jsonl", "goals_last.jsonl", "current_save.sav", "memory.jsonl"):
        ok((folder / name).is_file(), f"{name} kept")
    eq(records[0]["kept"]["ai_files"]["launches.jsonl"], "absent", "an absent one recorded")
    ok(record["profile_deleted"] and not (tmp / "build" / "profiles" / job["profile"]).exists(), "the profile deleted")


# ---------------------------------------------------------------------------------------------------- T16: the experience filter
def planted_world() -> dict:
    tiles = {"1,1": ["bg", "", 3, "NORMAL", 5, 1, 2]}
    return {
        "maps": {"0:1": {"key": "0:1", "name": "M", "const": "ROUTE101", "first_frame": 1, "tiles": tiles,
                         "tile_fields": list(FP.TILE_FIELDS), "visits": {"1,1": 2}, "bumped": {
                             "1,1|up": {"from": [1, 2], "direction": "up", "first": 1, "last": 2, "bumps": 3},
                             "2,2|down": {"from": [2, 1], "direction": "down", "first": 1, "last": 2, "bumps": 1,
                                          "slid": True, "odd": 1}},
                         "closed": {}, "people": {}, "persons": {}, "met": {}, "items": {"3,3": 7}, "edges": {"up": 1},
                         "arrivals": [[1, 1, 1, "x"]]},
                 "0:2": {"key": "0:2", "name": "N", "const": "ROUTE102", "tiles": tiles,
                         "tile_fields": list(reversed(FP.TILE_FIELDS)), "edges": {}}},
        "warps": {"0:1|1,1": {"to": "0:2", "arrival": [2, 2], "direction": "up", "inferred": False, "uses": 3,
                              "first": 1, "last": 2, "by": "ai"}},
        "connections": [{"source": "0:1", "target": "0:2", "direction": "up", "from": [1, 0], "arrival": [1, 9],
                         "offset": [0, 0], "by": "ai", "frame": 5},
                        {"source": "0:1", "target": "0:2", "direction": "up", "from": [1, 0], "arrival": [1, 9],
                         "offset": [0, 0], "by": "scene", "frame": 9}],
        "transitions": [[1, "0:1", "0:2", "warp", "ai", [1, 1], [2, 2], "up"]], "tiles_learned": 9, "news": 1,
        "heard": ["x"], "news_log": [[1, "x"]], "spoke": [1], "landmarks": {"0:1|1,1": "mart"},
        "rides": {"0:1|5|0:2": {"from": "0:1", "to": "0:2", "arrival": [1, 1], "who": 5, "gfx": 3, "tile": [2, 2],
                                "words": "go?", "place": "dock", "via": [], "first": 1, "last": 2, "uses": 2,
                                "closed": {"news": 1}, "secret": 1}},
        "rng_state": 12345}


def case_t16_filter(M, tmp):
    static, unclassified = M.extract_static(planted_world())
    text = json.dumps(static)
    for word in ('"visits"', '"items"', '"people"', '"persons"', '"met"', '"closed"', '"arrivals"', '"transitions"',
                 '"news"', '"heard"', '"news_log"', '"spoke"', '"uses"', '"first"', '"last"', '"by"', '"frame"',
                 '"bumps"', '"rng_state"', '"secret"', '"odd"'):
        ok(word not in text, f"{word} reached the experience")
    for listed in ("rng_state", "rides.0:1|5|0:2.secret", "maps.0:1.bumped.2,2|down.odd"):
        ok(listed in unclassified, f"{listed} dropped AND listed: {unclassified}")
    ok("0:2" not in static["maps"] and any(u.startswith("maps.0:2") for u in unclassified),
       "a map whose tile_fields differ is dropped and listed")
    # THROUGH judge_leg (verifier round 3, N3). The Exp column of 3.5: a NOT CLEAN leg writes NO experience row, and its
    # record says so (its world tail is there to extract)
    job = job_of(M, tmp / "nc", to="ch1_pokedex", seed=7803)
    _, _, records = play(M, job, {"L1": {"word": "NOT CLEAN"}})
    eq((records[0]["class"], records[0]["experience"]["written"], len(M.read_records_named(Path(job["out"]), M.EXPERIENCE))),
       (M.NOT_CLEAN, False, 0), "a NOT CLEAN leg: no experience row")
    # 3.7's rides: a ride whose `uses` grew in the leg against the START's line is listed as used, by its delta; one whose
    # `uses` did not grow is not
    start = world_of([[100, "0:3", "0:19", "connection", "ai", [1, 1], [2, 2], "down"]],
                     rides={"R1": {"from": "0:3", "uses": 1}, "R2": {"from": "0:3", "uses": 2}})
    plan = {"L6": {"world_extra": {"rides": {"R1": {"from": "0:3", "uses": 3}, "R2": {"from": "0:3", "uses": 2}}}}}
    _, _, records = practice_job(M, tmp / "rides", plan, to="ch6_dewford", world=start)
    eq(records[0]["rides"]["used"], {"R1": 2}, "the ride used twice in the leg, by its delta; the unused one not listed")


def case_t16_control(M, tmp):
    static, _ = M.extract_static(planted_world())
    eq(sorted(static["rides"]["0:1|5|0:2"]), sorted(M.RIDE_KEPT), "the rides' 9 static fields pass")
    eq(static["maps"]["0:1"]["bumped"]["2,2|down"].get("slid"), True, "slid kept")
    eq(static["maps"]["0:1"]["tiles"]["1,1"], ["bg", "", 3, "NORMAL"], "tiles have 4 fields")
    eq(len(static["connections"]), 1, "connections de-duplicated without by and frame")
    eq(static["warps"]["0:1|1,1"], {"to": "0:2", "arrival": [2, 2], "direction": "up", "inferred": False}, "a warp")
    real = json.loads((FIXTURES / "ch5loop_tcap.world.jsonl").read_text(encoding="utf-8").splitlines()[0])
    static, unclassified = M.extract_static(real)
    eq(unclassified, [], "the merged tree's real memory extracts with nothing unclassified")
    eq(len(static["maps"]), 4, "its 4 maps")
    k1 = {"frame": 10, "decision": "tell", "reason": "[AI-GOALS] RUSTURF_TUNNEL is somewhere it has not been: first to "
                                                    "ROUTE116, a seasoned player's knowledge: ROUTE116 has a way into it"}
    battle = {"frame": 20, "decision": "world", "digest": "f20 overworld ROUTE 116(0,31) xy=(1,1) party=[Torchic:L9 9/9]",
              "extra": {"kind": "trainer", "outcome": "won"}}
    fights, _ = M.fights_of([k1, battle])
    eq(fights[0]["foe"], None, "a K1 tell is never a fight's foe")
    eq(M.fights_of([k1])[0], [], "a K1 tell alone makes no fight")
    # the Exp column's CONTROL (3.5; verifier round 3, N3): a CLEAN leg writes its experience row, its record says so
    job = job_of(M, tmp / "cl", to="ch1_pokedex", seed=7804)
    _, _, records = play(M, job, {})
    eq((records[0]["class"], records[0]["experience"]["written"], len(M.read_records_named(Path(job["out"]), M.EXPERIENCE))),
       (M.CLEAN_CHOSEN, True, 1), "a CLEAN leg: one experience row")


# ---------------------------------------------------------------------------------------------------- T17: origin
def case_t17_origin(M, tmp):
    jobs = M.plan_jobs("WP1", 6611, data())
    practice = [j for j in jobs if j["kind"] == "practice"]
    eq({j["origin"] for j in practice}, {"practice"}, "a saved start: practice")
    _, _, records = practice_job(M, tmp, {}, to="ch6_dewford")
    eq(records[0]["job"]["origin"], "practice", "the record")


def case_t17_control(M, tmp):
    jobs = M.plan_jobs("WP1", 6611, data())
    eq({j["origin"] for j in jobs if j["kind"] == "chain"}, {"new_game"}, "a chain: new_game")
    eq([(leg["leg"], leg["frames"], leg["wall"]) for leg in jobs[0]["legs"]][5:],
       [("L6", 1_000_000, 7200.0), ("L7", 1_200_000, 7200.0)], "L6 at 1,000,000 frames and L7 at 1,200,000, 7,200 s (2.3)")
    eq(len(jobs), 39, "WP1: 9 chains, 27 practice jobs, 3 planted-wall jobs")
    _, _, records = play(M, job_of(M, tmp, to="ch1_pokedex"), {})
    eq(records[0]["job"]["origin"], "new_game", "the record")


# ---------------------------------------------------------------------------------------------------- T18: the continue rule
def guard_after(out_dir: Path, chain: str, cause: str = "world", leg: str = "L1"):
    """A stub's `after` hook: the probe's kill marker `<leg>.KILLED.json` as the tick writes it (cause world, profile or
    abort), planted once the leg's launch has ended."""
    def after(run):
        LC._write_json(out_dir / chain / f"{leg}.KILLED.json", {"cause": cause, "text": "planted"})
    return after


def case_t18_continue(M, tmp):
    cases = [("not reached", {"L1": {"miss": True}}, "C1"),
             ("purity not clean", {"L1": {"breach": True}}, "C2"),
             # (fix round 3's sweep) a REACHED NOT CLEAN leg; C2 stops it on both halves, its class and its purity (a NOT
             # CLEAN word fails L5.PURITY_CLEAN too), so the class half alone is redundant here (revert_frontier's Z25)
             ("a reached NOT CLEAN leg", {"L1": {"word": "NOT CLEAN"}}, "C2"),
             ("tail not kept", {"L1": {"truncate": True}}, "C3"),
             ("STOP", None, "C6")]
    for i, (name, plan, word) in enumerate(cases):
        job = job_of(M, tmp / f"c{i}", seed=7400 + i)
        if plan is None:
            plan = {"L1": {"after": lambda run, out=Path(job["out"]): (out / "STOP.txt").write_text("x", encoding="utf-8")}}
        record, stub, records = play(M, job, plan)
        eq(stub.calls, [f"{job['chain']}-L1"], f"{name}: L2 NOT RUN")
        ok(word in (record["stop_reason"] or ""), f"{name}: the reason names {word}: {record['stop_reason']}")
        eq(record["not_run"], ["L2"], f"{name}: listed NOT RUN")
    job = job_of(M, tmp / "g", seed=7410)
    record, stub, _ = play(M, job, {"L1": {"after": guard_after(Path(job["out"]), job["chain"])}})
    eq(len(stub.calls), 1, "guard-cut: L2 NOT RUN")
    ok("C4 the probe's guard killed it" in (record["stop_reason"] or ""), f"the reason names C4: {record['stop_reason']}")
    # a CARRYING chain whose leg kept no goal snapshot (a soft-deadline or killed end writes none): the next leg could not
    # carry one, so C3 stops the chain (the lead's accepted rule; verifier round 1, F3)
    job = job_of(M, tmp / "s", seed=7411)
    record, stub, _ = play(M, job, {"L1": {"goals": False}})
    eq(stub.calls, [f"{job['chain']}-L1"], "no goal snapshot kept in a carrying chain: L2 NOT RUN")
    ok("C3 no goal snapshot was kept" in (record["stop_reason"] or ""), f"the reason names C3: {record['stop_reason']}")


def case_t18_control(M, tmp):
    job = job_of(M, tmp, seed=7420)
    record, stub, records = play(M, job, {})
    eq(len(stub.calls), 2, "all hold: L2 runs")
    l1 = by_leg(records)["L1"]
    eq(stub.carried[1]["START"][1], str(Path(l1["kept"]["folder"]) / "world_last.jsonl"), "from the KEPT world line")
    ok(stub.carried[1]["START"][0].endswith("end_state.ss1"), "from L1's end state")
    eq(md5(Path(l1["kept"]["folder"]) / "end_state.ss1"), l1["kept"]["state_md5"], "the kept state")
    eq(Path(stub.carried[1]["START"][0]).parent.name.rsplit("-", 1)[1], "L1", "L1's own run folder")
    off = job_of(M, tmp / "off", seed=7421, goals="off")
    _, stub, _ = play(M, off, {"L1": {"goals": False}})
    eq(len(stub.calls), 2, "a chain that carries no snapshot (GOALS-OFF) needs none kept: L2 runs")


# ---------------------------------------------------------------------------------------------------- T19: start custody
def custody_start(tmp: Path, held: str = "ch5_rival_meet", party=("Torchic",), md5_ok: bool = True):
    state = tmp / "C2_end_state.ss1"
    state.write_bytes(b"c2 state")
    world = tmp / "C2_world.jsonl"
    world.write_text(json.dumps({"maps": {}}) + "\n" + json.dumps({"maps": {}, "transitions": []}) + "\n",
                     encoding="utf-8")
    info = dict(FP.STARTS["C2"])
    files = {"state": state, "world": world, "job": None, "made_by": "planted"}
    truth = {"map": [0, 3], "frame": 1, "story": {"marks": marks_through(held)},
             "party_exp": [["0", name, 1, 5] for name in party]}
    patch = {"C2": {**info, "md5": md5(state) if md5_ok else "0" * 32, "world_md5": md5(world)}}
    return files, truth, patch


def case_t19_custody(M, tmp):
    for name, kwargs in (("md5 differs", {"md5_ok": False}), ("truth lacks ch5_rival_meet", {"held": "ch5_devon_corp"}),
                         ("no starter line", {"party": ("Zigzagoon",)}),
                         ("two starter lines", {"party": ("Torchic", "Mudkip")})):
        files, truth, patch = custody_start(tmp, **kwargs)
        with mock.patch.dict(M.STARTS, patch):
            _, problems = M.start_custody("C2", files, truth, data())
        ok(problems, f"{name}: refused")
    stub_truths: dict = {}
    job = job_of(M, tmp / "j", to="ch6_dewford", kind="practice", from_chapter=6)
    job["start"] = planted_start(M, tmp / "j", stub_truths)
    job["start"]["state_md5"] = "0" * 32
    stub = Stub(job, {})
    stub.truths.update(stub_truths)
    _, stub, records = play(M, job, {}, stub=stub)
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "a start whose md5 differs: REFUSED before launch")
    pending = job_of(M, tmp / "p", to="ch6_dewford", kind="practice", from_chapter=6, seed=7203)
    pending["start"] = {"kind": "pending", "id": "unresolved"}
    try:
        _, stub, records = play(M, pending, {})
    except Exception as error:  # noqa: BLE001 - the guard's absence: the job crashes instead of refusing
        raise AssertionError(f"an unresolved start (no state, no world line) crashed the job ({type(error).__name__}: "
                             f"{error}) instead of a REFUSED record before launch") from None
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "an unresolved start: REFUSED before launch")
    other = job_of(M, tmp / "o", to="ch1_pokedex", seed=7204)
    other["legs"][0]["proof"]["flags"]["ADVENTURE_STARTED"] = 1
    _, stub, records = play(M, other, {})
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "legs that are not the staged milestones': REFUSED")
    # C5's WORLD half (3.6; verifier round 3, R3-M1 a): a start whose world line is no longer the kept line (its sha256
    # differs), its state untouched: REFUSED before launch; a practice job's kept chain end, and a chain's next leg whose
    # kept line changed between the legs
    stub_truths = {}
    job = job_of(M, tmp / "w", to="ch6_dewford", kind="practice", from_chapter=6, seed=7205)
    job["start"] = planted_start(M, tmp / "w", stub_truths)
    Path(job["start"]["world"]).write_text(json.dumps(world_of([])) + "\n", encoding="utf-8")
    stub = Stub(job, {})
    stub.truths.update(stub_truths)
    _, stub, records = play(M, job, {}, stub=stub)
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "a start whose world line's sha256 differs: REFUSED before launch")
    ok("the world line" in records[0]["class_why"], f"the refusal names the world line: {records[0]['class_why']}")
    chain = job_of(M, tmp / "c", seed=7206)

    def tamper(index, leg, start, env):
        if index == 1:
            Path(start["world"]).write_text(json.dumps(world_of([])) + "\n", encoding="utf-8")
    _, stub, records = play(M, chain, {}, before_leg=tamper)
    eq((len(stub.calls), by_leg(records)["L2"]["class"]), (1, M.REFUSED),
       "a next leg whose kept world line changed between the legs: REFUSED before launch")


def case_t19_control(M, tmp):
    files, truth, patch = custody_start(tmp)
    with mock.patch.dict(M.STARTS, patch):
        entry, problems = M.start_custody("C2", files, truth, data())
    eq(problems, [], "a matching start")
    eq((entry["starter"], entry["starter_from"]), ("TORCHIC", "truth_party"), "starter_from kept")
    # C5's CONTROL (verifier round 3, R3-M1 a): a kept start whose state and world line are the kept ones is launched
    stub_truths = {}
    job = job_of(M, tmp / "w", to="ch6_dewford", kind="practice", from_chapter=6, seed=7207)
    job["start"] = planted_start(M, tmp / "w", stub_truths)
    stub = Stub(job, {})
    stub.truths.update(stub_truths)
    _, stub, records = play(M, job, {}, stub=stub)
    eq((len(stub.calls), records[0]["class"]), (1, M.CLEAN_CHOSEN), "a start whose state and world line match: launched")


# ---------------------------------------------------------------------------------------------------- T20: the donor
def case_t20_donor(M, tmp):
    job = job_of(M, tmp, to="ch1_pokedex", with_donor=False)
    other = Path(job["build_root"]) / "profiles" / "another-jobs-profile"
    other.mkdir(parents=True)
    (other / "metadata.yml").write_text("rom: another\n", encoding="utf-8")
    record, stub, records = play(M, job, {})
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "no donor: REFUSED")
    ok("LaunchError" in records[0]["class_why"], f"with the LaunchError text: {records[0]['class_why']}")
    # the PROFILE refusals (verifier round 2's V61 and V63, NITs until round 3): a profile the launcher refuses, or one that
    # is not a probe profile, is refused by `plan` and `run` (jobs_problems); a profile that EXISTS before the job (a
    # leftover) is REFUSED by the child, never launched in, named and never deleted by it
    jobs = M.plan_jobs("P1", 6601, data())
    for profile in ("endless-P1-torchic", "ai-fp-a name with spaces"):
        bad = copy.deepcopy(jobs)
        bad[0]["profile"] = profile
        ok(any("is not a probe profile the launcher accepts" in p for p in M.jobs_problems(bad)),
           f"the profile {profile!r}: refused")
    left = job_of(M, tmp / "left", to="ch1_pokedex", seed=7208)
    leftover = Path(left["build_root"]) / "profiles" / left["profile"]
    leftover.mkdir(parents=True)
    (leftover / "x.txt").write_text("a leftover\n", encoding="utf-8")
    record, stub, records = play(M, left, {})
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "a leftover profile: REFUSED before launch")
    ok((leftover / "x.txt").is_file() and not record["profile_deleted"] and str(leftover) in str(record["leftover"]),
       f"the leftover named, never deleted by the job: {record['leftover']}")
    # (fix round 3's sweep, N6) the CHILD's own profile refusals: a job whose profile is not a probe profile, and a child
    # whose live_step5.PROFILE is not its job's: each REFUSED before any launch
    main = job_of(M, tmp / "main", to="ch1_pokedex", seed=7209)
    main["profile"] = "endless-P1-x"
    _, stub, records = play(M, main, {})
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "a job whose profile is not a probe profile: REFUSED")
    ok("is not a probe profile" in records[0]["class_why"], f"the refusal names it: {records[0]['class_why']}")
    other = job_of(M, tmp / "other", to="ch1_pokedex", seed=7210)
    stub = Stub(other, {})
    saved = L5.PROFILE
    L5.PROFILE = "ai-fp-another-jobs-profile"
    try:
        M.run_job(other, stub)
    finally:
        L5.PROFILE = saved
    records = [r for r in M.read_records(Path(other["out"])) if r.get("record") == "leg"]
    eq((stub.calls, records[0]["class"]), ([], M.REFUSED), "live_step5.PROFILE not the job's: REFUSED")
    ok("live_step5.PROFILE is" in records[0]["class_why"], f"the refusal names it: {records[0]['class_why']}")


def case_t20_control(M, tmp):
    job = job_of(M, tmp, to="ch1_pokedex")
    seen: list[str] = []

    def look(index, leg, start, env):
        marker = Path(job["build_root"]) / "profiles" / job["profile"] / ".ai_player_profile"
        seen.append(marker.read_text(encoding="utf-8"))
    play(M, job, {}, before_leg=look)
    ok(seen and M.DONOR in seen[0], f"the marker names {M.DONOR}: {seen}")
    eq(M.jobs_problems(M.plan_jobs("P1", 6601, data())), [], "the plan's own profiles: accepted (round 3, N7)")


# ---------------------------------------------------------------------------------------------------- T21: the stage watch
def watch_tick(M, tmp: Path, digest: str) -> Path:
    out = tmp / "out"
    out.mkdir(parents=True, exist_ok=True)
    deps = batch_deps(M, tmp, stage_digest=lambda stage: digest, stage_every=0.0)
    state = {"aborted": False, "ai_stop": False, "out_over": False, "last_stage": -10.0, "last_sandbox": deps.clock(),
             "last_pass": None}
    M.tick([], out, {"REAL": tmp}, {"REAL": {"digest": "ALL", "sandbox": str(tmp)}}, {"REAL": "SANDBOX"}, state, deps)
    return out


def sandbox_tick(M, tmp: Path, digest: str) -> Path:
    """One tick whose SANDBOX watch is due (3.13: the junctioned sandbox's tracked modules/ and plugins/, every 10 min;
    here `sandbox_every` 0) and whose stage watch is not; the sandbox's digest at the batch's start is "SANDBOX"."""
    out = tmp / "sout"
    out.mkdir(parents=True, exist_ok=True)
    deps = batch_deps(M, tmp, sandbox_digest=lambda sandbox: digest, sandbox_every=0.0)
    state = {"aborted": False, "ai_stop": False, "out_over": False, "last_stage": deps.clock(), "last_sandbox": -10.0,
             "last_pass": None}
    M.tick([], out, {"REAL": tmp}, {"REAL": {"digest": "ALL", "sandbox": str(tmp / "sandbox")}}, {"REAL": "SANDBOX"},
           state, deps)
    return out


def case_t21_stage_watch(M, tmp):
    out = watch_tick(M, tmp, "CHANGED")
    ok((out / "STOP.txt").is_file(), "a staged file changed: STOP.txt")
    job = job_of(M, tmp / "j", to="ch2_wally")
    job["out"] = str(out)
    _, stub, _ = play(M, job, {})
    eq(stub.calls, [], "no new leg after STOP.txt")
    out = sandbox_tick(M, tmp / "sb", "CHANGED")
    ok((out / "STOP.txt").is_file() and "sandbox" in (out / "STOP.txt").read_text(encoding="utf-8"),
       "the junctioned sandbox's modules/ or plugins/ changed: STOP.txt (verifier round 1, F3)")
    # the ORCHESTRATOR's half (3.13; verifier round 3, N1: only the child's check was tested): with STOP.txt in --out, every
    # pending job is DROPPED with the reason and never spawned
    stop = "STOP.txt: the code under test changed mid-batch"
    eq(M.start_check({"legs": []}, view(stop=True)), (M.DROP, stop), "start_check DROPs a pending job on STOP.txt")
    (tmp / "st" / "out").mkdir(parents=True)
    (tmp / "st" / "out" / M.STOP_FILE).write_text("planted\n", encoding="utf-8")
    result, log, _ = sched(M, tmp / "st", plain_jobs(M, 2))
    eq((log, [why for _, why in result["not_started"]]), ([], [stop, stop]), "both pending jobs DROPPED, none spawned")


def case_t21_control(M, tmp):
    out = watch_tick(M, tmp, "ALL")
    ok(not (out / "STOP.txt").exists(), "unchanged: no STOP")
    ok(not (sandbox_tick(M, tmp / "sb", "SANDBOX") / "STOP.txt").exists(), "an unchanged sandbox: no STOP")
    eq(M.start_check({"legs": []}, view()), (M.GO, ""), "no STOP.txt: GO (round 3, N1)")


# ---------------------------------------------------------------------------------------------------- T22: the AI-only stop
def case_t22_ai_stop(M, tmp):
    band_ledger(tmp / "ledger.json")
    jobs = M.plan_jobs("WP1", 2000001, data())[:6]
    stage = {"REAL": fake_stage(M, tmp, "REAL")}
    bad = [{"L1": {"word": "NOT CLEAN"}}, {"L1": {"exit": 124, "no_verdict": True}},
           {"L1": {"exit": 7, "no_verdict": True, "stdout": "[AI-GATE] FAIL rule (a)\n"}},
           {"L1": {"exit": 8, "no_verdict": True}}, {"L1": {"exit": 1, "no_verdict": True}}]
    plans = {job["chain"]: plan for job, plan in zip(jobs, bad)}
    spawned: list = []
    code = run_quiet(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stage, parallel=1),
                     batch_deps(M, tmp, plans=plans, log=spawned))
    eq(code, 6, "exit 6")
    ok((tmp / "out" / M.ATTENTION_FILE).is_file(), "AI-ATTENTION.txt")
    eq(len(spawned), 5, "no launch after the fifth")
    ok(not list(tmp.rglob("ATTENTION.md")), "never the learner's ATTENTION.md")


def case_t22_control(M, tmp):
    four = [leg_record(f"r{i}", k, i) for i, k in enumerate((M.REFUSED, M.NOT_CLEAN, M.HUNG, M.REFUSED))]
    for reset in (M.CLEAN_CHOSEN, M.CUT_WORLD, M.CLEAN_BUDGET):
        eq(M.ai_stop_streak(four + [leg_record("x", reset, 9)]), 0, f"{reset} resets")
    eq(M.ai_stop_streak(four + [leg_record("i", M.INFRA, 9)]), 4, "INFRA between: neither")


# ---------------------------------------------------------------------------------------------------- T23: schema
def case_t23_schema(M, tmp):
    out = tmp / "out"
    M.append_record(out, {**leg_record("a", M.CLEAN_CHOSEN, 0), "schema_version": 2})
    try:
        M.build_report(out)
    except M.SchemaRefused:
        pass
    else:
        raise AssertionError("schema_version 2 was read")
    with redirect_stdout(io.StringIO()):
        eq(M.main(["report", str(out)]), 2, "exit 2")


def case_t23_control(M, tmp):
    out = tmp / "out"
    M.append_record(out, leg_record("a", M.CLEAN_CHOSEN, 0, reached=True))
    with redirect_stdout(io.StringIO()):
        eq(M.main(["report", str(out)]), 0, "1 reads")
    ok((out / "blockers.json").is_file() and (out / "blockers.md").is_file(), "the report files")
    ok(M.HEADER in (out / "blockers.md").read_text(encoding="utf-8"), "headed as development data")


# ---------------------------------------------------------------------------------------------------- T24: resume
class Killable(Running):
    def __init__(self) -> None:
        self.killed = False

    def kill_tree(self):
        self.killed = True


def killed_first_run(M, tmp: Path, jobs: list[dict], stages: dict, handles: list | None = None, **changes) -> Path:
    """A batch whose ORCHESTRATOR was killed while its first job played L2: L1's record written, L2's run folder made.
    `changes` go to batch_args (a development batch: `trainer=False, prediction=...`)."""
    out = tmp / "out"

    class Interrupted(KeyboardInterrupt):
        pass

    def spawn(job, job_path, log_path):
        handle = Killable()
        if handles is not None:
            handles.append(handle)
        leg = job["legs"][0]
        M.append_record(out, {**leg_record(M.run_id_of(job["batch"], job["chain"], "L1"), M.CLEAN_CHOSEN, 1.0,
                                           reached=True), "job": {"id": job["chain"], "origin": "new_game"}})
        M.write_json(out / job["chain"] / "current_leg.json", {"leg": "L2", "arm": f"{job['chain']}-L2"})
        run = Path(job["build_root"]) / "profiles" / job["profile"] / "ai_player_runs" / f"20261114-1-{job['chain']}-L2"
        run.mkdir(parents=True)
        (run / "world.jsonl").write_text(json.dumps({"maps": {}}) + "\n", encoding="utf-8")
        return handle

    def interrupted(seconds):
        raise Interrupted()
    deps = batch_deps(M, tmp, spawn=spawn)
    deps.sleep = interrupted
    try:
        run_quiet(M, batch_args(write_jobs(tmp, jobs), out, stages, **changes), deps)
    except KeyboardInterrupt:
        return out
    raise AssertionError("the first run was not interrupted")


def case_t24_resume(M, tmp):
    band_ledger(tmp / "ledger.json")
    jobs, stages = p1_batch(M, tmp)
    jobs = jobs[:2]
    handles: list = []
    out = killed_first_run(M, tmp, jobs, stages, handles)
    ok(handles and all(h.killed for h in handles), "an interrupt while the jobs run kills every running child")
    # the RESUME's refusals (3.13; verifier rounds 2 and 3: V57, V58, W37, NITs until round 3), each on the killed batch,
    # BEFORE its real resume below: exit 2, no launch, the records untouched
    records_before = (out / M.RECORDS).read_bytes()
    child = (f"{sys.executable} -B C:/stage/code/ai_player/gates/frontier_probe.py child "
             f"{out.resolve() / 'jobs' / (jobs[1]['chain'] + '.job.json')}")
    for name, args, processes, why in (
            ("--resume while a child of this --out still runs", batch_args(tmp / "jobs.json", out, stages, resume=True),
             (child,), "child process(es) of this --out still run"),
            ("--resume with another jobs.json than the batch's",
             batch_args(write_jobs(tmp, jobs[:1], "other.json"), out, stages, resume=True), (), "another jobs.json"),
            ("a non-empty --out without --resume", batch_args(tmp / "jobs.json", out, stages), (), "is not empty")):
        spawned = []
        code, text = refusal_of(M, args, batch_deps(M, tmp, log=spawned, processes=processes))
        eq((code, spawned, (out / M.RECORDS).read_bytes() == records_before), (2, [], True),
           f"{name}: refused, no launch, the records untouched")
        ok(why in text, f"{name}: the refusal names it: {text[-400:]}")
    ok(any("the job id is given twice" in p for p in M.jobs_problems([jobs[0], jobs[0]])),
       "a job id given twice: refused (a run_id is keyed by it; round 2's V60)")
    # (fix round 3's sweep, N6) --resume on an --out that holds no batch.json (a folder no batch wrote): refused, nothing
    # written in it
    stray = tmp / "stray"
    stray.mkdir()
    (stray / "x.txt").write_text("not a batch\n", encoding="utf-8")
    spawned = []
    code, text = refusal_of(M, batch_args(tmp / "jobs.json", stray, stages, resume=True), batch_deps(M, tmp, log=spawned))
    eq((code, spawned, sorted(p.name for p in stray.iterdir())), (2, [], ["x.txt"]),
       "--resume on an --out with no batch.json: refused, nothing written")
    ok(f"holds no {M.BATCH_FILE}" in text, f"the refusal names it: {text[-400:]}")
    spawned: list = []
    eq(run_quiet(M, batch_args(tmp / "jobs.json", out, stages, resume=True), batch_deps(M, tmp, log=spawned)), 0,
       "resumed")
    ok(("spawn", jobs[0]["chain"]) not in spawned,
       f"the resumed job is never launched again (its leg in flight salvaged, never re-run): {spawned}")
    legs = [r for r in M.read_records(out) if r.get("record") == "leg"]
    ids = [r["run_id"] for r in legs]
    eq(len(ids), len(set(ids)), f"no run_id twice: {ids}")
    first = {r["run_id"]: r for r in legs}
    in_flight = M.run_id_of("P1", jobs[0]["chain"], "L2")
    ok(in_flight in first, f"the leg in flight keeps a record (salvaged), never lost: {sorted(first)}")
    eq(first[in_flight]["class"], M.INFRA, "the leg in flight: INFRA (salvaged)")
    ok(M.run_id_of("P1", jobs[1]["chain"], "L2") in first, "the job never started runs in full")
    again = first[M.run_id_of("P1", jobs[0]["chain"], "L1")]
    eq(M.append_record(out, again), False, "a run_id already written is never written twice")
    eq(sum(1 for r in M.read_records(out) if r.get("run_id") == again["run_id"]), 1, "one line")


def case_t24_control(M, tmp):
    band_ledger(tmp / "ledger.json")
    jobs, stages = p1_batch(M, tmp)
    eq(run_quiet(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stages), batch_deps(M, tmp)), 0, "P1 ran")
    legs = [r for r in M.read_records(tmp / "out") if r.get("record") == "leg"]
    eq(len(legs), 12, "both arms on the 3 shared seeds, 2 legs each")
    eq(len({r["run_id"] for r in legs}), 12, "12 distinct run_ids")
    eq({r["job"]["arm"] for r in legs}, {"REAL", "WALL-OLDALE"}, "both arms")
    eq(M.jobs_problems(jobs), [], "distinct job ids: accepted (round 3, N7)")
    spawned: list = []
    # (verifier round 3, N1) a child of ANOTHER batch's --out still running never blocks this one's resume
    other = f"{sys.executable} -B C:/stage/code/ai_player/gates/frontier_probe.py child {tmp / 'elsewhere' / 'jobs' / 'x.job.json'}"
    eq(run_quiet(M, batch_args(tmp / "jobs.json", tmp / "out", stages, resume=True),
                 batch_deps(M, tmp, log=spawned, processes=(other,))), 0,
       "the finished batch resumed, beside another --out's running child")
    eq(spawned, [], "a finished batch launches nothing")


# ---------------------------------------------------------------------------------------------------- T24d: a DEVELOPMENT resume
def dev_resume_setup(M, tmp: Path) -> tuple[list[dict], dict, Path, Path]:
    """A DEVELOPMENT P1 batch (seed 7601, its two arms; a temp ledger, no entry before it) whose orchestrator was killed
    while its first job played L2: its ledger entry was begun BEFORE the first launch (and finished ERROR by the interrupt)."""
    (tmp / "ledger.json").write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
    jobs, stages = p1_batch(M, tmp, first=7601)
    jobs = jobs[:2]
    prediction = tmp / "p.txt"
    prediction.write_text("x\n", encoding="utf-8")
    out = killed_first_run(M, tmp, jobs, stages, trainer=False, prediction=prediction)
    eq([(e["id"], e["first"], e["last"]) for e in ledger.load(tmp / "ledger.json")["entries"]], [(1, 7601, 7601)],
       "the killed development batch began ONE entry")
    return jobs, stages, prediction, out


def divergent_copy(tmp: Path, seed: int) -> Path:
    """A DIVERGENT COPY of the seed ledger: SEED_LEDGER_GLOBS reads the copies in the work trees, the lab and the learner
    clone, which share ONE id sequence, so a copy that diverged can hold a resumed batch's own id. Its entry #1 names
    `seed` (verifier round 4, V4-M1)."""
    other = tmp / "other-copy" / "ledger.json"
    other.parent.mkdir(parents=True)
    other.write_text(json.dumps({"what": "a divergent copy", "entries": [
        {"id": 1, "family": "story", "driver": "another session", "purpose": "development", "first": seed, "last": seed,
         "status": "started"}]}), encoding="utf-8")
    return other


def case_t24d_resume(M, tmp):
    """3.13's resume of a DEVELOPMENT batch skips ONLY the batch's OWN ledger entry, the (ledger path, entry id) pair
    (verifier round 3, R3-M3): another entry naming its seeds still refuses the resume (exit 2, no ledger write, no
    launch), whether it sits in the batch's own ledger (one written while it was down) or in a DIVERGENT COPY under the
    batch's own id (verifier round 4, V4-M1: the key's ledger-path half)."""
    jobs, stages, prediction, out = dev_resume_setup(M, tmp)
    data_ = json.loads((tmp / "ledger.json").read_text(encoding="utf-8"))
    data_["entries"].append({"id": 2, "family": "story", "driver": "another", "purpose": "development", "first": 7601,
                             "last": 7601, "status": "done"})
    (tmp / "ledger.json").write_text(json.dumps(data_), encoding="utf-8")
    start = (tmp / "ledger.json").read_bytes()
    spawned: list = []
    code, text = refusal_of(M, batch_args(tmp / "jobs.json", out, stages, trainer=False, prediction=prediction, resume=True),
                            batch_deps(M, tmp, log=spawned))
    eq((code, (tmp / "ledger.json").read_bytes() == start, spawned), (2, True, []),
       "another entry naming the seeds: the resume refused, no ledger write, no launch")
    lines = [line for line in text.splitlines() if line.startswith("REFUSED: a seed of 7601-7601 is named")]
    ok(len(lines) == 1 and lines[0].endswith("#2 (development, 7601-7601)"), f"only the OTHER entry refuses: {lines}")
    # the ledger-path half: a FRESH killed batch (its own ledger holds #1 only) read beside a divergent copy whose #1, the
    # batch's own id, names 7601: refused, both ledgers byte-unchanged, no launch, the refusal naming THAT copy's #1 alone
    fresh = tmp / "divergent"
    fresh.mkdir()
    jobs, stages, prediction, out = dev_resume_setup(M, fresh)
    other = divergent_copy(fresh, 7601)
    ledgers = (fresh / "ledger.json", other)
    start = [path.read_bytes() for path in ledgers]
    spawned = []
    code, text = refusal_of(M, batch_args(fresh / "jobs.json", out, stages, trainer=False, prediction=prediction, resume=True),
                            batch_deps(M, fresh, log=spawned, seed_ledgers=lambda path: [path, other]))
    eq((code, [path.read_bytes() for path in ledgers] == start, spawned), (2, True, []),
       "a divergent copy's #1 naming the seeds: the resume refused, no ledger write, no launch")
    lines = [line for line in text.splitlines() if line.startswith("REFUSED: a seed of 7601-7601 is named")]
    ok(len(lines) == 1 and lines[0].endswith(f"{other} #1 (development, 7601-7601)"),
       f"only the divergent copy's #1 refuses, never the batch's own #1: {lines}")


def case_t24d_control(M, tmp):
    """A DEVELOPMENT batch resumed (3.13; WP1 starts "with --resume ready"; verifier round 3, R3-M3: T24 resumes only trainer
    batches): its OWN entry names its seeds and is never a refusal; the resume exits 0, keeps ONE entry and finishes it as a
    DEVELOPMENT one; the resumed job is never launched again; no run_id twice. The same with a divergent copy of the ledger
    read beside it whose entry #1, the batch's own id, names another seed (verifier round 4, V4-M1)."""
    jobs, stages, prediction, out = dev_resume_setup(M, tmp)
    spawned: list = []
    code, text = run_text(M, batch_args(tmp / "jobs.json", out, stages, trainer=False, prediction=prediction, resume=True),
                          batch_deps(M, tmp, log=spawned))
    eq(code, 0, f"the development batch resumed: {text[-400:]}")
    entries = ledger.load(tmp / "ledger.json")["entries"]
    eq([(e["id"], e["first"], e["last"]) for e in entries], [(1, 7601, 7601)], "still ONE entry, the batch's own")
    ok(str(entries[0]["verdict"]).startswith("DEVELOPMENT, never graded"), f"finished DEVELOPMENT: {entries[0]['verdict']!r}")
    ok(("spawn", jobs[0]["chain"]) not in spawned and ("spawn", jobs[1]["chain"]) in spawned,
       f"the resumed job never relaunched, the job never started run: {spawned}")
    ids = [r["run_id"] for r in M.read_records(out) if r.get("record") == "leg"]
    eq(len(ids), len(set(ids)), f"no run_id twice: {ids}")
    # the ledger-path half's CONTROL (verifier round 4, V4-M1): the same divergent copy beside it, its #1 (the batch's own
    # id) naming a seed the batch does NOT use, never refuses: the batch's own #1 is still skipped with a second ledger read
    fresh = tmp / "divergent"
    fresh.mkdir()
    jobs, stages, prediction, out = dev_resume_setup(M, fresh)
    other = divergent_copy(fresh, 7700)
    spawned = []
    code, text = run_text(M, batch_args(fresh / "jobs.json", out, stages, trainer=False, prediction=prediction, resume=True),
                          batch_deps(M, fresh, log=spawned, seed_ledgers=lambda path: [path, other]))
    eq(code, 0, f"a divergent copy's #1 naming another seed: the resume runs: {text[-400:]}")
    eq([(e["id"], e["first"], e["last"]) for e in ledger.load(fresh / "ledger.json")["entries"]], [(1, 7601, 7601)],
       "beside the divergent copy: still ONE entry, the batch's own")
    ok(("spawn", jobs[0]["chain"]) not in spawned and ("spawn", jobs[1]["chain"]) in spawned,
       f"beside the divergent copy: the resumed job never relaunched, the job never started run: {spawned}")


# ---------------------------------------------------------------------------------------------------- T25: the deadline
def view(**changes) -> dict:
    out = {"now": 1000.0, "deadline": None, "dependency": None, "own_running": 0, "singles_others": 0,
           "regression": False, "reserve_gb": 100.0, "waited": 0.0, "max_wait": 7200}
    out.update(changes)
    return out


class HungChild:
    """A stub child whose brain hangs: it writes no job record and ends when its process tree is killed, or (so a removed
    watchdog cannot hang the suite) by itself after `limit` polls, still with no job record."""

    def __init__(self, job: dict, limit: int = 40) -> None:
        self.job, self.limit, self.pid, self.kills, self.polls = job, limit, 8, 0, 0

    def poll(self):
        self.polls += 1
        return 1 if self.kills or self.polls > self.limit else None

    def kill_tree(self):
        self.kills += 1


def watchdog_drive(M, tmp: Path, make_child, seconds: int = 3):
    """One plain job through `drive` with its watchdog at `seconds` (the clock moves 1 s a pass) and `make_child(job)` as
    its child. Returns (the result, the children, --out)."""
    out = tmp / "out"
    out.mkdir(parents=True, exist_ok=True)
    stages = {"REAL": fake_stage(M, tmp, "REAL")}
    manifests = {"REAL": json.loads((stages["REAL"] / "manifest.json").read_text(encoding="utf-8"))}
    handles: list = []

    def spawn(job, job_path, log_path):
        handles.append(make_child(job))
        return handles[-1]
    deps = batch_deps(M, tmp, spawn=spawn)
    facts = {"batch": "S", "mode": "trainer", "started": "now", "entry_id": None, "parallel": 1}
    with mock.patch.object(M, "job_watchdog_seconds", lambda job: seconds), redirect_stdout(io.StringIO()):
        result = M.drive(plain_jobs(M, 1), out, stages, manifests, facts,
                         SimpleNamespace(deadline=None, max_wait=7200, resume=False), deps)
    return result, handles, out


def case_t25_deadline(M, tmp):
    job = {"legs": [{"leg": "L1", "wall": 3600.0}]}
    eq(M.start_check(job, view(deadline=1000.0 + 3600 + 300 + 1200 - 1))[0], M.DROP, "wall plus margins past --deadline")
    eq(M.start_check(job, view(deadline=1000.0 + 3600, regression=True))[0], M.DROP, "a WAIT reaching it")
    # the CHILD's own check before every leg (3.13; verifier round 1, F3): a deadline reached between legs keeps the next
    # leg from launching
    job = job_of(M, tmp / "d", seed=7430)
    record, stub, _ = play(M, job, {"L1": {"after": lambda run: job.update(deadline=time.time())}})
    eq(stub.calls, [f"{job['chain']}-L1"], "a deadline reached between legs: L2 never launched")
    eq((record["stopped_at"], record["not_run"]), ("L2", ["L2"]), "L2 NOT RUN")
    ok("deadline" in (record["stop_reason"] or ""), f"the reason names the deadline: {record['stop_reason']}")
    # the watchdog (3.13): a child alive past its job's summed watchdog is killed (its process tree, once) and salvaged
    _, handles, out = watchdog_drive(M, tmp / "w", HungChild)
    eq(handles[0].kills, 1, "a child alive past its watchdog: its process tree killed, once")
    ok((out / handles[0].job["chain"] / "WATCHDOG.txt").is_file(), "WATCHDOG.txt written")
    eq([r.get("stop_reason") for r in M.read_records(out) if r.get("record") == "job"],
       ["the job's process ended (killed by its watchdog)"], "salvaged, as killed by its watchdog")


def case_t25_control(M, tmp):
    job = {"legs": [{"leg": "L1", "wall": 3600.0}]}
    eq(M.start_check(job, view(deadline=1000.0 + 3600 + 300 + 1200))[0], M.GO, "exactly the margins: launched")
    eq(M.start_check(job, view(deadline=10 ** 9))[0], M.GO, "far from it")
    job = job_of(M, tmp / "d", seed=7431)
    job["deadline"] = time.time() + 10 ** 6
    _, stub, _ = play(M, job, {})
    eq(len(stub.calls), 2, "a deadline with room for both legs: both run")
    wd = tick_job(M, tmp / "wd")
    wd["watchdog_seconds"] = 3
    out = Path(wd["out"])
    out.mkdir(parents=True, exist_ok=True)
    deps = batch_deps(M, tmp / "wd", newest_world=lambda runs: (None, None), folder_bytes=lambda path: 0)
    handle = Killable()
    state = {"aborted": False, "ai_stop": False, "out_over": False, "last_stage": deps.clock(),
             "last_sandbox": deps.clock(), "last_pass": None}
    M.tick([(wd, handle, deps.clock() - 3)], out, {}, {}, {}, state, deps)
    ok(not handle.killed and not (out / wd["chain"] / "WATCHDOG.txt").exists(),
       "exactly at its watchdog: not killed (only a child strictly past it is)")
    _, handles, out = watchdog_drive(M, tmp / "w", lambda job: TimedChild(M, job, passes=2))
    eq([r.get("stop_reason") for r in M.read_records(out) if r.get("record") == "job"], [None],
       "a child that ends by itself in time keeps its own job record (nothing salvaged)")
    ok(not (out / handles[0].job["chain"] / "WATCHDOG.txt").exists(), "and is never killed by the watchdog")


# ---------------------------------------------------------------------------------------------------- T26: the scheduler
def sched(M, tmp: Path, jobs: list[dict], passes: int = 3, processes=(), free=100.0, parallel: int = 8,
          max_wait: float = 7200, on_end: dict | None = None, stages: dict | None = None, codes: dict | None = None,
          limit: int = 300):
    """`drive` on `jobs` with TimedChild children (each ends at its `passes`-th poll), a planted process list and free
    space. At most `limit` passes: past it the planted clock FAILS the case (an AssertionError), so a scheduler whose bound
    was removed fails its case instead of hanging it (verifier round 3, R3-M2)."""
    out = tmp / "out"
    out.mkdir(parents=True, exist_ok=True)
    stages = stages or {"REAL": fake_stage(M, tmp, "REAL")}
    manifests = {name: json.loads((path / "manifest.json").read_text(encoding="utf-8")) for name, path in stages.items()}
    handles: list = []
    log: list = []
    procs = processes if callable(processes) else (lambda: list(processes))
    reading = {"singles": 0}

    def measured():
        # the other singles the orchestrator was shown in this pass, counted HERE (not by the module's singles_of):
        # pokebot.py processes without --endless-target that are not the probe's own (ai-fp-) profiles
        commands = procs()
        reading["singles"] = sum(1 for c in commands
                                 if "pokebot.py" in c and "--endless-target" not in c and "ai-fp-" not in c)
        return commands

    def spawn(job, job_path, log_path):
        log.append({"chain": job["chain"], "own_running": sum(1 for h in handles if not h.done),
                    "others": reading["singles"], "job": json.loads(Path(job_path).read_text(encoding="utf-8")),
                    "done": [h.job["chain"] for h in handles if h.done]})
        handle = TimedChild(M, job, passes, (on_end or {}).get(job["chain"]))
        handles.append(handle)
        return handle
    deps = batch_deps(M, tmp, spawn=spawn, processes=measured, free=free, limit=limit)
    facts = {"batch": jobs[0]["batch"], "mode": "trainer", "started": "now", "entry_id": None, "parallel": parallel}
    args = SimpleNamespace(deadline=None, max_wait=max_wait, resume=False)
    result = M.drive(jobs, out, stages, manifests, facts, args, deps)
    return result, log, out


def plain_jobs(M, n: int, first: int = 2000001) -> list[dict]:
    return [M.make_job("S", "REAL", "REAL", "chain", "Story", "TREECKO", first + i, M.legs_for("ch1_pokedex", data()),
                       {"kind": "new_game", "id": "NG"}, "carry") for i in range(n)]


def reached_l5(M, folder_tmp: Path, world: dict | None = None, tried: list[str] | None = None):
    """An on_end hook: the source chain's REACHED L5 record, with its kept example files and their hashes (its world line
    `world`, default empty; its goal snapshot's `tried_items` `tried`, default none)."""
    def write(job):
        keep = Path(job["out"]) / job["chain"] / "L5"
        keep.mkdir(parents=True, exist_ok=True)
        (keep / "end_state.ss1").write_bytes(b"L5 end")
        (keep / "world_last.jsonl").write_text(json.dumps(world if world is not None else world_of([])) + "\n",
                                               encoding="utf-8")
        goals = {} if tried is None else {"tried_items": {"$set": sorted(tried)}}
        (keep / "goals_last.jsonl").write_text(json.dumps({"kind": "goals", "memory": {"goals": goals}}) + "\n",
                                               encoding="utf-8")
        M.append_record(Path(job["out"]), {**leg_record(M.run_id_of(job["batch"], job["chain"], "L5"), M.CLEAN_CHOSEN,
                                                        5.0, reached=True),
                                           "job": {"id": job["chain"], "persona": job["persona"],
                                                   "starter": job["starter"], "starter_from": "plan"},
                                           "kept": {"folder": str(keep), "state_md5": md5(keep / "end_state.ss1"),
                                                    "world_sha256": M.sha256_of(keep / "world_last.jsonl"),
                                                    "goals_sha256": M.sha256_of(keep / "goals_last.jsonl")}})
    return write


def wp1_pair(M):
    jobs = M.plan_jobs("WP1", 2000001, data())
    source = jobs[0]
    practice = next(j for j in jobs if (j.get("depends_on") or {}).get("chain") == source["chain"])
    return source, practice


def case_t26_scheduler(M, tmp):
    calls = {"n": 0}

    def others():
        calls["n"] += 1
        return ["python pokebot.py some-lane-profile"] * (10 if calls["n"] <= 3 else 0)
    result, log, _ = sched(M, tmp / "a", plain_jobs(M, 8), passes=6, processes=others)
    # 3.13's singles cap is 16: own running + the other singles seen in that pass + this one (the spec's number, not
    # M.SINGLES_CAP, so a changed constant is caught too)
    over = [(e["chain"], e["own_running"], e["others"]) for e in log if e["own_running"] + e["others"] + 1 > 16]
    eq(over, [], "never a launch past the singles cap of 16 (own running + other singles + this one)")
    eq(sum(1 for e in log if e["others"] == 10), 6, "six own launches beside 10 other singles (6 + 10 = 16), no more")
    eq((len(log), result["not_started"]), (8, []), "the others fall to 0 mid-run: all 8 start, not_started empty")
    lane = {"n": 0}

    def regression():
        lane["n"] += 1
        return ["python ai_player/gates/run_regression.py --full"] if lane["n"] <= 2 else []
    result, log, _ = sched(M, tmp / "b", plain_jobs(M, 1), processes=regression)
    eq(len(log), 1, "run_regression.py running: WAIT, then start")
    ok(lane["n"] >= 3, "it waited while the lane ran")
    result, log, _ = sched(M, tmp / "c", plain_jobs(M, 2), free=43.0, parallel=2)
    eq(log[1]["done"], [log[0]["chain"]], "the disk reservation short: the second WAITs until the first ends")
    source, practice = wp1_pair(M)
    result, log, _ = sched(M, tmp / "d", [source, practice], passes=3, on_end={source["chain"]: reached_l5(M, tmp)})
    entry = next(e for e in log if e["chain"] == practice["chain"])
    eq((entry["job"]["start"]["kind"], entry["done"]), ("chain_end", [source["chain"]]),
       "a WP1b job SKIPPED, then started from its source's L5 end")
    stage = {"REAL": fake_stage(M, tmp / "e", "REAL", {"G1": {"persona": "Story", "starter": "TREECKO",
                                                              "starter_from": "job_file", "made_by": "x"}})}
    result, log, _ = sched(M, tmp / "e", [source, practice], passes=2, stages=stage)
    entry = next(e for e in log if e["chain"] == practice["chain"])
    eq((entry["job"]["start"]["id"], entry["job"]["start"]["fallback_for"]), ("G1", "STRE"),
       "its chain ENDED without one: its fallback start at once, labelled")
    result, log, _ = sched(M, tmp / "f", plain_jobs(M, 1), max_wait=3,
                           processes=lambda: ["python run_regression.py"])
    ok(log == [] and "max-wait" in result["not_started"][0][1], f"a WAIT past --max-wait: DROPPED ({result['not_started']})")
    # the reservation's boundary from below (3.13 says "under" 40 + 2.0 GB; verifier round 3, N1): 0.01 GB under it WAITs
    eq(M.start_check({"legs": []}, view(reserve_gb=41.99))[0], M.WAIT, "a reservation of 41.99 GB: WAIT")


def case_t26_control(M, tmp):
    result, log, _ = sched(M, tmp / "a", plain_jobs(M, 8), passes=3)
    eq(result["most_running"], 8, "0 others: 8 at once")
    # the reservation EXACTLY at 40 + 2.0 GB is not under it (3.13; verifier round 3, N1; the spec's numbers): GO, and in a
    # batch 43.25 GB free less one running job's 1.25 GB budget (its profile folder empty) lets the second start beside it
    eq(M.start_check({"legs": []}, view(reserve_gb=42.0))[0], M.GO, "a reservation of exactly 42.0 GB: GO")
    result, log, _ = sched(M, tmp / "r", plain_jobs(M, 2), free=43.25, parallel=2)
    eq([e["done"] for e in log], [[], []], "43.25 - 1.25 = 42.0 GB: the second starts beside the first")
    source, practice = wp1_pair(M)
    other = plain_jobs(M, 1, 2000099)[0]
    result, log, _ = sched(M, tmp / "b", [source, practice, other], passes=3,
                           on_end={source["chain"]: reached_l5(M, tmp)})
    order = [e["chain"] for e in log]
    eq(order[:2], [source["chain"], other["chain"]], "a ready job behind a SKIPPED one launches in the same pass")
    eq(order[2], practice["chain"], "the SKIPPED job keeps its place")
    result, log, _ = sched(M, tmp / "c", [source, practice], passes=8, max_wait=2,
                           on_end={source["chain"]: reached_l5(M, tmp)})
    eq([e["chain"] for e in log], [source["chain"], practice["chain"]], "a SKIP longer than --max-wait: not DROPPED")


# ---------------------------------------------------------------------------------------------------- T27: graded-driver agreement
def big_world(sizes: dict[str, int]):
    real = LC.measure_then_delete

    def fake(path):
        record = real(path)
        leg = Path(path).parent.name.rsplit("-", 1)[1]
        if leg in sizes:
            record["bytes"] = sizes[leg]
        return record
    return mock.patch.object(LC, "measure_then_delete", fake)


def zipped_row(record: dict) -> dict:
    import zipfile

    with zipfile.ZipFile(record["kept"]["zip"]) as kept:
        return json.loads(kept.read("row.json").decode("utf-8"))


def case_t27_agreement(M, tmp):
    job = job_of(M, tmp, seed=7501)
    with big_world({"L1": 500_000_000}):
        _, stub, records = play(M, job, {})
    l1 = by_leg(records)["L1"]
    eq(len(stub.calls), 2, "a reached, clean leg with a 500,000,000-byte world continues here")
    eq(l1["continue"]["live_chain"]["go"], False, "it stops in continue_after")
    ok("C3" in l1["continue"]["live_chain"]["why"], "continue_after's C3")
    ok(any("continue_after would stop here" in n for n in l1["notes"]), "the record says why")
    eq(by_leg(records)["L2"]["start_memory"]["goal_memory"], "carried", "a leg that carries a goal snapshot says so")


def case_t27_control(M, tmp):
    job = job_of(M, tmp, to="ch3_rustboro", seed=7502)
    _, _, records = play(M, job, {"L3": {"miss": True}})
    for record in records:
        row = zipped_row(record)
        eq(record["reached"], LC.leg_reached(row)[0], f"{record['leg']['leg']}: reached equals leg_reached")
        eq(record["continue"]["go"], LC.continue_after(row, False)[0], f"{record['leg']['leg']}: the decision")
    mc = job_of(M, tmp / "mc", to="ch2_wally", seed=6702, mc=True, goals="never")
    with big_world({"L1": 500_000_000}):
        _, stub, records = play(M, mc, {})
    l1 = by_leg(records)["L1"]
    eq((len(stub.calls), l1["continue"]["go"]), (1, False), "an MC job STOPS at the 500,000,000-byte leg")
    eq(l1["continue"]["why"], l1["continue"]["live_chain"]["why"], "exactly as continue_after")
    ok(all(ENV_GOALS not in arm.env for arm in stub.arms), "and sends no AI_PLAYER_GOALS")
    # an MC chain that CONTINUES (verifier round 2's NIT, round 3's N7: the job above launches only a fresh L1, which no
    # job sends AI_PLAYER_GOALS): L1 keeps a goal snapshot a carrying chain's L2 would send; the MC chain's L2 starts from
    # L1's kept end and sends none
    cont = job_of(M, tmp / "mc2", to="ch2_wally", seed=6706, mc=True, goals="never")
    _, stub, records = play(M, cont, {})
    l1 = by_leg(records)["L1"]
    eq((len(stub.arms), stub.arms[-1].state_from), (2, "START"), "the MC chain continued to a non-fresh L2")
    ok(l1["kept"]["goals_sha256"], "L1 kept a goal snapshot")
    ok(ENV_GOALS not in stub.arms[1].env, "an MC chain's non-fresh L2 sends no AI_PLAYER_GOALS")


# ---------------------------------------------------------------------------------------------------- T28: imports
def importers(root: Path) -> list[str]:
    """Every file of the AI's package (ai_player/ outside gates/ and evidence/) whose SYNTAX imports frontier_probe."""
    found = []
    for path in (root / "ai_player").rglob("*.py"):
        rel = path.relative_to(root / "ai_player")
        if rel.parts[0] in ("gates", "evidence") or "__pycache__" in rel.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                     [node.module or ""] + [a.name for a in node.names] if isinstance(node, ast.ImportFrom) else [])
            if any("frontier_probe" in name for name in names):
                found.append(rel.as_posix())
    return found


def case_t28_imports(M, tmp):
    from ai_player.gates.check_grader_imports import scan

    root = tmp / "ai"
    (root / "ai_player").mkdir(parents=True)
    mode = root / "ai_player" / "mode.py"
    mode.write_text('"""It never imports frontier_probe."""\n# from ai_player.gates import frontier_probe\nx = 1\n',
                    encoding="utf-8")
    eq(importers(root), [], "a mention in a comment or a docstring")
    mode.write_text(mode.read_text(encoding="utf-8") + "from ai_player.gates import frontier_probe\n", encoding="utf-8")
    eq(importers(root), ["mode.py"], "a planted import is found")
    copy_root = tmp / "copy"
    for path in (REPO / "ai_player").rglob("*.py"):
        rel = path.relative_to(REPO)
        if rel.parts[1] == "evidence" or "__pycache__" in rel.parts:
            continue
        (copy_root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy_root / rel)
    probe = copy_root / "ai_player" / "gates" / "frontier_probe.py"
    text = probe.read_text(encoding="utf-8")
    anchor = "from ai_player.gates import ledger  # noqa: E402\n"
    ok(text.count(anchor) == 1, "the anchor")
    probe.write_text(text.replace(anchor, anchor + "from ai_player.personality import PERSONALITIES  # noqa: E402\n"),
                     encoding="utf-8")
    ok(scan(copy_root, ("ai_player.gates.frontier_probe",)), "the G-3 scan sees a planted AI import in the probe")


def case_t28_control(M, tmp):
    from ai_player.gates import check_grader_imports as G

    eq(importers(REPO), [], "no AI file imports the probe")
    eq(G.scan(REPO, ("ai_player.gates.frontier_probe",)), [], "the probe takes no value from the AI")
    eq(G.GRADERS, ("ai_player.gates.rate_step5", "ai_player.gates.live_step5", "ai_player.gates.live_chain"),
       "GRADERS unchanged")


# ---------------------------------------------------------------------------------------------------- T29: mutant staging
def fake_code(target: Path) -> None:
    (target / "ai_player" / "knowledge").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "ai_player" / "knowledge" / "milestones.json",
                 target / "ai_player" / "knowledge" / "milestones.json")
    (target / "ai_player" / "brain").mkdir(parents=True, exist_ok=True)
    (target / "ai_player" / "brain" / "navigator.py").write_text("def walls(here):\n    return frozenset()\n",
                                                                 encoding="utf-8")
    (target / "ai_player" / "mode.py").write_text("x = 1\nx = 1\n", encoding="utf-8")


def fake_sandbox(tmp: Path) -> Path:
    sandbox = tmp / "sandbox"
    for name in M_LINKS:
        (sandbox / name).mkdir(parents=True, exist_ok=True)
        (sandbox / name / "keep.txt").write_text(name, encoding="utf-8")
    (sandbox / "profiles" / "endless-P1-torchic").mkdir(parents=True, exist_ok=True)
    (sandbox / "profiles" / "endless-P1-torchic" / "metadata.yml").write_text("rom: x\n", encoding="utf-8")
    (sandbox / "pokebot.py").write_text("print(1)\n", encoding="utf-8")
    return sandbox


M_LINKS = ("modules", "plugins", "mgba", "roms")


def stage_with(M, tmp: Path, name: str, mutant: str | None):
    sandbox = tmp / "sandbox" if (tmp / "sandbox").is_dir() else fake_sandbox(tmp)
    return M.build_stage(tmp / name, "c0ffee", tmp, sandbox, sandbox / "profiles" / "endless-P1-torchic", mutant, [],
                         archive=lambda repo, commit, code: fake_code(code), free=lambda p: 100.0,
                         work_tree=lambda p: False)


def files_of(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def case_t29_mutant(M, tmp):
    code = tmp / "code"
    fake_code(code)
    refused(M, M.apply_mutant, code, "none", {"file": "ai_player/brain/navigator.py", "anchor": "absent text",
                                              "replacement": "x"})
    refused(M, M.apply_mutant, code, "twice", {"file": "ai_player/mode.py", "anchor": "x = 1\n", "replacement": "y\n"})
    refused(M, stage_with, M, tmp, "unknown", "no-such-mutant")


def case_t29_control(M, tmp):
    mutant = {"file": "ai_player/brain/navigator.py", "anchor": "    return frozenset()\n",
              "replacement": "    return frozenset({here})\n"}
    with mock.patch.dict(M.MUTANTS, {"planted": mutant}):
        plain = stage_with(M, tmp, "plain", None)
        walled = stage_with(M, tmp, "walled", "planted")
    eq(walled["mutant"]["file"], "ai_player/brain/navigator.py", "the manifest names the file")
    a, b = files_of(tmp / "plain" / "code" / "ai_player"), files_of(tmp / "walled" / "code" / "ai_player")
    eq(sorted(k for k in a if a[k] != b.get(k)), ["brain/navigator.py"], "the staged tree differs in exactly that file")
    ok(plain["play_digest"] != walled["play_digest"], "the play digest names the edit")
    counts = M.sandbox_counts(tmp / "sandbox")
    for name in ("plain", "walled"):
        result = M.teardown(tmp / name)
        ok(result["unchanged"] and not (tmp / name).exists(), f"teardown of {name}: junctions first, then deleted")
    eq(M.sandbox_counts(tmp / "sandbox"), counts, "the sandbox unchanged")


# ---------------------------------------------------------------------------------------------------- T30: hard-coded copies
def pin_personalities(copy_value, ai_value) -> bool:
    return set(copy_value) == set(ai_value)


def pin_fields(copy_value, ai_value) -> bool:
    return list(copy_value) == list(ai_value)


def case_t30_copies(M, tmp):
    from ai_player.personality import PERSONALITIES
    from ai_player.world.memory import MapMemory

    ok(not pin_personalities(M.PERSONALITIES, list(PERSONALITIES) + ["Hiker"]), "a 4th personality fails the pin")
    ok(not pin_fields(M.TILE_FIELDS, list(reversed(MapMemory("0:0").to_dict()["tile_fields"]))), "reordered fields fail")


def case_t30_control(M, tmp):
    from ai_player import game_memory
    from ai_player.brain import bossprep
    from ai_player.personality import PERSONALITIES
    from ai_player.world.memory import MapMemory

    ok(pin_personalities(M.PERSONALITIES, PERSONALITIES), "3 personalities equal PERSONALITIES as a set")
    ok(pin_fields(M.TILE_FIELDS, MapMemory("0:0").to_dict()["tile_fields"]), "7 field names equal to_dict()'s")
    eq((M.GOALS_FILE, M.GOALS_KIND), (game_memory.GOALS_FILE_NAME, game_memory.SNAPSHOT_KIND), "part 0's file and kind")
    eq(M.BOSSPREP_ACTING, bossprep.ACTING, "boss preparation's acting personalities")


# ---------------------------------------------------------------------------------------------------- T31: the LOOP key
WOODS, R104 = "24:11", "0:19"
CONSTS = {WOODS: "PETALBURG_WOODS", R104: "ROUTE104"}


def alternating(n: int, last: int, step: int = 100, hows=("warp",), first: int | None = None) -> list:
    if first is not None and n > 1:
        frames = [first + round(i * (last - first) / (n - 1)) for i in range(n)]
    else:
        frames = [last - (n - 1 - i) * step for i in range(n)]
    return [[frame, *((R104, WOODS) if i % 2 == 0 else (WOODS, R104)), hows[i % len(hows)], "ai", [1, 1], [2, 2], "up"]
            for i, frame in enumerate(frames)]


def loop_leg(M, trans: list, start: int, end: int, klass: str, reason: str, nxt: str, end_const: str,
             reached: bool = False, records: list | None = None, frames: int = 600000):
    loop = M.loop_measure(world_of(trans, CONSTS), start, end, frames, records or [])
    loop["keyed"] = M.loop_keyed(loop, reached, klass, reason)
    # (no churn here: the churn rule is judge_leg's own, and T31's CONTROL reads it from run_job's record and the report;
    # verifier round 3, R3-M4 a: this helper's copy of the rule made that item vacuous)
    return loop, M.blocker_of(5, nxt, reason, end_const, klass, reached, loop)


def loop_practice(M, tmp: Path, n: int, start_world: dict | None = None, **plan_changes):
    """ONE practice leg (L6) through run_job and judge_leg with `n` PETALBURG_WOODS|ROUTE104 crossings of its own after its
    start truth's frame 5000 (its kept start line `start_world`, default one connection), and the report of its --out:
    (its record, its report's chapter-6 cell)."""
    plan = {"L6": {"transitions": alternating(n, 5000 + 400_000, first=5000 + 100), "consts": CONSTS, **plan_changes}}
    _, _, records = practice_job(M, tmp, plan, to="ch6_dewford", world=start_world)
    report = M.build_report(Path(records[0]["kept"]["folder"]).parents[1])
    return records[0], report["trees"]["PLAY"]["6"]


def case_t31_loop(M, tmp):
    end_t = 1_289_802
    loop_t, key_t = loop_leg(M, alternating(118, end_t - 92_013), 689_802, end_t, M.CLEAN_BUDGET,
                             "play: stopped: not finished within N frames", "ch5_return_goods", "ROUTE116")
    end_c = 943_821
    loop_c, key_c = loop_leg(M, alternating(74, end_c - 20), 488_525, end_c, M.CLEAN_CHOSEN,
                             "play: stuck: no progress for N frames", "ch5_rusturf_grunt", "ROUTE104")
    eq(key_t["key"], key_c["key"], "E0's two loop legs: ONE LOOP key")
    eq(key_t["key"], [5, "-", "loop", "PETALBURG_WOODS|ROUTE104", "LOOP"], "the LOOP key")
    _, key_cut = loop_leg(M, alternating(80, 900_000), 100_000, 900_500, M.CUT_WORLD, M.reason_norm(M.CUT_TEXT), "-",
                          "UNKNOWN")
    eq(key_cut["key"], key_t["key"], "a CUT-WORLD leg on the same pair joins it")
    out = tmp / "out"
    for i, key in enumerate((key_t, key_c)):
        M.append_record(out, leg_record(f"E0-{i}", M.CLEAN_BUDGET, i, blocker=key, leg={"leg": "L5", "chapter": 5,
                                                                                        "index": 4}))
    eq([(b["key"], b["count"]) for b in M.build_report(out)["trees"]["TREE"]["5"]["blockers"]], [(key_t["key"], 2)],
       "count 2")
    raw = (FIXTURES / "a1_e0_loops.json").read_bytes()
    eq(hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), LOOPS_SHA256, "the committed fixture's sha256")
    keys = {}
    for leg in json.loads(raw)["legs"]:
        f = facts(exit=leg["exit"], verdict=verdict(leg["outcome"], leg["real_frames"]), frames=leg["frames"])
        klass = M.classify(f)[0]
        world = {"maps": {k: {"const": v} for k, v in leg["consts"].items()}, "transitions": leg["transitions"]}
        loop = M.loop_measure(world, leg["start_frame"], leg["end_frame"], leg["frames"], [])
        reason = M.reason_norm(leg["outcome"])
        loop["keyed"] = M.loop_keyed(loop, leg["reached"], klass, reason)
        nxt = M.next_unmet(leg["marks_after"], data())["next"]
        keys[leg["chain"]] = (M.blocker_of(5, nxt, reason, "x", klass, leg["reached"], loop), nxt, loop)
    eq(keys["LC-T-6483"][0]["key"], key_t["key"], "E0 T's own transitions give the same key")
    eq(keys["LC-C-6482"][0]["key"], key_t["key"], "E0 C's own transitions give the same key")
    eq((keys["LC-T-6483"][1], keys["LC-C-6482"][1]), ("ch5_return_goods", "ch5_rusturf_grunt"), "their own next unmet")
    eq((keys["LC-T-6483"][2]["crossings"], keys["LC-C-6482"][2]["crossings"]), (118, 74), "59 and 37 each way")
    # THE MODULE's START-FRAME CUT (3.8; verifier round 3, R3-M1 d: the fixture above is cut by make_a1_fixtures.py, so it
    # tested the script's cut): a practice leg whose kept start line already carries 20 PETALBURG_WOODS|ROUTE104 crossings
    # (frames 3,100-5,000, the last AT the start truth's frame 5000) and which makes 30 of its own counts ONLY its own 30
    # (with the carried prefix: 50, over the bar of 40)
    record, _ = loop_practice(M, tmp / "cut", 30, start_world=world_of(alternating(20, 5000), CONSTS))
    loop = record["measures"]["loop"]
    eq((loop["pair"], loop["crossings"], loop["transitions_in_leg"]), ("PETALBURG_WOODS|ROUTE104", 30, 30),
       "only the leg's own crossings and transitions, never the carried prefix's")
    # 3.8's "LOOPS SEEN" table (verifier round 3, N3): a flagged leg (60 crossings, then a discrete battle-loss stop: its
    # own key) is listed there, through judge_leg and build_report, never hidden
    record, cell = loop_practice(M, tmp / "flag", 60, miss=True, reason="play: stuck: 3 battles lost (MAX_LOSSES 3)")
    eq((record["measures"]["loop"]["keyed"], [row["run_id"] for row in cell["loops_seen"]]), ("flag", [record["run_id"]]),
       "a flagged leg is listed under loops seen")


def case_t31_control(M, tmp):
    end = 1_289_802
    start = end - 600_000

    def shaped(n=118, last_gap=92_013, klass=None, reason="play: stopped: not finished within N frames", **kw):
        return loop_leg(M, alternating(n, end - last_gap, **kw), start, end, klass or M.CLEAN_BUDGET, reason,
                        "ch5_return_goods", "ROUTE116")
    eq(shaped(40)[0]["keyed"], "LOOP", "40 crossings (20 each way): LOOP")
    eq(shaped(last_gap=120_000)[0]["keyed"], "LOOP", "a last crossing exactly 120,000 frames before the end: LOOP")
    loop, key = shaped(40, 120_001, first=start + 1)
    eq((loop["keyed"], key["key"][4]), ("flag", M.CLEAN_BUDGET), "120,001 frames: its own key, flagged")
    ok(loop["window_share"] >= 0.75, f"even with a window share of 0.75+ ({loop['window_share']})")
    eq(shaped(39)[0]["keyed"], "none", "39 crossings: no LOOP")
    loop, key = loop_leg(M, alternating(118, end - 50), start, end, M.CLEAN_CHOSEN, "play: done: chN reached",
                         "ch6_briney_house", "RUSTBORO_CITY", reached=True)
    eq((loop["keyed"], key), ("none", None), "a reached leg with 118 crossings: never LOOP, no blocker")
    # CHURN BY THE MODULE'S OWN RULE (3.8; verifier round 3, R3-M4 a: the line above once checked this helper's copy of the
    # rule): through run_job, judge_leg and build_report, a REACHED leg with 118 crossings is churn, listed in the report's
    # churn table (never ranked, never a loop seen); one with 38 is neither
    got = {}
    for name, n in (("many", 118), ("few", 38)):
        record, cell = loop_practice(M, tmp / name, n)
        got[name] = (record["reached"], record["measures"]["loop"]["crossings"], record["measures"]["loop"]["churn"],
                     [row["run_id"] for row in cell["churn"]] == [record["run_id"]], record["blocker"], cell["loops_seen"])
    eq(got, {"many": (True, 118, True, True, None, []), "few": (True, 38, False, False, None, [])},
       "(reached, crossings, churn, alone in the churn table, blocker, loops seen)")
    raise_records = [{"frame": start, "decision": "goal", "action": "raise"}, {"frame": end - 60_000,
                                                                               "decision": "goal_end", "action": "raise"}]
    loop, _ = loop_leg(M, alternating(60, end - 70_000), start, end, M.CLEAN_BUDGET, "play: stopped", "ch6_dewford",
                       "ROUTE104", records=raise_records)
    eq((loop["crossings_raise"], loop["keyed"]), (60, "none"), "60 crossings all during an ACTIVE raise: no LOOP")
    loop, key = shaped(reason="play: stuck: N battles lost (MAX_LOSSES N)", klass=M.CLEAN_CHOSEN)
    eq((loop["keyed"], key["key"][2]), ("flag", "play: stuck: N battles lost (MAX_LOSSES N)"),
       "a battle-loss stop after a loop: its own key, flagged")
    eq(shaped(118, hows=("warp", "connection"))[0]["crossings"], 118, "edge and warp crossings count alike")
    records = [{"decision": "goal_end", "reason": "stuck: ping-pong between two maps"},
               {"decision": "goal_end", "reason": "done: stuck: ping-pong said later"},
               {"decision": "tell", "reason": "stuck: ping-pong"}]
    eq(M.loop_measure(world_of([]), 0, 10, 10, records)["pingpong_ends"], 1, "pingpong_ends counts only goal_end ones")


# ---------------------------------------------------------------------------------------------------- T32: goal custody
def case_t32_goal_custody(M, tmp):
    job = job_of(M, tmp, seed=7601)

    def tamper(index, leg, start, env):
        if index == 1:
            Path(start["goals"]).write_text('{"kind":"goals","memory":{"goals":{}},"forged":1}\n', encoding="utf-8")
    _, stub, records = play(M, job, {}, before_leg=tamper)
    eq(len(stub.calls), 1, "REFUSED before the launch")
    eq(by_leg(records)["L2"]["class"], M.REFUSED, "a next leg whose snapshot's sha256 differs")
    jobs = M.plan_jobs("MC", 6701, data(), to="ch1_pokedex")
    jobs[0]["env"] = {ENV_GOALS: "x"}
    # its OWN reason (the lead, 2026-11-15: fix round 5's empty-env rule refuses the key too, so a check that only
    # some refusal names it passed with this guard removed: G84 read NOT CAUGHT in the first full lane)
    mc_reason = f"an MC job never sends {ENV_GOALS} (E0's harness, 2.4b)"
    ok(any(p.endswith(mc_reason) for p in M.jobs_problems(jobs)), "an MC job naming AI_PLAYER_GOALS: refused, MC's reason")
    msg = refused(M, M.plan_jobs, "MC", 6701, data(), "ch1_pokedex", {ENV_GOALS: "x"})
    ok(mc_reason in msg, f"plan's refusal gives MC's reason: {msg}")
    # AI_PLAYER_GOALS on a leg that carries NO snapshot (C5, 3.11; verifier round 3, N1): a GOALS-OFF chain's L2 whose
    # checked environment names it (a harness regression, planted): REFUSED before its launch
    off = job_of(M, tmp / "off", seed=7603, goals="off")

    def plant(index, leg, start, env):
        if index == 1:
            env[ENV_GOALS] = str(start["goals"])
    _, stub, records = play(M, off, {}, before_leg=plant)
    l2 = by_leg(records)["L2"]
    eq((len(stub.calls), l2["class"]), (1, M.REFUSED), "AI_PLAYER_GOALS on a leg carrying none: REFUSED before launch")
    ok("carries no goal snapshot" in l2["class_why"], f"the refusal names it: {l2['class_why']}")
    # 3.7's losses_carried (verifier round 3, R3-M4 b): a GOALS-OFF leg from a kept 2-loss snapshot carries none of it: 0
    _, _, records = practice_job(M, tmp / "lossoff", {}, goals={"losses": 2, "tried": []}, to="ch6_dewford",
                                 goals_policy="off")
    eq((records[0]["start_memory"]["goal_memory"], records[0]["start_memory"]["losses_carried"]), ("none", 0),
       "a GOALS-OFF leg from a kept 2-loss snapshot: losses_carried 0")


def case_t32_control(M, tmp):
    job = job_of(M, tmp, seed=7602)
    seen: list = []

    def look(index, leg, start, env):
        if index == 1:
            runs = Path(job["build_root"]) / "profiles" / job["profile"] / "ai_player_runs"
            written = FP.last_line_of(next(runs.glob(f"*-{job['chain']}-L1")) / "goals.jsonl")
            seen.append((Path(env[ENV_GOALS]).read_bytes().rstrip(b"\r\n"), written.rstrip(b"\r\n")))
    _, stub, records = play(M, job, {}, before_leg=look)
    eq(len(stub.calls), 2, "the carried leg ran")
    eq(seen[0][0], seen[0][1], "the carried snapshot arrives byte-identical")
    eq(by_leg(records)["L2"]["start_memory"]["goal_memory"], "carried", "goal_memory: carried")
    _, _, records = practice_job(M, tmp / "none", {}, goals=False, to="ch6_dewford")
    eq(records[0]["start_memory"]["goal_memory"], "none", "a start with none runs, goal_memory: none")
    # 3.7's losses_carried (verifier round 3, R3-M4 b; P2's CONTROL and the report's carried-in losses read it): a leg that
    # CARRIES a snapshot holding 2 battles lost records 2
    _, _, records = practice_job(M, tmp / "loss", {}, goals={"losses": 2, "tried": []}, to="ch6_dewford")
    eq((records[0]["start_memory"]["goal_memory"], records[0]["start_memory"]["losses_carried"]), ("carried", 2),
       "a carried 2-loss snapshot: losses_carried 2")


# ---------------------------------------------------------------------------------------------------- T33: MC is E0's harness
def other_state(run) -> None:
    """A stub's `after` hook: the launch command names another --state than the one the leg started from (a harness
    regression): live_chain's custody sees it on the row; A1's own pre-launch check ran before the launch."""
    at = run.command.index("--state")
    run.command[at + 1] = run.command[at + 1] + ".other"


def mc_leg(leg: str, go: bool = True, why: str = "C1-C6 held") -> dict:
    """A planted leg record of the one-leg MC job MC-X: CLEAN, fresh and reached, continuing or not."""
    return {"schema_version": 1, "record": "leg", "run_id": f"MC-X-{leg}", "class": "CLEAN-CHOSEN", "reached": True,
            "fresh": {"ok": True}, "continue": {"go": go, "why": why}, "leg": {"leg": leg},
            "job": {"id": "MC-X", "mc": True, "legs_planned": [leg]}}


def mc_batch(M, tmp: Path, jobs: list[dict], plans: dict | None = None, timed: bool = False, parallel: int = 8,
             out_capped: bool = False) -> SimpleNamespace:
    """An MC batch (2.4b) through the REAL run_batch in development mode (a temp ledger and evidence folder, --parallel
    `parallel`, 100 GB free): stub children run in this process (`plans` per chain), or with `timed` stay running for 3
    polls each, the children alive at each launch counted; with `out_capped` --out reads over its cap at every tick (so a
    job still pending after the first pass is DROPPED unlaunched; the planted clock fails past 200 passes). Returns the
    exit, the ledger entry's verdict, the most alive at once, batch.json and the launches."""
    (tmp / "ledger.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp / "ledger.json").write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
    stages = {"REAL": fake_stage(M, tmp, "REAL")}
    prediction = tmp / "p.txt"
    prediction.write_text("MC predicted\n", encoding="utf-8")
    handles: list = []
    most = [0]

    def spawn(job, job_path, log_path):
        handles.append(TimedChild(M, job, passes=3))
        most[0] = max(most[0], sum(1 for h in handles if not h.done))
        return handles[-1]
    out = (tmp / "out").resolve()
    launched: list = []
    sizes = {"folder_bytes": lambda path: M.OUT_CAP_BYTES + 1 if Path(path).resolve() == out else 0} if out_capped else {}
    code = run_quiet(M, batch_args(write_jobs(tmp, jobs), out, stages, trainer=False, prediction=prediction,
                                   parallel=parallel),
                     batch_deps(M, tmp, plans=plans, spawn=spawn if timed else None, log=launched,
                                limit=200 if out_capped else 2000, **sizes))
    entries = ledger.load(tmp / "ledger.json")["entries"]
    return SimpleNamespace(code=code, verdict=str(entries[0].get("verdict")) if len(entries) == 1 else f"{entries}",
                           most=most[0], batch=json.loads((out / M.BATCH_FILE).read_text(encoding="utf-8")),
                           launched=[chain for _, chain in launched])


MC_READS = "THE MERGE CHECK (MC, 2.4b, a hard-break check, never a rate) reads"


def case_t33_mc(M, tmp):
    mc = job_of(M, tmp, to="ch2_wally", seed=6703, mc=True, goals="never")
    with big_world({"L1": 500_000_000}):
        _, stub, records = play(M, mc, {})
    eq(len(stub.calls), 1, "an MC job decides by continue_after (the 500,000,000-byte leg stops it)")
    eq(M.disk_decision(1_000_000_001, 50.0, None, mc=True), None, "an MC leg is never cut at 1,000,000,000")
    _, marker, killed = one_tick(M, tmp / "tick", tick_job(M, tmp / "tick", mc=True), world=1_000_000_001)
    ok(marker is None and not killed, "the tick itself never cuts an MC leg at 1,000,000,000 (verifier round 1, F1)")
    # an MC job's custody is live_chain's own (custody_problems, continue_after's C5; verifier round 1, F3): a break planted
    # AFTER the launch (L2's command names another --state than L1's end state) stops the chain, and MC reads STOP
    broken = job_of(M, tmp / "custody", to="ch2_wally", seed=6707, mc=True, goals="never")
    _, _, records = play(M, broken, {"L2": {"after": other_state}})
    l2 = by_leg(records)["L2"]
    ok(l2["custody"] and not l2["continue"]["go"] and "C5 custody" in (l2["continue"]["why"] or ""),
       f"L2's custody break stops it: {l2['custody']}, {l2['continue']}")
    reading = M.build_report(Path(broken["out"]))["mc"]
    eq(reading["reading"], "STOP", f"an MC chain with a custody break reads STOP ({reading})")
    eq(M.mc_reading([mc_leg("L1", go=False, why="C5 custody: planted")]),
       {"reading": "STOP", "chains": 1, "problems": ["MC-X L1: C5 custody: planted"]},
       "MC reads each leg's continue decision: a CLEAN, fresh, reached leg that did not continue is a STOP")
    jobs = M.plan_jobs("MC", 6701, data(), to="ch1_pokedex")
    for job in jobs:
        job["seed"] = 6800
    ok(any("MC seed" in p for p in M.jobs_problems(jobs)), "an MC seed outside 6701-6799")
    path = tmp / "ledger.json"
    path.write_text(json.dumps({"entries": [{"id": 1, "first": 6701, "last": 6701, "purpose": "development"}]}),
                    encoding="utf-8")
    hits, _, _ = M.seeds_named(6701, 6703, [path])
    ok(hits, "an MC seed named by an entry")
    hung = job_of(M, tmp / "hung", to="ch2_wally", seed=6704, mc=True, goals="never")
    play(M, hung, {"L2": {"exit": 124, "no_verdict": True}})
    eq(M.build_report(Path(hung["out"]))["mc"]["reading"], "STOP", "a HUNG MC leg reads STOP")
    # MC's LEDGER VERDICT names its reading (2.4b names PASS and STOP; verifier round 3, N7): an MC batch, through the real
    # run_batch, one of whose chains HANGS, finishes its development entry reading STOP, naming that chain
    jobs = M.plan_jobs("MC", 6721, data(), to="ch1_pokedex")
    stop = mc_batch(M, tmp / "verdict", jobs, plans={jobs[1]["chain"]: {"L1": {"exit": 124, "no_verdict": True}}})
    ok(stop.code == 0 and stop.verdict.startswith(f"DEVELOPMENT, never graded: {MC_READS} STOP over 3 chains: "
                                                  f"{jobs[1]['chain']} L1: HUNG"), f"the entry reads STOP: {stop.verdict!r}")
    # (fix round 6, verifier round 6's V6-1, MAJOR) a PLANNED MC chain DROPPED before its launch is a chain that did not run,
    # never no chain: an MC batch of 3 at P 2 whose --out reads over its cap launches 2 (both reach) and DROPS the third,
    # and its entry reads STOP over 3 chains naming it (it read "PASS over 2 chains" before the fix)
    jobs = M.plan_jobs("MC", 6721, data(), to="ch1_pokedex")
    dropped = mc_batch(M, tmp / "dropped", jobs, parallel=2, out_capped=True)
    eq((dropped.code, dropped.launched), (0, [jobs[0]["chain"], jobs[1]["chain"]]),
       "the --out cap: 2 launched, the third never")
    ok(dropped.verdict.startswith(f"DEVELOPMENT, never graded: {MC_READS} STOP over 3 chains: {jobs[2]['chain']}: "
                                  "DROPPED, not run"), f"a dropped MC chain reads STOP over 3: {dropped.verdict[:300]!r}")
    eq(M.mc_reading([], {"MC-Y": ["L1"]}),
       {"reading": "STOP", "chains": 1, "problems": ["MC-Y: DROPPED, not run (no leg and no job record)"]},
       "an MC batch whose every planned job was dropped reads STOP, never None")
    eq(M.mc_reading([mc_leg("L1")], {"MC-X": ["L1"], "MC-Y": ["L1"]})["chains"], 2,
       "the chain count is the planned one, not the started one")
    # an MC job whose goal policy is not "never" is refused by plan and run (round 2's V59, a NIT until round 3)
    jobs = M.plan_jobs("MC", 6701, data(), to="ch1_pokedex")
    jobs[0]["goals"] = "carry"
    ok(any("an MC job carries no goal snapshot" in p for p in M.jobs_problems(jobs)),
       "an MC job whose goal policy is not 'never': refused")


def case_t33_mc_control_pass(M, tmp):
    good = job_of(M, tmp, to="ch2_wally", seed=6705, mc=True, goals="never")
    _, _, records = play(M, good, {})
    eq([r["custody"] for r in records], [[], []], "live_chain's custody holds on both legs of an untouched MC chain")
    reading = M.build_report(Path(good["out"]))["mc"]
    eq((reading["reading"], reading["problems"]), ("PASS", []), "an MC chain that reached its target reads PASS")


def case_t33_control(M, tmp):
    jobs = M.plan_jobs("MC", 6701, data(), repo=REPO)
    eq([(j["persona"], j["starter"]) for j in jobs], [("Story", "TREECKO"), ("Catcher", "TORCHIC"),
                                                      ("Trainer", "MUDKIP")], "the 3 diagonal chains")
    eq(jobs[0]["legs"][-1]["target"], M.frontier_target(REPO), "to the newest graded target")
    eq([leg["frames"] for leg in jobs[0]["legs"]], [LC.FRAMES_BY_CHAPTER[c] for c in range(1, 6)], "live_chain's legs")
    ok(all(j["goals"] == "never" and j["mc"] for j in jobs), "no goal key")
    eq(M.MC_PARALLEL, 3, "P = 3")
    with mock.patch.object(LC, "GUARD_WORLD_BYTES", 1234):
        eq(M.world_cut(True), 1234, "an MC job's world cut IS live_chain.GUARD_WORLD_BYTES (read, never copied)")
        # (verifier round 3, N2: this was asserted outside the patch, so a copied 1,750,000,000 passed)
        eq(M.profile_budget(True), 1234 + 250_000_000, "its profile budget is that READ value + 250,000,000")
    ok(M.profile_budget(True) > M.world_cut(True), "its profile budget lies above it")
    eq(M.mc_reading([mc_leg("L1")]), {"reading": "PASS", "chains": 1, "problems": []}, "a leg that continued: PASS")
    case_t33_mc_control_pass(M, tmp / "pass")
    # P = 3 AT RUN TIME, on a batch where it BINDS (2.4b; verifier round 3, N2: every MC plan has 3 jobs): 6 MC jobs asked
    # --parallel 8 with room for 8 run at most 3 at once, and batch.json says P 3
    six = M.plan_jobs("MC", 6711, data(), to="ch1_pokedex") + M.plan_jobs("MC", 6714, data(), to="ch1_pokedex")
    capped = mc_batch(M, tmp / "p3", six, timed=True)
    eq((capped.code, capped.most, capped.batch["parallel"], capped.batch["parallel_asked"]), (0, 3, 3, 8),
       "an MC batch of 6 runs at most 3 at once (asked 8)")
    # (fix round 5, verifier round 4's V4-N2 = H03) the verdict's chain count is the batch's own, not a fixed 3: these 6
    # chains (stub children that write no leg) finish the entry reading STOP over 6 chains
    ok(capped.verdict.startswith(f"DEVELOPMENT, never graded: {MC_READS} STOP over 6 chains: "),
       f"a 6-chain MC entry reads over 6 chains: {capped.verdict[:200]!r}")
    # MC's LEDGER VERDICT (2.4b; verifier round 3, N7): an MC batch whose 3 chains all reach finishes its entry reading PASS
    passing = mc_batch(M, tmp / "verdict", M.plan_jobs("MC", 6721, data(), to="ch1_pokedex"))
    ok(passing.code == 0 and passing.verdict.startswith(f"DEVELOPMENT, never graded: {MC_READS} PASS over 3 chains; "),
       f"the entry reads PASS: {passing.verdict!r}")
    # (fix round 6, V6-1's CONTROL) the same 3 chains at P 2 with no cap: all 3 launch and reach, PASS over 3 chains, and a
    # planned job that RAN (a leg, no job record) is never called DROPPED; batch.json carries the plan
    jobs = M.plan_jobs("MC", 6721, data(), to="ch1_pokedex")
    p2 = mc_batch(M, tmp / "p2", jobs, parallel=2)
    eq((p2.code, p2.launched), (0, [job["chain"] for job in jobs]), "P 2, no cap: all 3 launch")
    ok(p2.verdict.startswith(f"DEVELOPMENT, never graded: {MC_READS} PASS over 3 chains; "),
       f"P 2, no cap: the entry reads PASS over 3: {p2.verdict[:300]!r}")
    eq(p2.batch["mc_planned"], {job["chain"]: [leg["leg"] for leg in job["legs"]] for job in jobs},
       "batch.json names every planned MC chain and its legs")
    eq(M.mc_reading([mc_leg("L1")], {"MC-X": ["L1"]}), {"reading": "PASS", "chains": 1, "problems": []},
       "a planned MC job that ran its leg: PASS")


# ---------------------------------------------------------------------------------------------------- T34: WP1b dependency and fallback
def gm_world() -> dict:
    """A source L5 end's world line for GM's discriminator (3.15 item 7): one remembered item tile on RUSTBORO_CITY (a
    map the next leg starts on) and one on ROUTE101 (off the list)."""
    world = world_of([])
    world["maps"] = {"0:3": {"key": "0:3", "name": "R", "const": "RUSTBORO_CITY", "items": {"5,5": 1}},
                     "0:16": {"key": "0:16", "name": "S", "const": "ROUTE101", "items": {"3,3": 1}}}
    return world


def gm_dependency(M, tmp: Path, tried: list[str]):
    """GM's GOALS-ON A/B job resolved against its source chain's reached L5 end (the world line `gm_world()`, the
    snapshot's `tried_items` `tried`)."""
    gm = M.plan_jobs("GM", 2000001, data())
    out = tmp / "gm"
    reached_l5(M, tmp, world=gm_world(), tried=tried)({**gm[0], "out": str(out)})
    legs = {r["run_id"]: r for r in M.read_records(out) if r.get("record") == "leg"}
    return M.dependency_of(gm[1], legs, set(), out, {})


def pair_jobs(M, persona: str, starter: str) -> tuple[dict, dict]:
    """WP1's New Game chain of one pair and its first WP1b practice job."""
    jobs = M.plan_jobs("WP1", 2000001, data())
    source = next(j for j in jobs if j["kind"] == "chain" and (j["persona"], j["starter"]) == (persona, starter))
    return source, next(j for j in jobs if (j.get("depends_on") or {}).get("chain") == source["chain"])


def g1_stage(M, tmp: Path, persona: str, starter: str) -> dict:
    return {"REAL": fake_stage(M, tmp, "REAL", {"G1": {"persona": persona, "starter": starter, "starter_from": "job_file",
                                                       "made_by": "x"}})}


def case_t34_dependency(M, tmp):
    source, practice = wp1_pair(M)
    stage = fake_stage(M, tmp, "REAL", {"G1": {"persona": "Story", "starter": "TREECKO", "starter_from": "job_file",
                                               "made_by": "x"}})
    stages = {"REAL": (stage, json.loads((stage / "manifest.json").read_text(encoding="utf-8")))}
    found = M.dependency_of(practice, {}, set(), tmp, stages)
    ok(found is not None, "a WP1b job HAS a dependency (None would launch it at once, before its source)")
    eq(found[0], "skip", "launched before its source chain's reached L5 record: never (SKIP)")
    state, _ = M.dependency_of(practice, {M.run_id_of("WP1", source["chain"], "L4"): {"reached": True}}, set(), tmp,
                               stages)
    eq(state, "skip", "a fallback start taken while that chain still runs: never")
    state, start = M.dependency_of(practice, {}, {source["chain"]}, tmp, stages)
    eq((state, start["id"], start["fallback_for"]), ("ready", "G1", "STRE"), "a missed pair's G start carries fallback_for")
    # GM's A/B is DROPPED as VACUOUS when its source's end holds no discriminating tile (3.15 item 7; verifier round 1,
    # F3): here an UNTRIED item tile on RUSTBORO_CITY and a TRIED one on a map off the list
    eq(M.discriminator_tiles(gm_world(), {"memory": {"goals": {"tried_items": {"$set": ["0:16|3,3"]}}}}), [],
       "no discriminating tile: a tried tile off the list, an untried one on it")
    found = gm_dependency(M, tmp / "v", ["0:16|3,3"])
    ok(found[0] == "drop" and "VACUOUS" in str(found[1]), f"no discriminating tile: the A/B DROPPED as VACUOUS ({found})")
    # drive (2.1, 2.2): a fallback start plays its OWN starter (from its job file), never the plan's; a start of another
    # persona is never launched (a saved start keeps its game's persona)
    src, prac = pair_jobs(M, "Story", "TORCHIC")
    _, log, _ = sched(M, tmp / "fb", [src, prac], passes=2, stages=g1_stage(M, tmp / "fb", "Story", "TREECKO"))
    entry = next(e for e in log if e["chain"] == prac["chain"])
    eq((entry["job"]["start"]["id"], entry["job"]["starter"], entry["job"]["starter_from"]), ("G1", "TREECKO", "job_file"),
       "a Story/TORCHIC pair's fallback G1 plays G1's own TREECKO (job_file), never the plan's TORCHIC")
    result, log, _ = sched(M, tmp / "fp", [src, prac], passes=2, stages=g1_stage(M, tmp / "fp", "Catcher", "TORCHIC"))
    ok(prac["chain"] not in [e["chain"] for e in log], "a start of another persona is never launched")
    eq([why for chain, why in result["not_started"] if chain == prac["chain"]], ["its start G1 is a Catcher's"],
       "it is named in not_started")
    # the fallback SLOT (2.1; verifier round 3, N3): a missed chain's SECOND practice job (slot 1) takes its persona's
    # SECOND start, G2, never the first one
    slot1 = next(j for j in M.plan_jobs("WP1", 2000001, data()) if (j.get("depends_on") or {}).get("chain") ==
                 source["chain"] and (j.get("fallback") or {}).get("slot") == 1)
    two = fake_stage(M, tmp / "s2", "REAL", {sid: {"persona": "Story", "starter": "TREECKO", "starter_from": "job_file",
                                                   "made_by": "x"} for sid in ("G1", "G2")})
    state, start = M.dependency_of(slot1, {}, {source["chain"]}, tmp, {"REAL": (two, json.loads(
        (two / "manifest.json").read_text(encoding="utf-8")))})
    eq((state, start["id"], start["fallback_for"]), ("ready", "G2", "STRE"), "slot 1: the persona's second start, G2")
    # 3.7's start_memory.fallback_for (verifier round 3, N3; a fallback is counted apart): the leg a fallback start plays
    # records the pair it stands in for
    job = job_of(M, tmp / "fbleg", to="ch6_dewford", kind="practice", from_chapter=6, seed=7213)
    job["start"] = start
    stub = Stub(job, {})
    stub.truths[md5(Path(start["state"]))] = {"frame": 5000, "map": [0, 3], "state_md5": md5(Path(start["state"])),
                                              "story": {"marks": marks_through("ch5_rival_meet"), "stats": {}}}
    _, stub, records = play(M, job, {}, stub=stub)
    eq((len(stub.calls), records[0]["start_memory"]["fallback_for"]), (1, "STRE"),
       "a fallback start's leg: start_memory.fallback_for names its pair")
    # the dependency HANG GUARD (3.13; verifier round 2's V62, a NIT until round 3): a WP1b job whose source chain is not in
    # the batch (nothing runs, its dependency can never resolve) is DROPPED with the reason, never waited on forever
    result, log, _ = sched(M, tmp / "orphan", [practice])
    eq((log, [why for _, why in result["not_started"]]), ([], ["its dependency can never resolve (nothing runs)"]),
       "an orphaned WP1b job: DROPPED, never launched")
    # (fix round 3's sweep, N6) dependency_of's other DROPs: a REACHED source whose kept files are not all recorded; a
    # source chain that ENDED without a reached L5 for a job with no fallback; and, through drive (start_check's DROP of a
    # dependency), a missed chain's fallback start that is not on the stage: each DROPPED with its reason, never launched
    unkept = {M.run_id_of("WP1", source["chain"], "L5"): {"reached": True, "kept": {"folder": str(tmp)}}}
    state, why = M.dependency_of(practice, unkept, set(), tmp, stages)
    ok(state == "drop" and "kept files are not all recorded" in str(why), f"a source's kept files unrecorded: {state}, {why}")
    state, why = M.dependency_of({**practice, "fallback": None}, {}, {source["chain"]}, tmp, stages)
    ok(state == "drop" and "ended without a reached L5" in str(why), f"no fallback: {state}, {why}")
    result, log, _ = sched(M, tmp / "nofb", [source, practice], passes=2)
    eq(([e["chain"] for e in log], [why for chain, why in result["not_started"] if chain == practice["chain"]]),
       ([source["chain"]], [f"its source chain {source['chain']} missed and its fallback start G1 is not on the stage"]),
       "a fallback start not on the stage: DROPPED, never launched")


def case_t34_control(M, tmp):
    source, practice = wp1_pair(M)
    out = tmp / "out"
    reached_l5(M, tmp)({**source, "out": str(out)})
    legs = {r["run_id"]: r for r in M.read_records(out) if r.get("record") == "leg"}
    state, start = M.dependency_of(practice, legs, set(), out, {})
    eq((state, start["kind"]), ("ready", "chain_end"), "a reached source: from that end")
    ok(start["goals"] and Path(start["goals"]).is_file(), "with its snapshot")
    missed = {M.run_id_of("WP1", source["chain"], "L5"): {"reached": False}}
    stage = fake_stage(M, tmp, "REAL", {"G1": {"persona": "Story", "starter": "TREECKO", "starter_from": "job_file",
                                               "made_by": "x"}})
    stages = {"REAL": (stage, json.loads((stage / "manifest.json").read_text(encoding="utf-8")))}
    state, start = M.dependency_of(practice, missed, set(), out, stages)
    eq((state, start["id"]), ("ready", "G1"), "an L5 that missed: the fallback at once")
    p2 = next(j for j in M.plan_jobs("WP1", 2000001, data()) if j["arm"] == "WALL-BRINEY"
              and j["persona"] == "Story")
    eq((p2["depends_on"], p2["fallback"], p2["seed"]), (practice["depends_on"], practice["fallback"], practice["seed"]),
       "P2 takes its twin's start and seed")
    eq(M.discriminator_tiles(gm_world(), {"memory": {"goals": {"tried_items": {"$set": ["0:3|5,5"]}}}}), ["0:3|5,5"],
       "a tried item tile on RUSTBORO_CITY discriminates")
    state, start = gm_dependency(M, tmp / "v", ["0:3|5,5"])
    eq((state, start.get("discriminator")), ("ready", ["0:3|5,5"]), "the A/B runs, its discriminating tile recorded")
    _, log, _ = sched(M, tmp / "own", [source, practice], passes=3, on_end={source["chain"]: reached_l5(M, tmp / "own")})
    entry = next(e for e in log if e["chain"] == practice["chain"])
    eq((entry["job"]["start"]["kind"], entry["job"]["starter"], entry["job"]["starter_from"]), ("chain_end", "TREECKO", "plan"),
       "a start of the job's own persona (its source's L5 end) launches, the plan's starter kept")


# ---------------------------------------------------------------------------------------------------- T35: stale and K1
GONE = "not picked up: no item ball where it lay at (17, 7) any more"


def gone(tile: str) -> dict:
    return {"decision": "goal_end", "action": "pick_up", "reason": GONE, "extra": {"key": f"item:{tile}"}}


def case_t35_stale(M, tmp):
    stale = M.stale_measure("carried", {"24:7|17,7"}, [gone("24:7|3,3")], None)
    eq((stale["item_errands"], stale["gone_or_unreachable"]), (0, 1), "a tile NOT in tried_items is not an errand")
    _, _, records = practice_job(M, tmp, {"L6": {"records": [gone("24:7|17,7")]}}, goals={"tried": ["24:7|17,7"]},
                                 to="ch6_dewford", goals_policy="off")
    eq(records[0]["measures"]["stale"]["snapshot"], "kept", "GOALS-OFF: kept, not carried")
    ok(records[0]["measures"]["stale"]["item_errands"] != "unknown", "a GOALS-OFF leg's item_errands is never unknown")
    k1 = {"frame": 3, "decision": "tell", "reason": "[AI-GOALS] RUSTURF_TUNNEL is somewhere it has not been: first to "
                                                   "ROUTE116, a seasoned player's knowledge: ROUTE116 has a way into it"}
    fights, _ = M.fights_of([k1, {"decision": "world", "digest": "", "extra": {"kind": "trainer", "outcome": "won"}}])
    eq(fights[0]["foe"], None, "a K1 tell is never read as a foe")


def case_t35_control(M, tmp):
    stale = M.stale_measure("carried", {"24:7|17,7"}, [gone("24:7|17,7"), gone("24:7|17,7")], None)
    eq((stale["item_errands"], stale["item_outcomes"]), (1, 2), "a tile counted once however many outcomes")
    _, _, records = practice_job(M, tmp, {"L6": {"records": [gone("24:7|17,7"), gone("24:7|17,7")]}},
                                 goals={"tried": ["24:7|17,7"]}, to="ch6_dewford", goals_policy="off")
    stale = records[0]["measures"]["stale"]
    eq((stale["item_errands"], stale["snapshot"]), (1, "kept"), "GOALS-OFF: item_errands 1, snapshot kept")
    _, _, records = practice_job(M, tmp / "g1", {"L6": {"records": [gone("24:7|17,7")]}}, goals=False, to="ch6_dewford")
    stale = records[0]["measures"]["stale"]
    eq((stale["item_errands"], stale["snapshot"], stale["gone_or_unreachable"]), ("unknown", "none", 1),
       "a start with no snapshot")
    raw = (FIXTURES / "a1_k1_tells.jsonl").read_bytes()
    eq(hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), TELLS_SHA256, "the committed fixture's sha256")
    leads = M.k1_leads([json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()])
    eq((leads["count"], [lead["lead"] for lead in leads["leads"]]), (2, ["ROUTE116"]), "two real K1 tells, lead ROUTE116")


# ---------------------------------------------------------------------------------------------------- T36: boss prep and the raise reason
def raise_leg(M, tmp: Path, ended: bool, persona: str = "Story"):
    frames = 1_000_000
    start, end = 5000, 5000 + frames
    trans = [[f, *(("0:19", "24:11") if i % 2 == 0 else ("24:11", "0:19")), "warp", "ai", [1, 1], [2, 2], "up"]
             for i, f in enumerate(range(end - 100_000 - 59 * 100, end - 100_000 + 1, 100))]
    records = [{"frame": end - 99_000, "decision": "goal", "action": "raise", "reason": "raise for BRAWLY"}]
    if ended:
        records.append({"frame": end - 50_000, "decision": "goal_end", "action": "raise", "reason": "done"})
    plan = {"L6": {"miss": True, "exit": 4, "reason": "frame-budget", "real": frames, "transitions": trans,
                   "consts": {"0:19": "ROUTE104", "24:11": "PETALBURG_WOODS"}, "records": records}}
    return practice_job(M, tmp, plan, to="ch6_dewford", persona=persona)


def case_t36_raise(M, tmp):
    _, _, records = raise_leg(M, tmp, ended=False)
    record = records[0]
    eq(record["class"], M.CLEAN_BUDGET, "a CLEAN-BUDGET end")
    eq(record["blocker"]["key"][2], M.RAISE_TEXT, "the raise reason")
    eq(record["measures"]["loop"]["keyed"], "flag", "its own key, flagged, never LOOP")
    ok(record["blocker"]["key"][4] != "LOOP", "never the LOOP key")
    # through judge_leg and build_report (verifier round 3, N3): 3.7's raise_end read from the AI's log ("the raise ends,
    # budget spent"), and 3.8's BOSS-PREP BREAKDOWN of a chapter 6-7 key: a not-reached L6 leg that planned, raised and ran
    # out of budget, carrying in a snapshot with 2 battles lost
    plan = {"L6": {"miss": True, "exit": 4, "reason": "frame-budget", "real": 1_000_000, "records": [
        {"frame": 6000, "decision": "tell", "reason": PLAN_TELL},
        {"frame": 7000, "decision": "goal", "action": "raise", "reason": "raise for BRAWLY"},
        {"frame": 900_000, "decision": "goal_end", "action": "raise", "reason": "the budget is spent"}],
        "log": ["[AI-BOSSPREP] BRAWLY: the raise ends, budget spent (Mudkip at L14 of L16)"]}}
    _, _, records = practice_job(M, tmp / "bp", plan, goals={"losses": 2, "tried": []}, to="ch6_dewford")
    eq(records[0]["bossprep"]["raise_end"], "budget spent", "a raise ended by its budget, read from the AI's log")
    entry = next(b for b in M.build_report(Path(records[0]["kept"]["folder"]).parents[1])["blockers"] if b["chapter"] == 6)
    eq(entry.get("bossprep"), {"plan_made": 1, "raise_ended_by_budget": 1, "trainee_reached_target": 0,
                               "trainer_only_logged": 0, "losses_carried_in": 2, "losses_in_leg": 0},
       "the chapter 6 key's boss-prep breakdown")


#: a boss-prep plan tell in the form `brain/bossprep.py` writes it (T36)
PLAN_TELL = ("[AI-BOSSPREP] BRAWLY: the plan: raise Mudkip (0000beef) from L12 to L16 as the one who leads (close); a "
             "near-best option; the Trainer only logs it")


def case_t36_control(M, tmp):
    _, _, records = raise_leg(M, tmp, ended=True)
    record = records[0]
    eq(record["blocker"]["raw"][2], M.reason_norm("frame-budget"), "a raise that ended before the budget end: the leg's "
                                                                   "own reason")
    plan = {"L6": {"records": [{"frame": 6000, "decision": "tell",
                                "reason": "[AI-BOSSPREP] BRAWLY: the plan: raise Mudkip (0000beef) from L12 to L16 as the "
                                          "one who leads (close); a near-best option; the Trainer only logs it"}]}}
    _, _, records = practice_job(M, tmp / "t", plan, to="ch6_dewford", persona="Trainer")
    bossprep = records[0]["bossprep"]
    eq((bossprep["acting"], bossprep["raise_goals"]), ("logs only", 0), "a Trainer leg: acting logged only, no raise")
    eq(bossprep["plan"]["trainee"], "Mudkip", "its plan read")
    # (verifier round 3, N3) a raise the AI says is DONE ends "target reached", never "budget spent"; and a chapter 1-5
    # key carries no boss-prep breakdown
    plan = {"L6": {"records": [{"frame": 7000, "decision": "goal", "action": "raise", "reason": "raise for BRAWLY"},
                               {"frame": 9000, "decision": "goal_end", "action": "raise", "reason": "done"}],
                   "log": ["[AI-BOSSPREP] BRAWLY: the raise is done (Mudkip at L16)"]}}
    _, _, records = practice_job(M, tmp / "done", plan, to="ch6_dewford")
    eq(records[0]["bossprep"]["raise_end"], "target reached", "a raise that is done: target reached")
    job = job_of(M, tmp / "c1", to="ch1_pokedex", seed=7813)
    play(M, job, {"L1": {"miss": True}})
    blockers = M.build_report(Path(job["out"]))["blockers"]
    eq([(b["chapter"], "bossprep" in b) for b in blockers], [(1, False)], "a chapter 1 key: no boss-prep breakdown")


# ---------------------------------------------------------------------------------------------------- T37: --parallel under 1
def parallel_run(M, tmp: Path, parallel: int, env: dict | None = None, trainer: bool = True,
                 resume: bool = False) -> SimpleNamespace:
    """One P1 REAL job through the REAL run_batch (--trainer with a temp band ledger, or with `trainer` False development
    mode with an EMPTY temp ledger and a prediction file; a valid fake stage, stub children) with `--parallel parallel`,
    the job's env `env` and `--resume resume`; the planted clock FAILS past 50 passes, so a scheduler that admits no job
    fails this case fast instead of hanging the suite. Returns the exit, the printed text, the launches, whether the temp
    ledger is byte-unchanged, its entries and whether --out was made."""
    prediction = None
    if trainer:
        band_ledger(tmp / "ledger.json")
    else:
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "ledger.json").write_text(json.dumps({"what": "", "entries": []}), encoding="utf-8")
        prediction = tmp / "p.txt"
        prediction.write_text("T37 predicted\n", encoding="utf-8")
    band = (tmp / "ledger.json").read_bytes()
    stages = {"REAL": fake_stage(M, tmp, "REAL")}
    jobs = [job for job in M.plan_jobs("P1", 2000001, data()) if job["stage"] == "REAL"][:1]
    if env is not None:
        jobs[0]["env"] = env
    spawned: list = []
    code, text = refusal_of(M, batch_args(write_jobs(tmp, jobs), tmp / "out", stages, trainer=trainer,
                                          prediction=prediction, parallel=parallel, resume=resume),
                            batch_deps(M, tmp, log=spawned, limit=50))
    return SimpleNamespace(code=code, text=text, spawned=spawned, ledger_same=(tmp / "ledger.json").read_bytes() == band,
                           entries=ledger.load(tmp / "ledger.json")["entries"], out_made=(tmp / "out").exists())


def case_t37_parallel(M, tmp):
    # (fix round 5, verifier round 4's V4-N3, rated MAJOR by impact: the never-hang rule) P under 1 admits no job, so the
    # scheduler would wait forever: `run` refuses it before --out is made, with no ledger write and no launch
    for parallel in (0, -1):
        r = parallel_run(M, tmp / f"p{parallel}", parallel)
        eq((r.code, r.spawned, r.ledger_same, r.out_made), (2, [], True, False),
           f"--parallel {parallel}: refused (exit 2), nothing launched, the ledger byte-unchanged, --out not made "
           f"({r.text[-300:]!r})")
        ok(f"REFUSED: --parallel {parallel} is under 1" in r.text, f"the refusal names the value: {r.text[-300:]!r}")
    # (fix round 6, verifier round 6's V6-2) the refusal is not a trainer-only one: in DEVELOPMENT mode --parallel 0 is
    # refused before ledger.begin (the temp ledger holds no entry) and before --out is made
    r = parallel_run(M, tmp / "dev0", 0, trainer=False)
    eq((r.code, r.spawned, r.ledger_same, r.entries, r.out_made), (2, [], True, [], False),
       f"development mode, --parallel 0: refused, nothing launched, no ledger entry, --out not made ({r.text[-300:]!r})")
    ok("REFUSED: --parallel 0 is under 1" in r.text, f"development mode names the refusal: {r.text[-300:]!r}")
    # ... and it is not skipped on --resume: the --parallel refusal is among the REFUSED lines of a resume
    r = parallel_run(M, tmp / "res0", 0, resume=True)
    refusals = [line for line in r.text.splitlines() if line.startswith("REFUSED: ")]
    eq((r.code, r.spawned), (2, []), f"--resume with --parallel 0: refused, nothing launched ({r.text[-300:]!r})")
    ok(any(line.startswith("REFUSED: --parallel 0 is under 1") for line in refusals),
       f"--resume: the --parallel refusal is among the REFUSED lines: {refusals}")


def case_t37_control(M, tmp):
    r = parallel_run(M, tmp / "p1", 1)
    eq((r.code, r.spawned, r.ledger_same), (0, [("spawn", "REAL-N-STRE-2000001")], True), "--parallel 1 runs its one job")
    ok("--parallel" not in r.text, f"no --parallel refusal at 1: {r.text[-300:]!r}")
    # (fix round 6, V6-2's CONTROLs) development mode at --parallel 1 runs its job; a --resume at --parallel 1 (refused for
    # its missing batch.json) carries no --parallel refusal
    r = parallel_run(M, tmp / "dev1", 1, trainer=False)
    eq((r.code, r.spawned, len(r.entries)), (0, [("spawn", "REAL-N-STRE-2000001")], 1),
       f"development mode, --parallel 1: runs its one job, one ledger entry ({r.text[-300:]!r})")
    ok("--parallel" not in r.text, f"development mode: no --parallel refusal at 1: {r.text[-300:]!r}")
    r = parallel_run(M, tmp / "res1", 1, resume=True)
    ok(r.code == 2 and "holds no batch.json" in r.text and "--parallel" not in r.text,
       f"--resume at --parallel 1: refused for its batch.json only, no --parallel refusal: {r.text[-300:]!r}")


# ---------------------------------------------------------------------------------------------------- T38: a job's env is EMPTY
def case_t38_job_env(M, tmp):
    # (fix round 5) the probe derives every launch key itself (run_job's `sent`) and never sends a job's own env, so a key
    # there would be silently dropped: plan and run refuse ANY key, the allowed ones each named
    msg = refused(M, M.plan_jobs, "P1", 6601, data(), None, {ENV_TARGET: "ch1_pokedex"})
    ok(f"{ENV_TARGET} is set by the probe itself" in msg, f"plan refuses an allowed key: {msg}")
    for key in M.ENV_ALLOWED:
        jobs = M.plan_jobs("P1", 6601, data())
        jobs[0]["env"] = {key: "1"}
        ok(any(p.endswith(f"{key} is set by the probe itself: a job's env is never sent") for p in M.jobs_problems(jobs)),
           f"jobs_problems refuses a job env naming {key}")
    # (the lead, 2026-11-15: verifier round 6's V6-3, V6M1) an MC job's env is refused the same way, each allowed key named
    msg = refused(M, M.plan_jobs, "MC", 6701, data(), "ch1_pokedex", {"AI_PLAYER_CLOCK": "10:00"})
    ok("AI_PLAYER_CLOCK is set by the probe itself" in msg, f"plan refuses an allowed key on an MC job: {msg}")
    for key in M.ENV_ALLOWED:
        jobs = M.plan_jobs("MC", 6701, data(), "ch1_pokedex")
        jobs[0]["env"] = {key: "1"}
        ok(any(p.endswith(f"{key} is set by the probe itself: a job's env is never sent") for p in M.jobs_problems(jobs)),
           f"jobs_problems refuses an MC job env naming {key}")
    r = parallel_run(M, tmp / "clock", 1, env={"AI_PLAYER_CLOCK": "1"})
    eq((r.code, r.spawned, r.ledger_same, r.out_made), (2, [], True, False),
       f"run: a jobs.json whose job env names AI_PLAYER_CLOCK: refused, no launch, no ledger write, --out not made "
       f"({r.text[-300:]!r})")
    ok("AI_PLAYER_CLOCK is set by the probe itself" in r.text, f"the refusal names the key: {r.text[-300:]!r}")


def case_t38_control(M, tmp):
    for batch, first, to in (("P1", 6601, None), ("GM", 6611, None), ("WP1", 6621, None), ("MC", 6701, "ch1_pokedex")):
        jobs = M.plan_jobs(batch, first, data(), to)
        eq(([j["env"] for j in jobs if j["env"] != {}], M.jobs_problems(jobs)), ([], []),
           f"every {batch} job carries env {{}} and is accepted")
    r = parallel_run(M, tmp / "empty", 1, env={})
    eq((r.code, r.spawned), (0, [("spawn", "REAL-N-STRE-2000001")]), "a job whose env is {} runs")


# ---------------------------------------------------------------------------------------------------- AM-11: compare and replay
def moves(*pairs) -> list[dict]:
    return [{"frame": f, "decision": "decide", "action": a, "reason": "r"} for f, a in pairs]


def case_am11_compare(M, tmp):
    a = moves((10, "press A"), (20, "press B"), (31, "press UP"))
    b = moves((10, "press A"), (20, "press B"), (32, "press UP"))
    index, text = M.compare_moves(a, b)
    eq(index, 2, "a one-frame split found at its index")
    ok("FIRST DIFFERENT MOVE at index 2" in text, text)
    path = tmp / "a.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in [{"frame": 5, "decision": "say", "action": "say"},
                                                           {"frame": 6, "decision": "world", "action": "x"},
                                                           *a]), encoding="utf-8")
    eq(len(M.load_moves(path)), 3, "'say' and 'world' records skipped")


def case_am11_compare_control(M, tmp):
    a = moves((10, "press A"), (20, "press B"))
    eq(M.compare_moves(a, copy.deepcopy(a))[0], None, "identical: no split (a determinism check, never a replication)")


def replay_setup(M, tmp: Path):
    _, _, records = practice_job(M, tmp, {}, to="ch6_dewford")
    folder = Path(records[0]["kept"]["folder"])
    stage = tmp / "stage"
    donor(stage / "build")
    return records[0], folder, stage


def replay_quiet(M, *args, **kwargs):
    saved = (L5.PROFILE, L5.REPO)
    try:
        with mock.patch.dict(os.environ, {}), redirect_stdout(io.StringIO()):
            return M.replay(*args, **kwargs)
    finally:
        L5.PROFILE, L5.REPO = saved


def case_am11_replay(M, tmp):
    record, folder, stage = replay_setup(M, tmp)
    (folder / "world_last.jsonl").unlink()
    refused(M, replay_quiet, M, folder, stage, "ai-fp-replay-1", run_leg=lambda *a: None)
    record, folder, stage = replay_setup(M, tmp / "b")
    (stage / "build" / "profiles" / "ai-fp-replay-1").mkdir(parents=True)
    refused(M, replay_quiet, M, folder, stage, "ai-fp-replay-1", run_leg=lambda *a: None)
    # replay SANITIZES the environment before its launch (3.11; verifier round 1's V09, a NIT until round 3): a parent's
    # AI_PLAYER_FAULT_*, POKEBOT_* and PYTHONPATH are gone when the leg is launched
    record, folder, stage = replay_setup(M, tmp / "env")
    planted = {"AI_PLAYER_FAULT_NO_HINTS": "1", "POKEBOT_BOSSMODE_TOPUP": "1", "PYTHONPATH": "x"}
    environs: list = []
    with mock.patch.dict(os.environ, planted):
        replay_quiet(M, folder, stage, "ai-fp-replay-2", run_leg=lambda arm, build, carried: environs.append(
            dict(os.environ)) or SimpleNamespace(exit_code=0, elapsed=1.0, run_dir=None))
    eq(sorted(name for name in planted if name in environs[0]), [], "none of the parent's variables at the launch")
    # an MC example is replayed as MC plays (2.4b; verifier round 3, N7): its KEPT goal snapshot is never sent
    arms, folder, stage = mc_replay(M, tmp / "mc")
    ok((folder / "goals_last.jsonl").is_file() and ENV_GOALS not in arms[0].env,
       f"an MC example's kept snapshot is never sent: {sorted(arms[0].env)}")
    # (fix round 3's sweep, N6) replay refuses a folder no leg record keeps (a copy elsewhere in --out), and a profile that
    # is not a probe profile
    record, folder, stage = replay_setup(M, tmp / "c")
    lone = Path(record["kept"]["folder"]).parents[1] / "elsewhere" / "L9"
    shutil.copytree(folder, lone)
    refused(M, replay_quiet, M, lone, stage, "ai-fp-replay-4", run_leg=lambda *a: None)
    refused(M, replay_quiet, M, folder, stage, "endless-P1-x", run_leg=lambda *a: None)


def mc_replay(M, tmp: Path) -> tuple[list, Path, Path]:
    """ONE MC leg played (it keeps a goal snapshot, as every leg does), then replayed from its kept example: (the arms the
    replay launched, the example folder, the stage)."""
    job = job_of(M, tmp, to="ch1_pokedex", seed=6708, mc=True, goals="never")
    _, _, records = play(M, job, {})
    folder = Path(records[0]["kept"]["folder"])
    stage = tmp / "stage"
    donor(stage / "build")
    arms: list = []
    replay_quiet(M, folder, stage, "ai-fp-replay-3", run_leg=lambda arm, build, carried: arms.append(arm) or
                 SimpleNamespace(exit_code=0, elapsed=1.0, run_dir=None))
    return arms, folder, stage


def case_am11_replay_control(M, tmp):
    record, folder, stage = replay_setup(M, tmp)
    seen = []

    def run_leg(arm, build, carried):
        seen.append((arm, build, {k: tuple(str(p) for p in v[:2]) for k, v in carried.items()}))
        return SimpleNamespace(exit_code=0, elapsed=1.0, run_dir=None)
    eq(replay_quiet(M, folder, stage, "ai-fp-replay-1", seed=99, run_leg=run_leg), 0, "a replay ran")
    arm, build, carried = seen[0]
    eq((arm.seed, arm.state_from, arm.fresh), (99, "EXAMPLE", False), "a new seed, from the example")
    eq(carried["EXAMPLE"], (str(folder / "end_state.ss1"), str(folder / "world_last.jsonl")), "the kept state and line")
    eq(arm.env[ENV_GOALS], str(folder / "goals_last.jsonl"), "the kept goal snapshot")
    eq(Path(build), stage / "build", "on the stage's build root")
    # (verifier round 3) the sanitize keeps a variable off its strip list
    environs: list = []
    record, folder, stage = replay_setup(M, tmp / "env")
    with mock.patch.dict(os.environ, {"A1FP_HARMLESS": "kept"}):
        replay_quiet(M, folder, stage, "ai-fp-replay-2", run_leg=lambda arm, build, carried: environs.append(
            dict(os.environ)) or SimpleNamespace(exit_code=0, elapsed=1.0, run_dir=None))
    eq(environs[0].get("A1FP_HARMLESS"), "kept", "a variable off the strip list reaches the launch")


# ==================================================================================================== THE TESTS
class Base(unittest.TestCase):
    def case(self, fn) -> None:
        tmp = Path(tempfile.mkdtemp(prefix=f"{fn.__name__}_", dir=_TEMP_ROOT))
        fn(FP, tmp)


#: (T id, FAULT case, CONTROL case): every guard of 4.1
CASES = [
    ("T1", case_t1_refused, case_t1_control), ("T1b", case_t1b_gate_timeout, case_t1b_control),
    ("T2", case_t2_budget, case_t2_control), ("T2b", case_t2b_missing_verdict, case_t2b_control),
    ("T3", case_t3_freshness, case_t3_control), ("T4", case_t4_not_clean, case_t4_control),
    ("T5", case_t5_claim, case_t5_control), ("T6", case_t6_clustering, case_t6_control),
    ("T7", case_t7_next_unmet, case_t7_control), ("T8", case_t8_ranking, case_t8_control),
    ("T9", case_t9_env, case_t9_control), ("T10", case_t10_trainer, case_t10_control),
    ("T11", case_t11_placement, case_t11_control), ("T12", case_t12_band, case_t12_control),
    ("T13", case_t13_seeds, case_t13_control), ("T14", case_t14_disk, case_t14_control),
    ("T15", case_t15_retention, case_t15_control), ("T16", case_t16_filter, case_t16_control),
    ("T17", case_t17_origin, case_t17_control), ("T18", case_t18_continue, case_t18_control),
    ("T19", case_t19_custody, case_t19_control), ("T20", case_t20_donor, case_t20_control),
    ("T21", case_t21_stage_watch, case_t21_control), ("T22", case_t22_ai_stop, case_t22_control),
    ("T23", case_t23_schema, case_t23_control), ("T24", case_t24_resume, case_t24_control),
    ("T24d", case_t24d_resume, case_t24d_control),
    ("T25", case_t25_deadline, case_t25_control), ("T26", case_t26_scheduler, case_t26_control),
    ("T27", case_t27_agreement, case_t27_control), ("T28", case_t28_imports, case_t28_control),
    ("T29", case_t29_mutant, case_t29_control), ("T30", case_t30_copies, case_t30_control),
    ("T31", case_t31_loop, case_t31_control), ("T32", case_t32_goal_custody, case_t32_control),
    ("T33", case_t33_mc, case_t33_control), ("T34", case_t34_dependency, case_t34_control),
    ("T35", case_t35_stale, case_t35_control), ("T36", case_t36_raise, case_t36_control),
    ("T37", case_t37_parallel, case_t37_control), ("T38", case_t38_job_env, case_t38_control),
    ("AM11c", case_am11_compare, case_am11_compare_control), ("AM11r", case_am11_replay, case_am11_replay_control),
]


class GuardTests(Base):
    """One FAULT and one CONTROL test per guard (T1-T38); the methods are made from CASES below."""


def _make(fn):
    return lambda self: self.case(fn)


for _tid, _fault, _control in CASES:
    setattr(GuardTests, f"test_{_tid.lower()}_fault", _make(_fault))
    setattr(GuardTests, f"test_{_tid.lower()}_control", _make(_control))


def load_module(tmp: Path, name: str, anchor: str | None = None, replacement: str | None = None):
    """`frontier_probe.py` (with `anchor` replaced exactly once) loaded from a temp `ai_player/gates/frontier_probe.py`,
    its REPO, GATES and EVIDENCE_DIR rebound to this tree's: the copy a guard-removed FAULT run uses (never the tree).
    RAISES RuntimeError when the anchor is not unique."""
    text = SOURCE.read_text(encoding="utf-8")
    if anchor is not None:
        count = text.count(anchor)
        if count != 1:
            raise RuntimeError(f"{name}: the anchor hits {count} times: {anchor!r}")
        text = text.replace(anchor, replacement)
    path = tmp / name / "ai_player" / "gates" / "frontier_probe.py"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"frontier_probe_mut_{name}", path)
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


def run_case(module, fn) -> str | None:
    """None when `fn` passes on `module`, else the AssertionError's text (any other exception is reported as such)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"mut_{fn.__name__}_", dir=_TEMP_ROOT))
    try:
        fn(module, tmp)
    except AssertionError as error:
        return f"AssertionError: {error}"[:400]
    except Exception as error:  # noqa: BLE001
        return f"{type(error).__name__}: {error}"[:400]
    return None


class CopyLoadTests(Base):
    """The CONTROL of the guard-removed runs: the UNCHANGED source loaded as a copy passes every case."""

    def test_the_unchanged_copy_passes_every_case(self) -> None:
        module = load_module(Path(tempfile.mkdtemp(prefix="copy_", dir=_TEMP_ROOT)), "M0")
        failed = [(fn.__name__, why) for _, fault, control in CASES for fn in (fault, control)
                  if (why := run_case(module, fn)) is not None]
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
