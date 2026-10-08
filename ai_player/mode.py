"""The AI player's BRAIN: what it does, one frame at a time. Framework-free by construction.

WHY THIS FILE KNOWS NOTHING ABOUT THE FRAMEWORK (RULING 37 Q1, and the adversarial review's finding
10 on step 0): the AI is built to become a standalone program that loads the ROM itself. So the brain
sees the game ONLY through the two abstract interfaces below, `Controls` (buttons and time) and
`Eyes` (what it can see), and it ends ONLY by returning its give-up reason. Everything that ties it
to the framework (starting a session, the guard listener, parking, listener isolation, the purity
audit, exit codes) lives in `ai_player/host/`; `ai_player/host/session.py` builds the real
controller and drives `Brain.play` one frame per `yield`. The purity gate enforces the split: this
file may not import `ai_player.host` (rule c), and it has no door into the framework at all (rule a).

BUILD STEP 0 (design draft §6, "purity scaffolding"). The brain is a PLACEHOLDER that presses
nothing, lets `frames` frames pass, and gives up with reason `step0-placeholder`. Later steps replace
`Brain.play` with the real brain (eyes, world model, navigator, battle decider, menus, goals,
personality, coach). The contract stays: it yields once per frame, every press goes through
`controls`, and it ends by RETURNING a reason (a return without one is a programming error, exit 5).

The fault and control switches are read by the host from the environment (`ai_player/options.py`)
and handed in as `BrainSettings`, so the fault arms exercise this very loop. None is set on the happy
path.

BUILD STEP 1 adds the EYES (`Eyes.look()` returns an immutable `Observation`, `ai_player/eyes/`) and a
second brain, the WATCHER (`AI_PLAYER_BRAIN=watcher`): every `watch_every` frames it looks, writes the
Observation to the action log (`ai_player/memory_log.py`) and prints the scorer-compatible lines for what
changed, and it presses NOTHING. It is how the eyes are proven against ground truth live, under the
same purity audit as every run, and it is the recorder later brains build on.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Protocol

from ai_player.brain.explore import explore_intent, goto_intent, weights_for
from ai_player.brain.navigator import Navigator
from ai_player.eyes.observation import Observation
from ai_player.hands.menus import mart_buy, nurse_heal
from ai_player.hands.pad import Faults, Hands
from ai_player.memory_log import ActionLog, ScorerLines
from ai_player.options import HANDS_BRAINS, INTENT_MARGIN, WORLD_BRAINS, HandsOptions
from ai_player.personality import pick_personality
from ai_player.runlog import RecordFile
from ai_player.skills.clock import set_wall_clock
from ai_player.skills.intro import play_intro
from ai_player.skills.roam_train import roam_train
from ai_player.world.memory import WorldMemory, read_world

__all__ = [
    "CONTROL_TAP_EVERY_STEPS",
    "FAULT_HANG_AT_STEP",
    "FAULT_HANG_MAX_SECONDS",
    "FAULT_RAISE_AT_STEP",
    "PLACEHOLDER_REASON",
    "WATCHER_REASON",
    "WORLD_FILE_NAME",
    "Brain",
    "BrainSettings",
    "Controls",
    "Eyes",
    "HandsBrain",
    "WatcherBrain",
]

#: FAULT `AI_PLAYER_FAULT_RAISE`: the brain raises on this step.
FAULT_RAISE_AT_STEP = 30
#: FAULT `AI_PLAYER_FAULT_HANG`: the brain blocks on this step, for at most this many seconds (a
#: bound, so even a launcher that failed to kill it could not leave it running forever).
FAULT_HANG_AT_STEP = 30
FAULT_HANG_MAX_SECONDS = 300
#: CONTROL `AI_PLAYER_CONTROL_TAP`: the placeholder taps B once every this many steps.
CONTROL_TAP_EVERY_STEPS = 60
#: The step-0 placeholder's give-up reason.
PLACEHOLDER_REASON = "step0-placeholder"
#: The watcher's give-up reason, after it has watched `frames` frames.
WATCHER_REASON = "watcher-done"
#: BUILD STEP 3: the world memory's snapshots, one JSON line each, in the run directory.
WORLD_FILE_NAME = "world.jsonl"


class Controls(Protocol):
    """The brain's hands: buttons and time. Each action is a generator that yields once per frame."""

    def wait(self, frames: int) -> Generator[None, None, None]:
        """Let `frames` frames pass without touching any button."""

    def tap(self, button: str) -> Generator[None, None, None]:
        """Press `button` for one frame, then leave it released for one frame."""

    def hold(self, button: str, frames: int) -> Generator[None, None, None]:
        """Hold `button` for `frames` frames, and always release it."""


class Eyes(Protocol):
    """The brain's view of the game (build step 1). `ai_player/host/eyes.py` implements it with memory
    reads; a standalone build implements it some other way."""

    def look(self) -> Observation:
        """Everything on screen and in the menus, at the current frame, as an immutable snapshot. Never
        raises for a part it cannot read: that part is None and `Observation.problems` says why."""


@dataclass(frozen=True)
class BrainSettings:
    """What the brain is told about this run."""

    frames: int
    fault_raise: bool = False
    fault_hang: bool = False
    control_tap: bool = False
    watch_every: int = 60


class Brain:
    """STEP 0 PLACEHOLDER. Presses nothing (except under the CONTROL switch); waits; gives up.

    BUILD STEP 2: also the door to the HANDS brains. The session builds a `Brain` for every brain but the
    watcher, and the host is finished (no change to it in step 2), so the choice is made HERE: when the run
    asks for a hands brain (`AI_PLAYER_BRAIN` in `options.HANDS_BRAINS`, read through `HandsOptions`, the
    same environment the session read), `play` hands the run to a `HandsBrain`. For `placeholder` nothing
    changes: `HandsOptions.from_env` is read and ignored."""

    def __init__(self, settings: BrainSettings, say: Callable[[str], None]) -> None:
        self.settings = settings
        self._say = say
        options = HandsOptions.from_env()
        self._hands = HandsBrain(settings, say, options) if options.brain in HANDS_BRAINS + WORLD_BRAINS else None

    def play(self, controls: Controls, eyes: Eyes | None) -> Generator[None, None, str]:
        """One `yield` per frame. Returns the give-up reason."""
        if self._hands is not None:
            return (yield from self._hands.play(controls, eyes))
        settings = self.settings
        step = 0
        while step < settings.frames:
            if settings.fault_raise and step >= FAULT_RAISE_AT_STEP:
                raise RuntimeError("AI_PLAYER_FAULT_RAISE: injected brain fault")
            if settings.fault_hang and step >= FAULT_HANG_AT_STEP:
                self._hang()
            if settings.control_tap and step % CONTROL_TAP_EVERY_STEPS == 0:
                yield from controls.tap("B")
                step += 2
                continue
            yield from controls.wait(1)
            step += 1
        return PLACEHOLDER_REASON

    def _hang(self) -> None:
        """FAULT `AI_PLAYER_FAULT_HANG` only: block the main thread, as a stuck brain would. Nothing in
        this process can end the run now; only the launcher's hard wall clock can. Bounded anyway."""
        self._say(f"[AI-LIFECYCLE] FAULT_HANG: the brain blocks the main thread (at most {FAULT_HANG_MAX_SECONDS}s)")
        for _ in range(FAULT_HANG_MAX_SECONDS):
            time.sleep(1)
        raise RuntimeError("AI_PLAYER_FAULT_HANG: nobody killed the hung brain within its bound")


class WatcherBrain:
    """BUILD STEP 1: watches and presses nothing. Every `watch_every` frames: look, print the scorer
    lines for what changed (`[AI-STARTER]`, `[MAP]`, `[DEX]`, `[TRAINER] end`, `[CATCH] end`, and the
    `[hb]` heartbeat every 3600 frames), print a one-line digest (`[AI-EYES]`), and append the whole
    Observation to the action log. After `frames` frames it prints the last look's heartbeat (`end=1`)
    and how long its looks took (`[AI-EYES] cost ...`), and gives up with `watcher-done`. Its first look
    is at its first step, so the run's starting state is always recorded."""

    def __init__(self, settings: BrainSettings, say: Callable[[str], None], actions: ActionLog) -> None:
        if settings.watch_every <= 0:
            raise ValueError(f"watch_every must be positive, got {settings.watch_every}")
        self.settings = settings
        self._say = say
        self._actions = actions
        self.scorer = ScorerLines()
        self.costs: list[float] = []

    def play(self, controls: Controls, eyes: Eyes | None) -> Generator[None, None, str]:
        if eyes is None:
            raise RuntimeError("the watcher brain needs eyes")
        settings = self.settings
        reason = f"watcher: observe every {settings.watch_every} frames, press nothing"
        step = 0
        last: Observation | None = None
        while step < settings.frames:
            if step % settings.watch_every == 0:
                last = eyes.look()
                for line in self.scorer.update(last):
                    self._say(line)
                self._say(f"[AI-EYES] {last.digest()}")
                for problem in last.problems:
                    self._say(f"[AI-EYES] problem f{last.frame}: {problem}")
                self._actions.record(last, decision="observe", action="none", reason=reason, full=True)
                self.costs.append(last.cost_ms)
            yield from controls.wait(1)
            step += 1
        for line in self.scorer.final(last):
            self._say(line)
        self._say(self.cost_line())
        return WATCHER_REASON

    def cost_line(self) -> str:
        costs = sorted(self.costs)
        if not costs:
            return "[AI-EYES] cost: no looks"
        mean = sum(costs) / len(costs)
        median = costs[len(costs) // 2]
        return (f"[AI-EYES] cost over {len(costs)} looks: mean={mean:.2f}ms median={median:.2f}ms "
                f"min={costs[0]:.2f}ms max={costs[-1]:.2f}ms records={self._actions.records}")


class HandsBrain:
    """BUILD STEP 2: plays ONE skill with the AI's own hands (`ai_player/hands/`, `ai_player/skills/`) and gives
    up with the skill's outcome as its reason: `intro` (fresh boot to the truck), `nurse` (heal at the nurse in
    front of the player), `mart` (buy `HandsOptions.mart_count` of `mart_item` from the clerk in front of the
    player), `clock` (set the wall clock in front of the player).

    THE SEED: one integer per run (`AI_PLAYER_SEED`, or drawn from the clock and logged), split into two
    streams: CHOICES (personality, gender, name) and PACING (the pad's jitter), so that a change of pacing never
    changes a choice. BOUNDED: the skill gets at most `settings.frames` frames; past that it is stopped and the
    reason says so. THE LOG: the first and the last look go into the action log whole, every press and every
    page read in between (`hands/pad.py`), and `[AI-HANDS]` lines into the run's log.

    BUILD STEP 3 adds the WORLD brains (`options.WORLD_BRAINS`): `explore` (the navigator explores with the
    personality's taste until `AI_PLAYER_GOAL_MAP`, `brain/explore.py`), `roam` (train by roaming through grass,
    `skills/roam_train.py`), `goto` (errands to tiles of the current map, `AI_PLAYER_GOTO`). They keep a WORLD
    MEMORY (`world/memory.py`), told every look the hands take, started empty or from a previous run's
    `world.jsonl` (`AI_PLAYER_WORLD`), and written to `<run_dir>/world.jsonl` (one snapshot line at every map change
    and at the end); `[AI-WORLD]` lines go into the run's log. The navigator's path noise and detours come from the
    CHOICES stream."""

    def __init__(self, settings: BrainSettings, say: Callable[[str], None], options: HandsOptions) -> None:
        self.settings = settings
        self.options = options
        self._say = say
        self.seed = options.seed if options.seed is not None else time.time_ns() % 1_000_000_007
        self.actions = ActionLog(RecordFile(options.run_dir))
        #: BUILD STEP 3: the world brains' memory, its snapshots (`<run_dir>/world.jsonl`) and its navigator.
        self.world: WorldMemory | None = None
        self.navigator: Navigator | None = None
        self._world_file = RecordFile(options.run_dir, WORLD_FILE_NAME)

    def play(self, controls: Controls, eyes: Eyes | None) -> Generator[None, None, str]:
        if eyes is None:
            raise RuntimeError("the hands brain needs eyes")
        options = self.options
        choices = random.Random(f"{self.seed}:choices")
        pacing = random.Random(f"{self.seed}:pacing")
        faults = Faults(ungated_a=options.fault_ungated_a, blind_count=options.fault_blind_count)
        hands = Hands(eyes, controls, pacing, choices, self.actions, self._say, faults)
        personality = pick_personality(choices, self.seed, options.personality)
        self._say(f"[AI-HANDS] brain={options.brain} seed={self.seed} ({'given' if options.seed is not None else 'from the clock'}) "
                  f"personality={personality.name} ({personality.chosen_by}) faults=ungated_a:{faults.ungated_a},"
                  f"blind_count:{faults.blind_count} frames={self.settings.frames}")
        if options.brain in WORLD_BRAINS:
            self._start_world(hands, choices, personality.name)
        first = hands.look()
        self.actions.record(first, decision="start", action=options.brain, reason="the first look", full=True,
                            extra={"seed": self.seed, "personality": personality.name})
        outcome = yield from self._bounded(self._skill(hands, personality), hands)
        hands.pad.finish()
        last = hands.look()
        self.actions.record(last, decision="end", action=options.brain, reason=outcome, full=True)
        if self.world is not None:
            self._save_world("the end of the run")
            self._say(f"[AI-WORLD] memory at the end: {self._memory_line()}")
            self._say(f"[AI-WORLD] navigator: {self.navigator.summary()}")
        gates: dict[str, int] = {}
        for press in hands.pad.history:
            key = f"{press['button']}:{press['gate'].split(':', 1)[0].split(' (', 1)[0][:40]}"
            gates[key] = gates.get(key, 0) + 1
        self._say(f"[AI-HANDS] outcome={outcome!r} presses={hands.pad.presses} frames={hands.pad.frames} "
                  f"looks={hands.looks} records={self.actions.records}")
        self._say(f"[AI-HANDS] presses by gate: {dict(sorted(gates.items()))}")
        return f"{options.brain}: {outcome}"

    def _skill(self, hands: Hands, personality) -> Generator[None, None, str]:
        options = self.options
        if options.brain == "intro":
            return (yield from play_intro(hands, personality))
        if options.brain == "nurse":
            return (yield from nurse_heal(hands))
        if options.brain == "mart":
            return (yield from mart_buy(hands, options.mart_item, options.mart_count))
        if options.brain == "clock":
            hours, minutes = options.clock if options.clock is not None else (None, None)
            return (yield from set_wall_clock(hands, hours, minutes))
        budget = options.intent_frames or max(600, self.settings.frames - INTENT_MARGIN)
        if options.brain == "explore":
            intent = explore_intent(options.goal_map, personality.name, budget)
            return (yield from self.navigator.run(intent, f"explore{' to ' + options.goal_map if options.goal_map else ''}"))
        if options.brain == "roam":
            return (yield from roam_train(hands, self.navigator, options.roam_steps))
        if options.brain == "goto":
            return (yield from self.navigator.run(goto_intent(list(options.goto), budget), "errands on this map"))
        raise ValueError(f"no hands skill named {options.brain!r}")

    # ------------------------------------------------------------------ build step 3: the world
    def _start_world(self, hands: Hands, choices: random.Random, personality: str) -> None:
        """The memory (empty, or a previous run's, `AI_PLAYER_WORLD`), told every look the hands take, and the
        navigator over it (the CHOICES stream: its path noise and detours never shift with the pacing)."""
        options = self.options
        world = read_world(options.world_in) if options.world_in is not None else None
        source = f"the last snapshot of {options.world_in}" if world is not None else "nothing (a new memory)"
        self.world = world if world is not None else WorldMemory()
        hands.watchers.append(self.world.observe)
        weights = weights_for(personality)
        self.navigator = Navigator(hands, self.world, choices, weights.grass_cost, personality,
                                   on_map_change=lambda: self._save_world("a map change"))
        self._say(f"[AI-WORLD] memory from {source}: {self._memory_line()}; goal {options.goal_map or '-'}; personality "
                  f"{personality} (weights {weights})")

    def _memory_line(self) -> str:
        world = self.world
        names = world.names()
        maps = ", ".join(f"{names[key]} {len(memory.tiles)} tiles {len(memory.bumped)} bumped" for key, memory in world.maps.items())
        return (f"{len(world.maps)} maps ({maps or 'none'}), {world.tiles_learned} tiles learned, {len(world.warps)} warp links, "
                f"{len(world.connections)} connections, {len(world.transitions)} map changes")

    def _save_world(self, why: str) -> None:
        self._world_file.append(self.world.snapshot())
        self.actions.record(None, decision="world", action="snapshot", reason=why, frame=None,
                            extra={"maps": len(self.world.maps), "tiles": self.world.tiles_learned})

    def _bounded(self, skill: Generator[None, None, str], hands: Hands) -> Generator[None, None, str]:
        """Drive `skill` one frame per `yield`, for at most `settings.frames` frames."""
        frames = 0
        try:
            while True:
                if frames >= self.settings.frames:
                    hands.tell(f"the skill did not finish within {frames} frames: stopped")
                    return f"stopped: not finished within {frames} frames"
                try:
                    next(skill)
                except StopIteration as done:
                    return str(done.value)
                yield
                frames += 1
        finally:
            skill.close()
