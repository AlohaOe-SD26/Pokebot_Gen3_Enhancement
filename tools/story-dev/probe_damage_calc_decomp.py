"""GATE — design v2 step 11, M1a (damage-calculator fidelity): OUR calculator
(`sandbox-pokebot/modules/battle_strategies/_util.py`, `BattleStrategyUtil.calculate_move_damage_range`) against the
game, as the decomp orders it. A PURE gate: no emulator, no ROM, nothing written to disk.

WHY. The design (`ai-research-notes/2026-09-30-dmgcalc11-DESIGN.md`, F2, after a five-angle recon and a three-lens
review) found that our calculator applies the crit and Charge AFTER STAB and the type chart (D1), walks the chart in
DEFENDER order instead of TABLE order (D2) and never floors a type step at 1 (D3), besides a set of base-term
divergences (Marvel Scale on the wrong battler, Guts + burn, Brick Break vs Reflect, KI-109/110/111, Struggle, Hidden
Power under Charge, fixed damage vs an immune type). Step 11 is MEASUREMENT ONLY (F1): every deviation is pinned here as a
KNOWN-DIVERGENCE row with three literals (the game, ours, the delta), so `#27-dmgcalcfix` has a gate that turns exactly
the fixed rows red.

THE INSTRUMENT CANNOT CERTIFY ITSELF (the review's blocker M1A-1). The game side of the sweep comes from a port
(`dmgcalc_port.py`, a decomp-ordered TEST ORACLE), and a port written in our order would find nothing and pass. So:
  - every game value asserted here was HAND-DERIVED from the decomp before the port existed
    (`2026-09-30-dmgcalc11-PREDICTIONS.md`, derivation in `2026-09-30-dmgcalc11-recon/m1_rows_game.md`), and the port is
    checked AGAINST those literals, never the reverse;
  - every OURS value pins current behaviour, measured on REAL `BattlePokemon` objects built from 0x58-byte gBattleMons
    records inside a REAL `BattleState` (`2026-09-30-dmgcalc11-recon/m1_rows_ours.md`, whose construction this reuses);
  - the enumerated bounds are asserted EXACTLY as pre-registered, and each must be at least its bucket's largest anchor
    delta (a smaller bound would mean the PORT is wrong);
  - the mutant "the port in OUR order" must turn the anchors red.

INPUT DIMENSIONS (a row per value):
  after-base order: crit (D-A1, D-A3) | crit + Charge (D-A2) | table vs defender order, under (D-N1) and over (D-O1) |
                    the per-step minimum (D-N2) | Struggle's skip (B-STR) | Charge on the LISTED type (B-HPC vs D-A2)
  base term: Marvel Scale on either battler (B-MS1, B-MS2) | Guts + burn (B-GUTS) | Brick Break vs Reflect (B-BB) |
             badges, foe -> us (B-KI110-B7, B-KI110-B8) | Solarbeam in rain (B-KI111) | Hidden Power type/power (B-HP,
             B-HPC)
  fixed damage: Sonicboom (B-SONIC) | Psywave's range (B-PSY) | vs an immune type, with a move whose NAME branch
                matches in our code (B-NS, B-ST, B-SF)
  the sweep: 17 move types x 289 ORDERED defender pairs (the port's table types, ROM order) x STAB x crit x Charge
             (Electric moves only) x B = 2..259, the real calculator with its base patched to B (BK-*, SW)
  the harness itself: the flag stub is live (L1); the side check refuses a stand-in (S1); the port's table is the ROM's
                      and its walk flags a no-effect hit (P1, P2); the CASES comparator is exact (C1)
  ADDED after the ADVERSARIAL MUTANT PASS (72 mutants, 2026-09-30), each killing mutants no row reached: burn without
  Guts (B-BURN) | Reflect, non-crit (B-REFL) and crit (B-CRIT-REFL) | badge 7 on OUR Sp. Atk (B-KI110-SPA) | a lost Atk
  stage, non-crit (B-STAGE) and crit (B-STAGE-CRIT) | a gained SpD stage on a special crit (B-SPD-CRIT, this gate's own
  row: nothing else reached U32) | a level not a multiple of 5 (B-LVL) | Charge on a non-Electric move (B-CHG-TACKLE) |
  Foresight (B-FORESIGHT) | the NON-immune fixed-damage branches (B-SF2, B-NS2, B-ST2, B-DR)

HOW THE ROWS REACH THE CODE. `_util` imported `get_event_flag` by name, so the badge flags are patched on `_util` per
row (patching `modules.memory` does nothing); `_calculate_base_move_damage` is patched on the class for Group D and the
sweep. Both always go through `sys.modules`, so a mutant module exec'd there is what every row runs.

SPEED. The sweep is 5,368,464 calls of the real calculator (~33 s in one process). Its results are cached per the AST of
`_util.py` MINUS `_calculate_base_move_damage` (the sweep patches that method, so its body never runs) and the port's
per the AST of `dmgcalc_port.py` MINUS `fixed_damage` (the sweep never calls it); so a mutant that cannot change the
sweep reuses it, and one that can re-runs it. The calculator half runs in a process pool (one task per move type; the
mutant's SOURCE is handed to the workers, never written to disk), in-process if no pool can be made. Measured
2026-09-30 after the follow-up (38 mutants, 7 of which change what the sweep can run): ~71 s with the pool; ⚠ 295 s
in-process, i.e. AT run_gates' 300 s FAST limit, so a machine that cannot make a pool will likely time out (loudly, rc
124). The two paths' sweeps were compared equal (real and m2).

FIRST RUN (2026-09-30): every pre-registered literal and bucket bound reproduced, and all 20 mutants turned exactly
their pre-written sets red, plus SW, whose own hand-multiplied total was an arithmetic slip (now written as factors).
FOLLOW-UP RUN (the adversarial pass's rows and 18 new mutants): every new row's game AND ours literal reproduced; 37 of
38 mutant sets were exact; u7's pre-written set missed BK-C and BK-CC (their anchor re-measurement runs the same
base-call assert), corrected in place with the reason. Each gate-check hollowing the pass found (calc == ours in the D
and B rows, L1's direction, the base-call assert, a raising row read as a pass, the comparator) was re-run on a scratch
copy and now fails a case (u8, u8, u9, u7, u7, C1).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 -u probe_damage_calc_decomp.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import json
import os
import pathlib
import struct
import sys
import time
import types
from array import array
from functools import lru_cache
from operator import sub
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001 - a stream without reconfigure keeps its encoding
    pass

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(HERE))

import modules.battle_strategies._util  # noqa: E402,F401  (the calculator under test; always read via sys.modules)
from modules.battle_state import BattlePokemon, BattleState, TemporaryStatus, Weather  # noqa: E402
from modules.pokemon import StatusCondition, get_move_by_name, get_species_by_name, get_type_by_name  # noqa: E402
import dmgcalc_port  # noqa: E402,F401  (the decomp-ordered oracle; always read via sys.modules)

U_NAME, P_NAME = "modules.battle_strategies._util", "dmgcalc_port"
U_PATH = SANDBOX / "modules" / "battle_strategies" / "_util.py"
P_PATH = HERE / "dmgcalc_port.py"
TYPES_JSON = SANDBOX / "modules" / "data" / "types.json"
REAL_U, REAL_P = sys.modules[U_NAME], sys.modules[P_NAME]
assert pathlib.Path(REAL_U.__file__).resolve() == U_PATH.resolve(), REAL_U.__file__
assert pathlib.Path(REAL_P.__file__).resolve() == P_PATH.resolve(), REAL_P.__file__
REAL_SRC = {U_NAME: U_PATH.read_text(encoding="utf-8"), P_NAME: P_PATH.read_text(encoding="utf-8")}
CURRENT_SRC = dict(REAL_SRC)  # what sys.modules holds right now (a mutant run swaps one entry)
PACKAGES = {U_NAME: "modules.battle_strategies", P_NAME: ""}
PATHS = {U_NAME: U_PATH, P_NAME: P_PATH}

FAILURES: list[str] = []


def U():
    return sys.modules[U_NAME]


def P():
    return sys.modules[P_NAME]


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def row(label, fn, tag, reds):
    try:
        ok, detail = fn()
    except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
        ok, detail = False, f"raised {type(error).__name__}: {error}"
    if not ok:
        reds.append(label.split()[0])
    if not tag:
        check(label, ok, detail)


def _install(name, source, filename):
    """Exec `source` as a fresh module registered as `name` (a mutant is never written to disk)."""
    mod = types.ModuleType(name)
    mod.__file__ = str(PATHS[name])
    mod.__package__ = PACKAGES[name]
    sys.modules[name] = mod
    exec(compile(source, filename, "exec"), mod.__dict__)
    return mod


# ---------------------------------------------------------------- object construction (m1_rows_ours.md's pin script)
STATUS1_POISON = 1 << 3
STATUS1_BURN = 1 << 4
STATUS3_CHARGED_UP = 1 << 9
B_WEATHER_RAIN_TEMPORARY = 1 << 0


def ivs_word(hp=0, atk=0, df=0, spe=0, spa=0, spd=0, is_egg=0, ability_num=0) -> int:
    return ((hp & 31) | (atk & 31) << 5 | (df & 31) << 10 | (spe & 31) << 15 | (spa & 31) << 20 | (spd & 31) << 25
            | (is_egg & 1) << 30 | (ability_num & 1) << 31)


def mon_record(species, types_, level, atk=100, df=100, spe=100, spa=100, spd=100, hp=None, max_hp=None, ivs=None,
               ability_num=0, status1=0, move=None, stages=None, status2=0) -> bytes:
    """One 0x58-byte gBattleMons entry (pret/pokeemerald include/pokemon.h `struct BattlePokemon`). The types are
    written by id at 0x21/0x22 in the ROW's ROM order (type2 = type1 for a mono-type, as the ROM stores it); our
    `BattlePokemon.types` reads them from there, never from the species. `stages` maps a statStages index (1 Atk,
    2 Def, 4 SpA, 5 SpD; the byte is 0x18 + index) to its raw value (6 = stage 0, 5 = -1, 7 = +1)."""
    sp = get_species_by_name(species)
    ability = sp.abilities[1 if (ability_num and len(sp.abilities) > 1) else 0]
    t1 = get_type_by_name(types_[0]).index
    t2 = get_type_by_name(types_[1]).index if types_[1] else t1
    max_hp = 150 if max_hp is None else max_hp
    hp = max_hp if hp is None else hp
    rec = bytearray(0x58)
    struct.pack_into("<H", rec, 0x00, sp.index)
    struct.pack_into("<HHHHH", rec, 0x02, atk, df, spe, spa, spd)
    struct.pack_into("<HHHH", rec, 0x0C, get_move_by_name(move).index if move else 0, 0, 0, 0)
    struct.pack_into("<I", rec, 0x14, ivs_word(ability_num=ability_num, **(ivs or {})))
    for i in range(8):
        rec[0x18 + i] = (stages or {}).get(i, 6)  # statStages: 6 = stage 0
    rec[0x20] = ability.index
    rec[0x21] = t1
    rec[0x22] = t2
    rec[0x24] = get_move_by_name(move).pp if move else 0
    struct.pack_into("<H", rec, 0x28, hp)
    rec[0x2A] = level
    rec[0x2B] = 70
    struct.pack_into("<H", rec, 0x2C, max_hp)
    struct.pack_into("<H", rec, 0x2E, 0)  # no held item
    struct.pack_into("<I", rec, 0x4C, status1)
    struct.pack_into("<I", rec, 0x50, status2)  # status2 (STATUS2_FORESIGHT = 1 << 29)
    return bytes(rec)


def make_state(ours: bytes, foe: bytes, ours_status3=0, foe_status3=0, foe_reflect=0, weather=0) -> BattleState:
    """A REAL single-battle BattleState: gBattleMons[4] (slots 2/3 unused), gStatuses3, gSideTimers (the foe's reflect
    timer is byte 12), no disable structs, no absent battlers."""
    side_timers = bytearray(24)
    side_timers[12] = foe_reflect
    side_timers[13] = 1 if foe_reflect else 0
    return BattleState(
        battle_type=struct.pack("<I", 0),
        side_timers=bytes(side_timers),
        battler_party_indexes=struct.pack("<HHHH", 0, 0, 0, 0),
        battler_party_order=bytes([0x01, 0x23, 0x45]),
        battler_count=2,
        battler=ours + foe + bytes(0x58 * 2),
        battler_status3=struct.pack("<IIII", ours_status3, foe_status3, 0, 0),
        battler_disable_structs=bytes(0x1C * 4),
        absent_battler_flags=0,
        current_turn=1,
        weather=weather,
    )


def assert_sides(state, attacker, defender, attacker_side):
    """Side membership is decided by RECORD EQUALITY, and `BattleStateSide.__contains__` returns NotImplemented for a
    non-BattlePokemon, which `in` reads as True. So call `__contains__` directly and demand exactly True/False."""
    own, opp = state.own_side, state.opponent
    assert isinstance(attacker, BattlePokemon) and isinstance(defender, BattlePokemon), "a stand-in, not a BattlePokemon"
    assert attacker._data != defender._data, "attacker and defender records are identical"
    a_own, d_own = own.__contains__(attacker), own.__contains__(defender)
    a_opp, d_opp = opp.__contains__(attacker), opp.__contains__(defender)
    for v in (a_own, d_own, a_opp, d_opp):
        assert v is True or v is False, f"__contains__ returned {v!r} (NotImplemented reads True)"
    if attacker_side == "ours":
        assert a_own is True and a_opp is False, "attacker not on OUR side"
        assert d_own is False and d_opp is True, "defender not on the FOE side"
    else:
        assert a_own is False and a_opp is True, "attacker not on the FOE side"
        assert d_own is True and d_opp is False, "defender not on OUR side"


FLAG_LOG: list[str] = []


def set_flags(flags):
    """Patch `_util.get_event_flag` (the name `_util` imported) with a recorder: the row's flags True, all else False."""
    FLAG_LOG.clear()

    def fake_get_event_flag(name):
        FLAG_LOG.append(name)
        return bool(flags.get(name, False))

    U().get_event_flag = fake_get_event_flag


def run_calc(state, move_name, attacker_side="ours", flags=None, crit=False, base_override=None):
    """The REAL calculator on the state's REAL battlers, sides asserted first. Returns ((min, max), attacker)."""
    u = U()
    saved_flag = u.get_event_flag
    set_flags(flags or {})
    b = state.battling_pokemon
    ours, foe = b[0], b[1]
    attacker, defender = (ours, foe) if attacker_side == "ours" else (foe, ours)
    assert_sides(state, attacker, defender, attacker_side)
    assert ours.ability.index == ours.ability_n and foe.ability.index == foe.ability_n, "ability byte 0x20 mismatch"
    move = get_move_by_name(move_name)
    cls = u.BattleStrategyUtil
    base_calls: list = []
    saved_base = cls.__dict__["_calculate_base_move_damage"]
    if base_override is not None:
        def fake_base(self, mv, att, dfn, is_critical_hit=False):
            base_calls.append(is_critical_hit)
            return base_override

        cls._calculate_base_move_damage = fake_base
    try:
        r = cls(state).calculate_move_damage_range(move, attacker, defender, is_critical_hit=crit)
    finally:
        cls._calculate_base_move_damage = saved_base
        u.get_event_flag = saved_flag
    if base_override is not None:
        assert base_calls == [crit], f"the patched base was not called exactly once with crit={crit}: {base_calls}"
    return (r.min, r.max), attacker


def rom_pair(types_):
    return (types_[0], types_[1] or types_[0])


# ------------------------------------------------------------------------------------ P rows (the port itself)
def p_rows(tag=""):
    reds: list = []

    def p1():  # the port's table IS the ROM chart: every entry, and each attacking type's rows in the same order
        p = P()
        data = json.loads(TYPES_JSON.read_text(encoding="utf-8"))
        names = [t["name"] for t in data]
        ids_ok = all(p.ROM_TYPE_IDS[n] == get_type_by_name(n).index for n in names) and len(p.ROM_TYPE_IDS) == 18
        want_types = tuple(sorted((n for n in names if n != "???"), key=lambda n: get_type_by_name(n).index))
        body = [(a, d, m) for a, d, m in p.TYPE_EFFECTIVENESS if a != p.FORESIGHT]
        sentinel = [i for i, (a, _, _) in enumerate(p.TYPE_EFFECTIVENESS) if a == p.FORESIGHT]
        after = p.TYPE_EFFECTIVENESS[sentinel[0] + 1:] if len(sentinel) == 1 else None
        per_type = {}
        for a, d, m in body:
            per_type.setdefault(a, []).append((d, m / 10))
        order_ok = all(per_type.get(t["name"], []) == [(d, float(v)) for d, v in t["effectiveness"].items()]
                       for t in data)
        ok = (ids_ok and p.TABLE_TYPES == want_types and len(p.TYPE_EFFECTIVENESS) == 111 and len(sentinel) == 1
              and after == [("Normal", "Ghost", 0), ("Fighting", "Ghost", 0)] and order_ok)
        return ok, (f"ids {ids_ok}; {len(p.TABLE_TYPES)} table types in ROM order {p.TABLE_TYPES == want_types}; "
                    f"{len(p.TYPE_EFFECTIVENESS)} rows; sentinel at {sentinel}, then {after}; types.json order {order_ok}")

    def p2():  # the walk's flags, hand-derived from the decomp (not from the port's output)
        p = P()
        got = {
            # Ground->Flying 0 (BM:396) then Ground->Rock 20 (BM:398): the step floors 0 back to 1 (BSC:1324-1325),
            # but DOESNT_AFFECT_FOE is set (BSC:1329-1330), so the HP update is skipped (BSC:1862): the hit deals 0
            "no-effect then x2": p.after_base(10, "Ground", ("Normal", "Normal"), ("Flying", "Rock"), False, False),
            # Normal->Ghost 0 sits AFTER the sentinel (BM:446): applied without Foresight, skipped with it (BSC:1388-1393)
            "Normal vs Ghost": p.after_base(10, "Normal", ("Fighting", "Fighting"), ("Ghost", "Ghost"), False, False),
            "Normal vs Ghost, Foresight": p.after_base(10, "Normal", ("Fighting", "Fighting"), ("Ghost", "Ghost"),
                                                       False, False, foresight=True),
            # a mono-type (type2 == type1) takes its row ONCE (BSC:1401-1402)
            "mono Rock steps": p.type_steps("Fighting", "Rock", "Rock"),
        }
        want = {"no-effect then x2": (0, 0), "Normal vs Ghost": (0, 0), "Normal vs Ghost, Foresight": (8, 10),
                "mono Rock steps": (20,)}
        return got == want, str(got)

    for label, fn in (("P1 the port's table is the ROM chart (types.json: every entry, ids, within-type order), "
                       "17 table types", p1),
                      ("P2 the port's walk: a no-effect hit deals 0, the Foresight sentinel, a mono-type row once", p2)):
        row(label, fn, tag, reds)
    return reds


# ----------------------------------------------------------------- D rows (after the base: B given, both sides)
#: id, what, move, (attacker species, attacker types), (defender species, defender types ROM order), B, crit, Charge,
#: GAME [min, max] (hand-derived, PREDICTIONS), OURS (min, max) (the pin), DELTA on max (ours - game)
D_SPEC = {
    "D-A1": ("the crit applied after STAB/type (Fighting STAB vs Normal/Rock, B=3, crit)", "Karate Chop",
             ("Hitmonlee", ("Fighting", None)), ("Zigzagoon", ("Normal", "Rock")), 3, True, False,
             (30, 36), (27, 32), -4),
    "D-A2": ("the same with Charge (Spark STAB vs Water/Flying, B=3, crit + Charge)", "Spark",
             ("Pikachu", ("Electric", None)), ("Wingull", ("Water", "Flying")), 3, True, True,
             (61, 72), (54, 64), -8),
    "D-A3": ("Mud-Slap STAB (attacker type2) vs Electric/Steel, B=5, crit", "Mud-slap",
             ("Whiscash", ("Water", "Ground")), ("Magnemite", ("Electric", "Steel")), 5, True, False,
             (51, 60), (47, 56), -4),
    "D-N1": ("the type order, under (Bite STAB vs Sableye Dark/Ghost, B=5)", "Bite",
             ("Poochyena", ("Dark", None)), ("Sableye", ("Dark", "Ghost")), 5, False, False,
             (5, 7), (5, 6), -1),
    "D-N2": ("the per-step minimum of 1 (Signal Beam vs Steel/Flying, B=2)", "Signal Beam",
             ("Magikarp", ("Water", None)), ("Skarmory", ("Steel", "Flying")), 2, False, False,
             (1, 1), (1, 0), -1),
    "D-O1": ("the type order, over (Karate Chop vs Rock/Flying, B=3)", "Karate Chop",
             ("Magikarp", ("Water", None)), ("Aerodactyl", ("Rock", "Flying")), 3, False, False,
             (1, 2), (2, 3), +1),
}


def d_measure(rid):
    """(port (min, max), calculator (min, max)) for a Group D row: the port from the row's spec, the calculator on REAL
    objects with its base patched to B."""
    _, mv, (asp, aty), (dsp, dty), B, crit, charge, _, _, _ = D_SPEC[rid]
    st = make_state(mon_record(asp, aty, 50, move=mv), mon_record(dsp, dty, 50, max_hp=200),
                    ours_status3=STATUS3_CHARGED_UP if charge else 0)
    if charge:
        assert TemporaryStatus.ChargedUp in st.battling_pokemon[0].status_temporary, "Charge did not reach status3"
    calc, _ = run_calc(st, mv, crit=crit, base_override=B)
    move = get_move_by_name(mv)
    p = P()
    port = p.after_base(B, move.type.name, rom_pair(aty), rom_pair(dty), crit,
                        p.charge_applies(charge, move.type.name, move.type.name))
    return port, calc


def d_rows(tag=""):
    reds: list = []
    for rid, (what, *_rest) in D_SPEC.items():
        game, ours, delta = D_SPEC[rid][7], D_SPEC[rid][8], D_SPEC[rid][9]

        def fn(rid=rid, game=game, ours=ours, delta=delta):
            port, calc = d_measure(rid)
            ok = (port == game and calc == ours and calc[1] - port[1] == delta and ours[1] - game[1] == delta
                  and delta != 0)
            return ok, (f"game(port) {list(port)} want {list(game)}; ours {calc} want {ours}; "
                        f"delta {calc[1] - port[1]:+d} want {delta:+d}")

        row(f"{rid} {what}: game {list(game)}, ours {ours}, delta {delta:+d}", fn, tag, reds)
    return reds


# --------------------------------------------------------------- B rows (the base term, the full real calculator)
#: The BASE B the hand derivation found for each Group B row (m1_rows_game.md: "+2 -> B = ..."), fed to the PORT so
#: its after-base half is checked against the same hand-derived game literal. The calculator never sees these.
B_HAND = {"B-MS1": 12, "B-MS2": 17, "B-GUTS": 28, "B-BB": 35, "B-KI110-B7": 18, "B-KI110-B8": 19, "B-KI111": 28,
          "B-STR": 24, "B-HP": 32, "B-HPC": 32,
          # the adversarial pass's rows (2026-09-30 follow-up): the coordinator gave their GAME literals (derived twice);
          # these B values are this gate's own derivation from src/pokemon.c (P:), feeding the port the same literal.
          # Tackle L50 Atk 100 vs Def 100: 100*35*22/100/50 = 15 (P:3243-3260).
          "B-BURN": 9,        # burn halves a non-Guts attacker: 15/2 = 7, +2 (P:3263-3264, P:3371)
          "B-REFL": 9,        # Reflect, no crit, singles: 15/2 = 7, +2 (P:3267-3273)
          "B-KI110-SPA": 21,  # our SpA x1.1 on badge 7 (P:3165): 110*40*22/100/50 = 19, +2
          "B-STAGE": 12,      # Atk stage -1: 100*10/15 = 66 (P:1874, P:3100-3104); 66*35*22/100/50 = 10, +2
          "B-STAGE-CRIT": 17,  # a crit ignores a LOST Atk stage: attack stays 100 (P:3237-3240): 15, +2
          "B-CRIT-REFL": 17,   # a crit skips Reflect (P:3267 `gCritMultiplier == 1`): 15, +2
          "B-LVL": 5,          # L8: level factor 2*8/5+2 = 5 (P:3246); 100*35*5/100/50 = 3, +2
          "B-CHG-TACKLE": 17,  # Charge does not touch the base term: 15, +2
          "B-FORESIGHT": 17,   # the base term ignores Foresight: 15, +2
          "B-SPD-CRIT": 19}    # Water Gun crit, SpA stage 0 (raw, P:3292-3295), defender SpD +1 IGNORED (raw 100,
#                                P:3306-3309): 100*40*22/100/50 = 17, +2


def b_rows(tag=""):
    reds: list = []
    p = P()

    def three(game, ours, delta, calc, port, extra_ok=True, extra=""):
        ok = (calc == ours and port == game and calc[1] - game[1] == delta and ours[1] - game[1] == delta
              and extra_ok)
        return ok, (f"game {list(game)} (port {list(port)}); ours {calc} want {ours}; "
                    f"delta {calc[1] - game[1]:+d} want {delta:+d}" + (f"; {extra}" if extra else ""))

    def after(rid, move_type, att, dfn, charge=False, struggle=False, crit=False, foresight=False):
        return p.after_base(B_HAND[rid], move_type, att, dfn, crit, charge, struggle, foresight)

    def ms1():
        st = make_state(mon_record("Magikarp", ("Water", None), 50, atk=100, move="Tackle"),
                        mon_record("Milotic", ("Water", None), 50, df=100, max_hp=200, status1=STATUS1_BURN))
        pre = st.battling_pokemon[1].status_permanent is StatusCondition.Burn
        calc, _ = run_calc(st, "Tackle")
        return three((10, 12), (14, 17), +5, calc, after("B-MS1", "Normal", ("Water", "Water"), ("Water", "Water")),
                     pre, f"foe burned {pre}")

    def ms2():
        st = make_state(mon_record("Magikarp", ("Water", None), 50, atk=100, status1=STATUS1_POISON, move="Tackle"),
                        mon_record("Milotic", ("Water", None), 50, df=100, max_hp=200))
        pre = st.battling_pokemon[0].status_permanent is StatusCondition.Poison
        calc, _ = run_calc(st, "Tackle")
        return three((14, 17), (10, 12), -5, calc, after("B-MS2", "Normal", ("Water", "Water"), ("Water", "Water")),
                     pre, f"ours poisoned {pre}")

    def guts():
        st = make_state(mon_record("Rattata", ("Normal", None), 50, atk=100, ability_num=1, status1=STATUS1_BURN,
                                   move="Quick Attack"),
                        mon_record("Magikarp", ("Water", None), 50, df=100, max_hp=200))
        pre = st.battling_pokemon[0].ability.name == "Guts"
        calc, _ = run_calc(st, "Quick Attack")
        return three((35, 42), (18, 22), -20, calc,
                     after("B-GUTS", "Normal", ("Normal", "Normal"), ("Water", "Water")), pre, f"Guts {pre}")

    def bb():
        st = make_state(mon_record("Hitmonlee", ("Fighting", None), 50, atk=100, move="Brick Break"),
                        mon_record("Zigzagoon", ("Normal", None), 50, df=100, max_hp=200), foe_reflect=5)
        pre = st.opponent.reflect_timer.turns_remaining == 5 and st.own_side.reflect_timer.turns_remaining == 0
        calc, _ = run_calc(st, "Brick Break")
        return three((88, 104), (45, 54), -50, calc,
                     after("B-BB", "Fighting", ("Fighting", "Fighting"), ("Normal", "Normal")), pre, f"Reflect {pre}")

    def ki110(rid, flags, game, ours, delta):
        def fn():
            st = make_state(mon_record("Poochyena", ("Dark", None), 50, spd=100, max_hp=200),
                            mon_record("Magikarp", ("Water", None), 50, spa=100, move="Water Gun"))
            calc, _ = run_calc(st, "Water Gun", attacker_side="foe", flags=flags)
            # ⚠ (follow-up C) no "BADGE08 was queried" clause: a CORRECT KI-110 fix stops reading BADGE08, and the row
            # must then go green on re-pinned literals. L1 proves the badge patch reaches `_util`.
            return three(game, ours, delta, calc, after(rid, "Water", ("Water", "Water"), ("Dark", "Dark")))
        return fn

    def ki111():
        st = make_state(mon_record("Tangela", ("Grass", None), 50, spa=100, move="Solarbeam"),
                        mon_record("Magikarp", ("Water", None), 50, spd=100, max_hp=200),
                        weather=B_WEATHER_RAIN_TEMPORARY)
        pre = st.weather is Weather.Rain
        calc, _ = run_calc(st, "Solarbeam")
        return three((71, 84), (137, 162), +78, calc,
                     after("B-KI111", "Grass", ("Grass", "Grass"), ("Water", "Water")), pre, f"rain {pre}")

    def struggle():
        st = make_state(mon_record("Zigzagoon", ("Normal", None), 50, atk=100, move="Struggle"),
                        mon_record("Shuppet", ("Ghost", None), 50, df=100, max_hp=200))
        calc, _ = run_calc(st, "Struggle")
        return three((20, 24), (1, 0), -24, calc,
                     after("B-STR", "Normal", ("Normal", "Normal"), ("Ghost", "Ghost"), struggle=True))

    def hp():
        st = make_state(mon_record("Zigzagoon", ("Normal", None), 50, spa=100, move="Hidden Power",
                                   ivs=dict(hp=31, atk=31, df=31, spe=31, spa=31, spd=31)),
                        mon_record("Rattata", ("Normal", None), 50, spd=100, max_hp=200))
        a = st.battling_pokemon[0]
        rolled = (a.hidden_power_type.name, a.hidden_power_damage)
        calc, _ = run_calc(st, "Hidden Power")
        # a FIDELITY row: the game equals ours, delta 0 (the game's Dark 70 is m1_rows_game.md's hiddenpowercalc)
        return three((27, 32), (27, 32), 0, calc, after("B-HP", "Dark", ("Normal", "Normal"), ("Normal", "Normal")),
                     rolled == ("Dark", 70), f"ours rolls {rolled}, the game Dark 70")

    def hpc():
        st = make_state(mon_record("Zigzagoon", ("Normal", None), 50, spa=100, move="Hidden Power",
                                   ivs=dict(hp=31, atk=31, df=31, spe=31, spa=30, spd=31)),
                        mon_record("Magikarp", ("Water", None), 50, spd=100, max_hp=200),
                        ours_status3=STATUS3_CHARGED_UP)
        a = st.battling_pokemon[0]
        rolled = (a.hidden_power_type.name, a.hidden_power_damage)
        charged = TemporaryStatus.ChargedUp in a.status_temporary
        calc, _ = run_calc(st, "Hidden Power")
        listed = get_move_by_name("Hidden Power").type.name
        port = after("B-HPC", "Electric", ("Normal", "Normal"), ("Water", "Water"),
                     charge=p.charge_applies(charged, listed, "Electric"))
        return three((54, 64), (108, 128), +64, calc, port, rolled == ("Electric", 70) and charged,
                     f"ours rolls {rolled}, charged {charged}, listed {listed}")

    def fixed(rid, move_name, attacker, defender, game, ours, delta, target_hp=200):
        def fn():
            (asp, aty), (dsp, dty) = attacker, defender
            st = make_state(mon_record(asp, aty, 30, move=move_name),
                            mon_record(dsp, dty, 50, max_hp=200, hp=target_hp))
            calc, _ = run_calc(st, move_name)
            move = get_move_by_name(move_name)
            port = p.fixed_damage(move.effect, 30, target_hp, move.type.name, rom_pair(dty))
            return three(game, ours, delta, calc, port, extra=f"effect {move.effect}")
        return fn

    # ---- the adversarial pass's rows (follow-up A). GAME literals: the coordinator's, derived twice by hand from the
    # decomp; B-SPD-CRIT is THIS gate's own (one derivation, P:3292-3309), added because no specified row could kill
    # U32 (every special crit row had a defender SpD stage of 0, where raw == modified under any inversion).
    NORMAL, ZIG, RAT = ("Normal", "Normal"), ("Zigzagoon", ("Normal", None)), ("Rattata", ("Normal", None))

    def tackle(rid, game, ours, delta, crit=False, level=50, ours_kw=None, foe_kw=None, state_kw=None, foe=RAT,
               port_kw=None, pre=lambda st: (True, "")):
        def fn():
            st = make_state(mon_record(ZIG[0], ZIG[1], level, atk=100, move="Tackle", **(ours_kw or {})),
                            mon_record(foe[0], foe[1], 50, df=100, max_hp=200, **(foe_kw or {})), **(state_kw or {}))
            pre_ok, pre_detail = pre(st)
            calc, _ = run_calc(st, "Tackle", crit=crit)
            port = after(rid, "Normal", NORMAL, rom_pair(foe[1]), crit=crit, **(port_kw or {}))
            return three(game, ours, delta, calc, port, pre_ok, pre_detail)
        return fn

    def burned(st):
        a = st.battling_pokemon[0]
        ok = a.status_permanent is StatusCondition.Burn and a.ability.name != "Guts"
        return ok, f"ours burned, ability {a.ability.name}"

    def reflect_up(st):
        ok = st.opponent.reflect_timer.turns_remaining == 5
        return ok, f"foe Reflect {st.opponent.reflect_timer.turns_remaining}"

    def atk_minus_one(st):
        ok = st.battling_pokemon[0].stats_modifiers.attack == -1
        return ok, f"ours Atk stage {st.battling_pokemon[0].stats_modifiers.attack}"

    def charged_up(st):
        ok = TemporaryStatus.ChargedUp in st.battling_pokemon[0].status_temporary
        return ok, f"ours charged {ok}"

    def foresighted(st):
        ok = TemporaryStatus.Foresight in st.battling_pokemon[1].status_temporary
        return ok, f"foe Foresight {ok}"

    def ki110_spa():
        st = make_state(mon_record("Magikarp", ("Water", None), 50, spa=100, move="Water Gun"),
                        mon_record("Poochyena", ("Dark", None), 50, spd=100, max_hp=200))
        calc, _ = run_calc(st, "Water Gun", flags={"BADGE07_GET": True})
        return three((26, 31), (26, 31), 0, calc,
                     after("B-KI110-SPA", "Water", ("Water", "Water"), ("Dark", "Dark")))

    def spd_crit():
        st = make_state(mon_record("Zigzagoon", ("Normal", None), 50, spa=100, move="Water Gun"),
                        mon_record("Rattata", ("Normal", None), 50, spd=100, max_hp=200, stages={5: 7}))
        stage = st.battling_pokemon[1].stats_modifiers.special_defence
        calc, _ = run_calc(st, "Water Gun", crit=True)
        return three((32, 38), (32, 38), 0, calc,
                     after("B-SPD-CRIT", "Water", NORMAL, NORMAL, crit=True), stage == 1, f"foe SpD stage {stage}")

    new_rows = (
        ("B-BURN burn halves a non-Guts attacker (FIDELITY): game [11, 13] = ours (11, 13)",
         tackle("B-BURN", (11, 13), (11, 13), 0, ours_kw={"status1": STATUS1_BURN}, pre=burned)),
        ("B-REFL Reflect halves a non-crit (FIDELITY): game [11, 13] = ours (11, 13)",
         tackle("B-REFL", (11, 13), (11, 13), 0, state_kw={"foe_reflect": 5}, pre=reflect_up)),
        ("B-KI110-SPA badge 7 boosts OUR Sp. Atk (FIDELITY): game [26, 31] = ours (26, 31)", ki110_spa),
        ("B-STAGE our Atk stage -1 (FIDELITY): game [15, 18] = ours (15, 18)",
         tackle("B-STAGE", (15, 18), (15, 18), 0, ours_kw={"stages": {1: 5}}, pre=atk_minus_one)),
        ("B-STAGE-CRIT the same, CRIT (a crit ignores the lost stage; D1): game [43, 51], ours (42, 50), delta -1",
         tackle("B-STAGE-CRIT", (43, 51), (42, 50), -1, crit=True, ours_kw={"stages": {1: 5}}, pre=atk_minus_one)),
        ("B-CRIT-REFL a CRIT into Reflect (a crit ignores Reflect; D1): game [43, 51], ours (42, 50), delta -1",
         tackle("B-CRIT-REFL", (43, 51), (42, 50), -1, crit=True, state_kw={"foe_reflect": 5}, pre=reflect_up)),
        ("B-LVL our L8 attacker, level factor 5 (FIDELITY): game [5, 7] = ours (5, 7)",
         tackle("B-LVL", (5, 7), (5, 7), 0, level=8)),
        ("B-SF2 Super Fang vs a Normal foe at 150/200 (FIDELITY): game 75 = ours (75, 75)",
         fixed("B-SF2", "Super Fang", ZIG, RAT, (75, 75), (75, 75), 0, target_hp=150)),
        ("B-CHG-TACKLE a CHARGED Tackle (Charge is Electric only; FIDELITY): game [21, 25] = ours (21, 25)",
         tackle("B-CHG-TACKLE", (21, 25), (21, 25), 0, state_kw={"ours_status3": STATUS3_CHARGED_UP},
                port_kw={"charge": p.charge_applies(True, "Normal", "Normal")}, pre=charged_up)),
        ("B-NS2 Night Shade vs Water (FIDELITY): game 30 = ours (30, 30)",
         fixed("B-NS2", "Night Shade", ("Shuppet", ("Ghost", None)), ("Magikarp", ("Water", None)),
               (30, 30), (30, 30), 0)),
        ("B-ST2 Seismic Toss vs Normal (FIDELITY): game 30 = ours (30, 30)",
         fixed("B-ST2", "Seismic Toss", ("Hitmonlee", ("Fighting", None)), RAT, (30, 30), (30, 30), 0)),
        ("B-DR Dragon Rage vs Normal (FIDELITY): game 40 = ours (40, 40)",
         fixed("B-DR", "Dragon Rage", ZIG, RAT, (40, 40), (40, 40), 0)),
        ("B-FORESIGHT Tackle into a FORESIGHTED Ghost: game [21, 25], ours (1, 0), delta -25",
         tackle("B-FORESIGHT", (21, 25), (1, 0), -25, foe=("Shuppet", ("Ghost", None)),
                foe_kw={"status2": 1 << 29}, port_kw={"foresight": True}, pre=foresighted)),
        ("B-SPD-CRIT a CRIT special hit, defender SpD +1 ignored (FIDELITY; this gate's own row): game [32, 38] = "
         "ours (32, 38)", spd_crit),
    )

    for label, fn in (
            ("B-MS1 Marvel Scale on the (burned) DEFENDER: game [10, 12], ours (14, 17), delta +5", ms1),
            ("B-MS2 Marvel Scale wrongly on our (poisoned) attacker: game [14, 17], ours (10, 12), delta -5", ms2),
            ("B-GUTS Guts + burn (no halving in the game): game [35, 42], ours (18, 22), delta -20", guts),
            ("B-BB Brick Break removes Reflect first: game [88, 104], ours (45, 54), delta -50", bb),
            ("B-KI110-B7 our Sp. Def boost on badge 7 (foe -> us): game [22, 27], ours (23, 28), delta +1",
             ki110("B-KI110-B7", {"BADGE07_GET": True}, (22, 27), (23, 28), +1)),
            ("B-KI110-B8 the same, badge 8 only: game [23, 28], ours (22, 27), delta -1",
             ki110("B-KI110-B8", {"BADGE08_GET": True}, (23, 28), (22, 27), -1)),
            ("B-KI111 Solarbeam in rain: game [71, 84], ours (137, 162), delta +78", ki111),
            ("B-STR Struggle is typeless (vs Ghost): game [20, 24], ours (1, 0), delta -24", struggle),
            ("B-HP Hidden Power (all IVs 31: Dark, 70), a FIDELITY row: game [27, 32] = ours (27, 32)", hp),
            ("B-HPC Hidden Power rolled Electric under Charge: game [54, 64], ours (108, 128), delta +64", hpc),
            ("B-SONIC Sonicboom (KI-109): game 20 (no random), ours (3, 4), delta -16",
             fixed("B-SONIC", "Sonicboom", ("Zigzagoon", ("Normal", None)), ("Rattata", ("Normal", None)),
                   (20, 20), (3, 4), -16)),
            ("B-PSY Psywave at L30 (KI-109; the minimum is level/2): game [15, 45], ours (2, 3), delta -42",
             fixed("B-PSY", "Psywave", ("Abra", ("Psychic", None)), ("Rattata", ("Normal", None)),
                   (15, 45), (2, 3), -42)),
            ("B-NS Night Shade vs Normal (immune in the game): game 0, ours (30, 30), delta +30",
             fixed("B-NS", "Night Shade", ("Shuppet", ("Ghost", None)), ("Rattata", ("Normal", None)),
                   (0, 0), (30, 30), +30)),
            ("B-ST Seismic Toss vs Ghost: game 0, ours (30, 30), delta +30",
             fixed("B-ST", "Seismic Toss", ("Hitmonlee", ("Fighting", None)), ("Shuppet", ("Ghost", None)),
                   (0, 0), (30, 30), +30)),
            ("B-SF Super Fang vs Ghost: game 0, ours (100, 100), delta +100",
             fixed("B-SF", "Super Fang", ("Zigzagoon", ("Normal", None)), ("Shuppet", ("Ghost", None)),
                   (0, 0), (100, 100), +100))) + new_rows:
        row(label, fn, tag, reds)
    return reds


# ------------------------------------------------------- L / S rows (the harness's own levers are live and honest)
def ls_rows(tag=""):
    reds: list = []

    def tackle_state():
        return make_state(mon_record("Zigzagoon", ("Normal", None), 50, atk=100, move="Tackle"),
                          mon_record("Rattata", ("Normal", None), 50, df=100, max_hp=200))

    def l1():  # the badge stub reaches the calculator: BADGE01 must move ours (pinned: m1_rows_ours.md's control)
        off, _ = run_calc(tackle_state(), "Tackle", flags={})
        q_off = "BADGE01_GET" in FLAG_LOG
        on, _ = run_calc(tackle_state(), "Tackle", flags={"BADGE01_GET": True})
        q_on = "BADGE01_GET" in FLAG_LOG
        return off == (21, 25) and on == (22, 27) and q_off and q_on, f"off {off}, BADGE01 {on}; queried {q_off}/{q_on}"

    def s1():  # a stand-in must be REFUSED (the hazard: `stand_in in side` is True because __contains__ says NotImplemented)
        st = tackle_state()
        a, d = st.battling_pokemon[0], st.battling_pokemon[1]
        assert_sides(st, a, d, "ours")  # the real pair is accepted
        stand_in = SimpleNamespace(_data=a._data, types=a.types, ability=a.ability, level=a.level)
        hazard = st.own_side.__contains__(stand_in) is NotImplemented
        twin = make_state(mon_record("Zigzagoon", ("Normal", None), 50), mon_record("Zigzagoon", ("Normal", None), 50))
        cases = {"stand-in attacker": (st, stand_in, d, "ours"), "stand-in defender": (st, a, stand_in, "ours"),
                 "swapped sides": (st, d, a, "ours"), "wrong side named": (st, a, d, "foe"),
                 "identical records": (twin, twin.battling_pokemon[0], twin.battling_pokemon[1], "ours")}
        refused = {}
        for name, args in cases.items():
            try:
                assert_sides(*args)
                refused[name] = False
            except AssertionError:
                refused[name] = True
        return hazard and all(refused.values()), f"__contains__(stand-in) is NotImplemented: {hazard}; refused {refused}"

    def c1():  # the CASES comparator: a mutant that reddens MORE (or fewer) rows than its set is a mismatch
        # (the adversarial pass: a comparator weakened to `want <= red` accepted over-reddening unnoticed)
        probes = [((frozenset({"A", "B"}), frozenset({"A"})), False),   # over-reddening, `want` too small
                  ((frozenset({"A"}), frozenset({"A", "B"})), False),   # under-reddening
                  ((frozenset({"A"}), frozenset()), False),             # a comment-only edit that reddened a row
                  ((frozenset({"A"}), frozenset({"A"})), True),
                  ((frozenset(), frozenset()), True)]
        got = [case_verdict(set(red), set(want)) for (red, want), _ in probes]
        return got == [want for _, want in probes], f"verdicts {got}"

    for label, fn in (("L1 the badge stub is LIVE: BADGE01 on vs off changes ours (21, 25) -> (22, 27)", l1),
                      ("S1 the side check refuses a stand-in, swapped sides, a wrong side and identical records", s1),
                      ("C1 the CASES comparator reports over- AND under-reddening as a mismatch", c1)):
        row(label, fn, tag, reds)
    return reds


# ---------------------------------------------------------------------------------------- the enumerated sweep
SWEEP_TYPES: tuple[str, ...] = REAL_P.TABLE_TYPES  # move types AND defender types: the port's table, ROM order
SWEEP_BS = tuple(range(2, 260))
#: One whitelisted, non-Struggle move per type (design F2's Tier A, keyed on moves.json `effect`: HIT where the type has
#: one, else the first Tier A move by index). Its power never matters (the base is patched); none is a name our
#: calculator special-cases, none is Hidden Power, none is a sound move.
SWEEP_MOVES = {"Normal": "Pound", "Fighting": "Karate Chop", "Flying": "Wing Attack", "Poison": "Acid",
               "Ground": "Bone Club", "Rock": "Rock Throw", "Bug": "Megahorn", "Ghost": "Lick", "Steel": "Steel Wing",
               "Fire": "Blast Burn", "Water": "Water Gun", "Grass": "Vine Whip", "Electric": "Thunderpunch",
               "Psychic": "Psychic", "Ice": "Ice Punch", "Dragon": "Dragon Claw", "Dark": "Bite"}
SWEEP_TIER_A = {"HIT", "HIGH_CRITICAL", "RECHARGE", "FLINCH_HIT", "PARALYZE_HIT", "FREEZE_HIT", "DEFENSE_DOWN_HIT",
                "DEFENSE_UP_HIT", "SPECIAL_DEFENSE_DOWN_HIT"}
SWEEP_ATTACKER, SWEEP_DEFENDER = "Rattata", "Zigzagoon"  # Run Away (abilityNum 0) / Pickup: no ability our code tests


def sweep_off_type(move_type):
    """The attacker's type for STAB OFF: any type other than the move's."""
    return "Fighting" if move_type == "Normal" else "Normal"


def sweep_combos(move_types=None):
    for mt in (move_types or SWEEP_TYPES):
        for t1 in SWEEP_TYPES:
            for t2 in SWEEP_TYPES:
                for stab in (False, True):
                    for charge in ((False, True) if mt == "Electric" else (False,)):
                        yield mt, t1, t2, stab, charge


@lru_cache(maxsize=None)
def _sweep_record(species, t1, t2):
    return mon_record(species, (t1, t2), 50, max_hp=200)


def _calc_sweep_chunk(task):
    """One move type of the sweep through the REAL calculator (`task` = (util source or None for the real module,
    move type)). Runs in a pool worker or in-process; restores whatever `_util` module it found."""
    util_src, move_type = task
    previous = sys.modules[U_NAME]
    if util_src is None:
        sys.modules[U_NAME] = REAL_U
    else:
        _install(U_NAME, util_src, "<calc sweep: mutant _util>")
    u = sys.modules[U_NAME]
    cls = u.BattleStrategyUtil
    cur = [0]
    calls = [0]

    def fake_base(self, move, attacker, defender, is_critical_hit=False):
        calls[0] += 1
        return cur[0]

    saved_base, saved_flag = cls.__dict__["_calculate_base_move_damage"], u.get_event_flag
    cls._calculate_base_move_damage = fake_base
    u.get_event_flag = lambda name: False
    try:
        move = get_move_by_name(SWEEP_MOVES[move_type])
        out = {}
        for mt, t1, t2, stab, charge in sweep_combos((move_type,)):
            att_t = mt if stab else sweep_off_type(mt)
            st = make_state(_sweep_record(SWEEP_ATTACKER, att_t, att_t), _sweep_record(SWEEP_DEFENDER, t1, t2),
                            ours_status3=STATUS3_CHARGED_UP if charge else 0)
            bp = st.battling_pokemon
            a, d = bp[0], bp[1]
            calc = cls(st).calculate_move_damage_range
            for crit in (False, True):
                mins, maxs = array("i"), array("i")
                for B in SWEEP_BS:
                    cur[0] = B
                    r = calc(move, a, d, is_critical_hit=crit)
                    mins.append(r.min)
                    maxs.append(r.max)
                out[(mt, t1, t2, stab, charge, crit)] = (mins, maxs)
        return out, calls[0]
    finally:
        cls._calculate_base_move_damage = saved_base
        u.get_event_flag = saved_flag
        sys.modules[U_NAME] = previous


_KEYS: dict = {}


def _sweep_key(source, drop):
    """The AST of `source` without the function `drop` (comments never count): what the sweep can depend on."""
    if (source, drop) not in _KEYS:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if isinstance(body, list):
                node.body = [n for n in body if not (isinstance(n, ast.FunctionDef) and n.name == drop)]
        _KEYS[(source, drop)] = ast.dump(tree)
    return _KEYS[(source, drop)]


POOL = None
_CALC: dict = {}  # calculator sweeps by key: the real one's, plus at most one mutant's
_STATS: dict = {}  # bucket statistics by (port key, calculator key)
SWEEP_TIMES: list = []


def calc_sweep():
    """{(move type, t1, t2, stab, charge, crit): (mins, maxs) over SWEEP_BS} for the CURRENT `_util`, and the number
    of times the patched base was called. Cached per `_sweep_key(_util, "_calculate_base_move_damage")`."""
    src = CURRENT_SRC[U_NAME]
    key = _sweep_key(src, "_calculate_base_move_damage")
    if key not in _CALC:
        started = time.perf_counter()
        tasks = [(None if src == REAL_SRC[U_NAME] else src, mt) for mt in SWEEP_TYPES]
        parts = None
        if POOL is not None:
            from concurrent.futures.process import BrokenProcessPool
            try:
                parts = list(POOL.map(_calc_sweep_chunk, tasks))
            except (BrokenProcessPool, OSError) as error:
                print(f"  (the process pool failed: {type(error).__name__}: {error}; the sweep runs in-process)")
        if parts is None:
            parts = [_calc_sweep_chunk(task) for task in tasks]
        merged, calls = {}, 0
        for out, n in parts:
            merged.update(out)
            calls += n
        real_key = _sweep_key(REAL_SRC[U_NAME], "_calculate_base_move_damage")
        for stale in [k for k in _CALC if k != real_key]:  # memory: the real sweep plus at most one other
            del _CALC[stale]
        _CALC[key] = (merged, calls)
        SWEEP_TIMES.append(("calculator", time.perf_counter() - started))
    return _CALC[key]


BUCKETS = {(False, False): "NC", (True, False): "C", (False, True): "NCC", (True, True): "CC"}
#: ⚙ PRE-REGISTERED (PREDICTIONS, "The enumerated bounds"): (ours UNDER the game, max; ours OVER the game, max; the min
#: end's max |delta|), all in HP.
PREREG = {"NC": (1, 1, 1), "C": (4, 0, 4), "NCC": (4, 0, 4), "CC": (8, 0, 7)}
N_PER = {"NC": 17 * 289 * 2 * 258, "C": 17 * 289 * 2 * 258, "NCC": 289 * 2 * 258, "CC": 289 * 2 * 258}
#: The anchors each bucket's bound must reach (measured on the D rows at run time): under / over.
ANCHORS = {"NC": (("D-N1", "D-N2"), ("D-O1",)), "C": (("D-A1", "D-A3"), ()), "NCC": ((), ()), "CC": (("D-A2",), ())}


def sweep_stats():
    """Per bucket: n, and (value, witness) for under / over / min, the port vs the calculator over the whole sweep."""
    ckey = _sweep_key(CURRENT_SRC[U_NAME], "_calculate_base_move_damage")
    pkey = _sweep_key(CURRENT_SRC[P_NAME], "fixed_damage")
    if (pkey, ckey) in _STATS:
        return _STATS[(pkey, ckey)]
    calc, calls = calc_sweep()
    started = time.perf_counter()
    p = P()
    low = (-10 ** 9, None)
    stats = {b: {"n": 0, "under": low, "over": low, "min": low} for b in BUCKETS.values()}
    for mt, t1, t2, stab, charge in sweep_combos():
        att_t = mt if stab else sweep_off_type(mt)
        chg = p.charge_applies(charge, mt, mt)  # a sweep move's listed type IS its type (no Hidden Power)
        for crit in (False, True):
            s = stats[BUCKETS[(crit, charge)]]
            pmins, pmaxs = p.after_base_many(SWEEP_BS, mt, (att_t, att_t), (t1, t2), crit, chg)
            cmins, cmaxs = calc[(mt, t1, t2, stab, charge, crit)]
            if not (len(pmins) == len(pmaxs) == len(cmins) == len(cmaxs) == len(SWEEP_BS)):
                raise AssertionError(f"sweep column lengths differ at {(mt, t1, t2, stab, charge, crit)}")
            s["n"] += len(SWEEP_BS)
            for name, left, right, mapper in (("under", pmaxs, cmaxs, None), ("over", cmaxs, pmaxs, None),
                                              ("min", cmins, pmins, abs)):
                diffs = list(map(sub, left, right)) if mapper is None else list(map(abs, map(sub, left, right)))
                v = max(diffs)
                if v > s[name][0]:
                    i = diffs.index(v)
                    s[name] = (v, (mt, (t1, t2), "STAB" if stab else "no STAB", "crit" if crit else "no crit",
                                   "Charge" if charge else "no Charge", SWEEP_BS[i],
                                   (pmins[i], pmaxs[i]), (cmins[i], cmaxs[i])))
    stats["_calls"] = calls
    stats["_combos"] = sum(1 for _ in sweep_combos())
    SWEEP_TIMES.append(("port + compare", time.perf_counter() - started))
    _STATS[(pkey, ckey)] = stats
    return stats


def fmt_witness(w):
    if w is None:
        return "none"
    mt, pair, stab, crit, charge, B, game, ours = w
    return f"{mt} vs {pair[0]}/{pair[1]}, {stab}, {crit}, {charge}, B={B}: game {list(game)}, ours {ours}"


def bk_rows(tag=""):
    reds: list = []

    def sw():  # the sweep is whole: every tuple evaluated once, through the patched base, by the real calculator
        stats = sweep_stats()
        total = sum(stats[b]["n"] for b in BUCKETS.values())
        # ⚠ written as its factors after the FIRST run: the hand-multiplied literal (5,368,992) was an arithmetic slip
        # of this gate's own; the sweep enumerated exactly 17*289*2*2*258 + 289*2*2*258 = 5,368,464 (Electric's Charge)
        want_total = 17 * 289 * 2 * 2 * len(SWEEP_BS) + 289 * 2 * 2 * len(SWEEP_BS)
        ok = (SWEEP_BS == tuple(range(2, 260)) and total == want_total and stats["_calls"] == total
              and stats["_combos"] == 17 * 289 * 2 + 289 * 2
              and len(SWEEP_TYPES) == 17 and all(get_move_by_name(m).type.name == t for t, m in SWEEP_MOVES.items())
              and all(get_move_by_name(m).effect in SWEEP_TIER_A for m in SWEEP_MOVES.values())
              and set(SWEEP_MOVES) == set(SWEEP_TYPES))
        return ok, (f"{total:,} tuples, the patched base called {stats['_calls']:,} times, {stats['_combos']:,} "
                    f"combinations, {len(SWEEP_TYPES)} types")

    def bk(bucket):
        def fn():
            stats = sweep_stats()[bucket]
            got = (stats["under"][0], stats["over"][0], stats["min"][0])
            under_anchors, over_anchors = ANCHORS[bucket]
            measured = {rid: d_measure(rid) for rid in under_anchors + over_anchors}
            a_under = max([m[0][1] - m[1][1] for rid, m in measured.items() if rid in under_anchors] or [0])
            a_over = max([m[1][1] - m[0][1] for rid, m in measured.items() if rid in over_anchors] or [0])
            ok = got == PREREG[bucket] and stats["n"] == N_PER[bucket] and got[0] >= a_under and got[1] >= a_over
            detail = (f"under {got[0]} / over {got[1]} / min end {got[2]} (pre-registered {PREREG[bucket]}); "
                      f"n {stats['n']:,}; the anchors need under >= {a_under}, over >= {a_over}")
            if not tag:
                detail += "".join(f"\n          witness {name}: {fmt_witness(stats[name][1])}"
                                  for name in ("under", "over", "min"))
            return ok, detail
        return fn

    for label, fn in (("SW the sweep is whole: 17 move types x 289 ordered pairs x STAB x crit x Charge x B=2..259", sw),
                      ("BK-NC the non-crit bucket: under 1, over 1, min end 1", bk("NC")),
                      ("BK-C the crit bucket: under 4, over 0, min end 4", bk("C")),
                      ("BK-NCC the non-crit + Charge bucket: under 4, over 0, min end 4", bk("NCC")),
                      ("BK-CC the crit + Charge bucket: under 8, over 0, min end 7", bk("CC"))):
        row(label, fn, tag, reds)
    return reds


def all_rows(tag):
    return set(p_rows(tag) + d_rows(tag) + b_rows(tag) + ls_rows(tag) + bk_rows(tag))


# ------------------------------------------------------------------------------------------------------ mutants
#: The mutants. ⛔ EVERY SET BELOW WAS DERIVED ROW BY ROW FROM WHAT THE MUTANT CHANGES AND WRITTEN BEFORE THE GATE'S
#: FIRST MUTANT RUN (the derivations are in each label's comment). A set that differs on a run is a RESULT to explain,
#: never a set to re-derive to match.
_U_D1_OLD = '''        # Same-type Attack Bonus
        if move_type in attacker_types:
            damage = _percentage(damage, 150)

        # Type effectiveness
        for defender_type in defender_types:
            damage = _percentage(damage, int(100 * move_type.get_effectiveness_against(defender_type)))

        if move.name == "Dragon Rage":
            return DamageRange(40)

        if move.name == "Sonic Boom":
            return DamageRange(20)

        if move.name == "Super Fang":
            return DamageRange(max(1, defender.current_hp // 2))

        if move.name in ("Night Shade", "Seismic Toss"):
            return DamageRange(attacker.level)

        if move.name == "Psy Wave":
            return DamageRange(attacker.level, _percentage(attacker.level, 150))

        if is_critical_hit:
            damage *= 2

        if (
            isinstance(attacker, BattlePokemon)
            and TemporaryStatus.ChargedUp in attacker.status_temporary
            and move_type.name == "Electric"
        ):
            damage *= 2
'''
_U_D1_NEW = '''        if is_critical_hit:
            damage *= 2

        if (
            isinstance(attacker, BattlePokemon)
            and TemporaryStatus.ChargedUp in attacker.status_temporary
            and move_type.name == "Electric"
        ):
            damage *= 2

        # Same-type Attack Bonus
        if move_type in attacker_types:
            damage = _percentage(damage, 150)

        # Type effectiveness
        for defender_type in defender_types:
            damage = _percentage(damage, int(100 * move_type.get_effectiveness_against(defender_type)))

        if move.name == "Dragon Rage":
            return DamageRange(40)

        if move.name == "Sonic Boom":
            return DamageRange(20)

        if move.name == "Super Fang":
            return DamageRange(max(1, defender.current_hp // 2))

        if move.name in ("Night Shade", "Seismic Toss"):
            return DamageRange(attacker.level)

        if move.name == "Psy Wave":
            return DamageRange(attacker.level, _percentage(attacker.level, 150))
'''
_P_ORDER_OLD = '''        d = B * crit_mul * DMG_MULTIPLIER  # BSC:1296
        if charge_listed_electric:  # BSC:1298-1299
            d *= 2
        # --- Cmd_typecalc (BSC:1355-1424)
        if stab:  # BSC:1371-1372: `* 15` then `/ 10`, two statements
            d = d * 15 // 10
        for mul in steps:  # ModulateDmgByType (BSC:1321-1325), once per applied row, IN TABLE ORDER
            d = d * mul // 10  # BSC:1323
            if d == 0 and mul != 0:  # BSC:1324-1325: a step never takes nonzero-able damage to 0
                d = 1
'''
_P_ORDER_NEW = '''        d = B * DMG_MULTIPLIER
        if stab:
            d = d * 15 // 10
        for mul in steps:
            d = d * mul // 10
            if d == 0 and mul != 0:
                d = 1
        d = d * crit_mul
        if charge_listed_electric:
            d *= 2
'''
_P_WALK_OLD = '''    for atk, dfn, mul in TYPE_EFFECTIVENESS:
        if atk == FORESIGHT:
            if foresight:
                break
            continue
        if atk == move_type:
            if dfn == type1:
                steps.append(mul)
            if dfn == type2 and type1 != type2:
                steps.append(mul)
    return tuple(steps)
'''
_P_WALK_DEFENDER_ORDER = '''    for defender_type in ((type1,) if type1 == type2 else (type1, type2)):
        for atk, dfn, mul in TYPE_EFFECTIVENESS:
            if atk == FORESIGHT:
                if foresight:
                    break
                continue
            if atk == move_type and dfn == defender_type:
                steps.append(mul)
    return tuple(steps)
'''

CASES: list = [
    # ---- the three named mutants (PREDICTIONS, "The mutants")
    # m1: the port in OUR order. Only rows whose port call has crit or Charge move: D-A1/D-A2/D-A3 (the anchors). The
    # crit/Charge buckets shrink to type-order/per-step-minimum effects x2/x4 (under 2/2/4, not 4/4/8): BK-C, BK-NCC,
    # BK-CC. The non-crit bucket, every non-crit B row (B-HPC's and B-CHG-TACKLE's Charge is off), P2: unchanged.
    # (Follow-up) B-STAGE-CRIT and B-CRIT-REFL: port 17 -> STAB 25 -> x2 = 50 -> [42, 50], not [43, 51]: red.
    # B-SPD-CRIT has no STAB and no type row: 19 x 2 = 38 in either order: green.
    ("m1 the PORT in OUR order (crit and Charge after STAB/type) -> D-A1 D-A2 D-A3 BK-C BK-NCC BK-CC B-STAGE-CRIT "
     "B-CRIT-REFL", P_PATH, _P_ORDER_OLD, _P_ORDER_NEW,
     {"D-A1", "D-A2", "D-A3", "BK-C", "BK-NCC", "BK-CC", "B-STAGE-CRIT", "B-CRIT-REFL"}),
    # m2: `_util` with D1 FIXED. D-A1/A2/A3 flip (ours = the game: 36, 72, 60), so their OURS literal fails; the same
    # buckets shrink (only D2/D3 remain). Every non-crit B row is untouched, and B-HPC's Charge doubles 32 either
    # before or after the x2 vs Water (128 both ways): green. L1, S1, C1, P rows: untouched.
    # (Follow-up) B-STAGE-CRIT and B-CRIT-REFL: ours 17 x 2 = 34 -> STAB 51 -> (43, 51) = the game, not (42, 50): red.
    # B-SPD-CRIT: 38 either way: green. B-CHG-TACKLE: the Charge block still needs an Electric move: green.
    ("m2 _util with D1 FIXED (crit x2 and Charge x2 before STAB/type) -> D-A1 D-A2 D-A3 BK-C BK-NCC BK-CC "
     "B-STAGE-CRIT B-CRIT-REFL", U_PATH, _U_D1_OLD, _U_D1_NEW,
     {"D-A1", "D-A2", "D-A3", "BK-C", "BK-NCC", "BK-CC", "B-STAGE-CRIT", "B-CRIT-REFL"}),
    # m3: the port's walk in DEFENDER order. D-N1 (Dark/Ghost -> 6) and D-O1 (Rock/Flying -> 3) flip; D-N2 gives 1
    # either way; D-A1/A2/A3's pairs are already in table order. BK-NC's OVER bound came only from order (D-O1), so
    # it drops to 0: red. The crit/Charge bounds come from STAB x (2, 2), which no order changes: green. P2's cases
    # are order-free: green.
    ("m3 the port's type walk in DEFENDER order -> D-N1 D-O1 BK-NC", P_PATH,
     _P_WALK_OLD, _P_WALK_DEFENDER_ORDER, {"D-N1", "D-O1", "BK-NC"}),
    # ---- one per row family (the port)
    # m4: no per-step minimum. D-N2's 2 -> 1 -> 0 stays 0 (game 0). BK-NC keeps under 1 from order (D-N1), over 1
    # (D-O1), min 1 (immune pairs): green. The crit/Charge buckets start at d >= 4, so no step reaches 0: green.
    ("m4 the port without the per-step minimum -> D-N2", P_PATH,
     "            if d == 0 and mul != 0:  # BSC:1324-1325: a step never takes nonzero-able damage to 0\n"
     "                d = 1\n", "", {"D-N2"}),
    # m5: Charge read from the ROLLED type. B-HPC's port doubles (-> 128). D-A2 and the sweep have listed == rolled.
    ("m5 the port applies Charge on the rolled Hidden Power type -> B-HPC", P_PATH,
     '    return bool(charged) and listed_type == "Electric"',
     '    return bool(charged) and move_type == "Electric"', {"B-HPC"}),
    # m6: Struggle not skipped. B-STR's port takes STAB and Normal->Ghost 0 (-> 0). Nothing else passes struggle.
    ("m6 the port without Struggle's skip -> B-STR", P_PATH, "    if struggle:\n", "    if False:\n", {"B-STR"}),
    # m7: Psywave's floor at the level (our calculator's reading). Only B-PSY calls it.
    ("m7 a wrong Psywave floor (the level, not level/2) -> B-PSY", P_PATH,
     "        return level * 50 // 100, level * 150 // 100", "        return level, level * 150 // 100", {"B-PSY"}),
    # m8: fixed damage without typecalc's immunity. B-NS/B-ST/B-SF deal 30/30/100; B-SONIC/B-PSY hit non-immune types.
    ("m8 the port's fixed damage ignores a x0 type -> B-NS B-ST B-SF", P_PATH,
     "    if 0 in type_steps(move_type, type1, type2, foresight):\n        return 0, 0\n", "",
     {"B-NS", "B-ST", "B-SF"}),
    # m9: the sentinel read as the table's END (the post-sentinel Normal/Fighting -> Ghost rows never apply). B-ST and
    # B-SF stop being immune; B-NS's Ghost->Normal row is before the sentinel. P2's "Normal vs Ghost" deals damage.
    # The non-crit and crit buckets see Normal/Fighting hit Ghosts (the game now far above ours' (1, 0)); Electric
    # (the Charge buckets) has no Ghost row: green.
    ("m9 the port stops at the Foresight sentinel -> B-ST B-SF P2 BK-NC BK-C", P_PATH,
     "        if atk == FORESIGHT:\n            if foresight:\n                break\n            continue\n",
     "        if atk == FORESIGHT:\n            break\n", {"B-ST", "B-SF", "P2", "BK-NC", "BK-C"}),
    # m10: STAB from type1 only. D-A3's attacker is Water/Ground (Ground is type2) -> no STAB (40). Every other row's
    # and the sweep's attacker is a mono-type.
    ("m10 the port's STAB reads only the attacker's type1 -> D-A3", P_PATH,
     "        stab = move_type in tuple(attacker_types)", "        stab = move_type == tuple(attacker_types)[0]",
     {"D-A3"}),
    # m11: no floor at 1 in the random factor. D-N2's d = 1 -> min 0. A d of 1 in the sweep only raises a |min delta|
    # to 1, inside every bucket's bound.
    ("m11 the port's random factor without its floor at 1 -> D-N2", P_PATH,
     "            mins.append(d * 85 // 100 or 1)  # the r = 15 end (85%)",
     "            mins.append(d * 85 // 100)  # the r = 15 end (85%)", {"D-N2"}),
    # m12: a no-effect hit reported as gBattleMoveDamage. P2's Ground vs Flying/Rock reads (1, 1). In the sweep such a
    # tuple is (1, 1) vs ours (1, 0): under 1, inside every bound; the immune (0, 0) tuples keep the min end at 1.
    ("m12 the port reports gBattleMoveDamage on a no-effect hit -> P2", P_PATH,
     "        if no_effect:\n            mins.append(0)\n            maxs.append(0)\n            continue\n", "",
     {"P2"}),
    # ---- one per row family (the calculator: each is the FIX its row pins, so `#27-dmgcalcfix` turns exactly it red)
    ("u1 _util: Marvel Scale keyed on the DEFENDER's status -> B-MS1 B-MS2", U_PATH,
     '        if defender.ability.name == "Marvel Scale" and attacker_status is not StatusCondition.Healthy:',
     '        if defender.ability.name == "Marvel Scale" and defender_status is not StatusCondition.Healthy:',
     {"B-MS1", "B-MS2"}),
    ("u2 _util: no burn halving under Guts -> B-GUTS", U_PATH,
     "            if attacker_status is StatusCondition.Burn:\n",
     '            if attacker_status is StatusCondition.Burn and attacker.ability.name != "Guts":\n', {"B-GUTS"}),
    ("u3 _util: Brick Break ignores Reflect -> B-BB", U_PATH,
     "            if defender_side.reflect_timer.turns_remaining > 0 and not is_critical_hit:",
     '            if defender_side.reflect_timer.turns_remaining > 0 and not is_critical_hit and move.effect != '
     '"BRICK_BREAK":', {"B-BB"}),
    # u4: BADGE07 (not 08) boosts our Sp. Def. B7 set -> (22, 27); B8 set -> (23, 28); BADGE08 no longer queried.
    ("u4 _util: KI-110 fixed (BADGE07 boosts our Sp. Def) -> B-KI110-B7 B-KI110-B8", U_PATH,
     '        if get_event_flag("BADGE08_GET") and defender_is_player:',
     '        if get_event_flag("BADGE07_GET") and defender_is_player:', {"B-KI110-B7", "B-KI110-B8"}),
    ("u5 _util: KI-111 fixed (the data's spelling Solarbeam) -> B-KI111", U_PATH,
     'move.name == "Solar Beam"', 'move.name == "Solarbeam"', {"B-KI111"}),
    # u6: the badge read cut from the calculator: L1 sees no change. No other row sets BADGE01.
    ("u6 _util: BADGE01 never read (the stub goes dead) -> L1", U_PATH,
     '        if get_event_flag("BADGE01_GET") and attacker_is_player:',
     "        if False and attacker_is_player:", {"L1"}),
    # ---- comment-only edits: NOTHING red (a row must not fire on a mention)
    ("N1 a comment in _util naming the crit order turns NOTHING red", U_PATH,
     "        # Same-type Attack Bonus\n",
     "        # (edited) is_critical_hit: damage *= 2 happens below; D1, D2, D3 named in a comment only\n"
     "        # Same-type Attack Bonus\n", set()),
    ("N2 a comment in the port naming our order turns NOTHING red", P_PATH,
     "        # --- Cmd_typecalc (BSC:1355-1424)\n",
     "        # (edited) d = d * crit_mul after the steps, in a comment only\n"
     "        # --- Cmd_typecalc (BSC:1355-1424)\n", set()),
    # ======== FOLLOW-UP (the adversarial mutant pass, 72 mutants). Every set below was derived row by row, INCLUDING
    # the new rows, and written BEFORE the first run that contained it. Ids are the pass's (U18, U19, ...).
    # U18: the WRONG Guts "fix": the burn halving deleted outright. B-BURN (Zigzagoon, Pickup, burned): 15 + 2 = 17 ->
    # STAB 25 -> (21, 25), not (11, 13). B-GUTS: 26 + 2 = 28 -> STAB 42 -> (35, 42), not (18, 22). No other row has a
    # burned ATTACKER (B-MS1's burn is the defender's). The sweep patches the base: cached, green.
    ("U18 _util: the burn halving deleted (a WRONG Guts fix) -> B-BURN B-GUTS", U_PATH,
     "            # Burn cuts attack in half\n            if attacker_status is StatusCondition.Burn:\n"
     "                damage //= 2\n\n", "", {"B-BURN", "B-GUTS"}),
    # U19: the WRONG Brick Break "fix": the physical Reflect block deleted. B-REFL: 17 -> 25 -> (21, 25). B-BB: 35 ->
    # 52 -> 104 -> (88, 104). B-CRIT-REFL: a crit already skipped Reflect: green.
    ("U19 _util: the Reflect block deleted (a WRONG Brick Break fix) -> B-REFL B-BB", U_PATH,
     "            # Reflect\n"
     "            if defender_side.reflect_timer.turns_remaining > 0 and not is_critical_hit:\n"
     "                if self._battle_state.is_double_battle and defender_partner is not None:\n"
     "                    damage = 2 * (damage // 3)\n"
     "                else:\n"
     "                    damage //= 2\n\n", "", {"B-REFL", "B-BB"}),
    # U17: the WRONG KI-110 "fix": BADGE07 retargeted to OUR Sp. Def, BADGE08 dropped (our Sp. Atk boost is lost).
    # B-KI110-B7: our SpD 110 -> 18 -> (22, 27), not (23, 28). B-KI110-B8: nothing -> (23, 28), not (22, 27).
    # B-KI110-SPA: SpA 100 -> 19 -> STAB 28 -> (23, 28), not (26, 31). No other row sets a badge 7/8 flag.
    ("U17 _util: BADGE07 retargeted to Sp. Def, BADGE08 dropped (a WRONG KI-110 fix) -> B-KI110-B7 B-KI110-B8 "
     "B-KI110-SPA", U_PATH,
     '        if get_event_flag("BADGE07_GET") and attacker_is_player:\n'
     "            special_attack = _percentage(special_attack, 110)\n"
     '        if get_event_flag("BADGE08_GET") and defender_is_player:\n'
     "            special_defence = _percentage(special_defence, 110)\n",
     '        if get_event_flag("BADGE07_GET") and defender_is_player:\n'
     "            special_defence = _percentage(special_defence, 110)\n",
     {"B-KI110-B7", "B-KI110-B8", "B-KI110-SPA"}),
    # U38: BADGE07's Sp. Atk 110 -> 100. B-KI110-SPA -> (23, 28). B-KI110-B7's attacker is the FOE (never boosted).
    ("U38 _util: BADGE07's Sp. Atk boost 110 -> 100 -> B-KI110-SPA", U_PATH,
     "            special_attack = _percentage(special_attack, 110)",
     "            special_attack = _percentage(special_attack, 100)", {"B-KI110-SPA"}),
    # U20: Reflect halves crits. B-CRIT-REFL: 15 -> 7, +2 = 9 -> STAB 13 -> x2 = 26 -> (22, 26). The non-crit Reflect
    # rows (B-REFL, B-BB) are unchanged.
    ("U20 _util: Reflect halves a crit too -> B-CRIT-REFL", U_PATH,
     "            if defender_side.reflect_timer.turns_remaining > 0 and not is_critical_hit:",
     "            if defender_side.reflect_timer.turns_remaining > 0:", {"B-CRIT-REFL"}),
    # U21: the negative-stage denominator x5 -> x10 (the module prelude, so the sweep re-runs: it never calls it).
    # B-STAGE: 100*10/20 = 50 -> 7, +2 = 9 -> 13 -> (11, 13), not (15, 18). B-STAGE-CRIT takes the raw Atk on a crit;
    # every other row's stages are 0 (10/10) or positive (the numerator): green.
    ("U21 _util: the stage denominator x5 -> x10 -> B-STAGE", U_PATH,
     "    return original_stat * (10 + max(0, modifier_level) * 5) // (10 + abs(min(0, modifier_level)) * 5)",
     "    return original_stat * (10 + max(0, modifier_level) * 5) // (10 + abs(min(0, modifier_level)) * 10)",
     {"B-STAGE"}),
    # U22: the crit Atk-stage rule inverted (`<= 0` -> `> 0`). B-STAGE-CRIT: stage -1 now applied: 66 -> 10, +2 = 12
    # -> 18 -> x2 = 36 -> (30, 36). B-CRIT-REFL's stage is 0 (raw == modified): green.
    ("U22 _util: the crit Atk-stage rule inverted -> B-STAGE-CRIT", U_PATH,
     "                if is_critical_hit and attacker.stats_modifiers.attack <= 0:",
     "                if is_critical_hit and attacker.stats_modifiers.attack > 0:", {"B-STAGE-CRIT"}),
    # U32: the crit Sp.Def-stage rule inverted (`> 0` -> `<= 0`). Only B-SPD-CRIT (the row added for it) has a
    # nonzero defender SpD stage on a special crit: +1 now applied: 150 -> 586 / 50 = 11, +2 = 13 -> x2 = 26 -> (22, 26).
    ("U32 _util: the crit Sp.Def-stage rule inverted -> B-SPD-CRIT", U_PATH,
     "            if is_critical_hit and isinstance(defender, BattlePokemon) and "
     "defender.stats_modifiers.special_defence > 0:",
     "            if is_critical_hit and isinstance(defender, BattlePokemon) and "
     "defender.stats_modifiers.special_defence <= 0:", {"B-SPD-CRIT"}),
    # U05: the PHYSICAL level factor as 2 * (level // 5) + 2 (the first of the two identical lines). Only B-LVL (L8:
    # 4, not 5) is at a level that is not a multiple of 5: 100*35*4/100/50 = 2, +2 = 4 -> STAB 6 -> (5, 6).
    ("U05 _util: the physical level factor 2 * (level // 5) + 2 -> B-LVL", U_PATH,
     "            damage *= move_power\n            damage *= 2 * attacker.level // 5 + 2\n\n"
     "            if isinstance(defender, BattlePokemon):",
     "            damage *= move_power\n            damage *= 2 * (attacker.level // 5) + 2\n\n"
     "            if isinstance(defender, BattlePokemon):", {"B-LVL"}),
    # U03: Super Fang on total_hp. B-SF2 (150/200) -> 100. B-SF's foe is at 200/200 (and immune in the game): its OURS
    # is 100 either way. The sweep re-runs (calculate_move_damage_range changed) and uses no Super Fang.
    ("U03 _util: Super Fang halves total_hp -> B-SF2", U_PATH,
     "            return DamageRange(max(1, defender.current_hp // 2))",
     "            return DamageRange(max(1, defender.total_hp // 2))", {"B-SF2"}),
    # U01: Charge on every type. B-CHG-TACKLE: 25 x 2 = 50 -> (42, 50). D-A2 and B-HPC already double (Electric);
    # the sweep charges only Electric moves: identical, green.
    ("U01 _util: Charge doubles every type -> B-CHG-TACKLE", U_PATH,
     "            and TemporaryStatus.ChargedUp in attacker.status_temporary\n"
     '            and move_type.name == "Electric"\n',
     "            and TemporaryStatus.ChargedUp in attacker.status_temporary\n", {"B-CHG-TACKLE"}),
    # U43: the Dragon Rage branch deleted. B-DR falls through: base 0 + 2 = 2 (special, no floor) -> (1, 2).
    ("U43 _util: the Dragon Rage branch deleted -> B-DR", U_PATH,
     '        if move.name == "Dragon Rage":\n            return DamageRange(40)\n\n', "", {"B-DR"}),
    # ---- the port's non-immune fixed-damage branches (they never ran before the follow-up rows)
    ("P-SF4 the port's Super Fang // 4 -> B-SF2", P_PATH,
     "        half = max(1, target_hp // 2)", "        half = max(1, target_hp // 4)", {"B-SF2"}),
    # LEVEL_DAMAGE x2: B-NS2 and B-ST2 deal 60. B-NS and B-ST are immune (0) before the branch: green.
    ("P-LD2 the port's level damage x2 -> B-NS2 B-ST2", P_PATH,
     "        return level, level", "        return level * 2, level * 2", {"B-NS2", "B-ST2"}),
    ("P-DR20 the port's Dragon Rage 20 -> B-DR", P_PATH,
     "        return 40, 40", "        return 20, 20", {"B-DR"}),
    # ---- GATE SELF-PROTECTION: each is caught ONLY through a gate check the pass showed could be hollowed unnoticed
    # u7 = U23: the base called WITHOUT is_critical_hit. The D rows' base-call assert fires on the crit anchors (D-A1,
    # D-A2, D-A3); the real base then applies Reflect (B-CRIT-REFL: (22, 26)), the lost Atk stage (B-STAGE-CRIT:
    # (30, 36)) and the SpD +1 (B-SPD-CRIT: (22, 26)). The sweep's patched base ignores the argument: identical.
    # ⚠ CORRECTED after its FIRST run (2026-09-30), not re-derived to match: the pre-written set omitted BK-C and
    # BK-CC. Those rows re-measure their anchors through `d_measure` (the same base-call assert), and their anchors are
    # the crit rows (BK-C: D-A1, D-A3; BK-CC: D-A2), so they raise. BK-NC (non-crit anchors) and BK-NCC (no anchor)
    # stayed green, which confirms the cause. The first-run set was exactly this one.
    ("u7 _util: the base called without is_critical_hit (U23) -> D-A1 D-A2 D-A3 B-STAGE-CRIT B-CRIT-REFL B-SPD-CRIT "
     "BK-C BK-CC", U_PATH,
     "        damage = self._calculate_base_move_damage(move, attacker, defender, is_critical_hit)",
     "        damage = self._calculate_base_move_damage(move, attacker, defender)",
     {"D-A1", "D-A2", "D-A3", "B-STAGE-CRIT", "B-CRIT-REFL", "B-SPD-CRIT", "BK-C", "BK-CC"}),
    # u8 = U11: the min's max(1, ...) removed. Only where ours' damage is 0 or 1 does the min change: D-N2, B-STR and
    # B-FORESIGHT read (0, 0), not (1, 0); their deltas (on the max) do not move, so ONLY `calc == ours` catches it.
    # The sweep's bounds: every |min delta| stays inside 1/4/4/7 and the maxes are untouched: green.
    ("u8 _util: the min's max(1, ...) removed (U11) -> D-N2 B-STR B-FORESIGHT", U_PATH,
     "        return DamageRange(max(1, _percentage(damage, 85)), damage)",
     "        return DamageRange(_percentage(damage, 85), damage)", {"D-N2", "B-STR", "B-FORESIGHT"}),
    # u9 = U36: BADGE01 110 -> 120. L1's badge arm reads (25, 30), not (22, 27); no other row sets BADGE01.
    ("u9 _util: BADGE01's boost 110 -> 120 (U36) -> L1", U_PATH,
     "            attack = _percentage(attack, 110)", "            attack = _percentage(attack, 120)", {"L1"}),
]


def case_verdict(red, want):
    """A mutant passes only when it reddens EXACTLY its set: more is as wrong as fewer (row C1 pins this)."""
    return set(red) == set(want)


def _make_pool():
    try:
        from concurrent.futures import ProcessPoolExecutor

        return ProcessPoolExecutor(max_workers=max(1, min(len(SWEEP_TYPES), os.cpu_count() or 1)))
    except Exception as error:  # noqa: BLE001 - no pool is not a failure: the sweep runs in-process
        print(f"  (no process pool: {type(error).__name__}: {error}; the sweep runs in-process)")
        return None


def main() -> int:
    global POOL
    started = time.perf_counter()
    POOL = _make_pool()
    try:
        print("P — the port's own table and walk");                                        p_rows()
        print("\nD — after the base (B given): the port AND the real calculator");        d_rows()
        print("\nB — the base term: the real calculator on real objects");                 b_rows()
        print("\nL/S/C — the flag stub is live; the side check refuses a stand-in; the comparator is exact"); ls_rows()
        print("\nBK — the enumerated buckets (the real calculator, its base patched, vs the port)"); bk_rows()
        print(f"\n  (rows took {time.perf_counter() - started:.1f} s; sweeps: "
              + ", ".join(f"{name} {secs:.1f} s" for name, secs in SWEEP_TIMES) + ")")
        print("\nM — mutants (each must turn EXACTLY its named rows red)")
        for i, (label, path, old, new, want) in enumerate(CASES):
            name = U_NAME if path == U_PATH else P_NAME
            t_case = time.perf_counter()
            try:
                src = REAL_SRC[name]
                n = src.count(old)
                if n != 1:
                    raise AssertionError(f"mutant anchor found {n} times: {old[:80]!r}")
                msrc = src.replace(old, new)
                _install(name, msrc, f"<mutant {i}>")
                CURRENT_SRC[name] = msrc
                red = all_rows("m")
                verdict = case_verdict(red, want)
                check(label, verdict, f"red {sorted(red)}" + ("" if verdict else f" (want {sorted(want)})")
                      + f" [{time.perf_counter() - t_case:.1f} s]")
            except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
                check(label, False, f"{type(error).__name__}: {error}")
            finally:
                sys.modules[U_NAME], sys.modules[P_NAME] = REAL_U, REAL_P
                CURRENT_SRC.update(REAL_SRC)
    finally:
        if POOL is not None:
            POOL.shutdown()
    print(f"\n  (total {time.perf_counter() - started:.1f} s)")
    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
