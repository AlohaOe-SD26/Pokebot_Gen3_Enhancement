# Ch3-4 recon, angle 02: how a person plays it, what the game tells them, and one Gemini list adjudicated (2026-10-15)

> **STATUS: NOTE, not truth** (CLAUDE.md, "Gemini research notes"). Written by a Claude research subagent, read-only.
> - **VERIFIED** = read in pret/pokeemerald (fetched raw with `gh api repos/pret/pokeemerald/contents/<path>` on
>   2026-10-15) or in our own code, with the citation. Line numbers are those of the fetched master files.
> - **UNVERIFIED** = recall or human-play estimate. It must not set a code threshold without the user's agreement.
>
> ⛔ **PERSON-FAIR (USER RULINGS 35-37).** Coordinates, flags, map ids and routes below are for the DEVELOPERS:
> designing proofs, expectations and fault arms. Never feed them to the AI as hints. The only things the AI may be
> told are the on-screen words quoted in §1, and only at the level the game itself says them.
>
> Scope: from the end of WALLY's catching tutorial (DAD's speech in the Petalburg Gym) to ROXANNE's STONE BADGE and
> TM39. Includes the optional areas reachable in that window: Route 104 (south and north), the beach, Mr. Briney's
> cottage, the flower shop, Petalburg Woods, Rustboro City, Route 116 and the Rusturf Tunnel mouth.

## 0. Headlines (each carries its caveat)

1. **The game names the destination exactly twice, and both times it is DAD's speech:** "Head for RUSTBORO CITY beyond
   this town … challenge the GYM LEADER, ROXANNE". After that, the guidance is **two route signs**: `ROUTE 104
   → PETALBURG CITY` on the south part, which points BACK east, and `ROUTE 104 ↑ RUSTBORO CITY` at the north end. A
   third hint is the Aqua grunt's "after something in RUSTBORO". Nothing in the window tells the player to enter
   Petalburg Woods by name. The woods are simply the way north (VERIFIED: the texts are in §1, and the warps put the
   woods between the two halves of Route 104: Route104 `map.json` warps (10,30) (11,30) north and (10,38) (11,38)
   (32,42) (33,42) south).
2. **Correction to USER RULING 33's gift list (VERIFIED):**
   - The **AMULET COIN is NOT in chapters 3-4.** MOM gives it in Littleroot only after `FLAG_BADGE05_GET`, the
     Balance Badge (`data/scripts/players_house.inc:307-317`).
   - The **QUICK CLAW** is in the window: the Trainer's School teacher gives it with no gate
     (`RustboroCity_PokemonSchool/scripts.inc:77-90`).
   - The **BLACK GLASSES** are a HIDDEN item on Route 116 at (70,13), `FLAG_HIDDEN_ITEM_ROUTE_116_BLACK_GLASSES`
     (`flags.h:642`), next to a man whose line hints at them: "I dropped my glasses… Can you help me find them?"
     (`Route116/scripts.inc:413`). ⚠ Whether (70,13) can be reached BEFORE Roxanne is **UNVERIFIED**. It lies east of
     the Rusturf Tunnel mouth, and Gemini claims it "normally requires Verdanturf access". The routing angle must
     settle this with a pathfind from a real position plus a control tile.
3. **HM01 CUT can be obtained BEFORE Roxanne (VERIFIED).** The Cutter has no badge check
   (`RustboroCity_CuttersHouse/scripts.inc:4-13`). Two in-window lines point a person to him:
   - SCOTT, in the Trainer's School: "The first thing you should do is to have a POKéMON learn the move CUT. If I
     remember correctly, someone in this town has CUT." (`RustboroCity_PokemonSchool/scripts.inc:300-314`);
   - a man in the Pokémon Center: "The man next door gave me an HM!" (`RustboroCity_PokemonCenter_1F/scripts.inc:43`).

   Using Cut in the field still needs the STONE BADGE, as the Cutter says himself (`…/scripts.inc:36`).
4. **Gemini adjudication (§5):**
   - About 95 names were checked.
   - **Flags (35 named):** 25 CONFIRMED and 1 with unclear timing. 5 are NOT DEFINED: 4 invented gift flags
     (`…TM09`, `…HM01`, `…TM39`, `…GREAT_BALL_PETALBURG_WOODS`) and 1 invented hide flag. 4 are real names given the
     wrong MEANING.
   - **Trainers (20):** 8 fully CONFIRMED. 11 had the wrong level, count or class, and 1 had the wrong constant
     (`TRAINER_JOEY_1`).
   - **Script and text labels:** 3 of 8 NOT FOUND.
   - Exactly as CLAUDE.md predicts: the NAMES are mostly good, and the descriptions and party details are not.
5. **Starter matchup (VERIFIED type chart and learnsets):**
   - Mudkip (Mud-Slap at L6, Water Gun at L10) and Treecko (Absorb at L6) hit Geodude 4x / 2x and Nosepass 2x.
   - **Torchic has NO super-effective move until Combusken's Double Kick at L16.** Its Ember is 0.5x against both of
     Roxanne's species, and Roxanne's Rock Tomb is 2x against it.
   - Two in-window lines say so: the Gym Guide ("can't stand WATER-type and GRASS-type moves") and a Rustboro woman
     ("FIRE-type POKéMON don't match up well against ROCK-type POKéMON").

## 1. Every line that points the player somewhere, in the order a person meets them (VERIFIED quotes)

The coordinates in brackets are DEVELOPER-ONLY.

### 1.1 Petalburg Gym, the moment the tutorial ends
- **WALLY's goodbye** (`PetalburgCity_Gym/scripts.inc:1180`): "…Oh! My mom's waiting for me, so I have to go!"
- **DAD's directive**, said once, automatically (`PetalburgCity_Gym_Text_DadGoCollectBadges`,
  `PetalburgCity_Gym/scripts.inc:1193-1208`, played by `…_EventScript_ReturnFromWallyTutorial` at :76-93, which then
  sets `VAR_PETALBURG_GYM_STATE` to 2 at :90): "DAD: Now… {PLAYER}, if you want to become a strong TRAINER, here's my
  advice. Head for RUSTBORO CITY beyond this town. There, you should challenge the GYM LEADER, ROXANNE. After her, go
  on to other POKéMON GYMS and defeat their LEADERS. Collect BADGES from them, understood? Of course, I'm a GYM
  LEADER, too. We'll battle one day, {PLAYER}. But that's only after you become stronger."
- **If the player talks to DAD again** (state 2, `PetalburgCity_Gym_Text_NormanGoToRustboro`, :1210-1218): "DAD: Hm?
  Aren't you going to the POKéMON GYM in RUSTBORO CITY? There's no challenge for me to battle a greenhorn TRAINER. …
  I'll battle you, {PLAYER}, when you can show me four GYM BADGES, okay?" This is a **repeatable** person-fair
  reminder, and a good fallback hint source for a forgetful personality.
- ⚠ "Beyond this town" gives NO compass direction. A person infers "west", because they came from the east.
  Petalburg's own sign says only `PETALBURG CITY "Where people mingle with nature."` (`PetalburgCity/scripts.inc:719`).

### 1.2 Petalburg's west exit: SCOTT's cutscene (no battle, no direction)
- Coord triggers at x=4, y=10..13 on `VAR_SCOTT_PETALBURG_ENCOUNTER == 0` (PetalburgCity `map.json` coord_events;
  script `PetalburgCity_EventScript_Scott`, `PetalburgCity/scripts.inc:518-543`). The script sets `VAR_SCOTT_STATE` 1
  at :525 and `VAR_SCOTT_PETALBURG_ENCOUNTER` 1 at :540.
- What he says (:726-741): "Excuse me! Let me guess, from the way you're dressed, are you a POKéMON TRAINER?" … "Well,
  maybe not. Your clothes aren't all that dirty. You're either a rookie TRAINER, or maybe you're just an ordinary
  kid." … "I'm roaming the land in search of talented TRAINERS. I'm sorry to have taken your time."
- Developer note: it is the first scene of chapter 3, a forced scene the AI has to sit through on its first walk
  west. It is not in `milestones.json`.

### 1.3 Route 104, south (Petalburg side, the beach, the cottage)
- Sign at (27,66): `ROUTE 1O4 {RIGHT_ARROW} PETALBURG CITY` (`Route104/scripts.inc:1045`). It points BACK to
  Petalburg, so a person reads it as "Rustboro is the other way".
- Sign at (20,50): `MR. BRINEY'S COTTAGE` (:1042).
- Girl at (25,49): "That seaside cottage is where MR. BRINEY lives. He was once a mighty sailor who never feared the
  sea, however stormy." (:984)
- **The cottage is EMPTY in this window (VERIFIED):** `FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY` and `…_PEEKO` are set at New
  Game (`data/scripts/new_game.inc:132-133`). A curious person walks in and finds nobody.
- Catching advice:
  - Boy at (27,63): "If you're going to throw a POKé BALL, weaken the wild POKéMON first. It will be easier to catch
    if it's been poisoned, burned, or lulled to sleep." (:995)
  - Woman at (30,50): "…You should throw POKé BALLS only at wild POKéMON." (:1001)
- Girl at (28,74): "…if TRAINERS lock eyes, it's a challenge to battle. If you don't want to battle, stay out of their
  sight." (:1007)

### 1.4 Petalburg Woods
- Sign at (14,32), near the south entrances (`PetalburgWoods_Text_TrainerTipsExperience`, `PetalburgWoods/scripts.inc:437`):
  "Any POKéMON that appears even once in a battle is awarded EXP Points. To raise a weak POKéMON, put it at the left
  of the team list. As soon as a battle starts, switch it out…" This is the game itself teaching the
  **switch-training** trick a person uses to raise a catch for Roxanne.
- Boy at (15,19): "If your POKéMON are weak and you want to avoid battles, you should stay out of tall grass." (:410)
- Boy at (30,34): "Sometimes, there are things on the ground even if you can't see them. That's why I always check
  where I'm walking." (:417) This is the person-fair hint that **hidden items exist**.
- **The DEVON researcher scene.** Coord triggers at (26,23) and (27,23) on `VAR_PETALBURG_WOODS_STATE == 0`
  (`map.json`); the scripts are `PetalburgWoods_EventScript_DevonResearcherLeft/Right` (:4-58).
  - Lines, in order (:299-358): "Hmmm… Not a one to be found…" → "Hello, have you seen any POKéMON called SHROOMISH
    around here? I really love that POKéMON." → (grunt) "I was going to ambush you, but you had to dawdle in PETALBURG
    WOODS forever…" → "You! DEVON RESEARCHER! Hand over those papers!" → "Aiyeeeh! You're a POKéMON TRAINER, aren't
    you? You've got to help me, please!" → "No one who crosses TEAM AQUA gets any mercy, not even a kid! Come on and
    battle me!"
  - Then a forced `trainerbattle_no_intro TRAINER_GRUNT_PETALBURG_WOODS` (:23 and :51): one Poochyena at L9
    (`trainer_parties.h:103`).
  - After the battle the grunt says "…we of TEAM AQUA are also after something in RUSTBORO. I'll let you go today!"
    (:333-341). The researcher says "…I'll give you a GREAT BALL as my thanks!" (:343), gives it with `giveitem
    ITEM_GREAT_BALL` (:73), then adds "Didn't that TEAM AQUA thug say they were after something in RUSTBORO, too?"
    (:351).
  - The end state is `VAR_PETALBURG_WOODS_STATE` = 1 (:92). **No flag records the Great Ball.**
- Sign at (11,8), near the north exit (:447): "…If a POKéMON runs out of PP, it must be taken to a POKéMON CENTER."
- ⚠ **The MIRACLE SEED girl at (33,5)** says "Oh, neat! That's the BADGE from RUSTBORO GYM! You must be a TRAINER.
  You should try using this item." (:423). Her script has **no badge check** (:229-238), but her line assumes one.
  The woods have Cut trees at (19,10) and (19,11) (`map.json`). It is UNVERIFIED, but likely by design, that she sits
  behind them, which would make the seed a post-badge item. The routing angle should check this.

### 1.5 Route 104, north (the flower shop, the bridge, Rustboro's doorstep)
- Sign at (17,23): TRAINER TIPS on DOUBLE BATTLES, "pairs of TRAINERS who challenge others for 2-on-2 POKéMON
  battles…" (`Route104/scripts.inc:1056`). This warns the player about the twins GINA & MIA (a double battle,
  `trainers.h:5800`).
- Sign at (7,20): `PRETTY PETAL FLOWER SHOP` (:1053).
- Boy at (5,26): "I like filling my mouth with seeds, then spitting them out fast! You can have this, so you try it
  out!" He gives `ITEM_TM_BULLET_SEED` (TM09) and sets `FLAG_RECEIVED_TM_BULLET_SEED` (:317-325). His follow-up line:
  "A TM … is good only for one-time use … Think twice before using it!" (:1021).
- Expert F at (37,8): "If you see BERRIES growing in loamy soil, feel free to take them. But make sure you plant a
  BERRY in the same spot…" She gives `ITEM_CHESTO_BERRY` and sets `FLAG_RECEIVED_CHESTO_BERRY_ROUTE_104`
  (`Route104/scripts.inc:248-256`; text in `data/text/berries.inc:6`).
- **Sign at (23,5): `ROUTE 1O4 {UP_ARROW} RUSTBORO CITY`** (`Route104/scripts.inc:1049`). This is the strongest
  person-fair pointer between the woods and the city. `milestones.json` does not cite it today (its `ch3_rustboro`
  hint is the grunt/researcher line); it may be worth adding as a second hint source.
- Inside the flower shop (texts in `data/text/berries.inc`):
  - The owner gives a berry lesson ("This is the PRETTY PETAL flower shop…", :137).
  - A girl gives the **WAILMER PAIL** ("…You can have this.", :171; `FLAG_RECEIVED_WAILMER_PAIL`).
  - A little girl gives **one random berry per day** (:188; `FLAG_DAILY_FLOWER_SHOP_RECEIVED_BERRY`, `flags.h:1589`).
- The WHITE HERB florist is hidden until `FLAG_BADGE03_GET` (`Route104/scripts.inc:21-29`), so she is OUT of the
  window.

### 1.6 Rustboro City (all VERIFIED, `RustboroCity/scripts.inc` unless noted)
- **Signs:**
  - City sign: `RUSTBORO CITY "The city probing the integration of nature and science."` (:1145)
  - **Gym sign:** `RUSTBORO CITY POKéMON GYM LEADER: ROXANNE "The ROCK-loving honors student!"` (:1135). This is the
    first ON-SCREEN statement of Roxanne's type.
  - School sign: `POKéMON TRAINER'S SCHOOL "We'll teach you anything about POKéMON!"` (:1150)
  - `DEVON CORPORATION` (:1130) and `CUTTER'S HOUSE` (:1155).
  - Tunnel sign (30,8): "Timesaving tunnel nearing completion! …there's also a big X splashed across it in red
    paint…" (:1123)
- **The type hint from an NPC:** a woman at (22,34) says "I challenged the GYM LEADER, but… It's not going to be easy
  winning with my FIRE-type POKéMON… FIRE-type POKéMON don't match up well against ROCK-type POKéMON…" (:946)
- Man at (26,23): "Have you taken the POKéMON GYM challenge? When you get that shiny GYM BADGE in hand…" (:928)
- Man at (19,27): "A POKéMON you get in a trade from someone grows fast. But if you don't have certain GYM BADGES,
  it may not obey you…" (:986)
- Mart (`RustboroCity_Mart/scripts.inc:67`): "I'm buying some PARLYZ HEALS and ANTIDOTES. Just in case I run into
  SHROOMISH in PETALBURG WOODS." This is a person-fair hint about WHERE Shroomish lives. The researcher's line in
  §1.4 is the other one.
- **The Trainer's School** (`RustboroCity_PokemonSchool/scripts.inc`):
  - The teacher gives the **QUICK CLAW** with no condition (:77-90): "Students who don't study get a little taste of
    my QUICK CLAW…" (:242).
  - The blackboard lists the status conditions and their cures (:198-240).
  - A kid says "I always wanted a SEEDOT, and I'm finally getting one!" (:262).
  - **SCOTT** (visible from New Game until Devon Corp 3F hides him, at `RustboroCity_DevonCorp_3F/scripts.inc:55`) says
    the CUT line quoted in §0.3.
  - There are no trainer battles in the school (map.json: no object has a NORMAL trainer type).
- **The Cutter** gives HM01 with no gate (§0.3).
- **Flat 2, 2F:** "My daddy made this! But I can't use it, so you can have it." He gives a PREMIER BALL and sets
  `FLAG_RECEIVED_PREMIER_BALL_RUSTBORO` (`RustboroCity_Flat2_2F/scripts.inc:8-16, 28`).
- **House 1:** a trade, the player's RALTS for the trader's SEEDOT "DOTS", which holds a Chesto Berry
  (`RustboroCity_House1/scripts.inc:4-27`; `src/data/trade.h:987-1001`).
- **Devon Corp 1F:** the stairs are guarded ("only authorized people are allowed to enter here") until
  `FLAG_RETURNED_DEVON_GOODS` (`RustboroCity_DevonCorp_1F/scripts.inc:4-9, 108`).
- **The Mart before `FLAG_MET_DEVON_EMPLOYEE`** (that flag is set post-badge on Route 116) sells Poké Ball, Potion,
  Super Potion, Antidote, Parlyz Heal, Escape Rope, Repel and X items, and **no Great Ball**
  (`RustboroCity_Mart/scripts.inc:9-29`).

### 1.7 Route 116 and the tunnel mouth (optional in this window)
- Signs:
  - `ROUTE 116 {LEFT_ARROW} RUSTBORO CITY` (`Route116/scripts.inc:438`).
  - `RUSTURF TUNNEL "Linking RUSTBORO and VERDANTURF" "The tunnel project has been canceled."` (:442).
  - `TUNNELER'S REST HOUSE` (:448).
  - Two TRAINER TIPS signs: "press the B Button … evolution cancel" (:451) and "Your BAG has several POCKETS" (:459).
- Wanda's boyfriend: "Nnn… Roar! I want to dig that tunnel!" (:355; he is visible, because his hide flag is not set
  at New Game).
- The Glasses Man (§0.2): "I dropped my glasses… Can you help me find them?" (:413).
- Out of window: Mr. Briney (`new_game.inc:201`) and the Devon employee (`new_game.inc:243`) are hidden at New Game.

### 1.8 The Rustboro Gym (`RustboroCity_Gym/scripts.inc`)
- **Gym Guide** (:106-126): "…ROXANNE, the GYM LEADER, is a user of ROCK-type POKéMON. The ROCK type is very durable,
  but it can't stand WATER-type and GRASS-type moves. Come see me afterwards, if you beat the GYM LEADER."
- **Trainer lines that warn:**
  - Josh: "You haven't seen anything of the ROCK type's terrifying power!" (:147)
  - Tommy: "If you can't beat me, you won't stand a chance against ROXANNE!" / "ROXANNE is stronger than me by
    several times. You'd better be on your guard!" (:151, :158)
  - Marc: "…It took smarts and sense for her to pick the ROCK type at her young age." (:173)
- **ROXANNE** (:178): "Hello, I am ROXANNE, the RUSTBORO POKéMON GYM LEADER. I became a GYM LEADER so that I might
  apply what I learned at the POKéMON TRAINER'S SCHOOL in battle. Would you kindly demonstrate how you battle, and
  with which POKéMON?"
- **On defeat** (:13-34):
  - Text: "…Please accept the official POKéMON LEAGUE STONE BADGE." The badge text says it "heightens the ATTACK
    power" and "enables them to use the HM move CUT outside of battle" (:203).
  - Flags and vars, in this order: `FLAG_DEFEATED_RUSTBORO_GYM`, `FLAG_BADGE01_GET`, `VAR_RUSTBORO_CITY_STATE` = 1,
    `VAR_PETALBURG_GYM_STATE` += 1.
  - Then `giveitem ITEM_TM_ROCK_TOMB` and `FLAG_RECEIVED_TM_ROCK_TOMB`. ⚠ **If the bag is full, TM39 is NOT given**
    (:30, `Common_EventScript_ShowBagIsFull`). The next talk to Roxanne retries it (:8).
- Roxanne afterwards (:220): "…you should challenge other GYM LEADERS."

## 2. The opponents in the window (VERIFIED: `trainers.h` and `trainer_parties.h` via `opponents.h`)

| where | trainer (constant, class) | party | trainers.h / trainer_parties.h |
|---|---|---|---|
| Petalburg Woods (scripted) | `TRAINER_GRUNT_PETALBURG_WOODS` (Team Aqua) | Poochyena 9 | :124 / :103 |
| Woods (7,32) | `TRAINER_LYLE` (Bug Catcher) | Wurmple 3 ×4 | :7396 / :8163 |
| Woods (4,14) | `TRAINER_JAMES_1` (Bug Catcher) | Nincada 6 ×2 | :7456 / :8233 |
| R104 south (11,44) | `TRAINER_CINDY_1` (Lady) | Zigzagoon 7 | :1372 / :1451 |
| R104 south (18,67) | `TRAINER_BILLY` (Youngster) | Zigzagoon 5, Seedot 7 | :3832 / :4214 |
| R104 south (15,59) | `TRAINER_DARIAN` (Fisherman) | Magikarp 9 | :8356 / :9436 |
| R104 north (31,24) | `TRAINER_HALEY_1` (Lass) | Lotad 6, Shroomish 6 | :7252 / :8007 |
| R104 north (21,25) | `TRAINER_WINSTON_1` (Rich Boy) | Zigzagoon 7 | :1636 / :1709 |
| R104 north (27-28,15) | `TRAINER_GINA_AND_MIA_1` (Twins, DOUBLE) | Seedot 6, Lotad 6 | :5800 / :6269 |
| R104 north (29,8) | `TRAINER_IVAN` (Fisherman) | Magikarp 5, 6, 7 | :4048 / :4477 |
| Gym (5,13) | `TRAINER_JOSH` (Youngster, id 320) | Geodude 10 | :3844 / :4227 |
| Gym (3,9) | `TRAINER_TOMMY` (Youngster, id 321) | Geodude 8 ×2 | :3856 / :4236 |
| Gym (1,6) | `TRAINER_MARC` (Hiker, id 571) | Geodude 8 ×2 | :6856 / :7649 |
| **Gym** | **`TRAINER_ROXANNE_1` (id 265)** | **Geodude 12 (Tackle, Defense Curl, Rock Throw, Rock Tomb) ×2; Nosepass 15 (Block, Harden, Tackle, Rock Tomb) holding an ORAN BERRY** | :3184 / :3367-3387 |
| R116 (optional) | `TRAINER_JOEY` (Machop 9), `TRAINER_JOSE` (Wurmple 8, Nincada 8), `TRAINER_JERRY_1` (Ralts 9), `TRAINER_CLARK` (Geodude 8), `TRAINER_JANICE` (Marill 9), `TRAINER_KAREN_1` (Shroomish 9), `TRAINER_SARAH` (Lotad 8, Zigzagoon 8), `TRAINER_DAWSON` (Zigzagoon 8, Poochyena 8), `TRAINER_DEVAN` (Geodude 8 ×2), `TRAINER_JOHNSON` (Shroomish 8, Lotad 8) | see the left column | `Route116/scripts.inc:226-343` |

Developer cross-check against `ai_player/knowledge/milestones.json`:
- `ch4_gym_trainers` lists only JOSH and TOMMY. **MARC** (id 571, trainer flag 0x500+571 = 1851, at (1,6)) is not
  there. Check whether that is deliberate (off the path?). Whether he can be avoided is UNVERIFIED.
- The levels and ids of the other milestone fights match the decomp above.
- Which route trainers stand in the way and which can be avoided is UNVERIFIED (that is the routing angle's job).

## 3. What there is to catch (VERIFIED, `src/data/wild_encounters.json`, land slot rates summed)

No fishing in this window: the OLD ROD is given in DewfordTown (`data/maps/DewfordTown/scripts.inc`, `giveitem
ITEM_OLD_ROD`, found by `gh search code`), which is after the badge.

| map (json line) | species, share of encounters, levels |
|---|---|
| Route 104 (:417) | Poochyena 40% L4-5, Wurmple 20% L4, **Marill 20% L4-5**, Taillow 10% L4-5, **Wingull 10% L3-5** |
| Petalburg Woods (:1786) | Poochyena 30% L5-6, Wurmple 25% L5-6, **Shroomish 15% L5-6**, Silcoon 10% L5, Cascoon 10% L5, Taillow 5% L5-6, **Slakoth 5% L5-6** |
| Route 116 (:1320) | Poochyena 28% L6-8, Whismur 20% L6, Nincada 20% L6-7, Taillow 20% L6-8, **Abra 10% L7**, **Skitty 2% L7-8** |
| Rusturf Tunnel (:1855) | Whismur 100% L5-8 |
| Route 102, behind the player (:109) | Poochyena 30%, Wurmple 30%, **Lotad 20%**, Zigzagoon 15%, **Ralts 4%**, **Seedot 1%**, L3-4 |

The in-game lines that point at a species: SHROOMISH (the researcher and the Rustboro Mart woman), SEEDOT (the school
kid and the trade house), RALTS (the trade house asks for one).

## 4. How a typical person plays this stretch, and the matchup

### 4.1 The matchup (VERIFIED)
The type rows are in `src/battle_main.c`: Normal→Rock ½ :337, Fire→Rock ½ :344, Water→Ground ×2 :350, Water→Rock ×2
:351, Grass→Ground ×2 :363, Grass→Rock ×2 :366, Fighting→Rock ×2 :383, Ground→Rock ×2 :398, Flying→Rock ½ :404,
Rock→Fire ×2 :420, Rock→Flying ×2 :424, Rock→Bug ×2 :425. Any pair not listed is ×1.

The species types are in `species_info.h`: Geodude Rock/Ground, Nosepass Rock, Combusken Fire/Fighting. The learnsets
are in `level_up_learnsets.h`.

| starter | first move that is super-effective on Roxanne | Geodude / Nosepass | danger | verdict |
|---|---|---|---|---|
| TREECKO (Grass) | ABSORB at L6 (:3572) | ×4 / ×2 | Rock is neutral on Grass | easy. TM09 BULLET SEED is compatible (`tmhm_learnsets.h:6638`) |
| MUDKIP (Water) | MUD-SLAP at L6 (Ground), then WATER GUN at L10 (:3676) | ×2 then ×4 / ×2 | Rock is neutral on Water | easiest |
| TORCHIC (Fire) | none until COMBUSKEN at L16 learns DOUBLE KICK (Fighting) at L16 (:3638; `evolution.h:127`) | Ember ×½ / ×½; Scratch ×½; Peck (L16) ×½ | **Rock Tomb and Rock Throw are ×2 on Fire** | hard. Needs L16 or a helper |

**Helpers a person catches for Torchic** (all catchable before the gym; VERIFIED learnsets):
- SHROOMISH: Absorb from L1, Stun Spore at L7 (:3987);
- LOTAD: Absorb at L7 (:3846);
- MARILL: Water Gun only at L10 (:2519); the wild ones are L4-5;
- WINGULL: Water Gun from L1 (:4034), but it is Water/Flying, so Rock moves hit it ×2;
- SEEDOT, SHROOMISH or LOTAD taught TM09 BULLET SEED (compatible: `tmhm_learnsets.h:7140, 7325, 7053`).

All three starters can learn TM39 ROCK TOMB (`tmhm_learnsets.h:6638, 6726, 6804`), but it arrives only after the
badge.

Person-fair status: the AI may know the TYPE facts **only because the game says them**: the Gym Guide (WATER and
GRASS), the Rustboro woman (FIRE is bad against ROCK) and the Gym sign ("ROCK-loving"). It must not get them from a
type table it has not seen. If the AI has a battle-learned type memory, that is its own experience.

### 4.2 Typical human play (UNVERIFIED: human-play recall and the Gemini estimate in `2026-10-03-human-reference-NOTE.md` §2; for scale only)
- **Order.** The Scott scene, then Route 104 south. Most people talk to the girl and peek into the empty cottage, and
  some walk the beach. Then the woods: the researcher scene, the grunt fight and the Great Ball. Then Route 104 north:
  the TM09 boy, a look into the flower shop for the Wailmer Pail, and the bridge trainers including the twins'
  double battle. Then Rustboro.
- **In Rustboro, before the gym:** heal at the Pokémon Center, buy Poké Balls and Potions, wander into the Trainer's
  School (Quick Claw, Scott). Many people also pick up HM01 now because Scott mentions it.
- **Catches.** Most people catch 2-5 species by Roxanne, out of a human estimate of 5-10 "seen and caught". The usual
  picks are a Shroomish or Slakoth from the woods, a Wingull, Marill or Taillow on 104, and a Poochyena or Wurmple
  "because it was there". Route 116 (Abra, Skitty, Whismur, Nincada) is often visited for training and catching
  before the gym, because it is right next to Rustboro.
- **Training.** The team is usually L10-16 at Roxanne (Gemini estimate, high confidence). A Torchic player commonly
  grinds to L16 for Combusken, often on Route 116 or Route 104 trainers. Treecko and Mudkip players often fight at
  L12-14 and win. People use the woods sign's switch-training to raise a catch.
- **Healing.** People walk back to the Rustboro Pokémon Center before the gym, and often between the gym trainers
  and Roxanne. Potions and the Oran berries from the Route 104 trees (§5, VERIFIED tree contents) are used mid-fight.
- **What a person usually skips here:** the Rusturf Tunnel interior (dead end, and they are told the project was
  canceled), and the items behind Cut trees, which they come back for later.

### 4.3 Visible item balls and hidden items (VERIFIED placement, from `map.json`; reachability UNVERIFIED for anything marked †)

| map | visible item balls (flag) | hidden items (flag) |
|---|---|---|
| Route 104 | Poké Ball (29,53) `FLAG_ITEM_ROUTE_104_POKE_BALL`; Potion (5,8) `…_POTION`; X Accuracy (37,22)† next to a Cut tree at (35,22) `…_X_ACCURACY`; PP Up (39,15)† `…_PP_UP` | Potion (14,55), Antidote (16,72), Heart Scale (16,64) on the south beach; Poké Ball (3,9) and Super Potion (7,6) north (`FLAG_HIDDEN_ITEM_ROUTE_104_*`) |
| Petalburg Woods | Paralyze Heal (4,26), Ether (4,8), X Attack (35,20)†, Great Ball (45,7)† (`FLAG_ITEM_PETALBURG_WOODS_*`) | Potion (39,35), Tiny Mushroom (26,6)† and (40,29), Poké Ball (4,19) |
| Rustboro City | X Defend (36,51)† `FLAG_ITEM_RUSTBORO_CITY_X_DEFEND` | none |
| Route 116 | Repel (10,17), Potion (34,7), Ether (19,6)† beside a Cut tree at (21,6), X Special (55,12)†, HP Up (80,8)† | Super Potion (22,9)†, **Black Glasses (70,13)†** |
| Rusturf Tunnel | Poké Ball (3,1), Max Ether (30,2)† | none |
| Petalburg City | Max Revive (19,2)†, Ether (3,28)† | Rare Candy (11,29)† |

Berry trees (`new_game.inc:7-18` with the map.json tree ids):
- Route 104 south (22-24,41): Oran, Pecha.
- Route 104 north: Oran (3,23), Cheri (3,25), Cheri (34,6), Leppa (36,6).
- Route 116 (18-21,2): Pinap ×2, Chesto ×2.

## 5. The Gemini enumeration, adjudicated name by name

The call was `py -3.12 tools/story-dev/gemini_relay.py --file <prompt>`, with **no `--model`** (the default Pro).
One call, 2026-10-15. The raw answer was kept in the scratchpad, not in the repo. Legend:
- **CONFIRMED**: the name exists AND the claim about it holds.
- **NAME OK / CLAIM REFUTED**: the name exists but Gemini's description of it is wrong.
- **REFUTED**: wrong.
- **NOT FOUND**: no such symbol.

### 5.1 Flags
| Gemini name | verdict | evidence |
|---|---|---|
| FLAG_HIDE_PETALBURG_CITY_WALLY | CONFIRMED | flags.h:775; set at `PetalburgCity_Gym/scripts.inc:86` |
| FLAG_HIDE_PETALBURG_GYM_WALLY | NAME OK / timing unclear | flags.h:917. Cleared at the START of the tutorial (`PetalburgCity_Gym/scripts.inc:185`); the return scene uses `removeobject` |
| FLAG_HIDE_ROUTE_104_TEAM_AQUA | **NOT FOUND** | not in flags.h, and there is no Aqua object in the Route104 map.json |
| FLAG_HIDE_PETALBURG_WOODS_DEVON_EMPLOYEE / _AQUA_GRUNT | CONFIRMED | flags.h:773-774; map.json objects 3-4 |
| FLAG_MET_DEVON_EMPLOYEE | **NAME OK / CLAIM REFUTED** | flags.h:313. It is set on ROUTE 116 by the Repeat Ball employee AFTER the goods are recovered (`Route116/scripts.inc:55`), not by the woods researcher. The woods record themselves only in `VAR_PETALBURG_WOODS_STATE` (`PetalburgWoods/scripts.inc:92`) |
| FLAG_RECEIVED_GREAT_BALL_PETALBURG_WOODS | **NOT FOUND** | the Great Ball has no flag (`PetalburgWoods/scripts.inc:73`) |
| FLAG_RECEIVED_MIRACLE_SEED | CONFIRMED | flags.h:323; `PetalburgWoods/scripts.inc:236` |
| FLAG_RECEIVED_TM09 | **NOT FOUND** | the real one is `FLAG_RECEIVED_TM_BULLET_SEED` (flags.h:288) |
| FLAG_RECEIVED_WAILMER_PAIL | CONFIRMED | flags.h:112 |
| FLAG_RECEIVED_CHESTO_BERRY_ROUTE_104 | **NAME OK / CLAIM REFUTED** | flags.h:272. Given OUTSIDE by Expert F at (37,8) (`Route104/scripts.inc:248-256`), not in the shop |
| FLAG_RECEIVED_WHITE_HERB | **NAME OK / CLAIM REFUTED** | flags.h:305. The florist is outside on Route 104 and appears only after BADGE03 (`Route104/scripts.inc:21-29`) |
| FLAG_RECEIVED_HM01 | **NOT FOUND** | the real one is `FLAG_RECEIVED_HM_CUT` (flags.h:159) |
| FLAG_RECEIVED_QUICK_CLAW | CONFIRMED | flags.h:301 |
| FLAG_RECEIVED_PREMIER_BALL_RUSTBORO | CONFIRMED | flags.h:235 |
| FLAG_BADGE01_GET | CONFIRMED | flags.h:1359; `RustboroCity_Gym/scripts.inc:19` |
| FLAG_RECEIVED_TM39 | **NOT FOUND** | the real one is `FLAG_RECEIVED_TM_ROCK_TOMB` (flags.h:187) |
| FLAG_ITEM_ROUTE_104_POTION | NAME OK / "south" REFUTED | flags.h:1188; the ball is at (5,8), on the north part |
| FLAG_ITEM_ROUTE_104_POKE_BALL, _X_ACCURACY | CONFIRMED | flags.h:1110, :1168 |
| FLAG_ITEM_PETALBURG_WOODS_PARALYZE_HEAL, _ETHER | CONFIRMED | flags.h:1170, :1111 |
| FLAG_ITEM_ROUTE_116_POTION, _X_SPECIAL, _ETHER, _REPEL | CONFIRMED | flags.h:1199, :1054, :1072, :1073 |
| FLAG_ITEM_RUSTURF_TUNNEL_POKE_BALL | CONFIRMED | flags.h:1101 |
| FLAG_HIDDEN_ITEM_ROUTE_104_POTION, _ANTIDOTE, _HEART_SCALE, _POKE_BALL | CONFIRMED | flags.h:583, :631, :634, :608 |
| FLAG_HIDDEN_ITEM_PETALBURG_WOODS_POTION, _TINY_MUSHROOM_1, _2, _POKE_BALL | CONFIRMED | flags.h:604-607 |
| Black Glasses flag ("name unknown") | resolved | `FLAG_HIDDEN_ITEM_ROUTE_116_BLACK_GLASSES` (flags.h:642) |

**Gemini missed** these flags:
- `FLAG_ITEM_PETALBURG_WOODS_GREAT_BALL`, `…_X_ATTACK`
- `FLAG_HIDDEN_ITEM_ROUTE_104_SUPER_POTION`
- `FLAG_ITEM_ROUTE_104_PP_UP`
- `FLAG_ITEM_ROUTE_116_HP_UP`
- `FLAG_HIDDEN_ITEM_ROUTE_116_SUPER_POTION`
- `FLAG_ITEM_RUSTURF_TUNNEL_MAX_ETHER`
- `FLAG_DEFEATED_RUSTBORO_GYM`
- `FLAG_RUSTBORO_NPC_TRADE_COMPLETED` (flags.h:175)
- `FLAG_MET_SCOTT_RUSTBORO` (flags.h:336)
- `FLAG_DAILY_FLOWER_SHOP_RECEIVED_BERRY`

### 5.2 Vars
| Gemini claim | verdict | evidence |
|---|---|---|
| VAR_PETALBURG_CITY_STATE "2 when Wally returns, 3 after Scott, which allows Route 104" | **NAME OK / CLAIM REFUTED** | vars.h:107. It is set to 2 when the tutorial BEGINS (`PetalburgCity_Gym/scripts.inc:183`) and to 3 when it ends (`PetalburgCity/scripts.inc:47`). Scott writes `VAR_SCOTT_PETALBURG_ENCOUNTER` (vars.h:221) and `VAR_SCOTT_STATE`. No gate on Route 104 was found |
| VAR_PETALBURG_GYM_STATE "advances when the tutorial completes" | CONFIRMED | vars.h:153; set to 2 at `PetalburgCity_Gym/scripts.inc:90`; +1 at the badge (`RustboroCity_Gym/scripts.inc:21`) |
| VAR_RUSTBORO_CITY_STATE "0 in the window; increments after leaving the gym" | **partly REFUTED** | vars.h:110. Set to 1 INSIDE the gym, at the badge (`RustboroCity_Gym/scripts.inc:20`). The theft scene is a coord trigger on value 1 outside (Rustboro map.json, (23,20..24)) |
| (missed) VAR_PETALBURG_WOODS_STATE | n/a | vars.h:172. This is the woods' only record |

### 5.3 Items
- **CONFIRMED:**
  - ITEM_TM09 (`include/constants/items.h:325`; the enum, which the scripts spell with the alias `ITEM_TM_BULLET_SEED`)
  - ITEM_HM01 (:367)
  - ITEM_TM39 (:355)
  - Wailmer Pail (shop girl)
  - Great Ball (the researcher)
  - Miracle Seed (the woods girl)
  - Quick Claw (the teacher)
  - Premier Ball (Flat2_2F)
  - HM01 (the Cutter)
  - TM39 (Roxanne)
  - all four Route 116 balls
  - the Rusturf Poké Ball
  - the Route 104 and woods hidden items
  - the Oran and Pecha trees south, the Cheri tree north
- **REFUTED:**
  - "Chesto Berry from a girl INSIDE the flower shop": it is Expert F outside. The shop girl gives a RANDOM daily berry.
  - "White Herb inside the flower shop": it is the outside florist, after badge 3.
- **UNVERIFIED:** "Black Glasses … normally requiring Verdanturf access" (the routing angle).
- **Missed:** the Leppa tree, PP Up, X Attack, the woods Great Ball ball, HP Up, Max Ether, the X Defend in Rustboro.

### 5.4 Trainers (the `opponents.h` names, then the `trainer_parties.h` parties)
- **CONFIRMED (name and party):**
  - CINDY_1 (Zigzagoon 7)
  - IVAN (Magikarp 5, 6, 7)
  - GINA_AND_MIA_1 (Seedot 6, Lotad 6, double)
  - GRUNT_PETALBURG_WOODS (Poochyena 9)
  - ROXANNE_1 (12, 12, 15)
  - JANICE (Marill 9)
  - JOSE (Wurmple 8, Nincada 8)
  - KAREN_1 (Shroomish 9)
- **Name OK, detail REFUTED:**

  | trainer | Gemini said | the decomp has |
  |---|---|---|
  | WINSTON_1 | "Youngster" | Rich Boy |
  | HALEY_1 | L7/L7 | L6/L6 |
  | LYLE | L6 ×4 | Wurmple 3 ×4 |
  | JAMES_1 | Nincada 8 | Nincada 6 ×2 |
  | JOSH | Geodude 10 ×3 | one Geodude 10 |
  | TOMMY | Geodude 11 | Geodude 8 ×2 |
  | MARC | Geodude 11 | Geodude 8 ×2 |
  | CLARK | Geodude 8 ×3 | one Geodude 8 |
  | JOHNSON | School Kid, Shroomish 9 | Youngster, Shroomish 8 + Lotad 8 |
  | DAWSON | School Kid, Whismur 9 | Rich Boy, Zigzagoon 8 + Poochyena 8 |
  | DEVAN | Geodude 9 | Geodude 8 ×2 |

- **NOT FOUND:** `TRAINER_JOEY_1`. The real one is `TRAINER_JOEY` (`opponents.h:326`, Machop 9, which is what Gemini
  had).
- **Missed:** BILLY and DARIAN (Route 104 south), JERRY_1 and SARAH (Route 116).

⇒ **Its gym-trainer parties were wrong in all three cases.** Never take a party, level or class from Gemini.

### 5.5 Labels, events and dialogue
| Gemini label | verdict | the real one |
|---|---|---|
| PetalburgCity_Gym_EventScript_Norman | NAME OK / the scene described belongs elsewhere | the post-tutorial speech is `…_EventScript_ReturnFromWallyTutorial` (:76); `…_Norman` (:101) is the talk-again switch |
| PetalburgCity_EventScript_Scott | CONFIRMED | `PetalburgCity/scripts.inc:518` |
| PetalburgWoods_EventScript_DevonResearcher | **NOT FOUND** | `…_DevonResearcherLeft` / `…Right` (:4, :32) |
| RustboroCity_Gym_EventScript_Roxanne | CONFIRMED | :4 |
| PetalburgCity_Gym_Text_NormanGoToRustboro | NAME OK / **quote REFUTED** | Gemini's "I'm going to RUSTBORO CITY... Wait, no..." is invented. The real text is in §1.1 |
| PetalburgWoods_Text_PleaseSaveMe | **NOT FOUND** | `PetalburgWoods_Text_YouHaveToHelpMe` (:318) |
| RustboroCity_Gym_Text_GymGuideAdvice | CONFIRMED (paraphrase) | :106. Gemini dropped the "WATER-type and GRASS-type" clause, which is the useful part |
| RustboroCity_Gym_Text_RoxannePreBattle | **NOT FOUND** (quote CONFIRMED near-verbatim) | `RustboroCity_Gym_Text_RoxanneIntro` (:178) |

- Events: the Scott scene, the woods scene and the Roxanne sequence are CONFIRMED in substance.
- Gemini MISSED:
  - Scott's CUT hint in the school;
  - the Rustboro woman's FIRE-vs-ROCK line;
  - the two route signs;
  - the trade house;
  - the empty cottage.

### 5.6 Wild Pokémon
- Species sets: CONFIRMED for all four maps.
- Levels are slightly off:
  - Route 104: Wurmple is L4 only, and Wingull is L3-5.
  - Route 116: Whismur is L6 only, Nincada L6-7, Abra L7.
- "Old Rod not obtainable in the window": CONFIRMED (DewfordTown).

## 6. What this means for chapters 3-4 (developer suggestions, not decisions)
1. The person-fair hint chain is: DAD (Rustboro, Roxanne) → `ROUTE 104 ↑ RUSTBORO CITY` sign → the grunt's
   "RUSTBORO" → the Gym sign "ROCK-loving" → the Gym Guide "WATER-type and GRASS-type". All are quoted in §1.
   - DAD's talk-again line (§1.1) is a natural place to REFRESH a forgotten goal.
2. Expect two forced scenes the AI does not choose: SCOTT at the west exit (§1.2) and the woods ambush (§1.4,
   unavoidable battle). A pre-registered proof should assert `VAR_SCOTT_PETALBURG_ENCOUNTER` = 1 and
   `VAR_PETALBURG_WOODS_STATE` = 1 (identity: these exact vars), not a battle count.
3. RULING 33 gifts in this window:
   - **Quick Claw**: yes, with no gate.
   - **Black Glasses**: placement verified, pre-badge reachability open.
   - **Amulet Coin**: no, it is a badge-5 Mom gift.
   - Also free here, if a personality explores: TM09, Wailmer Pail, a daily berry, Chesto, Premier Ball, Great Ball,
     HM01, and the Miracle Seed (probably post-badge, see §1.4).
4. Torchic runs need either L16 (Double Kick) or a Grass/Water catch. The game's own hints justify a catch: the
   Shroomish lines, the Gym Guide and the Rustboro woman. Training to "the leader's level" means Nosepass 15 (§2).
5. `ch4_gym_trainers` omits MARC. Confirm whether that is intended.
6. Full bag means no TM39 (§1.8). The bag is unlikely to be full this early, but a proof that asserts TM39 should check
   `FLAG_RECEIVED_TM_ROCK_TOMB`, not assume it.

*Sources were fetched to the session scratchpad, `ch34_02/decomp/`, and are not committed. The verifier script is
`ch34_02/verify.py` in the same scratchpad.*
