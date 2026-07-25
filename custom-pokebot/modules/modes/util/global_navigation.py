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
        if graph.region_of(current_map) == graph.region_of(target_map):
            yield from navigate_to(
                target_map,
                target_coords,
                run=run,
                avoid_encounters=avoid_encounters,
                avoid_scripted_events=avoid_scripted_events,
            )
            return

        route = graph.plan(current_map, target_map)
        if route is None:
            raise BotModeError(
                f"No known warp route from {_map_name(current_map)} to {_map_name(target_map)}.\n"
                "(Routes through Dive or dynamic warps are not supported.)"
            )

        leg = route[0]
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
        if graph.region_of(arrived_map) == graph.region_of(leg.from_map):
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
        if graph.region_of(arrived_map) == graph.region_of(leg.from_map):
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
