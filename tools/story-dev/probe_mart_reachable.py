"""`#24-marthreachable` — ⛔ WHERE CAN THE BOT ACTUALLY BUY? OBSERVE-ONLY.

USER RULING 12 (2026-09-25, `06-DECISIONS-LOG.md`) rules that a lost Elite Four run **RESTOCKS AND
RETRIES**. That needs a §Ch24-owned restock leg — and `#24-marthreachable` is filed as the PROBE
that must run *before* any restock code, because `probe_league_lobby_facts.py` measured the League
Mart **REFUSING** (`PathFindingError`) from `post_league_lobby.ss1` (build-spec hazard **H7**).

⛔⛔ **A LEG THAT PLANS TO BUY SOMEWHERE THE PLANNER REFUSES IS THE `KI-48` SILENT-HANG SHAPE**, and
inside the League there is no retreat. So this settles it by measurement first.

‼ **THE TRAP THIS PROBE IS BUILT AROUND.** `get_map_objects()` is a **CAMERA-RANGE WINDOW** — an
object outside ~7-9 tiles is absent from it WHETHER OR NOT IT EXISTS. So *"the clerk isn't in the
list"* is **NOT** evidence the clerk isn't there. ⇒ this probe prints the **ROM TEMPLATE** objects
(where NPCs are *defined* to be) beside the **LIVE** objects (what is actually loaded right now),
and refuses to conclude absence from the live list alone.

⛔ **AND IT CARRIES ITS OWN POSITIVE CONTROL, DERIVED FROM WHERE WE ACTUALLY STAND** — never a
hardcoded tile. If the control REFUSES, the instrument is broken and every other refusal on the run
is meaningless. A probe whose failure mode is indistinguishable from its finding is worthless.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_mart_reachable.py [fixture.ss1 ...]
      (default: the two that matter — inside the lobby, and the post-whiteout RESPAWN tile)
"""

import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a result
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import load_profile_by_name  # noqa: E402

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map import get_map_data, get_map_objects  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402
from modules.map_path import calculate_path  # noqa: E402
from modules.player import get_player_avatar  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
BAR = "=" * 100

#: ⛔ THE TWO THAT MATTER, and WHY each — a fixture list without reasons rots.
#:   * `post_league_lobby.ss1`   — standing INSIDE the lobby, where the Mart is claimed to be.
#:   * `post_ch24_atdoor_L75.ss1` — `EVER_GRANDE_CITY (18,6)`, which is **THE POST-WHITEOUT RESPAWN
#:     TILE** (one tile south of the League door). ⭐ This is the one RULING 12 actually needs: after
#:     a loss the bot wakes up HERE, and the restock leg has to start from it.
DEFAULT_FIXTURES = ["post_league_lobby.ss1", "post_ch24_atdoor_L75.ss1"]

#: Claimed landmarks per map. ‼ These are CLAIMS to be tested, not facts to rely on.
LANDMARKS = {
    MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F: {
        "nurse stand (victory_road.py:391)": (3, 4),
        "MART clerk approach (the H7 claim)": (16, 3),
        "lobby south exit (toward Ever Grande)": (9, 11),
    },
}


def _walkable_neighbour(map_enum, tile):
    """A control target derived from where we ACTUALLY stand — never hardcoded.

    ⛔ It must also not be a WARP: `map_path.py` only PENALISES a non-destination warp rather than
    forbidding it, so routing 'successfully' onto one proves nothing about ordinary walking.
    """
    x, y = tile
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        cand = (x + dx, y + dy)
        try:
            data = get_map_data(map_enum, cand)
            if data.collision == 0 and not data.is_surfable and "warp" not in str(data.map_type).lower():
                return cand
        except Exception:  # noqa: BLE001 - an unreadable neighbour is simply not a candidate
            continue
    return None


def _report(fixture: str) -> int:
    save = SAVES / fixture
    if not save.is_file():
        print(f"  ABORT (instrument, not a result) — no fixture: {fixture}")
        return 1
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    try:
        map_enum = MapRSE(avatar.map_group_and_number)
    except Exception:  # noqa: BLE001 - an unknown map id is a result; stop honestly
        print(f"  ABORT — unknown map id {avatar.map_group_and_number}")
        return 1
    tile = tuple(avatar.local_coordinates)

    print(BAR)
    print(f"  FIXTURE {fixture}   standing: {map_enum.name} {tile}")
    print(BAR)

    # ---- THE CONTROL, FIRST. A refusal below means nothing if the planner is simply broken here.
    control = _walkable_neighbour(map_enum, tile)
    if control is None:
        print("  ⛔ CONTROL UNAVAILABLE — no ordinary walkable neighbour. Every path result below is")
        print("     UNINTERPRETABLE; treat this fixture as un-probed rather than as a finding.")
    else:
        try:
            n = len(calculate_path((map_enum, tile), (map_enum, control)))
            print(f"  ✅ CONTROL: path to adjacent {control} = {n} waypoint(s) — the planner works from")
            print("     this position, so a REFUSAL below is a property of the DESTINATION, not the instrument.")
        except Exception as error:  # noqa: BLE001 - a broken control is the most important reading here
            print(f"  ⛔⛔ CONTROL REFUSED ({type(error).__name__}) — THE INSTRUMENT IS BLIND ON THIS MAP.")
            print("     ⇒ Do NOT read any refusal below as 'unreachable'. Fix the control first.")

    # ---- ROM TEMPLATES vs LIVE OBJECTS ---------------------------------------------------------
    # ‼ THE WHOLE POINT. `MapLocation.objects` is the ROM's definition (ORIGINAL positions, always
    # present); `get_map_objects()` is the LIVE, CAMERA-RANGE-WINDOWED list. Printing only the
    # second is how "the clerk isn't spawned" gets asserted from a window that simply didn't reach.
    try:
        templates = list(get_map_data(map_enum, tile).objects)
    except Exception as error:  # noqa: BLE001 - recorded, never fatal
        templates = []
        print(f"  ⚠ ROM template objects unreadable: {type(error).__name__}: {error}")
    try:
        live = [(tuple(o.current_coords), "isPlayer" in o.flags) for o in get_map_objects()]
    except Exception as error:  # noqa: BLE001
        live = []
        print(f"  ⚠ live objects unreadable: {type(error).__name__}: {error}")

    print(f"\n  ROM TEMPLATE objects on this map: {len(templates)}")
    for t in templates[:20]:
        coords = getattr(t, "local_coordinates", "<?>")
        kind = getattr(t, "kind", getattr(t, "script_label", "<?>"))
        print(f"    template @ {str(coords):>10}   {str(kind)[:60]}")
    print(f"\n  LIVE objects loaded right now: {len(live)}  "
          f"(⛔ CAMERA-RANGE WINDOW — an empty/short list is NOT proof of absence)")
    for coords, is_player in live:
        print(f"    live     @ {str(coords):>10}   {'<- PLAYER' if is_player else ''}")

    # ---- CAN WE ROUTE TO A SHOP? ---------------------------------------------------------------
    marks = LANDMARKS.get(map_enum)
    if not marks:
        print(f"\n  (no landmark claims recorded for {map_enum.name} — position and objects above are")
        print("   the reading; add landmarks here only once something claims one.)")
    else:
        print("\n  ROUTING TO THE CLAIMED LANDMARKS:")
        for label, dest in marks.items():
            try:
                n = len(calculate_path((map_enum, tile), (map_enum, dest)))
                verdict = f"{n} waypoint(s)" + ("  (0 = already standing on it)" if n == 0 else "")
            except Exception as error:  # noqa: BLE001 - a refusal IS the reading we came for
                verdict = f"REFUSED — {type(error).__name__}: {str(error)[:60]}"
            print(f"    {label:<44} -> {verdict}")

    # ---- ⭐ THE SWEEP THAT ACTUALLY ANSWERS THE QUESTION ----------------------------------------
    # ‼ A single hardcoded "clerk approach" tile can only ever tell you whether THAT GUESS routes.
    # If it refuses you cannot tell "the clerk is unreachable" from "you guessed the wrong tile".
    # ⇒ derive the targets from the ROM TEMPLATES and try EVERY neighbour of each, so the reading is
    # "reachable from X" or "reachable from nowhere" — which are different findings.
    if templates:
        print("\n  ⭐ NEIGHBOUR SWEEP — for each ROM-defined object, can we stand next to it?")
        print("     (a counter NPC is talked to from an adjacent tile; the object's OWN tile is solid)")
        for t in templates:
            coords = getattr(t, "local_coordinates", None)
            if coords is None:
                continue
            ox, oy = tuple(coords)
            if (ox, oy) == tile:
                continue
            reachable = []
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                cand = (ox + dx, oy + dy)
                try:
                    coll = get_map_data(map_enum, cand).collision
                except Exception:  # noqa: BLE001
                    coll = "?"
                if coll != 0:
                    reachable.append(f"{cand}=WALL")
                    continue
                try:
                    n = len(calculate_path((map_enum, tile), (map_enum, cand)))
                    reachable.append(f"{cand}={n}wp")
                except Exception as error:  # noqa: BLE001 - a refusal is the reading
                    reachable.append(f"{cand}=REFUSED({type(error).__name__})")
            print(f"    object @ {str((ox, oy)):>10}  ->  " + "  ".join(reachable))
            # ⭐⭐ AND AT COUNTER DISTANCE (2 tiles). MEASURED on this very map: the NURSE object sits
            # at (3,2) with ALL FOUR neighbours WALL, yet `LEAGUE_NURSE_STAND = (3,4)` works — because
            # a Gen-3 shop/centre NPC stands BEHIND A SOLID COUNTER and is talked to ACROSS it.
            # ⇒ "adjacent" is the WRONG model for a counter, and testing only adjacency is how
            # "the clerk is unreachable" gets concluded from a tile that was never the stand tile.
            far = []
            for dx, dy in ((0, 2), (0, -2), (2, 0), (-2, 0)):
                cand = (ox + dx, oy + dy)
                try:
                    coll = get_map_data(map_enum, cand).collision
                except Exception:  # noqa: BLE001
                    coll = "?"
                if coll != 0:
                    far.append(f"{cand}=WALL")
                    continue
                try:
                    n = len(calculate_path((map_enum, tile), (map_enum, cand)))
                    far.append(f"{cand}={n}wp")
                except Exception as error:  # noqa: BLE001
                    far.append(f"{cand}=REFUSED({type(error).__name__})")
            print(f"    {'':>10}  counter-distance (2):  " + "  ".join(far))

    print(BAR)
    return 0


def main() -> int:
    fixtures = sys.argv[1:] or DEFAULT_FIXTURES
    print(BAR)
    print("  `#24-marthreachable` — WHERE CAN THE BOT ACTUALLY BUY?  ⛔ OBSERVE-ONLY:")
    print("  no button is pressed, no step is taken, nothing is bought.")
    print("  ⇒ It blocks `#24-restockleg`, which USER RULING 12 authorises but which must not be")
    print("    written against a shop the planner refuses to route to.")
    print(BAR)
    rc = 0
    for fixture in fixtures:
        rc |= _report(fixture)

    print("\n  ⛔ WHAT THIS PROBE DOES **NOT** SETTLE, STATED SO NOTHING OVER-READS IT:")
    print("     * Whether the clerk would SELL to us, or what the shop STOCKS. Routing to a tile is")
    print("       not a transaction, and `#24-restockleg` needs prices, not just reachability.")
    print("     * Whether the money exists. The basket is ₽54,300 against a measured ₽1,741, and a")
    print("       whiteout HALVES what remains — reachability does not touch that problem.")
    print("     * Whether a clerk absent from the LIVE list is really absent. Read the ROM template")
    print("       count beside it; an empty camera window is not an absence.")
    print(BAR)
    return rc


if __name__ == "__main__":
    sys.exit(main())
