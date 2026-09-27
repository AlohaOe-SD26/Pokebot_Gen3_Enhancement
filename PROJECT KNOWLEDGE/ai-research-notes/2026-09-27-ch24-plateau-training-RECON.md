# 2026-09-27 — §Ch24 R1 shape A: training cannot leave the plateau (5 of 6 §Ch24 runs of #27-batch0927) — a NOTE

> ⛔ **A NOTE, NOT A SOURCE OF TRUTH.** A read-only Claude agent (recon), then a second agent told to REFUTE each
> key claim against the logs, the code and the decomp. The batch was still running; counts are at ~4:00 PM.

## Recon

SHAPE A: §Ch24 training cannot leave the plateau. This is a NOTE, not truth. Nothing was edited, started or stopped.

**MEASURED (batch logs, build d21c0c3c)**

Six runs reached §Ch24. In the five no-Fly runs, every attempt was the same: all five derails ran `train_for_league` twice, and the log shows zero rungs trained (no "L→L at" line anywhere in those runs).

| run | party at §Ch24 entry | Fly | why each trainee stopped |
|---|---|---|---|
| P1 r4 | Zigzagoon L10; Mightyena, Beautifly, Breloom, Azumarill L47; Blaziken L62 | none | Zigzagoon: "no reachable ground". The other five: the picker chose VICTORY_ROAD_1F (15,39), and the plateau guard refused it. |
| P2 r1 | Castform L26; Ninjask, Mightyena, Beautifly, Shedinja L47; one member already at the floor | none | Same pattern. |
| P2 r3 | Castform L27; Mightyena, Skitty, Exploud L47; one at the floor | none | Same pattern. |
| P3 r5 | Zigzagoon L13; Beautifly, Mightyena, Azumarill L47; Exploud L48; Sceptile L61 | none | Same pattern. |
| P4 r3 | Linoone L36, Castform L37 (no ground); Exploud, Mightyena, Azumarill L47; Blaziken L62 | none | Same pattern. |

- No party held a Fly-compatible species. Checked against HM02 in `modules/data/species.json`: only Wingull, Pelipper, Taillow, Swellow, Swablu and Tropius can learn Fly.
- Box contents:
  - P1 r4, P2 r1 and P4 r3 each caught a Wingull into the PC box (`outcome=Caught`, party matches the run).
  - P3 r5's two Wingull attempts ended Won and RanAway, so no Wingull.
  - P2 r3's log shows no flyer catch.
- **The one run with Fly (P4 r2, the control):**
  - It taught Fly to Swellow. The picker chose ROUTE121 for Castform, then VR1F (15,39), healing at the south Ever Grande Poké Center.
  - Every member reached L65. §Ch24 training ran from frame 5.52M to 8.87M, about 3.35M frames.
  - Cost per trainee on that one run: Blaziken L47→65 about 0.54M frames, Lombre 47→65 about 0.61M, Beautifly 48→65 about 0.72M, Castform 37→65 about 1.47M.
  - It was then refused because the League basket was short: Hyper Potion 26/30, Full Restore 1/3, Revive 2/3. Four Hyper Potions were used in battle during training.
- **Side finding:** P2 r1's Ninjask and Shedinja share PID ADCAB5A0 (the Shedinja/Ninjask split; the game gives both the same PID). `_ch24_slot_of` and `_ch24_level_of` look mons up by PID only (`pokemon_league.py:1699-1727`), so they would mix the two up. That is an INFERRED bug.

**(1) Training grounds for L47→65 from the plateau without Fly**

- **Code:**
  - `TRAINING_GRASS` tops out at VR1F (15,39), wilds 36-40 (`training_areas.py:117`). Every route is L28 or lower (`:25-47`), and B1F/B2F sit in the pending list with no tile (`:181-182`).
  - The ladder offers only grounds the trainee out-levels (`max_wild_max=level+1`, `pokemon_league.py:1888`), so VR1F opens at L39. That is why the L10-37 stragglers get no ground.
  - The plateau guard `_plateau_walkoff_refused` (`:1797-1802`, call site `:1926-1935`) refuses VR1F for all the L39+ trainees.
- **Decomp wild levels:** 1F 36-40; B1F 38-42 (plus Rock Smash 30-40); B2F 40-44.
- **Decomp geography:**
  - The only Victory Road door on the plateau is Ever Grande (18,27), which leads into 1F at (39,5).
  - I decoded `map.bin` and the tile attributes offline and flood-filled from (39,5). As a check, the same decode reproduces the measured result that (15,39) is unreachable from (39,5), and it finds the entrance-half ladder at (9,14).
  - From (39,5), the exit half is 188 tiles, 178 of them `MB_CAVE` encounter tiles. They roll the same 36-40 table.
  - Its only other exit is the ladder at (21,32) to B1F (20,21). That is a 9-tile pocket (8 cave tiles, B1F table 38-42), sealed by Rock Smash rocks and Strength boulders at (20-21, 25-26).
  - Reaching B2F from the plateau would mean doing the boulder puzzle in reverse, so I infer it is not practical.
- **Heal:** the VR1F heal anchor is the Ever Grande Poké Center (`story_mode.py:1605`), on the south half. The plateau has no walking path to it (`victory_road.py:361-363`). The only plateau heal is the League nurse (`:392`, `heal_at_league` `:3279`). She is not a `PokemonCenter`, so `train_team` cannot use her as-is.

**(2) Design history**

- **Gap 4 (2026-09-26):**
  - The crash was measured first: `UnreachableDestinationError (15,39)… still at (39,5)`.
  - The first guard used a warp-blind `calculate_path`, and review rejected it.
  - It was narrowed to "no Fly + on the plateau + a VICTORY_ROAD ground", with fault arm `NOWALKCHECK`. Both arms were graded (`2026-09-26-ch24-walkoff-GRADED.md:11-14`).
  - The same note, under "WHAT IT DOES NOT SETTLE" (`:30`), says such a party "still cannot train at all — gap 5, or a grind tile in VR1F's EXIT half (not built: needs a live tile dump)". **This batch measures exactly that prediction, in 5 of 6 runs.**
- **Gap 5:**
  - The recon options were O1 (withdraw a boxed flyer at the lobby PC), O2 (a detour to catch one) and O3 (a dex exemption for flyers).
  - USER RULING 20 set aside O2 and O3: the flyer must come from organic catching, with no chapter-specific fixes (`06:7431-7444`). RULING 21 allows a brief fighter↔carrier swap (`06:7446`).
  - The exit-half tile question ("U3") was put to the user and never answered (flyer recon `:57`).
  - Box-first Fly is built on `wt/r20fly` (553082e2, `ensure_fly_learner` `:2408-2457`). It is not in the batch build.

**(3) Candidate fixes, smallest first, each with its risk**

- **B. Train higher in §Ch23, before the plateau.**
  - `TRAIN_TARGET=47` (`victory_road.py:493`) was chosen to fit the old 250k per-call ceiling. RULING 14's chunked training replaced that ceiling, and the target's own comment expected the remaining gap to be closed after Wally, which never happens.
  - Raising the pre-Wally target (`:3870`, `:3908`) uses the loop that already works: entrance half plus the south Poké Center. It needs no Fly, and the basket is bought afterwards (leg 11), so training cannot eat it.
  - By arithmetic (INFERRED), a working rung would give all five refused runs the four members at L65 that RULING 15 requires.
  - Risks:
    - Frames. It costs about 0.5-0.7M per fighter (one trajectory, replayed only), so about 2.4-3.6M more. The 6M `CH23_TRAIN_PURSE_FRAMES`, the allowance and the 7M cap would need re-sizing.
    - `BENCH_SPECIES` are skipped (`:504`).
    - It changes a shared path, so it needs an A/B on an ordinary §Ch23 run.
- **C. Fly through box-first (already built).**
  - It could cover P1 r4, P2 r1 and P4 r3, but it is unverified whether each Wingull was still boxed at §Ch24 and passes `_fly_teach_plan`.
  - Risks:
    - P2 r3 and P3 r5 own no flyer; for them this waits on RULING 20 Phase 2.
    - Training after leg 11 drains the basket, which is exactly what failed P4 r2. It needs a re-buy at the League mart.
- **A. A grind tile in the exit half, healed by the League nurse.**
  - Risks:
    - It is plausibly chapter-specific, and U3 is unruled.
    - It needs a live encounter probe on a tile such as (38,5).
    - `train_team` needs a hook to heal at the nurse.
    - `_ch24_step_out_if_fly_illegal` heads for the south Poké Center apron (`pokemon_league.py:1789-1790`), which the plateau cannot reach.
    - Katelynn and Quincy may still be unbeaten (leg 9 routed around them) and could spot the bot in the exit half.
    - Every heal cycle has to use the (18,27) return trap on purpose.
    - Basket drain, as in C.

**Open, not checked:** P4 r2's refusal says `ENTERED_ELITE_FOUR is still True`, but that flag is supposed to be False until the guards are talked to (step 1 of entry).

## Adversarial verification

This is a note, not the truth. I opened every cited source myself: 8 claims hold, 1 holds only after correcting a citation, and 3 are refuted.

**The biggest finding (claim 2, measured):** P4 run 2 did not stop at training. After all five members reached L65 (f8870401), the party walked into the Elite Four. It beat Sidney (map 16,0; Won at f8884881). It then lost to Phoebe (map 16,1; Lost at f8933909; whiteout recovery at f8934096). The 4 Hyper Potions were used against Phoebe, on Castform (f8903350-f8917091), not in training battles. R1's "basket short" refusal was the re-entry after the whiteout, and its message says ENTERED_ELITE_FOUR is still True. The Full Restore 1/3 and Revive 2/3 shortfalls had no logged uses, and no R1 or basket line appears before the first entry. So on the first pass, R1's basket gate apparently did not stop a short basket (inferred). The training numbers themselves are right:
- 3.35M frames in total.
- 0.54, 0.61 and 0.72M frames per fighter.
- Route 121 first, then VR1F (15,39), healing at the Ever Grande Pokémon Center.

**Claim 5 (inferred from my own offline decode of the decomp):** The numbers reproduce exactly: 188 tiles, 178 of them MB_CAVE, the (21,32) ladder, and a 9-tile pocket on B1F. But the pocket is "sealed" only for a walker that cannot use field moves. From (22,26), the rock at (21,26) can be smashed, and the boulder at (20,26) can then be pushed west onto the free tile (19,26). A search that models Rock Smash, Strength, Surf, ledges and waterfalls reaches 1F (15,39) by this route:
- pocket → B1F (17,16)
- → B2F
- → B1F (30,25)
- → ladder (8,3)
- → 1F (9,14) → (15,39)

The route climbs one waterfall, so it needs Waterfall, which these parties had. The measured crash was a walk within one map, so it cannot refute a route across floors. "(15,39) is not reachable" is true for the bot's current walker, not for the game. This needs a live probe before anything is built on it.

**Claim 3:** The parties really held no Fly learner. But species.json lists 38 species that learn move 19, not six. Altaria, Crobat, Skarmory, Vibrava, Flygon, Salamence and Xatu are all catchable in Hoenn before the League. The runs met some of them: P2 run 1 had 13 Skarmory and 29 Trapinch battles, and P3 run 5 caught a Zubat.

**Claim 4:** The P2 citation f4198369 is an Oddish catch. The Wingull was caught at f4194761 on Route 118 and went to the box. The substance of the claim holds.

**Confirmed as stated:**
- **1:** 5 of 6 runs had no Fly; everyone L47+ was refused, and the L10-37 stragglers had no ground. The L39 cutoff comes from the code, since no L38 or L39 trainee appeared.
- **6:** Wild levels 36-40, 38-42 and 40-44.
- **7:** The code lines match, and the batch build has the same code at lines 1792 and 1883.
- **8:** The heal anchor is the Ever Grande Pokémon Center, and the League nurse is not in the PokemonCenter enum.
- **9:** Right, but 47 is also the level Mightyena learns Crunch, which the claim leaves out.
- **10:** The guard was built on a measured crash, and the note says a no-Fly party still cannot train.
- **11:** Lines 7765-7785 exist only in wt/r20fly's copy of 06. Commit 553082e2 is not an ancestor of d21c0c3c, and no U3 ruling exists.
- **12:** The shared PID is measured. The conflation is inferred from the PID-only lookups at pokemon_league.py:1699-1727.

**Files:**
- P4 debug log: C:/Remote Projects/Pokebot_Gen3_Enhancement/sandbox-pokebot/profiles/endless-P4-random/debug-logs/P4-Story_(ENDLESS_RESET)-debug-20260927-085623.log (lines 29551-47202)
- Decode scripts: <session scratchpad>/decomp/ff.py, multi.py, push.py
- Branch code: C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/modules/story/pokemon_league.py

- **[CONFIRMED]** 1. Five of the six §Ch24 runs (P1 r4, P2 r1, P2 r3, P3 r5, P4 r3) had no Fly knower and trained zero rungs. Every trainee at L39 or above was refused at VR1F (15,39) by the plateau guard, and the L10-37 stragglers got 'no reachable ground'.  
  How: MEASURED. The ENDLESS RESET lines show six §Ch24 runs: P1 r4, P2 r1, P2 r3, P3 r5, P4 r2 and P4 r3. P4 r2 is the only one that taught Fly (P4-stdout:247770). Each cited block (P1:483853-483915, P2:260716-260771 and 614416-614462, P3:371959-372022, P4:609630-609689) prints 'nobody in the party can learn Fly'. Every refused trainee is L47-L62. The 'no reachable ground' trainees are L10, L13, L26, L27, L36 and L37. INFERRED: the L39 cutoff comes from the code (VR1F max 40 = level+1), because no L38 or L39 trainee appears in these runs.
- **[REFUTED]** 2. In P4 r2, Fly was taught to Swellow. All five members were trained to L65 on ROUTE121 and then VR1F (15,39), healing at the Ever Grande PC, in about 3.35M frames. L47->65 cost about 0.54-0.72M frames per fighter. R1 then refused because the basket was short after 4 Hyper Potions were used in training battles.  
  How: The training half is correct (MEASURED). In P4 debug 085623 the Castform rung ran on ROUTE 121 (f5526001-f5551201) and then on VR1F (15,39) with heals at map (16,12). Frame costs: Blaziken L47->65 f6991201->f7531201 = 0.540M; Lombre 0.605M; Beautifly L48->65 0.717M. All five reach L65 at f8870401. The final clause is WRONG. Only 4 item uses are logged in that file, and all 4 are Hyper Potions on Castform in Phoebe's room (map 16,1; lines 47019-47086, f8903350-f8917091). This came after the party walked into the Elite Four (f8870944 -> 16,0) and beat Sidney (Won f8884881). Phoebe's battle ended outcome=Lost at f8933909, then 'WHITEOUT recovery #3' at f8934096. R1's refusal at f8934170 was the re-entry after the whiteout, and its message says ENTERED_ELITE_FOUR is still True. The Full Restore 1/3 and Revive 2/3 shortfalls had no logged uses, so they predate the entry. No R1 or basket line appears in stdout before that first entry.
- **[REFUTED]** 3. No party in the no-Fly runs held a Fly-compatible species, and among the relevant species only Wingull, Pelipper, Taillow, Swellow, Swablu and Tropius learn HM02.  
  How: The party half is correct (MEASURED). None of the species in the five parties has 19 in species.json tm_hm, and the P2 hb lines show the hidden L65 members were Swampert. The 'only six' half is wrong. species.json lists 38 species that learn move 19. Besides the six named, the Hoenn-obtainable ones include Altaria, Crobat, Skarmory, Vibrava, Flygon, Salamence and Xatu. The runs actually met some of them: P2 r1 had 13 Skarmory and 29 Trapinch battles, P4 r3 met an Altaria, and P3 r5 caught a Zubat (f3887471), whose line reaches Crobat.
- **[CONFIRMED]** 4. P1 r4, P2 r1 and P4 r3 caught a Wingull into the PC box. P3 r5's Wingull attempts ended Won/RanAway.  
  How: MEASURED, but the P2 citation points at the wrong battle. P1 130030 f3753244: Caught, 'vs Wingull L20', 6-member party, then +#278. P4 120136 f4005784: Caught, with 'CATCH #278 Wingull … goes to the PC box'. For P2, the cited frame f4198369 is an ODDISH catch (battle started f4196432). The Wingull was caught at f4194761 on ROUTE 118, with DEXFENCE '(goes to the PC box)' and +#278 at f4197601. P3 112652 had one catch attempt (f3897892), which ended RanAway at f3905092 because of the ball reserve. Its other Wingull battles were Won, and no +#278 appears.
- **[REFUTED]** 5. From the plateau door (18,27) into VR1F (39,5), the exit half is 188 tiles (178 MB_CAVE). Its only other exit is the ladder (21,32) to B1F (20,21), a 9-tile pocket sealed by Rock Smash rocks and Strength boulders. (15,39) is not reachable.  
  How: I decoded the decomp myself (curl of map.bin, general and cave metatile_attributes.bin, and the map.json files). The counts reproduce exactly: 188 tiles, 178 MB_CAVE, warps only (39,5) and (21,32). The B1F pocket is 9 tiles. But 'sealed' and 'not reachable' hold only for a walker that cannot use field moves. From the pocket tile (22,26), the rock at (21,26) can be smashed, and the boulder at (20,26) can then be pushed west onto the free MB_CAVE tile (19,26) (elevation 3). A search that models Rock Smash, Strength pushes, Surf, ledges and waterfalls finds a route to 1F (15,39): pocket -> B1F (17,16) -> B2F -> B1F (30,25) -> ladder (8,3) -> 1F (9,14). That route climbs one waterfall (B2F 9,14->9,11), which needs HM Waterfall; the Ch23 parties had it. INFERRED from an offline model, not a live test. The measured crash was a same-map walk, so it does not refute a cross-map route.
- **[CONFIRMED]** 6. Decomp wild levels: VR 1F 36-40, B1F 38-42 (rock smash 30-40), B2F 40-44.  
  How: Parsed src/data/wild_encounters.json (raw): 1F land 36-40; B1F land 38-42 and rock_smash 30-40; B2F land 40-44 (water 25-40, fishing 5-45).
- **[CONFIRMED]** 7. The ladder only offers out-leveled grounds (max_wild_max=level+1), and the plateau guard refuses any VICTORY_ROAD ground when nobody has Fly on the plateau.  
  How: In the wt/r20fly pokemon_league.py: line 1888 is best_training_area(level, max_wild_max=level + 1, …). Line 1802 returns (not can_fly) and on_plateau and name.startswith('VICTORY_ROAD'). Lines 1926-1935 call it when not can_fly_to_anchor(heal_center). Batch build d21c0c3c has the same code at lines 1792 and 1883.
- **[CONFIRMED]** 8. VR1F's heal anchor is the Ever Grande Poké Center (south half, no walking path from the plateau). Only the League nurse heals on the plateau, and she is not a PokemonCenter.  
  How: story_mode.py:1605 maps VICTORY_ROAD_1F to PokemonCenter.EvergrandeCity (27,48). victory_road.py:361-363 records the Center as walking-unreachable from the exit landing. Line 392 sets LEAGUE_NURSE_STAND (3,4), and line 391 says heal_in_pokemon_center cannot be reused. The PokemonCenter enum (map_data.py:1524-1545) has no League entry. Caveat: 'no walking path' holds within the EVER_GRANDE_CITY map. Claim 5's decode suggests a route through the cave that uses field moves.
- **[CONFIRMED]** 9. §Ch23 TRAIN_TARGET=47 was chosen to fit the 250k per-call ceiling, which chunked training has since replaced. The comment expects the remaining gap to be closed on B1F after Wally.  
  How: victory_road.py:483-493: '47 is the highest target that fits' the 250,000 per-call ceiling, and lines 490-492 put the remaining gap on B1F after Wally. Lines 511-530 describe chunked training replacing the per-call refusal (USER RULING 14). Line 3870 gates on TRAIN_TARGET before Wally, and line 3908 calls train_for_victory_road. Nuance the claim leaves out: lines 487-489 say 47 is also CRUNCH_LEVEL, so the ceiling was not the only reason for the number.
- **[CONFIRMED]** 10. The gap 4 guard was built on a measured crash and narrowed after review. Its graded note says a no-Fly party still cannot train (gap 5 or an exit-half tile, not built).  
  How: walkoff-GRADED.md:11 records the OBSERVE crash 'Could not reach (15, 39) … still at (39, 5)'. Line 13's skip-arm reproduces it (load-bearing). Lines 17-22 cover the review that narrowed the guard. Lines 30-31: 'Such a party still cannot train at all — gap 5 … or a grind tile in VR1F's EXIT half (not built)'.
- **[CONFIRMED]** 11. RULING 20 superseded the chapter-specific flyer options, and RULING 21 allows a brief swap. Box-first Fly is built on wt/r20fly but is not in batch build d21c0c3c. The exit-half tile decision U3 is unresolved.  
  How: 06:7439 says RULING 20 'Supersedes the gap-5 options O2 … and O3', and 7446-7447 gives RULING 21 'swap briefly'. Lines 7765-7785 exist only in the worktree copy of 06, which has 7797 lines; main's copy has 7686. `git merge-base --is-ancestor 553082e2 d21c0c3c` fails, and 553082e2 is only on wt/r20fly. `_boxed_fly_learners` appears 0 times in d21c0c3c's pokemon_league.py, and BOX-FIRST is at worktree lines 2408-2457. RECON:57 poses U3, and no U3 or exit-half ruling is in either 06.
- **[CONFIRMED]** 12. Ninjask and Shedinja share PID ADCAB5A0 in P2 r1, so the PID-only lookups in the §Ch24 ladder would conflate them (inferred).  
  How: MEASURED: P2-stdout:260767 shows Ninjask#ADCAB5A0 and 260768 shows Shedinja#ADCAB5A0, and hb f6966001 lists both. INFERRED: _ch24_slot_of and _ch24_level_of (1699-1727) return the first party match by personality_value. train_for_league uses them at 1879, 1961-1973, 1990 and 2014, so a Shedinja trainee (slot 5) would resolve to Ninjask (slot 1). This run never reached that code because the guard refused first.
