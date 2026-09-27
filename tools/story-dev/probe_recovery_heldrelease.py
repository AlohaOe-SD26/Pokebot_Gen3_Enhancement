r"""GATE (static) — every Story recovery starts from NO held input (KI-106 / `#27-evgpcwedge`, 2026-09-27).

WHY: `_held_inputs` is Python-side state OR'd into the pad every frame. A navigator abandoned mid-walk by an abort keeps
what it held: navigators have no `finally:`, and §Ch23's `_sampling` doesn't either. MEASURED in batch `#26-batch0926`
(P1r8, 8 badges): B+Up survived a whiteout, and the held Up walked the Ever Grande respawn (27,49) into the Poké Center.
Every `ensure_facing_direction(Down)` then failed, because Emerald reads a held Up first. Five derails ended the run.

  D1  In `StoryMode.run()`, the `except BotModeError` handler that holds BOTH recoveries (it branches on
      `self._whiteout_pending`) calls `context.emulator.reset_held_buttons()` BEFORE that branch. So the whiteout
      recovery AND the derail recovery both start from an empty pad.
  D2  The release is skipped only under `POKEBOT_RECOVERY_FAULT_KEEPHELD`, and that arm is registered in 29.
  D3  It ANNOUNCES the released mask: a `RECOVERY-HELD` `debug_logger.event` sits in the same pre-branch block.
FAULT ARMS (built in; each must FAIL):
  F1  the release deleted;
  F2  the release moved INSIDE the whiteout branch, so only one recovery gets it;
  F3  the release only MENTIONED in a comment. AST reading ignores comments, so a mention cannot pass.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_recovery_heldrelease.py
"""
import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
SM = REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = REPO / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_RECOVERY_FAULT_KEEPHELD"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _is_whiteout_branch(node) -> bool:
    """`if not self._whiteout_pending:` (or `if self._whiteout_pending:`)."""
    if not isinstance(node, ast.If):
        return False
    t = node.test.operand if isinstance(node.test, ast.UnaryOp) else node.test
    return isinstance(t, ast.Attribute) and t.attr == "_whiteout_pending"


def _recovery_handler(tree):
    cls = next((n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StoryMode"), None)
    run = next((n for n in (cls.body if cls else []) if isinstance(n, ast.FunctionDef) and n.name == "run"), None)
    for n in ast.walk(run) if run else []:
        if isinstance(n, ast.ExceptHandler) and getattr(n.type, "id", None) == "BotModeError":
            if any(_is_whiteout_branch(s) for s in n.body):
                return n
    return None


def _calls(nodes, attr) -> bool:
    return any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == attr
               for s in nodes for c in ast.walk(s))


def _consts(nodes) -> str:
    return " ".join(c.value for s in nodes for c in ast.walk(s)
                    if isinstance(c, ast.Constant) and isinstance(c.value, str))


def gate(src: str, sink=None) -> None:
    h = _recovery_handler(ast.parse(src))
    check(h is not None, "D1 found StoryMode.run()'s recovery handler (except BotModeError + the whiteout branch)", sink)
    if h is None:
        return
    i = next(k for k, s in enumerate(h.body) if _is_whiteout_branch(s))
    pre = h.body[:i]
    check(_calls(pre, "reset_held_buttons"),
          "D1 `reset_held_buttons()` is called BEFORE the whiteout/derail branch (both recoveries get it)", sink)
    check(ARM in _consts(pre), f"D2 the release is gated only by `{ARM}` (read in the same pre-branch block)", sink)
    check(f"`{ARM}`" in REGISTRY.read_text(encoding="utf-8"), f"D2 `{ARM}` is registered in 29", sink)
    check("RECOVERY-HELD" in _consts(pre) and _calls(pre, "event"),
          "D3 the released mask is ANNOUNCED (`RECOVERY-HELD` debug_logger.event, pre-branch)", sink)


def main() -> int:
    print("=" * 92)
    print("GATE (static) — every Story recovery starts from NO held input (KI-106 / #27-evgpcwedge)")
    print("=" * 92)
    src = SM.read_text(encoding="utf-8")
    gate(src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    call = "else context.emulator.reset_held_buttons())"
    check(src.count(call) == 1, "(fault-arm anchor present exactly once)")
    f1: list = []
    gate(src.replace(call, "else 0)", 1), f1)
    check(bool(f1), f"F1 the release deleted FAILS the gate ({len(f1)})")

    # F2: move the release into the whiteout branch — the pre-branch block loses it.
    f2: list = []
    anchor = "                if not self._whiteout_pending:\n"
    s2 = src.replace(call, "else 0)", 1).replace(
        anchor, anchor + "                    context.emulator.reset_held_buttons()\n", 1)
    gate(s2, f2)
    check(bool(f2), f"F2 the release moved INSIDE one recovery branch FAILS the gate ({len(f2)})")

    # F3: only a COMMENT mentions it.
    f3: list = []
    gate(src.replace(call, "else 0)  # context.emulator.reset_held_buttons()", 1), f3)
    check(bool(f3), f"F3 a comment-only mention FAILS the gate ({len(f3)})")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
