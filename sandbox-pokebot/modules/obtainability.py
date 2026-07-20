"""
Obtainability classifier (#41, derivable half).

Given an internal species id, works out HOW that species is obtained in this
game, using only data derivable NOW: the wild encounter index (#9) and the
evolution graph in species.json. Everything runs in INTERNAL species ids
(`Species.index`) — `evolves_from` and `SpeciesEvolution.target_species_index`
are internal ids, so no id-space conversion is needed (see 11-LIVINGDEX-DESIGN
§0.1).

Categories this module CAN determine:
  - "wild"       — has >=1 wild encounter (hunt it).
  - "evolution"  — obtained by evolving a pre-evolution; the chain down to the
                   base species and the evolution method(s) are recorded.
  - "unknown"    — no wild encounter and no derivable evolution base that is
                   itself obtainable. These are the gift / static / roamer /
                   in-game-trade / event / genuinely-unobtainable species whose
                   authoritative lists are a separate research compile
                   (11-LIVINGDEX-DESIGN §Research Gaps). Marked honestly as
                   "unknown" here rather than guessed.

Nothing in here reads the save or the ROM directly beyond the already-cached
encounter index + the loaded species data, so it is cheap and unit-testable.
"""

from __future__ import annotations

import logging

from modules import encounter_index

_log = logging.getLogger("obtainability")

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
# Genuinely NOT automatable without a second game/link.
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
      {species_index, kind, automatable, needs_user, reason,
       # evolution-only extras:
       evolves_from, method, chain, base_index, base_kind}
    kind ∈ {"wild", "evolution", "unknown"}.
    """
    result = {
        "species_index": species_index,
        "kind": "unknown",
        "automatable": False,
        "needs_user": False,
        "reason": "",
    }

    if _has_wild(species_index):
        result.update(kind="wild", automatable=True, reason="wild encounter")
        return result

    from modules.pokemon import get_species_by_index

    try:
        species = get_species_by_index(species_index)
    except Exception:
        result["reason"] = "no data"
        return result

    pre = getattr(species, "evolves_from", None)
    if pre is not None and pre >= 0:
        chain = evolution_chain_to_base(species_index)
        base_index = chain[0] if chain else pre
        base_kind = "wild" if _has_wild(base_index) else "unknown"

        # Collect the methods for every step of the chain (base -> ... -> this).
        step_methods = []
        for i in range(len(chain) - 1):
            evo = _evolution_method(chain[i], chain[i + 1])
            step_methods.append(evo.method if evo else "unknown")
        method = step_methods[-1] if step_methods else "unknown"

        has_trade = any(m in _TRADE_METHODS for m in step_methods)
        has_special = any(m in (_ITEM_METHOD, _BEAUTY_METHOD) for m in step_methods)
        all_level = all(m in _AUTO_LEVEL_METHODS for m in step_methods) and step_methods
        # Automatable end-to-end only if the base is catchable now AND every
        # step is a plain level-up (no trade, no stone, no beauty).
        automatable = bool(all_level and base_kind == "wild")
        needs_user = bool(has_trade or has_special or base_kind != "wild")

        base_name = _species_name(base_index)
        label = _METHOD_LABELS.get(method, method)
        if base_kind == "wild":
            reason = f"evolve {base_name} ({label})"
        else:
            reason = f"evolve {base_name} — but {base_name} isn't wild-catchable here"
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
            reason=reason,
        )
        return result

    # No wild, no pre-evolution -> a base species that isn't wild in Emerald:
    # gift / static / roamer / in-game-trade / event / unobtainable-without-trade.
    # The authoritative split is the research compile — mark honestly.
    result.update(
        kind="unknown",
        reason="not wild here — special obtain (gift/static/trade/event); needs the obtainability research list",
    )
    return result


def plan_for(species_index: int) -> dict:
    """A living-dex plan for a target species:
      {kind, target_index, reason, automatable, needs_user}
    where `target_index` is the species the mode should actually hunt in the
    wild to make progress:
      - wild      -> the species itself.
      - evolution with a wild base -> the BASE species (hunt it; evolving is a
        later step / user action per `needs_user`).
      - otherwise -> target_index None (nothing to hunt; needs the research
        list or a manual step).
    """
    info = classify(species_index)
    if info["kind"] == "wild":
        return {
            "kind": "wild",
            "target_index": species_index,
            "reason": "wild",
            "automatable": True,
            "needs_user": False,
        }
    if info["kind"] == "evolution" and info.get("base_kind") == "wild":
        return {
            "kind": "evolution",
            "target_index": info["base_index"],
            "reason": info["reason"],
            "automatable": info["automatable"],
            "needs_user": info["needs_user"],
        }
    return {
        "kind": info["kind"] if info["kind"] != "wild" else "unknown",
        "target_index": None,
        "reason": info["reason"],
        "automatable": False,
        "needs_user": True,
    }
