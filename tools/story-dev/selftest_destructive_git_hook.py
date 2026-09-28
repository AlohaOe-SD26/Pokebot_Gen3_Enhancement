"""GATE — prove `.claude/hooks/block_destructive_git.py` can still BLOCK, still ALLOW, and still SPEAKS VALID JSON.

WHY THIS EXISTS (2026-09-27, `08-MISTAKES.md`; the hook approved by the user 2026-09-28). A reviewer agent "reverted" a
test mutation with `git checkout -- <file>` while the fix under review was UNCOMMITTED, and deleted the fix. The hook
blocks git commands that can silently discard work, for every agent.

⛔ THE FIRST VERSION WAS BROKEN IN A WAY ITS OWN GATE COULD NOT SEE. It was PowerShell; its deny output was NOT VALID
JSON (a BOM-less .ps1 is read as Windows-1252 by PowerShell 5.1, which mangled the reason's em-dash), so Claude Code
could never have honoured it. The gate ran only the case table, never the real stdout. An adversarial review found it,
plus 49 bypasses in 79 probes (a `# don't` comment hid every later line; `for ... do git ...`; `$(...)`; directories
as paths; `--har`; ...). ⇒ The hook is now Python (`shlex` lexing, `json.dumps` output) and this gate checks the REAL
output, not just the decision function.

WHAT IT CHECKS
  S1  the hook's case table passes (incident, the review's bypass classes A-H, its false positives, mentions, the hatch);
  S2  FAULT ARM: the decision forced to ALWAYS-ALLOW must FAIL the table;
  S3  FAULT ARM: the decision forced to ALWAYS-BLOCK must FAIL the table;
  S4  registered in `.claude/settings.json` (PreToolUse, Bash|PowerShell) as the Python hook;
  S5  THE REAL HOOK PROCESS: a destructive Bash command and a destructive PowerShell command each print stdout that
      `json.loads` accepts, is ASCII-only, and says permissionDecision "deny"; an ordinary command prints NOTHING;
      garbage stdin prints nothing and exits 0 (fails open); a non-ASCII command still yields ASCII JSON.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 selftest_destructive_git_hook.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

BAR = "=" * 92
ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "block_destructive_git.py"
SETTINGS = ROOT / ".claude" / "settings.json"
failures: list = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        failures.append(msg)


def load_hook():
    spec = importlib.util.spec_from_file_location("block_destructive_git", HOOK)
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
    print("GATE — the destructive-git hook blocks discarding work, allows ordinary work, and emits valid JSON")
    print(BAR)
    if not HOOK.exists():
        print(f"  ⛔ MISSING: {HOOK} — the hook the project relies on is not on disk. A failure, not a skip.")
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
        registered = any("block_destructive_git.py" in c for c in cmds)
    except (OSError, ValueError) as err:
        print(f"  ‼ could not read {SETTINGS}: {err}")
        registered = False
    check(registered, "S4 registered in .claude/settings.json (PreToolUse, Bash|PowerShell), the Python hook")

    # S7 — every hook finds its script through $CLAUDE_PROJECT_DIR (2026-09-28, MEASURED): with a RELATIVE path, a
    # hook runs against the session's CURRENT directory. From `tools/story-dev` the Python hook could not open its
    # file and exited 2 (= BLOCK every command), and the PowerShell hooks failed with a non-blocking code, so the
    # "ENFORCED" `git add -A` hook silently let a dry run through. `|| true` keeps a path failure from exiting 2.
    def relative_hook_paths(cfg_: dict) -> list:
        bad_ = []
        for _event, entries in (cfg_.get("hooks") or {}).items():
            for e in entries:
                for h in e.get("hooks", []):
                    c = h.get("command", "")
                    if ".claude/hooks/" in c and "$CLAUDE_PROJECT_DIR/.claude/hooks/" not in c:
                        bad_.append(c)
                    elif ".claude/hooks/" in c and not c.rstrip().endswith("|| true"):
                        bad_.append(c + "   <- no '|| true' (a path failure could exit 2 and block everything)")
        return bad_
    try:
        cfg_now = json.loads(SETTINGS.read_text(encoding="utf-8"))
        bad = relative_hook_paths(cfg_now)
    except (OSError, ValueError) as err:
        bad = [f"unreadable settings: {err}"]
    check(not bad, f"S7 every hook command uses \"$CLAUDE_PROJECT_DIR/.claude/hooks/...\" and '|| true' {bad or ''}")
    mutated = {"hooks": {"PreToolUse": [{"matcher": "Bash|PowerShell", "hooks": [
        {"type": "command", "command": "py -3.12 .claude/hooks/block_destructive_git.py"}]}]}}
    check(bool(relative_hook_paths(mutated)), "S7 FAULT ARM — a RELATIVE hook path is caught")

    g = "g" + "it"
    for tool, cmd in (("Bash", f"{g} checkout -- CLAUDE.md"), ("PowerShell", f"{g} reset --hard"),
                      ("Bash", f"{g} stash drop  # résumé — café")):
        rc, out = run_hook({"tool_name": tool, "tool_input": {"command": cmd}, "cwd": str(ROOT)})
        try:
            dec = json.loads(out)["hookSpecificOutput"]["permissionDecision"]
        except (ValueError, KeyError, TypeError):
            dec = f"UNPARSEABLE: {out[:120]!r}"
        check(rc == 0 and dec == "deny" and out.isascii(),
              f"S5 [{tool}] {cmd[:40]!r} -> valid ASCII JSON deny (got {dec!r}, rc={rc})")
    rc, out = run_hook({"tool_name": "Bash", "tool_input": {"command": f"{g} status --short"}, "cwd": str(ROOT)})
    check(rc == 0 and out == "", f"S5 an ordinary command prints NOTHING (got {out[:80]!r})")
    rc, out = run_hook("this is not json")
    check(rc == 0 and out == "", f"S5 garbage stdin fails OPEN: nothing printed, exit 0 (rc={rc}, out={out[:60]!r})")

    # S6 — S5 must be able to FAIL: a mutant hook that prints plain text (the first version's real failure: output
    # Claude Code cannot parse) must NOT pass the JSON check.
    src = HOOK.read_text(encoding="utf-8")
    anchor = "            print(json.dumps({"
    if src.count(anchor) == 1:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            mut = Path(tmp) / "mutant_hook.py"
            mut.write_text(src.replace(anchor, "            print('BLOCKED \\u2014 not json'); (json.dumps({", 1)
                           .replace("REASON.format(why=why)}}))", "REASON.format(why=why)}}))", 1), encoding="utf-8")
            _rc, mout = run_hook({"tool_name": "Bash", "tool_input": {"command": f"{g} stash drop"}, "cwd": str(ROOT)}, mut)
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
    print("PASS — destructive commands get a VALID deny, ordinary work passes, both mutants fail the table.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
