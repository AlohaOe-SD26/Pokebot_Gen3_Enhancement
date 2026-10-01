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
  THE FOLD (2026-09-30, `evidence/2026-09-30-doubleitems13-ADVERSARIAL.txt`, three independent agents; every claim
  re-derived on this code before it became a row):
  SF1-cure, SF2-*, N2-import  the three PRODUCTION FIXES' rows. Each is red on the literal 799e6adf code and green on
             the fix (the RV-* revert mutants keep that proof standing). SF2-bound and SF2-unset are green on both: they
             pin the bound and the untouched flag-unset loop.
  X01-X13    the executor hunter's rows. ⭐ X01 is the one that mattered: DQ14 stops on Cancel, so it never proved the PID
             is read at the ACTUAL slot (DQ14 is now labelled so); X01 stops on slot 0, the living partner.
  K-*        the strategy hunter's rows (its K-fullrestore kept only its pure half, K-hp255, and its K-obs-cure was dropped:
             SF-1 made "no cure in a double" the intended behaviour; K-ledger-switch from its addendum).
  ⛔ ISOLATION: a row whose own subject a fault changes (a refusal NOGUARD would press, a fault's own shape) runs under
  `iso_env`, which clears the job's fault — so the PRE-REGISTERED fault sets stay EXACT. X02 deliberately does not.
  Every fixture's battle type now carries IS_MASTER (a real battle always does; K-scope-real adds TWO_OPPONENTS).
FAULTS      the three C7 production envs (never set in a real run; `29-DISABLED-FEATURES-REGISTRY.md`), each with the
            EXACT red set the PREDICTIONS filed: CURSOR0 {DQ11, DQ12}; WRONGSLOT {DQ13}; NOGUARD {DQ15}. ⇒ DQ14's refusal
            comes from the RANGE check (the scroll stops on Cancel, slot 7), which NOGUARD — skipping only the PID
            comparison — keeps; so NOGUARD leaves DQ14 green (the builder's statement the PREDICTIONS asked for).
MUTANTS     exec'd source edits (never written to disk) of the four files, one per rule, each with an EXACT red set.
            MUTANTS: the build's own (written before their first run; MUTANT_ADDITIONS records, honestly labelled, what
            each ALSO reddens among the fold's rows — MEASURED, then explained one by one). FOLD_MUTANTS: the fix reverts,
            SF-2's rules and the adversaries' REAL survivors (derived before their first run). FAULT_MUTANTS: mutants in
            fault-arm code, run UNDER their fault (the old runner never set a fault with a mutant installed, so 14 of the
            executor hunter's kills were invisible). Three mention-only edits must turn NOTHING red: a gate that fires on
            a comment teaches the reader to bypass it. COVERAGE fails if any row is in no fault's or mutant's set. Jobs
            run in a process pool, in-process if no pool can be made (`--inprocess` forces it).

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
ROW_ENVS = (FLAG, KEYITEMS, FRAC, "POKEBOT_R27_FAULT_RAISE", "POKEBOT_R27_FAULT_ALLORDINARY",
            "POKEBOT_RESERVE_FAULT_NOLOCK")
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
                                          "Full Restore", "X Attack", "Repel", "Max Potion", "Ether", "Max Ether")}
POTION = ITEM["Potion"]
PARENT = ("PARENT", None)
#: OUR two battlers. ⭐ Both DISCRIMINATE: party 1 at side 0, party 4 at side 1, so an index-space mix-up gives a
#: different answer (D8). The PIDs are the Step-0 fixture's (Sceptile, Mightyena).
L_PID, R_PID, O1_PID, O3_PID = 0x863B0917, 0x5C96EA9B, 0x0C1A7D01, 0x05017D03
L_IDX, R_IDX = 1, 4
BPI_RAW = struct.pack("<4H", L_IDX, 0, R_IDX, 1)                     # gBattlerPartyIndexes, u16[4]
TRAINER, DOUBLE, MULTI, PARTNER = 1 << 3, 1 << 0, 1 << 6, 1 << 22
#: ‼ THE FOLD (2026-09-30, the strategy hunter's N06/N07): a REAL battle never carries Trainer|Double alone. IS_MASTER
#: is set in every non-link battle (pret `battle_main.c:1009-1010`) and every two-trainer double has TWO_OPPONENTS
#: (`battle_setup.c:1274-1275`, Route 123's P family). A fixture with the bare two bits let an exact-match scope test
#: pass every row while making the feature dead live. Every fixture now carries IS_MASTER; K-scope-real adds both.
IS_MASTER, TWO_OPP = 1 << 2, 1 << 15
REAL_DOUBLE = TRAINER | DOUBLE | IS_MASTER
SWELLOW_PID = 0x0B30A747


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


def dstate(*, lhp=90, rhp=90, lst=0, rst=0, flags=REAL_DOUBLE, turn=3, order=(1, 4, 0, 2, 3, 5), bpi=None,
           single=False, left=("Sceptile", L_PID), right=("Mightyena", R_PID), absent=0) -> BattleState:
    """A REAL double `BattleState`: our left Sceptile (party 1) and right Mightyena (party 4), both /100, against a
    Claydol and a Solrock. `lst` / `rst` are our battlers' status1 (2 = asleep); `bpi` overrides gBattlerPartyIndexes;
    `left` / `right` replace a battler's (species, PID); `absent` is gAbsentBattlerFlags; `single` makes it a SINGLE
    trainer battle (two battlers, no Double bit)."""
    battler = (mon_rec(SPECIES_ID[left[0]], lhp, 100, left[1], lst)
               + mon_rec(SPECIES_ID["Claydol"], 80, 80, O1_PID))
    if not single:
        battler += (mon_rec(SPECIES_ID[right[0]], rhp, 100, right[1], rst)
                    + mon_rec(SPECIES_ID["Solrock"], 80, 80, O3_PID))
    return BattleState(battle_type=struct.pack("<I", TRAINER | IS_MASTER if single else flags), side_timers=bytes(24),
                       battler_party_indexes=BPI_RAW if bpi is None else struct.pack("<4H", *bpi),
                       battler_party_order=pack_order(order), battler_count=2 if single else 4, battler=battler,
                       battler_status3=bytes(16), battler_disable_structs=bytes(0x70), absent_battler_flags=absent,
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
def iso_env(values):
    """An env for ONE row that ALSO saves, clears and restores the three C7 fault envs (the executor hunter's
    `iso_env`). ⛔ For the rows whose own subject a fault would change (a refusal NOGUARD would press, the faults' own
    shapes): without it they would join a fault's red set, and the PRE-REGISTERED sets (CURSOR0 {DQ11, DQ12},
    WRONGSLOT {DQ13}, NOGUARD {DQ15}) would no longer be exact. A row that SHOULD run under the job's fault (X02, which
    kills a mutant only a fault job reveals) does not use it."""
    keys = ROW_ENVS + FAULT_ENVS
    saved = {k: os.environ.get(k) for k in keys}
    try:
        for k in keys:
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
def sworld(*, env=None, state=None, fresh=None, bag=None, cls=0x20, reserved=None, reserved_raises=False,
           mui_raises=False, cursor=bytes([0, 0, 1, 0])):
    """Production's world for the STRATEGY rows: the env (the row's flags only), `read_symbol` over fake symbols
    (recorded), EWRAM behind `*gBattleStruct` (recorded), the bag (counted), the opponent reader (counted; trainer 271,
    class `cls`), the RULING 18 reserve, the logger (recorded), `choose_healing_item` spied (its `options` recorded),
    `_maybe_use_item` and `_r27_key_gate` spied (counted), the parent's double turn (PARENT), and `get_battle_state`
    REBOUND wherever bound (counted; it returns `fresh`, else `state`).
    The reserve (the fold of the three-lens review's N1): `league_reserve.reserved_quantities` is faked — `reserved`
    ({} = not armed), or a raise — so the REAL logging filter (`_maybe_use_item`'s) and observe's silent one see the same
    reserve; `league_reserve._warned` is EMPTIED for the world and restored after, so a row sees its own log lines and
    never leaks a latch into the next one."""
    sm = SM()
    lr = modules.story.league_reserve
    saved_warned = set(lr._warned)
    lr._warned.clear()
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

    def fake_reserved():
        if reserved_raises:
            raise RuntimeError("the reserve read is broken")
        return dict(reserved or {})

    patches = [(modules.memory, "read_symbol", fake_read), (modules.items, "get_item_bag", fake_bag),
               (modules.debug_logger, "event", fake_event), (TI, "read_opponent_trainers", fake_reader),
               (TI, "trainer_class", lambda _tid, *_a, **_k: cls),
               (lr, "reserved_quantities", fake_reserved),
               (modules.story.battle_items, "choose_healing_item", spy_chi),
               (modules.pokemon_party, "get_party", lambda: PARTY6),
               (sm, "context", types.SimpleNamespace(emulator=types.SimpleNamespace(read_bytes=fake_bytes))),
               (sm, "_r27_key_gate", spy_kg), (sm.StoryItemBattleStrategy, "_maybe_use_item", spy_mui),
               (sm.LevelUpTravelBattleStrategy, "decide_turn_in_double_battle", lambda _s, _bs, _bi: PARENT)]
    for mod in list(sys.modules.values()):
        if isinstance(mod, types.ModuleType) and mod.__dict__.get("get_battle_state") is ORIG_GBS:
            patches.append((mod, "get_battle_state", fake_gbs))
    try:
        with _env(env), _patched(patches):
            yield log
    finally:
        lr._warned.clear()
        lr._warned.update(saved_warned)


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

        # RULING 18's shape, armed: hold one Hyper Potion and the whole Full Restore line back. ⛔ Given as the RESERVED
        # QUANTITIES, so `_maybe_use_item` runs the REAL filter and observe its silent twin (the fold of N1).
        reserved = {"Hyper Potion": 1, "Full Restore": 1}
        st = dstate(lhp=20)
        s1 = new_strategy()
        with sworld(state=st, bag=bag, reserved=reserved) as log1:
            s1._maybe_use_item(st)                              # the singles call: what it hands the HP policy
        s2 = new_strategy()
        with sworld(env={FLAG: "observe"}, state=st, bag=bag, reserved=reserved) as log2:
            s2.decide_turn_in_double_battle(st, 0)              # observe's mirror, through production
            mirror = DBL().heal_options(bag.items, SM()._dbl_reserve_silent)

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
        # The fold (2026-09-30): look for side 1's pending request in ANY ledger, never at one assumed key — keying by
        # party index or by species name is the same behaviour, and a row must not redden on an implementation detail.
        pending = next((led.get("_hp_when_item_requested") for led in getattr(s, "_dbl_ledgers", {}).values()
                        if led.get("_hp_when_item_requested") is not None), None)
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
            st = dstate(lhp=20, flags=REAL_DOUBLE | extra)
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
        st = dstate(lhp=20, flags=REAL_DOUBLE | MULTI)
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

    # ---------------------------------------------------------------------- the PRODUCTION FIXES (2026-09-30)
    def sf1_cure():
        # SF-1: asleep at full HP, the bag a Full Heal AND a Full Restore. A double asks NO cure policy (D10), so the
        # parent's turn — the first build spent the Full Restore here — and observe mirrors it (`would=-`).
        bag = (("Full Heal", 1), ("Full Restore", 1))
        st = dstate(lhp=100, lst=2)
        s = new_strategy()
        with sworld(env={FLAG: "1"}, state=st, bag=Bag(*bag)):
            act = s.decide_turn_in_double_battle(st, 0)
        s2 = new_strategy()
        with sworld(env={FLAG: "observe"}, state=st, bag=Bag(*bag)) as log:
            s2.decide_turn_in_double_battle(st, 0)
        o = one(lines(log, "DBLITEM-OBS"))
        ok = act == PARENT and field(o, "would") == "-" and field(o, "why") == "above_fraction"
        return ok, f"flag 1 {act}; observe {o}"

    def n2_import():
        # N2: with `double_items` unimportable, the flag-unset path still returns the parent's turn (the flag test runs
        # before any import), and the flag-on path fails OPEN to it.
        pkg = modules.story
        saved_attr, saved_mod = pkg.__dict__.get("double_items"), sys.modules.get(DBL_NAME)
        out = {}
        try:
            if "double_items" in pkg.__dict__:
                delattr(pkg, "double_items")
            sys.modules[DBL_NAME] = None                       # `import modules.story.double_items` now raises
            for flag in (None, "1"):
                s = new_strategy()
                st = dstate(lhp=20)
                with sworld(env={FLAG: flag} if flag else None, state=st) as log:
                    try:
                        out[flag] = s.decide_turn_in_double_battle(st, 0)
                    except Exception as error:  # noqa: BLE001 - the row reports a raise as its own red result
                        out[flag] = f"raised {type(error).__name__}"
        finally:
            sys.modules[DBL_NAME] = saved_mod
            setattr(pkg, "double_items", saved_attr)
        return out == {None: PARENT, "1": PARENT}, f"{out}"

    # ---------------------------------------------------------------------- the THREE-LENS REVIEW's N1 (2026-09-30)
    def r_silent():
        # N1: in the reserve era observe must stay SILENT — no `[RESERVE]` line, the `_warned` latch untouched — on an
        # input where the REAL filter DOES log (the control at the end proves the input is not vacuous).
        lr = modules.story.league_reserve
        bag = Bag(("Potion", 1), ("Hyper Potion", 2))
        st = dstate(lhp=20)
        s = new_strategy()
        with sworld(env={FLAG: "observe"}, state=st, bag=bag, reserved={"Hyper Potion": 1}) as log:
            s.decide_turn_in_double_battle(st, 0)
            obs_reserve = [m for c, m in log.events if c == "RESERVE"]
            latch_after_obs = set(lr._warned)
            lr.filter_medicine_for_reserve([(ITEM["Hyper Potion"], 2, 200)])        # the control: the real filter
            control = [m for c, m in log.events if c == "RESERVE"]
        ok = not obs_reserve and not latch_after_obs and len(control) == 1 and len(lines(log, "DBLITEM-OBS")) == 1
        return ok, f"observe RESERVE lines {obs_reserve}; latch {latch_after_obs}; control {len(control)} line(s)"

    def r_parity():
        # N1: the silent filter's OUTPUT equals the real one's — armed, not armed, NOLOCK — and, through
        # `heal_options`, on a broken reserve read (both fail UNLOCKED).
        lr = modules.story.league_reserve
        med = [(ITEM["Potion"], 2, 20), (ITEM["Hyper Potion"], 2, 200), (ITEM["Full Restore"], 1, 255),
               (ITEM["Full Heal"], 1, 0)]
        armed = {"Hyper Potion": 1, "Full Restore": 1}
        res = {}
        for name, reserved, env in (("armed", armed, None), ("unarmed", {}, None),
                                    ("nolock", armed, {"POKEBOT_RESERVE_FAULT_NOLOCK": "1"})):
            with sworld(env=env, reserved=reserved):
                silent, real = SM()._dbl_reserve_silent(list(med)), lr.filter_medicine_for_reserve(list(med))
            res[name] = (silent == real, [(i.name, q) for i, q, _p in silent])
        bag = Bag(("Potion", 2), ("Hyper Potion", 1))
        with sworld(reserved_raises=True):
            a = DBL().heal_options(bag.items, SM()._dbl_reserve_silent)
            b = DBL().heal_options(bag.items, lr.filter_medicine_for_reserve)
        res["raise"] = (a == b and len(a) == 2, [(i.name, q) for i, q, _p in a])
        ok = all(v[0] for v in res.values()) and res["armed"][1] != [(i.name, q) for i, q, _p in med]
        return ok, f"{res}"

    # ---------------------------------------------------------------------- the ADVERSARIAL fold (2026-09-30), strategy
    def k_mode():
        d = DBL()
        got = [d.mode({FLAG: v}) for v in ("OBSERVE", "Observe", "observe ", "1 ", "10", "1\n")]
        return got == [d.OFF] * 6, f"{got}"

    def k_scope_real():
        d = DBL()
        pure = [d.in_scope(REAL_DOUBLE), d.in_scope(REAL_DOUBLE | TWO_OPP)]
        s = new_strategy()
        st = dstate(lhp=20, flags=REAL_DOUBLE | TWO_OPP)                      # Route 123's two-trainer double
        with sworld(env={FLAG: "1"}, state=st):
            act = s.decide_turn_in_double_battle(st, 0)
        return pure == [True, True] and act == use(POTION, L_IDX), f"{pure}; {act}"

    def k_active():
        got = DBL().active_positions([3, 1, 0, 2, 4, 5])
        return got == (3, 1), f"{got}"

    def k_guardnone():
        a = 0x5C96EA9B
        got = [DBL().guard_ok(a, a, None, 6), DBL().guard_ok(a, a, 0, None)]
        return got == [False, False], f"{got}"

    def k_guardhigh():
        a = 0x5C96EA9B
        got = DBL().guard_ok(a, a ^ 0x0001_0000, 0, 6)
        return got is False, f"{got}"

    def k_hp255():
        fr, mp = ITEM["Full Restore"], ITEM["Max Potion"]
        got = DBL().hp_only([(fr, 1, 255), (mp, 1, 255)])
        return got == [(fr, 1, 255), (mp, 1, 255)], f"{len(got)} kept"

    def k_parity_noreserve():
        bag = Bag(("Potion", 3), ("Full Restore", 1), ("Full Heal", 1))
        st = dstate(lhp=20)
        s1 = new_strategy()
        with sworld(state=st, bag=bag) as log1:
            s1._maybe_use_item(st)
        s2 = new_strategy()
        with sworld(env={FLAG: "observe"}, state=st, bag=bag) as log2:
            s2.decide_turn_in_double_battle(st, 0)
        mirror = DBL().heal_options(bag.items, lambda m: m)

        def names(opts):
            return [(o[0].name, o[1], o[2]) for o in opts]

        want = [("Potion", 3, 20), ("Full Restore", 1, 255)]
        got1 = names(log1.hp_opts[0]) if len(log1.hp_opts) == 1 else log1.hp_opts
        got2 = names(log2.hp_opts[0]) if len(log2.hp_opts) == 1 else log2.hp_opts
        return got1 == got2 == names(mirror) == want, f"{got1}; {got2}; {names(mirror)}"

    def k_reserve_raise():
        bag = Bag(("Potion", 2), ("Hyper Potion", 1))

        def boom(_medicine):
            raise RuntimeError("the reserve broke")

        a, b = DBL().heal_options(bag.items, boom), DBL().heal_options(bag.items, None)
        return a == b and len(a) == 2, f"{len(a)} {len(b)}"

    def k_ether():
        bag = Bag(("Potion", 1), ("Ether", 1), ("Max Ether", 1))
        got = [(o[0].name, o[2]) for o in DBL().heal_options(bag.items, None)]
        return got == [("Potion", 20)], f"{got}"

    def k_why_boundary():
        got = DBL().hp_decline_reason(35, 100, [(POTION, 1, 20)], worst_hit_taken=50)
        return got == "losing_race", f"{got}"

    def k_worst_per_mon():
        # the PARTNER's 60-HP hit must not make the requester's Potion a losing race (D3: the worst hit is per Pokémon)
        s = new_strategy()
        acts = []
        for side, lhp, rhp in ((1, 90, 90), (1, 90, 30), (0, 30, 30)):
            st = dstate(lhp=lhp, rhp=rhp)
            with sworld(env={FLAG: "1"}, state=st):
                acts.append(s.decide_turn_in_double_battle(st, side))
        return acts == [PARENT, PARENT, use(POTION, L_IDX)], f"{[a[0] for a in acts]}"

    def k_cap_shared():
        s = new_strategy()
        s._item_uses = 4                                        # the PER-BATTLE cap already spent
        st = dstate(lhp=20)
        with sworld(env={FLAG: "1"}, state=st):
            a1 = s.decide_turn_in_double_battle(st, 0)
        s2 = new_strategy()
        st2 = dstate(rhp=20)
        with sworld(env={FLAG: "1"}, state=st2):
            a2 = s2.decide_turn_in_double_battle(st2, 1)
        return a1 == PARENT and a2 == use(POTION, R_IDX) and s2._item_uses == 1, f"{a1[0]} {a2[0]} {s2._item_uses}"

    def k_key_once():
        s = new_strategy()
        kb = []
        for side, st in ((0, dstate(lhp=20)), (1, dstate(rhp=20))):
            with sworld(env={FLAG: "1", KEYITEMS: "1"}, state=st, cls=0x20) as log:
                s.decide_turn_in_double_battle(st, side)
            kb += lines(log, "KEYBATTLE")
        return len(kb) == 1, f"{kb}"

    def k_d10_side1():
        s = new_strategy()
        st = dstate(rhp=100, rst=2)                             # the RIGHT asleep at full HP
        with sworld(env={FLAG: "1"}, state=st, bag=Bag(("Full Heal", 1))):
            act = s.decide_turn_in_double_battle(st, 1)
        return act == PARENT, f"{act}"

    def k_ledger_switch():
        # side 1's Mightyena takes a 60 hit; a DIFFERENT Pokémon (Swellow, party 2) then holds side 1 at 30: its own
        # ledger, so the old Pokémon's worst hit must not refuse its Potion.
        s = new_strategy()
        acts = []
        for st in (dstate(rhp=90), dstate(rhp=30),
                   dstate(rhp=30, right=("Swellow", SWELLOW_PID), bpi=(L_IDX, 0, 2, 1))):
            with sworld(env={FLAG: "1"}, state=st):
                acts.append(s.decide_turn_in_double_battle(st, 1))
        return acts == [PARENT, PARENT, use(POTION, 2)], f"{[a[0] for a in acts]}"

    def obs1(s, st, side=0, **kw):
        with sworld(state=st, **kw) as log:
            s.decide_turn_in_double_battle(st, side)
        return one(lines(log, "DBLITEM-OBS"))

    def k_obs_switch():
        s = new_strategy()
        obs1(s, dstate(lhp=90), env={FLAG: "observe"})
        o = obs1(s, dstate(lhp=30, left=("Swellow", SWELLOW_PID), bpi=(2, 0, R_IDX, 1)), env={FLAG: "observe"})
        return field(o, "worst") == "0" and field(o, "would") == "Potion", f"{o}"

    def obs_seq(hps):
        s = new_strategy()
        return [obs1(s, dstate(lhp=h), env={FLAG: "observe"}) for h in hps]

    def k_obs_maxworst():
        o = obs_seq((90, 60, 50))
        return field(o[2], "worst") == "30", f"{[field(x, 'worst') for x in o]}"

    def k_obs_rise():
        o = obs_seq((30, 90, 80))
        return field(o[2], "worst") == "10", f"{[field(x, 'worst') for x in o]}"

    def k_obs_cap():
        s = new_strategy()
        s._item_uses = 4
        o = obs1(s, dstate(lhp=20), env={FLAG: "observe"})
        return (field(o, "would"), field(o, "why"), field(o, "uses")) == ("-", "cap", "4"), f"{o}"

    def k_obs_ineff():
        s = new_strategy()
        s._items_ineffective = True
        o = obs1(s, dstate(lhp=20), env={FLAG: "observe"})
        return (field(o, "would"), field(o, "why")) == ("-", "ineffective"), f"{o}"

    def k_obs_frac():
        s = new_strategy()
        o = obs1(s, dstate(lhp=70), env={FLAG: "observe", FRAC: "0.8"})
        return (field(o, "would"), field(o, "why")) == ("Potion", "hp"), f"{o}"

    def k_obs_two():
        s = new_strategy()
        st = dstate(lhp=20, flags=REAL_DOUBLE | TWO_OPP)
        with sworld(env={FLAG: "observe", KEYITEMS: "1"}, state=st) as log:
            with _patched([(TI, "read_opponent_trainers", lambda _two: (300, 271)),
                           (TI, "trainer_class", lambda tid, *_a, **_k: {300: 0x05, 271: 0x20}[tid])]):
                s.decide_turn_in_double_battle(st, 0)
        o = one(lines(log, "DBLITEM-OBS"))
        return (field(o, "key"), field(o, "would")) == ("1", "Potion"), f"{o}"

    def k_obs_dict():
        s = new_strategy()
        before = copy.deepcopy(s.__dict__)
        for h in (60, 30):
            obs1(s, dstate(lhp=h), env={FLAG: "observe"})
        after = {k: v for k, v in s.__dict__.items() if k != "_dbl_obs"}
        return after == before, f"changed {[k for k in after if before.get(k) != after.get(k)]}"

    def k_obs_null():
        s = new_strategy()
        st = dstate(lhp=20)
        with sworld(env={FLAG: "observe"}, state=st) as log:
            inner = modules.memory.read_symbol

            def rs(name, offset=0, size=0):
                return bytes(4) if name == "gBattleStruct" else inner(name, offset, size)

            with _patched([(modules.memory, "read_symbol", rs)]):
                s.decide_turn_in_double_battle(st, 0)
        o = one(lines(log, "DBLITEM-OBS"))
        return (field(o, "bpo"), field(o, "bpo_pos")) == ("?", "?"), f"{o}"

    def k_absent():
        s = new_strategy()
        st = dstate(rhp=20, absent=0b0100)                     # battler 2 absent: no right Pokémon
        with sworld(env={FLAG: "1"}, state=st) as log:
            act = s.decide_turn_in_double_battle(st, 1)
        return act == PARENT and not dbl_events(log), f"{act}; {dbl_events(log)}"

    def k_obs_key0():
        s = new_strategy()
        o = obs1(s, dstate(lhp=20), env={FLAG: "observe"}, cls=0x05)
        return (field(o, "key"), field(o, "would")) == ("0", "Potion"), f"{o}"

    def k_obs_keyitems0():
        s = new_strategy()
        o = obs1(s, dstate(lhp=20), env={FLAG: "observe", KEYITEMS: "0"}, cls=0x05)
        return (field(o, "would"), field(o, "why")) == ("Potion", "hp"), f"{o}"

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
        ("SF1-cure [fix] asleep at 100/100, Full Heal + Full Restore: flag 1 asks no cure (the parent's turn); observe "
         "would=-", sf1_cure),
        ("N2-import [fix] double_items unimportable: flag unset -> the parent's turn (no raise); flag 1 fails open",
         n2_import),
        ("R-silent [review N1] observe in the reserve era: no [RESERVE] line, the latch untouched (the real filter "
         "logs on the same input)", r_silent),
        ("R-parity [review N1] the silent filter's output = the real filter's: armed, unarmed, NOLOCK, a broken read",
         r_parity),
        ("K-mode [adversary] mode(): OBSERVE / Observe / 'observe ' / '1 ' / '10' / '1\\n' are all OFF", k_mode),
        ("K-scope-real [adversary] real flags (IS_MASTER, TWO_OPPONENTS) are in scope; flag 1 acts there", k_scope_real),
        ("K-active [adversary] active_positions keeps order: [3,1,...] -> (3, 1)", k_active),
        ("K-guardnone [adversary] guard_ok with slot or count None -> False, no raise", k_guardnone),
        ("K-guardhigh [adversary] guard_ok compares all 32 PID bits", k_guardhigh),
        ("K-hp255 [adversary] hp_only keeps the 255 items (Full Restore, Max Potion)", k_hp255),
        ("K-parity-noreserve [adversary] DQ03 with no reserve: Full Restore on all three sides of the parity",
         k_parity_noreserve),
        ("K-reserve-raise [adversary] heal_options fails UNLOCKED on a raising reserve", k_reserve_raise),
        ("K-ether [adversary] heal_options excludes PP items (Ether, Max Ether)", k_ether),
        ("K-why-boundary [adversary] hp_decline_reason at exactly the fraction: losing_race", k_why_boundary),
        ("K-worst-per-mon [adversary] the partner's 60-HP hit does not refuse the requester's Potion", k_worst_per_mon),
        ("K-cap-shared [adversary] the 4-use cap is PER BATTLE, never per Pokémon", k_cap_shared),
        ("K-key-once [adversary] KEYITEMS: one [KEYBATTLE] line per battle, both battlers acting", k_key_once),
        ("K-d10-side1 [adversary] DQ07 on side 1: the right asleep, Full Heal only -> the parent's turn", k_d10_side1),
        ("K-ledger-switch [adversary] a new Pokémon on side 1 gets its own ledger (UseItem(Potion, 2))", k_ledger_switch),
        ("K-obs-switch [adversary] observe's tracker is per Pokémon: a switched-in Pokémon starts at worst=0",
         k_obs_switch),
        ("K-obs-maxworst [adversary] observe's worst is the MAX drop (90, 60, 50 -> 30)", k_obs_maxworst),
        ("K-obs-rise [adversary] observe never counts a rise (30, 90, 80 -> 10)", k_obs_rise),
        ("K-obs-cap [adversary] observe honours the per-battle cap: would=- why=cap uses=4", k_obs_cap),
        ("K-obs-ineff [adversary] observe honours the disable: would=- why=ineffective", k_obs_ineff),
        ("K-obs-frac [adversary] observe honours POKEBOT_HEAL_AT_FRACTION (0.8: 70/100 heals)", k_obs_frac),
        ("K-obs-two [adversary] observe reads opponent B in a TwoOpponents battle (one key side is enough)", k_obs_two),
        ("K-obs-dict [adversary] two observe decisions leave __dict__ (but _dbl_obs) unchanged", k_obs_dict),
        ("K-obs-null [adversary] a non-EWRAM gBattleStruct pointer reads bpo=? bpo_pos=?", k_obs_null),
        ("K-absent [adversary] an absent right battler: the parent's turn, no DBLITEM line", k_absent),
        ("K-obs-key0 [adversary] KEYITEMS unset, a non-key class: key=0 and would=Potion", k_obs_key0),
        ("K-obs-keyitems0 [adversary] KEYITEMS='0' is OFF in observe too", k_obs_keyitems0),
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

    def __init__(self, *, g, menu_order=MENU, cursor=(0, 0, 0, 0), bag_opens=True, party_opens=True, bag_delay=0,
                 drop_a=0):
        self.g = g
        self.party_opens = party_opens
        #: SF-2's model of the action menu: the first `drop_a` A presses are DROPPED (the menu stays up); the next one
        #: is ACCEPTED (battler g's controller leaves `HandleInputChooseAction`) and the bag opens `bag_delay` frames
        #: later (0 = at once). A B back out of the bag re-opens the action menu.
        self.bag_delay, self.drop_a = bag_delay, drop_a
        self.accepted, self.bag_at = False, None
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

    #: The party-menu states: `party` (the cursor), `party_msg` (a REFUSAL's "won't have any effect" — it closes back to
    #: the bag) and `party_ok` (a SUCCESS — the menu exits straight to the battle).
    PARTY_STATES = ("party", "party_msg", "party_ok")
    #: The ACTIVE player party indexes (BPI_RAW: battlers 0 and 2) — only a heal on one of them counts in
    #: `numHealingItemsUsed` (pret pokemon.c:5094-5100; the three-lens review's G2).
    ACTIVE = (L_IDX, R_IDX)

    def order(self):
        return self.menu_order if self.state in self.PARTY_STATES else list(range(6))

    def _tick(self):
        if self.bag_at is not None and self.frame >= self.bag_at and self.state == "battle":
            self.state, self.bag_at = "bag", None

    def controller(self, battler):
        """Battler g's controller callback: its action menu until an A is accepted, then something else."""
        self._tick()
        return "HandleInputChooseAction" if battler == self.g and self.state == "battle" and not self.accepted \
            else "Idle"

    def symbol(self, name):
        self._tick()
        table = {"gPlayerParty": b"".join(bytes(self.recs[i]) for i in self.order()),
                 "gPlayerPartyCount": bytes([6]), "gPartyMenu": bytes(self.party_menu),
                 "gBattlerInMenuId": bytes([self.bim]), "gBattlerPartyIndexes": BPI_RAW,
                 "gBattleResults": bytes([0, 0, 0, self.healed]) + bytes(0x40),
                 "gActionSelectionCursor": bytes(self.cursor)}
        return table[name]

    def game_state(self):
        self._tick()
        return {"battle": GameState.BATTLE, "bag": GameState.BAG_MENU, "bag_item": GameState.BAG_MENU,
                "party": GameState.PARTY_MENU, "party_msg": GameState.PARTY_MENU,
                "party_ok": GameState.PARTY_MENU}[self.state]

    def state_symbol(self):
        self._tick()
        return {"battle": "BATTLEMAINCB2", "bag": "CB2_BAGMENURUN", "bag_item": "CB2_BAGMENURUN",
                "party": "CB2_UPDATEPARTYMENU", "party_msg": "CB2_UPDATEPARTYMENU",
                "party_ok": "CB2_UPDATEPARTYMENU"}[self.state]

    def hp(self, index):
        return struct.unpack_from("<H", self.recs[index], 0x56)[0]

    def press_button(self, name):
        self.presses.append((self.frame, self.state, name, self.party_menu[9]))
        self._tick()
        st = self.state
        if st == "battle":
            if name == "A" and self.bag_opens:
                if self.drop_a > 0:
                    self.drop_a -= 1                         # dropped: the action menu stays up
                elif not self.accepted:
                    self.accepted = True
                    if self.bag_delay:
                        self.bag_at = self.frame + self.bag_delay
                    else:
                        self.state = "bag"
            elif name in ("Left", "Right", "Up", "Down"):
                i = self.cursor[self.g]
                i = {"Left": i - 1 if i in (1, 3) else i, "Right": i + 1 if i in (0, 2) else i,
                     "Up": i - 2 if i in (2, 3) else i, "Down": i + 2 if i in (0, 1) else i}[name]
                self.cursor[self.g] = i
        elif st == "bag":
            self.state = {"A": "bag_item", "B": "battle"}.get(name, st)
            if self.state == "battle":
                self.accepted = False                        # backed out: the action menu re-opens
        elif st == "bag_item":
            if name == "A" and self.party_opens:
                self.state, self.party_menu[9], self.bim = "party", 0, self.g
            elif name == "B":
                self.state = "bag"
        elif st == "party":
            if name == "A":
                index = self.menu_order[self.party_menu[9]] if self.party_menu[9] < 6 else None
                rec = None if index is None else self.recs[index]
                self.state = "party_msg"                             # a REFUSAL unless the medicine applies
                if rec is not None:
                    hp = struct.unpack_from("<H", rec, 0x56)[0]
                    if 0 < hp < 100 and self.bag.items[0].quantity > 0:   # G1: applied AT SELECTION
                        struct.pack_into("<H", rec, 0x56, min(100, hp + 20))
                        self.bag.items[0].quantity -= 1
                        if index in self.ACTIVE:                     # G2: only an on-field player battler counts
                            self.healed += 1
                        self.state = "party_ok"
            elif name == "B":
                self.state = "bag"
        elif st == "party_msg" and name == "B":
            self.state = "bag"                                       # a refusal closes back to the bag
        elif st == "party_ok" and name == "B":
            # ‼ G2 (the three-lens review): a SUCCESSFUL in-battle medicine exits straight to the battle
            # (`CB2_SetUpExitToBattleScreen`, pret party_menu.c:1312-1313, :4476-4477) and the battler's choice is
            # FINAL — its controller sits in `CompleteWhenChoseItem`; the action menu does NOT re-open. The first model
            # walked a success back through the bag and re-opened the menu (`accepted = False`), which the game never
            # does. `accepted` stays True here.
            self.state = "battle"


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
        return controller(battler) if controller else game.controller(battler)

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


def run_item_iso(game, *, target, g, env, state=None, **kw):
    """`run_item` under `iso_env`: the row's env, faults included, and NOTHING the job set."""
    with iso_env(env), xworld(game, env=env, **kw) as log:
        out = drive(BAS().battle_action_use_item(state or dstate(), POTION, target, g), game)
    return out, log


class PaddedGame(Game):
    """Real memory does not stop at `gPlayerParty`'s 600 bytes: `read_symbol(offset=700)` returns the NEXT symbol's
    bytes (`memory.py:66-70`). The plain fake returns b'' there, which is stricter than the hardware (the executor
    hunter's N31 survived the NOGUARD job only because of that)."""

    def symbol(self, name):
        data = super().symbol(name)
        return data + bytes([0xEE]) * 200 if name == "gPlayerParty" else data


class StaleGame(Game):
    """The party stays in MENU order after the menu closes (a stale permutation): `after`'s `same=` must say 0."""

    def order(self):
        if self.state in self.PARTY_STATES or getattr(self, "_seen_party", False):
            return self.menu_order
        return list(range(6))

    def press_button(self, name):
        if self.state in self.PARTY_STATES:
            self._seen_party = True
        super().press_button(name)


def menu_lines(log):
    return [m for m in lines(log, "DBLITEM") if m.startswith("menu ")]


def after_lines(log):
    return [m for m in lines(log, "DBLITEM") if m.startswith("after ")]


def one(items):
    return items[0] if len(items) == 1 else ""


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

    # ---------------------------------------------------------------------- the ADVERSARIAL fold (2026-09-30), executor
    def x01():
        # ⭐ THE MOST IMPORTANT MISS (the executor hunter's N37): battler 2 aims at menu slot 1, the scroll stops on slot
        # 0 — where the menu OPENS (G2), and where a KI-38 give-up leaves it — and slot 0 is the LIVING PARTNER. The guard
        # must refuse on the PID at the ACTUAL slot; a guard that reads the PID at the aim passes and feeds the partner.
        game = Game(g=2)
        out, log = run_item_iso(game, target=R_IDX, g=2, env={FLAG: "1"}, party_scroll=0)
        m, a = one(menu_lines(log)), one(after_lines(log))
        ok = (out == "done" and field(m, "slot") == "0" and field(m, "menu_pid") == "863B0917"
              and field(m, "intended_pid") == "5C96EA9B" and field(m, "ok") == "0" and field(m, "a_pressed") == "0"
              and not party_a(game) and game.hp(L_IDX) == 40 and "Potion=1->1" in a)
        return ok, f"menu {m}; after {a}; party A {party_a(game)}"

    def x02():
        # battler 0's REAL action scroll reads byte 0 (byte 2 set differently). NOT isolated on purpose: under the CURSOR0
        # job it must stay green (battler 0 never consults the fault) — and a fault mutant that flips battler 0 too
        # (the executor hunter's N02) shows only there.
        game = Game(g=0, cursor=(0, 3, 1, 3))
        with xworld(game):
            out = drive(BM().scroll_to_battle_action(1, False), game)
        dirs = [p[2] for p in game.presses]
        return out == "done" and dirs == ["Right"] and bytes(game.cursor) == bytes([1, 3, 1, 3]), \
            f"presses {dirs}; cursor {list(game.cursor)}"

    def x03():
        # `observe` never reaches the executor: the item flow reads nothing and logs no DBLITEM; the Struggle loop
        # presses A every frame and never reads controller 2 (P-OBS = P-OFF on every gameplay line).
        game = Game(g=2)
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "observe"})
        ok1 = out == "done" and not log.reads and not dbl_events(log) and len(party_a(game)) == 1
        game2 = Game(g=0)

        def controller(battler, game=game2):
            return ("HandleInputChooseAction" if game.frame >= 10 else "Idle") if battler == 2 else "Idle"

        def main(game=game2):
            return "HandleTurnActionSelectionState" if game.frame < 40 else "Done"

        with xworld(game2, env={FLAG: "observe"}, controller=controller, main=main) as log2:
            drive(BAS().battle_action_use_move(TurnAction.UseMove, 0, 0, dstate()), game2)
        late = [p[0] for p in game2.presses if p[2] == "A" and p[0] >= 10]
        ok2 = late == list(range(10, 40)) and log2.cb2 == 0 and not lines(log2, "DBLITEM")
        return ok1 and ok2, f"item: reads {log.reads} DBLITEM {dbl_events(log)}; D11: A>=10 {len(late)} cb2 {log2.cb2}"

    def x04():
        # an unreadable battle type is NOT a double (fail closed into today's flow). UNREACHABLE live (`BattleType` is
        # `boundary=KEEP`), kept as defence: it pins the direction `_dbl_on` fails in.
        class BadState:
            @property
            def is_double_battle(self):
                raise RuntimeError("battle type unreadable")

            def map_battle_party_index(self, i):
                return i

        game = Game(g=2)
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"}, state=BadState())
        ok = out == "done" and not log.reads and not dbl_events(log) and len(party_a(game)) == 1
        return ok, f"reads {log.reads}; DBLITEM {dbl_events(log)}; party A {party_a(game)}"

    def x05():
        # WRONGSLOT's OWN shape, both sides, isolated from the job's fault: the cursor goes to the PARTNER's slot.
        res = {}
        for g, tgt, want_slot, want_pid, want_int in ((2, R_IDX, "0", "863B0917", "5C96EA9B"),
                                                       (0, L_IDX, "1", "5C96EA9B", "863B0917")):
            game = Game(g=g)
            out, log = run_item_iso(game, target=tgt, g=g, env={FLAG: "1", F_WRONGSLOT: "1"})
            m = one(menu_lines(log))
            res[g] = (out == "done" and log.aims == [int(want_slot)] and field(m, "slot") == want_slot
                      and field(m, "menu_pid") == want_pid and field(m, "intended_pid") == want_int
                      and field(m, "ok") == "0" and field(m, "a_pressed") == "0" and not party_a(game), log.aims, m)
        return all(v[0] for v in res.values()), f"{res}"

    def x06():
        # P-NOG's pre-registered line shape: WRONGSLOT + NOGUARD on battler 0 → `slot=1 … ok=0 a_pressed=1`, the
        # PARTNER healed and the target not.
        game = Game(g=0)
        out, log = run_item_iso(game, target=L_IDX, g=0, env={FLAG: "1", F_WRONGSLOT: "1", F_NOGUARD: "1"})
        m, a = one(menu_lines(log)), one(after_lines(log))
        ok = (out == "done" and field(m, "slot") == "1" and field(m, "ok") == "0" and field(m, "a_pressed") == "1"
              and " hp=40->40 " in a and "partner=Mightyena#5C96EA9B hp=30->50" in a and "Potion=1->0" in a)
        return ok, f"menu {m}; after {a}"

    def x07():
        # NOGUARD skips ONLY the PID comparison: a broken self binding, Cancel (7) and slot 6 = count still press
        # nothing. PaddedGame: an out-of-range read returns bytes, as real memory does.
        res = {}
        for name, tgt, ps in (("self", L_IDX, None), ("cancel7", R_IDX, 7), ("slot6", R_IDX, 6)):
            game = PaddedGame(g=2)
            _out, log = run_item_iso(game, target=tgt, g=2, env={FLAG: "1", F_NOGUARD: "1"}, party_scroll=ps)
            m = one(menu_lines(log))
            res[name] = (field(m, "a_pressed") == "0" and not party_a(game), m)
        return all(v[0] for v in res.values()), f"{res}"

    def x08():
        # `_dbl_before`'s own read failing fails CLOSED (self=0, no A) — with and without NOGUARD.
        res = {}
        for name, env in (("plain", {FLAG: "1"}), ("noguard", {FLAG: "1", F_NOGUARD: "1"})):
            game = Game(g=2)
            out, log = run_item_iso(game, target=R_IDX, g=2, env=env, raise_on="gBattlerPartyIndexes")
            m = one(menu_lines(log))
            res[name] = (out == "done" and field(m, "self") == "0" and field(m, "a_pressed") == "0"
                         and not party_a(game) and game.state == "battle", m)
        return all(v[0] for v in res.values()), f"{res}"

    def x09():
        # `battler_in_menu` is the GAME's gBattlerInMenuId, never our g: a game that says battler 0 opened the menu.
        game = Game(g=2)
        orig = game.press_button

        def press(name, game=game, orig=orig):
            orig(name)
            if game.state == "party":
                game.bim = 0

        game.press_button = press
        _out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"})
        m = one(menu_lines(log))
        return field(m, "battler_in_menu") == "0", f"{m}"

    def x10():
        # a refusal must not log `[ITEM-FLOW] target-chosen` (rule 7: log the action, not the intent).
        game = Game(g=2, menu_order=(1, 2, 0, 4, 3, 5))
        out, log = run_item_iso(game, target=R_IDX, g=2, env={FLAG: "1"})
        tc = [m for _c, m in log.events if "target-chosen" in m]
        return out == "done" and not tc and not party_a(game), f"target-chosen lines {tc}"

    def x11():
        # `same=` really compares the identity: a party left in MENU order after the menu closed reads same=0.
        game = StaleGame(g=2)
        _out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"})
        a = one(after_lines(log))
        return field(a, "same") == "0", f"{a}"

    def x12():
        # NOGUARD's pre-registered reddening as a POSITIVE row: under NOGUARD a PID mismatch IS pressed, logged honestly.
        game = Game(g=2, menu_order=(1, 2, 0, 4, 3, 5))
        _out, log = run_item_iso(game, target=R_IDX, g=2, env={FLAG: "1", F_NOGUARD: "1"})
        m = one(menu_lines(log))
        return field(m, "ok") == "0" and field(m, "a_pressed") == "1" and len(party_a(game)) == 1, f"{m}"

    def x13():
        # CURSOR0 is armed by "1" ONLY: "0", "" and "yes" still read byte 2 — and "1" reads byte 0 (the arm's shape).
        res = {}
        for val, want in (("0", [1, 3, 1, 3]), ("", [1, 3, 1, 3]), ("yes", [1, 3, 1, 3]), ("1", [1, 3, 0, 3])):
            game = Game(g=2, cursor=(1, 3, 0, 3))
            with iso_env({F_CURSOR0: val}), xworld(game):
                drive(BM().scroll_to_battle_action(1, True), game)
            res[val] = list(game.cursor) == want
        return all(res.values()), f"{res}"

    # ---------------------------------------------------------------------- SF-2: the doubles bag-open budget
    def bag_flow(game, env=None):
        out, log = run_item(game, target=R_IDX, g=2, env={FLAG: "1"} if env is None else env)
        battle_a = [p[0] for p in game.presses if p[1] == "battle" and p[2] == "A"]
        flow = [m for _c, m in log.events if m.startswith("[ITEM-FLOW]")]
        opened = any(m.startswith("[ITEM-FLOW] opened-bag") for m in flow)
        gave_up = any("bag-did-not-open" in m for m in flow)
        return out, battle_a, opened, gave_up, flow

    def sf2_nobag():
        # N3 (the three-lens review): the A is ACCEPTED (the action menu lets go) but no bag ever comes. The exit must say
        # so in its OWN terminal stage — never the generic "… the strategy will re-decide", which is false here (nothing
        # re-decides a battler whose controller left its action menu; a KI-46 derail follows).
        out, battle_a, opened, gave_up, flow = bag_flow(Game(g=2, bag_delay=10 ** 6))
        own = [m for m in flow if "but no bag within 150 frames" in m and "KI-46" in m]
        ok = out == "done" and len(battle_a) == 1 and not opened and not gave_up and len(own) == 1
        return ok, f"A presses {battle_a}; generic give-up {gave_up}; own stage {own}"

    def sf2_unset():
        # ⛔ the flag-UNSET path keeps today's loop press for press (SF-2 is flag-on doubles only): on the same slow bag
        # it presses three times and gives up at 90 — the shipped behaviour, deliberately left alone (rule 9).
        out, battle_a, opened, gave_up, _flow = bag_flow(Game(g=2, bag_delay=120), env={})
        ok = out == "done" and len(battle_a) == 3 and gave_up and not opened
        return ok, f"A presses at {battle_a}; gave up {gave_up}; opened {opened}"

    def sf2_accept():
        # the action menu lets go after the FIRST A and the bag takes 120 frames: one A, then a wait; never a give-up.
        # (Today's 3 × 30 loop presses three times and returns at 90 while the bag is still opening.)
        out, battle_a, opened, gave_up, flow = bag_flow(Game(g=2, bag_delay=120))
        ok = out == "done" and len(battle_a) == 1 and opened and not gave_up
        return ok, f"A presses in the action menu at {battle_a}; opened {opened}; gave up {gave_up}"

    def sf2_drop():
        # P-ON's shape, stretched: the first A is DROPPED (the menu stays up), the second is accepted, the bag takes 70.
        out, battle_a, opened, gave_up, flow = bag_flow(Game(g=2, drop_a=1, bag_delay=70))
        ok = out == "done" and len(battle_a) == 2 and opened and not gave_up
        return ok, f"A presses at {battle_a}; opened {opened}; gave up {gave_up}"

    def sf2_bound():
        # every A dropped (the menu never lets go): exactly three presses, then today's bounded give-up.
        game = Game(g=2, drop_a=99)
        out, battle_a, opened, gave_up, flow = bag_flow(game)
        ok = out == "done" and len(battle_a) == 3 and not opened and gave_up and game.frame <= 100
        return ok, f"A presses at {battle_a}; gave up {gave_up}; frames {game.frame}"

    cases = [
        ("DQ11 scroll_to_battle_action(1, True) on cursor [1,3,0,3]: byte 2 read, Right until byte 2 = 1", dq11),
        ("DQ12 battle_action_use_item(..., battler_index=2) calls scroll_to_battle_action(1, True); byte 2 moves", dq12),
        ("DQ13 executor positive control, matching PIDs: cursor to the requester's slot, A; ok=1 a_pressed=1; after",
         dq13),
        ("DQ14 the scroll stops short on Cancel (slot 7 != aim): refused — BY THE RANGE CHECK. ⚠ It does NOT pin that "
         "the PID is read at the actual slot (any PID is refused at slot 7); X01 pins that", dq14),
        ("DQ15 a PID mismatch at the slot: no A, the B unwind runs; ok=0 a_pressed=0; nothing healed", dq15),
        ("DQ16 the Struggle loop; controller 2 opens its menu at f10: flag 1 no A after it; unset A every frame", dq16),
        ("DQ17 flag unset, executor: no guard read, no DBLITEM line, today's A", dq17),
        ("DBself [builder] battler 2 aimed at the LEFT's index: the PID matches, the SELF binding refuses", db_self),
        ("DBguardraise [builder] the guard's gPartyMenu read raises: fails CLOSED (no A), err logged", db_guardraise),
        ("DBsingleexec [builder] flag 1 in a SINGLE battle: no guard read, no DBLITEM line, today's A", db_singleexec),
        ("DBmenuclosed [builder] the party menu never opened: the guard refuses (no A into the bag)", db_menuclosed),
        ("DBmove [builder] battle_action_use_move passes battler_index > 1 to the action scroll", db_move),
        ("DBd11b2 [builder] D11 is battler 0's only: battler 2's own Struggle loop keeps confirming, flag on", db_d11b2),
        ("X01 [adversary] battler 2 aimed at slot 1, the scroll stops on slot 0 (the living partner): refused on the PID "
         "at the ACTUAL slot; no A, the partner and the bag untouched", x01),
        ("X02 [adversary] battler 0's real action scroll reads byte 0 (byte 2 set differently)", x02),
        ("X03 [adversary] observe never reaches the executor: no read, no DBLITEM; the Struggle loop is today's", x03),
        ("X04 [adversary] an unreadable battle type is not a double: today's flow (unreachable live; direction pinned)",
         x04),
        ("X05 [adversary] WRONGSLOT's own shape (isolated), both sides: the partner's slot, refused", x05),
        ("X06 [adversary] WRONGSLOT + NOGUARD (isolated): P-NOG's `slot=1 … ok=0 a_pressed=1`, the partner healed", x06),
        ("X07 [adversary] NOGUARD skips only the PID check: self=0, slot 7, slot 6 = count press nothing", x07),
        ("X08 [adversary] the pre-bag read failing fails closed (self=0, no A), with and without NOGUARD", x08),
        ("X09 [adversary] battler_in_menu is the game's gBattlerInMenuId", x09),
        ("X10 [adversary] a refusal logs no `target-chosen`", x10),
        ("X11 [adversary] same=0 when the identity at the party index changed", x11),
        ("X12 [adversary] NOGUARD (isolated) presses a PID mismatch and logs ok=0 a_pressed=1", x12),
        ("X13 [adversary] CURSOR0 is armed by '1' only ('0', '', 'yes' read byte 2; '1' reads byte 0)", x13),
        ("SF2-accept [fix] flag-on double: the menu lets go after one A, the bag takes 120 frames: ONE A, bag reached",
         sf2_accept),
        ("SF2-drop [fix] the first A dropped, the second accepted, the bag 70 frames later: two A, bag reached",
         sf2_drop),
        ("SF2-bound [fix] every A dropped: exactly three presses, then the bounded give-up", sf2_bound),
        ("SF2-unset [fix] flag unset, the same slow bag: TODAY's three presses and the give-up, unchanged", sf2_unset),
        ("SF2-nobag [review N3] the A accepted, no bag ever: its OWN terminal stage (KI-46 expected), not the generic "
         "'the strategy will re-decide'", sf2_nobag),
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
    # ⚠ THE FOLD changed two base sets, each for a stated reason: MD11 loses DQ08 (DQ08 now looks for the pending request
    # in ANY ledger — a ledger keyed by the PID alone is the same behaviour); MD12 loses DQ07 (since SF-1 a double asks
    # no cure policy, so `hp_only` no longer decides DQ07).
    ("MD11 ledger_key = the PID alone", "dbl", [("    return pid, species", "    return pid")], {"DP06"}),
    ("MD12 hp_only keeps parameter 0 (a param-0 cure reaches observe's options)", "dbl",
     [("    return [opt for opt in options if opt[2] > 0]", "    return [opt for opt in options if opt[2] >= 0]")],
     {"DP07", "DQ03"}),
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
    ("MS01 the flag-unset tests dropped (both the env test and `mode != OFF`: unset falls through to the acting path)",
     "sm",
     [('        if _os_dbl.environ.get("POKEBOT_R27_DOUBLEITEMS") not in ("observe", "1"):\n'
       "            return super().decide_turn_in_double_battle(battle_state, battler_index)\n", ""),
      ("            in_scope = mode != _dbl.OFF and _dbl.in_scope(battle_state.type)",
       "            in_scope = _dbl.in_scope(battle_state.type)")], {"DQ01"}),
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
    ("MS08 D10's cure skip removed (a double asks the cure policy with the full bag)", "sm",
     [("        if item is None and not doubles:", "        if item is None:")], {"DQ07", "SF1-cure", "K-d10-side1"}),
    ("MS09 D10's cure skip applied in SINGLES too", "sm",
     [("        if item is None and not doubles:", "        if item is None and False:")], {"DBsinglescure"}),
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

#: ⚠ THE FOLD (2026-09-30) — what each EXISTING mutant ALSO reddens among the fold's new rows. ⛔ HONESTLY LABELLED: these
#: were MEASURED on the fold's first run (the existing mutants against the new rows), and only then checked by hand, one
#: by one — every addition below has a stated mechanism, e.g. MD10's byte stride also reads the PARTNER at raw[0] (X06's
#: `partner=` changes) and breaks X12's self binding; MB05/MB06 press into X01's living partner. They are NOT a
#: pre-registration. The fold's NEW mutants (FOLD_MUTANTS, FAULT_MUTANTS) were derived before their first run.
MUTANT_ADDITIONS = {
    "MD02": {"K-mode"}, "MD07": {"K-active"}, "MD09": {"K-guardnone"}, "MD10": {"X06", "X12"},
    "MD12": {"K-parity-noreserve"}, "MD14": {"K-ether"}, "MD15": {"K-obs-frac"}, "MD16": {"K-why-boundary"},
    "MD17": {"K-ledger-switch", "K-worst-per-mon"},
    "MS02": {"K-obs-cap", "K-obs-dict", "K-obs-frac", "K-obs-ineff", "K-obs-key0", "K-obs-keyitems0", "K-obs-maxworst",
             "K-obs-null", "K-obs-rise", "K-obs-switch", "K-obs-two", "SF1-cure",
             "R-silent"},                    # (the review's fold: derived before its run — observe acts, no OBS line)
    "MS03": {"K-cap-shared", "K-ledger-switch"},
    "MS04": {"K-cap-shared", "K-ledger-switch", "K-scope-real", "K-worst-per-mon"},
    "MS06": {"K-ledger-switch", "K-worst-per-mon"}, "MS10": {"K-d10-side1", "SF1-cure"},
    "MS11": {"N2-import"}, "MS12": {"N2-import"}, "MS13": {"K-obs-maxworst", "K-obs-rise"}, "MS15": {"K-obs-dict"},
    "MS21": {"K-key-once"},
    "MB05": {"X01", "X07"}, "MB06": {"X01", "X05", "X07", "X08", "X10"}, "MB08": {"X07"},
    # MB09 + SF2-unset: with the executor's flag test gone, the flag-unset double takes the SF-2 bag loop (one press).
    # (SF2-unset was written after the additions were measured; this one was caught by the gate's own exact check.)
    "MB09": {"X03", "SF2-unset"},
    "MB12": {"X06"}, "MB13": {"X01", "X06", "X11"}, "MB14": {"X01", "X05"}, "MB16": {"X04"},
    "MM01": {"X13"}, "MM02": {"X13"},
}

_SM_SWAP = ("    saved = {name: getattr(strategy, name) for name in _dbl.LEDGER_FIELDS}\n"
            "    for name in _dbl.LEDGER_FIELDS:\n        setattr(strategy, name, ledger[name])\n"
            "    try:\n        action = strategy._maybe_use_item(battle_state, side=side, doubles=True)\n"
            "    finally:\n        for name in _dbl.LEDGER_FIELDS:\n            ledger[name] = getattr(strategy, name)\n"
            "            setattr(strategy, name, saved[name])\n")


def _swap_with(fields_expr: str, extra: str = "") -> str:
    """The ledger swap over a mutated field tuple (the strategy hunter's S14/S15/S17 shapes)."""
    return "    _F = " + fields_expr + "\n" + extra + _SM_SWAP.replace("_dbl.LEDGER_FIELDS", "_F")


_A_BLOCK = ("        if _dbl_ctx is None or _dbl_guard(_dbl_ctx, _menu_slot):\n"
            '            context.emulator.press_button("A")\n            yield\n            _stage("target-chosen")\n')
_WRONGSLOT = ('        if _dbl_ctx is not None and _dbl_env(_DBL_FAULT_WRONGSLOT):\n'
              '            _menu_slot = 1 - _dbl_ctx["side"]\n')
_GUARD_PRESS = '        press = ok or (_dbl_env(_DBL_FAULT_NOGUARD) and bool(ctx["self"]) and in_range)'
_CURSOR_IF = ("    if is_right_side_pokemon:\n        import os as _os_c1\n\n"
              '        if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") == "1":\n'
              "            is_right_side_pokemon = False\n")

#: THE FOLD'S NEW MUTANTS (2026-09-30), every red set DERIVED BY HAND BEFORE THEIR FIRST RUN. `RV-*` revert a
#: production fix to the shipped 799e6adf behaviour (each must redden exactly its fix's rows: the red-on-unfixed proof,
#: kept as a standing pin); `SF2-*` break the new bag rule; `K*` / `X*` are the adversaries' REAL survivors (their ids,
#: N/S renamed KN/KS for the strategy hunter and XN for the executor hunter), adapted to this code.
FOLD_MUTANTS: list = [
    # ---- the production-fix REVERTS (the proof that each fix's rows were red on the unfixed code)
    ("RV-SF1a revert SF-1, acting path: hp_only(medicine) handed to the cure policy in a double (799e6adf)", "sm",
     [("        if item is None and not doubles:", "        if item is None:"),
      ("            from modules.story.battle_items import choose_status_or_revive_item\n\n"
       "            item = choose_status_or_revive_item(",
       "            from modules.story.battle_items import choose_status_or_revive_item\n\n"
       "            if doubles:\n                from modules.story.double_items import hp_only as _dbl_hp_only\n\n"
       "                medicine = _dbl_hp_only(medicine)\n            item = choose_status_or_revive_item(")],
     {"SF1-cure"}),
    ("RV-SF1b revert SF-1, observe: the cure fallback on the HP options (799e6adf)", "sm",
     [("        if item is None:\n            why = _dbl.hp_decline_reason(",
       "        if item is None:\n            from modules.story.battle_items import choose_status_or_revive_item as _c\n\n"
       "            item = _c(mon.status_permanent, 2, options, uses_so_far=uses, allow_revive=False)\n"
       '            why = "cure"\n        if item is None:\n            why = _dbl.hp_decline_reason(')],
     {"SF1-cure"}),
    ("RV-SF2 revert SF-2: today's 3 x 30 loop in a flag-on double too (799e6adf)", "bas",
     [("    if _dbl_ctx is not None:\n        # design v2 step 13, SF-2:", "    if False:\n        # design v2 step 13, SF-2:")],
     {"SF2-accept", "SF2-drop", "SF2-nobag"}),
    ("RV-N2 revert N2: double_items imported BEFORE the flag test (799e6adf)", "sm",
     [('        if _os_dbl.environ.get("POKEBOT_R27_DOUBLEITEMS") not in ("observe", "1"):',
       "        from modules.story import double_items as _dbl_early  # noqa: F401\n"
       '        if _os_dbl.environ.get("POKEBOT_R27_DOUBLEITEMS") not in ("observe", "1"):')],
     {"N2-import"}),
    # ---- SF-2's own rules
    ("SF2a the action-menu check dropped (re-press regardless)", "bas",
     [("        if get_battle_controller_callback(battler_index) not in _DBL_CHOOSE_ACTION:\n            break",
       "        if False:\n            break")], {"SF2-accept", "SF2-drop", "SF2-nobag"}),
    # ---- the THREE-LENS REVIEW's code nits (2026-09-30): reverts and their rules, derived before their first run
    ("RV-N1 revert N1: observe back on the LOGGING reserve filter", "sm",
     [("    options = _dbl.heal_options(get_item_bag().items, _dbl_reserve_silent)",
       "    options = _dbl.heal_options(get_item_bag().items, __import__(\"modules.story.league_reserve\", "
       "fromlist=[\"x\"]).filter_medicine_for_reserve)")], {"R-silent"}),
    ("N1a the silent filter ignores POKEBOT_RESERVE_FAULT_NOLOCK", "sm",
     [('    if _os_rs.environ.get("POKEBOT_RESERVE_FAULT_NOLOCK") == "1":\n        return medicine\n', "")],
     {"R-parity"}),
    ("N1b the silent filter never subtracts the reserve", "sm",
     [("    return apply_reserve(medicine, reserved) if reserved else medicine", "    return medicine")],
     {"R-parity", "DQ03"}),
    ("RV-N3 revert N3: the accepted-no-bag exit returns False and logs the generic 're-decide' line", "bas",
     [('    stage(f"A accepted after {presses} press(es) but no bag within {_DBL_BAG_WAIT_AFTER_ACCEPT} frames — this '
       'battler "\n          f"cannot be re-decided (its controller left the action menu); a KI-46 derail is expected")\n'
       "    return None\n", "    return False\n")], {"SF2-nobag"}),
    ("N3b the caller logs the generic give-up on the accepted-no-bag exit too", "bas",
     [("        if _bag_open is not None:\n", "        if True:\n")], {"SF2-nobag"}),
    ("SF2b the post-accept wait dropped (give up at once)", "bas",
     [("    for _ in range(_DBL_BAG_WAIT_AFTER_ACCEPT):", "    for _ in range(0):")], {"SF2-accept", "SF2-drop"}),
    ("SF2c the press bound dropped (presses for as long as the menu stays up)", "bas",
     [("    while presses < _DBL_BAG_PRESSES:", "    while presses < 10 ** 9:")], {"SF2-bound"}),
    ("SF2e the doubles bag loop used with the flag unset too", "bas",
     [("    if _dbl_ctx is not None:\n        # design v2 step 13, SF-2:", "    if True:\n        # design v2 step 13, SF-2:")],
     {"SF2-unset"}),
    # ---- the strategy hunter's REAL survivors (double_items.py)
    ("KN01 mode(): 'OBSERVE' case-folded turns observe on", "dbl",
     [('    if value == "observe":', '    if value is not None and value.lower() == "observe":')], {"K-mode"}),
    ("KN02 mode(): any value starting with '1' turns it on", "dbl",
     [('    if value == "1":', '    if value is not None and value.startswith("1"):')], {"K-mode"}),
    ("KN03 mode(): trailing whitespace stripped", "dbl",
     [("    value = None if env is None else env.get(FLAG)",
       '    value = None if env is None else ((env.get(FLAG) or "").rstrip() or None)')], {"K-mode"}),
    ("KN06 in_scope also excludes TwoOpponents (every two-trainer double out)", "dbl",
     [("    return not bits & (BATTLE_TYPE_MULTI | BATTLE_TYPE_INGAME_PARTNER)",
       "    return not bits & (BATTLE_TYPE_MULTI | BATTLE_TYPE_INGAME_PARTNER | (1 << 15))")],
     {"K-scope-real", "K-obs-two"}),
    ("KN07 in_scope requires EXACTLY Trainer|Double (IS_MASTER puts every real battle out)", "dbl",
     [("    if not bits & BATTLE_TYPE_TRAINER or not bits & BATTLE_TYPE_DOUBLE:",
       "    if bits != BATTLE_TYPE_TRAINER | BATTLE_TYPE_DOUBLE:")],
     {"DQ02", "DQ03", "DQ04", "DQ05", "DQ08", "DQ10", "DBuse", "DBerr", "DBobsfields", "DBobsworst", "DBobskey",
      "DBobsdisc", "DBjudge", "SF1-cure", "K-scope-real", "K-parity-noreserve", "K-worst-per-mon", "K-cap-shared",
      "K-key-once", "K-ledger-switch", "K-obs-switch", "K-obs-maxworst", "K-obs-rise", "K-obs-cap", "K-obs-ineff",
      "K-obs-frac", "K-obs-two", "K-obs-null", "K-obs-key0", "K-obs-keyitems0", "R-silent"}),
    ("KN12 active_positions sorted (left/right lost)", "dbl",
     [("    return order[0], order[1]", "    return tuple(sorted((order[0], order[1])))")], {"K-active"}),
    ("KN21 guard_ok: the slot/count None checks dropped (raises)", "dbl",
     [("    if intended_pid is None or menu_pid is None or slot is None or count is None:",
       "    if intended_pid is None or menu_pid is None:")], {"K-guardnone"}),
    ("KN22 guard_ok compares the PID's low 16 bits only", "dbl",
     [("    return menu_pid == intended_pid", "    return menu_pid & 0xFFFF == intended_pid & 0xFFFF")], {"K-guardhigh"}),
    ("KN23 hp_only also drops the 255 items", "dbl",
     [("    return [opt for opt in options if opt[2] > 0]", "    return [opt for opt in options if 0 < opt[2] < 255]")],
     {"K-hp255", "K-parity-noreserve"}),
    ("KN25 heal_options fails CLOSED on a raising reserve", "dbl",
     [("        except Exception:  # noqa: BLE001 - fail UNLOCKED, the strategy's own rule (story_mode.py, RULING 18 "
       "filter)\n            pass\n",
       "        except Exception:  # noqa: BLE001 - the mutant fails closed\n            medicine = []\n")],
     {"K-reserve-raise", "R-parity"}),
    ("KN28 hp_decline_reason: above_fraction at >=", "dbl",
     [("    if current_hp / total_hp > heal_at_fraction:\n        return \"above_fraction\"",
       "    if current_hp / total_hp >= heal_at_fraction:\n        return \"above_fraction\"")], {"K-why-boundary"}),
    ("KN31 _is_healing also accepts pp_recovery (Ether, Max Ether)", "dbl",
     [('    return str(getattr(use, "value", use)) == HEALING_BATTLE_USE',
       '    return str(getattr(use, "value", use)) in (HEALING_BATTLE_USE, "pp_recovery")')], {"K-ether"}),
    # ---- the strategy hunter's REAL survivors (story_mode.py)
    ("KS08 the ledger keyed by SIDE", "sm",
     [("ledgers.setdefault(_dbl.ledger_key(mon.personality_value, mon.species.index), _dbl.new_ledger())",
       "ledgers.setdefault(side, _dbl.new_ledger())")], {"K-ledger-switch"}),
    ("KS09 ONE ledger shared by both battlers", "sm",
     [("ledgers.setdefault(_dbl.ledger_key(mon.personality_value, mon.species.index), _dbl.new_ledger())",
       'ledgers.setdefault("shared", _dbl.new_ledger())')], {"DQ08", "K-worst-per-mon", "K-ledger-switch"}),
    ("KS14 the swap omits _worst_hit", "sm",
     [(_SM_SWAP, _swap_with('tuple(f for f in _dbl.LEDGER_FIELDS if f != "_worst_hit")'))],
     {"K-worst-per-mon", "K-ledger-switch"}),
    ("KS15 the swap includes _item_uses (a cap per Pokémon)", "sm",
     [(_SM_SWAP, _swap_with('_dbl.LEDGER_FIELDS + ("_item_uses",)', '    ledger.setdefault("_item_uses", 0)\n'))],
     {"K-cap-shared"}),
    ("KS17 the swap includes _r27_verdict (a key verdict per Pokémon)", "sm",
     [(_SM_SWAP, _swap_with('_dbl.LEDGER_FIELDS + ("_r27_verdict",)', '    ledger.setdefault("_r27_verdict", None)\n'))],
     {"K-key-once"}),
    ("KS20 the doubles cure skip only for side 0", "sm",
     [("        if item is None and not doubles:", "        if item is None and not (doubles and side == 0):")],
     {"K-d10-side1"}),
    ("KS24 observe's tracker keyed by SIDE", "sm",
     [("tracker.setdefault(_dbl.ledger_key(pid, mon.species.index),", "tracker.setdefault(side,")], {"K-obs-switch"}),
    ("KS26 observe's worst = the LATEST drop", "sm",
     [('        rec["worst"] = max(rec["worst"], rec["hp"] - cur)', '        rec["worst"] = rec["hp"] - cur')],
     {"K-obs-maxworst"}),
    ("KS27 observe counts HP RISES as hits", "sm",
     [('    if rec["hp"] is not None and rec["hp"] > cur:\n        rec["worst"] = max(rec["worst"], rec["hp"] - cur)',
       '    if rec["hp"] is not None and rec["hp"] != cur:\n        rec["worst"] = max(rec["worst"], abs(rec["hp"] - cur))')],
     {"K-obs-rise"}),
    ("KS29 observe ignores the per-battle cap", "sm",
     [('    uses = getattr(strategy, "_item_uses", 0)', "    uses = 0")], {"K-obs-cap"}),
    ("KS30 observe ignores _items_ineffective", "sm",
     [('    elif getattr(strategy, "_items_ineffective", False):', "    elif False:")], {"K-obs-ineff"}),
    ("KS31 observe ignores POKEBOT_HEAL_AT_FRACTION", "sm",
     [('worst_hit_taken=rec["worst"], uses_so_far=uses, **frac_kw)\n        why = "hp"',
       'worst_hit_taken=rec["worst"], uses_so_far=uses)\n        why = "hp"')], {"K-obs-frac"}),
    ("KS32 observe reads opponent A only", "sm",
     [("        two = BattleType.TwoOpponents in battle_state.type\n        opp_a, opp_b = _ti.read_opponent_trainers(two)",
       "        two = False\n        opp_a, opp_b = _ti.read_opponent_trainers(two)")], {"K-obs-two"}),
    ("KS34 observe writes _worst_hit", "sm",
     [('    rec["hp"] = cur\n    # The key class by the PURE verdict',
       '    rec["hp"] = cur\n    strategy._worst_hit = max(strategy._worst_hit, rec["worst"])\n'
       "    # The key class by the PURE verdict")], {"K-obs-dict"}),
    ("KS41 observe's EWRAM check on *gBattleStruct dropped", "sm",
     [("        if not 0x0200_0000 <= ptr < 0x0204_0000:\n"
       '            raise ValueError(f"gBattleStruct={ptr:#x} is not in EWRAM")\n', "")], {"K-obs-null"}),
    ("KS42 _dbl_act's `mon is None` early return dropped", "sm",
     [("    if mon is None:\n        return None\n    ledgers = getattr(", "    ledgers = getattr(")], {"K-absent"}),
    ("KS43 observe's key = the KEYITEMS-dependent allow", "sm",
     [('        key = 1 if reason == "key_class" else (0 if reason == "not_a_key_class" else "?")',
       '        key = int(_ti.key_battle_verdict(_os_obs.environ.get("POKEBOT_R27_KEYITEMS") == "1", sides)[0])')],
     {"K-obs-key0"}),
    ("KS46 observe reads POKEBOT_R27_KEYITEMS as truthy ('0' turns it on)", "sm",
     [('        allow = _ti.key_battle_verdict(_os_obs.environ.get("POKEBOT_R27_KEYITEMS") == "1", sides)[0]',
       '        allow = _ti.key_battle_verdict(bool(_os_obs.environ.get("POKEBOT_R27_KEYITEMS")), sides)[0]')],
     {"K-obs-keyitems0"}),
    # ---- the executor hunter's REAL survivors and fault-arm kills, run WITHOUT a fault (the iso rows see them now)
    ("XN01 C1: every battler reads byte 2", "bm",
     [('    yield from _select_in_menu("gActionSelectionCursor", action_index, is_right_side_pokemon)',
       '    yield from _select_in_menu("gActionSelectionCursor", action_index, True)')], {"X02", "X13"}),
    ("XN04 CURSOR0 armed by ANY value", "bm",
     [('        if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") == "1":',
       '        if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") is not None:')], {"X13"}),
    # ⚠ the misspelt name is split ("POKE" "BOT_…", implicit concatenation in the exec'd mutant) so this gate's own source
    # never holds it as a quoted POKEBOT_* literal — lint_docs R6 would (rightly) demand a registry row for it.
    ("XN05 CURSOR0 reads a misspelt env name (the fault silently dead)", "bm",
     [('        if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") == "1":',
       '        if _os_c1.environ.get("POKE" "BOT_R27_FAULT_CURSOR0") == "1":')], {"X13"}),
    ("XN06 CURSOR0 consulted for battler 0 only", "bm",
     [("    if is_right_side_pokemon:\n        import os as _os_c1", "    if not is_right_side_pokemon:\n        import os as _os_c1")],
     {"X13"}),
    ("XN08 C1 passes bool(action_index), not the side", "bm",
     [('    yield from _select_in_menu("gActionSelectionCursor", action_index, is_right_side_pokemon)',
       '    yield from _select_in_menu("gActionSelectionCursor", action_index, bool(action_index))')], {"X02", "X13"}),
    ("XN13 _dbl_env accepts 'observe' (observe turns the guard and D11 on)", "bas",
     [('    return _os_dbl.environ.get(name) == "1"', '    return _os_dbl.environ.get(name) in ("1", "observe")')],
     {"X03"}),
    ("XN17 ctx side = g (WRONGSLOT aims at -1 for battler 2)", "bas",
     [('    ctx = {"g": battler_index, "side": battler_index // 2,', '    ctx = {"g": battler_index, "side": battler_index,')],
     {"X05"}),
    ("XN18 ctx side = g % 2 (always 0)", "bas",
     [('    ctx = {"g": battler_index, "side": battler_index // 2,', '    ctx = {"g": battler_index, "side": battler_index % 2,')],
     {"X05"}),
    ("XN25 _dbl_before's except keeps self=True (fails OPEN on the binding)", "bas",
     [('        ctx["intended"], ctx["self"], ctx["err"] = None, False, type(error).__name__',
       '        ctx["intended"], ctx["self"], ctx["err"] = None, True, type(error).__name__')], {"X08"}),
    ("XN30 the guard's range check off by one (slot <= count)", "bas",
     [("        in_range = 0 <= slot < count", "        in_range = 0 <= slot <= count")], {"X07"}),
    ("XN31 the guard's range check dropped", "bas",
     [("        in_range = 0 <= slot < count", "        in_range = True")], {"X07"}),
    ("XN32 NOGUARD skips the self binding too", "bas",
     [(_GUARD_PRESS, "        press = ok or (_dbl_env(_DBL_FAULT_NOGUARD) and in_range)")], {"X07", "X08"}),
    ("XN33 NOGUARD skips the range check too", "bas",
     [(_GUARD_PRESS, '        press = ok or (_dbl_env(_DBL_FAULT_NOGUARD) and bool(ctx["self"]))')], {"X07"}),
    ("XN34 NOGUARD presses whatever (no self, no range)", "bas",
     [(_GUARD_PRESS, "        press = ok or _dbl_env(_DBL_FAULT_NOGUARD)")], {"X07", "X08"}),
    ("XN35 the menu line logs ok= from the PRESS", "bas",
     [("menu_pid={menu_pid} intended_pid={intended} ok={int(ok)} a_pressed={int(press)} aim={aim} ",
       "menu_pid={menu_pid} intended_pid={intended} ok={int(press)} a_pressed={int(press)} aim={aim} ")],
     {"X06", "X12"}),
    ("XN36 the menu line logs a_pressed= from the VERDICT", "bas",
     [("menu_pid={menu_pid} intended_pid={intended} ok={int(ok)} a_pressed={int(press)} aim={aim} ",
       "menu_pid={menu_pid} intended_pid={intended} ok={int(ok)} a_pressed={int(ok)} aim={aim} ")], {"X06", "X12"}),
    ("XN37 the guard reads the PID at the AIM (review F8 half-applied: the living partner is fed)", "bas",
     [('            f["menu_pid"] = unpack_uint32(read_symbol("gPlayerParty", offset=100 * slot, size=4))',
       '            f["menu_pid"] = unpack_uint32(read_symbol("gPlayerParty", offset=100 * aim, size=4))')], {"X01"}),
    ("XN39 battler_in_menu logs our g, not gBattlerInMenuId", "bas",
     [('        f["bim"] = read_symbol("gBattlerInMenuId", size=1)[0]', '        f["bim"] = ctx["g"]')], {"X09"}),
    ("XN43 `target-chosen` staged on a refusal too", "bas",
     [(_A_BLOCK, "        if _dbl_ctx is None or _dbl_guard(_dbl_ctx, _menu_slot):\n"
                 '            context.emulator.press_button("A")\n            yield\n        _stage("target-chosen")\n')],
     {"X10"}),
    ("XN47 the after line's same= always 1", "bas",
     [('        same = int(bool(t0 and t1 and t0["pid"] == t1["pid"]))', "        same = 1")], {"X11"}),
    ("XN50 WRONGSLOT applied BEFORE the KI-101 re-map (which overwrites it)", "bas",
     [(_WRONGSLOT, ""),
      ("        _menu_slot = target_index\n        _ki101_wait = 0\n",
       "        _menu_slot = target_index\n        _ki101_wait = 0\n" + _WRONGSLOT)], {"X05", "X06"}),
    ("XN51 WRONGSLOT aims at the requester's OWN side", "bas",
     [('            _menu_slot = 1 - _dbl_ctx["side"]', '            _menu_slot = _dbl_ctx["side"]')], {"X05", "X06"}),
    ("XN52 WRONGSLOT aims at 1 - g", "bas",
     [('            _menu_slot = 1 - _dbl_ctx["side"]', '            _menu_slot = 1 - _dbl_ctx["g"]')], {"X05"}),
    ("XN54 WRONGSLOT aims at bench slot 2 + side", "bas",
     [('            _menu_slot = 1 - _dbl_ctx["side"]', '            _menu_slot = 2 + _dbl_ctx["side"]')], {"X05", "X06"}),
]
#: LEFT OUT from the adversaries' survivors, with their own (re-checked) arguments: the EQUIVALENT or UNREACHABLE ones
#: (strategy: N04 N10 N11 N15 N24 N26 N27 N29 S01 S02 S18 S37 S39 S44; executor: N03 N14 N15 N24 N26 N27 N29 N40 N59
#: N60 N63 N66 N67 — e.g. N59's `break` is followed by the same `return`, N60's `sub_802C098` exists only in the R/S
#: symbol files), and the strategy hunter's S33 ("observe drops the cure fallback"), which SF-1 made the INTENDED code:
#: its inverse is RV-SF1b. ⛔ The `mode != OFF` half of N2's double test is EQUIVALENT alone (the env test before it
#: guards the same values); MS01 drops both.

#: FAULT-ARM MUTANTS (the fold, 2026-09-30): the executor hunter showed the old runner never ran a mutant WITH a fault
#: set, so a mutant that lives in fault-arm code was invisible. These jobs install the mutant AND set the fault; the red
#: set is the fault's pre-registered set changed by the mutant, derived before the first run.
FAULT_MUTANTS: list = [
    ("XN02 CURSOR0 TOGGLES the side for every battler (battler 0 reads byte 2 under the fault)", "bm",
     [(_CURSOR_IF, "    import os as _os_c1\n\n"
                   '    if _os_c1.environ.get("POKEBOT_R27_FAULT_DBL_CURSOR0") == "1":\n'
                   "        is_right_side_pokemon = not is_right_side_pokemon\n")],
     F_CURSOR0, {"DQ11", "DQ12", "X02"}),
    ("XN53 WRONGSLOT fires with the flag unset and in singles", "bas",
     [(_WRONGSLOT, "        if _dbl_env(_DBL_FAULT_WRONGSLOT):\n            _menu_slot = 1 - battler_index // 2\n")],
     F_WRONGSLOT, {"DQ13", "DQ17", "DBsingleexec"}),
    ("XN34f NOGUARD presses whatever, under the NOGUARD job", "bas",
     [(_GUARD_PRESS, "        press = ok or _dbl_env(_DBL_FAULT_NOGUARD)")],
     F_NOGUARD, {"DQ14", "DQ15", "DBself", "X07", "X08"}),
]

_MUTANT_IDS = {label.split()[0] for label, _t, _e, _w in MUTANTS}
assert set(MUTANT_ADDITIONS) <= _MUTANT_IDS, sorted(set(MUTANT_ADDITIONS) - _MUTANT_IDS)
_SRCS: dict = {}


def _jobs() -> list:
    """Every job: ("fault", label, env, None, want), ("mutant", label, target, edits, want) or
    ("fmutant", label, target, (edits, fault env), want)."""
    return ([("fault", f"FAULT {env}", env, None, set(want)) for env, want in FAULT_SETS.items()]
            + [("mutant", label, target, edits, set(want) | MUTANT_ADDITIONS.get(label.split()[0], set()))
               for label, target, edits, want in MUTANTS]
            + [("mutant", label, target, edits, set(want)) for label, target, edits, want in FOLD_MUTANTS]
            + [("fmutant", label, target, (edits, fault), set(want))
               for label, target, edits, fault, want in FAULT_MUTANTS])


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
            fault = None
            if kind == "fmutant":                           # a mutant in fault-arm code, run UNDER that fault
                edits, fault = edits
            msrcs[target] = _apply(srcs[target], edits)
            _install(NAMES[target], PATHS[target], msrcs[target], i)
            if fault:
                os.environ[fault] = "1"
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
