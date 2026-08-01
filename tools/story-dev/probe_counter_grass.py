"""KI-44 probe: is the counter's configured training grass a sane place to train?

NO EMULATION LOOP — boots the ROM only so the wild-encounter tables are readable, then
asks static questions. Costs seconds, not frames.

WHY THIS EXISTS. Batch4 (`x4-runs/20260731-201554`) caught a **Machop L15 in FIERY_PATH**
and then tried to train it at `PETALBURG_TRAINING_GRASS = (ROUTE102, (9, 2))` — the grass
configured for the BOSS (Norman, in Petalburg), not for where the counter actually is.
Training failed 7 of 7 with the bot stranded on ROUTE103 (45, 7).

Two separate questions, and the log only showed the first:
  1. can the bot GET there?            -> no (KI-44's visible symptom)
  2. is it worth going even if it can? -> this probe

`story_mode.py:739` already records that Route 102 is "L4 ... ~25 xp a kill, i.e. never" —
it is the pathological case `FODDER_LEVEL_GAP` was invented for. This prints the numbers
side by side so the fix is chosen on evidence rather than on that comment.

    cd tools/story-dev
    PYTHONUTF8=1 py -3.12 probe_counter_grass.py --profile probe-grass
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--profile", default="probe-grass")
ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"])
ap.add_argument(
    "--state",
    default=None,
    help="optional .ss1 in saves/ — load it so the LIVE reachability predicate has a real "
    "player position, which is the only way to know whether the KI-44 fix actually fires",
)
args = ap.parse_args()

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / f"{args.build}-pokebot"))

from modules.context import context  # noqa: E402
from modules.profiles import create_profile, profile_directory_exists, load_profile_by_name  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402
from modules.game import set_rom  # noqa: E402

if not profile_directory_exists(args.profile):
    roms = list_available_roms()
    assert roms, "no ROMs found in roms/"
    create_profile(args.profile, roms[0])
profile = load_profile_by_name(args.profile)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

# The encounter tables are read through the emulator's memory view, not straight off the
# ROM file, so an emulator instance is required even though we never step a frame.
from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0

from modules.map import get_wild_encounters_for_map  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402


def land_band(map_enum):
    """(min, max) land-encounter level for a map, or None."""
    try:
        enc = get_wild_encounters_for_map(*map_enum.value)
        if enc is None or not enc.land_encounters:
            return None
        return (min(e.min_level for e in enc.land_encounters),
                max(e.max_level for e in enc.land_encounters))
    except Exception as error:  # noqa: BLE001
        return f"ERR {type(error).__name__}: {error}"


# The grass Norman's config sends a counter to, vs the map the counter is caught on and
# its immediate neighbours (all reachable on foot from Fiery Path).
PLACES = ["ROUTE102", "FIERY_PATH", "ROUTE112", "JAGGED_PASS", "ROUTE111", "MT_CHIMNEY"]

print(f"build={args.build}  rom={profile.rom.id}\n")
print(f"{'map':<14}{'land wild levels':<20}note")
print("-" * 64)
bands = {}
for name in PLACES:
    m = getattr(MapRSE, name, None)
    if m is None:
        print(f"{name:<14}{'(no such map)':<20}")
        continue
    b = land_band(m)
    bands[name] = b
    note = ""
    if name == "ROUTE102":
        note = "<- PETALBURG_TRAINING_GRASS, what Norman's cfg uses"
    elif name == "FIERY_PATH":
        note = "<- where the Machop counter is actually CAUGHT"
    shown = f"{b[0]}-{b[1]}" if isinstance(b, tuple) else str(b)
    print(f"{name:<14}{shown:<20}{note}")

print("\n--- the decision this drives -------------------------------------------")
r102, fiery = bands.get("ROUTE102"), bands.get("FIERY_PATH")
if isinstance(r102, tuple) and isinstance(fiery, tuple):
    print(f"A freshly-caught counter is L{fiery[0]}-{fiery[1]} BY CONSTRUCTION (it came off")
    print(f"FIERY_PATH's own table). Training it at ROUTE102 means grinding L{r102[0]}-{r102[1]} wilds")
    print("with a mon that is already far above them — the exact 'i.e. never' case")
    print("story_mode.py:739 documents, AND it is eight maps away across a route the")
    print("bot demonstrably cannot cross (KI-44: stranded at ROUTE103 (45,7), 6/7 runs).")
    print()
    print("Whereas the hunting ground it is standing on is level-matched by definition")
    print("and needs ZERO travel.")
else:
    print("could not read one of the two tables; see above")

# Frame-cost model, the same one train_counter uses, for a L15 -> L21 Machop.
print("\n--- estimate_frames_to_level (the model train_counter actually gates on) ---")
try:
    from types import SimpleNamespace

    from modules.pokemon import get_species_by_name
    from modules.story.training_areas import estimate_frames_to_level

    machop = SimpleNamespace(level=15, species=get_species_by_name("Machop"))
    for name in ("ROUTE102", "FIERY_PATH"):
        b = bands.get(name)
        if not isinstance(b, tuple):
            continue
        try:
            est = estimate_frames_to_level(machop, 21, b[1])
            print(f"  L15 -> L21 on {name:<12} (wild L{b[1]}): {est:>12,.0f} frames")
        except Exception as error:  # noqa: BLE001
            print(f"  L15 -> L21 on {name:<12}: ERR {type(error).__name__}: {error}")
    print("\n  (MAX_PREP_TRAINING_FRAMES = 250,000 is the budget these are gated against.)")
except Exception as error:  # noqa: BLE001
    print(f"  model unavailable: {type(error).__name__}: {error}")

# --- the question the static tables CANNOT answer -----------------------------
# `counter_training_ground` only helps if the LIVE reachability predicate actually admits
# a ground from where the counter was caught. If it rejects everything, the fix silently
# falls back to the boss's patch and nothing changes. That needs a real player position.
if args.state:
    print("\n--- LIVE: does the KI-44 fix actually fire from a real position? ---")
    state = Path(__file__).parent / "saves" / args.state
    if not state.is_file():
        state = Path(args.state)
    if not state.is_file():
        print(f"  no such state: {args.state}")
    else:
        context.emulator.load_save_state(state.read_bytes())
        # Let the frame settle so the map/party readers see a consistent world.
        for _ in range(10):
            context.emulator.run_single_frame()
        from modules.player import get_player_avatar

        from modules.story.counter_hunt import counter_training_ground
        from modules.story.training_areas import best_training_area

        try:
            av = get_player_avatar()
            here = MapRSE(tuple(av.map_group_and_number)).name
            print(f"  loaded {state.name}: standing on {here} {tuple(av.local_coordinates)}")
        except Exception as error:  # noqa: BLE001
            print(f"  could not read the avatar: {type(error).__name__}: {error}")

        from plugins.custom_modes.story_mode import _counter_area_allowed

        for lvl in (15, 16, 20):
            pick = best_training_area(lvl, allow=_counter_area_allowed)
            print(f"  best_training_area(L{lvl}, allow=_counter_area_allowed) -> {pick}")

        norman_cfg = {"grass": (MapRSE.ROUTE102, (9, 2)), "heal": "PetalburgCity"}
        grass, heal = counter_training_ground(15, norman_cfg)
        same = grass is not None and tuple(grass) == tuple(norman_cfg["grass"])
        print(f"\n  counter_training_ground(L15, Norman cfg) -> grass={grass} heal={heal}")
        print(f"  => {'FELL BACK to the boss patch (fix did NOT fire)' if same else 'RELOCATED (fix fired)'}")
