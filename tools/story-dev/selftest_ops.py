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
  B9 the installer: the default run is a dry run (exit 0, names the task, 1:00 AM, py -3.12 -B, StartWhenAvailable,
     "no scheduled task was created") and the task's registration state is unchanged; the installed command never
     carries the test flag (FAULT: a mutant text carrying it is caught).
  B10 the weekly snapshot (--publish-to): FAULT a target inside the clone is refused and not created; CONTROL the six
     files land in a main-checkout target, a learner.log over 5 MB is cut to its last 5,000 lines, and runs.jsonl
     over 5 MB is published WHOLE (measured 2026-10-21: the real one is 10.2 MB in 2,586 lines).
  B11 FAULT runs.jsonl shrank since the previous backup -> still ok, with 'WARN runs.jsonl shrank A -> B' (a reparse
     may legitimately rewrite it). CONTROL it grew -> no warning.

Run: cd tools/story-dev && py -3.12 selftest_ops.py      (about 10 s)
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
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

    def backup(self, minute: int = 0, **kw):
        import datetime as dt
        when = dt.datetime(2026, 10, 21, 1, minute)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code, status = self.tool.run_backup(self.clone, self.dest, 14, 10.0, self.status, when=when, **kw)
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
            str(e2.status), "--min-free-gb", "0"]
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


def b11(tmp: Path) -> None:
    """runs.jsonl shrinking between backups is a WARNING (a reparse may rewrite it), never a failure, never silent."""
    e = Env(tmp, "b11")
    code, _s, out = e.backup(minute=0)
    runs = e.clone / "data" / "runs.jsonl"
    runs.write_text(runs.read_text(encoding="utf-8") + jl([{"run": 999}]), encoding="utf-8")
    code2, s2, out2 = e.backup(minute=1)
    check("B11 CONTROL: runs.jsonl grew -> ok and no 'shrank' warning",
          code == 0 and code2 == 0 and not any("shrank" in w for w in s2["warnings"]), out + out2)
    runs.write_text(jl({"run": i} for i in range(50)), encoding="utf-8")
    code3, s3, out3 = e.backup(minute=2)
    check("B11 FAULT: runs.jsonl shrank -> still ok (exit 0) with 'WARN runs.jsonl shrank 201 -> 50'",
          code3 == 0 and s3["ok"] and any("WARN runs.jsonl shrank 201 -> 50" in w for w in s3["warnings"]), out3)


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
        for test in (b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11):
            try:
                test(tmp)
            except Exception as ex:  # noqa: BLE001 - a crash is a FAIL with its reason, never a silent pass
                check(f"{test.__name__.upper()} crashed", False, f"{type(ex).__name__}: {ex}")
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:300]}"))
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks, {len(bad)} failed)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
