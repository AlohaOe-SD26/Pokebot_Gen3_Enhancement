"""(build step 5.1) WAITING ON A PRESS: how long a screen that waits for a button stood with no press. Framework-free.

WHY (the step-5 verifier's FAILURE, USER RULING 37 Q6 "never idle: it never stands still"): twice a run the AI stood
600 to 1,200 frames in front of a screen that waited for a press, a yes/no ("Do you choose this POKéMON?") or a text
waiting for A, each time under a busy REASON that was not true ("waiting for the choose_starter to open", "waiting until
the player is free to talk"). The step-5 check counted only the catch-all reason, so a stand-still under any NAMED
reason passed. A reason is a label; this is the PROPERTY: what the screen showed, and whether a press came.

THE RULE: a screen WAITS FOR A PRESS when the eyes say a text waits for A or B, or a menu (a yes/no, a list, a cursor)
takes input (`hands/dialogue.py` awaits_press). `WaitWatch`, a hands watcher, is told every look: a STRETCH begins at the
first look that waits for a press after the last press, and ends at the next press (the pad's count moved) or at the
first look that does not wait. A person reads before pressing, so a stretch of a few seconds is human pace (the pad's
reading delay is at most `Pacing.read_max` frames, its thinking pause `Pacing.think`); the graders bound the LONGEST
(`gates/live_step5.py`, `gates/rate_step5.py`: `AWAIT_MAX`). Every stretch of `NOTE_FRAMES` or more is written to the
action log (`decision` "await") with its frames, what waited and the busy reason the pad was giving meanwhile, and the
play brain's end record carries the longest (`WaitWatch.summary`).
"""

from __future__ import annotations

from collections.abc import Callable

from ai_player.eyes.observation import Observation
from ai_player.hands.dialogue import awaits_press, player_free

__all__ = ["BATTLE_STATES", "NOTE_FRAMES", "PUSH_NOTE", "BattleClock", "PushWatch", "WaitWatch"]

#: Stretches at least this long (frames) are written to the action log (shorter ones are only counted).
NOTE_FRAMES = 60
#: (build step 5.2) pressing stretches at least this long (free frames) are written to the action log (`PushWatch`)
PUSH_NOTE = 600


class WaitWatch:
    """Told every look (`Hands.watchers`); `presses()` is the pad's press count; `note(decision, action, reason, extra)`
    writes an action-log record; `doing()` the pad's current busy reason (or None)."""

    def __init__(self, presses: Callable[[], int], note: Callable[..., None],
                 doing: Callable[[], str | None] = lambda: None) -> None:
        self._presses = presses
        self._note = note
        self._doing = doing
        #: the open stretch: {"first", "last", "presses", "what", "doing"}
        self.current: dict | None = None
        self.longest: dict | None = None
        self.stretches = 0
        self.noted: list[dict] = []

    def __call__(self, look: Observation) -> None:
        waiting = awaits_press(look)
        presses = self._presses()
        stretch = self.current
        if stretch is not None and (waiting is None or presses != stretch["presses"]):
            self._close(stretch)
            stretch = self.current = None
        if waiting is None:
            return
        doing = self._doing()
        if stretch is None:
            self.current = {"first": look.frame, "last": look.frame, "presses": presses, "what": waiting,
                            "doing": [doing] if doing else []}
        else:
            stretch["last"] = look.frame
            # every reason the pad gave meanwhile, in order (the property is blind to them; the log says them all)
            if doing and doing not in stretch["doing"] and len(stretch["doing"]) < 4:
                stretch["doing"].append(doing)

    def _close(self, stretch: dict) -> None:
        frames = stretch["last"] - stretch["first"]
        self.stretches += 1
        if self.longest is None or frames > self.longest["frames"]:
            self.longest = {**stretch, "frames": frames}
        if frames >= NOTE_FRAMES:
            doing = "; then ".join(stretch["doing"])
            record = {"first": stretch["first"], "last": stretch["last"], "frames": frames, "what": stretch["what"],
                      "doing": doing}
            self.noted.append(record)
            self._note("await", f"{frames}f", f"a screen waited for a press {frames} frames ({stretch['what']}) while "
                                             f"{doing or 'it pressed nothing'}", record)

    def finish(self) -> None:
        """The run ends: an open stretch is closed (and noted when long enough)."""
        if self.current is not None:
            self._close(self.current)
            self.current = None

    def summary(self) -> dict:
        longest = self.longest or {}
        return {"stretches": self.stretches, "longest": longest.get("frames", 0), "longest_at": longest.get("first"),
                "longest_what": longest.get("what"), "noted": len(self.noted)}


class PushWatch:
    """(build step 5.2, the step-5.1 review's finding 5: "the stall check cannot see pushing against a blocker": at OLDALE
    about 1,160 presses moved the player 377 steps toward places someone stood in the way of, roughly 7,500 frames, and
    THE STALL PROPERTY passed, because no SCREEN waited for a press) PRESSING THAT BRINGS NOTHING NEW. Told every look
    (`Hands.watchers`): a STRETCH is the FREE time (the player free on the overworld: `player_free`, no fade, a view)
    since the last NEW thing: `novelty()` changed (the play brain passes its world memory's tiles learned and the maps it
    has stood on: a tile seen for the first time, a map stood on for the first time) or a battle began. Time that is not
    free (a text, a menu, a scene) PAUSES the stretch: it neither counts nor ends it (a text met again and again is not
    new). A stretch counts only when the pad PRESSED something in it (`presses()`): standing still is the stall
    property's business. Stretches of `PUSH_NOTE` free frames or more are written to the action log (`decision` "push"),
    the longest to the end record (`summary`); the graders bound the longest (`gates/rate_step5.py` PUSH_MAX, with the
    game's second path, `gates/play_harness.py` PlaceRecorder)."""

    def __init__(self, presses: Callable[[], int], note: Callable[..., None], novelty: Callable[[], tuple]) -> None:
        self._presses = presses
        self._note = note
        self._novelty = novelty
        self.mark: tuple | None = None
        #: the open stretch: {"first", "last", "frames" (free), "presses" (at its start)}
        self.current: dict | None = None
        self._free_at: int | None = None
        self.longest: dict | None = None
        self.stretches = 0
        self.noted: list[dict] = []

    def __call__(self, look: Observation) -> None:
        mark = self._novelty()
        battle = bool(look.screen.in_battle)
        if battle or mark != self.mark:
            self._end_stretch()
            self.mark = mark
            self._free_at = None
            if battle:
                return
        free = player_free(look) and not look.screen.fading and look.view is not None
        if not free:
            self._free_at = None  # paused: the time a text or a scene takes is no pressing
            return
        if self.current is None:
            self.current = {"first": look.frame, "last": look.frame, "frames": 0, "presses": self._presses(), "told": 0}
        elif self._free_at is not None:
            self.current["frames"] += max(0, look.frame - self._free_at)
            self.current["last"] = look.frame
            self._tell_open()
        self._free_at = look.frame

    def _tell_open(self) -> None:
        """(build step 5.2, the round's development sweep step52dev3: the BLOCKED control pushed against someone in the way
        for 136,370-244,940 free frames by the game's second path, and the AI's own record said 0-1,758, because a run cut
        off by its frame budget never ENDS its last stretch) a stretch still OPEN is written to the action log each time it
        grows by `PUSH_NOTE` frames with presses in it, so the AI's record has it whenever the run stops."""
        stretch = self.current
        if stretch is None or stretch["frames"] < stretch["told"] + PUSH_NOTE:
            return
        pressed = self._presses() - stretch["presses"]
        if pressed <= 0:
            return
        stretch["told"] = stretch["frames"]
        self._note("push", f"{stretch['frames']}f open", f"{stretch['frames']} free frames of pressing ({pressed} presses) "
                                                         f"with nothing new so far: the stretch goes on",
                   {"first": stretch["first"], "last": stretch["last"], "frames": stretch["frames"], "presses": pressed,
                    "open": True})

    def _end_stretch(self) -> None:
        stretch, self.current = self.current, None
        if stretch is None:
            return
        pressed = self._presses() - stretch["presses"]
        if pressed <= 0:
            return
        frames = stretch["frames"]
        self.stretches += 1
        record = {"first": stretch["first"], "last": stretch["last"], "frames": frames, "presses": pressed}
        if self.longest is None or frames > self.longest["frames"]:
            self.longest = record
        if frames >= PUSH_NOTE:
            self.noted.append(record)
            self._note("push", f"{frames}f", f"{frames} free frames of pressing ({pressed} presses) that brought nothing "
                                             f"new: no tile seen, no map stood on, no battle", record)

    def wind_up(self) -> None:
        """The run ends: an open stretch is closed (and noted when long enough). (Its own name: a call-site census by
        name must not take the many other `finish` calls for this one's.)"""
        self._end_stretch()

    def push_report(self) -> dict:
        """The end record's summary: the stretches counted, the longest, where it began, its presses, how many noted."""
        longest = self.longest or {}
        return {"stretches": self.stretches, "longest": longest.get("frames", 0), "longest_at": longest.get("first"),
                "longest_presses": longest.get("presses"), "noted": len(self.noted)}


#: the game states the eyes show while a battle is on screen (as `skills/flee.py` in_battle reads them)
BATTLE_STATES = ("BATTLE", "BATTLE_STARTING", "BATTLE_ENDING")


class BattleClock:
    """(build step 5.2, the round's development sweep step52dev2) The frames a BATTLE was on screen over the run, told every
    look (`Hands.watchers`): from one look in a battle to the next. A look round is judged by the new tiles it showed per
    frame of its OWN time (`brain/goals.py` goal_yield), and the battles met in the grass are not its time: a look round of
    ROUTE 101 that met 12 battles walked 1,561 of its 5,703 frames and showed 32 new tiles."""

    def __init__(self) -> None:
        self.battle_frames = 0
        self._at: int | None = None

    def __call__(self, look: Observation) -> None:
        if look.screen.in_battle or look.screen.game_state in BATTLE_STATES:
            if self._at is not None:
                self.battle_frames += max(0, look.frame - self._at)
            self._at = look.frame
        else:
            self._at = None
