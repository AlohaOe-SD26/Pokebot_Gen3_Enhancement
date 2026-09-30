"""Design v2 step 12 (W, weaken-to-catch; USER RULING 25): the PURE decision module.

WHY. RULING 25 wants a wanted wild Pokémon WEAKENED before the balls are thrown, and never KNOCKED OUT: a KO loses the
species for this encounter, and the balls it would have saved were the point. This module decides, for ONE turn of a
catch battle, whether to DAMAGE (with a move whose damage is known exactly, or — stage 2, behind its own flag — a hit
the calculator bounds), to STATUS (sleep over paralysis), to THROW the parent's own best ball, or to DEFER (hand the
turn to the parent `CatchStrategy`, byte-identical to the flag being off). The spec is
`PROJECT KNOWLEDGE/ai-research-notes/2026-09-30-weaken12-DESIGN.md` (D1-D15); every row the gate
`tools/story-dev/probe_weaken_catch.py` asserts was pre-registered in `…-weaken12-PREDICTIONS.md` before this file
existed.

⛔ THE CONTRACT
- PURE: no emulator, no memory read, no `random`, no import of the damage calculator. The adapter
  (`plugins/custom_modes/story_mode.py`, `_r25_weaken_turn`) builds the frozen snapshots below from the `battle_state`
  it is handed plus pure `read_symbol` reads, and passes stage 2's numbers (min, crit_max) in `WEnv.calc_ranges`.
- The ONLY environment reads are the FAULT arms (`FAULT_*`), each a production switch that changes exactly ONE rule and
  is never set in a real run (registered in `29-DISABLED-FEATURES-REGISTRY.md`). The feature flags themselves are
  read ONCE per run by `StoryMode.reset_per_run_state` and arrive here inside `WEnv`.
- Offsets are decoded HERE, from raw bytes, so the gate pins them: our disable struct's `encoredMove` is at 0x06
  (`include/battle.h:73-74`); `battle_state.py`'s `encored_move` reads 0x04 (the disabled move) — a shared-path bug
  (upstream too) that D9 routes to its own KI; deliberately NOT fixed here.
- The catch chance is `battle_script_commands.c:9987-10028` in its own integer order (D12); the float
  `calculate_catch_success_chance` exceeds 1 above odds 254 and is never used here.
- The module never returns an item other than a Poké Ball (RULING 27: no healing items, ever).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from math import isqrt

# ============================================================================================================ switches
FLAG = "POKEBOT_R25_WEAKEN"                      # {unset, observe, 1}: read per run by reset_per_run_state
FLAG_CALC = "POKEBOT_R25_WEAKEN_CALC"            # {unset, 1}: stage 2 (the calculator's bound)
FLAG_KINDS = "POKEBOT_R25_WEAKEN_KINDS"          # default "dex,team"
DEFAULT_KINDS = ("dex", "team")

#: FAULT arms (graded only; never set in a real run). Each changes exactly the ONE rule its name gives.
FAULT_NOFLOOR = "POKEBOT_R25_FAULT_WEAKEN_NOFLOOR"          # skip hp - X >= 1 (E then taken at max(hp - X, 1))
FAULT_NOENCORE = "POKEBOT_R25_FAULT_WEAKEN_NOENCORE"        # skip "the target knows Encore -> no damage"
FAULT_CALCLEAK = "POKEBOT_R25_FAULT_WEAKEN_CALCLEAK"        # stage 2 runs with POKEBOT_R25_WEAKEN_CALC unset
FAULT_ACTIVEONLY = "POKEBOT_R25_FAULT_WEAKEN_ACTIVEONLY"    # the retaliation clause reads the LEAD only
FAULT_NOPP = "POKEBOT_R25_FAULT_WEAKEN_NOPP"                # stage 1 ignores the raw slot's PP
FAULT_MASTERBALL = "POKEBOT_R25_FAULT_WEAKEN_MASTERBALL"    # THROW's ball = the best held ball BY catch_p
FAULT_SPECIESID = "POKEBOT_R25_FAULT_WEAKEN_SPECIESID"      # the target's identity by SPECIES, not PID
FAULT_NETGAIN = "POKEBOT_R25_FAULT_WEAKEN_NETGAIN"          # E_gain netted: E(hp) - (1 + E(hp - X))
FAULT_NAMEDISPATCH = "POKEBOT_R25_FAULT_WEAKEN_NAMEDISPATCH"  # exact damage dispatched by the calculator's NAMES
FAULTS = (FAULT_NOFLOOR, FAULT_NOENCORE, FAULT_CALCLEAK, FAULT_ACTIVEONLY, FAULT_NOPP, FAULT_MASTERBALL,
          FAULT_SPECIESID, FAULT_NETGAIN, FAULT_NAMEDISPATCH)


def _fault(name: str) -> bool:
    return os.environ.get(name, "").strip() == "1"


# ============================================================================================================ verdicts
DAMAGE, STATUS, THROW, DEFER = "DAMAGE", "STATUS", "THROW", "DEFER"
VERDICTS = frozenset({DAMAGE, STATUS, THROW, DEFER})
#: Every Gen 3 ball (items.json names). A THROW returns one of these and nothing else (RULING 27).
BALLS = frozenset({"Master Ball", "Ultra Ball", "Great Ball", "Poké Ball", "Safari Ball", "Net Ball", "Dive Ball",
                   "Nest Ball", "Repeat Ball", "Timer Ball", "Luxury Ball", "Premier Ball"})

# ============================================================================================================ constants
#: D4's judgements (design v2 §3 "Weaken constants"; re-derived from step 14's batch).
ODDS_THROW_ONLY = 0.5       # the one-throw chance at or above which weakening is pointless
EGAIN_MIN = 1.0             # expected BALLS saved (E(hp) - E(hp - X)) a damage turn must buy
PROGRESS_PCT = 10           # a damage turn must take at least 10% of max HP
WEAKEN_MARGIN = 3           # stage 2: ub = ceil(crit_max * 1.10) + WEAKEN_MARGIN (NOT ACCEPT_MARGIN: dmgcalc11 F8)
CAP_DAMAGE_TURNS = 1        # per battle
CAP_STATUS_TRIES = 3        # per battle; a berry cure counts as a try
CAP_NO_PROGRESS = 2         # acting turns after which neither HP nor status moved -> throw-only
PRESSURE_FACTOR = 2         # Struggle horizon H = 2 * (usable balls + slack): the 2 covers our Pressure
#: PD5 (the adversarial pass, 2026-09-30) raised the slack from 4 to 8: with 30 usable balls H is 76 (it was 68).
#: ⚠ WHAT IT BOUNDS (corrected by the build review, W12-S1): the THROW phase only, never a flee phase. A trapped Run is
#: refused at SELECTION and costs no turn (battle_main.c:4339-4346), and ordinary failed flees are UNBOUNDED
#: (battle_util.c:464-475: the u8 speedVar wraps from runTries 5, so success is never guaranteed). ⇒ While the catch is
#: attempted, the target cannot Struggle into its own recoil within the horizon; once the catch is ABANDONED (the
#: out-of-balls flee, or the dex reserve / faint bail), a failed-flee phase can still let a PP-exhausted target Struggle
#: into its own recoil. That residual is recorded, and no slack value can bound it.
HORIZON_SLACK = 8

# --- raw bits (include/constants/battle.h)
S1_SLEEP, S1_POISON, S1_BURN, S1_FREEZE, S1_PARALYSIS, S1_TOXIC = 0x7, 0x8, 0x10, 0x20, 0x40, 0x80
S1_ANY = S1_SLEEP | S1_POISON | S1_BURN | S1_FREEZE | S1_PARALYSIS | S1_TOXIC
S2_CONFUSION, S2_UPROAR, S2_WRAPPED = 0x7, 0x70, 0xE000
S2_SUBSTITUTE, S2_NIGHTMARE, S2_CURSED, S2_FORESIGHT, S2_TORMENT = 1 << 24, 1 << 27, 1 << 28, 1 << 29, 1 << 31
S3_LEECHSEED, S3_ON_AIR, S3_UNDERGROUND, S3_CHARGED_UP = 1 << 2, 1 << 6, 1 << 7, 1 << 9
S3_IMPRISONED_OTHERS, S3_UNDERWATER = 1 << 13, 1 << 18
S3_SEMI_INVULNERABLE = S3_ON_AIR | S3_UNDERGROUND | S3_UNDERWATER
SIDE_SAFEGUARD, SIDE_FUTUREATTACK = 1 << 5, 1 << 6
WEATHER_SAND, WEATHER_HAIL = 0x18, 0x80          # gBattleWeather: sandstorm temporary|permanent; hail

#: gBattleTypeFlags: every bit that makes this anything but an ordinary single WILD battle -> DEFER (D4). That is
#: the design's list (trainer, safari, double, roamer, the legendary / Regi / Kyogre / Groudon / Rayquaza flags,
#: Pyramid, Pike) widened to "every bit except IS_MASTER (1 << 2, set in an ordinary wild battle: the Step-0 reads
#: log flags=4) and RECORDED_IS_MASTER (1 << 31)" — link, multi, the tutorial and first battle, the Frontier, etc.
NON_SINGLE_WILD = 0xFFFFFFFF & ~((1 << 2) | (1 << 31))
BT_DOUBLE, BT_TRAINER, BT_SAFARI, BT_ROAMER, BT_LEGENDARY = 1 << 0, 1 << 3, 1 << 7, 1 << 10, 1 << 13

# --- move effects (moves.json `effect`; dispatch is by EFFECT, never by name)
EXACT_EFFECTS = frozenset({"LEVEL_DAMAGE", "SONICBOOM", "DRAGON_RAGE", "SUPER_FANG"})
#: the calculator's NAMES (`_util.py` :215-224) — only the NAMEDISPATCH fault uses them ("Sonic Boom" != "Sonicboom")
CALC_EXACT_NAMES = ("Dragon Rage", "Sonic Boom", "Super Fang", "Night Shade", "Seismic Toss")
#: PAIN_SPLIT (PD2, the adversarial pass): the target's Pain Split before our hit sets its HP to the average of the
#: two, while our X was bounded on its start-of-turn HP.
SELF_HARM_EFFECTS = frozenset({"RECOIL", "DOUBLE_EDGE", "RECOIL_IF_MISS", "RAMPAGE", "BELLY_DRUM", "EXPLOSION",
                               "PAIN_SPLIT"})
ENDER_EFFECTS = frozenset({"TELEPORT", "ROAR", "PERISH_SONG", "MEMENTO"})
CALLING_EFFECTS = frozenset({"METRONOME", "MIRROR_MOVE", "ASSIST", "SLEEP_TALK"})
ACQUIRE_EFFECTS = frozenset({"TRANSFORM", "MIMIC", "SKETCH"})
DRAIN_EFFECTS = frozenset({"ABSORB", "LEECH_SEED"})
SLEEP_EFFECT, PARALYZE_EFFECT = "SLEEP", "PARALYZE"
CONTACT_RETALIATORS = frozenset({"Rough Skin", "Poison Point", "Flame Body", "Effect Spore"})
MOVE_STRUGGLE = 165
#: Stage 2's Tier A (plain: one hit, fixed power, no condition) — `tools/story-dev/audit_damage_calc.py` TIER_A, the
#: step-11 whitelist (dmgcalc11 F2), keyed on effect; Struggle (move 165) is excluded by index.
TIER_A = frozenset({
    "HIT", "HIGH_CRITICAL", "ALWAYS_HIT", "QUICK_ATTACK", "VITAL_THROW", "PAY_DAY", "SKY_UPPERCUT",
    "THUNDER", "KNOCK_OFF", "THIEF", "RAPID_SPIN", "FLINCH_HIT", "PARALYZE_HIT", "FREEZE_HIT",
    "ACCURACY_DOWN_HIT", "ALL_STATS_UP_HIT", "ATTACK_DOWN_HIT", "ATTACK_UP_HIT", "DEFENSE_DOWN_HIT",
    "DEFENSE_UP_HIT", "SPECIAL_ATTACK_DOWN_HIT", "SPECIAL_DEFENSE_DOWN_HIT", "SPEED_DOWN_HIT",
    "SUPERPOWER", "OVERHEAT", "RECHARGE", "DOUBLE_EDGE", "RECOIL", "RECOIL_IF_MISS", "ABSORB", "RAGE", "HIDDEN_POWER",
})
#: PD5 (the adversarial pass): Tier A members stage 2 never admits. A RECHARGE move's recharge turn throws no ball and
#: is not counted by the Struggle horizon. (TIER_A itself stays the step-11 whitelist, verbatim.)
STAGE2_EXCLUDED = frozenset({"RECHARGE"})
#: Gen 3's special types (a type's split decides physical/special; the badge-7 boost divergence is special-side)
SPECIAL_TYPES = frozenset({"Fire", "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark"})

#: gTypeEffectiveness (`src/battle_main.c` :335-450), in the game's order: (attacker, defender, x10). The entries after
#: the FORESIGHT marker are skipped when the target has Foresight on it (Cmd_typecalc's loop breaks there).
_CHART = (
    ("Normal", "Rock", 5), ("Normal", "Steel", 5), ("Fire", "Fire", 5), ("Fire", "Water", 5), ("Fire", "Grass", 20),
    ("Fire", "Ice", 20), ("Fire", "Bug", 20), ("Fire", "Rock", 5), ("Fire", "Dragon", 5), ("Fire", "Steel", 20),
    ("Water", "Fire", 20), ("Water", "Water", 5), ("Water", "Grass", 5), ("Water", "Ground", 20),
    ("Water", "Rock", 20), ("Water", "Dragon", 5), ("Electric", "Water", 20), ("Electric", "Electric", 5),
    ("Electric", "Grass", 5), ("Electric", "Ground", 0), ("Electric", "Flying", 20), ("Electric", "Dragon", 5),
    ("Grass", "Fire", 5), ("Grass", "Water", 20), ("Grass", "Grass", 5), ("Grass", "Poison", 5),
    ("Grass", "Ground", 20), ("Grass", "Flying", 5), ("Grass", "Bug", 5), ("Grass", "Rock", 20),
    ("Grass", "Dragon", 5), ("Grass", "Steel", 5), ("Ice", "Water", 5), ("Ice", "Grass", 20), ("Ice", "Ice", 5),
    ("Ice", "Ground", 20), ("Ice", "Flying", 20), ("Ice", "Dragon", 20), ("Ice", "Steel", 5), ("Ice", "Fire", 5),
    ("Fighting", "Normal", 20), ("Fighting", "Ice", 20), ("Fighting", "Poison", 5), ("Fighting", "Flying", 5),
    ("Fighting", "Psychic", 5), ("Fighting", "Bug", 5), ("Fighting", "Rock", 20), ("Fighting", "Dark", 20),
    ("Fighting", "Steel", 20), ("Poison", "Grass", 20), ("Poison", "Poison", 5), ("Poison", "Ground", 5),
    ("Poison", "Rock", 5), ("Poison", "Ghost", 5), ("Poison", "Steel", 0), ("Ground", "Fire", 20),
    ("Ground", "Electric", 20), ("Ground", "Grass", 5), ("Ground", "Poison", 20), ("Ground", "Flying", 0),
    ("Ground", "Bug", 5), ("Ground", "Rock", 20), ("Ground", "Steel", 20), ("Flying", "Electric", 5),
    ("Flying", "Grass", 20), ("Flying", "Fighting", 20), ("Flying", "Bug", 20), ("Flying", "Rock", 5),
    ("Flying", "Steel", 5), ("Psychic", "Fighting", 20), ("Psychic", "Poison", 20), ("Psychic", "Psychic", 5),
    ("Psychic", "Dark", 0), ("Psychic", "Steel", 5), ("Bug", "Fire", 5), ("Bug", "Grass", 20), ("Bug", "Fighting", 5),
    ("Bug", "Poison", 5), ("Bug", "Flying", 5), ("Bug", "Psychic", 20), ("Bug", "Ghost", 5), ("Bug", "Dark", 20),
    ("Bug", "Steel", 5), ("Rock", "Fire", 20), ("Rock", "Ice", 20), ("Rock", "Fighting", 5), ("Rock", "Ground", 5),
    ("Rock", "Flying", 20), ("Rock", "Bug", 20), ("Rock", "Steel", 5), ("Ghost", "Normal", 0),
    ("Ghost", "Psychic", 20), ("Ghost", "Dark", 5), ("Ghost", "Steel", 5), ("Ghost", "Ghost", 20),
    ("Dragon", "Dragon", 20), ("Dragon", "Steel", 5), ("Dark", "Fighting", 5), ("Dark", "Psychic", 20),
    ("Dark", "Ghost", 20), ("Dark", "Dark", 5), ("Dark", "Steel", 5), ("Steel", "Fire", 5), ("Steel", "Water", 5),
    ("Steel", "Electric", 5), ("Steel", "Ice", 20), ("Steel", "Rock", 20), ("Steel", "Steel", 5),
    ("FORESIGHT", "FORESIGHT", 0),
    ("Normal", "Ghost", 0), ("Fighting", "Ghost", 0),
)


def type_effect(move_type: str, def_types, foresight: bool) -> tuple[bool, bool, bool]:
    """(immune, super_effective, not_very_effective) exactly as Cmd_typecalc walks the chart (a type listed twice
    counts once: `types[0] != types[1]`)."""
    types = tuple(dict.fromkeys(def_types))
    immune = se = nve = False
    for atk, dfn, mul in _CHART:
        if atk == "FORESIGHT":
            if foresight:
                break
            continue
        if atk != move_type or dfn not in types:
            continue
        if mul == 0:
            immune = True
        elif mul > 10:
            se = True
        elif mul < 10:
            nve = True
    return immune, se, nve


# ============================================================================================================ snapshots
@dataclass(frozen=True)
class WMove:
    """One RAW move slot (never the compacted `BattlePokemon.moves`): id, data fields, and its current PP."""
    move_id: int
    name: str
    effect: str
    type: str
    power: int
    pp: int
    contact: bool = False
    sound: bool = False


@dataclass(frozen=True)
class WTarget:
    pid: int
    species_id: int
    species: str
    dex: int
    level: int
    hp: int
    max_hp: int
    types: tuple            # LIVE (gBattleMons 0x21/0x22)
    ability: str            # LIVE (0x20, Trace-able), mapped to its name
    species_ability: str
    catch_rate: int
    moves: tuple            # the 4 RAW slots (WMove or None)
    status1: int = 0
    status2: int = 0
    status3: int = 0
    item: str | None = None
    item_effect: str = "no_effect"  # the held item's hold effect (PD3: a confuse_* berry); a default for old snapshots


@dataclass(frozen=True)
class WSelf:
    pid: int
    species: str
    level: int
    hp: int
    max_hp: int
    types: tuple
    ability: str            # LIVE
    species_ability: str
    moves: tuple            # the 4 RAW slots
    status1: int = 0
    status2: int = 0
    status3: int = 0
    item: str | None = None
    item_effect: str = "no_effect"
    disable: bytes = bytes(0x1C)   # our gDisableStructs[0], RAW (decoded below, so the gate pins the offsets)
    flash_fire: bool = False       # our Flash Fire boost MAY be on (stage 2's divergence; the adapter is conservative)


@dataclass(frozen=True)
class WParty:
    """The abilities of EVERY party member able to battle (not an egg, HP > 0) — the retaliation clause's subjects
    (any faint-switch brings one in). The lead's entry is its LIVE ability."""
    abilities: tuple


@dataclass(frozen=True)
class WEnv:
    flag: str = ""                  # "", "observe" or "1" (anything else is off)
    calc: bool = False              # POKEBOT_R25_WEAKEN_CALC=1
    kinds: tuple = DEFAULT_KINDS
    kind: str | None = None         # the mode's `_catch_ctx["kind"]`
    ctx_sp: str | None = None       # the mode's `_catch_ctx["sp"]`, "<species>#<national dex>"
    battle_flags: int = 0           # gBattleTypeFlags
    turn: int = 0                   # gBattleResults + 0x13, a PURE read (KI-108: never a cached BattleState)
    weather: int = 0                # gBattleWeather
    side_foe: int = 0               # gSideStatuses[1] (the target's side)
    safeguard_timer: int = 0        # the target side's Safeguard timer
    ball: str | None = None         # THE ball THROW uses: the parent's `_get_best_poke_ball` (allowlist; never Master)
    bag: tuple = ()                 # ((ball name, quantity), ...) every ball held
    usable_balls: int = 0           # the parent's throwable balls (allowlist, Master Ball excluded)
    banned: tuple = ()              # context.config.battle.banned_moves
    badge7: bool = False            # stage 2 only
    underwater: bool = False        # the Dive Ball's condition
    owned: bool = False             # the Repeat Ball's condition
    calc_ranges: tuple = ()         # stage 2: per RAW slot (min, crit_max) or None, from the adapter's calculator
    read_error: str | None = None


@dataclass(frozen=True)
class WMemo:
    """Per-battle state, carried on the strategy instance. `history` holds the FIRST decision of each turn, keyed on
    the pure turn read (`decide_turn` can run more than once per turn): (turn, verdict, target hp, target status1)."""
    pid: int
    species_id: int
    ctx_ok: bool
    history: tuple = ()


@dataclass(frozen=True)
class WDecision:
    verdict: str
    reason: str
    slot: int | None = None         # the RAW move slot (the game's move-menu index) for DAMAGE / STATUS
    move: str | None = None
    ball: str | None = None         # THROW only
    stage: int | None = None        # DAMAGE only: 1 (exact) or 2 (the calculator's bound)
    x: int | None = None            # DAMAGE: the exact damage (stage 1) or the non-crit min (stage 2)


# ============================================================================================================ decoders
def _u16(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def disabled_move(disable: bytes) -> int:
    return _u16(disable, 0x04)


def encored_move(disable: bytes) -> int:
    """`struct DisableStruct.encoredMove` is at 0x06 (`include/battle.h:73-74`), NOT 0x04 (that is `disabledMove`)."""
    return _u16(disable, 0x06)


def disable_timer(disable: bytes) -> int:
    return disable[0x0B] & 0xF


def encore_timer(disable: bytes) -> int:
    return disable[0x0E] & 0xF


def taunt_timer(disable: bytes) -> int:
    return disable[0x13] & 0xF


# ========================================================================================================= catch chance
def ball_bonus_x10(ball: str, *, level: int, types, turn: int, underwater: bool, owned: bool) -> int | None:
    """The ball's multiplier x10 (`battle_script_commands.c:9936-9985`, `sBallCatchBonuses` :841). None = the Master
    Ball (success is forced). ⚠ Net Ball reads the battler's LIVE types; the Timer Ball's u8 wraps exactly as the
    game's."""
    if ball == "Master Ball":
        return None
    if ball in ("Ultra Ball",):
        return 20
    if ball in ("Great Ball", "Safari Ball"):
        return 15
    if ball == "Net Ball":
        return 30 if ("Water" in types or "Bug" in types) else 10
    if ball == "Dive Ball":
        return 35 if underwater else 10
    if ball == "Nest Ball":
        if level < 40:
            m = (40 - level) & 0xFF
            return 10 if m <= 9 else m
        return 10
    if ball == "Repeat Ball":
        return 30 if owned else 10
    if ball == "Timer Ball":
        m = (turn + 10) & 0xFF
        return 40 if m > 40 else m
    return 10                        # Poké, Luxury, Premier (and any unknown name: the plain multiplier)


def catch_p(rate: int, bonus_x10: int, max_hp: int, hp: int, status1: int) -> float:
    """The one-throw chance, `Cmd_handleballthrow` (`battle_script_commands.c:9987-10028`) in its own integer order:
    odds = (rate * bonus / 10) * (3*max - 2*hp) / (3*max); sleep/freeze x2; poison/burn/paralysis/toxic x15/10;
    odds > 254 -> caught; else b = 1048560 / Sqrt(Sqrt(16711680 / odds)) and 4 checks of Random() < b."""
    odds = (rate * bonus_x10 // 10) * (3 * max_hp - 2 * hp) // (3 * max_hp)
    if status1 & (S1_SLEEP | S1_FREEZE):
        odds *= 2
    if status1 & (S1_POISON | S1_BURN | S1_PARALYSIS | S1_TOXIC):
        odds = odds * 15 // 10
    if odds > 254:
        return 1.0
    if odds <= 0:
        return 0.0                   # unreachable in the game (the lowest rate is 3); the game would divide by zero
    b = 1048560 // isqrt(isqrt(16711680 // odds))
    return (b / 65536) ** 4


def catch_p_ball(ball: str, target: WTarget, env: WEnv, hp: int, status1: int) -> float:
    bonus = ball_bonus_x10(ball, level=target.level, types=target.types, turn=env.turn, underwater=env.underwater,
                           owned=env.owned)
    if bonus is None:
        return 1.0
    return catch_p(target.catch_rate, bonus, target.max_hp, hp, status1)


def expected_balls(ball: str, target: WTarget, env: WEnv, hp: int, status1: int) -> float:
    """E(h) = 1 / catch_p: the expected number of balls at HP `h` (infinity when a throw cannot succeed)."""
    p = catch_p_ball(ball, target, env, hp, status1)
    return float("inf") if p <= 0 else 1.0 / p


def e_gain(ball: str, target: WTarget, env: WEnv, x: int) -> float:
    """Expected BALLS saved by taking `x` HP now: E(hp) - E(hp - x) (D4, revised before the predictions: the damage
    turn spends no ball, so it is not netted). E is taken at max(hp - x, 1), which only matters under NOFLOOR."""
    after = max(target.hp - x, 1)
    gain = expected_balls(ball, target, env, target.hp, target.status1) - \
        expected_balls(ball, target, env, after, target.status1)
    if _fault(FAULT_NETGAIN):
        gain -= 1.0
    return gain


# ============================================================================================================ helpers
def in_scope(kind, kinds) -> bool:
    return kind is not None and kind in tuple(kinds)


def stage2_wanted(calc: bool) -> bool:
    """Stage 2 runs only with POKEBOT_R25_WEAKEN_CALC=1 (the adapter asks this before computing any range)."""
    return bool(calc) or _fault(FAULT_CALCLEAK)


def ctx_matches(env: WEnv, target: WTarget) -> bool:
    return env.ctx_sp == f"{target.species}#{target.dex}"


def _knows(mon, effects) -> list:
    return [m for m in mon.moves if m is not None and m.effect in effects]


def _usable_slots(me: WSelf, effects=None, *, ignore_pp: bool = False) -> list:
    """(slot, move) for our RAW slots with PP > 0 that are not the disabled move."""
    dis = disabled_move(me.disable)
    out = []
    for slot, m in enumerate(me.moves):
        if m is None or (effects is not None and m.effect not in effects):
            continue
        if (m.pp <= 0 and not ignore_pp) or (dis and m.move_id == dis):
            continue
        out.append((slot, m))
    return out


def _uproar_any(target: WTarget, me: WSelf) -> bool:
    return bool((target.status2 | me.status2) & S2_UPROAR)


def _history_caps(memo: "WMemo | None", target: WTarget, env: WEnv) -> tuple[bool, int, int]:
    """(damage cap spent, status tries spent, no-progress turns) from the per-turn history. A decision of THIS turn
    never spends a cap (a re-entry in the same turn repeats its verdict). A no-progress turn is an ACTING turn
    (DAMAGE or STATUS) after which, at the next decision on a LATER turn, the target's HP was not lower and it had
    gained no status."""
    if memo is None:
        return False, 0, 0
    past = sorted(h for h in memo.history if h[0] < env.turn)
    damage_spent = sum(1 for h in past if h[1] == DAMAGE) >= CAP_DAMAGE_TURNS
    tries = sum(1 for h in past if h[1] == STATUS)
    obs = past + [(env.turn, None, target.hp, target.status1)]
    no_progress = 0
    for (_t, verdict, hp, st), (_nt, _nv, nhp, nst) in zip(obs, obs[1:]):
        if verdict not in (DAMAGE, STATUS):
            continue
        if not (nhp < hp or (not (st & S1_ANY) and (nst & S1_ANY))):
            no_progress += 1
    return damage_spent, tries, no_progress


def _throw(env: WEnv, target: WTarget, reason: str) -> WDecision:
    ball = env.ball
    if _fault(FAULT_MASTERBALL):
        held = [name for name, qty in env.bag if qty > 0 and name in BALLS]
        if held:
            ball = max(held, key=lambda n: catch_p_ball(n, target, env, target.hp, target.status1))
    return WDecision(THROW, reason, ball=ball)


def _exact_x(m: WMove, me: WSelf, target: WTarget) -> int | None:
    """Stage 1's exact damage, dispatched on EFFECT (moves.json spells it "Sonicboom"; the calculator "Sonic Boom")."""
    if _fault(FAULT_NAMEDISPATCH):
        key = m.name
        table = dict(zip(CALC_EXACT_NAMES, ("DRAGON_RAGE", "SONICBOOM", "SUPER_FANG", "LEVEL_DAMAGE", "LEVEL_DAMAGE")))
        effect = table.get(key)
    else:
        effect = m.effect if m.effect in EXACT_EFFECTS else None
    if effect == "LEVEL_DAMAGE":
        return me.level
    if effect == "SONICBOOM":
        return 20
    if effect == "DRAGON_RAGE":
        return 40
    if effect == "SUPER_FANG":
        return target.hp // 2 if target.hp >= 2 else 1
    return None


def _self_harm_reason(target: WTarget, me: WSelf, party: WParty, env: WEnv) -> str | None:
    """D4's BINARY no-self-harm rule: None only if the target can hurt ITSELF in NO way for the rest of this battle."""
    for m in _knows(target, SELF_HARM_EFFECTS):
        return f"self-harm:{m.effect}"
    if "Ghost" in target.types:
        for m in _knows(target, {"CURSE"}):
            return "self-harm:GHOST_CURSE"
    for m in _knows(target, CALLING_EFFECTS):
        return f"self-harm:{m.effect}"
    if not _fault(FAULT_NOENCORE) and _knows(target, {"ENCORE"}):
        return "encore-knower"
    for m in _knows(target, ACQUIRE_EFFECTS):
        return f"acquires:{m.effect}"
    # PD3 (the adversarial pass): a confusion berry (Figy, Wiki, Mago, Aguav, Iapapa: hold effects confuse_*) fires at
    # half HP, where our hit leaves it, and can confuse it; a confused self-hit can KO.
    if target.item_effect.startswith("confuse_"):
        return f"self-harm:confusion-berry:{target.item}"
    sand_immune = bool({"Rock", "Ground", "Steel"} & set(target.types)) or target.ability == "Sand Veil"
    hail_immune = "Ice" in target.types
    if _knows(target, {"SANDSTORM"}) and not sand_immune:
        return "weather-move:SANDSTORM"
    if _knows(target, {"HAIL"}) and not hail_immune:
        return "weather-move:HAIL"
    horizon = PRESSURE_FACTOR * (env.usable_balls + HORIZON_SLACK)
    total_pp = sum(m.pp for m in target.moves if m is not None)
    if total_pp <= horizon:
        return f"struggle-pp:{total_pp}<={horizon}"
    # the weather IN EFFECT, whether or not Cloud Nine / Air Lock is on the field (the suppressor may leave)
    if env.weather & WEATHER_SAND and not sand_immune:
        return "weather:sandstorm"
    if env.weather & WEATHER_HAIL and not hail_immune:
        return "weather:hail"
    subjects = (me.ability,) if _fault(FAULT_ACTIVEONLY) else tuple(party.abilities)
    if "Trace" in subjects:
        # PD1 (the adversarial pass; a real KO path): a Trace member that faint-switches in copies the TARGET's live
        # ability (battle_util.c:2561-2566, :3003-3043), e.g. its Rough Skin, which then chips the target every time
        # it makes contact on a throw turn. So the target's own ability is a subject too.
        subjects = subjects + (target.ability,)
    contact = any(m is not None and m.contact for m in target.moves)
    drain = bool(_knows(target, DRAIN_EFFECTS))
    for ab in subjects:
        if ab in CONTACT_RETALIATORS and contact:
            return f"retaliation:{ab}"
        if ab == "Liquid Ooze" and drain:
            return "retaliation:Liquid Ooze"
        if ab == "Synchronize":
            return "retaliation:Synchronize"
        # PD4 (the adversarial pass): a faint-switch to a Sand Stream member starts a sandstorm that chips a target
        # that is not sand-immune on every later turn
        if ab == "Sand Stream" and not sand_immune:
            return "retaliation:Sand Stream"
    return None


def _stage2_divergence(target: WTarget, me: WSelf, env: WEnv, m: WMove) -> str | None:
    """Step 11's PERSISTENT known divergences of the calculator (dmgcalc11 D11; audit_damage_calc `_before_reasons`):
    while one holds, the calculator's bound is not trusted and stage 2 does no damage."""
    if me.ability == "Guts" and me.status1 & S1_BURN:
        return "divergence:guts-burn"
    if target.ability == "Marvel Scale" and ((target.status1 | me.status1) & S1_ANY):
        return "divergence:marvel-scale"
    if me.flash_fire:
        return "divergence:flash-fire"
    if me.status3 & S3_CHARGED_UP:
        return "divergence:charge"
    if env.badge7 and (m.type in SPECIAL_TYPES or m.effect == "HIDDEN_POWER"):
        return "divergence:badge7-special"
    if me.ability != me.species_ability or target.ability != target.species_ability:
        return "divergence:ability-not-species"
    return None


def _damage(target: WTarget, me: WSelf, party: WParty, env: WEnv, damage_spent: bool) -> tuple:
    """(WDecision | None, reason). Stage 1 (exact damage) first, then stage 2 (the calculator's bound, CALC only)."""
    if damage_spent:
        return None, "damage-cap"
    harm = _self_harm_reason(target, me, party, env)
    if harm is not None:
        return None, harm
    foresight = bool(target.status2 & S2_FORESIGHT)
    rejected: list = []
    admissible: list = []
    for slot, m in _usable_slots(me, ignore_pp=_fault(FAULT_NOPP)):
        x = _exact_x(m, me, target)
        if x is None:
            continue
        immune, se, nve = type_effect(m.type, target.types, foresight)
        if m.name in env.banned:          # W12-N1 (the build review): banned_moves binds DAMAGE as it binds STATUS
            rejected.append(f"banned@{slot}")
            continue
        if immune:
            rejected.append(f"immune@{slot}")
            continue
        if target.ability == "Wonder Guard" and m.power and (not se or nve):
            rejected.append(f"wonder-guard@{slot}")
            continue
        if not target.hp * 2 > target.max_hp:
            rejected.append(f"half@{slot}")
            continue
        if not _fault(FAULT_NOFLOOR) and not target.hp - x >= 1:
            rejected.append(f"floor@{slot}")
            continue
        if not x * 100 >= PROGRESS_PCT * target.max_hp:
            rejected.append(f"progress@{slot}")
            continue
        gain = e_gain(env.ball, target, env, x)
        if not gain >= EGAIN_MIN:
            rejected.append(f"egain@{slot}")
            continue
        admissible.append((x, -slot, slot, m))
    if admissible:
        x, _neg, slot, m = max(admissible)
        return WDecision(DAMAGE, f"stage1:{m.effect}", slot=slot, move=m.name, stage=1, x=x), ""
    if stage2_wanted(env.calc):
        for slot, m in _usable_slots(me, TIER_A):
            if m.effect in STAGE2_EXCLUDED:
                rejected.append(f"recharge@{slot}")
                continue
            if m.move_id == MOVE_STRUGGLE or slot >= len(env.calc_ranges) or env.calc_ranges[slot] is None:
                continue
            # W12-N1 (the build review): banned_moves binds stage 2 as it binds stage 1 and STATUS
            if m.name in env.banned:
                rejected.append(f"banned@{slot}")
                continue
            div = _stage2_divergence(target, me, env, m)
            if div is not None:
                rejected.append(f"{div}@{slot}")
                continue
            lo, crit_max = env.calc_ranges[slot]
            ub = (crit_max * 11 + 9) // 10 + WEAKEN_MARGIN
            if not target.hp * 2 > target.max_hp:
                rejected.append(f"half@{slot}")
                continue
            if not target.hp - ub >= 1:
                rejected.append(f"bound@{slot}")
                continue
            if not lo * 100 >= PROGRESS_PCT * target.max_hp:
                rejected.append(f"progress@{slot}")
                continue
            if not e_gain(env.ball, target, env, lo) >= EGAIN_MIN:
                rejected.append(f"egain@{slot}")
                continue
            admissible.append((lo, -slot, slot, m))
        if admissible:
            lo, _neg, slot, m = max(admissible)
            return WDecision(DAMAGE, f"stage2:{m.effect}", slot=slot, move=m.name, stage=2, x=lo), ""
    return None, (",".join(rejected) if rejected else "no-damage-move")


def _status(target: WTarget, me: WSelf, env: WEnv, tries: int) -> tuple:
    """(WDecision | None, reason): sleep over paralysis, at most CAP_STATUS_TRIES tries per battle."""
    if tries >= CAP_STATUS_TRIES:
        return None, "status-cap"
    if taunt_timer(me.disable) > 0:
        return None, "taunt"
    if target.status2 & S2_SUBSTITUTE:
        return None, "substitute"
    if target.status1 & S1_ANY:
        return None, "has-status"
    if env.side_foe & SIDE_SAFEGUARD or env.safeguard_timer > 0:
        return None, "safeguard"
    if _knows(target, {"MAGIC_COAT"}):
        return None, "magic-coat"
    foresight = bool(target.status2 & S2_FORESIGHT)
    sleep, para, rejected = [], [], []
    for slot, m in _usable_slots(me, {SLEEP_EFFECT, PARALYZE_EFFECT}):
        if m.name in env.banned:
            rejected.append(f"banned@{slot}")
            continue
        if m.sound and target.ability == "Soundproof":
            rejected.append(f"soundproof@{slot}")
            continue
        if m.effect == SLEEP_EFFECT:
            if _uproar_any(target, me):
                rejected.append(f"uproar@{slot}")
                continue
            if target.ability in ("Insomnia", "Vital Spirit"):
                rejected.append(f"insomnia@{slot}")
                continue
            sleep.append((slot, m))
        else:
            if target.ability == "Limber":
                rejected.append(f"limber@{slot}")
                continue
            if type_effect(m.type, target.types, foresight)[0]:
                rejected.append(f"immune@{slot}")
                continue
            if target.ability == "Synchronize":
                rejected.append(f"synchronize@{slot}")
                continue
            para.append((slot, m))
    for group in (sleep, para):
        if group:
            slot, m = group[0]
            return WDecision(STATUS, f"status:{m.effect}", slot=slot, move=m.name), ""
    return None, (",".join(rejected) if rejected else "no-status-move")


# ========================================================================================================= the decision
def decide_weaken_turn(target: WTarget, me: WSelf, party: WParty, env: WEnv, memo: "WMemo | None" = None) -> WDecision:
    """ONE turn's verdict (D4; the first match wins): DEFER, then THROW-ONLY, then DAMAGE (stage 1, then stage 2),
    then STATUS, else THROW."""
    # ---- DEFER: the parent decides, exactly as with the flag off
    if env.flag not in ("observe", "1"):
        return WDecision(DEFER, "off")
    if not in_scope(env.kind, env.kinds):
        return WDecision(DEFER, "kind")
    if env.read_error:
        return WDecision(DEFER, f"read:{env.read_error}")
    if memo is None:
        if not ctx_matches(env, target):
            return WDecision(DEFER, "context")
    else:
        if not memo.ctx_ok:
            return WDecision(DEFER, "context")
        if _fault(FAULT_SPECIESID):
            if memo.species_id != target.species_id:
                return WDecision(DEFER, "pid")
        elif memo.pid != target.pid:
            return WDecision(DEFER, "pid")
    if env.battle_flags & NON_SINGLE_WILD:
        return WDecision(DEFER, f"battle-type:{env.battle_flags & NON_SINGLE_WILD:#x}")
    if me.item_effect == "choice_band":
        return WDecision(DEFER, "choice")
    if env.ball is None:
        return WDecision(DEFER, "no-ball")
    # ---- THROW-ONLY
    if memo is not None and memo.species_id != target.species_id:
        return _throw(env, target, "transformed")
    if encored_move(me.disable) or encore_timer(me.disable):
        return _throw(env, target, "encore-on-us")
    if me.status2 & S2_TORMENT:
        return _throw(env, target, "torment")
    if disabled_move(me.disable) or disable_timer(me.disable):
        return _throw(env, target, "disabled")
    if target.status3 & S3_IMPRISONED_OTHERS:
        return _throw(env, target, "imprison")
    if target.status3 & S3_SEMI_INVULNERABLE:
        return _throw(env, target, "semi-invulnerable")
    if target.status2 & S2_SUBSTITUTE:
        return _throw(env, target, "substitute")
    if target.status2 & S2_CONFUSION:
        return _throw(env, target, "confused")
    if target.status1 & (S1_POISON | S1_BURN | S1_TOXIC):
        return _throw(env, target, "ticking:status1")
    if target.status2 & (S2_WRAPPED | S2_CURSED | S2_NIGHTMARE):
        return _throw(env, target, "ticking:status2")
    if target.status3 & S3_LEECHSEED:
        return _throw(env, target, "ticking:leech-seed")
    if env.side_foe & SIDE_FUTUREATTACK:
        return _throw(env, target, "ticking:future-sight")
    if _knows(target, {"EXPLOSION"}) and "Damp" not in (me.ability, target.ability):
        return _throw(env, target, "explosion")
    for m in _knows(target, ENDER_EFFECTS):
        return _throw(env, target, f"ender:{m.effect}")
    for m in _knows(target, CALLING_EFFECTS):
        return _throw(env, target, f"calling:{m.effect}")
    if catch_p_ball(env.ball, target, env, target.hp, target.status1) >= ODDS_THROW_ONLY:
        return _throw(env, target, "odds")
    damage_spent, tries, no_progress = _history_caps(memo, target, env)
    if no_progress >= CAP_NO_PROGRESS:
        return _throw(env, target, "no-progress")
    # ---- DAMAGE (damage is lasting, sleep wears off: damage before status [review N1])
    decision, dmg_reason = _damage(target, me, party, env, damage_spent)
    if decision is not None:
        return decision
    # ---- STATUS
    decision, st_reason = _status(target, me, env, tries)
    if decision is not None:
        return decision
    return _throw(env, target, f"dmg:{dmg_reason}|st:{st_reason}")


def remember(memo: "WMemo | None", target: WTarget, env: WEnv, decision: WDecision) -> WMemo:
    """The next per-battle memo: at the battle's FIRST decision, the target's identity (PID, species) and whether the
    mode's context named it; then the FIRST decision of each turn."""
    if memo is None:
        memo = WMemo(pid=target.pid, species_id=target.species_id, ctx_ok=ctx_matches(env, target))
    if any(h[0] == env.turn for h in memo.history):
        return memo
    return WMemo(memo.pid, memo.species_id, memo.ctx_ok,
                 memo.history + ((env.turn, decision.verdict, target.hp, target.status1),))


# ============================================================================================================ replay
def _plain(obj):
    if isinstance(obj, bytes):
        return {"__bytes__": obj.hex()}
    if isinstance(obj, (list, tuple)):
        return [_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def snapshot_json(target: WTarget, me: WSelf, party: WParty, env: WEnv, memo: "WMemo | None") -> str:
    """Everything `decide_weaken_turn` read, as one compact JSON string (the `[WEAKEN]` lines' `snap=`), so a grader can
    REPLAY a logged verdict (a determinism check, never a replication)."""
    return json.dumps(_plain({"target": asdict(target), "me": asdict(me), "party": asdict(party), "env": asdict(env),
                              "memo": None if memo is None else asdict(memo)}), separators=(",", ":"),
                      ensure_ascii=True)


def _unplain(obj):
    if isinstance(obj, dict) and set(obj) == {"__bytes__"}:
        return bytes.fromhex(obj["__bytes__"])
    if isinstance(obj, list):
        return tuple(_unplain(x) for x in obj)
    if isinstance(obj, dict):
        return {k: _unplain(v) for k, v in obj.items()}
    return obj


def snapshot_from_json(text: str) -> tuple:
    """The inverse of `snapshot_json`: (target, me, party, env, memo)."""
    raw = _unplain(json.loads(text))

    def moves(ms):
        return tuple(None if m is None else WMove(**m) for m in ms)

    t = dict(raw["target"])
    t["moves"] = moves(t["moves"])
    s = dict(raw["me"])
    s["moves"] = moves(s["moves"])
    memo = raw["memo"]
    return (WTarget(**t), WSelf(**s), WParty(**raw["party"]), WEnv(**raw["env"]),
            None if memo is None else WMemo(**memo))


__all__ = ["WMove", "WTarget", "WSelf", "WParty", "WEnv", "WMemo", "WDecision", "DAMAGE", "STATUS", "THROW", "DEFER",
           "catch_p", "ball_bonus_x10", "catch_p_ball", "expected_balls", "e_gain", "decide_weaken_turn", "remember",
           "in_scope", "stage2_wanted", "snapshot_json", "snapshot_from_json"]
