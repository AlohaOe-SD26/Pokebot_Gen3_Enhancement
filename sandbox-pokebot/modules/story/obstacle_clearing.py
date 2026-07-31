"""Field-move obstacles that SEAL a journey (`#24-smashroute`, KI-41).

WHY THIS EXISTS
---------------
A Rock Smash rock is not "difficult terrain" — it is a wall that one button press turns
into a corridor, and the pathfinder is right to call it impassable while it stands. The
consequence, measured 2026-07-31 from `rocksmash_taught.ss1` (Mauville 32,15):

  * ROUTE111 reachability has a hard floor at y~100-101 across columns 17-20 — the twin
    rocks at **(18,101)** and **(19,100)**.
  * ROUTE112 therefore scores **0 of 76** sampled tiles reachable from Mauville.
  * FIERY_PATH's only two doors are on ROUTE112 — so **Machop, the counter the
    `#24-counters` ladder names for Norman, is unreachable**, and the chain correctly
    diagnoses its answer and then ends the run.

`#24-journey` (warp planning at map granularity) did NOT fix this and was never going to:
after that fix a warp route to Fiery Path IS found — two candidates, both ROUTE112 doors —
and neither first leg is walkable. The rock is the blocker.

The story already smashes this exact rock, in two places, with the coordinate hard-coded
(`early_game.travel_to_fallarbor`, `travel_lavaridge_to_petalburg`). Nothing generic did.

WHY IT CAN BE GENERAL (probed, not assumed — `tools/story-dev/probe_smash_choke.py`)
------------------------------------------------------------------------------------
The obstacles are visible in game data, so this needs no hand-maintained table:

    ROUTE111 object events near the choke:
      (18,101)  script=EventScript_RockSmash
      (19,100)  script=EventScript_RockSmash
    ...and `map_path` tags exactly those two tiles, and no others in the band:
      (18,101) dyn_collision_flag=17 dyn_object_id=15
      (19,100) dyn_collision_flag=18 dyn_object_id=16

So: read the map's object events, keep the ones whose script is a known field-move
obstacle, and check whether the tile beside one is somewhere the bot can currently stand.
That is a fact about the ROM, refreshed per map, rather than a list that rots.

‼ TWO RULES THIS MODULE KEEPS
-----------------------------
1. **Never claim an obstacle is clearable without the capability.** A wrong YES sends the
   bot on a long walk to nowhere, which this project has paid for twice (KI-24b, and the
   refuted gateway waypoints). The move AND the badge are both checked, live.
2. **Judge by the world, never by the plan.** `early_game._smash_rock` already does this —
   it succeeds when the rock OBJECT is gone, not when a script ends — and it is idempotent,
   which matters because these rocks **RESPAWN on map reload**. This module adds the
   discovery; it does not re-implement the smashing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

_log = logging.getLogger("obstacle_clearing")

#: Object-event script symbol -> (field move needed, the badge that unlocks it outside
#: battle). ‼ ACTIONABLE ONLY. Every symbol below was counted off the ROM's own object
#: events, never recalled (`tools/story-dev/probe_smash_plan.py` scan, 2026-07-31):
#:      EventScript_StrengthBoulder  59 objects
#:      EventScript_RockSmash        44 objects
#:      EventScript_CutTree          33 objects
#: and the (18,101) Rock Smash rock was then confirmed end to end.
CLEARABLE_SCRIPTS: dict[str, tuple[str, str]] = {
    "EventScript_RockSmash": ("Rock Smash", "BADGE03_GET"),
}

#: Verified to EXIST, deliberately NOT actionable. Kept here so the next agent finds the
#: real symbol name and the real reason instead of re-deriving both — and so nobody adds
#: one to the table above without reading why it was left out.
#:
#: * `EventScript_CutTree` (Cut, BADGE01_GET) — the mechanism is identical (the object is
#:   REMOVED, which is what `clear_obstacle`'s success test watches for), but it has never
#:   been driven end to end here. Enabling it is a small change plus one live probe; it is
#:   left off because a wrong YES costs a long walk to nowhere, which this project has paid
#:   for twice (KI-24b, and the refuted gateway waypoints).
#: * `EventScript_StrengthBoulder` (Strength, BADGE04_GET) — ‼ NOT the same mechanism and
#:   must not be added without new clearing code. A boulder is PUSHED, not destroyed: the
#:   object still exists afterwards, one tile over. `clear_obstacle` succeeds when the
#:   object is GONE, so it would never see success, would burn its whole attempt budget,
#:   and would report a failure on a push that actually worked.
KNOWN_BUT_UNSUPPORTED: dict[str, str] = {
    "EventScript_CutTree": "mechanism matches, but never validated live — needs one probe",
    "EventScript_StrengthBoulder": "a boulder is PUSHED, not removed; the success test cannot see it",
}

#: face direction -> (dx, dy). Matches `early_game._smash_rock`'s own table.
_STEP = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}

#: ‼ RE-ENTRANCY GUARD — this is not defensive garnish, it closes a real infinite loop.
#: `clear_obstacle` -> `early_game._smash_rock` -> `_navigate_riding_out` (to walk to the
#: approach tile), and `_navigate_riding_out` is exactly where obstacle clearing is hooked.
#: So if that short walk fails for ANY reason — an NPC in the way, a scene, a bumped
#: trainer — the handler searches again, finds the SAME rock (its approach tile is still
#: reachable), and calls `clear_obstacle` again, one level deeper. The `cleared_obstacles`
#: set that bounds the outer loop is per-CALL, so each nested level starts with an empty
#: one and the recursion is unbounded.
#:
#: This is the project's oldest shape of bug: *a bounded loop re-entered by its dispatcher
#: is still infinite* (KI-34, 23.9M frames). Caught by `repro_smashrock_battle_wedge.py`
#: going from sub-90s to >500s the moment the hook landed — the sweep earned its keep.
_clearing_in_progress: bool = False


def is_clearing_in_progress() -> bool:
    """True while a clearance is running. Callers hooked into navigation must not start
    another one — see `_clearing_in_progress`."""
    return _clearing_in_progress


@dataclass(frozen=True)
class Obstacle:
    """A clearable obstacle and a proven way to act on it."""

    map: tuple[int, int]
    #: The tile the obstacle occupies (impassable until cleared).
    tile: tuple[int, int]
    #: A tile the bot can currently REACH, orthogonally adjacent to `tile`.
    stand_tile: tuple[int, int]
    #: The direction to face from `stand_tile` to look at `tile`.
    face: str
    move: str
    badge: str
    script: str

    def describe(self) -> str:
        return (f"{self.move} obstacle at {self.tile} — stand {self.stand_tile} facing "
                f"{self.face} ({self.script})")


def obstacles_on_map(map_group_and_number: tuple[int, int]) -> list[tuple[tuple[int, int], str]]:
    """Every clearable obstacle's (tile, script_symbol) on a map, from the ROM's own
    object events. Fail-safe: returns [] on any read error, never raises."""
    try:
        from modules.map import get_map_data

        map_data = get_map_data(tuple(map_group_and_number), (0, 0))
    except Exception as error:  # noqa: BLE001
        _log.debug("could not read map objects for %r: %s", map_group_and_number, error)
        return []

    out: list[tuple[tuple[int, int], str]] = []
    for obj in getattr(map_data, "objects", ()) or ():
        script = getattr(obj, "script_symbol", None)
        if script not in CLEARABLE_SCRIPTS:
            continue
        try:
            out.append((tuple(obj.local_coordinates), script))
        except Exception:  # noqa: BLE001
            continue
    return out


def _have_capability(move: str, badge: str) -> bool:
    """Does a party mon know `move` AND does the player hold the badge that enables it
    outside battle? Both, or the answer is no — this mirrors
    `story.region_reach._live_capability`, deliberately, so the two cannot disagree about
    what the bot can do."""
    try:
        from modules.memory import get_event_flag
        from modules.pokemon_party import get_party

        if not get_party().has_pokemon_with_move(move):
            return False
        return bool(get_event_flag(badge))
    except Exception as error:  # noqa: BLE001
        _log.debug("capability check failed for %s/%s: %s", move, badge, error)
        return False


def _reachable(map_group_and_number: tuple[int, int], tile: tuple[int, int]) -> bool:
    """Can the bot walk to this tile RIGHT NOW? Uses `calculate_path` from the live player
    location — deliberately the same oracle `navigate_to` consults, so this can never
    disagree with it about what is walkable."""
    try:
        from modules.map_path import calculate_path
        from modules.player import get_player_location

        calculate_path(get_player_location(), (tuple(map_group_and_number), tuple(tile)))
        return True
    except Exception:  # noqa: BLE001
        return False


def find_clearable_obstacle(
    map_group_and_number: tuple[int, int],
    *,
    prefer_toward: tuple[int, int] | None = None,
) -> Obstacle | None:
    """The best obstacle on this map that the bot can actually reach and actually clear.

    An obstacle qualifies only if ALL of these hold, each checked rather than assumed:
      * its script is a known field-move obstacle (from the ROM's object events);
      * the party knows the move AND the player has the badge;
      * at least one orthogonally adjacent tile is REACHABLE right now.

    `prefer_toward`, when given, breaks ties toward a goal tile — of two clearable rocks,
    open the one that leads where we are going.

    Returns None when nothing qualifies. ‼ None means "I found nothing I can act on", NOT
    "there is no obstacle": a rock the bot cannot reach or cannot smash is correctly not a
    plan. Never raises.
    """
    try:
        candidates: list[Obstacle] = []
        capability_cache: dict[str, bool] = {}

        for tile, script in obstacles_on_map(map_group_and_number):
            move, badge = CLEARABLE_SCRIPTS[script]
            if move not in capability_cache:
                capability_cache[move] = _have_capability(move, badge)
            if not capability_cache[move]:
                continue
            for face, (dx, dy) in _STEP.items():
                # To FACE `tile` from `stand`, `stand` must be on the opposite side.
                stand = (tile[0] - dx, tile[1] - dy)
                if stand[0] < 0 or stand[1] < 0:
                    continue
                if not _reachable(map_group_and_number, stand):
                    continue
                candidates.append(Obstacle(
                    map=tuple(map_group_and_number), tile=tile, stand_tile=stand,
                    face=face, move=move, badge=badge, script=script,
                ))
                break  # one usable approach per obstacle is enough

        if not candidates:
            return None
        if prefer_toward is None:
            return candidates[0]
        return min(
            candidates,
            key=lambda o: abs(o.tile[0] - prefer_toward[0]) + abs(o.tile[1] - prefer_toward[1]),
        )
    except Exception as error:  # noqa: BLE001
        # ‼ Fail LOUDLY rather than silently returning "nothing to do" — a guard that
        # returns the same value when it breaks as when it is healthy is invisible
        # (08-MISTAKES 2026-07-27).
        try:
            from modules.console import console

            console.print(f"[yellow]obstacle_clearing: search failed ({type(error).__name__}: "
                          f"{error}) — treating the route as blocked.[/]")
        except Exception:  # noqa: BLE001
            pass
        return None


#: How many maps of a route to search for an obstacle. The blocker is by construction near
#: the reachable frontier, so it is on one of the first maps; searching the whole route
#: would cost a `calculate_path` per adjacent tile per obstacle across all of Hoenn.
_ROUTE_SEARCH_DEPTH = 4


def find_obstacle_on_route(
    from_map: tuple[int, int],
    to_map: tuple[int, int],
    *,
    prefer_toward: tuple[int, int] | None = None,
) -> Obstacle | None:
    """The first clearable obstacle on the way from `from_map` to `to_map`.

    ‼ SEARCHING ONLY THE START AND DESTINATION MAPS WOULD NEVER FIND THE REAL ONE. The rock
    that seals Mauville -> Fiery Path is on **ROUTE111**, which is neither: the journey is
    MAUVILLE -> ROUTE111 -> ROUTE112 -> FIERY_PATH. So walk the map-graph route and search
    each map in order, nearest first.

    Only obstacles whose stand tile is reachable RIGHT NOW qualify (see
    `find_clearable_obstacle`), which is what keeps this from proposing a rock on the far
    side of a different wall. Never raises.
    """
    if _clearing_in_progress:
        # We are already inside a clearance; the navigation that asked is the short walk to
        # an approach tile. Answering would recurse (see `_clearing_in_progress`).
        return None
    try:
        from modules.warp_graph import get_warp_graph

        route = get_warp_graph().map_route(tuple(from_map), tuple(to_map))
        if route is None:
            route = []
        # The current map first — a blocker can be on the map we are standing on.
        for candidate_map in [tuple(from_map), *route][:_ROUTE_SEARCH_DEPTH + 1]:
            found = find_clearable_obstacle(candidate_map, prefer_toward=prefer_toward)
            if found is not None:
                return found
        return None
    except Exception as error:  # noqa: BLE001
        _log.debug("find_obstacle_on_route failed: %s", error)
        return None


def clear_obstacle(obstacle: Obstacle):
    """Walk to `obstacle.stand_tile`, face the obstacle, and use the field move.

    Delegates the actual clearing to `early_game._smash_rock`, which is already hardened
    the hard way: it judges success by the rock OBJECT being gone (not by a script ending —
    Rock Smash can roll a wild encounter, and a battle-interrupted field script can read
    active forever), it is idempotent so a recovery re-entry is a no-op, and it is bounded.

    ‼ Sets `_clearing_in_progress` for the duration, in a `try/finally` so an abort or a
    `BotModeError` cannot leave it stuck on (which would silently disable obstacle clearing
    for the rest of the run — a guard that fails ON is as bad as one that fails off).

    Imported locally: `early_game` is a very large module and importing it at module scope
    would create a cycle through the story package.
    """
    global _clearing_in_progress

    from modules.map_data import MapRSE
    from modules.story.early_game import _smash_rock

    _clearing_in_progress = True
    try:
        yield from _smash_rock(MapRSE(tuple(obstacle.map)), obstacle.stand_tile, obstacle.face)
    finally:
        _clearing_in_progress = False
