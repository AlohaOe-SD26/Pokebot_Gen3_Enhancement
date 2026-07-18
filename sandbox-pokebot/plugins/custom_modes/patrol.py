"""
Patrol (Custom) — walks a user-defined loop of waypoints on the current map,
triggering wild encounters along the way.

The stock Spin mode hunts on a single tile; Patrol covers ground: long grass
strips, cave corridors, or any route section you define. Encounters are
handled by the bot's default encounter pipeline (shiny detection, custom
catch filters, stats, notifications all apply, exactly like stock modes).

Setup: create `patrol.yml` in your profile folder (profiles/<name>/):

    # Waypoints are visited in order, then loop back to the first.
    # Two forms (mixable):
    #   - [x, y]                      -> tile on the CURRENT map (where you
    #                                    stand when the mode starts)
    #   - {map: [group, number], at: [x, y]}   -> tile on a specific map
    # Read tiles/maps from the GUI's map debug tab (-d), or the HTTP API's /map.
    waypoints:
      - [10, 14]
      - {map: [1, 4], at: [15, 20]}

Waypoints must be reachable by walking/surfing across directly CONNECTED
maps (the pathfinder cannot route through warps/doors — an upstream
limitation; a warp tile may only be a final destination).
"""

from typing import Generator

import yaml

from modules.battle_state import BattleOutcome
from modules.context import context
from modules.map_data import MapFRLG, MapRSE
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
        # A multi-map route may legitimately START on a map without encounters
        # (e.g. a town between two grass routes), so a configured patrol.yml
        # also makes the mode selectable.
        if context.profile is not None and (context.profile.path / CONFIG_FILE_NAME).exists():
            return True
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

        # Waypoints without an explicit map use the map the player is on when
        # the mode starts; `navigate_to` re-routes from wherever a battle
        # left the player.
        start_map = get_player_avatar().map_group_and_number
        while True:
            for waypoint_map, (x, y) in waypoints:
                yield from navigate_to(waypoint_map or start_map, (x, y), avoid_encounters=False)

    def _load_waypoints(self) -> list[tuple[tuple[int, int] | None, tuple[int, int]]]:
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

        def _coordinate_pair(value, index: int, what: str) -> tuple:
            if not isinstance(value, list) or len(value) != 2 or not all(
                isinstance(coordinate, int) and not isinstance(coordinate, bool) for coordinate in value
            ):
                raise BotModeError(
                    f"`{CONFIG_FILE_NAME}` waypoint #{index + 1}: {what} must be two whole numbers, e.g. `[12, 7]`."
                )
            return value[0], value[1]

        # Each parsed waypoint is (map | None, (x, y)); None = the map the
        # player is standing on when the mode starts.
        waypoints: list = []
        for index, entry in enumerate(raw_waypoints):
            if isinstance(entry, dict):
                unknown_keys = set(entry.keys()) - {"map", "at"}
                if unknown_keys or "map" not in entry or "at" not in entry:
                    raise BotModeError(
                        f"`{CONFIG_FILE_NAME}` waypoint #{index + 1} is invalid: a mapping entry must be exactly "
                        "`{map: [group, number], at: [x, y]}`."
                    )
                waypoint_map = _coordinate_pair(entry["map"], index, "`map`")
                map_enum = MapRSE if context.rom.is_rse else MapFRLG
                try:
                    map_enum(waypoint_map)
                except ValueError:
                    raise BotModeError(
                        f"`{CONFIG_FILE_NAME}` waypoint #{index + 1}: map "
                        f"[{waypoint_map[0]}, {waypoint_map[1]}] does not exist in this game."
                    )
                coordinates = _coordinate_pair(entry["at"], index, "`at`")
                waypoints.append((waypoint_map, coordinates))
            else:
                waypoints.append((None, _coordinate_pair(entry, index, "each `[x, y]` entry")))
        return waypoints
