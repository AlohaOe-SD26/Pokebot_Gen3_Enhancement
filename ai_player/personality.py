"""The AI's PERSONALITY, as far as build step 2 needs it: who it is at the start of a game (USER RULING 37 Q8:
"All three (Catcher, Story, Trainer) from day one"; design draft §2.3 and §5). Framework-free.

WHAT IS HERE NOW: the base personality, drawn from the run's seed unless the run names one, and the two
choices the intro asks for, the player's GENDER and NAME, made by a personality-WEIGHTED random draw. The
weights are TASTE, not strategy: nothing in the game depends on the gender or the name, so each personality
only leans a little, so that runs of different personalities differ (pillar 5, variety) and two runs with
different seeds differ (§7). Every draw is from the run's CHOICES stream (`random.Random`, seeded and logged
by the brain), so a seed reproduces a run's choices, and the pad's pacing never shifts them.

Later steps add the intent weights (explore, catch, train, story), drift and the favourite species (§2.3).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

__all__ = ["GENDER_LEAN", "NAMES", "PERSONALITIES", "Personality", "choose_gender", "choose_name", "pick_personality"]

PERSONALITIES = ("Catcher", "Story", "Trainer")
#: P(GIRL) by personality; the rest is BOY. A small lean each, nothing more (see the module docstring).
GENDER_LEAN: dict[str, float] = {"Catcher": 0.6, "Story": 0.45, "Trainer": 0.5}
#: The small lists the name is drawn from. Mixed case on purpose, at most 7 letters (`PLAYER_NAME_LENGTH`):
#: a lower-case letter is on the keyboard's second page, so typing these uses the page switch too.
NAMES: dict[str, tuple[str, ...]] = {
    "BOY": ("SAM", "Kai", "Rowan", "ELI", "Jude", "Milo"),
    "GIRL": ("IRIS", "Luna", "Nova", "PIA", "Rosa", "Wren"),
}


@dataclass(frozen=True)
class Personality:
    name: str
    seed: int
    chosen_by: str  # "seed" or "named by the run"


def pick_personality(choices: random.Random, seed: int, named: str | None = None) -> Personality:
    """The base personality: the one the run names, or a draw from the choices stream."""
    if named:
        if named not in PERSONALITIES:
            raise ValueError(f"personality must be one of {PERSONALITIES}, got {named!r}")
        return Personality(named, seed, "named by the run")
    return Personality(choices.choice(PERSONALITIES), seed, "seed")


def choose_gender(choices: random.Random, personality: Personality) -> tuple[str, float]:
    """("BOY" or "GIRL", the P(GIRL) it was drawn with)."""
    lean = GENDER_LEAN[personality.name]
    return ("GIRL" if choices.random() < lean else "BOY"), lean


def choose_name(choices: random.Random, gender: str) -> str:
    return choices.choice(NAMES[gender])
