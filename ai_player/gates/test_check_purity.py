"""FAULT tests for the purity gate: every rule must FAIL on a planted violation and stay SILENT on mentions.

    py -3.12 ai_player/gates/test_check_purity.py          # or: py -3.12 -m unittest ai_player.gates.test_check_purity

WHY (CLAUDE.md session rule 6): "FAULT-TEST every gate: prove it fails when the thing it guards is
broken, and prove it does NOT fire on mere mentions in comments or docstrings. A gate with false
positives teaches the reader to bypass it." Each test copies the REAL package into a temporary folder,
plants one file (or appends to one), and scans the copy, so the plant is judged exactly as real code
would be. The real package is never touched.

`VERIFIER_PROBES` are the 41 bypass attempts of the first independent verifier (2026-10-07), verbatim;
the first gate let 29 through. `VERIFIER2_PROBES` are the second verifier's 22 static probes and its
two live plants (VB, VP), verbatim; the second gate let 20 through. Each must now be caught, by the
rule named next to it, IN the planted file (a failure somewhere else would not prove the plant was
seen). `ROUND3_PROBES` plant the rules added for that report, and `STEP01_PROBES` the rules added for
the adversarial review of step 0 (step 0.1), including its later rounds (S18-S22: the verifier's report
on step 0.1; S23-S26: its notes on round 2, the frame fence's thread surface and the instrument's
registry). `LegitimateCodeTests` is the other direction: ordinary
code using every allowed surface must pass, so the rules are not just "refuse everything".

‼ "Verbatim" with one exception: step 0.1 renamed the subpackage `ai_player/platform/` to
`ai_player/host/` (finding 10: `platform` shadowed the standard library), so every probe path and
module name that said `platform` now says `host`. Nothing else in any probe changed.
"""

from __future__ import annotations

import importlib.util
import marshal
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_purity  # noqa: E402  (test-side: imported by path, the package need not be installed)

REAL_PACKAGE = check_purity.PACKAGE_DIR
REAL_HOOK = check_purity.DEFAULT_HOOK
REAL_BUILD_ROOT = check_purity.DEFAULT_BUILD_ROOT
if not REAL_HOOK.is_file() and os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT"):
    # (R1 + R2, build stage 4) a COPY of the package (`gates/revert_r1.py`'s mutants run this file there) has no framework
    # beside it: the hook and the build root are the support root's, as `test_saving.py` finds them
    REAL_BUILD_ROOT = Path(os.environ["AI_PLAYER_TEST_SUPPORT_ROOT"]) / "sandbox-pokebot"
    REAL_HOOK = REAL_BUILD_ROOT / "plugins" / "custom_modes" / "ai_player_mode.py"

# (id, file relative to ai_player/ or None for the hook, "new" | "append" | "hook", source, rule that must fire there)
VERIFIER_PROBES: list[tuple[str, str | None, str, str, str]] = [
    ("P01 aliased import of a bot module", "brain_x.py", "new", "import modules.menuing as m\n", "a"),
    ("P02 from-import of a bot function", "brain_x.py", "new", "from modules.battle_handler import handle_battle\n", "a"),
    ("P03 from modules import menuing as mm", "brain_x.py", "new", "from modules import menuing as mm\n", "a"),
    ("P04 star import of a bot module", "brain_x.py", "new", "from modules.menuing import *\n", "a"),
    ("P05 from-import of a state-changing name", "brain_x.py", "new",
     "from ai_player.host.attribution import framework_memory as fm\nfrom somewhere import write_bytes\n", "b"),
    ("P06 getattr with a constant banned name", "brain_x.py", "new", "def f(emu):\n    getattr(emu, 'write_bytes')(0, b'')\n", "b"),
    ("P07 getattr with a concatenated name", "brain_x.py", "new", "def f(emu):\n    getattr(emu, 'write_' + 'bytes')(0, b'')\n", "d"),
    ("P08 getattr through a variable", "brain_x.py", "new", "def f(emu):\n    n = 'load_save_state'\n    getattr(emu, n)(b'')\n", "d"),
    ("P09 operator.methodcaller", "brain_x.py", "new", "import operator\ndef f(emu):\n    operator.methodcaller('write_bytes', 0, b'')(emu)\n", "a"),
    ("P10 operator.attrgetter", "brain_x.py", "new", "import operator\ndef f(emu):\n    operator.attrgetter('reset')(emu)()\n", "a"),
    ("P11 emu.__getattribute__", "brain_x.py", "new", "def f(emu):\n    emu.__getattribute__('load_save_state')(b'')\n", "d"),
    ("P12 object.__getattribute__", "brain_x.py", "new", "def f(emu):\n    object.__getattribute__(emu, 'reset')()\n", "d"),
    ("P13 sys.modules[...]", "brain_x.py", "new", "import sys\ndef f():\n    return sys.modules['modules.battle_handler'].handle_battle\n", "d"),
    ("P14 sys.modules.get(...)", "brain_x.py", "new", "import sys\nm = sys.modules.get('modules.menuing')\n", "d"),
    ("P15 re-export of context through the controller", "brain_x.py", "new",
     "from ai_player.host.controller import context\ndef f():\n    context.emulator._held_inputs |= 1\n", "a"),
    ("P16 re-export of modules.memory through attribution", "brain_x.py", "new",
     "from ai_player.host.attribution import framework_memory\ndef f():\n    framework_memory.set_event_flag_by_number(5)\n", "a"),
    ("P17 attribute walk from an allowlisted file", "host/controller.py", "append",
     "\nimport modules.context\ndef _sneak():\n    return modules.battle_handler.handle_battle\n", "a"),
    ("P18 importlib.util exec_module", "brain_x.py", "new",
     "import importlib.util\ns = importlib.util.spec_from_file_location('sm', 'plugins/custom_modes/story_mode.py')\n"
     "m = importlib.util.module_from_spec(s)\ns.loader.exec_module(m)\n", "a"),
    ("P19 runpy.run_module", "brain_x.py", "new", "import runpy\nrunpy.run_module('modules.menuing')\n", "a"),
    ("P20 exec", "brain_x.py", "new", "exec('import modules.menuing')\n", "d"),
    ("P21 builtins.__dict__['__import__']", "brain_x.py", "new", "import builtins\nbuiltins.__dict__['__import__']('modules.menuing')\n", "a"),
    ("P22 aliased import_module", "brain_x.py", "new", "from importlib import import_module as im\nm = im('modules.menuing')\n", "a"),
    ("P23 import_module bound to a variable", "brain_x.py", "new", "import importlib\nimp = importlib.import_module\nm = imp('modules.menuing')\n", "a"),
    ("P24 __import__ bound to a variable", "brain_x.py", "new", "i = __import__\nm = i('modules.menuing')\n", "d"),
    ("P25 getattr bound to a variable", "brain_x.py", "new", "ga = getattr\ndef f(emu):\n    ga(emu, 'write_bytes')(0, b'')\n", "d"),
    ("P26 vars(emu).get(...)", "brain_x.py", "new", "def f(emu):\n    vars(emu).get('write_bytes')\n", "d"),
    ("P27 vars(emu)[...]", "brain_x.py", "new", "def f(emu):\n    vars(emu)['write_bytes']\n", "d"),
    ("P28 the `tests` root", "brain_x.py", "new", "from tests.utility import BotTestCase\n", "a"),
    ("P29 the `utility` root (a namespace package)", "brain_x.py", "new", "import utility.extract_stats_encounters\n", "a"),
    ("P30 emulator.load_save_game", "brain_x.py", "new", "def f(emu):\n    emu.load_save_game(b'')\n", "b"),
    ("P31 emulator._core.load_state", "brain_x.py", "new", "def f(emu, vf):\n    emu._core.load_state(vf)\n", "d"),
    ("P32 emulator._pressed_inputs write", "brain_x.py", "new", "def f(emu):\n    emu._pressed_inputs = 1\n", "d"),
    # Rule letter changed from d to a in round 3: `sys.path` is now judged as a library SURFACE.
    ("P33 sys.path trick to reach the test side", "brain_x.py", "new",
     "import sys\nsys.path.insert(0, 'ai_player/gates')\nimport inspect_state\n", "a"),
    ("P34 bare `import modules` + attribute walk", "brain_x.py", "new", "import modules\nx = modules.menuing\n", "a"),
    ("P35 __import__ direct", "brain_x.py", "new", "m = __import__('modules.menuing')\n", "d"),
    ("P36 importlib.__import__", "brain_x.py", "new", "import importlib\nm = importlib.__import__('modules.menuing')\n", "a"),
    ("P37 modules.context in a non-host file", "brain_x.py", "new", "from modules.context import context\n", "a"),
    ("P38 a .pyw file", "sneaky.pyw", "new", "import modules.menuing\nfrom modules.memory import write_symbol\n", "a"),
    ("P39 set_event_flag_by_number", "brain_x.py", "new", "def f(fm):\n    fm.set_event_flag_by_number(5)\n", "b"),
    ("P40 hook: absolute import of story_mode", None, "hook", "from plugins.custom_modes.story_mode import StoryMode\n", "a"),
    ("P41 hook: sys.modules route to story_mode", None, "hook",
     "import sys\nS = sys.modules.get('plugins.custom_modes.story_mode')\n", "d"),
]

# Plants for the rules added after the first verifier's report, in the same format.
NEW_RULE_PROBES: list[tuple[str, str | None, str, str, str]] = [
    ("N01 a module exports a value derived from an import", "host/leaky.py", "new",
     "import os\nENVIRONMENT = os.environ\n__all__ = ['ENVIRONMENT']\n", "a"),
    ("N02 import from a module with no __all__", "brain_x.py", "new", "from ai_player.host.planted_helper import X\n", "a"),
    ("N03 import of a submodule object", "brain_x.py", "new", "from ai_player.host import controller\n", "a"),
    ("N04 `import ai_player.x` binds a module object", "brain_x.py", "new", "import ai_player.host.controller as c\n", "a"),
    ("N05 the play loop imports the launcher side", "brain_x.py", "new", "from ai_player.host.launcher import run_child\n", "c"),
    ("N06 the launcher side imports the framework", "host/launcher.py", "append", "\nfrom modules.context import context\n", "c"),
    ("N07 a button outside the controller", "brain_x.py", "new", "def f(emu):\n    emu.press_button('A')\n", "b"),
    ("N08 the controller walks a path its door does not list", "host/controller.py", "append",
     "\ndef _sneak():\n    return context.bot_listeners\n", "a"),
    ("N09 the controller aliases the emulator", "host/controller.py", "append",
     "\ndef _sneak():\n    emulator = context.emulator\n    return emulator\n", "a"),
    ("N10 a module door without `as`", "host/attribution.py", "append", "\nimport modules.memory\n", "a"),
    ("N11 a dunder attribute", "brain_x.py", "new", "def f(x):\n    return x.__class__\n", "d"),
    ("N12 typing.get_type_hints evaluates strings", "brain_x.py", "new", "import typing\ndef f(g):\n    return typing.get_type_hints(g)\n", "d"),
    ("N13 threading outside the instrument", "brain_x.py", "new", "import threading\n", "a"),
    ("N14 a traceback walked to a frame's globals", "brain_x.py", "new", "def f(e):\n    return e.__traceback__.tb_frame.f_globals\n", "d"),
    ("N15 a private identifier as data", "brain_x.py", "new", "NAME = '_pressed_inputs'\n", "d"),
    # Rule letter changed from d to a in round 3: a library module used as a value is a SURFACE breach.
    ("N16 the sys module passed around", "brain_x.py", "new", "import sys\nS = sys\n", "a"),
    ("N17 a star import from the standard library", "brain_x.py", "new", "from os import *\n", "a"),
    ("N18 the instrument's exemption is exact", "host/attribution_helper.py", "new",
     "def f(emu):\n    emu.write_bytes(0, b'')\n", "b"),
    ("N19 tracing hooks", "brain_x.py", "new", "import sys\nsys.settrace(None)\n", "d"),
    ("N20 a module path string", "brain_x.py", "new", "TARGET = 'modules.battle_handler'\n", "a"),
    ("N21 relative import above the package top", "brain_x.py", "new", "from ...outside import thing\n", "a"),
    ("N22 a string naming the test side", "brain_x.py", "new", "WHERE = 'ai_player.gates.inspect_state'\n", "c"),
    ("N23 an extra frame advance by name", "brain_x.py", "new", "def f(emu):\n    emu.run_single_frame()\n", "b"),
    ("N24 a hook relative import of story_mode", None, "hook", "from .story_mode import StoryMode\n", "a"),
]

# The second verifier's static probes (gate_bypass_probes.py, 2026-10-07), verbatim, and its two live
# plants' sources (verifier_live_plants.py). The gate of that day passed 20 of these 22 (+ VB, VP).
_G10_FRAME_WALK = textwrap.dedent(
    """
    from sys import _getframe as gf

    def f():
        frame = gf(0)
        for _ in range(64):
            match frame:
                case object(f_globals={'context': ctx}):
                    match ctx:
                        case object(emulator=object(press_button=pb)):
                            pb('A')
                            return
            match frame:
                case object(f_back=back):
                    frame = back
            if frame is None:
                return
    """
)
_VB_PLANT = textwrap.dedent(
    """
    import dataclasses

    __all__ = ["tick"]
    DONE = []


    def tick(step: int) -> None:
        if step != 100 or DONE:
            return
        DONE.append(step)
        loaded = dict(dataclasses.inspect.getmembers(dataclasses.sys))['mod' + 'ules']
        pathfinder = loaded.get('modules.' + 'map_path')
        player = loaded.get('modules.' + 'player')
        print(f"[VERIFIER-PLANT] reached bot modules: {pathfinder!r} {player!r}", flush=True)
        where = dict(dataclasses.inspect.getmembers(player))['get_player_location']()
        plan = dict(dataclasses.inspect.getmembers(pathfinder))['calculate_path']
        goal = (where[0], (where[1][0], where[1][1] + 2))
        try:
            route = plan(where, goal)
            print(f"[VERIFIER-PLANT] the BOT's pathfinder planned {len(route)} waypoints from {where} to {goal}: {route[:3]}", flush=True)
        except Exception as error:
            print(f"[VERIFIER-PLANT] the BOT's pathfinder was called and raised {type(error).__name__}: {error}", flush=True)
    """
)
_VP_PLANT = textwrap.dedent(
    """
    from sys import _getframe as gf

    __all__ = ["tick"]
    COUNT = []


    def tick(step: int) -> None:
        if step % 8 != 0:
            return
        frame = gf(0)
        for _ in range(64):
            match frame:
                case object(f_globals={'context': ctx}):
                    match ctx:
                        case object(emulator=object(press_button=pb)):
                            pb('A')
                            COUNT.append(step)
                            if len(COUNT) == 1:
                                print("[VERIFIER-PLANT] pressed A via frame walk + match patterns", flush=True)
                            return
            match frame:
                case object(f_back=back):
                    frame = back
            if frame is None:
                return
    """
)
VERIFIER2_PROBES: list[tuple[str, str | None, str, str, str]] = [
    ("G01 `from sys import path` then path.insert", "brain_v.py", "new",
     "from sys import path\npath.insert(0, 'ai_player/gates')\n", "a"),
    ("G02 `os.sys.path.insert`", "brain_v.py", "new", "import os\nos.sys.path.insert(0, 'ai_player/gates')\n", "a"),
    ("G03 `from os import sys as s`", "brain_v.py", "new",
     "from os import sys as s\nS2 = s\ns.path.insert(0, 'ai_player/gates')\n", "a"),
    ("G04 `from sys import _getframe`", "brain_v.py", "new", "from sys import _getframe as gf\ndef f():\n    return gf(1)\n", "a"),
    ("G05 `from sys import exc_info` + tb walked via match pattern", "brain_v.py", "new",
     "from sys import exc_info\ndef f():\n    match exc_info()[2]:\n        case object(tb_frame=fr):\n            return fr\n", "a"),
    ("G06 match class pattern reads a PRIVATE attribute", "brain_v.py", "new",
     "def f(a):\n    match a:\n        case object(_emulator=emu):\n            return emu\n", "d"),
    ("G07 match class pattern binds a STATE-CHANGING method", "brain_v.py", "new",
     "def f(emu):\n    match emu:\n        case object(write_bytes=wb):\n            wb(0x02000000, b'\\x00')\n", "b"),
    ("G08 match class pattern binds an INPUT method outside the controller", "brain_v.py", "new",
     "def f(emu):\n    match emu:\n        case object(press_button=pb):\n            pb('A')\n", "b"),
    ("G09 match class pattern reads a DUNDER", "brain_v.py", "new",
     "from ai_player.host.controller import Controller\n"
     "def f():\n    match Controller.tap:\n        case object(__globals__={'context': ctx}):\n            return ctx\n", "d"),
    ("G10 match pattern frame walk", "brain_v.py", "new", _G10_FRAME_WALK, "a"),
    ("G11 dataclasses.inspect.getmembers", "brain_v.py", "new",
     "import dataclasses\ndef f(emu):\n    return dict(dataclasses.inspect.getmembers(emu))['press_' + 'button']('A')\n", "a"),
    ("G12 sys.modules via dataclasses.sys + getmembers + split strings", "brain_v.py", "new",
     "import dataclasses\n"
     "def f():\n"
     "    mods = dict(dataclasses.inspect.getmembers(dataclasses.sys))['mod' + 'ules']\n"
     "    return mods['modules.' + 'battle_handler']\n", "a"),
    ("G13 functools.update_wrapper as a dynamic setattr", "brain_v.py", "new",
     "import functools\n"
     "def f(emu):\n"
     "    src = type('W', (), {'_pressed' + '_inputs': 1})\n"
     "    functools.update_wrapper(emu, src, assigned=('_pressed' + '_inputs',), updated=())\n", "a"),
    ("G13b functools.update_wrapper, split as '_' + 'pressed_inputs'", "brain_v.py", "new",
     "import functools\n"
     "def f(emu):\n"
     "    n = '_' + 'pressed_inputs'\n"
     "    functools.update_wrapper(emu, type('W', (), {n: 1}), assigned=(n,), updated=())\n", "a"),
    ("G14 traceback.walk_stack -> frames", "brain_v.py", "new",
     "import traceback\n"
     "def f():\n"
     "    for fr, _ in traceback.walk_stack(None):\n"
     "        match fr:\n"
     "            case object(f_globals={'context': ctx}):\n"
     "                return ctx\n", "a"),
    ("G15 os.system / os.environ", "brain_v.py", "new", "import os\nos.environ['AI_PLAYER_X'] = '1'\nos.system('echo hi')\n", "a"),
    ("G16 pathlib write of a .py file", "brain_v.py", "new",
     "import pathlib\npathlib.Path('statistics.py').write_text('import modules.menuing\\n')\n", "f"),
    ("G17 str.format attribute walk", "brain_v.py", "new",
     "def f(emu):\n    return '{0._pressed_inputs}{0.__class__.__init__.__globals__}'.format(emu)\n", "d"),
    ("G18 typing.sys / contextlib.sys / enum.sys", "brain_v.py", "new",
     "import typing, contextlib, enum\nP = typing.sys.path\nQ = contextlib.sys\nR = enum.sys\n", "a"),
    ("G19 bytes constant decoded to a forbidden name", "brain_v.py", "new",
     "import dataclasses\ndef f(emu):\n    return dict(dataclasses.inspect.getmembers(emu))[b'write_bytes'.decode()]\n", "a"),
    ("G20 instrument exports a function returning context.emulator", "host/attribution.py", "append",
     "\ndef handle():\n    return context.emulator\n__all__ = ['Attribution', 'PurityCounters', 'Sealed', 'handle']\n", "g"),
    ("VB live plant: the bot's pathfinder through getmembers", "_plant.py", "new", _VB_PLANT, "a"),
    ("VP live plant: a press through a frame walk", "_plant.py", "new", _VP_PLANT, "a"),
]

# Plants for the rules added after the second verifier's report.
ROUND3_PROBES: list[tuple[str, str | None, str, str, str]] = [
    ("R01 setattr is refused", "brain_r.py", "new", "def f(x):\n    setattr(x, 'a', 1)\n", "d"),
    ("R02 delattr is refused", "brain_r.py", "new", "def f(x):\n    delattr(x, 'a')\n", "d"),
    ("R03 getattr(template, 'format')", "brain_r.py", "new", "def f(o):\n    return getattr('{0._x}', 'format')(o)\n", "d"),
    ("R04 getattr(path, 'write_text')", "brain_r.py", "new", "def f(p):\n    getattr(p, 'write_text')('x')\n", "f"),
    ("R05 a template that is not a constant", "brain_r.py", "new", "def f(t, o):\n    return t.format(o)\n", "d"),
    ("R06 an index field in a format template", "brain_r.py", "new", "def f(o):\n    return '{0[k]}'.format(o)\n", "d"),
    ("R07 an attribute field in a NESTED format spec", "brain_r.py", "new", "def f(a, b):\n    return '{0:{1.x}}'.format(a, b)\n", "d"),
    ("R08 format_map on a template that is not a constant", "brain_r.py", "new", "def f(t, o):\n    return t.format_map(o)\n", "d"),
    ("R09 a match pattern binding .format", "brain_r.py", "new",
     "def f(s):\n    match s:\n        case object(format=fm):\n            return fm\n", "d"),
    ("R10 open for writing", "brain_r.py", "new", "def f():\n    open('statistics.py', 'w').write('x')\n", "f"),
    ("R11 open with a mode chosen at run time", "brain_r.py", "new", "def f(m):\n    return open('x', m)\n", "f"),
    ("R12 open passed around", "brain_r.py", "new", "OPEN = open\n", "f"),
    ("R13 Path.open('a')", "brain_r.py", "new", "from pathlib import Path\ndef f():\n    Path('x').open('a')\n", "f"),
    ("R14 Path.replace(target): a file move", "brain_r.py", "new", "def f(p):\n    p.replace('statistics.py')\n", "f"),
    ("R15 Path.rename", "brain_r.py", "new", "def f(p):\n    p.rename('statistics.py')\n", "f"),
    ("R16 Path.mkdir outside the writers", "brain_r.py", "new", "def f(p):\n    p.mkdir()\n", "f"),
    ("R17 monkeypatching a library the framework shares", "brain_r.py", "new", "import time\ntime.sleep = print\n", "f"),
    ("R18 deleting a library attribute", "brain_r.py", "new", "import json\ndel json.loads\n", "f"),
    ("R19 monkeypatching another AI module's class", "brain_r.py", "new",
     "from ai_player.options import RunOptions\nRunOptions.from_env = None\n", "f"),
    ("R20 changing another AI module's data", "brain_r.py", "new",
     "from ai_player.options import ALL_SWITCHES\nALL_SWITCHES[0] = 'x'\n", "f"),
    ("R21 the instrument's finalize outside the lifecycle", "brain_r.py", "new", "def f(a):\n    return a.finalize_audit()\n", "g"),
    ("R22 the instrument's verdict writer outside the lifecycle", "brain_r.py", "new",
     "def f(a):\n    return a.write_verdict_file(None, {})\n", "g"),
    ("R23 `exec` reached as an attribute (enum.bltns.exec)", "brain_r.py", "new", "def f(x):\n    x.exec('import modules.menuing')\n", "d"),
    ("R24 a re-exported reflective function (contextlib.wraps IS functools.wraps)", "brain_r.py", "new",
     "from contextlib import wraps\n", "a"),
    ("R25 traceback.walk_tb", "brain_r.py", "new", "import traceback\ndef f(e):\n    return traceback.walk_tb(e)\n", "a"),
    ("R26 os.environ.setdefault (an environment WRITE)", "brain_r.py", "new", "import os\nos.environ.setdefault('X', '1')\n", "a"),
    ("R27 os.putenv", "brain_r.py", "new", "import os\nos.putenv('X', '1')\n", "a"),
    ("R28 sys.exc_info", "brain_r.py", "new", "import sys\ndef f():\n    return sys.exc_info()\n", "a"),
    ("R29 a module reached through datetime", "brain_r.py", "new", "import datetime\nS = datetime.sys\n", "a"),
    ("R30 the play loop rewrites sys.path", "brain_r.py", "new", "import sys\nsys.path[:] = ['ai_player/gates']\n", "a"),
    ("R31 the os module passed around", "brain_r.py", "new", "import os\ndef f(g):\n    return g(os)\n", "a"),
    ("R32 a partial library path used as a value", "brain_r.py", "new", "import os\nE = os.environ\n", "a"),
    ("R33 sys.monitoring outside the instrument", "brain_r.py", "new", "import sys\nsys.monitoring.set_events(4, 0)\n", "a"),
    ("R34 a new export from a host module", "host/controller.py", "append",
     "\ndef extra():\n    return 1\n__all__ = ['BUTTONS', 'MAX_ACTION_FRAMES', 'Controller', 'ControllerError', 'extra']\n", "g"),
    # host/eyes.py became a LISTED host module in step 1, so R35 plants a name the gate truly does not list.
    ("R35 a host module the gate does not list", "host/eyes_extra.py", "new", "__all__ = []\n", "g"),
    ("R36 a `__dict__` slot (it would undo the slots)", "brain_r.py", "new", "class C:\n    __slots__ = ('__dict__',)\n", "d"),
    ("R37 getattr(x, 'open') bypassing the mode check", "brain_r.py", "new", "def f(p):\n    getattr(p, 'open')('w')\n", "f"),
    ("R38 an instrument's private state through a match pattern", "brain_r.py", "new",
     "def f(a):\n    match a:\n        case object(_counters=c):\n            return c\n", "d"),
    ("R39 getattr with a constant PRIVATE name on another object", "brain_r.py", "new",
     "def f(emu):\n    return getattr(emu, '_pressed_inputs')\n", "d"),
    ("R40 hasattr with a constant dunder name", "brain_r.py", "new", "def f(g):\n    return hasattr(g, '__globals__')\n", "d"),
    ("R41 Path.replace(target=...) as a keyword", "brain_r.py", "new", "def f(p):\n    p.replace(target='statistics.py')\n", "f"),
    ("R42 contextlib.chdir moves the framework's working folder", "brain_r.py", "new",
     "import contextlib\ndef f():\n    return contextlib.chdir('..')\n", "a"),
    ("R43 an async generator's code object", "brain_r.py", "new", "def f(g):\n    return g.ag_code\n", "d"),
]

# Plants for the rules added for the adversarial review of step 0 (step 0.1, 2026-10-07).
STEP01_PROBES: list[tuple[str, str | None, str, str, str]] = [
    ("S01 the brain imports the host side (finding 10)", "mode.py", "append",
     "\nfrom ai_player.host.controller import Controller\n", "c"),
    ("S02 the brain imports a host module object (finding 10)", "mode.py", "append",
     "\nimport ai_player.host.session as s\n", "a"),
    ("S03 the hook puts a path IN FRONT of the standard library (finding 4)", None, "hook",
     "sys.path.insert(0, 'x')\n", "a"),
    ("S04 the hook rewrites sys.path by slice (finding 4)", None, "hook", "sys.path[:] = ['x'] + sys.path\n", "f"),
    ("S05 the hook passes sys.path around (finding 4)", None, "hook", "P = sys.path\n", "a"),
    ("S06 signal handlers outside the session (finding 7)", "brain_s.py", "new",
     "import signal\nsignal.signal(signal.SIGINT, print)\n", "a"),
    ("S07 the session uses signal beyond its surface (finding 7)", "host/session.py", "append",
     "\ndef _sneak():\n    return signal.raise_signal(signal.SIGINT)\n", "a"),
    ("S08 atexit outside the hook (finding 9)", "brain_s.py", "new", "import atexit\natexit.register(print)\n", "a"),
    ("S09 the framework's main-loop module outside isolation (finding 1)", "brain_s.py", "new",
     "import modules.main as m\nm.get_bot_listeners = None\n", "a"),
    ("S10 isolation walks modules.main beyond its door (finding 1)", "host/isolation.py", "append",
     "\ndef _sneak():\n    return framework_main.main_loop\n", "a"),
    ("S11 isolation assigns another modules.main name (finding 1)", "host/isolation.py", "append",
     "\ndef _sneak():\n    framework_main.work_queue = None\n", "a"),
    ("S12 the session reads context beyond its door (findings 5, 6)", "host/session.py", "append",
     "\ndef _sneak():\n    return context.emulator\n", "a"),
    ("S13 the hook reads context beyond its door (finding 9)", None, "hook", "E = context.emulator\n", "a"),
    ("S14 the instrument's isolation check named outside the session (finding 1)", "brain_s.py", "new",
     "def f(a):\n    a.watch_guard(None, None)\n", "g"),
    ("S15 the instrument's exit watchdog named outside the lifecycle", "brain_s.py", "new",
     "def f(a):\n    a.arm_exit_watchdog(0)\n", "g"),
    ("S16 a new export from the session (rule g)", "host/session.py", "append",
     "\ndef extra():\n    return 1\n__all__ = ['Session', 'start_session', 'extra']\n", "g"),
    ("S17 threading.Timer outside the instrument", "brain_s.py", "new", "import threading\nT = threading.Timer\n", "a"),
    # Round 2 (the verifier's report on step 0.1): threading spread to the session (the interrupt watch)
    # and the lifecycle (single-entry finish), each on its own narrow surface; the instrument reads
    # main.py's pass counter for its frame-continuity check, and no other file may.
    ("S18 the session uses threading beyond Thread (round 2)", "host/session.py", "append",
     "\ndef _sneak():\n    return threading.Timer(1, print)\n", "a"),
    ("S19 the lifecycle uses threading beyond Lock and get_ident (round 2)", "host/lifecycle.py", "append",
     "\ndef _sneak():\n    return threading.Thread(target=print)\n", "a"),
    ("S20 the brain imports threading (round 2)", "mode.py", "append", "\nimport threading\n", "a"),
    ("S21 the session reads main.py's pass counter, the instrument's door only (round 2)", "host/session.py", "append",
     "\ndef _sneak():\n    return context.frame\n", "a"),
    ("S22 the controller uses threading at all (round 2)", "host/controller.py", "append",
     "\nimport threading\nL = threading.Lock\n", "a"),
    # Round 3 (the verifier's notes on round 2): the instrument's FRAME FENCE takes `threading.RLock`
    # and `threading.get_ident`; the re-entrant lock is the instrument's alone, and `get_ident` is the
    # instrument's and the lifecycle's, never the session's or the brain's.
    ("S23 the session takes the instrument's frame lock type (round 3)", "host/session.py", "append",
     "\ndef _sneak():\n    return threading.RLock()\n", "a"),
    ("S24 the session reads thread ids (round 3: the instrument and the lifecycle only)", "host/session.py", "append",
     "\ndef _sneak():\n    return threading.get_ident()\n", "a"),
    ("S25 AI code imports the instrument's registry (round 3; not in its __all__)", "brain_s.py", "new",
     "from ai_player.host.attribution import _REGISTRY\n", "a"),
    ("S26 AI code reaches the instrument's registry as an attribute (round 3)", "brain_s.py", "new",
     "import ai_player.host.attribution as instrument\nR = instrument._REGISTRY\n", "d"),
]


@contextmanager
def planted_copy(target: str | None, mode: str, source: str, extra: dict[str, str] | None = None):
    """A temporary copy of the real package (and hook) with one plant. Yields (package, hook)."""
    with tempfile.TemporaryDirectory(prefix="ai_player_gate_") as tmp:
        package = Path(tmp) / "ai_player"
        shutil.copytree(REAL_PACKAGE, package, ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures"))
        hook = Path(tmp) / "ai_player_mode.py"
        hook.write_text(REAL_HOOK.read_text(encoding="utf-8"), encoding="utf-8")
        for relative, text in (extra or {}).items():
            (package / relative).write_text(text, encoding="utf-8")
        if mode == "hook":
            hook.write_text(hook.read_text(encoding="utf-8") + "\n" + source, encoding="utf-8")
        elif target is not None:
            path = package / target
            path.parent.mkdir(parents=True, exist_ok=True)
            if mode == "append":
                path.write_text(path.read_text(encoding="utf-8") + source, encoding="utf-8")
            else:
                path.write_text(textwrap.dedent(source), encoding="utf-8")
        yield package, hook


def run_python(code: str, cwd: Path) -> str:
    """Run a snippet in a fresh interpreter with `cwd` first on the path; return its output."""
    done = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, {str(cwd)!r}); {code}"],
        cwd=str(cwd), capture_output=True, text=True, timeout=120,
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": ""},
    )
    return (done.stdout + done.stderr).strip()


class GateTestCase(unittest.TestCase):
    def assert_caught(self, result: check_purity.GateResult, rule: str, fragment: str) -> None:
        hits = [v for v in result.violations if v.rule == rule and fragment in v.file]
        self.assertFalse(result.passed, "the gate PASSED a planted violation")
        self.assertTrue(hits, f"expected a [{rule}] finding in {fragment}; got:\n{check_purity.report(result)}")

    def run_probe(self, probe: tuple[str, str | None, str, str, str], extra: dict[str, str] | None = None) -> None:
        title, target, mode, source, rule = probe
        with planted_copy(target, mode, source, extra) as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            fragment = "<hook>" if mode == "hook" else Path(target or "").name
            self.assert_caught(result, rule, fragment)


class ControlTests(GateTestCase):
    def test_control_real_package_passes(self) -> None:
        """Without this, every FAIL below could be a gate that fails on everything."""
        result = check_purity.scan(REAL_PACKAGE, REAL_HOOK, REAL_BUILD_ROOT)
        self.assertEqual(result.violations, [], check_purity.report(result))
        self.assertTrue(result.passed)
        self.assertIn("mode.py", result.scanned)
        self.assertIn(check_purity.HOOK_KEY, result.scanned)
        self.assertEqual(result.roles["host/attribution.py"], "instrument")
        self.assertEqual(result.roles["host/launcher.py"], "launcher")

    def test_control_unchanged_copy_passes(self) -> None:
        """The copying itself must not trip the gate, or every plant below would 'fail' for free."""
        with planted_copy(None, "new", "") as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            self.assertTrue(result.passed, check_purity.report(result))

    def test_zero_files_is_a_failure_not_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = check_purity.scan(Path(tmp), None, REAL_BUILD_ROOT)
            self.assertFalse(result.passed)


class VerifierProbeTests(GateTestCase):
    def test_every_verifier_probe_is_caught(self) -> None:
        for probe in VERIFIER_PROBES:
            with self.subTest(probe[0]):
                self.run_probe(probe)

    def test_every_second_verifier_probe_is_caught(self) -> None:
        for probe in VERIFIER2_PROBES:
            with self.subTest(probe[0]):
                self.run_probe(probe)


class NewRuleTests(GateTestCase):
    def test_every_new_rule_fires(self) -> None:
        helper = {"host/planted_helper.py": "X = 1\n"}  # a module WITHOUT __all__, for N02
        for probe in NEW_RULE_PROBES:
            with self.subTest(probe[0]):
                self.run_probe(probe, helper)

    def test_every_round3_rule_fires(self) -> None:
        for probe in ROUND3_PROBES:
            with self.subTest(probe[0]):
                self.run_probe(probe)

    def test_every_step01_rule_fires(self) -> None:
        for probe in STEP01_PROBES:
            with self.subTest(probe[0]):
                self.run_probe(probe)

    def test_a_package_folder_named_like_the_standard_library_fails(self) -> None:
        """Finding 10: step 0's `ai_player/platform/` shadowed the standard library's `platform` for
        anything that put `ai_player/` on sys.path. A folder (or module) named like a library fails."""
        with planted_copy("platform/__init__.py", "new", "__all__ = []\n") as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            hits = [v for v in result.violations if v.rule == "a" and v.file == "ai_player/platform"]
            self.assertTrue(hits, check_purity.report(result))
        with planted_copy("statistics.py", "new", "__all__ = []\n") as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            hits = [v for v in result.violations if v.rule == "a" and v.file == "ai_player/statistics.py"]
            self.assertTrue(hits, check_purity.report(result))

    def test_the_host_folder_is_not_a_library_name(self) -> None:
        """CONTROL for the test above: the real package's top-level names shadow nothing."""
        result = check_purity.scan(REAL_PACKAGE, REAL_HOOK, REAL_BUILD_ROOT)
        self.assertFalse([v for v in result.violations if "named like the standard library" in v.message])
        self.assertNotIn("host", sys.stdlib_module_names)

    def test_e_sourceless_bytecode_fails(self) -> None:
        with planted_copy(None, "new", "") as (package, hook):
            (package / "brain.pyc").write_bytes(b"\x00" * 32)
            self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "e", "brain.pyc")

    def test_e_extension_module_fails(self) -> None:
        with planted_copy(None, "new", "") as (package, hook):
            (package / "brain.cp312-win_amd64.pyd").write_bytes(b"MZ")
            self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "e", "brain.cp312-win_amd64.pyd")

    def test_e_pycache_without_source_is_not_a_finding(self) -> None:
        """CPython ignores a `__pycache__` .pyc whose source is gone, so those are not importable."""
        with planted_copy(None, "new", "") as (package, hook):
            (package / "__pycache__").mkdir(exist_ok=True)
            (package / "__pycache__" / f"ghost.{sys.implementation.cache_tag}.pyc").write_bytes(b"\x00" * 32)
            self.assertTrue(check_purity.scan(package, hook, REAL_BUILD_ROOT).passed)

    def test_a_framework_shadowing_a_library_fails(self) -> None:
        """A `json/` folder in the bot's folder would be what `import json` loads in the bot process."""
        with planted_copy(None, "new", "") as (package, hook), tempfile.TemporaryDirectory() as build:
            (Path(build) / "json").mkdir()
            result = check_purity.scan(package, hook, Path(build))
            self.assert_caught(result, "a", "<library allowlist>")

    def test_a_discovered_root_is_a_framework_import(self) -> None:
        """A folder nobody listed in STATIC_FRAMEWORK_ROOTS still counts once it exists in the build root."""
        with planted_copy("brain_x.py", "new", "import planted_root.thing as t\n") as (package, hook), \
                tempfile.TemporaryDirectory() as build:
            (Path(build) / "planted_root").mkdir()
            result = check_purity.scan(package, hook, Path(build))
            self.assert_caught(result, "a", "brain_x.py")
            self.assertIn("planted_root", result.framework_roots)

    def test_a_denylist_backstops_an_overbroad_door(self) -> None:
        """Even if someone opened a door to a bot module, the bot's brain stays out."""
        saved = check_purity.DOORS
        try:
            check_purity.DOORS = saved + (check_purity.Door("modules.menuing", None, {"brain_x.py": None}, "test"),)
            self.run_probe(("backstop", "brain_x.py", "new", "import modules.menuing as m\n", "a"))
        finally:
            check_purity.DOORS = saved


class FileRuleTests(GateTestCase):
    """Rule (e): what the import system can load must be what the gate read."""

    def test_e_source_hidden_in_pycache_fails(self) -> None:
        """The second verifier's probe (pycache_hide_probe.py), verbatim: a .py in `__pycache__`,
        imported as `ai_player.__pycache__.brain`. Both the hidden file and the import must fail."""
        hidden = "import modules.menuing as m\nfrom modules.memory import write_symbol\n__all__ = ['f']\n\n\ndef f():\n    return m, write_symbol\n"
        brain = "from ai_player.__pycache__.brain import f\n__all__ = ['g']\n\n\ndef g():\n    return f()\n"
        with planted_copy("brain_v.py", "new", brain) as (package, hook):
            (package / "__pycache__").mkdir()
            (package / "__pycache__" / "brain.py").write_text(hidden, encoding="utf-8")
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            self.assert_caught(result, "e", "__pycache__/brain.py")
            self.assert_caught(result, "a", "brain_v.py")

    def test_e_a_coding_cookie_cannot_hide_code(self) -> None:
        """In UTF-7, `+AAo-` is a newline: read as UTF-8 text the import below is inside a comment, but
        CPython decodes by the cookie and RUNS it. The gate must judge what CPython runs."""
        source = b"# coding: utf-7\nX = 1  # harmless +AAo-import modules.menuing as hidden\n"
        with planted_copy(None, "new", "") as (package, hook):
            (package / "brain_cookie.py").write_bytes(source)
            # NON-VACUITY: the hidden line really is code to CPython (it fails to import `modules`
            # here, which proves it ran).
            ran = run_python("import ai_player.brain_cookie", package.parent)
            self.assertIn("No module named 'modules'", ran, ran)
            self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "a", "brain_cookie.py")

    def test_e_any_other_file_in_pycache_fails(self) -> None:
        with planted_copy(None, "new", "") as (package, hook):
            (package / "host" / "__pycache__").mkdir()
            (package / "host" / "__pycache__" / "notes.txt").write_text("x", encoding="utf-8")
            self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "e", "notes.txt")

    def _forge(self, package: Path, hash_based: bool) -> Path:
        """Write a cache file for options.py whose HEADER matches the real source but whose CODE says
        DEFAULT_FRAMES = 7 (the real source says 3000). Returns the cache path."""
        source = package / "options.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("DEFAULT_FRAMES = 3000", text)
        forged = compile(text.replace("DEFAULT_FRAMES = 3000", "DEFAULT_FRAMES = 7"), str(source), "exec", dont_inherit=True)
        if hash_based:  # flags 0b01: hash-based, UNCHECKED (loaded without looking at the source)
            header = importlib.util.MAGIC_NUMBER + (1).to_bytes(4, "little") + importlib.util.source_hash(b"anything")
        else:
            stat = source.stat()
            header = (
                importlib.util.MAGIC_NUMBER + (0).to_bytes(4, "little")
                + (int(stat.st_mtime) & 0xFFFFFFFF).to_bytes(4, "little") + (stat.st_size & 0xFFFFFFFF).to_bytes(4, "little")
            )
        cache = Path(importlib.util.cache_from_source(str(source)))
        cache.parent.mkdir(exist_ok=True)
        cache.write_bytes(header + marshal.dumps(forged))
        return cache

    def test_e_forged_timestamp_cache_fails_and_really_loads(self) -> None:
        with planted_copy(None, "new", "") as (package, hook):
            cache = self._forge(package, hash_based=False)
            # NON-VACUITY: CPython really runs the forged code instead of the source.
            loaded = run_python("import ai_player.options as o; print('DEFAULT_FRAMES', o.DEFAULT_FRAMES)", package.parent)
            self.assertIn("DEFAULT_FRAMES 7", loaded, "the forged cache was not what CPython loaded: the test proves nothing")
            self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "e", cache.name)

    def test_e_forged_unchecked_hash_cache_fails_and_really_loads(self) -> None:
        with planted_copy(None, "new", "") as (package, hook):
            cache = self._forge(package, hash_based=True)
            loaded = run_python("import ai_player.options as o; print('DEFAULT_FRAMES', o.DEFAULT_FRAMES)", package.parent)
            self.assertIn("DEFAULT_FRAMES 7", loaded, "the forged cache was not what CPython loaded: the test proves nothing")
            self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "e", cache.name)

    def test_e_genuine_caches_pass(self) -> None:
        """CONTROL: the caches CPython itself writes must pass, and must be judged (not skipped)."""
        with planted_copy(None, "new", "") as (package, hook):
            run_python("import ai_player.options, ai_player.runlog", package.parent)
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            self.assertTrue(result.passed, check_purity.report(result))
            self.assertGreaterEqual(result.caches_checked, 2, check_purity.report(result))

    def test_e_stale_cache_is_not_a_finding(self) -> None:
        """CONTROL: a forged cache whose header does NOT match its source is ignored by CPython (it
        compiles the source instead), so it is not a finding either."""
        with planted_copy(None, "new", "") as (package, hook):
            cache = self._forge(package, hash_based=False)
            data = bytearray(cache.read_bytes())
            data[12:16] = (int.from_bytes(data[12:16], "little") + 1).to_bytes(4, "little")  # wrong source size
            cache.write_bytes(bytes(data))
            loaded = run_python("import ai_player.options as o; print('DEFAULT_FRAMES', o.DEFAULT_FRAMES)", package.parent)
            self.assertIn("DEFAULT_FRAMES 3000", loaded)
            self.assertTrue(check_purity.scan(package, hook, REAL_BUILD_ROOT).passed)

    def test_e_link_inside_the_package_fails(self) -> None:
        with planted_copy(None, "new", "") as (package, hook), tempfile.TemporaryDirectory() as outside:
            Path(outside, "menu.py").write_text("import modules.menuing as m\n", encoding="utf-8")
            link = package / "linked"
            try:
                if os.name == "nt":
                    import _winapi

                    _winapi.CreateJunction(outside, str(link))
                else:
                    os.symlink(outside, link)
            except (OSError, ImportError, AttributeError) as error:
                self.skipTest(f"cannot create a link here: {error}")
            try:
                self.assert_caught(check_purity.scan(package, hook, REAL_BUILD_ROOT), "e", "linked")
            finally:
                if os.name == "nt":
                    os.rmdir(link)  # removes the junction, not its target
                else:
                    os.unlink(link)


class PinTests(GateTestCase):
    """Rule (g): the surfaces the gate cannot judge are pinned."""

    def test_g_instrument_change_fails(self) -> None:
        self.run_probe(("instrument edited", "host/attribution.py", "append", "\n# an innocent-looking comment\n", "g"))

    def test_g_brain_lists_must_agree(self) -> None:
        source = (REAL_PACKAGE / "host" / "attribution.py").read_text(encoding="utf-8")
        self.assertIn('    "modules/map_path.py",\n', source)
        with planted_copy(None, "new", "") as (package, hook):
            (package / "host" / "attribution.py").write_text(source.replace('    "modules/map_path.py",\n', ""), encoding="utf-8")
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            hits = [v for v in result.violations if v.rule == "g" and "modules.map_path" in v.message]
            self.assertTrue(hits, check_purity.report(result))

    def test_g_every_backstop_module_is_watched_live(self) -> None:
        """The real lists agree today (the control for the test above)."""
        result = check_purity.scan(REAL_PACKAGE, REAL_HOOK, REAL_BUILD_ROOT)
        self.assertFalse([v for v in result.violations if v.rule == "g"], check_purity.report(result))


class LegitimateCodeTests(GateTestCase):
    def test_ordinary_code_on_every_allowed_surface_passes(self) -> None:
        """The other direction: rules that refuse ordinary code teach people to bypass the gate."""
        source = '''
            from __future__ import annotations

            import json
            import math
            import os
            import os.path
            import re
            import time
            from collections import Counter, abc
            from collections.abc import Generator
            from dataclasses import dataclass, field
            from pathlib import Path
            from typing import NoReturn

            from ai_player.options import DEFAULT_FRAMES, RunOptions

            __all__ = ["Plan", "Walker", "plan"]


            @dataclass
            class Plan:
                steps: list[str] = field(default_factory=list)


            class Walker:
                __slots__ = ("_x", "y")

                def __init__(self) -> None:
                    self._x = 1
                    self.y = 2

                def name(self) -> str:
                    return f"{type(self).__name__}:{self._x}:{getattr(self, '_x')}"

                def steps(self) -> Generator[int, None, None]:
                    yield from range(3)


            def plan(text: str, options: RunOptions) -> str:
                words = re.findall(r"\\w+", text.replace("a", "b"))
                words.remove("x") if "x" in words else None
                total = math.sqrt(len(words)) + time.monotonic() + DEFAULT_FRAMES
                path = Path(os.path.join("a", "b")).with_suffix(".txt")
                environment = os.environ.get("AI_PLAYER_X", "") + os.sep
                data = json.loads(json.dumps({"n": total}))
                if path.exists():
                    with open(path) as handle:
                        data["text"] = handle.read()
                    with path.open("rb") as handle:
                        data["size"] = len(handle.read())
                counts = Counter(words)
                label = "{}-{}".format(1, 2) + "{name:>{width}}".format(name="x", width=4)
                isinstance(counts, abc.Mapping)
                hasattr(path, "name")
                getattr(counts, "most_common")(1)
                match data:
                    case {"n": number}:
                        label += str(number)
                match path:
                    case Path(name=name):
                        label += name
                return label + environment + options.describe()


            def stop() -> NoReturn:
                raise SystemExit(0)
            '''
        with planted_copy("brain_ok.py", "new", source) as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            planted = [str(v) for v in result.violations if "brain_ok.py" in v.file]
            self.assertEqual(planted, [], "ordinary code fired the gate")
            self.assertTrue(result.passed, check_purity.report(result))


#: (R1 + R2, build spec 2026-10-29 D12 (c): USER RULING 52) the play loop may not end, restart or catch the end of its own
#: process: each plant must fail by the rule named, IN the planted file
EXIT_PROBES: list[tuple[str, str | None, str, str, str]] = [
    ("X01 sys.exit in brain/", "brain/exit_plant.py", "new", "import sys\n\n\ndef give_up():\n    sys.exit(0)\n", "a"),
    ("X02 raise SystemExit in brain/", "brain/exit_plant.py", "new", "def give_up():\n    raise SystemExit(2)\n", "b"),
    ("X03 the exit() builtin in skills/", "skills/exit_plant.py", "new", "def give_up():\n    exit()\n", "b"),
    ("X04 the quit() builtin in mode.py", "mode.py", "append", "\n\ndef _give_up():\n    quit()\n", "b"),
    ("X05 except KeyboardInterrupt in game_memory.py", "game_memory.py", "append",
     "\n\ndef _keep_going(step):\n    try:\n        step()\n    except KeyboardInterrupt:\n        return None\n", "b"),
    ("X06 SystemExit caught in options.py", "options.py", "append",
     "\n\ndef _never_end(step):\n    try:\n        step()\n    except SystemExit:\n        return None\n", "b"),
    # (R1 + R2 follow-up, spec 2026-10-29 D1: N-1) the forms that discard, swallow or hold back an exit WITHOUT naming one
    # of the four names above: each passed the HEAD gate (measured, `s53/r1f/probe_gates.out`, `mine/probe_plants_all.out`)
    ("X07 raise GeneratorExit in brain/", "brain/exit_plant.py", "new", "def give_up():\n    raise GeneratorExit\n", "b"),
    ("X08 except BaseException in skills/", "skills/exit_plant.py", "new",
     "def keep(step):\n    try:\n        step()\n    except BaseException:\n        return None\n", "b"),
    ("X09 except (ValueError, BaseException) in mode.py", "mode.py", "append",
     "\n\ndef _keep(step):\n    try:\n        step()\n    except (ValueError, BaseException):\n        return None\n", "b"),
    ("X10 except* BaseException in hands/", "hands/exit_plant.py", "new",
     "def keep(step):\n    try:\n        step()\n    except* BaseException:\n        pass\n", "b"),
    ("X11 a BaseExceptionGroup subclass in world/", "world/exit_plant.py", "new",
     "class Stop(BaseExceptionGroup):\n    pass\n", "b"),
    ("X12 a bare except in game_memory.py", "game_memory.py", "append",
     "\n\ndef _keep(step):\n    try:\n        step()\n    except:\n        return None\n", "b"),
    ("X13 finally: return in brain/", "brain/exit_plant.py", "new",
     "def keep(step):\n    try:\n        step()\n    finally:\n        return None\n", "b"),
    ("X14 finally: break in a loop that encloses the try, in skills/", "skills/exit_plant.py", "new",
     "def keep(steps):\n    for step in steps:\n        try:\n            step()\n        finally:\n            break\n", "b"),
    ("X15 a class defining __exit__ in hands/", "hands/exit_plant.py", "new",
     "class Keep:\n    def __enter__(self):\n        return self\n\n    def __exit__(self, kind, value, trace):\n"
     "        return True\n", "b"),
    ("X16 contextlib.ExitStack with a swallowing callback in brain/", "brain/exit_plant.py", "new",
     "import contextlib\n\n\ndef keep(step):\n    with contextlib.ExitStack() as stack:\n        stack.push(lambda *e: True)\n"
     "        step()\n", "b"),
    ("X17 finally: yield from controls.wait(1) in skills/", "skills/exit_plant.py", "new",
     "def keep(controls, step):\n    try:\n        yield from step()\n    finally:\n        yield from controls.wait(1)\n", "b"),
    ("X18 return inside a for loop inside a finally, in hands/", "hands/exit_plant.py", "new",
     "def keep(step, items):\n    try:\n        step()\n    finally:\n        for item in items:\n            return item\n", "b"),
    ("X19 ExitStack imported under another name in brain/", "brain/exit_plant.py", "new",
     "from contextlib import ExitStack as Stack\n\n\ndef keep(step):\n    with Stack() as stack:\n        step()\n", "b"),
    ("X20 finally: break in a nested loop's else, in skills/", "skills/exit_plant.py", "new",
     "def keep(steps, items):\n    for step in steps:\n        try:\n            step()\n        finally:\n"
     "            for item in items:\n                pass\n            else:\n                break\n", "b"),
    # (U2 spec 2026-10-30 D16, RV-7) a raise, or a failing assert, reached from a `finally` REPLACES the exit in flight;
    # each passed the 417df790 gate (measured, `s53/u2/probe_rv57.out`)
    ("X21 finally: raise ValueError(...) in skills/", "skills/exit_plant.py", "new",
     "def keep(step):\n    try:\n        yield from step()\n    finally:\n        raise ValueError('replaced')\n", "b"),
    ("X22 a bare finally: raise in brain/", "brain/exit_plant.py", "new",
     "def keep(step):\n    try:\n        step()\n    finally:\n        raise\n", "b"),
    ("X23 finally: try: f() except OSError: raise, in hands/", "hands/exit_plant.py", "new",
     "def keep(step, f):\n    try:\n        step()\n    finally:\n        try:\n            f()\n        except OSError:\n"
     "            raise\n", "b"),
    ("X24 finally: assert ok, in world/", "world/exit_plant.py", "new",
     "def keep(step, ok):\n    try:\n        step()\n    finally:\n        assert ok\n", "b"),
]

#: (U2 spec D16) CONTROL for X21-X24: a `raise` and an `assert` in the `try` body, and in a def nested in the `finally`
#: (its own scope), pass
RAISE_FORMS_CONTROL = '''\
"""finally: raise ValueError; finally: assert ok (mentions only)."""


def keep(step, ok):
    try:
        assert ok
        if not step():
            raise ValueError("not done")
    finally:
        def later():
            assert ok
            raise ValueError("later")

        _ = later
    return ok
'''

#: (D1) CONTROL for X07-X20: the same words as mentions, the narrow forms that are fine, and the scopes a `finally` may hold
EXIT_FORMS_CONTROL = '''\
"""GeneratorExit, BaseException, BaseExceptionGroup, ExitStack and AsyncExitStack are the host's; never `except:`,
`finally: return`, `finally: yield` or `def __exit__` here."""

# raise GeneratorExit; except BaseException: pass; contextlib.ExitStack(); finally: return None; def __exit__
WHY = "BaseException, BaseExceptionGroup and ExitStack belong to the host"


def keep(step, items):
    try:
        step()
    except ValueError:
        return None
    finally:
        def later():
            yield 1
            return 2

        for item in items:
            if item:
                break
            continue
        while items:
            break
        _ = later
    return items


def exit_menu(menu):
    return menu.exit_menu()
'''


class PlayLoopExitTests(GateTestCase):
    def test_the_play_loop_cannot_exit(self) -> None:
        """FAULT: each plant of `EXIT_PROBES` fails by its rule in its own file. CONTROL: the same words in a docstring, a
        comment or a sentence pass; the lifecycle keeps its `sys.exit` and the launcher its `KeyboardInterrupt` (the real
        package passes, with both files scanned). (U2 spec D16) FAULT X21-X24: a raise or an assert reached from a
        `finally` fails "b" (mutants S40h, S40i); CONTROL: the same in the `try` body and in a nested def pass."""
        for probe in EXIT_PROBES:
            with self.subTest(probe[0]):
                self.run_probe(probe)
        mention = ('"""It never calls sys.exit(), exit() or quit(), and never raises SystemExit or catches\n'
                   'KeyboardInterrupt."""\n\n# sys.exit(1); raise SystemExit; except KeyboardInterrupt\n'
                   'WHY = "SystemExit and KeyboardInterrupt belong to the host"\n')
        with planted_copy("brain/exit_mention.py", "new", mention) as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            self.assertEqual([v for v in result.violations if "exit_mention" in v.file], [], check_purity.report(result))
            self.assertTrue(result.passed, check_purity.report(result))
            self.assertIn("host/lifecycle.py", result.scanned)
            self.assertIn("host/launcher.py", result.scanned)
        self.assertIn("sys.exit(code)", (REAL_PACKAGE / "host" / "lifecycle.py").read_text(encoding="utf-8"))
        self.assertIn("except KeyboardInterrupt", (REAL_PACKAGE / "host" / "launcher.py").read_text(encoding="utf-8"))
        # (R1 + R2 follow-up, D1) CONTROL for X07-X20: mentions, `except ValueError:`, `def exit_menu`, and a `finally`
        # holding a nested def (with a return and a yield) and loops with their own break/continue, all pass
        with planted_copy("brain/exit_forms_control.py", "new", EXIT_FORMS_CONTROL) as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            self.assertEqual([str(v) for v in result.violations if "exit_forms_control" in v.file], [],
                             check_purity.report(result))
            self.assertTrue(result.passed, check_purity.report(result))
        # (U2 spec D16) CONTROL for X21-X24: a raise and an assert in the `try` body and in a def nested in the `finally`
        with planted_copy("skills/raise_forms_control.py", "new", RAISE_FORMS_CONTROL) as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            self.assertEqual([str(v) for v in result.violations if "raise_forms_control" in v.file], [],
                             check_purity.report(result))
            self.assertTrue(result.passed, check_purity.report(result))


class MentionTests(GateTestCase):
    def test_mentions_in_comments_docstrings_and_strings_do_not_fire(self) -> None:
        source = '''
            """This docstring says import modules.menuing and calls write_symbol('x', b'') and
            context.emulator.write_bytes(0, b'') and emulator.load_save_state(s) and reset() and
            sys.modules['modules.battle_handler'] and emulator._pressed_inputs |= 1 and exec(...)
            and getattr(x, n) and __import__('modules.menuing') and operator.methodcaller, and also
            dataclasses.inspect.getmembers(x), functools.update_wrapper, os.sys.path, '{0._x}'.format(o),
            case object(_core=c), Path('x').write_text('y'), open('x', 'w'), a.finalize_audit()."""

            # import modules.battle_strategies
            # from plugins.custom_modes.story_mode import StoryMode
            # context.emulator.write_bytes(0x02000000, b"\\x00"); set_event_flag("FLAG_X"); emulator.reset()
            # emulator._core.load_state(vf); sys.path.insert(0, "gates"); import importlib; vars(x)
            # from sys import _getframe; os.environ['X'] = '1'; time.sleep = print; setattr(x, 'y', 1)

            # step 0.1: a.watch_guard(g, f); a.arm_exit_watchdog(0); signal.signal(signal.SIGINT, h)
            # atexit.register(f); modules.main.get_bot_listeners = f; sys.path.insert(0, "x")

            NOTE = "never call write_to_save_block or set_event_var or load_save_state from here"
            LATER = "watch_guard and arm_exit_watchdog belong to the host; get_bot_listeners is main.py's"
            MORE = f"see modules.menuing and {NOTE}, and never touch _pressed_inputs or sys.modules"
            WHY = "the press_button door is the controller's; run_frame belongs to the main loop"
            ALSO = "never use str.format with {0.attribute} fields, nor write_text, nor rename"


            def explain() -> str:
                """Mentions modules.modes.util.walking and write_bytes and __getattribute__, as text only."""
                return "reset is a word, write_symbol is a word, getattr is a word, format is a word"


            class Notes:
                """A class docstring naming load_save_game and _core and sys.path and __pycache__."""

                field = "x"
                """An attribute docstring naming ai_player.gates.check_purity and modules.menuing."""


            def terse() -> None:
                """reset"""


            "modules.menuing"
            "_pressed_inputs"
            "finalize_audit"
            '''
        # The last three are docstrings / string statements whose WHOLE value is an identifier: only
        # the string-statement exemption keeps them silent (a mutation run proved sentences alone
        # would not test it).
        with planted_copy("planted_mentions.py", "new", source) as (package, hook):
            result = check_purity.scan(package, hook, REAL_BUILD_ROOT)
            planted = [v for v in result.violations if "planted_mentions.py" in v.file]
            self.assertEqual(planted, [], f"mentions fired the gate: {planted}")
            self.assertTrue(result.passed, check_purity.report(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
