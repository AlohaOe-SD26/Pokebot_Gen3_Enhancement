"""
Reverse wild-encounter index for the Hunt Planner (#9).

Answers "where do I hunt species X?" by inverting every map's wild-encounter
tables into: species -> [ {map, map_name, method, rate%, level range} ].

Data source: modules.map.get_wild_encounters_for_map(), which reads the
ROM's `gWildMonHeaders` (land/surf/rock-smash/old+good+super rod tables with
per-slot rates). Building therefore needs a running emulator with the ROM
loaded (same constraint as warp_graph). The result is cached per-ROM to
cache/encounter_index_<rom>.json so later launches are instant; a
corrupt/missing/old cache is transparently rebuilt (mirrors the warp_graph
fix: any non-dict payload -> rebuild, never crash).

The "rate" is the summed per-slot percentage for that species within the
method's table on that map — i.e. "given a <method> encounter here, the
chance it is this species". That is the right number for ranking hunt spots.
Live counts (caught/shiny) are NOT part of this static index.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from modules.context import context
from modules.runtime import get_base_path

_log = logging.getLogger("hunt_planner")

_CACHE_VERSION = 1

# (WildEncounterList attribute, human method label). Order = display priority.
_METHODS = [
    ("land_encounters", "Grass"),
    ("surf_encounters", "Surfing"),
    ("rock_smash_encounters", "Rock Smash"),
    ("old_rod_encounters", "Old Rod"),
    ("good_rod_encounters", "Good Rod"),
    ("super_rod_encounters", "Super Rod"),
]

# Encounter method -> recommended bot mode (only offered if the mode exists;
# see recommended_mode_for_method()).
_METHOD_MODE = {
    "Grass": "Spin",
    "Surfing": "Spin",          # Spin also triggers encounters while surfing
    "Rock Smash": "Rock Smash",
    "Old Rod": "Fishing",
    "Good Rod": "Fishing",
    "Super Rod": "Fishing",
}

_index: dict | None = None  # {species_index(int): [location dict, ...]}


def _cache_path() -> Path:
    rom_id = getattr(context.rom, "id", "unknown")
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(rom_id))
    cache_dir = get_base_path() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"encounter_index_{safe}.json"


def _map_name(map_key: tuple[int, int]) -> str:
    try:
        from modules.map_data import get_map_enum

        return get_map_enum(map_key).pretty_name
    except Exception:
        return f"Map {map_key[0]}.{map_key[1]}"


def _build_index() -> dict:
    """Read every map's encounter tables from the ROM and invert them."""
    from modules import map as map_module

    # One call populates the whole per-ROM cache (it walks gWildMonHeaders).
    map_module.get_wild_encounters_for_map(0, 0)
    per_rom = map_module._wild_encounters_cache.get(context.rom.id, {})

    index: dict[int, list] = {}
    for map_key, wild_list in per_rom.items():
        if wild_list is None:
            continue
        map_name = _map_name(map_key)
        for attr, method in _METHODS:
            encounters = getattr(wild_list, attr, None) or []
            # Aggregate multiple slots of the same species within this method.
            agg: dict[int, dict] = {}
            for enc in encounters:
                sid = enc.species.index
                slot = agg.setdefault(
                    sid,
                    {"rate": 0, "min_level": enc.min_level, "max_level": enc.max_level, "name": enc.species.name},
                )
                slot["rate"] += int(enc.encounter_rate)
                slot["min_level"] = min(slot["min_level"], enc.min_level)
                slot["max_level"] = max(slot["max_level"], enc.max_level)
            for sid, slot in agg.items():
                index.setdefault(sid, []).append(
                    {
                        "map": [map_key[0], map_key[1]],
                        "map_name": map_name,
                        "method": method,
                        "rate": slot["rate"],
                        "min_level": slot["min_level"],
                        "max_level": slot["max_level"],
                    }
                )
    # Sort each species' locations best-rate-first, then by name for stability.
    for locations in index.values():
        locations.sort(key=lambda loc: (-loc["rate"], loc["map_name"], loc["method"]))
    return index


def _save_cache(index: dict) -> None:
    try:
        payload = {"version": _CACHE_VERSION, "rom": getattr(context.rom, "id", ""), "index": index}
        _cache_path().write_text(json.dumps(payload), encoding="utf-8")
    except OSError as error:
        _log.warning("could not write encounter-index cache: %s", error)


def _load_cache() -> dict | None:
    path = _cache_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # Guard against a non-dict / partial / hand-edited file (warp_graph lesson).
    if not isinstance(payload, dict) or payload.get("version") != _CACHE_VERSION:
        return None
    raw = payload.get("index")
    if not isinstance(raw, dict):
        return None
    try:
        return {int(sid): locations for sid, locations in raw.items()}
    except (ValueError, TypeError, AttributeError):
        return None


def get_encounter_index(rebuild: bool = False) -> dict:
    """Return (building/caching on first use) the species->locations index."""
    global _index
    if _index is not None and not rebuild:
        return _index
    if not rebuild:
        cached = _load_cache()
        if cached is not None:
            _index = cached
            return _index
    _index = _build_index()
    _save_cache(_index)
    return _index


def _resolve_species_index(species) -> int | None:
    # NOTE: check str BEFORE the `.index` attribute path — `str` has a
    # built-in `.index` method, so a name string would otherwise resolve to
    # that method instead of a species id.
    if isinstance(species, bool):
        return None
    if isinstance(species, int):
        return species
    if isinstance(species, str):
        try:
            from modules.pokemon import get_species_by_name

            return get_species_by_name(species).index
        except Exception:
            return None
    if hasattr(species, "index"):  # Species object
        return species.index
    return None


def locations_for_species(species) -> list:
    """All wild locations for a species, best-rate first. [] if none (e.g.
    legendaries/statics/gift/evolve-only Pokémon have no wild table)."""
    sid = _resolve_species_index(species)
    if sid is None:
        return []
    return list(get_encounter_index().get(sid, []))


def recommended_mode_for_method(method: str, available_modes: list | None = None) -> str:
    """Map an encounter method to the best EXISTING bot mode, else 'Manual'."""
    mode = _METHOD_MODE.get(method, "Manual")
    if available_modes is None:
        try:
            from modules.modes import get_bot_mode_names

            available_modes = get_bot_mode_names()
        except Exception:
            available_modes = []
    return mode if mode in available_modes else "Manual"


def index_stats() -> dict:
    """Small summary for validation/reporting."""
    index = get_encounter_index()
    return {
        "species_with_locations": len(index),
        "total_location_rows": sum(len(v) for v in index.values()),
    }
