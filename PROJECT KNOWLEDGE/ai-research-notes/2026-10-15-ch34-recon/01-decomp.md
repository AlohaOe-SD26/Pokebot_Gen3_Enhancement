# Chapters 3-4 recon, angle 01: THE DECOMP (Route 104, Petalburg Woods, Rustboro, Rustboro Gym)

> ⚠ **AI-RESEARCH NOTE, NOT A SOURCE OF TRUTH** (see `../00-READ-THIS-FIRST.md`). Written 2026-10-15 by a
> Claude subagent WITH tool access. Every claim is tagged:
> - **VERIFIED**: read in `pret/pokeemerald` (master `731ad5bf`, committed 2026-10-01) or in our tree, with the citation.
> - **MODEL**: computed by my own static walkability/sight script from the decomp layouts (not a live run).
>   The model mirrors `GetCollisionAtCoords`, `IsElevationMismatchAt`, ledge jumps and trainer sight
>   (citations in §10), but wandering NPCs are frozen at their spawn tile. Confirm load-bearing MODEL claims live.
> - **UNVERIFIED**: recall or inference that I did not check.
>
> ⛔ **PERSON-FAIR (USER RULINGS 35-37).** Every coordinate, flag, route and step count below is for the
> DEVELOPERS: for designing proofs, expectations and fault arms. None of it may be fed to the AI player as a hint.
> The AI only gets what the game's dialogue and signs say. §12 lists the dialogue-level hints the game itself
> gives in these chapters.

---

## 0. Headline findings (read these first)

1. **From Petalburg, only ONE Woods entrance works: the south-WEST door, Route 104 (10/11,38).** The south-EAST door
   (32/33,42) sits in a ledge-locked pocket that you can only LEAVE (ledges `MB_JUMP_WEST` at x=28 y=49..54 and
   `MB_JUMP_SOUTH` at (29,55) and (31..33,57)). The pocket is reachable only by walking OUT of the Woods' SE exit.
   The Route 104 **Poké Ball item ball (29,53)** is inside that pocket. **MODEL** (ledge behaviours, collision bits
   and the warps are VERIFIED in `Route104/map.json` warps[2..7] and the layout). Agent 05 found the same independently.
2. **The Woods scene is unavoidable going north, and it is the only fight that matters there.** The trigger is the
   two-tile corridor (26,23)/(27,23) (`coord_events`, `VAR_PETALBURG_WOODS_STATE == 0`). Every northbound path
   crosses it (MODEL), and there is no other way north: the x=12..15 passage has a south-only ledge at y=22.
   Grunt: **POOCHYENA L9** (`trainer_parties.h:103`). The researcher gives a **GREAT BALL** with **no flag**; the
   proof is `VAR_PETALBURG_WOODS_STATE` going 0 → 1 (`PetalburgWoods/scripts.inc:92`). **VERIFIED.**
3. **The Gina & Mia twins (double battle) block the only bridge to Rustboro, but only if the party has 2 usable
   Pokémon.** With exactly one non-egg Pokémon that has HP > 0, they never engage on sight
   (`trainer_see.c` `CheckTrainer`, `pokemon.c:4527-4544`). Facing down, sight 1. The bridge row y=16 at x=27/28 is
   the only crossing (MODEL). Talking to them with one usable Pokémon gives `Route104_Text_GinaNotEnoughMons`.
   **VERIFIED** (the rule). An A/B with 1 vs 2 usable Pokémon has arms that really differ.
4. **Beating ROXANNE marks JOSH, TOMMY and MARC as defeated** (`settrainerflag`, `data/scripts/set_gym_trainers.inc:12-16`,
   called at `RustboroCity_Gym/scripts.inc:23`). ⇒ **A proof that "the AI fought the gym trainers" can never rest
   on their trainer flags after the badge: they are set either way.** Check the flags BEFORE Roxanne, or count the
   battles. Skipped gym trainers are gone for good, with their EXP. **VERIFIED.**
5. **`ai_player/knowledge/milestones.json` `ch4_gym_trainers` lists only JOSH and TOMMY. It is missing MARC**
   (HIKER, `TRAINER_MARC` = 571, flag 0x73B = 1851, 2× GEODUDE L8, at (1,6)). **VERIFIED** (read-only
   cross-check of our file; `RustboroCity_Gym/map.json` obj[4], `scripts.inc:51-54`).
6. **Gym tile (1,9) is seen by BOTH Tommy (facing W, range 3) and Marc (facing S, range 3).** With 2 usable Pokémon
   and both trainers undefeated, stepping there starts a two-trainer DOUBLE battle (4× GEODUDE L8)
   (`trainer_see.c:191-233` `CheckForTrainersWantingBattle`). **VERIFIED** (the rule), **MODEL** (the overlap).
   Agent 05 found the same.
7. **Gifts in chapters 3-4 that need NO condition:** QUICK CLAW (Trainer's School teacher), HM01 CUT (Cutter),
   TM09 BULLET SEED (Route 104 boy), CHESTO BERRY (Route 104 north woman), WAILMER PAIL plus a daily random berry
   (flower shop), GREAT BALL (Woods researcher), TM39 ROCK TOMB (Roxanne). **VERIFIED.**
   **AMULET COIN is NOT in these chapters:** Mom gives it after `FLAG_BADGE05_GET` (`players_house.inc:307-317`).
   **BLACK GLASSES is NOT reachable either:** it is a hidden item at Route 116 (70,13), east of the Rusturf Tunnel
   (MODEL: not reachable on foot from Rustboro). **VERIFIED** (location).
8. **The MIRACLE SEED girl, the Woods GREAT BALL item and the X ATTACK item are behind the two Cut trees** at Woods
   (19,10)/(19,11) (MODEL). Using Cut in the field needs `FLAG_BADGE01_GET` (`party_menu.c:120,3725`). The girl's
   line mentions "the BADGE from RUSTBORO GYM", but her script does not check the badge (`scripts.inc:229-238`); the
   trees are the only gate. The same holds for the Route 104 **X ACCURACY** (37,22), behind the tree (35,22).
9. **Right after the badge, leaving the gym fires the Devon "goods stolen" scene.** Roxanne sets
   `VAR_RUSTBORO_CITY_STATE = 1` (`Gym/scripts.inc:20`), and the coord triggers at (23,20..24) fire at state 1.
   From the gym door, every path to the rest of the city crosses x=23 (MODEL). Plan the chapter-4 end state
   around it: it is the first beat of chapter 5.
10. **No rival battle happens in chapters 3-4.** The Rustboro and Route 104 rivals start hidden
    (`new_game.inc:129,231`) and appear only after the PokéNav (Devon 3F, `scripts.inc:66`). **VERIFIED.**

---

## 1. Map graph: connections and warps (VERIFIED, `data/maps/<MAP>/map.json`)

| From | How | To |
|---|---|---|
| PETALBURG_CITY | west edge (Petalburg `left` offset -50 ↔ Route 104 `right` offset 50) | ROUTE104 x=39, y≥50 |
| ROUTE104 | `up`, offset 0 | RUSTBORO_CITY (bottom edge) |
| ROUTE104 | `down` | ROUTE105 (sea; needs Surf) |
| ROUTE104 (17,50) | warp 0 | Mr. Briney's cottage |
| ROUTE104 (5,18) | warp 1 | Pretty Petal Flower Shop |
| ROUTE104 (10,30)/(11,30) | warps 2,3 (`MB_DEEP_SOUTH_WARP`) | PETALBURG_WOODS north door (14,5)/(15,5) |
| ROUTE104 (10,38)/(11,38) | warps 4,5 (`MB_NON_ANIMATED_DOOR`) | Woods SW door (16,38)/(17,38) |
| ROUTE104 (32,42)/(33,42) | warps 6,7 | Woods SE door (36,38)/(37,38). Exit-only pocket, see §0.1 |
| RUSTBORO_CITY | `up` / `right` | ROUTE115 / ROUTE116 |
| RUSTBORO (27,19) | warp 0, animated door (collision 1: press UP from (27,20)) | RUSTBORO_CITY_GYM (5,19)/(6,19) |
| RUSTBORO (16,38) | warp 3, animated door; heal location (16,39) | Pokémon Center 1F |
| RUSTBORO (16,45) | warp 2, animated door | Mart |
| RUSTBORO (27,34) | warp 4, animated door | Trainer's School |
| RUSTBORO (9,38) | warp 8, animated door | Cutter's house |
| RUSTBORO (11,15)/(12,15) | warps 5,6, non-animated (walk on) | Devon Corp 1F |
| RUSTBORO (33,19) / (30,28) / (26,46) / (13,30) / (5,51) | warps 7, 9, 11, 1, 10 | House1 (trade) / House2 / House3 / Flat1 / Flat2 |

- Door kinds come from the metatile behaviour: `MB_ANIMATED_DOOR` tiles have collision 1 and are entered by
  pressing UP from the tile below. **VERIFIED** (layout bits via my probe; the rule is UNVERIFIED-in-code, but it
  matches `TryDoorWarp`).
- Rustboro heal location: `HEAL_LOCATION_RUSTBORO_CITY` = (16,39) (`src/data/heal_locations.json`). Entering the
  Pokémon Center sets it (`setrespawn`, `RustboroCity_PokemonCenter_1F/scripts.inc:7`). **VERIFIED.**
- Losing any of these trainer battles means a whiteout (`battle_setup.c:1333-1338` `CB2_EndTrainerBattle`) to the
  last Pokémon Center entered. **VERIFIED.** For the Woods grunt, `VAR_PETALBURG_WOODS_STATE` stays 0, so the scene
  replays on the next pass.

---

## 2. Route 104 south (Petalburg → Woods) (VERIFIED `Route104/map.json`, `scripts.inc`)

**Trainers** (full table in §7): **CINDY** (Lady) at (11,44), next to the SW Woods door; **BILLY** (Youngster), who
walks a loop from (18,67) (`WALK_SEQUENCE_DOWN_RIGHT_UP_LEFT`, range 5×6; agent 05 simulated the loop); **DARIAN**
(Fisherman) at (15,59) with sight 0, so he is talk-only and never approaches.

**Mr. Briney's cottage (17,50):** it is **EMPTY in chapters 3-4**. `FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY` and `_PEEKO` are
set at New Game (`data/scripts/new_game.inc:132-133`). Entering sets `FLAG_LANDMARK_MR_BRINEY_HOUSE`
(`Route104_MrBrineysHouse/scripts.inc:6`). The boat object (12,54) is visible: `FLAG_HIDE_ROUTE_104_MR_BRINEY_BOAT` is
not set at New Game. Briney himself (12,51) is hidden (`new_game.inc:134`). Sign at (20,50): "MR. BRINEY'S COTTAGE".

**Items:**
- Poké Ball item ball (29,53), `FLAG_ITEM_ROUTE_104_POKE_BALL` (0x421). It is in the exit-only SE pocket (§0.1).
- Hidden: POTION (14,55) `FLAG_HIDDEN_ITEM_ROUTE_104_POTION`; ANTIDOTE (16,72) `..._ANTIDOTE`; HEART SCALE (16,64)
  `..._HEART_SCALE`. All are reachable on foot (MODEL).
- Berry trees at (22..24,41): ORAN_2 and PECHA have berries from New Game, SOIL_3 is empty (`new_game.inc:7-8`).

**Wandering NPC hints** (dialogue): Girl1 (25,49) says "That seaside cottage is where MR. BRINEY lives". Boy1 (27,63)
says weaken a wild Pokémon before throwing a ball. Woman (30,50) is in the SE pocket. Girl2 (28,74) says
"if TRAINERS lock eyes, it's a challenge … stay out of their sight". Route sign (27,66) reads "ROUTE 104 → PETALBURG CITY".

## 3. Petalburg Woods (VERIFIED `PetalburgWoods/map.json`, `scripts.inc`)

- **The scene** (`scripts.inc:4-94`). Triggers at (26,23) (Left) and (27,23) (Right) while `VAR_PETALBURG_WOODS_STATE == 0`.
  The researcher (MAN_2, (26,20), `LOCALID_PETALBURG_WOODS_DEVON_EMPLOYEE`) asks about SHROOMISH. The grunt
  (AQUA_MEMBER_M, (26,17)) walks in and battles with `trainerbattle_no_intro TRAINER_GRUNT_PETALBURG_WOODS`
  (POOCHYENA L9, iv 0). Then: `removeobject` on both. That sets their object flags `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT`
  (0x2D5) and `FLAG_HIDE_PETALBURG_WOODS_DEVON_EMPLOYEE` (0x2D4) (`event_object_movement.c:1389-1397`). The researcher
  gives a **GREAT BALL** (`giveitem`, no flag, `:73`; if the bag is full he says so and gives nothing, `:78-81`).
  `VAR_PETALBURG_WOODS_STATE = 1` (`:92`). The trainer flag 0x50A (= 1290) is set on a win (`battle_setup.c:1264`).
- Both NPCs are **visible from New Game**: neither hide flag is in `EventScript_ResetAllMapFlags` (`new_game.inc:115-`).
  Talking to them before the trigger does nothing (`script 0x0`).
- Dialogue the AI hears: the grunt says "we of TEAM AQUA are also after something in RUSTBORO"
  (`PetalburgWoods_Text_YouveGotSomeNerve`, `:333-341`). The researcher says "Didn't that TEAM AQUA thug say they were
  after something in RUSTBORO, too?" (`PetalburgWoods_Text_TeamAquaAfterSomethingInRustboro`, `:351-354`).
- **Trainers:** **LYLE** (Bug Catcher, (7,32), faces D/L/R, sight 3): 4× WURMPLE L3. **JAMES** (Bug Catcher, (4,14),
  faces D/U/R, sight 3): 2× NINCADA L6. Every northbound path crosses one of the lines each of them can face
  (MODEL). Because they turn, a human can slip past by timing. Treat them as "usually fought".
- **Gift:** the MIRACLE SEED girl (GIRL_2, (33,5)), `FLAG_RECEIVED_MIRACLE_SEED` (0x129), unconditional script, but she
  stands behind the Cut trees (§0.8).
- **Item balls:** ETHER (4,8) `FLAG_ITEM_PETALBURG_WOODS_ETHER` 0x422, reachable. PARALYZE HEAL (4,26) `..._PARALYZE_HEAL`
  0x45D, reachable. GREAT BALL (45,7) 0x420 and X ATTACK (35,20) 0x41F are behind Cut.
- **Hidden:** POTION (39,35), reachable. POKé BALL (4,19), reachable. TINY MUSHROOM (26,6) and (40,29) are NOT
  reachable without Cut (MODEL).
- **Signs:** TRAINER TIPS (14,32): put a weak Pokémon first and switch it out to share EXP. TRAINER TIPS (11,8): PP.
  NPC Boy2 (30,34): "things on the ground even if you can't see them". Boy1 (15,19): stay out of tall grass if weak.
- Map flags: `allow_escaping: false` (`map.json:11`); weather `WEATHER_SHADE`.

## 4. Route 104 north (Woods north door → Rustboro) (VERIFIED)

- **Trainers:** **HALEY** (Lass, (31,24), faces W, sight 7). **WINSTON** (Rich Boy, (21,25), `ROTATE_COUNTERCLOCKWISE`,
  sight 3): every northbound path crosses one of his lines, so pass by timing. **GINA & MIA** (Twins, (27,15)/(28,15),
  double, see §0.3). **IVAN** (Fisherman, (29,8), sight 0, talk-only).
- **Gifts:** **TM09 BULLET SEED**, Boy2 (5,26), `FLAG_RECEIVED_TM_BULLET_SEED` (0x106), unconditional (`scripts.inc:317-326`).
  **CHESTO BERRY**, Expert F (37,8), `FLAG_RECEIVED_CHESTO_BERRY_ROUTE_104` (0xF6), unconditional (`:248-258`).
  The WHITE HERB florist (8,19) is hidden until `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` AND `FLAG_BADGE03_GET` (`:21-29`),
  so she is not in these chapters.
- **Pretty Petal Flower Shop** (door (5,18); `Route104_PrettyPetalFlowerShop/scripts.inc`):
  - Entering sets `FLAG_LANDMARK_FLOWER_SHOP`.
  - The owner (0,3), first talk, sets `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` (0x7F) and offers to explain berries (YES/NO).
    She sells decorations only after badge 3 (`:5-10,44-50`).
  - Wailmer Pail girl (7,3): **WAILMER PAIL** (key item), `FLAG_RECEIVED_WAILMER_PAIL` (0x5E), unconditional (`:62-76`).
  - Random-berry girl (11,6): a random one of CHERI..PERSIM, once per day, `FLAG_DAILY_FLOWER_SHOP_RECEIVED_BERRY`
    (`:78-91`; `random 8` + `FIRST_BERRY_INDEX`, order in `items.h:152-159`).
- **Items:** POTION (5,8) `FLAG_ITEM_ROUTE_104_POTION` 0x46F, reachable. **PP UP (39,15)** `..._PP_UP` 0x3EA: NOT
  reachable on foot; it is on a water-locked island, so Surf (MODEL). **X ACCURACY (37,22)** `..._X_ACCURACY` 0x45B:
  behind the Cut tree (35,22).
- **Hidden:** SUPER POTION (7,6) and POKé BALL (3,9), both reachable.
- **Berry trees:** CHERI_1 (34,6), LEPPA (36,6), ORAN_1 (3,23) and CHERI_2 (3,25) have berries from New Game
  (`new_game.inc:9-12`). SOIL_1/2/4 are empty.
- **Signs:** "TRAINER TIPS: DOUBLE BATTLES … the one at the left of the list and the top one" (17,23). "ROUTE 104 ↑
  RUSTBORO CITY" (23,5). "PRETTY PETAL FLOWER SHOP" (7,20).
- The rival trigger (17,51) and the hidden rival need `VAR_ROUTE104_STATE == 1`, which is set only by the PokéNav
  scene (`RustboroCity/scripts.inc:33`). Not in chapters 3-4.

## 5. Rustboro City (VERIFIED `RustboroCity/map.json`, `scripts.inc`)

- **Arrival:** `FLAG_VISITED_RUSTBORO_CITY` (system flag, 0x879 = 2169) is set on map transition (`scripts.inc:7`).
  `VAR_RUSTBORO_CITY_STATE` is 0, and no coord trigger fires at 0 (the triggers need 1, 2, 4 or 7). **Arrival is quiet.**
  No wild encounters in the city (no `MAP_RUSTBORO_CITY` entry in `wild_encounters.json`).
- **Not interactable in these chapters:** the Aqua grunt (13,21), Devon Employee 1 (30,10), the rival (16,50) and the
  scientist (11,15). All are hidden by `new_game.inc:127-130`.
- **Pokémon Center 1F:** the nurse heals; `setrespawn HEAL_LOCATION_RUSTBORO_CITY`.
- **Mart** (`RustboroCity_Mart/scripts.inc:4-46`): before `FLAG_MET_DEVON_EMPLOYEE` (set on Route 116, `Route116/scripts.inc:55`)
  it sells Poké Ball, Potion, Super Potion, Antidote, Paralyze Heal, Escape Rope, Repel, X Speed, X Attack, X Defend.
- **Trainer's School** (door (27,34)):
  - The teacher (GENTLEMAN, (5,3)) gives the **QUICK CLAW**. `FLAG_RECEIVED_QUICK_CLAW` (0x113). **The only condition is
    "not received yet"** (`RustboroCity_PokemonSchool/scripts.inc:77-90`). If the player talks to him from the side
    (`VAR_FACING` E/W), he first walks a "check on students" loop. Bag full → `Common_EventScript_ShowBagIsFull`.
  - Blackboard (4..7,2): a status-condition menu (5 topics). Notebook (3,5).
  - **SCOTT** is in the school (0,10) from New Game. His hide flag is not in `ResetAllMapFlags`; it is set later at
    Devon 3F `:55`. Talking to him sets `FLAG_MET_SCOTT_RUSTBORO` (0x136), `VAR_SCOTT_STATE += 1` (`:159-169`). With the
    badge: `FLAG_MET_SCOTT_AFTER_OBTAINING_STONE_BADGE` (0x1CB). It is optional flavour.
- **Cutter's house** (door (9,38)): POKEFAN_M (7,5) gives **HM01 CUT** unconditionally, `FLAG_RECEIVED_HM_CUT` (0x89)
  (`RustboroCity_CuttersHouse/scripts.inc:4-13`). Field use needs the Stone Badge (`party_menu.c:3725`).
- **Devon Corp 1F:** the stair guard blocks the stairs until `FLAG_RETURNED_DEVON_GOODS` (`DevonCorp_1F/scripts.inc:6`).
  Upstairs is not reachable in these chapters.
- **House1** (33,19): an in-game trade, your RALTS for SEEDOT "DOTS" holding a CHESTO BERRY, OT KOBE
  (`House1/scripts.inc:4-26`, `src/data/trade.h` ~987-1001), `FLAG_RUSTBORO_NPC_TRADE_COMPLETED`.
- **Item ball:** X DEFEND (36,51), `FLAG_ITEM_RUSTBORO_CITY_X_DEFEND` (0x411), reachable (MODEL).
- **Dialogue hints** (§12): the Woman (22,34) says FIRE is bad against ROCK. Man1 (26,23) asks whether you have taken
  the GYM challenge. The gym sign (23,19) reads "LEADER: ROXANNE … The ROCK-loving honors student!" Boy2 (12,45):
  Mr. Briney walks in the tunnel.

## 6. Rustboro Gym and ROXANNE (VERIFIED `RustboroCity_Gym/map.json`, `scripts.inc`, `trainers.h`, `trainer_parties.h`)

- **Layout:** entrance (5,19)/(6,19); ROXANNE at (5,2) facing down. Talk from (5,3) facing up. Gym guide (MAN_2) at
  (3,18): ROXANNE uses ROCK; "it can't stand WATER-type and GRASS-type moves" (`scripts.inc:106-126`).
  Statues (2,18)/(8,18) show "certified" text once the badge is earned.
- **Gym trainers** (all `trainerbattle_single`):
  - **JOSH** (Youngster, (5,13), faces S, sight 2): GEODUDE L10, moves {TACKLE}.
  - **TOMMY** (Youngster, (3,9), faces W, sight 3): 2× GEODUDE L8.
  - **MARC** (Hiker, (1,6), faces S, sight 3): 2× GEODUDE L8.
  - All three can be avoided: an entrance-to-(5,3) path that touches no sight line exists, 30 steps against a shortest
    24 (MODEL). Tile (1,9) is the two-trainer trap (§0.6).
- **ROXANNE** (`TRAINER_ROXANNE_1`, `trainers.h:3184`, `trainer_parties.h:3367`). AI: CHECK_BAD_MOVE | TRY_TO_FAINT |
  CHECK_VIABILITY. Trainer items: **2× POTION**. Party:
  - GEODUDE L12, iv 100: TACKLE, DEFENSE CURL, ROCK THROW, ROCK TOMB.
  - GEODUDE L12, iv 100: same moves.
  - **NOSEPASS L15**, iv 200, holding an **ORAN BERRY**: BLOCK, HARDEN, TACKLE, ROCK TOMB.

  `trainerbattle_single … RustboroCity_Gym_EventScript_RoxanneDefeated, NO_MUSIC` (`scripts.inc:5`).
- **On victory** (`scripts.inc:13-34`), in order:
  - The STONE BADGE message.
  - `setflag FLAG_DEFEATED_RUSTBORO_GYM` (0x4F0 = 1264) and `setflag FLAG_BADGE01_GET` (0x867 = 2151).
  - `VAR_RUSTBORO_CITY_STATE = 1`; `VAR_PETALBURG_GYM_STATE += 1`; `VAR_0x8008 = 1`.
  - `Common_EventScript_SetGymTrainers`, which marks Josh, Tommy and Marc defeated (§0.4).
  - **TM39 ROCK TOMB**: `giveitem ITEM_TM_ROCK_TOMB`, then `FLAG_RECEIVED_TM_ROCK_TOMB` (0xA5).
  - ⚠ If the bag is full at that moment, the TM is skipped and the flag stays clear. Talking to Roxanne again retries
    (`:8`). That is a small edge case for a proof.
- Trainer flag numbers: TRAINER_FLAGS_START 0x500 + id (`flags.h:1343`, `battle_setup.c:1259-1264`).
  ROXANNE 0x609 (1545), JOSH 0x640 (1600), TOMMY 0x641 (1601), MARC 0x73B (1851).

## 7. Every trainer in chapters 3-4 (VERIFIED: `map.json` object, `scripts.inc` battle line, `trainers.h`, `trainer_parties.h`)

| Trainer (id → flag) | Class | Where | Facing / sight | Battle | Team |
|---|---|---|---|---|---|
| CINDY_1 (114 → 0x572) | Lady | R104 (11,44) | up+right / 3 | single; trainer item FULL RESTORE | ZIGZAGOON L7 @NUGGET |
| BILLY (319 → 0x63F) | Youngster | R104 (18,67), walks a loop | all / 2 | single | ZIGZAGOON L5, SEEDOT L7 |
| DARIAN (696 → 0x7B8) | Fisherman | R104 (15,59) | left / **0** (talk-only) | single | MAGIKARP L9 |
| GRUNT_PETALBURG_WOODS (10 → 0x50A) | Team Aqua | Woods, scripted | n/a | `no_intro`, forced | POOCHYENA L9 |
| LYLE (616 → 0x768) | Bug Catcher | Woods (7,32) | D/L/R / 3 | single | WURMPLE L3 ×4 |
| JAMES_1 (621 → 0x76D) | Bug Catcher | Woods (4,14) | D/U/R / 3 | single | NINCADA L6 ×2 |
| HALEY_1 (604 → 0x75C) | Lass | R104 (31,24) | left / 7 | single | LOTAD L6, SHROOMISH L6 |
| WINSTON_1 (136 → 0x588) | Rich Boy | R104 (21,25) | rotating / 3 | single; trainer item FULL RESTORE | ZIGZAGOON L7 @NUGGET |
| GINA_AND_MIA_1 (483 → 0x6E3) | Twins | R104 (27,15)+(28,15) | down / 1 | **DOUBLE** (needs 2 usable mons) | SEEDOT L6, LOTAD L6 |
| IVAN (337 → 0x651) | Fisherman | R104 (29,8) | down / **0** (talk-only) | single | MAGIKARP L5, L6, L7 |
| JOSH (320 → 0x640) | Youngster | Gym (5,13) | down / 2 | single | GEODUDE L10 (TACKLE) |
| TOMMY (321 → 0x641) | Youngster | Gym (3,9) | left / 3 | single | GEODUDE L8 ×2 |
| MARC (571 → 0x73B) | Hiker | Gym (1,6) | down / 3 | single | GEODUDE L8 ×2 |
| ROXANNE_1 (265 → 0x609) | Leader | Gym (5,2) | n/a (talk) | single; 2× POTION | GEODUDE L12 ×2, NOSEPASS L15 @ORAN |

- Not in these chapters: the rival battles at Route 104 (17,51) and Rustboro (16,50) (`TRAINER_{MAY,BRENDAN}_RUSTBORO_*`:
  a starter-counter at L13 plus the rival's starter at L15). They become reachable only after the PokéNav.
- UNVERIFIED: whether and when CINDY or WINSTON actually use their FULL RESTORE. That is battle-AI item logic, which
  I did not read.
- Rematch fields (Haley, Winston, Cindy, James) register for Match Call only if `FLAG_HAS_MATCH_CALL` is set. It is
  set at the PokéNav scene, so it does not apply in these chapters.

## 8. Wild encounters (VERIFIED `src/data/wild_encounters.json`, `gWildMonHeaders`)

| Map (json line) | Table / rate | Species (summed slot %) and levels |
|---|---|---|
| ROUTE104 (416) | land, 20 | POOCHYENA 40% (L4-5), WURMPLE 20% (L4), MARILL 20% (L4-5), TAILLOW 10% (L4-5), WINGULL 10% (L3-5) |
| ROUTE104 | water (Surf), 4 | WINGULL 95% (L10-30), PELIPPER 5% (L25-30). Not in these chapters (no Surf) |
| ROUTE104 | fishing, 30 | **MAGIKARP in all 10 slots** (old rod L5-10; good rod L10-30; super rod L20-45). No rod in these chapters (UNVERIFIED where the first rod comes from) |
| PETALBURG_WOODS (1785) | land, 20 | POOCHYENA 30% (L5-6), WURMPLE 25% (L5-6), SHROOMISH 15% (L5-6), SILCOON 10% (L5), CASCOON 10% (L5), TAILLOW 5% (L5-6), **SLAKOTH 5%** (L5-6) |
| PETALBURG_WOODS | water / fishing | none |
| RUSTBORO_CITY | any | none |

Slot rates are `20,20,10,10,10,10,5,5,4,4,1,1` (land) and `60,30,5,4,1` (water). The fishing groups are old 70/30,
good 60/20/20, super 40/40/15/4/1 (the json `fields`). For catching (RULING 33), SHROOMISH (Woods) and MARILL (Route
104) are GRASS and WATER types against ROXANNE. The type facts are general knowledge, UNVERIFIED in `types.json`.

## 9. Flags and vars a proof can read (VERIFIED: values from `include/constants/flags.h` / `vars.h`)

| Name | Value | Set by | Notes |
|---|---|---|---|
| `VAR_PETALBURG_WOODS_STATE` | 0x4098 (16536) | Woods scene end, `:92` → 1 | The ONLY save proof that Route 104 south and the Woods were walked |
| `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT` / `_DEVON_EMPLOYEE` | 0x2D5 / 0x2D4 | `removeobject` in the scene | A second, independent witness of the scene |
| Grunt trainer flag | 0x50A (1290) | Win only | A loss means a whiteout and the var stays 0 |
| `FLAG_VISITED_RUSTBORO_CITY` | 0x879 (2169) | Rustboro on-transition | |
| `FLAG_RECEIVED_QUICK_CLAW` | 0x113 | School teacher | |
| `FLAG_RECEIVED_HM_CUT` | 0x89 | Cutter | |
| `FLAG_RECEIVED_TM_BULLET_SEED` | 0x106 | Route 104 boy (5,26) | |
| `FLAG_RECEIVED_CHESTO_BERRY_ROUTE_104` | 0xF6 | Route 104 woman (37,8) | |
| `FLAG_RECEIVED_WAILMER_PAIL` | 0x5E | Flower shop girl | |
| `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` | 0x7F | Flower shop owner | |
| `FLAG_RECEIVED_MIRACLE_SEED` | 0x129 | Woods girl (behind Cut) | |
| `FLAG_MET_SCOTT_RUSTBORO` | 0x136 | Scott in the school | Optional |
| `FLAG_DEFEATED_RUSTBORO_GYM` | 0x4F0 (1264) | Roxanne win | |
| `FLAG_BADGE01_GET` | 0x867 (2151) | Roxanne win | |
| `FLAG_RECEIVED_TM_ROCK_TOMB` | 0xA5 | Roxanne win, if the bag has room | |
| `VAR_RUSTBORO_CITY_STATE` | 0x405A | 0 → 1 at Roxanne win | 1 arms the stolen-goods triggers (§0.9) |
| `VAR_PETALBURG_GYM_STATE` | 0x4085 | +1 at Roxanne win | |
| Item-ball flags | see §2-5 | Picking up the ball | |
| Hidden-item flags | `FLAG_HIDDEN_ITEM_ROUTE_104_*`, `FLAG_HIDDEN_ITEM_PETALBURG_WOODS_*` | Finding the item | |

## 10. Static reachability and step counts (MODEL, developer-only)

Method: my scratch script reads `map.bin` for collision (bits 10-11) and elevation (bits 12-15), plus the metatile
behaviours. The script is `ch34a_paths.py`, in the session scratchpad, which is not kept, so rerun it from this
description if needed. The rules it mirrors:
- `GetCollisionAtCoords`, `IsElevationMismatchAt` and `ObjectEventUpdateElevation`: `event_object_movement.c:4641-4654, 7673-7737`.
- Directional blocks: `metatile_behavior.c:933-977`.
- Ledges, which have collision 1 and are jumped only in their own direction: `field_player_avatar.c:744-750`.
- Trainer sight and the clear-path check: `trainer_see.c:301-405`.

Objects block their spawn tile, and hide flags follow New Game.

| Segment | Shortest | Avoid-all-sight path | Must-cross |
|---|---|---|---|
| Petalburg edge → Woods SW door (10/11,38) | 51 | 52 (dodge CINDY via column x=10) | none |
| Woods SW door → north door | 85 | none if turning trainers can face any way | LYLE row 32, JAMES row 14 (timing); event (26/27,23) |
| Woods SE door → north door | 105 | same | same |
| Woods north exit (10/11,30) → Rustboro edge | 54 | none with 2 usable mons (twins) | twins (2 mons only); WINSTON column x=21 (timing) |
| Rustboro south edge → gym tile (27,20) | 47 | | |
| Rustboro south edge → Pokémon Center (16,39) | 23 | | |
| Rustboro south edge → School (27,35) | 32 | | |
| Rustboro south edge → Cutter (9,39) | 23 | | |
| Rustboro Pokémon Center → gym | 30 | | |
| Gym entrance → (5,3) | 24 | 30 (avoids JOSH, TOMMY, MARC) | none |

- **Minimum walk for the whole of chapters 3-4: about 51 + 85 + 54 + 47 + 24 = 261 steps.** That excludes
  battles, turning and errands. It is a baseline for the AI's steps-vs-shortest metric.
- ⚠ The model freezes wanderers and turners. LYLE, JAMES, WINSTON and CINDY turn, and BILLY patrols. "Must-cross"
  means "a line one of their facings covers", not "a guaranteed battle".

## 11. Cross-check against our tree (read-only)

`ai_player/knowledge/milestones.json`:
- `PETALBURG_WOODS_STATE` 16536, `VISITED_RUSTBORO_CITY` 2169, `DEFEATED_RUSTBORO_GYM` 1264 and `BADGE01_GET` 2151 all
  match.
- The trainer ids and flags for GRUNT (10/1290), JOSH (320/1600), TOMMY (321/1601) and ROXANNE_1 (265/1545) all match,
  and so do the levels.
- **Mismatch:** MARC is absent from `ch4_gym_trainers` (§0.5).
- **Trap:** `ch4_gym_trainers` "done" uses trainer flags that ROXANNE's win sets anyway (§0.4).
- Chapter 3 has no milestone for the free gifts (Quick Claw, Bullet Seed, Chesto, Wailmer Pail, HM01) or the optional
  Route 104 and Woods trainers. That is a gap if RULING 33's "gift items" is to be measured.

## 12. What the GAME tells a player (the only hints the AI may use)

- Dad (chapter 2): head for RUSTBORO CITY and challenge ROXANNE (already used by `milestones.json`).
- Route 104 sign (27,66): "ROUTE 104 → PETALBURG CITY". Sign (23,5): "ROUTE 104 ↑ RUSTBORO CITY".
- Route 104 Girl2: if TRAINERS lock eyes, it is a battle; stay out of their sight.
- Woods grunt and researcher: TEAM AQUA is "after something in RUSTBORO".
- Woods TRAINER TIPS (14,32): lead with a weak Pokémon and switch it out to share EXP.
- Rustboro Woman: FIRE does not match up well against ROCK. Gym sign: "ROCK-loving honors student". Gym guide: ROCK
  "can't stand WATER-type and GRASS-type moves".
- Teacher: "Students who don't study get a little taste of my QUICK CLAW". The Cutter hands over HM01 after
  `RustboroCity_CuttersHouse_Text_YouCanPutThisHMToGoodUse`. The TRAINER TIPS sign on Route 104 (17,23) explains
  DOUBLE BATTLES.

## 13. Tool hazard found while doing this (for every agent fetching the decomp)

`gh api repos/pret/pokeemerald/contents/<binary>.bin` mangles some binaries. This applies both to the raw media type
and to the JSON `content` base64. The bytes come back as UTF-8 with replacement characters:
`PetalburgWoods/map.bin` returned 5914 bytes instead of 4224, and `PetalburgCity/map.bin` returned 2528 instead of
1800. **Fetch binaries by blob sha** (`gh api repos/pret/pokeemerald/git/blobs/<sha>`, then decode the base64) and
check the length against the blob's `size`. Text files are unaffected. Any layout-based result computed from a
mangled `.bin` is wrong.

## 14. Open items to confirm live (cheap, decisive)

1. The twins A/B: 1 usable Pokémon vs 2 crossing (27/28,16). The arms differ by construction (§0.3).
2. Gym (1,9) with 2 usable Pokémon: expect a Tommy + Marc two-trainer double.
3. After Roxanne, read the trainer flags 0x640, 0x641 and 0x73B without ever fighting them: expect all set (§0.4).
   That is the fault arm for any "fought the gym trainers" proof.
4. The post-badge exit: expect the stolen-goods scene on crossing x=23 at y 20..24.
5. Whether FLAG_TEMP_11/12 (the Cut trees) reset on map load, so the trees regrow. UNVERIFIED here.
