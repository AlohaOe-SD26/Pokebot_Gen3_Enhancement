"""PROMOTION TOOL — copy sandbox → custom under the project's own rules, and REFUSE if they are unmet.

‼‼ WHY THIS IS A TOOL AND NOT A CHECKLIST. Promotion has a documented procedure (measure first,
restore point BEFORE touching anything, copy, re-measure BOTH directions, verify by DRIVING and
never by a diff) — and on 2026-08-14 a hand-run promotion still shipped with a hole: the gate that
proved the promoted fix hard-coded `sandbox-pokebot` on its import path, so **nothing verified the
fix had actually landed in the other fork.** A prose checklist cannot notice that; a tool can
refuse. `CLAUDE.md`: *anything enforceable belongs in a GATE, not in prose.*

⛔ THIS TOOL DOES NOT DECIDE. Promotion is the USER's call, every time — it only executes an
already-approved one, and it fails closed on anything it cannot verify.

WHAT IT REFUSES TO DO (each of these is a real failure this project has paid for):
  * promote with a DIRTY working tree            — you could not tell afterwards what moved
  * promote without an annotated RESTORE POINT   — there would be no rollback target
  * promote while local and origin have diverged — the remote is the truth here
  * promote a file that is IDENTICAL             — a no-op promotion inflates a commit and lies
  * report success without RE-MEASURING drift in BOTH directions afterwards

WHAT IT STILL CANNOT DO, and says so: it cannot DRIVE the bot. A copy is not evidence. After this
returns, run a real driver against `--build custom` and paste the ACCEPTANCE line — that is the
standing rule and this tool prints the reminder rather than pretending to satisfy it.

    PYTHONUTF8=1 py -3.12 promote.py --check                       # measure only, change nothing
    PYTHONUTF8=1 py -3.12 promote.py --restore-point <tag> --go     # execute an approved promotion

Exit 0 = clean (or, with --check, drift measured). Exit 1 = refused or verification failed.
"""

import hashlib
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
CUSTOM = REPO / "custom-pokebot"
#: ⛔⛔ THE COMPARISON SET, AND ITS LIMITS — SAY THEM, DO NOT IMPLY COVERAGE (2026-08-17, pass 2+3).
#: Two independent audit agents flagged the same thing: `drift: 0` reads like "the forks are
#: identical" and it means "the forks are identical IN `modules/` AND `plugins/`, over `*.py`".
#: It does NOT look at root scripts, `*.yml`, `profiles/`, `tests/`, `utility/` or `tools/`.
#: ‼ Both agents then diffed ALL of those by hand and found them byte-identical TODAY — so this is
#: a FALSE-CONFIDENCE risk, not a live gap. The fix is therefore honesty in the OUTPUT rather than a
#: wider comparison: widening it would sweep in `profiles/` (gitignored runtime state that is
#: SUPPOSED to differ) and start reporting drift that is not drift.
TREES = ("modules", "plugins")
SCOPE_NOTE = ("compared: modules/ + plugins/, *.py only  |  NOT compared: root scripts, *.yml, "
              "profiles/ (runtime, expected to differ), tests/, utility/, tools/")
BAR = "=" * 92


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, timeout=60)


def measure() -> "tuple[list[str], list[str]]":
    """(files differing or missing in custom, files present in custom but not sandbox).

    ‼ BOTH DIRECTIONS. A one-way sweep cannot see a file that exists only in the target, which is
    how a promotion can silently leave orphaned code behind.
    """
    differing, orphaned = [], []
    for tree in TREES:
        for source in sorted((SANDBOX / tree).rglob("*.py")):
            if "__pycache__" in source.parts:
                continue
            rel = source.relative_to(SANDBOX)
            target = CUSTOM / rel
            if not target.exists():
                differing.append(str(rel).replace("\\", "/"))
            elif _digest(source) != _digest(target):
                differing.append(str(rel).replace("\\", "/"))
        for target in sorted((CUSTOM / tree).rglob("*.py")):
            if "__pycache__" in target.parts:
                continue
            rel = target.relative_to(CUSTOM)
            if not (SANDBOX / rel).exists():
                orphaned.append(str(rel).replace("\\", "/"))
    return differing, orphaned


def _refuse(reason: str) -> int:
    print(f"\n  ⛔ REFUSED — {reason}")
    print(BAR)
    return 1


def main() -> int:
    check_only = "--check" in sys.argv
    go = "--go" in sys.argv
    tag = None
    if "--restore-point" in sys.argv:
        index = sys.argv.index("--restore-point")
        if index + 1 < len(sys.argv):
            tag = sys.argv[index + 1]

    print(BAR)
    print("PROMOTION — sandbox-pokebot → custom-pokebot")
    print(BAR)

    differing, orphaned = measure()
    # ‼ PRINT THE SCOPE BESIDE THE NUMBER. "drift: 0" reads as "the forks are identical"; it means
    # "identical in what this tool looks at". Two audit agents had to derive that from the source.
    print(f"  SCOPE: {SCOPE_NOTE}")
    print(f"  drift (sandbox → custom): {len(differing)} file(s)")
    for name in differing:
        print(f"      {name}")
    print(f"  orphaned (in custom only): {len(orphaned)} file(s)")
    for name in orphaned:
        print(f"      ‼ {name}")

    if check_only or not go:
        print("\n  (measure only — nothing was changed. Pass --restore-point <tag> --go to execute.)")
        print(BAR)
        return 0

    # ---- REFUSALS, in the order that makes each one cheapest to fix --------------------------
    if not differing:
        return _refuse("there is nothing to promote — drift is already zero. A no-op promotion "
                       "would inflate a commit and claim work that did not happen.")

    dirty = _git("status", "--porcelain").stdout.strip()
    if dirty:
        return _refuse("the working tree is DIRTY. Promote from a clean tree, so the resulting "
                       f"diff is exactly the promotion and nothing else.\n{dirty[:400]}")

    ahead_behind = _git("rev-list", "--left-right", "--count", "HEAD...@{upstream}").stdout.split()
    if len(ahead_behind) == 2 and ahead_behind != ["0", "0"]:
        return _refuse(f"local and origin have diverged (ahead {ahead_behind[0]}, behind "
                       f"{ahead_behind[1]}). The remote is the truth here — reconcile first.")

    if not tag:
        return _refuse("no --restore-point given. A promotion without a rollback target is not "
                       "reversible; create an annotated tag first and pass its name.")
    if _git("rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode != 0:
        return _refuse(f"restore point {tag!r} does not exist. Create it BEFORE promoting:\n"
                       f"      git tag -a {tag} -m \"...\" && git push origin {tag}")
    if _git("ls-remote", "--exit-code", "--tags", "origin", tag).returncode != 0:
        return _refuse(f"restore point {tag!r} exists locally but is NOT PUSHED. A rollback target "
                       f"that lives only on this machine is not a rollback target.\n"
                       f"      git push origin {tag}")

    # ---- execute ----------------------------------------------------------------------------
    print(f"\n  restore point verified (local + origin): {tag}")
    print("  copying:")
    for name in differing:
        source, target = SANDBOX / name, CUSTOM / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"      promoted {name}")

    # ---- verify: re-measure, both directions, and prove byte-equality per file ---------------
    after_differing, after_orphaned = measure()
    mismatched = [n for n in differing if _digest(SANDBOX / n) != _digest(CUSTOM / n)]
    print("\n  VERIFY")
    print(f"      drift after     : {len(after_differing)} (expected 0)")
    print(f"      orphaned after  : {len(after_orphaned)} (expected 0)")
    print(f"      byte-identical  : {len(differing) - len(mismatched)}/{len(differing)}")
    if after_differing or mismatched:
        return _refuse("post-copy verification FAILED — the trees are still not identical.")

    print("\n  ✅ COPY VERIFIED. Drift is zero in both directions.")
    print("\n  ‼ NOT DONE YET — A COPY IS NOT EVIDENCE. The standing rule is VERIFY BY DRIVING:")
    print("      PYTHONUTF8=1 py -3.12 story_harness.py <save> --driver <d> --build custom")
    print("      ...and paste the ACCEPTANCE line. Also run any --build-aware gates against")
    print("      custom (repro_box_counter_move_test.py, repro_pid_identity_key.py), because a")
    print("      gate that only ever imports sandbox cannot see whether the fix landed here.")
    print("  ‼ Then record it in custom-pokebot/DIVERGENCE-LOG.md and update the drift row.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
