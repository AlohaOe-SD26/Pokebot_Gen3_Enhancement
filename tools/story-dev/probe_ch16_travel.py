"""§Ch16 increment 1 recon: is the SLATEPORT leg plannable at all, and where does it break?
NO EMULATION LOOP — static `calculate_path`, seconds. Run this BEFORE spending a driven run.

WHY STATIC FIRST. The driven travel leg for §Ch15 cost multiple 10-minute runs to learn things a
30-second static check would have narrowed. A static FAIL is a strong signal to plan around; a
static OK is "worth driving", nothing more.

‼‼ AND A STATIC "OK" HAS LIED HERE BEFORE — this is the single most important caveat in this file.
`calculate_path` reads the ROM's LAYOUT. The Jagged Pass hideout door read **"2 waypoints"** while
the game had it WALLED SHUT behind a `setmetatile` that only a coord trigger removes, and that
false YES is what made the door look reachable for three weeks. `get_map_data` cannot see
metatile changes, hidden objects, or NPCs standing in doorways. **Never promote a static OK to a
finding.**

WHAT THIS ANSWERS, from the §Ch16 anchor `post_maxie.ss1`:
  1. Where does the anchor actually stand? (reported as a MapRSE **enum**, never `map_name` —
     that is a display LABEL and reads "MAUVILLE CITY" for MAUVILLE_CITY_GYM.)
  2. The long haul: can the planner span **MAUVILLE_CITY -> SLATEPORT_CITY**? ‼ KI-48 says direct
     navigation cannot walk ROUTE110 -> MAUVILLE_CITY (3/3 failures, it enumerates only Mauville's
     six building doors and never the map connection). We travel the OPPOSITE way here, which may
     or may not share the fault — that is exactly what this probe is for, rather than assuming.
  3. The last leg: **SLATEPORT_CITY -> the harbor door (28,12)** (warp id 8 -> harbor (11,14)).
  4. Inside the harbor: door **(11,14) -> trigger 3 (8,14)**.

‼ CONTROLS, because a probe that returns FAIL for everything has found a common SYMPTOM, not a
common cause (the prevention rule from `08-MISTAKES` 2026-07-30):
  * a SHORT intra-map hop on each map must plan — if the control fails, the planner is not
    answering at all and every FAIL below is uninterpretable;
  * the anchor's era is asserted (`SLATEPORT_HARBOR_STATE == 1`) so a wrong-era save cannot be
    mistaken for a routing failure — the mistake that cost seven probes on 2026-08-10.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch16_travel.py
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

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
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import _event_vars, get_event_var
from modules.player import get_player_avatar

SAVES = pathlib.Path(__file__).resolve().parent / "saves"
ANCHOR = "post_maxie.ss1"

HARBOR_DOOR_CITY = (28, 12)   # SLATEPORT_CITY warp 8 -> SLATEPORT_CITY_HARBOR (11,14)
HARBOR_LANDING = (11, 14)
TRIGGER3 = (8, 14)

line = "=" * 88


def plan(a_map: MapRSE, a: tuple[int, int], b_map: MapRSE, b: tuple[int, int]) -> str:
    try:
        start = get_map_data(a_map, a)
        end = get_map_data(b_map, b)
        return f"OK, {len(calculate_path(start, end))} waypoints"
    except PathFindingError as error:
        return f"FAIL ({str(error)[:110]})"
    except Exception as error:  # noqa: BLE001 - a probe reports, it does not crash
        return f"FAIL ({type(error).__name__}: {str(error)[:110]})"


print(line)
print("§Ch16 TRAVEL RECON — static only. A static OK means 'worth driving', NOT 'proven'.")
print(line)

path = SAVES / ANCHOR
if not path.is_file():
    raise SystemExit(f"‼ missing anchor {path}. Run probe_ch16_anchor.py's instructions first.")
context.emulator.load_save_state(path.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
here_map = MapRSE(tuple(avatar.map_group_and_number))
here_tile = tuple(avatar.local_coordinates)
print(f"\n0. THE ANCHOR — {ANCHOR}")
print(f"   standing on {here_map.name}{here_tile}")

# ---- ERA ASSERTION, before any routing conclusion ----
if "SLATEPORT_HARBOR_STATE" not in _event_vars:
    raise SystemExit("‼ UNTRUSTED: 'SLATEPORT_HARBOR_STATE' is not a known var name.")
harbor_state = get_event_var("SLATEPORT_HARBOR_STATE")
print(f"   SLATEPORT_HARBOR_STATE={harbor_state}  ({'correct era' if harbor_state == 1 else '‼ WRONG ERA'})")
if harbor_state != 1:
    print("\n‼ STOP. This anchor is not the §Ch16 era, so any routing result below would be")
    print("  answering the wrong question. Fix the anchor first (probe_ch16_anchor.py).")
    raise SystemExit(1)

print("\n1. PLANNER CONTROLS — a short hop on each map must plan, or every FAIL below is noise")
# ‼ PICK THE CONTROL TILE EMPIRICALLY, DO NOT GUESS ONE. The first draft used
# SLATEPORT_CITY (28,13) -> (28,14) and it FAILED — not because the planner was broken but
# because (28,14) simply is not walkable. **A control that can legitimately fail is not a
# control**; it made a healthy planner look dead and would have sent the next reader hunting a
# routing bug that does not exist. (Same family as the playbook's "a liveness check whose success
# condition the driven action cannot produce".) Try the four neighbours and use the first that
# plans; if NONE plan, THAT is the real negative and it is reported as such.
def _first_walkable_neighbour(m: MapRSE, origin: tuple[int, int]) -> tuple[str, tuple[int, int] | None]:
    x, y = origin
    for cand in ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)):
        if plan(m, origin, m, cand).startswith("OK"):
            return f"{m.name} intra-map", cand
    return f"{m.name} intra-map", None


controls = []
for _m, _o in (
    (MapRSE.SLATEPORT_CITY, (28, 13)),
    (MapRSE.SLATEPORT_CITY_HARBOR, HARBOR_LANDING),
    (MapRSE.MAUVILLE_CITY, (22, 6)),
):
    _label, _dest = _first_walkable_neighbour(_m, _o)
    if _dest is None:
        print(f"   {_label:<28} {_o} -> ‼ NO neighbour plans at all — the planner is dead on this map")
        control_failed_hard = True
        continue
    controls.append((_label, _m, _o, _m, _dest))
control_ok = True
control_failed_hard = False
for label, am, a, bm, b in controls:
    r = plan(am, a, bm, b)
    print(f"   {label:<28} {a} -> {b}: {r}")
    if r.startswith("FAIL"):
        control_ok = False
if not control_ok:
    print("   ‼ A CONTROL FAILED — the planner is not answering on that map. Treat the legs below")
    print("     as UNINTERPRETABLE rather than as routing failures.")

print("\n2. THE LONG HAUL — MAUVILLE_CITY -> SLATEPORT_CITY (the KI-48 corridor, opposite direction)")
print(f"   MAUVILLE(22,6) -> SLATEPORT(28,13): {plan(MapRSE.MAUVILLE_CITY, (22, 6), MapRSE.SLATEPORT_CITY, (28, 13))}")
print(f"   MAUVILLE(22,6) -> ROUTE110(14,97):  {plan(MapRSE.MAUVILLE_CITY, (22, 6), MapRSE.ROUTE110, (14, 97))}")
# ‼ LOCALISE THE BREAK. Mauville->Route110 planning while Mauville->Slateport does not means the
# failure is in the SECOND half. Ask the second half on its own rather than inferring it.
print(f"   ROUTE110(14,97) -> SLATEPORT(28,13): {plan(MapRSE.ROUTE110, (14, 97), MapRSE.SLATEPORT_CITY, (28, 13))}")
print(f"   ROUTE110(14,97) -> SLATEPORT(14,4):  {plan(MapRSE.ROUTE110, (14, 97), MapRSE.SLATEPORT_CITY, (14, 4))}")

print("\n3. THE LAST LEG — SLATEPORT_CITY -> the harbor door, then inside the harbor")
print(f"   SLATEPORT(28,13) -> harbor door{HARBOR_DOOR_CITY}: "
      f"{plan(MapRSE.SLATEPORT_CITY, (28, 13), MapRSE.SLATEPORT_CITY, HARBOR_DOOR_CITY)}")
print(f"   harbor{HARBOR_LANDING} -> trigger3{TRIGGER3}: "
      f"{plan(MapRSE.SLATEPORT_CITY_HARBOR, HARBOR_LANDING, MapRSE.SLATEPORT_CITY_HARBOR, TRIGGER3)}")

print("\n4. OUT OF THE DUNGEON — can the planner even leave the anchor's own map?")
print(f"   ‼ Expect FAIL: {here_map.name} exits by WARPS, and `calculate_path` does not cross them.")
print(f"   {here_map.name}{here_tile} -> JAGGED_PASS(16,20): "
      f"{plan(here_map, here_tile, MapRSE.JAGGED_PASS, (16, 20))}")

print("\n" + line)
print("READ THIS BEFORE ACTING ON THE ABOVE:")
print("  * A static OK is permission to DRIVE the leg, not evidence the leg works.")
print("  * A static FAIL on a WARP-connected pair is expected and means nothing — the chapter")
print("    must walk those legs explicitly, exactly as §Ch15's travel leg does.")
print("  * The real evidence is a driven run graded on SLATEPORT_HARBOR_STATE == 2 AND control.")
print(line)
