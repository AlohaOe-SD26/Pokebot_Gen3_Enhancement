"""TEST SIDE (build step 5): the PLAY brain in a throwaway emulator, in this process, with the GAME's own story read beside it.

    py -3.12 ai_player/gates/play_harness.py (--fresh | --state PATH) [--seed N] [--frames N] [--personality P]
                                             [--starter S] [--target MILESTONE] [--fault no_hints|no_training]
                                             [--game-clock YYYY-MM-DDTHH:MM] [--clock HH:MM] [--world-in world.jsonl]
                                             [--save-end PATH] [--run-dir DIR] [--every N]
    prints one line: PLAY {json}

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
         "rested_at_home": 16}
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
    raw_stats = bytes(emulator.read_bytes(sb1 + SB1_GAME_STATS, 4 * 20))
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

    def after_frame(self) -> None:
        self.frame += 1
        if self.frame % self.every:
            return
        try:
            now = story_truth(self.context, guard=True)
            outcome, flags = battle_now()
        except Exception:  # noqa: BLE001 - the save blocks move between screens: try again next time
            self.errors += 1
            return
        if self.outcome == 0 and outcome != 0:
            self.battles.append({"f": self.frame, "outcome": outcome, "result": OUTCOMES.get(outcome, str(outcome)),
                                 "trainer": bool(flags & BATTLE_TYPE_TRAINER), "stats": now["stats"]})
        self.outcome = outcome
        self._step_sample(now["stats"]["steps"])
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
                "last": self.last, "blips": self.blips, "battles": self.battles, "steps": self.steps}


#: (build step 5.1) THE WAITS by a second path, test side: the tasks that poll a button THEMSELVES (a yes/no, a menu with a
#: cursor, a list), by their `gTasks[].func` symbols (the decomp's names, `src/*.c`); with the framework's own
#: `modules.tasks.is_waiting_for_input` (a text printer waiting for A or B, a script's WaitForAorBPress), the GAME WAITS
#: FOR A PRESS. Never the AI's eyes.
INPUT_TASKS = ("Task_HandleYesNoInput", "Task_HandleConfirmStarterInput", "Task_HandleStarterChooseInput",
               "Task_HandleMultichoiceInput", "Task_HandleMultichoiceGridInput", "Task_ShopMenu", "Task_BuyMenu",
               "Task_BuyHowManyDialogueHandleInput", "Task_SetClock_HandleInput", "Task_SetClock_HandleConfirmInput",
               "Task_CallYesOrNoCallback", "StartMenuTask", "Task_HandleMainMenuInput",
               "Task_NewGameBirchSpeech_ProcessNameYesNoMenu", "Task_NewGameBirchSpeech_ChooseGender",
               "Task_ReturnToItemListAfterItemPurchase", "Task_HandleCaughtMonPageInput",
               # (build step 5.1, the verifier's round: battles covered) the party menu's list and its action menu (a
               # Pokemon sent in, in a battle or on the field) and the bag's list (a ball thrown, an item used)
               "Task_HandleChooseMonInput", "Task_HandleSelectionMenuInput", "Task_BagMenu_HandleInput")
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
    then). The tasks that poll a button count on every screen."""
    from modules.battle_state import get_battle_controller_callback
    from modules.memory import get_game_state, read_symbol
    from modules.tasks import TaskList, is_waiting_for_input

    tasks = TaskList(read_symbol("gTasks"))
    for name in INPUT_TASKS:
        if name in tasks:
            return name
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
    return "a text or script waits for A/B" if is_waiting_for_input() else None


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


def play(context, seed: int, frames: int, run_dir: Path, personality: str | None, starter: str | None, target: str,
         faults: set[str], clock: str | None, world_in: str | None, recorder: StoryRecorder | None) -> dict:
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.mode import BrainSettings, HandsBrain
    from ai_player.options import DEFAULT_MART_COUNT, DEFAULT_MART_ITEM, HandsOptions

    emulator = context.emulator
    clock_value = tuple(int(p) for p in clock.split(":")) if clock else None
    options = HandsOptions(brain="play", run_dir=run_dir, seed=seed, personality=personality, mart_item=DEFAULT_MART_ITEM,
                           mart_count=DEFAULT_MART_COUNT, clock=clock_value, fault_ungated_a=False, fault_blind_count=False,
                           world_in=Path(world_in) if world_in else None, target=target, starter=starter,
                           fault_no_hints="no_hints" in faults, fault_no_training="no_training" in faults,
                           fault_no_errands="no_errands" in faults)
    lines: list[str] = []
    brain = HandsBrain(BrainSettings(frames=frames), lines.append, options)
    controls = HarnessControls(emulator)
    waits = WaitRecorder(controls)
    started = time.monotonic()
    steps = brain.play(controls, FrameworkEyes())
    reason, count = "harness: the brain overran its budget", 0
    # (build step 5.1: every loop bounded) at most the brain's frames and a margin: the brain ends itself within its budget
    for count in range(frames + 11):
        try:
            next(steps)
        except StopIteration as done:
            reason = done.value
            break
        emulator.run_single_frame()
        if recorder is not None:
            recorder.after_frame()
        waits.after_frame()
    else:
        count = frames + 11
    return {"seed": seed, "personality": personality, "starter": starter, "target": target, "faults": sorted(faults),
            "reason": reason, "frames": count, "seconds": round(time.monotonic() - started, 1), "presses": controls.presses,
            "lines": lines, "report": brain.play_report, "actions": str(run_dir / "actions.jsonl"),
            "world_file": str(run_dir / "world.jsonl"), "waits_game": waits.result()}


def run(state: Path | None, seed: int, frames: int, personality: str | None, starter: str | None, target: str,
        faults: set[str], game_clock: str | None, clock: str | None, world_in: str | None, run_dir: Path,
        save_end: Path | None, every: int, checkpoints: Path | None = None) -> dict:
    context = boot(PROFILE)
    emulator = context.emulator
    if state is not None:
        emulator.load_save_state(state.read_bytes())
    if game_clock:
        pin_game_clock(emulator, game_clock)
    start = story_truth(context) if state is not None else None
    recorder = StoryRecorder(context, every, checkpoints)
    result = play(context, seed, frames, run_dir, personality, starter, target, faults, clock, world_in, recorder)
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
    args = parser.parse_args()
    if args.state is None and not args.fresh:
        parser.error("--state PATH or --fresh")
    faults = {f.strip() for f in args.fault.split(",") if f.strip()}
    unknown = faults - set(FAULTS)
    if unknown:
        parser.error(f"unknown faults {sorted(unknown)}: {FAULTS}")
    run_dir = args.run_dir or Path(tempfile.mkdtemp(prefix="ai_play_"))
    result = run(args.state, args.seed, args.frames, args.personality, args.starter, args.target, faults, args.game_clock,
                 args.clock, args.world_in, run_dir, args.save_end, args.every, args.checkpoints)
    print("PLAY " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
