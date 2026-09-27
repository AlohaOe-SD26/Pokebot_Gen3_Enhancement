r"""GATE — the story's HM teach must PROVE the bag cursor is on the HM before pressing A (`#26-hmwrongitem`, 2026-09-26).

WHY: MEASURED in the live batch — 9 of 87 HM teaches used HM06 Rock Smash instead of HM03 / HM07: a permanent,
unforgettable slot on the Surf/Waterfall target, a 9,000-frame hard cap and a derail each time. Upstream
`scroll_to_item_in_bag` computes the slot from the TM/HM pocket as stored, and the game SORTS that pocket when the bag
opens (proven by the A/B on `norman_done.ss1`, whose stored pocket is unsorted — see the GRADED note).

  V1  `early_game.teach_hm_move`'s DEFAULT path scrolls with `pokemon_league.scroll_to_tm_verified(item)`; the upstream
      `scroll_to_item_in_bag(item)` appears only under the skip-the-fix arm `POKEBOT_HMTEACH_FAULT_UNVERIFIED`, which is
      registered in 29.
  V2  a REFUSAL from the verified scroll closes the bag (a bounded B loop that stops at a controllable overworld) and
      RE-RAISES — the derail recovery cannot close a bag, so a refusal that left it open would wedge the run.
  V3  the verified scroll itself still refuses to press A on a wrong item (its BotModeError on a failed correction) and
      verifies against the LIVE pocket (`get_item_bag().tms_hms`), not the stored order.
FAULT ARMS (built in): the default path reverted to the upstream scroll (V1); the refusal handler without its settle-and-check
loop (V2).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_hmteach_itemverify.py
"""
from __future__ import annotations

import ast
import io
import pathlib
import sys
import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
EG = ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
PL = ROOT / "sandbox-pokebot" / "modules" / "story" / "pokemon_league.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _strip(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def _func(src: str, name: str):
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def v1_v2(src: str, sink=None):
    fn = _func(src, "teach_hm_move")
    body = _strip(ast.get_source_segment(src, fn) or "") if fn else ""
    arm = "POKEBOT_HMTEACH_FAULT_UNVERIFIED"
    i_if = body.find(f'os.environ.get("{arm}") == "1"')
    i_old = body.find("yield from scroll_to_item_in_bag(item)")
    i_else = body.find("else:", max(i_if, 0))
    i_new = body.find("yield from scroll_to_tm_verified(item)")
    check(fn is not None and 0 <= i_if < i_old < i_else < i_new,
          "V1 the default path uses scroll_to_tm_verified; the upstream scroll only under the arm", sink)
    check(body.count("yield from scroll_to_item_in_bag(item)") == 1,
          "V1 … and the upstream scroll appears exactly ONCE (the arm)", sink)
    check(f"`{arm}`" in REGISTRY.read_text(encoding="utf-8"), f"V1 {arm} is registered in 29", sink)
    handler = None
    if fn is not None:
        for node in ast.walk(fn):
            if isinstance(node, ast.Try) and any("scroll_to_tm_verified" in (ast.get_source_segment(src, s) or "")
                                                 for s in node.body):
                handler = node.handlers[0] if node.handlers else None
    hsrc = _strip(ast.get_source_segment(src, handler) or "") if handler else ""
    check(handler is not None and "BotModeError" in hsrc and 'press_button("B")' in hsrc and "for _ in range(" in hsrc
          and "GameState.OVERWORLD" in hsrc and hsrc.rstrip().endswith("raise"),
          "V2 a refusal closes the bag (bounded B loop to a controllable overworld) and RE-RAISES", sink)
    check("yield from wait_until_truly_controllable()" in hsrc and "could not close the bag" in hsrc,
          "V2 … then SETTLES and raises a DISTINCT error if the menus are still open (the function's own guarantee)", sink)


def v3(src: str, sink=None):
    fn = _func(src, "scroll_to_tm_verified")
    body = _strip(ast.get_source_segment(src, fn) or "") if fn else ""
    check("get_item_bag().tms_hms" in body and "raise BotModeError(" in body and "for _ in range(" in body,
          "V3 the verified scroll reads the LIVE pocket, corrects in a bounded loop, and refuses on failure", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — the HM teach proves the bag cursor is on the HM before pressing A (#26-hmwrongitem)")
    print("=" * 92)
    eg = EG.read_text(encoding="utf-8")
    v1_v2(eg)
    v3(PL.read_text(encoding="utf-8"))

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    reverted = eg.replace("            yield from scroll_to_tm_verified(item)\n",
                          "            yield from scroll_to_item_in_bag(item)\n", 1)
    v1_v2(reverted, sink)
    check(bool(sink) and reverted != eg, f"FAULT the default path reverted to the upstream scroll FAILS V1 ({len(sink)})")
    sink = []
    no_close = eg.replace("            yield from wait_until_truly_controllable()\n"
                          "            if get_game_state() is not GameState.OVERWORLD or _menu_task_active():\n", "            if False:\n", 1)
    v1_v2(no_close, sink)
    check(bool(sink) and no_close != eg, f"FAULT a refusal handler without its settle-and-check FAILS V2 ({len(sink)})")

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
