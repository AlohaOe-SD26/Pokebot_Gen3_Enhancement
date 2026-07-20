"""Ordered Emerald story-chapter registry with completion milestones.

This is the machine-readable form of the overview table in
``PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md`` §1.5. Each Chapter carries a
single **completion milestone** — the event flag (or var) that proves the
chapter is finished and the player has moved on. The progress detector
(``modules/story/progress.py``) walks this list in order; the current chapter
is the first one whose milestone is not yet met.

Every flag/var name here resolves against
``modules/data/event_flags/emerald.txt`` and ``.../event_vars/emerald.txt``
(validated by ``validate_registry()``). Names sourced from the design doc,
which took them from those same tables (ground truth).

A few milestones are marked ``verify_live=True`` — the flag is the best proxy
we have from static analysis, but its exact set-point should be confirmed once
the bot can run the game (documented as an open item in the design doc). They
are still correct *ordering* boundaries; only the precise trigger frame is
uncertain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class FlagVarReader(Protocol):
    """Anything the detector can read progress from — a live-memory adapter or
    a parsed ``SaveData`` both satisfy this. ``get_item_bag`` is optional (only
    item-milestones use it) and may be absent on minimal readers."""

    def get_event_flag(self, flag_name: str) -> bool: ...

    def get_event_var(self, var_name: str) -> int: ...


@dataclass(frozen=True)
class Milestone:
    """A single proof-of-completion check against a reader.

    kind == "flag": event ``flag`` is set.
    kind == "var" : event ``var`` >= ``at_least``.
    kind == "item": the named key item is in the bag (quantity > 0).
    """

    kind: str
    name: str
    at_least: int = 1
    verify_live: bool = False

    def met(self, reader: FlagVarReader) -> bool:
        try:
            if self.kind == "flag":
                return bool(reader.get_event_flag(self.name))
            if self.kind == "var":
                return int(reader.get_event_var(self.name)) >= self.at_least
            if self.kind == "item":
                get_bag = getattr(reader, "get_item_bag", None)
                if get_bag is None:
                    return False
                from modules.items import get_item_by_name

                item = get_item_by_name(self.name)
                if item is None:
                    return False
                return get_bag().quantity_of(item) > 0
        except Exception:
            # An unknown/unreadable milestone must never crash detection; treat
            # it as "not yet met" (validate_registry() catches real typos).
            return False
        return False

    def describe(self) -> str:
        if self.kind == "var":
            return f"var {self.name} >= {self.at_least}"
        if self.kind == "item":
            return f"item {self.name} in bag"
        return f"flag {self.name}"


def flag(name: str, *, verify_live: bool = False) -> Milestone:
    return Milestone("flag", name, verify_live=verify_live)


def var_at_least(name: str, value: int, *, verify_live: bool = False) -> Milestone:
    return Milestone("var", name, at_least=value, verify_live=verify_live)


def has_item(name: str, *, verify_live: bool = False) -> Milestone:
    return Milestone("item", name, verify_live=verify_live)


@dataclass(frozen=True)
class Chapter:
    key: str            # stable id, e.g. "4" or "16b"
    order: int          # strict global ordering
    name: str
    area: str
    complete: Milestone  # proof this chapter is DONE
    objective: str       # what to do while this chapter is CURRENT
    badge: str | None = None  # badge earned in this chapter, if any


# ---------------------------------------------------------------------------
# The ordered chapter list. `order` is the single source of sequencing.
# ---------------------------------------------------------------------------
CHAPTERS: list[Chapter] = [
    Chapter("0", 0, "Intro & Identity", "Truck → Littleroot",
            flag("ADVENTURE_STARTED"),
            "Finish the intro: name/gender with Birch, set the clock, get the "
            "running shoes and first bag; become controllable in Littleroot."),
    Chapter("1", 1, "Starter & first steps", "Route 101 / Oldale / Rt 102-103",
            flag("RECEIVED_POKEDEX_FROM_BIRCH"),
            "Rescue Birch (pick a starter on Route 101), beat the rival on "
            "Route 103, receive the Pokédex + Poké Balls from Birch."),
    Chapter("2", 2, "Petalburg & Wally", "Petalburg City",
            flag("THANKED_FOR_PLAYING_WITH_WALLY"),
            "Meet Dad (Norman) at the Petalburg Gym and do the catching "
            "tutorial with Wally."),
    Chapter("3", 3, "Woods (rescue) & Cut", "Rt 104 / Petalburg Woods / Rustboro",
            flag("RECEIVED_HM_CUT"),
            "Cross Route 104 and Petalburg Woods (help the Devon researcher), "
            "reach Rustboro, and get HM01 Cut from the Cutter's House."),
    Chapter("4", 4, "Gym 1 — Roxanne (Rock)", "Rustboro City",
            flag("BADGE01_GET"), badge="Stone",
            objective="Beat Roxanne at the Rustboro Gym for the Stone Badge "
                      "(Cut becomes field-usable)."),
    Chapter("5", 5, "Devon errand & Peeko rescue", "Rustboro / Rt 116 / Rusturf Tunnel",
            flag("RECEIVED_POKENAV"),
            "Chase the goods-thief through Rusturf Tunnel, free Peeko, return "
            "the Devon Goods, and receive the PokéNav; beat the rival."),
    Chapter("5b", 6, "Mr. Briney & the boat", "Rt 104 (Briney's cottage)",
            flag("MR_BRINEY_SAILING_INTRO"),
            "Reach Mr. Briney's cottage so he'll sail you to Dewford."),
    Chapter("6", 7, "To Dewford + Steven's letter", "Rt 104/105 / Granite Cave",
            flag("DELIVERED_STEVEN_LETTER"),
            "Sail to Dewford, get HM05 Flash, explore Granite Cave and deliver "
            "Steven's letter."),
    Chapter("7", 8, "Gym 2 — Brawly (Fighting)", "Dewford Town",
            flag("BADGE02_GET"), badge="Knuckle",
            objective="Beat Brawly at the Dewford Gym for the Knuckle Badge "
                      "(Flash becomes field-usable)."),
    Chapter("8", 9, "Slateport & Oceanic Museum", "Rt 109 / Slateport",
            flag("DELIVERED_DEVON_GOODS"),
            "Sail to Slateport, push through the Aqua grunts at the Oceanic "
            "Museum, and deliver the Devon parts to Captain Stern."),
    Chapter("9", 10, "Mauville & the Bike", "Rt 110 / Mauville",
            flag("RECEIVED_HM_ROCK_SMASH"),
            "Head up Route 110 (beat the rival), reach Mauville, get the Bike "
            "from Rydel's and HM06 Rock Smash from the SE house."),
    Chapter("10", 11, "Gym 3 — Wattson (Electric)", "Mauville City",
            flag("BADGE03_GET"), badge="Dynamo",
            objective="Beat Wattson at the Mauville Gym for the Dynamo Badge "
                      "(Rock Smash becomes field-usable)."),
    Chapter("11", 12, "Rt 111/112 & Mt. Chimney", "Rt 111 desert / Mt. Chimney",
            flag("DEFEATED_EVIL_TEAM_MT_CHIMNEY"),
            "Cross to Lavaridge via Fiery Path/Rt 112; stop Team Magma at Mt. "
            "Chimney (Go-Goggles + Meteorite along the way)."),
    Chapter("12", 13, "Gym 4 — Flannery (Fire)", "Lavaridge Town",
            flag("BADGE04_GET"), badge="Heat",
            objective="Beat Flannery at the Lavaridge Gym for the Heat Badge "
                      "(Strength becomes field-usable)."),
    Chapter("13", 14, "Gym 5 — Norman (Dad)", "Petalburg City",
            flag("BADGE05_GET"), badge="Balance",
            objective="Return to Petalburg (needs 4 badges) and beat Dad for "
                      "the Balance Badge; then get HM03 Surf nearby."),
    Chapter("14", 15, "Rt 118/119 & Weather Institute", "Rt 118 / 119 / Weather Inst.",
            flag("RECEIVED_HM_FLY"),
            "Surf Route 118 to 119, rescue the Weather Institute from Team "
            "Aqua (get Castform), beat the rival — who gives HM02 Fly."),
    Chapter("14b", 16, "Devon Scope & Fortree Kecleon", "Fortree City / Route 120",
            flag("KECLEON_FLED_FORTREE"),
            "Get the Devon Scope from Steven on Route 120, then reveal and "
            "battle the invisible Kecleon blocking the Fortree Gym door."),
    Chapter("15", 17, "Gym 6 — Winona (Flying)", "Fortree City",
            flag("BADGE06_GET"), badge="Feather",
            objective="Solve the rotating-gate puzzle and beat Winona for the "
                      "Feather Badge (Fly becomes field-usable)."),
    Chapter("16", 18, "To Lilycove", "Rt 120/121 / Lilycove",
            flag("MET_RIVAL_LILYCOVE"),
            "Travel Routes 120/121 to Lilycove; the Mt. Pyre / Team Hideout "
            "arc begins."),
    Chapter("16b", 19, "Mt. Pyre", "Rt 122/123 / Mt. Pyre",
            has_item("Magma Emblem"),
            "Surf to Mt. Pyre; at the summit get the Magma Emblem (key item "
            "that opens the Magma Hideout). [completion = Magma Emblem in bag "
            "— the design doc's [P4] authoritative signal; the HIDE_ NPC flag "
            "proved unreliable in testing. Progress also tracked by var "
            "MT_PYRE_STATE.]"),
    Chapter("16c", 20, "Slateport submarine theft", "Slateport Harbor",
            flag("EVIL_TEAM_ESCAPED_STERN_SPOKE"),
            "Team Aqua steals the submarine at Slateport Harbor."),
    Chapter("16d", 21, "Magma Hideout — Groudon", "Jagged Pass / Magma Hideout",
            flag("GROUDON_AWAKENED_MAGMA_HIDEOUT"),
            "Enter the Magma Hideout (needs the Magma Emblem in the bag); "
            "confront Maxie as Groudon awakens."),
    Chapter("17", 22, "Team Aqua Hideout & submarine", "Lilycove / Aqua Hideout",
            flag("TEAM_AQUA_ESCAPED_IN_SUBMARINE"),
            "Raid the Aqua Hideout (room-key + Electrode puzzle); Team Aqua "
            "escapes in the submarine."),
    Chapter("18", 23, "Mossdeep & Space Center", "Rt 124/125 / Mossdeep",
            flag("RECEIVED_HM_DIVE"),
            "Surf to Mossdeep, defend the Space Center with Steven (double "
            "battle), get HM08 Dive from Steven's house."),
    Chapter("19", 24, "Gym 7 — Tate & Liza (Psychic)", "Mossdeep City",
            flag("BADGE07_GET"), badge="Mind",
            objective="Win the double battle vs Tate & Liza for the Mind Badge "
                      "(Dive becomes field-usable)."),
    Chapter("20", 25, "Seafloor Cavern — Kyogre", "Rt 128 / Seafloor Cavern",
            flag("KYOGRE_ESCAPED_SEAFLOOR_CAVERN"),
            "Dive on Route 128 into the Seafloor Cavern; Archie awakens "
            "Kyogre."),
    Chapter("21", 26, "Sootopolis crisis & Rayquaza", "Sootopolis / Sky Pillar",
            flag("DEFEATED_RAYQUAZA"),
            "Dive into Sootopolis; climb the Sky Pillar (Mach Bike) to rouse "
            "Rayquaza and quell the legendaries."),
    Chapter("22", 27, "Gym 8 — Juan (Water)", "Sootopolis City",
            flag("BADGE08_GET"), badge="Rain",
            objective="Beat Juan at the Sootopolis Gym for the Rain Badge; get "
                      "HM07 Waterfall from Wallace."),
    Chapter("23", 28, "Victory Road", "Rt 128/132-134 → Ever Grande",
            flag("DEFEATED_WALLY_VICTORY_ROAD"),
            "Surf/Waterfall/Dive to Ever Grande and clear Victory Road "
            "(Strength/Rock Smash/Flash inside); beat Wally."),
    Chapter("24", 29, "Elite Four + Champion", "Ever Grande / Pokémon League",
            flag("SYS_GAME_CLEAR"),
            "Beat Sidney → Phoebe → Glacia → Drake, then Champion Wallace."),
]


# The 8 gym badges, in order, are the reliable progress SPINE: in normal play
# they are earned strictly in sequence and cannot be skipped. Detection anchors
# on them first, then refines with the finer milestone flags.
BADGE_FLAG_NAMES: list[str] = [f"BADGE0{n}_GET" for n in range(1, 9)]


def _compute_badges_before() -> dict[str, int]:
    """Badges held *during* each chapter, derived from which chapter earns each
    badge (the ``badge`` field). A chapter that earns a badge counts as holding
    the badge only AFTER it completes, so its ``badges_before`` is the running
    total before the increment."""
    result: dict[str, int] = {}
    earned = 0
    for c in CHAPTERS:
        result[c.key] = earned
        if c.badge is not None:
            earned += 1
    return result


BADGES_BEFORE: dict[str, int] = _compute_badges_before()


def completed_chapters(reader: FlagVarReader) -> list[Chapter]:
    """Every chapter whose milestone is met (may be non-contiguous on hacked or
    partially-progressed saves)."""
    return [c for c in CHAPTERS if c.complete.met(reader)]


def is_game_cleared(reader: FlagVarReader) -> bool:
    try:
        return bool(reader.get_event_flag("SYS_GAME_CLEAR"))
    except Exception:
        return False


def badge_level(reader: FlagVarReader) -> int:
    """Highest badge number that is set (0-8). Uses the HIGHEST set badge, not a
    count, so a save missing an earlier badge flag still reads as at-least-here."""
    level = 0
    for index, flag_name in enumerate(BADGE_FLAG_NAMES, start=1):
        try:
            if reader.get_event_flag(flag_name):
                level = index
        except Exception:
            pass
    return level


def chapters_in_bracket(level: int) -> list[Chapter]:
    """Chapters played while holding exactly ``level`` badges (the segment
    between earning badge ``level`` and earning badge ``level``+1)."""
    return [c for c in CHAPTERS if BADGES_BEFORE[c.key] == level]


def current_chapter(reader: FlagVarReader) -> Chapter:
    """The chapter the save is currently working on.

    Anchored on the badge spine: pick the bracket for the current badge level,
    then the first chapter in that bracket whose milestone is not yet met. This
    is robust both to a legit save missing a stray flag (the badge still places
    it) and to a hacked save with items/flags set out of order (they can't move
    it outside its badge bracket)."""
    if is_game_cleared(reader):
        return CHAPTERS[-1]
    bracket = chapters_in_bracket(badge_level(reader))
    if not bracket:  # defensive; every level 0-8 has a bracket
        return CHAPTERS[-1]
    for chapter in bracket:
        if not chapter.complete.met(reader):
            return chapter
    # Whole bracket done but the next badge isn't set yet — sit on the last
    # chapter of the bracket (the gym battle that grants the next badge).
    return bracket[-1]


def milestone_anomalies(reader: FlagVarReader) -> list[Chapter]:
    """Chapters whose milestone is met but which lie AHEAD of the current badge
    level (``badges_before`` > level). A non-empty result means progress flags
    or key items exist beyond what the badge count supports — the signature of a
    hand-edited/test save. Surfaced as a diagnostic, not an error."""
    level = badge_level(reader)
    return [
        c for c in CHAPTERS
        if BADGES_BEFORE[c.key] > level and c.complete.met(reader)
    ]


def validate_registry() -> list[str]:
    """Check that every milestone flag/var name resolves against the Emerald
    offset tables. Returns a list of problem strings (empty == all good).

    This does NOT need a running emulator — it only touches the name→offset
    lookup tables in ``modules/game``."""
    from modules.game import get_event_flag_offset, get_event_var_offset

    problems: list[str] = []
    seen_orders: dict[int, str] = {}
    for chapter in CHAPTERS:
        # ordering must be strictly increasing / unique
        if chapter.order in seen_orders:
            problems.append(
                f"duplicate order {chapter.order}: {chapter.key} and {seen_orders[chapter.order]}"
            )
        seen_orders[chapter.order] = chapter.key
        m = chapter.complete
        try:
            if m.kind == "flag":
                get_event_flag_offset(m.name)
            elif m.kind == "var":
                get_event_var_offset(m.name)
            elif m.kind == "item":
                from modules.items import get_item_by_name

                if get_item_by_name(m.name) is None:
                    problems.append(f"{chapter.key}: unknown item {m.name!r}")
            else:
                problems.append(f"{chapter.key}: unknown milestone kind {m.kind!r}")
        except KeyError:
            problems.append(f"{chapter.key}: unknown {m.kind} name {m.name!r}")

    if [c.order for c in CHAPTERS] != sorted(c.order for c in CHAPTERS):
        problems.append("CHAPTERS is not in ascending `order`")
    return problems
