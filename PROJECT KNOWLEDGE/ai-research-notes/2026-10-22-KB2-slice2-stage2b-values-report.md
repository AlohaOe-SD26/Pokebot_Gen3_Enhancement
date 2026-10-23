# KB2 slice 2 STAGE 2b, BUILDER A (the values): report, 2026-10-22

## Verdict
events.json is BUILT at the pin (731ad5bf) and checked: `extract_events.py --check` OK, `extract_items.py --check` OK
(items_gifts.json untouched; extract_items.py NOT edited), `verify_world.py` 0 mismatches, `--selftest` PASS with all 26
stage-2a plants and 20 new stage-2b plants each on exactly one line, and a 20-mutant verifier RULE-DELETION diagonal
with every mutant caught by its own plant(s) only. Nothing committed. test_kb2.py NOT edited: ONE of its tests is now
red BY DESIGN (see "Known red"). Chapter packs not regenerated; run_gates not run (builder B).

## Files changed (working tree, uncommitted)
- `ai_player/gates/extract_events.py` (NEW, 842 lines). The scratch dir work-build2b-A/ (diag.py, guards.py,
  counts.py, mutant copies) is DELETED; work-fix2/ is not mine and was left alone. Imports extract_items as `ei` and REUSES, never copies:
  `script_files, check_sources, parse_labels, build_edges, read_maps, map_roots, check_map_scripts, c_roots, Graph`
  (incl. `Graph.paths_to`, the path walk), `closure, cmd, ref, cond_text, common_tests, known_paths, as_num,
  vanilla_lines, name_ids, NEVER_CONTINUES, EXCLUDED_LABELS, refuse_dev_keys, check_dev_names, defined_names,
  check_maps_json`.
- `ai_player/knowledge/world/events.json` (generated, 2.78 MB).
- `ai_player/gates/verify_world.py` (stage-2b section after `s2_plant_result`; selftest + main wiring; usage line; and
  ONE fix in the stage-2a shared reader `s2_strip`: a one-line `/* ... */` comment is now dropped. Before it,
  `data/scripts/cable_club.inc:687 /* Never used */` was the LAST line of `EventScript_TradeCenter_Chair1`, so the
  verifier made Chair1 "fall" into the dead Chair2 (and :693 into Chair3): measured CONTROL before the fix = 3 lines
  (Chair2, Chair3 "no record", dead split). After: 0, and the 2a CONTROL and all 26 2a plants unchanged.)

## Commands and summary lines (each after the last source edit)
- `py -3.12 ai_player/gates/extract_events.py` -> `[KB2-EVENTS] wrote ...events.json: labels 2278, changes 3773
  (conditional 1393), gates 32 (worded 20), dead 54, excluded groups 7` (50.5 s; ~47 s of it is entry_tests'
  paths_to over 2278 labels, see risks)
- `py -3.12 ai_player/gates/extract_events.py --check` -> `[KB2-EVENTS] CHECK OK: events.json identical to a fresh
  extraction` (50.8 s). A determinism check, not a replication.
- `py -3.12 ai_player/gates/extract_items.py --check` -> `[KB2-ITEMS] CHECK OK: items_gifts.json identical to a fresh
  extraction` (8.9 s)
- `py -3.12 ai_player/gates/verify_world.py` -> `[VERIFY-WORLD] PASS: 0 mismatches (every record; checked {'bosses': 57,
  'campaign': 66, 'citations': 2042, 'events_dead': 54, 'events_gates': 32, 'events_labels': 2278, 'field_moves': 8,
  'items': 274, 'items_dead': 5, 'items_eon_excluded': 1, 'items_gift_lines': 176, 'items_golden': 40,
  'items_mart_lists': 37, 'map_battles': 543, 'maps': 518, 'trainers': 855}; W1 scanned 15 knowledge files)` (4.6 s)
- `py -3.12 ai_player/gates/verify_world.py --selftest` -> 54 `[PASS]` lines, 0 FAIL, last line
  `[VERIFY-WORLD] SELFTEST PASS` (14.7 s). Includes `[PASS] EV CONTROL: events.json, 0 mismatches ({'events_labels':
  2278, 'events_dead': 54, 'events_gates': 32})` and 20 `[PASS] EV FAULT (...)`.
- `py -3.12 ai_player/gates/verify_world.py --plant f` -> `[VERIFY-WORLD] PLANT f PASS: MISMATCH events label
  RustboroCity_Gym_EventScript_RoxanneDefeated: reported (1 lines)`
- `py -3.12 -m pyflakes extract_events.py verify_world.py` -> no output, exit 0.
- `check_fairness.developer_keys()` -> `['decomp', 'flag', 'measured', 'note', 'taught_by']` (T-FAIR holds).
- `py -3.12 ai_player/gates/test_kb2.py` -> `Ran 89 tests in 86.360s` / `FAILED (failures=1)`: see Known red.

## Known red (for builder B)
`test_kb2.W1WithheldTests.test_scan_every_knowledge_file` (test_kb2.py:217) pins the world/ file list to
`ew.OUTPUTS + (ei.OUT_NAME,)`; events.json is a new world file. Fix in test_kb2: add `xe.OUT_NAME` (extract_events).

## Counts (re-measured; recon numbers are notes)
Plain grep of the three homes + the mystery-gift files (scratch counts.py, deleted):
| cmd | map scripts | shared (no gift files) | event_scripts.s | mystery gift | recon said |
|---|---|---|---|---|---|
| setflag | 606 | 248 | 27 | 8 | 606 / 256 (incl. gift) / 27: AGREES |
| clearflag | 217 | 37 | 15 | 0 | 217 + 37 (event_scripts.s not counted by the recon) |
| setvar | 1521 | 324 | 10 | 1 | 1521 / 325 (incl. gift) / 10: AGREES |
| addvar | 81 | 23 | 0 | 1 | 81 + 24 (incl. gift): AGREES |
| subvar | 11 | 1 | 0 | 1 | 11 (map): AGREES |
| cleartrainerflag | 3 | 1 | 0 | 0 | recon "3": it counted map scripts only; 4 in all |
| settrainerflag | 0 | 57 | 0 | 0 | 57: AGREES |
| warp / warpsilent / warpdoor | 116+5 / 8+5 / 2 | | | | 121 / 13 / 2: AGREES |
| trainerbattle* | 639 | 13 | 0 | 0 | (not given) |
| copyvar 108+55+1, special 690+375+5, specialvar 241+100 | | | | | (not given) |
Recon Q6's BUGFIX count: 11 blocks (spec R-3): not re-counted here (vanilla_lines is 2a's, unchanged).
W7 "13 events facts": the spec's own list "rows 1, 4-12, 14, 15" is TWELVE rows. I also made row 3 (ChooseStarter)
findable: 13 with it. Reported, not resolved.

events.json:
- labels 2278 (reachable, >= 1 kept change); 96 of them reached only from C (`reached_from: "C"`, `c_ref`).
- changes 3773: special 1390, setflag 806, trainerbattle 652, setvar 436, clearflag 237, warp 140, settrainerflag 57,
  copyvar 24, addvar 20, subvar 7, cleartrainerflag 4. Conditional 1393 (special 727, setflag 298, setvar 141,
  clearflag 109, warp 81, trainerbattle 14, copyvar 10, subvar 7, addvar 6).
- trigger kinds: called 2239, talk 886, map_script 355, battle 97, C 65, sign 54, coord 52.
- excluded (7 groups): special vars 1107 lines (setvar 919, copyvar 121, addvar 52, setorcopyvar 10, subvar 5); temp
  vars 518 (setvar 469, addvar 32, copyvar 17); temp flags 44 (setflag 42, clearflag 2); special flags 39 (clearflag
  21, setflag 18); not a save flag 1 (`setflag VAR_0x8005`, secret_base.inc:276, the UB the file's own comment names);
  mystery gift 19 op lines (8 files); Eon Ticket 1 label (CableClub_EventScript_DistributeEonTicket).
- dead: 54 labels (0 op lines after a stop in a live label). Includes the Mossdeep Gym switches (8 + DrawMap), Steven's
  DiveItemBall, Trick House Puzzle 7 switches (15), Cave of Origin shakes (5), ContestLobby SetDebug (pruned branch),
  Players House AirLatiBroadcast, TradeCenter Chair2/3, the unused Route 111 sandstorm triggers (Up, Right).
- gates 32: steer 16, locked 16; worded 20, `when: null` 12.

## The hand tables (all cites checked by check_cites at build; gate cites re-checked by the verifier at verify time)
GATE_WORDS (keyed by label; 20 entries, every one a candidate, check_gate_table):
| label(s) | words (short) | cites |
|---|---|---|
| OldaleTown_EventScript_BlockedPath | west exit blocked by the footprints man until Birch gives you the Pokedex | OldaleTown/map.json:125 `"var": "VAR_OLDALE_TOWN_STATE"`, :126 `"var_value": "0"`; LittlerootTown_ProfessorBirchsLab/scripts.inc:501 `call ..._ReceivePokedex`, :511 `setvar VAR_OLDALE_TOWN_STATE, 1`; OldaleTown/scripts.inc:15 `setvar VAR_OLDALE_TOWN_STATE, 1` |
| PetalburgCity_EventScript_ShowGymToPlayer0..3 | until you visit your father and agree to go with Wally, the boy walks you to the Gym | PetalburgCity/map.json:201/:210/:219/:228 `"var": "VAR_PETALBURG_CITY_STATE"`; PetalburgCity_Gym/scripts.inc:183 `setvar VAR_PETALBURG_CITY_STATE, 2` |
| Route101_EventScript_PreventExitSouth/West/North | cannot leave Route 101 while Birch is chased, until you pick from his bag | Route101/scripts.inc:39 `setvar VAR_ROUTE101_STATE, 2`, :223 `special ChooseStarter`, :231 `setvar VAR_ROUTE101_STATE, 3`; Route101/map.json:134/:152/:188 `"var": "VAR_ROUTE101_STATE"` |
| PetalburgCity_Gym_EventScript_SpeedRoomDoor / AccuracyRoomDoor | locked until the first four badges (Rustboro, Dewford, Mauville, Lavaridge each count one, after the first talk with your father) | PetalburgCity_Gym/scripts.inc:716 / :744 `goto_if_lt VAR_PETALBURG_GYM_STATE, 6,`; :90 `setvar VAR_PETALBURG_GYM_STATE, 2`; RustboroCity_Gym:21, DewfordTown_Gym:152, MauvilleCity_Gym:95, LavaridgeTown_Gym_1F:63 `addvar VAR_PETALBURG_GYM_STATE, 1` |
| the 10 trainer doors (Confusion, L/R Defense, Recovery, L/R Strength, L/R OHKO, L/R Gym Leader's) | locked until you beat Randall / Randall / Mary / Mary / Parker / Alexia / Alexia / George / Jody / Berke | PetalburgCity_Gym/scripts.inc:754/764/774/784/794/804/814/824/834/844 `goto_if_not_defeated TRAINER_X,`; :737 `msgbox PetalburgCity_Gym_Text_DoorAppearsLocked` |
EFFECT_WORDS (op-keyed; filled from a JOIN, never a flag name): settrainerflag "{name} now counts as beaten"
(src/scrcmd.c:1858 `SetTrainerFlag(index);`), cleartrainerflag "{name} no longer counts as beaten" (:1866
`ClearTrainerFlag(index);`), warp "you are moved to {map}" with WARP_CMDS: warp :748, warpsilent :762, warpdoor :776,
warpteleport :808, warpmossdeepgym :822, warpspinenter :2250, warpwhitefade :2304 (each `SetWarpDestination(mapGroup,
mapNum, warpId, x, y);`); warphole uncited (MAP_UNDEFINED -> setholewarp's map): no words.
PERSIST_RANGES: temp flags flags.h:11, :43 + overworld.c:798; special flags flags.h:1644, :1651; temp vars vars.h:8,
:25; special vars vars.h:280, :306 + event_data.c:171. FLAGS_COUNT flags.h:1641. COPYVAR_BUG scrcmd.c:371,
event_data.c:166, :167. PLACEHOLDER_BATTLES battle_setup.h:13 (PYRAMID), :16 (HILL).
SAFE (whitelist, uncited by design: a command off it makes a change CONDITIONAL, never certain): listed in the file.

## The unknown / null list
- `when: null` gates (12, in `_gates_when_null`): LilycoveCity_CoveLilyMotel_1F BlockingTV; Littleroot Brendan's/May's
  house GoSeeRoom; Littleroot NeedPokemonTriggerLeft/Right; Route110_TrickHouseEnd TrickMasterExitTrigger; Route111
  ViciousSandstormTriggerDown/Left (VAR_TEMP_3: needs the on-transition reading); BattleTowerMultiPartnerRoom
  TalkToPotentialPartner; CableClub DirectCornerAttendant / UnionRoomAttendant; LilycoveCity_Harbor FerryAttendant
  (FLAG_SYS_GAME_CLEAR has no script setflag at the pin; not worded).
- `effect: null`: every setflag/clearflag/setvar/addvar/subvar/copyvar/special/trainerbattle change (by rule); 2 warps
  (warphole: MAP_SOOTOPOLIS_CITY_GYM_B1F and MAP_UNDEFINED).
- copyvar values "unknown (vanilla copyvar bug, scrcmd.c:371)": 4 (LilycoveMuseum_2F :78, SkyPillar_2F :12, SkyPillar_4F
  :12, cave_hole.inc :9).
- trainerbattle `trainer: null` 2 (BattlePyramid_TrainerBattle, TrainerHill_EventScript_TrainerBattle: placeholder).
- conditional: 1393 changes (dev.after lists the lines).
- label dev.tests: 96 labels have 0 known paths (C-only), 54 have collapsed paths (> MAX_PATHS).

## W7 acceptance (map, label) for builder B's test
1 MAP_ROUTE103 Route103_EventScript_RivalEnd (:131 setvar VAR_BIRCH_LAB_STATE 4, :133 setflag
FLAG_DEFEATED_RIVAL_ROUTE103, :134 setvar VAR_OLDALE_RIVAL_STATE 1). 3 MAP_ROUTE101 Route101_EventScript_BirchsBag
(:223 special ChooseStarter). 4 gate OldaleTown_EventScript_BlockedPath (MAP_OLDALE_TOWN, worded) + label
OldaleTown_OnTransition + MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB ..._EventScript_GivePokedex (:510 setflag
FLAG_ADVENTURE_STARTED, :511 setvar). 5 same map ..._EventScript_ReceivePokedex (:537 setflag FLAG_SYS_POKEDEX_GET).
6 gates PetalburgCity_Gym_EventScript_SpeedRoomDoor / AccuracyRoomDoor (MAP_PETALBURG_CITY_GYM, worded) +
RustboroCity_Gym_EventScript_RoxanneDefeated addvar :21. 7 MAP_PETALBURG_CITY PetalburgCity_EventScript_WallyTutorial
warp :52 (map MAP_PETALBURG_CITY_GYM). 8 same label special StartWallyTutorialBattle :40. 9 gates
PetalburgCity_EventScript_ShowGymToPlayer0..3 (MAP_PETALBURG_CITY, worded). 10 MAP_PETALBURG_WOODS
PetalburgWoods_EventScript_DevonResearcherLeft/Right (coord trigger; trainerbattle :23/:51) +
..._RemoveDevonResearcher (:92 setvar). 11 MAP_ROUTE104 Route104_EventScript_BattleMay{Treecko,Torchic,Mudkip} /
BattleBrendan* and MAP_RUSTBORO_CITY RustboroCity_EventScript_BattleMay* / BattleBrendan*: trainerbattle, dev.tests holds
`VAR_RESULT eq YES (answer)` (the YES/NO is two labels up). 12 MAP_RUSTBORO_CITY_DEVON_CORP_3F
RustboroCity_DevonCorp_3F_EventScript_MeetPresident (:68) + MAP_RUSTBORO_CITY RustboroCity_EventScript_ScientistAddMatchCall
(:33), _MatchCallTutorial (:88). 14 MAP_RUSTBORO_CITY_GYM RustboroCity_Gym_SetGymTrainers (settrainerflag :14-16).
15 RustboroCity_Gym_EventScript_RoxanneDefeated (:18 setflag, :20 setvar, :21 addvar).

## Verifier rules, plants, and the rule-deletion diagonal (scratch copies; CONTROL = the real output)
20 mutants, each one rule's `if` made False / loop emptied (diag.py, 2m32s): every one CONTROL 0 and red ONLY on its own
plant(s): ev_member_extra b2; ev_member_missing b2m; ev_ops f; ev_maps b1+b1c; ev_maps_conly b1c; ev_cond_certain
b3+b3c; ev_cond_callee b3c; ev_cond_after b3a; ev_r3 b8; ev_trig b4; ev_effect_op b10; ev_effect_warp b10w;
ev_effect_trainer b10t; ev_dead b7; ev_gw_null b5n; ev_gw_nocite b5; ev_gw_cite b5c; ev_gatecands b6; ev_r4 k2;
ev_r6 b9. All CAUGHT. Two SURVIVED the first run and were strengthened: ev_effect_op (b10 was ALSO caught by the trainer
branch, which ran for every op: the trainer check now runs only on settrainerflag/cleartrainerflag) and ev_cond_callee
(no plant: added b3c, Oldale's setflag after `call Common_EventScript_SetupRivalGfxId`, whose callee can `end`).

## Extractor guards: FAULT / CONTROL / call-deleting mutant (scratch guards.py, 46 s; entry_tests stubbed for speed)
CONTROL build PASS. FAULTs REFUSED: cites (a GATE_WORDS line +1), gatetable (a label no candidate), joins
(TRAINER_ROXANNE_1 removed from names), r4 (a bare `flag` key), r5 (an undefined dev flag), r6 (an `x` key), door
(write_output given an R-4 object). Mutants deleting the CALL: del_check_cites, del_check_gate_table, del_check_joins,
del_refuse_all_build (r4, r5, r6), del_refuse_all_door: each FAULT arm then PASSES = CAUGHT by that arm. Not armed:
check_gate_table's ">1 candidate" clause, R-7 (withheld; it is ew.refuse_withheld, slice 1's).

## Deviations from the spec
1. `copyvar` is an op (the spec's list omits it; R-3 names its value rule, and leaving a saved-var write out would
   understate the label). `setorcopyvar` -> setvar/copyvar by its source.
2. `specialvar` is listed as op `special` (dev.cmd says which). Getters are listed too: a special's effect is never read.
3. NOT listed (said in `_notes.changes`): removeobject, give/take, money, coins, set*warp, setrespawn, frontier/contest
   macros, a special's own C writes. A label's `changes` is not everything it does.
4. Special (not saved) flags and the past-FLAGS_COUNT `setflag VAR_0x8005` are dropped too (persistent only).
5. Label-level `dev` (tests on every known path, via 2a's paths_to): added so a 2-levels-up yes/no (W7 row 11) is shown.
6. Gate candidates: two re-checkable patterns only (steer, locked); a person moved INTO a way on transition
   (Oldale's BlockWestEntrance setobjectxyperm) is NOT a candidate.

## Open risks
- extract_events takes ~50 s (entry_tests). Builder B's mutant run will be slow; stub entry_tests where not tested.
- The verifier's ev_candidates and the extractor's gate_candidates agree at the pin (CONTROL 0) but read closures
  differently (mentions vs control edges); a decomp change could split them.
- SAFE is a hand whitelist without cites; a wrong member would make a change wrongly certain. The verifier's blacklist
  (EV_DIVERT/EV_STOPS) is the independent check; they agree on all 2380 certain changes.
- dead: "unverified: may be reached from C" is never emitted (any C mention makes a label a root, as in 2a).

## For builder B: the new calls and branches to mutate (call-deleting / branch mutants)
extract_events.py: build(): ei.check_sources, check_cites, ei.check_map_scripts, check_joins, check_gate_table,
gate_candidates, set_aliases (ctx), the eon `excluded_closure` branch, the `not g.reachable` dead branch and its pruned
`via` branch, the live_body dead-lines loop, the `if drop` excluded branch, `rec["conditional"] = bool(after)` /
dev.after, the diverts() call, the `if not idx` reached_from-C branch, the entry_tests call, the gift-file count loop
(`code.strip()`); build_all/write_output refuse_all (2 calls). change_of: trainer_of + PLACEHOLDER_BATTLES branch, each
alias.get (flag target, var target, copy source), p.dropped (flag, var), setorcopyvar branch, copyvar VAR-source vs
literal (COPYVAR_BUG, `n < VARS_START`), settrainerflag name-None -> null, specialvar persistent dest dev.vars, warp
wid `len(rest) in (1, 3)`, `WARP_CMDS.get(mn)` null words, mapname None. Persist.dropped: each range, FLAGS_COUNT
branch. safe_line / SAFE_PREFIX; callee_returns (Refused -> False, CALLEE_FLOW, the goto_if/call_if regex); diverts
call/call_if branch; live_body stop. triggers_of: object hide-flag dev, coord VAR_ regex, sign, ms_lines map_script,
ms_tables loop, battle, called cond flags/vars, C. mapscript_types (per-line key). entry_tests. gate_candidates: steer
conditions (player_moves, writes, warp, story), locked (persistent_test, target profile warp/writes/story/end, `on`
body + CTRL edges); persistent_test (trainer branch, regex, dropped); profile counters. check_gate_table (both
clauses). gate_records (GATE_WORDS lookup, null list). table_cites rows (GATE_WORDS, EFFECT_WORDS, WARP_CMDS None skip,
PERSIST_RANGES, FLAGS_COUNT, COPYVAR, PLACEHOLDER). main --check compare.
verify_world.py: s2_strip `/* */` removal; ev_eval (`/` -> `//`, token check); ev_ids (rematches enum, opponents.h);
ev_saved (each range, FLAGS_COUNT); ev_live; ev_op (each branch, PYRAMID/HILL, aliases, setorcopyvar); ev_raw
(after_eon/eon, mapkinds type filters, dead vs want, dead_lines); ev_fwd; ev_callee_stops; ev_reached; ev_kinds
(map_script / map_script_2 / battle / called, reached filter, C); ev_out_ops; ev_candidates (prof filters, steer,
locked regex `(?:.*,)?`, later warp); the 20 rule sites above (already diagonal-tested here; test_kb2 should pin them);
selftest EV wiring; main `--plant` routing and `load_events`.
