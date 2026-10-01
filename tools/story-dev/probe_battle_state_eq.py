r"""GATE (offline, no ROM) — `BattleState.__eq__` compares the party ORDER and the TURN, so every `get_battle_state()`
caller in a frame sees what the FIRST caller of that frame saw (`#27-battleeq`, KI-108, 2026-10-01).

WHY: upstream's `__eq__` compares 9 of the 11 constructor fields; it omits `_battler_party_order` and `_current_turn`.
`get_battle_state()` re-reads memory on the first call of a frame and hands the new object to the cache setter
(`state_cache.py`), which KEEPS THE OLD OBJECT when `old == new`. So a re-read that differs only in the order or the
turn is called "equal", and every later caller in that frame (and in later frames, until a compared field changes)
receives the OLD order and turn. The KI-96 / KI-101 menu re-maps exist only to get a FRESH order. MEASURED live on
2026-09-28 (`evidence/2026-09-28-ki47oor-VOID-injection.txt`, Run B): the driver's own re-read said 104523 while the
handler, in the same frame, read 012345. The fix compares both fields unless `POKEBOT_KI108_FAULT_OLDEQ` is exactly
"1" (read PER CALL), which restores upstream's compare for A/B. Design + predictions (filed before code):
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-01-battleeq-DESIGN.md`.

‼ THE CAVEAT: the fix makes second callers CURRENT, not correct. It does NOT cover a memory write made WITHIN a frame
(the `age_in_frames == 0` early return is unchanged; row K9-runA pins that), and "fresh" is not "the player's order".

THE WORLD: the REAL `get_battle_state()` and `BattleState` (the file's source, loaded fresh per subject) over a fake
`read_symbol` (`gBattleResults` is read at offset 0x13) and a SETTABLE frame counter that starts at 1 (at 0 the very
first call would return the empty cache). Each row gets a fresh `StateCache` from the (possibly mutated)
`state_cache.py`. "FAULT" rows run with the switch "1"; "FIX" rows with it unset. The switch is cleared at start and
restored at exit, so an inherited environment cannot decide a row.

ROWS
  C0        the first call is fresh (order and turn from memory) and is stored in the cache.
  C1        two calls in one frame with no change return the SAME object.
  K1        switch ON reproduces the bug: an order-only change; the first caller is fresh, the second gets the OLD
            order and IS the old object.
  K2        fixed: the second caller gets the new order and is the first caller's object.
  K3-*      the stale object persists into the NEXT frame (fault) / the fixed object is kept, not replaced (fix).
  K4-*      the turn alone changes.
  K5        order AND HP change together: both arms identical (the VACUITY WITNESS - an ordinary A/B moves a compared
            field and therefore cannot tell the arms apart).
  K6 / K6-* `__eq__` semantics: identical bytes are equal and a different HP is unequal in BOTH arms, a non-BattleState
            gives NotImplemented; an order-only or turn-only difference is equal (fault) / unequal (fix).
  K7-*      the switch is read per call, and ONLY the exact string "1" restores the old compare.
  K8-*      the bookkeeping: the cache item's `.frame` stamp moves on an order-only change only under the fix, and an
            unchanged re-read never bumps it.
  K9-runA   an IN-FRAME memory write after the frame's first read is invisible to later callers in BOTH arms (out of
            scope by design: the early return is unchanged).
  K9-*      KI-108's Run-B shape: first read, a memory write, the entry aged one frame, a plain re-read, then the
            "handler" call. Fault: the handler gets the OLD order although the re-read saw the new; fix: the new.
  W1-W6     wiring, by AST (comments and docstrings cannot satisfy or trip them): W1/W2 `__eq__` reads both halves of
            the order / the turn; W3 every such read sits inside an `if` whose test reads the switch; W4 `__eq__` reads
            the switch by its exact literal and nothing reads it at module level; W5 the literal is registered in
            `29-DISABLED-FEATURES-REGISTRY.md`; W6 `get_battle_state` keeps its early return, stores the new object,
            and RETURNS THE LOCAL.

MUTANTS (each graded only when the UNMUTATED subject passes every row; each red set below was written BEFORE the
mutant's first run). M0 is the upstream mirror's file verbatim (the bug, permanently re-runnable). M8 is a
comment-only mention and must redden NOTHING. A COVERAGE check requires every row to be in some mutant's red set.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_battle_state_eq.py
"""
import ast
import importlib.util
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
BS = SANDBOX / "modules" / "battle_state.py"
SC = SANDBOX / "modules" / "state_cache.py"
MIRROR_BS = REPO / "40cakes repo" / "pokebot-gen3" / "modules" / "battle_state.py"
REGISTRY = REPO / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
SWITCH = "POKEBOT_KI108_FAULT_OLDEQ"
FIELDS = ("_battler_party_order", "_current_turn")

from modules.context import context  # noqa: E402  (after the sys.path insert)

ORDER_A = bytes.fromhex("012345")
ORDER_B = bytes.fromhex("104523")
TURN_A, TURN_B = 3, 4
HP_A, HP_B = 20, 13
failures: list = []


def check(cond, msg) -> None:
    if not cond:
        failures.append(msg)
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


# ---------------------------------------------------------------- the fake world
class FakeEmulator:
    """Only what `StateCacheItem` touches. The frame is SET by the row, never advanced implicitly."""

    def __init__(self, frame: int = 1) -> None:
        self.frame = frame

    def get_frame_count(self) -> int:
        return self.frame


class FakeMemory:
    """The eleven symbols `get_battle_state()` reads, behind a `read_symbol(name, offset=0, size=0)`."""

    def __init__(self) -> None:
        self.sym = {
            "gBattleTypeFlags": bytearray(4),
            "gSideTimers": bytearray(0x18),
            "gBattlerPartyIndexes": bytearray(8),
            "gBattlePartyCurrentOrder": bytearray(ORDER_A),
            "gBattlersCount": bytearray([2]),
            "gBattleMons": bytearray(0x160),
            "gStatuses3": bytearray(0x10),
            "gDisableStructs": bytearray(0x70),
            "gAbsentBattlerFlags": bytearray(1),
            "gBattleResults": bytearray(0x20),
            "gBattleWeather": bytearray(2),
        }
        self.set_turn(TURN_A)
        self.set_hp(HP_A)

    def read_symbol(self, name: str, offset: int = 0, size: int = 0) -> bytes:
        block = self.sym[name]
        return bytes(block[offset:offset + size]) if size else bytes(block[offset:])

    def set_order(self, order: bytes) -> None:
        self.sym["gBattlePartyCurrentOrder"][:] = order

    def set_turn(self, turn: int) -> None:
        self.sym["gBattleResults"][0x13] = turn

    def set_hp(self, hp: int) -> None:
        # battler 0's HP (struct BattlePokemon +0x28): a COMPARED field (`_battler`).
        self.sym["gBattleMons"][0x28:0x2A] = hp.to_bytes(2, "little")


_seq = [0]


def _load(name: str, src: str, path: pathlib.Path):
    _seq[0] += 1
    modname = f"_ki108_{name}_{_seq[0]}"
    spec = importlib.util.spec_from_loader(modname, loader=None, origin=str(path))
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(path)
    sys.modules[modname] = mod
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


class Subject:
    """The code under test: battle_state.py + state_cache.py sources (each loaded fresh) and the registry text."""

    def __init__(self, bs_src: str, sc_src: str, reg: str) -> None:
        self.bs_src, self.sc_src, self.reg = bs_src, sc_src, reg
        self.bs = _load("battle_state", bs_src, BS)
        self.scm = _load("state_cache", sc_src, SC)


class World:
    def __init__(self, subj: Subject) -> None:
        self.emu = FakeEmulator(1)
        context.emulator = self.emu
        self.mem = FakeMemory()
        self.sc = subj.scm.StateCache()
        subj.bs.state_cache = self.sc
        subj.bs.read_symbol = self.mem.read_symbol
        self.subj = subj

    def gbs(self):
        return self.subj.bs.get_battle_state()

    @property
    def item(self):
        return self.sc.battle_state

    def next_frame(self) -> None:
        self.emu.frame += 1


class switch:
    """`with switch("1"):` = the FAULT arm; `with switch(None):` = the fix. Always cleared on exit."""

    def __init__(self, value) -> None:
        self.value = value

    def __enter__(self):
        if self.value is None:
            os.environ.pop(SWITCH, None)
        else:
            os.environ[SWITCH] = self.value
        return self

    def __exit__(self, *_exc) -> None:
        os.environ.pop(SWITCH, None)


def order(state) -> bytes:
    return bytes(state._battler_party_order)


def make_state(bs, order_bytes=ORDER_A, turn=TURN_A, hp=HP_A):
    """A `BattleState` built exactly as `get_battle_state()` builds one, from fresh bytes objects."""
    m = FakeMemory()
    m.set_order(order_bytes)
    m.set_turn(turn)
    m.set_hp(hp)
    r = m.read_symbol
    return bs.BattleState(
        r("gBattleTypeFlags", size=0x04), r("gSideTimers", size=0x18), r("gBattlerPartyIndexes", size=0x08),
        r("gBattlePartyCurrentOrder", size=0x03), r("gBattlersCount", size=0x01)[0], r("gBattleMons", size=0x160),
        r("gStatuses3", size=0x10), r("gDisableStructs", size=0x70), r("gAbsentBattlerFlags", size=0x01)[0],
        r("gBattleResults", offset=0x13, size=1)[0], int.from_bytes(r("gBattleWeather", size=0x02), "little"))


# ---------------------------------------------------------------- the rows (each returns (ok, detail))
def row_c0(S):
    with switch(None):
        w = World(S)
        r = w.gbs()
        ok = order(r) == ORDER_A and r._current_turn == TURN_A and w.item.value is r
        return ok, f"order={order(r).hex()} turn={r._current_turn} stored={w.item.value is r}"


def row_c1(S):
    with switch(None):
        w = World(S)
        a = w.gbs()
        b = w.gbs()
        return b is a, f"second call is the first's object: {b is a}"


def _order_change(S, env):
    """frame 1: a; frame 2: memory order -> B; f = first caller, s = second caller."""
    with switch(env):
        w = World(S)
        a = w.gbs()
        w.next_frame()
        w.mem.set_order(ORDER_B)
        f = w.gbs()
        s = w.gbs()
        return a, f, s


def row_k1(S):
    a, f, s = _order_change(S, "1")
    ok = order(f) == ORDER_B and order(s) == ORDER_A and s is a
    return ok, f"first={order(f).hex()} second={order(s).hex()} second_is_old={s is a}"


def row_k2(S):
    a, f, s = _order_change(S, None)
    ok = order(f) == ORDER_B and order(s) == ORDER_B and s is f
    return ok, f"first={order(f).hex()} second={order(s).hex()} second_is_first={s is f}"


def _persist(S, env):
    """frame 1: a; frame 2: order -> B, f2, s2; frame 3 (no change): f3, s3."""
    with switch(env):
        w = World(S)
        a = w.gbs()
        w.next_frame()
        w.mem.set_order(ORDER_B)
        f2 = w.gbs()
        w.gbs()
        w.next_frame()
        f3 = w.gbs()
        s3 = w.gbs()
        return a, f2, f3, s3


def row_k3_fault(S):
    a, f2, f3, s3 = _persist(S, "1")
    ok = order(f3) == ORDER_B and order(s3) == ORDER_A and s3 is a
    return ok, f"frame 3: first={order(f3).hex()} second={order(s3).hex()} second_is_frame1_object={s3 is a}"


def row_k3_fix(S):
    a, f2, f3, s3 = _persist(S, None)
    ok = order(f3) == ORDER_B and order(s3) == ORDER_B and s3 is f2
    return ok, f"frame 3: first={order(f3).hex()} second={order(s3).hex()} second_is_frame2_object={s3 is f2}"


def _turn_change(S, env):
    with switch(env):
        w = World(S)
        a = w.gbs()
        w.next_frame()
        w.mem.set_turn(TURN_B)
        f = w.gbs()
        s = w.gbs()
        return a, f, s


def row_k4_fault(S):
    a, f, s = _turn_change(S, "1")
    ok = f._current_turn == TURN_B and s._current_turn == TURN_A and s is a
    return ok, f"first turn={f._current_turn} second turn={s._current_turn} second_is_old={s is a}"


def row_k4_fix(S):
    a, f, s = _turn_change(S, None)
    ok = f._current_turn == TURN_B and s._current_turn == TURN_B and s is f
    return ok, f"first turn={f._current_turn} second turn={s._current_turn} second_is_first={s is f}"


def row_k5(S):
    seen = {}
    for env in ("1", None):
        with switch(env):
            w = World(S)
            w.gbs()
            w.next_frame()
            w.mem.set_order(ORDER_B)
            w.mem.set_hp(HP_B)
            f = w.gbs()
            s = w.gbs()
            seen[env] = (order(s) == ORDER_B, s is f)
    ok = seen["1"] == seen[None] == (True, True)
    return ok, f"(second has new order, second is first): fault={seen['1']} fix={seen[None]}"


def row_k6(S):
    out = []
    for env in ("1", None):
        with switch(env):
            x, y, y_hp = make_state(S.bs), make_state(S.bs), make_state(S.bs, hp=HP_B)
            out.append((x == y) is True and (x != y) is False and x.__eq__(42) is NotImplemented
                       and (x == 42) is False and (x == y_hp) is False)
    return all(out), f"identical-equal / NotImplemented / hp-unequal: fault={out[0]} fix={out[1]}"


def row_k6_fault(S):
    with switch("1"):
        x = make_state(S.bs)
        yo, yt = make_state(S.bs, order_bytes=ORDER_B), make_state(S.bs, turn=TURN_B)
        got = ((x == yo), (x == yt), (x != yo))
    return got == (True, True, False), f"(==order-only, ==turn-only, !=order-only) = {got}"


def row_k6_fix(S):
    with switch(None):
        x = make_state(S.bs)
        yo, yt = make_state(S.bs, order_bytes=ORDER_B), make_state(S.bs, turn=TURN_B)
        got = ((x == yo), (x == yt), (x != yo), (x != yt))
    return got == (False, False, True, True), f"(==order, ==turn, !=order, !=turn) = {got}"


def row_k7_fault(S):
    with switch("1"):
        x = make_state(S.bs)
        got = (x == make_state(S.bs, order_bytes=ORDER_B), x == make_state(S.bs, turn=TURN_B))
    return got == (True, True), f'switch "1": (==order-only, ==turn-only) = {got}'


def row_k7_fix(S):
    x = make_state(S.bs)
    yo, yt = make_state(S.bs, order_bytes=ORDER_B), make_state(S.bs, turn=TURN_B)
    bad = []
    for v in ("0", "", "true", "yes", "01", " 1", "1 ", "2", None):
        with switch(v):
            if (x == yo) or (x == yt):
                bad.append(repr(v))
    flips = []
    for v in ("1", None, "1", "0"):  # the SAME objects, the SAME module: only a per-call read can follow this
        with switch(v):
            flips.append(x == yo)
    ok = not bad and flips == [True, False, True, False]
    return ok, f"values that restored the old compare: {bad or 'none'}; per-call flip 1/unset/1/0 -> {flips}"


def row_k8_fault(S):
    with switch("1"):
        w = World(S)
        w.gbs()
        f1 = w.item.frame
        w.next_frame()
        w.mem.set_order(ORDER_B)
        w.gbs()
        w.gbs()
        got = (f1, w.item.frame, w.item._last_check_frame)
    return got == (1, 1, 2), f"(frame after f1, frame after f2, last_check after f2) = {got}"


def row_k8_fix(S):
    with switch(None):
        w = World(S)
        w.gbs()
        f1 = w.item.frame
        w.next_frame()
        w.mem.set_order(ORDER_B)
        w.gbs()
        w.gbs()
        f2 = (w.item.frame, w.item._last_check_frame)
        w.next_frame()
        w.gbs()
        f3 = (w.item.frame, w.item._last_check_frame)
    got = (f1, f2, f3)
    return got == (1, (2, 2), (2, 3)), f"(f1 frame, f2 (frame, check), f3 (frame, check)) = {got}"


def row_k9_runa(S):
    seen = {}
    for env in ("1", None):
        with switch(env):
            w = World(S)
            w.gbs()                      # an earlier frame's read: the cache is warm
            w.next_frame()
            d = w.gbs()                  # the dispatcher: the frame's FIRST caller
            w.mem.set_order(ORDER_B)     # an in-frame write (Run A: no ageing)
            h = w.gbs()                  # the handler, same frame
            seen[env] = (order(d).hex(), order(h).hex())
    ok = seen["1"] == seen[None] == (ORDER_A.hex(), ORDER_A.hex())
    return ok, f"(dispatcher, handler) fault={seen['1']} fix={seen[None]}"


def _run_b(S, env):
    with switch(env):
        w = World(S)
        w.gbs()
        w.next_frame()
        w.gbs()                          # the dispatcher's condition: the frame's first caller
        w.mem.set_order(ORDER_B)         # the driver's write
        w.item._last_check_frame -= 1    # the driver ages the entry by one frame
        r = w.gbs()                      # the driver's plain re-read
        h = w.gbs()                      # the handler's own call, same frame
        return r, h


def row_k9_fault(S):
    r, h = _run_b(S, "1")
    ok = order(r) == ORDER_B and order(h) == ORDER_A
    return ok, f"driver re-read={order(r).hex()} handler={order(h).hex()}"


def row_k9_fix(S):
    r, h = _run_b(S, None)
    ok = order(r) == ORDER_B and order(h) == ORDER_B and h is r
    return ok, f"driver re-read={order(r).hex()} handler={order(h).hex()} handler_is_reread={h is r}"


# ---------------------------------------------------------------- wiring (AST)
def _call_name(c) -> str:
    f = c.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def _is_switch_read(n) -> bool:
    return (isinstance(n, ast.Call) and _call_name(n) in ("get", "getenv") and bool(n.args)
            and isinstance(n.args[0], ast.Constant) and n.args[0].value == SWITCH)


def _eq_fn(tree):
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "BattleState"), None)
    if cls is None:
        return None
    return next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__eq__"), None)


def _field_reads(eq, field):
    return {n.value.id for n in ast.walk(eq)
            if isinstance(n, ast.Attribute) and n.attr == field and isinstance(n.value, ast.Name)}


def row_w1(S):
    eq = _eq_fn(ast.parse(S.bs_src))
    got = _field_reads(eq, FIELDS[0]) if eq else set()
    return {"self", "other"} <= got, f"__eq__ reads {FIELDS[0]} on {sorted(got)}"


def row_w2(S):
    eq = _eq_fn(ast.parse(S.bs_src))
    got = _field_reads(eq, FIELDS[1]) if eq else set()
    return {"self", "other"} <= got, f"__eq__ reads {FIELDS[1]} on {sorted(got)}"


def row_w3(S):
    eq = _eq_fn(ast.parse(S.bs_src))
    if eq is None:
        return False, "no BattleState.__eq__"
    reads = [n for n in ast.walk(eq) if isinstance(n, ast.Attribute) and n.attr in FIELDS]
    guarded = set()
    for n in ast.walk(eq):
        if isinstance(n, ast.If) and any(_is_switch_read(x) for x in ast.walk(n.test)):
            guarded.update(id(x) for x in ast.walk(n))
    loose = [n.lineno for n in reads if id(n) not in guarded]
    return bool(reads) and not loose, f"{len(reads)} read(s) of the two fields; unguarded at {loose}"


def row_w4(S):
    tree = ast.parse(S.bs_src)
    eq = _eq_fn(tree)
    in_eq = eq is not None and any(_is_switch_read(n) for n in ast.walk(eq))
    in_fn = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            in_fn.update(id(x) for x in ast.walk(n))
    outside = [n.lineno for n in ast.walk(tree) if _is_switch_read(n) and id(n) not in in_fn]
    return in_eq and not outside, f"read inside __eq__: {in_eq}; read outside any function at {outside}"


def row_w5(S):
    return SWITCH in S.reg, f"{SWITCH} in 29-DISABLED-FEATURES-REGISTRY.md: {SWITCH in S.reg}"


def row_w6(S):
    tree = ast.parse(S.bs_src)
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_battle_state"), None)
    if fn is None:
        return False, "no get_battle_state"
    body = [ast.unparse(s) for s in fn.body]
    early = body[0] == "if state_cache.battle_state.age_in_frames == 0:\n    return state_cache.battle_state.value"
    built = any(isinstance(s, ast.Assign) and [ast.unparse(t) for t in s.targets] == ["battle_state"]
                and isinstance(s.value, ast.Call) and _call_name(s.value) == "BattleState" for s in fn.body)
    stored = "state_cache.battle_state = battle_state" in body
    returns_local = body[-1] == "return battle_state"
    ok = early and built and stored and returns_local
    return ok, f"early return={early} builds local={built} stores={stored} returns the local={returns_local}"


ROWS = [
    ("C0", row_c0), ("C1", row_c1), ("K1", row_k1), ("K2", row_k2),
    ("K3-fault", row_k3_fault), ("K3-fix", row_k3_fix), ("K4-fault", row_k4_fault), ("K4-fix", row_k4_fix),
    ("K5", row_k5), ("K6", row_k6), ("K6-fault", row_k6_fault), ("K6-fix", row_k6_fix),
    ("K7-fault", row_k7_fault), ("K7-fix", row_k7_fix), ("K8-fault", row_k8_fault), ("K8-fix", row_k8_fix),
    ("K9-runA", row_k9_runa), ("K9-fault", row_k9_fault), ("K9-fix", row_k9_fix),
    ("W1", row_w1), ("W2", row_w2), ("W3", row_w3), ("W4", row_w4), ("W5", row_w5), ("W6", row_w6),
]


def run_rows(S, verbose=False) -> set:
    red = set()
    for label, fn in ROWS:
        try:
            ok, detail = fn(S)
        except Exception as err:  # noqa: BLE001 - a raising row is a RED row, with its reason printed
            ok, detail = False, f"raised {type(err).__name__}: {err}"
        if not ok:
            red.add(label)
        if verbose:
            check(ok, f"{label:<8} {detail}")
    return red


# ---------------------------------------------------------------- mutants (red sets written BEFORE the first run)
class Unbuildable(Exception):
    pass


def _sub(src: str, old: str, new: str) -> str:
    n = src.count(old)
    if n != 1:
        raise Unbuildable(f"anchor found {n} times (need exactly 1): {old[:70]!r}")
    return src.replace(old, new)


GUARD = f'os.environ.get("{SWITCH}") != "1"'
BOTH = "self._battler_party_order != other._battler_party_order or self._current_turn != other._current_turn"
IF_BLOCK = (f"            if {GUARD} and (\n"
            f"                {BOTH}\n"
            "            ):\n"
            "                return False\n")
TASKS_IMPORT = "from modules.tasks import get_global_script_context\n"
STORE_RETURN = "    state_cache.battle_state = battle_state\n    return battle_state\n"
EARLY = "    if state_cache.battle_state.age_in_frames == 0:\n        return state_cache.battle_state.value\n"
EQ_TAIL = ("                and self._weather == other._weather\n            )\n"
           "        else:\n            return NotImplemented\n")
SETTER = "        if self._battle_state.value != new_battle_state:\n"

FAULT_ROWS = {"K1", "K3-fault", "K4-fault", "K6-fault", "K7-fault", "K8-fault", "K9-fault"}
REVERT_RED = {"K2", "K3-fix", "K4-fix", "K6-fix", "K7-fix", "K8-fix", "K9-fix", "W1", "W2", "W3", "W4"}
NOSWITCH_RED = FAULT_ROWS | {"K7-fix", "W3", "W4"}


def mutants(bs: str, sc: str, reg: str):
    """(name, builder, EXACT predicted red set). Builders raise Unbuildable when an anchor is not unique."""
    return [
        ("M0 the upstream mirror's battle_state.py, verbatim (the unfixed code)",
         lambda: Subject(MIRROR_BS.read_text(encoding="utf-8"), sc, reg), REVERT_RED),
        ("M1 revert to the mirror's __eq__ (the KI-108 `if` removed; its WHY comment left in place)",
         lambda: Subject(_sub(bs, IF_BLOCK, ""), sc, reg), REVERT_RED),
        ("M2 drop only the turn",
         lambda: Subject(_sub(bs, BOTH, "self._battler_party_order != other._battler_party_order"), sc, reg),
         {"K4-fix", "K6-fix", "K7-fix", "W2"}),
        ("M3 drop only the order",
         lambda: Subject(_sub(bs, BOTH, "self._current_turn != other._current_turn"), sc, reg),
         {"K2", "K3-fix", "K6-fix", "K7-fix", "K8-fix", "K9-fix", "W1"}),
        ("M4 ignore the switch (always the fix)",
         lambda: Subject(_sub(bs, GUARD, "True"), sc, reg), NOSWITCH_RED),
        ("M5 read the switch at IMPORT (loaded with the switch unset)",
         lambda: Subject(_sub(_sub(bs, GUARD, "not _KI108_OLDEQ"), TASKS_IMPORT,
                              TASKS_IMPORT + f'_KI108_OLDEQ = os.environ.get("{SWITCH}") == "1"\n'), sc, reg),
         NOSWITCH_RED),
        ("M6 get_battle_state returns the CACHE value, not the local",
         lambda: Subject(_sub(bs, STORE_RETURN, "    state_cache.battle_state = battle_state\n"
                                                "    return state_cache.battle_state.value\n"), sc, reg),
         {"K1", "K3-fault", "K4-fault", "K9-fault", "W6"}),
        ("M7 the cache setter ALWAYS stores (state_cache.py)",
         lambda: Subject(bs, _sub(sc, SETTER, "        if True:\n"), reg),
         {"K1", "K3-fault", "K3-fix", "K4-fault", "K8-fault", "K8-fix", "K9-fault"}),
        ("M8 comment-only mentions of every mutant's code (must redden NOTHING)",
         lambda: Subject(_sub(_sub(_sub(bs, TASKS_IMPORT, TASKS_IMPORT
                                        + f'# _KI108_OLDEQ = os.environ.get("{SWITCH}") == "1"   (a mention)\n'),
                                   STORE_RETURN, "    state_cache.battle_state = battle_state\n"
                                                 "    # return state_cache.battle_state.value\n"
                                                 "    return battle_state\n"),
                              IF_BLOCK, "            # if True and (self._current_turn != other._current_turn):\n"
                                        "            #     return True\n" + IF_BLOCK),
                         sc, reg), set()),
        ("M9 rename the switch literal in battle_state.py",
         lambda: Subject(bs.replace(SWITCH, SWITCH + "X") if bs.count(SWITCH) else _sub(bs, SWITCH, ""), sc, reg),
         NOSWITCH_RED),
        ("M10 re-read on age 0 (the early return removed: the design's REJECTED alternative)",
         lambda: Subject(_sub(bs, EARLY, ""), sc, reg),
         {"C1", "K1", "K2", "K3-fault", "K3-fix", "K4-fault", "K4-fix", "K5", "K9-runA", "K9-fault", "K9-fix",
          "W6"}),
        ("M11 the new object is never stored in the cache",
         lambda: Subject(_sub(bs, STORE_RETURN, "    return battle_state\n"), sc, reg),
         {"C0", "C1", "K1", "K2", "K3-fault", "K3-fix", "K4-fault", "K4-fix", "K5", "K8-fault", "K8-fix",
          "K9-runA", "K9-fault", "K9-fix", "W6"}),
        ("M12 __eq__ returns False (not NotImplemented) for a non-BattleState",
         lambda: Subject(_sub(bs, EQ_TAIL, EQ_TAIL.replace("return NotImplemented", "return False")), sc, reg),
         {"K6"}),
        ("M13 the switch's registry row removed",
         lambda: Subject(bs, sc, reg.replace(SWITCH, "REMOVED")), {"W5"}),
    ]


def main() -> int:
    inherited = os.environ.pop(SWITCH, None)
    saved_emulator = getattr(context, "emulator", None)
    try:
        bs_src = BS.read_text(encoding="utf-8")
        sc_src = SC.read_text(encoding="utf-8")
        reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
        if inherited is not None:
            print(f"  (note: {SWITCH}={inherited!r} was set in the environment; cleared for the gate, restored after)")
        print(f"ROWS - the REAL get_battle_state()/BattleState from {BS.relative_to(REPO)}")
        base_red = run_rows(Subject(bs_src, sc_src, reg), verbose=True)
        print(f"  -> {len(ROWS)} rows, red: {sorted(base_red) or 'none'}")

        print("MUTANTS (graded only when the unmutated subject passes every row)")
        muts = mutants(bs_src, sc_src, reg)
        if base_red:
            check(False, f"MUTANTS NOT GRADED: the unmutated subject has {len(base_red)} red row(s) "
                         f"{sorted(base_red)} - no mutant can prove anything against a red baseline")
        else:
            for name, build, predicted in muts:
                try:
                    subj = build()
                except Unbuildable as err:
                    check(False, f"{name}: UNBUILDABLE ({err})")
                    continue
                red = run_rows(subj)
                check(red == predicted, f"{name}\n         predicted {sorted(predicted) or '{} (nothing)'}\n"
                                        f"         actual    {sorted(red) or '{} (nothing)'}")
        covered = set().union(*(p for _, _, p in muts))
        uncovered = [label for label, _ in ROWS if label not in covered]
        check(not uncovered, f"COVERAGE every row is in some mutant's red set (uncovered: {uncovered or 'none'})")
        print(f"  ({len(muts)} mutants)")
    finally:
        os.environ.pop(SWITCH, None)
        if inherited is not None:
            os.environ[SWITCH] = inherited
        context.emulator = saved_emulator

    print()
    if failures:
        print(f"FAIL - {len(failures)} check(s) failed")
        return 1
    print("PASS - every get_battle_state() caller in a frame sees the first caller's order and turn; the switch "
          "restores the 9-field compare per call")
    return 0


if __name__ == "__main__":
    sys.exit(main())
