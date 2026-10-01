"""GATE — prove `.claude/hooks/block_shell_text.py` can still BLOCK, still ALLOW, still SPEAKS VALID JSON, and fails OPEN.

WHY THIS EXISTS (USER RULING 29, 2026-10-01; `08-MISTAKES.md` 2026-09-30 and 2026-10-01). The written rule
"documentation and code text never pass through a shell-quoted string" was broken FIVE times in two sessions; CLAUDE.md
rule 6 turns a rule broken repeatedly into a gate. The hook reuses `block_destructive_git.py`'s parser, so a change
there can break this hook too: this gate is what notices.

WHAT IT CHECKS (the destructive-git gate's shape; its first version's failure, output Claude Code could not parse, is
why S5/S6 read the REAL process output):
  S1  the hook's case table passes (the five real incidents, H1-H6, mentions, ordinary work, the hatch);
  S2  FAULT ARM: the decision forced to ALWAYS-ALLOW must FAIL the table;
  S3  FAULT ARM: the decision forced to ALWAYS-BLOCK must FAIL the table;
  S4  registered in `.claude/settings.json` (PreToolUse, Bash|PowerShell) through "$CLAUDE_PROJECT_DIR/.claude/hooks/"
      and ending in `|| true` (the destructive gate's S7 covers every hook's shape; this pins THIS hook's entry);
  S5  THE REAL HOOK PROCESS: a Bash heredoc and a PowerShell here-string written to a file each print ASCII JSON with
      permissionDecision "deny"; a non-ASCII body still yields ASCII JSON; an ordinary command prints NOTHING; garbage
      stdin prints nothing and exits 0; the hook copied WITHOUT its parser module fails OPEN (nothing, exit 0);
  S6  FAULT ARM: a mutant hook printing plain text is REJECTED by the S5 JSON check.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 selftest_shell_text_hook.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

BAR = "=" * 92
ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "block_shell_text.py"
SETTINGS = ROOT / ".claude" / "settings.json"
failures: list = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        failures.append(msg)


def load_hook():
    spec = importlib.util.spec_from_file_location("block_shell_text", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_hook(payload, hook_path: Path = HOOK) -> "tuple[int, str]":
    data = payload if isinstance(payload, str) else json.dumps(payload)
    r = subprocess.run([sys.executable, str(hook_path)], input=data, capture_output=True, text=True, encoding="utf-8",
                       timeout=30, cwd=str(ROOT))
    return r.returncode, (r.stdout or "").strip()


def deny_is_valid(out: str) -> bool:
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny" and out.isascii()
    except (ValueError, KeyError, TypeError):
        return False


def main() -> int:
    print(BAR)
    print("GATE — the shell-text hook blocks text written through the shell, allows ordinary work, emits valid JSON")
    print(BAR)
    if not HOOK.exists():
        print(f"  ⛔ MISSING: {HOOK} — the hook USER RULING 29 approved is not on disk. A failure, not a skip.")
        return 1
    hook = load_hook()

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = hook.run_selftest()
    for line in buf.getvalue().splitlines():
        print(f"    {line.strip()}")
    check(rc == 0, "S1 the hook's case table passes")

    for tag, label, forced in (("S2", "ALWAYS-ALLOW", None), ("S3", "ALWAYS-BLOCK", "forced")):
        with redirect_stdout(io.StringIO()):
            mrc = hook.run_selftest(decide=lambda text, shell, f=forced: f)
        check(mrc != 0, f"{tag} FAULT ARM — decision forced to {label} — makes the case table FAIL")

    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
        cmds = [h.get("command", "") for e in cfg.get("hooks", {}).get("PreToolUse", [])
                if "Bash" in e.get("matcher", "") and "PowerShell" in e.get("matcher", "")
                for h in e.get("hooks", [])]
        mine = [c for c in cmds if "block_shell_text.py" in c]
    except (OSError, ValueError) as err:
        print(f"  ‼ could not read {SETTINGS}: {err}")
        mine = []
    check(len(mine) == 1 and "$CLAUDE_PROJECT_DIR/.claude/hooks/block_shell_text.py" in mine[0]
          and mine[0].rstrip().endswith("|| true"),
          f"S4 registered ONCE in .claude/settings.json (PreToolUse, Bash|PowerShell), via $CLAUDE_PROJECT_DIR, "
          f"ending '|| true' (got {mine})")

    cases = (("Bash", "cat > a.md <<'EOF'\nsome text\nEOF"),
             ("PowerShell", "@'\nsome text\n'@ | Set-Content a.md"),
             ("Bash", "cat > a.md <<'EOF'\nrésumé — café\nEOF"))
    for tool, cmd in cases:
        rc, out = run_hook({"tool_name": tool, "tool_input": {"command": cmd}, "cwd": str(ROOT)})
        try:
            dec = json.loads(out)["hookSpecificOutput"]["permissionDecision"]
        except (ValueError, KeyError, TypeError):
            dec = f"UNPARSEABLE: {out[:120]!r}"
        check(rc == 0 and dec == "deny" and out.isascii(),
              f"S5 [{tool}] {cmd[:36]!r} -> valid ASCII JSON deny (got {dec!r}, rc={rc})")
    rc, out = run_hook({"tool_name": "Bash", "tool_input": {"command": "git status --short && grep -n '<<EOF' a.md"},
                        "cwd": str(ROOT)})
    check(rc == 0 and out == "", f"S5 an ordinary command (with a QUOTED '<<EOF' mention) prints NOTHING (got {out[:80]!r})")
    rc, out = run_hook("this is not json")
    check(rc == 0 and out == "", f"S5 garbage stdin fails OPEN: nothing printed, exit 0 (rc={rc}, out={out[:60]!r})")
    with tempfile.TemporaryDirectory() as tmp:
        lone = Path(tmp) / "block_shell_text.py"
        shutil.copy2(HOOK, lone)
        rc, out = run_hook({"tool_name": "Bash", "tool_input": {"command": cases[0][1]}, "cwd": str(ROOT)}, lone)
        check(rc == 0 and out == "",
              f"S5 WITHOUT its parser module the hook fails OPEN: nothing printed, exit 0 (rc={rc}, out={out[:60]!r})")

    src = HOOK.read_text(encoding="utf-8")
    anchor = "            print(json.dumps({"
    if src.count(anchor) == 1:
        with tempfile.TemporaryDirectory() as tmp:
            mut = Path(tmp) / "block_shell_text.py"
            shutil.copy2(HOOK.parent / "block_destructive_git.py", Path(tmp) / "block_destructive_git.py")
            mut.write_text(src.replace(anchor, "            print('BLOCKED \\u2014 not json'); (json.dumps({", 1),
                           encoding="utf-8")
            _rc, mout = run_hook({"tool_name": "Bash", "tool_input": {"command": cases[0][1]}, "cwd": str(ROOT)}, mut)
            check(bool(mout) and not deny_is_valid(mout),
                  f"S6 FAULT ARM — a hook printing non-JSON is REJECTED by the S5 check (got {mout[:50]!r})")
    else:
        check(False, "S6 (mutation anchor not found exactly once — update the gate)")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print(f"  {f}")
        return 1
    print("PASS — text written through the shell gets a VALID deny, ordinary work passes, both mutants fail the table.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
