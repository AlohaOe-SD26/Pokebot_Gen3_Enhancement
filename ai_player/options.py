"""Run options for the AI player, carried from the launcher to the mode through environment variables.

WHY ENVIRONMENT VARIABLES: the mode runs inside a separate `pokebot.py` process that the launcher
starts. The framework's command line has no slot for mode options, and editing the framework is
forbidden (RULING 37 Q2), so the environment is the only channel that needs no framework change.

WHY THE FAULT SWITCHES ARE READ HERE, INSIDE THE AI'S OWN CODE: a fault arm must exercise the real
production path, not a driver's imitation of it (CLAUDE.md rule 6; the story-drive protocol). The
happy path never sets any of them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ALL_SWITCHES",
    "BRAINS",
    "DEFAULT_BRAIN",
    "DEFAULT_FRAMES",
    "DEFAULT_MART_COUNT",
    "DEFAULT_MART_ITEM",
    "DEFAULT_WATCH_EVERY",
    "HANDS_BRAINS",
    "VERDICT_FILE_NAME",
    "ENV_BRAIN",
    "ENV_CLOCK",
    "ENV_CONTROL_TAP",
    "ENV_FAULT_BLIND_COUNT",
    "ENV_FAULT_HANG",
    "ENV_FAULT_KEEP_LISTENERS",
    "ENV_FAULT_MANUAL",
    "ENV_FAULT_NO_CROP",
    "ENV_FAULT_NO_REBIND",
    "ENV_FAULT_RAISE",
    "ENV_FAULT_SKIP_RESTORE",
    "ENV_FAULT_UNGATED_A",
    "ENV_FRAMES",
    "ENV_MART_COUNT",
    "ENV_MART_ITEM",
    "ENV_PACKAGE_ROOT",
    "ENV_PERSONALITY",
    "ENV_RUN_DIR",
    "ENV_SEED",
    "ENV_WALL_DEADLINE",
    "ENV_WATCH_EVERY",
    "HandsOptions",
    "RunOptions",
]

ENV_FRAMES = "AI_PLAYER_FRAMES"
ENV_RUN_DIR = "AI_PLAYER_RUN_DIR"
#: The folder that CONTAINS `ai_player/`. The hook APPENDS it to `sys.path` (never in front of the
#: standard library), and the session checks that `ai_player` really loaded from there.
ENV_PACKAGE_ROOT = "AI_PLAYER_PACKAGE_ROOT"
#: Unix time at which the mode ends ITSELF with reason `wall-clock`, a few seconds before the
#: launcher's hard kill, so that a run that runs out of time still prints its purity verdict.
ENV_WALL_DEADLINE = "AI_PLAYER_WALL_DEADLINE"

#: FAULT: skip removing the framework's listeners. Proves the foreign-press/write counters can fire.
ENV_FAULT_KEEP_LISTENERS = "AI_PLAYER_FAULT_KEEP_LISTENERS"
#: FAULT: the brain raises after a few frames. Proves a crash ENDS the process (never parks it).
ENV_FAULT_RAISE = "AI_PLAYER_FAULT_RAISE"
#: FAULT: a listener raises inside the framework's own exception handler, which switches the bot to
#: Manual (`modules/main.py` 155-166). Proves the guard ends the process instead of parking.
ENV_FAULT_MANUAL = "AI_PLAYER_FAULT_MANUAL"
#: FAULT: the brain blocks the main thread (bounded), so neither the guard nor the soft deadline can
#: run. Proves the launcher's HARD wall clock still ends the run, and says it has no verdict (arm T2);
#: and that Ctrl+Break in the framework's own console still ends it, WITH a verdict, through the
#: session's interrupt watch (arm IH).
ENV_FAULT_HANG = "AI_PLAYER_FAULT_HANG"
#: FAULT: isolation does NOT take over the framework's listener-rebuild door
#: (`modules.main.get_bot_listeners`). With a reset or a rewind in the run, the framework's fresh
#: listeners come back without the AI's guard: proves the instrument's per-frame isolation check
#: ends that run as `isolation-lost` instead of letting it starve silently.
ENV_FAULT_NO_REBIND = "AI_PLAYER_FAULT_NO_REBIND"
#: FAULT: isolation does not give the framework its listener list back at the end. Proves the hook's
#: INDEPENDENT `[AI-HOOK]` observation of the list at process exit can fail (it is not true by
#: construction).
ENV_FAULT_SKIP_RESTORE = "AI_PLAYER_FAULT_SKIP_RESTORE"
#: CONTROL (not a fault): the placeholder taps B through the controller. Proves AI presses are
#: COUNTED as AI presses, so `ai_presses=0` in the normal arm is a measurement, not a dead counter.
ENV_CONTROL_TAP = "AI_PLAYER_CONTROL_TAP"
#: FAULT (build step 1): the eyes do NOT crop to the on-screen view, so every object the game has
#: loaded (up to ~10 tiles away, off screen) and every sign of the map is "seen". Proves the crop is
#: what keeps off-screen things out of an Observation (design draft §10.7: a person cannot see them),
#: i.e. that the "outside object is absent" check is not true by construction (live arm E2X).
ENV_FAULT_NO_CROP = "AI_PLAYER_FAULT_NO_CROP"

#: Which brain plays (build step 1). `placeholder` is step 0's (presses nothing, waits, gives up);
#: `watcher` OBSERVES every `AI_PLAYER_WATCH_EVERY` frames through the eyes, writes each Observation
#: to the action log and the scorer-compatible lines to the run's log, and presses nothing.
#: Build step 2 adds the HANDS brains (`HANDS_BRAINS`), each of which plays ONE skill with the AI's own
#: hands and gives up with the skill's outcome: `intro` (fresh boot to the truck), `nurse` (heal at the
#: nurse in front of the player), `mart` (buy at the clerk in front of the player), `clock` (set the wall
#: clock in front of the player).
ENV_BRAIN = "AI_PLAYER_BRAIN"
ENV_WATCH_EVERY = "AI_PLAYER_WATCH_EVERY"
HANDS_BRAINS = ("intro", "nurse", "mart", "clock")
BRAINS = ("placeholder", "watcher") + HANDS_BRAINS
DEFAULT_BRAIN = "placeholder"
DEFAULT_WATCH_EVERY = 60

#: BUILD STEP 2, the hands brains' options. WHY THE BRAIN READS THEM ITSELF: the host (`ai_player/host/`) is
#: FINISHED (the orchestrator's rule for step 2: no change to the purity layer), and the session hands the
#: brain only step 0's `BrainSettings`; so `ai_player/mode.py` `Brain` reads these through `HandsOptions`
#: from the SAME environment the session read its options from.
#: The run's seed (an integer): the choices stream (gender, name, personality) and the pacing stream are
#: both derived from it. Unset: a seed from the clock, logged.
ENV_SEED = "AI_PLAYER_SEED"
#: The base personality (Catcher, Story, Trainer); unset: drawn from the seed.
ENV_PERSONALITY = "AI_PLAYER_PERSONALITY"
#: The mart brain: what to buy and how many (default "POKé BALL" x 5).
ENV_MART_ITEM = "AI_PLAYER_MART_ITEM"
ENV_MART_COUNT = "AI_PLAYER_MART_COUNT"
#: The clock brain: the time to set, "HH:MM" (default: the computer's local time, as a person would).
ENV_CLOCK = "AI_PLAYER_CLOCK"
#: FAULT (build step 2): the dialogue driver presses A on its cadence without the eyes' wait gate and never
#: stops for a menu (the naive driver; `hands/pad.py` Faults). Proves the gate is what keeps choices by intent.
ENV_FAULT_UNGATED_A = "AI_PLAYER_FAULT_UNGATED_A"
#: FAULT (build step 2): the menu driver moves a cursor by a press count from the top without reading it.
#: Proves reading the cursor is what types the right name (the keyboard's cursor starts on the last key).
ENV_FAULT_BLIND_COUNT = "AI_PLAYER_FAULT_BLIND_COUNT"
DEFAULT_MART_ITEM = "POKé BALL"
DEFAULT_MART_COUNT = 5

#: Every fault and control switch (the launcher prints the ones that are set).
ALL_SWITCHES = (
    ENV_FAULT_KEEP_LISTENERS, ENV_FAULT_RAISE, ENV_FAULT_MANUAL, ENV_FAULT_HANG, ENV_FAULT_NO_REBIND,
    ENV_FAULT_SKIP_RESTORE, ENV_CONTROL_TAP, ENV_FAULT_NO_CROP, ENV_FAULT_UNGATED_A, ENV_FAULT_BLIND_COUNT,
)

DEFAULT_FRAMES = 3000

#: The instrument's verdict file, in the run directory. The launcher grades a run from THIS file, not
#: from printed lines (any code in the process can print a line that looks like a verdict).
VERDICT_FILE_NAME = "purity.json"


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip() == "1"


@dataclass(frozen=True)
class RunOptions:
    """Everything the mode needs to know about this run, frozen at mode start."""

    frames: int
    run_dir: Path | None
    wall_deadline: float | None
    fault_keep_listeners: bool
    fault_raise: bool
    fault_manual: bool
    fault_hang: bool
    fault_no_rebind: bool
    fault_skip_restore: bool
    control_tap: bool
    brain: str = DEFAULT_BRAIN
    watch_every: int = DEFAULT_WATCH_EVERY
    fault_no_crop: bool = False

    @classmethod
    def from_env(cls) -> "RunOptions":
        raw_frames = os.environ.get(ENV_FRAMES, "").strip()
        frames = int(raw_frames) if raw_frames else DEFAULT_FRAMES
        if frames <= 0:
            raise ValueError(f"{ENV_FRAMES} must be a positive frame count, got {frames}")
        raw_dir = os.environ.get(ENV_RUN_DIR, "").strip()
        raw_deadline = os.environ.get(ENV_WALL_DEADLINE, "").strip()
        brain = os.environ.get(ENV_BRAIN, "").strip() or DEFAULT_BRAIN
        if brain not in BRAINS:
            raise ValueError(f"{ENV_BRAIN} must be one of {BRAINS}, got {brain!r}")
        raw_every = os.environ.get(ENV_WATCH_EVERY, "").strip()
        watch_every = int(raw_every) if raw_every else DEFAULT_WATCH_EVERY
        if watch_every <= 0:
            raise ValueError(f"{ENV_WATCH_EVERY} must be a positive frame count, got {watch_every}")
        return cls(
            frames=frames,
            run_dir=Path(raw_dir) if raw_dir else None,
            wall_deadline=float(raw_deadline) if raw_deadline else None,
            fault_keep_listeners=_flag(ENV_FAULT_KEEP_LISTENERS),
            fault_raise=_flag(ENV_FAULT_RAISE),
            fault_manual=_flag(ENV_FAULT_MANUAL),
            fault_hang=_flag(ENV_FAULT_HANG),
            fault_no_rebind=_flag(ENV_FAULT_NO_REBIND),
            fault_skip_restore=_flag(ENV_FAULT_SKIP_RESTORE),
            control_tap=_flag(ENV_CONTROL_TAP),
            brain=brain,
            watch_every=watch_every,
            fault_no_crop=_flag(ENV_FAULT_NO_CROP),
        )

    def describe(self) -> str:
        switches = [
            name
            for name, on in (
                ("FAULT_KEEP_LISTENERS", self.fault_keep_listeners),
                ("FAULT_RAISE", self.fault_raise),
                ("FAULT_MANUAL", self.fault_manual),
                ("FAULT_HANG", self.fault_hang),
                ("FAULT_NO_REBIND", self.fault_no_rebind),
                ("FAULT_SKIP_RESTORE", self.fault_skip_restore),
                ("CONTROL_TAP", self.control_tap),
                ("FAULT_NO_CROP", self.fault_no_crop),
            )
            if on
        ]
        deadline = "none" if self.wall_deadline is None else f"{self.wall_deadline:.1f}"
        return (
            f"frames={self.frames} brain={self.brain} watch_every={self.watch_every} "
            f"switches={','.join(switches) or 'none'} wall_deadline={deadline} run_dir={self.run_dir}"
        )


@dataclass(frozen=True)
class HandsOptions:
    """BUILD STEP 2: what a hands brain needs that step 0's `BrainSettings` does not carry (see ENV_SEED for
    why the brain reads it itself). `seed` None = not given (the brain draws one from the clock and logs it)."""

    brain: str
    run_dir: Path | None
    seed: int | None
    personality: str | None
    mart_item: str
    mart_count: int
    clock: tuple[int, int] | None
    fault_ungated_a: bool
    fault_blind_count: bool

    @classmethod
    def from_env(cls) -> "HandsOptions":
        brain = os.environ.get(ENV_BRAIN, "").strip() or DEFAULT_BRAIN
        raw_dir = os.environ.get(ENV_RUN_DIR, "").strip()
        raw_seed = os.environ.get(ENV_SEED, "").strip()
        raw_count = os.environ.get(ENV_MART_COUNT, "").strip()
        count = int(raw_count) if raw_count else DEFAULT_MART_COUNT
        if not 1 <= count <= 99:
            raise ValueError(f"{ENV_MART_COUNT} must be 1..99, got {count}")
        raw_clock = os.environ.get(ENV_CLOCK, "").strip()
        clock = None
        if raw_clock:
            hours, minutes = (int(part) for part in raw_clock.split(":", 1))
            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError(f"{ENV_CLOCK} must be HH:MM, got {raw_clock!r}")
            clock = (hours, minutes)
        return cls(
            brain=brain,
            run_dir=Path(raw_dir) if raw_dir else None,
            seed=int(raw_seed) if raw_seed else None,
            personality=os.environ.get(ENV_PERSONALITY, "").strip() or None,
            mart_item=os.environ.get(ENV_MART_ITEM, "").strip() or DEFAULT_MART_ITEM,
            mart_count=count,
            clock=clock,
            fault_ungated_a=_flag(ENV_FAULT_UNGATED_A),
            fault_blind_count=_flag(ENV_FAULT_BLIND_COUNT),
        )
