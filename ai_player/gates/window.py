"""TEST SIDE: the GBA screen's window, written down HERE as literals (AI-player build step 3.1, the step-3 review's
finding 6). Pure.

WHY: the crop check of `gates/live_step3.py` (every tile the AI knows lay inside the window of the tile it was first
seen from) used `world/memory.py` in_window, which takes the window from the EYES' own constants (`eyes/view.py`
VIEW_HALF_WIDTH, VIEW_UP, VIEW_DOWN). Widen both together and the check still passes: it measured the eyes against
themselves. The gate's window is therefore written here from the hardware and the decomp, independently:

  * the screen is 240 x 160 pixels (`include/gba/defines.h` DISPLAY_WIDTH, DISPLAY_HEIGHT) and a map tile is 16 x 16,
    so 15 columns: the player's column and 7 on each side;
  * 10 rows of whole tiles, scrolled by 8 pixels (`src/field_camera.c`: VOFS = 40 standing still), so the player's row,
    4 whole rows and a HALF row above and below: 5 rows each way (measured live by `gates/live_step1.py` arm GEO).

A test (`gates/test_world.py` WindowTests) widens the eyes' constants and checks the gate still flags a tile seen from
8 columns away; a mutant (`gates/revert_step3.py`) puts the eyes' constants back into the gate and is caught.
"""

from __future__ import annotations

__all__ = ["SCREEN_DOWN", "SCREEN_HALF_WIDTH", "SCREEN_UP", "on_screen_from"]

#: Columns left and right of the player on screen (240 / 16 = 15 = 7 + 1 + 7).
SCREEN_HALF_WIDTH = 7
#: Rows above and below the player on screen, the outermost HALF visible (160 / 16 = 10, offset by 8 pixels).
SCREEN_UP = 5
SCREEN_DOWN = 5


def on_screen_from(seen_from: tuple[int, int], xy: tuple[int, int]) -> bool:
    """Was `xy` on screen while the player stood on `seen_from`? (The gate's own window, never the eyes'.)"""
    return abs(xy[0] - seen_from[0]) <= SCREEN_HALF_WIDTH and -SCREEN_UP <= xy[1] - seen_from[1] <= SCREEN_DOWN
