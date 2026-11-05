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
    "DEFAULT_BATTLES",
    "DEFAULT_BRAIN",
    "DEFAULT_FRAMES",
    "DEFAULT_MART_COUNT",
    "DEFAULT_MART_ITEM",
    "DEFAULT_ROAM_STEPS",
    "DEFAULT_TARGET",
    "DEFAULT_WATCH_EVERY",
    "HANDS_BRAINS",
    "INTENT_MARGIN",
    "VERDICT_FILE_NAME",
    "WORLD_BRAINS",
    "ENV_BATTLES",
    "ENV_BRAIN",
    "ENV_CLOCK",
    "ENV_CONTROL_TAP",
    "ENV_FAULT_BLIND_COUNT",
    "ENV_FAULT_HANG",
    "ENV_FAULT_FORGET_FIELD",
    "ENV_FAULT_IGNORE_RECOIL",
    "ENV_FAULT_IGNORE_REFUSAL",
    "ENV_FAULT_IGNORE_TYPES",
    "ENV_FAULT_UNCAPPED_RECOIL",
    "ENV_FAULT_OVERKILL",
    "ENV_FAULT_SHIFT_FAINTED",
    "ENV_FAULT_FORGET_UNUSABLE",
    "ENV_FAULT_NO_CATCH_STATUS",
    "ENV_FAULT_IGNORE_PP",
    "ENV_FAULT_FORGET_SHIFT",
    "ENV_FAULT_KEEP_LISTENERS",
    "ENV_FAULT_MANUAL",
    "ENV_FAULT_NO_CROP",
    "ENV_FAULT_NO_HINTS",
    "ENV_FAULT_NO_REBIND",
    "ENV_FAULT_NO_TRAINING",
    "ENV_FAULT_NO_ERRANDS",
    "ENV_FAULT_NO_INSTRUCTED",
    "ENV_FAULT_INSTRUCTED_MISSTEP",
    "ENV_FAULT_RAISE",
    "ENV_FAULT_SKIP_RESTORE",
    "ENV_FAULT_UNGATED_A",
    "ENV_FRAMES",
    "ENV_GOAL_MAP",
    "ENV_GOTO",
    "ENV_INTENT_FRAMES",
    "ENV_MART_COUNT",
    "ENV_MART_ITEM",
    "ENV_PACKAGE_ROOT",
    "ENV_PERSONALITY",
    "ENV_PURPOSE",
    "ENV_ROAM_STEPS",
    "ENV_RUN_DIR",
    "ENV_SEED",
    "ENV_STARTER",
    "ENV_TALK_TO",
    "ENV_TARGET",
    "ENV_WALL_DEADLINE",
    "ENV_WATCH_EVERY",
    "ENV_WORLD",
    "ENV_MEMORY",
    "ENV_CONTINUE",
    "ENV_CART",
    "ENV_FAULT_NO_SAVE",
    "ENV_HOST",
    "CARTS",
    "HOSTS",
    "HandsOptions",
    "RunOptions",
    "parse_tiles",
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
#: BUILD STEP 3: the WORLD brains (the world model and the AI's own navigator, `ai_player/world/`, `ai_player/brain/`),
#: played by the same `HandsBrain`: `explore` (explore with the personality's taste until `AI_PLAYER_GOAL_MAP`, or
#: until stuck / out of frames), `roam` (train by roaming through grass for `AI_PLAYER_ROAM_STEPS` steps, fleeing wild
#: battles), `goto` (walk to each tile of `AI_PLAYER_GOTO` on the current map in turn).
#: BUILD STEP 4: the BATTLE brain (also a world brain: it walks and roams with the same memory and navigator), which FIGHTS
#: with the AI's own decider (`brain/battle.py`, `skills/battle.py`): the battle on screen at the start, then the person
#: at `AI_PLAYER_TALK_TO` (walked up to and talked to: a trainer, the rival), then wild battles met while roaming the
#: grass, until `AI_PLAYER_BATTLES` battles have ended. The step-3 world brains above still FLEE (their proofs stand).
#: BUILD STEP 5: the PLAY brain (a world brain too), which plays the STORY itself: the goal manager (`brain/goals.py`) reads
#: where the story is from the milestone marks and chooses one goal at a time (the story's next step, or a human errand:
#: heal, shop, train, catch, an item, a chat), until the milestone `AI_PLAYER_TARGET` is done or the frames run out.
WORLD_BRAINS = ("explore", "roam", "goto", "battle", "play")
BRAINS = ("placeholder", "watcher") + HANDS_BRAINS + WORLD_BRAINS
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
#: BUILD STEP 3 (the world brains). The map to reach by exploring (a map constant as the eyes name it, e.g.
#: "LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN"); unset: explore with no goal.
ENV_GOAL_MAP = "AI_PLAYER_GOAL_MAP"
#: The roam brain's training steps.
ENV_ROAM_STEPS = "AI_PLAYER_ROAM_STEPS"
DEFAULT_ROAM_STEPS = 120
#: The goto brain's errands: tiles of the current map, "x,y;x,y;...".
ENV_GOTO = "AI_PLAYER_GOTO"
#: A `world.jsonl` a previous run wrote: the AI starts with that memory (its last line), so knowledge grows over a
#: playthrough. Unset: it starts knowing nothing.
ENV_WORLD = "AI_PLAYER_WORLD"
#: The intent's own frame budget (it ends itself with "budget:" before the run's frame budget stops it); unset:
#: the run's frames minus `INTENT_MARGIN`.
ENV_INTENT_FRAMES = "AI_PLAYER_INTENT_FRAMES"
INTENT_MARGIN = 600
#: BUILD STEP 4 (the battle brain). How many battles to play before it ends ("battles: N played"); default 1.
ENV_BATTLES = "AI_PLAYER_BATTLES"
DEFAULT_BATTLES = 1
#: "x,y": a person on the current map to walk up to and talk to first (a trainer, the rival); unset: nobody.
ENV_TALK_TO = "AI_PLAYER_TALK_TO"
#: Why it battles: "train" (wild battles fought for experience, run from when its Pokemon is low or the foe far stronger)
#: or "travel" (run from a wild battle it does not want, by its temperament). Default "train".
ENV_PURPOSE = "AI_PLAYER_PURPOSE"
#: FAULT (build step 4): the decider values every move as if every type matchup were neutral and nothing had STAB (the
#: TYPE arm's fault: shows the type chart is what makes it choose the effective move).
ENV_FAULT_IGNORE_TYPES = "AI_PLAYER_FAULT_IGNORE_TYPES"
#: FAULT (build step 4): the decider ignores recoil (the RECOIL arm's fault).
ENV_FAULT_IGNORE_RECOIL = "AI_PLAYER_FAULT_IGNORE_RECOIL"
#: FAULTS (the step-4 verifier's round, `brain/battle.py` BattleFaults): the recoil charged on the move's whole worth (the
#: step-4 rule); the replacement after a faint sees only the party menu's look (the step-4 bug); the party menu's refusal
#: watched instead of read (the step-4 skill).
ENV_FAULT_UNCAPPED_RECOIL = "AI_PLAYER_FAULT_UNCAPPED_RECOIL"
ENV_FAULT_FORGET_FIELD = "AI_PLAYER_FAULT_FORGET_FIELD"
ENV_FAULT_IGNORE_REFUSAL = "AI_PLAYER_FAULT_IGNORE_REFUSAL"
#: FAULTS (step 4.1, `brain/battle.py` BattleFaults): every move valued uncapped (step 4: overkill valued); the shift
#: question answered about the fainted foe and the party menu ranked by level (step 4); a refused move chosen again (step 4).
ENV_FAULT_OVERKILL = "AI_PLAYER_FAULT_OVERKILL"
ENV_FAULT_SHIFT_FAINTED = "AI_PLAYER_FAULT_SHIFT_FAINTED"
ENV_FAULT_FORGET_UNUSABLE = "AI_PLAYER_FAULT_FORGET_UNUSABLE"
#: FAULT (step 4.1 round 2, `brain/battle.py` BattleFaults): no sleep or paralysis move to help a catch (step 4: none).
ENV_FAULT_NO_CATCH_STATUS = "AI_PLAYER_FAULT_NO_CATCH_STATUS"
#: FAULT (step 4.1 round 2): the decider blind to its moves' PP, so the GAME refuses a move with none (as it refuses a
#: Disabled one: the same code) and gives the move grid back: finding 2's refusal played live.
ENV_FAULT_IGNORE_PP = "AI_PLAYER_FAULT_IGNORE_PP"
#: FAULT (step 4.1 round 3): the shift question judged about the incoming foe, but the member chosen there NOT carried into
#: the party menu (ranked again, by level): the live A/B of the carry (arm SHIFTCX).
ENV_FAULT_FORGET_SHIFT = "AI_PLAYER_FAULT_FORGET_SHIFT"
#: BUILD STEP 5 (the play brain). The milestone to reach (an id of `knowledge/milestones.json`, e.g. `ch1_pokedex`, the
#: end of chapter 1; `ch2_wally`, of chapter 2); the brain ends "done: ..." once the marks prove it.
ENV_TARGET = "AI_PLAYER_TARGET"
DEFAULT_TARGET = "ch1_pokedex"
#: The starter to take from PROF. BIRCH's bag (TREECKO, TORCHIC, MUDKIP); unset: the personality's seeded draw. The
#: acceptance batch names one per run (design draft §10.5: "the starter is SEEDED per run, giving 9 runs = 3 per starter").
ENV_STARTER = "AI_PLAYER_STARTER"
#: FAULT (build step 5): the goal manager never uses a hint (no goal map from the words it read, nobody asked): it explores
#: with its taste alone (the HINTS arm: slower, or a reasoned stop within its budget).
ENV_FAULT_NO_HINTS = "AI_PLAYER_FAULT_NO_HINTS"
#: FAULT (build step 5): no training before a known fight (the TRAIN arm: the rival's win rate measured without it).
ENV_FAULT_NO_TRAINING = "AI_PLAYER_FAULT_NO_TRAINING"
#: FAULT (build step 5.1): the BEELINE control: no look-around errand, no detour, no stop on a new map, no chat, no catching
#: roam (`brain/goals.py` errands_off): the ERRANDS_OFF arm the intent mix, the seed divergence and the no-speedrun bound
#: must tell apart from the real code.
ENV_FAULT_NO_ERRANDS = "AI_PLAYER_FAULT_NO_ERRANDS"
#: R1 + R2 (build spec 2026-10-29 section 3 (e); D8, D11, D14, D17): the game's memory file (`memory.jsonl`,
#: `game_memory.py`), resolved by the LAUNCHER (`paths.py` AppPaths) and handed over here. The play brain saves through the
#: game's own dialog whenever it is given one (D14); a run without it behaves exactly as before R1.
ENV_MEMORY = "AI_PLAYER_MEMORY"
#: "1": this run CONTINUES the game on the cartridge from the title (`--continue`, D11): the AI plays the title itself.
ENV_CONTINUE = "AI_PLAYER_CONTINUE"
#: D17: what the cartridge held when the run began: `empty` (--fresh or --state emptied it), `continued`, `kept` (no flag).
ENV_CART = "AI_PLAYER_CART"
#: CONTROL (R1, D14): a memory file is given, but the AI never saves and keeps no memory file: the pre-R1 loop.
ENV_FAULT_NO_SAVE = "AI_PLAYER_FAULT_NO_SAVE"
#: FAULT (chapter 5, 2026-11-05): the play brain never calls the instructed-choice skill (`skills/instructed.py`): a forced
#: multichoice and the POKéNAV's menus are the stop they were before it (the live arm L2).
ENV_FAULT_NO_INSTRUCTED = "AI_PLAYER_FAULT_NO_INSTRUCTED"
#: FAULT (chapter 5, the live arm L4): the FIRST field choice of each scene takes the next option with a word instead of the
#: named one (a slip of the thumb), so a forced menu comes back under its "Please select ..." page.
ENV_FAULT_INSTRUCTED_MISSTEP = "AI_PLAYER_FAULT_INSTRUCTED_MISSTEP"
#: Who started the play brain, for the memory file's `session` line: `launcher` (the default) or `harness` (the in-process
#: test side, which has no lifecycle: D12 (a) classifies a harness session by its `end` line alone).
ENV_HOST = "AI_PLAYER_HOST"
#: The values `AI_PLAYER_CART` and `AI_PLAYER_HOST` may take (= `game_memory.py` CARTS and HOSTS; a test pins them equal).
CARTS = ("empty", "continued", "kept")
HOSTS = ("launcher", "harness")

#: Every fault and control switch (the launcher prints the ones that are set).
ALL_SWITCHES = (
    ENV_FAULT_KEEP_LISTENERS, ENV_FAULT_RAISE, ENV_FAULT_MANUAL, ENV_FAULT_HANG, ENV_FAULT_NO_REBIND,
    ENV_FAULT_SKIP_RESTORE, ENV_CONTROL_TAP, ENV_FAULT_NO_CROP, ENV_FAULT_UNGATED_A, ENV_FAULT_BLIND_COUNT,
    ENV_FAULT_IGNORE_TYPES, ENV_FAULT_IGNORE_RECOIL, ENV_FAULT_UNCAPPED_RECOIL, ENV_FAULT_FORGET_FIELD,
    ENV_FAULT_IGNORE_REFUSAL, ENV_FAULT_OVERKILL, ENV_FAULT_SHIFT_FAINTED, ENV_FAULT_FORGET_UNUSABLE,
    ENV_FAULT_NO_CATCH_STATUS, ENV_FAULT_IGNORE_PP, ENV_FAULT_FORGET_SHIFT, ENV_FAULT_NO_HINTS, ENV_FAULT_NO_TRAINING,
    ENV_FAULT_NO_ERRANDS, ENV_FAULT_NO_SAVE, ENV_FAULT_NO_INSTRUCTED, ENV_FAULT_INSTRUCTED_MISSTEP,
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
    # BUILD STEP 3 (the world brains); defaults so a caller that names only the step-2 fields still works
    goal_map: str | None = None
    roam_steps: int = DEFAULT_ROAM_STEPS
    goto: tuple[tuple[int, int], ...] = ()
    world_in: Path | None = None
    intent_frames: int | None = None
    # BUILD STEP 4 (the battle brain); defaults so a caller that names only the earlier fields still works
    battles: int = DEFAULT_BATTLES
    talk_to: tuple[int, int] | None = None
    purpose: str = "train"
    fault_ignore_types: bool = False
    fault_ignore_recoil: bool = False
    # (the step-4 verifier's round)
    fault_uncapped_recoil: bool = False
    fault_forget_field: bool = False
    fault_ignore_refusal: bool = False
    # (step 4.1)
    fault_overkill: bool = False
    fault_shift_fainted: bool = False
    fault_forget_unusable: bool = False
    # (step 4.1 round 2)
    fault_no_catch_status: bool = False
    fault_ignore_pp: bool = False
    # (step 4.1 round 3)
    fault_forget_shift: bool = False
    # BUILD STEP 5 (the play brain); defaults so a caller that names only the earlier fields still works
    target: str = DEFAULT_TARGET
    starter: str | None = None
    fault_no_hints: bool = False
    fault_no_training: bool = False
    # BUILD STEP 5.1
    fault_no_errands: bool = False
    # R1 + R2 (build spec 2026-10-29, section 3 (e)): the memory file, a continue, what the cart held, the no-save CONTROL,
    # and who started the brain; defaults so a caller that names only the earlier fields behaves exactly as before R1
    memory_file: Path | None = None
    continue_game: bool = False
    cart: str | None = None
    fault_no_save: bool = False
    host: str = "launcher"
    # (chapter 5, 2026-11-05) the instructed-choice skill's two faults; defaults: the skill plays, no slip
    fault_no_instructed: bool = False
    fault_instructed_misstep: bool = False

    def __post_init__(self) -> None:
        # D19: a continued game's memory is its save's, and nothing else's: a world file beside a continue is an error
        if self.continue_game and self.world_in is not None:
            raise ValueError(f"{ENV_WORLD} cannot be given with {ENV_CONTINUE}: the memory of a continued game is its "
                             f"save's (the memory file), never another world file")
        if self.continue_game and self.memory_file is None:
            raise ValueError(f"{ENV_CONTINUE} needs {ENV_MEMORY}: a continue restores the memory of the save it continues")
        if self.cart is not None and self.cart not in CARTS:
            raise ValueError(f"{ENV_CART} must be one of {CARTS}, got {self.cart!r}")
        if self.host not in HOSTS:
            raise ValueError(f"{ENV_HOST} must be one of {HOSTS}, got {self.host!r}")

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
        raw_steps = os.environ.get(ENV_ROAM_STEPS, "").strip()
        steps = int(raw_steps) if raw_steps else DEFAULT_ROAM_STEPS
        if not 1 <= steps <= 5000:
            raise ValueError(f"{ENV_ROAM_STEPS} must be 1..5000, got {steps}")
        raw_world = os.environ.get(ENV_WORLD, "").strip()
        raw_memory = os.environ.get(ENV_MEMORY, "").strip()
        raw_intent = os.environ.get(ENV_INTENT_FRAMES, "").strip()
        raw_battles = os.environ.get(ENV_BATTLES, "").strip()
        battles = int(raw_battles) if raw_battles else DEFAULT_BATTLES
        if not 1 <= battles <= 200:
            raise ValueError(f"{ENV_BATTLES} must be 1..200, got {battles}")
        talk = parse_tiles(os.environ.get(ENV_TALK_TO, ""))
        purpose = os.environ.get(ENV_PURPOSE, "").strip() or "train"
        if purpose not in ("train", "travel"):
            raise ValueError(f"{ENV_PURPOSE} must be train or travel, got {purpose!r}")
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
            goal_map=os.environ.get(ENV_GOAL_MAP, "").strip() or None,
            roam_steps=steps,
            goto=parse_tiles(os.environ.get(ENV_GOTO, "")),
            world_in=Path(raw_world) if raw_world else None,
            intent_frames=int(raw_intent) if raw_intent else None,
            battles=battles,
            talk_to=talk[0] if talk else None,
            purpose=purpose,
            fault_ignore_types=_flag(ENV_FAULT_IGNORE_TYPES),
            fault_ignore_recoil=_flag(ENV_FAULT_IGNORE_RECOIL),
            fault_uncapped_recoil=_flag(ENV_FAULT_UNCAPPED_RECOIL),
            fault_forget_field=_flag(ENV_FAULT_FORGET_FIELD),
            fault_ignore_refusal=_flag(ENV_FAULT_IGNORE_REFUSAL),
            fault_overkill=_flag(ENV_FAULT_OVERKILL),
            fault_shift_fainted=_flag(ENV_FAULT_SHIFT_FAINTED),
            fault_forget_unusable=_flag(ENV_FAULT_FORGET_UNUSABLE),
            fault_no_catch_status=_flag(ENV_FAULT_NO_CATCH_STATUS),
            fault_ignore_pp=_flag(ENV_FAULT_IGNORE_PP),
            fault_forget_shift=_flag(ENV_FAULT_FORGET_SHIFT),
            target=os.environ.get(ENV_TARGET, "").strip() or DEFAULT_TARGET,
            starter=os.environ.get(ENV_STARTER, "").strip().upper() or None,
            fault_no_hints=_flag(ENV_FAULT_NO_HINTS),
            fault_no_training=_flag(ENV_FAULT_NO_TRAINING),
            fault_no_errands=_flag(ENV_FAULT_NO_ERRANDS),
            memory_file=Path(raw_memory) if raw_memory else None,
            continue_game=_flag(ENV_CONTINUE),
            cart=os.environ.get(ENV_CART, "").strip() or None,
            fault_no_save=_flag(ENV_FAULT_NO_SAVE),
            host=os.environ.get(ENV_HOST, "").strip() or "launcher",
            fault_no_instructed=_flag(ENV_FAULT_NO_INSTRUCTED),
            fault_instructed_misstep=_flag(ENV_FAULT_INSTRUCTED_MISSTEP),
        )


def parse_tiles(text: str) -> tuple[tuple[int, int], ...]:
    """"x,y;x,y" -> ((x, y), (x, y)); empty -> ()."""
    tiles = []
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        x, y = (int(v) for v in part.split(",", 1))
        tiles.append((x, y))
    return tuple(tiles)
