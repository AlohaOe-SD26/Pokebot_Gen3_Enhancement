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

BUILD STEP 5 adds the PLAY brain (`AI_PLAYER_BRAIN=play`, `HandsBrain._play`): the AI plays the STORY itself toward
`AI_PLAYER_TARGET` (a milestone of `knowledge/milestones.json`), one goal at a time from the goal manager
(`brain/goals.py`), each with a logged reason, by the personality's weights (`personality.py`), and ends with "done: <target>
reached" or a reason (the frame budget, `STORY_PATIENCE` frames without a milestone, `MAX_LOSSES` battles lost: every
battle the navigator's battler played, inside a goal or in a scene, `_count_losses`).
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Protocol

from ai_player.brain.battle import BattleFaults, BattleMind, needs_rest
from ai_player.brain.explore import explore_intent, goto_intent, weights_for
from ai_player.brain.goals import (
    CURIOSITY_KINDS, Goal, GoalManager, GoalRunner, battles_lost, goal_yield, party_share, yield_snapshot,
)
from ai_player.brain.navigator import Navigator, nav_free
from ai_player.eyes.observation import Observation
from ai_player.hands.dialogue import advance, busy_reason, player_free, talk
from ai_player.hands.waiting import BattleClock, PushWatch, WaitWatch
from ai_player.hands.menus import local_clock, mart_buy, nurse_heal, set_clock
from ai_player.hands.pad import Faults, Hands
from ai_player.knowledge.story import load_story
from ai_player.memory_log import ActionLog, ScorerLines
from ai_player.options import HANDS_BRAINS, INTENT_MARGIN, WORLD_BRAINS, HandsOptions
from ai_player.personality import PersonalityState, choose_favourite, choose_starter, pick_personality
from ai_player.runlog import RecordFile
from ai_player.skills.battle import play_battle
from ai_player.skills.clock import set_wall_clock
from ai_player.skills.flee import in_battle
from ai_player.skills.intro import play_intro
from ai_player.skills.roam_train import roam_train
from ai_player.skills.story import answer_question, choose_starter as choose_starter_in_bag, leave_shop, play_out
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
#: BUILD STEP 4: the battle brain's roaming (its training steps are a bound: it ends when enough battles have ended), and
#: the frames it gives a walk up to a person it challenges.
ROAM_FOR_BATTLES = 3000
CHALLENGE_WALK_BUDGET = 6000
#: BUILD STEP 5: the play brain gives up when no milestone was reached for this many frames (33 minutes of play: the
#: longest stretch of chapter 1, the asking, training, healing and walk to the rival, took up to ~75,000 frames in the
#: development sweeps of 2026-10-14, `gates/rate_step5.py`), or after this many battles lost.
STORY_PATIENCE = 120_000
MAX_LOSSES = 3
#: BUILD STEP 5.1 (the step-5 adversarial review's finding 2: "chapter 4 will stop as stuck while it is still training"):
#: `STORY_PATIENCE` counts from the last REAL PROGRESS, not only from the last milestone: battles WON while training, a
#: level gained, a heal, a map never seen before, a catch, an item (picked up or bought). A heal counts at most this many
#: times a milestone (heal, get hurt, heal is no progress), so goals that keep FAILING are still stopped by the patience.
HEAL_RESETS_MAX = 3
#: BUILD STEP 5.1 (the step-5 verifier's FAILURE (b): a goal chosen on the frame a scene's map change landed, the scene's
#: text then waited for A while `talk` waited 1,200 frames): after a map change the screen must stay free this many frames
#: before a goal is chosen (a person takes in a new place; a scene that begins on arrival begins within them: PROF.
#: BIRCH's lab scene began within the 25 frames of thinking that followed the map change at f40017 in arm CH1M).
SETTLE_FREE = 30
#: BUILD STEP 5.1 (the step-5 verifier: "every `while True` ... has a frame/attempt bound"): passes of the play loop in a row
#: that let no frame pass before the loop gives up (each pass decides, plays a screen or settles: every one lets frames
#: pass, so this many in a row is a loop that does nothing), and the loop's passes at most (a pass takes at least one
#: decision's thinking pause, 14 frames: a run's frame budget bounds it long before this).
STILL_PASSES_MAX = 50
PLAY_PASSES_MAX = 100_000
#: (the step-5.1 verifier's second round) what played between two goals, as the goal manager's balance counts it: the story's
BETWEEN_GOALS = Goal("scene", "what played between two goals (a scene, the settling)")


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
        #: BUILD STEP 5: the play brain's report (milestones reached, goals, battles lost), for its end line and the harness
        self.play_report: dict | None = None

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
        if options.brain == "battle":
            return (yield from self._battles(hands, personality.name))
        if options.brain == "play":
            return (yield from self._play(hands, personality))
        raise ValueError(f"no hands skill named {options.brain!r}")

    # ------------------------------------------------------------------ build step 5: the story
    def _play(self, hands: Hands, personality) -> Generator[None, None, str]:
        """BUILD STEP 5, the PLAY brain: the AI plays the STORY itself (design draft §2.3 "goal manager", §6; USER RULING 37:
        badge 1 in 4 chapters, human pacing, never idle). At every decision the goal manager (`brain/goals.py`) reads where
        the story is from the eyes' milestone marks (`knowledge/story.py`) and chooses ONE goal with a logged reason: the
        current milestone's next step or a human errand (heal, shop, train, an item, catch, a chat), by the personality's
        weights (`personality.py` ERRANDS, with its step-based DRIFT and a FAVOURITE species); the goal is played by the AI's
        own skills (`brain/goals.py` GoalRunner: the navigator, roaming, `skills/story.py`). Scenes and battles met on the
        way are played through the navigator's `handle` with the play brain's own ANSWERS to a scene's yes/no
        (`skills/story.py` answer_question), its MENUS (PROF. BIRCH's bag, the wall clock) and the battle decider. The
        seeded streams are its own (`<seed>:story`, `<seed>:goals`, `<seed>:drift`, `<seed>:battle`), so no earlier brain's
        draws move. Ends "done: <milestone> ..." when the marks prove `AI_PLAYER_TARGET`, or with a reason (the frame budget,
        no milestone for `STORY_PATIENCE` frames, `MAX_LOSSES` battles lost)."""
        options, nav, world = self.options, self.navigator, self.world
        seed = self.seed
        story_rng = random.Random(f"{seed}:story")
        state = PersonalityState(personality.name, random.Random(f"{seed}:drift"), self._say)
        state.favourite = choose_favourite(story_rng)
        starter, starter_why = choose_starter(story_rng, personality.name, options.starter)
        mind = BattleMind(personality.name, random.Random(f"{seed}:battle"), "travel", BattleFaults())
        nav.battler = lambda: play_battle(hands, mind, f"battle ({mind.purpose})")
        nav.answer = answer_question
        nav.on_menu = lambda kind, why: self._story_menu(hands, kind, why, starter)
        look = hands.look()
        story = load_story(look.player.gender if look.player is not None else None)
        manager = GoalManager(story, state, random.Random(f"{seed}:goals"), hints_off=options.fault_no_hints,
                              train_off=options.fault_no_training, errands_off=options.fault_no_errands)
        manager.memory.landmarks = world.landmarks  # the doors it recognised live in the world memory: a later run has them
        # (build step 5.2, the verifier's round) so do the people who have spoken to it (never chatted with again); and the
        # navigator keeps a warp's ping-pong past its intent and marks what the reach shows no way to (the earlier brains
        # keep neither)
        manager.memory.spoke = world.spoke
        nav.ponged = {}
        nav.mark_cut = True
        manager.say = hands.tell  # (build step 5.1) a draw that chose no errand is told too
        hands.watchers.append(manager.notice)
        # (build step 5.1, the step-5 verifier's FAILURE) every stretch a screen WAITED FOR A PRESS with none, whatever the
        # reason it gave (`hands/waiting.py`): written to the action log, graded by `gates/live_step5.py` / `rate_step5.py`
        waits = WaitWatch(lambda: hands.pad.presses, hands.note, lambda: getattr(hands.pad, "doing", None))
        hands.watchers.append(waits)
        # (build step 5.2, the step-5.1 review's finding 5: about 7,500 frames of walking into someone at OLDALE passed the
        # stall property) every stretch of FREE time with presses that brought nothing new (no tile seen, no map stood on,
        # no battle), whatever the goal (`hands/waiting.py`): graded by `gates/live_step5.py` / `rate_step5.py` PUSH_MAX
        pushes = PushWatch(lambda: hands.pad.presses, hands.note,
                           lambda: (world.tiles_learned, sum(1 for memory in world.maps.values() if memory.visits)))
        hands.watchers.append(pushes)
        # (build step 5.2, step52dev2) the frames battles took: a look round's yield is counted over its OWN time
        battle_clock = BattleClock()
        hands.watchers.append(battle_clock)
        runner = GoalRunner(hands, nav, manager, mind, hands.tell)
        target = story.index(options.target)
        hands.tell(f"play brain: target {options.target} ({story.milestones[target].title}); personality {state.base} "
                   f"(errands {state.errands}); favourite Pokemon {state.favourite} (the shiny hunt is deferred); starter "
                   f"{starter} ({starter_why}); faults no_hints:{options.fault_no_hints},no_training:{options.fault_no_training},"
                   f"no_errands:{options.fault_no_errands}")
        self.play_report = report = {"milestones": [], "goals": [], "losses": 0, "target": options.target, "progress": [],
                                     "won_training": 0, "waits": None, "pushes": None,
                                     # (the step-5.1 verifier's second round) the goal manager's own count of its time
                                     # (`brain/goals.py` spent): a report only since build step 5.2
                                     "spent": manager.memory.spent}
        self._waits = waits
        self._pushes = pushes
        ended: list = [None]  # (the second round) the pad's frames when the last goal ended (what played after it: a scene)

        def visited(const: str) -> bool:
            return any(memory.const == const and memory.visits for memory in world.maps.values())

        def current(seen: Observation) -> int:
            return manager.milestone(seen, visited)[0] if seen.progress is not None and seen.progress.marks else last[0]

        last: list = [-1, None]  # the last milestone read from marks (index, milestone): kept while marks are not read
        changed_at = hands.pad.frames
        progress: dict = {}  # (build step 5.1) the last progress snapshot (`_progress`)
        still, last_frames = 0, -1
        for _ in range(PLAY_PASSES_MAX):
            # (build step 5.1) a bound on passes that let no frame pass: never a loop that does nothing
            still = still + 1 if hands.pad.frames == last_frames else 0
            last_frames = hands.pad.frames
            if still > STILL_PASSES_MAX:
                return self._play_end(hands, story, manager, runner, report, "stuck",
                                      f"{still} passes of the play loop in a row let no frame pass")
            # the battles LOST since the last decision, wherever they were played (inside a goal: training, a walk, a talk;
            # or a scene on screen): until the step-5 verifier's round of 2026-10-14 only the second kind was counted, so a
            # run that whited out twice while training reported "battles lost 0" and MAX_LOSSES could not fire
            # (`gates/test_goals.py` PlayLoopTests drives this loop to its MAX_LOSSES end; mutant G46 removes this call)
            stop = self._count_losses(hands, nav, report)
            if stop is not None:
                return self._play_end(hands, story, manager, runner, report, "stuck", stop)
            look = hands.look()
            nav.take_changes()
            if look.progress is not None and look.progress.marks:
                index, milestone = manager.milestone(look, visited)
            elif last[0] < 0 and look.player is None:
                index, milestone = 0, story.milestones[0]  # the title screen: a New Game (nothing is saved yet)
            else:
                index, milestone = last
            if look.player is not None and look.player.gender is not None and look.player.gender != story.gender:
                story = load_story(look.player.gender)  # the player's own sprite: whose house is whose
                manager.story = story
            if index != last[0] and index >= 0:
                self._milestone_line(hands, look, story, last, index, milestone, report, visited)
                last[0], last[1], changed_at = index, milestone, hands.pad.frames
                progress["heals_counted"] = 0
                # (build step 5.2, the verifier's round) the story moved on: what it could not get to is worth a look again
                nav.story_moved()
            # (build step 5.1, the step-5 review's finding 2) REAL progress short of a milestone resets the patience too
            moved = self._progress(look, world, runner, report, progress)
            if moved:
                report["progress"].append({"frame": look.frame, "pad_frames": hands.pad.frames, "what": moved})
                hands.tell(f"[AI-GOALS] progress: {'; '.join(moved)}: the story's patience counts from here "
                           f"(it had waited {hands.pad.frames - changed_at} frames)")
                changed_at = hands.pad.frames
            if milestone is None or index > target:
                return self._play_end(hands, story, manager, runner, report, "done", f"{options.target} reached")
            if milestone.steps and milestone.steps[0].do == "intro" and (look.player is None
                                                                         or look.screen.game_state != "OVERWORLD"):
                if any(goal["kind"] == "intro" for goal in report["goals"]):
                    return self._play_end(hands, story, manager, runner, report, "stuck", "the New Game intro again")
                outcome = yield from play_intro(hands, personality)
                report["goals"].append({"kind": "intro", "outcome": outcome, "frame": look.frame})
                if not outcome.startswith("in the truck"):
                    return self._play_end(hands, story, manager, runner, report, "stuck", outcome)
                continue
            # (the step-5 verifier, 2026-10-14) checked on EVERY pass, not only when the player is free: a screen that never
            # frees would otherwise call `play_out` again and again until the launcher's frame budget ended the run
            # (`gates/test_goals.py` PlayLoopTests drives this loop on such a screen; mutant G47 brings the old rule back)
            if hands.pad.frames - changed_at > STORY_PATIENCE:
                return self._play_end(hands, story, manager, runner, report, "stuck",
                                      f"no progress for {hands.pad.frames - changed_at} frames (no milestone, battle won "
                                      f"training, level, new map, catch, item or heal; since {milestone.title})")
            if not nav_free(look):
                stop = yield from play_out(hands, nav, f"{milestone.title}: what is on screen")
                if stop is not None and "battle was lost" not in stop:  # a loss is counted at the top of the loop
                    hands.tell(f"what was on screen ended: {stop}")
                    if not nav_free(hands.look()):
                        yield from hands.pad.busy("waiting for the screen to settle after a stop")
                continue
            # (build step 5.1, the step-5 verifier's FAILURE (b)) SETTLE FIRST: right after a map change a scene may begin
            # (PROF. BIRCH's lab), so the screen must stay free `SETTLE_FREE` frames before a goal is chosen
            arrived = world.transitions[-1].frame if getattr(world, "transitions", None) else None
            if arrived is not None and 0 <= look.frame - arrived < SETTLE_FREE:
                yield from hands.pad.busy("taking in the new place: a scene may begin on arrival")
                continue
            state.step(nav.stats.steps)
            if ended[0] is not None and hands.pad.frames > ended[0]:
                # (the step-5.1 verifier's second round) what played BETWEEN two goals (a scene the loop played out, the
                # settling) was the story's time: a person who has just watched WALLY's tutorial has had plenty of story
                manager.spent(BETWEEN_GOALS, hands.pad.frames - ended[0])
                ended[0] = None
            goal = manager.next_goal(look, world, milestone, index)
            hands.tell(f"[AI-GOALS] goal {goal.kind}: {goal.reason} (milestone {milestone.id}, personality {state.active})")
            hands.note("goal", goal.kind, goal.reason, {"milestone": milestone.id, "active": state.active, "key": goal.key,
                                                        "map": goal.map, "steps": goal.steps})
            if goal.kind == "give_up":
                # (build step 5.2, the verifier's round) OUT OF IDEAS (`brain/goals.py` next_goal): the run ends here, not
                # after the story's patience of pressing for nothing
                return self._play_end(hands, story, manager, runner, report, "stuck", goal.reason)
            began = hands.pad.frames
            yield from hands.pad.idle(hands.pad.think_frames(), f"deciding: {goal.kind}: {goal.reason[:80]}")
            seen = hands.look()
            if not nav_free(seen):
                # (build step 5.1) the screen changed while it decided (a scene began): the goal waits, the scene first
                hands.tell(f"[AI-GOALS] goal {goal.kind} waits: the screen changed while it decided ({busy_reason(seen)}); "
                           f"what is on screen first")
                report["goals"].append({"kind": goal.kind, "key": goal.key, "ok": None, "frames": hands.pad.frames - began,
                                        "outcome": "dropped: a scene began while it decided", "milestone": milestone.id})
                # (build step 5.1, the verifier's second round: the live CH2T arm's 'chat' dropped at f227827 was graded as
                # the 11,019 frames of WALLY's scene that followed) a goal's END is recorded: what came after it was no goal
                manager.spent(goal, hands.pad.frames - began)
                hands.note("goal_end", goal.kind, "dropped: a scene began while it decided",
                           {"ok": None, "frames": hands.pad.frames - began, "key": goal.key, "story_moved": False,
                            "yield": {"productive": False, "dropped": True}})
                ended[0] = hands.pad.frames
                continue
            battles = len(nav.battle_log)
            # (build step 5.2, the step-5.1 review's finding 1: "it loafs") what the goal BRINGS is counted: before it ...
            before = yield_snapshot(seen, world, runner, battle_clock.battle_frames)
            ok, outcome = yield from runner.pursue(goal, milestone, index, current)
            after = hands.look()
            # ... and after it: a CURIOSITY goal is done only when it brought something (`brain/goals.py` goal_yield): 5.1
            # called a look round whose budget ran out "done" whatever it saw
            made = goal_yield(goal, before, yield_snapshot(after, world, runner, battle_clock.battle_frames), outcome,
                              hands.pad.frames - began)
            made["frames"] = hands.pad.frames - began
            made["place"] = getattr(runner, "detour_place", None) if goal.kind == "detour" else None
            if goal.kind in CURIOSITY_KINDS and not made["productive"]:
                ok = False
            manager.outcome(goal, ok)
            if goal.kind == "train":
                report["won_training"] += sum(1 for _, _, result in nav.battle_log[battles:] if result in ("won", "caught"))
            report["goals"].append({"kind": goal.kind, "key": goal.key, "ok": ok, "frames": hands.pad.frames - began,
                                    "outcome": outcome[:200], "milestone": milestone.id})
            hands.tell(f"[AI-GOALS] goal {goal.kind} {'done' if ok else 'not done'}: {outcome[:300]}")
            # (build step 5.1, the verifier's second round) the goal's END, and its frames into the goal manager's count
            # (`brain/goals.py` spent; a report since build step 5.2): a curiosity goal in which the story moved on is the story's
            moved_story = current(after) != index
            manager.spent(goal, hands.pad.frames - began, moved_story)
            # (build step 5.2) the curiosity in a row, the boredom clock (only a PRODUCTIVE curiosity goal resets it), and
            # what an unproductive one marks (a map exhausted, a place blocked)
            manager.after_goal(goal, made, after.frame, milestone.id, moved_story)
            hands.note("goal_end", goal.kind, outcome[:200], {"ok": ok, "frames": hands.pad.frames - began, "key": goal.key,
                                                             "story_moved": moved_story, "yield": made})
            ended[0] = hands.pad.frames
        return self._play_end(hands, story, manager, runner, report, "stuck", f"{PLAY_PASSES_MAX} passes of the play loop")

    @staticmethod
    def _progress(look: Observation, world, runner, report: dict, seen: dict) -> list[str]:
        """(build step 5.1, the step-5 review's finding 2) What REAL PROGRESS a person would see since the last snapshot
        `seen` (updated here): battles WON while training (`report["won_training"]`), a level gained (by one Pokemon, by its
        PID, above its highest level seen: the verifier's second round; the party's levels added up rose back after WALLY's
        tutorial lent the party a Pokemon), a map never seen before (the world memory's maps), a catch (the POKéDEX's owned
        count), an item picked up or bought (the runner's records), a heal (at most `HEAL_RESETS_MAX` a milestone: heal, get
        hurt, heal again is no progress). The first call only takes the snapshot."""
        mons = [m for m in look.party or () if not m.is_egg] if look.party is not None else None
        before = seen.get("snapshot") or {}
        # (build step 5.1, the verifier's second round: the SUM of the party's levels fell from 15 to 10 when WALLY's
        # tutorial lent the player a Zigzagoon, and rose back "10 -> 15" after it: a false "level gained") a level is GAINED
        # by one Pokemon, by its IDENTITY (its PID, CLAUDE.md rule 3), above the highest level it was seen at; a Pokemon never
        # seen before only sets its own mark (a catch counts by the POKéDEX)
        peaks: dict = seen.setdefault("peaks", {})
        gained = 0
        for mon in mons or ():
            peak = peaks.get(mon.pid)
            if peak is not None and mon.level > peak:
                gained += mon.level - peak
            if peak is None or mon.level > peak:
                peaks[mon.pid] = mon.level
        seen["gained"] = seen.get("gained", 0) + gained
        now = {"won_training": report.get("won_training", 0),
               "levels": seen["gained"],
               "maps": len(getattr(world, "maps", {}) or {}),
               "owned": look.progress.dex_owned if look.progress is not None else before.get("owned"),
               "items": len(getattr(runner, "picked", ())) + sum(1 for s in getattr(runner, "shopping", ()) if "bought" in s),
               "heals": sum(1 for h in getattr(runner, "heals", ()) if h == "healed")}
        if "snapshot" not in seen:
            seen["snapshot"] = now
            seen.setdefault("heals_counted", 0)
            return []
        moved: list[str] = []
        names = {"won_training": "battles won while training", "levels": "a level gained", "maps": "a map never seen before",
                 "owned": "a catch (the POKéDEX's owned count)", "items": "an item picked up or bought", "heals": "a heal"}
        for key, name in names.items():
            if now[key] is None or before.get(key) is None or now[key] <= before[key]:
                continue
            if key == "heals":
                if seen.get("heals_counted", 0) >= HEAL_RESETS_MAX:
                    continue
                seen["heals_counted"] = seen.get("heals_counted", 0) + 1
            moved.append(f"{name} ({before[key]} -> {now[key]})")
        seen["snapshot"] = now
        return moved

    @staticmethod
    def _count_losses(hands: Hands, nav: Navigator, report: dict) -> str | None:
        """The play brain's count of battles LOST (`brain/goals.py` battles_lost over every battle the navigator's battler
        played, inside a goal or in a scene alike) into `report["losses"]`, each new one told; the end reason once
        `MAX_LOSSES` were lost, else None."""
        lost = battles_lost(nav.battle_log)
        while report["losses"] < lost:
            report["losses"] += 1
            hands.tell(f"a battle was LOST ({report['losses']} of at most {MAX_LOSSES}): the party whited out; it goes on "
                       f"from where the game put it")
        if report["losses"] >= MAX_LOSSES:
            return f"{report['losses']} battles lost (MAX_LOSSES {MAX_LOSSES})"
        return None

    def _story_menu(self, hands: Hands, kind: str, why: str, starter: str) -> Generator[None, None, bool]:
        """A menu a story scene raises (the navigator's `on_menu`): PROF. BIRCH's bag (the starter the personality drew) or
        the wall clock (the computer's time, as a person sets it, or `AI_PLAYER_CLOCK`)."""
        if kind == "choose_starter":
            return (yield from choose_starter_in_bag(hands, starter, f"{why}: PROF. BIRCH's bag: {starter}"))
        if kind == "clock":
            hours, minutes = self.options.clock if self.options.clock is not None else local_clock()
            return (yield from set_clock(hands, hours, minutes, f"{why}: the wall clock to {hours}:{minutes:02d}"))
        if kind in ("mart_buy", "mart_menu"):
            # (build step 5.1) a mart's list or menu left open (an item not on the list stops `mart_buy` there): left
            return (yield from leave_shop(hands, self.navigator, why)) == "left"
        return False

    def _milestone_line(self, hands: Hands, look: Observation, story, last: list, index: int, milestone, report,
                        visited: Callable[[str], bool] | None = None) -> None:
        marks = dict(look.progress.marks) if look.progress is not None else {}
        if last[1] is not None and index > last[0]:
            for passed in story.milestones[max(last[0], 0):index]:
                # (build step 5.1, the step-5 verifier: "MILESTONE ch1_intro done ... VAR_LITTLEROOT_INTRO_STATE=0 (>= 1)"
                # quoted a proof that did not hold) HOW it passed: its proofs hold, a WAYPOINT stood on, or OPTIONAL
                proven = passed.done(marks) is True
                if proven:
                    how = "done"
                elif passed.optional:
                    how = "passed as OPTIONAL (not required; its proofs do not hold)"
                elif passed.waypoint is not None and visited is not None and visited(passed.waypoint):
                    how = f"passed as a WAYPOINT (it stood on {passed.waypoint}; its save proofs do not hold yet)"
                else:
                    how = "passed (a later milestone's proofs hold)"
                report["milestones"].append({"id": passed.id, "frame": look.frame, "pad_frames": hands.pad.frames,
                                             "proofs": passed.proofs(marks), "how": "done" if proven else how.split(" (")[0]})
                hands.tell(f"[AI-GOALS] MILESTONE {passed.id} {how} at f{look.frame} ({passed.title}): {passed.proofs(marks)}")
        if milestone is not None:
            hands.tell(f"[AI-GOALS] the story is at {milestone.id} ({milestone.title}); proofs now: {milestone.proofs(marks)}")
            hands.note("milestone", milestone.id, milestone.title, {"index": index, "frame": look.frame})

    def _play_end(self, hands: Hands, story, manager, runner, report, kind: str, why: str) -> str:
        # the losses are the LOOP's count (`_count_losses`, at the top of every pass), never recounted here: every way out
        # of the loop leaves it after that pass's count, with no battle in between, so a recount could only HIDE a loop
        # that stopped counting (the step-5 verifier's round 2: with the loop's call removed, this recount made the
        # sweep's "the AI's battles lost == the game's" pass 40 of 40). A disagreement is told, not mended.
        logged = battles_lost(runner.nav.battle_log)
        if logged != report["losses"]:
            hands.tell(f"the loop counted {report['losses']} battles lost, but the battle log holds {logged}")
        waits = getattr(self, "_waits", None)
        if waits is not None:
            waits.finish()
            report["waits"] = waits.summary()
        pushes = getattr(self, "_pushes", None)
        if pushes is not None:
            # (build step 5.2) the longest free stretch of presses that brought nothing new
            pushes.wind_up()
            report["pushes"] = pushes.push_report()
        prep = {key: dict(value) for key, value in manager.memory.fight_prep.items()}
        hands.tell(f"[AI-GOALS] the end ({kind}: {why}); milestones {[m['id'] for m in report['milestones']]}; before the "
                   f"fights {prep}; roams {len(runner.roams)}, heals {runner.heals}, shopping {runner.shopping}, items "
                   f"{runner.picked}, battles lost {report['losses']}, personality {manager.state.history}, favourite "
                   f"{manager.state.favourite}; progress resets {len(report.get('progress') or [])}; waits on a press "
                   f"{report.get('waits')}; pressing with nothing new {report.get('pushes')}; curiosity that brought "
                   f"nothing {manager.memory.idle}")
        hands.note("end", kind, why, {"milestones": report["milestones"], "fight_prep": prep, "roams": runner.roams,
                                      "heals": runner.heals, "shopping": runner.shopping, "items": runner.picked,
                                      "losses": report["losses"], "drift": manager.state.history,
                                      "favourite": manager.state.favourite, "progress": report.get("progress"),
                                      "waits": report.get("waits"), "pushes": report.get("pushes"),
                                      "idle": dict(manager.memory.idle),
                                      "blocked": {m: {k: sorted(map(list, v)) for k, v in maps.items() if v}
                                                  for m, maps in manager.memory.blocked.items() if any(maps.values())},
                                      "exhausted": dict(manager.memory.exhausted), "spent": dict(manager.memory.spent),
                                      "seen_levels": dict(manager.memory.seen_levels),
                                      "no_balls": dict(manager.memory.no_balls), "home_heals": manager.memory.home_heals})
        return f"{kind}: {why}"

    # ------------------------------------------------------------------ build step 4: battles
    def _battles(self, hands: Hands, personality: str) -> Generator[None, None, str]:
        """BUILD STEP 4, the BATTLE brain: the AI's own decider (`brain/battle.py`) plays every battle through the
        navigator's battler (`skills/battle.py` play_battle): the battle on screen at the start; then the person at
        `AI_PLAYER_TALK_TO`, walked up to and talked to (a trainer, the rival); then wild battles met roaming the grass
        (`skills/roam_train.py`, which now FIGHTS through the same battler), until `AI_PLAYER_BATTLES` have ended. The
        decider's draws come from their own stream of the seed (`<seed>:battle`), so a battle never shifts a walk's
        choices. Returns "battles: N played: [outcomes]" or why it stopped."""
        options, nav = self.options, self.navigator
        faults = BattleFaults(ignore_types=options.fault_ignore_types, ignore_recoil=options.fault_ignore_recoil,
                              uncapped_recoil=options.fault_uncapped_recoil, forget_field=options.fault_forget_field,
                              ignore_refusal=options.fault_ignore_refusal, overkill=options.fault_overkill,
                              shift_fainted=options.fault_shift_fainted, forget_unusable=options.fault_forget_unusable,
                              no_catch_status=options.fault_no_catch_status, ignore_pp=options.fault_ignore_pp,
                              forget_shift=options.fault_forget_shift)
        mind = BattleMind(personality, random.Random(f"{self.seed}:battle"), options.purpose, faults)
        nav.battler = lambda: play_battle(hands, mind, f"battle ({options.purpose})")
        nav.battle_limit = None  # set for the roaming only: a battle met on the way to a challenge does not end the brain
        hands.tell(f"battle brain: {options.battles} battle(s), purpose {options.purpose}, personality {mind.personality} "
                   f"({mind.temper}); talk to {options.talk_to or 'nobody'}; faults ignore_types:{options.fault_ignore_types},"
                   f"ignore_recoil:{options.fault_ignore_recoil}"
                   + "".join(f",{name}:True" for name, on in (("uncapped_recoil", faults.uncapped_recoil),
                                                              ("forget_field", faults.forget_field),
                                                              ("ignore_refusal", faults.ignore_refusal),
                                                              ("overkill", faults.overkill),
                                                              ("shift_fainted", faults.shift_fainted),
                                                              ("forget_unusable", faults.forget_unusable),
                                                              ("no_catch_status", faults.no_catch_status),
                                                              ("ignore_pp", faults.ignore_pp),
                                                              ("forget_shift", faults.forget_shift)) if on))
        played = nav.battle_outcomes
        look = hands.look()
        if in_battle(look):
            stop = yield from nav.handle(look, "the battle on screen")
            if stop is not None and not stop.startswith("done:"):
                return f"battles: {len(played)} played {played}; {stop}"
        if options.talk_to is not None and len(played) < options.battles:
            stop = yield from self._challenge(hands, options.talk_to)
            if stop is not None and not stop.startswith("done:"):
                return f"battles: {len(played)} played {played}; {stop}"
        if len(played) < options.battles:
            rest = needs_rest(hands.look().party)
            if rest is not None:
                return f"battles: {len(played)} played {played}; rest: {rest}: it does not go training"
            nav.battle_limit = options.battles
            nav.battle_rest = lambda look: needs_rest(look.party)
            outcome = yield from roam_train(hands, nav, ROAM_FOR_BATTLES, "train: roam the grass, battling what comes")
            if "done:" not in outcome:
                return f"battles: {len(played)} played {played}; {outcome}"
        return f"battles: {len(played)} played: {played}"

    def _challenge(self, hands: Hands, tile: tuple[int, int]) -> Generator[None, None, str | None]:
        """Walk up to the person standing at `tile` (on the current map, seen on screen) and talk to them: a trainer or
        the rival, whose words lead to a battle that the navigator's battler then plays. None when the battle (if any)
        was played and the brain goes on; otherwise why it stopped."""
        nav = self.navigator
        look = hands.look()
        person = next((o for o in (look.view.objects if look.view else ()) if o.source == "object" and (o.x, o.y) == tile), None)
        if person is None or look.player is None or look.player.x is None:
            return f"stuck: nobody is seen at {tile}"
        here = (look.player.x, look.player.y)
        beside = sorted(((tile[0] + dx, tile[1] + dy) for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1))),
                        key=lambda xy: abs(xy[0] - here[0]) + abs(xy[1] - here[1]))
        reached = None
        for spot in beside:
            # (a wild battle met on the way is played by the navigator's battler and the walk goes on: no battle limit is
            # set while walking up to a challenge)
            if spot != here:
                yield from nav.go_to(spot, f"walk up to the person at {tile}", CHALLENGE_WALK_BUDGET)
            where = hands.look().player
            if where is not None and (where.x, where.y) == spot:
                reached = spot
                break
            if in_battle(hands.last):
                break  # a trainer saw the player first
        look = hands.look()
        if not in_battle(look):
            if reached is None:
                return f"stuck: no tile beside the person at {tile} could be reached"
            person = next((o for o in (look.view.objects if look.view else ()) if o.source == "object"
                           and o.local_id == person.local_id), person)
            if not (yield from talk(hands, person, f"challenge the person at {tile}")):
                return f"stuck: the person at {tile} did not answer"
            outcome = yield from advance(hands, lambda l: in_battle(l) or player_free(l), f"listen to the person at {tile}")
            look = hands.last
            if outcome.startswith("menu:"):
                return f"stuck: an unexpected {outcome[5:]} while the person at {tile} talked"
        if not in_battle(look):
            return f"stuck: talking to the person at {tile} led to no battle"
        return (yield from nav.handle(look, f"the battle with the person at {tile}"))

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
        """Drive `skill` one frame per `yield`, for at most `settings.frames` frames (build step 5.1: a `for` over the
        frames, so the bound is the loop itself)."""
        try:
            for frames in range(self.settings.frames):
                try:
                    next(skill)
                except StopIteration as done:
                    return str(done.value)
                yield
            hands.tell(f"the skill did not finish within {self.settings.frames} frames: stopped")
            return f"stopped: not finished within {self.settings.frames} frames"
        finally:
            skill.close()
