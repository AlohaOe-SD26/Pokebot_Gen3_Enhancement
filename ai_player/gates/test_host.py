"""UNIT proofs for the step-0.1 host fixes, each with a mutant half that REVERTS the fix.

    py -3.12 ai_player/gates/test_host.py          # or: py -3.12 -m unittest ai_player.gates.test_host

WHY (the adversarial review of step 0: "each fix needs an arm or test that FAILS when the fix is
reverted"). Every test here runs its harness in a FRESH interpreter, twice: once on the real code (the
fix holds) and once on a temporary copy with that one fix reverted by a text mutation of the REAL file
(the same harness must then see the old failure). A test that cannot tell the two apart proves
nothing, so the mutant half is part of every test, not an afterthought. Each fix also has a LIVE arm in
`live_step0.py`; these are the fast, isolated halves.

  finding 4  the hook APPENDS the repo root to sys.path, so the standard library wins for a colliding
             name (`tabnanny.py` at the repo root). The mutant is a copy of the REAL hook file with its
             `sys.path.append(root)` reverted to step 0's `sys.path.insert(0, root)`, loaded the same
             way (round 2: the first version ran a copy of step 0's line inside the harness instead).
  finding 6  the session refuses to start when the framework is in debug mode (exit 9 with a verdict
             file); without the check the start falls through. (Live: arms G and M6.)
  finding 8  the instrument's look-ahead depth is PER THREAD: a `peek_frame` open in one thread must
             not turn another thread's frame into a look-ahead. AND (round 2, the verifier's V5, the
             same-thread variant): a frame the MAIN LOOP runs is real even while a look-ahead is open
             on the same thread; a frame run from inside the look-ahead's body stays a look-ahead
             (the control). (Live: arms XWT and M8t for the cross-thread case; XW, M8, M8c for V5.)
  finding 3  the instrument's objects refuse attribute writes from outside and COUNT each attempt;
             the counter store only grows (the live arm XK attacks the same in a real run).
  round 2 (c) the objects that decide how a run ENDS (the lifecycle, the session, the listener
             isolation, the guard listener) refuse and count writes from any file but their own,
             while their own module still writes them (the control). (Live: arms XK and M3.)
  round 3 (the verifier's two notes on round 2):
    registry  the instrument's REGISTRY and its counter stores answer only the instrument's own file:
             `_REGISTRY.payload_of(counters).add("real_frames", None, None, N)` turned an UNVERIFIED
             run CLEAN; now it is refused and counted, and so is a store handed out by any route.
             The mutant halves revert the registry check and the store check, and the same attack
             turns UNVERIFIED into CLEAN again. (Live: arm XK's five registry attacks, and M3.)
    fence    the interrupt-watch race: while one thread finishes the run, a frame on ANOTHER thread
             must not run (it used to run unaudited, or after the verdict as a false
             `ran-after-finish` BREACH), and the finish waits for a frame already in flight. The
             mutant half reverts the fence: the finish completes while a frame is still running, and
             the next frame runs after the verdict and ends the process as `ran-after-finish`.
             (Live: arms IG, IR and their mutants M9, M9r; M9w for the watch's measured wording.)

TEST-SIDE RESIDUAL, on purpose: since round 3 the registry refuses every caller outside the
instrument's file, and a few harnesses must still reach the instrument's `_State` (to tell it where
the framework's files are, with no emulator). They do it through code COMPILED under the instrument's
own file name (`_instrument_grab`), the residual the instrument's docstring names; the static gate
refuses `compile` in the AI's own code.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUILD_ROOT = REPO / "sandbox-pokebot"
HOOK = BUILD_ROOT / "plugins" / "custom_modes" / "ai_player_mode.py"
RESULT_TAG = "HARNESS-RESULT "

#: The hook's line under test (finding 4) and step 0's line, which the mutant puts back.
HOOK_APPEND = "    sys.path.append(root)\n"
HOOK_STEP0_PREPEND = "    sys.path.insert(0, root)  # MUTANT: step 0's prepend\n"
#: The instrument's frame classification (finding 8, same thread): the main loop first.
ORDER_FIX = "        if main_loop:\n            return \"real\"\n        if getattr(s.local, \"peek\", 0) > 0:\n            return \"look-ahead\"\n"
ORDER_STEP01 = (
    "        if getattr(s.local, \"peek\", 0) > 0:  # MUTANT: step 0.1's order\n            return \"look-ahead\"\n"
    "        if main_loop:\n            return \"real\"\n"
)
#: The owner-file instance guard (finding 3 and round 2 (c)).
GUARD_CHECK = (
    "        caller = sys._getframe(1)\n        if caller.f_code.co_filename != _REGISTRY.owner_of(type(self)):\n"
    "            _tamper_all(f\"{type(self).__name__}.{name} was assigned from {_where(caller)}\")"
)
GUARD_OFF = (
    "        caller = sys._getframe(1)\n        if False:  # MUTANT\n"
    "            _tamper_all(f\"{type(self).__name__}.{name} was assigned from {_where(caller)}\")"
)
#: Round 3: the registry's caller check, and each counter store's caller check.
REGISTRY_CHECK = "        if caller.f_code.co_filename != own_file:\n            problem = f\"the instrument's registry"
REGISTRY_OFF = "        if False:  # MUTANT: the registry's caller check reverted\n            problem = f\"the instrument's registry"
STORE_CHECK = "        if caller.f_code.co_filename != own_file:\n            values[\"instrument_tampered\"] += 1\n"
STORE_OFF = "        if False:  # MUTANT: the store's caller check reverted\n            values[\"instrument_tampered\"] += 1\n"
#: Round 3: the frame fence (a frame on another thread while one thread finishes; a frame in flight).
FENCE_CHECK = "        return finisher is not None and finisher != threading.get_ident()\n"
FENCE_OFF = "        return False  # MUTANT: the frame fence reverted\n"
FENCE_WAIT = "        held = self._fence_frames()\n"
FENCE_WAIT_OFF = "        held = False  # MUTANT: the finish no longer waits for a frame in flight\n"
COUNT_CHECK = "        if type(count) is not int or count < 1:\n"
COUNT_OFF = "        if False:  # MUTANT\n"


# ---------------------------------------------------------------------------------- harnesses
# Each runs in a fresh interpreter (`--harness NAME --root ROOT`), with ROOT = the folder that
# contains the `ai_player` under test, and prints one `HARNESS-RESULT {json}` line.


def _instrument_grab(module):
    """TEST SIDE ONLY. The registry answers only code of the instrument's own file (round 3), so a
    harness that must set up the instrument's `_State` reaches it through a function COMPILED under
    that file's name: the residual the instrument documents, used here on purpose."""
    namespace: dict = {}
    exec(compile("def grab(registry, owner):\n    return registry.payload_of(owner)\n", module._OWN_FILE, "exec"), namespace)
    registry = module._REGISTRY
    return lambda owner: namespace["grab"](registry, owner)


def _framework_frame_chain(module) -> tuple[dict, dict]:
    """Code compiled under the framework's own file names, so the instrument sees the exact call
    chain of a real frame: main.py `main_loop` -> libmgba.py `run_single_frame` -> the core's
    `run_frame` (here: whatever callable is passed in)."""
    emulator_code: dict = {}
    main_code: dict = {}
    exec(compile("def run_single_frame(core_run_frame, *args):\n    return core_run_frame(*args)\n",
                 str(BUILD_ROOT / "modules" / "libmgba.py"), "exec"), emulator_code)
    exec(compile("def main_loop(run_single_frame, core_run_frame, *args):\n    return run_single_frame(core_run_frame, *args)\n",
                 str(BUILD_ROOT / "modules" / "main.py"), "exec"), main_code)
    return emulator_code, main_code


def harness_hook_path(root: Path, hook_file: str) -> dict:
    """Load a hook FILE the way a plugin is loaded (by path), with AI_PLAYER_PACKAGE_ROOT pointing at a
    folder that holds a fake `ai_player` AND a `tabnanny.py` named like a standard-library module, and
    run the hook's own path function. `hook_file` is the real hook or a mutated copy of it."""
    import importlib.util

    sys.path.insert(0, str(BUILD_ROOT))
    os.environ["AI_PLAYER_PACKAGE_ROOT"] = str(root)
    spec = importlib.util.spec_from_file_location("ai_player_hook_under_test", hook_file)
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    already = "tabnanny" in sys.modules
    hook._append_repo_root_to_path()
    import ai_player  # noqa: F401 - must come from `root`: proves the root IS on the path
    import tabnanny

    return {
        "hook_file": hook_file,
        "tabnanny_imported_before": already,
        "tabnanny_file": getattr(tabnanny, "__file__", ""),
        "tabnanny_is_the_plant": bool(getattr(tabnanny, "PLANTED", False)),
        "ai_player_file": ai_player.__file__,
        "root_index": sys.path.index(str(root)),
        "path_len": len(sys.path),
    }


def harness_debug_refusal(root: Path, run_dir: Path) -> dict:
    """Start a session with the framework in debug mode; report how it ended and its verdict file."""
    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    os.environ["AI_PLAYER_RUN_DIR"] = str(run_dir)
    os.environ["AI_PLAYER_PACKAGE_ROOT"] = str(root)
    from modules.config.schemas_v1 import HTTP
    from modules.context import context

    context.debug = True
    context.bot_mode = "AI Player"
    # The sandbox's GLOBAL profiles/http.yml switches the HTTP server ON (a fork divergence), and with
    # no profile loaded that is what this context holds. Off here, so only the debug check can refuse.
    context.config.http = HTTP()
    from ai_player.host.session import start_session

    code = None
    try:
        start_session(str(root))
    except SystemExit as stop:
        code = stop.code
    verdict_path = run_dir / "purity.json"
    verdict = json.loads(verdict_path.read_text(encoding="utf-8")) if verdict_path.is_file() else None
    log = (run_dir / "ai_player.log").read_text(encoding="utf-8") if (run_dir / "ai_player.log").is_file() else ""
    return {"exit_code": code, "verdict": verdict, "refused_line": [l for l in log.splitlines() if "REFUSED" in l]}


def harness_peek_threads(root: Path) -> dict:
    """Open a look-ahead (`peek_frame`) in a worker thread and, while it is open, ask the instrument
    how it would classify a frame run by the MAIN thread."""
    import contextlib
    import threading

    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    from ai_player.host.attribution import Attribution

    attribution = Attribution()
    entered, release = threading.Event(), threading.Event()
    kinds: dict[str, str] = {}

    @contextlib.contextmanager
    def fake_peek():
        yield None

    wrapper = attribution._make_peek_wrapper(fake_peek)

    def worker() -> None:
        with wrapper():
            kinds["worker_inside_its_own_peek"] = attribution._frame_kind(sys._getframe(0))
            entered.set()
            release.wait(10)

    thread = threading.Thread(target=worker)
    thread.start()
    entered.wait(10)
    kinds["main_while_worker_peeks"] = attribution._frame_kind(sys._getframe(0))
    release.set()
    thread.join(10)
    kinds["main_after"] = attribution._frame_kind(sys._getframe(0))
    return kinds


def harness_peek_same_thread(root: Path) -> dict:
    """The verifier's V5 at unit level: open a look-ahead on THIS thread and leave it open, then let
    code compiled under the framework's own file names run a frame the way main.py does
    (`main_loop` -> `run_single_frame` -> the core's `run_frame`), and a frame the way a look-ahead's
    body does (`modules/pokemon_party.py` calls the core's `run_frame` inside `peek_frame`)."""
    import contextlib

    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    import ai_player.host.attribution as module

    attribution = module.Attribution()
    state = _instrument_grab(module)(attribution)  # the documented residual, test side (round 3)
    libmgba = BUILD_ROOT / "modules" / "libmgba.py"
    main = BUILD_ROOT / "modules" / "main.py"
    party = BUILD_ROOT / "modules" / "pokemon_party.py"
    # What `install()` sets from the real emulator (no emulator here); the test side may write it.
    object.__setattr__(state, "libmgba_path", module._norm(libmgba))
    object.__setattr__(state, "main_path", module._norm(main))
    emulator_code: dict = {}
    main_code: dict = {}
    party_code: dict = {}
    exec(compile("def run_single_frame(core_run_frame):\n    return core_run_frame()\n", str(libmgba), "exec"), emulator_code)
    exec(compile("def main_loop(run_single_frame, core_run_frame):\n    return run_single_frame(core_run_frame)\n", str(main), "exec"), main_code)
    exec(compile("def read_party(core_run_frame):\n    return core_run_frame()\n", str(party), "exec"), party_code)

    def core_run_frame() -> str:
        return attribution._frame_kind(sys._getframe(1))  # what the run_frame wrapper sees as its caller

    def main_loop_frame() -> str:
        # main_loop -> run_single_frame -> the core's run_frame: the exact call chain of a real frame
        return main_code["main_loop"](emulator_code["run_single_frame"], core_run_frame)

    @contextlib.contextmanager
    def fake_peek():
        yield None

    wrapper = attribution._make_peek_wrapper(fake_peek)
    kinds = {"main_loop_frame_no_peek": main_loop_frame(), "peek_body_frame_no_peek": party_code["read_party"](core_run_frame)}
    held = wrapper()
    held.__enter__()  # entered on THIS thread and left open, as V5 did
    kinds["main_loop_frame_inside_open_peek"] = main_loop_frame()
    kinds["peek_body_frame_inside_open_peek"] = party_code["read_party"](core_run_frame)
    return kinds


def harness_counter_attacks(root: Path) -> dict:
    """Attribute-level attacks on a fresh instrument (no emulator needed): each must be refused and
    COUNTED. Reports the outcome of each and the tamper count."""
    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    import ai_player.host.attribution as module
    from ai_player.host.attribution import Attribution

    attribution = Attribution()
    counters = attribution.counters
    outcomes: dict[str, str] = {}

    def attempt(label: str, action) -> None:
        before = counters.instrument_tampered
        try:
            action()
            result = "ACCEPTED"
        except Exception as error:  # noqa: BLE001
            result = f"refused ({type(error).__name__})"
        outcomes[label] = f"{result}; counted={counters.instrument_tampered > before}"

    attempt("counters.real_frames = 0", lambda: setattr(counters, "real_frames", 0))
    attempt("counters._values lookup", lambda: counters._values)
    attempt("counters._add(count=-1)", lambda: counters._add("real_frames", count=-1))
    attempt("store add(-1)", lambda: module._REGISTRY.payload_of(counters).add("real_frames", None, None, -1))
    attempt("attribution._installed = False", lambda: setattr(attribution, "_installed", False))
    attempt("type(counters).verdict = ...", lambda: setattr(type(counters), "verdict", lambda self: "CLEAN"))
    attempt("module.BREACH_COUNTERS = ()", lambda: setattr(module, "BREACH_COUNTERS", ()))
    # Round 3: every route through the registry (a module attribute anyone can name).
    registry = module._REGISTRY
    attempt("registry payload_of(counters).add(+5)", lambda: registry.payload_of(counters).add("real_frames", None, None, 5))
    attempt("registry vaults()[0].add(+5)", lambda: registry.vaults()[0].add("real_frames", None, None, 5))
    attempt("registry payload_of(attribution).local.depth = 1", lambda: setattr(registry.payload_of(attribution).local, "depth", 1))
    attempt("registry payload_of(attribution).brain_cache poisoned",
            lambda: registry.payload_of(attribution).brain_cache.update({"map_path.py": False}))
    attempt("registry sealed() fingerprints cleared", lambda: registry.sealed()[0][1].clear())
    attempt("registry bind() a forged payload", lambda: registry.bind(object(), None))
    # ...and a store handed out by the residual route (compiled under the instrument's name): its own
    # check still refuses a caller from any other file.
    store = _instrument_grab(module)(counters)
    attempt("a handed-out store's add(+5)", lambda: store.add("real_frames", None, None, 5))
    attempt("a handed-out store's note()", lambda: store.note("tamper", "forged origin"))
    return {"outcomes": outcomes, "instrument_tampered": counters.instrument_tampered, "real_frames": counters.real_frames}


def harness_unverified_to_clean(root: Path, route: str) -> dict:
    """The verifier's exact claim (round 3): a fresh instrument has audited no frame, so its verdict
    is UNVERIFIED; one POSITIVE count added to `real_frames` from outside the instrument must not make
    it CLEAN. `route` is "registry" (`_REGISTRY.payload_of(counters).add`) or "store" (a store handed
    out by the residual route, then called from this file)."""
    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    import ai_player.host.attribution as module

    attribution = module.Attribution()
    counters = attribution.counters
    before = counters.verdict()
    try:
        if route == "registry":
            module._REGISTRY.payload_of(counters).add("real_frames", None, None, 1)
        else:
            _instrument_grab(module)(counters).add("real_frames", None, None, 1)
        outcome = "ACCEPTED"
    except Exception as error:  # noqa: BLE001
        outcome = f"refused ({type(error).__name__})"
    return {
        "route": route, "verdict_before": before, "outcome": outcome, "verdict_after": counters.verdict(),
        "real_frames": counters.real_frames, "instrument_tampered": counters.instrument_tampered,
    }


def harness_finish_fence(root: Path) -> dict:
    """Round 3, the verifier's interrupt-watch race, at unit level and deterministic. Three threads
    and the instrument's real `run_frame` wrapper, driven through code compiled under the framework's
    own file names (so the frames are REAL main-loop frames to the instrument):
      1. thread `frame-1` starts a frame that stays IN FLIGHT (its native part blocks on an event);
      2. thread `finisher` runs a function named `finish` compiled under `host/lifecycle.py`'s name
         (what the instrument accepts as the lifecycle's finish): `finalize_audit`, then
         `write_verdict_file`. After 1 s: has the finish completed while the frame was in flight?
         Then the frame is released, and the finish must complete;
      3. thread `frame-2` (the main thread waking up late) starts a frame after the verdict. After 2 s:
         did that frame run?
    A `HARNESS-PARTIAL` line is printed after step 2, because a run without the fence ends the
    process in step 3 (`ran-after-finish`, exit 6) before the final line."""
    import threading
    import time

    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    import ai_player.host.attribution as module

    attribution = module.Attribution()
    state = _instrument_grab(module)(attribution)
    object.__setattr__(state, "libmgba_path", module._norm(BUILD_ROOT / "modules" / "libmgba.py"))
    object.__setattr__(state, "main_path", module._norm(BUILD_ROOT / "modules" / "main.py"))
    emulator_code, main_code = _framework_frame_chain(module)
    lifecycle_code: dict = {}
    exec(compile("def finish(attribution):\n    attribution.finalize_audit()\n"
                 "    return attribution.write_verdict_file(None, {'exit_reason': 'harness'})\n",
                 str(module._LIFECYCLE_FILE), "exec"), lifecycle_code)

    events: list[tuple[str, str, float]] = []
    release = threading.Event()
    finished = threading.Event()
    keep_alive = threading.Event()

    def native_frame(block: bool) -> None:
        events.append(("frame-start", threading.current_thread().name, time.monotonic()))
        if block:
            release.wait(20)
        events.append(("frame-end", threading.current_thread().name, time.monotonic()))

    wrapper = attribution._make_run_frame_wrapper(native_frame)

    def main_loop_frame(block: bool) -> None:
        main_code["main_loop"](emulator_code["run_single_frame"], wrapper, block)

    def finisher() -> None:
        lifecycle_code["finish"](attribution)
        events.append(("finish-done", threading.current_thread().name, time.monotonic()))
        finished.set()
        keep_alive.wait(60)  # the finishing thread stays alive, as the interrupt watch does until os._exit

    frame_1 = threading.Thread(target=main_loop_frame, args=(True,), name="frame-1", daemon=True)
    frame_1.start()
    for _ in range(200):
        if any(kind == "frame-start" for kind, _, _ in events):
            break
        time.sleep(0.01)
    finish_thread = threading.Thread(target=finisher, name="finisher", daemon=True)
    finish_thread.start()
    time.sleep(1.0)
    partial = {
        "frame_1_in_flight_at_check": not any(kind == "frame-end" for kind, _, _ in events),
        "finish_completed_while_frame_in_flight": finished.is_set(),
    }
    release.set()
    frame_1.join(10)
    partial["finish_completed_after_release"] = finished.wait(10)
    order = [kind for kind, _, _ in events]
    partial["order"] = order
    partial["frame_in_flight_recorded"] = bool(state.frame_in_flight)
    print("HARNESS-PARTIAL " + json.dumps(partial), flush=True)

    frame_2 = threading.Thread(target=main_loop_frame, args=(False,), name="frame-2", daemon=True)
    frame_2.start()
    time.sleep(2.0)
    return {
        **partial,
        "frame_2_ran": any(kind == "frame-start" and name == "frame-2" for kind, name, _ in events),
        "frame_2_still_waiting": frame_2.is_alive(),
        "ran_after_finish": attribution.counters.ran_after_finish,
    }


def harness_guarded_attacks(root: Path) -> dict:
    """Round 2 (c): build a real Session (no emulator needed until `start`) and write the state that
    decides how the run ends, from THIS file (not the owner of any of those classes). Each must be
    refused and counted. CONTROL: the owning modules' own code still writes the same objects."""
    sys.path.insert(0, str(BUILD_ROOT))
    sys.path.append(str(root))
    from ai_player.host.session import Session
    from ai_player.options import RunOptions

    session = Session(RunOptions.from_env(), None)
    counters = session.attribution.counters
    lifecycle, isolation, guard = session.lifecycle, session.isolation, session.guard
    outcomes: dict[str, str] = {}

    def attempt(label: str, action) -> None:
        before = counters.instrument_tampered
        try:
            action()
            result = "ACCEPTED"
        except Exception as error:  # noqa: BLE001
            result = f"refused ({type(error).__name__})"
        outcomes[label] = f"{result}; counted={counters.instrument_tampered > before}"

    attempt("lifecycle._verdict_path = None", lambda: setattr(lifecycle, "_verdict_path", None))
    attempt("lifecycle._attribution = None", lambda: setattr(lifecycle, "_attribution", None))
    attempt("lifecycle._finishing = True", lambda: setattr(lifecycle, "_finishing", True))
    attempt("del lifecycle._abandoned", lambda: delattr(lifecycle, "_abandoned"))
    attempt("session.lifecycle = None", lambda: setattr(session, "lifecycle", None))
    attempt("session.frame_cap = 10**12", lambda: setattr(session, "frame_cap", 10**12))
    attempt("session.interrupted = None", lambda: setattr(session, "interrupted", None))
    attempt("isolation._exit = 'forged'", lambda: setattr(isolation, "_exit", "forged"))
    attempt("guard._on_frame = print", lambda: setattr(guard, "_on_frame", print))
    # CONTROL: the owners' own code is not refused (and not counted).
    before = counters.instrument_tampered
    lifecycle.note_abandoned()  # lifecycle.py writes lifecycle._abandoned
    session._on_signal(2, None)  # session.py writes session.interrupted
    controls = {
        "lifecycle.note_abandoned() took effect": lifecycle.abandoned is True,
        "session._on_signal(2) took effect": session.interrupted == 2,
        "the owners' writes were not counted": counters.instrument_tampered == before,
        "no attack changed the state": (session.lifecycle is lifecycle and session.frame_cap < 10**12
                                        and lifecycle.finishing is False),
    }
    return {"outcomes": outcomes, "controls": controls, "instrument_tampered": counters.instrument_tampered}


HARNESSES = {
    "hook_path": lambda root, extra: harness_hook_path(root, extra),
    "debug_refusal": lambda root, extra: harness_debug_refusal(root, Path(extra)),
    "peek_threads": lambda root, extra: harness_peek_threads(root),
    "peek_same_thread": lambda root, extra: harness_peek_same_thread(root),
    "counter_attacks": lambda root, extra: harness_counter_attacks(root),
    "guarded_attacks": lambda root, extra: harness_guarded_attacks(root),
    "unverified_to_clean": lambda root, extra: harness_unverified_to_clean(root, extra),
    "finish_fence": lambda root, extra: harness_finish_fence(root),
}
PARTIAL_TAG = "HARNESS-PARTIAL "


# ---------------------------------------------------------------------------------- test plumbing
def run_harness_raw(name: str, root: Path, extra: str = "") -> tuple[int, str, dict | None, dict | None]:
    """(exit code, output, the result or None, the partial result or None)."""
    done = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--harness", name, "--root", str(root), "--extra", extra],
        cwd=str(BUILD_ROOT), capture_output=True, text=True, timeout=180,
        env={**{k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}, "PYTHONUTF8": "1",
             "PYTHONDONTWRITEBYTECODE": "1"},
    )
    result = partial = None
    for line in done.stdout.splitlines():
        if line.startswith(RESULT_TAG):
            result = json.loads(line[len(RESULT_TAG):])
        elif line.startswith(PARTIAL_TAG):
            partial = json.loads(line[len(PARTIAL_TAG):])
    return done.returncode, done.stdout + done.stderr, result, partial


def run_harness(name: str, root: Path, extra: str = "") -> dict:
    code, output, result, _ = run_harness_raw(name, root, extra)
    if result is None:
        raise AssertionError(f"harness {name} printed no result (exit {code}):\n{output[-6000:]}")
    return result


def mutate(text: str, old: str, new: str, where: str) -> str:
    if text.count(old) != 1:
        raise AssertionError(f"mutation anchor not unique in {where} ({text.count(old)} hits): {old!r}")
    return text.replace(old, new)


def copy_package(mutations: list[tuple[str, str, str]]) -> Path:
    """A temporary copy of the real package with each (file, old, new) mutation applied EXACTLY once."""
    root = Path(tempfile.mkdtemp(prefix="ai_player_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures"))
    try:
        for relative, old, new in mutations:
            path = root / "ai_player" / relative
            path.write_text(mutate(path.read_text(encoding="utf-8"), old, new, relative), encoding="utf-8")
    except AssertionError:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


class HookPathTests(unittest.TestCase):
    """Finding 4: the standard library must win over a repo-root file with a library's name."""

    def _plant_root(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="ai_player_root_"))
        (root / "ai_player").mkdir()
        (root / "ai_player" / "__init__.py").write_text("MODE_NAME = 'AI Player'\n", encoding="utf-8")
        (root / "tabnanny.py").write_text("PLANTED = True  # named like the standard library's tabnanny\n", encoding="utf-8")
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def test_the_hook_appends_and_the_standard_library_wins(self) -> None:
        root = self._plant_root()
        result = run_harness("hook_path", root, str(HOOK))
        self.assertFalse(result["tabnanny_imported_before"], f"NON-VACUITY: tabnanny was already loaded: {result}")
        self.assertTrue(result["ai_player_file"].startswith(str(root)), f"the root is on the path (ai_player came from it): {result}")
        self.assertFalse(result["tabnanny_is_the_plant"], f"the standard library must win: {result}")
        self.assertEqual(result["root_index"], result["path_len"] - 1, f"the root is APPENDED: {result}")

    def test_the_hook_reverted_to_step0_loses_to_the_plant(self) -> None:
        """MUTANT: a copy of the REAL hook file with its append reverted to step 0's prepend, loaded
        exactly as above. The plant must win; without this, the test above could pass for a reason
        that has nothing to do with the hook's line."""
        root = self._plant_root()
        folder = Path(tempfile.mkdtemp(prefix="ai_player_hook_mutant_"))
        self.addCleanup(shutil.rmtree, folder, True)
        mutant = folder / HOOK.name
        mutant.write_text(mutate(HOOK.read_text(encoding="utf-8"), HOOK_APPEND, HOOK_STEP0_PREPEND, HOOK.name), encoding="utf-8")
        result = run_harness("hook_path", root, str(mutant))
        self.assertEqual(result["hook_file"], str(mutant), result)
        self.assertTrue(result["tabnanny_is_the_plant"], f"step 0's prepend must lose to the plant: {result}")
        self.assertEqual(result["root_index"], 0, result)


class DebugRefusalTests(unittest.TestCase):
    """Finding 6: never start in the framework's debug mode, where main.py parks a failing mode."""

    def _run(self, root: Path) -> dict:
        run_dir = Path(tempfile.mkdtemp(prefix="ai_player_debug_run_"))
        self.addCleanup(shutil.rmtree, run_dir, True)
        return run_harness("debug_refusal", root, str(run_dir))

    def test_debug_mode_is_refused_with_a_verdict(self) -> None:
        result = self._run(REPO)
        self.assertEqual(result["exit_code"], 9, result)
        verdict = result["verdict"] or {}
        self.assertEqual((verdict.get("facts") or {}).get("exit_reason"), "refused-debug-mode", result)
        self.assertEqual(verdict.get("verdict"), "UNVERIFIED", result)
        self.assertTrue(result["refused_line"], result)

    def test_without_the_check_the_start_does_not_refuse(self) -> None:
        """MUTANT: the debug check reverted. The same harness must see the start fall through (here to
        the instrument's install, which crashes for want of an emulator; the live mutant arm M6 shows
        what a real debug-mode run then does)."""
        root = copy_package([("host/session.py", "        if debug:\n", "        if False:  # MUTANT\n")])
        self.addCleanup(shutil.rmtree, root, True)
        result = self._run(root)
        reason = ((result["verdict"] or {}).get("facts") or {}).get("exit_reason")
        self.assertNotEqual(reason, "refused-debug-mode", result)
        self.assertEqual((reason, result["exit_code"]), ("crash", 2), result)


class PeekThreadTests(unittest.TestCase):
    """Finding 8: the look-ahead depth belongs to the thread that opened the look-ahead."""

    def test_a_peek_in_another_thread_does_not_hide_a_frame(self) -> None:
        result = run_harness("peek_threads", REPO)
        self.assertEqual(result["worker_inside_its_own_peek"], "look-ahead", f"NON-VACUITY: the wrapper marks its own thread: {result}")
        self.assertEqual(result["main_while_worker_peeks"], "extra", f"the main thread's frame must not be a look-ahead: {result}")
        self.assertEqual(result["main_after"], "extra", result)

    def test_a_shared_depth_hides_the_frame(self) -> None:
        """MUTANT: step 0's shared depth (one counter for every thread). The same harness must see the
        main thread's frame classified as a look-ahead, i.e. skipped by the audit."""
        root = copy_package([
            ("host/attribution.py", "_MISSING = object()\n", "_MISSING = object()\n_SHARED_PEEK = type('Shared', (), {})()  # MUTANT\n"),
            ("host/attribution.py", "        local = _REGISTRY.payload_of(self).local\n\n        @contextlib.contextmanager",
             "        local = _SHARED_PEEK  # MUTANT\n\n        @contextlib.contextmanager"),
            ("host/attribution.py", "        if getattr(s.local, \"peek\", 0) > 0:\n            return \"look-ahead\"\n",
             "        if getattr(_SHARED_PEEK, \"peek\", 0) > 0:  # MUTANT\n            return \"look-ahead\"\n"),
        ])
        self.addCleanup(shutil.rmtree, root, True)
        result = run_harness("peek_threads", root)
        self.assertEqual(result["main_while_worker_peeks"], "look-ahead", f"the mutant must misclassify: {result}")


class PeekSameThreadTests(unittest.TestCase):
    """Finding 8, same thread (the verifier's V5): an open look-ahead must not hide the main loop's frames."""

    def test_a_main_loop_frame_is_real_inside_an_open_peek(self) -> None:
        result = run_harness("peek_same_thread", REPO)
        self.assertEqual(result["main_loop_frame_no_peek"], "real", f"NON-VACUITY: the harness's main loop is recognised: {result}")
        self.assertEqual(result["main_loop_frame_inside_open_peek"], "real", f"the main loop's frame must stay real: {result}")
        self.assertEqual(result["peek_body_frame_inside_open_peek"], "look-ahead", f"CONTROL: a frame from a look-ahead's body stays a look-ahead: {result}")
        self.assertEqual(result["peek_body_frame_no_peek"], "extra", f"CONTROL: the same frame outside a look-ahead is extra: {result}")

    def test_step01_order_hides_the_main_loop_frame(self) -> None:
        """MUTANT: step 0.1's order (the look-ahead depth before the main loop): the same harness must
        see the main loop's frame turned into a look-ahead, which is how V5 went unaudited."""
        root = copy_package([("host/attribution.py", ORDER_FIX, ORDER_STEP01)])
        self.addCleanup(shutil.rmtree, root, True)
        result = run_harness("peek_same_thread", root)
        self.assertEqual(result["main_loop_frame_no_peek"], "real", result)
        self.assertEqual(result["main_loop_frame_inside_open_peek"], "look-ahead", f"the mutant must misclassify: {result}")


class CounterAttackTests(unittest.TestCase):
    """Finding 3, at unit level (the live arm XK does the same inside a real run)."""

    def test_every_attack_is_refused_and_counted(self) -> None:
        result = run_harness("counter_attacks", REPO)
        for label, outcome in result["outcomes"].items():
            with self.subTest(label):
                self.assertTrue(outcome.startswith("refused") and outcome.endswith("counted=True"), f"{label}: {outcome}")
        self.assertGreaterEqual(result["instrument_tampered"], len(result["outcomes"]), result)

    def test_without_the_guards_the_attacks_get_through(self) -> None:
        """MUTANT: the instance guard, the store's counts-only-grow check, and (round 3) the registry's
        and the stores' caller checks reverted."""
        root = copy_package([
            ("host/attribution.py", GUARD_CHECK, GUARD_OFF),
            ("host/attribution.py", COUNT_CHECK, COUNT_OFF),
            ("host/attribution.py", REGISTRY_CHECK, REGISTRY_OFF),
            ("host/attribution.py", STORE_CHECK, STORE_OFF),
        ])
        self.addCleanup(shutil.rmtree, root, True)
        result = run_harness("counter_attacks", root)
        self.assertTrue(result["outcomes"]["store add(-1)"].startswith("ACCEPTED"), result)
        # The instrument's objects hold no state (`__slots__ = ()`), so Python itself still refuses these
        # writes; without the guard nobody COUNTS them, and an uncounted refusal cannot be graded.
        for label in ("counters.real_frames = 0", "attribution._installed = False"):
            with self.subTest(label):
                self.assertTrue(result["outcomes"][label].endswith("counted=False"), result)
        for label in ("registry payload_of(counters).add(+5)", "registry vaults()[0].add(+5)",
                      "registry payload_of(attribution).local.depth = 1",
                      "registry payload_of(attribution).brain_cache poisoned",
                      "a handed-out store's add(+5)", "a handed-out store's note()"):
            with self.subTest(label):
                self.assertEqual(result["outcomes"][label], "ACCEPTED; counted=False", result)
        # The fingerprints are a TUPLE since round 3, so even an accepted `sealed()` cannot clear them.
        self.assertTrue(result["outcomes"]["registry sealed() fingerprints cleared"].startswith("refused (AttributeError)"), result)

    def test_without_the_registry_check_the_state_routes_get_through(self) -> None:
        """MUTANT: ONLY the registry's caller check reverted. The routes to the instrument's `_State`
        (the per-thread door depth, the bot-code cache) are open again and nobody counts them; the
        counter stores' own check still refuses a count (the other layer)."""
        root = copy_package([("host/attribution.py", REGISTRY_CHECK, REGISTRY_OFF)])
        self.addCleanup(shutil.rmtree, root, True)
        result = run_harness("counter_attacks", root)
        for label in ("registry payload_of(attribution).local.depth = 1", "registry payload_of(attribution).brain_cache poisoned"):
            with self.subTest(label):
                self.assertEqual(result["outcomes"][label], "ACCEPTED; counted=False", result)
        self.assertEqual(result["outcomes"]["registry payload_of(counters).add(+5)"], "refused (PermissionError); counted=True", result)


class UnverifiedToCleanTests(unittest.TestCase):
    """Round 3, the verifier's second note: one positive count from outside must not turn UNVERIFIED into CLEAN."""

    def _check_refused(self, route: str) -> None:
        result = run_harness("unverified_to_clean", REPO, route)
        self.assertEqual(result["verdict_before"], "UNVERIFIED", f"NON-VACUITY: no frame audited yet: {result}")
        self.assertTrue(result["outcome"].startswith("refused"), result)
        self.assertEqual(result["real_frames"], 0, result)
        self.assertGreaterEqual(result["instrument_tampered"], 1, f"the attempt is COUNTED: {result}")
        self.assertEqual(result["verdict_after"], "BREACH", result)

    def _mutant(self, route: str, mutations: list[tuple[str, str]]) -> dict:
        root = copy_package([("host/attribution.py", old, new) for old, new in mutations])
        self.addCleanup(shutil.rmtree, root, True)
        result = run_harness("unverified_to_clean", root, route)
        self.assertEqual(result["verdict_before"], "UNVERIFIED", result)
        return result

    def _check_clean_again(self, result: dict) -> None:
        self.assertEqual((result["outcome"], result["real_frames"], result["instrument_tampered"]), ("ACCEPTED", 1, 0), result)
        self.assertEqual(result["verdict_after"], "CLEAN", f"the mutant must reproduce the verifier's claim: {result}")

    def test_through_the_registry_it_is_refused(self) -> None:
        self._check_refused("registry")

    def test_through_the_registry_without_both_checks_it_reads_clean(self) -> None:
        """MUTANT: the registry's AND the store's caller checks reverted (the fix of this note, whole):
        UNVERIFIED becomes CLEAN, exactly as the verifier read from the round-2 code."""
        self._check_clean_again(self._mutant("registry", [(REGISTRY_CHECK, REGISTRY_OFF), (STORE_CHECK, STORE_OFF)]))

    def test_through_the_registry_each_layer_alone_still_refuses(self) -> None:
        """Each layer on its own stops THIS route: with only the registry check reverted the store
        refuses the call, and with only the store check reverted the registry refuses it. (The
        registry check alone is what stops the `_State` routes: `CounterAttackTests`.)"""
        for label, mutation in (("registry check reverted", (REGISTRY_CHECK, REGISTRY_OFF)), ("store check reverted", (STORE_CHECK, STORE_OFF))):
            with self.subTest(label):
                result = self._mutant("registry", [mutation])
                self.assertTrue(result["outcome"].startswith("refused (PermissionError)"), result)
                self.assertEqual((result["real_frames"], result["verdict_after"]), (0, "BREACH"), result)

    def test_through_a_handed_out_store_it_is_refused(self) -> None:
        self._check_refused("store")

    def test_through_a_handed_out_store_without_its_check_it_reads_clean(self) -> None:
        """MUTANT: the store's own caller check reverted (the registry check alone cannot see a store
        that was handed out by another route)."""
        self._check_clean_again(self._mutant("store", [(STORE_CHECK, STORE_OFF)]))


class FrameFenceTests(unittest.TestCase):
    """Round 3, the verifier's first note: the interrupt-watch race, deterministic at unit level."""

    def test_the_finish_waits_for_a_frame_in_flight_and_fences_the_next(self) -> None:
        code, output, result, partial = run_harness_raw("finish_fence", REPO)
        self.assertIsNotNone(result, f"exit {code}:\n{output[-4000:]}")
        self.assertTrue(result["frame_1_in_flight_at_check"], f"NON-VACUITY: the frame was in flight at the check: {result}")
        self.assertFalse(result["finish_completed_while_frame_in_flight"], f"the finish must wait for the frame in flight: {result}")
        self.assertTrue(result["finish_completed_after_release"], result)
        self.assertEqual(result["order"], ["frame-start", "frame-end", "finish-done"], result)
        self.assertTrue(result["frame_in_flight_recorded"], f"the verdict records the wait: {result}")
        self.assertFalse(result["frame_2_ran"], f"a frame on another thread after the finish must not run: {result}")
        self.assertTrue(result["frame_2_still_waiting"], result)
        self.assertEqual(result["ran_after_finish"], 0, f"a late frame is not a false BREACH: {result}")
        self.assertIn("waits for the process to end instead of running", output, "the fence says so, once")

    def test_without_the_fence_the_race_is_back(self) -> None:
        """MUTANT: the fence reverted (no thread is fenced out; the finish does not wait for a frame in
        flight). The same harness must see the finish complete while a frame runs, and the late frame
        run after the verdict: the tripwire ends the process as `ran-after-finish` (the verifier's mutant)."""
        root = copy_package([("host/attribution.py", FENCE_CHECK, FENCE_OFF), ("host/attribution.py", FENCE_WAIT, FENCE_WAIT_OFF)])
        self.addCleanup(shutil.rmtree, root, True)
        code, output, result, partial = run_harness_raw("finish_fence", root)
        self.assertIsNotNone(partial, output[-4000:])
        self.assertTrue(partial["finish_completed_while_frame_in_flight"], f"the mutant's finish does not wait: {partial}")
        self.assertEqual(partial["order"], ["frame-start", "finish-done", "frame-end"], partial)
        self.assertIsNone(result, f"the mutant's late frame must end the process before the final line: {result}")
        self.assertEqual(code, 6, output[-4000:])
        self.assertIn("[AI-EXIT] reason=ran-after-finish code=6", output)


class GuardedObjectTests(unittest.TestCase):
    """Round 2 (c): the lifecycle, the session, the isolation and the guard listener are guarded."""

    def test_writes_from_outside_are_refused_and_counted(self) -> None:
        result = run_harness("guarded_attacks", REPO)
        for label, outcome in result["outcomes"].items():
            with self.subTest(label):
                self.assertTrue(outcome.startswith("refused") and outcome.endswith("counted=True"), f"{label}: {outcome}")
        for label, ok in result["controls"].items():
            with self.subTest(label):
                self.assertTrue(ok, f"CONTROL failed: {label}: {result}")
        self.assertGreaterEqual(result["instrument_tampered"], len(result["outcomes"]), result)

    def test_without_the_owner_check_the_writes_get_through(self) -> None:
        """MUTANT: the owner-file check reverted. The same writes must then be ACCEPTED and uncounted,
        which is what the verifier measured on the step-0.1 lifecycle."""
        root = copy_package([("host/attribution.py", GUARD_CHECK, GUARD_OFF)])
        self.addCleanup(shutil.rmtree, root, True)
        result = run_harness("guarded_attacks", root)
        for label in ("lifecycle._verdict_path = None", "session.frame_cap = 10**12", "isolation._exit = 'forged'", "guard._on_frame = print"):
            with self.subTest(label):
                self.assertEqual(result["outcomes"][label], "ACCEPTED; counted=False", result)


class ControllerTogetherTests(unittest.TestCase):
    """(R1 + R2, build spec 2026-10-29 D12 (b): USER RULING 52) The REAL controller (`host/controller.py`) refuses START or
    SELECT held together with any other button, so no reset or erase combination can be pressed (the soft reset
    A+B+START+SELECT, the title's B+SELECT combinations). It runs here with a FAKE framework (`modules.context`, whose
    emulator records the buttons down) and a fake instrument's `seal_module`, loaded under a private name, so the test
    needs no emulator; the controller's own code is the file's."""

    def load(self):
        import importlib.util
        import types
        from unittest import mock

        down: set[str] = set()
        emulator = types.SimpleNamespace(press_button=lambda button: None, hold_button=down.add,
                                         release_button=down.discard)
        context_module = types.ModuleType("modules.context")
        context_module.context = types.SimpleNamespace(emulator=emulator)
        instrument = types.ModuleType("ai_player.host.attribution")
        instrument.seal_module = lambda name: None
        fakes = {"modules": types.ModuleType("modules"), "modules.context": context_module,
                 "ai_player.host.attribution": instrument}
        with mock.patch.dict(sys.modules, fakes):
            spec = importlib.util.spec_from_file_location("controller_under_test", REPO / "ai_player" / "host" / "controller.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return module, down

    @staticmethod
    def drive(generator, frames: int) -> None:
        for _ in range(frames):
            next(generator)

    def test_start_or_select_never_with_another_button(self) -> None:
        module, down = self.load()
        controller = module.Controller()
        # FAULT: A held, then a tap of START (the soft reset's start); B held, then SELECT (the title's erase combinations)
        for held, other in (("A", "Start"), ("B", "Select"), ("Start", "A"), ("Select", "B")):
            with self.subTest(held=held, other=other):
                holding = controller.hold(held, 30)
                self.drive(holding, 2)
                with self.assertRaises(module.ControllerError):
                    self.drive(controller.tap(other), 1)
                with self.assertRaises(module.ControllerError):
                    self.drive(controller.hold(other, 5), 1)
                holding.close()
                self.assertEqual(down, set())  # the held button was released
                self.assertEqual(controller.held, set())
        # CONTROL: B held with a direction (running) is allowed; one button after another is allowed; START alone is
        holding = controller.hold("B", 30)
        self.drive(holding, 2)
        self.drive(controller.tap("Up"), 2)
        holding.close()
        for button in ("Start", "A", "Select", "B"):
            self.drive(controller.tap(button), 2)
        self.drive(controller.hold("Start", 3), 3)
        self.assertEqual(controller.held, set())


def _harness_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True, choices=sorted(HARNESSES))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--extra", default="")
    args = parser.parse_args()
    result = HARNESSES[args.harness](args.root, args.extra)
    print(RESULT_TAG + json.dumps(result, default=str), flush=True)
    sys.stdout.flush()
    os._exit(0)  # the debug harness armed the instrument's exit watchdog; nothing else to wait for


if __name__ == "__main__":
    if "--harness" in sys.argv:
        _harness_main()
    unittest.main(verbosity=2)
