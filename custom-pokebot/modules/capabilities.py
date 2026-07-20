"""
Player capability gate (#42, easy half).

Reads from the loaded save what the player can currently DO, so hunt / living-
dex can skip (defer) a target whose encounter method needs a capability the
player lacks — with a clear, human reason — instead of walking somewhere it
cannot trigger the encounter.

Only the CAPABILITY half is here (rods / field moves / badges — all directly
save-readable). Full map reachability through HM-gated terrain (Cut trees, Surf
water on the PATH, etc.) is the harder v2 (11-LIVINGDEX-DESIGN §#42 "HARD"):
the warp-graph navigator models warps only, so this module does not attempt it.

Design principle: be PERMISSIVE when unsure — an unknown method returns allowed
so we never wrongly skip a catchable species; we only defer when a required
capability is clearly absent.

Emerald field-move badge prerequisites (fixed facts, 11-LIVINGDEX-DESIGN §#42):
  Surf       -> Balance Badge (BADGE05_GET)
  Rock Smash -> Dynamo  Badge (BADGE03_GET)
"""

from __future__ import annotations

import logging

_log = logging.getLogger("capabilities")

_SURF_BADGE = "BADGE05_GET"
_ROCK_SMASH_BADGE = "BADGE03_GET"
_RODS = ("Old Rod", "Good Rod", "Super Rod")


def _has_badge(flag_name: str) -> bool:
    try:
        from modules.memory import get_event_flag

        return bool(get_event_flag(flag_name))
    except Exception as error:
        _log.debug("badge read failed (%s): %s", flag_name, error)
        return False


def _party_has_move(move_name: str) -> bool:
    try:
        from modules.pokemon_party import get_party

        return get_party().first_pokemon_with_move(move_name) is not None
    except Exception as error:
        _log.debug("party move read failed (%s): %s", move_name, error)
        return False


def _has_item(item_name: str) -> bool:
    try:
        from modules.items import get_item_bag, get_item_by_name

        return get_item_bag().quantity_of(get_item_by_name(item_name)) > 0
    except Exception as error:
        _log.debug("item read failed (%s): %s", item_name, error)
        return False


def can_use_method(method: str) -> tuple:
    """(allowed: bool, reason_if_not: str) for an encounter method.

    Recognised methods: Grass / Walking, Surfing, Old Rod, Good Rod, Super Rod,
    Rock Smash. Unknown methods are allowed (permissive), so a species is never
    wrongly deferred.
    """
    name = (method or "").strip()

    if name in ("", "Grass", "Walking", "Land"):
        return True, ""

    if name == "Surfing":
        if not _party_has_move("Surf"):
            return False, "needs Surf on a party Pokémon"
        if not _has_badge(_SURF_BADGE):
            return False, "needs the Balance Badge to use Surf"
        return True, ""

    if name in _RODS:
        if not _has_item(name):
            return False, f"needs the {name}"
        return True, ""

    if name == "Rock Smash":
        if not _party_has_move("Rock Smash"):
            return False, "needs Rock Smash on a party Pokémon"
        if not _has_badge(_ROCK_SMASH_BADGE):
            return False, "needs the Dynamo Badge to use Rock Smash"
        return True, ""

    # Unknown / other -> permissive.
    return True, ""


def capability_report() -> dict:
    """A snapshot of the player's relevant capabilities (for the GUI / logging /
    live-verification). Every read is guarded — safe to call even without a save
    (returns all-False)."""
    return {
        "surf": _party_has_move("Surf"),
        "balance_badge": _has_badge(_SURF_BADGE),
        "rock_smash": _party_has_move("Rock Smash"),
        "dynamo_badge": _has_badge(_ROCK_SMASH_BADGE),
        "old_rod": _has_item("Old Rod"),
        "good_rod": _has_item("Good Rod"),
        "super_rod": _has_item("Super Rod"),
    }
