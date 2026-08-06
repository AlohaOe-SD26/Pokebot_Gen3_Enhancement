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


#: Lattice points sampled on the NEXT map when looking for somewhere to walk to. These are
#: cheap local ROM reads (`get_map_data(...).collision`), not pathfinding.
_CONNECTION_SAMPLES = 8  # per axis, so up to 64 probes
#: How many of those may be validated with `calculate_path`. Each validation is synchronous
#: and freezes the emulator, so this is a freeze budget — same reasoning as `_STAGED_VALIDATIONS`.
_CONNECTION_VALIDATIONS = 6


def _connection_step(graph, current_map, target_map, avoid_encounters, avoid_scripted_events):
    """A tile to WALK TO on the next map along the route, when no WARP validates.

    ‼ WHY THIS EXISTS — measured 2026-08-05, Fortree -> Mt. Pyre. The journey died on
    ROUTE120 (7,56) with `Could not find a path from (7/56 @ ROUTE120) to (22/29 @ ROUTE122)`,
    and the bot was NOT stuck: `calculate_path` reached ROUTE121 in **79 waypoints** the whole
    time. The hole is that both leg-pickers deal exclusively in WARPS —
    `pick_leg` walks `warp_candidates()` and `_staged_progress_warp` walks `warps_from()` —
    but **ROUTE120 -> ROUTE121 is a map CONNECTION, not a warp.** With no warp to offer, control
    fell through to the unvalidated `region_route[0]` branch, which handed `navigate_to` a tile
    two connections away that `calculate_path` can never span, and the whole trip failed.

    So: the navigator could WALK to a target, or WARP toward one, but it could not **walk across
    a map border as an intermediate step**. This is the connection analogue of
    `_staged_progress_warp`; the loop in `navigate_to_anywhere` already turns partial progress
    into a journey, so one border per iteration is enough.

    ‼‼ **DEFAULT OFF (`POKEBOT_CONNECTION_STEP=1` to enable). MEASURED HARMFUL AS WRITTEN.**
    It does cross the border (live A/B: old dies on ROUTE120, new reaches ROUTE121) — but it
    then STRANDS the bot. From the tile it chose, ROUTE121 (21,5), `calculate_path` cannot reach
    ROUTE121's own south edge ((10,19)/(20,19)/(0,19)), nor (22,12), nor (25,16) — so the onward
    route to ROUTE122 is sealed off. Route 121 has a north band and a south band that do not
    connect in the sampled region, and **the lattice below scans `y` from the TOP, so it is
    biased toward NORTHERN tiles — the wrong end when the target is south.**

    Two things must be fixed before this is enabled by default:
      1. **Aim the tile choice at the onward route.** `map_path.py` gives every edge-connected
         map a global `offset` and a shared `level` (`PathTile.global_coordinates`), which is the
         principled way to say "pick the candidate nearest where we go next". A first-walkable
         lattice scan is a coin flip.
      2. **Remember rejected step targets** (the `used_warps` pattern) so a re-plan offers a
         DIFFERENT tile instead of re-deriving the same one.
    ‼ And it must be BATCH-validated: this runs BEFORE the unvalidated `region_route[0]` branch,
    so it can divert journeys that succeed today. That is a whole-game regression vector, and
    this project has shipped three such regressions in one week by not measuring first.

    Returns `(map, tile)` to walk to, or None to leave existing behaviour untouched.
    """
    import os

    from modules.map import get_map_data

    if os.environ.get("POKEBOT_CONNECTION_STEP", "0").strip() not in ("1", "true", "True"):
        return None

    route = graph.map_route(current_map, target_map)
    if not route:
        return None
    next_map = tuple(route[0])
    # ‼ ONLY for a genuine border crossing. If the next hop is reached by a WARP, the warp
    # pickers above own it — walking "to" it here would duplicate their job and bypass the
    # `used_warps` bookkeeping that stops ping-pong.
    if next_map not in graph.connections.get(tuple(current_map), set()):
        return None

    try:
        head = get_map_data(next_map, (0, 0))
        width, height = head.map_size
        # ‼ NEVER offer a warp tile. Walking onto a warp FIRES it, so the trip would end one
        # map PAST the intended step and report success (08-MISTAKES 2026-08-05, twice).
        warp_tiles = {tuple(w.local_coordinates) for w in head.warps}
    except Exception:  # noqa: BLE001 — an unreadable map simply means "no opinion"
        return None

    step_x = max(1, width // _CONNECTION_SAMPLES)
    step_y = max(1, height // _CONNECTION_SAMPLES)
    candidates = []
    for y in range(1, height, step_y):
        for x in range(1, width, step_x):
            tile = (x, y)
            if tile in warp_tiles:
                continue
            try:
                if not get_map_data(next_map, tile).collision:
                    candidates.append(tile)
            except Exception:  # noqa: BLE001
                continue

    for tile in candidates[:_CONNECTION_VALIDATIONS]:
        if _walk_is_possible(next_map, tile, avoid_encounters, avoid_scripted_events):
            return next_map, tile
    return None


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

# ‼ KI-43. `_navigate_when_ready` may NOT use the cap above, and the reason is a hard
# constraint rather than a preference. StoryMode's global watchdog derails the run after
# **18,000 frames** with an unchanged progress signature (`story_mode.py`, `_stall_frames
# >= 18000`) — and a wrapper that waits while pressing nothing and changing nothing IS an
# unchanged signature. `_MAX_NON_OVERWORLD_FRAMES` is 60*60*5 = 18,000: the SAME number.
# The watchdog fires on frame 18,000 (`>=`) and the wrapper's `break` needs 18,001 (`>`),
# so the derail won by one frame every single time and the escape hatch was dead code.
#
# Measured (batch3 `3875843c` vs baseline `289d1710`): the Rustboro Poké Ball restock buys
# in batches of ten to farm the free Premier Ball per purchase, and the SECOND purchase
# re-enters navigation while the avatar is still settling out of the shop UI. Baseline
# chained three purchases 33/33; batch3 completed **0 of 36** — every one sat here for
# 18,000 frames and derailed, so each restock bought 10 balls instead of 30.
#
# So this wait must expire comfortably INSIDE the watchdog window, letting `navigate_to`
# raise its own honest "not in the overworld" error so `_navigate_riding_out` can spend a
# retry on it. The condition it exists for — a battle transition — clears in a few frames;
# ten seconds is already generous. Pinned by `repro_watchdog_budget_collision.py`.
_TRANSIENT_WAIT_FRAMES = 600  # 10s at 60 fps — must stay well under the 18,000 watchdog


def _map_name(map_group_and_number: tuple[int, int]) -> str:
    enum = MapRSE if context.rom.is_rse else MapFRLG
    try:
        return enum(tuple(map_group_and_number)).name
    except ValueError:
        return str(tuple(map_group_and_number))


def pick_leg(candidates, used_warps, visited_maps, is_walkable):
    """Choose which candidate warp to take: prefer one leading somewhere NEW.

    Pure, so it can be tested without an emulator — which matters, because the bug it
    encodes is invisible by inspection. `is_walkable(edge)` is injected for the same reason.

    ‼ THE TWO PASSES ARE THE WHOLE POINT. Having just warped INTO a map, the bot is
    STANDING ON the door back out, so a walkability check on that tile trivially succeeds in
    zero steps — and it is the first candidate the BFS offers. Observed 2026-07-31 by
    tracing the branch taken: `ROUTE116 -> RUSTURF_TUNNEL -> ROUTE116 -> RUSTURF_TUNNEL`,
    forever. `used_warps` cannot prevent it, because Rusturf Tunnel has THREE doors and the
    return trip is a DIFFERENT edge each time. The interior was passable all along
    (`calculate_path` (4,10) -> (29,16) inside the tunnel: OK, 42 waypoints) — the executor
    was thrashing, not blocked.

    A revisit is DEPRIORITISED, never forbidden: a real route can legitimately re-enter a
    map (out of a cave and back in by another mouth), so the second pass exists to allow
    exactly that once nothing new is available.
    """
    for allow_revisit in (False, True):
        for candidate in candidates:
            if candidate in used_warps:
                # A deterministic picker re-picks a failed choice forever unless the
                # failure is REMEMBERED (08-MISTAKES: "recovery is just a countdown to
                # Manual if the same inputs produce the same choice").
                continue
            if not allow_revisit and tuple(candidate.to_map) in visited_maps:
                continue
            if is_walkable(candidate):
                return candidate
    return None


#: How many candidate warps the staged-progress step may VALIDATE with `calculate_path`.
#: Each validation is synchronous (the emulator does not advance during it), so this is a
#: freeze budget, not a search-quality knob.
_STAGED_VALIDATIONS = 10


def _staged_progress_warp(graph, current_map, target_map, used_warps,
                          avoid_encounters: bool, avoid_scripted_events: bool,
                          visited_maps=frozenset()):
    """Pick a warp that gets us CLOSER even though it is not on any planned route.

    ‼ WHY THIS IS NEEDED, and why "one warp at a time" was not enough (measured
    2026-07-31, from `norman_done.ss1`). `warp_candidates` returns the first warp of a
    route to the TARGET — but the map graph is built from ROM headers, and those describe
    ROUTE104 as one connected map. It is not: **PETALBURG_WOODS is a separate map entered
    by a warp, and it splits Route 104 in two.** So the graph believes the whole journey
    Petalburg -> Fiery Path needs exactly ONE warp (`ROUTE112 -> FIERY_PATH`), both
    candidates for it are hundreds of tiles away behind that split, neither validates, and
    the executor stops with nothing to do. Measured from Petalburg: ROUTE104 31/200 tiles
    reachable, **PETALBURG_WOODS 0/132, RUSTBORO_CITY 0/150, ROUTE116 0/125**.

    The fix is to stop requiring the next step to be on a route to the goal, and instead
    take any reachable warp that does not move us further away — then re-plan from there.
    The loop in `navigate_to_anywhere` already re-plans after every warp, so partial
    progress compounds.

    ‼ THIS IS NOT THE REFUTED "GATEWAY WAYPOINTS" IDEA (KI-39, 2026-07-30). That one
    hand-picked a gateway and routed to it with `navigate_to_anywhere`, which took the same
    broken same-region branch and failed identically — it could not have worked. These
    waypoints are DERIVED from the graph, ranked by measured distance, and each is
    VALIDATED with `calculate_path` before being committed to.

    Ranking, both parts measured rather than assumed:
      * **distance to the target must not INCREASE.** From Petalburg every house/gym/mart
        door is 9 hops from Fiery Path against the current 8 — strictly worse — so this one
        rule excludes all of them. The Woods entrance is 8, and is kept.
      * **more onward exits wins ties.** The Woods entrance and Mr Briney's front door are
        BOTH exactly 8, so distance alone cannot tell "the way onward" from "a one-room
        house". Exit count can.
    """
    here_distance = graph.map_distance(current_map, target_map)
    if here_distance is None:
        return None

    # Warps on this map, and on maps directly connected to it (from Petalburg the useful
    # door is on ROUTE104, not in the city). Deliberately NOT the whole route: each
    # candidate costs a `calculate_path` to validate and the emulator is frozen throughout.
    nearby = [tuple(current_map), *sorted(graph.connections.get(tuple(current_map), ()))]
    scored = []
    for near_map in nearby:
        for edge in graph.warps_from(near_map):
            if edge in used_warps:
                continue
            distance = graph.map_distance(edge.to_map, target_map)
            if distance is None or distance > here_distance:
                continue
            # ‼ DEPRIORITISE MAPS WE HAVE ALREADY BEEN ON — this closes a real infinite
            # ping-pong, observed 2026-07-31 by tracing the branch taken:
            #     ROUTE116 -> RUSTURF_TUNNEL -> ROUTE116 -> RUSTURF_TUNNEL -> ...
            # Rusturf Tunnel's middle is sealed by the Wanda-quest rocks, so from just
            # inside it the ONLY walkable warp leads straight back out — and `used_warps`
            # cannot stop that, because the tunnel has THREE separate doors, so the return
            # trip is a DIFFERENT edge every time. This is the playbook's "chain walker
            # loops between floors: within-floor reachability is DIRECTIONAL" in a new
            # costume.
            #
            # Deprioritised, not excluded: a legitimate route can revisit a map (out of a
            # cave and back in by another mouth), so a visited destination is still allowed
            # as a LAST resort — it just never beats an unexplored one.
            revisit = 1 if tuple(edge.to_map) in visited_maps else 0
            scored.append((distance, revisit, -graph.onward_exits(edge.to_map), edge))
    scored.sort(key=lambda row: (row[0], row[1], row[2]))

    for _distance, _revisit, _exits, edge in scored[:_STAGED_VALIDATIONS]:
        if _walk_is_possible(edge.from_map, edge.from_coords, avoid_encounters, avoid_scripted_events):
            return edge
    return None


def _navigate_when_ready(navigate_to, *args, **kwargs):
    """`navigate_to`, but WAIT for the overworld first instead of raising on a transition.

    ‼ WHY (measured 2026-07-31, `norman_done.ss1` -> FIERY_PATH). The journey reached
    ROUTE116 and then failed **24 times in a row** with
    `The game is currently not in the overworld. Cannot navigate.` — `navigate_to`'s entry
    guard (`walking.py:175`). The harness heartbeat at the failure read
    `ctrl=SmashRouteMode.run state=BATTLE_STARTING`, in a run of wild encounters on Route
    116 grass. The bot was not stuck: it was being asked to navigate DURING a battle
    transition, a condition that clears itself in a few frames.

    `navigate_to_anywhere` waits for the overworld at the top of its loop, but not every
    `navigate_to` below that is reached without yielding first — the "step off the warp
    tile and walk back on" fork presses directional buttons for up to 80 frames, and a wild
    encounter starting in that window lands squarely on the next `navigate_to`. A transient
    was being reported as a routing failure, and `_navigate_riding_out` then spent a whole
    retry on it (its fail-fast guard cannot help: that guard only records a position while
    the avatar is CONTROLLABLE, which it is not mid-battle).

    ‼ KI-43 — THIS USED TO BE BOUNDED BY `_MAX_NON_OVERWORLD_FRAMES`, "the same generous cap
    as the loop's own wait, so a genuine softlock still surfaces rather than yielding for
    ever". That cap is 18,000 frames and the global watchdog derails at 18,000 frames of
    unchanged progress signature — which is exactly what this loop produces, because it
    presses nothing and changes nothing. The derail won by one frame EVERY time and the
    `break` below never once executed. See `_TRANSIENT_WAIT_FRAMES` above for the measurement.
    """
    from modules.player import player_avatar_is_controllable

    waited = 0
    while get_game_state() is not GameState.OVERWORLD or not player_avatar_is_controllable():
        waited += 1
        if waited > _TRANSIENT_WAIT_FRAMES:
            break  # let `navigate_to` raise its own honest error rather than hang here
        yield
    yield from navigate_to(*args, **kwargs)


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
    #: Maps we have already stood on during THIS journey. Used to deprioritise a warp that
    #: would take us somewhere we have already been — see `_staged_progress_warp`, which is
    #: where the ROUTE116 <-> RUSTURF_TUNNEL ping-pong was closed.
    visited_maps: set = set()
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
        visited_maps.add(current_map)

        # --- 1. Can we simply WALK there? Unchanged fast path. -------------------
        # This is the branch every existing caller already takes for a same-region
        # target; asking `calculate_path` first only changes what happens when the
        # answer is NO (see 2). A YES behaves exactly as it did before.
        if _walk_is_possible(target_map, target_coords, avoid_encounters, avoid_scripted_events):
            yield from _navigate_when_ready(
                navigate_to,
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
        # ‼ TWO PASSES: prefer a door to somewhere NEW, and only accept a door back to a map
        # we have already stood on if nothing else works. Without this the executor walks
        # straight back out the way it came in, for a reason that is obvious only once seen:
        # having just warped into RUSTURF_TUNNEL, the bot is STANDING ON the door back to
        # ROUTE116, so `_walk_is_possible` on that tile trivially succeeds (zero steps) and
        # it is the first candidate the BFS offers. Result, observed by tracing the branch
        # taken 2026-07-31: ROUTE116 -> TUNNEL -> ROUTE116 -> TUNNEL, forever.
        # `used_warps` cannot prevent it — the tunnel has THREE doors, so the trip back is a
        # different edge each time — and the interior really is passable
        # (`calculate_path` (4,10) -> (29,16) inside the tunnel: OK, 42 waypoints), so this
        # was pure self-inflicted thrash, not a blocked route.
        leg = pick_leg(
            candidates,
            used_warps,
            visited_maps,
            lambda c: _walk_is_possible(
                c.from_map, c.from_coords, avoid_encounters, avoid_scripted_events
            ),
        )

        if leg is None:
            # --- 2b. STAGED PROGRESS ------------------------------------------------
            # Nothing on a route to the goal is reachable. That does NOT mean we are
            # stuck: it usually means the graph is wrong about a map being walkable
            # (PETALBURG_WOODS splits ROUTE104, which the ROM headers do not say), so the
            # planned first warp is on the far side of a split we have not crossed yet.
            # Take a reachable warp that does not move us further away and re-plan from
            # there; the loop above turns partial progress into a journey.
            leg = _staged_progress_warp(
                graph, current_map, target_map, used_warps,
                avoid_encounters, avoid_scripted_events, visited_maps,
            )

        if leg is None:
            # --- 2c. CONNECTION STEP (2026-08-05) -----------------------------------
            # No WARP validates — but the next hop may simply be the map next door, which
            # neither picker above can express (both deal only in warps). Measured: the
            # Fortree -> Mt. Pyre journey died on ROUTE120 while ROUTE121 was reachable in
            # 79 waypoints, because ROUTE120 -> ROUTE121 is a CONNECTION.
            #
            # ‼ ORDER IS DELIBERATE: this sits AFTER both warp pickers (a real warp route is
            # always preferred) and BEFORE the unvalidated `region_route[0]` branch below, so
            # that branch stops being REACHED rather than being deleted. Deleting it outright
            # would be the "remove a behaviour because its failure is loud" move that cost
            # three regressions in one week — its own comment claims it keeps working
            # cross-region journeys alive, and that claim is untested either way.
            step = _connection_step(
                graph, current_map, target_map, avoid_encounters, avoid_scripted_events
            )
            if step is not None:
                step_map, step_tile = step
                context.message = f"Story: crossing into {_map_name(step_map)}…"
                yield from _navigate_when_ready(
                    navigate_to,
                    step_map,
                    step_tile,
                    run=run,
                    avoid_encounters=avoid_encounters,
                    avoid_scripted_events=avoid_scripted_events,
                )
                yield from wait_for_player_avatar_to_be_standing_still()
                # Counts against the leg budget: a border crossing is progress, and without
                # this an oscillation between two maps would be unbounded.
                legs_taken += 1
                continue

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
                yield from _navigate_when_ready(
                    navigate_to,
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
        yield from _navigate_when_ready(
            navigate_to,
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
                yield from _navigate_when_ready(
                    navigate_to,
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
