"""Self-test for tools/status.py (backlog A1, spec S1-5). Offline, about 5 s, on a FAKE learner tree.

T1 a good tree: every labelled field present, no 'unavailable' in the tuner section, at most 40 lines and 2.5 KB.
T2 FAULT: a zero-byte state.json and a truncated cycles.jsonl -> those fields say 'unavailable', the other sections
   still print, no traceback, exit 0.
T3 a pinned --now and --started give the exact elapsed and ETA strings.
T4 READ-ONLY: every file in the fake tree is byte-identical, with the same mtime, after a run.
T5 the raw-log archive line (backlog O3): the count of runs/<tag>/raw.zip and the last archive-check result; a
   half-written data/archive_check.json makes only that line 'unavailable'.
"""
from __future__ import annotations

import hashlib
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
    return clone


def snapshot(root: Path) -> dict[str, tuple[str, float]]:
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime) for p in root.rglob("*")
            if p.is_file()}


def tuner_block(out: str) -> str:
    return out.split("BOT TUNER", 1)[-1].split("DISK:", 1)[0]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        clone = fake_tree(root)
        base = ["--clone", str(clone), "--repo", str(root / "repo"), "--now", "2026-10-20 3:41 PM"]
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

    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:200]}"))
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
