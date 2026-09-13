"""`#26-healmap-lavaridge` — from Route 112's LOWER section, which Poké Center can we actually walk to?

⛔ WHY THIS EXISTS. `_training_area_heal_map()` (`plugins/custom_modes/story_mode.py:1121`, `:1126`)
answers **LavaridgeTown** for both `ROUTE112` and `FIERY_PATH`. Our own `NO_RETURN_GROUNDS`
(`modules/story/training_areas.py`) records the opposite, MEASURED 2026-07-26:
    Lavaridge (9,6) -> ROUTE112 (11,36) = OK, 60 waypoints
    ROUTE112 (11,36) -> Lavaridge (9,6) = FAIL          <- "lower section cannot path back (ledges)"
Measured cost: `Cannot reach LAVARIDGE_TOWN` 79 times across the 2026-09 batches, 32 of 39 of them
from ROUTE112, via the chain
    counter-hunt in FIERY_PATH -> damaged -> [MAP] FIERY PATH(24,14) -> ROUTE 112(0,27) -> heal -> fail.

⛔⛔ THE QUESTION THIS ANSWERS IS *"WHICH CENTRE IS REACHABLE"*, AND IT IS DELIBERATELY NOT
*"SHOULD WE RE-MAP IT"*. The punch-list entry stops short of a table edit on purpose: "Mauville is
probably reachable" is exactly the kind of plausible map claim this project has been burned by.

‼‼ HOW TO READ THE RESULT — THE THREE OUTCOMES ARE NOT INTERCHANGEABLE. This classification is
lifted from `probe_counter_reachability.py`, which learned it the hard way (three of five cases came
back "not on connected maps", which is a TOOL limit, not a map fact):
  * `OK, N waypoints`        => genuinely walkable. STRONG, trustworthy evidence.
  * `NEEDS A WARP`           => `calculate_path` plans only across DIRECTLY CONNECTED maps and cannot
                                cross warps. This says NOTHING about reachability — wrong tool.
  * `FAIL on connected maps` => real, but STILL not proof of unreachable (KI-24: the tile planner
                                reads dual-elevation bridges as WALLS and once called Route 118
                                unreachable when it plainly is not).
⇒ A POSITIVE here is worth acting on. A NEGATIVE is "unproven" and needs the navigation instrument
(`_navigate_riding_out`, which DOES cross warps) before anyone edits a table on the strength of it.

⛔ THE CONTROL IS NOT OPTIONAL. `CONTROL_OK` re-runs the 2026-07-26 measurement that is already in
`NO_RETURN_GROUNDS` (Lavaridge -> ROUTE112, expected OK ~60 waypoints). If it does NOT pass, this
probe is broken and every other line it prints is meaningless — it reports ABORT and refuses to
answer. Without that, a probe that fails for a setup reason would print FAIL for every candidate and
read as "nothing is reachable", which is precisely the false conclusion this file exists to prevent.
(That is not hypothetical: querying `region_reach` offline earlier today returned False for all four
candidates — because it FAILS CLOSED with no ROM, not because anything was unreachable.)

Run: py -3.12 tools/story-dev/probe_heal_reachability.py
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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

from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import get_game_state
from modules.player import get_player_avatar, player_avatar_is_controllable

SAVES = REPO / "tools" / "story-dev" / "saves"
ANCHOR = "lavaridge.ss1"   # verified clean + pre-Norman by probe_counter_tiles.py

#: ⛔⛔ CORRECTED 2026-09-12 AFTER AN AGENT CAUGHT ME MEASURING FROM A TILE THE BOT BARELY USES.
#: The first version read `(26,36)` off the `[MAP] FIERY PATH -> ROUTE 112 pos=(...)` line, calling it
#: “the REAL tile”. **That `pos=` is the PRE-transition position** — the logger samples position
#: alongside the ALREADY-UPDATED map name, so the pair is internally inconsistent. The truth is the
#: next `[hb]`/`[STUCK]` heartbeat once standing on Route 112.
#: MEASURED over every FIERY_PATH->ROUTE112 exit in the 2026-09 batches (44 distinct tiles):
#:     (31, 9) x117    (26,34) x106    (6,4) x22    (6,7) x11    (11,37) x8    (26,36) x5
#: ⇒ (26,36) is real but RARE. Route 112 is ledge-split, so the answer can differ per tile — which is
#: exactly why this now measures from ALL the common ones and reports the spread instead of one.
FROM_TILES = [
    (MapRSE.ROUTE112, (31, 9)),    # most common landing
    (MapRSE.ROUTE112, (26, 34)),
    (MapRSE.ROUTE112, (6, 4)),
    (MapRSE.ROUTE112, (6, 7)),
    (MapRSE.ROUTE112, (11, 37)),
    (MapRSE.ROUTE112, (26, 36)),   # the tile the first (wrong) measurement used
]
#: The tile NO_RETURN_GROUNDS measured from, kept so this probe can reproduce that exact reading.
FROM_TILE_2026_07_26 = (MapRSE.ROUTE112, (11, 36))

#: Every Poké Center door, from `modules/map_data.py`'s `PokemonCenter` enum. ⛔ NOT hand-typed
#: coordinates — read the enum so a ROM/data change cannot silently desync this probe.
from modules.map_data import PokemonCenter

CANDIDATES = [
    ("LavaridgeTown  (what we map TODAY)", PokemonCenter.LavaridgeTown),
    ("FallarborTown", PokemonCenter.FallarborTown),
    ("MauvilleCity", PokemonCenter.MauvilleCity),
    ("VerdanturfTown", PokemonCenter.VerdanturfTown),
    ("PetalburgCity", PokemonCenter.PetalburgCity),
]


def path_result(src, dst):
    """Classify one `calculate_path` attempt into the THREE outcomes, never two."""
    try:
        path = calculate_path(src, dst, avoid_encounters=False, avoid_scripted_events=False)
        return "OK", f"OK, {len(path)} waypoints"
    except PathFindingError as error:
        text = str(error)
        if "not on connected maps" in text:
            return "WARP", "NEEDS A WARP — calculate_path cannot cross warps (wrong tool, not a map fact)"
        return "FAIL", f"FAIL on connected maps (real, but see KI-24) — {text[:110]}"
    except Exception as error:  # noqa: BLE001 - a probe must report, never crash the report
        return "ERROR", f"ERROR — {type(error).__name__}: {error}"


print("=" * 96)
print("  #26-healmap-lavaridge — which Poké Center is reachable from Route 112's lower section?")
print("=" * 96)

save = SAVES / ANCHOR
if not save.is_file():
    print(f"  ABORT (instrument, not a result) — no anchor save: {ANCHOR}")
    raise SystemExit(1)

context.emulator.load_save_state(save.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

try:
    avatar = get_player_avatar()
    here = tuple(avatar.map_group_and_number)
    here_tile = tuple(avatar.local_coordinates)
    state = get_game_state().name
    ctrl = player_avatar_is_controllable()
    here_name = getattr(get_map_data_for_current_position(), "map_name", "?")
    print(f"  anchor: {ANCHOR} -> {here_name} {here} {here_tile}  state={state} controllable={ctrl}")
except Exception as error:  # noqa: BLE001
    print(f"  ABORT (instrument, not a result) — could not read the anchor: {error!r}")
    raise SystemExit(1)

# --- THE CONTROL --------------------------------------------------------------------------------
print()
print("  CONTROL — re-run the 2026-07-26 reading already recorded in NO_RETURN_GROUNDS:")
kind, text = path_result((MapRSE.LAVARIDGE_TOWN, (9, 6)), FROM_TILE_2026_07_26)
print(f"    Lavaridge (9,6) -> ROUTE112 (11,36) : {text}")
print(f"    (recorded 2026-07-26 as: OK, 60 waypoints)")
if kind != "OK":
    print()
    print("  ⛔⛔ ABORT (instrument, not a result) — the CONTROL did not reproduce.")
    print("     Every candidate line below would be meaningless, so none is printed. Fix the probe.")
    raise SystemExit(1)
print("    ✅ control reproduces — the instrument works on this pair, so a FAIL below is about the MAP.")

# --- THE KNOWN-BAD REVERSE ----------------------------------------------------------------------
print()
print("  KNOWN-BAD REVERSE — the leg NO_RETURN_GROUNDS says fails:")
_, text = path_result(FROM_TILE_2026_07_26, (MapRSE.LAVARIDGE_TOWN, (9, 6)))
print(f"    ROUTE112 (11,36) -> Lavaridge (9,6) : {text}")

# --- THE QUESTION -------------------------------------------------------------------------------
print()
print("  THE QUESTION — from EVERY common post-exit tile (Route 112 is ledge-split):")
rows = []
for src in FROM_TILES:
    print(f"    from {src[0].name} {src[1]}:")
    for label, centre in CANDIDATES:
        dst = (centre.value[0], centre.value[1])
        kind, text = path_result(src, dst)
        rows.append((f"{src[1]} -> {label}", kind, text))
        print(f"       {label:<34} {text[:88]}")

print()
print("=" * 96)
ok = [r for r in rows if r[1] == "OK"]
if ok:
    print("  ✅ REACHABLE (trustworthy positives):")
    for label, _, text in ok:
        print(f"       {label}  —  {text}")
    print("  ⇒ a POSITIVE from calculate_path is strong evidence and is safe to act on.")
else:
    print("  ⚠ NO trustworthy positive from calculate_path.")
    print("    ⛔ That is NOT 'nothing is reachable'. Any WARP result is the wrong tool, and a FAIL")
    print("       on connected maps is still 'unproven' (KI-24). ⇒ escalate to the NAVIGATION")
    print("       instrument (`_navigate_riding_out`, which DOES cross warps) before editing a table.")
print("=" * 96)
