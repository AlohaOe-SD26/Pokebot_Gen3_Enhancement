"""The AI's ATLAS: the STATIC type of each map (KI-128, 2026-10-31; the loader's first slice). Framework-free, read only.

WHAT IT ANSWERS: is a map OPEN COUNTRY (a route, a town, a city, an ocean route) or not, by the map type the game itself
gives it. A seasoned player knows this from the map-name popup, the look of the place and a guide's map (USER RULINGS 40
and 45: static game knowledge is allowed; live hidden state is not). It answers None for a map it does not hold, so the
caller falls back to what it knew before (the map's name).

WHY (KI-128): the brain told open country from an interior by the map's NAME (`brain/goals.py` OUTDOOR), and PETALBURG
WOODS, a route by its type, is not named like one. In all three A0 runs (2026-10-30) the AI was evicted from the woods and
refused the way back in, and never reached their north half. `brain/goals.py` open_way asks this module instead.

WHAT IT READS, AND NOTHING ELSE: the world file `world/maps.json` (written by the test side's `gates/extract_world.py`
from the pinned decomp), once, cached; of it only each map's `id` and `map_type`. No flag, no script, no label, no
coordinate: `gates/check_fairness.py` declares this module the file's only LOADER and classifies every key path of the
file (RULE B), so any developer key read here fails that gate (B2).
(chapter 6 NS1, 2026-11-06) From the same two keys: the TOWNS and CITIES by the names people say (`town_places`: a trip
offered "to PETALBURG" is a trip to PETALBURG CITY).
(chapter 7 NS4, 2026-11-06) The SECOND world file, `world/bosses.json` (the same extractor): of each boss only its `role`,
`name` and `battled_on`, so it knows which leader holds which gym (`gym_leaders`), as a seasoned player does (USER RULING
40). Its every key path is classified in `gates/check_fairness.py` too; its badge flag, trainer id and source lines are
developer data no loader reads.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "OPEN_TYPES",
    "PLACE_TYPES",
    "gym_leaders",
    "open_map",
    "town_places",
]

_FILE = Path(__file__).parent / "world" / "maps.json"
#: the map types of OPEN COUNTRY (include/constants/map_types.h): a person walks through these on the way somewhere
OPEN_TYPES = frozenset({"MAP_TYPE_ROUTE", "MAP_TYPE_TOWN", "MAP_TYPE_CITY", "MAP_TYPE_OCEAN_ROUTE"})
_CACHE: dict[str, dict[str, str]] = {}


def _types() -> dict[str, str]:
    """Each map's const, `MAP_` dropped (the eyes' `map_const`: "PETALBURG_WOODS") -> its map type, read once."""
    if "types" not in _CACHE:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        _CACHE["types"] = {str(entry["id"]).removeprefix("MAP_"): str(entry["map_type"]) for entry in data["maps"]}
    return _CACHE["types"]


def open_map(const: str | None) -> bool | None:
    """Is map `const` open country by its static type (`OPEN_TYPES`)? True or False; None for a const the atlas does not
    hold (or none given): the caller then decides by what it knew before."""
    kind = _types().get(const or "")
    if kind is None:
        return None
    return kind in OPEN_TYPES


#: the map types of a TOWN or a CITY (include/constants/map_types.h): a place a person names when they speak of a trip
PLACE_TYPES = frozenset({"MAP_TYPE_TOWN", "MAP_TYPE_CITY"})


def town_places() -> dict[str, str]:
    """(chapter 6 NS1, 2026-11-06) Every TOWN and CITY of the game by the name people say it by -> its map const: the
    const with its `_TOWN` / `_CITY` dropped, the underscores spoken as spaces ("DEWFORD" -> "DEWFORD_TOWN", "EVER
    GRANDE" -> "EVER_GRANDE_CITY"). What a seasoned player knows from the region map (USER RULINGS 40, 45); read from the
    same two keys as `open_map` (each map's `id` and `map_type`), nothing else."""
    if "places" not in _CACHE:
        places = {}
        for const, kind in _types().items():
            if kind in PLACE_TYPES:
                head, _, last = const.rpartition("_")
                name = (head if last in ("TOWN", "CITY") else const).replace("_", " ")
                places[name] = const
        _CACHE["places"] = places
    return dict(_CACHE["places"])


_BOSSES = Path(__file__).parent / "world" / "bosses.json"


def gym_leaders() -> dict[str, str]:
    """(chapter 7 NS4, 2026-11-06) Every GYM LEADER by name -> the gym map they are fought in (the map const as the eyes
    name it, `MAP_` dropped): "BRAWLY" -> "DEWFORD_TOWN_GYM". What a seasoned player knows (USER RULING 40: "which leader
    holds which gym"; the gym's own sign says it too). The world file's SECOND slice, read once: of each boss only its
    `role`, `name` and `battled_on` (`gates/check_fairness.py` classifies every key of the file; the rest is not read)."""
    if "leaders" not in _CACHE:
        data = json.loads(_BOSSES.read_text(encoding="utf-8"))
        leaders = {}
        for boss in data["bosses"]:
            if boss.get("role") == "gym_leader" and boss.get("battled_on"):
                leaders[str(boss["name"])] = str(boss["battled_on"][0]).removeprefix("MAP_")
        _CACHE["leaders"] = leaders
    return dict(_CACHE["leaders"])
