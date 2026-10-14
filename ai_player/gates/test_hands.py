"""UNIT PROOFS of AI-player build step 2 (the HANDS: the pad, the dialogue and menu drivers, the eyes' menu
perception). Test side.

    py -3.12 ai_player/gates/test_hands.py        (exit 0 = every test passed)

RECORDED OBSERVATIONS. The menu and dialogue tests start from screens the AI's eyes really saw in the game:
`gates/fixtures/hands_recorded_{intro,clock,mart,nurse}.json`, written by `gates/hands_harness.py --record`
(every look whose menu, cursor, wait or page changed, as `Observation.to_dict()` writes it). Each test rebuilds
those ScreenStates and drives the REAL hands against a small MODEL of the menu that reacts to presses as the
decomp's code does (each model names its source); a model starts in the recorded state. A model is not the
game: the live arms (`gates/live_step2.py`) play the same skills in the game itself.

What each class proves, and its FAULT half (a check that cannot fail proves nothing, CLAUDE.md rule 6):
  FrameworkFreeTests  the hands, the skills, the personality and the eyes' menu file import nothing from the
                      framework or the host side; FAULT: a planted import is caught.
  ScreenReadTests     `eyes/screens.py`: read_ui on the raw bytes the host reads (the gender menu's real `sMenu`
                      bytes, a script yes/no in its 5-frame input delay, the main menu, the clock, the keyboard,
                      the intro movie), decode_text / page_text (FAULT: the page rule without its fix reads a
                      recorded CLEAR wait as an empty page), key_position against the decomp's keyboard,
                      task_wait; and the host's POINTER RANGE CHECK (`host/eyes.py` _rom_bytes, _ewram_bytes): a
                      garbage pointer is refused before the emulator is touched (one killed the process once).
  PadTests            a press without a gate is refused; the reading delay is 0.3 s to 2.5 s and grows with the
                      text; the jitter is seeded (same seed, same presses; another seed, other presses).
  DialogueTests       on recorded pages: A only on frames that WAIT, never while a page prints, and no press on
                      the choice that follows; each page's reading delay starts after it has PRINTED and covers
                      the whole page; FAULT `ungated_a`: A while printing and on the choice, which picks the
                      default.
  YesNoTests          the wall clock's recorded "Is this the correct time?" opens on NO: the AI moves to YES and
                      the A's gate says the cursor is on YES; the nurse's recorded yes/no is in its input delay:
                      nothing is pressed until it takes input; FAULT `blind_count`: NO is chosen.
  CursorTests         the gender menu (recorded) and a menu whose cursor starts ELSEWHERE (the mart menu as
                      recorded after a purchase, cursor on SELL): the chosen option is the intended one; FAULT
                      `blind_count`: from SELL a count from the top lands on QUIT. choose()'s gate is its OWN
                      look (a lying move_cursor lands no A); move_cursor waits out an input delay by itself.
  KeyboardTests       from the recorded keyboard (upper page, cursor (0,0)) and from a recorded mid-name frame
                      ('Ro', cursor (2,2) on the lower page), the AI types exactly 'Rosa' and confirms on OK; a
                      wrong letter ('Rox') and a keyboard that opens with text ('Kai') are deleted with B;
                      FAULT `blind_count`: the name is wrong from the second letter on.
  ClockTests          the hold length per minute follows the decomp; from the recorded 10:00 the clock is set to
                      21:47 and YES confirmed (model); FAULT `blind_count`: the confirmation is NO.
  QuantityTests       the mart's "How many?" (recorded x1) is read up to x5 and to x23 (+10 steps), then A.
  TalkTests           no A is pressed to START a conversation while a script runs (the museum-greeter rule);
                      when the player is free and faces the person it is; FAULT: with the free check removed
                      the A lands while the script runs.
  SceneTests          STEP 2.1: what the AI watches while it stands still is NAMED (`scene_of`: the main callback,
                      then a task, then the game state; the fade): every stretch the four skills logged under the
                      catch-all before 2.1 has a scene; every SCENE_CALLBACKS name is a symbol of the ROM; FAULT: no
                      scene and no fade IS the catch-all (which `live_step2.py` fails), a misspelt symbol raises.
  PressKindTests      STEP 2.1: `live_step2.py` classify_a on digests copied from the evidence: a wait, a menu
                      confirm, a talk; FAULT: a wait for another reason, a busy menu, another menu, a talk while a
                      script waits, an ungated A: each refused.
STEP 2.1, THE STEP-2 REVIEW'S ITEMS (each fix with a mutant in `gates/revert_step2.py` that this file catches):
  StallTests          (1) an unknown prompt (a script runs, nothing on screen changes, no menu the eyes know) is
                      "stuck:<reason>" after STALL_FRAMES, not the 3-minute budget; a scene the eyes NAME gets
                      STALL_FRAMES_SCENE; a screen that changes is never stuck; the measured still stretches.
  ProvenanceTests     (2) two different uncommitted trees give two different evidence CODE lines (a digest).
  PadFrameTests       (3) the pad counts each frame as it passes (a skill stopped mid-press: the frames it ran), and
                      `live_step2.check_purity` fails the step-2 XBC numbers (pad 5991, instrument 6000).
  FadeTests           (4) nothing takes input while a palette fade runs (`read_ui`), and the intro presses START only
                      on a movie that takes it (a model of `src/intro.c` MainCB2_Intro, which drops a key in a fade).
  NameQuestionTests   (5) "So it's NAME?" names EXACTLY the typed name; an unreadable page is answered from what the
                      keyboard confirmed (no NO-and-retype loop); another name is answered NO.
  SubSkillFailureTests (6) a failed choice, name or answer ends the intro, the nurse, the mart and the clock AT ONCE.
  GenderSlideTests    FOUND through (6): the gender menu stays on screen, not taking input, while Birch's sprites slide
                      after a cursor move (the eyes used to report it closed; the old intro chose again and hid it).
(7) is `gates/test_eyes.py` PartyNoneTests.test_a_torn_slot_makes_the_whole_party_none (`revert_step11.py` R5c).

The FAULT switches show the tests catch a NAIVE driver. That each check of the REAL code carries weight is
`gates/revert_step2.py`: it breaks one check per copy of the package and runs this file there (44 mutants since
the review's items: 39 caught by their predicted tests, 5 REDUNDANT ALONE, each with the reason it is redundant).
"""

from __future__ import annotations

import ast
import json
import os
import random
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
#: Where the framework lives. A REVERT copy of the package (`gates/revert_step2.py`) runs this file from a
#: temporary folder and points here at the real repo (as `gates/test_eyes.py` does): without it the host's
#: range-check test cannot import `ai_player.host.eyes` (it needs the framework) and ERRORs in every copy.
SUPPORT = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
for entry in (str(REPO), str(SUPPORT / "sandbox-pokebot")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from ai_player.eyes.observation import (  # noqa: E402
    MenuView, Observation, PlayerState, ScreenState, SeenObject, Tile, View,
)
from ai_player.eyes.screens import (  # noqa: E402
    KEYBOARD_COLUMNS, KEYBOARD_PAGES, PARAGRAPH, SCENE_CALLBACKS, SCENE_STATES, decode_text, key_position, page_text, read_ui,
    scene_of, task_wait,
)
from ai_player.hands.dialogue import (  # noqa: E402
    GENERIC_BUSY, STALL_FRAMES, STALL_FRAMES_SCENE, STUCK, UNGATED_GATE, advance, busy_reason, player_free, talk,
)
from ai_player.hands.menus import (  # noqa: E402
    BLIND_GATE, CLOCK_BUDGET, MART_CLERK_GFX, NURSE_GFX, TYPE_BUDGET, WAIT_UI_BUDGET, answer_yes_no, choose, clock_hold_frames,
    mart_buy, move_cursor, nurse_heal, set_clock, set_quantity, type_name,
)
from ai_player.hands.pad import HUMAN_PACING, Faults, Hands, Pad, PadError  # noqa: E402
from ai_player.personality import Personality, choose_gender, choose_name  # noqa: E402
from ai_player.skills.intro import TRUCK_MAP, name_in_question, play_intro  # noqa: E402

PACKAGE = REPO / "ai_player"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
#: The files that must stay framework-free and host-free (build step 2's).
FRAMEWORK_FREE = ("eyes/screens.py", "hands/__init__.py", "hands/pad.py", "hands/dialogue.py", "hands/menus.py",
                  "skills/__init__.py", "skills/intro.py", "skills/clock.py", "personality.py")


def recorded(brain: str) -> list[dict]:
    return json.loads((FIXTURES / f"hands_recorded_{brain}.json").read_text(encoding="utf-8"))["records"]


def screen_from(data: dict) -> ScreenState:
    """A recorded `ScreenState` dict (Observation.to_dict) back into the dataclass."""
    data = dict(data)
    ui = data.pop("ui", None)
    if ui is not None:
        ui = dict(ui)
        ui["options"] = tuple(ui.get("options") or ())
        ui["prices"] = tuple(ui.get("prices") or ())
        if ui.get("cursor_xy") is not None:
            ui["cursor_xy"] = tuple(ui["cursor_xy"])
        ui = MenuView(**ui)
    return ScreenState(ui=ui, **data)


def find(records: list[dict], test) -> dict:
    hit = next((r for r in records if test(r)), None)
    if hit is None:
        raise AssertionError("no recorded screen matches")
    return hit


def observation(screen: ScreenState, frame: int, player: PlayerState | None = None, view: View | None = None) -> Observation:
    return Observation(frame=frame, screen=screen, player=player, view=view, party=(), bag=None, progress=None,
                       battle=None, last_battle_outcome=0, problems=(), cost_ms=0.0)


def overworld_screen(**changes) -> ScreenState:
    base = dict(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False, waits_for_button=False,
                in_battle=False)
    base.update(changes)
    return ScreenState(**base)


# ------------------------------------------------------------------------------------------- the rig
class Model:
    """A menu or a text, reacting to presses. `tick(button, new)` runs ONE frame with `button` held (`new` on the
    hold's first frame, as `JOY_NEW` sees it); `screen()` is what the eyes would report after it."""

    frame = 0

    def tick(self, button: str | None, new: bool) -> None:
        self.frame += 1
        if button is not None and new:
            self.press(button)
        self.step(button)

    def press(self, button: str) -> None:
        pass

    def step(self, held: str | None) -> None:
        pass

    def screen(self) -> ScreenState:
        raise NotImplementedError

    def player(self) -> PlayerState | None:
        return None

    def view(self) -> View | None:
        return None


class FakeControls:
    """The brain's `Controls` on a model: one model frame per `yield`, a hold's first frame is a new press."""

    def __init__(self, model: Model) -> None:
        self.model = model
        self.log: list[tuple[int, str, int]] = []

    def wait(self, frames: int):
        for _ in range(frames):
            self.model.tick(None, False)
            yield

    def tap(self, button: str):
        yield from self.hold(button, 1)
        yield from self.wait(1)

    def hold(self, button: str, frames: int):
        self.log.append((self.model.frame, button, frames))
        for index in range(frames):
            self.model.tick(button, index == 0)
            yield


class FakeEyes:
    def __init__(self, model: Model) -> None:
        self.model = model

    def look(self) -> Observation:
        return observation(self.model.screen(), self.model.frame, self.model.player(), self.model.view())


class Recorder:
    """The action log's `record` (`memory_log.ActionLog.record`'s signature), kept in a list: the idle and busy
    records carry the pad's frame (`extra["pad_frame"]`), which on a model is the model's own frame."""

    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, look, decision: str, action: str, reason: str, extra: dict | None = None) -> None:
        self.records.append({"decision": decision, "action": action, "reason": reason, "extra": extra or {}})


def rig(model: Model, faults: Faults = Faults(), seed: int = 5, actions: Recorder | None = None) -> Hands:
    return Hands(FakeEyes(model), FakeControls(model), random.Random(f"{seed}:pacing"), random.Random(f"{seed}:choices"),
                 actions, lambda line: None, faults)


def drive(generator, budget: int = 200_000):
    """Run a hands generator to its end (each `next` is one frame, the model ticked inside the controls)."""
    for _ in range(budget):
        try:
            next(generator)
        except StopIteration as done:
            return done.value
    raise AssertionError("the generator did not end within the budget")


# ------------------------------------------------------------------------------------------- models
class MenuModel(Model):
    """`src/menu.c` Menu_ProcessInputNoWrap: Up / Down move the cursor between min and max (no wrap), A chooses
    the cursor, B chooses MENU_B_PRESSED; `delay` frames ignore input first (`Task_HandleYesNoInput`'s tRight)."""

    def __init__(self, start: ScreenState, delay: int = 0) -> None:
        self.base = start
        self.kind = start.ui.kind
        self.options = start.ui.options
        self.cursor = start.ui.cursor
        self.delay = delay
        self.chosen: int | None = None
        self.presses_while_closed = 0
        self.dropped = 0  # presses the menu IGNORED because they came during its input delay

    def press(self, button: str) -> None:
        if self.chosen is not None:
            self.presses_while_closed += 1
            return
        if self.delay > 0:
            self.dropped += 1
            return
        if button == "Up":
            self.cursor = max(0, self.cursor - 1)
        elif button == "Down":
            self.cursor = min(len(self.options) - 1, self.cursor + 1)
        elif button == "A":
            self.chosen = self.cursor
        elif button == "B":
            self.chosen = -1

    def step(self, held: str | None) -> None:
        if self.delay > 0:
            self.delay -= 1

    def screen(self) -> ScreenState:
        if self.chosen is not None:
            return ScreenState(**{**self.base.__dict__, "ui": None})
        ui = MenuView(**{**self.base.ui.__dict__, "cursor": self.cursor, "accepts_input": self.delay == 0})
        return ScreenState(**{**self.base.__dict__, "ui": ui})


class DialogueModel(Model):
    """A message of pages (`src/text.c`: a page PRINTS a character every `speed` frames, then the printer waits
    in RENDER_STATE_CLEAR for a NEW A or B; a press while printing only speeds the page up, `canABSpeedUpPrint`),
    followed by a CHOICE (a yes/no whose cursor starts on `default`), as in the nurse's and Birch's scripts."""

    def __init__(self, pages: list[str], speed: int = 2, default: int = 0) -> None:
        self.pages = pages
        self.speed = speed
        self.page = 0
        self.shown = 0
        self.timer = 0
        self.default = default
        self.choice_open = False
        self.chosen: int | None = None
        self.cursor = default
        self.presses: list[tuple[int, str, str]] = []  # (frame, button, what the screen was)
        self.completed: dict[int, int] = {}  # page index -> the frame it finished printing (its wait began)
        self.advanced: list[tuple[int, int]] = []  # (frame, page index) of each press that moved a WAITING page on

    def state(self) -> str:
        if self.chosen is not None:
            return "done"
        if self.choice_open:
            return "choice"
        return "waiting" if self.shown >= len(self.pages[self.page]) else "printing"

    def press(self, button: str) -> None:
        state = self.state()
        self.presses.append((self.frame, button, state))
        if state == "printing" and button in ("A", "B"):
            self.shown = len(self.pages[self.page])
            self.completed.setdefault(self.page, self.frame)
        elif state == "waiting" and button in ("A", "B"):
            self.advanced.append((self.frame, self.page))
            if self.page + 1 < len(self.pages):
                self.page, self.shown = self.page + 1, 0
            else:
                self.choice_open = True
        elif state == "choice":
            if button == "A":
                self.chosen = self.cursor
            elif button == "Down":
                self.cursor = 1
            elif button == "Up":
                self.cursor = 0

    def step(self, held: str | None) -> None:
        if self.state() == "printing":
            self.timer += 1
            if self.timer >= self.speed:
                self.timer = 0
                self.shown += 1
                if self.shown >= len(self.pages[self.page]):
                    self.completed.setdefault(self.page, self.frame)

    def screen(self) -> ScreenState:
        state = self.state()
        done = PARAGRAPH.join(self.pages[:self.page])
        text = (done + PARAGRAPH if done else "") + self.pages[self.page][:self.shown]
        if state == "waiting":
            return overworld_screen(screen="text", text_box_open=True, waits_for_button=True,
                                    wait_reason="text printer 0 CLEAR", text=text + PARAGRAPH, script_running=True,
                                    controls_locked=True)
        if state == "choice":
            return overworld_screen(screen="menu", menu="yes_no", text=text, script_running=True, controls_locked=True,
                                    ui=MenuView(kind="yes_no", options=("YES", "NO"), cursor=self.cursor))
        if state == "done":
            return overworld_screen()
        return overworld_screen(screen="text", text_box_open=True, text=text, script_running=True, controls_locked=True)

    def player(self) -> PlayerState:
        return PlayerState(map_group=0, map_number=0, map_name="TEST", map_const="TEST", x=5, y=5, facing="up",
                           movement="walking", elevation=3, avatar_flags=0, trainer_id=1)


class KeyboardModel(Model):
    """`src/naming_screen.c`: the cursor moves as HandleDpadMovement moves it (the row wraps over the keys and the
    button column, which is entered at row sKeyRowToButtonRow[y] and left at the row remembered in tButtonId or
    sButtonRowToKeyRow[y]); SELECT turns the page (symbols -> upper -> lower) and keeps the cursor on the
    buttons or clamps it, with input off while the page turns; A types the key (and moves the cursor to OK when
    the text is full), or acts as PAGE / BACK / OK on the buttons; B deletes; START puts the cursor on OK."""

    ORDER = ("symbols", "upper", "lower")

    def __init__(self, start: ScreenState) -> None:
        ui = start.ui
        self.base = start
        self.page = ui.page
        self.x, self.y = ui.cursor_xy
        self.text = ui.text
        self.max = ui.max_chars or 7
        self.button_id = 0
        self.busy = 0
        self.closed = False

    def press(self, button: str) -> None:
        if self.closed or self.busy:
            return
        cols = KEYBOARD_COLUMNS[self.page]
        if button == "Select":
            self.turn_page()
        elif button == "B":
            self.text = self.text[:-1]
        elif button == "Start":
            self.x, self.y = cols, 2
        elif button == "A":
            if self.x < cols:
                char = KEYBOARD_PAGES[self.page][self.y][self.x]
                if len(self.text) < self.max:
                    self.text += char
                if len(self.text) >= self.max:
                    self.x, self.y = cols, 2
            elif self.y == 0:
                self.turn_page()
            elif self.y == 1:
                self.text = self.text[:-1]
            else:
                self.closed = True
        elif button in ("Up", "Down", "Left", "Right"):
            self.move(button)

    def turn_page(self) -> None:
        old_cols = KEYBOARD_COLUMNS[self.page]
        on_last = self.x == old_cols
        self.page = self.ORDER[(self.ORDER.index(self.page) + 1) % 3]
        cols = KEYBOARD_COLUMNS[self.page]
        if on_last:
            self.x = cols
        elif self.x >= cols:
            self.x = cols - 1
        self.busy = 20

    def move(self, button: str) -> None:
        cols = KEYBOARD_COLUMNS[self.page]
        dx = {"Left": -1, "Right": 1}.get(button, 0)
        dy = {"Up": -1, "Down": 1}.get(button, 0)
        prev_x = self.x
        x, y = self.x + dx, self.y + dy
        if x < 0:
            x = cols
        if x > cols:
            x = 0
        if dx:
            if x == cols:
                self.button_id = y
                y = (0, 1, 1, 2)[y]
            elif prev_x == cols:
                y = self.button_id if y == 1 else (0, 0, 3)[y]
        if x == cols:
            y = y % 3
            if y == 0:
                self.button_id = 1
            elif y == 2:
                self.button_id = 2
        else:
            y = y % 4
        self.x, self.y = x, y

    def step(self, held: str | None) -> None:
        if self.busy:
            self.busy -= 1

    def screen(self) -> ScreenState:
        if self.closed:
            return ScreenState(**{**self.base.__dict__, "ui": None, "game_state": "MAIN_MENU"})
        ui = MenuView(kind="naming", page=self.page, cursor_xy=(self.x, self.y), text=self.text, max_chars=self.max,
                      accepts_input=self.busy == 0)
        return ScreenState(**{**self.base.__dict__, "ui": ui})


class ClockModel(Model):
    """`src/wallclock.c` Task_SetClock_HandleInput: while the hand is between two minutes it keeps turning by
    CalcMinHandDelta(speed) degrees a frame; on a minute, A asks "Is this the correct time?" (a yes/no that
    opens on NO); a held Left / Right starts the next minute (speed + 1) and AdvanceClock moves the time."""

    def __init__(self, start: ScreenState) -> None:
        self.base = start
        self.hours, self.minutes = start.ui.hours, start.ui.minutes
        self.angle = self.minutes * 6
        self.speed = 0
        self.asking: MenuModel | None = None
        self.confirmed: bool | None = None
        self.asked = 0

    @staticmethod
    def delta(speed: int) -> int:
        return 6 if speed > 60 else 3 if speed > 30 else 2 if speed > 10 else 1

    def tick(self, button: str | None, new: bool) -> None:
        self.frame += 1
        if self.confirmed:
            return
        if self.asking is not None:
            self.asking.tick(button, new)
            if self.asking.chosen is not None:
                if self.asking.chosen == 0:
                    self.confirmed = True
                self.asking = None
            return
        if self.angle % 6:
            self.turn(self.direction)
            return
        self.angle = self.minutes * 6
        if button == "A" and new:
            yes_no = ScreenState(**{**self.base.__dict__, "ui": MenuView(kind="yes_no", options=("YES", "NO"), cursor=1)})
            self.asking = MenuModel(yes_no)
            self.asked += 1
            return
        self.direction = {"Left": -1, "Right": 1}.get(button or "", 0)
        if self.direction:
            self.speed = min(self.speed + 1, 0xFF)
            self.turn(self.direction)
            total = (self.hours * 60 + self.minutes + self.direction) % 1440
            self.hours, self.minutes = divmod(total, 60)
        else:
            self.speed = 0

    direction = 0

    def turn(self, direction: int) -> None:
        delta = self.delta(self.speed)
        if direction > 0:
            self.angle = self.angle + delta if self.angle < 360 - delta else 0
        elif direction < 0:
            self.angle = self.angle - delta if self.angle else 360 - delta

    def screen(self) -> ScreenState:
        if self.confirmed:
            return ScreenState(**{**self.base.__dict__, "ui": None})
        if self.asking is not None:
            return self.asking.screen()
        ui = MenuView(**{**self.base.ui.__dict__, "hours": self.hours, "minutes": self.minutes, "accepts_input": self.angle % 6 == 0})
        return ScreenState(**{**self.base.__dict__, "ui": ui})


class QuantityModel(Model):
    """`src/menu_helpers.c` AdjustQuantityAccordingToDPadInput: Up +1, Down -1, Right +10, Left -10, between 1
    and the maximum (wrapping by one at the ends); A takes the number."""

    def __init__(self, start: ScreenState, maximum: int) -> None:
        self.base = start
        self.quantity = start.ui.quantity
        self.maximum = maximum
        self.taken: int | None = None

    def press(self, button: str) -> None:
        if self.taken is not None:
            return
        q, m = self.quantity, self.maximum
        if button == "Up":
            q = 1 if q == m else q + 1
        elif button == "Down":
            q = m if q == 1 else q - 1
        elif button == "Right":
            q = min(q + 10, m)
        elif button == "Left":
            q = max(q - 10, 1)
        elif button == "A":
            self.taken = q
        self.quantity = q

    def screen(self) -> ScreenState:
        if self.taken is not None:
            return ScreenState(**{**self.base.__dict__, "ui": None})
        ui = MenuView(**{**self.base.ui.__dict__, "quantity": self.quantity, "max_quantity": self.maximum})
        return ScreenState(**{**self.base.__dict__, "ui": ui})


# ------------------------------------------------------------------------------------------- tests
class FrameworkFreeTests(unittest.TestCase):
    @staticmethod
    def foreign_imports(source: str) -> list[str]:
        bad = []
        for node in ast.walk(ast.parse(source)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            bad += [n for n in names if n.split(".")[0] in ("modules", "plugins", "mgba") or n.startswith("ai_player.host")]
        return bad

    def test_step2_files_import_no_framework_and_no_host(self) -> None:
        for relative in FRAMEWORK_FREE:
            self.assertEqual(self.foreign_imports((PACKAGE / relative).read_text(encoding="utf-8")), [], relative)

    def test_fault_a_planted_import_is_caught(self) -> None:
        source = (PACKAGE / "hands" / "menus.py").read_text(encoding="utf-8")
        self.assertTrue(self.foreign_imports(source + "\nfrom modules.menuing import scroll_to_item\n"))
        self.assertTrue(self.foreign_imports(source + "\nfrom ai_player.host.eyes import FrameworkEyes\n"))


class ScreenReadTests(unittest.TestCase):
    #: `sMenu` read live at the gender menu (2026-10-07, scratch probe of a fresh New Game): cursorPos 0, max 1.
    GENDER_SMENU = bytes.fromhex("000100000101010010000000")

    def test_menus_from_their_tasks(self) -> None:
        data = bytes(32)
        ui = read_ui("MAIN_MENU", {"Task_NewGameBirchSpeech_ChooseGender": data}, {"menu": self.GENDER_SMENU})
        self.assertEqual((ui.kind, ui.options, ui.cursor, ui.accepts_input), ("gender", ("BOY", "GIRL"), 0, True))
        moved = bytearray(self.GENDER_SMENU)
        moved[2] = 1
        self.assertEqual(read_ui("MAIN_MENU", {"Task_NewGameBirchSpeech_ChooseGender": data}, {"menu": bytes(moved)}).cursor, 1)
        # a script's yes/no ignores input until its tRight (data[2]) reaches 5
        early = (3).to_bytes(2, "little").rjust(6, b"\0") + bytes(26)
        late = (5).to_bytes(2, "little").rjust(6, b"\0") + bytes(26)
        self.assertFalse(read_ui("OVERWORLD", {"Task_HandleYesNoInput": early}, {"menu": self.GENDER_SMENU}).accepts_input)
        self.assertTrue(read_ui("OVERWORLD", {"Task_HandleYesNoInput": late}, {"menu": self.GENDER_SMENU}).accepts_input)
        main = (0).to_bytes(2, "little") + (1).to_bytes(2, "little") + bytes(28)
        ui = read_ui("MAIN_MENU", {"Task_HandleMainMenuInput": main}, {})
        self.assertEqual((ui.kind, ui.options, ui.cursor), ("main_menu", ("NEW GAME", "OPTION"), 1))
        clock = (6 * 30).to_bytes(2, "little") + bytes(2) + (21).to_bytes(2, "little") + (30).to_bytes(2, "little") + bytes(24)
        ui = read_ui("UNKNOWN", {"Task_SetClock_HandleInput": clock}, {})
        self.assertEqual((ui.kind, ui.hours, ui.minutes, ui.accepts_input), ("clock", 21, 30, True))
        turning = (6 * 30 + 2).to_bytes(2, "little") + clock[2:]
        self.assertFalse(read_ui("UNKNOWN", {"Task_SetClock_HandleInput": turning}, {}).accepts_input)
        naming = {"state": 2, "page": 2, "x": 3, "y": 1, "text": "Ro", "max_chars": 7, "input_enabled": True}
        ui = read_ui("NAMING_SCREEN", {"Task_NamingScreen": data}, {"naming": naming})
        self.assertEqual((ui.kind, ui.page, ui.cursor_xy, ui.text, ui.accepts_input), ("naming", "lower", (3, 1), "Ro", True))
        self.assertFalse(read_ui("NAMING_SCREEN", {"Task_NamingScreen": data}, {"naming": {**naming, "state": 4}}).accepts_input)
        self.assertEqual(read_ui("TITLE_SCREEN", {"Task_Scene1_WaterDrops": data}, {}).kind, "intro_movie")
        self.assertIsNone(read_ui("TITLE_SCREEN", {}, {}))  # the copyright screen runs no task
        self.assertIsNone(read_ui("OVERWORLD", {"Task_WeatherMain": data}, {}))

    def test_the_recorded_screens_rebuild(self) -> None:
        seen = {r["screen"]["ui"]["kind"] for b in ("intro", "clock", "mart", "nurse") for r in recorded(b) if r["screen"]["ui"]}
        self.assertTrue({"intro_movie", "title", "main_menu", "gender", "naming", "yes_no", "clock", "mart_menu",
                         "mart_buy", "mart_quantity"} <= seen, seen)
        for record in recorded("clock"):
            self.assertIsInstance(screen_from(record["screen"]), ScreenState)

    def test_decode_and_page(self) -> None:
        # "Hi!\pOK\nyes$": the paragraph is kept as PARAGRAPH, the line break is a space, EOS stops
        raw = bytes([0xC2, 0xDD, 0xAB, 0xFB, 0xC9, 0xC5, 0xFE, 0xED, 0xD9, 0xE7, 0xFF, 0xBB])
        self.assertEqual(decode_text(raw), f"Hi!{PARAGRAPH}OK yes")
        self.assertEqual(decode_text(bytes([0xFC, 0x01, 0x02, 0xBB, 0xFD, 0x01, 0xBC, 0xFF])), "AB")  # colour code, placeholder
        self.assertEqual(page_text(f"one{PARAGRAPH}two"), "two")

    def test_the_page_of_a_recorded_clear_wait(self) -> None:
        wait = find(recorded("intro"), lambda r: r["screen"]["waits_for_button"] and "text printer" in (r["screen"]["wait_reason"] or ""))
        text = wait["screen"]["text"]
        self.assertTrue(text.endswith(PARAGRAPH), text)
        self.assertEqual(page_text(text), "Hi! Sorry to keep you waiting!")
        # FAULT: the rule before its fix (no trailing break dropped) reads that page as EMPTY
        self.assertEqual(text.rsplit(PARAGRAPH, 1)[-1].strip(), "")

    def test_keys_are_the_decomps(self) -> None:
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,-/":
            page, x, y = key_position(char)
            self.assertEqual(KEYBOARD_PAGES[page][y][x], char)
            self.assertLess(x, KEYBOARD_COLUMNS[page])
        self.assertEqual(key_position("R"), ("upper", 5, 2))  # sKeyboardChars "MNOPQRS " row 2
        self.assertEqual(key_position("o"), ("lower", 2, 2))

    def test_task_waits(self) -> None:
        self.assertEqual(task_wait({"Task_NewGameBirchSpeech_WaitPressBeforeNameChoice"}),
                         "task Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (A or B)")
        self.assertIsNone(task_wait({"Task_NewGameBirchSpeech_ChooseGender", "Task_WeatherMain"}))

    def test_a_followed_pointer_is_range_checked_before_any_read(self) -> None:
        """`host/eyes.py` _rom_bytes / _ewram_bytes: the framework's `read_bytes` does not bound a cartridge read,
        and a garbage pointer there killed the process (an access violation, the first run of the step-2 eyes:
        the naming screen's template pointer while it was set up). Out of range: refused BEFORE the emulator is
        touched (here there is no emulator at all: an in-range pointer reaches it and fails on the missing one)."""
        from ai_player.host import eyes as host_eyes

        for address, length in ((0xFFFFFFFF, 1), (0x09000000, 4), (0x08FFFFFE, 4), (0x0203FFFF, 4), (0x00000000, 1)):
            with self.assertRaisesRegex(RuntimeError, "not a cartridge pointer"):
                host_eyes._rom_bytes(address, length)
        for address in (0x08000000, 0x03000000, 0x02040000):
            with self.assertRaisesRegex(RuntimeError, "not an EWRAM pointer"):
                host_eyes._ewram_bytes(address, 4)
        with self.assertRaises(AttributeError):  # in range: it goes on to the (absent) emulator
            host_eyes._rom_bytes(0x08000000, 4)


class PadTests(unittest.TestCase):
    def pad(self, seed: int = 1) -> tuple[Pad, list]:
        records: list = []
        return Pad(FakeControls(DialogueModel(["x"])), random.Random(seed), lambda *a: records.append(a)), records

    def test_a_press_needs_a_gate(self) -> None:
        pad, _ = self.pad()
        with self.assertRaises(PadError):
            drive(pad.press("A", "why", ""))
        with self.assertRaises(PadError):
            drive(pad.idle(5, ""))

    def test_reading_delay_is_bounded_and_grows_with_the_text(self) -> None:
        pad, _ = self.pad()
        short = [pad.reading_frames(5) for _ in range(50)]
        long = [pad.reading_frames(60) for _ in range(50)]
        self.assertTrue(all(HUMAN_PACING.read_base <= f <= HUMAN_PACING.read_max for f in short + long))
        self.assertLess(sum(short) / 50, sum(long) / 50)
        self.assertEqual(pad.reading_frames(10_000), HUMAN_PACING.read_max)

    def test_jitter_is_seeded(self) -> None:
        def presses(seed: int) -> list:
            pad, _ = self.pad(seed)
            for _ in range(5):
                drive(pad.press("A", "w", "g"))
            return [(p["hold"], p["gap"]) for p in pad.history]

        self.assertEqual(presses(3), presses(3))
        self.assertNotEqual(presses(3), presses(4))
        self.assertTrue(all(3 <= h <= 7 and 8 <= g <= 18 for h, g in presses(3)))


class DialogueTests(unittest.TestCase):
    def pages(self) -> list[str]:
        """The nurse's pages as the eyes READ them (recorded), then her question (a yes/no follows)."""
        texts = [page_text(r["screen"]["text"]) for r in recorded("nurse") if r["screen"]["waits_for_button"]
                 and "text printer" in (r["screen"]["wait_reason"] or "")]
        return texts[:2]

    def test_a_only_on_waits_and_never_on_the_choice(self) -> None:
        pages = self.pages()
        self.assertEqual(pages[0], "Hello, and welcome to the POKéMON CENTER.")
        model = DialogueModel(pages)
        hands = rig(model)
        outcome = drive(advance(hands, lambda look: False, "test"))
        self.assertEqual(outcome, "menu:yes_no")
        self.assertEqual([state for _, button, state in model.presses], ["waiting", "waiting"])
        self.assertIsNone(model.chosen)

    def test_each_page_is_read_after_it_has_printed(self) -> None:
        """HUMAN PACE, and what advance()'s FIRST wait check (on the look that starts the reading) carries: the
        reading delay before each A STARTS on a look where the page has finished printing, and it is the delay for
        that WHOLE page. Without that check the driver "reads" a page while it is still printing, its delay runs
        out over a half-printed page, and its A comes as soon as the page completes (`gates/revert_step2.py`
        H2-outer is caught here, and only here: A still never lands while printing, the gate's own check
        refuses that)."""
        pages = self.pages()
        model = DialogueModel(pages)
        recorder = Recorder()
        hands = rig(model, actions=recorder)
        self.assertEqual(drive(advance(hands, lambda look: False, "test")), "menu:yes_no")
        reads = [r for r in recorder.records if r["decision"] == "idle" and r["reason"].startswith("reading ")]
        self.assertEqual([page for _, page in model.advanced], [0, 1])
        for frame, page in model.advanced:
            before = [r for r in reads if r["extra"]["pad_frame"] < frame]
            self.assertTrue(before, f"no reading delay before the A on page {page}")
            last = before[-1]
            self.assertGreaterEqual(last["extra"]["pad_frame"], model.completed[page],
                                    f"page {page}: the reading began at frame {last['extra']['pad_frame']}, before the page "
                                    f"finished printing at {model.completed[page]}")
            self.assertTrue(last["reason"].startswith(f"reading {len(pages[page])} new characters"), last["reason"])

    def test_fault_ungated_a_presses_while_printing_and_picks_the_default(self) -> None:
        model = DialogueModel(self.pages(), default=0)
        hands = rig(model, Faults(ungated_a=True))
        drive(advance(hands, lambda look: look.screen.ui is None and model.state() == "done", "test"))
        states = [state for _, _, state in model.presses]
        self.assertIn("printing", states)
        self.assertIn("choice", states)
        self.assertEqual(model.chosen, 0)  # the default, not a choice by intent
        self.assertTrue(all(p["gate"] == UNGATED_GATE for p in hands.pad.history))


class YesNoTests(unittest.TestCase):
    def clock_question(self) -> ScreenState:
        return screen_from(find(recorded("clock"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "yes_no")["screen"])

    def test_the_clock_question_opens_on_no_and_the_ai_says_yes(self) -> None:
        start = self.clock_question()
        self.assertEqual(start.ui.cursor, 1)  # recorded: "Is this the correct time?" opens on NO
        model = MenuModel(start)
        hands = rig(model)
        self.assertTrue(drive(answer_yes_no(hands, True, "test")))
        self.assertEqual(model.chosen, 0)
        buttons = [p["button"] for p in hands.pad.history]
        self.assertEqual(buttons, ["Up", "A"])
        self.assertIn("cursor on 0 (YES)", hands.pad.history[-1]["gate"])

    def test_fault_blind_count_says_no(self) -> None:
        model = MenuModel(self.clock_question())
        hands = rig(model, Faults(blind_count=True))
        drive(answer_yes_no(hands, True, "test"))
        self.assertEqual(model.chosen, 1)  # NO: the count assumed the cursor started on YES
        self.assertEqual(hands.pad.history[-1]["gate"], BLIND_GATE)

    def test_nothing_is_pressed_during_the_input_delay(self) -> None:
        start = screen_from(find(recorded("nurse"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "yes_no")["screen"])
        self.assertFalse(start.ui.accepts_input)  # recorded: the first frames of the script's yes/no
        model = MenuModel(start, delay=5)
        hands = rig(model)
        self.assertTrue(drive(answer_yes_no(hands, True, "test")))
        self.assertEqual(model.chosen, 0)
        first_press = hands.pad.history[0]
        self.assertGreaterEqual(first_press["at"], 5)


class CursorTests(unittest.TestCase):
    def test_gender_by_reading_the_cursor(self) -> None:
        start = screen_from(find(recorded("intro"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "gender")["screen"])
        for want, index in (("GIRL", 1), ("BOY", 0)):
            model = MenuModel(start)
            self.assertTrue(drive(choose(rig(model), "gender", want, "test")))
            self.assertEqual(model.chosen, index)

    def test_a_menu_whose_cursor_starts_elsewhere(self) -> None:
        start = screen_from(find(recorded("mart"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "mart_menu"
                                 and r["screen"]["ui"]["cursor"] == 1)["screen"])
        self.assertEqual(start.ui.options[start.ui.cursor], "SELL")  # recorded: on its way to QUIT after a purchase
        model = MenuModel(start)
        self.assertTrue(drive(choose(rig(model), "mart_menu", "BUY", "test")))
        self.assertEqual(model.options[model.chosen], "BUY")
        blind = MenuModel(start)
        drive(choose(rig(blind, Faults(blind_count=True)), "mart_menu", "BUY", "test"))
        self.assertEqual(blind.options[blind.chosen], "SELL")  # FAULT: 0 presses "from the top", A on SELL

    def mart_menu_on_sell(self) -> ScreenState:
        return screen_from(find(recorded("mart"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "mart_menu"
                                and r["screen"]["ui"]["cursor"] == 1)["screen"])

    def test_the_press_gate_is_its_own_look(self) -> None:
        """choose() presses A only when ITS OWN look shows the cursor on the option, not on move_cursor's word.
        In the shipped code move_cursor's last look and the gate's look are the SAME frame, so the gate's cursor
        check is redundant WITH move_cursor (`gates/revert_step2.py` H3 is caught only here). This test hands
        choose() a move_cursor that answers True without moving anything (a future change between the two
        looks, a misread) and shows that no A lands on the option the cursor is really on."""
        model = MenuModel(self.mart_menu_on_sell())

        def says_it_moved(hands, kind, target, why):
            yield from ()
            return True

        hands = rig(model)
        with mock.patch("ai_player.hands.menus.move_cursor", says_it_moved):
            self.assertFalse(drive(choose(hands, "mart_menu", "BUY", "test")))
        self.assertIsNone(model.chosen, f"A chose {model.options[model.chosen] if model.chosen is not None else None}")
        self.assertNotIn("A", [p["button"] for p in hands.pad.history])

    def test_move_cursor_waits_for_input_by_itself(self) -> None:
        """move_cursor presses nothing while the menu ignores input (a script yes/no's first 5 frames,
        `Task_HandleYesNoInput`: the nurse's, recorded in that delay). Inside choose() this check is redundant:
        choose() waited for input first (`wait_for_ui`) and no step-2 menu takes it away again, so
        `gates/revert_step2.py` H9 is caught only here. move_cursor is public and does not assume its caller
        waited: called directly on the delayed menu, it waits, then ONE Down reaches NO; nothing is dropped."""
        start = screen_from(find(recorded("nurse"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "yes_no")["screen"])
        self.assertFalse(start.ui.accepts_input)
        model = MenuModel(start, delay=5)
        hands = rig(model)
        self.assertTrue(drive(move_cursor(hands, "yes_no", 1, "test")))
        self.assertEqual(model.cursor, 1)
        self.assertEqual(model.dropped, 0, "a press landed in the input delay and the game dropped it")
        self.assertEqual([p["button"] for p in hands.pad.history], ["Down"])


class KeyboardTests(unittest.TestCase):
    def start(self, test) -> ScreenState:
        return screen_from(find(recorded("intro"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "naming" and test(r["screen"]["ui"]))["screen"])

    def test_types_rosa_from_the_opening_keyboard(self) -> None:
        start = self.start(lambda ui: ui["accepts_input"] and ui["text"] == "" and ui["page"] == "upper")
        model = KeyboardModel(start)
        self.assertTrue(drive(type_name(rig(model), "Rosa", "test")))
        self.assertTrue(model.closed)
        self.assertEqual(model.text, "Rosa")

    def test_types_rosa_from_a_cursor_left_mid_name(self) -> None:
        start = self.start(lambda ui: ui["text"] == "Ro" and ui["accepts_input"])
        self.assertNotEqual(start.ui.cursor_xy, (0, 0))
        model = KeyboardModel(start)
        self.assertTrue(drive(type_name(rig(model), "Rosa", "test")))
        self.assertEqual(model.text, "Rosa")

    def test_a_wrong_letter_is_deleted_with_b(self) -> None:
        """The text is READ after every press, and whatever is not how the name begins is deleted with B. Two ways
        it happens: a slipped press leaves a letter that is not the name's next one ('Rox' on the recorded
        mid-name keyboard), and a keyboard OPENS with text in it (the decomp has one: `src/naming_screen.c`
        sWaldaWordsScreenTemplate `.copyExistingString = TRUE`; the player's, a box's and a Pokemon's are FALSE,
        so v1 meets only the slip). The AI deletes exactly the letters that do not fit (1, then 3) and types
        'Rosa'. Without the check (`gates/revert_step2.py` H5) the AI types on after the wrong letters."""
        start = self.start(lambda ui: ui["text"] == "Ro" and ui["accepts_input"])
        for text, deletes in (("Rox", 1), ("Kai", 3)):
            ui = MenuView(**{**start.ui.__dict__, "text": text})
            model = KeyboardModel(ScreenState(**{**start.__dict__, "ui": ui}))
            hands = rig(model)
            self.assertTrue(drive(type_name(hands, "Rosa", "test")), text)
            self.assertEqual(model.text, "Rosa", text)
            deleted = [p for p in hands.pad.history if p["button"] == "B"]
            self.assertEqual(len(deleted), deletes, text)
            self.assertTrue(all("B deletes a letter" in p["gate"] for p in deleted), [p["gate"] for p in deleted])

    def test_fault_blind_count_types_the_wrong_name(self) -> None:
        start = self.start(lambda ui: ui["accepts_input"] and ui["text"] == "" and ui["page"] == "upper")
        model = KeyboardModel(start)
        drive(type_name(rig(model, Faults(blind_count=True)), "Rosa", "test"))
        self.assertTrue(model.text.startswith("R"))  # the first key: the cursor really was on the top-left key
        self.assertNotEqual(model.text, "Rosa")  # then it starts on the previous key, not the top-left one


class ClockTests(unittest.TestCase):
    def test_hold_frames_follow_the_decomp(self) -> None:
        self.assertEqual(clock_hold_frames(10), 60)
        self.assertEqual(clock_hold_frames(30), 120)
        self.assertEqual(clock_hold_frames(60), 180)
        self.assertEqual(clock_hold_frames(100), 220)
        model = ClockModel(screen_from(find(recorded("clock"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "clock")["screen"]))
        for _ in range(clock_hold_frames(45)):
            model.tick("Right", False)
        while model.angle % 6:
            model.tick(None, False)
        self.assertEqual(model.hours * 60 + model.minutes - 600, 45)  # the model agrees: 45 minutes from 10:00

    def test_sets_the_time_and_says_yes(self) -> None:
        start = screen_from(find(recorded("clock"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "clock")["screen"])
        self.assertEqual((start.ui.hours, start.ui.minutes), (10, 0))  # recorded: the clock opens at 10:00
        model = ClockModel(start)
        self.assertTrue(drive(set_clock(rig(model), 21, 47, "test")))
        self.assertTrue(model.confirmed)
        self.assertEqual((model.hours, model.minutes), (21, 47))

    def test_fault_blind_count_never_confirms(self) -> None:
        start = screen_from(find(recorded("clock"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "clock")["screen"])
        model = ClockModel(start)
        self.assertFalse(drive(set_clock(rig(model, Faults(blind_count=True)), 21, 47, "test")))
        self.assertFalse(model.confirmed)
        self.assertGreater(model.asked, 1)  # asked again and again, answered NO each time


class QuantityTests(unittest.TestCase):
    def test_reads_the_quantity(self) -> None:
        start = screen_from(find(recorded("mart"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "mart_quantity")["screen"])
        self.assertEqual(start.ui.quantity, 1)
        for want in (5, 23):
            model = QuantityModel(start, maximum=33)
            hands = rig(model)
            self.assertTrue(drive(set_quantity(hands, want, "test")))
            self.assertEqual(model.taken, want)
        self.assertIn("Right", [p["button"] for p in hands.pad.history])


class TalkTests(unittest.TestCase):
    class Person(Model):
        def __init__(self, busy_frames: int) -> None:
            self.busy = busy_frames
            self.talked_at: int | None = None
            self.facing = "left"
            self.presses: list[tuple[int, str, bool]] = []

        def press(self, button: str) -> None:
            self.presses.append((self.frame, button, self.busy > 0))
            if button == "Up":
                self.facing = "up"
            if button == "A" and self.busy == 0 and self.talked_at is None:
                self.talked_at = self.frame

        def step(self, held: str | None) -> None:
            if self.busy:
                self.busy -= 1

        def screen(self) -> ScreenState:
            if self.talked_at is not None:
                return overworld_screen(screen="text", text_box_open=True, script_running=True, controls_locked=True)
            return overworld_screen(script_running=self.busy > 0, controls_locked=self.busy > 0)

        def player(self) -> PlayerState:
            return PlayerState(map_group=0, map_number=0, map_name="TEST", map_const="TEST", x=5, y=5, facing=self.facing,
                               movement="walking", elevation=3, avatar_flags=0, trainer_id=1)

        def view(self) -> View:
            nurse = SeenObject(kind="npc", x=5, y=3, dx=0, dy=-2, local_id=1, graphics_id=58, facing="down", elevation=3,
                               source="object")
            counter = Tile(x=5, y=4, dx=0, dy=-1, metatile=1, behavior=0x80, behavior_name="COUNTER", collision=1, elevation=3,
                           blocked=True, water=False, encounter=None, tall_grass=False, ledge=None, door=False, warp=False,
                           half_visible=False)
            floor = Tile(x=5, y=5, dx=0, dy=0, metatile=1, behavior=0, behavior_name="NORMAL", collision=0, elevation=3,
                         blocked=False, water=False, encounter=None, tall_grass=False, ledge=None, door=False, warp=False,
                         half_visible=False)
            rows = tuple(tuple(counter if (dx, dy) == (0, -1) else floor for dx in range(-7, 8)) for dy in range(-5, 6))
            return View(left=7, right=7, up=5, down=5, rows=rows, objects=(nurse,), cropped=True)

    def test_no_a_while_a_script_runs(self) -> None:
        model = self.Person(busy_frames=80)
        hands = rig(model)
        nurse = model.view().objects[0]
        self.assertTrue(drive(talk(hands, nurse, "test")))
        a_presses = [p for p in model.presses if p[1] == "A"]
        self.assertEqual(len(a_presses), 1)
        self.assertFalse(a_presses[0][2], "A was pressed while a script was running")
        self.assertEqual(model.facing, "up")  # it turned to face the nurse across the counter first
        self.assertFalse(player_free(observation(model.screen(), model.frame, model.player(), model.view())))

    def test_fault_without_the_free_check_a_lands_on_the_running_script(self) -> None:
        model = self.Person(busy_frames=80)
        hands = rig(model)
        nurse = model.view().objects[0]
        with mock.patch("ai_player.hands.dialogue.player_free", lambda look: True):
            drive(talk(hands, nurse, "test"))
        self.assertTrue(any(button == "A" and busy for _, button, busy in model.presses))


class SceneTests(unittest.TestCase):
    """STEP 2.1 (the step-2 verifier: 530 frames of Birch's opening logged under the catch-all "the game is busy
    (main_menu)"): what the AI watches while it stands still has a NAME (`eyes/screens.py` scene_of, the fade
    `ScreenState.fading`, `hands/dialogue.py` busy_reason). The catch-all is left for a screen no table names."""

    @staticmethod
    def reason(**changes) -> str:
        base = dict(game_state="MAIN_MENU", screen="menu", menu="main_menu", text_box_open=False, waits_for_button=False,
                    in_battle=False)
        base.update(changes)
        return busy_reason(observation(ScreenState(**base), 1))

    def test_scene_lookup_order(self) -> None:
        # the main callback first: back from the clock the MAP loads, though the clock's exit task still runs
        self.assertEqual(scene_of("UNKNOWN", {"Task_SetClock_Exit"}, "CB2_ReturnToFieldLocal"), "the map loading")
        self.assertEqual(scene_of("UNKNOWN", {"Task_SetClock_WaitFadeIn"}, None), "the wall clock")
        # the stretch the verifier named: Birch's opening timer (src/main_menu.c Task_NewGameBirchSpeech_WaitToShowBirch)
        self.assertEqual(scene_of("MAIN_MENU", {"Task_NewGameBirchSpeech_WaitToShowBirch"}, None), "Professor Birch's speech")
        self.assertEqual(scene_of("UNKNOWN", set(), "NULL"), "the game starting up")
        self.assertEqual(scene_of("TITLE_SCREEN", set(), None), SCENE_STATES["TITLE_SCREEN"])
        self.assertIsNone(scene_of("UNKNOWN", {"Task_WeatherMain"}, None))

    def test_busy_names_what_it_watches(self) -> None:
        birch = scene_of("MAIN_MENU", {"Task_NewGameBirchSpeech_WaitToShowBirch"}, None)
        self.assertEqual(self.reason(scene=birch),
                         "watching: Professor Birch's speech (it runs by itself: nothing on screen takes a press now)")
        self.assertEqual(self.reason(scene=birch, fading=True), "watching: the screen fades (Professor Birch's speech)")
        self.assertEqual(self.reason(fading=True), "watching: the screen fades (main_menu)")
        # the earlier rules still come first
        self.assertEqual(self.reason(scene=birch, text="Hi"), "reading along: a text is printing")
        self.assertEqual(self.reason(scene=birch, ui=MenuView(kind="gender", accepts_input=False)),
                         "watching: the gender is not taking input yet")
        self.assertEqual(self.reason(scene=birch, screen="transition"), "watching: the screen changes")
        # the FAULT half: with no scene and no fade it IS the catch-all (what the verifier saw), which live_step2 fails
        self.assertTrue(self.reason().startswith(GENERIC_BUSY))

    def test_every_stretch_measured_under_the_catch_all_has_a_scene(self) -> None:
        """(game state, tasks, main callback) of each stretch the four skills stood still under the catch-all before
        step 2.1 (measured 2026-10-07 with a spy on busy_reason, seed 3: the intro, the nurse, the mart, the clock)."""
        stretches = [
            ("UNKNOWN", set(), "NULL"), ("TITLE_SCREEN", set(), None),
            ("MAIN_MENU", {"Task_MainMenuCheckSaveFile"}, None), ("MAIN_MENU", {"Task_MainMenuCheckBattery"}, None),
            ("MAIN_MENU", {"Task_DisplayMainMenu"}, None), ("MAIN_MENU", {"Task_HandleMainMenuAPressed"}, None),
            ("MAIN_MENU", {"Task_NewGameBirchSpeech_Init"}, None), ("MAIN_MENU", {"Task_NewGameBirchSpeech_WaitToShowBirch"}, None),
            ("MAIN_MENU", {"Task_NewGameBirchSpeech_WaitForSpriteFadeInWelcome"}, None),
            ("MAIN_MENU", {"Task_NewGameBirchSpeechSub_WaitForLotad", "Task_NewGameBirchSpeech_SlidePlatformAway"}, None),
            ("UNKNOWN", {"Task_HandleInput", "Task_UpdateButtonFlash"}, "CB2_NewGameBirchSpeech_ReturnFromNamingScreen"),
            ("MAIN_MENU", {"Task_NewGameBirchSpeech_Cleanup"}, None), ("UNKNOWN", {"Task_MuddySlope", "Task_WeatherInit"}, "CB2_NewGame"),
            ("UNKNOWN", set(), "CB2_InitBuyMenu"), ("UNKNOWN", {"ListMenuDummyTask", "Task_ExitBuyMenu"}, "CB2_BuyMenu"),
            ("UNKNOWN", set(), "CB2_ReturnToField"), ("UNKNOWN", set(), "CB2_ReturnToFieldLocal"),
            ("UNKNOWN", set(), "CB2_StartWallClock"), ("UNKNOWN", {"Task_SetClock_WaitFadeIn"}, "CB2_WallClock"),
            ("UNKNOWN", {"Task_SetClock_Exit"}, "ReturnFromStartWallClock"),
            ("UNKNOWN", {"Task_SetClock_Exit"}, "CB2_ReturnToFieldContinueScriptPlayMapMusic"),
            # BUILD STEP 5 (measured 2026-10-14 with `probe_callbacks` from a RESCUED_BIRCH state): the starter choice
            ("CHOOSE_STARTER", {"Task_MuddySlope", "Task_WeatherMain"}, "CB2_ChooseStarter"),
            ("CHOOSE_STARTER", {"Task_DuckBGMForPokemonCry", "Task_HandleConfirmStarterInput"}, "CB2_StarterChoose"),
            ("UNKNOWN", {"Task_DuckBGMForPokemonCry", "Task_HandleConfirmStarterInput"}, "CB2_GiveStarter"),
            ("UNKNOWN", {"Task_BattleTransition", "Task_Blur"}, "CB2_StartFirstBattle"),
        ]
        for state, tasks, callback in stretches:
            self.assertIsNotNone(scene_of(state, tasks, callback), (state, tasks, callback))

    def test_a_settling_position_is_named(self) -> None:
        """BUILD STEP 5 (measured 2026-10-14): a ledge jump's landing and a map edge crossed leave the position settling
        for a frame with nothing else on screen; that frame is named, and a settled player with nothing on screen is
        still the catch-all (the FAULT half)."""
        settling = PlayerState(map_group=0, map_number=0, map_name="TEST", map_const="TEST", x=None, y=None,
                               facing="down", movement="walking", elevation=3, avatar_flags=1, trainer_id=1,
                               settling=True)
        self.assertEqual(busy_reason(observation(overworld_screen(), 1, settling)),
                         "watching: the player's move finishing (a jump, a map's edge: the position settles)")
        settled = PlayerState(map_group=0, map_number=0, map_name="TEST", map_const="TEST", x=5, y=5,
                              facing="down", movement="walking", elevation=3, avatar_flags=1, trainer_id=1)
        self.assertTrue(busy_reason(observation(overworld_screen(), 1, settled)).startswith(GENERIC_BUSY))

    def test_every_scene_callback_is_a_symbol_of_the_rom(self) -> None:
        """`host/eyes.py` resolves each SCENE_CALLBACKS name with `get_symbol` and SKIPS one the ROM does not name, so a
        misspelt name would fall back silently: each must resolve. FAULT half: a misspelt one raises."""
        from modules.context import context
        from modules.game import get_symbol, set_rom
        from modules.profiles import load_profile_by_name

        if getattr(context, "rom", None) is None:
            profile = load_profile_by_name("ai-step0-fixture")
            context.profile = profile
            set_rom(profile.rom)
        for name in SCENE_CALLBACKS:
            if name != "NULL":
                self.assertGreater(get_symbol(name)[0], 0, name)
        with self.assertRaises(RuntimeError):
            get_symbol("CB2_ReturnToFieldLocall")


class PressKindTests(unittest.TestCase):
    """STEP 2.1: the A-press classes `gates/live_step2.py` checks on every real launcher arm (`classify_a`, over
    `probe_presses.gate_kind`), on digests as the action log writes them (copied from the step-2 evidence), each
    with its FAULT half."""

    def test_the_classes_and_their_faults(self) -> None:
        from ai_player.gates.live_step2 import classify_a
        from ai_player.gates.probe_presses import gate_kind

        def press(gate: str, digest: str) -> tuple[str, bool]:
            return classify_a({"reason": gate, "digest": digest})

        wait = "f1213 menu menu=main_menu waits=A/B(text printer 0 CLEAR) party=? cost=0.20ms"
        self.assertEqual(press("text printer 0 CLEAR", wait), ("wait", True))
        self.assertEqual(press("text printer 0 WAIT", wait), ("wait", False))  # the look waited for another reason
        task = "f5587 menu menu=main_menu waits=A/B(task Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (A or B)) party=?"
        self.assertEqual(press("task Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (A or B)", task), ("wait", True))
        yes = "f6233 menu menu=main_menu ui=yes_no[YES] party=? cost=0.21ms"
        self.assertEqual(press("yes_no cursor on 0 (YES)", yes), ("menu", True))
        self.assertEqual(press("yes_no cursor on 0 (YES)", yes.replace("ui=yes_no[", "ui=yes_no(busy)[")), ("menu", False))
        self.assertEqual(press("gender cursor on 1 (GIRL)", yes), ("menu", False))  # another menu is open
        self.assertEqual(press("yes_no cursor on 0 (YES)", wait), ("menu", False))  # no menu, a text waits
        key = "f5757 menu menu=naming ui=naming[upper at (5, 2) text=''] dex=0/0 money=0 badges=0 problems=1"
        self.assertEqual(press("keyboard: cursor on 'R' at (5,2) of the upper page", key), ("menu", True))
        self.assertEqual(press("mart_quantity reads x5, the number wanted", "f1 other ui=mart_quantity[x5 max 33] X"), ("menu", True))
        self.assertEqual(press("clock reads 13:37, the time wanted", "f1 other ui=clock[13:37] X"), ("menu", True))
        talk_look = "f12701 overworld LITTLEROOT TOWN(1,1) xy=(5,2) facing=up walking sees=[sign(0,-1)]"
        self.assertEqual(press("talk: facing up to the sign at (0,-1), nothing running", talk_look), ("talk", True))
        self.assertEqual(press("talk: facing up to the sign at (0,-1), nothing running",
                               talk_look.replace("overworld", "overworld waits=A/B(script waitbuttonpress)")), ("talk", False))
        self.assertEqual(press(UNGATED_GATE, wait), ("other", False))
        self.assertEqual(gate_kind("mart_buy cursor on 0 (POKé BALL)"), ("menu", "mart_buy"))
        # (the step-4 verifier's round) the battle party menu's refusal: its words WAIT over the list, which takes no input
        refusal = ("f252451 menu menu=party waits=A/B(text printer 6 WAIT) ui=party(busy)[0] ROUTE 116(0,31) xy=(36,15) "
                   "facing=up walking party=[Grovyle:L17 37/49,Nincada:L6 0/21] dex=5/17 money=7004 badges=0 cost=0.87ms")
        self.assertEqual(press("text printer 6 WAIT", refusal), ("wait", True))
        self.assertEqual(press("text printer 6 WAIT", refusal.replace("ui=party(busy)[", "ui=party[")), ("wait", False))


# ------------------------------------------------------------------------------------------- STEP 2.1: the review's items
#: The reason an overworld script gives (`busy_reason`), which an unlisted menu in a script reads as.
SCENE_REASON = "watching: a scene plays (a script runs, the controls are locked)"
#: A frozen menu: its input delay never ends (`MenuModel`), so `choose` cannot press on it.
FOREVER = 10 ** 9
#: The personality the intro tests play (seed 5, as `rig`).
PERSONALITY = Personality("Catcher", 5, "seed")


def intended(seed: int = 5) -> tuple[str, str]:
    """(gender, name) `play_intro` draws first from `rig(..., seed)`'s CHOICES stream."""
    choices = random.Random(f"{seed}:choices")
    gender, _ = choose_gender(choices, PERSONALITY)
    return gender, choose_name(choices, gender)


def person_view(graphics_id: int) -> View:
    """A person (by graphics id) two tiles up, across a COUNTER: the nurse's and the clerk's place."""
    person = SeenObject(kind="npc", x=5, y=3, dx=0, dy=-2, local_id=1, graphics_id=graphics_id, facing="down", elevation=3,
                        source="object")
    counter = Tile(x=5, y=4, dx=0, dy=-1, metatile=1, behavior=0x80, behavior_name="COUNTER", collision=1, elevation=3,
                   blocked=True, water=False, encounter=None, tall_grass=False, ledge=None, door=False, warp=False,
                   half_visible=False)
    floor = Tile(x=5, y=5, dx=0, dy=0, metatile=1, behavior=0, behavior_name="NORMAL", collision=0, elevation=3,
                 blocked=False, water=False, encounter=None, tall_grass=False, ledge=None, door=False, warp=False,
                 half_visible=False)
    rows = tuple(tuple(counter if (dx, dy) == (0, -1) else floor for dx in range(-7, 8)) for dy in range(-5, 6))
    return View(left=7, right=7, up=5, down=5, rows=rows, objects=(person,), cropped=True)


def standing(facing: str = "up", map_const: str = "TEST") -> PlayerState:
    return PlayerState(map_group=0, map_number=0, map_name="TEST", map_const=map_const, x=5, y=5, facing=facing,
                       movement="walking", elevation=3, avatar_flags=0, trainer_id=1)


class StillModel(Model):
    """A screen on which NOTHING the eyes see changes: an overworld script runs, the controls are locked, no menu, no
    text, nothing waits. An unlisted menu in a script (a list menu, a number input) looks exactly so to the eyes: the
    review's item 1. `scene` is what the eyes name (None: nothing); `changes_every` > 0 turns the player around every
    that many frames (something on screen moves)."""

    def __init__(self, scene: str | None = None, changes_every: int = 0) -> None:
        self.scene = scene
        self.changes_every = changes_every
        self.presses: list[tuple[int, str]] = []

    def press(self, button: str) -> None:
        self.presses.append((self.frame, button))

    def screen(self) -> ScreenState:
        return overworld_screen(script_running=True, controls_locked=True, scene=self.scene)

    def player(self) -> PlayerState:
        turned = self.changes_every and (self.frame // self.changes_every) % 2
        return standing("left" if turned else "up")


class StallTests(unittest.TestCase):
    """STEP 2.1, the review's item 1 (`hands/dialogue.py` advance's stall detector): an unknown prompt is reported as
    "stuck:<reason>" after STALL_FRAMES unchanged frames, not watched for the 3-minute budget under a false reason."""

    def test_an_unknown_prompt_is_stuck_after_300_frames(self) -> None:
        model = StillModel()
        hands = rig(model)
        self.assertEqual(drive(advance(hands, lambda look: False, "test")), f"{STUCK}{SCENE_REASON}")
        self.assertEqual(hands.pad.frames, STALL_FRAMES)  # not DIALOGUE_BUDGET (10,800): the pre-review "budget"
        self.assertEqual(model.presses, [])

    def test_a_scene_the_eyes_name_is_watched_longer(self) -> None:
        """While the eyes NAME what plays (the nurse's machine, Birch's opening) the AI waits STALL_FRAMES_SCENE."""
        hands = rig(StillModel(scene="the nurse healing the party"))
        self.assertEqual(drive(advance(hands, lambda look: False, "test")), f"{STUCK}{SCENE_REASON}")
        self.assertEqual(hands.pad.frames, STALL_FRAMES_SCENE)

    def test_a_screen_that_changes_is_never_stuck(self) -> None:
        """Non-vacuity: a scene in which something moves every 250 frames (less than the limit) runs 3,000 frames,
        ten times the limit, and ends "done"."""
        model = StillModel(changes_every=250)
        hands = rig(model)
        self.assertEqual(drive(advance(hands, lambda look: look.frame >= 3000, "test")), "done")
        self.assertGreaterEqual(hands.pad.frames, 3000)

    def test_the_measured_still_stretches_fit_their_limits(self) -> None:
        """MEASURED 2026-10-08 (seed 3, in-process, every busy frame of `advance` in the four step-2 skills): the
        longest stretches on which nothing the eyes see changed, with the scene the eyes named."""
        measured = {"Professor Birch's speech": 455, "the nurse healing the party": 319, "the copyright screen": 119, None: 58}
        for scene, frames in measured.items():
            limit = STALL_FRAMES_SCENE if scene is not None else STALL_FRAMES
            self.assertLess(frames, limit, scene)
        # why there are two limits: one limit of STALL_FRAMES would have stopped Birch's opening and the nurse
        self.assertGreater(measured["Professor Birch's speech"], STALL_FRAMES)
        self.assertGreater(measured["the nurse healing the party"], STALL_FRAMES)


class ReleaseControls(FakeControls):
    """`FakeControls` that records each button a hold RELEASES (the controller always releases, even when closed)."""

    def __init__(self, model: Model) -> None:
        super().__init__(model)
        self.released: list[str] = []

    def hold(self, button: str, frames: int):
        try:
            yield from super().hold(button, frames)
        finally:
            self.released.append(button)


class PadFrameTests(unittest.TestCase):
    """STEP 2.1, the review's item 3: the pad's frame count is the frames that ran, also when a skill is STOPPED in
    the middle of a press (the brain's frame budget): `gates/live_step2.py` asserts it against the instrument."""

    def test_frames_are_counted_as_they_pass(self) -> None:
        controls = ReleaseControls(DialogueModel(["x"]))
        pad = Pad(controls, random.Random(1), lambda *a: None)
        press = pad.press("A", "why", "gate", hold=6)
        for _ in range(4):  # four frames of the 6-frame hold, then the skill is stopped
            next(press)
        press.close()
        self.assertEqual(pad.frames, 4)  # before 2.1: 0 (the press was counted only once it had finished)
        self.assertEqual(controls.released, ["A"])
        drive(pad.press("B", "why", "gate", hold=5))
        self.assertEqual(pad.frames, 4 + 5 + pad.history[-1]["gap"])
        hold = pad.hold("Right", 30, "why", "gate")
        for _ in range(7):
            next(hold)
        hold.close()
        self.assertEqual(pad.frames, 4 + 5 + pad.history[-2]["gap"] + 7)
        self.assertEqual(controls.released, ["A", "B", "Right"])

    def test_the_driver_compares_the_pad_with_the_instrument(self) -> None:
        """`live_step2.check_purity`'s new check, on synthetic runs: the step-2 XBC numbers (pad 5991, instrument
        6000) fail it; equal numbers pass."""
        from ai_player.gates.live_step2 import ARMS, Run, check_purity

        def frame_check(pad_frames: int, real_frames: int) -> bool:
            run = Run(ARMS[0], ai_log=f"[AI-HANDS] outcome='x' presses=119 frames={pad_frames} looks=1 records=1\n",
                      verdict={"verdict": "CLEAN", "counters": {"real_frames": real_frames}, "facts": {}})
            check_purity(run, None)
            return next(ok for ok, text in run.checks if text.startswith("the AI pad's own frame count"))

        self.assertTrue(frame_check(6000, 6000))
        self.assertFalse(frame_check(5991, 6000))
        self.assertFalse(frame_check(11999, 12000))


class MovieModel(Model):
    """`src/intro.c` MainCB2_Intro: a NEW key ends the movie only `if (gMain.newKeys != 0 && !gPaletteFade.active)`.
    The movie fades during FADES (frame ranges); a START pressed during a fade is DROPPED; one that is taken ends the
    movie, and here the screen becomes the truck so that `play_intro` ends (what follows the movie is other tests').
    The eyes' picture of it is built by the REAL `read_ui` from the task and the fade."""

    FADES = ((0, 50), (60, 130))  # a 10-frame gap, shorter than a 'think' (14-45 frames), then a second fade

    def __init__(self) -> None:
        self.dropped = 0
        self.taken_at: int | None = None

    def fading(self) -> bool:
        return any(start <= self.frame < end for start, end in self.FADES)

    def press(self, button: str) -> None:
        if self.taken_at is not None:
            return
        if self.fading():
            self.dropped += 1
        else:
            self.taken_at = self.frame

    def screen(self) -> ScreenState:
        if self.taken_at is not None:
            return overworld_screen()
        fading = self.fading()
        ui = read_ui("TITLE_SCREEN", {"Task_Scene1_WaterDrops": bytes(32)}, {"fading": fading})
        return ScreenState(game_state="TITLE_SCREEN", screen="title", menu=None, text_box_open=False, waits_for_button=False,
                           in_battle=False, ui=ui, fading=fading, scene=SCENE_STATES["TITLE_SCREEN"])

    def player(self) -> PlayerState | None:
        return standing(map_const=TRUCK_MAP) if self.taken_at is not None else None


class FadeTests(unittest.TestCase):
    """STEP 2.1, the review's item 4: while a palette fade runs nothing takes input (`eyes/screens.py` read_ui), and
    the intro presses START only on a screen that takes it (`skills/intro.py`)."""

    def test_nothing_takes_input_while_a_fade_runs(self) -> None:
        data = bytes(32)
        main = (0).to_bytes(2, "little") + (0).to_bytes(2, "little") + bytes(28)
        for state, tasks, kind in (("TITLE_SCREEN", {"Task_Scene1_WaterDrops": data}, "intro_movie"),
                                   ("TITLE_SCREEN", {"Task_TitleScreenPhase3": data}, "title"),
                                   ("MAIN_MENU", {"Task_HandleMainMenuInput": main}, "main_menu")):
            calm = read_ui(state, tasks, {"fading": False})
            fading = read_ui(state, tasks, {"fading": True})
            self.assertEqual((calm.kind, calm.accepts_input), (kind, True))
            self.assertEqual((fading.kind, fading.accepts_input, fading.cursor), (kind, False, calm.cursor))

    def test_the_intro_waits_out_a_fade_before_start(self) -> None:
        """Against `MovieModel`: exactly one START, taken; none dropped in a fade. Without the eyes' fade rule the AI
        presses within its first 'think' (14-45 frames), inside the first fade (0-50): dropped; without the press
        gate's own input check, after the first fade it presses inside the second (60-130): dropped."""
        model = MovieModel()
        hands = rig(model)
        gender, name = intended()
        self.assertEqual(drive(play_intro(hands, PERSONALITY)), f"in the truck; intended {name} ({gender})")
        self.assertEqual(model.dropped, 0, "a START was pressed while the movie faded, and the game dropped it")
        self.assertEqual([p["button"] for p in hands.pad.history], ["Start"])
        self.assertFalse(any(start <= model.taken_at < end for start, end in MovieModel.FADES))


class GenderSlideModel(MenuModel):
    """`src/main_menu.c` Task_NewGameBirchSpeech_ChooseGender: a cursor move starts Birch's sprite slide (the tasks
    SlideOutOldGenderSprite, SlideInNewGenderSprite; SLIDE frames here), during which the menu STAYS on screen and
    ignores input. The eyes' picture is built by the REAL `read_ui` from the task that runs and `sMenu`."""

    SLIDE = 30

    def __init__(self, start: ScreenState) -> None:
        super().__init__(start)
        self.slide = 0
        self.dropped_in_slide = 0

    def press(self, button: str) -> None:
        if self.slide:
            self.dropped_in_slide += 1
            return
        before = self.cursor
        super().press(button)
        if self.chosen is None and self.cursor != before:
            self.slide = self.SLIDE

    def step(self, held: str | None) -> None:
        if self.slide:
            self.slide -= 1

    def screen(self) -> ScreenState:
        if self.chosen is not None:
            return ScreenState(**{**self.base.__dict__, "ui": None})
        task = "Task_NewGameBirchSpeech_SlideOutOldGenderSprite" if self.slide else "Task_NewGameBirchSpeech_ChooseGender"
        menu = bytearray(ScreenReadTests.GENDER_SMENU)
        menu[2] = self.cursor
        return ScreenState(**{**self.base.__dict__, "ui": read_ui("MAIN_MENU", {task: bytes(32)}, {"menu": bytes(menu)})})


class GenderSlideTests(unittest.TestCase):
    """STEP 2.1, FOUND by the review's item 6 (a failed choice now ends the skill): the gender menu stays on screen,
    NOT taking input, while Birch's sprites slide after a cursor move (`eyes/screens.py` UI_BUSY_TASKS). Before, the
    eyes said it had closed: `move_cursor` gave up after its Down, `choose` failed, and the intro's old loop chose
    again on its next turn and hid it."""

    def gender_menu(self) -> ScreenState:
        return screen_from(find(recorded("intro"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "gender")["screen"])

    def test_girl_is_chosen_through_the_slide(self) -> None:
        start = self.gender_menu()
        self.assertEqual(start.ui.cursor, 0)  # recorded: the menu opens on BOY
        model = GenderSlideModel(start)
        hands = rig(model)
        self.assertTrue(drive(choose(hands, "gender", "GIRL", "test")))
        self.assertEqual(model.chosen, 1)
        self.assertEqual(model.dropped_in_slide, 0)
        self.assertEqual([p["button"] for p in hands.pad.history], ["Down", "A"])

    def test_the_slide_reads_as_the_menu_not_taking_input(self) -> None:
        menu = bytearray(ScreenReadTests.GENDER_SMENU)
        menu[2] = 1
        for task in ("Task_NewGameBirchSpeech_SlideOutOldGenderSprite", "Task_NewGameBirchSpeech_SlideInNewGenderSprite"):
            ui = read_ui("MAIN_MENU", {task: bytes(32)}, {"menu": bytes(menu)})
            self.assertEqual((ui.kind, ui.cursor, ui.accepts_input), ("gender", 1, False), task)


class NameTailModel(Model):
    """The end of the intro: the naming keyboard (`KeyboardModel`, from a recorded screen), then "So it's NAME?" (a
    yes/no opening on YES, its page from `question(typed, typings)`: None = a page the eyes cannot read), then the truck
    on YES, or the keyboard again, empty, on NO (`src/main_menu.c` Task_NewGameBirchSpeech_ProcessNameYesNoMenu)."""

    def __init__(self, keyboard: ScreenState, question) -> None:
        self.start = keyboard
        self.question = question
        self.keyboard = KeyboardModel(keyboard)
        self.typings = 1
        self.answers: list[int] = []
        self.menu: MenuModel | None = None
        self.in_truck = False

    def tick(self, button: str | None, new: bool) -> None:
        self.frame += 1
        if self.in_truck:
            return
        if self.menu is not None:
            self.menu.tick(button, new)
            if self.menu.chosen is not None:
                self.answers.append(self.menu.chosen)
                if self.menu.chosen == 0:
                    self.in_truck = True
                else:
                    self.keyboard = KeyboardModel(self.start)
                    self.typings += 1
                self.menu = None
            return
        self.keyboard.tick(button, new)
        if self.keyboard.closed:
            asked = ScreenState(game_state="MAIN_MENU", screen="menu", menu="yes_no", text_box_open=False, waits_for_button=False,
                                in_battle=False, text=self.question(self.keyboard.text, self.typings),
                                ui=MenuView(kind="yes_no", options=("YES", "NO"), cursor=0))
            self.menu = MenuModel(asked)

    def screen(self) -> ScreenState:
        if self.in_truck:
            return overworld_screen()
        if self.menu is not None:
            return self.menu.screen()
        return self.keyboard.screen()

    def player(self) -> PlayerState | None:
        return standing(map_const=TRUCK_MAP) if self.in_truck else None


class NameQuestionTests(unittest.TestCase):
    """STEP 2.1, the review's item 5 (`skills/intro.py`): "So it's NAME?" names EXACTLY the typed name or not; a page
    the eyes cannot read is answered from what the keyboard CONFIRMED, never by NO and a re-typing loop."""

    def keyboard(self) -> ScreenState:
        return screen_from(find(recorded("intro"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "naming"
                                and r["screen"]["ui"]["accepts_input"] and r["screen"]["ui"]["text"] == ""
                                and r["screen"]["ui"]["page"] == "upper")["screen"])

    def test_the_name_is_compared_exactly(self) -> None:
        self.assertTrue(name_in_question("So it’s Rosa?", "Rosa"))  # as the eyes read it (charmap 0xB4)
        self.assertTrue(name_in_question("So it's Rosa?", "Rosa"))
        self.assertFalse(name_in_question("So it’s Kaiden?", "Kai"))  # the pre-2.1 substring rule said YES
        self.assertFalse(name_in_question("So it’s R.qq?", "Rosa"))  # XBN's question
        self.assertFalse(name_in_question("So it’s L   ?", "Luna"))  # XBN's question, seed 9
        self.assertIsNone(name_in_question(None, "Rosa"))
        self.assertIsNone(name_in_question("Hi! Sorry to keep you waiting!", "Rosa"))  # a stale page, not the question

    def test_an_unreadable_question_relies_on_the_keyboard(self) -> None:
        gender, name = intended()
        model = NameTailModel(self.keyboard(), lambda typed, typings: None)
        self.assertEqual(drive(play_intro(rig(model), PERSONALITY)), f"in the truck; intended {name} ({gender})")
        self.assertEqual((model.typings, model.answers), (1, [0]))  # typed once, YES; before 2.1: NO and re-typed

    def test_a_question_naming_another_name_is_answered_no(self) -> None:
        gender, name = intended()
        model = NameTailModel(self.keyboard(), lambda typed, typings: f"So it’s {typed}{'a' if typings == 1 else ''}?")
        self.assertEqual(drive(play_intro(rig(model), PERSONALITY)), f"in the truck; intended {name} ({gender})")
        self.assertEqual((model.typings, model.answers), (2, [1, 0]))  # NO to "So it's {name}a?", then YES


class CounterModel(Model):
    """A person (`graphics_id`) across a counter; the player stands free, facing them. Each A moves the conversation
    to the next of `screens` (the last one stays: a menu that never takes input, so the skill's choice FAILS)."""

    def __init__(self, graphics_id: int, screens: list[ScreenState]) -> None:
        self.graphics_id = graphics_id
        self.screens = screens
        self.at = -1  # -1: not talking yet

    def press(self, button: str) -> None:
        if button == "A" and self.at < len(self.screens) - 1:
            self.at += 1

    def screen(self) -> ScreenState:
        return overworld_screen() if self.at < 0 else self.screens[self.at]

    def player(self) -> PlayerState:
        return standing()

    def view(self) -> View:
        return person_view(self.graphics_id)


class SubSkillFailureTests(unittest.TestCase):
    """STEP 2.1, the review's item 6: a sub-skill that FAILS (`choose`, `type_name`, `answer_yes_no`; here: a menu that
    never takes input) ends the skill AT ONCE with its reason. Before 2.1 the skills ignored the result and went round
    their loops (60 turns in the intro, 6 at the nurse, 12 at the mart, CLOCK_BUDGET at the clock)."""

    def recorded_ui(self, kind: str) -> ScreenState:
        return screen_from(find(recorded("intro"), lambda r: (r["screen"]["ui"] or {}).get("kind") == kind)["screen"])

    def play(self, model: Model) -> tuple[str, Hands]:
        hands = rig(model)
        return drive(play_intro(hands, PERSONALITY)), hands

    def test_the_intro_reports_each_failure_at_once(self) -> None:
        gender, name = intended()
        keyboard = KeyboardModel(screen_from(find(recorded("intro"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "naming"
                                                  and r["screen"]["ui"]["accepts_input"])["screen"]))
        keyboard.busy = FOREVER  # the keyboard never takes input
        question = ScreenState(game_state="MAIN_MENU", screen="menu", menu="yes_no", text_box_open=False, waits_for_button=False,
                               in_battle=False, text=f"So it’s {name}?", ui=MenuView(kind="yes_no", options=("YES", "NO"), cursor=0))
        cases = (
            (MenuModel(self.recorded_ui("main_menu"), delay=FOREVER), "intro: NEW GAME could not be chosen on the main menu",
             WAIT_UI_BUDGET),
            (MenuModel(self.recorded_ui("gender"), delay=FOREVER), f"intro: {gender} could not be chosen on the gender menu",
             WAIT_UI_BUDGET),
            (keyboard, f"intro: the name {name!r} could not be typed on the keyboard", TYPE_BUDGET),
            (MenuModel(question, delay=FOREVER), "intro: the name question could not be answered", WAIT_UI_BUDGET),
        )
        for model, outcome, budget in cases:
            got, hands = self.play(model)
            self.assertEqual(got, outcome)
            self.assertLessEqual(hands.pad.frames, budget + 60, outcome)  # ONE try, not 60

    def test_the_nurse_reports_a_failed_yes_no_at_once(self) -> None:
        page = overworld_screen(screen="text", text_box_open=True, waits_for_button=True, wait_reason="text printer 0 CLEAR",
                                text=f"Hello, and welcome to the POKéMON CENTER.{PARAGRAPH}", script_running=True,
                                controls_locked=True)
        asked = overworld_screen(screen="menu", menu="yes_no", text="Would you like to rest your POKéMON?", script_running=True,
                                 controls_locked=True, ui=MenuView(kind="yes_no", options=("YES", "NO"), cursor=0, accepts_input=False))
        hands = rig(CounterModel(NURSE_GFX, [page, asked]))
        self.assertEqual(drive(nurse_heal(hands)), "the nurse's yes/no could not be answered YES")
        self.assertLessEqual(hands.pad.frames, WAIT_UI_BUDGET + 400)  # before 2.1: 6 tries, "the nurse's dialogue did not end"

    def test_the_mart_reports_a_failed_choice_at_once(self) -> None:
        shop = overworld_screen(screen="menu", menu="mart_menu", text="How may I serve you?", script_running=True,
                                controls_locked=True, ui=MenuView(kind="mart_menu", options=("BUY", "SELL", "QUIT"), cursor=0,
                                                                  accepts_input=False))
        hands = rig(CounterModel(MART_CLERK_GFX, [shop]))
        self.assertEqual(drive(mart_buy(hands, "POKé BALL", 5)), "could not choose BUY in the shop menu")
        self.assertLessEqual(hands.pad.frames, WAIT_UI_BUDGET + 400)  # before 2.1: 12 tries

    def test_the_clock_reports_a_failed_yes_no_at_once(self) -> None:
        class FrozenQuestionClock(ClockModel):
            """The clock, whose "Is this the correct time?" never takes input."""

            def tick(self, button: str | None, new: bool) -> None:
                super().tick(button, new)
                if self.asking is not None:
                    self.asking.delay = FOREVER

        start = screen_from(find(recorded("clock"), lambda r: (r["screen"]["ui"] or {}).get("kind") == "clock")["screen"])
        model = FrozenQuestionClock(start)
        hands = rig(model)
        self.assertFalse(drive(set_clock(hands, 10, 2, "test")))
        self.assertEqual(model.asked, 1)  # before 2.1: asked again for up to CLOCK_BUDGET turns
        self.assertLess(hands.pad.frames, CLOCK_BUDGET)


class ProvenanceTests(unittest.TestCase):
    """STEP 2.1, the review's item 2 (`gates/provenance.py`): the evidence's CODE line tells two uncommitted trees
    apart. Before 2.1 every uncommitted tree printed the same "HEAD x; ai_player/ has UNCOMMITTED changes"."""

    def test_two_different_trees_give_two_lines(self) -> None:
        from ai_player.gates.provenance import line

        one = line("abc1234", "ai_player/", b"diff --git a/x b/x\n-1\n+2\n", {}, 1)
        two = line("abc1234", "ai_player/", b"diff --git a/x b/x\n-1\n+3\n", {}, 1)
        self.assertNotEqual(one, two)
        self.assertIn("working-tree digest sha256:", one)
        self.assertEqual(one, line("abc1234", "ai_player/", b"diff --git a/x b/x\n-1\n+2\n", {}, 1))  # the same tree: the same line
        new_a = line("abc1234", "ai_player/", b"", {"ai_player/new.py": b"a = 1\n"}, 0)
        new_b = line("abc1234", "ai_player/", b"", {"ai_player/new.py": b"a = 2\n"}, 0)
        self.assertNotEqual(new_a, new_b)  # an UNTRACKED file's content counts
        self.assertIn("clean at HEAD", line("abc1234", "ai_player/", b"", {}, 0))

    def test_this_trees_line_is_recomputable(self) -> None:
        """Read-only git on the real repository (`SUPPORT`, also from a copy of the package): the same line twice."""
        from ai_player.gates.provenance import provenance

        first, second = provenance(SUPPORT), provenance(SUPPORT)
        self.assertEqual(first, second)
        self.assertIn("working-tree digest sha256:", first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
