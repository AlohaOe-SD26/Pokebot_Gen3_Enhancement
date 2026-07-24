"""Ch12 recon 2: does the static Lavaridge->R111(18,99) path cross the Go-Goggles
desert (a SCRIPT gate, invisible to collision), and is the southbound rock staging
tile (18,100) reachable? Also re-check with avoid_scripted_events=True (the
navigate_to default) — the prior session's 'no way south' may have come from that.
"""

import pathlib as _pl
import sys

_SAVES = _pl.Path(__file__).resolve().parent / "saves"
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulator.load_save_state((_SAVES / "flannery_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import calculate_path, PathFindingError

LAV, R112, R111 = MapRSE.LAVARIDGE_TOWN, MapRSE.ROUTE112, MapRSE.ROUTE111


def show_path(frm, to, label, **kw):
    try:
        wps = calculate_path(frm, to, **kw)
    except PathFindingError as e:
        print(f"{label}: NO PATH ({str(e)[:70]})")
        return None
    except Exception as e:
        print(f"{label}: err {type(e).__name__}: {str(e)[:70]}")
        return None
    # summarize the course: per-map list of (min_y, max_y, count)
    per_map = {}
    for w in wps:
        name = MapRSE(w.map).name if not isinstance(w.map, MapRSE) else w.map.name
        x, y = w.coordinates
        lo, hi, n = per_map.get(name, (999, -1, 0))
        per_map[name] = (min(lo, y), max(hi, y), n + 1)
    print(f"{label}: PATHABLE ({len(wps)} steps) course:")
    for name, (lo, hi, n) in per_map.items():
        print(f"    {name}: y {lo}..{hi} ({n} steps)")
    return wps


print("=== avoid_scripted_events=False ===")
show_path((LAV, (9, 7)), (R111, (18, 99)), "Lav->R111(18,99)",
          avoid_encounters=False, avoid_scripted_events=False)
print("=== avoid_scripted_events=True + avoid_encounters=True (navigate_to defaults) ===")
show_path((LAV, (9, 7)), (R111, (18, 99)), "Lav->R111(18,99) [safe]",
          avoid_encounters=True, avoid_scripted_events=True)
print("=== rock staging ===")
show_path((R111, (18, 99)), (R111, (18, 100)), "R111(18,99)->(18,100) [smash staging]",
          avoid_encounters=False, avoid_scripted_events=False)
print("=== R111 south from staging after smash (simulate: path from (18,102)) ===")
show_path((R111, (18, 102)), (MapRSE.MAUVILLE_CITY, (19, 6)), "R111(18,102)->Mauville [safe]",
          avoid_encounters=True, avoid_scripted_events=True)
print("=== sanity: desert seal — can the static planner cross the desert mid-section? ===")
show_path((R111, (18, 30)), (R111, (18, 99)), "R111(18,30)->south(18,99) desert crossing",
          avoid_encounters=False, avoid_scripted_events=False)
print("=== where does the desert seal begin? binary-search southward reach from (13,90) ===")
for y in (88, 84, 80, 76, 72, 68, 60, 50):
    show_path((R111, (13, 90)), (R111, (18, y)), f"R111(13,90)->(18,{y})",
              avoid_encounters=False, avoid_scripted_events=False)
print("done")
