#!/usr/bin/env python3
"""KB2 slice 2, STAGE 2a (spec S3-4): items_gifts.json, the gifts, marts, TM/HM sources and purchases a seasoned player knows.

    py -3.12 ai_player/gates/extract_items.py               # writes ai_player/knowledge/world/items_gifts.json (PINNED clone)
    py -3.12 ai_player/gates/extract_items.py --check       # re-extracts into a temp folder; exit 1 if the file differs
    py -3.12 ai_player/gates/extract_items.py --decomp DIR  # a clone elsewhere (its HEAD must still equal tools/decomp.pin)

INTENT (USER RULING 40, a SEASONED player): a person who has played Emerald knows where the TMs and HMs are and who gives
them, what each mart sells and when its stock grows, and which gifts are once, daily or a choice. This file turns the
pinned decomp into those facts, with every condition in WORDS for the AI and the flag/var names behind it only under a
`dev` dict (R-4). Spec: `PROJECT KNOWLEDGE/ai-research-notes/2026-10-22-BUILD-SPEC-S3-4-slice2.md` (rules R-1..R-7).

WHY NOT "parse giveitem per map" (the recon, `2026-10-22-KB2-slice2-recon-*.md`): item balls live in a shared file and
are placed by map.json; 3 of the 165 finditem labels and RS leftovers are dead, marked only by comments; script code
also lives in data/event_scripts.s; many gifts are runtime values, daily, random or a choice. So:
  * THE SCRIPT SOURCES are what the assembler sees: the `.include` closure of data/event_scripts.s (every map
    scripts.inc, the shared data/scripts/*.inc it includes, and its own inline labels). The closure of data/mystery_gift.s
    is EXCLUDED (R-3: not solo vanilla play) and counted. Preprocessor blocks keep the vanilla side (`#ifndef BUGFIX` /
    the `#else` of `#ifdef BUGFIX|UBFIX`), line numbers kept.
  * R-2 ATTRIBUTE BY REFERENCE: a label belongs to every map whose map.json (object, coord trigger, sign) or whose
    `<map>_MapScripts` reaches it through any reference (goto, call, the conditional forms, `case`, a trainerbattle's
    post-defeat label, a table entry) or by falling through into the next label. A label named in C (src/, include/) is
    a root too, `reached_from: C` with that file:line. A label reached by nothing is DEAD: never in an AI-facing record,
    listed in `dead` with its file:line.
  * R-1 ONE SOURCE PER FACT: field items and hidden items are slice 1's (maps.json `item_balls`, `hidden_items`); this
    file only points at them (`maps_json: {map, list, index}`), and tm_hm copies no coordinates.
  * CONDITIONS: every distinct PATH from a root to the line is computed (the branches taken into it, the branches it
    survives, a coord trigger's var test, a trainer already beaten before a later line, entry through a post-defeat
    script). A label falls into the next one only when its last statement is a non-terminating COMMAND (falls_through:
    a data table never does). The gift's OWN guard (a flag set on the way or after that every path tests unset, or a
    saved var it writes that every path tests; a post-defeat or coord-trigger entry counts as guarded) becomes
    `repeat`. With no own guard, `repeat` rests on POSITIVE evidence only (repeat_by_setters): `repeatable` when
    nothing after the gift moves saved state, `once` / `until_received` when what moves is read on the way to the gift
    or hides the giver, else `unknown` (listed in _notes.repeat_unknown with its setters). The tests common to every
    path, and an either/or on the own var, stay in dev.tests and become `when` words by WORD RULES below, except the
    own once-guard itself (is_once_guard); a test no rule words makes `when` null and the record is listed in
    `_when_null` (spec: never invent words; never 'no condition' over a non-empty dev.tests). A branch on
    `specialvar VAR_RESULT, Fn` where Fn's C body is one constant `return` is never taken and is cut from the graph
    (ContestLobby's debug branch).
  * exclusive_with: five decomp-derived rules, see link_exclusive (object-hide flags, a choice var, an earlier
    choice flag, a shared once-guard) and menu_exclusive (rule E: the arms of one menu).
  * CITED TABLES: CHOOSER_CITED (chosen_by of a special, command or var) and MAP_CONDITIONS (a map no script gates,
    the Mirage Tower) carry the decomp line of each entry with a token check_cites finds on it at the pin.
  * VALUES: a `giveitem VAR_*` line is resolved by walking back to the var's writers: `random N` + `addvar` (a range of
    item ids), `setvar` in the labels a switch dispatches to (the union), `copyvar` from a saved var (its writers), or a
    C special whose body indexes a `static const u16` item array (that array, cited). Otherwise `what: "unknown"` + why.

THE GUARDS (each refuses with exit 2 naming what it found; test_kb2.py feeds each a broken input beside a healthy one,
and a scratch mutant that deletes each CALL is caught):
  check_sources        a map or shared script file that neither data/event_scripts.s nor data/mystery_gift.s includes
  check_cites          a CHOOSER_CITED / MAP_CONDITIONS cite whose line does not hold its token at the pin
  vanilla_lines        a preprocessor conditional other than #ifdef/#ifndef BUGFIX|UBFIX (its vanilla side is unknown)
  parse_labels         a label defined twice (the reference graph would be ambiguous)
  check_map_scripts    a map.json script name that is no label (an event whose script the graph cannot see)
  closure              one root's closure passing MAX_CLOSURE labels
  mart_items           a mart list with no terminator (the list would run on into the next label)
  check_maps_json      maps.json from another decomp commit than the one read here (R-1's pointers would be stale)
  refuse_dev_keys  R-4 a key named flag/flags/var/vars, or a FLAG_/VAR_ name in a string, outside a `dev` dict
  check_dev_names  R-5 a `dev` flag/var name that include/constants/flags.h or vars.h does not #define (NOT emerald.txt)
  refuse_route_keys R-6 a key named x, y, route, path, steps or coords anywhere (slice 1's W6 scan)
  refuse_withheld  R-7 a withheld field (iv / aiFlags), slice 1's scan
verify_world.py re-derives this file by its own reading (a BACKWARD reference walk from each gift line, a FLAG_DAILY_
name test, map.json object flags) and never imports this module.
NOT IN THIS STAGE: events.json (stage 2b). Nothing in ai_player's play code reads this file until a loader and a
KNOWLEDGE_FIELDS classification of world/ exist.
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
from extract_seasoned import Decomp, balanced, parse_defines, parse_enum_blocks, strip_comments, write_json  # noqa: E402,E501  (slice 1's decomp helpers)
import extract_world as ew  # noqa: E402  (the pin, map folders, the W1 / W6 scans)

Refused = ew.Refused
OUT_DEFAULT = ew.OUT_DEFAULT
OUT_NAME = "items_gifts.json"
MADE_BY = "ai_player/gates/extract_items.py"
EVENT_ROOT = "data/event_scripts.s"
GIFT_ROOT = "data/mystery_gift.s"
#: the only preprocessor symbols a script file may test (the census's 11 blocks); vanilla = BUGFIX/UBFIX undefined
FIX_SYMBOLS = ("BUGFIX", "UBFIX")
#: one closure from one root: the largest measured at the pin is far below this (test_kb2 asserts the margin)
MAX_CLOSURE = 1500
#: how far back a path condition or a value is followed through predecessor labels
MAX_DEPTH = 12
#: distinct paths kept per line before they are merged into their common tests (marked '@collapsed')
MAX_PATHS = 32
GIFT_CMDS = {"giveitem": "item", "givemon": "mon", "giveegg": "egg", "givedecoration": "decoration"}
MART_CMDS = {"pokemart": "items", "pokemartdecoration": "decorations", "pokemartdecoration2": "decorations"}
BUY_CMDS = ("additem", "adddecoration")
FIND_CMD = "finditem"
WATCHED = set(GIFT_CMDS) | set(MART_CMDS) | set(BUY_CMDS) | {FIND_CMD}
#: FIX ROUND 2, item 6: the script commands whose ScrCmd body NEVER continues to the next line, each cited to the
#: src/scrcmd.c line that stops or jumps (check_cites holds the token there). A label ending in one never falls into
#: the next label (round 1 let `gotopostbattlescript` fall: 5 phantom edges in data/scripts/trainer_battle.inc).
#: `gotostd` jumps unless its index is out of range (:241), which no script uses. Stage 2b reuses this edge builder.
NEVER_CONTINUES = {
    "end": ("src/scrcmd.c:107", "StopScript(ctx);"),
    "goto": ("src/scrcmd.c:153", "ScriptJump(ctx, ptr);"),
    "return": ("src/scrcmd.c:159", "ScriptReturn(ctx);"),
    "vgoto": ("src/scrcmd.c:204", "ScriptJump(ctx, (u8 *)(addr - sAddressOffset));"),
    "gotostd": ("src/scrcmd.c:242", "ScriptJump(ctx, *ptr);"),
    "returnram": ("src/scrcmd.c:286", "ScriptJump(ctx, gRamScriptRetAddr);"),
    "endram": ("src/scrcmd.c:293", "StopScript(ctx);"),
    "gotopostbattlescript": ("src/scrcmd.c:1836", "ctx->scriptPtr = BattleSetup_GetScriptAddrAfterBattle();"),
    "gotobeatenscript": ("src/scrcmd.c:1842", "ctx->scriptPtr = BattleSetup_GetTrainerPostBattleScript();"),
}
#: a label whose last command is one of these does not run on into the next label (`step_end` closes a movement
#: list, `pokemartlistend` a mart list: without it the list label "falls" into the clerk script after it)
TERMINATORS = tuple(NEVER_CONTINUES) + ("step_end", "pokemartlistend")
#: R-4: these key names may occur ONLY inside a `dev` dict (check_fairness.developer_keys() hazard, spec R-4)
DEV_KEYS = ("flag", "flags", "var", "vars")
NAME_RE = re.compile(r"\b(?:FLAG|VAR)_\w+")
#: vars a script uses as scratch (special 0x80xx vars, VAR_RESULT, temp vars): a value in one is written on the path
SCRATCH_VAR = re.compile(r"VAR_0x80\w\w|VAR_RESULT|VAR_TEMP_\w+")
#: the shared script the Hall of Fame runs (data/maps/EverGrandeCity_HallOfFame calls its labels): the one file the
#: setter word rule (F5, setter_words) reads a var value from
HOF_FILE = "data/scripts/hall_of_fame.inc"
#: R-3: labels whose closure is an event distribution, not solo vanilla play (cited: data/scripts/cable_club.inc,
#: `specialvar VAR_RESULT, ShouldDistributeEonTicket`, a record-mixing gate)
EXCLUDED_LABELS = {"CableClub_EventScript_DistributeEonTicket": "the Eon Ticket (record mixing / event distribution)"}
#: chosen_by of a value written by a C special, a script command or a var a script compares (the spec's chosen_by
#: words). F4 (fix round 1): EVERY entry carries the decomp line that makes it true, as (path:line, a token that must be
#: on that line at the pin); check_cites refuses the build when a token is not there (a moved pin fails loudly).
#: Round 0 called the Favor Lady's prize a `choice`; her request, and so the prize, is drawn at random.
CHOOSER_CITED = {
    "PickLotteryCornerTicket": ("draw", ("src/lottery_corner.c:70", "numMatchingDigits > 1"),
                                ("src/lottery_corner.c:106", "sLotteryPrizes[gSpecialVar_0x8004 - 1]")),
    "GetPlayerTrainerIdOnesDigit": ("trainer_id", ("src/field_specials.c:903", "playerTrainerId[0]) % 10")),
    "GetLeadMonFriendshipScore": ("friendship", ("src/field_specials.c:952", "MON_DATA_FRIENDSHIP")),
    "GetPokeblockNameByMonNature": ("nature", ("src/field_specials.c:1271", "GetNature(")),
    "FavorLadyGetPrize": ("random", ("src/lilycove_lady.c:133", "favorId = Random() % ARRAY_COUNT(sFavorLadyRequests)"),
                          ("src/lilycove_lady.c:283", "prize = sFavorLadyPrizes[sFavorLadyPtr->favorId]")),
    "VAR_STARTER_MON": ("starter", ("src/battle_setup.c:921", "*GetVarPointer(VAR_STARTER_MON) = gSpecialVar_Result")),
    "checkplayergender": ("gender", ("src/scrcmd.c:2016", "gSpecialVar_Result = gSaveBlock2Ptr->playerGender")),
    "random": ("random", ("src/scrcmd.c:484", "gSpecialVar_Result = Random() % max")),
    "multichoice": ("choice", ("src/scrcmd.c:1361", "ScriptMenu_Multichoice(")),
    "multichoicedefault": ("choice", ("src/scrcmd.c:1380", "ScriptMenu_MultichoiceWithDefault(")),
    "multichoicegrid": ("choice", ("src/scrcmd.c:1410", "ScriptMenu_MultichoiceGrid(")),
    "yesno": ("choice", ("src/scrcmd.c:1343", "ScriptMenu_YesNo(")),
    # fix round 2 (item 6): the scrolling menu is a menu producer (the Glass Workshop, Route113_GlassWorkshop:59)
    "ShowScrollableMultichoice": ("choice", ("src/field_specials.c:2254", "void ShowScrollableMultichoice(void)")),
    # fix round 2 (item 5): which Lilycove lady stands there is fixed by the trainer ID at new game
    "Script_GetLilycoveLadyId": ("trainer_id", ("src/lilycove_lady.c:64", "id %= 6;"),
                                 ("src/lilycove_lady.c:115", "void Script_GetLilycoveLadyId(void)")),
}
CHOOSER_OF = {k: v[0] for k, v in CHOOSER_CITED.items()}
#: a condition on a MAP that no script tests (F6, fix round 1): the gift's `when` is null (no word rule gives it) and
#: the cited condition goes to `dev.map_condition`. Keyed by map folder prefix; cites checked like CHOOSER_CITED.
MAP_CONDITIONS = {
    "MirageTower_": ("the Mirage Tower stands on Route 111 only when a coin flip on entering Route 111 shows it, and "
                     "never again after its event (VAR_MIRAGE_TOWER_STATE set)",
                     ("src/mirage_tower.c:320", "if (VarGet(VAR_MIRAGE_TOWER_STATE))"),
                     ("src/mirage_tower.c:328", "visible = rand & 1;"),
                     ("data/maps/Route111/scripts.inc:42", "special SetMirageTowerVisibility")),
    # fix round 3, item 6: the Castform scientist's talk script is ungated (WeatherScientist, :195-199), but while
    # VAR_WEATHER_INSTITUTE_STATE is 0 the map's on-entry script puts him behind Team Aqua (:6, :12): he is out of
    # reach until Shelly is beaten on this floor (:42), whose post-battle script sets the state to 1 (:60)
    "Route119_WeatherInstitute_2F": (
        "the scientist who gives Castform stands behind Team Aqua, out of reach, until you defeat Shelly on this floor "
        "(VAR_WEATHER_INSTITUTE_STATE 0 places him there)",
        ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:6",
         "call_if_eq VAR_WEATHER_INSTITUTE_STATE, 0, Route119_WeatherInstitute_2F_EventScript_SetScientistPosAquaHere"),
        ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:12",
         "setobjectxyperm LOCALID_WEATHER_INSTITUTE_2F_SCIENTIST, 1, 6"),
        ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:42", "trainerbattle_single TRAINER_SHELLY_WEATHER_INSTITUTE"),
        ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:60", "setvar VAR_WEATHER_INSTITUTE_STATE, 1")),
}
#: WORD RULES for `when`: a test whose words a rule gives. Anything else leaves `when` null (listed in _when_null).
#: The draw's words say a prize is NOT guaranteed: a ticket wins only when at least its last 2 digits match a
#: Pokemon's ID number (src/lottery_corner.c:70 `numMatchingDigits > 1`, the digits compared from the last one,
#: :127-141), so most draws win nothing.
WORDS_BY_CHOOSER = {"gender": "by the player's gender", "friendship": "by the lead Pokemon's friendship",
                    "trainer_id": "by the last digit of your trainer ID", "starter": "by your starter",
                    "random": "at random", "nature": "by the lead Pokemon's nature", "choice": "by your answer",
                    "draw": "by the daily lottery draw: a prize only when at least the last 2 digits of the drawn "
                            "number match the ID number of one of your Pokemon (party or PC), so most draws win "
                            "nothing"}
#: FIX ROUND 2, item 3: producers of VAR_RESULT whose ScrCmd body MEASURES ROOM (bag, PC decoration space, party):
#: the room check every gift has, which `repeat` covers. Each is cited to the line computing the result.
#: (`giveitem` / `givedecoration` are macros that callstd STD_OBTAIN_ITEM / _DECORATION, asm/macros/event.inc:1950 /
#: :1964, whose `additem` / `adddecoration` set the result: data/scripts/obtain_item.inc:5 / :72.)
ROOM_PRODUCERS = {
    "checkitemspace": ("src/scrcmd.c:511", "gSpecialVar_Result = CheckBagHasSpace(itemId, (u8)quantity);"),
    "checkdecorspace": ("src/scrcmd.c:570", "gSpecialVar_Result = DecorationCheckSpace(decorId);"),
    "giveitem": ("src/scrcmd.c:493", "gSpecialVar_Result = AddBagItem(itemId, (u8)quantity);"),
    "givedecoration": ("src/scrcmd.c:554", "gSpecialVar_Result = DecorationAdd(decorId);"),
    "givemon": ("src/scrcmd.c:1691", "gSpecialVar_Result = ScriptGiveMon("),
    "giveegg": ("src/scrcmd.c:1699", "gSpecialVar_Result = ScriptGiveEgg(species);"),
    "getpartysize": ("src/scrcmd.c:900", "gSpecialVar_Result = CalculatePlayerPartyCount();"),
}
#: FIX ROUND 2, item 3: "do you OWN X" checks: a POSSESSION is a condition (worded from the item's display name and
#: count, have_words), never room. Round 1 counted checkitem as room and so printed 'no condition' over the Coin Case's
#: Harbor Mail trade (MauvilleCity_House2/scripts.inc:9-10) and the Shell Bell's 4 + 4 shoal items (ShoalCave_
#: LowTideEntranceRoom/scripts.inc:23-26).
POSSESSION = {
    "checkitem": ("src/scrcmd.c:520", "gSpecialVar_Result = CheckBagHasItem(itemId, (u8)quantity);"),
    "checkpcitem": ("src/scrcmd.c:546", "gSpecialVar_Result = CheckPCHasItem(itemId, quantity);"),
    "checkdecor": ("src/scrcmd.c:578", "gSpecialVar_Result = CheckHasDecoration(decorId);"),
    "checkmoney": ("src/scrcmd.c:1760", "gSpecialVar_Result = IsEnoughMoney(&gSaveBlock1Ptr->money, amount);"),
    "checkcoins": ("src/scrcmd.c:2130", "bool8 ScrCmd_checkcoins(struct ScriptContext *ctx)"),
}
#: FIX ROUND 2, item 4: every `special` / `specialvar` met on a gift's trigger path or continuation, each read at its
#: C body (cited: path:line + a token on it). (kind, subject or reader, value, why, *cites). Kinds:
#:   inert     writes nothing a script test reads (text, the screen, a menu's own window, party or box mon data, the
#:             registered item, a TV show, the roamer);
#:   result    inert, but writes VAR_RESULT from a menu or callback (so it is the producer of the test after it);
#:   resource  spends a quantity (berry powder, berries) that `subject` (a reader special) measures: never a block,
#:             the reader's test stays a condition;
#:   writes    sets a saved state `subject` to `value` (a flag, a var, or a SPECIAL_STATES pseudo-state);
#:   record    keeps a size record in var `subject` that only a bigger one beats: the gift is offered again whenever
#:             its test holds (its own re-arm).
#: A special NOT in this table on the continuation makes `repeat` unknown; on the trigger path, `when` null.
SPECIAL_EFFECTS = {
    "BufferTMHMMoveName": ("inert", None, None, "copies a move name into a string buffer",
                           ("src/field_specials.c:1638", "bool8 BufferTMHMMoveName(void)")),
    # fix round 3, item 3: two more read at their C bodies (each on the way into a gift whose `when` is worded)
    "BufferTrendyPhraseString": ("inert", None, None, "copies the trendy phrase into a string buffer",
                                 ("src/dewford_trend.c:290", "void BufferTrendyPhraseString(void)")),
    "ShouldTryRematchBattle": ("inert", None, None, "returns whether the gym leader is ready for a rematch (reads)",
                               ("src/battle_setup.c:1839", "bool8 ShouldTryRematchBattle(void)")),
    "ChangeBoxPokemonNickname": ("inert", None, None, "opens the naming screen for the boxed gift mon",
                                 ("src/tv.c:3307", "void ChangeBoxPokemonNickname(void)")),
    "ChangePokemonNickname": ("inert", None, None, "opens the naming screen for the party gift mon",
                              ("src/tv.c:3292", "void ChangePokemonNickname(void)")),
    "ClearLinkContestFlags": ("inert", None, None, "zeroes gLinkContestFlags (RAM, not saved)",
                              ("src/contest_util.c:2771", "void ClearLinkContestFlags(void)")),
    "DoBerryBlending": ("resource", "PlayerHasBerries", None, "the blender minigame: spends a berry",
                        ("src/berry_blender.c:1047", "void DoBerryBlending(void)")),
    "DoContestHallWarp": ("inert", None, None, "a warp with its screen effects",
                          ("src/field_screen_effect.c:755", "void DoContestHallWarp(void)")),
    "DoMirageTowerCeilingCrumble": ("inert", None, None, "sprites and a screen shake",
                                    ("src/mirage_tower.c:420", "void DoMirageTowerCeilingCrumble(void)")),
    "DrawWholeMapView": ("inert", None, None, "redraws the map", ("src/field_camera.c:94", "void DrawWholeMapView(void)")),
    "GetPCBoxToSendMon": ("inert", None, None, "returns the box number",
                          ("src/field_specials.c:3400", "u16 GetPCBoxToSendMon(void)")),
    "GetPlayerBigGuyGirlString": ("inert", None, None, "copies 'big guy' / 'big girl' into a string buffer",
                                  ("src/field_specials.c:906", "void GetPlayerBigGuyGirlString(void)")),
    "HasEnoughBerryPowder": ("inert", None, None, "reads the berry powder amount",
                             ("src/berry_powder.c:153", "bool8 HasEnoughBerryPowder(void)")),
    "HealPlayerParty": ("inert", None, None, "restores the party's HP, PP and status",
                        ("src/script_pokemon_util.c:30", "void HealPlayerParty(void)")),
    "InitRoamer": ("inert", None, None, "creates the roaming Latias / Latios (no script test reads the roamer)",
                   ("src/roamer.c:108", "void InitRoamer(void)")),
    "PrintPlayerBerryPowderAmount": ("inert", None, None, "prints the amount in a window",
                                     ("src/berry_powder.c:217", "void PrintPlayerBerryPowderAmount(void)")),
    "RemoveBerryPowderVendorMenu": ("inert", None, None, "closes a window",
                                    ("src/berry_powder.c:234", "void RemoveBerryPowderVendorMenu(void)")),
    "ResetTrickHouseNuggetFlag": ("writes", "FLAG_HIDDEN_ITEM_TRICK_HOUSE_NUGGET", False,
                                  "clears the hidden Nugget's flag (FlagClear)",
                                  ("src/field_specials.c:1182", "void ResetTrickHouseNuggetFlag(void)")),
    "SetContestTrainerGfxIds": ("inert", None, None, "sets the object graphics vars VAR_OBJ_GFX_ID_0..3 (sprites)",
                                ("src/contest_util.c:2294", "void SetContestTrainerGfxIds(void)")),
    "SetPacifidlogTMReceivedDay": ("writes", "VAR_PACIFIDLOG_TM_RECEIVED_DAY", None, "stores today's day count",
                                   ("src/field_specials.c:1566", "u16 SetPacifidlogTMReceivedDay(void)")),
    "ShakeCamera": ("inert", None, None, "a camera shake task", ("src/field_specials.c:1470", "void ShakeCamera(void)")),
    "ShouldReadyContestArtist": ("inert", None, None, "sets VAR_0x8004 from this contest's result (scratch)",
                                 ("src/contest_util.c:2367", "void ShouldReadyContestArtist(void)")),
    "ShouldShowBoxWasFullMessage": ("writes", "FLAG_SHOWN_BOX_WAS_FULL_MESSAGE", True,
                                    "sets the 'box was full' message flag once",
                                    ("src/field_specials.c:3405", "bool8 ShouldShowBoxWasFullMessage(void)")),
    "ShowScrollableMultichoice": ("result", None, None, "a scrolling menu: its choice is VAR_RESULT (a menu producer)",
                                  ("src/field_specials.c:2254", "void ShowScrollableMultichoice(void)"),
                                  ("src/field_specials.c:2384", "gSpecialVar_Result = MULTI_B_PRESSED;")),
    "SwapRegisteredBike": ("inert", None, None, "swaps the registered (Select) item, which no script reads",
                           ("src/item.c:572", "void SwapRegisteredBike(void)")),
    "TakeBerryPowder": ("resource", "HasEnoughBerryPowder", None, "spends berry powder",
                        ("src/berry_powder.c:188", "bool8 TakeBerryPowder(void)")),
    "TryEnterContestMon": ("inert", None, None, "sets up this contest's entrants (RAM)",
                           ("src/contest_util.c:1958", "void TryEnterContestMon(void)")),
    "TryPutLotteryWinnerReportOnAir": ("inert", None, None, "stores a TV show",
                                       ("src/tv.c:2186", "void TryPutLotteryWinnerReportOnAir(void)")),
    "TurnOffTVScreen": ("inert", None, None, "map metatiles", ("src/tv.c:869", "void TurnOffTVScreen(void)")),
    "TurnOnTVScreen": ("inert", None, None, "map metatiles", ("src/tv.c:875", "void TurnOnTVScreen(void)")),
    "MauvilleGymDeactivatePuzzle": ("inert", None, None, "map metatiles",
                                    ("src/field_specials.c:727", "void MauvilleGymDeactivatePuzzle(void)")),
    "ResetHealLocationFromDewford": ("inert", None, None, "moves the whiteout point, which no script test reads",
                                     ("src/field_specials.c:3881", "void ResetHealLocationFromDewford(void)")),
    "GetPlayerTrainerIdOnesDigit": ("inert", None, None, "returns a digit of the trainer ID",
                                    ("src/field_specials.c:901", "u8 GetPlayerTrainerIdOnesDigit(void)")),
    "GetLeadMonFriendshipScore": ("inert", None, None, "returns the lead's friendship band",
                                  ("src/field_specials.c:949", "u8 GetLeadMonFriendshipScore(void)")),
    "ChoosePartyMon": ("inert", None, None, "opens the party menu (the choice goes to VAR_0x8004)",
                       ("src/party_menu.c:6262", "void ChoosePartyMon(void)")),
    "GetSeedotSizeRecordInfo": ("inert", None, None, "prints the record",
                                ("src/pokemon_size_record.c:157", "void GetSeedotSizeRecordInfo(void)")),
    "GetLotadSizeRecordInfo": ("inert", None, None, "prints the record",
                               ("src/pokemon_size_record.c:176", "void GetLotadSizeRecordInfo(void)")),
    "CompareSeedotSize": ("record", "VAR_SEEDOT_SIZE_RECORD", None,
                          "a Seedot bigger than the record sets a new record (a bigger one beats it again)",
                          ("src/pokemon_size_record.c:164", "void CompareSeedotSize(void)"),
                          ("src/pokemon_size_record.c:132", "*sizeRecord = sizeParams;")),
    "CompareLotadSize": ("record", "VAR_LOTAD_SIZE_RECORD", None,
                         "a Lotad bigger than the record sets a new record (a bigger one beats it again)",
                         ("src/pokemon_size_record.c:183", "void CompareLotadSize(void)"),
                         ("src/pokemon_size_record.c:132", "*sizeRecord = sizeParams;")),
    # the Lilycove ladies (src/lilycove_lady.c): the Favor Lady
    "Script_GetLilycoveLadyId": ("inert", None, None, "returns which lady stands there",
                                 ("src/lilycove_lady.c:115", "void Script_GetLilycoveLadyId(void)")),
    "GetFavorLadyState": ("inert", None, None, "reads her state (SPECIAL_READS)",
                          ("src/lilycove_lady.c:159", "u8 GetFavorLadyState(void)")),
    "BufferFavorLadyRequest": ("inert", None, None, "a string buffer",
                               ("src/lilycove_lady.c:175", "void BufferFavorLadyRequest(void)")),
    "BufferFavorLadyItemName": ("inert", None, None, "a string buffer",
                                ("src/lilycove_lady.c:198", "void BufferFavorLadyItemName(void)")),
    "BufferFavorLadyPlayerName": ("inert", None, None, "a string buffer",
                                  ("src/lilycove_lady.c:210", "void BufferFavorLadyPlayerName(void)")),
    "HasAnotherPlayerGivenFavorLadyItem": ("inert", None, None, "reads a stored name",
                                           ("src/lilycove_lady.c:181", "bool8 HasAnotherPlayerGivenFavorLadyItem(void)")),
    "DidFavorLadyLikeItem": ("inert", None, None, "reads likedItem",
                             ("src/lilycove_lady.c:218", "bool8 DidFavorLadyLikeItem(void)")),
    "Script_FavorLadyOpenBagMenu": ("result", None, None, "the bag menu: 1 when you pick an item",
                                    ("src/lilycove_lady.c:224", "void Script_FavorLadyOpenBagMenu(void)")),
    "Script_DoesFavorLadyLikeItem": ("writes", "STATE_FAVOR_LADY", "LILYCOVE_LADY_STATE_COMPLETED",
                                     "DoesFavorLadyLikeItem marks her request done and counts a liked item",
                                     ("src/lilycove_lady.c:259", "bool8 Script_DoesFavorLadyLikeItem(void)"),
                                     ("src/lilycove_lady.c:237", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_COMPLETED;")),
    "IsFavorLadyThresholdMet": ("inert", None, None, "reads the liked-item count",
                                ("src/lilycove_lady.c:264", "bool8 IsFavorLadyThresholdMet(void)")),
    "FavorLadyGetPrize": ("writes", "STATE_FAVOR_LADY", "LILYCOVE_LADY_STATE_PRIZE", "picks the prize, state PRIZE",
                          ("src/lilycove_lady.c:278", "u16 FavorLadyGetPrize(void)"),
                          ("src/lilycove_lady.c:285", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_PRIZE;")),
    "SetFavorLadyState_Complete": ("writes", "STATE_FAVOR_LADY", "LILYCOVE_LADY_STATE_COMPLETED", "state COMPLETED",
                                   ("src/lilycove_lady.c:289", "void SetFavorLadyState_Complete(void)"),
                                   ("src/lilycove_lady.c:292", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_COMPLETED;")),
    # the Quiz Lady
    "GetQuizLadyState": ("inert", None, None, "reads her state (SPECIAL_READS)",
                         ("src/lilycove_lady.c:347", "u8 GetQuizLadyState(void)")),
    # fix round 3, item 3: who wrote her quiz is SAVED state (her quiz's player name and trainer ID), read here (:382-386,
    # the IsQuizTrainerIdNotPlayer check at :383); this special also rewrites it when the quiz's answer word is locked
    # (:378 clears the name: the author becomes the lady), so it is a writer of a runtime value, never inert
    "GetQuizAuthor": ("writes", "STATE_QUIZ_AUTHOR", None, "returns who wrote her quiz; may replace a locked quiz by one "
                      "of her own (the author becomes the lady)",
                      ("src/lilycove_lady.c:358", "u8 GetQuizAuthor(void)"),
                      ("src/lilycove_lady.c:378", "quiz->playerName[0] = EOS;"),
                      ("src/lilycove_lady.c:383", "IsQuizTrainerIdNotPlayer()")),
    "IsQuizAnswerCorrect": ("inert", None, None, "compares two words",
                            ("src/lilycove_lady.c:479", "bool8 IsQuizAnswerCorrect(void)")),
    "QuizLadyShowQuizQuestion": ("result", None, None, "the easy-chat quiz screen: 1 when you submit an answer",
                                 ("src/easy_chat.c:1573", "void QuizLadyShowQuizQuestion(void)")),
    "QuizLadyGetPlayerAnswer": ("result", None, None, "the easy-chat answer screen: 1 when you submit an answer",
                                ("src/lilycove_lady.c:474", "void QuizLadyGetPlayerAnswer(void)")),
    "BufferQuizAuthorNameAndCheckIfLady": ("inert", None, None, "a string buffer, and whether the lady wrote it",
                                           ("src/lilycove_lady.c:457",
                                            "bool8 BufferQuizAuthorNameAndCheckIfLady(void)")),
    "BufferQuizPrizeItem": ("inert", None, None, "puts the prize in VAR_0x8005",
                            ("src/lilycove_lady.c:487", "void BufferQuizPrizeItem(void)")),
    "ClearQuizLadyPlayerAnswer": ("inert", None, None, "clears your last answer (you give a new one before it is read)",
                                  ("src/lilycove_lady.c:505", "void ClearQuizLadyPlayerAnswer(void)")),
    "SetQuizLadyState_Complete": ("writes", "STATE_QUIZ_LADY", "LILYCOVE_LADY_STATE_COMPLETED", "state COMPLETED",
                                  ("src/lilycove_lady.c:493", "void SetQuizLadyState_Complete(void)"),
                                  ("src/lilycove_lady.c:496", "sQuizLadyPtr->state = LILYCOVE_LADY_STATE_COMPLETED;")),
    "SetQuizLadyState_GivePrize": ("writes", "STATE_QUIZ_LADY", "LILYCOVE_LADY_STATE_PRIZE", "state PRIZE",
                                   ("src/lilycove_lady.c:499", "void SetQuizLadyState_GivePrize(void)"),
                                   ("src/lilycove_lady.c:502", "sQuizLadyPtr->state = LILYCOVE_LADY_STATE_PRIZE;")),
    "ClearQuizLadyQuestionAndAnswer": ("inert", None, None, "clears the quiz text you are about to write",
                                       ("src/lilycove_lady.c:526", "void ClearQuizLadyQuestionAndAnswer(void)")),
    "QuizLadyPickNewQuestion": ("writes", "STATE_QUIZ_AUTHOR", "QUIZ_AUTHOR_LADY",
                                "picks her next question of her own (her state is untouched; the author becomes the lady)",
                                ("src/lilycove_lady.c:516", "void QuizLadyPickNewQuestion(void)"),
                                ("src/lilycove_lady.c:311", "sQuizLadyPtr->playerName[0] = EOS;"),
                                ("src/lilycove_lady.c:382", "return QUIZ_AUTHOR_LADY;")),
    # fix round 3, item 3: NOT inert. It stores your trainer ID and name as the quiz's author (:554-555), which
    # GetQuizAuthor reads back (:383 IsQuizTrainerIdNotPlayer, :386): her quiz is then YOURS
    "QuizLadyRecordCustomQuizData": ("writes", "STATE_QUIZ_AUTHOR", "QUIZ_AUTHOR_PLAYER",
                                     "stores your quiz's prize, your name and your trainer ID: the quiz is now yours",
                                     ("src/lilycove_lady.c:547", "void QuizLadyRecordCustomQuizData(void)"),
                                     ("src/lilycove_lady.c:554",
                                      "sQuizLadyPtr->playerTrainerId[i] = gSaveBlock2Ptr->playerTrainerId[i];"),
                                     ("src/lilycove_lady.c:386", "return QUIZ_AUTHOR_PLAYER;")),
    "QuizLadySetCustomQuestion": ("result", None, None, "the easy-chat screen for your own question",
                                  ("src/lilycove_lady.c:536", "void QuizLadySetCustomQuestion(void)")),
    "QuizLadySetWaitingForChallenger": ("writes", "STATE_QUIZ_WAITING", "TRUE", "waitingForChallenger = TRUE",
                                        ("src/lilycove_lady.c:559", "void QuizLadySetWaitingForChallenger(void)")),
    "QuizLadyTakePrizeForCustomQuiz": ("resource", None, None, "takes the bag item you offer as your quiz's prize",
                                       ("src/lilycove_lady.c:542", "void QuizLadyTakePrizeForCustomQuiz(void)")),
    "Script_QuizLadyOpenBagMenu": ("result", None, None, "the bag menu: 1 when you pick an item",
                                   ("src/lilycove_lady.c:511", "void Script_QuizLadyOpenBagMenu(void)")),
}
#: a reader special whose result IS a SPECIAL_STATES state (its tests are tests on that state)
SPECIAL_READS = {"GetFavorLadyState": "STATE_FAVOR_LADY", "GetQuizLadyState": "STATE_QUIZ_LADY",
                 "GetQuizAuthor": "STATE_QUIZ_AUTHOR"}
#: the saved C states the specials above read and write: the value at new game and EVERY C writer, read (the re-arm
#: scan's C side: none re-arms in solo play; record mixing is excluded by R-3)
SPECIAL_STATES = {
    "STATE_FAVOR_LADY": {"initial": "LILYCOVE_LADY_STATE_READY", "c": [
        "InitLilycoveFavorLady READY at new game (src/lilycove_lady.c:143, from InitLilycoveLady, src/new_game.c:199) "
        "and inside SetFavorLadyState_Complete, overwritten at :292",
        "ResetFavorLadyForRecordMix READY (:156, record mixing: R-3)",
        "FavorLadyGetPrize PRIZE (:285) and DoesFavorLadyLikeItem COMPLETED (:237): script specials, scanned as writers"],
        "cites": [("src/lilycove_lady.c:143", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_READY;"),
                  ("src/lilycove_lady.c:156", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_READY;"),
                  ("src/new_game.c:199", "InitLilycoveLady();")]},
    "STATE_QUIZ_LADY": {"initial": "LILYCOVE_LADY_STATE_READY", "c": [
        "InitLilycoveQuizLady READY at new game (src/lilycove_lady.c:320)",
        "ResetQuizLadyForRecordMix READY (:342, record mixing: R-3)",
        "SetQuizLadyState_Complete COMPLETED (:496) and SetQuizLadyState_GivePrize PRIZE (:502): script specials, "
        "scanned as writers"],
        "cites": [("src/lilycove_lady.c:320", "sQuizLadyPtr->state = LILYCOVE_LADY_STATE_READY;"),
                  ("src/lilycove_lady.c:342", "sQuizLadyPtr->state = LILYCOVE_LADY_STATE_READY;")]},
    # fix round 3, item 3: who wrote her quiz (a name and trainer ID in her saved quiz); at new game her own
    # (InitLilycoveQuizLady -> QuizLadyPickQuestion clears the name, :311; an empty name reads as the lady, :397, :382)
    "STATE_QUIZ_AUTHOR": {"initial": "QUIZ_AUTHOR_LADY", "c": [
        "QuizLadyPickQuestion clears the author name at new game (src/lilycove_lady.c:311)",
        "GetQuizAuthor (:378), QuizLadyPickNewQuestion and QuizLadyRecordCustomQuizData (:554): script specials, "
        "scanned as writers; record mixing brings in other players' quizzes (R-3)"],
        "cites": [("src/lilycove_lady.c:311", "sQuizLadyPtr->playerName[0] = EOS;"),
                  ("src/lilycove_lady.c:397", "if (sQuizLadyPtr->playerName[0] == EOS)")]},
    "STATE_QUIZ_WAITING": {"initial": "FALSE", "c": ["read only by IsQuizLadyWaitingForChallenger (:468)"],
                           "cites": [("src/lilycove_lady.c:468", "bool8 IsQuizLadyWaitingForChallenger(void)")]},
}
#: WORD RULE for a special's result (item 5): the words of `eq value` of a special the decomp shows, each cited. The
#: Lilycove lady is fixed by the trainer ID at new game (src/lilycove_lady.c:63-65), so the AI can check which lady
#: is there by looking; in solo play the Favor Lady takes one item, and only her single best item reaches her
#: LILYCOVE_LADY_GIFT_THRESHOLD (fix round 3, item 4).
SPECIALVAR_WORDS = {
    ("Script_GetLilycoveLadyId", "LILYCOVE_LADY_FAVOR"): (
        "the lady in the Lilycove Pokemon Center is the Favor Lady (which of the three ladies stands there is fixed "
        "by your trainer ID when the game starts)",
        ("src/lilycove_lady.c:64", "id %= 6;"), ("src/lilycove_lady.c:65", "id >>= 1;")),
    ("Script_GetLilycoveLadyId", "LILYCOVE_LADY_QUIZ"): (
        "the lady in the Lilycove Pokemon Center is the Quiz Lady (which of the three ladies stands there is fixed by "
        "your trainer ID when the game starts)",
        ("src/lilycove_lady.c:64", "id %= 6;"), ("src/lilycove_lady.c:65", "id >>= 1;")),
    ("Script_FavorLadyOpenBagMenu", "1"): (
        "you pick an item from your bag for her",
        ("data/scripts/lilycove_lady.inc:71", "goto_if_eq VAR_RESULT, 1, LilycoveCity_PokemonCenter_1F_EventScript_"
                                              "GiveFavorItem")),
    ("Script_DoesFavorLadyLikeItem", "1"): (
        "it is an item she likes (one that fits her request)",
        ("src/lilycove_lady.c:245", "if (sFavorLadyAcceptedItemLists[sFavorLadyPtr->favorId][i] == itemId)")),
    # FIX ROUND 3, item 4 (solo-play true): DoesFavorLadyLikeItem sets her state COMPLETED on EVERY item given (:237),
    # liked or not, and in solo play only record mixing sets it back to READY (:156, R-3): she takes ONE item from you.
    # One liked item counts 1 towards her threshold of 5 (:248), but her single BEST item sets the count to 5 at once
    # (:250-251), so the only item that can win her prize is her best one.
    ("IsFavorLadyThresholdMet", "1"): (
        "the one item you give her is her single favourite thing for her request (she takes only one item from you, "
        "and only her favourite one earns her prize)",
        ("src/lilycove_lady.c:237", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_COMPLETED;"),
        ("src/lilycove_lady.c:248", "sFavorLadyPtr->numItemsGiven++;"),
        ("src/lilycove_lady.c:250", "if (sFavorLadyPtr->bestItem == itemId)"),
        ("src/lilycove_lady.c:251", "sFavorLadyPtr->numItemsGiven = LILYCOVE_LADY_GIFT_THRESHOLD;"),
        ("src/lilycove_lady.c:270", "return numItemsGiven < LILYCOVE_LADY_GIFT_THRESHOLD ? FALSE : TRUE;"),
        ("include/constants/lilycove_lady.h:13", "#define LILYCOVE_LADY_GIFT_THRESHOLD    5"),
        ("data/scripts/lilycove_lady.inc:15",
         "goto_if_eq VAR_RESULT, LILYCOVE_LADY_STATE_COMPLETED, LilycoveCity_PokemonCenter_1F_EventScript_"
         "FavorLadyCompleted")),
    # fix round 3, item 4: READY at new game (:143), COMPLETED once you give her any item (:237); only record mixing
    # sets it back to READY (:156, R-3), so in solo play this holds until you hand her your one item
    ("GetFavorLadyState", "LILYCOVE_LADY_STATE_READY"): (
        "you have not given her an item yet (she takes only one)",
        ("src/lilycove_lady.c:143", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_READY;"),
        ("src/lilycove_lady.c:237", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_COMPLETED;"),
        ("data/scripts/lilycove_lady.inc:14",
         "goto_if_eq VAR_RESULT, LILYCOVE_LADY_STATE_READY, LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyReady")),
    ("GetFavorLadyState", "LILYCOVE_LADY_STATE_PRIZE"): (
        "she still owes you her prize from a visit when your bag was full",
        ("data/scripts/lilycove_lady.inc:16", "goto_if_eq VAR_RESULT, LILYCOVE_LADY_STATE_PRIZE"),
        ("src/lilycove_lady.c:285", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_PRIZE;")),
    ("GetQuizLadyState", "LILYCOVE_LADY_STATE_PRIZE"): (
        "she still owes you her quiz prize from a visit when your bag was full",
        ("data/scripts/lilycove_lady.inc:136", "goto_if_eq VAR_RESULT, LILYCOVE_LADY_STATE_PRIZE"),
        ("data/scripts/lilycove_lady.inc:265", "special SetQuizLadyState_GivePrize")),
    ("GetQuizAuthor", "QUIZ_AUTHOR_LADY"): (
        "her quiz is one of her own",
        ("data/scripts/lilycove_lady.inc:143", "goto_if_eq VAR_RESULT, QUIZ_AUTHOR_LADY")),
    ("GetQuizAuthor", "QUIZ_AUTHOR_OTHER_PLAYER"): (
        "her quiz is one another player wrote (it reaches her by record mixing)",
        ("data/scripts/lilycove_lady.inc:142", "goto_if_eq VAR_RESULT, QUIZ_AUTHOR_OTHER_PLAYER")),
    ("QuizLadyGetPlayerAnswer|QuizLadyShowQuizQuestion", "1"): (
        "you give her an answer",
        ("data/scripts/lilycove_lady.inc:186", "goto_if_eq VAR_RESULT, 1, LilycoveCity_PokemonCenter_1F_EventScript_"
                                               "SubmitQuizResponse")),
    ("IsQuizAnswerCorrect", "1"): (
        "you answer her quiz correctly",
        ("data/scripts/lilycove_lady.inc:215", "goto_if_eq VAR_RESULT, TRUE, LilycoveCity_PokemonCenter_1F_EventScript_"
                                               "CorrectResponse")),
    ("CompareSeedotSize", "COMPARE_SIZE_LARGER"): (
        "you show him a Seedot bigger than the biggest one he has seen (each bigger one sets a new record)",
        ("data/maps/SootopolisCity_LotadAndSeedotHouse/scripts.inc:15", "goto_if_eq VAR_RESULT, COMPARE_SIZE_LARGER"),
        ("src/pokemon_size_record.c:132", "*sizeRecord = sizeParams;")),
    ("CompareLotadSize", "COMPARE_SIZE_LARGER"): (
        "you show him a Lotad bigger than the biggest one he has seen (each bigger one sets a new record)",
        ("data/maps/SootopolisCity_LotadAndSeedotHouse/scripts.inc:58", "goto_if_eq VAR_RESULT, COMPARE_SIZE_LARGER"),
        ("src/pokemon_size_record.c:132", "*sizeRecord = sizeParams;")),
}
#: WORD RULE for a scratch result whose producer differs by the way in (no single special to key on): the words of
#: the test AT ITS LINE (keyed (line, op, value)), cited to that line. The size-record men's party choice; the Quiz
#: Lady's answer screen (lilycove_lady.inc:186, fed by :190 / :195).
LINE_WORDS = {
    ("data/maps/SootopolisCity_LotadAndSeedotHouse/scripts.inc:11", "ne", "PARTY_NOTHING_CHOSEN"): (
        "you show him one of your Pokemon",
        ("data/maps/SootopolisCity_LotadAndSeedotHouse/scripts.inc:11", "goto_if_eq VAR_RESULT, PARTY_NOTHING_CHOSEN")),
    ("data/maps/SootopolisCity_LotadAndSeedotHouse/scripts.inc:54", "ne", "PARTY_NOTHING_CHOSEN"): (
        "you show him one of your Pokemon",
        ("data/maps/SootopolisCity_LotadAndSeedotHouse/scripts.inc:54", "goto_if_eq VAR_RESULT, PARTY_NOTHING_CHOSEN")),
    ("data/scripts/lilycove_lady.inc:186", "eq", "1"): (
        "you give her an answer",
        ("data/scripts/lilycove_lady.inc:186", "goto_if_eq VAR_RESULT, 1, LilycoveCity_PokemonCenter_1F_EventScript_"
                                               "SubmitQuizResponse")),
}
#: the values VAR_FACING can hold (the player faces one of the four ways: include/constants/global.h:138-141), so a
#: way that fails all four VAR_FACING tests is not a way (the Oceanic Museum grunt exits by one of four branches)
FINITE_DOMAINS = {"VAR_FACING": ("DIR_SOUTH", "DIR_NORTH", "DIR_WEST", "DIR_EAST")}
FINITE_CITES = [("include/constants/global.h:138", "#define DIR_SOUTH       1"),
                ("include/constants/global.h:141", "#define DIR_EAST        4")]
#: the game clears every TEMP flag and var on each map entry: a block on one lasts one visit (re-armed by leaving)
TEMP_CLEAR = ("src/overworld.c:798", "ClearTempFieldEventData();")
#: FIX ROUND 2, item 5: gift lines that are ONE prize offered in two places, decided at the decomp. The Trick House's
#: Entrance tent pair is the End pair's PICK-UP, not a second tent: the End's no-room branch sets
#: VAR_TRICK_HOUSE_PRIZE_PICKUP 1 (Route110_TrickHouseEnd/scripts.inc:157, :195), and only that (at level 8) makes the
#: Entrance set state 6 (Route110_TrickHouseEntrance/scripts.inc:19, :33, :38), whose case 6 offers the tent (:225).
EXCLUSIVE_CITED = [
    (("Route110_TrickHouseEnd_EventScript_GiveRedTent:1", "Route110_TrickHouseEnd_EventScript_GiveBlueTent:1",
      "Route110_TrickHouseEntrance_EventScript_GiveRedTent:1", "Route110_TrickHouseEntrance_EventScript_GiveBlueTent:1"),
     "one tent: the Entrance offers the End's tent again only when it did not fit",
     ("data/maps/Route110_TrickHouseEnd/scripts.inc:157",
      "call_if_eq VAR_RESULT, FALSE, Route110_TrickHouseEnd_EventScript_NoRoomForTent"),
     ("data/maps/Route110_TrickHouseEnd/scripts.inc:195", "setvar VAR_TRICK_HOUSE_PRIZE_PICKUP, 1"),
     ("data/maps/Route110_TrickHouseEntrance/scripts.inc:19", "goto_if_eq VAR_TRICK_HOUSE_PRIZE_PICKUP, 1"),
     ("data/maps/Route110_TrickHouseEntrance/scripts.inc:33", "goto_if_eq VAR_TRICK_HOUSE_LEVEL, 8"),
     ("data/maps/Route110_TrickHouseEntrance/scripts.inc:38", "setvar VAR_TRICK_HOUSE_ENTRANCE_STATE, 6"),
     ("data/maps/Route110_TrickHouseEntrance/scripts.inc:225",
      "case 6, Route110_TrickHouseEntrance_EventScript_MechadollReward")),
]
#: choosers fixed when the game starts: gifts on different values of one are alternatives (exclusive_with, item 5)
FIXED_CHOOSERS = ("gender", "trainer_id")
#: FIX ROUND 3, item 1 (the SOLE-WRITER rule): every script command that WRITES a flag or var given as an operand, with
#: the operand positions it writes, each cited to its ScrCmd body. Measured at the pin: the mnemonics of data/ whose
#: operand is a FLAG_/VAR_ name (asm/macros/event.inc); a test (goto_if_*), a `switch` or an object command only reads.
WRITER_CMDS = {
    "setflag": ((0,), ("src/scrcmd.c:584", "FlagSet(ScriptReadHalfword(ctx));")),
    "clearflag": ((0,), ("src/scrcmd.c:590", "FlagClear(ScriptReadHalfword(ctx));")),
    "setvar": ((0,), ("src/scrcmd.c:363", "u16 *ptr = GetVarPointer(ScriptReadHalfword(ctx));")),
    "copyvar": ((0,), ("src/scrcmd.c:371", "*ptr = *GetVarPointer(ScriptReadHalfword(ctx));")),
    "setorcopyvar": ((0,), ("src/scrcmd.c:377", "u16 *ptr = GetVarPointer(ScriptReadHalfword(ctx));")),
    "addvar": ((0,), ("src/scrcmd.c:468", "u16 *ptr = GetVarPointer(ScriptReadHalfword(ctx));")),
    "subvar": ((0,), ("src/scrcmd.c:475", "u16 *ptr = GetVarPointer(ScriptReadHalfword(ctx));")),
    "specialvar": ((0,), ("src/scrcmd.c:129", "u16 *var = GetVarPointer(ScriptReadHalfword(ctx));")),
    "getplayerxy": ((0, 1), ("src/scrcmd.c:890", "u16 *pX = GetVarPointer(ScriptReadHalfword(ctx));"),
                    ("src/scrcmd.c:891", "u16 *pY = GetVarPointer(ScriptReadHalfword(ctx));")),
    "checkcoins": ((0,), ("src/scrcmd.c:2133", "*ptr = GetCoins();")),
}
#: `removeobject <local id>` sets the hide flag of that object (map.json `flag`): a script writer of that flag
REMOVEOBJECT_SETS = ("src/event_object_movement.c:1394", "FlagSet(GetObjectEventFlagIdByObjectEventId(objectEventId));")
#: FIX ROUND 3, item 1: the C code that writes flags or vars by a RANGE or a COMPUTED id (not one named constant), measured
#: at the pin by a grep of src/ for FlagSet / FlagClear / VarSet / GetVarPointer / memset on the save flags and vars whose
#: id is not a single FLAG_/VAR_ name. (key, namespace, members, effect, *cites). members: ('all',); ('range', LO, HI)
#: inclusive, the bounds evaluated from include/constants (flags.h, vars.h, opponents.h, rematches.h); ('prefix', P)
#: every name starting with P; ('objects', ((map, local id), ...)) the map.json hide flags of those objects. effect:
#: 'start' (new game: the START state, so never a writer after it), 'daily' (cleared each new day), 'map_entry'
#: (cleared on every map entry), None (a writer this rule cannot evaluate: the name is not SOLE). Names written by C BY
#: NAME (a table entry, a FlagSet(FLAG_X)) are caught by the C-mention scan, not here: the match-call completion flags
#: (src/pokenav_match_call_data.c:1018), the Sootopolis ice vars (src/field_tasks.c:621), the TV vars (src/tv.c:2481).
C_RANGES = [
    ("new game flags", "flag", ("all",), "start",
     ("src/event_data.c:34", "memset(gSaveBlock1Ptr->flags, 0, sizeof(gSaveBlock1Ptr->flags));"),
     ("src/new_game.c:167", "InitEventData();")),
    ("new game vars", "var", ("all",), "start",
     ("src/event_data.c:35", "memset(gSaveBlock1Ptr->vars, 0, sizeof(gSaveBlock1Ptr->vars));")),
    ("daily flags", "flag", ("range", "DAILY_FLAGS_START", "DAILY_FLAGS_END"), "daily",
     ("src/event_data.c:52", "memset(&gSaveBlock1Ptr->flags[DAILY_FLAGS_START / 8], 0, DAILY_FLAGS_SIZE);"),
     ("src/clock.c:44", "ClearDailyFlags();")),
    ("temp flags", "flag", ("range", "TEMP_FLAGS_START", "TEMP_FLAGS_END"), "map_entry",
     ("src/event_data.c:41", "memset(&gSaveBlock1Ptr->flags[TEMP_FLAGS_START / 8], 0, TEMP_FLAGS_SIZE);"),
     ("src/overworld.c:798", "ClearTempFieldEventData();")),
    ("temp vars", "var", ("range", "TEMP_VARS_START", "TEMP_VARS_END"), "map_entry",
     ("src/event_data.c:42", "memset(&gSaveBlock1Ptr->vars[TEMP_VARS_START - VARS_START], 0, TEMP_VARS_SIZE);"),
     ("src/overworld.c:798", "ClearTempFieldEventData();")),
    ("trainer flags", "flag", ("range", "TRAINER_FLAGS_START", "TRAINER_FLAGS_END"), None,
     ("src/battle_setup.c:1249", "FlagSet(GetTrainerAFlag());"),
     ("src/battle_setup.c:1264", "FlagSet(TRAINER_FLAGS_START + trainerId);"),
     ("src/battle_setup.c:1269", "FlagClear(TRAINER_FLAGS_START + trainerId);")),
    ("match call registrations", "flag",
     ("range", "TRAINER_REGISTERED_FLAGS_START", "TRAINER_REGISTERED_FLAGS_START + REMATCH_TABLE_ENTRIES - 1"), None,
     ("src/pokenav_match_call_data.c:1160", "FlagSet(TRAINER_REGISTERED_FLAGS_START + index);"),
     ("src/battle_setup.c:1748", "return TRAINER_REGISTERED_FLAGS_START + i;"),
     ("src/battle_setup.c:1760", "FlagSet(matchCallFlagId);")),
    ("decoration flags", "flag", ("range", "FLAG_DECORATION_1", "FLAG_DECORATION_14"), None,
     ("src/decoration.c:1291", "FlagClear(FLAG_DECORATION_1 + i);"),
     ("src/secret_base.c:605", "FlagClear(FLAG_DECORATION_1 + gSpecialVar_0x8004);"),
     ("src/secret_base.c:649", "FlagSet(flag);")),
    ("hidden item flags", "flag", ("prefix", "FLAG_HIDDEN_ITEM_"), None,
     ("src/field_specials.c:937", "FlagSet(gSpecialVar_0x8004);")),
    ("union room players", "flag", ("range", "FLAG_HIDE_UNION_ROOM_PLAYER_1", "FLAG_HIDE_UNION_ROOM_PLAYER_8"), None,
     ("src/union_room_player_avatar.c:161", "FlagSet(FLAG_HIDE_UNION_ROOM_PLAYER_1 + player_idx);"),
     ("src/union_room_player_avatar.c:166", "FlagClear(FLAG_HIDE_UNION_ROOM_PLAYER_1 + player_idx);")),
    ("frontier symbols", "flag", ("range", "FLAG_SYS_TOWER_SILVER", "FLAG_SYS_PYRAMID_GOLD"), None,
     ("src/frontier_util.c:1922", "FlagSet(FLAG_SYS_TOWER_SILVER + facility * 2);"),
     ("src/frontier_util.c:1924", "FlagSet(FLAG_SYS_TOWER_GOLD + facility * 2);")),
    ("object graphics vars", "var", ("range", "VAR_OBJ_GFX_ID_0", "VAR_OBJ_GFX_ID_F"), None,
     ("src/field_specials.c:2772", "VarSet(VAR_OBJ_GFX_ID_F - i, OBJ_EVENT_GFX_BRENDAN_NORMAL);"),
     ("src/union_room_player_avatar.c:171", "VarSet(VAR_OBJ_GFX_ID_0 + leaderId, gfxId);"),
     ("src/secret_base.c:603", "VarSet(gSpecialVar_Result, gDecorations[decorations[i]].tiles[0]);"),
     ("src/decoration.c:1298", "VarSet(")),
    # every C caller of RemoveObjectEventByLocalIdAndMap (event_object_movement.c:1394 sets the object's hide flag)
    # other than the removeobject command: the camera object has no map.json flag (field_specials.c:1266), secret base
    # decorations carry decoration flags (secret_base.c:645), union room players the union room flags (:181)
    ("objects removed by C", "flag", ("objects", (("MAP_BIRTH_ISLAND_EXTERIOR", "LOCALID_BIRTH_ISLAND_EXTERIOR_ROCK"),
                                                  ("MAP_BATTLE_FRONTIER_BATTLE_TOWER_LOBBY",
                                                   "LOCALID_TOWER_LOBBY_REPORTER"))), None,
     ("src/field_effect.c:3734", "RemoveObjectEventByLocalIdAndMap(tLocalId, tMapNum, tMapGroup);"),
     ("data/maps/BirthIsland_Exterior/scripts.inc:69", "setfieldeffectargument 0, LOCALID_BIRTH_ISLAND_EXTERIOR_ROCK"),
     ("src/tv.c:3445", "RemoveObjectEventByLocalIdAndMap(LOCALID_TOWER_LOBBY_REPORTER")),
]
#: what a C range's effect makes of a gift whose only blockers it re-arms (a 'start' range never re-arms)
RANGE_DECIDES = {"daily": "daily", "map_entry": "repeatable"}
#: FIX ROUND 3, item 1: C lines that NAME a flag/var and were read to be a pure READ, so the sole-writer scan may skip
#: them: {name: [(path:line, token)]}. Every other C mention keeps the name from being SOLE ("named by C code"). Empty
#: by choice: no gift's value needs one at the pin (the Exp Share's src/pokenav_match_call_data.c:183 is a table READ,
#: but nothing proves the table is never written through, so the record stays `unknown`, worded 'named by C code').
CITED_READS = {}
#: FIX ROUND 3, item 1: a blocking flag/var with OTHER writers is re-armed in solo play as these hand-read entries say
#: (path:line + token, checked by check_cites): {name: (repeat, words or None, *cites)}. The words join `when`.
_SHOAL_WORDS = ("each new day it comes back, but only once you talk to the Shell Bell man in the cave's entrance room "
                "(he puts the day's shoal items back)")
_SHOAL_CITES = (("src/clock.c:53", "SetShoalItemFlag(daysSince);"),
                ("src/field_specials.c:1420", "FlagSet(FLAG_SYS_SHOAL_ITEM);"),
                ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:22",
                 "call_if_set FLAG_SYS_SHOAL_ITEM, ShoalCave_LowTideEntranceRoom_EventScript_ResetShoalItems"),
                ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:90", "clearflag FLAG_SYS_SHOAL_ITEM"))
REARM = {
    "FLAG_RECEIVED_SHOAL_SALT_1": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                   ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:82",
                                    "clearflag FLAG_RECEIVED_SHOAL_SALT_1")),
    "FLAG_RECEIVED_SHOAL_SALT_2": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                   ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:83",
                                    "clearflag FLAG_RECEIVED_SHOAL_SALT_2")),
    "FLAG_RECEIVED_SHOAL_SALT_3": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                   ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:84",
                                    "clearflag FLAG_RECEIVED_SHOAL_SALT_3")),
    "FLAG_RECEIVED_SHOAL_SALT_4": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                   ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:85",
                                    "clearflag FLAG_RECEIVED_SHOAL_SALT_4")),
    "FLAG_RECEIVED_SHOAL_SHELL_1": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                    ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:86",
                                     "clearflag FLAG_RECEIVED_SHOAL_SHELL_1")),
    "FLAG_RECEIVED_SHOAL_SHELL_2": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                    ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:87",
                                     "clearflag FLAG_RECEIVED_SHOAL_SHELL_2")),
    "FLAG_RECEIVED_SHOAL_SHELL_3": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                    ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:88",
                                     "clearflag FLAG_RECEIVED_SHOAL_SHELL_3")),
    "FLAG_RECEIVED_SHOAL_SHELL_4": ("daily", _SHOAL_WORDS, *_SHOAL_CITES,
                                    ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:89",
                                     "clearflag FLAG_RECEIVED_SHOAL_SHELL_4")),
    # the contest hall runs its prize script again on every contest you enter: the reception sets the state back to 1
    # (contest_hall.inc:181, EnterMon) and the hall's map_script_2 runs the contest on 1 (ContestHall/scripts.inc:58)
    "VAR_CONTEST_HALL_STATE": ("repeatable", None,
                               ("data/scripts/contest_hall.inc:181", "setvar VAR_CONTEST_HALL_STATE, 1"),
                               ("data/maps/ContestHall/scripts.inc:58",
                                "map_script_2 VAR_CONTEST_HALL_STATE, 1, ContestHall_EventScript_Contest")),
}


# ---------------------------------------------------------------- the script sources
def include_closure(d, root):
    """Every data/ file the assembler reads from `root` through `.include`, in a fixed breadth-first order."""
    out, todo = [], [root]
    while todo:
        rel = todo.pop(0)
        if rel in out:
            continue
        out.append(rel)
        for m in re.finditer(r'^\s*\.include\s+"([^"]+)"', d.read(rel), re.M):
            if m.group(1).startswith("data/") and m.group(1) not in out:
                todo.append(m.group(1))
    return out


def script_files(d):
    """(the files the event scripts assemble from, the mystery-gift files). Text-only files (data/text/) are left out:
    they hold `.string` labels only."""
    ev = include_closure(d, EVENT_ROOT)
    mg = [f for f in include_closure(d, GIFT_ROOT) if f != GIFT_ROOT and f not in ev]
    return [f for f in ev if not f.startswith("data/text/")], [f for f in mg if not f.startswith("data/text/")]


def check_sources(d, event_files, gift_files):
    """GUARD: every map scripts.inc and every data/scripts/*.inc is assembled by event_scripts.s or mystery_gift.s.
    WHY: a file in neither would be silently ignored, and its gifts would be absent with nothing saying so."""
    want = ["data/maps/%s/scripts.inc" % f for f in ew.map_folders(d)
            if os.path.isfile(os.path.join(d.root, "data", "maps", f, "scripts.inc"))]
    want += ew.library_scripts(d)
    lost = sorted(set(want) - set(event_files) - set(gift_files))
    if lost:
        raise Refused("script files neither data/event_scripts.s nor data/mystery_gift.s includes: %s" % lost[:5])


def strip_comment(line):
    if line.lstrip().startswith(".string"):
        return line.rstrip()
    line = re.sub(r"/\*.*?\*/", "", line)
    return line.split("@", 1)[0].split("//", 1)[0].rstrip()


def vanilla_lines(text, rel):
    """[(line number, code)] with comments dropped and every line a vanilla build does not assemble blanked (R-3):
    `#ifdef BUGFIX|UBFIX` blocks drop their first side and keep `#else`; `#ifndef` keeps its first side.
    GUARD: any other conditional refuses (its vanilla side is unknown)."""
    out, stack = [], []
    for i, line in enumerate(text.split("\n"), 1):
        m = re.match(r"\s*#\s*(\w+)\s*(\w*)", line)
        if m and not line.lstrip().startswith(".string"):
            kw, sym = m.groups()
            if kw == "include" or kw == "define":
                out.append((i, ""))
                continue
            if kw in ("ifdef", "ifndef"):
                if sym not in FIX_SYMBOLS:
                    raise Refused("%s:%d: a conditional on %r (only %s are known)" % (rel, i, sym, FIX_SYMBOLS))
                stack.append(kw == "ifndef")
            elif kw == "else" and stack:
                stack[-1] = not stack[-1]
            elif kw == "endif" and stack:
                stack.pop()
            else:
                raise Refused("%s:%d: an unknown preprocessor line %r" % (rel, i, line.strip()))
            out.append((i, ""))
            continue
        out.append((i, "" if not all(stack) else strip_comment(line)))
    if stack:
        raise Refused("%s: an #ifdef without its #endif" % rel)
    return out


LABEL_RE = re.compile(r"^([A-Za-z_]\w*)::?$")


def parse_labels(d, files):
    """{label: {file, line, body: [(line, code)], next}} over `files`. GUARD: a label defined twice refuses."""
    labels = {}
    for rel in files:
        prev = None
        for ln, code in vanilla_lines(d.read(rel), rel):
            m = LABEL_RE.match(code)
            if m:
                name = m.group(1)
                if name in labels:
                    raise Refused("label %s defined twice: %s:%d and %s:%d" % (name, labels[name]["file"],
                                                                               labels[name]["line"], rel, ln))
                labels[name] = {"file": rel, "line": ln, "body": [], "next": None}
                if prev is not None:
                    labels[prev]["next"] = name
                prev = name
            elif prev is not None and code.strip():
                labels[prev]["body"].append((ln, code.strip()))
    return labels


def cmd(code):
    """(mnemonic, [args]) of one code line."""
    m = re.match(r"(\.?\w+)\s*(.*)$", code)
    if not m:
        return "", []
    rest = m.group(2).strip()
    return m.group(1), ([a.strip() for a in rest.split(",")] if rest else [])


def operand(args):
    """{operand: X}, or {dev: {operand: X}} when X is a flag or var name (R-4: names only under `dev`)."""
    x = args[0] if args else None
    return {"dev": {"operand": x}} if x and NAME_RE.search(x) else {"operand": x}


def ref(lab, ln):
    return "%s:%d" % (lab["file"], ln)


# ---------------------------------------------------------------- the reference graph
def build_edges(labels):
    """{label: [(target, kind, line, cond, switch_line)]}. kind: goto, call, goto_if, call_if, case, map_script, ref
    (any other token naming a label: a table entry, a post-defeat label), fall (no terminator: runs into the next).
    cond: ("flag", F, is_set) | ("var", V, op, value) | ("trainer", T, defeated) | None."""
    edges = {}
    for name, lab in labels.items():
        out, sw_var, sw_line = [], None, None
        for ln, code in lab["body"]:
            mn, args = cmd(code)
            if mn.startswith("."):
                for tok in re.findall(r"[A-Za-z_]\w*", " ".join(args)) if mn != ".string" else []:
                    if tok in labels:
                        out.append((tok, "ref", ln, None, None))
                continue
            if mn == "switch":
                sw_var, sw_line = (args[0] if args else None), ln
                continue
            if mn == "case" and len(args) == 2 and args[1] in labels:
                out.append((args[1], "case", ln, ("var", sw_var, "eq", args[0]), sw_line))
                continue
            mc = re.match(r"(goto|call)_if_(set|unset|lt|eq|gt|le|ge|ne|defeated|not_defeated)$", mn)
            if mc and args and args[-1] in labels:
                op = mc.group(2)
                if op in ("set", "unset"):
                    c = ("flag", args[0], op == "set")
                elif op in ("defeated", "not_defeated"):
                    c = ("trainer", args[0], op == "defeated")
                else:
                    c = ("var", args[0], op, args[1] if len(args) > 2 else None)
                out.append((args[-1], mc.group(1) + "_if", ln, c, None))
                continue
            if mn == "map_script_2" and len(args) == 3 and args[2] in labels:
                out.append((args[2], "map_script", ln, ("var", args[0], "eq", args[1]), None))
                continue
            if mn.startswith("trainerbattle") and ew.battle_trainer(args):
                for tok in args:
                    if tok in labels:  # the post-defeat script: runs once, on the first win
                        out.append((tok, "battle", ln, ("trainer", ew.battle_trainer(args), True), None))
                continue
            for tok in re.findall(r"[A-Za-z_]\w*", " ".join(args)):
                if tok in labels:
                    out.append((tok, mn if mn in ("goto", "call") else "ref", ln, None, None))
        if lab["next"] and falls_through(lab):
            out.append((lab["next"], "fall", lab["body"][-1][0] if lab["body"] else lab["line"], None, None))
        edges[name] = out
    return edges


def falls_through(lab):
    """True when the label runs on into the next label: it has no body (an alias of the next label), or its LAST
    statement is a command that is not a terminator. WHY (fix round 1, F2): a body that ends in a directive (`.2byte 0`,
    `.byte 0`, `.string`...) is data, and a `map_script` / `map_script_2` table is a table: neither is executed, so
    neither falls into the next label. Round 0 skipped directives when finding the last statement, so ~160
    `map_script_2` tables 'fell' into the script after them; that phantom path erased HM Surf's real trigger
    (PetalburgCity_WallysHouse/scripts.inc:16) and gave the Route 114 berry man a `map_script` giver."""
    if not lab["body"]:
        return True
    last = lab["body"][-1][1]
    if last.startswith(".") or any(cmd(c)[0] in ("map_script", "map_script_2") for _, c in lab["body"]):
        return False
    return cmd(last)[0] not in TERMINATORS


def closure(edges, start, kinds=None):
    """Every label reachable from `start` (itself included). GUARD: more than MAX_CLOSURE labels refuses."""
    seen, todo = set(), [start]
    while todo:
        lab = todo.pop()
        if lab in seen or lab not in edges:
            continue
        seen.add(lab)
        if len(seen) > MAX_CLOSURE:
            raise Refused("the closure from %s passed %d labels" % (start, MAX_CLOSURE))
        for tgt, kind, _, _, _ in edges[lab]:
            if tgt not in seen and (kinds is None or kind in kinds):
                todo.append(tgt)
    return seen


# ---------------------------------------------------------------- the roots
def read_maps(d):
    """[(folder, map.json object)] for every map folder."""
    return [(f, json.loads(d.read("data/maps/%s/map.json" % f))) for f in ew.map_folders(d)]


def map_roots(maps, labels):
    """[{label, map, giver, cond, object_flag}] for every map.json event script and every map's `<name>_MapScripts`."""
    roots = []
    for folder, j in maps:
        mid = j["id"]
        for n, o in enumerate(j.get("object_events") or [], 1):
            roots.append({"label": o.get("script"), "map": mid, "cond": None, "object_flag": o.get("flag"),
                          "giver": {"map": mid, "kind": "object", "object": n, "local_id": o.get("local_id", n),
                                    "graphics": o.get("graphics_id")}})
        for c in j.get("coord_events") or []:
            if c.get("type") == "trigger":
                roots.append({"label": c.get("script"), "map": mid, "object_flag": None,
                              "cond": ("var", c.get("var"), "eq", str(c.get("var_value"))),
                              "giver": {"map": mid, "kind": "coord"}})
        for b in j.get("bg_events") or []:
            if b.get("type") == "sign":
                roots.append({"label": b.get("script"), "map": mid, "cond": None, "object_flag": None,
                              "giver": {"map": mid, "kind": "sign"}})
        ms = (j.get("shared_scripts_map") or j["name"]) + "_MapScripts"
        if ms in labels:
            roots.append({"label": ms, "map": mid, "cond": None, "object_flag": None,
                          "giver": {"map": mid, "kind": "map_script"}})
    return roots


def check_map_scripts(roots, labels):
    """GUARD: every map.json script names a label (a raw `0x0` / `0` / empty script is no script). WHY: an event whose
    label the graph lacks would drop every gift it reaches without a word. Also marks each object root whose flag
    EventScript_ResetAllMapFlags sets at new game (`hidden`: it starts hidden)."""
    reset = hidden_at_start(labels)
    for r in roots:
        r["hidden"] = r["giver"]["kind"] == "object" and r["object_flag"] in reset
    bad = sorted({"%s %s" % (r["map"], r["label"]) for r in roots
                  if r["label"] not in labels and str(r["label"]) not in ("0x0", "0", "", "None")})
    if bad:
        raise Refused("map.json scripts that are no label of the event scripts: %s" % bad[:5])
    return [r for r in roots if r["label"] in labels]


def c_roots(d, labels):
    """{label: 'file:line'} of the first C line (src/, include/) naming each label: the labels C runs directly."""
    hits = {}
    for top in ("src", "include"):
        base = os.path.join(d.root, top)
        for dirpath, _, names in sorted(os.walk(base)):
            for fn in sorted(names):
                if not fn.endswith((".c", ".h")):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), d.root).replace("\\", "/")
                text = d.read(rel)
                for tok in sorted(set(re.findall(r"[A-Za-z_]\w*", text)) & set(labels)):
                    if tok not in hits:
                        hits[tok] = "%s:%d" % (rel, ew.line_of(text, re.search(r"\b%s\b" % tok, text).start()))
    return hits


def c_texts(d):
    """{rel: text} of every src/**/*.c and *.h, read once per Decomp."""
    if getattr(d, "_c_texts", None) is None:
        out = {}
        for dirpath, _, names in sorted(os.walk(os.path.join(d.root, "src"))):
            for fn in sorted(names):
                if fn.endswith((".c", ".h")):
                    rel = os.path.relpath(os.path.join(dirpath, fn), d.root).replace("\\", "/")
                    out[rel] = d.read(rel)
        d._c_texts = out
    return d._c_texts


def c_name_index(d):
    """{FLAG_/VAR_ name: [(rel, line, line text)]} of every src/ C line naming it, built once per Decomp."""
    if getattr(d, "_c_names", None) is None:
        out = {}
        for rel, text in sorted(c_texts(d).items()):
            for n, line in enumerate(text.split("\n"), 1):
                for name in set(re.findall(r"\b(?:FLAG|VAR)_\w+", line)):
                    out.setdefault(name, []).append((rel, n, line))
        d._c_names = out
    return d._c_names


def c_function(d, fn):
    """(rel, line, body text) of the C function `fn(void)`, or None (memoised per Decomp)."""
    memo = d.__dict__.setdefault("_c_funcs", {})
    if fn not in memo:
        memo[fn] = None
        for rel, text in c_texts(d).items():
            if fn not in text:
                continue
            m = re.search(r"^[\w \*]*\b%s\(void\)\s*\{" % re.escape(fn), text, re.M)
            if m:
                memo[fn] = (rel, ew.line_of(text, m.start()), text[m.end() - 1:balanced(text, m.end() - 1)])
                break
    return memo[fn]


def constant_return(body):
    """The constant a C body always returns (`{ return FALSE; }` with comments), else None."""
    m = re.fullmatch(r"\{\s*return\s+(TRUE|FALSE|\d+)\s*;\s*\}", re.sub(r"//[^\n]*|/\*.*?\*/", "", body, flags=re.S))
    return None if not m else {"TRUE": 1, "FALSE": 0}.get(m.group(1), None if not m.group(1).isdigit()
                                                                 else int(m.group(1)))


def prune_constant_branches(d, labels, edges):
    """Drop a branch on VAR_RESULT that a `specialvar VAR_RESULT, Fn` just before it can never take, because Fn's C
    body is one constant `return` (ContestLobby's debug branch: IsContestDebugActive returns FALSE, so its additem is
    dead code the recon calls 'functionally unused'). Returns [(label, line, Fn, 'file:line', the cut target)]."""
    pruned = []
    ops = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b, "lt": lambda a, b: a < b, "ge": lambda a, b: a >= b,
           "gt": lambda a, b: a > b, "le": lambda a, b: a <= b}
    for name, outs in edges.items():
        keep = []
        for e in outs:
            tgt, kind, ln, c, _ = e
            if kind in ("goto_if", "call_if") and c and c[0] == "var" and c[1] == "VAR_RESULT" and c[2] in ops:
                prev = [cmd(code) for l2, code in labels[name]["body"] if l2 < ln]
                last = prev[-1] if prev else ("", [])
                fn = last[1][1] if last[0] == "specialvar" and len(last[1]) == 2 and last[1][0] == "VAR_RESULT" \
                    else None
                found = c_function(d, fn) if fn else None
                k = constant_return(found[2]) if found else None
                val = {"TRUE": 1, "FALSE": 0}.get(c[3], int(c[3]) if (c[3] or "").isdigit() else None)
                if k is not None and val is not None and not ops[c[2]](k, val):
                    pruned.append((name, ln, fn, "%s:%d" % (found[0], found[1]), tgt))
                    continue
            keep.append(e)
        edges[name] = keep
    return pruned


# ---------------------------------------------------------------- conditions
NEG ={"eq": "ne", "ne": "eq", "lt": "ge", "ge": "lt", "gt": "le", "le": "gt"}


#: include/constants/global.h:113-114 (MALE 0, FEMALE 1): a gender result spelt as a number
GENDER_NUM = {"MALE": "0", "FEMALE": "1"}


def restores(lab, var, value):
    """Does a called label end by setting `var` back to `value`, the value its call_if_eq tested (so the result is the
    same after the call)? Birch's lab: `call_if_eq VAR_RESULT, MALE, ...MayGivePokeBalls`, whose body ends
    `setvar VAR_RESULT, 0` / `return` (LittlerootTown_ProfessorBirchsLab/scripts.inc:507, :522-523)."""
    body = lab["body"]
    if not body or cmd(body[-1][1])[0] != "return":
        return False
    last = [cmd(c)[1] for _, c in body if cmd(c)[0] == "setvar" and cmd(c)[1][:1] == [var]]
    if not last or len(last[-1]) < 2:
        return False
    return GENDER_NUM.get(last[-1][1], last[-1][1]) == GENDER_NUM.get(value, value)


#: the call_if forms whose conditions are each other's opposite (exactly one of a pair on one flag / var value runs)
OPPOSITE_CALL_IF = {("call_if_set", "call_if_unset"), ("call_if_eq", "call_if_ne"), ("call_if_lt", "call_if_ge"),
                    ("call_if_gt", "call_if_le")}


def opposite_call_ifs(a, b):
    """Are command lines a = (mnemonic, args) and b two call_ifs on the SAME flag / var and value with OPPOSITE
    conditions (so exactly one of them runs)? Fix round 3, item 5."""
    (ma, xa), (mb, xb) = a, b
    if (ma, mb) not in OPPOSITE_CALL_IF and (mb, ma) not in OPPOSITE_CALL_IF:
        return False
    n = 1 if ma in ("call_if_set", "call_if_unset") else 2
    return len(xa) == n + 1 and len(xb) == n + 1 and xa[:n] == xb[:n]


def negate(c):
    if c[0] in ("flag", "trainer"):
        return (c[0], c[1], not c[2])
    return ("var", c[1], NEG.get(c[2], c[2]), c[3])


class Graph:
    """The labels, their edges, predecessors, roots and owners: one build per decomp."""

    def __init__(self, d, labels, edges, roots, croots):
        self.d, self.labels, self.edges, self.roots, self.croots = d, labels, edges, roots, croots
        self.pruned = prune_constant_branches(d, labels, edges)
        self.preds = {}
        for src, outs in edges.items():
            for tgt, kind, ln, c, sw in outs:
                self.preds.setdefault(tgt, []).append((src, kind, ln, c, sw))
        self.owner_roots = {}  # label -> [root index]
        self.c_owner = {}      # label -> sorted C refs
        self.max_closure = 0
        for i, r in enumerate(roots):
            cl = closure(edges, r["label"])
            self.max_closure = max(self.max_closure, len(cl))
            for lab in cl:
                self.owner_roots.setdefault(lab, []).append(i)
        for lab, where in sorted(croots.items()):
            cl = closure(edges, lab)
            self.max_closure = max(self.max_closure, len(cl))
            for x in cl:
                self.c_owner.setdefault(x, set()).add(where)
        self.root_at = {}
        for i, r in enumerate(roots):
            self.root_at.setdefault(r["label"], []).append(i)
        self._memo = {}

    def reachable(self, lab):
        return lab in self.owner_roots or lab in self.c_owner

    def producer(self, lab, upto, var, depth=0, stack=()):
        """What last wrote `var` before line `upto` of `lab`: ('cmd', mnemonic) | ('special', name) |
        ('const', value) | ('copy', var); when the label does not write it, the one writer every predecessor agrees
        on (a few labels back); else None."""
        for ln, code in reversed([b for b in self.labels[lab]["body"] if b[0] < upto]):
            mn, args = cmd(code)
            if mn == "specialvar" and args and args[0] == var:
                return ("special", args[1])
            if var == "VAR_RESULT" and mn == "special" and args and special_sets_result(self.d, args[0]):
                # fix round 2 (item 6): the scrolling menu is a menu; another special writing the result is its
                # producer (the Favor Lady's bag menu, the size records)
                return ("cmd", "multichoice") if args[0] == "ShowScrollableMultichoice" else ("special", args[0])
            if mn == "setvar" and args and args[0] == var:
                return ("const", args[1])
            if mn == "copyvar" and args and args[0] == var:
                return ("copy", args[1])
            if var == "VAR_RESULT" and mn in POSSESSION:
                # fix round 2 (item 3): a possession check, with what it checks and how many
                return ("cmd", mn, args[0] if args else None, args[1] if len(args) > 1 else "1")
            if var == "VAR_RESULT" and (mn in ("random", "checkplayergender", "yesnobox") or "multichoice" in mn
                                        or mn in ROOM_PRODUCERS or (mn == "msgbox" and "MSGBOX_YESNO" in args)):
                return ("cmd", "yesno" if mn in ("msgbox", "yesnobox") else
                        "multichoice" if "multichoice" in mn else mn)
            if (mn == "call" or mn.startswith("call_if_")) and args and args[-1] in self.labels and \
                    self.writes_var(args[-1], var):
                # fix round 2: a called label that writes the var decides it. A call taken only on a ROOM result
                # refines that result (the Shell Bell's CheckSpaceWillBeFreed, ShoalCave_LowTideEntranceRoom:30-31);
                # any other is unknown (the Fan Club's VAR_TEMP_1, set by the call_if bodies, scripts.inc:43-49)
                if mn.startswith("call_if_") and var == "VAR_RESULT" and args[0] == "VAR_RESULT":
                    inner = self.producer(lab, ln, var, depth, stack)
                    if inner and inner[0] == "cmd" and inner[1] in ROOM_PRODUCERS:
                        return inner
                if mn == "call_if_eq" and args[0] == var and len(args) == 3 and restores(self.labels[args[-1]], var,
                                                                                       args[1]):
                    continue  # the callee puts back the value it was called on (Birch's lab :522 / :530)
                # FIX ROUND 3, item 5: the LATEST producer is the callee's own (its body read alone: depth 4 stops the
                # walk into its callers). A plain `call` hands it on; a `call_if` does too when the line before it is
                # the OPPOSITE call_if (exactly one of the two runs) and both callees end in the same producer. Cozmo:
                # `call_if_unset FLAG_TEMP_2, ...NoticeMeteorite` / `call_if_set FLAG_TEMP_2, ...AskForMeteorite`
                # both end in a MSGBOX_YESNO (FallarborTown_CozmosHouse/scripts.inc:15-16, :31, :35), so the test
                # after them reads the player's ANSWER, not the earlier checkitem ITEM_METEORITE (:8).
                inner = self.callee_producer(args[-1], var)
                if mn == "call" and inner:
                    return inner
                prev = [cmd(c) for l2, c in self.labels[lab]["body"] if l2 < ln]
                if inner and prev and opposite_call_ifs(prev[-1], (mn, args)) and \
                        self.callee_producer(prev[-1][1][-1], var) == inner:
                    return inner
                return ("call", args[-1])
        if depth >= 4:
            return None
        found = set()
        for src, kind, ln, _, _ in self.preds.get(lab, []):
            if kind in ("goto", "fall", "goto_if", "case", "call", "call_if") and src not in stack \
                    and self.reachable(src):
                found.add(self.producer(src, ln, var, depth + 1, stack + (lab,)))
        if len(found) > 1 and all(f and f[0] == "special" for f in found):
            # fix round 2: two specials, one per way in (the Quiz Lady's question / answer screens, lilycove_lady.inc
            # :190 / :195, both feed :185-186): the result comes from one of them
            return ("special", "|".join(sorted(f[1] for f in found)))
        return found.pop() if len(found) == 1 else None

    def callee_producer(self, lab, var):
        """Fix round 3, item 5: the producer of `var` when the called label `lab` returns, read from its own body ONLY
        when it is one straight run ending in `return` (no branch, call, case or jump: then its last producer is the
        one the caller sees); else None."""
        if lab not in self.labels:
            return None
        body = self.labels[lab]["body"]
        if not body or cmd(body[-1][1])[0] != "return" or any(
                kind in ("goto", "call", "goto_if", "call_if", "case", "fall") for _, kind, *_ in self.edges[lab]):
            return None
        return self.producer(lab, 10 ** 9, var, 4, ())

    def paths_to(self, lab, upto, depth=0, stack=()):
        """The PATHS into line `upto` of `lab`: a tuple of frozensets, one per distinct path from a root, each holding
        the tests that path passes ((cond, how) pairs) and markers: ('@guard', 'battle', T) entered through T's
        post-defeat script (runs once), ('@guard', 'coord', V) a coord trigger on var V, ('@hidden', F) the root
        object starts hidden, ('@c', ref) reached from C, ('@deep',) past MAX_DEPTH, ('@collapsed',) more than
        MAX_PATHS paths merged into their common tests. Inside the label: a goto_if it survives is negated, and a
        trainerbattle before the line means that trainer is already defeated.
        FIX ROUND 2: a predecessor skipped because it is already on the way (a loop: 'choose a different one' goes back
        to the menu) yields NO path through it, never an empty one: round 1 turned a label whose every predecessor was
        on the stack into an empty path, a phantom 'no condition' (the Glass Workshop's and the Favor Lady's menus loop).
        A result that depended on the stack or the depth bound is not memoised."""
        return self._paths(lab, upto, depth, stack)[0]

    def _paths(self, lab, upto, depth, stack):
        """(paths, cut): cut is True when a loop or the depth bound shaped the answer (then it is not memoised)."""
        key = (lab, upto)
        if key in self._memo:
            return self._memo[key], False
        own = set()
        for ln, code in self.labels[lab]["body"]:
            if ln >= upto:
                break
            mn, args = cmd(code)
            if mn.startswith("trainerbattle") and mn not in ew.REMATCH_MACROS and ew.battle_trainer(args):
                own.add((("trainer", ew.battle_trainer(args), True), "battle"))
            for tgt, kind, eln, c, _ in self.edges[lab]:
                if eln == ln and kind == "goto_if" and c is not None:
                    own.add((negate(c), self._where(lab, ln, c)))
        entries = []
        for i in self.root_at.get(lab, []):
            r = self.roots[i]
            e = set()
            if r["cond"]:
                e |= {(r["cond"], "coord"), ("@guard", "coord", r["cond"][1])}
            if r["giver"]["kind"] == "object" and r["object_flag"] not in (None, "0"):
                # fix round 2 (item 2): the giver object is there only while its map.json hide flag is clear: a
                # trigger-level condition of every path that starts at it
                e.add((("flag", r["object_flag"], False), "object"))
            if r.get("hidden"):
                e.add(("@hidden", r["object_flag"]))
            entries.append(frozenset(e))
        if lab in self.croots:
            entries.append(frozenset({("@c", self.croots[lab])}))
        cut, live = False, [p for p in self.preds.get(lab, []) if self.reachable(p[0])]
        if depth < MAX_DEPTH:
            for src, kind, ln, c, sw in live:
                if src in stack:
                    cut = True
                    continue
                add = set()
                if c is not None and kind in ("goto_if", "call_if", "case", "map_script"):
                    add.add((c, self._where(src, sw if kind == "case" else ln, c)))
                if kind == "battle":
                    add |= {(c, "battle"), ("@guard", "battle", c[1])}
                sub, sub_cut = self._paths(src, ln, depth + 1, stack + (lab,))
                cut = cut or sub_cut
                for p in sub:
                    entries.append(frozenset(p | add))
        elif live:
            cut = True
            entries.append(frozenset({("@deep",)}))
        if not entries and not live:
            entries = [frozenset()]  # a label nothing reaches: no test (it is dead, or a root without a condition)
        entries = sorted(set(entries), key=lambda p: sorted(map(repr, p)))
        if len(entries) > MAX_PATHS:
            entries = [frozenset(set.intersection(*[set(p) for p in entries]) | {("@collapsed",)})]
        res = tuple(frozenset(p | own) for p in entries)
        if not cut:
            self._memo[key] = res
        return res, cut

    def writes_var(self, lab, var):
        """Does the forward closure of `lab` write `var` (for VAR_RESULT: any command producing a result)?"""
        key = ("writes", lab, var)
        if key not in self._memo:
            hit = False
            for x in closure(self.edges, lab, kinds=("goto", "call", "goto_if", "call_if", "case", "fall")):
                for _, code in self.labels[x]["body"]:
                    mn, args = cmd(code)
                    if (args[:1] == [var] and mn in ("setvar", "addvar", "subvar", "copyvar", "specialvar")) or \
                            (var == "VAR_RESULT" and result_writer(self, mn, args)):
                        hit = True
            self._memo[key] = hit
        return self._memo[key]

    def _where(self, lab, ln, c):
        """How a var test's value was produced: a chooser word ('gender', 'random'...), 'room' (bag/party room),
        'have:<cmd>:<item>:<count>' (a possession check, fix round 2), 'special:<Fn>' (a special's result), 'answer'
        (a yes/no question: the player's own reply, not game state), 'const', or the test's own ref."""
        if c[0] == "var" and c[1] is not None:
            if c[1] in CHOOSER_OF:
                return CHOOSER_OF[c[1]]
            p = self.producer(lab, ln, c[1])
            if p and p[0] == "cmd" and p[1] in ROOM_PRODUCERS:
                return "room"
            if p and p[0] == "cmd" and p[1] in POSSESSION:
                return "have:%s:%s:%s" % p[1:4]
            if p and p[0] == "cmd" and p[1] == "yesno":
                return "answer"
            if p and p[0] == "cmd" and p[1] in CHOOSER_OF:
                return CHOOSER_OF[p[1]]
            if p and p[0] == "special":
                return "special:" + p[1]
            if p and p[0] == "const":
                return "const"
        return ref(self.labels[lab], ln)

    def forward(self, lab):
        """The gift's own continuation: labels reached by goto/call/fall/branches (not texts or tables)."""
        return closure(self.edges, lab, kinds=("goto", "call", "goto_if", "call_if", "case", "fall"))


def badge_words(flag, is_set):
    m = re.fullmatch(r"FLAG_BADGE0(\d)_GET", flag)
    if m:
        return ("after badge %s" if is_set else "before badge %s") % m.group(1)
    if flag == "FLAG_SYS_GAME_CLEAR":
        return "after entering the Hall of Fame" if is_set else "before entering the Hall of Fame"
    return None


def cond_text(c):
    if c[0] == "flag":
        return "%s %s" % (c[1], "set" if c[2] else "unset")
    if c[0] == "trainer":
        return "%s %s" % (c[1], "defeated" if c[2] else "not defeated")
    return "%s %s %s" % (c[1], c[2], c[3])


# ---------------------------------------------------------------- values
class Values:
    """Resolves the item a `giveitem VAR_*` / `additem VAR_*` line gives (see the module docstring)."""

    def __init__(self, d, g):
        self.d, self.g = d, g
        self.items = item_ids(d)
        self.item_of = {}
        for k, v in self.items.items():
            if k.startswith("ITEM_") and v not in self.item_of:
                self.item_of[v] = k
        self.decor = parse_defines(d.read("include/constants/decorations.h"))
        self._c = None

    def num(self, tok):
        if re.fullmatch(r"\d+", tok or ""):
            return int(tok)
        for table in (self.items, self.decor):
            if tok in table:
                return table[tok]
        raise KeyError(tok)

    def c_text(self):
        return c_texts(self.d)

    def c_special(self, fn, var):
        """(items, ref, why) of a C special: its body must index a `static const u16` array of ITEM_ constants that
        lands in `var` (gSpecialVar_0x800N = arr[...], or a specialvar's return of arr[...])."""
        found = c_function(self.d, fn)
        if found is None:
            return None, None, "the C special %s was not found" % fn
        rel, line, body = found
        sv = re.search(r"gSpecialVar_0x%s\s*=\s*(\w+)\s*\[" % var[-4:], body) if var.startswith("VAR_0x") else None
        arr = sv.group(1) if sv else None
        if arr is None:
            ret = re.search(r"(\w+)\s*=\s*(s\w+)\s*\[[^\]]*\];(?:.|\n)*?return\s+\1\s*;", body)
            arr = ret.group(2) if ret else None
        if arr is None:
            ret = re.search(r"return\s+(s\w+)\s*\[", body)
            arr = ret.group(1) if ret else None
        if arr is None:
            return None, "%s:%d" % (rel, line), "set at runtime by the C special %s (no item table)" % fn
        for rel2, t2 in self.c_text().items():
            am = re.search(r"static const u16 %s\s*\[[^\]]*\]\s*=\s*\{" % arr, t2) if arr in t2 else None
            if am:
                body2 = t2[am.end() - 1:balanced(t2, am.end() - 1)]
                return sorted(set(re.findall(r"\bITEM_\w+", body2)) - {"ITEM_NONE"}), \
                    "%s:%d" % (rel2, ew.line_of(t2, am.start())), None
        return None, "%s:%d" % (rel, line), "the C table %s was not found" % arr

    def resolve(self, lab, upto, var, depth=0, stack=()):
        """[(value, ref, chooser)] the line may give; ('unknown', ref, why) for a writer that cannot be resolved."""
        g = self.g
        if not SCRATCH_VAR.fullmatch(var):
            return self.saved_var(var, depth, stack)
        body = [b for b in g.labels[lab]["body"] if b[0] < upto]
        base = 0
        for ln, code in reversed(body):
            mn, args = cmd(code)
            if not args or (args[0] != var and not (mn == "random" and var == "VAR_RESULT") and mn != "special"):
                continue
            here = ref(g.labels[lab], ln)
            if mn == "addvar":
                base += self.num(args[1])
            elif mn == "random" and var == "VAR_RESULT":
                n = self.num(args[0])
                return [(self.item_of.get(base + i, "unknown"), here, "random") for i in range(n)]
            elif mn == "setvar":
                return [(args[1], here, self.chooser_into(lab, depth, stack))]
            elif mn == "copyvar":
                if SCRATCH_VAR.fullmatch(args[1]):
                    return self.resolve(lab, ln, args[1], depth, stack)
                return self.saved_var(args[1], depth, stack)
            elif mn == "specialvar":
                return self.from_c(args[1], var, here)
            elif mn == "special" and var.startswith("VAR_0x"):
                items, cref, why = self.c_special(args[0], var)
                if items is not None or (why and "no item table" in why and self.writes(args[0], var)):
                    return self.from_c(args[0], var, here)
        if depth >= MAX_DEPTH:
            return [("unknown", ref(g.labels[lab], upto), "deeper than %d labels" % MAX_DEPTH)]
        out = []
        for src, kind, ln, c, sw in g.preds.get(lab, []):
            if src in stack or not g.reachable(src) or kind == "ref":
                continue
            out += self.resolve(src, ln, var, depth + 1, stack + (lab,))
        return out or [("unknown", ref(g.labels[lab], upto), "no writer of the var on any path")]

    def writes(self, fn, var):
        found = c_function(self.d, fn)
        return bool(found and re.search(r"gSpecialVar_0x%s\s*=" % var[-4:], found[2]))

    def from_c(self, fn, var, here):
        items, cref, why = self.c_special(fn, var)
        chooser = CHOOSER_OF.get(fn)
        if items is None:
            return [("unknown", cref or here, why)]
        return [(it, cref, chooser) for it in items]

    def saved_var(self, var, depth, stack):
        """Every writer of a saved var anywhere in the reachable scripts (a value stored on one visit, given later)."""
        if depth >= MAX_DEPTH:
            return [("unknown", None, "deeper than %d labels" % MAX_DEPTH)]
        out = []
        for name, lab in self.g.labels.items():
            if not self.g.reachable(name):
                continue
            for ln, code in lab["body"]:
                mn, args = cmd(code)
                if mn in ("setvar", "copyvar") and len(args) > 1 and args[0] == var:
                    out += self.resolve(name, ln, args[1], depth + 1, stack) if mn == "copyvar" else \
                        [(args[1], ref(lab, ln), None)]
        return out or [("unknown", None, "no writer of the saved var")]

    def chooser_into(self, lab, depth, stack):
        """How the label holding a setvar was chosen: the producer of the switch / branch that leads into it."""
        g = self.g
        for src, kind, ln, c, sw in g.preds.get(lab, []):
            if kind in ("case", "goto_if") and c and c[0] == "var" and c[1]:
                if c[1] in CHOOSER_OF:
                    return CHOOSER_OF[c[1]]
                p = g.producer(src, sw if kind == "case" else ln, c[1])
                if p and p[1] in CHOOSER_OF:
                    return CHOOSER_OF[p[1]]
            if kind in ("goto", "fall") and depth < MAX_DEPTH and src not in stack:
                r = self.chooser_into(src, depth + 1, stack + (lab,))
                if r:
                    return r
        return None


# ---------------------------------------------------------------- items metadata
def tm_hm_lists(d):
    """(['ITEM_TM_FOCUS_PUNCH', ...], ['ITEM_HM_CUT', ...]) in id order: include/item.h builds these names from
    include/constants/tms_hms.h's FOREACH_TM / FOREACH_HM lists (ITEM_TM_<move> = ITEM_TM01 + its index)."""
    t = d.read("include/constants/tms_hms.h")
    out = []
    for which in ("TM", "HM"):
        m = re.search(r"#define FOREACH_%s\(F\)((?:\s*\\\s*F\(\w+\))+)" % which, t)
        if not m:
            raise Refused("include/constants/tms_hms.h has no FOREACH_%s list" % which)
        out.append(["ITEM_%s_%s" % (which, x) for x in re.findall(r"F\((\w+)\)", m.group(1))])
    return out[0], out[1]


def item_ids(d):
    """{ITEM_X or a range name: id}: include/constants/items.h is an enum of the items plus #defines on top of it,
    and the TM/HM names come from tms_hms.h (tm_hm_lists)."""
    text = d.read("include/constants/items.h")
    ids = parse_defines(text, parse_enum_blocks(text))
    tms, hms = tm_hm_lists(d)
    for base, names in (("ITEM_TM01", tms), ("ITEM_HM01", hms)):
        for i, n in enumerate(names):
            ids[n] = ids[base] + i
    return ids


def item_kinds(d):
    """{ITEM_X: 'key_item'} for the key-items pocket (src/data/items.h `.pocket = POCKET_KEY_ITEMS`)."""
    t = d.read("src/data/items.h")
    out = {}
    for m in re.finditer(r"\[(ITEM_\w+)\]\s*=\s*\{", t):
        body = t[m.end() - 1:balanced(t, m.end() - 1)]
        if re.search(r"\.pocket\s*=\s*POCKET_KEY_ITEMS", body):
            out[m.group(1)] = "key_item"
    return out


def kind_of(cmd_name, what, keys):
    if cmd_name != "giveitem":
        return GIFT_CMDS[cmd_name]
    names = [what] if isinstance(what, str) else (what.get("one_of") or [])
    kinds = set()
    for n in names:
        if n.startswith("ITEM_TM"):
            kinds.add("tm")
        elif n.startswith("ITEM_HM"):
            kinds.add("hm")
        else:
            kinds.add(keys.get(n, "item"))
    return kinds.pop() if len(kinds) == 1 else "item"


def tm_hm_items(d):
    """Every TM and HM, in id order (tms_hms.h's lists: 50 TMs, 8 HMs at the pin)."""
    tms, hms = tm_hm_lists(d)
    return tms + hms


# ---------------------------------------------------------------- the build
def build(d, maps_json, names):
    """The parts of items_gifts.json; every guard runs; nothing is written. `names`: trainer symbol -> 'Class Name'
    (slice 1's trainers.json), for the words of a 'trainer defeated' test."""
    event_files, gift_files = script_files(d)
    check_sources(d, event_files, gift_files)
    check_cites(d)
    labels = parse_labels(d, event_files)
    edges = build_edges(labels)
    maps = read_maps(d)
    roots = check_map_scripts(map_roots(maps, labels), labels)
    croots = c_roots(d, labels)
    g = Graph(d, labels, edges, roots, croots)
    vals = Values(d, g)
    keys = item_kinds(d)
    flags_h = d.read("include/constants/flags.h")
    daily = daily_flags(flags_h)
    obj_flag_gifts = {}  # (map, object flag) -> root labels of objects carrying it
    for r in roots:
        if r["giver"]["kind"] == "object" and r["object_flag"] not in (None, "0"):
            obj_flag_gifts.setdefault((r["map"], r["object_flag"]), set()).add(r["label"])

    lines = []  # every watched command line of the event scripts: (label, line, mnemonic, args)
    for name, lab in labels.items():
        for ln, code in lab["body"]:
            mn, args = cmd(code)
            if mn in WATCHED:
                lines.append((name, ln, mn, args))
    excluded_closure = set()
    for lab in EXCLUDED_LABELS:
        if lab in labels:
            excluded_closure |= closure(edges, lab)
    ctx = Context(g, maps, excluded_closure, maps_json)
    ctx.hidden0 = hidden_at_start(labels)
    ctx.item_names = item_names(d)

    def owners(lab):
        idx = g.owner_roots.get(lab, [])
        return idx, sorted({roots[i]["map"] for i in idx}), sorted(g.c_owner.get(lab, set()))

    def givers(idx):
        seen, out = set(), []
        for i in idx:
            k = json.dumps(roots[i]["giver"], sort_keys=True)
            if k not in seen:
                seen.add(k)
                out.append(roots[i]["giver"])
        return sorted(out, key=lambda x: (x["map"], x["kind"], x.get("object", 0)))

    gifts, dead, excluded, purchases, mart_lines, when_null, repeat_unknown = [], [], [], [], [], [], []
    counter = {}
    for name, ln, mn, args in lines:
        lab = labels[name]
        counter[name] = counter.get(name, 0) + 1
        idx, maps_of, c_of = owners(name)
        where = ref(lab, ln)
        if name in excluded_closure:
            excluded.append({"ref": where, "label": name, "command": mn, **operand(args),
                             "why": EXCLUDED_LABELS.get(name) or "reached only from an R-3 excluded label"})
            continue
        if not idx and not c_of:
            via = [p for p in g.pruned if name in closure(edges, p[4])]
            why = "no map.json event, map script or C line reaches this label"
            if via:
                why = "reached only through a branch the game never takes: %s always returns one value (%s), " \
                      "tested at %s" % (via[0][2], via[0][3], ref(labels[via[0][0]], via[0][1]))
            dead.append({"label": name, "ref": "%s:%d" % (lab["file"], lab["line"]), "line": where, "command": mn,
                         **operand(args), "why": why})
            continue
        if mn == FIND_CMD:
            continue  # a placed item ball: maps.json `item_balls` (R-1)
        if mn in BUY_CMDS and not idx:
            excluded.append({"ref": where, "label": name, "command": mn, **operand(args),
                             "why": "the item-giving machinery itself (reached only from C: %s)" % c_of[0]})
            continue
        if mn in MART_CMDS:
            mart_lines.append((name, ln, mn, args, idx))
            continue
        what = value_of(vals, name, ln, args[0] if args else None, mn)
        rec_id = "%s:%d" % (name, counter[name])
        paths = g.paths_to(name, ln)
        info = repeat_of(g, name, ln, mn, paths, daily, vals, ctx) if mn in GIFT_CMDS else {"repeat": None, "own": None}
        when, dev, unworded = when_of(paths, info["own"], names, g, info, ctx)
        if mn in GIFT_CMDS:
            when, unworded = rearm_words(info, when, unworded)
            dev.update(repeat_dev(info))
        for prefix, (cond, *cites) in sorted(MAP_CONDITIONS.items()):
            if any(roots[i]["giver"]["map"] in map_ids_of(maps, prefix) for i in idx):
                dev["map_condition"] = {"text": cond, "refs": [c for c, _ in cites]}
                unworded = unworded + ["%s (%s)" % (cond, ", ".join(c for c, _ in cites))]
                when = None
        dev["ref"] = where
        if info["repeat"] == "unknown" and mn in GIFT_CMDS:
            repeat_unknown.append({"id": "%s:%d" % (name, counter[name]), "dev": {"why": info["why"]}})
        rec = {"id": rec_id, "maps": maps_of, "giver": givers(idx)}
        if c_of and not idx:
            rec["reached_from"] = {"C": c_of}
        if mn in GIFT_CMDS:
            rec.update({"kind": kind_of(mn, what, keys), "what": what, "repeat": info["repeat"], "exclusive_with": [],
                        "when": when, "dev": dev, "ref": where})
            if mn in ("givemon",) and len(args) > 1:
                rec["level"] = int(args[1]) if args[1].isdigit() else args[1]
            gifts.append(rec)
            rec["_sets"], rec["_vars"] = continuation(g, name)
            rec["_sets"] = rec["_sets"] | on_the_way(g, name, ln)
            rec["_common"], rec["own"] = common_tests(paths), info["own"]
            rec["_conds"] = conditions(paths, None, None, ctx) if known_paths(paths) == list(paths) else []
            rec["_fwd"] = g.forward(name) - {name}
            # an own VAR guards one state: two gifts share it only when they test the same value(s) of it
            rec["_key"] = tuple(sorted(repr(c) for c, _ in rec["_common"] if c[1] == info["own"]))
        else:
            rec.update({"kind": "decoration" if mn == "adddecoration" else
                        kind_of("giveitem", what, keys) if isinstance(what, (str, dict)) else "item",
                        "what": what, "paid_with": paid_with(g, name, ln), "when": when, "dev": dev, "ref": where})
            purchases.append(rec)
        if when is None:
            when_null.append({"id": rec_id, "dev": {"unworded": unworded}})
    link_exclusive(gifts, g, obj_flag_gifts)
    marts = build_marts(g, mart_lines, roots, givers, labels, when_null, names, ctx)
    excluded += mystery_lines(d, gift_files)
    tm_hm = build_tm_hm(d, gifts, marts, purchases, maps_json)
    return {"gifts": gifts, "marts": marts, "tm_hm": tm_hm, "purchases": purchases, "dead": dead,
            "excluded": excluded, "when_null": when_null, "repeat_unknown": repeat_unknown,
            "max_closure": g.max_closure, "graph": g}


def repeat_dev(info):
    """The developer side of a `repeat` value (fix round 2): why, the blocking writes, the re-arming writers, C uses."""
    out = {"repeat_why": info.get("why")} if info.get("why") else {}
    if info.get("blocked"):
        out["blocked_by"] = ["%s = %s (%s)" % (s, show_value(v), r) for s, (v, r) in sorted(info["blocked"].items())]
    if info.get("rearm"):
        out["rearm"] = [{"ref": w["ref"], "writes": w["writes"]} for w in info["rearm"]]
    if info.get("other_writers"):
        out["other_writers"] = info["other_writers"]
    if info.get("c_uses"):
        out["c_uses"] = info["c_uses"]
    if info.get("trigger_specials"):
        out["untabled_specials_on_the_way"] = info["trigger_specials"]
    return out


def show_value(v):
    return {"flag": lambda: "set" if v[1] else "clear"}.get(v[0], lambda: " ".join(map(str, v)))()


def rearm_words(info, when, unworded):
    """FIX ROUND 3, item 1: a gift re-armed by a cited REARM entry is offered again only as that entry's hand-read
    words say (the Shoal Cave salt: each day, after you talk to the Shell Bell man): they join `when` ('no condition'
    gives way to them); a gift whose untabled special runs on the way in (item 3) has `when` null."""
    if info.get("trigger_specials"):
        return None, unworded + ["a special on the way in that SPECIAL_EFFECTS does not table: %s"
                                 % ", ".join(info["trigger_specials"])]
    words = info.get("rearm_words") or []
    if not words or when is None:
        return when, unworded
    if when == "no condition beyond `repeat`":
        return "; ".join(words), unworded
    return "%s; %s" % (when, "; ".join(words)), unworded


def item_names(d):
    """{ITEM_X: 'Display Name'} from src/data/items.h (`.name = _("HARBOR MAIL")` -> 'Harbor Mail'): game knowledge
    for the possession words (item 3), never a flag or var name."""
    out = {}
    for m in re.finditer(r'\[(ITEM_\w+)\]\s*=\s*\{\s*\.name\s*=\s*_\("([^"]*)"\)', d.read("src/data/items.h")):
        out[m.group(1)] = " ".join(w if "." in w else w.capitalize() for w in m.group(2).split())
    return out


def map_ids_of(maps, prefix):
    """The map ids whose folder starts with `prefix` (a MAP_CONDITIONS key)."""
    return {j["id"] for folder, j in maps if folder.startswith(prefix)}


def value_of(vals, lab, ln, operand, mn):
    """The constant, or {one_of, chosen_by, refs} for a var operand, or 'unknown' with `why`. A value of the wrong TYPE
    for the command (a DECOR_ for giveitem, an ITEM_ for givedecoration) is a writer on another branch: dropped."""
    if operand is None or not operand.startswith("VAR_"):
        return operand
    prefix = "DECOR_" if "decoration" in mn else "ITEM_"
    got = [x for x in vals.resolve(lab, ln, operand)
           if x[0] == "unknown" or (x[0].startswith(prefix) and x[0] not in ("ITEM_NONE", "DECOR_NONE"))]
    items = sorted({v for v, _, _ in got if v != "unknown"})
    refs = sorted({r for _, r, _ in got if r})
    choosers = sorted({c for _, _, c in got if c})
    if not items or any(v == "unknown" for v, _, _ in got):
        why = sorted({c for v, _, c in got if v == "unknown" and c}) or ["a writer could not be resolved"]
        # F7 (fix round 1): an unresolved set still says how it is chosen, or `unknown` (never a missing key)
        known = sorted({c for v, _, c in got if c and v != "unknown"})
        return {"one_of": "unknown", "chosen_by": known[0] if len(known) == 1 else "unknown", "why": "; ".join(why),
                "refs": refs, "known_part": items}
    out = {"one_of": items, "chosen_by": choosers[0] if len(choosers) == 1 else ("unknown" if not choosers
                                                                                else "+".join(choosers)),
           "refs": refs}
    if out["chosen_by"] in WORDS_BY_CHOOSER:
        # the chooser's words where the AI reads the set (F6: the lottery says most draws win nothing; `note` would be
        # a developer key the AI never sees)
        out["words"] = WORDS_BY_CHOOSER[out["chosen_by"]]
    return out


def daily_flags(flags_h):
    """Flag names #defined in flags.h between `// Daily Flags` and `// Special Flags` (DAILY_FLAGS_START..END)."""
    a = flags_h.find("DAILY_FLAGS_START")
    b = flags_h.find("DAILY_FLAGS_END", a)
    return set(re.findall(r"#define\s+(FLAG_\w+)", flags_h[a:b]))


def hidden_at_start(labels):
    """Flags EventScript_ResetAllMapFlags (data/scripts/new_game.inc, run by src/new_game.c) sets: objects carrying
    one start HIDDEN and appear only when a script clears it."""
    lab = labels.get("EventScript_ResetAllMapFlags")
    out = set()
    for _, code in (lab or {"body": []})["body"]:
        mn, args = cmd(code)
        if mn == "setflag" and args:
            out.add(args[0])
    return out


MARKS = ("@guard", "@hidden", "@c", "@deep", "@collapsed")


def tests_of(path):
    """The (cond, how) tests of one path (its markers dropped)."""
    return {x for x in path if x[0] not in MARKS}


def known_paths(paths):
    """The paths whose tests are known: not reached from C, not past MAX_DEPTH."""
    return [p for p in paths if not any(x[0] in ("@c", "@deep") for x in p)]


def continuation(g, lab):
    """(flags the gift's continuation sets, vars it sets / adds / copies into)."""
    flags, vars_ = set(), set()
    for x in g.forward(lab):
        for _, code in g.labels[x]["body"]:
            mn, args = cmd(code)
            if mn == "setflag" and args:
                flags.add(args[0])
            elif mn in ("setvar", "addvar", "copyvar") and args:
                vars_.add(args[0])
    return flags, vars_


def on_the_way(g, lab, ln, depth=4):
    """Flags set BEFORE the gift on the way to it: earlier in its label, or in the labels that jump or fall into it
    (a few labels back). The bike shop sets its received flag before the choice; an egg's flag precedes giveegg."""
    out, seen, todo = set(), set(), [(lab, ln, 0)]
    while todo:
        x, upto, dep = todo.pop()
        if (x, upto) in seen:
            continue
        seen.add((x, upto))
        for l2, code in g.labels[x]["body"]:
            mn, args = cmd(code)
            if l2 < upto and mn == "setflag" and args:
                out.add(args[0])
        if dep < depth:
            for src, kind, eln, _, _ in g.preds.get(x, []):
                if kind in ("goto", "fall", "goto_if", "case", "call") and g.reachable(src):
                    todo.append((src, eln, dep + 1))
    return out


def repeat_of(g, lab, ln, mn, paths, daily, vals, ctx):
    """{repeat, own, why, blocked, finals, rearm, ...}: how often the gift can be had, on POSITIVE EVIDENCE (fix round 2).
    `own` (the gift's OWN guard: a flag its continuation sets that every known path tests unset, or a saved var it
    writes that every path tests; a path entered through a post-defeat script or a coord trigger on a var it writes
    counts as guarded) is kept for dev.own and link_exclusive's shared-guard rule. daily: that own flag is in flags.h's
    daily block (the game clears it every day); weekly: it is cleared again where a C special counts 7 days. Every other
    value comes from evidence(): `once` / `until_received` need a BLOCKING writer and NO RE-ARM, `repeatable` needs an
    open path or a re-arm, and anything the extractor cannot derive is `unknown` (listed in _notes.repeat_unknown).
    WHY: rounds 0 and 1 asserted a value from the ABSENCE of something they did not look for (a re-arming writer, a
    special's effect, a possession check): the Glass Workshop read `until_received` although :195 re-opens it."""
    real = known_paths(paths)
    flags_set, vars_set = continuation(g, lab)
    flags_set = flags_set | on_the_way(g, lab, ln)

    def guarded(p):
        return any(x[0] == "@guard" and (x[1] == "battle" or x[2] in vars_set) for x in p)

    own, own_kind = None, None
    for f in sorted(flags_set):
        t = ("flag", f, False)
        if real and any(t in {c for c, _ in tests_of(p)} for p in real) and \
                all(t in {c for c, _ in tests_of(p)} or guarded(p) for p in real):
            own, own_kind = f, "flag"
            break
    if own is None:
        for v in sorted(vars_set):
            if SCRATCH_VAR.fullmatch(v):
                continue
            has = [any(c[0] == "var" and c[1] == v for c, _ in tests_of(p)) for p in real]
            if real and any(has) and all(h or guarded(p) for h, p in zip(has, real)):
                own, own_kind = v, "var"
                break
    trig = trigger_specials(g, lab, ln) - set(SPECIAL_EFFECTS)
    out = evidence(g, lab, ln, mn, paths, ctx, trig)
    out["trigger_specials"] = sorted(trig)
    if not out.get("missing"):
        if own_kind == "flag" and own in daily:
            out.update(repeat="daily", why="its flag is in include/constants/flags.h's daily block (cleared each day)")
        elif own_kind == "flag" and weekly(g, lab, own, vals):
            out.update(repeat="weekly", why="its flag is cleared again where a C special counts 7 days")
    out["own"] = own
    if own_kind == "var":
        out["own_values"] = own_writes(g, lab, own)
    return out


#: flags and vars the game clears when a map is entered (src/overworld.c ClearTempFieldEventData): a guard on one
#: lasts one visit
TEMP_NAME = re.compile(r"FLAG_TEMP_\w+|VAR_TEMP_\w+")
#: the result codes of a gift command (VAR_RESULT right after it) and the one that means "not received"
#: (include/constants/pokemon.h:155-157 MON_GIVEN_TO_PARTY 0, MON_GIVEN_TO_PC 1, MON_CANT_GIVE 2)
RESULT_NUM = {"TRUE": 1, "FALSE": 0, "YES": 1, "NO": 0, "MON_GIVEN_TO_PARTY": 0, "MON_GIVEN_TO_PC": 1,
              "MON_CANT_GIVE": 2}
GIFT_RESULTS = {"giveitem": ({0, 1}, {0}), "givedecoration": ({0, 1}, {0}), "additem": ({0, 1}, {0}),
                "adddecoration": ({0, 1}, {0}), "givemon": ({0, 1, 2}, {2}), "giveegg": ({0, 1, 2}, {2})}
#: one continuation walk keeps at most this many ways (each a straight run to a terminator) and visits at most
#: MAX_WALK states (label, line, call frames, last writes, results); past either -> `unknown` (test_kb2 measures the
#: peak at the pin against these)
MAX_WAYS = 512
MAX_WALK = 20000
#: the C line that sets a trainer's flag when you win (a post-defeat script runs on that win, once)
TRAINER_FLAG_SET = ("src/battle_setup.c:1262", "void SetTrainerFlag(u16 trainerId)")
#: the only C writer that CLEARS a trainer flag is the script command `cleartrainerflag` (src/scrcmd.c:1866)
TRAINER_FLAG_CLEAR = ("src/scrcmd.c:1866", "ClearTrainerFlag(index);")


def result_writer(g, mn, args):
    """True when the command writes VAR_RESULT (the gift's own result is then no longer what a test reads)."""
    if args[:1] == ["VAR_RESULT"] and mn in ("setvar", "addvar", "subvar", "copyvar", "specialvar"):
        return True
    if mn == "special" and args:
        return special_sets_result(g.d, args[0])
    return mn in ("random", "checkplayergender", "yesnobox", "getpartysize") or "multichoice" in mn or \
        mn in ROOM_PRODUCERS or mn in POSSESSION or mn == "removeitem" or (mn == "msgbox" and "MSGBOX_YESNO" in args)


def special_sets_result(d, fn):
    """A `special` (not specialvar) that writes gSpecialVar_Result: SPECIAL_EFFECTS says so (a menu or a callback
    writes it), or its C body assigns it."""
    e = SPECIAL_EFFECTS.get(fn)
    if e and e[0] in ("result", "record"):
        return True
    found = c_function(d, fn) if d is not None else None
    return bool(found and "gSpecialVar_Result" in found[2])


def writes_of(g, x, mn, args, ctx):
    """[(subject, value)] the command writes, or None for a special SPECIAL_EFFECTS does not table. Subjects: a flag /
    var name, 'TRAINER:<T>', 'ITEM:<X>' (bag possession), a pseudo-state of SPECIAL_STATES, 'special:<reader>' (a
    resource a reader measures). Values: ('flag', bool) | ('set', k) | ('add', k) | ('sub', k) | ('copy', src) |
    ('record',) | ('unknown', why). VAR_RESULT and the 0x80xx specials are scratch: never a subject."""
    if mn in ("setflag", "clearflag") and args:
        return [(args[0], ("flag", mn == "setflag"))]
    if mn in ("settrainerflag", "cleartrainerflag") and args:
        return [("TRAINER:" + args[0], ("flag", mn == "settrainerflag"))]
    if mn in ("setvar", "addvar", "subvar", "copyvar") and len(args) > 1:
        if SCRATCH_VAR.fullmatch(args[0]) and not TEMP_NAME.fullmatch(args[0]):
            return []
        return [(args[0], ({"setvar": "set", "addvar": "add", "subvar": "sub", "copyvar": "copy"}[mn], args[1]))]
    if mn == "removeobject" and args:
        return [(f, ("flag", True)) for f in sorted(ctx.object_flags(x, args[0]))]
    if mn == "removeitem" and args:
        return [("ITEM:" + args[0], ("sub", args[1] if len(args) > 1 else "1"))]
    if mn in ("special", "specialvar") and args:
        fn = args[-1]
        e = SPECIAL_EFFECTS.get(fn)
        if e is None:
            return None
        if e[0] == "writes":
            return [(e[1], ("set", e[2]) if e[2] is not None else ("unknown", "%s writes a runtime value" % fn))]
        if e[0] == "resource":
            return [("special:" + e[1], ("sub", "?"))] if e[1] else []
        if e[0] == "record":
            return [(e[1], ("record",))]
        return []
    if mn.startswith("trainerbattle") and ew.battle_trainer(args):
        return [("TRAINER:" + ew.battle_trainer(args), ("flag", True))]
    return []


def gift_ways(g, lab, ln, mn, ctx):
    """(ways, missing specials, complete): every way the script can run on from the gift line to a terminator, each
    {'writes': {subject: (value, ref)} (the LAST write wins), 'fail': True when the gift's own result said 'not
    received' (a full bag / party and PC)}. Both arms of every branch are walked; a `call` runs its callee and comes
    back; a `return` in the gift's own frame resumes after each call into it (frame_callers). VAR_RESULT is followed
    while it still holds the gift's result: a branch on it narrows the possible results, and a way whose results are
    all the failure code is a room-fail way. Bounded by MAX_CLOSURE states and MAX_WAYS ways (past either: complete
    is False)."""
    allv, failv = GIFT_RESULTS.get(mn, ({0, 1}, {0}))
    ways, missing, seen = [], set(), set()
    dom0 = tuple(sorted((v, frozenset(vals_)) for v, vals_ in FINITE_DOMAINS.items()))
    todo = [(lab, ln, (), (), frozenset(allv), mn in GIFT_RESULTS, dom0)]
    while todo:
        x, after, frames, writes, poss, live, dom = todo.pop()
        final = {}
        for s, v, where in writes:
            final[s] = (v, where)
        writes = tuple(sorted((s, v, w) for s, (v, w) in final.items()))  # only the last write of a subject matters
        key = (x, after, frames, writes, poss, live, dom)
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > MAX_WALK or len(ways) > MAX_WAYS:
            return ways, missing, False
        ended = False
        for l2, code in g.labels[x]["body"]:
            if l2 <= after:
                continue
            c_mn, args = cmd(code)
            w = writes_of(g, x, c_mn, args, ctx)
            if w is None:
                missing.add(args[-1])
                w = []
            writes = writes + tuple((s, v, ref(g.labels[x], l2)) for s, v in w)
            branch = [e for e in g.edges[x] if e[2] == l2 and e[1] in ("goto", "call", "goto_if", "call_if", "case")]
            if live and result_writer(g, c_mn, args) and not branch:
                live = False
            for tgt, kind, _, c, _ in branch:
                if kind in ("goto_if", "call_if"):
                    taken, rest = poss, poss
                    tdom, rdom = dom, dom
                    if live and c and c[0] == "var" and c[1] == "VAR_RESULT":
                        k = RESULT_NUM.get(c[3], as_num(c[3]))
                        if k is not None:
                            taken = frozenset(r for r in poss if test_holds(("var", "V", c[2], str(k)), str(r)))
                            rest = poss - taken
                    if c and c[0] == "var" and c[1] in FINITE_DOMAINS:
                        cur = dict(dom)[c[1]]
                        t = frozenset(v for v in cur if test_holds(c, v))
                        tdom = tuple((v, t if v == c[1] else s) for v, s in dom)
                        rdom = tuple((v, cur - t if v == c[1] else s) for v, s in dom)
                    if taken and all(s for _, s in tdom):
                        todo.append((tgt, 0, frames + (((x, l2),) if kind == "call_if" else ()), writes, taken, live,
                                     tdom))
                    poss, dom = rest, rdom
                elif kind == "case":
                    todo.append((tgt, 0, frames, writes, poss, live, dom))
                elif kind == "goto":
                    todo.append((tgt, 0, frames, writes, poss, live, dom))
                elif kind == "call":
                    todo.append((tgt, 0, frames + ((x, l2),), writes, poss, live, dom))
            if not poss or not all(s for _, s in dom):  # no result or no facing is left: this way cannot go on
                ended = True
                break
            if c_mn in ("goto", "call") and branch:
                ended = True
                break
            if c_mn in TERMINATORS:
                if c_mn == "return":
                    if frames:
                        (fx, fl), rest_frames = frames[-1], frames[:-1]
                        todo.append((fx, fl, rest_frames, writes, poss, live, dom))
                    else:
                        callers = frame_callers(g, x)
                        todo += [(src, cl, (), writes, poss, live, dom) for src, cl in callers]
                        if not callers:
                            ways.append(way_of(writes, poss, failv))
                else:
                    ways.append(way_of(writes, poss, failv))
                ended = True
                break
        if not ended:
            nxt = [t for t, kind, *_ in g.edges[x] if kind == "fall"]
            if nxt:
                todo += [(t, 0, frames, writes, poss, live, dom) for t in nxt]
            else:
                ways.append(way_of(writes, poss, failv))
    return ways, missing, True


def way_of(writes, poss, failv):
    final = {}
    for s, v, where in writes:
        final[s] = (v, where)
    return {"writes": final, "fail": bool(poss) and set(poss) <= set(failv)}


def continuation_refs(g, lab, ln):
    """FIX ROUND 3, item 1: {'file:line'} of every line the gift's OWN CONTINUATION can run: the rest of its label after
    the gift line, every label reached from there by goto / call / a branch / a case / the fall, and, after a `return`
    in the gift's own frame (not inside a callee), the lines after each call into it (frame_callers). A writer here is
    the gift's own; any writer elsewhere keeps its blocking name from being SOLE (sole_writer). Lines BEFORE the gift
    line are not its continuation: a write on the way in runs before the gift, so the rule cannot tell it from a
    re-arm without reasoning about reachability (the round-2 shortcut this round removes)."""
    out, seen, todo = set(), set(), [(lab, ln, False)]
    while todo:
        x, after, in_call = todo.pop()
        if (x, after, in_call) in seen:
            continue
        seen.add((x, after, in_call))
        ended = False
        for l2, code in g.labels[x]["body"]:
            if l2 <= after:
                continue
            out.add(ref(g.labels[x], l2))
            mn, _ = cmd(code)
            for tgt, kind, eln, _, _ in g.edges[x]:
                if eln == l2 and kind in ("goto", "goto_if", "case"):
                    todo.append((tgt, 0, in_call))
                elif eln == l2 and kind in ("call", "call_if"):
                    todo.append((tgt, 0, True))
            if mn in TERMINATORS:
                if mn == "return" and not in_call:
                    todo += [(src, cl, False) for src, cl in frame_callers(g, x)]
                ended = True
                break
        if not ended:
            todo += [(t, 0, in_call) for t, kind, *_ in g.edges[x] if kind == "fall"]
    return out


def trigger_specials(g, lab, ln):
    """FIX ROUND 3, item 3: the `special` / `specialvar` functions that can run ON THE WAY INTO line `ln` of `lab`: its
    own earlier lines, the lines before the jump / branch / case / call / fall in every label that leads into it (back
    to MAX_DEPTH labels), and the bodies of the labels those earlier lines `call` (their forward closure). One not in
    SPECIAL_EFFECTS makes `when` null and forbids the 'a path stays open' `repeatable` (its effect is unknown)."""
    out, seen, todo = set(), set(), [(lab, ln, 0)]
    called = set()
    while todo:
        x, upto, dep = todo.pop()
        if (x, upto) in seen:
            continue
        seen.add((x, upto))
        for l2, code in g.labels[x]["body"]:
            if l2 >= upto:
                break
            mn, args = cmd(code)
            if mn in ("special", "specialvar") and args:
                out.add(args[-1])
        called |= {t for t, kind, eln, _, _ in g.edges[x] if kind in ("call", "call_if") and eln < upto}
        if dep < MAX_DEPTH:
            for src, kind, eln, _, _ in g.preds.get(x, []):
                if kind in ("goto", "fall", "goto_if", "case", "call", "call_if", "map_script", "battle") and \
                        g.reachable(src):
                    todo.append((src, eln, dep + 1))
    for t in called:
        for y in closure(g.edges, t, kinds=("goto", "call", "goto_if", "call_if", "case", "fall")):
            for _, code in g.labels[y]["body"]:
                mn, args = cmd(code)
                if mn in ("special", "specialvar") and args:
                    out.add(args[-1])
    return out


def before_writes(g, lab, ln, ctx, depth=4):
    """{subject: (value, ref)} written ON THE WAY into the gift: earlier in its own label (the last write wins), then
    in the labels that jump, fall, branch or call into it (a few labels back; a subject already found is kept)."""
    out, seen, todo = {}, set(), [(lab, ln, 0)]
    while todo:
        x, upto, dep = todo.pop(0)
        if (x, upto) in seen:
            continue
        seen.add((x, upto))
        here = {}
        for l2, code in g.labels[x]["body"]:
            if l2 >= upto:
                break
            m2, a2 = cmd(code)
            for s, v in writes_of(g, x, m2, a2, ctx) or []:
                here[s] = (v, ref(g.labels[x], l2))
        for s, v in here.items():
            out.setdefault(s, v)
        if dep < depth:
            for src, kind, eln, _, _ in g.preds.get(x, []):
                if kind in ("goto", "fall", "goto_if", "case", "call", "call_if") and g.reachable(src):
                    todo.append((src, eln, dep + 1))
    return out


def subject_of(c, how):
    """The saved state a test reads: a flag / var name, 'TRAINER:<T>', 'ITEM:<X>' (a possession check), the pseudo-state
    a SPECIAL_READS special reports, 'special:<reader>' (a resource reader), else None (a scratch value computed here)."""
    if c[0] == "trainer":
        return "TRAINER:" + c[1]
    if c[0] == "flag":
        return c[1]
    if not c[1]:
        return None
    if SCRATCH_VAR.fullmatch(c[1]) and not TEMP_NAME.fullmatch(c[1]):
        if how.startswith("have:checkitem:") or how.startswith("have:checkpcitem:"):
            return "ITEM:" + how.split(":")[2]
        if how.startswith("special:"):
            fn = how.split(":", 1)[1]
            if fn in SPECIAL_READS:
                return SPECIAL_READS[fn]
            e = SPECIAL_EFFECTS.get(fn)
            if e and e[0] == "record":
                return e[1]
            if any(v[0] == "resource" and v[1] == fn for v in SPECIAL_EFFECTS.values()):
                return "special:" + fn
        return None
    return c[1]


def path_tests(g, p, lab, ln):
    """[(cond, how, subject)] of one path, plus: a post-defeat entry's trigger 'the trainer not yet beaten' (the battle
    happens only then, and the win sets the trainer flag: TRAINER_FLAG_SET), and the IMPLIED test of a scratch value
    computed by exactly one conditional call on the way (the Fan Club's `call_if_unset FLAG_RECEIVED_RED_SCARF,
    ...CheckMonCool` is the only writer of the VAR_TEMP_1 value the case reads, SlateportCity_PokemonFanClub
    /scripts.inc:47-51)."""
    out = [(c, how, subject_of(c, how)) for c, how in tests_of(p)]
    for x in p:
        if x[0] == "@guard" and x[1] == "battle":
            out.append((("trainer", x[2], False), "battle-entry", "TRAINER:" + x[2]))
    for c, how, _ in list(out):
        if c[0] != "var" or not c[1] or not SCRATCH_VAR.fullmatch(c[1]) or how in ("room", "const", "answer") or \
                how.startswith(("have:", "special:", "battle")) or chooser_of_how(how):
            continue
        guards = set()
        for cc, tgt in call_ifs_on_the_way(g, lab, ln):
            for y in closure(g.edges, tgt, kinds=("goto", "call", "goto_if", "call_if", "case", "fall")):
                for _, code in g.labels[y]["body"]:
                    m2, a2 = cmd(code)
                    if m2 == "setvar" and a2[:1] == [c[1]] and len(a2) > 1 and test_holds(c, a2[1]) is True:
                        guards.add(cc)
        if len(guards) == 1:
            gc = guards.pop()
            out.append((gc, "implied", subject_of(gc, "")))
    return out


def call_ifs_on_the_way(g, lab, ln, depth=4):
    """[(cond, callee)] of the call_if lines that run before line `ln` of `lab` (its own earlier lines and those of the
    labels that jump, fall or branch into it, a few labels back)."""
    out, seen, todo = [], set(), [(lab, ln, 0)]
    while todo:
        x, upto, dep = todo.pop()
        if (x, upto) in seen:
            continue
        seen.add((x, upto))
        out += [(c, t) for t, kind, eln, c, _ in g.edges[x] if kind == "call_if" and eln < upto and c]
        if dep < depth:
            for src, kind, eln, _, _ in g.preds.get(x, []):
                if kind in ("goto", "fall", "goto_if", "case", "call") and g.reachable(src):
                    todo.append((src, eln, dep + 1))
    return out


def evaluate(c, how, subj, fv, anchors, ctx):
    """Does test `c` still hold once its subject has the value `fv`? True / False / None (cannot be told) / 'resource'
    (a quantity moved by an amount: the test stays a condition, never a block) / 'record' (a size record that only a
    bigger one beats: SPECIAL_EFFECTS 'record')."""
    kind = fv[0]
    if kind == "unknown":
        return None
    if kind == "record":
        return "record"
    if c[0] in ("flag", "trainer"):
        return fv[1] == c[2] if kind == "flag" else None
    if subj and subj.startswith("ITEM:"):
        if kind == "sub":
            if ctx.unique_item(subj[5:]):
                return test_holds(("var", "V", c[2], c[3]), "0")  # the one copy is gone: the check now says FALSE
            return "resource"
        return None
    if kind == "set":
        return test_holds(c, fv[1])
    if kind in ("add", "sub"):
        k0, d = as_num(anchors.get(subj)), as_num(fv[1])
        if k0 is None or d is None:
            return "resource"
        return test_holds(c, str(k0 + d if kind == "add" else k0 - d))
    return None


def path_status(tests, received, failed, pre, ctx, maps):
    """One path's fate after the gift, over the ways that RECEIVE it: 'open' (a way leaves every test holding: nothing
    it reads changed, or the gift wrote back a value it accepts: `sat`), 'blocked' (on every receiving way a written
    value fails a test: `blockers`), or 'unknown' (a written value cannot be evaluated, or the gift writes saved state
    the path does not read but something else does: an indirect effect cannot be ruled out)."""
    anchors = {s: c[3] for c, _, s in tests if s and c[0] == "var" and c[2] == "eq"}
    subjects = {s for _, _, s in tests if s}

    def on(way):
        blockers, sat, unknown = {}, [], []
        for c, how, s in tests:
            if not s:
                continue
            got = way["writes"].get(s) or pre.get(s)
            if got is None:
                continue
            r = evaluate(c, how, s, got[0], anchors, ctx)
            if r is False:
                blockers[s] = got
            elif r is None:
                unknown.append("%s: %s (%s)" % (cond_text(c), got[0], got[1]))
            elif r is True or r == "record":
                sat.append((s, got[1]))
        if blockers:
            return "blocked", blockers, sat, unknown
        if unknown:
            return "unknown", blockers, sat, unknown
        stray = sorted({s for s in list(way["writes"]) + list(pre) if s not in subjects and not ctx.inert(s, maps)})
        if stray:
            return "unknown", blockers, sat, ["writes %s, which a script reads, though this path does not test it "
                                              "(an indirect effect cannot be ruled out)" % ", ".join(stray)]
        return "open", blockers, sat, unknown
    got = [on(w) for w in received]
    opens = [x for x in got if x[0] == "open"]
    if opens:
        return {"st": "open", "sat": sorted({s for x in opens for s in x[2]})}
    unknown = [x for x in got if x[0] == "unknown"]
    if unknown or not got:
        return {"st": "unknown", "why": "; ".join(sorted({u for x in unknown for u in x[3]})) or "no receiving way"}
    blockers = {}
    for x in got:
        blockers.update(x[1])
    # a not-received way leaves the gift offered when nothing but a TEMP flag/var blocks it (cleared on re-entering)
    offered = any(r[0] != "blocked" or all(TEMP_NAME.fullmatch(s) for s in r[1]) for r in map(on, failed))
    return {"st": "blocked", "blockers": blockers, "offered_on_fail": offered}


def evidence(g, lab, ln, mn, paths, ctx, trig=None):
    """The `repeat` decision (fix rounds 2 and 3; see repeat_of). Each known path to the gift gets path_status over the
    ways the gift is RECEIVED on (gift_ways), its tests (path_tests) and what was written on the way (before_writes):
      repeatable  a path stays OPEN (the gift's own loop rewrites a value it accepts, the Glass Workshop's :195
                  `setvar VAR_GLASS_WORKSHOP_STATE, 2` for :27's `eq 2`; or nothing it reads changes), unless a special
                  on the way in is untabled (`trig`, item 3: its effect is unknown, so 'nothing changes' is unproven);
                  or every path is blocked and each blocked path's blockers are re-armed by a CITED REARM entry or a C
                  range whose effect decides (RANGE_DECIDES); the Contest Hall's :181 is a REARM entry;
      daily       as repeatable, decided `daily` (the Shoal Cave salt and shells, REARM; a daily-range flag);
      once        every path is blocked and on each one some blocker is SOLE (sole_writer: no writer anywhere in the
                  decomp but the gift's own continuation, no C mention, no C range);
      until_received  as once, but a way where the gift's own result said 'not received' (a full bag, or party and
                  PC) leaves a path unblocked: the gift stays offered (Beldum's :84 NoMoreRoomForPokemon);
      unknown     a path reached from C or past the depth bound, a walk past its bound, a special SPECIAL_EFFECTS
                  lacks on the continuation, a value that cannot be evaluated, or a blocked path none of whose blockers
                  is sole or re-armed by a table (its other writers go to dev.other_writers / dev.c_uses).
    WHY (fix round 3): round 2 asserted `once` from reasoning about reachability (one_shot, the 'spent' writer), and
    three wrong values came of it (the Shoal Cave salt is re-armed daily, the counter Luxury Ball on every win). Only
    the sole-writer pattern, which verify_world.py's a7 re-checks over EVERY record by its own scan, may say once."""
    ways, missing, complete = gift_ways(g, lab, ln, mn, ctx)
    out = {"repeat": "unknown", "blocked": {}, "rearm": [], "missing": bool(missing)}
    if missing:
        out["why"] = "specials on its continuation that SPECIAL_EFFECTS does not table: %s" % ", ".join(sorted(missing))
        return out
    if not complete:
        out["why"] = "the continuation walk passed its bound (%d states / %d ways)" % (MAX_WALK, MAX_WAYS)
        return out
    real = known_paths(paths)
    if not real or len(real) < len(paths):
        out["why"] = "a path reached from C or past %d labels: its tests are unknown" % MAX_DEPTH
        return out
    pre = before_writes(g, lab, ln, ctx)
    received = [w for w in ways if not w["fail"]]
    failed = [w for w in ways if w["fail"]]
    maps = {g.roots[i]["map"] for i in g.owner_roots.get(lab, [])}
    sts = []
    for p in real:
        tests = path_tests(g, p, lab, ln)
        path_pre = dict(pre)
        for c, how, s in tests:
            if how == "battle-entry":
                path_pre[s] = (("flag", True), "%s (the win sets it)" % TRAINER_FLAG_SET[0])
        sts.append((tests, path_status(tests, received, failed, path_pre, ctx, maps)))
    opens = [st for _, st in sts if st["st"] == "open"]
    if opens:
        if trig:
            out["why"] = ("a path stays open after the gift, but a special on the way in that SPECIAL_EFFECTS does not "
                          "table may change state: %s" % ", ".join(sorted(trig)))
            return out
        out.update(repeat="repeatable", rearm=[{"ref": r, "writes": s} for s, r in
                                               sorted({x for st in opens for x in st["sat"]}, key=lambda x: x[1])],
                   why="a path stays open after the gift" + (" (the gift writes back a value it accepts)"
                                                             if any(st["sat"] for st in opens) else
                                                             " (nothing it tests is changed)"))
        return out
    unknowns = [st for _, st in sts if st["st"] == "unknown"]
    if unknowns:
        out["why"] = unknowns[0]["why"]
        return out
    own = continuation_refs(g, lab, ln)
    blocked, decided, rearm, words, others, c_uses = {}, set(), [], [], [], []
    for _, st in sts:
        res = {s: sole_writer(ctx, s, own) for s in sorted(st["blockers"])}
        sole = [s for s in res if res[s]["sole"]]
        if sole:
            blocked.update({s: st["blockers"][s] for s in sole})
            continue
        if all(res[s]["decides"] for s in res):
            decided |= {res[s]["decides"] for s in res}
            rearm += [{"ref": c, "writes": s} for s in res for c in res[s]["cites"]]
            words += [res[s]["words"] for s in res if res[s]["words"]]
            continue
        for s in res:
            others += res[s]["others"]
            c_uses += res[s]["c"]
    out["blocked"] = blocked
    if others or c_uses:
        out["why"] = ("every path is blocked, but a blocking flag/var has a writer outside the gift's own "
                      "continuation, so the rule cannot say it stays blocked: %s"
                      % "; ".join(sorted(set(others + c_uses))[:4]))
        out["other_writers"] = sorted(set(others))
        out["c_uses"] = sorted(set(c_uses))
        return out
    if decided:
        if len(decided) > 1:
            out["why"] = "its blocked paths are re-armed differently (%s)" % ", ".join(sorted(decided))
            return out
        out.update(repeat=decided.pop(), rearm_words=sorted(set(words)),
                   rearm=sorted({(w["ref"], w["writes"]): w for w in rearm}.values(),
                                key=lambda w: (w["ref"], w["writes"])),
                   why="every path is blocked after the gift, but a cited re-arm (REARM / a C range) opens it again")
        return out
    offered = any(st["offered_on_fail"] for _, st in sts)
    out.update(repeat="until_received" if offered else "once",
               why="every path is blocked by a SOLE writer: only the gift's own continuation writes %s%s" % (
                   ", ".join(sorted(blocked)), "; a way where it was not received leaves it offered" if offered else ""))
    return out


def sole_writer(ctx, s, own):
    """FIX ROUND 3, item 1: is the blocking subject `s` written by NOTHING in the whole decomp but the gift's own
    continuation (`own`, continuation_refs)? {'sole', 'others' (writers elsewhere: 'NAME: mnemonic at ref', and the C
    ranges), 'c' ('NAME named by C code at file:line'), 'ranges', 'decides' (a REARM entry's or a deciding C range's
    repeat value, else None), 'words', 'cites'}. Writers are counted over every ALIAS of the name (one flag id, two
    names: FLAG_TEMP_SKIP_GABBY_INTERVIEW is FLAG_TEMP_1).
      a FLAG_ / VAR_ name   SOLE when no script writer (WRITER_CMDS, a removeobject of an object carrying it) outside
                            `own`, no src/ line naming it (unless CITED_READS lists that line as a read) and no C range
                            covering it other than the new-game start;
      ITEM:<X>              SOLE when the item has exactly one source in the game (ctx.unique_item);
      anything else         (a trainer's flag, set by the battle; a SPECIAL_STATES state; a resource) is never sole: no
                            name scan can re-check it.
    `decides`: a REARM entry (cited) for the name; or, when the only writers outside `own` are C ranges, a range whose
    effect RANGE_DECIDES maps (daily -> daily, every map entry -> repeatable)."""
    out = {"sole": False, "others": [], "c": [], "ranges": [], "decides": None, "words": None, "cites": []}
    if s.startswith("ITEM:"):
        out["sole"] = ctx.unique_item(s[5:])
        if not out["sole"]:
            out["others"] = ["%s: a source of the item at %s" % (s, x) for x in ctx.item_sources.get(s[5:], [])[:3]]
        return out
    if not re.fullmatch(r"(?:FLAG|VAR)_\w+", s):
        out["others"] = ["%s: not a flag or var name, so no whole-decomp scan can re-check it" % s]
        return out
    wi = ctx.writer_index()
    for nm in wi.aliases(s):
        out["others"] += ["%s: %s at %s" % (s, m, r) for r, m in wi.script.get(nm, []) if r not in own]
        reads = {c for c, _ in CITED_READS.get(nm, [])}
        out["c"] += ["%s named by C code at %s:%d" % (s, rel, n) for rel, n, _ in c_name_index(ctx.g.d).get(nm, [])
                     if "%s:%d" % (rel, n) not in reads]
    out["ranges"] = wi.ranges_of(s)
    if s in REARM:
        out["decides"], out["words"] = REARM[s][0], REARM[s][1]
        out["cites"] = [c for c, _ in REARM[s][2:]]
    elif not out["others"] and not out["c"] and out["ranges"]:
        eff = {e for _, e, _ in out["ranges"]}
        if len(eff) == 1 and next(iter(eff)) in RANGE_DECIDES:
            out["decides"] = RANGE_DECIDES[next(iter(eff))]
            out["cites"] = [c for _, _, c in out["ranges"]]
    out["sole"] = not out["others"] and not out["c"] and not out["ranges"]
    out["others"] += ["%s: written by C (%s, %s)" % (s, k, c) for k, _, c in out["ranges"]]
    return out


def c_int(expr, names):
    """A C integer expression of ints, names, + - * / % and parentheses, evaluated (KeyError / ValueError if not)."""
    expr = re.sub(r"\b0x[0-9A-Fa-f]+\b", lambda m: str(int(m.group(0), 16)), expr.strip())
    expr = re.sub(r"[A-Za-z_]\w*", lambda m: str(names[m.group(0)]), expr)
    if not re.fullmatch(r"[\d\s+\-*/%()]*", expr):
        raise ValueError(expr)
    return int(eval(expr.replace("/", "//"), {"__builtins__": {}}, {}))  # noqa: S307 (validated above)


def name_ids(d):
    """{name: int} of every #define in include/constants/flags.h and vars.h, with the counts their bounds use
    (opponents.h MAX_TRAINERS_COUNT, the rematches.h enum): a flag's id, so aliases share one. Memoised per Decomp."""
    if getattr(d, "_name_ids", None) is None:
        names = parse_enum_blocks(d.read("include/constants/rematches.h"))
        pending = []
        for rel in ("include/constants/opponents.h", "include/constants/flags.h", "include/constants/vars.h"):
            pending += re.findall(r"^[ \t]*#define[ \t]+([A-Za-z_]\w*)[ \t]+([^\n]+)$", strip_comments(d.read(rel)),
                                  flags=re.M)
        for _ in range(8):
            left = []
            for k, v in pending:
                try:
                    names[k] = c_int(v.strip().rstrip("\\").strip(), names)
                except (KeyError, ValueError, SyntaxError):
                    left.append((k, v))
            pending = left
        d._name_ids = names
    return d._name_ids


def data_script_files(d):
    """Every script file under data/ (*.inc, *.s), sorted: the sole-writer scan reads ALL of them (the event scripts,
    the mystery-gift files, labels nothing reaches), not only the graph's closure."""
    out = []
    for dirpath, _, files in sorted(os.walk(os.path.join(d.root, "data"))):
        for fn in sorted(files):
            if fn.endswith((".inc", ".s")):
                out.append(os.path.relpath(os.path.join(dirpath, fn), d.root).replace("\\", "/"))
    return out


class WriterIndex:
    """FIX ROUND 3, item 1: the WHOLE-DECOMP writer index the sole-writer rule reads, built once per build.
    script  {name: [('file:line', mnemonic)]}: every WRITER_CMDS line of every data/ script file naming it at a written
            operand, and every `removeobject` line under the hide flag of each object it can remove (the objects of
            that local id on the maps whose scripts reach the line; a removeobject through a var other than
            VAR_LAST_TALKED counts for every object of those maps);
    ids     {name: id} (name_ids), for the aliases and the C ranges (C_RANGES, members resolved once)."""

    def __init__(self, d, g, maps, ctx):
        self.ids = name_ids(d)
        self.by_id = {}
        for n, v in self.ids.items():
            if n.startswith(("FLAG_", "VAR_")):
                self.by_id.setdefault((n[:n.index("_")], v), []).append(n)
        self.script = {}
        self.obj_by_map = {}
        for folder, j in maps:
            for o in j.get("object_events") or []:
                if o.get("flag") not in (None, "0"):
                    self.obj_by_map.setdefault(j["id"], []).append((o.get("local_id"), o["flag"]))
        for rel in data_script_files(d):
            text = d.read(rel)
            try:
                rows = vanilla_lines(text, rel)
            except Refused:  # a data file outside the script closure with another conditional: every line counts
                rows = [(i, strip_comment(x)) for i, x in enumerate(text.split("\n"), 1)]
            label = None
            for n, code in rows:
                code = code.strip()
                m = LABEL_RE.match(code)
                if m:
                    label = m.group(1)
                    continue
                mn, args = cmd(code)
                where = "%s:%d" % (rel, n)
                if mn in WRITER_CMDS:
                    for i in WRITER_CMDS[mn][0]:
                        if i < len(args) and re.fullmatch(r"(?:FLAG|VAR)_\w+", args[i]):
                            self.script.setdefault(args[i], []).append((where, mn))
                elif mn == "removeobject" and args and label in g.labels:
                    flags = set()
                    for mid in {g.roots[i]["map"] for i in g.owner_roots.get(label, [])}:
                        for lid, flag in self.obj_by_map.get(mid, []):
                            if args[0] == lid or (args[0].startswith("VAR_") and args[0] != "VAR_LAST_TALKED"):
                                flags.add(flag)
                    if args[0] == "VAR_LAST_TALKED":
                        flags |= ctx.object_flags(label, "VAR_LAST_TALKED")
                    for flag in sorted(flags):
                        self.script.setdefault(flag, []).append((where, mn))
        self.range_members = []
        for key, ns, members, effect, *cites in C_RANGES:
            self.range_members.append((key, ns, self.members(members), effect, cites[0][0]))

    def members(self, spec):
        """The set of ids a C_RANGES members spec covers (None = every id of the namespace)."""
        if spec[0] == "all":
            return None
        if spec[0] == "range":
            return set(range(c_int(spec[1], self.ids), c_int(spec[2], self.ids) + 1))
        if spec[0] == "prefix":
            return {v for n, v in self.ids.items() if n.startswith(spec[1])}
        if spec[0] == "objects":
            return {self.ids[f] for mid, lid in spec[1] for lid2, f in self.obj_by_map.get(mid, [])
                    if lid2 == lid and f in self.ids}
        raise Refused("C_RANGES: an unknown members spec %r" % (spec,))

    def aliases(self, name):
        """Every name with the id of `name` (itself first; just itself when its id is unknown)."""
        if name not in self.ids:
            return [name]
        return [name] + sorted(set(self.by_id.get((name[:name.index("_")], self.ids[name]), [])) - {name})

    def ranges_of(self, name):
        """[(range key, effect, first cite)] of every C range writing `name`, the new-game start left out."""
        if name not in self.ids:
            return []
        ns, v = ("flag" if name.startswith("FLAG_") else "var"), self.ids[name]
        return [(k, e, c) for k, rns, mem, e, c in self.range_members
                if rns == ns and e != "start" and (mem is None or v in mem)]


class Context:
    """What evidence() reads across the whole game, built once per build: the names some script or map.json READS, the
    C files naming each flag/var, the sources of each item, the object hide flags, and (fix round 3) the whole-decomp
    WRITER index of every flag and var (writer_index, built on first use)."""

    def __init__(self, g, maps, excluded, maps_json):
        self.g, self.excluded, self.maps = g, excluded, maps
        self._wi = None
        self.obj_flag = {}
        for r in g.roots:
            if r["giver"]["kind"] == "object":
                self.obj_flag[(r["map"], r["giver"]["local_id"])] = r["object_flag"]
        self.readers, self.temp_readers = set(), {}
        self.item_sources = {}
        for name, lab in g.labels.items():
            if not g.reachable(name) or name in excluded:
                continue
            mids = {g.roots[i]["map"] for i in g.owner_roots.get(name, [])}
            for ln, code in lab["body"]:
                mn, args = cmd(code)
                if not args:
                    continue
                if re.match(r"(goto|call)_if_", mn) or mn in ("switch", "map_script_2", "checkflag",
                                                              "checktrainerflag"):
                    nm = ("TRAINER:" + args[0]) if "defeated" in mn or mn == "checktrainerflag" else args[0]
                    self.readers.add(nm)
                    if TEMP_NAME.fullmatch(nm):
                        self.temp_readers.setdefault(nm, set()).update(mids)
                if mn in ("giveitem", "additem") and not args[0].startswith("VAR_"):
                    self.item_sources.setdefault(args[0], []).append(ref(lab, ln))
        for folder, j in maps:
            for o in j.get("object_events") or []:
                if o.get("flag") not in (None, "0"):
                    self.readers.add(o["flag"])
            for c in j.get("coord_events") or []:
                if c.get("var"):
                    self.readers.add(c["var"])
            for b in j.get("bg_events") or []:
                if b.get("flag"):
                    self.readers.add(b["flag"])
        for m in maps_json["maps"]:
            for lst in ("item_balls", "hidden_items"):
                for i, it in enumerate(m.get(lst) or []):
                    self.item_sources.setdefault(it["item"], []).append("maps.json %s %s[%d]" % (m["id"], lst, i))
        for name, lab in g.labels.items():  # mart lists: the .2byte entries of every list a pokemart line names
            for ln, code in lab["body"]:
                mn, args = cmd(code)
                if mn == "pokemart" and args and args[0] in g.labels and g.reachable(name):
                    for _, c2 in g.labels[args[0]]["body"]:
                        m2, a2 = cmd(c2)
                        if m2 == ".2byte" and a2 and a2[0].startswith("ITEM_") and a2[0] != "ITEM_NONE":
                            self.item_sources.setdefault(a2[0], []).append("mart %s" % args[0])
        self._c = {}

    def writer_index(self):
        """The WriterIndex (fix round 3, item 1), built once."""
        if self._wi is None:
            self._wi = WriterIndex(self.g.d, self.g, self.maps, self)
        return self._wi

    def object_flags(self, label, local_id):
        """The map.json hide flags of the object `removeobject <local_id>` removes in `label` (VAR_LAST_TALKED: the
        objects whose script reaches it): removing it sets that flag, so it stays gone."""
        g = self.g
        idx = g.owner_roots.get(label, [])
        if local_id == "VAR_LAST_TALKED":
            flags = {g.roots[i]["object_flag"] for i in idx if g.roots[i]["giver"]["kind"] == "object"}
        else:
            flags = {self.obj_flag.get((g.roots[i]["map"], local_id)) for i in idx}
        return {f for f in flags if f not in (None, "0")}

    def c_named(self, name, writes_only=False):
        """['file:line'] of every src/ C line naming `name`; with writes_only, only the lines this rule cannot show
        to be a pure READ (anything but `FlagGet(NAME)` / `VarGet(NAME)`: a FlagSet, a VarSet, a GetVarPointer, a
        table entry)."""
        hits = []
        for rel, n, line in c_name_index(self.g.d).get(name, []):
            if writes_only and re.search(r"\b(FlagGet|VarGet)\s*\(\s*%s\s*\)" % re.escape(name), line):
                continue
            hits.append("%s:%d" % (rel, n))
        return hits

    def unique_item(self, item):
        """True when the item has exactly one source in the game (a gift, an item ball, a hidden item, a mart list)."""
        return len(self.item_sources.get(item, [])) == 1

    def inert(self, s, maps):
        """A write that no trigger can feel: an item taken or a resource spent (a test that reads it is on the path
        itself), a temp flag/var no script of these maps tests, or a flag/var no script, map.json event or C file
        reads."""
        if s.startswith(("ITEM:", "special:")):
            return True
        if s.startswith("TRAINER:") or s in SPECIAL_STATES:
            return False
        if TEMP_NAME.fullmatch(s):
            return not (self.temp_readers.get(s, set()) & maps)
        return s not in self.readers and not self.c_named(s)


def chooser_of_how(how):
    """The chooser a test's `how` names (a CHOOSER_OF special, command or var), else None."""
    if how.startswith("special:"):
        return CHOOSER_OF.get(how.split(":", 1)[1])
    return how if how in WORDS_BY_CHOOSER else None


def frame_callers(g, lab):
    """[(label, line)] of every `call` / `call_if` whose callee runs (by goto, fall, a branch or a case) into `lab`: where
    a `return` in lab's frame resumes. Bounded by MAX_DEPTH labels back."""
    out, seen, todo = set(), set(), [(lab, 0)]
    while todo:
        x, dep = todo.pop()
        if x in seen:
            continue
        seen.add(x)
        for src, kind, ln, _, _ in g.preds.get(x, []):
            if not g.reachable(src):
                continue
            if kind in ("call", "call_if"):
                out.add((src, ln))
            elif kind in ("goto", "fall", "goto_if", "case") and dep < MAX_DEPTH:
                todo.append((src, dep + 1))
    return sorted(out)


def own_writes(g, lab, own):
    """The values the gift's continuation `setvar`s into its own var (F5); None when it also adds, subtracts or copies
    into it (a relative write: no test can be shown to be the once-guard)."""
    vals_, relative = set(), False
    for x in g.forward(lab):
        for _, code in g.labels[x]["body"]:
            mn2, args = cmd(code)
            if args and args[0] == own:
                if mn2 == "setvar" and len(args) > 1:
                    vals_.add(args[1])
                elif mn2 in ("addvar", "subvar", "copyvar"):
                    relative = True
    return None if relative else sorted(vals_)


def weekly(g, lab, own, vals):
    """The own flag is cleared again by the giver's script on a path that tests a C special counting 7 days
    (`gLocalTime.days - x >= 7`)."""
    for i in g.owner_roots.get(lab, []):
        for x in closure(g.edges, g.roots[i]["label"]):
            body = g.labels[x]["body"]
            if any(cmd(c)[0] == "clearflag" and cmd(c)[1][:1] == [own] for _, c in body):
                for ln2, c in body + [b for p in g.preds.get(x, []) for b in g.labels[p[0]]["body"]]:
                    m2, a2 = cmd(c)
                    found = c_function(vals.d, a2[1]) if m2 == "specialvar" and len(a2) == 2 else None
                    if found and re.search(r"gLocalTime\.days\s*-\s*\w+\s*>=\s*7\b", found[2]):
                        return True
    return False


def trainer_words(names, sym, defeated):
    who = names.get(sym, sym)
    return ("after you defeat %s" if defeated else "before you defeat %s") % who


def common_tests(paths):
    """{(cond, how)} of the conditions EVERY known path tests. The intersection is on the condition alone (the SS
    Ticket's two paths test `VAR_LITTLEROOT_HOUSES_STATE_MAY eq 3` at two map_script_2 lines, F5), except for a
    scratch result read through a possession check or a special: there the producer is part of the condition (the
    Shell Bell's two `VAR_RESULT ne FALSE` read two different checkitem lines)."""
    real = known_paths(paths)
    if not real:
        return set()

    def key(c, how):
        return (c, how) if how.startswith(("have:", "special:")) else c
    keys = set.intersection(*[{key(c, h) for c, h in tests_of(p)} for p in real])
    out = set()
    for k in keys:
        c = k[0] if isinstance(k[0], tuple) else k
        hows = sorted({h for p in real for c2, h in tests_of(p) if key(c2, h) == k})
        out.add((c, hows[0]))
    return out


def as_num(x):
    """An int for a decimal / hex literal or TRUE / FALSE, else None (a symbolic constant)."""
    if x in ("TRUE", "FALSE"):
        return int(x == "TRUE")
    try:
        return int(x, 0)
    except (TypeError, ValueError):
        return None


def test_holds(c, value):
    """Whether the var test c = ('var', V, op, k) passes when V == value; None when it cannot be told."""
    a, b = as_num(value), as_num(c[3])
    if a is None or b is None:
        if c[2] in ("eq", "ne"):
            return (value == c[3]) == (c[2] == "eq")
        return None
    return {"eq": a == b, "ne": a != b, "lt": a < b, "le": a <= b, "gt": a > b, "ge": a >= b}.get(c[2])


def start_consts(d):
    """{symbol: int} for reading a test's value at NEW GAME: the flag / var ids (name_ids) and the item enum
    (include/constants/items.h, ITEM_NONE = 0). Memoised per Decomp."""
    if getattr(d, "_start_consts", None) is None:
        out = dict(name_ids(d))
        out.update(parse_enum_blocks(d.read("include/constants/items.h")))
        d._start_consts = out
    return d._start_consts


def holds_at_start(c, ctx):
    """FIX ROUND 3, item 2: does test `c` HOLD at new game? A flag starts clear (src/event_data.c:34) unless
    EventScript_ResetAllMapFlags sets it (ctx.hidden0, src/new_game.c:196); a var starts 0 (src/event_data.c:35).
    True / False, or None when the compared value is a symbol this cannot read (then it is no once-guard: kept)."""
    if c[0] == "flag":
        return c[2] == (c[1] in (ctx.hidden0 if ctx else set()))
    if c[0] != "var" or not c[1]:
        return None
    k = as_num(c[3])
    if k is None and ctx is not None:
        k = start_consts(ctx.g.d).get(c[3])
    if k is None:
        return None
    return test_holds(("var", c[1], c[2], str(k)), "0")


def is_once_guard(c, own, info, ctx=None):
    """F5 (fix round 1): is test `c` the gift's ONCE-GUARD itself (dropped from `when`: `repeat` says it), rather than a
    story gate (kept)? A flag test on the own flag is the guard. A test on the own VAR is the guard only when the gift's
    own post-gift `setvar` flips it away from the gift (the test fails at every value the gift writes) AND the value it
    compares with is one the gift itself writes (`ne 1`, `lt 2`, `gt 2` with `setvar V, 1|2`). Every `eq` test is kept,
    `eq 0` included: the Letter's `map_script_2 VAR_DEVON_CORP_3F_STATE, 0` (RustboroCity_DevonCorp_3F/scripts.inc)
    stays in dev.tests as the fix spec's F2 requires (kept means `when` null, never a false 'no condition').
    FIX ROUND 3, item 2: and only when the test HOLDS AT NEW GAME (holds_at_start). A test that fails at the start
    (an own var tested `ne 0`, an own flag tested set) is a PRECONDITION something else must make true first, so it
    stays a condition: the lottery's owed prize, `goto_if_ne VAR_POKELOT_PRIZE_ITEM, ITEM_NONE`
    (LilycoveCity_DepartmentStore_1F/scripts.inc:12), is not 'no condition'."""
    if own is None or c[1] != own or holds_at_start(c, ctx) is not True:
        return False
    if c[0] == "flag":
        return True
    written = (info or {}).get("own_values")
    if not written or c[0] != "var" or any(test_holds(c, w) is not False for w in written):
        return False
    return any(as_num(w) is not None and as_num(w) == as_num(c[3]) or w == c[3] for w in written)


def setter_words(g, c):
    """The ONE setter word rule (F5): a var test `eq k` whose every `setvar V, k` site is in
    data/scripts/hall_of_fame.inc (and nothing else writes V: no addvar / subvar / copyvar, no C file names it) reads
    'after entering the Hall of Fame'. Derived from the setter sites, never typed per record."""
    if g is None or c[0] != "var" or c[2] != "eq" or not c[1]:
        return None
    key = ("setter_words", c[1], c[3])
    if key in g._memo:
        return g._memo[key]
    g._memo[key] = None
    sites = []
    for name, lab in g.labels.items():
        if not g.reachable(name):
            continue
        for _, code in lab["body"]:
            mn, args = cmd(code)
            if args and args[0] == c[1]:
                if mn in ("addvar", "subvar", "copyvar"):
                    return None
                if mn == "setvar" and len(args) > 1 and (args[1] == c[3] or (
                        as_num(args[1]) is not None and as_num(args[1]) == as_num(c[3]))):
                    sites.append(lab["file"])
    if not sites or any(f != HOF_FILE for f in sites):
        return None
    if g.d is not None and c_name_index(g.d).get(c[1]):
        return None
    g._memo[key] = "after entering the Hall of Fame"
    return g._memo[key]


def canon(v):
    """A test value in one spelling: a number for TRUE / FALSE / YES / NO / a literal, else the symbol."""
    n = RESULT_NUM.get(v, as_num(v))
    return str(n) if n is not None else v


def norm(c, how):
    """A boolean result in one spelling: `ne FALSE` is `eq TRUE`, `eq 0` is `eq FALSE` (a possession check, a special,
    VAR_RESULT), so two paths that took opposite arms compare equal-and-opposite and a test met twice in two spellings
    is one (the Quiz Lady's :240-241 `eq 1` / `eq 0` after `ne 1`)."""
    if c[0] == "var" and c[2] in ("eq", "ne") and canon(c[3]) in ("0", "1") and \
            (how.startswith(("have:", "special:")) or c[1] == "VAR_RESULT"):
        true = (canon(c[3]) == "1") == (c[2] == "eq")
        return ("var", c[1], "eq", "TRUE" if true else "FALSE"), how
    return c, how


def cond_key(c, how):
    """Tests on one key read one value: the subject, or for an unmapped scratch value its var plus how it was made."""
    s = subject_of(c, how)
    return s if s else (c[1], how)


def prune(conds):
    """Drop a test another test on the same key already implies (`eq 2` makes `ne 1` and `lt 10` say nothing)."""
    out = []
    for c, how in conds:
        if c[0] == "var" and c[2] != "eq" and any(
                c2[0] == "var" and c2[2] == "eq" and cond_key(c2, h2) == cond_key(c, how) and test_holds(c, c2[3])
                for c2, h2 in conds):
            continue
        if (c, how) not in out:
            out.append((c, how))
    return out


def complementary(a, b):
    (ca, ha), (cb, hb) = a, b
    if ca[0] != cb[0] or ca[1] != cb[1] or cond_key(ca, ha) != cond_key(cb, hb):
        return False
    if ca[0] in ("flag", "trainer"):
        return ca[2] != cb[2]
    if {ca[2], cb[2]} == {"eq", "ne"}:
        return ca[3] == cb[3]
    return ca[2] == cb[2] == "eq" and {canon(ca[3]), canon(cb[3])} == {"0", "1"}


def merge(paths):
    """Paths that differ only by one test and its opposite are one path without it (the Favor Lady's 'has another
    player given her an item' TRUE / FALSE both lead on to her request, lilycove_lady.inc:28-29); a path that holds
    every test of another, and more, says nothing the other does not (it is absorbed)."""
    ps = [frozenset(p) for p in paths]
    changed = True
    while changed:
        changed = False
        ps = sorted(set(ps), key=lambda p: (len(p), sorted(map(repr, p))))
        for i, p in enumerate(ps):
            for q in ps[i + 1:]:
                if p < q:
                    ps.remove(q)
                    changed = True
                    break
                d1, d2 = p - q, q - p
                if len(d1) == 1 and len(d2) == 1 and complementary(next(iter(d1)), next(iter(d2))):
                    ps.remove(p)
                    ps.remove(q)
                    ps.append(p & q)
                    changed = True
                    break
            if changed:
                break
    return ps


def once_guard(c, how, blocked, hidden0, own=None, ctx=None):
    """Fix round 2: a test the gift's own BLOCKING writer fails and that held before it (a flag clear at new game tested
    unset, a var tested by anything but `eq` that holds at 0, a SPECIAL_STATES state tested at its initial value): the
    repeat axis, said by `repeat`, not a condition in `when`. The gift's OWN var is left to is_once_guard (its own
    writes, own_writes), so that rule stays the one that decides it. Fix round 3, item 2: the var's start value is read
    through holds_at_start, so a symbol (ITEM_NONE) is compared as its number, never as text."""
    s = subject_of(c, how)
    if s not in blocked:
        return False
    if c[0] == "flag":
        return c[2] is False and s not in hidden0
    if s in SPECIAL_STATES:
        return test_holds(c, SPECIAL_STATES[s]["initial"]) is True
    return c[0] == "var" and s != own and c[2] != "eq" and holds_at_start(c, ctx) is True


def holds_at_reset(c):
    """A test on a TEMP flag/var that holds at its value on entering the map (clear / 0): true on every arrival."""
    return c[0] in ("flag", "var") and c[1] and TEMP_NAME.fullmatch(c[1]) and (
        c[2] is False if c[0] == "flag" else test_holds(c, "0") is True)


def conditions(paths, own, info, ctx):
    """Per known path: its CONDITIONS, [(cond, how)]: every test, the trigger's own included (a coord var, the giver
    object's hide flag, a map_script_2 var), possession checks and special results included, EXCEPT the repeat axis
    (bag / party room, the gift's own once-guard), a yes / no answer, a test on a constant just set, and a temp test that
    holds on arrival. Implied tests are pruned (prune)."""
    blocked = (info or {}).get("blocked") or {}
    hidden0 = ctx.hidden0 if ctx else set()
    out = []
    for p in known_paths(paths):
        conds = []
        for c, how in sorted(tests_of(p), key=repr):
            started_hidden = c[0] == "flag" and c[1] in hidden0  # set at new game: a story gate, never the once-guard
            if how in ("room", "const", "answer") or (is_once_guard(c, own, info, ctx) and not started_hidden) or \
                    once_guard(c, how, blocked, hidden0, own, ctx) or holds_at_reset(c):
                continue
            conds.append(norm(c, how))
        out.append(prune(conds))
    return out


def have_words(how, c, ctx):
    """'needs 4 Shoal Salt' / 'only while you do not have the Scanner'... from a possession check's item display name
    (src/data/items.h) and count: game knowledge (item names), never a flag or var name (item 3)."""
    _, mn, x, n = how.split(":", 3)
    has, hasnt = test_holds(("var", "V", c[2], c[3]), "1"), test_holds(("var", "V", c[2], c[3]), "0")
    if (has, hasnt) not in ((True, False), (False, True)):
        return None
    if mn in ("checkitem", "checkpcitem"):
        name = ctx.item_names.get(x) if ctx else None
        if not name:
            return None
        where = " in the PC" if mn == "checkpcitem" else ""
        return ("needs %s %s%s" % (n, name, where)) if has else ("only while you have fewer than %s %s%s" % (n, name,
                                                                                                         where))
    if mn == "checkmoney":
        return ("needs at least %s money" % x) if has else ("only while you have less than %s money" % x)
    if mn == "checkcoins":
        return ("needs at least %s Game Corner coins" % x) if has else None
    return None


def words_of(c, how, names, g, ctx):
    """The words of one condition by a WORD RULE, else None: the giver object hidden at new game, a badge or the Hall
    of Fame flag, a trainer beaten, a SPECIALVAR_WORDS entry, a possession check, a chooser, a var value set only in the
    Hall of Fame script (setter_words)."""
    if how == "object":
        return "the giver is not there at first: they appear later in the story" if ctx and c[1] in ctx.hidden0 \
            else None
    if c[0] == "flag":
        return badge_words(c[1], c[2])
    if c[0] == "trainer":
        return trainer_words(names, c[1], c[2])
    if how.startswith("special:") and c[2] == "eq":
        w = SPECIALVAR_WORDS.get((how.split(":", 1)[1], canon(c[3])))
        if w:
            return w[0]
    for (line, op, value), (words, *_) in LINE_WORDS.items():
        if line == how and op == c[2] and canon(value) == canon(c[3]):
            return words
    if how.startswith("have:"):
        return have_words(how, c, ctx)
    ch = chooser_of_how(how)
    if ch in WORDS_BY_CHOOSER:
        return WORDS_BY_CHOOSER[ch]
    return setter_words(g, c)


def when_of(paths, own, names, g=None, info=None, ctx=None):
    """(words or None, dev, [unworded]). FIX ROUND 2, item 2: 'no condition beyond `repeat`' ONLY when at least one
    known path to the line has NO condition left (conditions); otherwise every path's conditions are worded (one
    phrase, or 'either (A) or (B)' when the paths differ) or `when` is null and the unworded ones are listed. WHY:
    round 1 intersected the paths' tests, so two gated paths with DIFFERENT gates printed 'no condition' (ReturnGoods,
    Kiri's berry, the Devon Scope, TM Facade, Castform, the Favor and Quiz Ladies). dev.tests: the conditions every
    path makes; dev.path_tests: each path's, when they differ."""
    real = known_paths(paths)
    flags, vars_, unworded = set(), set(), []
    for p in real:
        for c, _ in tests_of(p):
            (flags if c[0] == "flag" else vars_ if c[0] == "var" and c[1] else set()).add(c[1])
    per = merge(conditions(paths, own, info, ctx))
    texts = [sorted(cond_text(c) for c, _ in p) for p in per]
    common = sorted(set.intersection(*[set(t) for t in texts])) if texts else []
    dev = {"flags": sorted(flags), "vars": sorted(vars_), "tests": common, "paths": len(paths)}
    if len({tuple(t) for t in texts}) > 1:
        dev["path_tests"] = sorted(texts)
    if len(real) < len(paths):
        dev["unknown_paths"] = sorted({x[1] if len(x) > 1 else x[0] for p in paths for x in p
                                       if x[0] in ("@c", "@deep")})
        unworded.append("a path reached only from C or past %d labels: its tests are unknown" % MAX_DEPTH)
    if own:
        dev["own"] = own
    if not real:
        unworded.append("reached only from C or past %d labels: the path's tests are unknown" % MAX_DEPTH)
        return None, dev, unworded
    if any(not p for p in per):
        return "no condition beyond `repeat`", dev, []
    phrases = []
    for p in per:
        ws = []
        for c, how in sorted(p, key=repr):
            w = words_of(c, how, names, g, ctx)
            if w is None:
                unworded.append(cond_text(c) + (" (%s)" % how if how.startswith(("have:", "special:")) else ""))
            elif w not in ws:
                ws.append(w)
        phrases.append("; ".join(ws))
    if unworded:
        return None, dev, sorted(set(unworded))
    phrases = sorted(set(phrases))
    if len(phrases) == 1:
        return phrases[0], dev, []
    return "either " + " or ".join("(%s)" % x for x in phrases), dev, []


def link_exclusive(gifts, g, obj_flag_gifts):
    """exclusive_with, four decomp-derived rules (TAKING ONE REMOVES THE OTHER):
    (A) taking G sets the map.json flag that HIDES another object of the same map whose script holds gift H (the
        Mirage Tower fossils);
    (B) every path to G and to H tests one saved var (or the starter) for DIFFERENT values, the var being neither's own
        and written by neither's continuation (Lileep / Anorith by the fossil revived; the starter dolls);
    (C) every path to G tests a saved flag set and every path to H tests it unset, the flag being neither's own and set
        by neither's continuation (the Desert Underpass fossil you did NOT choose);
    (D) G and H share their own once-guard (one flag or var) and give different things (Birch's Johto starters, the
        bikes, Return / Frustration this week)."""
    by_label = {}
    for gf in gifts:
        by_label.setdefault(gf["id"].rsplit(":", 1)[0], []).append(gf)
    # a var some script `addvar`s is a progress COUNTER (the Trick House level): its values come in turn, not instead
    counters = {cmd(code)[1][0] for lab in g.labels.values() for _, code in lab["body"]
                if cmd(code)[0] in ("addvar", "subvar") and cmd(code)[1]}
    for gf in gifts:
        ex = set()
        for mid in gf["maps"]:
            for fl in gf["_sets"]:
                for root_label in obj_flag_gifts.get((mid, fl), ()):
                    for x in closure(g.edges, root_label):
                        for h in by_label.get(x, []):
                            if h is not gf:
                                ex.add(h["id"])
        for h in gifts:
            if h is gf or not set(gf["maps"]) & set(h["maps"]):
                continue
            mine = {c for c, _ in gf["_common"]}
            theirs = {c for c, _ in h["_common"]}
            written = gf["_vars"] | h["_vars"] | gf["_sets"] | h["_sets"]
            for c in mine:
                if c[1] in (gf["own"], h["own"]) or c[1] in written:
                    continue
                if c[0] == "var" and c[2] == "eq" and c[1] not in counters and \
                        (c[1] == "VAR_STARTER_MON" or not SCRATCH_VAR.fullmatch(c[1])):
                    if any(o[0] == "var" and o[1] == c[1] and o[2] == "eq" and o[3] != c[3] for o in theirs):
                        ex.add(h["id"])
                if c[0] == "flag" and not c[1].startswith("FLAG_TEMP") and ("flag", c[1], not c[2]) in theirs:
                    ex.add(h["id"])
            if gf["own"] and gf["own"] == h["own"] and gf["what"] != h["what"] and gf["_key"] == h["_key"] \
                    and gf["id"].rsplit(":", 1)[0] != h["id"].rsplit(":", 1)[0] \
                    and not any(c[0] == "var" and c[1] in counters and not SCRATCH_VAR.fullmatch(c[1])
                                and any(o[1] == c[1] and o != c for o in theirs) for c in mine) \
                    and h["id"].rsplit(":", 1)[0] not in gf["_fwd"] and gf["id"].rsplit(":", 1)[0] not in h["_fwd"]:
                ex.add(h["id"])
        gf["exclusive_with"] = sorted(ex)
    menu_exclusive(gifts, g, by_label)
    link_fixed_choosers(gifts)
    ids = {gf["id"]: gf for gf in gifts}
    for members, *_ in EXCLUSIVE_CITED:  # (F) one prize offered in two places, decided at the decomp
        for a in members:
            if a in ids:
                ids[a]["exclusive_with"] = sorted(set(ids[a]["exclusive_with"]) | ({m for m in members if m in ids}
                                                                                   - {a}))
    for gf in gifts:  # symmetric
        for h in gf["exclusive_with"]:
            if gf["id"] not in ids[h]["exclusive_with"]:
                ids[h]["exclusive_with"] = sorted(ids[h]["exclusive_with"] + [gf["id"]])
    for gf in gifts:
        for k in ("_sets", "_vars", "_common", "own", "_key", "_fwd", "_conds"):
            gf.pop(k, None)


def link_fixed_choosers(gifts):
    """RULE G (fix round 2, item 5): two gifts of one map whose every path tests ONE chooser fixed when the game starts
    (the player's gender, the trainer ID) for DIFFERENT values are alternatives: exclusive_with each other, whatever
    else their paths test. WHY: Lavaridge's Go-Goggles (May's or Brendan's, LavaridgeTown/scripts.inc:55-57), Birch's
    Poke Balls, and the Favor Lady's vs the Quiz Lady's prize (src/lilycove_lady.c:63-65) read as two gifts each."""
    sets ={gf["id"]: [{(c[1], chooser_of_how(how), canon(c[3])) for c, how in p
                        if c[0] == "var" and c[2] == "eq" and chooser_of_how(how) in FIXED_CHOOSERS}
                       for p in gf["_conds"]] for gf in gifts}
    for gf in gifts:
        for h in gifts:
            if h is gf or not set(gf["maps"]) & set(h["maps"]):
                continue
            a, b = sets[gf["id"]], sets[h["id"]]
            if not a or not b or not all(a) or not all(b):
                continue
            # every pair of paths reads one fixed chooser for different values
            if all(any(x[:2] == y[:2] and x[2] != y[2] for x in pa for y in pb) for pa in a for pb in b) \
                    and h["id"] not in gf["exclusive_with"]:
                gf["exclusive_with"] = sorted(gf["exclusive_with"] + [h["id"]])


def menu_switches(g):
    """[(label, line, [arm labels])] of every reachable `switch VAR_RESULT` whose value a MENU produced (multichoice,
    multichoicedefault, multichoicegrid, a yes/no box: Graph.producer). The arms are the `case` targets plus the `goto`
    right after the last case (the default arm: the Trick House tent menu is `case 0, Red` + `goto Blue`)."""
    out = []
    for name, lab in sorted(g.labels.items()):
        if not g.reachable(name):
            continue
        body = lab["body"]
        for i, (ln, code) in enumerate(body):
            mn, args = cmd(code)
            if mn != "switch" or args[:1] != ["VAR_RESULT"]:
                continue
            p = g.producer(name, ln, "VAR_RESULT")
            if not (p and p[0] == "cmd" and p[1] in ("multichoice", "yesno")):
                continue
            arms = []
            for _, code2 in body[i + 1:]:
                mn2, a2 = cmd(code2)
                if mn2 == "case" and len(a2) == 2:
                    if a2[1] in g.labels and a2[1] not in arms:
                        arms.append(a2[1])
                    continue
                if mn2 == "goto" and a2 and a2[0] in g.labels and a2[0] not in arms:
                    arms.append(a2[0])
                break
            out.append((name, ln, arms))
    return out


def arm_labels(g, arm, switch_label):
    """The labels one menu arm runs (goto, call, the branches, case, fall), never re-entering the menu's own label: an
    arm that loops back to the menu ('choose a different one') is not thereby a part of every other arm."""
    seen, todo = set(), [arm]
    while todo:
        x = todo.pop()
        if x in seen or x == switch_label or x not in g.edges:
            continue
        seen.add(x)
        if len(seen) > MAX_CLOSURE:
            break
        todo += [t for t, kind, *_ in g.edges[x] if kind in ("goto", "call", "goto_if", "call_if", "case", "fall")]
    return seen


def menu_exclusive(gifts, g, by_label):
    """RULE E (fix round 1, F3): gift lines in DIFFERENT arms of one menu switch are ONE choice: each is exclusive_with
    the gifts of the sibling arms (a gift every arm reaches is in none). WHY: the Deep Sea Tooth / Scale
    (SlateportCity_Harbor/scripts.inc:324 MULTI_STERN_DEEPSEA) and the Red / Blue Tent (Route110_TrickHouseEnd/
    scripts.inc:165, Route110_TrickHouseEntrance/scripts.inc:403 MULTI_TENT) read as independent gifts in round 0.
    Not between two `repeatable` gifts: nothing after either changes state, so the menu can be opened again for the
    other. A var-valued gift reached through an arm says chosen_by `choice` where it had no chooser."""
    for name, ln, arms in menu_switches(g):
        members = [{h["id"] for x in arm_labels(g, a, name) for h in by_label.get(x, [])} for a in arms]
        for i, mine in enumerate(members):
            others = set().union(*[m for j, m in enumerate(members) if j != i]) if len(members) > 1 else set()
            for gid in mine - others:
                gf = next(x for x in gifts if x["id"] == gid)
                if isinstance(gf["what"], dict) and gf["what"].get("chosen_by") == "unknown":
                    gf["what"]["chosen_by"] = "choice"
                    gf["what"]["words"] = WORDS_BY_CHOOSER["choice"]
                for hid in others - mine:
                    h = next(x for x in gifts if x["id"] == hid)
                    if gf["repeat"] == "repeatable" and h["repeat"] == "repeatable":
                        continue
                    if hid not in gf["exclusive_with"]:
                        gf["exclusive_with"] = sorted(gf["exclusive_with"] + [hid])


def paid_with(g, lab, ln):
    """coins / money when the purchase's label or a predecessor removes them; else None."""
    seen = [lab] + [p[0] for p in g.preds.get(lab, [])]
    for x in seen:
        for _, code in g.labels[x]["body"]:
            mn = cmd(code)[0]
            if mn == "removecoins":
                return "coins"
            if mn == "removemoney":
                return "money"
    return None


def mart_items(g, list_label):
    """The `.2byte` entries of a mart list up to its terminator. GUARD: a list with no terminator refuses."""
    lab = g.labels.get(list_label)
    if lab is None:
        raise Refused("mart list %s is no label" % list_label)
    out = []
    for _, code in lab["body"]:
        mn, args = cmd(code)
        if mn == "pokemartlistend" or (mn == ".2byte" and args and args[0] in ("ITEM_NONE", "DECOR_NONE", "0")):
            return out
        if mn == ".2byte" and args:
            out.append(args[0])
        elif mn not in (".align",):
            break
    raise Refused("mart list %s has no terminator (pokemartlistend / ITEM_NONE / 0)" % list_label)


def flag_setters(g, flag, is_set):
    """F6 (fix round 1), R-2 BY REFERENCE: where a mart list's tested flag gets the value the list needs, as
    [{flag, ref, label, reached_by: [{ref, test}]}] (developer-only, under `dev`). `reached_by` is each line that jumps
    or calls into the setter's label, with the test it makes there. The Petalburg mart's expanded list needs
    FLAG_PETALBURG_MART_EXPANDED_ITEMS, set only in data/event_scripts.s (Common_EventScript_ReadyPetalburgGymForBattle),
    which the four gyms call at VAR_PETALBURG_GYM_STATE 6: no script in Petalburg says so. Words still only from a rule."""
    out = []
    for name, lab in sorted(g.labels.items()):
        if not g.reachable(name):
            continue
        for ln, code in lab["body"]:
            mn, args = cmd(code)
            if mn == ("setflag" if is_set else "clearflag") and args and args[0] == flag:
                by = sorted({(ref(g.labels[src], eln), cond_text(c) if c else None)
                             for src, kind, eln, c, _ in g.preds.get(name, [])
                             if kind in ("goto", "call", "goto_if", "call_if", "case", "fall") and g.reachable(src)},
                            key=lambda x: (x[0], x[1] or ""))
                out.append({"flag": flag, "ref": ref(lab, ln), "label": name,
                            "reached_by": [{"ref": r, "test": t} for r, t in by]})
    return out


def build_marts(g, mart_lines, roots, givers, labels, when_null, names, ctx=None):
    """One record per clerk script (the root label whose closure holds pokemart lines); one list per pokemart line."""
    by_root = {}
    for name, ln, mn, args, idx in mart_lines:
        for i in idx:
            by_root.setdefault(roots[i]["label"], []).append((name, ln, mn, args, i))
    marts = []
    for root_label in sorted(by_root, key=lambda k: (labels[k]["file"], labels[k]["line"])):
        entries = sorted(set((n, ln, mn, tuple(a)) for n, ln, mn, a, _ in by_root[root_label]),
                         key=lambda e: (labels[e[0]]["file"], e[1]))
        idx = sorted({i for *_, i in by_root[root_label]})
        lists = []
        for name, ln, mn, args in entries:
            paths = g.paths_to(name, ln)
            when, dev, unworded = when_of(paths, None, names, g, None, ctx)
            dev["ref"] = ref(labels[name], ln)
            # (a TEMP flag is cleared on entering a map: a setter of it on another map says nothing about this list)
            setters = [s for c in sorted({c for c, _ in common_tests(paths) if c[0] == "flag"
                                          and not TEMP_NAME.fullmatch(c[1])}) for s in
                       flag_setters(g, c[1], c[2])]
            if setters:
                dev["setters"] = setters
            lists.append({"label": args[0], "kind": MART_CMDS[mn], "items": mart_items(g, args[0]), "when": when,
                          "dev": dev, "ref": ref(labels[name], ln)})
            if when is None:
                when_null.append({"id": "mart %s %s" % (root_label, args[0]), "dev": {"unworded": unworded}})
        marts.append({"id": root_label, "maps": sorted({roots[i]["map"] for i in idx}), "clerk": givers(idx),
                      "lists": lists})
    return marts


def mystery_lines(d, gift_files):
    """R-3: the watched lines of the mystery-gift scripts, excluded and counted (not solo vanilla play)."""
    out = []
    for rel in gift_files:
        for ln, code in vanilla_lines(d.read(rel), rel):
            mn, args = cmd(code.strip())
            if mn in WATCHED:
                out.append({"ref": "%s:%d" % (rel, ln), "label": None, "command": mn,
                            **operand(args),
                            "why": "mystery gift (data/mystery_gift.s): an event distribution, not solo vanilla play"})
    return out


def build_tm_hm(d, gifts, marts, purchases, maps_json):
    """Every TM and HM with every source: gift ids, maps.json item-ball / hidden-item pointers (R-1: no coordinates),
    mart lists, purchases."""
    rows = []
    for item in tm_hm_items(d):
        src = []
        for gf in gifts:
            w = gf["what"]
            if w == item or (isinstance(w, dict) and isinstance(w.get("one_of"), list) and item in w["one_of"]):
                src.append({"gift": gf["id"]})
        for m in maps_json["maps"]:
            for lst, kind in (("item_balls", "field_item"), ("hidden_items", "hidden_item")):
                for i, it in enumerate(m.get(lst) or []):
                    if it["item"] == item:
                        src.append({kind: {"maps_json": {"map": m["id"], "list": lst, "index": i}}})
        for mt in marts:
            for i, lst in enumerate(mt["lists"]):
                if item in lst["items"]:
                    src.append({"mart": {"id": mt["id"], "list": i}})
        for p in purchases:
            w = p["what"]
            if w == item or (isinstance(w, dict) and isinstance(w.get("one_of"), list) and item in w["one_of"]):
                src.append({"purchase": p["id"]})
        rows.append({"item": item, "kind": "hm" if item.startswith("ITEM_HM") else "tm", "sources": src})
    return rows


# ---------------------------------------------------------------- the R-4..R-7 doors
def dev_key_hits(obj, path="$", in_dev=False):
    """R-4: every key named flag/flags/var/vars, and every string holding a FLAG_/VAR_ name, outside a `dev` dict."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            inside = in_dev or k == "dev"
            if not in_dev and k in DEV_KEYS:
                out.append("%s.%s (key)" % (path, k))
            out += dev_key_hits(v, "%s.%s" % (path, k), inside)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += dev_key_hits(v, "%s[%d]" % (path, i), in_dev)
    elif isinstance(obj, str) and not in_dev and NAME_RE.search(obj):
        out.append("%s = %r" % (path, obj[:60]))
    return out


def refuse_dev_keys(obj):
    hits = dev_key_hits(obj)
    if hits:
        raise Refused("R-4: flag/var names outside a `dev` dict: %s" % hits[:5])


def dev_names(obj):
    """Every name in a `dev` dict's flags / vars lists."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "dev" and isinstance(v, dict):
                out |= set(v.get("flags") or []) | set(v.get("vars") or [])
                if v.get("own"):
                    out.add(v["own"])
            else:
                out |= dev_names(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= dev_names(v)
    return out


def defined_names(d):
    names = set()
    for rel in ("include/constants/flags.h", "include/constants/vars.h"):
        names |= set(re.findall(r"^#define\s+((?:FLAG|VAR)_\w+)", d.read(rel), re.M))
    return names


def check_dev_names(obj, defined):
    """GUARD R-5: every `dev` flag/var name is #defined in flags.h / vars.h at the pin (not emerald.txt: it lacks 9 real
    names and misspells FALLARBOR)."""
    bad = sorted(n for n in dev_names(obj) if n not in defined)
    if bad:
        raise Refused("R-5: dev names not #defined in include/constants/flags.h or vars.h: %s" % bad[:8])


def table_cites():
    """[(table entry, 'path:line', token)] of every cited table entry: CHOOSER_CITED and MAP_CONDITIONS."""
    out = []
    for name, (_, *cites) in sorted(CHOOSER_CITED.items()):
        out += [("CHOOSER_OF " + name, c, t) for c, t in cites]
    for name, (_, *cites) in sorted(MAP_CONDITIONS.items()):
        out += [("MAP_CONDITIONS " + name, c, t) for c, t in cites]
    # fix round 2: every new cited table is checked the same way (items 1, 3, 4, 5, 6)
    for table, rows in (("NEVER_CONTINUES", NEVER_CONTINUES), ("ROOM_PRODUCERS", ROOM_PRODUCERS),
                        ("POSSESSION", POSSESSION)):
        out += [("%s %s" % (table, k), c, t) for k, (c, t) in sorted(rows.items())]
    for name, e in sorted(SPECIAL_EFFECTS.items()):
        out += [("SPECIAL_EFFECTS " + name, c, t) for c, t in e[4:]]
    for name, e in sorted(SPECIAL_STATES.items()):
        out += [("SPECIAL_STATES " + name, c, t) for c, t in e["cites"]]
    for key, (_, *cites) in sorted(SPECIALVAR_WORDS.items()):
        out += [("SPECIALVAR_WORDS %s=%s" % key, c, t) for c, t in cites]
    for ids, _, *cites in EXCLUSIVE_CITED:
        out += [("EXCLUSIVE_CITED " + ids[0], c, t) for c, t in cites]
    for key, (_, *cites) in sorted(LINE_WORDS.items()):
        out += [("LINE_WORDS %s" % key[0], c, t) for c, t in cites]
    out += [("FINITE_DOMAINS VAR_FACING", c, t) for c, t in FINITE_CITES]
    # fix round 3 (item 1): the sole-writer rule's tables
    for name, (_, *cites) in sorted(WRITER_CMDS.items()):
        out += [("WRITER_CMDS " + name, c, t) for c, t in cites]
    out += [("REMOVEOBJECT_SETS", REMOVEOBJECT_SETS[0], REMOVEOBJECT_SETS[1])]
    for key, _, _, _, *cites in C_RANGES:
        out += [("C_RANGES " + key, c, t) for c, t in cites]
    for name, (_, _, *cites) in sorted(REARM.items()):
        out += [("REARM " + name, c, t) for c, t in cites]
    for name, cites in sorted(CITED_READS.items()):
        out += [("CITED_READS " + name, c, t) for c, t in cites]
    out += [("TRAINER_FLAG_SET", TRAINER_FLAG_SET[0], TRAINER_FLAG_SET[1]),
            ("TRAINER_FLAG_CLEAR", TRAINER_FLAG_CLEAR[0], TRAINER_FLAG_CLEAR[1]),
            ("TEMP_CLEAR", TEMP_CLEAR[0], TEMP_CLEAR[1])]
    return out


def check_cites(d):
    """GUARD F4: every CHOOSER_OF / MAP_CONDITIONS entry's cited line holds its token at the pin. WHY: a chooser word
    the AI acts on ('random' vs 'choice') must rest on a line someone can open; a pin bump that moves the line refuses
    instead of leaving a stale fact."""
    bad = []
    for entry, where, token in table_cites():
        rel, n = where.rsplit(":", 1)
        lines = d.read(rel).split("\n")
        if int(n) > len(lines) or token not in lines[int(n) - 1]:
            bad.append("%s: %s does not hold %r" % (entry, where, token))
    if bad:
        raise Refused("cited table lines do not hold their tokens: %s" % bad[:4])


def check_maps_json(maps_json, sha):
    """GUARD R-1: the maps.json the pointers index was extracted from THIS decomp commit."""
    if maps_json.get("_source") != "pret/pokeemerald@" + sha:
        raise Refused("maps.json is from %r, the decomp read here is %s: regenerate slice 1 first"
                      % (maps_json.get("_source"), sha))


def refuse_all(obj, defined):
    refuse_dev_keys(obj)
    check_dev_names(obj, defined)
    hits = ew.route_keys(obj)
    if hits:
        raise Refused("R-6: route keys %s (never routes, coordinates or step lists)" % hits[:5])
    ew.refuse_withheld(OUT_NAME, obj)


# ---------------------------------------------------------------- run
def build_all(d, maps_path):
    with open(maps_path, "rb") as f:
        raw = f.read()
    maps_json = json.loads(raw.decode("utf-8"))
    check_maps_json(maps_json, d.sha)
    trainers_path = os.path.join(os.path.dirname(maps_path), "trainers.json")
    with open(trainers_path, "rb") as f:
        traw = f.read()
    names = {t["symbol"]: ("%s %s" % (t.get("class_name") or "", t["name"])).strip()
             for t in json.loads(traw.decode("utf-8"))["trainers"]}
    res = build(d, maps_json, names)
    digest = hashlib.sha256("\n".join("%s %s" % kv for kv in sorted(d.used.items())).encode()).hexdigest()
    obj = {
        "_generated": {"made_by": MADE_BY, "slice": "spec S3-4 slice 2, stage 2a (KB2)",
                       "files_read": len(d.used), "files_digest": digest,
                       "inputs": {"maps.json": hashlib.sha256(raw).hexdigest(),
                                  "trainers.json": hashlib.sha256(traw).hexdigest()},
                       "max_closure": res["max_closure"]},
        "_source": "pret/pokeemerald@" + d.sha,
        "_kind": "static game knowledge (USER RULING 40)",
        "_reader": ew.READER,
        "_notes": {
            "when": "words for the AI: a rule-worded test (badges, the Hall of Fame, a chooser, a var value set only "
                    "in the Hall of Fame) or 'no condition beyond `repeat`' (only when dev.tests is empty); null = a "
                    "test or a map condition no rule words (listed in _when_null, never invented)",
            "dev": "developer-only (R-4): the tests on every path to the line, the gift's own flag/var, the line",
            "repeat": "once / until_received (a full bag leaves it offered) / daily / weekly / repeatable (nothing after "
                      "the gift changes saved state) / unknown (it changes state, but no link to how the gift is "
                      "reached could be shown: listed in repeat_unknown)",
            "repeat_unknown": res["repeat_unknown"],
            "what": "a constant, or {one_of, chosen_by, words, refs} resolved from the var's writers, or one_of "
                    "'unknown' + chosen_by + why",
            "exclusive_with": "gifts that taking this one removes (map.json hide flags, a choice var, an earlier "
                              "choice, a shared once-guard, the arms of one menu)",
            "field_items": "maps.json (slice 1: item_balls, hidden_items); tm_hm points at them by map + list + index",
            "dead": "labels no map.json event, map script or C line reaches; never in an AI-facing record",
            "excluded": "R-3: mystery gift and record-mixing scripts, and the item machinery itself (C-only)",
        },
        "field_items": "maps.json",
        "gifts": res["gifts"], "marts": res["marts"], "tm_hm": res["tm_hm"], "purchases": res["purchases"],
        "dead": res["dead"], "excluded": res["excluded"], "_when_null": res["when_null"],
    }
    refuse_all(obj, defined_names(d))
    return obj, res


def write_output(out_dir, obj, d):
    """The ONE door to disk: R-4..R-7 run again here, so no path writes a file they have not seen."""
    refuse_all(obj, defined_names(d))
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
    ap.add_argument("--maps", default=os.path.join(OUT_DEFAULT, "maps.json"), help="slice 1's maps.json (R-1)")
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
                print("[KB2-ITEMS] CHECK FAILED: %s differs or is missing (regenerate: py -3.12 "
                      "ai_player/gates/extract_items.py)" % OUT_NAME)
                return 1
            print("[KB2-ITEMS] CHECK OK: %s identical to a fresh extraction" % OUT_NAME)
            return 0
        obj = run(root, a.out, a.maps)
        print("[KB2-ITEMS] wrote %s: gifts %d, marts %d, tm_hm %d, purchases %d, dead %d, excluded %d, when null %d" % (
            os.path.join(a.out, OUT_NAME), len(obj["gifts"]), len(obj["marts"]), len(obj["tm_hm"]),
            len(obj["purchases"]), len(obj["dead"]), len(obj["excluded"]), len(obj["_when_null"])))
        return 0
    except Refused as exc:
        print("[KB2-ITEMS] REFUSED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
