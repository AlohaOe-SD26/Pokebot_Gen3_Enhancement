"""TEST SIDE ONLY (boss preparation round 2, 2026-11-11): the game's EXPERIENCE RULE as a model, and a species' experience
YIELD read from the pinned decomp. The AI never imports this file (`gates/check_fairness.py`: a yield is hidden); the gates
use it to predict what a switch-trained battle gives (`gates/test_bossprep.py` ExpModelTests, the live probe
`gates/probe_bossprep.py raise-battle`, the A/B's judge).

THE RULE (`src/battle_script_commands.c` Cmd_getexp, cited in the round-2 spec section 1.2):
  * E = expYield x the foe's level / 7, integer;
  * `viaSentIn` counts each party member whose bit is in gSentPokesToOpponent (it was SENT OUT against the foe: the lead at
    the battle's start, every member switched in after, `src/battle_util.c` UpdateSentPokesToOpponentValue; nothing
    clears the bit of a member switched out in a single wild battle) AND has HP above 0 (a fainted member is skipped by the
    `continue` before it is counted);
  * no Exp. Share held: each counted member gets E / viaSentIn (integer, at least 1); with one held by a living member,
    the sent members split E/2 and each holder gets E/2 / holders;
  * a trainer battle, a traded Pokemon and a Lucky Egg x1.5 each; a member at level 100 nothing; a FAINTED member nothing.

    py -3.12 -B ai_player/gates/exp_rule.py SPECIES LEVEL [SENT]      (prints E and each share; needs POKEBOT_DECOMP)
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

__all__ = ["decomp_growth", "decomp_yield", "expected_gain", "full_exp", "switch_share", "total_exp"]

_YIELDS: dict[str, int] = {}
_GROWTH: dict[str, str] = {}


def full_exp(yield_: int, foe_level: int) -> int:
    """E: the foe's full experience (`calculatedExp`, integer arithmetic)."""
    return yield_ * foe_level // 7


def expected_gain(yield_: int, foe_level: int, sent_alive, holders: int = 0, count_fainted: bool = False) -> list[int]:
    """Each SENT member's gain, in the order of `sent_alive` (one bool a member sent out against the foe: True when it
    still has HP when the foe faints). A fainted member gets 0 and is not counted (FAULT `count_fainted`: it is counted,
    so the others' shares shrink). `holders`: living members holding an Exp. Share (each also gets E/2 / holders,
    not returned here). No trainer, trade or Lucky Egg bonus (a wild battle of the player's own Pokemon)."""
    exp = full_exp(yield_, foe_level)
    alive = [bool(a) for a in sent_alive]
    via = sum(1 for a in alive if a or count_fainted)
    if via == 0:
        return [0 for _ in alive]
    if holders:
        share = max(1, (exp // 2) // via)
    else:
        share = max(1, exp // via)
    return [share if a else 0 for a in alive]


def switch_share(yield_: int, foe_level: int) -> int:
    """The switch-trained trainee's share: it led, was switched out on turn 1 for ONE partner who knocked the foe out,
    both standing: floor(floor(Y x L / 7) / 2) (spec section 1.3)."""
    return expected_gain(yield_, foe_level, (True, True))[0]


def decomp_yield(species: str, decomp: str | os.PathLike | None = None) -> int | None:
    """A species' `.expYield` from the pinned decomp's `src/data/pokemon/species_info.h` (gate side: the developers'
    proof, never the AI's knowledge). `species` as the AI names it ("Poochyena") or as the decomp does ("POOCHYENA").
    None when the decomp is not found (POKEBOT_DECOMP) or the species is not in it."""
    if not _load(decomp):
        return None
    return _YIELDS.get(_key(species))


def decomp_growth(species: str, decomp: str | os.PathLike | None = None) -> str | None:
    """A species' `.growthRate` ("GROWTH_MEDIUM_FAST") from the pinned decomp (gate side, as `decomp_yield`)."""
    if not _load(decomp):
        return None
    return _GROWTH.get(_key(species))


def total_exp(growth: str, level: int) -> int | None:
    """The total EXP at `level` for the growth rates of the Pokemon near RUSTBORO (`src/data/pokemon/experience_tables.h`
    EXP_MEDIUM_FAST n^3, EXP_MEDIUM_SLOW, EXP_FAST, EXP_SLOW); None for another."""
    n = level
    if growth == "GROWTH_MEDIUM_FAST":
        return n ** 3
    if growth == "GROWTH_MEDIUM_SLOW":
        return int(6 * n ** 3 / 5 - 15 * n ** 2 + 100 * n - 140)
    if growth == "GROWTH_FAST":
        return 4 * n ** 3 // 5
    if growth == "GROWTH_SLOW":
        return 5 * n ** 3 // 4
    return None


def _key(species: str) -> str:
    return re.sub(r"[^A-Z0-9]", "_", species.upper().replace("É", "E")).strip("_")


def _load(decomp) -> bool:
    if _YIELDS:
        return True
    root = Path(decomp or os.environ.get("POKEBOT_DECOMP") or "C:/Remote Projects/_decomp/pokeemerald")
    path = root / "src" / "data" / "pokemon" / "species_info.h"
    if not path.is_file():
        return False
    current = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        found = re.match(r"\s*\[SPECIES_(\w+)\]\s*=", line)
        if found:
            current = found.group(1)
            continue
        found = re.search(r"\.expYield\s*=\s*(\d+)", line)
        if found and current is not None:
            _YIELDS[current] = int(found.group(1))
        found = re.search(r"\.growthRate\s*=\s*(GROWTH_\w+)", line)
        if found and current is not None:
            _GROWTH[current] = found.group(1)
    return bool(_YIELDS)


if __name__ == "__main__":
    name, level = sys.argv[1], int(sys.argv[2])
    sent = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    y = decomp_yield(name)
    if y is None:
        print(f"no yield for {name} (POKEBOT_DECOMP?)")
        sys.exit(1)
    print(f"{name} L{level}: yield {y}, E {full_exp(y, level)}, shares with {sent} sent "
          f"{expected_gain(y, level, [True] * sent)}")
