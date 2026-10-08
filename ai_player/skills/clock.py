"""SKILL: set the wall clock in the player's room (build step 2; design draft §6 criterion 1: "it gets through
the intro (name, gender, CLOCK)").

The clock hangs on the wall of the player's room (`data/maps/LittlerootTown_*House_2F` bg event
`..._EventScript_WallClock` at (5, 1)); the player stands below it. The skill: face it and press A (only while
the player is free: `hands/dialogue.py` talk), read "The clock is stopped…" and advance it, set the time on
the clock screen by READING the hands' time (`hands/menus.py` set_clock), YES to "Is this the correct time?"
(its cursor opens on NO), then advance what follows (Mom comes upstairs, `data/scripts/players_house.inc`
PlayersHouse_2F_EventScript_WallClock) until the player is free again.

THE TIME: what a person sets, their own clock's time (the computer's local time, `hands/menus.py`
local_clock), unless the run names one. It is logged before it is set.

HOW THE AI GETS HERE: step 2 has no navigator. `gates/make_clock_fixture.py` walks a saved game from the truck
to the clock with button presses (test side), and the arm starts the AI there. In step 3 the navigator walks
the AI from the truck into the house, up the stairs and to this tile itself (`README.md`, "Known limits").
"""

from __future__ import annotations

from collections.abc import Generator

from ai_player.hands.dialogue import advance, dialogue_over, talk, talk_direction
from ai_player.hands.menus import local_clock, set_clock
from ai_player.hands.pad import Hands

__all__ = ["set_wall_clock"]


def set_wall_clock(hands: Hands, hours: int | None = None, minutes: int | None = None) -> Generator[None, None, str]:
    """Returns "clock set to H:MM" or what went wrong."""
    why = "set the wall clock"
    look = hands.look()
    signs = [o for o in (look.view.objects if look.view else ()) if o.kind == "sign" and talk_direction(look, o) is not None]
    if not signs:
        return "no clock (an interactable tile of the wall) in reach"
    clock = signs[0]
    if hours is None or minutes is None:
        hours, minutes = local_clock()
        source = "the computer's local time"
    else:
        source = "named by the run"
    hands.tell(f"{why}: the clock at ({clock.dx},{clock.dy}); the time to set: {hours}:{minutes:02d} ({source})")
    if not (yield from talk(hands, clock, why)):
        return "the clock did not answer"
    outcome = yield from advance(hands, lambda l: l.screen.ui is not None and l.screen.ui.kind == "clock", why)
    if outcome not in ("done", "menu:clock"):
        return f"no clock screen: {outcome}"
    if not (yield from set_clock(hands, hours, minutes, why)):
        return "the clock was not set"
    outcome = yield from advance(hands, dialogue_over, f"{why}: what follows")
    if outcome != "done":
        return f"after the clock: {outcome}"
    return f"clock set to {hours}:{minutes:02d}"
