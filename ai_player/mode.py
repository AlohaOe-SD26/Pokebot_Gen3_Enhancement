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
from dataclasses import dataclass, replace
from typing import Protocol

from ai_player.brain.battle import BattleFaults, BattleMind, needs_rest
from ai_player.brain.saving import SavePolicy, own_cart
from ai_player.brain.explore import explore_intent, goto_intent, weights_for
from ai_player.brain.goals import (
    CURIOSITY_KINDS, Goal, GoalManager, GoalRunner, battles_lost, goal_yield, party_share, yield_snapshot,
)
from ai_player.brain.navigator import Navigator, nav_free
from ai_player.eyes.observation import Observation
from ai_player.game_memory import (
    MemoryFileError, MemoryWriter, MonRegistry, battle_part, build_payload, goals_part, party_of, personality_part,
    read_book, restore, restore_battle, restore_goals, restore_personality, where_of,
)
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
from ai_player.skills.saving import SAVE_CLOSE_BUDGET, SAVE_WRITE_BUDGET, continue_game, save_game
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
#: (R5, backlog item R5 "a FREE-SCREEN precondition", 2026-10-28) the rounds the settle before "done" takes at most
#: (`HandsBrain._settle_before_done`): each round plays out a screen that is not free and then takes the decision's pause
#: and one more look. The measured case took THREE (the R5 build's development check from the fixture probe's ch2_dad end
#: states, seeds 5301 and 5302): the first pause finds WALLY's tutorial beginning; the tutorial's own warp back to the gym
#: frees the player for one frame before the gym's return scene, which the second pause finds; the third finds the gym
#: free. Six leave room for a longer chain and still bound the settle (LESSONS PL-4). (R5's fix round) Every NEW run of the
#: R5 live A/B (held-out seeds 5351-5354) took the same three pauses (the adversarial review's settle_rounds.out), and
#: `test_r5_the_measured_ch2_dad_chain_takes_three_rounds` pins it: with 2 rounds (G354) that chain ends NOT free.
DONE_SETTLE_ROUNDS = 6
#: (R5's fix round, the review's finding R5-F1) the frames of the run's budget (`settings.frames`) the settle before "done"
#: always leaves: it hands on a frame only while more than this many are left, then stops and SAYS so, and the run ends
#: "done" (its proof holds). Without it a settle longer than what was left was cut by the brain's own bound (`_bounded`)
#: into "stopped: not finished within N frames" with no end record, no "end" note and no line saying the target was
#: reached, and `gates/live_step5.py`'s HONESTY check read that stop over a proof that holds as a lie. `_bounded` needs ONE
#: frame to see the run return (it resumes the skill once per frame); the second is slack.
DONE_BUDGET_MARGIN = 2
#: (the step-5.1 verifier's second round) what played between two goals, as the goal manager's balance counts it: the story's
BETWEEN_GOALS = Goal("scene", "what played between two goals (a scene, the settling)")
#: (R1, build spec 2026-10-29 D13) the frames the play loop waits, pressing nothing, on a save page it meets outside the save
#: skill (a guard against a skill bug: with the skill as built it should never fire): the write and the close together
SAVE_PAGE_WAIT = SAVE_WRITE_BUDGET + SAVE_CLOSE_BUDGET


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


class _RebasedEyes:
    """(R2, build spec 2026-10-29 D7) THE FRAME BASE of a continue run: every look's `frame` is the emulator's plus `base`
    (`MemoryBook.frame_base`: 1 + the largest frame stamp in the memory file), so every stamp the restored memory carries
    stays in the PAST after the cold boot (the emulator's counter starts at 0 again: a door found closed is retried only
    `CLOSED_RETRY_FRAMES` after its stamp, which a counter restarted at 0 would not reach for that long). The base is 0 in
    every run that is not a continue, and then the eyes are not wrapped at all (T6)."""

    def __init__(self, eyes: Eyes, base: int) -> None:
        self.inner = eyes
        self.base = base

    def look(self) -> Observation:
        seen = self.inner.look()
        return replace(seen, frame=seen.frame + self.base)


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
    CHOICES stream.

    R1 + R2 (build spec 2026-10-29): with a memory file (`AI_PLAYER_MEMORY`, D14) the play brain SAVES through the game's
    own dialog at USER RULING 51's moments (`brain/saving.py`, `skills/saving.py` save_game), keeps `memory.jsonl`
    (`game_memory.py`: a save line at the START of each write, `lost` lines, its `end` line), and with
    `AI_PLAYER_CONTINUE` CONTINUES the game from the title itself (`skills/saving.py` continue_game), restoring its memory
    AS OF the save the game loaded, never newer. A run without a memory file behaves exactly as before R1."""

    #: (R1 + R2) the memory file's state, at its pre-R1 values: a brain built without `__init__` (the play-loop tests) and a
    #: run without a memory file keep them (`_open_memory` sets them per run)
    _memory_path = None
    _saving = False
    _continuing = False
    _frame_base = 0
    _book = None
    _writer = None
    _policy = None
    _registry = None
    _continued = None
    _saves_made = 0
    _at_save_presses = None
    _continue_may_retry = False
    _kept = None
    _choices = None

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
        # (R1 + R2) the game's memory file, read FIRST: a newer one is refused before anything is pressed or written
        refused = self._open_memory()
        if self._frame_base:
            eyes = _RebasedEyes(eyes, self._frame_base)
        hands = Hands(eyes, controls, pacing, choices, self.actions, self._say, faults)
        personality = pick_personality(choices, self.seed, self._remembered_personality() or options.personality)
        self._say(f"[AI-HANDS] brain={options.brain} seed={self.seed} ({'given' if options.seed is not None else 'from the clock'}) "
                  f"personality={personality.name} ({personality.chosen_by}) faults=ungated_a:{faults.ungated_a},"
                  f"blind_count:{faults.blind_count} frames={self.settings.frames}")
        if self._memory_path is not None:
            self._say(f"[AI-HANDS] memory={self._memory_path} saving={self._saving} continue={self._continuing} "
                      f"frame_base={self._frame_base} cart={getattr(options, 'cart', None)} "
                      f"refused={refused or '-'}")
        self._choices = choices
        if options.brain in WORLD_BRAINS and not self._continuing:
            self._start_world(hands, choices, personality.name)
        first = hands.look()
        self.actions.record(first, decision="start", action=options.brain, reason="the first look", full=True,
                            extra={"seed": self.seed, "personality": personality.name})
        if refused is not None:
            outcome = refused
        else:
            outcome = yield from self._bounded(self._skill(hands, personality), hands)
        hands.pad.finish()
        last = hands.look()
        self.actions.record(last, decision="end", action=options.brain, reason=outcome, full=True)
        self._end_memory(hands, outcome, last)
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
            if self._continuing:
                return (yield from self._continue(hands, personality))
            return (yield from self._play(hands, personality))
        raise ValueError(f"no hands skill named {options.brain!r}")

    # ------------------------------------------------------------------ R1 + R2: the memory file, saving, continuing
    def _open_memory(self) -> str | None:
        """(R1 + R2, build spec section 3 (e)) The play brain's memory file (`HandsOptions.memory_file`), read once before
        anything is pressed. Sets whether this run SAVES (a memory file and not the no-save CONTROL, D14) and CONTINUES
        (D11), and the frame base of a continue (D7). Returns the run's end reason when the file refuses the run, else
        None:
          * a NEWER schema (D9): refused, the file left byte-identical (nothing of this run is ever written to it);
          * a file that cannot be read (no header, a broken middle line): refused;
          * a continue with no save line to continue;
          * a NEW game on a game that already has a memory file: refused (only a continue adds to a memory file; the
            launcher's `--fresh` and `--state` archive it first, D10)."""
        options = self.options
        path = getattr(options, "memory_file", None) if options.brain == "play" else None
        self._memory_path = path
        self._continuing = path is not None and bool(getattr(options, "continue_game", False))
        self._saving = path is not None and not getattr(options, "fault_no_save", False)
        if path is None or not (self._saving or self._continuing):
            return None
        try:
            self._book = read_book(path)
        except MemoryFileError as error:
            self._saving = self._continuing = False
            if error.kind == "newer":
                return f"stuck: the memory file was written by a newer program ({error})"
            return f"stuck: the memory file cannot be used ({error})"
        if self._continuing:
            if self._book is None or not self._book.saves():
                self._saving = self._continuing = False
                return f"stuck: there is no save in the memory file to continue ({path})"
            self._frame_base = self._book.frame_base()
        elif self._book is not None:
            self._saving = False
            return (f"stuck: this game already has a memory file ({path}): only a continue adds to it (the launcher's "
                    f"--fresh or --state archives it first)")
        return None

    def _remembered_personality(self) -> str | None:
        """(R2) A continue plays on with the personality its game began with (the memory file's header)."""
        if not self._continuing or self._book is None:
            return None
        return (self._book.header_line.get("identity") or {}).get("personality")

    def _session(self, how: str, cart: str | None, **more) -> dict:
        """(R2) This run's `session` line (`game_memory.py`): how it began, who started it, where its logs are, what the
        cart held (D17: `kept` when nobody said), its frame base."""
        options = self.options
        run_dir = getattr(options, "run_dir", None)
        return {"how": how, "host": getattr(options, "host", "launcher"), "run_dir": str(run_dir) if run_dir else None,
                "cart": cart or "kept", "frame_base": self._frame_base, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                **more}

    def _game_name(self) -> str:
        """(R2) The header's `game`: the profile the memory file belongs to and when the game began."""
        path = self._memory_path
        folder = path.parent.parent.name if path.parent.name == "ai_player" else path.parent.name
        return f"{folder}|{time.strftime('%Y-%m-%dT%H:%M:%S')}"

    def _continue(self, hands: Hands, personality) -> Generator[None, None, str]:
        """(R1 + R2, build spec section 3 (b), (c) and (f)) CONTINUE the game from power-on (`skills/saving.py`
        continue_game: never NEW GAME), then restore the memory AS OF the save the game loaded (`game_memory.py` restore),
        and play on. Right after the restore and BEFORE the first look of the continued game, the RESTORE RECORD is
        written (finding F2): the `session` line (with `restored_maps`) and a `world.jsonl` snapshot "restored from save
        <id>" (the live proof grades the memory the brain ACTS on from these). A continue that STOPS writes its session
        line and ends the run "stuck" through the play loop's own end (so the end record and a CHOSEN `end` line are
        written: no later continue). (R1 fix round, review R-2) A stop on a bound or a failed read (`may_retry`: nothing
        restored, nothing played) ends the same way, but its `end` line says `stopped_before_restore` and is not chosen,
        so a later continue may try again (the launcher looks through it to the session before)."""
        book = self._book
        result = yield from continue_game(hands, book, "continue the saved game")
        self._continued = result
        if not result.continued:
            self._continue_may_retry = bool(result.may_retry)
            self._writer = MemoryWriter(self._memory_path, book, header=None,
                                        session=self._session("continue", "continued", continued_from=None,
                                                              page=result.page, verified=False))
            self._writer.write_session()
            self._start_world(hands, self._choices, personality.name)
            return (yield from self._play(hands, personality, stop=f"the continue stopped: {result.why}"))
        record = result.record
        restored = restore(book, record["id"])
        self._writer = MemoryWriter(self._memory_path, book, header=None,
                                    session=self._session("continue", "continued", continued_from=record["id"],
                                                          page=result.page, verified=result.arrival,
                                                          restored_maps=restored.restored_maps, losses=restored.losses))
        written = self._writer.write_session()
        self._start_world(hands, self._choices, personality.name, restored.world)
        self._save_world(f"restored from save {record['id']}")
        hands.note("restore", "memory", f"restored from save {record['id']}",
                   {"save": record["id"], "maps": restored.restored_maps, "losses": restored.losses,
                    "frame_base": self._frame_base, "newest": result.newest, "page": result.page_kind})
        hands.tell(f"[AI-SAVE] continued save {record['id']}: its memory restored as of that save "
                   f"({len(restored.restored_maps)} maps, {restored.losses} battles lost so far); frame base "
                   f"{self._frame_base}")
        if not written:
            return (yield from self._play(hands, personality, stop="the memory of this continue could not be written"))
        return (yield from self._play(hands, personality, restored=restored))

    def _start_saving(self, hands: Hands, manager, state, mind, runner, starter: str, report: dict) -> None:
        """(R1, build spec section 3 (d)) With a memory file: the save POLICY over the goal manager's memory (its state lives
        there, so a continue restores it), the save goal's player (`runner.saver`, this brain's `_save`), the run's frames
        left for the policy, and the Pokemon REGISTRY by PID (L3 (a)-(b), a hands watcher). A new game's writer is made
        here; it writes nothing before the first save (no save, no file)."""
        if not self._saving:
            return
        report["saves"] = []
        if self._registry is None:
            self._registry = MonRegistry()
        self._kept = (manager, state, mind)
        if self._writer is None:
            identity = {"seed": self.seed, "personality": state.base, "favourite": state.favourite, "starter": starter,
                        "gender": None, "name": None}
            self._writer = MemoryWriter(self._memory_path, None, header={"game": self._game_name(), "identity": identity},
                                        session=self._session("new game", getattr(self.options, "cart", None)))
        self._policy = SavePolicy(manager.memory, hands.tell)
        manager.saving = self._policy
        manager.frames_left = lambda: self._frames_left(hands)
        runner.saver = lambda goal: self._save(hands, goal.reason, report)
        nav = self.navigator
        registry = self._registry
        hands.watchers.append(lambda seen: registry.observe(
            seen, caught=bool(nav.battle_log) and nav.battle_log[-1][2] == "caught"))

    def _frames_left(self, hands: Hands) -> int:
        """The run's frames left (`settings.frames`, the bound `_bounded` keeps), as the pad counts them."""
        return self.settings.frames - hands.pad.frames

    def _payload(self, report: dict, saving: dict) -> dict:
        """(R2) A save's memory: the world memory, the goal manager's KEEP fields, the personality, the battle mind, the
        registry, the battles lost so far (`game_memory.py` build_payload). `saving`: what THIS save makes of the save
        policy's fields (`SavePolicy.saved_state`), so the memory as of the save already counts the save itself (R1 fix
        round, review R-1: built before the SAVED page records it, the line held the save before it)."""
        manager, state, mind = self._kept
        goals = goals_part(replace(manager.memory, **saving))
        return build_payload(world=self.world.to_dict(), goals=goals, personality=personality_part(state),
                             battle=battle_part(mind), mons=self._registry.to_dict(), losses=report["losses"])

    def _save(self, hands: Hands, why: str, report: dict) -> Generator[None, None, str]:
        """(R1) SAVE through the game's own dialog (`skills/saving.py` save_game). At the first look with the whole SAVING
        page (the START of the write, D5) the save's line is appended to the memory file; on the SAVED page the `saved`
        line follows and the policy records the save (every due satisfied). OVERWRITE is answered YES only when the cart
        is this game's own (D17, `own_cart`). Returns the skill's outcome ("saved...", "not saved: ...", "stuck: ...")."""
        writer, policy = self._writer, self._policy
        pending: dict = {}

        def on_writing(stamp, look: Observation) -> bool:
            if stamp is None:
                hands.tell("[AI-SAVE] the play time was not read on the SAVING page: no memory line for this save")
                return False
            if writer.header is not None and look.player is not None:
                writer.header["identity"]["gender"] = look.player.gender
            saving = policy.saved_state(stamp, look.frame, writer.next_id, why)
            line = writer.write_save(play_time=stamp, frame=look.frame, where=where_of(look), party=party_of(look), why=why,
                                     payload=self._payload(report, saving))
            pending.update(written=line, stamp=stamp, frame=look.frame)
            hands.tell(f"[AI-SAVE] save {line.id}'s memory line ({'full' if line.full else 'a delta'}, {line.size} bytes) "
                       f"at play time {stamp[0]}:{stamp[1]:02d}: {'written' if line.reached else 'NOT WRITTEN'}")
            return line.reached

        def on_saved(look: Observation) -> None:
            line = pending.get("written")
            if line is None:
                return
            if line.reached:
                writer.write_saved(line.id, look.frame)
            # the save's own frame (the start of its write, its memory line's `frame`): the policy then remembers exactly
            # what the save's memory line says it will (R1 fix round, review R-1)
            policy.record_save(pending["stamp"], pending["frame"], line.id, why)

        outcome = yield from save_game(hands, why, own_cart(getattr(self.options, "cart", None), self._saves_made > 0),
                                       lambda: self._frames_left(hands), on_writing, on_saved)
        if outcome.startswith("saved"):
            self._saves_made += 1
            self._at_save_presses = hands.pad.presses
        line = pending.get("written")
        report.setdefault("saves", []).append({"why": why, "outcome": outcome, "id": line.id if line else None,
                                               "full": line.full if line else None, "size": line.size if line else None,
                                               "pad_frames": hands.pad.frames})
        hands.note("save", "outcome", outcome, {"why": why, "id": line.id if line else None})
        return outcome

    def _save_before_done(self, hands: Hands, report: dict) -> Generator[None, None, None]:
        """(R1, build spec section 3 (d), T8) THE END SAVE: the run is about to end "done" (R5's settle has played the
        screen out). A save that is DUE is made now, if the settled screen is free and the policy may save (the play time,
        the 3-minute gap, the frames). Its frames are handed on through `_settle_frames`, as the settle's are: the brain's
        own bound never cuts it. What it did is `report["end_save"]` and the end record's `saved_at_end`."""
        policy = self._policy
        if policy is None:
            return
        here = self.world.here() if self.world is not None else None
        due = policy.due_now(here.const if here is not None else None)
        if due is None:
            return
        look = hands.look()
        if not (report.get("settle") or {}).get("free"):
            why = "the screen at the end is not free"
        else:
            ok, why = policy.may_save(look, self._frames_left(hands) - DONE_BUDGET_MARGIN)
            why = None if ok else why
        if why is not None:
            hands.tell(f"[AI-SAVE] no save before putting the game down ({due['why']}): {why}")
            report["end_save"] = {"saved": False, "outcome": f"not saved: {why}"}
            return
        ended, outcome = yield from self._settle_frames(
            hands, self._save(hands, f"before putting the game down: {due['why']}", report))
        if not ended:
            outcome = "not saved: the run's frame budget ran out"
        report["end_save"] = {"saved": str(outcome).startswith("saved"), "outcome": outcome}

    def _after_milestones(self, ids: list[str]) -> None:
        """(R1, D3, D18) The milestones just passed, by their IDS only, to the save policy (a big story moment)."""
        if self._policy is not None and ids:
            self._policy.after_milestones(ids)

    def _after_heal(self, goal: Goal, ok: bool) -> None:
        """(R1, D3) A heal goal ended: at a POKéMON CENTER a save is due (the policy reads where it healed)."""
        if self._policy is None or goal.kind != "heal":
            return
        here = self.world.here() if self.world is not None else None
        self._policy.after_heal(goal, ok, here.const if here is not None else None)

    def _lost_line(self, hands: Hands) -> Callable[[], object] | None:
        """(R1, D12 (e)) What `_count_losses` calls at each battle lost: a `lost` line in the memory file (None: no file)."""
        writer = self._writer
        if writer is None:
            return None
        return lambda: writer.write_lost(hands.look())

    def _end_memory(self, hands: Hands, outcome: str, last: Observation) -> None:
        """(R1, D12 (a)) The memory file's `end` line, for every play-brain run that keeps one: `chosen` (done or stuck),
        `budget` (stopped), `at_save` (the last thing the run did was a successful save: no press since it)."""
        writer = self._writer
        if writer is None:
            return
        at_save = self._at_save_presses is not None and hands.pad.presses == self._at_save_presses
        if writer.write_end(outcome, at_save, last.frame, self._continue_may_retry) is False:
            hands.tell("[AI-SAVE] the memory file's end line did not reach the file")
        for problem in writer.problems:
            hands.tell(f"[AI-SAVE] memory file: {problem}")

    def _save_screen(self, hands: Hands, kind: str, why: str) -> Generator[None, None, bool]:
        """(R1, build spec D13) A save screen the play loop met OUTSIDE the save skill (the navigator's `on_menu`): the
        loop NEVER presses on a save page. A `save_dialog` (the write, a page) is waited out with no press, at most
        `SAVE_PAGE_WAIT` frames (True once it has gone; False, told: left unhandled). A save question or a START menu that
        takes input is closed with B (a B on the question is NO), told. With the skill as built none of this should fire:
        it guards against a skill bug."""
        if kind == "save_dialog":
            start = hands.pad.frames
            while hands.pad.frames - start < SAVE_PAGE_WAIT:
                look = hands.look()
                ui = look.screen.ui
                if ui is None or ui.kind != "save_dialog":
                    hands.tell(f"{why}: a save page the loop met went away after {hands.pad.frames - start} frames, with "
                               f"no press")
                    return True
                yield from hands.pad.busy("a save page is on screen: no press (DON'T TURN OFF THE POWER)")
            hands.tell(f"{why}: a save page stayed {SAVE_PAGE_WAIT} frames: left unhandled, with no press")
            hands.note("save_screen", "unhandled", kind, {"frames": hands.pad.frames - start})
            return False
        look = hands.look()
        ui = look.screen.ui
        if ui is not None and ui.kind == kind and ui.accepts_input:
            what = "the save question: B is NO" if kind == "save_yes_no" else "a START menu left open: B closes it"
            hands.tell(f"{why}: {what}")
            yield from hands.pad.press("B", why, f"{kind} takes input; {what}")
            return True
        yield from hands.pad.busy(busy_reason(look))
        return True

    # ------------------------------------------------------------------ build step 5: the story
    def _play(self, hands: Hands, personality, restored=None, stop: str | None = None) -> Generator[None, None, str]:
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
        no milestone for `STORY_PATIENCE` frames, `MAX_LOSSES` battles lost). (R5) "Done" comes after what is on screen has
        been played out (`_settle_before_done`), and every end records the screen it ends on (`_end_screen`).
        (R1 + R2) `restored`: a continue's memory as of its save (`game_memory.Restored`): the goal manager's KEEP fields,
        the personality, the battle mind, the registry and the battles lost so far start from it (D16, T5). `stop`: the run
        ends "stuck" with it at once, through the loop's own end (a continue that stopped)."""
        options, nav, world = self.options, self.navigator, self.world
        seed = self.seed
        story_rng = random.Random(f"{seed}:story")
        state = PersonalityState(personality.name, random.Random(f"{seed}:drift"), self._say)
        state.favourite = choose_favourite(story_rng)
        starter, starter_why = choose_starter(story_rng, personality.name, options.starter)
        mind = BattleMind(personality.name, random.Random(f"{seed}:battle"), "travel", BattleFaults())
        if restored is not None:
            # (R2, D16) the personality and the battle mind as of the save (the drift starts afresh)
            restore_personality(state, restored.personality)
            restore_battle(mind, restored.battle)
            self._registry = restored.mons
        nav.battler = lambda: play_battle(hands, mind, f"battle ({mind.purpose})")
        nav.answer = answer_question
        nav.on_menu = lambda kind, why: self._story_menu(hands, kind, why, starter)
        look = hands.look()
        story = load_story(look.player.gender if look.player is not None else None)
        manager = GoalManager(story, state, random.Random(f"{seed}:goals"), hints_off=options.fault_no_hints,
                              train_off=options.fault_no_training, errands_off=options.fault_no_errands)
        if restored is not None:
            manager.memory = restore_goals(manager.memory, restored.goals)  # (R2, D16) what it remembers, as of the save
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
        if restored is not None:
            # (R2, T5) the battles lost so far, as of the save: MAX_LOSSES counts across processes; new ones on top
            report["losses"] = report["restored_losses"] = restored.losses
        # (R1) with a memory file: the save policy, the save goal's player, the registry (`_start_saving`)
        self._start_saving(hands, manager, state, mind, runner, starter, report)
        self._waits = waits
        self._pushes = pushes
        ended: list = [None]  # (the second round) the pad's frames when the last goal ended (what played after it: a scene)

        def visited(const: str) -> bool:
            return any(memory.const == const and memory.visits for memory in world.maps.values())

        def current(seen: Observation) -> int:
            return manager.milestone(seen, visited)[0] if seen.progress is not None and seen.progress.marks else last[0]

        # (R5's fix round, the review's finding R5-F6) the milestones the story passed from one look to a later one, by the
        # loop's own read (`current`): the settle before "done" names the ones its screens passed (`_settle_before_done`;
        # a ch2_dad run's settle plays WALLY's tutorial, ch2_wally's proof). Kept as a field, as `_waits` is, so the
        # settle's signature (which the R5 A/B's recording wrapper calls) stays as it was
        self._passed_between = lambda first, then: [m.id for m in story.milestones[max(current(first), 0):current(then)]]

        last: list = [-1, None]  # the last milestone read from marks (index, milestone): kept while marks are not read
        changed_at = hands.pad.frames
        progress: dict = {}  # (build step 5.1) the last progress snapshot (`_progress`)
        still, last_frames = 0, -1
        if stop is not None:
            return self._play_end(hands, story, manager, runner, report, "stuck", stop)
        lost_line = self._lost_line(hands)
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
            stop = self._count_losses(hands, nav, report, lost_line)
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
                # (R5, backlog item R5: a FREE SCREEN before "done") the target's proof is read on this pass's look, and it
                # can flip while the screen is still busy (a scene, a box, the frame before an arrival scene): what is on
                # screen is played out first and the run ends "done" just below whatever that brought, an unsettled end
                # SAID (`_settle_before_done`; the end record, `_end_screen`)
                yield from self._settle_before_done(hands, nav, look, options.target, report)
                # (R1, T8) a save that is due is made before the game is put down, on the settled screen
                yield from self._save_before_done(hands, report)
            if milestone is None or index > target:
                return self._play_end(hands, story, manager, runner, report, "done", f"{options.target} reached")
            if milestone.steps and milestone.steps[0].do == "intro" and (look.player is None
                                                                         or look.screen.game_state != "OVERWORLD"):
                if any(goal["kind"] == "intro" for goal in report["goals"]):
                    return self._play_end(hands, story, manager, runner, report, "stuck", "the New Game intro again")
                if self._continued is not None:
                    # (R1, build spec 3 (e)) a CONTINUED game never plays the New Game intro: it never starts a new game
                    return self._play_end(hands, story, manager, runner, report, "stuck",
                                          "the title screen in a continued game: it never starts a New Game")
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
            # (R1, D3) a heal at a POKéMON CENTER makes a save due
            self._after_heal(goal, ok)
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
            if goal.kind == "save" and outcome.startswith("stuck:"):
                # (R1, build spec 3 (b)) a save dialog that could not be closed, a write that never ended, or a save the
                # memory could not record: the run ends here (never left to `play_out`, never pressed through)
                return self._play_end(hands, story, manager, runner, report, "stuck", outcome[len("stuck: "):])
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
    def _count_losses(hands: Hands, nav: Navigator, report: dict, on_lost: Callable[[], object] | None = None) -> str | None:
        """The play brain's count of battles LOST (`brain/goals.py` battles_lost over every battle the navigator's battler
        played, inside a goal or in a scene alike) into `report["losses"]`, each new one told; the end reason once
        `MAX_LOSSES` were lost, else None. (R1 + R2) A continue's battles lost before its save (`restored_losses`, T5) are
        counted first, the new ones on top; `on_lost` is told each new one (the memory file's `lost` line, D12 (e))."""
        lost = report.get("restored_losses", 0) + battles_lost(nav.battle_log)
        while report["losses"] < lost:
            report["losses"] += 1
            hands.tell(f"a battle was LOST ({report['losses']} of at most {MAX_LOSSES}): the party whited out; it goes on "
                       f"from where the game put it")
            if on_lost is not None:
                on_lost()
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
        if kind in ("save_dialog", "save_yes_no", "start_menu"):
            # (R1, D13) a save screen met outside the save skill: never an A on it (`_save_screen`)
            return (yield from self._save_screen(hands, kind, why))
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
            # (R1, D3, D18) after a big story moment a save is due: only the milestone IDS reach the save policy
            self._after_milestones([passed.id for passed in story.milestones[max(last[0], 0):index]])
        if milestone is not None:
            hands.tell(f"[AI-GOALS] the story is at {milestone.id} ({milestone.title}); proofs now: {milestone.proofs(marks)}")
            hands.note("milestone", milestone.id, milestone.title, {"index": index, "frame": look.frame})

    def _settle_before_done(self, hands: Hands, nav: Navigator, look: Observation, target: str,
                            report: dict) -> Generator[None, None, None]:
        """(R5, backlog item R5 "a FREE-SCREEN precondition", 2026-10-28; the recon `ai-research-notes/2026-10-28-R5-recon-
        {code,record,game}.md`) The run is about to end "done": the target's proof holds on this pass's look. But a proof can
        flip while the screen is still busy (FLAG_SET_WALL_CLOCK before MOM's upstairs text, ROXANNE's badge before TM39's),
        and a goal can hand the loop back mid-screen (`play_out` giving up, `talk_to`'s "talked; then ...", a walk's stop
        read before the screen). A person finishes what is on screen before putting the game down, and a save (backlog R1)
        is possible only on a free screen. So, at most `DONE_SETTLE_ROUNDS` times:
          * a screen that is not free is PLAYED OUT (`play_out`: it presses through waiting text, LESSONS PL-1, within its
            own bound, PL-4), and the battles it lost are counted as the loop counts them (`_count_losses`), so the end
            record agrees with the battle log; a play-out that leaves the screen busy ends the settle (PL-3: not retried);
          * a free screen gets the decision's pause that every goal gets (`_play`'s thinking pause) and one more look: ONE
            free look is not a free SCREEN. MEASURED 2026-10-28 (the R5 fixture probe, development seeds 5301 and 5302,
            target ch2_dad, on the tree before R5): DAD's scene ends with a warp to PETALBURG CITY, the warp's exit frees
            the player for ONE frame (the AI's own `nav_free` reads that frame free), and WALLY's tutorial (the city's
            ON_FRAME script) locks the controls on the very next frame: both runs ended "done" there, the game taking no
            input. (The tutorial's own warp back to the gym does the same before the gym's return scene: the settle's
            second pause finds it, `DONE_SETTLE_ROUNDS`.)
        The run then ends "done" whatever the settle brought: the game's proof holds, and a stop reason over a proof that
        holds would be a lie (`gates/live_step5.py`'s HONESTY check compares the exact "done: <target> reached"). A screen
        that did not free is SAID instead (PL-3): told, noted ("end_screen") and in the end record (`_end_screen`). What
        the settle did is `report["settle"]`. On a free look that stays free it presses nothing and plays nothing out: only
        the pause passes.
        (R5's fix round, the adversarial review's findings) Three more ends of the settle, each SAID, each still "done":
          * THE FRAME BUDGET (R5-F1): every frame of the settle is handed on through `_settle_frames`, which stops while
            `DONE_BUDGET_MARGIN` frames of `settings.frames` are left, so the brain's own bound never cuts a run whose
            target is reached into "stopped" with no end record; a cut is told and noted ("end_screen", "budget");
          * MAX_LOSSES (R5-F5): a play-out that loses the run's last allowed battle ends the settle at once (no pause, no
            further play-out: the run fights no battle past MAX_LOSSES), its stop the loop's own MAX_LOSSES reason;
          * the milestones the story passed while the screen was played out (R5-F6; a ch2_dad run's settle plays WALLY's
            tutorial, ch2_wally's proof) are told and kept in `report["settle"]["passed"]` and the end record. They are not
            added to `report["milestones"]` or told as MILESTONE lines, which the graders read."""
        began, played, paused, stop, cut, first = hands.pad.frames, 0, 0, None, False, look
        for _ in range(DONE_SETTLE_ROUNDS):
            if not nav_free(look):
                played += 1
                ended, stop = yield from self._settle_frames(hands, play_out(hands, nav,
                                                                             f"{target} reached: what is on screen first"))
                lost = self._count_losses(hands, nav, report, self._lost_line(hands))
                look = hands.look()
                if not ended:
                    cut, stop = True, f"the run's frame budget ran out ({self.settings.frames} frames)"
                    break
                if lost is not None:
                    stop = lost
                    break
                if not nav_free(look):
                    break
            pause, before = hands.pad.think_frames(), hands.pad.frames
            ended, _ = yield from self._settle_frames(hands, hands.pad.idle(
                pause, f"deciding to stop here, {target} reached: does a scene begin?"))
            paused += hands.pad.frames - before
            look = hands.look()
            if not ended:
                cut, stop = True, f"the run's frame budget ran out ({self.settings.frames} frames)"
                break
            if nav_free(look):
                break
        free = nav_free(look)
        between = getattr(self, "_passed_between", None)
        passed = between(first, look) if between is not None else []
        report["settle"] = {"played": played, "paused": paused, "frames": hands.pad.frames - began, "stop": stop,
                            "free": free, "budget": cut, "passed": passed}
        if passed:
            hands.tell(f"[AI-GOALS] what was on screen after {target} took the story further: it passed {', '.join(passed)} "
                       f"while it was played out (the run still ends at its target)")
        if cut:
            held = None if free else busy_reason(look)
            hands.tell(f"[AI-GOALS] {target} reached, but the run's frame budget ran out while what is on screen was played "
                       f"out ({self.settings.frames - hands.pad.frames} frames left): the run ends here, on a screen "
                       f"{'that is free' if free else 'held by: ' + str(held)}")
            hands.note("end_screen", "budget", held or "free", {"target": target, "stop": stop, "frame": look.frame,
                                                                 "played": played})
        elif not free:
            held = busy_reason(look)
            hands.tell(f"[AI-GOALS] {target} reached, but the screen did not free ({stop or 'a scene still plays'}): the run "
                       f"ends here, on a screen held by: {held}")
            hands.note("end_screen", "not free", held, {"target": target, "stop": stop, "frame": look.frame,
                                                        "played": played})

    def _settle_frames(self, hands: Hands, work: Generator[None, None, object]) -> Generator[None, None, tuple]:
        """(R5's fix round, R5-F1) Hand on `work`'s frames (a play-out, the decision's pause) for the settle before "done",
        one per `yield` as `_bounded` drives them, while more than `DONE_BUDGET_MARGIN` frames of the run's budget are
        left (the pad counts every frame it hands on, `hands/pad.py` `_count`). (True, its result) when `work` ended;
        (False, None) when the budget's end came first: `work` is then CLOSED, as `_bounded` closes a skill (a held button
        is released), and the run goes on to its end with no frame passing."""
        limit = self.settings.frames - DONE_BUDGET_MARGIN
        try:
            while hands.pad.frames < limit:
                try:
                    next(work)
                except StopIteration as done:
                    return True, done.value
                yield
            return False, None
        finally:
            work.close()

    @staticmethod
    def _end_screen(hands: Hands, report: dict, kind: str) -> dict:
        """(R5) The screen at the run's END, by one more look (a read at the same frame: no frame passes): whether it is
        free (`nav_free`, the loop's own test), what holds it (`busy_reason`) and the frame; for a "done" end also what
        the settle before it did (`_settle_before_done`): `played_out`, whether it had to PLAY a screen out (the pause
        alone is not one: R5's fix round renamed it from `settled`, which read as "the screen settled", the review's
        R5-F6), its frames, its pause, the last play-out's stop (or the budget's, or MAX_LOSSES') and the milestones the
        story passed meanwhile. Recorded at EVERY end (the report, the end line, the end note): a guard for the reader,
        never evidence (the recon's verifier: "keep it as a guard, never as evidence"), and no grader counts it. The look
        is a FRESH one (`hands.look()`, never `hands.last`: a play-out can end the run with the screen changed since the
        loop's last look, the MAX_LOSSES end after a whiteout)."""
        seen = hands.look()
        free = nav_free(seen)
        screen = {"free": free, "held_by": None if free else busy_reason(seen), "frame": seen.frame}
        if kind == "done":
            settle = report.get("settle") or {}
            screen.update(played_out=bool(settle.get("played")), settle_frames=settle.get("frames", 0),
                          paused=settle.get("paused", 0), settle_stop=settle.get("stop"), passed=settle.get("passed", []))
            if "end_save" in report:
                # (R1, T8) whether the end save was made (only a run that keeps a memory file and had a save due)
                screen["saved_at_end"] = bool(report["end_save"].get("saved"))
        return screen

    def _play_end(self, hands: Hands, story, manager, runner, report, kind: str, why: str) -> str:
        # (R5) the screen the run ends on, read FIRST (one more look at the same frame, so the wait and push watchers close
        # their stretches after it): into the report, the end line and the end note (`_end_screen`). (R5's fix round, the
        # sweep's S56, now pinned by `test_r5_the_end_look_closes_the_wait_record`) The order is ON PURPOSE: frames that
        # passed after the loop's last look with a box waiting for a press (a play-out that ended the run at MAX_LOSSES)
        # really passed, and the wait record must reach the end, not stop at the last look (`hands/waiting.py`; the
        # push record's history: "a run cut off by its frame budget never ENDS its last stretch"). On a "done" end the
        # settle's last look is at the end's frame, so the end look adds nothing there.
        screen = report["end_screen"] = self._end_screen(hands, report, kind)
        # the losses are the LOOP's count (`_count_losses`, at the top of every pass and, since R5, after each screen the
        # settle before "done" plays out), never recounted here: every way out of the loop leaves it after that count, with
        # no battle in between, so a recount could only HIDE a loop that stopped counting (the step-5 verifier's round 2:
        # with the loop's call removed, this recount made the sweep's "the AI's battles lost == the game's" pass 40 of 40).
        # A disagreement is told, not mended.
        logged = report.get("restored_losses", 0) + battles_lost(runner.nav.battle_log)
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
                   f"nothing {manager.memory.idle}; the screen at the end "
                   f"{'free' if screen.get('free') else 'NOT free (' + str(screen.get('held_by')) + ')'}"
                   + (f" ({'played out first' if screen.get('played_out') else 'nothing to play out'}, the settle "
                      f"{screen.get('settle_frames')} frames"
                      f"{'; the story passed ' + ', '.join(screen['passed']) + ' meanwhile' if screen.get('passed') else ''})"
                      if kind == "done" else ""))
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
                                      "no_balls": dict(manager.memory.no_balls), "home_heals": manager.memory.home_heals,
                                      # (R5) the screen the run ended on (`_end_screen`)
                                      "end_screen": screen})
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
    def _start_world(self, hands: Hands, choices: random.Random, personality: str, restored: dict | None = None) -> None:
        """The memory (empty, or a previous run's, `AI_PLAYER_WORLD`), told every look the hands take, and the
        navigator over it (the CHOICES stream: its path noise and detours never shift with the pacing). (R2) `restored`:
        a continue's world memory AS OF its save (`game_memory.py` restore), never a world file's last line (D19)."""
        options = self.options
        world = read_world(options.world_in) if options.world_in is not None else None
        source = f"the last snapshot of {options.world_in}" if world is not None else "nothing (a new memory)"
        if restored is not None:
            world = WorldMemory.from_dict(restored)
            source = "the save it continued (memory.jsonl, as of that save)"
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
