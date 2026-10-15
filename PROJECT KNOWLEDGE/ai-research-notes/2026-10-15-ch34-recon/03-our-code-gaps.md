# 03: our AI player's gaps for chapters 3-4 (a read-only audit)

**Status: a NOTE, not truth.** Written 2026-10-15 by a Claude research subagent (angle 03, "audit our code"). Nothing was
run in the emulator. Every claim carries one of four tags:
* **VERIFIED-code**: I read it in our tree. The `file:line` refers to the working copy on 2026-10-15, with step 5.1 uncommitted.
* **VERIFIED-decomp**: I read it in pret/pokeemerald through `gh api`.
* **MODEL**: a breadth-first search over pret's `map.bin` (collision, elevation, metatile behaviour) plus `map.json` objects.
  It is not the game: moving NPCs are frozen where map.json puts them, and a rotating trainer counts as looking every way.
* **UNVERIFIED**: an inference or an estimate.

**Person-fair (USER RULINGS 35-37).** Every coordinate, sight line and route in this file is for DEVELOPERS: for designing
proofs, fixtures and pre-registered expectations. None of it may be given to the AI as a hint. The AI may only use what the
game's dialogue and signs say. Where a gap below needs knowledge the AI does not have, the fix must come from that kind of
in-game source (marked "person-fair source").

The scratch scripts that produced the MODEL results are in this session's scratchpad: `audit03_reach.py`,
`audit03_halves.py`, `audit03_doors.py`, `audit03_warplooks.py` and `audit03_parties.py`. They are not part of the repo.

---

## 0. The gaps, ranked by how likely each is to STOP a run

| # | Gap | Where | Likelihood of stopping a run |
|---|-----|-------|------------------------------|
| 1 | **ROUTE 104 is one map with two halves that are NOT joined on foot. The only land link is PETALBURG WOODS, and the goal manager treats the woods as an INTERIOR.** After the woods scene, the next "go to RUSTBORO CITY" walks back out of the woods' SOUTH exit. From then on, the woods entrances already used are refused to every travel walk. Healing at Petalburg while training on Route 104 north has the same problem. | `brain/goals.py:432` (the OUTDOOR regex), `:455-485` (`lead_toward`), `:492-502` (`keeps_going`), `:435-452` (`world_distance`), `:1160-1180` (`_nearest_place`), `:1608-1622` (`_travel`); `brain/explore.py:155` (`ROUTE_VALUE` 10), `:174-203` (`route_to`) | **Very high.** Expected end: `play: stuck: no progress for 120000 frames` on Route 104 south (VERIFIED-code + MODEL; the trajectory is UNVERIFIED) |
| 2 | **ROXANNE can end the run.** `MAX_LOSSES` is 3 for the WHOLE run. A loss does not cause more training. Training sessions cut short by a rest still count toward `TRAIN_SESSIONS` 8. Nothing plans a type advantage. | `mode.py:103`, `:559-570`; `brain/goals.py:189`, `:859-877`, `:1064-1067`, `:1474-1481`, `:395-403`; `personality.py:153-163` | **High**, worst for a Torchic and for the Story personality (VERIFIED-code; the levels are an UNVERIFIED estimate) |
| 3 | **The first evolution played live.** All three starters evolve at L16. The Story personality's ROXANNE target is exactly L16, and the others' is 17-18. The README says an evolution has never been played live. | `README.md:2027-2029`; decomp `src/data/pokemon/evolution.h:125-130` | **Medium**: certain to happen in every chapter-4 run; whether it breaks is UNVERIFIED |
| 4 | **The default YES opens a party menu the play brain cannot handle.** The trader in RUSTBORO's House1 asks a yes/no. YES opens `ChoosePartyMon`. `_story_menu` does not know that menu, so the loop replays the screen until the patience runs out. | `skills/story.py:75-91`; `mode.py:572-583`; `brain/navigator.py:1014-1017`; decomp `data/maps/RustboroCity_House1/scripts.inc:12-14` | **Medium**: it needs a CHAT draw with that NPC (Trainer 0.3, Story 0.18, Catcher 0.12) |
| 5 | **Double battles.** The twins on Route 104 north are unavoidable (MODEL) once the party has 2 usable Pokemon. In the gym, one tile is in both TOMMY's and MARC's sight: stepping on it starts a TWO-TRAINER double battle. Doubles have only been played from step-4 fixtures. | `brain/battle.py:851-853`, `:1099-1118`, `:1292-1293`; `skills/battle.py:168-169`, `:368-403`; decomp `src/trainer_see.c:196-240`, `:248-293` | **Low-medium** (the foes are L6-L8) |
| 6 | **Frame budgets are sized for chapters 1-2.** One `go` (9,000 frames, plus at most 2 extensions for battles) is shorter than Petalburg to Rustboro, so more decisions happen INSIDE the woods, which feeds gap 1. The README's runs use `--frames 330000`. | `brain/goals.py:200`, `:252-253`; `README.md:388-389` | Medium as an amplifier of gap 1 (UNVERIFIED) |
| 7 | **The woods' north entrance has the look `DEEP_SOUTH_WARP`.** The eyes call it an exit, but `EXIT_PRESS` has no entry for it. Pressed from the side, it fails and is remembered CLOSED. | `brain/navigator.py:233-237`, `:930-936`; `eyes/view.py:131`, `:201`; decomp Route104 (10,30),(11,30) | Low-medium: only when going back SOUTH through the woods (VERIFIED-code + VERIFIED-decomp layout) |
| 8 | **The milestone data leaves out MARC**, the gym's third trainer. | `knowledge/milestones.json:145-250`, `:1177-1241` | **None**: the milestone is optional. Only the data is wrong |
| 9 | **Route 104 has diagonal ledges.** `world/memory.py:105-107` still says "none on v1's maps". They are treated as walls. | `world/memory.py:105-107` | Low (UNVERIFIED whether the game lets the player walk on them) |
| 10 | **No hidden-item search and no hold-an-item skill.** The Quick Claw would sit in the bag. Gift-givers are met only by a chance CHAT. | `brain/goals.py:896-903`, `:1118-1134` | **None** as a run-stopper; a RULING 33 shortfall (section 3) |

---

## 1. Are the ch3/ch4 milestones right? (question 1)

Everything below was checked against the decomp unless marked otherwise.

| Milestone (`milestones.json`) | Claim | Decomp | Verdict |
|---|---|---|---|
| `ch3_route104` (:1025-1070) | done = `VAR_PETALBURG_WOODS_STATE` (16536) >= 1; a waypoint on ROUTE104 | `include/constants/vars.h:172` gives `0x4098` = 16536. `data/maps/PetalburgWoods/scripts.inc:92` has `setvar VAR_PETALBURG_WOODS_STATE, 1` | VERIFIED. It shares its proof with `ch3_woods`, so it only ever passes as a waypoint (by design: the note at :1058) |
| `ch3_route104` | hint "RUSTBORO CITY", said by DAD | `data/maps/PetalburgCity_Gym/scripts.inc:1197` has "Head for RUSTBORO CITY beyond this town." | VERIFIED |
| `ch3_woods` (:1072-1131) | done = the same var >= 1; fight GRUNT_PETALBURG_WOODS L9 | `PetalburgWoods/scripts.inc:4-30` and `:32-58` (the scene), `:23` and `:51` (`trainerbattle_no_intro`), `:90-94` (var set to 1 AFTER the battle and the GREAT BALL). Party: `src/data/trainer_parties.h:103-109` POOCHYENA L9. Flag 1290 = `0x500` + 10 (`opponents.h`, `flags.h:1343`) | VERIFIED |
| `ch3_woods` | "the scene plays as the player walks through" | `data/maps/PetalburgWoods/map.json` coord_events (26,23) and (27,23), `VAR_PETALBURG_WOODS_STATE` 0 | VERIFIED-decomp. **MODEL: forced.** With those two tiles walled, no south entrance reaches the north exit. Its `follow` step (:1096-1098) is therefore never reached in practice |
| `ch3_woods` | the fight is not "named" (trained for only by levels SEEN) | `goals.py:1049-1062` | VERIFIED-code. The grunt is L9; no training is triggered for it |
| `ch3_rustboro` (:1133-1175) | done = `FLAG_VISITED_RUSTBORO_CITY` 2169; hint "RUSTBORO" from the woods | `flags.h:1348` gives `SYSTEM_FLAGS` 0x860, and `:1380` gives +0x19 = 2169. Words: the grunt "after something in RUSTBORO" (`PetalburgWoods/scripts.inc:~340`) and the researcher "...in RUSTBORO, too?" (`:351-354`) | VERIFIED. (DAD's "RUSTBORO CITY" holds the whole word "RUSTBORO" as well) |
| `ch4_gym_trainers` (:1177-1241) | JOSH L10 (flag 1600), TOMMY L8,L8 (flag 1601) | `trainer_parties.h:4227-4234` and `:4236-4247`; `RustboroCity_Gym/scripts.inc:42-50` | VERIFIED, **but INCOMPLETE**: `RustboroCity_Gym/map.json` has a third trainer, MARC (hiker at (1,6), sight 3, script `:52-55`), `TRAINER_MARC` = 571 (`opponents.h:575`), flag 1851, party GEODUDE L8 x2 (`trainer_parties.h:7649-7660`). The `trainers` table (:145-250) lacks MARC too |
| `ch4_roxanne` (:1243-1308) | done = `FLAG_DEFEATED_RUSTBORO_GYM` 1264 and `FLAG_BADGE01_GET` 2151; levels 12,12,15; named | `flags.h:1319` gives 0x4F0 = 1264, and `:1359` gives 0x860+7 = 2151. Both are set in `RustboroCity_Gym/scripts.inc:13-26`. Party `trainer_parties.h:3367-3389`: GEODUDE L12 x2 (Tackle, Defense Curl, Rock Throw, Rock Tomb) and NOSEPASS L15 (Block, Harden, Tackle, Rock Tomb, **holds an ORAN BERRY**) | VERIFIED |
| `ch4_roxanne` | hint "ROXANNE", said by DAD | `PetalburgCity_Gym/scripts.inc:1200` has "the GYM LEADER, ROXANNE." | VERIFIED |
| looks | gym door 461, POKéMON CENTER door 97, MART door 65 in RUSTBORO | RUSTBORO's `map.bin` at its warps: (27,19) is 461, (16,38) is 97, (16,45) is 65 | VERIFIED (layout read) |
| `roxanne` gfx 125 | `OBJ_EVENT_GFX_ROXANNE` | not re-read (the README says `--verify` checks every gfx id) | UNVERIFIED by me |

**Test-design caveat (VERIFIED-code).** The hint words are kept in the world memory's `heard` set (`world/memory.py:729`,
`:751`). A chapter-3 run started from a bot save, without the chapter-2 run's `world.jsonl`, has never "heard" DAD. It then
explores with no goal map (`goals.py:999-1002`). Carry `AI_PLAYER_WORLD` (or `--world-in`) from the chapter-2 run.

---

## 2. What will break on the way (question 2)

### 2.1 The woods and Route 104's two halves (gap 1, the run-stopper)

Facts:
* ROUTE104 is ONE map, 40x80 (`layouts.json` LAYOUT_ROUTE104). Its six woods warps are in `Route104/map.json`: (10,30) and
  (11,30) on the north side; (10,38), (11,38), (32,42) and (33,42) on the south side. VERIFIED-decomp.
* **MODEL** (`audit03_halves.py`): from the woods' north exit, the walkable region reaches Rustboro's edge (y=0). It does
  NOT reach Petalburg's edge (the connection is at offset 50; rows 61-63 are walkable) or either south entrance. From
  Petalburg's edge, Rustboro's edge and the north exit's stand tile are unreachable. **The halves are joined only through
  PETALBURG_WOODS.**

Our code:
* `OUTDOOR = ^(ROUTE\d+|[A-Z]+_(TOWN|CITY))$` (`goals.py:432`). "PETALBURG_WOODS" does not match, so the goal manager treats
  the woods as an interior. VERIFIED-code.
* **After the scene, the AI walks back south.** The scene sets the var, `moved_on` ends the walk, and the next decision is
  made inside the woods. The current milestone is now `ch3_rustboro`: go to RUSTBORO_CITY. That map has never been visited,
  so `_travel` asks `lead_toward` (`goals.py:1612`). Because the woods are not OUTDOOR, the check at `:473-475` ("out in the
  open with something left to see here") is skipped. `lead_toward` returns the nearest visited outdoor map with something
  left to see: ROUTE104, 1 link away (`:476-485`). The walk to ROUTE104 then finds a KNOWN route through the warp it came in
  by. That route is scored at `ROUTE_VALUE` 10 (x10, `explore.py:155`, `:288-289`), against 0.6-0.8 for an unused exit such
  as the north one (`:150-152`, `:290-291`). Result: it walks out through the SOUTH entrance. VERIFIED-code; the trajectory
  is UNVERIFIED.
* **Back on Route 104 south, the woods are refused.** `keeps_going` drops every "back" exit whose inside map is not OUTDOOR
  and is not the goal (`goals.py:492-502`), so the entrance just used is no option. Only an unused second entrance is left.
  Once both are used, the travel walk enters the woods only through the explorer's fallback (`goals.py:523-524`), when
  nothing else is left on Route 104 south. **Expected end: STORY_PATIENCE** (`mode.py:102`, `:451-454`): Route 104 south is
  not a new map, so it resets nothing.
* **Even after Rustboro is known, crossing south to north still breaks.** `route_to` (`explore.py:174-203`) and
  `world_distance` (`goals.py:435-452`) see ROUTE104 as one node with a direct link up to RUSTBORO_CITY. From the south
  half, the "route" target is the north road, which is unreachable (MODEL). The woods doors stay "back" and stay refused.
  This hits every return north after a heal or a whiteout in PETALBURG.
* **While training for ROXANNE, the AI heals at the wrong centre.** `_grass_map` (`goals.py:1624-1640`) ranks ROUTE104
  before ROUTE116 on a tie (distance 1 each, then alphabetical), so training happens on Route 104 north. After a rest,
  `_nearest_place` (`goals.py:1160-1180`) ranks by (link distance, been in, name). PETALBURG's centre and RUSTBORO's are both
  1 link from ROUTE104, so the name decides: **"PETALBURG_CITY_POKEMON_CENTER_1F" < "RUSTBORO_…"**. The AI tries to heal at
  Petalburg, through the woods, which is the refused direction above. VERIFIED-code; the outcome is UNVERIFIED (expect
  failed heals, DANGER_RETRIES, possibly a whiteout).
* The same class of map will come back later: RUSTURF_TUNNEL, GRANITE_CAVE and other "passage" maps that are neither a
  town, a city nor a route.

### 2.2 Trainers whose sight forces a battle (MODEL, `audit03_reach.py`)

* **Route 104 north**: no path from the woods' north exit to Rustboro avoids every trainer's sight. The smallest set that
  must be crossed is GINA and MIA (twins at (27,15) and (28,15), facing down, sight 1, so the tiles (27,16) and (28,16)) plus
  WINSTON (a rich boy at (21,25), rotating, sight 3: worst case). HALEY (31,24) faces left with sight 7 and can be avoided.
  The twins are `trainerbattle_double TRAINER_GINA_AND_MIA_1` (`Route104/scripts.inc:966`, `:973`; `doubleBattle = TRUE` at
  `trainers.h:5800`), SEEDOT L6 and LOTAD L6 (`trainer_parties.h:6269-6280`). **They engage only when the player has two
  usable Pokemon** (`src/trainer_see.c:283`, `CheckTrainer`; VERIFIED-decomp). A one-Pokemon party walks past.
* **Route 104 south**: avoidable (CINDY (11,44) with sight 3 watches the column up to the SW woods entrance, BILLY near
  Petalburg). Their parties are L5-L7 (`trainer_parties.h:1451-1458`, `:4214-4225`).
* **Woods**: LYLE (7,32) has WURMPLE L3 x4 and JAMES (4,14) has NINCADA L6 x2 (`trainer_parties.h:8163-8184`,
  `:8233-8244`); both are off the forced corridor (MODEL).
* **RUSTBORO GYM** (11x20): ROXANNE's tile (5,3) can be reached avoiding every sight (MODEL). The shortest way from the door
  crosses JOSH's sight ((5,14), (5,15)). **(1,9) is in both TOMMY's sight (facing left) and MARC's (facing down).** With 2
  usable Pokemon that tile starts a TWO-TRAINER double battle (`src/trainer_see.c:196-240`, the
  `gNoOfApproachingTrainers == 2` branch). The gym's grid (# wall, . floor, R ROXANNE, J/T/M the trainers, G the guide):

```
###########
###########
#..#.R.#..#
...#...#...
...........
...........
#M.########
#..########
#........##
#..T#.##.##
#...#.##.##
#.###....##
#.....#####
#.##.J.####
#.##.....##
#.###.##.##
...........
...........
..#G....#..
...........
```

**Our handling of a trainer met mid-walk is VERIFIED-code.** `Navigator.handle` plays the battle through the battler and
the walk goes on (`navigator.py:953-987`); a loss ends the intent (`:978-979`). Doubles: one decision per battler, from the
action menu's battler (`skills/battle.py:168-169`); every (move, foe) pair is valued (`brain/battle.py:851-853`,
`:1099-1118`); the target cursor is read (`skills/battle.py:368-403`). In a double battle it never switches, heals or runs
(`brain/battle.py:1292-1293`; `README.md:2033-2036`). Two-trainer doubles have no fixture (UNVERIFIED that they work).

### 2.3 Ledges, cut trees, warps
* **Ledges.** Route 104 has 13 ledge tiles: JUMP_SOUTH, JUMP_WEST and **JUMP_SOUTHWEST** (layout read); the woods have
  JUMP_SOUTH. The cardinal ones are planned as one-way (`navigator.py:311-318`). A diagonal one is a "diagonal" ledge, so a
  wall (`world/memory.py:105-107`); that docstring's "none on v1's maps" is now stale. Low risk.
* **Cut trees** are objects: `cut_tree` in `eyes/view.py:218`, so walls; they are not people and not chat targets. In the
  woods, (19,10) and (19,11) keep 159 tiles out of reach without CUT (MODEL), including the GREAT BALL (45,7) and the
  X ATTACK (35,20). On Route 104, the X ACCURACY (37,22) is behind the tree at (35,22) and the PP UP (39,15) cannot be
  reached from the north path (MODEL). Each such ball is tried once and then marked tried (`goals.py:1432-1450`). Bounded.
* **Woods warps.** The woods' own exits are NORTH_ARROW_WARP and SOUTH_ARROW_WARP, which `EXIT_PRESS` covers. Route 104's
  south woods entrances are NON_ANIMATED_DOOR. **The north entrance (10,30) and (11,30) is DEEP_SOUTH_WARP.** The eyes
  list it as an exit (`eyes/view.py:131`, `:201`), but `EXIT_PRESS` (`navigator.py:233-237`) has no entry for it, so it
  is tried from any side. Pressed from the side, nothing happens and it is remembered CLOSED (`navigator.py:930-936`).
  In the game, this look warps only on a SOUTH press while standing on it (UNVERIFIED: I did not re-read
  `field_control_avatar.c`).

### 2.4 NPCs that block until an event
* **RUSTBORO Devon Corp 1F**: the stair guard is moved onto (14,2), in front of the stairs, until
  `FLAG_RETURNED_DEVON_GOODS` (`RustboroCity_DevonCorp_1F/scripts.inc:5-12`). It never moves. The explorer will
  find the 2F stairs unreachable for each intent. It costs time, not the run.
* **Mr. BRINEY** (Route 104's cottage) is hidden from the New Game on (`data/scripts/new_game.inc:132-133`), so no sail to
  DEWFORD can derail the run. The WHITE HERB florist appears only after BADGE03 (`Route104/scripts.inc:20-27`).
* **SCOTT** (PETALBURG (4,10)-(4,13), `VAR_SCOTT_PETALBURG_ENCOUNTER` 0) plays once as the player heads west. The player
  only turns. It is sat through like any scene.

### 2.5 Multi-floor buildings
RUSTBORO has Flat1 (1F-2F), Flat2 (1F-3F), the POKéMON CENTER 2F and Devon (guarded). The ping-pong and seen-all rules
cover stairs. RUSTBORO's centre 2F probably has back-wall doors with no warp, like OLDALE's and PETALBURG's (`README.md`
step-3 limits); UNVERIFIED for RUSTBORO. These cost time only.

### 2.6 Scenes the loop must sit through
The woods scene: about 8 `msgbox` pages, `trainerbattle_no_intro`, `giveitem GREAT_BALL`, and the researcher leaving. No
yes/no and no menu, so `SCENE_TURNS` 8 (`navigator.py:241`) is not reached. ROXANNE's badge scene and the TM ROCK TOMB
(`RustboroCity_Gym/scripts.inc:13-34`) come next. The run ends at the badge (`mode.py:437-438`, index > target), so the
STOLEN-GOODS coord scene outside the gym ((23,20)-(23,24), `VAR_RUSTBORO_CITY_STATE` 1, set at `:20`) falls after the run's
end. VERIFIED.

### 2.7 Yes/no questions in the chapter-3/4 area (gap 4)
`answer_question` says YES to anything it has no rule for (`skills/story.py:83-91`).
* RUSTBORO House1 trader: YES leads to `special ChoosePartyMon` (`RustboroCity_House1/scripts.inc:12-14`). That party menu
  is not in `_story_menu` (`mode.py:572-583`), so the result is `stuck: an unexpected party on screen`
  (`navigator.py:1014-1017`). The loop replays it (`mode.py:455-461`) until `STORY_PATIENCE`. B would decline the trade
  (`PARTY_NOTHING_CHOSEN`).
* The flower shop's "learn about berries?" is harmless text.
* Devon 2F (the fossil, nicknames) is behind the stair guard.

---

## 3. What is missing for RULING 33 here (question 3)

* **QUICK CLAW**: the RUSTBORO Trainer's School teacher, talked to; no condition but the flag
  (`RustboroCity_PokemonSchool/scripts.inc:77-90`; the school door is RUSTBORO (27,34)). Our code has no gift goal. The AI
  gets it only if it explores into the school AND a CHAT draw picks the teacher within 4 tiles (`goals.py:896-903`,
  `:1118-1134`; one draw per person per run). No code gives an item to HOLD (grep finds none). **Even once received, it
  would never be used.** Person-fair source: the school's sign and the teacher's own words.
* **AMULET COIN: not obtainable in badge 1.** MOM gives it only with `FLAG_BADGE05_GET` and after the POKéNAV
  registration (`data/scripts/players_house.inc`, `PlayersHouse_1F_EventScript_CheckGiveAmuletCoin` and `TryGiveAmuletCoin`,
  about lines 293-319). VERIFIED-decomp.
* **BLACK GLASSES: not reachable in badge 1.** It is a HIDDEN item at Route 116 (70,13) (`Route116/map.json` bg_events),
  east of the RUSTURF TUNNEL warps (47,8) and (65,10). MODEL: from RUSTBORO's edge the walkable region stops at x=60, even
  with the cut trees removed. Its owner, the glasses man, stands at (74,13) (`Route116/scripts.inc:150-175`). Also, our AI
  has no hidden-item search.
* **Other gifts in the chapter-3/4 area**, all needing a chat (VERIFIED-decomp):
  * the MIRACLE SEED (woods girl at (33,5), `PetalburgWoods/scripts.inc:229-238`);
  * TM BULLET SEED (Route 104 boy at (5,26), `Route104/scripts.inc:314-325`);
  * a CHESTO BERRY (Route 104 at (37,8), `:248-256`);
  * the WAILMER PAIL and a daily berry (flower shop, `Route104_PrettyPetalFlowerShop/scripts.inc:55-90`);
  * HM CUT (RUSTBORO's Cutter's house at (9,38), `RustboroCity_CuttersHouse/scripts.inc:7-10`).

  The GREAT BALL from the researcher and TM ROCK TOMB from ROXANNE come automatically.
* **Visible items.** Reachable without CUT (MODEL): ETHER (4,8) and PARALYZE HEAL (4,26) in the woods; a POTION (5,8) on
  Route 104 north; a POKé BALL (29,53) on Route 104 south; X DEFEND (36,51) in RUSTBORO. The ITEM goal covers balls on
  screen or remembered (`goals.py:821-831`). `Novelty._items` counts only balls and healing items
  (`navigator.py:564-567`): an ETHER, an X item or PP UP is no novelty. Minor.
* **Catching.** Opportunistic in any wild battle, one draw per species (`brain/battle.py:794-816`). The CATCH roam errand
  is **switched off for all of chapter 4** (`goals.py:879-880`: `not fight_next`), and it is drawn once per MAP per run
  (`catch_maps`), so ROUTE104's two halves get ONE draw. New species here (`src/data/wild_encounters.json`):
  * woods L5-6: SHROOMISH, SLAKOTH, SILCOON, CASCOON;
  * Route 104 L3-5: MARILL, WINGULL;
  * Route 116 L6-8: ABRA, NINCADA, SKITTY, WHISMUR.

  Person-fair source: the researcher asks "have you seen any POKéMON called SHROOMISH?" (`PetalburgWoods/scripts.inc`,
  `HaveYouSeenShroomish`).
* **Training to ROXANNE's level with TYPE ADVANTAGE.**
  * Built: the level target (`goals.py:1064-1067`: the strongest Pokemon to L15 + margin, so Story 16, Catcher 17,
    Trainer 18), and a switch in battle when badly matched (`brain/battle.py:1288-1329`, at most `MAX_SWITCHES` 2).
  * Missing:
    * any use of the type: the person-fair source is the GYM GUIDE at the door, "ROCK-type ... can't stand WATER-type and
      GRASS-type moves" (`RustboroCity_Gym/scripts.inc:106-126`), heard only through a chance chat;
    * any choice of who LEADS;
    * any catching of a WATER or GRASS Pokemon for the gym (MARILL on Route 104, SHROOMISH in the woods);
    * training a second Pokemon.
  * A TORCHIC (Fire) is weak against ROCK, and EMBER does 0.5x on GEODUDE. It depends on evolving at 16 and on learning
    DOUBLE KICK as COMBUSKEN (`level_up_learnsets.h:3645`), which is gap 3's untested path. A MUDKIP (Water Gun) and a
    TREECKO (Absorb) are favoured.

---

## 4. Patience, cooldowns and budgets against the longer stretch (question 4)

| Number | Value | Where | Against chapters 3-4 |
|---|---|---|---|
| `STORY_PATIENCE` | 120,000 frames since the last REAL progress | `mode.py:102`, `:451-454` | Enough for honest progress. **It is also the only thing that ends a gap-1 stall** (about 33 minutes) |
| `HEAL_RESETS_MAX` | 3 heals a milestone count as progress | `mode.py:108` | Chapter-4 training heals often; its battles won also reset the patience. OK |
| `MAX_LOSSES` | 3 for the **whole run** | `mode.py:103`, `:559-570` | Chapters 1-4 share it. Losses to ROXANNE plus earlier whiteouts can end the run. It needs a per-milestone count, or retraining after a loss |
| `GO_FRAMES` / extensions | 9,000, plus up to 2x the frames battles took (>= 600) | `goals.py:200`, `:252-253` | Petalburg to Rustboro (Route 104 south, the 48x44 woods with grass, Route 104 north and its trainers) is likely longer, so decisions get re-made inside the woods (gap 1) |
| `FIND_FRAMES` | 4,000 | `goals.py:201` | ROXANNE inside the 11x20 gym: fine |
| `FAIL_LIMIT` / `COOLDOWN_DECISIONS` / `STORY_ASIDE_FRAMES` | 2 / 12 / 6,000 | `goals.py:186-187`, `:247` | A talk to ROXANNE interrupted by JOSH counts as failed, so two interruptions put her aside. Cheap |
| `TRAIN_SESSIONS` | 8 sessions of 100 / 120 / 150 steps | `goals.py:189`, `:864`; `personality.py:154-162` | **Every session counts, including one stopped after its first battle by a rest** (`goals.py:1474-1481`; `training_rest` `:395-403`; Story `heal_below` 0.6). UNVERIFIED estimate: Route 104's L3-5 foes give about 35-45 exp each; a starter at about L12 needs about 1,550 exp for L16 and about 2,800 for L18 (medium-slow), so 2-6 battles a session may leave it under target when the 8 sessions run out (it then says "ready: no endless grind") |
| `NOVELTY_WINDOW` / `PINGPONG_USES` | 3,000 frames / 3 uses | `navigator.py:185`, `:187` | Re-crossing the known woods (about 40 tiles, about 650 frames) is fine. A woods-to-Route-104 ping-pong ends the intent, not the run |
| `BATTLE_STEPS` / `TEXT_BUDGET` | 150 menus / 5,400 frames per text stretch | `skills/battle.py:69-71` | A double is 2 menus a turn: OK. The evolution at L16 is inside one stretch: OK (UNVERIFIED live) |
| `MAX_SWITCHES` / `MAX_HEALS` | 2 / 2 per battle | `brain/battle.py:146-147` | ROXANNE has 3 Pokemon and an ORAN BERRY: tight but plausible |
| `APPROACH_BUDGET` / `SCENE_ROUNDS` | 4,000 / 12 | `skills/story.py:61-63` | OK |
| Run budget | `--frames 330000`, `--wall-seconds 3600` in the examples | `README.md:388-389` | Sized for one chapter. Chapters 3-4 with training will need more (UNVERIFIED how much) |

---

## 5. For the developers: fixtures and pre-registration hints (not for the AI)

* Starting saves that exist (bot saves, teaching side; use COPIES; never write into `tools/story-dev/saves/`):
  * `tools/story-dev/saves/post_wally.ss1` and `wally_done.ss1` start chapter 3;
  * `rustboro.ss1`, and `r20_pregym1_party4_r116.ss1` (a 4-Pokemon pre-gym party on Route 116) start chapter 4;
  * `gym1_done.ss1` and `r20_badge1_party1_gym.ss1` are end states.

  Their world memory will not have heard DAD (section 1 caveat).
* **Gap 1 A/B, decisive and cheap.** Start just after the woods scene (or at its trigger, (26,23)) and play one `go`
  decision. Pre-register: on the current code the next exit used is a SOUTH woods exit (Route 104 at (10,38)/(11,38) or
  (32,42)/(33,42)); with the woods counted as outdoor or passage, it is the north one (Route 104 at (10,30)/(11,30)). The
  ground truth is `gSaveBlock1` map and position, read by the harness. The discriminator is the y of the arrival on
  ROUTE104: north is below 31, south above 37.
* **Gap 2.** A ROXANNE loss on a Torchic L15 copy: assert that the next decisions TRAIN before the next challenge, and that
  a third loss in the run does not end it at a gym it could win after training.
* **Gap 4.** A copy in RUSTBORO House1 next to the trader: the CHAT plays the yes/no; assert the screen is free within N
  frames.

**Verification still owed** (this note is adversarial input, not a verdict): the gap-1 trajectory live (it is reasoned from
code, not run); `DEEP_SOUTH_WARP`'s press in `field_control_avatar.c`; whether diagonal-ledge tiles are walkable; and
`OBJ_EVENT_GFX_ROXANNE` = 125.
