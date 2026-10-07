"""Who pressed it? Who wrote it? Did bot code run for the AI? Counts every input, memory write, state
load, frame and bot-code call by ORIGIN, audits the emulator's SINKS, and writes the verdict file.

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
             copied them with `from modules.memory import ...`)
     loads   emulator.load_save_state / load_save_game / reset; the mGBA core's load_state,
             load_state_slot, load_save, load_temporary_save, load_raw_state, load_patch, reset
     frames  the core's step / run_loop (a frame advance outside the main loop)
   Origin = AI when any frame on the Python stack belongs to the `ai_player` package, else FOREIGN.
   An AI input counts as routed only when `platform/controller.py` is its IMMEDIATE caller, so bot
   code called from AI code cannot borrow the controller's name. Nested calls (write_symbol ->
   write_bytes) are counted once, at the outermost wrapper.

2. SINKS, audited by a wrapper on the core's `run_frame`, i.e. right before the CPU runs a frame:
     frames   a frame is REAL when the main loop runs it (`modules/main.py main_loop` ->
              `run_single_frame`), a LOOK-AHEAD inside `peek_frame` / `get_screenshot` /
              `get_task_look_ahead` (those restore the state afterwards), and EXTRA otherwise.
     inputs   every key LATCHED into the core for the frame (`get_inputs()`) must have been set by a
              counted input door since the last frame, else `unattributed_inputs`.
     memory   WRAM and IWRAM must be byte-identical from the end of one frame to the start of the
              next, unless a counted write or load ran in between, else `unattributed_state_changes`.
     instrument  before every real frame and at exit: every wrapper still installed, the core's
              callback lists and the emulator's frame callback unchanged, `context.emulator` the
              same object, the bot-code monitor still registered. Else `instrument_tampered`.

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
other caller is counted as tampering and refused). The classes here are SEALED (no method or class
attribute can be replaced after definition) and use `__slots__` (no instance attribute can shadow a
method), and the counters are read-only outside this module, so the AI's own code cannot rewrite the
numbers the file reports. After the file is written, the `run_frame` wrapper stays on as a TRIPWIRE:
`finish` ends with `sys.exit`, so no real frame should ever run again; if one does, something caught
that SystemExit and kept playing with every counter off, so the file is rewritten as BREACH
(`ran_after_finish`) and the process is ended with `os._exit`.

RESIDUAL BLIND SPOTS (so nobody over-reads a CLEAN): the memory sink snapshots WRAM and IWRAM, which
hold all of the game's variables, but not the CPU registers, the I/O registers, video memory or the
cartridge save; a change made ONLY there through a native call is invisible here. The bot-code
monitor sees bot code that RUNS, not bot DATA read without calling a function (a constant table);
that is the static gate's job (rule a). A run killed by the launcher's hard wall clock writes no
verdict file at all (the launcher says so).

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
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import FrameType, ModuleType

import modules.memory as framework_memory
from mgba import ffi
from modules.context import context

__all__ = ["Attribution", "PurityCounters", "Sealed"]

#: Emulator methods that change the buttons. press/hold/release count as input actions; the two
#: bulk methods count only when they actually change something.
EMULATOR_INPUT_METHODS = ("press_button", "hold_button", "release_button", "restore_held_buttons", "reset_held_buttons")
EMULATOR_WRITE_METHODS = ("write_bytes",)
EMULATOR_LOAD_METHODS = ("load_save_state", "load_save_game", "reset")
CORE_LOAD_METHODS = ("load_state", "load_state_slot", "load_save", "load_temporary_save", "load_raw_state", "load_patch", "reset")
CORE_FRAME_METHODS = ("step", "run_loop")
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
    "instrument_tampered", "instrument_errors", "ran_after_finish", "real_frames", "peek_restores",
)
#: Counters that each break purity on their own.
BREACH_COUNTERS = (
    "foreign_presses", "foreign_writes", "foreign_loads",
    "ai_writes", "ai_loads", "ai_unrouted_presses", "ai_bot_calls",
    "extra_frames", "unattributed_inputs", "unattributed_state_changes",
    "instrument_tampered", "instrument_errors", "ran_after_finish",
)
#: The exit code of a run that kept going after its verdict was written (= lifecycle.EXIT_PURITY_BREACH;
#: the lifecycle imports this module, so the number is repeated here rather than imported).
EXIT_RAN_AFTER_FINISH = 6
ORIGIN_KINDS = ("presses", "writes", "loads", "frames", "inputs", "memory", "bot", "tamper", "errors")

_PACKAGE_DIR = Path(__file__).resolve().parents[1]
_CONTROLLER_FILE = Path(__file__).resolve().parent / "controller.py"
_LIFECYCLE_FILE = Path(__file__).resolve().parent / "lifecycle.py"


def _norm(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _key_names(bits: int) -> str:
    names = [name for index, name in enumerate(KEY_NAMES) if bits & (1 << index)]
    return "+".join(names) or f"{bits:#x}"


def _swap_everywhere(old: Callable, new: Callable) -> int:
    """Re-bind every module-level name that refers to `old` so it refers to `new`. Returns how many."""
    swapped = 0
    for module in list(sys.modules.values()):
        if not isinstance(module, ModuleType):
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


class Sealed(type):
    """Metaclass: a class built with it cannot be changed after its definition.

    WHY: the verdict is computed by methods of a few classes. Any code holding an instance can reach
    its class (`type(obj)`) and replace a method there, which would rewrite the verdict without
    touching one counter. Refusing class-level assignment closes that at run time, for every route
    the static gate cannot see. (Instance-level shadowing is closed by `__slots__`.)"""

    def __setattr__(cls, name: str, value: object) -> None:
        raise AttributeError(f"{cls.__name__} is sealed: its attribute {name!r} cannot be set")

    def __delattr__(cls, name: str) -> None:
        raise AttributeError(f"{cls.__name__} is sealed: its attribute {name!r} cannot be deleted")


class PurityCounters(metaclass=Sealed):
    """The counts behind the verdict. READ-ONLY from outside this module: `counters.foreign_presses`
    reads, `counters.foreign_presses = 0` raises (no such slot), and the values live in a private
    dict that only this module touches."""

    __slots__ = ("_values", "_origins")

    def __init__(self) -> None:
        self._values: dict[str, int] = dict.fromkeys(COUNTER_NAMES, 0)
        self._origins: dict[str, Counter] = {kind: Counter() for kind in ORIGIN_KINDS}

    def __getattr__(self, name: str) -> int:
        # Called only when normal lookup fails, i.e. for the counter names. A private name never
        # reaches the dict (that would recurse while `_values` is still unset).
        if not name.startswith("_"):
            values = self._values
            if name in values:
                return values[name]
        raise AttributeError(name)

    def _add(self, name: str, kind: str | None = None, origin: str | None = None, count: int = 1) -> None:
        self._values[name] += count
        if kind is not None and origin is not None:
            self._origins[kind][origin] += count

    def snapshot(self) -> dict[str, int]:
        return dict(self._values)

    def origins_snapshot(self) -> dict[str, dict[str, int]]:
        return {kind: dict(counter.most_common(20)) for kind, counter in self._origins.items() if counter}

    def breach(self) -> bool:
        """Purity is broken by ANY foreign action; by the AI writing memory, loading a state, advancing
        a frame, pressing outside its controller or running bot code; by anything reaching the game
        through no door; and by the instrument being tampered with or failing."""
        return any(self._values[name] for name in BREACH_COUNTERS)

    def verdict(self) -> str:
        if self.breach():
            return "BREACH"
        if self._values["real_frames"] == 0:
            return "UNVERIFIED"  # the sink audit never ran, so nothing was measured
        return "CLEAN"

    def purity_line(self) -> str:
        # ‼ The first four fields are the contract other tools parse: keep their order and spelling.
        v = self._values
        return (
            f"[AI-PURITY] foreign_presses={v['foreign_presses']} foreign_writes={v['foreign_writes']} "
            f"foreign_loads={v['foreign_loads']} ai_presses={v['ai_presses']} "
            f"ai_writes={v['ai_writes']} ai_loads={v['ai_loads']} ai_bot_calls={v['ai_bot_calls']} "
            f"ai_unrouted_presses={v['ai_unrouted_presses']} extra_frames={v['extra_frames']} "
            f"unattributed_inputs={v['unattributed_inputs']} "
            f"unattributed_state_changes={v['unattributed_state_changes']} "
            f"instrument_tampered={v['instrument_tampered']} instrument_errors={v['instrument_errors']} "
            f"ran_after_finish={v['ran_after_finish']} "
            f"real_frames={v['real_frames']} peek_restores={v['peek_restores']} verdict={self.verdict()}"
        )

    def origins_line(self) -> str:
        parts = []
        for kind, counter in self._origins.items():
            if counter:
                top = ", ".join(f"{origin} x{count}" for origin, count in counter.most_common(6))
                parts.append(f"{kind}=[{top}]")
        return "[AI-PURITY-ORIGINS] " + ("; ".join(parts) if parts else "none")


class Attribution(metaclass=Sealed):
    """Installs the wrappers and the bot-code monitor, audits the sinks, keeps the counters, and
    removes everything when the lifecycle finalizes the audit."""

    __slots__ = (
        "_counters", "_package_prefix", "_controller_path", "_lifecycle_path", "_framework_root",
        "_display_roots", "_norm_cache", "_brain_cache", "_local", "_undo", "_installed_wrappers",
        "_module_wrappers", "_tamper_seen", "_installed", "_finalized", "_verdict_written",
        "_emulator", "_core", "_libmgba_path", "_main_path", "_frame_callback", "_callback_ids",
        "_peek_depth", "_ledger_pressed", "_ledger_held", "_snapshot", "_tool", "_monitor",
        "_disable", "_brain_entries", "_brain_exceptions", "_verdict_path", "_verdict_facts",
    )

    def __init__(self) -> None:
        self._counters = PurityCounters()
        self._package_prefix = _norm(_PACKAGE_DIR) + os.sep
        self._controller_path = _norm(_CONTROLLER_FILE)
        self._lifecycle_path = _norm(_LIFECYCLE_FILE)
        self._framework_root = _norm(Path(framework_memory.__file__).resolve().parents[1])
        self._display_roots = [self._framework_root, _norm(_PACKAGE_DIR.parent)]
        self._norm_cache: dict[str, str] = {}
        self._brain_cache: dict[str, bool] = {}
        self._brain_entries = tuple(os.path.normcase(entry) for entry in BOT_BRAIN_PATHS)
        self._brain_exceptions = frozenset(os.path.normcase(entry) for entry in BOT_BRAIN_EXCEPTIONS)
        self._local = threading.local()
        self._undo: list[Callable[[], None]] = []
        self._installed_wrappers: list[tuple[object, str, Callable, str]] = []
        self._module_wrappers: list[tuple[str, Callable]] = []
        self._tamper_seen: set[str] = set()
        self._installed = False
        self._finalized = False
        self._verdict_written = False
        self._emulator = None
        self._core = None
        self._libmgba_path = ""
        self._main_path = ""
        self._frame_callback = None
        self._callback_ids: dict[str, list[int] | None] = {}
        self._peek_depth = 0
        self._ledger_pressed = 0
        self._ledger_held = 0
        self._snapshot: tuple[bytes, bytes] | None = None
        self._tool: int | None = None
        self._monitor: Callable | None = None
        self._disable = None
        self._verdict_path: Path | None = None
        self._verdict_facts: dict[str, object] = {}

    @property
    def counters(self) -> PurityCounters:
        return self._counters

    # ------------------------------------------------------------------ install / finalize
    def install(self) -> None:
        if self._installed or self._finalized:
            raise RuntimeError("attribution is already installed (or already finalized)")
        emulator = context.emulator
        if emulator is None:
            raise RuntimeError("no emulator: the AI mode started before the framework created one")
        self._emulator = emulator
        self._core = emulator._core
        self._libmgba_path = self._path(type(emulator).run_single_frame.__code__.co_filename)
        self._main_path = _norm(Path(self._libmgba_path).with_name("main.py"))
        self._frame_callback = emulator._on_frame_callback

        for name in EMULATOR_INPUT_METHODS:
            self._wrap_method(emulator, "emulator", name, self._make_wrapper("presses", name, getattr(emulator, name)))
        for name in EMULATOR_WRITE_METHODS:
            self._wrap_method(emulator, "emulator", name, self._make_wrapper("writes", name, getattr(emulator, name)))
        for name in EMULATOR_LOAD_METHODS:
            self._wrap_method(emulator, "emulator", name, self._make_wrapper("loads", name, getattr(emulator, name)))
        self._wrap_method(emulator, "emulator", "peek_frame", self._make_peek_wrapper(emulator.peek_frame))
        for name in CORE_LOAD_METHODS:
            self._wrap_method(self._core, "core", name, self._make_wrapper("loads", name, getattr(self._core, name)))
        for name in CORE_FRAME_METHODS:
            self._wrap_method(self._core, "core", name, self._make_wrapper("frames", name, getattr(self._core, name)))
        self._wrap_method(self._core, "core", "run_frame", self._make_run_frame_wrapper(self._core.run_frame), keep=True)
        for name in MEMORY_FUNCTIONS:
            self._wrap_module_function(name)

        callbacks = self._core._callbacks
        for list_name in CORE_CALLBACK_LISTS:
            entries = getattr(callbacks, list_name, None)
            self._callback_ids[list_name] = [id(entry) for entry in entries] if isinstance(entries, list) else None
        self._install_monitor()
        # Inputs already held when the AI takes over were set by nobody the AI can name: they stay
        # OUT of the ledger, so if they reach a frame they count as unattributed.
        self._ledger_pressed = 0
        self._ledger_held = 0
        self._snapshot = self._memory_snapshot()
        self._installed = True

    def finalize_audit(self) -> PurityCounters:
        """The last instrument check, then every wrapper and the monitor come off. Only
        `lifecycle.finish` may call this: from anywhere else it is counted as tampering and refused."""
        caller = sys._getframe(1)
        if not self._is_lifecycle_finish(caller):
            self.note_tamper(f"finalize_audit was called by {self._describe(caller, 'finalize_audit')}, not by lifecycle.finish")
            return self._counters
        self._finalize()
        return self._counters

    def write_verdict_file(self, path: Path | None, facts: dict[str, object]) -> str:
        """Write `path` (the run's purity.json) ONCE, from this module's own counters. Only
        `lifecycle.finish` may call this. Returns a log line saying what happened."""
        caller = sys._getframe(1)
        if not self._is_lifecycle_finish(caller):
            self.note_tamper(f"write_verdict_file was called by {self._describe(caller, 'write_verdict_file')}, not by lifecycle.finish")
            return "[AI-LIFECYCLE] verdict file: REFUSED (wrong caller)"
        self._finalize()
        if self._verdict_written:
            return "[AI-LIFECYCLE] verdict file: already written; not written again"
        self._verdict_written = True
        self._verdict_path = path
        self._verdict_facts = {str(key): value for key, value in facts.items()}
        if path is None:
            return "[AI-LIFECYCLE] verdict file: none (no run_dir; a run started by hand prints its verdict only)"
        return self._write_verdict()

    def _write_verdict(self) -> str:
        path = self._verdict_path
        if path is None:
            return "[AI-LIFECYCLE] verdict file: none"
        payload = {
            "written_by": "ai_player/platform/attribution.py Attribution.write_verdict_file",
            "pid": os.getpid(),
            "verdict": self._counters.verdict(),
            "counters": self._counters.snapshot(),
            "origins": self._counters.origins_snapshot(),
            "facts": self._verdict_facts,
        }
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        except OSError as error:
            return f"[AI-LIFECYCLE] verdict file: FAILED to write {path}: {error}"
        return f"[AI-LIFECYCLE] verdict file written: {path}"

    def _finalize(self) -> None:
        """The last look while the wrappers are still on, then everything comes off EXCEPT the
        `run_frame` wrapper, which stays as a tripwire (`_ran_after_finish`)."""
        if self._finalized:
            return
        try:
            self.audit_instrument()
        except Exception as error:
            self._instrument_error("the last instrument audit", error)
        self._finalized = True
        self._uninstall()

    def _ran_after_finish(self, caller: FrameType) -> None:
        """A REAL frame after the verdict was written. `finish` ends with sys.exit, which leaves no
        frame to run, so something caught that SystemExit and kept playing while every counter was
        off. The verdict is rewritten as BREACH and the process ends at once (`os._exit`: a second
        SystemExit could be caught the same way)."""
        self._counters._add(
            "ran_after_finish", "tamper",
            f"a real frame ran after the verdict was written ({self._describe(caller, 'run_frame')}): "
            f"something caught the lifecycle's SystemExit",
        )
        self._verdict_facts = {
            **self._verdict_facts,
            "exit_reason": "ran-after-finish",
            "exit_code": EXIT_RAN_AFTER_FINISH,
            "first_ending": {k: self._verdict_facts.get(k) for k in ("exit_reason", "exit_code")},
        }
        line = self._write_verdict()
        try:
            print(f"[AI-LIFECYCLE] the run kept playing after its verdict was written: verdict rewritten as "
                  f"{self._counters.verdict()} ({line})", flush=True)
            print(self._counters.purity_line(), flush=True)
            print(f"[AI-EXIT] reason=ran-after-finish code={EXIT_RAN_AFTER_FINISH}", flush=True)
        finally:
            os._exit(EXIT_RAN_AFTER_FINISH)

    def _uninstall(self) -> None:
        while self._undo:
            undo = self._undo.pop()
            try:
                undo()
            except Exception as error:
                self._instrument_error("uninstalling", error)
        self._installed = False

    def _is_lifecycle_finish(self, frame: FrameType) -> bool:
        return self._path(frame.f_code.co_filename) == self._lifecycle_path and frame.f_code.co_name == "finish"

    def _wrap_method(self, owner: object, label: str, name: str, wrapper: Callable, keep: bool = False) -> None:
        """Install `wrapper` as `owner.name`. `keep`: never undo it (the run_frame tripwire must
        outlive the audit; the process ends right after the lifecycle's finish anyway)."""
        had_instance_attribute = name in vars(owner)
        original = vars(owner).get(name)
        setattr(owner, name, wrapper)
        self._installed_wrappers.append((owner, name, wrapper, label))
        if keep:
            return

        def undo() -> None:
            if had_instance_attribute:
                setattr(owner, name, original)
            else:
                delattr(owner, name)

        self._undo.append(undo)

    def _wrap_module_function(self, name: str) -> None:
        """Wrap a `modules.memory` function AND every module-level alias of it.

        WHY the sweep: `from modules.memory import write_symbol` copies the function into the
        importing module, so wrapping only `modules.memory` would miss it. (The emulator-level
        `write_bytes` wrapper would still catch the write itself; the sweep keeps the LABEL right.)
        The undo sweeps again, because a module first imported WHILE the AI ran copied the wrapper,
        not the original.
        """
        original = getattr(framework_memory, name)
        wrapper = self._make_wrapper("writes", name, original)
        _swap_everywhere(original, wrapper)
        self._module_wrappers.append((name, wrapper))
        self._undo.append(lambda: _swap_everywhere(wrapper, original))

    # ------------------------------------------------------------------ layer 1: the doors
    def _make_wrapper(self, kind: str, name: str, original: Callable) -> Callable:
        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            depth = getattr(self._local, "depth", 0)
            outermost = depth == 0
            state_change = False
            inputs_before = self._input_state() if kind == "presses" else None
            if outermost:
                try:
                    state_change = self._record(kind, name, args, inputs_before, sys._getframe(1))
                except Exception as error:
                    self._instrument_error(f"recording {name}", error)
                    state_change = kind != "presses"
            self._local.depth = depth + 1
            try:
                return original(*args, **kwargs)
            finally:
                self._local.depth = depth
                try:
                    if inputs_before is not None:
                        self._update_ledger(inputs_before)
                    elif state_change and self._installed:
                        # A COUNTED write or load changed memory on purpose: it is already in the
                        # counters, so the between-frames audit starts again from here.
                        self._snapshot = self._memory_snapshot()
                except Exception as error:
                    self._instrument_error(f"after {name}", error)

        return wrapper

    def _make_peek_wrapper(self, original: Callable) -> Callable:
        """`peek_frame` is a context manager; frames run inside it are look-ahead, not play."""

        @contextlib.contextmanager
        def peek_frame(*args, **kwargs):
            self._peek_depth += 1
            try:
                with original(*args, **kwargs) as value:
                    yield value
            finally:
                self._peek_depth -= 1

        return peek_frame

    def _input_state(self) -> tuple[int, int, int]:
        emulator = self._emulator
        return emulator._pressed_inputs, emulator._held_inputs, emulator._prev_pressed_inputs

    def _update_ledger(self, before: tuple[int, int, int]) -> None:
        """Only bits that THIS door call turned on are covered; bits that were already on (set by
        nobody the instrument saw) stay uncovered, so they show up at the sink."""
        pressed_before, held_before, _ = before
        pressed_after, held_after, _ = self._input_state()
        self._ledger_pressed |= pressed_after & ~pressed_before
        self._ledger_held = (self._ledger_held & held_after) | (held_after & ~held_before)

    def _record(self, kind: str, name: str, args: tuple, inputs_before, caller: FrameType) -> bool:
        """Count one outermost door call. Returns True when it was a counted state change (a write,
        a load or a frame advance), after which the memory baseline is taken again."""
        counters = self._counters
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
        return self._path(caller.f_code.co_filename) == self._libmgba_path and caller.f_code.co_name in PEEK_RESTORERS

    # ------------------------------------------------------------------ layer 2: the sinks
    def _make_run_frame_wrapper(self, original: Callable) -> Callable:
        @functools.wraps(original)
        def run_frame(*args, **kwargs):
            caller = sys._getframe(1)
            kind = self._frame_kind(caller)
            if self._finalized:
                # After the verdict only the framework's shutdown may run frames, and those are
                # look-ahead (its screenshot for the state file). A REAL frame means play went on.
                if kind == "real" and self._verdict_written:
                    self._ran_after_finish(caller)
                return original(*args, **kwargs)
            if kind == "look-ahead":
                return original(*args, **kwargs)
            try:
                self._audit_before_frame(kind, caller)
            except Exception as error:
                self._instrument_error("auditing a frame", error)
            result = original(*args, **kwargs)
            try:
                if kind == "real":
                    self._ledger_pressed = 0  # run_single_frame clears `_pressed_inputs` next
                self._snapshot = self._memory_snapshot()
            except Exception as error:
                self._instrument_error("after a frame", error)
            return result

        return run_frame

    def _frame_kind(self, caller: FrameType) -> str:
        if self._peek_depth > 0:
            return "look-ahead"
        if self._path(caller.f_code.co_filename) == self._libmgba_path:
            if caller.f_code.co_name in LOOK_AHEAD_FUNCTIONS:
                return "look-ahead"
            if caller.f_code.co_name == "run_single_frame":
                outer = caller.f_back
                if (
                    outer is not None
                    and outer.f_code.co_name == "main_loop"
                    and self._path(outer.f_code.co_filename) == self._main_path
                ):
                    return "real"
        return "extra"  # fail-closed: anything not placed as real or look-ahead is a breach

    def _audit_before_frame(self, kind: str, caller: FrameType) -> None:
        counters = self._counters
        if kind == "extra":
            is_ai, _ = self._classify(caller)
            counters._add("extra_frames", "frames", ("AI " if is_ai else "") + self._describe(caller, "run_frame"))
        else:
            counters._add("real_frames")
            self.audit_instrument()
        if self._snapshot is not None:
            now = self._memory_snapshot()
            if now != self._snapshot:
                counters._add("unattributed_state_changes", "memory", self._describe_change(self._snapshot, now))
        latched = self._emulator.get_inputs()
        stray = latched & ~(self._ledger_pressed | self._ledger_held)
        if stray:
            counters._add("unattributed_inputs", "inputs", f"{_key_names(stray)} latched with no counted press or hold")

    def _memory_snapshot(self) -> tuple[bytes, bytes]:
        memory = self._core._native.memory
        return (
            bytes(ffi.buffer(ffi.cast("char*", memory.wram), WRAM_SIZE)),
            bytes(ffi.buffer(ffi.cast("char*", memory.iwram), IWRAM_SIZE)),
        )

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
        monitoring = sys.monitoring
        tool = next((tool for tool in MONITORING_TOOL_IDS if monitoring.get_tool(tool) is None), None)
        if tool is None:
            raise RuntimeError(f"no free sys.monitoring tool id among {MONITORING_TOOL_IDS}: bot code cannot be watched")
        monitoring.use_tool_id(tool, MONITORING_TOOL_NAME)
        self._tool = tool
        self._disable = monitoring.DISABLE
        self._monitor = self._on_code_start  # one bound method, kept, so the audit can check identity
        monitoring.register_callback(tool, monitoring.events.PY_START, self._monitor)
        monitoring.set_events(tool, monitoring.events.PY_START)

        def undo() -> None:
            monitoring.set_events(tool, 0)
            monitoring.register_callback(tool, monitoring.events.PY_START, None)
            monitoring.free_tool_id(tool)

        self._undo.append(undo)

    def _is_brain_file(self, filename: str) -> bool:
        # Everything is compared in normcase form (on Windows: lower case, backslashes), so the
        # lists' "/" become os.sep here and a folder entry is one that ends with os.sep.
        path = self._path(filename)
        root = self._framework_root + os.sep
        if not path.startswith(root):
            return False
        relative = path[len(root):]
        if relative in self._brain_exceptions:
            return False
        return any(relative == entry or (entry.endswith(os.sep) and relative.startswith(entry)) for entry in self._brain_entries)

    def _on_code_start(self, code, instruction_offset):
        """PY_START callback: is this the bot's decision code, started on the AI's behalf?"""
        try:
            filename = code.co_filename
            brain = self._brain_cache.get(filename)
            if brain is None:
                brain = self._is_brain_file(filename)
                self._brain_cache[filename] = brain
            if not brain:
                return self._disable  # never asked again for this function
            frame = sys._getframe(1).f_back  # [0] this callback, [1] the bot function, then its callers
            while frame is not None:
                if self._path(frame.f_code.co_filename).startswith(self._package_prefix):
                    shown = self._shown(filename)
                    self._counters._add("ai_bot_calls", "bot", self._describe(frame, f"{shown}:{code.co_name}"))
                    break
                frame = frame.f_back
        except Exception as error:
            self._instrument_error("watching bot code", error)
        return None

    # ------------------------------------------------------------------ the instrument checks itself
    def audit_instrument(self) -> None:
        """Count every way the instrument could have been switched off or bypassed since install."""
        if not self._installed:
            return
        for owner, name, wrapper, label in self._installed_wrappers:
            if vars(owner).get(name) is not wrapper:
                self.note_tamper(f"the {label}.{name} wrapper was removed or replaced")
        for name, wrapper in self._module_wrappers:
            if getattr(framework_memory, name, None) is not wrapper:
                self.note_tamper(f"the modules.memory.{name} wrapper was removed or replaced")
        callbacks = self._core._callbacks
        for list_name, ids in self._callback_ids.items():
            entries = getattr(callbacks, list_name, None)
            now = [id(entry) for entry in entries] if isinstance(entries, list) else None
            if now != ids:
                self.note_tamper(f"the core's {list_name} callback list changed (it runs inside the frame)")
        if self._emulator._on_frame_callback is not self._frame_callback:
            self.note_tamper("the emulator's frame callback was replaced")
        if context.emulator is not self._emulator:
            self.note_tamper("context.emulator is no longer the emulator the AI started with")
        if self._tool is not None:
            monitoring = sys.monitoring
            if monitoring.get_tool(self._tool) != MONITORING_TOOL_NAME:
                self.note_tamper("the bot-code monitor's sys.monitoring tool id was freed or taken")
            elif monitoring.get_events(self._tool) != monitoring.events.PY_START:
                self.note_tamper("the bot-code monitor's sys.monitoring events were changed")
            else:
                previous = monitoring.register_callback(self._tool, monitoring.events.PY_START, self._monitor)
                if previous is not self._monitor:
                    self.note_tamper("the bot-code monitor's callback was replaced")

    def note_tamper(self, problem: str) -> None:
        """Count a distinct tampering problem once (it is re-detected on every frame)."""
        if problem in self._tamper_seen:
            return
        self._tamper_seen.add(problem)
        self._counters._add("instrument_tampered", "tamper", problem)

    def note_error(self, where: str, error: BaseException) -> None:
        """Count a failure of the audit itself (for the lifecycle, which has no access to the counts)."""
        self._instrument_error(where, error)

    def _instrument_error(self, where: str, error: BaseException) -> None:
        self._counters._add("instrument_errors", "errors", f"{where}: {type(error).__name__}: {error}")

    # ------------------------------------------------------------------ origin of a call
    def _path(self, filename: str) -> str:
        cached = self._norm_cache.get(filename)
        if cached is None:
            cached = _norm(filename)
            self._norm_cache[filename] = cached
        return cached

    def _classify(self, caller: FrameType) -> tuple[bool, bool]:
        """(is it the AI's?, did it come straight from the controller?). Only the IMMEDIATE caller
        counts as routing: bot code called from AI code is the AI's, and unrouted."""
        via_controller = self._path(caller.f_code.co_filename) == self._controller_path
        frame: FrameType | None = caller
        while frame is not None:
            if self._path(frame.f_code.co_filename).startswith(self._package_prefix):
                return True, via_controller
            frame = frame.f_back
        return False, False

    def _shown(self, filename: str) -> str:
        path = self._path(filename)
        for root in self._display_roots:
            if path.startswith(root + os.sep):
                return path[len(root) + 1 :].replace(os.sep, "/")
        return path.replace(os.sep, "/")

    def _describe(self, caller: FrameType, name: str) -> str:
        return f"{self._shown(caller.f_code.co_filename)}:{caller.f_lineno} {caller.f_code.co_name}->{name}"
