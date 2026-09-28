r"""GATE — `#24-restockleg` F1 (USER RULING 12, "Restock, then retry"): a basket-only R1 refusal restocks once, then R1
is decided again (2026-09-27).

WHY (`ai-research-notes/2026-09-27-ch24-basket-restock-RECON.md`, a NOTE, adversarially checked): batch run P4r2 entered
the Elite Four, beat Sidney and lost to Phoebe; every re-entry was then refused at R1 on a short basket that was
AFFORDABLE, because nothing restocks inside §Ch24.

  R1  `ch24_should_restock` (PURE): True only when EVERY reason is the basket's, on Ever Grande or in the lobby, and not
      under `POKEBOT_CH24_FAULT_NORESTOCK`; a level shortfall (alone or with the basket), no reason, or off-map ⇒ False.
  R2  WIRING (AST, `prepare_and_open_the_league`): R1's reasons are computed, THEN `ch24_should_restock`, THEN
      `VR.stock_for_the_elite_four(restock)`, THEN the reasons are recomputed, all BEFORE the refusal can raise. And
      STRUCTURALLY inside the restock `if`: the shop, then `stock` re-read from the bag, then `reasons` recomputed from
      THAT `stock`, then recorded (the review proved the text-order check alone passes with the recompute deleted).
  R3  the arm is read in production and registered in 29.
FAULT ARMS (built in; each must FAIL): the NORESTOCK arm (R1); the predicate loosened to "any basket reason" (R1); the
restock call removed (R2); the recompute deleted (R2); the post-restock bag re-read deleted (R2).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_restock.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.story.pokemon_league as PL  # noqa: E402

PL_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "pokemon_league.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_CH24_FAULT_NORESTOCK"
failures: list = []
BASKET = "League basket short: Hyper Potion 26/30, Full Restore 1/3, Revive 2/3"
LEVELS = "4 mōn below the L65 floor — only 2 of 6 at it, RULING 15 needs 4: X"


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def r1(fn, sink=None):
    check(fn([BASKET], True) is True, "R1 the basket as the ONLY reason, on Ever Grande/the lobby ⇒ restock", sink)
    check(fn([LEVELS, BASKET], True) is False, "R1 a level shortfall alongside the basket ⇒ no restock (shopping "
                                               "cannot fix levels)", sink)
    check(fn([LEVELS], True) is False, "R1 a level shortfall alone ⇒ no restock", sink)
    check(fn([], True) is False, "R1 no reason ⇒ no restock", sink)
    check(fn([BASKET], False) is False, "R1 off Ever Grande and the lobby ⇒ no restock (no Mart reachable)", sink)


def _restock_if(fn_node) -> "ast.If | None":
    return next((n for n in ast.walk(fn_node) if isinstance(n, ast.If) and isinstance(n.test, ast.Call)
                 and isinstance(n.test.func, ast.Name) and n.test.func.id == "ch24_should_restock"), None)


def _calls(node, name: str) -> bool:
    """Does `node` contain a call to `name` (a bare name or an attribute)?"""
    return any(isinstance(c, ast.Call) and (getattr(c.func, "id", None) == name or getattr(c.func, "attr", None) == name)
               for c in ast.walk(node))


def _assigns(node, target: str) -> "list[ast.Assign]":
    return [a for a in ast.walk(node) if isinstance(a, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == target for t in a.targets)]


def _is_recompute(a: ast.Assign) -> bool:
    """`reasons = … ch24_readiness_shortfall(left, stock, …)` — the SECOND argument must be the re-read `stock`."""
    return any(isinstance(c, ast.Call) and getattr(c.func, "id", None) == "ch24_readiness_shortfall"
               and len(c.args) >= 2 and isinstance(c.args[0], ast.Name) and c.args[0].id == "left"
               and isinstance(c.args[1], ast.Name) and c.args[1].id == "stock" for c in ast.walk(a.value))


def r2(src: str, sink=None):
    fn_node = next(n for n in ast.walk(ast.parse(src))
                   if isinstance(n, ast.FunctionDef) and n.name == "prepare_and_open_the_league")
    fn = ast.unparse(fn_node)
    i_reasons = fn.find("reasons = ch24_readiness_shortfall(left, stock, party_size=party_size, floor=floor)")
    i_should = fn.find("if ch24_should_restock(reasons")
    i_stock = fn.find("yield from VR.stock_for_the_elite_four(restock)")
    i_again = fn.find("report['readiness_after_restock'] = reasons")
    i_raise = fn.find("§Ch24 R1: REFUSING to enter the Elite Four")
    check(-1 < i_reasons < i_should < i_stock < i_again < i_raise,
          f"R2 reasons → should_restock → stock_for_the_elite_four → recompute → the refusal "
          f"({i_reasons} < {i_should} < {i_stock} < {i_again} < {i_raise})", sink)
    # ⛔ STRUCTURE, not text order (review 2026-09-27: deleting the recompute left every substring above in place and
    # the order check still passed). Inside the restock `if`, IN ORDER: the shop call; `stock` re-read from the bag;
    # `reasons` recomputed from THAT `stock`; then `readiness_after_restock` records it.
    node = _restock_if(fn_node)
    body = node.body if node else []

    def first(pred) -> int:
        return next((i for i, s in enumerate(body) if pred(s)), -1)

    j_shop = first(lambda s: _calls(s, "stock_for_the_elite_four"))
    j_read = first(lambda s: any(_calls(a.value, "bag_healing_stock") for a in _assigns(s, "stock")))
    j_again = first(lambda s: any(_is_recompute(a) for a in _assigns(s, "reasons")))
    j_record = first(lambda s: isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Subscript)
                     and ast.unparse(s.targets[0]) == "report['readiness_after_restock']"
                     and isinstance(s.value, ast.Name) and s.value.id == "reasons")
    check(-1 < j_shop < j_read < j_again < j_record,
          f"R2 inside the restock `if`: shop → `stock` RE-READ from the bag → `reasons` RECOMPUTED from that `stock` → "
          f"recorded ({j_shop} < {j_read} < {j_again} < {j_record})", sink)


class _DropStmt(ast.NodeTransformer):
    """Fault-arm mutation: inside the restock `if`, replace the first statement matching `pred` with `pass`."""

    def __init__(self, pred):
        self.pred, self.hits = pred, 0

    def visit_If(self, node):
        self.generic_visit(node)
        if node is not None and isinstance(node.test, ast.Call) and getattr(node.test.func, "id", None) == "ch24_should_restock":
            for i, s in enumerate(node.body):
                if self.hits == 0 and self.pred(s):
                    node.body[i] = ast.Pass()
                    self.hits += 1
        return node


def _mutate(src: str, pred) -> "tuple[str, int]":
    t = _DropStmt(pred)
    tree = t.visit(ast.parse(src))
    return ast.unparse(ast.fix_missing_locations(tree)), t.hits


def main() -> int:
    print("=" * 92)
    print("GATE — #24-restockleg F1: a basket-only R1 refusal restocks once, then R1 is decided again")
    print("=" * 92)
    os.environ.pop(ARM, None)
    src = PL_SRC.read_text(encoding="utf-8")
    print("\n== R1 the predicate ==")
    r1(PL.ch24_should_restock)
    print("\n== R2 wiring ==")
    r2(src)
    print("\n== R3 the arm ==")
    check(f'environ.get("{ARM}") != "1"' in src and f"`{ARM}`" in REGISTRY.read_text(encoding="utf-8"),
          f"R3 {ARM} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    os.environ[ARM] = "1"
    try:
        r1(PL.ch24_should_restock, sink)
    finally:
        os.environ.pop(ARM, None)
    check(bool(sink), f"FAULT {ARM} FAILS R1 ({len(sink)} caught)")
    node = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "ch24_should_restock")
    seg = ast.get_source_segment(src, node)
    loose, n = re.subn(r"all\(str\(r\)\.startswith\(\"League basket short\"\) for r in reasons\)",
                       'any(str(r).startswith("League basket short") for r in reasons)', seg, count=1)
    check(n == 1, "(fault-arm mutation applied exactly once: the predicate loosened to ANY basket reason)")
    ns: dict = {}
    exec(compile(loose, "<mutated ch24_should_restock>", "exec"), PL.__dict__, ns)  # noqa: S102 - gate fault arm
    sink = []
    r1(ns["ch24_should_restock"], sink)
    check(bool(sink), f"FAULT the loosened predicate FAILS R1 ({len(sink)} caught)")
    call = "            yield from VR.stock_for_the_elite_four(restock)\n"
    check(src.count(call) == 1, "(fault-arm mutation applied exactly once: the restock call removed)")
    sink = []
    r2(src.replace(call, "            pass\n", 1), sink)
    check(bool(sink), f"FAULT the restock call removed FAILS R2 ({len(sink)} caught)")
    # ⛔ The review's own mutation (2026-09-27): the recompute deleted, `readiness_after_restock = reasons` kept — R1
    # would then decide on the STALE pre-restock reasons. The old text-order check PASSED this.
    mutated, n = _mutate(src, lambda s: any(_is_recompute(a) for a in _assigns(s, "reasons")))
    check(n == 1, "(fault-arm mutation applied exactly once: the recompute deleted)")
    sink = []
    r2(mutated, sink)
    check(bool(sink), f"FAULT the recompute deleted FAILS R2 ({len(sink)} caught)")
    # …and the bag not re-read: the recompute would then run on the PRE-restock `stock` and reproduce the refusal.
    mutated, n = _mutate(src, lambda s: any(_calls(a.value, "bag_healing_stock") for a in _assigns(s, "stock")))
    check(n == 1, "(fault-arm mutation applied exactly once: the post-restock bag re-read deleted)")
    sink = []
    r2(mutated, sink)
    check(bool(sink), f"FAULT the post-restock bag re-read deleted FAILS R2 ({len(sink)} caught)")

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
