"""OFFLINE purity gate for the AI player: an AST walk that fails when bot code could reach the play loop.

    py -3.12 ai_player/gates/check_purity.py [--package DIR] [--hook FILE] [--build-root DIR]
    py -3.12 ai_player/gates/check_purity.py --instrument-digest     # after a REVIEWED instrument change
    exit 0 = PASS, 1 = FAIL, 2 = could not run

WHY (USER RULING 35; design draft §2.2 and §10.2; CLAUDE.md session rule 6, "anything enforceable
belongs in a GATE, not in prose"): the AI plays the game with its own code. This gate refuses every
route it knows of by which bot code, or a change to the game or to the framework, could get into the
AI's play loop. `py -3.12 -m ai_player run` runs it on the exact package it launches and refuses to
launch on a FAIL, so a PASS certifies what runs.

WHY IT IS AN ALLOWLIST ALL THE WAY DOWN. Two independent verifiers broke earlier versions, each time
through a door the gate had not listed: re-exports, aliased `import_module`, `sys.modules`, `.pyw`
files, private emulator fields (29 of 41 probes, first round); then `sys` reached as `os.sys` or
`dataclasses.sys`, `dataclasses.inspect.getmembers` as an attribute dictionary, `match` class patterns
(their attribute names are plain strings, not attribute nodes), `str.format` field access,
`functools.update_wrapper` as a dynamic setattr, file writes, and source hidden in `__pycache__`
(20 of 28, second round). Every one was a NAME the gate did not know was dangerous. So the standard
library is now a door too: a library module may be used only as `module.<attribute>`, and only for
attributes on its surface. Everything else is refused, whatever it is called.

FILE ROLES
  play loop   every file of `ai_player/` except the ones below, plus the hook file in
              `sandbox-pokebot/plugins/custom_modes/`. Runs inside the framework's process.
  brain       `mode.py`: a play-loop file that is framework-FREE: no door into the framework, and it
              may not import the host side (rule c). It sees the game only through abstract
              interfaces, so a standalone build can keep it unchanged (finding 10 of the step-0 review).
  launcher    `__main__.py`, `host/launcher.py` and (R1 + R2, D8) `paths.py`, the one resolver of the AI's user
              data: run in the LAUNCHER process, never inside the framework. Rules (a) imports, (b), (c), (d),
              (e) apply; library surfaces and (f) do not.
  instrument  `host/attribution.py`: a play-loop file that must name the state-changing
              functions and use reflection to wrap and count them, so (b), (d) and (f) do not apply
              to it. In exchange its exact bytes are pinned (rule g): every change is a reviewed change.
  test side   `ai_player/gates/`: may use the framework to GRADE the AI. Not scanned by a, b, d, f.

RULES
(a) IMPORTS AND SURFACES. Every import, and every USE of an imported name, must be on an allowlist:
    * framework: only `from M import N` for an explicit DOOR (module, name, file). A door that is an
      OBJECT lists the attribute paths each file may walk on it (`context.emulator.press_button` in
      the controller; `bot_listeners` and, with "=", assigning it, in isolation;
      `get_bot_listeners=` on `modules.main`, the framework's listener-rebuild door, in isolation
      only; build step 1's EYES: fifteen read-only framework functions (sixteen since build step 2 added
      `modules.game.get_symbol`, a symbol-table lookup) plus `context.emulator.read_bytes` /
      `get_frame_count` and `context.rom.is_emerald`, in `host/eyes.py` only), so an
      allowed object cannot be walked over to the bot, aliased or handed on.
      `import modules.x` without `as` binds the whole `modules` package and is always refused. The
      bot's brain is refused even if a door would let it in (a backstop).
    * standard library: only the modules in `LIBRARIES`, each for the files listed, and each name
      bound to one may be used ONLY as `name.<attribute>` with the attribute on that module's
      SURFACE: an explicit list for powerful modules (`sys`, `os`, `traceback`, `pathlib`, ...), or
      PUBLIC: a public attribute of the module, in this interpreter, that is not itself a module, not
      a reflective function (`getattr`, `update_wrapper`, `get_type_hints`, ...), and does not come
      from `operator`, `inspect`, `importlib`, `sys` and the like. `from M import x` is judged the
      same way. A module passed around as a value is refused (it is a door to every module it
      imports: `os.sys`, `dataclasses.inspect`, `enum.bltns`).
    * ai_player: only `from ai_player.x import Name` with `Name` in x's `__all__`, every `__all__`
      entry a name x DEFINES (no re-exports), and x a file this gate scanned (never a path through
      `__pycache__` or another dunder folder). `import ai_player...` and star imports are refused.
    * a string whose whole value is a bot module path (`'modules.menuing'`) is refused.
    * no top-level module or folder of the package may be named like a standard-library module
      (step 0's `ai_player/platform/` shadowed `platform` for anything that put `ai_player/` on the path).
(b) STATE CHANGES. No play-loop file may name a function that writes game memory, loads or resets
    the emulator, or advances frames (`STATE_CHANGING_NAMES`), as a call, an attribute, a name, an
    import, a `match` class-pattern attribute, a `getattr` constant or a string whose whole value is
    the name. The button functions (`INPUT_NAMES`) may be named only in `host/controller.py`.
    (R1 + R2, build spec 2026-10-29 D12 (c): USER RULING 52, the AI never ends or restarts its own process) `sys.exit` is
    on the surface of the lifecycle only (`host/lifecycle.py`; the launcher's `__main__.py` is not judged by surfaces), and
    the builtin names `exit`, `quit`, `SystemExit` and `KeyboardInterrupt` (`PLAY_LOOP_EXIT_NAMES`) are refused in every
    PLAY-LOOP file (`PLAY_LOOP_PARTS`: brain/, skills/, hands/, world/, eyes/, mode.py, personality.py, game_memory.py,
    options.py), raised or caught.
    (R1 + R2 follow-up, spec 2026-10-29 D1: N-1) The same files also may not name `GeneratorExit`, `BaseException`,
    `BaseExceptionGroup`, `ExitStack` or `AsyncExitStack` (as a name, an attribute such as `contextlib.ExitStack`, or an
    imported name), write a bare `except:`, reach a `return`, `yield`, `yield from` or `await` from a `finally` body (a
    nested def, lambda or class is its own scope), reach a `break` or `continue` from a `finally` body outside a loop
    nested in it, or define `__exit__`/`__aexit__`. Each discards, swallows or holds back an exit in flight without
    naming any exit class: a `return` in a `finally` drops the exception being raised, a `yield` there hands the caller
    a frame after the exit began, and an `__exit__` or an `ExitStack` callback that returns True swallows it.
    (U2 spec 2026-10-30 D16, RV-7) Nor may they reach a `raise` or an `assert` from a `finally` body (the same scope
    rule; a `try` nested in the `finally` is no shelter): a raise there, or a failing assert, REPLACES the exit in flight.
(c) SIDES. The play loop may not import the test side (`ai_player.gates`) or the launcher side,
    the launcher side may not import the framework, and the brain (`mode.py`) may not import the
    host side (`ai_player.host`).
(d) REFLECTION. Refused in the play loop: `__import__`, `eval`, `exec`, `compile`, `globals`,
    `locals`, `vars`, `help`, `breakpoint` and the other `REFLECTION_NAMES` (as names or attributes);
    `setattr` and `delattr`; `getattr` / `hasattr` except as a direct call with a constant name, which
    is then judged exactly like `obj.<name>`; private attributes (`x._y`) except on `self` and `cls`;
    dunder attributes and names except a few harmless ones; import-system, tracing and frame
    attributes (`modules`, `meta_path`, `settrace`, `monitoring`, `f_globals`, `f_back`, `tb_frame`,
    ...); `str.format` / `format_map` unless the template is a constant whose fields read no attribute
    or index (`'{0._x}'.format(obj)` walks attributes by name at run time); and strings whose whole
    value is a private or dunder identifier. A `match` class pattern's attribute names are judged
    like attributes.
(e) FILES. Every file in the package is judged: `.py` / `.pyw` are scanned, parsed from their BYTES
    as the import system does (read as UTF-8 text, a `# coding: utf-7` file shows a comment where
    Python runs an import); bytecode or extension modules outside `__pycache__` are refused; links
    (symlinks, junctions) are refused; a `__pycache__` folder may hold only the cache files CPython
    writes, and each cached file that CPython would load INSTEAD of its source (its header matches the
    source) must hold exactly the code of that source.
(f) SIDE EFFECTS. Only `runlog.py` (the AI's log) and the instrument (the verdict file) may write
    files: elsewhere the `pathlib.Path` writers (`write_text`, `mkdir`, `unlink`, `rename`, `touch`,
    ...), a one-argument `.replace(target)` (a file move; `str.replace` takes two) and `open` in any
    mode but read are refused (`os` and `shutil` writers are on no surface at all). No play-loop file may assign to, or delete, an attribute or item of anything it imported
    (a library the framework shares, a framework object, another AI module's class): that would
    change code other modules run.
(g) PINNED SURFACES. Each host module's `__all__` must equal the list in `HOST_EXPORTS`
    (a new host module or a new export is a reviewed gate change); the instrument's bytes must match
    `INSTRUMENT_SHA256`; the instrument's run-time list of bot code (`BOT_BRAIN_PATHS`) must cover
    every module the backstop refuses; the instrument's finalizing methods may be named only in
    `host/lifecycle.py`, and its isolation check (`watch_guard`) only in `host/session.py`.

THE HOOK'S PATH. The hook may touch `sys.path` only as `sys.path.append(...)`: putting the repo root
in FRONT of the standard library would let a repo-root file named like a library module replace it
(finding 4 of the step-0 review). Item assignment to `sys.path` is refused like any other.

Comments, docstrings and strings that merely MENTION a name never fire: the AST has no comments, a
string statement (a docstring) is skipped, f-string text is skipped, and a string is only flagged
when its WHOLE value is the identifier. `test_check_purity.py` proves both directions: every rule
fails on planted violations (including both verifiers' probes, verbatim) and stays silent on
mentions and on ordinary code.

LIMITS, stated so nobody over-reads a PASS.
* Static analysis cannot see values. A name bound by assignment is not tracked: `cls = type(obj)` and
  then `cls.method = f` is not refused here. The classes the verdict depends on are SEALED at run time
  instead (`attribution.Sealed`, with `__slots__`), the objects that decide how a run ends are
  `attribution.Guarded` (writable only from the file that defines their class, every other write
  refused and counted), and the verdict is a file only the instrument can write, read by the
  launcher; any other class the AI changes is its own.
* The PUBLIC surfaces are computed from THIS interpreter's standard library: run the gate with the
  Python the bot runs (3.12). The gate trusts the interpreter, its standard library and
  site-packages, and the framework's own code; it judges only which framework code the AI may reach.
* Bot DATA read without calling bot code (a constant table) is refused only here (rule a). Bot code
  that RUNS on the AI's behalf is also caught live (`ai_bot_calls`), as are presses, writes, loads
  and frames through any route (`[AI-PURITY]`); `gates/live_step0.py` fault-tests both halves on the
  same plants. The live audit's own blind spots (a native-only change to the CPU or I/O registers,
  video memory or the cartridge save) need the emulator core (`_core`, `ffi`) or a frame's globals,
  and every route to those that the verifiers found is refused here; that is a list of known routes,
  not a proof that no other exists.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import functools
import hashlib
import importlib
import importlib.machinery
import importlib.util
import marshal
import os
import re
import string
import sys
import typing
from dataclasses import dataclass, field
from pathlib import Path
from types import CodeType, FunctionType, ModuleType

PACKAGE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_ROOT = PACKAGE_DIR.parent / "sandbox-pokebot"
DEFAULT_HOOK = DEFAULT_BUILD_ROOT / "plugins" / "custom_modes" / "ai_player_mode.py"
HOOK_KEY = "<hook>"

TEST_SIDE_DIR = "gates/"
TEST_SIDE_MODULE = "ai_player.gates"
HOST_DIR = "host/"
HOST_MODULE = "ai_player.host"
LAUNCHER_FILES = frozenset({"__main__.py", "host/launcher.py", "paths.py"})
LAUNCHER_MODULES = frozenset({"ai_player.__main__", "ai_player.host.launcher", "ai_player.paths"})
INSTRUMENT = "host/attribution.py"
CONTROLLER = "host/controller.py"
ISOLATION = "host/isolation.py"
LIFECYCLE = "host/lifecycle.py"
SESSION = "host/session.py"
#: Build step 1: the EYES, the only file that reads the game (through the read-only doors below).
EYES = "host/eyes.py"
RUNLOG = "runlog.py"
#: The brain: framework-free, and it may not import the host side (rule c).
BRAIN_FILES = frozenset({"mode.py"})
#: (R1 + R2, D12 (c)) THE PLAY LOOP proper (the deciding code, its eyes and its memory): no file of it may end or restart
#: its own process (USER RULING 52: a continue happens only when the host restarts a KILLED run). Folders end in "/".
PLAY_LOOP_PARTS = ("brain/", "skills/", "hands/", "world/", "eyes/", "mode.py", "personality.py", "game_memory.py",
                   "options.py")
#: The builtins that end the process or catch its end (`sys.exit` is a library surface: the lifecycle's only). (R1 + R2
#: follow-up, D1) Also the classes that catch an exit without naming it (`BaseException`, `BaseExceptionGroup`), the one
#: that ends a generator (`GeneratorExit`), and the context managers whose callbacks can swallow one (`ExitStack`).
PLAY_LOOP_EXIT_NAMES = frozenset({"exit", "quit", "SystemExit", "KeyboardInterrupt",
                                  "GeneratorExit", "BaseException", "BaseExceptionGroup", "ExitStack", "AsyncExitStack"})
#: (D1) The exit names also judged as an ATTRIBUTE (`contextlib.ExitStack`) and as an imported name (`from contextlib import
#: ExitStack as S`): the classes only. `.exit` and `.quit` are ordinary method names on other objects; `sys.exit` is rule (a)'s.
PLAY_LOOP_EXIT_CLASSES = PLAY_LOOP_EXIT_NAMES - {"exit", "quit"}
#: (D1) In a `finally` body: what discards or holds back the exception in flight. A nested def, lambda or class is its own
#: scope; a loop nested in the `finally` owns its own `break` and `continue` (not its `return`).
FINALLY_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
FINALLY_LOOPS = (ast.For, ast.AsyncFor, ast.While)
#: (D1) A class that defines one of these can swallow whatever passes through its `with` (by returning True).
EXIT_METHODS = frozenset({"__exit__", "__aexit__"})


def in_play_loop(key: str) -> bool:
    """(R1, D12 (c)) Is the file `key` (relative to ai_player/) part of the play loop proper?"""
    return any(key == part or (part.endswith("/") and key.startswith(part)) for part in PLAY_LOOP_PARTS)

ANY_FILE = None

# ---------------------------------------------------------------------------------- (a) framework doors


@dataclass(frozen=True)
class Door:
    """One permitted way into the framework.

    `name` None means the module object itself. `files` maps each file that may use the door to the
    attribute paths it may walk on the imported object (None = any use, for classes the AI
    subclasses and for the instrument, which must reach inside to measure). A path ending in "="
    permits ASSIGNING that attribute."""

    module: str
    name: str | None
    files: dict
    why: str


DOORS: tuple[Door, ...] = (
    Door(
        "modules.context",
        "context",
        {
            CONTROLLER: frozenset({"emulator.press_button", "emulator.hold_button", "emulator.release_button"}),
            ISOLATION: frozenset({"bot_listeners", "bot_listeners="}),
            SESSION: frozenset({"bot_mode", "debug", "config.http.http_server.enable"}),
            INSTRUMENT: frozenset({"emulator", "bot_listeners", "frame"}),
            HOOK_KEY: frozenset({"bot_listeners"}),
            EYES: frozenset({"emulator.get_frame_count", "emulator.read_bytes", "rom.is_emerald"}),
        },
        "the framework's singleton. The controller may only press, hold and release buttons through "
        "it; isolation only reads and swaps the listener list; the session only reads the bot-mode "
        "name, the debug flag and whether the HTTP server is on; the instrument only takes the "
        "emulator handle it wraps, reads the listener list to check the AI's guard is in it, and "
        "reads main.py's pass counter (`frame`) to check the audit saw every main-loop frame; the "
        "hook only reads the listener list, for its own before/after record. The EYES (build step 1) "
        "only read: the emulator's frame counter (`get_frame_count` returns `core.frame_counter`), "
        "memory (`read_bytes(address, length)`, `modules/libmgba.py`, memmoves WRAM, IWRAM or ROM bytes "
        "INTO a new bytearray it returns, and raises on any other address), and whether the ROM is "
        "Emerald (a bool). None of the three reaches a button, a write, a load or a frame.",
    ),
    Door(
        "modules.main",
        None,
        {ISOLATION: frozenset({"get_bot_listeners", "get_bot_listeners="})},
        "the framework's main loop module, ONLY so isolation can own the name `main.py` calls to "
        "rebuild its listeners after a reset or a state load (and give it back on exit). Without it a "
        "rebuild ran the framework's listeners for a frame, behind the AI's back.",
    ),
    Door(
        "modules.modes._interface",
        "BotListener",
        {ISOLATION: None},
        "the base class of the AI's own GuardListener: the plugin seam itself, no bot logic.",
    ),
    Door(
        "modules.modes._interface",
        "BotMode",
        {HOOK_KEY: None},
        "the base class the hook registers the 'AI Player' mode with: the plugin seam, no bot logic.",
    ),
    Door(
        "modules.memory",
        None,
        {INSTRUMENT: None},
        "ONLY so the instrument can WRAP its write functions (and re-bind every copy of them) to count "
        "foreign writes. Reading the game is the eyes facade's job (build step 1).",
    ),
    Door(
        "mgba",
        "ffi",
        {INSTRUMENT: None},
        "the C-memory view the instrument READS all of WRAM and IWRAM through, to prove nothing wrote "
        "memory between frames (the emulator's read_bytes cannot reach the last byte of either).",
    ),
    # ---- BUILD STEP 1: the EYES' read-only doors, for `host/eyes.py` ONLY. Each is a FUNCTION the eyes
    # may call (path "" = call it / use its result; nothing on the function itself). Each `why` says
    # what it reads and why it cannot act: re-read the framework function before adding one here. What
    # the eyes do with a RESULT is not tracked statically (a value, rule-a limit); the live audit
    # counts every write, press, load, frame and bot-code call they could cause (`gates/live_step1.py`).
    Door(
        "modules.memory", "read_symbol", {EYES: frozenset({""})},
        "reads a symbol's bytes: `get_symbol(name)` (a dict lookup in the symbol table) then "
        "`context.emulator.read_bytes`. Nothing else.",
    ),
    Door(
        "modules.memory", "get_game_state", {EYES: frozenset({""})},
        "reads `gMain.callback2` and names it (`get_symbol_name`, a dict lookup); stores the answer in "
        "the framework's per-frame Python cache (`state_cache`), which only memoises reads.",
    ),
    Door(
        "modules.memory", "get_event_flag", {EYES: frozenset({""})},
        "reads ONE bit of save block 1 (`get_save_block`, a pointer read then `read_bytes`); an unknown "
        "flag name returns False without reading (so `gates/test_eyes.py` checks every name the eyes use).",
    ),
    Door(
        "modules.player", "get_player", {EYES: frozenset({""})},
        "reads 8 bytes of save block 1 and 14 of save block 2 (money, trainer id) into a `Player` "
        "that decodes them; memoised in `state_cache`.",
    ),
    Door(
        "modules.map", "get_map_data_for_current_position", {EYES: frozenset({""})},
        "reads the player's map and position (`get_player_avatar`: `gPlayerAvatar`, `gObjectEvents`, save "
        "block 1) and wraps `gMapHeader` in a `MapLocation`, whose properties the eyes use read the ROM "
        "(the map name, its warps and bg events). Its layout cache is a Python dict.",
    ),
    Door(
        "modules.map", "get_map_objects", {EYES: frozenset({""})},
        "reads `gObjectEvents` (16 x 0x24 bytes) into `ObjectEvent`s that decode bytes.",
    ),
    Door(
        "modules.map_data", "get_map_enum", {EYES: frozenset({""})},
        "builds the `MapRSE` enum member for (group, number): a lookup, no read at all.",
    ),
    Door(
        "modules.items", "get_item_bag", {EYES: frozenset({""})},
        "reads the bag from save block 1 (and the encryption key) into an `ItemBag` that decodes item ids "
        "and quantities (`get_item_by_index`, a table lookup); memoised in `state_cache`.",
    ),
    Door(
        "modules.pokedex", "get_pokedex", {EYES: frozenset({""})},
        "reads the Pokedex bit fields from save blocks 1 and 2; memoised in `state_cache`.",
    ),
    Door(
        "modules.pokemon", "get_species_by_index", {EYES: frozenset({""})},
        "a lookup in the species table loaded from `modules/data` (game facts): no memory read at all.",
    ),
    Door(
        "modules.pokemon", "get_move_by_index", {EYES: frozenset({""})},
        "a lookup in the move table loaded from `modules/data` (game facts): no memory read at all.",
    ),
    Door(
        "modules.battle_state", "get_battle_state", {EYES: frozenset({""})},
        "reads `gBattleTypeFlags`, `gSideTimers`, `gBattlerPartyIndexes`, `gBattleMons` and the rest of the "
        "battle structs into a `BattleState` that decodes bytes; memoised in `state_cache`.",
    ),
    Door(
        "modules.battle_state", "battle_is_active", {EYES: frozenset({""})},
        "reads `gMain.callback1` and compares its symbol name with BattleMainCB1.",
    ),
    Door(
        "modules.tasks", "get_tasks", {EYES: frozenset({""})},
        "reads `gTasks` into a `TaskList` whose tasks name their function pointer (a symbol lookup); "
        "memoised in `state_cache`.",
    ),
    Door(
        "modules.tasks", "get_global_script_context", {EYES: frozenset({""})},
        "reads `sGlobalScriptContext` into a `ScriptContext` (mode, native function name by symbol "
        "lookup); memoised in `state_cache`.",
    ),
    # ---- BUILD STEP 2 (the hands): one more READ-ONLY door for the eyes, added under the orchestrator's rule
    # "you may only add READ-ONLY doors (documented) to the gate's allowlist".
    Door(
        "modules.game", "get_symbol", {EYES: frozenset({""})},
        "BUILD STEP 2: a lookup in the symbol table (`modules/game.py`: `_symbols[name.strip().upper()]`, a "
        "dict; an unknown name raises): a symbol's (address, size). The eyes use it to tell WHICH buffer a "
        "text printer's `currentChar` points into (`gStringVar4`, `gDisplayedStringBattle`), so they can read "
        "the text on screen. It reads no memory at all, and cannot press, write, load or run a frame.",
    ),
    # ---- BUILD STEP 3 (the world and the navigator): one more READ-ONLY door for the eyes, under the same rule.
    Door(
        "modules.game", "get_symbol_name", {EYES: frozenset({""})},
        "BUILD STEP 3: the REVERSE lookup in the symbol table (`modules/game.py`: `_reverse_symbols.get(address, "
        "('', ''))[0]`, a dict): the name of the symbol AT an address. The eyes name the player's battle "
        "controller function (`gBattlerControllerFuncs[0]`) to see the battle's action menu (FIGHT / BAG / "
        "POKéMON / RUN) take input. `get_symbol` cannot do it: `HandleInputChooseAction` is a static function in "
        "two files (`src/battle_controller_player.c`, `src/battle_controller_safari.c`) and the forward table "
        "keeps one of them (measured 2026-10-08: it returned the Safari one, 0x081593D8, while the player's "
        "controller ran 0x08057588). It reads no memory at all, and cannot press, write, load or run a frame.",
    ),
)

#: The bot's brain. Refused even if a door would let it through. Every entry must also be covered by
#: the instrument's run-time list (`BOT_BRAIN_PATHS`, rule g), so the two halves watch the same code.
FORBIDDEN_PREFIXES: dict[str, str] = {
    "modules.modes.util": "the bot's navigation and interaction helpers",
    "modules.modes._listeners": "the listeners that play for the bot (the reason isolation exists)",
    "modules.battle_strategies": "the bot's battle brain",
    "modules.battle_handler": "the bot's battle driver",
    "modules.battle_action_selection": "the bot's battle menu driver",
    "modules.battle_menuing": "the bot's battle menu driver",
    "modules.battle_move_replacing": "the bot's move-learning decisions",
    "modules.battle_evolution_scene": "the bot's evolution-scene handling",
    "modules.faint_chooser": "the bot's faint replacement decision",
    "modules.encounter": "the bot's catch decision (judge_encounter / handle_encounter)",
    "modules.menuing": "the bot's menu scripts",
    "modules.map_path": "the bot's pathfinder",
    "modules.warp_graph": "the bot's long-range routing",
    "modules.mart": "the bot's shopping scripts",
    "modules.macros": "the bot's button macros",
    "modules.player_pc_navigaton": "the bot's PC scripts",
    "modules.pokemon_storage_navigaton": "the bot's box scripts",
    "modules.safari_strategy": "the bot's Safari Zone decisions",
    "modules.story": "the story bot",
    "modules.built_in_plugins": "the bot's built-in plugins",
    "modules.game_cheats": "the cheats plugin, which writes game memory",
    "modules.watchdog": "the watchdog, which loads save states",
    "plugins.custom_modes": "the bot's modes (story_mode and friends)",
}

#: Top-level names the framework provides on its own (its folder is `sys.path[0]` in the bot
#: process). The gate ALSO discovers every top-level folder and module in the build root, because
#: any folder there imports as a namespace package (`tests`, `utility`, `logs`, ...).
STATIC_FRAMEWORK_ROOTS = frozenset(
    {"modules", "plugins", "pokebot", "updater", "requirements", "mgba", "profiles", "tools", "tests", "utility"}
)

# ---------------------------------------------------------------------------------- (a) library surfaces
PUBLIC = None  # a library surface of None = PUBLIC (see `public_reason`)


@dataclass(frozen=True)
class Library:
    """A standard-library module the play loop may import.

    `files`: the play-loop files that may import it (None = every one). `surface`: the attribute
    paths that may be used on it, each mapped to the files allowed (None = every one); PUBLIC (None)
    means any attribute `public_reason` accepts. `extra`: explicit additions to a PUBLIC surface."""

    files: frozenset[str] | None
    surface: dict[str, frozenset[str] | None] | None
    extra: dict[str, frozenset[str] | None] = field(default_factory=dict)


_INSTRUMENT_ONLY = frozenset({INSTRUMENT})
LIBRARIES: dict[str, Library] = {
    "__future__": Library(ANY_FILE, PUBLIC),
    "abc": Library(ANY_FILE, PUBLIC),
    "collections": Library(ANY_FILE, PUBLIC),
    "collections.abc": Library(ANY_FILE, PUBLIC),
    "contextlib": Library(ANY_FILE, PUBLIC),
    "dataclasses": Library(ANY_FILE, PUBLIC),
    "datetime": Library(ANY_FILE, PUBLIC),
    "enum": Library(ANY_FILE, PUBLIC),
    "functools": Library(ANY_FILE, PUBLIC, extra={"wraps": _INSTRUMENT_ONLY}),  # the instrument's wrappers
    "heapq": Library(ANY_FILE, PUBLIC),
    "itertools": Library(ANY_FILE, PUBLIC),
    "json": Library(ANY_FILE, PUBLIC),
    "math": Library(ANY_FILE, PUBLIC),
    "random": Library(ANY_FILE, PUBLIC),
    "re": Library(ANY_FILE, PUBLIC),
    "statistics": Library(ANY_FILE, PUBLIC),
    "textwrap": Library(ANY_FILE, PUBLIC),
    "time": Library(ANY_FILE, PUBLIC),
    "typing": Library(ANY_FILE, PUBLIC),
    "os.path": Library(ANY_FILE, PUBLIC),  # reached as `os.path.x` or `from os import path`
    "os": Library(
        ANY_FILE,
        {
            "environ.get": ANY_FILE,  # READ an option; `os.environ[...] = ` and `os.putenv` are not on it
            "sep": ANY_FILE,
            "getpid": _INSTRUMENT_ONLY,  # the verdict file names the process that wrote it
            "_exit": _INSTRUMENT_ONLY,  # the post-verdict tripwire: a SystemExit could be caught again
        },
    ),
    "pathlib": Library(ANY_FILE, {"Path": ANY_FILE, "PurePath": ANY_FILE}),
    "traceback": Library(ANY_FILE, {"format_exception": ANY_FILE, "format_exception_only": ANY_FILE, "format_exc": ANY_FILE}),
    "sys": Library(
        ANY_FILE,
        {
            # (R1, D12 (c)) the lifecycle's `finish` only (it narrowed from every file; the launcher is not judged here)
            "exit": frozenset({LIFECYCLE}),
            "stdout": ANY_FILE,
            "stderr": ANY_FILE,
            "version_info": ANY_FILE,
            # The hook APPENDS the repo root: never in front of the standard library (finding 4).
            "path.append": frozenset({HOOK_KEY}),
            "modules.values": _INSTRUMENT_ONLY,  # re-binding every copy of a wrapped memory function
            "modules.get": _INSTRUMENT_ONLY,  # `seal_module` finds the module object it seals
            "_getframe": _INSTRUMENT_ONLY,  # who called a door
            "monitoring": _INSTRUMENT_ONLY,  # the bot-code monitor (layer 3)
        },
    ),
    # The instrument: per-thread depth counters, the daemon exit watchdog that ends a finished
    # process a non-daemon framework thread would otherwise hold open (at once when the run finished
    # off the main thread), and (round 3) the FRAME FENCE: a re-entrant frame lock and the finishing
    # thread's id, so no other thread runs a frame while `finish` runs. The session: the interrupt
    # watch thread, which ends a run whose main thread is stuck after Ctrl+C. The lifecycle: the lock
    # that makes `finish` single-entry across threads.
    "threading": Library(
        frozenset({INSTRUMENT, SESSION, LIFECYCLE}),
        {
            "local": _INSTRUMENT_ONLY,
            "Timer": _INSTRUMENT_ONLY,
            "current_thread": _INSTRUMENT_ONLY,
            "main_thread": _INSTRUMENT_ONLY,
            "RLock": _INSTRUMENT_ONLY,
            "Thread": frozenset({SESSION}),
            "Lock": frozenset({LIFECYCLE}),
            "get_ident": frozenset({LIFECYCLE, INSTRUMENT}),
        },
    ),
    "types": Library(_INSTRUMENT_ONLY, {"FrameType": _INSTRUMENT_ONLY, "ModuleType": _INSTRUMENT_ONLY}),
    # Ctrl+C / Ctrl+Break handlers that only set a flag (finding 7). Process-wide, so the session only.
    "signal": Library(
        frozenset({SESSION}),
        {"signal": frozenset({SESSION}), "SIGINT": frozenset({SESSION}), "SIGBREAK": frozenset({SESSION})},
    ),
    # The hook's after-the-run record of the framework's listener list (finding 9).
    "atexit": Library(frozenset({HOOK_KEY}), {"register": frozenset({HOOK_KEY})}),
}
#: The launcher process may also manage files and child processes. It never runs inside the bot.
LAUNCHER_LIBRARIES = frozenset(LIBRARIES) | frozenset({"argparse", "hashlib", "psutil", "shutil", "subprocess", "threading"})


def _denied_values() -> dict[int, str]:
    """Objects a PUBLIC surface never hands out, wherever they are re-exported (identity, not name:
    `contextlib.wraps` IS `functools.wraps`)."""
    denied: dict[int, str] = {}
    for name in ("getattr", "setattr", "delattr", "hasattr", "vars", "globals", "locals", "eval", "exec",
                 "compile", "__import__", "breakpoint", "open", "help", "input"):
        value = getattr(builtins, name, None)
        if value is not None:
            denied[id(value)] = f"builtins.{name}"
    for owner, names in (
        (functools, ("update_wrapper", "wraps")),  # setattr / getattr by names given as data
        (typing, ("get_type_hints", "ForwardRef")),  # evaluate strings as code
        (contextlib, ("chdir",)),  # changes the framework process's working folder
    ):
        for name in names:
            value = getattr(owner, name, None)
            if value is not None:
                denied[id(value)] = f"{owner.__name__}.{name}"
    denied[id(CodeType)] = "types.CodeType"
    denied[id(FunctionType)] = "types.FunctionType"
    return denied


DENIED_VALUES = _denied_values()
#: A PUBLIC attribute whose `__module__` is one of these is refused: they resolve names, reach
#: frames or build code at run time.
DENIED_VALUE_MODULES = frozenset(
    {
        "operator", "_operator", "inspect", "importlib", "importlib._bootstrap", "importlib._bootstrap_external",
        "importlib.util", "importlib.machinery", "runpy", "pkgutil", "gc", "ctypes", "_ctypes", "pickle",
        "_pickle", "copyreg", "marshal", "code", "codeop", "pdb", "bdb", "trace", "sys",
    }
)


@functools.lru_cache(maxsize=None)
def public_reason(module: str, attribute: str) -> str | None:
    """None when `module.attribute` is on a PUBLIC surface, else why not."""
    if attribute.startswith("_"):
        return "a private name"
    try:
        loaded = importlib.import_module(module)
    except Exception as error:  # noqa: BLE001
        return f"the module could not be imported to check it ({type(error).__name__})"
    namespace = vars(loaded)
    if attribute not in namespace:
        return f"not an attribute of {module} in this interpreter"
    value = namespace[attribute]
    if isinstance(value, ModuleType):
        return "a module (a module is a door to every module it imports)"
    if id(value) in DENIED_VALUES:
        return f"a reflective function ({DENIED_VALUES[id(value)]})"
    try:
        owner = getattr(value, "__module__", None)
    except Exception:  # noqa: BLE001
        owner = None
    if isinstance(owner, str) and owner in DENIED_VALUE_MODULES:
        return f"it comes from `{owner}`, which resolves names, reaches frames or builds code at run time"
    return None


# ---------------------------------------------------------------------------------- (b) state changes
STATE_CHANGING_NAMES = frozenset(
    {
        # game memory
        "write_symbol", "write_to_save_block", "set_event_flag", "set_event_flag_by_number",
        "set_event_var", "write_bytes", "memmove", "raw_write", "rawWrite8", "rawWrite16",
        "rawWrite32", "busWrite8", "busWrite16", "busWrite32",
        # emulator and core state
        "load_save_state", "load_save_game", "load_state", "load_state_slot", "load_save",
        "load_temporary_save", "load_raw_state", "load_patch", "load_file", "load_rom", "load_bios",
        "reset", "loadState", "loadSave", "create_save_state", "advance_time",
        # frame advances
        "run_frame", "run_single_frame", "run_loop", "runFrame", "peek_frame", "get_task_look_ahead",
    }
)
INPUT_NAMES = frozenset(
    {
        "press_button", "hold_button", "release_button", "restore_held_buttons", "reset_held_buttons",
        "set_inputs", "set_keys", "add_keys", "clear_keys", "setKeys", "addKeys", "clearKeys",
    }
)

# ---------------------------------------------------------------------------------- (d) reflection
REFLECTION_NAMES = frozenset(
    {
        "__import__", "eval", "exec", "compile", "globals", "locals", "vars", "help", "breakpoint",
        "__builtins__", "__loader__", "__spec__", "get_type_hints", "ForwardRef", "import_module",
    }
)
#: `re.compile(...)` / `pattern.compile` are everywhere and harmless; every other reflection name is
#: refused as an attribute too (`enum.bltns.exec` would otherwise be an attribute named `exec`).
REFLECTION_ATTRIBUTE_EXCEPTIONS = frozenset({"compile"})
ATTRIBUTE_READERS = frozenset({"getattr", "hasattr"})
ATTRIBUTE_WRITERS = frozenset({"setattr", "delattr"})
#: Attribute names refused on ANY object: the import system, tracing hooks, and frame internals
#: (a frame's `f_globals` is a module namespace, i.e. every name the framework imported).
FORBIDDEN_ATTRIBUTES = frozenset(
    {
        "modules", "meta_path", "path_hooks", "path_importer_cache", "settrace", "setprofile",
        "settrace_all_threads", "setprofile_all_threads", "addaudithook", "breakpointhook", "monitoring",
        "f_globals", "f_locals", "f_builtins", "f_back", "f_code", "f_trace", "f_trace_lines",
        "f_trace_opcodes", "tb_frame", "tb_next", "gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame",
        "ag_code", "get_type_hints", "import_module",
    }
)
FORMAT_METHODS = frozenset({"format", "format_map"})
ALLOWED_DUNDER_NAMES = frozenset({"__name__", "__file__", "__doc__", "__all__"})
ALLOWED_DUNDER_ATTRIBUTES = frozenset({"__name__", "__qualname__", "__doc__", "__init__"})
ALLOWED_DUNDER_STRINGS = ALLOWED_DUNDER_NAMES | ALLOWED_DUNDER_ATTRIBUTES | {"__main__"}

MODULE_STRING = re.compile(r"^(?:modules|plugins|mgba)(?:\.[A-Za-z_]\w*)+$")
TEST_SIDE_STRING = re.compile(r"^ai_player\.gates(?:\.|$)")
PRIVATE_STRING = re.compile(r"^_[A-Za-z0-9]\w*$")

# ---------------------------------------------------------------------------------- (e) files
SOURCE_SUFFIXES = tuple(sorted(set(importlib.machinery.SOURCE_SUFFIXES) | {".py", ".pyw"}))
OPAQUE_SUFFIXES = tuple(
    sorted(set(importlib.machinery.BYTECODE_SUFFIXES) | set(importlib.machinery.EXTENSION_SUFFIXES) | {".pyc", ".pyo", ".pyd", ".so"})
)
#: The only names CPython writes into `__pycache__`: `<module>.<cache tag>[.opt-N].pyc`.
CACHE_FILE = re.compile(r"^(?P<stem>[A-Za-z_]\w*)\.(?P<tag>[A-Za-z0-9_-]+?)(?:\.opt-(?P<opt>[12]))?\.pyc$")

# ---------------------------------------------------------------------------------- (f) side effects
#: The files that may write files, and what they write.
FILE_WRITERS: dict[str, str] = {
    RUNLOG: "the AI's own logs, <run_dir>/ai_player.log and the action log <run_dir>/actions.jsonl",
    INSTRUMENT: "the verdict file, <run_dir>/purity.json",
}
#: `pathlib.Path` methods that create, change, move or delete files (`write_bytes` is already rule b).
#: The `os` and `shutil` equivalents need no entry: they are not on any surface the play loop may use.
#: Deliberately NOT here: `remove` and `replace`, which lists and strings use all the time
#: (`.replace(target)` with one argument, the file move, is caught by its own check).
FILE_WRITE_NAMES = frozenset(
    {"write_text", "mkdir", "touch", "unlink", "rmdir", "rename", "symlink_to", "hardlink_to", "link_to", "chmod", "lchmod"}
)
READ_MODE_CHARACTERS = frozenset("rbt")

# ---------------------------------------------------------------------------------- (g) pinned surfaces
#: Each host module's exported names. A new host module, or a new export, is a gate change.
HOST_EXPORTS: dict[str, frozenset[str]] = {
    "host/__init__.py": frozenset(),
    INSTRUMENT: frozenset({"Attribution", "Guarded", "PurityCounters", "Sealed", "seal_module"}),
    CONTROLLER: frozenset({"BUTTONS", "MAX_ACTION_FRAMES", "Controller", "ControllerError"}),
    ISOLATION: frozenset({"GuardListener", "ListenerIsolation", "describe"}),
    LIFECYCLE: frozenset(
        {
            "EXIT_BRAIN_RETURNED", "EXIT_CRASH", "EXIT_FRAME_BUDGET", "EXIT_INTERRUPTED", "EXIT_OK",
            "EXIT_PARKED", "EXIT_PURITY_BREACH", "EXIT_REFUSED", "EXIT_WALL_CLOCK", "Lifecycle",
        }
    ),
    SESSION: frozenset({"Session", "start_session"}),
    EYES: frozenset({"MAP_OFFSET", "FrameworkEyes"}),
}
#: sha256 of `host/attribution.py` (line endings normalised to LF). The instrument is exempt from
#: rules b, d and f, so this gate cannot judge what it does; it pins WHAT IT IS instead. After a
#: change: re-read the whole file (no public method or attribute may hand out `context`, the emulator,
#: `modules.memory`, `ffi` or a frame), then set this to `--instrument-digest`'s output.
INSTRUMENT_SHA256 = "4ba24f27f519d53b66d6e38119338b7ee7f46795554cb71f910b93845e9b0103"
#: The instrument's control methods and the only files that may name them. The finalizers: only the
#: lifecycle's `finish` (the instrument also refuses any other caller at run time). The isolation
#: check: only the session, which hands it the real guard (a second call is refused and counted).
INSTRUMENT_CONTROL_NAMES: dict[str, frozenset[str]] = {
    "finalize_audit": frozenset({LIFECYCLE}),
    "write_verdict_file": frozenset({LIFECYCLE}),
    "arm_exit_watchdog": frozenset({LIFECYCLE}),
    "watch_guard": frozenset({SESSION}),
}


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _brain_reason(module: str) -> str | None:
    for prefix, reason in FORBIDDEN_PREFIXES.items():
        if module == prefix or module.startswith(prefix + "."):
            return f"{prefix} is {reason}"
    return None


def _format_is_plain(template: str, depth: int = 0) -> bool:
    """True when a format template reads no attribute and no index (`{0.x}`, `{0[x]}`), here or in
    a nested format spec."""
    if depth > 3:
        return False
    try:
        for _, field_name, spec, _ in string.Formatter().parse(template):
            if field_name is not None and ("." in field_name or "[" in field_name):
                return False
            if spec and not _format_is_plain(spec, depth + 1):
                return False
    except ValueError:
        return False
    return True


def instrument_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def discover_framework_roots(build_root: Path | None) -> frozenset[str]:
    """Every top-level name the bot process could import from its own folder."""
    roots = set(STATIC_FRAMEWORK_ROOTS)
    if build_root is not None and build_root.is_dir():
        for entry in build_root.iterdir():
            if entry.is_dir() and entry.name.isidentifier() and not _is_dunder(entry.name):
                roots.add(entry.name)
            elif entry.is_file() and entry.name.endswith(SOURCE_SUFFIXES + OPAQUE_SUFFIXES):
                stem = entry.name.split(".", 1)[0]
                if stem.isidentifier():
                    roots.add(stem)
    return frozenset(roots)


def _is_link(path: Path) -> bool:
    isjunction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or bool(isjunction and isjunction(path))


# ---------------------------------------------------------------------------------- results


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"  FAIL {self.file}:{self.line} [{self.rule}] {self.message}"


@dataclass
class GateResult:
    violations: list[Finding] = field(default_factory=list)
    allowed_imports: list[str] = field(default_factory=list)
    scanned: list[str] = field(default_factory=list)
    roles: dict[str, str] = field(default_factory=dict)
    test_side: list[str] = field(default_factory=list)
    exports: dict[str, list[str]] = field(default_factory=dict)
    framework_roots: frozenset[str] = frozenset()
    build_root_seen: bool = False
    caches_checked: int = 0
    caches_stale: int = 0
    caches_other_interpreter: int = 0
    instrument_sha256: str = ""

    @property
    def passed(self) -> bool:
        return not self.violations and bool(self.scanned)


@dataclass
class ModuleFacts:
    """What an ai_player module exports, and whether each export is a name it really defines."""

    all_names: list[str] | None
    all_line: int
    defined: set[str]
    imported: set[str]


def module_facts(tree: ast.Module) -> ModuleFacts:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    defined: set[str] = set()
    all_names: list[str] | None = None
    all_line = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
            continue
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id == "__all__":
                all_line = node.lineno
                if isinstance(value, (ast.List, ast.Tuple)) and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str) for e in value.elts
                ):
                    all_names = [e.value for e in value.elts]
                else:
                    all_names = []
                continue
            uses_import = any(isinstance(n, ast.Name) and n.id in imported for n in ast.walk(value))
            if not uses_import:
                defined.add(target.id)
    return ModuleFacts(all_names, all_line, defined - imported, imported)


def _string_tuple(tree: ast.Module, name: str) -> tuple[str, ...] | None:
    """The value of a top-level `NAME = ("a", "b", ...)`, or None."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            value = node.value
            if isinstance(value, (ast.Tuple, ast.List)) and all(
                isinstance(e, ast.Constant) and isinstance(e.value, str) for e in value.elts
            ):
                return tuple(e.value for e in value.elts)
    return None


# ---------------------------------------------------------------------------------- the scan


@dataclass(frozen=True)
class Binding:
    """What an imported local name stands for. kind: "door" (a framework object), "library" (a
    library module, or a partial path into one: `from os import environ` -> ("os", ("environ",))) or
    "object" (anything else imported: a class, a function, a constant)."""

    kind: str
    door_paths: frozenset[str] | None = None
    library: str = ""
    prefix: tuple[str, ...] = ()


class _Context:
    """Shared state of one scan: the package being judged and what its modules export."""

    def __init__(self, package_dir: Path, framework_roots: frozenset[str], result: GateResult) -> None:
        self.package_dir = package_dir
        self.framework_roots = framework_roots
        self.result = result
        self.module_keys: set[str] = set()  # every file of the package this scan reads as a module
        self._facts: dict[Path, ModuleFacts | None] = {}

    def door(self, module: str, name: str | None, key: str) -> Door | None:
        for door in DOORS:
            if door.module == module and door.name == name and key in door.files:
                return door
        return None

    def module_file(self, module: str) -> Path | None:
        """`ai_player.host.controller` -> its source file in the package being judged, if that is
        a file this scan reads (never one under `__pycache__`, the test side, or a dunder folder)."""
        parts = module.split(".")[1:]
        if any(not part.isidentifier() or _is_dunder(part) for part in parts):
            return None
        candidates: list[Path] = []
        if parts:
            base = self.package_dir.joinpath(*parts)
            candidates += [base.with_name(base.name + suffix) for suffix in SOURCE_SUFFIXES]
        else:
            base = self.package_dir
        candidates.append(base / "__init__.py")
        for candidate in candidates:
            if candidate.is_file():
                key = candidate.relative_to(self.package_dir).as_posix()
                return candidate if key in self.module_keys else None
        return None

    def facts(self, path: Path) -> ModuleFacts | None:
        if path not in self._facts:
            try:
                self._facts[path] = module_facts(ast.parse(path.read_bytes(), filename=str(path)))
            except (SyntaxError, OSError, UnicodeDecodeError, ValueError):
                self._facts[path] = None
        return self._facts[path]


class _FileScanner(ast.NodeVisitor):
    def __init__(self, ctx: _Context, key: str, display: str, role: str, package: list[str], tree: ast.Module) -> None:
        self.ctx = ctx
        self.key = key
        self.display = display
        self.role = role  # "play", "instrument" or "launcher"
        self.is_hook = key == HOOK_KEY
        self.exempt = role == "instrument"  # rules (b), (d) and (f)
        self.writes_files = key in FILE_WRITERS or role == "launcher"
        self.package = package
        self.parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                self.parents[child] = parent
        self.bindings: dict[str, Binding] = {}
        self._bind_imports(tree)

    # ------------------------------------------------------------------ helpers
    def fail(self, node: ast.AST, rule: str, message: str) -> None:
        self.ctx.result.violations.append(Finding(self.display, getattr(node, "lineno", 0), rule, message))

    @property
    def judges_surfaces(self) -> bool:
        return self.role != "launcher"

    @property
    def judges_effects(self) -> bool:
        return self.role == "play"

    def _absolute(self, node: ast.ImportFrom) -> str:
        """`from .x import y` in ai_player/host/z.py -> `ai_player.host.x`. Without this a
        relative import could reach the test side (or, from the hook, the bot's modes) unseen."""
        if node.level == 0:
            return node.module or ""
        keep = len(self.package) - (node.level - 1)
        if keep <= 0:
            return ""
        return ".".join(self.package[:keep] + ([node.module] if node.module else []))

    def _library(self, module: str) -> str:
        """'ok', 'elsewhere' (listed, but not for this file) or 'no'."""
        if self.role == "launcher":
            return "ok" if module in LAUNCHER_LIBRARIES else "no"
        library = LIBRARIES.get(module)
        if library is None:
            return "no"
        return "ok" if library.files is ANY_FILE or self.key in library.files else "elsewhere"

    def _surface_status(self, module: str, path: list[str]) -> str:
        """Is `module.<path>` on the surface this file may use? 'ok' (the path reached an allowed
        attribute: what follows is ordinary object access), 'partial' (a prefix of one) or 'no'."""
        library = LIBRARIES[module]
        explicit = library.surface if library.surface is not PUBLIC else library.extra
        partial = False
        for entry, files in explicit.items():
            if files is not ANY_FILE and self.key not in files:
                continue
            parts = entry.split(".")
            if path[: len(parts)] == parts:
                return "ok"
            if parts[: len(path)] == path:
                partial = True
        if partial:
            return "partial"
        if library.surface is PUBLIC and len(path) == 1 and public_reason(module, path[0]) is None:
            return "ok"
        return "no"

    def _why_not(self, module: str, attribute: str) -> str:
        if LIBRARIES[module].surface is PUBLIC:
            return public_reason(module, attribute) or "not allowed for this file"
        listed = sorted(e for e, files in LIBRARIES[module].surface.items() if files is ANY_FILE or self.key in files)
        return f"this file may use only {', '.join(f'{module}.{e}' for e in listed) or 'nothing'}"

    def _bind_imports(self, tree: ast.Module) -> None:
        """First pass: what every imported local name stands for (uses may precede a lazy import
        lexically, so this cannot be done during the main walk)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] == "ai_player":
                        continue
                    door = self.ctx.door(alias.name, None, self.key)
                    if door is not None and alias.asname:
                        self.bindings[alias.asname] = Binding("door", door_paths=door.files[self.key])
                    elif self.judges_surfaces and self._library(alias.name) == "ok":
                        if alias.asname:
                            self.bindings[alias.asname] = Binding("library", library=alias.name)
                        else:
                            top = alias.name.split(".", 1)[0]
                            if top in LIBRARIES:
                                self.bindings[top] = Binding("library", library=top)
            elif isinstance(node, ast.ImportFrom):
                base = self._absolute(node)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    door = self.ctx.door(base, alias.name, self.key) or self.ctx.door(f"{base}.{alias.name}", None, self.key)
                    if door is not None:
                        self.bindings[local] = Binding("door", door_paths=door.files[self.key])
                    elif self.judges_surfaces and base != "__future__" and self._library(base) == "ok":
                        sub = f"{base}.{alias.name}"
                        if sub in LIBRARIES:
                            self.bindings[local] = Binding("library", library=sub)
                        elif self._surface_status(base, [alias.name]) == "partial":
                            self.bindings[local] = Binding("library", library=base, prefix=(alias.name,))
                        else:
                            self.bindings[local] = Binding("object")
                    else:
                        self.bindings[local] = Binding("object")

    def _chain(self, node: ast.AST) -> list[str]:
        chain: list[str] = []
        current: ast.AST = node
        parent = self.parents.get(current)
        while isinstance(parent, ast.Attribute) and parent.value is current:
            chain.append(parent.attr)
            current = parent
            parent = self.parents.get(current)
        return chain

    def _chain_top(self, node: ast.AST) -> ast.AST:
        current: ast.AST = node
        parent = self.parents.get(current)
        while isinstance(parent, ast.Attribute) and parent.value is current:
            current = parent
            parent = self.parents.get(current)
        return current

    @staticmethod
    def _root_name(node: ast.AST) -> ast.Name | None:
        """`a.b[c].d` -> the Name `a` (through attributes and subscripts only)."""
        current = node
        for _ in range(64):
            if isinstance(current, ast.Name):
                return current
            if isinstance(current, (ast.Attribute, ast.Subscript)):
                current = current.value
                continue
            return None
        return None

    def _check_name_text(self, node: ast.AST, name: str, how: str) -> None:
        """Rules (b), (d), (f), (g) on an identifier, however it appears (name, attribute, import,
        match pattern, getattr constant, string)."""
        if self.exempt:
            return
        if name in STATE_CHANGING_NAMES:
            self.fail(node, "b", f"{how} `{name}`: the AI must not write memory, load or reset the emulator, or advance frames")
        if name in INPUT_NAMES and self.key != CONTROLLER:
            self.fail(node, "b", f"{how} `{name}`: only {CONTROLLER} may touch the buttons")
        # The builtins are reflection; an ATTRIBUTE that shares a name is judged in _check_attribute.
        if name in REFLECTION_NAMES and not isinstance(node, ast.Attribute):
            self.fail(node, "d", f"{how} `{name}`: it imports, evaluates or looks up names at run time")
        if name in FORBIDDEN_ATTRIBUTES:
            self.fail(node, "d", f"{how} `{name}`: the import system, tracing hooks and frames are off limits")
        if name in INSTRUMENT_CONTROL_NAMES and self.key not in INSTRUMENT_CONTROL_NAMES[name]:
            owners = ", ".join(sorted(INSTRUMENT_CONTROL_NAMES[name]))
            self.fail(node, "g", f"{how} `{name}`: only {owners} may name this instrument control (the finalizers "
                      f"belong to the lifecycle's finish, the isolation check to the session)")
        if (
            self.judges_effects
            and not self.writes_files
            and name in FILE_WRITE_NAMES
            and not isinstance(node, ast.Constant)
        ):
            self.fail(node, "f", f"{how} `{name}`: only {', '.join(sorted(FILE_WRITERS))} may create, move or delete files")

    def _check_attribute(self, node: ast.AST, attribute: str, base: ast.AST | None, how: str) -> None:
        """Rule (d) on an attribute name used on `base` (None: a match pattern or an unknown object)."""
        if self.exempt:
            return
        if _is_dunder(attribute):
            if attribute not in ALLOWED_DUNDER_ATTRIBUTES:
                self.fail(node, "d", f"{how} `.{attribute}`: dunder attributes reach the object model")
        elif attribute.startswith("_") and not (isinstance(base, ast.Name) and base.id in ("self", "cls")):
            self.fail(node, "d", f"{how} the private attribute `.{attribute}` of another object (only `self._x`)")
        if attribute in REFLECTION_NAMES and attribute not in REFLECTION_ATTRIBUTE_EXCEPTIONS:
            self.fail(node, "d", f"{how} `.{attribute}`: it imports, evaluates or looks up names at run time")

    # ------------------------------------------------------------------ (a), (c): imports
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(node, alias.name, alias.asname)
        self.generic_visit(node)

    def _check_import(self, node: ast.AST, name: str, asname: str | None) -> None:
        shown = f"import {name}" + (f" as {asname}" if asname else "")
        top = name.split(".", 1)[0]
        if top == "ai_player":
            if name == TEST_SIDE_MODULE or name.startswith(TEST_SIDE_MODULE + "."):
                self.fail(node, "c", f"`{shown}` imports test-side code into the play loop")
            else:
                self.fail(node, "a", f"`{shown}` binds an ai_player module object; import names with "
                          f"`from {name} import Name`, so only names in its __all__ can cross")
            return
        library = self._library(name)
        if library == "ok":
            if self.judges_surfaces and asname is None and top not in LIBRARIES:
                self.fail(node, "a", f"`{shown}` binds `{top}`, which is not itself an allowlisted library")
            return
        if library == "elsewhere":
            self.fail(node, "a", f"`{shown}`: {name} is allowlisted only for {sorted(LIBRARIES[name].files or [])}")
            return
        reason = _brain_reason(name)
        if reason:
            self.fail(node, "a", f"`{shown}` reaches the bot's brain: {reason}")
            return
        if self.role == "launcher" and top in self.ctx.framework_roots:
            self.fail(node, "c", f"`{shown}`: the launcher runs outside the framework and may not import it")
            return
        door = self.ctx.door(name, None, self.key)
        if door is not None:
            if asname is None:
                self.fail(node, "a", f"`{shown}` binds the whole `{top}` package, from which every loaded framework "
                          f"module is one attribute away; write `import {name} as <alias>`")
            else:
                self.ctx.result.allowed_imports.append(f"  ok   {self.display}:{node.lineno} {shown}")
            return
        where = "a framework import" if top in self.ctx.framework_roots else "an import"
        self.fail(node, "a", f"`{shown}` is {where} that is not on any allowlist for this file")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = self._absolute(node)
        shown_base = node.module if node.level == 0 else "." * node.level + (node.module or "")
        for alias in node.names:
            shown = f"from {shown_base} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
            self._check_name_text(node, alias.name, "imports")
            if alias.name in PLAY_LOOP_EXIT_CLASSES and in_play_loop(self.key):
                self._fail_exit(node, f"imports `{alias.name}`")
            if base == "__future__":
                continue
            if alias.name == "*":
                self.fail(node, "a", f"`{shown}`: a star import binds names nobody listed")
                continue
            self._check_from(node, base, alias.name, shown)
        self.generic_visit(node)

    def _check_from(self, node: ast.ImportFrom, base: str, name: str, shown: str) -> None:
        if not base:
            self.fail(node, "a", f"`{shown}` is a relative import above the top of its package")
            return
        full = f"{base}.{name}"
        top = base.split(".", 1)[0]
        if top == "ai_player":
            self._check_own_import(node, base, name, shown)
            return
        library = self._library(base)
        if library == "ok":
            if self.judges_surfaces:
                if full in LIBRARIES:
                    if self._library(full) != "ok":
                        self.fail(node, "a", f"`{shown}`: {full} is not allowlisted for this file")
                elif self._surface_status(base, [name]) == "no":
                    self.fail(node, "a", f"`{shown}`: `{name}` is not on the surface of `{base}` this file may "
                              f"use ({self._why_not(base, name)})")
            return
        if library == "elsewhere":
            self.fail(node, "a", f"`{shown}`: {base} is allowlisted only for {sorted(LIBRARIES[base].files or [])}")
            return
        reason = _brain_reason(full) or _brain_reason(base)
        if reason:
            self.fail(node, "a", f"`{shown}` reaches the bot's brain: {reason}")
            return
        if self.role == "launcher" and top in self.ctx.framework_roots:
            self.fail(node, "c", f"`{shown}`: the launcher runs outside the framework and may not import it")
            return
        if self.ctx.door(base, name, self.key) or self.ctx.door(full, None, self.key):
            self.ctx.result.allowed_imports.append(f"  ok   {self.display}:{node.lineno} {shown}")
            return
        where = "a framework import" if top in self.ctx.framework_roots else "an import"
        self.fail(node, "a", f"`{shown}` is {where} that is not on any allowlist for this file")

    def _check_own_import(self, node: ast.ImportFrom, base: str, name: str, shown: str) -> None:
        full = f"{base}.{name}"
        for module in (base, full):
            if module == TEST_SIDE_MODULE or module.startswith(TEST_SIDE_MODULE + "."):
                self.fail(node, "c", f"`{shown}` imports test-side code into the play loop")
                return
        if self.role != "launcher" and (base in LAUNCHER_MODULES or full in LAUNCHER_MODULES):
            self.fail(node, "c", f"`{shown}`: the play loop may not import the launcher side")
            return
        if self.key in BRAIN_FILES and any(m == HOST_MODULE or m.startswith(HOST_MODULE + ".") for m in (base, full)):
            self.fail(node, "c", f"`{shown}`: the brain is framework-free; it sees the game only through its "
                      f"abstract interfaces and may not import the host side")
            return
        path = self.ctx.module_file(base)
        facts = self.ctx.facts(path) if path is not None else None
        if facts is None:
            self.fail(node, "a", f"`{shown}`: {base} is not a module this gate read (a path through `__pycache__` "
                      f"or another dunder folder, a missing file, or one that does not parse)")
            return
        if facts.all_names is None:
            self.fail(node, "a", f"`{shown}`: {base} declares no __all__, so nothing may be imported from it")
            return
        if name not in facts.all_names:
            self.fail(node, "a", f"`{shown}`: `{name}` is not in {base}.__all__ (a submodule, an imported name, "
                      f"or a private one)")
            return
        if name not in facts.defined:
            self.fail(node, "a", f"`{shown}`: `{name}` is in {base}.__all__ but is not a name {base} defines "
                      f"(a re-export)")

    # ------------------------------------------------------------------ names
    def visit_Name(self, node: ast.Name) -> None:
        name = node.id
        self._check_name_text(node, name, "uses the name")
        if name in PLAY_LOOP_EXIT_NAMES and isinstance(node.ctx, ast.Load) and in_play_loop(self.key):
            self.fail(node, "b", f"uses `{name}`: the play loop never ends or restarts its own process, and never catches "
                      f"its end (USER RULING 52; the lifecycle ends the run when the brain RETURNS its reason)")
        if not self.exempt:
            if name in ATTRIBUTE_READERS:
                self._check_attribute_reader(node)
            elif name in ATTRIBUTE_WRITERS:
                self.fail(node, "d", f"uses `{name}`: setting or deleting attributes by name is refused (assign them)")
            elif _is_dunder(name) and name not in ALLOWED_DUNDER_NAMES:
                self.fail(node, "d", f"uses the name `{name}`")
            if name == "open" and self.judges_effects and not self.writes_files and isinstance(node.ctx, ast.Load):
                self._check_open(node, mode_index=1)
        binding = self.bindings.get(name)
        if binding is not None and isinstance(node.ctx, ast.Load):
            if binding.kind == "door":
                self._check_door_use(node, binding)
            elif binding.kind == "library":
                self._check_library_use(node, binding)
        self.generic_visit(node)

    # ------------------------------------------------------------------ (b): the play loop's own end (R1 + R2 follow-up, D1)
    def _fail_exit(self, node: ast.AST, what: str) -> None:
        self.fail(node, "b", f"{what}: the play loop never discards, swallows or holds back the end of its own process "
                  f"(USER RULING 52; the lifecycle ends the run when the brain RETURNS its reason)")

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None and in_play_loop(self.key):
            self._fail_exit(node, "a bare `except:` catches the process's end")
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        if in_play_loop(self.key):
            for statement in node.finalbody:
                self._check_finally(statement, in_loop=False)
        self.generic_visit(node)

    visit_TryStar = visit_Try

    def _check_finally(self, node: ast.AST, in_loop: bool) -> None:
        """A `return`, `yield`, `yield from` or `await` reached from a `finally` body (not through a nested scope), and a
        `break` or `continue` reached the same way outside a loop nested in it, discard or hold back the exit in flight;
        a `raise` or an `assert` reached the same way replaces it (U2 spec D16)."""
        if isinstance(node, FINALLY_SCOPES):
            return
        if isinstance(node, ast.Return) or (isinstance(node, (ast.Break, ast.Continue)) and not in_loop):
            self._fail_exit(node, f"a `{type(node).__name__.lower()}` in a `finally` discards the exit in flight")
        if isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await)):
            self._fail_exit(node, "a `yield` or `await` in a `finally` holds back the exit in flight (its caller gets "
                            "a frame after the end began)")
        if isinstance(node, (ast.Raise, ast.Assert)):
            # U2 spec 2026-10-30 D16 (RV-7): a raise (or a failing assert, which raises AssertionError) reached from a
            # `finally` body REPLACES the exit in flight, exactly as a `return` discards it; a try nested in the
            # `finally` is no shelter (its handlers and body are reached from the `finally` too)
            self._fail_exit(node, "a `raise` (or a failing `assert`) in a `finally` replaces the exit in flight")
        if isinstance(node, FINALLY_LOOPS):
            # the loop's own body owns its break/continue; its `else`, target, iterable and test do not
            for child in node.body:
                self._check_finally(child, in_loop=True)
            for child in [*node.orelse, *(getattr(node, field) for field in ("target", "iter", "test") if hasattr(node, field))]:
                self._check_finally(child, in_loop)
            return
        for child in ast.iter_child_nodes(node):
            self._check_finally(child, in_loop)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in EXIT_METHODS and in_play_loop(self.key):
            self._fail_exit(node, f"defines `{node.name}`, which can swallow whatever passes through its `with`")
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _check_attribute_reader(self, node: ast.Name) -> None:
        parent = self.parents.get(node)
        direct = (
            isinstance(parent, ast.Call)
            and parent.func is node
            and len(parent.args) >= 2
            and not any(isinstance(arg, ast.Starred) for arg in parent.args)
            and isinstance(parent.args[1], ast.Constant)
            and isinstance(parent.args[1].value, str)
        )
        if not direct:
            self.fail(node, "d", f"`{node.id}` is used other than as `{node.id}(obj, 'constant name')`: "
                      f"an attribute name chosen at run time could be anything")
            return
        # `getattr(obj, 'name')` IS `obj.name`: judge it exactly the same way.
        attribute = parent.args[1].value
        how = f"`{node.id}(..., {attribute!r})` reaches"
        self._check_attribute(parent, attribute, parent.args[0], how)
        if attribute in FORMAT_METHODS:
            self.fail(parent, "d", f"{how} `.{attribute}`, whose template cannot be checked through {node.id}")
        if self.judges_effects and not self.writes_files and attribute in (FILE_WRITE_NAMES | {"open", "replace"}):
            self.fail(parent, "f", f"{how} `.{attribute}`: only {', '.join(sorted(FILE_WRITERS))} may write files")

    def _is_attribute_reader_name(self, node: ast.Constant) -> bool:
        """Is this string the constant name in a direct `getattr(obj, 'name')` / `hasattr(...)`?"""
        parent = self.parents.get(node)
        return (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Name)
            and parent.func.id in ATTRIBUTE_READERS
            and len(parent.args) >= 2
            and parent.args[1] is node
        )

    def _check_door_use(self, node: ast.Name, binding: Binding) -> None:
        top = self._chain_top(node)
        stored = isinstance(top, ast.Attribute) and isinstance(top.ctx, (ast.Store, ast.Del))
        allowed = binding.door_paths
        if allowed is None:
            if stored and self.judges_effects:
                self.fail(node, "f", f"assigns to an attribute of the framework's `{node.id}`")
            return
        chain = ".".join(self._chain(node))
        want = chain + "=" if stored else chain
        if want not in allowed:
            used = f"{node.id}.{chain}" if chain else node.id
            paths = ", ".join(f"{node.id}.{path}" for path in sorted(allowed))
            verb = "assigns" if stored else "uses"
            self.fail(node, "a", f"{verb} `{used}`: this file may only use {paths} (a framework object is walked "
                      f"only along its door's paths; '=' marks one it may assign)")

    def _check_library_use(self, node: ast.Name, binding: Binding) -> None:
        library = binding.library
        prefix = list(binding.prefix)
        walked = [node.id]
        resolved = False
        for attribute in self._chain(node):
            walked.append(attribute)
            sub = f"{library}.{attribute}"
            if not prefix and sub in LIBRARIES:
                if self._library(sub) != "ok":
                    self.fail(node, "a", f"uses `{'.'.join(walked)}`: {sub} is not allowlisted for this file")
                    return
                library = sub
                continue
            prefix.append(attribute)
            status = self._surface_status(library, prefix)
            if status == "ok":
                resolved = True
                break
            if status == "no":
                self.fail(node, "a", f"uses `{'.'.join(walked)}`: not on the surface of `{library}` this file may use "
                          f"({self._why_not(library, prefix[0]) if len(prefix) == 1 else 'not a listed path'})")
                return
        if not resolved:
            self.fail(node, "a", f"uses `{'.'.join(walked)}` as a value: a library module, or part of one, may only "
                      f"be used as `<module>.<allowed attribute>` (passed around it hands out everything it imports)")
            return
        top = self._chain_top(node)
        if self.judges_effects and isinstance(top, ast.Attribute) and isinstance(top.ctx, (ast.Store, ast.Del)):
            self.fail(node, "f", f"assigns to `{'.'.join([node.id, *self._chain(node)])}`: the framework shares this "
                      f"library, so changing it changes the framework")

    def _check_open(self, func: ast.AST, mode_index: int) -> None:
        """`open(path)` / `path.open()` may only READ outside the file writers."""
        parent = self.parents.get(func)
        if not (isinstance(parent, ast.Call) and parent.func is func):
            self.fail(func, "f", "uses `open` other than as a direct call with a constant read mode")
            return
        if any(isinstance(arg, ast.Starred) for arg in parent.args) or any(k.arg is None for k in parent.keywords):
            self.fail(func, "f", "calls `open` with unpacked arguments: its mode cannot be checked")
            return
        mode: ast.expr | None = parent.args[mode_index] if len(parent.args) > mode_index else None
        for keyword in parent.keywords:
            if keyword.arg == "mode":
                mode = keyword.value
        if mode is None:
            return  # the default mode reads
        if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and set(mode.value) <= READ_MODE_CHARACTERS:
            return
        self.fail(func, "f", f"opens a file in a mode that is not a constant read mode: only "
                  f"{', '.join(sorted(FILE_WRITERS))} may write files")

    # ------------------------------------------------------------------ attributes, match patterns
    def visit_Attribute(self, node: ast.Attribute) -> None:
        attribute = node.attr
        self._check_name_text(node, attribute, "uses the attribute")
        self._check_attribute(node, attribute, node.value, "uses")
        if attribute in PLAY_LOOP_EXIT_CLASSES and isinstance(node.ctx, ast.Load) and in_play_loop(self.key):
            self._fail_exit(node, f"uses `.{attribute}`")
        if not self.exempt and attribute in FORMAT_METHODS:
            self._check_format(node)
        if self.judges_effects and not self.writes_files:
            if attribute == "open":
                self._check_open(node, mode_index=0)
            elif attribute == "replace":
                self._check_replace(node)
        if self.judges_effects and isinstance(node.ctx, (ast.Store, ast.Del)):
            self._check_store_on_import(node)
        self.generic_visit(node)

    def _check_format(self, node: ast.Attribute) -> None:
        parent = self.parents.get(node)
        receiver = node.value
        plain = isinstance(receiver, ast.Constant) and isinstance(receiver.value, str) and _format_is_plain(receiver.value)
        if not (isinstance(parent, ast.Call) and parent.func is node and plain):
            self.fail(node, "d", f"uses `.{node.attr}` on a template that is not a constant without attribute or index "
                      f"fields: `'{{0._x}}'.{node.attr}(obj)` reads attributes by name at run time (use an f-string)")

    def _check_replace(self, node: ast.Attribute) -> None:
        parent = self.parents.get(node)
        if not (isinstance(parent, ast.Call) and parent.func is node):
            self.fail(node, "f", "uses `.replace` other than as a call: `Path.replace` moves a file")
            return
        unpacked = any(isinstance(arg, ast.Starred) for arg in parent.args) or any(k.arg is None for k in parent.keywords)
        one_argument = len(parent.args) + len(parent.keywords) == 1
        if unpacked or one_argument or any(k.arg == "target" for k in parent.keywords):
            self.fail(node, "f", "calls `.replace(target)` with one argument, which is `Path.replace` (a file move; "
                      "`str.replace` takes two): only the file writers may move files")

    def _check_store_on_import(self, node: ast.Attribute) -> None:
        """Assigning or deleting an attribute of anything imported changes code other modules run.
        (Doors and libraries are judged, with their paths, in their own checks.)"""
        root = self._root_name(node.value)
        if root is None:
            return
        binding = self.bindings.get(root.id)
        if binding is not None and binding.kind == "object":
            self.fail(node, "f", f"assigns to `.{node.attr}` of the imported `{root.id}`: changing another module's "
                      f"object changes code that module (or the framework) runs")

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # No exemption for the hook any more: it may only APPEND to `sys.path` (finding 4).
        if self.judges_effects and isinstance(node.ctx, (ast.Store, ast.Del)):
            root = self._root_name(node.value)
            binding = self.bindings.get(root.id) if root is not None else None
            if binding is not None:
                self.fail(node, "f", f"assigns to an item of the imported `{root.id}`: changing another module's (or the "
                          f"framework's) data changes code it runs")
        self.generic_visit(node)

    def visit_MatchClass(self, node: ast.MatchClass) -> None:
        # `case object(name=x)` reads `subject.name`: the attribute names are plain strings in the
        # AST, so without this they would be an unchecked getattr.
        for attribute in node.kwd_attrs:
            self._check_name_text(node, attribute, "matches the attribute")
            self._check_attribute(node, attribute, None, "matches")
            if self.judges_effects and not self.writes_files and attribute in ("open", "replace"):
                self.fail(node, "f", f"matches the attribute `{attribute}`: its arguments cannot be checked through a pattern")
            if not self.exempt and attribute in FORMAT_METHODS:
                self.fail(node, "d", f"matches the attribute `{attribute}`: a bound format method's template cannot be checked")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # `__slots__ = ("_a", "_b")` directly in a class body declares the class's OWN attributes, the
        # very names `self._a` uses, so it is neither a dunder use nor private names as data. A
        # `__dict__` slot would undo what slots are for, so dunder entries are judged as usual.
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__slots__"
            and isinstance(self.parents.get(node), ast.ClassDef)
            and isinstance(node.value, (ast.Tuple, ast.List))
            and all(
                isinstance(e, ast.Constant) and isinstance(e.value, str) and e.value.isidentifier() and not _is_dunder(e.value)
                for e in node.value.elts
            )
        ):
            return
        self.generic_visit(node)

    # ------------------------------------------------------------------ strings
    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        # The text of an f-string is prose, not an identifier used as data: only its expressions count.
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                self.visit(value)

    def visit_Expr(self, node: ast.Expr) -> None:
        # A string statement (a docstring, or a note after a field) does nothing: it is a mention.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        value = node.value
        if not isinstance(value, str):
            return
        if MODULE_STRING.match(value):
            self.fail(node, "a", f"the string {value!r} names a bot module: it only exists to be imported or "
                      f"looked up at run time")
        if TEST_SIDE_STRING.match(value):
            self.fail(node, "c", f"the string {value!r} names the test side")
        if self.exempt:
            return
        self._check_name_text(node, value, "has a string naming")
        if value in ATTRIBUTE_READERS | ATTRIBUTE_WRITERS:
            self.fail(node, "d", f"has a string naming `{value}`")
        if self._is_attribute_reader_name(node):
            return  # `getattr(obj, '_x')` was judged as `obj._x`, with its real base (self is allowed)
        if _is_dunder(value) and value not in ALLOWED_DUNDER_STRINGS:
            self.fail(node, "d", f"has a string naming the dunder `{value}`")
        elif PRIVATE_STRING.match(value):
            self.fail(node, "d", f"has a string naming the private identifier `{value}`")


# ---------------------------------------------------------------------------------- (e) the files


def _role(key: str) -> str:
    if key in LAUNCHER_FILES:
        return "launcher"
    if key == INSTRUMENT:
        return "instrument"
    return "play"


def _pyc_problem(cache: Path, source: Path, optimization: int) -> str | None:
    """None when CPython would NOT load `cache` (it is stale or invalid, so the source is compiled
    instead) or when it holds exactly the source's code; else what is wrong with it."""
    data = cache.read_bytes()
    if len(data) < 16 or data[:4] != importlib.util.MAGIC_NUMBER:
        return None  # rejected by the import system, which then compiles the source
    flags = int.from_bytes(data[4:8], "little")
    if flags & ~0b11:
        return None
    source_bytes = source.read_bytes()
    if flags & 0b01:  # hash-based
        if flags & 0b10 and data[8:16] != importlib.util.source_hash(source_bytes):
            return None  # checked and stale
        # an UNCHECKED hash-based cache is loaded without looking at the source at all
    else:
        stat = source.stat()
        if (
            int.from_bytes(data[8:12], "little") != (int(stat.st_mtime) & 0xFFFFFFFF)
            or int.from_bytes(data[12:16], "little") != (stat.st_size & 0xFFFFFFFF)
        ):
            return None  # stale: the source is compiled instead
    try:
        loaded = marshal.loads(data[16:])
    except Exception as error:  # noqa: BLE001
        return f"its header says it is current, but its code cannot be decoded ({type(error).__name__})"
    try:
        expected = compile(source_bytes, str(source), "exec", dont_inherit=True, optimize=optimization)
    except SyntaxError:
        return None  # the source does not compile; the scan reports it as a parse failure
    if not isinstance(loaded, CodeType) or loaded != expected:
        return "CPython would load it INSTEAD of its source (the header matches the source), but it holds different code"
    return None


def _check_cache_folder(ctx: _Context, folder: Path, dirnames: list[str], filenames: list[str]) -> None:
    relative = folder.relative_to(ctx.package_dir).as_posix()
    for name in dirnames:
        ctx.result.violations.append(Finding(f"ai_player/{relative}/{name}", 0, "e", "a folder inside a __pycache__ folder"))
    for name in filenames:
        display = f"ai_player/{relative}/{name}"
        path = folder / name
        if _is_link(path):
            ctx.result.violations.append(Finding(display, 0, "e", "a link inside the package"))
            continue
        match = CACHE_FILE.match(name)
        if match is None:
            ctx.result.violations.append(
                Finding(display, 0, "e", "a file the import system never writes into __pycache__: source hidden here is "
                        "importable (`ai_player.__pycache__.<name>`) but is not judged; keep only cache files there")
            )
            continue
        source = next((folder.parent / (match["stem"] + suffix) for suffix in (".py", ".pyw") if (folder.parent / (match["stem"] + suffix)).is_file()), None)
        if source is None:
            continue  # CPython never loads a cached file whose source is gone
        if match["tag"] != sys.implementation.cache_tag:
            ctx.result.caches_other_interpreter += 1
            continue
        problem = _pyc_problem(path, source, int(match["opt"] or 0))
        if problem:
            ctx.result.violations.append(Finding(display, 0, "e", problem))
        else:
            ctx.result.caches_checked += 1


def _collect_files(ctx: _Context) -> list[Path]:
    """Every file of the package, judged by rule (e) on the way: links are refused (they are not
    followed), `__pycache__` folders are checked, opaque importables are refused."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ctx.package_dir, followlinks=False):
        folder = Path(dirpath)
        for name in list(dirnames):
            if _is_link(folder / name):
                relative = (folder / name).relative_to(ctx.package_dir).as_posix()
                ctx.result.violations.append(Finding(f"ai_player/{relative}", 0, "e", "a link inside the package: what it "
                                                     "points to is importable but is not judged"))
                dirnames.remove(name)
        dirnames.sort()
        if folder.name == "__pycache__":
            _check_cache_folder(ctx, folder, list(dirnames), sorted(filenames))
            dirnames[:] = []
            continue
        for name in sorted(filenames):
            path = folder / name
            relative = path.relative_to(ctx.package_dir).as_posix()
            if _is_link(path):
                ctx.result.violations.append(Finding(f"ai_player/{relative}", 0, "e", "a link inside the package"))
                continue
            if name.lower().endswith(OPAQUE_SUFFIXES):
                ctx.result.violations.append(
                    Finding(f"ai_player/{relative}", 0, "e", "an importable file the gate cannot read (bytecode or an "
                            "extension module); keep only source in the package")
                )
                continue
            files.append(path)
    return files


# ---------------------------------------------------------------------------------- (g) pins


def _check_exports(ctx: _Context, path: Path, key: str, display: str, role: str) -> None:
    facts = ctx.facts(path)
    if facts is None:
        return
    names = list(facts.all_names or [])
    if key.startswith(HOST_DIR):
        ctx.result.exports[key] = names
        if role != "launcher":
            pinned = HOST_EXPORTS.get(key)
            if pinned is None:
                ctx.result.violations.append(Finding(display, 0, "g", "a host module that HOST_EXPORTS does not list: "
                                                     "add it there with its exports (a reviewed gate change)"))
            elif set(names) != pinned:
                extra, missing = sorted(set(names) - pinned), sorted(pinned - set(names))
                ctx.result.violations.append(Finding(display, facts.all_line, "g", f"__all__ differs from HOST_EXPORTS "
                                                     f"(new: {extra or 'none'}; gone: {missing or 'none'}): a change to a "
                                                     f"host module's surface is a reviewed gate change"))
    for name in names:
        if name not in facts.defined:
            what = "an imported name" if name in facts.imported else "not a name this module defines"
            ctx.result.violations.append(Finding(display, facts.all_line, "a", f"__all__ exports `{name}`, which is {what} (a re-export)"))


def _check_instrument(ctx: _Context, path: Path) -> None:
    display = f"ai_player/{INSTRUMENT}"
    digest = instrument_digest(path)
    ctx.result.instrument_sha256 = digest
    if digest != INSTRUMENT_SHA256:
        ctx.result.violations.append(Finding(display, 0, "g", f"the instrument changed (sha256 {digest}, pinned "
                                             f"{INSTRUMENT_SHA256}): it is exempt from rules b, d and f, so re-read all of it "
                                             f"(nothing public may hand out context, the emulator, modules.memory, ffi or a "
                                             f"frame), then pin the new digest in INSTRUMENT_SHA256"))
    try:
        tree = ast.parse(path.read_bytes())
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return
    paths = _string_tuple(tree, "BOT_BRAIN_PATHS")
    exceptions = _string_tuple(tree, "BOT_BRAIN_EXCEPTIONS") or ()
    if paths is None:
        ctx.result.violations.append(Finding(display, 0, "g", "the instrument has no BOT_BRAIN_PATHS tuple: the live bot-code "
                                             "monitor would watch nothing"))
        return
    for module in FORBIDDEN_PREFIXES:
        candidate = module.replace(".", "/")
        covered = any(
            entry in (candidate + ".py", candidate + "/") or (entry.endswith("/") and (candidate + "/").startswith(entry))
            for entry in paths
        )
        if not covered or candidate + ".py" in exceptions:
            ctx.result.violations.append(Finding(display, 0, "g", f"BOT_BRAIN_PATHS does not cover {module}, which the "
                                                 f"import backstop refuses: the live monitor would not see it run"))


def _check_shadowing(ctx: _Context) -> None:
    for library in LIBRARIES:
        top = library.split(".", 1)[0]
        if top in ctx.framework_roots and top != "__future__":
            ctx.result.violations.append(
                Finding("<library allowlist>", 0, "a", f"the framework provides a top-level `{top}`, which would "
                        f"shadow the standard library's `{library}` in the bot process")
            )
    # Step 0.1, finding 10: the package's own top-level modules and subpackages must not be named like
    # the standard library (`ai_player/platform/` was): with `ai_player/` itself on sys.path, they
    # would replace the library module for the framework and for everything else in the process.
    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    if ctx.package_dir.is_dir():
        for entry in sorted(ctx.package_dir.iterdir()):
            name = entry.name.split(".", 1)[0] if entry.is_file() else entry.name
            importable = entry.is_dir() or entry.name.lower().endswith(SOURCE_SUFFIXES + OPAQUE_SUFFIXES)
            if importable and not _is_dunder(name) and name in stdlib:
                ctx.result.violations.append(
                    Finding(f"ai_player/{entry.name}", 0, "a", f"named like the standard library's `{name}`: with "
                            f"ai_player/ on sys.path it would shadow that module for the whole process; rename it")
                )


# ---------------------------------------------------------------------------------- driver


def _scan_file(ctx: _Context, path: Path, key: str, display: str, role: str, package: list[str]) -> None:
    try:
        # BYTES, not text: the import system decodes a file by its coding cookie, and so does
        # ast.parse on bytes. Read as UTF-8 text, `# coding: utf-7` source shows a comment where
        # Python runs an import (`+AAo-` is a newline in UTF-7).
        tree = ast.parse(path.read_bytes(), filename=str(path))
    except (SyntaxError, UnicodeDecodeError, ValueError) as error:
        line = getattr(error, "lineno", 0) or 0
        ctx.result.violations.append(Finding(display, line, "parse", f"cannot parse: {error}"))
        return
    _FileScanner(ctx, key, display, role, package, tree).visit(tree)


def scan(package_dir: Path = PACKAGE_DIR, hook: Path | None = DEFAULT_HOOK, build_root: Path | None = DEFAULT_BUILD_ROOT) -> GateResult:
    result = GateResult()
    result.build_root_seen = build_root is not None and build_root.is_dir()
    result.framework_roots = discover_framework_roots(build_root)
    ctx = _Context(package_dir, result.framework_roots, result)
    _check_shadowing(ctx)
    plan: list[tuple[Path, str]] = []
    for path in _collect_files(ctx):
        key = path.relative_to(package_dir).as_posix()
        if not path.name.lower().endswith(SOURCE_SUFFIXES):
            continue  # data: README, evidence transcripts
        if key.startswith(TEST_SIDE_DIR):
            result.test_side.append(key)
            continue
        plan.append((path, key))
    ctx.module_keys = {key for _, key in plan}
    for path, key in plan:
        role = _role(key)
        result.scanned.append(key)
        result.roles[key] = role
        relative = path.relative_to(package_dir)
        display = f"ai_player/{key}"
        _scan_file(ctx, path, key, display, role, ["ai_player", *relative.parent.parts])
        _check_exports(ctx, path, key, display, role)
        if key == INSTRUMENT:
            _check_instrument(ctx, path)
    if INSTRUMENT not in ctx.module_keys:
        result.violations.append(Finding(f"ai_player/{INSTRUMENT}", 0, "g", "the instrument is missing"))
    if hook is not None:
        if hook.is_file():
            result.scanned.append(HOOK_KEY)
            result.roles[HOOK_KEY] = "play"
            _scan_file(ctx, hook, HOOK_KEY, f"<hook> {hook.name}", "play", ["plugins", "custom_modes"])
        else:
            result.violations.append(Finding(str(hook), 0, "hook", "the hook file does not exist"))
    return result


def report(result: GateResult) -> str:
    lines = ["AI PLAYER PURITY GATE (offline AST)"]
    by_role: dict[str, list[str]] = {}
    for key in result.scanned:
        by_role.setdefault(result.roles.get(key, "play"), []).append(key)
    for role in ("play", "instrument", "launcher"):
        lines.append(f"  {role:<10} {len(by_role.get(role, []))}: {', '.join(by_role.get(role, [])) or 'none'}")
    lines.append(f"  test side (not scanned for a/b/d/f): {', '.join(result.test_side) or 'none'}")
    roots = "discovered in the build root" if result.build_root_seen else "STATIC LIST ONLY (build root not found)"
    lines.append(f"  framework top-level names: {len(result.framework_roots)} ({roots})")
    lines.append(f"  libraries: {len(LIBRARIES)} allowlisted, judged against Python {sys.version.split()[0]} ({sys.implementation.cache_tag})")
    lines.append(f"  __pycache__: {result.caches_checked} current cache file(s) proven equal to their source; "
                 f"{result.caches_other_interpreter} of another interpreter not judged (it cannot load them)")
    lines.append(f"  instrument sha256: {result.instrument_sha256 or '?'} ({'pinned' if result.instrument_sha256 == INSTRUMENT_SHA256 else 'NOT the pinned one'})")
    lines.append(f"  allowlisted framework imports found: {len(result.allowed_imports)}")
    lines.extend(result.allowed_imports)
    lines.append("  host exports (__all__), pinned by rule g:")
    for key, names in sorted(result.exports.items()):
        lines.append(f"    {key}: {', '.join(names) or '(empty)'}")
    if result.violations:
        lines.append(f"  VIOLATIONS: {len(result.violations)}")
        lines.extend(str(v) for v in result.violations)
    if not result.scanned:
        lines.append("  FAIL: scanned ZERO files; the gate is measuring nothing")
    lines.append(f"VERDICT: {'PASS' if result.passed else 'FAIL'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Offline purity gate for ai_player/.")
    parser.add_argument("--package", type=Path, default=PACKAGE_DIR, help="the ai_player package folder")
    parser.add_argument("--hook", type=Path, default=DEFAULT_HOOK, help="the framework hook file")
    parser.add_argument("--no-hook", action="store_true", help="do not scan the hook file")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT, help="the framework folder (for its top-level names)")
    parser.add_argument("--instrument-digest", action="store_true", help="print the instrument's sha256 (to pin after a review)")
    args = parser.parse_args(argv)
    if args.instrument_digest:
        print(instrument_digest(args.package / INSTRUMENT))
        return 0
    if not args.package.is_dir():
        print(f"cannot run: {args.package} is not a folder")
        return 2
    result = scan(args.package, None if args.no_hook else args.hook, args.build_root)
    print(report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
