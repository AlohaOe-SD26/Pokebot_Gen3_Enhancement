"""
The rare-species predicate (design v2 step 7, "RP"): INERT. Data plus pure functions; nothing here changes what the
bot does. Step 8 (the cap-3 rule and its rare exemption) is the first consumer.

    RARE = legendary OR special OR rate OR pseudo OR variant           (shiny: its own branch, and a reason here)

The species-level reasons (legendary, special, rate, pseudo) are precomputed by the generator,
`tools/story-dev/rare_species_dataset.py`, into `modules/data/emerald_rarity.json`, keyed by NATIONAL dex number.
‼ Not by the internal ROM index: Skitty is national 300 but internal 315, and national 315 is Roselia.

Two reasons belong to the INDIVIDUAL, so they are decided here:
  * variant: the species has a minority gender (ratio 31, 63 or 191) whose best_rate x P(minority) is <= 4%, and
    this individual IS that gender (the male Skitty, 0.51%). The record's ULTRA-RARE tier (03:3685-3688).
  * shiny:   the bot's shiny branch already catches every shiny; it appears here only as a reason.

TIER. ULTRA when the verdict carries the variant or the shiny reason, otherwise RARE. The record is tiered (03:3681):
RARE is caught when not owned, ULTRA on every encounter even if owned, which is what the shiny branch already does.
v2 builds no duplicate catching; the tier is carried so that policy never has to re-derive it.

LEGENDARY. It is a sibling of rare in RULING 25 ("rare/shiny/legendary", 06:8047), not one of the record's rare
kinds; it is folded in here because step 8 treats all three the same way (uncapped).

`note` explains a verdict that could not look anything up: "no_data" (no wild table and not listed: Surskit, Wynaut,
Sudowoodo), "no_species" (an empty slot, or species index 0, whose national number reads as 151 = Mew), "invalid"
(a failed checksum: the species bytes are garbage), "egg", or "adapter_error:<Type>". A verdict is never raised: a caller in a battle loop must not crash on a telemetry question.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_log = logging.getLogger("rarity")

DATA_FILE = Path(__file__).parent / "data" / "emerald_rarity.json"

TIER_RARE = "RARE"
TIER_ULTRA = "ULTRA"
SPECIES_REASONS = ("legendary", "special", "rate", "pseudo")
ULTRA_REASONS = ("variant", "shiny")


@dataclass(frozen=True)
class RareVerdict:
    rare: bool
    tier: str | None
    reasons: tuple[str, ...]
    note: str | None = None


def load_table(path: Path | str | None = None) -> dict[int, dict]:
    """{national dex: row}. A missing or unreadable file gives {} and a warning: every species then reads not rare."""
    try:
        payload = json.loads(Path(path or DATA_FILE).read_text(encoding="utf-8"))
        return {int(national): row for national, row in payload["species"].items()}
    except Exception as error:  # noqa: BLE001 — an unreadable table must degrade to "nothing is rare", never raise
        _log.warning("rarity table unavailable (%s: %s); every species reads as not rare",
                     type(error).__name__, error)
        return {}


@lru_cache(maxsize=1)
def _table() -> dict[int, dict]:
    return load_table()


def classify(row: dict | None, *, gender: str | None, shiny: bool = False) -> RareVerdict:
    """PURE. `row` is the species' table row (None = no data), `gender` is "male", "female" or None."""
    reasons = [] if row is None else [r for r in row.get("reasons", ()) if r in SPECIES_REASONS]
    if row is not None and row.get("variant_gender") is not None and gender == row["variant_gender"]:
        reasons.append("variant")
    if shiny:
        reasons.append("shiny")
    note = "no_data" if row is None else None
    if not reasons:
        return RareVerdict(False, None, (), note)
    tier = TIER_ULTRA if any(r in ULTRA_REASONS for r in reasons) else TIER_RARE
    return RareVerdict(True, tier, tuple(reasons), note)


def encounter_rarity(pokemon, table: dict[int, dict] | None = None) -> RareVerdict:
    """The verdict for a live `Pokemon`. Never raises."""
    try:
        if pokemon is None or pokemon.is_empty:
            return RareVerdict(False, None, (), "no_species")
        # ‼ A mon that fails its checksum decrypts to an arbitrary species, which can be a legendary (the review
        # measured a random blob reading as Lugia), and the opponent-party reader does not filter these out.
        if not pokemon.is_valid:
            return RareVerdict(False, None, (), "invalid")
        if pokemon.is_egg:
            return RareVerdict(False, None, (), "egg")
        species = pokemon.species
        if species.index == 0:
            return RareVerdict(False, None, (), "no_species")
        rows = _table() if table is None else table
        return classify(rows.get(species.national_dex_number), gender=pokemon.gender, shiny=bool(pokemon.is_shiny))
    except Exception as error:  # noqa: BLE001
        return RareVerdict(False, None, (), f"adapter_error:{type(error).__name__}")
