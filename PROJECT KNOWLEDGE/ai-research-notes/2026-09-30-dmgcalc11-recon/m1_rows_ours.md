> ⚠ A NOTE (step 11 prediction support, 2026-09-30). See ../2026-09-30-dmgcalc11-PREDICTIONS.md.

> Measured by running the REAL calculator offline (a pin of current behaviour).

# M1a: what OUR calculator returns (a pin of current behaviour)

Function measured: `BattleStrategyUtil.calculate_move_damage_range` in
`C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/modules/battle_strategies/_util.py` (worktree HEAD `22867e74`).
It was run offline with no emulator, on Python 3.12. The script asserts that the imported `_util` really is that file.

## Scripts
- `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/m1_ours/pin_ours.py`
  is the pin. Run it with `PYTHONUTF8=1 py -3.12 -W error::DeprecationWarning pin_ours.py`.
  It writes `pin_ours_results.json` beside itself, recording the full build of every row.
- `.../m1_ours/fault_side_assert.py` is a fault test of the side assertion (see below).
- No repository file was changed. `git status` in the worktree matches the state before the run: the two
  modifications it shows (`party_accounting_ledger.jsonl`, `magma_1f_fail.ss1`) were already there.

## How each object was built
- **BattlePokemon.** Each one is a REAL `BattlePokemon`, taken from `BattleState.battling_pokemon[0]` (ours) and
  `[1]` (foe). The state is built from hand-packed 0x58-byte records laid out per pret/pokeemerald
  `include/pokemon.h` `struct BattlePokemon` (fetched with `gh api`). The fields are:
  - species at 0x00 and the five battle stats at 0x02..0x0A;
  - `moves[0]` = the row's move, with its PP at 0x24;
  - the IV word at 0x14 (hp/atk/def/spe/spA/spD in 5-bit fields, with isEgg at bit 30 and abilityNum at bit 31);
  - `statStages` all 6 (stage 0);
  - ability id at 0x20, and type1/type2 at 0x21/0x22 set by id, with type2 = type1 for a mono-type as the ROM does;
  - HP at 0x28 and maxHP at 0x2C;
  - level at 0x2A;
  - item 0 (no held item);
  - status1 at 0x4C (POISON = bit 3, BURN = bit 4);
  - status2 = 0.
- **BattleState.** It is `BattleState(...)` with:
  - battle type 0 (a single battle), battler count 2, absent flags 0 and party order `01 23 45`;
  - `gStatuses3` 16 bytes, with STATUS3_CHARGED_UP (bit 9) on battler 0 where a row says Charge;
  - `gSideTimers` 24 bytes, with the foe's reflect timer (byte 12) = 5 for B-BB;
  - `gBattleWeather` = 1 (B_WEATHER_RAIN_TEMPORARY) for B-KI111, else 0;
  - disable structs all zero.
- **Abilities.** Our `BattlePokemon.ability` IGNORES byte 0x20: it returns `species.abilities[abilityNum]`. So each
  species was chosen to carry the intended ability. Byte 0x20 was set to match it, and the script asserts
  `ability.index == byte 0x20` for both battlers. The species were:
  - Milotic for Marvel Scale;
  - Rattata with abilityNum 1 for Guts;
  - otherwise species with inert abilities (Magikarp Swift Swim, Zigzagoon Pickup, Hitmonlee Limber, Pikachu
    Static, Whiscash Oblivious, Poochyena/Rattata Run Away, Tangela Chlorophyll, Abra Synchronize, Shuppet Insomnia,
    Wingull/Sableye/Skarmory Keen Eye, Magnemite Magnet Pull, Aerodactyl Rock Head).
  None of those has an ability that our function tests (Levitate, Wonder Guard, Soundproof, Volt/Water Absorb,
  Flash Fire, Thick Fat, Marvel Scale, Huge/Pure Power, Hustle, Guts, Plus/Minus, or the pinch abilities).
  The types come from bytes 0x21/0x22, not from the species.
- **Stats.** Every stat is 100 unless the row says otherwise. Our attacker has HP 150/150 (full, so no pinch
  ability can trigger). The defender has HP 200/200 and is L50. The attacker is L50, or L30 in the fixed-damage rows.
- **Moves** come from `modules.pokemon.get_move_by_name`. There is no `modules/moves.py`; `Move` lives in
  `modules.pokemon`. The data spellings are `Sonicboom`, `Psywave`, `Solarbeam` and `Mud-slap` (lower-case s).
  - "A Fighting move" in D-A1 and D-O1 is Karate Chop (Fighting, bp 50). It does not collide with any name our
    function special-cases.
  - The Group B moves read from the data are:
    - Tackle (Normal 35)
    - Quick Attack (40)
    - Brick Break (Fighting 75)
    - Water Gun (40)
    - Solarbeam (Grass 120)
    - Struggle (Normal 50)
    - Hidden Power (Normal, bp 1)
    - Sonicboom (Normal, bp 1)
    - Psywave (Psychic, bp 1)
    - Night Shade (Ghost, bp 1)
    - Seismic Toss (Fighting, bp 1)
    - Super Fang (Normal, bp 1)
- **Badges.** `modules.battle_strategies._util.get_event_flag` is patched per row with a recorder that returns the
  row's flags and False for everything else. Every Group B row queried BADGE01/05/07/08. A control run showed the
  patch takes effect: BADGE01 on Tackle moved (21, 25) to (22, 27).
- **Group D.** `BattleStrategyUtil._calculate_base_move_damage` is patched to return the row's B, then restored in
  `finally`. The script asserts that it was called exactly once with the row's `is_critical_hit`.
  `calculate_move_damage_range` was then called for real, with `is_critical_hit` as the row says.
- **Side check.** Before every computation the script calls `own_side.__contains__` and `opponent.__contains__`
  directly on the attacker and the defender. It requires each result to be exactly `True` or `False`, never
  `NotImplemented`. It then asserts that the attacker is on its intended side and the defender is on the other.
  The two records must also differ, because side membership is decided by record equality.
  - The fault test shows the assertion fires on swapped battlers and on a wrong side argument.
  - It also confirms the hazard: `"not a mon" in own_side` evaluates to `True`, because `__contains__` returns
    `NotImplemented`.
- **Attacker in B-KI110** is the FOE (battler 1); the defender is ours (battler 0).

## Per-row outputs: ours = (min, max), exactly as `DamageRange` returns them

| Row | Build (attacker vs defender) | ours (min, max) |
|---|---|---|
| D-A1 | Hitmonlee [Fighting] Karate Chop vs [Normal, Rock]; B=3; crit | (27, 32) |
| D-A2 | Pikachu [Electric] Spark, CHARGED vs [Water, Flying]; B=3; crit | (54, 64) |
| D-A3 | Whiscash [Water, Ground] Mud-slap vs [Electric, Steel]; B=5; crit | (47, 56) |
| D-N1 | Poochyena [Dark] Bite vs [Dark, Ghost]; B=5 | (5, 6) |
| D-N2 | Magikarp [Water] Signal Beam vs [Steel, Flying]; B=2 | (1, 0) |
| D-O1 | Magikarp [Water] Karate Chop vs [Rock, Flying]; B=3 | (2, 3) |
| B-MS1 | Magikarp [Water] Atk100 healthy Tackle vs Milotic [Water] Marvel Scale Def100 BURNED | (14, 17) |
| B-MS2 | Magikarp [Water] Atk100 POISONED Tackle vs Milotic [Water] Marvel Scale Def100 healthy | (10, 12) |
| B-GUTS | Rattata [Normal] Guts Atk100 BURNED Quick Attack vs Magikarp [Water] Def100 | (18, 22) |
| B-BB | Hitmonlee [Fighting] Atk100 Brick Break vs Zigzagoon [Normal] Def100, foe Reflect 5 | (45, 54) |
| B-KI110 (BADGE07 set, BADGE08 clear) | FOE Magikarp [Water] SpA100 Water Gun vs OUR Poochyena [Dark] SpD100 | (23, 28) |
| B-KI110 (BADGE08 set, BADGE07 clear) | same | (22, 27) |
| B-KI111 | Tangela [Grass] SpA100 Solarbeam vs Magikarp [Water] SpD100, RAIN | (137, 162) |
| B-STR | Zigzagoon [Normal] Atk100 Struggle vs Shuppet [Ghost] Def100 | (1, 0) |
| B-HP | Zigzagoon [Normal] SpA100, all IVs 31, Hidden Power vs Rattata [Normal] SpD100. Our HP reads **Dark, power 70** | (27, 32) |
| B-HPC | Zigzagoon [Normal] SpA100, IVs HP31 Atk31 Def31 Spe31 **SpA30** SpD31, CHARGED, vs Magikarp [Water] SpD100. Our HP reads **Electric, power 70** | (108, 128) |
| B-SONIC | Zigzagoon [Normal] L30 Sonicboom vs Rattata [Normal] HP200 (all stats 100) | (3, 4) |
| B-PSY | Abra [Psychic] L30 Psywave vs Rattata [Normal] HP200 (all stats 100) | (2, 3) |
| B-NS | Shuppet [Ghost] L30 Night Shade vs Rattata [Normal] HP200 | (30, 30) |
| B-ST | Hitmonlee [Fighting] L30 Seismic Toss vs Shuppet [Ghost] HP200 | (30, 30) |
| B-SF | Zigzagoon [Normal] L30 Super Fang vs Shuppet [Ghost] HP 200/200 | (100, 100) |

I checked every row by hand against the function's code, and each value is what its code path produces. Some of
the reasons are pinned behaviour, not claims about the game:
- **D-N2 and B-STR** return min > max, i.e. (1, 0). The `max(1, ...)` floor is applied to min only, after a
  type multiplier drove damage to 0.
- **B-MS1 and B-MS2**: Marvel Scale keys on the ATTACKER's status.
- **B-GUTS**: the burn halving still applies under Guts.
- **B-BB**: Reflect halves Brick Break.
- **B-KI110**: BADGE07 is skipped for a foe attacker, and BADGE08 applies to our defender.
- **B-KI111**: rain does not halve the move, because the name check is `"Solar Beam"` and the data says `Solarbeam`.
- **B-SONIC and B-PSY**: the name checks `"Sonic Boom"` and `"Psy Wave"` miss the data spellings. Both moves fall
  through to the generic formula with bp 1.
- **B-NS**: Night Shade into a Normal type still returns the level. The name-return comes after the type
  multiplier.

## Rows that could not be built fully faithfully, and why
- **B-SONIC and B-PSY: the spec gives no Atk/Def/SpA/SpD.** The game ignores those stats for these moves, but our
  function does not: it runs them through the generic formula with bp 1. The pin above uses 100 everywhere. A sweep
  over attacker Atk/SpA against defender Def/SpD gave:

  | Atk/SpA vs Def/SpD | 50/100, 100/100, 200/100, 100/50, 100/200 | 300/30 |
  |---|---|---|
  | B-SONIC | (3, 4) | (5, 6) |
  | B-PSY | (2, 3) | (5, 6) |

  So the value is stable across ordinary stats but not constant. B-NS, B-ST and B-SF are stat-independent (constant
  across the whole sweep).
- **B-SF: "HP 200 (current)" leaves max HP open.** I set max HP = 200. Our function reads only `current_hp`.
- **Abilities cannot be set by id alone.** Our accessor ignores byte 0x20, so each ability is expressed through the
  species and abilityNum, with 0x20 kept consistent with them. A row whose intended ability differed from the
  species' ability could not be built. None of these rows needed that.
- **Unspecified inputs.** Defender level and the attacker's HP were not given. I used defender L50 and attacker
  HP 150/150; neither reaches the calculator on these rows. The battle type is 0 (single, wild-style); none of its
  flags feed the calculator.
- **Charge-turn modelling.** "The damage turn" in B-KI111 has no counterpart in our function, which has no concept
  of a two-turn move's turns. The row is computed as a single call with rain active.
- **Gen 3 category** is decided by our `Type.is_physical`: type index < 9. Hidden Power's category follows the rolled
  type (Dark and Electric are special), because `_get_move_type_and_power` substitutes the type before the branch.
- **Species data order.** `species.json` type lists are not in ROM order (e.g. Whiscash is listed ['Ground', 'Water']).
  This is irrelevant here, because `BattlePokemon.types` reads bytes 0x21/0x22, which I set in the spec's ROM order.


## Appendix: the pin script (m1_ours/pin_ours.py)

```python
# -*- coding: utf-8 -*-
"""M1a: pin what OUR calculate_move_damage_range returns for every row in m1_rowspec.md.

Offline, no emulator. Every battler is a REAL BattlePokemon produced by a REAL BattleState's
`battling_pokemon` from hand-built 0x58-byte gBattleMons records (layout: pret/pokeemerald
include/pokemon.h struct BattlePokemon). Nothing in the repository is modified; the only patches
are in-process: `modules.battle_strategies._util.get_event_flag` (per row) and, for Group D only,
`BattleStrategyUtil._calculate_base_move_damage` (returns the row's B).

    PYTHONUTF8=1 py -3.12 pin_ours.py
"""
import json
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SANDBOX = r"C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot"
sys.path.insert(0, SANDBOX)

import modules.battle_strategies._util as U  # noqa: E402
from modules.battle_state import BattlePokemon, BattleState, TemporaryStatus, Weather  # noqa: E402
from modules.battle_strategies._util import BattleStrategyUtil  # noqa: E402
from modules.pokemon import (  # noqa: E402
    StatusCondition,
    get_move_by_name,
    get_species_by_name,
    get_type_by_name,
)

assert U.__file__.replace("\\", "/").startswith(SANDBOX), U.__file__

STATUS1_POISON = 1 << 3
STATUS1_BURN = 1 << 4
STATUS3_CHARGED_UP = 1 << 9
B_WEATHER_RAIN_TEMPORARY = 1 << 0


def ivs_word(hp=0, atk=0, df=0, spe=0, spa=0, spd=0, is_egg=0, ability_num=0) -> int:
    return (
        (hp & 31)
        | (atk & 31) << 5
        | (df & 31) << 10
        | (spe & 31) << 15
        | (spa & 31) << 20
        | (spd & 31) << 25
        | (is_egg & 1) << 30
        | (ability_num & 1) << 31
    )


def mon_record(
    species: str,
    types: tuple[str, str | None],
    level: int,
    atk=100,
    df=100,
    spe=100,
    spa=100,
    spd=100,
    hp=None,
    max_hp=None,
    ivs=None,
    ability_num=0,
    status1=0,
    move: str | None = None,
) -> bytes:
    """One 0x58-byte gBattleMons entry (struct BattlePokemon)."""
    sp = get_species_by_name(species)
    ability = sp.abilities[1 if (ability_num and len(sp.abilities) > 1) else 0]
    t1 = get_type_by_name(types[0]).index
    t2 = get_type_by_name(types[1]).index if types[1] else t1  # the ROM repeats type1 for a mono-type
    if max_hp is None:
        max_hp = 150
    if hp is None:
        hp = max_hp
    iv = ivs or {}
    rec = bytearray(0x58)
    struct.pack_into("<H", rec, 0x00, sp.index)
    struct.pack_into("<HHHHH", rec, 0x02, atk, df, spe, spa, spd)
    moves = [get_move_by_name(move).index if move else 0, 0, 0, 0]
    struct.pack_into("<HHHH", rec, 0x0C, *moves)
    struct.pack_into("<I", rec, 0x14, ivs_word(ability_num=ability_num, **iv))
    for i in range(8):
        rec[0x18 + i] = 6  # statStages: 6 = stage 0
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
    struct.pack_into("<I", rec, 0x50, 0)  # status2
    return bytes(rec)


def make_state(ours: bytes, foe: bytes, ours_status3=0, foe_status3=0, foe_reflect=0, ours_reflect=0, weather=0):
    battlers = ours + foe + bytes(0x58 * 2)  # gBattleMons[4]; slots 2/3 unused in a single battle
    status3 = struct.pack("<IIII", ours_status3, foe_status3, 0, 0)
    side_timers = bytearray(24)  # struct SideTimer[2], 12 bytes each
    side_timers[0] = ours_reflect
    side_timers[1] = 0 if ours_reflect else 0
    side_timers[12] = foe_reflect
    side_timers[13] = 1 if foe_reflect else 0
    return BattleState(
        battle_type=struct.pack("<I", 0),  # single, wild-style flags (none of these flags feed the calculator)
        side_timers=bytes(side_timers),
        battler_party_indexes=struct.pack("<HHHH", 0, 0, 0, 0),
        battler_party_order=bytes([0x01, 0x23, 0x45]),
        battler_count=2,
        battler=battlers,
        battler_status3=status3,
        battler_disable_structs=bytes(0x1C * 4),
        absent_battler_flags=0,
        current_turn=1,
        weather=weather,
    )


FLAG_LOG: list[str] = []


def set_flags(flags: dict[str, bool]):
    FLAG_LOG.clear()

    def fake_get_event_flag(name):
        FLAG_LOG.append(name)
        return bool(flags.get(name, False))

    U.get_event_flag = fake_get_event_flag


def assert_sides(state: BattleState, attacker: BattlePokemon, defender: BattlePokemon, attacker_side: str):
    own, opp = state.own_side, state.opponent
    assert isinstance(attacker, BattlePokemon) and isinstance(defender, BattlePokemon)
    assert attacker._data != defender._data, "attacker and defender records are identical"
    a_own = own.__contains__(attacker)
    d_own = own.__contains__(defender)
    a_opp = opp.__contains__(attacker)
    d_opp = opp.__contains__(defender)
    for v in (a_own, d_own, a_opp, d_opp):
        assert v is True or v is False, f"__contains__ returned {v!r} (NotImplemented reads True)"
    if attacker_side == "ours":
        assert a_own is True and a_opp is False, "attacker not on OUR side"
        assert d_own is False and d_opp is True, "defender not on the FOE side"
    else:
        assert a_own is False and a_opp is True, "attacker not on the FOE side"
        assert d_own is True and d_opp is False, "defender not on OUR side"


def describe(p: BattlePokemon) -> dict:
    return {
        "species": p.species.name,
        "types": [t.name for t in p.types],
        "ability": p.ability.name,
        "ability_byte_0x20": p.ability_n,
        "L": p.level,
        "stats": dict(atk=p.stats.attack, df=p.stats.defence, spa=p.stats.special_attack, spd=p.stats.special_defence),
        "hp": f"{p.current_hp}/{p.total_hp}",
        "status1": p.status_permanent.name,
        "status3": [s.name for s in p.status_temporary],
        "item": p.held_item,
    }


RESULTS: list[dict] = []


def run_row(row_id, state, move_name, attacker_side="ours", flags=None, crit=False, base_override=None, extra=None):
    set_flags(flags or {})
    b = state.battling_pokemon
    ours, foe = b[0], b[1]
    attacker, defender = (ours, foe) if attacker_side == "ours" else (foe, ours)
    assert_sides(state, attacker, defender, attacker_side)
    assert ours.ability.index == ours.ability_n and foe.ability.index == foe.ability_n
    move = get_move_by_name(move_name)
    util = BattleStrategyUtil(state)

    base_calls = []
    original_base = BattleStrategyUtil._calculate_base_move_damage
    if base_override is not None:

        def fake_base(self, mv, att, dfn, is_critical_hit=False):
            base_calls.append(is_critical_hit)
            return base_override

        BattleStrategyUtil._calculate_base_move_damage = fake_base
    try:
        r = util.calculate_move_damage_range(move, attacker, defender, is_critical_hit=crit)
    finally:
        BattleStrategyUtil._calculate_base_move_damage = original_base
    if base_override is not None:
        assert base_calls == [crit], f"patched base not called exactly once with crit={crit}: {base_calls}"
    out = {
        "row": row_id,
        "move": f"{move.name} (idx {move.index}, {move.type.name}, bp {move.base_power}, effect {move.effect})",
        "attacker_side": attacker_side,
        "attacker": describe(attacker),
        "defender": describe(defender),
        "weather": state.weather.name,
        "foe_reflect": state.opponent.reflect_timer.turns_remaining,
        "flags_set": {k: v for k, v in (flags or {}).items() if v},
        "flags_queried": list(FLAG_LOG),
        "crit": crit,
        "B_given": base_override,
        "ours": (r.min, r.max),
    }
    if extra:
        out.update(extra)
    RESULTS.append(out)
    return r


# ---------------------------------------------------------------- Group D (B given)
D = [
    # row, move, attacker (species, types), defender (species, types), B, crit, charge
    ("D-A1", "Karate Chop", ("Hitmonlee", ("Fighting", None)), ("Zigzagoon", ("Normal", "Rock")), 3, True, False),
    ("D-A2", "Spark", ("Pikachu", ("Electric", None)), ("Wingull", ("Water", "Flying")), 3, True, True),
    ("D-A3", "Mud-slap", ("Whiscash", ("Water", "Ground")), ("Magnemite", ("Electric", "Steel")), 5, True, False),
    ("D-N1", "Bite", ("Poochyena", ("Dark", None)), ("Sableye", ("Dark", "Ghost")), 5, False, False),
    ("D-N2", "Signal Beam", ("Magikarp", ("Water", None)), ("Skarmory", ("Steel", "Flying")), 2, False, False),
    ("D-O1", "Karate Chop", ("Magikarp", ("Water", None)), ("Aerodactyl", ("Rock", "Flying")), 3, False, False),
]
for row, mv, (asp, aty), (dsp, dty), B, crit, charge in D:
    st = make_state(
        mon_record(asp, aty, 50, move=mv),
        mon_record(dsp, dty, 50, max_hp=200),
        ours_status3=STATUS3_CHARGED_UP if charge else 0,
    )
    if charge:
        assert TemporaryStatus.ChargedUp in st.battling_pokemon[0].status_temporary
    run_row(row, st, mv, crit=crit, base_override=B)

# ---------------------------------------------------------------- Group B (full inputs)
# B-MS1: ours healthy Water attacker; foe Marvel Scale, BURNED
st = make_state(
    mon_record("Magikarp", ("Water", None), 50, atk=100, move="Tackle"),
    mon_record("Milotic", ("Water", None), 50, df=100, max_hp=200, status1=STATUS1_BURN),
)
assert st.battling_pokemon[1].status_permanent is StatusCondition.Burn
run_row("B-MS1", st, "Tackle")

# B-MS2: ours POISONED; foe Marvel Scale healthy
st = make_state(
    mon_record("Magikarp", ("Water", None), 50, atk=100, status1=STATUS1_POISON, move="Tackle"),
    mon_record("Milotic", ("Water", None), 50, df=100, max_hp=200),
)
assert st.battling_pokemon[0].status_permanent is StatusCondition.Poison
run_row("B-MS2", st, "Tackle")

# B-GUTS: ours Normal, Guts (Rattata abilityNum 1), BURNED; Quick Attack
st = make_state(
    mon_record("Rattata", ("Normal", None), 50, atk=100, ability_num=1, status1=STATUS1_BURN, move="Quick Attack"),
    mon_record("Magikarp", ("Water", None), 50, df=100, max_hp=200),
)
assert st.battling_pokemon[0].ability.name == "Guts"
run_row("B-GUTS", st, "Quick Attack")

# B-BB: Brick Break into REFLECT on the foe's side
st = make_state(
    mon_record("Hitmonlee", ("Fighting", None), 50, atk=100, move="Brick Break"),
    mon_record("Zigzagoon", ("Normal", None), 50, df=100, max_hp=200),
    foe_reflect=5,
)
assert st.opponent.reflect_timer.turns_remaining == 5 and st.own_side.reflect_timer.turns_remaining == 0
run_row("B-BB", st, "Brick Break")

# B-KI110: the FOE attacks us, Water Gun; two badge arms
for suffix, flags in (("(BADGE07 set, BADGE08 clear)", {"BADGE07_GET": True}), ("(BADGE08 set, BADGE07 clear)", {"BADGE08_GET": True})):
    st = make_state(
        mon_record("Poochyena", ("Dark", None), 50, spd=100, max_hp=200),
        mon_record("Magikarp", ("Water", None), 50, spa=100, move="Water Gun"),
    )
    run_row(f"B-KI110 {suffix}", st, "Water Gun", attacker_side="foe", flags=flags)

# B-KI111: Solarbeam in RAIN
st = make_state(
    mon_record("Tangela", ("Grass", None), 50, spa=100, move="Solarbeam"),
    mon_record("Magikarp", ("Water", None), 50, spd=100, max_hp=200),
    weather=B_WEATHER_RAIN_TEMPORARY,
)
assert st.weather is Weather.Rain
run_row("B-KI111", st, "Solarbeam")

# B-STR: Struggle into a Ghost
st = make_state(
    mon_record("Zigzagoon", ("Normal", None), 50, atk=100, move="Struggle"),
    mon_record("Shuppet", ("Ghost", None), 50, df=100, max_hp=200),
)
run_row("B-STR", st, "Struggle")

# B-HP: Hidden Power, all IVs 31
st = make_state(
    mon_record("Zigzagoon", ("Normal", None), 50, spa=100, move="Hidden Power",
               ivs=dict(hp=31, atk=31, df=31, spe=31, spa=31, spd=31)),
    mon_record("Rattata", ("Normal", None), 50, spd=100, max_hp=200),
)
a = st.battling_pokemon[0]
run_row("B-HP", st, "Hidden Power", extra={"hp_type": a.hidden_power_type.name, "hp_power": a.hidden_power_damage,
                                              "ivs": vars(a.ivs) if hasattr(a.ivs, "__dict__") else str(a.ivs)})

# B-HPC: Hidden Power rolling ELECTRIC (HP31 Atk31 Def31 Spe31 SpA30 SpD31), our side CHARGED
st = make_state(
    mon_record("Zigzagoon", ("Normal", None), 50, spa=100, move="Hidden Power",
               ivs=dict(hp=31, atk=31, df=31, spe=31, spa=30, spd=31)),
    mon_record("Magikarp", ("Water", None), 50, spd=100, max_hp=200),
    ours_status3=STATUS3_CHARGED_UP,
)
a = st.battling_pokemon[0]
assert a.hidden_power_type.name == "Electric", a.hidden_power_type.name
assert TemporaryStatus.ChargedUp in a.status_temporary
run_row("B-HPC", st, "Hidden Power", extra={"hp_type": a.hidden_power_type.name, "hp_power": a.hidden_power_damage,
                                               "ivs": "HP31 Atk31 Def31 Spe31 SpA30 SpD31"})

# L30 fixed-damage rows. The spec gives no Atk/Def/SpA/SpD (the game ignores them); OUR function
# may not, so the primary pin uses 100 everywhere and a sensitivity sweep follows.
L30 = [
    ("B-SONIC", "Sonicboom", ("Zigzagoon", ("Normal", None)), ("Rattata", ("Normal", None))),
    ("B-PSY", "Psywave", ("Abra", ("Psychic", None)), ("Rattata", ("Normal", None))),
    ("B-NS", "Night Shade", ("Shuppet", ("Ghost", None)), ("Rattata", ("Normal", None))),
    ("B-ST", "Seismic Toss", ("Hitmonlee", ("Fighting", None)), ("Shuppet", ("Ghost", None))),
    ("B-SF", "Super Fang", ("Zigzagoon", ("Normal", None)), ("Shuppet", ("Ghost", None))),
]
for row, mv, (asp, aty), (dsp, dty) in L30:
    st = make_state(mon_record(asp, aty, 30, move=mv), mon_record(dsp, dty, 50, max_hp=200, hp=200))
    run_row(row, st, mv)

SENS = []
for row, mv, (asp, aty), (dsp, dty) in L30:
    for s_att, s_def in ((50, 100), (100, 100), (200, 100), (100, 50), (100, 200), (300, 30)):
        st = make_state(
            mon_record(asp, aty, 30, atk=s_att, spa=s_att, move=mv),
            mon_record(dsp, dty, 50, df=s_def, spd=s_def, max_hp=200, hp=200),
        )
        set_flags({})
        b = st.battling_pokemon
        assert_sides(st, b[0], b[1], "ours")
        r = BattleStrategyUtil(st).calculate_move_damage_range(get_move_by_name(mv), b[0], b[1])
        SENS.append((row, s_att, s_def, (r.min, r.max)))
RESULTS.append({"row": "_sensitivity_L30", "sweep": SENS})

# control: the flag patch reaches the function (BADGE01 on our attacker must change B-GUTS-like damage)
st = make_state(mon_record("Zigzagoon", ("Normal", None), 50, atk=100, move="Tackle"),
                mon_record("Rattata", ("Normal", None), 50, df=100, max_hp=200))
b = st.battling_pokemon
set_flags({})
c0 = BattleStrategyUtil(st).calculate_move_damage_range(get_move_by_name("Tackle"), b[0], b[1])
set_flags({"BADGE01_GET": True})
c1 = BattleStrategyUtil(st).calculate_move_damage_range(get_move_by_name("Tackle"), b[0], b[1])
RESULTS.append({"row": "_control_flag_patch", "no_badge": (c0.min, c0.max), "badge01": (c1.min, c1.max)})
assert (c0.min, c0.max) != (c1.min, c1.max), "flag patch did not reach the function"

for r in RESULTS:
    if r["row"].startswith("_"):
        continue
    print(f"{r['row']:<34} ours={r['ours']}")
print()
print("control flag patch:", RESULTS[-1])
print("sensitivity (row, atk/spa, def/spd, ours):")
for s in SENS:
    print("  ", s)

with open(__file__.replace("pin_ours.py", "pin_ours_results.json"), "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=1, default=str)

```
