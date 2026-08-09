"""`#24-teachmsgstall`: does `normalize_to_overworld` refuse to settle while a MESSAGE is
still printing? Structural check — NO EMULATOR, runs in under a second.

THE BUG THIS DEFENDS AGAINST (reproduced 2026-08-09, 2 of 2 runs, frame-identical).
`teach_hm_move` hands off through `normalize_to_overworld()`, whose own call site
(`early_game.py`, "NORMALIZE FIRST") already warns that otherwise *"we open the BAG on top of
the pending prompt, and the whole teach wedges in BAG_MENU"*. That guard was written for an
open MENU and checks `_menu_task_active()` — whose markers are
`("Task_ShowStartMenu", "ListMenuDummyTask", "Task_HandleChooseMonInput")`. A post-battle
message chain is **not** a menu, so `Task_ContinueTaskAfterMessagePrints` never blocked the
hand-off. Teaching right after a WON battle therefore opens the bag mid-message and the bag
list never advances:

    TEACH EXIT reason=post-select-900-exhausted  ... frame=900
    TEACH EXIT reason=ride:hard-cap stall_peak=82 ... frame=8999
    tasks=['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']

— byte-for-byte the batch's own failing signature (`x4-runs/20260807-160545`).

WHY STRUCTURAL AND NOT LIVE. The live fixture exists and is cheap (~19,000 frames, see the
punch-list item), and it is the proof that the FIX WORKS. This script is the cheap regression
guard that the gate is still WIRED IN — the same role `repro_watchdog_budget_collision.py`
plays for KI-43, which existed precisely because a correct constant sat next to code that
never consulted it.

‼ POSITIVE CONTROL: the parser must also find `_menu_task_active` in the same `settled`
expression. That call is known to be there, so if the control fails the parser is broken and
a red result below would be meaningless rather than a real regression.

Fault-inject to see it go RED: delete the message check from `settled` and re-run.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_teach_message_gate.py
"""
import ast
import pathlib
import sys

SOURCE = pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot" / "modules" / "story" / "early_game.py"

#: The task the reproduction actually caught on screen. Kept as a literal here, on purpose:
#: this file is the one place that records WHICH symbol the gate has to know about.
REQUIRED_MARKER = "Task_ContinueTaskAfterMessagePrints"
CONTROL_CALL = "_menu_task_active"


def names_used(node: ast.AST) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def main() -> int:
    if not SOURCE.is_file():
        print(f"FAIL  cannot find {SOURCE}")
        return 1
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)

    func = next((n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == "normalize_to_overworld"), None)
    if func is None:
        print("FAIL  normalize_to_overworld not found — the parser cannot see the function")
        return 1

    settled = None
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "settled":
                    settled = node.value
    if settled is None:
        print("FAIL  no `settled = ...` assignment in normalize_to_overworld")
        return 1

    used = names_used(settled)
    checks = []

    # ---- POSITIVE CONTROL first ----
    control_ok = CONTROL_CALL in used
    checks.append((control_ok, f"CONTROL: `settled` consults {CONTROL_CALL}() "
                               f"(known to be present — proves the parser can see the expression)"))
    if not control_ok:
        for ok, label in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print("\n‼ CONTROL FAILED — the parser is not reading the right expression. "
              "A red result below would be meaningless. Fix this script, not the code.")
        return 1

    # ---- the gate itself ----
    gate_names = {n for n in used if "message" in n.lower() or "printing" in n.lower()}
    checks.append((bool(gate_names),
                   f"`settled` consults a message/printing predicate  (found: {sorted(gate_names) or 'NONE'})"))

    checks.append((REQUIRED_MARKER in text,
                   f"{REQUIRED_MARKER} appears in early_game.py at all"))

    # The marker must be reachable from the predicate, not merely mentioned in a comment.
    marker_in_code = any(
        isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value == REQUIRED_MARKER
        for node in ast.walk(tree)
    )
    checks.append((marker_in_code,
                   f"{REQUIRED_MARKER} is a STRING LITERAL in code (not only prose in a comment)"))

    for ok, label in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")

    failed = [label for ok, label in checks if not ok]
    print()
    if failed:
        print(f"RESULT: {len(failed)} FAILED — normalize_to_overworld can still hand off mid-message, "
              f"so a teach right after a WON battle will wedge in BAG_MENU (#24-teachmsgstall).")
        return 1
    print("RESULT: ALL PASS — the message gate is wired into `settled`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
