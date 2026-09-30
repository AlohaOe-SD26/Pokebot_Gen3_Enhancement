r"""GATE G-W — design v2 step 12 (weaken-to-catch, USER RULING 25): `modules/story/weaken_catch.py` (the PURE decision)
and its ADAPTER `_r25_weaken_turn` in `plugins/custom_modes/story_mode.py` (`ai-research-notes/2026-09-30-weaken12-DESIGN.md`
D1-D15; D11 is this gate).

WHY. Weaken-to-catch is the first catch-battle code that may DAMAGE a wanted Pokémon, so a wrong verdict can KO the very
species the battle exists to catch. Every W-row below EXECUTES the real module on a synthetic snapshot and asserts the
verdict that `ai-research-notes/2026-09-30-weaken12-PREDICTIONS.md` PRE-REGISTERED before the module existed — never a
value copied from the module's output. The catch-chance anchors (W67) are HAND-DERIVED here in integers, step by step,
from `battle_script_commands.c:9987-10028`.

ROWS
  W01-W64   the pre-registered table (S0 = the PREDICTIONS' default snapshot; each row changes only what it names).
            A row whose table entry gives a reason keyword asserts it too, so a THROW for the wrong reason is red.
            ⚠ W52's filed reason is "half", but D4 puts the one-throw-odds check BEFORE the damage stage and the S0
            target at 11/22 has a one-throw chance of 0.624 >= 0.5, so its operative reason is "odds". The VERDICT is as
            filed; the reason asserted is "odds" and the deviation is REPORTED (the builder does not decide it). WB52
            pins the "half" rule itself on a target whose odds stay below 0.5.
  W62, W65a-e  the ADAPTER on the REAL classes (StoryCatchStrategy / StoryDexCatchStrategy / StoryShinyCatchStrategy
            built with `__new__`) with a stand-in mode, a REAL BattleState built from raw `gBattleMons` records, and
            `read_symbol`, the bag, the logger and `get_battle_state` faked (the last REBOUND wherever it is bound and
            counted: every adapter row asserts 0 calls, KI-108).
  W66a-h    AST pins (production text; comments and docstrings never count).
  W67a-l    catch_p anchors, hand-derived.
  W68       a sweep: over every pure row's snapshot, the module returns only a verdict it defines and, for THROW, only a
            ball (RULING 27).
  WB*       BUILDER-ADDED rows (NOT pre-registered; each labelled): they pin rules the filed rows cannot isolate and the
            adapter's acting path (`act=`), its memo, its raw disable-struct read, its party read and the per-run flag
            parse. ⚠ VACUOUS filed rows, relabelled honestly: W38 (Seismic Toss is already Ghost-immune; WB38 isolates the
            Ghost-Curse rule), W51 (the floor also blocks; WXwgblock isolates Wonder Guard), W52 (the odds fire first;
            WB52 isolates the 50% rule), W58f (sleep is always preferred; W58e isolates the Synchronize skip).
  WX*, WXA* the ADVERSARIAL PASS's rows (2026-09-30, `scratchpad/w12m/proposed.py`; folded with the verdicts the pass
            derived): 48 pure rows, 4 function rows (WXbtsweep, WXcapseq, WXballs, WXcpstatus) and 20 adapter rows,
            each adapter row also asserting 0 get_battle_state() calls.
  WP*       the pass's PRODUCTION FIXES (PD1 Trace copies the target's ability; PD2 Pain Split; PD3 a confusion berry;
            PD4 a Sand Stream member; PD5 no RECHARGE in stage 2 and the horizon slack 4 -> 8; the memo nit), each RED on
            the pre-fix code (measured) and GREEN after, with controls where a fix could over-refuse.
FAULTS      the nine production fault envs (never set in a real run; `29-DISABLED-FEATURES-REGISTRY.md`). Each has an
            EXACT red set: its own set UNION its fold addition (FAULT_ADDITIONS), both written before their first run.
MUTANTS     exec'd source edits of the module or of story_mode.py (never written to disk), each with an EXACT red set
            written before its first run: the gate's own (MUTANTS, UNION MUTANT_ADDITIONS for the fold's rows), one
            REVERT per production fix (REVERT_MUTANTS: each must redden exactly its fix's rows), and the adversarial
            pass's formerly-missed mutants (PASS_MUTANTS; the ones it argued equivalent, conservative or unreachable are
            listed with its argument, not run). Two mention-only edits must turn NOTHING red (a gate that fires on a
            comment teaches the reader to bypass it). COVERAGE fails if any row is in no fault's or mutant's set. Jobs
            run in a process pool, in-process if no pool can be made (`--inprocess` forces it).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 -u probe_weaken_catch.py [--inprocess]     (exit 1 on any failure)
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
import time
import types
from dataclasses import replace

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
import modules.story.weaken_catch  # noqa: E402,F401  (always read via sys.modules: a mutant is exec'd there)
import plugins.custom_modes  # noqa: E402
import plugins.custom_modes.story_mode  # noqa: E402,F401
import modules.battle_state  # noqa: E402
import modules.battle_strategies._util  # noqa: E402
import modules.battle_strategies.catch  # noqa: E402
import modules.catch_balls  # noqa: E402
import modules.context  # noqa: E402
import modules.debug_logger  # noqa: E402
import modules.items  # noqa: E402
import modules.memory  # noqa: E402
from modules.battle_state import BattleState  # noqa: E402
from modules.battle_strategies import TurnAction  # noqa: E402
from modules.items import get_item_by_name  # noqa: E402
from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER  # noqa: E402

WC_NAME, SM_NAME = "modules.story.weaken_catch", "plugins.custom_modes.story_mode"
WC_PATH = SANDBOX / "modules" / "story" / "weaken_catch.py"
SM_PATH = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"
PATHS = {"wc": WC_PATH, "sm": SM_PATH}

FLAG, FLAG_CALC, FLAG_KINDS = "POKEBOT_R25_WEAKEN", "POKEBOT_R25_WEAKEN_CALC", "POKEBOT_R25_WEAKEN_KINDS"
F_NOFLOOR = "POKEBOT_R25_FAULT_WEAKEN_NOFLOOR"
F_NOENCORE = "POKEBOT_R25_FAULT_WEAKEN_NOENCORE"
F_CALCLEAK = "POKEBOT_R25_FAULT_WEAKEN_CALCLEAK"
F_ACTIVEONLY = "POKEBOT_R25_FAULT_WEAKEN_ACTIVEONLY"
F_NOPP = "POKEBOT_R25_FAULT_WEAKEN_NOPP"
F_MASTERBALL = "POKEBOT_R25_FAULT_WEAKEN_MASTERBALL"
F_SPECIESID = "POKEBOT_R25_FAULT_WEAKEN_SPECIESID"
F_NETGAIN = "POKEBOT_R25_FAULT_WEAKEN_NETGAIN"
F_NAMEDISPATCH = "POKEBOT_R25_FAULT_WEAKEN_NAMEDISPATCH"
ALL_ENVS = (FLAG, FLAG_CALC, FLAG_KINDS, F_NOFLOOR, F_NOENCORE, F_CALCLEAK, F_ACTIVEONLY, F_NOPP, F_MASTERBALL,
            F_SPECIESID, F_NETGAIN, F_NAMEDISPATCH)

with open(SANDBOX / "modules" / "data" / "moves.json", encoding="utf-8") as _fh:
    MOVES = json.load(_fh)                      # the GATE's own copy: rows never read the module under test for data
MOVE_ID = {m["name"]: i for i, m in enumerate(MOVES)}
with open(SANDBOX / "modules" / "data" / "species.json", encoding="utf-8") as _fh:
    SPECIES = json.load(_fh)
SPECIES_ID = {s["name"]: i for i, s in enumerate(SPECIES)}

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


def WC():
    return sys.modules[WC_NAME]


def SM():
    return sys.modules[SM_NAME]


# ================================================================================================= snapshot builders
PID_T, PID_T2, PID_M = 0x0BADF00D, 0x0C0FFEE0, 0x550A9BE6
S1_SLEEP2, S1_POISON, S1_BURN, S1_PARALYSIS = 0x2, 0x8, 0x10, 0x40
S2_SUBSTITUTE, S2_FORESIGHT, S2_TORMENT, S2_UPROAR2 = 1 << 24, 1 << 29, 1 << 31, 0x20
S3_LEECHSEED, S3_ON_AIR, S3_IMPRISONED = 1 << 2, 1 << 6, 1 << 13
SIDE_SAFEGUARD, SIDE_FUTUREATTACK = 1 << 5, 1 << 6


def mv(name, pp=None):
    """A RAW move slot from the gate's own moves.json, PP = the move's max unless given."""
    i = MOVE_ID[name]
    d = MOVES[i]
    return WC().WMove(i, d["name"], d["effect"], d["type"], d["base_power"], d["pp"] if pp is None else pp,
                      bool(d["makes_contact"]), bool(d["is_sound_move"]))


def moves(*spec):
    """(name, pp) / name / None per slot."""
    out = []
    for s in spec:
        if s is None:
            out.append(None)
        elif isinstance(s, tuple):
            out.append(mv(*s))
        else:
            out.append(mv(s))
    return tuple(out)


def t_moves(**slots):
    """S0's target moveset (Peck, Growl, Focus Energy, Quick Attack) with named slots replaced: t_moves(s2="Encore")."""
    base = ["Peck", "Growl", "Focus Energy", "Quick Attack"]
    for k, v in slots.items():
        base[int(k[1:])] = v
    return moves(*base)


def dis(*, disabled=0, disable_t=0, encored=0, encore_t=0, taunt=0) -> bytes:
    """A RAW 0x1C-byte `struct DisableStruct` (include/battle.h): disabledMove 0x04, encoredMove 0x06, disableTimer
    0x0B (low nibble), encoreTimer 0x0E, tauntTimer 0x13."""
    b = bytearray(0x1C)
    struct.pack_into("<HH", b, 0x04, disabled, encored)
    b[0x0B], b[0x0E], b[0x13] = disable_t, encore_t, taunt
    return bytes(b)


def T0(**kw):
    w = WC()
    base = w.WTarget(pid=PID_T, species_id=SPECIES_ID["Taillow"], species="Taillow", dex=276, level=6, hp=22,
                     max_hp=22, types=("Normal", "Flying"), ability="Guts", species_ability="Guts", catch_rate=200,
                     moves=t_moves())
    return replace(base, **kw)


LEAD_S0 = (("Tackle", 31), ("Seismic Toss", 20), ("Mud-slap", 10), ("Water Gun", 7))
LEAD_SING = (("Tackle", 31), ("Seismic Toss", 0), ("Sing", 15), ("Water Gun", 7))           # W57's premise
LEAD_TW = (("Tackle", 31), ("Seismic Toss", 0), ("Thunder Wave", 20), ("Water Gun", 7))
LEAD_GLARE = (("Tackle", 31), ("Seismic Toss", 0), ("Glare", 30), ("Water Gun", 7))
LEAD_TW_SING = (("Tackle", 31), ("Seismic Toss", 0), ("Thunder Wave", 20), ("Sing", 15))
LEAD_ST_SING = (("Tackle", 31), ("Seismic Toss", 20), ("Sing", 15), ("Water Gun", 7))
LEAD_ST0 = (("Tackle", 31), ("Seismic Toss", 0), ("Mud-slap", 10), ("Water Gun", 7))           # W63's lead


def ME0(lead=LEAD_S0, **kw):
    w = WC()
    base = w.WSelf(pid=PID_M, species="Mudkip", level=13, hp=40, max_hp=40, types=("Water",), ability="Torrent",
                   species_ability="Torrent", moves=moves(*lead))
    return replace(base, **kw)


PARTY_S0 = ("Torrent", "Run Away", "Compoundeyes", "Soundproof")


def P0(abilities=PARTY_S0):
    return WC().WParty(tuple(abilities))


def E0(**kw):
    w = WC()
    base = w.WEnv(flag="1", calc=False, kinds=("dex", "team"), kind="team", ctx_sp="Taillow#276", battle_flags=0x4,
                  turn=0, ball="Poké Ball", bag=(("Poké Ball", 30),), usable_balls=30, banned=())
    return replace(base, **kw)


def MEMO(history=(), *, pid=PID_T, species_id=None, ctx_ok=True):
    return WC().WMemo(pid, SPECIES_ID["Taillow"] if species_id is None else species_id, ctx_ok, tuple(history))


def S(t=None, me=None, party=PARTY_S0, env=None, memo=None, lead=LEAD_S0):
    return T0(**(t or {})), ME0(lead, **(me or {})), P0(party), E0(**(env or {})), memo


class X:
    """An expectation: the verdict, and optionally the slot, move, reason keyword(s), ball, x."""

    def __init__(self, verdict, slot=None, move=None, reason=None, ball=None, x=None):
        self.verdict, self.slot, self.move, self.ball, self.x = verdict, slot, move, ball, x
        self.reason = () if reason is None else ((reason,) if isinstance(reason, str) else tuple(reason))

    def diff(self, d) -> str:
        bad = []
        if d.verdict != self.verdict:
            bad.append(f"verdict {d.verdict}")
        for name in ("slot", "move", "ball", "x"):
            want = getattr(self, name)
            if want is not None and getattr(d, name) != want:
                bad.append(f"{name} {getattr(d, name)!r} (want {want!r})")
        for kw in self.reason:
            if kw not in (d.reason or ""):
                bad.append(f"reason {d.reason!r} lacks {kw!r}")
        return "; ".join(bad)


# ---- the pre-registered table (PREDICTIONS: W-row table). Each entry: (id, what changes, snapshot builder, expected)
SLP = S1_SLEEP2
PURE = [
    ("W01", "S0 (Seismic Toss X=13: hp-X 9, progress 13, E_gain ~1.97)", lambda: S(),
     X("DAMAGE", slot=1, move="Seismic Toss", x=13)),
    ("W02", "the flag unset", lambda: S(env={"flag": ""}), X("DEFER", reason="off")),
    ("W03", "kind hm", lambda: S(env={"kind": "hm"}), X("DEFER", reason="kind")),
    ("W04", "the context's sp names another species at the first decision",
     lambda: S(env={"ctx_sp": "Poochyena#261"}), X("DEFER", reason="context")),
    ("W05", "a later decision with a different PID",
     lambda: S(t={"pid": PID_T2}, env={"turn": 1}, memo=MEMO([(0, "THROW", 22, 0)])), X("DEFER", reason="pid")),
    ("W06", "a later decision, the same PID, a different species (Transform)",
     lambda: S(t={"species_id": SPECIES_ID["Mudkip"], "species": "Mudkip", "dex": 258, "types": ("Water",)},
               env={"turn": 1}, memo=MEMO([(0, "THROW", 22, 0)])), X("THROW", reason="transformed")),
    ("W07", "the TRAINER flag", lambda: S(env={"battle_flags": 0x4 | 0x8}), X("DEFER", reason="battle-type")),
    ("W08", "the DOUBLE flag", lambda: S(env={"battle_flags": 0x4 | 0x1}), X("DEFER", reason="battle-type")),
    ("W09", "the LEGENDARY flag", lambda: S(env={"battle_flags": 0x4 | (1 << 13)}), X("DEFER", reason="battle-type")),
    ("W10a", "the ROAMER flag", lambda: S(env={"battle_flags": 0x4 | (1 << 10)}), X("DEFER", reason="battle-type")),
    ("W10b", "the SAFARI flag", lambda: S(env={"battle_flags": 0x4 | (1 << 7)}), X("DEFER", reason="battle-type")),
    ("W11", "our item a Choice Band", lambda: S(me={"item": "Choice Band", "item_effect": "choice_band"}),
     X("DEFER", reason="choice")),
    ("W12", "our disable struct: the Encore move at 0x06 (no timer)", lambda: S(me={"disable": dis(encored=33)}),
     X("THROW", reason="encore-on-us")),
    ("W12b", "0x04 (disabledMove) with a timer, 0x06 = 0 — pins the offset",
     lambda: S(me={"disable": dis(disabled=69, disable_t=3)}), X("THROW", reason="disabled")),
    ("W14", "our Torment", lambda: S(me={"status2": S2_TORMENT}), X("THROW")),
    ("W15", "the target's Imprison", lambda: S(t={"status3": S3_IMPRISONED}), X("THROW")),
    ("W16", "the target semi-invulnerable (Fly)", lambda: S(t={"status3": S3_ON_AIR}), X("THROW")),
    ("W17", "the target behind a Substitute", lambda: S(t={"status2": S2_SUBSTITUTE}), X("THROW")),
    ("W18", "the target confused", lambda: S(t={"status2": 2}), X("THROW")),
    ("W19", "the target poisoned", lambda: S(t={"status1": S1_POISON}), X("THROW", reason="ticking")),
    ("W20", "the target Leech Seeded", lambda: S(t={"status3": S3_LEECHSEED}), X("THROW", reason="ticking")),
    ("W21", "our Future Sight pending on its side", lambda: S(env={"side_foe": SIDE_FUTUREATTACK}),
     X("THROW", reason="ticking")),
    ("W22", "the target knows Self-Destruct, no Damp", lambda: S(t={"moves": t_moves(s2="Selfdestruct")}),
     X("THROW", reason="explosion")),
    ("W23", "the same, with our lead's Damp",
     lambda: S(t={"moves": t_moves(s2="Selfdestruct")}, me={"ability": "Damp"}),
     X("THROW", reason=("self-harm", "no-status-move"))),
    ("W24", "the target knows Teleport", lambda: S(t={"moves": t_moves(s2="Teleport")}), X("THROW", reason="ender")),
    ("W25", "the target knows Roar", lambda: S(t={"moves": t_moves(s2="Roar")}), X("THROW", reason="ender")),
    ("W26", "the target knows Perish Song", lambda: S(t={"moves": t_moves(s2="Perish Song")}),
     X("THROW", reason="ender")),
    ("W27", "the target knows Memento", lambda: S(t={"moves": t_moves(s2="Memento")}), X("THROW", reason="ender")),
    ("W28", "the target knows Metronome", lambda: S(t={"moves": t_moves(s2="Metronome")}),
     X("THROW", reason="calling")),
    ("W29", "the target knows Mirror Move", lambda: S(t={"moves": t_moves(s2="Mirror Move")}),
     X("THROW", reason="calling")),
    ("W30", "the target knows Assist", lambda: S(t={"moves": t_moves(s2="Assist")}), X("THROW", reason="calling")),
    ("W31", "the target knows Sleep Talk", lambda: S(t={"moves": t_moves(s2="Sleep Talk")}),
     X("THROW", reason="calling")),
    ("W32", "a Great Ball and the target at 7/22 (30%)",
     lambda: S(t={"hp": 7}, env={"ball": "Great Ball", "bag": (("Great Ball", 30),)}), X("THROW", reason="odds")),
    ("W33", "a DAMAGE verdict at turn 0; now turn 1",
     lambda: S(env={"turn": 1}, memo=MEMO([(0, "DAMAGE", 22, 0)])), X("THROW", reason="damage-cap")),
    ("W33b", "decide again in the SAME turn after a DAMAGE verdict at that turn",
     lambda: S(env={"turn": 0}, memo=MEMO([(0, "DAMAGE", 22, 0)])), X("DAMAGE", slot=1, move="Seismic Toss")),
    ("W34", "the target knows Take Down", lambda: S(t={"moves": t_moves(s2="Take Down")}),
     X("THROW", reason="self-harm")),
    ("W35", "the target knows Belly Drum", lambda: S(t={"moves": t_moves(s2="Belly Drum")}),
     X("THROW", reason="self-harm")),
    ("W36", "the target knows Thrash", lambda: S(t={"moves": t_moves(s2="Thrash")}), X("THROW", reason="self-harm")),
    ("W37", "the target knows Jump Kick", lambda: S(t={"moves": t_moves(s2="Jump Kick")}),
     X("THROW", reason="self-harm")),
    ("W38", "a GHOST target knows Curse [VACUOUS for the Curse rule: Seismic Toss is already Ghost-immune; WB38 "
            "(Ghost + Foresight) isolates the Ghost-Curse rule]",
     lambda: S(t={"types": ("Ghost",), "moves": t_moves(s2="Curse")}), X("THROW")),
    ("W38b", "a non-Ghost target knows Curse", lambda: S(t={"moves": t_moves(s2="Curse")}), X("DAMAGE", slot=1)),
    ("W39", "the target knows Encore", lambda: S(t={"moves": t_moves(s2="Encore")}),
     X("THROW", reason="encore-knower")),
    ("W40", "the target knows Transform", lambda: S(t={"moves": t_moves(s2="Transform")}),
     X("THROW", reason="acquires")),
    ("W40b", "the target knows Mimic", lambda: S(t={"moves": t_moves(s2="Mimic")}), X("THROW", reason="acquires")),
    ("W40c", "the target knows Sketch", lambda: S(t={"moves": t_moves(s2="Sketch")}), X("THROW", reason="acquires")),
    ("W41", "the target knows Sandstorm (Normal/Flying)", lambda: S(t={"moves": t_moves(s2="Sandstorm")}),
     X("THROW")),
    ("W41b", "the same target Ground-type", lambda: S(t={"moves": t_moves(s2="Sandstorm"), "types": ("Ground",)}),
     X("DAMAGE", slot=1)),
    ("W42", "the target's total PP 60 (H = 2*(30+8) = 76 since PD5; filed with 2*(30+4) = 68)",
     lambda: S(t={"moves": moves(("Peck", 15), ("Growl", 15), ("Focus Energy", 15), ("Quick Attack", 15))}),
     X("THROW", reason="struggle")),
    # ⚠ PD5 (the horizon slack 4 -> 8, the adversarial pass's fold): H moved 68 -> 76, so the filed snapshot (total PP
    # 70) now reads THROW (struggle). The row keeps its purpose, the first total ABOVE H, at 78; WPh76 pins H itself.
    ("W42b", "the target's total PP 78 (the first total above H = 76; filed at 70 against H = 68 — REPORTED)",
     lambda: S(t={"moves": moves(("Peck", 20), ("Growl", 20), ("Focus Energy", 20), ("Quick Attack", 18))}),
     X("DAMAGE", slot=1)),
    ("W43", "sandstorm on", lambda: S(env={"weather": 0x10}), X("THROW")),
    ("W43b", "sandstorm on, a Ground target", lambda: S(env={"weather": 0x10}, t={"types": ("Ground",)}),
     X("DAMAGE", slot=1)),
    ("W43c", "sandstorm on, our Cloud Nine", lambda: S(env={"weather": 0x10}, me={"ability": "Cloud Nine"}),
     X("THROW")),
    ("W44", "a party member (not the lead) with Rough Skin; the target knows a contact move (Peck)",
     lambda: S(party=("Torrent", "Rough Skin", "Compoundeyes", "Soundproof")), X("THROW")),
    ("W44b", "the same, the target knows no contact move",
     lambda: S(party=("Torrent", "Rough Skin", "Compoundeyes", "Soundproof"),
               t={"moves": moves("Growl", "Focus Energy", "Sand-attack", "Leer")}), X("DAMAGE", slot=1)),
    ("W45", "a party member with Liquid Ooze; the target knows Absorb",
     lambda: S(party=("Torrent", "Liquid Ooze", "Compoundeyes", "Soundproof"), t={"moves": t_moves(s1="Absorb")}),
     X("THROW")),
    ("W46", "a party member with Synchronize", lambda: S(party=("Torrent", "Synchronize", "Compoundeyes", "Soundproof")),
     X("THROW")),
    ("W47", "Seismic Toss at PP 0", lambda: S(lead=(("Tackle", 31), ("Seismic Toss", 0), ("Mud-slap", 10),
                                                     ("Water Gun", 7))), X("THROW", reason="no-damage-move")),
    ("W49", "a Ghost target", lambda: S(t={"types": ("Ghost",)}), X("THROW", reason="immune")),
    ("W49b", "the same with Foresight on it", lambda: S(t={"types": ("Ghost",), "status2": S2_FORESIGHT}),
     X("DAMAGE", slot=1)),
    ("W50", "Night Shade in slot 1, a Normal target",
     lambda: S(lead=(("Tackle", 31), ("Night Shade", 15), ("Mud-slap", 10), ("Water Gun", 7))),
     X("THROW", reason="immune")),
    ("W51", "a Wonder Guard target with max HP 1 [VACUOUS for Wonder Guard: the floor and a zero E_gain also block at "
            "max HP 1; WXwgblock isolates Wonder Guard]",
     lambda: S(t={"ability": "Wonder Guard", "species_ability": "Wonder Guard", "hp": 1, "max_hp": 1}), X("THROW")),
    # ⚠ REPORTED DEVIATION: filed "(half)"; under D4's order the S0 target at 11/22 throws on the ODDS (0.624 >= 0.5)
    # before the damage stage is reached. Verdict as filed; reason asserted = the operative one. WB52 pins "half".
    ("W52", "the target at hp 11/22 [VACUOUS for the 50% rule: the one-throw odds (0.624) fire first; filed reason "
            "'half', operative 'odds' — REPORTED; WB52 isolates the 50% rule]",
     lambda: S(t={"hp": 11}), X("THROW", reason="odds")),
    ("W53", "Dragon Rage in slot 1 (40 >= 22)",
     lambda: S(lead=(("Tackle", 31), ("Dragon Rage", 10), ("Mud-slap", 10), ("Water Gun", 7))),
     X("THROW", reason="floor")),
    ("W54", "Sonicboom, a target with max HP 250 at 250 (20 < 25)",
     lambda: S(lead=(("Tackle", 31), ("Sonicboom", 20), ("Mud-slap", 10), ("Water Gun", 7)),
               t={"max_hp": 250, "hp": 250}), X("THROW", reason="progress")),
    ("W55", "Sonicboom, a rate-255 target, max 100 at 100 (E_gain ~0.98)",
     lambda: S(lead=(("Tackle", 31), ("Sonicboom", 20), ("Mud-slap", 10), ("Water Gun", 7)),
               t={"catch_rate": 255, "max_hp": 100, "hp": 100}), X("THROW", reason="egain")),
    ("W56", "Super Fang (X = 11 at hp 22)",
     lambda: S(lead=(("Tackle", 31), ("Super Fang", 10), ("Mud-slap", 10), ("Water Gun", 7))),
     X("DAMAGE", slot=1, move="Super Fang", x=11)),
    ("W57", "Sing in slot 2, Seismic Toss at PP 0", lambda: S(lead=LEAD_SING), X("STATUS", slot=2, move="Sing")),
    ("W57b", "as W57, the target's live Soundproof", lambda: S(lead=LEAD_SING, t={"ability": "Soundproof"}),
     X("THROW")),
    ("W57c", "as W57, Uproar on a battler (the target)", lambda: S(lead=LEAD_SING, t={"status2": S2_UPROAR2}),
     X("THROW")),
    ("W57d", "as W57, the target's live Insomnia", lambda: S(lead=LEAD_SING, t={"ability": "Insomnia"}), X("THROW")),
    ("W57e", "as W57, the target already paralysed", lambda: S(lead=LEAD_SING, t={"status1": S1_PARALYSIS}),
     X("THROW")),
    ("W57f", "as W57, Safeguard on its side",
     lambda: S(lead=LEAD_SING, env={"side_foe": SIDE_SAFEGUARD, "safeguard_timer": 5}), X("THROW")),
    ("W57g", "as W57, Taunt on us", lambda: S(lead=LEAD_SING, me={"disable": dis(taunt=2)}), X("THROW")),
    ("W57h", "as W57, 3 status tries spent (each one landed, then woke)",
     lambda: S(lead=LEAD_SING, env={"turn": 6},
               memo=MEMO([(0, "STATUS", 22, 0), (1, "THROW", 22, SLP), (2, "STATUS", 22, 0), (3, "THROW", 22, SLP),
                          (4, "STATUS", 22, 0), (5, "THROW", 22, SLP)])), X("THROW", reason="status-cap")),
    ("W57i", "as W57, the target holds a Chesto Berry (a berry is a try)",
     lambda: S(lead=LEAD_SING, t={"item": "Chesto Berry"}), X("STATUS", slot=2, move="Sing")),
    ("W57j", "as W57, the target knows Magic Coat", lambda: S(lead=LEAD_SING, t={"moves": t_moves(s2="Magic Coat")}),
     X("THROW")),
    ("W58", "Thunder Wave only; a Ground target", lambda: S(lead=LEAD_TW, t={"types": ("Ground",)}), X("THROW")),
    ("W58b", "Thunder Wave only; an Electric target", lambda: S(lead=LEAD_TW, t={"types": ("Electric",)}),
     X("STATUS", slot=2, move="Thunder Wave")),
    ("W58c", "Glare only; a Ghost target", lambda: S(lead=LEAD_GLARE, t={"types": ("Ghost",)}), X("THROW")),
    ("W58d", "Glare only; the same with Foresight",
     lambda: S(lead=LEAD_GLARE, t={"types": ("Ghost",), "status2": S2_FORESIGHT}), X("STATUS", slot=2, move="Glare")),
    ("W58e", "Thunder Wave only vs Synchronize (no ender)", lambda: S(lead=LEAD_TW, t={"ability": "Synchronize"}),
     X("THROW")),
    ("W58f", "Thunder Wave AND Sing vs Synchronize [VACUOUS for Synchronize: sleep is always preferred; W58e isolates "
             "the Synchronize skip, WBorder the sleep-first order]",
     lambda: S(lead=LEAD_TW_SING, t={"ability": "Synchronize"}),
     X("STATUS", slot=3, move="Sing")),
    ("W59", "Seismic Toss AND Sing, the target at full HP", lambda: S(lead=LEAD_ST_SING),
     X("DAMAGE", slot=1, move="Seismic Toss")),
    ("W60", "as W57, Sing in banned_moves", lambda: S(lead=LEAD_SING, env={"banned": ("Sing",)}), X("THROW")),
    ("W61", "bag: Master Ball x1 + Poké x30; the target at 7/22 (THROW)",
     lambda: S(t={"hp": 7}, env={"bag": (("Master Ball", 1), ("Poké Ball", 30))}), X("THROW", ball="Poké Ball")),
    ("W63", "CALC unset; Seismic Toss at PP 0, Tackle admissible by the calculator's bound",
     lambda: S(lead=(("Tackle", 31), ("Seismic Toss", 0), ("Mud-slap", 10), ("Water Gun", 7)),
               env={"calc": False, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))}), X("THROW")),
    ("W63b", "CALC=1, the same",
     lambda: S(lead=(("Tackle", 31), ("Seismic Toss", 0), ("Mud-slap", 10), ("Water Gun", 7)),
               env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))}),
     X("DAMAGE", slot=0, move="Tackle")),
    ("W64", "CALC=1, as W63b, our lead burned with Guts (its species' ability too)",
     lambda: S(lead=(("Tackle", 31), ("Seismic Toss", 0), ("Mud-slap", 10), ("Water Gun", 7)),
               env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))},
               me={"status1": S1_BURN, "ability": "Guts", "species_ability": "Guts"}),
     X("THROW", reason="divergence")),
    # ---- BUILDER-ADDED (NOT pre-registered): each isolates a rule a filed row cannot, or pins a cap's mechanics
    ("WB38", "[builder] a Ghost target WITH Foresight knows Curse (only the Ghost-Curse rule can stop the hit)",
     lambda: S(t={"types": ("Ghost",), "status2": S2_FORESIGHT, "moves": t_moves(s2="Curse")}),
     X("THROW", reason="self-harm:GHOST_CURSE")),
    ("WB52", "[builder] a rate-45 target at 11/22 (one-throw 0.12): the 50% rule is the operative one",
     lambda: S(t={"catch_rate": 45, "hp": 11}), X("THROW", reason="half")),
    ("WB54s", "[builder] Sonicboom on a 40/40 target: DAMAGE with X = 20 (by EFFECT; moves.json says 'Sonicboom')",
     lambda: S(lead=(("Tackle", 31), ("Sonicboom", 20), ("Mud-slap", 10), ("Water Gun", 7)),
               t={"max_hp": 40, "hp": 40}), X("DAMAGE", slot=1, move="Sonicboom", x=20)),
    ("WBnp", "[builder] 2 no-progress acting turns (a missed hit, a missed Sing) -> throw-only",
     lambda: S(lead=LEAD_ST_SING, env={"turn": 2}, memo=MEMO([(0, "DAMAGE", 22, 0), (1, "STATUS", 22, 0)])),
     X("THROW", reason="no-progress")),
    ("WBball", "[builder] no ball to throw -> DEFER", lambda: S(env={"ball": None}), X("DEFER", reason="no-ball")),
    ("WBctx", "[builder] the first decision's context did not match -> every later decision DEFERs",
     lambda: S(env={"turn": 1}, memo=MEMO([(0, "DEFER", 22, 0)], ctx_ok=False)), X("DEFER", reason="context")),
    ("WBorder", "[builder] Thunder Wave AND Sing, no Synchronize: sleep over paralysis",
     lambda: S(lead=LEAD_TW_SING), X("STATUS", slot=3, move="Sing")),
    ("WBlimber", "[builder] Thunder Wave only vs a live Limber", lambda: S(lead=LEAD_TW, t={"ability": "Limber"}),
     X("THROW")),
    # ---- ADVERSARIAL-PASS rows (2026-09-30, `scratchpad/w12m/proposed.py`, folded; NOT pre-registered): each verdict
    #      is the pass's hand derivation, kept as it computed it (none is changed by PD1-PD5; see the WP rows)
    ("WXfloor0", "[adv] lead L22 (Seismic Toss X=22) vs 22/22: hp - X = 0 -> the floor refuses",
     lambda: S(me={"level": 22}), X("THROW", reason="floor")),
    ("WXfloor1", "[adv] lead L21 (X=21) vs 22/22: hp - X = 1 -> admissible (E_gain 3.575-1.275=2.30)",
     lambda: S(me={"level": 21}), X("DAMAGE", slot=1, x=21)),
    ("WXprog10", "[adv] Sonicboom (20) vs a rate-45 200/200 target: exactly 10% -> DAMAGE (E_gain 1.91)",
     lambda: S(lead=(("Tackle", 31), ("Sonicboom", 20), ("Mud-slap", 10), ("Water Gun", 7)),
               t={"catch_rate": 45, "max_hp": 200, "hp": 200}), X("DAMAGE", slot=1, x=20)),
    ("WXprogmax", "[adv] Sonicboom vs a rate-45 target at 150/250: 20 < 10% of MAX (25) -> THROW progress",
     lambda: S(lead=(("Tackle", 31), ("Sonicboom", 20), ("Mud-slap", 10), ("Water Gun", 7)),
               t={"catch_rate": 45, "max_hp": 250, "hp": 150}), X("THROW", reason="progress")),
    ("WXodds15", "[adv] Taillow 15/22 (one-throw 0.5028 >= 0.5) -> THROW for the ODDS",
     lambda: S(t={"hp": 15}), X("THROW", reason="odds")),
    ("WXdig", "[adv] the target underground (Dig, status3 1<<7)", lambda: S(t={"status3": 1 << 7}),
     X("THROW", reason="semi-invulnerable")),
    ("WXdive", "[adv] the target underwater (Dive, status3 1<<18)", lambda: S(t={"status3": 1 << 18}),
     X("THROW", reason="semi-invulnerable")),
    ("WXconf4", "[adv] the target confused, counter 4 (status2 = 4: bit 2 only)", lambda: S(t={"status2": 4}),
     X("THROW", reason="confused")),
    ("WXburn", "[adv] the target burned (status1 0x10)", lambda: S(t={"status1": 0x10}), X("THROW", reason="ticking")),
    ("WXtoxic", "[adv] the target badly poisoned (status1 0x80 | counter 0x100)", lambda: S(t={"status1": 0x180}),
     X("THROW", reason="ticking")),
    ("WXwrap", "[adv] the target wrapped (status2 0x2000)", lambda: S(t={"status2": 0x2000}),
     X("THROW", reason="ticking:status2")),
    ("WXcursed", "[adv] the target cursed (status2 1<<28)", lambda: S(t={"status2": 1 << 28}),
     X("THROW", reason="ticking:status2")),
    ("WXnightmare", "[adv] the target under Nightmare (status2 1<<27)", lambda: S(t={"status2": 1 << 27}),
     X("THROW", reason="ticking:status2")),
    ("WXdedge", "[adv] the target knows Double-edge (DOUBLE_EDGE; also Volt Tackle)",
     lambda: S(t={"moves": t_moves(s2="Double-edge")}), X("THROW", reason="self-harm:DOUBLE_EDGE")),
    ("WXhailk", "[adv] the target knows Hail (Normal/Flying)", lambda: S(t={"moves": t_moves(s2="Hail")}),
     X("THROW", reason="weather-move:HAIL")),
    ("WXhailkice", "[adv] an ICE target knows Hail -> immune -> DAMAGE",
     lambda: S(t={"moves": t_moves(s2="Hail"), "types": ("Ice",)}), X("DAMAGE", slot=1)),
    ("WXhailw", "[adv] hail in effect (gBattleWeather 0x80)", lambda: S(env={"weather": 0x80}),
     X("THROW", reason="weather:hail")),
    ("WXhailwice", "[adv] hail in effect, an Ice target -> DAMAGE", lambda: S(env={"weather": 0x80}, t={"types": ("Ice",)}),
     X("DAMAGE", slot=1)),
    ("WXsandtemp", "[adv] a TEMPORARY sandstorm (0x08, the Sandstorm move's bit)", lambda: S(env={"weather": 0x08}),
     X("THROW", reason="weather:sandstorm")),
    ("WXppoint", "[adv] a party member with Poison Point; the target knows Peck (contact)",
     lambda: S(party=("Torrent", "Poison Point", "Compoundeyes", "Soundproof")),
     X("THROW", reason="retaliation:Poison Point")),
    ("WXfbody", "[adv] a party member with Flame Body; contact", lambda: S(party=("Torrent", "Flame Body")),
     X("THROW", reason="retaliation:Flame Body")),
    ("WXespore", "[adv] a party member with Effect Spore; contact", lambda: S(party=("Torrent", "Effect Spore")),
     X("THROW", reason="retaliation:Effect Spore")),
    ("WXoozeseed", "[adv] a party member with Liquid Ooze; the target knows Leech Seed (no Absorb)",
     lambda: S(party=("Torrent", "Liquid Ooze"), t={"moves": t_moves(s2="Leech Seed")}),
     X("THROW", reason="retaliation:Liquid Ooze")),
    ("WXh68", "[adv] the target's total PP 68 (the pass's H; below H = 76 since PD5 -> still THROW, struggle)",
     lambda: S(t={"moves": moves(("Peck", 20), ("Growl", 18), ("Focus Energy", 15), ("Quick Attack", 15))}),
     X("THROW", reason="struggle")),
    ("WXwgblock", "[adv] Wonder Guard on a 22/22 Normal/Flying target: Seismic Toss is SE+NVE -> blocked (isolates the "
                  "Wonder Guard rule W51 cannot)",
     lambda: S(t={"ability": "Wonder Guard", "species_ability": "Wonder Guard"}), X("THROW", reason="wonder-guard")),
    ("WXwgpass", "[adv] Wonder Guard on a 22/22 pure-Normal target: Seismic Toss SE only -> DAMAGE",
     lambda: S(t={"ability": "Wonder Guard", "species_ability": "Wonder Guard", "types": ("Normal",)}),
     X("DAMAGE", slot=1)),
    ("WXwgnshade", "[adv] Night Shade vs a Wonder Guard Bug/Ghost target at 50/50 (Ghost vs Ghost SE) -> DAMAGE x=13",
     lambda: S(lead=(("Tackle", 31), ("Night Shade", 15), ("Mud-slap", 10), ("Water Gun", 7)),
               t={"ability": "Wonder Guard", "species_ability": "Wonder Guard", "types": ("Bug", "Ghost"),
                  "max_hp": 50, "hp": 50}), X("DAMAGE", slot=1, move="Night Shade", x=13)),
    ("WXmax", "[adv] Seismic Toss (13) slot 1 AND Sonicboom (20) slot 2 vs 40/40 -> the largest X: Sonicboom",
     lambda: S(lead=(("Tackle", 31), ("Seismic Toss", 20), ("Sonicboom", 20), ("Water Gun", 7)),
               t={"max_hp": 40, "hp": 40}), X("DAMAGE", slot=2, move="Sonicboom", x=20)),
    ("WXtie", "[adv] Night Shade (slot 1) AND Seismic Toss (slot 2), both X=13, vs a Water 22/22 -> the LOWEST slot",
     lambda: S(lead=(("Tackle", 31), ("Night Shade", 15), ("Seismic Toss", 20), ("Water Gun", 7)),
               t={"types": ("Water",)}), X("DAMAGE", slot=1, move="Night Shade", x=13)),
    ("WXsfodd", "[adv] Super Fang at an ODD hp 21/22 -> X = 21 // 2 = 10",
     lambda: S(lead=(("Tackle", 31), ("Super Fang", 10), ("Mud-slap", 10), ("Water Gun", 7)), t={"hp": 21}),
     X("DAMAGE", slot=1, x=10)),
    ("WXvspirit", "[adv] as W57, the target's live Vital Spirit", lambda: S(lead=LEAD_SING, t={"ability": "Vital Spirit"}),
     X("THROW", reason="insomnia")),
    ("WXuproarus", "[adv] as W57, Uproar on OUR lead (status2 0x20)", lambda: S(lead=LEAD_SING, me={"status2": 0x20}),
     X("THROW", reason="uproar")),
    ("WXhypnosp", "[adv] Hypnosis (not a sound move) vs a live Soundproof -> STATUS(Hypnosis)",
     lambda: S(lead=(("Tackle", 31), ("Seismic Toss", 0), ("Hypnosis", 20), ("Water Gun", 7)),
               t={"ability": "Soundproof"}), X("STATUS", slot=2, move="Hypnosis")),
    ("WXs2bound0", "[adv] CALC=1, rate-45 target 19/30, Tackle (5, crit 14): ub = ceil(15.4)+3 = 19 -> hp-ub 0 -> THROW",
     lambda: S(lead=LEAD_ST0, t={"catch_rate": 45, "max_hp": 30, "hp": 19},
               env={"calc": True, "calc_ranges": ((5, 14), None, None, None)}), X("THROW", reason="bound")),
    ("WXs2bound1", "[adv] CALC=1, the same at 20/30: hp-ub = 1 -> DAMAGE(Tackle)",
     lambda: S(lead=LEAD_ST0, t={"catch_rate": 45, "max_hp": 30, "hp": 20},
               env={"calc": True, "calc_ranges": ((5, 14), None, None, None)}), X("DAMAGE", slot=0, move="Tackle")),
    ("WXs2half", "[adv] CALC=1, rate-45 target at 11/22 (exactly 50%), Tackle (3, 4) -> the stage-2 50% rule refuses",
     lambda: S(lead=LEAD_ST0, t={"catch_rate": 45, "hp": 11},
               env={"calc": True, "calc_ranges": ((3, 4), None, None, None)}), X("THROW", reason="half")),
    ("WXs2egain", "[adv] CALC=1, Tackle (3, 10) vs 22/22: E_gain at the MIN 3 is 0.61 < 1 -> THROW egain",
     lambda: S(lead=LEAD_ST0, env={"calc": True, "calc_ranges": ((3, 10), None, None, None)}),
     X("THROW", reason="egain")),
    ("WXs2prog", "[adv] CALC=1, a rate-3 target at 51/100, Tackle (1, 20): the MIN 1 < 10% -> THROW progress",
     lambda: S(lead=LEAD_ST0, t={"catch_rate": 3, "max_hp": 100, "hp": 51},
               env={"calc": True, "calc_ranges": ((1, 20), None, None, None)}), X("THROW", reason="progress")),
    ("WXs2tier", "[adv] CALC=1, a range supplied for a NON-Tier-A move (Flail) -> never a stage-2 candidate",
     lambda: S(lead=(("Flail", 15), ("Seismic Toss", 0), ("Mud-slap", 10), ("Water Gun", 7)),
               env={"calc": True, "calc_ranges": ((5, 10), None, None, None)}), X("THROW")),
    ("WXs2max", "[adv] CALC=1, Tackle (5, 10) slot 0 AND Water Gun (6, 10) slot 3 -> the larger MIN: Water Gun",
     lambda: S(lead=LEAD_ST0, env={"calc": True, "calc_ranges": ((5, 10), None, None, (6, 10))}),
     X("DAMAGE", slot=3, move="Water Gun")),
    ("WXdivms", "[adv] CALC=1, as W63b, the TARGET's Marvel Scale and OUR lead burned (not Guts): divergence",
     lambda: S(lead=LEAD_ST0, t={"ability": "Marvel Scale", "species_ability": "Marvel Scale"}, me={"status1": 0x10},
               env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))}),
     X("THROW", reason="divergence:marvel-scale")),
    ("WXdivff", "[adv] CALC=1, as W63b, our Flash Fire boost may be on",
     lambda: S(lead=LEAD_ST0, me={"ability": "Flash Fire", "species_ability": "Flash Fire", "flash_fire": True},
               env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))}),
     X("THROW", reason="divergence:flash-fire")),
    ("WXdivcharge", "[adv] CALC=1, as W63b, our Charge (status3 1<<9)",
     lambda: S(lead=LEAD_ST0, me={"status3": 1 << 9}, env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))}),
     X("THROW", reason="divergence:charge")),
    ("WXdivb7", "[adv] CALC=1, badge 7, the only candidate a SPECIAL move (Water Gun 5-10)",
     lambda: S(lead=LEAD_ST0, env={"calc": True, "badge7": True, "calc_ranges": (None, None, None, (5, 10))}),
     X("THROW", reason="divergence:badge7-special")),
    ("WXdivb7phys", "[adv] CALC=1, badge 7, the only candidate PHYSICAL (Tackle 5-10) -> DAMAGE (no divergence)",
     lambda: S(lead=LEAD_ST0, env={"calc": True, "badge7": True, "calc_ranges": ((5, 10), None, None, None)}),
     X("DAMAGE", slot=0, move="Tackle")),
    ("WXdivabil", "[adv] CALC=1, as W63b, the target's LIVE ability (Keen Eye) differs from its species' (Guts)",
     lambda: S(lead=LEAD_ST0, t={"ability": "Keen Eye"}, env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20))}),
     X("THROW", reason="divergence:ability-not-species")),
    ("WXfrozen", "[adv] as W57, a rate-45 target FROZEN (0x20; one-throw 0.12): the status skip is the operative rule",
     lambda: S(lead=LEAD_SING, t={"status1": 0x20, "catch_rate": 45}), X("THROW", reason="has-status")),
    ("WXegst", "[adv] a PARALYSED rate-45 target at 14/22, lead L5 (X=5): E_gain AT the status is 0.90 < 1 -> THROW "
               "egain (ignoring the status it would be 2.41)",
     lambda: S(t={"status1": 0x40, "catch_rate": 45, "hp": 14}, me={"level": 5}), X("THROW", reason="egain")),
    # ---- the PRODUCTION FIXES of the adversarial pass (PD1-PD5): each row was RED on 18b32bcc (measured before the fix,
    #      see the report) and GREEN after; each has a mutant that reverts the fix (MR*)
    ("WPtrace", "[PD1] a NON-lead Trace member (a faint-switch copies the target's LIVE Rough Skin, which then chips it "
                "every throw turn) -> THROW",
     lambda: S(party=("Torrent", "Trace"), t={"ability": "Rough Skin", "species_ability": "Rough Skin"}),
     X("THROW", reason="retaliation:Rough Skin")),
    ("WPtracectl", "[PD1 control] our own non-lead Rough Skin vs the same target -> THROW (the pre-fix rule)",
     lambda: S(party=("Torrent", "Rough Skin"), t={"ability": "Rough Skin", "species_ability": "Rough Skin"}),
     X("THROW", reason="retaliation:Rough Skin")),
    ("WPtraceguts", "[PD1 control] a Trace member vs a Guts target (a harmless copy) -> DAMAGE (the fix is scoped)",
     lambda: S(party=("Torrent", "Trace")), X("DAMAGE", slot=1)),
    ("WPpainsplit", "[PD2] the target knows Pain Split (it averages the HP before our hit) -> THROW",
     lambda: S(t={"moves": t_moves(s2="Pain Split")}), X("THROW", reason="self-harm:PAIN_SPLIT")),
    ("WPberry", "[PD3] the target holds a Figy Berry (confuse_spicy) -> no damage",
     lambda: S(t={"item": "Figy Berry", "item_effect": "confuse_spicy"}), X("THROW", reason="confusion-berry")),
    ("WPberryctl", "[PD3 control] the target holds an Oran Berry (restore_hp) -> DAMAGE (only confuse_* refuses)",
     lambda: S(t={"item": "Oran Berry", "item_effect": "restore_hp"}), X("DAMAGE", slot=1)),
    ("WPsandstream", "[PD4] a party member with Sand Stream, the target not sand-immune -> THROW",
     lambda: S(party=("Torrent", "Sand Stream")), X("THROW", reason="retaliation:Sand Stream")),
    ("WPsandstreamctl", "[PD4 control] the same vs a Ground (sand-immune) target -> DAMAGE",
     lambda: S(party=("Torrent", "Sand Stream"), t={"types": ("Ground",)}), X("DAMAGE", slot=1)),
    ("WPrecharge", "[PD5] CALC=1, Hyper Beam (RECHARGE) the only ranged slot -> never a stage-2 candidate",
     lambda: S(lead=(("Hyper Beam", 5), ("Seismic Toss", 0), ("Mud-slap", 10), ("Water Gun", 7)),
               env={"calc": True, "calc_ranges": ((5, 10), None, None, None)}), X("THROW", reason="recharge")),
    ("WPh76", "[PD5] the target's total PP exactly H = 2*(30+8) = 76 -> THROW (struggle)",
     lambda: S(t={"moves": moves(("Peck", 20), ("Growl", 18), ("Focus Energy", 20), ("Quick Attack", 18))}),
     X("THROW", reason="struggle")),
    # ---- the BUILD REVIEW's W12-N1 (2026-09-30): the DAMAGE verdict honours `banned_moves` in both stages, as STATUS
    #      always did. Each row was RED on 378a33b3 (measured before the fix) and GREEN after; reverts MNb1 / MNb2.
    ("WNbanned1", "[N1] S0 with Seismic Toss in banned_moves -> no stage-1 candidate -> THROW (banned)",
     lambda: S(env={"banned": ("Seismic Toss",)}), X("THROW", reason="banned")),
    ("WNbanned2", "[N1] CALC=1, as W63b with Tackle in banned_moves -> Water Gun's bound and Mud-slap's progress fail "
                  "-> THROW (banned)",
     lambda: S(lead=LEAD_ST0, env={"calc": True, "calc_ranges": ((5, 10), None, (0, 0), (8, 20)), "banned": ("Tackle",)}),
     X("THROW", reason="banned@0")),
]
PURE_IDS = [r[0] for r in PURE]


def decide(snap):
    t, me, party, env, memo = snap
    return WC().decide_weaken_turn(t, me, party, env, memo)


def pure_rows(tag=""):
    reds: list = []
    for rid, what, build, want in PURE:
        def fn(build=build, want=want):
            d = decide(build())
            bad = want.diff(d)
            return not bad, bad or f"{d.verdict} slot={d.slot} move={d.move} ball={d.ball} reason={d.reason}"
        row(f"{rid} {what}", fn, tag, reds)
    return reds


def wx_rows(tag=""):
    """The adversarial pass's function-style rows (folded 2026-09-30; NOT pre-registered)."""
    reds: list = []

    def bt_sweep():
        bad = []
        for bit in range(32):
            d = decide(S(env={"battle_flags": 0x4 | (1 << bit)}))
            want_defer = bit not in (2, 31)
            if want_defer and not (d.verdict == "DEFER" and "battle-type" in d.reason):
                bad.append(f"bit{bit}:{d.verdict}/{d.reason}")
            if not want_defer and d.verdict == "DEFER":
                bad.append(f"bit{bit}:DEFER")
        d0 = decide(S(env={"battle_flags": 0}))
        if d0.verdict != "DAMAGE":
            bad.append(f"flags0:{d0.verdict}")
        return not bad, f"bad {bad}"

    def cap_seq():
        """Caps through remember() (the cap rows build memos by hand): turn 0 DAMAGE, a turn-0 re-entry DAMAGE (one
        history entry), turn 1 at 9/22 on a rate-45 target (the hit landed; one-throw 0.12) -> the damage cap."""
        w = WC()
        t0, me, party, env, _ = S(t={"catch_rate": 45})
        memo = None
        d0 = w.decide_weaken_turn(t0, me, party, env, memo)
        memo = w.remember(memo, t0, env, d0)
        d0b = w.decide_weaken_turn(t0, me, party, env, memo)
        memo = w.remember(memo, t0, env, d0b)
        d1 = w.decide_weaken_turn(T0(catch_rate=45, hp=9), me, party, E0(turn=1), memo)
        ok = (d0.verdict == "DAMAGE" and d0b.verdict == "DAMAGE" and d1.verdict == "THROW" and "damage-cap" in d1.reason
              and len(memo.history) == 1)
        return ok, f"{d0.verdict} {d0b.verdict} {d1.verdict}/{d1.reason} hist {memo.history}"

    def balls():
        w = WC()

        def b(name, **kw):
            base = dict(level=6, types=("Normal", "Flying"), turn=0, underwater=False, owned=False)
            base.update(kw)
            return w.ball_bonus_x10(name, **base)
        got = {"Ultra": b("Ultra Ball"), "Great": b("Great Ball"), "Safari": b("Safari Ball"), "Poke": b("Poké Ball"),
               "Dive-under": b("Dive Ball", underwater=True), "Dive-land": b("Dive Ball"),
               "Repeat-owned": b("Repeat Ball", owned=True), "Repeat-new": b("Repeat Ball"),
               "Luxury": b("Luxury Ball"), "Premier": b("Premier Ball"), "Nest-L45": b("Nest Ball", level=45),
               "Nest-L35": b("Nest Ball", level=35)}
        want = {"Ultra": 20, "Great": 15, "Safari": 15, "Poke": 10, "Dive-under": 35, "Dive-land": 10,
                "Repeat-owned": 30, "Repeat-new": 10, "Luxury": 10, "Premier": 10, "Nest-L45": 10, "Nest-L35": 10}
        return got == want, f"{got}"

    def cp_status():
        """freeze x2 (the W67c sleep chain: odds 132, b 58253); toxic x15//10 (the W67d chain: odds 99, b 52428)."""
        w = WC()
        frz = w.catch_p(200, 10, 22, 22, 0x20)
        tox = w.catch_p(200, 10, 22, 22, 0x80)
        return frz == (58253 / 65536) ** 4 and tox == (52428 / 65536) ** 4, f"freeze {frz!r} toxic {tox!r}"

    cases = [
        ("WXbtsweep [adv] every gBattleTypeFlags bit but IS_MASTER / RECORDED_IS_MASTER DEFERs; flags 0 acts", bt_sweep),
        ("WXcapseq [adv] the damage cap through remember(): a same-turn re-entry repeats DAMAGE; the next turn caps",
         cap_seq),
        ("WXballs [adv] the ball table: Ultra 20, Great/Safari 15, Dive 35 underwater, Repeat 30 owned, Nest 10 at L35+",
         balls),
        ("WXcpstatus [adv] catch_p: freeze x2, toxic x15//10", cp_status),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ================================================================================================= W67 catch anchors
def chain(rate, bonus, mx, hp, status1=0) -> dict:
    """The GATE's own integer walk of `battle_script_commands.c:9987-10028` (the literals below are its hand derivation;
    this function only re-checks the arithmetic of each literal)."""
    from math import isqrt as _isqrt
    a = rate * bonus // 10
    odds = a * (3 * mx - 2 * hp) // (3 * mx)
    if status1 & 0x27:
        odds *= 2
    if status1 & 0xD8:
        odds = odds * 15 // 10
    if odds > 254:
        return {"odds": odds, "p": 1.0}
    q = 16711680 // odds
    s1 = _isqrt(q)
    s2 = _isqrt(s1)
    return {"odds": odds, "q": q, "s1": s1, "s2": s2, "b": 1048560 // s2}


#: HAND-DERIVED (each step checked with pencil arithmetic; the PREDICTIONS' W-row anchors, plus the ball table's).
ANCHORS = {
    # W67a: Taillow full HP, Poké: odds = 200*(66-44)//66 = 66; 16711680//66 = 253207 (66*253207 = 16711662);
    #       isqrt 503 (503^2 = 253009 <= 253207 < 254016); isqrt 22; b = 1048560//22 = 47661
    "W67a": ((200, 10, 22, 22, 0), {"odds": 66, "q": 253207, "s1": 503, "s2": 22, "b": 47661}),
    # W67b: hp 9: odds = 200*48//66 = 145; 16711680//145 = 115252 (145*115252 = 16711540, remainder 140; the
    #       PREDICTIONS wrote 115253, an off-by-one in the note that no later step inherits); isqrt 339; 18; b = 58253
    "W67b": ((200, 10, 22, 9, 0), {"odds": 145, "q": 115252, "s1": 339, "s2": 18, "b": 58253}),
    # W67c: sleep x2 at full HP: odds 66*2 = 132; 16711680//132 = 126603; isqrt 355 (355^2 = 126025); 18; b 58253
    "W67c": ((200, 10, 22, 22, S1_SLEEP2), {"odds": 132, "q": 126603, "s1": 355, "s2": 18, "b": 58253}),
    # W67d: paralysis x15//10: odds 66*15//10 = 99; 16711680//99 = 168804; isqrt 410 (410^2 = 168100); 20; b 52428
    "W67d": ((200, 10, 22, 22, S1_PARALYSIS), {"odds": 99, "q": 168804, "s1": 410, "s2": 20, "b": 52428}),
    # W67e (the boundary): rate 255 Poké at 1/200: odds = 255*598//600 = 254 -> NOT caught outright;
    #       16711680//254 = 65794; isqrt 256; 16; b = 65535 (the largest b there is: p = (65535/65536)^4 < 1)
    "W67e": ((255, 10, 200, 1, 0), {"odds": 254, "q": 65794, "s1": 256, "s2": 16, "b": 65535}),
    # W67e2: rate 255 Great (a = 3825//10 = 382) at 99/200: odds = 382*402//600 = 255 > 254 -> 1.0
    "W67e2": ((255, 15, 200, 99, 0), {"odds": 255, "p": 1.0}),
    # W67f: the Nest Ball at L6 = 40 - 6 = 34: a = 680; odds = 680*22//66 = 226; 16711680//226 = 73945; 271; 16; 65535
    "W67f": ((200, 34, 22, 22, 0), {"odds": 226, "q": 73945, "s1": 271, "s2": 16, "b": 65535}),
    # W67g: the Net Ball (30) vs a LIVE Bug type: a = 600; odds = 600*22//66 = 200; 16711680//200 = 83558; 289; 17;
    #       b = 1048560//17 = 61680
    "W67g": ((200, 30, 22, 22, 0), {"odds": 200, "q": 83558, "s1": 289, "s2": 17, "b": 61680}),
    # W67k: the LIVE arms' anchors (PREDICTIONS, ST at f165971): Taillow 21/21 -> odds 66 -> b 47661; at 6/21:
    #       odds = 200*51//63 = 161; 16711680//161 = 103799; isqrt 322; 17; b = 61680
    "W67k": ((200, 10, 21, 21, 0), {"odds": 66, "q": 253207, "s1": 503, "s2": 22, "b": 47661}),
    "W67k2": ((200, 10, 21, 6, 0), {"odds": 161, "q": 103799, "s1": 322, "s2": 17, "b": 61680}),
    # W67l: the INTEGER ORDER: a Great Ball on a rate-45 target at 8/22: a = 675//10 = 67 (not 67.5);
    #       odds = 67*50//66 = 50; 16711680//50 = 334233; isqrt 578; 24; b = 43690. (The float order gives 51 -> 45589.)
    "W67l": ((45, 15, 22, 8, 0), {"odds": 50, "q": 334233, "s1": 578, "s2": 24, "b": 43690}),
}


def _anchor_ok(key):
    args, lit = ANCHORS[key]
    got = chain(*args)
    if got != lit:
        return False, f"{key}: the gate's arithmetic {got} != the hand derivation {lit}"
    want = 1.0 if "p" in lit else (lit["b"] / 65536) ** 4
    p = WC().catch_p(*args)
    return p == want, f"{key}: catch_p{args} = {p!r} (want {want!r})"


def w67_rows(tag=""):
    reds: list = []

    def both(*keys):
        def fn():
            out = [_anchor_ok(k) for k in keys]
            return all(ok for ok, _ in out), " | ".join(d for _, d in out)
        return fn

    def nest():
        w = WC()
        bonus = w.ball_bonus_x10("Nest Ball", level=6, types=("Normal", "Flying"), turn=0, underwater=False,
                                 owned=False)
        ok, detail = _anchor_ok("W67f")
        p = w.catch_p_ball("Nest Ball", T0(), E0(), 22, 0)
        return (bonus == 34 and ok and p == (65535 / 65536) ** 4), f"bonus {bonus}; {detail}; catch_p_ball {p!r}"

    def net():
        w = WC()
        b_bug = w.ball_bonus_x10("Net Ball", level=6, types=("Bug", "Ground"), turn=0, underwater=False, owned=False)
        b_plain = w.ball_bonus_x10("Net Ball", level=6, types=("Normal", "Flying"), turn=0, underwater=False,
                                   owned=False)
        ok, detail = _anchor_ok("W67g")
        # the LIVE types decide: a Taillow (species Normal/Flying) whose battle types read Bug
        p = w.catch_p_ball("Net Ball", T0(types=("Bug",)), E0(), 22, 0)
        return (b_bug == 30 and b_plain == 10 and ok and p == (61680 / 65536) ** 4), \
            f"bug {b_bug}, plain {b_plain}; {detail}; live-Bug catch_p_ball {p!r}"

    def timer():
        w = WC()
        got = {t: w.ball_bonus_x10("Timer Ball", level=6, types=(), turn=t, underwater=False, owned=False)
               for t in (0, 5, 30, 45)}
        return got == {0: 10, 5: 15, 30: 40, 45: 40}, f"{got}"

    def master():
        w = WC()
        b = w.ball_bonus_x10("Master Ball", level=6, types=(), turn=0, underwater=False, owned=False)
        p = w.catch_p_ball("Master Ball", T0(), E0(), 22, 0)
        return b is None and p == 1.0, f"bonus {b}, p {p}"

    cases = [
        ("W67a catch_p Poké, Taillow 22/22: b 47661 (hand-derived)", both("W67a")),
        ("W67b catch_p at hp 9/22: b 58253 (non-full HP)", both("W67b")),
        ("W67c sleep x2 at full HP: odds 132, b 58253", both("W67c")),
        ("W67d paralysis x15//10: odds 99, b 52428", both("W67d")),
        ("W67e odds 254 is NOT certain (b 65535); odds 255 is 1.0", both("W67e", "W67e2")),
        ("W67f the Nest Ball at L6: bonus 34, odds 226", nest),
        ("W67g the Net Ball vs a LIVE Bug type: 30 (10 otherwise)", net),
        ("W67h the Timer Ball: turn 5 -> 15; 0 -> 10; capped at 40", timer),
        ("W67i the Master Ball: forced success, 1.0", master),
        ("W67k the live arms' anchors: 21/21 -> b 47661; 6/21 -> b 61680", both("W67k", "W67k2")),
        ("W67l the integer order: Great, rate 45, 8/22 -> odds 50 (not 51), b 43690", both("W67l")),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ================================================================================================= W68 sweep
def w68_rows(tag=""):
    reds: list = []

    def fn():
        w = WC()
        bad = []
        for rid, _what, build, _want in PURE:
            t, me, party, env, memo = build()
            d = w.decide_weaken_turn(t, me, party, env, memo)
            if d.verdict not in ("DAMAGE", "STATUS", "THROW", "DEFER"):
                bad.append(f"{rid}:verdict {d.verdict}")
            elif d.verdict == "THROW" and d.ball not in w.BALLS:
                bad.append(f"{rid}:item {d.ball!r}")
            elif d.verdict in ("DAMAGE", "STATUS") and (d.slot not in range(4) or me.moves[d.slot] is None):
                bad.append(f"{rid}:slot {d.slot}")
            elif d.verdict == "DEFER" and (d.ball is not None or d.slot is not None):
                bad.append(f"{rid}:defer carries an action")
        return not bad, f"{len(PURE)} snapshots; bad {bad}"

    row("W68 every snapshot: only a defined verdict; a THROW names only a Poké Ball (RULING 27)", fn, tag, reds)
    return reds


# ================================================================================================= the ADAPTER world
POKE = get_item_by_name("Poké Ball")
ORIG_GBS = modules.battle_state.get_battle_state
PARENT = ("PARENT", None)


def mon_rec(species, mvs, pp, hp, maxhp, level, ability_n, type1, type2, pid, status1=0, status2=0, item=0) -> bytes:
    """A 0x58-byte `struct BattlePokemon` (include/battle.h) from named fields."""
    raw = bytearray(0x58)
    struct.pack_into("<6H", raw, 0x00, species, 20, 20, 20, 20, 20)
    struct.pack_into("<4H", raw, 0x0C, *mvs)
    raw[0x18:0x20] = bytes([6] * 8)
    raw[0x20], raw[0x21], raw[0x22] = ability_n, type1, type2
    raw[0x24:0x28] = bytes(pp)
    struct.pack_into("<H", raw, 0x28, hp)
    raw[0x2A] = level
    struct.pack_into("<HH", raw, 0x2C, maxhp, item)
    struct.pack_into("<III", raw, 0x48, pid, status1, status2)
    return bytes(raw)


def party_rec(pid, species, hp, ability_bit=0, otid=0x00BEEF01) -> bytes:
    """A GENUINE 100-byte party record (real substructure order, XOR encryption, checksum), as
    `repro_pid_identity_key.build_mon` builds one, plus the ability bit (misc word 1, bit 31) and the current HP."""
    order = POKEMON_DATA_SUBSTRUCTS_ORDER[pid % 24]
    key = pid ^ otid
    logical = [struct.pack("<H", species) + bytes(10), bytes(12), bytes(12),
               bytes(4) + struct.pack("<I", (ability_bit & 1) << 31) + bytes(4)]
    checksum = sum(struct.unpack("<24H", b"".join(logical))) & 0xFFFF
    raw = [b""] * 4
    for li, chunk in enumerate(logical):
        raw[order[li]] = b"".join(struct.pack("<I", struct.unpack_from("<I", chunk, w * 4)[0] ^ key) for w in range(3))
    header = bytearray(32)
    struct.pack_into("<II", header, 0, pid, otid)
    header[19] = 0x02                                       # hasSpecies
    struct.pack_into("<H", header, 28, checksum)
    tail = bytearray(20)
    struct.pack_into("<H", tail, 6, hp)                     # offset 86: current HP
    return bytes(header) + b"".join(raw) + bytes(tail)


def party_bytes(members) -> tuple[bytes, int]:
    blob = b"".join(party_rec(*m) for m in members)
    return blob + bytes(600 - len(blob)), len(members)


PARTY_DEFAULT = ((PID_M, SPECIES_ID["Mudkip"], 40), (0x11111111, SPECIES_ID["Poochyena"], 17),
                 (0x22222222, SPECIES_ID["Nincada"], 20), (0x33333333, SPECIES_ID["Whismur"], 23))
PARTY_ROUGH = ((PID_M, SPECIES_ID["Mudkip"], 40), (0x11111111, SPECIES_ID["Poochyena"], 17),
               (0x44444444, SPECIES_ID["Carvanha"], 30), (0x33333333, SPECIES_ID["Whismur"], 23))
ME_REC = dict(species=SPECIES_ID["Mudkip"], mvs=(33, 69, 189, 55), pp=(31, 20, 10, 7), hp=40, maxhp=40, level=13,
              ability_n=67, type1=11, type2=11, pid=PID_M)
FOE_REC = dict(species=SPECIES_ID["Taillow"], mvs=(64, 45, 116, 98), pp=(35, 40, 30, 30), hp=22, maxhp=22, level=6,
               ability_n=62, type1=0, type2=2, pid=PID_T)


def real_state(foe_hp=22, disable0=bytes(0x1C), *, flags=0x4, foe=None, me=None, side_timers=bytes(24)):
    """A REAL single wild BattleState (flags = IS_MASTER, as the Step-0 reads log) from two raw records (`foe`/`me`
    override FOE_REC/ME_REC fields; `side_timers` is gSideTimers). Its own turn counter stays 0 whatever
    `gBattleResults` says: a reader that trusts it over the pure read is caught (WBact)."""
    f = dict(FOE_REC, hp=foe_hp, **(foe or {}))
    m = dict(ME_REC, **(me or {}))
    return BattleState(battle_type=struct.pack("<I", flags), side_timers=side_timers,
                       battler_party_indexes=struct.pack("<HHHH", 0, 0, 0, 0),
                       battler_party_order=bytes([0x01, 0x23, 0x45]), battler_count=2,
                       battler=mon_rec(**m) + mon_rec(**f) + bytes(0x58 * 2), battler_status3=bytes(16),
                       battler_disable_structs=disable0 + bytes(0x1C * 3), absent_battler_flags=0, current_turn=0,
                       weather=0)


class Bag:
    def __init__(self, qty):
        self.poke_balls = [types.SimpleNamespace(item=POKE, quantity=qty)] if qty else []
        self.number_of_balls_except_master_ball = qty


_PARTY_CACHE: dict = {}


@contextlib.contextmanager
def aworld(*, flag="1", kind="team", calc=False, turn=0, balls=30, disable0=bytes(0x1C), party=PARTY_DEFAULT,
           decide_raises=False, kinds=("dex", "team"), sp="Taillow#276", status3=bytes(8), sides=bytes(4),
           weather=bytes(2), banned=None, bag=None, badge7=False, decide_stub=None):
    """Production's world for the ADAPTER rows: a stand-in mode on SM's `context` (its kinds and the context's `sp` as
    given); `read_symbol` over fake symbols (recorded; gStatuses3 / gSideStatuses / gBattleWeather as given); the bag
    (`balls` Poké Balls, or `bag`); the allowlist (None: every ball but the Master Ball); the badge reads (only
    BADGE07_GET, when `badge7`); `banned_moves` (the real config unless given); the logger (recorded); the parent
    `CatchStrategy.decide_turn` (a PARENT sentinel); `get_battle_state` REBOUND wherever bound (counted: every adapter
    row asserts 0); `decide_weaken_turn` spied (counted), raising, or replaced by `decide_stub`."""
    sm, w = SM(), WC()
    mode = types.SimpleNamespace(_r25_weaken=flag, _r25_weaken_calc=calc, _r25_weaken_kinds=tuple(kinds),
                                 _catch_ctx={"kind": kind, "sp": sp})
    log = types.SimpleNamespace(events=[], reads=[], gbs=[], calls=[], mode=mode)
    if party not in _PARTY_CACHE:
        _PARTY_CACHE[party] = party_bytes(party)
    pb, count = _PARTY_CACHE[party]
    syms = {"gBattleResults": bytes(0x13) + bytes([turn]) + bytes(12), "gStatuses3": status3,
            "gDisableStructs": disable0 + bytes(0x1C), "gSideStatuses": sides, "gBattleWeather": weather,
            "gPlayerPartyCount": bytes([count]), "gPlayerParty": pb}

    def fake_read(name, offset=0, size=0):
        log.reads.append(name)
        return syms[name][offset:offset + size]

    def fake_event(message, *, category="STORY"):
        log.events.append((category, message))

    def spy_gbs(*_a, **_k):
        log.gbs.append(1)
        return real_state()

    real_decide = w.decide_weaken_turn

    def spy_decide(*a, **k):
        log.calls.append(1)
        if decide_raises:
            raise RuntimeError("the module raised")
        if decide_stub is not None:
            return decide_stub(w)
        return real_decide(*a, **k)

    config = modules.context.context.config
    if banned is not None:
        config = types.SimpleNamespace(battle=types.SimpleNamespace(banned_moves=list(banned)))
    ctx = types.SimpleNamespace(bot_mode_instance=mode, message="", config=config)
    if bag is None:
        bag = Bag(balls)
    patches = [(modules.memory, "read_symbol", fake_read),
               (modules.memory, "get_event_flag", lambda _n: bool(badge7) and _n == "BADGE07_GET"),
               (modules.battle_strategies._util, "get_event_flag", lambda _n: False),
               (modules.debug_logger, "event", fake_event), (modules.items, "get_item_bag", lambda: bag),
               (modules.battle_strategies.catch, "get_item_bag", lambda: bag),
               (modules.catch_balls, "allowed_ball_names", lambda: None),
               (modules.battle_strategies.catch.CatchStrategy, "decide_turn", lambda self, bs: PARENT),
               (sm, "context", ctx), (w, "decide_weaken_turn", spy_decide)]
    for mod in list(sys.modules.values()):
        if isinstance(mod, types.ModuleType) and mod.__dict__.get("get_battle_state") is ORIG_GBS:
            patches.append((mod, "get_battle_state", spy_gbs))
    saved = [(m, n, getattr(m, n)) for m, n, _f in patches]
    try:
        for m, n, f in patches:
            setattr(m, n, f)
        yield log
    finally:
        for m, n, f in saved:
            setattr(m, n, f)


def wlines(log):
    return [(c, m) for c, m in log.events if "WEAKEN" in c or "WEAKEN" in m]


def _new(cls_name, **fields):
    cls = getattr(SM(), cls_name)
    obj = cls.__new__(cls)
    for k, v in fields.items():
        setattr(obj, k, v)
    return obj


def _field(message, key):
    m = re.search(rf"(?:^| ){key}=(\S+)", message)
    return m.group(1) if m else None


def adapter_rows(tag=""):
    reds: list = []

    def w62():
        s = _new("StoryCatchStrategy")
        with aworld(flag="observe") as log:
            act = s.decide_turn(real_state())
        lines = wlines(log)
        if len(lines) != 1:
            return False, f"{len(lines)} WEAKEN lines: {lines}"
        cat, msg = lines[0]
        snap = json.loads(msg.split(" snap=", 1)[1])
        t, me, party, env, memo = WC().snapshot_from_json(msg.split(" snap=", 1)[1])
        replay = WC().decide_weaken_turn(t, me, party, env, memo)
        ok = (act == PARENT and cat == "WEAKEN" and msg.startswith("[WEAKEN-OBS] would=DAMAGE ")
              and _field(msg, "first") == "1" and _field(msg, "hp") == "22/22" and _field(msg, "st") == "0"
              and _field(msg, "tmv") == "64:35,45:40,116:30,98:30" and _field(msg, "slot") == "1"
              and snap["party"]["abilities"] == list(PARTY_S0) and replay.verdict == "DAMAGE" and not log.gbs
              and log.calls == [1])
        return ok, f"action {act}; [{cat}] {msg[:150]}…; party {snap['party']['abilities']}; replay " \
                   f"{replay.verdict}; gbs {len(log.gbs)}"

    def w65a():
        sm = SM()
        s = _new("StoryDexCatchStrategy", _fainted_this_battle=False, bail_reason=None, _no_faint_bail=False)
        real_escape = sm.StoryDexCatchStrategy.__dict__["_escape"]
        try:
            sm.StoryDexCatchStrategy._escape = staticmethod(lambda bs: TurnAction.run_away())
            with aworld(balls=sm.DEX_CATCH_BALL_RESERVE) as log:
                act = s.decide_turn(real_state())
        finally:
            sm.StoryDexCatchStrategy._escape = real_escape
        return (act == TurnAction.run_away() and not wlines(log) and not log.calls and s.bail_reason is not None
                and not log.gbs), f"action {act}; weaken lines {wlines(log)}; module calls {len(log.calls)}"

    def w65b():
        s = _new("StoryCatchStrategy")
        s._get_best_poke_ball = lambda bs: None
        with aworld() as log:
            act = s.decide_turn(real_state())
        return (act == TurnAction.run_away() and not wlines(log) and not log.calls and not log.gbs), \
            f"action {act}; weaken lines {wlines(log)}; module calls {len(log.calls)}"

    def w65c():
        s = _new("StoryCatchStrategy")
        with aworld(decide_raises=True) as log:
            act = s.decide_turn(real_state())
        lines = wlines(log)
        return (act == PARENT and len(lines) == 1 and lines[0][0] == "WEAKEN" and lines[0][1].startswith("ERR ")
                and not log.gbs), f"action {act}; lines {lines}"

    def w65d():
        s = _new("StoryCatchStrategy")
        with aworld(flag="") as log:
            act = s.decide_turn(real_state())
        return (act == PARENT and not wlines(log) and not log.reads and not log.calls and not log.gbs), \
            f"action {act}; lines {wlines(log)}; reads {log.reads}; module calls {len(log.calls)}"

    def w65e():
        s = _new("StoryShinyCatchStrategy")
        with aworld() as log:                     # flag 1, kind team: the adapter WOULD act if reached
            act = s.decide_turn(real_state())
        return (act == PARENT and not wlines(log) and not log.calls and not log.gbs), \
            f"action {act}; lines {wlines(log)}; module calls {len(log.calls)}"

    def wbact():
        s = _new("StoryCatchStrategy")
        state = real_state()
        with aworld(turn=0) as log0:
            a0 = s.decide_turn(state)
        with aworld(turn=1) as log1:
            a1 = s.decide_turn(state)
        l0, l1 = wlines(log0), wlines(log1)
        ok = (a0 == TurnAction.use_move(1) and a1 == TurnAction.use_item(POKE) and len(l0) == 1 and len(l1) == 1
              and all(c == "WEAKEN" for c, _m in l0 + l1) and l0[0][1].startswith("act=DAMAGE ")
              and l1[0][1].startswith("act=THROW ") and "damage-cap" in (_field(l1[0][1], "reason") or "")
              and not log0.gbs and not log1.gbs)
        return ok, f"turn 0 {a0} {[m[:60] for _c, m in l0]}; turn 1 {a1} {[m[:90] for _c, m in l1]}"

    def wbthrow():
        s = _new("StoryCatchStrategy")
        with aworld() as log:
            act = s.decide_turn(real_state(foe_hp=7))
        lines = wlines(log)
        return (act == TurnAction.use_item(POKE) and len(lines) == 1 and lines[0][0] == "WEAKEN"
                and lines[0][1].startswith("act=THROW ") and not log.gbs), f"action {act}; lines {lines}"

    def wbkind():
        s = _new("StoryCatchStrategy")
        with aworld(kind="hm") as log:
            act = s.decide_turn(real_state())
        return (act == PARENT and not wlines(log) and not log.reads and not log.calls), \
            f"action {act}; lines {wlines(log)}; reads {log.reads}"

    def wbencore():
        s = _new("StoryCatchStrategy")
        d0 = dis(encored=33)
        with aworld(disable0=d0) as log:
            act = s.decide_turn(real_state(disable0=d0))
        lines = wlines(log)
        return (act == TurnAction.use_item(POKE) and len(lines) == 1 and lines[0][0] == "WEAKEN"
                and "encore-on-us" in (_field(lines[0][1], "reason") or "") and not log.gbs), \
            f"action {act}; lines {[m[:120] for _c, m in lines]}"

    def wbparty():
        s = _new("StoryCatchStrategy")
        with aworld(party=PARTY_ROUGH) as log:
            act = s.decide_turn(real_state())
        lines = wlines(log)
        return (act == TurnAction.use_item(POKE) and len(lines) == 1 and lines[0][0] == "WEAKEN"
                and "retaliation:Rough_Skin" in (_field(lines[0][1], "reason") or "") and not log.gbs), \
            f"action {act}; lines {[m[:140] for _c, m in lines]}"

    def wbflags():
        sm = SM()
        got = {}
        saved = {k: os.environ.get(k) for k in (FLAG, FLAG_CALC, FLAG_KINDS)}
        try:
            for value in (None, "observe", "1", "0", "yes"):
                for k in (FLAG, FLAG_CALC, FLAG_KINDS):
                    os.environ.pop(k, None)
                if value is not None:
                    os.environ[FLAG] = value
                    os.environ[FLAG_CALC] = "1"
                    os.environ[FLAG_KINDS] = "dex, team ,hm"
                m = sm.StoryMode.__new__(sm.StoryMode)
                sm.StoryMode.reset_per_run_state(m)
                got[value] = (m._r25_weaken, m._r25_weaken_calc, m._r25_weaken_kinds)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        want = {None: ("", False, ("dex", "team")), "observe": ("observe", True, ("dex", "team", "hm")),
                "1": ("1", True, ("dex", "team", "hm")), "0": ("", True, ("dex", "team", "hm")),
                "yes": ("", True, ("dex", "team", "hm"))}
        return got == want, f"{got}"

    cases = [
        ("W62 observe: the parent's action unchanged; ONE [WEAKEN-OBS] would=DAMAGE … first=1 (its snapshot: HP, "
         "status, moves, the party read; it replays)", w62),
        ("W65a the dex reserve bail fires first (the adapter is never reached)", w65a),
        ("W65b the out-of-balls flee fires first (the adapter is never reached)", w65b),
        ("W65c an exception in the module -> DEFER (the parent's action) plus exactly ONE [WEAKEN] ERR line", w65c),
        ("W65d the flag unset -> the parent's action, 0 lines containing WEAKEN, 0 reads", w65d),
        ("W65e the shiny strategy never reaches the adapter (flag 1, kind team)", w65e),
        ("WBact [builder] flag 1: turn 0 -> use_move(1) + act=DAMAGE; turn 1 (the PURE turn read) -> the damage cap: "
         "use_item(Poké Ball) + act=THROW", wbact),
        ("WBthrow [builder] flag 1, the target at 7/22 -> use_item(the parent's ball) + act=THROW", wbthrow),
        ("WBkind [builder] kind hm -> no read, no line, the parent's action", wbkind),
        ("WBencore [builder] the RAW gDisableStructs read: encoredMove at 0x06 -> act=THROW encore-on-us", wbencore),
        ("WBparty [builder] the party read: a non-lead Rough Skin (Carvanha) -> act=THROW retaliation", wbparty),
        ("WBflags [builder] reset_per_run_state parses the three flags once per run ('0'/'yes' are OFF)", wbflags),
    ]

    # ---- ADVERSARIAL-PASS adapter rows (`scratchpad/w12m/proposed.py` PA-*, folded 2026-09-30): each runs the REAL
    #      StoryCatchStrategy in the generalised world and, unlike the pass's own version, ALSO asserts that
    #      get_battle_state was never called (else MA6 would miss them)
    def one(state, **world):
        s = _new("StoryCatchStrategy")
        with aworld(**world) as log:
            act = s.decide_turn(state)
        return act, wlines(log), log

    def reason(lines):
        return (_field(lines[0][1], "reason") or "") if lines else ""

    def throws(state, want_reason, **world):
        act, lines, log = one(state, **world)
        return (act == TurnAction.use_item(POKE) and len(lines) == 1 and want_reason in reason(lines)
                and not log.gbs), f"{act} {reason(lines)} gbs {len(log.gbs)}"

    def defers(state, want_reason, **world):
        act, lines, log = one(state, **world)
        return (act == PARENT and len(lines) == 1 and lines[0][1].startswith("act=DEFER") and want_reason in reason(lines)
                and not log.gbs), f"{act} {lines[:1]} gbs {len(log.gbs)}"

    def acts(state, want_act, **world):
        act, lines, log = one(state, **world)
        return act == want_act and not log.gbs, f"{act} {reason(lines)} gbs {len(log.gbs)}"

    sing_me = {"mvs": (33, 69, 47, 55), "pp": (31, 0, 15, 7)}      # Tackle, Seismic Toss at PP 0, Sing, Water Gun

    def a_st3():
        return throws(real_state(), "ticking:leech-seed", status3=bytes(4) + struct.pack("<I", 1 << 2))

    def a_st3_ours():
        act, lines, log = one(real_state(), status3=struct.pack("<I", 1 << 2) + bytes(4))
        return (act == TurnAction.use_move(1) and bool(lines) and lines[0][1].startswith("act=DAMAGE")
                and not log.gbs), f"{act} {reason(lines)} gbs {len(log.gbs)}"

    def a_side():
        return throws(real_state(), "ticking:future-sight", sides=struct.pack("<HH", 0, 1 << 6))

    def a_side_ours():
        return acts(real_state(), TurnAction.use_move(1), sides=struct.pack("<HH", 1 << 6, 0))

    def a_weather():
        return throws(real_state(), "weather:hail", weather=struct.pack("<H", 0x80))

    def a_s1():
        return throws(real_state(foe={"status1": 0x8}), "ticking:status1")

    def a_liveab():
        return throws(real_state(me={"ability_n": 24}), "retaliation:Rough_Skin")   # our LIVE Rough Skin (species Torrent)

    def a_types():
        return throws(real_state(foe={"type1": 7, "type2": 7}), "immune")          # LIVE types read Ghost

    def a_flags():
        return defers(real_state(flags=0x4 | 0x8), "battle-type")

    def a_choice():
        return defers(real_state(me={"item": 186}), "choice")                      # Choice Band (items.json 186)

    def a_usable():
        return throws(real_state(foe={"pp": (15, 15, 15, 15)}), "struggle-pp")    # total 60 <= H

    def a_kinds():
        act, lines, log = one(real_state(), kinds=("dex",))
        return (act == PARENT and not lines and not log.reads and not log.gbs), f"{act} lines {lines} reads {log.reads}"

    def a_obs2():
        s = _new("StoryCatchStrategy")
        with aworld(flag="observe", turn=0) as l0:
            a0 = s.decide_turn(real_state())
        with aworld(flag="observe", turn=1) as l1:
            a1 = s.decide_turn(real_state())
        w0, w1 = wlines(l0), wlines(l1)
        ok = (a0 == PARENT and a1 == PARENT and len(w0) == 1 and len(w1) == 1
              and w0[0][1].startswith("[WEAKEN-OBS] would=DAMAGE") and _field(w0[0][1], "first") == "1"
              and w1[0][1].startswith("[WEAKEN-OBS] would=THROW") and "damage-cap" in (_field(w1[0][1], "reason") or "")
              and _field(w1[0][1], "first") == "0" and not l0.gbs and not l1.gbs)
        return ok, f"{a0} {a1} | {[m[:70] for _c, m in w0 + w1]}"

    def a_ctx2():
        s = _new("StoryCatchStrategy")
        out = []
        for t in (0, 1):
            with aworld(turn=t, sp="Poochyena#261") as lg:
                a = s.decide_turn(real_state())
            out.append((a, wlines(lg), lg.gbs))
        ok = all(a == PARENT and len(ls) == 1 and ls[0][1].startswith("act=DEFER") and "context" in reason(ls) and not g
                 for a, ls, g in out)
        return ok, f"{[(a, reason(ls)) for a, ls, _g in out]}"

    def a_banned():
        return throws(real_state(me=sing_me), "banned", banned=("Sing",))

    def a_banned_ctl():
        return acts(real_state(me=sing_me), TurnAction.use_move(2), banned=())

    def a_safeguard():
        st = bytearray(24)
        st[12 + 6] = 5                                         # the OPPONENT side's Safeguard timer (gSideTimers[1])
        return throws(real_state(me=sing_me, side_timers=bytes(st)), "safeguard")

    def a_charge():
        """CALC=1 through the REAL calculator: our lead Charged (gStatuses3[0] bit 9), Seismic Toss at PP 0."""
        return throws(real_state(me={"pp": (31, 0, 10, 7)}), "divergence:charge",
                      status3=struct.pack("<I", 1 << 9) + bytes(4), calc=True)

    def a_b7():
        """CALC=1, BADGE07_GET set, Water Gun the only move with PP: a special move under badge 7 is a divergence."""
        return throws(real_state(me={"pp": (0, 0, 0, 7)}), "divergence:badge7-special", calc=True, badge7=True)

    class Bag2:
        def __init__(self):
            self.poke_balls = [types.SimpleNamespace(item=get_item_by_name("Master Ball"), quantity=1),
                               types.SimpleNamespace(item=POKE, quantity=30)]
            self.number_of_balls_except_master_ball = 30

    def a_master():
        return acts(real_state(foe_hp=7), TurnAction.use_item(POKE), bag=Bag2())

    def wp_nit():
        """The grading nit: a THROW whose ball the bag does not hold is logged `act=DEFER`, and the memo must record
        what was DONE (DEFER), not the verdict (THROW). The module is stubbed to name a Premier Ball the bag lacks."""
        s = _new("StoryCatchStrategy")
        with aworld(decide_stub=lambda w: w.WDecision(w.THROW, "stub", ball="Premier Ball")) as log:
            act = s.decide_turn(real_state())
        lines = wlines(log)
        memo = getattr(s, "_r25_wmemo", None)
        hist = None if memo is None else tuple(memo.history)
        return (act == PARENT and len(lines) == 1 and lines[0][0] == "WEAKEN" and lines[0][1].startswith("act=DEFER ")
                and hist == ((0, "DEFER", 22, 0),) and not log.gbs), f"{act} {[m[:40] for _c, m in lines]} hist {hist}"

    def wp_berry_a():
        """PD3 through the adapter: the target's held item's HOLD EFFECT is read (a Figy Berry, items.json 143)."""
        return throws(real_state(foe={"item": 143}), "confusion-berry")

    cases += [
        ("WPberryA [PD3] the adapter reads the target's hold effect: a Figy Berry -> act=THROW (confusion-berry)",
         wp_berry_a),
        ("WXAst3 [adv] the target's status3 read from ITS slot: Leech Seed -> THROW ticking", a_st3),
        ("WXAst3ours [adv] OUR status3 Leech Seed is no tick on the target -> DAMAGE", a_st3_ours),
        ("WXAside [adv] the target's side: our Future Sight pending -> THROW", a_side),
        ("WXAsideours [adv] OUR side's Future Sight (the target's) -> DAMAGE", a_side_ours),
        ("WXAweather [adv] gBattleWeather read: hail -> THROW", a_weather),
        ("WXAs1 [adv] the target's status1 at 0x4C: poisoned -> THROW ticking", a_s1),
        ("WXAliveab [adv] our lead's LIVE ability (Rough Skin; species Torrent) -> THROW retaliation", a_liveab),
        ("WXAtypes [adv] the target's LIVE types (Ghost) -> THROW immune", a_types),
        ("WXAflags [adv] the battle flags read: a trainer flag -> act=DEFER, the parent's action", a_flags),
        ("WXAchoice [adv] our hold effect read: a Choice Band -> act=DEFER", a_choice),
        ("WXAusable [adv] the usable balls read: total PP 60 <= H -> THROW struggle", a_usable),
        ("WXAkinds [adv] the mode's kinds (dex only) exclude team -> no read, no line", a_kinds),
        ("WXAobs2 [adv] observe stores the memo: turn 0 would=DAMAGE first=1; turn 1 would=THROW (the damage cap) "
         "first=0", a_obs2),
        ("WXActx2 [adv] a failed first-decision context DEFERs this turn AND the next", a_ctx2),
        ("WXAbanned [adv] banned_moves read: Sing banned -> THROW", a_banned),
        ("WXAbannedctl [adv] nothing banned -> STATUS(Sing), use_move(2)", a_banned_ctl),
        ("WXAsafeguard [adv] the OPPONENT side's Safeguard timer -> THROW", a_safeguard),
        ("WXAcharge [adv] CALC=1, the real calculator, our Charge (gStatuses3[0]) -> THROW divergence", a_charge),
        ("WXAmaster [adv] a Master Ball first in the pocket: THROW still uses the parent's Poké Ball", a_master),
        ("WXAb7 [adv] CALC=1, badge 7 read, a special move only -> THROW divergence", a_b7),
        ("WPnit [nit] a THROW whose ball the bag lacks: act=DEFER, and the memo records DEFER (what was done)", wp_nit),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


# ================================================================================================= W66 AST pins
ADAPTER_FUNCS = ("_r25_weaken_turn", "_r25_weaken_snapshot", "_r25_weaken_party", "_r25_weaken_ranges",
                 "_r25_weaken_bag_ball", "_r25_weaken_log")
#: The catch-strategy construction statements at cdb49f83 (`git show cdb49f83:…/story_mode.py`, read-only): each
#: (the `_r20_catch_start` statement, the return), in source order across on_battle_started + _dex_catch_commit.
BASE_CONSTRUCTION = [
    ("_r20_catch_start(self, 'dex' if _post_badge else 'team', encounter, dex=dex)",
     "return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()"),
    ("_r20_catch_start(self, 'shiny', encounter)", "return StoryShinyCatchStrategy()"),
    ("_r20_catch_start(self, 'hm', encounter)", "return StoryCatchStrategy()"),
    ("_r20_catch_start(self, 'counter', encounter)", "return StoryCatchStrategy()"),
]


def _cls(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == name)


def _method(cls, name):
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _func(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _body(f):
    body = list(f.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return body


def _names(node) -> set:
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.alias):
            out.add(n.name.split(".")[-1])
            if n.asname:
                out.add(n.asname)
    return out


def w66_rows(tag, srcs):
    reds: list = []
    sm_tree, wc_tree = ast.parse(srcs["sm"]), ast.parse(srcs["wc"])

    def adapter_nodes():
        cls = _cls(sm_tree, "StoryCatchStrategy")
        return [_method(cls, "decide_turn")] + [_func(sm_tree, n) for n in ADAPTER_FUNCS]

    def a():
        hits = [f.name for f in adapter_nodes() if "get_battle_state" in _names(f)]
        wc_hit = "get_battle_state" in _names(wc_tree)
        return not hits and not wc_hit, f"adapter hits {hits}; pure module hit {wc_hit}"

    def b():
        body = _body(_method(_cls(sm_tree, "StoryCatchStrategy"), "decide_turn"))
        got = [ast.unparse(s).split("\n")[0] for s in body]
        want = ["try:", "weaken = _r25_weaken_turn(self, battle_state)", "if weaken is not None:",
                "return super().decide_turn(battle_state)"]
        flee = len(body) == 4 and isinstance(body[0], ast.Try) and "_get_best_poke_ball" in _names(body[0]) \
            and "run_away" in _names(body[0])
        guard = len(body) == 4 and ast.unparse(body[2]) == "if weaken is not None:\n    return weaken"
        calls = sum(1 for n in ast.walk(sm_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "_r25_weaken_turn")
        return got == want and flee and guard and calls == 1, f"body {got}; flee {flee}; guard {guard}; call sites {calls}"

    def c():
        cls = _cls(sm_tree, "StoryMode")
        pairs = []
        for fname in ("_dex_catch_commit", "on_battle_started"):
            fn = _method(cls, fname)
            for node in ast.walk(fn):
                for fld in ("body", "orelse", "finalbody"):
                    blk = getattr(node, fld, None)
                    if not isinstance(blk, list):
                        continue
                    for i, st in enumerate(blk):
                        if isinstance(st, ast.Return) and st.value is not None and {
                                "StoryCatchStrategy", "StoryDexCatchStrategy", "StoryShinyCatchStrategy"} & _names(st):
                            pairs.append((ast.unparse(blk[i - 1]) if i else "", ast.unparse(st)))
        return sorted(pairs) == sorted(BASE_CONSTRUCTION), f"{pairs}"

    def d():
        cls = _cls(sm_tree, "StoryShinyCatchStrategy")
        fn = _method(cls, "decide_turn")
        last = ast.unparse(_body(fn)[-1])
        bases = [bb.id for bb in cls.bases if isinstance(bb, ast.Name)]
        bad = {"_r25_weaken_turn"} & _names(fn)
        supers = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "super"]
        return (last == "return CatchStrategy.decide_turn(self, battle_state)" and bases == ["StoryCatchStrategy"]
                and not bad and not supers), f"last {last!r}; bases {bases}; adapter refs {bad}; super() {len(supers)}"

    def e():
        mods = set()
        for n in ast.walk(wc_tree):
            if isinstance(n, ast.Import):
                mods |= {a_.name.split(".")[0] for a_ in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        allowed = {"__future__", "json", "os", "dataclasses", "math"}
        return mods <= allowed, f"imports {sorted(mods)} (allowed {sorted(allowed)})"

    def g():
        fn = _func(sm_tree, "_r25_weaken_log")
        calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "event"]
        cats = [ast.unparse(k.value) for c_ in calls for k in c_.keywords if k.arg == "category"]
        others = [n for f in adapter_nodes() if f.name != "_r25_weaken_log" for n in ast.walk(f)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "event"]
        return cats == ["'WEAKEN'"] and not others, f"categories {cats}; other logger calls {len(others)}"

    def h():
        hits = [f.name for f in adapter_nodes() if {"environ", "getenv"} & _names(f)]
        return not hits, f"environment reads in {hits}"

    cases = [
        ("W66a no get_battle_state in the adapter (StoryCatchStrategy.decide_turn + the _r25_weaken_* helpers) nor in "
         "the pure module (KI-108)", a),
        ("W66b the adapter sits after the out-of-balls flee and before super(), at ONE call site", b),
        ("W66c the catch-strategy construction lines are unchanged from cdb49f83", c),
        ("W66d the shiny strategy does not reach it (it returns CatchStrategy.decide_turn directly)", d),
        ("W66e the pure module imports only the standard library (no random, no emulator)", e),
        ("W66g the adapter logs in its OWN category WEAKEN, from one helper", g),
        ("W66h the adapter reads no environment variable (the flags come from the mode, per run)", h),
    ]
    for label, fn in cases:
        row(label, fn, tag, reds)
    return reds


def all_rows(tag, srcs):
    return set(pure_rows(tag) + wx_rows(tag) + w67_rows(tag) + w68_rows(tag) + adapter_rows(tag)
               + w66_rows(tag, srcs))


# ================================================================================================= FAULTS (exact sets)
#: Each fault's EXACT red set, derived row by row from the rows above and written BEFORE the gate's first run.
#: The PREDICTIONS filed the W-rows; the WB rows each fault also reddens are named (builder-added rows).
FAULT_SETS = {
    # skip hp - X >= 1: only Dragon Rage (40 >= 22) was stopped by the floor alone (W51: Wonder Guard first; W52: odds)
    F_NOFLOOR: {"W53"},
    F_NOENCORE: {"W39"},
    # stage 2 with CALC unset: only W63 carries calculator ranges with CALC off
    F_CALCLEAK: {"W63"},
    # the retaliation clause off the lead only: the three non-lead retaliators, and the adapter's party read (WBparty)
    F_ACTIVEONLY: {"W44", "W45", "W46", "WBparty"},
    # stage 1 ignores PP: every row built on "Seismic Toss at PP 0" whose target Seismic Toss can hit (W58c's Ghost
    # cannot); W63b turns into a stage-1 Seismic Toss (slot 1, not Tackle); W64 likewise
    F_NOPP: {"W47", "W57", "W57b", "W57c", "W57d", "W57e", "W57f", "W57g", "W57h", "W57i", "W57j", "W58", "W58b",
             "W58d", "W58e", "W58f", "W60", "W63", "W63b", "W64", "WBorder", "WBlimber"},
    F_MASTERBALL: {"W61"},
    F_SPECIESID: {"W05", "W06"},
    # the netted gain: every DAMAGE whose gross gain is in [1, 2): S0's 1.97 (W01 and its kin), Super Fang's 1.97,
    # stage 2's 1.13 (W63b); W59 falls to STATUS; the observe line (W62) and the acting adapter (WBact) turn to THROW
    F_NETGAIN: {"W01", "W33b", "W38b", "W41b", "W42b", "W43b", "W44b", "W49b", "W56", "W59", "W63b", "W62", "WB54s",
                "WBact"},
    # by NAME: "Sonicboom" (moves.json) is not "Sonic Boom" (the calculator): the Sonicboom rows lose their candidate
    F_NAMEDISPATCH: {"W54", "W55", "WB54s"},
}
#: THE FOLD (2026-09-30, the adversarial pass): what each fault ALSO reddens among the rows added by the fold, written
#: BEFORE the fold's first run. The WX/WXA additions are the pass's measured cross-run (`scratchpad/w12m/cross_out.txt`,
#: renamed); the WP additions are derived here by hand:
#:   ACTIVEONLY: the Trace member, our own non-lead Rough Skin and the Sand Stream member are non-lead subjects;
#:   NOPP: WPrecharge's lead carries Seismic Toss at PP 0 (stage 1 then acts before stage 2 is reached);
#:   NETGAIN: the three WP controls that expect DAMAGE on S0's numbers (gross 1.97).
FAULT_ADDITIONS = {
    F_NOFLOOR: {"WXfloor0"},
    F_NOENCORE: set(),
    F_CALCLEAK: {"WXAbanned", "WXAbannedctl", "WXAsafeguard"},
    F_ACTIVEONLY: {"WXppoint", "WXfbody", "WXespore", "WXoozeseed", "WPtrace", "WPtracectl", "WPsandstream"},
    F_NOPP: {"WNbanned2", "WXdivabil", "WXdivb7", "WXdivb7phys", "WXdivcharge", "WXdivff", "WXdivms", "WXfrozen", "WXhypnosp",
             "WXs2bound0", "WXs2bound1", "WXs2egain", "WXs2max", "WXs2prog", "WXs2tier", "WXuproarus", "WXvspirit",
             "WXAb7", "WXAbanned", "WXAbannedctl", "WXAcharge", "WXAsafeguard", "WPrecharge"},
    F_MASTERBALL: {"WXAmaster"},
    F_SPECIESID: set(),
    F_NETGAIN: {"WXbtsweep", "WXdivb7phys", "WXhailkice", "WXhailwice", "WXmax", "WXprog10", "WXs2bound1", "WXs2max",
                "WXsfodd", "WXtie", "WXwgnshade", "WXwgpass", "WXAobs2", "WXAsideours", "WXAst3ours", "WPtraceguts",
                "WPberryctl", "WPsandstreamctl"},
    F_NAMEDISPATCH: {"WXmax", "WXprog10", "WXprogmax"},
}

# ================================================================================================= MUTANTS (exact sets)
#: (label, target "wc" | "sm", [(old, new), ...] applied in order, the EXACT red set). Written BEFORE the first run.
MUTANTS: list = [
    # ---- DEFER
    ("M01 the flag check removed", "wc",
     [('    if env.flag not in ("observe", "1"):\n        return WDecision(DEFER, "off")',
       '    if False:\n        return WDecision(DEFER, "off")')], {"W02"}),
    ("M02 the kind check removed (the module's)", "wc",
     [('    if not in_scope(env.kind, env.kinds):\n        return WDecision(DEFER, "kind")',
       '    if False:\n        return WDecision(DEFER, "kind")')], {"W03"}),
    ("M02b in_scope always True (the module's and the adapter's)", "wc",
     [("    return kind is not None and kind in tuple(kinds)", "    return True")], {"W03", "WBkind"}),
    ("M03 the first decision's context check removed", "wc",
     [('        if not ctx_matches(env, target):\n            return WDecision(DEFER, "context")',
       '        if False:\n            return WDecision(DEFER, "context")')], {"W04"}),
    ("M03b a later decision ignores a failed context", "wc",
     [('        if not memo.ctx_ok:\n            return WDecision(DEFER, "context")',
       '        if False:\n            return WDecision(DEFER, "context")')], {"WBctx"}),
    ("M04 the PID check removed", "wc",
     [('        elif memo.pid != target.pid:\n            return WDecision(DEFER, "pid")',
       '        elif False:\n            return WDecision(DEFER, "pid")')], {"W05"}),
    ("M05 the battle-type check removed", "wc",
     [("    if env.battle_flags & NON_SINGLE_WILD:", "    if False:")], {"W07", "W08", "W09", "W10a", "W10b"}),
    ("M05b the battle-type mask = the trainer bit only", "wc",
     [("NON_SINGLE_WILD = 0xFFFFFFFF & ~((1 << 2) | (1 << 31))", "NON_SINGLE_WILD = 1 << 3")],
     {"W08", "W09", "W10a", "W10b"}),
    ("M06 the Choice item check removed", "wc", [('    if me.item_effect == "choice_band":', "    if False:")],
     {"W11"}),
    ("M07 the no-ball DEFER removed", "wc",
     [('    if env.ball is None:\n        return WDecision(DEFER, "no-ball")',
       '    if False:\n        return WDecision(DEFER, "no-ball")')], {"WBball"}),
    # ---- THROW-ONLY
    ("M08 the Transform (same PID, other species) check removed", "wc",
     [("    if memo is not None and memo.species_id != target.species_id:", "    if False:")], {"W06"}),
    ("M09 encoredMove read at 0x04 (the shared property's bug)", "wc",
     [("    return _u16(disable, 0x06)", "    return _u16(disable, 0x04)")], {"W12", "W12b", "WBencore"}),
    ("M10 the Encore-on-us check removed", "wc",
     [("    if encored_move(me.disable) or encore_timer(me.disable):", "    if False:")], {"W12", "WBencore"}),
    ("M11 the Torment check removed", "wc", [("    if me.status2 & S2_TORMENT:", "    if False:")], {"W14"}),
    ("M12 the Disable check removed (the slot filter still drops the disabled move: the reason changes)", "wc",
     [("    if disabled_move(me.disable) or disable_timer(me.disable):", "    if False:")], {"W12b"}),
    ("M13 the Imprison check removed", "wc", [("    if target.status3 & S3_IMPRISONED_OTHERS:", "    if False:")],
     {"W15"}),
    ("M14 the semi-invulnerable check removed", "wc",
     [("    if target.status3 & S3_SEMI_INVULNERABLE:", "    if False:")], {"W16"}),
    ("M15 the Substitute THROW-ONLY removed", "wc",
     [('    if target.status2 & S2_SUBSTITUTE:\n        return _throw(env, target, "substitute")',
       '    if False:\n        return _throw(env, target, "substitute")')], {"W17"}),
    ("M16 the confusion check removed", "wc", [("    if target.status2 & S2_CONFUSION:", "    if False:")], {"W18"}),
    ("M17 the status1 tick check removed", "wc",
     [("    if target.status1 & (S1_POISON | S1_BURN | S1_TOXIC):", "    if False:")], {"W19"}),
    ("M18 the Leech Seed tick check removed", "wc", [("    if target.status3 & S3_LEECHSEED:", "    if False:")],
     {"W20"}),
    ("M19 the Future Sight check removed", "wc", [("    if env.side_foe & SIDE_FUTUREATTACK:", "    if False:")],
     {"W21"}),
    ("M20 the Explosion THROW-ONLY removed (the self-harm rule still refuses damage: the reason changes)", "wc",
     [('    if _knows(target, {"EXPLOSION"}) and "Damp" not in (me.ability, target.ability):', "    if False:")],
     {"W22"}),
    ("M20b Damp ignored", "wc",
     [('    if _knows(target, {"EXPLOSION"}) and "Damp" not in (me.ability, target.ability):',
       '    if _knows(target, {"EXPLOSION"}):')], {"W23"}),
    ("M21 the enders removed", "wc",
     [("    for m in _knows(target, ENDER_EFFECTS):\n        return _throw(",
       "    for m in ():\n        return _throw(")], {"W24", "W25", "W26", "W27"}),
    ("M22 the calling THROW-ONLY removed (the self-harm rule still refuses damage: the reason changes)", "wc",
     [("    for m in _knows(target, CALLING_EFFECTS):\n        return _throw(",
       "    for m in ():\n        return _throw(")], {"W28", "W29", "W30", "W31"}),
    ("M23 the one-throw odds check removed", "wc",
     [("    if catch_p_ball(env.ball, target, env, target.hp, target.status1) >= ODDS_THROW_ONLY:", "    if False:")],
     {"W32", "W52"}),
    ("M24 the no-progress cap removed", "wc", [("    if no_progress >= CAP_NO_PROGRESS:", "    if False:")], {"WBnp"}),
    ("M25 the damage cap never spent", "wc",
     [("    damage_spent = sum(1 for h in past if h[1] == DAMAGE) >= CAP_DAMAGE_TURNS", "    damage_spent = False")],
     {"W33", "WBact"}),
    ("M25b this turn's own decision spends the cap (a re-entry would flip DAMAGE to THROW)", "wc",
     [("    past = sorted(h for h in memo.history if h[0] < env.turn)",
       "    past = sorted(h for h in memo.history if h[0] <= env.turn)")], {"W33b"}),
    # ---- DAMAGE: no self-harm
    # (re-anchored at the fold: PD2 put "PAIN_SPLIT" on a continuation line; both mutants leave it in place)
    ("M26 recoil / crash / rampage / Belly Drum dropped from the self-harm moves", "wc",
     [('SELF_HARM_EFFECTS = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "RAMPAGE", "BELLY_DRUM", '
       '"EXPLOSION",', 'SELF_HARM_EFFECTS = frozenset({"EXPLOSION",')], {"W34", "W35", "W36", "W37"}),
    ("M26b Explosion dropped from the self-harm moves", "wc",
     [('SELF_HARM_EFFECTS = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "RAMPAGE", "BELLY_DRUM", '
       '"EXPLOSION",',
       'SELF_HARM_EFFECTS = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "RAMPAGE", "BELLY_DRUM",')],
     {"W23"}),
    ("M27 the Ghost-Curse rule removed", "wc",
     [('    if "Ghost" in target.types:\n        for m in _knows(target, {"CURSE"}):',
       '    if False:\n        for m in _knows(target, {"CURSE"}):')], {"WB38"}),
    ("M27b every Curse-knower refused (not only a Ghost)", "wc",
     [('    if "Ghost" in target.types:\n        for m in _knows(target, {"CURSE"}):',
       '    if True:\n        for m in _knows(target, {"CURSE"}):')], {"W38b"}),
    ("M28 the acquired-move rule removed", "wc",
     [('    for m in _knows(target, ACQUIRE_EFFECTS):\n        return f"acquires:',
       '    for m in ():\n        return f"acquires:')], {"W40", "W40b", "W40c"}),
    ("M30 the Sandstorm-knower rule removed", "wc",
     [('    if _knows(target, {"SANDSTORM"}) and not sand_immune:', "    if False:")], {"W41"}),
    ("M30b sand immunity by Sand Veil only (types ignored)", "wc",
     [('    sand_immune = bool({"Rock", "Ground", "Steel"} & set(target.types)) or target.ability == "Sand Veil"',
       '    sand_immune = target.ability == "Sand Veil"')], {"W41b", "W43b"}),
    ("M31 the Struggle horizon removed", "wc", [("    if total_pp <= horizon:", "    if False:")], {"W42"}),
    ("M31d the horizon 2 larger (78 since PD5): W42b's 78 no longer exceeds it", "wc",
     [("    horizon = PRESSURE_FACTOR * (env.usable_balls + HORIZON_SLACK)",
       "    horizon = PRESSURE_FACTOR * (env.usable_balls + HORIZON_SLACK) + 2")], {"W42b"}),
    ("M32 the weather-in-effect rule removed", "wc",
     [("    if env.weather & WEATHER_SAND and not sand_immune:", "    if False:")], {"W43", "W43c"}),
    ("M32b Cloud Nine trusted to suppress the sand", "wc",
     [("    if env.weather & WEATHER_SAND and not sand_immune:",
       '    if env.weather & WEATHER_SAND and not sand_immune and "Cloud Nine" not in (me.ability, target.ability):')],
     {"W43c"}),
    ("M33 a contact retaliator refuses even with no contact move", "wc",
     [("        if ab in CONTACT_RETALIATORS and contact:", "        if ab in CONTACT_RETALIATORS:")], {"W44b"}),
    # ---- DAMAGE: stage 1
    ("M34 the stage-1 type immunity ignored", "wc",
     [('        if immune:\n            rejected.append(f"immune@{slot}")',
       '        if False:\n            rejected.append(f"immune@{slot}")')], {"W49", "W50"}),
    ("M34b the immunity AND the Ghost-Curse rule removed (W38's two independent blockers)", "wc",
     [('        if immune:\n            rejected.append(f"immune@{slot}")',
       '        if False:\n            rejected.append(f"immune@{slot}")'),
      ('    if "Ghost" in target.types:\n        for m in _knows(target, {"CURSE"}):',
       '    if False:\n        for m in _knows(target, {"CURSE"}):')], {"W38", "W49", "W50", "WB38"}),
    ("M35 every exact candidate admitted unchecked", "wc",
     [("        if x is None:\n            continue\n        immune, se, nve = type_effect(",
       "        if x is None:\n            continue\n        admissible.append((x, -slot, slot, m))\n        continue\n"
       "        immune, se, nve = type_effect(")], {"W49", "W50", "W51", "W53", "W54", "W55", "WB52"}),
    ("M36 the stage-1 50% rule removed", "wc",
     [('        if not target.hp * 2 > target.max_hp:\n            rejected.append(f"half@{slot}")\n            continue\n'
       "        if not _fault(FAULT_NOFLOOR)",
       '        if False:\n            rejected.append(f"half@{slot}")\n            continue\n'
       "        if not _fault(FAULT_NOFLOOR)")], {"WB52"}),
    ("M37 the stage-1 progress rule removed", "wc",
     [("        if not x * 100 >= PROGRESS_PCT * target.max_hp:", "        if False:")], {"W54"}),
    ("M38 the stage-1 E_gain rule removed", "wc",
     [("        gain = e_gain(env.ball, target, env, x)\n        if not gain >= EGAIN_MIN:",
       "        gain = e_gain(env.ball, target, env, x)\n        if False:")], {"W55"}),
    ("M39a Super Fang deals the whole HP", "wc",
     [("        return target.hp // 2 if target.hp >= 2 else 1", "        return target.hp if target.hp >= 2 else 1")],
     {"W56"}),
    ("M39b Dragon Rage deals 20", "wc",
     [('    if effect == "DRAGON_RAGE":\n        return 40', '    if effect == "DRAGON_RAGE":\n        return 20')],
     {"W53"}),
    ("M39c Sonicboom deals 25", "wc",
     [('    if effect == "SONICBOOM":\n        return 20', '    if effect == "SONICBOOM":\n        return 25')],
     {"W54", "WB54s"}),
    ("M39d LEVEL_DAMAGE uses the TARGET's level", "wc",
     [('    if effect == "LEVEL_DAMAGE":\n        return me.level', '    if effect == "LEVEL_DAMAGE":\n        return target.level')],
     {"W01"}),
    # ---- DAMAGE: stage 2
    ("M40 stage 2's bound without the 10% and the margin (ub = crit_max)", "wc",
     [("            ub = (crit_max * 11 + 9) // 10 + WEAKEN_MARGIN", "            ub = crit_max")], {"W63b"}),
    ("M41 the Guts-with-a-burn divergence removed", "wc",
     [('    if me.ability == "Guts" and me.status1 & S1_BURN:', "    if False:")], {"W64"}),
    # ⚠ CORRECTED AFTER THE FIRST RUN (2026-09-30), openly: the set was written {W63b}. The first run reddened W64 as
    # well, and that is right — W64 asserts the reason "divergence", which only stage 2 produces; with stage 2 never
    # running W64 still THROWs, but for "no-damage-move". The derivation missed that W64's REASON depends on stage 2.
    ("M42 stage 2 never runs", "wc", [("    if stage2_wanted(env.calc):", "    if False:")], {"W63b", "W64"}),
    # ---- STATUS
    ("M43 the status cap removed", "wc", [("    if tries >= CAP_STATUS_TRIES:", "    if False:")], {"W57h"}),
    ("M44 Taunt on us ignored", "wc", [("    if taunt_timer(me.disable) > 0:", "    if False:")], {"W57g"}),
    ("M45 an existing status ignored", "wc",
     [('    if target.status1 & S1_ANY:\n        return None, "has-status"',
       '    if False:\n        return None, "has-status"')], {"W57e"}),
    ("M46 Safeguard ignored", "wc",
     [("    if env.side_foe & SIDE_SAFEGUARD or env.safeguard_timer > 0:", "    if False:")], {"W57f"}),
    ("M47 Magic Coat ignored", "wc", [('    if _knows(target, {"MAGIC_COAT"}):', "    if False:")], {"W57j"}),
    ("M48 banned_moves ignored (re-anchored on the _status context at W12-N1)", "wc",
     [('        if m.name in env.banned:\n            rejected.append(f"banned@{slot}")\n            continue\n        if m.sound',
       '        if False:\n            rejected.append(f"banned@{slot}")\n            continue\n        if m.sound')], {"W60"}),
    ("M49 Soundproof ignored", "wc", [('        if m.sound and target.ability == "Soundproof":', "        if False:")],
     {"W57b"}),
    ("M50 Uproar ignored", "wc", [("            if _uproar_any(target, me):", "            if False:")], {"W57c"}),
    ("M51 Insomnia / Vital Spirit ignored", "wc",
     [('            if target.ability in ("Insomnia", "Vital Spirit"):', "            if False:")], {"W57d"}),
    ("M52 the paralysis type immunity ignored", "wc",
     [("            if type_effect(m.type, target.types, foresight)[0]:", "            if False:")], {"W58", "W58c"}),
    ("M52b the status check ignores Foresight", "wc",
     [("            if type_effect(m.type, target.types, foresight)[0]:",
       "            if type_effect(m.type, target.types, False)[0]:")], {"W58d"}),
    ("M53 Synchronize ignored", "wc", [('            if target.ability == "Synchronize":', "            if False:")],
     {"W58e"}),
    ("M54 paralysis over sleep", "wc", [("    for group in (sleep, para):", "    for group in (para, sleep):")],
     {"WBorder"}),
    ("M55 Limber ignored", "wc", [('            if target.ability == "Limber":', "            if False:")],
     {"WBlimber"}),
    ("M56 a held berry made a skip (it is a try, not a skip)", "wc",
     [('    if _knows(target, {"MAGIC_COAT"}):', '    if _knows(target, {"MAGIC_COAT"}) or target.item:')], {"W57i"}),
    # ---- THROW's ball, RULING 27
    ("M58 THROW names a ball the parent did not choose", "wc",
     [("    ball = env.ball\n    if _fault(FAULT_MASTERBALL):", '    ball = "Premier Ball"\n    if _fault(FAULT_MASTERBALL):')],
     {"W61", "WBthrow", "WBencore", "WBparty", "WBact"}),
    ("M58b THROW names an item that is not a ball", "wc",
     [("    ball = env.ball\n    if _fault(FAULT_MASTERBALL):", '    ball = "Potion"\n    if _fault(FAULT_MASTERBALL):')],
     {"W61", "W68", "WBthrow", "WBencore", "WBparty", "WBact"}),
    # ---- catch_p (W67)
    ("Mcp1 the constant 1048576 for 1048560 (b rounds up where Sqrt^2 = 16/18/22)", "wc",
     [("    b = 1048560 // isqrt(isqrt(16711680 // odds))", "    b = 1048576 // isqrt(isqrt(16711680 // odds))")],
     {"W67a", "W67b", "W67c", "W67e", "W67f", "W67k"}),
    ("Mcp2 the float order (rate * bonus / 10 not floored first)", "wc",
     [("    odds = (rate * bonus_x10 // 10) * (3 * max_hp - 2 * hp) // (3 * max_hp)",
       "    odds = rate * bonus_x10 * (3 * max_hp - 2 * hp) // (30 * max_hp)")], {"W67l"}),
    ("Mcp3 sleep x1", "wc", [("        odds *= 2", "        odds *= 1")], {"W67c"}),
    ("Mcp4 paralysis x2", "wc", [("        odds = odds * 15 // 10", "        odds = odds * 2")], {"W67d"}),
    ("Mcp5 odds 254 counted as certain", "wc", [("    if odds > 254:", "    if odds >= 254:")], {"W67e"}),
    ("Mcp6 the Nest Ball one point high", "wc", [("            m = (40 - level) & 0xFF", "            m = (41 - level) & 0xFF")],
     {"W67f"}),
    ("Mcp7 the Net Ball ignores Bug", "wc",
     [('        return 30 if ("Water" in types or "Bug" in types) else 10', '        return 30 if ("Water" in types) else 10')],
     {"W67g"}),
    ("Mcp8 the Timer Ball one point high", "wc",
     [("        m = (turn + 10) & 0xFF", "        m = (turn + 11) & 0xFF")], {"W67h"}),
    ("Mcp9 the Master Ball not forced", "wc",
     [("    if bonus is None:\n        return 1.0", "    if bonus is None:\n        return 0.5")], {"W67i"}),
    # ---- the pure module's purity
    ("M66e the pure module imports random", "wc", [("import json\nimport os\n", "import json\nimport os\nimport random  # noqa: F401\n")],
     {"W66e"}),
    ("M66a the pure module imports get_battle_state", "wc",
     [("import json\nimport os\n", "import json\nimport os\nfrom modules.battle_state import get_battle_state  # noqa: F401\n")],
     {"W66a", "W66e"}),
    ("MN2 a comment-only edit in the pure module naming random / get_battle_state turns NOTHING red", "wc",
     [("def _fault(name: str) -> bool:",
       "# (a mention only: import random; get_battle_state(); read_symbol())\ndef _fault(name: str) -> bool:")], set()),
    # ---- the ADAPTER (story_mode.py)
    ("MA1 the adapter BEFORE the out-of-balls flee", "sm",
     [("        weaken = _r25_weaken_turn(self, battle_state)\n        if weaken is not None:\n            return weaken\n"
       "        return super().decide_turn(battle_state)\n\n\ndef dex_catch_bail_reason(",
       "        return super().decide_turn(battle_state)\n\n\ndef dex_catch_bail_reason("),
      ('    def decide_turn(self, battle_state):\n        try:\n            if self._get_best_poke_ball(battle_state) is None:\n'
       '                context.message = "Story: out of Poké Balls — fleeing',
       '    def decide_turn(self, battle_state):\n        weaken = _r25_weaken_turn(self, battle_state)\n'
       '        if weaken is not None:\n            return weaken\n        try:\n'
       '            if self._get_best_poke_ball(battle_state) is None:\n'
       '                context.message = "Story: out of Poké Balls — fleeing')], {"W65b", "W66b"}),
    ("MA2 the adapter call removed", "sm",
     [("        weaken = _r25_weaken_turn(self, battle_state)\n        if weaken is not None:",
       "        weaken = None\n        if weaken is not None:")],
     {"W62", "W65c", "W66b", "WBact", "WBthrow", "WBencore", "WBparty"}),
    ("MA3 the adapter's flag gate removed (flag unset reaches the reads)", "sm",
     [('    if flag not in ("observe", "1"):\n        return None\n    try:\n        from modules.story import weaken_catch as _wc',
       "    try:\n        from modules.story import weaken_catch as _wc")], {"W65d"}),
    ("MA4 observe returns the verdict's action", "sm",
     [('            _r25_weaken_log(f"[WEAKEN-OBS] would={d.verdict} {head} first={first} snap={snap}")\n'
       "            return None",
       '            _r25_weaken_log(f"[WEAKEN-OBS] would={d.verdict} {head} first={first} snap={snap}")\n'
       "            return TurnAction.use_move(d.slot) if d.slot is not None else None")], {"W62"}),
    ("MA5 the category BATTLE", "sm",
     [('        _w_dl.event(message, category="WEAKEN")', '        _w_dl.event(message, category="BATTLE")')],
     {"W62", "W65c", "W66g", "WBact", "WBthrow", "WBencore", "WBparty"}),
    ("MA6 a get_battle_state() call in the snapshot", "sm",
     [("    ours = battle_state.own_side.active_battler\n    foe = battle_state.opponent.active_battler\n"
       "    if ours is None or foe is None:",
       "    from modules.battle_state import get_battle_state as _w_gbs\n\n    _w_gbs()\n"
       "    ours = battle_state.own_side.active_battler\n    foe = battle_state.opponent.active_battler\n"
       "    if ours is None or foe is None:")], {"W66a", "W62", "W65c", "WBact", "WBthrow", "WBencore", "WBparty"}),
    ("MA7 first=1 never set", "sm", [("                first = 1", "                first = 0")], {"W62"}),
    ("MA8 the ERR line dropped", "sm",
     [('        _r25_weaken_log(f"ERR v=1 err={type(error).__name__}: {error}")\n        return None',
       "        return None")], {"W65c"}),
    ("MA9 the adapter's own scope check removed (hm reaches the reads and logs)", "sm",
     [("        if not _wc.in_scope(kind, kinds):\n            return None", "        if False:\n            return None")],
     {"WBkind"}),
    ("MA10 the shiny strategy calls StoryCatchStrategy.decide_turn (reaching the adapter)", "sm",
     [("        return CatchStrategy.decide_turn(self, battle_state)",
       "        return StoryCatchStrategy.decide_turn(self, battle_state)")], {"W65e", "W66d"}),
    ("MA11 the dex strategy runs the adapter BEFORE its bails", "sm",
     [('    def decide_turn(self, battle_state):\n        import os as _os_bail\n\n',
       "    def decide_turn(self, battle_state):\n        import os as _os_bail\n\n"
       "        _w = _r25_weaken_turn(self, battle_state)\n        if _w is not None:\n            return _w\n")],
     {"W65a", "W66b"}),
    ("MA12 a construction line edited (hm)", "sm",
     [('                    _r20_catch_start(self, "hm", encounter)\n                    return StoryCatchStrategy()',
       '                    _r20_catch_start(self, "hm", encounter)\n                    return StoryCatchStrategy() if True else None')],
     {"W66c"}),
    ("MA13 reset_per_run_state keeps any flag value", "sm",
     [('        self._r25_weaken = _r25_w if _r25_w in ("observe", "1") else ""', "        self._r25_weaken = _r25_w")],
     {"WBflags"}),
    ("MA14 the adapter reads the flag from the environment, not the mode", "sm",
     [('        flag = getattr(mode, "_r25_weaken", "") if mode is not None else ""',
       '        flag = __import__("os").environ.get("POKEBOT_R25_WEAKEN", "")')],
     {"W62", "W65c", "W66h", "WBact", "WBthrow", "WBencore", "WBparty"}),
    # (re-anchored at the fold: the memo nit's fix remembers `done`, what was actually done, not `d`)
    ("MA15 the acting memo never stored (no per-battle cap)", "sm",
     [("        strategy._r25_wmemo = _wc.remember(memo, target, env, done)\n        _r25_weaken_log(f\"act=",
       "        _r25_weaken_log(f\"act=")], {"WBact"}),
    ("MA16 the turn from the cached BattleState, not the pure read (KI-108)", "sm",
     [('turn=read_symbol("gBattleResults", offset=0x13, size=1)[0]', "turn=battle_state.current_turn")], {"WBact"}),
    ("MA17 the raw disable struct not read (zeros)", "sm",
     [('        disable=bytes(read_symbol("gDisableStructs", size=0x1C)),', "        disable=bytes(0x1C),")],
     {"WBencore"}),
    ("MA18 the party read replaced by the lead alone", "sm",
     [("    party = _wc.WParty(abilities=_r25_weaken_party(me.pid, our_live))",
       "    party = _wc.WParty(abilities=(our_live,))")], {"W62", "WBparty"}),
    ("MN1 a comment-only edit in the adapter naming get_battle_state / environ / category='BATTLE' turns NOTHING red",
     "sm", [("def _r25_weaken_turn(strategy, battle_state):",
             "# (a mention only: get_battle_state(); os.environ; category=\"BATTLE\")\n"
             "def _r25_weaken_turn(strategy, battle_state):")], set()),
]

#: THE FOLD (2026-09-30, the adversarial pass): what each EXISTING mutant ALSO reddens among the rows the fold added,
#: written BEFORE the fold's first run. The WX/WXA additions are the pass's measured cross-run
#: (`scratchpad/w12m/cross_out.txt`, renamed), plus, for MA6, every WXA row that reaches the snapshot: the folded
#: adapter rows assert 0 get_battle_state() calls, which the pass's own versions did not (WXAkinds never reaches it).
#: The WP additions are derived here by hand:
#:   M30b: WPsandstreamctl's Ground target stops being sand-immune, so its Sand Stream member refuses the hit;
#:   M31: WPh76 (76) is no longer refused without the horizon; M42: WPrecharge's reason "recharge" is stage 2's;
#:   M58/M58b: WPberryA THROWs (its ball); MA2/MA5/MA6/MA14: WPnit and WPberryA run the adapter like WBparty;
#:   MA15: WPnit's memo is never stored.
_WXA_SNAPSHOT = {"WXAst3", "WXAst3ours", "WXAside", "WXAsideours", "WXAweather", "WXAs1", "WXAliveab", "WXAtypes",
                 "WXAflags", "WXAchoice", "WXAusable", "WXAobs2", "WXActx2", "WXAbanned", "WXAbannedctl",
                 "WXAsafeguard", "WXAcharge", "WXAmaster", "WXAb7"}
_WXA_THROWS = {"WXAb7", "WXAbanned", "WXAcharge", "WXAliveab", "WXAmaster", "WXAs1", "WXAsafeguard", "WXAside",
               "WXAst3", "WXAtypes", "WXAusable", "WXAweather"}
MUTANT_ADDITIONS = {
    "M02b": {"WXAkinds"},
    "M03": {"WXActx2"},
    "M03b": {"WXActx2"},
    "M05": {"WXbtsweep", "WXAflags"},
    "M05b": {"WXbtsweep"},
    "M06": {"WXAchoice"},
    "M14": {"WXdig", "WXdive"},
    "M16": {"WXconf4"},
    "M17": {"WXburn", "WXtoxic", "WXAs1"},
    "M18": {"WXAst3"},
    "M19": {"WXAside"},
    "M23": {"WXodds15"},
    "M25": {"WXcapseq", "WXAobs2"},
    "M25b": {"WXcapseq"},
    "M26": {"WXdedge"},
    "M30b": {"WPsandstreamctl"},
    "M31": {"WXh68", "WXAusable", "WPh76"},
    "M32": {"WXsandtemp"},
    "M34": {"WXAtypes"},
    "M34b": {"WXAtypes"},
    "M35": {"WNbanned1", "WXegst", "WXfloor0", "WXprogmax", "WXwgblock", "WXAtypes"},
    "M37": {"WXprogmax"},
    "M38": {"WXegst"},
    "M39a": {"WXsfodd"},
    "M39c": {"WXmax", "WXprog10", "WXprogmax"},
    "M39d": {"WXegst", "WXfloor0", "WXfloor1", "WXtie", "WXwgnshade"},
    "M40": {"WXs2bound0", "WNbanned2"},
    "M42": {"WNbanned2", "WXdivabil", "WXdivb7", "WXdivb7phys", "WXdivcharge", "WXdivff", "WXdivms", "WXs2bound0", "WXs2bound1",
            "WXs2egain", "WXs2half", "WXs2max", "WXs2prog", "WXAb7", "WXAcharge", "WPrecharge"},
    "M45": {"WXfrozen"},
    "M46": {"WXAsafeguard"},
    "M48": {"WXAbanned"},
    "M50": {"WXuproarus"},
    "M51": {"WXvspirit"},
    "M58": _WXA_THROWS | {"WPberryA"},
    "M58b": _WXA_THROWS | {"WPberryA"},
    "Mcp1": {"WXcpstatus"},
    "Mcp3": {"WXcpstatus"},
    "Mcp4": {"WXcpstatus", "WXegst"},
    "MA2": _WXA_SNAPSHOT | {"WPnit", "WPberryA"},
    "MA4": {"WXAobs2"},
    "MA5": {"WXAb7", "WXAbanned", "WXAcharge", "WXAchoice", "WXActx2", "WXAflags", "WXAliveab", "WXAs1",
            "WXAsafeguard", "WXAside", "WXAst3", "WXAst3ours", "WXAtypes", "WXAusable", "WXAweather", "WPnit",
            "WPberryA"},
    "MA6": _WXA_SNAPSHOT | {"WPnit", "WPberryA"},
    "MA7": {"WXAobs2"},
    "MA9": {"WXAkinds"},
    "MA14": _WXA_SNAPSHOT | {"WPnit", "WPberryA"},
    "MA15": {"WPnit"},
    "MA16": {"WXAobs2"},
}

#: THE PRODUCTION FIXES' REVERTS (the adversarial pass's fold): each reverts ONE fix and must redden exactly its rows.
#: Written BEFORE the fold's first run.
REVERT_MUTANTS: list = [
    ("MR1 PD1 reverted: a Trace member no longer adds the target's live ability", "wc",
     [('    if "Trace" in subjects:', "    if False:")], {"WPtrace"}),
    ("MR2 PD2 reverted: Pain Split dropped from the self-harm moves", "wc",
     [('"PAIN_SPLIT"})', "})")], {"WPpainsplit"}),
    ("MR3 PD3 reverted in the module: a confusion berry no longer refuses damage", "wc",
     [('    if target.item_effect.startswith("confuse_"):', "    if False:")], {"WPberry", "WPberryA"}),
    ("MR3b PD3 reverted in the adapter: the target's hold effect not read", "sm",
     [('        item_effect="no_effect" if foe.held_item is None else str(foe.held_item.hold_effect.value))',
       '        item_effect="no_effect")')], {"WPberryA"}),
    ("MR4 PD4 reverted: a Sand Stream member no longer refuses damage", "wc",
     [('        if ab == "Sand Stream" and not sand_immune:', "        if False:")], {"WPsandstream"}),
    ("MR5a PD5 reverted: stage 2 admits a RECHARGE move again", "wc",
     [("            if m.effect in STAGE2_EXCLUDED:", "            if False:")], {"WPrecharge"}),
    ("MR5b PD5 reverted: the horizon slack back to 4 (H = 68)", "wc",
     [("HORIZON_SLACK = 8", "HORIZON_SLACK = 4")], {"WPh76"}),
    ("MNb1 W12-N1 reverted in stage 1: a banned exact-damage move is a candidate again", "wc",
     [('        immune, se, nve = type_effect(m.type, target.types, foresight)\n        if m.name in env.banned:',
       '        immune, se, nve = type_effect(m.type, target.types, foresight)\n        if False:')],
     {"WNbanned1"}),
    ("MNb2 W12-N1 reverted in stage 2: a banned Tier A move is a candidate again", "wc",
     [('            if m.name in env.banned:\n                rejected.append(f"banned@{slot}")\n                continue\n            div =',
       '            if False:\n                rejected.append(f"banned@{slot}")\n                continue\n            div =')],
     {"WNbanned2"}),
    ("MR6 the memo nit reverted: the memo records the verdict, not what was done", "sm",
     [("        done = d if action is not None or d.verdict == _wc.DEFER else _wc.WDecision(_wc.DEFER, d.reason)",
       "        done = d")], {"WPnit"}),
]

#: The adversarial pass's formerly-MISSED mutants (`scratchpad/w12m/mutants.py`, folded 2026-09-30): anchors copied
#: verbatim (V50 and V63 re-anchored for PD2/PD5), each with the EXACT red set written by hand before the run.
PASS_MUTANTS: list = [
    ('V02 [adv] floor >=1 -> >=0 (admits a KO)', 'wc',
     [('        if not _fault(FAULT_NOFLOOR) and not target.hp - x >= 1:', '        if not _fault(FAULT_NOFLOOR) and not target.hp - x >= 0:')],
     {'WXfloor0'}),
    ('V03 [adv] floor >=1 -> >=2', 'wc',
     [('        if not _fault(FAULT_NOFLOOR) and not target.hp - x >= 1:', '        if not _fault(FAULT_NOFLOOR) and not target.hp - x >= 2:')],
     {'WXfloor1'}),
    ('V05 [adv] stage-2 50% rule removed', 'wc',
     [('            if not target.hp * 2 > target.max_hp:\n                rejected.append(f"half@{slot}")', '            if False:\n                rejected.append(f"half@{slot}")')],
     {'WXs2half'}),
    ('V06 [adv] stage-2 50% rule > -> >=', 'wc',
     [('            if not target.hp * 2 > target.max_hp:\n                rejected.append(f"half@{slot}")', '            if not target.hp * 2 >= target.max_hp:\n                rejected.append(f"half@{slot}")')],
     {'WXs2half'}),
    ('V07 [adv] stage-1 progress >= -> >', 'wc',
     [('        if not x * 100 >= PROGRESS_PCT * target.max_hp:', '        if not x * 100 > PROGRESS_PCT * target.max_hp:')],
     {'WXprog10'}),
    ('V08 [adv] stage-1 progress vs CURRENT hp, not max', 'wc',
     [('        if not x * 100 >= PROGRESS_PCT * target.max_hp:', '        if not x * 100 >= PROGRESS_PCT * target.hp:')],
     {'WXprogmax'}),
    ("V13 [adv] E_gain ignores the target's status", 'wc',
     [('    gain = expected_balls(ball, target, env, target.hp, target.status1) - \\\n        expected_balls(ball, target, env, after, target.status1)', '    gain = expected_balls(ball, target, env, target.hp, 0) - \\\n        expected_balls(ball, target, env, after, 0)')],
     {'WXegst'}),
    ('V14 [adv] one-throw threshold 0.5 -> 0.6', 'wc',
     [('ODDS_THROW_ONLY = 0.5 ', 'ODDS_THROW_ONLY = 0.6 ')],
     {'WXodds15'}),
    ('V24 [adv] semi-invulnerable = Fly only (Dig, Dive dropped)', 'wc',
     [('S3_SEMI_INVULNERABLE = S3_ON_AIR | S3_UNDERGROUND | S3_UNDERWATER', 'S3_SEMI_INVULNERABLE = S3_ON_AIR')],
     {'WXdig', 'WXdive'}),
    ('V25 [adv] confusion mask 0x7 -> 0x3', 'wc',
     [('S2_CONFUSION, S2_UPROAR, S2_WRAPPED = 0x7, 0x70, 0xE000', 'S2_CONFUSION, S2_UPROAR, S2_WRAPPED = 0x3, 0x70, 0xE000')],
     {'WXconf4'}),
    ('V26 [adv] ticking: burn dropped', 'wc',
     [('    if target.status1 & (S1_POISON | S1_BURN | S1_TOXIC):', '    if target.status1 & (S1_POISON | S1_TOXIC):')],
     {'WXburn'}),
    ('V27 [adv] ticking: toxic dropped', 'wc',
     [('    if target.status1 & (S1_POISON | S1_BURN | S1_TOXIC):', '    if target.status1 & (S1_POISON | S1_BURN):')],
     {'WXtoxic'}),
    ('V28 [adv] ticking: the whole status2 clause dropped', 'wc',
     [('    if target.status2 & (S2_WRAPPED | S2_CURSED | S2_NIGHTMARE):', '    if False:')],
     {'WXcursed', 'WXnightmare', 'WXwrap'}),
    ('V29 [adv] ticking: wrap dropped', 'wc',
     [('    if target.status2 & (S2_WRAPPED | S2_CURSED | S2_NIGHTMARE):', '    if target.status2 & (S2_CURSED | S2_NIGHTMARE):')],
     {'WXwrap'}),
    ('V30 [adv] ticking: curse dropped', 'wc',
     [('    if target.status2 & (S2_WRAPPED | S2_CURSED | S2_NIGHTMARE):', '    if target.status2 & (S2_WRAPPED | S2_NIGHTMARE):')],
     {'WXcursed'}),
    ('V31 [adv] ticking: nightmare dropped', 'wc',
     [('    if target.status2 & (S2_WRAPPED | S2_CURSED | S2_NIGHTMARE):', '    if target.status2 & (S2_WRAPPED | S2_CURSED):')],
     {'WXnightmare'}),
    ('V37 [adv] battle-type mask loses Kyogre/Groudon, Regi, Pike, Pyramid, Groudon/Kyogre/Rayquaza', 'wc',
     [('NON_SINGLE_WILD = 0xFFFFFFFF & ~((1 << 2) | (1 << 31))', 'NON_SINGLE_WILD = 0xFFFFFFFF & ~((1 << 2) | (1 << 31) | (1 << 12) | (1 << 14) | (1 << 20) | (1 << 21) | (7 << 28))')],
     {'WXbtsweep'}),
    ('V38 [adv] battle-type mask loses FIRST_BATTLE', 'wc',
     [('NON_SINGLE_WILD = 0xFFFFFFFF & ~((1 << 2) | (1 << 31))', 'NON_SINGLE_WILD = 0xFFFFFFFF & ~((1 << 2) | (1 << 31) | (1 << 4))')],
     {'WXbtsweep'}),
    ('V45 [adv] remember() records every call, not the first per turn (cons)', 'wc',
     [('    if any(h[0] == env.turn for h in memo.history):\n        return memo\n', '')],
     {'WXcapseq'}),
    ('V46 [adv] remember(): a failed first-decision context is forgotten (later turns act)', 'wc',
     [('        memo = WMemo(pid=target.pid, species_id=target.species_id, ctx_ok=ctx_matches(env, target))', '        memo = WMemo(pid=target.pid, species_id=target.species_id, ctx_ok=True)')],
     {'WXActx2'}),
    ('V50 [adv] self-harm: DOUBLE_EDGE dropped (Double-Edge, Volt Tackle)', 'wc',
     [('SELF_HARM_EFFECTS = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "RAMPAGE", "BELLY_DRUM", "EXPLOSION",', 'SELF_HARM_EFFECTS = frozenset({"RECOIL", "RECOIL_IF_MISS", "RAMPAGE", "BELLY_DRUM", "EXPLOSION",')],
     {'WXdedge'}),
    ('V51 [adv] Hail-knower rule dropped', 'wc',
     [('    if _knows(target, {"HAIL"}) and not hail_immune:', '    if False:')],
     {'WXhailk'}),
    ('V52 [adv] every target hail-immune', 'wc',
     [('    hail_immune = "Ice" in target.types', '    hail_immune = True')],
     {'WXAweather', 'WXhailk', 'WXhailw'}),
    ('V53 [adv] hail-in-effect rule dropped', 'wc',
     [('    if env.weather & WEATHER_HAIL and not hail_immune:', '    if False:')],
     {'WXAweather', 'WXhailw'}),
    ('V54 [adv] sand mask loses the TEMPORARY bit', 'wc',
     [('WEATHER_SAND, WEATHER_HAIL = 0x18, 0x80', 'WEATHER_SAND, WEATHER_HAIL = 0x10, 0x80')],
     {'WXsandtemp'}),
    ('V55 [adv] hail mask = the permanent-SUN bit', 'wc',
     [('WEATHER_SAND, WEATHER_HAIL = 0x18, 0x80', 'WEATHER_SAND, WEATHER_HAIL = 0x18, 0x40')],
     {'WXAweather', 'WXhailw'}),
    ('V57 [adv] Poison Point dropped', 'wc',
     [('CONTACT_RETALIATORS = frozenset({"Rough Skin", "Poison Point", "Flame Body", "Effect Spore"})', 'CONTACT_RETALIATORS = frozenset({"Rough Skin", "Flame Body", "Effect Spore"})')],
     {'WXppoint'}),
    ('V58 [adv] Flame Body dropped', 'wc',
     [('CONTACT_RETALIATORS = frozenset({"Rough Skin", "Poison Point", "Flame Body", "Effect Spore"})', 'CONTACT_RETALIATORS = frozenset({"Rough Skin", "Poison Point", "Effect Spore"})')],
     {'WXfbody'}),
    ('V59 [adv] Effect Spore dropped', 'wc',
     [('CONTACT_RETALIATORS = frozenset({"Rough Skin", "Poison Point", "Flame Body", "Effect Spore"})', 'CONTACT_RETALIATORS = frozenset({"Rough Skin", "Poison Point", "Flame Body"})')],
     {'WXespore'}),
    ('V60 [adv] Liquid Ooze: Leech Seed dropped', 'wc',
     [('DRAIN_EFFECTS = frozenset({"ABSORB", "LEECH_SEED"})', 'DRAIN_EFFECTS = frozenset({"ABSORB"})')],
     {'WXoozeseed'}),
    ('V62 [adv] Struggle horizon <= -> <', 'wc',
     [('    if total_pp <= horizon:', '    if total_pp < horizon:')],
     {'WPh76'}),
    ('V63 [adv] horizon slack -> 0 (the pass wrote 4 -> 0; re-anchored at 8 since PD5)', 'wc',
     [('HORIZON_SLACK = 8', 'HORIZON_SLACK = 0')],
     {'WPh76', 'WXh68'}),
    ('V70 [adv] Wonder Guard rule removed', 'wc',
     [('        if target.ability == "Wonder Guard" and m.power and (not se or nve):', '        if False:')],
     {'WXwgblock'}),
    ('V71 [adv] Wonder Guard: SE+NVE passes', 'wc',
     [('        if target.ability == "Wonder Guard" and m.power and (not se or nve):', '        if target.ability == "Wonder Guard" and m.power and not se:')],
     {'WXwgblock'}),
    ('V72 [adv] Wonder Guard blocks every exact move (cons)', 'wc',
     [('        if target.ability == "Wonder Guard" and m.power and (not se or nve):', '        if target.ability == "Wonder Guard":')],
     {'WXwgnshade', 'WXwgpass'}),
    ('V73 [adv] stage 1 picks the SMALLEST X', 'wc',
     [('        x, _neg, slot, m = max(admissible)\n        return WDecision(DAMAGE, f"stage1:', '        x, _neg, slot, m = min(admissible)\n        return WDecision(DAMAGE, f"stage1:')],
     {'WXmax', 'WXtie'}),
    ('V74 [adv] stage-1 ties to the HIGHEST slot', 'wc',
     [('        admissible.append((x, -slot, slot, m))\n    if admissible:', '        admissible.append((x, slot, slot, m))\n    if admissible:')],
     {'WXtie'}),
    ('V75 [adv] Super Fang rounds UP', 'wc',
     [('        return target.hp // 2 if target.hp >= 2 else 1', '        return (target.hp + 1) // 2 if target.hp >= 2 else 1')],
     {'WXsfodd'}),
    ('V90 [adv] stage-2 ub floor(1.1x) not ceil', 'wc',
     [('            ub = (crit_max * 11 + 9) // 10 + WEAKEN_MARGIN', '            ub = crit_max * 11 // 10 + WEAKEN_MARGIN')],
     {'WXs2bound0'}),
    ('V91 [adv] WEAKEN_MARGIN 3 -> 2', 'wc',
     [('WEAKEN_MARGIN = 3 ', 'WEAKEN_MARGIN = 2 ')],
     {'WXs2bound0'}),
    ('V92 [adv] stage-2 ub without the 10%', 'wc',
     [('            ub = (crit_max * 11 + 9) // 10 + WEAKEN_MARGIN', '            ub = crit_max + WEAKEN_MARGIN')],
     {'WXs2bound0'}),
    ('V93 [adv] stage-2 bound >=1 -> >=0', 'wc',
     [('            if not target.hp - ub >= 1:', '            if not target.hp - ub >= 0:')],
     {'WXs2bound0'}),
    ('V94 [adv] stage-2 E_gain at crit_max', 'wc',
     [('            if not e_gain(env.ball, target, env, lo) >= EGAIN_MIN:', '            if not e_gain(env.ball, target, env, crit_max) >= EGAIN_MIN:')],
     {'WXs2egain'}),
    ('V95 [adv] stage-2 progress at crit_max', 'wc',
     [('            if not lo * 100 >= PROGRESS_PCT * target.max_hp:', '            if not crit_max * 100 >= PROGRESS_PCT * target.max_hp:')],
     {'WXs2prog'}),
    ('V96 [adv] stage 2 ignores the Tier A whitelist', 'wc',
     [('        for slot, m in _usable_slots(me, TIER_A):', '        for slot, m in _usable_slots(me):')],
     {'WXs2tier'}),
    ('V97 [adv] stage 2 picks the smallest MIN', 'wc',
     [('            lo, _neg, slot, m = max(admissible)', '            lo, _neg, slot, m = min(admissible)')],
     {'WXs2max'}),
    ('V98 [adv] divergence: Marvel Scale removed', 'wc',
     [('    if target.ability == "Marvel Scale" and ((target.status1 | me.status1) & S1_ANY):', '    if False:')],
     {'WXdivms'}),
    ("V99 [adv] divergence: Marvel Scale on the TARGET's status only (the calculator's bug reads OUR status)", 'wc',
     [('    if target.ability == "Marvel Scale" and ((target.status1 | me.status1) & S1_ANY):', '    if target.ability == "Marvel Scale" and (target.status1 & S1_ANY):')],
     {'WXdivms'}),
    ('V100 [adv] divergence: Flash Fire removed', 'wc',
     [('    if me.flash_fire:', '    if False:')],
     {'WXdivff'}),
    ('V101 [adv] divergence: Charge removed', 'wc',
     [('    if me.status3 & S3_CHARGED_UP:', '    if False:')],
     {'WXAcharge', 'WXdivcharge'}),
    ('V102 [adv] divergence: badge 7 removed', 'wc',
     [('    if env.badge7 and (m.type in SPECIAL_TYPES or m.effect == "HIDDEN_POWER"):', '    if False:')],
     {'WXAb7', 'WXdivb7'}),
    ('V103 [adv] divergence: badge 7 on every move (cons)', 'wc',
     [('    if env.badge7 and (m.type in SPECIAL_TYPES or m.effect == "HIDDEN_POWER"):', '    if env.badge7:')],
     {'WXdivb7phys'}),
    ('V104 [adv] divergence: live-ability != species removed', 'wc',
     [('    if me.ability != me.species_ability or target.ability != target.species_ability:', '    if False:')],
     {'WXdivabil'}),
    ('V105 [adv] divergence: only OUR ability compared', 'wc',
     [('    if me.ability != me.species_ability or target.ability != target.species_ability:', '    if me.ability != me.species_ability:')],
     {'WXdivabil'}),
    ('V110 [adv] Vital Spirit dropped', 'wc',
     [('            if target.ability in ("Insomnia", "Vital Spirit"):', '            if target.ability in ("Insomnia",):')],
     {'WXvspirit'}),
    ('V111 [adv] Uproar: the target only', 'wc',
     [('    return bool((target.status2 | me.status2) & S2_UPROAR)', '    return bool(target.status2 & S2_UPROAR)')],
     {'WXuproarus'}),
    ('V112 [adv] Safeguard: the side bit only (eq in-game: set together)', 'wc',
     [('    if env.side_foe & SIDE_SAFEGUARD or env.safeguard_timer > 0:', '    if env.side_foe & SIDE_SAFEGUARD:')],
     {'WXAsafeguard'}),
    ('V114 [adv] Soundproof blocks every status move (cons)', 'wc',
     [('        if m.sound and target.ability == "Soundproof":', '        if target.ability == "Soundproof":')],
     {'WXhypnosp'}),
    ('V117 [adv] has-status misses freeze (poison/burn/toxic THROW-ONLY first)', 'wc',
     [('    if target.status1 & S1_ANY:\n        return None, "has-status"', '    if target.status1 & (S1_SLEEP | S1_PARALYSIS):\n        return None, "has-status"')],
     {'WXfrozen'}),
    ('V120 [adv] Ultra Ball 20 -> 15', 'wc',
     [('    if ball in ("Ultra Ball",):\n        return 20', '    if ball in ("Ultra Ball",):\n        return 15')],
     {'WXballs'}),
    ('V121 [adv] Great/Safari 15 -> 20', 'wc',
     [('    if ball in ("Great Ball", "Safari Ball"):\n        return 15', '    if ball in ("Great Ball", "Safari Ball"):\n        return 20')],
     {'WXballs'}),
    ('V122 [adv] Dive Ball inverted', 'wc',
     [('        return 35 if underwater else 10', '        return 10 if underwater else 35')],
     {'WXballs'}),
    ('V123 [adv] Repeat Ball inverted', 'wc',
     [('        return 30 if owned else 10', '        return 10 if owned else 30')],
     {'WXballs'}),
    ('V124 [adv] freeze not x2', 'wc',
     [('    if status1 & (S1_SLEEP | S1_FREEZE):', '    if status1 & S1_SLEEP:')],
     {'WXcpstatus'}),
    ('V125 [adv] toxic not x1.5', 'wc',
     [('    if status1 & (S1_POISON | S1_BURN | S1_PARALYSIS | S1_TOXIC):', '    if status1 & (S1_POISON | S1_BURN | S1_PARALYSIS):')],
     {'WXcpstatus'}),
    ("A01 [adv] the target's status3 read from OUR slot", 'sm',
     [('status3=unpack_uint32(status3[4:8]),', 'status3=unpack_uint32(status3[0:4]),')],
     {'WXAst3', 'WXAst3ours'}),
    ("A02 [adv] OUR status3 read from the target's slot", 'sm',
     [('        status2=unpack_uint32(od[0x50:0x54]), status3=unpack_uint32(status3[0:4]),', '        status2=unpack_uint32(od[0x50:0x54]), status3=unpack_uint32(status3[4:8]),')],
     {'WXAcharge'}),
    ("A03 [adv] the target's side read as OURS", 'sm',
     [('side_foe=unpack_uint16(sides[2:4])', 'side_foe=unpack_uint16(sides[0:2])')],
     {'WXAside', 'WXAsideours'}),
    ('A04 [adv] weather never read', 'sm',
     [('weather=unpack_uint16(read_symbol("gBattleWeather", size=2))', 'weather=0')],
     {'WXAweather'}),
    ("A05 [adv] the target's status1 read at 0x50", 'sm',
     [('catch_rate=int(foe.species.catch_rate), moves=moves(foe), status1=unpack_uint32(fd[0x4C:0x50]),', 'catch_rate=int(foe.species.catch_rate), moves=moves(foe), status1=unpack_uint32(fd[0x50:0x54]),')],
     {'WXAs1'}),
    ("A06 [adv] the LIVE ability replaced by the species'", 'sm',
     [('        return get_ability_by_index(bp.ability_n).name', '        return bp.ability.name')],
     {'WXAliveab'}),
    ('A07 [adv] battle flags never read', 'sm',
     [('battle_flags=int(battle_state.type.value)', 'battle_flags=4')],
     {'WXAflags'}),
    ('A08 [adv] our hold effect never read (Choice)', 'sm',
     [('        item_effect="no_effect" if ours.held_item is None else str(ours.held_item.hold_effect.value),', '        item_effect="no_effect",')],
     {'WXAchoice'}),
    ('A09 [adv] usable balls 0 (the Struggle horizon collapses)', 'sm',
     [('    usable = sum(q for name, q in bag if name != "Master Ball" and (allowed is None or name in allowed))', '    usable = 0')],
     {'WXAusable'}),
    ("A10 [adv] the mode's kinds ignored", 'sm',
     [('        kinds = tuple(getattr(mode, "_r25_weaken_kinds", _wc.DEFAULT_KINDS))', '        kinds = _wc.DEFAULT_KINDS')],
     {'WXAkinds'}),
    ("A11 [adv] a DEFER verdict (act) throws the parent's ball", 'sm',
     [('            action = None if item is None else TurnAction.use_item(item)\n', '            action = None if item is None else TurnAction.use_item(item)\n        elif ball_item is not None:\n            action = TurnAction.use_item(ball_item)\n')],
     {'WXAchoice', 'WXActx2', 'WXAflags'}),
    ('A12 [adv] observe never stores the memo', 'sm',
     [('            strategy._r25_wmemo = _wc.remember(memo, target, env, d)\n            _r25_weaken_log(f"[WEAKEN-OBS]', '            _r25_weaken_log(f"[WEAKEN-OBS]')],
     {'WXAobs2'}),
    ('A14 [adv] the party read gives the lead its SPECIES ability', 'sm',
     [('        if not lead_seen and mon.personality_value == ours_pid:\n            out.append(ours_live)', '        if not lead_seen and mon.personality_value == ours_pid:\n            out.append(mon.ability.name)')],
     {'WXAliveab'}),
    ('A16 [adv] banned_moves never read', 'sm',
     [('        banned=tuple(context.config.battle.banned_moves),', '        banned=(),')],
     {'WXAbanned'}),
    ('A17 [adv] Safeguard timer read off OUR side', 'sm',
     [('        safeguard_timer=int(battle_state.opponent.safeguard_timer.turns_remaining),', '        safeguard_timer=int(battle_state.own_side.safeguard_timer.turns_remaining),')],
     {'WXAsafeguard'}),
    ("A18 [adv] the target's SPECIES types", 'sm',
     [('types=tuple(t.name for t in foe.types), ability=live(foe)', 'types=tuple(t.name for t in foe.species.types), ability=live(foe)')],
     {'WXAtypes'}),
    ('A21 [adv] gStatuses3 never read', 'sm',
     [('    status3 = read_symbol("gStatuses3", size=8)', '    status3 = bytes(8)')],
     {'WXAcharge', 'WXAst3'}),
    ("A23 [adv] THROW's item = the bag's FIRST ball (a Master Ball first in the pocket)", 'sm',
     [('            item = ball_item if ball_item is not None and d.ball == ball_item.name else _r25_weaken_bag_ball(d.ball)', "            item = next((s.item for s in __import__('modules.items', fromlist=['x']).get_item_bag().poke_balls if s.quantity > 0), None)")],
     {'WPnit', 'WXAmaster'}),
    ("A25 [adv] the context's sp replaced by the live foe's (the context check can never fail)", 'sm',
     [('kind=kind, ctx_sp=ctx.get("sp"),', 'kind=kind, ctx_sp=f"{foe.species.name}#{foe.species.national_dex_number}",')],
     {'WXActx2'}),
    ('A26 [adv] badge 7 never read (stage 2)', 'sm',
     [('        badge7 = bool(get_event_flag("BADGE07_GET"))', '        badge7 = False')],
     {'WXAb7'}),
]
#: LEFT OUT, with the pass's own argument (equivalent, conservative or unreachable; `scratchpad/w12m/table.txt`):
#:   A15: fainted members counted (cons) -- MISS (cons: fainted members only add subjects)
#:   V01: floor hp-X>=1 -> hp-X>0 -- MISS (eq: integer hp-X>0 is hp-X>=1)
#:   V10: E_gain without max(.,1) (matters only under NOFLOOR) -- MISS (eq: after<1 only under NOFLOOR; DR-FAULT's verdict unchanged (E=1 either way))
#:   V12: E_gain >= -> > -- MISS (eq: an E_gain of exactly 1.0 does not occur)
#:   V16: odds >= -> > (eq: a p of exactly 0.5 does not exist) -- MISS (eq: p=(b/65536)^4 is never exactly 0.5)
#:   V20: Encore: the timer half dropped -- MISS (eq in-game: encoredMove/encoreTimer set+cleared together (bsc.c:8037-8039; bu.c:1720-1727,125-127))
#:   V22: Disable: the timer half dropped -- MISS (eq in-game: disabledMove/disableTimer set+cleared together (bsc.c:8006-8007; bu.c:1703-1708))
#:   V23: Disable: the move half dropped -- MISS (eq in-game: same)
#:   V34: Explosion: the TARGET's own Damp ignored (cons) -- MISS (cons: a Damp target that knows Explosion made THROW-ONLY)
#:   V61: self-harm's calling clause dropped (unreachable: THROW-ONLY calling fires first) -- MISS (unreachable: THROW-ONLY calling fires first)
#:   V76: Super Fang at hp 1 deals 0 (the game's min 1 dropped) -- MISS (eq: X=0 fails the 10% progress rule)
#:   V80: slot filter: the disabled move not dropped (eq) -- MISS (eq: THROW-ONLY 'disabled' precedes the slot filter)
#:   V82: typecalc counts a doubled type twice (eq: flags only) -- MISS (eq: types used for membership only)
#:   V106: stage 2: the Struggle exclusion dropped (eq: Struggle is never in a slot) -- MISS (eq: Struggle is never a move slot)
#:   V113: Safeguard: the timer only (eq in-game) -- MISS (eq in-game: Safeguard bit+timer set/cleared together)
#:   V116: status Substitute skip dropped (unreachable) -- MISS (unreachable: THROW-ONLY substitute precedes)
#:   V130: context by species NAME only (eq) -- MISS (eq: a species name fixes its dex number)
#: NOT ADDED: the 37 the gate already caught before the fold (V04, V09, V11, V15, V21, V32, V33, V35, V36, V39, V40,
#: V41, V42, V43, V44, V47, V48, V56, V64, V65, V66, V67, V77, V78, V79, V81, V115, V118, V119, V126, V127, V131,
#: A13, A19, A20, A22, A24).

_MUTANT_IDS = {label.split()[0] for label, _t, _e, _w in MUTANTS}
assert set(MUTANT_ADDITIONS) <= _MUTANT_IDS, sorted(set(MUTANT_ADDITIONS) - _MUTANT_IDS)
assert set(FAULT_ADDITIONS) == set(FAULT_SETS)

#: Every job: ("fault", label, env, None, want) or ("mutant", label, target, edits, want). An existing fault's or
#: mutant's EXACT set is its own literal set UNION its fold addition (both written before the fold's first run).
JOBS: list = ([("fault", f"FAULT {env}", env, None, set(want) | FAULT_ADDITIONS[env])
               for env, want in FAULT_SETS.items()]
              + [("mutant", label, target, edits, set(want) | MUTANT_ADDITIONS.get(label.split()[0], set()))
                 for label, target, edits, want in MUTANTS]
              + [("mutant", label, target, edits, set(want)) for label, target, edits, want in REVERT_MUTANTS]
              + [("mutant", label, target, edits, set(want)) for label, target, edits, want in PASS_MUTANTS])
_SRCS: dict = {}


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
    `from modules.story import weaken_catch` inside production reads the package attribute first."""
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
    real = {n: sys.modules[n] for n in (WC_NAME, SM_NAME)}
    saved_env = {k: os.environ.get(k) for k in ALL_ENVS}
    try:
        for k in ALL_ENVS:
            os.environ.pop(k, None)
        msrcs = dict(srcs)
        if kind == "fault":
            os.environ[target] = "1"
        else:
            msrcs[target] = _apply(srcs[target], edits)
            _install(WC_NAME if target == "wc" else SM_NAME, PATHS[target], msrcs[target], i)
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
                for i, red, err in pool.map(_job_red, range(len(JOBS)), chunksize=4):
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
    for k in ALL_ENVS:                          # the rows set what they need; an ambient value would skew them
        os.environ.pop(k, None)
    srcs = _sources()
    print("W — the pre-registered W-rows (and the builder's WB rows), the pure module executed")
    pure_rows("")
    print("\nWX — the adversarial pass's function rows")
    wx_rows("")
    print("\nW67 — catch_p anchors, hand-derived in integers")
    w67_rows("")
    print("\nW68 — the sweep")
    w68_rows("")
    print("\nW62 / W65 / WB — the ADAPTER on the real classes")
    adapter_rows("")
    print("\nW66 — AST pins")
    w66_rows("", srcs)
    baseline = all_rows("m", srcs)
    if baseline:
        print(f"\n⛔ BASELINE RED (no fault, no mutant): {sorted(baseline)} — a defect in the code under test. These rows "
              f"are left out of every job comparison below until fixed.")
    t1 = time.perf_counter()
    results, how = _run_jobs(inprocess)
    t2 = time.perf_counter()
    print(f"\nF/M — faults and mutants (each must turn EXACTLY its named rows red; {len(FAULT_SETS)} faults, "
          f"{len(JOBS) - len(FAULT_SETS)} mutants ({len(MUTANTS)} own, {len(REVERT_MUTANTS)} fix reverts, "
          f"{len(PASS_MUTANTS)} from the adversarial pass), run in {how}, {t2 - t1:.1f} s)")
    covered: set = set()
    for i, (kind, label, _target, _edits, want) in enumerate(JOBS):
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
