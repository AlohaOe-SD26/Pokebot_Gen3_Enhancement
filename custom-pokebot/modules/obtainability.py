"""
Obtainability classifier (#41).

Given an internal species id, works out HOW that species is obtained in this
game. Two data layers:

  1. DERIVABLE (any ROM, no research needed):
       - "wild"       — has >=1 wild encounter (hunt it) — from the encounter index (#9).
       - "evolution"  — obtained by evolving a pre-evolution; the chain down to the
                        base species and the evolution method(s) are recorded
                        (from species.json internal-id evolution graph).
  2. COMPILED + FACT-CHECKED (Emerald only — `modules/data/emerald_obtainability.json`):
     the base-non-wild species split into honest categories:
       - "gift"          — starter / fossil / NPC gift (bot: Static Gift / Starters resets).
       - "static"        — fixed interactable/legendary encounter (bot: Static Soft Resets).
       - "roamer"        — the roaming Eon Pokemon (Latias/Latios per the TV answer).
       - "ingame_trade"  — received via an in-game NPC trade (none in Emerald rescue an
                           otherwise-unobtainable species; see the data file's _ingame_trades).
       - "breeding"      — a baby obtained by breeding an obtainable evolved form.
       - "special"       — obtainable by a non-table wild mechanic (Feebas, Route 119 tiles).
       - "event"         — obtainable only via an event distribution / ticket item.
       - "unobtainable"  — no Emerald obtain path at all (trade from another game).

Everything runs in INTERNAL species ids (`Species.index`) — `evolves_from` and
`SpeciesEvolution.target_species_index` are internal ids, so no id-space
conversion is needed (see 11-LIVINGDEX-DESIGN §0.1). The Emerald override is
keyed by National Dex number in the data file and resolved to internal ids at
load. For non-Emerald ROMs the override is skipped and base-non-wild species
stay "unknown" (honest — those lists were only compiled for Emerald).

`emerald_reachable` is the honest "can you get this in Emerald WITHOUT trading?"
flag used for the second living-dex denominator. For an evolution it is derived
recursively: the base must be reachable AND no step may be a trade evolution.

Nothing here reads the save; it uses the cached encounter index + loaded species
data + the static override JSON, so it is cheap and unit-testable.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from modules import encounter_index

_log = logging.getLogger("obtainability")

# Categories the compiled Emerald override can assign to a base-non-wild species.
OVERRIDE_KINDS = ("gift", "static", "roamer", "ingame_trade", "breeding", "special", "event", "unobtainable")
# All kinds classify() can return.
ALL_KINDS = ("wild", "evolution") + OVERRIDE_KINDS + ("unknown",)

# Evolution methods that are fully automatable given the base mon + grinding
# (raise to a level / trigger a level-up condition). The which-result splits
# (Wurmple/Tyrogue/Nincada) are automatable but the RESULT is PV/IV/slot
# dependent — flagged in the reason, not over-promised.
_AUTO_LEVEL_METHODS = {
    "level",
    "level_with_friendship",
    "level_with_friendship_during_day",
    "level_with_friendship_during_night",
    "level_with_attack_lower_than_defence",
    "level_with_attack_greater_than_defence",
    "level_with_attack_equal_to_defence",
    "level_silcoon",
    "level_cascoon",
    "level_with_empty_slot_in_party",
}
# Genuinely NOT automatable without a second game/link — and NOT obtainable in
# Emerald without trading (so they drag emerald_reachable to False).
_TRADE_METHODS = {"trade", "trade_with_item"}
# Automatable only once a "use evolution stone" / Pokéblock-beauty helper exists.
_ITEM_METHOD = "item"
_BEAUTY_METHOD = "level_with_beauty"

_METHOD_LABELS = {
    "level": "level up",
    "level_with_friendship": "raise friendship",
    "level_with_friendship_during_day": "friendship (day)",
    "level_with_friendship_during_night": "friendship (night)",
    "level_with_attack_lower_than_defence": "level up (Atk<Def)",
    "level_with_attack_greater_than_defence": "level up (Atk>Def)",
    "level_with_attack_equal_to_defence": "level up (Atk=Def)",
    "level_silcoon": "level up (Silcoon branch)",
    "level_cascoon": "level up (Cascoon branch)",
    "level_with_empty_slot_in_party": "level up (empty slot + spare Ball)",
    "level_with_beauty": "max Beauty (blue Pokéblocks)",
    "item": "use an evolution stone",
    "trade": "trade",
    "trade_with_item": "trade holding an item",
}


# --------------------------------------------------------------------------
# Compiled Emerald override (base-non-wild species -> honest category)
# --------------------------------------------------------------------------
_OVERRIDE_PATH = Path(__file__).parent / "data" / "emerald_obtainability.json"


@lru_cache(maxsize=1)
def _load_override_raw() -> dict:
    """Load the National-Dex-keyed override JSON once. {natdex(int): entry}."""
    try:
        payload = json.loads(_OVERRIDE_PATH.read_text(encoding="utf-8"))
        species = payload.get("species", {})
        return {int(nd): entry for nd, entry in species.items()}
    except (OSError, ValueError, TypeError) as error:
        _log.warning("could not load emerald obtainability override: %s", error)
        return {}


def _is_emerald() -> bool:
    try:
        from modules.context import context

        return bool(context.rom is not None and context.rom.is_emerald)
    except Exception:
        return False


@lru_cache(maxsize=1)
def _override_by_internal_id() -> dict:
    """The override remapped to internal species ids — Emerald only. {index: entry}."""
    if not _is_emerald():
        return {}
    from modules.pokemon import get_species_by_national_dex

    out = {}
    for natdex, entry in _load_override_raw().items():
        try:
            out[get_species_by_national_dex(natdex).index] = entry
        except Exception:
            continue
    return out


def override_for(species_index: int) -> dict | None:
    """The compiled override entry for a species, or None (not overridden / non-Emerald)."""
    return _override_by_internal_id().get(species_index)


def ingame_trades() -> list:
    """The documented Emerald in-game NPC trades (metadata; not a per-species category)."""
    try:
        payload = json.loads(_OVERRIDE_PATH.read_text(encoding="utf-8"))
        return list(payload.get("meta", {}).get("_ingame_trades", []))
    except (OSError, ValueError, TypeError):
        return []


def _has_wild(species_index: int) -> bool:
    try:
        return bool(encounter_index.locations_for_species(species_index))
    except Exception:
        return False


def evolution_chain_to_base(species_index: int) -> list:
    """Walk `evolves_from` down to the base species. Returns [base, …, species]
    (base first). Cycle/length guarded (Gen-3 chains are <= 3)."""
    from modules.pokemon import get_species_by_index

    chain = [species_index]
    seen = {species_index}
    current = species_index
    for _ in range(6):
        try:
            species = get_species_by_index(current)
        except Exception:
            break
        pre = getattr(species, "evolves_from", None)
        if pre is None or pre < 0 or pre in seen:
            break
        chain.append(pre)
        seen.add(pre)
        current = pre
    chain.reverse()
    return chain


def _evolution_method(pre_index: int, target_index: int):
    """The SpeciesEvolution on `pre_index` whose result is `target_index`."""
    from modules.pokemon import get_species_by_index

    try:
        pre = get_species_by_index(pre_index)
        for evo in pre.evolutions:
            if int(evo.target_species_index) == int(target_index):
                return evo
    except Exception:
        pass
    return None


def _species_name(species_index: int) -> str:
    from modules.pokemon import get_species_by_index

    try:
        return get_species_by_index(species_index).name
    except Exception:
        return f"#{species_index}"


def classify(species_index: int) -> dict:
    """Classify how `species_index` is obtained. Returns a dict:
      {species_index, kind, automatable, needs_user, emerald_reachable, reason, note,
       # evolution-only extras:
       evolves_from, method, chain, base_index, base_kind, step_methods}
    kind ∈ ALL_KINDS. `emerald_reachable` answers "obtainable in Emerald without trading".
    """
    result = {
        "species_index": species_index,
        "kind": "unknown",
        "automatable": False,
        "needs_user": False,
        "emerald_reachable": False,
        "reason": "",
        "note": "",
    }

    # 1. Wild — derivable from the encounter index.
    if _has_wild(species_index):
        result.update(kind="wild", automatable=True, emerald_reachable=True, reason="wild encounter")
        return result

    from modules.pokemon import get_species_by_index

    try:
        species = get_species_by_index(species_index)
    except Exception:
        result["reason"] = "no data"
        return result

    # 2. Evolution — derivable from species.json.
    pre = getattr(species, "evolves_from", None)
    if pre is not None and pre >= 0:
        chain = evolution_chain_to_base(species_index)
        base_index = chain[0] if chain else pre

        step_methods = []
        for i in range(len(chain) - 1):
            evo = _evolution_method(chain[i], chain[i + 1])
            step_methods.append(evo.method if evo else "unknown")
        method = step_methods[-1] if step_methods else "unknown"

        # The base's own obtainability (recursive — resolves override/wild).
        base_info = classify(base_index)
        base_kind = base_info["kind"]

        has_trade = any(m in _TRADE_METHODS for m in step_methods)
        has_special = any(m in (_ITEM_METHOD, _BEAUTY_METHOD) for m in step_methods)
        all_level = all(m in _AUTO_LEVEL_METHODS for m in step_methods) and step_methods
        # Fully automatable only if the base is wild-catchable AND every step is a
        # plain level-up (no trade, no stone, no beauty).
        automatable = bool(all_level and base_kind == "wild")
        needs_user = bool(has_trade or has_special or base_kind != "wild")
        # Obtainable in Emerald without trading iff the base is reachable and no
        # step needs a trade. (item/beauty/friendship are reachable — just effort.)
        emerald_reachable = bool(base_info["emerald_reachable"] and not has_trade)

        base_name = _species_name(base_index)
        label = _METHOD_LABELS.get(method, method)
        if base_kind == "wild":
            reason = f"evolve {base_name} ({label})"
        elif base_info["emerald_reachable"]:
            reason = f"evolve {base_name} ({label}) — {base_name} via {base_kind}"
        else:
            reason = f"evolve {base_name} — but {base_name} isn't obtainable in Emerald ({base_kind})"
        if has_trade:
            reason += " · trade needed (manual)"

        result.update(
            kind="evolution",
            evolves_from=pre,
            method=method,
            chain=chain,
            base_index=base_index,
            base_kind=base_kind,
            step_methods=step_methods,
            automatable=automatable,
            needs_user=needs_user,
            emerald_reachable=emerald_reachable,
            reason=reason,
        )
        return result

    # 3. Base species, not wild — consult the compiled Emerald override.
    entry = override_for(species_index)
    if entry is not None:
        kind = entry.get("kind", "unknown")
        result.update(
            kind=kind,
            automatable=bool(entry.get("automatable", False)),
            needs_user=bool(entry.get("needs_user", True)),
            emerald_reachable=bool(entry.get("emerald_reachable", False)),
            reason=kind,
            note=entry.get("note", ""),
        )
        return result

    # 4. No wild, no pre-evolution, no override (e.g. a non-Emerald ROM, or a gap):
    # honestly "unknown" — the special-obtain research list only covers Emerald.
    result.update(
        kind="unknown",
        reason="not wild here — special obtain (gift/static/trade/event); needs the obtainability research list",
    )
    return result


def plan_for(species_index: int) -> dict:
    """A living-dex plan for a target species:
      {kind, target_index, reason, note, automatable, needs_user, emerald_reachable,
       wild_huntable}
    `target_index` is the species the mode should actually hunt IN THE WILD to make
    progress (None => must NOT be wild-hunted):
      - wild                        -> the species itself.
      - evolution with a wild base  -> the BASE species (hunt it; evolve is a later step).
      - gift/static/roamer          -> None; flagged for the reset bot (see `automatable`).
      - breeding/special/event/
        ingame_trade/unobtainable   -> None; manual or blocked.
    `wild_huntable` is True only for wild + evolution-with-wild-base — the ONLY
    cases the living-dex wild hunter should ever target. This is the obtainability
    gate: the bot never wild-hunts an unobtainable/event/trade/gift/static species.
    """
    info = classify(species_index)
    kind = info["kind"]

    if kind == "wild":
        return {
            "kind": "wild", "target_index": species_index, "reason": "wild", "note": "",
            "automatable": True, "needs_user": False, "emerald_reachable": True,
            "wild_huntable": True,
        }
    if kind == "evolution" and info.get("base_kind") == "wild":
        return {
            "kind": "evolution", "target_index": info["base_index"], "reason": info["reason"],
            "note": "", "automatable": info["automatable"], "needs_user": info["needs_user"],
            "emerald_reachable": info["emerald_reachable"], "wild_huntable": True,
        }

    # Everything else is NOT a wild hunt. Surface it honestly, never silently skip.
    return {
        "kind": kind if kind != "wild" else "unknown",
        "target_index": None,
        "reason": info["reason"],
        "note": info.get("note", ""),
        "automatable": info["automatable"],
        "needs_user": info["needs_user"],
        "emerald_reachable": info["emerald_reachable"],
        "wild_huntable": False,
    }


# --------------------------------------------------------------------------
# Census / denominators (for the dashboard's two completion metrics)
# --------------------------------------------------------------------------
def _all_real_species_indices() -> list:
    """The 386 real National-Dex species as internal ids (excludes the index-0
    placeholder that shares Mew's dex number, and the '?' form placeholders)."""
    from modules.pokemon import get_species_by_national_dex

    return [get_species_by_national_dex(n).index for n in range(1, 387)]


def census() -> dict:
    """Full obtainability census over the 386 National-Dex species:
      {
        "total": 386,
        "by_kind": {kind: count, ...},           # sums to 386
        "emerald_reachable": int,                # obtainable in Emerald WITHOUT trading
        "not_reachable": int,
      }
    Use `by_kind` for the category breakdown and `emerald_reachable` as the second
    living-dex denominator (M / obtainable-in-Emerald) alongside N / 386.
    """
    from collections import Counter

    kinds = Counter()
    reachable = 0
    for i in _all_real_species_indices():
        info = classify(i)
        kinds[info["kind"]] += 1
        if info["emerald_reachable"]:
            reachable += 1
    total = sum(kinds.values())
    return {
        "total": total,
        "by_kind": dict(kinds),
        "emerald_reachable": reachable,
        "not_reachable": total - reachable,
    }
