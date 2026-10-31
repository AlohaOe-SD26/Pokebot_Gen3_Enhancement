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
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "OPEN_TYPES",
    "open_map",
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
