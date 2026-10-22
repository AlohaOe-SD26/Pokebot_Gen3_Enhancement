# W7 adversarial pass: chapter pack 4 (Rustboro Gym / Roxanne)
Pin: tools/decomp.pin = 731ad5bfd6e6f265508d0efcca0ba42f9dcf5881; clone HEAD = same (MEASURED, git rev-parse).

## FALSE claims
None.

## Verdicts (all paths under C:/Remote Projects/_decomp/pokeemerald)
1. boss_team: TRUE (READ). src/data/trainers.h:3184 "[TRAINER_ROXANNE_1] =", :3190 ".doubleBattle = FALSE,", party sParty_Roxanne1;
   src/data/trainer_parties.h:3370-3371 ".lvl = 12," ".species = SPECIES_GEODUDE," (x2, 3377-3378), :3384-3386 ".lvl = 15," ".species = SPECIES_NOSEPASS," ".heldItem = ITEM_ORAN_BERRY,".
   Moves match pack (3373, 3387). Script: data/maps/RustboroCity_Gym/scripts.inc:5 "trainerbattle_single TRAINER_ROXANNE_1, ...".
   Not in claim (allowed knowledge): trainers.h:3189 ".items = {ITEM_POTION, ITEM_POTION, ITEM_NONE, ITEM_NONE}," -- Roxanne carries 2 Potions; the pack's Bosses section omits trainer items.
2. defeat flag 1545: TRUE (READ + INFERRED arithmetic). include/constants/opponents.h:269 "#define TRAINER_ROXANNE_1 265"; include/constants/flags.h:1343 "#define TRAINER_FLAGS_START 0x500" -> 1280+265=1545.
   Also JOSH 320->1600 (opponents.h:324), TOMMY 321->1601 (:325), MARC 571->1851 (:575): TRUE.
3. FLAG_BADGE01_GET set by the boss: TRUE (READ). scripts.inc:19 "setflag FLAG_BADGE01_GET" inside RustboroCity_Gym_EventScript_RoxanneDefeated (:13), the defeat script named at :5.
4. CUT hm_gate: TRUE (READ/MEASURED). src/party_menu.c:120 "FIELD_MOVE_CUT,         // FLAG_BADGE01_GET"; :3725 "if (fieldMove <= FIELD_MOVE_WATERFALL && FlagGet(FLAG_BADGE01_GET + fieldMove) != TRUE)".
   Also gated in the overworld tree script: data/scripts/field_move_scripts.inc:4 "goto_if_unset FLAG_BADGE01_GET, EventScript_CheckTreeCantCut".
   113 learners: MEASURED, grep -c "\.CUT = TRUE" src/data/pokemon/tmhm_learnsets.h -> 113 (per-species block count also 113).
   "met wild here: none": TRUE, no Rustboro/Gym entry in src/data/wild_encounters.json (MEASURED, python scan returned []).
5. no one-way warp: TRUE (READ). data/maps/RustboroCity_Gym/map.json warp_events: (5,19) and (6,19) both -> MAP_RUSTBORO_CITY warp 0; data/maps/RustboroCity/map.json warp 0 (27,19) -> MAP_RUSTBORO_CITY_GYM warp 0. Two-way. Gym map: connections null, MAP_TYPE_INDOOR, allow_running false (pack's "no running" correct).

Other pack lines checked: JOSH Lv10 GEODUDE (trainer_parties.h:4230-4231), TOMMY Lv8/8 GEODUDE (:4239-4245), MARC Lv8/8 GEODUDE (:7652-7658), all doubleBattle FALSE (trainers.h:3851, 3863, 6863). Sights from map.json: Josh 2, Tommy 3, Marc 3, Roxanne TRAINER_TYPE_NONE 0. TRUE.

## MISSING load-bearing facts (READ)
- M1 Gym trainers auto-cleared on badge: scripts.inc:22-23 "setvar VAR_0x8008, 1" / "call Common_EventScript_SetGymTrainers"; data/scripts/set_gym_trainers.inc:14-16 "settrainerflag TRAINER_JOSH/TOMMY/MARC". Flags 1600/1601/1851 get set by beating Roxanne even if those trainers were skipped.
- M2 Story progress from the badge: scripts.inc:20 "setvar VAR_RUSTBORO_CITY_STATE, 1", :21 "addvar VAR_PETALBURG_GYM_STATE, 1", :18 "setflag FLAG_DEFEATED_RUSTBORO_GYM" (pack declares story flags out of scope: known exclusion, not an error).
- M3 TM39 gift can be missed on a full bag: scripts.inc:29-31 "giveitem ITEM_TM_ROCK_TOMB" / "goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull" / "setflag FLAG_RECEIVED_TM_ROCK_TOMB"; re-talk re-offers via :8 (items out of scope: known exclusion).
- M4 Roxanne REMATCH is a DOUBLE: scripts.inc:37 "trainerbattle_rematch_double TRAINER_ROXANNE_1, ...". Not this chapter's fight, but "single" on ROXANNE is first-fight-only.
- M5 BADGE01 also gives a 10% Attack boost: src/pokemon.c:3161-3162 "if (ShouldGetStatBadgeBoost(FLAG_BADGE01_GET, battlerIdAtk))" / "attack = (110 * attack) / 100;" (minor).
- No gym entry gate: RustboroCity_Gym MapScripts is scripts.inc:1-2 ".byte 0" (READ; INFERRED no hidden gate).
