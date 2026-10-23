#!/usr/bin/env python3
"""KB2 slice 2, STAGE 2b (spec S3-4): events.json, the story-state changes and the gates a seasoned player knows.

    py -3.12 ai_player/gates/extract_events.py               # writes ai_player/knowledge/world/events.json (PINNED clone)
    py -3.12 ai_player/gates/extract_events.py --check       # re-extracts into a temp folder; exit 1 if the file differs
    py -3.12 ai_player/gates/extract_events.py --decomp DIR  # a clone elsewhere (its HEAD must still equal tools/decomp.pin)

INTENT (USER RULING 40, a SEASONED player): a person who has played Emerald knows what a story step changes (a person
appears, a way opens, a battle happens) and which ways stay shut until something is done. This file lists, per script
label, the persistent changes the label makes IN ORDER, how the label is triggered, and the candidate gates, with every
condition the AI may read in WORDS and every flag/var name only under a `dev` dict (R-4). Spec:
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-22-BUILD-SPEC-S3-4-slice2.md` (R-1..R-7, the `events.json` section).

THE BINDING PRINCIPLE (06 2026-10-22, learned over stage 2a's four rounds): a value for the AI is written ONLY from a
pattern an independent whole-decomp scan re-checks on every record, or from a small CITED hand table (path:line + token,
checked by check_cites at build time and again by verify_world.py). Anything else is null / conditional and is listed in
`_notes`. So:
  * THE GRAPH IS STAGE 2a's: the script sources (the `.include` closure of data/event_scripts.s, mystery-gift files out),
    the label parser, the edge builder, the roots and the reachability walk are IMPORTED from extract_items.py (never
    copied), so the two files cannot disagree on what is reachable or who owns a label (R-2).
  * labels[]: every REACHABLE label whose body holds a listed op on persistent state. A change is `conditional: false`
    only when every line before it in its label is on the SAFE list (a command that always runs on to the next line)
    or a call into a callee that provably always returns (callee_returns). Any other earlier line (a goto_if, a case, a
    special, a battle, a warp, a call that may end the script) makes it `conditional: true`, and the lines that make it
    so are listed in dev.after. WHY: a special can start a battle you lose; a call can end the script; nothing here
    reads C to rule that out, so the change is never stated as certain.
  * `effect` words come ONLY from EFFECT_WORDS (op-keyed templates, each cited to its ScrCmd line); a flag or var change
    has no words (its meaning is not written from its NAME). trainerbattle / settrainerflag carry the trainer joined to
    slice 1's trainers.json; warp carries the map joined to maps.json. The `register_matchcall` macro (a hidden
    `special SetMatchCallRegisteredFlag`, a saved flag) is a `special` change with its trainer and words cited to the
    macro and the special's C body (fix round 1, item 4; check_matchcall refuses a trainer that heads no rematch row).
  * PERSISTENT ONLY: a write to a temp flag/var, a special (not saved) flag or a special 0x80xx var (VAR_RESULT
    included) is dropped and counted in `excluded`, classified by numeric id from flags.h / vars.h (PERSIST_RANGES,
    cited), so an alias (FLAG_TEMP_SKIP_GABBY_INTERVIEW = FLAG_TEMP_1) is classified by what it IS, not how it is spelt.
  * R-3: `copyvar X, <literal>` reads var id <literal> through GetVarPointer, which returns NULL below VARS_START
    (src/event_data.c:166-167): the value is "unknown (vanilla copyvar bug, scrcmd.c:371)", never the literal.
  * gates[]: CANDIDATES found by two re-checkable patterns (steer: a coord trigger whose script moves the player and
    writes no persistent state, so it fires again; locked: a goto_if on persistent state whose branch ends without a
    warp while the label's own way on warps). Their `when` words come ONLY from GATE_WORDS, a cited hand table keyed by
    label; every other candidate has `when: null` and is listed in `_gates_when_null`. Words are never generated from
    flag names.
  * dead: labels with a listed op that no map.json event, map script, script reference or C line reaches, and op
    lines that sit after a never-continuing command in their own label: never in an AI-facing record.

THE GUARDS (each refuses with exit 2 naming what it found):
  extract_items' own: check_sources, vanilla_lines, parse_labels, check_map_scripts, closure (imported, unchanged)
  check_cites           a GATE_WORDS / EFFECT_WORDS / PERSIST_RANGES / COPYVAR_BUG cite whose line lacks its token
  check_gate_table      a GATE_WORDS label that is no candidate, or a tabled label with more than one candidate
  check_joins           a trainer the scripts battle / flag that trainers.json lacks
  check_matchcall       a register_matchcall trainer that heads no gRematchTable row (no flag would be set);
                        rematch_first refuses when the table cannot be read at all
  ei.check_maps_json    maps.json from another decomp commit (warp map names would be stale)
  refuse_all            R-4 (flag/var key or name outside `dev`), R-5 (a dev name flags.h / vars.h does not #define),
                        R-6 (a route key), R-7 (a withheld field), run again at the one door to disk
verify_world.py re-derives this file by its own reading and never imports this module.
NOT IN THIS STAGE: the chapter packs (tools/make_chapter_pack.py) do not read this file yet; nothing in ai_player's play
code reads it until a loader and a KNOWLEDGE_FIELDS classification of world/ exist.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from extract_seasoned import Decomp, write_json  # noqa: E402  (slice 1's decomp reader)
import extract_world as ew  # noqa: E402  (the pin, the W1 / W6 scans, battle_trainer)
import extract_items as ei  # noqa: E402  (stage 2a: the label parser, the edge builder, the roots, the path walk)

Refused = ew.Refused
OUT_DEFAULT = ew.OUT_DEFAULT
OUT_NAME = "events.json"
MADE_BY = "ai_player/gates/extract_events.py"
#: the edge kinds that are control flow (a text, movement or table mention is not)
CTRL = ("goto", "call", "goto_if", "call_if", "case", "fall")
#: the warp commands (asm/macros/event.inc `.macro warp*`), each cited to the line of its ScrCmd that sets the
#: destination from the script's own map operand. warphole is listed without a cite: with MAP_UNDEFINED it falls to the
#: map setholewarp chose (src/scrcmd.c:782-793), so no words are written for it.
WARP_CMDS = {
    "warp": ("src/scrcmd.c:748", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
    "warpsilent": ("src/scrcmd.c:762", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
    "warpdoor": ("src/scrcmd.c:776", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
    "warphole": None,
    "warpteleport": ("src/scrcmd.c:808", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
    "warpmossdeepgym": ("src/scrcmd.c:822", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
    "warpspinenter": ("src/scrcmd.c:2250", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
    "warpwhitefade": ("src/scrcmd.c:2304", "SetWarpDestination(mapGroup, mapNum, warpId, x, y);"),
}
#: script mnemonic -> the spec's op name. setorcopyvar is a set (literal) or a copy (var); specialvar runs a special.
#: copyvar is listed although the spec's op list omits it: R-3 names its value rule, and leaving a saved-var write out
#: would make `changes` claim less than the label does.
OPS = {"setflag": "setflag", "clearflag": "clearflag", "setvar": "setvar", "addvar": "addvar", "subvar": "subvar",
       "copyvar": "copyvar", "setorcopyvar": "setorcopyvar", "settrainerflag": "settrainerflag",
       "cleartrainerflag": "cleartrainerflag", "special": "special", "specialvar": "special"}
OPS.update({w: "warp" for w in WARP_CMDS})
#: STAGE 2b FIX ROUND 1, item 4: `register_matchcall TRAINER_X` is a MACRO that hides a saved-state write. Its body
#: (asm/macros/event.inc:1968-1972) runs `special SetMatchCallRegisteredFlag`, whose C body sets the saved flag
#: TRAINER_REGISTERED_FLAGS_START + the trainer's gRematchTable row (src/pokenav_match_call_data.c:1156-1161) when the
#: trainer is the FIRST id of a row (GetRematchIdxByTrainerIdx, :740-749; -1, no write, otherwise). So each line is a
#: change: op `special` (the special the macro runs), with the trainer joined to trainers.json and cited words. A line
#: whose trainer heads no row would write nothing: check_matchcall REFUSES it (none at the pin: 76 lines, 64 trainers,
#: every one a first id) rather than list a change that does not happen.
MATCHCALL_MACRO = "register_matchcall"
MATCHCALL_SPECIAL = "SetMatchCallRegisteredFlag"
OPS[MATCHCALL_MACRO] = "special"
#: where the rematch rows are read from, and the line that opens the table (cited, so a moved table refuses)
REMATCH_FILE = "src/battle_setup.c"
REMATCH_RE = re.compile(r"\[(REMATCH_\w+)\]\s*=\s*REMATCH\((TRAINER_\w+)\s*,")
#: the raw `trainerbattle` types whose named trainer is a placeholder: the Battle Pyramid / Trainer Hill opponent is set
#: at runtime (the scripts pass TRAINER_PHILLIP with BattleFacility_TrainerBattle_PlaceholderText)
PLACEHOLDER_BATTLES = {"TRAINER_BATTLE_PYRAMID": ("include/constants/battle_setup.h:13", "TRAINER_BATTLE_PYRAMID"),
                       "TRAINER_BATTLE_HILL": ("include/constants/battle_setup.h:16", "TRAINER_BATTLE_HILL")}
#: commands that ALWAYS run on to the next line: no jump, no script stop, no battle, no warp, no C special. A line not
#: on this list (or a `call` whose callee may not return) before a change makes the change conditional. The list is a
#: whitelist on purpose: an unknown command makes a change conditional, never certain. `msgbox` is a callstd of a
#: std script that returns; the give/check commands set VAR_RESULT and continue (the result is read by a LATER
#: branch, which is itself not on the list).
SAFE = frozenset((
    "lock", "lockall", "faceplayer", "release", "releaseall", "msgbox", "message", "messageautoscroll",
    "messageinstant", "waitmessage", "closemessage", "waitbuttonpress", "applymovement", "applywaitmovement",
    "waitmovement", "setflag", "clearflag", "setvar", "addvar", "subvar", "copyvar", "setorcopyvar", "settrainerflag",
    "cleartrainerflag", "playse", "waitse", "playfanfare", "waitfanfare", "playbgm", "savebgm", "fadedefaultbgm",
    "fadenewbgm", "fadeoutbgm", "fadeinbgm", "playmoncry", "waitmoncry", "delay", "setobjectxyperm", "setobjectxy",
    "setobjectmovementtype", "copyobjectxytoperm", "removeobject", "addobject", "showobjectat", "hideobjectat",
    "turnobject", "setobjectsubpriority", "resetobjectsubpriority", "fadescreen", "fadescreenspeed",
    "fadescreenswapbuffers", "setmetatile", "opendoor", "closedoor", "waitdooranim", "checkplayergender", "random",
    "checkitem", "checkitemspace", "checkpcitem", "checkdecor", "checkdecorspace", "checkmoney", "checkcoins",
    "getpartysize", "switch", "yesnobox", "multichoice", "multichoicedefault", "multichoicegrid", "giveitem",
    "givedecoration", "givemon", "giveegg", "additem", "adddecoration", "removeitem", "waitstate", "incrementgamestat",
    "setrespawn", "setweather", "doweather", "waitfieldeffect", "setfieldeffectargument", "setwildbattle",
    "showmoneybox", "hidemoneybox", "updatemoneybox", "removemoney", "addmoney", "showcoinsbox", "hidecoinsbox",
    "setescapewarp", "setdynamicwarp", "setwarp", "setholewarp", "setdivewarp", "getplayerxy", "textcolor",
    "signmsg", "normalmsg", "hidemonpic", "nop", "nop1"))
SAFE_PREFIX = ("buffer",)
#: the control lines a callee may hold and still return to its caller (a `goto` within the callee is followed: the
#: closure holds its target, and an `end` anywhere in the closure makes the callee unsafe)
CALLEE_FLOW = ("return", "goto", "call", "case", "switch")
#: PERSISTENT ONLY: id ranges whose writes are not saved story state, classified by NUMERIC id (aliases resolved):
#: (what, namespace, low name, high name, *cites). The write is dropped and counted in `excluded`.
PERSIST_RANGES = [
    ("temp flags (cleared on every map entry)", "flag", "TEMP_FLAGS_START", "TEMP_FLAGS_END",
     ("include/constants/flags.h:11", "#define TEMP_FLAGS_START 0x0"),
     ("include/constants/flags.h:43", "#define TEMP_FLAGS_END   FLAG_TEMP_1F"),
     ("src/overworld.c:798", "ClearTempFieldEventData();")),
    ("special flags (not saved)", "flag", "SPECIAL_FLAGS_START", "SPECIAL_FLAGS_END",
     ("include/constants/flags.h:1644", "#define SPECIAL_FLAGS_START"),
     ("include/constants/flags.h:1651", "#define SPECIAL_FLAGS_END")),
    ("temp vars (cleared on every map entry)", "var", "TEMP_VARS_START", "TEMP_VARS_END",
     ("include/constants/vars.h:8", "#define TEMP_VARS_START"),
     ("include/constants/vars.h:25", "#define TEMP_VARS_END")),
    ("special vars (scratch registers, the script result included; not saved)", "var", "SPECIAL_VARS_START",
     "SPECIAL_VARS_END",
     ("include/constants/vars.h:280", "#define SPECIAL_VARS_START"),
     ("include/constants/vars.h:306", "#define SPECIAL_VARS_END"),
     ("src/event_data.c:171", "return gSpecialVars[id - SPECIAL_VARS_START];")),
]
#: a flag id past every flag the save holds (and outside the special range) is no save flag: `setflag VAR_0x8005` sets
#: flag 0x8005 itself (data/scripts/secret_base.inc:276 says so: ScrCmd_setflag does not VarGet)
FLAGS_COUNT_CITE = ("include/constants/flags.h:1641", "#define FLAGS_COUNT (DAILY_FLAGS_END + 1)")
#: R-3: vanilla `copyvar X, <literal>` reads var id <literal>; GetVarPointer returns NULL below VARS_START
COPYVAR_BUG = "unknown (vanilla copyvar bug, scrcmd.c:371)"
COPYVAR_CITES = (("src/scrcmd.c:371", "*ptr = *GetVarPointer(ScriptReadHalfword(ctx));"),
                 ("src/event_data.c:166", "if (id < VARS_START)"),
                 ("src/event_data.c:167", "return NULL;"))
#: `effect` words, keyed by op (never by a flag or var name): a template filled from a JOIN (trainers.json, maps.json),
#: with the ScrCmd line that makes it true. A warp's words come from the map operand; WARP_CMDS cites each warp command.
EFFECT_WORDS = {
    "settrainerflag": ("{name} now counts as beaten", ("src/scrcmd.c:1858", "SetTrainerFlag(index);")),
    "cleartrainerflag": ("{name} no longer counts as beaten", ("src/scrcmd.c:1866", "ClearTrainerFlag(index);")),
    "warp": ("you are moved to {map}",),
    # keyed by the MACRO (it is a `special` op whose words come from the macro's own doc line, not from a name)
    MATCHCALL_MACRO: ("{name} is registered in your Match Call",
                      ("asm/macros/event.inc:1967", "Registers the specified trainer in Match Call"),
                      ("asm/macros/event.inc:1968", ".macro register_matchcall trainer:req"),
                      ("asm/macros/event.inc:1970", "special SetMatchCallRegisteredFlag"),
                      ("src/pokenav_match_call_data.c:1158",
                       "int index = GetRematchIdxByTrainerIdx(gSpecialVar_0x8004);"),
                      ("src/pokenav_match_call_data.c:1160", "FlagSet(TRAINER_REGISTERED_FLAGS_START + index);"),
                      ("src/pokenav_match_call_data.c:746",
                       "if (gRematchTable[rematchIdx].trainerIds[0] == trainerIdx)"),
                      ("src/battle_setup.c:260", "const struct RematchTrainer gRematchTable[REMATCH_TABLE_ENTRIES] =")),
}
#: gates[] WORDS: the HAND table, keyed by the candidate's label (spec: "a small HAND table keyed by label, cited, like
#: slice 1's campaign_skeleton.json"). Every cite (path:line, token) is checked by check_cites at build time and by
#: verify_world.py at verify time. A candidate without an entry has `when: null` and is listed in _gates_when_null.
_PETALBURG_STATE_CITES = (
    ("data/maps/PetalburgCity_Gym/scripts.inc:90", "setvar VAR_PETALBURG_GYM_STATE, 2"),
    ("data/maps/RustboroCity_Gym/scripts.inc:21", "addvar VAR_PETALBURG_GYM_STATE, 1"),
    ("data/maps/DewfordTown_Gym/scripts.inc:152", "addvar VAR_PETALBURG_GYM_STATE, 1"),
    ("data/maps/MauvilleCity_Gym/scripts.inc:95", "addvar VAR_PETALBURG_GYM_STATE, 1"),
    ("data/maps/LavaridgeTown_Gym_1F/scripts.inc:63", "addvar VAR_PETALBURG_GYM_STATE, 1"))


def _door(room, line, trainer, name):
    return ("in Petalburg Gym the %s door stays locked until you beat the Gym Trainer %s" % (room, name),
            ("data/maps/PetalburgCity_Gym/scripts.inc:%d" % line, "goto_if_not_defeated %s," % trainer),
            ("data/maps/PetalburgCity_Gym/scripts.inc:737", "msgbox PetalburgCity_Gym_Text_DoorAppearsLocked"))


_STEER = ("until you have visited your father in the Petalburg Gym and agreed to go with Wally, crossing this spot "
          "makes the boy by the Gym stop you and walk you to the Gym",)
_ROUTE101 = ("while Professor Birch is being chased on Route 101 you cannot leave the route: you are stepped back "
             "until you have picked a Pokemon from his bag to save him",
             ("data/maps/Route101/scripts.inc:39", "setvar VAR_ROUTE101_STATE, 2"),
             ("data/maps/Route101/scripts.inc:223", "special ChooseStarter"),
             ("data/maps/Route101/scripts.inc:231", "setvar VAR_ROUTE101_STATE, 3"))
GATE_WORDS = {
    "OldaleTown_EventScript_BlockedPath": (
        "Oldale Town's west exit is blocked: the man sketching footprints steps you back until Professor Birch has "
        "given you the Pokedex",
        ("data/maps/OldaleTown/map.json:125", '"var": "VAR_OLDALE_TOWN_STATE"'),
        ("data/maps/OldaleTown/map.json:126", '"var_value": "0"'),
        ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:501",
         "call LittlerootTown_ProfessorBirchsLab_EventScript_ReceivePokedex"),
        ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:511", "setvar VAR_OLDALE_TOWN_STATE, 1"),
        ("data/maps/OldaleTown/scripts.inc:15", "setvar VAR_OLDALE_TOWN_STATE, 1")),
    "PetalburgCity_EventScript_ShowGymToPlayer0": _STEER + (
        ("data/maps/PetalburgCity/map.json:201", '"var": "VAR_PETALBURG_CITY_STATE"'),
        ("data/maps/PetalburgCity_Gym/scripts.inc:183", "setvar VAR_PETALBURG_CITY_STATE, 2")),
    "PetalburgCity_EventScript_ShowGymToPlayer1": _STEER + (
        ("data/maps/PetalburgCity/map.json:210", '"var": "VAR_PETALBURG_CITY_STATE"'),
        ("data/maps/PetalburgCity_Gym/scripts.inc:183", "setvar VAR_PETALBURG_CITY_STATE, 2")),
    "PetalburgCity_EventScript_ShowGymToPlayer2": _STEER + (
        ("data/maps/PetalburgCity/map.json:219", '"var": "VAR_PETALBURG_CITY_STATE"'),
        ("data/maps/PetalburgCity_Gym/scripts.inc:183", "setvar VAR_PETALBURG_CITY_STATE, 2")),
    "PetalburgCity_EventScript_ShowGymToPlayer3": _STEER + (
        ("data/maps/PetalburgCity/map.json:228", '"var": "VAR_PETALBURG_CITY_STATE"'),
        ("data/maps/PetalburgCity_Gym/scripts.inc:183", "setvar VAR_PETALBURG_CITY_STATE, 2")),
    "Route101_EventScript_PreventExitSouth": _ROUTE101 + (
        ("data/maps/Route101/map.json:134", '"var": "VAR_ROUTE101_STATE"'),),
    "Route101_EventScript_PreventExitWest": _ROUTE101 + (
        ("data/maps/Route101/map.json:152", '"var": "VAR_ROUTE101_STATE"'),),
    "Route101_EventScript_PreventExitNorth": _ROUTE101 + (
        ("data/maps/Route101/map.json:188", '"var": "VAR_ROUTE101_STATE"'),),
    "PetalburgCity_Gym_EventScript_SpeedRoomDoor": (
        "in Petalburg Gym the Speed Room door stays locked until you have the first four badges (the Rustboro, "
        "Dewford, Mauville and Lavaridge Gyms each count one, after your first talk with your father here)",
        ("data/maps/PetalburgCity_Gym/scripts.inc:716", "goto_if_lt VAR_PETALBURG_GYM_STATE, 6,"),
        *_PETALBURG_STATE_CITES),
    "PetalburgCity_Gym_EventScript_AccuracyRoomDoor": (
        "in Petalburg Gym the Accuracy Room door stays locked until you have the first four badges (the Rustboro, "
        "Dewford, Mauville and Lavaridge Gyms each count one, after your first talk with your father here)",
        ("data/maps/PetalburgCity_Gym/scripts.inc:744", "goto_if_lt VAR_PETALBURG_GYM_STATE, 6,"),
        *_PETALBURG_STATE_CITES),
    "PetalburgCity_Gym_EventScript_ConfusionRoomDoor": _door("Confusion Room", 754, "TRAINER_RANDALL", "Randall"),
    "PetalburgCity_Gym_EventScript_LeftDefenseRoomDoor": _door("left Defense Room", 764, "TRAINER_RANDALL", "Randall"),
    "PetalburgCity_Gym_EventScript_RightDefenseRoomDoor": _door("right Defense Room", 774, "TRAINER_MARY", "Mary"),
    "PetalburgCity_Gym_EventScript_RecoveryRoomDoor": _door("Recovery Room", 784, "TRAINER_MARY", "Mary"),
    "PetalburgCity_Gym_EventScript_LeftStrengthRoomDoor": _door("left Strength Room", 794, "TRAINER_PARKER", "Parker"),
    "PetalburgCity_Gym_EventScript_RightStrengthRoomDoor": _door("right Strength Room", 804, "TRAINER_ALEXIA",
                                                                 "Alexia"),
    "PetalburgCity_Gym_EventScript_LeftOHKORoomDoor": _door("left One-Hit KO Room", 814, "TRAINER_ALEXIA", "Alexia"),
    "PetalburgCity_Gym_EventScript_RightOHKORoomDoor": _door("right One-Hit KO Room", 824, "TRAINER_GEORGE", "George"),
    "PetalburgCity_Gym_EventScript_LeftGymLeadersRoomDoor": _door("left Gym Leader's Room", 834, "TRAINER_JODY",
                                                                  "Jody"),
    "PetalburgCity_Gym_EventScript_RightGymLeadersRoomDoor": _door("right Gym Leader's Room", 844, "TRAINER_BERKE",
                                                                   "Berke"),
}
#: the player's object in a movement command (include/constants/event_objects.h: OBJ_EVENT_ID_PLAYER; the maps'
#: LOCALID_PLAYER alias)
PLAYER_IDS = ("LOCALID_PLAYER", "OBJ_EVENT_ID_PLAYER")
MOVE_CMDS = ("applymovement", "applywaitmovement")
#: commands whose presence in a candidate's closure means it is not a pure steer/lock (it moves the story on)
STORY_CMDS = ("trainerbattle", "givemon", "giveegg", "giveitem", "givedecoration", "removeobject", "special",
              "specialvar")


# ---------------------------------------------------------------- persistence (by numeric id)
class Persist:
    """Classifies a flag/var NAME by its numeric id (ei.name_ids: flags.h / vars.h with their bounds evaluated)."""

    def __init__(self, d):
        self.ids = ei.name_ids(d)
        self.ranges = [(what, ns, self.ids[lo], self.ids[hi]) for what, ns, lo, hi, *_ in PERSIST_RANGES]
        self.flags_count = self.ids["FLAGS_COUNT"]

    def dropped(self, ns, name):
        """None when `name` is saved story state of namespace ns ('flag'/'var'); else why it is dropped. A name with no
        id (not #defined) is NOT dropped here: R-5's check_dev_names refuses it at the door."""
        v = self.ids.get(name)
        if v is None:
            return None
        for what, rns, lo, hi in self.ranges:
            if rns == ns and lo <= v <= hi:
                return what
        if ns == "flag" and v >= self.flags_count:
            return "not a save flag (id past FLAGS_COUNT)"
        return None


def set_aliases(d, files):
    """{alias: FLAG_/VAR_ name} of every assembler `.set ALIAS, VAR_x` / `FLAG_x` line in the script files. WHY: a
    write through an alias is a write to the aliased var (data/scripts/berry_blender.inc:1 `.set NUM_OPPONENTS,
    VAR_0x8009` makes `setvar NUM_OPPONENTS, 1` a scratch write); unresolved, it would look like a saved var."""
    out = {}
    for rel in files:
        for m in re.finditer(r"^\s*\.set\s+(\w+)\s*,\s*((?:FLAG|VAR)_\w+)\s*$", d.read(rel), re.M):
            out[m.group(1)] = m.group(2)
    return out


# ---------------------------------------------------------------- the change records
def safe_line(mn):
    return mn in SAFE or mn.startswith(SAFE_PREFIX)


def callee_returns(g, lab, memo):
    """True when the callee `lab` provably runs back to its caller: every line of its control closure is SAFE or a
    return / goto / call / case / switch / goto_if / call_if (no `end`, no special, no battle, no warp). A closure past
    ei.MAX_CLOSURE is not proven."""
    if lab not in memo:
        memo[lab] = False
        if lab in g.labels:
            try:
                cl = ei.closure(g.edges, lab, kinds=CTRL)
            except Refused:
                return False
            ok = True
            for x in cl:
                for _, code in g.labels[x]["body"]:
                    mn, _ = ei.cmd(code)
                    if not (safe_line(mn) or mn in CALLEE_FLOW or re.match(r"(goto|call)_if_\w+$", mn)):
                        ok = False
            memo[lab] = ok
    return memo[lab]


def diverts(g, mn, args, memo):
    """Can this line keep the lines after it in its label from running?"""
    if safe_line(mn):
        return False
    if (mn == "call" or mn.startswith("call_if_")) and args and args[-1] in g.labels:
        return not callee_returns(g, args[-1], memo)
    return True


def live_body(lab):
    """(live lines, dead lines): a line after a never-continuing command (ei.NEVER_CONTINUES) with no label between
    never runs."""
    live, dead, stop = [], [], None
    for ln, code in lab["body"]:
        mn, _ = ei.cmd(code)
        (dead if stop else live).append((ln, code, stop))
        if mn in ei.NEVER_CONTINUES and stop is None:
            stop = (mn, ln)
    return live, dead


def trainer_of(mn, args):
    """(trainer symbol or None, why None)."""
    if args and args[0] in PLACEHOLDER_BATTLES:
        return None, "a facility battle (%s): the opponent is set at runtime; the script names a placeholder" % args[0]
    t = ew.battle_trainer(args) if mn.startswith("trainerbattle") else (args[0] if args else None)
    return t, None if t else "no TRAINER_ operand"


def rematch_first(d):
    """{TRAINER_ symbol: REMATCH_ row} of the FIRST trainer id of every gRematchTable row (REMATCH_FILE): the only
    trainers GetRematchIdxByTrainerIdx finds, so the only ones `register_matchcall` writes a flag for."""
    rows = {t: r for r, t in REMATCH_RE.findall(d.read(REMATCH_FILE))}
    if not rows:
        raise Refused("%s: no gRematchTable row read (the table moved; register_matchcall cannot be judged)"
                      % REMATCH_FILE)
    return rows


def check_matchcall(trainer, firsts, where):
    """GUARD (fix round 1, item 4): a `register_matchcall` line is a change only when its trainer heads a rematch row
    (src/pokenav_match_call_data.c:746, :1159); otherwise SetMatchCallRegisteredFlag writes nothing. Refuse instead of
    listing a change that does not happen."""
    if trainer not in firsts:
        raise Refused("register_matchcall %s at %s: the trainer heads no gRematchTable row, so no flag is set"
                      % (trainer, where))


def change_of(ctx, lab, ln, mn, args):
    """(change record, None) or (None, (excluded what, name)) for one op line."""
    where = ei.ref(lab, ln)
    p = ctx["persist"]
    if mn.startswith("trainerbattle"):
        t, why = trainer_of(mn, args)
        rec = {"op": "trainerbattle", "trainer": t, "name": ctx["names"].get(t) if t else None, "effect": None,
               "dev": {"cmd": mn, "ref": where}}
        if why:
            rec["dev"]["why"] = why
        return rec, None
    op = OPS[mn]
    alias = ctx["alias"]
    if op in ("setflag", "clearflag"):
        x = alias.get(args[0], args[0]) if args else None
        why = p.dropped("flag", x)
        if why:
            return None, (why, x)
        return {"op": op, "effect": None, "dev": {"flags": [x], "ref": where}}, None
    if op in ("setvar", "addvar", "subvar", "setorcopyvar", "copyvar"):
        x = alias.get(args[0], args[0]) if args else None
        why = p.dropped("var", x)
        if why:
            return None, (why, x)
        src = alias.get(args[1], args[1]) if len(args) > 1 else None
        if op == "setorcopyvar":
            op = "copyvar" if src and src.startswith("VAR_") else "setvar"
        dev = {"vars": [x], "ref": where}
        if op == "copyvar":
            if src and re.fullmatch(r"VAR_\w+", src):
                dev["vars"].append(src)
                dev["from"] = src
            else:
                n = ei.as_num(src)
                dev["value"] = COPYVAR_BUG if n is not None and n < p.ids["VARS_START"] else \
                    "unknown (copied from var id %s)" % src
        else:
            dev["value"] = src
        return {"op": op, "effect": None, "dev": dev}, None
    if op in ("settrainerflag", "cleartrainerflag"):
        t, _ = trainer_of(mn, args)
        name = ctx["names"].get(t)
        return {"op": op, "trainer": t, "name": name,
                "effect": EFFECT_WORDS[op][0].format(name=name) if name else None, "dev": {"ref": where}}, None
    if mn == MATCHCALL_MACRO:
        t = args[0] if args else None
        check_matchcall(t, ctx["rematch_first"], where)
        name = ctx["names"].get(t)
        return {"op": "special", "name": MATCHCALL_SPECIAL, "trainer": t,
                "effect": EFFECT_WORDS[MATCHCALL_MACRO][0].format(name=name) if name else None,
                "dev": {"cmd": mn, "ref": where}}, None
    if op == "special":
        fn = args[0] if mn == "special" else (args[1] if len(args) > 1 else None)
        dev = {"cmd": mn, "ref": where}
        if mn == "specialvar" and args and not p.dropped("var", args[0]):
            dev["vars"] = [args[0]]
        return {"op": "special", "name": fn, "effect": None, "dev": dev}, None
    # warp: map operand, warp id when given (1 or 3 operands after the map; 2 = x, y, which R-6 never copies)
    m = args[0] if args else None
    rest = args[1:]
    wid = rest[0] if len(rest) in (1, 3) else None
    mapname = ctx["map_names"].get(m)
    words = EFFECT_WORDS["warp"][0].format(map=mapname) if mapname and WARP_CMDS.get(mn) else None
    return {"op": "warp", "map": m, "warp_id": int(wid) if wid and wid.isdigit() else wid, "effect": words,
            "dev": {"cmd": mn, "ref": where}}, None


# ---------------------------------------------------------------- triggers (the DIRECT ways into a label)
def mapscript_types(g):
    """{(<map>_MapScripts label, line): (MAP_SCRIPT_ type, target label)} of every `map_script` line of every
    map-script root, and {table label: {(type, MapScripts label)}} for the targets that are tables (their
    map_script_2 rows inherit the type). WHY per LINE: one target can sit in several maps' MapScripts (a shared
    on_resume label); keyed by target alone, the second one became a phantom 'called' trigger (round 0)."""
    lines, tables = {}, {}
    for r in g.roots:
        if r["giver"]["kind"] != "map_script":
            continue
        for ln, code in g.labels[r["label"]]["body"]:
            mn, args = ei.cmd(code)
            if mn == "map_script" and len(args) == 2:
                lines[(r["label"], ln)] = (args[0], args[1])
                tables.setdefault(args[1], set()).add((args[0], r["label"]))
    return lines, tables


def ms_word(t):
    """MAP_SCRIPT_ON_FRAME_TABLE -> 'on_frame' (the spec's trigger names)."""
    return re.sub(r"_table$", "", t.lower().replace("map_script_", ""))


def triggers_of(g, name, ms_types, names):
    """The direct ways into `name`: map.json roots (talk / sign / coord), a map script, a post-defeat script, a call
    or jump from another reachable label, a C line. Each conditional entry carries its test under `dev`."""
    out, seen = [], set()

    def add(t):
        k = json.dumps(t, sort_keys=True)
        if k not in seen:
            seen.add(k)
            out.append(t)
    for i in g.root_at.get(name, []):
        r = g.roots[i]
        gv = r["giver"]
        if gv["kind"] == "object":
            t = {"kind": "talk", "map": gv["map"], "object": gv["local_id"], "graphics": gv["graphics"]}
            if r["object_flag"] not in (None, "0"):
                t["dev"] = {"flags": [r["object_flag"]], "test": "%s unset (the object is shown only then)"
                                                                 % r["object_flag"]}
            add(t)
        elif gv["kind"] == "coord":
            c = r["cond"]
            t = {"kind": "coord", "map": gv["map"], "dev": {"test": ei.cond_text(c)}}
            if re.fullmatch(r"VAR_\w+", c[1] or ""):  # TRIGGER_RUN_IMMEDIATELY (vars.h:312) is no var
                t["dev"]["vars"] = [c[1]]
            add(t)
        elif gv["kind"] == "sign":
            add({"kind": "sign", "map": gv["map"]})
        # a map_script root is a table, never a label that changes state itself
    ms_lines, ms_tables = ms_types
    for src, kind, ln, c, _ in g.preds.get(name, []):
        if not g.reachable(src):
            continue
        sref = ei.ref(g.labels[src], ln)
        if kind == "ref" and ms_lines.get((src, ln), (None, None))[1] == name:
            add({"kind": "map_script", "map_script": ms_word(ms_lines[(src, ln)][0]),
                 "maps": sorted({g.roots[i]["map"] for i in g.root_at.get(src, [])}), "dev": {"ref": sref}})
        elif kind == "map_script" and src in ms_tables:
            for t, ms in sorted(ms_tables[src]):
                e = {"kind": "map_script", "map_script": ms_word(t),
                     "maps": sorted({g.roots[i]["map"] for i in g.root_at.get(ms, [])}),
                     "dev": {"test": ei.cond_text(c), "ref": sref}}
                if re.fullmatch(r"VAR_\w+", c[1] or ""):
                    e["dev"]["vars"] = [c[1]]
                add(e)
        elif kind == "battle":
            add({"kind": "battle", "trainer": c[1], "name": names.get(c[1]), "dev": {"ref": sref}})
        else:
            t = {"kind": "called", "by": src, "how": kind, "dev": {"ref": sref}}
            if c is not None:
                t["dev"]["test"] = ei.cond_text(c)
                if c[0] == "flag":
                    t["dev"]["flags"] = [c[1]]
                elif c[0] == "var" and re.fullmatch(r"VAR_\w+", c[1] or ""):
                    t["dev"]["vars"] = [c[1]]
            add(t)
    if name in g.croots:
        add({"kind": "C", "dev": {"ref": g.croots[name]}})
    return out


def entry_tests(g, name):
    """dev: the tests EVERY known path from a root into the label passes (stage 2a's path walk, ei.Graph.paths_to +
    ei.common_tests, imported), each 'cond (how it was produced)', and how many paths were known. WHY: a label's
    direct trigger shows one step; the condition that decides it (a yes/no answer two labels up, a coord var) is on
    the path. Paths from C or past the depth bound are not known: their count says so, and an empty list over zero
    known paths means 'not shown', never 'no condition'."""
    first = g.labels[name]["body"][0][0] if g.labels[name]["body"] else g.labels[name]["line"] + 1
    paths = g.paths_to(name, first)
    known = ei.known_paths(paths)
    tests = sorted("%s (%s)" % (ei.cond_text(c), how) for c, how in ei.common_tests(paths))
    return {"tests": tests, "paths": len(paths), "paths_known": len(known),
            "collapsed": any(("@collapsed",) == x for p in paths for x in p if isinstance(x, tuple))}


# ---------------------------------------------------------------- gates (candidates + the hand table's words)
def profile(g, lab, persist):
    """What the control closure of `lab` does: player moves, persistent writes, warps, story commands, ends."""
    out = {"player_moves": 0, "writes": 0, "warp": 0, "story": 0, "end": 0}
    for x in ei.closure(g.edges, lab, kinds=CTRL):
        for _, code in g.labels[x]["body"]:
            mn, args = ei.cmd(code)
            if mn in MOVE_CMDS and args and args[0] in PLAYER_IDS:
                out["player_moves"] += 1
            if mn in ("setflag", "clearflag") and args and not persist.dropped("flag", args[0]):
                out["writes"] += 1
            if mn in ("setvar", "addvar", "subvar", "copyvar", "setorcopyvar") and args and \
                    not persist.dropped("var", args[0]):
                out["writes"] += 1
            if mn in WARP_CMDS:
                out["warp"] += 1
            if mn.startswith(STORY_CMDS):
                out["story"] += 1
            if mn == "end":
                out["end"] += 1
    return out


def persistent_test(c, persist):
    """A branch condition on saved story state: a persistent flag or var, or a trainer's beaten flag."""
    if c is None:
        return False
    if c[0] == "trainer":
        return True
    ns = "flag" if c[0] == "flag" else "var"
    return bool(re.fullmatch(r"(FLAG|VAR)_\w+", c[1] or "")) and c[1] in persist.ids and \
        not persist.dropped(ns, c[1])


def gate_candidates(g, persist):
    """[(label, kind, line, cond, maps)]. steer: a coord-trigger script that moves the player and makes no persistent
    write, warp or story command (so its trigger stays armed and it fires again); locked: a goto_if on persistent state
    whose target ends without a warp, write or story command while the label's own way on (its later lines and the
    labels they reach) warps."""
    out = []
    coord = {}
    for r in g.roots:
        if r["giver"]["kind"] == "coord":
            coord.setdefault(r["label"], []).append(r)
    for lab in sorted(coord):
        p = profile(g, lab, persist)
        if p["player_moves"] and not p["writes"] and not p["warp"] and not p["story"]:
            conds = sorted({r["cond"] for r in coord[lab]}, key=repr)
            out.append((lab, "steer", g.labels[lab]["line"], conds, sorted({r["map"] for r in coord[lab]})))
    for name in sorted(g.labels):
        if not g.reachable(name):
            continue
        body = g.labels[name]["body"]
        for tgt, kind, ln, c, _ in g.edges[name]:
            if kind != "goto_if" or not persistent_test(c, persist):
                continue
            pt = profile(g, tgt, persist)
            if pt["warp"] or pt["writes"] or pt["story"] or not pt["end"]:
                continue
            on = any(ei.cmd(code)[0] in WARP_CMDS for l2, code in body if l2 > ln)
            on = on or any(profile(g, t2, persist)["warp"] for t2, k2, l2, _, _ in g.edges[name]
                           if l2 > ln and k2 in CTRL)
            if on:
                maps = sorted({g.roots[i]["map"] for i in g.owner_roots.get(name, [])})
                out.append((name, "locked", ln, [c], maps))
    return out


def check_gate_table(cands):
    """GUARD: every GATE_WORDS label is a candidate, and a tabled label has exactly one candidate. WHY: a stale hand
    entry (its label no longer found) would silently drop its words; two candidates under one label would share words
    written for one of them."""
    by = {}
    for c in cands:
        by.setdefault(c[0], []).append(c)
    bad = sorted(k for k in GATE_WORDS if len(by.get(k, [])) != 1)
    if bad:
        raise Refused("GATE_WORDS labels that are not exactly one gate candidate: %s" % bad[:5])


def gate_records(g, cands):
    gates, null = [], []
    for lab, kind, ln, conds, maps in cands:
        dev = {"tests": [ei.cond_text(c) for c in conds], "ref": ei.ref(g.labels[lab], ln)}
        names = {c[1] for c in conds if c[0] in ("flag", "var") and re.fullmatch(r"(FLAG|VAR)_\w+", c[1] or "")}
        if any(n.startswith("FLAG_") for n in names):
            dev["flags"] = sorted(n for n in names if n.startswith("FLAG_"))
        if any(n.startswith("VAR_") for n in names):
            dev["vars"] = sorted(n for n in names if n.startswith("VAR_"))
        entry = GATE_WORDS.get(lab)
        if entry:
            dev["cites"] = ["%s %s" % (c, t) for c, t in entry[1:]]
            when = entry[0]
        else:
            when = None
            null.append(lab)
        gates.append({"label": lab, "maps": maps, "kind": kind, "when": when, "dev": dev})
    return gates, null


# ---------------------------------------------------------------- the build
def table_cites():
    """[(entry, 'path:line', token)] of every cited row of this file's tables."""
    out = []
    for k, e in sorted(GATE_WORDS.items()):
        out += [("GATE_WORDS " + k, c, t) for c, t in e[1:]]
    for k, e in sorted(EFFECT_WORDS.items()):
        out += [("EFFECT_WORDS " + k, c, t) for c, t in e[1:]]
    for k, e in sorted(WARP_CMDS.items()):
        if e:
            out.append(("WARP_CMDS " + k, e[0], e[1]))
    for what, _, _, _, *cites in PERSIST_RANGES:
        out += [("PERSIST_RANGES " + what, c, t) for c, t in cites]
    out.append(("FLAGS_COUNT", FLAGS_COUNT_CITE[0], FLAGS_COUNT_CITE[1]))
    out += [("COPYVAR_BUG", c, t) for c, t in COPYVAR_CITES]
    out += [("PLACEHOLDER_BATTLES " + k, c, t) for k, (c, t) in sorted(PLACEHOLDER_BATTLES.items())]
    return out


def check_cites(d):
    """GUARD: every cited table line holds its token at the pin. WHY: a gate's words or an op's effect the AI reads must
    rest on a line someone can open; a pin bump that moves a line refuses instead of leaving a stale fact."""
    bad = []
    for entry, where, token in table_cites():
        rel, n = where.rsplit(":", 1)
        lines = d.read(rel).split("\n")
        if int(n) > len(lines) or token not in lines[int(n) - 1]:
            bad.append("%s: %s does not hold %r" % (entry, where, token))
    if bad:
        raise Refused("cited table lines do not hold their tokens: %s" % bad[:4])


def check_joins(labels_out, names):
    """GUARD: every trainer a kept change names is in trainers.json (the join the spec asks for)."""
    bad = sorted({c["trainer"] for r in labels_out for c in r["changes"]
                  if c.get("trainer") and c["trainer"] not in names})
    if bad:
        raise Refused("trainers the scripts name that trainers.json lacks: %s" % bad[:5])


def build(d, maps_json, names):
    """The parts of events.json; every guard runs; nothing is written."""
    event_files, gift_files = ei.script_files(d)
    ei.check_sources(d, event_files, gift_files)
    check_cites(d)
    labels = ei.parse_labels(d, event_files)
    edges = ei.build_edges(labels)
    maps = ei.read_maps(d)
    roots = ei.check_map_scripts(ei.map_roots(maps, labels), labels)
    croots = ei.c_roots(d, labels)
    g = ei.Graph(d, labels, edges, roots, croots)
    persist = Persist(d)
    excluded_closure = set()
    for lab in ei.EXCLUDED_LABELS:
        if lab in labels:
            excluded_closure |= ei.closure(edges, lab)
    ctx = {"persist": persist, "names": names, "alias": set_aliases(d, event_files),
           "map_names": {m["id"]: m["name"] for m in maps_json["maps"]}, "rematch_first": rematch_first(d)}
    ms_types = mapscript_types(g)
    memo = {}
    out, dead, dropped, eon = [], [], {}, []
    for name, lab in labels.items():
        live, dead_lines = live_body(lab)
        ops = [(ln, code) for ln, code, _ in live if ei.cmd(code)[0] in OPS or
               ei.cmd(code)[0].startswith("trainerbattle")]
        for ln, code, stop in dead_lines:
            mn = ei.cmd(code)[0]
            if mn in OPS or mn.startswith("trainerbattle"):
                dead.append({"label": name, "ref": "%s:%d" % (lab["file"], lab["line"]), "line": ei.ref(lab, ln),
                             "command": mn, "why": "after `%s` (%s) in the same label: this line never runs"
                                                   % (stop[0], ei.ref(lab, stop[1]))})
        if not ops:
            continue
        if name in excluded_closure:
            eon.append({"label": name, "ref": "%s:%d" % (lab["file"], lab["line"])})
            continue
        if not g.reachable(name):
            via = [p for p in g.pruned if name in ei.closure(edges, p[4])]
            why = "no map.json event, map script, script reference or C line reaches this label"
            if via:
                why = "reached only through a branch the game never takes: %s always returns one value (%s), " \
                      "tested at %s" % (via[0][2], via[0][3], ei.ref(labels[via[0][0]], via[0][1]))
            dead.append({"label": name, "ref": "%s:%d" % (lab["file"], lab["line"]), "why": why})
            continue
        changes, after = [], []
        for ln, code, _ in live:
            mn, args = ei.cmd(code)
            if mn in OPS or mn.startswith("trainerbattle"):
                rec, drop = change_of(ctx, lab, ln, mn, args)
                if drop:
                    grp = dropped.setdefault(drop[0], {"lines": {}, "names": set()})
                    grp["lines"].setdefault(mn, set()).add(ei.ref(lab, ln))
                    grp["names"].add(drop[1])
                else:
                    rec["conditional"] = bool(after)
                    if after:
                        rec["dev"]["after"] = list(after)
                    changes.append(rec)
            if diverts(g, mn, args, memo):
                after.append("%s (%s)" % (code, ei.ref(lab, ln)))
        if not changes:
            continue
        idx = g.owner_roots.get(name, [])
        rec = {"label": name, "maps": sorted({roots[i]["map"] for i in idx}),
               "trigger": triggers_of(g, name, ms_types, names), "changes": changes,
               "ref": "%s:%d" % (lab["file"], lab["line"]), "dev": entry_tests(g, name)}
        if not idx:
            rec["reached_from"] = "C"
            rec["c_ref"] = sorted(g.c_owner.get(name, set()))[0]
        out.append(rec)
    check_joins(out, names)
    cands = gate_candidates(g, persist)
    check_gate_table(cands)
    gates, gates_null = gate_records(g, cands)
    excluded = []
    for what in sorted(dropped):
        grp = dropped[what]
        excluded.append({"what": "writes to %s" % what, "count": sum(len(v) for v in grp["lines"].values()),
                         "by_command": {k: len(v) for k, v in sorted(grp["lines"].items())},
                         "why": "persistent only (spec): not saved story state, so never a change",
                         "dev": {"names": sorted(n for n in grp["names"] if n)}})
    gift_lines = 0
    for rel in gift_files:
        for ln, code in ei.vanilla_lines(d.read(rel), rel):
            mn = ei.cmd(code.strip())[0]  # vanilla_lines keeps the indent; cmd() reads from column 0
            if mn in OPS or mn.startswith("trainerbattle"):
                gift_lines += 1
    excluded.append({"what": "mystery gift scripts (data/mystery_gift.s includes)", "count": gift_lines,
                     "why": "R-3: not solo vanilla play", "files": sorted(gift_files)})
    excluded.append({"what": "the Eon Ticket distribution (record mixing)", "count": len(eon),
                     "why": "R-3: " + ei.EXCLUDED_LABELS["CableClub_EventScript_DistributeEonTicket"],
                     "labels": eon})
    return {"labels": out, "gates": gates, "gates_null": gates_null, "dead": dead, "excluded": excluded,
            "max_closure": g.max_closure, "graph": g}


def refuse_all(obj, defined):
    """R-4..R-7 on the whole object (stage 2a's walkers, imported)."""
    ei.refuse_dev_keys(obj)
    ei.check_dev_names(obj, defined)
    hits = ew.route_keys(obj)
    if hits:
        raise Refused("R-6: route keys %s (never routes, coordinates or step lists)" % hits[:5])
    ew.refuse_withheld(OUT_NAME, obj)


def build_all(d, maps_path):
    with open(maps_path, "rb") as f:
        raw = f.read()
    maps_json = json.loads(raw.decode("utf-8"))
    ei.check_maps_json(maps_json, d.sha)
    trainers_path = os.path.join(os.path.dirname(maps_path), "trainers.json")
    with open(trainers_path, "rb") as f:
        traw = f.read()
    names = {t["symbol"]: ("%s %s" % (t.get("class_name") or "", t["name"])).strip()
             for t in json.loads(traw.decode("utf-8"))["trainers"]}
    res = build(d, maps_json, names)
    digest = hashlib.sha256("\n".join("%s %s" % kv for kv in sorted(d.used.items())).encode()).hexdigest()
    n_changes = sum(len(r["changes"]) for r in res["labels"])
    n_cond = sum(1 for r in res["labels"] for c in r["changes"] if c["conditional"])
    obj = {
        "_generated": {"made_by": MADE_BY, "slice": "spec S3-4 slice 2, stage 2b (KB2)",
                       "files_read": len(d.used), "files_digest": digest,
                       "inputs": {"maps.json": hashlib.sha256(raw).hexdigest(),
                                  "trainers.json": hashlib.sha256(traw).hexdigest()},
                       "max_closure": res["max_closure"]},
        "_source": "pret/pokeemerald@" + d.sha,
        "_kind": "static game knowledge (USER RULING 40)",
        "_reader": ew.READER,
        "_notes": {
            "labels": "every reachable script label whose body changes saved state by a listed op; maps by reference "
                      "(R-2: every map whose map.json event or map script reaches it)",
            "changes": "in label order: setflag, clearflag, setvar, addvar, subvar, copyvar, settrainerflag, "
                       "cleartrainerflag, warp, special, trainerbattle. The register_matchcall macro is listed as "
                       "special SetMatchCallRegisteredFlag with its trainer (asm/macros/event.inc:1970: it sets the "
                       "trainer's saved Match Call flag, src/pokenav_match_call_data.c:1160). NOT LISTED, so a "
                       "label's changes are not all it does: removeobject (an object's hide flag), the give/take "
                       "commands (items_gifts.json), money, coins, set*warp, setrespawn, frontier/contest/apprentice "
                       "macros, other macros that hide a special (seteventmon: special CreateEnemyEventMon, "
                       "asm/macros/event.inc:1995), and whatever a special's C code writes (a special's effect is "
                       "never read here)",
            "conditional": "false only when every earlier line of the label always runs on (SAFE, or a call whose "
                           "callee provably returns); true otherwise, with those lines in dev.after. The label "
                           "itself runs only as its triggers say",
            "effect": "words only for settrainerflag, cleartrainerflag, warp and register_matchcall (a cited "
                      "template filled from a join); null for every flag/var change, every other special and every "
                      "battle: their meaning is never written from a name",
            "trigger": "the DIRECT ways in: talk (object), sign, coord (dev test), map_script (on_transition, "
                       "on_frame, ...; a table entry's dev test), battle (the post-defeat script of that trainer), "
                       "called (by another label: how, and the dev test of a conditional jump), C (a src/ line)",
            "gates": "candidates from two patterns (steer: a coord trigger that moves the player and changes no "
                     "saved state; locked: a goto_if on saved state whose branch ends without a warp while the way "
                     "on warps); `when` words only from the cited hand table GATE_WORDS, else null and listed in "
                     "_gates_when_null",
            "dead": "labels with a listed op that nothing reaches, and op lines after a never-continuing command in "
                    "their label; never in an AI-facing record",
            "excluded": "temp / special / scratch writes (persistent only), mystery gift and record-mixing scripts "
                        "(R-3), counted",
            "copyvar": "a copyvar from a literal is " + COPYVAR_BUG + " (R-3: vanilla reads through a NULL pointer)",
            "counts": {"labels": len(res["labels"]), "changes": n_changes, "conditional": n_cond,
                       "gates": len(res["gates"]), "gates_worded": len(res["gates"]) - len(res["gates_null"]),
                       "dead": len(res["dead"])},
        },
        "labels": res["labels"], "gates": res["gates"], "dead": res["dead"], "excluded": res["excluded"],
        "_gates_when_null": res["gates_null"],
    }
    refuse_all(obj, ei.defined_names(d))
    return obj, res


def write_output(out_dir, obj, d):
    """The ONE door to disk: R-4..R-7 run again here, so no path writes a file they have not seen."""
    refuse_all(obj, ei.defined_names(d))
    os.makedirs(out_dir, exist_ok=True)
    write_json(os.path.join(out_dir, OUT_NAME), obj)


def run(decomp_root, out_dir=OUT_DEFAULT, maps_path=None):
    d = Decomp(decomp_root)
    obj, _ = build_all(d, maps_path or os.path.join(OUT_DEFAULT, "maps.json"))
    write_output(out_dir, obj, d)
    return obj


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--decomp")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--maps", default=os.path.join(OUT_DEFAULT, "maps.json"), help="slice 1's maps.json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        root = ew.resolve_decomp(a.decomp)
        if a.check:
            with tempfile.TemporaryDirectory() as tmp:
                run(root, tmp, a.maps)
                mine = os.path.join(a.out, OUT_NAME)
                same = os.path.exists(mine) and open(mine, "rb").read() == open(os.path.join(tmp, OUT_NAME), "rb").read()
            if not same:
                print("[KB2-EVENTS] CHECK FAILED: %s differs or is missing (regenerate: py -3.12 "
                      "ai_player/gates/extract_events.py)" % OUT_NAME)
                return 1
            print("[KB2-EVENTS] CHECK OK: %s identical to a fresh extraction" % OUT_NAME)
            return 0
        obj = run(root, a.out, a.maps)
        c = obj["_notes"]["counts"]
        print("[KB2-EVENTS] wrote %s: labels %d, changes %d (conditional %d), gates %d (worded %d), dead %d, "
              "excluded groups %d" % (os.path.join(a.out, OUT_NAME), c["labels"], c["changes"], c["conditional"],
                                      c["gates"], c["gates_worded"], c["dead"], len(obj["excluded"])))
        return 0
    except Refused as exc:
        print("[KB2-EVENTS] REFUSED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
