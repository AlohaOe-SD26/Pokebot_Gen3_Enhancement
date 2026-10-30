"""POLICY (R1, build spec 2026-10-29 section 3 (d); D2, D3, D17): WHEN the AI saves its game. Framework-free, deciding code.

USER RULING 51 (option A): a person saves "at a Pokemon Center, before a gym leader, and after a big story moment". So a save is
DUE:
  * AT A POKéMON CENTER: a `heal` goal that returned "healed" on a map whose const ends `CENTER_SUFFIX` (`after_heal`). The due
    EXPIRES when the player leaves that map unsaved (`due_now`): a person saves at the centre, not three routes later;
  * AFTER A BIG STORY MOMENT: one of `BIG_MOMENTS` passed (`after_milestones`, given milestone IDS only, D18: the marks and the
    flags never reach this module);
  * RIGHT BEFORE A GYM LEADER (finding m2): checked when the story goal about to be returned is the `talk` step of a milestone
    whose fight the game NAMES, and the player stands on that step's GYM map (`before_leader`). Once per APPROACH: an approach
    is the newest map change onto that gym (`world.transitions`); if it leaves to heal or train and comes back, it saves again
    before the talk. A save made since it entered, or within `SAVE_MIN_MINUTES` of game time (a centre save just before),
    counts as that save.
The newest reason wins, and one save satisfies every due (`record_save`). A save is never two within `SAVE_MIN_MINUTES` game
minutes: a due whose only obstacle is that gap is COVERED by the recent save and dropped (said), never saved later somewhere
that is no moment at all. With fewer than `SAVE_FRAMES_NEEDED` frames left, or no play time read, the due waits, told once.

`SavePolicy` holds NO state of its own: its state is the goal manager's memory (`brain/goals.py` _Memory: `save_due`,
`saved_for`, `last_save`), so a continue restores it with the rest (`game_memory.py` D16: `saved_for` and `last_save` KEEP,
`save_due` RESET). It answers; the goal manager (step 5) turns a `SaveChoice` into a `save` goal, after HEAL (block 1b) and in
STORY (block 8), and the play brain runs `skills/saving.py` save_game for it.

This module imports nothing from `brain/goals.py` (which will import it): `CENTER_SUFFIX` and the gym rule are this module's
own, and `gates/test_saving.py` pins them equal to the goal manager's.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ai_player.brain.navigator import nav_free
from ai_player.eyes.observation import Observation
from ai_player.knowledge.story import load_story
from ai_player.skills.saving import SAVE_FRAMES_NEEDED

__all__ = [
    "BIG_MOMENTS",
    "CENTER_SUFFIX",
    "DUE_KINDS",
    "GYM_SUFFIX",
    "SAVE_MIN_MINUTES",
    "SaveChoice",
    "SavePolicy",
    "milestone_ids",
    "own_cart",
]

#: D3, after a big story moment (USER RULING 51; U1 open): the starter is the player's; the first win over the rival; the
#: POKéDEX from PROF. BIRCH; the end of WALLY's catching tutorial; the DEVON researcher saved in PETALBURG WOODS; the STONE
#: BADGE. One constant; `gates/test_saving.py` checks every id is a milestone of `knowledge/milestones.json`.
BIG_MOMENTS = ("ch1_lab", "ch1_rival_route103", "ch1_pokedex", "ch2_wally", "ch3_woods", "ch4_roxanne")
#: No two saves within this many minutes of GAME play time (T2: for every moment).
SAVE_MIN_MINUTES = 3
#: A POKéMON CENTER's ground floor (= `brain/goals.py` CENTER_SUFFIX; pinned by a test) and a town's GYM (`is_gym`'s rule).
CENTER_SUFFIX = "POKEMON_CENTER_1F"
GYM_SUFFIX = "GYM"
DUE_KINDS = ("center", "moment", "leader")
_IDS: list[frozenset[str]] = []


def milestone_ids() -> frozenset[str]:
    """Every milestone id of `knowledge/milestones.json` (read once)."""
    if not _IDS:
        _IDS.append(frozenset(milestone.id for milestone in load_story(None).milestones))
    return _IDS[0]


def own_cart(cart: str | None, saved_this_run: bool) -> bool:
    """D17: whether a save already on the cartridge is this game's own, so "There is already a saved file" is answered YES:
    the launcher emptied the cart for this run (`empty`), the run CONTINUED that save (`continued`), or this run has saved
    already. A cart it was handed as it was (`kept`) holds a save it does not know: NO."""
    return bool(saved_this_run) or cart in ("empty", "continued")


@dataclass(frozen=True)
class SaveChoice:
    """A save the policy wants now: which due (`kind`), why (for the goal's reason), the goal key, the milestone (leader)."""

    kind: str
    reason: str
    key: str
    milestone: str | None = None


def _minutes(play_time) -> int:
    return int(play_time[0]) * 60 + int(play_time[1])


def _hours_minutes(play_time) -> str:
    return f"{int(play_time[0])}:{int(play_time[1]):02d}"


class SavePolicy:
    """When to save (module docstring). `memory` is the goal manager's `_Memory` (kept as `goal_memory`: the call-site census
    matches names, and `.memory` is everywhere); `say` a line for the run's log."""

    def __init__(self, memory, say=None) -> None:
        self.goal_memory = memory
        self._say = say if say is not None else (lambda line: None)

    # ------------------------------------------------------------------ what makes a save due
    def after_heal(self, goal, ok: bool, here_const: str | None) -> bool:
        """A heal goal ended: a save is due when it HEALED at a POKéMON CENTER (MOM's heal at home is no centre)."""
        if goal is None or goal.kind != "heal" or not ok or not here_const or not here_const.endswith(CENTER_SUFFIX):
            return False
        self._make_due("center", f"it healed at the POKéMON CENTER ({here_const})", here_const)
        return True

    def after_milestones(self, passed_ids: Iterable[str]) -> bool:
        """Milestones just passed, by their IDS ONLY (D18): a save is due after a big story moment. Anything that is not a
        milestone id (the marks, a flag's name) is REFUSED: only ids reach this module."""
        if isinstance(passed_ids, (str, bytes, dict)):
            raise TypeError(f"after_milestones takes milestone ids, not {type(passed_ids).__name__}")
        ids = list(passed_ids)
        known = milestone_ids()
        for item in ids:
            if not isinstance(item, str) or item not in known:
                raise ValueError(f"after_milestones takes milestone ids only: {item!r} is not one")
        moments = [item for item in ids if item in BIG_MOMENTS]
        if not moments:
            return False
        self._make_due("moment", f"a big story moment: {moments[-1]}", None, milestone=moments[-1])
        return True

    def _make_due(self, kind: str, why: str, place: str | None, milestone: str | None = None,
             entered: int | None = None) -> None:
        self.goal_memory.save_due = {"kind": kind, "why": why, "map": place, "milestone": milestone, "entered": entered,
                                "told": None}
        self._say(f"[AI-SAVE] a save is due: {why}")

    def due_now(self, here_const: str | None) -> dict | None:
        """The save due now, after expiring a centre's (or a leader's) when the player has left its map unsaved."""
        due = self.goal_memory.save_due
        if due is None:
            return None
        if due["kind"] in ("center", "leader") and here_const is not None and here_const != due["map"]:
            self._say(f"[AI-SAVE] the save due ({due['why']}) expired: it left {due['map']} unsaved")
            self.goal_memory.save_due = None
            return None
        return due

    # ------------------------------------------------------------------ whether it may save now
    def _blocker(self, look: Observation, frames_left: int) -> tuple[str | None, str]:
        """(what stands in the way, in words): "play_time", "gap", "frames", "busy", or (None, "")."""
        progress = look.progress
        play_time = progress.play_time if progress is not None else None
        if play_time is None:
            return "play_time", "the play time is not read"
        last = self.goal_memory.last_save
        if last is not None and last.get("play_time") is not None:
            since = _minutes(play_time) - _minutes(last["play_time"])
            if since < SAVE_MIN_MINUTES:
                return "gap", (f"its last save was at {_hours_minutes(last['play_time'])}, {since} game minutes ago (at least "
                               f"{SAVE_MIN_MINUTES} between saves)")
        if frames_left < SAVE_FRAMES_NEEDED:
            return "frames", f"{frames_left} frames left in the run (a save needs {SAVE_FRAMES_NEEDED})"
        if not nav_free(look):
            return "busy", "the screen is not free"
        return None, ""

    def may_save(self, look: Observation, frames_left: int) -> tuple[bool, str]:
        """Every condition of a save (spec 3 (d)): the play time read, `SAVE_MIN_MINUTES` since the last save,
        `SAVE_FRAMES_NEEDED` frames left, a free screen. (True, "") or (False, why)."""
        code, why = self._blocker(look, frames_left)
        return code is None, why

    def _wait(self, due: dict, code: str, why: str) -> None:
        """A due that cannot be saved now: COVERED by a recent save (the gap: dropped), or waiting (told once)."""
        if code == "gap":
            self._say(f"[AI-SAVE] no save for '{due['why']}': {why}; that save covers it")
            if due["kind"] == "leader" and due.get("milestone"):
                self.goal_memory.saved_for[due["milestone"]] = due.get("entered")
            self.goal_memory.save_due = None
            return
        if due.get("told") != why:
            due["told"] = why
            self._say(f"[AI-SAVE] the save due ({due['why']}) waits: {why}")

    # ------------------------------------------------------------------ the choices (the goal manager's blocks 1b and 8)
    def next_save(self, look: Observation, here_const: str | None, frames_left: int) -> SaveChoice | None:
        """Block 1b (right after HEAL): a save for a centre's or a big moment's due, if it may save now."""
        due = self.due_now(here_const)
        if due is None or due["kind"] == "leader":
            return None
        code, why = self._blocker(look, frames_left)
        if code is not None:
            self._wait(due, code, why)
            return None
        return SaveChoice(due["kind"], f"a save: {due['why']}", f"save:{due['kind']}", due.get("milestone"))

    def before_leader(self, look: Observation, world, milestone, step, story_goal,
                      frames_left: int) -> SaveChoice | None:
        """Block 8: the story goal about to be returned. A save goal in its place when it is the TALK to a gym leader (a
        named fight, on that step's gym map) and no save was made in this approach to the gym."""
        if story_goal is None or story_goal.kind != "talk" or step is None or step.do != "talk" \
                or not milestone.fight_named:
            return None
        here = world.here()
        const = here.const if here is not None else None
        if const is None or const != step.map or not const.endswith(f"_{GYM_SUFFIX}"):
            return None
        key = world.current
        entered = next((change.frame for change in reversed(world.transitions) if change.target == key), None)
        if milestone.id in self.goal_memory.saved_for and self.goal_memory.saved_for[milestone.id] == entered:
            return None  # saved in this approach already
        last = self.goal_memory.last_save
        if last is not None and entered is not None and int(last.get("frame", -1)) >= entered:
            self.goal_memory.saved_for[milestone.id] = entered  # a save since it entered the gym is the save before the leader
            return None
        due = self.goal_memory.save_due
        if due is None or due["kind"] != "leader" or due.get("milestone") != milestone.id or due.get("entered") != entered:
            self._make_due("leader", f"right before it talks to the leader ({milestone.title}, {const})", const,
                      milestone=milestone.id, entered=entered)
            due = self.goal_memory.save_due
        code, why = self._blocker(look, frames_left)
        if code is not None:
            self._wait(due, code, why)
            return None
        return SaveChoice("leader", f"a save: {due['why']}", f"save:leader:{milestone.id}", milestone.id)

    # ------------------------------------------------------------------ after a save
    def saved_state(self, play_time, frame: int, save_id: int, why: str) -> dict:
        """What save `save_id` makes of the policy's fields, as NEW values (the live memory is not touched): `last_save`
        is this save, a leader's approach is `saved_for`, no save is `save_due`. `record_save` sets exactly these.
        (R1 fix round, review R-1) The save's OWN memory line carries them: its payload is built at the START of the
        write, before the SAVED page records the save, so without them a continue from save k remembered save k-1 as its
        last save and no leader save for this approach, and saved AGAIN at once (the 3-minute rule and D3's "once per
        approach" broken)."""
        saved_for = dict(self.goal_memory.saved_for)
        due = self.goal_memory.save_due
        if due is not None and due["kind"] == "leader" and due.get("milestone"):
            saved_for[due["milestone"]] = due.get("entered")
        stamp = None if play_time is None else [int(play_time[0]), int(play_time[1])]
        return {"saved_for": saved_for, "last_save": {"id": int(save_id), "play_time": stamp, "frame": int(frame),
                                                      "why": why}, "save_due": None}

    def record_save(self, play_time, frame: int, save_id: int, why: str) -> None:
        """A save was made ("saved" on the SAVED page): it satisfies every due; a leader's approach is saved for."""
        state = self.saved_state(play_time, frame, save_id, why)
        self.goal_memory.saved_for.update(state["saved_for"])
        self.goal_memory.last_save = state["last_save"]
        self.goal_memory.save_due = state["save_due"]
