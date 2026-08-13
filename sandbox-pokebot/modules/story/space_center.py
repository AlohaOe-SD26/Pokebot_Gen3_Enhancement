"""§Ch19 — the Mossdeep Space Center: Team Magma's raid, and Steven's multi battle.

‼‼ GROUNDWORK ONLY — NOT WIRED INTO THE LADDER, AND NOT YET DRIVEN. What is here is the route and
the sequence, built from decomp research and from coordinates measured in our own ROM. What is
MISSING is the end of the beat: Steven's two talks, the party-selection menu, and the multi battle.
Do not add it to `story_mode.py` until those exist and the whole thing has a driven PASS.

SEQUENCE (decomp-sourced, coordinates measured from our own ROM by `probe_space_center_recon.py`):
  1. Mossdeep City — a FORCED cutscene. Six coord_event tiles (42,21) (41,22) (41,23) (41,24)
     (40,25) (40,26) run `MossdeepCity_EventScript_TeamMagmaEnterSpaceCenter`, in which Maxie and
     four grunts walk into the Space Center. ‼ It is unavoidable by construction: those six tiles
     are the only crossing to the Space Center door. It ends `VAR_MOSSDEEP_CITY_STATE = 2`.
  2. Enter 1F at the door `MOSSDEEP_CITY (64,15)` -> `SPACE_CENTER_1F (7,9)`.
  3. Cross 1F. Four grunts; only two matter. **Grunt 4 at (10,2)** watches the only walkable
     crossing of column x=10, so its battle is forced by geometry. **Grunt 2 at (13,2)** stands ON
     the only tile that reaches the stairs and must be TALKED to; beating it makes it step aside.
  4. Stairs `1F (13,1)` -> `2F (13,1)`.
  5. ‼ 2F fires an ON_FRAME script the instant the player is controllable — no coordinate
     condition — with a YES/NO box. Answering NO warps back to 1F with the var UNCHANGED, so it is
     a retry loop rather than an escape. YES chains three grunt battles back to back.
  6. Walk to Steven at (1,8) and talk TWICE. The first talk is DIALOGUE ONLY and sets
     `FLAG_INTERACTED_WITH_STEVEN_SPACE_CENTER`; a bot that waits for a battle here will hang.
     ‼ Leaving and re-entering 2F CLEARS that flag again (`EventScript_MoveCivilians` runs on every
     transition while `VAR_MOSSDEEP_CITY_STATE == 2`), so the two talks must happen in one visit.
  7. The second talk asks YES/NO and then opens a PARTY-SELECTION menu
     (`ChooseHalfPartyForBattle`, 1..3 Pokémon). Those are the only Pokémon fielded, with Steven's
     Metang 42 / Skarmory 43 / Aggron 44 as the ally, against Tabitha (36-40) and Maxie (42-44).

‼ THE COMPLETION MARKER IS `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3`, and the obvious alternative is a
TRAP. `FLAG_DEFEATED_MAGMA_SPACE_CENTER` looks like the natural "did we win" flag and is set by the
same script — but it is **not durable**: `ShouldDoRivalRayquazaCall` uses it as a step-counter gate
and `EventScript_RivalRayquazaCall` CLEARS it once the PokéNav call fires, roughly 250 steps later
on any town/route map. A chapter graded on it would pass, then silently un-pass. The var is written
once (0 -> 1 by the gym, 1 -> 2 after the three grunts, 2 -> 3 after Maxie) and never read again
once it reaches 3.

‼ AN AMBIENT INTERRUPTION THIS BEAT CREATES FOR EVERYONE ELSE: once
`FLAG_DEFEATED_MAGMA_SPACE_CENTER` is set, a `lockall` + `pokenavcall` Rayquaza scene can fire after
~250 steps on ANY town/city/route map — including mid-Surf, in a later chapter. Anything walking a
long way after this beat must be able to ride out an unexpected scene.
"""

from typing import Generator

from modules.context import context
from modules.map_data import MapRSE

#: Where the player ends up after the whole beat. Written once and never read again at 3.
STATE_VAR = "MOSSDEEP_SPACE_CENTER_STATE"
DONE_STATE = 3

#: Measured from our ROM (`probe_space_center_recon.py`), not recalled.
CITY = MapRSE.MOSSDEEP_CITY
FLOOR_1F = MapRSE.MOSSDEEP_CITY_SPACE_CENTER_1F
FLOOR_2F = MapRSE.MOSSDEEP_CITY_SPACE_CENTER_2F
STEVENS_HOUSE = MapRSE.MOSSDEEP_CITY_STEVENS_HOUSE

SPACE_CENTER_DOOR = (64, 15)      #: city tile; stand on (64,16) and press Up
SPACE_CENTER_DOOR_APPROACH = (64, 16)
STAIRS_1F = (13, 1)               #: reachable ONLY from (13,2), which Grunt 2 occupies
STAIRS_APPROACH_1F = (13, 2)
STEVEN_TILE_2F = (1, 8)
STEVEN_APPROACHES_2F = [((1, 7), "Down"), ((2, 8), "Left")]
STEVENS_HOUSE_DOOR = (19, 10)

#: Bounded rides. Every one of these is a BOUND, never a `while True`.
SCENE_TIMEOUT_FRAMES = 30_000
BATTLE_TIMEOUT_FRAMES = 60_000


def _tile() -> tuple[int, int]:
    from modules.player import get_player_avatar

    return tuple(get_player_avatar().local_coordinates)


def _map() -> tuple[int, int]:
    from modules.player import get_player_avatar

    return tuple(get_player_avatar().map_group_and_number)


def space_center_done() -> bool:
    """‼ Graded on the VAR, not on `FLAG_DEFEATED_MAGMA_SPACE_CENTER` — see the module docstring."""
    from modules.memory import get_event_var

    return get_event_var(STATE_VAR) >= DONE_STATE


def dive_received() -> bool:
    from modules.memory import get_event_flag

    return get_event_flag("RECEIVED_HM_DIVE")


def _mash_until(predicate, label: str, *, timeout: int = SCENE_TIMEOUT_FRAMES,
                accept: bool = False) -> Generator:
    """Press until `predicate()` is true, and report WHERE we were if it never becomes true.

    ‼‼ `accept=True` PRESSES **A ONLY**, AND ON THIS MAP THAT IS NOT A STYLE CHOICE. The story
    idiom elsewhere is two B presses to every A, which advances text cheaply. On Space Center 2F it
    would livelock the run: the ON_FRAME script opens a **MSGBOX_YESNO**, and B answers NO — which
    walks the player up one tile and warps them back to 1F **without changing
    `VAR_MOSSDEEP_SPACE_CENTER_STATE`**. Walking back up re-fires the same trigger. Enter, decline,
    get warped out, re-enter, forever: a healthy controllable avatar, no error, no flag movement.

    This is the playbook's own named bug ("a story scene contains a YES/NO ridden with raw B, which
    DECLINES the choice forever"), and it was predicted for this exact scene by an adversarial pass
    BEFORE the code was written — which is the only reason it is not in the mistakes log instead.

    ‼ BOUNDED, always. A wait loop with no ceiling is this project's most repeated bug shape."""
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort

    frames = 0
    while not predicate():
        _check_abort()
        if frames > timeout:
            raise BotModeError(
                f"Space Center: {label} did not complete within {frames} frames "
                f"(map {_map()} tile {_tile()})."
            )
        context.emulator.press_button("A" if accept or frames % 3 == 0 else "B")
        frames += 1
        yield
    return


#: The six coord_event tiles that run `MossdeepCity_EventScript_TeamMagmaEnterSpaceCenter`.
#: Read from `data/maps/MossdeepCity/map.json`; all six are gated `var_value: 1`, i.e. they only
#: fire while `VAR_MOSSDEEP_CITY_STATE == 1` (which the gym victory sets).
CUTSCENE_TRIGGER_TILES = [(42, 21), (41, 22), (41, 23), (41, 24), (40, 25), (40, 26)]

CITY_STATE_VAR = "MOSSDEEP_CITY_STATE"
CITY_STATE_AFTER_CUTSCENE = 2


def walk_into_the_space_center() -> Generator:
    """Heal, ride the forced Team Magma cutscene, and only THEN walk to the Space Center door.

    ‼‼ THIS IS TWO LEGS, AND THE FIRST DRIVEN RUN PROVED WHY. The original version navigated
    straight to the door approach (64,16) in one call, on the reasoning that the walk "crosses the
    cutscene trigger tiles by construction". It does not, and it cannot:

        [ch19a] FAILED: UnreachableDestinationError: Could not reach (64,16) on MOSSDEEP_CITY:
        the field is idle and we are still at (28,17)  (Could not find a path from (28/17) to (64/16))

    MEASURED CAUSE (`probe_ch19_route.py`, 2026-08-12): the gym victory SPAWNS five Team Magma NPCs
    that stand on the only land bridge — four grunts at (44,23)..(44,26) and Maxie at (45,25) — and
    our planner blocks every loaded object's tile (`map_path.py:710-717`). So the door is in a
    different connected component from the player and NO route exists until they leave.
    ‼ Under a collision-only model the door approach IS reachable, which is exactly how this looked
    at first like KI-59 (our planner over-blocking `Impassable *`). It is not. The planner is RIGHT;
    the wall is the NPCs, and the story's own answer is the cutscene. The probe now models the live
    objects so it cannot tell that lie twice.

    THE ROUTE, THEREFORE: heal → walk to the trigger line (pathable: 21-26 waypoints, measured) →
    ride the scene, which `removeobject`s all five and sets `VAR_MOSSDEEP_CITY_STATE = 2` → and only
    now plan to the door, because only now does a path exist.

    ‼ HEAL FIRST, AND IT IS NOT ONLY ABOUT HP. The anchor arrives at 66% with one Pokémon fainted
    (the §Ch16 lesson). But entering the Mossdeep Pokémon Center also runs `setrespawn` on its
    ON_TRANSITION, and the anchor's `lastHealLocation` is measured to be **LILYCOVE CITY** — across
    the sea, with no Fly user in the party. Losing Steven's battle warps the run to the last heal
    location, so healing here is what turns a loss from a cross-ocean disaster into a short walk.
    """
    from modules.map_data import PokemonCenter
    from modules.memory import get_event_var
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import heal_in_pokemon_center
    from modules.story.early_game import (
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        _ride_out_all_scenes,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    if _map() == FLOOR_1F.value or _map() == FLOOR_2F.value:
        return  # resume-safe: already inside the building

    _ch14_say("Story: Ch19 healing at Mossdeep (this also moves the respawn off Lilycove)...")
    yield from _navigate_riding_out(CITY, (28, 17))
    yield from heal_in_pokemon_center(PokemonCenter.MossdeepCity)
    yield from wait_until_truly_controllable()

    # --- leg 1a: the cutscene ------------------------------------------------------------------
    if get_event_var(CITY_STATE_VAR) < CITY_STATE_AFTER_CUTSCENE:
        _ch14_say("Story: Ch19 walking to the Team Magma cutscene trigger line...")
        reasons = []
        for trigger in CUTSCENE_TRIGGER_TILES:
            try:
                yield from _navigate_riding_out(CITY, trigger, tries=8)
            except BotModeError as error:  # noqa: BLE001 - NOT swallowed: six tiles fire the same
                # scene, so one being unreachable is an expected outcome of trying them in order.
                # Every reason is kept and raised together if none of them works.
                # ‼ EXCEPT A WHITEOUT. Without this guard the loop swallowed the abort six times
                # and then raised the message below — "the Team Magma NPCs are still standing on
                # the land bridge" — which after a whiteout is a FABRICATED diagnosis: the NPCs are
                # irrelevant and the player is outside a Pokémon Center. A laundered abort is worse
                # than a swallowed one, because it hands the next reader a confident wrong cause.
                reraise_if_aborting(error)
                reasons.append(f"{trigger}: {str(error)[:90]}")
                continue
            # Landing on the tile IS the action - the coord_event fires as the player steps on.
            yield from _ride_out_all_scenes()
            yield from wait_until_truly_controllable()
            if get_event_var(CITY_STATE_VAR) >= CITY_STATE_AFTER_CUTSCENE:
                break

        # ‼ ASSERT THE SCENE ACTUALLY RAN, rather than assuming a walk implies a cutscene. If the
        # var never moved, the five NPCs are still on the bridge and the next navigation would fail
        # far from its cause with an unrelated-looking "no path".
        state = get_event_var(CITY_STATE_VAR)
        if state < CITY_STATE_AFTER_CUTSCENE:
            raise BotModeError(
                f"Space Center: rode the trigger line but {CITY_STATE_VAR} is still {state} "
                f"(expected >= {CITY_STATE_AFTER_CUTSCENE}). The Team Magma NPCs are therefore "
                f"still standing on the only land bridge at x=44, y=23-26, and no route to the "
                f"Space Center door can exist. Tried: {'; '.join(reasons) or 'all six tiles'}."
            )
        _ch14_say(f"Story: Ch19 cutscene done, {CITY_STATE_VAR}={state} — the bridge is clear")

    # --- leg 1b: now, and only now, the door ---------------------------------------------------
    _ch14_say("Story: Ch19 crossing to the Space Center door")
    yield from _navigate_riding_out(CITY, SPACE_CENTER_DOOR_APPROACH, tries=12)
    yield from wait_until_truly_controllable()

    def inside() -> bool:
        return _map() == FLOOR_1F.value

    yield from _enter_warp_by_navigation(inside, CITY, SPACE_CENTER_DOOR, label="Space Center door")
    yield from wait_until_truly_controllable()
    _ch14_say(f"Story: Ch19 inside the Space Center at {_tile()}")


#: Free tiles from which the stair grunt at (13,2) can be face-tapped, with the direction to face.
#: Tried in order; the first one we can actually reach wins.
STAIR_GRUNT_TILE = (13, 2)
STAIR_GRUNT_APPROACHES = [((12, 2), "Right"), ((13, 3), "Up"), ((14, 2), "Left")]

#: Bounded ride for one talked-to trainer battle plus its aftermath.
TALK_BATTLE_TIMEOUT_FRAMES = 40_000


def _npc_is_on(map_enum, tile: tuple[int, int]) -> bool:
    """Is a LIVE object standing on `tile` right now?

    ‼ `get_map_objects()` is the only view of MUTATED positions and it only covers LOADED objects;
    `MapLocation.objects` reads the ROM header and always returns ORIGINAL positions. Mixing those
    two up is where most of this project's wrong conclusions about rooms have come from, so this
    says which one it uses: the live one."""
    from modules.map import get_map_objects
    from modules.player import get_player_avatar

    if tuple(get_player_avatar().map_group_and_number) != map_enum.value:
        return False
    try:
        return any(
            tuple(obj.current_coords) == tile
            for obj in get_map_objects()
            if "isPlayer" not in obj.flags
        )
    except Exception:  # noqa: BLE001 - an unreadable object list must not be read as "it moved"
        return True


def _talk_to_the_stair_grunt() -> Generator:
    """Walk beside the grunt plugging the stairs, face it, and start its battle.

    ‼‼ THIS LEG EXISTS BECAUSE NAVIGATING TO ITS TILE IS IMPOSSIBLE, NOT MERELY SLOW. The original
    `cross_first_floor` did `_navigate_riding_out(FLOOR_1F, (13,2))` — the tile the grunt is
    STANDING ON. Our planner blocks every loaded object's current and previous tile
    (`map_path.py:710-717`, `is_tile_accessible` -> False), so that destination can never be
    reached: `PathFindingError` -> `BotModeError` -> `_navigate_riding_out`'s fail-fast fires on
    try 2 ("the field is idle and we are still at ...") and the `tries=14` budget is never spent.

    ‼ AND IT WOULD NEVER HAVE FIXED ITSELF BY WAITING. This grunt has `sight_radius = 0` and its
    script opens `lock` / `faceplayer` — it is an INTERACTION trainer, not a sight trainer. Nothing
    happens until the player deliberately talks to it. The module's own docstring said "must be
    TALKED to" while no code talked to it; that is the gap this closes.

    ‼ ONLY FACE-TAP A TILE THE NPC ACTUALLY OCCUPIES, and re-verify before pressing. A face-tap
    toward an EMPTY tile STEPS the player when they already face that way — the playbook's rule —
    which here would walk us onto the stairs approach out of sequence."""
    from modules.modes import BotModeError
    from modules.modes.util.walking import ensure_facing_direction
    from modules.story.early_game import (
        _ch14_say,
        _navigate_riding_out,
        _ride_out_all_scenes,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    if not _npc_is_on(FLOOR_1F, STAIR_GRUNT_TILE):
        _ch14_say("Story: Ch19 the stairs are already clear — no grunt on (13,2)")
        return

    reasons = []
    for approach, facing in STAIR_GRUNT_APPROACHES:
        try:
            yield from _navigate_riding_out(FLOOR_1F, approach, tries=6)
        except BotModeError as error:  # noqa: BLE001 - NOT swallowed: three approaches exist, so
            # one failing is an expected outcome of trying them all. Reasons are raised together.
            # ‼ A whiteout here would otherwise be laundered into "could not clear the grunt
            # plugging the stairs (tried [...])" — a reachability claim about a floor we are no
            # longer standing on.
            reraise_if_aborting(error)
            reasons.append(f"{approach}: {str(error)[:80]}")
            continue

        yield from wait_until_truly_controllable()
        if not _npc_is_on(FLOOR_1F, STAIR_GRUNT_TILE):
            return  # it moved while we walked - nothing left to talk to

        _ch14_say(f"Story: Ch19 talking to the stair grunt from {approach} facing {facing}")
        yield from ensure_facing_direction(facing)
        yield
        context.emulator.press_button("A")
        yield

        # Ride the battle out. Graded on the GRUNT LEAVING ITS TILE, which is the thing the rest of
        # this leg depends on - not on "a battle happened", which a lost battle also satisfies.
        for frames in range(TALK_BATTLE_TIMEOUT_FRAMES):
            from modules.story.early_game import _check_abort

            _check_abort()
            if frames % 120 == 0 and not _on_1f():
                break  # a whiteout carried us off the map; the caller re-checks and recovers
            context.emulator.press_button("B" if frames % 3 else "A")
            yield
            if frames > 240 and not _npc_is_on(FLOOR_1F, STAIR_GRUNT_TILE):
                break

        yield from _ride_out_all_scenes()
        yield from wait_until_truly_controllable()

        # ‼‼ "THE GRUNT IS NOT THERE" AND "WE ARE NOT THERE" ARE DIFFERENT ANSWERS, and
        # `_npc_is_on` returns False for BOTH — it reports False whenever the player is off the
        # given map. Testing it alone meant a WHITEOUT during this battle logged "the stair grunt
        # has stepped aside" while the avatar stood outside the Mossdeep Pokémon Center; the caller
        # then navigated to (13,2), which the still-undefeated grunt still occupies, and failed with
        # the very "could not reach (13,2)" error this module's docstring warns names the wrong
        # problem. `clear_the_three_grunts` already got this right (`done_or_gone`); this leg did not.
        if not _on_1f():
            raise BotModeError(
                f"Space Center 1F: left the floor while fighting the stair grunt (now on {_map()} "
                f"at {_tile()}) — almost certainly a WHITEOUT. The grunt is undefeated and still "
                f"plugs {STAIR_GRUNT_TILE}, so the chapter must re-enter and talk to it again."
            )
        if not _npc_is_on(FLOOR_1F, STAIR_GRUNT_TILE):
            _ch14_say("Story: Ch19 the stair grunt has stepped aside")
            return
        reasons.append(f"{approach}: talked, but the grunt is still on {STAIR_GRUNT_TILE}")

    raise BotModeError(
        f"Space Center 1F: could not clear the grunt plugging the stairs at {STAIR_GRUNT_TILE}. "
        f"It has sight_radius 0, so it NEVER starts its own battle — it must be talked to, and "
        f"(13,2) is the only tile the stairs at (13,1) can be reached from. Tried "
        f"{[a for a, _ in STAIR_GRUNT_APPROACHES]}: {'; '.join(reasons)}"
    )


def _on_1f() -> bool:
    return _map() == FLOOR_1F.value


def cross_first_floor() -> Generator:
    """Reach 2F. The 1F grunts are unavoidable, and for TWO DIFFERENT REASONS that need two answers.

    ‼ SIGHT grunts fire by themselves — walking across the floor is enough, and `_navigate_riding_out`
    exists to be interrupted by exactly that. ‼ The STAIR grunt does NOT: `sight_radius = 0`, and it
    stands on (13,2), the only tile from which the stairs at (13,1) are reachable. It must be TALKED
    to, which is `_talk_to_the_stair_grunt`.

    ‼ HOW MANY SIGHT BATTLES THERE ARE IS NOT ASSERTED HERE. The groundwork claimed "four grunts;
    only two matter", resting the route on sight geometry — but the area atlas
    (`probe_space_center_recon.py`) does not print `trainer_sight_or_berry_tree_id` at all, so that
    claim was never measured, and an adversarial pass reads the map.json as up to FOUR forced
    fights. This leg therefore does not depend on the count: it rides out whatever fires and is
    graded on ARRIVING ON 2F."""
    from modules.story.early_game import (
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        wait_until_truly_controllable,
    )

    if _map() == FLOOR_2F.value:
        return  # resume-safe

    _ch14_say("Story: Ch19 crossing 1F — sight grunts fire on their own; the stair grunt must be talked to")
    yield from _talk_to_the_stair_grunt()
    yield from _navigate_riding_out(FLOOR_1F, STAIRS_APPROACH_1F, tries=14)
    yield from wait_until_truly_controllable()

    def upstairs() -> bool:
        return _map() == FLOOR_2F.value

    yield from _enter_warp_by_navigation(upstairs, FLOOR_1F, STAIRS_1F, label="Space Center stairs")
    yield from wait_until_truly_controllable()
    _ch14_say(f"Story: Ch19 reached 2F at {_tile()}")


def clear_the_three_grunts() -> Generator:
    """Answer the 2F prompt and fight the three grunts it chains.

    ‼ THE PROMPT FIRES BEFORE THE PLAYER CAN MOVE. `MossdeepCity_SpaceCenter_2F_OnFrame` has no
    coordinate condition, so it triggers on the first controllable frame on 2F. Answering NO walks
    the player up and warps them back to 1F with `VAR_MOSSDEEP_SPACE_CENTER_STATE` unchanged — that
    is a retry loop, not an exit, so the only way forward is YES.

    Graded on the var reaching 2, which the script writes after the third battle."""
    from modules.memory import get_event_var
    from modules.story.early_game import _ch14_say, wait_until_truly_controllable

    # ‼ THE `>= 2` EARLY RETURN IS RESUME-CORRECT AND MUST NOT BE "HARDENED" AWAY. The ON_FRAME is
    # `map_script_2 VAR_MOSSDEEP_SPACE_CENTER_STATE, 1`, i.e. gated on the var being EXACTLY 1, so
    # once it reaches 2 the prompt genuinely never fires again and waiting for it would hang.
    if get_event_var(STATE_VAR) >= 2:
        return  # resume-safe

    from modules.modes import BotModeError

    _ch14_say("Story: Ch19 answering the 2F prompt and fighting the three grunts...")

    # ‼ BAIL IF WE LEAVE 2F, don't just wait for the var. Two different things take us off this
    # floor and BOTH used to be invisible to this loop: answering the prompt NO warps the player to
    # 1F (13,1) with the var unchanged, and losing any of the three grunt battles whites out. In
    # either case the old predicate ("var >= 2") stays false, so the loop kept A-mashing — on a
    # different map — for its entire 60,000-frame budget before reporting a timeout that named the
    # wrong problem. Ending on the transition means the caller re-enters and re-tries, which is the
    # behaviour the script itself is built for.
    def done_or_gone() -> bool:
        return get_event_var(STATE_VAR) >= 2 or _map() != FLOOR_2F.value

    yield from _mash_until(
        done_or_gone,
        "the three-grunt gauntlet",
        timeout=BATTLE_TIMEOUT_FRAMES,
        accept=True,   # ‼ A ONLY - B answers NO here and warps us out. See `_mash_until`.
    )
    yield from wait_until_truly_controllable()

    state = get_event_var(STATE_VAR)
    if state < 2:
        raise BotModeError(
            f"Space Center 2F: left the floor with {STATE_VAR}={state} (now on {_map()} at "
            f"{_tile()}). Either the YES/NO was answered NO — which warps to 1F (13,1) and leaves "
            "the var untouched — or a grunt battle was lost. Both are retryable by re-entering 2F."
        )
    _ch14_say(f"Story: Ch19 three grunts done, {STATE_VAR}={state}")


# =================================================================================================
# LEG 5 — Steven's two talks, the party-selection menu, and the multi battle.
# =================================================================================================

STEVEN_FLAG = "INTERACTED_WITH_STEVEN_SPACE_CENTER"

#: Cursor slot ids inside the party menu. 0..5 are the party; `PARTY_SIZE` is CONFIRM and
#: `PARTY_SIZE + 1` is CANCEL (`src/party_menu.c`, comment at :1525). Reading 6 as "a seventh
#: Pokémon" is the KI-38 shape and would send the run into CANCEL.
PARTY_SIZE = 6
CURSOR_CONFIRM = PARTY_SIZE
CURSOR_CANCEL = PARTY_SIZE + 1

#: The multi battle fields at most three (`MULTI_PARTY_SIZE`). `GetMinBattleEntries()` returns 1
#: for this facility, so fewer is legal — but see `choose_battle_party` for why fewer is a trap.
MAX_BATTLE_ENTRIES = 3

MENU_STEP_FRAMES = 240
MENU_TOTAL_FRAMES = 6_000


def _selected_order() -> list[int]:
    """`gSelectedOrderFromParty` — the chosen party slots, stored as `slot + 1`, 0 meaning empty.

    ‼ THIS IS WHY THIS MENU CAN BE DRIVEN HONESTLY RATHER THAN MASHED. It is the game's own record
    of what has been picked, so every press can be CONFIRMED to have had the intended effect
    instead of assumed. Blind A-mashing here does not merely risk a wrong pick — it cannot work at
    all: A on an already-chosen mon opens `ACTIONS_NO_ENTRY`, whose first item DESELECTS it, so
    A-mash toggles one slot on and off forever with a healthy screen and no error."""
    from modules.memory import read_symbol

    return list(read_symbol("gSelectedOrderFromParty")[:4])


def _party_menu_open() -> bool:
    from modules.memory import GameState, get_game_state

    return get_game_state() == GameState.PARTY_MENU


def _cursor() -> int:
    from modules.menuing import get_current_party_menu_index

    return get_current_party_menu_index()


def battle_party_slots() -> list[int]:
    """The up-to-three party slots to field, strongest first.

    ‼ ALWAYS BRING THE MAXIMUM. `Cmd_checkteamslost` has an explicit special case for this fight:
    for `TRAINER_STEVEN_PARTNER` it sums HP over `gPlayerParty[0..2]` ONLY — the player's own picks
    — and declares the battle LOST the moment that total hits zero, no matter how healthy Steven
    still is. So "bring fewer and let the ally carry it" is exactly backwards; every mon left
    behind is a life removed from the loss condition.

    ‼ ELIGIBILITY IS THE GAME'S, NOT OURS. `GetBattleEntryEligibility` accepts a mon iff it is not
    an egg and its HP is not 0. Offering the cursor a fainted mon is worse than useless: its submenu
    is `ACTIONS_SUMMARY_ONLY`, whose FIRST item is SUMMARY, so the standard two-A pick would open
    the summary screen — a scene nothing here is prepared for."""
    from modules.pokemon_party import get_party

    eligible = [
        (index, mon)
        for index, mon in enumerate(get_party())
        if mon is not None and not mon.is_egg and mon.species is not None and mon.current_hp > 0
    ]
    eligible.sort(key=lambda pair: (-pair[1].level, -pair[1].current_hp))
    return [index for index, _mon in eligible[:MAX_BATTLE_ENTRIES]]


def _move_cursor_to(target: int) -> Generator:
    """Step the party-menu cursor onto `target`, reading it every iteration.

    ‼ NEVER COUNT PRESSES. `gPartyMenu[9]` is not a plain party index (KI-38 measured
    `cursors_seen = [0, 2, 3, 7]` on a four-mon party), and this menu adds CONFIRM and CANCEL on
    top of that. So this presses one step, re-reads, and stops when the game says it arrived."""
    from modules.modes import BotModeError

    for _ in range(40):
        here = _cursor()
        if here == target:
            return
        context.emulator.press_button("Down" if here < target else "Up")
        for _ in range(8):
            yield
        if _cursor() == here:
            # One nudge in the other direction covers a wrap at the end of the list.
            context.emulator.press_button("Up" if here < target else "Down")
            for _ in range(8):
                yield
    raise BotModeError(
        f"Space Center: could not move the party-menu cursor to slot {target}; it is stuck at "
        f"{_cursor()}. (CONFIRM is {CURSOR_CONFIRM} and CANCEL is {CURSOR_CANCEL} — a cursor that "
        "will not move is usually a menu that is not the one we think it is.)"
    )


def choose_battle_party() -> Generator:
    """Drive `ChooseHalfPartyForBattle`: pick the strongest three, then CONFIRM.

    THE SEQUENCE, from the decomp: A on a mon opens its submenu (cursor already on ENTER for an
    eligible mon), a second A enters it — and ‼ THE CURSOR DOES NOT ADVANCE, so the next pick must
    move it first. After the THIRD entry the game moves the cursor to CONFIRM by itself
    (`MoveCursorToConfirm`), but it does NOT start the battle: a final A on CONFIRM runs
    `Task_ValidateChosenHalfParty`, and only that closes the menu.

    Every step is verified against `gSelectedOrderFromParty`, so a press that did not land is a
    diagnosable failure rather than a silent wrong party."""
    from modules.modes import BotModeError
    from modules.story.early_game import _ch14_say

    wanted = battle_party_slots()
    if not wanted:
        raise BotModeError(
            "Space Center: the party-selection menu is open but NO party member is eligible "
            "(every one is fainted or an egg). The chapter should have healed before this point."
        )

    from modules.pokemon_party import get_party

    party = get_party()
    names = ", ".join(f"slot {i}={party[i].species.name} L{party[i].level}" for i in wanted)
    _ch14_say(f"Story: Ch19 party-select — bringing {len(wanted)} of {MAX_BATTLE_ENTRIES}: {names}")

    for wanted_slot in wanted:
        before = [v for v in _selected_order() if v]
        yield from _move_cursor_to(wanted_slot)

        landed = False
        for _attempt in range(3):
            context.emulator.press_button("A")          # open the submenu
            for _ in range(MENU_STEP_FRAMES // 8):
                yield
            context.emulator.press_button("A")          # ENTER (item 0 for an eligible mon)
            for _ in range(MENU_STEP_FRAMES // 8):
                yield
            after = [v for v in _selected_order() if v]
            if len(after) > len(before):
                landed = True
                break
            # ‼ Do NOT simply press A again. If the count did not rise, the second A may have
            # DESELECTED (ACTIONS_NO_ENTRY) or opened the SUMMARY screen (ACTIONS_SUMMARY_ONLY);
            # B backs out of both before we try once more.
            context.emulator.press_button("B")
            for _ in range(MENU_STEP_FRAMES // 8):
                yield

        if not landed:
            raise BotModeError(
                f"Space Center: pressing ENTER on party slot {wanted_slot} did not add it to "
                f"gSelectedOrderFromParty (still {_selected_order()}). The cursor was "
                f"{_cursor()}. A slot that refuses to enter is normally a fainted/egg mon, whose "
                "submenu offers SUMMARY rather than ENTER."
            )

    chosen = [v - 1 for v in _selected_order() if v]
    _ch14_say(f"Story: Ch19 party-select chose slots {chosen}; confirming")

    yield from _move_cursor_to(CURSOR_CONFIRM)
    for _ in range(20):
        context.emulator.press_button("A")
        for _ in range(12):
            yield
        if not _party_menu_open():
            return
    raise BotModeError(
        f"Space Center: chose slots {chosen} but the party menu did not close after CONFIRM "
        f"(cursor {_cursor()}). ‼ CONFIRM is slot {CURSOR_CONFIRM}; slot {CURSOR_CANCEL} is CANCEL, "
        "which opens a 'Cancel the battle?' YES/NO and loops back to Steven's prompt forever."
    )


def _steven_is_reachable() -> bool:
    from modules.map import get_map_data
    from modules.map_path import calculate_path

    for approach, _facing in STEVEN_APPROACHES_2F:
        try:
            calculate_path(get_map_data(FLOOR_2F, _tile()), get_map_data(FLOOR_2F, approach))
            return True
        except Exception:  # noqa: BLE001 - the question is only "is any approach reachable"
            continue
    return False


def fight_alongside_steven() -> Generator:
    """Talk to Steven TWICE, choose the battle party, and win the multi battle.

    ‼‼ TWICE, IN ONE VISIT, EVERY VISIT. `MossdeepCity_SpaceCenter_2F_OnTransition` calls
    `_MoveCivilians` whenever `VAR_MOSSDEEP_CITY_STATE == 2` — which is this entire beat — and its
    FIRST line is `clearflag FLAG_INTERACTED_WITH_STEVEN_SPACE_CENTER`. So every entry to 2F resets
    the conversation: the first talk is always dialogue only, and only the second opens the
    "are you ready?" prompt. A state machine that talks once and waits for a battle HANGS, and one
    that leaves the floor to heal between the talks starts over without knowing it.

    ‼ LOSING IS NOT AN ERROR, IT IS A RETRY. This battle bypasses the normal defeat plumbing: the
    script inspects the outcome itself and, on anything but a win, calls `SetCB2WhiteOut` directly.
    That halves the money and warps to the last heal location, but leaves the var at 2 and sets no
    trainer flag — so the beat is fully repeatable. The caller owns the retry budget."""
    from modules.memory import get_event_flag, get_event_var
    from modules.modes import BotModeError
    from modules.modes.util.walking import ensure_facing_direction
    from modules.story.early_game import (
        _ch14_say,
        _check_abort,
        _navigate_riding_out,
        _ride_out_all_scenes,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    if get_event_var(STATE_VAR) >= DONE_STATE:
        return  # resume-safe

    for talk in (1, 2):
        approached = False
        for approach, facing in STEVEN_APPROACHES_2F:
            try:
                yield from _navigate_riding_out(FLOOR_2F, approach, tries=6)
            except BotModeError as error:  # noqa: BLE001 - two approaches exist; the failure is
                # reported below if NEITHER works, which is the only real problem.
                # ‼ A whiteout would otherwise surface as "cannot reach Steven at (1,8)" — a fake
                # reachability failure on a map we have left.
                reraise_if_aborting(error)
                continue
            yield from wait_until_truly_controllable()
            yield from ensure_facing_direction(facing)
            yield
            approached = True
            break
        if not approached:
            raise BotModeError(
                f"Space Center 2F: cannot reach Steven at {STEVEN_TILE_2F} from {_tile()} "
                f"(tried {[a for a, _ in STEVEN_APPROACHES_2F]})."
            )

        _ch14_say(f"Story: Ch19 talking to Steven ({talk} of 2) from {_tile()}")
        context.emulator.press_button("A")
        yield

        if talk == 1:
            # Graded on the flag the first talk sets, not on "some text appeared".
            for _ in range(SCENE_TIMEOUT_FRAMES):
                _check_abort()
                if get_event_flag(STEVEN_FLAG):
                    break
                context.emulator.press_button("B" if _ % 3 else "A")
                yield
            yield from _ride_out_all_scenes()
            yield from wait_until_truly_controllable()
            if not get_event_flag(STEVEN_FLAG):
                raise BotModeError(
                    f"Space Center 2F: talked to Steven but {STEVEN_FLAG} never set. Without it "
                    "the second talk replays the same dialogue instead of offering the battle."
                )
            continue

        # --- the second talk: a YES/NO, then the party menu -----------------------------------
        # ‼ A ONLY while the prompt is up. B answers NO, which returns to a plain msgbox and leaves
        # the beat exactly where it was — a silent no-op that looks like a hang.
        for frames in range(SCENE_TIMEOUT_FRAMES):
            _check_abort()
            if _party_menu_open() or get_event_var(STATE_VAR) >= DONE_STATE:
                break
            if _map() != FLOOR_2F.value:
                break
            context.emulator.press_button("A")
            yield
        if _party_menu_open():
            yield from choose_battle_party()

    # --- ride the multi battle ------------------------------------------------------------------
    _ch14_say("Story: Ch19 the multi battle with Steven has started")
    for frames in range(BATTLE_TIMEOUT_FRAMES):
        _check_abort()
        if get_event_var(STATE_VAR) >= DONE_STATE:
            break
        if frames > 600 and _map() != FLOOR_2F.value:
            raise BotModeError(
                f"Space Center 2F: left the floor with {STATE_VAR}="
                f"{get_event_var(STATE_VAR)} — the multi battle was LOST (the script calls "
                "SetCB2WhiteOut directly on any outcome but a win). The beat is retryable: the "
                "var stays at 2 and no trainer flag is set, but both Steven talks must be redone."
            )
        context.emulator.press_button("B" if frames % 3 else "A")
        yield

    state = get_event_var(STATE_VAR)
    if state < DONE_STATE:
        raise BotModeError(
            f"Space Center 2F: {STATE_VAR}={state} after the multi battle (wanted {DONE_STATE}) "
            f"at {_tile()}."
        )

    # ‼ THE VAR IS SET MID-CUTSCENE. `setvar VAR_MOSSDEEP_SPACE_CENTER_STATE, 3` is followed by
    # ~25 more script commands — three setflags, five removeobjects, two fadescreens and two
    # msgboxes — so returning the moment it flips hands the ladder a locked avatar mid-fade. Ride
    # the rest out. (This is the `EventScript_ActivateStrength` trap that KI-56 was built on.)
    yield from _ride_out_all_scenes()
    yield from wait_until_truly_controllable()
    _ch14_say(f"Story: Ch19 Space Center defended, {STATE_VAR}={state}")


# =================================================================================================
# LEG 6 — HM08 Dive, at Steven's house. This is what the LADDER grades chapter 19 on.
# =================================================================================================

#: ‼ THE CHAPTER DOES NOT END WITH THE BATTLE. `chapters.py` grades chapter 19 on
#: `RECEIVED_HM_DIVE`, which is set in a DIFFERENT BUILDING. A §Ch19 that stopped at
#: `MOSSDEEP_SPACE_CENTER_STATE == 3` would pass its own test while `current_chapter()` kept
#: returning chapter 19 forever — and on the re-run the 2F Steven has been `removeobject`'d, so
#: there would be nobody left to talk to. Green acceptance, wedged ladder.
DIVE_FLAG = "RECEIVED_HM_DIVE"
STEVENS_HOUSE_APPROACH = (19, 11)
STEVENS_HOUSE_STATE_VAR = "STEVENS_HOUSE_STATE"

#: The interior side of Steven's front door. Both (3,7) and (4,7) warp back to the city; the player
#: arrives standing ON (3,7), which is why leaving needs a helper that steps off it first.
STEVENS_HOUSE_INTERIOR_DOOR = (3, 7)


def _has_hm08() -> bool:
    """‼ THE FLAG ALONE IS NOT PROOF OF THE ITEM. `EventScript_StevenGivesDive` does `giveitem`
    and then `setflag FLAG_RECEIVED_HM_DIVE` with NO check of `VAR_RESULT`, so a full TM/HM pocket
    would leave the flag set and the HM never received — the chapter grades green and §Ch21 fails
    on "cannot use Dive". The pocket cannot actually overflow in vanilla, which is exactly why this
    check is cheap insurance rather than a redesign."""
    try:
        from modules.items import get_item_bag, get_item_by_name

        return get_item_bag().quantity_of(get_item_by_name("HM08")) > 0
    except Exception:  # noqa: BLE001 - an unreadable bag must not be reported as a missing item
        return True


def collect_dive_from_stevens_house() -> Generator:
    """Walk into Steven's house; the Dive gift is an ON_FRAME script that fires by itself.

    ‼ THERE IS NOTHING TO TALK TO. `MossdeepCity_StevensHouse_OnFrame` is
    `map_script_2 VAR_STEVENS_HOUSE_STATE, 1`, so the scene starts on the first controllable frame
    after the warp — before the bot could take a step, let alone reach Steven. A "navigate to Steven
    and press A" leg would issue movement into a `lockall` and burn its budget looking like a hang.
    So: warp in, then RIDE, don't walk.

    ‼ The R/S item ball is a red herring. Our flag table carries
    `ITEM_MOSSDEEP_STEVENS_HOUSE_HM08`, and the decomp marks it dead: *"Unused Flag, leftover from
    R/S. HM08 is given to the player directly in Emerald"*. Grading on it would wait forever."""
    from modules.memory import get_event_flag, get_event_var
    from modules.modes import BotModeError
    from modules.story.early_game import (
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        _ride_out_all_scenes,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    # ‼ RESUMING WITH THE GIFT ALREADY TAKEN MUST STILL LEAVE THE HOUSE. The earlier version
    # returned here on the flag alone, which made attempts 2 and 3 of the chapter's retry loop
    # NO-OPS: if `leave_stevens_house()` had failed on attempt 1, the flag was already set, so the
    # retry returned instantly, `_chapter_done()` stayed False (we are still indoors), and the
    # chapter finally raised "RECEIVED_HM_DIVE still unset after 3 attempts" — with the flag SET,
    # HM08 in the bag, and an EMPTY reasons list. The message would have named the wrong problem
    # and the two spare attempts never retried the only thing that had actually failed.
    if get_event_flag(DIVE_FLAG) and _has_hm08():
        yield from leave_stevens_house()
        return  # resume-safe

    if _map() != STEVENS_HOUSE.value:
        _ch14_say("Story: Ch19 walking to Steven's house for HM08 Dive")
        yield from _navigate_riding_out(CITY, STEVENS_HOUSE_APPROACH, tries=10)
        yield from wait_until_truly_controllable()

        def inside() -> bool:
            return _map() == STEVENS_HOUSE.value

        yield from _enter_warp_by_navigation(
            inside, CITY, STEVENS_HOUSE_DOOR, label="Steven's house door"
        )

    # The scene fires on its own; ride it. Graded on the flag, bounded like every other ride here.
    from modules.story.early_game import _check_abort

    for frames in range(SCENE_TIMEOUT_FRAMES):
        _check_abort()
        if get_event_flag(DIVE_FLAG):
            break
        context.emulator.press_button("B" if frames % 3 else "A")
        yield
    yield from _ride_out_all_scenes()
    yield from wait_until_truly_controllable()

    if not get_event_flag(DIVE_FLAG):
        raise BotModeError(
            f"Space Center: {DIVE_FLAG} still unset inside Steven's house at {_tile()} "
            f"({STEVENS_HOUSE_STATE_VAR}={get_event_var(STEVENS_HOUSE_STATE_VAR)}). The gift is an "
            "ON_FRAME script gated on that var being 1; if it is 0 the Space Center beat did not "
            "actually finish, and if it is 2 the gift has already been taken."
        )
    if not _has_hm08():
        raise BotModeError(
            f"Space Center: {DIVE_FLAG} is set but HM08 is NOT in the bag. The gift script sets "
            "the flag without checking `giveitem` succeeded, so this is a full TM/HM pocket. "
            "§Ch21 would fail on 'cannot use Dive' with nothing to point at."
        )
    _ch14_say(f"Story: Ch19 HM08 Dive received ({DIVE_FLAG} set, HM08 in the bag)")
    yield from leave_stevens_house()


def leave_stevens_house() -> Generator:
    """Walk back out into Mossdeep City. ‼ THE CHAPTER IS NOT DONE UNTIL THIS HAS RUN.

    ‼‼ THIS WAS A REAL FAILURE, CAUGHT BY THE ACCEPTANCE TEST RATHER THAN SHIPPED. The first driven
    run of the full chapter got everything right and still FAILED:

        [ch19c] RESULT dive=True hm08=True ... map=MOSSDEEP_CITY_STEVENS_HOUSE at=(3, 7)
        [ch19c] ACCEPTANCE: FAIL (... outside=False can_continue=False)

    The Dive gift is an ON_FRAME script that fires on the doorstep, so the beat ENDS where it began
    — one tile inside a living room — and every completion signal the ladder looks at is already
    true there. §Ch20 departs from Mossdeep City, so a chapter that returned here would hand the
    next one an interior it never expected and fail somewhere unrelated to the cause.

    ‼ THIS IS KI-56's RULE FOR THE THIRD TIME: *a chapter's test must include "and the bot can
    continue"*. It was written about §Ch15 ending four floors underground, violated again by §Ch18
    ending on an eleven-tile island, and would have been violated a third time here. The only reason
    it was not is that the acceptance asks for a real `calculate_path` off the end tile instead of
    asking whether the avatar is "controllable" — which it was, the whole time, indoors."""
    from modules.story.early_game import (
        _ch14_say,
        _navigate_riding_out,
        _walk_through_warp,
        wait_until_truly_controllable,
    )

    if _map() != STEVENS_HOUSE.value:
        return  # resume-safe — already outside

    def outside() -> bool:
        return _map() == CITY.value

    # ‼ AN EXIT DOOR IS NOT AN ENTRY DOOR, AND THE NAVIGATION HELPERS CANNOT DO IT. Measured: the
    # first attempt used `_enter_warp_by_navigation` and failed with "Could not enter the warp at
    # (3, 7)". Both of the navigate-based helpers try to free the tile by stepping SOUTH to
    # `(x, y+1)` first — and (3,7) is the BOTTOM ROW of this house, so (3,8) does not exist. The
    # human action is simply to walk DOWN off the doorstep, which is what `_walk_through_warp`
    # exists for ("doors that can't be a pathfinding destination").
    if _tile() != STEVENS_HOUSE_INTERIOR_DOOR:
        yield from _navigate_riding_out(STEVENS_HOUSE, STEVENS_HOUSE_INTERIOR_DOOR, tries=6)
    yield from _walk_through_warp("Down", STEVENS_HOUSE.value, timeout_frames=600)
    yield from wait_until_truly_controllable()
    if not outside():
        from modules.modes import BotModeError

        raise BotModeError(
            f"Space Center: got HM08 but could not leave Steven's house (still on {_map()} at "
            f"{_tile()}). Leaving the run indoors strands the ladder — §Ch20 departs from the city."
        )
    _ch14_say(f"Story: Ch19 out of Steven's house, in Mossdeep City at {_tile()}")


def do_space_center_chapter() -> Generator:
    """§Ch19 end to end — defend the Mossdeep Space Center, then collect HM08 Dive.

    INTENT: set `RECEIVED_HM_DIVE`, which is what `chapters.py` grades chapter 19 on and what
    §Ch20/§Ch21 need in the bag.
    STORY CONDITION: 7 badges, in Mossdeep, `MOSSDEEP_SPACE_CENTER_STATE >= 1`.
    GOAL/END STATE: `RECEIVED_HM_DIVE` set, HM08 in the bag, avatar controllable and OUT of the
    building — graded BINARY.

    THE RETRY LOOP IS WHITEOUT RECOVERY, and this chapter needs it because losing Steven's multi
    battle is a NORMAL outcome rather than an error: the script inspects the battle result itself
    and calls `SetCB2WhiteOut` on anything but a win, which halves the money and warps the player to
    their last heal location — but leaves `MOSSDEEP_SPACE_CENTER_STATE` at 2 and sets no trainer
    flag. So the beat is genuinely repeatable, and every leg above is resume-safe so that a retry
    re-does only what is actually missing.

    ‼ THE RETRY BUDGET IS THE POINT. A loss that re-derives the same choices from the same inputs
    is a deterministic failure, and "it is recoverable" is not a reason to loop forever — a bounded
    loop re-entered by its dispatcher is still infinite. Three attempts, then stop with every
    reason attached."""
    from modules.memory import get_event_flag, get_event_var
    from modules.modes import BotModeError
    from modules.story.early_game import StoryAbort, _ch14_say, reraise_if_aborting

    # ‼ "DONE" INCLUDES BEING OUT OF THE BUILDING. Grading the resume check on the flag alone would
    # let a run that was interrupted inside Steven's house return immediately and hand §Ch20 an
    # interior. The flag is the achievement; standing somewhere the next chapter can start from is
    # the other half of it (KI-56).
    def _chapter_done() -> bool:
        return get_event_flag(DIVE_FLAG) and _has_hm08() and _map() != STEVENS_HOUSE.value

    if _chapter_done():
        return  # resume-safe

    attempts = []
    for attempt in range(1, 4):
        try:
            if get_event_var(STATE_VAR) < DONE_STATE:
                yield from walk_into_the_space_center()
                yield from cross_first_floor()
                yield from clear_the_three_grunts()
                yield from fight_alongside_steven()
            yield from collect_dive_from_stevens_house()
        except StoryAbort:
            # ‼‼ NEVER RETRY IN PLACE AFTER A WHITEOUT (KI-67). The abort latch is cleared ONLY by
            # `StoryMode.run`, so catching this and looping would run straight into the next
            # `_check_abort()` and die instantly — one whiteout would burn all three attempts in a
            # handful of frames and report three failures, two of them invented. Re-raising is not
            # giving up on the retry: `StoryMode.run` clears the latch, waits out the respawn,
            # steps out of the Pokémon Center and re-runs `_play()`, which re-enters this chapter
            # from wherever the player actually is. That is the retry, and it is bounded at 40.
            raise
        except BotModeError as error:  # noqa: BLE001 - NOT swallowed. A whiteout is an EXPECTED
            # outcome of this chapter's battles; every attempt's reason is kept and raised together
            # below if all three fail.
            # ‼ BOTH GUARDS ARE NEEDED. `except StoryAbort` above catches the abort while the
            # ORIGINAL object is in flight; this catches one whose identity an inner loop destroyed
            # by raising a fresh error. See `reraise_if_aborting`.
            reraise_if_aborting(error)
            attempts.append(f"attempt {attempt}: {str(error)[:200]}")
            _ch14_say(f"Story: Ch19 attempt {attempt} failed — {str(error)[:120]}")
            continue

        if _chapter_done():
            _ch14_say("Story: Ch19 complete — the Space Center is safe, HM08 Dive is in the bag, "
                      "and the bot is back outside")
            return

    raise BotModeError(
        f"Space Center: {DIVE_FLAG} still unset after 3 attempts. " + " | ".join(attempts)
    )
