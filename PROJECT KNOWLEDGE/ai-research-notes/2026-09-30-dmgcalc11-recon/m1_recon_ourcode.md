> ⚠ **A NOTE, NOT A SOURCE OF TRUTH.** Output of one agent of the design v2 step 11 recon (2026-09-30, a workflow of five fresh Claude agents; decomp read at pret/pokeemerald f90719c4). The design that uses it is `../2026-09-30-dmgcalc11-DESIGN.md`, whose author re-read every load-bearing claim it relies on (marked ✔ there). Line numbers are as of branch `wt/dmgcalc11` at `241929d7`. Scratch scripts it mentions were not committed.

# M1 recon: OUR damage calculator, line by line (design v2 step 11)

**Angle:** `calculate_move_damage_range` and everything it reads, set against the pret/pokeemerald decomp.
**Status:** a research NOTE, not truth. Every claim cites FILE:LINE. I read every cited line myself unless it is marked UNVERIFIED.

**Sources**
- Our code: worktree `C:/Remote Projects/pokebot-wt-ch24` (branch `wt/dmgcalc11`), read-only.
  - `sandbox-pokebot/modules/battle_strategies/_util.py` (below: `_util.py`)
  - `sandbox-pokebot/modules/battle_state.py`
  - `sandbox-pokebot/modules/pokemon.py`
  - `sandbox-pokebot/modules/items.py`
  - `sandbox-pokebot/modules/data/{moves,types,species}.json`
- Decomp: pret/pokeemerald `master`, HEAD `f90719c4` (2026-09-29), fetched 2026-09-30 with `gh api`.
  - `src/pokemon.c`, `src/battle_script_commands.c` (below: `bsc.c`), `data/battle_scripts_1.s` (below: `bs1.s`)
  - `src/battle_util.c`, `src/battle_main.c`
  - `include/pokemon.h`, `include/battle.h`, `include/battle_main.h`, `include/battle_util.h`
  - `include/constants/battle.h`, `include/constants/pokemon.h`
  - Local copies are in the scratchpad `decomp/` folder (`pokemon.c`, `bsc.c`, `bs1.s`, `battle_util.c`, `m1_*.h`, `m1_battle_main.c`).
- The arithmetic check script is `scratchpad/m1/pipeline_diff.py` (§7).

---

## 0. The findings that matter most for the design

1. **Our order of operations is not the game's.**
   - Ours: base (+2) → STAB → type → **crit ×2** → Charge ×2 → random (`_util.py:207-242`).
   - Game: base (+2) → **crit ×2 × dmgMultiplier** → Charge → Helping Hand → STAB → type → random.
     - `bsc.c:1296-1301` (damagecalc)
     - `bsc.c:1369-1406` (typecalc)
     - `bsc.c:1639-1651` (random)
     - The script order is at `bs1.s:249-252`.
   - ⇒ **crit_max under-predicts by up to 4 HP**, and by up to 8 HP with Charge. Non-crit max is off by at most ±1 (§7).
   - With W=1, the stage-2 bound `ceil(crit_max·1.10)+3` covers the ordering gap in every case enumerated (§7). It does NOT cover the model gaps in items 2-6.
2. **NEW (not in KI-109/110/111): Marvel Scale reads the ATTACKER's status.**
   - Ours, `_util.py:399`: `defender.ability == "Marvel Scale" and attacker_status is not Healthy`.
   - Game, `pokemon.c:3213`: `defender->status1`.
   - Milotic is the only holder (species.json). When our attacker is statused and Milotic is healthy, ours under-predicts physical damage by about 1/3.
3. **NEW: Guts + burn.**
   - The game skips the burn halving for Guts (`pokemon.c:3263`). Ours always halves (`_util.py:445-446`) and still applies Guts ×1.5 (`:397-398`).
   - ⇒ A burned Guts attacker is under-predicted by about 25%.
   - Holders include Taillow/Swellow, Makuhita/Hariyama and the Machop line, all common Hoenn team members.
4. **NEW: Psywave's range is wrong even after KI-109's spelling fix.**
   - Ours: `DamageRange(level, level*150//100)` (`_util.py:227-228`), so min = 100% of level.
   - Game: `level*(50+10k)/100` with k in 0..10, so min is 50% of level (`bsc.c:7932-7940`).
5. **Every fixed-damage return ignores type immunity** (`_util.py:215-228`, after the type loop at `:212-213`).
   - The game runs `typecalc` before each of them: `bs1.s:809-816` (Super Fang), `:819-827` (Dragon Rage), `:1720-1728` (Sonicboom), `:1195-1203` (Night Shade/Seismic Toss), `:1206-1214` (Psywave).
   - This confirms KI-109's fix note.
6. **Conditional ×2 multipliers are unmodelled.** They set `gBattleScripting.dmgMultiplier`:
   - Surf vs Dive (`bs1.s:240`), Whirlpool vs Dive (`:834`)
   - Twister (`:1829`) and Gust (`:1895`) vs Fly/Bounce
   - Earthquake/Magnitude vs Dig (`:1843`)
   - Stomp-family vs Minimize (`:1900`)
   - Facade (`:2257`), SmellingSalt (`:2274`), Pursuit on a switch (`:3091`)
   - Revenge (`bsc.c:9346`) and Weather Ball (`bsc.c:9792`)
   - **Brick Break** removes the screens BEFORE its damagecalc (`bs1.s:2423`, `removelightscreenreflect`). Ours still halves for Reflect.
7. **Degenerate ranges.**
   - For any type-IMMUNE plain move, ours returns `DamageRange(min=1, max=0)`: the zeroed damage flows through `:230-242` into `max(1, 85·0//100)`.
   - For a tiny base (≤5, 4× resisted), ours gives max=0 where the game floors each type step at 1 (`bsc.c:1324-1325`). There are 96 such cases in the enumerated sweep.
8. **Nothing exercises the crit path.** No caller passes `is_critical_hit=True`: a grep over every `.py` in the worktree finds only 3-arg calls. crit_max is new territory for M1a.
9. **The type chart itself is exact.** A programmatic diff of `types.json` against `gTypeEffectiveness` (`battle_main.c:335-449`) finds NONE.
   - Correction to a note: `CLAUDE-VALIDATED-concepts-round2.md:200` warns that the chart "migrated to a UQ_4_12 table". That is not so in pret/pokeemerald master: the 0/5/10/20 table is at `battle_main.c:335`, and `TYPE_MUL_*` is defined at `include/battle_main.h:31-34`.

---

## 1. Signature, return value, what "min" and "max" mean

```python
# _util.py:165-171
def calculate_move_damage_range(self, move: "Move", attacker: "Pokemon | BattlePokemon",
                                defender: "BattlePokemon", is_critical_hit: bool = False) -> DamageRange
```

- **`DamageRange`** (`_util.py:16-22`): `.min` and `.max`. `max` defaults to `min` when omitted.
- **"max"** is the damage of ONE hit at the 100% random roll, after STAB and type effectiveness.
  - It includes a crit only when `is_critical_hit=True` (then ×2 at `:230-231`, applied after STAB/type).
  - It includes Charge (`:233-238`).
  - It EXCLUDES:
    - multi-hit totals;
    - every `dmgMultiplier` condition (Facade, Stomp vs Minimize, Surf vs Dive, …);
    - Helping Hand (`:240`, todo);
    - Flash Fire's boost (`:518`, todo);
    - Mud Sport and Water Sport (`:402-406`, todo);
    - Cloud Nine and Air Lock (`:497`, todo).
- **"min"** is `max(1, 85*max//100)` (`:242`), the 85% roll.
  - `_percentage(v, p) = (p*v)//100` (`:36-37`). That equals the game's `damage*randPercent/100` with a floor and a zero-to-1 rule (`bsc.c:1639-1651`), provided the pre-random value matches.
  - The game's roll has 16 equiprobable values, 85..100 (`bsc.c:1642`).
- **Fixed-damage returns** skip crit and random (`:215-228`), as the game does (no critcalc or random in those scripts). The values: Dragon Rage (40,40); Super Fang (max(1, hp//2)); Night Shade/Seismic Toss (level, level); Psywave (level, 1.5·level).
- **An immune target** gives `(min=1, max=0)`, per §0 item 7.
- **An ability immunity** (Levitate, Wonder Guard, Soundproof, Volt/Water Absorb, Flash Fire) gives `(0, 0)` through the early return at `:204-205`.
- **A power-0 move** gives `(0, 0)` (`:321-322` → `:204`).

---

## 2. Every term, in the order ours applies it (exact arithmetic)

**Stage A: `calculate_move_damage_range` entry**

| # | Term | Ours (file:line, arithmetic) | Decomp counterpart |
|---|---|---|---|
| A1 | Defender/attacker types | `defender.species.types if isinstance(defender, Pokemon) else defender.types` (`_util.py:173-174`). `BattlePokemon.types` reads live bytes 0x21/0x22 and dedups equal types (`battle_state.py:577-584`) | `gBattleMons[].types[0/1]` (`pokemon.h:279`), with a dedup guard in typecalc (`bsc.c:1401-1402`) |
| A2 | Base damage | `_calculate_base_move_damage(...)` (`:176`); Stage B | `CalculateBaseDamage` (`pokemon.c:3106-3372`) |
| A3 | Move type and power | `_get_move_type_and_power` (`:25-29`): HIDDEN_POWER → `(hidden_power_type, hidden_power_damage)`, else `(move.type, move.base_power)` | `gDynamicBasePower` / `dynamicMoveType` via `Cmd_hiddenpowercalc` (`bsc.c:8889-8913`); the formula matches `battle_state.py:678-702` |

**Stage B: `_calculate_base_move_damage` (`_util.py:296-520`)**

| # | Term | Ours | Decomp | Match? |
|---|---|---|---|---|
| B1 | Which side is which | `attacker in own_side` (`:301`); `partner_for` (`:304`, `:308`, `:313`, `:317`). `__contains__` compares raw 0x58-byte blobs (`battle_state.py:370-377`, `:479-483`) | `battlerIdAtk/Def`, `GetBattlerSide` | ok for BattlePokemon. For a party `Pokemon` attacker, `__contains__` returns `NotImplemented`, which is truthy ⇒ "player" (a DeprecationWarning; see §9) |
| B2 | Power 0 → 0 | `:321-322` | power read at `pokemon.c:3119-3122` | ok |
| B3 | Raw stats | `attacker.stats.attack/special_attack`, `defender.stats.defence/special_defence` (`:324-327`). BattlePokemon stats are live u16s at 0x02-0x0B (`battle_state.py:496-504`) | `pokemon.c:3129-3132` | ok |
| B4 | Huge/Pure Power | `attack *= 2` (`:332-333`) | `pokemon.c:3158-3159` (before badges) | ok, same order |
| B5 | Badge boosts | B1 Atk, B5 Def, B7 SpA, **B8** SpD, each `(110*x)//100` if the side is the player (`:336-343`) | B1/B5/B7/**B7**, through `ShouldGetStatBadgeBoost` (`pokemon.c:3161-3168`). No boost in link, e-Reader, recorded-link, Frontier or Secret Base (`:3407-3419`) | **KI-110** (SpD on B8, dormant); exceptions missing |
| B6 | Type-boost held item | `hold_effect.value.endswith("_power")` and the prefix equals the move type → Atk or SpA `(100+param)` (`:346-355`). Enum values: `items.py:141-170` | `sHoldEffectToType` (`pokemon.c:1919-1938`, loop `:3171-3182`) | ok (the string mapping covers all 17) |
| B7 | Choice Band | Atk ×150% (`:357-358`) | `pokemon.c:3185-3186` | ok |
| B8 | Soul Dew (Atk and Def side) | SpA and SpD ×150% for Latias/Latios (`:359-360`, `:370-371`) | same, but **not in Frontier** (`pokemon.c:3187-3190`) | Frontier exclusion missing (irrelevant to Story) |
| B9 | DeepSeaTooth/Scale, Light Ball, Thick Club, Metal Powder | `:361-366`, `:372-375` | `pokemon.c:3191-3200` | ok |
| B10 | Enigma Berry hold effects | unsupported (comment `:329-330`) | `pokemon.c:3135-3156` | gap (Enigma only) |
| B11 | Thick Fat | defender, Fire/Ice → `special_attack //= 2` (`:388-389`) | `pokemon.c:3203-3204` | ok |
| B12 | Hustle | Atk ×150% (`:390-391`) | `:3205-3206` | ok |
| B13 | Plus/Minus | only when the attacker's PARTNER has the other ability (`:392-396`) | `ABILITY_ON_FIELD2` (`pokemon.c:3207-3210`; macro at `battle_util.h:38`) scans ALL battlers, foes included, with no HP check (`battle_util.c:3114-3122`) | scope narrower (doubles and edge cases only) |
| B14 | Guts | Atk ×150% if the status is not Healthy (`:397-398`) | `pokemon.c:3211-3212` (`status1 != 0`) | ok |
| B15 | **Marvel Scale** | Def ×150% if **attacker_status** is not Healthy (`:399-400`) | **`defender->status1`** (`pokemon.c:3213-3214`) | **BUG (new)** |
| B16 | Mud Sport / Water Sport | todo, not applied (`:402-406`). The statuses ARE parsed (`battle_state.py:111-112`, `:186-188`) | power /2 (`pokemon.c:3215-3218`) | gap |
| B17 | Overgrow/Blaze/Torrent/Swarm | `hp <= total_hp//3` → `power = (150*power)//100` (`:408-415`) | `pokemon.c:3219-3226` | ok |
| B18 | Explosion | `move.effect == "EXPLOSION"` → `defence //= 2` (`:417-418`) | `pokemon.c:3229-3230` | ok |
| B19 | Physical/special split | `Type.is_physical = index < 9`, `is_special = index >= 9` (`pokemon.py:307-313`) | `IS_TYPE_PHYSICAL(t) t < TYPE_MYSTERY`, `IS_TYPE_SPECIAL(t) t > TYPE_MYSTERY` (`battle.h:466-467`) | ??? (index 9) counts as special in ours; dead in practice (only Curse, power 0) |
| B20 | Attack stage (crit rule) | crit and stage ≤ 0 → raw, else `stat*(10+5·max(0,s))//(10+5·|min(0,s)|)` (`:32-33`, `:423-429`). A party `Pokemon` attacker always uses the raw stat | `APPLY_STAT_MOD` with `gStatStageRatios` (`pokemon.c:1868-1883`, `:3100-3104`, `:3234-3243`) | ok (the ratios are identical) |
| B21 | × power × (2·L//5+2) | `:431-432` | `pokemon.c:3245-3246` | ok |
| B22 | ÷ Def (crit rule: stage > 0 ignored) | `:434-440` | `pokemon.c:3248-3259` | ok |
| B23 | ÷ 50 | `:442` | `:3260` | ok |
| B24 | **Burn** | `damage //= 2` whenever burned (`:445-446`) | only if `ability != GUTS` (`pokemon.c:3263-3264`) | **BUG (new)** |
| B25 | Reflect | timer `turns_remaining > 0` and not crit; in doubles with a partner, `2*(d//3)`, else `//2` (`:449-453`). The timer bytes are `gSideTimers` (`battle_state.py:437-439`, `:814`) | the `SIDE_STATUS_REFLECT` bit and `gCritMultiplier == 1`; doubles when `CountAliveMonsInBattle(DEF_SIDE) == 2` (`pokemon.c:3267-3273`) | ok by proxy (a timer instead of the bit; UNVERIFIED that the two cannot disagree for a frame) |
| B26 | Spread halving | doubles, `move.target == "BOTH"`, partner present → `//2` (`:456-457`) | `pokemon.c:3276-3277` | ok. FOES_AND_ALLY moves (Earthquake, Magnitude) are not halved in either |
| B27 | Physical minimum 1 | `:460` | `pokemon.c:3280-3281` | ok |
| B28 | ??? → 0 | `:463-464` | `pokemon.c:3284-3285` | ok, but see B19 (ours then re-enters the special branch) |
| B29-B32 | Special: SpA stage, × power × level term, ÷ SpD stage, ÷ 50 | `:466-484` | `pokemon.c:3287-3315` | ok. No special minimum of 1 in either |
| B33 | Light Screen | `:487-491` | `pokemon.c:3318-3324` | ok |
| B34 | Spread halving (special) | `:494-495` | `:3327-3328` | ok |
| B35 | Cloud Nine / Air Lock | todo, ignored (`:497`) | `WEATHER_HAS_EFFECT2` (`pokemon.c:3331`; macro `battle_util.h:48`) | gap (Psyduck/Golduck, Rayquaza) |
| B36 | Rain | Fire `//2`, Water `(15*d)//10` (`:501-505`). `Weather.Rain` = any of bits 0-2 (`battle_state.py:312-322`) | only `B_WEATHER_RAIN_TEMPORARY` (`pokemon.c:3334-3345`). Every rain source sets TEMPORARY (`battle_util.c:2486`, `:2521`; `bsc.c:6690`) | ok in practice |
| B37 | Solar Beam in rain/sand/hail | `move.name == "Solar Beam"` (`:508-509`) | `gCurrentMove == MOVE_SOLAR_BEAM` (`pokemon.c:3348-3349`) | **KI-111** (the data spells it "Solarbeam", `moves.json:2663`) |
| B38 | Sun | Fire ×1.5, Water //2 (`:512-516`) | `pokemon.c:3352-3363` | ok |
| B39 | Flash Fire boost | todo, ignored (`:518`) | `pokemon.c:3367-3368` | gap (our own Flash Fire mon only) |
| B40 | +2 | `return damage + 2` (`:520`) | `pokemon.c:3371` | ok |

**Stage C: back in `calculate_move_damage_range` (`_util.py:180-242`)**

| # | Term | Ours | Decomp | Match? |
|---|---|---|---|---|
| C1 | Levitate vs Ground → 0 | `:180-181` | typecalc (`bsc.c:1375-1383`) | ok |
| C2 | Wonder Guard | 0 unless the move is >1× against ANY defender type (`:183-190`) | typecalc (`bsc.c:1409-1419`): blocked unless the net result is SE; SE+NVE counts as blocked; only when `AttacksThisTurn == 2` and power ≠ 0 | no Bug/Ghost combination differs in practice |
| C3 | Soundproof, Volt Absorb, Water Absorb, Flash Fire → 0 | `:192-202` | these abilities block (or heal) in `AbilityBattleEffects` (UNVERIFIED exact lines; not read) | ok for damage. Volt/Water Absorb make the foe's HP RISE |
| C4 | 0 → `DamageRange(0)` | `:204-205` | | |
| C5 | **STAB** | `move_type in attacker_types` → `(150*d)//100` (`:208-209`) | `IS_BATTLER_OF_TYPE` → `d*15/10` (`bsc.c:1369-1373`), applied **after** crit, dmgMultiplier, Charge and Helping Hand | **order differs** |
| C6 | Type effectiveness | per defender type in `[type1, type2]` order: `(int(100*eff)*d)//100` (`:212-213`) | chart-order loop (`bsc.c:1386-1406`). Each step is `d*m/10` with **d=0→1 when m≠0** (`bsc.c:1321-1325`). Foresight skips the Ghost immunities (`bsc.c:1388-1393`; chart `battle_main.c:445-447`) | ±1 (order); the min-1 floor is missing; Foresight is unmodelled |
| C7 | Dragon Rage 40 | `:215-216` (name matches `moves.json:2873`) | `bs1.s:819-827` (typecalc first) | ignores immunity (no Dragon immunity exists in Gen 3, so it is harmless) |
| C8 | Sonicboom 20 | `move.name == "Sonic Boom"` (`:218-219`), which never matches (`moves.json:1718`: "Sonicboom") | `bs1.s:1720-1728` | **KI-109** |
| C9 | Super Fang | `max(1, defender.current_hp//2)` (`:221-222`) | `bsc.c:7577-7583`, after typecalc (`bs1.s:809-816`) | Ghost immunity ignored |
| C10 | Night Shade / Seismic Toss | `attacker.level` (`:224-225`) | `bsc.c:7926-7930`, after typecalc (`bs1.s:1195-1203`) | immunity ignored (KI-109) |
| C11 | Psywave | `"Psy Wave"` (`:227-228`) never matches `moves.json:5218` "Psywave". Even if it did, min = level | `bsc.c:7932-7940`: `level*(rand*10+50)/100`, rand 0..10 | **KI-109**, plus the **min bug (new)** |
| C12 | **Crit** | `d *= 2` (`:230-231`), after STAB and type | `gCritMultiplier` inside damagecalc (`bsc.c:1296`), before STAB and type | order differs: up to 4 HP low (§7) |
| C13 | Charge | BattlePokemon with `ChargedUp` (status3 bit 9, `battle_state.py:173-174`) and an Electric **dynamic** type → ×2 (`:233-238`) | `gBattleMoves[gCurrentMove].type == TYPE_ELECTRIC`, the **static** type (`bsc.c:1298-1299`), before STAB and type | order, and Hidden Power (Electric) differs |
| C14 | Helping Hand | todo (`:240`) | `bsc.c:1300-1301` | gap (doubles) |
| C15 | Random | `DamageRange(max(1, (85*d)//100), d)` (`:242`) | `bsc.c:1639-1651` | ok |
| C16 | Focus Band / Endure / False Swipe caps at hp-1 | not modelled | `bsc.c:1677-1696` | the game deals LESS, so ours only over-predicts. Harmless to an upper bound |

**The game's order for a plain hit** (`bs1.s:236-252`: critcalc, damagecalc, typecalc, adjustnormaldamage):
1. B = CalculateBaseDamage + 2
2. × crit (1 or 2) × dmgMultiplier (1 or 2)
3. Charge ×2
4. Helping Hand ×1.5
5. STAB ×1.5
6. type steps (each floored, minimum 1)
7. random 85-100 (floored, minimum 1)
8. Focus Band/Endure/False Swipe cap
9. datahpupdate: a Substitute absorbs the damage, and HP is capped (`bsc.c:1844-1900`)

`dmgMultiplier` and `gCritMultiplier` are reset to 1 per action (`battle_util.c:92`, `bsc.c:3620-3624`).

---

## 3. Special cases: modelled or not

| Case | Modelled? | Where | Notes |
|---|---|---|---|
| Fixed damage (Dragon Rage, Sonicboom, Super Fang, Night Shade/Seismic Toss, Psywave) | partly | `_util.py:215-228` | Name-matched: Sonicboom and Psywave are misspelled (KI-109). All ignore immunity. Psywave's min is wrong |
| Level damage | yes | `:224-225` | immunity ignored (Night Shade vs Normal, Seismic Toss vs Ghost) |
| OHKO (Guillotine, Horn Drill, Fissure, Sheer Cold) | **no** | | Scored as ordinary 1-power moves. The game uses `tryKO` (`bs1.s:762-769`, `bsc.c:7490`) |
| Multi-hit (DOUBLE_HIT, MULTI_HIT, TRIPLE_KICK, TWINEEDLE, BEAT_UP) | **no** | | Per-hit only; each hit rolls its own crit and random. `lose_on_purpose.py:46-51` multiplies ad hoc |
| Crit | optional flag, never used | `:230`, `:424`, `:435`, `:449`, `:467`, `:477`, `:487` | Stage and screen rules correct; the ×2 order is wrong |
| Random 85-100 | yes | `:242` | exact, given the same pre-random value |
| STAB | yes | `:208-209` | order differs; the game skips it for Struggle (`bsc.c:1360-1364`), ours does not |
| Type effectiveness and immunity | yes | `:212-213` | chart identical; order ±1; no min-1 floor; no Foresight/Odor Sleuth (`TemporaryStatus.Foresight` is parsed at `battle_state.py:154-155`) |
| Weather (Rain/Sun ×1.5 and ×0.5) | yes | `:498-516` | Cloud Nine/Air Lock ignored; Solarbeam misspelled (KI-111). Sand/hail chip is end-of-turn, outside the calculator |
| Badges | yes, with bugs | `:336-343` | KI-110; no exceptions |
| Abilities (attacker) | Huge/Pure Power, Hustle, Guts, pinch 4, Plus/Minus | `:332-415` | missing: Flash Fire boost; the Guts-with-burn exception |
| Abilities (defender) | Thick Fat, Marvel Scale (buggy), Levitate, Wonder Guard, Soundproof, Volt/Water Absorb, Flash Fire | `:180-202`, `:388-400` | `.ability` comes from species plus the abilityNum bit (`battle_state.py:566-570`), not the live `gBattleMons.ability` byte 0x20 (`pokemon.h:278`; exposed only as `ability_n`, `battle_state.py:573-574`). A Trace/Role Play/Skill Swap change is invisible |
| Items | type boosters, Choice Band, species items | `:346-375` | no Enigma. Defender berries and Leftovers act AFTER the hit (outside the calculator) |
| Burn | yes | `:445-446` | ignores the Guts exception |
| Screens | yes | `:449-453`, `:487-491` | Brick Break removes them first in the game (`bs1.s:2423`) |
| Stat stages | yes | `:32-33`, `:423-440`, `:466-482` | only for BattlePokemon; a party `Pokemon` attacker uses raw stats |
| Charge | yes | `:233-238` | order and dynamic vs static type |
| Helping Hand, Mud/Water Sport | no | `:240`, `:402-406` | |
| dmgMultiplier conditions | no | | Listed in §0 item 6 |
| Variable-power moves (Flail/Reversal, Return/Frustration, Magnitude, Low Kick, Present, Eruption/Water Spout, Rollout/Ice Ball, Fury Cutter, Spit Up, Beat Up, Triple Kick) | no | | use the `moves.json` base power (1, 150, 30, 10, …) |
| Hidden Power | yes | `:25-29`; `battle_state.py:678-702` | Type and power formula match `bsc.c:8889-8913`; `HIDDEN_POWER_MAP` skips ??? correctly (`pokemon.py:51-68`) |
| Bide, Counter, Mirror Coat, Endeavor | no | todo `:172` | |
| Two-turn moves (Fly, Dig, Dive, Bounce, Solarbeam, Razor Wind, Skull Bash, Sky Attack), Future Sight/Doom Desire | formula only | | The damage lands on a later turn. Future Sight's stored damage is base-only, with no STAB/type/random/crit (`bsc.c:8929-8950`) |

---

## 4. Callers of `calculate_move_damage_range` in the sandbox (grep over all `*.py`)

**Direct callers**
- `_util.py:262`: `get_strongest_move_against` uses `.max`.
  - It skips `banned_moves`, 0 PP and the disabled move.
  - Ties go to the lowest slot (`list.index`); a best value ≤ 0 returns None (`:244-269`).
- `battle_strategies/lose_on_purpose.py:26`: `.max`, inverted to pick the weakest move. It applies ad-hoc ×2/×3/×5 for multi-hit and ×1.5 for ABSORB (`:30-60`).
- `plugins/custom_modes/story_mode.py:481`: the KI-95 faint-chooser rank, `_damage_of(mon, learned, foe)`.
  - Its attacker is a PARTY `Pokemon`: raw stats, `species.types`, and the `in own_side` → `NotImplemented` quirk (§9).
  - It returns None on exception.

**Callers of `get_strongest_move_against` (so indirectly `.max`)**
- `_util.py:547`: `get_potential_rotation_targets`, with a party `Pokemon` attacker.
- `battle_strategies/default.py`:
  - `:228` `decide_turn`
  - `:266`, `:273` `decide_turn_in_double_battle`
  - `:356` `_fight_on`
- `battle_strategies/level_up.py:35`: `LevelUpLeadBattleStrategy.decide_turn`. The Story strategies inherit this class: the MRO comment at `:46-50`, written about the faint chooser, names `StoryItemBattleStrategy -> LevelUpTravelBattleStrategy -> LevelUpLeadBattleStrategy`.
- `battle_strategies/run_away.py:23`, `:29`.
- `story_mode.py`:
  - `:228` `StoryCatchStrategy._fight_if_trapped_and_empty`
  - `:257` `StoryShinyCatchStrategy.decide_turn` (out of balls)
  - `:512` `LevelUpTravelBattleStrategy.decide_turn` (trainer battles)
  - `:583`, `:587` `decide_turn_in_double_battle`

**Summary of the callers**
- No caller passes `is_critical_hit`, so the crit path is dead in production.
- No caller computes damage aimed at our Pokémon, so `defender_is_player` is always False. That is why KI-110 is dormant, and the Badge 5 Def boost is dormant too.

**Tool callers** (not production): `tools/story-dev/probe_ghost_damage_real.py:123`, and the stubs at `probe_dexcatch_bail.py:146`, `probe_dex_catch_nofaintbail.py:163`, `repro_shiny_noballs.py:35`, `repro_nopp_trainer_loop.py:148-232` and `story_harness.py:206`. The same calculator is in `custom-pokebot/` and the upstream mirror (identical line numbers 165-242).

---

## 5. A "whitelisted effects" set (identified by `moves.json` `effect`)

The criterion: the effect's battle script is `BattleScript_EffectHit`, or `setmoveeffect X; goto BattleScript_EffectHit` (`bs1.s:21`, `:38`, `:64`, `:99`, `:122`, `:124`, `:149` map several effects straight to EffectHit). That means one hit, no dynamic power and no `dmgMultiplier`, so ours covers it with the formula alone. Effect names are as in `moves.json` (the decomp's `EFFECT_*` without the prefix).

**Tier A: plain, no condition** (include):
- HIT (but see Surf in Tier C)
- HIGH_CRITICAL, ALWAYS_HIT, QUICK_ATTACK, VITAL_THROW, PAY_DAY, SECRET_POWER, SKY_UPPERCUT, THUNDER, KNOCK_OFF, THIEF, RAPID_SPIN, FLINCH_HIT, PARALYZE_HIT, FREEZE_HIT
- ATTACK_DOWN_HIT, DEFENSE_DOWN_HIT, SPEED_DOWN_HIT, SPECIAL_ATTACK_DOWN_HIT, SPECIAL_DEFENSE_DOWN_HIT, ACCURACY_DOWN_HIT
- ATTACK_UP_HIT, DEFENSE_UP_HIT, ALL_STATS_UP_HIT, SUPERPOWER, OVERHEAT, RECHARGE
- DOUBLE_EDGE and RECOIL (**exclude Struggle, move index 165**: typecalc skips STAB and type for it, `bsc.c:1360-1364`), RECOIL_IF_MISS
- ABSORB, DREAM_EATER
- FALSE_SWIPE (capped, so it can only read low)
- FAKE_OUT (fails after turn 1 and reads 0)
- FOCUS_PUNCH, SNORE, RAGE
- HIDDEN_POWER (modelled; M1a should pin it)

Recoil and drain change OUR HP, not the target's. The script lines for these secondaries are at `bs1.s:319-371`, `:668`, `:720`, `:731`, `:1040-1062`, `:1764-1774`, `:2388`, `:2475`, `:2563-2569`, `:2640`, `:2648`, `:2712`, `:897`.

**Tier B: plain formula, but the secondary can move the TARGET's HP inside the observation window.** Include only if the AFTER read also passes the status exclusions:
- BURN_HIT, BLAZE_KICK, THAW_HIT, TRI_ATTACK: a new burn ticks at end of turn.
- POISON_HIT, POISON_TAIL, POISON_FANG: poison or toxic ticks.
- CONFUSE_HIT: a foe confused by our faster hit can hit itself the SAME turn.
- ⇒ **The spec's "foe is poisoned/burned/toxic/confused" exclusion must be evaluated at hp_after as well as hp_before.**

**Tier C: conditional ×2, or a screen skip.** Include only while the condition is observably false:
- HIT/Surf vs `TemporaryStatus.Underwater` (`bs1.s:237-240`)
- EARTHQUAKE (and MAGNITUDE, which is excluded anyway) vs `Underground` (`bs1.s:1834-1843`)
- GUST and TWISTER vs `InTheAir` (`bs1.s:1826-1829`, `:1892-1896`)
- FLINCH_MINIMIZE_HIT (Stomp, Needle Arm, Astonish, Extrasensory) vs `Minimized` (`bs1.s:1898-1900`)
- FACADE while our status is Healthy or Sleep/Freeze (`bs1.s:2252-2257`)
- SMELLINGSALT while the target is not paralysed (`bs1.s:2268-2274`)
- WEATHER_BALL while the weather is Neutral (`bsc.c:9787-9800`)
- BRICK_BREAK while no Reflect or Light Screen is on the foe's side (`bs1.s:2418-2427`)
- PURSUIT: the switch case is already excluded by the (PID, species) check (`bs1.s:3088-3091`)
- UPROAR and RAMPAGE: first turn only (lock-in turns have no "selected UseMove")
- EXPLOSION: the formula is right (the Def halving is modelled), but our mon faints. Exclude for practicality.

The status flags these tiers need (`Underwater`, `Underground`, `InTheAir`, `Minimized`, `Substitute`, `Foresight`, `Confused`, `Wrapped`, `LeechSeeded`, `Cursed`, `Nightmare`) are all parsed already (`battle_state.py:118-196`).

**Excluded** (not the plain formula):
- Multi-hit: DOUBLE_HIT, MULTI_HIT, TRIPLE_KICK, TWINEEDLE, BEAT_UP.
- Dynamic power: MAGNITUDE, FLAIL, RETURN, FRUSTRATION, LOW_KICK, PRESENT, ERUPTION, ROLLOUT, FURY_CUTTER, SPIT_UP.
- REVENGE: the ×2 depends on turn order.
- Fixed damage: SONICBOOM, DRAGON_RAGE, SUPER_FANG, LEVEL_DAMAGE, PSYWAVE. These are exact rows for step 12 stage 1, not formula samples.
- OHKO, COUNTER, MIRROR_COAT, BIDE, ENDEAVOR.
- Two-turn: SOLAR_BEAM, RAZOR_WIND, SKULL_BASH, SKY_ATTACK, SEMI_INVULNERABLE.
- FUTURE_SIGHT.
- TRAP: the end-of-turn wrap chip lands in the delta.

---

## 6. New divergences (beyond KI-109/110/111), ranked by effect on an UPPER bound

| Rank | Divergence | Direction | Size | Reach |
|---|---|---|---|---|
| 1 | Marvel Scale uses the attacker's status (`_util.py:399` vs `pokemon.c:3213`) | under-predicts when WE are statused and Milotic is healthy | about ×2/3 of the true value | Wallace's Milotic; wild Milotic (rare) |
| 2 | Guts + burn still halved (`:445` vs `pokemon.c:3263`) | under-predicts | about ×0.75 | our Swellow, Hariyama, Machamp, Heracross, Ursaring… when burned |
| 3 | Conditional ×2 (§0 item 6) and Brick Break vs screens | under-predicts | ×0.5 of the true value | the Tier C conditions |
| 4 | Crit applied after STAB/type (`:230` vs `bsc.c:1296`) | under-predicts crit_max | ≤4 HP (≤8 HP with Charge) | every crit |
| 5 | Foresight/Odor Sleuth not modelled | under-predicts (0 predicted vs a real hit) | total | only if WE used Foresight |
| 6 | Cloud Nine/Air Lock ignored | both directions | ×1.5 or ×2 | Psyduck/Golduck in weather |
| 7 | Mud Sport/Water Sport ignored | over-predicts | ×2 | a foe that used them |
| 8 | Flash Fire boost ignored | under-predicts | ×1.5 | our own activated Flash Fire mon |
| 9 | Plus/Minus scope; Helping Hand | under-predicts | ×1.5 | doubles |
| 10 | Dual-type order and the per-step min-1 floor | ±1; max=0 where the game gives ≥1 | 1 HP | tiny bases |
| 11 | Charge on a dynamic type (Hidden Power (Electric)) | over-predicts | ×2 | rare |
| 12 | Psywave min = level (should be ≥ level/2) | over-predicts the MIN | up to ×2 | Psywave users, once KI-109 is fixed |
| 13 | Fixed-damage immunity ignored (KI-109 fix note) | over-predicts | total | Ghost/Normal/Dark targets |
| 14 | `.ability` not live (Trace etc.) | both | total | Ralts line (Trace) |

---

## 7. Arithmetic check of the ordering-only gap (my scratch model, NOT a port)

**Method.** `scratchpad/m1/pipeline_diff.py`:
- It parses `gTypeEffectiveness` from the decomp.
- It holds the base value B (with its +2) equal in both pipelines.
- It sweeps B = 2..699, STAB on/off, crit on/off and Charge on/off, over every move type and every type pair in `species.json`.

**Results**
- **Chart diff, `types.json` vs decomp:** NONE.
- **Non-crit max:** under-predicts by at most **1**, e.g. (Bug/Flying, Fighting, B=2: game 1, ours 0). Over-predicts by at most **1**.
- **Crit max:** under-predicts by at most **4**. Example: a Bug/Fighting target, a STAB Flying move, B=3 gives game 36, ours 32 (11% relative). It never over-predicts.
- **Crit + Charge:** under-predicts by at most **8**.
- **Min, non-crit:** differs by at most **1**.
- **Degenerate ranges:** 96 cases where ours gives max=0 while the game gives ≥1 (B ≤ 5 against 4× resistance). Ours then returns min=1 > max=0.
- **The stage-2 bound** `ceil(crit_max·1.10)+3` with W=1 has **0 violations** from ordering alone, Charge included.

**Caveat.** This models only §2 Stage C. The base damage is assumed equal, which it is NOT in the §6 cases. M1a's full port must re-derive these numbers.

---

## 8. What this implies for M1a and M1b

**M1a rows to pin, beyond the spec's list**
1. The crit order: a B-odd STAB crit against a 4× target, expecting the game 36 vs ours 32.
2. Marvel Scale with the attacker statused and the defender healthy (and the reverse).
3. Guts plus burn.
4. The Psywave range (min is level/2).
5. Immunity against each fixed-damage effect.
6. `(min=1, max=0)` on an immune target.
7. Brick Break against Reflect.
8. Struggle (no STAB or type in the game).
9. Hidden Power type and power against the IV bits.
10. A dual-type order row that differs by 1.

**M1b**
- Compute crit_max with `is_critical_hit=True` (never called today).
- Treat `max == 0` as "predicted immune": log it, and do not score it against min.
- Evaluate the status and confusion exclusions at the AFTER read (Tier B).
- Exclude Tier C conditions from live status3 flags.
- Exclude a Substitute. The damage goes to `substituteHP` (`bsc.c:1864-1890`); `BattlePokemon.substitute_hp` is at `battle_state.py:744-746`.
- Log the effect name, so the whitelist can be applied after the fact as well as live.

---

## 9. Side findings (traps for whoever builds M1)

1. **Do not call `BattlePokemon.modified_stats()`** (`battle_state.py:590-620`).
   - Its stage table is Python **sets** (`{10, 40}`, `:594-608`), and `stages[i][0]` raises TypeError.
   - It is unused today: grep finds only its definition.
2. **A party `Pokemon` attacker relies on a truthy `NotImplemented`.**
   - `BattleStateSide.__contains__` returns `NotImplemented` for a non-BattlePokemon (`battle_state.py:370-377`). `attacker in own_side` is then truthy, with a DeprecationWarning; measured with `python -W error` on 3.9.13.
   - `partner_for(Pokemon)` returns our active battler (`battle_state.py:431-435`), because both `__ne__` return `NotImplemented` and the comparison falls back to identity (`pokemon.py:921-931`).
   - Supported Python is 3.11-3.13 (`requirements.py:7-8`), where this works.
   - UNVERIFIED: whether Python 3.14 turns it into a TypeError. If it does, `story_mode.py:481`'s `_damage_of` would return None for every mon.
3. **The BattlePokemon ability bit is correct.**
   - The layout: `isEgg` bit 30 (0x40 of byte 0x17), `abilityNum` bit 31 (0x80) (`include/pokemon.h:275-276`).
   - Ours: `is_egg` 0x40 (`battle_state.py:563`), ability 0x80 (`:567`).
4. **The weather mapping is correct.** Rain bits 0-2, sand 3-4, sun 5-6, hail 7 (`include/constants/battle.h:232-244` vs `battle_state.py:312-322`).
5. **Stat indices match** (`include/constants/pokemon.h:75-90` vs `battle_state.py:210-219`), and so do the type indices (`:6-23` vs `types.json` order).

---

## 10. Not verified by me (UNVERIFIED)

- The exact `AbilityBattleEffects` lines for the Soundproof, Volt Absorb, Water Absorb and Flash Fire blocks (C3). I did not open them.
- Whether Reflect's timer byte and its `SIDE_STATUS_REFLECT` bit can ever disagree on a frame we read.
- Python 3.14's handling of `NotImplemented` in a boolean context.
- The end-of-turn order of wrap, burn and poison damage within the same turn (it matters for Tier B/TRAP). I relied on the spec's `battle_util.c` citations and did not read them.
- Anything about `[TURN]` and the log categories in `battle_action_selection.py`. That is outside this angle and was not read.
