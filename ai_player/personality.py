"""The AI's PERSONALITY (USER RULING 37 Q8: "All three (Catcher, Story, Trainer) from day one"; design draft §2.3 and §5;
HUMAN-PLAY-DESIGN pillar 1). Framework-free.

BUILD STEP 2: the base personality, drawn from the run's seed unless the run names one, and the two choices the intro asks
for, the player's GENDER and NAME, made by a personality-WEIGHTED random draw. The weights are TASTE, not strategy:
nothing in the game depends on the gender or the name, so each personality only leans a little, so that runs of different
personalities differ (pillar 5, variety) and two runs with different seeds differ (§7). Every draw is from the run's
CHOICES stream (`random.Random`, seeded and logged by the brain), so a seed reproduces a run's choices, and the pad's
pacing never shifts them.

BUILD STEP 5 (the goal manager, `brain/goals.py`), three more things a person has:
  * ERRAND WEIGHTS (`Errands`, `ERRANDS`): how much each personality cares for the HUMAN ERRANDS the goal manager
    interleaves with the story (pillar 1: "a personality = its own scoring weights"): how far above the next known fight it
    trains (Trainer most, Story least, never far below: `train_margin`) and how long it roams at the least before one
    (`train_min_steps`); how much it seeks new species (Catcher most) and roams new grass for them; when it buys POKé BALLS
    and how many; when it heals; how often it talks to someone nearby; (build step 5.1, the step-5 adversarial review's
    "it plays like a speedrun") how often it LOOKS AROUND a new outdoor map and for how long (`look_around`, `look_frames`)
    and takes a DETOUR off the way (`detour`, `detour_frames`), Story least, none of them nothing; (build step 5.2,
    replacing the step-5.1 verifier's second round's BALANCE, a quota on the share of a session's time) how soon it grows
    BORED of the story alone (`bored_frames`: Catcher 8,000, Trainer 10,000, Story 12,000 frames since its last curiosity
    that came to something; `brain/goals.py` curious_odds). Taste, not measured from people (plausible values, each named
    here);
  * DRIFT (`PersonalityState`, design draft §2.3 "drift": "with a small chance ... it switches `active` for a bounded time,
    then returns to `base`"; §10.10: it counts STEPS, not the in-game clock): every `DRIFT_EVERY` steps the player walks, a
    `DRIFT_CHANCE` draw may switch the ACTIVE personality to another one for `DRIFT_STEPS` steps (seeded), after which it
    comes back to the base; both changes are LOGGED with the step count (`drift`);
  * a FAVOURITE POKéMON (pillar 1: "each playthrough gets a random wild-catchable Emerald species as its favourite"):
    drawn once per run from `knowledge/wild_species.json` (the species of the decomp's wild tables, extracted by
    `gates/extract_milestones.py --wild`) and logged. The shiny hunt for it is DEFERRED (the README's step-5 limits): for now
    it is only who the AI likes, and it would catch it whenever met (`favourite`).
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "DRIFT_CHANCE",
    "DRIFT_EVERY",
    "DRIFT_STEPS",
    "ERRANDS",
    "Errands",
    "GENDER_LEAN",
    "NAMES",
    "PERSONALITIES",
    "STARTER_LEAN",
    "Personality",
    "PersonalityState",
    "choose_favourite",
    "choose_gender",
    "choose_name",
    "choose_starter",
    "pick_personality",
    "wild_species",
]

PERSONALITIES = ("Catcher", "Story", "Trainer")
#: P(GIRL) by personality; the rest is BOY. A small lean each, nothing more (see the module docstring).
GENDER_LEAN: dict[str, float] = {"Catcher": 0.6, "Story": 0.45, "Trainer": 0.5}
#: The small lists the name is drawn from. Mixed case on purpose, at most 7 letters (`PLAYER_NAME_LENGTH`):
#: a lower-case letter is on the keyboard's second page, so typing these uses the page switch too.
NAMES: dict[str, tuple[str, ...]] = {
    "BOY": ("SAM", "Kai", "Rowan", "ELI", "Jude", "Milo"),
    "GIRL": ("IRIS", "Luna", "Nova", "PIA", "Rosa", "Wren"),
}
#: BUILD STEP 5: the starter, a TASTE by personality over the bag's three (TREECKO, TORCHIC, MUDKIP: `eyes/screens.py`
#: STARTER_OPTIONS), drawn once from the choices stream. Every one is possible for every personality (the design draft §10.5:
#: "the starter is SEEDED per run": the acceptance batch takes 3 per starter by seed, `gates/rate_step5.py`).
STARTER_LEAN: dict[str, tuple[float, float, float]] = {
    "Catcher": (0.34, 0.33, 0.33), "Story": (0.30, 0.35, 0.35), "Trainer": (0.30, 0.40, 0.30),
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


def choose_starter(choices: random.Random, personality: str, named: str | None = None) -> tuple[str, str]:
    """(the starter, why): the one the run names (`AI_PLAYER_STARTER`, the acceptance batch's seeding), or the
    personality's weighted draw."""
    options = ("TREECKO", "TORCHIC", "MUDKIP")
    if named:
        if named.upper() not in options:
            raise ValueError(f"starter must be one of {options}, got {named!r}")
        return named.upper(), "named by the run"
    lean = STARTER_LEAN.get(personality, STARTER_LEAN["Story"])
    return choices.choices(options, weights=lean)[0], f"the {personality}'s taste {dict(zip(options, lean))}"


# ------------------------------------------------------------------------------------------------ build step 5: errands
@dataclass(frozen=True)
class Errands:
    """How much a personality cares for each human errand (module docstring). Taste, not measured."""

    train_margin: int  # train until the strongest Pokemon is this many levels above the next known fight's strongest
    train_min_steps: int  # before a known fight, roam at least this many training steps (never straight in)
    train_session: int  # the training steps of one roaming session
    catch_seek: float  # the chance, on a map with grass not walked, that it roams there to meet new species (balls in hand)
    catch_roam_steps: int  # the roaming steps of such a session
    balls_low: int  # buy POKé BALLS when the bag holds fewer than this ...
    balls_buy: int  # ... this many at a time (money allowing)
    heal_below: float  # head for a POKéMON CENTER when the party's HP share falls under this (a centre known)
    chat: float  # the chance, when someone not talked to stands near, that it walks up and talks to them
    potions_buy: int  # POTIONS bought with the balls (a person stocks a few)
    # (build step 5.1, the step-5 review's finding 1: "it plays like a speedrun"; RULING 37 Q6: detours for exploring)
    # the chance, on an outdoor map new to it (its world memory, carried between sessions, had not stood there when this
    # session began; one draw a map, `brain/goals.py` may_look_around), that it looks around it first (Story least)
    look_around: float
    look_frames: int  # ... for this many frames (a bound, the errand's own budget)
    # the chance, travelling across an outdoor map toward a place it knows (one draw a map and milestone), of a short walk
    # to a place off the way, at least `brain/goals.py` DETOUR_MIN_TILES tiles from where it is, and a look there
    detour: float
    detour_frames: int  # ... for at most this many frames
    # (build step 5.2, the step-5.1 review's finding 2: "errands are filled by a quota, not interleaved": 5.1's BALANCE, a
    # share of the session's goal frames kept for errands, skipped the dice whenever it was short, and it was nearly the
    # quantity the graders' floor measured, so the AI aimed at the grader) BOREDOM instead: a person who has done nothing
    # but the story and its needs for a while grows CURIOUS. Every curiosity draw's odds rise SMOOTHLY from the
    # personality's own odds above to at most `brain/goals.py` CURIOUS_ODDS_CAP over this many frames since its last
    # curiosity that came to SOMETHING (a new place seen, an item, a catch, words, a talk: `brain/goals.py` goal_yield);
    # the dice are always thrown. Taste (the Catcher bores soonest, the Story player last), not measured from people.
    # (Lowered to 5,000 / 6,500 / 8,000 for the development sweeps step52dev3 and dev4 when a chapter-2 run fell under the
    # old floor of errands, `gates/rate_step5.py` MIX_MIN, and RESTORED: tuning a taste toward a share of frames is the
    # AI aiming at the grader's quantity again (`LESSONS.md` PF-14); the share floors are reported since 5.2, by the step's
    # own P2: "grade YIELD and SPACING, not share of frames")
    bored_frames: int = 12_000


ERRANDS: dict[str, Errands] = {
    "Catcher": Errands(train_margin=2, train_min_steps=100, train_session=120, catch_seek=0.9, catch_roam_steps=120,
                       balls_low=8, balls_buy=10, heal_below=0.5, chat=0.12, potions_buy=1,
                       look_around=0.8, look_frames=4200, detour=0.5, detour_frames=1500, bored_frames=8_000),
    "Story": Errands(train_margin=1, train_min_steps=80, train_session=100, catch_seek=0.3, catch_roam_steps=60,
                     balls_low=4, balls_buy=5, heal_below=0.6, chat=0.18, potions_buy=2,
                     look_around=0.55, look_frames=3000, detour=0.35, detour_frames=1200, bored_frames=12_000),
    "Trainer": Errands(train_margin=3, train_min_steps=150, train_session=150, catch_seek=0.45, catch_roam_steps=80,
                       balls_low=5, balls_buy=5, heal_below=0.45, chat=0.3, potions_buy=2,
                       look_around=0.7, look_frames=3600, detour=0.45, detour_frames=1500, bored_frames=10_000),
}
#: DRIFT (module docstring): every this many STEPS walked, one draw ...
DRIFT_EVERY = 400
#: ... with this chance switches the active personality to another ...
DRIFT_CHANCE = 0.25
#: ... for a number of steps drawn from this range, then back to the base.
DRIFT_STEPS = (250, 700)


class PersonalityState:
    """The personality AS IT PLAYS: the `base` it keeps, the `active` one it may drift into for a while (by STEPS walked,
    `step(steps)`), its errand weights (`errands`: the ACTIVE personality's), and its favourite species. Every draw is
    from its own seeded stream; every change is told through `say` and kept in `history` (the step it happened at)."""

    def __init__(self, base: str, rng: random.Random, say=None, drift_on: bool = True) -> None:
        self.base = base
        self.active = base
        self.rng = rng
        self.say = say
        self.drift_on = drift_on
        self.drift_until: int | None = None
        self.next_draw = DRIFT_EVERY
        self.history: list[dict] = []
        self.favourite: str | None = None
        #: the drift draws made so far (the rate of drifts is DRIFT_CHANCE of these: `gates/test_goals.py` DriftTests)
        self.draws = 0

    @property
    def errands(self) -> Errands:
        return ERRANDS.get(self.active, ERRANDS["Story"])

    def step(self, steps: int) -> str | None:
        """The player has walked `steps` steps in all: drift into another personality, or back to the base. Returns what
        changed (also told), or None."""
        if self.drift_until is not None and steps >= self.drift_until:
            was, self.active, self.drift_until = self.active, self.base, None
            return self._tell(steps, "back", f"the drift into {was} is over at step {steps}: back to {self.base}")
        if not self.drift_on or self.drift_until is not None:
            return None
        if steps < self.next_draw:
            return None
        self.next_draw = (steps // DRIFT_EVERY + 1) * DRIFT_EVERY
        self.draws += 1
        roll = self.rng.random()
        if roll >= DRIFT_CHANCE:
            return None
        other = self.rng.choice([p for p in PERSONALITIES if p != self.base])
        length = self.rng.randint(*DRIFT_STEPS)
        self.active, self.drift_until = other, steps + length
        return self._tell(steps, "drift", f"at step {steps} (draw {roll:.2f} < {DRIFT_CHANCE}) it drifts from {self.base} into "
                                          f"{other} for {length} steps, until step {self.drift_until}")

    def _tell(self, steps: int, kind: str, line: str) -> str:
        self.history.append({"step": steps, "kind": kind, "active": self.active, "line": line})
        if self.say is not None:
            self.say(f"[AI-PERSONALITY] {line}")
        return line


_WILD: dict[str, tuple[str, ...]] = {}


def wild_species() -> tuple[str, ...]:
    """The species a person can meet in the wild in Emerald (`knowledge/wild_species.json`, read once)."""
    if "species" not in _WILD:
        path = Path(__file__).parent / "knowledge" / "wild_species.json"
        _WILD["species"] = tuple(json.loads(path.read_text(encoding="utf-8"))["species"])
    return _WILD["species"]


def choose_favourite(choices: random.Random) -> str:
    """The run's FAVOURITE POKéMON: one wild-catchable species, drawn once (module docstring)."""
    return choices.choice(wild_species())
