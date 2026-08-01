"""Rebuild a party from another PROCESS's status blob (ENDLESS LOOP x4, #24-x4).

The dashboard's party strip, party tab and hover tooltip all read attributes off real
`Pokemon` objects. During an x4 batch the party the user wants to see belongs to a LANE —
a different process, with its own `context` and its own emulator — so there is no
`Pokemon` object to hand them.

Rather than fork the party renderer, this module rebuilds lightweight stand-ins that
expose the exact attribute surface that UI reads, from the JSON `modules/gui/tile_child.py`
publishes. The renderer then works unchanged.

‼ THE ATTRIBUTE SURFACE IS THE CONTRACT. Measured off the real code, not guessed:
    strip    (dashboard_gui 1145-1240): is_egg, is_shiny, name, species_name_for_stats
    tab row  (dashboard_gui 3209-3290): + current_hp, total_hp, level, status_condition,
                                          is_anti_shiny, exp_fraction_to_next_level
    tooltip  (dashboard_gui 1530-1700): + ability, gender, held_item, ivs, moves, nature,
                                          poke_ball, species(.types)
If the party UI starts reading something new, add it HERE and in `_mon_payload()` — a
missing attribute degrades to a placeholder rather than raising, so the failure is quiet.

‼ `status_condition` MUST be the real enum member. `dashboard_gui:3239` compares it with
`is not StatusCondition.Healthy` — an IDENTITY test, which any string or look-alike fails,
making every healthy Pokémon render as if it had a status condition.
"""

from __future__ import annotations

from typing import Any


def mon_payload(mon) -> dict:
    """Serialise ONE Pokémon to the JSON shape `RemotePokemon` rebuilds.

    Every field is read independently: a single unreadable attribute (party memory caught
    mid-write, an unusual species) must cost that FIELD, not the whole team.

    Two consumers, deliberately sharing one shape: `modules/gui/tile_child.py` publishes it
    every frame so the dashboard's party strip can follow the focused lane, and
    `modules/badge_log.py` freezes it at the instant a badge is earned.
    """

    def g(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    return {
        "name": g(lambda: str(mon.name)),
        "species": g(lambda: str(mon.species_name_for_stats)),
        "level": g(lambda: int(mon.level), 0),
        "hp": g(lambda: int(mon.current_hp), 0),
        "max_hp": g(lambda: int(mon.total_hp), 0),
        "egg": g(lambda: bool(mon.is_egg), False),
        "shiny": g(lambda: bool(mon.is_shiny), False),
        "anti_shiny": g(lambda: bool(mon.is_anti_shiny), False),
        "status": g(lambda: mon.status_condition.name, "Healthy"),
        "xp": g(lambda: round(float(mon.exp_fraction_to_next_level), 4), 0.0),
        "gender": g(lambda: mon.gender),
        "ball": g(lambda: mon.poke_ball.name),
        "nature": g(lambda: mon.nature.name),
        "ability": g(lambda: mon.ability.name),
        "item": g(lambda: mon.held_item.name if mon.held_item is not None else None),
        "types": g(lambda: [t.name for t in mon.species.types], []),
        "ivs": g(lambda: [mon.ivs.hp, mon.ivs.attack, mon.ivs.defence,
                          mon.ivs.special_attack, mon.ivs.special_defence, mon.ivs.speed]),
        "moves": g(lambda: [m.move.name for m in mon.moves if m is not None], []),
    }


class _Named:
    """Stands in for the small name-carrying objects (ball, nature, ability, item, type)."""

    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


class _IVs:
    __slots__ = ("hp", "attack", "defence", "special_attack", "special_defence", "speed")

    def __init__(self, values: list[int]):
        padded = list(values) + [0] * (6 - len(values))
        (self.hp, self.attack, self.defence,
         self.special_attack, self.special_defence, self.speed) = padded[:6]


class _Move:
    """The tooltip reads `move.move.name`, so the nesting is preserved."""

    __slots__ = ("move",)

    def __init__(self, name: str):
        self.move = _Named(name)


class _Species:
    __slots__ = ("name", "types")

    def __init__(self, name: str, types: list[str]):
        self.name = name
        self.types = [_Named(t) for t in types]


class RemotePokemon:
    """A party member belonging to another process, shaped like the real thing."""

    def __init__(self, data: dict[str, Any]):
        self._data = data
        species_name = data.get("species") or data.get("name") or "?"

        self.name = data.get("name") or species_name
        self.species_name_for_stats = species_name
        self.level = int(data.get("level") or 0)
        self.current_hp = int(data.get("hp") or 0)
        self.total_hp = int(data.get("max_hp") or 0)
        self.is_egg = bool(data.get("egg"))
        self.is_shiny = bool(data.get("shiny"))
        self.is_anti_shiny = bool(data.get("anti_shiny"))
        self.is_empty = False
        self.exp_fraction_to_next_level = float(data.get("xp") or 0.0)
        self.gender = data.get("gender")
        self.species = _Species(species_name, data.get("types") or [])
        self.poke_ball = _Named(data.get("ball") or "Poké Ball")
        self.nature = _Named(data.get("nature") or "?")
        self.ability = _Named(data.get("ability") or "?")
        self.held_item = _Named(data["item"]) if data.get("item") else None
        self.ivs = _IVs(data.get("ivs") or [])
        self.moves = [_Move(name) for name in (data.get("moves") or [])]

    @property
    def status_condition(self):
        """The REAL enum member — see the identity-comparison note in the module docstring."""
        from modules.pokemon import StatusCondition

        try:
            return StatusCondition[self._data.get("status") or "Healthy"]
        except Exception:
            return StatusCondition.Healthy

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<RemotePokemon {self.name} L{self.level} {self.current_hp}/{self.total_hp}>"


def party_from_status(status: dict | None) -> list[RemotePokemon]:
    """Build a party list from a lane's status blob. Never raises; unknown shapes -> []."""
    if not isinstance(status, dict):
        return []
    team = status.get("team")
    if not isinstance(team, list):
        return []
    party: list[RemotePokemon] = []
    for entry in team:
        if not isinstance(entry, dict):
            continue
        try:
            party.append(RemotePokemon(entry))
        except Exception:
            continue
    return party
