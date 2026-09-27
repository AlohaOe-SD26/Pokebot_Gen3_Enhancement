r"""GATE — RULING 20 Phase 1, increment B (Fly site) + USER RULING 21 (the Fly swap), 2026-09-27.

WHY (recon `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`, site "fly"; the interim read of `#27-batch0927`): the
one run that reached §Ch24 ended on "nobody in the party can learn Fly" while a Wingull sat in its PC. The only PC on
the plateau is the League lobby's, at (6,1), where the standard stand tile (10,2) is a guard's tile.

  F1  `pc_trip.pc_stand_for`: the lobby -> (6,2)/Up; any other map -> (10,2)/Up; `POKEBOT_R20_FAULT_LOBBYSTAND` -> (10,2)
      everywhere. No PC walk in pc_trip still aims at the bare constant.
  F2  `_boxed_fly_learners`: keeps a knower and a mon `_fly_teach_plan` can teach; drops a saturated one.
  F3  `ch24_trainees_below_floor` leaves the recorded carrier out; R1's head-count (AST) does too.
  F4  `restore_ch24_fighters`: nothing recorded -> no-op; a swap that lands -> PASS and the record is cleared; the swap
      skipped (`POKEBOT_R20_FAULT_NOSWAPBACK`) or not landing -> REFUSES by name.
  F5  `ensure_fly_learner` (collaborators stubbed): a party learner -> taught, no lobby; no party learner + a boxed one ->
      ONE lobby withdraw of the head, the swap recorded (fighters, carrier, boxed fighter), then the teach; a boxed
      KNOWER -> no teach; `POKEBOT_R20_FAULT_NOFLYBOX` -> no lobby, `no_learner`.
  F6  WIRING (AST): `prepare_and_open_the_league` calls `restore_ch24_fighters` after `E1-INSIDE` and before the guard
      talk; `story_mode` resets `_ch24_fly_swap` per run.
FAULT ARMS (built in; each must FAIL): NOFLYBOX (F5), NOSWAPBACK (F4), LOBBYSTAND (F1), the carrier exclusion removed
(F3), the swap-back moved after the guard talk (F6).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r20_flybox.py
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

import modules.story.early_game as EG  # noqa: E402
import modules.story.pc_trip as PT  # noqa: E402
import modules.story.pokemon_league as PL  # noqa: E402
from modules.modes import BotModeError  # noqa: E402

PT_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "pc_trip.py"
PL_SRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "pokemon_league.py"
SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARMS = ("POKEBOT_R20_FAULT_NOFLYBOX", "POKEBOT_R20_FAULT_LOBBYSTAND", "POKEBOT_R20_FAULT_NOSWAPBACK")
HMS = {"Cut", "Fly", "Surf", "Strength", "Flash", "Rock Smash", "Waterfall", "Dive"}
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def learned(name, power=40):
    return types.SimpleNamespace(move=types.SimpleNamespace(
        name=name, base_power=0 if name in ("Growl",) else power,
        tm_hm=types.SimpleNamespace(name="HM0x") if name in HMS else None))


def mon(pid, species, level, moves, fly=True):
    return types.SimpleNamespace(
        personality_value=pid, level=level, is_egg=False, moves=[learned(n) for n in moves],
        species=types.SimpleNamespace(name=species, can_learn_tm_hm=lambda _it, _f=fly: _f))


HM02 = types.SimpleNamespace(name="HM02")


def f1(sink=None):
    check(PT.pc_stand_for((16, 10)) == ((6, 2), "Up"), "F1 the League lobby stands at (6,2) facing Up", sink)
    check(PT.pc_stand_for((12, 1)) == ((10, 2), "Up"), "F1 any other map keeps the standard (10,2)/Up", sink)


def f2(sink=None):
    saved = (EG.boxed_hm_learner_pids, PT.box_views)
    knower = mon(0xA1, "Swellow", 50, ["Fly", "Peck"])
    teachable = mon(0xA2, "Wingull", 20, ["Water Gun", "Growl"])
    saturated = mon(0xA3, "Pelipper", 40, ["Surf", "Fly", "Dive", "Waterfall"])
    saturated.moves = [learned(n) for n in ("Surf", "Dive", "Waterfall", "Strength")]
    try:
        EG.boxed_hm_learner_pids = lambda _it, avoid=None: [0xA1, 0xA3, 0xA2]
        PT.box_views = lambda: ([], [knower, teachable, saturated])
        got = PL._boxed_fly_learners(HM02, [])
    finally:
        EG.boxed_hm_learner_pids, PT.box_views = saved
    check(got == [0xA1, 0xA2], f"F2 keeps the knower and the teachable one, drops the four-HM one ({got})", sink)


def _with_mode(swap):
    mode = types.SimpleNamespace(_ch24_fly_swap=swap)
    saved = PL.context.bot_mode_instance if hasattr(PL.context, "bot_mode_instance") else None
    PL.context.bot_mode_instance = mode
    return mode, saved


def f3(pl_src: str, sink=None):
    import modules.pokemon_party as PP

    party = [mon(1, "Swampert", 60, ["Surf"]), mon(2, "Wingull", 20, ["Fly"]), mon(3, "Zigzagoon", 19, ["Tackle"])]
    saved_gp = PP.get_party
    mode, saved = _with_mode({"fighters": [(1, "Swampert"), (3, "Zigzagoon"), (4, "Castform")],
                              "carrier": (2, "Wingull"), "boxed": (4, "Castform")})
    try:
        PP.get_party = lambda: party
        below = [p for p, _s, _l in PL.ch24_trainees_below_floor(65)]
        mode._ch24_fly_swap = None
        below_none = [p for p, _s, _l in PL.ch24_trainees_below_floor(65)]
    finally:
        PP.get_party = saved_gp
        PL.context.bot_mode_instance = saved
    check(below == [3, 1], f"F3 the recorded carrier (Wingull) is not a trainee ({below})", sink)
    check(sorted(below_none) == [1, 2, 3], f"F3 with no swap recorded, everyone below the floor is ({below_none})", sink)
    fn = ast.unparse(next(n for n in ast.walk(ast.parse(pl_src))
                          if isinstance(n, ast.FunctionDef) and n.name == "prepare_and_open_the_league"))
    check("(m.personality_value, m.species.name) != _carrier" in fn,
          "F3 R1's head-count leaves the carrier out (AST)", sink)


def f4(sink=None):
    saved_gp, saved_lobby = PL.get_party, PL._in_league_lobby
    st: dict = {}

    def lobby(errand, *, leave):
        st["lobby"] = leave
        if st["lands"]:
            st["party"][:] = [m for m in st["party"] if m.personality_value != 2] + [mon(4, "Castform", 36, ["Hail"])]
        return True, "ok", (st["lands"], "landed" if st["lands"] else "did_not_land", "")
        yield

    PL.get_party, PL._in_league_lobby = (lambda: st["party"]), lobby
    swap = {"fighters": [(1, "Swampert"), (3, "Zigzagoon"), (4, "Castform")], "carrier": (2, "Wingull"),
            "boxed": (4, "Castform")}

    def run(sw, lands):
        st.update(party=[mon(1, "Swampert", 60, ["Surf"]), mon(2, "Wingull", 20, ["Fly"]),
                         mon(3, "Zigzagoon", 19, ["Tackle"])], lands=lands)
        st.pop("lobby", None)
        mode, saved = _with_mode(dict(sw) if sw else None)
        rep: dict = {}
        err = None
        try:
            for _ in PL.restore_ch24_fighters(rep):
                pass
        except BotModeError as error:
            err = str(error)
        finally:
            PL.context.bot_mode_instance = saved
        return rep, err, mode

    try:
        rep, err, _m = run(None, True)
        check(rep.get("swapback") == "none_needed" and err is None and "lobby" not in st,
              "F4 nothing recorded ⇒ no-op, no lobby", sink)
        rep, err, m = run(swap, True)
        check(err is None and st.get("lobby") is False and m._ch24_fly_swap is None and "F-RESTORED" in rep["readings"],
              f"F4 a swap that lands ⇒ the fighters are back, the record is cleared ({err})", sink)
        rep, err, _m = run(swap, False)
        check(err is not None and "RULING 21" in err, f"F4 a swap that does not land ⇒ REFUSES by name ({err!r:.60})", sink)
        os.environ["POKEBOT_R20_FAULT_NOSWAPBACK"] = "1"
        try:
            rep, err, _m = run(swap, True)
        finally:
            os.environ.pop("POKEBOT_R20_FAULT_NOSWAPBACK", None)
        check(err is not None and "lobby" not in st, "F4 NOSWAPBACK ⇒ no swap, and the identity check REFUSES", sink)
    finally:
        PL.get_party, PL._in_league_lobby = saved_gp, saved_lobby


def f5(sink=None, efl=None):
    """`efl` is `ensure_fly_learner` or a mutated copy (a fault arm)."""
    import modules.items as IT

    efl = efl or PL.ensure_fly_learner
    saved = (PL.get_party, IT.get_item_bag, PL._boxed_fly_learners, PL._in_league_lobby, EG.teach_hm_move,
             PT.withdraw_from_box)
    st: dict = {}

    class Party(list):
        def first_pokemon_with_move(self, name):
            return next((m for m in self if m is not None and any(l.move.name == name for l in m.moves)), None)

    def withdraw(pids):
        victim = st["party"][-1]
        st["party"][:] = st["party"][:-1] + [st["box"][pids[0]]]
        st["deposited"] = victim.personality_value
        return True, "landed", ""
        yield

    def lobby(errand, *, leave):
        st["lobbies"].append(leave)
        result = yield from errand()          # the REAL errand: the withdraw, then the swap record
        if st.get("raise_on_leave"):
            raise BotModeError("stub: the walk out of the lobby gave up")
        return True, "ok", result

    def teach(_hm, slot, replace_slot=None):
        st["teaches"].append(st["party"][slot].personality_value)
        st["party"][slot].moves = [learned("Fly")] + st["party"][slot].moves[1:]
        yield

    PL.get_party = lambda: st["party"]
    IT.get_item_bag = lambda: types.SimpleNamespace(tms_hms=[types.SimpleNamespace(item=HM02, quantity=1)])
    PL._boxed_fly_learners = lambda _hm, _b: list(st["boxed"])
    PL._in_league_lobby, EG.teach_hm_move, PT.withdraw_from_box = lobby, teach, withdraw

    def run(party, boxed, box, raise_on_leave=False):
        st.update(party=Party(party), boxed=boxed, box=box, lobbies=[], teaches=[], raise_on_leave=raise_on_leave)
        mode, saved_mode = _with_mode(None)
        rep: dict = {}
        err = None
        try:
            for _ in efl(rep):
                pass
        except BotModeError as error:
            err = str(error)
        finally:
            PL.context.bot_mode_instance = saved_mode
        return rep, mode, err

    nofly = [mon(1, "Swampert", 60, ["Surf", "Dive", "Waterfall", "Strength"]), mon(3, "Zigzagoon", 19, ["Tackle"], False)]
    wingull = mon(0xB1, "Wingull", 20, ["Water Gun", "Growl"])
    knower = mon(0xB2, "Swellow", 50, ["Fly", "Peck"])
    try:
        rep, _m, _e = run([mon(1, "Swellow", 50, ["Peck", "Growl"]), mon(3, "Zigzagoon", 19, ["Tackle"], False)], [], {})
        check(rep.get("fly_teach") == "taught" and st["lobbies"] == [] and st["teaches"] == [1],
              f"F5 a party learner ⇒ taught, no lobby ({rep.get('fly_teach')}, {st['lobbies']})", sink)
        rep, m, _e = run(list(nofly), [0xB1], {0xB1: wingull})
        sw = m._ch24_fly_swap or {}
        check(rep.get("fly_teach") == "taught" and st["lobbies"] == [True] and st["teaches"] == [0xB1],
              f"F5 no party learner + a boxed one ⇒ ONE lobby withdraw (leave=True), then it is taught "
              f"({rep.get('fly_teach')}, {st['lobbies']}, {st['teaches']})", sink)
        check(sw.get("carrier") == (0xB1, "Wingull") and sw.get("boxed") == (3, "Zigzagoon")
              and sw.get("fighters") == [(1, "Swampert"), (3, "Zigzagoon")],
              f"F5 ... the swap is recorded: fighters, carrier, the boxed fighter ({sw})", sink)
        rep, m, err = run(list(nofly), [0xB1], {0xB1: wingull}, raise_on_leave=True)
        sw = m._ch24_fly_swap or {}
        check(err is not None and sw.get("carrier") == (0xB1, "Wingull") and sw.get("boxed") == (3, "Zigzagoon"),
              f"F5 the walk OUT raises after the withdraw ⇒ the swap record SURVIVES (review 2026-09-27) ({sw}, {err!r:.50})",
              sink)
        rep, _m, _e = run(list(nofly), [0xB2], {0xB2: knower})
        check(rep.get("fly_teach") == "already" and st["teaches"] == [],
              f"F5 a boxed KNOWER ⇒ withdrawn, no teach ({rep.get('fly_teach')})", sink)
        os.environ["POKEBOT_R20_FAULT_NOFLYBOX"] = "1"
        try:
            rep, _m, _e = run(list(nofly), [0xB1], {0xB1: wingull})
        finally:
            os.environ.pop("POKEBOT_R20_FAULT_NOFLYBOX", None)
        check(rep.get("fly_teach") == "no_learner" and st["lobbies"] == [],
              f"F5 NOFLYBOX ⇒ no lobby, no_learner ({rep.get('fly_teach')})", sink)
    finally:
        (PL.get_party, IT.get_item_bag, PL._boxed_fly_learners, PL._in_league_lobby, EG.teach_hm_move,
         PT.withdraw_from_box) = saved


def f6(pl_src: str, sm_src: str, pt_src: str, sink=None):
    fn = ast.unparse(next(n for n in ast.walk(ast.parse(pl_src))
                          if isinstance(n, ast.FunctionDef) and n.name == "prepare_and_open_the_league"))
    i_in, i_swap, i_guard = (fn.find("_take(report, 'E1-INSIDE')"), fn.find("restore_ch24_fighters(swapback)"),
                             fn.find("_navigate_riding_out(VR.LEAGUE_1F, LEAGUE_GUARD_TALK_TILE)"))
    check(-1 < i_in < i_swap < i_guard,
          f"F6 the swap-back runs after E1-INSIDE and before the guard talk ({i_in} < {i_swap} < {i_guard})", sink)
    check("self._ch24_fly_swap = None" in ast.unparse(ast.parse(sm_src)), "F6 story_mode resets _ch24_fly_swap", sink)
    check("navigate_to(here, PC_STAND_TILE)" not in ast.unparse(ast.parse(pt_src)),
          "F1 no PC walk in pc_trip aims at the bare constant any more", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — RULING 20 Phase 1 (B) Fly site + RULING 21 swap-back")
    print("=" * 92)
    for a in ARMS:
        os.environ.pop(a, None)
    pl, sm, pt = (p.read_text(encoding="utf-8") for p in (PL_SRC, SM_SRC, PT_SRC))
    print("\n== F1 the stand tile ==")
    f1()
    print("\n== F2 the boxed Fly learners ==")
    f2()
    print("\n== F3 the carrier is not a fighter ==")
    f3(pl)
    print("\n== F4 restore_ch24_fighters ==")
    f4()
    print("\n== F5 ensure_fly_learner (collaborators stubbed) ==")
    f5()
    print("\n== F6 wiring ==")
    f6(pl, sm, pt)
    print("\n== the arms ==")
    reg = REGISTRY.read_text(encoding="utf-8")
    for a in ARMS:
        check(a in (pl + pt) and f"`{a}`" in reg, f"{a} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    for arm, part in (("POKEBOT_R20_FAULT_NOFLYBOX", f5), ("POKEBOT_R20_FAULT_NOSWAPBACK", f4),
                      ("POKEBOT_R20_FAULT_LOBBYSTAND", f1)):
        sink: list = []
        os.environ[arm] = "1"
        try:
            part(sink)
        finally:
            os.environ.pop(arm, None)
        check(bool(sink), f"FAULT {arm} FAILS {part.__name__.upper()} ({len(sink)} caught)")
    # The carrier exclusion removed: rebuild ch24_trainees_below_floor without its `continue`.
    node = next(n for n in ast.walk(ast.parse(pl)) if isinstance(n, ast.FunctionDef) and n.name == "ch24_trainees_below_floor")
    src = ast.get_source_segment(pl, node)
    mutated, n = re.subn(r"if carrier is not None and \(mon\.personality_value, mon\.species\.name\) == carrier:\s*\n\s*continue",
                         "pass", src, count=1)
    check(n == 1, "(fault-arm mutation applied exactly once: the carrier exclusion removed)")
    ns: dict = {}
    exec(compile(mutated, "<mutated ch24_trainees_below_floor>", "exec"), PL.__dict__, ns)  # noqa: S102 - gate fault arm
    saved_fn = PL.ch24_trainees_below_floor
    sink = []
    try:
        PL.ch24_trainees_below_floor = ns["ch24_trainees_below_floor"]
        f3(pl, sink)
    finally:
        PL.ch24_trainees_below_floor = saved_fn
    check(bool(sink), f"FAULT the carrier exclusion removed FAILS F3 ({len(sink)} caught)")
    # The OLD ordering (review, 2026-09-27): the swap recorded AFTER the walk out of the lobby, not inside the errand.
    node = next(n for n in ast.walk(ast.parse(pl)) if isinstance(n, ast.FunctionDef) and n.name == "ensure_fly_learner")
    src = ast.get_source_segment(pl, node)
    inner = "                _record_fly_swap(before_keys, head)\n"
    after = "            ok, detail, verdict = yield from _in_league_lobby(_collect, leave=True)\n"
    check(src.count(inner) == 1 and src.count(after) == 1,
          "(fault-arm mutation applied exactly once: the swap recorded after the walk out)")
    mutated = src.replace(inner, "", 1).replace(after, after + "            _record_fly_swap(before_keys, head)\n", 1)
    ns = {}
    exec(compile(mutated, "<mutated ensure_fly_learner>", "exec"), PL.__dict__, ns)  # noqa: S102 - gate fault arm
    sink = []
    f5(sink, efl=ns["ensure_fly_learner"])
    check(bool(sink), f"FAULT the swap recorded after the walk out FAILS F5 ({len(sink)} caught)")
    call = "    yield from restore_ch24_fighters(swapback)\n"
    guard = "VR._navigate_riding_out(VR.LEAGUE_1F, LEAGUE_GUARD_TALK_TILE), 60_000)\n"
    check(pl.count(call) == 1 and pl.count(guard) == 1,
          "(fault-arm mutation applied exactly once: the swap-back moved after the guard walk)")
    moved = pl.replace(call, "", 1).replace(guard, guard + "        yield from restore_ch24_fighters(swapback)\n", 1)
    sink = []
    f6(moved, sm, pt, sink)
    check(bool(sink), f"FAULT the swap-back moved after the guard talk FAILS F6 ({len(sink)} caught)")

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
