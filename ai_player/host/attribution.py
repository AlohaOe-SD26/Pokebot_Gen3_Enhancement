"""Who pressed it? Who wrote it? Did bot code run for the AI? Counts every input, memory write, state
load, clock change, frame and bot-code call by ORIGIN, audits the emulator's SINKS, checks that the
AI's listener isolation is still in place before every frame, and writes the verdict file.

WHY (design draft §2.2 "foreign-press gate" and §10.2): RULING 35 says the AI plays by itself. The
framework still runs code every frame (listeners, plugins, the watchdog) that can press buttons,
write game memory or load save states. Removing those listeners is the fix (`isolation.py`); this
module is the MEASUREMENT that proves the fix holds, in every run, by instrumenting the ACTION
rather than its inputs (CLAUDE.md session rule 7).

WHY THREE LAYERS: the first version counted calls to the framework's entry points only. A verifier
planted a brain that wrote `emulator._pressed_inputs` directly: the counters read CLEAN while the
planted presses won the battle. So layer 2 audits what reached the game, whatever path it took. A
second verifier then ran the bot's PATHFINDER from inside the brain: it pressed nothing and wrote
nothing, so neither layer had anything to count (2026-10-07, plant VB). Layer 3 watches for bot code
itself running on the AI's behalf.

1. DOORS. While the AI mode runs, the framework's entry points are replaced by thin wrappers that
   count each call by origin:
     inputs  emulator.press_button / hold_button / release_button / restore_held_buttons /
             reset_held_buttons (the last two only when they change something)
     writes  emulator.write_bytes; modules.memory's write functions (re-bound in EVERY module that
             copied them with `from modules.memory import ...`); the game clock's methods on
             `core.rtc` (advance_time, use_* : the debug menu's "Advance RTC" is one of them)
     loads   emulator.load_save_state / load_save_game / reset; the mGBA core's load_state,
             load_state_slot, load_save, load_temporary_save, load_raw_state, load_patch, reset
     frames  the core's step / run_loop (a frame advance outside the main loop)
   Origin = AI when any frame on the Python stack belongs to the `ai_player` package, else FOREIGN.
   An AI input counts as routed only when `host/controller.py` is its IMMEDIATE caller, so bot
   code called from AI code cannot borrow the controller's name. Nested calls (write_symbol ->
   write_bytes) are counted once, at the outermost wrapper. A foreign press also records the chain
   of bot-code functions on its stack (origin kind `chains`), so the evidence names the PATH that
   pressed (`BattleListener.fight`), not only the line.

2. SINKS, audited by a wrapper on the core's `run_frame`, i.e. right before the CPU runs a frame:
     frames   a frame is REAL when the main loop runs it (`modules/main.py main_loop` ->
              `run_single_frame`), ALWAYS, whatever else is open; otherwise a LOOK-AHEAD inside
              `peek_frame` / `get_screenshot` / `get_task_look_ahead` (those restore the state
              afterwards), and EXTRA otherwise. (Step 0.1 checked the look-ahead depth FIRST: a
              verifier held a `peek_frame` open on the main thread, and every later main-loop frame
              was skipped as a look-ahead, so A pressed through no door won a battle with the verdict
              CLEAN and `real_frames=100` of 3000. Now a real frame with a look-ahead still open on
              its thread is itself counted as tampering.)
     continuity  `context.frame` (main.py adds one per main-loop pass) must advance by exactly one
              between two audited real frames, and by at most one from the last audited frame to the
              finish. Each main-loop frame that ran without a sink audit is counted
              (`instrument_tampered`): an independent cross-check that the audit saw every frame the
              main loop ran, whatever a future classification bug lets through.
     inputs   every key LATCHED into the core for the frame (`get_inputs()`) must have been set by a
              counted input door since the last frame, else `unattributed_inputs`; and the
              emulator's `_prev_pressed_inputs` (which decides what the NEXT press does) must still
              be what the last real frame left there, else `unattributed_inputs`.
     memory   WRAM and IWRAM must be byte-identical from the end of one frame to the start of the
              next, and the game clock's native setting (override, value) must be unchanged since
              the last counted door, else `unattributed_state_changes`.
     isolation  the AI's guard listener must be in `context.bot_listeners` before every real frame.
              If it is not, the framework rebuilt its list behind the AI's back (a reset or a state
              load makes `main.py` do that) and its listeners may already have pushed bot code on
              top of the AI: `isolation_lost`, and the session's callback ends the run with that
              reason BEFORE the frame runs, so a starved AI is a recorded BREACH, never a silent one.
     instrument  before every real frame and at exit: every wrapper still installed, the core's
              callback lists and the emulator's frame callback unchanged, `context.emulator` the
              same object, the bot-code monitor still registered, every SEALED module's namespace
              and code unchanged. Else `instrument_tampered`.

3. BOT CODE. A `sys.monitoring` PY_START hook (Python 3.12) sees every Python function START. When
   the function is the bot's decision code (`BOT_BRAIN_PATHS`, relative to the framework folder) and
   an `ai_player` frame is on the stack, that is the AI running the bot's brain: `ai_bot_calls`.
   Every other code location is switched off after its first start (`DISABLE`), so the cost is one
   callback per function, not per call. Bot code the FRAMEWORK runs (its listeners, in the fault
   arms) has no AI frame under it and is not counted here: its actions are counted by layers 1-2.

Fail-closed: a frame this module cannot place as REAL is EXTRA (a breach), a failure inside the
instrument is `instrument_errors` (a breach), and a run in which no real frame was audited has the
verdict UNVERIFIED, never CLEAN.

THE VERDICT IS WRITTEN BY THIS MODULE, NOT PRINTED. Any code in the process can print a line that
looks like `[AI-PURITY] ... verdict=CLEAN`. So the lifecycle's `finish` asks this module to write
`<run_dir>/purity.json`, and the launcher grades the run from that file: a child that exits 0
without one exits 8 instead. Only `lifecycle.finish` may finalize the audit or write the file (any
other caller is counted as tampering and refused). After the file is written, the `run_frame`
wrapper stays on as a TRIPWIRE: `finish` ends with `sys.exit`, so no real frame should ever run
again; if one does, something caught that SystemExit and kept playing with every counter off, so the
file is rewritten as BREACH (`ran_after_finish`) and the process is ended with `os._exit`. And `finish`
arms an EXIT WATCHDOG here (`arm_exit_watchdog`, the lifecycle's only): a daemon timer that ends the
process with `os._exit` if it is still alive 20 s after its verdict, because a non-daemon framework
thread (the HTTP server's) would otherwise hold the interpreter open at shutdown for ever. When
`finish` runs on a thread other than the main thread (the session's interrupt watch ending a run whose
main thread is stuck, or a GUI's worker thread), `sys.exit` cannot end the process at all, so the
watchdog ends it at once instead of 20 s later.

WHERE THE NUMBERS LIVE, AND WHY (step 0.1, the adversarial review's finding 3). The step-0 counters
kept their values in a private dict on the counters object, and the instrument kept its flags and
baselines in slots of its own object, so any code holding them could write `counters._values[...] = 0`,
`attribution._installed = False` or `attribution._snapshot = None`. Now:
  * the COUNTS live in a closure (`_make_vault`) that no attribute of any object leads to; the
    store only grows (adding a count below 1 is refused and itself counted), and the list of breach
    counters is captured inside it, so rebinding a module constant later changes nothing;
  * everything the instrument changes after it is built lives in a `_State` held in the same kind of
    closure (`_REGISTRY`); `Attribution` and `PurityCounters` hold NOTHING (`__slots__ = ()`);
  * the REGISTRY and the counter stores answer only THIS file's code (round 3). The module attribute
    `_REGISTRY` is reachable by name, and a verifier read from the code that
    `_REGISTRY.payload_of(counters).add("real_frames", None, None, 5)` was accepted uncounted: a POSITIVE
    count passed "counts only grow", and one fake real frame turns an UNVERIFIED run (no frame audited)
    into CLEAN. The same route handed out the `_State` (`.local.depth = 1` switches every door's
    counting off, a poisoned `brain_cache` hides bot code) and the fingerprint lists (`.clear()` them
    and a rewritten module namespace goes unseen). Now every registry function, and each store's
    `add` and `note`, refuses a caller whose code is not in this file, and counts the attempt;
  * instances refuse attribute assignment from any code outside this file, classes refuse it
    always (`Sealed`), and the host modules refuse it on their module object (`seal_module`); every
    refusal is COUNTED as `instrument_tampered`, not merely raised;
  * the same instance guard is public (`Guarded`): an instance of a `Guarded` class accepts
    attribute writes only from the file that DEFINES its class (recorded by `Sealed` when the class
    is built). The lifecycle, the session, the listener isolation and the guard listener use it, so
    `lifecycle._verdict_path = None`, `session.frame_cap = ...` or `guard._on_frame = ...` from
    the AI's own code are refused and counted too (a verifier wrote the lifecycle's slots unseen);
  * a sealed module's namespace and its functions' code are fingerprinted at seal time and checked
    before every real frame, so a write that goes around `__setattr__` (`vars(module)[...] = ...`)
    is still caught.
RESIDUAL (so nobody over-reads it): Python has no private memory. A closure's cells, a function's
`__code__`, code COMPILED under this file's name (the caller checks compare file names), `gc` and
`ctypes` can still reach anything; the static gate refuses every spelling of those in the AI's code
(dunders, private attributes of other objects, `vars`, `compile`, `gc`, `ctypes`), and the run-time
defenses refuse and count every ATTRIBUTE-level route and every call into the registry from outside.
That is a list of known routes, not a proof. (`gates/test_host.py` uses the compile route on purpose,
test-side, to reach the `_State` it needs; that is the residual working as documented.)

THE FRAME FENCE (round 3, a verifier's mutant of the interrupt watch). `finish` can run on a thread
other than the main thread: the session's interrupt watch ends a run whose main thread has not reached
the guard for 10 s. The main thread is not necessarily dead, only late: a brain blocked in one long
call (a coach request, later) wakes up and the main loop runs its next frame while the watch thread is
finishing. That frame either ran UNAUDITED (after the final audit, before the verdict was written) or
hit the tripwire (after the verdict: `ran-after-finish`, BREACH, exit 6, a false breach of a run that
was only interrupted). So now:
  * `finalize_audit` first names the FINISHING thread, then waits (bounded, `FRAME_IN_FLIGHT_SECONDS`)
    for a frame another thread is in the middle of, and holds the frame lock through the final audit;
  * the `run_frame` wrapper takes the same lock for every frame, and a frame on any thread OTHER than
    the finishing one does not run at all: it waits for the process to end (the exit watchdog ends it
    at once when `finish` ran off the main thread) and says so once (`[AI-LIFECYCLE] ... waits for the
    process to end instead of running`). If the process is still alive `FENCE_SECONDS` later, nothing
    is ending it, and the tripwire ends it as a BREACH;
  * the verdict file records which thread finished and whether a frame was in flight (`finish`).

RESIDUAL BLIND SPOTS of the sinks: the memory sink snapshots WRAM and IWRAM, which hold all of the
game's variables, but not the CPU registers, the I/O registers, video memory or the cartridge save;
a change made ONLY there through a native call is invisible here. The bot-code monitor sees bot code
that RUNS, not bot DATA read without calling a function (a constant table); that is the static
gate's job (rule a). A run killed by the launcher's hard wall clock writes no verdict file at all.

This is the ONLY play-loop file allowed to name the state-changing functions and to use reflection
(`gates/check_purity.py`, rules b, d and f), because wrapping them requires it. In exchange its exact
bytes are pinned in the gate (rule g): any change here is a reviewed change.
"""

from __future__ import annotations

import contextlib
import functools
import json
import os
import sys
import threading
import time
from collections import Counter, namedtuple
from collections.abc import Callable
from pathlib import Path
from types import FrameType, ModuleType

import modules.memory as framework_memory
from mgba import ffi
from modules.context import context

__all__ = ["Attribution", "Guarded", "PurityCounters", "Sealed", "seal_module"]

#: Emulator methods that change the buttons. press/hold/release count as input actions; the two
#: bulk methods count only when they actually change something.
EMULATOR_INPUT_METHODS = ("press_button", "hold_button", "release_button", "restore_held_buttons", "reset_held_buttons")
EMULATOR_WRITE_METHODS = ("write_bytes",)
EMULATOR_LOAD_METHODS = ("load_save_state", "load_save_game", "reset")
CORE_LOAD_METHODS = ("load_state", "load_state_slot", "load_save", "load_temporary_save", "load_raw_state", "load_patch", "reset")
CORE_FRAME_METHODS = ("step", "run_loop")
#: The game clock's methods (`mgba/core.py` class RTC). The game reads the clock for berries, tides,
#: Shoal Cave and every time-of-day event, so changing it is a write to the game's world.
RTC_METHODS = ("advance_time", "use_real_time", "use_real_time_with_offset", "use_fixed", "use_simulated_time")
MEMORY_FUNCTIONS = ("write_symbol", "write_to_save_block", "set_event_flag", "set_event_flag_by_number", "set_event_var")
#: Emulator-layer functions that run frames only to look ahead, and restore the state afterwards.
LOOK_AHEAD_FUNCTIONS = ("peek_frame", "get_screenshot", "get_task_look_ahead")
#: The look-ahead functions whose closing `load_save_state` is a restore, not a load.
PEEK_RESTORERS = ("peek_frame", "get_screenshot")
#: mGBA core callback lists. A callback runs INSIDE a frame, so a new one could act unseen.
CORE_CALLBACK_LISTS = (
    "video_frame_started", "video_frame_ended", "core_crashed", "shutdown",
    "sleep", "keys_read", "savedata_updated", "alarm",
)
WRAM_SIZE = 0x40000  # 0x02000000-0x0203FFFF
IWRAM_SIZE = 0x8000  # 0x03000000-0x03007FFF
KEY_NAMES = ("A", "B", "Select", "Start", "Right", "Left", "Up", "Down", "R", "L")

#: The bot's DECISION code, as paths relative to the framework folder (a trailing "/" = the whole
#: folder). Layer 3 counts any of it that starts while AI code is on the stack. The gate checks that
#: every module its import backstop refuses (`FORBIDDEN_PREFIXES`) is covered here, so the two lists
#: cannot drift apart. What is NOT here is the framework's eyes and hands (the emulator, memory
#: reading, data parsing, the context), which the AI is meant to use through its adapters.
BOT_BRAIN_PATHS = (
    "modules/modes/",
    "modules/battle_strategies/",
    "modules/story/",
    "modules/built_in_plugins/",
    "modules/battle_action_selection.py",
    "modules/battle_evolution_scene.py",
    "modules/battle_fault.py",
    "modules/battle_handler.py",
    "modules/battle_menuing.py",
    "modules/battle_move_replacing.py",
    "modules/debug_utilities.py",
    "modules/encounter.py",
    "modules/endless_x4.py",
    "modules/faint_chooser.py",
    "modules/game_cheats.py",
    "modules/macros.py",
    "modules/map_path.py",
    "modules/mart.py",
    "modules/menuing.py",
    "modules/player_pc_navigaton.py",
    "modules/pokemon_storage_navigaton.py",
    "modules/safari_strategy.py",
    "modules/warp_graph.py",
    "modules/watchdog.py",
    "plugins/",
)
#: Inside those folders, the plugin seam itself (base classes, the mode registry) and the AI's own hook.
BOT_BRAIN_EXCEPTIONS = (
    "modules/modes/__init__.py",
    "modules/modes/_interface.py",
    "plugins/custom_modes/ai_player_mode.py",
)
#: `sys.monitoring` tool ids the bot-code monitor may take. 0-2 and 5 are reserved by convention for
#: debuggers, coverage, profilers and optimizers; 3 and 4 are free.
MONITORING_TOOL_IDS = (4, 3)
MONITORING_TOOL_NAME = "ai_player purity monitor"

COUNTER_NAMES = (
    "ai_presses", "ai_unrouted_presses", "ai_writes", "ai_loads", "ai_bot_calls",
    "foreign_presses", "foreign_writes", "foreign_loads",
    "extra_frames", "unattributed_inputs", "unattributed_state_changes",
    "instrument_tampered", "instrument_errors", "ran_after_finish", "isolation_lost",
    "real_frames", "peek_restores",
)
#: Counters that each break purity on their own.
BREACH_COUNTERS = (
    "foreign_presses", "foreign_writes", "foreign_loads",
    "ai_writes", "ai_loads", "ai_unrouted_presses", "ai_bot_calls",
    "extra_frames", "unattributed_inputs", "unattributed_state_changes",
    "instrument_tampered", "instrument_errors", "ran_after_finish", "isolation_lost",
)
#: The exit code of a run that kept going after its verdict was written (= lifecycle.EXIT_PURITY_BREACH;
#: the lifecycle imports this module, so the number is repeated here rather than imported).
EXIT_RAN_AFTER_FINISH = 6
ORIGIN_KINDS = ("presses", "writes", "loads", "frames", "inputs", "memory", "bot", "tamper", "errors", "isolation", "chains")
#: How many bot-code frames a foreign press's chain names (outermost first).
CHAIN_DEPTH = 6
#: How many distinct origins of each kind the verdict file keeps (the most frequent first).
ORIGINS_KEPT = 50
#: After `lifecycle.finish` has written the verdict, the process must be gone within this many
#: seconds: a NON-daemon thread of the framework (its HTTP server runs one) holds the interpreter open
#: at shutdown for ever, which would be a parked process with a verdict that says it ended.
EXIT_WATCHDOG_SECONDS = 20.0
#: When `finish` runs on one thread, how long it waits for a frame ANOTHER thread is in the middle of.
#: A frame takes about a millisecond; a frame stuck in native code longer than this is not waited for.
FRAME_IN_FLIGHT_SECONDS = 5.0
#: How long a frame on a thread other than the finishing one waits for the process to end (longer than
#: `EXIT_WATCHDOG_SECONDS`, so the watchdog always ends a finished process first).
FENCE_SECONDS = 30.0

_PACKAGE_DIR = Path(__file__).resolve().parents[1]
_CONTROLLER_FILE = Path(__file__).resolve().parent / "controller.py"
_LIFECYCLE_FILE = Path(__file__).resolve().parent / "lifecycle.py"
#: The file name every function of THIS module carries (`co_filename`): code with any other file
#: name is not the instrument, and may not set the instrument's attributes.
_OWN_FILE = sys._getframe(0).f_code.co_filename
_MISSING = object()


def _norm(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _key_names(bits: int) -> str:
    names = [name for index, name in enumerate(KEY_NAMES) if bits & (1 << index)]
    return "+".join(names) or f"{bits:#x}"


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _where(frame: FrameType | None) -> str:
    """`ai_player/_plant.py:12 tick` for a frame (paths shown relative to the repo when possible)."""
    if frame is None:
        return "?"
    path = _norm(frame.f_code.co_filename)
    root = _norm(_PACKAGE_DIR.parent) + os.sep
    shown = path[len(root):] if path.startswith(root) else os.path.basename(path)
    return f"{shown.replace(os.sep, '/')}:{frame.f_lineno} {frame.f_code.co_name}"


def _swap_everywhere(old: Callable, new: Callable) -> int:
    """Re-bind every module-level name that refers to `old` so it refers to `new`. Returns how many."""
    swapped = 0
    for module in list(sys.modules.values()):
        if not isinstance(module, ModuleType) or isinstance(module, _SealedModule):
            continue
        try:
            aliases = [attr for attr, value in list(module.__dict__.items()) if value is old]
        except Exception:
            continue  # some lazy or proxy modules refuse introspection; they hold no alias we need
        for attr in aliases:
            setattr(module, attr, new)
            swapped += 1
    return swapped


def _first_difference(old: bytes, new: bytes) -> int:
    """Offset of the first differing byte (the buffers are known to differ). Chunked, so it is fast."""
    chunk = 4096
    for start in range(0, min(len(old), len(new)), chunk):
        if old[start : start + chunk] != new[start : start + chunk]:
            for offset in range(start, min(start + chunk, len(old), len(new))):
                if old[offset] != new[offset]:
                    return offset
    return min(len(old), len(new))


# ---------------------------------------------------------------------------------- the closures
_Registry = namedtuple("_Registry", "bind payload_of add_vault vaults add_sealed sealed own owner_of")
_Vault = namedtuple("_Vault", "add note read snapshot origins_snapshot origins_top breach")


def _make_registry() -> _Registry:
    """WHERE THE INSTRUMENT'S STATE LIVES: in this closure. `Attribution` and `PurityCounters` hold
    nothing themselves; their methods look their state up here by identity. So no attribute of any
    object the AI can hold leads to a counter, a flag or a baseline.

    The registry itself is a module attribute anyone can name, so EVERY function here answers only
    code of this file (round 3): any other caller is refused and counted as `instrument_tampered`
    (`_REGISTRY.payload_of(counters).add("real_frames", None, None, 5)` turned an UNVERIFIED run CLEAN)."""
    payloads: dict[int, tuple[object, object]] = {}
    vaults: list = []
    sealed: list = []
    owners: dict[int, tuple[type, str]] = {}
    own_file = _OWN_FILE  # captured now: rebinding the module's constant later changes nothing here

    def checked(name: str) -> None:
        caller = sys._getframe(2)  # [0] this check, [1] the registry function, [2] whoever called it
        if caller.f_code.co_filename != own_file:
            problem = f"the instrument's registry: {name} was called from {_where(caller)}"
            for vault in vaults:
                vault.add("instrument_tampered", "tamper", problem, 1)
            raise PermissionError(f"only the instrument may use its registry ({name})")

    def bind(owner: object, payload: object) -> None:
        checked("bind")
        if id(owner) in payloads:
            raise RuntimeError("an instrument object can be bound only once")
        payloads[id(owner)] = (owner, payload)  # the owner is kept alive, so its id is never reused

    def payload_of(owner: object):
        checked("payload_of")
        entry = payloads.get(id(owner))
        if entry is None or entry[0] is not owner:
            raise RuntimeError(f"this {type(owner).__name__} was not built by the instrument")
        return entry[1]

    def add_vault(vault: _Vault) -> None:
        checked("add_vault")
        vaults.append(vault)

    def live_vaults() -> tuple:
        checked("vaults")
        return tuple(vaults)

    def add_sealed(entry: tuple) -> None:
        checked("add_sealed")
        sealed.append(entry)

    def sealed_now() -> tuple:
        checked("sealed")
        return tuple(sealed)

    def own(cls: type, filename: str) -> None:
        checked("own")
        if id(cls) not in owners:
            owners[id(cls)] = (cls, filename)  # the class is kept alive, so its id is never reused

    def owner_of(cls: type) -> str | None:
        checked("owner_of")
        entry = owners.get(id(cls))
        return entry[1] if entry is not None and entry[0] is cls else None

    return _Registry(bind, payload_of, add_vault, live_vaults, add_sealed, sealed_now, own, owner_of)


_REGISTRY = _make_registry()


def _make_vault() -> _Vault:
    """THE COUNTS. They live in this closure and nowhere else, and they only GROW: `add` refuses a
    count below 1 (and counts the attempt). The breach list is captured here, at creation, so a
    later rebinding of the module's `BREACH_COUNTERS` cannot make a breach read as clean. `add` and
    `note` answer only code of this file (round 3): a store handed out by any route is still refused."""
    values: dict[str, int] = dict.fromkeys(COUNTER_NAMES, 0)
    origins: dict[str, Counter] = {kind: Counter() for kind in ORIGIN_KINDS}
    breach_names = tuple(BREACH_COUNTERS)
    own_file = _OWN_FILE

    def refuse_outsider(what: str, detail: object) -> None:
        caller = sys._getframe(2)  # [0] this check, [1] add / note, [2] whoever called it
        if caller.f_code.co_filename != own_file:
            values["instrument_tampered"] += 1
            origins["tamper"][f"the counter store's {what}({detail!r}) was called from {_where(caller)}"] += 1
            raise PermissionError("only the instrument counts")

    def add(name: str, kind: str | None, origin: str | None, count: int) -> None:
        refuse_outsider("add", (name, count))
        if type(count) is not int or count < 1:
            values["instrument_tampered"] += 1
            origins["tamper"][f"an attempt to add {count!r} to the counter {name!r} (counts only grow)"] += 1
            raise ValueError(f"the counts only grow: refused to add {count!r} to {name!r}")
        if name not in values:
            raise KeyError(f"no counter named {name!r}")
        values[name] += count
        if kind is not None and origin is not None:
            origins[kind][origin] += count

    def note(kind: str, origin: str) -> None:
        refuse_outsider("note", kind)
        origins[kind][origin] += 1

    def read(name: str) -> int:
        return values[name]

    def snapshot() -> dict[str, int]:
        return dict(values)

    def origins_snapshot() -> dict[str, dict[str, int]]:
        return {kind: dict(counter.most_common(ORIGINS_KEPT)) for kind, counter in origins.items() if counter}

    def origins_top(count: int) -> list[tuple[str, list[tuple[str, int]]]]:
        return [(kind, counter.most_common(count)) for kind, counter in origins.items() if counter]

    def breach() -> bool:
        return any(values[name] for name in breach_names)

    return _Vault(add, note, read, snapshot, origins_snapshot, origins_top, breach)


def _tamper_all(problem: str) -> None:
    """Count a refused attempt on the instrument, in every live counter store (one per process)."""
    for vault in _REGISTRY.vaults():
        vault.add("instrument_tampered", "tamper", problem, 1)


def _force_exit(code: int, waited: bool) -> None:
    """The exit watchdog fired: the verdict is written, but the process is still alive."""
    try:
        if waited:
            print(f"[AI-LIFECYCLE] the process was still alive {EXIT_WATCHDOG_SECONDS:g}s after its verdict (a non-daemon "
                  f"thread held the interpreter open at shutdown); ending it with os._exit({code})", flush=True)
        else:
            print(f"[AI-LIFECYCLE] the run was finished on a thread other than the main thread, where sys.exit cannot "
                  f"end the process; ending it with os._exit({code})", flush=True)
    finally:
        os._exit(code)


# ---------------------------------------------------------------------------------- sealing
class Sealed(type):
    """Metaclass: a class built with it cannot be changed after its definition.

    WHY: the verdict is computed by methods of a few classes. Any code holding an instance can reach
    its class (`type(obj)`) and replace a method there, which would rewrite the verdict without
    touching one counter. Refusing class-level assignment closes that at run time, for every route
    the static gate cannot see. Each refusal is also COUNTED as tampering.

    It also records, when the class is BUILT, the file whose code built it (the frame that ran the
    `class` statement): `Guarded` instances accept attribute writes only from that file."""

    def __init__(cls, name: str, bases: tuple, namespace: dict, **kwargs) -> None:
        super().__init__(name, bases, namespace, **kwargs)
        # [0] this method, [1] the code running the `class` statement (`__build_class__` and
        # `type.__call__` are C functions, so they leave no Python frame in between).
        _REGISTRY.own(cls, sys._getframe(1).f_code.co_filename)

    def __setattr__(cls, name: str, value: object) -> None:
        _tamper_all(f"the class attribute {cls.__name__}.{name} was assigned from {_where(sys._getframe(1))}")
        raise AttributeError(f"{cls.__name__} is sealed: its attribute {name!r} cannot be set")

    def __delattr__(cls, name: str) -> None:
        _tamper_all(f"the class attribute {cls.__name__}.{name} was deleted from {_where(sys._getframe(1))}")
        raise AttributeError(f"{cls.__name__} is sealed: its attribute {name!r} cannot be deleted")


class Guarded(metaclass=Sealed):
    """Base of the objects whose state decides how a run ends: only code in the file that DEFINES the
    instance's class may set or delete their attributes (for the instrument's own objects, THIS file;
    for the lifecycle, `host/lifecycle.py`; and so on). Anything else is refused AND counted (a
    refusal that is not counted cannot be graded). Give subclasses `__slots__`, so there is no
    `__dict__` to write around this."""

    __slots__ = ()

    def __setattr__(self, name: str, value: object) -> None:
        caller = sys._getframe(1)
        if caller.f_code.co_filename != _REGISTRY.owner_of(type(self)):
            _tamper_all(f"{type(self).__name__}.{name} was assigned from {_where(caller)}")
            raise AttributeError(f"{type(self).__name__} is guarded: {name!r} can be set only by its own module")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        caller = sys._getframe(1)
        if caller.f_code.co_filename != _REGISTRY.owner_of(type(self)):
            _tamper_all(f"{type(self).__name__}.{name} was deleted from {_where(caller)}")
            raise AttributeError(f"{type(self).__name__} is guarded: {name!r} can be deleted only by its own module")
        object.__delattr__(self, name)


class _SealedModule(ModuleType):
    """The class a sealed module object gets: its attributes cannot be rebound or deleted from
    outside (the module's own code writes its globals directly, which does not come through here)."""

    def __setattr__(self, name: str, value: object) -> None:
        _tamper_all(f"the module attribute {self.__name__}.{name} was assigned from {_where(sys._getframe(1))}")
        raise AttributeError(f"the module {self.__name__} is sealed: {name!r} cannot be rebound")

    def __delattr__(self, name: str) -> None:
        _tamper_all(f"the module attribute {self.__name__}.{name} was deleted from {_where(sys._getframe(1))}")
        raise AttributeError(f"the module {self.__name__} is sealed: {name!r} cannot be deleted")


def _code_parts(value: object) -> tuple:
    """The objects that make a function do what it does: its code, defaults and keyword defaults."""
    if isinstance(value, (staticmethod, classmethod)):
        value = value.__func__
    if isinstance(value, property):
        return tuple(part for accessor in (value.fget, value.fset, value.fdel) if accessor is not None for part in _code_parts(accessor))
    code = getattr(value, "__code__", None)
    if code is None:
        return ()
    return (value, code, value.__defaults__, value.__kwdefaults__)


def _fingerprint(module: ModuleType) -> list[tuple]:
    """Every (namespace, name, object, code parts) of a module and of the classes it defines.
    Dunder names are left out: the import system and `warnings` add some later on purpose."""
    entries: list[tuple] = []
    namespace = vars(module)
    for name, value in list(namespace.items()):
        if _is_dunder(name):
            continue
        entries.append((namespace, f"{module.__name__}.{name}", name, value, _code_parts(value)))
        if isinstance(value, type) and value.__module__ == module.__name__:
            class_namespace = vars(value)
            for attr, member in list(class_namespace.items()):
                if attr in ("__dict__", "__weakref__", "__doc__"):
                    continue
                entries.append((class_namespace, f"{module.__name__}.{name}.{attr}", attr, member, _code_parts(member)))
    return entries


def _fingerprint_changes(entries: tuple[tuple, ...]) -> list[str]:
    changed = []
    for namespace, label, name, value, parts in entries:
        if namespace.get(name, _MISSING) is not value:
            changed.append(f"{label} was rebound or removed")
        elif parts:
            function, code, defaults, kwdefaults = parts[:4]
            if function.__code__ is not code or function.__defaults__ is not defaults or function.__kwdefaults__ is not kwdefaults:
                changed.append(f"the code or defaults of {label} were replaced")
    return changed


def seal_module(name: str) -> None:
    """Seal the module `name` (called by a host module as its LAST statement, `seal_module(__name__)`):
    its attributes cannot be rebound from outside any more (refused and counted), and its namespace
    and code are fingerprinted now and checked before every real frame. Never seal a PACKAGE: the
    import system sets a package's submodules on it as attributes."""
    module = sys.modules.get(name)
    if module is None:
        raise RuntimeError(f"cannot seal {name!r}: it is not loaded")
    if isinstance(module, _SealedModule):
        return
    entries = tuple(_fingerprint(module))  # a tuple: nothing handed out can shorten the list of checks
    module.__class__ = _SealedModule
    _REGISTRY.add_sealed((name, entries))


# ---------------------------------------------------------------------------------- the objects
class PurityCounters(Guarded):
    """A READ-ONLY view of the counts behind the verdict. It holds nothing: the counts live in the
    instrument's closure. `counters.foreign_presses` reads; `counters.foreign_presses = 0` and
    `counters._anything` are refused and counted; `_add` works only for the instrument's own code."""

    __slots__ = ()

    def __init__(self, vault: _Vault) -> None:
        _REGISTRY.bind(self, vault)

    def __getattr__(self, name: str) -> int:
        # Reached only when normal lookup fails: the counter names, and probes of private storage.
        if name.startswith("_"):
            if not _is_dunder(name):
                _tamper_all(f"something looked up the counters' private {name!r} from {_where(sys._getframe(1))}")
            raise AttributeError(name)
        try:
            return _REGISTRY.payload_of(self).read(name)
        except KeyError:
            raise AttributeError(name) from None

    def _add(self, name: str, kind: str | None = None, origin: str | None = None, count: int = 1) -> None:
        caller = sys._getframe(1)
        if caller.f_code.co_filename != _OWN_FILE:
            _tamper_all(f"PurityCounters._add({name!r}, count={count!r}) was called from {_where(caller)}")
            raise PermissionError("only the instrument counts")
        _REGISTRY.payload_of(self).add(name, kind, origin, count)

    def snapshot(self) -> dict[str, int]:
        return _REGISTRY.payload_of(self).snapshot()

    def origins_snapshot(self) -> dict[str, dict[str, int]]:
        return _REGISTRY.payload_of(self).origins_snapshot()

    def breach(self) -> bool:
        """Purity is broken by ANY foreign action; by the AI writing memory, loading a state, advancing
        a frame, pressing outside its controller or running bot code; by anything reaching the game
        through no door; by the AI's isolation being lost; and by the instrument being tampered with
        or failing."""
        return _REGISTRY.payload_of(self).breach()

    def verdict(self) -> str:
        vault = _REGISTRY.payload_of(self)
        if vault.breach():
            return "BREACH"
        if vault.read("real_frames") == 0:
            return "UNVERIFIED"  # the sink audit never ran, so nothing was measured
        return "CLEAN"

    def purity_line(self) -> str:
        # ‼ The first four fields are the contract other tools parse: keep their order and spelling.
        v = _REGISTRY.payload_of(self).snapshot()
        return (
            f"[AI-PURITY] foreign_presses={v['foreign_presses']} foreign_writes={v['foreign_writes']} "
            f"foreign_loads={v['foreign_loads']} ai_presses={v['ai_presses']} "
            f"ai_writes={v['ai_writes']} ai_loads={v['ai_loads']} ai_bot_calls={v['ai_bot_calls']} "
            f"ai_unrouted_presses={v['ai_unrouted_presses']} extra_frames={v['extra_frames']} "
            f"unattributed_inputs={v['unattributed_inputs']} "
            f"unattributed_state_changes={v['unattributed_state_changes']} "
            f"instrument_tampered={v['instrument_tampered']} instrument_errors={v['instrument_errors']} "
            f"ran_after_finish={v['ran_after_finish']} isolation_lost={v['isolation_lost']} "
            f"real_frames={v['real_frames']} peek_restores={v['peek_restores']} verdict={self.verdict()}"
        )

    def origins_line(self) -> str:
        parts = []
        for kind, top in _REGISTRY.payload_of(self).origins_top(6):
            parts.append(f"{kind}=[" + ", ".join(f"{origin} x{count}" for origin, count in top) + "]")
        return "[AI-PURITY-ORIGINS] " + ("; ".join(parts) if parts else "none")


class _State(Guarded):
    """Everything the instrument changes after it is built. Reached only through `_REGISTRY`."""

    __slots__ = (
        "vault", "counters", "local", "package_prefix", "controller_path", "lifecycle_path", "framework_root",
        "display_roots", "brain_entries", "brain_exceptions", "norm_cache", "brain_cache", "undo",
        "installed_wrappers", "module_wrappers", "tamper_seen", "installed", "finalized", "verdict_written",
        "emulator", "core", "libmgba_path", "main_path", "frame_callback", "callback_ids", "snapshot",
        "ledger_pressed", "ledger_held", "expected_prev", "rtc", "tool", "monitor", "disable", "guard",
        "on_isolation_lost", "isolation_lost_reported", "verdict_path", "verdict_facts", "last_main_frame",
        "frame_lock", "finisher", "finisher_name", "frame_in_flight", "fence_reported",
    )


class Attribution(Guarded):
    """Installs the wrappers and the bot-code monitor, audits the sinks and the isolation, keeps the
    counters, and removes everything when the lifecycle finalizes the audit. Holds nothing itself."""

    __slots__ = ()

    def __init__(self) -> None:
        vault = _make_vault()
        _REGISTRY.add_vault(vault)
        s = _State()
        s.vault = vault
        s.counters = PurityCounters(vault)
        s.local = threading.local()  # per thread: the door nesting depth and the look-ahead depth
        s.package_prefix = _norm(_PACKAGE_DIR) + os.sep
        s.controller_path = _norm(_CONTROLLER_FILE)
        s.lifecycle_path = _norm(_LIFECYCLE_FILE)
        s.framework_root = _norm(Path(framework_memory.__file__).resolve().parents[1])
        s.display_roots = (s.framework_root, _norm(_PACKAGE_DIR.parent))
        s.brain_entries = tuple(os.path.normcase(entry) for entry in BOT_BRAIN_PATHS)
        s.brain_exceptions = frozenset(os.path.normcase(entry) for entry in BOT_BRAIN_EXCEPTIONS)
        s.norm_cache = {}
        s.brain_cache = {}
        s.undo = []
        s.installed_wrappers = []
        s.module_wrappers = []
        s.tamper_seen = set()
        s.installed = False
        s.finalized = False
        s.verdict_written = False
        s.emulator = None
        s.core = None
        s.libmgba_path = ""
        s.main_path = ""
        s.frame_callback = None
        s.callback_ids = {}
        s.snapshot = None
        s.ledger_pressed = 0
        s.ledger_held = 0
        s.expected_prev = 0
        s.rtc = None
        s.tool = None
        s.monitor = None
        s.disable = None
        s.guard = None
        s.on_isolation_lost = None
        s.isolation_lost_reported = False
        s.verdict_path = None
        s.verdict_facts = {}
        s.last_main_frame = None  # `context.frame` at the last audited real frame (continuity check)
        s.frame_lock = threading.RLock()  # held for every frame, and by `finalize_audit` (the frame fence)
        s.finisher = None  # the thread id that runs `lifecycle.finish` (named first thing by finalize_audit)
        s.finisher_name = ""
        s.frame_in_flight = False  # finalize_audit had to wait for a frame another thread was running
        s.fence_reported = False
        _REGISTRY.bind(self, s)

    @property
    def counters(self) -> PurityCounters:
        return _REGISTRY.payload_of(self).counters

    # ------------------------------------------------------------------ install / finalize
    def install(self) -> None:
        s = _REGISTRY.payload_of(self)
        if s.installed or s.finalized:
            raise RuntimeError("attribution is already installed (or already finalized)")
        emulator = context.emulator
        if emulator is None:
            raise RuntimeError("no emulator: the AI mode started before the framework created one")
        s.emulator = emulator
        s.core = emulator._core
        s.libmgba_path = self._path(type(emulator).run_single_frame.__code__.co_filename)
        s.main_path = _norm(Path(s.libmgba_path).with_name("main.py"))
        s.frame_callback = emulator._on_frame_callback

        for name in EMULATOR_INPUT_METHODS:
            self._wrap_method(emulator, "emulator", name, self._make_wrapper("presses", name, getattr(emulator, name)))
        for name in EMULATOR_WRITE_METHODS:
            self._wrap_method(emulator, "emulator", name, self._make_wrapper("writes", name, getattr(emulator, name)))
        for name in EMULATOR_LOAD_METHODS:
            self._wrap_method(emulator, "emulator", name, self._make_wrapper("loads", name, getattr(emulator, name)))
        self._wrap_method(emulator, "emulator", "peek_frame", self._make_peek_wrapper(emulator.peek_frame))
        for name in CORE_LOAD_METHODS:
            self._wrap_method(s.core, "core", name, self._make_wrapper("loads", name, getattr(s.core, name)))
        for name in CORE_FRAME_METHODS:
            self._wrap_method(s.core, "core", name, self._make_wrapper("frames", name, getattr(s.core, name)))
        clock = s.core.rtc
        for name in RTC_METHODS:
            self._wrap_method(clock, "rtc", name, self._make_wrapper("writes", name, getattr(clock, name)))
        self._wrap_method(s.core, "core", "run_frame", self._make_run_frame_wrapper(s.core.run_frame), keep=True)
        for name in MEMORY_FUNCTIONS:
            self._wrap_module_function(name)

        callbacks = s.core._callbacks
        for list_name in CORE_CALLBACK_LISTS:
            entries = getattr(callbacks, list_name, None)
            s.callback_ids[list_name] = [id(entry) for entry in entries] if isinstance(entries, list) else None
        self._install_monitor()
        # Inputs already held when the AI takes over were set by nobody the AI can name: they stay
        # OUT of the ledger, so if they reach a frame they count as unattributed.
        s.ledger_pressed = 0
        s.ledger_held = 0
        s.expected_prev = emulator._prev_pressed_inputs
        s.rtc = self._rtc_reading()
        s.snapshot = self._memory_snapshot()
        # The session installs this from the hook's constructor, inside main-loop pass `context.frame`
        # and BEFORE that pass's frame: so that frame is the first one the audit must see.
        s.last_main_frame = context.frame - 1
        s.installed = True

    def watch_guard(self, guard: object, on_lost: Callable[[], None] | None) -> None:
        """Before every real frame, check that `guard` (the AI's GuardListener) is in
        `context.bot_listeners`; if it is not, count `isolation_lost` and call `on_lost` (the session
        ends the run there). Only the session may name this (gate rule g); a second call is refused."""
        s = _REGISTRY.payload_of(self)
        if s.guard is not None:
            self.note_tamper(f"watch_guard was called a second time, from {_where(sys._getframe(1))}")
            return
        s.guard = guard
        s.on_isolation_lost = on_lost

    def finalize_audit(self) -> PurityCounters:
        """The last instrument check, then every wrapper and the monitor come off. Only
        `lifecycle.finish` may call this: from anywhere else it is counted as tampering and refused."""
        s = _REGISTRY.payload_of(self)
        caller = sys._getframe(1)
        if not self._is_lifecycle_finish(caller):
            self.note_tamper(f"finalize_audit was called by {self._describe(caller, 'finalize_audit')}, not by lifecycle.finish")
            return s.counters
        held = self._fence_frames()
        try:
            self._finalize()
        finally:
            if held:
                s.frame_lock.release()
        return s.counters

    def _fence_frames(self) -> bool:
        """THE FRAME FENCE, closed by the finish (see the module docstring). Names this thread as the
        finishing one FIRST (from here on a frame on any other thread waits for the process to end),
        then waits, bounded, for a frame another thread is in the middle of. Returns True when this
        thread now holds the frame lock (the caller releases it after the final audit)."""
        s = _REGISTRY.payload_of(self)
        if s.finisher is None:
            s.finisher = threading.get_ident()
            s.finisher_name = threading.current_thread().name
        if s.frame_lock.acquire(blocking=False):
            return True
        s.frame_in_flight = True
        return s.frame_lock.acquire(timeout=FRAME_IN_FLIGHT_SECONDS)

    def _fenced_out(self) -> bool:
        """Is ANOTHER thread finishing the run? Then this thread may not run a frame."""
        finisher = _REGISTRY.payload_of(self).finisher
        return finisher is not None and finisher != threading.get_ident()

    def _enter_frame(self) -> bool:
        """Take the frame lock for one frame. False (and the lock NOT held) when another thread is
        finishing the run, including when the finish began while this thread waited for the lock."""
        s = _REGISTRY.payload_of(self)
        if self._fenced_out():
            return False
        if not s.frame_lock.acquire(timeout=FENCE_SECONDS):
            return False
        if self._fenced_out():
            s.frame_lock.release()
            return False
        return True

    def _wait_for_the_end(self, caller: FrameType, kind: str) -> None:
        """A frame on a thread other than the finishing one. The verdict accounts for every frame up to
        the finish, so this one must not run; and it is not the run playing on after its verdict (what
        the tripwire is for), only a main thread that woke up late. It waits for the process to end:
        the exit watchdog ends it at once when `finish` ran off the main thread. If the process is
        still alive `FENCE_SECONDS` later, nothing is ending it, and the tripwire ends it as a BREACH."""
        s = _REGISTRY.payload_of(self)
        if not s.fence_reported:
            s.fence_reported = True
            try:
                print(f"[AI-LIFECYCLE] the run is being finished on thread {s.finisher_name!r}: a {kind} frame on thread "
                      f"{threading.current_thread().name!r} ({self._describe(caller, 'run_frame')}) waits for the process "
                      f"to end instead of running", flush=True)
            except Exception:
                pass
        time.sleep(FENCE_SECONDS)
        self._ran_after_finish(
            caller,
            f"a {kind} frame waited {FENCE_SECONDS:g}s for the process to end after thread {s.finisher_name!r} "
            f"finished the run ({self._describe(caller, 'run_frame')}), and it did not end",
        )

    def write_verdict_file(self, path: Path | None, facts: dict[str, object]) -> str:
        """Write `path` (the run's purity.json) ONCE, from this module's own counters. Only
        `lifecycle.finish` may call this. Returns a log line saying what happened."""
        s = _REGISTRY.payload_of(self)
        caller = sys._getframe(1)
        if not self._is_lifecycle_finish(caller):
            self.note_tamper(f"write_verdict_file was called by {self._describe(caller, 'write_verdict_file')}, not by lifecycle.finish")
            return "[AI-LIFECYCLE] verdict file: REFUSED (wrong caller)"
        self._finalize()
        if s.verdict_written:
            return "[AI-LIFECYCLE] verdict file: already written; not written again"
        s.verdict_written = True
        s.verdict_path = path
        s.verdict_facts = {str(key): value for key, value in facts.items()}
        if path is None:
            return "[AI-LIFECYCLE] verdict file: none (no run_dir; a run started by hand prints its verdict only)"
        return self._write_verdict()

    def arm_exit_watchdog(self, code: int) -> None:
        """Only `lifecycle.finish` may call this, right before its `sys.exit(code)`: a DAEMON timer
        ends the process with `os._exit(code)` if it is still alive `EXIT_WATCHDOG_SECONDS` later.
        WHY: the interpreter waits for every non-daemon thread before it exits, and the framework
        starts some (its HTTP server's thread never ends), so a finished run could otherwise sit in
        shutdown for ever: a park. Daemon threads keep running during that wait, so the timer fires.
        On any thread but the main thread `sys.exit` ends only that thread, never the process, so
        there the timer fires at once."""
        caller = sys._getframe(1)
        if not self._is_lifecycle_finish(caller):
            self.note_tamper(f"arm_exit_watchdog was called by {self._describe(caller, 'arm_exit_watchdog')}, not by lifecycle.finish")
            return
        on_main_thread = threading.current_thread() is threading.main_thread()
        delay = EXIT_WATCHDOG_SECONDS if on_main_thread else 0.0
        timer = threading.Timer(delay, _force_exit, args=(int(code), on_main_thread))
        timer.daemon = True
        timer.start()

    def _write_verdict(self) -> str:
        s = _REGISTRY.payload_of(self)
        path = s.verdict_path
        if path is None:
            return "[AI-LIFECYCLE] verdict file: none"
        payload = {
            "written_by": "ai_player/host/attribution.py Attribution.write_verdict_file",
            "pid": os.getpid(),
            "verdict": s.counters.verdict(),
            "counters": s.vault.snapshot(),
            "origins": s.vault.origins_snapshot(),
            "facts": s.verdict_facts,
            "finish": {
                "thread": s.finisher_name,
                "main_thread": s.finisher_name == threading.main_thread().name,
                "frame_in_flight": s.frame_in_flight,
            },
        }
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        except OSError as error:
            return f"[AI-LIFECYCLE] verdict file: FAILED to write {path}: {error}"
        return f"[AI-LIFECYCLE] verdict file written: {path}"

    def _finalize(self) -> None:
        """The last look while the wrappers are still on, then everything comes off EXCEPT the
        `run_frame` wrapper, which stays as a tripwire (`_ran_after_finish`)."""
        s = _REGISTRY.payload_of(self)
        if s.finalized:
            return
        try:
            self.audit_instrument()
        except Exception as error:
            self._instrument_error("the last instrument audit", error)
        try:
            if s.installed:
                self._check_continuity(final=True)
        except Exception as error:
            self._instrument_error("the last frame-continuity check", error)
        s.finalized = True
        self._uninstall()

    def _ran_after_finish(self, caller: FrameType, why: str | None = None) -> None:
        """A REAL frame after the verdict was written. `finish` ends with sys.exit, which leaves no
        frame to run, so something caught that SystemExit and kept playing while every counter was
        off. The verdict is rewritten as BREACH and the process ends at once (`os._exit`: a second
        SystemExit could be caught the same way). Also the frame fence's last resort (`why`)."""
        s = _REGISTRY.payload_of(self)
        s.vault.add(
            "ran_after_finish", "tamper",
            why or (f"a real frame ran after the verdict was written ({self._describe(caller, 'run_frame')}): "
                    f"something caught the lifecycle's SystemExit"), 1,
        )
        s.verdict_facts = {
            **s.verdict_facts,
            "exit_reason": "ran-after-finish",
            "exit_code": EXIT_RAN_AFTER_FINISH,
            "first_ending": {k: s.verdict_facts.get(k) for k in ("exit_reason", "exit_code")},
        }
        line = self._write_verdict()
        try:
            print(f"[AI-LIFECYCLE] the run kept playing after its verdict was written: verdict rewritten as "
                  f"{s.counters.verdict()} ({line})", flush=True)
            print(s.counters.purity_line(), flush=True)
            print(f"[AI-EXIT] reason=ran-after-finish code={EXIT_RAN_AFTER_FINISH}", flush=True)
        finally:
            os._exit(EXIT_RAN_AFTER_FINISH)

    def _uninstall(self) -> None:
        s = _REGISTRY.payload_of(self)
        while s.undo:
            undo = s.undo.pop()
            try:
                undo()
            except Exception as error:
                self._instrument_error("uninstalling", error)
        s.installed = False

    def _is_lifecycle_finish(self, frame: FrameType) -> bool:
        s = _REGISTRY.payload_of(self)
        return self._path(frame.f_code.co_filename) == s.lifecycle_path and frame.f_code.co_name == "finish"

    def _wrap_method(self, owner: object, label: str, name: str, wrapper: Callable, keep: bool = False) -> None:
        """Install `wrapper` as `owner.name`. `keep`: never undo it (the run_frame tripwire must
        outlive the audit; the process ends right after the lifecycle's finish anyway)."""
        s = _REGISTRY.payload_of(self)
        had_instance_attribute = name in vars(owner)
        original = vars(owner).get(name)
        setattr(owner, name, wrapper)
        s.installed_wrappers.append((owner, name, wrapper, label))
        if keep:
            return

        def undo() -> None:
            if had_instance_attribute:
                setattr(owner, name, original)
            else:
                delattr(owner, name)

        s.undo.append(undo)

    def _wrap_module_function(self, name: str) -> None:
        """Wrap a `modules.memory` function AND every module-level alias of it.

        WHY the sweep: `from modules.memory import write_symbol` copies the function into the
        importing module, so wrapping only `modules.memory` would miss it. (The emulator-level
        `write_bytes` wrapper would still catch the write itself; the sweep keeps the LABEL right.)
        The undo sweeps again, because a module first imported WHILE the AI ran copied the wrapper,
        not the original.
        """
        s = _REGISTRY.payload_of(self)
        original = getattr(framework_memory, name)
        wrapper = self._make_wrapper("writes", name, original)
        _swap_everywhere(original, wrapper)
        s.module_wrappers.append((name, wrapper))
        s.undo.append(lambda: _swap_everywhere(wrapper, original))

    # ------------------------------------------------------------------ layer 1: the doors
    def _make_wrapper(self, kind: str, name: str, original: Callable) -> Callable:
        s = _REGISTRY.payload_of(self)  # held by the closure, not by any attribute
        local = s.local

        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            depth = getattr(local, "depth", 0)
            outermost = depth == 0
            state_change = False
            inputs_before = self._input_state() if kind == "presses" else None
            if outermost:
                try:
                    state_change = self._record(kind, name, args, inputs_before, sys._getframe(1))
                except Exception as error:
                    self._instrument_error(f"recording {name}", error)
                    state_change = kind != "presses"
            local.depth = depth + 1
            try:
                return original(*args, **kwargs)
            finally:
                local.depth = depth
                try:
                    if inputs_before is not None:
                        self._update_ledger(inputs_before)
                    elif state_change and s.installed:
                        # A COUNTED write or load changed memory or the clock on purpose: it is
                        # already in the counters, so the between-frames audit starts again here.
                        s.snapshot = self._memory_snapshot()
                        s.rtc = self._rtc_reading()
                except Exception as error:
                    self._instrument_error(f"after {name}", error)

        return wrapper

    def _make_peek_wrapper(self, original: Callable) -> Callable:
        """`peek_frame` is a context manager; frames run inside it are look-ahead, not play. The depth
        is PER THREAD: a look-ahead in one thread must not make another thread's frame look-ahead."""
        local = _REGISTRY.payload_of(self).local

        @contextlib.contextmanager
        def peek_frame(*args, **kwargs):
            local.peek = getattr(local, "peek", 0) + 1
            try:
                with original(*args, **kwargs) as value:
                    yield value
            finally:
                local.peek = getattr(local, "peek", 1) - 1

        return peek_frame

    def _input_state(self) -> tuple[int, int, int]:
        emulator = _REGISTRY.payload_of(self).emulator
        return emulator._pressed_inputs, emulator._held_inputs, emulator._prev_pressed_inputs

    def _update_ledger(self, before: tuple[int, int, int]) -> None:
        """Only bits that THIS door call turned on are covered; bits that were already on (set by
        nobody the instrument saw) stay uncovered, so they show up at the sink."""
        s = _REGISTRY.payload_of(self)
        pressed_before, held_before, _ = before
        pressed_after, held_after, _ = self._input_state()
        s.ledger_pressed |= pressed_after & ~pressed_before
        s.ledger_held = (s.ledger_held & held_after) | (held_after & ~held_before)

    def _record(self, kind: str, name: str, args: tuple, inputs_before, caller: FrameType) -> bool:
        """Count one outermost door call. Returns True when it was a counted state change (a write,
        a load or a frame advance), after which the memory and clock baselines are taken again."""
        counters = _REGISTRY.payload_of(self).counters
        if kind == "presses":
            if name == "restore_held_buttons" and not (args and args[0]):
                return False  # restoring "nothing held" presses nothing
            if name == "reset_held_buttons" and not (inputs_before and inputs_before[1]):
                return False  # releasing when nothing is held changes nothing
        if kind == "loads" and self._peek_restore(caller):
            counters._add("peek_restores")
            return False
        is_ai, via_controller = self._classify(caller)
        origin = self._describe(caller, name)
        if kind == "presses":
            if is_ai:
                counters._add("ai_presses")
                if not via_controller:
                    counters._add("ai_unrouted_presses", "presses", "AI-UNROUTED " + origin)
            else:
                counters._add("foreign_presses", "presses", origin)
                chain = self._brain_chain(caller)
                if chain:
                    _REGISTRY.payload_of(self).vault.note("chains", chain)
            return False
        if kind == "frames":
            counters._add("extra_frames", "frames", ("AI " if is_ai else "") + origin)
            return True
        if kind == "writes":
            if is_ai:
                counters._add("ai_writes", "writes", "AI " + origin)
            else:
                counters._add("foreign_writes", "writes", origin)
            return True
        if is_ai:
            counters._add("ai_loads", "loads", "AI " + origin)
        else:
            counters._add("foreign_loads", "loads", origin)
        return True

    def _peek_restore(self, caller: FrameType) -> bool:
        s = _REGISTRY.payload_of(self)
        return self._path(caller.f_code.co_filename) == s.libmgba_path and caller.f_code.co_name in PEEK_RESTORERS

    # ------------------------------------------------------------------ layer 2: the sinks
    def _make_run_frame_wrapper(self, original: Callable) -> Callable:
        s = _REGISTRY.payload_of(self)

        @functools.wraps(original)
        def run_frame(*args, **kwargs):
            caller = sys._getframe(1)
            kind = self._frame_kind(caller)
            if not self._enter_frame():
                # Another thread is finishing the run (the frame fence): this frame never runs.
                self._wait_for_the_end(caller, kind)
            try:
                if s.finalized:
                    # After the verdict only the framework's shutdown may run frames, and those are
                    # look-ahead (its screenshot for the state file). A REAL frame means play went on.
                    if kind == "real" and s.verdict_written:
                        self._ran_after_finish(caller)
                    return original(*args, **kwargs)
                if kind == "look-ahead":
                    return original(*args, **kwargs)
                lost = False
                try:
                    lost = self._audit_before_frame(kind, caller)
                except Exception as error:
                    self._instrument_error("auditing a frame", error)
                if lost and s.on_isolation_lost is not None and not s.isolation_lost_reported:
                    s.isolation_lost_reported = True
                    s.on_isolation_lost()  # the session ends the run here, BEFORE this frame runs
                result = original(*args, **kwargs)
                try:
                    if kind == "real":
                        s.ledger_pressed = 0  # run_single_frame clears `_pressed_inputs` next...
                        s.expected_prev = s.emulator._pressed_inputs  # ...after copying it to `_prev_pressed_inputs`
                    s.snapshot = self._memory_snapshot()
                except Exception as error:
                    self._instrument_error("after a frame", error)
                return result
            finally:
                s.frame_lock.release()

        return run_frame

    def _frame_kind(self, caller: FrameType) -> str:
        s = _REGISTRY.payload_of(self)
        main_loop = self._is_main_loop_frame(caller)
        # The MAIN LOOP's frame is play, whatever else is open: a look-ahead never runs through
        # `main_loop -> run_single_frame`. (Checked first since a verifier held a peek_frame open
        # on the main thread and every later main-loop frame went unaudited as a "look-ahead".)
        if main_loop:
            return "real"
        if getattr(s.local, "peek", 0) > 0:
            return "look-ahead"
        if self._path(caller.f_code.co_filename) == s.libmgba_path and caller.f_code.co_name in LOOK_AHEAD_FUNCTIONS:
            return "look-ahead"
        return "extra"  # fail-closed: anything not placed as real or look-ahead is a breach

    def _is_main_loop_frame(self, caller: FrameType) -> bool:
        """Is this `run_frame` call the emulator's `run_single_frame`, called by main.py's `main_loop`?"""
        s = _REGISTRY.payload_of(self)
        if caller.f_code.co_name != "run_single_frame" or self._path(caller.f_code.co_filename) != s.libmgba_path:
            return False
        outer = caller.f_back
        return outer is not None and outer.f_code.co_name == "main_loop" and self._path(outer.f_code.co_filename) == s.main_path

    def _check_continuity(self, final: bool) -> None:
        """Did the audit see every frame the main loop ran? `context.frame` goes up by one per pass of
        main.py's loop (one frame each), so between two audited real frames it must go up by exactly
        one, and from the last audited frame to the finish by at most one (the finish runs inside a
        pass, before or during that pass's frame). Each main-loop frame that ran unaudited is counted."""
        s = _REGISTRY.payload_of(self)
        last = s.last_main_frame
        if last is None:
            return
        now = context.frame
        gap = now - last - 1
        if gap > 0:
            s.counters._add(
                "instrument_tampered", "tamper",
                "main-loop frames ran without a sink audit (context.frame advanced past the last audited real frame)",
                gap,
            )
        elif gap < 0 and not (final and gap == -1):
            self.note_tamper(f"context.frame went from {last} to {now} between two audited real frames (it should rise by one)")
        if not final:
            s.last_main_frame = now

    def _audit_before_frame(self, kind: str, caller: FrameType) -> bool:
        """The sink audit. Returns True when the AI's isolation is lost (the caller ends the run)."""
        s = _REGISTRY.payload_of(self)
        counters = s.counters
        lost = False
        if kind == "extra":
            is_ai, _ = self._classify(caller)
            counters._add("extra_frames", "frames", ("AI " if is_ai else "") + self._describe(caller, "run_frame"))
        else:
            counters._add("real_frames")
            self._check_continuity(final=False)
            if getattr(s.local, "peek", 0) > 0:
                self.note_tamper(
                    "a look-ahead (peek_frame) was still open on this thread when a real frame ran: it never "
                    "restored the state, and frames inside it are not audited"
                )
            self.audit_instrument()
            lost = self._guard_missing()
            prev = s.emulator._prev_pressed_inputs
            if prev != s.expected_prev:
                counters._add(
                    "unattributed_inputs", "inputs",
                    f"the emulator's _prev_pressed_inputs changed between frames ({_key_names(s.expected_prev) if s.expected_prev else 'none'} "
                    f"-> {_key_names(prev)}): it decides what the next press does",
                )
                s.expected_prev = prev
        if s.snapshot is not None:
            now = self._memory_snapshot()
            if now != s.snapshot:
                counters._add("unattributed_state_changes", "memory", self._describe_change(s.snapshot, now))
        elif s.installed:
            self.note_tamper("the memory baseline was cleared while the audit was installed")
        clock = self._rtc_reading()
        if clock != s.rtc:
            counters._add(
                "unattributed_state_changes", "memory",
                f"the game clock (RTC) changed with no counted door: override/value {s.rtc} -> {clock}",
            )
            s.rtc = clock
        latched = s.emulator.get_inputs()
        stray = latched & ~(s.ledger_pressed | s.ledger_held)
        if stray:
            counters._add("unattributed_inputs", "inputs", f"{_key_names(stray)} latched with no counted press or hold")
        return lost

    def _guard_missing(self) -> bool:
        s = _REGISTRY.payload_of(self)
        guard = s.guard
        if guard is None:
            return False
        listeners = context.bot_listeners
        if any(listener is guard for listener in listeners):
            return False
        names = ",".join(type(listener).__name__ for listener in listeners)
        s.counters._add(
            "isolation_lost", "isolation",
            f"a real frame was about to run without the AI's guard in context.bot_listeners "
            f"(n={len(listeners)} types=[{names}]): the framework rebuilt or replaced its listeners",
        )
        return True

    def _memory_snapshot(self) -> tuple[bytes, bytes]:
        memory = _REGISTRY.payload_of(self).core._native.memory
        return (
            bytes(ffi.buffer(ffi.cast("char*", memory.wram), WRAM_SIZE)),
            bytes(ffi.buffer(ffi.cast("char*", memory.iwram), IWRAM_SIZE)),
        )

    def _rtc_reading(self) -> tuple[int, int]:
        """The game clock's native setting: how mGBA answers the game when it asks for the time."""
        native = _REGISTRY.payload_of(self).core._core.rtc
        return int(native.override), int(native.value)

    @staticmethod
    def _describe_change(old: tuple[bytes, bytes], new: tuple[bytes, bytes]) -> str:
        parts = []
        for region, base, before, after in (("WRAM", 0x02000000, old[0], new[0]), ("IWRAM", 0x03000000, old[1], new[1])):
            if before != after:
                parts.append(f"{region} first at {base + _first_difference(before, after):#010x}")
        return "memory changed between frames, " + ", ".join(parts)

    # ------------------------------------------------------------------ layer 3: bot code
    def _install_monitor(self) -> None:
        """Register the PY_START hook. Fails (and so ends the run as a crash) if no tool id is free:
        a run in which bot code could not be watched must not report CLEAN."""
        s = _REGISTRY.payload_of(self)
        monitoring = sys.monitoring
        tool = next((tool for tool in MONITORING_TOOL_IDS if monitoring.get_tool(tool) is None), None)
        if tool is None:
            raise RuntimeError(f"no free sys.monitoring tool id among {MONITORING_TOOL_IDS}: bot code cannot be watched")
        monitoring.use_tool_id(tool, MONITORING_TOOL_NAME)
        s.tool = tool
        s.disable = monitoring.DISABLE
        s.monitor = self._on_code_start  # one bound method, kept, so the audit can check identity
        monitoring.register_callback(tool, monitoring.events.PY_START, s.monitor)
        monitoring.set_events(tool, monitoring.events.PY_START)

        def undo() -> None:
            monitoring.set_events(tool, 0)
            monitoring.register_callback(tool, monitoring.events.PY_START, None)
            monitoring.free_tool_id(tool)

        s.undo.append(undo)

    def _is_brain_file(self, filename: str) -> bool:
        # Everything is compared in normcase form (on Windows: lower case, backslashes), so the
        # lists' "/" become os.sep here and a folder entry is one that ends with os.sep.
        s = _REGISTRY.payload_of(self)
        path = self._path(filename)
        root = s.framework_root + os.sep
        if not path.startswith(root):
            return False
        relative = path[len(root):]
        if relative in s.brain_exceptions:
            return False
        return any(relative == entry or (entry.endswith(os.sep) and relative.startswith(entry)) for entry in s.brain_entries)

    def _on_code_start(self, code, instruction_offset):
        """PY_START callback: is this the bot's decision code, started on the AI's behalf?"""
        s = _REGISTRY.payload_of(self)
        try:
            filename = code.co_filename
            brain = s.brain_cache.get(filename)
            if brain is None:
                brain = self._is_brain_file(filename)
                s.brain_cache[filename] = brain
            if not brain:
                return s.disable  # never asked again for this function
            frame = sys._getframe(1).f_back  # [0] this callback, [1] the bot function, then its callers
            while frame is not None:
                if self._path(frame.f_code.co_filename).startswith(s.package_prefix):
                    shown = self._shown(filename)
                    s.counters._add("ai_bot_calls", "bot", self._describe(frame, f"{shown}:{code.co_name}"))
                    break
                frame = frame.f_back
        except Exception as error:
            self._instrument_error("watching bot code", error)
        return None

    def _brain_chain(self, caller: FrameType) -> str:
        """The bot-code functions on the stack of a foreign action, outermost first: the PATH that
        acted (`modules/modes/_listeners.py:BattleListener.fight > ...`), not only its last line."""
        names: list[str] = []
        frame: FrameType | None = caller
        while frame is not None:
            if self._is_brain_file(frame.f_code.co_filename):
                names.append(f"{self._shown(frame.f_code.co_filename)}:{frame.f_code.co_qualname}")
            frame = frame.f_back
        names.reverse()
        return " > ".join(names[:CHAIN_DEPTH])

    # ------------------------------------------------------------------ the instrument checks itself
    def audit_instrument(self) -> None:
        """Count every way the instrument could have been switched off or bypassed since install."""
        s = _REGISTRY.payload_of(self)
        if not s.installed:
            return
        for owner, name, wrapper, label in s.installed_wrappers:
            if vars(owner).get(name) is not wrapper:
                self.note_tamper(f"the {label}.{name} wrapper was removed or replaced")
        for name, wrapper in s.module_wrappers:
            if getattr(framework_memory, name, None) is not wrapper:
                self.note_tamper(f"the modules.memory.{name} wrapper was removed or replaced")
        callbacks = s.core._callbacks
        for list_name, ids in s.callback_ids.items():
            entries = getattr(callbacks, list_name, None)
            now = [id(entry) for entry in entries] if isinstance(entries, list) else None
            if now != ids:
                self.note_tamper(f"the core's {list_name} callback list changed (it runs inside the frame)")
        if s.emulator._on_frame_callback is not s.frame_callback:
            self.note_tamper("the emulator's frame callback was replaced")
        if context.emulator is not s.emulator:
            self.note_tamper("context.emulator is no longer the emulator the AI started with")
        for module_name, entries in _REGISTRY.sealed():
            for change in _fingerprint_changes(entries):
                self.note_tamper(f"the sealed module {module_name}: {change}")
        if s.tool is not None:
            monitoring = sys.monitoring
            if monitoring.get_tool(s.tool) != MONITORING_TOOL_NAME:
                self.note_tamper("the bot-code monitor's sys.monitoring tool id was freed or taken")
            elif monitoring.get_events(s.tool) != monitoring.events.PY_START:
                self.note_tamper("the bot-code monitor's sys.monitoring events were changed")
            else:
                previous = monitoring.register_callback(s.tool, monitoring.events.PY_START, s.monitor)
                if previous is not s.monitor:
                    self.note_tamper("the bot-code monitor's callback was replaced")

    def note_tamper(self, problem: str) -> None:
        """Count a distinct tampering problem once (it is re-detected on every frame)."""
        s = _REGISTRY.payload_of(self)
        if problem in s.tamper_seen:
            return
        s.tamper_seen.add(problem)
        s.counters._add("instrument_tampered", "tamper", problem)

    def note_error(self, where: str, error: BaseException) -> None:
        """Count a failure of the audit itself (for the lifecycle, which has no access to the counts)."""
        self._instrument_error(where, error)

    def _instrument_error(self, where: str, error: BaseException) -> None:
        _REGISTRY.payload_of(self).counters._add("instrument_errors", "errors", f"{where}: {type(error).__name__}: {error}")

    # ------------------------------------------------------------------ origin of a call
    def _path(self, filename: str) -> str:
        cache = _REGISTRY.payload_of(self).norm_cache
        cached = cache.get(filename)
        if cached is None:
            cached = _norm(filename)
            cache[filename] = cached
        return cached

    def _classify(self, caller: FrameType) -> tuple[bool, bool]:
        """(is it the AI's?, did it come straight from the controller?). Only the IMMEDIATE caller
        counts as routing: bot code called from AI code is the AI's, and unrouted."""
        s = _REGISTRY.payload_of(self)
        via_controller = self._path(caller.f_code.co_filename) == s.controller_path
        frame: FrameType | None = caller
        while frame is not None:
            if self._path(frame.f_code.co_filename).startswith(s.package_prefix):
                return True, via_controller
            frame = frame.f_back
        return False, False

    def _shown(self, filename: str) -> str:
        path = self._path(filename)
        for root in _REGISTRY.payload_of(self).display_roots:
            if path.startswith(root + os.sep):
                return path[len(root) + 1 :].replace(os.sep, "/")
        return path.replace(os.sep, "/")

    def _describe(self, caller: FrameType, name: str) -> str:
        return f"{self._shown(caller.f_code.co_filename)}:{caller.f_lineno} {caller.f_code.co_name}->{name}"


seal_module(__name__)
