"""GATE — prove `.claude/hooks/block-commit-over-gates.ps1` can still BLOCK and still ALLOW.

WHY THIS EXISTS. On 2026-09-25 this command committed over a RED suite:

    grep -aE "ALL [0-9]+ ENFORCING|FAIL" /tmp/gatesD.out | tail -2 && git add ... && git commit ...

`run_gates.py` had printed **FAILED: 1 of 85**. The commit proceeded anyway, because the exit
status gating it was **grep's** — and grep had SUCCEEDED at finding the word "FAIL". The gate's own
exit code was consulted by nothing.

‼ IT WAS THE SECOND OCCURRENCE. `08-MISTAKES.md` already held the first (a `for` loop whose
`&& echo PASS || echo FAIL` swallowed a red Tier 0 and let a docs commit through). The remedy
recorded then was PROSE, and prose did not hold. CLAUDE.md says committing over a red doc gate is
the same offence as `git add -A` — and `git add -A` has a hook. Now so does this.

⭐ AND THE HOOK'S OWN SELF-TEST REFUTED ITS FIRST DESIGN, WHICH IS WHY THIS GATE EXISTS AT ALL.
Version 1 blocked "a gate `.py` runs in the same command" — a BLACKLIST. The real 2026-09-25
command runs no gate; it greps a SAVED log. The self-test caught that the hook would have allowed
the exact command it was written to prevent. Version 2 inverts it into a WHITELIST: a `git commit`
may share its command only with `git`, message-writing (`cat`/`echo`/`printf`/`tee`), `cd`, `true`.
⇒ *a blacklist must enumerate every way to read a result and is wrong the moment one is missed.*

WHAT THIS GATE CHECKS. It runs the hook's `-SelfTest` case table (12 cases) and fails if ANY
regresses — in EITHER direction:
  * a BYPASS would let a commit ride on some other command's exit status again;
  * a FALSE POSITIVE would block the ordinary `git add && git commit && git push`, or a heredoc
    commit message that merely NAMES a gate — and this repo's messages name gates constantly.
    A check with false positives trains the reader to bypass it, which is strictly worse than none.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

BAR = "=" * 92
HOOK = Path(__file__).resolve().parent.parent.parent / ".claude" / "hooks" / "block-commit-over-gates.ps1"


def main() -> int:
    print(BAR)
    print("GATE — the commit-over-gates hook still blocks the real failure, and still allows work")
    print(BAR)

    if not HOOK.exists():
        print(f"  ⛔ MISSING: {HOOK}")
        print("  The hook CLAUDE.md relies on is not on disk. That is a failure, not a skip.")
        return 1

    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        # ⛔ NOT a silent pass. A gate that cannot run must SAY so; reporting PASS here would be
        # the same lie this whole class of bug is about.
        print("  ‼ SKIP — no powershell/pwsh on PATH, so the hook could not be exercised.")
        print("    Reported as a FAILURE on purpose: an unrun gate is not a passing gate.")
        return 1

    proc = subprocess.run(
        [powershell, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(HOOK), "-SelfTest"],
        capture_output=True, text=True,
    )
    for line in (proc.stdout or "").splitlines():
        print(f"  {line.strip()}" if line.strip() else "")
    for line in (proc.stderr or "").splitlines():
        if line.strip():
            print(f"  stderr: {line.strip()}")

    if proc.returncode != 0:
        print()
        print("  ‼ THE HOOK REGRESSED. Either a command that used to be blocked now slips through")
        print("    — and a commit can once again ride on grep's exit status over a RED suite — or a")
        print("    legitimate shape is now blocked, which trains the reader to bypass the hook.")
        print("    Both directions are failures. Fix the hook, not the case table, unless the case")
        print("    table itself encodes a false premise (which has happened here before).")
        return 1

    print()
    print("  PASS — the real 2026-09-25 command is still blocked, and the ordinary")
    print("         add/commit/push and gate-naming commit messages are still allowed.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
