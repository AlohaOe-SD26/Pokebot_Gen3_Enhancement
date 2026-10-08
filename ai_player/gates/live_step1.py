"""LIVE PROOF of AI-player build step 1 (the EYES): the watcher's Observations against ground truth.

    py -3.12 ai_player/gates/live_step1.py [--arms E1,E2,E2X,E3,E4,E5,E6,E7,E8,E9,E10,XW,SC,GEO,XG]

Each live arm runs the REAL launcher (`py -3.12 -m ai_player run`, which gates the real package first)
with `AI_PLAYER_BRAIN=watcher` on a pinned fixture: the watcher looks every 60 frames for 600 frames,
writes every Observation to the action log (`<run_dir>/actions.jsonl`) and the scorer lines to the run's
log, and presses nothing. The arm then compares the watcher's FIRST Observation with GROUND TRUTH that
`gates/probe_eyes.py` reads from the same fixture, on the same frame, by a SECOND PATH (its docstring
lists, per fact, which memory and which code: another copy the game keeps, the probe's own decoder of
the game's bytes, or the game's BEHAVIOUR under one press in the probe's throwaway emulator), and with
the fixture's DOCUMENTATION where it says something. Every check QUOTES both values. A value read from
the SAME bytes as the eyes is never called truth: it is labelled CONSISTENCY or SAME BYTES.
Evidence: `ai_player/evidence/<date>-step1-<ARM>.txt`. Exit 0 only if every arm passed.

WHAT EVERY WATCHER ARM MUST ALSO SHOW (purity): the instrument's verdict file says CLEAN, `ai_presses=0`,
every breach counter 0 (incl. `ai_bot_calls`: the eyes ran no bot code), `real_frames >= 600`, and the
run ended `reason=watcher-done code=0` by itself. The verdict file is written by the instrument, so no
line the AI prints can fake it.

PRE-REGISTERED PREDICTIONS (2026-10-07, written before the graded runs; from probes of the fixtures)
------------------------------------------------------------------------------------------------------
THE PROBE READS THE FRAME OF THE FIRST LOOK (`--settle 0`: the mode's first step comes before the main
loop's first frame), and EVERY arm with a probe asserts it (a first graded run used a 1-frame settle and
failed "same frame" everywhere: a correction of the instrument, recorded, not of the eyes).
EVERY ARM WITH A PROBE (E1-E9, SC) ALSO checks, against the probe's second path:
  * MAP (group, number): the live gMapHeader is byte-identical to exactly ONE header of the ROM table
    `gMapGroups`, walked by the probe; the NAME: that header's region-map section -> `gRegionMapEntries`
    -> decoded by the probe's own charmap (the eyes use the framework's `map_name`);
  * POSITION: save block 1 `pos` (the eyes: the player object's currentCoords - 7);
  * FACING on the overworld (E1, E2, E3, E6, E8, E9): what is DRAWN, the player sprite's animation
    (`gSprites[].animNum` in ANIM_STD order S,N,W,E) and its OAM hFlip (set only for the east frame); in
    a battle or a full-screen menu (E4, E5, E7) the overworld sprites are freed and the game keeps NO
    second copy: there the line says CONSISTENCY ONLY (the same byte, decoded by test code);
  * IN BATTLE: `gMain.inBattle` (a bit; the eyes read callback1);
  * PROGRESS: money (save block 1 XOR the key), badges and the ten story flags (bits at the decomp's
    flag ids), Pokedex owned and seen (the game's own rule: the bit in all of save block 2's owned/seen
    and save block 1's seen1/seen2), the balls (the poke-ball pocket, names from the ROM's gItems by the
    probe's charmap) and the healing items (items + berries whose ROM use function is
    ItemUseOutOfBattle_Medicine or ItemUseInBattle_Medicine);
  * PARTY: the framework's `get_party()` (its own decryption; the eyes decrypt with their own code):
    species, level, HP, max HP, PID, and (round 2) every move with its PP and max PP, and the status;
  * THE MAP-HEADER CHECK (round 2, the verifier: the old guard "cannot fire"): in the probe's own
    emulator a fresh look on the unchanged state reports no header problem, and with ANOTHER map's ROM
    header written over `gMapHeader` a fresh look refuses it ("is not map ...") and reports no player;
  * WAITS (round 2): the behaviour test now looks on every IDLE frame too (300 of them): every idle frame
    on which a text PRINTS must read waits=False, and every idle frame from which the screen sits still
    until the press, when the press then moves that text, waits=True (`probe_eyes.behaviour`).
ROUND 2 PREDICTIONS (2026-10-07, after the verifier found the eyes blind to RENDER_STATE_WAIT = 1, the
`{PAUSE_UNTIL_PRESS}` wait; written from probe runs of the fixtures, before the graded runs):
  * BATTLE SIDES (E4, E5, E10): the raw `gBattleMons` parse is the SAME bytes the eyes read, so that line
    now says CONSISTENCY ONLY; the TRUTH is the second copy, the party struct with the SAME PID
    (`gPlayerParty` / `gEnemyParty`, the framework's decryption: species, level, HP, max HP, status,
    moves with PP and max PP) and the species table's types (compared as sets);
  * OBJECTS on the overworld (the player drawn at (112, 72)): WHAT IS DRAWN, each object's sprite placed on
    screen relative to the player's: a still object is drawn exactly on its coordinates (mid-step: within
    one tile), and the eyes see exactly the still objects drawn inside the window (E2: the item ball local 7
    is DRAWN at screen x 240, past the 240-px screen);
  * `gTextFlags` in a battle (E4, E5, E10): bit 1 (useAlternateDownArrow, set by BattlePutTextOnWindow)
    set and nothing above bit 3: the bit-fields run from bit 0, so autoScroll is bit 2, as the eyes assume.
E1  TOWN `dewford.ss1` (README: "Dewford Town (11,9)"). PREDICT map DEWFORD TOWN (0,11), xy (11,9),
    facing right (sprite anim 7 = GO_EAST, hFlip on), screen overworld, no Task_DrawFieldMessage; every
    on-screen object of the probe's raw `gObjectEvents` parse is seen and nothing else; every in-map tile
    of the window agrees with the ROM layout decoded BY THE PROBE (metatile, behaviour, collision,
    elevation, the ROM header's warps) and with the framework's `MapLocation` (encounters, water, tall
    grass, and ledges and doors by the FRAMEWORK's behaviour names); NON-VACUITY: 2 doors and 2 warps in
    the window. BEHAVIOUR: no text on screen, so waits=False is the truth; the probe's own A press makes
    the NPC at dx=+1 talk: on every frame its text PRINTS by itself the eyes say waits=False, on every
    frame it then sits still they say waits=True. The scorer reads the run as starter Mudkip, 1 map;
    PARITY: dex_owned 0, badges [] and money_last None although the game holds 7 owned and 1 badge (the
    scorer only counts what HAPPENS in a run, from the bot's own line formats).
    CONTROL on every tile check (E1, E2, E3, E6, E8, E9): the same comparison against the eyes' window
    SHIFTED one column finds mismatches (> 0), so "no mismatches" is not true by construction.
E8  MAP EDGE `fallarbor.ss1` (Fallarbor Town (14,8), 20 tiles wide: the window reaches 2 columns past
    the east edge, where Route 113 is connected). PREDICT the 22 tiles past the edge equal the NEIGHBOUR
    map's own ROM tiles (the probe maps them through the connection), and nothing mismatches.
E2  ROUTE WITH TALL GRASS, the ITEM BALL OFF SCREEN `route116team.ss1` (FIXTURES.md5: "ROUTE116 (11,7),
    NO badges, party of 4 by PID: Mudkip#550A9BE6 L13 37/40, Poochyena#5815089E L4 16/17,
    Nincada#4457D0FB L6 20/20, Whismur#7E9BB3BA L6 23/23; ₽824"). PREDICT all of that read back; tall
    grass in the view; NON-VACUITY of the ledge check: 8 ledge tiles (5 west, 1 southwest, 2 south) in the
    window; THE CROP: the item ball (local id 7) that the probe finds ACTIVE in `gObjectEvents` at dx=+8
    (one column past the right edge) is ABSENT from all 10 Observations, while the trainer at dx=+1
    (local id 3) is PRESENT in all 10.
E2X FAULT `AI_PLAYER_FAULT_NO_CROP=1`, same fixture. PREDICT the item ball local 7 PRESENT at (+8,-1) and
    signs 18+ columns away present, `cropped=false`; purity still CLEAN (the fault is in what the eyes
    report, not in what they do). This is what makes E2's "absent" a measurement.
E3  ROUTE WITH TALL GRASS, the ITEM BALL ON SCREEN `boxwithdraw.ss1` (Route 121; CHANGELOG: "party 6").
    PREDICT the item ball local 29 seen as `item_ball` at (-6,-1), tall grass in the view, a party of 6;
    the bag's one healing item (Hyper Potion) and its one other (X Attack, not healing).
E4  WILD BATTLE `oldale.ss1` (live_step0: "a WILD battle on Route 101"). PREDICT screen battle, kind
    wild, own Mudkip L8 19/28 Water vs foe Wurmple L2 14/14 Bug, equal to the probe's raw `gBattleMons`;
    the own battler IS party slot `gBattlerPartyIndexes[0]`; no overworld view; no battle-end line;
    BEHAVIOUR: the battle's text waits for A (still for 300 frames, the press moves it): eyes waits=True,
    on the first look and on every idle frame (round 2: NON-VACUITY > 0 idle waiting frames, reason
    `text printer 0 CLEAR`); while the next text prints the eyes say waits=False.
E5  TRAINER BATTLE `trainer_battle_r116.ss1` (make_trainer_fixture: Route 116, a trainer battle at its
    first decision). PREDICT kind trainer, own Grovyle L16 vs Machop L9, equal to the raw parse; the
    OPPONENT id the eyes read (`gTrainerBattleOpponent_A`) == the trainer who STARTED the battle, read
    without that variable: `gSpecialVar_LastTalked` = local 3 -> the ROM template's script
    `Route116_EventScript_Joey` -> `trainerbattle` (0x5c) type 0, trainer 322; the ROM's `gTrainers[322]`
    is named JOEY with party [Machop L9] == the live `gEnemyParty`, and no other of the 855 trainers has
    that party; documentation: pret/pokeemerald `include/constants/opponents.h` TRAINER_JOEY 322.
    BEHAVIOUR as E4.
E6  TEXT BOX `ki15_nurse_wedge.ss1` (CHANGELOG: "the Rustboro nurse dialogue", re-opened forever).
    PREDICT screen text, text box open, and Task_DrawFieldMessage in the probe's own task parse (the
    task that draws the field message box and lives until it closes; the eyes read the box's mode byte);
    the map is the Rustboro Pokemon Center; the nurse (graphics 58, OBJ_EVENT_GFX_NURSE) is seen; the
    window's 3 warps. WAITS: BEHAVIOUR is the truth: the text is still for 300 frames with no input and
    the one A press moves it, so waits=True (and on every idle frame, > 0); after the press, on every frame the next paragraph PRINTS
    the eyes say waits=False (NON-VACUITY: > 0 such frames), and when it sits still again, True.
E7  MENU `ki17_partymenu_wedge.ss1` (KI archive: "state=PARTY_MENU ... Skitty 40HP alive, Taillow+Grovyle
    fainted", input-immune). PREDICT screen menu, menu party, in battle, no overworld view; truth: the
    probe names gMain.callback2 CB2_UpdatePartyMenu, gPartyMenu.menuType = 1 (IN_BATTLE) and the
    inBattle bit is set; Skitty hp 40, Taillow and Grovyle hp 0; waits=False, and BEHAVIOUR agrees: the
    party menu's message (text printer 6) moves BY ITSELF during the idle frames, i.e. it is printing,
    not waiting for a button. ROUND 2 (a NATURAL capture of the state-1 wait): that message is
    "SKITTY is already / in battle!{PAUSE_UNTIL_PRESS}" (`src/strings.c` gText_PkmnAlreadyInBattle); it
    prints for ~108 frames (> 0 idle printing frames, waits=False) and then sits in RENDER_STATE_WAIT on
    PRINTER 6 until the press moves it: on every one of those idle frames (> 0) the eyes say waits=True
    with reason `text printer 6 WAIT`. Before the fix (printer 0 only, states 2 and 3) that read False;
    arm XW measures it. Skitty's PARALYSIS makes the party status check non-vacuous.
E10 TRAINER DEFEAT TEXT `trainer_defeat_text_r116.ss1` (NEW, built by `gates/make_defeat_text_fixture.py`
    from E5's fixture by PLAYING the battle with button presses only: Quick Attack until Machop faints;
    it stops on the first frame text printer 0 is in state 1). PREDICT screen battle, kind trainer, the
    opponent 322 (JOEY, as E5), own Grovyle L16 46/47, foe Machop L9 0/31, both equal to the second copy;
    printer 0's text, decoded by the probe's charmap, is Joey's defeat text with the two control bytes the
    battle engine appends, "Ouch! A scrape!<FE>I have to put on a bandage!<FC><09>" (pret/pokeemerald
    data/text/trainers.inc Route116_Text_JoeyDefeat; src/battle_message.c appends EXT_CTRL_CODE_BEGIN 0xFC,
    EXT_CTRL_CODE_PAUSE_UNTIL_PRESS 0x09), state 1; the eyes say waits=True, reason `text printer 0 WAIT`;
    BEHAVIOUR: still for all 300 idle frames, the press moves the text: truth True, and waits=True on every
    idle frame (> 0); after the press "NICK got ₽144 for winning!" (ending in a paragraph break) PRINTS (> 0 frames, waits=False)
    and then waits at its down arrow (> 0 frozen frames, waits=True, reason CLEAR); the battle outcome the
    eyes read is 1 (Won) and every Pokemon of the enemy party has 0 HP (the second copy); no battle-end line.
XW  THE FIX, REVERTED (probes only, on copies of the package; the step-0.1 mutant pattern). Three copies:
    XW-0 unchanged (CONTROL), XW-A the pre-fix wait states {2, 3}, XW-B the pre-fix printer count 1. Each
    copy's probe runs on E10's and E7's fixtures and reports which eyes module and which rule it ran.
    PREDICT XW-0: no wrong frame and the first look right on both. XW-A: E10's first look reads False
    against a truth of True and every idle waiting frame is wrong; E7's idle waiting frames are all wrong.
    XW-B: E10 passes (its wait is on printer 0), E7's idle waiting frames are all wrong (printer 6). So
    each half of the fix is shown to be load-bearing on a natural capture.
E9  BAG `post_league_lobby.ss1` (FIXTURES.md5: "EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (3,4) ... the L75
    party"). PREDICT the map and position of the documentation; the bag check NON-VACUOUS both ways: 7
    healing items (Potion, Antidote, Super Potion, Hyper Potion, Full Restore, Full Heal, Revive) and 5
    other items (Nugget, X Attack, Escape Rope, Repel, King's Rock), each quantity equal to the probe's
    decode.
SC  SCORER on a REAL run: a watcher run on E2's fixture, its own `ai_player.log` through
    `ai-agent/scoring.py` `parse_log`. PREDICT starter Mudkip, maps_visited 1, no catches, no badges;
    frames, end_map, end_pos and end_party = the LAST look's (from the closing `[hb] ... end=1`); and each
    AI scorer line (starter, map, heartbeat) matches the scorer's own regex. PARITY (the verifier's note:
    "a save-started run gets a human_score built on dex 0"): dex_owned 0 because the owned count did not
    change in the run (4 -> 4) and the AI writes `[DEX]` only on a change, exactly as the bot's logger
    does (the arm QUOTES that line of `sandbox-pokebot/modules/debug_logger.py`, and fails if it is gone).
    (The first graded run predicted frames = the last look WITHOUT a closing heartbeat and failed: the
    scorer's `frames` is the last line it reads; the closing heartbeat was added, as the bot's own `[hb]`
    gives the scorer its end state. The full event set is proven on a synthetic log in
    `gates/test_eyes.py`; a watcher that presses nothing cannot make a battle end.)
GEO THE WINDOW, MEASURED (no AI run: the probe's throwaway emulator). On the overworld fixtures of E1,
    E2, E3, E6: PREDICT the player sprite's tile drawn at screen (112, 72), camera pans (0, 32), columns
    -7..+7 and rows -5..+5 on screen with rows -5 and +5 half visible, i.e. `eyes/view.py`'s window.
    CONTROL: on the battle fixture of E4 the same measurement does NOT give (112, 72) (the battle reuses
    the sprite), so the check is not true by construction.
XG  FAULT HALF OF THE TRUTH CHECKS (no emulator; needs E1-E7 and E10 in the same invocation). Each check above
    that the verifier called weak, and each new one, is re-run on a COPY of a graded arm's data with ONE
    value made wrong and must FAIL with its own line, while the unchanged copy passes: on the EYES' side
    (facing, map name and number, in battle, money, a badge, a story flag, Pokedex seen, a ball count,
    a healing item, a ledge, a warp, a metatile, the trainer id, waits in E6 and in E7) and on the
    TRUTH's side (the sprite's facing and its hFlip, the probe's badge bit, its ROM behaviour of a tile,
    the script's trainer argument, the behaviour's "the press moved the text", Task_DrawFieldMessage,
    gPartyMenu.menuType, and the probe's frame). Round 2 adds: E10's waits, one E7 idle waiting frame, a
    party move's PP and Skitty's status (eyes), the second copy's HP and a foe move's PP, an object's drawn
    position and the item ball drawn on screen, the header guard not refusing, gTextFlags in MSB order,
    and the defeat text without its control bytes (truth). A truth-side mutant that is caught proves the
    check READS its independent signal; a check that only looked at the eyes would pass it.
COST: the probe times 30 looks per fixture (one per frame); each live run prints its own `[AI-EYES] cost`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "ai-agent") not in sys.path:
    sys.path.insert(0, str(REPO / "ai-agent"))

from ai_player.eyes.view import BADGE_FLAGS, STORY_FLAGS, VIEW_DOWN, VIEW_HALF_WIDTH, VIEW_UP  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.options import ENV_BRAIN, ENV_FAULT_NO_CROP, ENV_WATCH_EVERY  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step1"
PROBE = Path(__file__).with_name("probe_eyes.py")
PROFILE = "ai-step1-eyes"
FRAMES, WATCH_EVERY, WALL = 600, 60, 120.0
LOOKS = FRAMES // WATCH_EVERY
#: (path, md5) PINNED: "same name, different bytes" has voided results in this project before.
FIXTURES: dict[str, tuple[Path, str]] = {
    "dewford.ss1": (SAVES / "dewford.ss1", "20bc6a6c9b2f82b25bf7e95af332f171"),
    "route116team.ss1": (SAVES / "route116team.ss1", "9710585350be10534737c4362c33189e"),
    "boxwithdraw.ss1": (SAVES / "boxwithdraw.ss1", "6f6eb29443b82f7d32dcac5f90c7c12d"),
    "oldale.ss1": (SAVES / "oldale.ss1", "df2d885f29e8aaefbacd2cb2d854c93a"),
    "trainer_battle_r116.ss1": (Path(__file__).resolve().parent / "fixtures" / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba"),
    "ki15_nurse_wedge.ss1": (SAVES / "ki15_nurse_wedge.ss1", "0db20ccd4ea2f797e6377fbd4be40042"),
    "ki17_partymenu_wedge.ss1": (SAVES / "ki17_partymenu_wedge.ss1", "0103bfe9881ba83eb8919a06a952938f"),
    "fallarbor.ss1": (SAVES / "fallarbor.ss1", "08b0f60035440c193024fed42c99a99e"),
    "post_league_lobby.ss1": (SAVES / "post_league_lobby.ss1", "5a75ea37ed5cc07ae8b0b0a75da5e909"),
    # built 2026-10-07 by gates/make_defeat_text_fixture.py (its printout: evidence E10, "the fixture")
    "trainer_defeat_text_r116.ss1": (Path(__file__).resolve().parent / "fixtures" / "trainer_defeat_text_r116.ss1",
                                     "d9e1a377f2ac5068871256921a3797db"),
}
#: Joey's defeat text as printer 0 shows it, decoded by the probe's charmap (<FE> = newline): pret/pokeemerald
#: `data/text/trainers.inc` Route116_Text_JoeyDefeat, and the two bytes `src/battle_message.c` appends to every
#: trainer's lose text, EXT_CTRL_CODE_BEGIN (0xFC) + EXT_CTRL_CODE_PAUSE_UNTIL_PRESS (0x09).
JOEY_DEFEAT_TEXT = "Ouch! A scrape!<FE>I have to put on a bandage!<FC><09>"
#: The framework's StatusCondition names, as the eyes name a status (`eyes/view.py` status_name).
STATUS_NAMES = {"Healthy": "ok", "Sleep": "sleep", "Poison": "poison", "Burn": "burn", "Freeze": "freeze",
                "Paralysis": "paralysis", "BadPoison": "toxic"}
#: The player's tile on screen when the camera is centred on a standing player (arm GEO measures it).
PLAYER_TILE_ON_SCREEN = [112, 72]
BREACH_COUNTERS = (
    "foreign_presses", "foreign_writes", "foreign_loads", "ai_writes", "ai_loads", "ai_unrouted_presses", "ai_bot_calls",
    "extra_frames", "unattributed_inputs", "unattributed_state_changes", "instrument_tampered", "instrument_errors",
    "ran_after_finish", "isolation_lost",
)
#: The ROM's own use functions of a healing item (pret/pokeemerald `src/item_use.c`), the truth for the
#: eyes' "healing" (which comes from the framework's item table).
ROM_HEALING_USES = ("ItemUseOutOfBattle_Medicine", "ItemUseInBattle_Medicine")
#: Where the bot writes its `[DEX]` line, for the parity check (the line is QUOTED, so a change shows).
BOT_LOGGER = REPO / "sandbox-pokebot" / "modules" / "debug_logger.py"
BOT_DEX_CONDITION = "if _last_owned is not None and owned - _last_owned:"


@dataclass
class Arm:
    name: str
    title: str
    fixture: str | None  # None: no live run (GEO)
    env: dict[str, str] = field(default_factory=dict)
    doc: str = ""  # what the fixture's documentation says, quoted


@dataclass
class Run:
    arm: Arm
    command: list[str] = field(default_factory=list)
    exit_code: int = -1
    elapsed: float = 0.0
    stdout: str = ""
    run_dir: Path | None = None
    verdict: dict | None = None
    records: list[dict] = field(default_factory=list)
    ai_log: str = ""
    probe: dict | None = None
    probe_raw: str = ""
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def first(self) -> dict:
        return (self.records[0].get("observation") or {}) if self.records else {}

    @property
    def truth(self) -> dict:
        return (self.probe or {}).get("truth") or {}


ARMS: list[Arm] = [
    Arm("E1", "TOWN: Dewford Town", "dewford.ss1", doc="tools/story-dev/README.md: `dewford.ss1` | Dewford Town (11,9)"),
    Arm("E2", "ROUTE 116, tall grass, ledges, an item ball just OFF screen (the crop)", "route116team.ss1",
        doc="FIXTURES.md5: ROUTE116 (11,7), NO badges, party of 4 by PID: Mudkip#550A9BE6 L13 37/40, Poochyena#5815089E "
            "L4 16/17, Nincada#4457D0FB L6 20/20, Whismur#7E9BB3BA L6 23/23; ₽824"),
    Arm("E2X", "FAULT AI_PLAYER_FAULT_NO_CROP: the same fixture, the crop off", "route116team.ss1", {ENV_FAULT_NO_CROP: "1"},
        doc="as E2"),
    Arm("E3", "ROUTE 121, tall grass, an item ball ON screen", "boxwithdraw.ss1",
        doc="07-CHANGELOG: boxwithdraw.ss1 = the end state of the box-catch run: party 6"),
    Arm("E4", "WILD BATTLE on Route 101", "oldale.ss1", doc="live_step0.py: oldale.ss1 = a WILD battle on Route 101"),
    Arm("E5", "TRAINER BATTLE on Route 116", "trainer_battle_r116.ss1",
        doc="make_trainer_fixture.py: Route 116, a trainer battle waiting at its first decision; pret/pokeemerald "
            "include/constants/opponents.h: #define TRAINER_JOEY 322"),
    Arm("E6", "TEXT BOX: the Rustboro nurse dialogue", "ki15_nurse_wedge.ss1",
        doc="07-CHANGELOG: A-mashing re-opened the Rustboro nurse dialogue forever (captured as ki15_nurse_wedge.ss1)"),
    Arm("E7", "MENU: the party menu inside a battle (KI-17)", "ki17_partymenu_wedge.ss1",
        doc="31-KNOWN-ISSUES-ARCHIVE KI-17: state=PARTY_MENU ... run05: Skitty 40HP alive, Taillow+Grovyle fainted; input-immune"),
    Arm("E8", "MAP EDGE: the next route seen across Fallarbor's east edge", "fallarbor.ss1",
        doc="the fixture's name (no table row): Fallarbor Town"),
    Arm("E9", "BAG: seven healing items and five others (the League lobby)", "post_league_lobby.ss1",
        doc="FIXTURES.md5: EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (3,4) (LEAGUE_NURSE_STAND), the L75 party"),
    Arm("E10", "TRAINER DEFEAT TEXT: Joey's lose text waits in RENDER_STATE_WAIT ({PAUSE_UNTIL_PRESS})",
        "trainer_defeat_text_r116.ss1",
        doc="make_defeat_text_fixture.py: E5's battle PLAYED with button presses until text printer 0 is in state 1; "
            "pret/pokeemerald data/text/trainers.inc Route116_Text_JoeyDefeat \"Ouch! A scrape!\\nI have to put on a bandage!$\"; "
            "src/battle_message.c appends EXT_CTRL_CODE_PAUSE_UNTIL_PRESS to every B_TXT_TRAINER1_LOSE_TEXT"),
    Arm("XW", "THE WAITS FIX, REVERTED: the pre-fix states {2,3} and printer count 1, each in a copy, probed on E10 and E7", None,
        doc="probes only, on temporary copies of the package"),
    Arm("SC", "SCORER: a real watcher run's log through ai-agent/scoring.py", "route116team.ss1", doc="as E2"),
    Arm("GEO", "THE WINDOW, MEASURED: the player sprite on screen, the camera pans", None),
    Arm("XG", "FAULT: each new truth check FAILS when one value (the eyes' or the truth's) is made wrong", None,
        doc="re-grades copies of E1-E7's data, no emulator"),
]


# ---------------------------------------------------------------------- running
def clean_env(extra: dict[str, str]) -> dict[str, str]:
    """The shell's environment minus every AI_PLAYER_* variable, plus this arm's (so nothing left in the
    shell can turn a fault on)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    env.update(extra)
    return env


def probe(fixture: str, behaviour: bool = True, root: Path | None = None) -> tuple[dict | None, str]:
    """The probe on one fixture. With `root` (a temporary copy of the package, arm XW), the COPY's probe
    runs and imports the copy's eyes; the build root is passed explicitly (the copy has no sandbox)."""
    path = FIXTURES[fixture][0]
    script = PROBE if root is None else root / "ai_player" / "gates" / PROBE.name
    # --settle 0: the probe reads the frame the state was saved at, which is the frame of the watcher's
    # FIRST look (the mode takes its first step before the main loop runs a frame); measured on the first
    # run of this driver, when a 1-frame settle put the probe one frame after the look on every fixture.
    command = [sys.executable, str(script), "--state", str(path), "--settle", "0", "--repeat", "30"]
    if behaviour:
        command.append("--behaviour")
    env = clean_env({} if root is None else {launcher.ENV_BUILD_ROOT: str(REPO / "sandbox-pokebot")})
    done = subprocess.run(command, cwd=str(REPO), env=env, capture_output=True, timeout=300)
    raw = done.stdout.decode("utf-8", errors="replace") + done.stderr.decode("utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith("PROBE "):
            return json.loads(line[len("PROBE "):]), raw
    return None, raw


def run_watcher(arm: Arm, build_root: Path) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    run.command = [
        sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(FRAMES), "--wall-seconds", f"{WALL:g}",
        "--build-root", str(build_root), "--run-dir", str(run.run_dir), "--state", str(FIXTURES[arm.fixture][0]),
    ]
    env = clean_env({ENV_BRAIN: "watcher", ENV_WATCH_EVERY: str(WATCH_EVERY), **arm.env})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    start = time.monotonic()
    proc = subprocess.Popen(run.command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        raw, _ = proc.communicate(timeout=WALL + 240)
    except subprocess.TimeoutExpired:
        launcher.kill_tree(proc)
        raw, _ = proc.communicate()
        raw = (raw or b"") + b"\n[DRIVER] the run overran the driver's own wall clock; process tree killed\n"
    run.elapsed = time.monotonic() - start
    run.exit_code = proc.returncode if proc.returncode is not None else -9
    run.stdout = raw.decode("utf-8", errors="replace")
    run.verdict = launcher.read_verdict(run.run_dir)
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    log = run.run_dir / "ai_player.log"
    if log.is_file():
        run.ai_log = log.read_text(encoding="utf-8", errors="replace")
    return run


# ---------------------------------------------------------------------- shared checks
def check_purity(run: Run) -> None:
    gate = next((line for line in run.stdout.splitlines() if line.startswith("[AI-GATE] exit=")), "")
    run.check("verdict=PASS" in gate and gate.endswith(f"package={REPO / 'ai_player'}"), f"the launcher gated the real package: {gate or 'MISSING'}")
    verdict = run.verdict or {}
    counters = verdict.get("counters") or {}
    facts = verdict.get("facts") or {}
    run.check(verdict.get("verdict") == "CLEAN", f"verdict file: verdict={verdict.get('verdict')} (want CLEAN)")
    run.check(counters.get("ai_presses") == 0, f"ai_presses={counters.get('ai_presses')} (want 0: the watcher presses nothing)")
    nonzero = {k: counters.get(k) for k in BREACH_COUNTERS if counters.get(k) != 0}
    run.check(not nonzero, f"every breach counter 0, incl. ai_bot_calls={counters.get('ai_bot_calls')} (non-zero: {nonzero or 'none'})")
    run.check((counters.get("real_frames") or 0) >= FRAMES, f"real_frames={counters.get('real_frames')} (want >= {FRAMES})")
    run.check(facts.get("exit_reason") == "watcher-done" and facts.get("exit_code") == 0 and run.exit_code == 0,
              f"ended by itself: exit_reason={facts.get('exit_reason')} exit_code={facts.get('exit_code')} process={run.exit_code}")
    run.check(facts.get("package_root") == str(REPO), f"the verdict file names the package that ran: {facts.get('package_root')}")


def check_records(run: Run) -> None:
    frames = [record.get("frame") for record in run.records]
    steps = {b - a for a, b in zip(frames, frames[1:])}
    run.check(len(run.records) == LOOKS, f"action log: {len(run.records)} records (want {LOOKS}, one per {WATCH_EVERY} frames)")
    run.check(steps == {WATCH_EVERY}, f"action log frames {frames[:3]}...{frames[-1:]} step {sorted(steps)} (want {WATCH_EVERY})")
    shapes = {(r.get("decision"), r.get("action"), bool(r.get("observation")), bool(r.get("digest"))) for r in run.records}
    run.check(shapes == {("observe", "none", True, True)}, f"every record: decision/action/observation/digest = {sorted(shapes)}")
    problems = sorted({p for r in run.records for p in (r.get("observation") or {}).get("problems", [])})
    run.check(not problems, f"no part of any look was unreadable: problems={problems or 'none'}")


def check_frame(run: Run) -> None:
    """Every truth below is read on THIS frame; a mismatch here voids the arm's comparisons."""
    probe_frame, look_frame = (run.probe or {}).get("frame"), run.first.get("frame")
    run.check(probe_frame is not None and probe_frame == look_frame,
              f"the probe and the first look read the same frame: probe f{probe_frame}, look f{look_frame}")


def check_place(run: Run, doc_map: str | None = None, doc_xy: tuple[int, int] | None = None) -> None:
    truth, player = run.truth, run.first.get("player") or {}
    tmap = truth.get("map") or {}
    eyes_map = (player.get("map_group"), player.get("map_number"))
    true_map = (tmap.get("group"), tmap.get("number"))
    run.check(eyes_map == true_map and len(tmap.get("header_matches", [])) == 1,
              f"MAP (group, number) eyes {eyes_map} (save block 1 location) == truth {true_map} (the live gMapHeader is "
              f"byte-identical to exactly one header of the ROM table gMapGroups, walked by the probe: {tmap.get('header_matches')})")
    run.check(player.get("map_name") == tmap.get("name") and tmap.get("name") not in (None, "?"),
              f"MAP NAME eyes {player.get('map_name')!r} (the framework's MapLocation.map_name) == truth {tmap.get('name')!r} "
              f"(region-map section {tmap.get('mapsec')} of the ROM header -> gRegionMapEntries -> decoded by the probe's own charmap)")
    eyes_xy, true_xy = [player.get("x"), player.get("y")], truth.get("position")
    run.check(eyes_xy == true_xy, f"POSITION eyes {eyes_xy} (object currentCoords - 7) == truth {true_xy} (save block 1 pos)")
    sprite = truth.get("facing_sprite") or {}
    if truth.get("facing") is not None:
        run.check(player.get("facing") == truth["facing"] and sprite.get("oam_hflip") == (truth["facing"] == "right"),
                  f"FACING eyes {player.get('facing')!r} (the object's facingDirection) == truth {truth['facing']!r}: what is DRAWN, "
                  f"the player sprite's {sprite.get('anim_table')} animNum {sprite.get('anim_num')} (ANIM_STD order down, up, left, "
                  f"right in fours) with OAM hFlip={sprite.get('oam_hflip')} (only the east frame is flipped)")
    else:
        run.check(player.get("facing") == truth.get("facing_object_byte_NOT_TRUTH"),
                  f"FACING CONSISTENCY ONLY, NOT GROUND TRUTH (the player's sprite slot now runs {sprite.get('anim_table')!r}: this "
                  f"screen freed the overworld sprites, so the game holds no second copy): eyes {player.get('facing')!r} == the "
                  f"same byte decoded by the probe {truth.get('facing_object_byte_NOT_TRUTH')!r}")
    if doc_map is not None:
        run.check(player.get("map_name") == doc_map, f"documentation: map {doc_map!r}; eyes {player.get('map_name')!r}")
    if doc_xy is not None:
        run.check(tuple(eyes_xy) == doc_xy, f"documentation: xy {doc_xy}; eyes {tuple(eyes_xy)}")
    screen = run.first.get("screen") or {}
    tscreen = truth.get("screen") or {}
    run.check(screen.get("in_battle") == tscreen.get("in_battle_bit"),
              f"IN BATTLE eyes {screen.get('in_battle')} (theirs: is gMain.callback1 BattleMainCB1) == truth gMain.inBattle bit "
              f"{tscreen.get('in_battle_bit')} (bit 1 of gMain+0x439, which the eyes do not read)")


def check_party(run: Run) -> None:
    eyes = [(m["species"], m["level"], m["hp"], m["max_hp"], m["pid"]) for m in run.first.get("party", [])]
    truth = [(m["species"], m["level"], m["hp"], m["max_hp"], m["pid"]) for m in run.truth.get("party", [])]
    run.check(bool(truth) and eyes == truth,
              f"PARTY (species, level, hp, max, PID) eyes {[(s, l, h, m, f'{p:08X}') for s, l, h, m, p in eyes]} == truth "
              f"(framework get_party) {[(s, l, h, m, f'{p:08X}') for s, l, h, m, p in truth]}")
    raw = [m["raw_level"] for m in run.truth.get("party", [])]
    run.check(raw == [m["level"] for m in run.first.get("party", [])], f"party levels == the raw level bytes {raw}")
    # Round 2 (the verifier: "moves, PP and status have no live truth comparison"): by PID, every move with
    # its PP and max PP, and the status, against the framework's own decryption and PP-bonus maths.
    eyes_moves = [(f"{m['pid']:08X}", m["status"], [(x["name"], x["pp"], x["max_pp"]) for x in m["moves"]])
                  for m in run.first.get("party", [])]
    true_moves = [(f"{m['pid']:08X}", STATUS_NAMES.get(m.get("status"), m.get("status")), [tuple(x) for x in m.get("moves", [])])
                  for m in run.truth.get("party", [])]
    used = sum(1 for _, _, moves in true_moves for _, pp, top in moves if pp < top)
    statuses = sorted({status for _, status, _ in true_moves})
    run.check(bool(true_moves) and eyes_moves == true_moves,
              f"PARTY MOVES, PP / MAX PP AND STATUS by PID: eyes (their own decryption, max PP from the move table and the "
              f"PP-up bits) == truth (framework get_party: its decryption, LearnedMove.pp / total_pp, StatusCondition); "
              f"{sum(len(m) for _, _, m in true_moves)} moves, {used} with PP used, statuses {statuses}: "
              + "; ".join(f"{pid} {status} " + ", ".join(f"{n} {p}/{t}" for n, p, t in moves) for pid, status, moves in true_moves)
              + ("" if eyes_moves == true_moves else f" || eyes {eyes_moves}"))


def item_key(name: str) -> str:
    """An item name compared across the framework's table ('Poké Ball', "King's Rock") and the ROM's
    ('POKé BALL', 'KING’S ROCK'): letters and digits only, accents dropped, case folded."""
    plain = unicodedata.normalize("NFKD", name)
    return "".join(c for c in plain.casefold() if c.isalnum())


def check_progress(run: Run, observation: dict | None = None, label: str = "eyes") -> dict:
    """Money, badges, story flags, the Pokedex and the bag against the probe's own decode of the save
    blocks (module docstring). Returns the counts, for the arms' non-vacuity checks."""
    look = run.first if observation is None else observation
    own = run.truth.get("progress") or {}
    eyes = look.get("progress") or {}
    bag = look.get("bag") or {}
    run.check(eyes.get("money") == own.get("money"),
              f"MONEY {label} {eyes.get('money')} (framework get_player) == truth {own.get('money')} (save block 1 money XOR save block 2 key)")
    flags = own.get("flags") or {}
    true_badges = [name for name in BADGE_FLAGS if flags.get(name)]
    run.check(list(eyes.get("badges", [])) == true_badges,
              f"BADGES {label} {eyes.get('badges')} (framework get_event_flag) == truth {true_badges} (the probe's own bits at the decomp's "
              f"flag ids 0x867..0x86E)")
    eyes_flags = [tuple(pair) for pair in eyes.get("flags", [])]
    true_flags = [(name, flags.get(name)) for name, _ in STORY_FLAGS]
    run.check(eyes_flags == true_flags,
              f"STORY FLAGS {label} == truth (bits at the decomp's ids): {['%s=%s' % (n, 'T' if v else 'F') for n, v in true_flags]}"
              + ("" if eyes_flags == true_flags else f"; {label} {eyes_flags}"))
    run.check((eyes.get("dex_owned"), eyes.get("dex_seen")) == (own.get("dex_owned"), own.get("dex_seen"))
              and list(eyes.get("owned_dex", [])) == list(own.get("owned_dex", [])),
              f"POKEDEX {label} owned {eyes.get('dex_owned')} seen {eyes.get('dex_seen')} (framework get_pokedex) == truth owned "
              f"{own.get('dex_owned')} seen {own.get('dex_seen')} (the game's rule over the THREE seen copies, save block 2 seen + save "
              f"block 1 seen1/seen2, and save block 2 owned); owned numbers {own.get('owned_dex')}")
    pockets = own.get("bag") or {}
    true_balls = sorted((item_key(e["name"]), e["quantity"]) for e in pockets.get("poke_balls", []) if e["quantity"] > 0)
    eyes_balls = sorted((item_key(name), quantity) for name, quantity in bag.get("balls", []))
    run.check(eyes_balls == true_balls and bag.get("ball_total") == sum(q for _, q in true_balls),
              f"BALLS {label} {bag.get('balls')} total {bag.get('ball_total')} (framework get_item_bag) == truth "
              f"{[(e['name'], e['quantity']) for e in pockets.get('poke_balls', [])]} (the poke-ball pocket of save block 1, quantities "
              f"XOR the key, names from the ROM's gItems by the probe's charmap)")
    carried = [e for p in ("items", "berries") for e in pockets.get(p, []) if e["quantity"] > 0]
    healing = [e for e in carried if e["field_use"] in ROM_HEALING_USES or e["battle_use"] in ROM_HEALING_USES]
    others = [e for e in carried if e not in healing]
    true_healing = sorted((item_key(e["name"]), e["quantity"]) for e in healing)
    eyes_healing = sorted((item_key(name), quantity) for name, quantity in bag.get("healing", []))
    run.check(eyes_healing == true_healing,
              f"HEALING ITEMS {label} {bag.get('healing')} (the framework's item table says 'healing') == truth "
              f"{[(e['name'], e['quantity']) for e in healing]} (items/berries pockets whose ROM gItems use function is "
              f"{' or '.join(ROM_HEALING_USES)}); left out as not healing: "
              f"{[(e['name'], e['field_use'], e['battle_use']) for e in others] or 'none in the bag'}")
    return {"healing": len(healing), "others": len(others), "flags_true": sum(1 for _, v in true_flags if v),
            "flags_false": sum(1 for _, v in true_flags if not v)}


def check_objects(run: Run) -> None:
    """Every object the probe's RAW parse puts on screen is seen, and nothing else (strict: `check_frame`
    proves the probe and the first look read the same frame, and NPCs walk)."""
    eyes = sorted((o["local_id"], o["dx"], o["dy"]) for o in (run.first.get("view") or {}).get("objects", []) if o["source"] == "object")
    truth = sorted((o["local_id"], o["dx"], o["dy"]) for o in run.truth.get("objects", []) if o["on_screen"] and not o["invisible"])
    off = sorted((o["local_id"], o["dx"], o["dy"]) for o in run.truth.get("objects", []) if not o["on_screen"])
    run.check(eyes == truth, f"OBJECTS on screen (local id, dx, dy): eyes {eyes} == truth (raw gObjectEvents, own window test) {truth}; "
              f"off screen and left out: {off or 'none'}")
    check_drawn_objects(run)


def check_drawn_objects(run: Run) -> None:
    """Round 2 (the verifier: object positions were the same bytes, a second decoder): WHAT IS DRAWN. Each
    object's sprite, placed on screen relative to the player's drawn tile, in tiles (`probe_eyes.truth`).
    Only on the overworld with the camera centred (the player's tile drawn at (112, 72)): a battle reuses
    the sprites. A STILL object (previousCoords == currentCoords) must be drawn exactly on its coordinates
    and a moving one within one tile; and the objects the eyes see must be exactly the still ones whose
    DRAWN tile is inside the window (moving ones are listed, not graded: mid-step they sit between tiles)."""
    player = run.truth.get("player_drawn_tile")
    if player != PLAYER_TILE_ON_SCREEN:
        run.notes.append(f"drawn objects not graded: the player's tile is drawn at {player} (not a centred overworld camera)")
        return
    visible = [o for o in run.truth.get("objects", []) if not o["invisible"]]
    placed, misplaced, moving = 0, [], []
    for o in visible:
        drawn = o.get("drawn")
        still = o["previous_dx_dy"] == [o["dx"], o["dy"]]
        if drawn is None:
            misplaced.append((o["local_id"], "no sprite in use"))
            continue
        if not still:
            moving.append(o["local_id"])
        good = ((drawn["dx"], drawn["dy"]) == (o["dx"], o["dy"]) if still
                else abs(drawn["dx"] - o["dx"]) < 1 and abs(drawn["dy"] - o["dy"]) < 1)
        placed += good
        if not good:
            misplaced.append((o["local_id"], (o["dx"], o["dy"]), (drawn["dx"], drawn["dy"])))
    run.check(bool(visible) and not misplaced,
              f"OBJECTS DRAWN: {placed} of {len(visible)} visible objects are DRAWN on their coordinates (sprite on screen relative to "
              f"the player's tile at {player}; {len(moving)} mid-step within one tile: {moving or 'none'}); misplaced: {misplaced or 'none'}")
    seen = sorted(o["local_id"] for o in (run.first.get("view") or {}).get("objects", []) if o["source"] == "object")
    drawn_in = sorted(o["local_id"] for o in visible if o.get("drawn") and o["local_id"] not in moving
                      and -VIEW_HALF_WIDTH <= o["drawn"]["dx"] <= VIEW_HALF_WIDTH and -VIEW_UP <= o["drawn"]["dy"] <= VIEW_DOWN)
    drawn_off = sorted((o["local_id"], o["drawn"]["screen_tile_xy"]) for o in visible if o.get("drawn") and o["local_id"] not in moving
                       and o["local_id"] not in drawn_in)
    seen_still = sorted(i for i in seen if i not in moving)
    run.check(seen_still == drawn_in,
              f"CROP BY WHAT IS DRAWN: the still objects the eyes see {seen_still} == those DRAWN inside the window {drawn_in}; drawn "
              f"outside it (local id, screen tile x, y): {drawn_off or 'none'}")


def check_header_guard(run: Run) -> None:
    """The map-header check can FAIL (round 2): `probe_eyes.header_guard`, in the probe's own emulator."""
    guard = (run.probe or {}).get("header_guard") or {}
    stale = guard.get("stale_header_problems") or []
    run.check(guard.get("clean_header_problems") == [] and guard.get("clean_player") is True
              and any("is not map" in p for p in stale) and guard.get("stale_player") is False,
              f"MAP HEADER CHECK: unchanged state -> header problems {guard.get('clean_header_problems')}, player seen "
              f"{guard.get('clean_player')}; with map {guard.get('stale_header_of_map')}'s ROM header written over gMapHeader (the "
              f"probe's emulator) -> refused: {stale[:1] or 'NOT REFUSED'}, player seen {guard.get('stale_player')}")


def check_text_flags(run: Run) -> None:
    """The bit order of `gTextFlags` the eyes assume (autoScroll = bit 2), measured in a battle: every battle
    message sets useAlternateDownArrow (bit 1 if the bit-fields run from bit 0, bit 6 if from bit 7)."""
    flags = (run.truth.get("screen") or {}).get("text_flags")
    run.check(flags is not None and flags & 0x02 and not flags & 0xF0,
              f"gTextFlags in a battle = {flags if flags is None else hex(flags)}: bit 1 (useAlternateDownArrow, set by "
              f"BattlePutTextOnWindow) set and no bit above 3, so the bit-fields run from bit 0 and autoScroll is bit 2 "
              f"(TEXT_FLAG_AUTO_SCROLL = 0x04), here {'SET' if flags and flags & 0x04 else 'clear'}")


#: The eyes' compact ledge glyphs (`Tile.flags`): the action log keeps the four straight directions and
#: '/' for any diagonal.
LEDGE_GLYPH = {"east": ">", "west": "<", "north": "^", "south": "v"}


def tile_pair(tile: list, truth: dict) -> tuple[tuple, tuple]:
    """(eyes, truth) for one tile, field by field: metatile, behaviour, collision, elevation (the PROBE's
    decode of the ROM layout and tileset attributes), collision and elevation again (the FRAMEWORK's
    MapLocation, a third decoder), encounters, water, tall grass (MapLocation), the ledge and the door
    (by the FRAMEWORK's behaviour names), and the warp (the probe's parse of the ROM header's warps; for a
    tile of the NEXT map the eyes mark only the current map's warps, so the warp is compared on this map)."""
    flags = tile[6]
    own = truth.get("own") or {}
    true_ledge = (LEDGE_GLYPH.get(truth["ledge"], "/") if truth.get("ledge") else "")
    eyes_ledge = next((c for c in flags if c in "<>^v/"), "")
    this_map = truth.get("source", "map") == "map"
    mine = (tile[2], tile[3], tile[4], tile[5], tile[4], tile[5], "l" in flags or "s" in flags, "w" in flags, "g" in flags,
            eyes_ledge, "d" in flags, ("p" in flags) if this_map else None)
    theirs = (own.get("metatile"), own.get("behavior"), own.get("collision"), own.get("elevation"), truth["collision"],
              truth["elevation"], truth["encounters"], truth["surfable"], truth["tall_grass"], true_ledge, truth["door"],
              truth["warp"] if this_map else None)
    return mine, theirs


TILE_FIELDS = ("metatile", "behaviour", "collision", "elevation", "collision(fw)", "elevation(fw)", "encounters", "water",
               "tall grass", "ledge", "door", "warp")


def check_tiles(run: Run, want_connection: bool = False, want: dict | None = None) -> dict:
    """Every tile of the window the probe can vouch for: the eyes (the LIVE grid, their own tables)
    against the probe's own decode of the ROM layout and the framework's MapLocation (`tile_pair`):
    tiles inside the map, and tiles past an edge with a connection, against the NEIGHBOUR map's own tile."""
    view = run.first.get("view") or {}
    eyes = {(t[0], t[1]): t for t in view.get("tiles", [])}
    mismatches, compared, across = [], 0, 0
    counts = {"ledge": 0, "door": 0, "warp": 0, "warp_across_edge": 0}
    for truth in run.truth.get("tiles", []):
        tile = eyes.get((truth["x"], truth["y"]))
        if tile is None:
            mismatches.append(f"({truth['x']},{truth['y']}) missing")
            continue
        compared += 1
        across += truth.get("source", "map") != "map"
        counts["ledge"] += bool(truth.get("ledge"))
        counts["door"] += bool(truth.get("door"))
        counts["warp"] += bool(truth.get("warp")) and truth.get("source", "map") == "map"
        counts["warp_across_edge"] += bool(truth.get("warp")) and truth.get("source", "map") != "map"
        mine, theirs = tile_pair(tile, truth)
        if mine != theirs:
            fields = [TILE_FIELDS[i] for i, (a, b) in enumerate(zip(mine, theirs)) if a != b]
            mismatches.append(f"({truth['x']},{truth['y']}) {fields}: eyes {mine} truth {theirs} {truth['tile_type']} [{truth.get('source')}]")
    # CONTROL: the same comparison against the eyes' tiles SHIFTED one column must find mismatches, or a
    # window of uniform tiles would make "no mismatches" true by construction.
    shifted = 0
    for truth in run.truth.get("tiles", []):
        tile = eyes.get((truth["x"] + 1, truth["y"]))
        if tile is not None:
            mine, theirs = tile_pair(tile, truth)
            shifted += mine != theirs
    run.check(shifted > 0, f"CONTROL: the same tile comparison, with the eyes' window shifted ONE column, finds {shifted} mismatches")
    grass = sum(1 for t in view.get("tiles", []) if "g" in t[6])
    run.check(compared > 0 and not mismatches,
              f"TILES: {compared} tiles compared ({compared - across} inside the map, {across} of the NEXT map across an edge) on "
              f"{', '.join(TILE_FIELDS)}: eyes (live grid gBackupMapLayout, their own tables) == truth (the probe's decode of the ROM "
              f"layout, tilesets and warps; the framework's MapLocation and behaviour names); ledge tiles {counts['ledge']}, doors "
              f"{counts['door']}, warps {counts['warp']}, tall grass {grass}; mismatches: {mismatches[:6] or 'none'}")
    if counts["warp_across_edge"]:
        run.notes.append(f"{counts['warp_across_edge']} warp tile(s) of the NEXT map are in the window: the eyes mark only the current "
                         f"map's warps (README: known limits)")
    for kind, minimum in (want or {}).items():
        run.check(counts[kind] >= minimum, f"NON-VACUITY: {counts[kind]} {kind} tile(s) of the window compared (pre-registered >= {minimum})")
    if want_connection:
        sources = sorted({t["source"].split(" tile ")[0] for t in run.truth.get("tiles", []) if t.get("source", "map") != "map"})
        run.check(across > 0, f"NON-VACUITY: {across} tiles of the window lie past a map edge with a connection: {sources}")
    run.notes.append("first look, the window as the eyes saw it:\n    " + "\n    ".join(view.get("ascii", [])))
    return counts


def waits_grade(behaviour: dict) -> dict:
    """The behaviour test graded (shared by `check_waits` and arm XW): the first look's truth, recomputed
    HERE from the behaviour's three observations, and the frames on which the eyes were wrong, per kind.
    Each frame entry is [frame, the eyes' waits, their reason, the printers (index, currentChar, state)]."""
    parts = (behaviour.get("text_on_screen"), behaviour.get("idle_still"), behaviour.get("press_moved_the_text"))
    truth = all(parts) if None not in parts else None
    kinds = {"idle printing": ("idle_printing_frames", False), "idle waiting": ("idle_waiting_frames", True),
             "printing": ("printing_frames", False), "frozen": ("frozen_text_frames", True)}
    out: dict = {"truth": truth, "first_waits": (behaviour.get("first_look") or {}).get("waits"),
                 "first_reason": (behaviour.get("first_look") or {}).get("reason")}
    for kind, (key, want) in kinds.items():
        frames = behaviour.get(key) or []
        out[kind] = {"frames": len(frames), "wrong": [f[0] for f in frames if bool(f[1]) is not want],
                     "reasons": sorted({str(f[2]) for f in frames}),
                     "printer_states": sorted({(p[0], p[2]) for f in frames for p in f[3]})}
    out["first_ok"] = truth is not None and truth == behaviour.get("waits_truth") and out["first_waits"] is truth
    return out


def check_waits(run: Run, want_printing: bool = False, want_frozen: bool = False, want_idle_printing: bool = False,
                want_idle_waiting: bool = False) -> None:
    """WAITS FOR A BUTTON against the game's BEHAVIOUR (`probe_eyes.behaviour`: a fresh load in the
    probe's emulator, 300 frames with no input, one A press, 300 frames with no input, the eyes looking at
    every frame). Each `want_*` is a pre-registered NON-VACUITY: at least one such frame."""
    behaviour = (run.probe or {}).get("behaviour") or {}
    screen = run.first.get("screen") or {}
    first = behaviour.get("first_look") or {}
    run.check(first.get("frame") == run.first.get("frame") and first.get("waits") == screen.get("waits_for_button"),
              f"the behaviour test starts on the first look's frame f{first.get('frame')} (look f{run.first.get('frame')}), where the "
              f"probe's own look agrees with the watcher's: waits={first.get('waits')} / {screen.get('waits_for_button')}")
    grade = waits_grade(behaviour)
    truth = grade["truth"]
    run.check(truth is not None and truth == behaviour.get("waits_truth") and screen.get("waits_for_button") is truth,
              f"WAITS FOR A BUTTON eyes {screen.get('waits_for_button')} (reason {screen.get('wait_reason')!r}) == truth BY BEHAVIOUR "
              f"{truth}: text on screen={behaviour.get('text_on_screen')}, {behaviour.get('idle_frames')} frames with no input changed "
              f"nothing={behaviour.get('idle_still')} (the text moved by itself at frame {behaviour.get('text_moved_by_itself_at')}), "
              f"one A press moved that text={behaviour.get('press_moved_the_text')} (moved anything={behaviour.get('press_moved')})")
    rows = (
        ("idle printing", "BEFORE the press: on all {n} frames where a text was PRINTING by itself (its currentChar changed on the "
                          "next frame, no input) the eyes said waits=False", want_idle_printing),
        ("idle waiting", "BEFORE the press: on all {n} WAITING frames (the screen sat still from there until the press, >= 30 "
                         "frames, a printer active, no menu task, and the press then moved that text) the eyes said waits=True",
         want_idle_waiting),
        ("printing", "after the press: on all {n} frames where a text was PRINTING by itself the eyes said waits=False", want_printing),
        ("frozen", "after the press: on all {n} frames from which a text then sat still for 30 frames (no menu task) the eyes "
                   "said waits=True", want_frozen),
    )
    for kind, text, want in rows:
        part = grade[kind]
        run.check(not part["wrong"] and (part["frames"] > 0 or not want),
                  text.format(n=part["frames"]) + f" (wrong: {part['wrong'][:8] or 'none'}; the eyes' reasons {part['reasons']}; "
                  f"printers (index, state) {part['printer_states']})" + (" (NON-VACUITY: pre-registered > 0)" if want else ""))


def first_view_objects(run: Run) -> list[tuple]:
    return [(o["kind"], o["local_id"], o["graphics_id"], o["dx"], o["dy"]) for o in (run.first.get("view") or {}).get("objects", [])]


def objects_in_every_look(run: Run, local_id: int) -> list[bool]:
    return [any(o["local_id"] == local_id and o["source"] == "object" for o in ((r.get("observation") or {}).get("view") or {}).get("objects", []))
            for r in run.records]


def scorer_record(run: Run) -> dict:
    import scoring

    path = run.run_dir / "ai_player.log"
    return scoring.parse_log(path)


def bot_dex_line() -> str:
    """The bot's own `[DEX]` condition, quoted with its line number (or MISSING)."""
    try:
        for number, line in enumerate(BOT_LOGGER.read_text(encoding="utf-8").splitlines(), 1):
            if BOT_DEX_CONDITION in line:
                return f"{BOT_LOGGER.relative_to(REPO).as_posix()}:{number}: {line.strip()}"
    except OSError:
        pass
    return "MISSING"


def check_scorer(run: Run, starter: str) -> None:
    import scoring

    record = scorer_record(run)
    last_frame = run.records[-1]["frame"] if run.records else None
    run.check(record["starter"] == starter, f"scoring.parse_log(ai_player.log): starter={record['starter']!r} (want {starter!r})")
    run.check(record["maps_visited"] == 1, f"scoring.parse_log: maps_visited={record['maps_visited']} (want 1)")
    run.check(record["frames"] == last_frame, f"scoring.parse_log: frames={record['frames']} == the last look's frame {last_frame}")
    run.check((record["catches"], record["badges"], record["wins"]) == (0, [], {}),
              f"scoring.parse_log: catches={record['catches']} badges={record['badges']} wins={record['wins']} (want none)")
    last = (run.records[-1].get("observation") or {}) if run.records else {}
    player = last.get("player") or {}
    party = str([f"{m['species']}:L{m['level']}" for m in last.get("party", [])])
    want_end = (player.get("map_name"), [player.get("x"), player.get("y")], party)
    got_end = (record["end_map"], record["end_pos"], record["end_party"])
    run.check(got_end == want_end, f"scoring.parse_log: the run's END (map, pos, party) {got_end} == the last look's {want_end}")
    lines = [line for line in run.ai_log.splitlines() if any(tag in line for tag in ("[AI-STARTER]", "[MAP]", "[hb]"))]
    regexes = {"[AI-STARTER]": scoring.STARTER_RE, "[MAP]": scoring.MAP_RE, "[hb]": scoring.HB_RE}
    bad = [line for line in lines for tag, rx in regexes.items() if tag in line and not (rx.search(line) and scoring.FRAME_RE.match(line))]
    run.check(len(lines) == 3 and not bad, f"the AI's scorer lines match the scorer's regexes: {lines} (non-matching: {bad or 'none'})")
    # PARITY, the verifier's note: a run started from a save scores only what HAPPENS in the run, like a
    # bot run, because the AI writes the bot's own line formats on the bot's own triggers.
    owned = [((r.get("observation") or {}).get("progress") or {}).get("dex_owned") for r in run.records]
    badges = ((run.first.get("progress") or {}).get("badges")) or []
    dex_lines = [line for line in run.ai_log.splitlines() if "[DEX] owned" in line]
    quote = bot_dex_line()
    run.check(record["dex_owned"] == 0 and not dex_lines and len(set(owned)) == 1 and quote != "MISSING",
              f"PARITY WITH THE BOT, NOT THE GAME'S TOTAL: scoring.parse_log dex_owned={record['dex_owned']} while the game owns "
              f"{owned[0] if owned else '?'} (every look: {sorted(set(owned))}): no `[DEX]` line was written ({len(dex_lines)}) because the "
              f"count never changed, and the bot writes it on the same trigger only, `{quote}`")
    run.check(record["badges"] == [] and record["money_last"] is None,
              f"PARITY: scoring.parse_log badges={record['badges']} while the game holds {badges or 'none'} (the scorer counts a badge "
              f"only from a leader WIN in the run, `[TRAINER] end opp=265..272 ... res=Won`), money_last={record['money_last']} (set "
              f"only by a `[TRAINER] end` line); human_score={record['human_score']} is therefore this run's, not the save's")
    run.notes.append("scoring.parse_log(ai_player.log) -> " + json.dumps({k: record[k] for k in (
        "starter", "maps_visited", "frames", "catches", "dex_owned", "badges", "money_last", "end_map", "end_pos", "end_party",
        "progress", "score", "human_score")}))


def own_starter(run: Run) -> str:
    """What the scorer SHOULD be told: the first party Pokemon of a starter family whose OT is the player,
    from the PROBE's party (framework get_party) and trainer id (raw save block 2)."""
    families = {252: "Treecko", 253: "Treecko", 254: "Treecko", 255: "Torchic", 256: "Torchic", 257: "Torchic",
                258: "Mudkip", 259: "Mudkip", 260: "Mudkip"}
    for mon in run.truth.get("party", []):
        if mon["dex"] in families and mon["ot_id"] == run.truth.get("trainer_id"):
            return families[mon["dex"]]
    return "Unknown"


def check_battle(run: Run, kind: str) -> None:
    battle = run.first.get("battle") or {}
    truth = run.truth.get("battle") or {}
    screen = run.first.get("screen") or {}
    run.check(screen.get("screen") == "battle" and screen.get("in_battle"), f"screen={screen.get('screen')} in_battle={screen.get('in_battle')}")
    run.check(battle.get("kind") == kind and truth.get("trainer") == (kind == "trainer"),
              f"battle kind eyes {battle.get('kind')!r}; truth gBattleTypeFlags={truth.get('type_flags')} trainer bit={truth.get('trainer')}")
    for side, key in (("own", "own"), ("foe", "foe")):
        battlers = [b for b in truth.get("battlers", []) if b["side"] == side]
        eyes = [(m["species"], m["level"], m["hp"], m["max_hp"], m["types"]) for m in battle.get(key, [])]
        raw = [(b["species"], b["level"], b["hp"], b["max_hp"], b["types"]) for b in battlers]
        run.check(bool(raw) and eyes == raw,
                  f"{side.upper()} SIDE CONSISTENCY ONLY, NOT GROUND TRUTH (the SAME gBattleMons bytes the eyes read, decoded by the "
                  f"probe): eyes {eyes} == {raw}")
        # THE TRUTH (round 2): the second copy, the party struct with the same PID.
        mine = [(m["species"], m["level"], m["hp"], m["max_hp"], m["status"], sorted(m["types"]),
                 [(x["name"], x["pp"], x["max_pp"]) for x in m["moves"]]) for m in battle.get(key, [])]
        copies = [b.get("second_copy") for b in battlers]
        theirs = [(c["species"], c["level"], c["hp"], c["max_hp"], STATUS_NAMES.get(c["status"], c["status"]), sorted(c["types"]),
                   [tuple(x) for x in c["moves"]]) for c in copies if c]
        where = [f"{c['party']}[{c['slot']}] PID {b['pid']:08X}" if c else f"NO single copy of PID {b['pid']:08X} ({b['copies_with_this_pid']})"
                 for b, c in zip(battlers, copies)]
        run.check(bool(theirs) and len(theirs) == len(battlers) and mine == theirs,
                  f"{side.upper()} SIDE (species, level, hp, max, status, types, moves with PP / max PP) eyes {mine} == truth: the SECOND "
                  f"COPY the game keeps, the party struct with the battler's PID ({'; '.join(where)}; the framework's decryption), "
                  f"types from the species table {theirs if mine != theirs else '(equal)'}")
        for b, c in zip(battlers, copies):
            if c:
                run.notes.append(f"identity vs index: battler {b['battler']} ({side}) PID {b['pid']:08X} is {c['party']} slot {c['slot']}; "
                                 f"gBattlerPartyIndexes[{b['battler']}] = {b['party_index']}")
    foe = [(m["species"], m["level"]) for m in battle.get("foe", [])]
    enemy = [tuple(m) for m in truth.get("enemy_party", [])]
    run.check(bool(foe) and foe[0] in enemy, f"the foe battler {foe} is in the live gEnemyParty {enemy} (framework Pokemon decode)")
    run.check(run.first.get("view") is None, "no overworld view in a battle (a person sees the battle screen)")
    ends = [line for line in run.ai_log.splitlines() if "[TRAINER] end" in line or "[CATCH] end" in line or "[AI-BATTLE] end" in line]
    run.check(not ends, f"no battle-end line (the battle is still waiting; nobody pressed): {ends or 'none'}")


# ---------------------------------------------------------------------- graders
def grade_overworld_basics(run: Run) -> None:
    screen = run.first.get("screen") or {}
    tscreen = run.truth.get("screen") or {}
    run.check(screen.get("screen") == "overworld" and not screen.get("text_box_open") and tscreen.get("callback2") == "CB2_Overworld"
              and "Task_DrawFieldMessage" not in tscreen.get("tasks", []),
              f"screen eyes {screen.get('screen')!r} text_box_open={screen.get('text_box_open')}; truth callback2={tscreen.get('callback2')} "
              f"(the probe's symbol lookup), Task_DrawFieldMessage running={'Task_DrawFieldMessage' in tscreen.get('tasks', [])} "
              f"(the probe's own gTasks parse)")


def grade_E1(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="DEWFORD TOWN", doc_xy=(11, 9))
    check_party(run)
    check_progress(run)
    check_objects(run)
    check_tiles(run, want={"door": 2, "warp": 2})
    grade_overworld_basics(run)
    check_waits(run, want_printing=True, want_frozen=True)
    check_header_guard(run)
    check_scorer(run, own_starter(run))


def grade_E2(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="ROUTE 116", doc_xy=(11, 7))
    check_party(run)
    doc = [("Mudkip", 13, 37, 40, 0x550A9BE6), ("Poochyena", 4, 16, 17, 0x5815089E), ("Nincada", 6, 20, 20, 0x4457D0FB),
           ("Whismur", 6, 23, 23, 0x7E9BB3BA)]
    eyes = [(m["species"], m["level"], m["hp"], m["max_hp"], m["pid"]) for m in run.first.get("party", [])]
    run.check(eyes == doc, f"documentation (FIXTURES.md5) party by PID {[(s, l, f'{h}/{m}', f'{p:08X}') for s, l, h, m, p in doc]}; eyes "
              f"{[(s, l, f'{h}/{m}', f'{p:08X}') for s, l, h, m, p in eyes]}")
    progress = run.first.get("progress") or {}
    run.check((progress.get("money"), progress.get("badges")) == (824, []), f"documentation: ₽824, no badges; eyes money={progress.get('money')} badges={progress.get('badges')}")
    check_progress(run)
    check_objects(run)
    check_tiles(run, want={"ledge": 8})
    grade_overworld_basics(run)
    check_header_guard(run)
    ball = next((o for o in run.truth.get("objects", []) if o["local_id"] == 7), None)
    run.check(ball is not None and ball["graphics_id"] == 59 and (ball["dx"], ball["dy"]) == (8, -1) and not ball["on_screen"],
              f"NON-VACUITY: the probe's raw gObjectEvents holds the item ball ACTIVE, off screen: {ball}")
    drawn = (ball or {}).get("drawn") or {}
    run.check(drawn.get("screen_tile_xy") == [240, 56] and drawn.get("on_screen_240x160") is False,
              f"WHAT IS DRAWN: the item ball's sprite is placed at screen {drawn.get('screen_tile_xy')} (want [240, 56]: its left edge is "
              f"the screen's right edge, 240 px), on the 240 x 160 screen={drawn.get('on_screen_240x160')}")
    absent = objects_in_every_look(run, 7)
    present = objects_in_every_look(run, 3)
    run.check(len(absent) == LOOKS and not any(absent), f"CROP: the off-screen item ball (local 7) in the {len(absent)} looks: {absent} (want all False)")
    run.check(len(present) == LOOKS and all(present), f"CROP: the on-screen trainer (local 3, dx=+1) in the {len(present)} looks: {present} (want all True)")
    run.check((run.first.get("view") or {}).get("cropped") is True, f"the view says cropped={(run.first.get('view') or {}).get('cropped')}")


def grade_E2X(run: Run) -> None:
    check_purity(run)
    check_records(run)
    seen = first_view_objects(run)
    ball = [o for o in seen if o[1] == 7]
    run.check(ball == [("item_ball", 7, 59, 8, -1)], f"FAULT: with the crop off the item ball IS reported: {ball or 'absent'}")
    every = objects_in_every_look(run, 7)
    run.check(len(every) == LOOKS and all(every), f"FAULT: the item ball in all {len(every)} looks: {every}")
    far = sorted({abs(o[3]) for o in seen if o[0] == "sign" and abs(o[3]) > VIEW_HALF_WIDTH})
    run.check(bool(far), f"FAULT: signs far off screen reported too (|dx| = {far})")
    run.check((run.first.get("view") or {}).get("cropped") is False, f"the view says cropped={(run.first.get('view') or {}).get('cropped')}")


def grade_E3(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="ROUTE 121")
    check_party(run)
    counts = check_progress(run)
    run.check((counts["healing"], counts["others"]) == (1, 1),
              f"NON-VACUITY of the healing check: {counts['healing']} healing item(s) and {counts['others']} other(s) in the bag (want 1 and 1)")
    check_objects(run)
    check_tiles(run)
    grade_overworld_basics(run)
    check_header_guard(run)
    seen = first_view_objects(run)
    ball = [o for o in seen if o[1] == 29]
    run.check(ball == [("item_ball", 29, 59, -6, -1)], f"the ON-screen item ball (local 29) is seen as an item ball: {ball or 'absent'}")
    run.check(len(run.first.get("party", [])) == 6, f"documentation: party 6; eyes {len(run.first.get('party', []))}")


def grade_E4(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="ROUTE 101")
    check_party(run)
    check_progress(run)
    check_battle(run, "wild")
    check_text_flags(run)
    check_waits(run, want_printing=True, want_idle_waiting=True)
    check_header_guard(run)


def grade_E5(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="ROUTE 116")
    check_party(run)
    check_progress(run)
    check_battle(run, "trainer")
    check_text_flags(run)
    check_waits(run, want_printing=True, want_idle_waiting=True)
    check_header_guard(run)
    check_opponent(run)


def check_opponent(run: Run) -> None:
    """The opponent trainer id against the trainer who STARTED the battle (E5, E10)."""
    battle = run.first.get("battle") or {}
    truth = (run.truth.get("battle") or {})
    who = truth.get("trainer_truth") or {}
    script = who.get("script") or {}
    eyes_id = battle.get("opponent_trainer_id")
    run.check(eyes_id is not None and eyes_id == who.get("trainer_from_script") and who.get("last_talked_local_id") == who.get("selected_object_local_id")
              and who.get("templates_with_that_local_id") == 1,
              f"OPPONENT trainer id eyes {eyes_id} (gTrainerBattleOpponent_A) == truth {who.get('trainer_from_script')}: the trainer who "
              f"STARTED the battle, gSpecialVar_LastTalked = local {who.get('last_talked_local_id')} (= gSelectedObjectEvent's object, local "
              f"{who.get('selected_object_local_id')}) -> the map's ROM object template -> its script {script.get('symbol')} bytes "
              f"{script.get('bytes')} = trainerbattle (op 0x{script.get('op', 0):02x}) type {script.get('type')}, trainer "
              f"{who.get('trainer_from_script')}")
    rom = who.get("rom_trainer") or {}
    enemy = truth.get("enemy_party")
    run.check(bool(rom) and rom.get("party") == enemy and who.get("trainers_with_this_party") == [eyes_id],
              f"the ROM's gTrainers[{rom.get('id')}] party {rom.get('party')} == the live gEnemyParty {enemy}, and of the 855 trainers "
              f"only {who.get('trainers_with_this_party')} has exactly that party")
    run.check(rom.get("name") == "JOEY" and eyes_id == 322,
              f"documentation: pret/pokeemerald include/constants/opponents.h `#define TRAINER_JOEY 322`; eyes {eyes_id}; the ROM's "
              f"gTrainers[{rom.get('id')}] name (the probe's charmap) {rom.get('name')!r}")
    run.notes.append(f"SAME BYTES AS THE EYES (not truth, for the record): gTrainerBattleOpponent_A = "
                     f"{truth.get('opponent_trainer_id_SAME_BYTES_AS_EYES')}")


def grade_E6(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="RUSTBORO CITY")
    check_party(run)
    check_progress(run)
    check_objects(run)
    check_tiles(run, want={"warp": 3})
    check_header_guard(run)
    screen = run.first.get("screen") or {}
    tscreen = run.truth.get("screen") or {}
    player = run.first.get("player") or {}
    run.check(player.get("map_const") == "RUSTBORO_CITY_POKEMON_CENTER_1F", f"the Rustboro Pokemon Center: eyes map_const={player.get('map_const')!r}")
    run.check(screen.get("screen") == "text" and screen.get("text_box_open") is True and "Task_DrawFieldMessage" in tscreen.get("tasks", []),
              f"TEXT BOX eyes screen={screen.get('screen')!r} text_box_open={screen.get('text_box_open')} (from sFieldMessageBoxMode) == truth: "
              f"Task_DrawFieldMessage is running in the probe's own gTasks parse {tscreen.get('tasks')} (the task that draws the field "
              f"message box and lives until it closes, src/field_message_box.c; the eyes do not read it)")
    check_waits(run, want_printing=True, want_frozen=True, want_idle_waiting=True)
    nurse = [o for o in first_view_objects(run) if o[2] == 58]
    run.check(len(nurse) == 1, f"the nurse (OBJ_EVENT_GFX_NURSE = 58) is seen: {nurse}")
    run.notes.append(f"SAME BYTES AS THE EYES (not truth, for the record): sFieldMessageBoxMode={tscreen.get('message_box_mode_SAME_BYTE_AS_EYES')}, "
                     f"sTextPrinters[0] active/state={tscreen.get('text_printer_active_state_SAME_BYTES_AS_EYES')}, script native="
                     f"{tscreen.get('script_native')}")


def grade_E7(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="MAUVILLE CITY")
    check_party(run)
    check_progress(run)
    screen = run.first.get("screen") or {}
    tscreen = run.truth.get("screen") or {}
    run.check((screen.get("screen"), screen.get("menu"), screen.get("in_battle")) == ("menu", "party", True)
              and tscreen.get("callback2") == "CB2_UpdatePartyMenu" and tscreen.get("party_menu_type") == 1 and tscreen.get("in_battle_bit"),
              f"MENU eyes screen={screen.get('screen')!r} menu={screen.get('menu')!r} in_battle={screen.get('in_battle')} == truth: gMain.callback2 "
              f"named {tscreen.get('callback2')} by the probe, gPartyMenu.menuType={tscreen.get('party_menu_type')} (1 = "
              f"PARTY_MENU_TYPE_IN_BATTLE, include/constants/party_menu.h; the eyes do not read it), gMain.inBattle={tscreen.get('in_battle_bit')}, "
              f"party-menu tasks {tscreen.get('tasks')}")
    run.check(run.first.get("view") is None, "no overworld view behind a full-screen menu")
    hp = {m["species"]: m["hp"] for m in run.first.get("party", [])}
    run.check((hp.get("Skitty"), hp.get("Taillow"), hp.get("Grovyle")) == (40, 0, 0),
              f"documentation: Skitty 40 HP alive, Taillow + Grovyle fainted; eyes {hp}")
    check_waits(run, want_idle_printing=True, want_idle_waiting=True)
    check_header_guard(run)
    behaviour = (run.probe or {}).get("behaviour") or {}
    run.check(behaviour.get("text_moved_by_itself_at") is not None,
              f"BEHAVIOUR: the party menu's message moved BY ITSELF at frame {behaviour.get('text_moved_by_itself_at')} (look at "
              f"f{run.first.get('frame')}): it was printing, not waiting for a button; printers then {behaviour.get('before_press', {}).get('printers')}")
    # Round 2: the NATURAL capture of RENDER_STATE_WAIT on printer 6.
    waiting = next((p for p in behaviour.get("text_before_press") or [] if p.get("printer") == 6), {})
    run.check(waiting.get("state") == 1 and waiting.get("last_two_bytes") == "fc09" and str(waiting.get("text", "")).endswith("in battle!<FC><09>"),
              f"THE STATE-1 WAIT, NATURAL: when the idle frames end, text printer 6 (the party menu's message window) is in state "
              f"{waiting.get('state')} (1 = RENDER_STATE_WAIT), the two bytes it consumed last are {waiting.get('last_two_bytes')} (fc09 = "
              f"EXT_CTRL_CODE_BEGIN, EXT_CTRL_CODE_PAUSE_UNTIL_PRESS), its buffer {waiting.get('buffer')} reads {waiting.get('text')!r} (the "
              f"menu has since written 'Choose a POKéMON.' over its start; src/strings.c gText_PkmnAlreadyInBattle = "
              f"\"{{STR_VAR_1}} is already\\nin battle!{{PAUSE_UNTIL_PRESS}}\")")


def grade_E8(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="FALLARBOR TOWN")
    check_party(run)
    check_progress(run)
    check_objects(run)
    check_tiles(run, want_connection=True)
    grade_overworld_basics(run)
    check_header_guard(run)


def grade_E9(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_xy=(3, 4))
    player = run.first.get("player") or {}
    run.check(player.get("map_const") == "EVER_GRANDE_CITY_POKEMON_LEAGUE_1F",
              f"documentation: EVER_GRANDE_CITY_POKEMON_LEAGUE_1F; eyes map_const={player.get('map_const')!r}")
    check_party(run)
    counts = check_progress(run)
    run.check((counts["healing"], counts["others"]) == (7, 5),
              f"NON-VACUITY of the healing check: {counts['healing']} healing items and {counts['others']} others in the bag (want 7 and 5)")
    check_objects(run)
    check_tiles(run)
    grade_overworld_basics(run)
    check_header_guard(run)


def grade_E10(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_place(run, doc_map="ROUTE 116")
    check_party(run)
    check_progress(run)
    check_battle(run, "trainer")
    check_text_flags(run)
    check_waits(run, want_printing=True, want_frozen=True, want_idle_waiting=True)
    check_header_guard(run)
    check_opponent(run)
    screen = run.first.get("screen") or {}
    printer = next((p for p in (run.truth.get("screen") or {}).get("active_printers", []) if p.get("printer") == 0), {})
    run.check(printer.get("state") == 1 and printer.get("last_two_bytes") == "fc09" and printer.get("text") == JOEY_DEFEAT_TEXT,
              f"THE DEFEAT TEXT (truth: the probe's own read of text printer 0 and of the buffer it points into, "
              f"{printer.get('buffer')}, by its charmap): state {printer.get('state')} (1 = RENDER_STATE_WAIT), the last two bytes "
              f"{printer.get('last_two_bytes')} (fc09), text {printer.get('text')!r} == Joey's defeat text {JOEY_DEFEAT_TEXT!r}")
    run.check(screen.get("waits_for_button") is True and screen.get("wait_reason") == "text printer 0 WAIT",
              f"the eyes at the defeat text: waits_for_button={screen.get('waits_for_button')} reason={screen.get('wait_reason')!r} "
              f"(want True, 'text printer 0 WAIT'; before the fix: False, arm XW)")
    build = FIXTURES["trainer_defeat_text_r116.ss1"][0].with_suffix(".build.json")
    try:
        made = json.loads(build.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        made = {}
    presses = made.get("presses") or []
    run.check(made.get("out_md5") == FIXTURES["trainer_defeat_text_r116.ss1"][1] and made.get("source_md5") == FIXTURES["trainer_battle_r116.ss1"][1],
              f"THE FIXTURE WAS PLAYED, NOT WRITTEN: {build.name} (make_defeat_text_fixture.py's printout) built md5 {made.get('out_md5')} "
              f"(pinned) from md5 {made.get('source_md5')} (E5's fixture) with {len(presses)} button presses only "
              f"({sorted({p[1] for p in presses})}), stopping at frame {made.get('found_at_frame')} with printer 0 "
              f"{made.get('printer0')}")
    enemy_hp = [c.get("hp") for b in (run.truth.get("battle") or {}).get("battlers", []) if b["side"] == "foe"
                for c in [b.get("second_copy") or {}]]
    outcome = run.first.get("last_battle_outcome")
    run.check(outcome == 1 and enemy_hp and all(hp == 0 for hp in enemy_hp) and len((run.truth.get("battle") or {}).get("enemy_party", [])) == 1,
              f"BATTLE OUTCOME eyes {outcome} (gBattleOutcome; 1 = Won) == truth: every Pokemon of the enemy party has 0 HP in its "
              f"second copy {enemy_hp} (the party {(run.truth.get('battle') or {}).get('enemy_party')})")


#: Arm XW: the waits fix, reverted in a copy of the package (file, old text, new text).
WAIT_MUTANTS: dict[str, tuple[str, str, str] | None] = {
    "XW-0": None,
    "XW-A": ("eyes/view.py", "TEXT_PRINTER_WAIT_STATES = frozenset({1, 2, 3})",
             "TEXT_PRINTER_WAIT_STATES = frozenset({2, 3})  # MUTANT XW-A: the pre-fix states"),
    "XW-B": ("eyes/view.py", "TEXT_PRINTER_COUNT = 32", "TEXT_PRINTER_COUNT = 1  # MUTANT XW-B: printer 0 only, as before the fix"),
}
#: What each copy must show, per fixture: True = every waits check passes; False = caught (some fail).
WAIT_MUTANT_PREDICTIONS = {
    ("XW-0", "trainer_defeat_text_r116.ss1"): True, ("XW-0", "ki17_partymenu_wedge.ss1"): True,
    ("XW-A", "trainer_defeat_text_r116.ss1"): False, ("XW-A", "ki17_partymenu_wedge.ss1"): False,
    ("XW-B", "trainer_defeat_text_r116.ss1"): True, ("XW-B", "ki17_partymenu_wedge.ss1"): False,
}


def make_wait_copy(mutation: tuple[str, str, str] | None) -> Path:
    """A temporary copy of the real package (`live_step0.make_copy`'s pattern), with ONE mutation applied
    exactly once (an anchor that is not unique aborts the arm)."""
    root = Path(tempfile.mkdtemp(prefix="ai_player_step1_waits_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures"))
    if mutation is not None:
        relative, old, new = mutation
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutation anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    return root


def grade_XW(run: Run) -> None:
    for name, mutation in WAIT_MUTANTS.items():
        root = make_wait_copy(mutation)
        try:
            for fixture in ("trainer_defeat_text_r116.ss1", "ki17_partymenu_wedge.ss1"):
                data, raw = probe(fixture, root=root)
                code = (data or {}).get("eyes_code") or {}
                ran_copy = bool(code.get("module")) and Path(code["module"]).resolve().is_relative_to(root.resolve())
                behaviour = (data or {}).get("behaviour") or {}
                grade = waits_grade(behaviour) if behaviour and "error" not in behaviour else None
                wrong = {k: grade[k]["wrong"] for k in ("idle printing", "idle waiting", "printing", "frozen")} if grade else None
                passes = bool(grade) and grade["first_ok"] and not any(wrong.values())
                want = WAIT_MUTANT_PREDICTIONS[(name, fixture)]
                run.check(ran_copy and grade is not None and passes is want,
                          f"[{name}] {fixture}: the copy's eyes ran ({code.get('module')}; wait states {code.get('wait_states')}, printers "
                          f"{code.get('printer_count')}); first look waits={grade and grade['first_waits']} ({grade and grade['first_reason']}) "
                          f"vs truth {grade and grade['truth']}; wrong frames per kind "
                          f"{ {k: len(v) for k, v in (wrong or {}).items()} } of "
                          f"{ {k: grade[k]['frames'] for k in ('idle printing', 'idle waiting', 'printing', 'frozen')} if grade else None }: "
                          f"{'PASSES' if passes else 'CAUGHT'} (predicted {'passes' if want else 'caught'})")
                if data is None:
                    run.notes.append(f"[{name}] {fixture}: no PROBE line: {raw[-1500:]}")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def grade_SC(run: Run) -> None:
    check_purity(run)
    check_records(run)
    check_frame(run)
    check_scorer(run, own_starter(run))


def grade_GEO(run: Run) -> None:
    for fixture in ("dewford.ss1", "route116team.ss1", "boxwithdraw.ss1", "ki15_nurse_wedge.ss1"):
        data, raw = probe(fixture, behaviour=False)
        window = (data or {}).get("window") or {}
        got = (window.get("player_tile_screen_xy"), window.get("camera_pan"), window.get("tile_columns_on_screen"),
               window.get("tile_rows_on_screen"), window.get("half_visible_rows"))
        want = ([112, 72], [0, 32], [-VIEW_HALF_WIDTH, VIEW_HALF_WIDTH], [-VIEW_UP, VIEW_DOWN], [-VIEW_UP, VIEW_DOWN])
        run.check(got == want, f"{fixture}: player tile at screen {got[0]}, pans {got[1]}, columns {got[2]}, rows {got[3]}, "
                  f"half-visible rows {got[4]} == eyes/view.py {want}")
        run.notes.append(f"{fixture} window measurement: {json.dumps(window)}")
        if data and data.get("cost_ms"):
            run.notes.append(f"{fixture} cost of a look (30 looks, one per frame, in-process): {json.dumps(data['cost_ms'])}")
    data, _ = probe("oldale.ss1", behaviour=False)
    window = (data or {}).get("window") or {}
    run.check(window.get("player_tile_screen_xy") != [112, 72],
              f"CONTROL: on the battle fixture the same measurement gives {window.get('player_tile_screen_xy')} (not [112, 72]): not true by construction")


def _set(path: str, value):
    """A mutation: set `path` (dots; an int is a list index) in a dict to `value`."""
    def apply(data: dict) -> None:
        keys = [int(k) if k.lstrip("-").isdigit() else k for k in path.split(".")]
        for key in keys[:-1]:
            data = data[key]
        data[keys[-1]] = value(data[keys[-1]]) if callable(value) else value
    return apply


def _drop_flag(letter: str, where: str):
    """A mutation of the eyes' compact tiles: remove `letter` from the first tile whose flags hold it."""
    def apply(observation: dict) -> None:
        tile = next(t for t in observation["view"]["tiles"] if letter in t[6])
        tile[6] = tile[6].replace(letter, "")
    return apply


#: (arm, what is made wrong, side ("eyes" = the watcher's first look, "truth" = the probe's), mutation,
#: the check that must catch it, a word its failing line must contain). Side "truth" proves a check READS
#: its independent signal (a check that only looked at the eyes would still pass).
GRADER_FAULTS = [
    ("E1", "facing right -> left", "eyes", _set("player.facing", "left"), check_place, "FACING"),
    ("E1", "the sprite's facing right -> up", "truth", _set("facing", "up"), check_place, "FACING"),
    ("E1", "the sprite's OAM hFlip on -> off", "truth", _set("facing_sprite.oam_hflip", False), check_place, "FACING"),
    ("E1", "map name DEWFORD TOWN -> DEWFORD", "eyes", _set("player.map_name", "DEWFORD"), check_place, "MAP NAME"),
    ("E1", "map number 11 -> 12", "eyes", _set("player.map_number", 12), check_place, "MAP (group"),
    ("E4", "in_battle True -> False", "eyes", _set("screen.in_battle", False), check_place, "IN BATTLE"),
    ("E1", "money 5080 -> 5081", "eyes", _set("progress.money", 5081), check_progress, "MONEY"),
    ("E1", "badge 1 dropped", "eyes", _set("progress.badges", []), check_progress, "BADGES"),
    ("E1", "story flag HIDE_PETALBURG_CITY_WALLYS_MOM True -> False", "eyes", _set("progress.flags.6.1", False),
     check_progress, "STORY FLAGS"),
    ("E1", "Pokedex seen 21 -> 22", "eyes", _set("progress.dex_seen", 22), check_progress, "POKEDEX"),
    ("E1", "17 Poke Balls -> 18", "eyes", _set("bag.balls.0.1", 18), check_progress, "BALLS"),
    ("E3", "the Hyper Potion left out of healing", "eyes", _set("bag.healing", []), check_progress, "HEALING"),
    ("E1", "the probe's badge bit cleared", "truth", _set("progress.flags.BADGE01_GET", False), check_progress, "BADGES"),
    ("E2", "one ledge tile loses its ledge", "eyes", None, check_tiles, "TILES"),
    ("E1", "one warp tile loses its warp", "eyes", None, check_tiles, "TILES"),
    ("E1", "one tile's metatile + 1", "eyes", _set("view.tiles.0.2", lambda v: v + 1), check_tiles, "TILES"),
    ("E1", "the probe's ROM decode of one tile's behaviour + 1", "truth", _set("tiles.0.own.behavior", lambda v: v + 1),
     check_tiles, "TILES"),
    ("E5", "opponent trainer 322 -> 323", "eyes", _set("battle.opponent_trainer_id", 323), None, "OPPONENT"),
    ("E5", "the script's trainer argument 322 -> 321", "truth", _set("battle.trainer_truth.trainer_from_script", 321),
     None, "OPPONENT"),
    ("E6", "waits True -> False", "eyes", _set("screen.waits_for_button", False), check_waits, "WAITS"),
    ("E6", "the behaviour: the A press did not move the text", "behaviour", _set("press_moved_the_text", False),
     check_waits, "WAITS"),
    ("E7", "waits False -> True", "eyes", _set("screen.waits_for_button", True), check_waits, "WAITS"),
    ("E6", "the probe's task list without Task_DrawFieldMessage", "truth",
     _set("screen.tasks", lambda tasks: [t for t in tasks if t != "Task_DrawFieldMessage"]), None, "TEXT BOX"),
    ("E7", "gPartyMenu.menuType 1 -> 0", "truth", _set("screen.party_menu_type", 0), None, "MENU"),
    ("E1", "the probe reads one frame later", "probe", _set("frame", lambda v: v + 1), check_frame, "same frame"),
    # round 2
    ("E10", "waits True -> False at the defeat text (the pre-fix answer)", "eyes", _set("screen.waits_for_button", False),
     check_waits, "WAITS FOR A BUTTON"),
    ("E7", "one idle WAITING frame (printer 6, state 1) reads waits=False", "behaviour", _set("idle_waiting_frames.0.1", False),
     check_waits, "WAITING frames"),
    ("E4", "a party move's PP - 1 (Tackle 27 -> 26)", "eyes", _set("party.0.moves.0.pp", lambda v: v - 1), check_party, "PARTY MOVES"),
    ("E7", "Skitty's status paralysis -> ok", "eyes", _set("party.0.status", "ok"), check_party, "PARTY MOVES"),
    ("E4", "the second copy's HP + 1", "truth", _set("battle.battlers.0.second_copy.hp", lambda v: v + 1),
     lambda r: check_battle(r, "wild"), "SECOND COPY"),
    ("E5", "the foe's second copy: a move's PP - 1", "truth", _set("battle.battlers.1.second_copy.moves.0.1", lambda v: v - 1),
     lambda r: check_battle(r, "trainer"), "SECOND COPY"),
    ("E2", "the trainer's (local 3) DRAWN position one tile right", "truth", None, check_objects, "OBJECTS DRAWN"),
    ("E2", "the item ball (local 7) DRAWN inside the window", "truth", None, check_objects, "CROP BY WHAT IS DRAWN"),
    ("E1", "the header check did not refuse the stale header", "probe", _set("header_guard.stale_header_problems", []),
     check_header_guard, "MAP HEADER CHECK"),
    ("E10", "gTextFlags read as MSB-first (0xC0)", "truth", _set("screen.text_flags", 0xC0), check_text_flags, "gTextFlags"),
    ("E10", "the defeat text without its PAUSE_UNTIL_PRESS bytes", "truth", _set("screen.active_printers.0.last_two_bytes", "2100"),
     None, "THE DEFEAT TEXT"),
]


def _move_drawn(local_id: int, dx: float):
    """A truth-side mutation: object `local_id` is DRAWN at dx (its coordinates unchanged)."""
    def apply(truth: dict) -> None:
        target = next(o for o in truth["objects"] if o["local_id"] == local_id)
        target["drawn"]["dx"] = dx(target["drawn"]["dx"]) if callable(dx) else dx
    return apply


OBJECT_FAULTS = {
    "the trainer's (local 3) DRAWN position one tile right": _move_drawn(3, lambda v: v + 1),
    "the item ball (local 7) DRAWN inside the window": _move_drawn(7, 7.0),
}


def grade_XG(run: Run, graded: dict[str, Run]) -> None:
    """FAULT HALF of the new truth checks: each is re-run on a COPY of a graded arm's data with one value
    made wrong (on the eyes' side, or on the TRUTH's side), and must FAIL with its own line; the same
    check on the unchanged copy must PASS (else the failure would mean nothing). No emulator runs."""
    import copy

    tile_faults = {"one ledge tile loses its ledge": _drop_flag("<", "ledge"), "one warp tile loses its warp": _drop_flag("p", "warp"),
                   **OBJECT_FAULTS}
    whole = {"E1": grade_E1, "E5": grade_E5, "E6": grade_E6, "E7": grade_E7, "E10": grade_E10}
    for arm, what, side, mutate, checker, word in GRADER_FAULTS:
        base = graded.get(arm)
        if base is None or not base.records or base.probe is None:
            run.check(False, f"[{arm}] {what}: the arm {arm} did not run in this invocation (run XG with it)")
            continue
        mutate = mutate or tile_faults.get(what)

        def regrade(apply: bool) -> list[str]:
            clone = Run(base.arm, records=copy.deepcopy(base.records), probe=copy.deepcopy(base.probe), ai_log=base.ai_log,
                        run_dir=base.run_dir, stdout=base.stdout, verdict=base.verdict, exit_code=base.exit_code)
            if apply:
                target = {"eyes": clone.records[0]["observation"], "truth": clone.probe.get("truth"), "probe": clone.probe,
                          "behaviour": clone.probe.get("behaviour")}[side]
                mutate(target)
            if checker is None:
                whole[arm](clone)
            else:
                checker(clone)
            return [text for ok, text in clone.checks if not ok]

        control = regrade(False)
        caught = [text for text in regrade(True) if word in text]
        run.check(not control and bool(caught),
                  f"[{arm}] {what} ({side} side): unchanged copy fails {len(control)} check(s); the mutant is CAUGHT by "
                  f"{caught[0][:260] if caught else 'NOTHING'}")


GRADERS = {"E1": grade_E1, "E2": grade_E2, "E2X": grade_E2X, "E3": grade_E3, "E4": grade_E4, "E5": grade_E5,
           "E6": grade_E6, "E7": grade_E7, "E8": grade_E8, "E9": grade_E9, "E10": grade_E10, "XW": grade_XW,
           "SC": grade_SC, "GEO": grade_GEO, "XG": None}


# ---------------------------------------------------------------------- evidence
def provenance() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO), capture_output=True, text=True, timeout=30).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "ai_player"], cwd=str(REPO),
                               capture_output=True, text=True, timeout=30).stdout.strip()
        return f"HEAD {head}; " + ("ai_player/ has UNCOMMITTED changes (the code under test is the working tree)" if dirty else "ai_player/ clean at HEAD")
    except Exception as error:  # noqa: BLE001
        return f"unknown ({error})"


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def write_evidence(run: Run, code_ref: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{EVIDENCE_TAG}-{run.arm.name}.txt"
    fixture = run.arm.fixture
    out = [
        f"AI PLAYER BUILD STEP 1 (THE EYES) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"code: {code_ref}",
        f"fixture: {FIXTURES[fixture][0].relative_to(REPO).as_posix()} md5={md5_of(FIXTURES[fixture][0])}" if fixture else "fixture: (several, see below)",
        f"fixture documentation: {run.arm.doc or '-'}",
        f"command: {' '.join(run.command) or '(no AI run: probes only)'}",
        f"env: {ENV_BRAIN}=watcher {ENV_WATCH_EVERY}={WATCH_EVERY} " + " ".join(f"{k}={v}" for k, v in run.arm.env.items()) if run.command else "env: -",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        "checks (pre-registered in ai_player/gates/live_step1.py's docstring; each quotes both values):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
    ]
    if run.notes:
        out += ["", "---- notes ----", *run.notes]
    if run.verdict is not None:
        out += ["", "---- the instrument's verdict file (purity.json) ----", json.dumps(run.verdict, indent=2, sort_keys=True)]
    if run.records:
        out += ["", f"---- the action log: {len(run.records)} records (digests) ----", *[r.get("digest") or "" for r in run.records],
                "", "---- the FIRST record in full (compact tiles: [x, y, metatile, behavior, collision, elevation, flags]) ----",
                json.dumps(run.records[0], sort_keys=True)]
    if run.probe is not None:
        out += ["", "---- GROUND TRUTH: gates/probe_eyes.py on the same fixture (truth, window, behaviour, cost; its own eyes look omitted) ----",
                json.dumps({k: v for k, v in run.probe.items() if k not in ("eyes",)}, sort_keys=True)]
    elif run.probe_raw:
        out += ["", "---- probe output (no PROBE line) ----", run.probe_raw[-3000:]]
    if run.stdout:
        keep = [line for line in run.stdout.splitlines() if line.startswith(("[AI-", "[DRIVER]")) or re.match(r"^f\d+ ", line)]
        out += ["", "---- evidence lines from stdout ([AI-*] and the scorer lines) ----", *keep]
    if run.ai_log:
        out += ["", "---- ai_player.log (the AI's own log: what scoring.parse_log reads) ----", run.ai_log.rstrip()]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:  # noqa: BLE001
            continue
        if ("pokebot.py" in cmd and PROFILE in cmd) or "probe_eyes.py" in cmd:
            found.append(f"pid {proc.info['pid']}: {cmd[:160]}")
    return found


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 1 (the eyes).")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS))
    args = parser.parse_args()
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2
    for name, (path, md5) in FIXTURES.items():
        actual = md5_of(path) if path.is_file() else "MISSING"
        if actual != md5:
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}: different bytes, results would not compare")
            return 2
    build_root = launcher.resolve_build_root()
    code_ref = provenance()
    results: list[Run] = []
    for arm in [a for a in ARMS if a.name in wanted]:
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        if arm.fixture is None:
            run = Run(arm)
        else:
            run = run_watcher(arm, build_root)
            run.probe, run.probe_raw = probe(arm.fixture)
        if arm.name == "XG":
            grade_XG(run, {done.arm.name: done for done in results})
        else:
            GRADERS[arm.name](run)
        evidence = write_evidence(run, code_ref)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text}")
        cost = next((line for line in run.stdout.splitlines() if line.startswith("[AI-EYES] cost")), "")
        if cost:
            print(f"  live {cost}")
    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<4} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
