# W7 adversarial pass: chapter pack 1 (ch1.md:95-108)

Pin: tools/decomp.pin = 731ad5bfd6e6f265508d0efcca0ba42f9dcf5881; `git -C _decomp/pokeemerald rev-parse HEAD` = same (MEASURED).
Lookup-first: `decomp_lookup.py ask "route 103 rival battle"` -> "NO PRIOR RULING OR FACT FOUND" (MEASURED).

## FALSE claims
None outright false. One QUALIFIED (claim 14, see below).

## Per-claim verdicts

1-6 [boss_team] TRUE (READ). Each trainers.h line is the trainer's `[TRAINER_...] =` header, `.doubleBattle = FALSE`, party symbol as cited:
- trainers.h:6244 `[TRAINER_BRENDAN_ROUTE_103_MUDKIP] =` ... `.party = NO_ITEM_DEFAULT_MOVES(sParty_BrendanRoute103Mudkip)`; trainer_parties.h:6784-6788 `.lvl = 5, .species = SPECIES_TREECKO`
- trainers.h:6280 BRENDAN_ROUTE_103_TREECKO -> trainer_parties.h:6828 `.lvl = 5, .species = SPECIES_TORCHIC`
- trainers.h:6316 BRENDAN_ROUTE_103_TORCHIC -> trainer_parties.h:6872 `.lvl = 5, .species = SPECIES_MUDKIP`
- trainers.h:6352 MAY_ROUTE_103_MUDKIP -> trainer_parties.h:6916 `SPECIES_TREECKO`, lvl 5
- trainers.h:6388 MAY_ROUTE_103_TREECKO -> trainer_parties.h:6960 `SPECIES_TORCHIC`, lvl 5
- trainers.h:6424 MAY_ROUTE_103_TORCHIC -> trainer_parties.h:7004 `SPECIES_MUDKIP`, lvl 5; trainers.h:6431 `.doubleBattle = FALSE,`
- Single at the script level too: data/maps/Route103/scripts.inc:56-81 `trainerbattle_no_intro TRAINER_..._ROUTE_103_...` (no double variant).
- Name suffix = PLAYER's starter (VAR_STARTER_MON 0/1/2 -> TREECKO/TORCHIC/MUDKIP variant): Route103/scripts.inc:35-38 `switch VAR_STARTER_MON / case 0, ...StartMayBattleTreecko / case 1, ...Torchic / case 2, ...Mudkip`. Rival = opposite gender: scripts.inc:23-24 `goto_if_eq VAR_RESULT, MALE, Route103_EventScript_RivalMay`. So exactly ONE of the six is fought per game (INFERRED from READ).
- Pack moves (Bosses section, not claims) also check: level_up_learnsets.h:3573-3574 Treecko POUND/LEER at 1; 3624-3625 Torchic SCRATCH/GROWL; 3677-3678 Mudkip TACKLE/GROWL (READ).

7-12 [progress_flag] TRUE (READ + arithmetic). include/constants/flags.h:1343 `#define TRAINER_FLAGS_START 0x500` (=1280). opponents.h:524 `TRAINER_BRENDAN_ROUTE_103_MUDKIP 520` (1800), :527 `..._TREECKO 523` (1803), :530 `..._TORCHIC 526` (1806), :533 `TRAINER_MAY_ROUTE_103_MUDKIP 529` (1809), :536 `..._TREECKO 532` (1812), :539 `..._TORCHIC 535` (1815). Flag is set only on a WIN: battle_setup.c:1338-1346 `SetMainCallback2(CB2_WhiteOut);` on defeat, else `SetBattledTrainersFlags();` (:1245-1249 `FlagSet(GetTrainerAFlag());`). Note: battle_setup.c:1252 `static void UNUSED SetBattledTrainerFlag` is unused, not the setter.

13 [double_battle] TRUE (READ). trainers.h:5776 `[TRAINER_AMY_AND_LIV_1] =`, :5778 `.trainerClass = TRAINER_CLASS_TWINS,`, :5783 `.doubleBattle = TRUE,`; script Route103/scripts.inc:198 `trainerbattle_double TRAINER_AMY_AND_LIV_1, ...`. opponents.h:485 `TRAINER_AMY_AND_LIV_1 481` -> flag 1761 matches pack line 50. Party Lv15 PLUSLE/MINUN (trainer_parties.h:6246-6252) (READ).

14 [one_way_warp] QUALIFIED-TRUE (MEASURED: work1/warps.py over all decomp map.json). Exactly 30 warps touch the area maps (`total 30`); 27 are reciprocal (`OK`). The other 3 are INSIDE_OF_TRUCK[0..2] -> `MAP_DYNAMIC` (InsideOfTruck/map.json:65,72,79), resolved by script InsideOfTruck/scripts.inc:33 `setdynamicwarp MAP_LITTLEROOT_TOWN, 3, 10`. NO map in the decomp has a warp with dest MAP_INSIDE_OF_TRUCK (`grep -rln '"dest_map": "MAP_INSIDE_OF_TRUCK"' data/maps/` -> rc=1). So the truck -> Littleroot link IS one-way; "none is one-way by warp data" holds only because DYNAMIC warps were not checkable. Correction: "27 of 30 warps reciprocal; the 3 INSIDE_OF_TRUCK DYNAMIC exits are one-way (no warp back into the truck)". Low impact (truck is ch1_intro only). All 8 map connections reciprocal (MEASURED).
- Also: ROUTE103[0] (45,6) -> ALTERING_CAVE is reciprocal but closed until postgame: Route103/scripts.inc:12 `call_if_set FLAG_SYS_GAME_CLEAR, Route103_EventScript_OpenAlteringCave` (READ).

## MISSING load-bearing facts (not in the claims list)
M1 Story flag for the boss is NOT the trainer flag: Route103/scripts.inc:131-135 `setvar VAR_BIRCH_LAB_STATE, 4` / `setflag FLAG_DEFEATED_RIVAL_ROUTE103` / `setvar VAR_OLDALE_RIVAL_STATE, 1` (set in Route103_EventScript_RivalEnd after the rival exits). Consumed e.g. LittlerootTown_MaysHouse_1F/scripts.inc:113 (READ).
M2 Losing the Route 103 rival battle = whiteout, flag unset: battle_setup.c:1336-1338 `SetMainCallback2(CB2_WhiteOut);` (READ; INFERRED that no_intro routes through CB2_EndTrainerBattle).
M3 Forced first battle on Route 101 (ch1_starter): `special ChooseStarter` (Route101/scripts.inc:223) -> BATTLE_TYPE_FIRST_BATTLE; enemy battle_controllers.c:70 `CreateMon(&gEnemyParty[0], SPECIES_ZIGZAGOON, 2, ...)`; cannot run: battle_main.c:4078-4081 `B_MSG_DONT_LEAVE_BIRCH ... BATTLE_RUN_FORBIDDEN`; loss does NOT white out: battle_setup.c:950-953 CB2_EndFirstBattle only returns to field (READ). Flags: Route101/scripts.inc:217-218 `setflag FLAG_SYS_POKEMON_GET` / `setflag FLAG_RESCUED_BIRCH`.
M4 Gating flag for leaving the chapter west: OldaleTown/scripts.inc:8 `call_if_unset FLAG_ADVENTURE_STARTED, OldaleTown_EventScript_BlockWestEntrance`; set at LittlerootTown_ProfessorBirchsLab/scripts.inc:510 `setflag FLAG_ADVENTURE_STARTED` (with :509 `setvar VAR_BIRCH_LAB_STATE, 5`); Pokedex :537 `setflag FLAG_SYS_POKEDEX_GET`; Poke Balls :519/:527 `giveitem ITEM_POKE_BALL, 5` (READ).
- HM gate: none needed in ch1 (no HM field-move script found in the area; INFERRED, consistent with the pack). Double battles: only AMY_AND_LIV_1 on Route103 (READ scripts.inc:198,216; others are trainerbattle_single).
