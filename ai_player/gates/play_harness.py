"""TEST SIDE (build step 5): the PLAY brain in a throwaway emulator, in this process, with the GAME's own story read beside it.

    py -3.12 ai_player/gates/play_harness.py (--fresh | --state PATH) [--seed N] [--frames N] [--personality P]
                                             [--starter S] [--target MILESTONE] [--fault no_hints|no_training]
                                             [--game-clock YYYY-MM-DDTHH:MM] [--clock HH:MM] [--world-in world.jsonl]
                                             [--save-end PATH] [--run-dir DIR] [--every N]
                                             [--profile-dir DIR [--memory FILE [--continue]]]
    prints one line: PLAY {json}
    (R1 + R2, build spec 2026-10-29 section 5) `--profile-dir` boots a throwaway profile with a FILE-BACKED cartridge save,
    `--memory` hands the brain its memory file (it then saves through the game's dialog), `--continue` continues that
    cartridge's save from power-on in place of `--fresh` (`memory_options`). `gates/live_r1.py` drives these.

WHY: a run through the real launcher is the PROOF (purity, `gates/live_step5.py`); this harness runs the SAME brain
(`ai_player.mode.HandsBrain`, brain "play") on the framework's emulator in-process (`gates/hands_harness.py` HarnessControls:
the controller's exact semantics), so chapter 1 can be developed, seeded by the dozen and RATED (`gates/rate_step5.py`).
Nothing here is evidence of purity.

THE SECOND PATH (`StoryRecorder`): every `--every` frames (default 30) the harness reads, with ITS OWN code and never the
AI's eyes, save block 1's flags and vars at the numbers `knowledge/milestones.json` names (each checked against the decomp by
`gates/extract_milestones.py --verify`) and the game's OWN counters (`include/global.h` gameStats, XOR save block 2's key:
GAME_STAT_STEPS, _WILD_BATTLES, _TRAINER_BATTLES), and records the frame each one CHANGED with the counters at that frame:
"the rival's flag went up at f123,456 with 9 wild battles fought before it" is the GAME's statement, not the AI's. At the
end: `hands_harness.truth` (party by PID, the bag, money, the battle counters) and the milestone marks by the same second
path (`story_truth`).

THE BATTLES (the step-5 verifier's round, 2026-10-14): the same samples read the game's `gBattleOutcome` (`src/battle_main.c`:
cleared to 0 by `BattleStartClearSetData` when a battle starts, set when it ends: B_OUTCOME_WON 1, LOST 2, DREW 3, RAN 4,
CAUGHT 7, `include/constants/battle.h`) and `gBattleTypeFlags` (set by `src/battle_setup.c` for each battle and kept until
the next; BATTLE_TYPE_TRAINER 1 << 3). Every change of the outcome from 0 to a value is one battle ENDED, recorded with
its frame, outcome and kind: the GAME's count of wild battles WON before the rival (not merely met: the wild-battle
counter also counts the ones fled) and of battles LOST (whiteouts), never the AI's own.

THE STEPS (the step-5 verifier's round 2, 2026-10-14: "wild battles WON before the rival" was met by the arm that never
trains in 6 of 10 seeds, so no GAME count told training from none): the same samples keep GAME_STAT_STEPS (the game's own
step counter) every time it changed, [frame, steps]. `gates/rate_step5.py` reads it, and the battles above, inside the
windows the AI's log says it was ROAMING TO TRAIN: the steps the GAME counted and the wild battles the GAME says were won
there. An arm that never trains has no such window, so both are 0.

THE GAME READS (build step 5.3, stage A2: the B1 debt is paid from the GAME, so first the game must be read; recorded in the
PLAY json's `game_reads` and in `READS_FILE`, NOT graded: stage A2 measures, the coordinator decides each debt row from the
numbers, stage B grades): (i) the party's HP at each battle's start, ONE start per battle (latched on the game's own
`gMain.inBattle`, so a visit to the in-battle BAG or PARTY menu does not start the same battle again), and at each
battle's end (`StoryRecorder` battle_starts and each battle's `party`); (ii) the tile type under the player at every position change, so the steps in tall grass
(`TileRecorder`); (iii) a press log with the player's facing and position at each press (`HarnessControls.log`), so a
turn on the spot is countable (`spins_of`); (iv) the frame equality, `frame0 + the harness's frames == the emulator's
count at the end` (`frame_check`: a mismatch prints a HARNESS FAIL line); (v) who ended the run, the harness's frame
budget or the AI's own return, from the harness's loop and never the brain's text (`harness_stop`). Each read is made by
the harness from memory, the emulator or the framework's map and player objects, never derived from the AI's records
(USER RULING 35; `06` 2026-10-23 D3). Their known answers, both ways, are `gates/test_step53_a2.py` LiveKnownAnswerTests.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import PROFILE, HarnessControls, pin_game_clock, truth  # noqa: E402
from ai_player.gates.probe_eyes import _u32, boot  # noqa: E402

KNOWLEDGE = REPO / "ai_player" / "knowledge" / "milestones.json"
#: `include/global.h` struct SaveBlock1: flags @0x1270, vars @0x139C, gameStats @0x159C; SaveBlock2 encryptionKey @0xAC.
SB1_FLAGS, SB1_VARS, SB1_GAME_STATS, SB2_KEY, VARS_START = 0x1270, 0x139C, 0x159C, 0xAC, 0x4000
#: `include/constants/game_stat.h`
STATS = {"steps": 5, "total_battles": 7, "wild_battles": 8, "trainer_battles": 9, "captures": 11, "used_pokecenter": 15,
         "rested_at_home": 16,
         # (build step 5.3, the re-sourcing fix round, R5: "it shopped" by the game) GAME_STAT_SHOPPED, raised once per
         # purchase as the money is taken (`src/shop.c` BuyMenuSubtractMoney, pinned decomp 731ad5b)
         "shopped": 38}
#: (test side) every item ball's FLAG_ITEM_* on badge 1's maps (`gates/extract_milestones.py --items`)
ITEM_FLAGS = Path(__file__).resolve().parent / "fixtures" / "item_flags.json"
FAULTS = ("no_hints", "no_training", "no_errands")


def tracked() -> tuple[dict[str, int], dict[str, int]]:
    """(flag name -> number, var name -> number) of every milestone proof (the knowledge file, decomp-checked)."""
    data = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    flags: dict[str, int] = {}
    variables: dict[str, int] = {}
    for milestone in data["milestones"]:
        flags.update(milestone["done"]["flags"])
        flags.update({f"TRAINER_{name}": number for name, number in milestone["done"]["trainers"].items()})
        variables.update({name: info["number"] for name, info in milestone["done"]["variables"].items()})
    # the rival's own trainer flags (the six Route 103 battles: whichever the player's starter set)
    for name, info in data["trainers"].items():
        flags.setdefault(f"TRAINER_{name}", info["flag"])
    return flags, variables


def story_truth(context, guard: bool = False) -> dict:
    """The milestone marks and the game's counters by the SECOND PATH (module docstring). `guard` (the recorder's samples
    while the game runs): refuse a frame on which the save blocks may be moving."""
    from modules.memory import read_symbol

    emulator = context.emulator
    if guard and _u32(read_symbol("gMain", 0x0C, 4), 0) == 0:
        # gMain.vblankCallback NULL: the save blocks may be MOVING (`MoveSaveBlocks_ResetHeap`, at every battle start and
        # map load; the eyes withhold the same frames, `host/eyes.py` _save_blocks_may_be_moving): no reading this frame
        raise RuntimeError("the save blocks may be moving (gMain.vblankCallback is NULL)")
    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    flag_bytes = bytes(emulator.read_bytes(sb1 + SB1_FLAGS, 300))
    var_bytes = bytes(emulator.read_bytes(sb1 + SB1_VARS, 0x200))
    key = int.from_bytes(bytes(emulator.read_bytes(sb2 + SB2_KEY, 4)), "little")
    raw_stats = bytes(emulator.read_bytes(sb1 + SB1_GAME_STATS, 4 * (max(STATS.values()) + 1)))
    flags, variables = tracked()
    out = {name: (flag_bytes[number // 8] >> (number % 8)) & 1 for name, number in flags.items()}
    out.update({f"VAR_{name}": int.from_bytes(var_bytes[2 * (number - VARS_START):2 * (number - VARS_START) + 2], "little")
                for name, number in variables.items()})
    stats = {name: int.from_bytes(raw_stats[4 * index:4 * index + 4], "little") ^ key for name, index in STATS.items()}
    items = {name: (flag_bytes[info["number"] // 8] >> (info["number"] % 8)) & 1
             for name, info in json.loads(ITEM_FLAGS.read_text(encoding="utf-8"))["flags"].items()}
    return {"marks": out, "stats": stats, "items": items}


#: `include/constants/battle.h`
BATTLE_TYPE_TRAINER = 1 << 3
#: THE STEPS: the fewest frames a step can take (running or on a bike: 8 frames a tile, `src/field_player_avatar.c` speeds;
#: walking 16): the step counter cannot rise faster
STEP_RATE = 8
OUTCOMES = {1: "won", 2: "lost", 3: "drew", 4: "ran", 5: "teleported", 6: "the foe fled", 7: "caught", 8: "no safari balls",
            9: "forfeited", 10: "the foe teleported"}


def battle_now() -> tuple[int, int]:
    """(gBattleOutcome, gBattleTypeFlags) by the framework's symbol reads (module docstring, THE BATTLES)."""
    from modules.memory import read_symbol

    return read_symbol("gBattleOutcome", size=1)[0], _u32(read_symbol("gBattleTypeFlags", size=4), 0)


def party_now() -> list | None:
    """The party by the framework's own decoder (species, level, HP, max HP), or None when it cannot be read this frame:
    a mark's change carries it (the rate grader reads the party's level and HP left at the rival's flag)."""
    from modules.pokemon_party import get_party

    try:
        return [[m.species.name, m.level, m.current_hp, m.total_hp] for m in get_party()]
    except Exception:  # noqa: BLE001 - a party mid-copy: no reading
        return None


def game_state_now() -> str:
    """(Build step 5.3, stage A2) The game's state by the framework's own read (`modules.memory.get_game_state`: the main
    callback), e.g. "OVERWORLD" or "BATTLE"."""
    from modules.memory import get_game_state

    return get_game_state().name


#: (build step 5.3, stage A2 fix round, read i) `include/main.h` struct Main: the byte at 0x439 holds the bit-fields
#: oamLoadDisabled:1, inBattle:1, anyLinkBattlerHasFrontierPass:1 (GCC on the ARM fills them from bit 0), so inBattle is bit 1
GMAIN_BATTLE_BYTE, IN_BATTLE_BIT = 0x439, 1 << 1


def battle_flag_now() -> bool:
    """(Build step 5.3, stage A2 fix round, read i) The GAME's own "a battle is on": `gMain.inBattle`, by the framework's
    symbol read. pret/pokeemerald sets it TRUE in `CB2_InitBattleInternal` (`src/battle_main.c`) as every battle begins,
    and sets it FALSE only as the battle ENDS (`ReturnFromBattleToOverworld`, `FreeRestoreBattleData`, the controllers'
    `SetBattleEndCallbacks` and the link ends, and `reload_save.c`). The in-battle BAG and PARTY menus leave it set (the
    party menu reads it there, `src/party_menu.c`), while the framework's game state reads BAG_MENU or PARTY_MENU for them
    (`modules/memory.py`: CB2_BAGMENURUN, CB2_UPDATEPARTYMENU) and BATTLE again on the way back. WHY: the step-5.3 A2
    verifier MEASURED two starts for one wild battle after a bag visit (the second with mid-fight HP) when a start was
    "BATTLE after a sample that was not"; this flag is what tells "the same battle, back from a menu" from "a new one"."""
    from modules.memory import read_symbol

    return bool(read_symbol("gMain", GMAIN_BATTLE_BYTE, 1)[0] & IN_BATTLE_BIT)


#: (build step 5.3, stage A2, read ii) the framework's name of the metatile behaviour of tall grass
#: (`modules/map.py` `_get_tile_type_name`, MB_TALL_GRASS), where wild battles are met
TALL_GRASS = "Tall Grass"


def tile_now() -> tuple[str, int, int] | None:
    """(Build step 5.3, stage A2, read ii) The player's ("group:number", x, y) on the OVERWORLD by the framework's player
    object (`modules.player.get_player_avatar`), or None off it."""
    if game_state_now() != "OVERWORLD":
        return None
    from modules.player import get_player_avatar

    avatar = get_player_avatar()
    group, number = avatar.map_group_and_number
    x, y = avatar.local_coordinates
    return f"{int(group)}:{int(number)}", int(x), int(y)


def tile_type_now() -> str:
    """(Build step 5.3, stage A2, read ii) The metatile behaviour under the player by the framework's map read
    (`modules.map.get_map_data_for_current_position().tile_type`, `modules/map.py`), e.g. `TALL_GRASS` or "Normal"."""
    from modules.map import get_map_data_for_current_position

    return str(get_map_data_for_current_position().tile_type)


class TileRecorder:
    """(Build step 5.3, stage A2, read ii) THE GRASS STEPS by the game. Every frame (cheap: the player object's position,
    which the framework reads from the object events), and ONLY when the position changed (the costly map read): the tile
    type under the player, recorded as `[frame, "group:number", x, y, tile type]`. The run's first position is `start`
    (where it began, no step); a warp is a change like any other (its tile is the door's or the arrival's, never grass).
    WHY every frame: a running or cycling step takes 8 frames (`STEP_RATE`), so the places recorder's 10-frame samples can
    skip a tile, and "steps in tall grass" (the step-5.3 critic's Q1: NOTRAIN won 3+ wild battles before the rival in 13 of
    18 seeds, so battles won do not tell training from none) needs every tile entered. Recorded, not graded."""

    def __init__(self) -> None:
        self.frame = 0
        self.errors = 0
        self.start: list | None = None
        self.steps: list[list] = []
        self._at: tuple | None = None

    def after_frame(self) -> None:
        self.frame += 1
        try:
            where = tile_now()
        except Exception:  # noqa: BLE001 - a read between screens: try again next frame
            self.errors += 1
            return
        if where is None or where == self._at:
            return
        self._at = where
        try:
            tile = tile_type_now()
        except Exception:  # noqa: BLE001 - logged None, counted
            tile = None
            self.errors += 1
        record = [self.frame, *where, tile]
        if self.start is None:
            self.start = record
        else:
            self.steps.append(record)

    def result(self) -> dict:
        return {"every": 1, "start": self.start, "steps": self.steps, "moves": len(self.steps),
                "grass_steps": sum(1 for step in self.steps if step[4] == TALL_GRASS), "errors": self.errors}


def spins_of(log: list[list]) -> dict:
    """(Build step 5.3, stage A2, read iii) From the press log (`HarnessControls.log`, `[frame, button, kind, frames,
    facing, map, x, y]`): between each two presses read on the overworld, a SPIN when the facing changed and the position
    did not (a turn on the spot), a MOVE when the position changed. Counted from the GAME's facing and position, never the
    AI's roam reports. Presses off the overworld (facing None) neither count nor break a pair's comparison."""
    spins = moves = 0
    previous = None
    for press in log:
        if press[4] is None:
            continue
        if previous is not None:
            if press[5:8] != previous[5:8]:
                moves += 1
            elif press[4] != previous[4]:
                spins += 1
        previous = press
    return {"spins": spins, "moves": moves}


def frame_check(frame0: int | None, harness_frames: int, recorder_frames: int | None, frame_end: int | None) -> dict:
    """(Build step 5.3, stage A2, read iv) THE FRAME EQUALITY: the emulator's own frame counter before the play loop
    (`frame0`) plus the frames the HARNESS ran (`harness_frames`, its `run_single_frame` calls) must equal the counter at
    the end, and the story recorder must have seen every one of those frames (`recorder_frames`, None when there is no
    recorder). WHY: every game read of the run is stamped with the recorder's frame; a frame run by anyone else (the AI's
    code calling the emulator, a load) would shift every stamp silently. A mismatch is a visible harness FAIL
    (`frame_check_line`), recorded in the PLAY json, never fixed up."""
    equal = (frame0 is not None and frame_end is not None and frame0 + harness_frames == frame_end
             and (recorder_frames is None or recorder_frames == harness_frames))
    return {"frame0": frame0, "frame_end": frame_end, "harness_frames": harness_frames, "recorder_frames": recorder_frames,
            "equal": bool(equal)}


def frame_check_line(check: dict) -> str | None:
    """The harness FAIL line for a frame check that does not hold (None when it holds)."""
    if check["equal"]:
        return None
    return (f"HARNESS FAIL: the frame count does not add up: frame0 {check['frame0']} + the harness's "
            f"{check['harness_frames']} frames != the emulator's {check['frame_end']} at the end (the recorder saw "
            f"{check['recorder_frames']})")


def harness_stop(ai_returned: bool, frames_run: int, frame_budget: int) -> dict:
    """(Build step 5.3, stage A2, read v; `06` 2026-10-23 D3) WHO ENDED THE RUN, from the harness's OWN counters, never the
    brain's text: "ai" when the AI's play generator returned (StopIteration: whatever reason it gave, which stays in
    `reason`), "harness" when the harness's loop ran out of its frame budget first. This in-process harness has no wall
    clock of its own (`wall_clock_seconds` None): the sweep's subprocess timeout kills it with no PLAY line at all."""
    return {"by": "ai" if ai_returned else "harness",
            "cause": "the AI's play loop returned" if ai_returned else "the harness's frame budget ran out",
            "frames_run": frames_run, "frame_budget": frame_budget, "wall_clock_seconds": None}


class StoryRecorder:
    """Every `every` frames: the marks and the counters by the second path; each change recorded with its frame.

    A change counts only when the NEXT sample reads the same value (it is recorded at the frame it was first read, with
    that sample's counters). MEASURED 2026-10-14 (the chapter-1 sweep step5dev4, seed 7): one sample at a wild battle's
    start read DEFEATED_RIVAL_ROUTE103 as set, 18,000 frames before the rival was met (an emulator frame can end while the
    game is moving its save blocks, `MoveSaveBlocks_ResetHeap`, so the pointer and the bytes it points at disagree for
    that frame); the grader took it as the rival's frame and graded the seed as having trained 0 steps before it. So a
    sample is not taken while `gMain.vblankCallback` is NULL (`story_truth`: the frames the eyes withhold for the same
    reason, counted in `errors`), and a reading no second sample confirms is counted in `blips`, never a change."""

    def __init__(self, context, every: int = 30, checkpoints: Path | None = None) -> None:
        self.context = context
        self.every = every
        #: (development) a folder where the emulator's state is saved at every milestone mark's change (test side)
        self.checkpoints = checkpoints
        self.frame = 0
        self.last: dict | None = None
        self.changes: list[dict] = []
        self.errors = 0
        self.blips: list[dict] = []
        #: a change read once, waiting for the next sample to confirm it: name -> its change record
        self.pending: dict[str, dict] = {}
        #: every battle ENDED (module docstring, THE BATTLES): {"f", "outcome", "result", "trainer", "stats"}
        self.battles: list[dict] = []
        self.outcome: int | None = None
        #: THE STEPS (module docstring): [frame, GAME_STAT_STEPS] at every sample where the game's step counter changed
        self.steps: list[list[int]] = []
        #: (build step 5.2) [frame, GAME_STAT_POKEMON_CAPTURES] and [frame, item-ball flags set] at every change: what a
        #: curiosity goal BROUGHT, by the game (`gates/rate_step5.py` game_yield)
        self.captures: list[list[int]] = []
        self.item_flags: list[list[int]] = []
        #: (build step 5.3, stage A2, read i) THE PARTY'S HP AT EACH BATTLE'S START, ONE START PER BATTLE: [frame, party]
        #: at the battle's first sample whose game state is BATTLE (`party_now`: [species, level, HP, max HP] per member,
        #: None when the party could not be read). Every battle END above carries its own `party` the same way. WHY: "the
        #: party's HP when a battle began" and "what a battle left" were the AI's own battle records (B1 debt R5.REST_RULE
        #: and L5.REST_RULE); these are the GAME's. Recorded, not graded (stage A2 measures before stage B decides).
        self.battle_starts: list[list] = []
        #: THE LATCH (the A2 fix round): True from a battle's recorded start until a sample reads the game's
        #: `gMain.inBattle` clear (`battle_flag_now`), so the BATTLE state coming back from the in-battle BAG or PARTY menu
        #: is the SAME battle, never a new start (MEASURED by the A2 verifier: 18 extra starts in 4 CH2/CH2_OFF smoke runs,
        #: each with mid-fight HP). None before the first readable sample: a run that BEGINS inside a battle records no
        #: start for that battle (it did not start there).
        self.in_battle: bool | None = None

    def after_frame(self) -> None:
        self.frame += 1
        if self.frame % self.every:
            return
        try:
            now = story_truth(self.context, guard=True)
            outcome, flags = battle_now()
            fighting = game_state_now() == "BATTLE"
            battle_on = battle_flag_now()
        except Exception:  # noqa: BLE001 - the save blocks move between screens: try again next time
            self.errors += 1
            return
        if self.in_battle is None:
            self.in_battle = fighting or battle_on  # the run's first sample: a battle already on did not start here
        elif fighting and self.in_battle is False:
            self.battle_starts.append([self.frame, party_now()])  # the battle's FIRST BATTLE sample: its one start
            self.in_battle = True
        elif self.in_battle and not fighting and not battle_on:
            self.in_battle = False  # the game says the battle is over: the next BATTLE sample is a new battle
        if self.outcome == 0 and outcome != 0:
            self.battles.append({"f": self.frame, "outcome": outcome, "result": OUTCOMES.get(outcome, str(outcome)),
                                 "trainer": bool(flags & BATTLE_TYPE_TRAINER), "stats": now["stats"],
                                 # (build step 5.3, stage A2, read i) the party's HP the battle LEFT, by the game
                                 "party": party_now()})
        self.outcome = outcome
        self._step_sample(now["stats"]["steps"])
        for timeline, value in ((self.captures, now["stats"]["captures"]), (self.item_flags, sum(now["items"].values()))):
            if not timeline or timeline[-1][1] != value:
                timeline.append([self.frame, value])
        if self.last is None:
            self.last = now
            return
        for name, value in now["marks"].items():
            waiting = self.pending.pop(name, None)
            if waiting is not None:
                if value == waiting["to"]:
                    self.changes.append(waiting)  # confirmed by a second sample: recorded at its first frame
                    self.last["marks"][name] = value
                    if self.checkpoints is not None:
                        self.checkpoints.mkdir(parents=True, exist_ok=True)
                        (self.checkpoints / f"{waiting['f']:07d}-{name}-{value}.ss1").write_bytes(
                            self.context.emulator.get_save_state())
                    continue
                self.blips.append({**waiting, "next": value, "next_f": self.frame})
            if value != self.last["marks"].get(name):
                self.pending[name] = {"f": self.frame, "mark": name, "from": self.last["marks"].get(name), "to": value,
                                      "stats": now["stats"], "party": party_now()}
        self.last = {"marks": dict(self.last["marks"]), "stats": now["stats"], "items": now["items"]}

    def _step_sample(self, steps: int) -> None:
        """THE STEPS: the game's step counter at this sample, kept as it was read whenever it changed (the reader of the
        timeline, `steps_counted`, takes only the rises the game can have made)."""
        if not self.steps or self.steps[-1][1] != steps:
            self.steps.append([self.frame, steps])

    def result(self) -> dict:
        return {"every": self.every, "changes": self.changes, "errors": self.errors, "frames": self.frame,
                "last": self.last, "blips": self.blips, "battles": self.battles, "steps": self.steps,
                "captures": self.captures, "item_flags": self.item_flags, "battle_starts": self.battle_starts}


#: (build step 5.1) THE WAITS by a second path, test side: the tasks that poll a button THEMSELVES (a yes/no, a menu with a
#: cursor, a list), by their `gTasks[].func` symbols (the decomp's names, `src/*.c`); with the framework's own
#: `modules.tasks.is_waiting_for_input` (a text printer waiting for A or B, a script's WaitForAorBPress), the GAME WAITS
#: FOR A PRESS (since the verifier's second round the harness's own `text_waits_now` in place of that read). Never the AI's
#: eyes.
INPUT_TASKS = ("Task_HandleYesNoInput", "Task_HandleConfirmStarterInput", "Task_HandleStarterChooseInput",
               "Task_HandleMultichoiceInput", "Task_HandleMultichoiceGridInput", "Task_ShopMenu", "Task_BuyMenu",
               "Task_BuyHowManyDialogueHandleInput", "Task_SetClock_HandleInput", "Task_SetClock_HandleConfirmInput",
               "Task_CallYesOrNoCallback", "Task_HandleMainMenuInput",
               "Task_NewGameBirchSpeech_ProcessNameYesNoMenu", "Task_NewGameBirchSpeech_ChooseGender",
               "Task_ReturnToItemListAfterItemPurchase", "Task_HandleCaughtMonPageInput",
               # (build step 5.1, the verifier's round: battles covered) the party menu's list and its action menu (a
               # Pokemon sent in, in a battle or on the field) and the bag's list (a ball thrown, an item used)
               "Task_HandleChooseMonInput", "Task_HandleSelectionMenuInput", "Task_BagMenu_HandleInput")
#: R1 (build spec 2026-10-29 E7, finding F7): the START MENU is no longer an INPUT_TASKS name. `StartMenuTask` only BUILDS the
#: menu (pret/pokeemerald `src/start_menu.c` CreateStartMenuTask / InitStartMenuStep: no input), and `Task_ShowStartMenu` runs
#: the menu's input AND the whole save dialog (its 256-261-frame flash write included, which polls nothing): the precise rule,
#: by the harness's OWN symbol reads, is `start_menu_input` (never the AI's eyes).
START_MENU_INPUT_CALLBACK = "HandleStartMenuInput"
SAVE_MENU_CALLBACK = "SaveCallback"
SAVE_INPUT_CALLBACKS = ("SaveConfirmInputCallback", "SaveOverwriteInputCallback")


def start_menu_input(tasks: set | frozenset | dict, show_data0: int | None, menu_callback: str | None,
                     save_callback: str | None) -> str | None:
    """R1 (E7): does the START MENU or the SAVE's yes/no poll the pad now? `tasks` the active task names, `show_data0`
    `Task_ShowStartMenu`'s data[0], the two callbacks NAMED (None when not one of the start menu's). The menu takes input
    only under `Task_ShowStartMenu` past its first frame (data[0] 0 sets `gMenuCallback` and polls nothing, `:566-573`) with
    `gMenuCallback == HandleStartMenuInput`; the save's yes/no only under `SaveCallback` with one of the two input callbacks
    (`:984-1084`). Neither callback is ever cleared, so a stale one under `StartMenuTask`, or after the task, is no wait."""
    if "Task_ShowStartMenu" not in tasks or "StartMenuTask" in tasks or not show_data0:
        return None
    if menu_callback == START_MENU_INPUT_CALLBACK:
        return "Task_ShowStartMenu (HandleStartMenuInput)"
    if menu_callback == SAVE_MENU_CALLBACK and save_callback in SAVE_INPUT_CALLBACKS:
        return f"Task_ShowStartMenu (SaveCallback: {save_callback})"
    return None


def start_menu_input_now(tasks) -> str | None:
    """`start_menu_input` by the harness's own reads: the task list (`modules.tasks.TaskList`), `gMenuCallback` and
    `sSaveDialogCallback` by symbol, each compared with the address `modules.game.get_symbol` gives the name (thumb bit off)."""
    from modules.game import get_symbol
    from modules.memory import read_symbol

    show = tasks["Task_ShowStartMenu"]
    if show is None:
        return None

    def named(symbol: str, names: tuple[str, ...]) -> str | None:
        address = int.from_bytes(bytes(read_symbol(symbol, 0, 4)), "little") & ~1
        return next((name for name in names if address and get_symbol(name)[0] & ~1 == address), None)

    present = {name for name in ("Task_ShowStartMenu", "StartMenuTask") if tasks[name] is not None}
    menu = named("gMenuCallback", (START_MENU_INPUT_CALLBACK, SAVE_MENU_CALLBACK))
    save = named("sSaveDialogCallback", SAVE_INPUT_CALLBACKS) if menu == SAVE_MENU_CALLBACK else None
    return start_menu_input(present, show.data_value(0), menu, save)


#: (build step 5.1, the verifier's round) the player's battle controller POLLING THE PAD (`src/battle_controller_player.c`):
#: the action menu, the move grid, a target (a double battle), the moves' reordering, the yes/no ("Use next POKéMON?")
BATTLE_INPUT_CALLBACKS = ("HandleInputChooseAction", "HandleInputChooseMove", "HandleInputChooseTarget",
                          "HandleMoveSwitching", "PlayerHandleYesNoInput")
#: ... and a battler's controller WAITING ON the text printer (each controller file has its own of these: the message of
#: any battler's turn); with printer 0 waiting for A/B, the battle's text waits for a press
BATTLE_TEXT_WAITS = ("CompleteOnInactiveTextPrinter", "CompleteOnInactiveTextPrinter2")
#: (build step 5.1) the second path's stretches at least this long are kept (shorter ones are counted)
WAIT_KEEP = 60


class WaitRecorder:
    """(build step 5.1) Every `every` frames: does the GAME wait for a press (`INPUT_TASKS`, `is_waiting_for_input`, read by
    the framework's own code), and has a press begun since the last sample (`HarnessControls.presses`, counted where the
    button goes down)? A STRETCH is a run of
    samples that wait with no press between them; its frames are the last sample's less the first's. Graded by
    `gates/rate_step5.py` beside the AI's own record (`hands/waiting.py`)."""

    def __init__(self, controls: HarnessControls, every: int = 10) -> None:
        self.controls = controls
        self.every = every
        self.frame = 0
        self.samples = self.errors = self.waiting_samples = 0
        self.open: list | None = None  # [first, last, presses, what]
        self.kept: list[list] = []
        self.longest: list | None = None
        self.count = 0

    def after_frame(self) -> None:
        self.frame += 1
        if self.frame % self.every:
            return
        try:
            what = waits_now()
        except Exception:  # noqa: BLE001 - a read between screens: try again next time
            self.errors += 1
            return
        self.samples += 1
        presses = self.controls.presses
        stretch = self.open
        if stretch is not None and (what is None or presses != stretch[2]):
            self._close(stretch)
            stretch = self.open = None
        if what is None:
            return
        self.waiting_samples += 1
        if stretch is None:
            self.open = [self.frame, self.frame, presses, what]
        else:
            stretch[1] = self.frame

    def _close(self, stretch: list) -> None:
        frames = stretch[1] - stretch[0]
        self.count += 1
        if self.longest is None or frames > self.longest[2]:
            self.longest = [stretch[0], stretch[1], frames, stretch[3]]
        if frames >= WAIT_KEEP:
            self.kept.append([stretch[0], stretch[1], frames, stretch[3]])

    def result(self) -> dict:
        if self.open is not None:
            self._close(self.open)
            self.open = None
        return {"every": self.every, "samples": self.samples, "errors": self.errors, "waiting_samples": self.waiting_samples,
                "stretches": self.count, "longest": self.longest, "kept": self.kept}


def waits_now() -> str | None:
    """(build step 5.1) What makes the GAME wait for a press now, by the framework's own reads (`WaitRecorder`), or None. A
    text or a script waiting for A/B is read on the OVERWORLD by the framework's `is_waiting_for_input`; in a BATTLE (the
    verifier's round: "the game-side second path does not cover battles") by the battle's own state: a battler's
    controller waiting on the text printer (`CompleteOnInactiveTextPrinter`, `BATTLE_TEXT_WAITS`) while printer 0 waits
    for A/B (`sTextPrinters[0]` active, state CLEAR or SCROLL_START: `src/text.c`), or the player's controller polling the
    pad (`BATTLE_INPUT_CALLBACKS`: the action menu, the move grid, a target, the yes/no). MEASURED 2026-10-14 (the
    development sweep step51dev2, seed 9): during a wild battle's opening the framework's overworld read of printer 0 said
    "waiting" for 510 frames before "Wild WURMPLE appeared!" was printed (a printer state left from before the battle);
    the controller condition is what tells a battle's own text from such a state (no controller waits on the printer
    then). The tasks that poll a button count on every screen. (The verifier's second round: the overworld read is now the
    harness's own, `text_waits_now`: the framework's `is_waiting_for_input` reads a script's LEFTOVER native pointer as a
    wait. MEASURED on a diagnostic replay of NOHINTS seed 938: in a wild battle's opening, BATTLE_STARTING, printer 0 was
    inactive and the context Stopped while that pointer named WaitForAorBPress; the 2026-10-14 "printer state left from
    before the battle" may have been this pointer, NOT measured then.)"""
    from modules.battle_state import get_battle_controller_callback
    from modules.memory import get_game_state, read_symbol
    from modules.tasks import TaskList

    tasks = TaskList(read_symbol("gTasks"))
    for name in INPUT_TASKS:
        if name in tasks:
            return name
    menu = start_menu_input_now(tasks)  # R1 (E7): the start menu and the save's yes/no, by the precise rule
    if menu is not None:
        return menu
    state = get_game_state().name
    if state == "BATTLE":
        battlers = read_symbol("gBattlersCount", size=1)[0]
        callbacks = [get_battle_controller_callback(index) for index in range(min(battlers, 4))]
        for index, callback in enumerate(callbacks):
            if index % 2 == 0 and callback in BATTLE_INPUT_CALLBACKS:
                return f"the battle's {callback} (battler {index})"
        if any(callback in BATTLE_TEXT_WAITS for callback in callbacks):
            active, printer_state = read_symbol("sTextPrinters", offset=0x1B, size=2)
            if active and printer_state in (2, 3):
                return "a battle text waits for A/B"
        return None
    if state != "OVERWORLD":
        return None
    return "a text or script waits for A/B" if text_waits_now() else None


#: (build step 5.2, the verifier's second round) the script's native function while it waits in `waitbuttonpress`
#: (pret/pokeemerald `src/scrcmd.c` ScrCmd_waitbuttonpress -> SetupNativeScript(ctx, WaitForAorBPress))
WAIT_NATIVE = "WaitForAorBPress"
#: `src/script.c` SCRIPT_MODE_NATIVE, as the framework's `ScriptContext.mode` names it
NATIVE_MODE = "Native"


def text_waits(mode: str, native: str | None, printer: tuple[int, int]) -> bool:
    """(build step 5.2, the verifier's second round) Does a text or a script wait for A/B, from the global script context's
    MODE and native function and text printer 0's (active, state)? A script waits only while its context RUNS that native
    (`NATIVE_MODE`): pret/pokeemerald `src/script.c` (read 2026-10-16) `StopScript` sets the mode STOPPED and never clears
    `nativePtr`, and a native that returns TRUE hands the context back to BYTECODE with `nativePtr` unchanged, so the pointer
    names the LAST native the context ran, long after it returned. A printer waits while active in state 2 or 3 (as the
    framework reads it). The framework's `is_waiting_for_input` asks the pointer alone: MEASURED on a diagnostic replay of
    NOHINTS seed 938 (f70300-f70740, and after each battle of its look round at f70318), the player WALKED, controllable,
    the context Stopped, printer 0 inactive, while it said "waiting", so the recorder counted no free time and none of the
    50 tiles its windows showed for the first time. (The AI's eyes have refused that leftover since build step 1,
    `eyes/view.py` script_waits_for_button; this is the harness's own read, from the decomp.)"""
    if mode == NATIVE_MODE and native == WAIT_NATIVE:
        return True
    return bool(printer[0]) and printer[1] in (2, 3)


def text_waits_now() -> bool:
    """`text_waits` by the framework's reads: the global script context (`modules.tasks.get_global_script_context`) and
    `sTextPrinters[0]` (Emerald). Test side: never the AI's eyes."""
    from modules.memory import read_symbol
    from modules.tasks import get_global_script_context

    script = get_global_script_context()
    active, state = read_symbol("sTextPrinters", offset=0x1B, size=2)
    return text_waits(script.mode, script.native_function_name, (active, state))


#: (build step 5.2) the game's pushing stretches at least this long (free frames) are kept (`PlaceRecorder`)
PUSH_KEEP = 300


class PlaceRecorder:
    """(build step 5.2, the step-5.1 review's findings 1, 3 and 5) THE PLACES by a second path, test side: every `every`
    frames, by the framework's own reads (`modules.player.get_player_avatar`: the player object's map and coordinates;
    `player_avatar_is_controllable`; `text_waits_now`, the framework's script context and text printer; the game state),
    never the AI's eyes:
      * the tiles the GAME's screen showed (the gate's own window, `gates/window.py`, round every position the player stood
        on while free: SEEN tiles, keyed by the map group, number and the map's own coordinates, as the AI's memory keys
        them) and the samples that showed NEW ones (`new_tiles`, [frame, how many]); the maps stood on, in order
        (`stays`, [frame, "group:number"] at each change), the player's position at each change (`moves`), and the
        stretches a text or a script waited for A/B on the overworld (`texts`, a TALK or a page read), and the stretches
        the game was in a BATTLE (`battles`): what a curiosity goal BROUGHT for its own time, and whether a detour stood
        where it said, by the game (`gates/rate_step5.py` game_yield);
      * THE PUSHING PROPERTY's second path (`push`): a stretch is the FREE time (controllable, nothing waiting for A/B)
        since the last NEW thing (a tile the screen showed for the first time, a map first stood on, a battle), paused by
        time that is not free, counted only when the controls pressed something in it (`HarnessControls.presses`); the
        longest, and every one of `PUSH_KEEP` frames or more.
    `seen` (a chapter-2 run's): the tiles its chapter 1 showed (`seen_tiles.json` of that run), so they are not new.
    (The verifier's second round) The run's OPENING window, the screen its first free sample showed, is no goal's yield:
    it is recorded as `opening` and not in `new_tiles` (seven truck chats of 16-44 frames had been credited its 165 tiles)."""

    def __init__(self, controls, every: int = 10, seen: set | None = None, pages: set | None = None) -> None:
        from ai_player.gates.window import SCREEN_DOWN, SCREEN_HALF_WIDTH, SCREEN_UP

        self.controls = controls
        self.every = every
        self.frame = 0
        self.samples = self.errors = 0
        #: (build step 5.2, the verifier's round: "the game's second path credits ANY text begun in a goal's span as a
        #: talk", the nurse's welcome right after a heal, a scripted stop met again) the PAGES the game has shown in this run
        #: (and, `pages`, in the run this one goes on from: its `TEXTS_FILE`), read from the game's message buffer
        #: (`gStringVar4`, where the field's message boxes expand what they print) when a text began waiting for A/B, cut
        #: where the box waits for a press (`split_pages`); every `texts` stretch says whether its message showed a page
        #: NEVER shown before. (The verifier's SECOND round: whole messages were compared, so OLDALE's footprints man, whose
        #: talk is the last two pages of his own scene, "told something new" 20 times by the game and never by the AI.)
        #: `text_errors`: buffer reads that failed or found no page (counted new, and reported)
        self.pages: set[str] = set(pages or ())
        self.text_errors = 0
        self.window = [(dx, dy) for dx in range(-SCREEN_HALF_WIDTH, SCREEN_HALF_WIDTH + 1)
                       for dy in range(-SCREEN_UP, SCREEN_DOWN + 1)]
        self.seen: set = set(seen or ())
        self.maps: set = {key[:2] for key in self.seen}
        #: (the verifier's second round) the new tiles of the run's first free window: the screen it began on
        self.opening: int | None = None
        self.new_tiles: list[list[int]] = []
        self.stays: list[list] = []
        self.moves: list[list] = []
        self.texts: list[list[int]] = []
        self._text: list[int] | None = None
        #: (build step 5.2, step52dev2) the stretches the game state was BATTLE, [first, last] sample frames
        self.battles: list[list[int]] = []
        self._battle: list[int] | None = None
        #: the open pushing stretch: [first, last, free frames, presses at its start]
        self._stretch: list | None = None
        self._free_at: int | None = None
        self.longest: list | None = None
        self.kept: list[list] = []
        self.count = 0

    def after_frame(self) -> None:
        self.frame += 1
        if self.frame % self.every:
            return
        try:
            sample = place_now()
        except Exception:  # noqa: BLE001 - a read between screens: try again next time
            self.errors += 1
            return
        self.samples += 1
        state, where, free, waiting = sample
        new = 0
        if where is not None:
            group, number, x, y = where
            stay = f"{group}:{number}"
            if not self.stays or self.stays[-1][1] != stay:
                self.stays.append([self.frame, stay])
            if not self.moves or self.moves[-1][1:] != [stay, x, y]:
                self.moves.append([self.frame, stay, x, y])
            if free:
                if (group, number) not in self.maps:
                    self.maps.add((group, number))
                    new += 1
                window = {(group, number, x + dx, y + dy) for dx, dy in self.window}
                fresh = window - self.seen
                self.seen |= fresh
                if self.opening is None:
                    # (the verifier's second round) the screen the run began on: seen, and no goal's yield
                    self.opening = len(fresh)
                elif fresh:
                    self.new_tiles.append([self.frame, len(fresh)])
                    new += len(fresh)
        if waiting and state == "OVERWORLD":
            if self._text is not None and self._text[1] >= self.frame - self.every:
                self._text[1] = self.frame
            else:
                # (build step 5.2, the verifier's round; its second round: by PAGE) did the message show a page the game
                # never showed before in the run?
                try:
                    pages = shown_pages()
                except Exception:  # noqa: BLE001 - a read between screens: counted, and the text counted new
                    pages = None
                if not pages:
                    self.text_errors += 1
                # (its own name: `new` above counts the new tiles, and a stretch closes on it)
                unseen = not pages or any(page not in self.pages for page in pages)
                self.pages.update(pages or ())
                self._text = [self.frame, self.frame, bool(unseen)]
                self.texts.append(self._text)
        if state == "BATTLE":
            # (step52dev2) the stretches the game was in a BATTLE: a look round's yield is counted over its own time
            if self._battle is not None and self._battle[1] >= self.frame - self.every:
                self._battle[1] = self.frame
            else:
                self._battle = [self.frame, self.frame]
                self.battles.append(self._battle)
        if state == "BATTLE" or new:
            self._close()
            self._free_at = None
            if state == "BATTLE":
                return
        if not free:
            self._free_at = None
            return
        presses = self.controls.presses
        if self._stretch is None:
            self._stretch = [self.frame, self.frame, 0, presses]
        elif self._free_at is not None:
            self._stretch[2] += self.frame - self._free_at
            self._stretch[1] = self.frame
        self._free_at = self.frame

    def _close(self) -> None:
        stretch, self._stretch = self._stretch, None
        if stretch is None or self.controls.presses - stretch[3] <= 0:
            return
        self.count += 1
        record = [stretch[0], stretch[1], stretch[2], self.controls.presses - stretch[3]]
        if self.longest is None or record[2] > self.longest[2]:
            self.longest = record
        if record[2] >= PUSH_KEEP:
            self.kept.append(record)

    def result(self) -> dict:
        self._close()
        return {"every": self.every, "samples": self.samples, "errors": self.errors, "seen": len(self.seen),
                "opening": self.opening, "new_tiles": self.new_tiles, "stays": self.stays, "moves": self.moves,
                "texts": self.texts, "pages": len(self.pages), "text_errors": self.text_errors,
                "battles": self.battles, "push": {"longest": self.longest, "kept": self.kept, "stretches": self.count, "keep": PUSH_KEEP}}


#: (build step 5.2, the verifier's second round) pret/pokeemerald `include/constants/characters.h` (read 2026-10-16):
#: CHAR_PROMPT_SCROLL 0xFA "waits for button press and scrolls dialog", CHAR_PROMPT_CLEAR 0xFB "waits for button press and
#: clears dialog": where a message box WAITS FOR A PRESS, so where one page a person reads ends; EOS 0xFF ends the string;
#: EXT_CTRL_CODE_BEGIN 0xFC and PLACEHOLDER_BEGIN 0xFD carry argument bytes, skipped as `modules.game.decode_string` skips
#: them (its lengths), so an argument byte is never read as a break
PAGE_BREAKS = (0xFA, 0xFB)
STRING_END = 0xFF
CONTROL_CODE, PLACEHOLDER = 0xFC, 0xFD


def split_pages(raw: bytes, decode) -> list[str]:
    """(build step 5.2, the verifier's second round) The PAGES of an encoded message: its bytes up to the string's end, cut
    at every code where the box waits for a press (`PAGE_BREAKS`), each piece decoded by `decode` (bytes -> str, the
    framework's `decode_string`) and its spacing normalised; empty pieces left out. OLDALE's footprints man's scene,
    "Aaaaah! Wait!\\nPlease don't come in here.\\pI just discovered ...\\pWait until ...", is three pages; his talk is the
    last two of them (pret/pokeemerald `data/maps/OldaleTown/scripts.inc`, read 2026-10-16)."""
    data = bytes(raw)
    pieces: list[bytes] = []
    piece = bytearray()
    at = 0
    while at < len(data):
        byte = data[at]
        at += 1
        if byte == STRING_END:
            break
        if byte in PAGE_BREAKS:
            pieces.append(bytes(piece))
            piece = bytearray()
            continue
        piece.append(byte)
        if byte == PLACEHOLDER:
            piece += data[at:at + 1]
            at += 1
        elif byte == CONTROL_CODE and at < len(data):
            code = data[at]
            length = 3 if code in (0x04, 0x0C, 0x10) else 2 if code in (0x01, 0x02, 0x03, 0x06, 0x08, 0x0D) else 1
            piece += data[at:at + length]
            at += length
    pieces.append(bytes(piece))
    pages = [" ".join(str(decode(piece + bytes([STRING_END])) or "").split()) for piece in pieces]
    return [page for page in pages if page]


def shown_pages() -> list[str]:
    """(build step 5.2, the verifier's round; its second round: the PAGES, not the whole message) The pages of the message
    the field's text box is showing, by the framework's own reads: `gStringVar4`, the buffer a message is expanded into
    before it is printed (pret/pokeemerald `src/field_message_box.c` ShowFieldMessage, `src/menu_helpers.c`
    DisplayMessageAndContinueTask: read 2026-10-15), cut into pages (`split_pages`) and decoded
    (`modules.game.decode_string`). Test side: never the AI's eyes."""
    from modules.game import decode_string
    from modules.memory import read_symbol

    return split_pages(read_symbol("gStringVar4"), decode_string)


def place_now() -> tuple[str, tuple[int, int, int, int] | None, bool, bool]:
    """(build step 5.2) The game's state, the player's (map group, number, x, y) on the overworld, whether the player is
    FREE (the framework's `player_avatar_is_controllable`, no script running in the global script context, text printer 0
    not printing and nothing waiting for A/B: a scene's text printing is no free time, MEASURED on the development smoke
    run of seed 1000, where controllability alone counted PROF. BIRCH's lab scene as 4,200 free frames) and whether a text
    or a script waits for A/B (since the verifier's second round `text_waits_now`, not the framework's
    `is_waiting_for_input`, which reads a finished script's leftover pointer as a wait), by the framework's own reads
    (`PlaceRecorder`)."""
    from modules.memory import get_game_state, read_symbol
    from modules.player import get_player_avatar, player_avatar_is_controllable
    from modules.tasks import get_global_script_context

    state = get_game_state().name
    if state != "OVERWORLD":
        return state, None, False, False
    avatar = get_player_avatar()
    group, number = avatar.map_group_and_number
    x, y = avatar.local_coordinates
    waiting = text_waits_now()
    printing = bool(read_symbol("sTextPrinters", offset=0x1B, size=1)[0])
    free = (bool(player_avatar_is_controllable()) and not waiting and not printing
            and not get_global_script_context().is_active)
    return state, (int(group), int(number), int(x), int(y)), free, waiting


def steps_counted(timeline: list[list[int]], start: int, end: int) -> tuple[int, int]:
    """THE STEPS the game counted between frames `start` and `end` of a recorder's timeline (`StoryRecorder.steps`): the
    sum of every rise between two readings inside the window that the game CAN have made (at most one step per
    `STEP_RATE` frames, +2 for a step under way at each reading); and how many changes were refused as impossible (a
    reading taken while the counter was being re-keyed or the save blocks moved: a spike up and back down). Robust by
    construction: a refused spike loses at most the few real steps on either side of it."""
    counted = refused = 0
    previous = None
    for frame, steps in timeline:
        if frame > end:
            break
        if previous is not None and frame > start:
            rise, gap = steps - previous[1], frame - previous[0]
            if 0 < rise <= 2 + gap // STEP_RATE:
                counted += rise
            else:
                refused += 1
        previous = (frame, steps)
    return counted, refused


#: (build step 5.2) the file a run's game-side seen tiles are written to (`PlaceRecorder`), for the run that goes on from it
SEEN_FILE = "seen_tiles.json"


def read_seen(path: str | None) -> set:
    """(build step 5.2) The tiles a run's `SEEN_FILE` says the game's screen showed: {(group, number, x, y)}."""
    if not path or not Path(path).is_file():
        return set()
    return {tuple(int(v) for v in item.split(":")) for item in json.loads(Path(path).read_text(encoding="utf-8"))}


#: (build step 5.2, the verifier's round) the file beside `SEEN_FILE` with the pages a run's game showed (`PlaceRecorder`
#: pages; whole messages before the verifier's second round), for the run that goes on from it: a chapter-2 talk is NEW
#: only if it shows a page chapter 1 never showed either
TEXTS_FILE = "seen_texts.json"
#: (the verifier's second round: "a row-level recount needs the %TEMP% run folders" and the rows were clipped) the
#: second path's whole record of a run (`PlaceRecorder.result`), beside its action log, for a recount
PLACES_FILE = "places.json"
#: (build step 5.3, stage A2) the five game reads of a run (the PLAY json's `game_reads`), beside its places
READS_FILE = "game_reads.json"


def frame_count(emulator) -> int | None:
    """(Build step 5.3, stage A2, read iv) The emulator's own frame counter (`get_frame_count`), or None when it has
    none (the frame check then reads not-equal: no count is no proof)."""
    try:
        return int(emulator.get_frame_count())
    except Exception:  # noqa: BLE001
        return None


def read_texts(seen_path: str | None) -> set:
    """(build step 5.2, the verifier's round) The pages the run whose `SEEN_FILE` is `seen_path` showed (its `TEXTS_FILE`,
    beside it); none for a run that wrote none."""
    if not seen_path:
        return set()
    path = Path(seen_path).with_name(TEXTS_FILE)
    return set(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else set()


def memory_options(memory: Path | None, continue_game: bool) -> dict:
    """(R1 + R2, build spec 2026-10-29 sections 3 (e) and 5) The `HandsOptions` fields a run with a memory file gets from
    the harness, as the launcher would give them (`host/launcher.py` cmd_run): the memory file, a continue, what the cart
    held (D17: `continued` for a continue; `empty` otherwise, as `--fresh` and `--state` empty it), and `host` "harness"
    (the session line's: this side has no lifecycle, so D12 (a) judges a harness session by its `end` line alone). A run
    WITHOUT a memory file gets none of them: the brain's options are then exactly the pre-R1 harness's (D14)."""
    if memory is None:
        if continue_game:
            raise ValueError("--continue needs --memory (a continue restores the memory of the save it continues)")
        return {}
    return {"memory_file": Path(memory), "continue_game": bool(continue_game),
            "cart": "continued" if continue_game else "empty", "host": "harness"}


def play(context, seed: int, frames: int, run_dir: Path, personality: str | None, starter: str | None, target: str,
         faults: set[str], clock: str | None, world_in: str | None, recorder: StoryRecorder | None,
         seen_in: str | None = None, memory: Path | None = None, continue_game: bool = False,
         watch=None) -> dict:
    """`memory` / `continue_game` (R1 + R2): `memory_options`. `watch` (TEST SIDE, `gates/live_r1.py`): a callable given
    the harness's controls, returning recorders whose `after_frame()` runs after every frame, after the harness's own (a
    watcher may BLOCK there: the live proof's kill point, with no frame in flight)."""
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.mode import MAX_LOSSES, BrainSettings, HandsBrain
    from ai_player.options import DEFAULT_MART_COUNT, DEFAULT_MART_ITEM, HandsOptions

    emulator = context.emulator
    clock_value = tuple(int(p) for p in clock.split(":")) if clock else None
    options = HandsOptions(brain="play", run_dir=run_dir, seed=seed, personality=personality, mart_item=DEFAULT_MART_ITEM,
                           mart_count=DEFAULT_MART_COUNT, clock=clock_value, fault_ungated_a=False, fault_blind_count=False,
                           world_in=Path(world_in) if world_in else None, target=target, starter=starter,
                           fault_no_hints="no_hints" in faults, fault_no_training="no_training" in faults,
                           fault_no_errands="no_errands" in faults, **memory_options(memory, continue_game))
    lines: list[str] = []
    brain = HandsBrain(BrainSettings(frames=frames), lines.append, options)
    controls = HarnessControls(emulator)
    watchers = list(watch(controls)) if watch is not None else []
    waits = WaitRecorder(controls)
    # (build step 5.2) THE PLACES by the second path: the tiles the game's screen showed, the maps, the texts, the pushing
    places = PlaceRecorder(controls, seen=read_seen(seen_in), pages=read_texts(seen_in))
    # (build step 5.3, stage A2, read ii) the tile under the player at every position change
    tiles = TileRecorder()
    started = time.monotonic()
    steps = brain.play(controls, FrameworkEyes())
    reason, count = "harness: the brain overran its budget", 0
    budget = frames + 11
    # (build step 5.3, stage A2, read iv) the emulator's own frame counter before the loop, and the frames THIS loop runs
    frame0 = frame_count(emulator)
    ran = 0
    ai_returned = False
    # (build step 5.1: every loop bounded) at most the brain's frames and a margin: the brain ends itself within its budget
    for count in range(budget):
        try:
            next(steps)
        except StopIteration as done:
            reason = done.value
            ai_returned = True
            break
        emulator.run_single_frame()
        ran += 1
        if recorder is not None:
            recorder.after_frame()
        waits.after_frame()
        places.after_frame()
        tiles.after_frame()
        for watcher in watchers:
            watcher.after_frame()
    else:
        count = budget
    frames_game = frame_check(frame0, ran, recorder.frame if recorder is not None else None, frame_count(emulator))
    failed = frame_check_line(frames_game)
    if failed:
        print(failed, flush=True)  # the visible harness FAIL (the PLAY line records it too)
    game_reads = {
        # (read i) the party's HP at each battle's start (one per battle) and end, by the game (`StoryRecorder`)
        "battle_hp": {"every": recorder.every if recorder is not None else None,
                      "starts": recorder.battle_starts if recorder is not None else [],
                      "ends": [[b["f"], b["result"], b["trainer"], b.get("party")] for b in recorder.battles]
                      if recorder is not None else []},
        # (read ii) the tile type at every position change
        "tiles": tiles.result(),
        # (read iii) every press with the facing and position at it, and what the GAME's facing makes of them
        "presses": {"count": controls.presses, "log": controls.log, "errors": controls.log_errors, **spins_of(controls.log)},
        # (read iv) the frame equality
        "frames": frames_game,
        # (read v) who ended the run, by the harness's own counters
        "stop": harness_stop(ai_returned, count, budget),
    }
    places_result = places.result()
    seen_file = run_dir / SEEN_FILE
    seen_file.write_text(json.dumps(sorted(":".join(str(v) for v in tile) for tile in places.seen)), encoding="utf-8")
    (run_dir / TEXTS_FILE).write_text(json.dumps(sorted(places.pages), ensure_ascii=False), encoding="utf-8")
    (run_dir / PLACES_FILE).write_text(json.dumps(places_result, ensure_ascii=False), encoding="utf-8")
    # (build step 5.3, stage A2) the five game reads beside the places, so a kept run folder (`--keep-runs`) holds them
    (run_dir / READS_FILE).write_text(json.dumps(game_reads, ensure_ascii=False), encoding="utf-8")
    return {"seed": seed, "personality": personality, "starter": starter, "target": target, "faults": sorted(faults),
            "reason": reason, "frames": count, "seconds": round(time.monotonic() - started, 1), "presses": controls.presses,
            "lines": lines, "report": brain.play_report, "actions": str(run_dir / "actions.jsonl"),
            "world_file": str(run_dir / "world.jsonl"), "waits_game": waits.result(), "places": places_result,
            "seen_file": str(seen_file),
            # (build step 5.3, A1-2) the play loop's MAX_LOSSES this run played with (the copy's own `mode.py`: 1 in a STOP
            # plan's copy), recorded by the HARNESS, which runs the AI anyway: the grader reads it here and imports nothing
            # from the AI (`rate_step5` LOSE3, the G-3 rule)
            "max_losses": MAX_LOSSES,
            # (build step 5.3, stage A2) THE GAME READS, each made by the harness from the game (memory, the emulator, the
            # framework's map and player objects), never from the AI's records: RECORDED, not graded (`READS_FILE`)
            "game_reads": game_reads}


def run(state: Path | None, seed: int, frames: int, personality: str | None, starter: str | None, target: str,
        faults: set[str], game_clock: str | None, clock: str | None, world_in: str | None, run_dir: Path,
        save_end: Path | None, every: int, checkpoints: Path | None = None, seen_in: str | None = None,
        profile_dir: Path | None = None, memory: Path | None = None, continue_game: bool = False, watch=None) -> dict:
    """`profile_dir` (R1 + R2, the live proof): boot on that throwaway profile FOLDER with the framework's FILE-BACKED
    cartridge save (`probe_save_kill.boot_profile`: `current_save.sav` read and written, as a real run's), instead of the
    in-memory fixture profile; the caller made it and owns it. `memory`, `continue_game`, `watch`: `play`."""
    if continue_game and (state is not None or profile_dir is None):
        raise ValueError("--continue boots a profile's cartridge save from power-on: it needs --profile-dir and no --state")
    if profile_dir is not None:
        from ai_player.gates.probe_save_kill import boot_profile

        context = boot_profile(Path(profile_dir), file_backed=True)
    else:
        context = boot(PROFILE)
    emulator = context.emulator
    if state is not None:
        emulator.load_save_state(state.read_bytes())
    if game_clock:
        pin_game_clock(emulator, game_clock)
    start = story_truth(context) if state is not None else None
    recorder = StoryRecorder(context, every, checkpoints)
    result = play(context, seed, frames, run_dir, personality, starter, target, faults, clock, world_in, recorder,
                  seen_in, memory, continue_game, watch)
    result["story"] = recorder.result()
    result["truth"] = truth(context)
    result["story_truth"] = story_truth(context)
    result["start_story"] = start
    if save_end is not None:
        save_end.parent.mkdir(parents=True, exist_ok=True)
        save_end.write_bytes(emulator.get_save_state())
        result["saved_end"] = str(save_end)
    return result


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) == 3 and sys.argv[1] == "truth":
        # the second path of a saved state: `hands_harness.truth` and the story's marks, counters and item flags
        context = boot(PROFILE)
        data = Path(sys.argv[2]).read_bytes()
        context.emulator.load_save_state(data)
        out = {**truth(context), "story": story_truth(context), "state_md5": __import__("hashlib").md5(data).hexdigest()}
        print("TRUTH " + json.dumps(out, ensure_ascii=False), flush=True)
        return 0
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state", type=Path)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--frames", type=int, default=300000)
    parser.add_argument("--personality", choices=("Catcher", "Story", "Trainer"))
    parser.add_argument("--starter", choices=("TREECKO", "TORCHIC", "MUDKIP"))
    parser.add_argument("--target", default="ch1_pokedex")
    parser.add_argument("--fault", default="", help=f"comma list of {FAULTS}")
    parser.add_argument("--game-clock", help="the cartridge's clock pinned from this ISO time (`hands_harness.pin_game_clock`)")
    parser.add_argument("--clock", help="HH:MM the AI sets on the wall clock (default: the computer's local time)")
    parser.add_argument("--world-in", help="a world.jsonl to start from")
    parser.add_argument("--save-end", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--every", type=int, default=30, help="frames between two second-path reads of the story")
    parser.add_argument("--checkpoints", type=Path, help="(development) save the state at every milestone mark's change here")
    parser.add_argument("--seen-in", help="(build step 5.2) the seen_tiles.json of the run this one goes on from")
    parser.add_argument("--profile-dir", type=Path, help="(R1 + R2) boot on this throwaway profile folder with a FILE-BACKED "
                                                         "cartridge save (the caller made it)")
    parser.add_argument("--memory", type=Path, help="(R1 + R2) the game's memory.jsonl (the profile's AppPaths path): the "
                                                    "brain saves through the game's dialog and keeps it")
    parser.add_argument("--continue", dest="continue_game", action="store_true",
                        help="(R1 + R2) CONTINUE the cartridge save from power-on (needs --profile-dir and --memory)")
    args = parser.parse_args()
    if args.continue_game:
        if args.state is not None or args.fresh or args.profile_dir is None or args.memory is None:
            parser.error("--continue needs --profile-dir and --memory, and no --state or --fresh")
    elif args.state is None and not args.fresh:
        parser.error("--state PATH or --fresh")
    faults = {f.strip() for f in args.fault.split(",") if f.strip()}
    unknown = faults - set(FAULTS)
    if unknown:
        parser.error(f"unknown faults {sorted(unknown)}: {FAULTS}")
    run_dir = args.run_dir or Path(tempfile.mkdtemp(prefix="ai_play_"))
    result = run(args.state, args.seed, args.frames, args.personality, args.starter, args.target, faults, args.game_clock,
                 args.clock, args.world_in, run_dir, args.save_end, args.every, args.checkpoints, args.seen_in,
                 args.profile_dir, args.memory, args.continue_game)
    print("PLAY " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
