"""
Patrol (Custom) — walks a user-defined loop of waypoints on the current map,
triggering wild encounters along the way.

The stock Spin mode hunts on a single tile; Patrol covers ground: long grass
strips, cave corridors, or any route section you define. Encounters are
handled by the bot's default encounter pipeline (shiny detection, custom
catch filters, stats, notifications all apply, exactly like stock modes).

Setup: create `patrol.yml` in your profile folder (profiles/<name>/):

    # Map-local coordinates, visited in order, then looping back to the first.
    # Read the current tile from the GUI's map debug tab, or the HTTP API's /map.
    waypoints:
      - [10, 14]
      - [15, 14]
      - [15, 20]

All waypoints must be on the map the player is standing on when the mode is
started, and must be reachable by walking (the pathfinder handles corners —
consecutive waypoints don't need to share a row/column).
"""

from typing import Generator

import yaml

from modules.battle_state import BattleOutcome
from modules.context import context
from modules.modes import BotMode, BotModeError
from modules.modes._asserts import assert_boxes_or_party_can_fit_pokemon, assert_player_has_poke_balls
from modules.modes.util import apply_white_flute_if_available, navigate_to
from modules.player import get_player_avatar

CONFIG_FILE_NAME = "patrol.yml"


class PatrolMode(BotMode):
    @staticmethod
    def name() -> str:
        return "Patrol (Custom)"

    @staticmethod
    def is_selectable() -> bool:
        return get_player_avatar().map_location.has_encounters

    def on_battle_ended(self, outcome: "BattleOutcome") -> None:
        if outcome is not BattleOutcome.Lost:
            assert_player_has_poke_balls()
            assert_boxes_or_party_can_fit_pokemon()

    def run(self) -> Generator:
        waypoints = self._load_waypoints()
        assert_player_has_poke_balls()
        assert_boxes_or_party_can_fit_pokemon()
        yield from apply_white_flute_if_available()

        # The map the player is on when the mode starts is the patrol map;
        # `navigate_to` re-routes from wherever a battle left the player.
        patrol_map = get_player_avatar().map_group_and_number
        while True:
            for x, y in waypoints:
                yield from navigate_to(patrol_map, (x, y), avoid_encounters=False)

    def _load_waypoints(self) -> list[tuple[int, int]]:
        config_path = context.profile.path / CONFIG_FILE_NAME
        if not config_path.exists():
            raise BotModeError(
                f"Patrol needs a waypoint list: create `{CONFIG_FILE_NAME}` in your profile folder\n"
                f"({config_path})\n"
                "with content like:\n\n"
                "waypoints:\n  - [10, 14]\n  - [15, 14]\n  - [15, 20]"
            )

        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise BotModeError(f"`{CONFIG_FILE_NAME}` is not valid YAML: {error}")

        raw_waypoints = data.get("waypoints") if isinstance(data, dict) else None
        if not isinstance(raw_waypoints, list) or len(raw_waypoints) < 2:
            raise BotModeError(f"`{CONFIG_FILE_NAME}` must contain a `waypoints` list with at least two entries.")

        waypoints: list[tuple[int, int]] = []
        for index, entry in enumerate(raw_waypoints):
            if (
                not isinstance(entry, list)
                or len(entry) != 2
                or not all(isinstance(coordinate, int) for coordinate in entry)
            ):
                raise BotModeError(
                    f"`{CONFIG_FILE_NAME}` waypoint #{index + 1} is invalid: each entry must be `[x, y]` "
                    "with whole-number map-local coordinates."
                )
            waypoints.append((entry[0], entry[1]))
        return waypoints
