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
from ai_player.hands.dialogue import awaits_press

__all__ = ["NOTE_FRAMES", "WaitWatch"]

#: Stretches at least this long (frames) are written to the action log (shorter ones are only counted).
NOTE_FRAMES = 60


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
