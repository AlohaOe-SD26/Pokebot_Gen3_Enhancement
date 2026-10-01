r"""GATE G-D13 — design v2 step 13 (KB-2, healing items in DOUBLE battles; `ai-research-notes/2026-09-30-doubleitems13-
DESIGN.md` C1-C7 and §7): the pure `modules/story/double_items.py`; the strategy half in
`plugins/custom_modes/story_mode.py` (`StoryItemBattleStrategy.decide_turn_in_double_battle`, `_dbl_act`,
`_dbl_observe`, and `_maybe_use_item`'s `side` / `doubles`); the executor half in `modules/battle_action_selection.py`
(C4's identity guard, the `menu` / `after` lines, D11's Struggle-loop exit); and C1 in `modules/battle_menuing.py`.

WHY. A double has TWO of our Pokémon choosing, and every index in the item path has two spaces (the strategy's side
{0, 1} against the game's battler id {0, 2}; the party index against the in-menu slot). A wrong one does not fail loudly:
in a double the wrong slot is often the LIVING partner, which takes the item silently (the adversary's F3). So every row
below EXECUTES production on fakes and asserts IDENTITY — PIDs — never a count or a position (rule 3), and every
pre-registered row asserts the outcome `ai-research-notes/2026-09-30-doubleitems13-PREDICTIONS.md` filed BEFORE the code
existed.

ROWS
  DP01-DP07  the pre-registered PURE rows, `double_items` executed on plain inputs.
  DQ01-DQ10  the pre-registered STRATEGY rows: the REAL `StoryItemBattleStrategy` (built with the real `__init__`) on a
             REAL double `BattleState` built from raw `gBattleMons` records — left Sceptile, party 1, PID 863B0917;
             right Mightyena, party 4, PID 5C96EA9B (both DISCRIMINATING: neither party index equals its side) — with
             `read_symbol`, the bag, the opponent reader, the logger, the parent's double turn (a PARENT sentinel) and
             `get_battle_state` (REBOUND wherever bound, counted) faked. Bag Potion ×1 unless stated.
  DQ11-DQ17  the pre-registered EXECUTOR rows: the REAL `battle_action_use_item` / `battle_action_use_move` /
             `scroll_to_battle_action` driven frame by frame against `Game`, a small stand-in for the in-battle item
             flow (the action cursor, the bag, the party menu in MENU order while open and FIELD order after, the cursor
             opening on slot 0, the medicine applied to whatever PID sits at the cursor when A is pressed — G1/G2).
  DB*        BUILDER-ADDED rows (NOT pre-registered, each labelled), added so every rule has a row a mutant can
             redden: the `use` line, the fail-open, the ledger fields, the KI-101 judge's side (P6's retry-then-disable
             shape), the observe row's fields / tracker / key / `disc` / scope, the singles cure (D10 is doubles-only),
             the signature, the executor's self binding, its fail-closed read, its menu-open precondition and its
             double-only test, C1's callers by AST, `battle_action_use_move`'s side, D11 being battler 0's only, and two
             pure helpers (the heal-fraction parse, the `why=` reason).
FAULTS      the three C7 production envs (never set in a real run; `29-DISABLED-FEATURES-REGISTRY.md`), each with the
            EXACT red set the PREDICTIONS filed: CURSOR0 {DQ11, DQ12}; WRONGSLOT {DQ13}; NOGUARD {DQ15}. ⇒ DQ14's refusal
            comes from the RANGE check (the scroll stops on Cancel, slot 7), which NOGUARD — skipping only the PID
            comparison — keeps; so NOGUARD leaves DQ14 green (the builder's statement the PREDICTIONS asked for).
MUTANTS     exec'd source edits (never written to disk) of the four files, one per rule, each with an EXACT red set
            written BEFORE its first run. Two mention-only edits (a comment that writes the code) must turn NOTHING red:
            a gate that fires on a comment teaches the reader to bypass it. COVERAGE fails if any row is in no fault's or
            mutant's set. Jobs run in a process pool, in-process if no pool can be made (`--inprocess` forces it).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 -u probe_double_items.py [--inprocess]     (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import contextlib
import copy
import json
import os
import pathlib
import re
import struct
import sys
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a stream without reconfigure keeps its own encoding
    pass

import modules.story  # noqa: E402
import modules.story.double_items  # noqa: E402,F401  (always read via sys.modules: a mutant is exec'd there)
import modules.story.battle_items  # noqa: E402
import modules.story.league_reserve  # noqa: E402
import modules.story.trainer_identity as TI  # noqa: E402
import modules.battle_menuing  # noqa: E402,F401
import modules.battle_action_selection  # noqa: E402,F401
import modules.battle_state  # noqa: E402
import modules.battle_strategies.default  # noqa: E402
import modules.debug_logger  # noqa: E402
import modules.items  # noqa: E402
import modules.memory  # noqa: E402
import modules.pokemon_party  # noqa: E402
import plugins.custom_modes  # noqa: E402
import plugins.custom_modes.story_mode  # noqa: E402,F401
from modules.battle_state import BattleState  # noqa: E402
from modules.battle_strategies import TurnAction  # noqa: E402
from modules.items import get_item_by_name  # noqa: E402
from modules.memory import GameState  # noqa: E402
from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER  # noqa: E402

DBL_NAME, SM_NAME = "modules.story.double_items", "plugins.custom_modes.story_mode"
BAS_NAME, BM_NAME = "modules.battle_action_selection", "modules.battle_menuing"
NAMES = {"dbl": DBL_NAME, "sm": SM_NAME, "bas": BAS_NAME, "bm": BM_NAME}
PATHS = {"dbl": SANDBOX / "modules" / "story" / "double_items.py",
         "sm": SANDBOX / "plugins" / "custom_modes" / "story_mode.py",
         "bas": SANDBOX / "modules" / "battle_action_selection.py",
         "bm": SANDBOX / "modules" / "battle_menuing.py"}

FLAG, KEYITEMS, FRAC = "POKEBOT_R27_DOUBLEITEMS", "POKEBOT_R27_KEYITEMS", "POKEBOT_HEAL_AT_FRACTION"
F_CURSOR0 = "POKEBOT_R27_FAULT_DBL_CURSOR0"
F_WRONGSLOT = "POKEBOT_R27_FAULT_DBL_WRONGSLOT"
F_NOGUARD = "POKEBOT_R27_FAULT_DBL_NOGUARD"
#: The envs a ROW sets. ⛔ The three C7 faults are NOT here: a job sets one for the whole row pass, and a world that
#: cleared it would silently run the fault-free code (the fault would then "redden nothing").
ROW_ENVS = (FLAG, KEYITEMS, FRAC, "POKEBOT_R27_FAULT_RAISE", "POKEBOT_R27_FAULT_ALLORDINARY")
FAULT_ENVS = (F_CURSOR0, F_WRONGSLOT, F_NOGUARD)

with open(SANDBOX / "modules" / "data" / "species.json", encoding="utf-8") as _fh:
    SPECIES_ID = {s["name"]: i for i, s in enumerate(json.load(_fh))}   # the GATE's own copy of the ids

FAILURES: list[str] = []
ROW_NAMES: set = set()


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def row(label, fn, tag, reds):
    rid = label.split()[0]
    ROW_NAMES.add(rid)
    try:
        ok, detail = fn()
    except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
        ok, detail = False, f"raised {type(error).__name__}: {error}"
    if not ok:
        reds.append(rid)
    if not tag:
        check(label, ok, detail)


def DBL():
    return sys.modules[DBL_NAME]


def SM():
    return sys.modules[SM_NAME]


def BAS():
    return sys.modules[BAS_NAME]


def BM():
    return sys.modules[BM_NAME]


# ============================================================================================================== data
ITEM = {n: get_item_by_name(n) for n in ("Potion", "Super Potion", "Hyper Potion", "Full Heal", "Awakening",
                                          "Full Restore", "X Attack", "Repel")}
POTION = ITEM["Potion"]
PARENT = ("PARENT", None)
#: OUR two battlers. ⭐ Both DISCRIMINATE: party 1 at side 0, party 4 at side 1, so an index-space mix-up gives a
#: different answer (D8). The PIDs are the Step-0 fixture's (Sceptile, Mightyena).
L_PID, R_PID, O1_PID, O3_PID = 0x863B0917, 0x5C96EA9B, 0x0C1A7D01, 0x05017D03
L_IDX, R_IDX = 1, 4
BPI_RAW = struct.pack("<4H", L_IDX, 0, R_IDX, 1)                     # gBattlerPartyIndexes, u16[4]
TRAINER, DOUBLE, MULTI, PARTNER = 1 << 3, 1 << 0, 1 << 6, 1 << 22


class Slot:
    def __init__(self, item, quantity):
        self.item, self.quantity = item, quantity


class Bag:
    """A bag pocket with real `Item` objects (so `battle_use is ItemBattleUse.Healing` is the production test)."""

    def __init__(self, *pairs):
        self.items = [Slot(ITEM[n], q) for n, q in pairs]

    def quantity_of(self, item):
        return sum(s.quantity for s in self.items if s.item is item)


def mon_rec(species, hp, maxhp, pid, status1=0, level=40) -> bytes:
    """A 0x58-byte `struct BattlePokemon` (include/battle.h): species 0x00, moves 0x0C, PP 0x24, HP 0x28, level 0x2A,
    max HP 0x2C, PID 0x48, status1 0x4C."""
    raw = bytearray(0x58)
    struct.pack_into("<H", raw, 0x00, species)
    struct.pack_into("<4H", raw, 0x0C, 33, 0, 0, 0)
    raw[0x24] = 35
    struct.pack_into("<H", raw, 0x28, hp)
    raw[0x2A] = level
    struct.pack_into("<H", raw, 0x2C, maxhp)
    struct.pack_into("<II", raw, 0x48, pid, status1)
    return bytes(raw)


def pack_order(order) -> bytes:
    return bytes(((order[i] & 0xF) << 4) | (order[i + 1] & 0xF) for i in (0, 2, 4))


def dstate(*, lhp=90, rhp=90, lst=0, flags=TRAINER | DOUBLE, turn=3, order=(1, 4, 0, 2, 3, 5), bpi=None,
           single=False) -> BattleState:
    """A REAL double `BattleState`: our left Sceptile (party 1) and right Mightyena (party 4), both /100, against a
    Claydol and a Solrock. `lst` is the left battler's status1 (2 = asleep); `bpi` overrides gBattlerPartyIndexes;
    `single` makes it a SINGLE trainer battle (two battlers, no Double bit)."""
    battler = mon_rec(SPECIES_ID["Sceptile"], lhp, 100, L_PID, lst) + mon_rec(SPECIES_ID["Claydol"], 80, 80, O1_PID)
    if not single:
        battler += mon_rec(SPECIES_ID["Mightyena"], rhp, 100, R_PID) + mon_rec(SPECIES_ID["Solrock"], 80, 80, O3_PID)
    return BattleState(battle_type=struct.pack("<I", TRAINER if single else flags), side_timers=bytes(24),
                       battler_party_indexes=BPI_RAW if bpi is None else struct.pack("<4H", *bpi),
                       battler_party_order=pack_order(order), battler_count=2 if single else 4, battler=battler,
                       battler_status3=bytes(16), battler_disable_structs=bytes(0x70), absent_battler_flags=0,
                       current_turn=turn, weather=0)


def use(item, target):
    return TurnAction.UseItem, (item, target)


class _Mon(types.SimpleNamespace):
    pass


class FakeParty(list):
    @property
    def first_non_fainted(self):
        return next((m for m in self if m.current_hp > 0), None)


PARTY6 = FakeParty(_Mon(index=i, is_egg=False, current_hp=50) for i in range(6))


def new_strategy():
    """The REAL class, built by its real `__init__` (its base reads `get_party()`, faked here)."""
    default = modules.battle_strategies.default
    saved = default.get_party
    default.get_party = lambda: PARTY6
    try:
        return SM().StoryItemBattleStrategy()
    finally:
        default.get_party = saved


ORIG_GBS = modules.battle_state.get_battle_state
BS_PTR = 0x0200_0010                                                   # Step 0's measured `*gBattleStruct`
#: EWRAM behind `*gBattleStruct`: `battlerPartyOrders[4][3]` at +0x60 — DIFFERENT per side (ours [1,4,0,2,3,5],
#: theirs [0..5]) and a distinct `+0x58` copy, so a wrong stride, offset or a missed dereference reads other bytes.
EWRAM = {}
for _i, _b in enumerate(bytes.fromhex("0100040002000000") + pack_order((1, 4, 0, 2, 3, 5)) + pack_order(range(6))
                        + pack_order((1, 4, 0, 2, 3, 5)) + pack_order(range(6))):
    EWRAM[BS_PTR + 0x58 + _i] = _b


@contextlib.contextmanager
def _env(values):
    saved = {k: os.environ.get(k) for k in ROW_ENVS}
    try:
        for k in ROW_ENVS:
            os.environ.pop(k, None)
        os.environ.update(values or {})
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def _patched(patches):
    saved = [(m, n, getattr(m, n)) for m, n, _f in patches]
    try:
        for m, n, f in patches:
            setattr(m, n, f)
        yield
    finally:
        for m, n, f in reversed(saved):
            setattr(m, n, f)


# ============================================================================================================ STRATEGY
@contextlib.contextmanager
def sworld(*, env=None, state=None, fresh=None, bag=None, cls=0x20, reserve=None, mui_raises=False,
           cursor=bytes([0, 0, 1, 0])):
    """Production's world for the STRATEGY rows: the env (the row's flags only), `read_symbol` over fake symbols
    (recorded), EWRAM behind `*gBattleStruct` (recorded), the bag (counted), the opponent reader (counted; trainer 271,
    class `cls`), the RULING 18 reserve (identity unless given), the logger (recorded), `choose_healing_item` spied
    (its `options` recorded), `_maybe_use_item` and `_r27_key_gate` spied (counted), the parent's double turn (PARENT),
    and `get_battle_state` REBOUND wherever bound (counted; it returns `fresh`, else `state`)."""
    sm = SM()
    log = types.SimpleNamespace(events=[], reads=[], ebytes=[], gbs=0, mui=0, kg=0, ti=0, bag=0, hp_opts=[])
    bag = Bag(("Potion", 1)) if bag is None else bag
    syms = {"gBattleStruct": struct.pack("<I", BS_PTR), "gActionSelectionCursor": bytes(cursor),
            "gBattlerPartyIndexes": BPI_RAW}

    def fake_read(name, offset=0, size=0):
        log.reads.append(name)
        data = syms[name]
        return data[offset:offset + (size or len(data))]

    def fake_bytes(address, length):
        log.ebytes.append(address)
        return bytes(EWRAM.get(address + i, 0xEE) for i in range(length))

    def fake_event(message, *, category="STORY"):
        log.events.append((category, message))

    def fake_bag():
        log.bag += 1
        return bag

    def fake_gbs(*_a, **_k):
        log.gbs += 1
        return fresh if fresh is not None else state

    def fake_reader(_two):
        log.ti += 1
        return 271, None

    real_mui = sm.StoryItemBattleStrategy.__dict__["_maybe_use_item"]
    real_kg = sm._r27_key_gate
    real_chi = modules.story.battle_items.choose_healing_item

    def spy_mui(self, *a, **k):
        log.mui += 1
        if mui_raises:
            raise RuntimeError("the policy raised")
        return real_mui(self, *a, **k)

    def spy_kg(strategy, battle_state):
        log.kg += 1
        return real_kg(strategy, battle_state)

    def spy_chi(current_hp, total_hp, options, **kw):
        log.hp_opts.append(list(options))
        return real_chi(current_hp, total_hp, options, **kw)

    patches = [(modules.memory, "read_symbol", fake_read), (modules.items, "get_item_bag", fake_bag),
               (modules.debug_logger, "event", fake_event), (TI, "read_opponent_trainers", fake_reader),
               (TI, "trainer_class", lambda _tid, *_a, **_k: cls),
               (modules.story.league_reserve, "filter_medicine_for_reserve", reserve or (lambda medicine: medicine)),
               (modules.story.battle_items, "choose_healing_item", spy_chi),
               (modules.pokemon_party, "get_party", lambda: PARTY6),
               (sm, "context", types.SimpleNamespace(emulator=types.SimpleNamespace(read_bytes=fake_bytes))),
               (sm, "_r27_key_gate", spy_kg), (sm.StoryItemBattleStrategy, "_maybe_use_item", spy_mui),
               (sm.LevelUpTravelBattleStrategy, "decide_turn_in_double_battle", lambda _s, _bs, _bi: PARENT)]
    for mod in list(sys.modules.values()):
        if isinstance(mod, types.ModuleType) and mod.__dict__.get("get_battle_state") is ORIG_GBS:
            patches.append((mod, "get_battle_state", fake_gbs))
    with _env(env), _patched(patches):
        yield log


def lines(log, category):
    return [m for c, m in log.events if c == category]


def dbl_events(log):
    return [(c, m) for c, m in log.events if "DBLITEM" in c or "DBLITEM" in m]


def field(message, key):
    m = re.search(rf"(?:^| ){re.escape(key)}=(\S+)", message)
    return m.group(1) if m else None


def strategy_rows(tag=""):
    reds: list = []

    def dq01():
        s = new_strategy()
        st = dstate(lhp=20)                                       # with the flag ON this would heal: a leak shows
        before = copy.deepcopy(s.__dict__)
        with sworld(state=st) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        ok = (act == PARENT and s.__dict__ == before and not dbl_events(log) and not log.reads and not log.ebytes
              and not log.bag and not log.ti and not log.mui and not log.gbs)
        return ok, (f"action {act}; dict unchanged {s.__dict__ == before}; DBLITEM {dbl_events(log)}; reads "
                    f"{log.reads}; bag {log.bag}; opponent {log.ti}; _maybe_use_item {log.mui}")

    def dq02():
        s = new_strategy()
        st = dstate(lhp=20)
        before = copy.deepcopy(s.__dict__)
        with sworld(env={FLAG: "observe"}, state=st) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        after = {k: v for k, v in s.__dict__.items() if k != "_dbl_obs"}
        obs = lines(log, "DBLITEM-OBS")
        others = [e for e in log.events if e[0] != "DBLITEM-OBS"]
        ok = (act == PARENT and after == before and len(obs) == 1 and field(obs[0], "would") == "Potion"
              and log.mui == 0 and log.kg == 0 and not others)
        return ok, f"action {act}; dict unchanged but _dbl_obs {after == before}; OBS {obs}; other lines {others}; " \
                   f"_maybe_use_item {log.mui}; _r27_key_gate {log.kg}"

    def dq03():
        bag = Bag(("Potion", 3), ("Super Potion", 2), ("Hyper Potion", 2), ("Full Heal", 1), ("Awakening", 1),
                  ("Full Restore", 1), ("X Attack", 1), ("Repel", 1))

        def reserve(medicine):                                  # RULING 18's shape: hold one Hyper Potion and the
            out = []                                            # whole Full Restore line back
            for item, qty, param in medicine:
                if item.name == "Full Restore":
                    continue
                out.append((item, qty - 1 if item.name == "Hyper Potion" else qty, param))
            return out

        st = dstate(lhp=20)
        s1 = new_strategy()
        with sworld(state=st, bag=bag, reserve=reserve) as log1:
            s1._maybe_use_item(st)                              # the singles call: what it hands the HP policy
        s2 = new_strategy()
        with sworld(env={FLAG: "observe"}, state=st, bag=bag, reserve=reserve) as log2:
            s2.decide_turn_in_double_battle(st, 0)              # observe's mirror, through production
        mirror = DBL().heal_options(bag.items, reserve)

        def names(opts):
            return [(o[0].name, o[1], o[2]) for o in opts]

        want = [("Potion", 3, 20), ("Super Potion", 2, 50), ("Hyper Potion", 1, 200)]
        got1 = names(log1.hp_opts[0]) if len(log1.hp_opts) == 1 else log1.hp_opts
        got2 = names(log2.hp_opts[0]) if len(log2.hp_opts) == 1 else log2.hp_opts
        ok = got1 == want and got2 == want and names(mirror) == want
        return ok, f"_maybe_use_item {got1}; observe {got2}; heal_options {names(mirror)}"

    def dq04():
        s = new_strategy()
        st = dstate(lhp=20)
        with sworld(env={FLAG: "1"}, state=st) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        return act == use(POTION, L_IDX), f"action {act}; lines {dbl_events(log)}"

    def dq05():
        s = new_strategy()
        st = dstate(rhp=20)
        with sworld(env={FLAG: "1"}, state=st) as log:
            act = s.decide_turn_in_double_battle(st, 1)
        return act == use(POTION, R_IDX), f"action {act}; lines {dbl_events(log)}"

    def dq06():
        s = new_strategy()
        st = dstate(lhp=100, rhp=20)
        with sworld(env={FLAG: "1"}, state=st) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        return act == PARENT, f"action {act}; lines {dbl_events(log)}"

    def dq07():
        s = new_strategy()
        st = dstate(lhp=100, lst=2)                             # asleep at full HP, the bag a Full Heal only
        with sworld(env={FLAG: "1"}, state=st, bag=Bag(("Full Heal", 1))) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        return act == PARENT, f"action {act}; lines {log.events}"

    def dq08():
        s = new_strategy()
        st1 = dstate(lhp=100, rhp=20)
        bag = Bag(("Potion", 1))
        with sworld(env={FLAG: "1"}, state=st1, bag=bag):
            a1 = s.decide_turn_in_double_battle(st1, 1)         # side 1 requests
            a2 = s.decide_turn_in_double_battle(st1, 0)         # then the partner decides
        ledger = getattr(s, "_dbl_ledgers", {}).get((R_PID, SPECIES_ID["Mightyena"]), {})
        pending = ledger.get("_hp_when_item_requested")
        bag.items[0].quantity = 0                               # the Potion applied: next turn, Mightyena reads 40
        st2 = dstate(lhp=100, rhp=40)
        with sworld(env={FLAG: "1"}, state=st2, fresh=st2, bag=bag) as log2:
            a3 = s.decide_turn_in_double_battle(st2, 1)
        consumed = [m for _c, m in log2.events if "CONSUMED" in m]
        ok = a1 == use(POTION, R_IDX) and a2 == PARENT and pending == (R_IDX, 20) and a3 == PARENT and len(consumed) == 1
        return ok, f"side 1 {a1}; side 0 {a2}; side 1's pending after the partner {pending}; next turn {a3} {consumed}"

    def dq09():
        out = []
        for extra in (MULTI, PARTNER):
            s = new_strategy()
            st = dstate(lhp=20, flags=TRAINER | DOUBLE | extra)
            with sworld(env={FLAG: "1"}, state=st) as log:
                act = s.decide_turn_in_double_battle(st, 0)
            out.append((act == PARENT and not dbl_events(log) and log.mui == 0, act))
        return all(o for o, _a in out), f"Multi / InGamePartner: {out}"

    def dq10():
        out = {}
        for cls in (0x05, 0x20):
            s = new_strategy()
            st = dstate(lhp=20)
            with sworld(env={FLAG: "1", KEYITEMS: "1"}, state=st, cls=cls) as log:
                act = s.decide_turn_in_double_battle(st, 0)
            out[cls] = (act, lines(log, "KEYBATTLE"))
        ok = (out[0x05][0] == PARENT and len(out[0x05][1]) == 1 and field(out[0x05][1][0], "key") == "False"
              and out[0x20][0] == use(POTION, L_IDX))
        return ok, f"0x05 {out[0x05]}; 0x20 {out[0x20][0]}"

    # ---------------------------------------------------------------------------------------- builder-added (strategy)
    def db_use():
        s = new_strategy()
        st = dstate(rhp=20)
        with sworld(env={FLAG: "1"}, state=st) as log:
            s.decide_turn_in_double_battle(st, 1)
        got = lines(log, "DBLITEM")
        want = ["use side=1 g=2 item=Potion target=Mightyena#5C96EA9B P=4 hp=20/100 self=1"]
        return got == want, f"{got}"

    def db_err():
        s = new_strategy()
        s._worst_hit, s._hp_seen = 7, {"singles": 1}            # singles values the ledger swap must hand back
        st = dstate(lhp=20)
        with sworld(env={FLAG: "1"}, state=st, mui_raises=True) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        got = lines(log, "DBLITEM")
        ok = (act == PARENT and len(got) == 1 and got[0].startswith("err side=0 g=0 RuntimeError")
              and s._worst_hit == 7 and s._hp_seen == {"singles": 1})
        return ok, f"action {act}; lines {got}; singles fields {s._worst_hit} {s._hp_seen}"

    def db_ledger():
        d = DBL()
        want = ("_hp_seen", "_worst_hit", "_hp_when_item_requested", "_status_when_item_requested",
                "_item_qty_when_requested")
        s = new_strategy()
        fresh = d.new_ledger()
        ok = (tuple(d.LEDGER_FIELDS) == want and set(fresh) == set(want)
              and all(getattr(s, f) == fresh[f] for f in want))
        return ok, f"LEDGER_FIELDS {d.LEDGER_FIELDS}; new_ledger {fresh}; instance {[getattr(s, f) for f in want]}"

    def db_obsfields():
        s = new_strategy()
        st = dstate(rhp=20)
        with sworld(env={FLAG: "observe"}, state=st) as log:
            s.decide_turn_in_double_battle(st, 1)
        got = lines(log, "DBLITEM-OBS")
        want = ["side=1 g=2 turn=3 me=Mightyena#5C96EA9B P=4 hp=20/100 would=Potion why=hp key=1 worst=0 uses=0 "
                "bpo=140235 bpo_pos=1 disc=1 cur=00000100"]
        return got == want, f"{got}"

    def db_obsworst():
        s = new_strategy()
        out = []
        for side, lhp, rhp in ((0, 60, 90), (1, 60, 90), (0, 30, 90)):
            st = dstate(lhp=lhp, rhp=rhp)
            with sworld(env={FLAG: "observe"}, state=st) as log:
                s.decide_turn_in_double_battle(st, side)
            out += lines(log, "DBLITEM-OBS")
        ok = (len(out) == 3 and field(out[2], "would") == "-" and field(out[2], "why") == "losing_race"
              and field(out[2], "worst") == "30" and field(out[1], "worst") == "0")
        return ok, f"{[(field(o, 'side'), field(o, 'hp'), field(o, 'would'), field(o, 'why'), field(o, 'worst')) for o in out]}"

    def db_obskey():
        out = {}
        for cls in (0x05, 0x20):
            s = new_strategy()
            st = dstate(lhp=20)
            with sworld(env={FLAG: "observe", KEYITEMS: "1"}, state=st, cls=cls) as log:
                s.decide_turn_in_double_battle(st, 0)
            obs = lines(log, "DBLITEM-OBS")
            out[cls] = (obs[0] if len(obs) == 1 else obs, log.kg, lines(log, "KEYBATTLE"))
        o5, o20 = out[0x05][0], out[0x20][0]
        ok = (isinstance(o5, str) and field(o5, "would") == "-" and field(o5, "why") == "not_key"
              and field(o5, "key") == "0" and isinstance(o20, str) and field(o20, "would") == "Potion"
              and field(o20, "key") == "1" and out[0x05][1] == 0 and out[0x20][1] == 0
              and not out[0x05][2] and not out[0x20][2])
        return ok, f"0x05 {out[0x05]}; 0x20 {out[0x20]}"

    def db_obsdisc():
        # D8: `disc` marks a row where the requester's party index differs from its SIDE. Here both are equal (left
        # party 0 at side 0, right party 1 at side 1), as T2 pre-registers for Tate & Liza's side 0: disc=0 on both.
        s = new_strategy()
        st = dstate(bpi=(0, 0, 1, 1))
        out = []
        for side in (0, 1):
            with sworld(env={FLAG: "observe"}, state=st) as log:
                s.decide_turn_in_double_battle(st, side)
            out += lines(log, "DBLITEM-OBS")
        got = [(field(o, "side"), field(o, "P"), field(o, "disc")) for o in out]
        return got == [("0", "0", "0"), ("1", "1", "0")], f"{got}"

    def db_noscope():
        s = new_strategy()
        st = dstate(lhp=20, flags=TRAINER | DOUBLE | MULTI)
        with sworld(env={FLAG: "observe"}, state=st) as log:
            act = s.decide_turn_in_double_battle(st, 0)
        ok = act == PARENT and not log.events and not log.reads and not log.bag
        return ok, f"action {act}; lines {log.events}; reads {log.reads}"

    def db_singlescure():
        s = new_strategy()
        st = dstate(lhp=100, lst=2)
        with sworld(state=st, bag=Bag(("Full Heal", 1))):
            act = s._maybe_use_item(st)                         # the SINGLES call: the cure still fires (D10 is doubles-only)
        return act == use(ITEM["Full Heal"], L_IDX), f"action {act}"

    def db_judge():
        # P6's shape on side 1: the item is REFUSED twice (the bag count never drops). The KI-101 judge must read the
        # SAME side that asked: one retry, then the per-battle disable (D4's bound for an HP item).
        s = new_strategy()
        st = dstate(lhp=100, rhp=20)
        acts = []
        with sworld(env={FLAG: "1"}, state=st, bag=Bag(("Potion", 1))) as log:
            for _ in range(3):
                acts.append(s.decide_turn_in_double_battle(st, 1))
        verdicts = [m for _c, m in log.events if "not consumed" in m]
        ok = (acts == [use(POTION, R_IDX), use(POTION, R_IDX), PARENT] and len(verdicts) == 2
              and "retrying once" in verdicts[0] and "disabling items" in verdicts[1]
              and s._index_space_flipped is True and s._items_ineffective is True)
        return ok, f"actions {[a[0] for a in acts]}; verdicts {verdicts}"

    cases = [
        ("DQ01 flag unset: the parent's action, __dict__ unchanged, no DBLITEM line, no read", dq01),
        ("DQ02 observe, left 20/100: the parent's action; __dict__ unchanged but _dbl_obs; ONE OBS line would=Potion; "
         "_maybe_use_item and _r27_key_gate never called", dq02),
        ("DQ03 observe PARITY: heal_options == the options _maybe_use_item hands choose_healing_item (and observe's own)",
         dq03),
        ("DQ04 flag 1, side 0, left 20/100: UseItem(Potion, the left's party index 1)", dq04),
        ("DQ05 flag 1, side 1, right 20/100: UseItem(Potion, the right's party index 4)", dq05),
        ("DQ06 flag 1, side 0, left 100/100, right 20/100: no item, the parent's action (self-only)", dq06),
        ("DQ07 flag 1, side 0, left asleep at 100/100, bag Full Heal only: no item (D10)", dq07),
        ("DQ08 flag 1: side 1 requests, then side 0 decides: side 1's pending request survives (and is judged next turn)",
         dq08),
        ("DQ09 flag 1, +Multi or +InGamePartner: the parent's action", dq09),
        ("DQ10 flag 1 + KEYITEMS=1: a non-key class -> no item; class LEADER -> UseItem", dq10),
        ("DBuse [builder] flag 1 acting: exactly one `[DBLITEM] use` line, identity and self=1", db_use),
        ("DBerr [builder] flag 1, the policy raises: the parent's action, ONE err line, the singles fields restored",
         db_err),
        ("DBledger [builder] LEDGER_FIELDS are D3's five, and new_ledger() equals a fresh instance's values", db_ledger),
        ("DBobsfields [builder] observe side 1: every field (bpo dereferenced at +0x60+3g, bpo_pos=1, disc=1)",
         db_obsfields),
        ("DBobsworst [builder] observe's own per-PID tracker: a 30-HP drop makes the Potion a losing race", db_obsworst),
        ("DBobskey [builder] observe + KEYITEMS=1: 0x05 would=- why=not_key key=0; 0x20 key=1; no gate, no KEYBATTLE",
         db_obskey),
        ("DBobsdisc [builder] observe: disc=0 where the party index equals the side (both sides)", db_obsdisc),
        ("DBnoscope [builder] observe in a Multi: the parent's action, no line, no read", db_noscope),
        ("DBsinglescure [builder] the SINGLES call still cures a sleeping lead with Full Heal (D10 is doubles-only)",
         db_singlescure),
        ("DBjudge [builder] side 1 refused twice: the judge reads side 1 — one retry, then the disable (P6's shape)",
         db_judge),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ============================================================================================================ EXECUTOR
def party_rec(pid, species, hp, maxhp, otid=0x00BEEF01) -> bytes:
    """A GENUINE 100-byte party record (real substructure order, XOR encryption, checksum), as
    `repro_pid_identity_key.build_mon` builds one, plus status1 (+0x50), HP (+0x56) and max HP (+0x58)."""
    order = POKEMON_DATA_SUBSTRUCTS_ORDER[pid % 24]
    key = pid ^ otid
    logical = [struct.pack("<H", species) + bytes(10), bytes(12), bytes(12), bytes(12)]
    checksum = sum(struct.unpack("<24H", b"".join(logical))) & 0xFFFF
    raw = [b""] * 4
    for li, chunk in enumerate(logical):
        raw[order[li]] = b"".join(struct.pack("<I", struct.unpack_from("<I", chunk, w * 4)[0] ^ key) for w in range(3))
    header = bytearray(32)
    struct.pack_into("<II", header, 0, pid, otid)
    header[19] = 0x02                                       # hasSpecies
    struct.pack_into("<H", header, 28, checksum)
    tail = bytearray(20)
    struct.pack_into("<HH", tail, 6, hp, maxhp)
    return bytes(header) + b"".join(raw) + bytes(tail)


#: FIELD order: party index -> (species, PID, HP). Our actives are party 1 (left) and party 4 (right).
FIELD = ((SPECIES_ID["Castform"], 0xC978D14E, 50), (SPECIES_ID["Sceptile"], L_PID, 40),
         (SPECIES_ID["Swellow"], 0x0B30A747, 50), (SPECIES_ID["Skitty"], 0x5CCCD8BE, 50),
         (SPECIES_ID["Mightyena"], R_PID, 30), (SPECIES_ID["Zigzagoon"], 0x33CB74C3, 50))
MENU = (1, 4, 0, 2, 3, 5)                                   # G2: [left active, right active, the rest]


class Game:
    """The in-battle item flow, small and deterministic. `menu_order` is the order the party menu REALLY shows (the
    executor's re-map may believe another); A on the party menu applies a 20-HP medicine to the PID at the cursor."""

    def __init__(self, *, g, menu_order=MENU, cursor=(0, 0, 0, 0), bag_opens=True, party_opens=True):
        self.g = g
        self.party_opens = party_opens
        self.recs = {i: bytearray(party_rec(pid, sp, hp, 100)) for i, (sp, pid, hp) in enumerate(FIELD)}
        self.menu_order = list(menu_order)
        self.state = "battle"
        self.cursor = bytearray(cursor)
        self.party_menu = bytearray(0x14)
        self.party_menu[8] = 0x11                            # menuType 1 (in battle), layout 1 (DOUBLE)
        self.bim = 0xFF
        self.bag = Bag(("Potion", 1))
        self.healed = 0
        self.frame = 0
        self.bag_opens = bag_opens
        self.presses: list = []                              # (frame, state, button, cursor slot)

    def order(self):
        return self.menu_order if self.state in ("party", "party_msg") else list(range(6))

    def symbol(self, name):
        table = {"gPlayerParty": b"".join(bytes(self.recs[i]) for i in self.order()),
                 "gPlayerPartyCount": bytes([6]), "gPartyMenu": bytes(self.party_menu),
                 "gBattlerInMenuId": bytes([self.bim]), "gBattlerPartyIndexes": BPI_RAW,
                 "gBattleResults": bytes([0, 0, 0, self.healed]) + bytes(0x40),
                 "gActionSelectionCursor": bytes(self.cursor)}
        return table[name]

    def game_state(self):
        return {"battle": GameState.BATTLE, "bag": GameState.BAG_MENU, "bag_item": GameState.BAG_MENU,
                "party": GameState.PARTY_MENU, "party_msg": GameState.PARTY_MENU}[self.state]

    def state_symbol(self):
        return {"battle": "BATTLEMAINCB2", "bag": "CB2_BAGMENURUN", "bag_item": "CB2_BAGMENURUN",
                "party": "CB2_UPDATEPARTYMENU", "party_msg": "CB2_UPDATEPARTYMENU"}[self.state]

    def hp(self, index):
        return struct.unpack_from("<H", self.recs[index], 0x56)[0]

    def press_button(self, name):
        self.presses.append((self.frame, self.state, name, self.party_menu[9]))
        st = self.state
        if st == "battle":
            if name == "A" and self.bag_opens:
                self.state = "bag"
            elif name in ("Left", "Right", "Up", "Down"):
                i = self.cursor[self.g]
                i = {"Left": i - 1 if i in (1, 3) else i, "Right": i + 1 if i in (0, 2) else i,
                     "Up": i - 2 if i in (2, 3) else i, "Down": i + 2 if i in (0, 1) else i}[name]
                self.cursor[self.g] = i
        elif st == "bag":
            self.state = {"A": "bag_item", "B": "battle"}.get(name, st)
        elif st == "bag_item":
            if name == "A" and self.party_opens:
                self.state, self.party_menu[9], self.bim = "party", 0, self.g
            elif name == "B":
                self.state = "bag"
        elif st == "party":
            if name == "A":
                rec = self.recs[self.menu_order[self.party_menu[9]]] if self.party_menu[9] < 6 else None
                if rec is not None:
                    hp = struct.unpack_from("<H", rec, 0x56)[0]
                    if 0 < hp < 100 and self.bag.items[0].quantity > 0:   # G1: applied AT SELECTION
                        struct.pack_into("<H", rec, 0x56, min(100, hp + 20))
                        self.bag.items[0].quantity -= 1
                        self.healed += 1
                self.state = "party_msg"
            elif name == "B":
                self.state = "bag"
        elif st == "party_msg" and name == "B":
            self.state = "bag"


def drive(gen, game, cap=3000):
    steps = 0
    for _ in gen:
        game.frame += 1
        steps += 1
        if steps >= cap:
            return "cap"
    return "done"


@contextlib.contextmanager
def xworld(game, *, env=None, remap=MENU, party_scroll=None, raise_on=None, real_action_scroll=False,
           controller=None, main=None):
    """Production's world for the EXECUTOR rows: `read_symbol` (recorded; `raise_on` makes one symbol raise), the game
    state, `get_battle_state` (the KI-101 re-map's array = `remap`; counted), the bag-item scroll (a no-op), the party
    scroll (records its aim, then leaves the cursor on the aim or on `party_scroll`), the action scroll (a recorded
    no-op, or a spy over the REAL `battle_menuing` one), the emulator and ROM, the bag (counted) and the logger."""
    bas, bm = BAS(), BM()
    log = types.SimpleNamespace(events=[], reads=[], gbs=0, aims=[], scrolls=[], bag=0, cb2=0)
    remap_state = dstate(order=remap)

    def fake_read(name, offset=0, size=0):
        log.reads.append(name)
        if name == raise_on:
            raise RuntimeError(f"{name} unreadable")
        data = game.symbol(name)
        return data[offset:offset + (size or len(data))]

    def fake_gbs(*_a, **_k):
        log.gbs += 1
        return remap_state

    def stub_bag_scroll(_item):
        yield

    def stub_party_scroll(target):
        log.aims.append(target)
        game.party_menu[9] = target if party_scroll is None else party_scroll
        yield

    real_scroll = bm.scroll_to_battle_action

    def action_scroll(action_index, is_right_side_pokemon=False):
        log.scrolls.append((action_index, is_right_side_pokemon))
        if real_action_scroll:
            yield from real_scroll(action_index, is_right_side_pokemon)
        else:
            yield

    def fake_bag():
        log.bag += 1
        return game.bag

    def fake_event(message, *, category="STORY"):
        log.events.append((category, message))

    def fake_controller(battler):
        if battler == 2:
            log.cb2 += 1
        return controller(battler) if controller else "Idle"

    ctx = types.SimpleNamespace(emulator=game, rom=types.SimpleNamespace(is_rse=True, is_rs=False, is_frlg=False))
    patches = [(bas, "read_symbol", fake_read), (bas, "get_game_state", game.game_state),
               (bas, "get_game_state_symbol", game.state_symbol), (bas, "get_battle_state", fake_gbs),
               (bas, "scroll_to_item_in_bag", stub_bag_scroll), (bas, "scroll_to_party_menu_index", stub_party_scroll),
               (bas, "scroll_to_battle_action", action_scroll), (bas, "scroll_to_move", lambda *_a, **_k: iter(())),
               (bas, "context", ctx), (bas, "get_battle_controller_callback", fake_controller),
               (bas, "get_main_battle_callback", main or (lambda: "Elsewhere")),
               (bm, "read_symbol", fake_read), (bm, "context", ctx),
               (modules.items, "get_item_bag", fake_bag), (modules.debug_logger, "event", fake_event)]
    with _env(env), _patched(patches):
        yield log


def party_a(game):
    return [p for p in game.presses if p[1] == "party" and p[2] == "A"]


def run_item(game, *, target, g, env=None, state=None, **kw):
    with xworld(game, env=env, **kw) as log:
        out = drive(BAS().battle_action_use_item(state or dstate(), POTION, target, g), game)
    return out, log


def executor_rows(tag=""):
    reds: list = []

    def dq11():
        game = Game(g=2, cursor=(1, 3, 0, 3))
        with xworld(game) as log:
            out = drive(BM().scroll_to_battle_action(1, True), game)
        dirs = [p[2] for p in game.presses]
        ok = out == "done" and dirs == ["Right"] and bytes(game.cursor) == bytes([1, 3, 1, 3])
        return ok, f"presses {dirs}; cursor {list(game.cursor)}; reads {log.reads}"

    def dq12():
        game = Game(g=2, cursor=(1, 0, 0, 0), bag_opens=False)
        out, log = run_item(game, target=R_IDX, g=2, real_action_scroll=True)
        dirs = [p[2] for p in game.presses if p[2] != "A"]
        ok = out == "done" and log.scrolls == [(1, True)] and dirs == ["Right"] and game.cursor[2] == 1
        return ok, f"scroll calls {log.scrolls}; direction presses {dirs}; cursor {list(game.cursor)}"

    def dq13():
        game = Game(g=2)
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"})
        menu = [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]
        after = [m for m in lines(log, "DBLITEM") if m.startswith("after ")]
        want_menu = ("menu g=2 battler_in_menu=2 layout=1 slot=1 menu_pid=5C96EA9B intended_pid=5C96EA9B ok=1 "
                     "a_pressed=1 aim=1 self=1")
        want_after = ("after g=2 target=Mightyena#5C96EA9B hp=30->50 status1=0->0 partner=Sceptile#863B0917 "
                      "hp=40->40 Potion=1->0 healed=0->1 same=1")
        pa = party_a(game)
        ok = (out == "done" and log.aims == [1] and len(pa) == 1 and pa[0][3] == 1 and menu == [want_menu]
              and after == [want_after] and game.state == "battle")
        return ok, f"aim {log.aims}; party A {pa}; menu {menu}; after {after}; state {game.state}"

    def dq14():
        game = Game(g=2)
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"}, party_scroll=7)   # stopped on Cancel
        menu = [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]
        m = menu[0] if len(menu) == 1 else ""
        ok = (out == "done" and field(m, "slot") == "7" and field(m, "ok") == "0" and field(m, "a_pressed") == "0"
              and not party_a(game) and game.state == "battle" and game.bag.items[0].quantity == 1)
        return ok, f"menu {menu}; party A {party_a(game)}; state {game.state}"

    def dq15():
        game = Game(g=2, menu_order=(1, 2, 0, 4, 3, 5))     # the menu disagrees with the re-map at slot 1
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"})
        menu = [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]
        after = [m for m in lines(log, "DBLITEM") if m.startswith("after ")]
        m, a = (menu[0] if len(menu) == 1 else ""), (after[0] if len(after) == 1 else "")
        bpresses = [p for p in game.presses if p[2] == "B"]
        ok = (out == "done" and field(m, "ok") == "0" and field(m, "a_pressed") == "0"
              and field(m, "intended_pid") == "5C96EA9B" and field(m, "menu_pid") not in (None, "5C96EA9B")
              and not party_a(game) and bpresses and game.state == "battle"
              and " hp=30->30 " in a and "Potion=1->1" in a and "healed=0->0" in a)
        return ok, f"menu {menu}; after {after}; party A {party_a(game)}; B presses {len(bpresses)}"

    def dq16():
        out = {}
        for flag in (None, "1"):
            game = Game(g=0)

            def controller(battler, game=game):
                if battler == 2:
                    return "HandleInputChooseAction" if game.frame >= 10 else "Idle"
                return "Idle"

            def main(game=game):
                return "HandleTurnActionSelectionState" if game.frame < 40 else "Done"

            with xworld(game, env={FLAG: flag} if flag else None, controller=controller, main=main) as log:
                res = drive(BAS().battle_action_use_move(TurnAction.UseMove, 0, 0, dstate()), game)
            late = [p[0] for p in game.presses if p[2] == "A" and p[0] >= 10]
            out[flag] = (res, late, log.cb2, lines(log, "DBLITEM"))
        unset, on = out[None], out["1"]
        ok = (unset[0] == "done" and unset[1] == list(range(10, 40)) and unset[2] == 0 and not unset[3]
              and on[0] == "done" and on[1] == [] and len(on[3]) == 1 and on[3][0].startswith("struggle-exit g=0"))
        return ok, (f"unset: A at frames >= 10 {len(unset[1])} (want 30), controller-2 reads {unset[2]}; flag 1: "
                    f"A at frames >= 10 {on[1]}, lines {on[3]}")

    def dq17():
        game = Game(g=2)
        out, log = run_item(game, target=R_IDX, g=2)
        pa = party_a(game)
        ok = (out == "done" and not log.reads and not dbl_events(log) and not log.bag and len(pa) == 1
              and pa[0][3] == 1 and game.hp(R_IDX) == 50)
        return ok, f"reads {log.reads}; DBLITEM {dbl_events(log)}; bag reads {log.bag}; party A {pa}"

    # ---------------------------------------------------------------------------------------- builder-added (executor)
    def db_self():
        game = Game(g=2)                                    # battler 2 aimed at the LEFT's party index (1)
        out, log = run_item(game, target=L_IDX, g=2, env={FLAG: "1"})
        menu = [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]
        m = menu[0] if len(menu) == 1 else ""
        ok = (out == "done" and field(m, "self") == "0" and field(m, "ok") == "0" and field(m, "a_pressed") == "0"
              and field(m, "menu_pid") == field(m, "intended_pid") == "863B0917" and not party_a(game))
        return ok, f"menu {menu}; party A {party_a(game)}"

    def db_guardraise():
        game = Game(g=2)
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"}, raise_on="gPartyMenu")
        menu = [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]
        m = menu[0] if len(menu) == 1 else ""
        ok = (out == "done" and field(m, "ok") == "0" and field(m, "a_pressed") == "0"
              and field(m, "err") == "RuntimeError" and not party_a(game) and game.state == "battle")
        return ok, f"menu {menu}; party A {party_a(game)}; state {game.state}"

    def db_singleexec():
        # C4: the guard and the `after` read run with the flag `1` AND a DOUBLE. A flag-on SINGLE is today's flow.
        game = Game(g=0, menu_order=(1, 0, 2, 3, 4, 5))
        out, log = run_item(game, target=L_IDX, g=0, env={FLAG: "1"}, state=dstate(single=True),
                            remap=(1, 0, 2, 3, 4, 5))
        pa = party_a(game)
        ok = (out == "done" and not log.reads and not dbl_events(log) and not log.bag and len(pa) == 1
              and pa[0][3] == 0 and game.hp(L_IDX) == 60)
        return ok, f"reads {log.reads}; DBLITEM {dbl_events(log)}; party A {pa}; left hp {game.hp(L_IDX)}"

    def db_menuclosed():
        # The guard reads only when the party menu IS open: here it never opens, and a stale slotId (4) happens to
        # point at the intended PID in FIELD order. ⛔ An A pressed now would land in the bag, not on a Pokémon.
        game = Game(g=2, party_opens=False)
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"})
        menu = [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]
        m = menu[0] if len(menu) == 1 else ""
        bag_a = [p for p in game.presses if p[1] == "bag_item" and p[2] == "A"]
        ok = (out == "done" and field(m, "ok") == "0" and field(m, "a_pressed") == "0"
              and field(m, "err") == "RuntimeError" and len(bag_a) == 1 and game.state == "battle")
        return ok, f"menu {menu}; A presses in the bag after the item {len(bag_a)} (want 1); state {game.state}"

    def db_move():
        out = {}
        for g in (0, 2):
            game = Game(g=g)
            with xworld(game) as log:
                drive(BAS().battle_action_use_move(TurnAction.UseMove, g, 0, dstate()), game)
            out[g] = log.scrolls
        return out == {0: [(0, False)], 2: [(0, True)]}, f"{out}"

    def db_d11b2():
        # D11 binds BATTLER 0's loop only: battler 2's own Struggle loop runs while its OWN action menu reads
        # HandleInputChooseAction, and must keep confirming (today's behaviour) with the flag on.
        game = Game(g=2)

        def controller(_battler):
            return "HandleInputChooseAction"

        def main(game=game):
            return "HandleTurnActionSelectionState" if game.frame < 40 else "Done"

        with xworld(game, env={FLAG: "1"}, controller=controller, main=main) as log:
            res = drive(BAS().battle_action_use_move(TurnAction.UseMove, 2, 0, dstate()), game)
        loop = [p[0] for p in game.presses if p[2] == "A" and p[0] >= 8]
        ok = res == "done" and loop == list(range(8, 40)) and not lines(log, "DBLITEM")
        return ok, f"A in the loop at frames {loop[:3]}..{loop[-1:]} ({len(loop)}, want 32); lines {lines(log, 'DBLITEM')}"

    cases = [
        ("DQ11 scroll_to_battle_action(1, True) on cursor [1,3,0,3]: byte 2 read, Right until byte 2 = 1", dq11),
        ("DQ12 battle_action_use_item(..., battler_index=2) calls scroll_to_battle_action(1, True); byte 2 moves", dq12),
        ("DQ13 executor positive control, matching PIDs: cursor to the requester's slot, A; ok=1 a_pressed=1; after",
         dq13),
        ("DQ14 the scroll stops short (Cancel, slot 7 != aim): refused by the guard's own slotId read", dq14),
        ("DQ15 a PID mismatch at the slot: no A, the B unwind runs; ok=0 a_pressed=0; nothing healed", dq15),
        ("DQ16 the Struggle loop; controller 2 opens its menu at f10: flag 1 no A after it; unset A every frame", dq16),
        ("DQ17 flag unset, executor: no guard read, no DBLITEM line, today's A", dq17),
        ("DBself [builder] battler 2 aimed at the LEFT's index: the PID matches, the SELF binding refuses", db_self),
        ("DBguardraise [builder] the guard's gPartyMenu read raises: fails CLOSED (no A), err logged", db_guardraise),
        ("DBsingleexec [builder] flag 1 in a SINGLE battle: no guard read, no DBLITEM line, today's A", db_singleexec),
        ("DBmenuclosed [builder] the party menu never opened: the guard refuses (no A into the bag)", db_menuclosed),
        ("DBmove [builder] battle_action_use_move passes battler_index > 1 to the action scroll", db_move),
        ("DBd11b2 [builder] D11 is battler 0's only: battler 2's own Struggle loop keeps confirming, flag on", db_d11b2),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ================================================================================================================ PURE
def pure_rows(tag=""):
    reds: list = []
    d = DBL()

    def dp01():
        got = [d.mode(e) for e in ({}, {FLAG: "observe"}, {FLAG: "1"}, {FLAG: "0"}, {FLAG: "yes"}, {FLAG: "ON"},
                                   {FLAG: " 1"})]
        want = [d.OFF, d.OBSERVE, d.ON, d.OFF, d.OFF, d.OFF, d.OFF]
        return got == want, f"{got}"

    def dp02():
        got = [d.in_scope(TRAINER | DOUBLE), d.in_scope(TRAINER | DOUBLE | MULTI), d.in_scope(TRAINER | DOUBLE | PARTNER),
               d.in_scope(TRAINER), d.in_scope(DOUBLE),
               d.in_scope(modules.battle_state.BattleType(TRAINER | DOUBLE))]          # the flag-object form too
        return got == [True, False, False, False, False, True], f"{got}"

    def dp03():
        got = (d.decode_bpo(bytes([0x02, 0x13, 0x45])), d.decode_bpo(bytes([0x12, 0x03, 0x45])),
               d.active_positions([0, 2, 1, 3, 4, 5]))
        return got == ([0, 2, 1, 3, 4, 5], [1, 2, 0, 3, 4, 5], (0, 2)), f"{got}"

    def dp04():
        a, b = 0x5C96EA9B, 0x0B30A747
        got = [d.guard_ok(a, a, 0, 6), d.guard_ok(a, b, 0, 6), d.guard_ok(a, a, 6, 6), d.guard_ok(a, a, 7, 6),
               d.guard_ok(a, a, 4, 4), d.guard_ok(None, a, 0, 6), d.guard_ok(None, None, 0, 6)]
        return got == [True] + [False] * 6, f"{got}"

    def dp05():
        raw = bytes.fromhex("0000000004000100")
        got = (d.self_ok(4, 2, raw), d.self_ok(1, 2, raw))
        return got == (True, False), f"{got}"

    def dp06():
        k = d.ledger_key(0x5C96EA9B, 287)
        ok = (k == (0x5C96EA9B, 287) and d.ledger_key(0x5C96EA9B, 287) != d.ledger_key(0x0B30A747, 287)
              and d.ledger_key(0x5C96EA9B, 287) != d.ledger_key(0x5C96EA9B, 305))
        return ok, f"{k}"

    def dp07():
        got = d.hp_only([(POTION, 1, 20), (ITEM["Full Heal"], 1, 0)])
        return got == [(POTION, 1, 20)], f"{got}"

    def db_frac():
        got = [d.heal_fraction_kw(""), d.heal_fraction_kw("0.8"), d.heal_fraction_kw("x")]
        return got == [{}, {"heal_at_fraction": 0.8}, {}], f"{got}"

    def db_why():
        p = [(POTION, 1, 20)]
        got = [d.hp_decline_reason(0, 100, p), d.hp_decline_reason(20, 100, p, uses_so_far=4),
               d.hp_decline_reason(90, 100, p), d.hp_decline_reason(20, 100, []),
               d.hp_decline_reason(20, 100, p, worst_hit_taken=50)]
        return got == ["fainted", "cap", "above_fraction", "no_hp_item", "losing_race"], f"{got}"

    cases = [
        ("DP01 mode(): unset/observe/1/0/yes/ON/' 1' -> off/observe/on/off/off/off/off", dp01),
        ("DP02 in_scope: Trainer+Double True; +Multi, +InGamePartner, Trainer alone, Double alone False", dp02),
        ("DP03 decode_bpo(02 13 45), decode_bpo(12 03 45), active_positions([0,2,1,3,4,5])", dp03),
        ("DP04 guard_ok: a match passes; a PID mismatch, slot 6, slot 7, slot = count, intended None refuse", dp04),
        ("DP05 self_ok on the u16 stride: (4, g=2) True, (1, g=2) False", dp05),
        ("DP06 ledger_key = (pid, species); two PIDs never share a ledger", dp06),
        ("DP07 hp_only keeps parameter > 0 only", dp07),
        ("DBfrac [builder] heal_fraction_kw parses the knob as _maybe_use_item does", db_frac),
        ("DBwhy [builder] hp_decline_reason names choose_healing_item's early exits in order", db_why),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ================================================================================================================= AST
def _fn(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def ast_rows(tag, srcs):
    reds: list = []

    def db_c1ast():
        tree = ast.parse(srcs["bas"])
        got = []
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            for call in (c for c in ast.walk(fn) if isinstance(c, ast.Call)):
                if isinstance(call.func, ast.Name) and call.func.id == "scroll_to_battle_action":
                    got.append((fn.name, ast.unparse(call)))
        got = sorted(got)
        want = sorted([("handle_battle_action_selection", "scroll_to_battle_action(2, battler_index > 1)"),
                       ("handle_battle_action_selection", "scroll_to_battle_action(3)"),
                       ("handle_battle_action_selection", "scroll_to_battle_action(0)"),
                       ("handle_battle_action_selection", "scroll_to_battle_action(2)"),
                       ("handle_battle_action_selection", "scroll_to_battle_action(1)"),
                       ("handle_battle_action_selection", "scroll_to_battle_action(2)"),
                       ("battle_action_use_item", "scroll_to_battle_action(1, battler_index > 1)"),
                       ("battle_action_use_pokeblock", "scroll_to_battle_action(1)"),
                       ("battle_action_use_move", "scroll_to_battle_action(0, battler_index > 1)")])
        return got == want, f"{got}"

    def db_c4ast():
        tree = ast.parse(srcs["bas"])
        handler = _fn(tree, "handle_battle_action_selection")
        calls = [ast.unparse(c) for c in ast.walk(handler) if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Name) and c.func.id == "battle_action_use_item"]
        sig = _fn(tree, "battle_action_use_item").args
        names = [a.arg for a in sig.args]
        defaults = [ast.unparse(x) for x in sig.defaults]
        ok = (calls == ["battle_action_use_item(battle_state, index, target_index, battler_index)"]
              and names == ["battle_state", "item", "target_index", "battler_index"] and defaults == ["0", "0"])
        return ok, f"calls {calls}; args {names} defaults {defaults}"

    def db_sig():
        tree = ast.parse(srcs["sm"])
        cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StoryItemBattleStrategy")
        mui = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_maybe_use_item")
        dt = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "decide_turn")
        act = _fn(tree, "_dbl_act")
        dt_calls = [ast.unparse(c) for c in ast.walk(dt) if isinstance(c, ast.Call)
                    and isinstance(c.func, ast.Attribute) and c.func.attr == "_maybe_use_item"]
        act_calls = [ast.unparse(c) for c in ast.walk(act) if isinstance(c, ast.Call)
                     and isinstance(c.func, ast.Attribute) and c.func.attr == "_maybe_use_item"]
        ok = ([a.arg for a in mui.args.args] == ["self", "battle_state", "side", "doubles"]
              and [ast.unparse(x) for x in mui.args.defaults] == ["0", "False"]
              and dt_calls == ["self._maybe_use_item(battle_state)"]
              and act_calls == ["strategy._maybe_use_item(battle_state, side=side, doubles=True)"])
        return ok, f"args {[a.arg for a in mui.args.args]}; decide_turn {dt_calls}; _dbl_act {act_calls}"

    cases = [
        ("DBc1ast [builder] (AST) C1's callers: use_move/use_item/RotateLead pass battler_index > 1; run, Safari and "
         "the Pokéblock stay on byte 0", db_c1ast),
        ("DBc4ast [builder] (AST) the UseItem case passes the handler's battler_index; the executor defaults it to 0",
         db_c4ast),
        ("DBsig [builder] (AST) _maybe_use_item(self, battle_state, side=0, doubles=False); the singles call passes "
         "nothing new; the doubles call passes side and doubles=True", db_sig),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


def all_rows(tag, srcs):
    return set(pure_rows(tag) + strategy_rows(tag) + executor_rows(tag) + ast_rows(tag, srcs))


# ============================================================================================================== FAULTS
#: EXACT red sets, PRE-REGISTERED in `2026-09-30-doubleitems13-PREDICTIONS.md` (the builder adds no row to any of them).
FAULT_SETS = {
    F_CURSOR0: {"DQ11", "DQ12"},
    F_WRONGSLOT: {"DQ13"},
    F_NOGUARD: {"DQ15"},
}

# ============================================================================================================= MUTANTS
#: (label, target "dbl" | "sm" | "bas" | "bm", [(old, new), ...] applied in order, the EXACT red set). The sets were
#: derived by hand from the rows above and written BEFORE the mutants' first run.
MUTANTS: list = [
    # ---- double_items.py (the pure rules) -------------------------------------------------------------------------
    ("MD01 mode(): 'ON' / 'on' also turn it on", "dbl",
     [('    if value == "1":\n        return ON', '    if value in ("1", "ON", "on"):\n        return ON')], {"DP01"}),
    ("MD02 mode(): the value is stripped (' 1' turns it on)", "dbl",
     [("    value = None if env is None else env.get(FLAG)",
       '    value = None if env is None else (env.get(FLAG) or "").strip()')], {"DP01"}),
    ("MD03 in_scope ignores Multi", "dbl",
     [("    return not bits & (BATTLE_TYPE_MULTI | BATTLE_TYPE_INGAME_PARTNER)",
       "    return not bits & BATTLE_TYPE_INGAME_PARTNER")], {"DP02", "DQ09", "DBnoscope"}),
    ("MD04 in_scope ignores the in-game partner", "dbl",
     [("    return not bits & (BATTLE_TYPE_MULTI | BATTLE_TYPE_INGAME_PARTNER)",
       "    return not bits & BATTLE_TYPE_MULTI")], {"DP02", "DQ09"}),
    ("MD05 in_scope drops the Trainer test (a wild double is in scope)", "dbl",
     [("    if not bits & BATTLE_TYPE_TRAINER or not bits & BATTLE_TYPE_DOUBLE:",
       "    if not bits & BATTLE_TYPE_DOUBLE:")], {"DP02"}),
    ("MD06 decode_bpo reads the LOW nibble first", "dbl",
     [("        out += [byte >> 4, byte & 0xF]", "        out += [byte & 0xF, byte >> 4]")], {"DP03", "DBobsfields"}),
    ("MD07 active_positions = positions 1-2 (the tail)", "dbl",
     [("    return order[0], order[1]", "    return order[1], order[2]")], {"DP03", "DBobsfields"}),
    ("MD08 guard_ok without the range check (Cancel = 7 and 6 pass)", "dbl",
     [("    if not 0 <= slot < count:\n        return False\n", "")], {"DP04"}),
    ("MD09 guard_ok without the None checks (two failed reads compare equal)", "dbl",
     [("    if intended_pid is None or menu_pid is None or slot is None or count is None:\n        return False\n", "")],
     {"DP04"}),
    ("MD10 gBattlerPartyIndexes read on a BYTE stride (raw[g])", "dbl",
     [('    return int.from_bytes(raw[2 * g:2 * g + 2], "little")', "    return raw[g]")], {"DP05", "DQ13", "DBuse"}),
    ("MD11 ledger_key = the PID alone", "dbl", [("    return pid, species", "    return pid")], {"DP06", "DQ08"}),
    ("MD12 hp_only keeps parameter 0 (a cure reaches the doubles policy)", "dbl",
     [("    return [opt for opt in options if opt[2] > 0]", "    return [opt for opt in options if opt[2] >= 0]")],
     {"DP07", "DQ03", "DQ07"}),
    ("MD13 heal_options skips the RULING 18 reserve", "dbl",
     [("    if reserve_filter is not None:", "    if False:")], {"DQ03"}),
    ("MD14 heal_options drops the Healing kind test (a Repel's 100 steps read as HP)", "dbl",
     [("slot in bag_items if _is_healing(slot.item)]", "slot in bag_items]")], {"DQ03"}),
    ("MD15 heal_fraction_kw ignores the knob", "dbl",
     [('        return {"heal_at_fraction": float(raw)}', "        return {}")], {"DBfrac"}),
    ("MD16 hp_decline_reason: rule 3's comparison reversed", "dbl",
     [("    if worst_hit_taken and best < worst_hit_taken:", "    if worst_hit_taken and best > worst_hit_taken:")],
     {"DBwhy", "DBobsworst"}),
    ("MD17 LEDGER_FIELDS without _worst_hit", "dbl",
     [('LEDGER_FIELDS = ("_hp_seen", "_worst_hit", "_hp_when_item_requested",',
       'LEDGER_FIELDS = ("_hp_seen", "_hp_when_item_requested",')], {"DBledger"}),
    ("MD18 MENTION ONLY: a comment that writes the 'ON' parse turns NOTHING red", "dbl",
     [('OFF, OBSERVE, ON = "off", "observe", "on"',
       '# if value in ("1", "ON"): return ON  -- a comment, never code\nOFF, OBSERVE, ON = "off", "observe", "on"')],
     set()),
    # ---- story_mode.py (the strategy half) ------------------------------------------------------------------------
    ("MS01 the flag-unset early return dropped (unset falls through to the acting path)", "sm",
     [("        if mode == _dbl.OFF:\n            return super().decide_turn_in_double_battle(battle_state, battler_index)\n",
       "")], {"DQ01"}),
    ("MS02 observe ACTS (calls the acting path) instead of logging", "sm",
     [("            _dbl_observe(self, battle_state, battler_index)\n",
       "            _dbl_act(self, battle_state, battler_index)\n")],
     {"DQ02", "DBobsfields", "DBobsworst", "DBobskey", "DBobsdisc"}),
    ("MS03 the decision reads the LEFT battler whatever the side", "sm",
     [("        mon = battle_state.own_side.left_battler if side == 0 else battle_state.own_side.right_battler\n"
       "        if mon is None or mon.total_hp <= 0:",
       "        mon = battle_state.own_side.left_battler\n        if mon is None or mon.total_hp <= 0:")],
     {"DQ05", "DQ08", "DBuse", "DBjudge"}),
    ("MS04 the decision reads the side REVERSED", "sm",
     [("        mon = battle_state.own_side.left_battler if side == 0 else battle_state.own_side.right_battler\n"
       "        if mon is None or mon.total_hp <= 0:",
       "        mon = battle_state.own_side.right_battler if side == 0 else battle_state.own_side.left_battler\n"
       "        if mon is None or mon.total_hp <= 0:")],
     {"DQ04", "DQ05", "DQ06", "DQ08", "DQ10", "DBuse", "DBsinglescure", "DBjudge"}),
    ("MS05 the KI-101 judge reads the LEFT battler whatever the side", "sm",
     [("                _judge_mon = ((_judge_state.own_side.left_battler if side == 0 else "
       "_judge_state.own_side.right_battler)",
       "                _judge_mon = ((_judge_state.own_side.left_battler)")], {"DBjudge"}),
    ("MS06 no ledger swap (the five fields shared by both battlers)", "sm",
     [("    for name in _dbl.LEDGER_FIELDS:\n        setattr(strategy, name, ledger[name])\n    try:\n"
       "        action = strategy._maybe_use_item(battle_state, side=side, doubles=True)\n    finally:\n"
       "        for name in _dbl.LEDGER_FIELDS:\n            ledger[name] = getattr(strategy, name)\n"
       "            setattr(strategy, name, saved[name])\n",
       "    action = strategy._maybe_use_item(battle_state, side=side, doubles=True)\n")], {"DQ08"}),
    ("MS07 the ledger written back but the singles fields NOT restored", "sm",
     [("            ledger[name] = getattr(strategy, name)\n            setattr(strategy, name, saved[name])\n",
       "            ledger[name] = getattr(strategy, name)\n")], {"DBerr"}),
    ("MS08 D10's HP-only filter removed (a double asks for Full Heal)", "sm",
     [("            if doubles:\n                from modules.story.double_items import hp_only as _dbl_hp_only\n\n"
       "                medicine = _dbl_hp_only(medicine)\n", "")], {"DQ07"}),
    ("MS09 D10's filter applied in SINGLES too", "sm",
     [("            if doubles:\n                from modules.story.double_items import hp_only",
       "            if True:\n                from modules.story.double_items import hp_only")], {"DBsinglescure"}),
    ("MS10 the doubles call passes doubles=False", "sm",
     [("strategy._maybe_use_item(battle_state, side=side, doubles=True)",
       "strategy._maybe_use_item(battle_state, side=side, doubles=False)")], {"DQ07", "DBsig"}),
    ("MS11 the strategy's scope check removed", "sm",
     [("        if not in_scope:\n            return super().decide_turn_in_double_battle(battle_state, battler_index)\n"
       "        if mode == _dbl.OBSERVE:", "        if mode == _dbl.OBSERVE:")], {"DQ09", "DBnoscope"}),
    ("MS12 observe runs BEFORE the scope check (a Multi logs a row)", "sm",
     [("        if not in_scope:\n            return super().decide_turn_in_double_battle(battle_state, battler_index)\n"
       "        if mode == _dbl.OBSERVE:\n            _dbl_observe(self, battle_state, battler_index)\n"
       "            return super().decide_turn_in_double_battle(battle_state, battler_index)\n",
       "        if mode == _dbl.OBSERVE:\n            _dbl_observe(self, battle_state, battler_index)\n"
       "            return super().decide_turn_in_double_battle(battle_state, battler_index)\n"
       "        if not in_scope:\n            return super().decide_turn_in_double_battle(battle_state, battler_index)\n")],
     {"DBnoscope"}),
    ("MS13 observe's tracker never records a drop (worst stays 0)", "sm",
     [('        rec["worst"] = max(rec["worst"], rec["hp"] - cur)', '        rec["worst"] = rec["worst"]')],
     {"DBobsworst"}),
    ("MS14 observe ignores POKEBOT_R27_KEYITEMS (allow always)", "sm",
     [('        allow = _ti.key_battle_verdict(_os_obs.environ.get("POKEBOT_R27_KEYITEMS") == "1", sides)[0]',
       "        allow = True")], {"DBobskey"}),
    ("MS15 observe's key field asks _r27_key_gate (it caches and logs)", "sm",
     [("        reason = _ti.key_battle_verdict(True, sides)[1]",
       '        reason = "key_class" if _r27_key_gate(strategy, battle_state) else "not_a_key_class"')],
     {"DQ02", "DBobskey"}),
    ("MS16 observe reads battlerPartyOrders at 3 * side, not 3 * g", "sm",
     [("_dbl.BPO_STRIDE * g, 3))", "_dbl.BPO_STRIDE * side, 3))")], {"DBobsfields"}),
    ("MS17 observe reads +0x60 off the SYMBOL (the pointer not followed, KI-115)", "sm",
     [("        raw = bytes(context.emulator.read_bytes(ptr + _dbl.BPO_OFFSET + _dbl.BPO_STRIDE * g, 3))",
       '        raw = bytes(read_symbol("gBattleStruct", offset=_dbl.BPO_OFFSET + _dbl.BPO_STRIDE * g, size=3))')],
     {"DBobsfields"}),
    ("MS18 the `[DBLITEM] use` line dropped", "sm",
     [('        _log_story_event(f"use side={side} g={g} item=',
       '        (lambda *_a, **_k: None)(f"use side={side} g={g} item=')], {"DBuse"}),
    ("MS19 observe's disc compares the party index with g, not the side", "sm",
     [("disc={int(party_index != side)}", "disc={int(party_index != g)}")], {"DBobsdisc"}),
    ("MS20 the fail-open removed (the policy's exception escapes)", "sm",
     [("        try:\n            action = _dbl_act(self, battle_state, battler_index)\n        except Exception as error:"
       "  # noqa: BLE001 - D9: FAIL OPEN — a battle that worked before must keep working\n"
       '            _log_story_event(f"err side={battler_index} g={2 * battler_index} {type(error).__name__}: {error}",\n'
       '                             "DBLITEM")\n            action = None\n',
       "        action = _dbl_act(self, battle_state, battler_index)\n")], {"DBerr"}),
    ("MS21 the KEYITEMS gate removed from _maybe_use_item (D6's composition)", "sm",
     [('        if _os.environ.get("POKEBOT_R27_KEYITEMS") == "1" and not _r27_key_gate(self, battle_state):\n'
       "            return None\n", "")], {"DQ10"}),
    ("MS22 MENTION ONLY: a comment writing `doubles=False` turns NOTHING red", "sm",
     [("def _dbl_act(strategy, battle_state, side: int):",
       "# strategy._maybe_use_item(battle_state, side=side, doubles=False)  -- a comment, never code\n"
       "def _dbl_act(strategy, battle_state, side: int):")], set()),
    # ---- battle_action_selection.py (the executor half) -----------------------------------------------------------
    ("MB01 battle_action_use_move drops the side (byte 0 for battler 2)", "bas",
     [("        yield from scroll_to_battle_action(0, battler_index > 1)",
       "        yield from scroll_to_battle_action(0)")], {"DBmove", "DBc1ast"}),
    ("MB02 battle_action_use_item drops the side", "bas",
     [("    yield from scroll_to_battle_action(1, battler_index > 1)", "    yield from scroll_to_battle_action(1)")],
     {"DQ12", "DBc1ast"}),
    ("MB03 RotateLead drops the side", "bas",
     [("                yield from scroll_to_battle_action(2, battler_index > 1)",
       "                yield from scroll_to_battle_action(2)")], {"DBc1ast"}),
    ("MB04 the UseItem case drops the battler", "bas",
     [("                yield from battle_action_use_item(battle_state, index, target_index, battler_index)",
       "                yield from battle_action_use_item(battle_state, index, target_index)")], {"DBc4ast"}),
    ("MB05 the guard trusts the AIM, not the cursor's slotId (review F8)", "bas",
     [("        slot = party_menu[9]", "        slot = aim")], {"DQ14"}),
    ("MB06 the guard's verdict is logged, then A is pressed anyway", "bas",
     [("        if _dbl_ctx is None or _dbl_guard(_dbl_ctx, _menu_slot):",
       "        if _dbl_ctx is None or _dbl_guard(_dbl_ctx, _menu_slot) or True:")],
     {"DQ14", "DQ15", "DBself", "DBguardraise", "DBmenuclosed"}),
    ("MB07 the guard fails OPEN on a read error", "bas",
     [('        ok = press = False\n        f["err"] = type(error).__name__',
       '        ok, press = False, True\n        f["err"] = type(error).__name__')], {"DBguardraise", "DBmenuclosed"}),
    ("MB08 the self binding dropped from the guard", "bas",
     [('        ok = bool(ctx["self"]) and _dbl.guard_ok(', "        ok = _dbl.guard_ok(")], {"DBself"}),
    ("MB09 the executor's flag test dropped (every double runs the step-13 path)", "bas",
     [("    if not _dbl_env(_DBL_FLAG):\n        return False\n", "")], {"DQ16", "DQ17"}),
    ("MB10 D11's exit removed", "bas",
     [("            if _d11 and get_battle_controller_callback(2) in _DBL_CHOOSE_ACTION:",
       "            if False and get_battle_controller_callback(2) in _DBL_CHOOSE_ACTION:")], {"DQ16"}),
    ("MB11 D11 binds battler 2's loop as well", "bas",
     [("        _d11 = battler_index == 0 and _dbl_on(battle_state)", "        _d11 = _dbl_on(battle_state)")],
     {"DBd11b2"}),
    ("MB12 the `after` line's partner read at g, not g ^ 2", "bas",
     [('        ctx["partner"] = _dbl.battler_party_index(indexes, battler_index ^ 2)',
       '        ctx["partner"] = _dbl.battler_party_index(indexes, battler_index)')], {"DQ13"}),
    ("MB13 the `after` line dropped", "bas",
     [("        if _dbl_ctx is not None:\n            _dbl_after(_dbl_ctx, item)",
       "        if False:\n            _dbl_after(_dbl_ctx, item)")], {"DQ13", "DQ15"}),
    ("MB14 the intended PID read at the requester's MENU slot as a party index (the index-space slip)", "bas",
     [('offset=100 * target_index, size=4))', 'offset=100 * (battler_index // 2), size=4))')], {"DQ13", "DQ15"}),
    ("MB16 the executor's double test dropped (a flag-on SINGLE runs the guard)", "bas",
     [("        return bool(battle_state.is_double_battle)", "        return True")], {"DBsingleexec"}),
    ("MB17 the guard's menu-open precondition dropped", "bas",
     [('        if get_game_state() != GameState.PARTY_MENU:\n            raise RuntimeError("the party menu is not open")\n',
       "")], {"DBmenuclosed"}),
    ("MB15 MENTION ONLY: a comment writing `scroll_to_battle_action(2)` turns NOTHING red", "bas",
     [('_DBL_FLAG = "POKEBOT_R27_DOUBLEITEMS"',
       '# yield from scroll_to_battle_action(2)  -- a comment, never code\n_DBL_FLAG = "POKEBOT_R27_DOUBLEITEMS"')],
     set()),
    # ---- battle_menuing.py (C1) -----------------------------------------------------------------------------------
    ("MM01 scroll_to_battle_action drops the side (upstream's byte 0)", "bm",
     [('    yield from _select_in_menu("gActionSelectionCursor", action_index, is_right_side_pokemon)',
       '    yield from _select_in_menu("gActionSelectionCursor", action_index)')], {"DQ11", "DQ12"}),
    ("MM02 the CURSOR0 switch inverted (byte 0 unless the fault is set)", "bm",
     [('        if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") == "1":',
       '        if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") != "1":')], {"DQ11", "DQ12"}),
]
#: LEFT OUT, with the argument (not run): MB-range — reading the PID at an out-of-range slot in the executor is
#: EQUIVALENT: `guard_ok` refuses any slot outside [0, count) whatever PID it is handed (MD08 pins that check).

_MUTANT_IDS: set = set()
_SRCS: dict = {}


def _jobs() -> list:
    return ([("fault", f"FAULT {env}", env, None, set(want)) for env, want in FAULT_SETS.items()]
            + [("mutant", label, target, edits, set(want)) for label, target, edits, want in MUTANTS])


JOBS: list = _jobs()


def _sources() -> dict:
    if not _SRCS:
        _SRCS.update({k: p.read_text(encoding="utf-8") for k, p in PATHS.items()})
    return _SRCS


def _apply(src: str, edits) -> str:
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            raise AssertionError(f"mutant anchor found {n} times: {old[:90]!r}")
        src = src.replace(old, new)
    return src


def _install(name: str, path, source: str, i: int):
    """Exec `source` as module `name` (never written to disk), and point the PACKAGE attribute at it too: a
    `from modules.story import double_items` inside production reads the package attribute first."""
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    mod.__package__ = name.rsplit(".", 1)[0]
    sys.modules[name] = mod
    parent, child = name.rsplit(".", 1)
    setattr(sys.modules[parent], child, mod)
    exec(compile(source, f"<mutant {i}>", "exec"), mod.__dict__)


def _job_red(i: int):
    """ONE fault or mutant: apply it (in memory, or in the env), run every row tagged, restore. Returns (i, the sorted
    red rows or None, an error text). Runs in a pool worker, or in-process."""
    kind, _label, target, edits, _want = JOBS[i]
    srcs = _sources()
    real = {n: sys.modules[n] for n in NAMES.values()}
    saved_env = {k: os.environ.get(k) for k in ROW_ENVS + FAULT_ENVS}
    try:
        for k in ROW_ENVS + FAULT_ENVS:
            os.environ.pop(k, None)
        msrcs = dict(srcs)
        if kind == "fault":
            os.environ[target] = "1"
        else:
            msrcs[target] = _apply(srcs[target], edits)
            _install(NAMES[target], PATHS[target], msrcs[target], i)
        return i, sorted(all_rows("m", msrcs)), ""
    except Exception as error:  # noqa: BLE001 - a job that cannot even run is a failed check, reported
        return i, None, f"{type(error).__name__}: {error}"
    finally:
        for name, mod in real.items():
            sys.modules[name] = mod
            parent, child = name.rsplit(".", 1)
            setattr(sys.modules[parent], child, mod)
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _run_jobs(inprocess: bool) -> tuple[dict, str]:
    results: dict = {}
    if not inprocess:
        try:
            from concurrent.futures import ProcessPoolExecutor
            workers = max(2, min(8, (os.cpu_count() or 2)))
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for i, red, err in pool.map(_job_red, range(len(JOBS)), chunksize=2):
                    results[i] = (red, err)
            return results, f"a pool of {workers} processes"
        except Exception as error:  # noqa: BLE001 - no pool: the same jobs in-process
            results.clear()
            how = f"in-process (no pool: {type(error).__name__}: {error})"
    else:
        how = "in-process (--inprocess)"
    for i in range(len(JOBS)):
        _i, red, err = _job_red(i)
        results[i] = (red, err)
    return results, how


def main() -> int:
    t0 = time.perf_counter()
    inprocess = "--inprocess" in sys.argv[1:]
    for k in ROW_ENVS + FAULT_ENVS:                         # the rows set what they need; an ambient value would skew them
        os.environ.pop(k, None)
    srcs = _sources()
    print("DP — the pre-registered PURE rows (and the builder's DB rows), `double_items` executed")
    pure_rows("")
    print("\nDQ01-DQ10 — the STRATEGY on the REAL class and a REAL double BattleState")
    strategy_rows("")
    print("\nDQ11-DQ17 — the EXECUTOR and C1, driven frame by frame")
    executor_rows("")
    print("\nDB — AST pins")
    ast_rows("", srcs)
    baseline = all_rows("m", srcs)
    if baseline:
        print(f"\n⛔ BASELINE RED (no fault, no mutant): {sorted(baseline)} — a defect in the code under test. These rows "
              f"are left out of every job comparison below until fixed.")
    t1 = time.perf_counter()
    results, how = _run_jobs(inprocess)
    t2 = time.perf_counter()
    print(f"\nF/M — faults and mutants (each must turn EXACTLY its named rows red; {len(FAULT_SETS)} faults, "
          f"{len(JOBS) - len(FAULT_SETS)} mutants, run in {how}, {t2 - t1:.1f} s)")
    covered: set = set()
    for i, (_kind, label, _target, _edits, want) in enumerate(JOBS):
        red, err = results[i]
        if red is None:
            check(label, False, err)
            continue
        red = set(red) - baseline
        want_now = set(want) - baseline
        covered |= set(want)
        check(label, red == want_now, f"red {sorted(red)}" + ("" if red == want_now else f" (want {sorted(want_now)})"))
    uncovered = sorted(ROW_NAMES - covered)
    check("COVERAGE every row is in at least one fault's or mutant's expected red set", not uncovered,
          f"{len(ROW_NAMES)} rows; uncovered {uncovered}")
    wall = time.perf_counter() - t0
    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s) in {wall:.1f} s:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL PASS ({len(ROW_NAMES)} rows, {len(FAULT_SETS)} faults, {len(JOBS) - len(FAULT_SETS)} mutants) "
          f"in {wall:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
