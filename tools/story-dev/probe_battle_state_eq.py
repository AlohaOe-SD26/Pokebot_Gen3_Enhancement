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

ROWS (every one is BEHAVIOURAL except R1; nothing here reads the source text of battle_state.py)
  C0        the first call is fresh (order and turn from memory) and is stored in the cache.
  C1        two calls in one frame with no change return the SAME object.
  K1        switch ON reproduces the bug: an order-only change; the first caller is fresh (it gets the locally built
            object, not the kept old one), the second gets the OLD order and IS the old object.
  K2        fixed: the second caller gets the new order and is the first caller's object.
  K3-*      the stale object persists into the NEXT frame (fault) / the fixed object is kept, not replaced (fix).
  K4-*      the turn alone changes.
  K5        order AND HP change together: both arms identical (the VACUITY WITNESS - an ordinary A/B moves a compared
            field and therefore cannot tell the arms apart).
  K6 / K6-* `__eq__` semantics: identical bytes are equal and a different HP is unequal in BOTH arms, a non-BattleState
            gives NotImplemented; an order-only or turn-only difference is equal (fault) / unequal (fix).
  K7-*      the switch is read per call (a flip on the SAME objects), on a sample of values.
  K8-*      the bookkeeping: the cache item's `.frame` stamp moves on an order-only change only under the fix, and an
            unchanged re-read never bumps it.
  K9-runA   an IN-FRAME memory write after the frame's first read is invisible to later callers in BOTH arms (out of
            scope by design: the early return is unchanged).
  K9-*      KI-108's Run-B shape: first read, a memory write, the entry aged one frame, a plain re-read, then the
            "handler" call. Fault: the handler gets the OLD order although the re-read saw the new; fix: the new.
  ---- added 2026-10-01 from the INDEPENDENT mutant hunt (its X1-X5; it found 22 non-equivalent survivors because
       the world above varies only ORDER_A -> ORDER_B, one turn step 3 -> 4, and battler 0's HP):
  K10       every ORDER change shape (byte 0 only, byte 1 only, byte 2 only, a whole-byte permutation with the same
            multiset and sum, the full permutation) and every TURN change (+1, -1, +2, to 0, 255 -> 0), in BOTH
            directions, through the real cache: fix = the second caller gets the new value; fault = it gets the old
            object.
  K11       each of upstream's 9 compared fields changed ALONE (first byte, last byte) is unequal, both ways round, in
            BOTH arms: the switch restores EXACTLY upstream's compare and the fix drops none of it.
  K12       the switch's value is compared with the string "1" and with NOTHING ELSE, and no method is called on it
            (exhaustive, not sampled: a str subclass records every comparison and attribute access). The module's
            own `os` / `os.environ` / `os.getenv` bindings (any alias) AND `os.environ.get` itself are served from a
            shim for the row, so hoisting the literal, aliasing `environ` or a function-local `import os` all pass.
            This row also pins the LITERAL behaviourally: the shim knows only the real variable name.
  K13       the frame counter going BACKWARDS (a reset / state load with no cache reset; `StateCacheItem`'s "frame
            lower than the data" branch) makes the next call fresh; then fault = second caller old, fix = new.
  R1        `29-DISABLED-FEATURES-REGISTRY.md` §B holds a TABLE ROW whose first cell is exactly the backticked literal.
  ⛔ REMOVED 2026-10-01 (the hunt): W1-W4 (AST wiring) were satisfied by DEAD code (`if False:`, an unused helper, a
     shadowed second `__eq__`, a lambda) and killed nothing the behaviour rows do not; W3/W4 FALSE-POSITIVED on the
     literal hoisted into a module constant, and W6 on the equivalent `age <= 0` / `age < 1`. K1 pins "the first call
     returns the locally built object" behaviourally (the only place the local and the kept object can differ in
     content is under the switch), C0 pins the store, C1 / K9-runA the early return. W5 was a bare substring test; R1
     replaces it. CLAUDE.md SESSION DISCIPLINE rule 6: a gate with false positives teaches the reader to bypass it.

MUTANTS (each graded only when the UNMUTATED subject passes every row; every red set was written BEFORE that mutant's
first run). M0 is the upstream mirror's file verbatim (the bug, permanently re-runnable). M14-M27 are the hunt's gap
families. M8 (comment-only mentions) and E1-E6 (EQUIVALENT refactors) must redden NOTHING. A COVERAGE check requires
every row to be in some mutant's red set, and a LOAD-BEARING check requires each of K10-K13 and R1 to be the ONLY red
row of at least one mutant.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_battle_state_eq.py
"""
import importlib.util
import os
import pathlib
import re
import sys
import types

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
BS = SANDBOX / "modules" / "battle_state.py"
SC = SANDBOX / "modules" / "state_cache.py"
MIRROR_BS = REPO / "40cakes repo" / "pokebot-gen3" / "modules" / "battle_state.py"
REGISTRY = REPO / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
SWITCH = "POKEBOT_KI108_FAULT_OLDEQ"

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


def _state_args(order_bytes=ORDER_A, turn=TURN_A, hp=HP_A) -> list:
    """The 11 `BattleState` constructor arguments, built exactly as `get_battle_state()` builds them (fresh objects)."""
    m = FakeMemory()
    m.set_order(order_bytes)
    m.set_turn(turn)
    m.set_hp(hp)
    r = m.read_symbol
    return [
        r("gBattleTypeFlags", size=0x04), r("gSideTimers", size=0x18), r("gBattlerPartyIndexes", size=0x08),
        r("gBattlePartyCurrentOrder", size=0x03), r("gBattlersCount", size=0x01)[0], r("gBattleMons", size=0x160),
        r("gStatuses3", size=0x10), r("gDisableStructs", size=0x70), r("gAbsentBattlerFlags", size=0x01)[0],
        r("gBattleResults", offset=0x13, size=1)[0], int.from_bytes(r("gBattleWeather", size=0x02), "little")]


def make_state(bs, order_bytes=ORDER_A, turn=TURN_A, hp=HP_A):
    return bs.BattleState(*_state_args(order_bytes, turn, hp))


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


# ---- K10-K13 and R1: the independent hunt's X1-X5 (2026-10-01), folded in with the gate's naming ----------------
ORDER_VARIANTS = ("102345", "013245", "012354", "014523", "104523")   # byte 0 / 1 / 2 only, a same-sum permutation, B
TURN_PAIRS = ((3, 4), (4, 3), (3, 5), (3, 0), (255, 0))


def _two_frames(S, env, old, new):
    """frame 1 with `old` applied to memory: a; frame 2 with `new` applied: f (first caller), s (second caller)."""
    with switch(env):
        w = World(S)
        old(w.mem)
        a = w.gbs()
        w.next_frame()
        new(w.mem)
        f = w.gbs()
        s = w.gbs()
        return a, f, s


def row_k10(S):
    cases = []
    for h in ORDER_VARIANTS:
        v = bytes.fromhex(h)
        for old, new in ((ORDER_A, v), (v, ORDER_A)):
            cases.append((f"order {old.hex()}->{new.hex()}", lambda m, o=old: m.set_order(o),
                          lambda m, n=new: m.set_order(n), lambda st, n=new: order(st) == n))
    for t0, t1 in TURN_PAIRS:
        cases.append((f"turn {t0}->{t1}", lambda m, t=t0: m.set_turn(t), lambda m, t=t1: m.set_turn(t),
                      lambda st, t=t1: st._current_turn == t))
    bad = []
    for label, old, new, is_new in cases:
        a, f, s = _two_frames(S, None, old, new)
        if not (is_new(f) and is_new(s) and s is f):
            bad.append(f"FIX {label}")
        a, f, s = _two_frames(S, "1", old, new)
        if not (is_new(f) and s is a):
            bad.append(f"FAULT {label}")
    return not bad, f"{len(cases)} order/turn changes x 2 arms; wrong: {bad or 'none'}"


NINE = ((0, "battle_type"), (1, "side_timers"), (2, "battler_party_indexes"), (4, "battler_count"), (5, "battler"),
        (6, "battler_status3"), (7, "battler_disable_structs"), (8, "absent_battler_flags"), (10, "weather"))


def _perturbed(i: int, where: str) -> list:
    args = _state_args()
    v = args[i]
    if isinstance(v, int):
        args[i] = v + 1
    else:
        b = bytearray(v)
        b[0 if where == "first" else -1] ^= 0xFF
        args[i] = bytes(b)
    return args


def row_k11(S):
    bad = []
    for env in ("1", None):
        with switch(env):
            x, x2 = S.bs.BattleState(*_state_args()), S.bs.BattleState(*_state_args())
            if not ((x == x2) is True and (x2 == x) is True and (x != x2) is False):
                bad.append(f"arm={env or 'fix'}: identical copies not equal")
            for i, name in NINE:
                for where in ("first", "last"):
                    y = S.bs.BattleState(*_perturbed(i, where))
                    got = ((x == y), (y == x), (x != y), (y != x))
                    if got != (False, False, True, True):
                        bad.append(f"arm={env or 'fix'} {name}[{where}] -> {got}")
    return not bad, f"9 fields x first/last byte x both orders x 2 arms; wrong: {bad or 'none'}"


class _SwitchProbe(str):
    """K12: a str that records every comparison and every attribute access made on it."""

    log: list = []

    def __eq__(self, o):
        _SwitchProbe.log.append(("==", o))
        return str.__eq__(self, o)

    def __ne__(self, o):
        _SwitchProbe.log.append(("!=", o))
        return str.__ne__(self, o)

    __hash__ = str.__hash__

    def __getattribute__(self, name):
        _SwitchProbe.log.append(("attr", name))
        return str.__getattribute__(self, name)


def row_k12(S):
    x = make_state(S.bs)
    yo = make_state(S.bs, order_bytes=ORDER_B)
    saved = dict(S.bs.__dict__)
    # every module global that IS os / os.environ / os.getenv (under any name) is served from the shim, AND the real
    # `os.environ.get` is shadowed for the row, so a function-local `import os` is served too.
    kinds = {n: ("os" if v is os else "environ" if v is os.environ else "getenv" if v is os.getenv else None)
             for n, v in saved.items()}
    bad = []
    try:
        for v in ("1", "on", "ON", "True", "y", "0", "", "1.0", "１"):
            env = {SWITCH: _SwitchProbe(v)}
            getenv = (lambda e: lambda k, d=None: e.get(k, d))(env)
            shim = types.SimpleNamespace(environ=env, getenv=getenv)
            for n, kind in kinds.items():
                if kind:
                    S.bs.__dict__[n] = {"os": shim, "environ": env, "getenv": getenv}[kind]
            os.environ.__dict__["get"] = getenv
            _SwitchProbe.log = []
            got = (x == yo)
            foreign = [e for e in _SwitchProbe.log if not (e[0] in ("==", "!=") and type(e[1]) is str and e[1] == "1")]
            if got != (v == "1"):
                bad.append(f"{v!r}: equal={got}")
            if foreign or not _SwitchProbe.log:
                bad.append(f"{v!r}: compared/used as {foreign or 'nothing (the value was never compared)'}")
    finally:
        os.environ.__dict__.pop("get", None)
        for n, kind in kinds.items():
            if kind:
                S.bs.__dict__[n] = saved[n]
    return not bad, f"the switch value is compared only with '1'; wrong: {bad or 'none'}"


def row_k13(S):
    seen = {}
    for env in ("1", None):
        with switch(env):
            w = World(S)
            w.emu.frame = 10
            a = w.gbs()
            w.emu.frame = 4                  # a reset / state load with no cache reset: frame < the entry's stamp
            w.mem.set_order(ORDER_B)
            f = w.gbs()
            s = w.gbs()
            seen[env] = (order(f).hex(), order(s).hex(), s is f, s is a)
    ok = (seen["1"] == (ORDER_B.hex(), ORDER_A.hex(), False, True)
          and seen[None] == (ORDER_B.hex(), ORDER_B.hex(), True, False))
    return ok, f"(first, second, second_is_first, second_is_old) fault={seen['1']} fix={seen[None]}"


def row_r1(S):
    m = re.search(r"^## B\.[^\n]*\n(.*?)(?=^## )", S.reg, re.S | re.M)
    sec = m.group(1) if m else ""
    hit = re.search(r"^\| `" + re.escape(SWITCH) + r"` \|", sec, re.M) is not None
    return hit, f"a §B table row whose first cell is exactly `{SWITCH}`: {hit}"


ROWS = [
    ("C0", row_c0), ("C1", row_c1), ("K1", row_k1), ("K2", row_k2),
    ("K3-fault", row_k3_fault), ("K3-fix", row_k3_fix), ("K4-fault", row_k4_fault), ("K4-fix", row_k4_fix),
    ("K5", row_k5), ("K6", row_k6), ("K6-fault", row_k6_fault), ("K6-fix", row_k6_fix),
    ("K7-fault", row_k7_fault), ("K7-fix", row_k7_fix), ("K8-fault", row_k8_fault), ("K8-fix", row_k8_fix),
    ("K9-runA", row_k9_runa), ("K9-fault", row_k9_fault), ("K9-fix", row_k9_fix),
    ("K10", row_k10), ("K11", row_k11), ("K12", row_k12), ("K13", row_k13), ("R1", row_r1),
]
NEW_ROWS = ("K10", "K11", "K12", "K13", "R1")


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
ORD = "self._battler_party_order != other._battler_party_order"
TRN = "self._current_turn != other._current_turn"
BOTH = f"{ORD} or {TRN}"
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
OS_FIRST = "import os\nfrom dataclasses"

FAULT_ROWS = {"K1", "K3-fault", "K4-fault", "K6-fault", "K7-fault", "K8-fault", "K9-fault"}
REVERT_RED = {"K2", "K3-fix", "K4-fix", "K6-fix", "K7-fix", "K8-fix", "K9-fix", "K10", "K12", "K13"}
NOSWITCH_RED = FAULT_ROWS | {"K7-fix", "K10", "K12", "K13"}


def _registry_row_deleted(reg: str) -> str:
    kept = [ln for ln in reg.split("\n") if not ln.startswith(f"| `{SWITCH}` |")]
    if len(kept) != len(reg.split("\n")) - 1:
        raise Unbuildable("the registry does not hold exactly one row for the switch")
    return "\n".join(kept) + f"\n\nRetired 2026-10-02: `{SWITCH}` was removed.\n"


def mutants(bs: str, sc: str, reg: str):
    """(name, builder, EXACT predicted red set). Builders raise Unbuildable when an anchor is not unique."""
    return [
        ("M0 the upstream mirror's battle_state.py, verbatim (the unfixed code)",
         lambda: Subject(MIRROR_BS.read_text(encoding="utf-8"), sc, reg), REVERT_RED),
        ("M1 revert to the mirror's __eq__ (the KI-108 `if` removed; its WHY comment left in place)",
         lambda: Subject(_sub(bs, IF_BLOCK, ""), sc, reg), REVERT_RED),
        ("M2 drop only the turn",
         lambda: Subject(_sub(bs, BOTH, ORD), sc, reg), {"K4-fix", "K6-fix", "K7-fix", "K10"}),
        ("M3 drop only the order",
         lambda: Subject(_sub(bs, BOTH, TRN), sc, reg),
         {"K2", "K3-fix", "K6-fix", "K7-fix", "K8-fix", "K9-fix", "K10", "K12", "K13"}),
        ("M4 ignore the switch (always the fix)",
         lambda: Subject(_sub(bs, GUARD, "True"), sc, reg), NOSWITCH_RED),
        ("M5 read the switch at IMPORT (loaded with the switch unset)",
         lambda: Subject(_sub(_sub(bs, GUARD, "not _KI108_OLDEQ"), TASKS_IMPORT,
                              TASKS_IMPORT + f'_KI108_OLDEQ = os.environ.get("{SWITCH}") == "1"\n'), sc, reg),
         NOSWITCH_RED),
        ("M6 get_battle_state returns the CACHE value, not the local",
         lambda: Subject(_sub(bs, STORE_RETURN, "    state_cache.battle_state = battle_state\n"
                                                "    return state_cache.battle_state.value\n"), sc, reg),
         {"K1", "K3-fault", "K4-fault", "K9-fault", "K10", "K13"}),
        ("M7 the cache setter ALWAYS stores (state_cache.py)",
         lambda: Subject(bs, _sub(sc, SETTER, "        if True:\n"), reg),
         {"K1", "K3-fault", "K3-fix", "K4-fault", "K8-fault", "K8-fix", "K9-fault", "K10", "K13"}),
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
          "K10", "K13"}),
        ("M11 the new object is never stored in the cache",
         lambda: Subject(_sub(bs, STORE_RETURN, "    return battle_state\n"), sc, reg),
         {"C0", "C1", "K1", "K2", "K3-fault", "K3-fix", "K4-fault", "K4-fix", "K5", "K8-fault", "K8-fix",
          "K9-runA", "K9-fault", "K9-fix", "K10", "K13"}),
        ("M12 __eq__ returns False (not NotImplemented) for a non-BattleState",
         lambda: Subject(_sub(bs, EQ_TAIL, EQ_TAIL.replace("return NotImplemented", "return False")), sc, reg),
         {"K6"}),
        ("M13 the switch's name removed from the registry",
         lambda: Subject(bs, sc, reg.replace(SWITCH, "REMOVED")), {"R1"}),
        # ---- the independent hunt's surviving families (its ids in brackets); each must die to a NEW row alone
        ("M14 [N01] order compared on byte 0 only",
         lambda: Subject(_sub(bs, ORD, "self._battler_party_order[0] != other._battler_party_order[0]"), sc, reg),
         {"K10"}),
        ("M15 [N06] order compared by byte SUM",
         lambda: Subject(_sub(bs, ORD, "sum(self._battler_party_order) != sum(other._battler_party_order)"), sc, reg),
         {"K10"}),
        ("M16 [N07] order compared as a byte SET",
         lambda: Subject(_sub(bs, ORD, "set(self._battler_party_order) != set(other._battler_party_order)"), sc, reg),
         {"K10"}),
        ("M17 [N08] order `<` (asymmetric: only an increase counts)",
         lambda: Subject(_sub(bs, ORD, "self._battler_party_order < other._battler_party_order"), sc, reg),
         {"K10"}),
        ("M18 [N09] turn `<` (asymmetric: only an increase counts)",
         lambda: Subject(_sub(bs, TRN, "self._current_turn < other._current_turn"), sc, reg), {"K10"}),
        ("M19 [N10] turn compared modulo 2",
         lambda: Subject(_sub(bs, TRN, "self._current_turn % 2 != other._current_turn % 2"), sc, reg), {"K10"}),
        ('M20 [N21] the switch restores on "1" OR "on"',
         lambda: Subject(_sub(bs, GUARD, f'os.environ.get("{SWITCH}") not in ("1", "on")'), sc, reg), {"K12"}),
        ("M21 [N30] upstream's compare drops _side_timers",
         lambda: Subject(_sub(bs, "\n                and self._side_timers == other._side_timers", ""), sc, reg),
         {"K11"}),
        ("M22 [N37] upstream's compare drops _weather",
         lambda: Subject(_sub(bs, "\n                and self._weather == other._weather", ""), sc, reg), {"K11"}),
        ("M23 [N38] _battler compared for battler 0 only ([:0x58])",
         lambda: Subject(_sub(bs, "and self._battler == other._battler\n",
                              "and self._battler[:0x58] == other._battler[:0x58]\n"), sc, reg), {"K11"}),
        ("M24 [N39] the FAULT arm drops _weather (the switch no longer restores upstream's exact compare)",
         lambda: Subject(_sub(bs, "                and self._weather == other._weather\n",
                              f'                and (self._weather == other._weather '
                              f'or os.environ.get("{SWITCH}") == "1")\n'), sc, reg), {"K11"}),
        ("M25 [N53] the backwards-frame branch returns 0 (state_cache.py: stale data trusted after a reset)",
         lambda: Subject(bs, _sub(sc, "            return 1000000\n", "            return 0\n"), reg), {"K13"}),
        ("M26 [W5a] the registry row's literal typo'd to a SUPERSTRING",
         lambda: Subject(bs, sc, _sub(reg, f"| `{SWITCH}` |", f"| `{SWITCH + 'X'}` |")), {"R1"}),
        ("M27 [W5b] the registry §B row deleted, a 'retired' mention left in prose",
         lambda: Subject(bs, sc, _registry_row_deleted(reg)), {"R1"}),
        # ---- EQUIVALENT refactors: each must redden NOTHING (a red here is a FALSE POSITIVE of the gate)
        ("E1 [WG] EQUIVALENT: the literal hoisted into a module constant",
         lambda: Subject(_sub(_sub(bs, OS_FIRST, f'import os\n_KI108_SWITCH = "{SWITCH}"\nfrom dataclasses'),
                              GUARD, 'os.environ.get(_KI108_SWITCH) != "1"'), sc, reg), set()),
        ("E2 [WH] EQUIVALENT: the early return on `age_in_frames < 1`",
         lambda: Subject(_sub(bs, "age_in_frames == 0:", "age_in_frames < 1:"), sc, reg), set()),
        ("E3 [N42] EQUIVALENT: the early return on `age_in_frames <= 0`",
         lambda: Subject(_sub(bs, "age_in_frames == 0:", "age_in_frames <= 0:"), sc, reg), set()),
        ("E4 [WI] EQUIVALENT: `from os import environ as _env` and `_env.get(...)`",
         lambda: Subject(_sub(_sub(bs, OS_FIRST, "import os\nfrom os import environ as _env\nfrom dataclasses"),
                              GUARD, f'_env.get("{SWITCH}") != "1"'), sc, reg), set()),
        ('E5 [WJ] EQUIVALENT: reversed operands `"1" != os.environ.get(...)`',
         lambda: Subject(_sub(bs, GUARD, f'"1" != os.environ.get("{SWITCH}")'), sc, reg), set()),
        ("E6 EQUIVALENT: `import os` moved from module level into __eq__",
         lambda: Subject(_sub(_sub(bs, OS_FIRST, "from dataclasses"), IF_BLOCK, "            import os\n" + IF_BLOCK),
                         sc, reg), set()),
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
        alone = {row: [n.split(" ")[0] for n, _, p in muts if p == {row}] for row in NEW_ROWS}
        check(all(alone.values()), f"LOAD-BEARING each of {', '.join(NEW_ROWS)} is the ONLY red row of some mutant: "
                                   f"{alone}")
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
          "restores upstream's 9-field compare per call, on exactly \"1\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
