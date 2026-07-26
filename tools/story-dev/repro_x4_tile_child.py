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

bridge.close()
print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
