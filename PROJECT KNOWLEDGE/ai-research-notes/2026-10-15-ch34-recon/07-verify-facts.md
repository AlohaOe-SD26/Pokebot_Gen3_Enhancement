# 07 — ADVERSARIAL VERIFIER: the decomp facts in 00-RECON-NOTE §1-§5 and §9

> **NOTE: not truth.** Written 2026-10-15 by a read-only Claude verifier whose brief was to FIND ERRORS in
> `00-RECON-NOTE.md`, not to agree with it. It re-read every load-bearing claim against pret/pokeemerald itself.
> Nothing was run in an emulator, and nothing outside this file was written (the scratch scripts live in the session
> scratchpad and are not kept).
>
> **Verdicts:**
> - **CONFIRMED**: I read the fact myself in the decomp, or in our tree for the few code claims. My own citation is given.
> - **CONFIRMED-MODEL**: I re-derived it with an INDEPENDENT static walk model (see §A). That is still a MODEL and is
>   not proof. A shared input (`map.bin`) means agreement with [01]/[05] is NOT a confidence signal.
> - **REFUTED**: the citation does not say what the note says. The correct fact and its citation are given.
> - **REFUTED-MODEL**: my independent model contradicts a reachability claim. A live probe should settle it.
> - **UNVERIFIABLE**: no decomp read can settle it (bot data, behaviour, our runtime).
>
> ⛔ **PERSON-FAIR (USER RULINGS 35-37).** Every coordinate, flag, var, route, choke and sight line below is for the
> DEVELOPERS (proof design, fixtures, expectations). None of it may reach the AI player as a hint. Dialogue quotes are
> listed only to check that the note quotes the game correctly. The AI may meet them only by reading them on screen.

---

## 0. Verdict summary (read this first)

**Totals.** About 190 individual claims were checked:
- about 155 CONFIRMED;
- about 20 CONFIRMED-MODEL;
- 3 REFUTED;
- 2 REFUTED-MODEL;
- 4 §9 proof-design defects (not REFUTED as facts, but they would make a proof wrong);
- 3 citation slips (substance right);
- 5 UNVERIFIABLE by decomp.

### 0a. REFUTED (fix the note)

| # | Note says | Fact | My citation |
|---|---|---|---|
| R1 | §2: "The tunnel sign [30,8] (`:1123`) and the RUSTURF TUNNEL sign (`Route116/scripts.inc:442`): 'The tunnel project has been canceled.'" | The **Rustboro** sign says something else: *"“Timesaving tunnel nearing completion!” …Is what it says on the sign, but there's also a big “X” splashed across it in red paint…"*. Only the Route 116 sign says "canceled". | `RustboroCity/scripts.inc:1123-1128` (shown by `RustboroCity_EventScript_TunnelSign`, `:179-181`, at bg (30,8)); `Route116/scripts.inc:442-446` |
| R2 | §2: "**A man** in the Pokémon Center (`:43`): 'The man next door gave me an HM!'" | The quote is right, but the speaker is the **GIRL**. | `RustboroCity_PokemonCenter_1F/scripts.inc:27-29` (`…_EventScript_Girl` → `…_Text_HMCutNextDoor`) |
| R3 | §1 beat 6: "Before this, a whiteout returns the player to PETALBURG" | A whiteout returns the player to the last `setrespawn`. That is Petalburg only if the AI entered PETALBURG's Pokémon Center 1F. Otherwise it is Oldale, or the Littleroot home respawn. The claim is conditional on the run's history and is wrong as an unconditional fact. | `battle_setup.c:1333-1338` (`CB2_WhiteOut`); `RustboroCity_PokemonCenter_1F/scripts.inc:7` shows the `setrespawn` pattern |

### 0b. REFUTED-MODEL (my independent model disagrees; settle by a live probe before a proof leans on it)

| # | Note says | My model says | Why |
|---|---|---|---|
| M1 | §3: "Optional Route 116 trainers at L8-9, **reachable from Rustboro** … JOEY, JOSE, JERRY_1, CLARK, JANICE, KAREN_1, SARAH, DAWSON, DEVAN, JOHNSON" | **6 of 10 can be reached without Cut**: JOEY (12,7), JOSE (13,17), CLARK (36,17), KAREN_1 (22,16), JOHNSON (36,13), DEVAN (42,13). **4 sit in a Cut-gated pocket**: JANICE (26,6), JERRY_1 (28,8), SARAH (33,8), DAWSON (33,5). None of the four can see into the reachable region. | The pocket (x≈17-36, y≈2-11) can be LEFT by the `MB_JUMP_WEST` ledges at x=16 and x=21 and by the `MB_JUMP_SOUTH` row y=12, but can be ENTERED only through the Cut tree at (32,10). The ledge tiles have collision 1. Sources: Route116 `map.json` object_events; `data/layouts/Route116/map.bin` (blob a6e9d88, size asserted). The levels and script lines ARE confirmed (§3 table) |
| M2 | §4b: Route 116 "reachable on foot in ch3-4: REPEL (10,17), **POTION (34,7)** [02]" | REPEL: yes. **POTION (34,7): no.** It is inside the same Cut pocket. Its only open neighbour, (34,8), is boxed by SARAH's own tile (33,8) and by walls. | as M1 |

The rest of the Route 116 rows agree with the note. ETHER (19,6) is behind Cut. HP UP (80,8) cannot be reached. **X SPECIAL (55,12)**, marked † (unverified) in the note, **can be reached** in my model. The item ball itself blocks the pass south of it. That is why my region's max x is 56 where [03] says 60; the conclusion does not change.

### 0c. §9 proof-design defects (the facts are right, but the proof would be wrong)

| # | Where | Defect | Decomp basis |
|---|---|---|---|
| D1 | §9b PASS 1: "`VAR_SCOTT_PETALBURG_ENCOUNTER` == 1 (the forced scene was sat through)" | **It can pass vacuously.** SCOTT's coord triggers are keyed ONLY on that var being 0, with no chapter gate. The scene therefore fires the first time the player steps on x=4, y=10..13 in Petalburg, which can happen during CHAPTER 2 (exploring west before or after DAD). The §9b start premise checks the woods var and the Rustboro flag but NOT this var. **Fix:** add `VAR_SCOTT_PETALBURG_ENCOUNTER == 0` to the start premise, or REPORT the start value and grade PASS 1 only when it was 0. | `PetalburgCity/map.json` coord_events (x=4, y=10..13, `VAR_SCOTT_PETALBURG_ENCOUNTER` = 0); `PetalburgCity/scripts.inc:518-543`. The tiles are forced for the west exit (CONFIRMED-MODEL, §A) |
| D2 | §9b PASS 2: "`VAR_PETALBURG_WOODS_STATE` == 1, AND `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT` set. **Two independent witnesses.**" | **They are not independent.** Both are written by the SAME script run: `removeobject` GRUNT at `:70` sets the hide flag, and `setvar` at `:92` sets the var. No other script in the repo touches either symbol (GitHub code search: the flag appears only in `flags.h` and `PetalburgWoods/map.json`; the var only in `vars.h`, the woods' `scripts.inc` and `map.json`). They are a valid **consistency pair** (flag set + var 0 means the scene was cut off between `:70` and `:92`), not two witnesses. Say so in the verdict. | `PetalburgWoods/scripts.inc:66-94`; `flags.h:774` |
| D3 | §9c PASS 1: "… and `VAR_RUSTBORO_CITY_STATE` == 1" | **It turns FALSE if the run keeps walking after the badge.** Leaving the gym plaza is forced across x=23, y=20..24 (CONFIRMED-MODEL, §A), and that coord trigger's scene sets the var to **2**. If chapter 4 is allowed to continue until "the screen is free" (PASS 2) and the AI then walks out, PASS 1 fails on a correct run. **Fix:** grade `>= 1`, or sample the var at the moment `FLAG_BADGE01_GET` turns on. | `RustboroCity/map.json` coord_events (23,20..24) on state 1; `RustboroCity/scripts.inc:271-297`: `setvar VAR_RUSTBORO_CITY_STATE, 2` at `:288` (also `setflag FLAG_DEVON_GOODS_STOLEN` `:287`) |
| D4 | §9c fault arm HOLD_B_EVOLVE ("the hands hold B in an evolution") and §6 gap 3 ("never hold B in an evolution scene") | The cancel fires only if **B is the ONLY key held** (`gMain.heldKeys == B_BUTTON`), only in state `EVOSTATE_WAIT_CYCLE_MON_SPRITE`, and only when `TASK_BIT_CAN_STOP` is set. A fault arm that holds B **plus** a direction or A never cancels. It would not REACH its state, so the arm would be vacuous. Conversely, the hands are safe while any second key is held. **Fix:** the arm must hold B alone, and its reach check must be "species unchanged at L16+". | `src/evolution_scene.c:637-647` |

### 0d. Citation slips (the substance is right)
- `set_gym_trainers.inc:12-16` → the routine is **`:13-17`** (label at `:13`, `settrainerflag` JOSH/TOMMY/MARC at `:14-16`). It is reached
  through `setvar VAR_0x8008, 1` (`RustboroCity_Gym/scripts.inc:22`) then `call Common_EventScript_SetGymTrainers` (`:23`), which
  dispatches on `VAR_0x8008` (`set_gym_trainers.inc:1-3`).
- "`VAR_PETALBURG_WOODS_STATE` 0→1 is its LAST command (`:92`)": it is the last STATE change, and `releaseall` at `:93` follows.
  The substance holds.
- §2 "Bullet Seed boy [5,26]: 'A TM … is good only for one-time use …' (`:1021`)": that line plays only AFTER the TM is
  given (`Route104/scripts.inc:320`, `:328-331`). The first talk gives `…_Text_LikeFillingMouthWithSeedsTakeThis` (`:1014-1019`).

### 0e. Upgrades: open items this pass settles
- **§1 beat 10 / §9a P6, "[05] says it moves to 2; UNVERIFIED"**: now **CONFIRMED 2** (`RustboroCity/scripts.inc:288`).
- **§10 Q9, `OBJ_EVENT_GFX_ROXANNE` = 125?**: **CONFIRMED** (`include/constants/event_objects.h:132`), and it matches
  `ai_player/knowledge/milestones.json:136-142`.
- **§10 Q7, Route 116 trainers west of the limit**: all ten stand at x ≤ 42 (`Route116/map.json`). Six are reachable
  without Cut and four are not (M1, MODEL).
- **§4a PREMIER BALL "[02 only]"**: now **CONFIRMED** with no gate beyond "not received" and a bag check
  (`RustboroCity_Flat2_2F/scripts.inc:8-16`). The flag is `FLAG_RECEIVED_PREMIER_BALL_RUSTBORO` = **0xD5** (`flags.h:235`).
- **§4a BLACK GLASSES**: stronger than "not before the badge". Route 116's east half can be reached on foot only in
  two ways, and both need far more progress:
  - from VERDANTURF to the south (`Route116/map.json` connection `down`, offset 80), which is reached from Mauville;
  - through RUSTURF TUNNEL's east exit. Inside the tunnel, the west entrance (4,10) is cut off from the east exit (18,20)
    by two `BREAKABLE_ROCK`s at (24,4)/(24,5), which need Rock Smash.

  CONFIRMED-MODEL: `RusturfTunnel/map.json` object_events + warps; layout blob 87ce9bc.

---

## A. Method, and the independent model's limits

**Text and constants.** I fetched raw from pret/pokeemerald `master` (HEAD `731ad5b` at fetch time):
- `include/constants/{flags,vars,opponents,event_objects,metatile_behaviors}.h`;
- `src/data/{trainers.h,trainer_parties.h,trade.h,wild_encounters.json}`;
- `src/data/pokemon/{evolution.h,level_up_learnsets.h,tmhm_learnsets.h,species_info.h}`;
- the `scripts.inc` and `map.json` of every map named;
- `data/scripts/{new_game,set_gym_trainers,players_house}.inc`;
- `src/{trainer_see,battle_setup,battle_main,battle_util,evolution_scene,party_menu,pokemon,field_control_avatar,overworld,event_data,event_object_movement,field_player_avatar,metatile_behavior}.c`.

**Binaries** (`map.bin`, `metatile_attributes.bin`) were fetched **by blob sha**, with `len == size` asserted, because of the
[01 §13] fetch hazard. Route104 6400 B, PetalburgWoods 4224 B, RustboroCity_Gym 440 B, RustboroCity 4800 B, Route116 4000 B,
PetalburgCity 1800 B and RusturfTunnel 1728 B all equal width × height × 2 from `layouts.json`.

**The walk model.** It is a BFS over (x, y, elevation). The rules were transcribed from the decomp, not recalled:
- collision bits and `GetCollisionAtCoords` (`event_object_movement.c:4641-4654`);
- `IsElevationMismatchAt` (`:7673-7689`) and `ObjectEventUpdateElevation` (`:7725-7737`);
- directional impassables (`:4697-4704`, `metatile_behavior.c:933-977`);
- ledges as `GetLedgeJumpDirection` (`:7631-7654`) evaluated BEFORE collision, exactly as `CheckForObjectEventCollision`
  orders them (`field_player_avatar.c:693-714`), landing two tiles on;
- step-on warps as terminals;
- sight as `GetTrainerApproachDistance` + `CheckPathBetweenTrainerAndPlayer` (`trainer_see.c:301-405`): directional, blocked
  by collision and objects.

Objects hidden by a `setflag` in `new_game.inc` are absent, and the White Herb florist is absent per `Route104/scripts.inc:21-29`.

**Limits.**
- Wanderers are frozen at their spawn tile.
- There is no timing.
- A rotating trainer is tested per facing and with all facings at once.
- BILLY's walk-sequence was simulated with `MoveNextDirectionInSequence` (`event_object_movement.c:3827-3853`).
- Hidden items count as "reachable" if the tile or a 4-neighbour is on the region.
- **This is a second MODEL, written with different code from [01]/[05], but on the same input. Use it to find
  disagreements, not to raise confidence.**

---

## B. §1 — The story path, flags and vars

| Claim (note) | Verdict | My citation |
|---|---|---|
| `VAR_PETALBURG_GYM_STATE` = 2, 0x4085, at `PetalburgCity_Gym/scripts.inc:90` | CONFIRMED | `vars.h:153`; `PetalburgCity_Gym/scripts.inc:89-90` (DAD's msgbox, then the setvar) |
| `VAR_PETALBURG_CITY_STATE` = 3 at the tutorial's end, `PetalburgCity/scripts.inc:47` | CONFIRMED | `vars.h:107`; `:47` |
| SCOTT: coord x=4, y=10..13 on `VAR_SCOTT_PETALBURG_ENCOUNTER == 0`; var → 1 at `:540`; `VAR_SCOTT_STATE` = 1 at `:525` before three msgboxes; no battle | CONFIRMED | `PetalburgCity/map.json` coord_events; `PetalburgCity/scripts.inc:518-543` (msgboxes `:526`, `:530`, `:534`); `vars.h:221`, `:229`. ⚠ See D1 |
| SCOTT's tiles are on the only west exit | CONFIRMED-MODEL | Blocking (4,10..13) leaves Petalburg's west edge unreachable from the gym door. The walkable seam is Petalburg y=12..13 = Route 104 y=62..63 |
| Only the SW woods door (10/11,38) can be entered from Route 104 south | CONFIRMED-MODEL | The south region reaches warps (10,38), (11,38), (17,50) only. The SE door (32/33,42) is in a pocket that can be left (it joins the south region) but never entered |
| Woods scene: coord (26,23)/(27,23) on `VAR_PETALBURG_WOODS_STATE == 0` | CONFIRMED | `PetalburgWoods/map.json` coord_events → `…_DevonResearcherLeft`/`Right` |
| Var → 1 at `:92`; 0x4098 = 16536 | CONFIRMED | `PetalburgWoods/scripts.inc:90-94`; `vars.h:172` (see §0d) |
| Second witnesses `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT` 0x2D5, `…_DEVON_EMPLOYEE` 0x2D4, set by `removeobject` | CONFIRMED (see D2 on "independent") | `flags.h:773-774`; `removeobject` `:70` (grunt) and `:91` (researcher). They are the objects' `flag` in `map.json` |
| Grunt trainer flag 0x50A (1290), only on a WIN | CONFIRMED | `opponents.h:14`; `battle_setup.c:1327-1349`: `SetBattledTrainersFlags()` runs only in the not-defeated branch |
| The Great Ball has NO flag (`:73`) | CONFIRMED | `:73` `giveitem ITEM_GREAT_BALL`, with no setflag anywhere in `:66-94` |
| A loss means a whiteout, the var stays 0 and the scene replays | CONFIRMED (by script structure) | The battle is at `:23`/`:51`. A loss diverts to `CB2_WhiteOut` (`battle_setup.c:1333-1338`) before `:92`. The trigger is keyed on var 0, and neither hide flag is set |
| The scene fires 15 rows north of the south doors | CONFIRMED | doors at y=38 (`PetalburgWoods/map.json` warps) − 23 |
| The scene is forced northbound | CONFIRMED-MODEL | Blocking (26,23)/(27,23) leaves NO SW→N path even with every object removed, Cut trees included. The corridor x=26-27, y=20-23 is walled on both sides (collision bits). Shortest is 85 steps through 31 grass tiles; the woods have 325 grass tiles |
| N exit = arrow warp (14/15,5), hold UP | CONFIRMED | Tileset behaviour at (14,5)/(15,5) = `MB_NORTH_ARROW_WARP`; `PetalburgWoods/map.json` warps |
| Arrival on Route 104 at (10/11,30), facing NORTH | CONFIRMED | Woods warps 0/1 → `MAP_ROUTE104` warp 2/3 = (10,30)/(11,30); behaviour `MB_DEEP_SOUTH_WARP`; `overworld.c:933-934` |
| `FLAG_VISITED_RUSTBORO_CITY` 0x879 (2169), set OnTransition | CONFIRMED | `flags.h:1348` (`SYSTEM_FLAGS` 0x860) and `:1380` (+0x19); `RustboroCity/scripts.inc:6-7`. OnTransition also runs on a connection crossing: `overworld.c:784` `LoadMapFromCameraTransition` → `RunOnTransitionMapScript` |
| A quiet arrival: no coord trigger armed at state 0 | CONFIRMED | Rustboro coord_events exist only for states 1, 2, 4 and 7; OnFrame only for 6 (`RustboroCity/scripts.inc:27-29`) |
| Heal: `setrespawn HEAL_LOCATION_RUSTBORO_CITY` | CONFIRMED | `RustboroCity_PokemonCenter_1F/scripts.inc:7` |
| "Before this, a whiteout returns the player to PETALBURG" | **REFUTED** (R3) | as R3 |
| `FLAG_RECEIVED_QUICK_CLAW` 0x113; `FLAG_RECEIVED_HM_CUT` 0x89; `FLAG_MET_SCOTT_RUSTBORO` 0x136 | CONFIRMED | `flags.h:301`, `:159`, `:336`. SCOTT in the school is visible from New Game: his hide flag is not among the `setflag`s in `new_game.inc` |
| JOSH 0x640 (1600), TOMMY 0x641 (1601), MARC 0x73B (1851) | CONFIRMED | `opponents.h:324`, `:325`, `:575` + `flags.h:1343` |
| ROXANNE's win sets all three | CONFIRMED | `set_gym_trainers.inc:13-17` (see §0d) |
| `FLAG_DEFEATED_RUSTBORO_GYM` 0x4F0 (1264), `FLAG_BADGE01_GET` 0x867 (2151), in the stated order; TM39 skipped on a full bag; talking again retries | CONFIRMED | `flags.h:1319`, `:1359`; `RustboroCity_Gym/scripts.inc:13-34` (badge text `:14-17`, flags `:18-19`, state `:20`, `addvar` `:21`, SetGymTrainers `:22-23`, TM `:28-34`); retry `:8`; bag full `:30` |
| ROXANNE is `TRAINER_TYPE_NONE`; talk from (5,3) facing up | CONFIRMED, with a nuance | `RustboroCity_Gym/map.json` obj1. Nuance: (4,2) and (6,2) are open floor (collision 0, elevation 3), so she can also be talked to from her SIDES. "(5,3)" is not the only approach |
| Her trainer flag 0x609 (1545) | CONFIRMED | `opponents.h:269` |
| Stolen-goods coord (23,20..24) on state 1 | CONFIRMED | `RustboroCity/map.json` coord_events |
| …forced on leaving the gym plaza | CONFIRMED-MODEL | From the gym door tile (27,20), blocking x=23, y=20..24 leaves an 88-tile pocket with no edge and no warp |
| …moves the state to 2 | **CONFIRMED (upgrade)** | `RustboroCity/scripts.inc:288` |
| `MARC` is missing from `milestones.json`; `ch4_gym_trainers` reads JOSH and TOMMY only | CONFIRMED (our tree, read-only) | A grep for `MARC`/`1851`/`571` finds no hit in `ai_player/knowledge/milestones.json`. Its ch3-4 trainer entries (`:219-250`) are GRUNT_PETALBURG_WOODS, JOSH, TOMMY and ROXANNE_1; `ch4_gym_trainers` done is at `:1182-1186` |
| §0.6: all three starters evolve at 16 | CONFIRMED | `evolution.h:125`, `:127`, `:129` |
| §0.6: B cancels an evolution | CONFIRMED, with a precision | `evolution_scene.c:637-647`. B must be the ONLY held key (D4) |
| §0.6: B on "learn the move?" answers NO | CONFIRMED (evolution-scene prompt) | `evolution_scene.c:946-951` |
| §0.6: an unevolved Torchic gets Peck, and Combusken gets Double Kick at 16 | CONFIRMED | Torchic `LEVEL_UP_MOVE(16, MOVE_PECK)`, `level_up_learnsets.h:3623-` (Peck `:3628`); Combusken `(16, MOVE_DOUBLE_KICK)` `:3638-` (`:3645`). Nuance: a Torchic that DOES evolve at 16 is offered both (Peck in battle as Torchic, then Double Kick in the evolution scene). "Instead" is right only for one that does not evolve |

---

## C. §2 — What the game TELLS the player (the quotes)

Each quote was compared word for word, and the speaker was checked by following the object's `script` in `map.json` to its
`msgbox`.

| Quote / location (note) | Verdict | My citation |
|---|---|---|
| DAD, automatic: "Head for RUSTBORO CITY beyond this town. There, you should challenge the GYM LEADER, ROXANNE." | CONFIRMED | `PetalburgCity_Gym/scripts.inc:1193-1208`, shown once at `:89` |
| DAD, repeatable: "Aren't you going to the POKéMON GYM in RUSTBORO CITY?" | CONFIRMED | `:1210-1218`; dispatched by `case 2` (`:105`) to `…_NormanNoBadges` (`:284-287`) |
| SCOTT: flavour only | CONFIRMED | `PetalburgCity/scripts.inc:726-741` |
| Route 104 signs: `→ PETALBURG CITY` [27,66], `↑ RUSTBORO CITY` [23,5] | CONFIRMED | `Route104/scripts.inc:1045-1051` (the game spells it "ROUTE 1O4", with a letter O); bg (27,66) and (23,5) |
| Nothing in the window names Petalburg Woods as the way | CONFIRMED (for the maps read) | No `.string` naming PETALBURG WOODS in PetalburgCity, PetalburgCity_Gym, Route104 or the flower shop. The first mentions are in Rustboro (`RustboroCity_Mart/scripts.inc:71`; `RustboroCity/scripts.inc:1003`, which is post-theft) |
| Girl [28,74]: "if TRAINERS lock eyes … stay out of their sight." | CONFIRMED | obj6 `Route104_EventScript_Girl2` → `:1007-1012` |
| Boy [27,63]: "weaken the wild POKéMON first." | CONFIRMED | obj4 `…_Boy1` → `:995-999` |
| Woman [30,50]: "throw POKé BALLS only at wild POKéMON." In the exit-only pocket | CONFIRMED; pocket CONFIRMED-MODEL | obj5 `…_Woman` → `:1001-1005`. Her neighbours are reachable only from the SE-door pocket |
| Woods TRAINER TIPS [14,32]: switch-training | CONFIRMED | bg `Sign1` → `PetalburgWoods/scripts.inc:437-445` |
| Woods boy [15,19]: stay out of tall grass | CONFIRMED | obj8 `…_Boy1` → `:410-415` |
| Woods boy [30,34]: "there are things on the ground even if you can't see them" | CONFIRMED | obj11 `…_Boy2` → `:417-421` |
| Woods TRAINER TIPS [11,8]: PP, "taken to a POKéMON CENTER" | CONFIRMED | `Sign2` → `:447-453` |
| Researcher: "have you seen any POKéMON called SHROOMISH around here?" | CONFIRMED | `:303-306` |
| Grunt: "we of TEAM AQUA are also after something in RUSTBORO." | CONFIRMED | `:333-341` (said after the battle, `:67`) |
| Researcher: "Didn't that TEAM AQUA thug say they were after something in RUSTBORO, too?" | CONFIRMED | `:351-354` |
| TRAINER TIPS [17,23]: double battles | CONFIRMED | `Route104/scripts.inc:1056-` |
| Bullet Seed boy [5,26]: one-time TM | CONFIRMED, with a nuance | `:1021-1026`, post-gift only (§0d) |
| Expert F [37,8]: berries | CONFIRMED | `:248-263` |
| Flower shop sign [7,20] | CONFIRMED | `:1053-1054` |
| Rustboro city sign `:1145` | CONFIRMED | `RustboroCity/scripts.inc:1145-1148` |
| Gym sign: "LEADER: ROXANNE 'The ROCK-loving honors student!'", the first on-screen statement of her type | CONFIRMED, with a nuance | `:1135-1138`; bg (23,19). Nuance: the FIRE/ROCK woman (below) links "the GYM LEADER" to ROCK by implication. If she is heard first, the sign is the first EXPLICIT statement, not the first statement |
| Woman [22,34]: "FIRE-type POKéMON don't match up well against ROCK-type POKéMON." | CONFIRMED | obj1 `RustboroCity_EventScript_Woman` (`:141-143`, unconditional) → `:946-951` |
| Man [26,23]: "Have you taken the POKéMON GYM challenge?" | CONFIRMED (before the badge) | obj6 `…_Man1` `:145-151` → `:928-933`. After the badge he says `:935-938` |
| Man [19,27]: traded Pokémon may disobey without badges | CONFIRMED | obj13 `…_Man2` `:224-229` → `:986-990` |
| Mart woman: "Just in case I run into SHROOMISH in PETALBURG WOODS" | CONFIRMED | `RustboroCity_Mart/scripts.inc:55-57` → `:67-71` (a POKEFAN F) |
| SCOTT in the school: "have a POKéMON learn the move CUT … someone in this town has CUT." | CONFIRMED (before the badge, first talk) | `RustboroCity_PokemonSchool/scripts.inc:159-169` → `:300-314` |
| "A man in the Pokémon Center: The man next door gave me an HM!" | **REFUTED** (R2: the speaker is the girl) | `RustboroCity_PokemonCenter_1F/scripts.inc:27-29`, `:43-46` |
| Teacher: "Students who don't study get a little taste of my QUICK CLAW." | CONFIRMED | `RustboroCity_PokemonSchool/scripts.inc:83` → `:242-247` |
| School kid: SEEDOT | CONFIRMED | `…_GameboyKid2` `:57-59` → `:262-264` |
| Tunnel signs: "The tunnel project has been canceled." | **REFUTED for the Rustboro sign** (R1) | `RustboroCity/scripts.inc:1123-1128` vs `Route116/scripts.inc:442-446` |
| Gym Guide: "ROXANNE … is a user of ROCK-type POKéMON. The ROCK type is very durable, but it can't stand WATER-type and GRASS-type moves." Fighting is not named | CONFIRMED | `RustboroCity_Gym/scripts.inc:56-62` (before victory) → `:106-126` |
| Trainer lines Josh `:147`, Tommy `:151`/`:158`, Marc `:173`; ROXANNE's intro `:178`; badge text `:203` ("…use the HM move CUT outside of battle") | CONFIRMED | same lines (`:147-149`, `:151-161`, `:173-176`, `:178-185`, `:203-208`) |

---

## D. §3 — Trainers, teams, single or double, avoidability

### D1. Ids, flags, classes and teams: every row CONFIRMED

Ids are from `opponents.h`; each flag is 0x500 + id. Teams and items are from `trainers.h` / `trainer_parties.h`.

| Trainer | id (`opponents.h`) | `trainers.h` (class, items, double, AI) | Party (`trainer_parties.h`) |
|---|---|---|---|
| CINDY_1 | 114 `:118` | `:1372-1382` LADY, FULL_RESTORE, FALSE | `:1451-1458` Zigzagoon L7 @NUGGET |
| BILLY | 319 `:323` | `:3832-3842` YOUNGSTER, FALSE | `:4214-4225` Zigzagoon L5, Seedot L7 |
| DARIAN | 696 `:700` | `:8356-8366` FISHERMAN | `:9436-9442` Magikarp L9 |
| GRUNT_PETALBURG_WOODS | 10 `:14` | `:124-134` TEAM_AQUA | `:103-109` Poochyena L9 |
| LYLE | 616 `:620` | `:7396-7406` BUG_CATCHER | `:8163-8184` Wurmple L3 ×4 |
| JAMES_1 | 621 `:625` | `:7456-7466` BUG_CATCHER | `:8233-8244` Nincada L6 ×2 |
| HALEY_1 | 604 `:608` | `:7252-7262` LASS | `:8007-8018` Lotad L6, Shroomish L6 |
| WINSTON_1 | 136 `:140` | `:1636-1646` RICH_BOY, FULL_RESTORE | `:1709-1716` Zigzagoon L7 @NUGGET |
| GINA_AND_MIA_1 | 483 `:487` | `:5800-5810` TWINS, **`doubleBattle = TRUE`** | `:6269-6280` Seedot L6, Lotad L6 |
| IVAN | 337 `:341` | `:4048-4058` FISHERMAN | `:4477-4493` Magikarp L5, L6, L7 |
| JOSH | 320 `:324` | `:3844-3854` YOUNGSTER | `:4227-4234` Geodude L10, moves {TACKLE} |
| TOMMY | 321 `:325` | `:3856-3866` YOUNGSTER | `:4236-4247` Geodude L8 ×2 |
| MARC | 571 `:575` | `:6856-6866` HIKER | `:7649-7660` Geodude L8 ×2 |
| ROXANNE_1 | 265 `:269` | `:3184-3194` LEADER, {POTION, POTION}, AI CHECK_BAD_MOVE \| TRY_TO_FAINT \| CHECK_VIABILITY | `:3367-3389` Geodude L12 ×2 {TACKLE, DEFENSE_CURL, ROCK_THROW, ROCK_TOMB}; Nosepass L15 @ORAN_BERRY {BLOCK, HARDEN, TACKLE, ROCK_TOMB} |

**How each battle starts (the scripts).** Every route and gym trainer uses `trainerbattle_single`:
- Route 104: `:832-982`;
- the woods: `PetalburgWoods/scripts.inc:253-260`;
- the gym: `RustboroCity_Gym/scripts.inc:5`, `:41-54`.

The twins use **`trainerbattle_double`**, which gives `…_GinaNotEnoughMons` or `…_MiaNotEnoughMons` (`Route104/scripts.inc:965-977`). The grunt
uses **`trainerbattle_no_intro`** (`PetalburgWoods/scripts.inc:23`, `:51`).

**Positions, facing and sight.** All CONFIRMED against `map.json` object_events (`movement_type`, `trainer_type`,
`trainer_sight_or_berry_tree_id`):
- CINDY (11,44) `FACE_UP_AND_RIGHT` 3; BILLY (18,67) `WALK_SEQUENCE_DOWN_RIGHT_UP_LEFT` 2 (range 5×6);
- DARIAN (15,59) `FACE_LEFT` **0**; LYLE (7,32) `FACE_DOWN_LEFT_AND_RIGHT` 3; JAMES (4,14) `FACE_DOWN_UP_AND_RIGHT` 3;
- HALEY (31,24) `FACE_LEFT` 7; WINSTON (21,25) `ROTATE_COUNTERCLOCKWISE` 3; twins (27,15)/(28,15) `FACE_DOWN` 1;
- IVAN (29,8) `FACE_DOWN` **0**; JOSH (5,13) `FACE_DOWN` 2; TOMMY (3,9) `FACE_LEFT` 3; MARC (1,6) `FACE_DOWN` 3;
- ROXANNE (5,2) `TRAINER_TYPE_NONE`.

**"Sight 0 means talk-only"** is CONFIRMED. With range 0 every `GetTrainerApproachDistance*` returns 0
(`trainer_see.c:327-368`), and `CheckPathBetweenTrainerAndPlayer` returns 0 on distance 0 (`:377-378`).

### D2. Mechanics

| Claim | Verdict | My citation |
|---|---|---|
| A trainer battle cannot be fled | CONFIRMED | `battle_main.c:4332-4337` (`BattleScript_PrintCantRunFromTrainer`) |
| Sight is checked every overworld frame, from the player's DESTINATION tile; a rotating trainer can spot a player who stands still | CONFIRMED | `overworld.c:1438-1457` → `field_control_avatar.c:147` runs before the `tookStep` gate (`:155`); `trainer_see.c:307` uses `PlayerGetDestCoords`. Precision: only while field controls are unlocked (`overworld.c:1445`) |
| The double gate: a `trainerbattle_double` trainer is skipped unless the player has 2 usable Pokémon; eggs and fainted ones do not count | CONFIRMED | `trainer_see.c:279-285`; `pokemon.c:4527-4544` (counts species ≠ EGG/NONE with HP ≠ 0) |
| Two spotting trainers are collected in one frame with 2 usable; with 1 usable it is a single with the first checked | CONFIRMED | `trainer_see.c:191-245` (the `break` at `:216-217`); two trainers set `BATTLE_TYPE_DOUBLE \| TWO_OPPONENTS \| TRAINER` (`battle_setup.c:1274-1275`) |
| Gym (1,9) is seen by both TOMMY and MARC | CONFIRMED (geometry) + MODEL | TOMMY left 3 → (2,9), (1,9); (0,9) is a wall. MARC down 3 → (1,7), (1,8), (1,9). The overlap is {(1,9)} |
| Gym shortest path 23-24 steps, crossing JOSH's line and (1,9); an all-avoiding path of about 30 | CONFIRMED-MODEL | Shortest door→(5,3) = **24**, through (5,15), (5,14) [JOSH] and (1,9..7) [TOMMY ∩ MARC, then MARC]. Avoiding all three = **30** |
| Losing means a whiteout to the last Pokémon Center entered | CONFIRMED (as "the last respawn") | `battle_setup.c:1333-1338` |
| No rival battle in ch3-4; the rivals start hidden and appear only after the PokéNav | CONFIRMED | `new_game.inc:129`, `:231`. The Route 104 rival is revealed only by `Route104/scripts.inc:47-55` on `VAR_ROUTE104_STATE` 1, which is set in `RustboroCity/scripts.inc:33`. The Rustboro rival is cleared only in `RustboroCity_DevonCorp_3F/scripts.inc` (code search) |
| ROXANNE matchups: Mudkip Mud-Slap L6 then Water Gun L10 (×2-×4 on Geodude, ×2 on Nosepass); Treecko Absorb L6 (×4 / ×2); Torchic Ember ×½, and Rock moves ×2 on Fire | CONFIRMED | Learnsets: Mudkip `level_up_learnsets.h:3676-` (`:3679`, `:3680`); Treecko `:3575`; Torchic Ember L10 `:3627`. Type rows in `battle_main.c`: Ground→Rock ×2 `:398`; Water→Rock and Water→Ground ×2 `:351`, `:350`; Grass→Rock and Grass→Ground ×2 `:366`, `:363`; Fire→Rock ×½ `:344`; Rock→Fire ×2 `:420`; Fighting→Rock ×2 `:383`; Normal→Rock and Flying→Rock ×½ `:337`, `:404`. Geodude Rock/Ground (`species_info.h:2237`); Nosepass Rock (`:8917`). Extra: a COMBUSKEN takes Rock moves at ×1, since Rock→Fighting is ×½ (`battle_main.c:422`) |
| "What the bot measured" (L16-17, 460 of 460) | UNVERIFIABLE by decomp | bot data, [04] |
| Route 116 trainers at L8-9; scripts `Route116/scripts.inc:226-343` | CONFIRMED (levels, lines, all singles) | JOEY Machop 9; JOSE 8, 8; JERRY_1 Ralts 9; CLARK Geodude 8; JANICE Marill 9; KAREN_1 Shroomish 9; SARAH 8, 8; DAWSON 8, 8; DEVAN Geodude 8 ×2; JOHNSON 8, 8 |
| …"reachable from Rustboro" | **REFUTED-MODEL for 4 of 10** (M1) | §0b |

### D3. "Avoidable?" column (all MODEL in the note; re-derived here)

| Trainer | Note | Mine | Detail |
|---|---|---|---|
| CINDY | Yes, by x=10 | **CONFIRMED-MODEL** | Seam→SW door is 52 steps; 53 avoiding her up and right lines {(11,41..43), (12..14,44)}; it ends at (10,38) |
| BILLY | Yes | **CONFIRMED-MODEL** | Simulated patrol x 18-23, y 65-73. It ends walking in place at (23,65) facing a wall at (23,64). The seam→door path keeps its 52 steps while avoiding his whole patrol and every sight tile |
| DARIAN, IVAN | Talk-only | CONFIRMED | sight 0 (D1) |
| GRUNT | No (northbound) | CONFIRMED-MODEL | B, "forced northbound" |
| LYLE | Timing-dependent | **CONFIRMED-MODEL** | Avoiding each single facing: S 85, W 85, E 91. Avoiding all facings at once: no path |
| JAMES | Only if he faces east as you cross row 14 | **CONFIRMED-MODEL** | Facing S or N: avoidable (85). **Facing E**: no path (his line (5..7,14) cuts the route) |
| Southbound, every woods trainer avoidable | (§8c) | CONFIRMED-MODEL | N exit→SW door 32 and →SE door 52, with all facings of both blocked |
| HALEY | Yes | CONFIRMED-MODEL | Line (24..30,24); avoiding it still gives 54 to the Rustboro edge |
| WINSTON | Timing-dependent | **CONFIRMED-MODEL** | Each single facing is avoidable (54). All four facings at once: no path |
| GINA & MIA | No, with 2 usable | **CONFIRMED-MODEL** | Their lines are exactly the deck tiles {(27,16), (28,16)}. Avoiding them leaves NO path from the woods N exit to Rustboro. The shortest walk (54) crosses the deck at (29..26,16) |
| JOSH, TOMMY, MARC | Yes | CONFIRMED-MODEL | 30-step path (D2) |

---

## E. §4 — Items and gifts

### E1. Gifts (conditions)

| Item | Verdict | My citation |
|---|---|---|
| GREAT BALL (researcher): no flag; a full bag gives nothing | CONFIRMED | `PetalburgWoods/scripts.inc:73-81` |
| TM09 BULLET SEED: `FLAG_RECEIVED_TM_BULLET_SEED` 0x106, no gate | CONFIRMED | `flags.h:288`; `Route104/scripts.inc:317-326`. The boy is reachable from the north half (MODEL) |
| CHESTO BERRY: 0xF6, no gate | CONFIRMED | `flags.h:272`; `Route104/scripts.inc:248-258` |
| WAILMER PAIL: 0x5E, no gate | CONFIRMED | `flags.h:112`; `Route104_PrettyPetalFlowerShop/scripts.inc:62-76` (no bag check). The shop door (5,18) is reachable from the north (MODEL) |
| Daily berry: one of CHERI..PERSIM | CONFIRMED | `:78-91`: `random 8` + `FIRST_BERRY_INDEX`; `flags.h:1589` |
| Owner: `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` 0x7F, set on first talk, YES/NO | CONFIRMED | `flags.h:149`; `:16-27` (set at `:22`, whatever the answer) |
| QUICK CLAW: only "not received yet"; from the side he walks a loop first | CONFIRMED | `RustboroCity_PokemonSchool/scripts.inc:77-98` (the `VAR_FACING` east/west movements `:81-82`; the bag check `:85`) |
| HM01 CUT: no gate; Cut in the field needs `FLAG_BADGE01_GET` | CONFIRMED | `RustboroCity_CuttersHouse/scripts.inc:4-13`; `party_menu.c:120`, `:3725` |
| PREMIER BALL | **CONFIRMED (upgrade from "[02 only]")** | `RustboroCity_Flat2_2F/scripts.inc:8-16`; `flags.h:235` 0xD5 |
| TM39: the bag must have room | CONFIRMED | `RustboroCity_Gym/scripts.inc:28-34` |
| RALTS-for-SEEDOT "DOTS" @Chesto; YES opens `ChoosePartyMon`; nothing chosen = decline | CONFIRMED | `RustboroCity_House1/scripts.inc:4-28` (`:12-16`); `src/data/trade.h:987-1001` (`DOTS`, SEEDOT, CHESTO_BERRY, `requestedSpecies` RALTS); `flags.h:175` 0x99 |
| MIRACLE SEED: no script gate, behind Cut, and her line assumes the badge | CONFIRMED + CONFIRMED-MODEL | `PetalburgWoods/scripts.inc:229-238`, `:423-427` ("That's the BADGE from RUSTBORO GYM!"). (33,5) is reachable only with the Cut trees (19,10)/(19,11) gone |
| WHITE HERB: hidden unless the owner was met AND badge 3 | CONFIRMED | `Route104/scripts.inc:21-29` |
| AMULET COIN: `FLAG_BADGE05_GET` | CONFIRMED | `players_house.inc:307-319`. It also needs `FLAG_ENABLE_MOM_MATCH_CALL` (`:293-294`). Out of window either way |
| BLACK GLASSES (70,13) not in ch3-4 | CONFIRMED-MODEL, stronger | `flags.h:642`; `Route116/map.json` bg_events. Not reachable from Rustboro. The east half needs Rock Smash through RUSTURF TUNNEL, or the walk north from Verdanturf (§0e) |
| Rustboro Mart before `FLAG_MET_DEVON_EMPLOYEE`: Poké Ball, Potion, Super Potion, Antidote, Paralyze Heal, Escape Rope, Repel, X Speed, X Attack, X Defend; no Great Ball | CONFIRMED | `RustboroCity_Mart/scripts.inc:4-31` (the expanded list `:40-53` has no Great Ball either). Precision: `FLAG_MET_DEVON_EMPLOYEE` is set by the Route 116 DEVON employee (`Route116/scripts.inc:54-55`). He is hidden from New Game (`new_game.inc:243`) and revealed only at the Slateport Oceanic Museum (`SlateportCity_OceanicMuseum_2F/scripts.inc`, code search), so it is long after the badge, not merely "after the badge" |

### E2. Visible item balls: placement CONFIRMED, reachability re-derived

Placements and flags are CONFIRMED (`map.json`; `flags.h`): `FLAG_ITEM_ROUTE_104_POTION` 0x46F `:1188`; `…_ROUTE_104_POKE_BALL`
0x421 `:1110`; woods ETHER 0x422 `:1111`; PARALYZE HEAL 0x45D `:1170`; GREAT BALL 0x420 `:1109`; X ATTACK 0x41F `:1108`;
Rustboro X DEFEND 0x411 `:1094`.

| Item | Note | Mine (MODEL) |
|---|---|---|
| R104 POTION (5,8) | reachable, north | CONFIRMED |
| R104 POKé BALL (29,53) | only via the SE exit | CONFIRMED: only from the SE-door pocket |
| R104 PP UP (39,15) | Surf | CONFIRMED unreachable on foot (with or without Cut) |
| R104 X ACCURACY (37,22) | behind Cut (35,22) | CONFIRMED: reachable only with the tree gone |
| Woods ETHER (4,8), PARALYZE HEAL (4,26) | reachable | CONFIRMED (77 and 23 steps from the SW door) |
| Woods GREAT BALL (45,7), X ATTACK (35,20) | behind Cut | CONFIRMED (117 and 133 with the trees gone; none without) |
| Rustboro X DEFEND (36,51) | only from Route 104's north strip at x=33 | CONFIRMED. Entering Rustboro at x=33 gives a 35-tile pocket holding the X Defend with no gym or PC access. Entries at x=12..19 give the 1024-tile street region without it |
| Route 116 REPEL (10,17) | reachable | CONFIRMED |
| Route 116 POTION (34,7) | reachable [02] | **REFUTED-MODEL** (M2) |
| Route 116 ETHER (19,6) | beside a Cut tree | CONFIRMED (Cut-gated) |
| Route 116 X SPECIAL (55,12) † | unverified | reachable without Cut (MODEL) |
| Route 116 HP UP (80,8) † | unverified | unreachable (MODEL) |
| Rusturf POKé BALL (3,1); MAX ETHER (30,2) † | | POKé BALL reachable from the Route 116 entrance; MAX ETHER is behind the Rock Smash rocks (MODEL) |

### E3. Hidden items and berry trees

- All coordinates CONFIRMED from `bg_events`. My model agrees with the note's split:
  - Route 104 POTION (14,55), ANTIDOTE (16,72) and HEART SCALE (16,64) are SOUTH; SUPER POTION (7,6) and POKé BALL (3,9) are NORTH;
  - woods POTION (39,35) and POKé BALL (4,19) are reachable; both TINY MUSHROOMs are not.
- Berry trees CONFIRMED (`new_game.inc:7-12`, `map.json`): ORAN (22,41) and PECHA (24,41) are reachable from the south;
  ORAN (3,23), CHERI (3,25), CHERI (34,6) and LEPPA (36,6) from the north (MODEL). The SOIL trees are not in
  `EventScript_ResetAllBerries`, so they start empty.

---

## F. §5 — Wild species: all CONFIRMED

Source: `src/data/wild_encounters.json`, land slots summed with the header's `encounter_rates`
(20/20/10/10/10/10/5/5/4/4/1/1).

| Map | Note | Verdict |
|---|---|---|
| ROUTE104 land, rate 20 | Poochyena 40% L4-5, Wurmple 20% L4, Marill 20% L4-5, Taillow 10% L4-5, Wingull 10% L3-5 | CONFIRMED (exact). Water: Wingull 95% / Pelipper 5%. Every fishing slot is Magikarp |
| PETALBURG_WOODS land, rate 20 | Poochyena 30% L5-6, Wurmple 25% L5-6, Shroomish 15% L5-6, Silcoon 10% L5, Cascoon 10% L5, Taillow 5% L5-6, Slakoth 5% L5-6 | CONFIRMED (exact) |
| RUSTBORO_CITY | none | CONFIRMED (no header) |
| ROUTE116 | Poochyena 28% L6-8, Whismur 20% L6, Nincada 20% L6-7, Taillow 20% L6-8, Abra 10% L7, Skitty 2% L7-8 | CONFIRMED (exact) |
| RUSTURF_TUNNEL | Whismur 100% L5-8 | CONFIRMED (land rate 10) |
| The OLD ROD comes from Dewford | CONFIRMED (location only) | `DewfordTown/scripts.inc` is the only `giveitem ITEM_OLD_ROD` (code search). "After the badge" is access timing, not re-read |
| SHROOMISH: Absorb from L1, Stun Spore at L7 | CONFIRMED | `level_up_learnsets.h:3987-3990` |
| MARILL: Water Gun at L10 | CONFIRMED | `:2523` |
| WINGULL: Water Gun at L1, Water/Flying, Rock ×2 | CONFIRMED | `:4036`; `species_info.h:8587`; `battle_main.c:424` |
| Shroomish, Seedot and Lotad can learn TM09 | CONFIRMED | `tmhm_learnsets.h:7327`, `:7142`, `:7057` (`TM09_BULLET_SEED`) |
| Whismur's Uproar (the [04] catch trap) | Mechanism CONFIRMED; frequency UNVERIFIABLE | Whismur learns Uproar at L5 (`level_up_learnsets.h:4990`), so every wild Whismur here (L5-8) can have it |

---

## G. §9 — DRAFT pre-registration

| Item | Verdict |
|---|---|
| Common rules (identity, reach floors, frozen tree, chained fixtures) | Not decomp facts. No objection; see D1-D4 for where §9 conflicts with the decomp |
| P1 woods choke: discriminator "var → 1 before the map changes via N" | Consistent with the decomp + MODEL (the scene is the only northbound link) |
| P2 twins: A (1 usable) no battle, B (2 usable) a double | CONFIRMED by construction (`trainer_see.c:279-285`; `pokemon.c:4527-4544`). Their lines are exactly (27,16)/(28,16) |
| P3 gym (1,9): A single (first checked), B `TWO_OPPONENTS` TOMMY + MARC | CONFIRMED (`trainer_see.c:198-240`; `battle_setup.c:1274-1275`). Which single in A depends on object-slot order: record it, do not predict it |
| P4 after-badge flags all set although unfought | CONFIRMED (`set_gym_trainers.inc:13-17`) |
| P5 gap-1 A/B discriminator: arrival y on ROUTE104 (> 37 south, < 31 north) | Computable and the arms differ: the N exit lands at y=30, the SW door at y=38, the SE door at y=42 (`Route104/map.json` warps) |
| P6 theft value "UNVERIFIED as 2" | **CONFIRMED 2** (`RustboroCity/scripts.inc:288`) |
| 9b start premise | **Incomplete (D1)**: add `VAR_SCOTT_PETALBURG_ENCOUNTER == 0` or grade conditionally |
| 9b PASS 2 "two independent witnesses" | **Wording REFUTED (D2)**: one script, two writes |
| 9b PASS 3: 0x50A set and trainer id 10 won | CONFIRMED (the flag is set only on a non-loss) |
| 9b REPORTED gift flags 0x106, 0xF6, 0x5E, 0x7F | CONFIRMED values |
| 9c PASS 1 `VAR_RUSTBORO_CITY_STATE == 1` | **Fragile (D3)**: use `>= 1` or sample at the badge |
| 9c "sample 0x640/0x641/0x73B BEFORE ROXANNE's battle" | CONFIRMED necessary (P4) |
| 9c HOLD_B_EVOLVE | **Arm design (D4)**: B alone, or the arm is vacuous |
| 9c TRADE_YES: B on the party menu gives `PARTY_NOTHING_CHOSEN`, a clean decline | CONFIRMED at the script level: `RustboroCity_House1/scripts.inc:16` routes `PARTY_NOTHING_CHOSEN` to `…_DeclineTrade` (`:30-33`). That B in `ChoosePartyMon` yields that value was not re-read in `party_menu.c`: UNVERIFIABLE here |
| `STORY_PATIENCE` 120,000 (`mode.py:102`), `MAX_LOSSES` 3 (`:103`), `TRAIN_SESSIONS` 8 (`goals.py:189`), `OUTDOOR` regex (`goals.py:432`) | CONFIRMED (our tree, read-only grep) |
| `README.md`/`rate_step5.py` line citations (`:300`, `:352`, `:1443`) | UNVERIFIABLE here (not re-read; not decomp) |

---

## H. Things the note gets right that are worth keeping loud

- The woods scene is the ONLY northbound link (a second independent model agrees, even with all objects and Cut trees
  removed). It is still MODEL until P1 runs.
- The twins' deck is the only crossing of Route 104 north, and their lines are exactly the two deck tiles.
- ROXANNE's win sets all three gym trainers' flags: any "fought" check must sample before her battle.
- `FLAG_BADGE01_GET` turns on before TM39 and its text (`RustboroCity_Gym/scripts.inc:18-19` vs `:28-34`).

*Sources: pret/pokeemerald `master` @ `731ad5b` (fetched 2026-10-15), files as cited. Our tree, read-only:
`ai_player/knowledge/milestones.json`, `ai_player/brain/goals.py:189,432`, `ai_player/mode.py:102-103`. The model
scripts were session-scratch only (`woods.py`, `r104.py`, `gym.py`, `rust.py`, `plaza.py`, `petal.py`, `r116walk.py`,
`tunnel.py`, `billy.py`, `hidden.py` on top of `model.py`) and are not kept.*
