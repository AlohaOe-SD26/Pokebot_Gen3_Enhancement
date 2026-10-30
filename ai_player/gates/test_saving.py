"""UNIT PROOFS of R1 + R2 (the AI saves like a person, continues after a kill, and its memory survives; build spec
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-29-R1R2-BUILD-SPEC.md` section 4). Test side, offline, seconds.

    py -3.12 ai_player/gates/test_saving.py        (exit 0 = every test passed)

BUILD STAGE 1 (the EYES: E1, E2, E4-E7). Each guard has a FAULT half (the broken rule, shown to give the wrong answer)
and a CONTROL half (the fresh value, shown to give the right one), CLAUDE.md rule 6:
  EyesSaveTests          `eyes/screens.py` read_ui's start menu and save dialog (the task decides first, then the
                         callbacks: a stale callback never reads as input), the save's yes/no as its own kind, the CONTINUE
                         window's TIME, the save error's A wait, the page words (`skills/saving.py`), the host's printer-7
                         rule for the main menu's error pages, the host's play-time read (3 bytes at SaveBlock2 + 0x0E), and
                         the play time left out of `hands/dialogue.py` seen_now.
  HarnessInputRuleTests  `gates/play_harness.py` start_menu_input (E7): the 261-frame write is no "wait for a press",
                         the menu and the save's yes/no are, a stale callback is not; FAULT: the old rule with
                         `Task_ShowStartMenu` counted as input counts every frame of the write.
BUILD STAGE 2 (spec section 8 step 3: the memory file and the paths, offline):
  MemoryFileTests        `game_memory.py`: the header and its schema (a newer one refused byte-identical), a torn last line
                         ignored and acknowledged by the next session (a torn MIDDLE line refused), deltas and their
                         deletions, FULL_EVERY, the parent chain across a continue, the restore as of the save (never
                         newer), the D16 restore table (every goal-memory field classified; every KEEP field survives,
                         every RESET field starts afresh), the personality and battle parts, the frame base, the Pokemon
                         registry (L3 a-b), the `end` and `lost` lines with the losses a continue undoes, the TIME match
                         (the newest within a minute), and a save line that did not reach the file.
  PathsTests             `paths.py` AppPaths (beside the cartridge; AI_PLAYER_HOME), its launcher-side role in the purity
                         gate, and `gates/check_paths.py` (a planted literal FAILS; docstrings and comments PASS).
BUILD STAGE 3 (spec section 8 step 4: the skills and the policy, offline, on models of the game's screens):
  SaveSkillTests         `skills/saving.py` save_game on `SaveModel` (the START menu and the save dialog as
                         `src/start_menu.c` runs them): START only on a free screen; each question READ, and answered on the
                         look that shows ITS words (orchestrator ruling 3); OVERWRITE YES only on its own cart (D17); the
                         WARNING's pages turned, then NO; an unread question never YES; every NO backed out to a free screen;
                         no YES under COMMIT_FRAMES_NEEDED; no press through the write, which is bounded; the stamp from the
                         WHOLE SAVING page, the memory line written at the START of the write (D5), the play time checked
                         through it; "saved" only on the SAVED page; the save error read and closed; a stale page never
                         believed before a YES; an unwritten memory line ends the run; the budgets at 2x the measured widths
                         (orchestrator ruling 1).
  ContinueSkillTests     continue_game on `ContinueModel` (power-on to the arrival) with a real memory file: CONTINUE only
                         on a TIME match, never NEW GAME, the erased page read and a STOP with zero presses once the main
                         menu takes input, the corrupted page and the silent window both found by the TIME, the arrival
                         verified (map, tile, PID, species) on a HELD free screen, the newest record within a minute wins, and
                         the losses a continue undoes told.
  PolicyTests            `brain/saving.py` SavePolicy: the centre due (and its expiry), the big moments (ids only, D18), the
                         leader save once per approach to the gym, the 3-game-minute gap (a due it blocks is covered), no
                         save without the play time, frames or a free screen; the policy's state is the goal memory's.
The halves that need the play loop (the run ENDING on an unwritten save line, MAX_LOSSES across a continue, the `end` line
written by HandsBrain.play, the save goal and the end save) are `gates/test_goals.py` PlayLoopTests `test_r1_*` and
R1PlayTests (build stage 4).
BUILD STAGE 4 (spec section 8 step 5: the loop, the options, the launcher, the controller, the gates):
  LauncherContinueTests  `host/launcher.py` and `__main__.py` on temporary profile folders: `--continue` drops the .ss1 and
                         keeps the cart (refused without a memory file, a cart, the marker, or with a world file); D12 (a)'s
                         END CLASSES one row each (fail closed); `launches.jsonl` (D20); `--fresh`/`--state` archive the
                         memory, a no-flag start is refused beside one (D10); a newer file refused byte-identical; every run
                         told its memory file and its cart (D17); the options carry them.
  CensusSiteTests        the paths and records the call-site census found no test drove (each closes census sites with
                         `gates/revert_r1.py`'s mutants): the save's and the continue's other ends, the memory file's
                         refusals, the host's look through to the save wait, the text and the play time.
"""

from __future__ import annotations

import dataclasses
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
#: Where the framework lives. A revert copy of the package runs this file from a temporary folder and points here at the
#: real repo (as `gates/test_eyes.py`).
SUPPORT = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
BUILD_ROOT = SUPPORT / "sandbox-pokebot"
for entry in (str(REPO), str(BUILD_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from ai_player.eyes import screens as screens_module  # noqa: E402
from ai_player.eyes.observation import Observation, Progress, ScreenState  # noqa: E402
from ai_player.eyes.screens import (  # noqa: E402
    ERROR_PAGE_TASKS, PARAGRAPH, SAVE_DIALOG_CALLBACKS, SAVE_INPUT_CALLBACKS, SAVE_MENU_CALLBACKS, UI_TASKS, YES_NO,
    read_ui, save_dialog_wait,
)
from ai_player.hands.dialogue import seen_now  # noqa: E402
from ai_player.skills.saving import error_page, fold, save_page  # noqa: E402

#: `src/start_menu.c` MENU_ACTION_*: POKéDEX 0, POKéMON 1, BAG 2, PLAYER 4, SAVE 5, OPTION 6, EXIT 7 (the probe's fixture menu).
ACTIONS = [0, 1, 2, 4, 5, 6, 7]
SYMBOLS = BUILD_ROOT / "modules" / "data" / "symbols" / "pokeemerald.sym"


def task(data0: int = 0, data1: int = 0) -> bytes:
    """A task's 32 data bytes with data[0] and data[1] set (s16 little endian)."""
    return data0.to_bytes(2, "little", signed=True) + data1.to_bytes(2, "little", signed=True) + bytes(28)


def smenu(cursor: int) -> bytes:
    """`sMenu` (`src/menu.c` struct Menu): cursorPos @2 (s8), min @3, max @4."""
    return bytes([0, 0, cursor & 0xFF, 0, 1]) + bytes(7)


def start_raw(cursor: int = 4, **extra) -> dict:
    """What `host/eyes.py` _ui reads for the start menu (`sStartMenuCursorPos`, `sCurrentStartMenuActions`) plus `extra`."""
    return {"fading": False, "start_menu": {"cursor": cursor, "actions": list(ACTIONS)}, **extra}


def look(progress: Progress | None, frame: int = 100) -> Observation:
    screen = ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False, waits_for_button=False,
                         in_battle=False)
    return Observation(frame=frame, screen=screen, player=None, view=None, party=(), bag=None, progress=progress, battle=None,
                       last_battle_outcome=0, problems=(), cost_ms=0.1)


def progress(play_time: tuple[int, int] | None, money: int = 3000) -> Progress:
    return Progress(money=money, badges=(), dex_owned=1, dex_seen=1, owned_dex=(258,), flags=(), marks=(), play_time=play_time)


def framework_rom() -> None:
    """The framework's ROM and symbol table, for the tests that run the host's own reads (as `gates/test_eyes.py`)."""
    from modules.context import context
    from modules.game import set_rom
    from modules.profiles import load_profile_by_name

    if getattr(context, "rom", None) is None:
        profile = load_profile_by_name("ai-step0-fixture")
        context.profile = profile
        set_rom(profile.rom)


class SparseMemory:
    """A fake emulator memory: `regions` maps a start address to its bytes; a read outside every region is a test error
    (so a test sees exactly which reads the host makes: `reads` lists them)."""

    def __init__(self, regions: dict[int, bytes]) -> None:
        self.regions = {start: bytes(data) for start, data in regions.items()}
        self.reads: list[tuple[int, int]] = []

    def read_bytes(self, address: int, length: int) -> bytes:
        self.reads.append((address, length))
        for start, data in self.regions.items():
            if start <= address and address + length <= start + len(data):
                return data[address - start:address - start + length]
        raise AssertionError(f"read outside the fake memory: 0x{address:08X} (+{length})")


def symbol(name: str) -> int:
    from modules.game import get_symbol

    return get_symbol(name)[0]


class EyesSaveTests(unittest.TestCase):
    # ---------------------------------------------------------------- E1: the start menu, the task deciding first
    def test_start_menu_takes_input_under_task_show_start_menu(self) -> None:
        tasks = {"Task_ShowStartMenu": task(1)}
        ui = read_ui("OVERWORLD", tasks, start_raw(4, menu_callback="HandleStartMenuInput", menu=smenu(4)))
        self.assertEqual((ui.kind, ui.options, ui.cursor, ui.accepts_input),
                         ("start_menu", ("POKéDEX", "POKéMON", "BAG", "PLAYER", "SAVE", "OPTION", "EXIT"), 4, True))
        # FAULT (mutant S1): `Task_ShowStartMenu` not in UI_TASKS: the menu that takes input is not seen at all
        with mock.patch.dict(screens_module.UI_TASKS):
            del screens_module.UI_TASKS["Task_ShowStartMenu"]
            self.assertIsNone(read_ui("OVERWORLD", tasks, start_raw(4, menu_callback="HandleStartMenuInput")))

    def test_start_menu_building_takes_no_input(self) -> None:
        ui = read_ui("OVERWORLD", {"StartMenuTask": task(0)}, start_raw(0))
        self.assertEqual((ui.kind, ui.cursor, ui.accepts_input), ("start_menu", 0, False))
        self.assertIn("SAVE", ui.options)

    def test_a_stale_callback_never_reads_as_input(self) -> None:
        """Finding G1: neither callback is ever cleared (`src/start_menu.c:629-634`, `:1024-1028`, `:1070-1074`)."""
        stale_cases = [
            # a B close left HandleStartMenuInput; the menu is being built again
            ("StartMenuTask", {"StartMenuTask": task(0)}, start_raw(menu_callback="HandleStartMenuInput")),
            # a successful save left SaveCallback and an input save callback; Task_ShowStartMenu's first frame
            ("data0", {"Task_ShowStartMenu": task(0)},
             start_raw(menu_callback="SaveCallback", save_callback="SaveConfirmInputCallback", menu=smenu(0))),
            ("data0 menu", {"Task_ShowStartMenu": task(0)}, start_raw(menu_callback="HandleStartMenuInput")),
            # a NO left an input save callback; the two frames before InitSave sets a new one
            ("StartMenuSaveCallback", {"Task_ShowStartMenu": task(1)},
             start_raw(menu_callback="StartMenuSaveCallback", save_callback="SaveConfirmInputCallback", menu=smenu(0))),
            ("SaveStartCallback", {"Task_ShowStartMenu": task(1)},
             start_raw(menu_callback="SaveStartCallback", save_callback="SaveOverwriteInputCallback", menu=smenu(0))),
            # an item's callback (any other gMenuCallback): the menu, taking none
            ("other", {"Task_ShowStartMenu": task(1)}, start_raw(menu_callback=None)),
        ]
        for name, tasks, raw in stale_cases:
            ui = read_ui("OVERWORLD", tasks, raw)
            self.assertIsNotNone(ui, name)
            self.assertFalse(ui.accepts_input, f"{name}: a stale callback read as input: {ui}")
            self.assertNotEqual(ui.kind, "save_yes_no", name)
        # CONTROL: the fresh values read as accepting
        fresh_menu = read_ui("OVERWORLD", {"Task_ShowStartMenu": task(1)}, start_raw(menu_callback="HandleStartMenuInput"))
        self.assertTrue(fresh_menu.accepts_input)
        fresh_yes = read_ui("OVERWORLD", {"Task_ShowStartMenu": task(1)},
                            start_raw(menu_callback="SaveCallback", save_callback="SaveConfirmInputCallback", menu=smenu(0)))
        self.assertEqual((fresh_yes.kind, fresh_yes.accepts_input), ("save_yes_no", True))

    def test_the_host_reads_no_callback_while_the_task_has_not_set_it(self) -> None:
        """`host/eyes.py` _ui reads `gMenuCallback` only under `Task_ShowStartMenu` past data[0] 0, and `sSaveDialogCallback`
        only while `gMenuCallback` is SaveCallback (a read that is never made cannot be stale). CONTROL: past data[0] 0 with
        SaveCallback both are read."""
        from modules.context import context

        from ai_player.host.eyes import FrameworkEyes

        framework_rom()
        menu_at, save_at = symbol("gMenuCallback"), symbol("sSaveDialogCallback")
        memory = SparseMemory({
            menu_at: (symbol("SaveCallback") | 1).to_bytes(4, "little"),
            save_at: (symbol("SaveConfirmInputCallback") | 1).to_bytes(4, "little"),
            symbol("sNumStartMenuActions"): bytes([len(ACTIONS)]),
            symbol("sCurrentStartMenuActions"): bytes(ACTIONS) + bytes(9 - len(ACTIONS)),
            symbol("sStartMenuCursorPos"): bytes([4]),
            symbol("sMenu"): smenu(0),
        })
        with mock.patch.object(context, "emulator", memory, create=True):
            for tasks in ({"StartMenuTask": task(0)}, {"Task_ShowStartMenu": task(0)}):
                memory.reads.clear()
                ui = FrameworkEyes()._ui("OVERWORLD", tasks)
                read = {address for address, _ in memory.reads}
                self.assertNotIn(menu_at, read, tasks)
                self.assertNotIn(save_at, read, tasks)
                self.assertFalse(ui.accepts_input)
            memory.reads.clear()
            ui = FrameworkEyes()._ui("OVERWORLD", {"Task_ShowStartMenu": task(1)})
            read = {address for address, _ in memory.reads}
            self.assertIn(menu_at, read)
            self.assertIn(save_at, read)
            self.assertEqual((ui.kind, ui.cursor, ui.accepts_input), ("save_yes_no", 0, True))

    def test_save_question_is_a_save_yes_no_with_its_cursor(self) -> None:
        for callback in SAVE_INPUT_CALLBACKS:
            for cursor in (0, 1):
                ui = read_ui("OVERWORLD", {"Task_ShowStartMenu": task(1)},
                             start_raw(menu_callback="SaveCallback", save_callback=callback, menu=smenu(cursor)))
                self.assertEqual((ui.kind, ui.options, ui.cursor, ui.accepts_input), ("save_yes_no", YES_NO, cursor, True))

    def test_save_pages_are_a_save_dialog_that_takes_no_input(self) -> None:
        for callback in [c for c in SAVE_DIALOG_CALLBACKS if c not in SAVE_INPUT_CALLBACKS] + [None]:
            ui = read_ui("OVERWORLD", {"Task_ShowStartMenu": task(1)},
                         start_raw(menu_callback="SaveCallback", save_callback=callback, menu=smenu(0)))
            self.assertEqual((ui.kind, ui.accepts_input), ("save_dialog", False), callback)

    def test_a_scene_yes_no_is_not_the_save_yes_no(self) -> None:
        late = (5).to_bytes(2, "little").rjust(6, b"\0") + bytes(26)  # Task_HandleYesNoInput's tRight past 5
        scene = read_ui("OVERWORLD", {"Task_HandleYesNoInput": late}, {"fading": False, "menu": smenu(0)})
        save = read_ui("OVERWORLD", {"Task_ShowStartMenu": task(1)},
                       start_raw(menu_callback="SaveCallback", save_callback="SaveConfirmInputCallback", menu=smenu(0)))
        self.assertEqual(scene.kind, "yes_no")
        self.assertEqual(save.kind, "save_yes_no")
        self.assertNotEqual(scene.kind, save.kind)

    def test_a_fade_takes_the_save_yes_no_input_away(self) -> None:
        ui = read_ui("OVERWORLD", {"Task_ShowStartMenu": task(1)},
                     {**start_raw(menu_callback="SaveCallback", save_callback="SaveConfirmInputCallback", menu=smenu(0)),
                      "fading": True})
        self.assertEqual((ui.kind, ui.accepts_input), ("save_yes_no", False))

    def test_the_save_error_wait(self) -> None:
        """`src/start_menu.c` SaveErrorTimer: A HELD is taken only once `sSaveDialogTimer` is 0."""
        self.assertIsNotNone(save_dialog_wait("SaveReturnErrorCallback", 0))
        self.assertIsNone(save_dialog_wait("SaveReturnErrorCallback", 12))  # FAULT half: still counting down
        self.assertIsNone(save_dialog_wait("SaveReturnSuccessCallback", 0))  # the success page polls A only to hurry it
        self.assertIsNone(save_dialog_wait(None, 0))

    # ---------------------------------------------------------------- E6: the CONTINUE window's TIME
    def test_main_menu_carries_the_continue_windows_time(self) -> None:
        with_save = read_ui("MAIN_MENU", {"Task_HandleMainMenuInput": task(1, 0)}, {"save_time": (0, 17)})
        self.assertEqual((with_save.options[0], with_save.hours, with_save.minutes), ("CONTINUE", 0, 17))
        # CONTROL: no save (tMenuType 0): no TIME, whatever SaveBlock2 holds
        empty = read_ui("MAIN_MENU", {"Task_HandleMainMenuInput": task(0, 0)}, {"save_time": (0, 17)})
        self.assertEqual((empty.options, empty.hours, empty.minutes), (("NEW GAME", "OPTION"), None, None))

    # ---------------------------------------------------------------- E2: the pages' words
    def test_save_page_words(self) -> None:
        self.assertEqual(save_page("Would you like to save the game?"), "CONFIRM")
        self.assertEqual(save_page("There is already a saved file. Is it okay to overwrite it?"), "OVERWRITE")
        self.assertEqual(save_page("SAVING… DON’T TURN OFF THE POWER."), "SAVING")
        self.assertEqual(save_page("SAVING… DON’T TURN"), "printing")  # a prefix: still printing
        self.assertEqual(save_page("SAVING…"), "printing")
        self.assertEqual(save_page("NICK saved the game."), "SAVED")
        warning = (f"WARNING!{PARAGRAPH}There is a different game file that is already saved.{PARAGRAPH}If you save now, the "
                   f"other file’s adventure, including items and POKéMON, will be entirely lost.{PARAGRAPH}Are you sure you "
                   "want to save now and overwrite the other save file?")
        self.assertEqual(save_page(warning), "DIFFERENT")
        self.assertEqual(save_page("WARNING!"), "DIFFERENT")  # its first page, as it shows before the first A
        self.assertEqual(save_page(f"Save error.{PARAGRAPH}Please exchange the backup memory."), "ERROR")
        self.assertIn("other file's adventure", fold(warning))  # the apostrophe and the paragraph marks folded
        for other in (None, "", "Hello there!", "Would you like to save the game? Yes", "saved the game."):
            self.assertIsNone(save_page(other), other)

    def test_error_page_words(self) -> None:
        self.assertEqual(error_page("The save file is corrupted. The previous save file will be loaded."), "corrupted")
        self.assertEqual(error_page("The save file has been erased due to corruption or damage."), "erased")
        self.assertEqual(error_page(f"The internal battery has run dry. The game can be played.{PARAGRAPH}However, "
                                    "clock-based events will no longer occur."), "battery")
        self.assertIsNone(error_page("The save file is corrupted. The"))  # part printed: not yet a page
        self.assertIsNone(error_page(None))

    # ---------------------------------------------------------------- E4: the error pages from printer 7
    def test_the_error_window_is_read_from_printer_7(self) -> None:
        """`host/eyes.py` _text: while a main-menu error task runs, the page is printer 7's ROM string. FAULT (mutant S5): the
        old rule reads printer 0's stale pointer. CONTROL: without the task, the old rule stands (printer 0)."""
        from modules.context import context

        from ai_player.eyes.screens import encode_char
        from ai_player.host.eyes import FrameworkEyes

        def encode(text: str) -> bytes:
            return bytes(encode_char(c) for c in text) + b"\xff"

        framework_rom()
        corrupted = encode("The save file is corrupted.")
        stale = encode("Hello")
        rom = 0x085E8000
        strings = bytearray(b"\xff" * 0x400)  # ROM strings end with EOS (0xFF): the one before each string bounds it
        strings[0x200:0x200 + len(stale)] = stale
        strings[0x300:0x300 + len(corrupted)] = corrupted
        printers = bytearray(0x24 * 32)
        printers[0:4] = (rom + 0x200 + len(stale)).to_bytes(4, "little")  # printer 0: done, one past its EOS
        printers[7 * 0x24:7 * 0x24 + 4] = (rom + 0x300 + len(corrupted)).to_bytes(4, "little")  # printer 7: done
        memory = SparseMemory({rom: bytes(strings), symbol("sTextPrinters"): bytes(printers)})
        with mock.patch.object(context, "emulator", memory, create=True):
            for name in ERROR_PAGE_TASKS:
                self.assertEqual(FrameworkEyes._text(True, frozenset({name})), "The save file is corrupted.")
            # CONTROL: no error task: printer 0's message, as before R1 (the FAULT the old rule gives under the task)
            self.assertEqual(FrameworkEyes._text(True, frozenset({"Task_HandleMainMenuInput"})), "Hello")

    # ---------------------------------------------------------------- E5: the play time
    def test_the_play_time_is_hours_and_minutes_only(self) -> None:
        """`host/eyes.py` _play_time reads 3 bytes at SaveBlock2 + 0x0E (u16 hours, u8 minutes): never the seconds (0x11)
        or the VBlanks (0x12)."""
        from modules.context import context

        from ai_player.host import eyes as host_eyes

        framework_rom()
        sb2 = 0x02024A54
        block = bytearray(0x20)
        block[0x0E:0x13] = bytes([0x01, 0x00, 17, 47, 9])  # 1:17, 47 s, 9 VBlanks
        pointer_at = symbol("gSaveBlock2Ptr")
        memory = SparseMemory({pointer_at: sb2.to_bytes(4, "little"), sb2: bytes(block)})
        with mock.patch.object(context, "emulator", memory, create=True):
            self.assertEqual(host_eyes._play_time(), (1, 17))
        block_reads = [(address - sb2, length) for address, length in memory.reads if address != pointer_at]
        self.assertEqual(block_reads, [(0x0E, 3)])
        self.assertTrue(all(offset + length <= 0x11 for offset, length in block_reads), block_reads)

    def test_the_play_time_is_not_in_seen_now(self) -> None:
        """D18: a minute tick leaves `seen_now` equal. CONTROL: a money change does not."""
        before = look(progress((0, 17)))
        tick = look(progress((0, 18)), frame=101)
        self.assertEqual(seen_now(before), seen_now(tick))
        self.assertNotEqual(seen_now(before), seen_now(look(progress((0, 17), money=3100), frame=101)))
        self.assertEqual(seen_now(look(None)), seen_now(look(None, frame=101)))
        # FAULT half: the progress compared whole (before D18) sees the tick as a change
        self.assertNotEqual(before.progress, tick.progress)

    # ---------------------------------------------------------------- the names are the ROM's
    def test_every_save_name_is_a_rom_symbol(self) -> None:
        """Every function and task the rules NAME is in the symbol table the host resolves them with (a name the table lacks
        would silently never match). FAULT: a misspelt name is not found."""
        names = {line.split()[-1] for line in SYMBOLS.read_text(encoding="utf-8").splitlines() if line.strip()}
        wanted = set(SAVE_MENU_CALLBACKS + SAVE_DIALOG_CALLBACKS + ERROR_PAGE_TASKS) | {"StartMenuTask", "Task_ShowStartMenu",
                                                                                      "gMenuCallback", "sSaveDialogCallback",
                                                                                      "sSaveDialogTimer"}
        self.assertEqual(sorted(wanted - names), [])
        self.assertNotIn("SaveConfirmInputCalback", names)
        self.assertEqual(UI_TASKS["Task_ShowStartMenu"], "start_menu")


class HarnessInputRuleTests(unittest.TestCase):
    """E7 (finding F7): the test side's own rule of "the game waits for a press" (`gates/play_harness.py`)."""

    def setUp(self) -> None:
        from ai_player.gates import play_harness

        self.harness = play_harness

    def test_the_write_is_not_a_wait_for_a_press(self) -> None:
        rule = self.harness.start_menu_input
        write = [({"Task_ShowStartMenu"}, 1, "SaveCallback", None)] * 261  # SaveDoSaveCallback: not an input callback
        self.assertEqual(sum(1 for frame in write if rule(*frame) is not None), 0)
        # FAULT: the old rule with Task_ShowStartMenu counted as an input task counts every frame of the write
        old = self.harness.INPUT_TASKS + ("Task_ShowStartMenu",)
        self.assertEqual(sum(1 for tasks, *_ in write if any(name in tasks for name in old)), 261)

    def test_the_menu_and_the_save_question_are_waits(self) -> None:
        rule = self.harness.start_menu_input
        self.assertIsNotNone(rule({"Task_ShowStartMenu"}, 1, "HandleStartMenuInput", None))
        for callback in ("SaveConfirmInputCallback", "SaveOverwriteInputCallback"):
            self.assertIsNotNone(rule({"Task_ShowStartMenu"}, 1, "SaveCallback", callback))

    def test_a_stale_callback_is_no_wait(self) -> None:
        rule = self.harness.start_menu_input
        self.assertIsNone(rule({"StartMenuTask"}, None, "HandleStartMenuInput", None))  # the menu being built
        self.assertIsNone(rule({"Task_ShowStartMenu"}, 0, "HandleStartMenuInput", None))  # its first frame
        self.assertIsNone(rule(set(), None, "SaveCallback", "SaveConfirmInputCallback"))  # after the task is gone
        self.assertIsNone(rule({"Task_ShowStartMenu"}, 1, "StartMenuSaveCallback", None))

    def test_start_menu_task_is_no_longer_an_input_task(self) -> None:
        self.assertNotIn("StartMenuTask", self.harness.INPUT_TASKS)
        self.assertNotIn("Task_ShowStartMenu", self.harness.INPUT_TASKS)


# ==================================================================== BUILD STAGE 2: the memory file and the paths
from ai_player import game_memory as gm  # noqa: E402
from ai_player.brain.battle import BattleMind  # noqa: E402
from ai_player.brain.goals import _Memory  # noqa: E402
from ai_player.eyes.observation import MonSummary, PlayerState  # noqa: E402
from ai_player.game_memory import (  # noqa: E402
    FULL_EVERY, GOAL_IN_WORLD, GOAL_KEEP, GOAL_RESET, R1_NEW_FIELDS, ROLES, SCHEMA_VERSION, MemoryFileError, MemoryWriter,
    MonRegistry, apply_delta, battle_part, build_payload, decode_value, diff, encode_value, end_line, goals_part, personality_part,
    read_book, restore, restore_battle, restore_goals, restore_personality,
)
from ai_player.personality import DRIFT_EVERY, PersonalityState  # noqa: E402
from ai_player.world.memory import WorldMemory  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
#: Three world-memory snapshots RECORDED by a development run on route101_south (maps 0:9 + 1:4, then 0:16 added).
WORLDS = [json.loads(line) for line in (FIXTURES / "route101_south.world.jsonl").read_text(encoding="utf-8").splitlines()
          if line.strip()]
HEADER = {"game": "ai-test|2026-10-29T10:00:00", "identity": {"seed": 1, "personality": "Story", "favourite": "ZIGZAGOON",
                                                             "starter": "TREECKO", "gender": "BOY", "name": "AI"}}
WHERE = {"map": "ROUTE_101", "tile": [5, 6]}
PARTY = [{"pid": "0000abcd", "species": "TREECKO"}]


def session(how: str = "new game", **extra) -> dict:
    return {"how": how, "host": "harness", "run_dir": "run", "cart": "empty" if how == "new game" else "continued",
            "started": "2026-10-29T10:00:00", **extra}


def world_frames(world: dict) -> int:
    """The largest frame stamp a recorded world memory holds (its map changes and closed doors)."""
    stamps = [int(t[0]) for t in world.get("transitions") or []]
    for memory in (world.get("maps") or {}).values():
        stamps += [int(info.get("frame", 0)) for info in (memory.get("closed") or {}).values() if isinstance(info, dict)]
    return max(stamps, default=0)


#: A frame later than every stamp the recorded worlds hold (a save line's frame is its look's: never before its payload).
BASE_FRAME = max(world_frames(world) for world in WORLDS) + 100


def payload_of(world: dict, talked=(), losses: int = 0, mons: dict | None = None) -> dict:
    memory = _Memory(talked=set(talked))
    return build_payload(world=world, goals=goals_part(memory),
                         personality={"base": "Story", "favourite": "ZIGZAGOON", "history": [], "draws": 0},
                         battle={"wishes": {}, "met": {}, "wild_met": 0}, mons=mons or {}, losses=losses)


def write_save(writer: MemoryWriter, n: int, payload: dict, play_time=None):
    return writer.write_save(play_time=play_time or (0, 17 + 3 * n), frame=BASE_FRAME + 1000 * n, where=WHERE, party=PARTY,
                             why="a test save", payload=payload)


def mon(pid: int, species: str, egg: bool = False) -> MonSummary:
    return MonSummary(slot=0, species=species, dex=252, level=5, hp=20, max_hp=20, status="", types=("GRASS",), moves=(),
                      pid=pid, ot_id=1, is_egg=egg)


def party_look(party, frame: int = 500, map_const: str = "ROUTE_101", tile=(5, 6), play_time=(0, 17)) -> Observation:
    player = PlayerState(map_group=0, map_number=16, map_name="ROUTE 101", map_const=map_const, x=tile[0], y=tile[1],
                         facing="down", movement="walking", elevation=3, avatar_flags=0, trainer_id=1)
    return dataclasses.replace(look(progress(play_time), frame), party=tuple(party), player=player)


def rich_memory() -> _Memory:
    """A goal-manager memory with EVERY field away from its default (`test_each_keep_field_survives_the_restore` checks
    that it is, so a new field not filled here fails there)."""
    return _Memory(
        talked={"0:9|1"}, tried_items={"0:16|3,4"}, item_tries={"0:16|3,4": 2}, catch_maps={"ROUTE_101"},
        chat_drawn={"0:9|2"}, fails={"go:x": 1}, cooldown={"go:x": 20}, decisions=5, asked_rounds={"ch1_lab": 1},
        landmarks={("0:9", (1, 2)): "mart"}, fight_prep={"ch4_roxanne": {"steps": 10, "sessions": 1, "ready": False}},
        sightings={("MAY", "ROUTE_103"): (3, 4, 1200)}, pages={"Hello there!": 500}, looked={"0:9"}, detoured={"0:9|ch1_lab"},
        seen_levels={"ROUTE_102": 5}, last_map="ROUTE_101", no_balls={"OLDALE_TOWN_MART": 2}, home_heals=1,
        scene_walls={"ch1_lab": {"0:16": {(5, 6), (5, 7)}}}, known_before={"0:9"}, aside_from={"go:x": 5}, passed_new=1,
        spent={"story": 5, "errand": 1, "curious": 2}, again={"0:9|ch1_lab": 1}, break_stops={"0:9|ch1_lab"},
        curious_since=4, curious_row=2, exhausted={"0:9|ch1_lab": "nothing new"},
        blocked={"ch2_wally": {"0:9": {(1, 2): "someone kept standing there"}}}, idle={"goals": 1, "frames": 9},
        center_looked={"0:2"}, explored={"0:2"}, decided_with_party=True, danger_again={"heal:x": 1},
        spoke={"0:9|3"}, hearing=True, lost_end=("ch1_lab", 3),
        saved_for={"ch4_roxanne": 4100}, last_save={"id": 2, "play_time": [0, 21], "frame": 3900, "why": "a test save"},
        save_due={"kind": "moment", "why": "ch1_lab", "map": None, "milestone": "ch1_lab", "entered": None, "told": None},
    )


class MemoryFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ai_memory_")
        self.dir = Path(self.tmp.name)
        self.path = self.dir / "memory.jsonl"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def lines(self) -> list[dict]:
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def new_writer(self) -> MemoryWriter:
        return MemoryWriter(self.path, None, header=HEADER, session=session())

    # ---------------------------------------------------------------- the header, the schema, the lines
    def test_the_header_is_the_first_line_with_schema_1(self) -> None:
        writer = self.new_writer()
        # no save, no file: a battle lost before the first save writes nothing
        self.assertIsNone(writer.write_lost(party_look([mon(0xABCD, "TREECKO")])))
        self.assertFalse(self.path.exists())
        result = write_save(writer, 1, payload_of(WORLDS[0]))
        self.assertTrue(result.reached)
        lines = self.lines()
        self.assertEqual([line["kind"] for line in lines], ["header", "session", "save"])
        self.assertEqual((lines[0]["schema_version"], SCHEMA_VERSION), (1, 1))
        self.assertEqual(lines[0]["identity"], HEADER["identity"])
        self.assertEqual((lines[1]["n"], lines[1]["how"], lines[1]["cart"]), (1, "new game", "empty"))
        self.assertEqual((lines[2]["id"], lines[2]["parent"], lines[2]["full"]), (1, None, True))
        self.assertEqual(lines[2]["play_time"], [0, 20])
        # every line is one ASCII line (a cut can never fall inside a multi-byte character)
        self.assertTrue(self.path.read_bytes().isascii())

    def test_a_newer_schema_is_refused_byte_identical(self) -> None:
        newer = (json.dumps({"kind": "header", "schema_version": SCHEMA_VERSION + 1, "game": "x", "identity": {}}) + "\n"
                 + '{"kind": "something a newer program writes"}\nnot even json\n')
        self.path.write_text(newer, encoding="utf-8")
        before = self.path.read_bytes()
        with self.assertRaises(MemoryFileError) as caught:
            read_book(self.path)
        self.assertEqual(caught.exception.kind, "newer")  # decided by the header, before any other line is judged
        self.assertEqual(self.path.read_bytes(), before)
        # CONTROL (mutant S24: the comparison is what refuses): the same file read by a program of that schema is no
        # "newer" refusal
        with mock.patch.object(gm, "SCHEMA_VERSION", SCHEMA_VERSION + 1):
            with self.assertRaises(MemoryFileError) as caught:
                read_book(self.path)
            self.assertEqual(caught.exception.kind, "unreadable")
        self.path.unlink()
        write_save(self.new_writer(), 1, payload_of(WORLDS[0]))  # a schema-1 file: read
        self.assertEqual(len(read_book(self.path).saves()), 1)

    def test_no_header_is_refused(self) -> None:
        self.path.write_text(json.dumps(session() | {"kind": "session", "n": 1}) + "\n", encoding="utf-8")
        with self.assertRaises(MemoryFileError) as caught:
            read_book(self.path)
        self.assertEqual(caught.exception.kind, "no_header")
        self.path.write_text("", encoding="utf-8")
        with self.assertRaises(MemoryFileError) as caught:
            read_book(self.path)
        self.assertEqual(caught.exception.kind, "no_header")
        self.assertIsNone(read_book(self.dir / "absent.jsonl"))  # no file: a game with no save yet

    def test_a_torn_last_line_is_ignored(self) -> None:
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[0]))
        write_save(writer, 2, payload_of(WORLDS[1]))
        good = self.path.read_text(encoding="utf-8")
        fragment = '{"kind":"save","id":3,"parent":2,"full":fal'
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(fragment)
        book = read_book(self.path)
        self.assertEqual((book.torn, book.ends_clean, [s["id"] for s in book.saves()]), (fragment, False, [1, 2]))
        # FAULT (mutant S25): a torn MIDDLE line (one more line after it, nothing acknowledging it) refuses the file
        self.path.write_text(good + fragment + "\n" + json.dumps(end_line(1, "done: x", False, 1)) + "\n", encoding="utf-8")
        with self.assertRaises(MemoryFileError) as caught:
            read_book(self.path)
        self.assertEqual(caught.exception.kind, "unreadable")

    def test_a_non_ascii_middle_line_is_refused(self) -> None:
        """(R1 + R2 follow-up, spec D4: the review's N-4) Every line is written with `ensure_ascii=True`, so a non-ASCII
        character in a line is a corrupted byte. FAULT (mutant M14): a `0xFF` byte inside a middle line's string (it
        decodes to U+FFFD, the JSON still parses, and the file used to be ACCEPTED with changed content) -> refused
        "unreadable"; a valid UTF-8 `é` in a middle line -> refused; a non-ASCII header -> "no_header". CONTROL: the clean
        file reads; a `0xFF` in a torn LAST line is ignored (`torn` set, D6), and once a continue's writer acknowledges
        it the next read accepts the file."""
        write_save(self.new_writer(), 1, payload_of(WORLDS[0]))
        clean = self.path.read_bytes()
        # the session line's free-text `run_dir` (a field no line check judges, so only the ASCII check can refuse it)
        free = b'"run_dir":"run"'
        self.assertEqual(clean.count(free), 1)
        self.assertEqual([line["kind"] for line in read_book(self.path).lines], ["header", "session", "save"])  # CONTROL
        for label, corrupted, kind in (
                ("a 0xFF byte in the middle line", clean.replace(free, b'"run_dir":"r\xffn"'), "unreadable"),
                ("a UTF-8 e-acute in the middle line", clean.replace(free, '"run_dir":"rén"'.encode("utf-8")), "unreadable"),
                # (the header's own kind kept: only its game string carries the byte, so the old code read the header)
                ("a non-ASCII header", clean.replace(b"ai-test|", b"ai-t\xffst|", 1), "no_header")):
            with self.subTest(label):
                self.path.write_bytes(corrupted)
                with self.assertRaises(MemoryFileError) as caught:
                    read_book(self.path)
                self.assertEqual(caught.exception.kind, kind)
        # CONTROL: a 0xFF byte in a torn LAST line is ignored, then acknowledged by the next session's writer
        fragment = b'{"kind":"lost","fr\xffme":12'
        self.path.write_bytes(clean + fragment)
        book = read_book(self.path)
        self.assertIsNotNone(book.torn)
        self.assertEqual([s["id"] for s in book.saves()], [1])
        follow = MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=1))
        self.assertTrue(follow.write_session(verified=True, restored_maps=["0:9"]))
        again = read_book(self.path)
        self.assertEqual((again.torn, again.acknowledged), (None, 1))
        self.assertEqual([s["n"] for s in again.sessions()], [1, 2])

    def test_the_next_session_ends_and_acknowledges_a_torn_line(self) -> None:
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[0]))
        fragment = '{"kind":"lost","frame":12'
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(fragment)
        book = read_book(self.path)
        follow = MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=1))
        self.assertTrue(follow.write_session(verified=True, restored_maps=["0:9"]))
        self.assertTrue(write_save(follow, 2, payload_of(WORLDS[1])).reached)
        again = read_book(self.path)
        self.assertEqual((again.torn, again.acknowledged, again.ends_clean), (None, 1, True))
        self.assertEqual([s["id"] for s in again.saves()], [1, 2])
        self.assertEqual([s["n"] for s in again.sessions()], [1, 2])
        # FAULT: appending after the cut line WITHOUT ending and acknowledging it joins the two into one broken line,
        # and the file is refused from then on
        self.tearDown()
        self.setUp()
        write_save(self.new_writer(), 1, payload_of(WORLDS[0]))
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(fragment)
        careless = MemoryWriter(self.path, read_book(self.path), header=None, session=session("continue", continued_from=1))
        careless.mend, careless.torn = False, None
        careless.write_session()
        write_save(careless, 2, payload_of(WORLDS[1]))
        with self.assertRaises(MemoryFileError) as caught:
            read_book(self.path)
        self.assertEqual(caught.exception.kind, "unreadable")
        # a cut line already ENDED (a session killed between ending it and acknowledging it): acknowledged, no blank line
        self.tearDown()
        self.setUp()
        write_save(self.new_writer(), 1, payload_of(WORLDS[0]))
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(fragment + "\n")
        book = read_book(self.path)
        self.assertEqual((book.torn, book.ends_clean), (fragment, True))
        MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=1)).write_session()
        again = read_book(self.path)
        self.assertEqual((again.torn, again.acknowledged, [line["kind"] for line in again.lines]),
                         (None, 1, ["header", "session", "save", "session"]))
        # a complete last line that only lost its newline is kept, and ended before the next line
        self.tearDown()
        self.setUp()
        write_save(self.new_writer(), 1, payload_of(WORLDS[0]))
        self.path.write_bytes(self.path.read_bytes().rstrip(b"\r\n"))
        book = read_book(self.path)
        self.assertEqual((book.torn, book.ends_clean, len(book.saves())), (None, False, 1))
        MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=1)).write_session()
        self.assertEqual([line["kind"] for line in read_book(self.path).lines], ["header", "session", "save", "session"])

    # ---------------------------------------------------------------- deltas and the parent chain
    def test_delta_round_trip(self) -> None:
        """apply(parent, diff(parent, child)) == child, on the RECORDED world snapshots and on random goal memories."""
        payloads = [payload_of(world, talked=[f"0:9|{i}"], losses=i) for i, world in enumerate(WORLDS)]
        for parent in payloads:
            for child in payloads:
                self.assertEqual(apply_delta(parent, diff(parent, child)), child)
        rng = random.Random(29)
        for _ in range(60):
            a = _Memory(talked={f"p{rng.randrange(9)}" for _ in range(rng.randrange(5))},
                        item_tries={f"m|{rng.randrange(5)}": rng.randrange(3) for _ in range(rng.randrange(4))},
                        sightings={("MAY", f"R{rng.randrange(3)}"): (rng.randrange(9), 1, 2) for _ in range(rng.randrange(3))})
            b = _Memory(talked={f"p{rng.randrange(9)}" for _ in range(rng.randrange(5))},
                        item_tries={f"m|{rng.randrange(5)}": rng.randrange(3) for _ in range(rng.randrange(4))},
                        sightings={("MAY", f"R{rng.randrange(3)}"): (rng.randrange(9), 1, 2) for _ in range(rng.randrange(3))})
            pa = payload_of(WORLDS[rng.randrange(3)], losses=rng.randrange(3)) | {"goals": goals_part(a)}
            pb = payload_of(WORLDS[rng.randrange(3)], losses=rng.randrange(3)) | {"goals": goals_part(b)}
            self.assertEqual(apply_delta(pa, diff(pa, pb)), pb)
        # a delta's paths are at most a section and two keys
        delta = diff(payloads[0], payloads[1])
        self.assertTrue(delta["set"] and all(len(path) <= 3 for path, _ in delta["set"]))
        self.assertIn(["world", "maps", "0:16"], [path for path, _ in delta["set"]])

    def test_a_delta_keeps_its_deletions(self) -> None:
        parent, child = payload_of(WORLDS[1]), payload_of(WORLDS[0])  # WORLDS[1] knows map 0:16; WORLDS[0] does not
        self.assertIn("0:16", parent["world"]["maps"])
        delta = diff(parent, child)
        self.assertIn(["world", "maps", "0:16"], delta["del"])
        self.assertNotIn("0:16", apply_delta(parent, delta)["world"]["maps"])
        # FAULT (mutant S26): a delta that drops its deletions rebuilds a memory that still knows the map
        self.assertIn("0:16", apply_delta(parent, {"set": delta["set"], "del": []})["world"]["maps"])
        # and a deletion of a key the parent does not hold is a broken chain, never ignored
        with self.assertRaises(MemoryFileError):
            apply_delta(child, {"set": [], "del": [["world", "maps", "0:16"]]})

    def test_full_every_8(self) -> None:
        writer = self.new_writer()
        written = {}
        for n in range(1, 19):
            written[n] = payload_of(WORLDS[n % 3], talked=[f"0:9|{i}" for i in range(n)], losses=n)
            self.assertTrue(write_save(writer, n, written[n]).reached)
        book = read_book(self.path)
        self.assertEqual([s["id"] for s in book.saves() if s["full"]], [1, 1 + FULL_EVERY + 1])
        self.assertEqual(FULL_EVERY, 8)
        for n, payload in written.items():
            self.assertEqual(book.rebuild(n), payload, f"save {n}")

    def test_rebuild_follows_the_parent_across_a_continue(self) -> None:
        writer = self.new_writer()
        p1, p2, p3 = (payload_of(WORLDS[0], talked=["a"]), payload_of(WORLDS[1], talked=["a", "b"]),
                      payload_of(WORLDS[0], talked=["a", "c"], losses=1))
        write_save(writer, 1, p1)
        write_save(writer, 2, p2)  # S2: abandoned (the game continued S1)
        follow = MemoryWriter(self.path, read_book(self.path), header=None, session=session("continue", continued_from=1))
        follow.write_session(verified=True)
        write_save(follow, 3, p3)
        book = read_book(self.path)
        s3 = book.save(3)
        self.assertEqual((s3["parent"], s3["full"]), (1, False))
        self.assertEqual(book.rebuild(3), p3)
        self.assertEqual(book.rebuild(2), p2)  # the abandoned line is still readable, never on a chain again
        # FAULT (mutant S28): S3's delta applied to the NEWEST earlier line (S2) instead of its parent rebuilds a memory
        # that knows what only the abandoned branch saw
        wrong = apply_delta(book.rebuild(2), s3["memory"])
        self.assertNotEqual(wrong, p3)
        self.assertIn("0:16", wrong["world"]["maps"])

    # ---------------------------------------------------------------- the restore (D16)
    def test_the_restore_is_not_newer_than_the_save(self) -> None:
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[0], losses=0))
        write_save(writer, 2, payload_of(WORLDS[1], losses=1))
        book = read_book(self.path)
        first = restore(book, 1)
        self.assertEqual(first.restored_maps, ["0:9", "1:4"])
        self.assertEqual(first.losses, 0)
        self.assertNotIn("memory", first.save)
        # the restored world is a real WorldMemory again, equal to the recorded snapshot
        self.assertEqual(WorldMemory.from_dict(first.world).to_dict(), WorldMemory.from_dict(WORLDS[0]).to_dict())
        # CONTROL (the newest save, R1-M's rule): it knows 0:16, so the check above can see the difference
        self.assertIn("0:16", restore(book, 2).restored_maps)

    def test_the_restore_table_is_the_specs(self) -> None:
        """D16's table, as the spec lists it (section 3 (c)): moving a field between KEEP and RESET is a design change,
        never a silent edit (mutant S31)."""
        self.assertEqual(set(GOAL_KEEP), {
            "talked", "tried_items", "item_tries", "catch_maps", "chat_drawn", "asked_rounds", "fight_prep", "sightings",
            "pages", "looked", "detoured", "seen_levels", "last_map", "no_balls", "home_heals", "scene_walls", "again",
            "break_stops", "exhausted", "blocked", "center_looked", "explored", "saved_for", "last_save"})
        self.assertEqual(set(GOAL_RESET), {
            "fails", "cooldown", "decisions", "known_before", "aside_from", "passed_new", "spent", "curious_since",
            "curious_row", "idle", "decided_with_party", "danger_again", "hearing", "lost_end", "save_due"})
        self.assertEqual(set(GOAL_IN_WORLD), {"landmarks", "spoke"})
        self.assertEqual(gm.PERSONALITY_FIELDS, ("base", "favourite", "history", "draws"))
        self.assertEqual(gm.BATTLE_FIELDS, ("wishes", "met", "wild_met"))

    def test_every_goal_memory_field_is_classified(self) -> None:
        names = {f.name for f in dataclasses.fields(_Memory)}
        tables = set(GOAL_KEEP) | set(GOAL_RESET) | set(GOAL_IN_WORLD)
        self.assertEqual(names - tables, set(), "a goal-memory field in no restore table")
        self.assertEqual(tables - names, set(R1_NEW_FIELDS) - names, "a table names a field the memory does not have")
        self.assertFalse(set(GOAL_KEEP) & set(GOAL_RESET) or set(GOAL_KEEP) & set(GOAL_IN_WORLD)
                         or set(GOAL_RESET) & set(GOAL_IN_WORLD))
        goals_part(_Memory())  # CONTROL: today's memory is fully classified

        @dataclasses.dataclass
        class Wider(_Memory):
            something_new: int = 0

        with self.assertRaises(MemoryFileError) as caught:  # FAULT: a field added unclassified
            goals_part(Wider())
        self.assertEqual(caught.exception.kind, "unclassified")
        self.assertIn("something_new", str(caught.exception))

    def test_each_keep_field_survives_the_restore(self) -> None:
        rich, fresh = rich_memory(), _Memory()
        names = {f.name for f in dataclasses.fields(_Memory)}
        for name in names:  # the test is vacuous for any field left at its default
            self.assertNotEqual(getattr(rich, name), getattr(fresh, name), f"rich_memory leaves {name} at its default")
        payload = payload_of(WORLDS[0]) | {"goals": goals_part(rich)}
        write_save(self.new_writer(), 1, payload)
        restored = restore_goals(_Memory(), restore(read_book(self.path), 1).goals)
        for name in sorted(names & set(GOAL_KEEP)):
            self.assertEqual(getattr(restored, name), getattr(rich, name), f"KEEP field {name}")
        for name in sorted(names & (set(GOAL_RESET) | set(GOAL_IN_WORLD))):
            self.assertEqual(getattr(restored, name), getattr(fresh, name), f"{name} starts afresh")
        # FAULT (mutant S31): one KEEP field left out of the restore is not what the save remembered
        goals = {key: value for key, value in goals_part(rich).items() if key != "talked"}
        self.assertNotEqual(restore_goals(_Memory(), goals).talked, rich.talked)

    def test_goal_memory_round_trip(self) -> None:
        rich = rich_memory()
        part = json.loads(json.dumps(goals_part(rich)))
        for name, value in part.items():
            self.assertEqual(decode_value(value), getattr(rich, name), name)
        self.assertEqual(decode_value(encode_value({"$set": 1, "a": 2})), {"$set": 1, "a": 2})  # a key that is a tag stays a key
        self.assertEqual(decode_value(encode_value({(1, 2): {3, 4}})), {(1, 2): {3, 4}})
        with self.assertRaises(MemoryFileError):
            encode_value(object())

    def test_the_personality_and_the_battle_mind(self) -> None:
        state = PersonalityState("Story", random.Random(1))
        state.favourite, state.draws, state.history = "ZIGZAGOON", 3, [{"step": 400, "kind": "drift", "active": "Trainer",
                                                                         "line": "it drifts"}]
        state.active, state.drift_until, state.next_draw = "Trainer", 900, 1200
        mind = BattleMind("Story", random.Random(2))
        mind.wishes, mind.met, mind.wild_met = {"ZIGZAGOON": True, "WURMPLE": False}, {"ZIGZAGOON": 2}, 3
        self.assertEqual(tuple(personality_part(state)), gm.PERSONALITY_FIELDS)
        self.assertEqual(tuple(battle_part(mind)), gm.BATTLE_FIELDS)
        payload = payload_of(WORLDS[0]) | {"personality": personality_part(state), "battle": battle_part(mind)}
        write_save(self.new_writer(), 1, payload)
        restored = restore(read_book(self.path), 1)
        after, again = PersonalityState("Story", random.Random(3)), BattleMind("Story", random.Random(4))
        after.active, after.drift_until, after.next_draw = "Catcher", 700, 800  # whatever it held, the drift starts afresh
        restore_personality(after, restored.personality)
        restore_battle(again, restored.battle)
        self.assertEqual((after.favourite, after.draws, after.history), (state.favourite, 3, state.history))
        self.assertEqual((after.active, after.drift_until, after.next_draw), ("Story", None, DRIFT_EVERY))
        self.assertEqual((again.wishes, again.met, again.wild_met), (mind.wishes, mind.met, 3))
        with self.assertRaises(MemoryFileError):  # another personality's save is never taken on
            restore_personality(PersonalityState("Trainer", random.Random(5)), restored.personality)

    def test_the_frame_base_exceeds_every_stamp(self) -> None:
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[2]))
        writer.write_lost(party_look([mon(0xABCD, "TREECKO")], frame=BASE_FRAME + 1500))
        writer.write_end("stopped: not finished", False, BASE_FRAME + 1700)
        book = read_book(self.path)
        base = book.frame_base()
        self.assertEqual(base, BASE_FRAME + 1701)
        stamps = [line["frame"] for line in book.lines if "frame" in line] + [world_frames(restore(book, 1).world)]
        self.assertTrue(stamps and all(base > stamp for stamp in stamps))
        self.assertGreater(world_frames(WORLDS[2]), 0)  # the recorded world does carry stamps: the check is not vacuous
        # a later session's base never falls below an earlier session's
        follow = MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=1,
                                                                            frame_base=base + 50_000))
        follow.write_session()
        self.assertEqual(read_book(self.path).frame_base(), base + 50_000)

    # ---------------------------------------------------------------- L3 (a)-(b): the registry
    def test_mons_by_pid_and_species_with_roles(self) -> None:
        registry = MonRegistry()
        self.assertEqual(registry.observe(party_look([mon(0x1, "TREECKO")], frame=10)), ["00000001"])
        registry.observe(party_look([mon(0x1, "TREECKO"), mon(0x2, "ZIGZAGOON")], frame=20), caught=True)
        registry.observe(party_look([mon(0x1, "TREECKO"), mon(0x2, "ZIGZAGOON"), mon(0x3, "?", egg=True)], frame=30))
        registry.observe(party_look([mon(0x2, "ZIGZAGOON"), mon(0x1, "GROVYLE"), mon(0x4, "WINGULL")], frame=40))
        entries = registry.to_dict()
        self.assertEqual(sorted(entries), ["00000001", "00000002", "00000004"])  # by PID, eggs not registered
        self.assertEqual([entries[k]["how"] for k in sorted(entries)], ["starter", "caught", "joined"])
        self.assertEqual((entries["00000001"]["species"], entries["00000001"]["species_seen"]), ("GROVYLE",
                                                                                                ["TREECKO", "GROVYLE"]))
        self.assertEqual(entries["00000001"]["frame"], 10)  # first seen, by its PID: a new slot is no new Pokemon
        self.assertEqual(set(entries["00000001"]["first"]), {"map", "tile"})  # never x, y or state (D15)
        self.assertEqual(entries["00000001"]["play_time"], [0, 17])
        registry.add_role(0x1, "lead", "ROXANNE", "ROXANNE")
        self.assertEqual(registry.entries["00000001"]["roles"], [{"role": "lead", "for": "ROXANNE", "until": "ROXANNE"}])
        with self.assertRaises(MemoryFileError):
            registry.add_role(0x1, "favourite")  # not a role of ROLES
        self.assertEqual(ROLES, ("lead", "hm_carrier", "counter", "catch_helper", "spare"))
        with self.assertRaises(MemoryFileError):
            MonRegistry({"00000009": {"roles": [{"role": "boss", "for": None, "until": None}]}})
        # through the file and back
        write_save(self.new_writer(), 1, payload_of(WORLDS[0], mons=registry.to_dict()))
        self.assertEqual(restore(read_book(self.path), 1).mons.to_dict(), registry.to_dict())

    # ---------------------------------------------------------------- end, lost, the losses a continue undoes
    def test_the_end_line_says_chosen_budget_and_at_save(self) -> None:
        cases = {"done: ch1_pokedex": (True, False), "stuck: no way on": (True, False),
                 "stopped: not finished within 3000 frames": (False, True), "play: done: x": (True, False),
                 "3 battles lost (MAX_LOSSES 3)": (False, False)}
        for reason, (chosen, budget) in cases.items():
            line = end_line(2, reason, True, 99)
            self.assertEqual((line["chosen"], line["budget"], line["at_save"], line["session"]), (chosen, budget, True, 2),
                             reason)
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[0]))
        self.assertTrue(writer.write_end("done: ch1_pokedex", True, BASE_FRAME + 5000))
        book = read_book(self.path)
        self.assertEqual(book.end_of(1)["at_save"], True)
        self.assertIsNone(book.end_of(2))

    def test_a_lost_line_per_loss_and_the_losses_a_continue_undoes(self) -> None:
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[0], losses=0))
        self.assertTrue(writer.write_lost(party_look([mon(1, "TREECKO")], frame=BASE_FRAME + 1100)))
        write_save(writer, 2, payload_of(WORLDS[1], losses=1))
        writer.write_lost(party_look([mon(1, "TREECKO")], frame=BASE_FRAME + 2100))
        writer.write_lost(party_look([mon(1, "TREECKO")], frame=BASE_FRAME + 2200))
        book = read_book(self.path)
        lost = [line for line in book.lines if line["kind"] == "lost"]
        self.assertEqual([line["after_save"] for line in lost], [1, 2, 2])
        self.assertEqual(set(lost[0]["where"]), {"map", "tile"})
        self.assertEqual((len(book.undone_losses(2)), len(book.undone_losses(1))), (2, 3))
        # a continue from S1 undid all three; one more loss after it is the only one the NEXT continue from S1 undoes
        follow = MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=1, losses=0))
        follow.write_session()
        follow.write_lost(party_look([mon(1, "TREECKO")], frame=BASE_FRAME + 9000))
        book = read_book(self.path)
        self.assertEqual(len(book.undone_losses(1)), 1)
        self.assertIsNone(book.undone_losses(2))  # S2 is no longer in the live history
        # FAULT: counting every lost line after S1 in file order counts the undone ones again
        after = [i for i, line in enumerate(book.lines) if line["kind"] == "save" and line["id"] == 1][0]
        self.assertEqual(sum(1 for line in book.lines[after:] if line["kind"] == "lost"), 4)

    def test_the_loss_count_is_restored(self) -> None:
        write_save(self.new_writer(), 1, payload_of(WORLDS[0], losses=2))
        self.assertEqual(restore(read_book(self.path), 1).losses, 2)  # MAX_LOSSES across a continue: the loop (stage 4)

    def test_one_minute_tolerance_and_the_newest_wins(self) -> None:
        writer = self.new_writer()
        write_save(writer, 1, payload_of(WORLDS[0]), play_time=(0, 17))
        write_save(writer, 2, payload_of(WORLDS[1]), play_time=(0, 21))  # abandoned below
        follow = MemoryWriter(self.path, read_book(self.path), header=None, session=session("continue", continued_from=1))
        follow.write_session()
        write_save(follow, 3, payload_of(WORLDS[2]), play_time=(0, 21))
        book = read_book(self.path)
        self.assertEqual(book.match_time((0, 21))["id"], 3)  # the newer line, later in the file, wins over the abandoned S2
        self.assertEqual(book.match_time((0, 22))["id"], 3)
        self.assertEqual(book.match_time((0, 18))["id"], 1)
        self.assertEqual(book.match_time((0, 16))["id"], 1)
        self.assertIsNone(book.match_time((0, 19)))  # two minutes from every stamp
        self.assertIsNone(book.match_time((1, 21)))  # an hour off
        # FAULT: the OLDEST line within a minute names the abandoned branch's save
        oldest = next(line for line in book.saves() if gm.minutes_apart(line["play_time"], (0, 21)) <= 1)
        self.assertEqual(oldest["id"], 2)

    def test_an_unwritten_save_line_is_reported(self) -> None:
        """The writer's half (the run ENDING on it is the loop's, stage 4): a line that did not reach the file is
        reported, and the next save does not name it as its parent."""
        blocked = self.dir / "memory_blocked.jsonl"
        blocked.mkdir()  # a folder where the file should be: every append fails as a full disk or a lock would
        writer = MemoryWriter(blocked, None, header=HEADER, session=session())
        result = write_save(writer, 1, payload_of(WORLDS[0]))
        self.assertFalse(result.reached)
        self.assertTrue(writer.problems)
        self.assertIsNone(writer.parent)
        # CONTROL: the same save on a writable path reached the file
        self.assertTrue(write_save(self.new_writer(), 1, payload_of(WORLDS[0])).reached)

    def test_the_writer_refuses_to_be_used_out_of_order(self) -> None:
        write_save(self.new_writer(), 1, payload_of(WORLDS[0]))
        book = read_book(self.path)
        with self.assertRaises(MemoryFileError):  # a new game never writes after an existing memory (D10's refusal)
            MemoryWriter(self.path, book, header=HEADER, session=session())
        with self.assertRaises(MemoryFileError):  # a continue needs the memory it continues
            MemoryWriter(self.dir / "other.jsonl", None, header=HEADER, session=session("continue", continued_from=1))
        with self.assertRaises(MemoryFileError):
            MemoryWriter(self.path, book, header=None, session=session("continue") | {"cart": "maybe"})


class PathsTests(unittest.TestCase):
    def test_dev_default_is_beside_the_cartridge(self) -> None:
        from ai_player.paths import AppPaths

        with mock.patch.dict(os.environ):
            os.environ.pop("AI_PLAYER_HOME", None)
            paths = AppPaths.for_profile("ai-r1live-x-5401", Path("/build"))
        self.assertEqual(paths.memory_jsonl,
                         Path("/build") / "profiles" / "ai-r1live-x-5401" / "ai_player" / "memory.jsonl")
        self.assertEqual(paths.launches_jsonl.name, "launches.jsonl")
        self.assertEqual(paths.retired_dir, paths.game_dir / "retired")
        # the profile folder that holds current_save.sav holds the game's folder: one save, one memory
        self.assertEqual(paths.game_dir.parent, Path("/build") / "profiles" / "ai-r1live-x-5401")

    def test_home_override(self) -> None:
        from ai_player.paths import AppPaths, PathsError

        self.assertEqual(AppPaths.for_profile("game1", Path("/build"), home="/home/ai").memory_jsonl,
                         Path("/home/ai") / "games" / "game1" / "memory.jsonl")
        with mock.patch.dict(os.environ, {"AI_PLAYER_HOME": "/data/ai"}):
            self.assertEqual(AppPaths.for_profile("game1", Path("/build")).game_dir, Path("/data/ai") / "games" / "game1")
        for name in ("..", "a/b", "a\\b", "C:x", ""):
            with self.assertRaises(PathsError, msg=name):
                AppPaths.for_profile(name, Path("/build"), home="")

    def test_retired_names_never_overwrite(self) -> None:
        from ai_player.paths import AppPaths

        with tempfile.TemporaryDirectory(prefix="ai_paths_") as tmp:
            paths = AppPaths.for_profile("g", Path(tmp), home=tmp)
            first = paths.retired_path("memory.jsonl", when=0)
            self.assertRegex(first.name, r"^memory-\d{8}-\d{6}\.jsonl$")
            first.parent.mkdir(parents=True)
            first.write_text("x", encoding="utf-8")
            second = paths.retired_path("memory.jsonl", when=0)
            self.assertNotEqual(first, second)
            self.assertTrue(second.name.endswith("-2.jsonl"))

    def test_paths_is_launcher_side(self) -> None:
        from ai_player.gates import check_purity

        self.assertIn("paths.py", check_purity.LAUNCHER_FILES)
        hook = BUILD_ROOT / "plugins" / "custom_modes" / "ai_player_mode.py"
        with tempfile.TemporaryDirectory(prefix="ai_paths_gate_") as tmp:
            package = Path(tmp) / "ai_player"
            shutil.copytree(check_purity.PACKAGE_DIR, package,
                            ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures"))
            control = check_purity.scan(package, hook, BUILD_ROOT)
            self.assertTrue(control.passed, check_purity.report(control))
            self.assertEqual(control.roles["paths.py"], "launcher")
            (package / "brain" / "x_paths.py").write_text("from ai_player.paths import AppPaths\n", encoding="utf-8")
            planted = check_purity.scan(package, hook, BUILD_ROOT)
            self.assertFalse(planted.passed)  # FAULT: the play loop resolving a path itself
            self.assertTrue([v for v in planted.violations if v.rule == "c" and "x_paths" in v.file])

    # ---------------------------------------------------------------- the gate
    def test_the_gate_fails_on_a_planted_literal(self) -> None:
        from ai_player.gates import check_paths

        plants = {
            "brain/x.py": 'ROOT = "C:/Remote Projects/Pokebot_Gen3_Enhancement"\n',
            "skills/y.py": 'def f(name):\n    return f"c:\\\\games\\\\{name}"\n',
            "mode.py": 'BUILD = "../sandbox-pokebot/profiles"\n',
            "world/z.py": "B = b'C:/x'\n",
            "host/launcher.py": 'def resolve_build_root():\n    return "ok: sandbox-pokebot"\n'
                                'def elsewhere():\n    return "sandbox-pokebot"\n',
        }
        for rel, source in plants.items():
            findings = check_paths.scan_source(rel, source)
            self.assertEqual(len(findings), 1, f"{rel}: {findings}")

    def test_the_gate_ignores_docstrings_and_comments(self) -> None:
        from ai_player.gates import check_paths

        source = ('"""The dev default is sandbox-pokebot under C:/Remote Projects."""\n'
                  "# C:\\\\ and sandbox-pokebot in a comment\n"
                  "def f():\n"
                  '    """C:/x, again in a docstring."""\n'
                  '    "a bare string statement naming sandbox-pokebot"\n'
                  '    return "a:/b, abc:/d and a plain word"\n')
        self.assertEqual(check_paths.scan_source("brain/x.py", source), [])
        self.assertEqual(check_paths.scan_source("paths.py", 'X = "C:/anything"\n'), [])  # the one resolver
        self.assertEqual(check_paths.scan_source(
            "host/launcher.py", 'def resolve_build_root():\n    return "sandbox-pokebot"\n'), [])

    def test_the_tree_passes(self) -> None:
        from ai_player.gates import check_paths

        ok, findings, scanned = check_paths.check()
        self.assertEqual(findings, [])
        self.assertTrue(ok and scanned > 30)
        done = subprocess.run([sys.executable, str(Path(check_paths.__file__))], capture_output=True, text=True,
                              timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue(done.stdout.strip().splitlines()[-1].startswith("PATHS GATE: PASS"))


# ====================================================================================================================
# BUILD STAGE 3 (spec section 8 step 4): the SAVE and CONTINUE skills (`skills/saving.py`) and the POLICY (`brain/saving.py`)
# ====================================================================================================================
from types import SimpleNamespace  # noqa: E402

from ai_player.brain.goals import CENTER_SUFFIX as GOALS_CENTER_SUFFIX  # noqa: E402
from ai_player.brain.goals import GYM_SUFFIX as GOALS_GYM_SUFFIX  # noqa: E402
from ai_player.brain.goals import Goal, is_gym  # noqa: E402
from ai_player.brain.saving import (  # noqa: E402
    BIG_MOMENTS, CENTER_SUFFIX, GYM_SUFFIX, SAVE_MIN_MINUTES, SavePolicy, milestone_ids, own_cart,
)
from ai_player.eyes.observation import MenuView, View  # noqa: E402
from ai_player.eyes.screens import MAIN_MENU_OPTIONS, START_MENU_ACTIONS  # noqa: E402
from ai_player.gates.test_hands import FakeControls, Model, Recorder, drive  # noqa: E402
from ai_player.hands.pad import Faults, Hands  # noqa: E402
from ai_player.knowledge.story import load_story  # noqa: E402
from ai_player.skills import saving as skill  # noqa: E402
from ai_player.skills.saving import (  # noqa: E402
    ARRIVAL_BUDGET, BACKOUT_PRESSES, COMMIT_FRAMES_NEEDED, CONFIRM_TEXT, CONTINUE_BUDGET, CORRUPTED_TEXT, ERASED_TEXT,
    OVERWRITE_TEXT, PAGE_PRESSES, SAVE_CLOSE_BUDGET, SAVE_DIALOG_BUDGET, SAVE_FRAMES_NEEDED, SAVE_WRITE_BUDGET, SAVING_TEXT,
    continue_game, save_game,
)
import contextlib  # noqa: E402

VIEW = View(left=0, right=0, up=0, down=0, rows=(), objects=(), cropped=True)
START_OPTIONS = tuple(START_MENU_ACTIONS[a] for a in ACTIONS)  # POKéDEX POKéMON BAG PLAYER SAVE OPTION EXIT
P = PARAGRAPH
WARNING_TEXT = (f"WARNING!{P}There is a different game file that is already saved.{P}If you save now, the other file's "
                f"adventure, including items and POKéMON, will be entirely lost.{P}Are you sure you want to save now and "
                f"overwrite the other save file?")
ERROR_TEXT = f"Save error.{P}Please exchange the backup memory."
SAVED_TEXT = "AI saved the game."
#: What the eyes read as printer 0's last message right after a NO reopens the START menu (stage 1's lag frame, 67741).
LAG_TEXT = "POKéMON"


def free_look(play_time=(0, 20), frame: int = 1000, map_const: str = "ROUTE_101", tile=(5, 6), scene: bool = False,
              party=None) -> Observation:
    """A look of the player on the overworld (free, unless `scene`), with its play time read."""
    screen = ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False, waits_for_button=False,
                         in_battle=False, script_running=scene)
    player = PlayerState(map_group=0, map_number=16, map_name="ROUTE 101", map_const=map_const, x=tile[0], y=tile[1],
                         facing="down", movement="walking", elevation=3, avatar_flags=0, trainer_id=1)
    return Observation(frame=frame, screen=screen, player=player, view=VIEW,
                       party=tuple(party if party is not None else (mon(0xABCD, "TREECKO"),)), bag=None,
                       progress=progress(play_time), battle=None, last_battle_outcome=0, problems=(), cost_ms=0.1)


class SaveModel(Model):
    """The game's START menu and save dialog (`src/start_menu.c`), frame by frame, reacting to presses as the game does:
    the menu built (no input), then taking input; A on SAVE opens the dialog; each question PRINTS, then its YES/NO takes
    input (a NO reopens the START menu, after stage 1's measured lag frame); YES goes on to the next question (OVERWRITE on
    a cart that holds a save, the WARNING's three paragraphs and its question on another game's cart) or to the SAVING page,
    the write (nothing changes on screen; `write` frames), then SAVED, the box's close and a free overworld, or the save
    ERROR's two waits. Every press is logged with the state and the text on screen (`presses`)."""

    def __init__(self, *, cart: str = "none", outcome: str = "saved", options=START_OPTIONS, cursor: int = 0,
                 write: int = 255, print_frames: int = 40, question_cursor: int = 0, play_time=(0, 20),
                 tick_at: int | None = None, tick_on_whole: bool = False, unreadable: bool = False,
                 lag_after_up: bool = False, free: bool = True, pre_frames: int = 2) -> None:
        self.state = "free" if free else "scene"
        self.pre_frames = pre_frames  # the frames before InitSave (2 in the game); the stale page shows meanwhile
        self.timer = 0
        self.cart, self.outcome, self.options, self.cursor = cart, outcome, tuple(options), cursor
        self.write, self.print_frames, self.question_cursor = write, print_frames, question_cursor
        self.play_time = tuple(play_time)
        self.tick_at, self.tick_on_whole, self.unreadable, self.lag_after_up = tick_at, tick_on_whole, unreadable, lag_after_up
        self.text: str | None = None
        self.yn = 0
        self.warn_page = 0
        self.presses: list[tuple[int, str, str, str | None]] = []
        self.marks: dict[str, int] = {}  # state -> the frame it was first entered
        self.saved = False
        self.lagged = False

    # ---------------------------------------------------------------- the machine
    def enter(self, state: str, timer: int = 0) -> None:
        self.state, self.timer = state, timer
        self.marks.setdefault(state, self.frame)
        if state == "saving_whole" and self.tick_on_whole:
            self.play_time = (self.play_time[0], self.play_time[1] + 1)

    def press(self, button: str) -> None:
        self.presses.append((self.frame, button, self.state, self.page_text()))
        state = self.state
        if state == "free" and button == "Start":
            self.enter("building", 3)
        elif state == "menu":
            if button in ("Up", "Down"):
                self.cursor = (self.cursor + (1 if button == "Down" else -1)) % len(self.options)
            elif button == "B":
                # the windows removed, the controls not yet the player's: longer than one press (hold + gap, 25 frames at
                # most), so a back-out that pressed B on any screen would press one here (N2)
                self.enter("menu_closing", 30)
            elif button == "A":
                self.enter("pre", self.pre_frames) if self.options[self.cursor] == "SAVE" else self.enter("other")
        elif state.startswith("q_"):
            if button in ("Up", "Down"):
                self.yn = 0 if button == "Up" else 1
                if self.lag_after_up and button == "Up":
                    self.text = LAG_TEXT  # the question's words gone from the look (ruling 3's case)
            elif button in ("A", "B"):
                yes = button == "A" and self.yn == 0
                if not yes:
                    self.text = LAG_TEXT
                    self.enter("lag", 1)
                elif state == "q_confirm" and self.cart == "own":
                    self.enter("print_overwrite", self.print_frames)
                elif state == "q_confirm" and self.cart == "different":
                    self.warn_page = 0
                    self.enter("warn", 20)
                else:
                    self.enter("print_saving", self.print_frames)
        elif state == "warn" and button in ("A", "B") and self.timer == 0:
            self.warn_page += 1
            if self.warn_page >= 3:
                self.yn = 1  # DisplayYesNoMenuWithDefault(1): it opens on NO
                self.enter("q_different")
            else:
                self.timer = 20
        elif state == "err1" and button in ("A", "B") and self.timer == 0:
            self.enter("err_timer", 30)
        elif state == "err_wait" and button == "A":
            self.enter("free")

    def step(self, held: str | None) -> None:
        if self.tick_at is not None and self.frame == self.tick_at:
            self.play_time = (self.play_time[0], self.play_time[1] + 1)
        if self.timer > 0:
            self.timer -= 1
            if self.timer > 0:
                return
        state = self.state
        if state == "building":
            self.enter("menu")
        elif state == "pre":
            self.enter("print_confirm", self.print_frames)
        elif state == "print_confirm":
            self.yn = self.question_cursor
            self.enter("q_confirm")
        elif state == "print_overwrite":
            self.yn = self.question_cursor
            self.enter("q_overwrite")
        elif state == "lag":
            self.enter("menu")
        elif state == "menu_closing":
            self.enter("free")
        elif state == "print_saving":
            self.enter("saving_whole", 4)
        elif state == "saving_whole":
            self.enter("writing", self.write if self.outcome != "never" else 10**9)
        elif state == "writing":
            if self.outcome == "saved":
                self.saved = True
                self.enter("saved_msg", 60)
            elif self.outcome == "error":
                self.enter("err1", 20)
            elif self.outcome == "vanish":
                self.enter("free")
        elif state == "saved_msg":
            self.enter("closing", 40)
        elif state == "closing":
            self.enter("free")
        elif state == "err_timer":
            self.enter("err_wait")

    # ---------------------------------------------------------------- what the eyes see
    def page_text(self) -> str | None:
        state = self.state
        progress_of = max(0, self.print_frames - self.timer)
        if state == "pre":
            return self.text
        if state == "print_confirm":
            return CONFIRM_TEXT[:max(1, len(CONFIRM_TEXT) * progress_of // self.print_frames)]
        if state == "q_confirm":
            return self.text if self.text == LAG_TEXT else ("Wuold you liek to svae?" if self.unreadable else CONFIRM_TEXT)
        if state == "print_overwrite":
            return OVERWRITE_TEXT[:max(1, len(OVERWRITE_TEXT) * progress_of // self.print_frames)]
        if state == "q_overwrite":
            return OVERWRITE_TEXT
        if state in ("warn", "q_different"):
            return WARNING_TEXT
        if state == "print_saving":
            return SAVING_TEXT[:max(1, len(SAVING_TEXT) * progress_of // self.print_frames)]
        if state in ("saving_whole", "writing"):
            return SAVING_TEXT
        if state in ("saved_msg", "closing"):
            return SAVED_TEXT
        if state in ("err1", "err_timer", "err_wait"):
            return ERROR_TEXT
        return self.text

    def screen(self) -> ScreenState:
        state = self.state
        base = dict(game_state="OVERWORLD", screen="menu", menu=None, text_box_open=True, waits_for_button=False,
                    in_battle=False)
        if state in ("free", "scene", "other", "menu_closing"):
            return ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False,
                               waits_for_button=False, in_battle=False, script_running=state in ("scene", "other"),
                               controls_locked=state == "menu_closing")
        if state in ("building", "menu"):
            ui = MenuView(kind="start_menu", options=self.options, cursor=self.cursor, accepts_input=state == "menu")
            return ScreenState(**{**base, "text_box_open": False}, ui=ui, text=self.text)
        text = self.page_text()
        if state.startswith("q_") or state == "lag":
            ui = MenuView(kind="save_yes_no", options=YES_NO, cursor=self.yn, accepts_input=True)
            return ScreenState(**base, ui=ui, text=text)
        waits = (state == "warn" and self.timer == 0) or (state == "err1" and self.timer == 0) or state == "err_wait"
        return ScreenState(**{**base, "waits_for_button": waits}, ui=MenuView(kind="save_dialog", accepts_input=False),
                           text=text, wait_reason="printer 0 waits" if waits else None)

    def player(self) -> PlayerState:
        return free_look().player

    def presses_from(self, state: str) -> list:
        """Presses made from the frame `state` was first entered on (none if it never was)."""
        start = self.marks.get(state)
        return [] if start is None else [p for p in self.presses if p[0] >= start]


class ModelEyes:
    """The eyes on a model: its screen, the player, the window (when the overworld shows), a party, the play time."""

    def __init__(self, model) -> None:
        self.model = model

    def look(self) -> Observation:
        model = self.model
        player = model.player()
        return Observation(frame=model.frame, screen=model.screen(), player=player, view=VIEW if player else None,
                           party=model.party() if hasattr(model, "party") else (mon(0xABCD, "TREECKO"),), bag=None,
                           progress=progress(model.play_time), battle=None, last_battle_outcome=0, problems=(),
                           cost_ms=0.1)


def rig_on(model) -> tuple[Hands, list[str], Recorder]:
    said: list[str] = []
    actions = Recorder()
    hands = Hands(ModelEyes(model), FakeControls(model), random.Random(7), random.Random(8), actions, said.append, Faults())
    return hands, said, actions


def run_save(model: SaveModel, cart_is_own: bool = True, frames_left=None, written: bool = True):
    """Run `save_game` on `model` to its end: (result, hands, said, calls). `calls` logs ("writing", frame, play time)
    and ("saved", frame)."""
    hands, said, _ = rig_on(model)
    calls: list[tuple] = []

    def on_writing(play_time, look):
        calls.append(("writing", look.frame, play_time, model.state))
        return written

    result = drive(save_game(hands, "a test save", cart_is_own, frames_left or (lambda: 10**6), on_writing,
                             lambda look: calls.append(("saved", look.frame))))
    return result, hands, said, calls


class SaveSkillTests(unittest.TestCase):
    """`skills/saving.py` save_game on `SaveModel` (spec section 4 SaveSkillTests), each guard with a FAULT and a CONTROL."""

    def assertFreeAtTheEnd(self, model: SaveModel) -> None:
        self.assertEqual(model.state, "free", "the skill returned with the screen not free")

    def test_start_only_on_a_free_screen(self) -> None:
        model = SaveModel(free=False)  # FAULT: a scene plays
        result, *_ = run_save(model)
        self.assertTrue(result.startswith("not saved: the player is not free"), result)
        self.assertEqual(model.presses, [])
        model = SaveModel()  # CONTROL
        result, *_ = run_save(model)
        self.assertEqual(result, "saved")
        self.assertEqual(model.presses[0][1:3], ("Start", "free"))
        self.assertTrue(model.saved)

    def test_each_question_read_before_yes(self) -> None:
        model = SaveModel(cart="own")
        hands, said, actions = rig_on(model)
        result = drive(save_game(hands, "t", True, lambda: 10**6, lambda p, look: True, lambda look: None))
        self.assertEqual(result, "saved")
        answers = [p for p in model.presses if p[1] == "A" and p[2].startswith("q_")]
        self.assertEqual([(p[2], p[3]) for p in answers], [("q_confirm", CONFIRM_TEXT), ("q_overwrite", OVERWRITE_TEXT)])
        log = actions.records
        for words in (CONFIRM_TEXT, OVERWRITE_TEXT):
            read = next(i for i, r in enumerate(log) if r["decision"] == "read" and r["reason"] == words)
            press = next(i for i, r in enumerate(log) if r["action"].startswith("press A") and words in r["reason"])
            self.assertLess(read, press, f"'{words}' pressed before it was read")
            self.assertTrue(any(r["action"].startswith("idle") and "reading the save question" in r["reason"]
                                for r in log[:read]))

    def test_overwrite_yes_only_when_the_cart_is_its_own(self) -> None:
        model = SaveModel(cart="own")  # FAULT half: a save it does not know
        result, _, said, calls = run_save(model, cart_is_own=False)
        self.assertEqual(result, "not saved: a saved file it does not know")
        self.assertFalse(model.saved)
        self.assertEqual(calls, [])
        self.assertIn(("B", "menu"), [p[1:3] for p in model.presses])
        self.assertFreeAtTheEnd(model)
        model = SaveModel(cart="own")  # CONTROL
        result, *_ = run_save(model, cart_is_own=True)
        self.assertEqual(result, "saved")
        self.assertTrue(model.saved)
        # D17's rule (`own_cart`): kept with no save this run -> NO; empty, continued, or saved this run -> YES
        self.assertFalse(own_cart("kept", False))
        self.assertTrue(own_cart("empty", False) and own_cart("continued", False) and own_cart("kept", True))
        self.assertFalse(own_cart(None, False))

    def test_the_warnings_pages_are_turned_then_no(self) -> None:
        model = SaveModel(cart="different")
        hands, said, actions = rig_on(model)
        result = drive(save_game(hands, "t", True, lambda: 10**6, lambda p, look: True, lambda look: None))
        self.assertEqual(result, "not saved: another game's save")
        warn = [p for p in model.presses if p[2] == "warn"]
        self.assertEqual([p[1] for p in warn], ["A", "A", "A"])
        question = [p for p in model.presses if p[2] == "q_different"]
        self.assertEqual([p[1] for p in question if p[1] in ("A", "B")], ["A"])  # NO chosen (it opens on NO)
        self.assertNotIn(("Up", "q_different"), [p[1:3] for p in model.presses])
        self.assertIn(("B", "menu"), [p[1:3] for p in model.presses])
        self.assertFalse(model.saved)
        self.assertFreeAtTheEnd(model)
        log = actions.records
        turns = [i for i, r in enumerate(log) if r["action"].startswith("press A") and "turns the page" in r["reason"]]
        self.assertEqual(len(turns), 3)
        for index in turns:  # each page READ (an idle), then A
            self.assertTrue(log[index - 2]["action"].startswith("idle") or log[index - 1]["decision"] == "read")

    def test_an_unread_question_is_never_answered_yes(self) -> None:
        model = SaveModel(unreadable=True)
        result, *_ = run_save(model)
        self.assertEqual(result, "not saved: an unread question")
        self.assertFalse(model.saved)
        self.assertNotIn("print_saving", model.marks)
        self.assertFreeAtTheEnd(model)

    def test_every_no_backs_out_to_a_free_screen(self) -> None:
        cases = {
            "not saved: a saved file it does not know": (dict(cart="own"), dict(cart_is_own=False)),
            "not saved: another game's save": (dict(cart="different"), {}),
            "not saved: an unread question": (dict(unreadable=True), {}),
            "not saved: too few frames left in the run to finish a save": ({}, dict(frames_left=lambda: 10)),
        }
        for expected, (made, run) in cases.items():
            model = SaveModel(**made)
            result, *_ = run_save(model, **run)
            self.assertEqual(result, expected)
            self.assertFreeAtTheEnd(model)
            backs = [p for p in model.presses if p[1] == "B"]
            self.assertTrue(1 <= len(backs) <= BACKOUT_PRESSES, (expected, model.presses))
            self.assertTrue(all(state in ("menu", "lag") or state.startswith("q_") for _, _, state, _ in backs))
            # the NO reopened the START menu: it was closed with B before the skill returned
            self.assertIn("lag", model.marks)

    def test_no_yes_with_too_few_frames_left(self) -> None:
        model = SaveModel()  # CONTROL: exactly enough
        result, *_ = run_save(model, frames_left=lambda: COMMIT_FRAMES_NEEDED)
        self.assertEqual(result, "saved")
        model = SaveModel()  # FAULT half: one frame short
        result, _, said, _ = run_save(model, frames_left=lambda: COMMIT_FRAMES_NEEDED - 1)
        self.assertEqual(result, "not saved: too few frames left in the run to finish a save")
        self.assertFalse(model.saved)
        yes =[p for p in model.presses if p[1] == "A" and p[2] == "q_confirm"]
        self.assertEqual(len(yes), 1)  # the one A was the NO
        self.assertIn("lag", model.marks)
        self.assertTrue(any("fewer than the 1500 a save needs" in line for line in said))
        self.assertFreeAtTheEnd(model)

    def test_the_write_is_waited_out_with_no_press(self) -> None:
        model = SaveModel(write=300)
        result, *_ = run_save(model)
        self.assertEqual(result, "saved")
        self.assertEqual(model.presses_from("saving_whole"), [])

    def test_a_write_that_never_ends_is_bounded(self) -> None:
        model = SaveModel(outcome="never")
        result, _, said, calls = run_save(model)
        self.assertEqual(result, f"stuck: the save did not finish within {SAVE_WRITE_BUDGET} frames")
        self.assertEqual(model.presses_from("saving_whole"), [])
        self.assertLessEqual(model.frame - model.marks["saving_whole"], SAVE_WRITE_BUDGET + 10)
        self.assertEqual([c[0] for c in calls], ["writing"])  # the stamp was taken; no "saved"

    def test_the_stamp_is_the_full_saving_pages_play_time(self) -> None:
        model = SaveModel(tick_on_whole=True)  # the minute turns on the frame the page becomes whole
        result, _, _, calls = run_save(model)
        self.assertEqual(result, "saved")
        writing = [c for c in calls if c[0] == "writing"]
        self.assertEqual(len(writing), 1)  # ONCE
        _, frame, play_time, state = writing[0]
        self.assertGreaterEqual(frame, model.marks["saving_whole"])  # FAULT (S14): a partial page's look would be earlier
        self.assertEqual(play_time, (0, 21))  # the whole page's play time, not the printing page's (0, 20)
        self.assertEqual(state, "saving_whole")

    def test_the_save_line_is_written_at_the_start_of_the_write(self) -> None:
        """D5 (finding F8): the memory line is in the FILE before the write ends: a kill between the SAVING page and the
        SAVED page (the generator stopped there) leaves it. FAULT: a line written at the SAVED page is not there yet."""
        with tempfile.TemporaryDirectory(prefix="ai_save_") as folder:
            path = Path(folder) / "memory.jsonl"
            writer = MemoryWriter(path, None, header=HEADER, session=session())
            model = SaveModel(write=300)
            hands, _, _ = rig_on(model)

            def on_writing(play_time, look):
                return write_save(writer, 1, payload_of(WORLDS[0]), play_time=play_time).reached

            late: list = []
            skill_run = save_game(hands, "t", True, lambda: 10**6, on_writing, lambda look: late.append(look.frame))
            for _ in range(200_000):
                next(skill_run)
                if model.state == "writing" and model.frame - model.marks["writing"] >= 100:
                    break
            skill_run.close()  # KILLED in the middle of the write
            self.assertEqual(model.state, "writing")
            book = read_book(path)
            self.assertIsNotNone(book)
            self.assertEqual([line["play_time"] for line in book.saves()], [[0, 20]])
            self.assertEqual(late, [])  # FAULT half: the SAVED page had not come, so a line written there is missing

    def test_the_play_time_is_checked_through_the_write(self) -> None:
        model = SaveModel(write=300)
        model.tick_at = None
        result, _, said, _ = run_save(model)  # CONTROL: a still clock is not told
        self.assertEqual(result, "saved")
        self.assertFalse(any("changed during the write" in line for line in said))
        model = SaveModel(write=300, tick_at=10**9)
        hands, said, _ = rig_on(model)
        skill_run = save_game(hands, "t", True, lambda: 10**6, lambda p, look: True, lambda look: None)

        def tick_mid_write():
            if model.state == "writing" and model.frame - model.marks["writing"] == 50:
                model.play_time = (0, 21)

        for _ in range(200_000):
            try:
                next(skill_run)
            except StopIteration as done:
                result = done.value
                break
            tick_mid_write()
        self.assertEqual(result, "saved")
        self.assertTrue(any("changed during the write" in line for line in said), said)  # FAULT: a moving clock is told

    def test_saved_only_on_the_saved_page(self) -> None:
        model = SaveModel(outcome="vanish")  # FAULT: the box closes with no SAVED page
        result, _, _, calls = run_save(model)
        self.assertEqual(result, "not saved: the box closed with no SAVED page")
        self.assertNotIn("saved", [c[0] for c in calls])
        model = SaveModel()  # CONTROL
        result, _, _, calls = run_save(model)
        self.assertEqual(result, "saved")
        saved = [c for c in calls if c[0] == "saved"]
        self.assertEqual(len(saved), 1)
        self.assertGreaterEqual(saved[0][1], model.marks["saved_msg"])

    def test_a_save_error_is_read_and_closed(self) -> None:
        model = SaveModel(outcome="error")
        result, _, said, calls = run_save(model)
        self.assertEqual(result, "not saved: the game said: Save error. Please exchange the backup memory.")
        self.assertEqual([p[1:3] for p in model.presses_from("err1")], [("A", "err1"), ("A", "err_wait")])
        self.assertNotIn("saved", [c[0] for c in calls])
        self.assertFreeAtTheEnd(model)

    def test_back_out_with_b_only_while_it_takes_input(self) -> None:
        for made, run in ((dict(cart="different"), {}), (dict(unreadable=True), {}), ({}, dict(frames_left=lambda: 1))):
            model = SaveModel(**made)
            run_save(model, **run)
            for frame, button, state, _ in model.presses:
                if button == "B":
                    self.assertIn(state, ("menu", "lag", "q_confirm", "q_overwrite", "q_different"))
        model = SaveModel(write=300)  # CONTROL: once SAVING appeared, no press of any kind (B included)
        run_save(model)
        self.assertEqual(model.presses_from("saving_whole"), [])

    def test_no_save_without_save_on_the_menu(self) -> None:
        model = SaveModel(options=tuple(o for o in START_OPTIONS if o != "SAVE"))
        result, *_ = run_save(model)
        self.assertEqual(result, "not saved: the START menu has no SAVE")
        self.assertEqual([p[1] for p in model.presses], ["Start", "B"])
        self.assertFreeAtTheEnd(model)

    def test_save_is_chosen_by_reading_the_cursor(self) -> None:
        model = SaveModel(cursor=6)  # the menu remembers its last row (EXIT)
        result, *_ = run_save(model)
        self.assertEqual(result, "saved")
        self.assertEqual([p[1] for p in model.presses if p[2] == "menu"], ["Up", "Up", "A"])

    def test_every_answer_rests_on_the_words_of_its_own_look(self) -> None:
        """Orchestrator ruling 3: the question's words are read on the SAME look as the press. The question opens with
        its cursor on NO; after the step up the text on screen is no longer the question's (stage 1's lag frame): no A is
        pressed on that look, and the question is closed with B (NO). CONTROL: the same question with its words: YES."""
        model = SaveModel(question_cursor=1, lag_after_up=True)
        result, *_ = run_save(model)
        self.assertEqual(result, "not saved: the question could not be answered")
        self.assertEqual([p for p in model.presses if p[1] == "A" and p[2] == "q_confirm"], [])
        self.assertFalse(model.saved)
        self.assertFreeAtTheEnd(model)
        model = SaveModel(question_cursor=1)
        result, *_ = run_save(model)
        self.assertEqual(result, "saved")
        self.assertEqual([(p[1], p[3]) for p in model.presses if p[2] == "q_confirm"], [("Up", CONFIRM_TEXT),
                                                                                           ("A", CONFIRM_TEXT)])

    def test_a_stale_page_is_not_believed(self) -> None:
        """Printer 0 keeps its last message: a dialog opened after an earlier save can show that save's SAVING or SAVED
        words before its own question prints. A SAVING / SAVED / ERROR page counts only after a YES in THIS dialog (FAULT:
        believed at once, the stamp is taken before any YES was pressed)."""
        for stale in (SAVING_TEXT, SAVED_TEXT, ERROR_TEXT):
            model = SaveModel(pre_frames=40)  # the dialog slow to start: the stale page outlasts the press's own frames
            model.text = stale
            result, _, _, calls = run_save(model)
            self.assertEqual(result, "saved", stale)
            self.assertEqual([(c[0], c[3]) for c in calls if c[0] == "writing"], [("writing", "saving_whole")], stale)

    def test_an_unwritten_save_line_ends_the_run(self) -> None:
        result, *_ = run_save(SaveModel(), written=False)  # FAULT: the memory line did not reach its file
        self.assertEqual(result, "stuck: the memory of this save could not be written (the game saved)")
        result, *_ = run_save(SaveModel(), written=True)  # CONTROL
        self.assertEqual(result, "saved")

    def test_the_budgets_keep_twice_the_measured_widths(self) -> None:
        """Orchestrator ruling 1: every budget at least 2x the widest value measured so far (stage 1's eyes probe at the
        AI's slowest pacing): START to free 1,603; the first whole SAVING look to SAVED 347 (e3-4 to e5 343); SAVED to free
        103 (the probe's e5 to e7); YES to free 624."""
        self.assertGreaterEqual(SAVE_DIALOG_BUDGET, 2 * 1603)
        self.assertGreaterEqual(SAVE_WRITE_BUDGET, 2 * (343 + 4))
        self.assertGreaterEqual(SAVE_CLOSE_BUDGET, 2 * 103)
        self.assertGreaterEqual(COMMIT_FRAMES_NEEDED, 2 * 624)
        self.assertGreaterEqual(SAVE_FRAMES_NEEDED, SAVE_DIALOG_BUDGET)


class ContinueModel(Model):
    """The cold boot to a continued game: the copyright screen, the intro movie and the title (each skipped with START once
    it takes input), a main-menu error page on printer 7 if any (A), the main menu (its options by `menu_type`, the
    CONTINUE window's TIME), and after CONTINUE the load and the arrival on the overworld (optionally one free frame, then
    a scene). Presses made once the main menu first took input are `menu_presses`."""

    def __init__(self, *, menu_type: int = 1, time=(0, 20), page: str | None = None, arrive_map: str = "ROUTE_101",
                 arrive_tile=(5, 6), party_pids=((0xABCD, "TREECKO"),), scene_after: bool = False) -> None:
        self.state, self.timer = "copyright", 12
        self.menu_type, self.time, self.page = menu_type, time, page
        self.arrive_map, self.arrive_tile, self.party_pids = arrive_map, tuple(arrive_tile), party_pids
        self.scene_after = scene_after
        self.cursor = 0
        self.play_time = time
        self.presses: list[tuple[int, str, str]] = []
        self.menu_open_at: int | None = None
        self.marks: dict[str, int] = {}
        self.new_game = False

    def enter(self, state: str, timer: int = 0) -> None:
        self.state, self.timer = state, timer
        self.marks.setdefault(state, self.frame)

    @property
    def options(self) -> tuple[str, ...]:
        return MAIN_MENU_OPTIONS[self.menu_type]

    def press(self, button: str) -> None:
        self.presses.append((self.frame, button, self.state))
        state = self.state
        if state == "movie" and button == "Start" and self.timer == 0:
            self.enter("title", 10)
        elif state == "title" and button == "Start" and self.timer == 0:
            self.enter("page", 30) if self.page else self.enter("menu_in", 8)
        elif state == "page" and button == "A":
            self.enter("menu_in", 8)
        elif state == "menu":
            if button in ("Up", "Down"):
                self.cursor = max(0, min(len(self.options) - 1, self.cursor + (1 if button == "Down" else -1)))
            elif button == "A":
                choice = self.options[self.cursor]
                if choice == "CONTINUE":
                    self.enter("loading", 80)
                elif choice == "NEW GAME":
                    self.new_game = True
                    self.enter("newgame")

    def step(self, held: str | None) -> None:
        if self.timer > 0:
            self.timer -= 1
            if self.timer > 0:
                return
        state = self.state
        if state == "copyright":
            self.enter("movie", 30)
        elif state == "menu_in":
            self.enter("menu")
            self.menu_open_at = self.frame
        elif state == "loading":
            self.enter("arrive_free", 1) if self.scene_after else self.enter("free")
        elif state == "arrive_free":
            self.enter("arrive_scene", 100)
        elif state == "arrive_scene":
            self.enter("free")

    @property
    def menu_presses(self) -> list:
        return [] if self.menu_open_at is None else [p for p in self.presses if p[0] >= self.menu_open_at]

    def screen(self) -> ScreenState:
        state = self.state
        if state in ("free", "arrive_free", "arrive_scene"):
            return ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False,
                               waits_for_button=False, in_battle=False, script_running=state == "arrive_scene")
        base = dict(game_state="TITLE_SCREEN", screen="title", menu=None, text_box_open=False, waits_for_button=False,
                    in_battle=False)
        if state == "movie":
            return ScreenState(**base, ui=MenuView(kind="intro_movie", accepts_input=self.timer == 0))
        if state == "title":
            return ScreenState(**base, ui=MenuView(kind="title", options=("PRESS START",), cursor=0,
                                                   accepts_input=self.timer == 0))
        if state == "page":
            return ScreenState(**{**base, "game_state": "MAIN_MENU", "waits_for_button": True}, text=self.page,
                               wait_reason="task Task_WaitForSaveFileErrorWindow (A)")
        if state in ("menu_in", "menu", "loading", "newgame"):
            hours, minutes = self.time if self.menu_type >= 1 else (None, None)
            ui = MenuView(kind="main_menu", options=self.options, cursor=self.cursor, accepts_input=state == "menu",
                          hours=hours, minutes=minutes)
            return ScreenState(**{**base, "game_state": "MAIN_MENU"}, ui=ui)
        return ScreenState(**base)

    def player(self) -> PlayerState | None:
        if self.state not in ("free", "arrive_free", "arrive_scene"):
            return None
        return free_look(map_const=self.arrive_map, tile=self.arrive_tile).player

    def party(self):
        return tuple(mon(pid, species) for pid, species in self.party_pids) if self.player() else ()


class ContinueSkillTests(unittest.TestCase):
    """`skills/saving.py` continue_game on `ContinueModel` with a real memory file (spec section 4 ContinueSkillTests)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ai_continue_")
        self.path = Path(self.tmp.name) / "memory.jsonl"
        writer = MemoryWriter(self.path, None, header=HEADER, session=session())
        write_save(writer, 1, payload_of(WORLDS[0]), play_time=(0, 20))  # WHERE ROUTE_101 (5, 6), PARTY TREECKO 0000abcd
        writer.write_lost(party_look([mon(0xABCD, "TREECKO")], frame=BASE_FRAME + 1500))
        write_save(writer, 2, payload_of(WORLDS[1]), play_time=(0, 26))
        self.book = read_book(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_continue(self, model: ContinueModel, book=None):
        hands, said, actions = rig_on(model)
        return drive(continue_game(hands, book or self.book, "continue the game")), said, actions

    def test_continue_only_on_a_time_match(self) -> None:
        model = ContinueModel(time=(0, 23))  # FAULT: a TIME no save line has (two minutes from 0:20 and 0:26... 3 and 3)
        result, said, _ = self.run_continue(model)
        self.assertEqual(result.outcome, "stopped")
        self.assertIn("the game holds a save the AI does not remember making (TIME 0:23", result.why)
        self.assertEqual(model.menu_presses, [])
        self.assertFalse(model.new_game)
        model = ContinueModel(time=(0, 26))  # CONTROL
        result, said, _ = self.run_continue(model)
        self.assertTrue(result.continued, result.why)
        self.assertEqual(result.record["id"], 2)
        self.assertTrue(result.newest)
        self.assertEqual([p[1] for p in model.menu_presses], ["A"])

    def test_never_new_game(self) -> None:
        model = ContinueModel(menu_type=0)
        result, *_ = self.run_continue(model)
        self.assertEqual(result.outcome, "stopped")
        self.assertEqual(result.why, "the save is gone: the main menu offers no CONTINUE")
        self.assertEqual(model.menu_presses, [])
        self.assertFalse(model.new_game)

    def test_the_erased_page_is_read_and_stops(self) -> None:
        model = ContinueModel(menu_type=0, page=ERASED_TEXT)
        result, said, actions = self.run_continue(model)
        self.assertEqual(result.why, f"the save is gone: {ERASED_TEXT}")
        self.assertEqual(result.page_kind, "erased")
        self.assertEqual([p[1:] for p in model.presses if p[2] == "page"], [("A", "page")])
        self.assertTrue(any(r["decision"] == "read" and r["reason"] == ERASED_TEXT for r in actions.records))
        self.assertEqual(model.menu_presses, [])
        self.assertFalse(model.new_game)

    def test_the_corrupted_page_continues_the_older_save(self) -> None:
        model = ContinueModel(time=(0, 20), page=CORRUPTED_TEXT)
        result, said, _ = self.run_continue(model)
        self.assertTrue(result.continued, result.why)
        self.assertEqual((result.record["id"], result.page_kind, result.newest), (1, "corrupted", False))
        self.assertIn("the game said the save was corrupted: it continues the save before it", result.lines)

    def test_a_silent_older_save_is_found_by_its_time(self) -> None:
        """The measured silent window: the game loads the save before with NO page. The TIME decides (FAULT, mutant S20:
        the newest record would be save 2, whose arrival differs)."""
        model = ContinueModel(time=(0, 20))
        result, *_ = self.run_continue(model)
        self.assertTrue(result.continued, result.why)
        self.assertEqual(result.record["id"], 1)
        self.assertIsNone(result.page)
        self.assertIn("the game continued an OLDER save than its last, with no page", result.lines)
        self.assertNotEqual(self.book.newest_save()["id"], result.record["id"])

    def test_the_arrival_is_verified(self) -> None:
        for name, made in (("tile", dict(arrive_tile=(5, 7))), ("map", dict(arrive_map="ROUTE_102")),
                           ("pid", dict(party_pids=((0xABCE, "TREECKO"),))),
                           ("species", dict(party_pids=((0xABCD, "GROVYLE"),)))):
            model = ContinueModel(time=(0, 26), **made)  # FAULT: the game is not where the save line says
            result, *_ = self.run_continue(model)
            self.assertEqual(result.outcome, "stopped", name)
            self.assertIn("the save it continued is not the one it remembers", result.why, name)
        model = ContinueModel(time=(0, 26))  # CONTROL
        result, *_ = self.run_continue(model)
        self.assertTrue(result.continued)
        self.assertEqual(result.arrival, {"where": WHERE, "party": PARTY})

    def test_the_arrival_is_a_held_free_screen(self) -> None:
        model = ContinueModel(time=(0, 26), scene_after=True)  # one free frame, then a scene
        result, *_ = self.run_continue(model)
        self.assertTrue(result.continued, result.why)
        self.assertGreaterEqual(result.arrived_at, model.marks["free"])  # FAULT (S23): the lone free frame is earlier
        self.assertLess(model.marks["arrive_free"], model.marks["free"])

    def test_one_minute_tolerance_and_the_newest_wins(self) -> None:
        for time, expected in (((0, 21), 1), ((0, 25), 2), ((0, 27), 2), ((0, 19), 1)):
            model = ContinueModel(time=time)
            result, *_ = self.run_continue(model)
            self.assertTrue(result.continued, (time, result.why))
            self.assertEqual(result.record["id"], expected, time)
        model = ContinueModel(time=(0, 28))  # two minutes from the newest stamp
        result, *_ = self.run_continue(model)
        self.assertEqual(result.outcome, "stopped")
        # an abandoned branch within a minute of a newer line: the newer, later in the file, wins
        follow = MemoryWriter(self.path, self.book, header=None, session=session("continue", continued_from=1))
        follow.write_session()
        write_save(follow, 3, payload_of(WORLDS[2]), play_time=(0, 26))
        book = read_book(self.path)
        result, *_ = self.run_continue(ContinueModel(time=(0, 26)), book)
        self.assertEqual(result.record["id"], 3)

    def test_the_continue_tells_the_losses_it_undoes(self) -> None:
        writer = MemoryWriter(self.path, self.book, header=None, session=session("continue", continued_from=2))
        writer.write_session()
        writer.write_lost(party_look([mon(0xABCD, "TREECKO")], frame=BASE_FRAME + 9000))
        writer.write_lost(party_look([mon(0xABCD, "TREECKO")], frame=BASE_FRAME + 9100))
        result, said, _ = self.run_continue(ContinueModel(time=(0, 26)), read_book(self.path))
        self.assertTrue(result.continued)
        self.assertEqual(len(result.undone), 2)
        self.assertIn("this continue undoes 2 battles lost after save 0:26", result.lines)
        self.assertTrue(any("undoes 2 battles" in line for line in said))
        result, *_ = self.run_continue(ContinueModel(time=(0, 26)))  # CONTROL: no loss after save 2
        self.assertEqual(result.undone, ())
        self.assertFalse(any("undoes" in line for line in result.lines))

    def test_the_title_is_skipped_only_while_it_takes_input(self) -> None:
        model = ContinueModel(time=(0, 26))
        result, *_ = self.run_continue(model)
        self.assertTrue(result.continued)
        starts = [p for p in model.presses if p[1] == "Start"]
        self.assertEqual([p[2] for p in starts], ["movie", "title"])
        self.assertTrue(all(p[0] >= model.marks[p[2]] + (30 if p[2] == "movie" else 10) for p in starts))


# ------------------------------------------------------------------------------------------- the policy
def gym_world(key: str = "11:3", const: str = "RUSTBORO_CITY_GYM", entries=(5000,)) -> SimpleNamespace:
    """A world memory as `before_leader` reads it: where the player is (`current`, `here().const`) and the map changes
    onto it (`transitions`)."""
    changes = [SimpleNamespace(frame=frame, target=key) for frame in entries]
    return SimpleNamespace(current=key, here=lambda: SimpleNamespace(const=const), transitions=changes)


class PolicyTests(unittest.TestCase):
    """`brain/saving.py` SavePolicy (spec section 4 PolicyTests): when a save is due, and when it may be made."""

    def setUp(self) -> None:
        self.memory = _Memory()
        self.said: list[str] = []
        self.policy = SavePolicy(self.memory, self.said.append)
        self.story = load_story("BOY")

    def milestone(self, ident: str):
        return next(m for m in self.story.milestones if m.id == ident)

    def heal(self) -> Goal:
        return Goal("heal", "the party is hurt", "ch2_dad", key="heal:x")

    def test_the_constants_are_the_goal_managers(self) -> None:
        self.assertEqual(CENTER_SUFFIX, GOALS_CENTER_SUFFIX)
        self.assertEqual(GYM_SUFFIX, GOALS_GYM_SUFFIX)
        for const in ("RUSTBORO_CITY_GYM", "PETALBURG_CITY_GYM", "RUSTBORO_CITY", "ROUTE_101"):
            self.assertEqual(const.endswith(f"_{GYM_SUFFIX}"), is_gym(const), const)

    def test_due_after_a_heal_at_a_center(self) -> None:
        self.assertFalse(self.policy.after_heal(self.heal(), True, "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F"))  # MOM's heal
        self.assertFalse(self.policy.after_heal(self.heal(), False, "OLDALE_TOWN_POKEMON_CENTER_1F"))  # it did not heal
        self.assertFalse(self.policy.after_heal(Goal("shop", "x", key="shop:x"), True, "OLDALE_TOWN_POKEMON_CENTER_1F"))
        self.assertIsNone(self.memory.save_due)
        self.assertTrue(self.policy.after_heal(self.heal(), True, "OLDALE_TOWN_POKEMON_CENTER_1F"))
        choice = self.policy.next_save(free_look(map_const="OLDALE_TOWN_POKEMON_CENTER_1F"), "OLDALE_TOWN_POKEMON_CENTER_1F",
                                       10**6)
        self.assertEqual((choice.kind, choice.key), ("center", "save:center"))

    def test_the_center_due_expires_on_leaving(self) -> None:
        self.policy.after_heal(self.heal(), True, "OLDALE_TOWN_POKEMON_CENTER_1F")
        self.assertIsNotNone(self.policy.due_now(None))  # a look with no map (a battle) does not expire it
        self.assertIsNotNone(self.policy.due_now("OLDALE_TOWN_POKEMON_CENTER_1F"))
        self.assertIsNone(self.policy.next_save(free_look(map_const="OLDALE_TOWN"), "OLDALE_TOWN", 10**6))  # FAULT S41
        self.assertIsNone(self.memory.save_due)
        self.assertTrue(any("expired" in line for line in self.said))

    def test_due_after_each_big_moment(self) -> None:
        for ident in BIG_MOMENTS:
            self.memory.save_due = None
            self.assertTrue(self.policy.after_milestones([ident]), ident)
            choice = self.policy.next_save(free_look(), "ROUTE_101", 10**6)
            self.assertEqual((choice.kind, choice.milestone), ("moment", ident))
        self.memory.save_due = None
        self.assertFalse(self.policy.after_milestones(["ch1_truck", "ch1_mom"]))  # CONTROL: no big moment
        self.assertIsNone(self.policy.next_save(free_look(), "ROUTE_101", 10**6))

    def test_big_moment_ids_exist(self) -> None:
        self.assertTrue(set(BIG_MOMENTS) <= milestone_ids(), set(BIG_MOMENTS) - milestone_ids())
        self.assertEqual(len(set(BIG_MOMENTS)), len(BIG_MOMENTS))

    def test_after_milestones_receives_ids_only(self) -> None:
        """D18 (finding m5): only milestone IDS reach this module. FAULT: the marks (a dict), a flag's name, a single string
        are refused; CONTROL: ids pass."""
        with self.assertRaises(TypeError):
            self.policy.after_milestones({"FLAG_SYS_POKEDEX_GET": 1, "FLAG_ADVENTURE_STARTED": 1})
        with self.assertRaises(ValueError):
            self.policy.after_milestones(["FLAG_SYS_POKEDEX_GET"])
        with self.assertRaises(TypeError):
            self.policy.after_milestones("ch1_pokedex")
        self.assertIsNone(self.memory.save_due)
        self.assertTrue(self.policy.after_milestones(["ch1_birch", "ch1_pokedex"]))
        self.assertEqual(self.memory.save_due["milestone"], "ch1_pokedex")

    def leader_choice(self, ident: str = "ch4_roxanne", world=None, play_time=(1, 0), frames_left: int = 10**6):
        milestone = self.milestone(ident)
        step = next(s for s in milestone.steps if s.do == "talk")
        story_goal = Goal("talk", f"talk to the leader of {step.map}", ident, map=step.map, key=f"talk:{ident}")
        world = world or gym_world(const=step.map)
        return self.policy.before_leader(free_look(play_time, frame=9000, map_const=step.map), world, milestone, step,
                                         story_goal, frames_left)

    def test_a_save_right_before_the_leader(self) -> None:
        choice = self.leader_choice()
        self.assertEqual((choice.kind, choice.milestone, choice.key), ("leader", "ch4_roxanne", "save:leader:ch4_roxanne"))
        # CONTROL: DAD's talk in his gym is no fight; the rival's named fight is on no gym map
        self.memory.save_due = None
        self.assertIsNone(self.leader_choice("ch2_dad"))
        self.assertIsNone(self.leader_choice("ch1_rival_route103", world=gym_world(const="ROUTE103")))
        # a walk TO the gym (not the talk) is no save moment
        milestone = self.milestone("ch4_roxanne")
        go = Goal("go", "to the gym", "ch4_roxanne", map="RUSTBORO_CITY_GYM", key="go:RUSTBORO_CITY_GYM")
        self.assertIsNone(self.policy.before_leader(free_look(map_const="RUSTBORO_CITY_GYM"), gym_world(), milestone,
                                                    milestone.steps[0], go, 10**6))
        # enter, save, (talk); leave to train and come back: a second save before the talk (S44: once per approach)
        self.memory.save_due = None
        self.assertIsNotNone(self.leader_choice(world=gym_world(entries=(5000,)), play_time=(1, 0)))
        self.policy.record_save((1, 0), 9000, 1, "before the leader")
        self.assertEqual(self.memory.saved_for, {"ch4_roxanne": 5000})
        self.assertIsNone(self.leader_choice(world=gym_world(entries=(5000,)), play_time=(1, 1)))  # saved this approach
        again = self.leader_choice(world=gym_world(entries=(5000, 12000)), play_time=(1, 30))
        self.assertIsNotNone(again)
        self.assertEqual(self.memory.save_due["entered"], 12000)

    def test_a_center_save_just_before_counts_as_the_leaders(self) -> None:
        self.policy.record_save((1, 0), 4000, 1, "healed at the centre")  # made before it entered the gym (frame 5000)
        self.assertIsNone(self.leader_choice(play_time=(1, 2)))  # within SAVE_MIN_MINUTES: that save counts
        self.assertEqual(self.memory.saved_for, {"ch4_roxanne": 5000})
        self.assertIsNone(self.memory.save_due)
        self.memory.saved_for.clear()
        self.assertIsNotNone(self.leader_choice(play_time=(1, 3)))  # CONTROL: 3 minutes later it saves again

    def test_a_save_since_entering_the_gym_counts(self) -> None:
        self.policy.record_save((1, 0), 6000, 1, "a save on the gym map")  # after the entry at frame 5000
        self.assertIsNone(self.leader_choice(play_time=(1, 10)))  # the gap has passed: the save since entering counts
        self.assertEqual(self.memory.saved_for, {"ch4_roxanne": 5000})
        self.memory.saved_for.clear()
        self.memory.last_save["frame"] = 4000  # CONTROL: a save from before this approach (and the gap passed)
        self.assertIsNotNone(self.leader_choice(play_time=(1, 10)))

    def test_three_game_minutes_between_saves(self) -> None:
        self.policy.record_save((0, 20), 1000, 1, "x")
        ok, why = self.policy.may_save(free_look((0, 22)), 10**6)  # FAULT S42: 2 minutes
        self.assertFalse(ok)
        self.assertIn("at least 3 between saves", why)
        self.assertEqual(self.policy.may_save(free_look((0, 23)), 10**6), (True, ""))  # CONTROL: 3
        # a due whose only obstacle is the gap is COVERED by that save (never saved later, somewhere else)
        self.policy.after_milestones(["ch1_pokedex"])
        self.assertIsNone(self.policy.next_save(free_look((0, 21)), "ROUTE_101", 10**6))
        self.assertIsNone(self.memory.save_due)
        self.assertEqual(SAVE_MIN_MINUTES, 3)

    def test_no_save_without_play_time(self) -> None:
        self.policy.after_milestones(["ch1_pokedex"])
        look = dataclasses.replace(free_look(), progress=progress(None))
        self.assertEqual(self.policy.may_save(look, 10**6), (False, "the play time is not read"))
        self.assertIsNone(self.policy.next_save(look, "ROUTE_101", 10**6))
        self.assertIsNotNone(self.memory.save_due)  # it waits (told once)
        self.policy.next_save(look, "ROUTE_101", 10**6)
        self.assertEqual(sum("waits" in line for line in self.said), 1)
        self.assertIsNotNone(self.policy.next_save(free_look(), "ROUTE_101", 10**6))  # CONTROL

    def test_no_save_without_frames_left(self) -> None:
        self.policy.after_milestones(["ch1_pokedex"])
        self.assertIsNone(self.policy.next_save(free_look(), "ROUTE_101", SAVE_FRAMES_NEEDED - 1))
        self.assertFalse(self.policy.may_save(free_look(), SAVE_FRAMES_NEEDED - 1)[0])
        self.assertIsNotNone(self.policy.next_save(free_look(), "ROUTE_101", SAVE_FRAMES_NEEDED))  # CONTROL

    def test_no_save_on_a_busy_screen(self) -> None:
        self.assertEqual(self.policy.may_save(free_look(scene=True), 10**6), (False, "the screen is not free"))
        self.assertTrue(self.policy.may_save(free_look(), 10**6)[0])

    def test_one_save_satisfies_every_due_and_the_newest_wins(self) -> None:
        self.policy.after_heal(self.heal(), True, "OLDALE_TOWN_POKEMON_CENTER_1F")
        self.policy.after_milestones(["ch1_pokedex"])
        self.assertEqual(self.memory.save_due["kind"], "moment")  # the newest reason
        self.policy.record_save((0, 30), 7000, 3, "x")
        self.assertIsNone(self.memory.save_due)
        self.assertEqual(self.memory.last_save, {"id": 3, "play_time": [0, 30], "frame": 7000, "why": "x"})
        self.assertIsNone(self.policy.next_save(free_look((0, 40)), "ROUTE_101", 10**6))

    def test_the_saved_state_is_what_record_save_sets(self) -> None:
        """(R1 fix round, review R-1) `saved_state` (what a save's own memory line carries) is EXACTLY what `record_save`
        then sets, and asking for it changes nothing: a save that then fails (an error page) leaves the live policy as it
        was. A leader's approach is in it; a save with no leader due adds none."""
        self.policy.record_save((0, 20), 1000, 1, "an earlier save")
        self.memory.save_due = {"kind": "leader", "why": "w", "map": "RUSTBORO_CITY_GYM", "milestone": "ch4_roxanne",
                                "entered": 5000, "told": None}
        before = (dict(self.memory.saved_for), dict(self.memory.last_save), dict(self.memory.save_due))
        state = self.policy.saved_state((1, 0), 9000, 2, "before the leader")
        self.assertEqual((dict(self.memory.saved_for), dict(self.memory.last_save), dict(self.memory.save_due)), before)
        self.assertEqual(state, {"saved_for": {"ch4_roxanne": 5000}, "save_due": None,
                                 "last_save": {"id": 2, "play_time": [1, 0], "frame": 9000, "why": "before the leader"}})
        self.policy.record_save((1, 0), 9000, 2, "before the leader")
        self.assertEqual({"saved_for": self.memory.saved_for, "last_save": self.memory.last_save,
                          "save_due": self.memory.save_due}, state)
        self.assertEqual(self.policy.saved_state((1, 9), 9900, 3, "x")["saved_for"], {"ch4_roxanne": 5000})  # no leader due

    def test_the_policy_state_is_the_goal_memorys(self) -> None:
        """SavePolicy holds no state of its own: its fields are the goal manager's, classified for a continue (D16)."""
        self.assertEqual(set(vars(self.policy)), {"goal_memory", "_say"})
        self.assertIn("saved_for", GOAL_KEEP)
        self.assertIn("last_save", GOAL_KEEP)
        self.assertIn("save_due", GOAL_RESET)


# ---------------------------------------------------------------------------------------------------- build stage 4
#: the party of `PARTY` as a look shows it
PARTY_MONS = [mon(0xABCD, "TREECKO")]


class LauncherContinueTests(unittest.TestCase):
    """(build stage 4, spec section 3 (e), D10-D12, D17, D19, D20) THE LAUNCHER, on temporary profile folders (no
    emulator): `--continue` drops the `.ss1` and keeps the cartridge save; it is refused without a memory file, a
    cartridge save, the profile marker, or with a world file set; D12 (a)'s END CLASSES decide whether the newest session
    may be continued (one case per row of the table, each refusal's FAULT half the rule it replaces); the launcher's own
    `launches.jsonl`; `--fresh` / `--state` archive the memory (never delete it); a start with no flag is refused when a
    memory file exists; a newer memory or launches file is refused byte-identical; every run is told its memory file and
    what the cart held."""

    PROFILE = "ai-r1-test"

    def setUp(self) -> None:
        from ai_player.host import launcher
        from ai_player.paths import AppPaths

        self.launcher = launcher
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_r1_launch_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.build = self.tmp / "build"
        (self.build / "pokebot.py").parent.mkdir(parents=True)
        (self.build / "pokebot.py").write_text("# not run\n", encoding="utf-8")
        self.profile = self.build / "profiles" / self.PROFILE
        self.profile.mkdir(parents=True)
        (self.profile / "metadata.yml").write_text("rom: test\n", encoding="utf-8")
        (self.profile / launcher.PROFILE_MARKER).write_text("test\n", encoding="utf-8")
        (self.profile / launcher.SAVE_FILE).write_bytes(b"\x01" * 64)
        (self.profile / launcher.STATE_FILE).write_bytes(b"\x02" * 32)
        self.game = AppPaths.for_profile(self.PROFILE, self.build, home="")
        self.runs = self.tmp / "runs"

    # ---- helpers
    def memory(self, host: str = "launcher", run_dir: Path | None = None, end: tuple[str, bool] | None = None,
               losses: int = 0) -> Path:
        """A memory file with one session and one save (and, optionally, `losses` lost lines and an end line)."""
        run_dir = run_dir if run_dir is not None else self.runs / "r1"
        writer = MemoryWriter(self.game.memory_jsonl, None, header=HEADER,
                              session={"how": "new game", "host": host, "run_dir": str(run_dir), "cart": "empty",
                                       "started": "2026-10-29T10:00:00"})
        self.assertTrue(write_save(writer, 1, payload_of(WORLDS[0])).reached)
        for n in range(losses):
            writer.write_lost(party_look(PARTY_MONS, frame=BASE_FRAME + 5000 + n))
        if end is not None:
            writer.write_end(end[0], end[1], BASE_FRAME + 9000)
        return run_dir

    def verdict(self, run_dir: Path, reason: str) -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "purity.json").write_text(json.dumps({"verdict": "CLEAN", "facts": {"exit_reason": reason}}),
                                             encoding="utf-8")

    def child(self, code: int = 0, killed: bool = False, interrupted: bool = False):
        return self.launcher.ChildResult(exit_code=code, elapsed=1.0, killed=killed, interrupted=interrupted)

    def check(self):
        return self.launcher.memory_check(self.game)

    # ---- --continue
    def test_continue_removes_the_ss1_and_keeps_the_sav(self) -> None:
        launcher = self.launcher
        sav = (self.profile / launcher.SAVE_FILE).read_bytes()
        line = launcher.seed_profile(self.profile, None, False, continue_game=True, game=self.game)
        self.assertIn("CONTINUE", line)
        self.assertFalse((self.profile / launcher.STATE_FILE).exists())  # the cartridge is the truth (D11)
        self.assertEqual((self.profile / launcher.SAVE_FILE).read_bytes(), sav)
        # CONTROL: a plain start (no memory file) resumes whatever the profile holds and leaves the .ss1
        (self.profile / launcher.STATE_FILE).write_bytes(b"\x02")
        self.assertIn("resuming", launcher.seed_profile(self.profile, None, False, game=self.game))
        self.assertTrue((self.profile / launcher.STATE_FILE).exists())

    def test_continue_refused_without_a_sav(self) -> None:
        (self.profile / self.launcher.SAVE_FILE).unlink()
        with self.assertRaises(self.launcher.LaunchError):
            self.launcher.seed_profile(self.profile, None, False, continue_game=True, game=self.game)
        self.assertTrue((self.profile / self.launcher.STATE_FILE).exists())  # nothing changed

    def test_continue_refused_on_a_foreign_profile(self) -> None:
        (self.profile / self.launcher.PROFILE_MARKER).unlink()
        with self.assertRaises(self.launcher.LaunchError):
            self.launcher.seed_profile(self.profile, None, False, continue_game=True, game=self.game)
        self.assertTrue((self.profile / self.launcher.STATE_FILE).exists())

    def test_continue_refused_without_memory(self) -> None:
        found = self.check()
        self.assertFalse(found.ok)
        self.assertIn("no memory file", found.why)
        self.assertIn(str(self.game.memory_jsonl), found.why)
        # a memory file with a header and a session but no save line (a writer never makes one: written by hand)
        self.game.memory_jsonl.parent.mkdir(parents=True, exist_ok=True)
        self.game.memory_jsonl.write_text(
            json.dumps({"kind": "header", "schema_version": SCHEMA_VERSION, "game": "x", "identity": {}}) + "\n"
            + json.dumps({"kind": "session", "n": 1, "how": "new game", "host": "launcher", "run_dir": str(self.runs / "r1"),
                          "cart": "empty"}) + "\n", encoding="utf-8")
        self.runs.joinpath("r1").mkdir(parents=True)
        found = self.check()
        self.assertEqual((found.ok, found.why), (False, "the memory file holds no save line: nothing to continue"))
        self.game.memory_jsonl.unlink()
        self.runs.joinpath("r1").rmdir()
        # CONTROL: one save and a kill (no verdict, no launcher line): allowed
        self.memory()
        self.runs.joinpath("r1").mkdir(parents=True)
        self.assertTrue(self.check().ok, self.check().why)

    def test_the_end_classes(self) -> None:
        """D12 (a), one case per row. FAULT halves: the draft's rule ("no chosen end line -> allowed") allowed a
        `play: stopped:` end and a CHOSEN end whose end line is missing; the classes refuse both."""
        cases = [
            # (what, how the run ended, the end line (reason, at_save) or None, launcher line or None, allowed, class)
            ("a kill: no verdict, no launcher line", None, None, None, True, "KILLED"),
            ("a crash", "crash", None, None, True, "INVOLUNTARY"),
            ("the frame budget of the session", "frame-budget", None, None, True, "INVOLUNTARY"),
            ("interrupted", "interrupted", None, None, True, "INVOLUNTARY"),
            ("done, not at a save", "play: done: ch1_pokedex reached", ("done: ch1_pokedex reached", False), None, False,
             "CHOSEN"),
            ("done, right after a save", "play: done: ch1_pokedex reached", ("done: ch1_pokedex reached", True), None,
             True, "CHOSEN"),
            ("stuck, not at a save", "play: stuck: 3 battles lost", ("stuck: 3 battles lost", False), None, False,
             "CHOSEN"),
            ("the brain's frame budget, not at a save", "play: stopped: not finished within 3000 frames",
             ("stopped: not finished within 3000 frames", False), None, False, "BUDGET"),
            ("the brain's frame budget, right after a save", "play: stopped: not finished within 3000 frames",
             ("stopped: not finished within 3000 frames", True), None, True, "BUDGET"),
            ("the soft wall clock", "wall-clock", None, None, False, "BUDGET"),
            ("the launcher's hard kill", None, None, {"hard_kill": True, "interrupted": False, "exit_reason": None},
             False, "BUDGET"),
            ("a stray exit", "stray-exit", None, None, False, "NOT CLEAN"),
            ("a purity breach", "purity-breach", None, None, False, "NOT CLEAN"),
            ("a CHOSEN reason with no end line", "play: done: ch1_pokedex reached", None, None, False, "CHOSEN"),
            ("a launcher line, no verdict (killed)", None, None, {"hard_kill": False, "interrupted": False,
                                                                  "exit_reason": None}, True, "KILLED"),
            ("a launcher line with the verdict's reason", None, ("done: x reached", False),
             {"hard_kill": False, "interrupted": False, "exit_reason": "play: done: x reached"}, False, "CHOSEN"),
            # (R1 + R2 follow-up, spec D2: USER RULING 52) the controller refused a reset or erase combination: NOT CLEAN
            # (refused), from the verdict file and from the launcher's line; mutant L13 (INVOLUNTARY) allows both
            ("a reset or erase combination refused", "reset-refused", None, None, False, "NOT CLEAN"),
            ("a launcher line, reset refused", None, None,
             {"hard_kill": False, "interrupted": False, "exit_reason": "reset-refused"}, False, "NOT CLEAN"),
        ]
        for what, reason, end, launch, allowed, kind in cases:
            with self.subTest(what):
                self.game.memory_jsonl.unlink(missing_ok=True)
                self.game.launches_jsonl.unlink(missing_ok=True)
                run_dir = self.runs / what.replace(" ", "_").replace(",", "").replace(":", "").replace("'", "")
                run_dir.mkdir(parents=True, exist_ok=True)
                self.memory(run_dir=run_dir, end=end)
                if reason is not None:
                    self.verdict(run_dir, reason)
                if launch is not None:
                    self.game.launches_jsonl.write_text(
                        json.dumps({"kind": "header", "schema_version": 1}) + "\n"
                        + json.dumps({"kind": "launch_end", "run_dir": str(run_dir), "exit_code": 0, **launch}) + "\n",
                        encoding="utf-8")
                found = self.check()
                self.assertEqual((found.ok, found.end_class), (allowed, kind), found.why)
                if what == "a CHOSEN reason with no end line":
                    self.assertIn("with no end line of the AI's (refused: fail closed)", found.why)
        # UNKNOWN: the session's run folder is gone and no launcher line names it
        self.game.memory_jsonl.unlink()
        self.game.launches_jsonl.unlink(missing_ok=True)
        self.memory(run_dir=self.runs / "gone")
        found = self.check()
        self.assertEqual((found.ok, found.end_class), (False, "UNKNOWN"), found.why)
        # a HARNESS session is judged by its end line alone: none -> killed (allowed); a chosen one -> refused
        self.game.memory_jsonl.unlink()
        self.memory(host="harness", run_dir=self.runs / "gone")
        self.assertEqual((self.check().ok, self.check().end_class), (True, "KILLED"))
        self.game.memory_jsonl.unlink()
        self.memory(host="harness", run_dir=self.runs / "gone", end=("done: x reached", False))
        self.assertEqual((self.check().ok, self.check().end_class), (False, "CHOSEN"))

    STOPPED = "stuck: the continue stopped: the main menu did not come within 1700 frames of power-on"

    def stopped_continue(self, run_dir: Path | None, host: str = "launcher", before_restore: bool = True,
                         reason: str | None = None, play_after: bool = False, verdict: str | None = None) -> None:
        """Append a CONTINUE session that STOPPED (its session line, then its end line, as `mode.py` writes them), and
        the host's record of how it ended (the verdict file of a launcher session)."""
        writer = MemoryWriter(self.game.memory_jsonl, read_book(self.game.memory_jsonl), header=None,
                              session={"how": "continue", "host": host, "run_dir": str(run_dir) if run_dir else None,
                                       "cart": "continued", "continued_from": None})
        self.assertTrue(writer.write_session())
        if play_after:  # a line no stopped continue can write: a battle lost after its session line
            writer.write_lost(party_look(PARTY_MONS, frame=BASE_FRAME + 20000))
        writer.write_end(reason or self.STOPPED, False, BASE_FRAME + 20001, stopped_before_restore=before_restore)
        if run_dir is not None and host == "launcher":
            self.verdict(run_dir, verdict or f"play: {reason or self.STOPPED}")

    def test_a_continue_that_stopped_before_its_restore_is_looked_through(self) -> None:
        """(R1 fix round, review R-2) A continue that STOPPED on a bound or a failed read restored and played nothing, so
        the launcher judges the session BEFORE it (here a kill: allowed). Before the fix its `stuck:` end was CHOSEN and
        every later --continue was refused: the game could never be continued again. FAULT halves, each refused: the
        spec's own stop (the save gone: `stopped_before_restore` False); a session that played after its line; the host's
        record naming another end; and the look-through never grants MORE than the session before (a chosen end there
        stays refused). Two stopped continues in a row are both looked through; a harness session the same."""
        def fresh() -> None:
            self.game.memory_jsonl.unlink(missing_ok=True)
            self.game.launches_jsonl.unlink(missing_ok=True)

        cases = [
            ("a bound: looked through to the kill", {}, None, True, "KILLED"),
            ("the save is gone (the spec's own stop)",
             dict(before_restore=False, reason="stuck: the continue stopped: the save is gone: the main menu offers no "
                                               "CONTINUE"), None, False, "CHOSEN"),
            ("it played after its session line", dict(play_after=True), None, False, "CHOSEN"),
            ("the host's record names another end", dict(verdict="play: stuck: 3 battles lost"), None, False, "CHOSEN"),
            ("the session before was chosen, not at a save", {}, ("done: ch1_pokedex reached", False), False, "CHOSEN"),
            ("the session before was chosen right after a save", {}, ("done: ch1_pokedex reached", True), True, "CHOSEN"),
        ]
        for number, (what, extra, first_end, allowed, kind) in enumerate(cases):
            with self.subTest(what):
                fresh()
                first = self.runs / f"first-{number}"
                first.mkdir(parents=True, exist_ok=True)
                self.memory(run_dir=first, end=first_end)
                if first_end is not None:
                    self.verdict(first, f"play: {first_end[0]}")
                self.stopped_continue(self.runs / f"second-{number}", **extra)
                found = self.check()
                self.assertEqual((found.ok, found.end_class), (allowed, kind), found.why)
        # two stopped continues in a row: both looked through, to the kill
        fresh()
        self.runs.joinpath("k").mkdir(parents=True, exist_ok=True)
        self.memory(run_dir=self.runs / "k")
        self.stopped_continue(self.runs / "s1")
        self.stopped_continue(self.runs / "s2")
        self.assertEqual((self.check().ok, self.check().end_class), (True, "KILLED"), self.check().why)
        # a harness session: the same (its end line is its record)
        fresh()
        self.memory(host="harness", run_dir=self.runs / "gone")
        self.stopped_continue(None, host="harness")
        self.assertEqual((self.check().ok, self.check().end_class), (True, "KILLED"), self.check().why)
        fresh()
        self.memory(host="harness", run_dir=self.runs / "gone")
        self.stopped_continue(None, host="harness", before_restore=False,
                              reason="stuck: the continue stopped: the save is gone: x")
        self.assertEqual((self.check().ok, self.check().end_class), (False, "CHOSEN"), self.check().why)

    def test_the_look_through_is_counted_and_told(self) -> None:
        """(R1 + R2 follow-up, spec D5: the verification's V2-5) Each continue the launcher looks through is COUNTED and
        TOLD, never capped. FAULT halves (mutants FX8, FX9): after 1, 5 and 50 stopped continues the words say `looked
        through N` and name the NEWEST stop's reason, `memory_check(...).looked_through` is N, and `judge_end` lists the
        stopped sessions newest first. CONTROL: with no stop, no "looked through" in the words and `looked_through` 0."""
        newest_reason = "stuck: the continue stopped: the continued game did not reach a free overworld within 160 frames"
        for stops in (1, 5, 50):
            with self.subTest(stops=stops):
                self.game.memory_jsonl.unlink(missing_ok=True)
                self.game.launches_jsonl.unlink(missing_ok=True)
                kill = self.runs / f"kill-{stops}"
                kill.mkdir(parents=True, exist_ok=True)
                self.memory(run_dir=kill)
                for n in range(stops):
                    self.stopped_continue(self.runs / f"stop-{stops}-{n}",
                                          reason=newest_reason if n == stops - 1 else None)
                found = self.check()
                self.assertEqual((found.ok, found.end_class), (True, "KILLED"), found.why)
                self.assertIn(f"looked through {stops} continue(s) that stopped before restoring anything", found.why)
                self.assertIn(f"the newest: 'play: {newest_reason}'", found.why)
                self.assertEqual(found.looked_through, stops)
                judgement = self.launcher.judge_end(read_book(self.game.memory_jsonl),
                                                    self.launcher.read_launches(self.game.launches_jsonl))
                numbers = [n for n, _ in judgement.looked_through]
                self.assertEqual(numbers, list(range(stops + 1, 1, -1)))  # sessions stops+1 .. 2, newest first
                self.assertEqual(judgement.looked_through[0][1], f"play: {newest_reason}")
        # CONTROL: no stopped continue, nothing looked through
        self.game.memory_jsonl.unlink(missing_ok=True)
        self.game.launches_jsonl.unlink(missing_ok=True)
        self.runs.joinpath("plain").mkdir(parents=True, exist_ok=True)
        self.memory(run_dir=self.runs / "plain")
        found = self.check()
        self.assertTrue(found.ok, found.why)
        self.assertNotIn("looked through", found.why)
        self.assertEqual(found.looked_through, 0)

    def test_the_continue_tells_the_losses_it_undoes(self) -> None:
        self.memory(losses=2)
        self.runs.joinpath("r1").mkdir(parents=True)
        found = self.check()
        self.assertTrue(found.ok)
        self.assertEqual(found.undone, 2)

    def test_the_launcher_writes_its_launch_end_line(self) -> None:
        launcher = self.launcher
        run_dir = self.runs / "r1"
        launcher.record_launch(self.game, run_dir, self.child(), {"facts": {"exit_reason": "play: done: x reached"}})
        launcher.record_launch(self.game, run_dir, self.child(124, killed=True), None)
        launcher.record_launch(self.game, run_dir, self.child(130, killed=True, interrupted=True), None)
        lines = launcher.read_launches(self.game.launches_jsonl)
        self.assertEqual([(l["exit_code"], l["hard_kill"], l["interrupted"], l["exit_reason"]) for l in lines],
                         [(0, False, False, "play: done: x reached"), (124, True, False, None), (130, False, True, None)])
        text = self.game.launches_jsonl.read_text(encoding="utf-8").splitlines()
        self.assertEqual(json.loads(text[0]), {"kind": "header", "schema_version": 1})  # one header
        self.assertEqual(sum(1 for line in text if '"header"' in line), 1)

    def test_a_newer_memory_is_refused_byte_identical(self) -> None:
        self.memory()
        text = self.game.memory_jsonl.read_bytes()
        newer = text.replace(b'"schema_version":1', b'"schema_version":2', 1)
        self.assertNotEqual(newer, text)
        self.game.memory_jsonl.write_bytes(newer)
        found = self.check()
        self.assertFalse(found.ok)
        self.assertIn("newer", found.why)
        self.assertEqual(self.game.memory_jsonl.read_bytes(), newer)
        # the launcher's own file too
        self.game.memory_jsonl.write_bytes(text)
        self.runs.joinpath("r1").mkdir(parents=True)
        launches = json.dumps({"kind": "header", "schema_version": 2}).encode() + b"\n"
        self.game.launches_jsonl.write_bytes(launches)
        found = self.check()
        self.assertFalse(found.ok)
        self.assertIn("newer", found.why)
        self.assertEqual(self.game.launches_jsonl.read_bytes(), launches)
        self.game.launches_jsonl.unlink()
        self.assertTrue(self.check().ok)  # CONTROL

    def test_an_unreadable_launches_file_is_refused(self) -> None:
        """(R1 + R2 follow-up, spec D7: the R-EXCEPT audit's one defect) FAULT (mutant L14): a `0xFF` byte in
        `launches.jsonl` used to escape `read_launches` as a raw UnicodeDecodeError (past `memory_check` and the CLI's
        handler: a traceback, not the refusal sentence); now `memory_check` returns `ok False` with "cannot be read", no
        exception, and the file is left byte-identical. CONTROL: the same file without the byte is allowed, as before."""
        self.memory()
        self.runs.joinpath("r1").mkdir(parents=True)
        clean = (json.dumps({"kind": "header", "schema_version": 1}) + "\n"
                 + json.dumps({"kind": "launch_end", "run_dir": str(self.runs / "other"), "exit_code": 0,
                               "hard_kill": False, "interrupted": False, "exit_reason": None}) + "\n").encode("ascii")
        self.game.launches_jsonl.write_bytes(clean)
        found = self.check()
        self.assertTrue(found.ok, found.why)  # CONTROL
        corrupted = clean.replace(b"other", b"oth\xffr")
        self.game.launches_jsonl.write_bytes(corrupted)
        found = self.check()  # no exception: the refusal sentence
        self.assertFalse(found.ok)
        self.assertIn("cannot be read", found.why)
        self.assertEqual(self.game.launches_jsonl.read_bytes(), corrupted)

    def test_fresh_archives_the_memory(self) -> None:
        launcher = self.launcher
        self.memory()
        launcher.record_launch(self.game, self.runs / "r1", self.child(), None)
        memory_text = self.game.memory_jsonl.read_bytes()
        line = launcher.seed_profile(self.profile, None, True, game=self.game)
        self.assertIn("archived", line)
        self.assertFalse(self.game.memory_jsonl.exists())
        self.assertFalse(self.game.launches_jsonl.exists())
        retired = sorted(self.game.retired_dir.glob("*.jsonl"))
        self.assertEqual(len(retired), 2)
        self.assertEqual(next(p for p in retired if p.name.startswith("memory-")).read_bytes(), memory_text)  # never rewritten
        self.assertFalse((self.profile / launcher.STATE_FILE).exists())
        # --state archives too, and never overwrites an earlier archive
        self.memory()
        fixture = self.tmp / "fixture.ss1"
        fixture.write_bytes(b"\x03" * 16)
        launcher.seed_profile(self.profile, fixture, False, game=self.game)
        self.assertEqual(len(sorted(self.game.retired_dir.glob("memory-*.jsonl"))), 2)

    def test_no_flag_start_refused_when_memory_exists(self) -> None:
        self.memory()
        with self.assertRaisesRegex(self.launcher.LaunchError, "memory.jsonl"):
            self.launcher.seed_profile(self.profile, None, False, game=self.game)
        self.assertTrue((self.profile / self.launcher.STATE_FILE).exists())  # nothing changed

    # ---- cmd_run: what every run is told
    def test_a_launch_end_that_cannot_be_recorded_is_said(self) -> None:
        from ai_player import __main__ as cli

        with mock.patch.object(cli, "record_launch", mock.Mock(side_effect=OSError("the disk is full"))):
            code, env, out = self.run_cli("--fresh")
        self.assertIsNotNone(env)
        self.assertIn(f"could not record the launch's end in {self.game.launches_jsonl}: the disk is full", out)

    def run_cli(self, *flags: str, environ: dict | None = None) -> tuple[int, dict | None, str]:
        from ai_player import __main__ as cli

        seen: dict = {}

        def fake_child(cmd, cwd, env, wall_seconds, transcript):
            seen.update(env)
            return self.launcher.ChildResult(exit_code=0, elapsed=0.1, killed=False)

        args = cli._parser().parse_args(["run", "--profile", self.PROFILE, "--run-dir", str(self.runs / "cli"), *flags])
        out = []
        env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
        env.update(environ or {})
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(cli, "resolve_build_root", lambda explicit=None: self.build), \
                mock.patch.object(cli, "_gate", lambda build_root, allow: True), \
                mock.patch.object(cli, "check_package_resolution", lambda build_root, env: "[AI-RUN] package: test"), \
                mock.patch.object(cli, "run_child", fake_child), \
                mock.patch("builtins.print", lambda *a, **k: out.append(" ".join(str(x) for x in a))):
            code = cli.cmd_run(args)
        return code, (seen or None), "\n".join(out)

    def test_every_run_gets_the_memory_path_and_the_cart(self) -> None:
        code, env, _ = self.run_cli("--fresh")
        self.assertEqual(env["AI_PLAYER_MEMORY"], str(self.game.memory_jsonl))
        self.assertEqual(env["AI_PLAYER_CART"], "empty")
        self.assertNotIn("AI_PLAYER_CONTINUE", env)
        lines = self.launcher.read_launches(self.game.launches_jsonl)  # the launch's end, recorded (D20)
        self.assertEqual([line["run_dir"] for line in lines], [str((self.runs / "cli").resolve())])

    def test_the_cart_is_told(self) -> None:
        fixture = self.tmp / "fixture.ss1"
        fixture.write_bytes(b"\x03" * 16)
        self.assertEqual(self.run_cli("--state", str(fixture))[1]["AI_PLAYER_CART"], "empty")
        self.game.launches_jsonl.unlink(missing_ok=True)
        self.assertEqual(self.run_cli()[1]["AI_PLAYER_CART"], "kept")  # no flag, no memory file: kept
        # --continue after a kill: continued, and the switch is set; an inherited switch never reaches a plain run
        self.memory(run_dir=self.runs / "killed")
        (self.runs / "killed").mkdir(parents=True)
        (self.profile / self.launcher.SAVE_FILE).write_bytes(b"\x01" * 64)  # the --state run above emptied the cart
        code, env, out = self.run_cli("--continue")
        self.assertIsNotNone(env, out)  # the child started (its exit is the launcher's no-verdict 8: a fake child)
        self.assertEqual((env["AI_PLAYER_CART"], env["AI_PLAYER_CONTINUE"]), ("continued", "1"), out)
        self.assertIn("this continue undoes 0 battles", out)
        continue_line = [line for line in out.splitlines() if "state: CONTINUE (current_state.ss1 removed; memory" in line]
        self.assertTrue(continue_line and str(self.game.memory_jsonl) in continue_line[0], out)
        self.assertFalse((self.profile / self.launcher.STATE_FILE).exists())
        self.game.memory_jsonl.unlink()
        self.game.launches_jsonl.unlink()
        code, env, _ = self.run_cli(environ={"AI_PLAYER_CONTINUE": "1"})
        self.assertNotIn("AI_PLAYER_CONTINUE", env)

    def test_continue_refused_with_a_world_file_set(self) -> None:
        self.memory(run_dir=self.runs / "killed")
        (self.runs / "killed").mkdir(parents=True)
        code, env, out = self.run_cli("--continue", environ={"AI_PLAYER_WORLD": str(self.tmp / "world.jsonl")})
        self.assertEqual((code, env), (2, None), out)
        self.assertIn("AI_PLAYER_WORLD", out)
        self.assertTrue((self.profile / self.launcher.STATE_FILE).exists())  # refused before anything changed
        # the brain's options refuse it too (D19)
        from ai_player.options import HandsOptions

        with self.assertRaises(ValueError):
            HandsOptions(brain="play", run_dir=None, seed=1, personality=None, mart_item="x", mart_count=1, clock=None,
                         fault_ungated_a=False, fault_blind_count=False, world_in=Path("w.jsonl"),
                         memory_file=Path("m.jsonl"), continue_game=True)
        # CONTROL: without the world file the same continue starts (the fake child leaves no verdict: the launcher's 8)
        code, env, out = self.run_cli("--continue")
        self.assertEqual((code, env["AI_PLAYER_CONTINUE"]), (8, "1"), out)

    def test_a_chosen_end_is_refused_by_the_cli(self) -> None:
        """The refusal is the launcher's "cannot start" path (exit 2), before anything in the profile changes."""
        run_dir = self.runs / "done"
        self.memory(run_dir=run_dir, end=("done: ch1_pokedex reached", False))
        self.verdict(run_dir, "play: done: ch1_pokedex reached")
        code, env, out = self.run_cli("--continue")
        self.assertEqual((code, env), (2, None), out)
        self.assertIn("USER RULING 52", out)
        self.assertTrue((self.profile / self.launcher.STATE_FILE).exists())

    def test_the_cli_main_runs_a_run(self) -> None:
        """`__main__.py` main: the command line parsed and `cmd_run` called (the child stood in, as in `run_cli`)."""
        from ai_player import __main__ as cli

        seen: dict = {}

        def fake_child(cmd, cwd, env, wall_seconds, transcript):
            seen.update(env)
            return self.launcher.ChildResult(exit_code=0, elapsed=0.1, killed=False)

        env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(cli, "resolve_build_root", lambda explicit=None: self.build), \
                mock.patch.object(cli, "_gate", lambda build_root, allow: True), \
                mock.patch.object(cli, "check_package_resolution", lambda build_root, env: "x"), \
                mock.patch.object(cli, "run_child", fake_child), mock.patch("builtins.print", lambda *a, **k: None):
            code = cli.main(["run", "--profile", self.PROFILE, "--fresh", "--run-dir", str(self.runs / "main")])
        self.assertEqual(code, 8)  # the fake child leaves no verdict: the launcher's own "not certified"
        self.assertEqual(seen["AI_PLAYER_CART"], "empty")

    def test_the_options_carry_the_memory(self) -> None:
        from ai_player import options as run_options

        self.assertEqual(run_options.CARTS, gm.CARTS)
        self.assertEqual(run_options.HOSTS, gm.HOSTS)
        env = {"AI_PLAYER_BRAIN": "play", "AI_PLAYER_MEMORY": "m.jsonl", "AI_PLAYER_CONTINUE": "1",
               "AI_PLAYER_CART": "continued", "AI_PLAYER_FAULT_NO_SAVE": "1", "AI_PLAYER_HOST": "harness"}
        with mock.patch.dict(os.environ, env):
            found = run_options.HandsOptions.from_env()
        self.assertEqual((found.memory_file, found.continue_game, found.cart, found.fault_no_save, found.host),
                         (Path("m.jsonl"), True, "continued", True, "harness"))
        with mock.patch.dict(os.environ, {"AI_PLAYER_CART": "maybe"}), self.assertRaises(ValueError):
            run_options.HandsOptions.from_env()
        with mock.patch.dict(os.environ, {}, clear=False):
            for key in env:
                os.environ.pop(key, None)
            plain = run_options.HandsOptions.from_env()
        self.assertEqual((plain.memory_file, plain.continue_game, plain.cart, plain.fault_no_save, plain.host),
                         (None, False, None, False, "launcher"))


# ---------------------------------------------------------------------------------------------------- build stage 4
# THE CALL-SITE CENSUS'S SITES (gates/call_census.py; orchestrator ruling 4: R1's census findings are closed by revert_r1's
# mutants, each of which DELETES one call): a site whose deletion no test saw is a path no test drove. These tests drive
# them: the save's and the continue's other ends, the memory file's refusals, the host's look through to the save wait
# and the play time, and the words each record carries.
class _NoSaveChoice(SaveModel):
    """A START menu whose A on SAVE does nothing (the menu never reacts)."""

    def press(self, button: str) -> None:
        if self.state == "menu" and button == "A":
            self.presses.append((self.frame, button, self.state, self.page_text()))
            return
        super().press(button)


class _DialogCloses(SaveModel):
    """A on SAVE rebuilds the START menu: the dialog closes before any question."""

    def press(self, button: str) -> None:
        if self.state == "menu" and button == "A" and self.options[self.cursor] == "SAVE":
            self.presses.append((self.frame, button, self.state, self.page_text()))
            self.enter("building", 60)  # longer than a press, so the skill sees the menu react
            return
        super().press(button)


class _EndlessWarning(SaveModel):
    """The WARNING's paragraphs never end (A only rewinds the page's timer)."""

    def press(self, button: str) -> None:
        if self.state == "warn" and button in ("A", "B") and self.timer == 0:
            self.presses.append((self.frame, button, self.state, self.page_text()))
            self.timer = 20
            return
        super().press(button)


class _DeafQuestion(SaveModel):
    """A question whose A is never taken (its YES and NO cannot be chosen); a B is still NO."""

    def press(self, button: str) -> None:
        if self.state.startswith("q_") and button == "A":
            self.presses.append((self.frame, button, self.state, self.page_text()))
            return
        super().press(button)


class _SavingNeverWhole(SaveModel):
    """The SAVING page is never seen whole (each look shows its first word): the stamp is taken on the SAVED page."""

    def page_text(self) -> str | None:
        if self.state in ("saving_whole", "writing"):
            return "SAVING…"
        return super().page_text()


class _Copyright(ContinueModel):
    """A power-on that never leaves the copyright screen."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.timer = 10 ** 7


class _MenuGoes(ContinueModel):
    """The main menu goes away (stops taking input) after the first look that saw it: while it is read."""

    looks_at_menu = 0

    def screen(self) -> ScreenState:
        if self.state == "menu":
            self.looks_at_menu += 1
            if self.looks_at_menu > 1:
                self.enter("loading", 10 ** 7)
        return super().screen()


class _DeafMenu(ContinueModel):
    """A main menu whose A is never taken."""

    def press(self, button: str) -> None:
        if self.state == "menu" and button == "A":
            self.presses.append((self.frame, button, self.state))
            return
        super().press(button)


class _EndlessLoad(ContinueModel):
    """CONTINUE pressed, the game never arrives."""

    def press(self, button: str) -> None:
        super().press(button)
        if self.state == "loading":
            self.timer = 10 ** 7


class _EndlessPages(ContinueModel):
    """Every A on the error page shows another page."""

    def press(self, button: str) -> None:
        if self.state == "page" and button == "A":
            self.presses.append((self.frame, button, self.state))
            self.enter("page", 30)
            return
        super().press(button)


class CensusSiteTests(unittest.TestCase):
    """(build stage 4) The paths and the records the call-site census found no test drove (module comment above)."""

    @staticmethod
    def records(hands, decision: str) -> list[dict]:
        return [r for r in hands.actions.records if r["decision"] == decision]

    # ---------------------------------------------------------------- the save: its other ends, its words
    def test_every_other_end_of_the_save_says_why(self) -> None:
        """SAVE that cannot be chosen, a dialog that closes on its own, a WARNING whose pages never end, a dialog that
        never reaches the write: each returns its own sentence (never nothing) after backing out, and says so."""
        result, hands, said, _ = run_save(_NoSaveChoice())
        self.assertEqual(result, "not saved: SAVE could not be chosen")
        result, hands, said, _ = run_save(_DialogCloses())
        self.assertEqual(result, "not saved: the save dialog closed")
        result, hands, said, _ = run_save(_EndlessWarning(cart="different"))
        self.assertTrue(result.startswith("stuck: the dialog could not be closed"), result)
        self.assertTrue(any(f"more than {PAGE_PRESSES} pages waited for A" in line for line in said), said[-3:])
        result, hands, said, _ = run_save(SaveModel(pre_frames=10 ** 6))
        self.assertTrue(result.startswith(("not saved", "stuck")), result)
        self.assertTrue(any(f"did not reach the write within {SAVE_DIALOG_BUDGET} frames (last on screen: save_dialog '')"
                            in line for line in said), said[-3:])

    def test_a_question_that_takes_no_answer_is_backed_out_with_b(self) -> None:
        """A YES that cannot be pressed is "failed", never a YES: the back-out's B (NO) names the question's words."""
        model = _DeafQuestion()
        result, hands, said, _ = run_save(model)
        self.assertEqual(result, "not saved: the question could not be answered")
        gates = [r["reason"] for r in hands.actions.records if r["action"].startswith("press B")]
        self.assertTrue(any("the save question ('Would you like to save the game?'): B is NO" in g for g in gates), gates)
        self.assertEqual(model.state, "free")

    def test_the_save_records_the_pages_words(self) -> None:
        """The records a grader reads: the question told with its words, the read pause naming them, a `read` note of the
        whole SAVING page (with the stamp) and of the SAVED page; no "never read whole" on the normal path."""
        result, hands, said, calls = run_save(SaveModel(play_time=(0, 20)))
        self.assertEqual(result, "saved")
        self.assertTrue(any("the question 'Would you like to save the game?' (CONFIRM): yes" in line for line in said), said)
        idles = [r["reason"] for r in self.records(hands, "idle")]
        self.assertIn("reading the save question: 'Would you like to save the game?'", idles)
        notes = [(r["reason"], r["extra"].get("page")) for r in self.records(hands, "read")]
        self.assertIn(("SAVING… DON'T TURN OFF THE POWER.", "SAVING"), notes)
        self.assertIn(("AI saved the game.", "SAVED"), notes)
        self.assertFalse(any("never read whole" in line for line in said))
        # the WARNING's pages are read by their words (`save_page` in each page's note)
        _, hands, _, _ = run_save(SaveModel(cart="different"))
        pages = [r["extra"].get("page") for r in self.records(hands, "read")]
        self.assertGreaterEqual(pages.count("DIFFERENT"), 3, pages)  # each paragraph turned, then the question
        # the save error's page, read before its A, and the A's gate naming its words
        result, hands, said, _ = run_save(SaveModel(outcome="error"))
        error = "Save error. Please exchange the backup memory."
        self.assertIn(f"reading the save error: '{error}'", [r["reason"] for r in self.records(hands, "idle")])
        gates = [r["reason"] for r in hands.actions.records if r["action"].startswith("press A")]
        self.assertTrue(any(gate.endswith(f"'{error}'") and "the save error page waits" in gate for gate in gates), gates)

    def test_a_stamp_taken_late_is_still_written_and_said(self) -> None:
        """The SAVING page never seen whole: the memory line is still written (on the SAVED page), and that is SAID."""
        result, hands, said, calls = run_save(_SavingNeverWhole())
        self.assertEqual(result, "saved")
        self.assertEqual([c[0] for c in calls], ["writing", "saved"])
        self.assertTrue(any("the SAVING page was never read whole: the stamp is taken late" in line for line in said))

    # ---------------------------------------------------------------- the continue: its other stops, its words
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ai_census_")
        self.path = Path(self.tmp.name) / "memory.jsonl"
        writer = MemoryWriter(self.path, None, header=HEADER, session=session())
        write_save(writer, 1, payload_of(WORLDS[0]), play_time=(0, 20))
        write_save(writer, 2, payload_of(WORLDS[1]), play_time=(0, 26))
        self.book = read_book(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_continue(self, model):
        hands, said, _ = rig_on(model)
        return drive(continue_game(hands, self.book, "continue the game")), hands, said

    def test_every_other_stop_of_the_continue_says_why(self) -> None:
        cases = [
            (_Copyright(), f"the main menu did not come within {CONTINUE_BUDGET} frames of power-on"),
            (_MenuGoes(time=(0, 26)), "the main menu went away while it was read"),
            (ContinueModel(time=(None, None)), "the CONTINUE window's TIME cannot be read"),
            (_DeafMenu(time=(0, 26)), "CONTINUE could not be chosen"),
            (_EndlessLoad(time=(0, 26)), f"the continued game did not reach a free overworld within {ARRIVAL_BUDGET} frames"),
            (_EndlessPages(time=(0, 26), page=CORRUPTED_TEXT), "more than 3 pages before the main menu"),
        ]
        for model, why in cases:
            with self.subTest(why):
                result, _, _ = self.run_continue(model)
                self.assertEqual(result.outcome, "stopped")
                self.assertTrue(result.why.startswith(why), result.why)
                self.assertFalse(model.new_game)
                # (R1 fix round, review R-2) a bound or a failed read: nothing restored, another continue may try again
                self.assertTrue(result.may_retry, why)

    def test_only_a_bound_or_a_failed_read_may_retry(self) -> None:
        """(R1 fix round, review R-2) The spec's own stops (section 3 (f): the save gone, with or without the erased page;
        a TIME it does not remember; an arrival that differs) are NOT retryable: their end stays CHOSEN, no later
        continue. CONTROL: a continue that worked is not a stop at all."""
        cases = [(ContinueModel(menu_type=0), "the save is gone: the main menu offers no CONTINUE"),
                 (ContinueModel(menu_type=0, page=ERASED_TEXT), f"the save is gone: {ERASED_TEXT}"),
                 (ContinueModel(time=(0, 23)), "the game holds a save the AI does not remember making"),
                 (ContinueModel(time=(0, 26), arrive_tile=(5, 7)), "the save it continued is not the one it remembers")]
        for model, why in cases:
            with self.subTest(why):
                result, _, _ = self.run_continue(model)
                self.assertEqual(result.outcome, "stopped")
                self.assertTrue(result.why.startswith(why), result.why)
                self.assertFalse(result.may_retry, why)
        result, _, _ = self.run_continue(ContinueModel(time=(0, 26)))
        self.assertTrue(result.continued)
        self.assertFalse(result.may_retry)

    def test_the_continue_records_the_time_it_rests_on(self) -> None:
        result, hands, said = self.run_continue(ContinueModel(time=(0, 26)))
        self.assertEqual(result.why, "continued the save of 0:26 (ROUTE_101 5,6)")
        self.assertIn("CONTINUE TIME 0:26", [r["reason"] for r in self.records(hands, "read")])
        gates = [r["reason"] for r in hands.actions.records if r["action"].startswith("press A")]
        self.assertTrue(any("TIME 0:26 = save 2's stamp 0:26" in gate for gate in gates), gates)
        result, _, _ = self.run_continue(ContinueModel(time=(0, 23)))
        self.assertIn("its saves: 1@0:20, 2@0:26", result.why)

    def test_a_loop_that_lets_no_frame_pass_is_stopped(self) -> None:
        """(build stage 4) continue_game's passes are bounded too: a title skip that lets no frame pass (as the census's
        mutant of its call made) STOPS the continue instead of hanging it."""
        with mock.patch.object(skill, "skip_title", lambda hands, kind: iter(())):
            result, _, _ = self.run_continue(ContinueModel(time=(0, 26)))
        self.assertEqual(result.outcome, "stopped")
        self.assertIn("let no frame pass", result.why)
        self.assertTrue(result.may_retry)  # (R1 fix round, review R-2) a bound: nothing restored

    # ---------------------------------------------------------------- the policy's words
    def test_the_gap_says_when_the_last_save_was(self) -> None:
        memory = _Memory(last_save={"id": 1, "play_time": [0, 20], "frame": 5, "why": "x"})
        ok, why = SavePolicy(memory).may_save(free_look((0, 21)), 10 ** 6)
        self.assertFalse(ok)
        self.assertIn("its last save was at 0:20, 1 game minutes ago", why)

    # ---------------------------------------------------------------- the memory file's refusals
    def lines_file(self, lines: list) -> Path:
        path = Path(self.tmp.name) / "broken.jsonl"
        path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
        return path

    def test_every_broken_memory_line_is_refused(self) -> None:
        header = {"kind": "header", "schema_version": 1, "game": "x", "identity": {}}
        save = {"kind": "save", "id": 1, "parent": None, "full": True, "play_time": [0, 1], "frame": 1, "where": WHERE,
                "party": PARTY, "why": "x", "memory": {}}
        broken = {
            "a version that is no number": [dict(header, schema_version="1")],
            "a second header": [header, header],
            "two saves share an id": [header, save, save],
            "a save without its keys": [header, {"kind": "save", "id": 1}],
            "a delta naming no parent": [header, dict(save, full=False, parent=None)],
            "a session without how": [header, {"kind": "session", "n": 1, "how": "maybe"}],
            "an end without at_save": [header, {"kind": "end", "session": 1}],
            "a torn line without its length": [header, {"kind": "torn"}],
        }
        for what, lines in broken.items():
            with self.subTest(what):
                with self.assertRaises(MemoryFileError):
                    read_book(self.lines_file(lines))
        # CONTROL: the header and the save alone read
        self.assertEqual(len(read_book(self.lines_file([header, save])).saves()), 1)

    def test_a_broken_chain_and_a_misused_writer_are_refused(self) -> None:
        header = {"kind": "header", "schema_version": 1, "game": "x", "identity": {}}
        save = {"kind": "save", "id": 1, "parent": None, "full": True, "play_time": [0, 1], "frame": 1, "where": WHERE,
                "party": PARTY, "why": "x", "memory": {}}
        looping = read_book(self.lines_file([header, save, dict(save, id=2, full=False, parent=3, memory={"set": [], "del": []}),
                                             dict(save, id=3, full=False, parent=2, memory={"set": [], "del": []})]))
        with self.assertRaises(MemoryFileError):
            looping.chain(2)
        with self.assertRaises(MemoryFileError):
            looping.save(99)
        for delta in (["not", "a", "dict"], {"set": [], "del": [[]]}, {"set": [], "del": [["a", "b", "c", "d"]]},
                      {"set": [[["a"], 1, 2]], "del": []}, {"set": [[["a", "b"], 1]], "del": []}):
            with self.subTest(delta=delta):
                with self.assertRaises(MemoryFileError):
                    apply_delta({"a": 1}, delta)
        with self.assertRaises(MemoryFileError):  # a new game needs its header
            MemoryWriter(Path(self.tmp.name) / "w.jsonl", None, header=None, session=session())
        writer = MemoryWriter(self.path, self.book, header=None, session=session("continue", continued_from=2))
        writer.write_session()
        with self.assertRaises(MemoryFileError):  # one session line
            writer.write_session()
        with self.assertRaises(MemoryFileError):  # a save line needs its play time
            writer.write_save(play_time=None, frame=1, where=WHERE, party=PARTY, why="x", payload={})
        with self.assertRaises(MemoryFileError):  # a role for a Pokemon it never saw
            MonRegistry().add_role(0x1234, "lead")

    def test_an_equal_payload_has_an_empty_delta_and_sets_are_tagged(self) -> None:
        payload = payload_of(WORLDS[1], talked={"0:9|1"}, losses=1)
        self.assertEqual(diff(payload, json.loads(json.dumps(payload))), {"set": [], "del": []})
        built = build_payload(world={"seen": {1, 2}}, goals={}, personality={"history": [("Story", 3)]},
                              battle={"met": {("MAY", 1): 2}}, mons={}, losses=0)
        self.assertEqual(built["world"], {"seen": {"$set": [1, 2]}})
        self.assertEqual(built["personality"]["history"], [{"$tuple": ["Story", 3]}])
        self.assertIn("$dict", built["battle"]["met"])

    def test_a_continue_to_an_abandoned_branch_rebuilds_its_history(self) -> None:
        """The live history after a continue from a save the file's newest session had cut (an abandoned branch): its
        chain back to the full line, and nothing after it (`MemoryBook.timeline`)."""
        writer = MemoryWriter(self.path, self.book, header=None, session=session("continue", continued_from=1))
        write_save(writer, 3, payload_of(WORLDS[2]), play_time=(0, 30))  # S3, a child of S1: S2 is now abandoned
        book = read_book(self.path)
        writer = MemoryWriter(self.path, book, header=None, session=session("continue", continued_from=2))
        writer.write_session()
        events = read_book(self.path).timeline()
        self.assertEqual(events, [("save", 1), ("save", 2)])

    # ---------------------------------------------------------------- the host's look (the framework's reads, faked)
    def test_the_host_look_carries_the_save_wait_the_text_and_the_play_time(self) -> None:
        """`host/eyes.py` look -> _screen -> _ui / _save_wait / _text, and look -> _progress -> _play_time, with the
        framework's game state and tasks stood in and its memory a `SparseMemory`: the save error's A (timer 0) is the
        look's wait, its words printer 0's, its play time SaveBlock2's. CONTROL: the timer still counting, no wait."""
        from types import SimpleNamespace as Ns

        from modules.context import context

        from ai_player.eyes.screens import encode_char
        from ai_player.host import eyes as host_eyes

        framework_rom()
        words = "Save error."
        encoded = bytes(encode_char(c) for c in words) + b"\xff"
        rom = 0x085E8000
        strings = bytearray(b"\xff" * 0x400)  # the ROM string is found by reading back from its end (`_rom_string`)
        strings[0x300:0x300 + len(encoded)] = encoded
        printers = bytearray(host_eyes.TEXT_PRINTER_SIZE * 32)
        printers[0:4] = (rom + 0x300 + len(encoded)).to_bytes(4, "little")  # printer 0 ACTIVE, done, one past its EOS
        printers[host_eyes.TEXT_PRINTER_ACTIVE] = 1
        sb2 = 0x02024A54
        block = bytearray(0x20)
        block[0x0E:0x11] = bytes([1, 0, 17])

        def memory(timer: int):
            regions = {
                rom: bytes(strings), symbol("sTextPrinters"): bytes(printers), symbol("gSaveBlock2Ptr"): sb2.to_bytes(4, "little"),
                sb2: bytes(block), symbol("gMenuCallback"): (symbol("SaveCallback") | 1).to_bytes(4, "little"),
                symbol("sSaveDialogCallback"): (symbol("SaveReturnErrorCallback") | 1).to_bytes(4, "little"),
                symbol("sSaveDialogTimer"): bytes([timer]), symbol("sNumStartMenuActions"): bytes([len(ACTIONS)]),
                symbol("sCurrentStartMenuActions"): bytes(ACTIONS) + bytes(9 - len(ACTIONS)),
                symbol("sStartMenuCursorPos"): bytes([4]), symbol("sMenu"): smenu(0),
            }
            fake = SparseMemory(regions)
            fake.get_frame_count = lambda: 500
            return fake

        patches = dict(get_game_state=lambda: Ns(name="OVERWORLD"), battle_is_active=lambda: False,
                       get_tasks=lambda: [Ns(symbol="Task_ShowStartMenu", data=task(1))],
                       get_pokedex=lambda: Ns(owned_species=[], seen_species=[]), get_player=lambda: Ns(money=7),
                       get_event_flag=lambda name: False, _marks=lambda: ())
        for timer, waits in ((0, True), (5, False)):
            # the module is SEALED against rebinding (`host/attribution.py` seal_module): the test side stands the framework's
            # functions in through the module's namespace itself, for this test only
            with self.subTest(timer=timer), mock.patch.object(context, "emulator", memory(timer), create=True), \
                    mock.patch.dict(host_eyes.__dict__, patches):
                seen = host_eyes.FrameworkEyes().look()
                self.assertEqual((seen.screen.ui.kind, seen.screen.ui.accepts_input), ("save_dialog", False))
                self.assertEqual(seen.screen.waits_for_button, waits, seen.problems)
                if waits:
                    self.assertIn("SaveReturnErrorCallback", seen.screen.wait_reason)
                self.assertEqual(seen.screen.text, words, seen.problems)
                self.assertEqual(seen.progress.play_time, (1, 17), seen.problems)

    @staticmethod
    def screen_rig(state: dict):
        """(R1 fix round, review R-3) `host/eyes.py` FrameworkEyes._screen with EVERY part it reads stood in, each with a
        value that shows in the ScreenState it returns, so deleting any one of its 12 `_guarded` reads changes what it
        returns: the framework's state, battle flag, tasks and symbols through the (sealed) module's namespace, the
        eyes' own readers on the instance. `state` picks the game state, the tasks and which waits the readers report."""
        from types import SimpleNamespace as Ns

        from ai_player.eyes.observation import MenuView
        from ai_player.host import eyes as host_eyes

        symbols = {"sFieldMessageBoxMode": 2, "gPaletteFade": 0xFF, "sGlobalScriptContextStatus": 0,
                   "sLockFieldControls": 1}

        def read_symbol(name, offset=0, size=1):
            return bytes([symbols[name]]) * max(1, size)

        patches = dict(get_game_state=lambda: Ns(name=state["game_state"]), battle_is_active=lambda: True,
                       get_tasks=lambda: [Ns(symbol=name, data=bytes(32)) for name in state["tasks"]],
                       read_symbol=read_symbol)
        eyes = host_eyes.FrameworkEyes()
        eyes._waits_for_button = lambda: state.get("button")
        eyes._battle_wait = lambda: state.get("battle")
        eyes._save_wait = lambda: state.get("save")
        eyes._ui = lambda game_state, task_data, fading: (
            MenuView(state["ui"], ("SAVE",), 0, False) if "Task_ShowStartMenu" in task_data and fading else None)
        eyes._text = lambda shown, tasks: "WORDS" if shown else None
        eyes._callback_name = lambda: "CB2_NewGame"
        return eyes, mock.patch.dict(host_eyes.__dict__, patches)

    def test_the_host_screen_reads_every_part(self) -> None:
        """(R1 fix round, review R-3: orchestrator ruling 4) `_screen`'s 12 `_guarded` reads each SHOW in the screen state:
        the battle flag, the message box, the tasks (the menu needs them), the button wait, the palette fade, the menu,
        the text, the script status, the field controls, the main callback (the scene); and, on their own screens, the
        battle wait (in a battle) and the save wait (a save page). Closes the census sites the stage-4 waiver covered.
        CONTROL: with nothing reported waiting, nothing waits."""
        from ai_player.eyes.screens import SCENE_CALLBACKS

        state = {"game_state": "OVERWORLD", "tasks": ["Task_ShowStartMenu"], "ui": "start_menu", "button": "BUTTON-WAIT"}
        eyes, patched = self.screen_rig(state)
        with patched:
            problems: list[str] = []
            seen = eyes._screen(problems)
            self.assertEqual(problems, [])
            self.assertTrue(seen.in_battle)  # battle_is_active, though the state is OVERWORLD
            self.assertTrue(seen.text_box_open)
            self.assertEqual((seen.ui.kind if seen.ui else None), "start_menu")  # the tasks and the fade reach the menu
            self.assertEqual((seen.waits_for_button, seen.wait_reason), (True, "BUTTON-WAIT"))
            self.assertTrue(seen.fading)
            self.assertEqual(seen.text, "WORDS")
            self.assertTrue(seen.script_running)
            self.assertTrue(seen.controls_locked)
            self.assertEqual(seen.scene, SCENE_CALLBACKS["CB2_NewGame"])
            # the battle wait (the level-up stats box): asked only in a battle, when nothing else waits
            state.update(game_state="BATTLE", tasks=[], button=None, battle="BATTLE-WAIT")
            seen = eyes._screen([])
            self.assertEqual((seen.waits_for_button, seen.wait_reason), (True, "BATTLE-WAIT"))
            # the save wait (the save error's A): asked only under a save page, when nothing else waits
            state.update(game_state="OVERWORLD", tasks=["Task_ShowStartMenu"], ui="save_dialog", battle=None,
                         save="SAVE-WAIT")
            seen = eyes._screen([])
            self.assertEqual((seen.ui.kind, seen.waits_for_button, seen.wait_reason), ("save_dialog", True, "SAVE-WAIT"))
            # CONTROL: nothing reported waiting -> nothing waits
            state.update(save=None)
            seen = eyes._screen([])
            self.assertEqual((seen.waits_for_button, seen.wait_reason), (False, None))

    def test_the_session_builds_the_eyes_the_save_reads_rest_on(self) -> None:
        """(R1 fix round, review R-3: orchestrator ruling 4) The host session's constructor builds the AI's eyes (its one
        `FrameworkEyes()` site): a fresh table of the save's callbacks (stage 1's `_save_callbacks`, resolved at the
        first look), the crop on, and its look reads the save wait. Closes the census site the stage-4 waiver covered."""
        from ai_player.host.eyes import FrameworkEyes
        from ai_player.host.session import Session
        from ai_player.options import RunOptions

        session = Session(RunOptions.from_env(), None)
        self.assertIsInstance(session.eyes, FrameworkEyes)
        self.assertEqual((session.eyes._save_callbacks, session.eyes.crop, session.eyes.looks), (None, True, 0))
        state = {"game_state": "OVERWORLD", "tasks": ["Task_ShowStartMenu"], "ui": "save_dialog", "save": "SAVE-WAIT"}
        eyes, patched = self.screen_rig(state)
        session.eyes.__dict__.update({k: v for k, v in eyes.__dict__.items() if k.startswith("_") and callable(v)})
        with patched:
            seen = session.eyes._screen([])
        self.assertEqual((seen.ui.kind, seen.wait_reason), ("save_dialog", "SAVE-WAIT"))

    def test_the_host_reads_the_continue_windows_time(self) -> None:
        """`host/eyes.py` _ui under the main menu's task: the CONTINUE window's TIME is SaveBlock2's play time."""
        from modules.context import context

        from ai_player.host.eyes import FrameworkEyes

        framework_rom()
        sb2 = 0x02024A54
        block = bytearray(0x20)
        block[0x0E:0x11] = bytes([2, 0, 5])
        memory = SparseMemory({symbol("gSaveBlock2Ptr"): sb2.to_bytes(4, "little"), sb2: bytes(block)})
        with mock.patch.object(context, "emulator", memory, create=True):
            ui = FrameworkEyes()._ui("MAIN_MENU", {"Task_HandleMainMenuInput": task(1, 0)})
        self.assertEqual((ui.options[0], ui.hours, ui.minutes), ("CONTINUE", 2, 5))


class LiveR1HeadlineTests(unittest.TestCase):
    """(R1 + R2 follow-up, spec part (j): the verification's V2-1 and V2-2; CLAUDE.md session discipline 2, the headline
    carries the caveat) `gates/live_r1.py`'s verdict LINE, offline: when K-BETWEEN is graded under a substituted kill rule,
    the line says how the spec's midpoint arm (K-BETWEEN-MID) fared, its PASSES as well as its count, and names the
    failing seeds; `verdict_line` is the one place the printed line and `verdict.json`'s `headline` come from. FAULT halves
    (mutants LV1, LV2): the line without the caveat; a caveat that counts the midpoint's seeds but not its passes. CONTROL:
    under the spec's own midpoint rule there is no caveat."""

    SEEDS = [1, 2, 3, 4]

    @classmethod
    def setUpClass(cls) -> None:
        from ai_player.gates import live_r1

        cls.live = live_r1

    def table(self, mid: dict) -> dict:
        """Every graded arm counted and good on the four seeds, and K-BETWEEN-MID as `mid` says."""
        live = self.live
        out = {(name, seed): {"counted": True, "pass": True if name not in live.OLD_OF else None,
                              "old_shows": True if name in live.OLD_OF else None}
               for name in live.GRADED_ARMS for seed in self.SEEDS}
        out.update({("K-BETWEEN-MID", seed): dict(value) for seed, value in mid.items()})
        return out

    def line(self, summaries: dict) -> str:
        return self.live.verdict_line(self.live.verdict_of(summaries, self.SEEDS), summaries, self.SEEDS, [])

    def test_the_caveat_counts_the_midpoint_passes_and_names_its_failing_seeds(self) -> None:
        live = self.live
        self.assertNotEqual(live.BETWEEN_RULE, "midpoint", "the caveat case needs the substituted rule (orchestrator ruling 5)")
        failing = self.table({seed: {"counted": True, "pass": False} for seed in self.SEEDS})
        caveat = live.between_caveat(failing, self.SEEDS)
        self.assertIn("counted 4 of 4; passed 0 of 4; FAILING on seeds [1, 2, 3, 4]; orchestrator ruling 5)", caveat)
        mixed = self.table({1: {"counted": True, "pass": True}, 2: {"counted": True, "pass": False},
                            3: {"counted": True, "pass": True}, 4: {"counted": False}})
        self.assertIn("counted 3 of 4; passed 2 of 3; FAILING on seeds [2]; orchestrator ruling 5)",
                      live.between_caveat(mixed, self.SEEDS))
        vacuous = self.table({seed: {"counted": False} for seed in self.SEEDS})
        self.assertIn("counted 0 of 4: vacuous; passed 0 of 0; orchestrator ruling 5)",
                      live.between_caveat(vacuous, self.SEEDS))
        passing = self.table({seed: {"counted": True, "pass": True} for seed in self.SEEDS})
        self.assertNotIn("FAILING", live.between_caveat(passing, self.SEEDS))

    def test_a_midpoint_counted_below_the_floor_is_not_called_vacuous(self) -> None:
        """(fix round, review RV-2) The midpoint counted on 2 of 4 seeds (under the floor of 3) and passed both, as on #58:
        the line says 'below the floor' and never 'vacuous', which is kept for counted 0. FAULT half (mutant LV3): the old
        rule `len(counted) < FLOOR` calls it vacuous. CONTROL: counted 0 is still 'vacuous'; counted 3 and 4 carry no word."""
        live = self.live
        some = self.table({1: {"counted": True, "pass": True}, 2: {"counted": False}, 3: {"counted": False},
                           4: {"counted": True, "pass": True}})
        caveat = live.between_caveat(some, self.SEEDS)
        self.assertIn("counted 2 of 4: below the floor; passed 2 of 2; orchestrator ruling 5)", caveat)
        self.assertNotIn("vacuous", caveat)
        self.assertNotIn("vacuous", self.line(some))
        none = self.table({seed: {"counted": False} for seed in self.SEEDS})
        self.assertIn("counted 0 of 4: vacuous; passed 0 of 0;", live.between_caveat(none, self.SEEDS))
        three = self.table({1: {"counted": True, "pass": True}, 2: {"counted": True, "pass": True},
                            3: {"counted": True, "pass": True}, 4: {"counted": False}})
        self.assertIn("counted 3 of 4; passed 3 of 3; orchestrator ruling 5)", live.between_caveat(three, self.SEEDS))
        every = self.table({seed: {"counted": True, "pass": True} for seed in self.SEEDS})
        self.assertIn("counted 4 of 4; passed 4 of 4; orchestrator ruling 5)", live.between_caveat(every, self.SEEDS))

    def test_the_verdict_line_carries_the_caveat(self) -> None:
        live = self.live
        failing = self.table({seed: {"counted": True, "pass": False} for seed in self.SEEDS})
        expected = (f"LIVE R1 VERDICT: PASS{live.between_caveat(failing, self.SEEDS)} (failing: none; below the floor: "
                    f"none; discriminators that differ: 0 of 0)")
        self.assertEqual(self.line(failing), expected)
        self.assertIn("FAILING on seeds [1, 2, 3, 4]", self.line(failing))
        # FAULT half: a line built without the caveat is told apart by the same comparison
        with mock.patch.object(live, "between_caveat", lambda summaries, seeds: ""):
            self.assertNotEqual(self.line(failing), expected)
        # CONTROL: under the spec's own midpoint rule there is no caveat at all
        with mock.patch.object(live, "BETWEEN_RULE", "midpoint"):
            self.assertEqual(live.between_caveat(failing, self.SEEDS), "")
            self.assertEqual(self.line(failing), "LIVE R1 VERDICT: PASS (failing: none; below the floor: none; "
                                                 "discriminators that differ: 0 of 0)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
