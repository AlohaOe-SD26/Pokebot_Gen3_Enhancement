"""TEST SIDE: EVERY A press of a hands brain, checked against the GAME'S BEHAVIOUR (AI-player build step 2.1).

    py -3.12 ai_player/gates/probe_presses.py BRAIN [--state PATH | --fresh] [--seed N] [--frames N]
                                              [--fault ungated_a|blind_count] [--mart-count N] [--clock HH:MM]
    prints one line: PRESSES {json}

WHY (the step-2 verifier): `gates/live_step2.py` checked that each A pressed on a text was gated by reading the
press's own log record (`waits=A/B(<gate>)` in its digest). The gate and the digest come from the SAME look, so
that check shows the log agrees with itself, never that the GAME was waiting. Two of the waits the hands press
on live were new in step 2 and had no behavioural proof at all: the TASK waits after "...your name?"
(`Task_NewGameBirchSpeech_WaitPressBeforeNameChoice`) and after the mart's "Here you go!"
(`Task_ReturnToItemListAfterItemPurchase`). And only the nurse arm limited the OTHER A presses (the talk, the
menu confirms) to screens that took them.

WHAT THIS DOES: it runs the hands brain in a throwaway emulator, exactly as `gates/hands_harness.py` does (the
same `HandsBrain`, the same seed, the controller's semantics), and at EVERY A press, BEFORE the press, it saves
the emulator's state and asks the GAME, in FORKS of that frame, the state reloaded before each:
  * PRINTING: in the first PRINT_WINDOW frames with no input, does a text printer that is active advance its
    `currentChar` (the text is still being drawn; text speed SLOW draws a character every 8 frames,
    `src/text.c` sTextSpeedFrameDelays {8, 4, 1})?
  * STILL: in IDLE_FRAMES frames with NO input, does nothing move: every active printer (index, currentChar,
    state), the message box mode, the main callback, the active tasks, the script's pointer and status?
  * MOVED BY A: the SAME press (A held as long as the AI holds it), then PRESS_WATCH frames: the first frame on
    which that snapshot changes;
  * A CONTINUE, NOT A CHOICE: B pressed instead, from the same state: the same snapshots, frame for frame, as
    after A? (every wait the hands gate on polls A OR B: `src/text.c` TextPrinterWait /
    TextPrinterWaitWithDownArrow, `src/scrcmd.c` WaitForAorBPress, `src/main_menu.c` line 1590
    `if ((JOY_NEW(A_BUTTON)) || (JOY_NEW(B_BUTTON)))`, `src/shop.c` line 1148 `if (JOY_NEW(A_BUTTON | B_BUTTON))`;
    on a menu A picks and B cancels, so the two differ there);
  * FREE (for the A that starts a conversation): the script context is shut down
    (`sGlobalScriptContextStatus` == CONTEXT_SHUTDOWN 2, `src/script.c`), the field controls are not locked,
    no printer is active; STARTED: after A the script context runs.
Then it reloads the saved state and lets the real press happen. Every value here is read by THIS file from raw
memory (the probe's own task and symbol reads), never by the AI's eyes, and the forks never touch the run:
`gates/live_step2.py` compares the forked run's outcome, frames and presses with an unforked
`hands_harness.py` run of the same seed (they must be equal).

The truth per A press is graded by `gates/live_step2.py` (arms WBI, WBN, WBM, WBC, WBX, XTW), by the press's GATE
(`gate_kind`): a WAIT gate must be still, moved by A, the same under B, and not printing; a MENU gate not
printing, still (the menu waited for input) and moved by A; a TALK gate free and started. This file is test side
(`ai_player/gates/`): the purity gate forbids the play loop to import it.

STEP 2.1 (the step-2 review, item 4: "presses other than A are never checked against the game"): every START, B
and SELECT press is forked too (`PressTester.check_other`). Such a press is not a "continue": it skips the intro
movie, starts the game at the title, leaves the mart's list, deletes a letter, puts the keyboard's cursor on OK,
turns the keyboard's page. So it is judged by ONE question, asked of the game: was it TAKEN? From the saved frame,
PRESS_WATCH frames with NO input, and (the state reloaded) the same frames with the press held as long as the AI
holds it; the press was taken when the two runs differ (`effect`: the snapshot above plus every active task's
DATA, `sMenu`, and the naming keyboard's state, page and cursor). The emulator is deterministic, so two runs from
one state with the same inputs are equal frame for frame (the A forks' "B-same" relies on the same fact); a press
the game DROPPED (a key during a palette fade, which the intro movie ignores: `src/intro.c` MainCB2_Intro) leaves
the two runs equal. The probe also reads, itself, whether a fade ran on the press's frame (`gPaletteFade.active`).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import PROFILE, HarnessControls, truth  # noqa: E402
from ai_player.gates.probe_eyes import _symbol, _u32, boot  # noqa: E402

#: Frames with no input in which the game must not move for "the game waited" (as `probe_eyes.behaviour`).
IDLE_FRAMES = 300
#: Frames watched after the press (or after B instead).
PRESS_WATCH = 60
#: Frames in which an active printer must advance for "the text was still printing" (the slowest text speed
#: draws one character every 8 frames).
PRINT_WINDOW = 8
#: `src/script.c`: enum { CONTEXT_RUNNING, CONTEXT_WAITING, CONTEXT_SHUTDOWN } (sGlobalScriptContextStatus).
CONTEXT_SHUTDOWN = 2
#: `include/text.h` struct TextPrinter: 0x24 bytes; currentChar @0, active @0x1B, state @0x1C.
PRINTER_SIZE, PRINTER_COUNT = 0x24, 32
#: A gate that says the game WAITED for the press (`ScreenState.wait_reason`).
WAIT_GATE = re.compile(r"^(text printer \d+ (WAIT|CLEAR|SCROLL_START)|script waitbuttonpress|task \S+ \(A( or B)?\))$")
#: STEP 2.1 (the review's item 4): the presses other than A the probe forks, judged by "was it taken?".
OTHER_BUTTONS = ("Start", "B", "Select")
#: `include/palette.h` struct PaletteFadeControl: `active` is bit 7 of byte 7 (read here by the probe itself).
FADE_BYTE, FADE_BIT = 0x07, 0x80
#: `src/naming_screen.c` struct NamingScreenData: state @0x1E10 ... template @0x1E28 (the block read by `effect`);
#: cursorSpriteId @0x1E23; `include/sprite.h` struct Sprite: 0x44 bytes, data[] @0x2E.
NAMING_BLOCK, NAMING_BLOCK_SIZE, NAMING_CURSOR_SPRITE, SPRITE_SIZE, SPRITE_DATA = 0x1E10, 0x1C, 0x1E23, 0x44, 0x2E
#: The menu gates the hands write (`hands/menus.py`), each with the `MenuView.kind` it names.
_MENU_GATES = (
    (re.compile(r"^(?P<kind>[a-z_]+) cursor on -?\d+ \("), None),
    (re.compile(r"^mart_quantity reads x\d+"), "mart_quantity"),
    (re.compile(r"^keyboard: "), "naming"),
    (re.compile(r"^clock reads \d+:\d+"), "clock"),
)


def gate_kind(gate: str) -> tuple[str, str | None]:
    """What a press's GATE claims: ("wait", None), ("menu", <the menu's kind>), ("talk", None) or ("other", None)."""
    gate = gate or ""
    if WAIT_GATE.match(gate):
        return "wait", None
    if gate.startswith("talk: facing "):
        return "talk", None
    for pattern, kind in _MENU_GATES:
        match = pattern.match(gate)
        if match:
            return "menu", kind or match.group("kind")
    return "other", None


def snapshot() -> dict:
    """What would MOVE if the game were not waiting, read raw by this file: every active text printer (index,
    currentChar, state), the message box mode, the main callback, the active tasks (names, in slot order), the
    global script context's pointer and its status, the field controls' lock."""
    from modules.memory import read_symbol

    printers = read_symbol("sTextPrinters", size=PRINTER_SIZE * PRINTER_COUNT)
    active = [[i, _u32(printers, PRINTER_SIZE * i), printers[PRINTER_SIZE * i + 0x1C]] for i in range(PRINTER_COUNT)
              if printers[PRINTER_SIZE * i + 0x1B]]
    raw_tasks = read_symbol("gTasks", size=40 * 16)
    tasks = [_symbol(_u32(raw_tasks, 40 * i) - 1) for i in range(16) if raw_tasks[40 * i + 4] and _u32(raw_tasks, 40 * i)]
    script = read_symbol("sGlobalScriptContext", size=12)
    return {"printers": active, "box": read_symbol("sFieldMessageBoxMode", size=1)[0],
            "callback2": _symbol(_u32(read_symbol("gMain", size=8), 4) - 1), "tasks": tasks,
            "script_ptr": _u32(script, 8), "script_status": read_symbol("sGlobalScriptContextStatus", size=1)[0],
            "locked": read_symbol("sLockFieldControls", size=1)[0], "naming_text": naming_text()}


def naming_text() -> str | None:
    """The naming keyboard's typed text, raw hex (`src/naming_screen.c` sNamingScreen -> struct NamingScreenData
    textBuffer[16] @0x1800), or None while no keyboard is allocated. A key typed changes nothing else this
    snapshot holds, so without it an A on a key would look like an A that did nothing."""
    from modules.context import context
    from modules.memory import read_symbol

    pointer = _u32(read_symbol("sNamingScreen", size=4), 0)
    if not 0x02000000 <= pointer < 0x02040000 - 0x1810:
        return None
    return bytes(context.emulator.read_bytes(pointer + 0x1800, 16)).hex()


def effect() -> dict:
    """STEP 2.1: what a press other than A may change, read raw by this file: the `snapshot`, every active task's
    DATA (a menu's cursor, a timer, the title's phase counters), `sMenu` (the yes/no and list cursors), and the
    naming keyboard's state, page and cursor (its block of `NamingScreenData` and the cursor sprite's data)."""
    from modules.context import context
    from modules.memory import read_symbol

    out = snapshot()
    raw_tasks = read_symbol("gTasks", size=40 * 16)
    out["task_data"] = [bytes(raw_tasks[40 * i + 8:40 * i + 40]).hex() for i in range(16) if raw_tasks[40 * i + 4]]
    out["menu"] = bytes(read_symbol("sMenu", size=12)).hex()
    pointer = _u32(read_symbol("sNamingScreen", size=4), 0)
    out["naming"] = None
    if 0x02000000 <= pointer < 0x02040000 - NAMING_BLOCK - NAMING_BLOCK_SIZE:
        block = bytes(context.emulator.read_bytes(pointer + NAMING_BLOCK, NAMING_BLOCK_SIZE))
        sprite = block[NAMING_CURSOR_SPRITE - NAMING_BLOCK]
        cursor = bytes(read_symbol("gSprites", sprite * SPRITE_SIZE + SPRITE_DATA, 4)).hex() if sprite < 64 else None
        out["naming"] = [block.hex(), cursor]
    return out


def fading_now() -> bool:
    """`gPaletteFade.active`, read by the probe itself."""
    from modules.memory import read_symbol

    return bool(read_symbol("gPaletteFade", FADE_BYTE, 1)[0] & FADE_BIT)


def _diff(a: dict, b: dict) -> list[str]:
    return sorted(k for k in a if a[k] != b.get(k))


class PressTester:
    """The forks at one A press (module docstring). `check` leaves the emulator exactly where it found it."""

    def __init__(self, context) -> None:
        self.context = context
        self.results: list[dict] = []
        self.others: list[dict] = []  # STEP 2.1: the START / B / SELECT presses (`check_other`)

    def check_other(self, entry: dict | None, button: str, held: int) -> None:
        """STEP 2.1 (the review's item 4): was this START / B / SELECT TAKEN? PRESS_WATCH frames with no input,
        then (reloaded) the same frames with the press; taken at the first frame the two `effect` runs differ.
        Leaves the emulator exactly where it found it."""
        emulator = self.context.emulator
        state = emulator.get_save_state()
        frame0 = emulator.get_frame_count()
        held_before = emulator.reset_held_buttons()
        result: dict = {"frame": frame0, "button": button, "action": (entry or {}).get("action"),
                        "gate": (entry or {}).get("reason"), "digest": (entry or {}).get("digest"), "held": held}
        try:
            result["fading"] = fading_now()
            idle = []
            for _ in range(PRESS_WATCH):
                emulator.run_single_frame()
                idle.append(effect())
            emulator.load_save_state(state)
            pressed = self._press(button, held, effect)
            taken = next((i + 1 for i, (a, b) in enumerate(zip(idle, pressed)) if a != b), None)
            result["taken_at"] = taken
            result["taken_by"] = _diff(idle[taken - 1], pressed[taken - 1]) if taken else []
        finally:
            emulator.load_save_state(state)
            emulator.restore_held_buttons(held_before)
        result["restored"] = emulator.get_frame_count() == frame0
        self.others.append(result)

    def check(self, entry: dict | None, held: int) -> None:
        emulator = self.context.emulator
        state = emulator.get_save_state()
        frame0 = emulator.get_frame_count()
        held_before = emulator.reset_held_buttons()
        result: dict = {"frame": frame0, "action": (entry or {}).get("action"), "gate": (entry or {}).get("reason"),
                        "digest": (entry or {}).get("digest"), "held": held}
        kind, menu = gate_kind(result["gate"] or "")
        result["kind"], result["menu"] = kind, menu
        try:
            s0 = snapshot()
            result["tasks"] = s0["tasks"]
            result["printers"] = s0["printers"]
            result["free"] = (s0["script_status"] == CONTEXT_SHUTDOWN and not s0["locked"] and not s0["printers"])
            # 1) PRINTING and STILL: no input
            first_change, changed_keys, printing = None, [], False
            before = {p[0]: p[1] for p in s0["printers"]}
            for i in range(IDLE_FRAMES):
                emulator.run_single_frame()
                now = snapshot()
                if i < PRINT_WINDOW and not printing:
                    after = {p[0]: p[1] for p in now["printers"]}
                    printing = any(k in after and after[k] != v for k, v in before.items())
                if first_change is None and now != s0:
                    first_change, changed_keys = i + 1, _diff(s0, now)
                if first_change is not None and i >= PRINT_WINDOW - 1:
                    break  # not still: the rest of the idle frames cannot change that
            result["printing"] = printing
            result["still"] = first_change is None
            result["moved_by_itself_at"] = first_change
            result["moved_by_itself"] = changed_keys
            # 2) A, the same press
            emulator.load_save_state(state)
            seq_a = self._press("A", held)
            moved = next((i + 1 for i, s in enumerate(seq_a) if s != s0), None)
            result["moved_by_a_at"] = moved
            result["moved_by_a"] = _diff(s0, seq_a[moved - 1]) if moved else []
            result["started"] = any(s["script_status"] != CONTEXT_SHUTDOWN for s in seq_a)
            # 3) B instead, from the same state
            emulator.load_save_state(state)
            seq_b = self._press("B", held)
            result["b_same"] = seq_b == seq_a
            if not result["b_same"]:
                i = next(i for i, (a, b) in enumerate(zip(seq_a, seq_b)) if a != b)
                result["b_differs_at"] = [i + 1, _diff(seq_a[i], seq_b[i])]
        finally:
            emulator.load_save_state(state)
            emulator.restore_held_buttons(held_before)
        result["restored"] = emulator.get_frame_count() == frame0
        self.results.append(result)

    def _press(self, button: str, held: int, read=snapshot) -> list[dict]:
        emulator = self.context.emulator
        out = []
        emulator.hold_button(button)
        try:
            for i in range(PRESS_WATCH):
                if i == held:
                    emulator.release_button(button)
                emulator.run_single_frame()
                out.append(read())
        finally:
            emulator.release_button(button)
        return out


class ForkingControls(HarnessControls):
    """`HarnessControls` (the controller's semantics), plus the forks before every A press. The press's own
    action-log record (written by the pad just before it presses) names its gate."""

    def __init__(self, emulator, tester: PressTester) -> None:
        super().__init__(emulator)
        self.tester = tester
        self.last_entry: dict | None = None

    def hold(self, button: str, frames: int):
        if button == "A":
            self.tester.check(self.last_entry, frames)
        elif button in OTHER_BUTTONS:  # STEP 2.1 (the review's item 4)
            self.tester.check_other(self.last_entry, button, frames)
        yield from super().hold(button, frames)


def play(context, brain: str, seed: int, frames: int, run_dir: Path, fault: str | None, mart_count: int | None,
         clock: str | None) -> dict:
    """`hands_harness.play`, with the forking controls (one frame per `next`)."""
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.mode import BrainSettings, HandsBrain
    from ai_player.options import DEFAULT_MART_COUNT, DEFAULT_MART_ITEM, HandsOptions

    emulator = context.emulator
    clock_value = tuple(int(p) for p in clock.split(":")) if clock else None
    options = HandsOptions(brain=brain, run_dir=run_dir, seed=seed, personality=None, mart_item=DEFAULT_MART_ITEM,
                           mart_count=mart_count or DEFAULT_MART_COUNT, clock=clock_value,
                           fault_ungated_a=fault == "ungated_a", fault_blind_count=fault == "blind_count")
    lines: list[str] = []
    brain_object = HandsBrain(BrainSettings(frames=frames), lines.append, options)
    tester = PressTester(context)
    controls = ForkingControls(emulator, tester)
    record = brain_object.actions.record

    def spy(*args, **kwargs):
        entry = record(*args, **kwargs)
        controls.last_entry = entry
        return entry

    brain_object.actions.record = spy
    started = time.monotonic()
    steps = brain_object.play(controls, FrameworkEyes())
    reason, count = None, 0
    while True:
        try:
            next(steps)
        except StopIteration as done:
            reason = done.value
            break
        emulator.run_single_frame()
        count += 1
        if count > frames + 10:
            reason = "harness: the brain overran its budget"
            break
    return {"brain": brain, "seed": seed, "fault": fault, "reason": reason, "frames": count, "presses": controls.presses,
            "seconds": round(time.monotonic() - started, 1), "lines": lines, "a_presses": tester.results,
            "other_presses": tester.others}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("brain", choices=("intro", "nurse", "mart", "clock"))
    parser.add_argument("--state", type=Path)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--frames", type=int, default=20000)
    parser.add_argument("--fault", choices=("ungated_a", "blind_count"))
    parser.add_argument("--mart-count", type=int)
    parser.add_argument("--clock")
    args = parser.parse_args()
    if args.state is None and not args.fresh:
        parser.error("--state PATH or --fresh")
    context = boot(PROFILE)
    if args.state is not None:
        context.emulator.load_save_state(args.state.read_bytes())
    import ai_player.eyes.screens as screens_module

    result = play(context, args.brain, args.seed, args.frames, Path(tempfile.mkdtemp(prefix="ai_presses_")), args.fault,
                  args.mart_count, args.clock)
    result["truth"] = truth(context)
    result["eyes_code"] = {"screens": screens_module.__file__, "task_waits": sorted(screens_module.TASK_WAITS)}
    result["constants"] = {"IDLE_FRAMES": IDLE_FRAMES, "PRESS_WATCH": PRESS_WATCH, "PRINT_WINDOW": PRINT_WINDOW,
                           "OTHER_BUTTONS": list(OTHER_BUTTONS)}
    print("PRESSES " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
