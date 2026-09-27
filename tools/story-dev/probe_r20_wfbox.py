r"""GATE — RULING 20 Phase 1, increment B (Waterfall): box-first inside `ensure_waterfall_learner` (2026-09-27).

WHY (recon note `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`): the generic PC-first gate
(`hm_learner_slot(item) is None`) never fires on the measured 8-badge shape: a SATURATED Wailmer/Swampert is
compatible, so the gate is False, and `ensure_waterfall_learner` raised although a usable learner sat in the PC.

  W1  `_boxed_waterfall_learners`: keeps a boxed mon that knows Waterfall or has a non-HM slot to spend; drops a
      SATURATED one; keeps `boxed_hm_learner_pids`' order.
  W2  `ensure_waterfall_learner` behaviour, collaborators stubbed:
      - a spendable party learner ⇒ taught, the box is never used;
      - a saturated party learner, a usable boxed one, centres offered ⇒ ONE withdraw of the head PID, then it is taught;
      - the withdrawn mon already knows Waterfall ⇒ no teach;
      - no centres ⇒ a refusal naming the boxed PID; `POKEBOT_HMPCFIRST_FAULT=skipfix` ⇒ a refusal, no withdraw;
      - nothing usable boxed ⇒ a refusal that says so; no compatible member at all ⇒ the refusal says THAT, not
        "four HM moves".
  W3  `_withdraw_hm_learner` returns and names the slot of the PID it was asked for, even when a higher-level
      compatible mon is already in the party (it used to return `hm_learner_slot`, the level ranking).
  W4  WIRING (AST): the Segment 22b caller offers Sootopolis.
FAULT ARMS (built in; each must FAIL): skipfix (W2), the caller without centres (W4), the old `hm_learner_slot`
identity in `_withdraw_hm_learner` (W3, by source mutation + exec).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_wfbox.py
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
import modules.story.victory_road as VR  # noqa: E402
from modules.modes import BotModeError  # noqa: E402

EG_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
SKIP_ARM = "POKEBOT_HMPCFIRST_FAULT"
HMS = {"Cut", "Fly", "Surf", "Strength", "Flash", "Rock Smash", "Waterfall", "Dive"}
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def learned(name):
    return types.SimpleNamespace(move=types.SimpleNamespace(
        name=name, tm_hm=types.SimpleNamespace(name="HM0x") if name in HMS else None))


def mon(pid, level, moves, compat=True):
    return types.SimpleNamespace(
        personality_value=pid, level=level, is_egg=False, moves=[learned(n) for n in moves],
        species=types.SimpleNamespace(name=f"M{pid:X}", can_learn_tm_hm=lambda _it, _c=compat: _c))


HM07 = types.SimpleNamespace(name="HM07", tm_hm_move=lambda: types.SimpleNamespace(name="Waterfall"))
SAT = ("Dive", "Surf", "Cut", "Flash")


def is_hm(l):
    return l.move.tm_hm is not None


def w1(sink=None):
    saved = (EG.boxed_hm_learner_pids, PT.box_views)
    box = [mon(0xC1, 40, SAT), mon(0xC2, 30, ("Tackle",)), mon(0xC3, 20, ("Waterfall", "Surf", "Dive", "Cut"))]
    try:
        EG.boxed_hm_learner_pids = lambda _it, avoid=None: [0xC3, 0xC1, 0xC2]
        PT.box_views = lambda: ([], box)
        got = VR._boxed_waterfall_learners(HM07, is_hm)
    finally:
        EG.boxed_hm_learner_pids, PT.box_views = saved
    check(got == [0xC3, 0xC2], f"W1 keeps the knower and the spendable one, drops the saturated L40, keeps order ({got})",
          sink)


def w2(sink=None):
    saved_vr = (VR.get_party, VR.field_move_carriers, VR._boxed_waterfall_learners)
    saved_eg = (EG._withdraw_hm_learner, EG.teach_hm_move)
    saved_items = ITEMS.get_item_bag
    st: dict = {}

    def carriers():
        k = next((m for m in st["party"] if any(l.move.name == "Waterfall" for l in m.moves)), None)
        return {"Waterfall": None if k is None else k.personality_value}

    def withdraw(_hm, pids, centres):
        st["withdraws"].append((list(pids), tuple(centres)))
        if st["lands"]:
            st["party"].append(st["box_mons"][pids[0]])
        yield

    def teach(_hm, slot):
        st["teaches"].append(st["party"][slot].personality_value)
        st["party"][slot].moves = [learned("Waterfall")] + st["party"][slot].moves[1:]
        yield

    VR.get_party, VR.field_move_carriers = (lambda: st["party"]), carriers
    VR._boxed_waterfall_learners = lambda _hm, _is: list(st["box"])
    EG._withdraw_hm_learner, EG.teach_hm_move = withdraw, teach
    ITEMS.get_item_bag = lambda: types.SimpleNamespace(tms_hms=[types.SimpleNamespace(item=HM07)])

    def run(party, box, centres, lands=True):
        st.update(party=list(party), box=list(box), lands=lands, withdraws=[], teaches=[],
                  box_mons={0xB1: mon(0xB1, 30, ("Tackle",)), 0xB3: mon(0xB3, 25, ("Waterfall",))})
        try:
            for _ in VR.ensure_waterfall_learner(heal_centers=centres):
                pass
        except BotModeError as error:
            return str(error)
        return None

    sat = [mon(1, 40, SAT), mon(2, 19, ("Tackle",), compat=False)]
    try:
        r = run([mon(1, 40, ("Dive", "Surf", "Water Gun", "Rollout")), mon(2, 19, ("Tackle",), False)], [0xB1], ("C",))
        check(r is None and st["withdraws"] == [] and st["teaches"] == [1],
              f"W2 a spendable party learner ⇒ taught, no withdraw ({st['withdraws']}, {st['teaches']})", sink)
        r = run(sat, [0xB1], ("C",))
        check(r is None and st["withdraws"] == [([0xB1], ("C",))] and st["teaches"] == [0xB1],
              f"W2 a SATURATED party learner + a usable boxed one ⇒ ONE withdraw of the head, then it is taught "
              f"({st['withdraws']}, {st['teaches']}, raised={r!r})", sink)
        r = run([mon(1, 40, SAT)], [0xB3, 0xB1], ("C",))
        check(r is None and st["withdraws"] == [([0xB3], ("C",))] and st["teaches"] == [],
              f"W2 the withdrawn mon already knows Waterfall ⇒ no teach ({st['teaches']})", sink)
        r = run([mon(1, 40, SAT)], [0xB1], ())
        check(r is not None and "000000B1" in r and st["withdraws"] == [],
              f"W2 no centres ⇒ a refusal naming the boxed PID, no withdraw ({r!r:.120})", sink)
        r = run([mon(1, 40, SAT)], [], ("C",))
        check(r is not None and "no usable Waterfall learner" in r and "four HM moves" in r and st["withdraws"] == [],
              f"W2 nothing usable boxed ⇒ a refusal that says so, and says saturated ({r!r:.120})", sink)
        r = run([mon(2, 19, ("Tackle",), compat=False)], [], ("C",))
        check(r is not None and "no party member is compatible" in r and "four HM moves" not in r,
              f"W2 no compatible member at all ⇒ the refusal says THAT ({r!r:.120})", sink)
        os.environ[SKIP_ARM] = "skipfix"
        try:
            r = run([mon(1, 40, SAT)], [0xB1], ("C",))
        finally:
            os.environ.pop(SKIP_ARM, None)
        check(r is not None and st["withdraws"] == [],
              f"W2 POKEBOT_HMPCFIRST_FAULT=skipfix ⇒ a refusal, no withdraw ({r!r:.80})", sink)
    finally:
        VR.get_party, VR.field_move_carriers, VR._boxed_waterfall_learners = saved_vr
        EG._withdraw_hm_learner, EG.teach_hm_move = saved_eg
        ITEMS.get_item_bag = saved_items


def w3(fn, sink=None):
    """`fn` is `_withdraw_hm_learner` (or a mutated copy). A higher-level compatible mon is already in the party."""
    import modules.modes.util.higher_level_actions as HLA

    saved = (EG.get_party, HLA.heal_in_pokemon_center)
    party = [mon(0xA0, 40, SAT)]

    def heal(_c):
        party.append(mon(0xB1, 30, ("Tackle",)))
        yield

    mode = types.SimpleNamespace()
    saved_mode = EG.context.bot_mode_instance if hasattr(EG.context, "bot_mode_instance") else None
    try:
        EG.get_party, HLA.heal_in_pokemon_center = (lambda: party), heal
        EG.context.bot_mode_instance = mode
        gen = fn(types.SimpleNamespace(name="HM07", tm_hm_move=lambda: types.SimpleNamespace(name="Waterfall")),
                 [0xB1], ("C",))
        slot = None
        try:
            while True:
                next(gen)
        except StopIteration as stop:
            slot = stop.value
    finally:
        EG.get_party, HLA.heal_in_pokemon_center = saved
        EG.context.bot_mode_instance = saved_mode
    check(slot == 1, f"W3 _withdraw_hm_learner returns the slot of the PID it was asked for (1), not the "
                     f"higher-level compatible mon's (0) — got {slot}", sink)
    check(getattr(mode, "_wanted_hm_learner_pids", None) == set(), "W3 ... and it disarms the hook afterwards", sink)


def w4(sm: str, sink=None):
    check("yield from ensure_waterfall_learner(heal_centers=(_PC22b.SootopolisCity,))" in ast.unparse(ast.parse(sm)),
          "W4 the Segment 22b caller offers Sootopolis", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 20 Phase 1 (B): box-first Waterfall")
    print("=" * 92)
    os.environ.pop(SKIP_ARM, None)
    sm, eg = SM_SRC.read_text(encoding="utf-8"), EG_SRC.read_text(encoding="utf-8")
    print("\n== W1 the boxed-learner filter ==")
    w1()
    print("\n== W2 behaviour (collaborators stubbed) ==")
    w2()
    print("\n== W3 the withdraw's identity ==")
    w3(EG._withdraw_hm_learner)
    print("\n== W4 wiring ==")
    w4(sm)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    os.environ[SKIP_ARM] = "skipfix"
    try:
        w2(sink)
    finally:
        os.environ.pop(SKIP_ARM, None)
    check(bool(sink), f"FAULT {SKIP_ARM}=skipfix FAILS W2 ({len(sink)} caught)")
    mutated, n = re.subn(r"ensure_waterfall_learner\(heal_centers=\(_PC22b\.SootopolisCity,\)\)",
                         "ensure_waterfall_learner()", sm, count=1)
    check(n == 1, "(fault-arm mutation applied exactly once: the caller without centres)")
    sink = []
    w4(mutated, sink)
    check(bool(sink), f"FAULT the caller without centres FAILS W4 ({len(sink)} caught)")
    # The old identity: rebuild `_withdraw_hm_learner` from source with `hm_learner_slot(item)` restored.
    fn_node = next(x for x in ast.walk(ast.parse(eg)) if isinstance(x, ast.FunctionDef) and x.name == "_withdraw_hm_learner")
    src = ast.get_source_segment(eg, fn_node)
    old, n = re.subn(r"slot = next\(\(i for i, m in enumerate\(get_party\(\)\)\s*if m is not None and wanted and "
                     r"m\.personality_value == wanted\[0\]\), None\)", "slot = hm_learner_slot(item)", src, count=1)
    check(n == 1, "(fault-arm mutation applied exactly once: the old hm_learner_slot identity)")
    ns: dict = {}
    exec(compile(old, "<mutated _withdraw_hm_learner>", "exec"), EG.__dict__, ns)  # noqa: S102 - gate fault arm
    sink = []
    w3(ns["_withdraw_hm_learner"], sink)
    check(bool(sink), f"FAULT the old hm_learner_slot identity FAILS W3 ({len(sink)} caught)")

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
