"""Render the ENDLESS LOOP x4 grid to a PNG, without Tk or an emulator.

Covers the states the dashboard can actually be in: a live lane, a lane that has not
booted yet, a lane restarting, and a lane that used up its restart budget — plus an
over-long message, to prove the truncation does not overflow the cell.
"""
import sys
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

import PIL.Image  # noqa: E402

from modules.tile_mosaic import MosaicTile, compose_mosaic  # noqa: E402

OUT = Path(__file__).parent / "x4-preview"
OUT.mkdir(exist_ok=True)


def fake_screen(rgb, label_band):
    """A 240x160 RGB frame with a horizontal band, so scaling errors are visible."""
    img = PIL.Image.new("RGB", (240, 160), rgb)
    for y in range(label_band, label_band + 20):
        for x in range(0, 240, 2):
            img.putpixel((x, y), (255, 255, 255))
    return img.tobytes()


tiles = [
    MosaicTile(
        tag="P1", starter="torchic", alive=True, runs_completed=3,
        message="Story: heading north - Professor Birch needs help!",
        party="TORCHIC L5  18/21", pixels=fake_screen((30, 60, 120), 20),
    ),
    MosaicTile(
        tag="P2", starter="mudkip", alive=True, runs_completed=1,
        message=("Story: a deliberately absurd message that goes on and on and on and must be "
                 "truncated with an ellipsis rather than spilling out of its cell or over the "
                 "next tile, because that is exactly the bug this test exists to catch"),
        party="MARSHTOMP L16  49/49", pixels=fake_screen((20, 90, 40), 90),
    ),
    # never published yet
    MosaicTile(tag="P3", starter="treecko", alive=True, runs_completed=0, pixels=None),
    # died and burned its restart budget
    MosaicTile(
        tag="P4", starter="random", alive=False, exhausted=True, restarts=20, runs_completed=7,
        message="Story: derailed", party="ZIGZAGOON L4  0/17", pixels=fake_screen((90, 30, 30), 60),
    ),
]

failures = []
for size in [(960, 640), (480, 320), (1440, 960), (300, 200)]:
    mosaic = compose_mosaic(size, tiles, focus=1)
    expected = (max(120, size[0] // 2) * 2, max(80, size[1] // 2) * 2)
    if mosaic.size != expected:
        failures.append(f"size {size}: got {mosaic.size}, expected {expected}")
    if mosaic.mode != "RGB":
        failures.append(f"size {size}: mode {mosaic.mode}")
    path = OUT / f"mosaic-{size[0]}x{size[1]}.png"
    mosaic.save(path)
    print(f"wrote {path}  ({mosaic.size[0]}x{mosaic.size[1]})")

# A restarting lane must render too (different text path than 'exhausted').
tiles[3].alive, tiles[3].exhausted, tiles[3].restarts = False, False, 2
compose_mosaic((960, 640), tiles, focus=3).save(OUT / "mosaic-restarting.png")
print(f"wrote {OUT / 'mosaic-restarting.png'}")

# Fewer tiles than slots must not raise (a lane list that failed to fully populate).
compose_mosaic((960, 640), tiles[:2], focus=0)
compose_mosaic((960, 640), [], focus=0)
print("OK: short tile lists render without raising")

# A corrupt/short frame must fall back to the placeholder rather than raising.
tiles[0].pixels = b"\x00" * 100
compose_mosaic((960, 640), tiles, focus=0)
print("OK: short pixel buffer falls back to placeholder")

if failures:
    print("FAIL:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
