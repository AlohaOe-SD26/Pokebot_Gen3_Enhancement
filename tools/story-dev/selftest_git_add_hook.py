"""GATE — prove `.claude/hooks/block-blind-git-add.ps1` can still BLOCK and still ALLOW.

WHY THIS EXISTS. `CLAUDE.md` calls that hook **"ENFORCED, not requested"** and both `/wrapup` and
`/checkpoint` tell the agent that `git add -A` is blocked by it. Three documents therefore lean on
it — and until 2026-08-22 nothing had ever proven it fires. Deep sanity check PASS 4 measured it
across 22 executed cases and found **eight bypasses and one false positive**:

    BYPASSES   git add -Av        short-option bundling defeated `-A\\b`
               git add --al       git accepts unambiguous long-option prefixes
               git add ./         the old pattern required the dot to END the token
               git add "."        quoting defeated a literal-dot match
               git add -- .       the end-of-options separator shifted the pathspec
               git add *          shell glob — same sweep, different spelling
               git -C <p> add -A  GLOBAL OPTIONS between `git` and the subcommand
               git add :/         pathspec magic for "the whole repo"

    FALSE POSITIVE  `|`, `;` and `&` were treated as shell separators even inside QUOTED TEXT and
               HEREDOC BODIES, so merely WRITING the phrase — a doc line, a test table, a
               mistakes-log entry — was blocked. It blocked the very command written to test the
               hook. This project's standing rule is that a check with false positives trains the
               reader to bypass it, which is strictly worse than no check.

‼ THE POINT OF THIS FILE. Pass 3 of the same audit found `repro_whiteout_abort.py` — a gate that
COULD NOT FAIL. The lesson recorded then was that anything enforceable belongs in a GATE, and that
every gate must be FAULT-TESTED both ways. A hardened hook with no standing proof would have been
the same defect one layer down, so the hook carries 31 permanent cases behind `-SelfTest` and this
gate runs them. Both directions were fault-injected on 2026-08-22 before shipping:
  * deleting the global-option skip   -> 3 of 31 FAIL (the `git -C` family reopens)
  * deleting the quote/heredoc mask   -> 1 of 31 FAIL (the false positive reopens)

EXIT CODES: 0 every case behaves; 1 any case regressed, or the hook is missing/unrunnable.
‼ A missing hook or a missing PowerShell is a LOUD FAILURE, never a silent pass — "the scan found
nothing" must never read as "nothing is wrong" (this project's silent-zero family).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 selftest_git_add_hook.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / ".claude" / "hooks" / "block-blind-git-add.ps1"

BAR = "=" * 88


def main() -> int:
    print(BAR)
    print("GIT-ADD HOOK — FAULT TEST (blocks the wildcard forms, allows the legitimate ones)")
    print(BAR)

    if not HOOK.is_file():
        print(f"  ‼ MISSING HOOK: {HOOK}")
        print("    CLAUDE.md calls this hook ENFORCED and /wrapup + /checkpoint both cite it.")
        print("    A missing enforcement mechanism is a failure, not a skip.")
        return 1

    # ‼ Resolve PowerShell rather than assuming it is on PATH, and FAIL LOUDLY if it is absent —
    # a gate that silently passes when it cannot run is the shape pass 3 spent a day on.
    shell = shutil.which("powershell") or shutil.which("pwsh")
    if shell is None:
        print("  ‼ NEITHER `powershell` NOR `pwsh` IS ON PATH — cannot execute the hook.")
        print("    Refusing to report success over a check that never ran.")
        return 1

    cmd = [shell, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(HOOK), "-SelfTest"]
    print(f"  RUNNING: {Path(shell).name} -File {HOOK.relative_to(REPO)} -SelfTest")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("  ‼ THE HOOK SELF-TEST TIMED OUT (120s). A hook must never hang — it runs on every")
        print("    Bash/PowerShell tool call, so a hang here wedges the whole session.")
        return 1

    for line in (proc.stdout or "").splitlines():
        print(f"  {line.strip()}" if line.strip() else "")
    for line in (proc.stderr or "").splitlines():
        if line.strip():
            print(f"  stderr: {line.strip()}")

    if proc.returncode != 0:
        print()
        print("  ‼ THE HOOK REGRESSED. A case that used to block now allows, or a case that used to")
        print("    allow now blocks. Both directions matter: a bypass lets a wildcard stage sweep in")
        print("    an unreviewed subagent file (this happened TWICE on 2026-08-13, and the second")
        print("    one was PUSHED); a false positive trains the reader to bypass the hook entirely.")
        return 1

    print()
    print("  PASS — the hook still blocks every wildcard form and still allows every")
    print("         legitimate one, including merely WRITING the phrase in a doc or a heredoc.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
