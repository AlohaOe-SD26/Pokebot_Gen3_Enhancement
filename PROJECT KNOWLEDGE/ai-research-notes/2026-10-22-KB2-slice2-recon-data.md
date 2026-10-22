# KB2 slice 2 recon (data angle): every source of an item, gift, mart and story event, at the pinned decomp

Pin: `git -C _decomp/pokeemerald rev-parse HEAD` = `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` = tools/decomp.pin (MEASURED).
Lookup-first: `py -3.12 tools/decomp_lookup.py ask "item ball finditem hidden item gift mart"` -> `NO PRIOR RULING OR FACT FOUND` (MEASURED).
All paths below are under `C:/Remote Projects/_decomp/pokeemerald` unless they start with `ai_player/` or `PROJECT KNOWLEDGE/`.
Probe scripts (items.py, gifts.py, gifts2.py, marts.py, flags.py, events.py, prefix.py) were run with `py -3.12 -I` from the
scratchpad `work-data/` and DELETED afterwards per the scratch rule; each count below states what the script did.

## 0. Corrections / additions to ALREADY ESTABLISHED (read first)

- **C1 (MEASURED, load-bearing): the census does not cover ALL event-script source.** `tools/scripts_census.py:42`
  `GROUPS = (("map scripts", "data/maps/*/scripts.inc"), ("shared scripts", "data/scripts/*.inc"))`. But
  `data/event_scripts.s` (1058 lines) holds inline script code: 27 `setflag` and 10 `setvar` lines (`grep -cE "^\s+setflag"` -> 27,
  `setvar` -> 10; gift/mart lines there: 0). Example that matters for marts: `data/event_scripts.s:676-678`
  `Common_EventScript_ReadyPetalburgGymForBattle::` / `clearflag FLAG_HIDE_PETALBURG_GYM_GREETER` / `setflag FLAG_PETALBURG_MART_EXPANDED_ITEMS`
  (the ONLY setter of that flag anywhere: `grep -rln PETALBURG_MART_EXPANDED .` -> event_scripts.s, PetalburgCity_Mart/scripts.inc, flags.h).
  Also `data/event_scripts.s:785 RusturfTunnel_EventScript_SetRusturfTunnelOpen:: setflag FLAG_RUSTURF_TUNNEL_OPENED` and the
  Mr. Briney move blocks (:597-623, :768-775, all FLAG_HIDE_*). "0 UNPARSED" stays true for the two globs; "complete" is not
  true for slice 2's purposes. A parser for events.json must also read event_scripts.s (its `.include` lines otherwise pull
  only the two globs plus data/text/*.inc).
- **C2 (MEASURED, load-bearing): slice 1 ALREADY extracts item balls and hidden items.** `ai_player/gates/extract_world.py:428-430`
  `def item_ball_scripts(d)` ... `finditem\s+(ITEM_\w+)`, and :510-515 `rec["item_balls"] = ...` / `rec["hidden_items"] = ...`.
  `ai_player/knowledge/world/maps.json`: 518 maps, 162 item_balls, 112 hidden_items (MEASURED by a python count). These
  equal the decomp counts below exactly. items_gifts.json does not need to re-derive field items; it can reference maps.json.
- **C3 (READ): other item-giving shapes beyond giveitem/givemon/giveegg/givedecoration/finditem:** `additem` (10 map lines +
  3 shared, census lines 193 and 582), incl. the Game Corner TMs `data/maps/MauvilleCity_GameCorner/scripts.inc:296`
  `additem ITEM_TM_DOUBLE_TEAM` (also :309 PSYCHIC, :322 FLAMETHROWER, :335 THUNDERBOLT, :348 ICE_BEAM) and
  `LilycoveCity_ContestLobby/scripts.inc:345 additem ITEM_CONTEST_PASS`. 15 `giveitem VAR_*` lines carry an item chosen at
  runtime (e.g. `Route123_BerryMastersHouse/scripts.inc:18 giveitem VAR_RESULT`), not statically nameable from the line.

## Q1. Item balls (map object -> item_ball_scripts.inc)

Mechanism (READ):
- The object's `script` field names a label in the shared file; `data/event_scripts.s:1024 .include "data/scripts/item_ball_scripts.inc"`.
- The label body is only `finditem ITEM_X` + `end` (no flag, no amount: 0 of 165 labels pass an amount, MEASURED).
- `asm/macros/event.inc:1955-1958` `.macro finditem item:req, amount=1` / `setorcopyvar VAR_0x8000, \item` / ... / `callstd STD_FIND_ITEM`.
- `data/event_scripts.s:98 .4byte Std_FindItem @ STD_FIND_ITEM`; `data/scripts/obtain_item.inc:95 Std_FindItem::`,
  :106 `call_if_eq VAR_0x8007, TRUE, EventScript_PickUpItem`, :111-112 `EventScript_PickUpItem::` / `removeobject VAR_LAST_TALKED`.
- The FLAG lives only in map.json: `removeobject` -> `src/scrcmd.c:1052 RemoveObjectEventByLocalIdAndMap(...)` ->
  `src/event_object_movement.c:1394 FlagSet(GetObjectEventFlagIdByObjectEventId(objectEventId));`. Bag full: `obtain_item.inc:107`
  `call_if_eq VAR_0x8007, FALSE, EventScript_NoRoomToPickUpItem` (ball stays; flag not set).

Example 1 (READ): `data/maps/Route102/map.json:94-104` `"graphics_id": "OBJ_EVENT_GFX_ITEM_BALL"`, `"x": 11`, `"y": 15`, ...
`"script": "Route102_EventScript_ItemPotion"`, `"flag": "FLAG_ITEM_ROUTE_102_POTION"` -> `data/scripts/item_ball_scripts.inc:1-2`
`Route102_EventScript_ItemPotion::` / `finditem ITEM_POTION` -> `include/constants/flags.h:1053 #define FLAG_ITEM_ROUTE_102_POTION 0x3E8`.
Example 2 (READ): `data/maps/Route104/map.json:296-306` `OBJ_EVENT_GFX_ITEM_BALL`, `"x": 39`, `"y": 15`,
`"script": "Route104_EventScript_ItemPPUp"`, `"flag": "FLAG_ITEM_ROUTE_104_PP_UP"` -> `item_ball_scripts.inc:13-14`
`Route104_EventScript_ItemPPUp::` / `finditem ITEM_PP_UP` -> `flags.h:1055 #define FLAG_ITEM_ROUTE_104_PP_UP 0x3EA`.

Counts (MEASURED, items.py over all `data/maps/*/map.json` object_events = 2776):
- 222 objects with `OBJ_EVENT_GFX_ITEM_BALL`; **162** of them name an item_ball_scripts label; 162 distinct flags, all `FLAG_ITEM_*`;
  every label prefix equals its map name (prefix.py: 0 mismatches); no non-ball graphic uses an item-ball label; no label used twice.
- **165 labels vs 162 objects: the 3 unreferenced labels are dead data** (grep of the whole tree finds only their definition):
  `item_ball_scripts.inc:529-530 AquaHideout_B2F_EventScript_ItemMasterBall:: / finditem ITEM_MASTER_BALL      // Unused`,
  `:537-538 Route119_EventScript_ItemMaxElixir:: / finditem ITEM_MAX_ELIXIR`, `:541-542 Route119_EventScript_ItemNestBall:: / finditem ITEM_NEST_BALL`.
- The 60 ITEM_BALL-graphic objects with another script are NOT field items: 48 Battle Pyramid (`BattlePyramid_FindItemBall`,
  flag "0", BattlePyramidSquare01..16 x3), and 12 Pokemon/props drawn as a ball: AquaHideout_B1F Electrode1/2, NewMauville_Inside
  Voltorb1-3, Birch's lab Cyndaquil/Totodile/Chikorita, MossdeepCity_StevensHouse Beldum, the rivals' house 2F balls, ContestHall (script 0x0).
- The one `finditem` in map scripts is dead: `data/maps/MossdeepCity_StevensHouse/scripts.inc:139-142` `@ Unused, leftover from RS` /
  `MossdeepCity_StevensHouse_EventScript_DiveItemBall::` / `finditem ITEM_HM_DIVE`; unreachable from any root (gifts.py). The real
  Dive gift is `MossdeepCity_StevensHouse/scripts.inc:36 giveitem ITEM_HM_DIVE`.

## Q2. Hidden items (map.json bg_events)

Shape (MEASURED): every hidden_item bg_event has exactly the keys `elevation, flag, item, type, x, y` (112 of 112); no
`quantity`/`underfoot` key; 112 distinct flags, all `FLAG_HIDDEN_ITEM_*`. bg_event totals: sign 533, hidden_item 112, secret_base 75.
Runtime (READ): `src/field_control_avatar.c:348-353` `case BG_EVENT_HIDDEN_ITEM:` / `gSpecialVar_0x8004 = (... >> 16) + FLAG_HIDDEN_ITEMS_START;`
/ `gSpecialVar_0x8005 = (u32)bgEvent->bgUnion.script;` / `if (FlagGet(gSpecialVar_0x8004) == TRUE) return NULL;` / `return EventScript_HiddenItemScript;`;
flag set at `obtain_item.inc:183 special SetHiddenItemFlag` -> `src/field_specials.c:935-937 FlagSet(gSpecialVar_0x8004)`.
`flags.h:545 #define FLAG_HIDDEN_ITEMS_START 0x1F4`. (No script label: the item is in map.json, not in any .inc.)
Example 1 (READ): `data/maps/Route104/map.json:606-611` `"type": "hidden_item"`, `"x": 14`, `"y": 55`, `"item": "ITEM_POTION"`, `"flag": "FLAG_HIDDEN_ITEM_ROUTE_104_POTION"`.
Example 2 (READ): `data/maps/Route113/map.json:449-454` `"x": 22`, `"y": 5`, `"item": "ITEM_TM_DOUBLE_TEAM"`, `"flag": "FLAG_HIDDEN_ITEM_ROUTE_113_TM_DOUBLE_TEAM"`.

## Q3. Gifts

Totals (MEASURED, gifts.py; agrees with the census): map scripts giveitem 145, givedecoration 13, givemon 7, giveegg 1,
finditem 1 (dead); shared giveitem 15, giveegg 1, finditem 165. `asm/macros/event.inc:1947-1950` `.macro giveitem item:req, amount=1` ... `callstd STD_OBTAIN_ITEM`.

Reachability (MEASURED: a label graph over both globs; edges = any argument naming a label + fall-through; roots = every
map.json object/coord/bg `script` (2112/289/475) plus each `<Map>_MapScripts`):
- reachable: all 145 giveitem + 13 givedecoration + 7 givemon + 1 giveegg in map scripts; 11 of 15 shared giveitem; 162 of 165 finditem.
- NOT reachable (9): the dead Dive ball; the 3 dead item-ball labels; Mystery Gift scripts `data/scripts/gift_aurora_ticket.inc:14`,
  `gift_battle_card.inc:12`, `gift_mystic_ticket.inc:15`, `gift_old_sea_map.inc:14` (giveitem) and `gift_pichu.inc:31 giveegg SPECIES_PICHU`.
  (event_scripts.s was not in the graph: C1; it has 0 gift lines.)

How the condition is expressed (MEASURED, gifts2.py over the 183 non-item-ball gift lines, forward closure within the file):
- 128: a `setflag` near the gift whose flag is tested by `goto_if_set/unset` or `call_if_set/unset` somewhere (the classic one-time gift);
- 25: no tested flag but a saved var set nearby and compared (VAR_*_STATE etc.);
- 1: the flag set is the giver's object-hide flag (giver disappears);
- 3: flag set but never tested in scripts (`Route119/scripts.inc:130 giveitem ITEM_HM_FLY` + :131 `setflag FLAG_RECEIVED_HM_FLY`;
  `RusturfTunnel/scripts.inc:56 giveitem ITEM_HM_STRENGTH`; `gift_battle_card.inc`): one-shot because the calling scene runs once (INFERRED);
- 26: no flag/var in the closure: repeatable or caller-guarded (bikes `MauvilleCity_BikeShop/scripts.inc:43,49,85,93`, Birch's Poke Balls
  `LittlerootTown_ProfessorBirchsLab/scripts.inc:519,527`, fossils `DesertUnderpass/scripts.inc:18,24`, berry gifts, Trick House tents, etc.).
  These counts are a HEURISTIC (bounded closure, same-file only), INFERRED-grade; the 128 is a floor.
- Bag-full branch: 85 of 160 giveitem lines (and 6 of 13 givedecoration) are followed within 2 commands by `goto_if_eq VAR_RESULT, FALSE, <label>`
  (gifts.py pattern counts: giveitem 69 with a later setflag + 16 without; MEASURED). A gift missed on a full bag stays offered when its flag is set only after that check (Example A/B).
- Q3 W7 rows in the W7 notes (PetalburgCity_Gym:716 etc.) are W7's READ citations, not re-read here.

Example A, one-time TM, object root (READ): `data/maps/Route104/map.json:439-449` `OBJ_EVENT_GFX_BOY_2`, `"x": 5`, `"y": 26`,
`"script": "Route104_EventScript_Boy2"`, `"flag": "0"` -> `Route104/scripts.inc:317-325` `Route104_EventScript_Boy2::` ...
:320 `goto_if_set FLAG_RECEIVED_TM_BULLET_SEED, Route104_EventScript_ReceivedBulletSeed` / :322 `giveitem ITEM_TM_BULLET_SEED` /
:323 `goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull` / :324 `setflag FLAG_RECEIVED_TM_BULLET_SEED`. flags.h:288 `0x106`.
Example B, boss post-battle TM (READ): `RustboroCity_Gym/scripts.inc:5 trainerbattle_single TRAINER_ROXANNE_1, ..., RustboroCity_Gym_EventScript_RoxanneDefeated, NO_MUSIC`;
:8 `goto_if_unset FLAG_RECEIVED_TM_ROCK_TOMB, RustboroCity_Gym_EventScript_GiveRockTomb`; :29-31 `giveitem ITEM_TM_ROCK_TOMB` /
`goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull` / `setflag FLAG_RECEIVED_TM_ROCK_TOMB`. flags.h:187 `0xA5`.
Example C, egg (flag BEFORE the gift) (READ): `LavaridgeTown/map.json:139 "script": "LavaridgeTown_EventScript_EggWoman"` ->
`LavaridgeTown/scripts.inc:224 goto_if_set FLAG_RECEIVED_LAVARIDGE_EGG, ...`, :230 `setflag FLAG_RECEIVED_LAVARIDGE_EGG`, :234 `giveegg SPECIES_WYNAUT`.
Example D, givemon (flag in a successor label) (READ): `RustboroCity_DevonCorp_2F/scripts.inc:142-145` `givemon SPECIES_LILEEP, 20` /
`goto_if_eq VAR_RESULT, MON_GIVEN_TO_PARTY, ..._ReceiveLileepParty` / `goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC, ..._ReceiveLileepPC` / `goto Common_EventScript_NoMoreRoomForPokemon`.
All givemon (READ): Birch lab :329 CYNDAQUIL 5, :370 TOTODILE 5, :411 CHIKORITA 5 (postgame Johto starters); `MossdeepCity_StevensHouse/scripts.inc:81 BELDUM, 5`;
`Route119_WeatherInstitute_2F/scripts.inc:81 givemon SPECIES_CASTFORM, 25, ITEM_MYSTIC_WATER`; DevonCorp_2F :142 LILEEP 20, :187 ANORITH 20.
(The Hoenn starter is NOT a givemon: `special ChooseStarter`, `Route101/scripts.inc:223`, per W7 ch1 M3.)

## Q4. Marts

(MEASURED, marts.py; READ for the quoted lines.) `asm/macros/event.inc:1152-1154 .macro pokemart products:req` / `.byte SCR_OP_POKEMART` / `.4byte \products`;
lists are `.2byte ITEM_*` lines ended by `pokemartlistend` (:1158-1159 `.2byte ITEM_NONE`). `src/shop.c:378-390 SetShopItemsForSale` just counts to the
terminator: no badge or story filter in C (grep of `FlagGet|FLAG_BADGE|VarGet` in src/shop.c: no hit).
- 27 `pokemart` (+5 `pokemartdecoration`, +5 `pokemartdecoration2`), all reachable. 22 pokemart lines are unconditional (one list per clerk).
- **Contents change ONLY by a script branch choosing a different list label; 4 marts do it, 5 list pairs:**
  - Oldale: `OldaleTown_Mart/scripts.inc:9 goto_if_set FLAG_ADVENTURE_STARTED, OldaleTown_Mart_ExpandedItems`; :10 Basic (POTION ANTIDOTE PARALYZE_HEAL AWAKENING) vs :24 Expanded (+POKE_BALL).
  - Petalburg: `PetalburgCity_Mart/scripts.inc:9 goto_if_set FLAG_PETALBURG_MART_EXPANDED_ITEMS, ...`; :10 Basic (11) vs :31 Expanded (13: +GREAT_BALL, +SUPER_POTION).
    The flag is set only in `event_scripts.s:678`, called when VAR_PETALBURG_GYM_STATE == 6, e.g. `RustboroCity_Gym/scripts.inc:24 call_if_eq VAR_PETALBURG_GYM_STATE, 6, Common_EventScript_ReadyPetalburgGymForBattle` (also DewfordTown_Gym:153, LavaridgeTown_Gym_1F:64, MauvilleCity_Gym:96), i.e. at the 4th badge (INFERRED from W7 ch2's state arithmetic).
  - Rustboro: `RustboroCity_Mart/scripts.inc:9-10 goto_if_unset/goto_if_set FLAG_MET_DEVON_EMPLOYEE`; :14 Basic (10) vs :34 Expanded (12: +TIMER_BALL +REPEAT_BALL); flag set at `Route116/scripts.inc:55 setflag FLAG_MET_DEVON_EMPLOYEE`.
  - Trainer Hill: `TrainerHill_Entrance/scripts.inc:240 goto_if_set FLAG_SYS_GAME_CLEAR, ...`; :241 Basic vs :262 Expanded (postgame).
- Other gates on a shop (not list swaps): Slateport decor `SlateportCity/scripts.inc:480 goto_if_unset FLAG_RECEIVED_SECRET_POWER`; flower shop
  `Route104_PrettyPetalFlowerShop/scripts.inc:19 goto_if_set FLAG_TEMP_1, ..._SellDecorations`; rooftop sale woman shown only when
  `LilycoveCity_DepartmentStoreRooftop/scripts.inc:6-8 getpokenewsactive POKENEWS_LILYCOVE` (its list ends `.2byte 0`, not pokemartlistend).
- Mart TMs: `LilycoveCity_DepartmentStore_4F` :21 FIRE_BLAST THUNDER BLIZZARD HYPER_BEAM, :39 PROTECT SAFEGUARD REFLECT LIGHT_SCREEN;
  `SlateportCity/scripts.inc:511` HIDDEN_POWER SECRET_POWER.
- Item counts per list (MEASURED, marts.py): Mauville 12, Verdanturf 11, Fallarbor 12, Lavaridge 9, Fortree 10, Lilycove 2F 11+10, Mossdeep 9, Sootopolis 9, League 7, Frontier 13, Slateport 9.

## Q5. TMs and HMs given by scripts (READ; `grep -rnE "^\s+giveitem ITEM_(TM|HM)"` -> 42 lines, 34 distinct items)

HMs (8): CUT `RustboroCity_CuttersHouse/scripts.inc:9`; FLASH `GraniteCave_1F/scripts.inc:9`; ROCK_SMASH `MauvilleCity_House1/scripts.inc:9`;
STRENGTH `RusturfTunnel/scripts.inc:56`; SURF `PetalburgCity_WallysHouse/scripts.inc:22`; FLY `Route119/scripts.inc:130`;
DIVE `MossdeepCity_StevensHouse/scripts.inc:36`; WATERFALL `SootopolisCity/scripts.inc:1260`.
Gym TMs (each on 2 lines, post-battle + re-talk): ROCK_TOMB RustboroCity_Gym:29; BULK_UP DewfordTown_Gym:171,178; SHOCK_WAVE MauvilleCity_Gym:115,123;
OVERHEAT LavaridgeTown_Gym_1F:82,90; FACADE PetalburgCity_Gym:394; AERIAL_ACE FortreeCity_Gym:52,60; CALM_MIND MossdeepCity_Gym:93,101; WATER_PULSE SootopolisCity_Gym_1F:118,125.
Other TMs: BULLET_SEED Route104:322; SLUDGE_BOMB DewfordTown_Hall:238; RETURN FallarborTown_CozmosHouse:19 and PacifidlogTown_House2:41; FRUSTRATION PacifidlogTown_House2:56;
HIDDEN_POWER FortreeCity_House2:22; STEEL_WING GraniteCave_StevensRoom:12; REST LilycoveCity_House2:9; THUNDERBOLT MauvilleCity:418; ROAR Route114:48;
DIG Route114_FossilManiacsHouse:14; GIGA_DRAIN Route123:17; BRICK_BREAK SootopolisCity_House1:9; SNATCH SSTidalRooms:9; TORMENT SlateportCity_BattleTentLobby:202;
ATTRACT VerdanturfTown_BattleTentLobby:227; THIEF SlateportCity_OceanicMuseum_1F:146; TAUNT Route110_TrickHouseEnd:110 and Route110_TrickHouseEntrance:362;
SECRET_POWER data/scripts/secret_power_tm.inc:46.
Not via giveitem: Game Corner `additem` x5 (C3); 14 TM item balls (FieryPath TOXIC, Route111 SANDSTORM, Route115 FOCUS_PUNCH, MeteorFalls IRON_TAIL and DRAGON_CLAW,
AbandonedShip ICE_BEAM and RAIN_DANCE, MtPyre SHADOW_BALL and SKILL_SWAP, ScorchedSlab SUNNY_DAY, SafariZone_Northwest SOLAR_BEAM, ShoalCave HAIL,
SeafloorCavern_Room9 EARTHQUAKE, VictoryRoad_B1F PSYCHIC; MEASURED prefix.py); 1 hidden (Route113 DOUBLE_TEAM, Q2); 10 mart TMs (Q4).

## Q6. setflag / setvar by family (MEASURED, flags.py: name prefix, and the flags.h/vars.h section the define sits under)

flags.h has NO "story range": it has a `// Scripts` block (`flags.h:95`, 0x50..), `// Event Flags` (`:748`, from 0x2BC, mostly FLAG_HIDE_*),
`// Item Ball Flags` (`:1052`, 0x3E8), `// Trainer Flags` (`:1339`), `// System Flags` (`:1346`, 0x860), `// Badges` (`:1358`), `// Towns and Cities` (`:1369`,
runs to `:1569`, so it also holds FLAG_SYS_* toggles), `// Daily Flags` (`:1569`), `// Special Flags` (`:1643`, 0x4000, not saved). Story flags are spread
over `Scripts` and the system block, so a name-family rule is the practical classifier.
- map scripts setflag 606: FLAG_HIDE_* 148; FLAG_RECEIVED_* 105; FLAG_DEFEATED_* 62; FLAG_TEMP_* 37 (incl. temp aliases); FLAG_SYS_* 33; FLAG_MET_* 32;
  FLAG_ENABLE_* 20; FLAG_VISITED_* 16; FLAG_DAILY_* 9; FLAG_BADGE* 8; FLAG_INTERACTED_* 2; other 134 (e.g. FLAG_REGISTER_RIVAL_POKENAV, FLAG_WALLACE_GOES_TO_SKY_PILLAR).
  By section: scripts 240, event 145, system/visited 83, (block after Match-Call registered) 52, temp 34+3, special 16, item_ball 13, daily 9, badge 8, system 3. 493 distinct flag names.
- shared setflag 256: FLAG_HIDE_* 187, other 23, FLAG_DECORATION_* 14, FLAG_SYS_* 9, FLAG_RECEIVED_* 8, ENABLE 5, TEMP 5, DAILY 3, UNLOCKED 1, `setflag VAR_0x8005` 1.
- event_scripts.s setflag 27: FLAG_HIDE_* 24, other 3 (C1).
- map scripts setvar 1521: special/result vars (VAR_0x8xxx, VAR_RESULT...) 727; VAR_TEMP_* 396; **VAR_*_STATE 243 (73 distinct)**; other 155
  (VAR_FRONTIER_* 34, VAR_OBJ_GFX_ID_* 36, VAR_TRICK_HOUSE_PRIZE_PICKUP 12, VAR_LITTLEROOT_HOUSES_STATE_MAY/_BRENDAN 3+3 (story vars not ending in _STATE)).
  By section: special 730, saved 354, temp 310 + alias 86, obj gfx 41. Shared setvar 325: special 192, TEMP 79, other 32, _STATE 18, non-VAR 4. event_scripts.s setvar 10: _STATE 2.
- So: of 606 map setflags, ~412 are persistent and not FLAG_HIDE_* (606-148-37-9), and of 1521 setvars only 354 hit saved vars (the rest are scratch). INFERRED from the counts.
- Story progress also moves by commands the spec does not list: `addvar` 81 map + 24 shared (e.g. `RustboroCity_Gym/scripts.inc:21 addvar VAR_PETALBURG_GYM_STATE, 1`),
  `clearflag` 217 + 37, `settrainerflag` 57 shared (`data/scripts/set_gym_trainers.inc`), `subvar` 11, `cleartrainerflag` 3 (census lines 98, 74, 495, 190, 278).
- Other event sources in map.json (MEASURED, events.py): coord_events 375 = trigger 289 (var: VAR_TEMP_* 129, *_STATE 118, other 42) + weather 86;
  object `flag` fields: FLAG_HIDE_* 483, FLAG_ITEM_* 162, FLAG_TEMP_* 135, other 360 (e.g. FLAG_DECORATION_1..), none 1636.
  map_script lines: 244 `map_script_2` (var==value frame/warp tables), ON_TRANSITION 200, ON_FRAME_TABLE 122, ON_RESUME 88, ON_WARP_INTO_MAP_TABLE 78, ON_LOAD 65.

## Q7. W7's missing facts -> slice-2 file and decomp source

| # | fact (W7 file) | slice-2 file | decomp source |
|---|---|---|---|
| 1 | FLAG_DEFEATED_RIVAL_ROUTE103 + VAR_BIRCH_LAB_STATE 4 + VAR_OLDALE_RIVAL_STATE 1 (ch1 M1) | events.json | `Route103/scripts.inc:131-135` setvar/setflag |
| 2 | losing the rival = whiteout, flag unset (ch1 M2) | NONE from scripts; one global rule | C: `src/battle_setup.c:1336-1338` (W7) |
| 3 | forced first battle: Zigzagoon Lv2, cannot run, loss returns to field (ch1 M3) | events.json carries only `special ChooseStarter` (`Route101/scripts.inc:223`); the battle facts are NONE (C: battle_controllers.c:70, battle_main.c:4078) | |
| 4 | Oldale west gate FLAG_ADVENTURE_STARTED / VAR_OLDALE_TOWN_STATE (ch1 M4, ch2 #5) | events.json | `OldaleTown/scripts.inc:8`, OldaleTown/map.json coord (0,10), lab :510-511 |
| 5 | Pokedex flag, 5 Poke Balls from the lab (ch1 M4) | events.json + items_gifts.json | lab :537 setflag; :519/:527 giveitem (no own flag: Q3 "26") |
| 6 | Petalburg Gym doors locked until VAR_PETALBURG_GYM_STATE >= 6; `addvar` per badge (ch2) | events.json (needs `goto_if_lt` + `addvar`) | `PetalburgCity_Gym/scripts.inc:716,744`; gyms' `addvar` |
| 7 | scripted `warp` / `warpdoor` moves (ch2 #2) | events.json (not maps.json, which holds only warp_events) | `warp` 116+5, `warpdoor` 2, `warpsilent` 13 lines (census) |
| 8 | Wally tutorial is `special StartWallyTutorialBattle` with party swap (ch2 #3) | events.json (special line); semantics NONE (C) | `PetalburgCity/scripts.inc:32-50` |
| 9 | Petalburg west-exit steer triggers (ch2 #4, ch3 M5) | events.json (coord trigger + setobjectxyperm) | PetalburgCity/map.json coord x=8,y=10..13; scripts.inc:8,14 |
| 10 | Petalburg Woods grunt FORCED (ch3 M1) | events.json for the trigger; "forced" needs a layout BFS: NONE in either file (data/layouts blockdata) | PetalburgWoods/map.json (26,23),(27,23); scripts.inc:23,51,92 |
| 11 | rival battles optional, YES/NO (ch3 M2) | events.json (msgbox MSGBOX_YESNO before trainerbattle_no_intro) | `Route104/scripts.inc:107,129,192,200`; `RustboroCity/scripts.inc:744,753,811,819` |
| 12 | rival gating vars set only after Devon Corp 3F (ch3 M3) | events.json | `RustboroCity_DevonCorp_3F/scripts.inc:68`; `RustboroCity/scripts.inc:33,88` |
| 13 | Gina & Mia need 2 usable mons (ch3 M4) | slice 1 trainers.json (`double`) + a rule; not slice 2 | `trainerbattle_double` NotEnoughMons arg, Route104/scripts.inc:966 |
| 14 | badge sets the gym trainers' flags (ch4 M1) | events.json (needs `settrainerflag` via `call Common_EventScript_SetGymTrainers`) | `RustboroCity_Gym/scripts.inc:22-23`; `data/scripts/set_gym_trainers.inc:14-16` |
| 15 | VAR_RUSTBORO_CITY_STATE 1, PETALBURG_GYM_STATE +1, FLAG_DEFEATED_RUSTBORO_GYM (ch4 M2) | events.json | `RustboroCity_Gym/scripts.inc:18,20,21` |
| 16 | TM39 Rock Tomb, missable on a full bag, re-offered (ch4 M3) | items_gifts.json | `RustboroCity_Gym/scripts.inc:8,29-31` |
| 17 | Roxanne rematch is a double (ch4 M4) | slice 1 trainers.json / bosses.json (rematch macro), not slice 2 | `RustboroCity_Gym/scripts.inc:37 trainerbattle_rematch_double` |
| 18 | Roxanne carries 2 Potions (ch4 claim 1 note) | NONE in the slice-2 files; slice 1 deliberately omits `.items` (`extract_world.py:36`) | `src/data/trainers.h:3189` |
| 19 | Badge 1 = 10% Attack (ch4 M5) | NONE (C mechanic) | `src/pokemon.c:3161-3162` |
| 20 | MAP_DYNAMIC truck warps are one-way (index) | already FIXED in slice 1 per 00-INDEX.md | InsideOfTruck/scripts.inc:33 |
