# 2026-09-30 — design v2 step 12: the DESIGN REVIEW (three lenses + refuters), verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (subagent returns). Each finding, its refuter verdict where one ran, and what each lens checked and found true. The design folds every confirmed finding (its REVIEW section).

# LENS safety

## safety:F1 [blocker] weaken12-DESIGN.md:102 (the Encore check runs only at decision time), :109 (a cap of 1 damage turn), :111-121 and :132-138 (STATUS and DAMAGE both choose Fight), :96-99 and :150 (DEFER and an exception hand the turn to the parent), :156-158 (D6 says BEFORE = gChosenMoveByBattler)
CLAIM: The design closes Encore only at SELECTION time. A target that knows Encore and moves first can Encore us in the same turn we choose any later Fight action (a STATUS retry after the target wakes, or the parent's status move after a DEFER). The game then runs our last-used move, which is the damage move, in place of the chosen one. A second X lands, although the whole KO bound assumes exactly one hit (hp − X ≥ 1, one damage turn). D6's instrument cannot see this: BEFORE would log the status move while the damage move ran.
EVIDENCE: - pret src/battle_util.c:111-117 (HandleAction_UseMove, at EXECUTION): if encoredMove is set and still known, gCurrentMove = gChosenMove = encoredMove. This overrides the chosen move of the same turn.
- src/battle_script_commands.c:8017-8045 (Cmd_trysetencore): encoredMove = gLastMoves[target].
- gLastMoves is written only at move end (battle_script_commands.c:4405-4408). It is reset only at battle start, on a switch-in and on a faint (battle_main.c:3053, :3222, :3314). Ball throws never clear it, so the damage move stays 'last' through every throw turn.
- The design verified only the selection-time path, battle_main.c:4192-4196 (design :57).
- dmgaudit.py:56 reads gChosenMoveByBattler. The execution override changes gChosenMove and gCurrentMove, not ...ByBattler.
- DEFER goes to the parent, which picks a status move when the target is Healthy and the chance is < 0.5 (catch.py:50-60). That is also a Fight action.
- Wilds that know Encore (my scan of wild_encounters.json × the last 4 level-up moves):
  - Spheal, Shoal Cave L25-30: Encore, Ice Ball, Body Slam, Aurora Beam (learnsets: Encore L7, Body Slam L19). Speed base 25 gives about 19-27. Body Slam's paralysis (×0.25) lets it outspeed a Mightyena or Marshtomp lead.
  - Wynaut, Route 130.
  - Shuckle, Altering Cave.
- Arithmetic: max 80, hp0 80, Dragon Rage X = 40 is admitted (40 ≥ 1). An Encore-forced second hit leaves 0 = KO.
- Reach today: it needs a lead that holds both an admissible damage move and a sleep/paralysis move (none in any fixture, w12_recon_fixture.md:40), or a DEFER after the damage turn. But the design's own open item (:214-215) proposes that kind of catching lead, and stage 2 widens the damage side to every Tier A hit.
FIX: - Make DAMAGE inadmissible against a target that knows EFFECT_ENCORE, as Explosion already is. Alternatively, after any damage turn force THROW for the rest of the battle; this also covers DEFER and D5's exception path.
- Add a W-row: damage turn done, target awake and knows Encore, status move available → THROW. Give it a fault arm that removes the rule.
- Instrument the EXECUTED move in the AFTER: gLastMoves[0] / gLastResultingMoves[0], set at bsc.c:4407-4408 from gChosenMove after the override. Pair it with the act.
VERDICT: refuted=False corrected=should-fix
REASONING: The mechanism is real, and the design does not close it structurally. But the blocker label does not hold. The finding's own concrete case (Spheal) is already closed by the design's rules. Across Emerald's wild data there is no instance any story lead can reach.

WHAT SURVIVES:
(1) The design checks Encore only at selection, as "our side is under Encore" (:102). In the same turn, an Encore that runs before our move replaces our chosen move with gLastMoves[us] at EXECUTION.
(2) gLastMoves is written only at move end, and a failed ball throw never reaches move end. So the damage move stays "last" through every throw turn.
(3) Neither the no-self-harm list (:122-128) nor THROW-ONLY (:101-110) mentions a target that knows Encore.
(4) The cap line (:109) does not say whether spending the 1-damage-turn cap makes EVERY later turn THROW-ONLY. v2 defined the caps per action (v2:732). So a STATUS retry after the damage turn is not excluded by the text.
(5) A DEFER or exception (:96-99, :150) hands the turn to the parent, which picks a sleep or paralysis move (catch.py:50-60, :186-210).
(6) D6's sentence "BEFORE records the move the game ACTUALLY chose" (:157) is false in this case. gChosenMoveByBattler is set at selection, and the execution override writes only gChosenMove and gCurrentMove.

WHY IT IS NOT A BLOCKER (no reachable KO):
(a) Every path needs a lead that holds a SLEEP or PARALYZE move. Both the design's STATUS and the parent's chooser use only those effects (catch.py:202-205). The design (:8-11) and the fixture recon (w12_recon_fixture.md:40-41) verify that no lead in any of the 66 fixture rows, and no story lead, has one. The only one is a slot-3 Skitty's Sing, and that Skitty never leads.
(b) Only three Emerald wilds know Encore. My scan (last 4 level-up moves over wild_encounters.json) found Spheal (Shoal Cave, L25-30), Wynaut (Route 130, L5-10) and Shuckle (Altering Cave, which is event-only, and Safari rock smash, which the design DEFERs at :97).
(c) Spheal is closed by the design's own rules. Its catch rate is 255. By the integer decomp formula with the worst ball (Poké Ball), the one-throw chance is 0.337 at full HP. Asleep it is 0.785 and paralyzed it is 0.503, both ≥ 0.5, so THROW-ONLY (:108). With a Great or Ultra Ball it is ≥ 0.503 even at full HP. STATUS is checked before DAMAGE, so DAMAGE on Spheal happens only when no status move or no status try is left. After that, the design has no STATUS to choose.
   - The parent (DEFER) picks a status move only when its float chance is < 0.5. On Spheal that means hp_after > 0.75 max.
   - A KO on the second hit needs X ≥ hp_after. That gives hp_before = hp_after + X > 1.5 max, which is impossible.
(d) Wynaut (base Speed 23; about 12 at L10; moves Splash, Charm, Encore) and Shuckle (base Speed 5) do not outspeed a late-game lead. Wynaut also has no way to paralyze it.
(e) No acting arm reaches it: W-EXEC is on Route 116, where no wild knows Encore, and Mudkip holds no sleep or paralysis move.

OVERSTATED: "the instrument cannot see this". dmgaudit's raw line also dumps both disable structs (dis=, which holds encoredMove at 0x06), plus Δbide and HP. A KO would still appear as res=Won, which is the design's primary safety readout (:160). Only the BEFORE move label would be wrong.

PROPOSED FIX: The first option, DAMAGE inadmissible against a target that knows EFFECT_ENCORE, is correct and covers every path. With it, our last move against such a target is never a damaging move. The alternative, forcing THROW after the damage turn, does NOT cover DEFER as the design's order stands: DEFER is checked first (:95-100), and the exception path also bypasses the pure module (:150). It needs the check placed ahead of both.

It remains a real defect with a bounded effect. The design claims B2 is closed (:20-23) and states the one-hit invariant as general (:129), yet the only protection here is incidental: catch-rate arithmetic and speed. The fix is one line. So should-fix.
V-EVIDENCE: DECOMP (local pret copy in the scratchpad decomp/):
- src_battle_util.c:111-117 (HandleAction_UseMove, at execution): if encoredMove != NONE and matches moves[encoredMovePos], then gCurrentMove = gChosenMove = encoredMove. This overrides the chosen move of the same turn.
- src_battle_script_commands.c:8017-8045 (Cmd_trysetencore): encoredMove = the target's move matching gLastMoves[target], if its PP != 0. There is no recency check.
- battle_scripts_1.s:1227-1237: Encore has only an accuracy check and trysetencore.
- src_battle_script_commands.c:4405-4408: gLastMoves = gChosenMove at MOVEEND_UPDATE_LAST_MOVES.
- The only other writes are resets, at src_battle_main.c:3053 (battle start), :3222 and :3314 (switch-in and faint).
- data_battle_scripts_2.s:94-103: BattleScript_ShakeBallThrow ends in finishaction, with no moveend, so a failed ball never changes gLastMoves.
- src_battle_main.c:4194 and :4399: gChosenMoveByBattler is set at SELECTION only. The execution override does not touch it.
- src_battle_controller_opponent.c (about :1563-1601): a wild mon picks MOD(Random(), 4) among its non-empty moves.
- src_battle_script_commands.c:9987-10030: the catch formula. Spheal catchRate 255 and baseSpeed 25; Wynaut baseSpeed 23 (src_data_pokemon_species_info.h:9544-9548, :10114-10118).
- Computed with integer sqrt, Poké Ball: full HP odds 85 → 0.337; paralysis 127 → 0.503; sleep 170 → 0.785. Great Ball at full HP: 127 → 0.503.

WILD SCAN (wild_encounters.json × the last 4 level-up moves), the only Encore knowers:
- SPHEAL, Shoal Cave, L25-30: Encore, Ice Ball, Body Slam, Aurora Beam;
- WYNAUT, Route 130, L5/10: Splash, Charm, Encore;
- SHUCKLE, gAlteringCave7 (event) and the Safari Zone rock-smash table.

OUR CODE (worktree pokebot-wt-ch24):
- sandbox-pokebot/modules/battle_strategies/catch.py:50-60 and :186-210: the parent chooses a status move only if the target is Healthy and the float chance is < 0.5, and only for the SLEEP or PARALYZE effects.
- sandbox-pokebot/modules/dmgaudit.py:56 reads gChosenMoveByBattler, :59 reads gDisableStructs, and :78 logs "dis=" (the Encore fields are visible).

DESIGN (weaken12-DESIGN.md):
- :8-11: no lead holds a sleep, paralysis or exact-damage move.
- :102: Encore is checked at selection only.
- :108: THROW-ONLY at a one-throw chance ≥ 0.5.
- :109: the caps' scope is ambiguous; v2:732 defined them per action.
- :111 and :122: STATUS is ordered before DAMAGE.
- :122-129: no Encore in the no-self-harm list, and "the only bound left is the hit itself".
- :157: "BEFORE records the move the game ACTUALLY chose".
- :160: 0 res=Won is the primary safety readout.

RECON:
- w12_recon_fixture.md:40-41: 49 distinct moves across the 66 rows; the only stage-1 move is Sing, on a Skitty that never leads.
- w12_recon_adversary.md:43-44: B2 raised the "Encore, then the next sleep pick" path; the design closed only the case where the Encore is already on us.

## safety:F2 [should-fix] weaken12-DESIGN.md:124-125 (the binary 'knows' list), :80-82 (D2: mismatch → DEFER, first in D4), :194-195 (D13: mismatch → THROW-ONLY)
CLAIM: Transform breaks the premise that 'knows' is fixed for the battle. On the damage turn the target knows only Transform, so damage is admitted. After it transforms, it holds our lead's moves (e.g. a recoil move and Roar), each with 5 PP, and can recoil itself to a KO from hp − X. Separately, D2 and D13 contradict each other: D2's species-mismatch DEFER comes first in D4, so D13's THROW-ONLY can never fire. The transformed target is then handed to the parent's unguarded chooser.
EVIDENCE: - pret src/battle_script_commands.c:7788-7798 (Cmd_transformdataexecution):
  - it copies gBattleMons bytes up to offsetof(pp): species, moves, ability, types (include/pokemon.h:260-283: moves at 0x0C, ability at 0x20, pp at 0x24);
  - it sets every PP to 5, so total PP ≤ 20 (the Struggle horizon, see F3);
  - HP (0x28) and personality (0x48) are NOT copied.
- A wild Ditto is in the Desert Underpass at L38-42 (scan), and its only move is Transform (10 PP, above the ≤ 4 Struggle rule).
- Mightyena learns Take Down (EFFECT_RECOIL) at L37 and Roar at L22 (src/data/pokemon/level_up_learnsets.h, Mightyena block). Fixture leads include Mightyena L38-43 (w12_recon_fixture.md:59).
- Species compare: SM:6453 formats ctx sp from encounter.pokemon.species. The live BattlePokemon.species (BS:566-570 derives the ability from it) becomes our lead's species after Transform, so D2 DEFERs.
FIX: - Add move-acquiring effects to the binary list: EFFECT_TRANSFORM (and Sketch/Mimic for completeness). Knows Transform → no damage.
- Identify the target by PID, not species (CLAUDE.md rule 3). Personality survives Transform. Store the first decision's opponent PID on the strategy instance.
- Make a mid-battle species change with the same PID → THROW-ONLY, per D13. A PID mismatch → DEFER.
- Add a row for each case.
VERDICT: refuted=True corrected=nit
REASONING: The mechanism is correct, but the finding's severity is overstated and the harm it describes cannot occur where the adapter runs.

1. Transform does do what the finding says. Cmd_transformdataexecution (pret src/battle_script_commands.c:7764-7798) copies every gBattleMons byte before `pp`, which includes species, moves and ability. It sets each move's PP to min(base, 5) and does not copy HP. So in principle, a "knows" list read on turn 1 does not hold for the rest of the battle.

2. That hazard cannot be reached inside story mode, which is where the adapter lives (StoryCatchStrategy):
   - The only wild Ditto is in MAP_DESERT_UNDERPASS, L38-45 (wild_encounters.json).
   - The Underpass is sealed unless FLAG_SYS_GAME_CLEAR is set. The tunnel's on-load script `call_if_unset FLAG_SYS_GAME_CLEAR, Route114_FossilManiacsTunnel_EventScript_CloseDesertUnderpass` puts red-rock-wall metatiles at (6,1) and (6,2) (pret data/maps/Route114_FossilManiacsTunnel/scripts.inc).
   - Story mode ends at game clear: at story_mode.py:6188-6200 it prints "THE GAME IS CLEARED ... Handing to manual." and calls `context.set_manual_mode()`. The last chapter's milestone is `flag("SYS_GAME_CLEAR")` (chapters.py:287-289).
   - Our own training_areas.py:200 already rejects DESERT_UNDERPASS as "post-game (Fossil Maniac), and Ditto".

   The other ways a move list can change are also out of reach before the game is cleared:
   - Mimic: Jigglypuff learns it at L39, but wild Jigglypuff are L24-25 (Route 115). Sudowoodo is never wild.
   - Sketch: Smeargle is only in Artisan Cave (post-game) and gAlteringCave9 (an event table).
   - Transform: the only other learner is Mew, which is never wild.

   So for every target the story can meet, the design's premise holds: what it "knows" is fixed for the battle.

3. The stacked conditions make it more remote still:
   - Stage 1 needs a lead with an exact-damage move. The design (:8-11) and the fixture recon (w12_recon_fixture.md:5, :40) show no story lead has one.
   - The finding's own example lead is Mightyena (Take Down, Roar). It has no exact-damage move, so stage 1 would never damage a Ditto with it.
   - Stage 2 stays OFF in every acting arm (D1, :75-76).

4. D2 vs D13 is at most unclear wording, not a contradiction with a safety effect.
   - ctx["sp"] is built from `encounter.pokemon.species`, the party mon (story_mode.py:6450-6453). D2 (:80) says it is compared with "the battle's opponent species" and never says which source. D13 (:194-195) says "live" species, which suggests D2 means the unchanged encounter or party species. On that reading D13 can fire.
   - Even if D2 did compare against the live gBattleMons species, the fallback is DEFER. A DEFER hands the turn to the parent's chooser, CatchStrategy.decide_turn (catch.py:41-62), which is exactly the behaviour with the flag unset. That chooser only ever throws a ball or uses a sleep/paralysis move, never a damaging move. So a DEFER cannot be worse than OFF.
   - Calling that chooser "unguarded" describes the existing baseline, not a regression this design introduces.

What is left is a nit:
- The binary list could add EFFECT_TRANSFORM, Mimic and Sketch as cheap future-proofing for the "POKEDEX HUNTING" work that story_mode.py:6192 calls WIP. That work would take this machinery post-game.
- D2 should name its comparison source (the party or encounter species, not gBattleMons) so D13 is not dead text.
- Identifying the target by PID is a reasonable tidy-up but guards nothing reachable.

Nothing in the design as written can KO a wanted target through Transform in any run the adapter takes part in.
V-EVIDENCE: pret src/battle_script_commands.c:7764-7798: Transform copies gBattleMons bytes up to `pp` and sets each move's PP to min(base, 5). The mechanism is confirmed.

wild_encounters.json: SPECIES_DITTO appears only under MAP_DESERT_UNDERPASS (L38, 40, 41, 42, 43, 45).

pret data/maps/Route114_FossilManiacsTunnel/scripts.inc:
- `Route114_FossilManiacsTunnel_OnLoad: call_if_unset FLAG_SYS_GAME_CLEAR, Route114_FossilManiacsTunnel_EventScript_CloseDesertUnderpass`
- That script does `setmetatile 6, 1 / 6, 2, METATILE_Fallarbor_RedRockWall`, so the Underpass is post-game only.

Level-up learnsets (decomp level_up_learnsets.h): Jigglypuff Mimic L39 (wild L24-25, Route 115 only); Sudowoodo Mimic L1 (not wild); Ditto and Mew Transform (Mew not wild); Smeargle Sketch (Artisan Cave post-game, gAlteringCave9 event only).

sandbox-pokebot/plugins/custom_modes/story_mode.py:6188-6200: "Story: THE GAME IS CLEARED (Ch24) ... Handing to manual.", followed by `self._reached_end_of_content = True; context.set_manual_mode()`.

sandbox-pokebot/modules/story/chapters.py:287-289: the Ch24 milestone is `flag("SYS_GAME_CLEAR")`.

sandbox-pokebot/modules/story/training_areas.py:200: "DESERT_UNDERPASS (L35-45) — post-game (Fossil Maniac), and Ditto/Whismur/Loudred."

story_mode.py:6450-6453: `sp = encounter.pokemon.species`; `s["sp"] = f"{sp.name}#{sp.national_dex_number}"`. This is the party or encounter species, not the live battle species.

The design leaves the D2 comparison source unspecified: weaken12-DESIGN.md:80 says "names the battle's opponent species", while :194-195 (D13) says "live species".

sandbox-pokebot/modules/battle_strategies/catch.py:41-62: the parent chooser only throws a ball or uses a sleep/paralysis move. A DEFER therefore equals the flag-off baseline.

weaken12-DESIGN.md:
- :8-11: no story lead holds an exact-damage move.
- :75-76: stage 2 is OFF in every acting arm.

w12_recon_fixture.md:40: no LEVEL_DAMAGE, SONICBOOM, DRAGON_RAGE or SUPER_FANG effect in any of the 66 fixture parties.

## safety:F3 [should-fix] weaken12-DESIGN.md:127-128 (the retaliation abilities of 'OUR' ACTIVE mon), :124-125 (Struggle-risk 'total PP ≤ 4'), :131 ('k is unbounded ... RULING 25')
CLAIM: The binary rule's 'NO way this battle' is checked on a one-turn snapshot of OUR side too. After the hit, a faint-switch can bring in a party member with Effect Spore, Poison Point, Flame Body, Rough Skin, Liquid Ooze or Synchronize (or remove our Cloud Nine). The target's contact or poison moves then start a tick that KOs it from hp − X. The team kind never flees after a faint. The Struggle rule is also inconsistent:
- The design rejects a k-turn floor because 'k is unbounded'.
- But RULING 25's 'never given up on' is per species ACROSS encounters. Within one battle, k is bounded by balls.
- The '≤ 4 PP' threshold matches neither premise, and it ignores our Pressure.
EVIDENCE: - catch.py:38-39: should_flee_after_faint is False for the team kind (StoryCatchStrategy). The dex kind continues after a faint under R24 NOFAINTBAIL (SM:153-160) or when trapped (SM:165-166).
- Route 116, the step's own fixture, has Abra (Synchronize) at 10% as a team target (w12_recon_fixture.md:23). Shroomish (Effect Spore) is a pre-gym-1 Petalburg Woods catch.
- RULING 25 text (06:8093-8095): 'no attempt cap, and no expected-throws refusal'. In-battle turns are bounded by the out-of-balls flee (SM:86-92) and the reserve bail (SM:197-217, DEX_CATCH_BALL_RESERVE=10 at SM:1681).
- Any battler with no usable move Struggles (pret src/battle_main.c:4184-4191, inside the all-battler loop). Struggle's recoil skips Rock Head (design :59).
- Our Pressure adds a PP deduction (src/battle_script_commands.c:1224-1225).
- Low-PP wild movesets (scan): Silcoon and Cascoon know only Harden (30 PP). A transformed Ditto has ≤ 20.
FIX: - Evaluate the retaliation-ability and weather-suppressor clauses over every party member that can battle (every possible faint-switch), not only the active mon.
- Replace 'total PP ≤ 4' with 'the target's total PP ≤ the in-battle horizon': spare balls, minus the reserve for the dex kind, plus the caps; halved under our Pressure.
- Correct :131's premise: k is ball-bounded per battle. Binary is still acceptable as the conservative choice.
- Add rows for a faint-switch retaliator and for Pressure plus low PP.
VERDICT: refuted=False corrected=should-fix
REASONING: The core claim holds. The design's binary rule promises the target "can hurt ITSELF in NO way this battle" (weaken12-DESIGN.md:122-123). But its retaliation clause (:127-128) reads only "OUR retaliation abilities (live byte)", and D3's WSelf (:87-90) snapshots only the active battler's live byte. No party-wide check appears anywhere in the design.

Why the path is reachable:
- The team kind never flees after a faint.
- The replacement mon is picked by HP, with no ability awareness.
- RULING 24 explicitly accepts faints during catches.
- Common Hoenn team members carry Effect Spore, Poison Point, Flame Body, Rough Skin, Liquid Ooze or Synchronize (Breloom, Roselia, Magcargo, Sharpedo, Gardevoir, Swalot).

Why nothing stops it: the design already applies its one damage turn before the switch (cap 1, :109). THROW-ONLY-on-ticking (:103-104) only prevents further damage. So a tick from a faint-switched retaliator (max/8 per turn) KOs the target from hp − X in about 4 turns instead of 8.

The design knew faint-switches reset per-mon hazards (it notes "Ghost Curse, once per our active mon", :28, and excluded Curse outright), yet it did not extend that to abilities. So this is a real gap in a stated safety premise. It stays should-fix, not blocker:
- It needs a chain of three low-probability events: a mid-catch faint, a retaliator next by HP, and a 1/3 or 1/10 trigger on a contact hit.
- The tick risk exists in the baseline too; weaken only speeds it up.
- Stage 1 almost never acts (:7-13), and stage 2 is OFF.
- On the W-EXEC fixture it is vacuous: the party's abilities are Torrent, Run Away, Compoundeyes and Soundproof (w12_recon_fixture.md:16-21).

Overstated sub-claims:
1. **Pressure.** It adds a PP only when the attacker is not the target (bsc.c:1224). The wild AI aims self-target moves at itself (battle_controller_opponent.c:1603-1604). So Pressure does nothing to the cited low-PP examples: Silcoon and Cascoon (Harden only) and Magikarp (Splash).
2. **Cloud Nine removal.** This is practically vacuous. Every Route 111 desert wild is sand-immune (v2 :630: Baltoy, Sandshrew and Trapinch are Ground; Cacnea has Sand Veil), and every Hoenn Sandstorm/Hail learner is immune (w12_recon_adversary.md N10).
3. **The "≤ 4 PP" threshold.** It really is unexplained, and it contradicts the design's own "k is unbounded" premise. Its practical effect is negligible, though. The only story-scope low-PP wilds are Silcoon and Cascoon (L5, Petalburg Woods, 30 PP). They reach Struggle only after about 30 uncaught throws. At catch rate 120, weakened, P(uncaught) is on the order of 1e-5, and even then Struggle recoil is about 1 HP per hit. Ditto (Desert Underpass L38-45) is outside story scope.
4. **":131's premise".** "k is unbounded" is literally wrong per battle: turns are bounded by the ball count. SM:86-92 flees at 0 balls, and SM:197-217 bails at the reserve (DEX_CATCH_BALL_RESERVE=10, SM:1681). RULING 25's "never given up on" is cross-battle (06:8093-8095). The finding itself concedes binary is still right, so this is a nit.

The first proposed fix is correct and should be applied: evaluate the retaliation-ability and weather-suppressor clauses over every party mon that can battle, and treat a Trace holder as copying the target's ability. The PP-horizon fix and the premise correction are nit-level.
V-EVIDENCE: The design:
- weaken12-DESIGN.md:122-123 promises damage only if the target "can hurt ITSELF in NO way this battle".
- :127-128 checks "OUR retaliation abilities (live byte)", which is the active battler only. WSelf at :87-90 has no party field.
- :28 acknowledges "Ghost Curse, once per our active mon", so faint-switches were considered for Curse but not for abilities.
- :109 caps damage at 1 turn, and it lands before any later switch.

Our code:
- sandbox-pokebot/modules/battle_strategies/catch.py:38-39: should_flee_after_faint returns False. StoryCatchStrategy (plugins/custom_modes/story_mode.py:85-93) does not override it.
- The dex kind continues under _no_faint_bail (story_mode.py:153-160) or when trapped (:165-166).
- The replacement is chosen by HP with no ability check (modules/battle_strategies/default.py:184, _util.py:556-575).
- 06-DECISIONS-LOG.md:8041: "A faint or a whiteout during a catch is ACCEPTED".

The decomp:
- The retaliation triggers are in src/battle_util.c:2753 (Rough Skin), 2768 (Effect Spore), 2792 (Poison Point) and 2822 (Flame Body).
- Struggle is confirmed at src/battle_main.c:4183-4191 (AreAllMovesUnusable).
- Pressure (src/battle_script_commands.c:1224-1225) requires gBattlerAttacker != gBattlerTarget. The wild AI targets itself with self-target moves (src/battle_controller_opponent.c:1603-1604), so Pressure does not apply to Harden or Splash.
- wild_encounters.json: Silcoon and Cascoon appear only in Petalburg Woods at L5 (Harden, 30 PP). Ditto appears only in the Desert Underpass at L38-45.

Ball bounds per battle: story_mode.py:85-93 (flee at 0 balls) and :197-217 (reserve bail), with DEX_CATCH_BALL_RESERVE = 10 at :1681.

The fixture party has no retaliator: w12_recon_fixture.md:16-21 lists Torrent, Run Away, Compoundeyes and Soundproof.

## safety:F4 [should-fix] weaken12-DESIGN.md:94-139 (D4 has no PP condition; a grep for 'PP' hits only :22-23, :65, :124)
CLAIM: D4 never requires the chosen DAMAGE or STATUS slot to have PP > 0. v2 had PP among its rows (v2:647). The game refuses a 0-PP pick. Our NoPP override and the KI-93 re-pick then run the FIRST slot with PP, with no weaken bound. That can be an unbounded damaging move, or Swagger / Leech Seed / Toxic, which start a self-hit or a tick. This is the one remaining refusal the design's THROW-ONLY and skip list do not close.
EVIDENCE: - BAS:549-572: on BattleScript_SelectingMoveWithNoPP, index = the first slot with pp > 0.
- BAS:390-418: the KI-93 re-pick takes the first unrefused slot with PP. Both are reached through KI93_SELECTION_REFUSAL_SCRIPTS (BAS:48-55), which includes SelectingMoveWithNoPP.
- The parent guards this (catch.py:196 `learned_move.pp == 0: continue`). The design's module is new code and states no such rule.
- PP carries over between battles until a heal, so a status move can start a battle at 0-1 PP.
- Mightyena learns Swagger at L27 (level_up_learnsets.h Mightyena block).
FIX: Add 'the chosen slot has PP > 0' (raw slot, BS:528 reads PP at 0x24+slot) as an admissibility rule for DAMAGE and STATUS. Add a W-row with a 0-PP Seismic Toss plus a damaging slot 0 → not DAMAGE, and a fault that drops the rule (it must redden exactly that row).
VERDICT: refuted=False corrected=should-fix
REASONING: I could not refute the finding. The design has no PP condition on our chosen move, the game refuses a 0-PP pick, and both of our re-pick paths then run the first slot that has PP, with no weaken bound.

1. **The game refuses the pick.** `TrySetCantSelectMoveBattleScript` sets `BattleScript_SelectingMoveWithNoPP` when the chosen slot's PP is 0 (pret `src/battle_util.c:1063-1074`). It is called at `src/battle_main.c:4382`. That script only prints a message and re-prompts (`data/battle_scripts_1.s:3552-3554`). The player controller does not check PP first.

2. **Our handler swaps in an unbounded move.**
   - While the refusal prompt is up, the handler records the committed slot as refused. `SelectingMoveWithNoPP` is one of the scripts in `KI93_SELECTION_REFUSAL_SCRIPTS` (`battle_action_selection.py:48-55`, recorded at :302-321). It then presses B, and `decide_turn` runs again.
   - The re-run returns the same verdict. D4 keys its caps on `battle_state.current_turn` and the re-prompt is still the same turn, so the "1 damage turn" cap does not stop it.
   - The KI-93 re-pick then replaces the slot with the first unrefused slot that has PP (`battle_action_selection.py:405-418`). The NoPP override does the same (:555-572). Neither checks any weaken bound.

3. **The design does not close it.**
   - A grep of the design for PP finds only :22-23 and :65 (both describe the re-pick) and :124 (the TARGET's Struggle risk).
   - :22 lists the refusals as "Torment, Disable, Taunt, Imprison and a Choice item". NoPP is missing from that list, even though the same sentence names the NoPP override.
   - D4 closes each listed refusal but not NoPP:
     - Encore, Torment, Disable and Imprison make the turn THROW-ONLY (:102).
     - A Choice item makes it DEFER (:100).
     - Taunt is a STATUS skip (:117). It is not needed for DAMAGE, because every stage-1 move has power 1.
   - Nothing in the DEFER, THROW-ONLY, STATUS or stage-1/stage-2 admissibility rules (:95-145) tests our slot's PP. D3 puts "the raw move slots" in the snapshot (:87), but no rule reads their PP.
   - The parent status chooser does filter PP (`catch.py:196`), so with weaken OFF this path does not exist.
   - The only mitigation I found is the header's "supersedes v2 where they differ" (:3). v2 names "PP" in its W-row list (v2:647), but it never states a PP rule or an expected verdict: v2's DEFER list (v2:604-610) has none. The adversary recon also verified that no W-row table exists anywhere (`w12_recon_adversary.md:25-30`). So the inherited word "PP" does not close the gap.

4. **It is reachable.** Party PP persists between battles until a heal. A status move can be drained across repeated catch battles (up to 3 tries per battle), and a stage-1 damage move can be drained by ordinary fights. The first slot with PP is usually a plain hit such as Tackle, which can KO a target at >50% HP when the lead is well above the wild's level. On a Mightyena it can instead be Roar (L22), which ends the battle, or Swagger (L27), which confuses the target so it can hit itself (both `level_up_learnsets.h:3755-3756`).

5. **Why should-fix, not blocker.** It needs WEAKEN set, a stage-1 or status move on the lead at exactly 0 PP, and the design itself says stage 1 will almost never act (:7-16). The effect is bounded and conditional. D6's "0 `res=Won`" readout would show a KO in any acting arm.

6. **An extra point for the fix.** D8's `--set-lead-move` writes Seismic Toss into an EMPTY slot (:163-166) but never says it writes that slot's PP byte. If the lever writes only the move id, the W-EXEC arm's own Seismic Toss would have 0 PP and be refused, and the re-pick would run Mudkip's slot-0 move instead. That arm would then fail on its own lever. The fix should also require D8 to write and read back a non-zero PP.

The proposed fix is correct and minimal: make "the chosen raw slot has PP > 0" an admissibility rule for DAMAGE and STATUS, add the row, and add a fault that reddens exactly that row.
V-EVIDENCE: - pret/pokeemerald `src/battle_util.c:1063-1074`:
  `if (gBattleMons[gActiveBattler].pp[gBattleBufferB[gActiveBattler][2]] == 0) { ... gSelectionBattleScripts[gActiveBattler] = BattleScript_SelectingMoveWithNoPP; limitations++; }`
  It is called at `src/battle_main.c:4382`, and `data/battle_scripts_1.s:3552-3554` only prints STRINGID_NOPPLEFT and re-prompts.
- `sandbox-pokebot/modules/battle_action_selection.py`:
  - :48-55 puts `BattleScript_SelectingMoveWithNoPP` in `KI93_SELECTION_REFUSAL_SCRIPTS`.
  - :302-321 records `_ki93_last_committed` as refused, once per park.
  - :405-418 re-picks the first slot with `_learned.pp > 0 and _slot not in _ki93_refused`.
  - :555-572 is the NoPP override: `if _lm is not None and _lm.pp > 0: index = _i; break`.
  - Neither path checks any weaken bound.
- `battle_state.py:518-533` reads PP at `0x24 + index` of the raw slot.
- `catch.py:196`: the parent skips `learned_move.pp == 0`. The weaken module is new and has no such rule.
- In the design (2026-09-30-weaken12-DESIGN.md):
  - A grep for "PP" hits only :22-23, :65 and :124 (the target's Struggle risk).
  - :22 lists "Torment, Disable, Taunt, Imprison and a Choice item" as the refusals and omits NoPP.
  - D4 (:95-145) has no our-slot PP condition in DEFER, THROW-ONLY, STATUS, stage 1 or stage 2.
  - The caps are keyed on current_turn (:109-110), so the same-turn re-prompt yields the same DAMAGE verdict.
  - D8 (:163-166) does not say the lever writes the new slot's PP.
- v2 `2026-09-29-r23-27-DESIGN-v2.md`:
  - :647 names "PP" only as a word in the row list.
  - Its DEFER list (:604-610) has no PP rule.
  - `w12_recon_adversary.md:25-30` verified that no W-row table exists.
- Mightyena learns Roar at L22 and Swagger at L27 (`level_up_learnsets.h:3755-3756`).

## safety:F5 [should-fix] weaken12-DESIGN.md:91-93 (catch_p over 'the full ball table'; THROW is not defined), :101-110
CLAIM: The design never says which ball THROW throws, or which ball the '≥ 0.5' and E-gain numbers are computed for. A module that picks the best ball by catch_p over the full table would throw the Master Ball (catch_p = 1.0). Today only the #40 allowlist in the parent's _get_best_poke_ball prevents that. If the two balls differ, the THROW-ONLY threshold is also judged for a ball that is not thrown.
EVIDENCE: - catch.py:212-233: _get_best_poke_ball honours allowed_ball_names() (fork #40; the default is every ball except Master).
- catch.py:239-241: Master Ball scores −1, so the parent never picks it.
- catch.py:62: the parent throws that ball.
- The design says 'THROW-ONLY ... never DEFER' (:44-46), so THROW is the adapter's own action, not the parent's.
FIX: - Specify THROW := TurnAction.use_item(self._get_best_poke_ball(battle_state)). None → DEFER; this is unreachable after the out-of-balls flee at SM:86-92.
- Compute catch_p and E-gain for that same ball.
- Add a W-row: a bag holding a Master Ball and Poké Balls → THROW uses the Poké Ball.
VERDICT: refuted=False corrected=should-fix
REASONING: The core of F5 holds. The design has an action verdict, THROW, but never says which ball it throws. It also never says which ball the "one-throw chance ≥ 0.5" test and the E-gain test are computed for.
- D3 (weaken12-DESIGN.md:87-93) lists the snapshots WTarget/WSelf/WEnv. None of them carries a ball or the bag. It then says catch_p covers "the full ball table" and decide_weaken_turn returns a bare THROW.
- D4 (:108) and the damage rules (:138, :141-142) use catch_p and E-gain without naming the ball.
- D5 (:147-153) says only what observe returns ("the parent's action unchanged"). It gives no THROW-to-TurnAction mapping for the acting mode.
- :44-46 forbids routing THROW through DEFER/super(), because the parent's status chooser runs at CS:50-60. So the adapter must build its own use_item, and the design leaves the ball to the implementer.
- A grep of the design for ball/use_item/_get_best_poke_ball finds no such specification.

This codebase has already paid for exactly this mismatch. SM:1723-1724 records: "The first version skipped the allowlist: a held-but-disallowed Ultra Ball made a rate-45 catch read 8.1 throws (admitted) while the thrower, barred from it, would throw Poké Balls at 16". SM:1733-1735 records a second mismatch of the same kind: the best ball held was scored while the thrower spent other balls. So "the threshold is judged for a ball that is not thrown" is a demonstrated failure class here, not a theoretical one.

Two parts of F5 are overstated, which is why it is not a blocker:
- (a) "Today only the #40 allowlist prevents that" is wrong. catch.py:239-241 independently gives the Master Ball a −1 multiplier. Because catch.py:229 compares against an initial 0, the Master Ball can never be picked even when allowed, and catch_balls.py:28-30 says so. F5's own second evidence bullet contradicts its claim.
- (b) The Master Ball throw is a hypothetical. It happens only if an implementer adds a "best by catch_p" loop, and the design never prescribes one. It is still a live risk: the decomp forces success for a Master Ball (battle_script_commands.c:10031, and :10009 for odds > 254), so any max-catch_p picker over the full table would choose it. Nothing in the design stops that.

Why the effect is bounded:
- The KO bound (hp − X ≥ 1, :129, :137) does not depend on the ball, so the wrong ball cannot KO a target.
- It does not change behaviour with the flags unset, and it cannot make an arm unable to fail.
- What it can do: throw a ball the user excluded, including the Master Ball, in violation of fork #40; and mis-gate the ≥0.5 and E-gain tests.

The proposed fix is sound: THROW := use_item(self._get_best_poke_ball(battle_state)); the same ball feeds catch_p and E-gain; and a W-row where a Master Ball plus Poké Balls → a Poké Ball. It needs one caveat. For the Net Ball, _get_best_poke_ball uses SPECIES types (catch.py:253-256), while the design's catch_p uses LIVE types (:92). So a Transform or Color Change target can still see a small residual mismatch even with the same ball; the W-row or the D13 note should cover it.

I checked the fixture and found no Master Ball in it. The fixture recon's "28 balls not counting the Master Ball" is only the name of the field it read, number_of_balls_except_master_ball (scratchpad/w12/dump_fixture_parties.py:74).
V-EVIDENCE: - Design gap:
  - weaken12-DESIGN.md:87-90: the snapshots hold no ball or bag.
  - :91-92: "catch_p ... with odds > 254 giving 1.0 and the full ball table".
  - :93: "returns one of {DAMAGE(slot), STATUS(slot), THROW, DEFER}", with no ball.
  - :108: "the one-throw chance ≥ 0.5", with no ball.
  - :138 and :141-142: E-gain, with no ball.
  - :44-46: THROW is never DEFER, so it cannot reuse super().
  - :147-153: the adapter specifies only observe's return.
- Parent code (sandbox-pokebot/modules/battle_strategies/catch.py):
  - :42 picks the ball; :62 is `return TurnAction.use_item(ball_to_throw)`.
  - :212-233: `_get_best_poke_ball` applies the allowed_ball_names() filter at :218 and :225.
  - :239-241: `case 1: catch_rate_multiplier = -1`, which excludes the Master Ball independently of #40. With the initial best of 0 (:223) and a strict `<` (:229), it is never chosen.
  - :253-256: the Net Ball uses `opponent.species.has_type` (species types, not live types).
- sandbox-pokebot/modules/catch_balls.py:28-31: "the Master Ball also stays never-auto-thrown by catch.py's own -1 multiplier". This refutes F5's "only the #40 allowlist".
- Precedent for this defect class (sandbox-pokebot/plugins/custom_modes/story_mode.py):
  - :1723-1724: "The first version skipped the allowlist: a held-but-disallowed Ultra Ball made a rate-45 catch read 8.1 throws (admitted) while the thrower ... would throw Poké Balls at 16".
  - :1733-1735: the best ball held was scored while the thrower spent other stacks.
  - :1703: `_BALL_BONUS_X10` knows only 4 balls.
- Adapter site: story_mode.py:85-93. The flee at :86-92 is inside try/except: pass; `super()` is at :93.
- Decomp (pret/pokeemerald src/battle_script_commands.c):
  - :9984 is the ball bonus lookup.
  - :10009 is `if (odds > 254) // mon caught`.
  - :10031 is `if (gLastUsedItem == ITEM_MASTER_BALL) shakes = BALL_3_SHAKES_SUCCESS;`.
  - So a full-table catch_p gives the Master Ball 1.0, which any max-catch_p picker would select.
- Fixture: scratchpad/w12/all_fixtures.txt:763 reads `balls_ex_master=28`, the field `bag.number_of_balls_except_master_ball` (dump_fixture_parties.py:74). There is no evidence that the fixture holds a Master Ball.

## safety:F6 [should-fix] weaken12-DESIGN.md:193-195 and :207-208 (W-EXEC, W-FAULT), :163-167 (D8)
CLAIM: W-FAULT (skip hp − X ≥ 1) is vacuous by construction on the named fixture and lever, and that can be computed now:
- With X = 13 against Route 116 targets, the bound can never bind at the first damage decision.
- The 1-damage-turn cap and the 50% rule forbid any later hit.
- So the fault arm equals the ON arm, and W-EXEC's 'not KO'd' cannot fail because of the bound.
D8's premise is also false: the lead Mudkip has no empty slot.
EVIDENCE: - pret src/data/wild_encounters.json gRoute116: Taillow L6-8, Skitty L7-8. species_info.h: baseHP Taillow 40, Skitty 50. Wild max HP (EV 0) is therefore 20-26 (Taillow) and 24-28 (Skitty).
- At full HP, hp − 13 ≥ 7.
- After one hit: Taillow is ≤ 50%. Skitty L8 at 28 has 15, but the cap blocks a second hit, and 15 − 13 = 2 ≥ 1 anyway.
- w12_recon_fixture.md:18: Mudkip L13 holds Tackle, Growl, Mud-Slap and Water Gun, so there is no EMPTY slot. The lever must overwrite a move, and BS:528 then reads the old slot's PP byte unless PP is also written.
- Mudkip learns Bide at L15 (fixture recon :36), so a move-replace prompt may evict the lever move mid-run.
FIX: - Pre-register a binding fault arm: a second lever whose X exceeds every Route 116 max HP, e.g. Dragon Rage X = 40 > 28. Then hp − X ≥ 1 is the ONLY refusal (check that the progress and E-gain rules do not also refuse under the fault), and the fault KOs at the first in-scope turn.
- Fix D8: name the overwritten slot, write and read back its PP, and pin how the L15 move-learn prompt is handled.
- Keep the discriminator computation.
VERDICT: refuted=False corrected=should-fix
REASONING: The core claim holds, and it can be computed from the design's own text. W-EXEC (DESIGN:207) pins the lever's damage at X = 13 ("Δbide = 13"). Every in-scope Route 116 target has at least 20 max HP, and a wild target is at full HP at its first damage decision: the ON arm only throws before it, balls do no damage, and none of these targets has a move that hurts itself. So hp − 13 ≥ 7 at that decision, and the bound hp − X ≥ 1 is satisfied.

After the first hit, the per-battle cap of one damage turn (DESIGN:109) makes every later turn THROW-ONLY. The bound does not bind even with the cap ignored: Skitty L8 with 28 max HP goes 28 → 15, and 15 − 13 = 2 ≥ 1. After that the 50% rule (DESIGN:136) refuses.

So a fault that only skips hp − X ≥ 1 (DESIGN:208) behaves exactly like ON on this fixture and lever. The design asks for a fault "chosen so that it binds on the arm's trajectory, by computation", and with this lever that cannot be met. Abra is THROW-ONLY anyway, because Teleport is an ender (DESIGN:106). This conflicts with story-drive SKILL.md §3: "FAULT ARMS — one per guard, or the guard is decoration … Every arm must FAIL for its own reason".

The design does partly anticipate this: W-FAULT's Pass column allows "or the arm is declared vacuous with its reason". So no false pass would be claimed, and G-W (D11) still tests the bound in pure-module rows and a mutant pass. That keeps it at should-fix rather than blocker: nothing KOs a wanted target and no behaviour changes with the flags unset. The defect is that the design picks a lever whose fault arm is vacuous by construction, which can be known now, not at Step 0. That leaves the bound without any live proof that it matters.

D8's premise is also false. The Mudkip has four moves, so there is no empty slot, and the lever must overwrite a move. The PP remark is also correct: BS:528 reads the slot's PP byte from 0x24+index, so the old move's PP is carried over unless it is written too.

One sub-claim is overstated. Bide at L15 cannot evict Seismic Toss. Both moves have base_power 1, and the story's move-learn policy (story_mode.py:603-708) handles Bide the same way whichever slot the lever overwrites: it either replaces Growl (the only status slot) or declines, because Normal is already covered by the stronger Tackle. Fighting stays a unique type, so it is never in the redundant pool. This does not affect the main finding. A minor citation slip: the finding's ':193-195' points at D12/D13, not the arms.
V-EVIDENCE: - **Route 116 table** (decomp copy of `src/data/wild_encounters.json`, gRoute116 land_mons): Taillow L6/7/8, Skitty L7/8, Abra L7, plus the owned Poochyena, Whismur and Nincada.
- **Base HP** (`species_info.h`): Taillow 40 (:8431), Skitty 50 (:8761), Abra 25 (:1901).
- **Max HP** by the Gen 3 formula `floor((2B+IV)L/100)+L+10`: Taillow is 20 at L6 IV0 and 26 at L8 IV31. Skitty is 24 at L7 IV0 and 28 at L8 IV31. Abra is 20-22, and is THROW-ONLY anyway through Teleport (DESIGN:106).
- **The design pins X = 13:** "Δbide = 13" (DESIGN:207), and D8 says 13 fixed damage (DESIGN:165-166).
- **The rules that stop a second hit:**
  - Cap: "1 damage turn … per-battle" (DESIGN:109).
  - 50% rule: "its hp is > 50% of max" (DESIGN:136).
  - The fault skips hp − X ≥ 1 only (DESIGN:137, :208).
- **Result:** at full HP, hp − 13 ≥ 7, so the bound never binds. After one hit, Taillow is at 7-13 of 20-26, which is ≤ 50%, and the cap blocks anyway. Skitty L8 goes 28 → 15, and 15 − 13 = 2 ≥ 1. So fault = ON, and the design's own escape clause "or the arm is declared vacuous" (DESIGN:208) is the only possible outcome.
- **Neither target can damage itself before the hit** (`level_up_learnsets.h`): Taillow's moves are Peck/Growl/Focus Energy/Quick Attack (:3960-3963), and Skitty's are Growl/Tackle/Tail Whip/Attract (:4127-4130).
- **Rule broken:** story-drive `SKILL.md:44-49`, "one per guard, or the guard is decoration … Every arm must FAIL for its own reason".
- **D8 premise false:**
  - `w12_recon_fixture.md:18` shows "Mudkip#550A9BE6 L13 … Tackle 31/35, Growl 40/40, Mud-Slap 10/10, Water Gun 7/25", so there is no empty slot. DESIGN:165 says "in an EMPTY slot, so no existing move is lost".
  - `sandbox-pokebot/modules/battle_state.py:528` has `current_pp = self._data[0x24 + index]`, so the old move's PP carries over unless it is written.
- **Bide sub-claim overstated:**
  - `moves.json:4098-4101`: Bide has base_power 1 and is Normal.
  - `moves.json:2418-2421`: Seismic Toss has base_power 1 and is Fighting.
  - `story_mode.py:661-667`: a new damaging move overwrites a status slot (Growl) first.
  - `story_mode.py:694-701`: a move of an already-covered type (Normal, via Tackle 35 BP) is declined unless it beats a weaker same-type move.
  - So Seismic Toss is never the slot Bide replaces.

## safety:F7 [nit] weaken12-DESIGN.md:122-131 (the binary rule replaces v2's hazard floor)
CLAIM: The binary list silently drops two of the six hazards RULING 25 names: weather MOVES (a target that knows Sandstorm or Hail and is not immune) and Spikes. v2 pinned both 'so the named hazard is not silently dropped'. There is no live effect today, but the W-row table will not carry them.
EVIDENCE: - 06:8096-8097 names 'weather, Spikes, Self-Destruct/Explosion, recoil, Curse, weather moves'.
- v2:630-631 has the weather-move clause and the Spikes rule, pinned by rows W38 and W40.
- The design's weather clause (:126) covers only weather already in effect.
- Every wild that knows Sandstorm or Hail is immune to it (w12_recon_gemini.md:160), so there is no live instance.
FIX: Restore 'knows Sandstorm/Hail and is not immune → no damage' as a binary clause, and a Spikes-is-inert row, or state each one's disposition with a pinning row.
VERDICT: (none: a nit, not sent to a refuter)

## safety:F8 [nit] weaken12-DESIGN.md:109-110 (caps keyed on battle_state.current_turn [R:OUR-3.6])
CLAIM: current_turn is exactly the field KI-108 names. When another reader calls get_battle_state() first in a frame (KI-108 names the GUI debug Battle tab), the handler receives the cached object, and its turn lags by one. The turn-2 decision then reads the same turn as turn 1, so every turn-keyed cap under-counts by one. There is no KO from this alone: HP is a compared field, so it is fresh and hp − X ≥ 1 is re-checked.
EVIDENCE: - BS:249-261: __eq__ omits _current_turn.
- state_cache.py:293-298: the setter keeps the OLD object when the new one is equal.
- BS:808-810: a same-frame call returns the cached object.
- modules/gui/debug_tabs.py:427 calls get_battle_state().
- pret battle_main.c:3960-3997: battleTurnCounter++ comes after every end-of-turn effect and TurnValuesCleanUp. TurnValuesCleanUp changes compared bytes only while isFirstTurn or rechargeTimer is nonzero (battle_main.c:4857-4890).
- 05:3066-3080 (KI-108) lists current_turn readers as exposed.
- The counter also saturates at 0xFF (battle_main.c:3995).
FIX: Read gBattleResults+0x13 with a raw read_symbol in the adapter (dmgaudit's no-cache pattern). Or state why a lagging turn is acceptable, with a row that feeds a stale-turn snapshot.
VERDICT: (none: a nit, not sent to a refuter)

### checked and found true
- A stale _catch_ctx cannot cross battles. on_battle_started clears it before any branch (SM:4036-4040), and _r20_catch_end clears it at battle end (SM:6498-6499). _r20_catch_start writes ctx on the line before each catch strategy is constructed (SM:6455; SM:4014-4015, 4092-4093, 4127-4128, 4237-4238). If _r20_levels() raises, ctx stays None, so the adapter DEFERs: safe, identical to today.
- The shiny path bypasses the adapter: StoryShinyCatchStrategy.decide_turn calls CatchStrategy.decide_turn(self, …) directly (SM:251-275). Kind 'shiny' is also out of scope.
- The hm and counter branches do reach the adapter (they return StoryCatchStrategy() at SM:4128 and :4238), but kinds 'hm' and 'counter' are outside the default dex,team scope, so they DEFER, which equals today. Trainer battles never get a catch strategy, and on_battle_started leaves ctx None for them.
- Placement: StoryDexCatchStrategy's reserve and faint bails (SM:197-217) and the out-of-balls flee (SM:86-92) run before the adapter slot. super() at SM:93 sits outside any try. A raise in _get_best_poke_ball already propagates today through CatchStrategy.decide_turn (catch.py:42).
- Flags unset: the only runtime change is an early DEFER in the adapter, which reads mode attributes with no side effects. The run header's env-all line lists only SET POKEBOT_* variables (debug_logger.py:262-266), so W-OFF's '0 lines contain WEAKEN' can hold.
- Observe inertness:
- The two snapshot fields outside BattleState (gSideStatuses; gWishFutureKnock.futureSightCounter, pret bsc.c:8931-8940) need raw read_symbol reads, which never touch state_cache.
- The bag, pokedex and map reads for the ball duplicate reads the flee (SM:87) and the parent (catch.py:42-53, 235-277) already make in that frame.
- The Encore 0x06 byte can be read from the passed object's disable-struct bytes (BS:280-289).
- The Encore offset is right: DisableStruct puts encoredMove at 0x06 and encoreTimer in the low nibble of 0x0E (pret include/battle.h DisableStruct). BS:729-734 reads 0x04 (disabledMove). D9's 'file, do not fix' is correct, because can_use_move (BS:547-559) is shared.
- At decision time, a THROW under Encore is safe: the selection-time Encore substitution applies only to B_ACTION_USE_MOVE (pret battle_main.c:4180-4196).
- Held items: no Gen 3 hold effect damages its holder (pret include/constants/hold_effects.h, 0-66: no Sticky Barb, Life Orb or Black Sludge). The confusion berries (HOLD_EFFECT_CONFUSE_*) exist, but no species_info.h entry gives one to a wild.
- Stage 2's Tier A (tools/story-dev/audit_damage_calc.py:131-137) excludes BURN_HIT, POISON_HIT, CONFUSE_HIT, TRI_ATTACK and SECRET_POWER; they are in Tier B at :141-143. So our own hit's secondary effect cannot start a tick or a self-hit. Tier A's RECOIL, DOUBLE_EDGE and ABSORB hurt only us.
- No wild moveset contains EFFECT_PAIN_SPLIT, so a same-turn HP drop before our hit is not possible that way (scan of wild_encounters.json × the last 4 level-up moves). Belly Drum is already in the binary list.
- The KI-93 re-pick and the NoPP override are reachable only through a selection refusal (BAS:48-55). D4 closes Torment, Disable, Imprison and Encore (THROW-ONLY), Choice (DEFER) and Taunt (the STATUS skip). Only NoPP is left open (F4). Refusals within a turn (Disable, Taunt, Imprison) make our move FAIL rather than substitute; only Encore substitutes (F1).
- W-EXEC is non-vacuous on Taillow. The exact integer catch chance with a Poké Ball at full HP is 0.28 (Skitty 0.337), below 0.5. Fighting is not immune against Normal/Flying. hp − 13 ≥ 7. OFF throws, because Mudkip has no SLEEP or PARALYZE move (catch.py:202-205).
# LENS mechanics

## mechanics:W12M-B1 [blocker] 2026-09-30-weaken12-DESIGN.md:122-128 (D4 DAMAGE: NO-SELF-HARM, 'none of OUR retaliation abilities (live byte)')
CLAIM: MISSING. The binary rule is meant to guarantee that the target 'can hurt ITSELF in NO way this battle', but it checks only the ability of the mon we have out now. The catch battle goes on after that mon faints, and the mon sent in next can have Rough Skin, Poison Point, Flame Body, Effect Spore, Synchronize, Liquid Ooze or Trace. Any of these can finish off a target that the damage turn left as low as 1 HP. Separately, our side's Cloud Nine, Air Lock or Damp only works while that mon stays in, so it cannot be counted on either.
EVIDENCE: Game: Rough Skin takes the attacker's maxHP/16 (minimum 1) on any contact hit, and Effect Spore, Poison Point and Flame Body can poison or burn the attacker. All of these use the DEFENDER's live ability, meaning whichever of our mons is in (pret src/battle_util.c:2753-2830). Synchronize passes poison, burn and paralysis back to the target (src/battle_script_commands.c:2501-2511; src/battle_util.c:2957-2970). Struggle also makes contact (src/data/battle_moves.h:2148-2158). WEATHER_HAS_EFFECT only checks for Cloud Nine or Air Lock among the battlers currently in (include/battle_util.h:47). Our code: CatchStrategy.should_flee_after_faint returns False (sandbox-pokebot/modules/battle_strategies/catch.py:38-39), and then battle_handler.py:520-535 calls choose_new_lead_after_faint, which sends in a bench mon. So the `team` kind ALWAYS keeps going after a faint. The `dex` kind keeps going when it is trapped (story_mode.py:168-169) or when POKEBOT_R24_NOFAINTBAIL=1 is set (story_mode.py:155-164, :2369). Common catches that bring these abilities: Shroomish Effect Spore (species_info.h:8513; Petalburg Woods, so a pre-gym-1 team catch), Roselia Poison Point (:10223), Carvanha Rough Skin (:9233), Abra and Ralts Synchronize/Trace (:1923, :11093), Tentacool and Gulpin Liquid Ooze (:2193, :10343), Slugma Flame Body (:6573). How to calibrate this: none of the 66 fixture parties has one of these abilities today (recon dump scratchpad/w12/all_fixtures.txt). A run creates the danger with its own catches.
FIX: Evaluate NO-SELF-HARM over every able, non-egg party member that could be sent in: use each member's actual ability, and count a Trace holder as holding the target's ability. Count our side's Cloud Nine, Air Lock and Damp only if every able party member has one. Add W-rows where the lead is clean and the bench holds Rough Skin, Poison Point or Synchronize, each expecting no damage.
VERDICT: refuted=False corrected=should-fix
REASONING: The core claim holds. The design promises that the target "can hurt ITSELF in NO way this battle" (DESIGN.md:122-123), but the ability part of that check reads only the "live byte" (:127), which is the active battler's ability. Nothing in D1-D14 looks at the party. A faint switch-in is a normal, allowed path:
- the `team` kind never flees after a faint;
- the `dex` kind keeps going when it is trapped, when its escape attempt fails (the game then forces the party screen), or when NOFAINTBAIL is set;
- USER RULING 24 explicitly accepts faints during a catch.

The damage cap (1 turn) is spent before any later switch-in, so re-reading the snapshot on later turns cannot undo it. The only guard that works is one applied at the moment the damage decision is made. The adversary recon had already flagged faint-switches for Curse and recoil (w12_recon_adversary.md:66-67). The design fixed the Trace case only for the active mon (via the live byte, S8), not for the bench. The design also rejects numeric floors because "k is unbounded" (:130-131). By its own logic, then, any hazard that repeats once a retaliating bench mon comes in (Poison Point or Flame Body poison/burn ticking maxHP/8 per turn, Rough Skin at maxHP/16 per contact hit) eventually matters.

I downgraded it from blocker because the effect is bounded and needs several things to happen in one battle:
1. A damage turn actually runs. Stage 1 "will almost never act" (DESIGN.md:7-16), and stage 2 is OFF in every acting arm (:75-76).
2. Our lead then faints later in the same battle.
3. The mon sent in has one of these abilities. None of the 66 fixture parties has one (ability tally from all_fixtures.txt). The W-EXEC fixture party is Torrent, Run Away, Compoundeyes and Soundproof.
4. The ability triggers enough times to finish the target.

So no pre-registered arm can KO through this path. Only a future release (stage 2, or a status/exact-damage lead) with a run that has caught a retaliator could do it.

Two sub-claims are wrong or overstated:
- **Damp:** for DAMAGE, knowing Explosion/Self-Destruct already rules damage out whatever Damp says (:124). Damp only moves the verdict between THROW-ONLY and STATUS (:105). Explosion also KOs its user at any HP, so weakening does not make it worse.
- **Cloud Nine / Air Lock:** the concern is correct in principle, since WEATHER_HAS_EFFECT only checks the battlers on the field. But there is almost no way to hold these in the story: Psyduck and Golduck come only from the Safari Zone, and Rayquaza is legendary.

The core bench-retaliator gap survives, and the proposed fix fits: evaluate the rule over every able, non-egg party member, count a Trace holder as holding the target's ability, and add W-rows where the lead is clean and the bench is not.
V-EVIDENCE: DESIGN 2026-09-30-weaken12-DESIGN.md:122-131. The rule reads "can hurt ITSELF in NO way this battle" and "none of OUR retaliation abilities (live byte)". It rejects the floor because "k is unbounded". No text anywhere covers the bench or faint switch-ins; a grep for bench/faint/switch finds only :127.

Our code (worktree at df4b1c6a / cdb49f83):
- sandbox-pokebot/modules/battle_strategies/catch.py:38-39: `should_flee_after_faint` returns False.
- sandbox-pokebot/modules/battle_handler.py:521-535: in a wild battle, a strategy that does not flee falls through to `choose_new_lead_after_faint`.
- sandbox-pokebot/plugins/custom_modes/story_mode.py:4014-4015: `team` is the pre-badge-1 kind and returns the plain StoryCatchStrategy, so it never bails.
- story_mode.py:149-171 (the dex kind):
  - with `_no_faint_bail` it takes the parent's answer (False);
  - `if self._escape(battle_state) is None: return super()...` covers the trapped case;
  - story_mode.py:2369 reads POKEBOT_R24_NOFAINTBAIL.

Game (decomp copy, identical to pret):
- data/battle_scripts_1.s:2839-2844: the player answers "No", `jumpifplayerran` fails, `printstring STRINGID_CANTESCAPE2`, and `BattleScript_FaintedMonTryChoose` runs `openpartyscreen`. So even the bailing dex kind is forced to send the bench in when the escape fails.
- src/battle_util.c:2753-2766, Rough Skin: maxHP/16, minimum 1, on any contact hit, using the defender's ability.
- src/battle_util.c:2768-2835: Effect Spore (1/10: sleep, poison or paralysis), Poison Point and Flame Body (1/3), each applied to the attacker.
- include/battle_util.h:47: WEATHER_HAS_EFFECT checks only ABILITY_ON_FIELD.

Species abilities (src/data/pokemon/species_info.h):
- :8513 Shroomish Effect Spore
- :10223 Roselia Poison Point
- :9233 Carvanha Rough Skin
- :1923 Abra Synchronize
- :11093 Ralts Synchronize/Trace
- :2193 Tentacool Liquid Ooze
- :10343 Gulpin Liquid Ooze
- :6573 Slugma Flame Body

USER RULING 24 (06-DECISIONS-LOG.md, ~:8041): "A faint or a whiteout during a catch is ACCEPTED."

Why it is not a blocker:
- DESIGN:7-16 and :75-76: stage 1 almost never acts, and stage 2 is OFF in every acting arm.
- scratchpad/w12/all_fixtures.txt: the ability tally across all 66 fixtures has no Rough Skin, Poison Point, Flame Body, Effect Spore, Synchronize, Liquid Ooze or Trace.
- all_fixtures.txt:764-767: the W-EXEC fixture party is Torrent, Run Away, Compoundeyes and Soundproof.

The Damp sub-claim is wrong for damage: DESIGN:124 already rules out damage against any Explosion/Self-Destruct knower, whatever Damp says. Damp only affects the THROW-ONLY rule at :105.

## mechanics:W12M-B2 [blocker] 2026-09-30-weaken12-DESIGN.md:122-125 (NO-SELF-HARM 'knows no …' on the CURRENT moveset), :194-195 (D13), :80-82 (D2)
CLAIM: MISSING. Transform gives the target new moves only AFTER the damage decision has been made. A wild Ditto knows only Transform, which has 10 PP, so it passes every 'knows no X' check and the 'total PP ≤ 4' check. It takes the hit, then transforms and gets our lead's moves at 5 PP each. Those can be recoil moves or enders, and 5 PP each is a quick path to Struggle. The re-read that D13 relies on happens a turn too late. D2 and D13 also contradict each other: a transformed Ditto no longer matches the context's `sp`, so D2 DEFERs before D13's THROW-ONLY can ever fire.
EVIDENCE: Transform copies species, moves, ability and types (every byte before `pp`) and sets each copied move's PP to at most 5 (src/battle_script_commands.c:7790-7799). The catch rate then comes from the copied species (:9935). A wild Ditto's learnset is Transform only (src/data/pokemon/level_up_learnsets.h:1827-1830), and Transform has pp = 10 (src/data/battle_moves.h:1875-1881). Wild Ditto appear in MAP_DESERT_UNDERPASS at L38-45 (src/data/wild_encounters.json). The story's Mightyena lead carries Take Down [RECOIL] in 4 pinned fixtures (post_grind_L60, post_maxie, post_mtpyre, magma_door_losing; recon fixture dump). Mightyena's learnset also has Roar, an ender (level_up_learnsets.h, sMightyenaLevelUpLearnset). Take Down recoil is 1/4 of damage dealt, minimum 1 (battle_script_commands.c:2636-2639). If the Ditto is faster, it transforms on turn 1 BEFORE our hit, but our turn-1 move was already chosen from the pre-Transform snapshot. The ctx `sp` is built from the encounter's species (story_mode.py:6450-6454), while BattlePokemon.species reads live gBattleMons+0x00 (battle_state.py:491-493), which Transform overwrites.
FIX: Treat a target that knows EFFECT_TRANSFORM as THROW-ONLY, so it never takes damage or a status turn. Settle D2 vs D13 explicitly: compare identity by PID, or run D13 before D2, and prefer THROW-ONLY because a DEFER hands the turn to the parent's status chooser. Add a Ditto row (knows Transform, full HP, lead with a stage-1 move → THROW).
VERDICT: refuted=False corrected=should-fix
REASONING: The mechanism holds. The blocker severity does not, because no run in step 12's scope can reach it.

WHAT SURVIVES:
(1) The NO-SELF-HARM test (DESIGN.md:122-128) is run on the target's CURRENT moveset. Its "calling move" clause lists only Metronome, Mirror Move, Assist and Sleep Talk (:107, :125). Transform is not on it.
(2) An untransformed wild Ditto knows only Transform, which has 10 PP. It passes every "knows no X" check and the "total PP <= 4" check, so the turn-1 damage can be admitted.
(3) D13 (:194-195) only covers decisions made AFTER the species has changed. The one allowed damage turn (:109) can happen before that. After it, the transformed Ditto holds our lead's moves at 5 PP each, and the design's own reasoning (:130-131, k unbounded) applies to them: a recoil move, or Struggle once 20 PP runs out, can then finish a target that the hit lowered.
(4) D2 does conflict with D13. `ctx["sp"]` comes from the encounter's party mon (story_mode.py:6450-6454). The live battle species reads gBattleMons+0x00 (battle_state.py:491-493), and Transform overwrites it. D4 puts the "context does not match" DEFER first (:96), so D13's THROW-ONLY is shadowed whenever the live species is the comparison source.

WHY IT IS NOT A BLOCKER:
(a) Wild Ditto exist only in MAP_DESERT_UNDERPASS. That map is closed until FLAG_SYS_GAME_CLEAR, which is set after the Hall of Fame (Route114_FossilManiacsTunnel/scripts.inc:15-22). Our own code records it as post-game (sandbox-pokebot/modules/story/training_areas.py:200). The only other Transform learner is Mew (level_up_learnsets.h:2097), an event legendary that D4 already DEFERs (:97-98).
(b) Stage 1 needs a lead that holds an exact-damage move. The design's own headline (:8-11) says no story lead has one. Mightyena's whole learnset has none (level_up_learnsets.h:3746-3763). So the finding's pairing of Mightyena's Take Down with a Ditto cannot happen under stage 1. The Mightyena fixtures are pre-League in any case.
(c) Stage 2 is OFF in every acting arm (:12-13, :75-76).
(d) Every arm runs on Route 116 against Taillow, Skitty and Abra (:165-166, :204-208), so no arm can meet a Ditto. The arms can still fail.
(e) The D2/D13 conflict leads to a DEFER, and a DEFER hands the turn to CatchStrategy.decide_turn (catch.py:41-63). That code only throws a ball or uses a status move. It never deals damage, and it is exactly what happens with the flag unset. So the conflict cannot cause a KO.
(f) Roar or Teleport copied through Transform would end the battle whether or not we weaken, because Ditto transforms on turn 1 in any case. The weaken design adds no exposure to enders.

So none of the blocker triggers holds in scope: no KO of a wanted target, no lost or hung battle, no behaviour change with the flags unset, and no arm made unable to fail.

It is still a real, cheap-to-fix gap in a classifier that will run once stage 2 is released or post-game play is added. The punch list already carries post-game work (#24-crackedfloorpathfinder, 03-PUNCH-LIST.md:1467). The design's stated principle, that the target can hurt itself in NO way this battle, is broken for a Transform user.

Fix: treat EFFECT_TRANSFORM as THROW-ONLY, like the calling moves. Make D2 compare identity by PID or by the party species, or run D13 before D2. Add a Ditto W-row.
V-EVIDENCE: Each item below was checked by me.
- pret battle_script_commands.c:7764-7805 (Cmd_transformdataexecution): copies every byte before `pp` (:7790-7791) and sets each move's PP to min(5, pp) (:7793-7799).
- :9935: catchRate is read from gBattleMons[target].species.
- :2636-2639: RECOIL_25 is gHpDealt/4, minimum 1.
- battle_moves.h: MOVE_TRANSFORM has pp = 10 and EFFECT_TRANSFORM.
- level_up_learnsets.h:1827-1830: Ditto learns Transform only. :2097: Mew learns Transform at L10, the only other learner. :3746-3763: Mightyena learns Roar and Take Down but NO exact-damage move.
- wild_encounters.json: SPECIES_DITTO appears only in MAP_DESERT_UNDERPASS, at L38-45.
- pret data/maps/Route114_FossilManiacsTunnel/scripts.inc:15-22: OnLoad calls CloseDesertUnderpass (red-rock metatiles at 6,1 and 6,2) while FLAG_SYS_GAME_CLEAR is unset, so the map is post-Hall-of-Fame.
- Our code:
  - sandbox-pokebot/modules/story/training_areas.py:200: "DESERT_UNDERPASS ... post-game (Fossil Maniac)".
  - plugins/custom_modes/story_mode.py:6450-6454: ctx sp comes from encounter.pokemon.species.
  - modules/battle_state.py:491-493: species is the live _data[0x00:0x02].
  - modules/battle_strategies/catch.py:41-63: the parent throws or uses a status move and never damages.
- The design:
  - :8-13: no lead has a stage-1 move, and stage 2 is OFF.
  - :96: the context-mismatch DEFER comes first.
  - :97-98: legendary DEFER.
  - :107, :124-125: the calling-move list, which omits Transform.
  - :109: one damage turn per battle.
  - :165-166, :204-208: every arm is on Route 116 (Taillow, Skitty, Abra).
  - :194-195: D13 only acts once the live species differs.

## mechanics:W12M-S1 [should-fix] 2026-09-30-weaken12-DESIGN.md:102 (THROW-ONLY 'our side is under Encore'), :111-121 (STATUS still selectable after the damage turn)
CLAIM: MISSING. The THROW-ONLY rule covers an Encore that is already on us when we decide. It does not cover an Encore that lands in the SAME turn before our move. In that case the game discards the move we chose and runs our last move again. After our damage turn, our last move stays the damaging move through every ball throw. So a later STATUS pick (sleep wears off and tries remain), or a DEFER to the parent's status chooser, can be turned into a second exact hit on a target already at hp − X. If hp − X ≤ X, that second hit is a KO.
EVIDENCE: HandleAction_UseMove replaces the chosen move with encoredMove at EXECUTION time (pret src/battle_util.c:110-117). trysetencore encores gLastMoves[target] whenever that move has PP left (src/battle_script_commands.c:8021-8040). gLastMoves is written only when a move is used (battle_script_commands.c:4407), and is reset only by SwitchInClearSetData and FaintClearSetData (src/battle_main.c:3222, :3314), so ball turns leave it unchanged. Sleep lasts only 1-4 of the target's turns (battle_script_commands.c:2481; battle_util.c:2015-2030), so D4's STATUS branch can come round again after DAMAGE. Wild species that know Encore: Spheal from L7 (level_up_learnsets.h:4529; Shoal Cave L25-35) and Wynaut from L1 (:4834). This only matters when the target moves first (for example our lead is paralysed, or the target has Quick Claw), which is why it is should-fix rather than a blocker.
FIX: Once a damaging move of ours has run in this battle and the same lead is still in, a target that knows Encore gets no further move selection and no DEFER, only THROW. Alternatively, put 'knows Encore' on the NO-SELF-HARM exclusion list. Add a row: after the damage turn, the target knows Encore, sleep has worn off → THROW.
VERDICT: refuted=False corrected=should-fix
REASONING: The mechanism holds, and the design text does not cover it. The design's only Encore guard is a check made at decision time: "our side is under Encore" (DESIGN:102). No list in D4 (:95-145) mentions a target that KNOWS Encore. The game swaps in the encored move when the move EXECUTES, not when we select it. So an Encore that lands earlier in the same turn turns our STATUS pick into our last move. If that move was the damaging one, it hits the target a second time. Nothing between our damage turn and a later STATUS turn resets gLastMoves: our ball throws do not write it, and the only writes are at battle start, on switch-in, on faint, and in the move-end code. Sleep wears off after 1-4 turns, and paralysis never does, so a STATUS pick can come after DAMAGE only on the sleep path. That fits D4's order: STATUS comes first, then DAMAGE while the target is asleep, then STATUS again once it wakes. This reads the caps at :109 per branch, as the ourcode recon's per-battle counters do (w12_recon_ourcode.md:130). If "caps are spent" meant ANY cap, THROW-ONLY would fire after the single damage turn and only the DEFER path would remain. The line is ambiguous, which is one more reason to pin it with a row.

The EXPOSURE is overstated in one place. For Spheal the finding's path is already closed.
- A second hit can KO only if hp' ≤ X, where hp' = hp − X ≤ max − X, so hp' ≤ max/2 in every KO state.
- Spheal's catch rate is 255. With the weakest ball (×1.0), the decomp formula gives a one-throw chance of at least 0.785 at hp' ≤ max/2 (I computed the minimum over max HP 15-139).
- So the THROW-ONLY rule "one-throw chance ≥ 0.5" (DESIGN:108) fires before STATUS in every KO-risk state.
- The DEFER path is closed as well: the parent tries a status move only when its own float chance is below 0.5 (catch.py:57). That function uses the same formula (_util.py:285-294), so it throws too.
- Spheal also knows Encore only at L25-30, since Hail at L31 pushes it out; not at L25-35 as the finding says.

What remains reachable in the game today:
- Wynaut, catch rate 125, at L5 and L10 on Route 130 (Mirage Island). At hp' ≤ max/2 its chance is 0.337-0.503, so STATUS stays open. Base speed 23 means it outspeeds a post-Surf lead only if our lead is paralysed or very slow.
- Plusle, Minun, Illumise, Gulpin and Slakoth appear wild below their Encore level.
- Shuckle is found only in the Safari Zone (a DEFER) and in Altering Cave 7 (event-only).
- The path also needs a lead holding BOTH a sleep move and an admitted damage move. The design's own headline (:8-11) says no story lead has one. The D8 lever gives Mudkip only Seismic Toss, so no arm exercises the path either.

Reach grows with stage 2 (plain hits plus any sleep holder, such as Skitty's Sing) and with the open "catching-lead choice" item (:214). Taken together, this is a real KO path for a wanted target, the one outcome this step exists to prevent, and it is bounded to a narrow and currently near-unreachable set of conditions. The fix is cheap, because the design already reads the target's moves (for Explosion, the enders and the calling moves). So should-fix stands, with the Spheal exposure struck.
V-EVIDENCE: Decomp (pret copy in scratchpad/decomp):
- battle_util.c:111-117, HandleAction_UseMove, which runs when the move executes: `else if (gDisableStructs[gBattlerAttacker].encoredMove != MOVE_NONE && ... == moves[encoredMovePos]) { gCurrentMove = gChosenMove = gDisableStructs[gBattlerAttacker].encoredMove; ...}`.
- battle_main.c:4192-4197 is the check made at action selection, and that is the only case the design cites (DESIGN:21, :57).
- battle_script_commands.c:8017-8044, Cmd_trysetencore: encores gLastMoves[target] when that move is in its move slots and has PP left, for 3-6 turns.
- gLastMoves is written only at battle_script_commands.c:4407 and :4412 (move end), and reset at battle_main.c:3053 (BattleStartClearSetData), :3222 (SwitchInClearSetData) and :3314 (FaintClearSetData). Nothing on the ball-throw path touches it.
- battle_script_commands.c:2481: sleep is `(Random() & 3) + 2`.
- Catch formula at battle_script_commands.c:9987-10028. My computation: rate 255 at hp ≤ max/2 with a ×1.0 ball gives p ≥ 0.785. Rate 125 gives 0.337-0.503.

Design text:
- DESIGN:102 is the only Encore guard, and it checks the state at decision time.
- DESIGN:108: one-throw chance ≥ 0.5 → THROW-ONLY. This precedes STATUS at :111 and covers Spheal.
- DESIGN:109: the caps wording is ambiguous.
- No "knows Encore" anywhere in :95-145.

Our code:
- catch.py:57-60: the parent tries a status move only when the float chance is below 0.5.
- catch.py:202-205: that move must have a SLEEP or PARALYZE effect.
- _util.py:285-294: the parent's chance uses the same formula as the decomp.

Data:
- species.json Encore learn levels: Spheal L7, Wynaut L1, Plusle and Minun L22, Illumise L25, Gulpin L23, Slakoth L7, Shuckle L14.
- pret wild_encounters.json:
  - Spheal: Shoal Cave, L26-32 on land and L25-35 on water. It knows Encore only at L25-30, because Hail at L31 pushes it out of the last four moves.
  - Wynaut: Route 130 (Mirage Island), L5 and L10 still know Encore; from L15 its four L15 moves replace it.
  - Plusle and Minun: Route 110 at L12-13. Illumise: Route 117 at L13-14. Gulpin: Route 110 at L12-13. Slakoth: Petalburg Woods at L5-6. All are below their Encore level.
  - Shuckle: Safari Zone and Altering Cave 7 (event-only).

## mechanics:W12M-S2 [should-fix] 2026-09-30-weaken12-DESIGN.md:124-125 ('Struggle-risk (total PP ≤ 4)') vs :131 ('k is unbounded')
CLAIM: REFUTED, the threshold does not match the design's own premise. The design rejects a floor summed over k turns because k is unbounded, yet it treats Struggle as a risk only at total PP ≤ 4. A wild mon uses up PP on every turn it acts. Once ALL its moves reach 0 PP it Struggles, and Struggle's recoil (minimum 1, and Rock Head does not stop it) KOs a 1-HP target. So any target whose total PP is at most the number of turns the battle can still last is a Struggle risk. Our side's Pressure halves that count, and Transform caps every move at 5 PP.
EVIDENCE: The wild picks its move with no PP check (pret src/battle_controller_opponent.c:1597-1601). It Struggles only when every move is unusable (src/battle_main.c:4184-4191; src/battle_util.c:1125-1139; battle_util.c:98-104 then forces MOVE_STRUGGLE). Pressure on the defender adds 1 PP per use (battle_script_commands.c:1224-1225). Struggle's recoil is 1/4 of damage dealt, minimum 1 (:2636-2639), and bypasses Rock Head (data/battle_scripts_1.s:3938-3940). Transform sets PP to ≤5 per move (:7793-7799). Battles really do run this long: 'one Absol took 23 balls' (story_mode.py:101).
FIX: Refuse damage when ceil(target total PP / (1 + any able party member of ours has Pressure)) is ≤ the most turns the battle can still last (balls above the reserve, plus remaining status tries, plus the no-progress cap). Add rows: total PP 20 with 30 balls → no damage; the same target with 5 balls → admitted; our Pressure lead.
VERDICT: refuted=False corrected=should-fix
REASONING: The finding holds. The design gives a binary rule: damage is allowed only if the target "can hurt ITSELF in NO way this battle" (DESIGN:122-123). It also says k, the number of turns, is unbounded (:131). Yet it counts Struggle as a risk only when total PP ≤ 4 (:124-125).

Nothing else in the design limits how long the battle runs after the damage turn. The per-battle caps at :109 limit only damage (1), status tries (3) and no-progress turns (2). After those, the bot keeps throwing until the target is caught or the bag is empty (story_mode.py:85-93). For a dex catch it stops at the 10-ball reserve or when one of our mons faints (story_mode.py:111-116, DEX_CATCH_BALL_RESERVE = 10 at :1681). The fixture carries 30 balls. So a battle can run 20 to 30 or more turns, and any target with 5 to about 30 total PP can run dry and Struggle inside the window this rule claims to cover.

The number 4 comes from v2 (v2:628, and :732 "Struggle PP 4 | Judgements"), which allowed up to 3 damage turns. It was never re-derived for the new whole-battle premise. The design text does not handle this case anywhere else.

The mechanics check out in the decomp. One detail makes the fix conservative rather than wrong: a wild mon that picks a move with 0 PP just wastes its turn (bsc.c:934). So Struggle starts no earlier than total PP ÷ (1 + Pressure) of the wild's turns, never sooner.

The effect is real, so the finding is not refuted. A concrete low-PP target exists in the story: a Zubat from 5 to 10 PP. It is not a blocker. Stage 1 almost never acts (DESIGN:7-16) and stage 2 is OFF. The one current example is a Zubat from 5 to 10 PP with catch rate 255. With a Poké Ball it catches about 34% per throw, so it would have to break free roughly 15 times in a row (about 0.2%). With a Great Ball its one-throw chance is about 0.50, which makes it THROW-ONLY (:108). Every other target under about 30 PP is already covered: Abra (Teleport, an ender), Sootopolis Gyarados (Thrash, rampage) and Claydol (Selfdestruct). Ditto (Transform, 10 PP, then at most 5 PP per move after it transforms) is the realistic KO case: a hard catch, and damage is allowed before the Transform happens (D13 blocks damage only after the species changes). But Ditto is found only in the Desert Underpass, after the League.

A smaller flaw in the proposed fix: a team catch has no reserve (StoryCatchStrategy throws until the bag is empty), so "balls above the reserve" should count ALL balls for that kind.
V-EVIDENCE: Design: DESIGN.md:122-123 "Damage is admissible only if the target can hurt ITSELF in NO way this battle"; :124-125 "Struggle-risk (total PP ≤ 4)"; :131 "k is unbounded"; :109 caps cover only damage (1), status (3) and no-progress (2) turns, not throws. The constant was inherited: v2:628 "total PP ≤ 4 (Struggle)" and v2:732 "Struggle PP 4 | Judgements". Adversary recon N7 (w12_recon_adversary.md:193) already flagged this constant as underspecified.

Decomp (local copy of pret):
- src_battle_controller_opponent.c:1597-1601 — the wild's random move pick, with no PP check (AI runs only for TRAINER|FIRST_BATTLE|SAFARI|ROAMER, :1561).
- src_battle_main.c:4184-4191 — AreAllMovesUnusable, run on every B_ACTION_USE_MOVE.
- src_battle_util.c:1125-1136 and :100-105 — noValidMoves forces MOVE_STRUGGLE.
- src_battle_script_commands.c:1224-1225 — the defender's Pressure adds 1 PP per use.
- :2636-2639 — RECOIL_25 is gHpDealt/4, minimum 1.
- src_battle_scripts_1.s:3939-3940 — `jumpifmove MOVE_STRUGGLE, BattleScript_DoRecoil` skips the Rock Head check.
- :7793-7799 — Transform sets PP to ≤5 per move.
- src_battle_script_commands.c:934 — a 0-PP pick fails without using PP, so Struggle starts later than the total-PP count.

Our code:
- story_mode.py:85-93 — StoryCatchStrategy throws until the bag is empty, then flees.
- :100-116 — the dex bail at the reserve or a faint; "one Absol took 23 balls".
- :1681 — DEX_CATCH_BALL_RESERVE = 10.

Reachable low-PP targets, taken from the decomp's wild_encounters.json and level-up learnsets:
- Zubat L5-10: cave surf slots (Meteor Falls 1F_1R, Seafloor Cavern, Shoal Cave, `water_mons` 5-35). It knows only Leech Life (15 PP) and is in none of the design's exclusions.
- Covered by other rules: Abra (Teleport 20, ender); Gyarados in Sootopolis (Thrash 20, rampage); Claydol (Selfdestruct).
- Ditto: Transform 10, Desert Underpass only (post-League).

## mechanics:W12M-S3 [should-fix] 2026-09-30-weaken12-DESIGN.md:91-92 (catch_p 'full ball table'), :108 (one-throw chance ≥ 0.5), :138, :142 (E-gain ≥ 1.0); v2 :638, :732
CLAIM: MISSING. Three things are never defined: the E-gain formula, which ball the 0.5 rule and the E-gain assume, and which status they assume. So neither the rows nor a fault can be written before the code. The THROW verdict also has to throw exactly the ball the parent would throw. If THROW is implemented as super(), the parent can apply a status move instead.
EVIDENCE: The parent chooses its ball again every turn with _get_best_poke_ball: the allowlist first (catch.py:212-233, allowlist :215-226), then float multipliers (catch.py:235-277). Those multipliers change during a battle: the Timer Ball's goes up each turn (catch.py:274-275; game battle_script_commands.c:9971-9974). Net Ball uses the SPECIES types in the parent (catch.py:253-256) but the LIVE types in the game (:9941-9942). The dex fence already learned that the whole bag matters, not just its best ball (story_mode.py:1737-1741; dex_catch_expected_throws_seq). Status multiplies odds ×2 or ×1.5 (:9991-9994), but sleep lasts only 1-4 of the target's turns (:2481; battle_util.c:2015-2030). Under the design's STATUS-then-DAMAGE order, a damage decision usually sees a sleeping target, and its E-gain then comes out at roughly half the awake value. If THROW went through super(), the parent would use a status move when the target is Healthy and the chance is below 0.5 (catch.py:50-60). D12's row 'catch_p agrees with dex_catch_expected_throws' only holds for the four balls in _BALL_BONUS_X10 (story_mode.py:1703, default 10 at :1741).
FIX: Define E_gain = E(hp, status, ball sequence) − E(hp − X_min, status, same sequence). Take the ball sequence from `_get_best_poke_ball`'s order over the allowed bag (the seq model, with catch_p at the given HP and status). State whether the damage turn's own cost is netted out, and that the current status is used (conservative). Use the parent's current best ball for the 0.5 rule. THROW returns TurnAction.use_item(self._get_best_poke_ball(state)). Limit D12's agreement row to Poké, Great, Ultra and Safari.
VERDICT: refuted=False corrected=should-fix
REASONING: The core of the finding holds, and the fixture's own numbers make it stronger than the reviewer showed. Two sub-claims are overstated.

1. E-gain has no formula anywhere. A grep of the whole worktree finds "E-gain" only as a bare threshold:
   - design :138 and :142;
   - v2 :638, :647 ("the E-gain" row), :732 and :841;
   - adversary recon S12 (:171-176) and decomp recon :306.
   v1 §4b (2026-09-28-r23-25-DESIGN.md:497-569) talks about expected throws but gives no formula. The design also never says which ball or which status the 0.5 rule (:108) or the E-gain assumes. D3 (:91-92) gives catch_p a full ball table but does not say which ball to evaluate it at.

2. This is load-bearing on the design's own W-EXEC arm (:207, D8 :163-167). I recomputed with the decomp formula: Seismic Toss for 13, Poké Ball (bonus 10), a healthy target, Route 116 catch rates from species_info.h (Taillow 200, Skitty 255, Whismur 190, Nincada 255).
   - The gross gain E(full) − E(full−13) is 1.69 to 1.97, so damage is admitted.
   - With the damage turn's own cost netted out, it is 0.69 to 0.97, so damage is refused and ON throws exactly as OFF does.
   - So one unstated definitional choice decides whether the arm has a discriminator at all.
   - The ball matters too. With a Great Ball, Skitty, Nincada and Poochyena reach a one-throw p of 0.503, which is ≥ 0.5, so they are THROW-ONLY, and the gross gain drops to 0.99, which fails ≥ 1.0.
   - So is the status. Asleep, p roughly doubles, the E-gain for these targets falls to between 0.27 and 0.99, and every such case fails. Under D4's STATUS-before-DAMAGE order (:111 before :122), that is exactly the state a damage decision usually sees.
   - D11 (:176-179) requires the W-rows and exact fault sets to be filed before the code. None of this can be pinned without a definition. The effect is bounded: the hp − X ≥ 1 bound and the no-self-harm rule are independent of E-gain, so no KO or hang results. That makes it should-fix, not a blocker.

3. Overstated: the claim that THROW could be implemented as super(). The design's own :44-46 rules out routing THROW-ONLY through the parent: "THROW-ONLY, never DEFER: a DEFER hands the turn to the parent's status chooser (CS:50-60)". So the intent is already stated. What is missing is only an explicit line saying which ball THROW uses. The parent picks its ball every turn at catch.py:42, allowlist at :212-233.

4. Refuted: the claim that D12 only holds for four balls. `dex_catch_expected_throws(catch_rate, ball_bonus_x10)` (story_mode.py:1768-1784) takes the multiplier as a parameter. The four-ball name map `_BALL_BONUS_X10` (:1703) is used only by the adapter `_expected_throws_for` (:1736). At full HP, the game computes (x·M)//(3M), and the function computes x//3; these are equal for any bonus. So D12's agreement row can be written for any ball, and there is no need to restrict it to Poké, Great, Ultra and Safari.

Corrected fix:
- Define E-gain explicitly: gross or net of the damage turn, and in balls or in turns.
- Name the status used (the current snapshot is the natural choice) and the ball used, which should be the parent's _get_best_poke_ball at that turn, or the seq model over the allowed bag.
- State that THROW returns use_item(self._get_best_poke_ball(state)).
- Pin the W-EXEC discriminator with these numbers.
- Drop the D12 narrowing.
V-EVIDENCE: Our code:
- catch.py:41-62: decide_turn calls _get_best_poke_ball every turn (:42). The status move is used when the target is Healthy and the chance is below 0.5 (:50-60).
- catch.py:212-233: the allowlist.
- catch.py:252-256: Net Ball uses species.has_type.
- catch.py:274-275: Timer Ball uses min(4.0, (10+current_turn)/10).
- story_mode.py:1703: `_BALL_BONUS_X10`, four balls.
- story_mode.py:1733-1741: the whole-bag seq adapter, default 10.
- story_mode.py:1768-1784: dex_catch_expected_throws(catch_rate, ball_bonus_x10) is parametric in the bonus.
- story_mode.py:85-93: the adapter site, flee then super().

pret/pokeemerald master (fetched 2026-09-30):
- battle_script_commands.c:841: sBallCatchBonuses.
- battle_script_commands.c:9941-9942: Net Ball uses IS_BATTLER_OF_TYPE, the live types.
- battle_script_commands.c:9971-9972: Timer uses battleTurnCounter + 10.
- battle_script_commands.c:9987-9994: odds, with sleep ×2 and the others ×1.5.
- battle_script_commands.c:10009: odds > 254 is a certain catch.
- battle_script_commands.c:2481: sleep lasts 2-5 counter ticks.
- battle_util.c:2015-2030: the sleep decrement.

Design and specs:
- The design's :44-46 already forbids handing THROW-ONLY to the parent's status chooser.
- The design's :91-92, :108, :138, :142 and v2 :638 and :732 use E-gain without defining it. A grep finds no definition anywhere in the tree.

Computed (scratchpad egain_check.py, the decomp formula with integer isqrt steps), Seismic Toss 13, Poké Ball, healthy target:
- Skitty, Nincada, Poochyena: E 2.97 → 1.27, gross 1.69, net 0.69.
- Taillow, Whismur: E 3.57 → 1.60, gross 1.97, net 0.97.
- With a Great Ball: Skitty's p_full is 0.503, which is ≥ 0.5, so the target is THROW-ONLY.
- Asleep with a Poké Ball: gross 0.27 to 0.99, all < 1.0.

## mechanics:W12M-N1 [nit] 2026-09-30-weaken12-DESIGN.md:94, :111-145 (order DEFER → THROW-ONLY → STATUS → DAMAGE)
CLAIM: The design reverses v2's 'damage first, then sleep, so no sleep turns are spent on damage' (v2:604) and gives no reason. With status first, the single damage turn uses up one of the target's 1-4 turns asleep. This costs efficiency only, not safety.
EVIDENCE: The sleep counter starts at 2-5 (battle_script_commands.c:2481) and goes down on each of the sleeper's move attempts. It wakes when the counter hits 0 (battle_util.c:2015-2030), so it sleeps through 1-4 of its turns. A damage turn gives the target one of those attempts.
FIX: Either restore damage-first while the target is awake and above 50%, or record why status-first was chosen (the target cannot act while asleep) as a 06 decision.
VERDICT: (none: a nit, not sent to a refuter)

## mechanics:W12M-N2 [nit] 2026-09-30-weaken12-DESIGN.md:119 (skip STATUS if the target holds Chesto/Lum or Cheri/Lum)
CLAIM: On when these berries trigger: the berry cures at MOVE_END of the SAME turn and is then used up. So one try would remove it, and a skip gives up the ×2/×1.5 status for the whole battle. The trade-off is 1 of 3 tries against giving up status completely.
EVIDENCE: ITEMEFFECT_MOVE_END runs at battle_script_commands.c:4331. Chesto cures sleep there (battle_util.c:3663-3671), and BattleScript_BerryCureSlpRet then does removeitem (data/battle_scripts_1.s:4314-4320). Wild holders: Chesto is a 5% rare item on Spinda, Whismur, Loudred and Exploud (species_info.h:8567, 10427, 10457, 10487). Lum is held only by Mew and Celebi (:4556, :7556). No wild species holds Cheri.
FIX: Allow one try against a berry holder, counted against the 3-try cap, or record the skip as deliberate.
VERDICT: (none: a nit, not sent to a refuter)

## mechanics:W12M-N3 [nit] 2026-09-30-weaken12-DESIGN.md:109 (cap: 1 damage turn)
CLAIM: For exact damage, the one-damage-turn cap rules out a second hit that would still be KO-safe and still allowed by the 50% rule. This costs efficiency only.
EVIDENCE: Super Fang does hp/2, minimum 1 (battle_script_commands.c:7577-7584). With an odd max HP of 45, a hit from full leaves 23 HP, which is above 50%. A second Super Fang leaves 12, which is safe. Seismic Toss from our L13 lead against a 40-HP target leaves 27 (above 50%), and a second hit leaves 14.
FIX: Keep the cap at 1 for stage 2 (W = 1). For stage 1, let the 50% and hp − X ≥ 1 gates govern, with a small cap, or record the choice.
VERDICT: (none: a nit, not sent to a refuter)

## mechanics:W12M-N4 [nit] 2026-09-30-weaken12-DESIGN.md:37 ('Wonder Guard blocks all four (power 1)')
CLAIM: REFUTED as written. Wonder Guard lets a super-effective hit through, and Night Shade is super-effective against a Ghost-type Wonder Guard holder (Shedinja). This does no harm, because the admission rule already refuses every Wonder Guard target and no wild species has the ability.
EVIDENCE: The Wonder Guard test requires !SUPER_EFFECTIVE (battle_script_commands.c:1409-1419), and it runs inside typecalc, before the scripts' bicbyte (data/battle_scripts_1.s:1200-1201). Ghost vs Ghost is ×2 (src/battle_main.c:431). Shedinja is the only Wonder Guard species (species_info.h:8423).
FIX: Reword to 'blocks all four except a super-effective one (Night Shade vs a Ghost type)', so no W-row expects Night Shade to deal 0 to Shedinja.
VERDICT: (none: a nit, not sent to a refuter)

### checked and found true
- VERIFIED: catch_p's integer order is exactly odds = ((rate*mult/10) * (3*maxHP - 2*hp)) / (3*maxHP), then sleep/freeze ×2 and psn/brn/par/toxic ×15/10 (integer), then odds > 254 means certain, else b = 1048560 / Sqrt(Sqrt(16711680/odds)) and 4 checks of Random() < b (pret src/battle_script_commands.c:9987-9994, :10009, :10025-10028). dex_catch_expected_throws (story_mode.py:1774-1789) is exact at full HP, because (a*M)//(3M) == a//3.
- VERIFIED ball conditions (battle_script_commands.c:9941-9979). Net ×3 uses the LIVE battler types. Dive ×3.5 only on MAP_TYPE_UNDERWATER. Nest is 40-level for level < 40, floored to 10 when ≤ 9, and 10 at ≥ 40. Repeat checks the caught flag of the live species. Timer is battleTurnCounter+10, capped at 40. Luxury and Premier are 10. Master is forced (:10030-10031).
- VERIFIED, and this settles the recon's UNVERIFIED Timer item: gBattleResults.battleTurnCounter is at offset 0x13 (include/battle.h:247), which is exactly what battle_state.current_turn reads (battle_state.py:822). It goes up once per turn (battle_main.c:3995-3997), so keying the caps on current_turn is sound.
- VERIFIED: a ball throw has no Substitute or semi-invulnerable test. The only blocks are trainer and Wally battles (battle_script_commands.c:9915-9926, the whole of 9905-10053), so THROW-ONLY (not DEFER) is right for those targets.
- VERIFIED: the sleep script checks, in order, Substitute, already asleep, Uproar/Insomnia/Vital Spirit, any status, accuracy, then Safeguard, and has no typecalc (data/battle_scripts_1.s:284-298). Insomnia and Vital Spirit are read from the live ability (battle_script_commands.c:6828-6848). Uproar on any battler blocks sleep (:6801-6826), but a Soundproof target is exempt (:6807), so the design's Uproar skip is slightly conservative.
- VERIFIED: the paralysis script checks Limber (live), Substitute, typecalc, any status, accuracy, then Safeguard (battle_scripts_1.s:1007-1025). Thunder Wave vs Ground is ×0 (battle_main.c:356). Glare vs Ghost is ×0 in a row after the Foresight marker (:445-446), so Foresight lifts it. Wonder Guard does not block status moves, because its test needs power ≠ 0 (battle_script_commands.c:1409-1419).
- VERIFIED: our moves.json is_sound_move set matches sSoundMovesTable exactly (battle_util.c:688-692; 10 moves, spelled 'Grasswhistle'), so keying Soundproof on that flag is correct.
- VERIFIED: Synchronize passes back poison, toxic (as poison), paralysis and burn, never sleep (battle_script_commands.c:2501-2511; battle_util.c:2957-2970). Magic Coat has priority 4 (src/data/battle_moves.h:3604-3613), so a target that knows it can bounce the move in the same turn.
- VERIFIED exact damage. All four scripts run typecalc and then clear the effectiveness flags (battle_scripts_1.s:809-827, :1195-1204, :1720-1729). LEVEL_DAMAGE is the attacker's level (battle_script_commands.c:7926-7930). Super Fang is hp/2 with minimum 1, so it is KO-safe at hp ≥ 2 (:7577-7584). Immunities: Ghost→Normal is before the Foresight marker, so Foresight never lifts it (battle_main.c:427). Normal/Fighting→Ghost are after it (:446-447; marker handling at battle_script_commands.c:1388-1391). Dragon has no ×0 row. Levitate only affects Ground moves (:1375), so it does not matter for these moves.
- VERIFIED Kecleon: Color Change fires after a damaging hit (power ≠ 0) that damaged it (battle_util.c:2738-2751). So it cannot change the immunity of the hit that triggers it, and D13's re-read each decision covers the turns after.
- VERIFIED Encore at selection time (battle_main.c:4192-4196) and at execution time (battle_util.c:110-117). encoredMove is at DisableStruct offset 0x06 (include/battle.h:70-74), while our reader uses 0x04 (battle_state.py:729-734), so D9's KI is correct. Torment, Disable, Taunt, Imprison and Choice refuse a pick at selection only. In the middle of a turn they only make the move fail, and never swap in another move.
- VERIFIED: Struggle recoil is 1/4 of damage dealt, minimum 1, and ignores Rock Head (battle_scripts_1.s:3938-3940; battle_script_commands.c:2636-2639). Belly Drum needs hp > max/2 and costs max/2 (:8785-8796). Explosion fails only if any battler has Damp (:6543-6547). Weather chip immunities are as the design says: sand spares Rock/Steel/Ground types, Sand Veil and Dig/Dive; hail spares Ice types and Dig/Dive; Cloud Nine or Air Lock on the field stops both (battle_script_commands.c:7602-7652; include/battle_util.h:47).
- VERIFIED: there are no wild doubles. battle_setup.c sets BATTLE_TYPE_DOUBLE only for trainers (:1275). Wild setups are at :408, :427 (roamer), :441 (safari), :451 (pike), :493, :505/:517/:556/:576 (legendary flags).
- VERIFIED: the one-throw 0.5 threshold matches the parent's rule (catch.py:50-62), and the float calculate_catch_success_chance has no odds > 254 branch (_util.py:271-294), so D12 is right not to use it.
- Checked and NOT reachable, so no finding: disobedience can run a different move (battle_util.c:3910-3948), but only for an outsider-OT mon before badge 8, and the story code has no in-game trade. Pain Split lowers HP before our hit, but only Misdreavus learns it (level_up_learnsets.h:2764), and it is not a wild in Emerald. No wild species holds a confusion pinch berry (no ITEM_FIGY/WIKI/MAGO/AGUAV/IAPAPA in species_info.h).
# LENS proof

## proof:W12-LP1 [blocker] 2026-09-30-weaken12-DESIGN.md:208 (W-FAULT row), with D4 :109-110, :122-137 and D8 :163-167
CLAIM: W-FAULT can never bind on this fixture with Seismic Toss, and its pass column lets it pass anyway ("or the arm is declared vacuous with its reason"). The design's own rules keep the target at FULL HP at every stage-1 damage decision, so neither hp − X ≥ 1 nor the >50% rule can change a verdict. As a result no live arm can observe a KO: the EXEC arm's "not KO'd" and D6's "0 res=Won" also cannot fail.
EVIDENCE: Why the target is always at full HP (hp = M) when DAMAGE is chosen: (a) the cap is 1 damage turn per battle (:109); (b) STATUS comes before DAMAGE, and stage 1 applies only sleep and paralysis, which cost no HP (:111); (c) NO-SELF-HARM is binary and excludes every way the target can hurt itself (:122-129); (d) Route 116 has no weather; (e) a wild mon starts at full HP. So hp − X ≥ 1 reduces to M > X, and '>50%' is always true.

The numbers:
- Max HP of the targets. Formula: floor((2·base+IV)·L/100)+L+10.
  - Taillow: base HP 40 (modules/data/species.json), L6-8 (w12/all_fixtures.txt:768), so M is 20-26.
  - Skitty: base 50, L7-8, so M is 24-28.
  - Abra is THROW-ONLY (it knows only Teleport, so it is an ENDER).
- Damage: X = the lead's level. It is 13 at load (all_fixtures.txt:764) and 15 at the only recorded first catch (evidence/2026-09-28-r20P2a-ON-240k-window.txt:24 'Mudkip:L15', :27-29 Taillow start).
- Smallest margin: M − X ≥ 20 − 17 = 3 even at L17.
- Super Fang can never bind either, since hp − hp//2 ≥ 1.

So every candidate fault that skips hp − X ≥ 1 is inert. The ARMS row then passes by declaration.
FIX: Drop the 'declared vacuous' exit. Make the fault bind by construction with a second lever value, Dragon Rage (effect DRAGON_RAGE, 40 fixed damage).
- Why it works:
  - pret data/battle_scripts_1.s:819-827 sets 40 after typecalc.
  - No Gen-3 type is immune to Dragon: its only attacking rows are src/battle_main.c:432-433, a super-effective one and a not-very-effective one.
  - 40 is more than the max HP of every Route 116 target (≤ 28).
- Arms:
  - DR-OFF ×2: the lever, flags unset. The parent throws.
  - DR-ON: WEAKEN=1. It must THROW at the discriminator turn (= DR-OFF).
  - DR-FAULT: skip hp − X ≥ 1. Expected reads:
    - BEFORE mv[0] = 82 and act[0] = 0;
    - Δbide[1] = 40;
    - AFTER kind=end with the foe's HP at 0;
    - `[CATCH] end … res=Won`.
- Pre-register that the implemented E-gain path does not raise when hp_after ≤ 0. If it raised, the adapter's try would DEFER and the fault would stop binding. The decomp formula gives odds 309 > 254, so p = 1.0 at hp = −18, and 200 (p 0.785) if clamped to 0; either way it admits.
VERDICT: refuted=False corrected=blocker
REASONING: The core claim holds. As written, W-FAULT can never bind on this fixture, and its pass column then passes it by declaration, which is exactly the rubric's "make an arm unable to fail".

**Why the target is always at full HP (hp = M) at a stage-1 damage decision**
- The cap is 1 damage turn per battle (DESIGN:109).
- The lever gives the lead no status move. Mudkip holds Tackle, Growl, Mud-slap and Water Gun (all_fixtures.txt:764), so nothing before the damage turn costs the target HP.
- NO-SELF-HARM rejects every self-damage source (DESIGN:122-128). The wanted Route 116 targets carry none anyway: the wild table at all_fixtures.txt:768 marks only Taillow, Abra and Skitty as new, and the old run's team catches were exactly those three (evidence r20P2a:24-25, :64-65, :70-71). Abra is Teleport-only, so it is THROW-ONLY (DESIGN:106).
- The parent only throws in a catch battle.

So at the only damage turn, >50% is trivially true, and `hp − X ≥ 1` reduces to M > X.

**The numbers (decomp HP formula, pokemon.c:2851-2852, wild EVs 0)**
- Taillow: base HP 40 (species_info.h:8431). At L6 with IV 0, M = 80·6/100 + 16 = 20.
- Skitty: base HP 50 (:8761). At L7 with IV 0, M = 24.
- X is the lead's level (Seismic Toss is `dmgtolevel`, battle_scripts_1.s:1195-1203). It is 13 at load (all_fixtures.txt:764).
- In the recorded 240k window the team catches happened at lead L15 (Taillow, r20P2a:23-25) and L17 (Skitty, :69-71), and `[CATCHTEAM] exit` came at party 6 (:72). The lead reached only L19 by the window's end (:88).
- A bind needs X ≥ 20 against a Taillow of IV 0-3. That is outside the window and not a computable arm.
- Super Fang can never KO (hp − hp//2 ≥ 1).

Dropping `hp − X ≥ 1` therefore changes no verdict. The design does not handle this. W-FAULT is "the EXEC arm plus a fault", and the EXEC arm is pinned to Seismic Toss with Δbide = 13 (DESIGN:207, D8:165). Its parenthetical "chosen so that it binds … by computation" is unsatisfiable with that lever, and the "or the arm is declared vacuous" exit (:208) turns that certainty into a pass. It also breaks the project's rule 4: a check must assert something the run does not already satisfy.

**Where the finding overstates**
1. "The EXEC arm's 'not KO'd' and D6's '0 res=Won' cannot fail" is too strong. They cannot detect a missing hp−X bound, but they can still catch other defects. Example: a dispatch bug or a CALC leak executes Water Gun. That hit is STAB and roughly 21-25 against Taillow's 20-26 HP, so it could KO. They are weak readouts for this bound, not impossible ones.
2. The bound is not wholly unproven. D11/G-W's production-env fault rows (DESIGN:176-180) test it offline. Only the LIVE proof is vacuous. That limits the harm, but it does not rescue W-FAULT's pass column, which the rubric covers directly.

**The proposed Dragon Rage fix checks out on the decomp**
- It sets 40 after typecalc (battle_scripts_1.s:819-827).
- Dragon's only attacking rows are vs Dragon (SE) and vs Steel (NVE) (battle_main.c:432-433), so nothing on Route 116 is immune.
- 40 exceeds every target's max HP (Taillow ≤ 26, Skitty ≤ 28).
- MOVE_DRAGON_RAGE is 82 (include_constants_moves.h:86).

One caveat on the fix: D8's "EMPTY slot" does not exist. The fixture's Mudkip holds four moves (all_fixtures.txt:764), so any lever, Dragon Rage included, must overwrite a slot. The fix's pre-registered "mv[0] = 82 / act[0] = 0" has to name the slot actually written. That is a separate D8 defect, not a reason to refute this one.
V-EVIDENCE: **The design's own text**
- DESIGN:109: "1 damage turn".
- DESIGN:122-129: NO-SELF-HARM is binary, "Then the only bound left is the hit itself: hp − X ≥ 1".
- DESIGN:133-137: LEVEL_DAMAGE = our level, then ">50% of max" and "hp − X ≥ 1".
- DESIGN:165: "gives the fixture's lead Mudkip (L13) Seismic Toss in an EMPTY slot".
- DESIGN:207: EXEC arm "Δbide = 13".
- DESIGN:208: W-FAULT "the EXEC arm plus a fault that skips hp − X ≥ 1 … or the arm is declared vacuous with its reason".

**The fixture and the past run**
- scratchpad/w12/all_fixtures.txt:764: "0 Mudkip … L13 … Tackle, Growl, Mud-slap, Water Gun". Four moves, so no empty slot.
- all_fixtures.txt:768: "Taillow!NEW 20% L6-8; Abra!NEW 10% L7-7; Skitty!NEW 2% L7-8".
- evidence/2026-09-28-r20P2a-ON-240k-window.txt:
  - :23-25: Taillow team catch with lead Mudkip L15; Taillow HP 22.
  - :64-65: Abra (the 3rd target) ends `res=OpponentTeleported` after one throw, which is why it is THROW-ONLY.
  - :69-71: Skitty team catch with lead Marshtomp L17; Skitty HP 25.
  - :72: `[CATCHTEAM] exit … party=6`.
  - :88: the lead reaches only L19 by the window's end.

**pret/pokeemerald**
- pokemon.c:2851-2852: newMaxHP = ((2·base + IV) + EV/4)·L/100 + L + 10.
- species_info.h:8431 (Taillow baseHP 40) and :8761 (Skitty baseHP 50). So the minimum M is 20 (Taillow L6, IV 0) and 24 (Skitty L7, IV 0).
- battle_scripts_1.s:1195-1203: LevelDamage runs typecalc, then dmgtolevel.
- battle_scripts_1.s:809-817: Super Fang uses damagetohalftargethp, so it can never KO.
- battle_scripts_1.s:819-827: Dragon Rage runs typecalc, then `setword gBattleMoveDamage, 40`.
- battle_main.c:432-433: Dragon's only attacking rows are vs Dragon and vs Steel.
- include_constants_moves.h:86: MOVE_DRAGON_RAGE is 82.

**The arithmetic**
- With X ≤ 19 across the window and M ≥ 20, `hp − X ≥ 1` always holds at full HP, and >50% is always true. So the fault changes no verdict, and W-FAULT exits via "declared vacuous".

## proof:W12-LP2 [should-fix] 2026-09-30-weaken12-DESIGN.md:163-167 (D8)
CLAIM: D8 says the lever puts Seismic Toss 'in an EMPTY slot, so no existing move is lost'. The fixture's Mudkip has no empty slot: it knows 4 moves. So the lever must OVERWRITE a move, and D8 names neither the slot nor the write or read-back mechanics.
EVIDENCE: The fixture's Mudkip:
- It knows Tackle 31/35, Growl 40/40, Mud-slap 10/10 and Water Gun 7/25 (w12/all_fixtures.txt:764; w12_recon_fixture.md:18).
- The decomp gives it 4 moves by L10 (level_up_learnsets.h:3676-3680).

How a faithful write can be done:
- The existing precedent is game_cheats.py:189-227 (`_rebuild_party`).
- It calls `debug_create_pokemon(original_pokemon=mon, …)`, passing EVERY field. It must: the defaults silently reset `held_item=None` (debug_utilities.py:121) and `friendship=70` (:125).
- What `debug_create_pokemon` does:
  - it keeps the PV when nature, gender and shiny match (:327-356);
  - it recomputes the checksum over the 24 decrypted u16 (:366);
  - it re-encrypts in the PV%24 substruct order (:386-392).
- `debug_write_party` then writes gPlayerPartyCount plus 600 bytes (:476-492).

Why the checksum matters: GetBoxMonData checks it, and a mismatch turns the mon into a Bad Egg (pret src/pokemon.c:3742-3746).

The game picks up a party write made in the overworld at battle start:
- REQUEST_ALL_BATTLE (src/battle_main.c:3363);
- the player controller reads MOVE1+i and PP1+i through GetMonData (src/battle_controller_player.c:1619-1625);
- the result is copied into gBattleMons (src/battle_main.c:3414-3416).

The read-back trap: get_party() is frame-cached (pokemon_party.py:279-280). A same-frame read-back returns the PRE-write party, the same trap --set-balls documents (story_harness.py:28997-28998).
FIX: Rewrite D8 as `--set-lead-move 1=Seismic Toss`, overwriting move slot 1 (Growl, 0 power).
- Why slot 1: the strategies never select it. The story move-learn policy then DECLINES Bide at L15, because Normal is already covered by the stronger Tackle (SM:694-703), and Mud Shot at L16 replaces Mud-slap. So Seismic Toss survives to Marshtomp.
- The write: build the mon with every field passed, as game_cheats.py:205-221 does, keeping each move's pp_ups.
- The read-back: raw `read_symbol('gPlayerParty', size=100)` → `Pokemon(...)`. Assert all of:
  - `is_valid`;
  - PID == 0x550A9BE6;
  - moves, PP, friendship, held item and exp as intended.
- On a mismatch, RAISE, as story_harness.py:29028-29032 does.
VERDICT: refuted=False corrected=should-fix
REASONING: The core claim holds. D8 (DESIGN.md:165) says the lever gives the fixture's lead Mudkip (L13) Seismic Toss "in an EMPTY slot, so no existing move is lost". That fixture's Mudkip already knows four moves, so there is no empty slot. The lever has to OVERWRITE one, and D8 does not say which. Nothing else in the design covers this: the W-EXEC row (:207) only says "the lever (D8)", and nowhere is a slot or the lost move named. The `<slot>=<move>` syntax does take a slot, but D8 never picks one for this fixture. Its stated property, that no existing move is lost, is false.

One sub-claim is overstated. The finding says D8 names no read-back mechanics, but D8:164 says "read back and logged like `--set-balls`". That lever reads back from the save block, never the frame-cached accessor, and it RAISES on a mismatch (story_harness.py:28997-28998, :29028-29032). So the read-back is specified by analogy. What the analogy lacks is the party-specific path: the raw gPlayerParty read, because get_party() is frame-cached (pokemon_party.py:279-280). That gap is minor. The unnamed overwrite plus the false premise is the real defect.

Why should-fix and not blocker:
- It is a test lever, so nothing changes with the flags unset.
- The ON and OFF EXEC arms both carry the lever, and the discriminator is computed on the arm's own trajectory (:167), so the lost move affects both arms equally.
- A literal "empty slot" build would find no empty slot, and with the `--set-balls`-style raise it would abort rather than run silently. No arm is made unable to fail.
- The design still has to make a choice it does not make: which move to lose, and whether Seismic Toss survives the later move-learns.

The proposed slot 1 (Growl) checks out against our own policy:
- The policy is story_mode.py:603-713. With moves [Tackle, Seismic Toss, Mud-slap, Water Gun] there is no status slot.
- At L15, Bide (Normal, power 1, pret battle_moves.h:1524-1528) arrives with Normal already covered and no weaker Normal move to replace, so the policy DECLINES (:693-703).
- At L16, Marshtomp's Mud Shot is Ground, which Mud-slap already covers, so it replaces the weaker Mud-slap.
- Seismic Toss therefore survives.
V-EVIDENCE: - **The design's own text:** DESIGN.md:163-167 (D8): "`--set-lead-move <slot>=<move>` ... read back and logged like `--set-balls`. It gives the fixture's lead Mudkip (L13) Seismic Toss in an EMPTY slot, so no existing move is lost."
- **The fixture's Mudkip has four moves:**
  - scratchpad/w12/all_fixtures.txt:764 (`r20_pregym1_party4_r116.ss1`, md5 MATCH): `0 Mudkip #550A9BE6 L13 ... :: Tackle[HIT]31/35, Growl[ATTACK_DOWN]40/40, Mud-slap[ACCURACY_DOWN_HIT]10/10, Water Gun[HIT]7/25`.
  - w12_recon_fixture.md:18 gives the same four moves.
- **The decomp agrees:** pret level_up_learnsets.h:3676-3680 has Tackle and Growl at L1, Mud-Slap at L6 and Water Gun at L10, so the L13 Mudkip is full.
- **The read-back is specified by analogy, which is why that sub-claim is overstated:**
  - story_harness.py:28997-28998 explains why get_item_bag() is not used ("cached per frame, so a same-frame read returns the object from BEFORE the write").
  - story_harness.py:29028-29032 raises `RuntimeError` when the read-back mismatches.
  - pokemon_party.py:279-280: `get_party` returns the cached party when `age_in_frames == 0`.
- **Write precedent:**
  - game_cheats.py:189-224: `_rebuild_party` passes held_item, friendship, experience, ivs/evs and the rest to `debug_create_pokemon`.
  - The defaults `held_item=None` and `friendship=70` are at debug_utilities.py:121 and :125.
- **Slot 1 survives the move-learns:**
  - Seismic Toss: pret battle_moves.h:900-904 (EFFECT_LEVEL_DAMAGE, power 1, Fighting). Bide: :1524-1528 (power 1, Normal).
  - Marshtomp learns Mud Shot at L16 (level_up_learnsets.h:3700).
  - story_mode.py:637-638 `is_damaging` = base_power > 0; :666-667 overwrites a status slot first; :693-703 handles a redundant type: upgrade a weaker same-type move, else DECLINE.

## proof:W12-LP3 [should-fix] 2026-09-30-weaken12-DESIGN.md:138 and :165-166 (stage-1 E-gain; D8's admissibility claim)
CLAIM: 'E-gain ≥ 1.0 throw' is defined nowhere in the design, v2 or v1. On this fixture, whether Seismic Toss is admissible at all depends on that definition, so W-EXEC can end up vacuous (ON throws = OFF) with no one noticing until the run.
EVIDENCE: Method: the exact decomp formula (src/battle_script_commands.c:9987-10028: integer odds, Sqrt(Sqrt), 4 shakes), with the Poké Ball the parent throws. That ball is confirmed by exp_throws=3.6 = 1/0.2797 at evidence r20P2a-ON-240k-window.txt:29, and by catch.py:212-239 (the Master Ball is never chosen).
- **Taillow** (rate 200):
  - full HP: odds 66, p 0.280;
  - after X = 13: hp 7-13, p 0.624. Gross E_full − E_after = 1.97; net of the spent turn = 0.97, which FAILS;
  - X = 14-17: gross 1.97-2.30, net 0.97-1.30, depending on the HP IV.
- **Skitty** (rate 255): p_full 0.337, p_after 0.785. Gross 1.69 (one case 1.97); net 0.69-0.97, which FAILS at every IV and every X from 13 to 17.
- **Abra**: THROW-ONLY (Teleport) before any damage check.
- The other stage-1 checks all pass:
  - >50% and hp − X ≥ 1;
  - progress: 13 ≥ 10% of 28;
  - the one-throw chance < 0.5;
  - type immunity: none (Fighting vs Normal/Flying, Normal, Psychic).
FIX: Write the E-gain formula into the predictions before the code, as E[throws | now] − E[throws | after hit] with or without the −1 for the turn spent. Then compute the W-EXEC discriminator with that formula, from the target's real maxHP read in the arm's own Step-0 runs.
- With the net definition, Skitty is never admissible, and Taillow only at X ≥ 14 with a small M. Say so, and pick the Taillow battle as the discriminator.
VERDICT: refuted=True corrected=nit
REASONING: **What survives: the gap is real but small.** The design (:138, :142), v2 (:638, :732) and v1 (2026-09-28-r23-25-DESIGN.md) all use "E-gain ≥ 1.0 throw" and never write down its formula. I re-derived the finder's numbers from the decomp formula and they are correct:
- Taillow, 22/22 HP, Poké Ball: odds 66, p 0.2798. After X = 13 (hp 9): odds 145, p 0.6243. Gross gain 1.97; with 1 subtracted for the turn, 0.97.
- Skitty, 25/25: odds 85, p 0.337. After X = 13 (hp 12): odds 173, p 0.785. Gross 1.69; minus 1, 0.69.

So a gross formula and a net one would give different verdicts on this fixture.

**What is refuted: the should-fix rating and the failure scenario.**

1. **Only the gross reading fits the project's vocabulary, and under it Seismic Toss is admitted.** In this project "throws" means BALLS.
   - `dex_catch_expected_throws` is documented as "Expected balls to catch a FULL-HP … target … the expectation is 1 / p" (story_mode.py:1768-1774).
   - Its companion's docstring says the same: "Expected balls … one throw per turn" (:1747-1748).
   - The `[CATCH]` line's `exp_throws=` is that same 1/p.
   - A damage turn spends no ball. So "E-gain ≥ 1.0 throw" means E[balls | now] − E[balls | after hit] ≥ 1.0.
   - The "minus one for the turn spent" version is the finder's own alternative. Nothing in the design suggests it.
   - Under the natural reading, both Taillow (1.97) and Skitty (1.69) pass at X = 13. The other stage-1 checks also pass (the finder agrees). So the arm is not vacuous for E-gain reasons.

2. **The design already catches vacuity before the run, so "no one noticing until the run" is wrong.**
   - D8 (:167): "The live arm's ON/OFF discriminator is computed at the Step-0 reads, on the arm's own trajectory."
   - The arms table (:199) is headed "to pre-register after the Step-0 reads".
   - W-FAULT (:208) allows "or the arm is declared vacuous with its reason".
   - D11 (:176-177) files the W-row table, with expected verdicts, in the PREDICTIONS BEFORE the code. v2's gate (:647) lists rows for "the E-gain". An expected verdict for such a row cannot be written without fixing the formula.
   - So the formula is pinned before the code, and the discriminator is computed from real Step-0 HP reads before the arm is registered. The finder's proposed fix is essentially the design's own procedure.

3. **"D8's admissibility claim" misreads D8.** D8 (:165-166) claims only that "Fighting is not immune against the Route 116 targets". That is true: Taillow is Normal/Flying, Skitty is Normal and Abra is Psychic, none immune to Fighting. D8 claims nothing about E-gain admissibility.

**Residual:** the formula should be written into the design in one line, E = 1/catch_p in balls, gross. That is a clarity nit, not a defect with an effect.
V-EVIDENCE: **Decomp** (scratchpad copy of battle_script_commands.c:9987-10028):
- `odds = (catchRate*ballMultiplier/10)*(maxHP*3-hp*2)/(3*maxHP)`
- `odds>254` means a certain catch.
- `odds = Sqrt(Sqrt(16711680/odds)); odds = 1048560/odds;` then four `Random() < odds` shake checks.

**Hand re-derivation (a Poké Ball has a multiplier of 10):**

| Target | Max HP | State | odds | p | E = 1/p |
|---|---|---|---|---|---|
| Taillow | 22 | full | 66 | 0.2798 | 3.574 |
| Taillow | 22 | hp 9 | 145 | 0.6243 | 1.602 |
| Skitty | 25 | full | 85 | 0.337 | 2.967 |
| Skitty | 25 | hp 12 | 173 | 0.785 | 1.274 |

- Taillow's full-HP p matches `exp_throws=3.6` in evidence/2026-09-28-r20P2a-ON-240k-window.txt:29.
- The max HP values come from that log: Taillow 22/22 and Skitty 25/25 appear in the `[BATTLE] started hp=` lines after each catch. Taillow was L6 and Skitty L7.

**Our code defines "throws" as balls:**
- sandbox-pokebot/plugins/custom_modes/story_mode.py:1768-1774: `dex_catch_expected_throws` — "Expected balls to catch a FULL-HP, status-free target … the expectation is 1 / p".
- The same file, :1747-1748: "Expected balls … one throw per turn".

**The design already makes the discriminator an input computed before the run:**
- 2026-09-30-weaken12-DESIGN.md:167: "The live arm's ON/OFF discriminator is computed at the Step-0 reads, on the arm's own trajectory."
- :199: "THE ARMS (to pre-register after the Step-0 reads)".
- :208: W-FAULT "or the arm is declared vacuous with its reason".
- :176-177: D11 files the "W-row table (id, snapshot, expected verdict) … in the PREDICTIONS BEFORE the code".
- 2026-09-29-r23-27-DESIGN-v2.md:647: the gate rows cover "the E-gain".

**D8's actual claim** (DESIGN.md:165-166) is only "Fighting is not immune against the Route 116 targets (Taillow, Skitty, Abra)". That is correct, and it is not an E-gain claim.

**The undefined term is confirmed:** a grep of PROJECT KNOWLEDGE finds "E-gain" only in the weaken12 design, its recon and v2 (:638, :732, :841). None of them gives a formula.

## proof:W12-LP4 [should-fix] 2026-09-30-weaken12-DESIGN.md:207 (W-EXEC pass: 'Δbide = 13') and :166
CLAIM: The pass value is hard-coded to the fixture's LOAD level. LEVEL_DAMAGE deals the lead's level on the catch turn. The only recorded trajectory reached its first catch at L15, so 'Δbide = 13' would fail on correct behaviour. This breaks CLAUDE.md rule 4 (derive the target from the state the run reached).
EVIDENCE: - Mudkip is L13 at load (all_fixtures.txt:764) and ended the battle at f154902 as 'Mudkip:L15' (r20P2a-ON-240k-window.txt:24).
- The first in-scope battle then started at f159430: Taillow, with Mudkip 44/44 leading (:27-29).
- Level damage = our level (the adversary note's reading of bs1.s:1195-1204).
- gBideDmg[1] accumulates the uncapped gBattleMoveDamage (src/battle_script_commands.c:1912).
FIX: Require Δbide[1] == gBattleMons[0].level, decoded from the BEFORE's `mons=` hex (offset 0x2A), and foe hp_after == hp_before − level > 0.
VERDICT: refuted=False corrected=should-fix
REASONING: The finding holds. The design's own D4 rule gets it right: "LEVEL_DAMAGE = our level" (DESIGN.md:133). The game uses the attacker's live battle level at the moment of the hit. But the design fixes the expected value at the fixture's load level in two places. D8 (:165-166) says "That is 13 fixed damage", and the W-EXEC pass (:207) says "Δbide = 13".

The lead is only L13 if the very first encounter is an in-scope target. Only Taillow (20%) or Skitty (2%) can qualify, because Abra's Teleport makes it an ENDER, which means throw-only (:117).

The one recorded trajectory on this fixture shows how fast the level moves:
- Mudkip went from L13 to L14 after the first wild win (window :7-8).
- It was L15 by f154902 (:24).
- It led the first in-scope battle, Taillow at f159430, at L15 with 44/44 HP (:27-29).

On a trajectory like that, correct behaviour gives Δbide = 15, and the arm as written grades it FAIL.

I looked for text that already handles this and found only partial cover:
- The arms heading says they are "to pre-register after the Step-0 reads" (:199).
- D8 says the discriminator is "computed at the Step-0 reads, on the arm's own trajectory" (:167).

Both of those derive WHICH turn to check, not the damage value. The value 13 is stated as fact in D8, and nothing marks it as a placeholder, so a pre-registration copied from this design would carry it over.

Severity stays should-fix, not blocker. The error makes the arm fail on correct behaviour; it does not make the arm unable to fail, KO a target, or change behaviour with the flags unset. The proposed fix is sound: the DMGAUDIT BEFORE line already logs the raw gBattleMons structs (`mons=`, 0x58 each; dmgaudit.py:59,79), and level sits at offset 0x2A. So the expected Δbide[1] can be decoded from the arm's own BEFORE line (rule 4).

A separate defect I found but did not file: the fixture's Mudkip holds four moves (Tackle, Growl, Mud-slap, Water Gun; all_fixtures.txt:764), so D8's "in an EMPTY slot, so no existing move is lost" is false as written.
V-EVIDENCE: Design:
- DESIGN.md:133 "LEVEL_DAMAGE = our level".
- DESIGN.md:165-166 "Mudkip (L13) Seismic Toss ... That is 13 fixed damage".
- DESIGN.md:207 W-EXEC pass "DMGAUDIT's BEFORE shows Seismic Toss, Δbide = 13".
- DESIGN.md:167 and :199: only the turn (the discriminator) is derived per trajectory, not the value.

Decomp:
- battle_scripts_1.s:1195-1204 (BattleScript_EffectLevelDamage runs `dmgtolevel` at :1202).
- battle_script_commands.c:7926-7930 `Cmd_dmgtolevel`: `gBattleMoveDamage = gBattleMons[gBattlerAttacker].level;` (the live battle level).
- battle_script_commands.c:1912 `gBideDmg[gActiveBattler] += gBattleMoveDamage;`.

Fixture: scratchpad/w12/all_fixtures.txt:764 "0 Mudkip #550A9BE6 L13 ... Tackle, Growl, Mud-slap, Water Gun" (four moves, no empty slot).

Recorded trajectory, tools/story-dev/evidence/2026-09-28-r20P2a-ON-240k-window.txt:
- :7-8: the first battle is Won and Mudkip is already L14.
- :24: 'Mudkip:L15' at f154902.
- :27-29: the first in-scope battle is Taillow (kind=team) at f159430, led by Mudkip at 44/44 (the L15 max HP).

Our code for the fix: sandbox-pokebot/modules/dmgaudit.py:59 reads gBattleMons (size 0xB0) and :79 emits `mons=` as two 0x58-byte hex structs. Level is at 0x2A, so the expected value can be decoded per run.

## proof:W12-LP5 [should-fix] 2026-09-30-weaken12-DESIGN.md:167, :204-208 (the ARMS table)
CLAIM: The KI-112 rules are applied only to W-OFF, but the lever changes the trajectory, so W-OFF is not the control for W-EXEC. Three gaps:
(a) W-EXEC has a single OFF run.
(b) Its Step-0 discriminator would come from one run.
(c) There is no rule for what happens when the two OFF runs, or an OBS run, diverge.
EVIDENCE: - Why the lever changes the trajectory: Growl→Seismic Toss adds a damaging move the fight strategy uses once Water Gun's 7 PP are gone.
- The KI-112 rules:
  - 'One control run is not a control' (05-KNOWN-ISSUES.md:3150);
  - 'graded A/Bs run the control at least TWICE' (:3163);
  - a per-turn table from ONE run can lose its tail; 'take such a table from two identical runs SEPARATED IN TIME' (:3185).
- Step 11 pre-registered the rule this table lacks: 'the two OFF runs must match each other first (else a third) … a lone divergent run is re-run, never graded' (2026-09-30-dmgcalc11-DESIGN.md:226-229).
- Runs separated in time are the ones KI-112's second event diverged in (05:3180-3184).
FIX: Add EXEC-OFF ×2: the lever, flags unset, DMGAUDIT=1, separated in time. These are the Step-0 reads, and the discriminator comes from both. Then:
- EXEC-ON must equal a reproducing EXEC-OFF on every line up to the discriminator turn.
- Copy step 11's decision rule verbatim for W-OFF, W-OBS and EXEC.
- Do the same for the DR arms in W12-LP1.
VERDICT: refuted=False corrected=should-fix
REASONING: I could not refute any of the three gaps. The design applies the KI-112 rules to W-OFF only. Its W-EXEC arm, which runs on a different trajectory, has one OFF run, a discriminator from an unspecified number of Step-0 reads, and no rule for what happens when runs diverge.

Why W-OFF cannot stand in as the control for W-EXEC:
- The design says so itself. D8 (:167) computes the discriminator "on the arm's own trajectory".
- The lever cannot go into an EMPTY slot as D8:165 claims. The fixture's lead Mudkip has four moves (Tackle, Growl, Mud-Slap, Water Gun 7/25; w12_recon_fixture.md:18), so the lever must overwrite one.
- Wherever Seismic Toss lands, it joins the list that `get_strongest_move_against` scores (sandbox-pokebot/modules/battle_strategies/_util.py:244-268). That list is scored by `calculate_move_damage_range`, which returns a fixed DamageRange(level) = 13 for Seismic Toss (_util.py:224-225). The ordinary fight path (default.py:219-233) can therefore pick it in battles that are not catches. That changes battle lengths and the frames after them.
- So W-EXEC OFF is the only control for W-EXEC ON, and the table (:207) says "ON/OFF" with no ×2. Compare :204 "W-OFF ×2 … SEPARATED IN TIME".

(a) holds: one control run. This breaks KI-112's standing rules:
- "One control run is not a control" (05:3150).
- "graded A/Bs run the control at least TWICE" (05:3163).
- Playbook 14:123-126, "A CONTROL IS A CLASS OF RUNS".

(b) holds: :167 says the discriminator comes "at the Step-0 reads" and never says how many runs. KI-112's second event is exactly this case. Step 11's single Step-0 probe was the run that diverged (05:3176-3185), and its per-turn table lost its tail. The rule written afterwards is "take such a table from two identical runs SEPARATED IN TIME" (05:3185; playbook 14:572).

(c) holds:
- W-OFF's pass (:204) is only "they match on every frame-stamped line". There is no "else a third".
- W-OBS (:205) says "a reproducing OFF" but does not say what happens when the OFF runs disagree, or when a lone OBS run diverges.
- W-EXEC requires no ON = OFF prefix up to the discriminator turn.
- Step 11 pre-registered all of this verbatim (dmgcalc11-DESIGN.md:227-229).

What limits the severity to should-fix, not blocker:
- The table is headed "to pre-register after the Step-0 reads" (:199).
- The playbook's standing rules (14:123-126, :572) would push a careful pre-registrer to double the control anyway.
- The failure this invites is a spurious FAIL / NOT-REACHED, or a grading rule improvised after the fact. It does not cause a KO, a behaviour change with flags unset, or an arm that cannot fail.
- One softer point: the finding says the fight strategy picks Seismic Toss "once Water Gun's 7 PP are gone". That is inferred, not measured, but the premise does not depend on it, because D8:167 already concedes the trajectory differs.
V-EVIDENCE: - Design, 2026-09-30-weaken12-DESIGN.md:
  - :204 "W-OFF ×2 | … the two runs SEPARATED IN TIME | they match on every frame-stamped line" (no else-a-third rule).
  - :205 W-OBS "= a reproducing OFF" (no rule for OFF-vs-OFF or a lone OBS divergence).
  - :207 "W-EXEC ON/OFF | the lever (D8) + WEAKEN=1 vs unset" (one OFF; no ON=OFF prefix check).
  - :167 "discriminator is computed at the Step-0 reads, on the arm's own trajectory" (run count unstated; concedes the trajectory differs from W-OFF).
  - :165 "Seismic Toss in an EMPTY slot".
- Fixture: w12_recon_fixture.md:18, Mudkip L13 "Tackle 31/35, Growl 40/40, Mud-Slap 10/10, Water Gun 7/25". There is no empty slot, so the lever must overwrite a move.
- Move choice: sandbox-pokebot/modules/battle_strategies/_util.py:244-268, `get_strongest_move_against` picks the max of `calculate_move_damage_range(...).max`; _util.py:224-225 returns DamageRange(attacker.level) for Seismic Toss; default.py:219-233 makes it the ordinary fight choice.
- KI-112:
  - 05-KNOWN-ISSUES.md:3150 "One control run is not a control".
  - :3163 "graded A/Bs run the control at least TWICE".
  - :3179 the second event was on an overworld walk.
  - :3185 "Take such a table from two identical runs SEPARATED IN TIME".
- Step 11's pre-registered rule, 2026-09-30-dmgcalc11-DESIGN.md:227-229: "the two OFF runs must match each other first (else a third) … a lone divergent run is re-run, never graded"; arms table :261-262 "M1b-OFF ×2", "M1b-ON ×2".
- Playbook:
  - 14-AGENT-PLAYBOOK.md:123-126 "A CONTROL IS A CLASS OF RUNS, NOT A RUN … Run the control at least TWICE" (a standing rule, so this is not a blocker).
  - :572 "take a live per-turn table from TWO identical runs SEPARATED IN TIME".

## proof:W12-LP6 [should-fix] 2026-09-30-weaken12-DESIGN.md:205 (W-OBS 'every OBS line replays to the same verdict'), D5 :151-153
CLAIM: The replay check cannot fail on a wrong read. It feeds the adapter's own logged snapshot back into the same deterministic pure function, so it tests only that serialization round-trips. On this fixture, W-OBS also only ever sees THROW verdicts: the party has no stage-1 move and Abra is an ender. So the DAMAGE/STATUS branches and `first=1` never replay live.
EVIDENCE: - The party has no stage-1 move, so OFF and ON choose the same action on every turn (w12_recon_fixture.md:24-26; all_fixtures.txt:764-767).
- A wrong raw read would still replay identically, because the snapshot IS the read. The design names two such reads:
  - the Encore move at disable offset 0x04 vs 0x06 (battle_state.py:729-730 vs include/battle.h:73-74);
  - the species ability vs the live `ability_n` (BS:566-575).
- An independent reader already logs the same turn's raw bytes. `[DMGAUDIT] BEFORE` carries `mons=` (gBattleMons 0x58 ×2), `dis=` (gDisableStructs 0x1C ×2), `s3=`, `side=`, `weather=` and `flags=` (dmgaudit.py:56-81). It is written at the selection exit, before any action runs, so the fields are the ones the adapter saw.
FIX: (1) Make the check a correctness test: decode every WEAKEN snapshot field from the same turn's BEFORE hex (hp 0x28, maxHP 0x2C, level 0x2A, status1/2, the live ability byte 0x20, moves/PP 0x0C-0x13/0x24-0x27, item 0x2E, encoredMove 0x06 and its timer, Taunt, Disable), and require equality.
(2) Add W-OBS-LEVER (the lever + WEAKEN=observe). It must equal a reproducing EXEC-OFF on every non-WEAKEN line, and it must show `would=DAMAGE first=1` at the discriminator turn, so a non-THROW verdict is replayed and cross-checked before the acting arm runs.
VERDICT: refuted=True corrected=nit
REASONING: One part of the finding is true: a replay of a logged snapshot cannot detect a wrong raw read, because the snapshot is the read. But the rest is overstated, and its fix does not work on this fixture.

(1) The design never presents the replay as a read-correctness check. D5 (:151-152) says each OBS line carries its snapshot "so the pure module can replay it". That is a check that the log is sufficient for an offline re-grade, and that the adapter adds no logic outside the pure module. It can fail: for example, if a field the verdict depends on is not logged, or if adapter state such as the per-battle caps (:109-110) or the `first=` marking is left out of the snapshot. It is not vacuous.

(2) Proposed fix (1) cannot catch either of the two wrong reads the finding names, on this fixture.
- The Encore read: disabledMove (0x04) and encoredMove (0x06) are both 0 unless Disable or Encore has been used. No Route 116 wild at L6-8 knows Disable, Encore, Taunt, Torment or Imprison. Our lead Mudkip knows none of them either. So reading 0x04 or 0x06 gives the same value, and the proposed equality check passes either way.
- The ability read: `.ability` (BS:564-568) already picks the species ability by the mon's ability bit (0x17 bit 7). It differs from the live byte 0x20 (BS:570-572) only after Trace, Role Play or Skill Swap. Nothing on this fixture has those.
- So the proposed check has the same blindness the finding charges the replay with. A bad offset like this is caught by a gate row built from crafted bytes, not by a live arm on a fixture where the field is always 0.

(3) "DAMAGE and first=1 never replay live" is overstated.
- W-OBSCALC's pass is "as W-OBS" (:206), so the replay also covers its stage-2 `would=` verdicts, and the first non-THROW verdict is marked `first=1` (:152-153). v2:660 itself predicts "Skitty `would=damage Mud-Slap`" under CALC. Mud-Slap is ACCURACY_DOWN_HIT, which is in Tier A (audit_damage_calc.py:135). Whether a Skitty (2%) is met depends on the trajectory.
- The stage-1 DAMAGE branch is exercised live by W-EXEC ON (:207). There the design pairs each `[WEAKEN] act=` with the next `[DMGAUDIT] BEFORE` by frame (:159). It requires that the game's own chosen move is Seismic Toss, Δbide = 13 and no KO. That is an independent reader checking the ACTION, which is a stronger test than any replay.
- The design already states that stage 1 cannot act on this fixture (:7-16). v2:661 records that the observe run is only the proof that `observe` is inert.

(4) Proposed fix (2), the W-OBS-LEVER arm, adds one more replay. By the finding's own premise, that replay cannot catch a wrong read. Its turn is also already covered by W-EXEC ON on the same trajectory.

What remains is a nit. The design could say in one line that the replay checks that the snapshot is complete, not that the reads are correct. It could also optionally cross-check the fields that actually vary on this fixture (hp, maxHP, level, status1/2, PP) against the BEFORE `mons=` hex. That is hygiene, not a defect with a bounded effect.
V-EVIDENCE: - pret include/battle.h:70-78: `u32 transformedMonPersonality; u16 disabledMove; u16 encoredMove;` puts disabledMove at 0x04 and encoredMove at 0x06. Both are 0 unless Disable or Encore is used.
- pret src/data/wild_encounters.json, gRoute116: Poochyena 6-8, Whismur 6, Nincada 6-7, Abra 7, Taillow 6-8, Skitty 7-8.
- pret src/data/pokemon/level_up_learnsets.h, early moves:
  - Taillow: Peck, Growl, Focus Energy (4), Quick Attack (8)
  - Skitty: Growl, Tackle, Tail Whip (3), Attract (7)
  - Abra: Teleport
  - Poochyena: Tackle, Howl, Sand-Attack
  - Nincada: Scratch, Harden, Leech Life, Sand-Attack
  - Whismur: Pound, Uproar
  - So there is no Disable, Encore, Taunt, Torment, Imprison, Trace, Role Play or Skill Swap.
- Lead party: w12_recon_fixture.md:18, Mudkip with Tackle, Growl, Mud-Slap and Water Gun.
- sandbox-pokebot/modules/battle_state.py:564-572: `ability` selects species.abilities[1] when `_data[0x17] & 0x80`, and `ability_n` is `_data[0x20]`. They differ only if the live byte changed.
- The design:
  - D5 :151-153 ("so the pure module can replay it"; `first=1` on the first non-THROW verdict);
  - W-OBSCALC :206 ("as W-OBS");
  - W-EXEC :207 (DMGAUDIT BEFORE shows Seismic Toss, Δbide = 13, no KO);
  - D6 :156-159 (the grade pairs `[WEAKEN] act=` with the next `[DMGAUDIT] BEFORE` by frame);
  - headline :7-16.
- v2 2026-09-29-r23-27-DESIGN-v2.md:660 ("Skitty `would=damage Mud-Slap`, the last under CALC only") and :661 (the observe run as the live proof that `observe` is inert).
- tools/story-dev/audit_damage_calc.py:131-137: TIER_A contains ACCURACY_DOWN_HIT and HIT.
- sandbox-pokebot/modules/dmgaudit.py:154-167: BEFORE is logged once the game has left the selection states.

## proof:W12-LP7 [should-fix] 2026-09-30-weaken12-DESIGN.md:204-205 (W-OFF, W-OBS); tools/story-dev/run_with_base_modules.py:28-30
CLAIM: Every live arm compares the build with the build. Nothing compares 'flags unset' against the BASE code, so 'no behaviour change with every flag unset' rests on reading the code. And the tool playbook §3e requires for attributing a divergence cannot load the base copy of the file step 12 changes.
EVIDENCE: - The file step 12 changes: D1 (the flag reads), D5 (the adapter) and D7 (the docstrings) all edit sandbox-pokebot/plugins/custom_modes/story_mode.py, which is imported as `plugins.custom_modes.story_mode` (story_harness.py:199).
- The runner cannot load it: `_module_name` asserts `parts[1] == "modules"` (run_with_base_modules.py:30), so passing story_mode.py aborts.
- Why it will be needed: step 11 needed BASE ×2 to attribute a KI-112 event (05:3170-3183).
FIX: Extend run_with_base_modules.py to register `plugins.custom_modes.*` modules (it asserts no added module was imported; weaken_catch.py is added under modules/, which is fine). Then add BASE ×2 (flags unset, base story_mode.py) against W-OFF ×2 under step 11's decision rule. If the design keeps build-vs-build, state why in 06.
VERDICT: refuted=False corrected=should-fix
REASONING: The finding stands. I checked every part of it against the design, our code and step 11's record.

1. **No base comparison anywhere.** The arms table (DESIGN:201-209) has G-W, W-OFF ×2, W-OBS, W-OBSCALC, W-EXEC ON/OFF and W-FAULT. Every live arm runs the build:
   - W-OFF passes when "they match on every frame-stamped line" (:204), which is build against build.
   - W-OBS passes when it equals "a reproducing OFF" (:205), again the build.
   - W-EXEC compares WEAKEN=1 with unset, both on the build.
   - Nothing compares a run with the flags unset against the Step-0 base run or any other base run. A grep of the design for "base", "inert" and "unset" finds no such check.

2. **The gate's pins do not cover it either.** D11's AST pins (:182-186) cover four things: no `get_battle_state`, the adapter's position, shiny not reaching it, and the construction lines. The only flag-unset property the design names is "NO line contains WEAKEN" (D6 :154). None of this shows that behaviour with the flags unset equals the base.
   - D5's "[WEAKEN] ERR line (flag on only)" (:149) implies the adapter body may run with the flag off. Nothing pins zero reads with the flag unset.

3. **This drops a check step 11 filed in advance and passed.** Step 11 had an offline base-vs-new arm, M1b-DIFF (dmgcalc11-DESIGN.md:264: the old module from `git show 241929d7:` against the new, flag unset, "identical yields and lines"). It passed: "the new modules equal the base as ASTs once the hooks are removed; with the flag unset, zero reads and zero logs" (:345-348). Step 12 has no equivalent row.

4. **The tool gap is real.**
   - `run_with_base_modules.py:30` asserts `parts[1] == "modules"`.
   - Step 12's production change is in `sandbox-pokebot/plugins/custom_modes/story_mode.py`: the adapter at SM:85-93 and the flag reads in `reset_per_run_state` at SM:2249.
   - The harness imports that file as `plugins.custom_modes.story_mode` (story_harness.py:199, :1114 and others).
   - So the tool that playbook §3e (14-AGENT-PLAYBOOK.md:557-567) names for attribution aborts on the one file step 12 changes.
   - Step 11 did need that attribution. Its BASE ×2 (05:3169-3183; dmgcalc11-PREDICTIONS.md:131-149) was needed because a live run left the predicted trajectory.

**What limits the severity:**
- §3e applies only when a live run leaves the predicted trajectory, so the tool gap blocks attribution only if that happens.
- A cheaper, more direct fix than live BASE ×2 is an offline DIFF row like step 11's M1b-DIFF: base `story_mode.py` against the new one, flags unset, the real classes, identical actions and zero reads and logs.

This is not a demonstrated behaviour change with the flags unset, so it is not a blocker. It is a missing proof of a property the design depends on, plus a latent gap in the attribution tool, so should-fix holds.
V-EVIDENCE: **The design**
- 2026-09-30-weaken12-DESIGN.md:204: W-OFF ×2 passes when "they match on every frame-stamped line; 0 lines contain `WEAKEN`" (build against build).
- :205: W-OBS passes when it is "= a reproducing OFF on every line without `WEAKEN`" (the build's OFF).
- :207: W-EXEC ON/OFF are both the build.
- :182-186: the AST pins cover no `get_battle_state`, the adapter after the flee and before `super()`, shiny not reaching it, and the construction lines unchanged. None of them is base against build.
- :149: "[WEAKEN] ERR line (flag on only)".
- A grep of the design for base/inert/unset finds no base comparison.

**The step 11 precedent step 12 drops**
- dmgcalc11-DESIGN.md:264: "M1b-DIFF | the old BAS module (`git show 241929d7:`) vs the new, flag unset ... | identical yields and lines".
- :345-348: it passed, with "the new modules equal the base as ASTs once the hooks are removed; with the flag unset, zero reads and zero logs".

**The tool**
- run_with_base_modules.py:30: `assert parts[0] == "sandbox-pokebot" and parts[1] == "modules", f"not a sandbox-pokebot module: {rel}"`.
- Step 12 changes sandbox-pokebot/plugins/custom_modes/story_mode.py: the adapter site at :85-93 and `reset_per_run_state` at :2249.
- The harness imports it as `plugins.custom_modes.story_mode` (story_harness.py:199, :1114, :1181).

**Why attribution may be needed**
- Playbook §3e (14-AGENT-PLAYBOOK.md:557-567) requires a BASE run with this tool when a live run leaves the predicted trajectory.
- Step 11 needed it: 05-KNOWN-ISSUES.md:3169-3183 (BASE ×2, the second KI-112 event) and dmgcalc11-PREDICTIONS.md:131-149 (the ADDENDUM A/B).

## proof:W12-LP8 [nit] 2026-09-30-weaken12-DESIGN.md:205 (W-OBS 'none in shiny/hm/counter/trainer battles')
CLAIM: On this fixture the exclusion clauses test almost nothing. HM and counter catches happen only when their hunt is armed, a shiny is 1/8192, and before badge 1 every catch is kind=team, so the dex path is never exercised live.
EVIDENCE: - The HM branch needs `_eg.HM_CATCH_TARGET_DEX` to be non-empty (SM:4109). It is set only when an HM hunt is armed (early_game.py:5214 / :5232).
- The counter branch needs `_chunt.COUNTER_CATCH_TARGET_DEX` (SM:4138-4139).
- `_post_badge` is False before badge 1, so StoryCatchStrategy is used, with kind 'team' (SM:4002-4015).
- The recorded runs on this fixture show only team catches (r20P2a-ON-240k-window.txt:29, and the CATCHTEAM exit at :78).
FIX: In the live grade, print the count of battles of each excluded kind the run reached, and declare a clause vacuous when its count is 0. Put the actual proof in G-W:
- adapter rows on the REAL StoryCatchStrategy with ctx kind=hm or counter must give no OBS line and the parent's sentinel;
- StoryShinyCatchStrategy with WEAKEN=1 must return the stubbed CatchStrategy sentinel and log no WEAKEN line.
VERDICT: (none: a nit, not sent to a refuter)

## proof:W12-LP9 [nit] 2026-09-30-weaken12-DESIGN.md:159-160 (D6: pair each `[WEAKEN] act=` with the next BEFORE by frame; the primary safety readout)
CLAIM: Pairing by 'the next BEFORE by frame' can silently mis-pair. An act= whose turn has no BEFORE is paired with the NEXT turn's (or the next battle's) BEFORE, and a re-entered selection gives two act= lines for one BEFORE. Separately, the KO readout depends only on the `[CATCH] end` writer.
EVIDENCE: - Where the BEFORE is written: only on the selection loop's fall-through (battle_action_selection.py:1009-1012).
- Early returns skip it: the KI-46 recovery (:177-196) and KI-96 (:888-889).
- Re-entry: decide_turn runs inside that loop (:198-205), and the selection is re-entered within one turn (dmgaudit.py:25-27).
- The turn is available on both sides: DMGAUDIT logs `t=` (dmgaudit.py:69).
FIX: Put the raw `t=` on every `[WEAKEN] act=` line, and pair on (the battle delimited by its CTL line, t). Require exactly one BEFORE per pair, and grade an orphan as UNGRADED, never paired onward.
- Also add a second, independent KO signal to the safety readout: no `AFTER kind=end` with the foe's HP at 0 in a team or dex `[CATCH]` battle.
VERDICT: (none: a nit, not sent to a refuter)

## proof:W12-LP10 [nit] 2026-09-30-weaken12-DESIGN.md:109-110 (caps 'keyed on battle_state.current_turn')
CLAIM: The caps are keyed on exactly the field KI-108 says can be stale. The handler binds its BattleState once per selection and reuses it, and a non-first cached get_battle_state() in a frame can return an old object with an old turn.
EVIDENCE: - `BattleState.__eq__` omits `_current_turn` (battle_state.py:249-261), and the cache keeps the old object when equal (state_cache.py:294-298; 05-KNOWN-ISSUES.md:3066-3075).
- The handler binds it once at battle_action_selection.py:116.
- DMGAUDIT avoids the problem by reading gBattleResults+0x13 raw (dmgaudit.py:69).
FIX: Key the caps on a raw read of gBattleResults+0x13 (the module already reads 0x06 raw for Encore). Also add a G-W row where the state object's turn is stale but the raw turn has moved on.
VERDICT: (none: a nit, not sent to a refuter)

## proof:W12-LP11 [nit] 2026-09-30-weaken12-DESIGN.md:183-184, :190-193 (D11 AST pin; D12 catch rows)
CLAIM: Two planned G-W checks cannot fail on the defects they are meant to catch:
(a) At full HP, the agreement between catch_p and dex_catch_expected_throws cannot see an HP-term bug.
(b) The AST pin 'no get_battle_state in the adapter' cannot see a call made from a helper or snapshot builder.
EVIDENCE: (a) At full HP both sides reduce to rate·bonus/10 // 3, and dex_catch_expected_throws hard-codes `//3` (SM:1782). So, for example, a denominator using hp instead of maxHP is identical at hp = M.
(b) The pin inspects only the adapter body, and the snapshot reads live in weaken_catch.py or other helpers.
FIX: (a) Add hand-derived rows below full HP, for example:
- Taillow M=22, hp=9: odds 145, b=58253, p=0.6242;
- Skitty M=25, hp=12: odds 173, p=0.7846;
- odds > 254: p = 1.0.
(b) Add a runtime row that monkeypatches every bound `get_battle_state` to raise and runs the adapter's DAMAGE row. Any call then turns it into DEFER plus ERR, and the row goes red.
VERDICT: (none: a nit, not sent to a refuter)

### checked and found true
- Existing gates will NOT go red under D5 (the adapter inserted between SM:92 and :93) or D7 (the docstring rewording):
- No gate pins the body of StoryCatchStrategy.decide_turn, and none pins the 'never fights back / never damages' text. A grep of tools/story-dev finds those phrases only in the docstrings at probe_dexcatch_bail.py:4 and probe_dex_open_fence.py:8.
- probe_dexcatch_bail.py:112-115/:185-188 and probe_dex_catch_nofaintbail.py:104-106 stub SM.StoryCatchStrategy.decide_turn wholesale, so they bypass the adapter.
- The nofaintbail text anchors (:287-288) sit on StoryDexCatchStrategy's 'import os as _os_bail'.
- D2 leaves the construction strings pinned at probe_dexcatch_bail.py:78-87 and the _r20_catch_start adjacency (probe_r20_telemetry.py:285) untouched.
- Corollary: those stubs mean the new G-W adapter rows must stub CatchStrategy.decide_turn, get_item_bag and the raw reader, NOT StoryCatchStrategy.decide_turn, or they cannot see the adapter.
- A checksummed party write made in the overworld before a battle reaches gBattleMons:
- REQUEST_ALL_BATTLE (src/battle_main.c:3363);
- GetMonData of MOVE1+i and PP1+i (src/battle_controller_player.c:1619-1625), with the checksum validated at src/pokemon.c:3742-3746;
- the copy into gBattleMons at src/battle_main.c:3414-3416.
- Seismic Toss is not type-immune against any Route 116 target: Fighting is neutral on Taillow (Normal/Flying), super-effective on Skitty and not very effective on Abra (Psychic). Abra is THROW-ONLY anyway: it knows only Teleport (species.json learnset {100: 1}).
- The parent throws a Poké Ball on this fixture: catch.py:212-239 never chooses the Master Ball, and exp_throws=3.6 = 1/0.2797 for Taillow and 3.0 = 1/0.337 for Skitty in the recorded run. Both one-throw chances (0.280 and 0.337) are below 0.5, so neither target is THROW-ONLY by the 0.5 rule.
- On the recorded (unlevered) trajectory, a team catch against an unowned species does happen with Mudkip leading: Taillow L6 at f159430, with Mudkip L15 at 44/44 in slot 0 (r20P2a-ON-240k-window.txt:27-29). With TEAM6 on a 4-mon party, CATCHTEAM exits after two catches (:78), so there are about 2-3 in-scope battles per run. The run's seed was not recorded.
- Wherever the lever writes Seismic Toss, the story move-learn policy keeps it through L15 (Bide) and L16 (Mud Shot). Bide either takes a status slot or is declined as redundant Normal (SM:666-703). Mud Shot upgrades Mud-slap.
- DMGAUDIT writes a BEFORE on every turn, ball throws included (pred=none when act ≠ 0; dmgaudit.py:103-106, :154-168). So 'OFF throws there' is observable as act[0]=1.
- gBideDmg[battler] accumulates the uncapped gBattleMoveDamage (src/battle_script_commands.c:1912), so a KO turn still shows the full fixed damage in Δbide.
- The design's claim that no constructor takes weaken= and that shiny bypasses the adapter holds: StoryShinyCatchStrategy.decide_turn calls CatchStrategy.decide_turn(self, …) directly (SM:275).