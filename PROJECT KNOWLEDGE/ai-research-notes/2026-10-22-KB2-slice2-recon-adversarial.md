# KB2 slice 2 recon, ADVERSARIAL angle: how a naive "parse finditem/giveitem/pokemart/setflag per map" goes wrong

Pin: `git -C _decomp/pokeemerald rev-parse HEAD` = 731ad5bfd6e6f265508d0efcca0ba42f9dcf5881 = tools/decomp.pin (MEASURED).
Lookup-first: `decomp_lookup.py ask "item gift flag events"` -> "NO PRIOR RULING OR FACT FOUND" (MEASURED).
All decomp paths are relative to `C:/Remote Projects/_decomp/pokeemerald`. Probe scripts (deleted after the run) were
balls.py, gifts.py, reach.py, flags.py, vars.py in the scratch work dir; their outputs are quoted below.

## 0. Corrections to ALREADY ESTABLISHED

- **E1 "12 #ifdef BUGFIX/UBFIX blocks": the count is 11, not 12** (MEASURED). `grep -rnE "#if(n)?def (BUGFIX|UBFIX)"
  data/maps/*/scripts.inc data/scripts/*.inc | wc -l` -> `11` (8 map: BattleTowerLobby x2, ContestLobby, Museum_2F,
  SpaceCenter_1F, SpaceCenter_2F, SkyPillar_2F, SkyPillar_4F; 3 shared: cave_hole, safari_zone, trainer_hill). The
  census note itself lists exactly these 11 (28 preprocessor lines), so the "12" is in the task text, not the census.
- **E2 the census scope misses `data/event_scripts.s`** (MEASURED). tools/scripts_census.py:42 `GROUPS = (("map scripts",
  "data/maps/*/scripts.inc"), ("shared scripts", "data/scripts/*.inc"))`. data/event_scripts.s holds commands too:
  `grep -c "^\s*setflag" data/event_scripts.s` -> `27`. Story-relevant examples: event_scripts.s:678 `setflag
  FLAG_PETALBURG_MART_EXPANDED_ITEMS`; :784-785 `setvar VAR_RUSTURF_TUNNEL_STATE, 6` / `setflag FLAG_RUSTURF_TUNNEL_OPENED`;
  :629-633 the Elite Four reset (`clearflag FLAG_DEFEATED_ELITE_4_SIDNEY` ... `setvar VAR_ELITE_4_STATE, 0`).
  "0 UNPARSED" is true for the files it read; it is not "every event-script line".
- **E3 slice 1 ALREADY extracts field items and hidden items** (READ). ai_player/gates/extract_world.py:510-515
  `rec["item_balls"] = [...]` / `rec["hidden_items"] = [...]` in maps.json. A slice 2 that re-parses them creates two
  sources for one fact; INFERRED: slice 2 should consume or cross-check maps.json's lists, not re-derive them a second way.

## 1. Conditionality (each kind: example, and what a static record must say to stay TRUE)

| kind | example (READ unless tagged) | a TRUE static record says |
|---|---|---|
| item is a runtime VALUE, not a constant | 15 `giveitem VAR_*` lines (MEASURED: `grep ... \| grep -v "giveitem ITEM_"`), e.g. LilycoveCity/scripts.inc:39-41 `random 10` / `addvar VAR_RESULT, FIRST_BERRY_INDEX` / `giveitem VAR_RESULT`; lottery DepartmentStore_1F/scripts.inc:40 `giveitem VAR_0x8005` from src/lottery_corner.c:14-19 `sLotteryPrizes[] = ITEM_PP_UP, ITEM_EXP_SHARE, ITEM_MAX_REVIVE, ITEM_MASTER_BALL` | "one of {set}, chosen at random / by a draw", with the set cited (C table or the random range); never a single item, never "VAR_RESULT" |
| daily (RTC) | LilycoveCity:37 `goto_if_set FLAG_DAILY_LILYCOVE_RECEIVED_BERRY`; 8 `FLAG_DAILY_*` gift lines (MEASURED, gifts.py) incl. Route104_PrettyPetalFlowerShop:82-88, Route111:148-152, Route114:26-33, Route120:90-136, Route123_BerryMastersHouse:13-20, SootopolisCity:700-707 | "repeatable once per day" (not "once") |
| weekly | PacifidlogTown_House2:8 `goto_if_set FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK`; :21 `specialvar VAR_RESULT, GetDaysUntilPacifidlogTMAvailable` | "repeatable weekly" |
| hidden mon stat decides WHICH item | PacifidlogTown_House2:13-17 `GetLeadMonFriendshipScore` -> :41 `giveitem ITEM_TM_RETURN` / :56 `giveitem ITEM_TM_FRUSTRATION`; also SlateportCity_PokemonFanClub:194, MossdeepCity_House1:9 `GetPokeblockNameByMonNature` | "Return OR Frustration, by the lead's friendship" -- a condition the AI cannot read (RULING 40 hidden state); the record must not imply a choice |
| player data decides which | Route120:94-99 `specialvar VAR_RESULT, GetPlayerTrainerIdOnesDigit` / `case 0, Route120_EventScript_GiveFigyBerry` ... | "one berry, by the trainer ID's last digit" |
| starter | MauvilleCity_GameCorner:385-388 `switch VAR_STARTER_MON` -> :396 `givedecoration DECOR_TREECKO_DOLL` (x3 labels, each `setflag FLAG_RECEIVED_STARTER_DOLL`) | "the doll of YOUR starter" (one of three) |
| gender | data/scripts/players_house.inc:392-407 `PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV` `checkplayergender` ... `giveitem ITEM_SS_TICKET`, called from BOTH LittlerootTown_BrendansHouse_1F and _MaysHouse_1F (MEASURED, reach.py) | "in the player's own house" (resolve by gender, as milestones.json `gendered_maps` does), not both houses |
| mutually exclusive choice | MirageTower_4F:9-15 `giveitem ITEM_ROOT_FOSSIL` / `setflag FLAG_HIDE_MIRAGE_TOWER_CLAW_FOSSIL` / `setflag FLAG_CHOSE_ROOT_FOSSIL` (and :29-35 the Claw mirror); downstream RustboroCity_DevonCorp_2F:142 `givemon SPECIES_LILEEP, 20` vs :187 `givemon SPECIES_ANORITH, 20`; Johto starters LittlerootTown_ProfessorBirchsLab:329/370/411 | "ONE of {A, B}; taking one removes the other"; a list of both is false |
| random AVAILABILITY of the place | src/mirage_tower.c:327-336 `rand = Random(); visible = rand & 1;` ... `FlagSet(FLAG_MIRAGE_TOWER_VISIBLE)`, called by Route111/scripts.inc:42 `special SetMirageTowerVisibility`; forced visible by MirageTower_1F:7 `setflag FLAG_FORCE_MIRAGE_TOWER_VISIBLE` | "the fossils are in a tower that appears on some visits" |
| badge / story flag gates the giver | Route104:20-24 `goto_if_unset FLAG_MET_PRETTY_PETAL_SHOP_OWNER, ...HideWhiteHerbFlorist` / `goto_if_unset FLAG_BADGE03_GET, ...` / `clearflag FLAG_HIDE_ROUTE_104_WHITE_HERB_FLORIST` | "after badge 3 and meeting the shop owner" |
| mart stock changes | 4 marts with Basic/Expanded lists (MEASURED, grep -B6 pokemart): OldaleTown_Mart:9 `goto_if_set FLAG_ADVENTURE_STARTED`; PetalburgCity_Mart:9 `FLAG_PETALBURG_MART_EXPANDED_ITEMS` (set in event_scripts.s:678, reached from 4 gyms when `VAR_PETALBURG_GYM_STATE` == 6, e.g. RustboroCity_Gym:24); RustboroCity_Mart:9-10 `FLAG_MET_DEVON_EMPLOYEE` (set Route116:55); TrainerHill_Entrance:240 `FLAG_SYS_GAME_CLEAR` | two lists per mart with the condition in words |
| bag full -> retry | LilycoveCity:42 `goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull` (flag not set) | "until received", not "once at first visit" |
| purchases that look like gifts | 13 `additem` lines (MEASURED); MauvilleCity_GameCorner:296 `additem ITEM_TM_DOUBLE_TEAM` (coins), LilycoveCity_DepartmentStoreRooftop:139 `additem VAR_TEMP_0` (vending) | "bought for coins/money", not a gift |
| not in solo vanilla play | data/mystery_gift.s:23 `.include "data/scripts/gift_aurora_ticket.inc"` (also Mystic Ticket, Old Sea Map, Pichu egg, battle card); cable_club.inc:22-33 Eon Ticket via `ShouldDistributeEonTicket` (record mixing) | omit, or mark "event distribution only" |
| berries (a whole item source not in any per-map script) | 88 `OBJ_EVENT_GFX_BERRY_TREE` objects (MEASURED); initial berries from data/scripts/new_game.inc:3 `setberrytree BERRY_TREE_ROUTE_102_ORAN, ...` (80 lines, census), regrowing on the clock | "berry tree <id>: starts with X; regrows" |

## 2. Reachability: how a per-map parser misattributes

MEASURED (reach.py over map scripts + data/scripts + event_scripts.s; reference = the label name appearing in any other
script, map.json, src/*.c or include/*.h): 739 labels hold a gift or a setflag; 348 referenced from their own map's
script, 129 from their own map.json, **173 from ANOTHER map's map.json** (162 item balls in item_ball_scripts.inc + 11
others, e.g. data/scripts/interview.inc:46 `SlateportCity_OceanicMuseum_1F_EventScript_Reporter`), **65 only from shared
files**, **7 from another map's script**, **6 only from C**, **9 from nowhere**.

- **Never reached (dead code) -> phantom items/flags** (READ):
  - data/scripts/item_ball_scripts.inc:529-530 `AquaHideout_B2F_EventScript_ItemMasterBall::` / `finditem ITEM_MASTER_BALL      // Unused`; :537-538 `Route119_EventScript_ItemMaxElixir`; :541-542 `Route119_EventScript_ItemNestBall` -- no map.json object names them (MEASURED, balls.py "labels unused"). 165 finditem labels, 162 placed.
  - MossdeepCity_StevensHouse/scripts.inc:139-142 `@ Unused, leftover from RS` / `MossdeepCity_StevensHouse_EventScript_DiveItemBall::` / `finditem ITEM_HM_DIVE` / `setflag FLAG_RECEIVED_HM_DIVE` (the real gift is :36 `giveitem ITEM_HM_DIVE`).
  - MossdeepCity_Gym/scripts.inc:112-116 `@ All the below switch scripts are leftover from RS and are functionally unused` / `MossdeepCity_Gym_EventScript_Switch1::` ... `setflag FLAG_MOSSDEEP_GYM_SWITCH_1` (Switch1-4). An events.json listing these would describe a Mossdeep gym mechanic that Emerald does not have (cf. KI-58).
  - players_house.inc:454-456 `@ Never called.` / `PlayersHouse_1F_EventScript_AirLatiBroadcast::` / `setflag FLAG_SYS_TV_LATIAS_LATIOS`.
  - LilycoveCity_ContestLobby:337-346 `@ Functionally unused` `..._SetDebug::` `setflag FLAG_HIDE_LILYCOVE_MUSEUM_CURATOR` ... `additem ITEM_CONTEST_PASS`.
  - 235 `@ ... unused` comment lines in script files (MEASURED, `grep -rn -i "@.*unused" ... | wc -l`); comments are the only marker -- a parser must test REFERENCE, not trust labels.
- **Placed by map.json, defined elsewhere**: every item ball (script label in the shared file; item from the label, flag from the OBJECT's `flag` field, map/x/y from the object). Parsing `finditem` lines per map yields 1 item (the dead Steven's-house one) and 165 unattributed.
- **ITEM_BALL graphic that is NOT an item** (MEASURED, balls.py: 60 objects): AquaHideout_B1F obj 6/8 `AquaHideout_B1F_EventScript_Electrode1` (a wild Electrode), NewMauville_Inside Voltorb1-3, the 6 Birch-lab / rival-house starter balls, MossdeepCity_StevensHouse obj 2 `..._BeldumPokeball`, ContestHall `0x0`, 48 BattlePyramidSquare objects `BattlePyramid_FindItemBall` (random Frontier items, flag `0`). A graphics-based item list calls Electrode an item.
- **Reached through call/goto from other maps** (MEASURED): event_scripts.s:676 `Common_EventScript_ReadyPetalburgGymForBattle` (sets the Petalburg MART flag) called from DewfordTown_Gym:153, LavaridgeTown_Gym_1F:64, MauvilleCity_Gym:96, RustboroCity_Gym:24 (`call_if_eq VAR_PETALBURG_GYM_STATE, 6, ...`): the effect lands on PetalburgCity_Mart, the call sits in whichever gym is 4th. data/scripts/set_gym_trainers.inc:1-9 `switch VAR_0x8008` / `case 1, RustboroCity_Gym_SetGymTrainers` ... dispatched by the caller's `setvar VAR_0x8008, 1` (RustboroCity_Gym:22-23) and using `settrainerflag` (57 lines, census) -- not `setflag`.
- **Reached from C** (MEASURED + READ): src/new_game.c:196 `RunScriptImmediately(EventScript_ResetAllMapFlags);` -> data/scripts/new_game.inc:115 (159 `setflag` lines: the INITIAL hide flags, not events); src/field_control_avatar.c:349-351 hidden items `gSpecialVar_0x8004 = ((u32)bgEvent->bgUnion.script >> 16) + FLAG_HIDDEN_ITEMS_START;` ... `return EventScript_HiddenItemScript;`; src/fldeff_cut.c -> FarawayIsland_Interior:166 `setflag FLAG_HIDE_MEW`; src/field_control_avatar.c -> RustboroCity_Gym:91 `setflag FLAG_ENABLE_ROXANNE_MATCH_CALL`.
- **Flags set with NO setflag line** (READ): item balls -- obtain_item.inc:111-112 `EventScript_PickUpItem::` / `removeobject VAR_LAST_TALKED` (asm/macros/event.inc:1953-1954 "sets the flag of the last-talked to object"); hidden items -- obtain_item.inc:183 `special SetHiddenItemFlag` (src/field_specials.c:935); trainer flags -- src/battle_setup.c:1245-1249 `SetBattledTrainersFlags` `FlagSet(GetTrainerAFlag());`; 45 `FlagSet(FLAG_...)` in src/*.c (MEASURED), e.g. src/mirage_tower.c:334, src/record_mixing.c:978 `FlagSet(FLAG_ENABLE_SHIP_SOUTHERN_ISLAND)`.
- **The same script owned by many maps**: 50 map.json carry `shared_scripts_map` (24 SecretBase, 15 BattlePyramidSquare01, 11 ContestHall) and 11 `shared_events_map` (MEASURED). slice 1 already resolves this (extract_world.py:493-495 `script_owner = j.get("shared_scripts_map") or folder`).
- **Automatic, not interactive**: `map_script` ON_TRANSITION labels set flags on entry, e.g. OldaleTown/scripts.inc:7 `setflag FLAG_VISITED_OLDALE_TOWN`; `clearflag` (217+37 lines) is how most people APPEAR (Route104:24 `clearflag FLAG_HIDE_ROUTE_104_WHITE_HERB_FLORIST`), so a setflag-only events list misses half the story.

## 3. The BUGFIX/UBFIX blocks: none changes an item, gift or flag

READ, all 11 (vanilla keeps `#ifndef` / `#else`):
- BattleTowerLobby:407-409 `tower_save 0`, :416-418 `incrementgamestat GAME_STAT_ENTERED_BATTLE_TOWER` -- save/stat only.
- ContestLobby:340-344 and LilycoveMuseum_2F:75-79 -- vanilla `copyvar VAR_LILYCOVE_MUSEUM_2F_STATE, 1, warn=FALSE` vs fix `setvar ..., 1`. A VAR, not a flag. The adjacent `setflag FLAG_HIDE_LILYCOVE_MUSEUM_CURATOR` / `additem ITEM_CONTEST_PASS` (ContestLobby:339, :345) are OUTSIDE the block and in a "Functionally unused" label.
- SkyPillar_2F:9-13, SkyPillar_4F:9-13, cave_hole.inc:6-10 -- same copyvar/setvar on `VAR_ICE_STEP_COUNT`.
- SpaceCenter_1F:217-221 a `case DIR_EAST/DIR_WEST` movement branch; SpaceCenter_2F:295-297 `releaseall`; safari_zone.inc:55-57 `releaseall`; trainer_hill.inc:16-18 `end`.
- Caveat for VAR records (INFERRED from READ): vanilla `copyvar X, 1` executes src/scrcmd.c:371 `*ptr = *GetVarPointer(ScriptReadHalfword(ctx));` and src/event_data.c:166-167 returns NULL for id < VARS_START, so the vanilla value is a read through a NULL pointer, NOT 1. The value actually stored is UNKNOWN. An events.json that records "VAR_LILYCOVE_MUSEUM_2F_STATE = 1" took the UBFIX side.

## 4. Flags: the RULING 40 boundary and phantom names

- **What tempts live reads** (INFERRED): every record that pairs a thing with its flag -- `item_balls[].flag`, `hidden_items[].flag` (already in maps.json, extract_world.py:511/515), a gift's "received" flag, a condition "requires FLAG_X". The obvious code is `if not flag(rec["flag"]): go get it`, which reads live hidden state (and for hidden items, whether an INVISIBLE item is still there). Rule A cannot see it: check_fairness.py:37 "LIMITS. Static analysis cannot follow a value"; a flag name only fails when a string literal's WHOLE value is the name (check_fairness.py:90 `_FLAG_NAME`, :365).
- **The classification hazard** (MEASURED + READ): today `developer_keys()` = `['decomp', 'flag', 'measured', 'note', 'taught_by']` (MEASURED: `py -3.12 -c "import check_fairness as c; print(sorted(c.developer_keys()))"`). Its rule is check_fairness.py:229-240 `return developer - elsewhere`: a key name stays refused only while NO file classifies it AI. **If items_gifts.json or events.json classifies any `...flag` path as `ai`, the key `flag` leaves the set and B2 stops refusing `x["flag"]` EVERYWHERE**, including milestones.json `trainers.*.flag` (DEVELOPER). The `KNOWLEDGE_FIELDS` step must mark every flag/var path `developer` (or `hidden`, carried only by a declared loader), and the condition text the AI reads must be words ("after badge 3", "once a day"), not a flag name. Currently classified files: milestones, moves, species, types, wild_species (MEASURED).
- **Phantom-flag check** (MEASURED, flags.py): flag names in script flag commands (map + shared + event_scripts.s): **713 distinct, 8 not in emerald.txt**; map.json `flag` fields: **593 distinct, 2 not in emerald.txt**; 0 of either undefined in include/constants/flags.h. The 9 distinct names are not phantoms but table gaps:
  - 4 SPECIAL flags (not save flags): flags.h:1645-1649 `FLAG_HIDE_MAP_NAME_POPUP (SPECIAL_FLAGS_START + 0x0)`, `FLAG_DONT_TRANSITION_MUSIC`, `FLAG_ENABLE_MULTI_CORRIDOR_DOOR`, `FLAG_STORING_ITEMS_IN_PYRAMID_BAG`;
  - 4 TEMP aliases: flags.h:1655-1658 `FLAG_TEMP_SKIP_GABBY_INTERVIEW FLAG_TEMP_1`, `..._REGICE_PUZZLE_STARTED FLAG_TEMP_2`, `..._REGICE_PUZZLE_FAILED FLAG_TEMP_3`, `FLAG_TEMP_HIDE_MIRAGE_ISLAND_BERRY_TREE FLAG_TEMP_11` (the table has `TEMP_1` etc.; temp flags reset on map load);
  - 1 SPELLING: flags.h:922 `FLAG_HIDE_FALLARBOR_POKEMON_CENTER_LANETTE 0x367` vs emerald.txt `871 HIDE_FALLORBOR_POKEMON_CENTER_LANETTE` (same id 0x367 = 871; the TABLE is misspelled).
  - Also: emerald.txt has 1164 rows; 80 of its names are not #defined in flags.h (e.g. `REMATCH_*`, `MATCH_CALL_REGISTERED`), and 461 flags.h #defines are not in it (MEASURED).
  - Vars (not asked, cheap): 172 distinct VAR names in var commands, 23 not in event_vars/emerald.txt: 16 special 0x80xx vars + 7 `VAR_TEMP_*` aliases (MEASURED, vars.py).
- Consequence: spec line 424-425 "limited to flags that exist in emerald.txt" would silently DROP real decomp flags (the Lanette one is a real save flag). The filter must key on flags.h (the decomp) with an alias table; `audit_flag_names.py` reads names WITHOUT the `FLAG_` prefix (tools/story-dev/audit_flag_names.py:12-16 `flags.add(parts[1])`), so it must strip the prefix and alias TEMP names before it can run on decomp output.

## 5. The independent verifier (re-derive from raw decomp, no shared code)

What a second reader can re-derive (INFERRED design input, each from a DIFFERENT source than the obvious extractor path):
- field items: from map.json `object_events` whose `script` label's FIRST command (in ANY script file) is `finditem` -> (map, x, y, item, flag). Expected counts (MEASURED): 162 placed, 3 library labels unplaced, 0 labels placed twice, 0 placed objects without a flag, 0 duplicate flags.
- hidden items: map.json `bg_events` `type: hidden_item` -> 112 (MEASURED).
- givemon/giveegg: 7 + 2 lines (MEASURED, gifts.py; Pichu egg is mystery-gift only); the first starter is NOT a givemon: Route101/scripts.inc:223 `special ChooseStarter`.
- giveitem: 160 lines in map+shared files (145 + 15, census; 0 in event_scripts.s), 15 with a VAR argument; givedecoration 13; marts 27 `pokemart` + 5 + 5 decoration marts (census).
- events: setflag/clearflag/setvar per LABEL, attributed by REFERENCE (who calls the label), including event_scripts.s.
Fault arms: (e) one field item moved to another map -- caught by comparing (map, x, y, item) tuples; (f) one setflag dropped -- caught by per-label command lists.
**Faults a naive verifier would MISS** (the measured shapes above):
- **(g) a dead label promoted to a real item**: plant `AquaHideout_B2F_EventScript_ItemMasterBall` (or Steven's `DiveItemBall`) into the output. A verifier that recounts `finditem` lines (166) AGREES with an extractor that emits every finditem line -- both share the misconception. Only a verifier that derives placement from map.json (162) catches it. This is the "agreement is not a confidence signal" failure in its purest form.
- (h) a condition stripped: drop the exclusivity of Root/Claw fossil, or the "daily"/"random" qualifier of the Lilycove berry. Every line still exists, every count matches; only the record's meaning is false. The verifier must re-derive the qualifier itself (FLAG_DAILY_* gate, `random`, VAR argument, exclusive `setflag FLAG_HIDE_*` of the sibling).
- (i) an item moved WITHIN its map (other x,y): (e) only moves it across maps; a per-map multiset verifier misses it.
- (j) an ITEM_BALL-graphic object (Electrode) reported as an item: a verifier filtering by graphics_id makes the same mistake.

## 6. Where the decomp contradicts the spec block (2026-10-19-BUILD-SPECS-step-3.md)

- Spec :424 "`events.json`: per map, the `setflag`/`setvar`/`goto_if_set`/`trainerbattle`/`special` lines" -- most persistent flags are set with NO setflag line (obtain_item.inc:112 `removeobject VAR_LAST_TALKED`; :183 `special SetHiddenItemFlag`; battle_setup.c:1249 `FlagSet(GetTrainerAFlag());`; set_gym_trainers.inc `settrainerflag`); 27 setflag lines live in data/event_scripts.s, outside every per-map file; and "per map" is wrong for 65 shared-only + 7 cross-map + 6 C-reached labels (section 2).
- Spec :424-425 "limited to flags that exist in `sandbox-pokebot/modules/data/event_flags/emerald.txt`" -- that filter removes 9 real decomp names (section 4), one of them a real save flag misspelled in the TABLE.
- Spec :417-418 fault arm "(f) one `setflag` dropped from a script" -- the item flags (162 placed item balls, each with its object `flag`, + 112 hidden items, MEASURED) have no setflag line to drop, so (f) cannot exercise the most numerous flag kind.
- Spec :421 "field items (object script -> `finditem`)" -- TRUE as written, but 3 of 165 finditem labels have no object (section 2) and slice 1 already ships the result (E3).
- Spec :422 "Route104 alone has 3 such lines" -- TRUE for data/maps/Route104/scripts.inc (:253 `giveitem ITEM_CHESTO_BERRY`, :270 `giveitem ITEM_WHITE_HERB`, :322 `giveitem ITEM_TM_BULLET_SEED`); Route104_PrettyPetalFlowerShop adds :72 `giveitem ITEM_WAILMER_PAIL` and :86 `giveitem VAR_RESULT`.
- Census/spec claim of "12" blocks -- 11 (E1).
