"""Everything the learner KNOWS before it runs a single game: the strategy knobs it may turn, the bosses it is
measured against, and the failure shapes our research has already named.

Sources (each claim here is copied from a document, not recalled):
- the knobs and their two values: step 14's batch (`tools/story-dev/x4-runs/20261001-210001/ARMS.json`). Every value
  below ran there for 13 hours, so the learner never sends the bot a setting nobody has run.
- the meanings: `PROJECT KNOWLEDGE/29-DISABLED-FEATURES-REGISTRY.md` (one row per flag).
- the trainer ids: pret/pokeemerald `include/constants/opponents.h`, as already pinned in
  `tools/story-dev/batch14_checks.py` TRAINERS.
- the walls: `PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md` (KI-118, KI-120, KI-122) and the run logs themselves.
"""
from __future__ import annotations

import re

#: Knobs held FIXED in every arm. They were identical in both step-14 arms, so the data says nothing about changing them.
FIXED = {
    "POKEBOT_R25_DMGAUDIT": "1",
    "POKEBOT_R25_WEAKEN": "observe",
    "POKEBOT_R25_WEAKEN_CALC": "1",
    "POKEBOT_MAINTAIN": "1",
    "POKEBOT_BOX_OVERFLOW_CATCH": "1",
    # Both 0 in step 14 and never run at 1 in any A/B: a Claude proposal may unlock them (README "Changing the knobs").
    "POKEBOT_R20_TEAM6": "0",
    "POKEBOT_R20_HUNTFIRST": "0",
}

#: The knobs the learner may turn: name -> (allowed values, short meaning). Value [0] is step 14's arm A (the baseline).
GENES: dict[str, tuple[tuple[str, ...], str]] = {
    "POKEBOT_R24_CATCHHURT": (("0", "1"), "catch new species even when the party is not at full strength"),
    "POKEBOT_R24_CATCHTRAIN": (("0", "1"), "catch new species even during a training grind"),
    "POKEBOT_R24_OVERSURVIVAL": (("0", "1"), "try a wanted catch before survival mode flees every wild"),
    "POKEBOT_R24_NOFAINTBAIL": (("0", "1"), "a faint during a catch sends the next mon instead of bailing"),
    "POKEBOT_R25_CAP": (("0", "1"), "three catch attempts per species instead of two"),
    "POKEBOT_R25_RARE": (("0", "1"), "rare species are exempt from the attempt cap"),
    "POKEBOT_R23_BALLRESTOCK": (("0", "1"), "top off Poke Balls at the Rustboro mart"),
    "POKEBOT_R27_KEYITEMS": (("0", "1"), "use healing items only against key trainers"),
    "POKEBOT_R26_KITTOPOFF": (("0", "1"), "top off the healing kit at the Rustboro mart"),
    "POKEBOT_R27_DOUBLEITEMS": (("0", "1"), "use healing items in double battles"),
    "POKEBOT_R20_OPENFENCE": (("0", "1"), "after gym 1, catch new species into the party"),
    # The first knob aimed at a WALL (2026-10-03). Unlike the eleven above, its alternative value never ran in step
    # 14. The exception to "only values that already ran" is deliberate: "4" drives the same target-level training
    # the bot's non-boss retry path runs every game (team_max + 5), so no new machinery is exercised.
    "POKEBOT_BOSSMODE_TOPUP": (("1", "4"), "levels boss mode trains before re-fighting a boss it keeps losing to"),
}

ALL_KEYS = tuple(FIXED) + tuple(GENES)

#: Step 14's two arms, as genomes over GENES (every gene's value), so its 78 runs seed the learner. Step 14 predates
#: the boss-mode knob and ran its default ("1") in both arms.
STEP14_A = {g: vals[0] for g, (vals, _) in GENES.items()}
STEP14_B = {g: "1" for g in GENES}  # every step-14 knob ON; the boss-mode knob at its default "1"

# ---------------------------------------------------------------------------------------------------------- trainers
LEADERS = {265: "ROXANNE", 266: "BRAWLY", 267: "WATTSON", 268: "FLANNERY",
           269: "NORMAN", 270: "WINONA", 271: "TATE_AND_LIZA", 272: "JUAN"}
ELITE_FOUR = {261: "SIDNEY", 262: "PHOEBE", 263: "GLACIA", 264: "DRAKE"}
CHAMPION = {335: "WALLACE"}
KEY_TRAINERS = {**LEADERS, **ELITE_FOUR, **CHAMPION}
#: badges + Elite Four + Champion: a run that becomes Champion scores 13 of 13.
MAX_PROGRESS = len(LEADERS) + len(ELITE_FOUR) + len(CHAMPION)

#: What our own research already says about a boss that walls runs. A HINT for the reader, never a diagnosis.
#: Keyed by the boss name `classify_wall` puts in "boss wall: <name>".
BOSS_HINTS = {
    "Norman": "KI-118: box-first takes a type-only counter that cannot win (fix designed on branch wt/boxfirst)",
    "Tate & Liza": "KI-122: a counter caught for an earlier boss keeps leading (stale _hunted_counter_pids)",
}

# ------------------------------------------------------------------------------------------------------------ walls
#: How a run's LAST derail is named. First match wins; anything else is summarised by its own text.
WALLS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("E4 refused: League basket short", re.compile(r"REFUSING to enter the Elite Four.*basket short"),
     "money or healing items ran short before the Elite Four"),
    ("E4 refused: team below level floor", re.compile(r"REFUSING to enter the Elite Four.*below the L\d+ floor"),
     "RULING 15: four mons must reach the level floor before the gauntlet"),
    ("training ended below floor", re.compile(r"training ended with mon still below the floor"),
     "KI-120 may freeze training when one mon cannot train"),
    ("heal walk blocked", re.compile(r"heal_in_pokemon_center: the walk to \w+ is BLOCKED"),
     "navigation: the path to a Pokemon Center is blocked"),
    ("unreachable target", re.compile(r"Could not reach"), "navigation: a story target could not be reached"),
)


#: "<boss>: N losses with no super-effective answer to <types>": the story bot gave up on a boss.
BOSS_LOSS_RE = re.compile(r"([^:]{2,40}): \d+ losses with no super-effective answer to ([\w/]+)")
TYPE_TO_BOSS = {"Normal": "Norman"}


def classify_wall(derail_text: str | None) -> str:
    """A short, stable name for the reason a run ended."""
    if not derail_text:
        return "no derail recorded"
    boss = BOSS_LOSS_RE.search(derail_text)
    if boss:
        name = boss.group(1).strip()
        if name == "this boss":  # the Norman message does not name him; his team is Normal-type
            name = TYPE_TO_BOSS.get(boss.group(2), name)
        return f"boss wall: {name}"
    for name, rx, _ in WALLS:
        if rx.search(derail_text):
            return name
    head = re.sub(r"\d+", "#", derail_text.split(" — ")[0])
    return head[:70]


def validate_genes(genes: dict) -> list[str]:
    """[] if `genes` names only known knobs with allowed values (a partial dict is fine: the rest stay baseline)."""
    errors = []
    for k, v in genes.items():
        if k not in GENES:
            errors.append(f"{k} is not a knob the learner may turn")
        elif str(v) not in GENES[k][0]:
            errors.append(f"{k}={v!r} is not one of {GENES[k][0]}")
    return errors
