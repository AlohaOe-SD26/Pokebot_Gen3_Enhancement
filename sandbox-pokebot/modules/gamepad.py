"""
Fork addition (sandbox, punch-list #10): XInput gamepad support.

Lets an Xbox-style controller — including the ROG Ally X's built-in pad —
play the game in Manual mode, exactly like the keyboard does: buttons are
held/released on the emulator via the same `hold_button`/`release_button`
API the stock key handler uses, so everything downstream (including the
macro recorder, which samples the emulator's input state) works unchanged.

Button mapping (fixed in v1):

    XInput                GBA
    ------------------    ----------
    D-Pad / left stick -> Up/Down/Left/Right
    A                  -> A
    B                  -> B
    X                  -> B   (secondary, matches Nintendo thumb layout)
    Y                  -> A   (secondary)
    Start (Menu)       -> Start
    Back (View)        -> Select
    LB                 -> L
    RB                 -> R
    Back + Start together -> toggle the handheld tool drawer (GUI only,
                             never injected into the game)

Implementation notes:
- ctypes against XInput1_4.dll (Windows 8+) with a fallback to
  XInput9_1_0.dll; anywhere neither loads (non-Windows, stripped-down
  systems) the feature reports "unavailable" and does nothing.
- Polling happens once per frame on the main thread via `GamepadListener`
  (registered by plugins/gamepad_plugin.py). When no controller is
  connected, XInputGetState is only re-tried every ~1 s — polling a missing
  pad is surprisingly expensive on Windows.
- Injection is gated on `context.bot_mode == "Manual"` (mirroring the
  stock keyboard handler); on leaving Manual, on disconnect, or on any
  error, every button this module holds is released.
"""

import ctypes
import sys
import time

from modules.context import context
from modules.libmgba import input_map

ERROR_SUCCESS = 0
ERROR_DEVICE_NOT_CONNECTED = 1167
DISCONNECTED_POLL_INTERVAL = 1.0  # seconds between re-checks when no pad found
THUMBSTICK_DEADZONE = 10000  # of 32767; a bit above XInput's documented 7849

XINPUT_DPAD_UP = 0x0001
XINPUT_DPAD_DOWN = 0x0002
XINPUT_DPAD_LEFT = 0x0004
XINPUT_DPAD_RIGHT = 0x0008
XINPUT_START = 0x0010
XINPUT_BACK = 0x0020
XINPUT_LEFT_SHOULDER = 0x0100
XINPUT_RIGHT_SHOULDER = 0x0200
XINPUT_A = 0x1000
XINPUT_B = 0x2000
XINPUT_X = 0x4000
XINPUT_Y = 0x8000

# XInput button bit -> GBA button name (keys of modules.libmgba.input_map).
BUTTON_MAPPING: dict[int, str] = {
    XINPUT_DPAD_UP: "Up",
    XINPUT_DPAD_DOWN: "Down",
    XINPUT_DPAD_LEFT: "Left",
    XINPUT_DPAD_RIGHT: "Right",
    XINPUT_START: "Start",
    XINPUT_BACK: "Select",
    XINPUT_LEFT_SHOULDER: "L",
    XINPUT_RIGHT_SHOULDER: "R",
    XINPUT_A: "A",
    XINPUT_B: "B",
    XINPUT_X: "B",
    XINPUT_Y: "A",
}


class _XInputGamepad(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class _XInputState(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_uint),
        ("Gamepad", _XInputGamepad),
    ]


def _load_xinput():
    if sys.platform != "win32":
        return None
    for dll_name in ("XInput1_4.dll", "XInput9_1_0.dll"):
        try:
            dll = ctypes.WinDLL(dll_name)
            get_state = dll.XInputGetState
            get_state.argtypes = [ctypes.c_uint, ctypes.POINTER(_XInputState)]
            get_state.restype = ctypes.c_uint
            return get_state
        except OSError:
            continue
    return None


class GamepadPoller:
    """Reads controller 0's state and translates it to GBA button names."""

    def __init__(self, get_state=None):
        # `get_state` is injectable for tests; None -> load the real DLL.
        self._get_state = get_state if get_state is not None else _load_xinput()
        self.available: bool = self._get_state is not None
        self.connected: bool = False
        self._backoff_until: float = 0.0

    def poll(self) -> "tuple[set[str], int] | None":
        """Returns (held GBA button names, raw XInput button mask), or None
        if no controller is available/connected right now."""
        if not self.available:
            return None
        if not self.connected and time.monotonic() < self._backoff_until:
            return None

        state = _XInputState()
        result = self._get_state(0, ctypes.byref(state))
        if result != ERROR_SUCCESS:
            # 1167 = not connected; treat any other error the same way but
            # keep re-checking on the same slow cadence.
            self.connected = False
            self._backoff_until = time.monotonic() + DISCONNECTED_POLL_INTERVAL
            return None

        self.connected = True
        pad = state.Gamepad
        raw_buttons = pad.wButtons

        held: set[str] = set()
        for bit, button_name in BUTTON_MAPPING.items():
            if raw_buttons & bit:
                held.add(button_name)

        # Left thumbstick as a digital D-pad.
        if pad.sThumbLX < -THUMBSTICK_DEADZONE:
            held.add("Left")
        elif pad.sThumbLX > THUMBSTICK_DEADZONE:
            held.add("Right")
        if pad.sThumbLY < -THUMBSTICK_DEADZONE:
            held.add("Down")
        elif pad.sThumbLY > THUMBSTICK_DEADZONE:
            held.add("Up")

        return held, raw_buttons


class GamepadListener:
    """BotListener (duck-typed): polls the pad once per frame on the main
    thread and drives the emulator's Manual-mode inputs edge-based."""

    def __init__(self, poller: "GamepadPoller | None" = None):
        self._poller = poller if poller is not None else GamepadPoller()
        self._held: set[str] = set()
        self._combo_was_down = False

    @property
    def poller(self) -> GamepadPoller:
        return self._poller

    def _release_everything(self) -> None:
        if self._held and context.emulator is not None:
            for button_name in self._held:
                try:
                    context.emulator.release_button(inputs=input_map[button_name])
                except Exception:
                    pass
        self._held = set()

    def _toggle_drawer(self) -> None:
        # Back+Start opens/closes the handheld tool drawer — couch-friendly.
        # UI action only; only meaningful when the dashboard screen is up
        # and in handheld mode.
        try:
            gui = context.gui
            screen = getattr(gui, "_emulator_screen", None)
            if (
                screen is not None
                and getattr(gui, "_current_screen", None) is screen
                and getattr(screen, "_handheld", False)
                and hasattr(screen, "_set_drawer")
            ):
                screen._set_drawer(not screen._drawer_open)
        except Exception:
            pass

    def handle_frame(self, bot_mode, frame) -> None:
        try:
            result = self._poller.poll()
            if result is None:
                self._release_everything()
                self._combo_was_down = False
                return
            held, raw_buttons = result

            # Back+Start combo: fire once on the rising edge, and suppress
            # the two buttons from game injection while both are down (the
            # user is clearly aiming for the UI toggle, not Start+Select).
            combo_down = bool(raw_buttons & XINPUT_BACK) and bool(raw_buttons & XINPUT_START)
            if combo_down:
                held = held - {"Start", "Select"}
                if not self._combo_was_down:
                    self._toggle_drawer()
            self._combo_was_down = combo_down

            gui_inputs_enabled = getattr(context.gui, "inputs_enabled", True)
            if context.bot_mode != "Manual" or context.emulator is None or not gui_inputs_enabled:
                self._release_everything()
                return

            for button_name in held - self._held:
                context.emulator.hold_button(inputs=input_map[button_name])
            for button_name in self._held - held:
                context.emulator.release_button(inputs=input_map[button_name])
            self._held = held
        except Exception:
            # A controller hiccup must never crash the frame loop; drop our
            # held buttons and try again next frame.
            try:
                self._release_everything()
            except Exception:
                pass


# Singleton listener so the GUI can show connection status.
listener = GamepadListener()


def get_status_text() -> str:
    poller = listener.poller
    if not poller.available:
        return "Controller: unavailable (no XInput)"
    if poller.connected:
        return "Controller: connected"
    return "Controller: not detected"
