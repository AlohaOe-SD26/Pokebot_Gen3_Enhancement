"""What a SEASONED player knows of a species' future and of where the wild Pokemon live (boss preparation BP-1,
2026-11-09). Framework-free, read only.

WHAT IT ANSWERS (USER RULINGS 40 and 58: a seasoned player knows Pokemon and Emerald; against a boss the party loses to,
training the party's own counter is a plan):
  * `evolutions(species)`: how a species evolves, as a Pokedex or a guide says it: (method, level or None, into);
  * `level_up(species)`: the moves it learns by level: (level, move);
  * `land_levels(map_const)`: the levels of the wild Pokemon on a map's land (its grass), as a guide lists them;
  * `land_slots(map_const)` (round 3): which species live on that land, each at its highest level there.
Every name is the AI's own (`knowledge/facts.py`): "Wurmple", "Poison Sting". A symbol that maps to no facts name is
left out (`unmapped` lists them, for the test side).

WHY: the readiness verdict (`brain/bossprep.py`) judges a party member at the level it WOULD reach (M3 of the BP-1
critique: today's party is not the party a person brings, a Wurmple at L18 is a Dustox or a Beautifly that knows
Confusion or Gust), and a raise goal chooses grass whose wild levels suit the Pokemon being raised.

WHAT IT READS, AND NOTHING ELSE (`gates/check_fairness.py` declares this module the three files' only LOADER and
classifies every key path of them, RULE B): of `seasoned/species.json` each entry's `symbol`, `name` and its
`evolutions[].method / parameter.value / into`; of `seasoned/learnsets.json` each entry's `symbol` and `level_up[].level /
move`; of `seasoned/encounters.json` each map's `map`, `availability` and its land slots' `species` and `min_level /
max_level`. Never a base stat, a catch rate, an experience yield, a growth rate or a wild held item (all HIDDEN: the fairness gate
refuses them here, B2), and never which branch a Wurmple takes (decided by its PID, which is hidden: the caller judges by
the worse branch).
"""

from __future__ import annotations

import json
from pathlib import Path

from .facts import move_named, species_named

__all__ = [
    "evolutions",
    "land_levels",
    "land_slots",
    "level_up",
    "unmapped",
    "wild_moves",
]

_FOLDER = Path(__file__).parent / "seasoned"
_CACHE: dict[str, object] = {}


def _load(name: str) -> dict:
    return json.loads((_FOLDER / name).read_text(encoding="utf-8"))


def _move(symbol: str) -> str | None:
    """A move's symbol ("MOVE_KARATE_CHOP") by its facts name ("Karate Chop"): the prefix dropped, the rest read as the
    screen prints it (`move_named`)."""
    return move_named(str(symbol).removeprefix("MOVE_").replace("_", " "))


def _species() -> dict[str, tuple[str | None, tuple[tuple[str, int | None, str], ...]]]:
    """Each species' symbol -> (its facts name, its evolutions as (method, level or None, the target's SYMBOL))."""
    if "species" not in _CACHE:
        out = {}
        for entry in _load("species.json")["species"]:
            evos = []
            for evo in entry["evolutions"]:
                level = evo["parameter"].get("value") if isinstance(evo["parameter"], dict) else None
                evos.append((str(evo["method"]), int(level) if isinstance(level, int) else None, str(evo["into"])))
            out[str(entry["symbol"])] = (species_named(str(entry["name"])), tuple(evos))
        _CACHE["species"] = out
    return _CACHE["species"]  # type: ignore[return-value]


def _by_name() -> dict[str, str]:
    """A facts name -> its species symbol."""
    if "names" not in _CACHE:
        _CACHE["names"] = {name: symbol for symbol, (name, _) in _species().items() if name is not None}
    return _CACHE["names"]  # type: ignore[return-value]


def _learnsets() -> dict[str, tuple[tuple[int, str | None], ...]]:
    if "learnsets" not in _CACHE:
        _CACHE["learnsets"] = {str(entry["symbol"]): tuple((int(m["level"]), _move(m["move"])) for m in entry["level_up"])
                               for entry in _load("learnsets.json")["species"]}
    return _CACHE["learnsets"]  # type: ignore[return-value]


def evolutions(species: str) -> tuple[tuple[str, int | None, str], ...]:
    """How `species` (a facts name) evolves: (method, level or None, the species it becomes, by its facts name); () for
    one that does not, or that is unknown."""
    symbol = _by_name().get(species)
    if symbol is None:
        return ()
    names = _species()
    out = []
    for method, level, into in names[symbol][1]:
        target = names.get(into, (None, ()))[0]
        if target is not None:
            out.append((method, level, target))
    return tuple(out)


def level_up(species: str) -> tuple[tuple[int, str], ...]:
    """The moves `species` (a facts name) learns by level, (level, move), as its level-up list orders them."""
    symbol = _by_name().get(species)
    if symbol is None:
        return ()
    return tuple((level, move) for level, move in _learnsets().get(symbol, ()) if move is not None)


def wild_moves(species: str, level: int) -> list[str]:
    """(boss preparation round 2, 2026-11-11) The moves a WILD `species` (a facts name) of `level` knows, as a seasoned
    player reckons it from the level-up list: the game's initial-moveset rule (`src/pokemon.c` GiveBoxMonInitialMoveset:
    every level-up move at or below its level, in the list's order, a move it knows already skipped, the FIRST one
    forgotten once it has four). [] for an unknown species. Static knowledge (a guide's learnset), nothing hidden."""
    out: list[str] = []
    for at, move in level_up(species):
        if at > level:
            break
        if move in out:
            continue
        out.append(move)
        if len(out) > 4:
            out.pop(0)
    return out


def land_levels(map_const: str | None) -> tuple[int, int] | None:
    """The lowest and highest level of the wild Pokemon on the LAND (the grass) of map `map_const` ("ROUTE104", the eyes'
    const; "MAP_ROUTE104" too), over the map's entries a player meets in normal play (`availability` "normal"); None
    when it has none."""
    if "land" not in _CACHE:
        land: dict[str, tuple[int, int]] = {}
        for entry in _load("encounters.json")["maps"]:
            if entry["availability"] != "normal":
                continue
            slots = ((entry.get("methods") or {}).get("land") or {}).get("slots") or ()
            if not slots:
                continue
            const = str(entry["map"]).removeprefix("MAP_")
            low = min(int(s["min_level"]) for s in slots)
            high = max(int(s["max_level"]) for s in slots)
            if const in land:
                low, high = min(low, land[const][0]), max(high, land[const][1])
            land[const] = (low, high)
        _CACHE["land"] = land
    return _CACHE["land"].get(str(map_const or "").removeprefix("MAP_"))  # type: ignore[union-attr]


def land_slots(map_const: str | None) -> tuple[tuple[str, int], ...]:
    """(boss preparation round 3, 2026-11-11) The wild Pokemon of a map's LAND as a guide's table lists them: each
    species (a facts name) once, at the HIGHEST level the map's land holds it (its strongest), over the entries a player
    meets in normal play; sorted by species. () when it has none. A species whose symbol maps to no facts name is left
    out. Static knowledge: who lives in the grass and how strong (never how often a slot comes up, never a yield)."""
    if "slots" not in _CACHE:
        found: dict[str, dict[str, int]] = {}
        for entry in _load("encounters.json")["maps"]:
            if entry["availability"] != "normal":
                continue
            slots = ((entry.get("methods") or {}).get("land") or {}).get("slots") or ()
            const = str(entry["map"]).removeprefix("MAP_")
            for slot in slots:
                name = _species().get(str(slot["species"]), (None, ()))[0]
                if name is None:
                    continue
                top = found.setdefault(const, {})
                top[name] = max(top.get(name, 0), int(slot["max_level"]))
        _CACHE["slots"] = {const: tuple(sorted(levels.items())) for const, levels in found.items()}
    return _CACHE["slots"].get(str(map_const or "").removeprefix("MAP_"), ())  # type: ignore[union-attr]


def unmapped() -> dict[str, list[str]]:
    """(test side) The symbols that map to no facts name: species names, evolution targets and learnset moves."""
    names = _species()
    species = sorted(symbol for symbol, (name, _) in names.items() if name is None)
    targets = sorted({into for _, evos in names.values() for _, _, into in evos if names.get(into, (None,))[0] is None})
    raw = {}
    for entry in _load("learnsets.json")["species"]:
        for move in entry["level_up"]:
            if _move(move["move"]) is None:
                raw[str(move["move"])] = True
    return {"species": species, "evolution_targets": targets, "moves": sorted(raw)}
