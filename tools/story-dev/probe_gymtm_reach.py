r"""OBSERVE-ONLY: why does `calculate_path` find no route from `devon_scope_got.ss1` (ROUTE120 (13,16)) to Fortree?
(2026-09-26, RULING 19's `--driver gymtm` continue check.)

Prints, from the fixture's own start state (nothing is moved or taught): the path result to several Fortree tiles and
to ROUTE120 tiles at growing distance, and the live objects in view. A CONTROL: the player's own tile must path.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gymtm_reach.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "gymtmprobe"
if not profile_directory_exists(PROFILE):
    create_profile(PROFILE, list_available_roms()[0])
profile = load_profile_by_name(PROFILE)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

from modules.map_data import MapRSE  # noqa: E402
from modules.map_path import PathFindingError, calculate_path  # noqa: E402
from modules.player import get_player_avatar  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"


def main() -> int:
    context.emulator.load_save_state((SAVES / "devon_scope_got.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    here = get_player_avatar().map_location
    print(f"at {here}")
    targets = [((MapRSE.ROUTE120), tuple(get_player_avatar().local_coordinates))]
    x, y = get_player_avatar().local_coordinates
    for dx, dy in ((0, 1), (0, 3), (-3, 0), (3, 0), (0, -3), (-6, 0), (0, 6), (-10, 0), (0, 10), (0, -10)):
        targets.append((MapRSE.ROUTE120, (x + dx, y + dy)))
    for t in ((5, 7), (22, 12), (40, 10), (45, 12), (47, 12), (20, 20)):
        targets.append((MapRSE.FORTREE_CITY, t))
    for m, t in targets:
        try:
            path = calculate_path(here, (m, t))
            print(f"  OK       {m.name} {t} len={len(path)}")
        except PathFindingError as e:
            print(f"  NO-PATH  {m.name} {t}: {str(e)[:140]}")
        except Exception as e:  # noqa: BLE001 - an observe-only probe reports every failure shape
            print(f"  ERROR    {m.name} {t}: {type(e).__name__}: {str(e)[:140]}")
    try:
        from modules.map import get_map_objects

        for o in get_map_objects():
            print(f"  object: local_id={getattr(o, 'local_id', '?')} at {getattr(o, 'current_coords', '?')} "
                  f"gfx={getattr(o, 'graphics_id', '?')}")
    except Exception as e:  # noqa: BLE001
        print(f"  objects unreadable: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
