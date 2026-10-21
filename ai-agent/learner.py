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
6. ARCHIVES its own old raw logs (backlog O3, 2026-10-21): the newest `keep_raw_cycles` cycles stay raw; each older
   cycle's `batch/` is zipped to `runs/<tag>/raw.zip` (+ `raw.manifest.json`), the zip is VERIFIED against the
   originals, and only then are the originals deleted. Nothing is ever deleted without a verified archive.

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
  archive    archive every cycle outside keep_raw_cycles now (refuses while the 24/7 learner holds its lock)
  archive-check  re-verify every runs/<tag>/raw.zip against its manifest (read-only; exit 1 on any BAD)
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
import zipfile
import zlib
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
#: The raw-log archive of one cycle (backlog O3): `runs/<tag>/raw.zip` with its `raw.manifest.json`. A zip is written as
#: `.part`, verified, then renamed; one that fails a later re-verification is kept aside as `.bad`.
ARCHIVE, ARCHIVE_PART, ARCHIVE_BAD, MANIFEST = "raw.zip", "raw.zip.part", "raw.zip.bad", "raw.manifest.json"
#: Below this much free disk no archive can be written safely: archive nothing, delete nothing, start no batch.
ARCHIVE_FLOOR_GB = 2.0
#: The rename of a finished `.part` is retried for a transient lock (an antivirus scan holds a new file briefly).
#: Module constants, so a TEST can shorten the wait; nothing in the environment changes them.
REPLACE_TRIES, REPLACE_WAIT_S = 5, 2.0
_os_replace = os.replace

DEFAULTS = {
    "lanes": "auto", "max_lanes": 24, "reserve_threads": 4, "reserve_ram_gb": 8, "ram_per_lane_gb": 1.5,
    "cycle_minutes": 720, "keep_raw_cycles": 3, "min_free_gb": 25, "design": "screen", "auto_update": True,
    "max_archives_per_prune": 3, "keep_archive_cycles": 0,
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


def _ours(c: dict, p: Path) -> bool:
    """A path this learner created for cycle `c`, by exact name: its `runs/<tag>/batch` or a lane profile
    `endless-<tag>-*`. Nothing else is ever archived or deleted (test R2)."""
    return (p.parent == RUNS / c["tag"] and p.name == "batch") or \
           (p.parent == PROFILES and p.name.startswith(f"endless-{c['tag']}-"))


class ArchiveError(RuntimeError):
    """An archive could not be written or verified. The originals are untouched."""


def _member(name: str, size: int, crc: int) -> dict:
    return {"name": name, "size": size, "crc32": crc}


def _scan_originals(cdir: Path, files: list[Path]) -> list[dict]:
    """(name, size, CRC32) of each original file, read from disk; names relative to `runs/<tag>/`."""
    out = []
    for f in files:
        crc, size = 0, 0
        with open(f, "rb") as fh:
            while chunk := fh.read(1 << 20):
                crc, size = zlib.crc32(chunk, crc), size + len(chunk)
        out.append(_member(f.relative_to(cdir).as_posix(), size, crc))
    return out


def _copy_member(zf: zipfile.ZipFile, src: Path, name: str) -> dict:
    """Stream one file into the zip, computing its CRC32 from the bytes read (never trusting the zip's own)."""
    info = zipfile.ZipInfo.from_file(src, name, strict_timestamps=False)
    info.compress_type = zipfile.ZIP_DEFLATED
    info._compresslevel = 6  # read by zipfile's compressor for a ZipInfo opened for writing (3.12 and 3.13)
    crc, size = 0, 0
    with open(src, "rb") as fin, zf.open(info, "w", force_zip64=True) as fout:
        while chunk := fin.read(1 << 20):
            crc, size = zlib.crc32(chunk, crc), size + len(chunk)
            fout.write(chunk)
    return _member(name, size, crc)


def verify_archive(zpath: Path, members: list[dict]) -> str | None:
    """None if `zpath` holds EXACTLY `members` (same names, sizes and CRC32s) and every member decompresses to its
    stored CRC (`testzip`); otherwise the reason. Never raises."""
    try:
        with zipfile.ZipFile(zpath) as zf:
            bad = zf.testzip()
            if bad is not None:
                return f"member {bad} fails its CRC"
            infos = zf.infolist()
            got = {i.filename: i for i in infos}
            want = {m["name"]: m for m in members}
            if len(infos) != len(got) or len(got) != len(want) or set(got) != set(want):
                return f"members differ: {len(infos)} in the zip, {len(want)} expected"
            for name, m in want.items():
                if got[name].file_size != m["size"]:
                    return f"{name}: size {got[name].file_size} != {m['size']}"
                if got[name].CRC != m["crc32"]:
                    return f"{name}: CRC {got[name].CRC:08x} != the source's {m['crc32']:08x}"
    except Exception as exc:  # noqa: BLE001 - an unreadable zip is a failed verification, never a crash
        return f"unreadable: {exc!r}"[:200]
    return None


def _replace_with_retry(src: Path, dst: Path) -> None:
    """os.replace, retried REPLACE_TRIES times REPLACE_WAIT_S apart on PermissionError (a transient antivirus lock)."""
    for attempt in range(1, REPLACE_TRIES + 1):
        try:
            _os_replace(src, dst)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES:
                raise
            log(f"rename {src.name} -> {dst.name} is locked (attempt {attempt}/{REPLACE_TRIES}); retrying")
            time.sleep(REPLACE_WAIT_S)


def _remove_part(part: Path) -> None:
    try:
        part.unlink(missing_ok=True)
    except OSError as exc:
        log(f"could not remove {part} ({exc!r}); the next prune removes it")


def _read_manifest(path: Path) -> dict | None:
    try:
        man = json.loads(path.read_text(encoding="utf-8"))
        return man if isinstance(man.get("members"), list) else None
    except (OSError, ValueError, AttributeError):
        return None


def _write_manifest(cdir: Path, tag: str, members: list[dict]) -> None:
    man = {"tag": tag, "written": now(), "n_files": len(members), "bytes_raw": sum(m["size"] for m in members),
           "bytes_zip": (cdir / ARCHIVE).stat().st_size, "members": members}
    tmp = cdir / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(man, indent=1), encoding="utf-8")
    tmp.replace(cdir / MANIFEST)


def _delete_ours(c: dict) -> None:
    for p in map(Path, c.get("created", [])):
        if _ours(c, p) and p.exists():
            shutil.rmtree(p, ignore_errors=True)


def archive_cycle(c: dict) -> str:
    """Archive one cycle's raw logs, then delete its originals (`batch/` and its lane profiles, by `_ours`).

    Order, so a crash or kill at ANY point loses nothing: write `raw.zip.part` -> verify it against the CRC32s read
    while streaming -> rename to `raw.zip` -> write `raw.manifest.json` -> delete the originals -> set the flags.
    Recovery: a `raw.zip` beside its originals is re-verified against them (the manifest's member list when there is
    one: deletion may have stopped part-way) and the originals deleted only if it passes; a failing one is renamed
    `raw.zip.bad`, the originals are KEPT and the next prune archives them again. Returns what happened; raises
    (with the originals untouched and no `.part` left) when the archive cannot be written or verified."""
    tag = c["tag"]
    cdir = RUNS / tag
    batch, zpath, part = cdir / "batch", cdir / ARCHIVE, cdir / ARCHIVE_PART
    ours_batch = any(_ours(c, p) and p.name == "batch" for p in map(Path, c.get("created", [])))
    files = sorted(f for f in batch.rglob("*") if f.is_file()) if ours_batch and batch.is_dir() else []
    if not files:  # nothing to archive (an empty or missing batch/): today's delete, as before O3 (tests R1/R2)
        _delete_ours(c)
        if zpath.exists():
            c["archived"] = True
        c["pruned"] = True
        return "no raw logs to archive; deleted its empty leftovers"
    if zpath.exists():
        sources = _scan_originals(cdir, files)
        man = _read_manifest(cdir / MANIFEST)
        if man:
            reason = verify_archive(zpath, man["members"])
            listed = {m["name"]: m for m in man["members"]}
            if not reason and any(listed.get(s["name"]) != s for s in sources):
                reason = "an original differs from (or is missing in) the manifest"
        else:
            reason = verify_archive(zpath, sources)
        if reason:
            _replace_with_retry(zpath, cdir / ARCHIVE_BAD)
            log(f"{tag}: raw.zip FAILED re-verification ({reason}); quarantined as {ARCHIVE_BAD}, the raw logs are "
                f"KEPT and archived again at the next prune")
            return "quarantined"
        if not man:
            _write_manifest(cdir, tag, sources)
        how = "re-verified an existing raw.zip against the originals"
    else:
        try:
            with zipfile.ZipFile(part, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6,
                                 strict_timestamps=False) as zf:
                members = [_copy_member(zf, f, f.relative_to(cdir).as_posix()) for f in files]
            reason = verify_archive(part, members)
            if reason:
                raise ArchiveError(f"{tag}: the new archive failed verification: {reason}")
            _replace_with_retry(part, zpath)
        except BaseException:
            _remove_part(part)
            raise
        _write_manifest(cdir, tag, members)
        how = "archived"
    _delete_ours(c)
    if batch.exists():
        raise ArchiveError(f"{tag}: raw.zip is verified but batch/ could not be fully deleted; retried next prune")
    c["archived"] = c["pruned"] = True
    man = _read_manifest(cdir / MANIFEST) or {}
    raw, packed = man.get("bytes_raw", 0), man.get("bytes_zip", 0)
    return f"{how}: {man.get('n_files')} files, {raw / 2**20:.0f} MB -> {packed / 2**20:.1f} MB; raw logs deleted"


def prune(cfg: dict, state: dict) -> None:
    """Archive, then delete, the raw logs and lane profiles of all but the newest `keep_raw_cycles` cycles (at most
    `max_archives_per_prune` archives a call, which bounds the cycle-boundary delay). Only paths this learner created
    and recorded, and only names it would have created. NEVER raises into the loop: a failure is logged and retried at
    the next boundary, and its originals stay. Under ARCHIVE_FLOOR_GB free it does nothing at all."""
    for c in state["cycles"]:  # a `.part` is never live outside archive_cycle: one left over is from a killed run
        part = RUNS / c["tag"] / ARCHIVE_PART
        if part.exists():
            _remove_part(part)
            log(f"{c['tag']}: removed a leftover {ARCHIVE_PART} (an archive interrupted earlier; its raw logs are "
                f"intact)")
    free = free_gb()
    if free < ARCHIVE_FLOOR_GB:
        log(f"prune: only {free:.1f} GB free, below the {ARCHIVE_FLOOR_GB} GB an archive needs: archiving and "
            f"deleting NOTHING")
        return
    keep, cap = int(cfg["keep_raw_cycles"]), int(cfg.get("max_archives_per_prune", 3))
    attempts = 0
    for c in state["cycles"][:-keep] if keep > 0 else state["cycles"]:
        if c.get("pruned"):
            continue
        if attempts >= cap:
            log(f"prune: {cap} archive(s) this boundary (max_archives_per_prune); the rest wait for the next one")
            break
        try:
            outcome = archive_cycle(c)
            if not outcome.startswith("no raw logs"):
                attempts += 1
            log(f"{c['tag']}: {outcome} (its run records are kept)")
        except Exception:  # noqa: BLE001 - never into the loop; the raw logs stay and the next boundary retries
            attempts += 1
            log(f"{c['tag']}: archiving FAILED, its raw logs are KEPT and it is retried at the next boundary:\n"
                f"{traceback.format_exc()}")
        save_state(state)
    save_state(state)


def disk_guard(cfg: dict, state: dict) -> bool:
    """Before a batch: True = enough free disk to start it. Under `min_free_gb` it ARCHIVES every cycle but the
    newest (never a delete without a verified archive); if still short it writes ATTENTION.md and the learner stops.
    Under ARCHIVE_FLOOR_GB prune archives and deletes nothing, so the learner stops with the raw logs intact."""
    if free_gb() >= float(cfg["min_free_gb"]):
        return True
    prune({**cfg, "keep_raw_cycles": 1, "max_archives_per_prune": 10 ** 6}, state)
    free = free_gb()
    if free >= float(cfg["min_free_gb"]):
        return True
    if free < ARCHIVE_FLOOR_GB:
        attention(f"Only {free:.1f} GB free on this disk: below the {ARCHIVE_FLOOR_GB} GB an archive needs, so the "
                  f"learner archived and deleted NOTHING and did not start the next batch. Free some space.")
    else:
        attention(f"Only {free:.0f} GB free on this disk after archiving old raw logs; config min_free_gb is "
                  f"{cfg['min_free_gb']}.")
    return False


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
            if not disk_guard(cfg, state):
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
        if recs:  # a batch whose logs are gone yields nothing: its OLD records must then be kept, not dropped (R9)
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
          f"raw cycles kept: {cfg['keep_raw_cycles']}; archived cycles: {len(list(RUNS.glob('*/' + ARCHIVE)))}")
    print(f"STOP file: {STOP.exists()}; ATTENTION: {ATTENTION.exists()}; consult: {cfg['consult']['enabled']}")
    print(f"findings: {FINDINGS / 'LATEST.md'}")
    return 0


def cmd_archive() -> int:
    """Archive every cycle outside keep_raw_cycles now. It takes the learner's lock, so it REFUSES while the 24/7
    learner runs (its own prune would race this one); `acquire_lock` replaces only a STALE lock."""
    why = acquire_lock()
    if why:
        print(f"archive refused: {why}. The running learner archives at each cycle boundary by itself.")
        return 2
    try:
        cfg, state = load_config(), load_state()
        prune({**cfg, "max_archives_per_prune": 10 ** 6}, state)
        print(f"archived; see {LOG}")
        return 0
    finally:
        release_lock()


def cmd_archive_check() -> int:
    """READ-ONLY re-verification of every `runs/<tag>/raw.zip` against its manifest. One line per zip, exit 1 on any
    BAD. Its result (with a timestamp) also goes to `data/archive_check.json`, which `tools/status.py` shows."""
    lines, bad = [], 0
    for zpath in sorted(RUNS.glob(f"*/{ARCHIVE}")):
        tag = zpath.parent.name
        man = _read_manifest(zpath.parent / MANIFEST)
        reason = verify_archive(zpath, man["members"]) if man else f"no readable {MANIFEST}"
        if reason:
            bad += 1
            lines.append(f"BAD {tag} {reason}")
        else:
            lines.append(f"OK {tag} {len(man['members'])} {zpath.stat().st_size}")
    print("\n".join(lines) if lines else "no archives yet")
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "archive_check.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps({"checked": now(), "archives": len(lines), "bad": bad, "lines": lines}, indent=1),
                   encoding="utf-8")
    tmp.replace(out)
    return 1 if bad else 0


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
    ap.add_argument("command", choices=["run", "once", "plan", "ingest", "reparse", "report", "status", "publish",
                                        "archive", "archive-check"])
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
    return {"plan": cmd_plan, "status": cmd_status, "publish": cmd_publish, "reparse": cmd_reparse,
            "archive": cmd_archive, "archive-check": cmd_archive_check}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
