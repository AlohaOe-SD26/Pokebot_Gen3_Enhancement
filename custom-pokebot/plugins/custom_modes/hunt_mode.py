"""
Hunt (Custom) — travel to a target species' best wild spot, then hunt it.

Set the target from the dashboard's Hunt tab (#9): it stores the species, the
map, a representative encounter tile, and the method. This mode walks there
via global (warp-aware) navigation, then runs the right hunting behaviour.
Encounters go through the bot's default pipeline, so shiny detection, custom
catch filters, stats and notifications all apply exactly like a stock mode.

If no reachable encounter tile could be determined (e.g. Rock Smash, or a
water spot needing Surf), the mode raises a friendly error asking you to walk
to the encounter area yourself and use the recommended stock mode.
"""

from typing import Generator

from modules.battle_state import BattleOutcome
from modules.encounter_index import get_hunt_target
from modules.modes import BotMode, BotModeError
from modules.modes._asserts import assert_boxes_or_party_can_fit_pokemon, assert_player_has_poke_balls
from modules.modes.util import apply_white_flute_if_available, fish, spin
from modules.modes.util.global_navigation import navigate_to_anywhere

_FISHING_METHODS = ("Old Rod", "Good Rod", "Super Rod")


class HuntMode(BotMode):
    @staticmethod
    def name() -> str:
        return "Hunt (Custom)"

    @staticmethod
    def is_selectable() -> bool:
        return get_hunt_target() is not None

    def on_battle_ended(self, outcome: "BattleOutcome") -> None:
        if outcome is not BattleOutcome.Lost:
            assert_player_has_poke_balls()
            assert_boxes_or_party_can_fit_pokemon()

    def run(self) -> Generator:
        target = get_hunt_target()
        if not target:
            raise BotModeError("No hunt target set — pick a species in the dashboard's Hunt tab first.")
        try:
            target_map = tuple(target["map"])
            method = target.get("method", "Grass")
            map_name = target.get("map_name", f"{target_map[0]}.{target_map[1]}")
            tile = target.get("tile")
            species = target.get("species", "target")
        except (KeyError, TypeError, ValueError):
            raise BotModeError("Hunt target is malformed — re-select it in the Hunt tab.")

        assert_player_has_poke_balls()
        assert_boxes_or_party_can_fit_pokemon()

        if tile is None:
            raise BotModeError(
                f"Couldn't auto-find a reachable {method} spot on {map_name} to hunt {species}. "
                "Walk to the encounter area yourself, then use the recommended mode."
            )

        # Travel to the encounter tile (avoiding encounters en route)...
        yield from navigate_to_anywhere(target_map, tuple(tile), avoid_encounters=True)
        # ...then hunt in place. Step-based encounters (grass/surf) come from
        # spinning; fishing methods use the rod loop.
        yield from apply_white_flute_if_available()
        if method in _FISHING_METHODS:
            yield from fish(loop=True)
        else:
            yield from spin()
