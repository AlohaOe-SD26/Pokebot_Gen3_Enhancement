"""The AI's knowledge of THE WAY THROUGH A DARK CAVE (P11-1, 2026-11-11). Framework-free, read only.

WHAT IT ANSWERS: is a map DARK (one of the caves that need FLASH: the screen shows only a small lit circle round the
player), and, on a dark map, from the ladder the player ARRIVED by, which ladder (or exit) is the way on toward a map:
"on GRANITE CAVE B1F, from the ladder down from 1F, the ladder on toward STEVEN is the one at (28, 21), to B2F". What a
person who has played Emerald before knows at a GUIDE'S level (USER RULING 40: static game knowledge, the way through a
cave; RULING 45: coordinates kept, as the world folder's map file already keeps every warp's). It is NOT a map of the cave: no tile, no
wall, no step list. The AI still SEES only the lit circle (chapter 6 round 7's rule) and its world memory learns only what
it saw; this module never writes to it.

WHY (P11-1, `PROJECT KNOWLEDGE/ai-research-notes/2026-11-09-P11-1-DARK-CAVE-DIAGNOSIS.md`): in the dark the explorer could
not tell which of B1F's seven ladders leads on, so the B2F exit, 8 tiles north of the arrival, was lit only at the end of a
274-349-step blind search (#111), 2.6x to 11x slower than with the whole screen (#107).

THE WAY THROUGH (round 2, 2026-11-11): the first live A/B (#114) found the walk toward STEVEN GOAL-LESS ("by looking
around: not told yet": the intent has no goal map), so a way asked for only by a goal never fired. `way_through` answers the
way a guide calls "the way through the cave" from the ladder arrived by, with no goal: the way toward the farthest map that
arrival leads to (GRANITE CAVE's far end, STEVEN's room, from the entrance side). (Round 2b) NEVER STRAIGHT BACK: where
that way would be the ladder the player came by (a pocket, a dead end, the far end behind them) the file marks none and
this answers None, so the AI's own explorer decides there, as before P11-1 (marks that stepped back made a goal-less walk
bounce between two ladders for ever on VICTORY ROAD: `gates/extract_ways.py`).

WHAT IT READS, AND NOTHING ELSE: `world/ways.json` (written by the test side's `gates/extract_ways.py` from the pinned
decomp's layouts), once, cached; of it each dark map's `id` and its `ways` (`from`, `take`, `leads_to`, `toward`,
`through`). The `_`-keys (the sources, the extractor's walk lengths) are the developers' and are never read.
`gates/check_fairness.py` declares this module the file's only LOADER and classifies every key path of it (RULE B).

A MISSING FILE IS NO DARK MAP: without `world/ways.json` every answer is "not dark" / None, which is the AI's behaviour
before P11-1, exactly (the live A/B's FAULT arm is this code with the file removed).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "Way",
    "dark",
    "way_on",
    "way_through",
]

_FILE = Path(__file__).parent / "world" / "ways.json"
_CACHE: dict[str, dict] = {}


@dataclass(frozen=True)
class Way:
    """One way on: from the ladder arrived by (`arrival`), the warp to take (`take`, its tile on this map) leads to map
    `leads_to`, toward map `toward` (consts as the eyes name them: `MAP_` dropped)."""

    arrival: tuple[int, int]
    take: tuple[int, int]
    leads_to: str
    toward: str


def _ways() -> dict[str, list[tuple[tuple[int, int], tuple[int, int], str, tuple[str, ...], str | None]]]:
    """Each dark map's const -> its ways as (arrival, take, leads_to, toward..., the far end it is the way through toward or
    None), read once; {} when the file is missing."""
    if "ways" not in _CACHE:
        found: dict[str, list] = {}
        if _FILE.is_file():
            data = json.loads(_FILE.read_text(encoding="utf-8"))
            for entry in data["maps"]:
                const = str(entry["id"]).removeprefix("MAP_")
                found[const] = [((int(way["from"][0]), int(way["from"][1])), (int(way["take"][0]), int(way["take"][1])),
                                 str(way["leads_to"]).removeprefix("MAP_"),
                                 tuple(str(name).removeprefix("MAP_") for name in way["toward"]),
                                 str(way["through"]).removeprefix("MAP_") if way["through"] else None)
                                for way in entry["ways"]]
        _CACHE["ways"] = found
    return _CACHE["ways"]


def dark(const: str | None) -> bool:
    """Is map `const` (the eyes' map const) one of the dark caves the file holds (`requires_flash`)? False for any other
    map, for None, and for every map when the file is missing."""
    return (const or "") in _ways()


def way_on(const: str | None, arrival: tuple[int, int] | None, wanted: Callable[[str], bool]) -> Way | None:
    """On dark map `const`, from the ladder at `arrival` (where the player came onto the map), the way on toward the first
    map `wanted(name)` accepts among the maps the file says this arrival leads toward (in the file's order: its ways by the
    ladder to take, each one's maps sorted); None off a dark map, from an arrival the file does not hold (a fall through a
    floor, a scene), or when no map it leads toward is wanted."""
    if not dark(const) or arrival is None:
        return None
    here = (int(arrival[0]), int(arrival[1]))
    for start, take, leads_to, toward, _through in _ways()[const or ""]:
        if start != here:
            continue
        for name in toward:
            if wanted(name):
                return Way(here, take, leads_to, name)
    return None


def way_through(const: str | None, arrival: tuple[int, int] | None) -> Way | None:
    """(round 2) On dark map `const`, from the ladder at `arrival`, THE WAY THROUGH the cave with no goal: the way toward the
    farthest map that arrival leads to (`Way.toward` names it); None off a dark map or from an arrival the file does not
    hold."""
    if not dark(const) or arrival is None:
        return None
    here = (int(arrival[0]), int(arrival[1]))
    for start, take, leads_to, _toward, through in _ways()[const or ""]:
        if start == here and through is not None:
            return Way(here, take, leads_to, through)
    return None
