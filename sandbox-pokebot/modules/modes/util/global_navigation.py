"""
Global (warp-aware) navigation for bot modes (sandbox enhancement #8).

`navigate_to()` only reaches maps in the player's current connected region.
`navigate_to_anywhere()` goes further: it plans a route through warps
(doors, stairs, cave entrances) using modules/warp_graph.py, then executes
it leg by leg — each leg is a plain `navigate_to()` whose destination is
the warp tile, which upstream's own machinery follows through onto the
next map (see walking.py: warp final-waypoint handling + warp timeout).

Not handled (raises a friendly BotModeError instead of guessing): routes
that would require Dive, dynamic warps, surf transitions upstream cannot
plan, and warps that turn out to be locked/event-gated at runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator

from modules.context import context
from modules.map_data import MapFRLG, MapRSE
from modules.memory import GameState, get_game_state
from modules.modes._interface import BotModeError
from modules.player import get_player_avatar
from modules.warp_graph import get_warp_graph

if TYPE_CHECKING:
    pass

# A cross-region route should never need this many warps; the bound only
# guards against planner/runtime disagreement causing an endless loop.
_MAX_LEGS = 32

# How many DISTINCT first-warps to consider when the direct walk is impossible
# (#24-journey / KI-39). Each one costs a `calculate_path` to validate, so this is a
# planning budget, not a route-length bound.
_WARP_CANDIDATES = 6


def _walk_is_possible(
    map_group_and_number: tuple[int, int],
    coordinates: tuple[int, int],
    avoid_encounters: bool,
    avoid_scripted_events: bool,
) -> bool:
    """Can the player WALK to this tile right now, without any warp?

    Asks `calculate_path` — deliberately the exact call `navigate_to` makes one line
    later, with the same arguments, so this can never disagree with it about what is
    walkable. (Probing reachability with a differently-parameterised call is how this
    project nearly retired a working feature; 08-MISTAKES 2026-07-30.)

    ‼ ON AN UNEXPECTED ERROR THIS RETURNS **True**, and says so loudly. The pessimistic
    answer would be the dangerous one: it would quietly reroute every navigation in the
    game through the warp planner the moment something unrelated started throwing. True
    preserves exactly today's behaviour — `navigate_to` runs and reports the real problem.
    """
    from modules.items import get_item_bag, get_item_by_name
    from modules.map_path import PathFindingError, calculate_path
    from modules.player import get_player_location

    try:
        calculate_path(
            get_player_location(),
            (tuple(map_group_and_number), tuple(coordinates)),
            avoid_encounters=avoid_encounters,
            avoid_scripted_events=avoid_scripted_events,
            has_acro_bike=get_item_bag().quantity_of(get_item_by_name("Acro Bike")) > 0,
            has_mach_bike=get_item_bag().quantity_of(get_item_by_name("Mach Bike")) > 0,
        )
        return True
    except PathFindingError:
        return False
    except Exception as error:  # noqa: BLE001
        from modules.console import console

        console.print(
            f"[yellow]navigate_to_anywhere: the walkability check failed "
            f"({type(error).__name__}: {error}) — assuming WALKABLE so behaviour is "
            f"unchanged. This guard is not protecting anything right now.[/]"
        )
        return True

# Frame-waits while the game is not in the overworld (a warp-arrival cutscene,
# an evolution, etc.) must NOT count against the warp-leg budget above — a
# single scripted event is easily more than _MAX_LEGS frames long, and counting
# them there would abort a perfectly good route with a misleading "looping"
# error. This separate, generous cap only exists to break a genuine softlock
# (the game never returning to the overworld) rather than yield forever.
_MAX_NON_OVERWORLD_FRAMES = 60 * 60 * 5  # ~5 minutes at 60 fps


def _map_name(map_group_and_number: tuple[int, int]) -> str:
    enum = MapRSE if context.rom.is_rse else MapFRLG
    try:
        return enum(tuple(map_group_and_number)).name
    except ValueError:
        return str(tuple(map_group_and_number))


def _warp_fired(leg, arrived_map: tuple[int, int]) -> bool:
    """Did stepping on `leg.from_coords` actually take us somewhere?

    ‼ THIS USED TO COMPARE REGIONS, and that was only ever correct by accident. A region
    is the union-find collapse of map connections, so a warp BETWEEN TWO MAPS OF THE SAME
    REGION — which is exactly the class `#24-journey` makes plannable (Rusturf Tunnel,
    the Route 110 cycling-road gates) — leaves the region unchanged and would have been
    reported as "the warp did not trigger (locked or event-gated?)". A correct feature
    would have looked like a locked door.

    Compare MAPS instead. A warp whose two ends are on the same map (in-map stairs) can't
    use map identity, so fall back to "we are no longer standing on the warp tile".
    """
    arrived_map = tuple(arrived_map)
    if tuple(leg.to_map) == tuple(leg.from_map):
        try:
            return tuple(get_player_avatar().local_coordinates) != tuple(leg.from_coords)
        except Exception:  # noqa: BLE001
            return False
    return arrived_map != tuple(leg.from_map)


def navigate_to_anywhere(
    map: "tuple[int, int] | MapFRLG | MapRSE",
    coordinates: tuple[int, int],
    run: bool = True,
    avoid_encounters: bool = True,
    avoid_scripted_events: bool = True,
) -> Generator:
    """Walk the player to any known map/tile, using warps when needed.

    Drop-in superset of `navigate_to` for overworld targets: same-region
    targets take exactly the old path; cross-region targets are routed
    through the warp graph one leg at a time (re-planned from the actual
    player position after every warp, so surprises self-correct).
    """
    # Imported here (not module top) to avoid import cycles with the util package.
    from modules.modes.util.walking import navigate_to, wait_for_player_avatar_to_be_standing_still

    if not isinstance(map, tuple):
        map = map.value
    target_map = tuple(map)
    target_coords = tuple(coordinates)

    graph = get_warp_graph()
    if graph.region_of(target_map) is None:
        raise BotModeError(f"Unknown destination map {_map_name(target_map)} — cannot navigate there.")

    legs_taken = 0
    non_overworld_frames = 0
    #: Warps already taken on THIS journey. Without it a re-plan after arriving can pick
    #: the warp straight back where it came from and ping-pong until `_MAX_LEGS`.
    used_warps: set = set()
    while legs_taken < _MAX_LEGS:
        if get_game_state() is not GameState.OVERWORLD:
            # Let whatever is going on (battle/evolution handled by listeners)
            # settle before reading the avatar. These waits are counted against
            # a separate, generous cap — NOT the warp-leg budget — so a normal
            # arrival cutscene can never masquerade as a "looping route".
            non_overworld_frames += 1
            if non_overworld_frames > _MAX_NON_OVERWORLD_FRAMES:
                raise BotModeError(
                    f"Navigation to {_map_name(target_map)} stalled: the game stayed out of the "
                    "overworld for too long (possible softlock). Aborting."
                )
            yield
            continue
        non_overworld_frames = 0

        current_map = tuple(get_player_avatar().map_group_and_number)

        # --- 1. Can we simply WALK there? Unchanged fast path. -------------------
        # This is the branch every existing caller already takes for a same-region
        # target; asking `calculate_path` first only changes what happens when the
        # answer is NO (see 2). A YES behaves exactly as it did before.
        if _walk_is_possible(target_map, target_coords, avoid_encounters, avoid_scripted_events):
            yield from navigate_to(
                target_map,
                target_coords,
                run=run,
                avoid_encounters=avoid_encounters,
                avoid_scripted_events=avoid_scripted_events,
            )
            return

        # --- 2. Not walkable — find a warp to route through. ---------------------
        # ‼ #24-journey / KI-39. `plan()` answers at REGION granularity and returns []
        # whenever start and goal share a region — and the WHOLE Hoenn overworld is one
        # region, so every overworld->overworld trip used to fall out of the branch above
        # and die in `navigate_to`, no matter how obviously a warp route existed. Measured
        # 2026-07-31: Verdanturf declares a map CONNECTION to Route 116, so the two are one
        # region, yet 0 of 40 sampled Route 116 tiles are walkable from Verdanturf and the
        # only real link is the Rusturf Tunnel warp. `warp_candidates()` answers at MAP
        # granularity and can therefore return it.
        region_route = graph.plan(current_map, target_map)
        candidates: list = []
        if region_route:
            # Keep the region planner's own choice FIRST, so a cross-region route that
            # works today keeps taking exactly the leg it takes today.
            candidates.append(region_route[0])
        for candidate in graph.warp_candidates(current_map, target_map, limit=_WARP_CANDIDATES):
            if candidate not in candidates:
                candidates.append(candidate)

        # ‼ VALIDATE, don't trust. A planned warp is only useful if its tile is walkable
        # FROM HERE — KI-39's own FIERY_PATH example planned a perfectly good one-warp
        # route whose leg 1 was itself unreachable, and the run burned frames discovering
        # that by walking. Ask before committing.
        leg = None
        for candidate in candidates:
            if candidate in used_warps:
                # A deterministic picker re-picks a failed choice forever unless the
                # failure is REMEMBERED (08-MISTAKES: "recovery is just a countdown to
                # Manual if the same inputs produce the same choice").
                continue
            if _walk_is_possible(
                candidate.from_map, candidate.from_coords, avoid_encounters, avoid_scripted_events
            ):
                leg = candidate
                break

        if leg is None:
            if region_route:
                # Nothing validated, but a cross-region plan exists. Take it unvalidated —
                # this is precisely today's behaviour, so this change can never make a
                # cross-region journey that works now start failing.
                leg = region_route[0]
            elif candidates:
                raise BotModeError(
                    f"Cannot reach {_map_name(target_map)}: it is not walkable from "
                    f"{_map_name(current_map)}, and none of the {len(candidates)} candidate "
                    f"warp route(s) start at a tile that can be walked to from here "
                    f"(tried: {', '.join(_map_name(c.from_map) + str(c.from_coords) for c in candidates)})."
                )
            else:
                # No warp route is known at all. Let `navigate_to` raise, so the caller
                # gets the pathfinder's own authoritative reason rather than our guess.
                yield from navigate_to(
                    target_map,
                    target_coords,
                    run=run,
                    avoid_encounters=avoid_encounters,
                    avoid_scripted_events=avoid_scripted_events,
                )
                return

        used_warps.add(leg)
        # Walking onto the warp tile makes upstream's navigation follow the
        # warp through to the destination map (walking.py handles the map
        # transition and its longer timeout).
        yield from navigate_to(
            leg.from_map,
            leg.from_coords,
            run=run,
            avoid_encounters=avoid_encounters,
            avoid_scripted_events=avoid_scripted_events,
        )
        yield from wait_for_player_avatar_to_be_standing_still()

        arrived_map = tuple(get_player_avatar().map_group_and_number)
        if not _warp_fired(leg, arrived_map):
            # FORK (2026-07-24, ch12_run1): a warp fires on STEPPING onto its tile.
            # If we are ALREADY standing on it (a battle ended there, or a resume
            # loaded there), the navigate above was a zero-step no-op and the warp
            # stays dormant — that is not a locked door. Step OFF one tile, walk
            # back ON, and re-check before concluding anything.
            if tuple(get_player_avatar().local_coordinates) == tuple(leg.from_coords):
                for _dir in ("Down", "Up", "Left", "Right"):
                    for _ in range(20):
                        context.emulator.press_button(_dir)
                        yield
                    if tuple(get_player_avatar().local_coordinates) != tuple(leg.from_coords):
                        break
                context.emulator.reset_held_buttons()
                yield from navigate_to(
                    leg.from_map,
                    leg.from_coords,
                    run=run,
                    avoid_encounters=avoid_encounters,
                    avoid_scripted_events=avoid_scripted_events,
                )
                yield from wait_for_player_avatar_to_be_standing_still()
                arrived_map = tuple(get_player_avatar().map_group_and_number)
        if not _warp_fired(leg, arrived_map):
            # The warp did not fire (locked door / event-gated / graph wrong).
            raise BotModeError(
                f"Warp at {leg.from_coords} on {_map_name(leg.from_map)} did not trigger "
                f"(locked or event-gated?). Aborting navigation to {_map_name(target_map)}."
            )
        # Loop continues: re-plan from wherever we actually arrived.
        legs_taken += 1

    raise BotModeError(
        f"Gave up navigating to {_map_name(target_map)} after {_MAX_LEGS} warp legs — "
        "the route may be looping. Please report this."
    )
