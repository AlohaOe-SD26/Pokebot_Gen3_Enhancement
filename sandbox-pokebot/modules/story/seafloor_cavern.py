"""§Ch20 — the SEAFLOOR CAVERN: dive in, solve nine rooms, wake Kyogre, escape the atoll.

‼ WHAT THIS CHAPTER IS ASSEMBLED FROM. Every leg below was DRIVEN STANDALONE first, as
`--driver ch20dive / ch20room1 / ch20room2 / ch20room6 / ch20room3 / ch20room8 / ch20room9`, each
reaching `ACCEPTANCE: PASS`. This module is the ASSEMBLY of proven ingredients, not new navigation.
Re-verified 2026-08-24 (`evidence/2026-08-24-ch20-ingredients-reverified.stdout.txt`) after the
abort-guard sweep touched `early_game.py`: the full nine-room chain still passes.

⛔⛔ THE FOUR TRAPS. Each cost a real drive to find; none is theoretical.

 1. KI-72 — NEVER LET THE PLANNER CHOOSE WHERE YOU SURFACE. `map_path` has never heard of
    `Underwater Blocked Above` / `Seaweed No Surfacing` and marks them accessible from all four
    directions, so it will happily route a dive to a tile you cannot come up on. Pick the surface
    tile EXPLICITLY and assert its `tile_type` before calling `surface_from_dive()`.

 2. ROOM 8 STEP 9 FACES **LEFT**, NEVER UP. Pushing north from `(5,4)` puts a boulder on `(5,3)` and
    PERMANENTLY seals the `(5,2)` door to Room 9 — the run is dead with no recovery but a reset.

 3. THE TRIGGER IS `ROOM9 (17,42)`, NOT `(16,42)`. `(16,42)` is plain floor and fires nothing.
    ‼ Upstream's own `puzzle_solver.py:457` navigates to `(16,42)` and then hands to a human, so
    copying upstream's route silently fires nothing at all.

 4. THE EXIT IS SOUTH. The chapter lands on `ROUTE128 (38,22)`, which is `MB_SHALLOW_WATER`:
    walkable wading, NOT surfable — so "surf from where you land" does nothing in any direction and
    reads as a hung leg. Step SOUTH to `(38,23)`, then Surf onto `(38,24)`.
    ⚠ DECOMP-CORRECTED 2026-08-24: the tile NORTH `(38,21)` is *also* sandbar (it is Maxie's spawn
    tile), and the closed lagoon starts two north at `(38,20)`. Of the sandbar ring's surf-entry
    points, **28 lead into the 41-tile lagoon and 46 into the 1,766-tile open ocean** — which is why
    the launch tile is hand-picked for exactly the same reason the surfacing tile is.

⛔⛔ TWO TRANSCRIPTION RULES, both earned by defects found while assembling this file.

 A. COMPARE MAPS BY ENUM VALUE, NEVER BY NAME STRING — and use `_on_map()` below, not a hand-rolled
    comparison. The harness's `_where()` returns the map's **NAME** (`MapRSE(...).name`, a string);
    this module's returns its **(group, number) tuple**. Every harness comparison — `where[0] ==
    "SEAFLOOR_CAVERN_ROOM8"`, `not in ("SEAFLOOR_CAVERN_ROOM9", "ROUTE128")` — copied verbatim would
    compare an int-pair against a string and be **ALWAYS UNEQUAL**, silently. The worst instance is
    the cutscene ride's whiteout guard: on a PERFECT run it would fire on the first iteration of
    every milestone and print a fabricated "WHITEOUT" signature. The second worst grades a flawless
    Room 6 crossing as FAIL. ‼ `_where()` can also return a REASON STRING, and indexing a string
    yields a character that likewise compares unequal forever — so test `isinstance(..., tuple)`
    first. `_on_map()` does both.

 B. NEVER LIFT A BARE TUPLE BETWEEN ROOMS — always pass the map enum and the tile TOGETHER. This
    cavern reuses coordinates across maps constantly, and the collisions are vicious:
    `(5,10)` is Room 1's boulder approach AND a `collision=1` ledge row in Room 8; `(4,1)` is Room
    6's door AND Room 2's ILLEGAL fourth-push target; `(4,5)` appears in both push tables with the
    SAME facing on different maps; `(4,10)` is Room 1's rock approach AND a Room 2 warp.

⛔ THERE IS NO PARTIAL RESUME INSIDE THE CAVERN. Every room is a `FLAG_TEMP_*` room, so all puzzle
state resets on every map load. Any re-entry re-solves Rooms 1 through 8 from scratch (~25 minutes).
The "already at the next hop, skip it" idiom other chapters use is WRONG here and must not be
copied. The only resume boundaries are: before the dive, and after `ROUTE128_STATE == 2`.

‼ GRADE ON `ROUTE128_STATE`, NEVER ON `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`. The flag is set at
`Room9/scripts.inc:128`, BEFORE the warp at `:138` and before a SECOND lock-all cutscene on Route
128 — a flag-graded chapter reports success from inside two nested scenes while standing on a
sandbar it cannot leave.
⛔ AND THE NAME IS BARE: `ROUTE128_STATE`. `VAR_ROUTE128_STATE` — the decomp's spelling, and what
every doc in this repo said until 2026-08-24 — is NOT in `_event_vars`, and `get_event_var` returns
**-1** for an unknown name, which compares False against every threshold forever. `_done_var` in
`story_mode.py` RAISES on a phantom name, which is exactly why the segment guard goes through it
instead of reading the var directly.
"""

from typing import Generator

from modules.context import context
from modules.map_data import MapRSE

# ---------------------------------------------------------------------------------------------
# TILES. Every one of these was MEASURED in a drive; none is inferred from a map dump.
# ---------------------------------------------------------------------------------------------
DIVE_TILE = (38, 27)          # ROUTE128, deep water: where we dive
CAVERN_DOOR = (38, 26)        # UNDERWATER_ROUTE128: the water door in
POOL_TILE = (6, 6)            # UNDERWATER_SEAFLOOR_CAVERN: the hand-picked surfacing pool (KI-72)
#: ⚠ NOT merely "the approach tile". Stepping onto it SOUTHWARD takes the 'Water South Arrow Warp'
#: straight back out to Route 128 — so never route casually through it.
CAVERN_EXIT = (6, 7)          # UNDERWATER_SEAFLOOR_CAVERN 'Water South Arrow Warp' -> ROUTE128
#: ⚠ THIS IS THE WAY BACK OUT, NOT WHERE WE COME UP. Measured in the drive: we surface at
#: `SEAFLOOR_CAVERN_ENTRANCE (10,17)`; `(10,18)` is the Deep Water tile you re-dive from.
#: An earlier comment here said "where we come up", which invites someone to "correct" the value.
#: ⛔ The forward chapter never uses this — it belongs to the harness's return-trip proof.
ENTRANCE_WATER = (10, 18)     # SEAFLOOR_CAVERN_ENTRANCE Deep Water — the way back OUT

ROOM1_WARP_UP = (10, 1)       # SEAFLOOR_CAVERN_ENTRANCE: the north exit into ROOM1
#: ⚠ PREDICTED, NOT A CONSTANT OF THE DRIVE. The harness READS the Room 1 arrival live
#: (`story_harness.py:6790`) rather than asserting this value; it is recorded here only so a log
#: line can say "(PREDICTED (5,18))". ⛔ Do not navigate TO it — read where you actually landed.
ROOM1_ARRIVAL_PREDICTED = (5, 18)
ROCK_APPROACH = (4, 10)       # face Right at BREAKABLE_ROCK (5,10)
BOULDER1_APPROACH = (5, 10)   # face Down  -> boulder (5,11) travels to (5,12)
BOULDER2_APPROACH = (11, 11)  # face Right -> boulder (12,11) travels to (13,11)
ROOM1_CORRIDOR_PROBE = (11, 11)
ROOM2_DOOR = (6, 2)

ROOM2_SMASH_APPROACH = (9, 7)                                     # face Left
ROOM2_PUSHES = (((4, 6), "Up"), ((4, 5), "Up"), ((4, 4), "Up"))   # EXACTLY three; a 4th is illegal
ROOM6_DOOR = (6, 1)

ROOM6_ENTRY = (11, 21)
ROOM6_EXIT = (4, 1)
ROOM3_ARRIVAL = (4, 15)
ROOM3_SIGHT_TILE = (6, 5)     # the confirmed DOUBLE trainer battle
ROOM3_EXIT = (8, 1)

ROOM8_ARRIVAL = (5, 12)
ROOM8_STAGING = (5, 8)
ROOM8_RETREAT = (5, 12)       # the arrow warp back to ROOM3, used by jam recovery
ROOM9_DOOR = (5, 2)
ROOM9_ARRIVAL = (5, 4)

ROOM9_TRIGGER = (17, 42)      # ⛔ NOT (16,42) — see trap 3
ROUTE128_LANDING = (38, 22)   # MB_SHALLOW_WATER: walkable, NOT surfable
ESCAPE_STAND = (38, 23)       # one step SOUTH, still sandbar
ESCAPE_WATER = (38, 24)       # MB_OCEAN_WATER: the launch tile
OCEAN_PROBE = (38, 27)        # proves we are in the 1,766-tile ocean, not the 41-tile lagoon

#: THE ADJUDICATED 9-PUSH SEQUENCE: (approach_tile, face). `strength_push` derives the boulder tile
#: (approach+1) and the destination (approach+2) itself and re-navigates to each approach on its own,
#: which is why rows 3 and 7 need no special casing here.
#: ⛔ COPIED VERBATIM FROM THE DRIVEN SOURCE, `tools/story-dev/story_harness.py:8060-8069`, which
#: executed with `attempts=1` and `exit_ok=True`. ⛔ DO NOT RE-DERIVE THESE, DO NOT "TIDY" THEM, and
#: do not trust any table that is not character-identical to that one.
#: ‼ A FABRICATED VERSION OF THIS TABLE WAS BRIEFLY COMMITTED TO THIS FILE (2026-08-24) — written
#: from a spec that CITED the line range without quoting it, so plausible-looking values were
#: invented. **8 of the 9 rows were wrong**; only row 9 (the one a warning had drawn attention to)
#: happened to be right. It was caught by a routing-extraction agent that read the real source.
#: ⇒ A FILE:LINE CITATION IS A POINTER, NOT THE CONTENT. Open it.
ROOM8_PUSHES = (
    ((5, 8), "Up"),      # 1: boulder (5,7) -> (5,6)
    ((5, 7), "Left"),    # 2: boulder (4,7) -> (3,7)
    ((4, 6), "Right"),   # 3: boulder (5,6) -> (6,6)   (the push-1 boulder, again)
    ((5, 6), "Up"),      # 4: boulder (5,5) -> (5,4)
    ((5, 5), "Left"),    # 5: boulder (4,5) -> (3,5)
    ((4, 5), "Up"),      # 6: boulder (4,4) -> (4,3)
    ((5, 5), "Right"),   # 7: boulder (6,5) -> (7,5)
    ((6, 5), "Up"),      # 8: boulder (6,4) -> (6,3)
    ((6, 4), "Left"),    # 9: boulder (5,4) -> (4,4)  ⛔ LEFT — Up would seal (5,3) forever
)


def _var(name: str):
    """Read an event var, returning a REASON STRING on failure rather than None.

    ‼ A bare `get_event_var` returns -1 for an UNKNOWN NAME, which is indistinguishable from a
    genuine -1 and compares False against every threshold forever. Callers that must not be fooled
    go through `story_mode._done_var`, which RAISES on a phantom name.
    """
    from modules.story.early_game import reraise_if_aborting

    try:
        from modules.memory import _event_vars, get_event_var

        if name not in _event_vars:
            return f"<phantom var name {name!r}>"
        return int(get_event_var(name))
    except Exception as error:  # noqa: BLE001 - a reason string beats a crash in a diagnostic
        reraise_if_aborting(error)
        return f"<unreadable: {type(error).__name__}>"


def _flag(name: str):
    """Read an event flag, returning a REASON STRING on failure rather than None."""
    from modules.story.early_game import reraise_if_aborting

    try:
        from modules.memory import _event_flags, get_event_flag

        if name not in _event_flags:
            return f"<phantom flag name {name!r}>"
        return bool(get_event_flag(name))
    except Exception as error:  # noqa: BLE001 - see `_var`
        reraise_if_aborting(error)
        return f"<unreadable: {type(error).__name__}>"


def _where():
    """(map tuple, local coords), or a reason string — never None."""
    from modules.story.early_game import reraise_if_aborting

    try:
        from modules.player import get_player_avatar

        avatar = get_player_avatar()
        return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)
    except Exception as error:  # noqa: BLE001 - see `_var`
        reraise_if_aborting(error)
        return f"<unreadable: {type(error).__name__}>"


def _on_map(map_enum) -> bool:
    """Are we on this map RIGHT NOW? Compares by enum VALUE, and survives a reason string.

    ⛔ USE THIS INSTEAD OF COMPARING MAP NAMES. See transcription rule A in the module docstring:
    the harness compares `MapRSE(...).name` strings, this module carries `(group, number)` tuples,
    and a verbatim copy of a harness comparison is silently ALWAYS FALSE — which turns a perfect
    run's whiteout guard into a fabricated alarm and a flawless Room 6 crossing into a FAIL.
    """
    where = _where()
    if not isinstance(where, tuple):
        return False
    return where[0] == map_enum.value


def _at(map_enum, tile) -> bool:
    """Are we on this map AND this exact tile? Pass both together — never a bare tuple.

    See transcription rule B: this cavern reuses coordinates across maps, and at least one reused
    tuple is a walkable approach on one map and a `collision=1` ledge on another.
    """
    where = _where()
    if not isinstance(where, tuple):
        return False
    return where[0] == map_enum.value and tuple(where[1]) == tuple(tile)


def route128_scene_outstanding() -> bool:
    """True when the cavern scene has RUN but the Route 128 scene has not finished.

    ⛔ DECOMP-VERIFIED 2026-08-24, AND IT CORRECTS THIS PROJECT'S OWN BUILD SPEC. The spec proposed
    branching on "the Kyogre flag is set but the var is < 2". That test CANNOT DISCRIMINATE: in
    `SeafloorCavern_Room9/scripts.inc`, `setvar VAR_ROUTE128_STATE, 1` is at `:115` and
    `setflag FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` is at `:128` — thirteen lines LATER, in the same
    script. There is no reachable state with the flag set and the var still at 0, so the flag half
    is dead code. ⇒ the honest condition is simply that the var sits at exactly 1.

    Recovery is REAL and cheap. `Route128_OnFrame` is
    `map_script_2 VAR_ROUTE128_STATE, 1, Route128_EventScript_KyogreAwakenedScene`, and ON_FRAME
    scripts run "every frame after the map has faded in, before player input is processed" — so
    simply BEING on Route 128 with the var at 1 re-fires the scene, which ends `setvar ..., 2`.
    ⛔ DO NOT try to recover by re-diving the cavern: `VAR_SEAFLOOR_CAVERN_STATE` is 1 and NOTHING in
    the game ever resets it (3 references repo-wide), so the `(17,42)` coord event is disarmed
    permanently.
    ‼ AND IT IS WORTH CLEARING PROMPTLY: Route 128 sits on the surf route to Ever Grande, so a stale
    `ROUTE128_STATE == 1` means the first frame of field control there — possibly mid-Elite-Four —
    is seized by a minute-long cutscene.
    """
    return _var("ROUTE128_STATE") == 1


def escape_outstanding() -> bool:
    """True when the SCENE is finished but the run is still parked on the atoll sandbar.

    ⛔ THIS CLOSES A REAL RESUME GAP, found by adversarial review. Between `ROUTE128_STATE` reaching
    2 and the escape walk completing there is a window where NEITHER other predicate helps:
      * `seafloor_cavern_done()` is False — we are still standing on `ROUTE128_LANDING`;
      * `route128_scene_outstanding()` is False — the var is 2, not 1.
    Without this branch the retry loop would RE-DIVE, ~25 minutes, into a trigger that is disarmed
    permanently, and do it up to three times before failing.
    ‼ The window is small but not exotic: the escape is two navigates plus a Surf launch, and an
    ordinary `BotModeError` anywhere in there lands exactly here.
    """
    route128_state = _var("ROUTE128_STATE")
    if not isinstance(route128_state, int) or route128_state < 2:
        return False
    from modules.map_data import MapRSE

    return _on_map(MapRSE.ROUTE128) and not seafloor_cavern_done()


def seafloor_cavern_done() -> bool:
    """§Ch20 complete: the release var reached 2 AND we are not still parked on the sandbar.

    ‼ The position half is written as "NOT standing on the landing tile", never as "surfing at
    `(38,24)`". The latter goes false forever once a later chapter sails away, which would re-run
    §Ch20 on every future resume.
    """
    route128_state = _var("ROUTE128_STATE")
    if not isinstance(route128_state, int) or route128_state < 2:
        return False
    where = _where()
    if not isinstance(where, tuple):
        return False
    current_map, coords = where
    if current_map != MapRSE.ROUTE128.value:
        return True  # already sailed on: strictly stronger than "off the sandbar"
    return coords != ROUTE128_LANDING


def assert_cavern_preflight() -> None:
    """Refuse to start unless the party can actually finish. Raises with a NAMED cause.

    ⛔ BADGE07 IS NOT DECORATION. The field-move gate is `map_path.py:794`:
    `context.rom.is_rse and get_event_flag("BADGE07_GET") and get_party().has_pokemon_with_move("Dive")`
    — so knowing Dive WITHOUT the badge makes the entire cavern unroutable, and the failure would
    present as a pathfinding error rather than a permissions error, which is a miserable thing to
    debug from a log.
    ‼ Upstream asserts Strength/Rock Smash/Surf only (`puzzle_solver.py:359-363`) because it starts
    the player INSIDE the cavern. Ours starts on the open ocean, so Dive and BADGE07 are additions,
    not copies.
    """
    from modules.modes import BotModeError
    from modules.modes._asserts import assert_has_pokemon_with_any_move

    assert_has_pokemon_with_any_move(["Dive"], "Seafloor Cavern needs a Pokémon that knows Dive.")
    assert_has_pokemon_with_any_move(["Surf"], "Seafloor Cavern needs a Pokémon that knows Surf.")
    assert_has_pokemon_with_any_move(
        ["Strength"], "Seafloor Cavern needs a Pokémon that knows Strength (Rooms 1, 2 and 8)."
    )
    assert_has_pokemon_with_any_move(
        ["Rock Smash"], "Seafloor Cavern needs a Pokémon that knows Rock Smash (Rooms 1 and 2)."
    )
    if _flag("BADGE07_GET") is not True:
        raise BotModeError(
            "Seafloor Cavern: BADGE07 (Mind Badge) is not held, so Dive is not field-usable. "
            "The cavern would be unroutable and the failure would surface as a pathfinding error. "
            f"(BADGE07_GET read {_flag('BADGE07_GET')!r}.)"
        )


def dive_into_the_cavern() -> Generator:
    """ROUTE128 -> dive -> the underwater cavern door -> surface inside SEAFLOOR_CAVERN_ENTRANCE.

    Transcribed from the driven `Ch20DiveMode._ingress` (`story_harness.py:6457-6548`), which
    reached `legs=6/6 at_entrance=True`.

    ⛔ THE KI-72 GUARD IS THE POINT OF THIS LEG. `map_path` cannot see `Underwater Blocked Above` or
    `Seaweed No Surfacing` and marks them reachable from all four directions, so it will happily
    route a dive to a tile you cannot come up on. We pick the surfacing tile EXPLICITLY and assert
    its `tile_type` first. ‼ The assert is written as a POSITIVE test ("it must be Deep Water")
    rather than a denylist, so an unreadable tile or a tile type nobody has met yet FAILS CLOSED.
    ⚠ This cavern happens to contain no un-surfaceable tile at all — that is INSURANCE, not a reason
    to delete the guard.

    ⛔ NEVER transcribe `_inject_dive_fixture` (`story_harness.py:6389-6455`). It `debug_write_party`s
    a Wailmer into slot 3 to give the drivers Dive. Production REFUSES (see `assert_cavern_preflight`)
    — it does not fabricate a party member.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import dive, surface_from_dive
    from modules.modes.util.walking import navigate_to
    from modules.player import AvatarFlags, get_player_avatar
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

    # ⛔ Starting already underwater is NOT a state this leg knows how to recover from, and
    # improvising a surface here could come up on a blocked tile. Refuse loudly instead.
    if AvatarFlags.Underwater in get_player_avatar().flags:
        raise BotModeError(
            "Seafloor Cavern: the run is already UNDERWATER at the start of the dive leg. "
            "That is not a state this chapter knows how to recover from — surface manually, or "
            f"restart the segment from the overworld. (at {_where()})"
        )

    yield from wait_until_truly_controllable()
    yield from _navigate_riding_out(MapRSE.ROUTE128, DIVE_TILE)
    if not _at(MapRSE.ROUTE128, DIVE_TILE):
        raise BotModeError(
            f"Seafloor Cavern: could not reach the dive tile {DIVE_TILE} on Route 128 — at {_where()}."
        )

    yield from dive()
    # ⛔ run=False on both underwater legs: the harness drives them walking, and that is what passed.
    yield from navigate_to(MapRSE.UNDERWATER_ROUTE128, CAVERN_DOOR, False)
    yield from navigate_to(MapRSE.UNDERWATER_SEAFLOOR_CAVERN, POOL_TILE, False)

    # --- KI-72: assert the surfacing tile BEFORE asking to come up -------------------------------
    from modules.map import get_map_data_for_current_position

    tile = get_map_data_for_current_position()
    tile_type = getattr(tile, "tile_type", None)
    if tile_type != "Deep Water":
        raise BotModeError(
            f"Seafloor Cavern (KI-72): refusing to surface at {POOL_TILE} — its tile_type is "
            f"{tile_type!r}, not 'Deep Water'. The planner cannot see un-surfaceable water, so "
            f"surfacing here could strand the run underwater."
        )

    yield from surface_from_dive()
    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ENTRANCE):
        raise BotModeError(
            f"Seafloor Cavern: surfaced but not in SEAFLOOR_CAVERN_ENTRANCE — at {_where()}."
        )
    context.message = f"Story: inside the Seafloor Cavern at {_where()}."


def enter_room1() -> Generator:
    """SEAFLOOR_CAVERN_ENTRANCE -> the north warp -> SEAFLOOR_CAVERN_ROOM1.

    From the driven `_enter_room1` (`story_harness.py:6780-6792`). `_navigate_riding_out` owns the
    surf-to-land dismount out of the entrance pool, so this leg does not do it by hand.

    ‼ THE ARRIVAL TILE IS READ LIVE, NOT ASSERTED AS A DESTINATION. `ROOM1_ARRIVAL_PREDICTED (5,18)`
    exists only so a log line can say "(PREDICTED …)". The harness reads where it actually landed
    (`story_harness.py:6790`), and so do we.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.player import get_player_avatar
    from modules.story.early_game import (
        _navigate_riding_out,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    try:
        yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ENTRANCE, ROOM1_WARP_UP)
    except Exception as error:  # noqa: BLE001 - a warp firing MID-WALK legitimately raises here
        reraise_if_aborting(error)
        # Not swallowed blindly: the map check below is the real verdict, and it runs either way.

    yield from wait_until_truly_controllable()
    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM1):
        raise BotModeError(
            f"Seafloor Cavern: took the {ROOM1_WARP_UP} warp but did not land in ROOM1 — "
            f"at {_where()}."
        )
    arrival = tuple(get_player_avatar().local_coordinates)
    context.message = f"Story: Seafloor Cavern ROOM1 at {arrival} (predicted {ROOM1_ARRIVAL_PREDICTED})."


def solve_room1() -> Generator:
    """Room 1: smash the rock, push two boulders, leave by the (6,2) door into Room 2.

    From the driven `_solve_room1` (`story_harness.py:6794-6899`), whose A/B is the real evidence:
    `calculate_path` to the corridor probe goes `PathFindingError` BEFORE and `OK len=6` AFTER, so
    the puzzle is measurably what opens the route rather than something we merely did on the way.

    ⛔ SMASHING BEFORE PUSH 1 IS FORCED, NOT STYLISTIC: `BOULDER1_APPROACH (5,10)` **is the rock's
    own tile**, so the push cannot be approached until the rock is gone.
    ⛔ DO NOT BACK-TRACK DOWN COLUMN 5 IN THE SAME MAP LOAD. From `(6,2)` the KI-77 despawn window
    covers y ∈ [-5,11], so boulder 1 parked at `(5,12)` would despawn and RESPAWN AT ITS TEMPLATE
    `(5,11)` — silently undoing the push in-game while our own bookkeeping still believed it.
    ⚠ Decoy: ROOM1 `(17,13)` is a South Arrow Warp to ROOM5. Our route stops at x=13; a drifting
    re-plan that steps south at x=17 leaves the room and re-arms every `FLAG_TEMP_*` in it.
    ⚠ Expected, not exceptional: the grunt at `(8,6)` has sight radius 2 and sits on the row-7 walk,
    so a trainer battle here is part of the route, not a fault.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import _navigate_riding_out, _smash_rock, strength_push

    yield from _smash_rock(MapRSE.SEAFLOOR_CAVERN_ROOM1, ROCK_APPROACH, "Right")
    yield from strength_push(MapRSE.SEAFLOOR_CAVERN_ROOM1, BOULDER1_APPROACH, "Down")
    yield from strength_push(MapRSE.SEAFLOOR_CAVERN_ROOM1, BOULDER2_APPROACH, "Right")

    yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM1, ROOM2_DOOR)
    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM2):
        raise BotModeError(
            f"Seafloor Cavern: solved Room 1 but the {ROOM2_DOOR} door did not land us in ROOM2 — "
            f"at {_where()}."
        )
    context.message = f"Story: Seafloor Cavern ROOM2 at {_where()}."


def solve_room2() -> Generator:
    """Room 2: smash, push a boulder north EXACTLY THREE times, leave by the (6,1) door into Room 6.

    From the driven `_solve_room2` (`story_harness.py:7108-7222`).

    ⛔ EXACTLY THREE PUSHES, independently re-derived: the `(6,1)` door only becomes reachable after
    the THIRD push (flood-fill reachable-count 9 → 21 → 22 → 23 → **31**), and a FOURTH push would
    target `(4,1)`, which is `collision=1`. More is not safer here.
    ‼ `FLAG_SYS_USE_STRENGTH` reads FALSE on entry — it is cleared by the ROOM1→ROOM2 warp, NOT
    "never cleared once per save" as one harness docstring still claims. `strength_push` re-activates
    Strength per call, which is why that stale comment costs nothing in practice. ⛔ Do not
    "optimise" the re-check away on the strength of that comment.
    ⛔ Do NOT copy upstream's shape (`puzzle_solver.py:399-401`: `use_strength` plus two bare
    `walk_one_tile`s) even though its tiles are right — wild encounters are live on every push tile
    here, and a battle between pushes breaks blind walking.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import (
        _check_abort,
        _navigate_riding_out,
        _smash_rock,
        strength_push,
        wait_until_truly_controllable,
    )

    yield from wait_until_truly_controllable()
    # `_smash_rock` navigates to its own approach tile, so no separate walk here.
    yield from _smash_rock(MapRSE.SEAFLOOR_CAVERN_ROOM2, ROOM2_SMASH_APPROACH, "Left")

    for approach, face in ROOM2_PUSHES:
        _check_abort()  # ⛔ FIRST statement, OUTSIDE any try: StoryAbort subclasses BotModeError
        yield from strength_push(MapRSE.SEAFLOOR_CAVERN_ROOM2, approach, face)

    yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM2, ROOM6_DOOR)
    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM6):
        raise BotModeError(
            f"Seafloor Cavern: solved Room 2 but the {ROOM6_DOOR} door did not land us in ROOM6 — "
            f"at {_where()}."
        )
    context.message = f"Story: Seafloor Cavern ROOM6 at {_where()}."


def cross_room6() -> Generator:
    """Room 6: the water-current maze, ending in Room 3. ⛔ ONE-WAY — there is no backing out.

    From the driven `_cross_room6` (`story_harness.py:7355-7431`). This was the first executed
    current crossing in this project; Rooms 6/7 were planner-level only until it ran, and a plan is
    not a walk.

    ⛔ `(4,1)` IS A STEP-ON DOOR, NOT A PARK TILE. The navigate is EXPECTED to end on
    `SEAFLOOR_CAVERN_ROOM3 (4,15)` because the door fires mid-walk — so "we did not arrive at
    `(4,1)`" is the success case, not a failure. The verdict is the MAP we ended on.
    ⛔ NO RETRY LOOP. The room is one-way; a retry would have nothing to retry from.
    ‼ If the walk does leave us still in Room 6, step onto the door deliberately rather than
    re-planning — `_pass_through_door` makes the warp tile a navigation target.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import (
        _navigate_riding_out,
        _pass_through_door,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    yield from wait_until_truly_controllable()
    try:
        yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM6, ROOM6_EXIT)
    except Exception as error:  # noqa: BLE001 - the door firing MID-WALK legitimately raises
        reraise_if_aborting(error)
        # Deliberately not re-raised: the map check below is the verdict either way.

    if _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM6):
        yield from _pass_through_door(ROOM6_EXIT, MapRSE.SEAFLOOR_CAVERN_ROOM6.value)

    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM3):
        raise BotModeError(
            f"Seafloor Cavern: crossed Room 6 but did not reach ROOM3 — at {_where()}. "
            f"Room 6 is ONE-WAY, so there is no retry from here."
        )
    context.message = f"Story: Seafloor Cavern ROOM3 at {_where()}."


def cross_room3() -> Generator:
    """Room 3: the push-free walk to the (8,1) door into Room 8. Its 7-boulder puzzle is OPTIONAL.

    From the driven `_cross_room3` (`story_harness.py:7867-7938`).

    ‼ ONE CALL IS THE WHOLE WALK. There is no step list and no direction table here, deliberately.
    The "18 steps" figure in the docs is a MEASURED `len(calculate_path)`, not a route to copy — and
    a copied step list would go stale the moment a defeated Shelly stands on `(7,5)`.
    ⚠ The route MUST pass the sight tile `(6,5)`, where an unavoidable **DOUBLE** trainer battle
    fires. That is the route, not a fault; `StoryMode.on_battle_started` owns the battle.
    ⛔ Two usable Pokémon are required BEFORE the walk, and this RAISES rather than logging: a double
    battle entered with one usable mon is an immediate loss, and losing resets the whole dungeon.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import _navigate_riding_out, reraise_if_aborting
    from modules.story.mossdeep_gym import _usable_pokemon

    usable = _usable_pokemon()
    if usable < 2:
        raise BotModeError(
            f"Seafloor Cavern: Room 3's unavoidable DOUBLE battle at {ROOM3_SIGHT_TILE} needs at "
            f"least 2 Pokémon able to fight; the party has {usable}. Losing here resets the entire "
            f"dungeon, so this refuses rather than trying."
        )

    try:
        yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM3, ROOM3_EXIT)
    except Exception as error:  # noqa: BLE001 - the (8,1) door firing mid-walk legitimately raises
        reraise_if_aborting(error)
        if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM8):
            # ⛔ A door firing mid-walk is benign; anything else (an unreachable destination) is NOT.
            raise

    if not _at(MapRSE.SEAFLOOR_CAVERN_ROOM8, ROOM8_ARRIVAL):
        raise BotModeError(
            f"Seafloor Cavern: crossed Room 3 but did not arrive at ROOM8 {ROOM8_ARRIVAL} — "
            f"at {_where()}."
        )
    context.message = f"Story: Seafloor Cavern ROOM8 at {ROOM8_ARRIVAL} — the boulder room."


def _recover_room8_jam() -> Generator:
    """Un-jam Room 8 by LEAVING and RE-ENTERING, which respawns all twelve boulders.

    From the driven `_recover_room8_jam` (`story_harness.py:8081-8135`), exercised for real by a
    fault-injected run (`recovered=True attempts=2`), not merely written.

    ⛔ EXIT AND RE-ENTER IS THE ONLY RECOVERY. NEVER improvise pushes near `(5,3)` to "clear" a jam —
    that is the tile which permanently seals the `(5,2)` door.
    ‼ The retreat tile `(5,12)` is a SOUTH ARROW WARP, and an arrow warp needs a HELD direction: it
    is not a pathfinding destination. The direction is DERIVED FROM THE TILE'S OWN NAME, never
    hardcoded — an earlier version hardcoded "Down" and review caught it, then the fault run showed
    the warp can fire during the navigate itself, which a hardcode would have handled blindly.
    """
    from modules.map import get_map_data_for_current_position
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import (
        _navigate_riding_out,
        _walk_through_warp,
        reraise_if_aborting,
    )

    COMPASS = {"North": "Up", "South": "Down", "East": "Right", "West": "Left"}

    try:
        yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM8, ROOM8_RETREAT)
    except Exception as error:  # noqa: BLE001 - the arrow warp can fire during the navigate itself
        reraise_if_aborting(error)

    if _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM8):
        tile = get_map_data_for_current_position()
        kind = getattr(tile, "tile_type", "") or ""
        # ⛔ GATE on the tile actually being an arrow warp, rather than scanning for a compass word
        # anywhere in the name — a substring scan would fire on unrelated tile types.
        if kind.endswith(" Arrow Warp"):
            direction = next((COMPASS[w] for w in COMPASS if w in kind), None)
            if direction is None:
                raise BotModeError(
                    f"Seafloor Cavern: {ROOM8_RETREAT} reads {kind!r} — an arrow warp with no "
                    f"compass word in its name. Refusing to guess a direction."
                )
            yield from _walk_through_warp(direction, MapRSE.SEAFLOOR_CAVERN_ROOM8.value)

    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM3):
        raise BotModeError(
            f"Seafloor Cavern: jam recovery could not retreat from Room 8 to Room 3 — at {_where()}."
        )
    yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM3, ROOM3_EXIT)
    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM8):
        raise BotModeError(
            f"Seafloor Cavern: jam recovery retreated but could not re-enter Room 8 — at {_where()}."
        )
    context.message = "Story: Seafloor Cavern — re-entered Room 8; boulders respawned."


def solve_room8() -> Generator:
    """Room 8: NINE Strength pushes, then out through the (5,2) door to Room 9. ONE retry.

    From the driven `_solve_room8` (`story_harness.py:8137-8230`), which executed `attempts=1`,
    `exit_ok=True`, and whose jam handler was separately proven by fault injection.

    ⛔⛔ THIS IS THE ROOM WHERE A MISTAKE IS PERMANENT. Push 9 faces **LEFT**. Facing Up puts a
    boulder on `(5,3)` and seals the `(5,2)` door to Room 9 for the rest of the run, with no
    recovery but a reset — which is why this leg CHECKS `(5,3)` explicitly after the pushes rather
    than trusting the sequence.
    ⛔ DO NOT REORDER, DEDUPE OR "OPTIMISE" `ROOM8_PUSHES`. Push 6 must precede push 9 because it
    vacates `(4,4)`, which is push 9's destination; a reordered variant was fault-tested and
    correctly refused. The two rows that share approach `(5,5)` with opposite facings are
    deliberate, not a duplication to clean up.
    ⛔ The staging walk crosses the one-way `Jump South` ledge row at `(4,10)(5,10)(6,10)` — the
    planner routes around it at x=3 or x=7. NEVER hardcode a waypoint through there.
    """
    from modules.map import get_map_objects
    from modules.map_data import MapRSE
    from modules.map_path import PathFindingError, calculate_path
    from modules.modes import BotModeError
    from modules.player import get_player_avatar
    from modules.story.early_game import (
        StoryAbort,
        _check_abort,
        _navigate_riding_out,
        reraise_if_aborting,
        strength_push,
    )

    ROOM8 = MapRSE.SEAFLOOR_CAVERN_ROOM8

    for attempt in (1, 2):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try
        jam = None

        yield from _navigate_riding_out(ROOM8, ROOM8_STAGING)
        # ‼ Assert by ARRIVING, never by inspecting the plan: a plan that says it can get there is
        # not the same fact as standing on the tile.
        if not _at(ROOM8, ROOM8_STAGING):
            jam = f"never reached the staging tile {ROOM8_STAGING} (at {_where()})"
        else:
            for index, (approach, face) in enumerate(ROOM8_PUSHES, 1):
                _check_abort()  # ⛔ FIRST statement, OUTSIDE any try
                try:
                    yield from strength_push(ROOM8, approach, face)
                except StoryAbort:
                    raise  # a whiteout is never a jam — KI-67, do not convert it into one
                except Exception as error:  # noqa: BLE001 - A PUSH FAILURE IS A JAM, NOT A FATALITY
                    # ⛔ THIS TRY/EXCEPT IS LOAD-BEARING AND WAS MISSING IN THE FIRST DRAFT. The
                    # driven harness wraps EVERY push (`story_harness.py:8193-8200`), records the
                    # jam and breaks so the recovery below can run. Without it a `strength_push`
                    # that gives up after its 8 tries propagates straight out of this function and
                    # skips `_recover_room8_jam()` entirely — turning the one CHEAP, fault-proven
                    # recovery into a ~25-minute full re-dive. Caught in adversarial review.
                    reraise_if_aborting(error)
                    jam = f"push {index} raised {type(error).__name__}: {str(error)[:120]}"
                    break

        # --- THE SEAL CHECK. Cheap, and the failure it catches is UNRECOVERABLE, so it runs
        # --- whether or not the sequence completed.
        seen = {
            obj.local_id: tuple(obj.current_coords)
            for obj in get_map_objects()
            if tuple(obj.map_group_and_number) == ROOM8.value and "isPlayer" not in obj.flags
        }
        if (5, 3) in seen.values():
            raise BotModeError(
                "Seafloor Cavern: Room 8 is SEALED — a boulder is sitting on (5,3), which blocks the "
                "(5,2) door to Room 9 permanently. This run cannot finish the cavern, and no retry "
                f"can help. (objects: {seen})"
            )

        if jam is None:
            try:
                calculate_path(
                    (ROOM8, tuple(get_player_avatar().local_coordinates)), (ROOM8, ROOM9_DOOR)
                )
                break  # the door is reachable: the room is solved
            except PathFindingError:
                jam = "the sequence completed but the exit path did not open"

        if attempt == 2:
            raise BotModeError(
                f"Seafloor Cavern: Room 8 failed after two attempts (one jam recovery). "
                f"Last jam: {jam}. Objects: {seen}"
            )
        context.message = f"Story: Seafloor Cavern — Room 8 jammed ({jam}); exiting to respawn."
        yield from _recover_room8_jam()

    context.message = "Story: Seafloor Cavern — Room 8 solved; the Room 9 door is reachable."


def _ride_until(label: str, predicate, budget_frames: int) -> Generator:
    """Advance a cutscene until `predicate()` holds, bounded, with a whiteout guard.

    From the driven `_ride_until` (`story_harness.py:8398-8441`).

    ⛔ THE BUTTON IS GATED, NOT MASHED. `A` is pressed ONLY when a printer is actually waiting for
    input; otherwise `B`. An earlier version mashed `A` across a scene seam and re-introduced the
    museum-greeter bug — an adversarial review caught it BEFORE the first run.
    ⛔ THE WHITEOUT GUARD COMPARES MAPS BY ENUM VALUE. See transcription rule A: the harness compares
    map NAME STRINGS, and a verbatim copy here would be always-true on a PERFECT run and print a
    fabricated whiteout signature on the first iteration of every milestone.
    ‼ Losing the Archie fight whites the run out, at which point the WhiteoutListener drops this
    generator entirely — so this guard is for detecting that we ended up somewhere unexpected, not
    for handling the loss. The loss is handled by the chapter's retry loop.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort
    from modules.tasks import is_waiting_for_input

    EXPECTED = (MapRSE.SEAFLOOR_CAVERN_ROOM9.value, MapRSE.ROUTE128.value)
    frames = 0
    while frames < budget_frames:
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try
        if predicate():
            return
        where = _where()
        if isinstance(where, tuple) and where[0] not in EXPECTED:
            raise BotModeError(
                f"Seafloor Cavern: while riding {label!r} the run left the expected maps and is at "
                f"{where}. That usually means the Archie fight was lost and the run whited out."
            )
        context.emulator.press_button("A" if is_waiting_for_input() else "B")
        yield
        frames += 1

    raise BotModeError(
        f"Seafloor Cavern: rode {label!r} for its full budget of {budget_frames} frames without the "
        f"milestone being reached — at {_where()}."
    )


def room9_and_escape() -> Generator:
    """Room 9: wake Kyogre, ride to Route 128, and get OFF the sandbar into open ocean.

    From the driven `Ch20Room9Mode` (`story_harness.py:8463-8623`), `ACCEPTANCE: PASS`.

    ⛔ THE TRIGGER IS `(17,42)`. `(16,42)` is plain floor and fires nothing — upstream's own
    `puzzle_solver.py:457` walks to `(16,42)` and then hands control to a human.
    ⛔ ARRIVING **IS** THE SCENE START: the coord event locks the player on `(17,42)`, so the
    navigate legitimately raises as the lockall takes control. That is not a failure.
    ⛔ THE ESCAPE IS TWO PLAIN NAVIGATES. The docs' phrase "face Down, then Surf" describes the
    OUTCOME; `calculate_path` emits the Surf waypoint itself and `follow_waypoints` executes it.
    Hand-rolling a facing and a button press here is how this leg gets broken.
    ⛔ AND THE LAUNCH TILE IS HAND-PICKED, for the same reason the surfacing tile was: of the
    sandbar ring's surf-entry points, 28 lead into a 41-tile CLOSED LAGOON and 46 into the
    1,766-tile open ocean. The final `calculate_path` to the dive tile is the anti-lagoon proof.
    """
    from modules.map_data import MapRSE
    from modules.map_path import PathFindingError, calculate_path
    from modules.modes import BotModeError
    from modules.player import AvatarFlags, get_player_avatar
    from modules.story.early_game import (
        _navigate_riding_out,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    # --- into Room 9 (this transit appears EXACTLY ONCE in the module) --------------------------
    try:
        yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM8, ROOM9_DOOR)
    except Exception as error:  # noqa: BLE001 - the door firing mid-walk legitimately raises
        reraise_if_aborting(error)
    if not _on_map(MapRSE.SEAFLOOR_CAVERN_ROOM9):
        raise BotModeError(
            f"Seafloor Cavern: took the {ROOM9_DOOR} door but did not land in ROOM9 — at {_where()}."
        )

    # --- the trigger must still be ARMED ------------------------------------------------------
    scs = _var("SEAFLOOR_CAVERN_STATE")
    if scs != 0:
        raise BotModeError(
            f"Seafloor Cavern: the {ROOM9_TRIGGER} coord event is DISARMED "
            f"(SEAFLOOR_CAVERN_STATE reads {scs!r}, and it only fires at 0). Nothing in the game "
            f"ever resets it, so re-diving cannot help — if ROUTE128_STATE is 1, go to Route 128 "
            f"and let its OnFrame scene finish instead."
        )

    try:
        yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM9, ROOM9_TRIGGER)
    except Exception as error:  # noqa: BLE001 - arriving IS the scene start; the lockall raises
        reraise_if_aborting(error)

    # --- ride the two cutscenes ---------------------------------------------------------------
    yield from _ride_until("SCENE -> ROUTE128", lambda: _on_map(MapRSE.ROUTE128), 80000)
    yield from _ride_until("ROUTE128 scene -> control", lambda: _var("ROUTE128_STATE") == 2, 60000)
    yield from wait_until_truly_controllable()

    yield from _escape_the_atoll()


def _escape_the_atoll() -> Generator:
    """Get OFF the sandbar into open ocean, and PROVE it is open ocean.

    ‼ EXTRACTED SO THERE IS EXACTLY ONE COPY. Three callers need it: the end of
    `room9_and_escape()`, and the two resume branches in the orchestrator that handle an
    interruption AFTER `ROUTE128_STATE` reached 2. A second copy would drift, and this walk contains
    the chapter's "and the bot can continue" proof.

    ⛔ TWO PLAIN NAVIGATES, NO MANUAL SURF. The docs' phrase "face Down, then Surf" describes the
    OUTCOME — `calculate_path` emits the Surf waypoint itself and `follow_waypoints` executes it.
    Hand-rolling a facing and a button press here is how this leg gets broken.
    """
    from modules.map_data import MapRSE
    from modules.map_path import PathFindingError, calculate_path
    from modules.modes import BotModeError
    from modules.player import AvatarFlags, get_player_avatar
    from modules.story.early_game import _navigate_riding_out

    yield from _navigate_riding_out(MapRSE.ROUTE128, ESCAPE_STAND)
    yield from _navigate_riding_out(MapRSE.ROUTE128, ESCAPE_WATER)

    avatar = get_player_avatar()
    coords = tuple(avatar.local_coordinates)
    if AvatarFlags.Surfing not in avatar.flags or coords != ESCAPE_WATER:
        raise BotModeError(
            f"Seafloor Cavern: reached ROUTE128_STATE == 2 but did not launch onto {ESCAPE_WATER} — "
            f"at {coords}, surfing={AvatarFlags.Surfing in avatar.flags}. The run is stranded on the "
            f"sandbar, which is walkable but not surfable in any direction."
        )

    # ⛔ ANTI-LAGOON. Pathing to the tile we originally dived from proves we are in the OPEN ocean
    # component and not the 41-tile closed lagoon north of the bar.
    # ‼ WRAPPED DELIBERATELY. `PathFindingError` is a bare `RuntimeError` (`map_path.py`), NOT a
    # `BotModeError` — so an unguarded call would escape the chapter's own `except BotModeError`
    # retry handler entirely and surface as a raw traceback, bypassing attempt tracking. That is,
    # the assertion guarding the worst outcome would itself have been the least well-reported.
    try:
        calculate_path((MapRSE.ROUTE128, coords), (MapRSE.ROUTE128, OCEAN_PROBE))
    except PathFindingError as error:
        raise BotModeError(
            f"Seafloor Cavern: launched onto {coords} but there is NO PATH to the open ocean at "
            f"{OCEAN_PROBE} — the run is in the 41-tile CLOSED LAGOON, not the 1,766-tile ocean. "
            f"({type(error).__name__}: {str(error)[:120]})"
        )
    context.message = "Story: Kyogre is awake and the run is clear of the atoll."


def prepare_for_the_cavern() -> Generator:
    """Heal and check the party BEFORE diving. ⛔ There is no Poké Center inside the cavern.

    Motivated by measurement, not caution: run 3 of the driven chain entered the Archie fight with
    **one mon already fainted and the lead at 96/135**, and the fight is the chain's ONE stochastic
    element (measured 2W/1L). A loss resets the ENTIRE dungeon — every room re-solves, ~25 minutes.
    ⛔ This must happen on the surface. Once you have dived, healing is not available at any point.
    """
    from modules.map_data import PokemonCenter
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import heal_in_pokemon_center
    from modules.story.early_game import _ch14_say, reraise_if_aborting
    from modules.story.mossdeep_gym import _usable_pokemon

    try:
        yield from heal_in_pokemon_center(PokemonCenter.MossdeepCity)
    except Exception as error:  # noqa: BLE001 - a failed heal must not silently become a dive
        reraise_if_aborting(error)
        raise BotModeError(
            f"Seafloor Cavern: could not heal at the Mossdeep Poké Center before diving "
            f"({type(error).__name__}: {str(error)[:120]}). There is no healing inside the cavern, "
            f"and losing to Archie resets the whole dungeon — refusing to dive un-healed."
        )

    usable = _usable_pokemon()
    if usable < 2:
        raise BotModeError(
            f"Seafloor Cavern: only {usable} Pokémon able to battle after healing. Room 3 has an "
            f"unavoidable DOUBLE battle and Room 9 has Archie; refusing to dive."
        )
    _ch14_say(f"Story: Ch20 prepared — healed at Mossdeep, {usable} able to battle.")


def _finish_on_route128() -> Generator:
    """The cavern scene already ran — finish the Route 128 half WITHOUT re-diving.

    ⛔ THIS IS THE ONLY RECOVERY THAT WORKS once the Room 9 trigger has fired. Decomp-verified:
    `VAR_SEAFLOOR_CAVERN_STATE` is 1 and nothing in the game ever resets it, so the `(17,42)` coord
    event is disarmed permanently and another dive can never complete the chapter. What DOES work is
    simply BEING on Route 128 — its ON_FRAME script re-fires at `ROUTE128_STATE == 1` and ends by
    setting the var to 2. See `route128_scene_outstanding` for the citations.
    """
    from modules.map_data import MapRSE
    from modules.story.early_game import (
        _ch14_say,
        _navigate_riding_out,
        wait_until_truly_controllable,
    )

    _ch14_say("Story: Ch20 — the cavern scene already ran; finishing on Route 128 rather than "
              "re-diving (that trigger is disarmed permanently).")
    if not _on_map(MapRSE.ROUTE128):
        yield from _navigate_riding_out(MapRSE.ROUTE128, ESCAPE_WATER)
    yield from _ride_until("ROUTE128 scene -> control", lambda: _var("ROUTE128_STATE") == 2, 60000)
    yield from wait_until_truly_controllable()
    # ⛔ CALL THE SHARED LEG, not a second copy of the two navigates. The first version duplicated
    # them here and therefore skipped BOTH the surfing assert and the anti-lagoon `calculate_path` —
    # i.e. the recovery path could have "succeeded" while leaving the run in the 41-tile closed
    # lagoon, which is the exact stranding this chapter's acceptance exists to rule out.
    yield from _escape_the_atoll()


def do_seafloor_cavern_chapter() -> Generator:
    """§Ch20 — the Seafloor Cavern, end to end: dive, nine rooms, Kyogre, and off the atoll.

    ‼ THE RETRY IS THE `StoryMode.run` LOOP, NOT A LOOP IN HERE (KI-67). `except StoryAbort: raise`
    is deliberate: the abort latch is cleared ONLY by `StoryMode.run`, so catching a whiteout and
    looping would run straight into the next `_check_abort()` and die instantly — one whiteout would
    burn all three attempts in a handful of frames and report three failures, two of them invented.
    Re-raising IS the retry: `run()` clears the latch, rides out the respawn, walks out of the Poké
    Center and re-runs `_play()`, which re-enters this chapter. That path is bounded at 40 recoveries.
    ⚠ AND EACH RETRY IS EXPENSIVE HERE: every room is a `FLAG_TEMP_*` room, so a re-entry re-solves
    Rooms 1-8 from scratch (~25 minutes). That is the cost of the Archie fight's 2W/1L, and it is
    why `prepare_for_the_cavern()` runs first.
    """
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import (
        StoryAbort,
        _ch14_say,
        _check_abort,
        _navigate_riding_out,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    if seafloor_cavern_done():
        return  # resume-safe

    # ⛔ THE RESUME BRANCH — DECOMP-VERIFIED, AND IT IS *NOT* "RE-DIVE". If the cavern scene already
    # ran, `SEAFLOOR_CAVERN_STATE` is 1 and NOTHING in the game ever resets it, so the (17,42)
    # trigger is disarmed permanently and another dive can never finish the chapter. What DOES work
    # is simply being on Route 128: its ON_FRAME script re-fires at `ROUTE128_STATE == 1` and ends
    # by setting the var to 2. See `route128_scene_outstanding`.
    if route128_scene_outstanding():
        yield from _finish_on_route128()
        if seafloor_cavern_done():
            _ch14_say("Story: Ch20 complete — recovered without re-diving.")
            return
    if escape_outstanding():
        _ch14_say("Story: Ch20 — resuming: only the atoll escape is left.")
        yield from _escape_the_atoll()
        if seafloor_cavern_done():
            _ch14_say("Story: Ch20 complete — escaped without re-diving.")
            return

    assert_cavern_preflight()

    attempts = []
    for attempt in range(1, 4):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE the try below
        try:
            # ⛔ RE-CHECKED EVERY ATTEMPT, NOT ONCE BEFORE THE LOOP. If a previous attempt failed
            # AFTER the Room 9 trigger fired, `SEAFLOOR_CAVERN_STATE` is already 1 and the trigger
            # is disarmed FOREVER — so re-diving is guaranteed to fail at the arm check, ~25 minutes
            # later. Without this line a single transient timeout after the trigger burns all three
            # attempts on runs that cannot possibly succeed. Caught in adversarial review.
            if route128_scene_outstanding():
                yield from _finish_on_route128()
                if seafloor_cavern_done():
                    _ch14_say("Story: Ch20 complete — finished on Route 128 without re-diving.")
                    return
            # ⛔ AND the narrower window: the scene is DONE (var 2) but we are still on the sandbar.
            # Re-diving here is pure waste — the trigger is disarmed. Just finish the walk.
            if escape_outstanding():
                _ch14_say("Story: Ch20 — scene already complete; only the atoll escape is left.")
                yield from _escape_the_atoll()
                if seafloor_cavern_done():
                    _ch14_say("Story: Ch20 complete — escaped without re-diving.")
                    return

            yield from prepare_for_the_cavern()
            yield from dive_into_the_cavern()
            yield from enter_room1()
            yield from solve_room1()
            yield from solve_room2()
            yield from cross_room6()
            yield from cross_room3()
            yield from solve_room8()
            yield from room9_and_escape()
        except StoryAbort:
            # ‼‼ NEVER RETRY IN PLACE AFTER A WHITEOUT (KI-67) — see this function's docstring.
            raise
        except BotModeError as error:  # noqa: BLE001 - NOT swallowed; every reason is kept and
            # raised together below if all three attempts fail. A whiteout losing to Archie is an
            # EXPECTED outcome of this chapter, not an anomaly.
            reraise_if_aborting(error)
            attempts.append(f"attempt {attempt}: {str(error)[:200]}")
            _ch14_say(f"Story: Ch20 attempt {attempt} failed — {str(error)[:120]}")
            continue

        if seafloor_cavern_done():
            _ch14_say("Story: Ch20 complete — Kyogre is awake, and the run is off the atoll in "
                      "open ocean.")
            return
        attempts.append(f"attempt {attempt}: legs finished but the chapter did not grade done")

    raise BotModeError(
        "Seafloor Cavern: failed after 3 attempts. " + " | ".join(attempts)
    )
