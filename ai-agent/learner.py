"""The Emerald AI strategy learner. It runs 24/7 on this PC and spends no AI credits.

Each CYCLE:
1. sizes itself to the machine (lanes = parallel games, in fours, one per starter for each strategy);
2. picks one strategy per four lanes (`brain.choose_arms`): the current best as the control, an inbox proposal, then
   the next rows of a screening design that measures every knob's own effect;
3. runs them side by side through the story bot's own batch runner (`tools/story-dev/x4_headless.py --arms`), which
   plays real games in the emulator and refuses anything malformed;
4. turns the logs into small run records (`scoring.py`), updates what it has learned and rewrites
   `findings/LATEST.md` (`report.py`);
5. optionally asks Claude for advice (`consult.py`, off by default);
6. deletes its own old raw logs, keeping the newest `keep_raw_cycles` cycles.

Resilience:
- If the learner dies mid-cycle, the batch keeps running. The next start ADOPTS it: it waits for that batch to end,
  then scores it, so no cycle is lost.
- Between cycles, if its own code has changed and `test_agent.py` passes, it exits with code 3 so the wrapper
  restarts it into the new code. If the tests fail, it keeps running the old code and says so.

Safety: it never edits code and never runs git. It writes only inside `ai-agent/`, plus the batch runner's lane
profiles, which it deletes later by exact name. One instance at a time (a lock). It waits instead of starting while
another batch is running, stops cleanly when the `STOP` file exists, and after repeated failures pauses and writes
`findings/ATTENTION.md` instead of retrying forever.

Commands (run from this folder with `py -3.12 learner.py <command>`):
  run        the 24/7 loop (what `run_agent.ps1` starts)
  once       exactly one cycle, then exit
  plan       show the next cycle's strategies and the exact batch command, without running anything
  ingest D   add an existing batch directory's runs as data (e.g. step 14's)
  reparse    re-read every batch whose raw logs still exist with the current parser (after a parser upgrade)
  report     rewrite findings/LATEST.md from the data
  status     where the learner is now
  publish    copy the findings and data into published/, small enough to commit for a cloud session
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

import psutil

AI = Path(__file__).resolve().parent
sys.path.insert(0, str(AI))
import brain  # noqa: E402
import consult  # noqa: E402
import knowledge as K  # noqa: E402
import report  # noqa: E402
import scoring  # noqa: E402

REPO = AI.parent
STORY_DEV = REPO / "tools" / "story-dev"
PROFILES = REPO / "sandbox-pokebot" / "profiles"
DATA, FINDINGS, INBOX, RUNS, PUBLISHED = AI / "data", AI / "findings", AI / "inbox", AI / "runs", AI / "published"
RUNS_FILE, CYCLES_FILE, STATE_FILE = DATA / "runs.jsonl", DATA / "cycles.jsonl", DATA / "state.json"
LOCK, LOG, STOP, ATTENTION = DATA / "agent.lock", DATA / "learner.log", AI / "STOP", FINDINGS / "ATTENTION.md"
RESTART_CODE = 3

DEFAULTS = {
    "lanes": "auto", "max_lanes": 24, "reserve_threads": 4, "reserve_ram_gb": 8, "ram_per_lane_gb": 1.5,
    "cycle_minutes": 720, "keep_raw_cycles": 3, "min_free_gb": 25, "design": "screen", "auto_update": True,
    "objective": "human_balanced",
    "wait_if_other_bots_running": True, "idle_wait_minutes": 15, "max_consecutive_failures": 3,
    "max_proposals_per_cycle": 1, "two_flip_prob": 0.3,
    "consult": {"enabled": False, "max_calls_per_day": 2, "model": "sonnet", "max_usd_per_call": 0.75,
                "timeout_minutes": 20, "max_waiting_proposals": 6},
}


#: config `objective` -> the run-record field the learner ranks by (USER RULINGS 32/33, `HUMAN-PLAY-DESIGN.md`).
OBJECTIVES = {"progress": "score", "human_balanced": "human_score"}


def score_key(cfg: dict) -> str:
    return OBJECTIVES.get(str(cfg.get("objective", "human_balanced")), "human_score")


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")


def log(msg: str) -> None:
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    DATA.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    path = AI / "config.json"
    if path.exists():
        user = json.loads(path.read_text(encoding="utf-8"))
        for k, v in user.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    if "_override_lanes" in DEFAULTS:
        cfg["lanes"] = DEFAULTS["_override_lanes"]
    if "_override_minutes" in DEFAULTS:
        cfg["cycle_minutes"] = DEFAULTS["_override_minutes"]
    return cfg


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"cycle": 0, "cycles": [], "current": None, "failures": 0}


def save_state(state: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, default=str), encoding="utf-8")
    tmp.replace(STATE_FILE)


def code_signature(folder: Path = AI) -> str:
    """A hash of the learner's own Python files: it changes when anyone edits the code."""
    h = hashlib.sha1()
    for p in sorted(folder.glob("*.py")):
        h.update(p.name.encode() + b"\0" + p.read_bytes())
    return h.hexdigest()[:12]


#: The learner RUNS only from a deployment checkout: a separate full clone (2026-10-03), so commits made while
#: developing never move the HEAD its batches run on. The batch runner's freeze watch aborts a cycle when HEAD moves,
#: and a docs-only commit on the main checkout killed cycle ai0002 that way. This file (git-ignored) marks the clone.
DEPLOYMENT = AI / "DEPLOYMENT"


def update_commands() -> list[list[str]]:
    """The ONLY git the learner runs: in its own clone, between cycles, fetch and fast-forward. A fast-forward
    cannot discard anything, and the clone carries no local work."""
    return [["git", "-C", str(REPO), "fetch", "--quiet", "origin"],
            ["git", "-C", str(REPO), "merge", "--ff-only", "--quiet", "origin/main"]]


def update_checkout() -> str:
    """Fast-forward the deployment clone to origin/main. Returns a one-line outcome for the log."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=120)
    try:
        if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
            return "update: skipped, the deployment clone has tracked changes (it should never have any)"
        before = git("rev-parse", "--short", "HEAD").stdout.strip()
        for cmd in update_commands():
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                return f"update: `{' '.join(cmd[3:])}` failed: {(r.stderr or r.stdout).strip()[:200]}"
        after = git("rev-parse", "--short", "HEAD").stdout.strip()
        return f"update: {before} -> {after}" if before != after else ""
    except Exception as exc:
        return f"update: failed: {exc!r}"


def tests_pass() -> bool:
    try:
        return subprocess.run([sys.executable, str(AI / "test_agent.py")], cwd=AI, capture_output=True,
                              timeout=600).returncode == 0
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------- safety checks
def acquire_lock() -> str | None:
    """None if this process now holds the lock, else why not."""
    DATA.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip())
        except ValueError:
            pid = -1
        if pid != os.getpid() and psutil.pid_exists(pid):
            try:
                if "learner.py" in " ".join(psutil.Process(pid).cmdline()):
                    return f"another learner is running (pid {pid})"
            except psutil.Error:
                pass
    LOCK.write_text(str(os.getpid()))
    return None


def release_lock() -> None:
    try:
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def _cmdlines():
    me = os.getpid()
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            if p.info["pid"] != me:
                yield p.info["pid"], " ".join(p.info["cmdline"] or [])
        except (psutil.Error, TypeError):
            continue


def other_bots_running() -> tuple[list[str], list[str]]:
    """(BATCHES, SINGLES) running on this PC now. A batch (`x4_headless.py`) or a harness drive (`story_harness.py`) is
    active work the learner must not compete with: it waits. A single bot (`pokebot.py`, e.g. a GUI window left open)
    only costs a lane's worth of CPU: the learner reserves a thread for each. Lanes of a batch are not singles."""
    batches, singles = [], []
    for pid, cmd in _cmdlines():
        if "x4_headless.py" in cmd or "story_harness.py" in cmd:
            batches.append(f"pid {pid}: {cmd[:120]}")
        elif "pokebot.py" in cmd and "--endless-target" not in cmd:
            singles.append(f"pid {pid}: {cmd[:120]}")
    return batches, singles


def batch_running(cdir: Path) -> bool:
    """True while the batch runner that writes into `cdir` is alive."""
    return any("x4_headless.py" in cmd and str(cdir) in cmd for _, cmd in _cmdlines())


def size_lanes(cfg: dict, singles: int = 0) -> tuple[int, str]:
    """(lanes, why). A multiple of 4 (one lane per starter for each strategy), measured now. `singles` = other single
    bots running, one thread reserved for each."""
    if str(cfg["lanes"]) != "auto":
        return int(cfg["lanes"]) // 4 * 4, "fixed in config.json"
    logical = psutil.cpu_count(logical=True) or 4
    free_gb = psutil.virtual_memory().available / 2 ** 30
    by_cpu = logical - int(cfg["reserve_threads"]) - singles
    by_ram = int((free_gb - float(cfg["reserve_ram_gb"])) / float(cfg["ram_per_lane_gb"]))
    n = max(0, min(int(cfg["max_lanes"]), by_cpu, by_ram)) // 4 * 4
    return n, f"auto: {logical} threads, {free_gb:.0f} GB free -> cpu {by_cpu}, ram {by_ram}, cap {cfg['max_lanes']}"


def free_gb() -> float:
    return shutil.disk_usage(AI).free / 2 ** 30


def attention(reason: str) -> None:
    FINDINGS.mkdir(parents=True, exist_ok=True)
    ATTENTION.write_text(f"# The learner paused itself\n\n{now()}\n\n{reason}\n\nFix the cause, delete this file, "
                         f"then start the learner again (`run_agent.ps1`).\n", encoding="utf-8")
    log(f"PAUSED for attention: {reason}")


# ------------------------------------------------------------------------------------------------------------- inbox
def read_inbox() -> list[dict]:
    """Valid waiting proposals, oldest first. An invalid one is moved to inbox/rejected/ with the reason."""
    out = []
    for path in sorted(INBOX.glob("*.json"), key=lambda p: p.stat().st_mtime):
        try:
            p = json.loads(path.read_text(encoding="utf-8"))
            errors = K.validate_genes(p.get("genes", {})) if isinstance(p.get("genes"), dict) else ["no genes"]
        except ValueError as exc:
            errors = [f"not JSON: {exc}"]
        if errors:
            (INBOX / "rejected").mkdir(exist_ok=True)
            shutil.move(str(path), INBOX / "rejected" / path.name)
            (INBOX / "rejected" / (path.stem + ".why.txt")).write_text("\n".join(errors), encoding="utf-8")
            log(f"inbox: rejected {path.name}: {errors}")
            continue
        p["_file"] = path.name
        out.append(p)
    return out


# ------------------------------------------------------------------------------------------------------------- cycle
def plan_cycle(cfg: dict, state: dict, lanes: int) -> dict:
    records = load_jsonl(RUNS_FILE)
    proposals = read_inbox()
    k = lanes // 4
    design, design_name = None, None
    if cfg.get("design") in ("screen", "pb12"):
        design_name, rows = brain.screen_rows()
        if rows:
            # A new knob changes the design's size; its row pointer then starts again at row 1.
            start = int(state.get("design_next", 0)) if state.get("design_name", "pb12") == design_name else 0
            design = {"rows": rows, "next": start}
    picks = brain.choose_arms(k, brain.summarize(records, score_key(cfg)), proposals, random.Random(),
                              float(cfg["two_flip_prob"]), int(cfg["max_proposals_per_cycle"]), design)
    n = state["cycle"] + 1
    while any(PROFILES.glob(f"endless-ai{n:04d}-*")) or (RUNS / f"ai{n:04d}").exists():
        n += 1
    tag = f"ai{n:04d}"
    names = [chr(ord("A") + i) for i in range(len(picks))]
    # A proposal counts as used when its genome runs this cycle, whoever picked it (it may equal the incumbent).
    running = {brain.genome_id(g) for g, _ in picks}
    used = [p.get("_file") for p in proposals if brain.genome_id(p["genes"]) in running]
    return {"n": n, "tag": tag, "lanes": lanes, "minutes": float(cfg["cycle_minutes"]),
            "design_next": design["next"] if design else state.get("design_next", 0),
            "design_name": design_name if design else state.get("design_name"),
            "arms": {name: {"genome": brain.genome_id(g), "label": brain.label(g), "why": why,
                            "env": brain.full_env(g)} for name, (g, why) in zip(names, picks)},
            "proposal_files": [f for f in used if f]}


def batch_command(plan: dict, cdir: Path) -> list[str]:
    return [sys.executable, str(STORY_DEV / "x4_headless.py"), "--build", "sandbox", "--lanes", str(plan["lanes"]),
            "--minutes", str(plan["minutes"]), "--arms", str(cdir / "arms.json"), "--profile-tag", plan["tag"],
            "--out", str(cdir / "batch")]


def run_cycle(cfg: dict, state: dict, lanes: int) -> bool:
    plan = plan_cycle(cfg, state, lanes)
    tag, cdir = plan["tag"], RUNS / plan["tag"]
    cdir.mkdir(parents=True)
    spec = {"comment": f"ai-agent cycle {tag}: " + "; ".join(f"{a}={v['label']}" for a, v in plan["arms"].items()),
            "arms": {a: v["env"] for a, v in plan["arms"].items()}}
    (cdir / "arms.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (cdir / "plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    state["cycle"] = plan["n"]
    state["design_next"] = plan["design_next"]
    state["design_name"] = plan.get("design_name")
    state["current"] = {"tag": tag, "started": now(), "lanes": lanes, "minutes": plan["minutes"]}
    save_state(state)
    for a, v in plan["arms"].items():
        log(f"{tag} arm {a} = {v['genome']} {v['label']} | {v['why']}")
    env = {k: v for k, v in os.environ.items() if not k.startswith("POKEBOT_")}
    env["PYTHONUTF8"] = "1"
    log(f"{tag}: starting {lanes} lanes for {plan['minutes']:.0f} minutes")
    with open(cdir / "x4.out.txt", "w", encoding="utf-8") as out:
        rc = subprocess.run(batch_command(plan, cdir), cwd=STORY_DEV, env=env, stdout=out,
                            stderr=subprocess.STDOUT).returncode
    return finish_cycle(cfg, load_state(), plan, rc)


def finish_cycle(cfg: dict, state: dict, plan: dict, rc) -> bool:
    """Score a finished batch and record it. Used both after a normal run and when ADOPTING an orphaned one."""
    tag = plan["tag"]
    batch = RUNS / tag / "batch"
    records = []
    if (batch / "ARMS.json").exists():
        try:
            records = scoring.parse_batch(batch, tag)
        except Exception:  # a half-written batch must not kill the learner; the reason goes to the log
            log(f"{tag}: parsing failed:\n{traceback.format_exc()}")
    for r in records:
        r["genome_id"] = brain.genome_id(r["genome"])
    append_jsonl(RUNS_FILE, records)
    usable = sum(1 for r in records if r.get("usable"))
    meta = json.loads((batch / "ARMS.json").read_text(encoding="utf-8")) if (batch / "ARMS.json").exists() else {}
    created = [str(batch)] + [str(PROFILES / ln["profile"]) for ln in meta.get("lanes", [])]
    cycle = {"source": "cycle", "tag": tag, "finished": now(), "exit": rc, "lanes": plan["lanes"],
             "runs": len(records), "usable": usable,
             "arms_label": ", ".join(f"{a}={v['genome']}" for a, v in plan["arms"].items()),
             "code_commit": meta.get("code_commit"), "created": created, "pruned": False}
    append_jsonl(CYCLES_FILE, [{k: v for k, v in cycle.items() if k != "created"}])
    state["cycles"].append(cycle)
    state["current"] = None
    ok = usable > 0
    if ok:
        for f in plan.get("proposal_files", []):
            (INBOX / "done").mkdir(parents=True, exist_ok=True)
            if (INBOX / f).exists():
                shutil.move(str(INBOX / f), INBOX / "done" / f)
    save_state(state)
    log(f"{tag}: batch exit {rc}; {len(records)} runs logged, {usable} scored")
    report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status=f"after cycle {tag}")
    log(consult.maybe_consult(cfg, REPO, AI, tag))
    prune(cfg, state)
    return ok


def adopt_unfinished(cfg: dict) -> bool | None:
    """If a previous learner died mid-cycle, finish that cycle: wait for its batch, then score it.
    None = nothing to adopt; False = STOP appeared while waiting; True/False otherwise = the cycle's outcome."""
    state = load_state()
    cur = state.get("current")
    if not cur:
        return None
    tag = cur["tag"]
    cdir = RUNS / tag
    if tag in {c.get("tag") for c in state["cycles"]} or not (cdir / "plan.json").exists():
        log(f"adopt: {tag} has no plan or is already recorded; clearing it")
        state["current"] = None
        save_state(state)
        return None
    if batch_running(cdir):
        log(f"adopt: {tag}'s batch is still running (the previous learner stopped mid-cycle); waiting for it")
        while batch_running(cdir):
            if not sleep_unless_stopped(2):
                return False
    log(f"adopt: scoring {tag}")
    plan = json.loads((cdir / "plan.json").read_text(encoding="utf-8"))
    return finish_cycle(cfg, state, plan, "adopted")


def prune(cfg: dict, state: dict) -> None:
    """Delete raw logs and lane profiles of all but the newest `keep_raw_cycles` cycles. Only paths this learner
    created and recorded, and only names it would have created."""
    keep = int(cfg["keep_raw_cycles"])
    for c in state["cycles"][:-keep] if keep > 0 else state["cycles"]:
        if c.get("pruned"):
            continue
        for p in map(Path, c.get("created", [])):
            ours = (p.parent == RUNS / c["tag"] and p.name == "batch") or \
                   (p.parent == PROFILES and p.name.startswith(f"endless-{c['tag']}-"))
            if ours and p.exists():
                shutil.rmtree(p, ignore_errors=True)
        c["pruned"] = True
        log(f"pruned the raw logs of {c['tag']} (its run records are kept)")
    save_state(state)


def sleep_unless_stopped(minutes: float) -> bool:
    """False if STOP appeared while waiting."""
    end = time.time() + 60 * minutes
    while time.time() < end:
        if STOP.exists():
            return False
        time.sleep(min(30.0, max(0.0, end - time.time())))
    return True


def loop(single: bool, dev: bool = False) -> int:
    if not DEPLOYMENT.exists() and not dev:
        print(f"This is not the learner's deployment checkout ({DEPLOYMENT} is missing). The learner runs from its own "
              f"clone so development commits cannot abort its batches: see README.md 'Where it runs'. Pass --dev to "
              f"run here anyway (smoke tests only).")
        return 2
    why = acquire_lock()
    if why:
        print(why)
        return 2
    started_sig, refused_sig = code_signature(), None
    log(f"learner started (code {started_sig})")
    try:
        if load_state().get("parser_version") != scoring.PARSER_VERSION and not single:
            # A parser upgrade arrived (e.g. through auto_update): re-read every retained batch once.
            cmd_reparse()
            st = load_state()
            st["parser_version"] = scoring.PARSER_VERSION
            save_state(st)
        adopted = adopt_unfinished(load_config())
        if adopted is False and STOP.exists():
            return 0
        while True:
            if STOP.exists():
                log("STOP file found: stopping (delete ai-agent/STOP to allow the next start)")
                return 0
            if ATTENTION.exists():
                log(f"{ATTENTION} exists: not starting a cycle until it is resolved and deleted")
                return 0
            if load_config().get("auto_update") and not single:
                msg = update_checkout()
                if msg:
                    log(msg)
            sig = code_signature()
            if not single and sig != started_sig and sig != refused_sig:
                if tests_pass():
                    log(f"code changed ({started_sig} -> {sig}) and test_agent.py passes: restarting into it")
                    return RESTART_CODE
                refused_sig = sig
                log(f"code changed ({sig}) but test_agent.py FAILS: keeping the running version {started_sig}")
            cfg, state = load_config(), load_state()
            if free_gb() < float(cfg["min_free_gb"]):
                prune({**cfg, "keep_raw_cycles": 1}, state)
                if free_gb() < float(cfg["min_free_gb"]):
                    attention(f"Only {free_gb():.0f} GB free on this disk; config min_free_gb is {cfg['min_free_gb']}.")
                    return 0
            batches, singles = other_bots_running()
            if not cfg["wait_if_other_bots_running"]:
                batches = []
            lanes, how = size_lanes(cfg, len(singles))
            if batches or lanes < 8:
                log(f"waiting {cfg['idle_wait_minutes']} min: " + (f"another batch is running: {batches[:3]}"
                                                                    if batches else
                                                                    f"only {lanes} lanes available ({how})"))
                if single or not sleep_unless_stopped(float(cfg["idle_wait_minutes"])):
                    return 0
                continue
            log(f"lanes = {lanes} ({how})" + (f"; {len(singles)} single bot(s) open, a thread reserved for each"
                                              if singles else ""))
            try:
                ok = run_cycle(cfg, state, lanes)
            except Exception:
                log(f"cycle crashed:\n{traceback.format_exc()}")
                state = load_state()
                state["current"] = None
                save_state(state)
                ok = False
            state = load_state()
            state["failures"] = 0 if ok else state.get("failures", 0) + 1
            save_state(state)
            if state["failures"] >= int(cfg["max_consecutive_failures"]):
                attention(f"{state['failures']} cycles in a row produced no scored runs. Read data/learner.log and "
                          f"the newest runs/<tag>/x4.out.txt.")
                return 0
            if single:
                return 0 if ok else 1
            if not ok and not sleep_unless_stopped(10):
                return 0
    finally:
        release_lock()


# ---------------------------------------------------------------------------------------------------------- commands
def cmd_ingest(batch_dir: str) -> int:
    path = str(Path(batch_dir).resolve())
    state = load_state()
    if path not in state.setdefault("ingested", []):
        state["ingested"].append(path)
        save_state(state)
    existing = {(r.get("batch"), r.get("lane"), r.get("log")) for r in load_jsonl(RUNS_FILE)}
    records = [r for r in scoring.parse_batch(Path(path), "ingest")
               if (r.get("batch"), r.get("lane"), r.get("log")) not in existing]
    for r in records:
        r["genome_id"] = brain.genome_id(r["genome"])
    append_jsonl(RUNS_FILE, records)
    if records:
        append_jsonl(CYCLES_FILE, [{"source": "ingest", "tag": f"ingest {records[0]['batch']}", "finished": now(),
                                    "exit": "-", "runs": len(records), "path": path,
                                    "usable": sum(1 for r in records if r["usable"]), "arms_label": "step-14 arms"}])
    log(f"ingested {len(records)} new runs from {path}")
    report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status="ingested")
    return 0


def cmd_reparse() -> int:
    """Re-read every batch whose raw logs still exist; keep the records of batches already pruned."""
    state = load_state()
    sources = {}
    for c in state["cycles"]:
        b = RUNS / c["tag"] / "batch"
        if (b / "ARMS.json").exists():
            sources[str(b)] = c["tag"]
    for p in state.get("ingested", []):
        if (Path(p) / "ARMS.json").exists():
            sources[p] = "ingest"
    fresh, covered = [], set()
    for path, label in sources.items():
        recs = scoring.parse_batch(Path(path), label)
        for r in recs:
            r["genome_id"] = brain.genome_id(r["genome"])
        fresh += recs
        covered.add(json.loads((Path(path) / "ARMS.json").read_text(encoding="utf-8")).get("stamp"))
    old = load_jsonl(RUNS_FILE)
    kept = [r for r in old if r.get("batch") not in covered]
    write_jsonl(RUNS_FILE, kept + fresh)
    log(f"reparse: {len(fresh)} records re-read from {len(sources)} batches; {len(kept)} kept from pruned batches")
    report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status="reparsed")
    return 0


def cmd_plan() -> int:
    cfg, state = load_config(), load_state()
    batches, singles = other_bots_running()
    lanes, how = size_lanes(cfg, len(singles))
    print(f"lanes = {lanes} ({how}); other batches: {batches or 'none'}; single bots: {len(singles)}")
    if lanes < 8:
        print("fewer than 8 lanes available: the learner would wait")
        return 0
    plan = plan_cycle(cfg, state, lanes)
    for a, v in plan["arms"].items():
        print(f"arm {a}: {v['genome']} {v['label']}\n    why: {v['why']}")
    print("command:", " ".join(batch_command(plan, RUNS / plan["tag"])))
    return 0


def cmd_status() -> int:
    state, cfg = load_state(), load_config()
    cur = state.get("current")
    alive = bool(cur) and batch_running(RUNS / cur["tag"])
    pid = LOCK.read_text().strip() if LOCK.exists() else None
    learner_alive = bool(pid) and pid.isdigit() and psutil.pid_exists(int(pid))
    print(f"learner process: {'RUNNING (pid ' + pid + ')' if learner_alive else 'NOT running'}")
    print(f"current cycle: {cur}; its batch is {'RUNNING' if alive else 'not running'}")
    print(f"cycles started: {state['cycle']}; failures in a row: {state.get('failures', 0)}; "
          f"design row next: {state.get('design_next', 0)}")
    print(f"runs recorded: {len(load_jsonl(RUNS_FILE))}; free disk: {free_gb():.0f} GB; "
          f"raw cycles kept: {cfg['keep_raw_cycles']}")
    print(f"STOP file: {STOP.exists()}; ATTENTION: {ATTENTION.exists()}; consult: {cfg['consult']['enabled']}")
    print(f"findings: {FINDINGS / 'LATEST.md'}")
    return 0


def cmd_publish() -> int:
    PUBLISHED.mkdir(exist_ok=True)
    for src in [FINDINGS / "LATEST.md", FINDINGS / "latest.json", FINDINGS / "DEVELOPER-NOTES.md", RUNS_FILE,
                CYCLES_FILE, LOG]:
        if src.exists():
            shutil.copy2(src, PUBLISHED / src.name)
    print(f"copied into {PUBLISHED}; commit that folder (explicit paths) for a cloud session to read it")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "once", "plan", "ingest", "reparse", "report", "status", "publish"])
    ap.add_argument("batch_dir", nargs="?")
    ap.add_argument("--lanes", default=None, help="override config.json's lanes for this process (e.g. a smoke test)")
    ap.add_argument("--minutes", type=float, default=None, help="override config.json's cycle_minutes")
    ap.add_argument("--dev", action="store_true", help="allow run/once outside the deployment clone (smoke tests)")
    a = ap.parse_args()
    if a.lanes is not None:
        DEFAULTS["_override_lanes"] = a.lanes
    if a.minutes is not None:
        DEFAULTS["_override_minutes"] = a.minutes
    if a.command in ("run", "once"):
        return loop(single=a.command == "once", dev=a.dev)
    if a.command == "ingest":
        if not a.batch_dir:
            ap.error("ingest needs a batch directory")
        return cmd_ingest(a.batch_dir)
    if a.command == "report":
        report.write(FINDINGS, load_jsonl(RUNS_FILE), load_jsonl(CYCLES_FILE), key=score_key(load_config()), status="report")
        print(FINDINGS / "LATEST.md")
        return 0
    return {"plan": cmd_plan, "status": cmd_status, "publish": cmd_publish, "reparse": cmd_reparse}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
