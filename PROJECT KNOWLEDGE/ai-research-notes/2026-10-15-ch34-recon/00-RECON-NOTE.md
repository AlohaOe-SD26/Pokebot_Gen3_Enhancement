# 00 — Chapters 3-4 recon, the SYNTHESIS (Route 104 → Petalburg Woods → Rustboro → the gym → ROXANNE)

> **NOTE - not truth until verified; the adversarial section below rules.**
> §10 (contradictions and open questions) is the adversarial section. Where §0-§9 and §10 disagree, §10 wins until a
> live probe or a decomp read settles the point.
>
> Written 2026-10-15 by a read-only Claude synthesis agent. It merges the six angle notes in this folder:
> [01] decomp, [02] human play and the Gemini adjudication, [03] our code's gaps, [04] what the bot learned,
> [05] static map facts, [06] the living-lessons draft. The synthesis agent also made five decomp reads of its own to
> settle contradictions; those are tagged **[00]**. Nothing was run, and nothing outside this file was written.
>
> **Evidence tags (kept from the angle notes):**
> - **VERIFIED**: read in pret/pokeemerald (master, fetched 2026-10-15) or in our tree, with the citation.
> - **MODEL**: computed by an agent's static walk/sight script from the decomp layouts. [05] calls this DERIVED. It
>   is exact for per-tile facts and approximate for reachability; wanderers are frozen at their spawn tile. Treat it as
>   UNVERIFIED wherever code will depend on it.
> - **UNVERIFIED**: recall, an estimate or an inference.
>
> Agreement between angles is NOT a confidence signal (CLAUDE.md, the measured Gemini rules). Where two static models
> agree, the claim is still MODEL.
>
> ⛔ **PERSON-FAIR (USER RULINGS 35-37).** Every coordinate, flag, var, route, choke, sight line, step count and
> hidden-item location here is for the DEVELOPERS: proof design, fixtures, expectations and fault arms. **None of it may
> reach the AI player as a hint.** The AI may use only what is on screen, plus hints at the level the game's DIALOGUE
> and SIGNS give. §2 is the complete list of those, and it is the only section whose CONTENT the AI may meet, and only
> by hearing or reading it in the game.

---

## 0. Ten things to know first (each carries its caveat)

1. **The likeliest run-stopper is ours, not the game's.**
   - Route 104 is ONE map whose two halves join on foot only through Petalburg Woods (MODEL [01][03][05]; the map id
     is VERIFIED).
   - Our goal manager treats the woods as an INTERIOR, because `OUTDOOR = ^(ROUTE\d+|[A-Z]+_(TOWN|CITY))$`
     (VERIFIED [00], `ai_player/brain/goals.py:432`).
   - [03] predicts that after the woods scene the AI walks back SOUTH, then refuses the woods, and ends on
     `STORY_PATIENCE`. That trajectory is UNVERIFIED (reasoned from code, not run).
   - ⚠ It is worse than [03] says: from Route 104 south only ONE woods entrance can be entered. The south-east door
     is in a ledge-locked pocket you can only leave (MODEL [01][05]). So [03]'s "an unused second entrance is left" does
     not exist (§10 C3).
2. **The woods scene is forced northbound, and it does NOT fire at the entrance** (MODEL, three static models).
   - It fires on the two-tile corridor (26,23)/(27,23), 15 rows north of the south doors.
   - `VAR_PETALBURG_WOODS_STATE` 0→1 is its LAST command (VERIFIED `PetalburgWoods/scripts.inc:92`). The Great Ball
     has no flag.
   - [04] marks "forced" UNVERIFIED (§10 C1). A live probe should settle it before a proof leans on it.
3. **Two double-battle traps, both gated on "2 usable Pokémon"** (VERIFIED rule: `trainer_see.c` `CheckTrainer`).
   - The Route 104 twins GINA & MIA stand on the only bridge (MODEL).
   - Gym tile (1,9) is seen by both TOMMY and MARC. With 2 usable Pokémon it starts a two-trainer double (rule
     VERIFIED; the overlap is MODEL; never live-tested).
4. **Beating ROXANNE marks JOSH, TOMMY and MARC as defeated** (VERIFIED `data/scripts/set_gym_trainers.inc:12-16`, called
   at `RustboroCity_Gym/scripts.inc:23`).
   - So a trainer flag read AFTER the badge proves nothing about fights.
   - **MARC is missing from `milestones.json`** (VERIFIED [00]: no hit for `MARC` or `1851` in
     `ai_player/knowledge/milestones.json`).
5. **Two scenes set their marker BEFORE they end.**
   - ROXANNE sets `FLAG_BADGE01_GET` before TM39 and its text (VERIFIED `RustboroCity_Gym/scripts.inc:13-34`).
   - SCOTT sets `VAR_SCOTT_STATE` before his dialogue (VERIFIED `PetalburgCity/scripts.inc:525`).
   - Our run ends when the target milestone is passed (VERIFIED [00] `ai_player/mode.py:437-438`), so a chapter-4
     run ends with the TM text still up.
6. **Level 16 lands inside the gym** (VERIFIED: `evolution.h:125-130` and the learnsets).
   - All three starters evolve at 16. Holding B cancels an evolution (`src/evolution_scene.c:637-647`).
   - A Torchic that does not evolve learns Peck instead of Combusken's Double Kick, its only good move against ROXANNE.
   - Our AI has never played an evolution live (VERIFIED [03] `ai_player/README.md:2027-2029`).
7. **RULING 33's named gifts in this window:**
   - QUICK CLAW: yes, with no gate (VERIFIED `RustboroCity_PokemonSchool/scripts.inc:77-90`).
   - AMULET COIN: no. It is a badge-5 gift (VERIFIED `players_house.inc:307-317`), already ruled as RULING 17
     (`06-DECISIONS-LOG.md:7362`).
   - BLACK GLASSES: not reachable before the badge (MODEL [01][03]).
   - RULING 33's own words are "if it can reach them" (`06:9160`), so this needs **no escalation**; it is reporting only.
8. **ROXANNE can end the run.** `MAX_LOSSES = 3` counts across the whole run (VERIFIED [00] `mode.py:103`), and a loss
   does not cause more training (VERIFIED-code [03]).
9. **Leaving the gym after the badge fires the Devon "stolen goods" scene.** It is a coord trigger at (23,20..24) on
   `VAR_RUSTBORO_CITY_STATE == 1` (VERIFIED trigger; the choke is MODEL). It is chapter 5's first beat.
10. **Three contradictions settled by this synthesis's own decomp reads [00]:**
    - `DEEP_SOUTH_WARP` fires on a STEP onto it, so [03]'s gap 7 mostly falls (§10 C4).
    - Diagonal ledges never jump (§10 C5).
    - Cut trees regrow, because TEMP flags clear on every map load (§10 C6).

---

## 1. The story path, and the FLAGS/VARS that prove each beat

Values come from `include/constants/flags.h` and `vars.h`. Trainer flags are `TRAINER_FLAGS_START` 0x500 + the trainer
id (`flags.h:1343`, `battle_setup.c:1259-1264`). All VERIFIED [01][02][03] unless tagged.

| # | Beat | Trigger | Proof (game-read) | Set at | Notes |
|---|---|---|---|---|---|
| 0 | Chapter 2 ends: DAD's speech | automatic after Wally's tutorial | `VAR_PETALBURG_GYM_STATE` = 2 (0x4085) | `PetalburgCity_Gym/scripts.inc:90` | `VAR_PETALBURG_CITY_STATE` = 3 at the tutorial's end (`PetalburgCity/scripts.inc:47`) [02] |
| 1 | SCOTT at Petalburg's west exit | coord x=4, y=10..13, `VAR_SCOTT_PETALBURG_ENCOUNTER == 0` | `VAR_SCOTT_PETALBURG_ENCOUNTER` = 1 | `PetalburgCity/scripts.inc:540` | ⚠ `VAR_SCOTT_STATE` = 1 is set at `:525`, BEFORE three msgboxes [04]. No battle. Not in `milestones.json` [02] |
| 2 | Route 104 south → woods | walking | none | | Only the SW door (10/11,38) can be entered from the south (MODEL) |
| 3 | **The woods scene**: researcher, grunt, battle, Great Ball | coord (26,23)/(27,23), `VAR_PETALBURG_WOODS_STATE == 0` | **`VAR_PETALBURG_WOODS_STATE` = 1** (0x4098 = 16536) | `PetalburgWoods/scripts.inc:92`, the last command | Second witnesses: `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT` 0x2D5 and `_DEVON_EMPLOYEE` 0x2D4 (set by `removeobject`). Grunt trainer flag 0x50A (1290), on a WIN only. The Great Ball has NO flag (`:73`). A loss means a whiteout, the var stays 0, and the scene replays |
| 4 | Woods north exit → Route 104 north | arrow warp (14/15,5), hold UP | none | | Arrival on Route 104 (10/11,30), facing NORTH (VERIFIED [00] `overworld.c:933-934`) |
| 5 | **Arrive in Rustboro** | map transition | **`FLAG_VISITED_RUSTBORO_CITY`** 0x879 (2169) | `RustboroCity/scripts.inc:7` (OnTransition) | A quiet arrival: `VAR_RUSTBORO_CITY_STATE` is 0, so no coord trigger is armed |
| 6 | Heal in Rustboro (optional) | entering the Pokémon Center | respawn = `HEAL_LOCATION_RUSTBORO_CITY` | `RustboroCity_PokemonCenter_1F/scripts.inc:7` | Before this, a whiteout returns the player to PETALBURG |
| 7 | Rustboro errands (optional) | talking | `FLAG_RECEIVED_QUICK_CLAW` 0x113; `FLAG_RECEIVED_HM_CUT` 0x89; `FLAG_RECEIVED_PREMIER_BALL_RUSTBORO`; `FLAG_MET_SCOTT_RUSTBORO` 0x136 | see §4 | RULING 33 material |
| 8 | Gym trainers (optional) | sight | JOSH 0x640 (1600), TOMMY 0x641 (1601), **MARC 0x73B (1851)** | win | ⛔ **Read these BEFORE ROXANNE's battle.** Her win sets all three (§0.4) |
| 9 | **ROXANNE** | talk from (5,3) facing up; she never spots you (`TRAINER_TYPE_NONE`) | **`FLAG_DEFEATED_RUSTBORO_GYM`** 0x4F0 (1264) and **`FLAG_BADGE01_GET`** 0x867 (2151) | `RustboroCity_Gym/scripts.inc:13-34` | In order: badge text; both flags; `VAR_RUSTBORO_CITY_STATE` = 1 (0x405A); `VAR_PETALBURG_GYM_STATE` += 1; SetGymTrainers; `giveitem` TM39 then `FLAG_RECEIVED_TM_ROCK_TOMB` 0xA5. ⚠ With a full bag the TM is skipped and its flag stays clear; talking to her again retries (`:8`, `:30`). Her trainer flag is 0x609 (1545) |
| 10 | (chapter 5) the stolen-goods scene | coord (23,20..24) on state 1 | `VAR_RUSTBORO_CITY_STATE` 1 → next | Rustboro `map.json` coord_events | Forced on leaving the gym plaza (MODEL). [05] says it moves to 2; UNVERIFIED by this note |

**How this maps onto `ai_player/knowledge/milestones.json`** (VERIFIED [01 §11][03 §1]):
- `ch3_route104` and `ch3_woods` share one proof (`PETALBURG_WOODS_STATE >= 1`), so `ch3_route104` only ever passes as
  a waypoint. That is by design (its note at :1058).
- `ch3_rustboro` = flag 2169. `ch4_roxanne` = 1264 and 2151.
- `ch4_gym_trainers` has two defects. It lacks MARC. And its "done" reads trainer flags that ROXANNE's win sets anyway.
- `ch3_woods`'s `taught_by` cites the BOT's segment start ("begins just inside the Woods south entrance",
  `early_game.py:1684`). It is not where the scene fires [05 §0.3].
- Chapter 3 has no milestone for the free gifts, and none for SCOTT's scene.

---

## 2. What the game TELLS the player (the ONLY hints the AI may use)

All quotes are VERIFIED [02 §1][01 §12][05 §7] unless tagged. Coordinates in brackets are developer-only.

**The destination:**
- **DAD, once, automatically** (`PetalburgCity_Gym/scripts.inc:1193-1208`): "Head for RUSTBORO CITY beyond this town.
  There, you should challenge the GYM LEADER, ROXANNE." ⚠ "Beyond this town" gives NO direction.
- **DAD again, repeatable** (`:1210-1218`): "Aren't you going to the POKéMON GYM in RUSTBORO CITY?" This is a
  person-fair way to REFRESH a forgotten goal.

**On the way:**
- **SCOTT** (`PetalburgCity/scripts.inc:726-741`): flavour only, with no direction.
- **Route 104 signs** (`Route104/scripts.inc:1045`, `:1049`): `ROUTE 104 → PETALBURG CITY` [27,66], which points BACK
  east, and `ROUTE 104 ↑ RUSTBORO CITY` [23,5], at the north end. The second is the strongest pointer between the
  woods and the city. `milestones.json` does not use it yet.
- Nothing in the window names Petalburg Woods as the way. The woods are simply where the road goes [02 §0.1].

**Advice from people and signs:**
- Route 104 girl [28,74] (`:1007`): "if TRAINERS lock eyes, it's a challenge to battle. If you don't want to battle,
  stay out of their sight."
- Route 104 boy [27,63] (`:995`): "weaken the wild POKéMON first."
- Route 104 woman [30,50] (`:1001`), in the exit-only pocket: "throw POKé BALLS only at wild POKéMON."
- Woods TRAINER TIPS [14,32] (`PetalburgWoods/scripts.inc:437`): "To raise a weak POKéMON, put it at the left of the
  team list. As soon as a battle starts, switch it out." The game teaches switch-training.
- Woods boy [15,19] (`:410`): stay out of tall grass if your Pokémon are weak.
- Woods boy [30,34] (`:417`): "there are things on the ground even if you can't see them". This is the person-fair
  hint that hidden items exist.
- Woods TRAINER TIPS [11,8] (`:447`): PP, and "taken to a POKéMON CENTER".

**The woods scene:**
- The researcher (`:303-306`): "have you seen any POKéMON called SHROOMISH around here?"
- The grunt (`:333-341`): "we of TEAM AQUA are also after something in RUSTBORO."
- The researcher (`:351-354`): "Didn't that TEAM AQUA thug say they were after something in RUSTBORO, too?"
- `milestones.json`'s `ch3_rustboro` hint uses these lines.

**Route 104 north:**
- TRAINER TIPS [17,23] (`Route104/scripts.inc:1056`): about DOUBLE BATTLES.
- Bullet Seed boy [5,26]: "A TM … is good only for one-time use … Think twice before using it!" (`:1021`).
- Expert F [37,8]: berries.
- Sign: `PRETTY PETAL FLOWER SHOP` [7,20].

**Rustboro:**
- City sign (`RustboroCity/scripts.inc:1145`).
- **Gym sign** (`:1135`): "LEADER: ROXANNE 'The ROCK-loving honors student!'". This is the first ON-SCREEN statement of
  her type.
- **Woman** [22,34] (`:946`): "FIRE-type POKéMON don't match up well against ROCK-type POKéMON."
- Man [26,23] (`:928`): "Have you taken the POKéMON GYM challenge?"
- Man [19,27] (`:986`): traded Pokémon may disobey without badges.
- Mart woman (`RustboroCity_Mart/scripts.inc:67`): "Just in case I run into SHROOMISH in PETALBURG WOODS". This says
  WHERE Shroomish lives.
- **SCOTT, in the school** (`RustboroCity_PokemonSchool/scripts.inc:300-314`): "have a POKéMON learn the move CUT …
  someone in this town has CUT."
- A man in the Pokémon Center (`RustboroCity_PokemonCenter_1F/scripts.inc:43`): "The man next door gave me an HM!"
- The teacher (`RustboroCity_PokemonSchool/scripts.inc:242`): "Students who don't study get a little taste of my QUICK
  CLAW."
- The school kid (`:262`): about SEEDOT.
- The tunnel sign [30,8] (`:1123`) and the RUSTURF TUNNEL sign (`Route116/scripts.inc:442`): "The tunnel project has
  been canceled."

**The gym:**
- **Gym Guide** [3,18] (`RustboroCity_Gym/scripts.inc:106-126`): "ROXANNE … is a user of ROCK-type POKéMON. The ROCK
  type is very durable, but it can't stand WATER-type and GRASS-type moves." This is the ONLY statement of the
  counter-types. Fighting is not named.
- Trainer lines: Josh `:147`, Tommy `:151`/`:158` ("ROXANNE is stronger than me by several times"), Marc `:173`.
- ROXANNE's intro (`:178`).
- The badge text (`:203`): the badge "enables them to use the HM move CUT outside of battle."

⛔ **Rule for the build.** The AI may know a type fact only because it heard or read one of these lines, or learned it in
its own battles. Its memory's `heard` set is where that lives (VERIFIED [03] `world/memory.py:729,751`). Today the gym
guide is heard only through a chance chat (VERIFIED-code [03] `goals.py:896-903`).

---

## 3. Trainers and battles on the way

All VERIFIED [01 §7][02 §2] from `map.json`, `scripts.inc`, `trainers.h` and `trainer_parties.h`, except the
"avoidable" column, which is MODEL [05 §2d, §3c, §5][01 §10].

| Trainer (id → flag) | Class | Where (dev) | Facing / sight | Battle | Team | Avoidable? (MODEL) |
|---|---|---|---|---|---|---|
| CINDY_1 (114 → 0x572) | Lady | R104 S (11,44) | up+right / 3 | single; carries a FULL RESTORE | Zigzagoon L7 @Nugget | Yes (go round her by column x=10) |
| BILLY (319 → 0x63F) | Youngster | R104 S (18,67), walks a loop | all / 2 | single | Zigzagoon L5, Seedot L7 | Yes (south of the walk) |
| DARIAN (696 → 0x7B8) | Fisherman | R104 S (15,59) | left / **0** | single | Magikarp L9 | Talk-only; never engages |
| GRUNT_PETALBURG_WOODS (10 → 0x50A) | Team Aqua | Woods, scripted | n/a | `trainerbattle_no_intro`, **forced, cannot be fled** | Poochyena L9 | **No** (northbound) |
| LYLE (616 → 0x768) | Bug Catcher | Woods (7,32) | D/L/R / 3 | single | Wurmple L3 ×4 | Timing-dependent (§10 C2) |
| JAMES_1 (621 → 0x76D) | Bug Catcher | Woods (4,14) | D/U/R / 3 | single | Nincada L6 ×2 | Only if he faces east as you cross row 14 (§10 C2) |
| HALEY_1 (604 → 0x75C) | Lass | R104 N (31,24) | left / 7 | single | Lotad L6, Shroomish L6 | Yes |
| WINSTON_1 (136 → 0x588) | Rich Boy | R104 N (21,25) | rotating / 3 | single; carries a FULL RESTORE | Zigzagoon L7 @Nugget | Timing-dependent: every path north crosses his column |
| **GINA_AND_MIA_1** (483 → 0x6E3) | Twins | R104 N bridge (27,15)+(28,15) | down / 1 | **DOUBLE** | Seedot L6, Lotad L6 | **No, with 2 usable Pokémon. They never engage with 1** (talking then gives `Route104_Text_GinaNotEnoughMons`) |
| IVAN (337 → 0x651) | Fisherman | R104 N (29,8) | down / **0** | single | Magikarp L5, L6, L7 | Talk-only |
| JOSH (320 → 0x640) | Youngster | Gym (5,13) | down / 2 | single | Geodude L10 (Tackle) | Yes |
| TOMMY (321 → 0x641) | Youngster | Gym (3,9) | left / 3 | single, **or a two-trainer double with MARC at (1,9)** | Geodude L8 ×2 | Yes |
| **MARC** (571 → 0x73B) | Hiker | Gym (1,6) | down / 3 | single, or the (1,9) double | Geodude L8 ×2 | Yes |
| **ROXANNE_1** (265 → 0x609) | Leader | Gym (5,2) | talk only | single; **2× POTION**; AI flags CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY | **Geodude L12** ×2 (Tackle, Defense Curl, Rock Throw, Rock Tomb); **Nosepass L15 @ORAN BERRY** (Block, Harden, Tackle, Rock Tomb) | n/a (the goal) |

**Mechanics that matter for the AI** (VERIFIED unless tagged):
- **A trainer battle cannot be fled.** [04 §2c] records the bot's ML-8, where trying to run from one went wrong.
- **Sight is checked EVERY overworld frame**, from the player's destination tile (`field_control_avatar.c:147`;
  `overworld.c:1438-1457`) [05 §0.6]. A rotating trainer (Winston, Lyle, James) can spot a player who is standing
  still. "Stop and wait" inside a rotating trainer's line is not safe.
- **Double-battle gate:** a `trainerbattle_double` trainer is skipped unless the player has two usable Pokémon
  (`trainer_see.c:279-285`, `CheckTrainer`; `GetMonsStateToDoubles_2`).
- **Two spotting trainers** are collected in one frame when the player has 2 usable Pokémon
  (`trainer_see.c:191-245`). With 1 usable Pokémon it is a single battle with whichever trainer is checked first
  [05 §0.5].
- **The gym's shortest path** from the door to ROXANNE (23-24 steps) crosses JOSH's line and (1,9). A path that avoids
  all three trainers exists, at about 30 steps (MODEL [01][05]).
- **Losing** any of these battles means a whiteout to the last Pokémon Center entered (`battle_setup.c:1333-1338`).
- **No rival battle** happens in chapters 3-4. The Route 104 and Rustboro rivals start hidden (`new_game.inc:129,231`)
  and appear only after the PokéNav [01 §0.10].
- **ROXANNE matchups** (VERIFIED [02 §4.1], the type rows in `battle_main.c` plus the learnsets):
  - MUDKIP: Mud-Slap at L6, then Water Gun at L10. ×2-×4 on Geodude, ×2 on Nosepass.
  - TREECKO: Absorb at L6. ×4 / ×2.
  - TORCHIC: no super-effective move until Combusken's Double Kick at L16. Ember is ×½, and Rock Tomb and Rock Throw
    are ×2 on Fire.
- **What the bot measured** (VERIFIED [04 §1], 1,769 badge-time party snapshots, levels taken AFTER the gym):
  - The starter line was at about L16-17 and evolved: Marshtomp 16, Combusken 17, Grovyle 17.
  - The bench sat at L7-8.
  - Every Torchic win was a Combusken with Double Kick (460 of 460).
- **Optional Route 116 trainers** at L8-9, reachable from Rustboro (VERIFIED [02 §2], `Route116/scripts.inc:226-343`):
  JOEY, JOSE, JERRY_1, CLARK, JANICE, KAREN_1, SARAH, DAWSON, DEVAN, JOHNSON. Which of them stand west of the
  reachable limit is not mapped (§10 Q7).

---

## 4. Items and gifts (with conditions)

### 4a. Gifts (VERIFIED [01][02][03] unless tagged)

| Item | Giver (dev: where) | Flag | Condition | In ch3-4? |
|---|---|---|---|---|
| GREAT BALL | the woods researcher, automatic | **none** | none; with a full bag he gives nothing (`PetalburgWoods/scripts.inc:78-81`) | yes, forced |
| TM09 BULLET SEED | Route 104 N boy (5,26) | `FLAG_RECEIVED_TM_BULLET_SEED` 0x106 | none (`Route104/scripts.inc:317-326`) | yes |
| CHESTO BERRY | Route 104 N Expert F (37,8), outdoors | `FLAG_RECEIVED_CHESTO_BERRY_ROUTE_104` 0xF6 | none (`:248-258`) | yes |
| WAILMER PAIL (key item) | flower shop girl | `FLAG_RECEIVED_WAILMER_PAIL` 0x5E | none (`Route104_PrettyPetalFlowerShop/scripts.inc:62-76`) | yes |
| A random berry, daily | flower shop little girl | `FLAG_DAILY_FLOWER_SHOP_RECEIVED_BERRY` | once per day; one of CHERI..PERSIM (`:78-91`) | yes |
| (berry lesson) | flower shop owner | `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` 0x7F | first talk; a YES/NO question | yes |
| **QUICK CLAW** | Trainer's School teacher | `FLAG_RECEIVED_QUICK_CLAW` 0x113 | **"not received yet" only** (`RustboroCity_PokemonSchool/scripts.inc:77-90`). Talked to from the side, he first walks a short loop | **yes** |
| HM01 CUT | the Cutter (Rustboro) | `FLAG_RECEIVED_HM_CUT` 0x89 | none (`RustboroCity_CuttersHouse/scripts.inc:4-13`). Using Cut in the field needs `FLAG_BADGE01_GET` (`party_menu.c:120,3725`) | yes, but only usable after the badge |
| PREMIER BALL | Rustboro Flat 2, 2F | `FLAG_RECEIVED_PREMIER_BALL_RUSTBORO` | none (`RustboroCity_Flat2_2F/scripts.inc:8-16`) [02 only] | yes |
| TM39 ROCK TOMB | ROXANNE, automatic | `FLAG_RECEIVED_TM_ROCK_TOMB` 0xA5 | the bag has room | at the badge |
| A trade: your RALTS for SEEDOT "DOTS" @Chesto | Rustboro House1 | `FLAG_RUSTBORO_NPC_TRADE_COMPLETED` | a RALTS (`RustboroCity_House1/scripts.inc:4-26`) | yes, but see gap 5 (§6) |
| MIRACLE SEED | woods girl (33,5) | `FLAG_RECEIVED_MIRACLE_SEED` 0x129 | the script has no gate (`:229-238`), but she stands **behind the Cut trees** (MODEL [01][05]). Her line assumes the badge | **no** (Cut) |
| WHITE HERB | Route 104 florist | | hidden until `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` AND `FLAG_BADGE03_GET` (`Route104/scripts.inc:21-29`) | **no** |
| AMULET COIN | MOM | | `FLAG_BADGE05_GET` (`players_house.inc:307-317`); RULING 17 | **no** |
| BLACK GLASSES | hidden item on Route 116 (70,13), `FLAG_HIDDEN_ITEM_ROUTE_116_BLACK_GLASSES` (`flags.h:642`) | | east of the Rusturf Tunnel. From Rustboro the walkable region stops at x=60 (MODEL [03]; [01] agrees) | **no** (MODEL; §10 C7) |

### 4b. Visible item balls (placement VERIFIED `map.json`; reachability MODEL)

| Map | Reachable on foot in ch3-4 | NOT reachable |
|---|---|---|
| Route 104 | POTION (5,8) `FLAG_ITEM_ROUTE_104_POTION` 0x46F (north-west grass corner); POKé BALL (29,53) 0x421, **only by leaving the woods through the SE exit** | PP UP (39,15): a pond islet, needs Surf. X ACCURACY (37,22): behind the Cut tree (35,22) |
| Petalburg Woods | ETHER (4,8) 0x422; PARALYZE HEAL (4,26) 0x45D | GREAT BALL (45,7) 0x420 and X ATTACK (35,20) 0x41F: behind Cut |
| Rustboro | X DEFEND (36,51) 0x411, **only from Route 104's north strip, walking north at x=33** into a city pocket that has no link to the streets [05] (§10 C9) | |
| Route 116 (optional) | REPEL (10,17), POTION (34,7) [02] | ETHER (19,6) beside a Cut tree; X SPECIAL (55,12)†, HP UP (80,8)† [02, † = unverified reachability] |
| Rusturf Tunnel | POKé BALL (3,1) [02] | MAX ETHER (30,2)† |

### 4c. Hidden items (VERIFIED `bg_events`; reachability MODEL)

| Map | Reachable | Behind Cut |
|---|---|---|
| Route 104 | POTION (14,55), ANTIDOTE (16,72), HEART SCALE (16,64), all south; SUPER POTION (7,6), POKé BALL (3,9), both north | |
| Petalburg Woods | POTION (39,35), POKé BALL (4,19) | TINY MUSHROOM (26,6) and (40,29) |

The person-fair hint that hidden items exist is the woods boy's line (§2). Our AI has no hidden-item search (§6 gap 12).

### 4d. Berry trees, and the Mart

**Berry trees** (VERIFIED `new_game.inc:7-12`): they are solid objects. Picking from them is a human-like errand.
- Route 104 south: ORAN (22,41) and PECHA (24,41).
- Route 104 north: ORAN (3,23), CHERI (3,25), CHERI (34,6) and LEPPA (36,6).
- The SOIL_* trees start empty.

**Rustboro Mart** (VERIFIED `RustboroCity_Mart/scripts.inc:4-46`). Before `FLAG_MET_DEVON_EMPLOYEE`, which is set
after the badge on Route 116, it sells:
- Poké Ball, Potion, Super Potion, Antidote, Paralyze Heal, Escape Rope, Repel;
- X Speed, X Attack, X Defend.
- It sells **no Great Ball**.

**Why the free balls matter:** the bot ran out of balls before gym 1 in 18 of 38 runs (UNVERIFIED agent note [04 §2h]).

---

## 5. Wild species and where (VERIFIED `src/data/wild_encounters.json`, land slots summed)

| Map | Rate | Species, share, levels | Notes |
|---|---|---|---|
| ROUTE104 land | 20 | Poochyena 40% L4-5, Wurmple 20% L4, **Marill 20% L4-5**, Taillow 10% L4-5, **Wingull 10% L3-5** | Grass is mostly in the SOUTH half. On the north half the only grass is a north-west pocket, and the walking line has none (MODEL [05 §2b]) |
| ROUTE104 water and fishing | | Wingull/Pelipper by Surf; Magikarp by rod | Neither is available: no Surf, and the OLD ROD comes from Dewford, after the badge (VERIFIED [02 §3]) |
| PETALBURG_WOODS land | 20 | Poochyena 30% L5-6, Wurmple 25% L5-6, **Shroomish 15% L5-6**, Silcoon 10% L5, Cascoon 10% L5, Taillow 5% L5-6, **Slakoth 5% L5-6** | 325 grass tiles; the northbound spine crosses about 31 (MODEL) |
| RUSTBORO_CITY | | none | |
| ROUTE116 (optional) | | Poochyena 28% L6-8, Whismur 20% L6, Nincada 20% L6-7, Taillow 20% L6-8, **Abra 10% L7**, **Skitty 2% L7-8** [02] | The bot's training ground (L8 foes) [04 §2h] |
| RUSTURF_TUNNEL | | Whismur 100% L5-8 [02] | |

**For ROXANNE** (VERIFIED learnsets [02 §4.1]):
- SHROOMISH has Absorb from L1 and Stun Spore at L7.
- MARILL gets Water Gun only at L10, and the wild ones are L4-5.
- WINGULL has Water Gun from L1, but it is Water/Flying, so Rock moves hit it ×2.
- Shroomish, Seedot and Lotad can learn TM09 Bullet Seed.

**What points a person at a species:** SHROOMISH by the researcher and the Mart woman; SEEDOT by the school kid and the
trade house; RALTS by the trade house. The trap [04 §2h] (UNVERIFIED agent note): 16 of 19 lost catch battles were
Whismur using Uproar while the bot kept throwing.

---

## 6. OUR CODE GAPS, ranked by run-stopping risk, each with a concrete fix

The ranking follows [03 §0], re-ordered with the other angles and with the [00] adjudications. Code citations are
VERIFIED-code [03] on the 2026-10-15 working copy (step 5.1 uncommitted), except those tagged [00].

### Gap 1 — VERY HIGH: Route 104's halves, and the woods treated as an interior
- **The defect.** `OUTDOOR` excludes PETALBURG_WOODS (`goals.py:432`, VERIFIED [00]).
  - After the scene, `lead_toward` (`:455-485`) picks ROUTE104 as the nearest visited outdoor map.
  - The known route back through the SW door outscores the unused north exit (`explore.py:155`, `:288-291`).
  - Back on Route 104 south, `keeps_going` (`:492-502`) refuses the woods' "back" exits.
- **Why it is worse than [03] says.** No second enterable entrance exists (§0.1). So the expected end is `stuck: no
  progress for 120000 frames` on Route 104 south (trajectory UNVERIFIED).
- **The same defect bites later:**
  - `route_to` and `world_distance` (`explore.py:174-203`, `goals.py:435-452`) see ROUTE104 as one node linked to
    Rustboro, so every return north after a heal or whiteout in Petalburg is planned to an unreachable edge.
  - `_nearest_place` (`goals.py:1160-1180`) breaks a distance tie by NAME, so it picks
    `PETALBURG_CITY_POKEMON_CENTER_1F` over Rustboro's centre.
  - `_grass_map` (`:1624-1640`) prefers ROUTE104 over ROUTE116 on a tie.
- **Fix** (person-fair: learned from its own walking, as a person learns the woods by trying [04 §2b]):
  1. Mark a non-OUTDOOR map a **passage** once the AI's OWN memory shows it has exits leading to two outdoor places,
     or to two parts of one outdoor map that its walked tiles show are not joined. Treat a passage like OUTDOOR in
     `lead_toward` (`:473-475`) and `keeps_going`. Never key this on the map's name.
  2. Make the world graph region-aware. Split a map node into the components of tiles the AI has walked, and attach
     each exit and edge-crossing to the component it was seen from. Then ROUTE104-south reaches RUSTBORO through the
     woods.
  3. Make `_nearest_place` and `_grass_map` break ties by the AI's own walking distance from its current component,
     or by the centre it used last, never by name.
- **Proof.** The [03 §5] A/B, pre-registered in §9. Discriminator: the y of the arrival on ROUTE104 after the scene
  (below 31 means north, above 37 means south).

### Gap 2 — HIGH: ROXANNE can end the run, and nothing plans a type advantage
- **The defect.**
  - `MAX_LOSSES = 3` counts across chapters 1-4 (VERIFIED [00] `mode.py:103`).
  - A loss does not cause more training.
  - `TRAIN_SESSIONS` 8 counts a session that a rest cut short (`goals.py:189`, `:1474-1481`, `:395-403`).
  - The target is the ace's level plus a margin: Story 16, Catcher 17, Trainer 18 (`goals.py:1064-1067`).
  - The CATCH errand is OFF for all of chapter 4 (`:879-880`) and drawn once per map, so Route 104's two halves get
    one draw.
- **Fix.**
  1. Count losses per named fight, and keep a whole-run cap above it.
  2. After a loss to a named fight, raise that fight's target by a step and train before re-challenging.
  3. Count a session only if it won at least one battle or walked its steps.
  4. Allow the catch errand in chapter 4 when the AI has HEARD a counter-type hint (the gym guide, the Rustboro woman
     or the gym sign, §2) and owns nothing of that type.
  5. Choose the lead by the AI's own type memory and the hints it heard, never by a table it has not seen.
- **Proof.** A ROXANNE-loss fault arm (§9).

### Gap 3 — MEDIUM, certain to occur: the first live evolution (L16) and a move-learn mid-battle
- **The facts.** Every chapter-4 run crosses L16 near or inside the gym. The AI has never played an evolution live
  ([03] gap 3). B held during the animation cancels it (`evolution_scene.c:637-647`), and B on "learn the move?"
  answers NO (`:946-951`) [04 §4].
- **Fix.**
  - Advance evolution text with A only, and never hold B in an evolution scene.
  - Play the "Delete a move?" prompt from the screen: keep the type-useful move.
  - Add a fixture that crosses L16 mid-battle. One Torchic case is mandatory, because a cancel there loses Double Kick.
- **Proof.** Identity: same PID, new species. Fault arm: hold B (§9).

### Gap 4 — MEDIUM: "done" while a box is still up
- **The facts.** `FLAG_BADGE01_GET` turns on before TM39's text, and `VAR_SCOTT_STATE` before SCOTT's lines (§0.5).
- **The risks.**
  - The run ends mid-scene (`mode.py:437-438`, VERIFIED [00]), so a chained chapter-5 start would begin inside TM39's
    text.
  - A goal acting on "done" could walk or press A into the scene.
  - Whether PL-2 ("scenes first", `mode.py:113`) already covers this is UNVERIFIED.
- **Fix.** Act on a milestone's completion, and end a run, only when the screen is free: no text box, controls
  unlocked. Assert that in the chapter-4 end check.

### Gap 5 — MEDIUM: the default YES opens a party menu the play brain cannot handle
- **The defect.** The Rustboro House1 trader's YES runs `special ChoosePartyMon` (`RustboroCity_House1/scripts.inc:12-14`).
  `_story_menu` (`mode.py:572-583`) does not know that menu, so the result is `stuck: an unexpected party on screen`
  (`navigator.py:1014-1017`), replayed until `STORY_PATIENCE`.
- **Fix.**
  1. Teach the play brain to leave an unexpected party menu with B. That gives `PARTY_NOTHING_CHOSEN`, a clean decline.
  2. Make `answer_question` (`skills/story.py:83-91`) say NO to a trade it has no plan for. Key the rule on the words
     on screen ("trade").
- **Proof.** A copy beside the trader: the screen must be free within N frames.

### Gap 6 — LOW-MEDIUM: double battles
- **The facts.** The twins (forced with 2 usable Pokémon) and the gym's (1,9) two-trainer double. Doubles have been
  played only from step-4 fixtures. In a double the AI never switches, heals or runs (`brain/battle.py:1292-1293`).
  There is no fixture for a two-trainer double.
- **Fix.** Add fixtures for both, and read the target cursor per battler (`skills/battle.py:368-403`). Heal and switch
  in doubles can come later. The foes are L6-8.

### Gap 7 — MEDIUM as an amplifier of gap 1: frame budgets sized for chapters 1-2
- **The facts.** One `go` is 9,000 frames plus at most 2 battle extensions (`goals.py:200`, `:252-253`). Petalburg to
  Rustboro is longer, so decisions get re-made INSIDE the woods.
- **Fix.** Extend a `go` while new tiles keep being seen, with a hard cap. Size the run budget from development seeds
  (§9).

### Gap 8 — infrastructure, a SWEEP-stopper (not an AI-run stopper)
- **Disk** (VERIFIED [06 EN-2]): `C:` is 96% full. About 18 GB of `%TEMP%/ai_*` run folders have leaked. The cause is
  `rate_step5.run_one`'s `mkdtemp` with no cleanup (`rate_step5.py:352`).
- **Fix.** One sweep root per sweep, deleted after grading, and a free-disk preflight. Chapters 3-4 sweeps are longer.
  Deleting the existing folders is the user's or coordinator's call.
- **Tree drift** (VERIFIED [06 PR-5]): the sweep driver checks the tree's digest once, at the start.
- **Fix.** Add a `FrozenTree` re-check before each job and before writing evidence.

### Gap 9 — TEST DESIGN: the world memory must be carried
- **The trap.** A chapter-3 run started from a bot save has never "heard" DAD, so it explores with no goal
  (`goals.py:999-1002`; `world/memory.py:729`) [03 §1].
- **Fix.** Chain from the AI's own chapter-2 end state with its `world.jsonl` (`AI_PLAYER_WORLD` / `--world-in`). Never
  start from a bot save alone.

### Gap 10 — LOW, downgraded by [00]: the woods' north entrance `DEEP_SOUTH_WARP`
- **What [03] said.** `EXIT_PRESS` (`navigator.py:233-237`) has no entry for it, so it would be "pressed from the side,
  fail, and be remembered CLOSED".
- **What the decomp says** (VERIFIED [00]):
  - `DEEP_SOUTH_WARP` is a non-animated door (`metatile_behavior.c:262-270`). That makes it a warp behaviour
    (`field_control_avatar.c:751-765`), and a warp behaviour fires on any completed STEP onto the tile
    (`TryStartStepBasedScript`, `:155-160`, `:483-487`).
  - Our navigator's rule for a behaviour with no `EXIT_PRESS` entry is "warps when stepped on: any side"
    (`navigator.py:230-232`, VERIFIED [00]).
  - The tile's only open neighbour is the one above it (MODEL [05] render).
  - So the expected behaviour is correct.
- **Residual risk** (UNVERIFIED, live): coming out of the woods, the player stands on (10,30) or (11,30), and both are
  warps. A sideways step onto the other one re-enters the woods: a ping-pong. The `PINGPONG_USES` bound (3) ends the
  intent, not the run.
- **Fix.** None until a live run shows it. Add an `EXIT_PRESS`-style note that it is step-on.

### Gap 11 — NONE as a stopper: data errors in `milestones.json`
- **The errors.** `ch4_gym_trainers` and the `trainers` table (`:145-250`, `:1177-1241`) lack MARC (571, flag 1851,
  Geodude L8 ×2). Its "done" uses flags that ROXANNE sets.
- **Fix.** Add MARC. Make the milestone's proof "the battle with that trainer id was won BEFORE `BADGE01_GET`".
  `extract_milestones.py --verify` against pret should then catch it.

### Gap 12 — NONE as a stopper; a RULING 33 shortfall: gifts, hidden items, held items, items that count
- **The gaps.**
  - There is no gift goal. Gifts come only from a chance CHAT draw, one per person per run (`goals.py:896-903`,
    `:1118-1134`).
  - There is no hold-an-item skill, so the Quick Claw would sit in the bag.
  - There is no hidden-item search.
  - `Novelty._items` counts only balls and healing items (`navigator.py:564-567`).
- **Fix** (person-fair):
  1. An errand to talk to people inside buildings the AI enters (the teacher, the shop, the Cutter), weighted by
     personality.
  2. A hold-item step after receiving a holdable item.
  3. A hidden-item search, unlocked by hearing the woods boy's line, that presses A on suspicious dead-ends while
     walking.

### Gap 13 — LOW: diagonal ledges
- **The facts.** `world/memory.py:105-107` still says "none on v1's maps". Route 104 has `MB_JUMP_SOUTHWEST` at
  (28,55) and (30,57) [05].
- They never jump (VERIFIED [00]). `GetLedgeJumpDirection` checks only the four cardinal behaviours
  (`event_object_movement.c:7631-7653`, `metatile_behavior.c:151-173`). So "treat them as walls" is CORRECT.
- **Fix.** Correct the docstring only.

### Gap 14 — a GATE to build BEFORE chapters 3-4: the person-fair data door [06 PL-7]
- **The risk.** `progress.marks` reaches the brain as an open dict (`brain/goals.py:381`; `mode.py:395,417,587`). This
  folder is full of developer coordinates.
- **Fix.** `check_fairness.py`:
  - (a) `.marks` may be read only inside an allowlist;
  - (b) no AI module subscripts `x`, `y`, `measured` or `decomp` in its knowledge;
  - (c) the knowledge files pass a schema allowlist.
  - Fault plants: an errand keyed on a mark, and a coordinate read. A docstring that mentions `.marks` must NOT be
    refused.

---

## 7. Traps the bot hit here (lessons, not code; RULING 35: the bot is a teacher only)

From [04 §2-§4] (VERIFIED against `08-MISTAKES.md`, `05`, `12` and the bot code, as cited there), plus the
process lessons from [06] that apply to a chapter-3/4 build.

1. **A scene can run while the game state reads OVERWORLD.**
   - SCOTT's scene never advanced under "press B only when not in the overworld" (`08-MISTAKES.md:175-189`).
   - Judge "a box is up" from the screen, never from the game state. A scene's var can flip at its START.
2. **"I can see the town" is not "I can walk there"** (ML-7).
   - Route 104 cost the bot hours, then recurred twice: a reachability read of 31/200 tiles, and a position-blind
     training picker that killed 319 runs (`08-MISTAKES.md:135-154`, `:2878-2917`, `:16700-16726`).
   - Map edges do not mean connected halves.
3. **A trainer battle cannot be fled** (ML-8). Heal before a stretch with trainers while the team is tiny.
4. **A door is entered by a completed step, from the right side** (ML-9).
   - The test harness's extra per-frame reads shifted the timing and HID the bug (`08-MISTAKES.md:190-216`).
   - A harness must not perturb timing.
5. **A scene that interrupts walking is the story, not an obstacle.** Ride it out and resume. And never aim at a tile
   you have not seen to be walkable: a hard-coded woods target was a tree, and 67 of 67 legs derailed
   (`08-MISTAKES.md:22350-22359`).
6. **Detect not getting closer; never mash A next to a person.**
   - KI-15 was a post-battle oscillation on Route 104 north.
   - An every-frame A nudge re-opened the Rustboro nurse in a loop (`08-MISTAKES.md:981-1000`).
7. **Decide where you are in the story from what has happened, not from the map you stand on.** A Route 116 save
   re-ran the woods travel (`07-CHANGELOG.md:1301-1308`).
8. **Local grass is too weak to train for ROXANNE.**
   - Route 104 and the woods are L3-6, so the bot trained on Route 116 (L6-8).
   - Run from a catch that is going badly (Whismur's Uproar; UNVERIFIED note).
9. **The gym.**
   - A switch into a weak bench hung (KI-8).
   - An L16 move-learn froze the handler (ML-10/ML-13).
   - "Lead strongest" fails against a type counter (`08-MISTAKES.md:423-431`).
   - Read the prompt on screen, and lead with the type that wins.
10. **B can throw the gym away:** it cancels the evolution and refuses the move (§6 gap 3).
11. **Process** [06]:
    - grade the PROPERTY, not the label (PF-1);
    - a fault arm must REACH its state, with a reach floor (PF-4);
    - grade on held-out seeds, with bounds registered before the run (PF-7, PF-8);
    - identical output is a replay, not a replication (PF-9);
    - a unit-tested rule is not a chapter proof (PF-12: "ROXANNE by her badge alone" has no live arm yet);
    - never change the tree a sweep runs on (PR-5);
    - state results only for the tree the evidence names (PR-3).

---

## 8. Developer-side map facts for proof design (⛔ NEVER AI hints)

All from [05] and [01]. Map ids, sizes and warps are VERIFIED. Paths, chokes and seams are MODEL.

### 8a. The maps
| Map | (group, num) | Size | Connections and warps |
|---|---|---|---|
| ROUTE104 | (0,19) | 40×80 | up → RUSTBORO (offset 0); right → PETALBURG (offset 50); down → ROUTE105 (Surf only). Woods doors: N (10/11,30) `DEEP_SOUTH_WARP`; SW (10/11,38) and SE (32/33,42) `NON_ANIMATED_DOOR`. Briney's cottage (17,50); flower shop (5,18) |
| PETALBURG_WOODS | (24,11) | 48×44 | warps only: N (14/15,5) `NORTH_ARROW_WARP` (stand on it, hold UP); SW (16/17,38) and SE (36/37,38) `SOUTH_ARROW_WARP` (hold DOWN). `allow_escaping: false`; weather SHADE |
| RUSTBORO_CITY | (0,3) | 40×60 | up → ROUTE115; down → ROUTE104; right → ROUTE116. Animated doors (collision 1; press UP from the tile below): gym (27,19), Pokémon Center (16,38), Mart (16,45), school (27,34), Cutter (9,38). Devon (11/12,15): step on |
| RUSTBORO_CITY_GYM | (11,3) | 11×20 | exits (5,19)/(6,19), arrow warps (hold DOWN); ROXANNE at (5,2), talk from (5,3) |

- ⚠ The unused maps `MAP_ROUTE104_PROTOTYPE` (27,0) and `..._PRETTY_PETAL_FLOWER_SHOP` (27,1) exist. A name match on
  `ROUTE104*` picks them up (`map_data.py:1344-1345`).

### 8b. Seams (walkable edge crossings, MODEL)
- Route 104 x=39 ↔ Petalburg x=0 at **y=62..63** only.
- Route 104 y=0 ↔ Rustboro y=59 at **x=12..19**, plus **x=33** (the pocket with the X Defend).
- Rustboro x=39 ↔ Route 116 at y=8..13.
- Rustboro top ↔ Route 115 at x=19..23. A wandering AI can leave north here; it is not on the story path.

### 8c. Chokes and one-ways (MODEL)
- **The band.** Route 104 rows y=31..37 are solid: the halves are linked only through the woods.
- **The SE pocket** (x≈29..33, y=42..56) can be left by ledges but never entered. It holds the Poké Ball (29,53) and
  the woman at (30,50).
- **Woods ledges** all jump SOUTH. They make the northbound route unique; going south has slack. Removing the scene
  tiles (26/27,23) cuts every northbound path. **Southbound, every woods trainer can be avoided.**
- **The bridge deck** (27/28,16): the twins.
- **The Winston column** x=21, rows 22..26.
- **Rustboro's main road** x=12..19.
- **The gym plaza** exit column x=23: the post-badge theft scene.

### 8d. Shortest static walks (MODEL; [01] and [05] differ by 1-3 steps through start tiles and counting, §10 C11)
| Segment | Steps |
|---|---|
| Petalburg edge → woods SW door | 51 (52 avoiding CINDY) |
| Woods SW door → N exit | 84-85, 31 grass tiles |
| Woods N exit → Rustboro edge | 54, 0 grass tiles |
| Rustboro south edge → gym door tile (27,20) | 47-50 |
| Rustboro south edge → Pokémon Center | 23-24 |
| Gym door → (5,3) | 23-24 shortest; about 30 avoiding all three trainers |
| **Chapter 3 minimum** (Petalburg → Rustboro) | **about 190 steps** |
| **Chapter 4 minimum** (Rustboro edge → ROXANNE) | **about 71 steps** |
| **Whole of ch3-4** | **about 261 steps** [01 §10], excluding battles, turning and errands |

### 8e. Static-reader traps [05 §6]
1. **Hidden-at-New-Game objects are still in `map.json`.** The Route 104 rival sits ON the cottage door (17,50). The
   woods grunt and researcher are the opposite case: they have hide flags but ARE visible until the scene.
2. **Scripts move objects.** The rival goes to (17,52); the Rustboro scientist and Devon employee move too.
3. **Animated doors have collision 1.** A BFS must target the tile below and press UP.
4. **Arrow warps fire on HOLDING the direction while standing on the tile.** Non-animated doors and `DEEP_SOUTH_WARP`
   fire on stepping onto the tile (VERIFIED [00]).
5. **Cut trees use TEMP flags and REGROW** on every map load. `ClearTempFieldEventData` zeroes the TEMP flags
   (`event_data.c:39-42`), and the map-load paths call it (`overworld.c:798`, `:848`) (VERIFIED [00]).
6. **The map edge is not the seam:** the walkable part is the intersection of both maps' edges.
7. **Indoor maps report fake edge reachability.**
8. **Fetch hazard.** `gh api .../contents/<file>.bin` can corrupt binaries (the woods' `map.bin` came back as 5914
   bytes, not 4224). Fetch by blob sha and assert `len == size` [01 §13][05 §8].

### 8f. Re-derivation
The MODEL scripts were in session scratchpads and are not kept: `ch34a_paths.py` [01], `audit03_*.py` [03], and
`analyze.py`, `chokes.py` and `shortest.py` [05]. The algorithm is in [05 §8]. A permanent home would be
`tools/story-dev/`, if the user wants one.

---

## 9. DRAFT pre-registration for the chapter 3 and chapter 4 proofs

⚠ **DRAFT.** Every bound below is a PROPOSAL with its reason. Bounds are registered in the driver BEFORE the first
graded run. They are set from DEVELOPMENT seeds only, never loosened after a graded result, and anything set after
observation is labelled RE-REGISTERED and re-run as a replay [06 PF-8].

**Common rules (all chapters):**
- **Seeds.** Graded seeds are held out, never used in development, and never re-graded after a failure. Record them in
  a committed seed ledger if PF-7's gate exists by then; otherwise in the evidence header and README.
  ⚠ `--first-seed` defaults to 1, a development seed (`rate_step5.py:1443`).
- **Ground truth** is read by the HARNESS from `gSaveBlock1` flags and vars, the framework's reads and the decomp
  values in §1. It never uses the AI's own constants [06 PF-6].
- **Identity, never counts.** A battle is identified by its trainer id, a Pokémon by its PID, an evolution by the same
  PID with a new species (CLAUDE.md rule 3).
- **Every fault arm** declares the state it must REACH, with a reach floor. 0.6 is the LOSE3 precedent
  (`rate_step5.py:300`). Grade only the runs that reached it [06 PF-4].
- **Every metric** must FAIL its control arm (no-op or beeline) before it is a claim [06 PF-3].
- **The tree is frozen** for the whole sweep (PR-5). Name the tree in every result (PR-3).
- **The start fixture** is the AI's OWN previous-chapter end state, chained, with its `world.jsonl` (§6 gap 9). Use
  COPIES only. Never write into `tools/story-dev/saves/`.

### 9a. Premise probes to run FIRST (developer probes; each one's arms must DIFFER)
| Probe | Fixture | Arms | Discriminator (computed in advance) | Why it comes first |
|---|---|---|---|---|
| P1 woods choke | a copy at the woods' SW door, state 0 | the AI's own walk north | `VAR_PETALBURG_WOODS_STATE` turns 1 before the map changes to Route 104 via the N exit | Settles §10 C1. ch3's proof stands on it |
| P2 twins | a copy on Route 104 north, below the bridge | A: 1 usable Pokémon; B: 2 usable | A: no battle on crossing (27/28,16). B: a double (battle type flags show DOUBLE) | The arms differ by construction (`CheckTrainer`). Confirm the fixture's "usable" count: eggs and fainted Pokémon do not count |
| P3 gym (1,9) | a copy inside the gym, all three trainers undefeated | A: 1 usable; B: 2 usable; step onto (1,9) | A: single battle, one trainer. B: TWO_OPPONENTS double, TOMMY + MARC | Settles §10 Q3. A gym proof must not assume "3 singles" |
| P4 after-badge flags | the AI's ch4 end state, or a probe that beats ROXANNE without fighting the trainers | read 0x640, 0x641, 0x73B after the badge | all three set although unfought | Proves the after-badge read is VACUOUS, so the "fought" check must read before the badge |
| P5 gap-1 A/B | the moment after the scene (or at its trigger) | A: current code; B: the passage/region fix | the y of the arrival on ROUTE104 after leaving the woods: A predicted > 37 (south), B < 31 (north) | Must show the arms differ. If A also goes north, gap 1 is refuted and its fix is not needed |
| P6 theft trigger | a post-badge copy in the gym plaza | walk west across x=23 | the scene starts; the `VAR_RUSTBORO_CITY_STATE` value afterwards is RECORDED (UNVERIFIED as 2) | Sets the chapter-5 start and the chapter-4 end state |

### 9b. Chapter 3 proof: "Petalburg to Rustboro, through the woods"
- **Start.** The AI's chapter-2 end, after DAD's speech (`VAR_PETALBURG_GYM_STATE` = 2), with `world.jsonl` carried.
  - Premise conjunct: `VAR_PETALBURG_WOODS_STATE` == 0 and `FLAG_VISITED_RUSTBORO_CITY` clear at the start. The proof
    must be able to fail.
- **PASS needs all of:**
  1. `VAR_SCOTT_PETALBURG_ENCOUNTER` == 1 (the forced scene was sat through).
  2. `VAR_PETALBURG_WOODS_STATE` == 1, AND `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT` set. Two independent witnesses.
  3. Grunt trainer flag 0x50A set (won), and the AI's battle log shows trainer id 10 won. The two must agree.
  4. `FLAG_VISITED_RUSTBORO_CITY` set.
  5. The run ends with the screen free.
  6. PL-1 never-idle holds on both paths, and the second path is shown to see the woods scene's screens (a STALL-style
     arm, [06 PF-1]).
- ⚠ "Rustboro implies the woods var is 1" holds BY CONSTRUCTION if P1 holds. It is a model-consistency check, not
  evidence of AI behaviour. Say so in the verdict.
- **REPORTED (no floor until development data exists):**
  - steps against about 190;
  - wild battles, catches (new PIDs with the player's OT) and species;
  - route trainers fought, by id;
  - gifts by flag (0x106, 0xF6, 0x5E, 0x7F);
  - item-ball flags picked up;
  - which hints were HEARD (DAD, the route sign, the grunt);
  - heals and whiteouts;
  - whether the twins fired, and the usable count at the time.
- **Fault arms:**
  - **WOODS_INTERIOR**: revert the gap-1 fix. Expected: no `FLAG_VISITED_RUSTBORO_CITY` within the budget, ending on
    patience. Reach: the scene var reached 1 in at least 0.6 of runs.
  - **NO_DAD**: start without the carried world memory. Expected: a measurable drop in goal-directed walking. Reported,
    with a separation bound set from development seeds.
  - **FAIRNESS plants** (gap 14): the gate refuses a mark-keyed errand and a coordinate read.
- **Bounds (with reasons):**
  - Run frames = the 95th percentile of development seeds × 1.5, rounded up. That covers the long tail without hiding
    a stall.
  - Proposed floor: not under the 330,000 used by the chapter-sized step-5 runs (`README.md:388-389`), because chapter
    3 is longer and the woods have 325 grass tiles.
  - `STORY_PATIENCE` stays 120,000 (`mode.py:102`). It is the stall detector, and the WOODS_INTERIOR arm proves it
    fires.
  - Wall clock: the same × 1.5 rule. Record the learner's lane count in the header [06 EN-6].

### 9c. Chapter 4 proof: "Rustboro to the STONE BADGE"
- **Start.** The AI's chapter-3 end, in Rustboro, chained.
  - Premise: `FLAG_BADGE01_GET` clear, and 0x640, 0x641 and 0x73B clear.
- **PASS needs all of:**
  1. `FLAG_DEFEATED_RUSTBORO_GYM` and `FLAG_BADGE01_GET` set, and `VAR_RUSTBORO_CITY_STATE` == 1.
  2. The screen is free at the end (gap 4). The TM39 text must not be left half-read.
  3. The battle with trainer id 265 is in the AI's log as WON, and the run's loss count agrees with the game (PL-9).
  4. PL-1 never-idle holds.
- **Sampled BEFORE ROXANNE's battle starts** (the gym trainers): 0x640, 0x641 and 0x73B, plus the AI's battle log by
  trainer id. **REPORTED, never required** [06 PF-12], because they are optional and avoidable (MODEL).
- **REPORTED:**
  - `FLAG_RECEIVED_TM_ROCK_TOMB` (it fails only with a full bag);
  - `FLAG_RECEIVED_QUICK_CLAW`, `FLAG_RECEIVED_HM_CUT` and the Premier Ball;
  - each party PID's level and species at the start of ROXANNE's battle, against her ace (L15) and the personality's
    target;
  - the types of the moves used against her;
  - whether the gym guide or the FIRE/ROCK woman was HEARD before the fight;
  - losses to ROXANNE, and the training done between attempts;
  - whether any (1,9) double fired.
- **Fault arms:**
  - **TRAINERS_MANDATORY** (mutant G74 [06 PF-12]): the "badge alone" claim must be lost.
  - **AFTER_BADGE_READ**: the trainer check moved after the badge must PASS vacuously. That proves why it is sampled
    before (P4).
  - **HOLD_B_EVOLVE**: the hands hold B in an evolution. Expected: the same PID keeps its species at L16 and the
    "evolved" report flags it. Reach: the PID crossed L16 in the run, floor 0.6.
  - **ROXANNE_LOSS**: from a copy where an L15 Torchic loses to her, the next decisions must TRAIN before the next
    challenge, and a third loss in the run must not end a gym it could win after training (gap 2). Reach: a loss
    happened.
  - **TRADE_YES**: a copy beside the House1 trader; the screen must be free within N frames, with N set from
    development (gap 5).
- **Bounds:**
  - The run-frame rule from 9b. Training makes chapter 4 longer: PATIENCE showed training stints of 58k-96k frames
    against 120,000 (`README.md:1191`, [06 PL-5]). Re-measure them in chapter 4 before keeping 120,000.
  - `MAX_LOSSES` stays as is until gap 2's fix lands. Then register its new per-fight value before any graded run.
  - Steps against about 71, reported.

---

## 10. ⚔ ADVERSARIAL: contradictions between the angles, and open questions (THIS SECTION RULES)

### 10a. Contradictions (both sides; the status says what settles each)

| # | Topic | Side A | Side B | Status |
|---|---|---|---|---|
| C1 | Is the woods scene avoidable going north? | [04 §2e]: UNVERIFIED; "if a path bypasses (26-27,23), neither ch3 milestone ever completes" | [01 §0.2], [03 §1], [05 §0.3]: MODEL, three independent static scripts; removing the two tiles cuts every northbound path | **OPEN until P1 runs.** Three agreeing models are still MODEL. They share one input (`map.bin`) and the same approximations (no wanderers) |
| C2 | Do the woods trainers stand on the route? | [03 §2.2]: LYLE and JAMES are "off the forced corridor" | [01 §3]: every northbound path crosses a line each can face. [05 §3c]: LYLE is timing-dependent; JAMES only if facing east at row 14 | Probably no real conflict: [03] means the scene's corridor. **[01]/[05]'s tile-removal tests are the relevant ones.** Expect 0-2 woods trainer battles, by timing |
| C3 | How many woods entrances can be entered from Route 104 south? | [03 §2.1]: "only an unused second entrance is left … once both are used" | [01 §0.1], [05 §0.2]: only the SW door; the SE door's pocket is exit-only (ledges) | **[01]/[05] rule (MODEL).** Gap 1's stall is MORE likely than [03] states |
| C4 | How does Route 104's `DEEP_SOUTH_WARP` (10/11,30) fire? | [03 §2.3]: "warps only on a SOUTH press while standing on it" (self-marked UNVERIFIED) | [05 §2a]: step onto it; it counts as a non-animated door | **SETTLED [00], VERIFIED: B.** `metatile_behavior.c:262-270` → `field_control_avatar.c:751-765` → fired on a step (`:155-160`, `:483-487`). `overworld.c:933-934` only sets the arrival facing (NORTH). Gap 7 of [03] is downgraded (§6 gap 10) |
| C5 | Can a diagonal ledge be walked or jumped? | [03] gap 9: UNVERIFIED | [05 §2b]: "effectively walls (UNVERIFIED that a diagonal behaviour never jumps)" | **SETTLED [00], VERIFIED:** never jumps (`event_object_movement.c:7631-7653`; `IsJumpSouth`/`IsJumpWest` match only the cardinal values, `metatile_behavior.c:151-173`). Walls, given the tiles' collision bits (MODEL) |
| C6 | Do the Cut trees regrow? | [01 §14.5] and [05 §6.4]: UNVERIFIED | none | **SETTLED [00], VERIFIED: yes.** TEMP flags are zeroed on each map load (`event_data.c:39-42`; `overworld.c:798`, `:848`) |
| C7 | Black Glasses before the badge | [02 §0.2]: UNVERIFIED; Gemini says "needs Verdanturf access" | [01 §0.7], [03 §3]: MODEL, unreachable on foot from Rustboro; [03]: the region stops at x=60 even with the Cut trees removed | Two models agree: **not in ch3-4 (MODEL).** A `calculate_path` check from a real Route 116 position, with a control tile that DOES path, would settle it (`00-READ-THIS-FIRST` gate). No escalation needed: RULING 33 says "if it can reach them" (`06:9160`) |
| C8 | Route 104 PP Up | [04 §6]: "may be behind the Cut tree (35,22)", UNVERIFIED | [01 §4], [05 §0.8]: a pond islet, needs Surf; [03]: unreachable from the north path | **[01]/[05] rule (MODEL).** Out of window either way |
| C9 | Rustboro X Defend (36,51) | [01 §5], [03 §3]: reachable | [05 §0.8]: reachable ONLY from Route 104's north strip at x=33, into a pocket with no link to the streets. [02]: unverified | Compatible, but **[05] is the one that matters for an expectation:** an AI that only walks Rustboro's streets can never see it |
| C10 | Is the Woods Shroomish real? | [04 §5b]: UNVERIFIED that Shroomish is in the woods table | [01 §8], [02 §3], [05 §8]: VERIFIED, 15% in `wild_encounters.json` | **[01]/[02]/[05] rule (VERIFIED)** |
| C11 | Step counts | [01 §10]: SW door → N 85; gym 24; Rustboro edge → gym 47; → PC 23 | [05]: 84; 23; 50 (from (16,59)); 24 | Start tiles and counting conventions differ. **Use them as orders of magnitude; never as bounds without re-deriving** |
| C12 | Torchic "hard" for ROXANNE | [02 §4.1]: hard (no super-effective move until L16) | [04 §1]: 460 of 460 bot Torchic wins came as a Combusken with Double Kick, and 0 starter faints | Both true: hard UNEVOLVED. That puts the weight on gap 3 (do not cancel the evolution) |
| C13 | The team's level at ROXANNE | [02 §4.2]: Gemini says L10-16 (UNVERIFIED) | [04 §1]: the bot's starter line was at L16-17 AFTER the gym. [03]: our targets are Story 16, Catcher 17, Trainer 18 | Never set a bound from the Gemini figure (CLAUDE.md: grade Gemini's names, not its numbers). [04]'s are measured, but bot-specific |
| C14 | Where the woods scene fires | `milestones.json` `ch3_woods` `taught_by` (via [05 §0.3]): "just inside the Woods south entrance" (the bot's segment start) | decomp coord_events: (26,23)/(27,23), 15 rows north | **The decomp rules (VERIFIED).** A proof expecting the scene on entry fails |
| C15 | When the run ends vs the theft scene | [03 §2.6]: the run ends at the badge, so the theft scene falls after it | [01 §0.9], [05 §0.9]: the chapter-4 end proof must expect the scene if the AI walks after the badge | Both hold: the end depends on whether chapter 4 stops at the badge or a chapter-5 run continues. **A chained chapter 5 starts mid-TM39 text (gap 4) and then meets this scene (P6)** |
| C16 | AMULET COIN's conditions | [01 §0.7], [02 §0.2]: after `FLAG_BADGE05_GET` | [03 §3]: BADGE05 and after the PokéNav registration | Out of window either way. Already RULING 17 (`06:7362`). Not settled here |
| C17 | Citations of the double-battle rule | `trainer_see.c:279-285` [05]; `:283` [03]; `pokemon.c:4527-4544` [01] | | Same rule, different lines quoted. **No conflict in substance** |

### 10b. Open questions (nobody has settled these)

- **Q1. How many usable Pokémon will the AI have at the twins and in the gym?** The bot arrived in Rustboro with a
  single L13 Mudkip [04 §7.5], but our AI catches in chapters 1-2. This decides whether the twins and (1,9) are live
  risks at all. Measure it on the chapter-2 end states.
- **Q2. The gap-1 trajectory** is reasoned from code and has never been run (P5).
- **Q3. Does (1,9) really start TOMMY + MARC as one double?** The rule is read and the overlap is MODEL (P3).
- **Q4. Do CINDY and WINSTON use their FULL RESTORE?** That depends on battle-AI item logic, which nobody read [01 §7].
- **Q5. Is 8 training sessions enough** to reach L16-18 on L3-6 foes? [03 §4] estimates 2-6 battles a session may fall
  short (UNVERIFIED). Measure it on development seeds.
- **Q6. Does PL-2 ("scenes first") already stop the AI acting mid-TM39 text** (gap 4)? Read `mode.py` and the story
  skills, or run it.
- **Q7. Which Route 116 trainers stand west of the reachable limit (x=60)?** That decides the optional pre-gym training
  there. Not mapped by any angle.
- **Q8. Does the RUSTBORO Pokémon Center 2F have back-wall doors with no warp,** like OLDALE's and PETALBURG's? That
  costs time only [03 §2.5].
- **Q9. Is `OBJ_EVENT_GFX_ROXANNE` = 125?** It is in `milestones.json` and was not re-read [03 §1]. `--verify` should
  cover it.
- **Q10. The second path of the never-idle check** must be shown to see the woods scene's and the gym's input screens
  (a STALL-style arm) [06 PF-1].
- **Q11. Proof hygiene in the regression running now.** [06] notes that no skill (`story-drive`, `unlazy`) mentions
  `ai_player`, so the living lessons are not loaded into AI-player rounds. That is a process gap for the coordinator,
  not a game fact.

*Sources: the six angle notes in this folder (01-06). The synthesis's own decomp reads (pret/pokeemerald master,
2026-10-15): `src/metatile_behavior.c`, `src/field_control_avatar.c`, `src/field_player_avatar.c`, `src/overworld.c`,
`src/event_data.c` and `src/event_object_movement.c`, kept in the session scratchpad (`synth/`), not committed. Our
tree, read-only: `ai_player/brain/navigator.py:225-237,920-936`, `brain/goals.py:428-432`, `mode.py:100-104,437-438`,
`knowledge/milestones.json` (a grep for MARC/1851 and the ch3/ch4 ids), and `06-DECISIONS-LOG.md:7362,9135-9161`.*
