"""Badge case — the data behind the trainer-card overlay (#24-badges).

Assembles, for one profile, the eight Hoenn badges with: whether it has been earned, the
gym leader's details, and — the part that makes this more than decoration — THE TEAM THAT
BEAT THEM, read back from the `badge-log.json` that `modules/badge_log.py` writes at the
instant each badge flag flips.

Pure data: no Tk, no `context` at import time, so it can be exercised without a GUI or an
emulator. The dashboard renders whatever this returns.

‼ LEADER DETAILS ARE DECOMP-VERIFIED, NOT RECALLED. Emerald differs from Ruby/Sapphire in
its gym roster, and this project has a standing rule against writing game facts from
memory. Every field in `BADGES` below carries its evidence in the module docstring of the
verification note; if you add a field, verify it the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BadgeInfo:
    """Static, verified facts about one badge and its gym."""

    flag: str
    badge: str
    leader: str
    city: str
    type: str
    ace: str
    ace_level: int
    sprite: str
    tm: str | None = None
    #: What the badge authorises outside battle, where that matters to the bot's routing.
    grants: str | None = None


@dataclass
class BadgeCaseEntry:
    """One slot in the case: the static facts plus this profile's state."""

    info: BadgeInfo
    earned: bool = False
    #: Every recorded win against this leader, oldest first (an endless batch replays the
    #: story many times, so there can be many).
    records: list[dict] = field(default_factory=list)

    @property
    def latest(self) -> dict | None:
        return self.records[-1] if self.records else None

    def team_summary(self, record: dict | None = None) -> str:
        """One line describing the team that won, e.g. 'COMBUSKEN L18, POOCHYENA L14'."""
        record = record if record is not None else self.latest
        if not record:
            return ""
        parts = []
        for mon in record.get("team", []):
            name = mon.get("name") or mon.get("species") or "?"
            level = mon.get("level")
            parts.append(f"{name} L{level}" if level else str(name))
        return ", ".join(parts)


def build_case(earned_flags, records: list[dict] | None = None) -> list[BadgeCaseEntry]:
    """Assemble the eight slots.

    `earned_flags` is any iterable of `BADGE0N_GET` flag names that are set; `records` is
    the parsed contents of a profile's `badge-log.json`. Both are tolerated as None/junk —
    the case simply renders empty, which is the correct display for a fresh profile.
    """
    earned = set(earned_flags or ())
    by_flag: dict[str, list[dict]] = {}
    for record in records or ():
        if isinstance(record, dict) and record.get("flag"):
            by_flag.setdefault(str(record["flag"]), []).append(record)

    entries = []
    for info in BADGES:
        entries.append(
            BadgeCaseEntry(
                info=info,
                # A recorded win implies the badge, even if the live flag read is
                # unavailable (e.g. a lane that has not published its flags yet).
                earned=info.flag in earned or bool(by_flag.get(info.flag)),
                records=by_flag.get(info.flag, []),
            )
        )
    return entries


def earned_count(entries: list[BadgeCaseEntry]) -> int:
    return sum(1 for entry in entries if entry.earned)


# ---------------------------------------------------------------------------
# THE CANONICAL TABLE — every field read out of the pokeemerald decomp (master, verified
# 2026-07-26). Parties are the `_1` STORY entries (`src/data/trainer_parties.h:3367-3613`
# via `src/data/trainers.h:3184-3278`), NOT the `_2`..`_5` rematch parties at
# `src/data/trainers.h:9244+`.
#
# ‼ THE 8TH LEADER IS **JUAN**, NOT WALLACE — this is where Emerald departs from
# Ruby/Sapphire, and the first version of this table (in badge_log.py) got it wrong from
# memory. `src/data/trainers.h:3268-3278`: `[TRAINER_JUAN_1]` is `TRAINER_CLASS_LEADER`,
# name "JUAN"; `:4024-4034`: `[TRAINER_WALLACE]` is `TRAINER_CLASS_CHAMPION` and is only
# ever battled at `data/maps/EverGrandeCity_ChampionsRoom/scripts.inc:43`. The game states
# it outright at `data/maps/CaveOfOrigin_B1F/scripts.inc:65-69`: "I was once the GYM LEADER
# of SOOTOPOLIS... I've entrusted my mentor JUAN with the GYM's operation."
#
# ‼ MOSSDEEP IS ONE TRAINER, NOT TWO. `include/constants/opponents.h:275` defines only
# `TRAINER_TATE_AND_LIZA_1`; `src/data/trainers.h:3256-3266` gives the name "TATE&LIZA"
# with `.doubleBattle = TRUE` and a single 4-Pokémon party. It is a DOUBLE battle and
# requires two usable Pokémon (`trainerbattle_double`,
# `data/maps/MossdeepCity_Gym/scripts.inc:52`).
#
# `grants` is the field move each badge authorises. This is not folklore: `src/party_menu.c`
# :117-127 orders the field-move enum to line up with the badge flags, and :3725 enforces
# `FlagGet(FLAG_BADGE01_GET + fieldMove)` — so the order below IS the mapping.
#
# Type labels are stated in each gym's own text EXCEPT Petalburg's: the decomp has no
# "Normal-type" gym-guide line for Norman, so "Normal" there is INFERRED from his party
# (Spinda/Vigoroth/Linoone/Slaking are all `{ TYPE_NORMAL, TYPE_NORMAL }` in
# `src/data/pokemon/species_info.h`). Flagged rather than presented as quoted.
# ---------------------------------------------------------------------------
BADGES: tuple[BadgeInfo, ...] = (
    BadgeInfo("BADGE01_GET", "Stone", "Roxanne", "Rustboro", "Rock", "Nosepass", 15,
              "Stone.png", "TM39 Rock Tomb", "Cut (HM01)"),
    BadgeInfo("BADGE02_GET", "Knuckle", "Brawly", "Dewford", "Fighting", "Makuhita", 19,
              "Knuckle.png", "TM08 Bulk Up", "Flash (HM05)"),
    BadgeInfo("BADGE03_GET", "Dynamo", "Wattson", "Mauville", "Electric", "Manectric", 24,
              "Dynamo.png", "TM34 Shock Wave", "Rock Smash (HM06)"),
    BadgeInfo("BADGE04_GET", "Heat", "Flannery", "Lavaridge", "Fire", "Torkoal", 29,
              "Heat.png", "TM50 Overheat", "Strength (HM04)"),
    BadgeInfo("BADGE05_GET", "Balance", "Norman", "Petalburg", "Normal", "Slaking", 31,
              "Balance.png", "TM42 Facade", "Surf (HM03)"),
    BadgeInfo("BADGE06_GET", "Feather", "Winona", "Fortree", "Flying", "Altaria", 33,
              "Feather.png", "TM40 Aerial Ace", "Fly (HM02)"),
    BadgeInfo("BADGE07_GET", "Mind", "Tate & Liza", "Mossdeep", "Psychic", "Lunatone / Solrock", 42,
              "Mind.png", "TM04 Calm Mind", "Dive (HM08)"),
    BadgeInfo("BADGE08_GET", "Rain", "Juan", "Sootopolis", "Water", "Kingdra", 46,
              "Rain.png", "TM03 Water Pulse", "Waterfall (HM07)"),
)
