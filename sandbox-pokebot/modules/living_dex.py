"""
Living-Dex orchestrator support (#23).

Derives an ordered list of target species to catch — by default every species
that HAS a wild encounter in this game and that the player does NOT yet own —
and persists the run's progress per profile so the "Living Dex (Custom)" bot
mode can work through it and resume across launches.

Species with no wild location (legendaries/statics/gift/trade/evolve-only) are
excluded from the auto list and reported under `skipped`, since this mode
catches only WILD encounters.
"""

from __future__ import annotations

import json
import logging

from modules.context import context
from modules import encounter_index

_log = logging.getLogger("living_dex")
RUN_FILE = "living_dex.json"


def owned_indices() -> set:
    """Species indices the player currently owns (from the in-game Pokédex)."""
    try:
        from modules.pokedex import get_pokedex

        return {species.index for species in get_pokedex().owned_species}
    except Exception as error:  # no save loaded yet, etc.
        _log.debug("owned_indices unavailable: %s", error)
        return set()


def is_owned(species_index: int) -> bool:
    return species_index in owned_indices()


def _all_wild_species_indices() -> list:
    """Every species with >=1 wild location, in National-Dex order."""
    index = encounter_index.get_encounter_index()
    from modules.pokemon import get_species_by_index

    entries = []
    for species_index in index.keys():
        try:
            species = get_species_by_index(int(species_index))
            entries.append((species.national_dex_number, int(species_index)))
        except Exception:
            continue
    entries.sort()
    return [sid for _, sid in entries]


def derive_targets(source: str = "uncaught_wild", explicit_names: list | None = None) -> dict:
    """Build a fresh run.

    - source "uncaught_wild" (default): all wild-catchable species not owned.
    - explicit_names: a user-picked list (names); non-wild/unknown ones are
      dropped into `skipped` with a reason.
    Returns {source, targets:[species_index], skipped:[{name,reason}], done:[]}.
    """
    skipped: list = []
    if explicit_names:
        from modules.pokemon import get_species_by_name

        targets: list = []
        for name in explicit_names:
            try:
                species = get_species_by_name(name)
            except Exception:
                skipped.append({"name": name, "reason": "unknown species"})
                continue
            if not encounter_index.locations_for_species(species.index):
                skipped.append({"name": name, "reason": "no wild location"})
                continue
            if species.index not in targets:
                targets.append(species.index)
        source = "custom_list"
    else:
        owned = owned_indices()
        targets = [sid for sid in _all_wild_species_indices() if sid not in owned]
    return {"source": source, "targets": targets, "skipped": skipped, "done": []}


def _run_path():
    if context.profile is None:
        return None
    return context.profile.path / RUN_FILE


def save_run(run: dict) -> None:
    path = _run_path()
    if path is None:
        return
    try:
        path.write_text(json.dumps(run), encoding="utf-8")
    except Exception as error:
        _log.warning("could not persist living-dex run: %s", error)


def load_run() -> dict | None:
    path = _run_path()
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("targets"), list):
            data.setdefault("done", [])
            data.setdefault("skipped", [])
            data.setdefault("source", "uncaught_wild")
            return data
    except Exception as error:
        _log.warning("could not read living-dex run (%s) — ignoring", error)
    return None


def clear_run() -> None:
    path = _run_path()
    if path is not None:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def progress(run: dict) -> tuple:
    """(#done, #total) for display. 'done' includes anything already owned."""
    total = len(run.get("targets", []))
    owned = owned_indices()
    done = sum(1 for sid in run.get("targets", []) if sid in owned or sid in run.get("done", []))
    return done, total


def next_target_index(run: dict) -> int | None:
    """The first target that is neither owned nor already marked done."""
    owned = owned_indices()
    done = set(run.get("done", []))
    for sid in run.get("targets", []):
        if sid not in owned and sid not in done:
            return sid
    return None
