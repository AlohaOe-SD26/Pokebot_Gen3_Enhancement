"""GATE — prove tools/ops/backup_learner.py (backlog O4, build spec S1-2) backs up the learner's data SAFELY.

WHY THIS EXISTS. The nightly backup runs with no human watching, against a learner that is appending to its files at
that moment, onto a disk the user has to remember to keep plugged in. Its failure modes are all SILENT: a backup on
the same disk it protects, a half line that makes the restored runs.jsonl unloadable (the learner's own load_jsonl
raises on it), a failed backup that still prunes the last good copies, a restore drill that writes into the clone.
Every test below pairs a FAULT arm (the bad condition, which must be caught) with a CONTROL arm (the good condition,
which must pass), so a test that cannot fail does not count. Everything runs on a FAKE clone tree in a temp folder;
the real clone, E:, Z: and %LOCALAPPDATA% are never touched.

  B1 round trip: every member's sha256 equals its source, member count == manifest == source list, the lock and *.tmp
     are excluded. FAULT: a source byte changed afterwards IS seen as a difference (the comparison is not vacuous).
  B2 FAULT torn append: a writer appends a whole line plus HALF a line while the copy reads, and another file already
     ends in a half line -> the backup holds only whole, parsing lines, a prefix of the file. CONTROL: an untouched
     .jsonl is byte-identical.
  B3 FAULT same volume (the injected st_dev probe AND the real temp folders, both on one disk) -> refused, nothing in
     the destination. CONTROL different volume -> ok. The test-only --test-allow-same-volume flag proceeds with a loud
     WARN in the status file (CLI, subprocess).
  B4 FAULT 5 GB free -> refused, no partial file. CONTROL 50 GB -> ok.
  B5 retention: 20 old backups -> exactly the 14 newest remain; notes.txt and learner-data-notadate.zip untouched.
     FAULT: the new backup fails verification -> NO old backup deleted.
  B6 FAULT a corrupt new zip (one byte flipped after writing) -> deleted, reported, old ones kept. CONTROL: not
     corrupted -> kept.
  B7 restore-check: a good zip restores and parses (CONTROL, empty target); FAULT a non-empty target is refused and
     left untouched; a target inside the clone is refused; a tampered zip fails.
  B8 (Windows) no handle outlives the copy: after a backup the learner's tmp.replace onto every data file succeeds.
     FAULT arm: a handle held on state.json makes that replace raise PermissionError (the probe can see a leak, and
     the hazard is real: opening with FILE_SHARE_DELETE was tried and does NOT avoid it, measured 2026-10-21).
  B9 the installer: the default run is a dry run (exit 0, names the task, 1:00 AM, -3.12 -B, StartWhenAvailable,
     "no scheduled task was created") and the task's registration state is unchanged; the installed command never
     carries the test flag (FAULT: a mutant text carrying it is caught). The task launches pyw.exe (no window at 1 AM),
     and the tool run HEADLESS through that launcher (stdout and stderr None, as under Task Scheduler) still returns
     its exit code and writes its status: FAULT same volume -> 2 REFUSED; CONTROL the test flag -> 0 ok.
  B10 the weekly snapshot (--publish-to): FAULT a target inside the clone is refused and not created; CONTROL the six
     files land in a main-checkout target, a learner.log over 5 MB is cut to its last 5,000 lines, and runs.jsonl
     over 5 MB is published WHOLE (measured 2026-10-21: the real one is 10.2 MB in 2,586 lines).
  B11 FAULT runs.jsonl shrank -> NEEDS-YOU: exit 1, ok false, the new zip KEPT, nothing pruned; 15 more shrunken
     nights still prune nothing (the baseline is the LARGEST earlier copy, not the newest). CONTROL it grew -> ok. The
     documented release (move the larger zips into a sub-folder) resumes pruning and leaves the sub-folder untouched.
  B12 (review finding 0, its absent.py shape) FAULT 14 good nights, then 15 nights with NO runs.jsonl -> every night
     NEEDS-YOU, exit 1, and all 14 good backups still exist and hold runs.jsonl; a clone that never had one is held
     too. CONTROL runs.jsonl back whole -> ok and pruning resumes.
  B13 (finding 1) FAULT backups named in the future (clock went backwards) -> NEEDS-YOU, the new zip KEPT, nothing
     deleted; with that hold disabled the new zip is still never pruned (`protect`). CONTROL past names -> the
     oldest is pruned. Unit: apply_retention never deletes the protected name.
  B14 (finding 3) FAULT a destination under the ops folder / a clone under it / an ops tree over the cap -> exit 2,
     nothing in the destination. CONTROL a normal layout captures the ops folder.
  B15 (finding 6) FAULT a fresh lock -> exit 2, the lock untouched; two CONCURRENT runs -> the second is REFUSED and
     the first completes. CONTROL a stale lock is replaced (WARN), no lock is left behind; the sweep removes only a
     .part over an hour old.
  B16 (finding 7) FAULT a backup name in non-ASCII digits is not ours: it takes no keep slot. CONTROL ASCII names are.
  B17 (finding 5) FAULT \\\\?\\ and UNC targets are refused outright by --restore-check and --publish-to, and with the
     name check blinded the IDENTITY check still refuses a target inside the clone. CONTROL a plain outside target
     restores.
  B18 (final re-verify 2026-10-21, blocker B3: hold on IDENTITY, not count) FAULT the reviewer's o4_regrow.py shape:
     3 nights of 100 records with keep 3, then 4 nights that each drop the same 10 records while 50 more are added
     (the count GROWS) -> every night NEEDS-YOU, nothing pruned, the pre-drop zips still hold the dropped record; the
     same with the reviewer's own key-less rows, and with earlier zips that carry no identity cache (the slow path).
     A manifest whose cached run_ids drop one record fails verification. CONTROL pure growth -> exit 0 and one prune
     a night; a reparse that rewrites every row's CONTENT under the same (batch, lane, log) -> no hold; the documented
     release (the pre-drop zips moved into a sub-folder) -> pruning resumes.
  B19 (B4) FAULT a leftover lock dated 30 days in the FUTURE (the reviewer's o4_lock.py arm) -> replaced, exit 0 three
     nights running; a FRESH lock naming an exited pid -> replaced. CONTROL a lock 30 s ahead with no readable pid
     (inside the 2-minute grace) and a fresh lock naming a LIVE process -> REFUSED, untouched.
  B20 (B5) FAULT a destination on a drive letter that is not present, with the REAL probes -> exit 2 'REFUSED:
     destination drive not present', in the status file too. CONTROL the same run to a present drive -> exit 0.

Run: cd tools/story-dev && py -3.12 selftest_ops.py      (about 10 s)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TOOL = ROOT / "tools" / "ops" / "backup_learner.py"
INSTALLER = ROOT / "tools" / "ops" / "install_ops_tasks.ps1"
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def load_tool():
    spec = importlib.util.spec_from_file_location("backup_learner_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.STATE_RETRY_SLEEP = 0.0
    mod.REPLACE_RETRY_SLEEP = 0.0
    return mod


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def jl(rows) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


def fake_clone(root: Path) -> Path:
    """A small learner tree with every kind of file the backup handles (and the two it must skip)."""
    clone = root / "clone" / "ai-agent"
    for d in ("data", "findings", "inbox/done", "inbox/rejected", "runs/ai0001/batch"):
        (clone / d).mkdir(parents=True, exist_ok=True)
    (clone / "data" / "runs.jsonl").write_text(jl({"run": i, "score": i * 1.5} for i in range(200)), encoding="utf-8")
    (clone / "data" / "cycles.jsonl").write_text(jl({"tag": f"ai{i:04d}"} for i in range(5)), encoding="utf-8")
    (clone / "data" / "consult_log.jsonl").write_text(jl({"day": "2026-10-21", "n": i} for i in range(3)),
                                                      encoding="utf-8")
    (clone / "data" / "learner.log").write_text("[x] line one\n[x] line two\n", encoding="utf-8")
    (clone / "data" / "state.json").write_text(json.dumps({"cycle": 5, "cycles": [{"tag": "ai0001"}]}),
                                               encoding="utf-8")
    (clone / "data" / "agent.lock").write_text("12345", encoding="utf-8")
    (clone / "data" / "state.tmp").write_text("{half", encoding="utf-8")
    (clone / "findings" / "LATEST.md").write_text("# latest\n", encoding="utf-8")
    (clone / "findings" / "latest.json").write_text("{}", encoding="utf-8")
    (clone / "findings" / "DEVELOPER-NOTES.md").write_text("notes\n", encoding="utf-8")
    (clone / "inbox" / "README.md").write_text("inbox\n", encoding="utf-8")
    (clone / "inbox" / "p1.json").write_text("{}", encoding="utf-8")
    (clone / "inbox" / "done" / "p0.json").write_text("{}", encoding="utf-8")
    (clone / "inbox" / "rejected" / "bad.json").write_text("{", encoding="utf-8")
    (clone / "config.json").write_text('{"keep_raw_cycles": 20}', encoding="utf-8")
    (clone / "runs" / "ai0001" / "batch" / "big.log").write_text("raw\n", encoding="utf-8")  # NOT backed up
    return clone


def expected_members(clone: Path, ops: Path) -> set[str]:
    out = set()
    for sub in ("data", "findings", "inbox"):
        for p in (clone / sub).rglob("*"):
            if p.is_file() and p.name != "agent.lock" and not p.name.endswith(".tmp"):
                out.add("ai-agent/" + p.relative_to(clone).as_posix())
    out.add("ai-agent/config.json")
    for p in ops.rglob("*"):
        if p.is_file() and not p.name.endswith(".tmp"):
            out.add("pokebot-ops/" + p.relative_to(ops).as_posix())
    return out


class Env:
    """One fresh fake world: a clone, an ops folder (holding the status file), a destination, and the tool with its
    disk probes injected (a DIFFERENT volume with 50 GB free unless a test says otherwise)."""

    def __init__(self, tmp: Path, name: str):
        self.root = tmp / name
        self.clone = fake_clone(self.root)
        self.ops = self.root / "localappdata" / "pokebot-ops"
        self.ops.mkdir(parents=True)
        (self.ops / "samples.jsonl").write_text(jl([{"t": 1, "free_gb_c": 70.0}]), encoding="utf-8")
        self.status = self.ops / "backup_status.json"
        self.dest = self.root / "E" / "pokebot-backups" / "learner"
        self.tool = load_tool()
        self.same_volume = False
        self.free = 50.0
        real_volume = self.tool.volume_id
        self.tool.volume_id = lambda p: (real_volume(p) if self.same_volume
                                         else 2 if self.tool.is_under(p, self.clone.parent) else 1)
        self.tool.free_gb = lambda p: self.free

    def backup(self, minute: int = 0, keep: int = 14, when=None, **kw):
        when = when or dt.datetime(2026, 10, 21, 1, minute)
        kw.setdefault("ops_dir", self.ops)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code, status = self.tool.run_backup(self.clone, self.dest, keep, 10.0, self.status, when=when, **kw)
        return code, status, buf.getvalue()

    def dest_files(self) -> list[str]:
        return sorted(p.name for p in self.dest.iterdir()) if self.dest.exists() else []


def zip_members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def flip_byte_in_member(zip_path: Path, member: str) -> None:
    with zipfile.ZipFile(zip_path) as z:
        info = z.getinfo(member)
    raw = bytearray(zip_path.read_bytes())
    name_len = int.from_bytes(raw[info.header_offset + 26:info.header_offset + 28], "little")
    extra_len = int.from_bytes(raw[info.header_offset + 28:info.header_offset + 30], "little")
    pos = info.header_offset + 30 + name_len + extra_len + info.compress_size // 2
    raw[pos] ^= 0xFF
    zip_path.write_bytes(bytes(raw))


def b1(tmp: Path) -> None:
    e = Env(tmp, "b1")
    want = expected_members(e.clone, e.ops)  # BEFORE the run: the status file it writes did not exist yet
    code, status, out = e.backup()
    check("B1 CONTROL: a backup on a different volume succeeds", code == 0 and status["ok"], out)
    zips = [n for n in e.dest_files() if n.endswith(".zip")]
    check("B1 exactly one zip, no .part left", zips == ["learner-data-20261021-0100.zip"], str(e.dest_files()))
    if not zips:
        return
    mem = zip_members(e.dest / zips[0])
    man = json.loads(mem.pop("MANIFEST.json"))
    check("B1 the member set is exactly the source list (lock and *.tmp excluded, runs/ never included)",
          set(mem) == want, f"extra {sorted(set(mem) - want)} missing {sorted(want - set(mem))}")
    check("B1 member count == manifest n_files == len(manifest members)",
          len(mem) == man["n_files"] == len(man["members"]), f"{len(mem)} {man['n_files']}")

    def src(name: str) -> Path:
        return (e.clone / name[len("ai-agent/"):]) if name.startswith("ai-agent/") else e.ops / name[len("pokebot-ops/"):]

    # The status file is rewritten after the zip, so its CURRENT bytes legitimately differ: compare it to the manifest.
    diffs = [n for n in mem if not n.endswith("backup_status.json") and sha(src(n).read_bytes()) != sha(mem[n])]
    check("B1 CONTROL: every member's sha256 equals its source file", not diffs, str(diffs))
    by_name = {m["name"]: m for m in man["members"]}
    check("B1 every manifest sha256 equals the member bytes",
          all(sha(mem[n]) == by_name[n]["sha256"] for n in mem), "")
    p = e.clone / "data" / "runs.jsonl"
    p.write_bytes(p.read_bytes().replace(b'"run": 7,', b'"run": 8,', 1))
    check("B1 FAULT: a source byte changed afterwards IS detected by the same comparison",
          sha(p.read_bytes()) != sha(mem["ai-agent/data/runs.jsonl"]), "")
    st = json.loads(e.status.read_text(encoding="utf-8"))
    check("B1 the status file says ok with bytes and the zip path", st["ok"] and st["bytes"] > 0 and st["zip"], str(st))


def b2(tmp: Path) -> None:
    e = Env(tmp, "b2")
    runs = e.clone / "data" / "runs.jsonl"
    cycles = e.clone / "data" / "cycles.jsonl"
    with open(cycles, "ab") as fh:  # the learner wrote half a line and has not finished it (no fsync)
        fh.write(b'{"tag": "ai00')
    before = {"ai-agent/data/runs.jsonl": runs.read_bytes(),  # the appended line comes AFTER the size is taken
              "ai-agent/data/cycles.jsonl": cycles.read_bytes().rsplit(b"\n", 1)[0] + b"\n"}
    untouched = e.clone / "data" / "consult_log.jsonl"
    before_untouched = untouched.read_bytes()
    real_open = e.tool._open_read
    fired = []

    class AppendingReader:
        """A file handle on runs.jsonl that, at the moment of the read, lets 'the learner' append one whole line and
        HALF of the next one: exactly the torn-append condition the trim must survive."""

        def __init__(self, path):
            self.fh = real_open(path)

        def fileno(self):
            return self.fh.fileno()

        def read(self, *a):
            with open(runs, "ab") as w:
                w.write(b'{"run": 900, "score": 1}\n{"run": 901, "sco')
            fired.append(1)
            return self.fh.read(*a)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.fh.close()

    e.tool._open_read = lambda p: AppendingReader(p) if Path(p).name == "runs.jsonl" else real_open(p)
    code, status, out = e.backup()
    check("B2 the concurrent writer really fired during the copy", fired == [1], str(fired))
    check("B2 FAULT torn append: the backup still succeeds", code == 0, out)
    zips = [n for n in e.dest_files() if n.endswith(".zip")]
    if not zips:
        return
    mem = zip_members(e.dest / zips[0])
    for name, path in (("ai-agent/data/runs.jsonl", runs), ("ai-agent/data/cycles.jsonl", cycles)):
        data = mem[name]
        lines = data.decode("utf-8").splitlines()
        parses = all(json.loads(x) is not None for x in lines if x.strip())
        check(f"B2 FAULT: {name} holds only whole lines that parse", parses and data.endswith(b"\n"), data[-60:].decode())
        check(f"B2 FAULT: {name} is a prefix of the file on disk (nothing invented)",
              path.read_bytes().startswith(data), "")
        check(f"B2 FAULT: {name} is EXACTLY the whole lines present when the copy opened it",
              data == before[name], f"{len(data)} vs {len(before[name])}")
    check("B2 CONTROL: an untouched .jsonl is byte-identical", mem["ai-agent/data/consult_log.jsonl"] == before_untouched,
          "")


def b3(tmp: Path) -> None:
    e = Env(tmp, "b3")
    e.same_volume = True  # the REAL st_dev: the temp clone and the temp destination are on one disk
    code, status, out = e.backup()
    check("B3 FAULT same volume (real st_dev of two temp folders) -> refused, exit 2",
          code == 2 and "SAME volume" in (status["error"] or ""), out)
    check("B3 FAULT: nothing written in the destination", e.dest_files() == [], str(e.dest_files()))
    st = json.loads(e.status.read_text(encoding="utf-8"))
    check("B3 FAULT: the status file says ok false, REFUSED", not st["ok"] and "REFUSED" in st["error"], str(st))
    e.same_volume = False
    e.tool.volume_id = lambda p: 7  # injected probe: every path reports the same volume
    code, status, out = e.backup(minute=1)
    check("B3 FAULT same volume (injected st_dev probe) -> refused, nothing written",
          code == 2 and e.dest_files() == [], out)
    e.tool.volume_id = lambda p: 2 if e.tool.is_under(p, e.clone.parent) else 1  # injected: a different disk
    code, status, out = e.backup(minute=2)
    check("B3 CONTROL different volume (injected) -> ok", code == 0 and status["ok"], out)
    st = json.loads(e.status.read_text(encoding="utf-8"))
    check("B3 CONTROL: the status file now says ok", st["ok"], str(st))

    # The CLI, as a real process with the REAL probe (temp is one disk): refused without the test flag, then the
    # test flag lets it through with a loud warning recorded in the status file.
    e2 = Env(tmp, "b3cli")
    base = [sys.executable, "-B", str(TOOL), "--clone", str(e2.clone), "--dest", str(e2.dest), "--status-file",
            str(e2.status), "--ops-dir", str(e2.ops), "--min-free-gb", "0"]
    r = subprocess.run(base, capture_output=True, text=True, timeout=120)
    check("B3 FAULT CLI without the test flag on one disk -> exit 2 REFUSED", r.returncode == 2 and "REFUSED" in r.stdout,
          r.stdout + r.stderr)
    r = subprocess.run(base + ["--test-allow-same-volume"], capture_output=True, text=True, timeout=120)
    st = json.loads(e2.status.read_text(encoding="utf-8"))
    check("B3 CONTROL CLI with --test-allow-same-volume -> exit 0 and the bypass is a WARN in output and status",
          r.returncode == 0 and "TEST FLAG" in r.stdout and any("TEST FLAG" in w for w in st["warnings"]),
          r.stdout + r.stderr)


def b4(tmp: Path) -> None:
    e = Env(tmp, "b4")
    e.free = 5.0
    code, status, out = e.backup()
    check("B4 FAULT 5 GB free -> refused, exit 2", code == 2 and "GB free" in (status["error"] or ""), out)
    check("B4 FAULT: no partial file (not even the folder's contents)", e.dest_files() == [], str(e.dest_files()))
    e.free = 50.0
    code, status, out = e.backup(minute=1)
    check("B4 CONTROL 50 GB free -> ok", code == 0 and e.dest_files() == ["learner-data-20261021-0101.zip"], out)


def seed_old(dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    names = [f"learner-data-202609{d:02d}-0100.zip" for d in range(1, 21)]
    for n in names:
        (dest / n).write_bytes(b"old backup " + n.encode())
    (dest / "notes.txt").write_text("the user's own file", encoding="utf-8")
    (dest / "learner-data-notadate.zip").write_bytes(b"not ours by name")
    return names


def b5(tmp: Path) -> None:
    e = Env(tmp, "b5")
    olds = seed_old(e.dest)
    code, status, out = e.backup()
    ours = [n for n in e.dest_files() if e.tool.ZIP_RE.match(n)]
    check("B5 CONTROL: exactly 14 backups remain", code == 0 and len(ours) == 14, f"{code} {len(ours)} {out}")
    check("B5 they are the 14 NEWEST (13 newest old + the new one)",
          ours == sorted(olds[-13:] + ["learner-data-20261021-0100.zip"]), str(ours))
    check("B5 notes.txt and learner-data-notadate.zip untouched",
          (e.dest / "notes.txt").read_text(encoding="utf-8") == "the user's own file"
          and (e.dest / "learner-data-notadate.zip").read_bytes() == b"not ours by name", str(e.dest_files()))

    f = Env(tmp, "b5fault")
    olds = seed_old(f.dest)
    f.tool.verify_zip = lambda path, expect=None: (["injected verification failure"], {})
    code, status, out = f.backup()
    check("B5 FAULT: a backup failing verification -> exit 1, ok false", code == 1 and not status["ok"], out)
    check("B5 FAULT: NO old backup deleted (all 20 + the two others remain)",
          f.dest_files() == sorted(olds + ["learner-data-notadate.zip", "notes.txt"]), str(f.dest_files()))


def b6(tmp: Path) -> None:
    e = Env(tmp, "b6")
    olds = seed_old(e.dest)
    real_write = e.tool.write_zip

    def corrupting_write(part, got, manifest):
        real_write(part, got, manifest)
        flip_byte_in_member(part, "ai-agent/data/runs.jsonl")

    e.tool.write_zip = corrupting_write
    code, status, out = e.backup()
    check("B6 FAULT a corrupt new zip -> exit 1, reported as VERIFY FAILED",
          code == 1 and "VERIFY FAILED" in (status["error"] or ""), out)
    check("B6 FAULT: the corrupt zip is deleted (no .zip, no .part of tonight)",
          not any("20261021" in n for n in e.dest_files()), str(e.dest_files()))
    check("B6 FAULT: every old backup kept", all((e.dest / n).exists() for n in olds), "")
    st = json.loads(e.status.read_text(encoding="utf-8"))
    check("B6 FAULT: the status file says ok false with the reason", not st["ok"] and "VERIFY" in st["error"], str(st))
    e.tool.write_zip = real_write
    code, status, out = e.backup(minute=5)
    check("B6 CONTROL: not corrupted -> kept", code == 0 and "learner-data-20261021-0105.zip" in e.dest_files(), out)


def b7(tmp: Path) -> None:
    e = Env(tmp, "b7")
    code, status, out = e.backup()
    z = Path(status["zip"]) if status.get("zip") else None
    if not z:
        check("B7 setup backup", False, out)
        return
    target = tmp / "b7restore"
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = e.tool.restore_check(z, target, e.clone)
    check("B7 CONTROL: empty target -> restore-check ok", rc == 0 and "OK restore-check" in buf.getvalue(), buf.getvalue())
    check("B7 CONTROL: the restored runs.jsonl equals the source",
          (target / "ai-agent" / "data" / "runs.jsonl").read_bytes() == (e.clone / "data" / "runs.jsonl").read_bytes(), "")
    busy = tmp / "b7busy"
    busy.mkdir()
    (busy / "keep.txt").write_text("mine", encoding="utf-8")
    with redirect_stdout(io.StringIO()):
        rc = e.tool.restore_check(z, busy, e.clone)
    check("B7 FAULT: a non-empty target is refused (exit 2) and left untouched",
          rc == 2 and sorted(p.name for p in busy.iterdir()) == ["keep.txt"], str(rc))
    inside = e.clone / "data" / "restore-here"
    with redirect_stdout(io.StringIO()):
        rc = e.tool.restore_check(z, inside, e.clone)
    check("B7 FAULT: a target inside the clone is refused and not created", rc == 2 and not inside.exists(), str(rc))
    bad = tmp / "b7bad.zip"
    bad.write_bytes(z.read_bytes())
    flip_byte_in_member(bad, "ai-agent/data/runs.jsonl")
    with redirect_stdout(io.StringIO()):
        rc = e.tool.restore_check(bad, tmp / "b7restore2", e.clone)
    check("B7 FAULT: a tampered zip fails the restore-check (exit 1)", rc == 1, str(rc))


def b8(tmp: Path) -> None:
    """No handle outlives the copy: on Windows a held handle makes the learner's tmp.replace(state.json) fail."""
    if os.name != "nt":
        check("B8 (not Windows: an open handle does not block a replace here)", True)
        return
    e = Env(tmp, "b8")
    code, _status, out = e.backup()

    def learner_replace(target: Path) -> str:
        tmpf = target.with_name(target.name + ".tmp")
        tmpf.write_bytes(target.read_bytes())
        try:
            os.replace(tmpf, target)
            return "replaced"
        except PermissionError as ex:
            tmpf.unlink(missing_ok=True)
            return f"PermissionError {ex.winerror}"

    blocked = [f"{p.name}: {r}" for p in (e.clone / "data").glob("*.json*") if (r := learner_replace(p)) != "replaced"]
    check("B8 CONTROL: after a backup, the learner can tmp.replace every data file (no handle leaked)",
          code == 0 and not blocked, f"{out} {blocked}")
    state = e.clone / "data" / "state.json"
    with open(state, "rb") as fh:
        fh.read()
        got = learner_replace(state)
    check("B8 FAULT arm: a handle HELD on state.json makes that replace FAIL (the probe can see a leak; the hazard is "
          "real on this OS)", got.startswith("PermissionError"), got)


def b10(tmp: Path) -> None:
    """The weekly snapshot (--publish-to): six files into the MAIN checkout, never into the clone; only the log is cut."""
    e = Env(tmp, "b10")
    big_log = "".join(f"[t] log line {i}\n" for i in range(400_000)).encode()  # about 7.5 MB
    (e.clone / "data" / "learner.log").write_bytes(big_log)
    # over 5 MB AND over 5,000 lines, so a tail cut would CHANGE it (with fewer lines the cut is a no-op: the first
    # version of this test used 1,500 lines and a mutant that cut data files survived it)
    big_runs = "".join(json.dumps({"run": i, "pad": "x" * 1000}) + "\n" for i in range(6000)).encode()  # about 6.1 MB
    (e.clone / "data" / "runs.jsonl").write_bytes(big_runs)
    inside = e.clone.parent / "ai-agent" / "published"
    with redirect_stdout(io.StringIO()):
        rc = e.tool.publish(e.clone, inside)
    check("B10 FAULT: a snapshot target inside the clone is refused and not created", rc == 2 and not inside.exists(),
          str(rc))
    out_dir = tmp / "b10main" / "ai-agent" / "published"
    with redirect_stdout(io.StringIO()):
        rc = e.tool.publish(e.clone, out_dir)
    names = sorted(p.name for p in out_dir.iterdir()) if out_dir.exists() else []
    check("B10 CONTROL: the six snapshot files land in the main-checkout target", rc == 0 and names == sorted(
        ["LATEST.md", "latest.json", "DEVELOPER-NOTES.md", "runs.jsonl", "cycles.jsonl", "learner.log"]), str(names))
    if rc == 0:
        log = (out_dir / "learner.log").read_bytes()
        check("B10 a learner.log over 5 MB is published as its LAST 5,000 lines",
              log.count(b"\n") == 5000 and big_log.endswith(log), str(log.count(b"\n")))
        check("B10 runs.jsonl over 5 MB is published WHOLE (a cut data file would read as the full history)",
              (out_dir / "runs.jsonl").read_bytes() == big_runs, "")


def night(day: int, minute: int = 0) -> dt.datetime:
    return dt.datetime(2026, 10, day, 1, minute)


def holds_runs(path: Path) -> bool:
    with zipfile.ZipFile(path) as z:
        return "ai-agent/data/runs.jsonl" in z.namelist()


def b11(tmp: Path) -> None:
    """runs.jsonl shrinking is a NEEDS-YOU hold: the zip is kept and nothing is pruned, on every night it stays short."""
    e = Env(tmp, "b11")
    code, _s, out = e.backup(when=night(1))
    runs = e.clone / "data" / "runs.jsonl"
    runs.write_text(runs.read_text(encoding="utf-8") + jl([{"run": 999}]), encoding="utf-8")
    code2, s2, out2 = e.backup(when=night(2))
    check("B11 CONTROL: runs.jsonl grew -> ok, exit 0, no hold",
          code == 0 and code2 == 0 and s2["ok"] and not s2["error"], out + out2)
    runs.write_text(jl({"run": i} for i in range(50)), encoding="utf-8")
    code3, s3, out3 = e.backup(when=night(3))
    check("B11 FAULT: runs.jsonl shrank -> NEEDS-YOU, exit 1, ok false, 'runs.jsonl shrank 201 -> 50'",
          code3 == 1 and not s3["ok"] and "NEEDS-YOU" in (s3["error"] or "")
          and "runs.jsonl shrank 201 -> 50" in s3["error"], out3)
    check("B11 FAULT: the shrunken night's zip is KEPT and nothing was pruned",
          (e.dest / "learner-data-20261003-0100.zip").exists() and s3["pruned"] == [] and s3["bytes"] > 0, str(s3))
    st = json.loads(e.status.read_text(encoding="utf-8"))
    check("B11 FAULT: the status FILE says ok false with the NEEDS-YOU reason", not st["ok"] and "NEEDS-YOU" in st["error"],
          str(st))
    codes = [e.backup(when=night(d), keep=14)[0] for d in range(4, 19)]  # 15 more nights, still 50 lines
    big = ["learner-data-20261001-0100.zip", "learner-data-20261002-0100.zip"]
    check("B11 FAULT: 15 more shrunken nights (18 zips, keep 14) -> every night exit 1 and BOTH larger backups remain",
          codes == [1] * 15 and all((e.dest / n).exists() for n in big), f"{codes} {e.dest_files()[:3]}")
    keep_dir = e.dest / "kept-before-reparse"
    keep_dir.mkdir()
    for n in big:
        os.replace(e.dest / n, keep_dir / n)
    code4, s4, out4 = e.backup(when=night(19))
    check("B11 CONTROL: the documented release (larger zips moved into a sub-folder) -> exit 0 and pruning resumes",
          code4 == 0 and s4["ok"] and len(s4["pruned"]) == 3, out4)
    check("B11 CONTROL: the sub-folder is never touched by retention",
          sorted(p.name for p in keep_dir.iterdir()) == big, "")


def b12(tmp: Path) -> None:
    """The reviewer's absent.py: a clone that LOST runs.jsonl must never prune the good copies away."""
    e = Env(tmp, "b12")
    runs = e.clone / "data" / "runs.jsonl"
    good_bytes = runs.read_bytes()
    first = [e.backup(when=night(d))[0] for d in range(1, 15)]
    good = sorted(n for n in e.dest_files() if e.tool.ZIP_RE.match(n))
    check("B12 setup: 14 good nightly backups, each holding runs.jsonl",
          first == [0] * 14 and len(good) == 14 and all(holds_runs(e.dest / n) for n in good), str(first))
    runs.unlink()
    results = [e.backup(when=night(d)) for d in range(15, 30)]
    check("B12 FAULT: 15 nights without runs.jsonl -> every night exit 1, ok false, NEEDS-YOU 'NOT captured'",
          all(c == 1 and not s["ok"] and "runs.jsonl was NOT captured" in (s["error"] or "") for c, s, _o in results),
          str([(c, (s["error"] or "")[:60]) for c, s, _o in results[:2]]))
    check("B12 FAULT: all 14 good backups still exist and still hold runs.jsonl",
          all((e.dest / n).exists() and holds_runs(e.dest / n) for n in good), str(e.dest_files()[:5]))
    check("B12 FAULT: each held night's zip was KEPT (29 zips now)",
          len([n for n in e.dest_files() if e.tool.ZIP_RE.match(n)]) == 29, str(len(e.dest_files())))
    runs.write_bytes(good_bytes)
    code, s, out = e.backup(when=night(30))
    check("B12 CONTROL: runs.jsonl back whole -> exit 0, ok, and pruning resumes (30 zips -> 14)",
          code == 0 and s["ok"] and len([n for n in e.dest_files() if e.tool.ZIP_RE.match(n)]) == 14, out)
    f = Env(tmp, "b12never")
    (f.clone / "data" / "runs.jsonl").unlink()
    seed_old(f.dest)
    code, s, out = f.backup()
    check("B12 FAULT: a clone that never had runs.jsonl -> held too (exit 1), all 20 old files kept",
          code == 1 and "no earlier backup holds one" in (s["error"] or "") and len(f.dest_files()) == 23, out)


def b13(tmp: Path) -> None:
    """A clock that went backwards must never make retention delete tonight's verified zip (review finding 1)."""
    e = Env(tmp, "b13")
    e.dest.mkdir(parents=True)
    future = [f"learner-data-2099010{i}-0100.zip" for i in range(1, 4)]
    for n in future:
        (e.dest / n).write_bytes(b"future")
    code, s, out = e.backup(keep=3)
    tonight = "learner-data-20261021-0100.zip"
    check("B13 FAULT: backups named in the future -> NEEDS-YOU (clock), exit 1, ok false",
          code == 1 and not s["ok"] and "named LATER than now" in (s["error"] or ""), out)
    check("B13 FAULT: tonight's zip KEPT, every future-named file kept, the size recorded",
          (e.dest / tonight).exists() and all((e.dest / n).exists() for n in future) and s["bytes"] > 0, str(s))

    g = Env(tmp, "b13protect")  # the second layer: with the clock hold disabled, `protect` alone must save it
    g.dest.mkdir(parents=True)
    for n in future:
        (g.dest / n).write_bytes(b"future")
    g.tool.clock_hold = lambda dest, final_name: []
    code, s, out = g.backup(keep=3)
    check("B13 FAULT: clock hold disabled -> tonight's zip is STILL not pruned (protect), exit 0",
          code == 0 and (g.dest / tonight).exists() and tonight not in s["pruned"], out + str(g.dest_files()))

    c = Env(tmp, "b13control")
    c.dest.mkdir(parents=True)
    past = [f"learner-data-2026101{i}-0100.zip" for i in range(1, 4)]
    for n in past:
        (c.dest / n).write_bytes(b"older")
    code, s, out = c.backup(keep=3)
    check("B13 CONTROL: past names, keep 3 -> exit 0, the OLDEST pruned, tonight's zip kept",
          code == 0 and s["pruned"] == [past[0]] and (c.dest / tonight).exists(), out)

    u = tmp / "b13unit"
    u.mkdir()
    names = [f"learner-data-2026100{i}-0100.zip" for i in range(1, 5)]
    for n in names:
        (u / n).write_bytes(b"x")
    gone = c.tool.apply_retention(u, 3, protect=names[0])
    check("B13 unit FAULT: apply_retention never deletes the protected name, even when it sorts oldest",
          gone == [] and (u / names[0]).exists(), str(gone))
    gone = c.tool.apply_retention(u, 3)
    check("B13 unit CONTROL: without protect the oldest IS deleted", gone == [names[0]], str(gone))


def b14(tmp: Path) -> None:
    """The ops folder is explicit and guarded: a destination or clone inside it, or a huge one, is refused."""
    e = Env(tmp, "b14")
    e.dest = e.ops / "backups"
    code, s, out = e.backup()
    check("B14 FAULT: a destination under the ops folder -> exit 2 REFUSED, the destination not created",
          code == 2 and "under the ops folder" in (s["error"] or "") and not e.dest.exists(), out)
    f = Env(tmp, "b14clone")
    code, s, out = f.backup(ops_dir=f.clone.parent)  # <root>/clone holds the clone and NOT the destination
    check("B14 FAULT: a clone under the ops folder -> exit 2 REFUSED, nothing in the destination",
          code == 2 and "the clone" in (s["error"] or "") and "under the ops folder" in s["error"]
          and f.dest_files() == [], out)
    g = Env(tmp, "b14big")
    g.tool.OPS_MAX_BYTES = 4000
    (g.ops / "big.bin").write_bytes(b"x" * 5000)
    code, s, out = g.backup()
    check("B14 FAULT: an ops tree over the cap -> exit 2 REFUSED, nothing in the destination",
          code == 2 and "cap" in (s["error"] or "") and g.dest_files() == [], out)
    (g.ops / "big.bin").unlink()
    code, s, out = g.backup(minute=1)
    mem = zip_members(Path(s["zip"])) if s.get("zip") else {}
    check("B14 CONTROL: a normal ops folder -> exit 0, and it is captured (pokebot-ops/samples.jsonl)",
          code == 0 and "pokebot-ops/samples.jsonl" in mem, out)


def b15(tmp: Path) -> None:
    """One run at a time (review finding 6), and the sweep never removes a young .part."""
    e = Env(tmp, "b15")
    e.dest.mkdir(parents=True)
    lock = e.dest / e.tool.LOCK_NAME
    lock.write_text("another run", encoding="utf-8")
    code, s, out = e.backup()
    check("B15 FAULT: a fresh lock -> exit 2 REFUSED, no zip, the lock untouched",
          code == 2 and "another backup holds" in (s["error"] or "") and lock.read_text(encoding="utf-8") == "another run"
          and not any(n.endswith(".zip") for n in e.dest_files()), out)
    old = time.time() - 3 * 3600
    os.utime(lock, (old, old))
    code, s, out = e.backup(minute=1)
    check("B15 CONTROL: a lock 3 h old is stale -> replaced with a WARN, exit 0, and no lock is left behind",
          code == 0 and any("stale lock" in w for w in s["warnings"]) and not lock.exists(), out)

    young = e.dest / "learner-data-20261020-0100.zip.part"
    stale = e.dest / "learner-data-20261019-0100.zip.part"
    alien = e.dest / "learner-data-٢٠٢٠0101-0100.zip.part"  # Arabic-Indic digits: not ours
    for p in (young, stale, alien):
        p.write_bytes(b"part")
    for p in (stale, alien):
        os.utime(p, (old, old))
    code, s, out = e.backup(minute=2)
    check("B15 CONTROL: the sweep removes our .part over an hour old (with a WARN)",
          code == 0 and not stale.exists() and any(stale.name in w for w in s["warnings"]), out)
    check("B15 FAULT: a .part under an hour old (a live run's) is NOT removed", young.exists(), str(e.dest_files()))
    check("B15 FAULT: a .part named in non-ASCII digits is not ours and is NOT removed", alien.exists(), "")

    c = Env(tmp, "b15concurrent")
    real_verify = c.tool.verify_zip
    paused, gate = threading.Event(), threading.Event()

    def slow_verify(path, expect=None):
        if threading.current_thread().name == "runA":
            paused.set()
            gate.wait(20)
        return real_verify(path, expect)

    c.tool.verify_zip = slow_verify
    res = {}
    ta = threading.Thread(target=lambda: res.__setitem__("A", c.backup()), name="runA")
    ta.start()
    paused.wait(20)
    res["B"] = c.backup()
    gate.set()
    ta.join(60)
    a_code, a_s = res.get("A", (None, {}, ""))[:2]
    b_code, b_s = res["B"][:2]
    check("B15 FAULT: two CONCURRENT runs -> the second is REFUSED (exit 2) by the lock",
          b_code == 2 and "another backup holds" in (b_s["error"] or ""), str(b_s.get("error")))
    check("B15 CONTROL: the first run completes (exit 0) with its zip", a_code == 0 and
          "learner-data-20261021-0100.zip" in c.dest_files(), f"{a_code} {a_s.get('error')} {c.dest_files()}")


def b16(tmp: Path) -> None:
    """Backup names are matched with ASCII [0-9] only: a non-ASCII-digit name takes no keep slot (finding 7)."""
    e = Env(tmp, "b16")
    e.dest.mkdir(parents=True)
    olds = [f"learner-data-202609{d:02d}-0100.zip" for d in range(1, 15)]  # 14 old + tonight = 15 > keep 14
    for n in olds:
        (e.dest / n).write_bytes(b"old")
    alien = "learner-data-٢٠٢٠0101-0100.zip"
    (e.dest / alien).write_bytes(b"not ours")
    check("B16 FAULT: ZIP_RE does not match a name in Arabic-Indic digits", e.tool.ZIP_RE.match(alien) is None, "")
    check("B16 CONTROL: ZIP_RE matches an ASCII backup name", e.tool.ZIP_RE.match(olds[0]) is not None, "")
    code, s, out = e.backup()
    ours = [n for n in e.dest_files() if re.fullmatch(r"learner-data-[0-9]{8}-[0-9]{4}\.zip", n, re.ASCII)]
    check("B16 FAULT: with the alien file present, exactly 14 REAL backups remain and the alien file is untouched",
          code == 0 and len(ours) == 14 and (e.dest / alien).read_bytes() == b"not ours", f"{code} {len(ours)} {out}")


def b17(tmp: Path) -> None:
    """--restore-check and --publish-to never write in the clone, whatever the spelling (review finding 5)."""
    e = Env(tmp, "b17")
    code, status, out = e.backup()
    z = Path(status["zip"]) if status.get("zip") else None
    if not z:
        check("B17 setup backup", False, out)
        return
    inside_t = e.clone / "data" / "restore-alias"
    outside_t = tmp / "b17out"
    q = lambda p: Path("\\\\?\\" + str(p.resolve()))  # noqa: E731
    drive, rest = os.path.splitdrive(str(inside_t.resolve()))
    unc = Path("\\\\localhost\\" + drive.rstrip(":") + "$" + rest)
    for label, target in (("\\\\?\\ spelling of a target inside the clone", q(inside_t)),
                          ("\\\\localhost\\C$ spelling of a target inside the clone", unc),
                          ("\\\\?\\ spelling of a target OUTSIDE the clone", q(outside_t))):
        with redirect_stdout(io.StringIO()) as buf:
            rc = e.tool.restore_check(z, target, e.clone)
        check(f"B17 FAULT restore-check: {label} -> refused outright (exit 2), nothing created",
              rc == 2 and "UNC" in buf.getvalue() and not inside_t.exists() and not outside_t.exists(),
              buf.getvalue())
    with redirect_stdout(io.StringIO()) as buf:
        rc = e.tool.publish(e.clone, q(e.clone / "published"))
    check("B17 FAULT publish: a \\\\?\\ spelling of a target inside the clone -> exit 2, not created",
          rc == 2 and not (e.clone / "published").exists(), buf.getvalue())
    # OUTSIDE the clone, so only the outright refusal can say no (the identity layer would catch the inside one alone:
    # a mutant deleting publish's refusal survived the line above)
    pub_out = tmp / "b17pubout"
    with redirect_stdout(io.StringIO()) as buf:
        rc = e.tool.publish(e.clone, q(pub_out))
    check("B17 FAULT publish: a \\\\?\\ spelling of a target OUTSIDE the clone -> refused outright, not created",
          rc == 2 and "UNC" in buf.getvalue() and not pub_out.exists(), buf.getvalue())
    with redirect_stdout(io.StringIO()):
        rc = e.tool.publish(e.clone, pub_out)
    check("B17 CONTROL publish: the same OUTSIDE target in a plain spelling publishes (exit 0)",
          rc == 0 and (pub_out / "runs.jsonl").exists(), str(rc))
    with redirect_stdout(io.StringIO()):
        rc = e.tool.restore_check(z, outside_t, e.clone)
    check("B17 CONTROL: the same OUTSIDE target in a plain spelling restores (exit 0)", rc == 0, str(rc))

    b = Env(tmp, "b17blind")  # the second layer alone: a name check that MISSES (as an alias spelling made it do)
    code, status, out = b.backup()
    b.tool.is_under = lambda child, parent: False
    check("B17 FAULT: with the name check blinded, inside() still finds a target in the clone by IDENTITY",
          b.tool.inside(b.clone / "data" / "x" / "y", b.clone.parent), "")
    check("B17 CONTROL: ... and does NOT claim an unrelated folder", not b.tool.inside(tmp / "elsewhere", b.clone.parent),
          "")
    blind_t = b.clone / "data" / "restore-blind"
    with redirect_stdout(io.StringIO()):
        rc = b.tool.restore_check(Path(status["zip"]), blind_t, b.clone) if status.get("zip") else -1
    check("B17 FAULT: with the name check blinded, restore-check into the clone is still refused, not created",
          rc == 2 and not blind_t.exists(), str(rc))
    with redirect_stdout(io.StringIO()):
        rc = b.tool.publish(b.clone, b.clone / "published-blind")
    check("B17 FAULT: with the name check blinded, publish into the clone is still refused, not created",
          rc == 2 and not (b.clone / "published-blind").exists(), str(rc))


def keyed_rows(ids) -> str:
    """runs.jsonl rows shaped like the learner's: identified by (batch, lane, log), plus fields a reparse rewrites."""
    return jl({"batch": f"202610{10 + i // 50:02d}-0100", "lane": i % 12 + 1, "log": f"Story-debug-{i:05d}.log",
               "score": i * 0.5, "champion": False} for i in ids)


def zip_has_record(path: Path, log_name: str) -> bool:
    with zipfile.ZipFile(path) as z:
        return log_name.encode() in z.read("ai-agent/data/runs.jsonl")


def b18(tmp: Path) -> None:
    """HOLD ON IDENTITY, NOT COUNT (final re-verify 2026-10-21, blocker B3; the reviewer's o4_regrow.py shape)."""
    def regrow(name: str, drop: bool, rows=keyed_rows, old_scheme: bool = False):
        e = Env(tmp, name)
        runs = e.clone / "data" / "runs.jsonl"
        runs.write_text(rows(range(0, 100)), encoding="utf-8")
        real_scheme = e.tool.ID_SCHEME
        if old_scheme:  # the first 3 zips are written as an OLDER tool would: no identity cache under today's scheme
            e.tool.ID_SCHEME = "an-older-scheme"
        first = [e.backup(when=night(d), keep=3)[0] for d in (1, 2, 3)]
        e.tool.ID_SCHEME = real_scheme
        nights = []
        for n in range(4):  # a bad reparse dropped records 0..9; the learner keeps appending 50 runs a night
            start = 10 if drop else 0
            runs.write_text(rows(range(start, 150 + 50 * n)), encoding="utf-8")
            nights.append(e.backup(when=night(4 + n), keep=3))
        return e, first, nights

    e, first, nights = regrow("b18regrow", drop=True)
    check("B18 setup: 3 nights of 100 records, keep 3 -> exit 0", first == [0, 0, 0], str(first))
    check("B18 FAULT 10 records dropped + 50 added a night (the COUNT grows 100 -> 140 -> 290): every night "
          "NEEDS-YOU, exit 1, 'MISSING'", all(c == 1 and not s["ok"] and "NEEDS-YOU" in (s["error"] or "")
                                             and "10 runs.jsonl record(s)" in s["error"] and "MISSING" in s["error"]
                                             for c, s, _o in nights),
          str([(c, s.get("runs_lines"), (s["error"] or "")[:90]) for c, s, _o in nights]))
    check("B18 FAULT: nothing was pruned on any of the 4 nights", all(s["pruned"] == [] for _c, s, _o in nights),
          str([s["pruned"] for _c, s, _o in nights]))
    pre = [f"learner-data-2026100{d}-0100.zip" for d in (1, 2, 3)]
    check("B18 FAULT: all 3 pre-drop backups still exist and still hold the dropped record 0",
          all((e.dest / n).exists() and zip_has_record(e.dest / n, "Story-debug-00000.log") for n in pre),
          str(e.dest_files()))
    check("B18 FAULT: the count pre-filter alone did NOT fire (runs.jsonl grew), so the hold is the identity check's",
          all("shrank" not in (s["error"] or "") for _c, s, _o in nights), "")

    c, cfirst, cnights = regrow("b18growth", drop=False)
    check("B18 CONTROL pure growth (+50 a night, nothing dropped): every night exit 0, ok, one zip pruned (keep 3)",
          cfirst == [0, 0, 0] and all(code == 0 and s["ok"] and len(s["pruned"]) == 1 for code, s, _o in cnights),
          str([(code, s["pruned"], (s["error"] or "")[:80]) for code, s, _o in cnights]))
    check("B18 CONTROL: exactly 3 backups remain", len([n for n in c.dest_files() if c.tool.ZIP_RE.match(n)]) == 3,
          str(c.dest_files()))

    r = Env(tmp, "b18rescore")  # what cmd_reparse legitimately does: the SAME identities, re-parsed field values
    runs = r.clone / "data" / "runs.jsonl"
    runs.write_text(keyed_rows(range(100)), encoding="utf-8")
    r.backup(when=night(1), keep=3)
    runs.write_text(keyed_rows(range(100)).replace('"champion": false', '"champion": true'), encoding="utf-8")
    code, s, out = r.backup(when=night(2), keep=3)
    check("B18 CONTROL a reparse that rewrites every row's CONTENT but keeps its identity -> exit 0, no hold",
          code == 0 and s["ok"], out)

    def unkeyed(ids) -> str:  # the reviewer's exact rows: no batch, lane or log -> identified by content
        return jl({"run_id": i} for i in ids)

    _u, _uf, unights = regrow("b18unkeyed", drop=True, rows=unkeyed)
    check("B18 FAULT the reviewer's o4_regrow rows ({'run_id': i}, no identity fields): every night held, nothing "
          "pruned", all(code == 1 and "MISSING" in (s["error"] or "") and s["pruned"] == [] for code, s, _o in unights),
          str([(code, (s["error"] or "")[:80]) for code, s, _o in unights]))
    _o, _of, onights = regrow("b18oldzips", drop=True, old_scheme=True)
    check("B18 FAULT earlier zips WITHOUT the identity cache (an older tool's): still held, read the slow way",
          all(code == 1 and "MISSING" in (s["error"] or "") for code, s, _o2 in onights),
          str([(code, (s["error"] or "")[:80]) for code, s, _o2 in onights]))

    # The release the message names: the pre-drop zips moved into a sub-folder -> pruning resumes.
    aside = e.dest / "kept-before-reparse"
    aside.mkdir()
    for n in pre:
        os.replace(e.dest / n, aside / n)
    code, s, out = e.backup(when=night(8), keep=3)
    check("B18 CONTROL the documented release (pre-drop zips moved into a sub-folder) -> exit 0, pruning resumes",
          code == 0 and s["ok"] and len(s["pruned"]) == 2 and sorted(p.name for p in aside.iterdir()) == pre,
          out + str(s["pruned"]))

    # The cache must be TRUE: a manifest whose run_ids disagree with its records fails verification.
    v = Env(tmp, "b18verify")
    real_manifest = v.tool.manifest_for

    def lying_manifest(got, clone, created):
        man = real_manifest(got, clone, created)
        row = next(m for m in man["members"] if m["name"] == v.tool.RUNS_MEMBER)
        row["run_ids"] = row["run_ids"][1:]  # one record silently missing from the cache
        return man

    v.tool.manifest_for = lying_manifest
    code, s, out = v.backup()
    check("B18 FAULT a manifest whose cached run_ids drop one record -> VERIFY FAILED, exit 1, nothing kept",
          code == 1 and "run_ids do not match" in (s["error"] or "") and v.dest_files() == [], out)
    v.tool.manifest_for = real_manifest
    code, s, out = v.backup(minute=1)
    check("B18 CONTROL the true cache verifies -> exit 0", code == 0 and s["ok"], out)
    check("B18 unit: a keyed row's identity is its (batch, lane, log), whatever its other fields; a row without them "
          "is a content hash", v.tool.run_identity({"batch": "b", "lane": 3, "log": "x.log", "score": 1})
          == v.tool.run_identity({"batch": "b", "lane": 3, "log": "x.log", "score": 9}) == '["b",3,"x.log"]'
          and v.tool.run_identity({"run": 1}).startswith("row:")
          and v.tool.run_identity({"run": 1}) != v.tool.run_identity({"run": 2}), "")


def dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait(30)
    return p.pid


def b19(tmp: Path) -> None:
    """A lock dated in the FUTURE, or naming a pid that is not running, is a dead run's (re-verify 2026-10-21, B4)."""
    e = Env(tmp, "b19future")  # the reviewer's o4_lock.py future arm: a killed run's lock, then the clock went back
    e.dest.mkdir(parents=True)
    lock = e.dest / e.tool.LOCK_NAME
    lock.write_text("unreadable: no pid", encoding="utf-8")  # so ONLY the age rule can call it stale
    ahead = time.time() + 30 * 86400
    os.utime(lock, (ahead, ahead))
    runs = [e.backup(minute=m) for m in range(3)]
    check("B19 FAULT a leftover lock dated 30 days AHEAD -> replaced with a WARN ('FUTURE'), exit 0 on all 3 nights",
          [c for c, _s, _o in runs] == [0, 0, 0] and any("FUTURE" in w for w in runs[0][1]["warnings"])
          and not lock.exists(), str([(c, s["error"]) for c, s, _o in runs]))
    lock.write_text("unreadable: no pid", encoding="utf-8")
    soon = time.time() + 30
    os.utime(lock, (soon, soon))
    code, s, out = e.backup(minute=5)
    check("B19 CONTROL a lock only 30 s ahead (inside the 2-minute grace for a coarse filesystem clock) and no pid "
          "-> REFUSED, exit 2, the lock untouched", code == 2 and "another backup holds" in (s["error"] or "")
          and lock.exists() and lock.read_text(encoding="utf-8") == "unreadable: no pid", out)
    lock.unlink(missing_ok=True)  # missing when a mutant replaced it: report that as the FAIL above, not a crash

    d = Env(tmp, "b19deadpid")
    d.dest.mkdir(parents=True)
    lock = d.dest / d.tool.LOCK_NAME
    gone = dead_pid()
    check("B19 unit: pid_alive(this process) is True, pid_alive(an exited child) is False",
          d.tool.pid_alive(os.getpid()) and not d.tool.pid_alive(gone), str(gone))
    lock.write_text(json.dumps({"pid": gone, "since": "now"}), encoding="utf-8")  # FRESH: the age rules say live
    code, s, out = d.backup()
    check("B19 FAULT a FRESH lock whose pid is not running -> replaced ('not running'), exit 0, no lock left",
          code == 0 and any("not running" in w for w in s["warnings"]) and not lock.exists(), out)
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        lock.write_text(json.dumps({"pid": holder.pid, "since": "now"}), encoding="utf-8")
        code, s, out = d.backup(minute=1)
        check("B19 CONTROL a fresh lock whose pid IS running (another live process) -> REFUSED, exit 2, untouched",
              code == 2 and "another backup holds" in (s["error"] or "") and lock.exists(), out)
    finally:
        holder.kill()
        holder.wait(30)


def free_drive_letter() -> str | None:
    for letter in "QPONMLKJIHGWVUTSR":
        if not os.path.exists(f"{letter}:\\"):
            return letter
    return None


def b20(tmp: Path) -> None:
    """A destination drive that is not present is REFUSED by preflight (re-verify 2026-10-21, B5)."""
    if os.name != "nt":
        check("B20 (not Windows: no drive letters)", True)
        return
    letter = free_drive_letter()
    if letter is None:
        check("B20 SKIPPED: every candidate drive letter is in use on this PC", True)
        return
    e = Env(tmp, "b20")
    e.tool.volume_id = load_tool().volume_id  # the REAL probes, as the nightly task runs them
    e.tool.free_gb = load_tool().free_gb
    e.dest = Path(f"{letter}:/pokebot-backups/learner")
    code, s, out = e.backup()
    st = json.loads(e.status.read_text(encoding="utf-8")) if e.status.exists() else {}
    check(f"B20 FAULT destination on an absent drive {letter}: -> exit 2 'REFUSED: destination drive not present'",
          code == 2 and (s["error"] or "").startswith("REFUSED: destination drive not present"), out)
    check("B20 FAULT: the status file records the refusal", "destination drive not present" in (st.get("error") or ""),
          str(st))
    check("B20 CONTROL drive_present: True for the temp folder's drive, False for the absent letter",
          e.tool.drive_present(tmp) and not e.tool.drive_present(e.dest), "")
    e.dest = e.root / "E" / "pokebot-backups" / "learner"
    e.tool.volume_id = lambda p: 2 if e.tool.is_under(p, e.clone.parent) else 1
    code, s, out = e.backup(minute=1)
    check("B20 CONTROL the same run to a present drive -> exit 0", code == 0 and s["ok"], out)


def installer_carries_test_flag(text: str) -> bool:
    return "--test-allow-same-volume" in text


def b9(tmp: Path) -> None:
    if os.name != "nt":
        check("B9 (not Windows: no Task Scheduler)", True)
        return
    ps = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command"]
    probe = "if (Get-ScheduledTask -TaskName 'Pokebot-Ops-Backup' -ErrorAction SilentlyContinue) {'present'} else {'absent'}"
    before = subprocess.run(ps + [probe], capture_output=True, text=True, timeout=120).stdout.strip()
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                        str(INSTALLER)], capture_output=True, text=True, timeout=120)
    after = subprocess.run(ps + [probe], capture_output=True, text=True, timeout=120).stdout.strip()
    out = r.stdout + r.stderr
    for want in ("WHATIF", "Pokebot-Ops-Backup", "daily at 1:00 AM", "-3.12 -B", "StartWhenAvailable",
                 "backup_learner.py", "no scheduled task was created"):
        check(f"B9 the default dry run prints '{want}'", r.returncode == 0 and want in out, out[-400:])
    check("B9 CONTROL: the dry run left the task's registration unchanged", before == after and before in
          ("present", "absent"), f"{before} -> {after}")
    m = re.search(r'run:\s+"([^"]+)" -3\.12 -B', out)
    launcher = m.group(1) if m else ""
    if Path(r"C:\Windows\pyw.exe").is_file():
        check("B9 the task launches pyw.exe (windowless: no console flashes at 1 AM)",
              launcher.lower().endswith("pyw.exe"), launcher or out[-400:])
    else:
        check("B9 no pyw.exe on this PC: the py.exe fallback is SAID, not silent", "pyw.exe was not found" in out, out)
    if launcher:
        # HEADLESS, as Task Scheduler runs it: stdout and stderr are None, so print() must be harmless and the exit
        # code and the status file are the only record.
        e = Env(tmp, "b9headless")
        shim = ("import sys, runpy; sys.stdout = sys.stderr = None; t = sys.argv[1]; sys.argv = sys.argv[1:]; "
                "runpy.run_path(t, run_name='__main__')")
        base = [launcher, "-3.12", "-B", "-c", shim, str(TOOL), "--clone", str(e.clone), "--dest", str(e.dest),
                "--status-file", str(e.status), "--ops-dir", str(e.ops), "--min-free-gb", "0"]
        quiet = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        rc = subprocess.run(base, **quiet).returncode
        st = json.loads(e.status.read_text(encoding="utf-8")) if e.status.exists() else {}
        check("B9 FAULT headless through the task's launcher: same volume -> exit 2 and the status file says REFUSED",
              rc == 2 and "REFUSED" in (st.get("error") or ""), f"{rc} {st}")
        rc = subprocess.run(base + ["--test-allow-same-volume"], **quiet).returncode
        st = json.loads(e.status.read_text(encoding="utf-8")) if e.status.exists() else {}
        check("B9 CONTROL headless through the task's launcher: test flag -> exit 0 and the status file says ok",
              rc == 0 and st.get("ok") is True, f"{rc} {st}")
    text = INSTALLER.read_text(encoding="utf-8")
    check("B9 the installer is ASCII-only (PowerShell 5.1 reads a BOM-less .ps1 as Windows-1252)", text.isascii(), "")
    check("B9 CONTROL: the installed command never carries --test-allow-same-volume", not installer_carries_test_flag(text))
    mutant = text.replace("Arguments   = ''", "Arguments   = '--test-allow-same-volume'", 1)
    check("B9 FAULT: a mutant installer carrying the test flag IS caught by that check",
          mutant != text and installer_carries_test_flag(mutant), "mutation anchor missing" if mutant == text else "")


def main() -> int:
    # ignore_cleanup_errors: a LEAKED handle (the B8 fault) must be reported as a FAIL line, not crash the cleanup.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        tmp = Path(td)
        for test in (b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15, b16, b17, b18, b19, b20):
            try:
                test(tmp)
            except Exception as ex:  # noqa: BLE001 - a crash is a FAIL with its reason, never a silent pass
                check(f"{test.__name__.upper()} crashed", False, f"{type(ex).__name__}: {ex}")
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        line = ("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:300]}")
        # ASCII-safe: a FAIL detail can hold a non-ASCII file name (B15/B16), and printing it to a cp1252 pipe once
        # crashed the report instead of showing the FAIL (found by mutant M15)
        print(line.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks, {len(bad)} failed)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
