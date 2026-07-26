"""Prove the dashboard's x4 wiring: _update_x4_tiles paints, _x4_click focuses.

Uses a REAL Tk canvas and a fake batch, so the seam under test is the actual dashboard
code (draw-rect maths, shared-memory read, mosaic call, canvas image swap, quadrant
hit-testing) rather than a re-implementation of it.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

import tkinter  # noqa: E402
from tkinter import Canvas  # noqa: E402

import PIL.Image  # noqa: E402

from modules.gui.dashboard_gui import DashboardScreen  # noqa: E402
from modules.tile_bridge import TileBridge  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


class FakeLane:
    def __init__(self, slot, tag, starter, alive=True, restarts=0):
        self.slot, self.tag, self.starter = slot, tag, starter
        self.is_alive, self.restarts = alive, restarts
        self.profile_name = f"endless-{tag}-{starter}"


class FakeBatch:
    max_restarts = 20

    def __init__(self, bridge):
        self.bridge = bridge
        self.polls = 0
        self.lanes = [
            FakeLane(0, "P1", "torchic"),
            FakeLane(1, "P2", "mudkip"),
            FakeLane(2, "P3", "treecko"),
            FakeLane(3, "P4", "random", alive=False, restarts=20),
        ]

    def poll(self):
        self.polls += 1


SHM = "pkbtiledashtest"
bridge = TileBridge(SHM, 4, create=True)
for slot, colour in enumerate([(180, 40, 40), (40, 180, 40), (40, 40, 180), (180, 180, 40)]):
    bridge.publish(
        slot, PIL.Image.new("RGB", (240, 160), colour).tobytes(), slot + 1, 1000 + slot, slot,
        {"lane": f"P{slot + 1}", "message": f"lane {slot} is playing", "party": "TORCHIC L5  18/21"},
    )

root = tkinter.Tk()
root.withdraw()
screen = DashboardScreen(root)
screen.frame = object()          # `update()` guards on this; unused here
screen.canvas = Canvas(root, width=960, height=640)
screen.canvas.pack()
root.update_idletasks()
screen._video_size = (960, 640)
screen._x4_batch = FakeBatch(bridge)

print("== _update_x4_tiles paints the grid ==")
screen._x4_last_paint = 0.0
screen._update_x4_tiles()
check(screen._x4_batch.polls == 1, "the batch was polled for dead lanes")
check(screen._current_canvas_image_id is not None, "an image was placed on the canvas")
check(screen._current_canvas_image is not None, "the PhotoImage reference is retained (else Tk garbage-collects it)")
first_id = screen._current_canvas_image_id
img = screen._current_canvas_image
check(img.width() == 960 and img.height() == 640, f"mosaic is 960x640 (got {img.width()}x{img.height()})")

print("\n== the repaint rate gate ==")
screen._update_x4_tiles()
check(screen._x4_batch.polls == 1, "an immediate second call was rate-limited")
screen._x4_last_paint = 0.0
screen._update_x4_tiles()
check(screen._x4_batch.polls == 2, "it repaints once the interval elapses")
check(screen._current_canvas_image_id != first_id, "the stale canvas image was replaced")
check(len(screen.canvas.find_all()) == 1, f"exactly one canvas item survives (got {len(screen.canvas.find_all())}) — no leak")

print("\n== many repaints must not leak canvas items ==")
for _ in range(30):
    screen._x4_last_paint = 0.0
    screen._update_x4_tiles()
check(len(screen.canvas.find_all()) == 1, f"still one canvas item after 30 repaints (got {len(screen.canvas.find_all())})")

print("\n== click-to-focus quadrant maths ==")
screen._log_event = lambda *a, **k: None  # the real one needs widgets we did not build
offset_x, offset_y, size = screen._video_draw_rect()
cases = [
    (offset_x + 10, offset_y + 10, 0, "top-left -> P1"),
    (offset_x + size[0] - 10, offset_y + 10, 1, "top-right -> P2"),
    (offset_x + 10, offset_y + size[1] - 10, 2, "bottom-left -> P3"),
    (offset_x + size[0] - 10, offset_y + size[1] - 10, 3, "bottom-right -> P4"),
    (offset_x + size[0] // 2 - 1, offset_y + size[1] // 2 - 1, 0, "just inside centre -> P1"),
]
for x, y, expected, label in cases:
    screen._x4_focus = -1
    consumed = screen._x4_click(types.SimpleNamespace(x=x, y=y))
    check(consumed is True, f"{label}: click consumed by the x4 handler")
    check(screen._x4_focus == expected, f"{label}: focus == {expected} (got {screen._x4_focus})")

screen._x4_focus = 2
screen._x4_click(types.SimpleNamespace(x=offset_x - 50, y=offset_y - 50))
check(screen._x4_focus == 2, "a click outside the video rect leaves focus alone")

print("\n== with no batch running, clicks fall through to the debug probe ==")
screen._x4_batch = None
check(screen._x4_click(types.SimpleNamespace(x=10, y=10)) is False, "handler declines the click when no batch is running")

print("\n== stop_endless_x4 clears the canvas ==")
screen._x4_batch = FakeBatch(bridge)
screen._x4_last_paint = 0.0
screen._update_x4_tiles()


class _Ctx:
    pass


import modules.gui.dashboard_gui as dg  # noqa: E402

dg.context.emulation_speed = 0
dg.context.bot_mode = "Story"
screen._x4_prev_speed, screen._x4_prev_mode = 3, "Manual"


class _StoppableBatch(FakeBatch):
    def stop(self):
        self.stopped = True


screen._x4_batch = _StoppableBatch(bridge)
screen.stop_endless_x4()
check(screen._x4_batch is None, "the batch reference was dropped")
check(screen._current_canvas_image_id is None, "the tile image was removed from the canvas")
check(len(screen.canvas.find_all()) == 0, "the canvas is empty again")

bridge.close()
root.destroy()
print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
