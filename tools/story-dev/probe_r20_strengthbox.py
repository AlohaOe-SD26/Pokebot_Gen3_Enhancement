r"""GATE — RULING 20 Phase 1, increment B (Strength): box-first for `ensure_strength_learner` (2026-09-27).

WHY (recon note `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`): `ensure_strength_learner` searched the PARTY
only. With the only HM04 learner in the PC it raised "no party member can learn HM04" and the Magma Hideout chapter
could not open 1F, although the run owned a learner. Since increment A, the required make-room can box that learner.

  S1  `boxed_hm_learner_pids(item, avoid=...)` ranks a mon that knows the move first, then a mon that cannot learn
      `avoid` (HM07 for a land HM, `#24-hm07funnel`), then level. `avoid=None` keeps the old order.
  S2  `ensure_strength_learner` behaviour, collaborators stubbed:
      - a party learner exists ⇒ it is taught, the box is never used;
      - no party learner, a boxed one, centres offered ⇒ ONE withdraw of the HEAD PID at those centres, then the
        withdrawn mon is taught; the box order was asked with avoid=HM07;
      - the withdrawn mon already knows Strength ⇒ no teach;
      - no centres (the in-hideout caller) ⇒ a refusal that NAMES the boxed PID, no withdraw;
      - `POKEBOT_HMPCFIRST_FAULT=skipfix` ⇒ refusal, no withdraw;
      - the withdraw does not land ⇒ refusal, no teach;
      - the party already knows Strength ⇒ nothing is called.
  S3  WIRING (AST): the heal-stop caller passes `heal_centers=(center,)`; the in-hideout caller passes none.
  S4  `POKEBOT_R20_FAULT_NOLANDPREF` is read in production and registered in 29.
FAULT ARMS (built in; each must FAIL): skipfix (S2's box-first case), NOLANDPREF (S2's avoid check), the heal-stop
caller without centres (S3), the in-hideout caller given centres (S3).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_strengthbox.py
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.items as ITEMS  # noqa: E402
import modules.story.early_game as EG  # noqa: E402
import modules.story.pc_trip as PT  # noqa: E402
from modules.modes import BotModeError  # noqa: E402

EG_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
PREF_ARM = "POKEBOT_R20_FAULT_NOLANDPREF"
SKIP_ARM = "POKEBOT_HMPCFIRST_FAULT"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def item(name):
    return types.SimpleNamespace(name=name, tm_hm_move=lambda: types.SimpleNamespace(
        name={"HM04": "Strength", "HM07": "Waterfall"}.get(name, name)))


def mon(pid, level, learns=("HM04",), moves=("Tackle",)):
    return types.SimpleNamespace(
        personality_value=pid, level=level, is_egg=False,
        moves=[types.SimpleNamespace(move=types.SimpleNamespace(name=n)) for n in moves],
        species=types.SimpleNamespace(name=f"M{pid:X}", can_learn_tm_hm=lambda it, _l=learns: it.name in _l))


def s1(sink=None):
    saved = PT.box_views
    swampert, sceptile = mon(0xA1, 50, ("HM04", "HM07")), mon(0xA2, 44)
    knower = mon(0xA3, 30, ("HM04", "HM07"), moves=("Strength",))
    try:
        PT.box_views = lambda: ([], [swampert, sceptile])
        pref = EG.boxed_hm_learner_pids(item("HM04"), avoid=item("HM07"))
        plain = EG.boxed_hm_learner_pids(item("HM04"))
        PT.box_views = lambda: ([], [sceptile, knower])
        known = EG.boxed_hm_learner_pids(item("HM04"), avoid=item("HM07"))
    finally:
        PT.box_views = saved
    check(pref == [0xA2, 0xA1], f"S1 avoid=HM07: the HM07-incapable L44 ranks before the HM07-capable L50 ({pref})", sink)
    check(plain == [0xA1, 0xA2], f"S1 avoid=None: the old level order is unchanged ({plain})", sink)
    check(known == [0xA3, 0xA2], f"S1 a mon that already knows Strength still ranks first ({known})", sink)


def s2(sink=None):
    """Drive the REAL ensure_strength_learner with its collaborators stubbed; return nothing, check inline."""
    names = ("_party_knows_strength", "land_hm_learner_slot", "boxed_hm_learner_pids", "_withdraw_hm_learner",
             "get_party", "teach_hm_move", "_ch14_say")
    saved = {n: getattr(EG, n) for n in names}
    saved_items = (ITEMS.get_item_bag, ITEMS.get_item_by_name)
    st: dict = {}

    def knows():
        return any(any(l.move.name == "Strength" for l in m.moves) for m in st["party"] if m is not None)

    def land(_hm):
        return next((i for i, m in enumerate(st["party"]) if m.species.can_learn_tm_hm(item("HM04"))), None)

    def boxed(_hm, avoid=None):
        st["avoid"].append(getattr(avoid, "name", None))
        return [p for p in st["box"]]

    def withdraw(_hm, pids, centres):
        st["withdraws"].append((list(pids), tuple(centres)))
        if st["lands"]:
            st["party"].append(st["box_mons"][pids[0]])
        yield

    def teach(_hm, slot):
        st["teaches"].append(st["party"][slot].personality_value)
        st["party"][slot].moves.append(types.SimpleNamespace(move=types.SimpleNamespace(name="Strength")))
        yield

    EG._party_knows_strength, EG.land_hm_learner_slot, EG.boxed_hm_learner_pids = knows, land, boxed
    EG._withdraw_hm_learner, EG.get_party, EG.teach_hm_move = withdraw, lambda: st["party"], teach
    EG._ch14_say = lambda *_a, **_k: None
    ITEMS.get_item_bag = lambda: types.SimpleNamespace(tms_hms=[types.SimpleNamespace(item=item("HM04"))])
    ITEMS.get_item_by_name = item

    def run(party, box, centres, lands=True):
        st.update(party=list(party), box=list(box), lands=lands, avoid=[], withdraws=[], teaches=[],
                  box_mons={0xB1: mon(0xB1, 44), 0xB2: mon(0xB2, 50, ("HM04", "HM07")),
                            0xB3: mon(0xB3, 40, moves=("Strength",))})
        raised = None
        try:
            for _ in EG.ensure_strength_learner(heal_centers=centres):
                pass
        except BotModeError as error:
            raised = str(error)
        return raised

    nolearn = [mon(1, 20, ()), mon(2, 30, ())]
    try:
        r = run([mon(1, 20, ()), mon(9, 40)], [0xB1], ("C",))
        check(r is None and st["withdraws"] == [] and st["teaches"] == [9],
              f"S2 a party learner exists ⇒ it is taught, no withdraw ({st['withdraws']}, {st['teaches']})", sink)
        r = run(nolearn, [0xB1, 0xB2], ("C",))
        check(r is None and st["withdraws"] == [([0xB1], ("C",))] and st["teaches"] == [0xB1],
              f"S2 no party learner + boxed + centres ⇒ ONE withdraw of the head PID, then it is taught "
              f"({st['withdraws']}, {st['teaches']}, raised={r})", sink)
        check(st["avoid"] == ["HM07"], f"S2 ... the box order was asked with avoid=HM07 ({st['avoid']})", sink)
        r = run(nolearn, [0xB3, 0xB1], ("C",))
        check(r is None and st["withdraws"] == [([0xB3], ("C",))] and st["teaches"] == [],
              f"S2 the withdrawn mon already knows Strength ⇒ no teach ({st['teaches']})", sink)
        r = run(nolearn, [0xB1], ())
        check(r is not None and "000000B1" in r and st["withdraws"] == [],
              f"S2 no centres (the in-hideout caller) ⇒ a refusal naming the boxed PID, no withdraw ({r!r})", sink)
        r = run(nolearn, [0xB1], ("C",), lands=False)
        check(r is not None and st["teaches"] == [] and len(st["withdraws"]) == 1,
              f"S2 the withdraw does not land ⇒ a refusal, no teach ({r!r})", sink)
        r = run([mon(1, 20, (), moves=("Strength",))], [0xB1], ("C",))
        check(r is None and st["withdraws"] == [] and st["teaches"] == [] and st["avoid"] == [],
              "S2 the party already knows Strength ⇒ nothing is called", sink)
        os.environ[SKIP_ARM] = "skipfix"
        try:
            r = run(nolearn, [0xB1], ("C",))
        finally:
            os.environ.pop(SKIP_ARM, None)
        check(r is not None and st["withdraws"] == [],
              f"S2 POKEBOT_HMPCFIRST_FAULT=skipfix ⇒ a refusal, no withdraw ({r!r})", sink)
    finally:
        for n, f in saved.items():
            setattr(EG, n, f)
        ITEMS.get_item_bag, ITEMS.get_item_by_name = saved_items


def s3(src: str, sink=None):
    def body(name):
        return ast.unparse(next(n for n in ast.walk(ast.parse(src))
                                if isinstance(n, ast.FunctionDef) and n.name == name))

    door, hideout = body("travel_to_magma_hideout_door"), body("open_magma_hideout_1f")
    check("yield from ensure_strength_learner(heal_centers=(center,))" in door,
          "S3 the heal-stop caller (travel_to_magma_hideout_door) offers the centre it stands next to", sink)
    check("yield from ensure_strength_learner()" in hideout and "heal_centers" not in hideout,
          "S3 the in-hideout caller (open_magma_hideout_1f) stays party-only", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 20 Phase 1 (B): box-first Strength")
    print("=" * 92)
    for a in (PREF_ARM, SKIP_ARM):
        os.environ.pop(a, None)
    eg = EG_SRC.read_text(encoding="utf-8")
    print("\n== S1 the box order ==")
    s1()
    print("\n== S2 behaviour (collaborators stubbed) ==")
    s2()
    print("\n== S3 wiring ==")
    s3(eg)
    print("\n== S4 the arm ==")
    check(f'environ.get("{PREF_ARM}") != "1"' in eg and f"`{PREF_ARM}`" in REGISTRY.read_text(encoding="utf-8"),
          f"S4 {PREF_ARM} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    for arm, val in ((SKIP_ARM, "skipfix"), (PREF_ARM, "1")):
        sink: list = []
        os.environ[arm] = val
        try:
            s2(sink)
        finally:
            os.environ.pop(arm, None)
        check(bool(sink), f"FAULT {arm}={val} FAILS S2 ({len(sink)} caught)")
    for label, pat, rep in (
            ("the heal-stop caller without centres", r"ensure_strength_learner\(heal_centers=\(center,\)\)",
             "ensure_strength_learner()"),
            ("the in-hideout caller given centres",
             r"(    # site; the refusal here still names any boxed learner\.\n    yield from )ensure_strength_learner\(\)",
             r"\1ensure_strength_learner(heal_centers=(PokemonCenter.LavaridgeTown,))")):
        mutated, n = re.subn(pat, rep, eg, count=1)
        check(n == 1, f"(fault-arm mutation applied exactly once: {label})")
        sink = []
        s3(mutated, sink)
        check(bool(sink), f"FAULT {label} FAILS S3 ({len(sink)} caught)")

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
