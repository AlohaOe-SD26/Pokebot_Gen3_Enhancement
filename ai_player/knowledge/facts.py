"""The game's FACTS a person knows (build step 4), read from the AI's own knowledge files. Framework-free.

WHY THESE FACTS AND NO OTHERS (HUMAN-PLAY-DESIGN pillar 3: "battle with TYPE advantages, both the Pokemon's types and the
MOVES' types, and account for RECOIL damage when choosing moves"): a person knows the type chart, what a move does as the
game describes it (its type, power, accuracy, PP, whether it hurts its user), and a species' types. They do not know a
wild Pokemon's exact HP, its moves before it uses them, or what a trainer will send out next: none of that is here, and
the eyes show the foe's HP only as its bar (`eyes/observation.py`). (Step 4.1 rounds 1-3, the hidden-information findings)
`species.json` still CARRIES each species' base stats, catch rate and experience yield (the extraction and the pret check
keep the whole record), but the decider reads a species' TYPES and NAME only: the ball is chosen by what is seen, not the
catch rate (round 1), and a foe's damage is guessed from a typical Pokemon of its level, not its base stats (round 3,
`brain/battle.py` TYPICAL_BASE, whose numbers `gates/test_battle.py` checks against the median of this file).

The files (`types.json`, `moves.json`, `species.json` next to this module) are extracted by the TEST-side
`gates/extract_knowledge.py` from the bot's game-fact data and checked entry by entry against pret/pokeemerald by
`gates/verify_knowledge.py`; each carries its provenance. This module only READS them, once.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "MoveFact",
    "SpeciesFact",
    "category_of",
    "move_fact",
    "move_named",
    "provenance",
    "species_fact",
    "species_named",
    "stab",
    "type_multiplier",
]

_FOLDER = Path(__file__).parent
_CACHE: dict[str, dict] = {}


def _load(name: str) -> dict:
    if name not in _CACHE:
        _CACHE[name] = json.loads((_FOLDER / name).read_text(encoding="utf-8"))
    return _CACHE[name]


@dataclass(frozen=True)
class MoveFact:
    """A move as the game describes it (`moves.json`)."""

    name: str
    type: str
    power: int
    accuracy: int  # percent
    never_misses: bool
    pp: int
    effect: str
    priority: int
    target: str  # SELECTED, BOTH (the two foes), FOES_AND_ALLY, USER, ... (`include/constants/battle.h` MOVE_TARGET_*)
    category: str  # physical, special (Gen 3: by type), status (no power)
    recoil_kind: str | None  # "of_damage_dealt", "if_it_misses", or None
    recoil_fraction: float  # of the damage dealt (or, for "if_it_misses", of the damage it would have dealt)
    self_ko: bool
    fixed_damage: bool
    two_turn: bool
    recharge: bool
    #: (the step-4 verifier's round) the miss recoil is capped at half the TARGET's max HP (Jump Kick, Hi Jump Kick:
    #: `moves.json` recoil "cap", from `DMG_RECOIL_FROM_MISS`)
    recoil_capped: bool = False

    @property
    def hit_chance(self) -> float:
        return 1.0 if self.never_misses else self.accuracy / 100.0


@dataclass(frozen=True)
class SpeciesFact:
    """A species as a Pokedex or a guide describes it (`species.json`)."""

    name: str
    dex: int
    types: tuple[str, ...]
    hp: int
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int
    catch_rate: int
    exp_yield: int
    growth: str


def provenance() -> dict[str, dict]:
    """Each knowledge file's provenance block (its source and the source's sha256)."""
    return {name: _load(f"{name}.json")["provenance"] for name in ("types", "moves", "species")}


def type_multiplier(attack_type: str, defender_types: tuple[str, ...] | list[str]) -> float:
    """The damage multiplier of a move of `attack_type` against a Pokemon of `defender_types` (a dual type multiplies
    both; a type listed twice counts once, as the game stores a single type twice)."""
    chart = _load("types.json")["chart"]
    row = chart.get(attack_type, {})
    value = 1.0
    for defend in dict.fromkeys(defender_types):
        value *= row.get(defend, 1.0)
    return value


def stab(move_type: str, user_types: tuple[str, ...] | list[str]) -> float:
    """Same-type attack bonus: 1.5 when the move's type is one of the user's."""
    return 1.5 if move_type in user_types else 1.0


def category_of(move_type: str) -> str:
    """Gen 3: physical or special by the move's TYPE."""
    return "physical" if move_type in _load("types.json")["physical_types"] else "special"


def move_fact(name: str) -> MoveFact | None:
    entry = _load("moves.json")["moves"].get(name)
    if entry is None:
        return None
    recoil = entry.get("recoil") or {}
    return MoveFact(name=name, type=entry["type"], power=entry["power"], accuracy=entry["accuracy"],
                    never_misses=entry["never_misses"], pp=entry["pp"], effect=entry["effect"], priority=entry["priority"],
                    target=entry["target"], category=entry["category"], recoil_kind=recoil.get("kind"), recoil_fraction=float(recoil.get("fraction", 0.0)),
                    self_ko=entry["self_ko"], fixed_damage=entry["fixed_damage"], two_turn=entry["two_turn"],
                    recharge=entry["recharge"], recoil_capped=bool(recoil.get("cap")))


def _letters(name: str) -> str:
    # (step 4.1 round 2) the gender signs are part of a NAME (NIDORAN♀ and NIDORAN♂ are two species): kept as letters
    return "".join(c for c in name.casefold().replace("é", "e").replace("♀", "f").replace("♂", "m") if c.isalnum())


def move_named(printed: str) -> str | None:
    """The move a screen PRINTS ("MUD-SLAP", "DOUBLE-EDGE": the battle's texts are upper case) by its name in the
    knowledge ("Mud-slap"), or None when no move has that name."""
    if "printed names" not in _CACHE:
        _CACHE["printed names"] = {_letters(name): name for name in _load("moves.json")["moves"]}
    return _CACHE["printed names"].get(_letters(printed))


def species_named(printed: str) -> str | None:
    """(step 4.1) The species a screen PRINTS ("TREECKO", "MR. MIME": the battle's texts are upper case) by its name in
    the knowledge ("Treecko"), or None when no species has that name."""
    if "printed species" not in _CACHE:
        _CACHE["printed species"] = {_letters(name): name for name in _load("species.json")["species"]}
    return _CACHE["printed species"].get(_letters(printed))


def species_fact(name: str) -> SpeciesFact | None:
    entry = _load("species.json")["species"].get(name)
    if entry is None:
        return None
    base = entry["base"]
    return SpeciesFact(name=name, dex=entry["dex"], types=tuple(entry["types"]), hp=base["hp"], attack=base["attack"],
                       defense=base["defense"], speed=base["speed"], sp_attack=base["sp_attack"],
                       sp_defense=base["sp_defense"], catch_rate=entry["catch_rate"], exp_yield=entry["exp_yield"],
                       growth=entry["growth"])
