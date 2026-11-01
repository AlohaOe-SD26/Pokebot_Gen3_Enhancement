"""The STORY a person knows is ahead (build step 5), read from the AI's own `milestones.json`. Framework-free.

WHY A FILE OF MILESTONES AND NOTHING ELSE (USER RULING 35; design draft §3: "the goal manager knows WHAT comes next; the AI
decides HOW"): a person who plays Pokemon knows the shape of the story (a starter, a rival, a POKéDEX, gyms) and learns the
particulars from what the game says. The file (`knowledge/milestones.json`, extracted from the bot's teaching docstrings and
data by the TEST-side `gates/extract_milestones.py`, every proof checked against pret/pokeemerald by its `--verify`) holds,
per milestone of badge 1 (RULING 37 Q3: 4 chapters) and of chapter 5, RUSTBORO after the badge (2026-11-01; 28 milestones in all): the flags / vars / trainers that PROVE it happened, where it happens,
what a person DOES for it (`steps`), the HINT the game gives (with the words whose reading unlocks it), the fight and its
levels, and the LOOKS a person recognises (a figure, a door, the wall clock). This module only READS the file, once, and
answers from the eyes' `Progress.marks`: which milestone is the current one, and what the maps of a step are for this
player (the player's house and the rival's swap with the GENDER the AI chose in its intro).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "Look",
    "Milestone",
    "Step",
    "Story",
    "load_story",
]

_FILE = Path(__file__).parent / "milestones.json"
_CACHE: dict[str, dict] = {}


def _load() -> dict:
    if "data" not in _CACHE:
        _CACHE["data"] = json.loads(_FILE.read_text(encoding="utf-8"))
    return _CACHE["data"]


@dataclass(frozen=True)
class Look:
    """What a person recognises on screen: a figure (`gfx`, object graphics ids) or a tile (`metatile` ids)."""

    name: str
    gfx: tuple[int, ...]
    metatile: tuple[int, ...]
    what: str


@dataclass(frozen=True)
class Step:
    """One thing a person DOES for a milestone: `go` to `map`, `use` a thing / `talk` to someone that looks like `look` on
    `map`, `ask` the people of `map` until `words` are heard, `follow` a scene, or play the `intro`. `told` (build step
    5.1): the words whose READING tells a person this step's map (its OWN words; None: a step only a visit makes known)."""

    do: str
    map: str | None = None
    look: str | None = None
    words: str | None = None
    told: str | None = None


@dataclass(frozen=True)
class Milestone:
    id: str
    chapter: int
    title: str
    flags: tuple[str, ...]  # proof: these flags set
    variables: tuple[tuple[str, int], ...]  # proof: these game variables at least these values
    trainers: tuple[str, ...]  # proof: these trainers' defeated flags (named TRAINER_<NAME> in the marks)
    maps: tuple[str, ...]
    steps: tuple[Step, ...]
    hint_said: str
    hint_words: str | None  # the words whose READING unlocks the hint's map (None: nothing to hear)
    hint_map: str | None
    fight_levels: tuple[int, ...]  # the opponents' party levels (empty: no fight)
    waypoint: str | None
    #: (build step 5.1) the fight is one the game NAMES to the player (the rival, a gym leader): its levels may be trained
    #: for before it is seen; any other fight's levels are learned only when seen (`brain/goals.py` fight_levels)
    fight_named: bool = False
    #: (build step 5.1) not required for the story: never the current milestone (the gym's trainers)
    optional: bool = False

    def done(self, marks: dict[str, int]) -> bool | None:
        """Every proof holds on the eyes' marks; None when a proof is not in the marks (not read)."""
        needed = [*self.flags, *(f"TRAINER_{name}" for name in self.trainers), *(name for name, _ in self.variables)]
        if any(name not in marks for name in needed):
            return None
        return (all(marks[name] for name in self.flags) and all(marks[f"TRAINER_{name}"] for name in self.trainers)
                and all(marks[name] >= value for name, value in self.variables))

    def proofs(self, marks: dict[str, int]) -> str:
        """Each proof with what the eyes read, for the log."""
        parts = [f"{name}={marks.get(name)}" for name in self.flags]
        parts += [f"TRAINER_{name}={marks.get('TRAINER_' + name)}" for name in self.trainers]
        parts += [f"VAR_{name}={marks.get(name)} (>= {value})" for name, value in self.variables]
        return ", ".join(parts)


class Story:
    """Badge 1's milestones in order, for one player (its GENDER resolves the gendered maps)."""

    def __init__(self, data: dict, gender: str | None) -> None:
        self.gender = gender if gender in ("BOY", "GIRL") else "BOY"
        self.gendered: dict[str, dict[str, str]] = data["gendered_maps"]
        self.looks: dict[str, Look] = {name: Look(name, tuple(info.get("gfx", ())), tuple(info.get("metatile", ())),
                                                  info.get("what", "")) for name, info in data["looks"].items()}
        self.trainer_levels: dict[str, tuple[int, ...]] = {name: tuple(info["levels"])
                                                           for name, info in data["trainers"].items()}
        self.milestones: tuple[Milestone, ...] = tuple(self._milestone(raw) for raw in data["milestones"])

    def resolve(self, name: str | None) -> str | None:
        """A map as the eyes name it: `<player_house_2f>` and the like by this player's gender."""
        if name is None or not (name.startswith("<") and name.endswith(">")):
            return name
        return self.gendered[name[1:-1]][self.gender]

    def _milestone(self, raw: dict) -> Milestone:
        done = raw["done"]
        hint = raw.get("hint") or {}
        fight = raw.get("fight") or {}
        return Milestone(
            id=raw["id"], chapter=int(raw["chapter"]), title=raw["title"],
            flags=tuple(done.get("flags", {})),
            variables=tuple((name, int(info["at_least"])) for name, info in done.get("variables", {}).items()),
            trainers=tuple(done.get("trainers", {})),
            maps=tuple(self.resolve(m) for m in raw.get("maps", [])),
            steps=tuple(Step(s["do"], self.resolve(s.get("map")), s.get("look"), s.get("words"), s.get("told"))
                        for s in raw.get("steps", [])),
            hint_said=hint.get("said", ""), hint_words=hint.get("words"), hint_map=self.resolve(hint.get("map")),
            fight_levels=tuple(fight.get("levels", ())), waypoint=raw.get("waypoint"),
            fight_named=bool(fight.get("named")), optional=bool(raw.get("optional")))

    def index(self, milestone_id: str) -> int:
        for number, milestone in enumerate(self.milestones):
            if milestone.id == milestone_id:
                return number
        raise ValueError(f"no milestone named {milestone_id!r}: {[m.id for m in self.milestones]}")

    def current(self, marks: dict[str, int]) -> tuple[int, Milestone | None]:
        """The FIRST milestone in order not done (and its index); (len, None) when every one is. A milestone whose proof
        was not read counts as not done (the AI does not assume progress it cannot see)."""
        for number, milestone in enumerate(self.milestones):
            if milestone.optional:
                continue  # (build step 5.1) not required: never the current one
            if milestone.done(marks) is not True:
                return number, milestone
        return len(self.milestones), None


def load_story(gender: str | None) -> Story:
    return Story(_load(), gender)
