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
(boss preparation BP-1, 2026-11-09) The same file's THIRD slice: a boss's TEAM (`boss_party`: species, level, moves and
held item of each Pokemon, USER RULINGS 40, 44, 58), for the readiness verdict before the next gym leader
(`brain/bossprep.py`). Never its IVs or the trainer's AI flags (not in the file).
(the chapter-5 search fix K1, 2026-11-13) maps.json's SECOND slice: the MAP LINKS, map level only (`entry_maps`: of each
map its `id`, each warp's `dest_map` and each connection's `map`; never a warp's `x`/`y`), so it knows which maps a place
is entered from, as a seasoned player knows from a guide's map (USER RULING 40: "the maps and their connections").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .facts import move_named, species_named

__all__ = [
    "BossMon",
    "OPEN_TYPES",
    "PLACE_TYPES",
    "boss_party",
    "entry_maps",
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


def entry_maps(const: str | None) -> frozenset[str]:
    """(the chapter-5 search fix K1, 2026-11-13) THE MAPS A PLACE IS ENTERED FROM: every other map with a door, stairs or
    a cave mouth that leads to map `const` (its warps' `dest_map`) or with an edge it lies beyond (its connections' `map`),
    as consts with `MAP_` dropped ("RUSTURF_TUNNEL" -> {"ROUTE116", "VERDANTURF_TOWN"}). What a seasoned player knows from
    a guide's map (USER RULING 40: "the maps and their connections"). MAP LEVEL ONLY: no warp's tile is read (its `x` and
    `y` stay unread here). frozenset() for a const no map leads to, or none given. Read once."""
    if "entries" not in _CACHE:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        found: dict[str, set[str]] = {}
        for entry in data["maps"]:
            source = str(entry["id"]).removeprefix("MAP_")
            leads = [str(warp["dest_map"]) for warp in entry.get("warps") or ()]
            leads += [str(link["map"]) for link in entry.get("connections") or ()]
            for target in leads:
                if target.removeprefix("MAP_") != source:
                    found.setdefault(target.removeprefix("MAP_"), set()).add(source)
        _CACHE["entries"] = {target: frozenset(sources) for target, sources in found.items()}
    return _CACHE["entries"].get(const or "", frozenset())


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


@dataclass(frozen=True)
class BossMon:
    """(boss preparation BP-1, 2026-11-09) One Pokemon of a boss's team as a seasoned player knows it (USER RULINGS 40,
    44, 58): its species and moves by the AI's own names (`knowledge/facts.py`), its level, and the item it holds (a guide
    lists it: RULING 44), spoken as the game spells it ("Sitrus Berry"), or None. Its IVs and the trainer's AI flags are
    not in the knowledge and stay unknown."""

    species: str
    level: int
    moves: tuple[str, ...]
    held_item: str | None


def _spoken(symbol: str, prefix: str) -> str:
    return str(symbol).removeprefix(prefix).replace("_", " ")


def boss_party(name: str) -> tuple[BossMon, ...]:
    """(boss preparation BP-1, 2026-11-09) The team of the boss called `name` ("BRAWLY"), in the order it is sent out:
    the world file's THIRD slice, read once; of each boss only its `name` and `party`, of each Pokemon only `species`,
    `level`, `moves` and `held_item` (all classified AI in `gates/check_fairness.py`; the held item by USER RULING 44).
    The first boss of that name (a gym leader's first fight; a rematch is a separate trainer the file does not join).
    () for a name the file does not hold. A species or move with no facts name is kept by its spoken name."""
    if "parties" not in _CACHE:
        data = json.loads(_BOSSES.read_text(encoding="utf-8"))
        parties: dict[str, tuple[BossMon, ...]] = {}
        for boss in data["bosses"]:
            key = str(boss["name"])
            if key in parties:
                continue
            team = []
            for mon in boss["party"]:
                species = _spoken(mon["species"], "SPECIES_")
                moves = tuple(move_named(_spoken(m, "MOVE_")) or _spoken(m, "MOVE_") for m in mon["moves"])
                item = mon.get("held_item")  # a party without held items has no such key
                team.append(BossMon(species_named(species) or species, int(mon["level"]), moves,
                                    _spoken(item, "ITEM_").title() if item else None))
            parties[key] = tuple(team)
        _CACHE["parties"] = parties
    return tuple(_CACHE["parties"].get(name, ()))
