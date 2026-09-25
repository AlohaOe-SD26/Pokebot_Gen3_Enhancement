r"""GATE — NOTHING UNGUARDED MAY STAND BETWEEN A `finally` AND ITS FIXTURE RESTORE.

WHY THIS EXISTS (2026-09-25, and it came within one line of real damage)
------------------------------------------------------------------------
`Ch24ChampionMode` clears the game. Its `finally` restores the pinned fixture so a CLEARED-GAME
state never reaches `current_state.ss1` — which is what the real bot resumes from. I added a
one-line fixture-CAPTURE convenience directly above that restore, inside the same `try`, and wrote
`os.environ` in a driver whose `run()` does `import os as _os`.

The NameError did not merely skip my capture. **It skipped the RESTORE:**

    [ch24champion] ⛔⛔ COULD NOT RESTORE THE FIXTURE: name 'os' is not defined —
                   `current_state.ss1` may now hold a CLEARED-GAME state.

⇒ **A CONVENIENCE DISABLED A SAFETY, ON ITS FIRST RUN.** No damage that time (every pinned fixture
verified OK, no tracked save was dirty, the user's own profiles were last written in July) — but the
blast radius was checked afterwards, which is exactly the wrong order.

THE RULE THIS ENFORCES
----------------------
Inside the `try` that guards a fixture restore, **every statement preceding the restore must itself
be a `try`** — i.e. it must be incapable of propagating an exception past itself and stranding the
restore. Guarded additions are fine and expected; bare ones are the defect.

WHAT IT CHECKS
  R1  For every `try` whose body performs a restore (`load_save_state`), each statement BEFORE that
      restore is an `ast.Try`. Anything else FAILS, and names the line.

⚠ DELIBERATE LIMITATION, STATED RATHER THAN HIDDEN. This checks only inside the restore's OWN
guarding `try`. Statements earlier in the enclosing `finally` (the readings/bookkeeping block) could
also strand a restore by raising. Those are reported as an INFO count, not failed, because they are
overwhelmingly `getattr`/dict writes and failing them would make this gate noisy — and a noisy gate
teaches the reader to bypass it, which is strictly worse than no gate (CLAUDE.md §6). If one of
those ever DOES strand a restore, tighten this to R2 and take the noise.

⛔ AST, NEVER GREP. A textual search for "load_save_state" cannot tell a guarded statement from a
bare one, which is the entire distinction being enforced.
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS = [HERE / "story_harness.py"]

RESTORE_CALLS = {"load_save_state"}


def _calls_restore(node: ast.AST) -> bool:
    """Does this statement (at any depth) call a restore?"""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            fn = sub.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name in RESTORE_CALLS:
                return True
    return False


def scan(path: Path) -> tuple[list[str], int, int]:
    """Returns (violations, restore_sites_seen, unguarded_prefinally_stmts)."""
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src, filename=str(path))

    violations: list[str] = []
    sites = 0
    info_pre = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        # Which top-level statement of this try's body performs the restore?
        restore_at = None
        for i, stmt in enumerate(node.body):
            if _calls_restore(stmt):
                restore_at = i
                break
        if restore_at is None:
            continue
        sites += 1
        for stmt in node.body[:restore_at]:
            if isinstance(stmt, ast.Try):
                continue  # guarded — exactly what the fix installed
            violations.append(
                f"{path.name}:{stmt.lineno}  a BARE `{type(stmt).__name__}` stands before the "
                f"fixture restore at line {node.body[restore_at].lineno} — if it raises, the "
                f"RESTORE NEVER RUNS and a run's state leaks into the next one. "
                f"Wrap it in its own try/except."
            )

    # INFO only (see the docstring's deliberate limitation)
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and node.finalbody:
            fin = node.finalbody
            guard_at = None
            for i, stmt in enumerate(fin):
                if isinstance(stmt, ast.Try) and any(_calls_restore(s) for s in stmt.body):
                    guard_at = i
                    break
            if guard_at is not None:
                info_pre += sum(1 for s in fin[:guard_at] if not isinstance(s, ast.Try))

    return violations, sites, info_pre


def run() -> int:
    print("=" * 96)
    print("GATE — nothing UNGUARDED may stand between a `finally` and its FIXTURE RESTORE")
    print("=" * 96)

    all_violations: list[str] = []
    total_sites = 0
    total_info = 0
    for path in TARGETS:
        if not path.exists():
            print(f"  ‼ MISSING  {path.name} — cannot scan")
            all_violations.append(f"{path.name} is missing")
            continue
        violations, sites, info_pre = scan(path)
        total_sites += sites
        total_info += info_pre
        print(f"  scanned {path.name}: {sites} restore site(s)")
        all_violations.extend(violations)

    if total_sites == 0:
        # ⛔ NON-VACUITY. A gate that finds nothing to guard is not passing, it is BLIND.
        print("  ⛔ NO RESTORE SITES FOUND AT ALL — this gate is measuring nothing.")
        print("=" * 96)
        print("RESULT: FAIL — zero restore sites; the matcher is broken or the file moved.")
        return 1

    print(f"  (info) {total_info} bare statement(s) sit earlier in a `finally`, before the "
          f"restore's guarding try — reported, NOT failed; see the docstring.")
    print("=" * 96)
    if all_violations:
        print(f"RESULT: FAIL — {len(all_violations)} unguarded statement(s) before a restore:")
        for v in all_violations:
            print(f"  ⛔ {v}")
        return 1
    print(f"RESULT: ALL PASS — {total_sites} restore site(s), nothing bare in front of any of them.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
