"""Is each #24-counters phase-2 hunting ground ACTUALLY reachable from where the counter
ladder fires? Answers the one thing `repro_counter_hunt.py` deliberately does not.

The executor is built and every failure path is proven to stop honestly — but a rung whose
destination cannot be walked to is INERT: it costs one wasted walk and then falls through to
the same stop the bot already did. This probe says which of the three rungs are live BEFORE
a batch's logs have to be read to find out.

THE THREE CASES (destination = `counter_plan.best_huntable`'s real answer, per
`repro_counter_huntable.py`):
  Norman  -> Fighting -> Machop    @ FIERY_PATH (18,19)   -- anchor: a PRE-NORMAN save
  Wattson -> Ground   -> Sandshrew @ ROUTE111  (25,55)    -- anchor: a PRE/POST-WATTSON save
  Winona  -> Elec/Rock/Ice -> Electrike @ ROUTE118 (29,15) -- anchor: a WINONA-ERA save

‼ HOW TO READ THE RESULT — the two answers are NOT symmetric.
  * `calculate_path` OK   => genuinely reachable. Strong, trustworthy evidence.
  * `calculate_path` FAIL => **NOT proof of unreachable.** This is KI-24: the tile-level
    planner reads the Route 118/119/120 dual-elevation bridges as WALLS, and it once
    reported Route 118 — the real Winona answer — as unreachable when it plainly is not.
    A FAIL here means "unproven", and `region_reach`'s hop count is the second opinion.
  * `region_reach` answers at MAP scale from the ROM's own connections + warps. It fails
    OPEN by design, so its YES is weaker than `calculate_path`'s YES but its NO is strong.
Taken together: OK/OK = live. FAIL/reachable = probably live, one wasted walk if not
(bounded by `UnreachableDestinationError`). FAIL/unreachable = the rung is INERT.

‼ Anchors are verified on load, never trusted by name — several saves in this directory have
proven misnamed, and `prenorman_fodder_grind.ss1` loads INSIDE A WILD BATTLE (documented in
probe_counter_tiles.py), which makes every navigation leg fail identically for one harness
reason rather than three map reasons. Its state is reported so that is visible, not silent.

Run: py -3.12 tools/story-dev/probe_counter_reachability.py
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

from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import GameState, get_game_state
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.story import region_reach

SAVES = REPO / "tools" / "story-dev" / "saves"

#: Frames to allow one navigation attempt before calling it inconclusive. Generous: the
#: Lavaridge->Fiery Path leg measured ~60 waypoints when story_harness walked it.
NAV_FRAME_CAP = 120_000

CASES = [
    ("NORMAN  (needs Fighting)", "prenorman_fodder_grind.ss1", MapRSE.FIERY_PATH, (18, 19)),
    ("NORMAN  (alt anchor)", "flannery_done.ss1", MapRSE.FIERY_PATH, (18, 19)),
    ("WATTSON (needs Ground)", "rocksmash_taught.ss1", MapRSE.ROUTE111, (25, 55)),
    ("WATTSON (alt anchor)", "wattson_done.ss1", MapRSE.ROUTE111, (25, 55)),
    ("WINONA  (needs Rock/Elec/Ice)", "devon_scope_got.ss1", MapRSE.ROUTE118, (29, 15)),
]

results = []
for label, save_name, dest_map, dest_tile in CASES:
    print("=" * 78)
    print(f"{label}  —  {save_name}  ->  {dest_map.name} {dest_tile}")
    print("=" * 78)
    save = SAVES / save_name
    if not save.is_file():
        print(f"  SKIP — no such save: {save_name}")
        results.append((label, save_name, "NO SAVE", "", "", "skipped"))
        continue

    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    # --- verify the anchor; never trust the filename ---
    try:
        avatar = get_player_avatar()
        here_map = tuple(avatar.map_group_and_number)
        here_tile = tuple(avatar.local_coordinates)
        state = get_game_state().name
        controllable = player_avatar_is_controllable()
        here_name = getattr(get_map_data_for_current_position(), "map_name", "?")
    except Exception as error:
        print(f"  SKIP — could not read the anchor: {error!r}")
        results.append((label, save_name, "UNREADABLE ANCHOR", "", ""))
        continue

    print(f"  anchor: map={here_map} {here_name} tile={here_tile} "
          f"state={state} controllable={controllable}")
    if state != "OVERWORLD" or not controllable:
        print("  ‼ NOT a clean overworld — a nav FAIL here is a HARNESS artefact, not a map fact.")

    # --- region scale (fails OPEN; a NO is the meaningful answer) ---
    try:
        hops = region_reach.hops_to(dest_map, here_map)
        why = "" if hops is not None else region_reach.why_unreachable(dest_map, here_map)
        region = f"reachable, {hops} hops" if hops is not None else f"UNREACHABLE — {why}"
    except Exception as error:
        region = f"CHECK FAILED — {error!r}"
    print(f"  region_reach : {region}")

    # --- tile scale ---
    # ‼ `calculate_path` IS THE WRONG INSTRUMENT ON ITS OWN, and this probe said so the
    # hard way on its first run: three of five cases came back "…are not on connected maps
    # (note that warps don't count)". That is not a map fact — `calculate_path` plans only
    # across DIRECTLY CONNECTED maps, and FIERY_PATH is entered through a cave-door WARP,
    # so it can never answer this question. It is kept because it CAN still catch the other
    # class (connected maps with genuinely no walkable route, e.g. Route 111's desert
    # split), but the two outcomes must never be reported as the same thing.
    try:
        path = calculate_path(
            (here_map, here_tile), (dest_map, dest_tile),
            avoid_encounters=False, avoid_scripted_events=False,
        )
        tile_result = f"OK, {len(path)} waypoints"
    except PathFindingError as error:
        text = str(error)
        if "not on connected maps" in text:
            tile_result = "N/A — needs a WARP; calculate_path cannot cross warps (wrong tool)"
        else:
            tile_result = f"FAIL on connected maps (real, though see KI-24) — {text}"
    except Exception as error:
        tile_result = f"ERROR — {error!r}"
    print(f"  calculate_path: {tile_result}")

    # --- the REAL answer: drive the navigation the executor actually uses ---
    # `counter_hunt.hunt` calls `_navigate_riding_out`, which goes through
    # `navigate_to_anywhere` and DOES cross warps, riding out any scene that aborts a leg.
    # This is the only test that answers "can the bot get there", so it is the verdict.
    nav_result = "not attempted"
    if state == "OVERWORLD" and controllable:
        import modules.story.early_game as eg

        frames = 0
        try:
            generator = eg._navigate_riding_out(dest_map, dest_tile, avoid_encounters=True)
            while frames < NAV_FRAME_CAP:
                next(generator)
                context.emulator.run_single_frame()
                frames += 1
            nav_result = f"CAP HIT after {frames} frames (inconclusive)"
        except StopIteration:
            try:
                now = get_player_avatar()
                arrived = tuple(now.map_group_and_number) == tuple(dest_map.value)
            except Exception:
                arrived = False
            nav_result = (
                f"ARRIVED in {frames} frames" if arrived
                else f"returned in {frames} frames but NOT on {dest_map.name}"
            )
        except Exception as error:
            nav_result = f"FAILED after {frames} frames — {type(error).__name__}: {error}"
    else:
        nav_result = "skipped — anchor is not a clean, controllable overworld"
    print(f"  ‼ navigate   : {nav_result}")
    print()
    results.append((label, save_name, region, tile_result, f"{here_name} {here_tile}", nav_result))

print("=" * 78)
print("VERDICT — which #24-counters rungs are LIVE")
print("=" * 78)
for label, save_name, region, tile_result, anchor, nav_result in results:
    # The DRIVEN navigation is the verdict — it is the code path the executor uses.
    if nav_result.startswith("ARRIVED"):
        verdict = "LIVE — the bot walked there"
    elif nav_result.startswith("FAILED"):
        verdict = "INERT from this anchor (real navigation failed)"
    elif nav_result.startswith("CAP HIT"):
        verdict = "INCONCLUSIVE (hit the frame cap)"
    elif tile_result.startswith("OK"):
        verdict = "LIVE (tile path proven, nav not driven)"
    else:
        verdict = "NOT TESTED — " + nav_result
    print(f"  {label:<32} {verdict}")
    print(f"      from {anchor or save_name}")
    print(f"      region={region}")
    print(f"      tile={tile_result}")
    print(f"      nav={nav_result}")
print()
print("Reminder: a FAIL from calculate_path is NOT proof of unreachable (KI-24 — it reads")
print("dual-elevation bridges as walls). An UNPROVEN rung costs one wasted walk, bounded by")
print("UnreachableDestinationError, and then falls through to the same honest stop.")
