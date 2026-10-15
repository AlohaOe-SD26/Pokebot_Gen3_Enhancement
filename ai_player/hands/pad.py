"""The AI's PAD: buttons pressed at a PERSON'S pace, every press logged with why it was allowed (build step 2).

WHY (USER RULING 37 Q6: "HUMAN pacing, but always goal-directed and never idle"): a person holds a button
for a few frames, leaves a moment between two presses, and reads a text before moving it on; a bot presses
for one frame on the first frame it can. The pad turns every press into a short HOLD of a jittered length
followed by a jittered gap, and gives the dialogue driver a READING DELAY proportional to the length of the
text on screen (bounded: 0.3 s to 2.5 s of game time). The jitter is seeded (one logged seed per run, its own
stream so that pacing never changes a choice), and every bound is a constant below.

NEVER IDLE WITHOUT A REASON. The pad has no bare "wait": `idle(frames, reason)` and `busy(reason)` both take a
reason, and the reason is LOGGED (consecutive frames with the same reason are one record, so a long cutscene
is one line, not a thousand). For step 2 that is the whole of "never idle": the AI only stands still while it
reads, thinks about a menu for a moment, or watches the game do something it cannot hurry.

EVERY PRESS NAMES ITS GATE. `press(button, why, gate)` refuses an empty gate: the gate is what the eyes said
on the look right before the press ("text printer 0 CLEAR", "yes_no cursor on YES", "naming: cursor on 'R'"),
and it is in the action log next to the press. That is what makes "every A that advanced a text was gated on
the eyes' waits-for-button" checkable from the log (`gates/test_hands.py`, `gates/live_step2.py`): the
museum-greeter lesson (`PROJECT KNOWLEDGE/08-MISTAKES.md`, 2026-07-23): A pressed when nothing waits STARTS a
conversation or picks a choice. The FAULT arm presses with the gate "NONE (FAULT ...)" so the log says so.

Every press goes through the brain's `Controls` (`ai_player/mode.py`), i.e. the host's controller, so the
purity instrument counts it as the AI's (`ai_presses`).
"""

from __future__ import annotations

import random
from collections.abc import Callable, Generator
from dataclasses import dataclass

__all__ = ["HUMAN_PACING", "MAX_IDLE_FRAMES", "Faults", "Hands", "Pacing", "Pad", "PadError"]

#: No single idle may last longer than this (a minute of game time): a longer one is a bug in the caller.
MAX_IDLE_FRAMES = 3600


class PadError(ValueError):
    pass


@dataclass(frozen=True)
class Pacing:
    """How a person's hands move, in FRAMES (60 a second). Every value is a (low, high) range the pad draws
    from, or a bound. Measured nowhere: they are a plausible human tempo, chosen to be clearly slower than
    the bot's one-frame presses and well inside every timing the game needs (a direction held shorter than
    a step's 16 frames only turns the player; a held key REPEATS only after `gKeyRepeatStartDelay` frames:
    40, `src/main.c`, and 16 on the naming screen, `src/naming_screen.c` NamingScreen_Init, so the longest
    press here, 7 frames, is one key press everywhere)."""

    press: tuple[int, int] = (3, 7)  # a press is held 50-117 ms
    gap: tuple[int, int] = (8, 18)  # then 133-300 ms before the next press of a sequence
    think: tuple[int, int] = (14, 45)  # a menu just opened: look at it for 0.23-0.75 s before acting
    turn: tuple[int, int] = (2, 4)  # turning in place: a short tap (a step would take 16 frames)
    read_base: int = 18  # a text: 0.3 s to take it in ...
    read_per_char: float = 2.4  # ... plus 2.4 frames a character (25 characters a second) ...
    read_max: int = 150  # ... at most 2.5 s, however long the page
    read_jitter: float = 0.2  # +-20 % on every reading delay


#: The pacing of every real run. (A test may pass a faster one; nothing in the package does.)
HUMAN_PACING = Pacing()


class Pad:
    """Buttons and time for the hands. `controls` is the brain's `Controls`; `record(decision, action, reason,
    extra)` writes one action-log record (the caller attaches the latest look's digest)."""

    def __init__(self, controls, rng: random.Random, record: Callable[[str, str, str, dict], None],
                 pacing: Pacing = HUMAN_PACING) -> None:
        self._controls = controls
        self._rng = rng
        self._record = record
        self.pacing = pacing
        #: Frames the pad has let pass (presses, gaps, idles), counted ONE BY ONE as each is handed on (`_count`).
        self.frames = 0
        self.presses = 0
        self.history: list[dict] = []  # every press: frame index, button, hold, gap, gate, why
        self._idle_reason: str | None = None
        self._idle_frames = 0
        self._last_idle: str | None = None

    @property
    def doing(self) -> str | None:
        """(build step 5.1) What the pad says it is doing while no button is pressed: the busy reason of the frames under
        way, else the last idle's reason (reading, thinking). For the log only (`hands/waiting.py` names it beside a long
        wait for a press); nothing decides by it."""
        return self._idle_reason or self._last_idle

    # ------------------------------------------------------------------ presses
    def press(self, button: str, why: str, gate: str, hold: int | None = None) -> Generator[None, None, None]:
        """Press `button` like a person: held for a jittered few frames, then a jittered gap. `gate` is what
        the eyes said that allowed this press; it may not be empty."""
        if not gate:
            raise PadError(f"a press of {button} without a gate ({why})")
        self._flush_idle()
        held = hold if hold is not None else self._rng.randint(*self.pacing.press)
        gap = self._rng.randint(*self.pacing.gap)
        entry = {"at": self.frames, "button": button, "hold": held, "gap": gap, "gate": gate, "why": why}
        self.history.append(entry)
        self.presses += 1
        self._record(why, f"press {button} {held}f", gate, {"hold": held, "gap": gap, "pad_frame": self.frames})
        yield from self._count(self._controls.hold(button, held))
        yield from self._count(self._controls.wait(gap))

    def turn(self, button: str, why: str, gate: str) -> Generator[None, None, None]:
        """A short tap of a direction: the player turns to face it without taking a step."""
        yield from self.press(button, why, gate, hold=self._rng.randint(*self.pacing.turn))

    def hold(self, button: str, frames: int, why: str, gate: str) -> Generator[None, None, None]:
        """Hold `button` for exactly `frames` frames, on purpose (the clock's hand turns while it is held)."""
        if not gate:
            raise PadError(f"a hold of {button} without a gate ({why})")
        if not 1 <= frames <= MAX_IDLE_FRAMES:
            raise PadError(f"a hold of {frames} frames")
        self._flush_idle()
        entry = {"at": self.frames, "button": button, "hold": frames, "gap": 0, "gate": gate, "why": why}
        self.history.append(entry)
        self.presses += 1
        self._record(why, f"hold {button} {frames}f", gate, {"hold": frames, "pad_frame": self.frames})
        yield from self._count(self._controls.hold(button, frames))

    # ------------------------------------------------------------------ time, always with a reason
    def idle(self, frames: int, reason: str) -> Generator[None, None, None]:
        """Let `frames` frames pass on purpose: reading, thinking about a menu. Logged with its reason."""
        if not reason:
            raise PadError("an idle without a reason")
        if not 0 <= frames <= MAX_IDLE_FRAMES:
            raise PadError(f"an idle of {frames} frames ({reason})")
        if frames == 0:
            return
        self._flush_idle()
        self._record("idle", f"idle {frames}f", reason, {"pad_frame": self.frames})
        self._last_idle = reason
        yield from self._count(self._controls.wait(frames))

    def busy(self, reason: str) -> Generator[None, None, None]:
        """One frame of watching the game do something the AI cannot hurry (a text printing, a fade, a scene).
        Consecutive frames with the same reason are logged as ONE record when the reason changes."""
        if not reason:
            raise PadError("a busy frame without a reason")
        if reason != self._idle_reason:
            self._flush_idle()
            self._idle_reason = reason
        self._idle_frames += 1
        yield from self._count(self._controls.wait(1))

    def _count(self, frames: Generator[None, None, None]) -> Generator[None, None, None]:
        """Hand on the frames of one `Controls` action, COUNTING each as it is handed on.

        STEP 2.1 (the step-2 review, item 3: "assert pad frames == counters.real_frames"): the pad used to add a
        press's hold and gap to `frames` after the whole press, so a skill STOPPED mid-press (the brain's frame
        budget, `mode.py` HandsBrain._bounded) left those frames uncounted. Measured on the step-2 evidence: the
        two arms stopped by their budget logged `frames=11999` against the instrument's `real_frames=12000` (XBN)
        and 5991 against 6000 (XBC); the arms that ended by themselves agreed. Counting here makes the pad's count
        the frames that really ran, which `gates/live_step2.py` now asserts against the instrument on every
        launcher arm. The inner action is CLOSED with this one (a hold always releases its button)."""
        try:
            for _ in frames:
                self.frames += 1
                yield
        finally:
            frames.close()

    def finish(self) -> None:
        """Write out a pending busy record (the brain calls this when a skill ends)."""
        self._flush_idle()

    def _flush_idle(self) -> None:
        if self._idle_reason is not None and self._idle_frames:
            self._record("watch", f"busy {self._idle_frames}f", self._idle_reason,
                         {"pad_frame": self.frames - self._idle_frames})
        self._idle_reason = None
        self._idle_frames = 0

    # ------------------------------------------------------------------ human delays
    def reading_frames(self, characters: int) -> int:
        """How long a person reads `characters` new characters: base + per character, +-20 %, bounded."""
        pacing = self.pacing
        raw = pacing.read_base + pacing.read_per_char * max(0, characters)
        raw *= 1.0 + self._rng.uniform(-pacing.read_jitter, pacing.read_jitter)
        return int(min(max(raw, pacing.read_base), pacing.read_max))

    def think_frames(self) -> int:
        return self._rng.randint(*self.pacing.think)


@dataclass(frozen=True)
class Faults:
    """FAULT switches of the hands (read by the host from the environment, `ai_player/options.py`); none is
    set on the happy path. Each makes the hands do what a NAIVE driver does, so a fault arm can show the harm
    the real driver avoids (`gates/live_step2.py`)."""

    #: The dialogue driver presses A on its cadence whatever the screen shows: no wait gate, no menu check.
    ungated_a: bool = False
    #: The menu driver moves a cursor by a press COUNT from the top, without reading where the cursor is.
    blind_count: bool = False


class Hands:
    """What every skill holds: the eyes it looks with, the PAD it presses with (built here, on the brain's
    `Controls`), the run's CHOICES random stream (gender, name, ...: a different stream from the pad's
    pacing, so pacing never changes a choice), the fault switches, and the action log. `look()` remembers
    the latest Observation, and every record the hands write carries that look's digest."""

    def __init__(self, eyes, controls, pacing_rng: random.Random, choices: random.Random, actions,
                 say: Callable[[str], None], faults: Faults = Faults(), pacing: Pacing = HUMAN_PACING) -> None:
        self.eyes = eyes
        self.choices = choices
        self.actions = actions
        self.say = say
        self.faults = faults
        self.last = None
        self.looks = 0
        self.pad = Pad(controls, pacing_rng, self.note, pacing)
        #: BUILD STEP 3: callables told EVERY look (the world model, `world/memory.py` WorldMemory.observe), so what the
        #: eyes showed during a scene, a menu or a battle is remembered too, not only what the navigator looked at.
        self.watchers: list[Callable] = []

    def look(self):
        self.last = self.eyes.look()
        self.looks += 1
        for watcher in self.watchers:
            watcher(self.last)
        return self.last

    def note(self, decision: str, action: str, reason: str, extra: dict | None = None) -> None:
        """One action-log record, with the latest look's digest and frame."""
        if self.actions is not None:
            self.actions.record(self.last, decision=decision, action=action, reason=reason, extra=extra or None)

    def tell(self, line: str) -> None:
        """A line for people (the run's log), also in the action log."""
        self.say(f"[AI-HANDS] {line}")
        self.note("tell", "say", line)
