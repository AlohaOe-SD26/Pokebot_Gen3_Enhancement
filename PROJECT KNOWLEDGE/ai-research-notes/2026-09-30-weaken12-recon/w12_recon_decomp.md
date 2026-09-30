# 2026-09-30 — design v2 step 12 (weaken-to-catch) recon: the game's mechanics, checked against the decomp

⚠ **A NOTE, NOT TRUTH.** A Claude recon agent's report (model output), verbatim. Every load-bearing claim is re-checked by the author at its FILE:LINE before the design relies on it; the design note records which.

**Step 12 (weaken-to-catch): game-mechanics check against the pret/pokeemerald decomp**

This is a note, not truth. Every "VERIFIED" means I read that decomp line myself. The decomp copy is master `f90719c46ce710427cfcae65419a3fa684b34a8a` (2026-09-29), saved at `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\decomp\`. The spec checked is `C:\Remote Projects\pokebot-wt-ch24\PROJECT KNOWLEDGE\ai-research-notes\2026-09-29-r23-27-DESIGN-v2.md`, §Step 12 (lines 599-666). Nothing in the worktree was modified.

File abbreviations used below:
- BSC = `src/battle_script_commands.c`
- BU = `src/battle_util.c`
- BM = `src/battle_main.c`
- BS1 / BS2 = `data/battle_scripts_1.s` / `data/battle_scripts_2.s`
- MV = `src/data/battle_moves.h`
- SI = `src/data/pokemon/species_info.h`
- BCO = `src/battle_controller_opponent.c`
- BAI = `src/battle_ai_switch_items.c`
- BSET = `src/battle_setup.c`

---

## (1) The catch formula

**C1. "catch_p is exactly BSC:9987-10028" — VERIFIED.** `Cmd_handleballthrow` is BSC:9905-10053. Written exactly:

```
a    = (rate * bonus_x10) // 10                        # 9987: integer divide first (Great x rate 45 -> 67, not 67.5)
odds = a * (3*maxHP - 2*hp) // (3*maxHP)               # 9987-9989: in-battle hp/maxHP
if status in (SLEEP, FREEZE):             odds *= 2                 # 9991-9992
if status in (PSN, BRN, PAR, TOXIC):      odds = odds * 15 // 10    # 9993-9994 (two separate ifs; status1 holds only one)
if odds > 254 or ball == MASTER: return 1.0            # 10009-10020; Master forced at 10030-10031
b = 1048560 // isqrt(isqrt(16711680 // odds))          # 10025-10026
return (b / 65536) ** 4                                # 10028: 4 checks of Random() < b
```

- The loop runs 4 checks: `BALL_3_SHAKES_SUCCESS` is 4 (`include/battle_controllers.h:135-139`).
- `Random()` returns a u16 (`include/random.h:8`). `Sqrt` returns a u16 (`include/gba/syscall.h:20`). INFERRED: `Sqrt` rounds down (it is the BIOS square-root call, which is not in the decomp source).
- INFERRED by arithmetic: in the `odds ≤ 254` branch, `b ≤ 65535`, so a single check never reaches 1. At odds 254, `b` is 65535, and a catch is certain only when odds exceed 254.
- INFERRED by arithmetic: `odds = 0` (a divide by zero) is unreachable. The lowest catch rate in the game is 3 (21 species in SI), and every ball's multiplier is at least 10, so odds is always at least 1.

**C2. Status bonus in Gen 3 — VERIFIED (BSC:9991-9994).**
- Sleep or freeze: ×2.
- Poison, burn, paralysis, or toxic poison: ×1.5. Emerald does include toxic poison (9993).

**C3. Ball multipliers ×10 — VERIFIED.**

| Ball | ×10 value | Condition | Decomp |
|---|---|---|---|
| Ultra | 20 | none | BSC:841-847 |
| Great | 15 | none | BSC:841-847 |
| Poké | 10 | none | BSC:841-847 |
| Safari | 15 | catch rate becomes `safariCatchFactor*1275/100` | 9932-9933 |
| Net | 30 / 10 | 30 if the battler is currently Water or Bug type | 9941-9946 |
| Dive | 35 / 10 | 35 only on an underwater map | 9947-9952 |
| Nest | 40 − level / 10 | 40 − level if level < 40, floored at 10; 10 at level ≥ 40 | 9953-9964 |
| Repeat | 30 / 10 | 30 only if the species is already caught; never helps a new species | 9965-9970 |
| Timer | 10 + turn counter, max 40 | turn counter goes up in `BattleTurnPassed` | 9971-9975; counter at BM:3995-3997 |
| Luxury, Premier | 10 | none | 9976-9978 |
| Master | always caught | forced success | 10030-10031 |

- Master Ball detail: at 9984 its index into the bonus table is −1 (`include/constants/items.h:10-11`), so it reads outside the table. It never matters because success is forced.
- Net Ball reads the battler's current in-battle types, not the species types.

**C4. "No Substitute or semi-invulnerable test in the ball throw" — VERIFIED.**
- There is no Substitute or semi-invulnerable check anywhere in 9905-10053.
- `BattleScript_BallThrow` (BS2:50-53) is just a message followed by `handleballthrow`.
- The only blocks are a trainer battle (9915-9920) and Wally's tutorial (9921-9926).
- Additional fact: item actions, including ball throws, run before any move that turn (BM:4819-4824).

## (2) Exact-damage effects

**D1. The fixed damage values — all VERIFIED.**
- **Seismic Toss and Night Shade** (LEVEL_DAMAGE, BS1:1195-1204): damage = the attacker's level (BSC:7926-7930).
  - Seismic Toss: Fighting, 100% accuracy, makes contact (MV:900-911).
  - Night Shade: Ghost, 100% accuracy (MV:1316-1327).
- **Sonic Boom** (SONICBOOM): damage = 20 (BS1:1720-1729). Normal, 90% accuracy (MV:640-651).
- **Dragon Rage** (DRAGON_RAGE): damage = 40 (BS1:819-828). Dragon, 100% accuracy (MV:1069-1080).
- **Super Fang** (SUPER_FANG): damage = hp // 2, minimum 1 (BSC:7577-7584). Normal, 90% accuracy, makes contact (MV:2109-2120).
- **Super Fang at 1 HP:** it deals 1 damage and knocks the target out. At hp ≥ 2 it leaves ceil(hp/2).
- **Psywave is correctly excluded.** Its damage is random: level × (50..150)/100 (BSC:7932-7941).

**D2. Every way these moves deal something else or nothing — all VERIFIED unless marked.**
- **Type immunity applies.**
  - Every one of these scripts runs `typecalc` (BS1:814, 824, 1200, 1725).
  - An immunity sets "doesn't affect" (BSC:1329-1333), and the HP update is skipped (BSC:1862).
  - Normal and Fighting are ×0 against Ghost (BM:446-447). These rows sit after the Foresight marker (BM:445), so Foresight or Odor Sleuth on the target removes this immunity (BSC:1388-1391).
  - Ghost is ×0 against Normal (BM:427). This row is before the marker, so Foresight does not remove it.
  - Dragon has no ×0 matchup in Gen 3. The only ×0 rows are BM:356, 391, 396, 409, 427, 446, 447.
  - Result: Sonic Boom, Seismic Toss and Super Fang do 0 to Shuppet, Duskull and Sableye (SI:10627, 10147, 8977). Night Shade does 0 to Normal types such as Skitty, Whismur and Taillow (SI:8767, 10417, 8437).
  - The script clears the super- and not-very-effective flags, and the fixed value overwrites the stale damage. So there is no type multiplier and no STAB (the STAB at 1369-1373 multiplies the stale value).
- **Wonder Guard:** all four moves have power 1 (MV:643, 1072, 2112, 903, 1319), so Wonder Guard blocks them unless they are super-effective (BSC:1409-1419).
- **Abilities that do not apply:**
  - Levitate: Ground moves only (1375).
  - Soundproof: none of these are sound moves (BU:690-691).
  - Volt Absorb, Water Absorb, Flash Fire: none of these types (BU:2667-2715).
  - Magic Coat: none of these moves carry the Magic Coat flag.
- **Substitute:** the damage goes to the Substitute and anything beyond its HP is lost. The target's HP does not change (BSC:1865-1892).
- **Protect / Detect:** the move is stopped (macro at BSC:57; checks at 992-1002 and 1123). All four moves are affected by Protect.
- **Semi-invulnerable target** (Fly, Dig, Dive, Bounce): the move misses (1062-1085), unless the attacker has Lock-On or Mind Reader active (1056).
- **Accuracy modifiers:**
  - Stat stages (1128-1142); Foresight ignores the target's evasion.
  - Compound Eyes ×1.3 (1152).
  - Sand Veil in a sandstorm ×0.8 (1154).
  - Hustle ×0.8 on physical types (1156).
  - BrightPowder / Lax Incense (1172-1173).
  - Minimize raises evasion by 1 in Gen 3 (BS1:1476-1480).
- **Endure / Focus Band:** these cap the damage at hp − 1, and only when damage ≥ hp (BSC:5861-5899). They apply to Seismic Toss, Night Shade, Sonic Boom and Dragon Rage. They do not apply to Super Fang, whose script has no `adjustsetdamage` (BS1:809-817).
- **Randomness:** these scripts have no `critcalc` or `damagecalc`, so there is no critical hit and no random roll.
- **Result:** damage is always one of {X, 0, hp − 1}, and X is never exceeded.

**D3. Side effects that hit us, not the target — VERIFIED.**
- Seismic Toss and Super Fang make contact, so the target's contact abilities fire on us (BU:2753-2855):
  - Static: we may be paralysed.
  - Poison Point, Flame Body, Effect Spore: we may be poisoned, burned or slept.
  - Rough Skin: we lose 1/16 of our max HP.
  - Cute Charm (Skitty, SI:8783): we may be infatuated, 1 in 3.
- The target's Counter returns 2× the physical damage it took (BSC:7943-7952). Night Shade is Ghost-type, which is physical in Gen 3, so it can be Countered. This threatens our HP, not the target's.

## (3) Status moves

**S1. The complete lists — VERIFIED.**
- Sleep moves:
  - Sing: Normal, 55%, sound (MV:614).
  - Sleep Powder: Grass, 75% (MV:1030).
  - Hypnosis: Psychic, 60% (MV:1238).
  - Lovely Kiss: Normal, 75% (MV:1849).
  - Spore: Grass, 100% (MV:1914).
  - GrassWhistle: Grass, 55%, sound (MV:4163).
  - Yawn: delayed sleep (MV:3656).
- Paralysis moves:
  - Thunder Wave: Electric, 100% (MV:1121).
  - Stun Spore: Grass, 75% (MV:1017).
  - Glare: Normal, 75% (MV:1784).
- All of these can be stopped by Protect and bounced by Magic Coat (flags, e.g. MV:624, 1131, 1248, 4173).

**S2. The sleep script, in order (BS1:284-298):**
1. Soundproof (attackcanceler BSC:932 → BU:2645-2660).
2. Substitute (288).
3. Already asleep (289).
4. Uproar, Insomnia or Vital Spirit (290 → BSC:6828-6848 and 6801-6826).
5. Any existing status (291).
6. Accuracy and Protect (292).
7. Safeguard (293).

There is no `typecalc` in this script, so there is no type immunity.

**S3. The paralysis script, in order (BS1:1007-1025):**
1. Limber (1011).
2. Substitute (1012).
3. `typecalc` (1013-1014).
4. Already paralysed (1015).
5. Any existing status (1016).
6. Accuracy (1017).
7. Safeguard (1018).

**S4. Verdicts on the spec's skip list and the other conditions the brief asked about:**

| Condition | Verdict | Evidence |
|---|---|---|
| Insomnia / Vital Spirit (sleep) | VERIFIED. Shuppet has Insomnia. | BSC:6836-6837; BS1:2455-2456; SI:10643 |
| Limber (paralysis) | VERIFIED | BS1:1011 |
| Safeguard | VERIFIED | BS1:293, 1018, 2458 |
| Substitute | VERIFIED | BS1:288, 1012, 2457 |
| Soundproof vs Sing / GrassWhistle | VERIFIED. Wild Whismur has Soundproof. | BU:690-691; SI:10433 |
| Thunder Wave vs Ground | VERIFIED: Electric is ×0 vs Ground | BM:356 |
| Thunder Wave vs Electric type | **Not immune in Gen 3.** Electric vs Electric is ×0.5, and no type test exists in the script or in SetMoveEffect. Volt Absorb does not block it either (needs power ≠ 0). | BM:354; BS1:1007-1025; BSC:2395-2426; BU:2668 |
| Glare vs Ghost | VERIFIED, with a nuance: Foresight on the target removes the immunity | BM:445-446; BSC:1388-1391 |
| Powders vs Grass | **No immunity in Gen 3.** No `typecalc` for sleep, and no Grass ×0 row. Hypnosis also works on Dark types. | BS1:284-298; BM chart |
| Own Tempo | Not relevant: blocks confusion only | BS1:907; BU:2871-2876 |
| Shield Dust | Not relevant: blocks only secondary effects, and status moves apply as primary effects | BSC:2253-2255; BS1:297, 1022 |
| Synchronize | Passes back poison, toxic (as poison), paralysis and burn, **never sleep**. Thunder Wave / Stun Spore / Glare on Abra, Ralts or Natu paralyses our mon, unless our mon has Limber. Costs us only; prefer sleep against these targets. | BSC:2503-2511, 2962-2963; BSC:4275-4279; BU:2957-2971; SI:1923, 11093, 5343; BSC:2396-2421 |
| Taunt (on our mon) | VERIFIED: status moves cannot be selected | BU:1110-1111 |

**S5. Status gaps the spec's skip list misses — all VERIFIED:**
- **Uproar.** If any battler is in an Uproar (ours or theirs), sleep fails, unless the target has Soundproof (BSC:6801-6826). A target that is already asleep is woken at end of turn by an active Uproar (BU:1621-1638) and at its own move (BU:2004-2011). Whismur learns Uproar at L5 (our `modules/data/species.json`: move 253 = MOVE_UPROAR, `include/constants/moves.h:257`), and the spec's Step 12 fixture party (Mudkip, Poochyena, Nincada, Whismur) includes Whismur.
- **Already statused.** A target with any status cannot be slept or paralysed (BS1:291, 1016). A paralysed target cannot be put to sleep.
- **Magic Coat.** If the target used Magic Coat that turn, our status move is bounced onto us (BSC:962-969).
- **Sleep length.** The counter is set to 2-5 (BSC:2481) and drops at the sleeper's move attempt (BU:2020-2023), so the target sleeps 1-4 of its own turns.
  - Early Bird drops it by 2 (BU:2016-2017; Natu SI:5343).
  - Shed Skin cures any status with 1-in-3 chance each end of turn (BU:2606-2626).
  - Snore and Sleep Talk still work while asleep (BU:2026).
- **Yawn** never misses except against Protect or a semi-invulnerable target (BS1:2459; BSC:1103-1110). It fails if the target is already drowsy or has a status (BSC:9352-9363). Sleep lands at end of the next turn (BU:1749-1764).

## (4) Hazard floor

**H1. Ghost Curse costs the user max_hp//2 + 1 — VERIFIED.**
- Cost is the user's max HP / 2, minimum 1 (BSC:8477-8479). The script applies it to the user and can knock the user out (BS1:1511-1530).
- Only a Ghost-type user pays HP (BS1:1483).
- Nuance: Curse fails with no HP cost if our mon is already cursed (BSC:8470-8473) or behind a Substitute (BS1:1518). So it costs HP at most once per our active mon; a new mon of ours can be cursed again.
- Shuppet learns Curse at L20 and Duskull at L34 (our species.json; move 174 = MOVE_CURSE).

**H2. Recoil — VERIFIED, with one refutation.**
- 1/4 of the HP dealt: Take Down, Submission, Struggle (BS1:897-901).
- 1/3 of the HP dealt: Double-Edge, Volt Tackle (BS1:2567-2569).
- Minimum 1 in both cases (BSC:2636-2639, 2843-2846).
- "HP dealt" is capped at our mon's current HP (BSC:1920-1928) or its Substitute's HP (1868-1882). So the spec's "recoil from our own current HP" is correct.
- **REFUTED for Struggle:** Rock Head blocks recoil (BS1:3940), but Struggle skips that check (BS1:3939). So "Rock Head → floor 1" does not hold for Struggle.
- Nuance: the bound holds per hit. It adds up across throw turns and resets when our mon changes.

**H3. Crash damage (Jump Kick, Hi Jump Kick) — NUANCED: it is bounded, not unbounded.**
- Moves: MV:341, 1771; script BS1:849-869.
- On a miss (including our Protect, a semi-invulnerable target, or evasion), crash damage = half the damage it would have done, minimum 1, **capped at our mon's max HP / 2** (BSC:6747-6752).
- No crash if our mon is immune by type (BS1:859).
- Treating it as "unbounded" is conservative, not wrong. Meditite learns Hi Jump Kick at L32 (species.json).

**H4. Rampage (Thrash, Petal Dance, Outrage) — VERIFIED as a hazard.**
- Moves: MV:484, 1043, 2603.
- The user is locked in for 2-3 turns, then confuses itself (BU:1670-1684).
- A confused mon hits itself half the time, with a power-40 attack against itself (BU:2142-2162). This can knock it out.

**H5. Sandstorm / hail chip — VERIFIED; the exact bound is known.**
- Damage per end of turn: max HP / 16, minimum 1 (BSC:7602-7652).
- Sand immunity: Rock, Steel or Ground type, Sand Veil, underground, or underwater (7608-7616).
- Hail immunity: Ice type, underground, or underwater (7629-7631).
- No chip at all if Cloud Nine or Air Lock is on the field (`include/battle_util.h:47`).
- It hits every turn, including throw turns, and ignores Substitute (BS1:3200-3224).
- No chip on the turn a temporary storm ends (BU:1373-1377, 1411-1415).
- Route 111's overworld sandstorm is permanent in battle (BU:2492-2499; `constants/battle.h:236-238`).
- Hail never comes from overworld weather; the overworld only supplies rain, sand or drought (BU:2479-2510).

**H6. Route 111 / Cacnea — VERIFIED.**
- `wild_encounters.json` `gRoute111` land Pokémon: Baltoy, Cacnea, Sandshrew, Trapinch.
- Cacnea is Grass type with Sand Veil as its only ability (SI:9637, 9653).
- Baltoy is Ground/Psychic (SI:8857), Sandshrew is Ground (SI:827), Trapinch is Ground (SI:9277).
- Nuance: W39's "Cacnea without Sand Veil" row is synthetic. That case cannot happen in Gen 3.

**H7. Weather moves — VERIFIED.**
- Sandstorm and Hail set 5 turns of weather (BSC:7595-7597, 9064-9066) and fail if that weather is already active (7588, 9057).
- Rain Dance and Sunny Day do no chip damage (BU:1336-1407).
- Additional fact: Rain Dance overwrites the weather (BSC:6690), so it also ends even a permanent sandstorm.

**H8. Spikes are no hazard to a wild target — VERIFIED.**
- Spikes damage fires only on a switch-in (BSC:5229-5245), and a wild target never switches in.
- This also settles one of the spec's UNVERIFIED items: **there are no wild double battles in Emerald.** No wild-battle start sets the double-battle flag (BSET:402-494, 505-576).

**H9. Explosion / Self-Destruct vs Damp — VERIFIED.**
- It fails only if **any** battler has Damp, including the user or our mon (BSC:6538-6557).
- Otherwise the user faints before the accuracy check (BS1:379-380 vs 394), so it faints even on a miss, against Protect, or against a Ghost.
- Geodude learns Self-Destruct L21 and Explosion L41; Baltoy learns them at L19 and L45 (species.json).

**H10. Our Liquid Ooze — NUANCED: bounded.**
- When the target drains us (Absorb, Mega Drain, Giga Drain, Leech Life), it loses half the HP it drained, minimum 1 (BS1:343-349; BSC:6925-6931).
- When the target's Leech Seed is on us, the target loses min(our max HP/8, our HP) each end of turn (BU:1505-1518; BS1:3265-3284).
- Dream Eater has no Liquid Ooze check (BS1:425-462).

**H11. Our Rough Skin — NUANCED: bounded.** The target loses 1/16 of its own max HP, minimum 1, per contact hit on us (BU:2753-2766).

**H12. Our Poison Point, Flame Body, Effect Spore — VERIFIED as hazards.**
- On contact, the target may be poisoned or burned: Poison Point and Flame Body 1 in 3, Effect Spore 1 in 10 (sleep, poison or paralysis) (BU:2768-2835).
- Poison or burn then ticks for max HP/8 each end of turn (BU:1521-1556).
- Blocked on the target by Poison or Steel type, or Immunity (BSC:2300-2340), and by Fire type or Water Veil (BSC:2341-2379).
- Static only paralyses, which is harmless to the target (BU:2807-2821).

**H13. Our Synchronize — VERIFIED as a hazard.** If the target poisons, burns or paralyses us, it gets the same status (toxic becomes plain poison) (BSC:4275-4279; BU:2957-2971). Only the poison and burn cases tick damage.

**H14. Struggle — VERIFIED.**
- It has no type (BSC:1360-1364), so it can hit Ghosts.
- It is picked only when all the target's moves are unusable (BM:4184; BU:1082-1139).
- The wild's random move pick does not check PP (BCO:1597-1601); picking a 0-PP move just wastes its turn (BSC:934-940).
- Our Pressure doubles its PP use (BSC:1224-1225).

**E1. Battle enders — all VERIFIED.**
- **Teleport** (BS1:1925-1938): fails in trainer battles (1929) and when the target cannot escape (BM:4043-4077):
  - our Shadow Tag;
  - our Arena Trap, unless the target is Flying or has Levitate (Trapinch can have Arena Trap, SI:9293);
  - our Magnet Pull against a Steel target;
  - Mean Look, Block or Spider Web;
  - a Wrap-family move;
  - its own Ingrain.
  - Smoke Ball or Run Away overrides all of these (BM:4034-4039).
  - Abra learns Teleport at L1.
- **Roar / Whirlwind** (BS1:593-602, 3324-3332): always works if the target's level ≥ our level; otherwise a level-weighted roll can make it fail (BSC:7164-7183). Blocked by our Suction Cups or our Ingrain (597-598). Our Soundproof blocks Roar only.
- **Perish Song** (BSC:8508-8526): only a Soundproof battler is exempt. Our Soundproof (Whismur) protects only us; the target still faints after 3 turns.
- **Memento** (BSC:9072-9090; BS1:2204-2249): the user faints even against our Protect or Substitute. It fails only if both our Attack and Special Attack are already at −6 and we did not Protect.
- **Metronome** (BSC:7885-7923): can call any move except the 15 on its forbidden list (725-746).

**What the spec misses:**
- **M1. Encore forces our last move.**
  - If the target's Encore is on us, any move we select becomes our last move (BM:4192-4197). An exact-damage move would hit again and can cross the floor or knock the target out.
  - Item throws use a separate action path (BM:4221), so throwing a ball still works.
  - Wynaut learns Encore at L1, and Counter, Mirror Coat, Safeguard and Destiny Bond at L15 (species.json; IDs checked in `include/constants/moves.h`).
- **M2. Sleep Talk.**
  - A sleeping target can still use its other moves (BU:2026; BSC:8209-8219, 8241-8257), including Explosion, Memento, Teleport, Roar, Perish Song, Curse and recoil moves.
  - So the "knows X" checks must not be skipped while the target is asleep.
- **M3. Our pending Future Sight or Doom Desire** lands on the target 2 turns later (BSC:8931-8940; BU:1798-1799). It is not in the spec's "ticking" list.
- **M4. The floor must hold for the whole battle, not one turn.**
  - The ball goes before the target each turn (BM:4819-4824). But after a failed throw, the target acts and end-of-turn effects run again.
  - So every per-turn hazard repeats on each throw turn: weather chip, recoil, and Curse on a fresh mon of ours.
- **M5. Things that cannot knock the target out** (do not refuse on these):
  - Substitute needs hp > max HP/4 (BSC:7808-7830).
  - Belly Drum needs hp > max HP/2 (8785-8806).
  - Pain Split sets both to the average, which is at least 1 (8049-8071).
- **M6. Ordinary wild Pokémon never flee on their own.**
  - The switch and item AI runs only for trainers (BAI:541). The AI that can flee runs only for trainer, first, Safari and roamer battles (BCO:1563-1576).
  - An ordinary wild picks one of its known moves uniformly at random each turn (BCO:1597-1608).
- **M7. Color Change can make a type check stale.** Kecleon changes type after a damaging hit (BU:2738-2751), so a type-based immunity decided before the hit may no longer hold.

## Cross-checks against our code (secondary)

- **`calculate_catch_success_chance` is wrong for high odds.** It has no `odds > 254` branch (`sandbox-pokebot/modules/battle_strategies/_util.py:285-294`). For large odds it returns more than 1; for example, odds 1000 gives about 4.47. Do not reuse it.
- **`dex_catch_expected_throws` matches the game at full HP** (`plugins/custom_modes/story_mode.py:1777-1784`).
- **`_BALL_BONUS_X10` knows only 4 balls** (`story_mode.py:1703`); every other ball defaults to 10. That is conservative for estimating throws, but not exact for `catch_p`.
- **`catch.py` multipliers** (`modules/battle_strategies/catch.py:235-277`) match the decomp for Nest, Dive and Repeat. Two differences:
  - Net Ball uses the species types; the game uses the battler's current types.
  - Timer Ball uses `battle_state.current_turn`, but the game uses `battleTurnCounter`. UNVERIFIED whether they are equal.
- **The damage calculator ignores type immunity for fixed-damage moves.** `_util.py:204-228` returns the fixed value by move name, after the type step and without a zero check. So it reports level damage for Night Shade against a Normal type, and 20 / hp//2 / level against a Ghost, where the game deals 0. That is safe for knockout checks but overstates progress and E-gain.
- **`moves.json` matches the decomp.** Its effect, type, accuracy, contact and sound fields agree for the exact-damage moves (lines 1718, 2418, 2873, 3538, 5673) and the key status moves (1648 Sing, 3013 Thunder Wave, 4798 Glare, 11203 Grasswhistle), so dispatching on effect is supported by our data.
