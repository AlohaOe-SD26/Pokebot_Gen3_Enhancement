r"""GATE — USER RULING 16: §Ch23 leg 11 buys only the MISSING League-basket quantities (`#26-ch23money`).

WHY (2026-09-26): 3 of 3 organic runs that reached leg 11 were refused on money, and leg 11 priced and bought the
WHOLE ₽54,300 basket even when some of it was already in the bag. The user ruled "buy only what's missing" — the same
end state by item name, NOT a thinner basket (that 2026-09-05 ruling stands).

  B1  the item data prices the full `LEAGUE_BASKET` at exactly `LEAGUE_MIN_MONEY` (₽54,300);
  B2  `basket_to_buy` (PURE): empty bag ⇒ the whole basket; a partial bag ⇒ only the missing quantities, in the
      basket's own order (largest line first); a full or over-full bag ⇒ []; unrelated items change nothing;
  B3  leg 11 buys `to_buy` (never the raw `LEAGUE_BASKET`), checks money against `need_money`, never opens the Mart
      menu when nothing is missing, and still verifies the WHOLE basket afterwards; the `FULLBASKET` arm is read in
      code and registered.
FAULT ARMS: a `basket_to_buy` that returns the whole basket regardless (the pre-ruling behaviour) FAILS B2; a leg
that buys `LEAGUE_BASKET` FAILS B3.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch23_basket_buy.py
"""
from __future__ import annotations

import ast
import io
import sys
import tokenize
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.story import victory_road as VR  # noqa: E402

SRC = SANDBOX / "modules" / "story" / "victory_road.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def b2(to_buy, sink=None):
    full = list(VR.LEAGUE_BASKET)
    check(to_buy({}) == full, "B2 empty bag ⇒ the whole basket, in order", sink)
    r = to_buy({"Hyper Potion": 5})
    check(r == [("Hyper Potion", 25), ("Full Restore", 3), ("Full Heal", 8), ("Revive", 3)],
          f"B2 5 Hyper Potions carried ⇒ buy 25 (+ the other lines): {r}", sink)
    r = to_buy({"Hyper Potion": 30, "Full Restore": 1, "Full Heal": 8, "Revive": 5})
    check(r == [("Full Restore", 2)], f"B2 only Full Restore short ⇒ buy exactly 2: {r}", sink)
    check(to_buy(dict(full)) == [], "B2 a full basket ⇒ nothing to buy", sink)
    check(to_buy({"Hyper Potion": 37, "Full Restore": 3, "Full Heal": 18, "Revive": 3}) == [],
          "B2 an over-full basket (the L75 fixture's 37/3/18/3) ⇒ nothing to buy", sink)
    check(to_buy({"Potion": 9, "Nugget": 2}) == full, "B2 unrelated items change nothing", sink)


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def b3(src, sink=None):
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "stock_for_the_elite_four")
    code = _strip_comments(ast.get_source_segment(src, fn) or "")
    check("for name, qty in to_buy]" in code and "for name, qty in LEAGUE_BASKET])" not in code,
          "B3 leg 11 buys `to_buy`, never the raw LEAGUE_BASKET", sink)
    check("< need_money" in code and "gap = need_money - have" in code, "B3 the money check uses need_money", sink)
    check("elif not to_buy:" in code, "B3 nothing missing ⇒ the Mart menu is never opened", sink)
    check("missing = {name: qty for name, qty in LEAGUE_BASKET if after.get(name, 0) < qty}" in code,
          "B3 the WHOLE basket is still verified afterwards", sink)
    check('_fault("FULLBASKET")' in code and '"FULLBASKET": "POKEBOT_CH23_FAULT_FULLBASKET"' in src
          and "`POKEBOT_CH23_FAULT_FULLBASKET`" in REGISTRY.read_text(encoding="utf-8"),
          "B3 the FULLBASKET arm is read in code, in FAULT_ARMS, and registered", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 16: §Ch23 leg 11 buys only what is missing")
    print("=" * 92)
    src = SRC.read_text(encoding="utf-8")
    print("\n== B1 prices ==")
    check(VR.basket_cost(VR.LEAGUE_BASKET) == VR.LEAGUE_MIN_MONEY,
          f"B1 the item data prices the full basket at ₽{VR.basket_cost(VR.LEAGUE_BASKET):,} == "
          f"LEAGUE_MIN_MONEY ₽{VR.LEAGUE_MIN_MONEY:,}")
    check(VR.basket_cost(VR.basket_to_buy({"Hyper Potion": 5})) == VR.LEAGUE_MIN_MONEY - 5 * 1200,
          "B1 carrying 5 Hyper Potions saves exactly ₽6,000")
    print("\n== B2 the missing quantities (pure) ==")
    b2(VR.basket_to_buy)
    print("\n== B3 the leg ==")
    b3(src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    b2(lambda stock: list(VR.LEAGUE_BASKET), sink)
    check(bool(sink), f"FAULT the pre-ruling 'always the whole basket' FAILS B2 ({len(sink)} caught)")
    sink = []
    b3(src.replace("for name, qty in to_buy]),", "for name, qty in LEAGUE_BASKET]),"), sink)
    check(bool(sink), f"FAULT a leg that buys the raw LEAGUE_BASKET FAILS B3 ({len(sink)} caught)")

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
