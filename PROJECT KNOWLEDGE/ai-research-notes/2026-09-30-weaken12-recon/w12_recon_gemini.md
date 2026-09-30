# 2026-09-30 — design v2 step 12 (weaken-to-catch) recon: a Gemini fan-out, validated against the decomp by a Claude agent

⚠ **A NOTE, NOT TRUTH.** A Claude recon agent's report (model output), verbatim. Every load-bearing claim is re-checked by the author at its FILE:LINE before the design relies on it; the design note records which.

# Step 12 (W, weaken-to-catch): Gemini fan-out, checked against pret/pokeemerald

This is a NOTE, not a source of truth. Decomp files were fetched with `gh api` from pret/pokeemerald master today.

**How it ran.** I sent four Gemini prompts, one per question, in parallel, with no `--model` flag (default `gemini-3.1-pro-preview`). The worktree has no gitignored `sandbox-pokebot/profiles/gemini.key`, so the first run failed with "No API key". I ran the main checkout's relay instead: `diff -q` shows it is byte-identical, and it resolves its own key. I never read or printed the key.

Raw Gemini output: `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/gem/gemini_weaken_q{1,2,3,4}.md`

## Error rate (my tally of claims I checked)

About 187 claims checked, 48 wrong, roughly 26%.

| Area | Checked | Wrong | Notes |
|---|---|---|---|
| Q1 move effects | 43 | 12 | 6 wrong facts, 6 wrong or invented names |
| Q2 abilities | 41 | 9 | 3 of these say "30%" where the game uses 1/3 |
| Q3 hold-effect constants and values | 20 | 1 | |
| Q3 which wild species hold which item | 34 | 18 | 53%; Gemini's weakest area |
| Q3 berry mechanics | 4 | 1 | plus one invented script name |
| Q4 sleep and paralysis | 45 | 6 | |

This fits the standing rule: names are mostly usable, data and "why it matters" advice are not. About 11 names were invented or wrong.

## WRONG, with the correct fact

**Q1, move effects**
- Double-Edge is `EFFECT_DOUBLE_EDGE`, recoil 1/3 (battle_moves.h:497; battle_scripts_1.s:2567-2568; battle_script_commands.c:2843-2846). It is not `EFFECT_RECOIL` at 1/4.
- Volt Tackle is `EFFECT_DOUBLE_EDGE` with a secondary chance of 0 (battle_moves.h:4475). Gen 3 Volt Tackle has no paralysis chance. Gemini gave it as `EFFECT_RECOIL` in Q1 and as `EFFECT_PARALYZE_HIT` 10% in Q4.
- `EFFECT_FLY`, `EFFECT_DIG`, `EFFECT_DIVE` and `EFFECT_BOUNCE` do not exist. All four moves use `EFFECT_SEMI_INVULNERABLE` (battle_move_effects.h:159; battle_moves.h:250, 1186, 3786, 4423).
- "Dig/Dive dodge Poké Balls" is wrong. `BattleScript_BallThrow` (battle_scripts_2.s:50-53) goes straight to `handleballthrow`, and battle_script_commands.c:9905-10050 has no Substitute or semi-invulnerable test. This agrees with the spec's [G-N4].
- Belly Drum cannot make the user faint. It needs `hp > maxHP/2` and Attack below +6, then subtracts maxHP/2 (battle_script_commands.c:8787-8796).
- Soft-Boiled and Milk Drink are `EFFECT_SOFTBOILED` (battle_moves.h:1760, 2709), not `EFFECT_RESTORE_HP`. The heal of 1/2 is correct (6615-6625).
- Morning Sun, Synthesis and Moonlight heal 20/30 (2/3) in sun, not 100% (battle_script_commands.c:8873).
- Dream Eater has no Liquid Ooze check (battle_scripts_1.s:453-462). The Absorb family does (345), and so does Leech Seed (3271).
- `EFFECT_AROMATHERAPY` does not exist. Aromatherapy is `EFFECT_HEAL_BELL` (battle_moves.h:4061).
- Gemini said a wild Roar "fails if the wild is lower level". In fact, if the attacker's level is at least the target's, it always succeeds. Otherwise it fails only when `(rand*(atkLv+defLv)>>8)+1 <= defLv/4` (battle_script_commands.c:7166-7177), so a lower-level wild's Roar usually still works.

**Q2, abilities**
- Effect Spore triggers 10% of the time, not 30% (`Random()%10==0`, battle_util.c:2774). Sleep, poison and paralysis each get 1/3 of that (2779-2783).
- `ABILITYEFFECT_CONTACT` does not exist. The case is `ABILITYEFFECT_ON_DAMAGE` (include/battle_util.h:16).
- Static, Flame Body, Poison Point, Cute Charm and Shed Skin all trigger at 1/3, not 30% (battle_util.c:2813, 2828, 2798, 2844, 2607).
- Volt Absorb does not absorb Thunder Wave. It requires `power != 0` (battle_util.c:2668). The same mistake appears in Q4.
- `CheckSoundMove` does not exist. The list is `sSoundMovesTable` (battle_util.c:688-692).
- Shield Dust lives in `SetMoveEffect` at battle_script_commands.c:2253, not in battle_util.c. The fact itself is correct.
- `WEATHER_*_PERMANENT` is not a real name. The constants are `B_WEATHER_*` (include/constants/battle.h:232-243).

**Q3, held items**
- Cheri's constant is `HOLD_EFFECT_CURE_PAR` (hold_effects.h:6).
- HP berries do NOT heal mid-turn. `HOLD_EFFECT_RESTORE_HP` requires `!moveTurn` (battle_util.c:3323) and only runs at the end of the turn (1496).
- `BattleScript_ChestoBerryAwakes` does not exist. The script is `BattleScript_BerryCureSlpRet` (battle_scripts_1.s:4314). Chesto does cure on the same turn, at MOVE_END (battle_script_commands.c:4331; battle_util.c:3663-3670).
- Wrong species/item claims:

| Gemini said | Actually (species_info.h) |
|---|---|
| Zigzagoon holds Oran 50% | 5% (:7967) |
| Sitrus is held by no wild | Linoone 5% (:7997) |
| Shuckle holds Berry Juice | Oran Berry 100% (:6416-6417) |
| Whismur and Loudred hold Chesto 50% | 5% (:10427, :10457) |
| Exploud holds Chesto 50% | Exploud is not a wild encounter |
| Wurmple holds Pecha and BrightPowder | Wurmple holds nothing (:8009) |
| Vulpix and Numel hold Rawst 50% | 100% (:1136-1137, :9496-9497) |
| Vulpix holds Charcoal 5% | Rawst 100% |
| Kecleon and Girafarig hold Persim 50% | 5% (:8837, :6117) |
| Skitty holds Leppa 50% | 5% (:8777) |
| Lotad/Lombre hold Mental Herb | nothing |
| Machop/Machoke hold Focus Band | nothing |
| Nincada holds Soft Sand | nothing |
| Geodude/Graveler hold Hard Stone | Everstone (:2247, :2277) |

- The wild item rolls are 45% none, 50% common, 5% rare. If the common and rare item are the same, the chance is 100%. A Compound Eyes lead changes this to 20/60/20 (pokemon.c:6684-6691, 6715-6718).
- Gemini missed: Spinda Chesto 5% (:8567), Poochyena/Mightyena Pecha 5% (:7907, :7937), Koffing Smoke Ball 5%, Pikachu Light Ball 5%. Miltank holds Moomoo Milk 100%, but that item has no hold effect (items.h:390-401).

**Q4, sleep and paralysis**
- The catch status bonus is in `Cmd_handleballthrow` at battle_script_commands.c:9991-9994. There is no `statusBonus` variable and it is not in pokemon.c. The values (×2 sleep/freeze, ×1.5 others) are correct.
- Bounce is `EFFECT_SEMI_INVULNERABLE`; its paralysis is set at battle_scripts_1.s:2003-2004. Thunder is `EFFECT_THUNDER` (battle_moves.h:1134).
- Secret Power on ordinary grass inflicts POISON. Only long grass inflicts sleep; the fallback is paralysis (battle_script_commands.c:9623-9627, 9647-9648). The code is not in battle_util.c.

## CONFIRMED (the facts the plan depends on)

**Self-damage, faint and ending effects**
- Struggle: recoil 1/4 of damage dealt, and Rock Head does not stop it (battle_scripts_1.s:3939-3940).
- Normal recoil (`EFFECT_RECOIL`, 1/4 of `gHpDealt`) and Double-Edge-style recoil (1/3): Rock Head does stop these. Both recoils are at least 1 HP (battle_script_commands.c:2636-2638, 2843-2846).
- Crash moves: Rock Head does not stop crash damage. Crash damage is half the damage the move would have done, capped at the target's maxHP/2 (battle_script_commands.c:6747-6752). There is no crash damage against an immune target (battle_scripts_1.s:859).
- Explosion/Self-Destruct fails if any battler has Damp (battle_script_commands.c:6543-6547). Explosion halves the target's Defense (pokemon.c:3229-3230).
- Memento makes the user faint, but fails if our Attack and Sp. Atk are both at −6 (battle_script_commands.c:9072-9089).
- Substitute costs 1/4 max HP and fails at HP ≤ 1/4 (battle_script_commands.c:7810-7814).
- Ghost Curse costs the user maxHP/2 and can make it faint. It is decided by the user's type when used (battle_scripts_1.s:1483) and fails against a target behind a Substitute (1518; battle_script_commands.c:8477).
- Teleport ends a wild battle, except when it is a trainer battle or the wild is trapped (battle_scripts_1.s:1925-1937; battle_main.c:4021-4084).
- Roar ends a wild battle (battle_scripts_1.s:3330-3331). Suction Cups and Ingrain block it (597-598). Roar is in the sound-move list (battle_util.c:690), so a Soundproof lead also blocks it.
- Perish Song does not affect a Soundproof battler (battle_script_commands.c:8516).
- Baton Pass and Assist fail in the wild because the wild party is zeroed (wild_encounter.c:383; battle_script_commands.c:9496-9503).

**Healing and chip damage**
- Rest heals fully and sets sleep turns to 3, which means 2 turns asleep (battle_script_commands.c:6779).
- Recover heals 1/2; Wish heals 1/2; Ingrain heals 1/16 (battle_util.c:1482); Leech Seed drains 1/8 (1512); Pain Split averages HP; Swallow heals max HP ÷ (1 << (3 − stockpile)) (6912); Refresh cures poison, burn and paralysis.
- Sandstorm chip is 1/16. Rock, Steel and Ground types are immune, and so are Sand Veil and a target underground or underwater (battle_script_commands.c:7608-7616). Hail chip is 1/16; Ice types and underground/underwater targets are immune. Cloud Nine or Air Lock stops weather chip (include/battle_util.h:47).
- Overworld weather gives only rain, sand or sun (battle_util.c:2479-2510), so hail can come only from the Hail move (1408-1414).

**Abilities**
- Sturdy only blocks one-hit-KO moves (battle_script_commands.c:7513).
- Synchronize passes back poison, toxic (as poison), paralysis and burn, but not sleep (2502-2511).
- Rough Skin deals 1/16 of the attacker's max HP (battle_util.c:2760).
- Infatuation stops the attacker 50% of the time (battle_util.c:2190). Early Bird counts sleep down by 2 (2016-2019). Snore and Sleep Talk still work while asleep (2025).
- Lightning Rod only redirects; it gives no immunity (161-169). Sand Veil reduces accuracy ×0.8 in sand (battle_script_commands.c:1154).
- Guts, Marvel Scale and Thick Fat: pokemon.c:3211, 3213, 3203.
- Shadow Tag, Arena Trap and Magnet Pull trap as expected (battle_main.c:4043-4071).
- Snow Cloak does not exist in Gen 3 (abilities.h has 78 abilities, the last being Air Lock).

**Sleep and paralysis**
- Sleep lasts a counter of 2-5 (battle_script_commands.c:2481). Yawn puts the target to sleep at the end of the next turn (9361; battle_util.c:1749-1762).
- `EFFECT_SLEEP` has no type check (battle_scripts_1.s:284-298). `EFFECT_PARALYZE` does (1013-1014), which is why Thunder Wave fails on Ground and Glare fails on Ghost.
- Electric types are not immune to paralysis in Gen 3 (battle_script_commands.c:2395-2425).
- Insomnia and Vital Spirit block sleep and Yawn (6836-6837; battle_scripts_1.s:2455-2456).
- Substitute, Safeguard and an existing status block both sleep and paralysis moves.
- Tri Attack's secondary picks burn, freeze or paralysis at 1/3 each (battle_script_commands.c:2601).
- Every sleep and paralysis move's accuracy and PP in Gemini's table matched battle_moves.h.

**Items**
- Oran heals 10, Sitrus 30, Berry Juice 20; pinch berries heal 1/8. All trigger at HP ≤ 1/2 (items.h:1704, 1747, 588; battle_util.c:3213-3219).
- Chance items: Focus Band 10% (battle_script_commands.c:5878), Quick Claw 20% (battle_main.c:4653), BrightPowder ×0.9 and Lax Incense ×0.95 accuracy (battle_script_commands.c:1172-1173), King's Rock 10%, Shell Bell 1/8 of damage dealt, Leftovers 1/16.

## Gaps and leads not handled by spec §Step 12

**Movesets used below.** I computed each wild's moveset from its last 4 level-up moves (`GiveBoxMonInitialMoveset`, pokemon.c:2991-3011) across every wild_encounters.json level. Battle Pike and Pyramid are excluded. Static encounters (legendaries, roamers, Aqua Hideout Electrode, Kecleon and Sudowoodo statics) are NOT covered.

1. **Belly Drum is missing from the hazard floor. This is the one gap that affects safety.** The target pays maxHP/2 whenever its HP is above 1/2 (battle_script_commands.c:8792-8796). That is exactly the "damage while above 50%" window. If the target moves first, our exact-damage hit lands on HP − maxHP/2. Wild Hariyama at L40-42 in Victory Road knows it (level_up_learnsets.h:4454). Pain Split, which Gemini also named, is known by no wild.

2. **Uproar is missing from the status skip list.** During an Uproar, sleep fails unless the target itself has Soundproof (battle_script_commands.c:6801-6826, 6828-6843, 2273-2290). An Uproar lasts 2-5 turns (2573). Spinda L14-16 on Route 113 and Chimecho L28 at the Mt Pyre summit are affected; Whismur (Soundproof) is not. Our reader already exposes Uproar (battle_state.py:124-125).

3. **The spec says nothing about the target's own held item.**
   - Chesto (Whismur, Loudred, Spinda, 5%) cures sleep on the same turn. This wastes status tries; the 3-try cap limits the cost.
   - HP berries heal once, at the end of the turn, when HP ≤ 1/2: Linoone (Oran 50%, Sitrus 5%), Zigzagoon Oran 5%, Pikachu Oran 50%, Shuckle Oran 100%. This undoes some progress but cannot cause a faint.
   - A Compound Eyes lead makes these rare items 4× as likely. The fixture party's Nincada has Compound Eyes (inferred).
   - The item is already readable (battle_state.py:662-667, offset +0x2E).

4. **Transform (Ditto L38-45, Desert Underpass).** Transform copies species, moves, ability and types, and sets each move's PP to 5 (battle_script_commands.c:7790-7798; pokemon.h:260-281). The catch rate is then read from the copied species (9935), while personality stays unchanged. So throw-only and immunity checks need a fresh read every turn. An identity check that reads the battle species will see a "different" foe.

5. **Our code: `battle_state.py` `.ability` (565-570) is worked out from the species and a stored ability bit, while the game checks the live ability byte at +0x20 (`ability_n`, 573-574).** After Trace these differ (wild Ralts L4 on Route 102, a rare species). Immunity gates should read +0x20. The impact is my inference.

6. **Exact-damage moves go through the type check** (battle_scripts_1.s:1200, 1725, 824, 814).
   - Sonic Boom, Super Fang and Seismic Toss do 0 to Ghost types; Night Shade does 0 to Normal types.
   - This is not a safety risk, but the log would show a predicted 20 against an actual 0, and the turn is wasted.
   - Seismic Toss and Super Fang make contact (battle_moves.h:900, 2109), so the target's contact abilities hit our lead.
   - These moves have power 1, which triggers Kecleon's Color Change (battle_util.c:2741).

7. **The out-of-balls flee can fail.** This is the W-b row "0 balls → flee" (battle_main.c:4043-4077). Whether the parent handles "can't escape" is unverified. Causes:
   - Shadow Tag: Wynaut on Route 130, Wobbuffet in the Safari Zone.
   - Arena Trap: Trapinch on Route 111 and in Mirage Tower.
   - Magnet Pull, against a Steel lead only.
   - The target's Mean Look or Block: Golbat and Zubat in Victory Road, Nosepass.
   - The target's trapping moves: Seviper, Shuckle, Tentacool and Tentacruel (Wrap); Pinsir (Bind); Clamperl (Clamp); Clamperl, Wailmer and Wailord (Whirlpool); Solrock and Torkoal (Fire Spin).

8. **Several spec rows can never happen with natural wild movesets, so they can only be tested in the pure gate.**
   - No wild knows Memento, Perish Song, Metronome, Mirror Move, Assist, Sleep Talk, Magic Coat, Substitute, Minimize, Spikes, Heal Bell, any semi-invulnerable move or any crash move.
   - The only rampage user is Gyarados (Thrash, Sootopolis fishing).
   - The only wild Sandstorm user (Claydol) and Hail user (Spheal) are immune to their own weather, so W40 never fires naturally.
   - Rows that can happen:

     | Hazard | Wilds |
     |---|---|
     | Teleport | Abra L7-10, Natu, Xatu |
     | Explosion / Self-Destruct | Baltoy L19-21 (Route 111), Geodude, Graveler, Claydol, Pineco |
     | Ghost Curse | Shuppet L22-30, Banette |
     | Roar / Whirlwind | Poochyena/Mightyena L25-28, Whismur L35-38, Aron/Lairon, Houndour, Snubbull, Makuhita/Hariyama, Tropius |

9. **Some hazards the spec treats as unbounded actually have a limit.** Crash damage is at most our maxHP/2; Rough Skin deals 1/16; sand and hail deal 1/16 per turn; Absorb-family Liquid Ooze equals half the damage dealt. Treating them as unbounded is conservative, not wrong.

10. **Status efficiency, not safety** (all affect the expected gain from each ball throw):
    - Shed Skin cures at 1/3 per turn (Seviper L15-17 on Route 114, Silcoon, Cascoon).
    - Early Bird shortens sleep (Seedot, Nuzleaf, Doduo, Natu, Girafarig, Houndour, Ledyba).
    - A target with Synchronize (Abra, Natu, Xatu, Ralts) passes paralysis back to our lead. Sleep is not passed back, so the spec's sleep-first order already avoids this.
    - Corsola's Refresh cures paralysis.

11. **Stage 2 (off) whitelist.** Secret Power on grass and Tri Attack's burn can leave a ticking status. Commit cdb49f83 already moved Secret Power to Tier B.

12. **An aside that settles one of the spec's UNVERIFIED items (§5).** No wild battle setup sets `BATTLE_TYPE_DOUBLE` (battle_setup.c:408, 427, 441, 451, 485, 493, 505, 517, 556, 576); doubles appear only for trainers (1275). So there are no wild doubles in Emerald. The flag assignments are read directly; that no other code path adds the flag is my inference.

**Spec facts re-confirmed along the way:** Damp on any battler; sand immunity at 7608-7616; Super Fang does at least 1 damage, which justifies the spec's "hp ≥ 2" rule (7579-7581); Sonic Boom 20 and Dragon Rage 40 (battle_scripts_1.s:1727, 826); level damage equals our level (7928); the sound-move list; a ball works through Substitute or semi-invulnerability.

**Files, all in the scratchpad above:**
- Decomp copies: `decomp/` and `mine/`
- Scripts: `parse_moves.py`, `q.py`, `hazmoves.py`
- Wild-species table: `wild_species.json`
