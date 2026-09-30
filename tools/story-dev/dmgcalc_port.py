"""A PURE, decomp-ordered port of Gen 3's damage arithmetic AFTER the base term — a TEST ORACLE for design v2 step 11
(M1a, `probe_damage_calc_decomp.py`). ⛔ Never imported by production: it exists so the gate can compare OUR calculator
(`sandbox-pokebot/modules/battle_strategies/_util.py`, `calculate_move_damage_range`) against the game's ORDER.

WHY A PORT AND NOT OUR CODE. Our calculator applies STAB and the type chart first and the crit (and Charge) last; the
game applies the crit and Charge first (design D1), walks the type chart in TABLE order rather than defender order (D2),
and floors each type step at 1 (D3). A port written in our order would agree with our calculator and prove nothing, so
this one follows the decomp line by line, and the gate checks it against HAND-DERIVED literals filed before it existed
(`ai-research-notes/2026-09-30-dmgcalc11-PREDICTIONS.md`, derived in `2026-09-30-dmgcalc11-recon/m1_rows_game.md`).

SOURCE. pret/pokeemerald `master` @ f90719c46ce710427cfcae65419a3fa684b34a8a, read with
`gh api -H "Accept: application/vnd.github.raw" repos/pret/pokeemerald/contents/<path>`. Abbreviations in the comments:
BSC = src/battle_script_commands.c, BM = src/battle_main.c, BS1 = data/battle_scripts_1.s, BH = include/battle.h,
BMH = include/battle_main.h, BU = src/battle_util.c, CP = include/constants/pokemon.h,
CB = include/constants/battle.h.

SCOPE (what is NOT modelled, deliberately — the gate's rows and sweep never need it): the base term itself
(`CalculateBaseDamage`, src/pokemon.c; the caller supplies B, "+2 included"); Helping Hand (BSC:1300-1301, a doubles-only
effect: ignored); the target's abilities in `Cmd_typecalc` (Levitate BSC:1375, Wonder Guard after the loop): the caller
uses a neutral defender; Focus Band / Endure / False Swipe in `Cmd_adjustnormaldamage` (BSC:1658+); Substitute.

Types are named as `sandbox-pokebot/modules/data/types.json` names them ("???" is TYPE_MYSTERY).
"""

from __future__ import annotations

from functools import lru_cache

DECOMP_COMMIT = "f90719c46ce710427cfcae65419a3fa684b34a8a"

#: CP:6-23 — the ROM's type ids (TYPE_NORMAL 0 ... TYPE_DARK 17), keyed by the types.json name.
ROM_TYPE_IDS = {
    "Normal": 0, "Fighting": 1, "Flying": 2, "Poison": 3, "Ground": 4, "Rock": 5, "Bug": 6, "Ghost": 7, "Steel": 8,
    "???": 9, "Fire": 10, "Water": 11, "Grass": 12, "Electric": 13, "Psychic": 14, "Ice": 15, "Dragon": 16, "Dark": 17,
}

#: TYPE_FORESIGHT (0xFE, BMH:37): the sentinel row of the table. Rows AFTER it apply only to a target WITHOUT Foresight.
FORESIGHT = "FORESIGHT"

#: gTypeEffectiveness, BM:335-449 (`const u8 gTypeEffectiveness[336]`), transcribed IN TABLE ORDER as
#: (attacking type, defending type, multiplier in tenths: TYPE_MUL_NO_EFFECT 0, _NOT_EFFECTIVE 5, _SUPER_EFFECTIVE 20,
#: BMH:31-34). The TYPE_ENDTABLE terminator (BM:448) is not a row here: iteration ends at the list's end.
#: ⛔ The ORDER is load-bearing: `Cmd_typecalc` applies the rows in this order and floors after each one, so reordering
#: two rows for the same attacking type changes results (D-N1: Dark->Ghost precedes Dark->Dark; D-O1: Fighting->Flying
#: precedes Fighting->Rock).
TYPE_EFFECTIVENESS: list[tuple[str, str, int]] = [
    ("Normal", "Rock", 5),  # BM:337
    ("Normal", "Steel", 5),  # BM:338
    ("Fire", "Fire", 5),  # BM:339
    ("Fire", "Water", 5),  # BM:340
    ("Fire", "Grass", 20),  # BM:341
    ("Fire", "Ice", 20),  # BM:342
    ("Fire", "Bug", 20),  # BM:343
    ("Fire", "Rock", 5),  # BM:344
    ("Fire", "Dragon", 5),  # BM:345
    ("Fire", "Steel", 20),  # BM:346
    ("Water", "Fire", 20),  # BM:347
    ("Water", "Water", 5),  # BM:348
    ("Water", "Grass", 5),  # BM:349
    ("Water", "Ground", 20),  # BM:350
    ("Water", "Rock", 20),  # BM:351
    ("Water", "Dragon", 5),  # BM:352
    ("Electric", "Water", 20),  # BM:353
    ("Electric", "Electric", 5),  # BM:354
    ("Electric", "Grass", 5),  # BM:355
    ("Electric", "Ground", 0),  # BM:356
    ("Electric", "Flying", 20),  # BM:357
    ("Electric", "Dragon", 5),  # BM:358
    ("Grass", "Fire", 5),  # BM:359
    ("Grass", "Water", 20),  # BM:360
    ("Grass", "Grass", 5),  # BM:361
    ("Grass", "Poison", 5),  # BM:362
    ("Grass", "Ground", 20),  # BM:363
    ("Grass", "Flying", 5),  # BM:364
    ("Grass", "Bug", 5),  # BM:365
    ("Grass", "Rock", 20),  # BM:366
    ("Grass", "Dragon", 5),  # BM:367
    ("Grass", "Steel", 5),  # BM:368
    ("Ice", "Water", 5),  # BM:369
    ("Ice", "Grass", 20),  # BM:370
    ("Ice", "Ice", 5),  # BM:371
    ("Ice", "Ground", 20),  # BM:372
    ("Ice", "Flying", 20),  # BM:373
    ("Ice", "Dragon", 20),  # BM:374
    ("Ice", "Steel", 5),  # BM:375
    ("Ice", "Fire", 5),  # BM:376
    ("Fighting", "Normal", 20),  # BM:377
    ("Fighting", "Ice", 20),  # BM:378
    ("Fighting", "Poison", 5),  # BM:379
    ("Fighting", "Flying", 5),  # BM:380
    ("Fighting", "Psychic", 5),  # BM:381
    ("Fighting", "Bug", 5),  # BM:382
    ("Fighting", "Rock", 20),  # BM:383
    ("Fighting", "Dark", 20),  # BM:384
    ("Fighting", "Steel", 20),  # BM:385
    ("Poison", "Grass", 20),  # BM:386
    ("Poison", "Poison", 5),  # BM:387
    ("Poison", "Ground", 5),  # BM:388
    ("Poison", "Rock", 5),  # BM:389
    ("Poison", "Ghost", 5),  # BM:390
    ("Poison", "Steel", 0),  # BM:391
    ("Ground", "Fire", 20),  # BM:392
    ("Ground", "Electric", 20),  # BM:393
    ("Ground", "Grass", 5),  # BM:394
    ("Ground", "Poison", 20),  # BM:395
    ("Ground", "Flying", 0),  # BM:396
    ("Ground", "Bug", 5),  # BM:397
    ("Ground", "Rock", 20),  # BM:398
    ("Ground", "Steel", 20),  # BM:399
    ("Flying", "Electric", 5),  # BM:400
    ("Flying", "Grass", 20),  # BM:401
    ("Flying", "Fighting", 20),  # BM:402
    ("Flying", "Bug", 20),  # BM:403
    ("Flying", "Rock", 5),  # BM:404
    ("Flying", "Steel", 5),  # BM:405
    ("Psychic", "Fighting", 20),  # BM:406
    ("Psychic", "Poison", 20),  # BM:407
    ("Psychic", "Psychic", 5),  # BM:408
    ("Psychic", "Dark", 0),  # BM:409
    ("Psychic", "Steel", 5),  # BM:410
    ("Bug", "Fire", 5),  # BM:411
    ("Bug", "Grass", 20),  # BM:412
    ("Bug", "Fighting", 5),  # BM:413
    ("Bug", "Poison", 5),  # BM:414
    ("Bug", "Flying", 5),  # BM:415
    ("Bug", "Psychic", 20),  # BM:416
    ("Bug", "Ghost", 5),  # BM:417
    ("Bug", "Dark", 20),  # BM:418
    ("Bug", "Steel", 5),  # BM:419
    ("Rock", "Fire", 20),  # BM:420
    ("Rock", "Ice", 20),  # BM:421
    ("Rock", "Fighting", 5),  # BM:422
    ("Rock", "Ground", 5),  # BM:423
    ("Rock", "Flying", 20),  # BM:424
    ("Rock", "Bug", 20),  # BM:425
    ("Rock", "Steel", 5),  # BM:426
    ("Ghost", "Normal", 0),  # BM:427  (BEFORE the sentinel: applies even through Foresight)
    ("Ghost", "Psychic", 20),  # BM:428
    ("Ghost", "Dark", 5),  # BM:429
    ("Ghost", "Steel", 5),  # BM:430
    ("Ghost", "Ghost", 20),  # BM:431
    ("Dragon", "Dragon", 20),  # BM:432
    ("Dragon", "Steel", 5),  # BM:433
    ("Dark", "Fighting", 5),  # BM:434
    ("Dark", "Psychic", 20),  # BM:435
    ("Dark", "Ghost", 20),  # BM:436
    ("Dark", "Dark", 5),  # BM:437
    ("Dark", "Steel", 5),  # BM:438
    ("Steel", "Fire", 5),  # BM:439
    ("Steel", "Water", 5),  # BM:440
    ("Steel", "Electric", 5),  # BM:441
    ("Steel", "Ice", 20),  # BM:442
    ("Steel", "Rock", 20),  # BM:443
    ("Steel", "Steel", 5),  # BM:444
    (FORESIGHT, FORESIGHT, 0),  # BM:445  TYPE_FORESIGHT, TYPE_FORESIGHT, TYPE_MUL_NO_EFFECT
    ("Normal", "Ghost", 0),  # BM:446
    ("Fighting", "Ghost", 0),  # BM:447
]

#: Every type the table names (attacking or defending; the sentinel excluded), in ROM id order. The gate enumerates its
#: move types and its ORDERED defender type pairs from this, never from species.json (whose type lists are not ROM
#: ordered). TYPE_MYSTERY (9) is never named by the table, so it is not here: 17 types.
TABLE_TYPES: tuple[str, ...] = tuple(
    sorted({name for atk, dfn, _ in TYPE_EFFECTIVENESS if atk != FORESIGHT for name in (atk, dfn)},
           key=ROM_TYPE_IDS.__getitem__)
)

#: Cmd_damagecalc's `gBattleScripting.dmgMultiplier`: 1 for every move this port serves (set to 1 per move by
#: HandleAction_UseMove, BU:91-92, and by MoveValuesCleanUp, BSC:3624). Other values belong to moves outside M1's
#: whitelist.
DMG_MULTIPLIER = 1


def charge_applies(charged: bool, listed_type: str, move_type: str) -> bool:
    """BSC:1298: `gStatuses3[attacker] & STATUS3_CHARGED_UP && gBattleMoves[gCurrentMove].type == TYPE_ELECTRIC`.

    It reads the move's LISTED type (the move table), not GET_MOVE_TYPE (BH:458-464). `move_type`, the type the move
    actually rolled (Hidden Power's dynamic type), is accepted and DELIBERATELY NOT READ: Hidden Power is listed Normal,
    so a Hidden Power that rolled Electric is not doubled by Charge (row B-HPC)."""
    return bool(charged) and listed_type == "Electric"


@lru_cache(maxsize=None)
def type_steps(move_type: str, type1: str, type2: str, foresight: bool = False) -> tuple[int, ...]:
    """The multipliers (tenths) `Cmd_typecalc` applies to the damage, IN THE ORDER IT APPLIES THEM (BSC:1386-1406).

    It walks the TABLE, not the defender: for each row whose attacking type is the move's type it checks the target's
    type1 (BSC:1397-1399) and then its type2, the latter only when type2 != type1 (BSC:1400-1403; the ROM repeats type1
    for a mono-type). At the TYPE_FORESIGHT sentinel it stops if the target has Foresight (BSC:1388-1391: `break`), else
    it skips the sentinel and applies the rows after it (BSC:1392-1393)."""
    steps: list[int] = []
    for atk, dfn, mul in TYPE_EFFECTIVENESS:
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


def _defender_pair(defender_types_rom) -> tuple[str, str]:
    """(type1, type2) as gBattleMons holds them; a one-element sequence is a mono-type, which the ROM stores twice."""
    types = tuple(defender_types_rom)
    return (types[0], types[0]) if len(types) == 1 else (types[0], types[1])


def after_base_many(Bs, move_type: str, attacker_types, defender_types_rom, crit: bool, charge_listed_electric: bool,
                    struggle: bool = False, foresight: bool = False) -> tuple[list[int], list[int]]:
    """The game's [85%, 100%] damage for each base B in `Bs` (the value CalculateBaseDamage returns, +2 included).

    Returns the columns (mins, maxs). `after_base` is this with one B; the gate's sweep calls this directly so the
    per-combination work (the table walk) is done once per combination, not once per B.

      `charge_listed_electric` — the result of `charge_applies(...)` (the attacker is charged AND the move is LISTED
      Electric). `struggle` — the move is MOVE_STRUGGLE. `attacker_types` — gBattleMons types[0..1] (a mono-type may be
      given once). `defender_types_rom` — the target's (type1, type2) in ROM order."""
    type1, type2 = _defender_pair(defender_types_rom)
    if struggle:
        # BSC:1360-1364: `if (gCurrentMove == MOVE_STRUGGLE) { gBattlescriptCurrInstr++; return; }` — typecalc returns
        # at once: no STAB and no type chart (Struggle hits a Ghost for full damage). damagecalc has already run.
        stab = False
        steps: tuple[int, ...] = ()
    else:
        # BSC:1369: IS_BATTLER_OF_TYPE (BH:471) — type1 OR type2 of the attacker. The type is GET_MOVE_TYPE (BSC:1366),
        # i.e. the ROLLED type for Hidden Power, which the caller passes as `move_type`.
        stab = move_type in tuple(attacker_types)
        steps = type_steps(move_type, type1, type2, foresight)
    # ModulateDmgByType with TYPE_MUL_NO_EFFECT sets MOVE_RESULT_DOESNT_AFFECT_FOE (BSC:1329-1330). That flag is part of
    # MOVE_RESULT_NO_EFFECT (CB:228), and Cmd_healthbarupdate (BSC:1812) and Cmd_datahpupdate (BSC:1862) then skip the
    # HP change: the hit DEALS 0 even when a later row floored gBattleMoveDamage back to 1 (e.g. Ground vs Flying/Rock:
    # Ground->Flying 0 at BM:396, then Ground->Rock 20 at BM:398 makes 0 into 1 via BSC:1324-1325).
    no_effect = 0 in steps
    crit_mul = 2 if crit else 1  # gCritMultiplier: 2 on a crit, 1 otherwise (Cmd_critcalc, BSC:1283-1285)
    mins: list[int] = []
    maxs: list[int] = []
    for B in Bs:
        # --- Cmd_damagecalc (BSC:1290-1304): the crit and Charge come FIRST, before STAB and the type chart (D1)
        d = B * crit_mul * DMG_MULTIPLIER  # BSC:1296
        if charge_listed_electric:  # BSC:1298-1299
            d *= 2
        # --- Cmd_typecalc (BSC:1355-1424)
        if stab:  # BSC:1371-1372: `* 15` then `/ 10`, two statements
            d = d * 15 // 10
        for mul in steps:  # ModulateDmgByType (BSC:1321-1325), once per applied row, IN TABLE ORDER
            d = d * mul // 10  # BSC:1323
            if d == 0 and mul != 0:  # BSC:1324-1325: a step never takes nonzero-able damage to 0
                d = 1
        if no_effect:
            mins.append(0)
            maxs.append(0)
            continue
        # --- ApplyRandomDmgMultiplier (BSC:1639-1651), called by Cmd_adjustnormaldamage (BSC:1662):
        # randPercent = 100 - (Random() % 16), i.e. 85..100; nonzero damage is multiplied, divided by 100, floored at 1.
        if d == 0:
            mins.append(0)
            maxs.append(0)
        else:
            mins.append(d * 85 // 100 or 1)  # the r = 15 end (85%)
            maxs.append(d * 100 // 100 or 1)  # the r = 0 end (100%)
    return mins, maxs


def after_base(B: int, move_type: str, attacker_types, defender_types_rom, crit: bool, charge_listed_electric: bool,
               struggle: bool = False, foresight: bool = False) -> tuple[int, int]:
    """The game's (min, max) damage for ONE base B: Cmd_damagecalc -> Cmd_typecalc -> ApplyRandomDmgMultiplier."""
    mins, maxs = after_base_many((B,), move_type, attacker_types, defender_types_rom, crit, charge_listed_electric,
                                 struggle, foresight)
    return mins[0], maxs[0]


def fixed_damage(effect: str, level: int, target_hp: int, move_type: str, defender_types_rom,
                 foresight: bool = False) -> tuple[int, int]:
    """(min, max) HP dealt by a fixed-damage move, keyed on moves.json's `effect` name.

    Each script runs `typecalc` BEFORE it sets the damage (BS1:814 SuperFang, BS1:824 DragonRage, BS1:1200 LevelDamage,
    BS1:1211 Psywave, BS1:1725 Sonicboom), and `bicbyte` clears only SUPER_EFFECTIVE/NOT_VERY_EFFECTIVE, so a x0 row
    leaves MOVE_RESULT_DOESNT_AFFECT_FOE set and Cmd_datahpupdate deals nothing (BSC:1862). The value itself is set
    AFTER typecalc (so STAB and the x2/x0.5 rows never touch it), and `adjustsetdamage` (BSC:5861) has NO random factor."""
    type1, type2 = _defender_pair(defender_types_rom)
    if 0 in type_steps(move_type, type1, type2, foresight):
        return 0, 0
    if effect == "SONICBOOM":  # BS1:1727 `setword gBattleMoveDamage, 20`
        return 20, 20
    if effect == "DRAGON_RAGE":  # BS1:826 `setword gBattleMoveDamage, 40`
        return 40, 40
    if effect == "LEVEL_DAMAGE":  # Cmd_dmgtolevel, BSC:7926-7930: the ATTACKER's level (Night Shade, Seismic Toss)
        return level, level
    if effect == "SUPER_FANG":  # Cmd_damagetohalftargethp, BSC:7577-7584: the target's CURRENT hp / 2, at least 1
        half = max(1, target_hp // 2)
        return half, half
    if effect == "PSYWAVE":  # Cmd_psywavedamageeffect, BSC:7932-7941: r = Random() % 16 redrawn while > 10, so r is
        # 0..10; damage = level * (10 r + 50) / 100, i.e. level * 50 / 100 up to level * 150 / 100 (11 values)
        return level * 50 // 100, level * 150 // 100
    raise ValueError(f"not a fixed-damage effect this port knows: {effect!r}")
