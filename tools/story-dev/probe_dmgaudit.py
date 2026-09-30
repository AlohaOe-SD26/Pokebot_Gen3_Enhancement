"""GATE G-AUDIT — design v2 step 11 (M1b): `audit_damage_calc.py`, the PURE classifier and acceptance for the
`[DMGAUDIT]` raw reads (`ai-research-notes/2026-09-30-dmgcalc11-DESIGN.md` F4 [R:SR-2, SR-8]; the line contract
`2026-09-30-dmgcalc11-recon/m1_line_format.md`, v=1).

WHY. Production logs RAW reads only; every verdict is computed offline by the classifier, so the classifier is where a
wrong verdict would be born. Every row here EXECUTES the real classifier on SYNTHETIC `[DMGAUDIT]` lines built from
named fields (`mon_hex` packs a 0x58-byte `struct BattlePokemon`), and asserts the verdict the DESIGN names — never one
copied from the classifier's output. The defaults are real Step-0 values (Marcel's Manectric, f3190263: 83 -> 18,
Δ gBideDmg[1] 65; Hideo's Koffings for the trainer KO), and the T rows rebuild the 17-turn per-turn verdict table of
the PREDICTIONS from the committed Step-0 evidence file.

ROWS: I (instrument), P (pairing), S (samples), W (whitelist tiers), R (per-read strata, each at BEFORE ONLY (b) and at
AFTER ONLY (a)), Q (BEFORE-only strata), G (strata only the pair shows), C (self-check), X (acceptance), O (outputs),
PC (the independent port control: absence, the adapter's EXACT `dmgcalc_port.after_base` calls, inside/outside with the
real port, unreplayable records), T (the Step-0 table and its FAULT arm), and PIN (production: `modules/dmgaudit.py`
EXECUTED with its reads faked — (a) flag unset: zero reads, zero log lines; (b) flag set: zero get_battle_state()
calls, the category, the kinds, the FAULT switch, every line parses under this audit's v=1 parser — and AST pins on
the hook sites in `battle_action_selection.py` / `battle_handler.py` and on dmgaudit.py itself), and N (integrated
from the ADVERSARIAL MUTANT PASS of 2026-09-30, plus the rows for the live-found FAINT RESET (DESIGN F6 ⚠) and Hidden
Power's ROLLED type: the classifier's edges and the gate's OWN literal copy of F2's tiers (NR-*), production executed
with DISTINCT bytes in every RAW field and a valid EWRAM chain, a staged fixture for the prediction (NP-*), and two more
hook-file AST pins (NH-*)). Every world that runs production REBINDS `get_battle_state` wherever it is bound.
Then the mutants (CASES, PROD_CASES, PASS_CASES): each is an exec'd source edit (of the classifier, of dmgaudit.py, or a
text edit of a hook file; never written to disk) with the EXACT set of rows it must turn red, derived row by row and
written before that mutant's first run; they run in a process pool (in-process if none can be made), and a COVERAGE
check fails if any row is in no mutant's expected set. A row red WITHOUT any mutant (a production defect) is reported as
BASELINE RED, fails the gate, and is left out of every mutant's comparison (so one defect does not hide the others).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 -u probe_dmgaudit.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import pathlib
import re
import struct
import sys
import tempfile
import time
import types
from functools import lru_cache

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(HERE))
A_PATH = HERE / "audit_damage_calc.py"
A_NAME = "audit_damage_calc"
import audit_damage_calc  # noqa: E402,F401

# production (the PIN rows): the module executed, the two hook files read as text (AST only)
import modules.battle_state  # noqa: E402
import modules.battle_strategies._util  # noqa: E402,F401  (the calculator `_prediction` runs)
import modules.context  # noqa: E402  (its `context.emulator` is faked for the Flash Fire EWRAM chain)
import modules.debug_logger  # noqa: E402
import modules.dmgaudit  # noqa: E402,F401  (always read via sys.modules: a mutant is exec'd there)
import modules.memory  # noqa: E402
from modules.battle_state import BattleState  # noqa: E402

D_NAME = "modules.dmgaudit"
D_PATH = SANDBOX / "modules" / "dmgaudit.py"
BAS_PATH = SANDBOX / "modules" / "battle_action_selection.py"
BH_PATH = SANDBOX / "modules" / "battle_handler.py"
FLAG, FAULT = "POKEBOT_R25_DMGAUDIT", "POKEBOT_R25_FAULT_DMGAUDIT_BIDE0"

STEP0 = HERE / "evidence" / "2026-09-30-dmgcalc11-STEP0.txt"
DEBUG_LOGGER = REPO / "sandbox-pokebot" / "modules" / "debug_logger.py"
with open(REPO / "sandbox-pokebot" / "modules" / "data" / "moves.json", encoding="utf-8") as _fh:
    MOVES = json.load(_fh)                      # the GATE's own copy: the builders never read the module under test

FAILURES: list[str] = []
ACC, EXC, NAS, REJ, UNP, SUP = "ACCEPTED", "EXCLUDED", "NOT-A-SAMPLE", "REJECTED", "UNPAIRED", "SUPERSEDED"


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


ROW_NAMES: set = set()                                  # every row's ID (for the coverage check)


def row(label, fn, tag, reds):
    ROW_NAMES.add(label.split()[0])
    try:
        ok, detail = fn()
    except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
        ok, detail = False, f"raised {type(error).__name__}: {error}"
    if not ok:
        reds.append(label.split()[0])
    if not tag:
        check(label, ok, detail)


def A():
    return sys.modules[A_NAME]


# ======================================================================================================== builders
def mon_hex(m: dict) -> str:
    """A 0x58-byte `struct BattlePokemon` from named fields (offsets: m1_line_format.md)."""
    raw = bytearray(0x58)
    struct.pack_into("<6H", raw, 0x00, m["species"], m["atk"], m["def_"], m["spe"], m["spa"], m["spd"])
    struct.pack_into("<4H", raw, 0x0C, *m["moves"])
    struct.pack_into("<I", raw, 0x14, m["ivs"])
    raw[0x18:0x20] = bytes(m["stages"])
    raw[0x20], raw[0x21], raw[0x22] = m["ability"], m["type1"], m["type2"]
    raw[0x24:0x28] = bytes(m["pp"])
    struct.pack_into("<H", raw, 0x28, m["hp"])
    raw[0x2A] = m["level"]
    struct.pack_into("<HH", raw, 0x2C, m["maxhp"], m["item"])
    struct.pack_into("<III", raw, 0x48, m["pid"], m["status1"], m["status2"])
    return raw.hex()


def csv(xs) -> str:
    return ",".join(str(x) for x in xs)


def _raw_fields(s: dict) -> str:
    ff = "null" if s["ff"] is None else csv(s["ff"])
    return (f"t={s['t']} out={s['out']} flags={s['flags']:08x} act={csv(s['act'])} mv={csv(s['mv'])} "
            f"bide={csv(s['bide'])} weather={s['weather']} side={csv(s['side'])} s3={s['s3'][0]:08x},{s['s3'][1]:08x} "
            f"dis={'0' * 56},{'0' * 56} mons={mon_hex(s['me'])},{mon_hex(s['foe'])} ff={ff}")


def before_line(frame: int, s: dict) -> str:
    """Field order as the contract gives it: the RAW fields, badges, pred, base, eff (base is `none` with no pred)."""
    pred = s["pred"] if isinstance(s["pred"], str) else csv(s["pred"])
    base = s.get("base")
    base = "none" if base is None or isinstance(s["pred"], str) else csv(base)
    eff = s.get("eff") or (MOVES[s["mv"][0]]["effect"] if s["mv"][0] else "-")
    return f"f{frame} [DMGAUDIT] BEFORE v=1 {_raw_fields(s)} badges={s['badges']} pred={pred} base={base} eff={eff}"


def after_line(frame: int, s: dict) -> str:
    party = ",".join(f"{pid:08x}:{hp}" for pid, hp in s["party"])
    return f"f{frame} [DMGAUDIT] AFTER v=1 kind={s['kind']} {_raw_fields(s)} party={party}"


def ctl(frame: int) -> str:
    return f"f{frame} [DMGAUDIT] CTL v=1"


ZERO6 = ((0, 0),) * 6
#: Marcel's Manectric turn (Step-0 f3190263): our Mightyena's Take Down (36, RECOIL, Tier A), the foe's Howl
ME = dict(species=287, atk=70, def_=62, spe=71, spa=50, spd=52, moves=(33, 269, 36, 44), ivs=0, stages=(6,) * 8,
          ability=22, type1=17, type2=17, pp=(35, 20, 18, 23), hp=89, level=31, maxhp=127, item=0, pid=0x5C96EA9B,
          status1=0, status2=0)
FOE = dict(species=338, atk=60, def_=45, spe=80, spa=65, spd=45, moves=(336, 98, 209, 316), ivs=0, stages=(6,) * 8,
           ability=9, type1=13, type2=13, pp=(40, 30, 20, 40), hp=83, level=26, maxhp=83, item=0, pid=0x000B7088,
           status1=0, status2=0)
BASE_B = dict(t=0, out=0, flags=0xC, act=(0, 0, 255, 255), mv=(36, 336, 0, 0), bide=(27201, 67667, 297, 3722),
              weather=0, side=(0, 0), s3=(0, 0), me=ME, foe=FOE, ff=(0, 0), badges=0x3F, pred=(56, 66, 112, 132),
              base=(40, 44), eff=None)
PRED = BASE_B["pred"]


def merge(base: dict, over: dict | None) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = {**out[k], **v} if k in ("me", "foe") and isinstance(v, dict) else v
    return out


def mv_setup(move: int, slot_pp: int = 20, foe_move: int = 336) -> dict:
    """Our chosen move `move` in slot 0 of our moveset."""
    return {"mv": (move, foe_move, 0, 0), "me": {"moves": (move, 269, 36, 44), "pp": (slot_pp, 20, 18, 23)}}


def pair(b=None, a=None, *, obs=65, d0=16, kind="entry", frame=3190263, used=True, setup=None) -> list[str]:
    """[BEFORE, AFTER] of one turn. AFTER is DERIVED from BEFORE as the game would leave it (counter +1 at an entry,
    kept at a battle end with outcome 1; Δ gBideDmg = (d0, obs); our chosen move's PP -1 by move id when `used`; HP
    down by the damage), then `a` overrides it."""
    B = merge(merge(BASE_B, setup), b)
    me, foe = dict(B["me"]), dict(B["foe"])
    me["hp"] = max(0, me["hp"] - d0)
    if used and B["mv"][0] in me["moves"]:
        i = me["moves"].index(B["mv"][0])
        me["pp"] = tuple(p - 1 if j == i else p for j, p in enumerate(me["pp"]))
    foe["hp"] = max(0, min(foe["maxhp"], foe["hp"] - obs))
    end = kind == "end"
    derived = dict(t=B["t"] if end else B["t"] + 1, out=1 if end else 0, flags=B["flags"],
                   act=B["act"] if end else (255,) * 4, mv=B["mv"] if end else (0,) * 4,
                   bide=(B["bide"][0] + d0, B["bide"][1] + obs, B["bide"][2], B["bide"][3]),
                   weather=B["weather"], side=B["side"], s3=B["s3"], me=me, foe=foe,
                   ff=None if end else (0, 0) if B["ff"] is None else B["ff"], kind=kind,
                   party=((foe["pid"], foe["hp"]), (0x00157F88, 94)) + ZERO6[:4])
    return [before_line(frame, B), after_line(frame + 700, merge(derived, a))]


#: Hideo's Koffings (Step-0 f3173282): #1 (55 HP) KO'd by our Bite and replaced by #2 — the SAME species, a new PID
KOFF1 = dict(FOE, species=109, moves=(33, 120, 124, 108), pp=(35, 5, 20, 20), hp=55, maxhp=55, pid=0x00092588,
             ability=26, type1=3, type2=3)
KOFF2 = dict(KOFF1, moves=(33, 139, 124, 108), pp=(35, 40, 20, 20), pid=0x00124A88)


def tko(b=None, a=None, *, obs=90, our_move=44, foe_move=33, **kw) -> list[str]:
    setup = {"foe": KOFF1, "mv": (our_move, foe_move, 0, 0),
             "me": {"moves": (33, 269, 36, 44) if our_move in (33, 269, 36, 44) else (our_move, 269, 36, 44),
                    "pp": (35, 20, 20, 25)}, "pred": (70, 83, 140, 166)}
    a0 = {"foe": KOFF2, "party": ((KOFF1["pid"], 0), (KOFF2["pid"], 55)) + ZERO6[:4]}
    return pair(b, merge(a0, a), obs=obs, setup=setup, **kw)


CLEAN = pair()


def audit(lines, margin=None):
    mod = A()
    return mod.audit_text("\n".join(lines), mod.ACCEPT_MARGIN if margin is None else margin)


def one(lines, margin=None):
    rep = audit(lines, margin)
    vs = rep.verdicts
    if len(vs) != 1:
        raise AssertionError(f"want 1 verdict, got {len(vs)}")
    return vs[0], rep


def at(rep, frame):
    return next(v for v in rep.verdicts if v.before.frame == frame)


def vtxt(v) -> str:
    return f"{v.status} kind={v.kind!r} reasons={list(v.reasons)} tags={list(v.tags)} sc={v.selfcheck!r} d={v.d_bide}"


def excluded_with(lines, reason):
    v, _ = one(lines)
    return v.status == EXC and reason in v.reasons, vtxt(v)


# ======================================================================================================== I rows
def i_rows(tag=""):
    reds: list = []

    def i1():
        rep = audit([ctl(3189301)] + CLEAN)
        lines = A().render(rep)
        return (rep.raw_count == 3 and rep.parsed_count == 3 and rep.instrument_ok and rep.exit_code == 2
                and "  INSTRUMENT: OK" in lines), f"raw {rep.raw_count} parsed {rep.parsed_count} exit {rep.exit_code}"

    def i2():
        b, a = CLEAN
        bad = [re.sub(r"( mons=[0-9a-f]{174})[0-9a-f]{2},", r"\1,", b),              # a truncated hex field
               "f5 [DMGAUDIT] BOGUS v=1",                                          # an unknown kind
               "f5 [DMGAUDIT] CTL v=2",                                            # another contract version
               a.rsplit(" party=", 1)[0],                                          # a missing field
               "fNone [DMGAUDIT] CTL v=1",                                         # an unread frame
               b + " x=1",                                                         # a field outside the contract
               b.replace(" base=40,44", "", 1)]                                    # a BEFORE without base=
        got = []
        for extra in bad:
            rep = audit([ctl(3189301)] + CLEAN + [extra])
            got.append((rep.raw_count, rep.parsed_count, rep.exit_code,
                        any(ln.startswith("  INSTRUMENT: FAIL") for ln in A().render(rep))))
        return all(g == (4, 3, 3, True) for g in got), str(got)

    def i3():
        rep = audit([ctl(3189301)] + CLEAN + ["... (event log size cap reached — only STUCK dumps from here) ..."])
        lines = A().render(rep)
        return (rep.capped and rep.exit_code == 3 and any("30 MB cap" in ln for ln in lines)
                and rep.raw_count == rep.parsed_count == 3), f"capped {rep.capped} exit {rep.exit_code}"

    def i4():
        return A().CAP_MARKER in DEBUG_LOGGER.read_text(encoding="utf-8"), repr(A().CAP_MARKER)

    def i5():
        text = "\n".join([ctl(3189301)] + pair(obs=136, b={"foe": {"hp": 200, "maxhp": 200}})) + "\n"
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "debug.log"
            p.write_text(text, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                c3 = A().main([str(p)])
                c4 = A().main([str(p), "--margin", "4"])
        return c3 == 1 and c4 == 2 and "ACCEPTANCE: FAIL" in out.getvalue(), f"margin 3 -> {c3}, margin 4 -> {c4}"

    def i6():
        rep = audit([ctl(3189301), "f3189400 [DMGAUDIT] ERR v=1 where=before err=KeyError"] + CLEAN)
        return (rep.raw_count == rep.parsed_count == 4 and len(rep.errs) == 1
                and any(ln.startswith("  ERR lines: 1") for ln in A().render(rep))), f"errs {len(rep.errs)}"

    for label, fn in (("I1 CTL + a clean pair: raw 3 == parsed 3, INSTRUMENT OK, exit 2 (INSUFFICIENT)", i1),
                      ("I2 a malformed [DMGAUDIT] line (7 shapes, one a BEFORE without base=) counts raw, not parsed: "
                       "INSTRUMENT FAIL, exit 3", i2),
                      ("I3 the logger's 30 MB cap marker: INSTRUMENT FAIL, exit 3", i3),
                      ("I4 CAP_MARKER is the text debug_logger.py writes at its cap", i4),
                      ("I5 the CLI: one over-bound hit exits 1 at the default margin, 2 (n=1) at --margin 4", i5),
                      ("I6 an ERR line parses and is reported", i6)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== P rows
def p_rows(tag=""):
    reds: list = []
    END = {"t": 3}

    def p1():
        v, _ = one(pair(END, obs=90, kind="end"))
        return v.status == ACC and v.kind == "KO" and v.selfcheck == "n/a: battle end", vtxt(v)

    def p2():
        v, _ = one(pair(END, {"out": 0}, obs=90, kind="end"))
        return v.status == REJ and v.reasons == ("end-without-outcome",), vtxt(v)

    def p3():
        v, _ = one(pair(END, {"t": 4}, obs=90, kind="end"))
        return v.status == REJ and v.reasons == ("end-turn-moved",), vtxt(v)

    def p4():
        v, _ = one(tko())
        return v.status == ACC and v.kind == "trainer KO" and v.selfcheck == "n/a: foe changed", vtxt(v)

    def p5():   # a switch: the old mon is alive in the party and our hit did not reach its HP
        v, _ = one(tko(obs=30, a={"party": ((KOFF1["pid"], 55), (KOFF2["pid"], 55)) + ZERO6[:4]}))
        return v.status == REJ and v.reasons == ("foe-changed-not-ko",), vtxt(v)

    def p6():
        v, _ = one(tko(a={"party": ((KOFF1["pid"], 3), (KOFF2["pid"], 55)) + ZERO6[:4]}))
        return v.status == REJ and v.reasons == ("foe-changed-old-hp-not-0",), vtxt(v)

    def p7():
        v, _ = one(tko({"side": (0, 0x10)}))
        return v.status == REJ and v.reasons == ("foe-changed-spikes",), vtxt(v)

    def p7a():
        v, _ = one(tko(a={"side": (0, 0x10)}))
        return v.status == REJ and v.reasons == ("foe-changed-spikes",), vtxt(v)

    def p8():
        v, _ = one(pair(a={"t": 2}))
        return v.status == REJ and v.reasons == ("turn-gap",), vtxt(v)

    def p9():
        first = pair({"bide": (27201, 67600, 297, 3722)}, frame=100)[0]
        second = before_line(200, merge(BASE_B, {}))
        rep = audit([first, second, CLEAN[1]])
        v1, v2 = at(rep, 100), at(rep, 200)
        return (v1.status == SUP and v2.status == ACC and v2.d_bide == 65), f"{vtxt(v1)} || {vtxt(v2)}"

    def p10():
        rep = audit([CLEAN[0], ctl(3190500), CLEAN[1]])
        v = rep.verdicts[0]
        return (len(rep.verdicts) == 1 and v.status == UNP and v.reasons == ("no-after-before-ctl",)
                and len(rep.orphans) == 1), f"{vtxt(v)} orphans {len(rep.orphans)}"

    def p11():
        rep = audit([CLEAN[0]])
        v = rep.verdicts[0]
        return len(rep.verdicts) == 1 and v.status == UNP and v.reasons == ("no-after-at-log-end",), vtxt(v)

    for label, fn in (("P1 the battle-end pair (counter still T, outcome 1): ACCEPTED 'KO'", p1),
                      ("P2 a battle-end read with outcome 0: REJECTED end-without-outcome", p2),
                      ("P3 a battle-end read with the counter moved: REJECTED end-turn-moved", p3),
                      ("P4 the trainer-KO pair (Koffing -> Koffing, a new PID): ACCEPTED 'trainer KO'", p4),
                      ("P5 a changed foe with Δbide < its HP (a switch): REJECTED foe-changed-not-ko", p5),
                      ("P6 a changed foe whose old PID's party HP is not 0: REJECTED foe-changed-old-hp-not-0", p6),
                      ("P7 a trainer KO with Spikes on the foe's side at BEFORE: REJECTED foe-changed-spikes", p7),
                      ("P7a the same with Spikes at AFTER only", p7a),
                      ("P8 a turn gap (the entry read at T+2): REJECTED turn-gap", p8),
                      ("P9 a double BEFORE: the latest wins, the first is SUPERSEDED", p9),
                      ("P10 a CTL clears a pending BEFORE (UNPAIRED); the next AFTER is an orphan", p10),
                      ("P11 a BEFORE at the log's end is UNPAIRED", p11)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== S rows
def s_rows(tag=""):
    reds: list = []

    def s1():
        v, _ = one(CLEAN)
        return (v.status == ACC and v.kind == "turn" and v.battle == "trainer" and v.tier == "A"
                and v.effect == "RECOIL" and v.d_bide == 65 and v.tags == () and v.selfcheck == "agree"), vtxt(v)

    def s2():   # asleep: our chosen move's PP unchanged, nothing dealt
        v, _ = one(pair(used=False, obs=0))
        return v.status == NAS and v.reasons == ("our-pp-unchanged",), vtxt(v)

    def s3():   # Encore: slot 0 (Tackle) spent PP, the CHOSEN Take Down (slot 2) did not
        v, _ = one(pair(a={"me": {"pp": (34, 20, 18, 23)}}, used=False))
        return v.status == NAS and v.reasons == ("our-pp-unchanged",), vtxt(v)

    def s4():   # the same species with a new PID
        v, _ = one(pair(a={"me": {"pid": 0x11111111}}))
        return v.status == REJ and v.reasons == ("our-identity-changed",), vtxt(v)

    def s5():
        a_ = one(pair({"act": (1, 0, 255, 255), "mv": (0, 336, 0, 0)}, used=False))[0]
        b_ = one(pair({"mv": (0, 336, 0, 0)}, used=False))[0]
        return all(v.status == NAS and v.reasons == ("our-action-not-a-move",) for v in (a_, b_)), \
            f"{vtxt(a_)} || {vtxt(b_)}"

    def s6():
        v, _ = one(pair({"mv": (165, 336, 0, 0)}, used=False))
        return v.status == NAS and v.reasons == ("our-move-not-in-moveset",), vtxt(v)

    def s7():
        v, _ = one(pair(obs=-40, a={"foe": {"hp": 83}}))
        return v.status == EXC and "instrument-fault" in v.reasons and "no-damage" not in v.reasons, vtxt(v)

    def s8():
        v, _ = one(pair(obs=0))
        return v.status == EXC and v.reasons == ("no-damage",), vtxt(v)

    def s9():
        v, _ = one(pair({"flags": 0x800D}))
        return v.status == EXC and "doubles" in v.reasons, vtxt(v)

    def s10():
        v, _ = one(pair({"pred": (0, 0, 0, 0)}))
        return v.status == EXC and v.reasons == ("predicted-immune",), vtxt(v)

    def s11():
        a_ = one(pair({"pred": "none"}))[0]
        b_ = one(pair({"pred": "err:KeyError"}))[0]
        return all(v.status == EXC and v.reasons == ("no-prediction",) for v in (a_, b_)), f"{vtxt(a_)} || {vtxt(b_)}"

    def s12():
        big = {"foe": {"hp": 200, "maxhp": 200}}
        rep = audit(pair(big, obs=66, frame=10) + pair(big, obs=67, frame=20) + pair(big, obs=133, frame=30))
        t = [at(rep, f).tags for f in (10, 20, 30)]
        return t == [(), ("crit-or-under-prediction (ambiguous)",), ("over-crit_max+1",)], str(t)

    def s13():
        v, rep = one(pair(obs=55))
        v = at(rep, 3190263)
        return v.status == ACC and v.tags == ("below-noncrit-min",), vtxt(v)

    def s14():
        v, _ = one(pair({"flags": 0x4}))
        return v.status == ACC and v.battle == "wild", vtxt(v)

    for label, fn in (("S1 a clean hit: ACCEPTED turn, trainer, tier A, untagged, self-check agrees", s1),
                      ("S2 our chosen move's PP unchanged: NOT-A-SAMPLE our-pp-unchanged", s2),
                      ("S3 the chosen move != the slot whose PP dropped (matched by move id): NOT-A-SAMPLE", s3),
                      ("S4 our PID changed (same species): REJECTED our-identity-changed", s4),
                      ("S5 our action not a move (an item; or move 0): NOT-A-SAMPLE", s5),
                      ("S6 the chosen move is not in our moveset (Struggle): NOT-A-SAMPLE", s6),
                      ("S7 a negative Δbide: EXCLUDED instrument-fault (not no-damage)", s7),
                      ("S8 Δbide 0 with PP spent: EXCLUDED no-damage", s8),
                      ("S9 doubles (flags bit 0x1): EXCLUDED doubles", s9),
                      ("S10 max == 0: EXCLUDED predicted-immune", s10),
                      ("S11 pred=none / pred=err: EXCLUDED no-prediction", s11),
                      ("S12 crit ambiguity: obs=max untagged, max+1 ambiguous, crit_max+1 over", s12),
                      ("S13 a hit below the non-crit min is ACCEPTED and tagged", s13),
                      ("S14 wild vs trainer: flags 0x4 reads 'wild'", s14)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== W rows
STAT_HIT = re.compile(r"_(UP|DOWN)_HIT$")


def w_rows(tag=""):
    reds: list = []

    def w1():
        t = A().tier_of
        got = {name: t(i, MOVES[i]["effect"]) for name, i in (("Tackle", 33), ("Take Down", 36), ("Struggle", 165),
                                                               ("Surf", 57), ("Ember", 52), ("Facade", 263),
                                                               ("Twister", 239), ("Fury Attack", 31),
                                                               ("Selfdestruct", 120), ("Metal Claw", 232))}
        want = {"Tackle": "A", "Take Down": "A", "Struggle": "OUT", "Surf": "C", "Ember": "B", "Facade": "C",
                "Twister": "C", "Fury Attack": "OUT", "Selfdestruct": "OUT", "Metal Claw": "A"}
        return got == want, str({k: v for k, v in got.items() if want[k] != v})

    def w2():
        m = A()
        effects = {x["effect"] for x in MOVES}
        tiers = (m.TIER_A, m.TIER_B, m.TIER_C)
        missing = sorted((m.TIER_A | m.TIER_B | m.TIER_C) - effects)
        overlap = (m.TIER_A & m.TIER_B) | (m.TIER_A & m.TIER_C) | (m.TIER_B & m.TIER_C)
        stat_hits = sorted(e for e in effects if STAT_HIT.search(e) and e not in m.TIER_A)
        return (not missing and not overlap and not stat_hits and all(tiers)), \
            f"missing {missing} overlap {sorted(overlap)} stat *_HIT outside A {stat_hits}"

    def w3():
        rep = audit(pair(setup=mv_setup(31), frame=10) + pair(setup=mv_setup(52), frame=20)
                    + pair(setup=mv_setup(57), frame=30))
        f, e, s = at(rep, 10), at(rep, 20), at(rep, 30)
        return (f.status == EXC and f.reasons == ("outside-whitelist",) and e.status == ACC and e.tier == "B"
                and s.status == ACC and s.tier == "C"), f"{vtxt(f)} || {vtxt(e)} {e.tier} || {vtxt(s)} {s.tier}"

    for label, fn in (("W1 tier_of: Surf C and Struggle OUT by INDEX; the rest by effect", w1),
                      ("W2 the whitelist names exist in moves.json, are disjoint, and hold every stat *_HIT", w2),
                      ("W3 samples by tier: Fury Attack EXCLUDED outside-whitelist; Ember B and Surf C ACCEPTED", w3)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== R rows
#: (id, reason, our-move setup or None, the condition) — the per-read strata; each row runs twice: the condition at
#: BEFORE ONLY (b: AFTER reset to the neutral value) and at AFTER ONLY (a)
R_CASES = (
    ("R01", "foe-status", None, {"foe": {"status1": 0x8}}),
    ("R02", "foe-confused", None, {"foe": {"status2": 0x1}}),
    ("R03", "foe-trapped", None, {"foe": {"status2": 0x2000}}),
    ("R04", "foe-leech-seed", None, {"s3": (0, 0x4)}),
    ("R05", "foe-cursed", None, {"foe": {"status2": 0x10000000}}),
    ("R06", "foe-nightmare", None, {"foe": {"status2": 0x8000000}}),
    ("R07", "foe-substitute", None, {"foe": {"status2": 0x1000000}}),
    ("R08", "foe-focus-band", None, {"foe": {"item": 196}}),
    ("R09", "foe-held-item", None, {"foe": {"item": 139}}),
    ("R10", "C:surf-underwater", 57, {"s3": (0, 0x40000)}),
    ("R11", "C:earthquake-underground", 89, {"s3": (0, 0x80)}),
    ("R12", "C:gust-in-the-air", 16, {"s3": (0, 0x40)}),
    ("R13", "C:minimized", 23, {"s3": (0, 0x100)}),
    ("R14", "C:smellingsalt-paralysis", 265, {"foe": {"status1": 0x40}}),
    ("R15", "C:facade-status", 263, {"me": {"status1": 0x40}}),
    ("R16", "C:weather-ball-weather", 311, {"weather": 1}),
    ("R17", "C:brick-break-screens", 280, {"side": (0, 1)}),
    ("R18", "C:sport", 52, {"s3": (0x20000, 0)}),
    ("R19", "our-pinch", 52, {"me": {"hp": 40}}),
    ("R20", "our-flash-fire", None, {"ff": (1, 0)}),
    ("R21", "our-rough-skin", None, {"me": {"ability": 24}}),
)


def _neutral(state: dict, cond: dict) -> dict:
    return {k: ({kk: state[k][kk] for kk in v} if isinstance(v, dict) else state[k]) for k, v in cond.items()}


def r_lines(move, cond, where):
    setup = mv_setup(move) if move else {}
    if move == 52 and "me" in cond:                     # R19: Blaze with a Fire move
        setup = merge(setup, {"me": {"ability": 66}})
    base = merge(merge(BASE_B, setup), {})
    if where == "b":
        return pair(cond, _neutral(base, cond), setup=setup)
    return pair(None, cond, setup=setup)


def r_rows(tag=""):
    reds: list = []
    for rid, reason, move, cond in R_CASES:
        for where, what in (("b", "BEFORE only"), ("a", "AFTER only")):
            row(f"{rid}{where} {reason} at {what}: EXCLUDED with that reason",
                lambda m=move, c=cond, w=where, r=reason: excluded_with(r_lines(m, c, w), r), tag, reds)
    return reds


# ======================================================================================================== Q rows
def q_rows(tag=""):
    reds: list = []

    def has(lines_list, reason):
        vs = [one(x)[0] for x in lines_list]
        return all(v.status == EXC and reason in v.reasons for v in vs), " || ".join(vtxt(v) for v in vs)

    def q04():
        ghost = one(pair({"mv": (36, 174, 0, 0), "foe": {"type1": 7}}))[0]
        normal = one(pair({"mv": (36, 174, 0, 0)}))[0]
        return (ghost.status == EXC and "foe-self-hurt-move" in ghost.reasons and normal.status == ACC), \
            f"{vtxt(ghost)} || {vtxt(normal)}"

    def q07():
        low = one(pair(setup=mv_setup(206)))[0]                                        # 83 <= crit_max 132
        high = one(pair({"foe": {"hp": 200, "maxhp": 200}}, setup=mv_setup(206)))[0]   # 200 > 132
        return (low.status == EXC and "C:false-swipe-hp" in low.reasons and high.status == ACC), \
            f"{vtxt(low)} || {vtxt(high)}"

    cases = (
        ("Q01 the foe's action is an item: foe-item-action",
         lambda: has([pair({"act": (0, 1, 255, 255), "mv": (36, 0, 0, 0)})], "foe-item-action")),
        ("Q02 the foe's chosen move reads 0 (Struggle / a lock): foe-move-zero",
         lambda: has([pair({"mv": (36, 0, 0, 0)})], "foe-move-zero")),
        ("Q03 the foe's chosen move hurts itself (Selfdestruct, Take Down, Substitute): foe-self-hurt-move",
         lambda: has([pair({"mv": (36, m, 0, 0)}) for m in (120, 36, 164)], "foe-self-hurt-move")),
        ("Q04 Curse by a Ghost-type foe hurts itself; by a non-Ghost it does not", q04),
        ("Q05 the foe's Protect / Endure / Bide: foe-protect-endure-bide",
         lambda: has([pair({"mv": (36, m, 0, 0)}) for m in (182, 203, 117)], "foe-protect-endure-bide")),
        ("Q06 our Pursuit vs a switching foe: C:pursuit-switch",
         lambda: has([pair({"act": (0, 2, 255, 255)}, setup=mv_setup(228, foe_move=0))], "C:pursuit-switch")),
        ("Q07 False Swipe with the foe's HP before <= crit_max: C:false-swipe-hp (above it: ACCEPTED)", q07),
        ("Q08 PERSISTENT Guts + burn at BEFORE",
         lambda: has([pair({"me": {"ability": 62, "status1": 0x10}})], "persistent:guts-burn")),
        ("Q09 PERSISTENT Marvel Scale + a status, on the foe and on us",
         lambda: has([pair({"foe": {"ability": 63, "status1": 0x8}}), pair({"me": {"ability": 63, "status1": 0x8}})],
                     "persistent:marvel-scale")),
        ("Q10 PERSISTENT Cloud Nine (foe) / Air Lock (ours)",
         lambda: has([pair({"foe": {"ability": 13}}), pair({"me": {"ability": 77}})],
                     "persistent:cloud-nine-air-lock")),
        ("Q11 PERSISTENT Flash Fire set at BEFORE",
         lambda: has([pair({"ff": (1, 0)}, {"ff": (0, 0)})], "persistent:flash-fire")),
    )
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== G rows
def g_rows(tag=""):
    reds: list = []

    def has(lines_list, reason):
        vs = [one(x)[0] for x in lines_list]
        return all(v.status == EXC and reason in v.reasons for v in vs), " || ".join(vtxt(v) for v in vs)

    def g05():
        guts = one(pair({"me": {"ability": 62}}, {"me": {"status1": 0x40}}))[0]
        plain = one(pair(None, {"me": {"status1": 0x40}}))[0]
        return (guts.status == EXC and "our-status-changed-guts-facade" in guts.reasons and plain.status == ACC), \
            f"{vtxt(guts)} || {vtxt(plain)}"

    def g07():  # the dip: 60 - 30 = 30 <= 127 // 3 = 42, though both reads show 60 (drained back up)
        v = one(pair({"me": {"ability": 66, "hp": 60}}, {"me": {"hp": 60}}, d0=30, setup=mv_setup(52)))[0]
        return v.status == EXC and v.reasons == ("our-pinch",), vtxt(v)

    def g11():  # the replacement's own status and item say nothing about our hit
        v = one(tko(a={"foe": {"status1": 0x8, "item": 139}}))[0]
        return v.status == ACC and v.kind == "trainer KO", vtxt(v)

    cases = (
        ("G01 the foe's Def or SpD stage changed: foe-def-stage-changed",
         lambda: has([pair(a={"foe": {"stages": (6, 6, 7, 6, 6, 6, 6, 6)}}),
                      pair(a={"foe": {"stages": (6, 6, 6, 6, 6, 5, 6, 6)}})], "foe-def-stage-changed")),
        ("G02 the foe's types changed (Conversion): foe-profile-changed",
         lambda: has([pair(a={"foe": {"type1": 11, "type2": 11}})], "foe-profile-changed")),
        ("G03 the foe side's screens changed: foe-screens-changed",
         lambda: has([pair(a={"side": (0, 2)})], "foe-screens-changed")),
        ("G04 our Atk or SpA stage changed: our-attack-stage-changed",
         lambda: has([pair(a={"me": {"stages": (6, 5, 6, 6, 6, 6, 6, 6)}}),
                      pair(a={"me": {"stages": (6, 6, 6, 6, 7, 6, 6, 6)}})], "our-attack-stage-changed")),
        ("G05 a status change with Guts: our-status-changed-guts-facade (without Guts: ACCEPTED)", g05),
        ("G06 the weather changed: weather-changed", lambda: has([pair(a={"weather": 8})], "weather-changed")),
        ("G07 our HP dipped to <= max/3 mid-turn (HP before - Δbide[0]) with Blaze + a Fire move: our-pinch", g07),
        ("G08 our Liquid Ooze vs a draining foe (Absorb; Leech Seed on us): our-liquid-ooze",
         lambda: has([pair({"me": {"ability": 64}, "mv": (36, 71, 0, 0)}),
                      pair({"me": {"ability": 64}}, {"s3": (0x4, 0)})], "our-liquid-ooze")),
        ("G09 a trainer KO by a Tier B move (Ember): foe-after-unobservable",
         lambda: has([tko(our_move=52)], "foe-after-unobservable")),
        ("G10 a trainer KO after the foe's Harden: foe-after-unobservable",
         lambda: has([tko(foe_move=106)], "foe-after-unobservable")),
        ("G11 a trainer KO: the REPLACEMENT's status and item are not judged (ACCEPTED)", g11),
        ("G12 Tier B (Ember) whose secondary shows at AFTER (foe burned): EXCLUDED foe-status",
         lambda: has([pair(a={"foe": {"status1": 0x10}}, setup=mv_setup(52))], "foe-status")),
    )
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== C rows
def c_rows(tag=""):
    reds: list = []

    def c1():
        v, rep = one(pair(a={"foe": {"hp": 23}}))
        dis = [x.before.frame for x in rep.selfcheck_disagreements]
        return (v.selfcheck == "DISAGREE" and dis == [3190263]
                and any("disagreements 1:" in ln for ln in A().render(rep))), f"{vtxt(v)} {dis}"

    def c2():   # Step-0 f3191078: 18 -> 18 while our hit dealt 65 (the foe's Hyper Potion)
        v, rep = one(pair({"act": (0, 1, 255, 255), "mv": (36, 0, 0, 0), "foe": {"hp": 18}}, {"foe": {"hp": 18}}))
        return v.selfcheck == "n/a: foe item action" and rep.selfcheck_disagreements == [], vtxt(v)

    def c3():   # every exclusion on a turn whose HP difference DISAGREES with Δbide (so a missed one would show)
        mis = {"foe": {"hp": 30}}
        cases = {
            "n/a: foe held item": pair({"foe": {"item": 139}}, mis),
            "n/a: leech seed on us": pair({"s3": (0x4, 0)}, mis),
            "n/a: foe drain or heal move": pair({"mv": (36, 105, 0, 0)}, mis),
            "n/a: end-of-turn tick": pair({"foe": {"status1": 0x8}}, mis),
            "n/a: KO": pair(None, {"foe": {"hp": 0}}, obs=65),
            "n/a: doubles": pair({"flags": 0x800D}, mis),
        }
        got = {k: one(x)[0].selfcheck for k, x in cases.items()}
        weather = one(pair({"weather": 8}, dict(mis, weather=8)))[0].selfcheck
        return all(k == g for k, g in got.items()) and weather == "n/a: end-of-turn tick", f"{got} weather={weather}"

    def c4():
        a_ = one(tko())[0].selfcheck
        b_ = one(pair({"t": 3}, obs=90, kind="end"))[0].selfcheck
        return a_ == "n/a: foe changed" and b_ == "n/a: battle end", f"{a_} || {b_}"

    for label, fn in (("C1 a Δbide/HP disagreement on a clean turn is counted, with its frame", c1),
                      ("C2 the masked heal (the foe's item action) is not a disagreement", c2),
                      ("C3 each enumerated heal/tick exclusion holds (held item, Leech Seed on us, heal move, "
                       "tick, weather, KO, doubles)", c3),
                      ("C4 a trainer KO and a battle end are not self-checked", c4)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== X rows
BIG = {"foe": {"hp": 200, "maxhp": 200}}


@lru_cache(maxsize=None)
def clean_block(n: int) -> tuple:
    out: list = []
    for i in range(n):
        out += pair(frame=4_000_000 + 1000 * i)
    return tuple(out)


def x_rows(tag=""):
    reds: list = []
    m = A().ACCEPT_MARGIN
    cmax = PRED[3]

    def verdict(lines, margin=None):
        rep = audit(lines, margin)
        return rep.acceptance, rep

    def x1():
        got, rep = verdict(list(clean_block(300)) + pair(BIG, obs=cmax + m + 1))
        return got == "FAIL" and len(rep.hits) == 301 and len(rep.over) == 1, f"{got} n={len(rep.hits)}"

    def x2():
        got, rep = verdict(list(clean_block(300)) + pair(merge(BIG, {"foe": {"item": 139}}), obs=cmax + m + 1))
        return got == "PASS" and len(rep.hits) == 300, f"{got} n={len(rep.hits)}"

    def x3():
        got, rep = verdict(list(clean_block(300)) + pair(BIG, obs=cmax + m))
        return got == "PASS" and len(rep.hits) == 301 and rep.over == [], f"{got} n={len(rep.hits)}"

    def x4():
        got, rep = verdict(list(clean_block(299)))
        return got == "INSUFFICIENT" and len(rep.hits) == 299, f"{got} n={len(rep.hits)}"

    def x5():
        got, rep = verdict(list(clean_block(299)) + pair({"foe": {"item": 139}}))
        return got == "INSUFFICIENT" and len(rep.hits) == 299, f"{got} n={len(rep.hits)}"

    def x6():
        got, rep = verdict(pair(BIG, obs=cmax + m + 1))
        return got == "FAIL" and rep.exit_code == 1, f"{got} exit {rep.exit_code}"

    def x7():
        lines = list(clean_block(300)) + pair(BIG, obs=cmax + 4)
        a_, _ = verdict(lines, 3)
        b_, _ = verdict(lines, 4)
        c_, _ = verdict(list(clean_block(300)))
        return (a_, b_, c_) == ("FAIL", "PASS", "PASS"), f"{a_} {b_} {c_}"

    for label, fn in (("X1 300 clean + one clean at crit_max + ACCEPT_MARGIN + 1: FAIL", x1),
                      ("X2 the same sample in an excluded stratum (held item): PASS", x2),
                      ("X3 exactly at crit_max + ACCEPT_MARGIN: PASS", x3),
                      ("X4 299 clean samples: INSUFFICIENT", x4),
                      ("X5 299 clean + one EXCLUDED hit: INSUFFICIENT (an excluded hit never counts)", x5),
                      ("X6 a single over-bound hit (n=1): FAIL, not INSUFFICIENT (one fails it for good)", x6),
                      ("X7 the margin is a parameter: +4 fails at 3, passes at 4; 300 clean alone PASS", x7)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== O rows
def o_rows(tag=""):
    reds: list = []

    def o1():
        lines = ([ctl(3189301)] + pair(frame=10) + pair({"foe": {"item": 139}}, frame=20)
                 + pair(used=False, obs=0, frame=30) + pair(a={"foe": {"hp": 23}}, frame=40))
        rep = audit(lines)
        out = A().render(rep)
        text = "\n".join(out)
        want = ["[DMGAUDIT] lines: raw 9, parsed 9", "== strata", "foe-held-item", "our-pp-unchanged",
                "max(obs-cmax)", "effect RECOIL", "stratum foe-held-item", "disagreements 1: [(40, 65, 60)]",
                "  f10 foe=338 hp=83->18 dbide=65 ACCEPTED kind=turn trainer tier=A eff=RECOIL",
                "port control:", "ACCEPTANCE: INSUFFICIENT"]
        missing = [w for w in want if w not in text]
        per_pair = [ln for ln in out if re.match(r"  f\d+ foe=", ln)]
        return not missing and len(per_pair) == 4, f"missing {missing}; per-pair lines {len(per_pair)}"

    def o2():   # the numbers: obs 70 (-62), 134 (+2, 1.015), 50 (below min 56)
        rep = audit(pair(BIG, obs=70, frame=10) + pair(BIG, obs=134, frame=20) + pair(BIG, obs=50, frame=30))
        line = next(ln for ln in A().render(rep) if ln.strip().startswith("ACCEPTED (the acceptance set)"))
        nums = line.split("set)")[1].split()
        return nums == ["3", "+2", "1.015", "0", "0", "1"], line

    def o3():   # the M1a bound: 8 for a charged Electric move (Spark), else 4 (also for a CHARGED Take Down: Charge
        #             doubles Electric moves only); and its over count
        rep = audit(pair({"s3": (0x200, 0), "foe": {"hp": 200, "maxhp": 200}}, obs=139, setup=mv_setup(209),
                         frame=10) + pair(BIG, obs=137, frame=20)
                    + pair({"s3": (0x200, 0), "foe": {"hp": 200, "maxhp": 200}}, obs=137, frame=30))
        b = [A().m1a_bound(at(rep, f)) for f in (10, 20, 30)]
        line = next(ln for ln in A().render(rep) if ln.strip().startswith("ACCEPTED (the acceptance set)"))
        nums = line.split("set)")[1].split()
        return b == [8, 4, 4] and nums[3:5] == ["3", "2"], f"bounds {b} {line}"

    for label, fn in (("O1 the outputs: raw/parsed, strata, per-effect and per-stratum error, self-check with "
                       "frames, one line per BEFORE, port control, acceptance", o1),
                      ("O2 the error numbers: max(obs-cmax), max(obs/cmax), over counts, below-min", o2),
                      ("O3 the M1a bound is 8 for a charged Electric move, 4 otherwise, and is counted", o3)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== PC rows
def pc_rows(tag=""):
    reds: list = []

    def lines_with(fake, hits=()):
        saved = sys.modules.get("dmgcalc_port", "absent")
        try:
            sys.modules["dmgcalc_port"] = fake
            return A().port_control(list(hits))
        finally:
            if saved == "absent":
                sys.modules.pop("dmgcalc_port", None)
            else:
                sys.modules["dmgcalc_port"] = saved

    def spy_calls(lines):
        """The EXACT `after_base` calls the audit makes for `lines`' accepted hits (a spy port: every call inside)."""
        calls: list = []
        fake = types.ModuleType("dmgcalc_port")

        def after_base(**kw):
            calls.append(kw)
            return (1, 10 ** 6)

        fake.after_base = after_base
        rep = audit(lines)
        got = lines_with(fake, rep.hits)
        return calls, got, rep

    def call(B, crit, move_type="Normal", att=("Dark", "Dark"), dfn=("Electric", "Electric"), charge=False,
             struggle=False, foresight=False):
        return dict(B=B, crit=crit, move_type=move_type, attacker_types=att, defender_types_rom=dfn,
                    charge_listed_electric=charge, struggle=struggle, foresight=foresight)

    def pc1():
        got = lines_with(None)                                   # None in sys.modules: the import raises
        return len(got) == 1 and got[0].startswith("port control: unavailable (no dmgcalc_port module"), str(got)

    def pc2():
        got = lines_with(types.ModuleType("dmgcalc_port"))
        return got == ["port control: unavailable (dmgcalc_port has no after_base)"], str(got)

    def pc3():  # Take Down (listed Normal), OUR dual types (Dark, Normal), a DUAL-type foe in ROM order (Electric,
        #             Water); base 40/44 — both type pairs in ROM order, so a swap on either side shows
        calls, got, rep = spy_calls(pair({"foe": {"type1": 13, "type2": 11}, "me": {"type1": 17, "type2": 0}}))
        dual = dict(att=("Dark", "Normal"), dfn=("Electric", "Water"))
        want = [call(40, False, **dual), call(44, True, **dual)]
        return (len(rep.hits) == 1 and calls == want and got[0].startswith("port control: 1 clean hits: 1 replayed")), \
            f"{calls} {got}"

    def pc4():  # Spark (listed Electric) while we are CHARGED (s3 0x200): Charge applies
        calls, _, rep = spy_calls(pair({"s3": (0x200, 0)}, setup=mv_setup(209)))
        want = [call(40, False, "Electric", charge=True), call(44, True, "Electric", charge=True)]
        return len(rep.hits) == 1 and calls == want, str(calls)

    def pc5():  # Hidden Power: move_type is the ROLLED type; Charge reads the LISTED type (Normal) -> never doubled
        electric = ivs(31, 31, 31, 31, 30, 31)                # type bits 47 -> 15*47//63+1 = 12 -> skips ??? -> 13
        lines = (pair({"s3": (0x200, 0), "me": {"ivs": electric}}, setup=mv_setup(237), frame=10)
                 + pair({"me": {"ivs": ivs(31, 31, 31, 31, 31, 31)}}, setup=mv_setup(237), frame=20))
        calls, _, rep = spy_calls(lines)
        want = [call(40, False, "Electric"), call(44, True, "Electric"), call(40, False, "Dark"), call(44, True, "Dark")]
        return len(rep.hits) == 2 and calls == want, str(calls)

    def pc6():  # the FOE identified by Foresight (status2 0x20000000): foresight=True
        calls, _, rep = spy_calls(pair({"foe": {"status2": 0x20000000}}))
        want = [call(40, False, foresight=True), call(44, True, foresight=True)]
        return len(rep.hits) == 1 and calls == want, str(calls)

    def pc7():  # the REAL port, by hand: Normal, no STAB, vs Electric (no row): non-crit B 40 -> [34, 40]; crit B 44
        #           -> 88 -> [74, 88]; so the port's [non-crit min, crit max] = [34, 88]
        rep = audit(pair(BIG, obs=65, frame=10) + pair(BIG, obs=89, frame=20) + pair(BIG, obs=33, frame=30))
        got = A().port_control(rep.hits)
        want = ["port control: 3 clean hits: 3 replayed, 0 unreplayable [], 2 outside the port's [non-crit min, crit "
                "max]: f20 obs 89 port [34,88], f30 obs 33 port [34,88]"]
        return len(rep.hits) == 3 and got == want, str(got)

    def pc8():  # base=none, and a type id outside 0..17: unreplayable, never counted inside
        lines = (pair({"base": None}, frame=10) + pair({"foe": {"type1": 200, "type2": 200}}, frame=20))
        rep = audit(lines)
        got = A().port_control(rep.hits)
        want = ["port control: 2 clean hits: 0 replayed, 2 unreplayable [10, 20], 0 outside the port's [non-crit min, "
                "crit max]"]
        return len(rep.hits) == 2 and got == want, str(got)

    def pc9():  # the adapter's type names are the port's, and the Hidden Power roll matches the M1a rows B-HP/B-HPC
        import dmgcalc_port
        names = {n: i for i, n in enumerate(A().TYPE_NAMES)}
        hp = A().hidden_power_type
        return (names == dmgcalc_port.ROM_TYPE_IDS and hp(ivs(31, 31, 31, 31, 31, 31)) == "Dark"
                and hp(ivs(31, 31, 31, 31, 30, 31)) == "Electric"), f"{hp(ivs(31, 31, 31, 31, 30, 31))}"

    for label, fn in (("PC1 no port module: 'port control: unavailable'", pc1),
                      ("PC2 a port module without after_base: 'port control: unavailable'", pc2),
                      ("PC3 the adapter's EXACT calls: non-crit from b, crit from bcrit, listed Normal, our types, the "
                       "foe's types in ROM order", pc3),
                      ("PC4 Charge = our s3 0x200 AND a LISTED-Electric move (Spark)", pc4),
                      ("PC5 Hidden Power: move_type is the ROLLED type (Electric, Dark); Charge never applies (listed "
                       "Normal)", pc5),
                      ("PC6 foresight = the foe's status2 FORESIGHT bit", pc6),
                      ("PC7 the REAL port: an inside and two outside observations, listed with their frames", pc7),
                      ("PC8 base=none / a type id outside 0..17: unreplayable", pc8),
                      ("PC9 the adapter's type names equal the port's ROM_TYPE_IDS; the Hidden Power roll", pc9)):
        row(label, fn, tag, reds)
    return reds


def ivs(hp, atk, df, spe, spa, spd) -> int:
    """The IV word at 0x14 (5-bit fields HP, Atk, Def, Speed, SpAtk, SpDef)."""
    return hp | atk << 5 | df << 10 | spe << 15 | spa << 20 | spd << 25


# ======================================================================================================== T rows
S0_LINE = re.compile(r"^f(\d+) (\S+) turn=(\d+) outcome=(\d+) bide=\[([^\]]*)\] act=\[([^\]]*)\] mv=\[([^\]]*)\] "
                     r"count=(\d+) flags=([0-9a-f]+) ff=(\[[^\]]*\]|\S+) cb=(\S+) (.*)$")
S0_MON = re.compile(r"b(\d):sp=(\d+) hp=(\d+)/(\d+) pid=([0-9a-f]+) moves=\[([^\]]*)\] pp=\[([^\]]*)\] st1=([0-9a-f]+)")
#: The PREDICTIONS' per-turn verdict table (M1b; the 17 singles USE_MOVE exits of the Step-0 trajectory):
#: exit frame -> (status, kind, reasons that must be present, battle)
TABLE = {
    3173282: (EXC, "trainer KO", {"foe-self-hurt-move"}, "trainer"),
    3174185: (ACC, "KO", set(), "trainer"),
    3185457: (NAS, "", {"our-pp-unchanged"}, "trainer"),
    3186160: (NAS, "", {"our-pp-unchanged"}, "trainer"),
    3186810: (EXC, "turn", {"no-damage", "foe-held-item"}, "trainer"),
    3187609: (EXC, "KO", {"foe-held-item"}, "trainer"),
    3190263: (ACC, "turn", set(), "trainer"),
    3191078: (EXC, "turn", {"foe-item-action"}, "trainer"),
    3191967: (ACC, "trainer KO", set(), "trainer"),
    # The table allowed EITHER verdict here ("ACCEPTED if our hit came first, else excluded: the foe's Def stage
    # changed; the read decides"). The first live audit then showed a faint RESETS the foe's record (DESIGN F6 ⚠), so
    # the read CANNOT decide any more: Shiftry chose Harden and fainted, so the classifier keys on that choice.
    3193320: (EXC, "KO", {"foe-after-unobservable"}, "trainer"),
    3197066: (ACC, "trainer KO", set(), "trainer"),
    3198642: (ACC, "turn", set(), "trainer"),
    3199547: (EXC, "KO", {"foe-move-zero"}, "trainer"),
    3208167: (ACC, "KO", set(), "wild"),
    3210218: (ACC, "KO", set(), "wild"),
    3216950: (ACC, "turn", set(), "wild"),
    3217980: (ACC, "KO", set(), "wild"),
}
NAMED_CLEAN = [3190263, 3198642, 3216950]           # the self-check's named turns (PREDICTIONS, FAULT)


#: Each Step-0 species' ability (Gen 3 ids), so a faint's RESET (ability 0) is visible in the T rows: Koffing Levitate,
#: Pikachu and Manectric Static, Shiftry Chlorophyll, Loudred Soundproof, Vigoroth Vital Spirit, Poochyena Run Away,
#: Shuppet Insomnia, Linoone Pickup; our Mightyena Intimidate.
S0_ABILITY = {109: 26, 25: 9, 338: 9, 300: 34, 371: 43, 365: 72, 286: 50, 377: 15, 289: 53, 287: 22}


def _s0_mon(mm, item=0) -> dict:
    sp = int(mm[2])
    return dict(species=sp, atk=50, def_=50, spe=50, spa=50, spd=50,
                moves=tuple(int(x) for x in mm[6].split(",")), ivs=0,
                stages=(6, 6, 6, 6, 6, 6, 6, 8) if sp == 25 else (6,) * 8,     # Pikachu's Double Teams (Evasion +2)
                ability=S0_ABILITY.get(sp, 0), type1=0, type2=0,
                pp=tuple(int(x) for x in mm[7].split(",")), hp=int(mm[3]), level=30, maxhp=int(mm[4]), item=item,
                pid=int(mm[5], 16), status1=int(mm[8], 16), status2=0)


@lru_cache(maxsize=None)
def step0_lines(fault: bool = False) -> tuple:
    """The Step-0 raw reads -> [DMGAUDIT] lines for the 17 singles USE_MOVE exits (+ their next ENTRY/BATTLE-END).
    Fields Step-0 did not read are neutral, except Vanessa's Pikachu's Oran Berry (the decomp's sParty_Vanessa) and
    the party (the old PID at 0 HP on an identity change). `fault`: bide[1] := bide[0] (M1b-FAULT's switch)."""
    reads = []
    for ln in STEP0.read_text(encoding="utf-8").splitlines():
        m = S0_LINE.match(ln)
        if m:
            reads.append((m, {int(mm[1]): mm for mm in S0_MON.finditer(m[12])}))
    out: list = []
    for i, (m, mons) in enumerate(reads):
        act, mv = [int(x) for x in m[6].split(",")], [int(x) for x in m[7].split(",")]
        if m[2] != "EXIT" or act[0] != 0 or mv[0] == 0 or int(m[9], 16) & 1:
            continue
        nxt = next((r for r in reads[i + 1:] if r[0][2] in ("ENTRY", "BATTLE-END")), None)
        if nxt is None:                                 # the log's last EXIT (f3232457) has no next read
            continue
        nm, nmons = nxt

        def state(mm, mmons):
            bide = [int(x) for x in mm[5].split(",")]
            if fault:
                bide[1] = bide[0]
            ff = None if mm[10] == "null" else tuple(int(x) for x in mm[10].strip("[]").split(","))
            foe = _s0_mon(mmons[1], item=139 if int(mmons[1][2]) == 25 else 0)
            return dict(t=int(mm[3]), out=int(mm[4]), flags=int(mm[9], 16),
                        act=tuple(int(x) for x in mm[6].split(",")), mv=tuple(int(x) for x in mm[7].split(",")),
                        bide=tuple(bide), weather=0, side=(0, 0), s3=(0, 0), me=_s0_mon(mmons[0]), foe=foe, ff=ff)

        b, a = state(m, mons), state(nm, nmons)
        if nm[2] == "BATTLE-END" and a["foe"]["hp"] == 0 and a["foe"]["pid"] == b["foe"]["pid"]:
            # the faint RESET the first live audit found (DESIGN F6 ⚠): ability 0, stages neutral, item cleared
            a["foe"] = dict(a["foe"], ability=0, stages=(6,) * 8, item=0)
        obs = a["bide"][1] - b["bide"][1]
        hi = max(obs, 0) + 2 if obs > 0 else 48
        b.update(badges=0, pred=(hi * 85 // 100, hi, 2 * (hi * 85 // 100), 2 * hi), base=(hi, hi), eff=None)
        old, new = b["foe"], a["foe"]
        party = ((old["pid"], 0), (new["pid"], new["hp"])) if old["pid"] != new["pid"] else ((old["pid"], new["hp"]),)
        a.update(kind="end" if nm[2] == "BATTLE-END" else "entry", party=party + ZERO6[:6 - len(party)])
        out += [before_line(int(m[1]), b), after_line(int(nm[1]), a)]
    return tuple(out)


def t_rows(tag=""):
    reds: list = []

    def t1():
        rep = audit(list(step0_lines()))
        vs = {v.before.frame: v for v in rep.verdicts}
        bad = []
        for f, (st, kind, need, battle) in TABLE.items():
            v = vs.get(f)
            if v is None or v.status != st or v.kind != kind or not need <= set(v.reasons) or \
                    (st == ACC and (v.reasons or v.battle != battle)):
                bad.append((f, None if v is None else vtxt(v)))
        elig = [v.before.frame for v in rep.verdicts if v.selfcheck in ("agree", "DISAGREE")]
        return (len(rep.verdicts) == 17 and set(vs) == set(TABLE) and not bad and elig == NAMED_CLEAN
                and rep.selfcheck_disagreements == [] and rep.acceptance == "INSUFFICIENT" and len(rep.hits) == 9
                and rep.instrument_ok), f"n={len(rep.verdicts)} bad={bad} elig={elig} acc={rep.acceptance} " \
                                        f"hits={len(rep.hits)}"

    def t2():
        rep = audit(list(step0_lines(fault=True)))
        dis = [v.before.frame for v in rep.selfcheck_disagreements]
        return dis == NAMED_CLEAN, f"FAULT disagreements at {dis}"

    for label, fn in (("T1 the PREDICTIONS' 17-turn table from the Step-0 reads (a KO's end read RESET, as live): every "
                       "verdict, the self-check's named turns (0 disagreements), INSUFFICIENT with 9 accepted", t1),
                      ("T2 the FAULT arm offline (bide[1] := bide[0]): the self-check disagrees on exactly the named "
                       "turns", t2)):
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== PIN rows
ORIG_GBS = modules.battle_state.get_battle_state
HOOKS = ("on_battle_start", "on_selection_entry", "on_selection_exit", "on_battle_end")


def Dm():
    return sys.modules[D_NAME]


def _rec(m: dict) -> bytes:
    return bytes.fromhex(mon_hex(m))


def fake_syms(action: int = 0) -> dict:
    """The bytes each symbol production reads holds, for one selection (our Take Down vs Marcel's Manectric)."""
    party = bytearray(600)
    struct.pack_into("<I", party, 0, FOE["pid"])
    struct.pack_into("<H", party, 0x56, FOE["hp"])
    return {"gBideDmg": struct.pack("<4i", 27201, 67667, 297, 3722),
            "gChosenMoveByBattler": struct.pack("<4H", 36, 336, 0, 0),
            "gChosenActionByBattler": bytes([action, 0, 255, 255]),
            "gSideStatuses": bytes(4), "gStatuses3": bytes(8), "gDisableStructs": bytes(0x38),
            "gBattleMons": _rec(ME) + _rec(FOE),
            "gBattleResources": bytes(4),                          # NULL: ff=null, no dereference
            "gBattleResults": bytes(0x13) + bytes([2]) + bytes(12), "gBattleOutcome": bytes(1),
            "gBattleTypeFlags": struct.pack("<I", 0xC), "gBattleWeather": bytes(2), "gEnemyParty": bytes(party)}


def real_state():
    """A REAL single-battle BattleState from the same two records (M1a's construction), so that `_prediction` runs the
    real calculator on real BattlePokemon objects — the path a hidden get_battle_state() call would sit on."""
    return BattleState(battle_type=struct.pack("<I", 0), side_timers=bytes(24),
                       battler_party_indexes=struct.pack("<HHHH", 0, 0, 0, 0),
                       battler_party_order=bytes([0x01, 0x23, 0x45]), battler_count=2,
                       battler=_rec(ME) + _rec(FOE) + bytes(0x58 * 2), battler_status3=bytes(16),
                       battler_disable_structs=bytes(0x1C * 4), absent_battler_flags=0, current_turn=1, weather=0)


@contextlib.contextmanager
def world(*, flag="1", fault=False, syms=None, mem=None, callback="SetActionsAndBattlersTurnOrder", active=True,
          raise_on=None, calc_raise=False, pending=False, badges=()):
    """Production's world, faked (the adversarial pass's `world()`, merged with this gate's rebinding):
      the env (`flag` None = unset, else its literal value; `fault` sets the FAULT switch);
      `read_symbol` — a recorder over `syms` (default `fake_syms()`), raising KeyError on `raise_on`;
      `context.emulator.read_bytes` — a recorder over `mem` (address -> bytes; the Flash Fire EWRAM chain);
      `get_event_flag` — True for the names in `badges`;  `debug_logger.event` — a recorder;
      the two battle-state probes `on_selection_exit` consults (`active`, `callback`);
      `calc_raise` — the calculator's `calculate_move_damage_range` raises;
      and `get_battle_state` REBOUND wherever it is bound (a module that from-imported it would dodge a patch on
      `modules.battle_state` alone). `pending` is written to the module's `_pending` first."""
    log = types.SimpleNamespace(events=[], reads=[], gbs=[], emu=[])
    syms = fake_syms() if syms is None else syms
    mem = {} if mem is None else mem

    def fake_read(name, offset=0, size=0):
        log.reads.append(name)
        if raise_on and name == raise_on:
            raise KeyError(name)
        return syms[name][offset:offset + size]

    def fake_event(message, *, category="STORY"):
        log.events.append((category, message))

    class Emu:
        def read_bytes(self, addr, n):
            log.emu.append(addr)
            return mem.get(addr, bytes(n))[:n]

    def spy_gbs(*_a, **_k):
        log.gbs.append(1)
        return real_state()

    def boom(*_a, **_k):
        raise ZeroDivisionError("the calculator raised")

    bs = modules.battle_state
    patches = [(modules.memory, "read_symbol", fake_read), (modules.memory, "get_event_flag", lambda n: n in badges),
               (modules.debug_logger, "event", fake_event), (bs, "battle_is_active", lambda: active),
               (bs, "get_main_battle_callback", lambda: callback), (modules.context.context, "emulator", Emu())]
    if calc_raise:
        patches.append((modules.battle_strategies._util.BattleStrategyUtil, "calculate_move_damage_range", boom))
    for mod in list(sys.modules.values()):
        if isinstance(mod, types.ModuleType) and mod.__dict__.get("get_battle_state") is ORIG_GBS:
            patches.append((mod, "get_battle_state", spy_gbs))
    saved = [(m, n, getattr(m, n)) for m, n, _f in patches]
    env = {k: os.environ.get(k) for k in (FLAG, FAULT)}
    try:
        for k, value in ((FLAG, flag), (FAULT, "1" if fault else None)):
            if value is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = value
        for m, n, f in patches:
            setattr(m, n, f)
        Dm()._pending = pending
        yield log
    finally:
        for m, n, f in saved:
            setattr(m, n, f)
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def prod(flag: bool, fault: bool = False, action: int = 0):
    """The PIN rows' world: `fake_syms(action)`, the flag set or unset."""
    return world(flag="1" if flag else None, fault=fault, syms=fake_syms(action))


def run_seq(fault=False, action=0):
    """start, exit, entry, exit, end — flag SET."""
    d, state = Dm(), real_state()
    with prod(True, fault, action) as log:
        d._pending = False
        d.on_battle_start()
        d.on_selection_exit(state)
        d.on_selection_entry()
        d.on_selection_exit(state)
        d.on_battle_end()
    return log


def _field(message, key):
    m = re.search(rf" {key}=(\S+)", message)
    return m.group(1) if m else None


def _obj_call(stmt, obj, attr, args=()):
    """`stmt` is the expression statement `obj.attr(*args)` (args as source text), with no keywords."""
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == attr
            and isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == obj
            and [ast.unparse(a) for a in stmt.value.args] == list(args) and not stmt.value.keywords)


def _count_calls(tree, obj, attr):
    return sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == attr and isinstance(n.func.value, ast.Name) and n.func.value.id == obj)


def _func(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _body(f):
    body = list(f.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and \
            isinstance(body[0].value.value, str):
        body = body[1:]                                 # the docstring
    return body


def pin_rows(tag, srcs):
    reds: list = []

    def unset(hook):
        def fn():
            d = Dm()
            with prod(False) as log:
                d._pending = True                       # so the ONLY gate left is the flag
                getattr(d, hook)(*((real_state(),) if hook == "on_selection_exit" else ()))
            return log.reads == [] and log.events == [], f"reads {log.reads} events {log.events}"
        return fn

    def b1():
        log = run_seq()
        befores = [m for _c, m in log.events if m.startswith("BEFORE ")]
        ran = [bool(re.search(r" pred=\d+,\d+,\d+,\d+ base=\d+,\d+ eff=RECOIL$", m)) for m in befores]
        return log.gbs == [] and len(befores) == 2 and all(ran), f"get_battle_state calls {len(log.gbs)}; {ran}"

    def b2():
        log = run_seq()
        cats = [c for c, _m in log.events]
        return len(cats) == 5 and set(cats) == {"DMGAUDIT"}, str(cats)

    def b3():
        log = run_seq()
        kinds = [m.split()[0] for _c, m in log.events]
        after_kinds = [_field(m, "kind") for _c, m in log.events if m.startswith("AFTER ")]
        return kinds == ["CTL", "BEFORE", "AFTER", "BEFORE", "AFTER"] and after_kinds == ["entry", "end"], \
            f"{kinds} {after_kinds}"

    def b4():
        normal = [_field(m, "bide") for _c, m in run_seq().events if m.startswith("BEFORE ")]
        fault = [_field(m, "bide") for _c, m in run_seq(fault=True).events if m.startswith("BEFORE ")]
        return normal == ["27201,67667,297,3722"] * 2 and fault == ["27201,27201,297,3722"] * 2, f"{normal} {fault}"

    def b5():
        log = run_seq()
        text = "\n".join(f"f{1000 + i} [{c}] {m}" for i, (c, m) in enumerate(log.events))
        rep = audit(text.splitlines())
        return (rep.raw_count == rep.parsed_count == 5 and rep.by_kind == {"CTL": 1, "BEFORE": 2, "AFTER": 2}), \
            f"raw {rep.raw_count} parsed {rep.parsed_count} {[u[1] for u in rep.unparsed]}"

    def b6():   # our action is an item: pred=none, and the contract still wants base=none on the BEFORE line
        log = run_seq(action=1)
        befores = [f"f1 [{c}] {m}" for c, m in log.events if m.startswith("BEFORE ")]
        rep = audit(befores)
        return (len(befores) == 2 and all(" pred=none base=none eff=-" in b for b in befores)
                and rep.raw_count == rep.parsed_count == 2), \
            f"{[b[b.index(' pred='):] for b in befores]} unparsed {[u[1] for u in rep.unparsed]}"

    def c1():
        tree = ast.parse(srcs["bas"])
        body = _body(_func(tree, "handle_battle_action_selection"))
        return (_count_calls(tree, "_dmgaudit", "on_selection_entry") == 1
                and ast.unparse(body[0]) == "battle_state = get_battle_state()"
                and _obj_call(body[1], "_dmgaudit", "on_selection_entry")), \
            f"{ast.unparse(body[0])[:60]} || {ast.unparse(body[1])[:60]}"

    def c2():
        tree = ast.parse(srcs["bas"])
        body = _body(_func(tree, "handle_battle_action_selection"))
        whiles = [i for i, s in enumerate(body) if isinstance(s, ast.While)]
        return (_count_calls(tree, "_dmgaudit", "on_selection_exit") == 1
                and _obj_call(body[-1], "_dmgaudit", "on_selection_exit", ("battle_state",))
                and bool(whiles) and whiles[-1] < len(body) - 1), f"last: {ast.unparse(body[-1])[:70]}"

    def main_loop(tree):
        body = _body(_func(tree, "handle_battle"))
        loops = [i for i, s in enumerate(body) if isinstance(s, ast.While)
                 and "battle_is_active()" in ast.unparse(s.test) and "_learn_or_evo_pending()" in ast.unparse(s.test)]
        return body, loops

    def c3():
        tree = ast.parse(srcs["bh"])
        body, loops = main_loop(tree)
        return (len(loops) == 1 and _count_calls(tree, "_dmgaudit", "on_battle_start") == 1
                and _obj_call(body[loops[0] - 1], "_dmgaudit", "on_battle_start")), \
            f"loops {loops}; before: {ast.unparse(body[loops[0] - 1])[:60] if loops else '-'}"

    def c4():
        tree = ast.parse(srcs["bh"])
        body, loops = main_loop(tree)
        return (len(loops) == 1 and _count_calls(tree, "_dmgaudit", "on_battle_end") == 1
                and _obj_call(body[loops[0] + 1], "_dmgaudit", "on_battle_end")), \
            f"loops {loops}; after: {ast.unparse(body[loops[0] + 1])[:60] if loops else '-'}"

    def c5():
        tree = ast.parse(srcs["dmgaudit"])
        hits = [ast.unparse(n)[:40] for n in ast.walk(tree)
                if (isinstance(n, ast.Name) and n.id == "get_battle_state")
                or (isinstance(n, ast.Attribute) and n.attr == "get_battle_state")
                or (isinstance(n, ast.alias) and (n.name == "get_battle_state" or n.asname == "get_battle_state"))]
        return hits == [], str(hits)

    def c6():
        tree = ast.parse(srcs["dmgaudit"])
        events = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and ((isinstance(n.func, ast.Attribute) and n.func.attr == "event")
                       or (isinstance(n.func, ast.Name) and n.func.id == "event"))]
        bad = [ast.unparse(n)[:60] for n in events
               if not any(k.arg == "category" and isinstance(k.value, ast.Constant) and k.value.value == "DMGAUDIT"
                          for k in n.keywords)]
        return bool(events) and not bad, f"{len(events)} event calls; not DMGAUDIT: {bad}"

    cases = [(f"PIN-a{i + 1} flag UNSET: {h} reads nothing and logs nothing (with a BEFORE pending)", unset(h))
             for i, h in enumerate(HOOKS)]
    cases += [
        ("PIN-b1 flag SET: ZERO get_battle_state() calls across the four hooks, while the calculator path ran "
         "(pred and base are numbers)", b1),
        ("PIN-b2 flag SET: all 5 lines are category DMGAUDIT", b2),
        ("PIN-b3 flag SET: start/exit/entry/exit/end log CTL, BEFORE, AFTER(entry), BEFORE, AFTER(end)", b3),
        ("PIN-b4 the FAULT switch makes the logged bide position 1 equal position 0", b4),
        ("PIN-b5 every line production writes parses under this audit's v=1 parser (raw 5 == parsed 5)", b5),
        ("PIN-b6 a BEFORE with pred=none carries base=none and parses (the contract's 'base on every BEFORE')", b6),
        ("PIN-c1 (AST) exactly one on_selection_entry(), the statement right after battle_state = get_battle_state()",
         c1),
        ("PIN-c2 (AST) exactly one on_selection_exit(battle_state), the LAST statement, after the while", c2),
        ("PIN-c3 (AST) handle_battle: on_battle_start() is the statement immediately before the main loop", c3),
        ("PIN-c4 (AST) handle_battle: on_battle_end() is the statement immediately after the main loop", c4),
        ("PIN-c5 (AST) dmgaudit.py never names get_battle_state (Name, Attribute or import; comments ignored)", c5),
        ("PIN-c6 (AST) every debug_logger.event call in dmgaudit.py passes category='DMGAUDIT'", c6),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ======================================================================================================== N rows
# Integrated from the ADVERSARIAL MUTANT PASS (2026-09-30, `proposed.py`: each row was validated there to pass on the real
# code and to redden its target mutants), plus the rows for the live-found faint reset and Hidden Power's rolled type.
#: The design's OWN literal lists (F2's tiers; F4's self-hurt list; the classifier's documented FOE_SELF_STATE and drain
#: sets), held BY THE GATE and never read from the module under test.
F2_A = {"HIT", "HIGH_CRITICAL", "ALWAYS_HIT", "QUICK_ATTACK", "VITAL_THROW", "PAY_DAY", "SECRET_POWER", "SKY_UPPERCUT",
        "THUNDER", "KNOCK_OFF", "THIEF", "RAPID_SPIN", "FLINCH_HIT", "PARALYZE_HIT", "FREEZE_HIT", "SUPERPOWER",
        "OVERHEAT", "RECHARGE", "DOUBLE_EDGE", "RECOIL", "RECOIL_IF_MISS", "ABSORB", "RAGE", "HIDDEN_POWER"}
F2_B = {"BURN_HIT", "BLAZE_KICK", "THAW_HIT", "TRI_ATTACK", "POISON_HIT", "POISON_TAIL", "POISON_FANG", "CONFUSE_HIT"}
F2_C = {"EARTHQUAKE", "GUST", "TWISTER", "FLINCH_MINIMIZE_HIT", "FACADE", "SMELLINGSALT", "WEATHER_BALL", "BRICK_BREAK",
        "PURSUIT", "FALSE_SWIPE", "FAKE_OUT", "FOCUS_PUNCH", "SNORE", "DREAM_EATER"}
F4_SELF_HURT = {"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "SUBSTITUTE", "BELLY_DRUM", "PAIN_SPLIT", "EXPLOSION",
                "MEMENTO"}
SELF_STATE = {"DEFENSE_UP", "DEFENSE_UP_2", "SPECIAL_DEFENSE_UP_2", "DEFENSE_CURL", "COSMIC_POWER", "CALM_MIND",
              "BULK_UP", "CURSE", "SUPERPOWER", "DEFENSE_UP_HIT", "ALL_STATS_UP_HIT", "PSYCH_UP", "HAZE",
              "SEMI_INVULNERABLE", "MINIMIZE", "MUD_SPORT", "WATER_SPORT", "CONVERSION", "CONVERSION_2", "CAMOUFLAGE",
              "TRANSFORM", "SKILL_SWAP", "ROLE_PLAY"}
DRAIN = {"ABSORB", "DREAM_EATER"}                       # (LEECH_SEED is observed through our s3 instead)
FIRST: dict = {}
for _i, _m in enumerate(MOVES):
    FIRST.setdefault(_m["effect"], _i)                  # the first move index carrying each effect
BLAZE_EMBER = merge(mv_setup(52), {"me": {"ability": 66}})
EW = 0x02000000
RES, FLAGS_PTR = EW + 0x1000, EW + 0x2000


def all_excl(cases, reason):
    vs = [one(x)[0] for x in cases]
    return all(v.status == EXC and reason in v.reasons for v in vs), " || ".join(vtxt(v) for v in vs)


def distinct_syms():
    """Every RAW field holds a DISTINCT value (so an offset, order, width or sign slip shows), and gBattleResources
    points into EWRAM (a valid Flash Fire chain in `distinct_mem`)."""
    party = bytearray(600)
    for slot, (pid, hp) in enumerate(((FOE["pid"], 83), (0x00157F88, 94))):
        struct.pack_into("<I", party, slot * 100, pid)
        struct.pack_into("<I", party, slot * 100 + 4, 0xDEADBEEF)          # the OT id beside the PID
        party[slot * 100 + 0x54], party[slot * 100 + 0x55] = 26, 0xFF      # level, mail id beside the HP
        struct.pack_into("<H", party, slot * 100 + 0x56, hp)
    return {"gBideDmg": struct.pack("<4i", 27201, -5, 297, 3722),
            "gChosenMoveByBattler": struct.pack("<4H", 36, 336, 7, 8),
            "gChosenActionByBattler": bytes([0, 1, 254, 253]),
            "gSideStatuses": struct.pack("<2H", 0x10, 0x3), "gStatuses3": struct.pack("<2I", 0x20000, 0x40004),
            "gDisableStructs": bytes(range(0x38)),
            "gBattleMons": _rec(ME) + _rec(FOE),
            "gBattleResources": struct.pack("<I", RES),
            "gBattleResults": bytes(0x12) + bytes([9, 5]) + bytes(12), "gBattleOutcome": bytes([0]),
            "gBattleTypeFlags": struct.pack("<I", 0x0000800C), "gBattleWeather": struct.pack("<H", 0x0108),
            "gEnemyParty": bytes(party)}


def distinct_mem(flags_ptr=FLAGS_PTR):
    """gBattleResources -> (+0x00 a decoy pointer, +0x04 the flags pointer) -> u32 flags[0], flags[1]."""
    return {RES: struct.pack("<I", 0x02003000), RES + 4: struct.pack("<I", flags_ptr),
            flags_ptr: struct.pack("<I", 1), flags_ptr + 4: struct.pack("<I", 0x100),
            0x02003000: struct.pack("<I", 0x77), 0x02003004: struct.pack("<I", 0x88)}


def dworld(**kw):
    return world(**{"syms": distinct_syms(), "mem": distinct_mem(), **kw})


def staged_state():
    """real_state() with the foe at Def +2: a crit ignores the defender's positive Def stage, so b != bcrit and the
    crit range differs from the plain one (D15/D16/D17 become distinguishable)."""
    foe = dict(FOE, stages=(6, 6, 8, 6, 6, 6, 6, 6))
    return BattleState(battle_type=struct.pack("<I", 0), side_timers=bytes(24),
                       battler_party_indexes=struct.pack("<HHHH", 0, 0, 0, 0),
                       battler_party_order=bytes([0x01, 0x23, 0x45]), battler_count=2,
                       battler=_rec(ME) + _rec(foe) + bytes(0x58 * 2), battler_status3=bytes(16),
                       battler_disable_structs=bytes(0x1C * 4), absent_battler_flags=0, current_turn=1, weather=0)


def _acc_nums(rep):
    line = next(ln for ln in A().render(rep) if ln.strip().startswith("ACCEPTED (the acceptance set)"))
    return line.split("set)")[1].split()


def n_rows(tag, srcs):
    reds: list = []
    cmax = PRED[3]

    # ------------------------------------------------------------------ the live-found faint reset (DESIGN F6 ⚠)
    RESET = {"foe": {"ability": 0, "stages": (6,) * 8, "item": 0}}
    B_KO = {"t": 3, "foe": {"ability": 26, "stages": (6, 6, 7, 6, 6, 7, 6, 8)}}   # Levitate, Def/SpD +1, Evasion +2

    def nr_faint_reset():
        v = one(pair(B_KO, RESET, obs=90, kind="end"))[0]              # 83 -> 0: the record reset at the AFTER read
        return v.status == ACC and v.kind == "KO" and v.reasons == (), vtxt(v)

    def nr_faint_harden():
        v = one(pair(merge(B_KO, {"mv": (36, 106, 0, 0)}), RESET, obs=90, kind="end"))[0]
        return v.status == EXC and v.reasons == ("foe-after-unobservable",), vtxt(v)

    # ------------------------------------------------------------------ Hidden Power's ROLLED type (the gap, fixed)
    GRASS, FIRE = ivs(30, 31, 30, 31, 30, 31), ivs(30, 31, 30, 30, 30, 31)   # bits 42 -> Grass; 34 -> Fire

    def nr_hp_rolled_type():
        dip = one(pair({"me": {"ability": 65, "hp": 60, "ivs": GRASS}}, {"me": {"hp": 60}}, d0=30,
                       setup=mv_setup(237)))[0]                            # the dip only (60 - 30 = 30 <= 42)
        per_read = one(pair({"me": {"ability": 65, "ivs": GRASS}}, {"me": {"hp": 40}}, setup=mv_setup(237)))[0]
        sport = one(pair({"me": {"ivs": FIRE}, "s3": (0, 0x20000)}, {"s3": (0, 0)}, setup=mv_setup(237)))[0]
        return (A().hidden_power_type(GRASS) == "Grass" and A().hidden_power_type(FIRE) == "Fire"
                and dip.reasons == ("our-pinch",) and per_read.reasons == ("our-pinch",)
                and sport.reasons == ("C:sport",)), f"{vtxt(dip)} || {vtxt(per_read)} || {vtxt(sport)}"

    # ------------------------------------------------------------------ classifier rows (the pass)
    def nr_sport():
        return all_excl([pair({"s3": (0, 0x20000)}, {"s3": (0, 0)}, setup=mv_setup(52)),     # the FOE's Water Sport
                         pair({"s3": (0x10000, 0)}, {"s3": (0, 0)}, setup=mv_setup(209)),    # OUR Mud Sport, Spark
                         pair(None, {"s3": (0, 0x10000)}, setup=mv_setup(209))], "C:sport")  # the foe's, at AFTER

    def nr_twister():
        return all_excl([pair({"s3": (0, 0x40)}, {"s3": (0, 0)}, setup=mv_setup(239))], "C:gust-in-the-air")

    def nr_counters():
        a, da = all_excl([pair({"foe": {"status2": c}}, {"foe": {"status2": 0}}) for c in (2, 3, 4, 5)],
                         "foe-confused")
        b, db = all_excl([pair({"foe": {"status2": c}}, {"foe": {"status2": 0}})
                          for c in (0x4000, 0x6000, 0x8000, 0xA000)], "foe-trapped")
        return a and b, da + " ## " + db

    def nr_foestatus():
        return all_excl([pair({"foe": {"status1": s}}, {"foe": {"status1": 0}}) for s in (0x2, 0x20, 0x40, 0x80, 0x10)],
                        "foe-status")

    def nr_brick():
        return all_excl([pair({"side": (0, 2)}, {"side": (0, 0)}, setup=mv_setup(280))], "C:brick-break-screens")

    def nr_pinch_edges():
        a, da = all_excl([pair(None, {"me": {"hp": 42}}, setup=BLAZE_EMBER)], "our-pinch")         # 42 == 127 // 3
        b, db = all_excl([pair({"me": {"ability": 66, "hp": 60}}, {"me": {"hp": 60}}, d0=18, setup=mv_setup(52))],
                         "our-pinch")                                                           # the dip lands on 42
        return a and b, da + " ## " + db

    def nr_selfhurt():
        return all_excl([pair({"mv": (36, FIRST[e], 0, 0)}) for e in sorted(F4_SELF_HURT)], "foe-self-hurt-move")

    def nr_falseswipe_edge():
        return all_excl([pair({"foe": {"hp": cmax, "maxhp": 200}}, setup=mv_setup(206))], "C:false-swipe-hp")

    def nr_unobservable():
        return all_excl([tko(foe_move=FIRST[e]) for e in sorted(SELF_STATE)], "foe-after-unobservable")

    def nr_profile():
        return all_excl([pair(a={"foe": {"ability": 47}}), pair(a={"foe": {"def_": 60}}),
                         pair(a={"foe": {"spd": 60}})], "foe-profile-changed")

    def nr_ooze():
        return all_excl([pair({"me": {"ability": 64}, "s3": (0x4, 0)}, {"s3": (0, 0)}),
                         *[pair({"me": {"ability": 64}, "mv": (36, FIRST[e], 0, 0)}) for e in sorted(DRAIN)]],
                        "our-liquid-ooze")

    def nr_facade_sleep():
        return all_excl([pair(None, {"me": {"status1": 0x2}}, setup=mv_setup(263))], "our-status-changed-guts-facade")

    def nr_selfcheck_halves():
        mis = {"foe": {"hp": 30}}
        cases = {
            "held item at BEFORE only (a consumed berry)": (pair({"foe": {"item": 139}}, {"foe": {"item": 0, "hp": 30}}),
                                                            "n/a: foe held item"),
            "the foe's Absorb": (pair({"mv": (36, 71, 0, 0)}, mis), "n/a: foe drain or heal move"),
            "Leech Seed on us at BEFORE only": (pair({"s3": (0x4, 0)}, {"s3": (0, 0), **mis}), "n/a: leech seed on us"),
            "Leech Seed on us at AFTER only": (pair(None, {"s3": (0x4, 0), **mis}), "n/a: leech seed on us"),
            "poisoned at AFTER only": (pair(None, {"foe": {"status1": 0x8, "hp": 30}}), "n/a: end-of-turn tick"),
            "foe seeded at AFTER": (pair(None, {"s3": (0, 0x4), **mis}), "n/a: end-of-turn tick"),
            "foe rooted at AFTER": (pair(None, {"s3": (0, 0x400), **mis}), "n/a: end-of-turn tick"),
            "foe cursed": (pair(None, {"foe": {"status2": 0x10000000, "hp": 30}}), "n/a: end-of-turn tick"),
            "foe nightmare": (pair(None, {"foe": {"status2": 0x8000000, "hp": 30}}), "n/a: end-of-turn tick"),
            "foe wrapped": (pair(None, {"foe": {"status2": 0x4000, "hp": 30}}), "n/a: end-of-turn tick"),
            "foe substitute": (pair(None, {"foe": {"status2": 0x1000000, "hp": 30}}), "n/a: end-of-turn tick"),
            "weather at AFTER only": (pair(None, {"weather": 8, **mis}), "n/a: end-of-turn tick"),
            "a disagreement of exactly 1": (pair(a={"foe": {"hp": 17}}), "DISAGREE"),
        }
        got = {k: one(x)[0].selfcheck for k, (x, _w) in cases.items()}
        bad = {k: g for k, g in got.items() if g != cases[k][1]}
        return not bad, str(bad)

    def nr_same_turn_entry():
        v = one(pair(a={"t": 0}))[0]
        return v.status == REJ and v.reasons == ("turn-gap",), vtxt(v)

    def nr_tko_identity():
        slot2 = one(tko(a={"party": ((KOFF2["pid"], 55), (0x1234, 40), (KOFF1["pid"], 0), (0, 0), (0, 0), (0, 0))}))[0]
        edge = one(tko(obs=55))[0]                      # Δbide == the old foe's HP exactly: still a KO
        return (slot2.status == ACC and slot2.kind == "trainer KO" and edge.status == ACC), \
            f"{vtxt(slot2)} || {vtxt(edge)}"

    def nr_tko_after_ff():
        return all_excl([tko(a={"ff": (1, 0)})], "our-flash-fire")

    def nr_accept_kinds():
        over = cmax + A().ACCEPT_MARGIN + 1
        cases = {
            "battle-end KO": pair({"t": 3, "foe": {"hp": 100, "maxhp": 200}}, obs=over, kind="end"),
            "trainer KO": tko(obs=170),
            "wild": pair(merge(BIG, {"flags": 0x4}), obs=over),
            "Tier B (Ember)": pair(BIG, obs=over, setup=mv_setup(52)),
            "Tier C (Surf)": pair(BIG, obs=over, setup=mv_setup(57)),
        }
        got = {}
        for k, lines in cases.items():
            rep = audit(lines)
            got[k] = (rep.acceptance, [v.status for v in rep.verdicts], [v.kind for v in rep.verdicts])
        return all(g[0] == "FAIL" and g[1] == [ACC] for g in got.values()), str(got)

    def nr_output_edges():
        at_min = audit(pair(obs=56))
        a = one(pair(obs=56))[0].tags == () and _acc_nums(at_min)[5] == "0"
        charged = audit(pair({"s3": (0x200, 0), "foe": {"hp": 200, "maxhp": 200}}, obs=cmax + 8, setup=mv_setup(209)))
        b = _acc_nums(charged)[4] == "0"
        ko = audit(pair(BIG, obs=70, frame=10) + pair({"t": 3, "foe": {"hp": 100, "maxhp": 200}}, obs=134, kind="end",
                                                      frame=20))
        c = _acc_nums(ko)[1] == "+2"
        return a and b and c, f"at-min {a} charged {b} ko {c} {_acc_nums(ko)}"

    def nr_hp_mystery_skip():
        got = A().hidden_power_type(ivs(30, 31, 30, 30, 30, 31))
        return got == "Fire", got                       # type bits 34 -> 9 (TYPE_MYSTERY) -> skipped to 10

    def nr_port_edges():
        rep = audit(pair(BIG, obs=34, frame=10) + pair(BIG, obs=88, frame=20))   # exactly the port's [34, 88] ends
        got = A().port_control(rep.hits)
        return len(rep.hits) == 2 and got[0].endswith(" 0 outside the port's [non-crit min, crit max]"), str(got)

    def nr_whitelist_table():
        t = A().tier_of
        bad = []
        for e, i in sorted(FIRST.items()):
            if i in (57, 165):
                continue
            want = "A" if (e in F2_A or STAT_HIT.search(e)) else "B" if e in F2_B else "C" if e in F2_C else "OUT"
            got = t(i, e)
            if got != want:
                bad.append((e, got, want))
        return not bad and t(57, "HIT") == "C" and t(165, "RECOIL") == "OUT", str(bad)

    def nr_parser():
        b, a = CLEAN
        bad = [b.replace(" t=0 ", " t=0 t=0 ", 1),                                  # a repeated field
               a.replace(" kind=entry ", " kind=bogus ", 1),                        # an AFTER kind outside the contract
               a.rsplit(",", 1)[0],                                                  # a party of 5
               re.sub(r"( dis=[0-9a-f]{54})[0-9a-f]{2},", r"\1,", b),                # a truncated dis
               re.sub(r" pred=\S+ base=\S+", " pred=err: base=none", b),             # pred=err with no name
               "f5 [DMGAUDIT] ERR v=1 where=entry err=KeyError"]                     # an ERR where outside the contract
        got = [(r.raw_count, r.parsed_count, r.exit_code) for r in (audit([ctl(1)] + CLEAN + [x]) for x in bad)]
        return all(g == (4, 3, 3) for g in got), str(got)

    # ------------------------------------------------------------------ production rows (the pass), with the rebinding
    def np_fields():
        d, st = Dm(), real_state()
        with dworld(badges=("BADGE01_GET", "BADGE08_GET")) as log:
            d.on_selection_exit(st)
            d.on_selection_entry()
        msgs = [m for _c, m in log.events]
        b = A().parse_line(f"f1 [DMGAUDIT] {msgs[0]}")
        a = A().parse_line(f"f2 [DMGAUDIT] {msgs[1]}")
        want = dict(t=5, out=0, flags=0x800C, act=(0, 1, 254, 253), mv=(36, 336, 7, 8), bide=(27201, -5, 297, 3722),
                    weather=0x108, side=(0x10, 0x3), s3=(0x20000, 0x40004), ff=(1, 0x100))
        bad = [(k, getattr(r, k), w) for r in (b, a) for k, w in want.items() if getattr(r, k) != w]
        if (b.mons[0].pid, b.mons[1].pid) != (ME["pid"], FOE["pid"]):
            bad.append(("mons", b.mons[0].pid, b.mons[1].pid))
        if _field(msgs[0], "dis") != bytes(range(0x1C)).hex() + "," + bytes(range(0x1C, 0x38)).hex():
            bad.append(("dis", (_field(msgs[0], "dis") or "")[:20]))
        if a.party != ((FOE["pid"], 83), (0x00157F88, 94)) + ZERO6[:4]:
            bad.append(("party", a.party[:2]))
        if b.badges != 0b10000001:
            bad.append(("badges", b.badges))
        # the inner EWRAM guard: a flags pointer outside EWRAM -> ff=null, nothing dereferenced through it
        with dworld(mem=distinct_mem(flags_ptr=0x08000000)) as log2:
            d.on_selection_exit(st)
        ff2 = _field(log2.events[0][1], "ff") if log2.events else None
        if ff2 != "null" or any(x >= 0x08000000 for x in log2.emu):
            bad.append(("ff guard", ff2, [hex(x) for x in log2.emu]))
        return not bad, str(bad)

    def np_pred_exact():
        from modules.pokemon import get_move_by_index
        d, st = Dm(), staged_state()
        u = modules.battle_strategies._util.BattleStrategyUtil(st)
        mv = get_move_by_index(36)
        att, dfn = st.own_side.left_battler, st.opponent.left_battler
        plain, crit = u.calculate_move_damage_range(mv, att, dfn), u.calculate_move_damage_range(mv, att, dfn, True)
        want_pred = f"{plain.min},{plain.max},{crit.min},{crit.max}"
        want_base = (f"{u._calculate_base_move_damage(mv, att, dfn, False)},"
                     f"{u._calculate_base_move_damage(mv, att, dfn, True)}")
        swapped = u.calculate_move_damage_range(mv, dfn, att)
        with dworld() as log:
            d.on_selection_exit(st)
        msg = log.events[0][1] if log.events else ""
        got = (_field(msg, "pred"), _field(msg, "base"))
        discriminates = (crit.max != plain.max and (swapped.min, swapped.max) != (plain.min, plain.max)
                         and want_base.split(",")[0] != want_base.split(",")[1])
        return got == (want_pred, want_base) and discriminates and log.gbs == [], \
            f"got {got} want {(want_pred, want_base)} discriminates {discriminates} gbs {len(log.gbs)}"

    def np_exit_guard():
        d, out = Dm(), []
        for cb, active in (("HandleTurnActionSelectionState", True), ("sub_8012324", True),
                           ("SetActionsAndBattlersTurnOrder", False)):
            with dworld(callback=cb, active=active) as log:
                d.on_selection_exit(real_state())
                out.append((cb, active, len(log.events), d._pending))
        return all(n == 0 and p is False for _c, _a, n, p in out), str(out)

    def np_pending():
        d, st, kinds = Dm(), real_state(), {}
        with dworld(pending=True) as log:              # a stale BEFORE from an abandoned battle
            d.on_battle_start()
            d.on_selection_entry()
            kinds["stale"] = [m.split()[0] for _c, m in log.events]
        with dworld() as log:
            d.on_battle_start()
            d.on_selection_entry()                       # the battle's first entry: nothing pending
            d.on_selection_exit(st)
            d.on_selection_entry()
            d.on_selection_entry()                       # a re-entry within the same selection
            d.on_battle_end()                            # nothing pending any more
            kinds["seq"] = [m.split()[0] for _c, m in log.events]
        return kinds == {"stale": ["CTL"], "seq": ["CTL", "BEFORE", "AFTER"]}, str(kinds)

    def np_raise():
        d, st = Dm(), real_state()
        got, raised, pend = [], [], None
        try:
            with dworld(raise_on="gBideDmg") as log:
                d.on_selection_exit(st)
                pend = d._pending
                d._pending = True
                d.on_selection_entry()
                d._pending = True
                d.on_battle_end()
                got = [m for _c, m in log.events]
        except Exception as e:  # noqa: BLE001 - a hook that raises is exactly what this row catches
            raised.append(type(e).__name__)
        rep = audit([f"f{i} [DMGAUDIT] {m}" for i, m in enumerate(got)])
        return (not raised and got == ["ERR v=1 where=before err=KeyError", "ERR v=1 where=after-entry err=KeyError",
                                       "ERR v=1 where=after-end err=KeyError"]
                and rep.raw_count == rep.parsed_count == 3 and pend is False), \
            f"raised {raised} got {got} parsed {rep.parsed_count} pending-after-a-failed-BEFORE {pend}"

    def np_end_no_ff():
        d = Dm()
        with dworld(pending=True) as log:
            d.on_battle_end()
        return ("gBattleResources" not in log.reads and log.emu == [] and bool(log.events)
                and _field(log.events[0][1], "ff") == "null"), f"reads {log.reads} emu {log.emu}"

    def np_ff_null_resources():
        d, out = Dm(), []
        for res in (0, 0x03000000):
            syms = distinct_syms()
            syms["gBattleResources"] = struct.pack("<I", res)
            with dworld(syms=syms) as log:
                d.on_selection_exit(real_state())
            out.append((hex(res), _field(log.events[0][1], "ff") if log.events else None, list(log.emu)))
        return all(ff == "null" and emu == [] for _r, ff, emu in out), str(out)

    def np_flag_values():
        d, out = Dm(), []
        for val in ("0", "true", " "):
            with dworld(flag=val, pending=True) as log:
                d.on_battle_start()
                d.on_selection_exit(real_state())
                d.on_selection_entry()
                d.on_battle_end()
                out.append((val, len(log.reads), len(log.events)))
        return all(r == 0 and e == 0 for _v, r, e in out), str(out)

    def np_pred_err():
        d = Dm()
        with dworld(calc_raise=True) as log:
            d.on_selection_exit(real_state())
        msg = log.events[0][1] if log.events else ""
        return " pred=err:ZeroDivisionError base=none eff=RECOIL" in msg, msg[-60:]

    # ------------------------------------------------------------------ hook-file rows (AST)
    def nh_gbs_count():
        t = ast.parse(srcs["bas"])
        n = sum(1 for x in ast.walk(t) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                and x.func.id == "get_battle_state")
        return n == 5, f"get_battle_state() calls in BAS: {n} (5 at the base commit 241929d7 and now)"

    def nh_no_dmgaudit_literal():
        hits = [k for k in ("bas", "bh") for x in ast.walk(ast.parse(srcs[k]))
                if isinstance(x, ast.Constant) and isinstance(x.value, str) and "DMGAUDIT" in x.value]
        return not hits, str(hits)

    cases = [
        ("NR-faint-reset a battle-end KO whose AFTER foe record is RESET (ability 0, stages neutral, item 0): ACCEPTED",
         nr_faint_reset),
        ("NR-faint-harden the same, the foe having chosen Harden: foe-after-unobservable", nr_faint_harden),
        ("NR-hp-rolled-type Hidden Power's ROLLED type drives the pinch (per read and the dip) and the sports",
         nr_hp_rolled_type),
        ("NR-sport the foe's Water Sport, our Mud Sport (Spark), the foe's at AFTER", nr_sport),
        ("NR-twister Twister vs a foe in the air", nr_twister),
        ("NR-counters every confusion counter value and every wrap counter value", nr_counters),
        ("NR-foestatus every status1 kind (sleep, freeze, paralysis, toxic, burn) is foe-status", nr_foestatus),
        ("NR-brick Brick Break vs Light Screen", nr_brick),
        ("NR-pinch-edges HP exactly maxHP/3, at AFTER and by the dip", nr_pinch_edges),
        ("NR-selfhurt every F4 self-hurt effect (the first move of each)", nr_selfhurt),
        ("NR-falseswipe-edge False Swipe with the foe's HP exactly crit_max", nr_falseswipe_edge),
        ("NR-unobservable a trainer KO after each FOE_SELF_STATE move", nr_unobservable),
        ("NR-profile the foe's ability, Def, SpD changed", nr_profile),
        ("NR-ooze Liquid Ooze: Leech Seed on us at BEFORE only; the foe's Absorb and Dream Eater", nr_ooze),
        ("NR-facade-sleep Facade with our status going 0 -> sleep", nr_facade_sleep),
        ("NR-selfcheck-halves each self-check exclusion at the read that carries it; a disagreement of 1",
         nr_selfcheck_halves),
        ("NR-same-turn-entry an entry read with the counter unchanged: turn-gap", nr_same_turn_entry),
        ("NR-tko-identity the old PID found in party slot 2; Δbide == its HP exactly", nr_tko_identity),
        ("NR-tko-after-ff a trainer KO still judges OUR Flash Fire at AFTER", nr_tko_after_ff),
        ("NR-accept-kinds an over-bound hit FAILS as a battle-end KO, a trainer KO, wild, Tier B, Tier C",
         nr_accept_kinds),
        ("NR-output-edges obs == min untagged; the charged bound (+8) edge; max(obs-cmax) over a KO", nr_output_edges),
        ("NR-hp-mystery-skip a Hidden Power roll of 9 skips TYPE_MYSTERY (Fire)", nr_hp_mystery_skip),
        ("NR-port-edges observations exactly at the port's ends are inside", nr_port_edges),
        ("NR-whitelist-table every moves.json effect's tier equals the gate's OWN literal F2 lists", nr_whitelist_table),
        ("NR-parser 6 more contract deviations count raw, not parsed (exit 3)", nr_parser),
        ("NP-fields distinct bytes in every RAW field: both lines parsed and every field asserted; badges; the "
         "inner EWRAM guard", np_fields),
        ("NP-pred-exact pred and base equal the calculator's own on a STAGED fixture (foe Def +2, base != bcrit)",
         np_pred_exact),
        ("NP-exit-guard no BEFORE while selecting (both states) or when the battle is inactive", np_exit_guard),
        ("NP-pending a stale BEFORE is dropped; the first entry, a re-entry and the end log nothing without one",
         np_pending),
        ("NP-raise a read failure is ONE ERR line per hook, never raised, never leaves a BEFORE pending", np_raise),
        ("NP-end-no-ff the battle-end read never touches gBattleResources (ff=null)", np_end_no_ff),
        ("NP-ff-null-resources a NULL or non-EWRAM gBattleResources: ff=null, nothing dereferenced",
         np_ff_null_resources),
        ("NP-flag-values '0', 'true', ' ' are OFF: no read, no line", np_flag_values),
        ("NP-pred-err a raising calculator logs pred=err:<Name> base=none", np_pred_err),
        ("NH-gbs-count BAS holds exactly 5 get_battle_state() calls (the base commit's count: step 11 added none)",
         nh_gbs_count),
        ("NH-no-dmgaudit-literal no string in BAS or the battle handler contains DMGAUDIT", nh_no_dmgaudit_literal),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


def all_rows(tag, srcs):
    return set(i_rows(tag) + p_rows(tag) + s_rows(tag) + w_rows(tag) + r_rows(tag) + q_rows(tag) + g_rows(tag)
               + c_rows(tag) + x_rows(tag) + o_rows(tag) + pc_rows(tag) + t_rows(tag) + pin_rows(tag, srcs)
               + n_rows(tag, srcs))


R_AFTER = {f"R{i:02d}a" for i in range(1, 22)}

#: The mutants: (label, old, new, the EXACT set of rows it must turn red). Each set was derived row by row from the
#: rows above and written BEFORE the gate's first mutant run.
CASES: list = [
    # --- the acceptance
    ("M01 '>=' for '>' in the acceptance bound -> I5 X3 X7 (a sample exactly at crit_max + margin)",
     "    return obs > crit_max + margin", "    return obs >= crit_max + margin", {"I5", "X3", "X7"}),
    ("M02 excluded strata counted in the verdict -> X2 X5 T1",
     "    hits = [v for v in verdicts if v.status == ACCEPTED]",
     "    hits = [v for v in verdicts if v.status in (ACCEPTED, EXCLUDED) and v.pred is not None "
     "and (v.d_bide or 0) > 0]", {"X2", "X5", "T1"}),
    ("M03 the 300 floor ignored -> I1 I5 X4 X5 O1 T1",
     "    if len(hits) < MIN_SAMPLES:", "    if False:", {"I1", "I5", "X4", "X5", "O1", "T1"}),
    ("M04 INSUFFICIENT decided before FAIL (one over-bound hit reads INSUFFICIENT) -> I5 X6 NR-accept-kinds",
     "    if over:\n        return FAIL, hits, over\n    if len(hits) < MIN_SAMPLES:\n"
     "        return INSUFFICIENT, hits, over\n",
     "    if len(hits) < MIN_SAMPLES:\n        return INSUFFICIENT, hits, over\n    if over:\n"
     "        return FAIL, hits, over\n", {"I5", "X6", "NR-accept-kinds"}),
    # --- the pairing
    ("M05 pairing on turn+1 only (no battle-end pair) -> P1 P2 P3 C4 T1 NR-faint-* NR-accept-kinds NR-output-edges",
     "        pairing = _end_pairing(b, a)", "        pairing = _entry_pairing(b, a)",
     {"P1", "P2", "P3", "C4", "T1", "NR-faint-reset", "NR-faint-harden", "NR-accept-kinds", "NR-output-edges"}),
    ("M06 the foe's identity on SPECIES only -> P4 P5 P6 P7 P7a G09 G10 G11 T1 NR-unobservable NR-tko-identity",
     "    same_foe = foe_b.pid == foe_a.pid", "    same_foe = foe_b.species == foe_a.species",
     {"P4", "P5", "P6", "P7", "P7a", "G09", "G10", "G11", "T1", "NR-unobservable", "NR-tko-identity"}),
    ("M07 OUR identity on species only -> S4",
     "    same_me = me_b.pid == me_a.pid", "    same_me = me_b.species == me_a.species", {"S4"}),
    ("M08 the latest BEFORE does not win (the first stays pending) -> P9",
     "            pending = r\n        elif r.kind == \"AFTER\":",
     "            pending = pending if pending is not None else r\n        elif r.kind == \"AFTER\":", {"P9"}),
    ("M09 a CTL does not clear a pending BEFORE -> P10",
     "        if r.kind == \"CTL\":", "        if r.kind == \"CTL\" and False:", {"P10"}),
    ("M10 the trainer KO's Δbide >= HP check dropped -> P5",
     "    if d_bide < old.hp:", "    if False:", {"P5"}),
    ("M11 the trainer KO's old-PID party HP 0 check dropped -> P6",
     "    if not any(pid == old.pid and hp == 0 for pid, hp in a.party):", "    if False:", {"P6"}),
    ("M12 the trainer KO's Spikes check dropped -> P7 P7a",
     "    if (b.side[1] | a.side[1]) & SIDE_SPIKES:", "    if False:", {"P7", "P7a"}),
    # --- the sample
    ("M13 the PP check by SLOT (the slot whose PP dropped) instead of move id -> S3",
     "    return me_b.pp[me_b.moves.index(move_id)] - me_a.pp[me_a.moves.index(move_id)]",
     "    return max(x - y for x, y in zip(me_b.pp, me_a.pp))", {"S3"}),
    ("M14 a negative Δbide is not an instrument fault -> S7",
     "    if v.d_bide < 0:", "    if False:", {"S7"}),
    ("M15 a Δbide of 0 is not 'no damage' -> S8 T1",
     "    if v.d_bide == 0:", "    if False:", {"S8", "T1"}),
    ("M16 doubles not stratified -> S9",
     "    if b.flags & FLAG_DOUBLE:\n        reasons.add(\"doubles\")", "    if False:\n        reasons.add(\"doubles\")",
     {"S9"}),
    ("M17 max == 0 not stratified -> S10",
     "    elif b.pred[1] == 0:", "    elif False:", {"S10"}),
    # --- the strata
    ("M18 every stratum check evaluated at BEFORE only -> R01a..R21a G12 NR-sport NR-pinch-edges NR-hp-rolled-type NR-tko-after-ff",
     "    reasons |= _state_reasons(a, v.move, mv, foe_ok=not foe_fainted)\n", "",
     R_AFTER | {"G12", "NR-sport", "NR-pinch-edges", "NR-hp-rolled-type", "NR-tko-after-ff"}),
    ("M19 a trainer KO's REPLACEMENT judged by the per-mon foe checks -> G11",
     "    reasons |= _state_reasons(a, v.move, mv, foe_ok=not foe_fainted)",
     "    reasons |= _state_reasons(a, v.move, mv, foe_ok=True)", {"G11"}),
    ("M20 a Tier B trainer KO is not unobservable -> G09",
     "        if tier == \"B\" or foe_eff in FOE_SELF_STATE:", "        if foe_eff in FOE_SELF_STATE:", {"G09"}),
    ("M21 the pinch dip (HP before - Δbide[0]) not checked -> G07 NR-pinch-edges NR-hp-rolled-type",
     "    if me_b.hp - d_bide0 <= me_b.maxhp // 3 and PINCH.get(me_b.ability) == damage_type(move_id, me_b):",
     "    if False:", {"G07", "NR-pinch-edges", "NR-hp-rolled-type"}),
    ("M22 the foe's Def/SpD stage change not stratified -> G01",
     "            out.add(\"foe-def-stage-changed\")", "            pass", {"G01"}),
    ("M23 the foe's chosen move 0 read as a clean move -> Q02 T1",
     "            out.add(\"foe-move-zero\")", "            pass", {"Q02", "T1"}),
    # --- the whitelist
    ("M24 Surf keyed on its effect (HIT -> Tier A) -> W1 W3 NR-whitelist-table",
     "    if move_id == MOVE_SURF:\n        return \"C\"", "    if False:\n        return \"C\"", {"W1", "W3", "NR-whitelist-table"}),
    ("M25 Struggle keyed on its effect (RECOIL -> Tier A) -> W1 NR-whitelist-table",
     "    if move_id == MOVE_STRUGGLE:", "    if False:", {"W1", "NR-whitelist-table"}),
    # --- the self-check
    ("M26 the self-check keeps the foe's item action (the masked heal) -> C2 T1 T2",
     "    if b.act[1] == ACTION_USE_ITEM:\n        return \"n/a: foe item action\"",
     "    if False:\n        return \"n/a: foe item action\"", {"C2", "T1", "T2"}),
    ("M27 the self-check keeps a held item at BEFORE -> C3 T1 T2 NR-selfcheck-halves",
     "    if foe_b.item:\n        return \"n/a: foe held item\"", "    if False:\n        return \"n/a: foe held item\"",
     {"C3", "T1", "T2", "NR-selfcheck-halves"}),
    # --- tags and the instrument
    ("M28 the crit-ambiguity tag includes obs == max -> S12",
     "    if hi < obs <= cmax:", "    if hi <= obs <= cmax:", {"S12"}),
    ("M29 the raw count taken from the parsed records (a mismatch hidden) -> I2 NR-parser",
     "    rep.raw_count = sum(1 for ln in lines if TAG in ln)", "    rep.raw_count = len(recs)", {"I2", "NR-parser"}),
    ("M30 the logger's cap marker ignored -> I3",
     "    rep.capped = any(CAP_MARKER in ln for ln in lines)", "    rep.capped = False", {"I3"}),
    # --- the independent port control's adapter (added with the base= field; sets written before their first run)
    ("MP1 the adapter passes Hidden Power's LISTED type (Normal) as move_type -> PC5",
     "    rolled = hidden_power_type(me.ivs) if v.move == MOVE_HIDDEN_POWER else listed", "    rolled = listed", {"PC5"}),
    ("MP2 Charge read from the ROLLED type (a Hidden Power that rolled Electric gets doubled) -> PC5",
     "charge_listed_electric=bool(b.s3[0] & S3_CHARGED) and listed == \"Electric\",",
     "charge_listed_electric=bool(b.s3[0] & S3_CHARGED) and rolled == \"Electric\",", {"PC5"}),
    ("MP3 the crit replayed from b instead of bcrit -> PC3 PC4 PC5 PC6 PC7 NR-port-edges",
     "dict(B=b.base[1], crit=True, **common)", "dict(B=b.base[0], crit=True, **common)",
     {"PC3", "PC4", "PC5", "PC6", "PC7", "NR-port-edges"}),
    ("MP4 the port's top taken from the NON-crit call -> PC3 PC4 PC5 PC6 PC7 NR-port-edges",
     "            _, hi = fn(**calls[1])", "            _, hi = fn(**calls[0])", {"PC3", "PC4", "PC5", "PC6", "PC7", "NR-port-edges"}),
    ("MP5 the foe's types passed in reversed order -> PC3",
     "defender_types_rom=(TYPE_NAMES[foe.type1], TYPE_NAMES[foe.type2]),",
     "defender_types_rom=(TYPE_NAMES[foe.type2], TYPE_NAMES[foe.type1]),", {"PC3"}),
    ("MP6 the defender's types taken from OUR record -> PC3 PC4 PC5 PC6 PC8",
     "defender_types_rom=(TYPE_NAMES[foe.type1], TYPE_NAMES[foe.type2]),",
     "defender_types_rom=(TYPE_NAMES[me.type1], TYPE_NAMES[me.type2]),", {"PC3", "PC4", "PC5", "PC6", "PC8"}),
    ("MP7 foresight never passed -> PC6",
     "foresight=bool(foe.status2 & S2_FORESIGHT))", "foresight=False)", {"PC6"}),
    ("MP8 an unreplayable record counted as replayed (inside) -> PC8",
     "            unreplayable.append(v.before.frame)\n            continue\n",
     "            lo, hi = 0, 10 ** 9\n", {"PC8"}),
    # --- the faint rule (DESIGN F6 ⚠) and Hidden Power's rolled type (added with them; sets written before their run)
    ("MF1 the faint rule dropped (only a changed PID skips the AFTER foe record) -> NR-faint-reset NR-faint-harden T1",
     "    foe_fainted = not same_foe or foe_a.hp == 0", "    foe_fainted = not same_foe",
     {"NR-faint-reset", "NR-faint-harden", "T1"}),
    ("MT1 the per-read pinch and the sports read the LISTED type -> NR-hp-rolled-type",
     "    eff, mtype = mv[\"effect\"], damage_type(move_id, me)", "    eff, mtype = mv[\"effect\"], mv[\"type\"]",
     {"NR-hp-rolled-type"}),
    ("MT2 the pinch DIP reads the LISTED type -> NR-hp-rolled-type",
     "PINCH.get(me_b.ability) == damage_type(move_id, me_b):", "PINCH.get(me_b.ability) == mv[\"type\"]:",
     {"NR-hp-rolled-type"}),
    # --- one mutant for each row no other mutant reached (so every row is shown to be able to turn red)
    ("MX1 CAP_MARKER is not the logger's text -> I3 I4",
     'CAP_MARKER = "event log size cap reached"', 'CAP_MARKER = "event log cap reached"', {"I3", "I4"}),
    ("MX2 ERR lines not reported -> I6",
     '    if rep.errs:\n        out.append(f"  ERR lines:', '    if False:\n        out.append(f"  ERR lines:', {"I6"}),
    ("MX3 the entry pairing never rejects -> P8 NR-same-turn-entry",
     '    return None if a.t == b.t + 1 else "turn-gap"', "    return None", {"P8", "NR-same-turn-entry"}),
    ("MX4 a BEFORE left at the log's end is dropped silently -> P11",
     '    if pending is not None:\n        verdicts.append(Verdict(before=pending, after=None, status=UNPAIRED, '
     'reasons=("no-after-at-log-end",)))\n', "", {"P11"}),
    ("MX5 wild and trainer swapped -> S1 S14 T1 O1",
     '    v.battle = "trainer" if b.flags & FLAG_TRAINER else "wild"',
     '    v.battle = "wild" if b.flags & FLAG_TRAINER else "trainer"', {"S1", "S14", "T1", "O1"}),
    ("MX6 an unchanged PP counts as run -> S2 S3 T1 O1",
     "    if drop < 1:", "    if drop < 0:", {"S2", "S3", "T1", "O1"}),
    ("MX7 a chosen move 0 is not 'not a move' -> S5",
     "    if b.act[0] != ACTION_USE_MOVE or v.move == 0:", "    if b.act[0] != ACTION_USE_MOVE:", {"S5"}),
    ("MX8 the not-in-moveset guard removed -> S6",
     "    if move_id not in me_b.moves or move_id not in me_a.moves:\n        return None\n", "", {"S6"}),
    ("MX9 no-prediction not stratified -> S11",
     '    if b.pred is None:\n        reasons.add("no-prediction")', '    if False:\n        reasons.add("no-prediction")',
     {"S11"}),
    ("MX10 the below-min tag dropped -> S13",
     '    if obs < lo:\n        out.append("below-noncrit-min")', '    if False:\n        out.append("below-noncrit-min")',
     {"S13"}),
    ("MX11 Tier C and Tier A overlap (HIT in both) -> W2",
     'TIER_C = frozenset({"EARTHQUAKE",', 'TIER_C = frozenset({"HIT", "EARTHQUAKE",', {"W2"}),
    ("MX12 Blaze keyed on Water -> R19b R19a G07 NR-pinch-edges",
     'PINCH = {65: "Grass", 66: "Fire",', 'PINCH = {65: "Grass", 66: "Water",',
     {"R19b", "R19a", "G07", "NR-pinch-edges"}),
    ("MX13 the foe's item action not stratified -> Q01 T1",
     '    if foe_act == ACTION_USE_ITEM:\n        out.add("foe-item-action")',
     '    if False:\n        out.add("foe-item-action")', {"Q01", "T1"}),
    ("MX14 EXPLOSION dropped from FOE_SELF_HURT -> Q03 NR-selfhurt T1",
     '"EXPLOSION", "MEMENTO"})', '"MEMENTO"})', {"Q03", "NR-selfhurt", "T1"}),
    ("MX15 ENDURE dropped from FOE_PROTECT -> Q05",
     'FOE_PROTECT = frozenset({"PROTECT", "ENDURE", "BIDE"})', 'FOE_PROTECT = frozenset({"PROTECT", "BIDE"})', {"Q05"}),
    ("MX16 Pursuit's condition dropped -> Q06",
     '    if mv["effect"] == "PURSUIT" and foe_act == ACTION_SWITCH:', "    if False:", {"Q06"}),
    ("MX17 False Swipe's condition dropped -> Q07 NR-falseswipe-edge",
     '    if mv["effect"] == "FALSE_SWIPE" and b.pred is not None and foe.hp <= b.pred[3]:', "    if False:",
     {"Q07", "NR-falseswipe-edge"}),
    ("MX18 Guts + burn dropped -> Q08",
     "    if me.ability == AB_GUTS and me.status1 & S1_BURN:", "    if False:", {"Q08"}),
    ("MX19 Marvel Scale on OUR side dropped -> Q09",
     "    if (foe.ability == AB_MARVEL_SCALE and foe.status1) or (me.ability == AB_MARVEL_SCALE and me.status1):",
     "    if foe.ability == AB_MARVEL_SCALE and foe.status1:", {"Q09"}),
    ("MX20 Air Lock's id off by one (76, Cacophony) -> Q10",
     "AB_CLOUD_NINE, AB_AIR_LOCK = 13, 77", "AB_CLOUD_NINE, AB_AIR_LOCK = 13, 76", {"Q10"}),
    ("MX21 persistent Flash Fire dropped -> Q11",
     '    if b.ff is not None and b.ff[0]:\n        out.add("persistent:flash-fire")',
     '    if False:\n        out.add("persistent:flash-fire")', {"Q11"}),
    ("MX22 foe-profile-changed dropped -> G02 NR-profile",
     '            out.add("foe-profile-changed")', "            pass", {"G02", "NR-profile"}),
    ("MX23 foe-screens-changed dropped -> G03",
     "    if (b.side[1] ^ a.side[1]) & SIDE_SCREENS:", "    if False:", {"G03"}),
    ("MX24 our-attack-stage-changed dropped -> G04",
     '        out.add("our-attack-stage-changed")', "        pass", {"G04"}),
    ("MX25 the status change counted with Facade only (Guts dropped) -> G05",
     '(me_b.ability == AB_GUTS or mv["effect"] == "FACADE")', '(mv["effect"] == "FACADE")', {"G05"}),
    ("MX26 Liquid Ooze's draining-move half dropped -> G08 NR-ooze",
     '            (b.act[1] == ACTION_USE_MOVE and move_info(b.mv[1])["effect"] in FOE_DRAIN)', "            False",
     {"G08", "NR-ooze"}),
    ("MX27 the self-check always agrees -> C1 T2 NR-selfcheck-halves O1",
     '    return "agree" if a.bide[1] - b.bide[1] == foe_b.hp - foe_a.hp else "DISAGREE"', '    return "agree"',
     {"C1", "T2", "NR-selfcheck-halves", "O1"}),
    ("MX28 the over list always empty -> I5 X1 X6 X7 NR-accept-kinds",
     "    over = [v for v in hits if over_bound(v.d_bide, v.pred[3], margin)]", "    over = []",
     {"I5", "X1", "X6", "X7", "NR-accept-kinds"}),
    ("MX29 max(obs/cmax) divided by the non-crit max -> O2",
     "    ratio = max(v.d_bide / v.pred[3] for v in hs)", "    ratio = max(v.d_bide / v.pred[1] for v in hs)", {"O2"}),
    ("MX30 a missing port module reported as nothing -> PC1",
     '    except ImportError as error:\n        return [f"port control: unavailable (no dmgcalc_port module: {error})"]',
     "    except ImportError:\n        return []", {"PC1"}),
    ("MX31 a port without after_base reported as nothing -> PC2",
     '    if fn is None:\n        return ["port control: unavailable (dmgcalc_port has no after_base)"]',
     "    if fn is None:\n        return []", {"PC2"}),
    ("MX32 Fire and Water swapped in TYPE_NAMES -> PC3 PC9 NR-hp-rolled-type NR-hp-mystery-skip",
     '"???", "Fire",\n              "Water",', '"???", "Water",\n              "Fire",',
     {"PC3", "PC9", "NR-hp-rolled-type", "NR-hp-mystery-skip"}),
    # --- a comment-only edit: NOTHING red
    ("M31 a comment edit naming the code turns NOTHING red",
     "#: Fewer clean whitelisted hits than this is INSUFFICIENT, never PASS (F4).",
     "#: (edited, a comment only: over_bound(obs, crit_max, margin) > and MIN_SAMPLES) Fewer clean whitelisted hits "
     "than this is INSUFFICIENT, never PASS (F4).", set()),
]


#: PRODUCTION mutants: (label, target, [(old, new), ...] applied in order, the EXACT red set). Target "dmgaudit" is
#: exec'd as `modules.dmgaudit` (and its text feeds the AST rows); "bas" / "bh" are TEXT edits of the hook files (AST
#: rows only). Never written to disk. Sets written before the gate's first production-mutant run.
PB = {f"PIN-b{i}" for i in range(1, 7)}
PROD_CASES: list = [
    ("PM1 the entry hook reads (the party) BEFORE its flag check -> PIN-a2 NP-flag-values", "dmgaudit",
     [('    """The first selection entry after a BEFORE: its AFTER (`kind=entry`)."""\n    global _pending\n',
       '    """The first selection entry after a BEFORE: its AFTER (`kind=entry`)."""\n    global _pending\n'
       '    _party()\n')], {"PIN-a2", "NP-flag-values"}),
    ("PM2 a get_battle_state() call added at the top of _prediction -> PIN-b1 PIN-c5 NP-pred-exact", "dmgaudit",
     [('    """`pred=` and `eff=` for the move the GAME records as our chosen move (never the strategy\'s index)."""\n',
       '    """`pred=` and `eff=` for the move the GAME records as our chosen move (never the strategy\'s index)."""\n'
       '    from modules.battle_state import get_battle_state\n    get_battle_state()\n')],
     {"PIN-b1", "PIN-c5", "NP-pred-exact"}),
    ("PM3 the category BATTLE -> PIN-b2 PIN-b5 PIN-b6 PIN-c6", "dmgaudit",
     [('    debug_logger.event(message, category="DMGAUDIT")', '    debug_logger.event(message, category="BATTLE")')],
     {"PIN-b2", "PIN-b5", "PIN-b6", "PIN-c6"}),
    ("PM4 the exit hook removed -> PIN-c2", "bas",
     [("    _dmgaudit.on_selection_exit(battle_state)\n", "")], {"PIN-c2"}),
    ("PM5 the exit hook moved INSIDE the while body -> PIN-c2", "bas",
     [("    # flag-gated, never raises.\n    _dmgaudit.on_selection_exit(battle_state)\n",
       "    # flag-gated, never raises.\n"),
      ('                raise RuntimeError(f"Invalid turn action: {action}")\n',
       '                raise RuntimeError(f"Invalid turn action: {action}")\n'
       '        _dmgaudit.on_selection_exit(battle_state)\n')], {"PIN-c2"}),
    ("PM6 on_battle_end() placed BEFORE the loop -> PIN-c4", "bh",
     [("    _dmgaudit.on_battle_end()\n", ""),
      ("    _dmgaudit.on_battle_start()\n", "    _dmgaudit.on_battle_end()\n    _dmgaudit.on_battle_start()\n")],
     {"PIN-c4"}),
    ("PM7 a comment in dmgaudit.py that NAMES get_battle_state turns NOTHING red", "dmgaudit",
     [("\n_pending = False\n", "\n# (a comment only) get_battle_state() / modules.battle_state.get_battle_state is never "
                               "called here\n_pending = False\n")], set()),
    ("PM8 the entry hook runs BEFORE battle_state = get_battle_state() -> PIN-c1", "bas",
     [("    battle_state = get_battle_state()\n    # design v2 step 11 (M1b): the AFTER of a pending `[DMGAUDIT]` "
       "BEFORE. Observe-only, flag-gated, never raises.\n    _dmgaudit.on_selection_entry()\n",
       "    _dmgaudit.on_selection_entry()\n    battle_state = get_battle_state()\n")], {"PIN-c1"}),
    ("PM9 the flag read ONCE at import, not per call -> PIN-b1..b6 and every NP row that needs the flag ON", "dmgaudit",
     [('def _on() -> bool:\n    return os.environ.get(FLAG, "").strip() == "1"\n',
       '_ON = os.environ.get(FLAG, "").strip() == "1"\n\n\ndef _on() -> bool:\n    return _ON\n')],
     PB | {"NP-fields", "NP-pred-exact", "NP-pending", "NP-raise", "NP-end-no-ff", "NP-ff-null-resources",
           "NP-pred-err"}),
    ("PM10 the FAULT switch ignored -> PIN-b4", "dmgaudit",
     [('    if os.environ.get(FAULT_BIDE0, "").strip() == "1":\n        bide4[1] = bide4[0]\n', "")], {"PIN-b4"}),
    ("PMX1 the start hook logs BEFORE its flag check -> PIN-a1 PIN-b2 PIN-b3 PIN-b5 NP-flag-values NP-pending",
     "dmgaudit",
     [('    """`battle_handler.handle_battle`, before its loop: the control line; any stale BEFORE is dropped."""\n'
       '    global _pending\n',
       '    """`battle_handler.handle_battle`, before its loop: the control line; any stale BEFORE is dropped."""\n'
       '    global _pending\n    _log("CTL v=1")\n')],
     {"PIN-a1", "PIN-b2", "PIN-b3", "PIN-b5", "NP-flag-values", "NP-pending"}),
    ("PMX2 the exit hook reads BEFORE its flag check -> PIN-a3 NP-flag-values", "dmgaudit",
     [('    final, no action run yet, so no HP has changed)."""\n    global _pending\n',
       '    final, no action run yet, so no HP has changed)."""\n    global _pending\n    _party()\n')],
     {"PIN-a3", "NP-flag-values"}),
    ("PMX3 the end hook reads BEFORE its flag check -> PIN-a4 NP-flag-values", "dmgaudit",
     [('    read: `gBattleResources` is freed by then (the Step-0 reads: NULL at every battle end)."""\n    global _pending\n',
       '    read: `gBattleResources` is freed by then (the Step-0 reads: NULL at every battle end)."""\n    global _pending\n'
       '    _party()\n')], {"PIN-a4", "NP-flag-values"}),
    ("PMX4 on_battle_start() removed -> PIN-c3", "bh", [("    _dmgaudit.on_battle_start()\n", "")], {"PIN-c3"}),
]

R_BEFORE_A33 = ({f"R{i:02d}b" for i in range(1, 22)} - {"R19b"}) | {"T1", "NR-sport", "NR-twister", "NR-counters",
                                                                     "NR-foestatus", "NR-brick", "NR-hp-rolled-type"}
SELF_HALVES = {"NR-selfcheck-halves"}
#: The ADVERSARIAL MUTANT PASS's mutants (2026-09-30; anchors copied verbatim from its mutants.py / wmuts.py). Each
#: red set was DERIVED BY HAND over every row, before the first run of these mutants against this gate. A44 and
#: A64 are left out: no row can catch them (A44 is equivalent for every prediction our calculator makes; A64 only
#: excludes MORE, which the design allows).
PASS_CASES: list = [
    ('A01 C:sport foe half dropped (only OUR s3 checked)', 'audit',
     [('    if mtype in ("Fire", "Electric") and (rd.s3[0] | (rd.s3[1] if foe_ok else 0)) & S3_SPORTS:', '    if mtype in ("Fire", "Electric") and rd.s3[0] & S3_SPORTS:')],
     {'NR-hp-rolled-type', 'NR-sport'}),
    ('A02 C:sport for Fire only (Electric dropped)', 'audit',
     [('    if mtype in ("Fire", "Electric") and (rd.s3[0]', '    if mtype == "Fire" and (rd.s3[0]')],
     {'NR-sport'}),
    ('A03 S3_SPORTS = Water Sport only (Mud Sport bit dropped)', 'audit',
     [('S3_SPORTS = 0x10000 | 0x20000', 'S3_SPORTS = 0x20000')],
     {'NR-sport'}),
    ("A04 Tier C Gust/Twister: Twister's condition dropped", 'audit',
     [('if eff in ("GUST", "TWISTER") and', 'if eff in ("GUST",) and')],
     {'NR-twister'}),
    ('A05 confusion mask 0x1 (not 0x7)', 'audit',
     [('S2_CONFUSION, S2_WRAPPED, S2_SUBSTITUTE = 0x7, 0xE000, 0x1000000', 'S2_CONFUSION, S2_WRAPPED, S2_SUBSTITUTE = 0x1, 0xE000, 0x1000000')],
     {'NR-counters'}),
    ('A06 wrapped mask 0x2000 (not 0xE000)', 'audit',
     [('S2_CONFUSION, S2_WRAPPED, S2_SUBSTITUTE = 0x7, 0xE000, 0x1000000', 'S2_CONFUSION, S2_WRAPPED, S2_SUBSTITUTE = 0x7, 0x2000, 0x1000000')],
     {'NR-counters', 'NR-selfcheck-halves'}),
    ('A07 foe-status only for ticking statuses (sleep/para/freeze admitted)', 'audit',
     [('        if foe.status1:\n            out.add("foe-status")', '        if foe.status1 & S1_TICKS:\n            out.add("foe-status")')],
     {'NR-foestatus'}),
    ('A08 Brick Break vs Reflect only (Light Screen dropped)', 'audit',
     [('if eff == "BRICK_BREAK" and rd.side[1] & SIDE_SCREENS:', 'if eff == "BRICK_BREAK" and rd.side[1] & 0x1:')],
     {'NR-brick'}),
    ("A09 per-read pinch '<' (hp == maxhp//3 admitted)", 'audit',
     [('    if me.hp <= me.maxhp // 3 and PINCH.get(me.ability) == mtype:', '    if me.hp < me.maxhp // 3 and PINCH.get(me.ability) == mtype:')],
     {'NR-pinch-edges'}),
    ("A10 pinch DIP '<'", 'audit',
     [('    if me_b.hp - d_bide0 <= me_b.maxhp // 3', '    if me_b.hp - d_bide0 < me_b.maxhp // 3')],
     {'NR-pinch-edges'}),
    ("A33 per-read strata at AFTER only (the BEFORE call removed; M18's mirror)", 'audit',
     [('    reasons |= _state_reasons(b, v.move, mv, foe_ok=True)\n', '')],
     R_BEFORE_A33),
    ("A61 field-level Tier C moved under foe_ok (skipped on a trainer KO's AFTER)", 'audit',
     [('    # Tier C, our half and the field\n    if eff == "FACADE"', '    # Tier C, our half and the field\n    if not foe_ok:\n        return out\n    if eff == "FACADE"')],
     {'NR-tko-after-ff'}),
    ('A11 FOE_SELF_HURT loses DOUBLE_EDGE', 'audit',
     [('FOE_SELF_HURT = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS",', 'FOE_SELF_HURT = frozenset({"RECOIL", "RECOIL_IF_MISS",')],
     {'NR-selfhurt'}),
    ('A12 FOE_SELF_HURT loses RECOIL_IF_MISS (Jump Kick crash)', 'audit',
     [('FOE_SELF_HURT = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS",', 'FOE_SELF_HURT = frozenset({"RECOIL", "DOUBLE_EDGE",')],
     {'NR-selfhurt'}),
    ('A13 FOE_SELF_HURT loses BELLY_DRUM', 'audit',
     [('"SUBSTITUTE", "BELLY_DRUM", "PAIN_SPLIT",', '"SUBSTITUTE", "PAIN_SPLIT",')],
     {'NR-selfhurt'}),
    ('A14 FOE_SELF_HURT loses PAIN_SPLIT', 'audit',
     [('"SUBSTITUTE", "BELLY_DRUM", "PAIN_SPLIT",', '"SUBSTITUTE", "BELLY_DRUM",')],
     {'NR-selfhurt'}),
    ('A15 FOE_SELF_HURT loses MEMENTO', 'audit',
     [('"EXPLOSION", "MEMENTO"})', '"EXPLOSION"})')],
     {'NR-selfhurt'}),
    ("A30 False Swipe '<' (foe hp == crit_max admitted)", 'audit',
     [('foe.hp <= b.pred[3]:', 'foe.hp < b.pred[3]:')],
     {'NR-falseswipe-edge'}),
    ('A62 foe-move-zero checked only when the foe did not switch (loosened: dropped for a foe item)', 'audit',
     [('        if foe_mv == 0:\n            out.add("foe-move-zero")', '        if foe_mv == 0 and b.mv[0] == 0:\n            out.add("foe-move-zero")')],
     {'Q02', 'T1'}),
    ("A63 Ghost Curse read from the foe's AFTER types? no: Curse self-hurt for ANY type (conservative)", 'audit',
     [('(feff == "CURSE" and TYPE_GHOST in (foe.type1, foe.type2))', '(feff == "CURSE")')],
     {'Q04'}),
    ('A16 FOE_SELF_STATE loses SEMI_INVULNERABLE', 'audit',
     [('"PSYCH_UP", "HAZE", "SEMI_INVULNERABLE", "MINIMIZE",', '"PSYCH_UP", "HAZE", "MINIMIZE",')],
     {'NR-unobservable'}),
    ('A17 FOE_SELF_STATE loses DEFENSE_UP_2 (Barrier/Iron Defense)', 'audit',
     [('FOE_SELF_STATE = frozenset({"DEFENSE_UP", "DEFENSE_UP_2", ', 'FOE_SELF_STATE = frozenset({"DEFENSE_UP", ')],
     {'NR-unobservable'}),
    ('A18 foe-profile-changed on types only (ability/Def/SpD dropped)', 'audit',
     [('    if (foe_b.type1, foe_b.type2, foe_b.ability, foe_b.def_, foe_b.spd) != \\\n                (foe_a.type1, foe_a.type2, foe_a.ability, foe_a.def_, foe_a.spd):', '    if (foe_b.type1, foe_b.type2) != \\\n                (foe_a.type1, foe_a.type2):')],
     {'NR-profile'}),
    ('A19 Liquid Ooze: Leech Seed on us read at AFTER only', 'audit',
     [('            or (b.s3[0] | a.s3[0]) & S3_LEECHSEED):', '            or a.s3[0] & S3_LEECHSEED):')],
     {'NR-ooze'}),
    ('A20 FOE_DRAIN loses DREAM_EATER', 'audit',
     [('FOE_DRAIN = frozenset({"ABSORB", "DREAM_EATER", "LEECH_SEED"})', 'FOE_DRAIN = frozenset({"ABSORB", "LEECH_SEED"})')],
     {'NR-ooze'}),
    ('A21 status change counted with Guts only (Facade dropped)', 'audit',
     [('(me_b.ability == AB_GUTS or mv["effect"] == "FACADE")', '(me_b.ability == AB_GUTS)')],
     {'NR-facade-sleep'}),
    ('A65 weather-changed dropped', 'audit',
     [('    if b.weather != a.weather:\n        out.add("weather-changed")', '    if False:\n        out.add("weather-changed")')],
     {'G06'}),
    ('A22 self-check held item read at AFTER (not BEFORE)', 'audit',
     [('    if foe_b.item:\n        return "n/a: foe held item"', '    if foe_a.item:\n        return "n/a: foe held item"')],
     SELF_HALVES),
    ('A23 self-check: foe DRAIN dropped (heal only)', 'audit',
     [('in (FOE_DRAIN | FOE_HEAL):', 'in FOE_HEAL:')],
     SELF_HALVES),
    ('A24 self-check: Leech Seed on us at BEFORE only', 'audit',
     [('    if (b.s3[0] | a.s3[0]) & S3_LEECHSEED:\n        return "n/a: leech seed on us"', '    if b.s3[0] & S3_LEECHSEED:\n        return "n/a: leech seed on us"')],
     SELF_HALVES),
    ('A24b self-check: Leech Seed on us at AFTER only', 'audit',
     [('    if (b.s3[0] | a.s3[0]) & S3_LEECHSEED:\n        return "n/a: leech seed on us"', '    if a.s3[0] & S3_LEECHSEED:\n        return "n/a: leech seed on us"')],
     SELF_HALVES),
    ('A25 self-check: tick status at BEFORE only', 'audit',
     [('    if ((foe_b.status1 | foe_a.status1) & S1_TICKS', '    if (foe_b.status1 & S1_TICKS')],
     SELF_HALVES),
    ('A26 self-check: foe Leech Seed / Ingrain dropped', 'audit',
     [('or (b.s3[1] | a.s3[1]) & (S3_LEECHSEED | S3_ROOTED)', 'or False')],
     SELF_HALVES),
    ('A27 self-check: foe status2 ticks (curse/nightmare/wrap/sub) dropped', 'audit',
     [('            or (foe_b.status2 | foe_a.status2) & (S2_CURSED | S2_NIGHTMARE | S2_WRAPPED | S2_SUBSTITUTE)', '            or False')],
     SELF_HALVES),
    ('A28 self-check: weather at BEFORE only', 'audit',
     [('            or b.weather or a.weather):', '            or b.weather):')],
     SELF_HALVES),
    ('A50 self-check tolerance +-1', 'audit',
     [('    return "agree" if a.bide[1] - b.bide[1] == foe_b.hp - foe_a.hp else "DISAGREE"', '    return "agree" if abs((a.bide[1] - b.bide[1]) - (foe_b.hp - foe_a.hp)) <= 1 else "DISAGREE"')],
     SELF_HALVES),
    ('A29 entry pairing loosened: counter T or T+1', 'audit',
     [('    return None if a.t == b.t + 1 else "turn-gap"', '    return None if a.t - b.t in (0, 1) else "turn-gap"')],
     {'NR-same-turn-entry'}),
    ("A31 trainer KO: old mon's party HP read by POSITION (slot 0)", 'audit',
     [('    if not any(pid == old.pid and hp == 0 for pid, hp in a.party):', '    if a.party[0] != (old.pid, 0):')],
     {'NR-tko-identity'}),
    ('A32 trainer KO: d_bide <= hp rejected (boundary, conservative)', 'audit',
     [('    if d_bide < old.hp:', '    if d_bide <= old.hp:')],
     {'NR-tko-identity'}),
    ("A66 trainer KO: the 'old PID' taken from the AFTER foe (identity check vacuous)", 'audit',
     [('    if not any(pid == old.pid and hp == 0 for pid, hp in a.party):', '    if not any(hp == 0 for pid, hp in a.party if pid != a.mons[1].pid):')],
     {'P6'}),
    ('A67 end pairing: outcome check dropped', 'audit',
     [('    if a.out == 0:\n        return "end-without-outcome"', '    if False:\n        return "end-without-outcome"')],
     {'P2'}),
    ('A46 acceptance counts Tier A only (an over in Tier B/C ignored)', 'audit',
     [('    hits = [v for v in verdicts if v.status == ACCEPTED]', '    hits = [v for v in verdicts if v.status == ACCEPTED and v.tier == "A"]')],
     {'NR-accept-kinds'}),
    ('A47 acceptance: over checked on non-KO turns only', 'audit',
     [('    over = [v for v in hits if over_bound(v.d_bide, v.pred[3], margin)]', '    over = [v for v in hits if v.kind == "turn" and over_bound(v.d_bide, v.pred[3], margin)]')],
     {'NR-accept-kinds'}),
    ('A68 acceptance: over checked on trainer battles only', 'audit',
     [('    over = [v for v in hits if over_bound(v.d_bide, v.pred[3], margin)]', '    over = [v for v in hits if v.battle == "trainer" and over_bound(v.d_bide, v.pred[3], margin)]')],
     {'NR-accept-kinds'}),
    ('A69 acceptance: over uses the ACCEPT_MARGIN constant, not the parameter', 'audit',
     [('    over = [v for v in hits if over_bound(v.d_bide, v.pred[3], margin)]', '    over = [v for v in hits if over_bound(v.d_bide, v.pred[3], ACCEPT_MARGIN)]')],
     {'I5', 'X7'}),
    ("A34 below-min tag '<='", 'audit',
     [('    if obs < lo:', '    if obs <= lo:')],
     {'NR-output-edges'}),
    ("A35 >cmax+M1a count '>='", 'audit',
     [('    n_m1a = sum(v.d_bide > v.pred[3] + m1a_bound(v) for v in hs)', '    n_m1a = sum(v.d_bide >= v.pred[3] + m1a_bound(v) for v in hs)')],
     {'NR-output-edges'}),
    ("A36 stats below-min '<='", 'audit',
     [('    below = sum(v.d_bide < v.pred[0] for v in hs)', '    below = sum(v.d_bide <= v.pred[0] for v in hs)')],
     {'NR-output-edges'}),
    ("A43 M1a bound: Charge regardless of the move's type", 'audit',
     [('    charged = v.before.s3[0] & S3_CHARGED and move_info(v.move)["type"] == "Electric"', '    charged = v.before.s3[0] & S3_CHARGED')],
     {'O3'}),
    ('A70 stats row n: hits restricted to d_bide>0 but NOT pred[3]>0 filter... (per-stratum max over KO only)', 'audit',
     [('    diff = max(v.d_bide - v.pred[3] for v in hs)', '    diff = max(v.d_bide - v.pred[3] for v in hs if v.kind == "turn") if any(v.kind == "turn" for v in hs) else 0')],
     {'NR-output-edges'}),
    ('A37 parser: a repeated field accepted (the last wins)', 'audit',
     [('        if not eq or not key or key in fields:', '        if not eq or not key:')],
     {'NR-parser'}),
    ('A38 parser: AFTER kind unchecked', 'audit',
     [('        if fields["kind"] not in ("entry", "end"):', '        if False:')],
     {'NR-parser'}),
    ('A39 parser: party length unchecked', 'audit',
     [('        if len(party) != 6:', '        if False:')],
     {'NR-parser'}),
    ('A40 parser: dis unchecked', 'audit',
     [('    _hexes(fields["dis"], 2, 56)\n', '    pass\n')],
     {'NR-parser'}),
    ('A71 parser: pred of any 4 fields accepted incl. a malformed err', 'audit',
     [('if fields["pred"] == "none" or re.fullmatch(r"err:[\\w.]+", fields["pred"]):', 'if fields["pred"] == "none" or fields["pred"].startswith("err"):')],
     {'NR-parser'}),
    ('A72 parser: ERR where unchecked', 'audit',
     [('        if fields["where"] not in ("ctl", "before", "after-entry", "after-end") or not re.fullmatch(r"[\\w.]+",', '        if not re.fullmatch(r"[\\w.]+",')],
     {'NR-parser'}),
    ('A41 port control: open interval', 'audit',
     [('        if not lo <= v.d_bide <= hi:', '        if not lo < v.d_bide < hi:')],
     {'NR-port-edges'}),
    ("A42 Hidden Power: TYPE_MYSTERY skip '>' (t==9 -> '???')", 'audit',
     [('    if t >= 9:', '    if t > 9:')],
     {'NR-hp-mystery-skip', 'NR-hp-rolled-type'}),
    ('A73 port adapter: attacker types swapped (STAB-equivalent)', 'audit',
     [('attacker_types=(TYPE_NAMES[me.type1], TYPE_NAMES[me.type2]),', 'attacker_types=(TYPE_NAMES[me.type2], TYPE_NAMES[me.type1]),')],
     {'PC3'}),
    ('A74 port adapter: foresight from OUR status2', 'audit',
     [('foresight=bool(foe.status2 & S2_FORESIGHT))', 'foresight=bool(me.status2 & S2_FORESIGHT))')],
     {'PC6'}),
    ("A75 port adapter: Charge from the FOE's s3", 'audit',
     [('charge_listed_electric=bool(b.s3[0] & S3_CHARGED)', 'charge_listed_electric=bool(b.s3[1] & S3_CHARGED)')],
     {'PC4'}),
    ('D01 bide read UNSIGNED', 'dmgaudit',
     [('signed=True)', 'signed=False)')],
     {'NP-fields'}),
    ('D02 Flash Fire: inner EWRAM guard dropped', 'dmgaudit',
     [('            if _EWRAM[0] <= flags_ptr < _EWRAM[1]:', '            if True:')],
     {'NP-fields'}),
    ('D03 Flash Fire: outer EWRAM guard dropped', 'dmgaudit',
     [('        if _EWRAM[0] <= resources < _EWRAM[1]:', '        if True:')],
     {'NP-ff-null-resources'}),
    ('D04 Flash Fire: flags pointer read at +0 (secretBase) not +4', 'dmgaudit',
     [('context.emulator.read_bytes(resources + 4, 4)', 'context.emulator.read_bytes(resources + 0, 4)')],
     {'NP-fields'}),
    ('D05 Flash Fire: flags[b] read as bytes (stride 1)', 'dmgaudit',
     [('read_bytes(flags_ptr + 4 * b, 4)', 'read_bytes(flags_ptr + b, 4)')],
     {'NP-fields'}),
    ('D06 party HP offset 0x54 (level/mail) not 0x56', 'dmgaudit',
     [('party[i * 100 + 0x56:i * 100 + 0x58]', 'party[i * 100 + 0x54:i * 100 + 0x56]')],
     {'NP-fields'}),
    ('D07 party PID offset +4 (OT id) not +0', 'dmgaudit',
     [('unpack_uint32(party[i * 100:i * 100 + 4])', 'unpack_uint32(party[i * 100 + 4:i * 100 + 8])')],
     {'NP-fields'}),
    ('D08 turn counter at +0x12 not +0x13', 'dmgaudit',
     [("read_symbol('gBattleResults', offset=0x13, size=1)", "read_symbol('gBattleResults', offset=0x12, size=1)")],
     {'NP-fields'}),
    ('D09 mons written in (foe, ours) order', 'dmgaudit',
     [('"mons=" + ",".join(mons[i * 0x58:(i + 1) * 0x58].hex() for i in range(2)),', '"mons=" + ",".join(mons[i * 0x58:(i + 1) * 0x58].hex() for i in (1, 0)),')],
     {'NP-fields'}),
    ('D10 mv read as u8 (not u16)', 'dmgaudit',
     [('"mv=" + ",".join(str(unpack_uint16(moves[i * 2:i * 2 + 2])) for i in range(4)),', '"mv=" + ",".join(str(moves[i]) for i in range(4)),')],
     {'NP-fields'}),
    ('D11 side written in reversed order', 'dmgaudit',
     [('"side=" + ",".join(str(unpack_uint16(sides[i * 2:i * 2 + 2])) for i in range(2)),', '"side=" + ",".join(str(unpack_uint16(sides[i * 2:i * 2 + 2])) for i in (1, 0)),')],
     {'NP-fields'}),
    ('D12 s3 written in reversed order', 'dmgaudit',
     [('"s3=" + ",".join(f"{unpack_uint32(status3[i * 4:i * 4 + 4]):08x}" for i in range(2)),', '"s3=" + ",".join(f"{unpack_uint32(status3[i * 4:i * 4 + 4]):08x}" for i in (1, 0)),')],
     {'NP-fields'}),
    ('D13 act written reversed', 'dmgaudit',
     [('"act=" + ",".join(str(x) for x in read_symbol("gChosenActionByBattler", size=4)),', '"act=" + ",".join(str(x) for x in reversed(read_symbol("gChosenActionByBattler", size=4))),')],
     {'NP-fields'}),
    ('D14 weather read as the low byte only', 'dmgaudit',
     [('f"weather={unpack_uint16(read_symbol(\'gBattleWeather\', size=2))}",', 'f"weather={read_symbol(\'gBattleWeather\', size=2)[0]}",')],
     {'NP-fields'}),
    ('D15 prediction attacker/defender SWAPPED', 'dmgaudit',
     [('attacker, defender = battle_state.own_side.left_battler, battle_state.opponent.left_battler', 'attacker, defender = battle_state.opponent.left_battler, battle_state.own_side.left_battler')],
     {'NP-pred-exact'}),
    ('D16 crit prediction WITHOUT is_critical_hit=True', 'dmgaudit',
     [('crit = util.calculate_move_damage_range(move, attacker, defender, is_critical_hit=True)', 'crit = util.calculate_move_damage_range(move, attacker, defender)')],
     {'NP-pred-exact'}),
    ('D17 bcrit computed with crit False', 'dmgaudit',
     [('f"{util._calculate_base_move_damage(move, attacker, defender, True)}")', 'f"{util._calculate_base_move_damage(move, attacker, defender, False)}")')],
     {'NP-pred-exact'}),
    ('D18 exit guard dropped (BEFORE written while still selecting)', 'dmgaudit',
     [('        if not battle_is_active() or get_main_battle_callback() in _SELECTION_STATES:\n            return\n', '        if False:\n            return\n')],
     {'NP-exit-guard'}),
    ('D19 exit guard: sub_8012324 not a selection state', 'dmgaudit',
     [('_SELECTION_STATES = ("HandleTurnActionSelectionState", "sub_8012324")', '_SELECTION_STATES = ("HandleTurnActionSelectionState",)')],
     {'NP-exit-guard'}),
    ('D20 battle start does not drop a stale BEFORE', 'dmgaudit',
     [('    _pending = False\n    try:\n        _log("CTL v=1")', '    try:\n        _log("CTL v=1")')],
     {'NP-pending'}),
    ('D21 entry does not consume the BEFORE (every re-entry logs an AFTER)', 'dmgaudit',
     [('    _pending = False\n    try:\n        _log(f"AFTER v=1 kind=entry', '    try:\n        _log(f"AFTER v=1 kind=entry')],
     {'NP-pending'}),
    ('D22 entry logs without a pending BEFORE', 'dmgaudit',
     [('    if not _on() or not _pending:\n        return\n    _pending = False\n    try:\n        _log(f"AFTER v=1 kind=entry', '    if not _on():\n        return\n    _pending = False\n    try:\n        _log(f"AFTER v=1 kind=entry')],
     {'NP-pending'}),
    ('D23 end logs without a pending BEFORE', 'dmgaudit',
     [('    if not _on() or not _pending:\n        return\n    _pending = False\n    try:\n        _log(f"AFTER v=1 kind=end', '    if not _on():\n        return\n    _pending = False\n    try:\n        _log(f"AFTER v=1 kind=end')],
     {'NP-pending'}),
    ('D24 the end read dereferences Flash Fire', 'dmgaudit',
     [('_raw(flash_fire=False)', '_raw(flash_fire=True)')],
     {'NP-end-no-ff'}),
    ('D25 flag loosened: any non-empty value turns it on', 'dmgaudit',
     [('    return os.environ.get(FLAG, "").strip() == "1"', '    return os.environ.get(FLAG, "").strip() != ""')],
     {'NP-flag-values'}),
    ('D26 _pending set BEFORE the log (a failed BEFORE leaves a pending)', 'dmgaudit',
     [('        _log(f"BEFORE v=1 {_raw(flash_fire=True)} badges={_badges()} {_prediction(battle_state)}")\n        _pending = True', '        _pending = True\n        _log(f"BEFORE v=1 {_raw(flash_fire=True)} badges={_badges()} {_prediction(battle_state)}")')],
     {'NP-raise'}),
    ("D27 entry hook's try/except removed (a read failure propagates into the battle)", 'dmgaudit',
     [('    _pending = False\n    try:\n        _log(f"AFTER v=1 kind=entry {_raw(flash_fire=True)} {_party()}")\n    except Exception as error:  # noqa: BLE001 - telemetry must never affect a battle\n        _err("after-entry", error)', '    _pending = False\n    _log(f"AFTER v=1 kind=entry {_raw(flash_fire=True)} {_party()}")')],
     {'NP-raise'}),
    ("D28 ERR where name drifts from the contract ('entry')", 'dmgaudit',
     [('        _err("after-entry", error)', '        _err("entry", error)')],
     {'NP-raise'}),
    ('D29 prediction error logged as pred=none (err: path lost)', 'dmgaudit',
     [('        pred = f"err:{type(error).__name__}"', '        pred = "none"')],
     {'NP-pred-err'}),
    ('D30 badges: 7 badges only', 'dmgaudit',
     [('for i in range(8) if get_event_flag', 'for i in range(7) if get_event_flag')],
     {'NP-fields'}),
    ('H01 BAS: a SECOND get_battle_state() right before the exit hook', 'bas',
     [('    _dmgaudit.on_selection_exit(battle_state)\n', '    battle_state = get_battle_state()\n    _dmgaudit.on_selection_exit(battle_state)\n')],
     {'NH-gbs-count'}),
    ('H02 BAS: a DMGAUDIT event emitted from BAS itself', 'bas',
     [('    _dmgaudit.on_selection_exit(battle_state)\n', "    debug_logger.event('x', category='DMGAUDIT')\n    _dmgaudit.on_selection_exit(battle_state)\n")],
     {'NH-no-dmgaudit-literal'}),
    ('W01 an OUT effect admitted to Tier A: DOUBLE_HIT (Double Kick: two hits in one Δbide)', 'audit',
     [('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "DOUBLE_HIT", ')],
     {'NR-whitelist-table'}),
    ('W02 an OUT effect admitted: LEVEL_DAMAGE (Night Shade / Seismic Toss)', 'audit',
     [('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "LEVEL_DAMAGE", ')],
     {'NR-whitelist-table'}),
    ('W03 an OUT effect admitted: OHKO', 'audit',
     [('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "OHKO", ')],
     {'NR-whitelist-table'}),
    ('W04 an OUT effect admitted: FLAIL (dynamic power)', 'audit',
     [('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "FLAIL", ')],
     {'NR-whitelist-table'}),
    ('W05 an OUT effect admitted: TRAP (Whirlpool)', 'audit',
     [('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "TRAP", ')],
     {'NR-whitelist-table'}),
    ('W06 an OUT effect admitted: TWINEEDLE', 'audit',
     [('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "TWINEEDLE", ')],
     {'NR-whitelist-table'}),
    ('W07 Tier B -> A: POISON_FANG moved (trainer KO no longer unobservable)', 'audit',
     [('"POISON_HIT", "POISON_TAIL", "POISON_FANG",\n', '"POISON_HIT", "POISON_TAIL",\n'), ('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "POISON_FANG", ')],
     {'NR-whitelist-table'}),
    ('W08 Tier B -> A: CONFUSE_HIT moved', 'audit',
     [('"POISON_FANG",\n                    "CONFUSE_HIT"})', '"POISON_FANG"})'), ('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "CONFUSE_HIT", ')],
     {'NR-whitelist-table'}),
    ('W09 Tier C -> A: PURSUIT moved (label only)', 'audit',
     [('"BRICK_BREAK", "PURSUIT", "FALSE_SWIPE",', '"BRICK_BREAK", "FALSE_SWIPE",'), ('TIER_A = frozenset({\n    "HIT", ', 'TIER_A = frozenset({\n    "HIT", "PURSUIT", ')],
     {'NR-whitelist-table'}),
    ('W10 a Tier A entry dropped: THUNDER -> OUT (samples lost)', 'audit',
     [('"SKY_UPPERCUT",\n    "THUNDER", ', '"SKY_UPPERCUT",\n    ')],
     {'NR-whitelist-table'}),
    ('W11 a Tier C entry dropped: SNORE -> OUT', 'audit',
     [('"FOCUS_PUNCH", "SNORE", "DREAM_EATER"', '"FOCUS_PUNCH", "DREAM_EATER"')],
     {'NR-whitelist-table'}),
    ("W12 Surf by index removed from C AND Struggle kept (only Surf's index moved to 58)", 'audit',
     [('MOVE_SURF, MOVE_STRUGGLE, MOVE_HIDDEN_POWER = 57, 165, 237', 'MOVE_SURF, MOVE_STRUGGLE, MOVE_HIDDEN_POWER = 58, 165, 237')],
     {'NR-whitelist-table', 'R10a', 'R10b', 'W1', 'W3'}),
]

PATHS = {"dmgaudit": D_PATH, "bas": BAS_PATH, "bh": BH_PATH}


def _apply(src: str, edits) -> str:
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            raise AssertionError(f"mutant anchor found {n} times: {old[:80]!r}")
        src = src.replace(old, new)
    return src


def _install(name: str, path, package: str, source: str, i: int):
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    mod.__package__ = package
    sys.modules[name] = mod
    exec(compile(source, f"<mutant {i}>", "exec"), mod.__dict__)


#: Every mutant as (label, target, edits, want): the classifier's (CASES), production's (PROD_CASES), the pass's.
JOBS: list = ([(label, "audit", [(old, new)], want) for label, old, new, want in CASES] + list(PROD_CASES)
              + list(PASS_CASES))
_SRCS: dict = {}


def _sources() -> dict:
    """The unmutated texts (read once per process)."""
    if not _SRCS:
        _SRCS.update({k: p.read_text(encoding="utf-8") for k, p in PATHS.items()})
        _SRCS["audit"] = A_PATH.read_text(encoding="utf-8")
    return _SRCS


def _job_red(i: int):
    """ONE mutant: apply its edits in memory (never to disk), run every row tagged, restore. Returns (i, the sorted red
    rows or None, an error text). Runs in a pool worker, or in-process when no pool can be made."""
    _label, target, edits, _want = JOBS[i]
    srcs = _sources()
    real_a, real_d = sys.modules[A_NAME], sys.modules[D_NAME]
    try:
        msrcs = {k: srcs[k] for k in PATHS}
        if target == "audit":
            _install(A_NAME, A_PATH, "", _apply(srcs["audit"], edits), i)
        else:
            msrcs[target] = _apply(srcs[target], edits)
            if target == "dmgaudit":
                _install(D_NAME, D_PATH, "modules", msrcs[target], i)
        return i, sorted(all_rows("m", msrcs)), ""
    except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
        return i, None, f"{type(error).__name__}: {error}"
    finally:
        sys.modules[A_NAME], sys.modules[D_NAME] = real_a, real_d


def _run_jobs() -> tuple[dict, str]:
    """Every mutant's red set, in a process pool (each worker imports this gate once; ~190 mutants x ~0.3 s would be
    about a minute in one process), or in-process if no pool can be made. Returns ({i: (red, error)}, how)."""
    results: dict = {}
    try:
        from concurrent.futures import ProcessPoolExecutor
        workers = max(2, min(8, (os.cpu_count() or 2)))
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for i, red, err in pool.map(_job_red, range(len(JOBS)), chunksize=4):
                results[i] = (red, err)
        return results, f"a pool of {workers} processes"
    except Exception as error:  # noqa: BLE001 - no pool (a sandbox, a frozen interpreter): the same jobs in-process
        results.clear()
        for i in range(len(JOBS)):
            _i, red, err = _job_red(i)
            results[i] = (red, err)
        return results, f"in-process (no pool: {type(error).__name__}: {error})"


def main() -> int:
    t0 = time.perf_counter()
    for k in (FLAG, FAULT):                     # the rows set these themselves; an ambient value would skew them
        os.environ.pop(k, None)
    srcs = {k: p.read_text(encoding="utf-8") for k, p in PATHS.items()}
    print("I — instrument");                  i_rows("")
    print("\nP — pairing");                   p_rows("")
    print("\nS — samples");                   s_rows("")
    print("\nW — whitelist tiers");           w_rows("")
    print("\nR — per-read strata (b: at BEFORE only; a: at AFTER only)");   r_rows("")
    print("\nQ — BEFORE-only strata");        q_rows("")
    print("\nG — strata only the pair shows"); g_rows("")
    print("\nC — self-check");                c_rows("")
    print("\nX — acceptance");                x_rows("")
    print("\nO — outputs");                   o_rows("")
    print("\nPC — port control");             pc_rows("")
    print("\nT — the Step-0 table");          t_rows("")
    print("\nPIN — production (modules/dmgaudit.py executed; the hook sites by AST)");  pin_rows("", srcs)
    print("\nN — the adversarial pass's rows, the faint reset, Hidden Power's rolled type");  n_rows("", srcs)
    baseline = all_rows("m", srcs)
    if baseline:
        print(f"\n⛔ BASELINE RED (no mutant applied): {sorted(baseline)} — a defect in the code under test. These rows "
              f"are left out of every mutant comparison below until fixed.")
    results, how = _run_jobs()
    print(f"\nM — mutants (each must turn EXACTLY its named rows red; {len(JOBS)} mutants, run in {how})")
    covered: set = set()
    for i, (label, _target, _edits, want) in enumerate(JOBS):
        red, err = results[i]
        if red is None:
            check(label, False, err)
            continue
        red = set(red) - baseline
        want_now = want - baseline
        covered |= want
        check(label, red == want_now, f"red {sorted(red)}" + ("" if red == want_now else f" (want {sorted(want_now)})")
              + (f" [baseline-red rows left out: {sorted(want & baseline)}]" if want & baseline else ""))
    uncovered = sorted(ROW_NAMES - covered)
    check("COVERAGE every row appears in at least one mutant's expected red set", not uncovered,
          f"{len(ROW_NAMES)} rows; uncovered {uncovered}")
    wall = time.perf_counter() - t0
    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s) in {wall:.1f} s:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL PASS ({len(ROW_NAMES)} rows, {len(JOBS)} mutants) in {wall:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
