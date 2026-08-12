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


def walk_into_the_space_center() -> Generator:
    """Heal, cross Mossdeep (riding out the forced Team Magma cutscene), and enter 1F.

    ‼ HEAL FIRST, ALWAYS. The §Ch16 lesson, and it applies literally here: the anchor this chapter
    is developed against (`post_mossdeep_gym.ss1`) arrives at **66% HP with one Pokémon fainted**,
    straight out of a gym fight. Walking into seven trainer battles on that party is how a run
    whites out and then "passes" because a whiteout heals."""
    from modules.map_data import PokemonCenter
    from modules.modes.util.higher_level_actions import heal_in_pokemon_center
    from modules.story.early_game import (
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        wait_until_truly_controllable,
    )

    _ch14_say("Story: Ch19 healing at Mossdeep before the Space Center...")
    yield from _navigate_riding_out(CITY, (28, 17))
    yield from heal_in_pokemon_center(PokemonCenter.MossdeepCity)
    yield from wait_until_truly_controllable()

    # ‼ The walk to the door CROSSES the cutscene trigger tiles by construction — there is no other
    # route. `_navigate_riding_out` is used precisely because it expects to be interrupted.
    _ch14_say("Story: Ch19 crossing to the Space Center (a forced Team Magma scene fires en route)")
    yield from _navigate_riding_out(CITY, SPACE_CENTER_DOOR_APPROACH, tries=12)
    yield from wait_until_truly_controllable()

    def inside() -> bool:
        return _map() == FLOOR_1F.value

    yield from _enter_warp_by_navigation(inside, CITY, SPACE_CENTER_DOOR, label="Space Center door")
    yield from wait_until_truly_controllable()
    _ch14_say(f"Story: Ch19 inside the Space Center at {_tile()}")


def cross_first_floor() -> Generator:
    """Reach 2F. Two of the four 1F grunts are unavoidable, for two different reasons.

    ‼ GRUNT 4 at (10,2) is forced by GEOMETRY: the only walkable crossing of column x=10 is rows 3
    and 4, and those are exactly its sight tiles. ‼ GRUNT 2 at (13,2) is forced because it stands
    on the ONLY tile from which the stairs at (13,1) can be reached — it is a physical plug, and
    beating it makes it step aside. So this leg expects battles and rides them out rather than
    treating them as failures."""
    from modules.story.early_game import (
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        wait_until_truly_controllable,
    )

    _ch14_say("Story: Ch19 crossing 1F — grunts at (10,2) and (13,2) are unavoidable")
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

    if get_event_var(STATE_VAR) >= 2:
        return  # resume-safe

    _ch14_say("Story: Ch19 answering the 2F prompt and fighting the three grunts...")
    yield from _mash_until(
        lambda: get_event_var(STATE_VAR) >= 2,
        "the three-grunt gauntlet",
        timeout=BATTLE_TIMEOUT_FRAMES,
        accept=True,   # ‼ A ONLY - B answers NO here and warps us out. See `_mash_until`.
    )
    yield from wait_until_truly_controllable()
    _ch14_say(f"Story: Ch19 three grunts done, {STATE_VAR}={get_event_var(STATE_VAR)}")
