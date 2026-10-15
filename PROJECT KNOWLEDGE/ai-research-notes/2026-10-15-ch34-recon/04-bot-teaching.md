# 2026-10-15 — ch3/ch4 recon, angle 04: what the STORY BOT learned on Route 104, Petalburg Woods, Rustboro and ROXANNE

> ⚠ **AI RESEARCH NOTE, NOT A SOURCE OF TRUTH.** One read-only Claude agent wrote this. Nothing was driven and no
> emulator was started. Every claim is tagged:
> - **VERIFIED** means I read it in the decomp (pret/pokeemerald via `gh api`) or in our own code, docs or logs, and the
>   citation is given.
> - **UNVERIFIED** means it is inferred or quoted from a note.
>
> On any conflict, the authoritative docs (`05`, `08`, `12`) win.
>
> ⛔ **TEACHING MATERIAL ONLY (USER RULING 35).** This describes what the bot met and why. It is never code for the AI
> player to copy.
>
> ⛔ **PERSON-FAIR (RULINGS 35-37).** Every coordinate, flag, var and trainer roster here is for the DEVELOPERS, to design
> proofs and expectations. None of it may be fed to the AI as a hint. The only hints a person gets on these maps are the
> lines in §5a: the dialogue and signs.

## 0. THE SHORT VERSION

1. **Route 104 is two places.** Petalburg Woods splits it, and the ROM's connection graph does not show the split. The
   bot lost hours there, and later lost 319 runs to a picker that forgot it (§2).
2. **Two scenes end after their completion marker.**
   - Scott sets `VAR_SCOTT_STATE` *before* he speaks.
   - ROXANNE sets `BADGE01_GET` *before* TM39 and its explanation.
   - A "done" check fires mid-scene in both (§3).
3. **Level 16 lands inside the gym.** All three starters evolve at 16, and two of them learn a move mid-battle there.
   - The bot hung on the move-learn prompt (ML-10/ML-13).
   - Holding B cancels an evolution. For Torchic that means Peck instead of Double Kick, its only good move against
     ROXANNE (§4).
4. **Levels the bot found sufficient (§1, measured across 1,769 unique badge-1 team snapshots):**
   - The starter line wins at about **L16-17**, evolved: Marshtomp 16, Combusken 17, Grovyle 17.
   - The rest of the team sits at about **L7-8**. In practice the bot beats ROXANNE with its starter alone.
5. **The bot never collected anything here.**
   - Gifts: Quick Claw and Chesto Berry; the Miracle Seed probably comes later (the White Herb is post-badge-3).
   - Item balls, hidden items, and the Woods' Shroomish.
   - It cannot teach RULING 33's errands on these maps (§6).
6. **Our own knowledge has a hole.** The gym has **three** trainers. The bot's docs say "two Youngsters", and
   `milestones.json` `ch4_gym_trainers` lists only JOSH and TOMMY. The Hiker MARC is missing (§3).

## 1. ROXANNE: the levels the bot found sufficient, per starter (VERIFIED, my count)

**Source.** Every `badge-log.json` under `sandbox-pokebot/profiles/*/` and `custom-pokebot/profiles/*/` (129 files).
Each holds the party snapshot taken when `BADGE01_GET` turned on (`modules/badge_log.py`).

**Method.**
- Deduplicated by (species, level, IVs) of the whole party, which leaves 1,780 unique snapshots.
- Dropped 11 with any member at L30 or higher (fixture or post-game re-earns), which leaves 1,769.
- Script: scratchpad `badge1_levels.py` (read-only).

⚠ These levels are taken **after** the gym, so they include the EXP from the gym's trainers and ROXANNE. The level going
in was about 1-2 lower. The bot's prep targets the band `(13, 17)`, "user: team between Lv 13-17 before Roxanne"
(`story_mode.py:5022`). Its sufficiency gate trains only the sweeper (07-CHANGELOG 2026-07-23).

| starter | n | starter-line level at the badge (p10 / median / p90, range) | form | starter fainted yet won | HP p10 after the win | 2nd-best party member (median / p90) |
|---|---|---|---|---|---|---|
| Mudkip | 629 | 16 / 16 / 17 (15-18) | Marshtomp 618, Mudkip 11 | 10 | 36% | L7 / L10 |
| Torchic | 460 | 17 / 17 / 18 (17-20) | Combusken 460 (all) | **0** | 69% | L8 / L10 |
| Treecko | 680 | 16 / 17 / 18 (14-21) | Grovyle 661, Treecko 19 | 15 | 47% | L8 / L16 |

**Movesets at the badge (VERIFIED, same data):**
- Marshtomp: Water Gun, Mud-Slap, Mud Shot, Tackle.
- Combusken: Scratch, Peck, **Double Kick**, Ember. Double Kick appears in 460 of 460.
- Grovyle: Quick Attack, Absorb, Pursuit and/or Fury Cutter, Pound.

**Reading (UNVERIFIED inference):**
- Every Torchic win came as a Combusken with Double Kick. The old belief that "Torchic is the hard starter for Roxanne"
  holds only for an **unevolved** Torchic.
- Treecko's line spreads widest, and its starter fainted most often. Absorb is its only super-effective move, and
  Fury Cutter is Bug, which is resisted by Rock.
- A lone L16 Treecko did lose once (`28-HANDOFF-ARCHIVE.md:2725`).

**Context:**
- **Reach.** Gym 1 was reached in 91% and 93% of runs, before and after the Wally fix (`07-CHANGELOG.md:28374`).
- **First-attempt win.** About .89 and .94 in two baseline batches (`ai-research-notes/2026-10-01-batch14-recon/b14_recon_stats.md:35`).
  That figure is itself an agent note with INFERRED classification.

**Leader data (VERIFIED, decomp):** ROXANNE_1 has Geodude L12 ×2 and Nosepass L15 holding an **Oran Berry**.
- Geodude moves: Tackle, Defense Curl, Rock Throw, **Rock Tomb**.
- Nosepass moves: Block, Harden, Tackle, Rock Tomb.
- Source: `src/data/trainer_parties.h:3367` (`sParty_Roxanne1`).

**Learnsets that matter (VERIFIED, `src/data/pokemon/level_up_learnsets.h`):**
- Mudkip: Water Gun at L10 (`:3676`). Marshtomp: Mud Shot at L16 (`:3692`).
- Torchic: Ember at L10, and **Peck** at L16 if it does not evolve (`:3623`). Combusken: **Double Kick** at L16 (`:3638`).
- Treecko: Absorb at L6 and Pursuit at L16 (`:3572`). Grovyle: Fury Cutter at L16 and Pursuit at L17 (`:3587`).

**What a learner should take from this (principle, not code):**
- A Water, Grass or Fighting move on an evolved starter at about the leader's ace level (15), plus a heal before the
  door, wins about nine times in ten for this bot.
- The bot's team of four is not a team in battle. Its bench averages L7-8. RULING 33 asks for something better: a
  team trained toward the leader's level, with type advantages.

## 2. TRAPS ON THE WAY, in story order

### 2a. Petalburg's west exit: the Scott scene
- **What happened.** Walking to Petalburg's only west exit (row y=12/13) fires a one-time cutscene,
  `PetalburgCity_EventScript_Scott`, at (4,12).
  - It runs while the game state stays OVERWORLD.
  - The bot's "press B only when not in the overworld" ride-out never advanced it, and the navigator aborted on it.
  - Sources: `08-MISTAKES.md:175-189`; `early_game.py:1616-1651` (the docstring and a hand-walk loop that advances on
    `script_context.is_active`). VERIFIED.
- **Decomp.** The var is set before the dialogue (VERIFIED, `data/maps/PetalburgCity/scripts.inc:518-543`):
  - `setvar VAR_SCOTT_STATE, 1` comes at `:525`, *before* three msgboxes and his walk-off.
  - `VAR_SCOTT_PETALBURG_ENCOUNTER` and `removeobject` come only at `:540-541`.
- **Teaches.** "A text box is up" must be judged from the screen, never from the game state. A scene's var can flip at
  its start.

### 2b. Route 104 is split by the Woods (ML-7)
- **What happened.** `navigate_to_anywhere` from Petalburg to Rustboro always failed. Hours of coordinate guessing
  failed too.
  - Route 104 is one map ID whose south (beach) half and north half join only by walking through Petalburg Woods by
    warp.
  - The connection graph shows Petalburg→Route104→Rustboro as edge-connected.
  - Sources: `08-MISTAKES.md:135-154`; `12-STORYMODE-DESIGN.md:2516-2535`. VERIFIED.
- **It recurred twice later:**
  - From Petalburg, Route 104 reads 31/200 tiles reachable, Woods 0/132, Rustboro 0/150 (`08-MISTAKES.md:2878-2917`).
  - A training-ground picker blind to position sent the bot from Route 104 north to grounds on the south side, killing
    319 runs (`training_areas.py:281-288`; `08-MISTAKES.md:16700-16726`).
- **Decomp (VERIFIED, `data/maps/Route104/map.json` `warp_events`):** there are three pairs of Woods doors.
  - (10-11,30) leads to the Woods' north exit (14-15,5).
  - (10-11,38) leads to the Woods' south door (16-17,38). The bot uses this one.
  - (32-33,42) leads to the Woods' second south door (36-37,38).
  - `data/maps/PetalburgWoods/map.json` `warp_events` confirm the other ends.
  - Route 104 connects up to Rustboro and right to Petalburg (offset 50) (`connections`).
- **Teaches.** "I can see the town on the map" does not mean "I can walk there". A person learns the way through the
  Woods by trying. The AI's world memory must not assume map edges connect halves.

### 2c. Route 104 south: a trainer battle with a one-mon party (ML-8)
- **What happened.** At this point the party is a single Pokémon.
  - The lead dropped below the flee threshold in a trainer battle, and the strategy tried to run, which raises.
  - The fix: never flee a trainer, fight on, and heal at Petalburg before leaving.
  - Source: `08-MISTAKES.md:156-173`. VERIFIED.
- **Who (UNVERIFIED which one the bot met).** The trainer nearest the bot's door is CINDY at (11,44), sight 3, Zigzagoon
  L7 holding a Nugget.
  - Sources: `Route104/map.json` obj 25; `trainer_parties.h:1451`. VERIFIED that she is there.
  - The bot's docstring says only "a Route 104 trainer's sight line catches us" (`early_game.py:1621-1623`).
- **Teaches.** A trainer battle can't be fled, so heal before a stretch with trainers while the team is tiny.

### 2d. Doors that do not fire (ML-9) and the harness that hid it
- **What happened.** The bot stood on the Woods door and the warp did not trigger, leaving it "stuck" in the real bot.
  - Single-frame presses do not finish a tile step, and map reads flicker during the fade.
  - The test harness read extra state every frame. That shifted the timing and hid the bug.
  - Fix: make the door tile a navigation target and step through it fully (`_pass_through_door`).
  - Source: `08-MISTAKES.md:190-216`. VERIFIED.
- **Teaches.** A door is entered by a completed step into it, from the right side.

### 2e. Petalburg Woods: the grunt scene
- **Trigger (VERIFIED, `PetalburgWoods/map.json` `coord_events`).** Two triggers at (26,23) and (27,23), each gated on
  `VAR_PETALBURG_WOODS_STATE == 0`, run `…DevonResearcherLeft` or `…Right`.
- **Scene (VERIFIED, `PetalburgWoods/scripts.inc:4-94`):**
  1. The researcher looks for SHROOMISH.
  2. The grunt enters, the researcher flees behind the player, and a `trainerbattle_no_intro TRAINER_GRUNT_PETALBURG_WOODS`
     follows (`:23`/`:51`). The grunt has Poochyena L9 (`trainer_parties.h:103`).
  3. The grunt runs off, and `giveitem ITEM_GREAT_BALL` follows. A full bag gives a "You're loaded with items" line and
     no ball (`:73-81`).
  4. "TEAM AQUA … after something in RUSTBORO" (`:84`). The researcher walks out.
  5. **Only then** come `setvar VAR_PETALBURG_WOODS_STATE, 1` and `releaseall` (`:91-93`). Here the var is a safe
     completion marker, because it is the last command.
- **What happened to the bot.**
  - It rides the scene out by catching the navigator's abort, then pressing B and retrying, bounded at 15 rounds
    (`early_game.py:1679-1729`).
  - Its docs call the scene MANDATORY (`12-STORYMODE-DESIGN.md:2560-2565`).
  - ⚠ **UNVERIFIED whether it is unavoidable.** The decomp gives only two trigger tiles, and I did not read the
    layout's passability. If a path to the north exit (14-15,5) bypasses (26-27,23), then the AI can leave the Woods
    with the var still 0. Both `ch3_route104` and `ch3_woods` in `milestones.json` use exactly that var
    (`PETALBURG_WOODS_STATE ≥ 1`), so neither would ever complete.
  - Developers should check this on the layout, or with `calculate_path` and a control, before building expectations.
- **A later Woods trap (VERIFIED).** A hard-coded destination (26,5) inside the Woods was a solid tree. 67 of 67 legs
  derailed (`08-MISTAKES.md:22350-22359`; graded in `2026-09-26-woods-GRADED.md`).
- **Teaches.**
  - A scene that interrupts walking is the story, not an obstacle. Ride it out and resume the goal.
  - Never aim at a tile you have not seen to be walkable.

### 2f. Route 104 north: the post-battle oscillation (archived KI-15)
- **What happened.** After a trainer battle, the navigator bounced between (5,6) and (5,7) forever. Two of three
  confirmed 20k-frame hangs were here (`31-KNOWN-ISSUES-ARCHIVE.md:928-987`).
- **Fixes.**
  - A no-progress bail in `navigate_to`.
  - A single A press when the player is frozen in place for 240 frames, to clear a post-battle wedge (`cb=ReturnFromBattle`).
  - An earlier every-frame A "nudge" re-opened the Rustboro nurse's dialogue in a loop (`08-MISTAKES.md:981-1000`).
- **Teaches.** Detect when you are not getting closer. Never mash A next to a person.

### 2g. Rustboro: a resume edge
- **What happened.** Segment 3's "past the Woods?" check looked only at RUSTBORO_CITY.
  - A save on Route 116, the pre-gym grass reachable only through Rustboro, re-ran the Woods travel and derailed.
  - The fix counts the whole Rustboro area: the city, map group 11, Route 116 and Rusturf.
  - Sources: `07-CHANGELOG.md:1301-1308`; `story_mode.py:4984-5011`. VERIFIED.
- **Teaches.** Decide where you are in the story from what has happened, not from the map you stand on.

### 2h. Pre-gym catching and training on Route 116 (prep for ch4)
- **Local grass is too weak to train for ROXANNE (VERIFIED).**
  - Bot tables: Route 104 wilds L4-6, Woods L5-6 (`training_areas.py:205-206`).
  - So the bot trains on Route 116 (11,7), the "R116 L8 vs ~L17" case (`early_game.py:2105-2107`; `story_mode.py:2193-2200`).
- **Catch battles were the killers (UNVERIFIED agent note).** In a large corpus, 16 of 19 lost catch battles were
  Whismur using Uproar while the bot kept throwing (`2026-09-27-pregym1-cap-RECON.md`).
- **Ball supply.** 18 of 38 runs ran out of balls before gym 1, and the bot buys only in Rustboro. Same note,
  UNVERIFIED.
- **Teaches.**
  - Picking up the free balls on the way would ease the ball shortage (see §6).
  - Run from a catch that is going badly.

### 2i. The gym
- **Hang 1: the switch into a weak bench (KI-8, still open as a framework issue).**
  - ROXANNE vs a Torchic with an L6-7 bench hung on the in-battle party menu while switching into the weak bench.
  - The bot now attacks through trainer battles and never rotates proactively.
  - Sources: `05-KNOWN-ISSUES.md:120-140`; `08-MISTAKES.md:480-490`. VERIFIED.
- **Hang 2: a level-16 move-learn mid-fight (ML-10/ML-13).**
  - The starter reached L16 before Nosepass came out, and the "Delete a move?" prompt froze the handler.
  - It was fixed from on-screen text, and evolution is always allowed (`08-MISTAKES.md:218-243, 345-359`). VERIFIED.
- **"Lead strongest" was not enough.**
  - The bot leads its highest level and heals at the Rustboro PC first (`early_game.py:2051-2102`).
  - A later rival fight showed the level heuristic fails against a type counter (`08-MISTAKES.md:423-431`).
- **Teaches.** Read the prompt on screen: learn a move, or keep the old ones. Lead with the type that wins, not just the
  highest level.

## 3. DECOMP CROSS-CHECKS: corrections to our own bot docs and AI knowledge (VERIFIED)

| claim in our tree | decomp says | consequence |
|---|---|---|
| "~3 Bug-Catcher trainers" in the Woods (`12-STORYMODE-DESIGN.md:2560-2561`, `early_game.py:1687`) | **two**: LYLE (7,32), sight 3, a party of L3 Wurmple; JAMES (4,14), sight 3, Nincada L6 ×2 (`PetalburgWoods/map.json` objs; `trainer_parties.h:8163`, `:8233`). The third battle is the grunt. | small; expectations should say 2 + grunt |
| "two gym Youngsters" (`12-STORYMODE-DESIGN.md:2572`, `early_game.py:2063`) and `milestones.json` `ch4_gym_trainers` = {JOSH, TOMMY} | **three**: JOSH (5,13), sight 2, Geodude L10; TOMMY (3,9), sight 3, Geodude L8 ×2; **MARC, a Hiker, at (1,6), sight 3, Geodude L8 ×2** (`RustboroCity_Gym/map.json` objs 1, 2, 4; `trainer_parties.h:4227`, `:4236`, `:7649`) | **MARC is missing** from the AI's milestone data and from the `trainers` table (`milestones.json:226-249`). The bot's straight path just never met him. |
| "Advance dialogue until BADGE01_GET" (`early_game.py:2064`) | `RoxanneDefeated` sets `FLAG_BADGE01_GET` (and `DEFEATED_RUSTBORO_GYM`, `VAR_RUSTBORO_CITY_STATE=1`) **before** `giveitem ITEM_TM_ROCK_TOMB` and the TM explanation (`RustboroCity_Gym/scripts.inc:13-34`) | a "done" check on the badge fires mid-scene. The bot follows it with `_wait_until_cutscene_over`; the AI must also wait for the TM text to finish. |
| the gym guide | at (3,18): "ROXANNE … ROCK-type … can't stand WATER-type and GRASS-type moves" (`RustboroCity_Gym/scripts.inc` `GymGuideAdvice`) | ⭐ a **person-fair** type hint the AI may use. Fighting is not named. |
| Route 104 north twins | `trainerbattle_double TRAINER_GINA_AND_MIA_1` with a `…NotEnoughMons` text (`Route104/scripts.inc:966`, `:973`); twins at (27-28,15), sight 1 | with a one-mon party they refuse. The AI must read that as "not now", not as a failure. |
| Route 104's rival trigger (17,51) | gated on `VAR_ROUTE104_STATE == 1`, which is set only in Rustboro by an ON_FRAME script gated on `VAR_RUSTBORO_CITY_STATE == 6` (post-PokéNav, `RustboroCity/scripts.inc:27-33`) | it cannot fire in ch3/ch4 |
| arriving in Rustboro | `RustboroCity_OnTransition` sets `FLAG_VISITED_RUSTBORO_CITY` (`RustboroCity/scripts.inc:6-7`) | matches `ch3_rustboro`'s done flag |

## 4. LEVEL 16 IS A TRAP FOR EVERY STARTER, AND B MAKES IT WORSE (VERIFIED)

- **The bot's band ends right at 16.** It is `(13, 17)` and the ace is L15. All three starters evolve at 16, and the
  badge data shows nearly every win came after evolving (§1).
- **Holding B during the evolution animation cancels it** (`src/evolution_scene.c:637-647`, "check if B Button was
  held, so the evolution gets stopped").
- **B on the "learn the move?" yes/no answers NO** (`:946-951`).
- **The consequence for Torchic.** A Torchic stopped at 16 learns **Peck** (Flying, resisted by Rock), not Combusken's
  **Double Kick**. Its one good move against ROXANNE is then gone.
- **The bot's fix.** Always allow evolution, after a cancel path hung (ML-10).
- **A learner that advances text with B can throw away the gym.** A person does not hold B through an evolution they
  want.

## 5. WHAT A PERSON IS TOLD HERE: the only hints the AI may use

### 5a. Dialogue and signs (VERIFIED decomp text)
- **DAD:** "Head for RUSTBORO CITY … challenge the GYM LEADER, ROXANNE". This is already the hint in `milestones.json`.
- **Woods researcher:** "TEAM AQUA … after something in RUSTBORO" (`PetalburgWoods/scripts.inc:351-354`).
- **Woods sign 1, TRAINER TIPS:** "To raise a weak POKéMON, put it at the left of the team list … switch it out. It
  will earn EXP Points" (`:437-445`). The game itself teaches swap-training.
- **Woods sign 2:** PP, and "taken to a POKéMON CENTER" (`:447-453`).
- **Woods Boy 1:** "stay out of tall grass" if your Pokémon are weak (`:410-415`).
- **Woods Boy 2:** hidden items, "I always check where I'm walking" (`:417-421`).
- **Rustboro gym guide:** the Water/Grass advice (§3).
- **Route 104 sign:** TRAINER TIPS on double battles (`Route104/map.json` bg (17,23)).

### 5b. The researcher's first line asks about SHROOMISH (`:303-306`)
A person-fair nudge to catch one. It is Grass-type, which counters ROXANNE. UNVERIFIED that Shroomish is in the Woods
table; check `modules/data` before using it in an expectation.

## 6. WHAT THE BOT NEVER DID HERE: it cannot teach these (VERIFIED by grep)

A grep of `sandbox-pokebot/modules/story/*.py` and `story_mode.py` finds no code for the following. All are RULING 33
material that the AI must learn without a teacher.

**Gifts:**
- **Quick Claw** from the Rustboro school teacher. No badge gate before `giveitem` (`RustboroCity_PokemonSchool/scripts.inc:77-88`).
- **White Herb.** ⚠ **Not available in ch3/ch4.** The flower-shop woman at Route 104 (8,19) stays hidden until
  `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` **and** `FLAG_BADGE03_GET` are set (`Route104/scripts.inc:21-29`; the gift is at
  `:265-272`).
- **Chesto Berry** from the woman at (37,8) on Route 104 (`:248-255`).
- **Miracle Seed** from the Woods girl at (33,5). Her text presumes the STONE BADGE (`PetalburgWoods/scripts.inc:229-237`,
  `:423-427`). Two Cut trees stand at (19,10-11). UNVERIFIED that they wall her off.

**Visible items:**
- Woods: Great Ball (45,7), X Attack (35,20), Ether (4,8), Paralyze Heal (4,26).
- Route 104: Poké Ball (29,53), Potion (5,8), X Accuracy (37,22), PP Up (39,15). The PP Up may be behind the Cut tree at
  (35,22). UNVERIFIED.

**Hidden items:**
- Woods: Potion, Tiny Mushroom ×2, Poké Ball.
- Route 104: Super Potion, Poké Ball, Potion, Antidote, Heart Scale.
- Source: both `map.json` `bg_events`.

**Berry trees:** on Route 104 (`map.json` objs 9-14, 16-19).

**Why the balls matter.** The free balls alone would cover much of the shortage in §2h.

## 7. RISKS FOR WHOEVER BUILDS THE ch3/ch4 PROOFS (UNVERIFIED unless cited)

1. **The Woods scene may be avoidable** (§2e). If it is, the goal manager could loop, because the done-var is shared by
   two milestones. Check before relying on it.
2. **MARC** is absent from `milestones.json` (§3). A proof that "all gym trainers are optional" or "ROXANNE by badge
   alone" should know he exists, and that his sight line (sight 3 at (1,6)) may or may not touch a person's path.
3. **The badge flag flips before the TM text**, and Scott's var flips before his dialogue (§2a, §3). A goal that is
   "done" while a box is still up must not make the AI walk or press A.
4. **L16 evolution and move-learn inside the gym** (§4). A seeded proof should include a starter that crosses 16
   mid-fight.
5. **Expect a one-mon party through all of ch3.** The bot reached Rustboro as a party of one Mudkip L13 (`rustboro.ss1`
   per `2026-09-27-pregym1-cap-RECON.md`). Expect refused doubles and un-fleeable trainers.

## SOURCES READ
- **Our docs:** `05-KNOWN-ISSUES.md` (KI-8), `31-KNOWN-ISSUES-ARCHIVE.md` (KI-15), `08-MISTAKES.md` (ML-7/8/9/10/13 and
  the 2026-07-21, 07-24, 07-30, 07-31, 09-12 and 09-26 entries), `12-STORYMODE-DESIGN.md` (§3 Ch3-4, §16, §16.1, the
  Rustboro Atlas), `14-AGENT-PLAYBOOK.md` §4, `07-CHANGELOG.md`, `06-DECISIONS-LOG.md`.
- **Agent notes:** `2026-09-26-woods-{PREDICTIONS,GRADED}.md`, `2026-09-27-pregym1-cap-RECON.md`,
  `2026-10-01-batch14-recon/b14_recon_stats.md`.
- **Our code:** `sandbox-pokebot/modules/story/early_game.py`, `training_areas.py`, `plugins/custom_modes/story_mode.py`,
  `ai_player/knowledge/milestones.json`.
- **Data:** 129 `badge-log.json` files.
- **Decomp:** `data/maps/{PetalburgWoods,Route104,RustboroCity_Gym}/{map.json,scripts.inc}`,
  `data/maps/{PetalburgCity,RustboroCity,RustboroCity_PokemonSchool}/scripts.inc`, `src/data/trainer_parties.h`,
  `src/data/pokemon/level_up_learnsets.h`, `src/evolution_scene.c`.
