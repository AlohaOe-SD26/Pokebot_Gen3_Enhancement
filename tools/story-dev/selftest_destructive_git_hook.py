"""GATE — prove `.claude/hooks/block-destructive-git.ps1` can still BLOCK and still ALLOW.

WHY THIS EXISTS (2026-09-27, `08-MISTAKES.md`; the hook approved by the user 2026-09-28). A reviewer
agent "reverted" a test mutation with `git checkout -- <file>` while the fix under review was
UNCOMMITTED, and deleted the fix. CLAUDE.md already forbade discarding local work, force-pushing and
unasked branch deletion — in prose. The hook enforces it for every agent; this gate proves the hook
still works, in BOTH directions:
  * a BYPASS would let a destructive command through again (the first draft had two, both found by
    its own self-test: PowerShell's equal -and/-or precedence let `--force` through, and a quoted
    path with a space — this repo's own path shape — hid `git -C "<path>" checkout -- f`);
  * a FALSE POSITIVE would block ordinary work (branch switches, unstaging, `stash list`, a commit
    message that merely MENTIONS a destructive command). A gate that fires on mentions trains the
    reader to bypass it, which is strictly worse than no gate.

WHAT IT CHECKS
  S1  the hook's `-SelfTest` case table passes (it exits 0);
  S2  FAULT ARM: a copy whose decision is forced to ALWAYS-ALLOW must FAIL its table;
  S3  FAULT ARM: a copy whose decision is forced to ALWAYS-BLOCK must FAIL its table;
  S4  the hook is registered in `.claude/settings.json` under PreToolUse for Bash|PowerShell.
The arms prove the table has teeth both ways: a table of only "allow" cases would pass S2's mutant.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 selftest_destructive_git_hook.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BAR = "=" * 92
ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "block-destructive-git.ps1"
SETTINGS = ROOT / ".claude" / "settings.json"
failures: list = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        failures.append(msg)


def run_selftest(ps: str, path: Path) -> "tuple[int, str]":
    proc = subprocess.run([ps, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path), "-SelfTest"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def mutant(src: str, old: str, new: str) -> "str | None":
    return src.replace(old, new, 1) if src.count(old) == 1 else None


def main() -> int:
    print(BAR)
    print("GATE — the destructive-git hook still blocks discarding work, and still allows ordinary work")
    print(BAR)
    if not HOOK.exists():
        print(f"  ⛔ MISSING: {HOOK} — the hook the project relies on is not on disk. A failure, not a skip.")
        return 1
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if ps is None:
        print("  ‼ no powershell/pwsh on PATH: the hook could not be exercised. Reported as a FAILURE on purpose.")
        return 1

    rc, out = run_selftest(ps, HOOK)
    for line in out.splitlines():
        if line.strip():
            print(f"    {line.strip()}")
    check(rc == 0, "S1 the hook's own case table passes")

    src = HOOK.read_text(encoding="utf-8")
    arms = (
        ("S2", "decision forced to ALWAYS-ALLOW",
         "                $r = Get-SegmentVerdict $seg $hatchSeen\n", "                $r = $null\n"),
        ("S3", "decision forced to ALWAYS-BLOCK",
         "                $r = Get-SegmentVerdict $seg $hatchSeen\n", "                $r = 'forced'\n"),
    )
    with tempfile.TemporaryDirectory() as tmp:
        for tag, label, old, new in arms:
            m = mutant(src, old, new)
            check(m is not None, f"({tag} mutation applied exactly once: {label})")
            if m is None:
                continue
            p = Path(tmp) / f"mutant_{tag}.ps1"
            p.write_text(m, encoding="utf-8-sig")
            mrc, _ = run_selftest(ps, p)
            check(mrc != 0, f"{tag} FAULT ARM — {label} — makes the case table FAIL (exit {mrc})")

    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
        cmds = [h.get("command", "") for e in cfg.get("hooks", {}).get("PreToolUse", [])
                if "Bash" in e.get("matcher", "") and "PowerShell" in e.get("matcher", "")
                for h in e.get("hooks", [])]
        registered = any("block-destructive-git.ps1" in c for c in cmds)
    except (OSError, ValueError) as error:
        print(f"  ‼ could not read {SETTINGS}: {error}")
        registered = False
    check(registered, "S4 registered in .claude/settings.json (PreToolUse, Bash|PowerShell)")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print(f"  {f}")
        return 1
    print("PASS — the 2026-09-27 command is blocked, ordinary work is allowed, and the table fails both mutants.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
