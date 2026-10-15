"""TEACHER SIDE (build step 5): extract badge 1's STORY MILESTONES into the AI's own knowledge file, and check them.

    py -3.12 ai_player/gates/extract_milestones.py            # writes ai_player/knowledge/milestones.json
    py -3.12 ai_player/gates/extract_milestones.py --check    # exits 1 if the written file differs from a fresh extraction
    py -3.12 ai_player/gates/extract_milestones.py --verify [--plant] [--evidence PATH]
                                                              # every fact against pret/pokeemerald (gh api); --plant: three
                                                              # facts changed in memory must be found, and nothing else

WHY (USER RULING 35; design draft §3 "How the bot teaches it": "`modules/story/early_game.py` step docstrings ('STORY
CONDITION' / 'GOAL/END STATE') ... -> `milestones.json`: ordered story beats as {needs flags, sets flag, where}: the goal
manager knows WHAT comes next; the AI decides HOW"). The story bot is TEACHING material: this script reads the bot's DATA
(its event flag and var tables, `sandbox-pokebot/modules/data/event_{flags,vars}/emerald.txt`: name -> number) and NAMES the
bot's chapter functions whose docstrings taught each beat (`modules/story/early_game.py`: the line found by name, the file's
sha256 recorded), and writes the AI's own `ai_player/knowledge/milestones.json`. It never imports the bot and the play loop
never reads the bot: `ai_player/knowledge/story.py` reads only the JSON.

WHAT A MILESTONE CARRIES (USER RULING 37 Q3: badge 1 in 4 chapters):
  * `done`: the FLAGS that must be set, the VARS that must have reached a value, the TRAINERS whose defeated flag must be
    set (flag `TRAINER_FLAGS_START` 0x500 + the trainer's id): what PROVES it happened, each with its number;
  * `maps`: where it happens (a map constant as the eyes name it; `<player_house_2f>` and the like are resolved by the
    player's gender: the player's house and the rival's swap between BOY and GIRL, `InsideOfTruck_EventScript_SetIntroFlags`);
  * `steps`: what a person DOES for it, in order (`go` to a map, `use` a thing / `talk` to someone who LOOKS like something,
    `ask` the people of a map until some words are heard, `follow` a scene that plays by itself);
  * `hint`: what the GAME TELLS the player in dialogue, quoted from the decomp, and the WORDS whose reading unlocks it (the
    goal manager uses a hint's map only after the AI has READ those words on screen: `world/memory.py` heard);
  * `fight`: the trainers met and their party levels (`src/data/trainer_parties.h`), for the train-before-a-fight errand;
  * `taught_by` (the bot's function and its line) and `decomp` (the script that sets each proof).
LOOKS (`looks`): what a person RECOGNISES on screen, by what the eyes report: a person by their figure (`graphics_id`,
`include/constants/event_objects.h`), a thing on a wall or a door by its metatile (`include/constants/metatile_labels.h`; the
wall clock MEASURED on `gates/fixtures/clock_room.ss1` and checked against both houses' layouts in the decomp).

VERIFY (`--verify`): through `gh api repos/pret/pokeemerald/contents/...`: every flag's `#define` (expressions such as
`(SYSTEM_FLAGS + 0x84)` evaluated) equals the bot table's number; every var's `#define` equals 0x4000 + the table's number;
every proof is SET by the script file the milestone names (`setflag FLAG_X` / `setvar VAR_X, N`, or `trainerbattle* TRAINER_X`
for a trainer); every trainer's id (`include/constants/opponents.h`) and party levels (`src/data/trainers.h` ->
`src/data/trainer_parties.h`); every look's graphics id and metatile; and each hint's quoted words appear in the decomp text
of the map it names. `--plant` changes three facts in memory (a flag number, a fight level, a look) and must report exactly
those three.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BOT = REPO / "sandbox-pokebot"
FLAG_TABLE = BOT / "modules" / "data" / "event_flags" / "emerald.txt"
VAR_TABLE = BOT / "modules" / "data" / "event_vars" / "emerald.txt"
TEACHER = BOT / "modules" / "story" / "early_game.py"
OUT = REPO / "ai_player" / "knowledge" / "milestones.json"
REPOSITORY = "pret/pokeemerald"
TRAINER_FLAGS_START = 0x500
VARS_START = 0x4000

#: Maps that depend on the player's GENDER (`data/maps/InsideOfTruck/scripts.inc` SetIntroFlagsMale / Female: a BOY lives
#: in BRENDAN's house and his rival MAY next door; a GIRL the other way round).
GENDERED_MAPS: dict[str, dict[str, str]] = {
    "player_house_1f": {"BOY": "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", "GIRL": "LITTLEROOT_TOWN_MAYS_HOUSE_1F"},
    "player_house_2f": {"BOY": "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F", "GIRL": "LITTLEROOT_TOWN_MAYS_HOUSE_2F"},
    "rival_house_1f": {"BOY": "LITTLEROOT_TOWN_MAYS_HOUSE_1F", "GIRL": "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F"},
    "rival_house_2f": {"BOY": "LITTLEROOT_TOWN_MAYS_HOUSE_2F", "GIRL": "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F"},
}

#: What a person RECOGNISES (module docstring, LOOKS). `gfx`: object graphics ids; `metatile`: a tile's metatile id; `decomp`:
#: the constant each is checked against (`--verify`).
LOOKS: dict[str, dict] = {
    "clock": {"metatile": [0x22F, 0x28F], "what": "the new wall clock on the wall of the player's room",
              "decomp": "bg_event *_EventScript_WallClock at (5, 1) of LittlerootTown_{Brendans,Mays}House_2F (`--verify`); "
                        "its metatile is the LIVE grid's, MEASURED (the bedrooms are decorated on load: "
                        "SecretBase_EventScript_InitDecorations setmetatile's them, so the ROM layout holds another tile there)",
              "measured": [{"map": "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F", "x": 5, "y": 1, "metatile": 0x28F,
                            "state": "ai_player/gates/fixtures/clock_room.ss1 (the AI's eyes, 2026-10-14)"},
                           {"map": "LITTLEROOT_TOWN_MAYS_HOUSE_2F", "x": 3, "y": 1, "metatile": 0x22F,
                            "state": "the play brain's own New Game (play_harness --fresh --seed 1 --personality Story, "
                                     "game clock 2026-10-14T10:00), saved at f17152 on arriving upstairs (the AI's eyes, "
                                     "2026-10-14)"}]},
    "pokemon_center_door": {"metatile": [0x061], "what": "the door of a POKéMON CENTER (red roof, POKé sign)",
                            "decomp": "METATILE_General_Door_PokeCenter"},
    "mart_door": {"metatile": [0x041], "what": "the door of a POKéMON MART (blue roof, MART sign)",
                  "decomp": "METATILE_General_Door_PokeMart"},
    # (build step 5.1, the verifier's second round: the live CH2T arm searched PETALBURG CITY door by door for its GYM) the
    # gym's door is the GENERAL tileset's, the same in every city: METATILE_General_Door_Gym (0x1CD) under the warp to
    # MAP_PETALBURG_CITY_GYM at (15, 8) of `data/layouts/PetalburgCity/map.bin` and to MAP_RUSTBORO_CITY_GYM at (27, 19) of
    # `data/layouts/RustboroCity/map.bin` (read 2026-10-14 from pret/pokeemerald by blob, low 10 bits of each block)
    "gym_door": {"metatile": [0x1CD], "what": "the door of a POKéMON GYM (the big building, the GYM sign)",
                 "decomp": "METATILE_General_Door_Gym"},
    "nurse":{"gfx": [58], "what": "the POKéMON CENTER nurse", "decomp": "OBJ_EVENT_GFX_NURSE"},
    "clerk": {"gfx": [83], "what": "the mart's clerk", "decomp": "OBJ_EVENT_GFX_MART_EMPLOYEE"},
    "birchs_bag": {"gfx": [97], "what": "PROF. BIRCH's bag on the ground", "decomp": "OBJ_EVENT_GFX_BIRCHS_BAG"},
    "rival": {"gfx": [105, 100], "what": "the rival (MAY or BRENDAN), met in the rival's room",
              "decomp": "OBJ_EVENT_GFX_RIVAL_MAY_NORMAL, OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL"},
    "rivals_poke_ball": {"gfx": [59], "what": "the POKé BALL on the floor of the rival's room",
                         "decomp": "OBJ_EVENT_GFX_ITEM_BALL"},
    "norman": {"gfx": [129], "what": "DAD (NORMAN), the PETALBURG GYM leader", "decomp": "OBJ_EVENT_GFX_NORMAN"},
    "mom": {"gfx": [215], "what": "MOM, at home (she heals the party once PROF. BIRCH is rescued)", "decomp": "OBJ_EVENT_GFX_MOM"},
    "roxanne": {"gfx": [125], "what": "ROXANNE, the RUSTBORO GYM leader", "decomp": "OBJ_EVENT_GFX_ROXANNE"},
}

#: What a person hears and the map it names: the words (as the eyes read a page, upper case where the game writes it).
#: Each `said` is quoted from the decomp file named (`--verify` finds the words there). A hint's `map` is the place its
#: words NAME (or the map whose own script says them: heard there); a hint with no words names nothing, and the goal
#: manager heads for its map only once the AI has been there (`brain/goals.py` hint_known). `gates/test_goals.py`
#: HintTests checks every hint against that rule.
#: DAD after WALLY's tutorial (`PetalburgCity_Gym_Text_DadGoCollectBadges`, read 2026-10-14 through gh api): where chapters 3
#: and 4 lead.
DAD_RUSTBORO = {"said": "DAD: Now... {PLAYER}, if you want to become a strong TRAINER, here's my advice. Head for RUSTBORO "
                        "CITY beyond this town. There, you should challenge the GYM LEADER, ROXANNE.",
                "words": "RUSTBORO CITY", "map": "RUSTBORO_CITY", "file": "data/maps/PetalburgCity_Gym/scripts.inc"}
# ---------------------------------------------------------------------------------------------------- the milestones
#: The AUTHORED teaching table (RULING 35: the bot's chapter docstrings and the decomp taught it; every proof, number and
#: level is checked by `--verify`). `steps` vocabulary: the module docstring.
MILESTONES: list[dict] = [
    # ---------------------------------------------------------------- CHAPTER 1: the intro to the Pokedex
    {"id": "ch1_intro", "chapter": 1, "title": "A New Game: name, gender, the moving truck",
     "done": {"vars": {"LITTLEROOT_INTRO_STATE": 1}}, "waypoint": "INSIDE_OF_TRUCK", "maps": ["INSIDE_OF_TRUCK"],
     "steps": [{"do": "intro"}],
     "note": "VAR_LITTLEROOT_INTRO_STATE is set by a COORD event inside the truck (`InsideOfTruck_EventScript_SetIntroFlags`, "
             "map.json coord_events), i.e. on the first steps toward its door: the intro itself ends earlier, standing in "
             "the truck, so the milestone is passed once the AI stands on INSIDE_OF_TRUCK (the waypoint)",
     "hint": {"said": "PROF. BIRCH's welcome speech (the New Game intro)", "words": None, "map": None},
     "taught_by": [("modules/story/intro.py", None)],
     "decomp": {"LITTLEROOT_INTRO_STATE": "data/maps/InsideOfTruck/scripts.inc"}},
    {"id": "ch1_truck", "chapter": 1, "title": "Off the moving truck into LITTLEROOT TOWN",
     "done": {"flags": ["VISITED_LITTLEROOT_TOWN"]}, "maps": ["INSIDE_OF_TRUCK", "LITTLEROOT_TOWN"],
     "steps": [{"do": "go", "map": "LITTLEROOT_TOWN"}],
     "hint": {"said": "the truck has stopped; the light of its open back door", "words": None, "map": "LITTLEROOT_TOWN"},
     "taught_by": [("modules/story/early_game.py", "walk_off_truck_and_into_house")],
     "decomp": {"VISITED_LITTLEROOT_TOWN": "data/maps/LittlerootTown/scripts.inc"}},
    {"id": "ch1_mom", "chapter": 1, "title": "MOM shows the player into the new house",
     "done": {"vars": {"LITTLEROOT_INTRO_STATE": 4}}, "maps": ["LITTLEROOT_TOWN", "<player_house_1f>"],
     "steps": [{"do": "follow"}],
     "hint": {"said": "MOM: ... your room is upstairs. Go check it out, dear! DAD bought you a new clock ... Don't forget to "
                      "set it!", "words": None, "map": None, "file": "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "walk_off_truck_and_into_house")],
     "decomp": {"LITTLEROOT_INTRO_STATE": "data/scripts/players_house.inc"}},
    {"id": "ch1_clock", "chapter": 1, "title": "Set the wall clock in the player's room",
     "done": {"flags": ["SET_WALL_CLOCK"]}, "maps": ["<player_house_2f>"],
     "steps": [{"do": "go", "map": "<player_house_2f>", "told": "upstairs"},
               {"do": "use", "map": "<player_house_2f>", "look": "clock", "told": "clock"}],
     "hint": {"said": "MOM: {PLAYER}, your room is upstairs. ... DAD bought you a new clock to mark our move here. Don't "
                      "forget to set it!", "words": "clock", "map": "<player_house_2f>",
              "file": "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "go_upstairs_and_set_clock")],
     "decomp": {"SET_WALL_CLOCK": "data/scripts/players_house.inc"}},
    {"id": "ch1_rival_house", "chapter": 1, "title": "Next door: meet the rival in the rival's house",
     "done": {"vars": {"LITTLEROOT_RIVAL_STATE": 3}},
     "maps": ["<rival_house_1f>", "<rival_house_2f>"],
     "steps": [{"do": "go", "map": "<rival_house_1f>", "told": "next door"},
               {"do": "go", "map": "<rival_house_2f>", "told": "is upstairs, I think",
                "file": "data/maps/LittlerootTown_MaysHouse_1F/scripts.inc"}],
     "note": "(build step 5.1, the step-5 review's finding 3) no step says 'use the POKé BALL on the floor': the game never "
             "tells the player to. The rival's mom says the rival 'is upstairs' (RivalsHouse_1F_Text_OhYoureTheNewNeighbor), "
             "and upstairs a POKé BALL lies on the floor (an object with the item ball's look, "
             "LittlerootTown_MaysHouse_2F_EventScript_RivalsPokeBall, which plays MeetMay at VAR_LITTLEROOT_RIVAL_STATE 2): "
             "the AI's item curiosity walks up to it, as a person's does",
     "hint": {"said": "MOM: One of DAD's friends lives in town. PROF. BIRCH is his name. He lives right next door, so you "
                      "should go over and introduce yourself.", "words": "next door", "map": "<rival_house_1f>",
              "file": "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "visit_rivals_house")],
     "decomp": {"LITTLEROOT_RIVAL_STATE": "data/maps/LittlerootTown_MaysHouse_2F/scripts.inc"}},
    {"id": "ch1_birch", "chapter": 1, "title": "Route 101: PROF. BIRCH chased by a wild POKéMON; open his bag",
     "done": {"flags": ["RESCUED_BIRCH"]}, "maps": ["LITTLEROOT_TOWN", "ROUTE101"],
     "steps": [{"do": "go", "map": "ROUTE101", "told": "BAG"},
               {"do": "use", "map": "ROUTE101", "look": "birchs_bag", "told": "BAG"}],
     "hint": {"said": "PROF. BIRCH: Hello! You over there! Please! Help! In my BAG! There's a POKé BALL!",
              "words": "BAG", "map": "ROUTE101", "file": "data/maps/Route101/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "_go_north_to_birch_rescue")],
     "decomp": {"RESCUED_BIRCH": "data/maps/Route101/scripts.inc"}},
    {"id": "ch1_starter", "chapter": 1, "title": "Choose a starter from the bag and win the first battle",
     "done": {"flags": ["SYS_POKEMON_GET"], "vars": {"BIRCH_LAB_STATE": 2}}, "maps": ["ROUTE101"],
     "steps": [{"do": "follow"}],
     "hint": {"said": "the three POKé BALLS of the bag: 'Do you choose this POKéMON?'", "words": None, "map": None},
     "fight": {"wild": "ZIGZAGOON", "levels": [2]},
     "taught_by": [("modules/story/early_game.py", "help_birch_and_choose_starter")],
     "decomp": {"SYS_POKEMON_GET": "data/maps/Route101/scripts.inc", "BIRCH_LAB_STATE": "data/maps/Route101/scripts.inc"}},
    {"id": "ch1_lab", "chapter": 1, "title": "In the lab: the starter is the player's, and Birch sends the player to the rival",
     "done": {"vars": {"BIRCH_LAB_STATE": 3}}, "maps": ["LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB"],
     "steps": [{"do": "follow"}],
     "hint": {"said": "PROF. BIRCH: My kid, {RIVAL}, is also studying POKéMON ... don't you think it might be a good idea to "
                      "go see {RIVAL}?", "words": None, "map": None,
              "file": "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "finish_birch_lab")],
     "decomp": {"BIRCH_LAB_STATE": "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"}},
    {"id": "ch1_rival_route103", "chapter": 1, "title": "Find the rival on ROUTE 103 and win the battle",
     "done": {"flags": ["DEFEATED_RIVAL_ROUTE103"]}, "maps": ["<rival_house_1f>", "OLDALE_TOWN", "ROUTE103"],
     "steps": [{"do": "ask", "map": "<rival_house_1f>", "words": "ROUTE 103"},
               {"do": "go", "map": "ROUTE103", "told": "ROUTE 103"},
               {"do": "talk", "map": "ROUTE103", "look": "rival", "told": "ROUTE 103"}],
     "hint": {"said": "the rival's mom: Oh, {RIVAL} went out to ROUTE 103 just a little while ago.", "words": "ROUTE 103",
              "map": "ROUTE103", "file": "data/maps/LittlerootTown_MaysHouse_1F/scripts.inc"},
     # (build step 5.1) NAMED: the rival is a fight the game names to the player (RULING 33's "train to the leader's
     # level" applies to the rival and the gym leaders only; any other trainer's levels are learned when SEEN)
     "fight": {"trainers": ["MAY_ROUTE_103_TREECKO", "MAY_ROUTE_103_TORCHIC", "MAY_ROUTE_103_MUDKIP",
                            "BRENDAN_ROUTE_103_TREECKO", "BRENDAN_ROUTE_103_TORCHIC", "BRENDAN_ROUTE_103_MUDKIP"],
               "named": True},
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: `DEFEATED_RIVAL_ROUTE103` is set")],
     "decomp": {"DEFEATED_RIVAL_ROUTE103": "data/maps/Route103/scripts.inc"}},
    {"id": "ch1_pokedex", "chapter": 1, "title": "Back to the lab: the POKéDEX from PROF. BIRCH",
     "done": {"flags": ["RECEIVED_POKEDEX_FROM_BIRCH", "SYS_POKEDEX_GET", "ADVENTURE_STARTED"]},
     "maps": ["ROUTE103", "LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB"],
     "steps": [{"do": "go", "map": "LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", "told": "LAB"}, {"do": "follow"}],
     "hint": {"said": "MAY: Well, it's time to head back to the LAB.", "words": "LAB",
              "map": "LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", "file": "data/maps/Route103/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "GOAL/END STATE: `RECEIVED_POKEDEX_FROM_BIRCH` is set")],
     "decomp": {"RECEIVED_POKEDEX_FROM_BIRCH": "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc",
                "SYS_POKEDEX_GET": "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc",
                "ADVENTURE_STARTED": "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"}},
    # ---------------------------------------------------------------- CHAPTER 2: Oldale to Petalburg (Wally's tutorial)
    {"id": "ch2_oldale", "chapter": 2, "title": "OLDALE TOWN (its mart sells POKé BALLS once the adventure has started)",
     "done": {"flags": ["VISITED_OLDALE_TOWN"]}, "maps": ["ROUTE101", "OLDALE_TOWN"],
     "steps": [{"do": "go", "map": "OLDALE_TOWN"}],
     "hint": {"said": "ROUTE 101 sign: ROUTE 101 {UP_ARROW} OLDALE TOWN", "words": None, "map": "OLDALE_TOWN",
              "file": "data/maps/Route101/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "GOAL/END STATE: `RECEIVED_POKEDEX_FROM_BIRCH` is set")],
     "decomp": {"VISITED_OLDALE_TOWN": "data/maps/OldaleTown/scripts.inc"}},
    {"id": "ch2_route102", "chapter": 2, "title": "West of Oldale: ROUTE 102 and its trainers (open once the adventure has started)",
     "done": {"flags": ["VISITED_PETALBURG_CITY"]}, "waypoint": "ROUTE102", "maps": ["OLDALE_TOWN", "ROUTE102"],
     "steps": [{"do": "go", "map": "PETALBURG_CITY", "told": "PETALBURG"}],
     "hint": {"said": "MOM, on the TV: Look! It's PETALBURG GYM! Maybe DAD will be on!", "words": "PETALBURG",
              "map": "PETALBURG_CITY", "file": "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc"},
     "fight": {"trainers": ["CALVIN_1", "RICK", "TIANA", "ALLEN"]},
     "note": "no save flag records a walk through ROUTE 102: the eyes see the map, and FLAG_VISITED_PETALBURG_CITY, which "
             "only that walk can set before SURF, is the save's proof. The game never NAMES ROUTE 102 to the player: the "
             "place it names is PETALBURG, so that is where the AI heads (the step-5 verifier, 2026-10-14); ROUTE 102 is "
             "the waypoint passed on the way",
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: begins in Petalburg City with the Pokédex")],
     "decomp": {"VISITED_PETALBURG_CITY": "data/maps/PetalburgCity/scripts.inc"}},
    {"id": "ch2_petalburg", "chapter": 2, "title": "PETALBURG CITY, where DAD runs the GYM",
     "done": {"flags": ["VISITED_PETALBURG_CITY"]}, "maps": ["ROUTE102", "PETALBURG_CITY"],
     "steps": [{"do": "go", "map": "PETALBURG_CITY", "told": "PETALBURG"}],
     "hint": {"said": "MOM, on the TV: Look! It's PETALBURG GYM! Maybe DAD will be on!", "words": "PETALBURG",
              "map": "PETALBURG_CITY", "file": "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: begins in Petalburg City with the Pokédex")],
     "decomp": {"VISITED_PETALBURG_CITY": "data/maps/PetalburgCity/scripts.inc"}},
    {"id": "ch2_dad", "chapter": 2, "title": "DAD at the PETALBURG GYM: talk to him (WALLY walks in)",
     "done": {"flags": ["HIDE_PETALBURG_CITY_WALLYS_MOM"]}, "maps": ["PETALBURG_CITY", "PETALBURG_CITY_GYM"],
     "steps": [{"do": "go", "map": "PETALBURG_CITY_GYM", "told": "PETALBURG GYM"},
               {"do": "talk", "map": "PETALBURG_CITY_GYM", "look": "norman", "told": "PETALBURG GYM"}],
     "hint": {"said": "MOM, on the TV: Look! It's PETALBURG GYM! Maybe DAD will be on!", "words": "PETALBURG GYM",
              "map": "PETALBURG_CITY_GYM", "file": "data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: begins in Petalburg City with the Pokédex")],
     "decomp": {"HIDE_PETALBURG_CITY_WALLYS_MOM": "data/maps/PetalburgCity_Gym/scripts.inc"}},
    {"id": "ch2_wally", "chapter": 2, "title": "WALLY's catching tutorial, back in the gym",
     "done": {"vars": {"PETALBURG_GYM_STATE": 2}}, "maps": ["PETALBURG_CITY", "PETALBURG_CITY_GYM"],
     "steps": [{"do": "follow"}],
     "hint": {"said": "DAD: {PLAYER}, go with WALLY ... (the tutorial plays as one scene)", "words": None, "map": None,
              "file": "data/maps/PetalburgCity_Gym/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: begins in Petalburg City with the Pokédex")],
     "decomp": {"PETALBURG_GYM_STATE": "data/maps/PetalburgCity_Gym/scripts.inc"}},
    # ---------------------------------------------------------------- CHAPTER 3: Route 104, Petalburg Woods, Rustboro
    {"id": "ch3_route104", "chapter": 3, "title": "West of Petalburg: ROUTE 104 (south)",
     "done": {"vars": {"PETALBURG_WOODS_STATE": 1}}, "waypoint": "ROUTE104", "maps": ["PETALBURG_CITY", "ROUTE104"],
     "steps": [{"do": "go", "map": "RUSTBORO_CITY", "told": "RUSTBORO CITY"}],
     "hint": DAD_RUSTBORO,
     "note": "no save flag records the walk onto ROUTE 104: the eyes see the map; VAR_PETALBURG_WOODS_STATE, set past it, is "
             "the save's proof. DAD names RUSTBORO CITY, never ROUTE 104, so that is where the AI heads (the step-5 "
             "verifier, 2026-10-14); ROUTE 104 is the waypoint passed on the way",
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: begins controllable in Petalburg (post-Wally tutorial)")],
     "decomp": {"PETALBURG_WOODS_STATE": "data/maps/PetalburgWoods/scripts.inc"}},
    {"id": "ch3_woods", "chapter": 3, "title": "PETALBURG WOODS: the TEAM AQUA GRUNT bothering the DEVON researcher",
     "done": {"vars": {"PETALBURG_WOODS_STATE": 1}}, "maps": ["PETALBURG_WOODS"],
     "steps": [{"do": "go", "map": "RUSTBORO_CITY", "told": "RUSTBORO CITY"}, {"do": "follow"}],
     "hint": DAD_RUSTBORO,
     "fight": {"trainers": ["GRUNT_PETALBURG_WOODS"]},  # not named: its levels are learned when SEEN (build step 5.1)
     "note": "the woods are on the way to RUSTBORO CITY, which DAD names: the scene with the DEVON researcher plays as the "
             "player walks through them",
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: begins just inside the Woods south entrance")],
     "decomp": {"PETALBURG_WOODS_STATE": "data/maps/PetalburgWoods/scripts.inc"}},
    {"id": "ch3_rustboro", "chapter": 3, "title": "RUSTBORO CITY",
     "done": {"flags": ["VISITED_RUSTBORO_CITY"]}, "maps": ["ROUTE104", "RUSTBORO_CITY"],
     "steps": [{"do": "go", "map": "RUSTBORO_CITY", "told": "RUSTBORO"}],
     "hint": {"said": "the DEVON researcher: TEAM AQUA ... after something in RUSTBORO", "words": "RUSTBORO",
              "map": "RUSTBORO_CITY", "file": "data/maps/PetalburgWoods/scripts.inc"},
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: standing on Route 104 north")],
     "decomp": {"VISITED_RUSTBORO_CITY": "data/maps/RustboroCity/scripts.inc"}},
    # ---------------------------------------------------------------- CHAPTER 4: the RUSTBORO GYM
    {"id": "ch4_gym_trainers", "chapter": 4, "title": "The RUSTBORO GYM's trainers",
     "done": {"trainers": ["JOSH", "TOMMY"]}, "maps": ["RUSTBORO_CITY_GYM"],
     # (build step 5.1, the step-5 review's finding 5) OPTIONAL: a path to ROXANNE may pass TOMMY by (he faces left at
     # (3, 9), RustboroCity_Gym/map.json), so ROXANNE is proven by her badge alone and this is never the current milestone
     "optional": True,
     "steps": [{"do": "go", "map": "RUSTBORO_CITY_GYM", "told": "ROXANNE"}, {"do": "follow"}],
     "hint": {**DAD_RUSTBORO, "words": "ROXANNE", "map": "RUSTBORO_CITY_GYM"},
     "fight": {"trainers": ["JOSH", "TOMMY"]},  # not named: learned when SEEN
     "taught_by": [("modules/story/early_game.py", "STORY CONDITION: in Rustboro City with a starter strong enough to win")],
     "decomp": {"JOSH": "data/maps/RustboroCity_Gym/scripts.inc", "TOMMY": "data/maps/RustboroCity_Gym/scripts.inc"}},
    {"id": "ch4_roxanne", "chapter": 4, "title": "ROXANNE: the STONE BADGE",
     "done": {"flags": ["DEFEATED_RUSTBORO_GYM", "BADGE01_GET"]}, "maps": ["RUSTBORO_CITY_GYM"],
     "steps": [{"do": "go", "map": "RUSTBORO_CITY_GYM", "told": "ROXANNE"},
               {"do": "talk", "map": "RUSTBORO_CITY_GYM", "look": "roxanne", "told": "ROXANNE"}],
     "hint": {**DAD_RUSTBORO, "words": "ROXANNE", "map": "RUSTBORO_CITY_GYM"},
     "fight": {"trainers": ["ROXANNE_1"], "named": True},  # DAD names her: "challenge the GYM LEADER, ROXANNE"
     "taught_by": [("modules/story/early_game.py", "GOAL/END STATE: BADGE01_GET set (Stone Badge earned)")],
     "decomp": {"DEFEATED_RUSTBORO_GYM": "data/maps/RustboroCity_Gym/scripts.inc",
                "BADGE01_GET": "data/maps/RustboroCity_Gym/scripts.inc"}},
]

#: The trainers' ids (`include/constants/opponents.h`) and party levels (`src/data/trainer_parties.h`), as the decomp says:
#: authored from it and CHECKED by `--verify` (the bot's trainer data is not read: the levels are a person's "how strong is
#: the next fight", which the human-reference note's boss table verified for the leaders, `knowledge.BOSS_LEVELS`).
TRAINERS: dict[str, dict] = {
    "MAY_ROUTE_103_TREECKO": {"id": 532, "levels": [5], "party": "sParty_MayRoute103Treecko"},
    "MAY_ROUTE_103_TORCHIC": {"id": 535, "levels": [5], "party": "sParty_MayRoute103Torchic"},
    "MAY_ROUTE_103_MUDKIP": {"id": 529, "levels": [5], "party": "sParty_MayRoute103Mudkip"},
    "BRENDAN_ROUTE_103_TREECKO": {"id": 523, "levels": [5], "party": "sParty_BrendanRoute103Treecko"},
    "BRENDAN_ROUTE_103_TORCHIC": {"id": 526, "levels": [5], "party": "sParty_BrendanRoute103Torchic"},
    "BRENDAN_ROUTE_103_MUDKIP": {"id": 520, "levels": [5], "party": "sParty_BrendanRoute103Mudkip"},
    "CALVIN_1": {"id": 318, "levels": [5], "party": "sParty_Calvin1"},
    "RICK": {"id": 615, "levels": [4, 4], "party": "sParty_Rick"},
    "TIANA": {"id": 603, "levels": [4, 4], "party": "sParty_Tiana"},
    "ALLEN": {"id": 333, "levels": [4, 3], "party": "sParty_Allen"},
    "GRUNT_PETALBURG_WOODS": {"id": 10, "levels": [9], "party": "sParty_GruntPetalburgWoods"},
    "JOSH": {"id": 320, "levels": [10], "party": "sParty_Josh"},
    "TOMMY": {"id": 321, "levels": [8, 8], "party": "sParty_Tommy"},
    "ROXANNE_1": {"id": 265, "levels": [12, 12, 15], "party": "sParty_Roxanne1"},
}


# ---------------------------------------------------------------------------------------------------- extraction
def _table(path: Path) -> dict[str, int]:
    """The bot's event table: one `<number> <NAME>` per line (decimal; flags absolute, vars from 0x4000)."""
    out: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            out[parts[1]] = int(parts[0])
    return out


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _teacher_line(text: str, needle: str | None) -> int | None:
    """The line of the bot's teaching text: `def <needle>(` for a function, else the first line holding `needle`."""
    if needle is None:
        return None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(f"def {needle}(") or line.startswith(f"def {needle} ("):
            return number
    for number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return number
    return None


def extract() -> dict:
    flags, evars = _table(FLAG_TABLE), _table(VAR_TABLE)
    teacher_text = TEACHER.read_text(encoding="utf-8")
    milestones = []
    for raw in MILESTONES:
        done = raw["done"]
        flag_numbers = {name: flags[name] for name in done.get("flags", [])}
        var_numbers = {name: VARS_START + evars[name] for name in done.get("vars", {})}
        trainer_flags = {name: TRAINER_FLAGS_START + TRAINERS[name]["id"] for name in done.get("trainers", [])}
        fight = raw.get("fight")
        if fight is not None and "trainers" in fight:
            fight = {**fight, "levels": sorted({lvl for name in fight["trainers"] for lvl in TRAINERS[name]["levels"]}),
                     "per_trainer": {name: TRAINERS[name]["levels"] for name in fight["trainers"]}}
        taught = []
        for file, needle in raw.get("taught_by", []):
            path = BOT / "modules" / "story" / Path(file).name if file.startswith("modules/story/") else BOT / file
            text = teacher_text if path == TEACHER else (path.read_text(encoding="utf-8") if path.is_file() else "")
            taught.append({"file": f"sandbox-pokebot/{file}", "what": needle, "line": _teacher_line(text, needle),
                           "sha256": _sha256(path) if path.is_file() else None})
        milestones.append({
            "id": raw["id"], "chapter": raw["chapter"], "title": raw["title"],
            "done": {"flags": flag_numbers, "variables": {name: {"number": var_numbers[name], "at_least": value}
                                                          for name, value in done.get("vars", {}).items()},
                     "trainers": trainer_flags},
            "waypoint": raw.get("waypoint"), "optional": bool(raw.get("optional")), "maps": raw["maps"],
            "steps": raw["steps"], "hint": raw["hint"],
            "fight": fight, "note": raw.get("note"), "taught_by": taught, "decomp": raw["decomp"],
        })
    return {
        "provenance": {
            "extractor": "ai_player/gates/extract_milestones.py",
            "teacher": [{"file": "sandbox-pokebot/modules/story/early_game.py", "sha256": _sha256(TEACHER)}],
            "tables": [{"file": "sandbox-pokebot/modules/data/event_flags/emerald.txt", "sha256": _sha256(FLAG_TABLE)},
                       {"file": "sandbox-pokebot/modules/data/event_vars/emerald.txt", "sha256": _sha256(VAR_TABLE)}],
            "checked_against": f"{REPOSITORY} (`--verify`)",
            "rule": "RULING 35: teaching DATA only; the play loop reads this file through ai_player/knowledge/story.py",
        },
        "gendered_maps": GENDERED_MAPS,
        "looks": LOOKS,
        "trainers": {name: {"id": info["id"], "flag": TRAINER_FLAGS_START + info["id"], "levels": info["levels"]}
                     for name, info in TRAINERS.items()},
        "milestones": milestones,
    }


def render(data: dict) -> str:
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------------------------------- verification
def fetch(path: str) -> str:
    result = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/contents/{path}", "-H", "Accept: application/vnd.github.raw"],
                            capture_output=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path}: {result.stderr.decode(errors='replace')[:300]}")
    return result.stdout.decode("utf-8", errors="replace")


def fetch_bytes(path: str) -> bytes:
    """A BINARY file of the decomp, through the contents API's base64 (measured 2026-10-14: the raw media type through
    `gh` on Windows returned 192 bytes for a 144-byte map.bin: its line ends were translated)."""
    result = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/contents/{path}"], capture_output=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path}: {result.stderr.decode(errors='replace')[:300]}")
    import base64

    return base64.b64decode(json.loads(result.stdout.decode("utf-8"))["content"])


def defines(header: str) -> dict[str, str]:
    return {m.group(1): m.group(2).split("//")[0].strip() for m in re.finditer(r"^#define\s+(\w+)\s+(.+)$", header, re.M)}


def evaluate(name: str, table: dict[str, str], depth: int = 0) -> int:
    """A `#define`'s value: numbers, other defines, + and parentheses (flags.h's `(SYSTEM_FLAGS + 0x84)`)."""
    if depth > 20:
        raise ValueError(f"{name}: too deep")
    expr = table[name]
    tokens = re.findall(r"0x[0-9A-Fa-f]+|\d+|\w+|[+\-()]", expr)
    out = []
    for token in tokens:
        if re.fullmatch(r"0x[0-9A-Fa-f]+|\d+", token):
            out.append(str(int(token, 0)))
        elif re.fullmatch(r"\w+", token):
            out.append(str(evaluate(token, table, depth + 1)))
        else:
            out.append(token)
    return int(eval("".join(out), {"__builtins__": {}}, {}))  # noqa: S307 - digits, + - and parentheses only


def party_levels(parties: str, label: str) -> list[int]:
    found = re.search(rf"{label}\[\]\s*=\s*\{{(.*?)\n\}};", parties, re.S)
    return [int(v) for v in re.findall(r"\.lvl\s*=\s*(\d+)", found.group(1))] if found else []


def verify(data: dict, say) -> list[str]:
    problems: list[str] = []
    opponents = defines(fetch("include/constants/opponents.h"))
    # (flags.h's SYSTEM_FLAGS is TRAINER_FLAGS_END + 1, and that is TRAINER_FLAGS_START + MAX_TRAINERS_COUNT - 1, a
    # constant of opponents.h)
    flags_h = {**opponents, **defines(fetch("include/constants/flags.h"))}
    vars_h = defines(fetch("include/constants/vars.h"))
    trainers_h = fetch("src/data/trainers.h")
    parties = fetch("src/data/trainer_parties.h")
    objects = defines(fetch("include/constants/event_objects.h"))
    metatiles = defines(fetch("include/constants/metatile_labels.h"))
    scripts: dict[str, str] = {}

    def script(path: str) -> str:
        if path not in scripts:
            scripts[path] = fetch(path)
        return scripts[path]

    say(f"[VERIFY] pret/pokeemerald via gh api: flags.h {len(flags_h)} defines, vars.h {len(vars_h)}, opponents.h "
        f"{len(opponents)}, event_objects.h {len(objects)}, metatile_labels.h {len(metatiles)}")
    checked = {"flags": 0, "vars": 0, "trainers": 0, "setters": 0, "levels": 0, "looks": 0, "hints": 0}
    for milestone in data["milestones"]:
        mid, done = milestone["id"], milestone["done"]
        for name, number in done["flags"].items():
            full = f"FLAG_{name}"
            ours = evaluate(full, flags_h) if full in flags_h else None
            checked["flags"] += 1
            if ours != number:
                problems.append(f"{mid}: {full}: ours {number}, pret {ours}")
            setter = re.search(rf"setflag {full}\b", script(milestone["decomp"][name]))
            checked["setters"] += 1
            if not setter:
                problems.append(f"{mid}: {full} is not set (`setflag`) in {milestone['decomp'][name]}")
        for name, info in done["variables"].items():
            full = f"VAR_{name}"
            ours = evaluate(full, vars_h) if full in vars_h else None
            checked["vars"] += 1
            if ours != info["number"]:
                problems.append(f"{mid}: {full}: ours {info['number']:#x}, pret {ours if ours is None else hex(ours)}")
            text = script(milestone["decomp"][name])
            values = [int(v, 0) for v in re.findall(rf"setvar {full}, (\w+)", text) if re.fullmatch(r"0x[0-9A-Fa-f]+|\d+", v)]
            checked["setters"] += 1
            if info["at_least"] not in values:
                problems.append(f"{mid}: {full} is never set to {info['at_least']} in {milestone['decomp'][name]} "
                                f"(setvar values there: {sorted(set(values))})")
        for name, flag in done["trainers"].items():
            setter = re.search(rf"trainerbattle\w* TRAINER_{name}\b", script(milestone["decomp"][name]))
            checked["setters"] += 1
            if not setter:
                problems.append(f"{mid}: TRAINER_{name} is not fought in {milestone['decomp'][name]}")
        fight = milestone.get("fight") or {}
        for name, levels in (fight.get("per_trainer") or {}).items():
            full = f"TRAINER_{name}"
            tid = evaluate(full, opponents) if full in opponents else None
            checked["trainers"] += 1
            if tid != data["trainers"][name]["id"]:
                problems.append(f"trainers: {full}: ours {data['trainers'][name]['id']}, pret {tid}")
            block = re.search(rf"\[{full}\]\s*=\s*\{{(.*?)\n    \}},", trainers_h, re.S)
            label = re.search(r"\.party = \w+\((\w+)\)", block.group(1)).group(1) if block else None
            pret = party_levels(parties, label) if label else []
            checked["levels"] += 1
            if pret != levels:
                problems.append(f"fight: {full} levels: ours {levels}, pret {pret} ({label})")
    for name, look in data["looks"].items():
        checked["looks"] += 1
        if "gfx" in look:
            names = [n.strip() for n in look["decomp"].split(",")]
            pret = [evaluate(n, objects) if n in objects else None for n in names]
            if pret != look["gfx"]:
                problems.append(f"looks: {name}: ours gfx {look['gfx']}, pret {pret} ({look['decomp']})")
        elif name == "clock":
            # the wall clock's metatile is NOT the ROM layout's (both bedrooms are decorated on load by
            # `SecretBase_EventScript_InitDecorations`, which `setmetatile`s the live grid the eyes read): it is MEASURED
            # live per house (`looks.clock.measured`); the decomp checks WHERE the clock is: the same bg event in both
            positions = clock_positions()
            measured = {m["map"]: (m["x"], m["y"], m["metatile"]) for m in look.get("measured", [])}
            for house, (x, y) in sorted(positions.items()):
                const = GENDERED_MAPS["player_house_2f"]["BOY" if "Brendans" in house else "GIRL"]
                seen = measured.get(const)
                if seen is None or seen[:2] != (x, y) or seen[2] not in look["metatile"]:
                    problems.append(f"looks: clock: {house}'s WallClock bg event is at {(x, y)}; measured there: {seen}")
        else:
            label = look["decomp"]
            pret = evaluate(label, metatiles) if label in metatiles else None
            if [pret] != look["metatile"]:
                problems.append(f"looks: {name}: ours metatile {[hex(v) for v in look['metatile']]}, pret {pret} ({label})")
    def said_in(path: str) -> str:
        text = re.sub(r'"\s*\n\s*\.string\s*"', "", script(path))
        return text.replace("\\n", " ").replace("\\l", " ").replace("\\p", " ")

    checked["told"] = 0
    for milestone in data["milestones"]:
        hint = milestone["hint"]
        if hint.get("words") and hint.get("file"):
            checked["hints"] += 1
            if hint["words"] not in said_in(hint["file"]):
                problems.append(f"{milestone['id']}: hint words {hint['words']!r} are not in {hint['file']}")
        # (build step 5.1) every STEP's own words (`told`): in the script the step names, else the milestone hint's
        for step in milestone["steps"]:
            if not step.get("told"):
                continue
            path = step.get("file") or hint.get("file")
            checked["told"] += 1
            if not path or step["told"] not in said_in(path):
                problems.append(f"{milestone['id']}: the {step['do']} step's words {step['told']!r} are not in {path}")
    say(f"[VERIFY] checked: {checked['flags']} flag numbers, {checked['vars']} var numbers, {checked['setters']} proofs set by "
        f"their scripts, {checked['trainers']} trainer ids, {checked['levels']} party level lists, {checked['looks']} looks, "
        f"{checked['hints']} hint words in their scripts, {checked['told']} steps' own words in their scripts")
    return problems


def clock_positions() -> dict[str, tuple[int, int]]:
    """Where each bedroom's wall clock is: its `*_EventScript_WallClock` bg event (`data/maps/<house>/map.json`)."""
    out = {}
    for house in ("LittlerootTown_BrendansHouse_2F", "LittlerootTown_MaysHouse_2F"):
        meta = json.loads(fetch(f"data/maps/{house}/map.json"))
        clock = next((e for e in meta["bg_events"] if str(e.get("script", "")).endswith("WallClock")), None)
        if clock is not None:
            out[house] = (int(clock["x"]), int(clock["y"]))
    return out


#: TEST SIDE ONLY (the graders' second path, never the AI's knowledge: a person does not know a save's flags): the
#: FLAG_ITEM_* flag of every item ball on the maps of badge 1, so `gates/live_step5.py` can prove an item was PICKED UP by the
#: game's own record (the game sets the ball's flag when it is taken: `data/scripts/obtain_item.inc` Std_FindItem
#: `removeobject` + the object's hide flag).
ITEM_FLAGS_OUT = REPO / "ai_player" / "gates" / "fixtures" / "item_flags.json"
ITEM_MAPS = ("LittlerootTown", "Route101", "OldaleTown", "Route103", "Route102", "PetalburgCity", "Route104",
             "PetalburgWoods", "RustboroCity")


def item_flags() -> dict:
    flags_h = {**defines(fetch("include/constants/opponents.h")), **defines(fetch("include/constants/flags.h"))}
    out = {}
    for name in ITEM_MAPS:
        meta = json.loads(fetch(f"data/maps/{name}/map.json"))
        for obj in meta.get("object_events", []):
            flag = obj.get("flag", "")
            if obj.get("graphics_id") == "OBJ_EVENT_GFX_ITEM_BALL" and str(flag).startswith("FLAG_ITEM_"):
                out[flag] = {"number": evaluate(flag, flags_h), "map": name, "x": obj["x"], "y": obj["y"],
                             "script": obj.get("script")}
    return {"provenance": f"{REPOSITORY} data/maps/<map>/map.json item balls and include/constants/flags.h",
            "maps": list(ITEM_MAPS), "flags": dict(sorted(out.items()))}


WILD_OUT = REPO / "ai_player" / "knowledge" / "wild_species.json"
WILD_SOURCE = "src/data/wild_encounters.json"


def wild_species() -> dict:
    """(personality.py's FAVOURITE: "a random wild-catchable Emerald species", design draft §2.3) The species a person can
    meet in the wild in Emerald: every species of every map's land, water, rock-smash and fishing table of the decomp's
    `gWildMonHeaders` group (no maps, rates or levels are kept: only WHICH species are wild), named as `species.json` names
    them."""
    raw = json.loads(fetch(WILD_SOURCE))
    names = {re.sub(r"[^A-Z0-9]", "", n.upper()): n
             for n in json.loads((REPO / "ai_player" / "knowledge" / "species.json").read_text(encoding="utf-8"))["species"]}
    found: set[str] = set()
    for group in raw["wild_encounter_groups"]:
        if group.get("label") != "gWildMonHeaders":
            continue
        for encounter in group.get("encounters", []):
            for table in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                for mon in (encounter.get(table) or {}).get("mons", []):
                    key = re.sub(r"[^A-Z0-9]", "", mon["species"].removeprefix("SPECIES_").replace("_F", "F").replace("_M", "M"))
                    found.add(names.get(key, mon["species"]))
    blob = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/contents/{WILD_SOURCE}", "--jq", ".sha"], capture_output=True,
                          timeout=120).stdout.decode().strip()
    return {"provenance": {"source": f"{REPOSITORY} {WILD_SOURCE}", "git_blob_sha": blob,
                           "rule": "the species only (which can be met in the wild); no map, rate or level is kept"},
            "species": sorted(found)}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wild", action="store_true", help="(gh api) write ai_player/knowledge/wild_species.json")
    parser.add_argument("--items", action="store_true", help="(gh api, TEST SIDE) write gates/fixtures/item_flags.json")
    parser.add_argument("--check", action="store_true", help="exit 1 if the written file differs from a fresh extraction")
    parser.add_argument("--verify", action="store_true", help="check every fact against pret/pokeemerald (gh api)")
    parser.add_argument("--plant", action="store_true", help="with --verify: three facts changed in memory must be found")
    parser.add_argument("--evidence", type=Path, help="with --verify: also write the report here")
    args = parser.parse_args()
    if args.items:
        data = item_flags()
        ITEM_FLAGS_OUT.write_text(render(data), encoding="utf-8")
        print(f"[MILESTONES] wrote {ITEM_FLAGS_OUT.relative_to(REPO)}: {len(data['flags'])} item balls on {len(ITEM_MAPS)} maps")
        return 0
    if args.wild:
        data = wild_species()
        WILD_OUT.write_text(render(data), encoding="utf-8")
        print(f"[MILESTONES] wrote {WILD_OUT.relative_to(REPO)}: {len(data['species'])} wild species "
              f"({data['provenance']['source']} blob {data['provenance']['git_blob_sha']})")
        return 0
    fresh = render(extract())
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        same = current == fresh
        print(f"[MILESTONES] {OUT.relative_to(REPO)} {'is up to date' if same else 'DIFFERS from a fresh extraction'}")
        return 0 if same else 1
    if not args.verify:
        OUT.write_text(fresh, encoding="utf-8")
        data = json.loads(fresh)
        print(f"[MILESTONES] wrote {OUT.relative_to(REPO)}: {len(data['milestones'])} milestones in "
              f"{len({m['chapter'] for m in data['milestones']})} chapters, {len(data['looks'])} looks, "
              f"{len(data['trainers'])} trainers")
        return 0
    lines: list[str] = []

    def say(line: str) -> None:
        print(line, flush=True)
        lines.append(line)

    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from ai_player.gates.provenance import provenance

    say(f"[VERIFY] code: {provenance(REPO)}")
    data = json.loads(OUT.read_text(encoding="utf-8"))
    say(f"[VERIFY] {OUT.relative_to(REPO)}: {len(data['milestones'])} milestones; teacher "
        f"{data['provenance']['teacher'][0]['file']} sha256 {data['provenance']['teacher'][0]['sha256']}")
    if args.plant:
        clock = next(m for m in data["milestones"] if m["id"] == "ch1_clock")
        clock["done"]["flags"]["SET_WALL_CLOCK"] = 0x52
        rival = next(m for m in data["milestones"] if m["id"] == "ch1_rival_route103")
        rival["fight"]["per_trainer"]["MAY_ROUTE_103_MUDKIP"] = [6]
        data["looks"]["nurse"]["gfx"] = [57]
    try:
        problems = verify(data, say)
    except Exception as error:  # noqa: BLE001
        say(f"[VERIFY] could not fetch or read the decomp: {type(error).__name__}: {error}")
        return 2
    for problem in problems:
        say(f"[VERIFY] MISMATCH {problem}")
    verdict = "PASS" if not problems else "FAIL"
    if args.plant:
        planted = {"ch1_clock: FLAG_SET_WALL_CLOCK: ours 82, pret 81",
                   "fight: TRAINER_MAY_ROUTE_103_MUDKIP levels: ours [6], pret [5] (sParty_MayRoute103Mudkip)",
                   "looks: nurse: ours gfx [57], pret [58] (OBJ_EVENT_GFX_NURSE)"}
        verdict = ("PASS (the plants were found, and nothing else)" if set(problems) == planted
                   else f"FAIL (found {sorted(problems)})")
    say(f"[VERIFY] OVERALL {verdict}")
    if args.evidence is not None:
        from ai_player.gates.provenance import keep_earlier

        keep_earlier(args.evidence)
        args.evidence.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if verdict.startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
