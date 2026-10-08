"""TEST SIDE: WHERE THE GAME SAYS THE PLAYER STANDS, by its own BEHAVIOUR (AI-player step 3, the verifier's weak proof).

    py -3.12 ai_player/gates/game_answer.py STATE GROUP NUMBER X Y [--after-warp GROUP NUMBER X Y |
                                                                    --after-connection GROUP NUMBER X Y DIRECTION]
                                                                          prints one line: ANSWER {json}

WHY: the step-3 graders read the player's map and tile from save block 1 (`location`, `pos`) in a second emulator, and
the eyes read the same `pos` (and require the player object's tile to agree: `eyes/view.py` settled_position). The
step-3 verifier: "agreement between two memory reads, not a fully separate kind of evidence". This asks the GAME:

  1. PREDICT, from the ROM's STATIC map data at the CLAIMED map and tile (the framework's `MapLocation`: each tile's
     collision, behaviour and elevation, the map's warps, coord events and connections; never the live grid the eyes
     read, never the AI), what holding ONE direction will do: "walks K steps and stops" (the next tile is a wall), or
     "walks K steps and the map becomes M" (the edge, across the ROM's connection). A line is used only when it is
     CLEAN: every tile walked plain floor or tall grass (`PLAIN`: no warp, no coord event that would run now, no
     ledge, no one-way tile), the same elevation, and no person (live object, or its movement area) within a tile of it.
     A trial that meets a wild battle in the grass says nothing; the axis's other clean direction is tried.
  2. HOLD that direction in a throwaway emulator loaded from the saved state, and COUNT what the game does: its own
     step counter (`gameStats[GAME_STAT_STEPS]`, the counter the step-3 truth already reads) and the map it LOADED
     (`gMapHeader`: the header the game's loader copied from the ROM, compared byte for byte with the ROM's header).
  3. AGREE: every trial must match its prediction, and at least one must predict a STEP (`walking_agrees`: a "0 steps,
     then a wall" line also agrees with a player who cannot move at all: measured on STUCK's locked state). A claimed
     tile one off walks a different number of steps before the
     same wall or edge (or meets another); `ruled_out` counts the 8 neighbouring tiles whose own prediction differs
     for a trial direction (a neighbour that is itself a wall is impossible as a claim and counted apart).
  Also: the map the game has LOADED (`gMapHeader`) is the claimed map's ROM header (map identity by the loader's copy,
  not by save block 1's `location`).

WHAT IT IS NOT: it does not see the screen, and the step counter and `gMapHeader` are memory too; but they are the
GAME'S reactions to presses, predicted from the ROM layout at the claimed tile: a wrong claim gets a wrong prediction.
A tile with no clean line (deep in grass, beside people) gets `trials: []` and says so: `inconclusive`.
The probe holds buttons in its OWN throwaway emulator (test side); the AI's run and its state are not touched.

SINCE THE STEP-3 VERIFIER'S SECOND ROUND ("STUCK's game answer is INCONCLUSIVE ... the end tile [8,3] has no
behavioural confirmation"): measured 2026-10-08 on that state, no press can move the player there at all: Mom's
`LittlerootTown_BrendansHouse_1F_EventScript_GoUpstairsToSetClock` (`lockall`, a `msgbox` waiting) holds the controls,
so every direction held 600 frames moved nothing and counted no step. Two additions answer such a state:
  4. LOCKED (`locked`, only when no trial ran): each direction held `LOCK_HOLD` frames from the saved state; the game
     counts no step, the save block's tile and the loaded map do not change. That is the game's own answer that the
     player cannot have moved since the state was saved (a scene holds it), not merely "no clean line".
  5. THE ARRIVAL (`--after-warp GROUP NUMBER X Y`: the warp the player last used, by the AI's own account): the ROM's
     warp table says where that warp lands (`MapWarp`: the destination map and warp id, that warp's tile), and the
     decomp says what the game does next: arriving on a door or a non-animated door (stairs) the player faces SOUTH, a
     deep-south warp NORTH (`src/overworld.c` GetAdjustedInitialDirection), and the exit task walks ONE step that way
     for a door or a non-animated door (`src/field_screen_effect.c` SetUpWarpExitTask: Task_ExitDoor,
     Task_ExitNonAnimDoor; Task_ExitNonDoor takes no step; `src/metatile_behavior.c` MetatileBehavior_IsDoor: 0x69,
     0x8D; IsNonAnimDoor: 0x60, 0x6C, 0x6E). The predicted tile must be the claim; a claimed neighbour must not be
     (`ruled_out`). The grader also checks the AI pressed nothing after that arrival.

BUILD STEP 3.1 (the step-3 review's item 7: "grep the gates for any grade that compares a post-warp position to a raw
warp TARGET"): AUDITED 2026-10-08 over every file of `gates/`. The ROM's warp table is read in three places only: this
file (THE ARRIVAL above, which never grades against the raw landing tile: it applies the exit step the game takes for a
door-family landing, SetUpWarpExitTask, so a door's player rests ONE TILE SOUTH of it), `probe_eyes.py` (the tile truth
of `live_step1.py`, a tile's look against the table, no position) and `exit_looks.py` (coverage, no position). Every
other post-warp grade reads SAVE BLOCK 1's `pos` after the transition (`live_step1.py` WARP / WARPY: `save_xy` on the
first settled frame of the new map; `live_step3.py` TRUTH: `hands_harness.py truth`; `make_mart_fixture.py` place).
THE ARRIVAL itself is checked against save block 1's position after the transition, the claim (`agrees`), and now says
how far the raw landing is from it (`raw_landing_is_the_claim`): on STUCK's state the raw landing (8, 2) is NOT where the
player stands, (8, 3) is, so a grade on the raw target would fail there (`live_step3.py` grade_STUCK checks both).

THE STEP-3.1 VERIFIER'S SECOND ROUND ("what happens after the twin is not graded by the game's answer"): the arm SCENEX
now runs to the explorer's own end, which is Route 101 (after May, the twin lets the player pass), and the moment the
player arrives there at VAR_LITTLEROOT_TOWN_STATE 2, Birch's rescue scene holds the controls: a clean line predicted
"Down: 1 step, then the map becomes Littleroot" and the game counted 0 (measured 2026-10-08). Two additions:
  6. LOCKED is now also asked when a trial predicted a STEP and the game took none, loading no map (`stopped_trials`):
     either the claim is wrong or nothing can move the player; LOCKED tells which.
  7. THE ARRIVAL ACROSS A CONNECTION (`--after-connection GROUP NUMBER X Y DIRECTION`: the edge the player last walked
     off, by the AI's own memory): the ROM's connection on that side (its neighbour and offset, the arithmetic `plan`
     uses at an edge) says where the player lands; a connection is walked across, so there is no exit step. A locked
     player whose ROM arrival is the claim agrees (`agree_by_arrival`), as with a warp.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import GAME_STATS, SB1_GAME_STATS, SB1_VARS, SB2_ENCRYPTION_KEY, VARS_START  # noqa: E402
from ai_player.gates.probe_eyes import _u32, boot  # noqa: E402

PROFILE = "ai-step0-fixture"
DIRECTIONS = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
#: The ROM's connection direction names (`modules/map.py` MapConnection.direction) by D-pad direction.
SIDES = {"Up": "North", "Down": "South", "Left": "West", "Right": "East"}
#: The longest line predicted (a wall or an edge must come within this many tiles).
LINE_MAX = 12
#: Behaviours a clean line may walk on: plain floor, and tall grass (a person walks through it; a wild battle met on
#: the way makes THAT trial inconclusive, and the next clean direction is tried: measured 2026-10-08, the ROAM arm ends
#: deep in Route 101's grass, where a floor-only rule left no line at all).
PLAIN = ("Normal", "Tall Grass")
#: Frames: settle after loading, with no input, so that a step in flight when the state was saved ends before the
#: count begins (measured 2026-10-08: arm BUMP's state is saved 8 frames into its last step, whose end the game's
#: counter then added to the first trial: "Left: 0 predicted, 1 counted"); a turn and the walk's start; per step;
#: after releasing (the last step ends, a connection's new map settles).
SETTLE, TURN, PER_STEP, AFTER = 40, 24, 16, 120
#: `include/constants/event_objects.h` OBJ_EVENT_ID_PLAYER: the player's own object event.
PLAYER_LOCAL_ID = 0xFF
#: Frames each direction is held to ask whether the player can move at all (module docstring, 4).
LOCK_HOLD = 120
#: (module docstring, 5) The behaviours (the framework's names, `modules/map.py`) after which the exit task walks one
#: step, and its direction: MB_NON_ANIMATED_DOOR 0x60, MB_WATER_DOOR 0x6C, MB_ANIMATED_DOOR 0x69 ("Door Warp"),
#: MB_PETALBURG_GYM_DOOR 0x8D face SOUTH; MB_DEEP_SOUTH_WARP 0x6E faces NORTH (checked first by the game).
EXIT_STEP = {"Non-Animated Door": (0, 1), "Water Door": (0, 1), "Door Warp": (0, 1), "Petalburg Gym Door": (0, 1),
             "Deep South Warp": (0, -1)}


def _steps(context) -> int:
    from modules.memory import read_symbol

    emulator = context.emulator
    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    key = int.from_bytes(bytes(emulator.read_bytes(sb2 + SB2_ENCRYPTION_KEY, 4)), "little")
    raw = bytes(emulator.read_bytes(sb1 + SB1_GAME_STATS + 4 * GAME_STATS["steps"], 4))
    return int.from_bytes(raw, "little") ^ key


def _loaded_header() -> bytes:
    from modules.memory import read_symbol

    return bytes(read_symbol("gMapHeader", size=0x1C))


def _pos(context) -> tuple[int, int]:
    """Save block 1's `pos` (s16 x, y @0)."""
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    raw = bytes(context.emulator.read_bytes(sb1, 4))
    return int.from_bytes(raw[0:2], "little", signed=True), int.from_bytes(raw[2:4], "little", signed=True)


def walking_agrees(trials: list[dict], loaded_ok: bool) -> bool:
    """The walking answer (module docstring, 3): every trial matched its prediction, the loaded map is the claimed one,
    AND at least one trial predicted a STEP. Pure. WHY the last (measured 2026-10-08, the graded run of the step-3
    verifier's second round): on STUCK's state, where a scene holds the controls, the fault claim (7, 3) had one clean
    line, "Up: 0 steps, then a wall", and the game counted 0 steps: it AGREED. A prediction of no step cannot tell a
    player standing before a wall from a player who cannot move at all."""
    return bool(trials) and all(t["agree"] for t in trials) and loaded_ok and any(t["predicted"]["steps"] > 0 for t in trials)


def exit_tile(landing: tuple[int, int], behaviour: str) -> tuple[int, int]:
    """Where the player stands once a warp's exit task is over (module docstring, 5): one step from the landing tile
    for a door or a non-animated door (south; north for a deep-south warp), none otherwise. Pure."""
    dx, dy = EXIT_STEP.get(behaviour, (0, 0))
    return landing[0] + dx, landing[1] + dy


def arrival_after_warp(source_map: tuple[int, int], source_tile: tuple[int, int]) -> dict:
    """The ROM's answer to where the warp at `source_tile` of `source_map` leaves the player (module docstring, 5)."""
    from modules.map import get_map_data

    warp = next((w for w in get_map_data(source_map, source_tile).warps if tuple(w.local_coordinates) == tuple(source_tile)), None)
    if warp is None:
        return {"error": f"no warp at {list(source_tile)} of {list(source_map)} in the ROM's warp table"}
    dest, warp_id = (warp.destination_map_group, warp.destination_map_number), warp.destination_warp_id
    if dest == (127, 127) or warp_id == 0xFF:
        return {"error": f"a dynamic warp or one with no destination warp ({list(dest)}, id {warp_id}): not modelled"}
    landing = tuple(get_map_data(dest, (0, 0)).warps[warp_id].local_coordinates)
    behaviour = get_map_data(dest, landing).tile_type
    tile = exit_tile(landing, behaviour)
    return {"warp": {"map": list(source_map), "tile": list(source_tile)}, "map": list(dest), "destination_warp_id": warp_id,
            "landing": list(landing), "landing_behaviour": behaviour, "exit_step": list(EXIT_STEP.get(behaviour, (0, 0))),
            "tile": list(tile)}


def arrival_after_connection(source_map: tuple[int, int], source_tile: tuple[int, int], direction: str) -> dict:
    """(the step-3.1 verifier's second round) The ROM's answer to where walking `direction` off `source_tile` of
    `source_map` across the map's edge leaves the player: the map's connection on that side (`MapConnection`: the
    neighbour and its offset), the same arithmetic as `plan`'s edge (no exit step: a connection is walked across)."""
    from modules.map import get_map_data

    direction = direction.capitalize()
    here = get_map_data(source_map, source_tile)
    width, height = here.map_size
    dx, dy = DIRECTIONS[direction]
    x, y = source_tile[0] + dx, source_tile[1] + dy
    if 0 <= x < width and 0 <= y < height:
        return {"error": f"{list(source_tile)} going {direction} does not leave {list(source_map)}"}
    link = next((c for c in here.connections if c.direction == SIDES[direction]), None)
    if link is None:
        return {"error": f"{list(source_map)} has no {SIDES[direction]} connection"}
    dest = (link.destination_map_group, link.destination_map_number)
    dest_w, dest_h = get_map_data(dest, (0, 0)).map_size
    tile = {"Up": (x - link.offset, dest_h + y), "Down": (x - link.offset, y - height),
            "Left": (dest_w + x, y - link.offset), "Right": (x - width, y - link.offset)}[direction]
    return {"connection": {"map": list(source_map), "tile": list(source_tile), "direction": direction, "offset": link.offset},
            "map": list(dest), "landing": list(tile), "landing_behaviour": get_map_data(dest, tile).tile_type,
            "exit_step": [0, 0], "tile": list(tile)}


def locked(context, state: bytes) -> dict:
    """Can the player move at all from the saved state? Each direction held `LOCK_HOLD` frames (module docstring, 4)."""
    emulator = context.emulator
    held = {}
    for direction in DIRECTIONS:
        emulator.load_save_state(state)
        for _ in range(SETTLE):
            emulator.run_single_frame()
        steps0, header0, pos0 = _steps(context), _loaded_header(), _pos(context)
        emulator.hold_button(direction)
        try:
            for _ in range(LOCK_HOLD):
                emulator.run_single_frame()
        finally:
            emulator.release_button(direction)
        held[direction] = {"game_steps": _steps(context) - steps0, "moved": _pos(context) != pos0,
                           "map_changed": _loaded_header() != header0}
    return {"locked": all(not h["game_steps"] and not h["moved"] and not h["map_changed"] for h in held.values()),
            "held_frames": LOCK_HOLD, "held": held}


def _rom_header(map_key: tuple[int, int]) -> bytes:
    from modules.map import get_map_data

    return bytes(get_map_data(map_key, (0, 0))._map_header)  # noqa: SLF001 - test side: the ROM's header bytes


def _which_map(header: bytes, candidates: list[tuple[int, int]]) -> list[int] | None:
    found = [list(key) for key in candidates if _rom_header(key) == header]
    return found[0] if found else None


def _people(context) -> set[tuple[int, int]]:
    """Every tile a person (a live object other than the player) stands on, may walk to (its movement area), or is
    next to: a line through any of them is not clean."""
    from modules.map import get_map_objects

    near: set[tuple[int, int]] = set()
    for obj in get_map_objects():
        if obj.local_id == PLAYER_LOCAL_ID:
            continue
        spots = {obj.current_coords, obj.initial_coords}
        ix, iy = obj.initial_coords
        for x in range(ix - obj.range_x, ix + obj.range_x + 1):
            for y in range(iy - obj.range_y, iy + obj.range_y + 1):
                spots.add((x, y))
        for x, y in spots:
            near |= {(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    return near


def live_coord_events(context, map_key: tuple[int, int]) -> set[tuple[int, int]]:
    """The tiles of the map's coord events that WOULD run a script now (`src/event_data.c`
    GetCoordEventScriptAtPosition: no script = weather only; no trigger variable = always; otherwise only while
    `VarGet(trigger) == index`), the variable read from save block 1 (`vars[]` @0x139C); a special variable (0x8000+)
    is taken as live (unknown: conservative)."""
    from modules.map import get_map_data
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    live = set()
    for event in get_map_data(map_key, (0, 0)).coord_events:
        if event.script_pointer == 0:
            continue
        var = event.trigger_var_number
        if var == 0 or var >= 0x8000:
            live.add(tuple(event.local_coordinates))
            continue
        value = int.from_bytes(bytes(context.emulator.read_bytes(sb1 + SB1_VARS + 2 * (var - VARS_START), 2)), "little")
        if value == event.trigger_value:
            live.add(tuple(event.local_coordinates))
    return live


def mismatch(z: int, tile_z: int) -> bool:
    """`src/event_object_movement.c` IsElevationMismatchAt: an object at elevation `z` may not step onto a tile of
    elevation `tile_z` when both are set (0 and 15 are not) and they differ."""
    return z != 0 and tile_z not in (0, 15) and tile_z != z


def plan(map_key: tuple[int, int], start: tuple[int, int], direction: str, people: set, coords: set, z: int) -> dict:
    """The ROM's prediction for holding `direction` from `start` on `map_key` (module docstring, step 1). `coords`:
    the tiles of the coord events that would run now (`live_coord_events`); `z`: the player's elevation at the start
    (it follows every tile stepped on whose elevation is not 15: `ObjectEventUpdateElevation`)."""
    from modules.map import get_map_data

    here = get_map_data(map_key, start)
    width, height = here.map_size
    warps = {tuple(w.local_coordinates) for w in here.warps}
    dx, dy = DIRECTIONS[direction]
    for k in range(1, LINE_MAX + 1):
        x, y = start[0] + dx * k, start[1] + dy * k
        if not (0 <= x < width and 0 <= y < height):
            side = SIDES[direction]
            link = next((c for c in here.connections if c.direction == side), None)
            if link is None:
                return {"clean": True, "steps": k - 1, "ends": "blocked", "at": [x, y], "why": "the map's edge, no connection"}
            dest = (link.destination_map_group, link.destination_map_number)
            dest_w, dest_h = get_map_data(dest, (0, 0)).map_size
            arrival = {"Up": (x - link.offset, dest_h + y), "Down": (x - link.offset, y - height),
                       "Left": (dest_w + x, y - link.offset), "Right": (x - width, y - link.offset)}[direction]
            if not (0 <= arrival[0] < dest_w and 0 <= arrival[1] < dest_h):
                return {"clean": False, "why": f"the edge at {[x, y]} has no tile of {dest} beyond it"}
            tile = get_map_data(dest, arrival)
            if tile.collision != 0 or tile.tile_type not in PLAIN or mismatch(z, tile.elevation):
                return {"clean": False, "why": f"the arrival {list(arrival)} on {list(dest)} is {tile.tile_type}, collision "
                                               f"{tile.collision}, elevation {tile.elevation} (the player's {z})"}
            return {"clean": True, "steps": k, "ends": "map", "map": list(dest), "arrival": list(arrival),
                    "why": f"the {side} connection at offset {link.offset}"}
        tile = get_map_data(map_key, (x, y))
        if tile.collision != 0:
            return {"clean": True, "steps": k - 1, "ends": "blocked", "at": [x, y],
                    "why": f"{tile.tile_type}, collision {tile.collision}"}
        if mismatch(z, tile.elevation):
            return {"clean": True, "steps": k - 1, "ends": "blocked", "at": [x, y],
                    "why": f"an elevation step: the tile's {tile.elevation}, the player's {z}"}
        if tile.tile_type not in PLAIN or (x, y) in warps or (x, y) in coords or (x, y) in people:
            return {"clean": False, "why": f"({x}, {y}): {tile.tile_type}, elevation {tile.elevation}"
                                           f"{', a warp' if (x, y) in warps else ''}{', a coord event' if (x, y) in coords else ''}"
                                           f"{', a person near' if (x, y) in people else ''}"}
        if tile.elevation != 15:
            z = tile.elevation
    return {"clean": False, "why": f"no wall or edge within {LINE_MAX} tiles"}


def trial(context, state: bytes, direction: str, predicted: dict, claimed: tuple[int, int]) -> dict:
    """Hold `direction` from the saved state and count what the game does (module docstring, step 2)."""
    from modules.memory import get_game_state

    emulator = context.emulator
    emulator.load_save_state(state)
    for _ in range(SETTLE):
        emulator.run_single_frame()
    steps0, header0 = _steps(context), _loaded_header()
    limit = TURN + PER_STEP * (predicted["steps"] + 2)
    emulator.hold_button(direction)
    held, changed_at, state_seen = 0, None, set()
    try:
        while held < limit:
            emulator.run_single_frame()
            held += 1
            state_seen.add(get_game_state().name)
            if _loaded_header() != header0:
                changed_at = held
                break
    finally:
        emulator.release_button(direction)
    for _ in range(AFTER):
        emulator.run_single_frame()
        state_seen.add(get_game_state().name)
    steps = _steps(context) - steps0
    header = _loaded_header()
    loaded = _which_map(header, [claimed] + ([tuple(predicted["map"])] if predicted.get("map") else []))
    battle = any("BATTLE" in name for name in state_seen)
    if battle:
        agree = None  # a wild battle met on the way (tall grass): this trial says nothing; the next direction is tried
    elif predicted["ends"] == "map":
        agree = steps == predicted["steps"] and loaded == predicted["map"]
    else:
        agree = steps == predicted["steps"] and header == header0
    return {"direction": direction, "predicted": predicted, "game_steps": steps, "map_changed": header != header0,
            "loaded_map": loaded, "changed_after_frames": changed_at, "held_frames": held,
            "game_states": sorted(state_seen), "battle": battle, "agree": agree}


def stopped_trials(trials: list[dict]) -> bool:
    """(the step-3.1 verifier's second round) A trial that predicted a STEP and in which the game counted none and loaded
    no map: either the claim is wrong, or nothing can move the player (a scene holds the controls: Birch's rescue on
    Route 101 starts the moment the player arrives at VAR_LITTLEROOT_TOWN_STATE 2). Then LOCKED is asked too. Pure."""
    return any(t["predicted"]["steps"] > 0 and t["game_steps"] == 0 and not t["map_changed"] and not t["battle"] for t in trials)


def answer(state_path: Path, claimed_map: tuple[int, int], claimed_pos: tuple[int, int],
           after_warp: tuple[tuple[int, int], tuple[int, int]] | None = None,
           after_connection: tuple[tuple[int, int], tuple[int, int], str] | None = None) -> dict:
    context = boot(PROFILE)  # puts the framework on sys.path
    from modules.map import get_map_data, get_player_map_object

    state = state_path.read_bytes()
    context.emulator.load_save_state(state)
    saved_steps = _steps(context)
    for _ in range(SETTLE):
        context.emulator.run_single_frame()
    # a step in flight when the state was saved ends now, and the game counts a step at its END
    in_flight = _steps(context) - saved_steps
    player = get_player_map_object()
    loaded_ok = _loaded_header() == _rom_header(claimed_map)
    people = _people(context)
    coords = live_coord_events(context, claimed_map)
    z = player.current_elevation if player is not None else get_map_data(claimed_map, claimed_pos).elevation
    plans = {d: plan(claimed_map, claimed_pos, d, people, coords, z) for d in DIRECTIONS}
    # the trials: one per axis when it can, preferring a line that ends in a map change, then the longest; a trial that
    # met a wild battle says nothing and the axis's other clean direction is tried
    trials, battles = [], []
    for axis in (("Up", "Down"), ("Left", "Right")):
        clean = [d for d in axis if plans[d]["clean"]]
        clean.sort(key=lambda d: (plans[d]["ends"] != "map", -plans[d]["steps"]))
        for d in clean:
            result = trial(context, state, d, plans[d], claimed_map)
            if result["battle"]:
                battles.append(result)
                continue
            trials.append(result)
            break
    # what the trials rule out: the neighbouring tiles whose own prediction differs for a trial direction
    ruled, walls = [], []
    width, height = get_map_data(claimed_map, (0, 0)).map_size
    for nx in (-1, 0, 1):
        for ny in (-1, 0, 1):
            if (nx, ny) == (0, 0):
                continue
            other = (claimed_pos[0] + nx, claimed_pos[1] + ny)
            if not (0 <= other[0] < width and 0 <= other[1] < height) or get_map_data(claimed_map, other).collision != 0:
                walls.append(list(other))
                continue
            # a person standing there would have that tile's elevation (unless it is 15: then as the claim's)
            other_z = get_map_data(claimed_map, other).elevation
            other_z = z if other_z == 15 else other_z
            for t in trials:
                theirs = plan(claimed_map, other, t["direction"], people, coords, other_z)
                mine = t["predicted"]
                key = lambda p: (p.get("clean"), p.get("steps"), p.get("ends"), p.get("map"))  # noqa: E731
                if theirs["clean"] and key(theirs) != key(mine):
                    ruled.append(list(other))
                    break
    # (module docstring, 4 and 5) no trial, or (the step-3.1 verifier's second round) a trial the game did not step at
    # all: can the player move at all, and where did the last warp (or connection) leave it?
    lock = locked(context, state) if (not trials or stopped_trials(trials)) else None
    arrival = None
    if after_warp is not None or after_connection is not None:
        arrival = arrival_after_warp(*after_warp) if after_warp is not None else arrival_after_connection(*after_connection)
        if "error" not in arrival:
            arrival["agrees"] = arrival["map"] == list(claimed_map) and arrival["tile"] == list(claimed_pos)
            arrival["raw_landing_is_the_claim"] = arrival["map"] == list(claimed_map) and arrival["landing"] == list(claimed_pos)
            if not trials or (lock and lock["locked"]):  # every tile beside the claim a person could stand on gets another prediction
                ruled = [[claimed_pos[0] + nx, claimed_pos[1] + ny] for nx in (-1, 0, 1) for ny in (-1, 0, 1)
                         if (nx, ny) != (0, 0) and [claimed_pos[0] + nx, claimed_pos[1] + ny] not in walls]
    return {
        "state": str(state_path), "claimed_map": list(claimed_map), "claimed_pos": list(claimed_pos),
        "player_object": None if player is None else {"local_id": player.local_id, "tile": list(player.current_coords)},
        "steps_in_flight": in_flight, "settled_tile": None if player is None else list(player.current_coords),
        "loaded_header_is_claimed_map": loaded_ok, "live_coord_events": sorted(list(xy) for xy in coords),
        "plans": plans, "trials": trials, "trials_that_met_a_battle": battles,
        "agree": walking_agrees(trials, loaded_ok),
        "inconclusive": not trials,
        "locked": lock, "arrival": arrival,
        "agree_by_arrival": bool(lock and lock["locked"] and arrival and arrival.get("agrees") and loaded_ok),
        "ruled_out": ruled, "neighbours_that_are_walls": walls,
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    state, group, number, x, y = sys.argv[1], *map(int, sys.argv[2:6])
    after_warp = after_connection = None
    if len(sys.argv) == 11 and sys.argv[6] == "--after-warp":
        g, n, wx, wy = map(int, sys.argv[7:11])
        after_warp = ((g, n), (wx, wy))
    elif len(sys.argv) == 12 and sys.argv[6] == "--after-connection":
        g, n, wx, wy = map(int, sys.argv[7:11])
        after_connection = ((g, n), (wx, wy), sys.argv[11])
    elif len(sys.argv) != 6:
        print(f"usage: {__doc__.splitlines()[2].strip()} [--after-warp GROUP NUMBER X Y | --after-connection GROUP NUMBER X Y "
              f"DIRECTION]", file=sys.stderr)
        return 2
    print("ANSWER " + json.dumps(answer(Path(state), (group, number), (x, y), after_warp, after_connection),
                                 ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
