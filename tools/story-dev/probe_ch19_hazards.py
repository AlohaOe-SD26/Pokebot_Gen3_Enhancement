"""§Ch19 PRE-BUILD HAZARD CHECKS — test the predictions BEFORE writing the chapter.

‼ WHY. An adversarial planning pass predicted, in advance and with citations, exactly how the first
driven run of §Ch19 would fail. Predictions are NOTES, not truth — this project's rule — but they
are cheap to test, and a prediction that survives a test is worth more than any amount of careful
reasoning. Each check below is one the planner nominated, with its predicted outcome written down
BEFORE the run so the result cannot be rationalised afterwards.

  H1  The bot cannot walk out of the Mossdeep Gym. (23,8) — where §Ch18 leaves the player — is an
      11-tile collision island whose only cheap exit is (21,6), a COORD EVENT, which no warp-graph
      solver reads. PREDICT: a path from (23,8) to the gym door (7,35) FAILS, while the control path
      to (21,6) SUCCEEDS.
  H2  No party member can learn Dive and the party is full. PREDICT: zero learners, six Pokémon.
      ‼ Note what this does and does not block: RECEIVING HM08 needs no learner, so §Ch19/§Ch20 are
      unaffected. It is the SEAFLOOR CAVERN that is gated, because the bot must actually dive.
  H5  Mossdeep City is cut in two by the five Team Magma NPCs the gym victory spawns, so a single
      route from the gym to the Space Center cannot exist. PREDICT: a path from the gym door area to
      the Space Center approach (64,16) FAILS, or returns a route crossing the x=44 land bridge that
      the NPCs occupy.

‼ KI-60 APPLIES TO EVERY RESULT HERE: `calculate_path` never validates its SOURCE tile, so a result
is evidence about the DESTINATION only. Each check therefore asserts the avatar's real position
first, rather than trusting where the handoff says it is.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch19_hazards.py
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar
from modules.pokemon_party import get_party

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_mossdeep_gym.ss1"
line = "=" * 100
results: list[tuple[str, bool, str]] = []


def record(label: str, predicted_ok: bool, detail: str) -> None:
    results.append((label, predicted_ok, detail))
    print(f"  [{'AS PREDICTED' if predicted_ok else 'PREDICTION WRONG'}] {label}\n        {detail}")


def path_between(map_enum, source, destination):
    """Returns (ok, description). Never raises — a failure IS the measurement."""
    try:
        waypoints = calculate_path(get_map_data(map_enum, source), get_map_data(map_enum, destination))
        return True, f"path found, {len(waypoints)} waypoint(s)"
    except PathFindingError as error:
        return False, f"PathFindingError: {str(error)[:110]}"
    except Exception as error:  # noqa: BLE001 — an errored plan is reported, never hidden
        return False, f"{type(error).__name__}: {str(error)[:110]}"


context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(90):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
here_map = MapRSE(tuple(avatar.map_group_and_number))
here_tile = tuple(avatar.local_coordinates)

print(line)
print("§Ch19 PRE-BUILD HAZARD CHECKS")
print(line)
print(f"\nanchor: {ANCHOR.name}")
print(f"avatar: {here_map.name} {here_tile}   (‼ asserted, not assumed — KI-60)")

# ---------------------------------------------------------------- H1
print("\n" + line)
print("H1 — can the bot walk OUT of the gym from where §Ch18 leaves it?")
print(line)
print()
if here_map is not MapRSE.MOSSDEEP_CITY_GYM:
    # ‼ H1 IS NOW A REGRESSION GUARD RATHER THAN A HAZARD CHECK. When first run, this anchor stood
    # on (23,8) and the gym door was unreachable — §Ch18 passed its own test while stranding the
    # run. §Ch18 now exits via the (21,6) coord warp and ends in Mossdeep City, so the anchor being
    # OUTSIDE the gym is the fix, and the check is inverted to keep it that way.
    record(
        "H1 FIXED — the post-gym anchor is no longer stranded inside the gym",
        here_map is MapRSE.MOSSDEEP_CITY,
        f"anchor stands on {here_map.name} {here_tile}. §Ch18 now leaves via (21,6) -> (7,30) -> "
        "the door. Were this back inside the gym, §Ch19's first navigation would raise "
        "PathFindingError with no hint that the gym was the cause.",
    )
else:
    to_door, door_detail = path_between(MapRSE.MOSSDEEP_CITY_GYM, here_tile, (7, 35))
    to_coord_warp, coord_detail = path_between(MapRSE.MOSSDEEP_CITY_GYM, here_tile, (21, 6))
    print(f"  {here_tile} -> gym door (7,35) : {door_detail}")
    print(f"  {here_tile} -> (21,6) CONTROL  : {coord_detail}")
    record(
        "H1 the gym door is NOT reachable by walking",
        not to_door,
        "the leaders' platform is an island; the door is unreachable"
        if not to_door else "‼ the door IS reachable — H1 refuted, the exit is a normal walk",
    )
    record(
        "H1 control: (21,6) IS reachable",
        to_coord_warp,
        "the coord-event exit is walkable, so it is a usable escape"
        if to_coord_warp else "‼ the control failed too — something more basic is wrong",
    )

# ---------------------------------------------------------------- H2
print("\n" + line)
print("H2 — can anybody learn Dive, and is the party full?")
print(line)
print()
party = [mon for mon in get_party() if mon is not None]
try:
    from modules.items import get_item_by_name

    # ‼ The item is called "HM08", not "HM08 Dive" — the first spelling raised KeyError and cost this
    # check a run. `modules/data/items.json` is the authority; do not guess an item name.
    dive = get_item_by_name("HM08")
    learners = []
    for index, mon in enumerate(party):
        try:
            if mon.species.can_learn_tm_hm(dive):
                learners.append(f"{index}:{mon.species.name}")
        except Exception:  # noqa: BLE001 — try the alternate API rather than give up silently
            compatible = getattr(mon.species, "tm_hm_learnset", None)
            if compatible is not None and dive in compatible:
                learners.append(f"{index}:{mon.species.name}")
    detail = f"party {len(party)}/6: {', '.join(m.species.name + ' L' + str(m.level) for m in party)}"
    print(f"  {detail}")
    print(f"  Dive learners in party: {learners or 'NONE'}")
    record(
        "H2 no party member can learn Dive, and the party is full",
        not learners and len(party) >= 6,
        f"{len(learners)} learner(s), party size {len(party)}. ‼ This does NOT block receiving HM08 "
        "(a script gift needs no learner) — it blocks USING Dive, i.e. the Seafloor Cavern.",
    )
except Exception as error:  # noqa: BLE001 — say what could not be read rather than nothing
    record("H2 could not be evaluated", False, f"{type(error).__name__}: {str(error)[:150]}")

# ---------------------------------------------------------------- H5
print("\n" + line)
print("H5 — is Mossdeep City cut in two by the Team Magma wall?")
print(line)
print()
gym_door_area = (38, 10)          # just outside the gym
space_center_approach = (64, 16)  # the tile you stand on to enter the Space Center
trigger_line = (41, 23)           # one of the six cutscene trigger tiles
ok_full, detail_full = path_between(MapRSE.MOSSDEEP_CITY, gym_door_area, space_center_approach)
ok_trigger, detail_trigger = path_between(MapRSE.MOSSDEEP_CITY, gym_door_area, trigger_line)
print(f"  (38,10) -> Space Center approach (64,16) : {detail_full}")
print(f"  (38,10) -> trigger line (41,23)          : {detail_trigger}")
print("\n  ‼ These are read from the ROM collision layer for a map the player is NOT standing on,")
print("    so the five Magma NPCs are NOT modelled as obstacles here. A path found now can still")
print("    fail on approach, when the engine materialises them near the camera. That divergence is")
print("    itself the hazard, and it is why the chapter routes to the trigger line FIRST.")
record(
    "H5 the trigger line is reachable (so a two-leg route is viable)",
    ok_trigger,
    detail_trigger,
)

print("\n" + line)
print("SUMMARY")
print(line)
confirmed = sum(1 for _, ok, _ in results if ok)
print(f"\n  {confirmed} / {len(results)} predictions held\n")
for label, ok, _ in results:
    print(f"    {'HELD  ' if ok else 'FAILED'}  {label}")
print("""
  A prediction that FAILED is not a bad outcome — it means the hazard is not real and the build can
  skip a defence it would otherwise have carried forever. What matters is that neither answer was
  decided after seeing the result.
""")
print(line)
