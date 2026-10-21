"""Self-test for tools/status.py (backlog A1, spec S1-5). Offline, about 5 s, on a FAKE learner tree.

T1 a good tree: every labelled field present, no 'unavailable' in the tuner section, at most 40 lines and 2.5 KB.
T2 FAULT: a zero-byte state.json and a truncated cycles.jsonl -> those fields say 'unavailable', the other sections
   still print, no traceback, exit 0.
T3 a pinned --now and --started give the exact elapsed and ETA strings.
T4 READ-ONLY: every file in the fake tree is byte-identical, with the same mtime, after a run.
T5 the raw-log archive line (backlog O3): the count of runs/<tag>/raw.zip and the last archive-check result; a
   half-written data/archive_check.json makes only that line 'unavailable'.
T6 the archive line's held count (O3 review fix): cycles HELD for review, from data/state.json; an unreadable
   state.json gives 'held for review: ?', never a false 0.
T7 the nightly backup line (backlog O4, final re-verify 2026-10-21 B6), from tools/ops/backup_learner.py's
   backup_status.json. CONTROL ok -> 'BACKUP: ok' with the last run's age and the newest zip's (T1 also keeps the
   whole screen in budget with it); CONTROL no status file -> 'no backup yet'. FAULT a NEEDS-YOU night and a REFUSED
   night show the word, the ages and the reason, cut to the screen width; a half-written file and a JSON that is not
   a status say 'unavailable', exit 0, never a false ok.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

STATUS = Path(__file__).resolve().parent / "status.py"
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def run(*args: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(STATUS), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)
    return proc.returncode, proc.stdout + proc.stderr


def fake_tree(root: Path) -> Path:
    clone = root / "clone" / "ai-agent"
    (clone / "data").mkdir(parents=True)
    (clone / "findings").mkdir()
    (clone / "inbox").mkdir()
    state = {"current": {"tag": "ai0099", "started": "2026-10-20 04:05:32 AM", "lanes": 12, "minutes": 720.0},
             "failures": 0}
    (clone / "data" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    rows = [{"source": "cycle", "tag": f"ai009{i}", "runs": 50 + i, "usable": 40 + i} for i in range(6, 9)]
    (clone / "data" / "cycles.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (clone / "data" / "learner.log").write_text("[2026-10-20 04:05:30 AM] consult: exit 0, 2 proposal(s) queued\n",
                                               encoding="utf-8")
    (clone / "data" / "agent.lock").write_text("999999", encoding="utf-8")
    (clone / "findings" / "LATEST.md").write_text("# x\nChampions: 10/100 (10%) of scored runs.\n", encoding="utf-8")
    for name in ("a", "b"):
        (clone / "inbox" / f"{name}.json").write_text("{}", encoding="utf-8")
    repo = root / "repo"
    (repo / "PROJECT KNOWLEDGE").mkdir(parents=True)
    (repo / "PROJECT KNOWLEDGE" / "ai-frontier.txt").write_text("AI frontier: test chapter\n", encoding="utf-8")
    (repo / "ai_player" / "evidence").mkdir(parents=True)
    (repo / "ai_player" / "evidence" / "x.txt").write_text("line\nOVERALL: PASS\n", encoding="utf-8")
    dest = root / "backupdisk" / "pokebot-backups" / "learner"  # the nightly backup's folder and its status file
    dest.mkdir(parents=True)
    for name in ("learner-data-20261019-0100.zip", "learner-data-20261020-0100.zip", "notes.txt"):
        (dest / name).write_bytes(b"PK")
    write_backup_status(root, {"time": "2026-10-20 01:00:05 AM", "ok": True, "dest": str(dest),
                               "zip": str(dest / "learner-data-20261020-0100.zip"), "bytes": 1076145, "warnings": [],
                               "error": None, "pruned": []})
    return clone


def write_backup_status(root: Path, status) -> Path:
    path = root / "localappdata" / "pokebot-ops" / "backup_status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(status if isinstance(status, str) else json.dumps(status), encoding="utf-8")
    return path


def backup_of(out: str) -> str:
    return next((l for l in out.splitlines() if l.startswith("BACKUP:")), "(no BACKUP line)")


def snapshot(root: Path) -> dict[str, tuple[str, float]]:
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime) for p in root.rglob("*")
            if p.is_file()}


def tuner_block(out: str) -> str:
    return out.split("BOT TUNER", 1)[-1].split("DISK:", 1)[0]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        clone = fake_tree(root)
        status_file = root / "localappdata" / "pokebot-ops" / "backup_status.json"
        base = ["--clone", str(clone), "--repo", str(root / "repo"), "--now", "2026-10-20 3:41 PM",
                "--backup-status", str(status_file)]
        before = snapshot(root)
        code, out = run(*base)
        after = snapshot(root)
        block = tuner_block(out)
        check("T1 exit 0", code == 0, str(code))
        for want in ("cycle ai0099", "12 lanes", "ai0098 48/58", "Champions: 10/100", "consult inbox 2 waiting",
                     "consult: exit 0", "AI frontier: test chapter", "x.txt: OVERALL: PASS", "NOT YET"):
            check(f"T1 shows '{want}'", want in out, want)
        check("T1 CONTROL: no 'unavailable' in the tuner section of a good tree", "unavailable" not in block, block)
        check("T1 at most 40 lines", len(out.splitlines()) <= 40, str(len(out.splitlines())))
        check("T1 at most 2.5 KB", len(out.encode("utf-8")) <= 2560, str(len(out.encode("utf-8"))))
        check("T4 READ-ONLY: the tree is byte-identical with the same mtimes", before == after)

        (clone / "data" / "state.json").write_text("", encoding="utf-8")
        with open(clone / "data" / "cycles.jsonl", "a", encoding="utf-8") as fh:
            fh.write('{"source": "cycle", "tag": "ai01')  # a row being written right now
        code, out = run(*base)
        block = tuner_block(out)
        check("T2 FAULT: exit 0 with a broken state.json", code == 0, str(code))
        check("T2 FAULT: no traceback", "Traceback" not in out, out[-300:])
        check("T2 FAULT: the cycle field says 'unavailable'", "cycle: unavailable" in block, block)
        check("T2 FAULT: the truncated cycles row is skipped, the good rows still print", "ai0098 48/58" in block, block)
        check("T2 FAULT: the other sections still print", "DISK:" in out and "AI PLAYER:" in out, out[-300:])

        code, out = run(*base, "--started", "1:10 PM", "--eta-minutes", "240")
        check("T3 elapsed from a pinned clock", "elapsed 2 h 31 m" in out, out.splitlines()[2] if out else "")
        check("T3 ETA from a pinned clock", "ETA 5:10 PM" in out, out.splitlines()[2] if out else "")

        check("T5 CONTROL: no archives yet -> '0 raw.zip | archive-check never run'",
              "raw-log archives: 0 raw.zip | archive-check never run" in out, tuner_block(out))
        (clone / "runs" / "ai0090").mkdir(parents=True)
        (clone / "runs" / "ai0090" / "raw.zip").write_bytes(b"PK")
        (clone / "data" / "archive_check.json").write_text(json.dumps(
            {"checked": "2026-10-21 04:00:00 AM", "archives": 1, "bad": 0, "lines": ["OK ai0090 4 2"]}),
            encoding="utf-8")
        code, out = run(*base)
        check("T5 the archive count and the last archive-check result are shown",
              "raw-log archives: 1 raw.zip | last archive-check 2026-10-21 04:00:00 AM: 1 checked, 0 BAD" in out,
              tuner_block(out))
        check("T5 'not built yet' no longer lists O3", "NOT YET" in out and "O3" not in out.split("NOT YET", 1)[1],
              out[-200:])
        (clone / "data" / "archive_check.json").write_text('{"checked": "2026-10', encoding="utf-8")
        code, out = run(*base)
        check("T5 FAULT: a half-written archive_check.json -> that line says 'unavailable', exit 0, the rest prints",
              code == 0 and "raw-log archives: unavailable" in out and "AI PLAYER:" in out, tuner_block(out))

        # T6 the held count (O3 review fix): cycles the learner HELD for review, read from data/state.json
        (clone / "data" / "archive_check.json").unlink()
        state = {"current": None, "failures": 0, "cycles": [{"tag": "ai0090", "pruned": True},
                                                           {"tag": "ai0091", "held": {"reason": "x", "since": "y"}}]}
        (clone / "data" / "state.json").write_text(json.dumps(state), encoding="utf-8")
        code, out = run(*base)
        check("T6 one held cycle -> 'held for review: 1 (ai0091)' on the archive line",
              code == 0 and "| held for review: 1 (ai0091)" in out, tuner_block(out))
        state["cycles"][1].pop("held")
        (clone / "data" / "state.json").write_text(json.dumps(state), encoding="utf-8")
        code, out = run(*base)
        check("T6 CONTROL: nothing held -> 'held for review: 0'", "| held for review: 0" in out, tuner_block(out))
        (clone / "data" / "state.json").write_text("", encoding="utf-8")
        code, out = run(*base)
        check("T6 FAULT: an unreadable state.json -> 'held for review: ?', exit 0",
              code == 0 and "| held for review: ?" in out, tuner_block(out))

        # T7 the nightly backup line (backlog O4; final re-verify 2026-10-21 B6), from backup_status.json
        code, out = run(*base)
        check("T7 CONTROL an ok backup -> 'BACKUP: ok', the last run's age and the newest zip's (from its NAME)",
              backup_of(out) == "BACKUP: ok | last run 14 h 40 m ago | newest zip 14 h 41 m old", backup_of(out))
        dest = root / "backupdisk" / "pokebot-backups" / "learner"
        needs = ("NEEDS-YOU (the new zip was written, verified and KEPT; NOTHING was pruned): 10 runs.jsonl record(s) "
                 "held by 3 earlier backup(s) are MISSING tonight (newest holder learner-data-20261019-0100.zip; e.g. "
                 '["20261010-0100",1,"Story-debug-00000.log"]): a reparse that dropped records? If intended, move '
                 "those backups into a sub-folder of the destination (retention never looks inside one) and pruning "
                 "resumes")
        write_backup_status(root, {"time": "2026-10-20 01:00:05 AM", "ok": False, "dest": str(dest),
                                   "zip": str(dest / "learner-data-20261020-0100.zip"), "error": needs, "pruned": []})
        code, out = run(*base)
        line = backup_of(out)
        check("T7 FAULT a held night -> 'BACKUP: NEEDS-YOU', the ages, then the reason (cut to the screen width)",
              line.startswith("BACKUP: NEEDS-YOU | last run 14 h 40 m ago | newest zip 14 h 41 m old | 10 runs.jsonl "
                              "record(s)") and len(line) <= 118, line)
        check("T7 FAULT ... and the whole screen stays within 40 lines and 2.5 KB",
              len(out.splitlines()) <= 40 and len(out.encode("utf-8")) <= 2560,
              f"{len(out.splitlines())} lines {len(out.encode('utf-8'))} bytes")
        write_backup_status(root, {"time": "2026-10-20 01:00:05 AM", "ok": False, "dest": "Q:/pokebot-backups/learner",
                                   "zip": None, "error": "REFUSED: destination drive not present: Q:\\ for "
                                   "Q:/pokebot-backups/learner (is the backup disk plugged in?)", "pruned": []})
        code, out = run(*base)
        line = backup_of(out)
        check("T7 FAULT a refused night -> 'BACKUP: REFUSED' and its reason",
              line.startswith("BACKUP: REFUSED | last run 14 h 40 m ago | newest zip ?")
              and "destination drive not present" in line, line)
        write_backup_status(root, '{"time": "2026-10')  # the backup is rewriting it right now
        code, out = run(*base)
        check("T7 FAULT a half-written backup_status.json -> 'BACKUP: unavailable', exit 0, no traceback, the rest "
              "prints", code == 0 and backup_of(out).startswith("BACKUP: unavailable: JSONDecodeError")
              and "Traceback" not in out and "AI PLAYER:" in out, backup_of(out))
        write_backup_status(root, "{}")
        code, out = run(*base)
        check("T7 FAULT a JSON file that is not a backup status -> 'unavailable', never a false ok",
              backup_of(out).startswith("BACKUP: unavailable: ValueError"), backup_of(out))
        code, out = run(*base[:-1], str(root / "nowhere" / "backup_status.json"))
        check("T7 CONTROL no status file (the task never ran) -> 'BACKUP: no backup yet'",
              backup_of(out) == "BACKUP: no backup yet (no backup_status.json)", backup_of(out))
        spec = importlib.util.spec_from_file_location("status_under_test", STATUS)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        default = mod.default_backup_status()
        check("T7 the default status path is ops_config.json's status_file, expanded (no '%')",
              default.name == "backup_status.json" and default.parent.name == "pokebot-ops" and "%" not in str(default),
              str(default))

    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:200]}"))
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
