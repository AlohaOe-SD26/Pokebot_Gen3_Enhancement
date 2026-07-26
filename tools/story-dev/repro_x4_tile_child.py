"""Prove the ENDLESS LOOP x4 PUBLISHING path: PokebotTileChild._on_frame.

`mgba` is absent on this box, so it is stubbed just enough for `modules.libmgba` to
import. Nothing from the stub is exercised — the test drives `_on_frame` against a fake
`context.emulator`, which is exactly the seam the real lane uses.

Covers: the publish rate gate, RGB conversion, the shared-memory round trip, the status
blob, and the two failure modes that must NOT kill a lane (a screen read that raises,
and an oversized message).
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

# --- stub `mgba` so modules.libmgba imports -------------------------------
for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    module = types.ModuleType(name)
    sys.modules[name] = module
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

import PIL.Image  # noqa: E402

from modules.context import context  # noqa: E402
from modules.gui.tile_child import PokebotTileChild  # noqa: E402
from modules.tile_bridge import FRAME_BYTES, TileBridge  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


class FakeEmulator:
    """Only the surface `_on_frame` touches."""

    def __init__(self, image):
        self.image = image
        self.reads = 0

    def get_current_screen_image(self):
        self.reads += 1
        if isinstance(self.image, Exception):
            raise self.image
        return self.image


SHM = "pkbtilechildtest"
bridge = TileBridge(SHM, 1, create=True)

child = PokebotTileChild(lambda: None, lambda: None, shm_name=SHM, slot=0, lanes=1, lane_tag="P1")
child._bridge = TileBridge(SHM, 1, create=False)

print("== publishes a frame ==")
screen = PIL.Image.new("RGB", (240, 160), (12, 34, 56))
screen.putpixel((0, 0), (200, 100, 50))
context.emulator = FakeEmulator(screen)
context.message = "Story: choosing Torchic!"

child._on_frame()
frame = bridge.read(0)
check(frame is not None, "a frame reached shared memory")
if frame:
    check(len(frame.pixels) == FRAME_BYTES, "frame is a full 240x160 RGB buffer")
    check(tuple(frame.pixels[0:3]) == (200, 100, 50), "pixel (0,0) survived the round trip")
    check(frame.status.get("lane") == "P1", "status carries the lane tag")
    check(frame.status.get("message") == "Story: choosing Torchic!", "status carries context.message")
    check(frame.sequence == 1, "sequence starts at 1")
    # Key-completeness, not just spot checks: a `_status()` that silently stops building
    # part of the blob (e.g. a method spliced into the middle of it) shows up here rather
    # than as a blank tile nobody attributes to this.
    for key in ("lane", "message", "mode", "frame", "parked", "starter_chosen", "log"):
        check(key in frame.status, f"status carries '{key}'")

print("\n== the rate gate holds lanes to ~20 Hz ==")
before = context.emulator.reads
for _ in range(500):
    child._on_frame()
check(context.emulator.reads == before, f"500 immediate frames caused 0 extra screen reads (got {context.emulator.reads - before})")
child._last_publish_ns = 0  # simulate the interval elapsing
child._on_frame()
check(context.emulator.reads == before + 1, "one read once the interval elapsed")
check(bridge.read(0).sequence == 2, "sequence advanced to 2")

print("\n== a non-RGB screen is converted, not rejected ==")
child._last_publish_ns = 0
context.emulator = FakeEmulator(PIL.Image.new("RGBA", (240, 160), (9, 9, 9, 255)))
child._on_frame()
frame = bridge.read(0)
check(frame is not None and len(frame.pixels) == FRAME_BYTES, "RGBA screen published as RGB")
check(tuple(frame.pixels[0:3]) == (9, 9, 9), "RGBA converted correctly")

print("\n== an odd-sized screen is resized, not rejected ==")
child._last_publish_ns = 0
context.emulator = FakeEmulator(PIL.Image.new("RGB", (480, 320), (7, 7, 7)))
child._on_frame()
check(len(bridge.read(0).pixels) == FRAME_BYTES, "480x320 screen resized to 240x160")

print("\n== a screen read that raises must NOT kill the lane ==")
child._last_publish_ns = 0
last_seq = bridge.read(0).sequence
context.emulator = FakeEmulator(RuntimeError("emulator exploded"))
try:
    child._on_frame()
    check(True, "_on_frame swallowed the exception")
except Exception as exc:
    check(False, f"_on_frame raised {type(exc).__name__}: {exc} — a lane would die")
check(bridge.read(0).sequence == last_seq, "the last good frame is left intact")

print("\n== an absurd message must not abort the publish ==")
child._last_publish_ns = 0
context.emulator = FakeEmulator(PIL.Image.new("RGB", (240, 160), (1, 2, 3)))
context.message = "X" * 5000
child._on_frame()
frame = bridge.read(0)
check(frame is not None, "publish survived an oversized status blob")
check(frame.sequence == last_seq + 1, "sequence advanced past the failure case")

print("\n== no bridge attached (a lane running blind) ==")
child._bridge = None
child._last_publish_ns = 0
try:
    child._on_frame()
    check(True, "_on_frame is a no-op without a bridge")
except Exception as exc:
    check(False, f"_on_frame raised without a bridge: {exc}")

print("\n== PARK: the dashboard's command reaches the lane ==")
import tempfile  # noqa: E402

from modules.tile_bridge import CMD_PARK  # noqa: E402

child.close_requested = False
child._bridge = TileBridge(SHM, 1, create=False)
child._parked = False
child._log_reenables = 0

profile_dir = Path(tempfile.mkdtemp(prefix="parktest-"))
context.profile = types.SimpleNamespace(path=profile_dir)


class ResettableEmulator(FakeEmulator):
    """Adds the surface `context.emulation_speed`/`reset()` actually touch."""

    def __init__(self, image):
        super().__init__(image)
        self.resets = 0
        self._throttle = False
        self._speed = 0.0

    def reset(self):
        self.resets += 1

    def set_throttle(self, value):
        self._throttle = bool(value)

    def get_throttle(self):
        return self._throttle

    def set_speed_factor(self, value):
        self._speed = float(value)

    def get_speed_factor(self):
        return self._speed


context.emulator = ResettableEmulator(PIL.Image.new("RGB", (240, 160), (3, 3, 3)))
context.bot_mode = "Story (ENDLESS RESET)"
context.emulation_speed = 0

from modules import debug_logger  # noqa: E402

debug_logger.enable(context.profile, name_prefix="P1-")
check(debug_logger.is_enabled(), "the lane is logging before the park")

bridge.send_command(0, CMD_PARK, 42)
child._last_publish_ns = 0
child._on_frame()

check(child._parked is True, "the lane reports itself parked")
check(context.bot_mode == "Manual", f"bot mode -> Manual (got {context.bot_mode})")
check(context.emulation_speed == 1, f"speed -> 1x (got {context.emulation_speed})")
check(context.emulator.resets == 1, f"the emulator was reset to the title (resets={context.emulator.resets})")
check(not debug_logger.is_enabled(), "the debug log was CLOSED — this is what makes the copy safe")

print("\n== !! a parked lane must NOT re-arm its logger ==")
# Without the `_parked` guard, `_ensure_logging` would notice the logger is off and
# re-open the file a fraction of a second later — so the collector would archive a file
# that another process had just started writing to again.
for _ in range(10):
    child._last_publish_ns = 0
    child._on_frame()
check(not debug_logger.is_enabled(), "still closed after 10 more frames")
check(child._log_reenables == 0, f"the self-healer never fired (got {child._log_reenables})")

print("\n== the park is idempotent: the same command is not re-run ==")
resets_before = context.emulator.resets
for _ in range(5):
    child._last_publish_ns = 0
    child._on_frame()
check(context.emulator.resets == resets_before, "the same command sequence did not re-park")

print("\n== a parked lane keeps publishing, so its tile stays live ==")
seq_before = bridge.read(0).sequence
child._last_publish_ns = 0
child._on_frame()
frame = bridge.read(0)
check(frame.sequence > seq_before, "frames still publish while parked")
check(frame.status.get("parked") is True, "and the status says parked (the dashboard waits on this)")

child._bridge.close()
bridge.close()
print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
