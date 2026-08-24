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
