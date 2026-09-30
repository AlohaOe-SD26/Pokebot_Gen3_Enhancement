"""M1b's OFFLINE classifier and audit — design v2 step 11 (`#26-organiccatch`; the design is
`PROJECT KNOWLEDGE/ai-research-notes/2026-09-30-dmgcalc11-DESIGN.md`, F4; the line contract is
`2026-09-30-dmgcalc11-recon/m1_line_format.md`, v=1).

WHY IT EXISTS. Production (`sandbox-pokebot/modules/dmgaudit.py`, behind `POKEBOT_R25_DMGAUDIT=1`) logs RAW reads
only: a BEFORE at the selection exit, an AFTER at the next selection entry or at the battle's end. Every verdict is
computed HERE, offline, so that it is pure and gateable (`probe_dmgaudit.py`), and a classifier bug found after step
14 costs a re-audit, not a re-batch (F3).

WHAT IT DOES, in F4's order:
  1. counts the lines containing `[DMGAUDIT]` (RAW) and the ones that parse (PARSED); a mismatch, or the logger's 30 MB
     cap marker anywhere in the log, is an INSTRUMENT failure (exit 3);
  2. PAIRS each BEFORE(T) with EITHER the entry read at T+1, OR the battle-end read with `gBattleOutcome != 0` and the
     counter still T (the game never increments it on a battle's last turn: battle_main.c:3988-3997). A double
     BEFORE: the latest wins. A changed foe identity (PID) is kept only as a TRAINER KO: Δ`gBideDmg[1]` >= the foe's
     HP at BEFORE, the old PID's party HP 0, and no Spikes on the foe's side (a switch-in's Spikes are recorded);
  3. decides whether the pair is a SAMPLE: our action USE_MOVE with a nonzero chosen move, our PID unchanged, and the
     chosen MOVE's PP down by >= 1, matched by MOVE ID (never by slot);
  4. puts every sample in its STRATA (never a silent discard): each per-read reason is evaluated at BOTH reads; a hit
     is Δ`gBideDmg[1]` > 0, a 0 is "no-damage", a negative is an "instrument-fault" (the foe's Bide resets it);
  5. runs the SELF-CHECK (Δ`gBideDmg[1]` == the foe's HP difference on clean non-KO singles turns);
  6. prints the per-stratum and per-effect error vs the LIVE prediction, the self-check, one line per BEFORE, the
     INDEPENDENT PORT CONTROL (every accepted hit replayed through `dmgcalc_port.after_base` from the logged `base=`
     terms: non-crit from b, crit from bcrit; `port_calls` documents each argument), and the ACCEPTANCE: >= MIN_SAMPLES
     clean whitelisted hits and 0 over
     crit_max + ACCEPT_MARGIN. One over is a FAIL at any sample size (B1: one is enough to fail it for good); fewer
     than MIN_SAMPLES otherwise is INSUFFICIENT, never PASS.

THE FAINT RULE (DESIGN F6 ⚠, found by the first live audit): a faint RESETS the foe's gBattleMons record (ability 0,
stages neutral, item cleared), and on a trainer KO the slot holds the REPLACEMENT. So when the foe FAINTED (its AFTER
HP is 0) or was replaced, no per-mon foe check or comparison runs on the AFTER record (a reset record would otherwise
exclude EVERY KO as "changed", the very evidence B4 keeps); side-level and our-side reasons still run. What that loses
is re-covered by `foe-after-unobservable`: our move is Tier B (its secondary could only be judged on the foe's own AFTER
record), or the foe's chosen move could have changed its own damage-relevant state before our hit (FOE_SELF_STATE:
Def/SpD stages, types, a semi-invulnerable or minimized state, a sport).
TYPES: the pinch abilities and the sports key on the type a move DEALS its damage as — Hidden Power's ROLLED type
(`damage_type`) — while Charge reads the LISTED type (the port's contract; M1a's B-HPC).

STEP 11 REVIEW FIXES (review11.md, LENS audit; each pinned by rows and mutants in probe_dmgaudit.py):
  F1 persistent:marvel-scale is the FOE's Marvel Scale with the foe OR us statused (B-MS1, B-MS2); ours never counts.
  F2 SECRET_POWER is Tier B (its mountain secondary is confusion). F3 `foe-called-move` (Metronome, Mirror Move,
  Assist, Sleep Talk, Nature Power), fainted or not. F4 False Swipe excluded while the foe's HP <= crit_max + margin
  + 1 (the audit's margin reaches the classifier). F5 `our-flash-fire-unobservable` at a battle-END read. F6
  `ability-not-species` (live byte vs the species', IV bit 31; HP-0 records skipped; unloadable species data fails the
  INSTRUMENT). F7 `our-burn-changed` before a physical hit; SKULL_BASH in FOE_SELF_STATE. F8 the self-check skips a
  pending Future Sight. F9a (verified in the decomp: see TIER_B_BIDE) only a confusing Tier B secondary keeps the Tier B
  faint and AFTER-status exclusions. F9b Superpower's -1 Atk / Overheat's -2 SpA (clamped) are the move's own drop.

CHOICES WHERE F4 IS SILENT (each is conservative: it can only EXCLUDE more, never accept more):
  - `foe-profile-changed` (the foe's types, ability, Def or SpD stat differ between reads: Conversion, Camouflage,
    Transform) is the same idea as F4's "Def/SpD stage changed", for what else our calculator reads from the foe.
  - Action-derived reasons (the foe's item action, its chosen move, Pursuit) come from BEFORE only: the entry read's
    `act`/`mv` are reset to 255/0 (Step-0 raw reads), and a battle-end read repeats BEFORE's.
  - False Swipe's condition is defined on "the foe's HP before" (F2), so it has no AFTER half.
  - The self-check's enumerated heal/tick list (F4) is extended with the foe's own heal moves, Pain Split and a
    Substitute (each moves the foe's HP without, or not only through, `gBideDmg`).

Exit codes: 0 PASS, 1 FAIL, 2 INSUFFICIENT, 3 INSTRUMENT (raw != parsed, or the cap marker).

Run:  py -3.12 audit_damage_calc.py <debug-log> [--margin N]
Gate: cd tools/story-dev && PYTHONUTF8=1 py -3.12 -u probe_dmgaudit.py
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import struct
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MOVES_JSON = REPO / "sandbox-pokebot" / "modules" / "data" / "moves.json"
DEBUG_LOGGER = REPO / "sandbox-pokebot" / "modules" / "debug_logger.py"

#: The acceptance's slack over the LIVE crit_max (F8). ⚠ A PROPOSAL for the user, not a ruling: while D1 stands, a
#: STAB 4x crit on an odd post-base value reads 4 HP over ours (about 1/512 per such hit), and one over is a FAIL.
ACCEPT_MARGIN = 3
#: Fewer clean whitelisted hits than this is INSUFFICIENT, never PASS (F4).
MIN_SAMPLES = 300
#: M1a's PRE-REGISTERED bounds (PREDICTIONS: crit under by 4; crit + Charge under by 8). Reported beside the margin;
#: `probe_damage_calc_decomp.py` asserts the measured values exactly after its first run.
M1A_BOUND_CRIT = 4
M1A_BOUND_CRIT_CHARGE = 8
#: The text `debug_logger._event` writes ONCE when it stops logging events at its 30 MB cap.
CAP_MARKER = "event log size cap reached"
TAG = "[DMGAUDIT]"

# --- verdicts
ACCEPTED, EXCLUDED, NOT_A_SAMPLE, REJECTED = "ACCEPTED", "EXCLUDED", "NOT-A-SAMPLE", "REJECTED"
UNPAIRED, SUPERSEDED = "UNPAIRED", "SUPERSEDED"
PASS, FAIL, INSUFFICIENT = "PASS", "FAIL", "INSUFFICIENT"

# --- game constants (decomp `include/constants/battle.h`; `m1_line_format.md`)
ACTION_USE_MOVE, ACTION_USE_ITEM, ACTION_SWITCH = 0, 1, 2
FLAG_DOUBLE, FLAG_TRAINER = 0x1, 0x8
S1_POISON, S1_BURN, S1_PARALYSIS, S1_TOXIC = 0x8, 0x10, 0x40, 0x80
S1_FACADE = S1_POISON | S1_BURN | S1_PARALYSIS | S1_TOXIC          # Facade's (and SmellingSalt's) condition
S1_TICKS = S1_POISON | S1_BURN | S1_TOXIC                          # end-of-turn damage
S2_CONFUSION, S2_WRAPPED, S2_SUBSTITUTE = 0x7, 0xE000, 0x1000000
S2_NIGHTMARE, S2_CURSED = 0x8000000, 0x10000000
S3_LEECHSEED, S3_ON_AIR, S3_UNDERGROUND, S3_MINIMIZED = 0x4, 0x40, 0x80, 0x100
S3_CHARGED, S3_ROOTED, S3_UNDERWATER = 0x200, 0x400, 0x40000
S3_SPORTS = 0x10000 | 0x20000                                      # Mud Sport | Water Sport
SIDE_SCREENS, SIDE_SPIKES = 0x1 | 0x2, 0x10                        # Reflect | Light Screen; Spikes
#: SIDE_STATUS_FUTUREATTACK (1 << 6): include/constants/battle.h:215 (pret/pokeemerald @ f90719c4). Its hit lands in
#: HandleWishPerishSongOnTurnEnd under HITMARKER_IGNORE_BIDE (src/battle_util.c:1783), so it moves the foe's HP but
#: not gBideDmg: the self-check cannot compare that turn.
SIDE_FUTURE_ATTACK = 0x40
ST_ATK, ST_DEF, ST_SPATK, ST_SPDEF = 1, 2, 4, 5                    # statStages index (6 = neutral)
TYPE_GHOST = 7
AB_FLASH_FIRE = 18
AB_ROUGH_SKIN, AB_GUTS, AB_MARVEL_SCALE, AB_LIQUID_OOZE = 24, 62, 63, 64
AB_CLOUD_NINE, AB_AIR_LOCK = 13, 77
#: Gen 3 splits physical and special by TYPE: these deal physical damage (a burn halves them: pokemon.c's burn branch)
PHYSICAL_TYPES = frozenset({"Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel"})
PINCH = {65: "Grass", 66: "Fire", 67: "Water", 68: "Bug"}          # Overgrow, Blaze, Torrent, Swarm
ITEM_FOCUS_BAND = 196
MOVE_SURF, MOVE_STRUGGLE, MOVE_HIDDEN_POWER = 57, 165, 237
S2_FORESIGHT = 0x20000000
#: The ROM's type ids 0..17 by the names `types.json` (and so `dmgcalc_port`) uses; 9 is TYPE_MYSTERY ("???").
TYPE_NAMES = ("Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", "???", "Fire",
              "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark")

# --- the WHITELIST (F2), keyed on moves.json `effect`, except Surf and Struggle, keyed on the move index
TIER_A = frozenset({
    "HIT", "HIGH_CRITICAL", "ALWAYS_HIT", "QUICK_ATTACK", "VITAL_THROW", "PAY_DAY", "SKY_UPPERCUT",
    "THUNDER", "KNOCK_OFF", "THIEF", "RAPID_SPIN", "FLINCH_HIT", "PARALYZE_HIT", "FREEZE_HIT",
    # the stat-down and stat-up *_HIT effects (every one moves.json holds)
    "ACCURACY_DOWN_HIT", "ALL_STATS_UP_HIT", "ATTACK_DOWN_HIT", "ATTACK_UP_HIT", "DEFENSE_DOWN_HIT",
    "DEFENSE_UP_HIT", "SPECIAL_ATTACK_DOWN_HIT", "SPECIAL_DEFENSE_DOWN_HIT", "SPEED_DOWN_HIT",
    "SUPERPOWER", "OVERHEAT", "RECHARGE", "DOUBLE_EDGE", "RECOIL", "RECOIL_IF_MISS", "ABSORB", "RAGE", "HIDDEN_POWER",
})
#: a secondary that can move the FOE's HP the same turn: valid only when the AFTER read passes the status rules.
#: SECRET_POWER is here, not in Tier A (review F2): in the MOUNTAIN environment its secondary is CONFUSION
#: (battle_script_commands.c:9641-9642), and a same-turn confusion self-hit is recorded in gBideDmg.
TIER_B = frozenset({"SECRET_POWER",
                    "BURN_HIT", "BLAZE_KICK", "THAW_HIT", "TRI_ATTACK", "POISON_HIT", "POISON_TAIL", "POISON_FANG",
                    "CONFUSE_HIT"})
#: The Tier B secondaries that CAN move gBideDmg[1] on the same turn (review F9a, verified in pret/pokeemerald @
#: f90719c4): only CONFUSION does, through the foe's self-hit in its own move (battle_util.c:2145-2160, then
#: `datahpupdate BS_ATTACKER` with no HITMARKER_IGNORE_BIDE, battle_scripts_1.s:3809-3811). A burn or poison TICK
#: runs in DoBattlerEndTurnEffects, which sets HITMARKER_IGNORE_BIDE on every call (battle_util.c:1464; BattleTurnPassed
#: re-enters it per effect, battle_main.c:3965), and Cmd_datahpupdate skips the bide record under that flag
#: (battle_script_commands.c:1905-1907). Paralysis and freeze move no HP. So only these two keep the Tier B faint and
#: AFTER-status exclusions; the other Tier B moves are judged like Tier A.
TIER_B_BIDE = frozenset({"CONFUSE_HIT", "SECRET_POWER"})
#: conditional: valid only while the condition is observably false at BOTH reads (Surf joins by index)
TIER_C = frozenset({"EARTHQUAKE", "GUST", "TWISTER", "FLINCH_MINIMIZE_HIT", "FACADE", "SMELLINGSALT", "WEATHER_BALL",
                    "BRICK_BREAK", "PURSUIT", "FALSE_SWIPE", "FAKE_OUT", "FOCUS_PUNCH", "SNORE", "DREAM_EATER"})

# --- the foe's chosen move (its effect, from the data)
FOE_SELF_HURT = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "SUBSTITUTE", "BELLY_DRUM", "PAIN_SPLIT",
                           "EXPLOSION", "MEMENTO"})                 # + CURSE by a Ghost-type user
FOE_PROTECT = frozenset({"PROTECT", "ENDURE", "BIDE"})              # Protect and Detect share PROTECT
FOE_DRAIN = frozenset({"ABSORB", "DREAM_EATER", "LEECH_SEED"})
FOE_HEAL = frozenset({"RESTORE_HP", "SOFTBOILED", "MOONLIGHT", "MORNING_SUN", "SYNTHESIS", "REST", "SWALLOW", "WISH",
                      "INGRAIN", "PAIN_SPLIT"})
#: a foe move that can change what our hit meets before it lands (unobservable once the foe is replaced)
FOE_SELF_STATE = frozenset({"DEFENSE_UP", "DEFENSE_UP_2", "SPECIAL_DEFENSE_UP_2", "DEFENSE_CURL", "COSMIC_POWER",
                            "CALM_MIND", "BULK_UP", "CURSE", "SUPERPOWER", "DEFENSE_UP_HIT", "ALL_STATS_UP_HIT",
                            "PSYCH_UP", "HAZE", "SEMI_INVULNERABLE", "MINIMIZE", "MUD_SPORT", "WATER_SPORT",
                            "CONVERSION", "CONVERSION_2", "CAMOUFLAGE", "TRANSFORM", "SKILL_SWAP", "ROLE_PLAY",
                            "SKULL_BASH"})                     # Skull Bash's first turn: Def +1 (review F7)
#: a foe move that CALLS another move (review F3): what it runs, and so whether it hurts the foe or changes its state,
#: cannot be read from the chosen move (Mirror Move copies our Take Down and its recoil). Sleep Talk is redundant with
#: foe-status and Nature Power calls only plain moves in Gen 3; both are here for completeness (they only exclude more).
FOE_CALLS_MOVE = frozenset({"METRONOME", "MIRROR_MOVE", "ASSIST", "SLEEP_TALK", "NATURE_POWER"})


def _load_moves(path: Path = MOVES_JSON) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)                    # a list: the index IS the move index (Surf 57, Struggle 165)


MOVES = _load_moves()

SPECIES_JSON = REPO / "sandbox-pokebot" / "modules" / "data" / "species.json"
ABILITIES_JSON = REPO / "sandbox-pokebot" / "modules" / "data" / "abilities.json"


def _load_species_abilities(species_path: Path = SPECIES_JSON, abilities_path: Path = ABILITIES_JSON) -> list:
    """Each ROM species index -> its ability ids, from the SAME files the bot loads (modules/pokemon.py:
    `species.json`'s list index IS the ROM species index; `abilities.json`'s index IS the ability id). A name that
    abilities.json does not hold raises: the table is never silently partial."""
    with open(abilities_path, encoding="utf-8") as fh:
        ids = {a["name"]: i for i, a in enumerate(json.load(fh))}
    with open(species_path, encoding="utf-8") as fh:
        return [tuple(ids[name] for name in s["abilities"]) for s in json.load(fh)]


#: (review F6) None + the error when the species data cannot be loaded: `audit_text` then fails the INSTRUMENT (exit 3).
try:
    SPECIES_ABILITIES, SPECIES_ERROR = _load_species_abilities(), ""
except Exception as _error:  # noqa: BLE001 - reported as an instrument failure by every audit, never swallowed
    SPECIES_ABILITIES, SPECIES_ERROR = None, f"{type(_error).__name__}: {_error}"


def species_ability(m) -> int | None:
    """The ability the SPECIES gives this record: the second one when the IV word's bit 31 (abilityNum) is set and the
    species has two (the bot's own rule, battle_state.py `ability`); None when the species is unknown."""
    if SPECIES_ABILITIES is None or not 0 <= m.species < len(SPECIES_ABILITIES):
        return None
    abilities = SPECIES_ABILITIES[m.species]
    return abilities[1] if len(abilities) > 1 and m.ivs >> 31 & 1 else abilities[0]


def _ability_not_species(m) -> bool:
    """(review F6) The LIVE ability byte (0x20) differs from the species ability (Trace, Role Play, Skill Swap): our
    calculator reads the SPECIES one. A fainted record (HP 0) is skipped: a faint resets the byte to 0 (DESIGN F6 ⚠;
    every mismatch in the first live log, ours included, was such a record)."""
    if m.hp == 0 or SPECIES_ABILITIES is None:
        return False
    return species_ability(m) != m.ability


def move_info(move_id: int) -> dict:
    if 0 <= move_id < len(MOVES):
        m = MOVES[move_id]
        return {"effect": m["effect"], "type": m["type"], "name": m["name"]}
    return {"effect": "?", "type": "?", "name": f"#{move_id}"}


def tier_of(move_id: int, effect: str) -> str:
    """"A", "B", "C" or "OUT" (F2). Surf and Struggle by INDEX: Surf is HIT yet doubles vs a diving target; Struggle
    is RECOIL yet typeless."""
    if move_id == MOVE_STRUGGLE:
        return "OUT"
    if move_id == MOVE_SURF:
        return "C"
    if effect in TIER_A:
        return "A"
    if effect in TIER_B:
        return "B"
    if effect in TIER_C:
        return "C"
    return "OUT"


# ============================================================================================================ parsing
@dataclass
class Mon:
    species: int
    atk: int
    def_: int
    spe: int
    spa: int
    spd: int
    moves: tuple
    ivs: int
    stages: tuple
    ability: int
    type1: int
    type2: int
    pp: tuple
    hp: int
    level: int
    maxhp: int
    item: int
    pid: int
    status1: int
    status2: int


def parse_mon(raw: bytes) -> Mon:
    """`struct BattlePokemon` (0x58; decomp `include/pokemon.h`)."""
    if len(raw) != 0x58:
        raise ValueError(f"a BattlePokemon record is 0x58 bytes, got {len(raw)}")
    (species, atk, def_, spe, spa, spd, m0, m1, m2, m3, ivs, stages, ability, type1, type2, pp, hp, level, maxhp,
     item) = _MON_HEAD.unpack_from(raw, 0x00)
    pid, status1, status2 = _MON_TAIL.unpack_from(raw, 0x48)
    return Mon(species=species, atk=atk, def_=def_, spe=spe, spa=spa, spd=spd, moves=(m0, m1, m2, m3), ivs=ivs,
               stages=tuple(stages), ability=ability, type1=type1, type2=type2, pp=tuple(pp), hp=hp, level=level,
               maxhp=maxhp, item=item, pid=pid, status1=status1, status2=status2)


#: 0x00 species, 0x02-0x0A the five stats, 0x0C moves[4], 0x14 the IV word, 0x18 statStages[8], 0x20 ability, 0x21/0x22
#: types, (0x23 pad), 0x24 pp[4], 0x28 hp, 0x2A level, (0x2B friendship), 0x2C maxHP, 0x2E item; then 0x48 personality,
#: 0x4C status1, 0x50 status2.
_MON_HEAD = struct.Struct("<6H4HI8s3Bx4sHBxHH")
_MON_TAIL = struct.Struct("<3I")


@dataclass
class Rec:
    frame: int
    kind: str                       # CTL | BEFORE | AFTER | ERR
    line_no: int
    t: int = 0
    out: int = 0
    flags: int = 0
    act: tuple = ()
    mv: tuple = ()
    bide: tuple = ()
    weather: int = 0
    side: tuple = ()
    s3: tuple = ()
    mons: tuple = ()
    ff: tuple | None = None
    badges: int = 0
    pred: tuple | None = None       # (min, max, crit_min, crit_max) or None
    pred_raw: str = ""
    base: tuple | None = None       # (b, bcrit): the calculator's own base term, non-crit and crit; None for `none`
    eff: str = ""
    after_kind: str = ""            # entry | end
    party: tuple = ()               # ((pid, hp), ...) x 6
    where: str = ""
    err: str = ""


LINE_RE = re.compile(r"^f(\d+) \[DMGAUDIT\] ([A-Z]+)((?: [^ ]+)*)$")
RAW_KEYS = ("t", "out", "flags", "act", "mv", "bide", "weather", "side", "s3", "dis", "mons", "ff")
KEYS = {"CTL": ("v",), "BEFORE": ("v",) + RAW_KEYS + ("badges", "pred", "base", "eff"),
        "AFTER": ("v", "kind") + RAW_KEYS + ("party",), "ERR": ("v", "where", "err")}


_INT_RE = re.compile(r"-?\d+")
_HEX_RE = {w: re.compile(f"[0-9a-f]{{{w}}}") for w in (8, 56, 176)}


def _int(s: str) -> int:
    if not _INT_RE.fullmatch(s):
        raise ValueError(f"not an int: {s!r}")
    return int(s)


_INTS_RE = {n: re.compile(",".join([r"-?\d+"] * n)) for n in (2, 4)}
_HEXES_RE = {(n, w): re.compile(",".join([f"[0-9a-f]{{{w}}}"] * n)) for n in (1, 2) for w in (8, 56, 176)}


def _ints(s: str, n: int) -> tuple:
    """Exactly n comma-separated decimal ints (one regex for the whole field)."""
    if not _INTS_RE[n].fullmatch(s):
        raise ValueError(f"want {n} ints: {s!r}")
    return tuple(int(p) for p in s.split(","))


def _hexes(s: str, n: int, width: int) -> tuple:
    """Exactly n comma-separated lowercase hex strings of `width` digits (one regex for the whole field)."""
    if not _HEXES_RE[(n, width)].fullmatch(s):
        raise ValueError(f"want {n} x hex{width}: {s[:40]!r}")
    return tuple(s.split(","))


def parse_line(line: str, line_no: int = 0) -> Rec:
    """One `[DMGAUDIT]` line -> a Rec; ValueError on ANY deviation from the v=1 contract (it then counts as unparsed,
    and raw != parsed fails the audit)."""
    m = LINE_RE.match(line)
    if not m:
        raise ValueError("not `f<frame> [DMGAUDIT] <KIND> <key=value>...`")
    kind = m.group(2)
    if kind not in KEYS:
        raise ValueError(f"unknown kind {kind}")
    fields: dict = {}
    for tok in m.group(3).split(" ")[1:]:
        key, eq, value = tok.partition("=")
        if not eq or not key or key in fields:
            raise ValueError(f"bad or repeated field {tok[:40]!r}")
        fields[key] = value
    if set(fields) != set(KEYS[kind]):
        raise ValueError(f"{kind} fields {sorted(fields)} != the contract's {sorted(KEYS[kind])}")
    if fields["v"] != "1":
        raise ValueError(f"v={fields['v']} (this audit reads v=1)")
    r = Rec(frame=int(m.group(1)), kind=kind, line_no=line_no)
    if kind == "ERR":
        if fields["where"] not in ("ctl", "before", "after-entry", "after-end") or not re.fullmatch(r"[\w.]+",
                                                                                                   fields["err"]):
            raise ValueError("bad ERR fields")
        r.where, r.err = fields["where"], fields["err"]
        return r
    if kind == "CTL":
        return r
    r.t, r.out, r.weather = _int(fields["t"]), _int(fields["out"]), _int(fields["weather"])
    r.flags = int(_hexes(fields["flags"], 1, 8)[0], 16)
    r.act, r.mv, r.bide = _ints(fields["act"], 4), _ints(fields["mv"], 4), _ints(fields["bide"], 4)
    r.side = _ints(fields["side"], 2)
    r.s3 = tuple(int(h, 16) for h in _hexes(fields["s3"], 2, 8))
    _hexes(fields["dis"], 2, 56)
    r.mons = tuple(parse_mon(bytes.fromhex(h)) for h in _hexes(fields["mons"], 2, 176))
    r.ff = None if fields["ff"] == "null" else _ints(fields["ff"], 2)
    if kind == "BEFORE":
        r.badges = _int(fields["badges"])
        r.pred_raw = fields["pred"]
        if fields["pred"] == "none" or re.fullmatch(r"err:[\w.]+", fields["pred"]):
            r.pred = None
        else:
            r.pred = _ints(fields["pred"], 4)
        r.base = None if fields["base"] == "none" else _ints(fields["base"], 2)
        if not re.fullmatch(r"-|[A-Z0-9_]+", fields["eff"]):
            raise ValueError(f"bad eff {fields['eff']!r}")
        r.eff = fields["eff"]
    else:
        if fields["kind"] not in ("entry", "end"):
            raise ValueError(f"bad AFTER kind {fields['kind']!r}")
        r.after_kind = fields["kind"]
        party = []
        for p in fields["party"].split(","):
            pm = re.fullmatch(r"([0-9a-f]{8}):(\d+)", p)
            if not pm:
                raise ValueError(f"bad party entry {p!r}")
            party.append((int(pm.group(1), 16), int(pm.group(2))))
        if len(party) != 6:
            raise ValueError("party wants 6 entries")
        r.party = tuple(party)
    return r


# ============================================================================================================ classify
@dataclass
class Verdict:
    before: Rec
    after: Rec | None
    status: str = ""
    kind: str = ""                  # turn | KO | trainer KO | battle end (outcome N)
    reasons: tuple = ()
    move: int = 0
    effect: str = ""
    tier: str = ""
    battle: str = ""                # wild | trainer
    d_bide: int | None = None       # Δ gBideDmg[1]: the observed damage of a sample
    d_bide0: int | None = None
    tags: tuple = ()
    selfcheck: str = ""             # agree | DISAGREE | n/a: <why>

    @property
    def pred(self):
        return self.before.pred


def _pp_drop(me_b: Mon, me_a: Mon, move_id: int):
    """The chosen MOVE's PP drop, matched by move id in each read (never by slot) [R:SR-2]; None if not in both."""
    if move_id not in me_b.moves or move_id not in me_a.moves:
        return None
    return me_b.pp[me_b.moves.index(move_id)] - me_a.pp[me_a.moves.index(move_id)]


def _entry_pairing(b: Rec, a: Rec):
    return None if a.t == b.t + 1 else "turn-gap"


def _end_pairing(b: Rec, a: Rec):
    if a.out == 0:
        return "end-without-outcome"
    return None if a.t == b.t else "end-turn-moved"


def _trainer_ko(b: Rec, a: Rec, d_bide: int):
    """None when a changed foe identity is a trainer KO (F4); else the rejection reason."""
    old = b.mons[1]
    if d_bide < old.hp:
        return "foe-changed-not-ko"
    if not any(pid == old.pid and hp == 0 for pid, hp in a.party):
        return "foe-changed-old-hp-not-0"
    if (b.side[1] | a.side[1]) & SIDE_SPIKES:
        return "foe-changed-spikes"
    return None


def damage_type(move_id: int, me: Mon) -> str:
    """The type the move DEALS its damage as: Hidden Power's ROLLED type (the game's dynamicMoveType, pokemon.c:3215 and
    :3219; our calculator does the same), every other move's LISTED type. What the pinch abilities and the sports key
    on. (Charge alone reads the LISTED type: `port_calls`, `m1a_bound`.)"""
    return hidden_power_type(me.ivs) if move_id == MOVE_HIDDEN_POWER else move_info(move_id)["type"]


def _state_reasons(rd: Rec, move_id: int, mv: dict, foe_ok: bool) -> set:
    """The strata that are a STATE of one read. Evaluated at BEFORE and at AFTER. `foe_ok` False = the foe's AFTER
    record is not the foe we hit (it FAINTED, so the game reset its record, or a trainer KO put the replacement in the
    slot), so the per-mon foe checks do not apply to it."""
    out: set = set()
    me, foe = rd.mons
    eff, mtype = mv["effect"], damage_type(move_id, me)
    if foe_ok:
        if foe.status1:
            out.add("foe-status")
        if foe.status2 & S2_CONFUSION:
            out.add("foe-confused")
        if foe.status2 & S2_WRAPPED:
            out.add("foe-trapped")
        if rd.s3[1] & S3_LEECHSEED:
            out.add("foe-leech-seed")
        if foe.status2 & S2_CURSED:
            out.add("foe-cursed")
        if foe.status2 & S2_NIGHTMARE:
            out.add("foe-nightmare")
        if foe.status2 & S2_SUBSTITUTE:
            out.add("foe-substitute")
        if foe.item == ITEM_FOCUS_BAND:
            out.add("foe-focus-band")
        if foe.item:
            out.add("foe-held-item")
        if _ability_not_species(foe):
            out.add("ability-not-species")
        # Tier C, the foe's half
        if move_id == MOVE_SURF and rd.s3[1] & S3_UNDERWATER:
            out.add("C:surf-underwater")
        if eff == "EARTHQUAKE" and rd.s3[1] & S3_UNDERGROUND:
            out.add("C:earthquake-underground")
        if eff in ("GUST", "TWISTER") and rd.s3[1] & S3_ON_AIR:
            out.add("C:gust-in-the-air")
        if eff == "FLINCH_MINIMIZE_HIT" and rd.s3[1] & S3_MINIMIZED:
            out.add("C:minimized")
        if eff == "SMELLINGSALT" and foe.status1 & S1_PARALYSIS:
            out.add("C:smellingsalt-paralysis")
    # Tier C, our half and the field
    if eff == "FACADE" and me.status1 & S1_FACADE:
        out.add("C:facade-status")
    if eff == "WEATHER_BALL" and rd.weather:
        out.add("C:weather-ball-weather")
    if eff == "BRICK_BREAK" and rd.side[1] & SIDE_SCREENS:
        out.add("C:brick-break-screens")
    if mtype in ("Fire", "Electric") and (rd.s3[0] | (rd.s3[1] if foe_ok else 0)) & S3_SPORTS:
        out.add("C:sport")
    # our side
    if me.hp <= me.maxhp // 3 and PINCH.get(me.ability) == mtype:
        out.add("our-pinch")
    if rd.ff is not None and rd.ff[0]:
        out.add("our-flash-fire")
    if me.ability == AB_ROUGH_SKIN:
        out.add("our-rough-skin")
    if _ability_not_species(me):
        out.add("ability-not-species")
    return out


def _before_reasons(b: Rec, move_id: int, mv: dict, margin: int = ACCEPT_MARGIN) -> set:
    """What only BEFORE carries: the chosen actions (the entry read resets them), and the PERSISTENT known-divergence
    states at BEFORE (M1a's rows) [R:M1b-8]."""
    out: set = set()
    me, foe = b.mons
    foe_act, foe_mv = b.act[1], b.mv[1]
    if foe_act == ACTION_USE_ITEM:
        out.add("foe-item-action")
    if foe_act == ACTION_USE_MOVE:
        feff = move_info(foe_mv)["effect"]
        if foe_mv == 0:
            out.add("foe-move-zero")                    # Struggle, or a locked move (Uproar) [R:M1b-9]
        elif feff in FOE_SELF_HURT or (feff == "CURSE" and TYPE_GHOST in (foe.type1, foe.type2)):
            out.add("foe-self-hurt-move")
        if feff in FOE_PROTECT:
            out.add("foe-protect-endure-bide")
        if feff in FOE_CALLS_MOVE:
            out.add("foe-called-move")                  # (review F3) a BEFORE reason: it fires whether or not the foe fainted
    if mv["effect"] == "PURSUIT" and foe_act == ACTION_SWITCH:
        out.add("C:pursuit-switch")
    # the hp-1 clamp can bind [R:M1A-8] whenever the foe's HP is at most the GAME's damage, which may exceed crit_max:
    # while it is within crit_max + margin + 1, a clamped observation could sit inside the acceptance band (review F4)
    if mv["effect"] == "FALSE_SWIPE" and b.pred is not None and foe.hp <= b.pred[3] + margin + 1:
        out.add("C:false-swipe-hp")
    if me.ability == AB_GUTS and me.status1 & S1_BURN:
        out.add("persistent:guts-burn")
    # (review F1) only the FOE's Marvel Scale touches damage WE deal. The game raises its Def when the FOE is statused
    # (pokemon.c:3213); our calculator does it when WE are (_util.py:399-400). Either state is a known divergence
    # (M1a's rows B-MS1 and B-MS2); our own Marvel Scale never affects our attack.
    if foe.ability == AB_MARVEL_SCALE and (foe.status1 or me.status1):
        out.add("persistent:marvel-scale")
    if {me.ability, foe.ability} & {AB_CLOUD_NINE, AB_AIR_LOCK}:
        out.add("persistent:cloud-nine-air-lock")
    if b.ff is not None and b.ff[0]:
        out.add("persistent:flash-fire")
    return out


def _change_reasons(b: Rec, a: Rec, move_id: int, mv: dict, tier: str, foe_fainted: bool, d_bide0: int) -> set:
    """What only the PAIR shows: a change between the reads, and our HP's dip. When the foe FAINTED (or was replaced)
    its AFTER record says nothing about the foe we hit, so no per-mon foe comparison runs; the foe's CHOSEN move stands
    in for it (DESIGN F6 ⚠: a faint resets ability, stages and item)."""
    out: set = set()
    me_b, foe_b = b.mons
    me_a, foe_a = a.mons
    if not foe_fainted:
        if (foe_b.stages[ST_DEF], foe_b.stages[ST_SPDEF]) != (foe_a.stages[ST_DEF], foe_a.stages[ST_SPDEF]):
            out.add("foe-def-stage-changed")
        if (foe_b.type1, foe_b.type2, foe_b.ability, foe_b.def_, foe_b.spd) != \
                (foe_a.type1, foe_a.type2, foe_a.ability, foe_a.def_, foe_a.spd):
            out.add("foe-profile-changed")
    else:
        foe_eff = move_info(b.mv[1])["effect"] if b.act[1] == ACTION_USE_MOVE else ""
        if mv["effect"] in TIER_B_BIDE or foe_eff in FOE_SELF_STATE:
            out.add("foe-after-unobservable")           # (review F9a: only a secondary that can move gBideDmg[1])
    if (b.side[1] ^ a.side[1]) & SIDE_SCREENS:
        out.add("foe-screens-changed")
    stages_b = (me_b.stages[ST_ATK], me_b.stages[ST_SPATK])
    stages_a = (me_a.stages[ST_ATK], me_a.stages[ST_SPATK])
    # (review F9b) Superpower drops our Atk by 1 and Overheat our SpA by 2, AFTER the hit (battle_scripts_1.s:2388-2389
    # and :2648-2649, clamped at stage 0 by statbuffchange): exactly that drop is the move's own, not a change the hit met
    own_drop = {"SUPERPOWER": (max(0, stages_b[0] - 1), stages_b[1]),
                "OVERHEAT": (stages_b[0], max(0, stages_b[1] - 2))}.get(mv["effect"])
    if stages_a != stages_b and stages_a != own_drop:
        out.add("our-attack-stage-changed")
    if me_b.status1 != me_a.status1 and (me_b.ability == AB_GUTS or mv["effect"] == "FACADE"):
        out.add("our-status-changed-guts-facade")
    if (me_b.status1 ^ me_a.status1) & S1_BURN and damage_type(move_id, me_b) in PHYSICAL_TYPES:
        out.add("our-burn-changed")                     # (review F7) a burn halves a physical hit, whatever our ability
    # (review F5) the battle-end read cannot read Flash Fire (gBattleResources is freed): a Flash Fire mon's Fire hit
    # after the foe's Fire move this turn may have been boosted, unobservably
    if (a.after_kind == "end" and me_b.ability == AB_FLASH_FIRE and damage_type(move_id, me_b) == "Fire"
            and b.act[1] == ACTION_USE_MOVE and move_info(b.mv[1])["type"] == "Fire"):
        out.add("our-flash-fire-unobservable")
    if b.weather != a.weather:
        out.add("weather-changed")
    if me_b.hp - d_bide0 <= me_b.maxhp // 3 and PINCH.get(me_b.ability) == damage_type(move_id, me_b):
        out.add("our-pinch")                            # the dip: HP before - Δ gBideDmg[0] [R:M1b-7]
    if me_b.ability == AB_LIQUID_OOZE and (
            (b.act[1] == ACTION_USE_MOVE and move_info(b.mv[1])["effect"] in FOE_DRAIN)
            or (b.s3[0] | a.s3[0]) & S3_LEECHSEED):
        out.add("our-liquid-ooze")                      # [R:SR-15]
    return out


def _selfcheck(b: Rec, a: Rec) -> str:
    """F4's self-check on a clean turn: Δ gBideDmg[1] == the foe's HP difference. 'n/a: <why>' when not clean."""
    foe_b, foe_a = b.mons[1], a.mons[1]
    if a.after_kind != "entry":
        return "n/a: battle end"
    if b.flags & FLAG_DOUBLE:
        return "n/a: doubles"
    if foe_b.pid != foe_a.pid:
        return "n/a: foe changed"
    if foe_a.hp == 0:
        return "n/a: KO"
    if foe_b.item:
        return "n/a: foe held item"
    if b.act[1] == ACTION_USE_ITEM:
        return "n/a: foe item action"
    if b.act[1] == ACTION_USE_MOVE and move_info(b.mv[1])["effect"] in (FOE_DRAIN | FOE_HEAL):
        return "n/a: foe drain or heal move"
    if (b.s3[0] | a.s3[0]) & S3_LEECHSEED:
        return "n/a: leech seed on us"
    if ((foe_b.status1 | foe_a.status1) & S1_TICKS or (b.s3[1] | a.s3[1]) & (S3_LEECHSEED | S3_ROOTED)
            or (foe_b.status2 | foe_a.status2) & (S2_CURSED | S2_NIGHTMARE | S2_WRAPPED | S2_SUBSTITUTE)
            or b.weather or a.weather):
        return "n/a: end-of-turn tick"
    if (b.side[1] | a.side[1]) & SIDE_FUTURE_ATTACK:
        return "n/a: future attack"                     # (review F8) it lands under HITMARKER_IGNORE_BIDE
    return "agree" if a.bide[1] - b.bide[1] == foe_b.hp - foe_a.hp else "DISAGREE"


def classify_pair(b: Rec, a: Rec, margin: int = ACCEPT_MARGIN) -> Verdict:
    v = Verdict(before=b, after=a)
    me_b, foe_b = b.mons
    me_a, foe_a = a.mons
    v.battle = "trainer" if b.flags & FLAG_TRAINER else "wild"
    v.d_bide, v.d_bide0 = a.bide[1] - b.bide[1], a.bide[0] - b.bide[0]
    v.move = b.mv[0]
    mv = move_info(v.move)
    v.effect, v.tier = mv["effect"], tier_of(v.move, mv["effect"])
    # 1. the pairing (F4) [R:M1b-1, SR-1]
    if a.after_kind == "end":
        pairing = _end_pairing(b, a)
    else:
        pairing = _entry_pairing(b, a)
    if pairing:
        v.status, v.reasons = REJECTED, (pairing,)
        return v
    v.selfcheck = _selfcheck(b, a)
    # 2. a SAMPLE: our move ran
    if b.act[0] != ACTION_USE_MOVE or v.move == 0:
        v.status, v.reasons = NOT_A_SAMPLE, ("our-action-not-a-move",)
        return v
    same_me = me_b.pid == me_a.pid
    if not same_me:
        v.status, v.reasons = REJECTED, ("our-identity-changed",)
        return v
    drop = _pp_drop(me_b, me_a, v.move)
    if drop is None:
        v.status, v.reasons = NOT_A_SAMPLE, ("our-move-not-in-moveset",)
        return v
    if drop < 1:
        v.status, v.reasons = NOT_A_SAMPLE, ("our-pp-unchanged",)
        return v
    # 3. the foe's identity: a change is kept only as a trainer KO
    same_foe = foe_b.pid == foe_a.pid
    if not same_foe:
        why = _trainer_ko(b, a, v.d_bide)
        if why:
            v.status, v.reasons = REJECTED, (why,)
            return v
        v.kind = "trainer KO"
    elif a.after_kind == "end":
        v.kind = "KO" if foe_a.hp == 0 else f"battle end (outcome {a.out})"
    else:
        v.kind = "turn"
    # 4. the strata: never a silent discard
    reasons: set = set()
    if b.flags & FLAG_DOUBLE:
        reasons.add("doubles")
    if v.d_bide < 0:
        reasons.add("instrument-fault")                 # the foe's Bide resets gBideDmg [R:M1b-9]
    if v.d_bide == 0:
        reasons.add("no-damage")                        # a miss, Protect, a failed move [R:M1b-2]
    if b.pred is None:
        reasons.add("no-prediction")
    elif b.pred[1] == 0:
        reasons.add("predicted-immune")
    if v.tier == "OUT":
        reasons.add("outside-whitelist")
    # A faint RESETS the foe's gBattleMons record (ability 0, stages neutral, item cleared: DESIGN F6 ⚠, found by the
    # first live audit), and a trainer KO puts the replacement in the slot: either way the AFTER record is not the foe
    # we hit, so no per-mon foe check or comparison runs on it.
    foe_fainted = not same_foe or foe_a.hp == 0
    reasons |= _state_reasons(b, v.move, mv, foe_ok=True)
    reasons |= _state_reasons(a, v.move, mv, foe_ok=not foe_fainted)
    reasons |= _before_reasons(b, v.move, mv, margin)
    reasons |= _change_reasons(b, a, v.move, mv, v.tier, foe_fainted, v.d_bide0)
    # (review F9a) a Tier B secondary other than confusion cannot move gBideDmg[1] this turn (its burn/poison ticks run
    # under HITMARKER_IGNORE_BIDE: see TIER_B_BIDE), so the status it leaves at AFTER is not a reason. The foe had none
    # at BEFORE, so "foe-status" can only have come from the AFTER read.
    if v.tier == "B" and v.effect not in TIER_B_BIDE and not foe_b.status1:
        reasons.discard("foe-status")
    v.reasons = tuple(sorted(reasons))
    v.status = EXCLUDED if reasons else ACCEPTED
    return v


def over_bound(obs: int, crit_max: int, margin: int) -> bool:
    return obs > crit_max + margin


def m1a_bound(v: Verdict) -> int:
    charged = v.before.s3[0] & S3_CHARGED and move_info(v.move)["type"] == "Electric"
    return M1A_BOUND_CRIT_CHARGE if charged else M1A_BOUND_CRIT


def _tags(v: Verdict, margin: int = ACCEPT_MARGIN) -> tuple:
    if v.pred is None or v.d_bide is None or v.d_bide <= 0:
        return ()
    lo, hi, _cmin, cmax = v.pred
    obs, out = v.d_bide, []
    if obs < lo:
        out.append("below-noncrit-min")
    if hi < obs <= cmax:
        out.append("crit-or-under-prediction (ambiguous)")
    if obs > cmax:
        out.append(f"over-crit_max+{obs - cmax}")
    if over_bound(obs, cmax, margin):
        out.append("OVER-ACCEPTANCE-BOUND")
    return tuple(out)


# ============================================================================================================ the audit
@dataclass
class Report:
    raw_count: int = 0
    parsed_count: int = 0
    unparsed: list = field(default_factory=list)       # (line_no, error, line)
    capped: bool = False
    species_error: str = ""                             # (review F6) the species data could not be loaded
    by_kind: dict = field(default_factory=dict)
    errs: list = field(default_factory=list)
    orphans: list = field(default_factory=list)        # AFTERs with no pending BEFORE
    eff_mismatch: list = field(default_factory=list)
    verdicts: list = field(default_factory=list)
    margin: int = ACCEPT_MARGIN
    acceptance: str = ""
    hits: list = field(default_factory=list)
    over: list = field(default_factory=list)

    @property
    def instrument_ok(self) -> bool:
        return self.raw_count == self.parsed_count and not self.capped and not self.species_error

    @property
    def selfcheck_disagreements(self) -> list:
        return [v for v in self.verdicts if v.selfcheck == "DISAGREE"]

    @property
    def exit_code(self) -> int:
        if not self.instrument_ok:
            return 3
        return {PASS: 0, FAIL: 1, INSUFFICIENT: 2}[self.acceptance]


def pair_records(recs: list, margin: int = ACCEPT_MARGIN) -> tuple[list, list]:
    """Log order. A BEFORE is pending until the next AFTER consumes it; a later BEFORE supersedes it (the latest
    wins); a CTL (battle start) clears it. Returns (verdicts for every BEFORE, orphan AFTERs). `margin` reaches the
    classifier (False Swipe's band, review F4)."""
    verdicts, orphans = [], []
    pending = None
    for r in recs:
        if r.kind == "CTL":
            if pending is not None:
                verdicts.append(Verdict(before=pending, after=None, status=UNPAIRED, reasons=("no-after-before-ctl",)))
            pending = None
        elif r.kind == "BEFORE":
            if pending is not None:
                verdicts.append(Verdict(before=pending, after=None, status=SUPERSEDED,
                                        reasons=("a-later-before",)))
            pending = r
        elif r.kind == "AFTER":
            if pending is None:
                orphans.append(r)
            else:
                verdicts.append(classify_pair(pending, r, margin))
                pending = None
    if pending is not None:
        verdicts.append(Verdict(before=pending, after=None, status=UNPAIRED, reasons=("no-after-at-log-end",)))
    verdicts.sort(key=lambda v: v.before.line_no)
    return verdicts, orphans


def acceptance(verdicts: list, margin: int) -> tuple[str, list, list]:
    hits = [v for v in verdicts if v.status == ACCEPTED]
    over = [v for v in hits if over_bound(v.d_bide, v.pred[3], margin)]
    if over:
        return FAIL, hits, over
    if len(hits) < MIN_SAMPLES:
        return INSUFFICIENT, hits, over
    return PASS, hits, over


@lru_cache(maxsize=1 << 16)
def _parse_memo(line: str, line_no: int) -> Rec:
    """`parse_line`, memoised on (line, line number): the gate re-audits the same 300-sample block many times per pass.
    A failure is not cached (lru_cache re-raises every time); nothing downstream mutates a Rec."""
    return parse_line(line, line_no)


def audit_text(text: str, margin: int = ACCEPT_MARGIN) -> Report:
    rep = Report(margin=margin)
    lines = text.splitlines()
    recs = []
    for i, ln in enumerate(lines, 1):
        if TAG not in ln:
            continue
        try:
            recs.append(_parse_memo(ln, i))
        except ValueError as error:
            rep.unparsed.append((i, str(error), ln))
    rep.raw_count = sum(1 for ln in lines if TAG in ln)
    rep.parsed_count = len(recs)
    rep.capped = any(CAP_MARKER in ln for ln in lines)
    rep.species_error = "" if SPECIES_ABILITIES is not None else (SPECIES_ERROR or "the species table is missing")
    for r in recs:
        rep.by_kind[r.kind] = rep.by_kind.get(r.kind, 0) + 1
    rep.errs = [r for r in recs if r.kind == "ERR"]
    rep.eff_mismatch = [r for r in recs if r.kind == "BEFORE" and r.eff != "-"
                        and r.eff != move_info(r.mv[0])["effect"]]
    rep.verdicts, rep.orphans = pair_records(recs, margin)
    for v in rep.verdicts:
        if v.status in (ACCEPTED, EXCLUDED):
            v.tags = _tags(v, margin)
    rep.acceptance, rep.hits, rep.over = acceptance(rep.verdicts, margin)
    return rep


# ============================================================================================================ output
def _stats_row(label: str, vs: list, margin: int) -> str:
    hs = [v for v in vs if v.pred is not None and v.pred[3] > 0 and v.d_bide is not None and v.d_bide > 0]
    if not hs:
        return f"  {label:<44} {0:>4}  -"
    diff = max(v.d_bide - v.pred[3] for v in hs)
    ratio = max(v.d_bide / v.pred[3] for v in hs)
    n_margin = sum(over_bound(v.d_bide, v.pred[3], margin) for v in hs)
    n_m1a = sum(v.d_bide > v.pred[3] + m1a_bound(v) for v in hs)
    below = sum(v.d_bide < v.pred[0] for v in hs)
    return f"  {label:<44} {len(hs):>4}  {diff:>+13}  {ratio:>13.3f}  {n_margin:>8}  {n_m1a:>9}  {below:>5}"


def hidden_power_type(ivs: int) -> str:
    """The type Hidden Power ROLLS (pokeemerald `Cmd_hiddenpowercalc`): bit i of the type bits is the low bit of IV i
    in the order HP, Atk, Def, Speed, SpAtk, SpDef (the IV word at 0x14 holds them as 5-bit fields in that order);
    type = 15 * bits / 63 + 1, skipping TYPE_MYSTERY (9)."""
    bits = sum(((ivs >> (5 * i)) & 1) << i for i in range(6))
    t = 15 * bits // 63 + 1
    if t >= 9:
        t += 1
    return TYPE_NAMES[t]


def port_calls(v: Verdict) -> list[dict]:
    """The two `dmgcalc_port.after_base` calls that replay one sample, as keyword dicts: non-crit from `b`, crit from
    `bcrit` (the calculator's own base terms, logged as `base=`). What the port's contract asks for:
      move_type — the type the move ROLLS (GET_MOVE_TYPE: Hidden Power's dynamic type; for every other move, its
                  listed type); the port uses it for STAB and the type chart;
      charge_listed_electric — our gStatuses3 CHARGED_UP (0x200) AND the move's LISTED type Electric (BSC:1298 reads
                  the move table: a Hidden Power that rolled Electric is NOT doubled; M1a's row B-HPC);
      attacker_types / defender_types_rom — (type1 0x21, type2 0x22) of our and the foe's BEFORE records, ROM order;
      struggle — move 165; foresight — the FOE's status2 FORESIGHT bit (Ghost immunity lifted).
    Raises (ValueError / IndexError) when the record cannot be replayed (`base=none`, a type id outside 0..17)."""
    b = v.before
    if b.base is None:
        raise ValueError("base=none")
    me, foe = b.mons
    listed = move_info(v.move)["type"]
    rolled = hidden_power_type(me.ivs) if v.move == MOVE_HIDDEN_POWER else listed
    common = dict(move_type=rolled,
                  attacker_types=(TYPE_NAMES[me.type1], TYPE_NAMES[me.type2]),
                  defender_types_rom=(TYPE_NAMES[foe.type1], TYPE_NAMES[foe.type2]),
                  charge_listed_electric=bool(b.s3[0] & S3_CHARGED) and listed == "Electric",
                  struggle=v.move == MOVE_STRUGGLE,
                  foresight=bool(foe.status2 & S2_FORESIGHT))
    return [dict(B=b.base[0], crit=False, **common), dict(B=b.base[1], crit=True, **common)]


def port_control(hits: list) -> list[str]:
    """The INDEPENDENT control (F4 [R:SR-7]): every clean accepted hit replayed through M1a's decomp-ordered port
    (`dmgcalc_port.after_base`, imported lazily) from the calculator's own base terms; an observation outside the
    port's [non-crit min, crit max] is counted and listed with its frame. It checks the ORACLE against the game's real
    damage, beside the acceptance (which checks OUR calculator)."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    try:
        port = importlib.import_module("dmgcalc_port")
    except ImportError as error:
        return [f"port control: unavailable (no dmgcalc_port module: {error})"]
    fn = getattr(port, "after_base", None)
    if fn is None:
        return ["port control: unavailable (dmgcalc_port has no after_base)"]
    outside, unreplayable = [], []
    for v in hits:
        try:
            calls = port_calls(v)
            lo, _ = fn(**calls[0])
            _, hi = fn(**calls[1])
        except Exception:  # noqa: BLE001 - a record the control cannot replay is reported, never stops the audit
            unreplayable.append(v.before.frame)
            continue
        if not lo <= v.d_bide <= hi:
            outside.append((v.before.frame, v.d_bide, lo, hi))
    line = (f"port control: {len(hits)} clean hits: {len(hits) - len(unreplayable)} replayed, "
            f"{len(unreplayable)} unreplayable {unreplayable[:20]}, {len(outside)} outside the port's "
            f"[non-crit min, crit max]")
    if outside:
        line += ": " + ", ".join(f"f{f} obs {o} port [{lo},{hi}]" for f, o, lo, hi in outside[:20])
    return [line]


def pair_line(v: Verdict) -> str:
    b, a = v.before, v.after
    foe_b = b.mons[1]
    if a is None:
        hp = f"{foe_b.hp}->?"
    elif a.mons[1].pid == foe_b.pid:
        hp = f"{foe_b.hp}->{a.mons[1].hp}"
    else:
        old = next((h for pid, h in a.party if pid == foe_b.pid), "?")
        hp = f"{foe_b.hp}->{old} (party; replaced by {a.mons[1].species})"
    d = "-" if v.d_bide is None else str(v.d_bide)
    pred = "none" if b.pred is None else f"[{b.pred[0]},{b.pred[1]}] cmax={b.pred[3]}"
    extra = f" kind={v.kind}" if v.kind else ""
    if v.status in (ACCEPTED, EXCLUDED):
        extra += f" {v.battle} tier={v.tier} eff={v.effect} pred={pred}"
    return (f"  f{b.frame} foe={foe_b.species} hp={hp} dbide={d} {v.status}{extra}"
            f" reasons={','.join(v.reasons) or '-'} tags={','.join(v.tags) or '-'}"
            f"{' self-check=' + v.selfcheck if v.selfcheck else ''}")


def render(rep: Report) -> list[str]:
    out = ["== instrument =="]
    kinds = ", ".join(f"{k} {rep.by_kind.get(k, 0)}" for k in ("CTL", "BEFORE", "AFTER", "ERR"))
    out.append(f"  [DMGAUDIT] lines: raw {rep.raw_count}, parsed {rep.parsed_count} ({kinds})")
    for i, err, ln in rep.unparsed[:20]:
        out.append(f"    UNPARSED line {i}: {err} :: {ln[:160]}")
    out.append(f"  logger cap marker ({CAP_MARKER!r}): {'PRESENT' if rep.capped else 'absent'}")
    if rep.errs:
        out.append(f"  ERR lines: {len(rep.errs)}: " + ", ".join(f"f{r.frame} {r.where} {r.err}" for r in rep.errs[:20]))
    if rep.orphans:
        out.append(f"  orphan AFTERs (no pending BEFORE): {len(rep.orphans)}: {[r.frame for r in rep.orphans[:20]]}")
    if rep.eff_mismatch:
        out.append(f"  WARN eff disagrees with moves.json on {len(rep.eff_mismatch)} BEFOREs: "
                   f"{[r.frame for r in rep.eff_mismatch[:20]]}")
    if rep.instrument_ok:
        out.append("  INSTRUMENT: OK")
    else:
        why = []
        if rep.raw_count != rep.parsed_count:
            why.append(f"raw {rep.raw_count} != parsed {rep.parsed_count}")
        if rep.capped:
            why.append("the logger hit its 30 MB cap (events after it are missing)")
        if rep.species_error:
            why.append(f"the species data could not be loaded ({rep.species_error}): ability-not-species is unchecked")
        out.append("  INSTRUMENT: FAIL — " + "; ".join(why))

    out.append("== strata (a pair carries every reason that applies; each reason is counted) ==")
    for status in (ACCEPTED, EXCLUDED, NOT_A_SAMPLE, REJECTED, UNPAIRED, SUPERSEDED):
        vs = [v for v in rep.verdicts if v.status == status]
        line = f"  {status:<44} {len(vs):>4}"
        if status == ACCEPTED and vs:
            def split(key):
                c: dict = {}
                for v in vs:
                    c[key(v)] = c.get(key(v), 0) + 1
                return ", ".join(f"{k} {n}" for k, n in sorted(c.items()))
            line += f"   ({split(lambda v: v.battle)}; tier {split(lambda v: v.tier)}; {split(lambda v: v.kind)})"
        out.append(line)
        counts: dict = {}
        for v in vs:
            if status == ACCEPTED:
                continue
            for r in v.reasons:
                counts[r] = counts.get(r, 0) + 1
        for r, n in sorted(counts.items()):
            out.append(f"    {r:<42} {n:>4}")

    m = rep.margin
    out.append(f"== error vs the LIVE prediction (hits with a prediction; M = ACCEPT_MARGIN {m}; M1a bound "
               f"{M1A_BOUND_CRIT}, {M1A_BOUND_CRIT_CHARGE} with Charge) ==")
    out.append(f"  {'group':<44} {'n':>4}  {'max(obs-cmax)':>13}  {'max(obs/cmax)':>13}  {'>cmax+M':>8}  "
               f"{'>cmax+M1a':>9}  {'<min':>5}")
    acc = [v for v in rep.verdicts if v.status == ACCEPTED]
    out.append(_stats_row("ACCEPTED (the acceptance set)", acc, m))
    for eff in sorted({v.effect for v in acc}):
        out.append(_stats_row(f"  effect {eff}", [v for v in acc if v.effect == eff], m))
    exc = [v for v in rep.verdicts if v.status == EXCLUDED]
    for r in sorted({r for v in exc for r in v.reasons}):
        out.append(_stats_row(f"stratum {r}", [v for v in exc if r in v.reasons], m))
    for eff in sorted({v.effect for v in exc}):
        out.append(_stats_row(f"excluded effect {eff}", [v for v in exc if v.effect == eff], m))
    amb = [v.before.frame for v in acc if any(t.startswith("crit-or-under") for t in v.tags)]
    out.append(f"  crit or under-prediction, ambiguous (max < obs <= crit_max), accepted: {len(amb)}: {amb[:20]}")
    below = [v.before.frame for v in acc if "below-noncrit-min" in v.tags]
    out.append(f"  hits below the non-crit min (step 12's progress side), accepted: {len(below)}: {below[:20]}")

    elig = [v for v in rep.verdicts if v.selfcheck in ("agree", "DISAGREE")]
    dis = rep.selfcheck_disagreements
    na: dict = {}
    for v in rep.verdicts:
        if v.selfcheck.startswith("n/a"):
            na[v.selfcheck] = na.get(v.selfcheck, 0) + 1
    out.append("== self-check (clean singles non-KO turns: Δ gBideDmg[1] == the foe's HP difference) ==")
    out.append(f"  eligible {len(elig)} at {[v.before.frame for v in elig][:30]}; disagreements {len(dis)}: "
               + str([(v.before.frame, v.d_bide, v.before.mons[1].hp - v.after.mons[1].hp) for v in dis][:30]))
    out.append(f"  not eligible: {dict(sorted(na.items()))}")

    out.append("== one line per BEFORE (frame, foe species, HP before->after, Δbide, verdict, reasons) ==")
    out.extend(pair_line(v) for v in rep.verdicts)
    out.append("== independent control ==")
    out.extend("  " + ln for ln in port_control(acc))

    n = len(rep.hits)
    detail = (f"{n} clean whitelisted hits (floor {MIN_SAMPLES}); {len(rep.over)} over crit_max + {m} "
              f"(ACCEPT_MARGIN {m}, a PROPOSAL for the user)")
    if rep.over:
        detail += ": " + ", ".join(f"f{v.before.frame} obs {v.d_bide} > {v.pred[3]}+{m}" for v in rep.over[:20])
    out.append(f"ACCEPTANCE: {rep.acceptance} — {detail}")
    if not rep.instrument_ok:
        out.append("EXIT 3: the instrument failed; the acceptance above is not graded")
    return out


def run_text(text: str, margin: int = ACCEPT_MARGIN) -> tuple[int, list[str], Report]:
    rep = audit_text(text, margin)
    return rep.exit_code, render(rep), rep


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1b's offline [DMGAUDIT] classifier and audit (design v2 step 11, F4)")
    ap.add_argument("log", help="a debug log written with POKEBOT_R25_DMGAUDIT=1")
    ap.add_argument("--margin", type=int, default=ACCEPT_MARGIN, help=f"ACCEPT_MARGIN (default {ACCEPT_MARGIN})")
    args = ap.parse_args(argv)
    text = Path(args.log).read_text(encoding="utf-8", errors="replace")
    code, lines, _rep = run_text(text, args.margin)
    for ln in lines:
        print(ln)
    return code


if __name__ == "__main__":
    sys.exit(main())
