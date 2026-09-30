> ⚠ A NOTE: the CONTRACT between step 11's production raw reads (`sandbox-pokebot/modules/dmgaudit.py`) and its offline
> classifier (`tools/story-dev/audit_damage_calc.py`). Design: `../2026-09-30-dmgcalc11-DESIGN.md` F3/F4. v=1.

# `[DMGAUDIT]` line format, v=1

Every line is written by `debug_logger.event(message, category="DMGAUDIT")`, so in the debug log it reads
`f<frame> [DMGAUDIT] <KIND> v=1 <field>=<value> ...`. Fields are space-separated `key=value`; no value contains a space.
Integers are decimal; `hex` values are lowercase, no `0x`, fixed width; lists are comma-separated.

| KIND | When | Fields |
|---|---|---|
| `CTL` | battle start (`battle_handler.handle_battle`, before its loop); clears any pending BEFORE | `v=1` |
| `BEFORE` | the selection EXIT: after `handle_battle_action_selection`'s `while`, only when the battle is active and the main callback has LEFT the selection states | the RAW fields below, plus `badges`, `pred`, `eff` |
| `AFTER` | `kind=entry`: the FIRST selection entry after a BEFORE (right after `battle_state = get_battle_state()`); `kind=end`: the battle handler's loop exit, when a BEFORE is pending. Each consumes the pending BEFORE | `kind`, the RAW fields below, plus `party` |
| `ERR` | a read or a prediction raised (never propagated) | `where=<ctl|before|after-entry|after-end>`, `err=<ExceptionTypeName>` |

**The RAW fields** (all by pure `read_symbol`; never `get_battle_state()`):

| Field | Source | Format |
|---|---|---|
| `t` | `gBattleResults` + 0x13 (battleTurnCounter) | int |
| `out` | `gBattleOutcome` | int |
| `flags` | `gBattleTypeFlags` | hex8 |
| `act` | `gChosenActionByBattler[0..3]` | 4 ints |
| `mv` | `gChosenMoveByBattler[0..3]` (u16) | 4 ints |
| `bide` | `gBideDmg[0..3]` (s32; only differences are meaningful: never reset per battle) | 4 ints |
| `weather` | `gBattleWeather` (u16) | int |
| `side` | `gSideStatuses[0..1]` (u16; bit 0x1 Reflect, 0x2 Light Screen, 0x10 Spikes, 0x20 Safeguard, 0x40 Future attack, 0x100 Mist) | 2 ints |
| `s3` | `gStatuses3[0..1]` (u32) | 2 × hex8 |
| `dis` | `gDisableStructs[0..1]` (0x1C bytes each) | 2 × hex56 |
| `mons` | `gBattleMons[0..1]` (0x58 bytes each; the decomp's `struct BattlePokemon`) | 2 × hex176 |
| `ff` | Flash Fire: `gBattleResources` → `flags` (+0x04) → u32 `flags[0..1]`; `null` if a pointer is outside EWRAM (it IS null at a battle's end) | 2 ints or `null` |

**BEFORE only:** `badges` = an int, bit i set when `BADGE0{i+1}_GET` is set (for the offline port replay);
`pred=<min>,<max>,<cmin>,<cmax>` = the LIVE `calculate_move_damage_range` for `gChosenMoveByBattler[0]` (non-crit
min/max, then `is_critical_hit=True` min/max), computed on the handler's existing `battle_state`, our left battler vs
the foe's left battler; `pred=none` when our action is not USE_MOVE (0) or the move is 0; `pred=err:<Name>` if it
raised. `base=<b>,<bcrit>` = the calculator's own base term `_calculate_base_move_damage(..., False/True)` for the same move (so the offline audit can replay the decomp-ordered port `dmgcalc_port.after_base` from it), `none` when `pred` is `none` or an error. `eff` = the chosen move's `effect` (from `moves.json`), or `-`. Field order on a BEFORE line: the RAW fields, then `badges`, `pred`, `base`, `eff`.

**AFTER only:** `party` = the 6 `gEnemyParty` slots (100 bytes each) as `<pid hex8>:<hp int>` (pid at +0x00, current
HP at +0x56), comma-separated; the classifier uses it for "the old foe's HP is 0" on a trainer KO.

**The fault switch** `POKEBOT_R25_FAULT_DMGAUDIT_BIDE0=1` (M1b-FAULT): `bide` reports slot 0's value in position 1
(the reader pointed at the wrong battler). Registered in `29` with the flag.

**`struct BattlePokemon` offsets** (0x58; decomp `include/pokemon.h`): species 0x00; attack 0x02, defense 0x04, speed
0x06, spAttack 0x08, spDefense 0x0A; moves 0x0C (4 × u16); IVs word 0x14; statStages 0x18 (8 bytes, 6 = neutral: HP,
Atk, Def, Speed, SpAtk, SpDef, Acc, Eva); ability 0x20; type1 0x21; type2 0x22; pp 0x24 (4); hp 0x28 (u16); level 0x2A;
maxHP 0x2C (u16); item 0x2E (u16); personality 0x48 (u32); status1 0x4C (u32; sleep 0x7, poison 0x8, burn 0x10,
freeze 0x20, paralysis 0x40, toxic 0x80); status2 0x50 (u32; confusion 0x7, substitute 0x1000000, wrapped 0xE000,
nightmare 0x8000000, cursed 0x10000000, foresight 0x20000000; the rest in the decomp's `include/constants/battle.h`).
`gStatuses3` bits (u32): leech seed 0x4, on air 0x40, underground 0x80, minimized 0x100, charged up 0x200, rooted 0x400,
mud sport 0x10000, water sport 0x20000, underwater 0x40000.
