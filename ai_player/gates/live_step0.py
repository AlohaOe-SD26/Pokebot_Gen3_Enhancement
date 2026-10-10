"""LIVE PROOF of AI-player build steps 0 and 0.1 (purity scaffolding): every arm through the real code.

    py -3.12 ai_player/gates/live_step0.py [--arms A,P,B,...]

Each arm runs the real framework headless with the real hook under a wall clock, grades the run,
prints PASS/FAIL with the evidence lines, and writes the whole transcript to
`ai_player/evidence/<date>-step01-<ARM>.txt`. Exit 0 only if every arm passed. Most arms go through
`py -3.12 -m ai_player run ...` (the real launcher and the purity gate it runs first); the DIRECT arms
(H2, IB, IC, IH, G and their mutants) start `pokebot.py` themselves, because what they test is what
happens when the launcher is NOT in the way (a person's own start, a console Ctrl+C, a debug start).

WHAT A RUN IS GRADED FROM: the instrument's VERDICT FILE (`<run_dir>/purity.json`, written by
`host/attribution.py` from its own counters, and only when `lifecycle.finish` asks). Printed lines
are evidence for people, and each arm checks that the printed `[AI-PURITY]` line agrees with the file,
but no grade rests on a line the AI's own code could have printed (arm XE prints a forged one). The
driver picks the run directory itself (`--run-dir`), so it never reads a path the child printed.
Launcher lines are trusted only when printed BEFORE the child started (the first `[AI-GATE]` line).
The `[AI-HOOK]` lines are printed by the hook, which the AI's isolation code does not control.

FOUR KINDS OF FAULT ARM
* SWITCH arms set an `AI_PLAYER_FAULT_*` variable that the AI's own code reads (`options.py`), so
  the fault runs the production path.
* PLANT arms (X*, RL*) copy the package to a temporary folder, add a `_plant.py` that does one
  forbidden thing from inside the AI's play loop (`tick(step, session)` is called once per brain step
  by `host/session.py` `_steps`), and run THAT copy through the real launcher with `--allow-ungated`
  (the launcher gates the copy and, rightly, refuses it otherwise: arm XR proves that). Each plant
  arm grades BOTH halves on the same plant where both apply: the static gate must FAIL the copy with
  the predicted rule in `_plant.py`, and the live audit must catch the action. The real package is
  only read.
* RUNTIME-ONLY plants (XE, XY, XZ) attack the EVIDENCE rather than the game, with code the static gate
  has no rule against by design (printing a line, replacing the session's lifecycle). Their guard is
  the verdict file and the launcher's check of it; the static result is recorded, not graded.
* MUTANT arms (M*) REVERT ONE FIX in a temporary copy (a text mutation of one file, applied exactly
  once) and run a fixed arm's scenario on it. They PASS only when that arm's own grade FAILS on the
  mutant: the proof that the arm would catch the fix being reverted (the review's rule: "each fix
  needs an arm or test that FAILS when the fix is reverted").

PRE-REGISTERED PREDICTIONS (written before the graded runs; the grade code below encodes them)
-----------------------------------------------------------------------------------------------
Step 0 (2026-10-07, all 27 graded PASS on the step-0 code; re-run on the step-0.1 code, same predictions
unless noted):
A   normal, fresh New Game, 3000 frames. PREDICT exit 0, `reason=step0-placeholder`, every breach
    counter 0 (incl. ai_bot_calls, isolation_lost), ai_presses=0, real_frames>=3000, verdict CLEAN;
    gate PASS on the real package before launch; the verdict file names the real package.
P   CONTROL (`AI_PLAYER_CONTROL_TAP=1`), fresh: PREDICT ai_presses=50 EXACTLY, ai_unrouted_presses=0,
    unattributed_inputs=0, CLEAN. WHY: without it, the zeros in A could be counters that never count.
B   FAULT keep-listeners on `oldale.ss1` (a WILD battle on Route 101): PREDICT foreign_presses>0 from
    framework code, `purity-breach` code 6, battle over afterwards; ai_bot_calls=0.
A2  the SAME fixture, no fault. PREDICT exit 0, CLEAN, and the battle STILL waiting afterwards.
    STEP 0.1 (finding 2): AND the state inspected afterwards is THIS run's: md5 differs from the seed's
    and its frame counter is >= the seed's + 3000 (the seed's is read by the same inspector). CONTROL:
    the same check run on (seed, seed) must FAIL, so it is not true by construction.
C   FAULT the brain raises: PREDICT exit 2 by itself, `crash`, a traceback naming the fault, a verdict file.
D   listener restoration, fresh: PREDICT (from the verdict file) the same 14 listeners at entry and
    exit, only the GuardListener while playing. STEP 0.1 (finding 9): "same list object" in the
    isolation report compares a saved reference with itself, so D is now graded on the HOOK's own
    record: `[AI-HOOK] listeners before the AI starts: n=14 ...` and, at process exit,
    `same_list_object=True members_unchanged=True` with the same 14 types.
W   FAULT keep-listeners + the cheats plugin's infinite_money, on `route103.ss1`: PREDICT
    foreign_writes>0 from modules/game_cheats.py and money afterwards 900000.
W2  the same cheats file, no fault: PREDICT CLEAN and money afterwards 3000; STEP 0.1: the after-state
    is this run's (as A2), with the same CONTROL.
M   FAULT a listener raises; main.py switches to Manual: PREDICT `parked-manual` code 3.
T   SOFT wall clock (frames=10,000,000, wall 25 s): PREDICT `wall-clock` code 124, not killed, CLEAN.
T2  HARD wall clock (FAULT the brain hangs, wall 25 s): PREDICT exit 124, killed, survivors=[],
    `NO PURITY VERDICT`, NO verdict file and no `[AI-PURITY]` line.
XO  PLANT CONTROL (does nothing): PREDICT static PASS and live CLEAN, exit 0.
XP  PLANT `_pressed_inputs |= A` every 8 steps, oldale.ss1, 9000 frames: static [d]; unattributed_inputs>0,
    BREACH, exit 6; battle OVER afterwards.
XH  PLANT `_held_inputs ^= A` every 8 steps: static [d]; unattributed_inputs>0.
XM  PLANT an ffi memmove of money=900000 into WRAM, route103.ss1: static [d];
    unattributed_state_changes>0, money afterwards 900000.
XL  PLANT a rewind through the core's Python `load_state`: static [b]; ai_loads>0.
XN  PLANT the same rewind through the NATIVE `lib.mCoreLoadStateNamed`: static [d]; ai_loads=0 but
    unattributed_state_changes>0.
XS  PLANT `emulator.load_save_game(...)`: static [b]; ai_loads>0.
XF  PLANT an extra `emulator._core.run_frame()`: static [b]; extra_frames>0.
XT  PLANT a callback appended to the core's keys_read list: static [d]; instrument_tampered>0.
XB  PLANT the second verifier's VB, verbatim: the bot's PATHFINDER reached through
    `dataclasses.inspect.getmembers(dataclasses.sys)` and CALLED from the brain, route103.ss1.
    static [a]; live ai_bot_calls>0 naming modules/map_path.py, BREACH, exit 6.
XG  PLANT the second verifier's VP, verbatim: a press of A found by a frame walk + match class
    patterns, oldale.ss1. static [a]; live ai_unrouted_presses>0.
XK  PLANT: one unrouted press (a breach), then attempts to hide it. Step 0 had five; STEP 0.1
    (finding 3) adds eight: look up `counters._values`, `counters._add(count=-1)`, the counter store's
    own `add(-1)` reached through the instrument's registry, assign `attribution._counters`,
    `_installed = False`, `_snapshot = None`, rebind the instrument module's `BREACH_COUNTERS`, and
    rewrite it in the module's namespace dict (`vars(module)[...]`). PREDICT static FAIL; twelve
    attempts REFUSED, the namespace rewrite accepted by Python but DETECTED by the module fingerprint;
    every one of the thirteen named by its own tamper origin; the verdict file still BREACH with
    unattributed_inputs>0 and instrument_tampered>=13; exit 6.
XE  RUNTIME-ONLY PLANT: replace `session.lifecycle` with a fake that prints a forged CLEAN verdict and
    exits 0. PREDICT the child exits 0, NO verdict file, and the launcher exits 8.
XY  RUNTIME-ONLY PLANT: print the same forged lines and `raise SystemExit(0)`. PREDICT `stray-exit` code 2,
    WITH a verdict file.
XZ  RUNTIME-ONLY PLANT: call the REAL `give_up`, CATCH its SystemExit and keep playing. PREDICT the
    file is rewritten BREACH with `ran_after_finish>=1`, `ran-after-finish` code 6, the first ending kept.
XR  the XP plant WITHOUT `--allow-ungated`: PREDICT the launcher's gate FAILS the copy and the launcher
    exits 7 without starting the framework.

Step 0.1 (2026-10-07, the adversarial review of step 0; predicted cold before the first graded run):
RL  (finding 1) PLANT on oldale.ss1: at step 20 register a FOREIGN plugin (code compiled under a
    file name outside the package) whose listener pushes a pressing handler on its very FIRST frame;
    at step 30 save the state; at step 300 load it back (a rewind: the frame counter goes backwards,
    so `main.py` rebuilds its listeners). PREDICT static FAIL [b]; live: the AI's rebuild door was
    asked (`rebuilds_served>=1` in the isolation exit line), the foreign listener was never built (no
    `[PLANT] a FRESH foreign listener ran` line), foreign_presses=0, isolation_lost=0, ai_loads>=1 so
    `purity-breach` code 6, ended by itself, the wild battle still waiting afterwards.
RLX (finding 1) the RL plant + FAULT `AI_PLAYER_FAULT_NO_REBIND=1`: PREDICT the fresh foreign
    listener runs ONCE and pushes its handler, foreign_presses>=1 (that one frame), isolation_lost>=1,
    `reason=isolation-lost code=6`, ended by itself (not killed), a verdict file. Never a silent starve.
M1  MUTANT: RLX with the instrument's per-frame guard check removed. PREDICT grade_RLX FAILS (the AI
    starves silently under the foreign handler until the hard wall clock kills it, with no verdict).
BT  (finding 9) FAULT keep-listeners on `ai_player/gates/fixtures/trainer_battle_r116.ss1` (a TRAINER
    battle waiting at its first decision; built by `make_trainer_fixture.py` from `evostall.ss1`).
    PREDICT the seed inspects as BATTLE with the trainer flag; foreign_presses>0; a press chain names
    `BattleListener.fight` (the listener that runs `DefaultBattleStrategy` for every trainer battle);
    ai_bot_calls=0; `purity-breach` code 6; the after-state is this run's.
    ‼ PREDICTION MISS (first graded run, 2026-10-07 13:09): every prediction held EXCEPT the ending:
    `reason=frame-budget code=4`, not `purity-breach` 6. The trainer battle kept the bot's handler on
    top of the AI for longer than `--frames` + 600, so the guard ended the STARVED run itself (the
    design working: a starve is never silent). Wild battle B ended sooner, which is why B's
    prediction held. AMENDED after that run, graded from the second run on: verdict BREACH and either
    `purity-breach` 6 or `frame-budget` 4, never killed; with `frame-budget`, the guard's own line must
    show the AI advanced fewer steps than `--frames`.
BT2 the same fixture, no fault: PREDICT CLEAN exit 0; afterwards the trainer battle is STILL waiting
    (in_battle, trainer flag); after-state md5 differs, frame counter >= seed + 3000.
DX  (finding 9) FAULT `AI_PLAYER_FAULT_SKIP_RESTORE=1`, fresh: PREDICT the hook's exit line says
    `same_list_object=False` with only the GuardListener: D's hook check is not true by construction.
M3  MUTANT: XK with the instance attribute guard, the counter store's "counts only grow" check and the
    module guard disabled. PREDICT grade_XK FAILS (attacks ACCEPTED).
XC  (finding 5) PLANT `context.emulator._core.rtc.advance_time(1 h)` at step 100, fresh: static [b]
    (`advance_time`); live ai_writes>=1 with an origin naming `advance_time`, BREACH, exit 6.
XQ  (finding 5) PLANT the same clock change NATIVELY (`core._core.rtc.value += 1 h`, no Python door):
    static [d]; live unattributed_state_changes>=1 with an origin naming the game clock (RTC).
M5r MUTANT: XQ with the instrument's clock comparison removed. PREDICT grade_XQ FAILS.
XV  (finding 5) PLANT `context.emulator._prev_pressed_inputs = 0x3FF` once at step 100, fresh: static
    [d]; live unattributed_inputs>=1 with an origin naming `_prev_pressed_inputs`.
M5p MUTANT: XV with the instrument's `_prev_pressed_inputs` watch removed. PREDICT grade_XV FAILS.
H   (finding 5) an ai_player-owned profile whose http.yml says `enable: true` (port 18899), via the
    launcher: PREDICT the run header says `[AI-RUN] http_server=off (forced`, the child's `[AI-START]`
    says `http_server=off`, CLEAN exit 0, and http.yml afterwards says `enable: false`.
H2  (finding 5) the same profile state, the framework started DIRECTLY (no launcher to fix it): PREDICT
    `[AI-START] ... http_server=on`, `[AI-START] REFUSED`, `reason=refused-http-server code=9`, a verdict
    file (UNVERIFIED: no frame ran), no `[AI-ISOLATION]` line.
    (Added before the first H2 run, from reading `modules/web/http.py` `start_http_server`: its
    thread is NOT a daemon, so the refused process would sit in interpreter shutdown for ever; it
    must still exit 9 by itself, through the lifecycle's exit watchdog. M5w measures the claim.)
M5h MUTANT: H2 with the session's HTTP refusal removed. PREDICT grade_H2 FAILS (the run proceeds).
M5w MUTANT: H2 with the lifecycle's exit watchdog not armed. PREDICT grade_H2 FAILS: the verdict file
    is written, but the process never exits (the driver's clock kills it), i.e. a parked process.
IB  (finding 7) the framework started DIRECTLY in a hidden console of its own, sent CTRL_BREAK 3 s
    after the AI isolated: PREDICT `reason=interrupted code=130` by itself, a verdict file (CLEAN),
    the line `[AI-LIFECYCLE] interrupted by signal 21`.
IC  (finding 7) the same with CTRL_C to the console: PREDICT the same with signal 2.
M7  MUTANT: IB with the session's interrupt handlers not installed. PREDICT grade_IB FAILS (Windows
    terminates the process on Ctrl+Break: no verdict file).
Every plant arm that breaches must exit 6 by itself (never killed) with `reason=purity-breach`.

Step 0.1, ROUND 2 (2026-10-07, the verifier's report on the step-0.1 fixes; predicted cold before the
first graded run of these arms). Changed arms:
XK  now also attacks the objects that decide how a run ENDS, which a verifier found writable unseen:
    `lifecycle._verdict_path = None`, `lifecycle._attribution`, `lifecycle._finishing = True`,
    `session.lifecycle`, `session.frame_cap = 10**12`, `isolation._exit = 'forged'`,
    `guard._on_frame`. PREDICT each REFUSED and named by its own tamper origin; instrument_tampered
    >= 20; the rest as before.
M3  now also reverts the owner-file instance guard those objects use. PREDICT grade_XK FAILS.
XE  `Session` is now guarded, so the plain `session.lifecycle = fake` is refused and counted (XK). XE
    now swaps the lifecycle with `object.__setattr__`, the documented residual (refused statically,
    rule d), so the forged ending still reaches the LAUNCHER's verdict-file check, which is what XE
    tests. PREDICT unchanged: child exit 0, no verdict file, launcher exit 8.
New arms:
RLF (finding 1, the loader the review suggested) PLANT on oldale.ss1: the same foreign plugin as RL at
    step 20 and a save at step 30, but at step 300 the plant only QUEUES a FOREIGN callback (code
    compiled outside the package) on `modules.main.work_queue`, the channel the HTTP server uses; the
    framework's main loop runs it between frames, and it loads the step-30 state (a rewind, so main.py
    rebuilds its listeners). PREDICT static FAIL [a]; live: foreign_loads>=1 with an origin naming
    `foreign_rewinder_plugin.py`, ai_loads=0, rebuilds_served>=1, the foreign listener never built,
    foreign_presses=0, isolation_lost=0; the AI was NOT starved: the brain gave up with its own reason
    (`the brain's own reason was 'step0-placeholder', but the purity verdict is BREACH`), so the ending
    is `purity-breach` 6 (the foreign load is the breach, correctly), not killed; the wild battle still
    waiting afterwards.
M1r MUTANT of RLF: the rebuild door reverted (`ListenerIsolation(rebind=False)` in the session). PREDICT
    grade_RLF FAILS: the fresh foreign listener runs, isolation_lost>=1, `isolation-lost` code 6.
G   (finding 6, LIVE) the framework started DIRECTLY through a test-side `-c` wrapper that sets
    `context.debug = True` right before main.py's main loop (headless forces it off; a GUI started
    with `--debug` has it on), with FAULT_MANUAL armed. PREDICT the child prints `[AI-START] ...
    debug=True`, `[AI-START] REFUSED`, `reason=refused-debug-mode code=9`, process exit 9 by itself,
    a verdict file (UNVERIFIED: no frame ran), no `[AI-ISOLATION] active`.
M6  MUTANT of G: the session's debug check reverted. PREDICT grade_G FAILS. Expected mechanism (from
    reading `modules/main.py` 158-166 and `modules/context.py` `debug_stepping_mode`): the run starts
    in debug mode, the planted listener raises at frame 30, main.py's debug branch calls
    `debug_stepping_mode()`, which fails headless (no `_emulator_screen`), and main.py's outer handler
    ends the process with exit 1 and NO verdict file (in a GUI it would park in stepping mode).
XW  (the verifier's V5, verbatim: the same-thread look-ahead) PLANT on oldale.ss1: at step 100 enter
    `context.emulator.peek_frame()` and never leave it; then press A through no door every 8 steps.
    PREDICT static FAIL [b]; live: real_frames >= 3000 (every main-loop frame audited although a
    look-ahead is open on the main thread), a tamper origin naming the open look-ahead,
    unattributed_inputs>0, BREACH, `purity-breach` 6, not killed; the battle OVER afterwards (the
    presses reached the game).
M8  MUTANT of XW: step 0.1's classification order (the look-ahead depth checked before the main loop).
    PREDICT grade_XW FAILS (real_frames about 100); AND the second layer, the frame-continuity check,
    still makes the verdict BREACH with a tamper origin naming main-loop frames run without a sink audit.
M8c the M8 mutation PLUS the continuity check removed: the verifier's V5 reproduced. PREDICT verdict
    CLEAN, `step0-placeholder` exit 0, real_frames < 1500, and the battle OVER afterwards (unseen
    presses won it). Read with M8: each of the two layers alone turns this attack into a BREACH.
XWT (finding 8, CROSS-thread, LIVE) PLANT, fresh: at step 100 a worker thread enters `peek_frame(0)` (no
    frame; the main thread waits for it, so the emulator is never used by two threads at once) and holds
    it open for the rest of the run; at step 110 the MAIN thread runs one extra `core.run_frame()`.
    PREDICT static FAIL [b]; live extra_frames>=1 with an origin naming `_plant.py`, BREACH, exit 6: the
    worker's look-ahead does not make the main thread's frame a look-ahead.
M8t MUTANT of XWT: step 0's look-ahead depth shared by every thread. PREDICT grade_XWT FAILS (the extra
    frame is skipped as a look-ahead, extra_frames=0; the memory sink may still see its effects).
IH  (the verifier's V4) the framework DIRECTLY in its own console with FAULT_HANG; CTRL_BREAK 3 s after
    the AI isolated (the brain is already hung). PREDICT `[AI-LIFECYCLE] interrupted by signal 21, but
    no frame reached the guard`, `reason=interrupted-unresponsive code=130`, a verdict file (CLEAN),
    the instrument's line that the run was finished off the main thread, the child exiting by itself
    within 16 s of the signal (1 s for the handler + 10 s grace + margin).
M7h MUTANT of IH: the interrupt watch not started. PREDICT grade_IH FAILS (the hung child is killed by
    the helper's bound, no verdict file).
M7x MUTANT of IH: the exit watchdog waits 20 s even off the main thread. PREDICT grade_IH FAILS (the
    process outlives its verdict by about 20 s; the instrument's line says it waited).
Finding 4 (the hook APPENDS) and the per-thread look-ahead depth (finding 8) also have unit proofs in
`test_host.py`, each with a REAL revert of the fix as its mutant half.

Step 0.1, ROUND 3 (2026-10-07, the verifier's two notes on round 2; predicted cold, before the first
graded run of these arms). The two fixes: (1) the instrument's FRAME FENCE (`host/attribution.py`):
while one thread runs `lifecycle.finish`, a frame on any other thread waits for the process to end
instead of running, and the finish waits for a frame already in flight; the interrupt watch's line
says what it MEASURED (frames that ran / reached the guard since the signal), never "stuck" by
assumption. (2) The instrument's REGISTRY and counter stores answer only the instrument's own file.
Changed arms:
XK  five more attacks, all through the registry: `payload_of(counters).add(+5)` (the verifier's
    route), `vaults()[0].add(+5)`, `payload_of(attribution).local.depth = 1` (switches the doors'
    counting off), a poisoned `brain_cache`, `sealed()[0][1].clear()`; the old store `add(-1)` is now
    refused at the registry. PREDICT every one REFUSED and named by its own tamper origin (the
    registry's line naming the plant function); instrument_tampered >= 25; the rest as before.
M3  also reverts the registry's and the stores' caller checks. PREDICT grade_XK FAILS.
IH  unchanged predictions; the watch's line now reads `no frame reached the guard within 10s: no
    frame ran at all since the watch saw the signal`.
New arms (all DIRECT, in a console of the framework's own, Ctrl+Break 3 s after the AI isolated; each
runs a COPY with a test-side plant whose static result is recorded, not graded: the plant only
OBSERVES and slows the console; it touches neither the game nor the instrument). The plant: (a) from
step 1, while `lifecycle.finishing` is True every stdout line takes 20 ms (a slow console: it widens
the finish's window, so the race below is met every run instead of by luck; lines stay whole); (b) an
OBSERVER thread, independent of the instrument, reads the EMULATOR's own frame counter from the moment
the finish begins and prints `[PLANT-OBSERVER] a frame RAN after the finish began ... (n frames)` on
every change.
IG  (the verifier's VIB, as a FAULT) the guard IGNORES the interrupt flag (a text mutation of the
    session), so the main thread keeps running frames and only the watch can end the run. PREDICT
    `[AI-LIFECYCLE] interrupted by signal 21, and the main thread is NOT stuck: K frames ran and J
    reached the guard` with K, J > 0 and no "stuck" claim; the fence line `the run is being finished
    on thread 'ai-player-interrupt-watch': a real frame on thread 'MainThread' ... waits for the
    process to end`; the observer sees at most ONE frame after the finish began (the one already in
    flight); `reason=interrupted-unresponsive code=130` with a verdict file, CLEAN, ran_after_finish=0,
    `finish.thread` = the watch; the child exits by itself within 20 s of the signal.
M9  MUTANT of IG: the frame fence reverted (no thread fenced out; the finish does not wait for a frame
    in flight). PREDICT grade_IG FAILS: frames keep running during the finish (the observer sees
    many), and a frame after the verdict trips `ran-after-finish` code 6 (the verifier's observation).
M9w MUTANT of IG: the watch's measured wording reverted to step 0.1's line. PREDICT grade_IG FAILS on
    the wording: the line claims `the main thread is stuck after N frames` while frames ran.
IR  (the real-code race the verifier described) no mutation; at step 30 the brain BLOCKS the main
    thread (a long call) until `lifecycle.finishing` is True, then returns at once, so the main loop's
    next step is a frame while the watch is finishing. PREDICT the watch's line `no frame ran at all
    since the watch saw the signal`; `[PLANT] woke`; the fence line for 'MainThread'; the observer sees
    NO frame after the finish began; `interrupted-unresponsive` 130, a verdict file, CLEAN,
    ran_after_finish=0, `finish.thread` = the watch; exit by itself within 20 s of the signal.
M9r MUTANT of IR: the frame fence reverted. PREDICT grade_IR FAILS: the woken main thread's frame RUNS
    during the finish (the observer sees it; if it lands after the verdict, also `ran-after-finish` 6).
The registry note and the fence also have unit proofs in `test_host.py` (`UnverifiedToCleanTests`,
`FrameFenceTests`), each with its mutant half.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.host import launcher  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_CONTROL_TAP,
    ENV_FAULT_HANG,
    ENV_FAULT_KEEP_LISTENERS,
    ENV_FAULT_MANUAL,
    ENV_FAULT_NO_REBIND,
    ENV_FAULT_RAISE,
    ENV_FAULT_SKIP_RESTORE,
    ENV_PACKAGE_ROOT,
)

SAVES = REPO / "tools" / "story-dev" / "saves"
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step01"
GATE = Path(__file__).with_name("check_purity.py")
INSPECT = Path(__file__).with_name("inspect_state.py")
CONSOLE_SIGNAL = Path(__file__).with_name("console_signal.py")
#: (path, md5) PINNED here: "same name, different bytes" has voided results in this project before
#: (`tools/story-dev/saves/FIXTURES.md5`). The driver refuses to run on different bytes.
FIXTURES: dict[str, tuple[Path, str]] = {
    "oldale.ss1": (SAVES / "oldale.ss1", "df2d885f29e8aaefbacd2cb2d854c93a"),
    "route103.ss1": (SAVES / "route103.ss1", "0d951fe21be35a6eafade207ddff5961"),
    "trainer_battle_r116.ss1": (Path(__file__).resolve().parent / "fixtures" / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba"),
}
BATTLE_FIXTURE = "oldale.ss1"
OVERWORLD_FIXTURE = "route103.ss1"
TRAINER_FIXTURE = "trainer_battle_r116.ss1"
CHEATS_FILE = "game_cheats.yml"
MONEY_TARGET = 900_000  # modules/game_cheats.py MONEY_TARGET
FIXTURE_MONEY = 3000
OUTER_GRACE_SECONDS = 90  # the driver's own clock around the launcher's clock
HTTP_ON_CONFIG = "# Written by ai_player/gates/live_step0.py (arms H / H2): the HTTP server ON.\nhttp_server:\n  enable: true\n  ip: 127.0.0.1\n  port: 18899\n"

KV_RE = re.compile(r"(\w+)=(\S+)")
EXIT_RE = re.compile(r"\[AI-EXIT\] reason=(\S+) code=(-?\d+)")
CHILD_RE = re.compile(r"\[AI-RUN\] child exit code=(-?\d+) elapsed=([\d.]+)s killed=(\w+)")
TYPES_RE = re.compile(r"n=(\d+) types=\[([^\]]*)\]")
SINK_COUNTERS = ("extra_frames", "unattributed_inputs", "unattributed_state_changes", "instrument_tampered",
                 "instrument_errors", "isolation_lost")
FORGED_PURITY = (
    "[AI-PURITY] foreign_presses=0 foreign_writes=0 foreign_loads=0 ai_presses=0 ai_writes=0 ai_loads=0 "
    "ai_bot_calls=0 ai_unrouted_presses=0 extra_frames=0 unattributed_inputs=0 unattributed_state_changes=0 "
    "instrument_tampered=0 instrument_errors=0 real_frames=3000 peek_restores=0 verdict=CLEAN"
)
FORGED_EXIT = "[AI-EXIT] reason=step0-placeholder code=0"

# ---------------------------------------------------------------------- the plants
_PLANT_HEADER = '"""PLANTED by ai_player/gates/live_step0.py into a TEMPORARY COPY of the package. Never in the real one."""\n'


@dataclass(frozen=True)
class Plant:
    source: str
    counter: str | None  # the verdict-file counter that must be > 0 (None: graded by the arm itself)
    rule: str | None  # the static rule that must fire in _plant.py (None: no static expectation)
    runtime_only: bool = False  # the attack is on the evidence; the static result is recorded, not graded


PLANTS: dict[str, Plant] = {
    "XO": Plant(
        """
        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            return None
        """,
        None,
        None,
    ),
    "XP": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step % 8 == 0:
                context.emulator._pressed_inputs |= 1  # press A through no door
        """,
        "unattributed_inputs",
        "d",
    ),
    "XH": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step % 8 == 0:
                context.emulator._held_inputs ^= 1  # hold / let go of A through no door
        """,
        "unattributed_inputs",
        "d",
    ),
    "XM": Plant(
        """
        from mgba import ffi
        from modules.context import context
        from modules.memory import get_encryption_key, read_symbol, unpack_uint32

        __all__ = ["tick"]
        MONEY = 900_000
        MONEY_OFFSET = 0x490  # Emerald, gSaveBlock1


        def tick(step: int, session=None) -> None:
            if step == 100:
                pointer = unpack_uint32(read_symbol("gSaveBlock1Ptr"))
                data = (MONEY ^ get_encryption_key()).to_bytes(4, "little")
                wram = context.emulator._core._native.memory.wram
                ffi.memmove(ffi.cast("char*", wram) + ((pointer + MONEY_OFFSET) & 0x3FFFF), data, 4)
        """,
        "unattributed_state_changes",
        "d",
    ),
    "XL": Plant(
        """
        import mgba.vfs
        from modules.context import context

        __all__ = ["tick"]
        SAVED = []


        def tick(step: int, session=None) -> None:
            if step == 30:
                SAVED.append(context.emulator.get_save_state())
            if step == 300 and SAVED:
                vfile = mgba.vfs.VFile.fromEmpty()
                vfile.write(SAVED[0], len(SAVED[0]))
                vfile.seek(0, whence=0)
                context.emulator._core.load_state(vfile)  # a rewind through the core's Python door
        """,
        "ai_loads",
        "b",
    ),
    "XN": Plant(
        """
        import mgba.vfs
        from mgba import lib
        from modules.context import context

        __all__ = ["tick"]
        SAVED = []


        def tick(step: int, session=None) -> None:
            if step == 30:
                SAVED.append(context.emulator.get_save_state())
            if step == 300 and SAVED:
                vfile = mgba.vfs.VFile.fromEmpty()
                vfile.write(SAVED[0], len(SAVED[0]))
                vfile.seek(0, whence=0)
                core = context.emulator._core
                lib.mCoreLoadStateNamed(core._core, vfile.handle, 0)  # the same rewind, natively
                SAVED.append(vfile)  # keep the file alive
        """,
        "unattributed_state_changes",
        "d",
    ),
    "XS": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                emulator = context.emulator
                emulator.load_save_game(emulator.read_save_data())
        """,
        "ai_loads",
        "b",
    ),
    "XF": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                context.emulator._core.run_frame()  # one frame the main loop never asked for
        """,
        "extra_frames",
        "b",
    ),
    "XT": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 50:
                core = context.emulator._core
                core._callbacks.keys_read.append(lambda: core.set_keys(raw=1))  # runs INSIDE frames
        """,
        "instrument_tampered",
        "d",
    ),
    # The second verifier's VB plant (verifier_live_plants.py), verbatim except for the signature.
    "XB": Plant(
        """
        import dataclasses

        __all__ = ["tick"]
        DONE = []


        def tick(step: int, session=None) -> None:
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
        """,
        "ai_bot_calls",
        "a",
    ),
    # The second verifier's VP plant, verbatim except for the signature.
    "XG": Plant(
        """
        from sys import _getframe as gf

        __all__ = ["tick"]
        COUNT = []


        def tick(step: int, session=None) -> None:
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
        """,
        "ai_unrouted_presses",
        "a",
    ),
    "XK": Plant(
        """
        import ai_player.host.attribution as instrument_module
        from modules.context import context

        __all__ = ["tick"]


        def _attempt(label, action) -> None:
            try:
                action()
            except Exception as error:
                print(f"[PLANT] {label}: refused ({type(error).__name__}: {error})", flush=True)
                return
            print(f"[PLANT] {label}: ACCEPTED", flush=True)


        def _zero(counters) -> None:
            counters.unattributed_inputs = 0


        def _patch_class(counters) -> None:
            type(counters).breach = lambda self: False


        def _shadow(attribution) -> None:
            attribution.finalize_audit = lambda: attribution.counters


        def _finalize(attribution) -> None:
            # Returning normally means ACCEPTED; the instrument refuses by counting it, not by raising.
            before = attribution.counters.instrument_tampered
            attribution.finalize_audit()
            if attribution.counters.instrument_tampered > before:
                raise PermissionError("the instrument counted it as tampering and kept its wrappers on")


        def _write(attribution) -> None:
            line = attribution.write_verdict_file(None, {"exit_reason": "forged"})
            if "REFUSED" in line:
                raise PermissionError(line)


        def _values(counters) -> None:
            counters._values["unattributed_inputs"] = 0


        def _store_subtract(counters) -> None:
            instrument_module._REGISTRY.payload_of(counters).add("unattributed_inputs", None, None, -1)


        def _store_inflate(counters) -> None:
            # Round 3, the verifier's route: a POSITIVE count passed "counts only grow".
            instrument_module._REGISTRY.payload_of(counters).add("real_frames", None, None, 5)


        def _vault_inflate() -> None:
            instrument_module._REGISTRY.vaults()[0].add("real_frames", None, None, 5)


        def _depth_switch(attribution) -> None:
            instrument_module._REGISTRY.payload_of(attribution).local.depth = 1


        def _cache_poison(attribution) -> None:
            instrument_module._REGISTRY.payload_of(attribution).brain_cache.update({"map_path.py": False})


        def _fingerprints_clear() -> None:
            instrument_module._REGISTRY.sealed()[0][1].clear()


        def _assign(owner, name, value) -> None:
            setattr(owner, name, value)


        def _namespace(module) -> None:
            vars(module)["BREACH_COUNTERS"] = ()


        def tick(step: int, session=None) -> None:
            if step == 30:
                context.emulator._pressed_inputs |= 1  # one press through no door: a real breach
            if step == 60:
                attribution = session.attribution
                counters = attribution.counters
                _attempt("zero the unattributed_inputs counter", lambda: _zero(counters))
                _attempt("patch the counters' class through type()", lambda: _patch_class(counters))
                _attempt("shadow finalize_audit on the instance", lambda: _shadow(attribution))
                _attempt("call finalize_audit from the brain", lambda: _finalize(attribution))
                _attempt("call write_verdict_file from the brain", lambda: _write(attribution))
                _attempt("zero the store through counters._values", lambda: _values(counters))
                _attempt("subtract through counters._add(count=-1)", lambda: counters._add("unattributed_inputs", count=-1))
                _attempt("subtract through the counter store's own add(-1)", lambda: _store_subtract(counters))
                _attempt("replace attribution._counters", lambda: _assign(attribution, "_counters", None))
                _attempt("switch the audit off with attribution._installed = False", lambda: _assign(attribution, "_installed", False))
                _attempt("clear the memory baseline with attribution._snapshot = None", lambda: _assign(attribution, "_snapshot", None))
                _attempt("rebind the instrument module's BREACH_COUNTERS", lambda: _assign(instrument_module, "BREACH_COUNTERS", ()))
                _attempt("rewrite BREACH_COUNTERS in the module's namespace dict", lambda: _namespace(instrument_module))
                # Round 2: the objects that decide how the run ENDS. (Values that would wreck the run if
                # accepted are the objects' own, so a mutant that accepts them still ends.)
                lifecycle = session.lifecycle
                _attempt("suppress the verdict file with lifecycle._verdict_path = None", lambda: _assign(lifecycle, "_verdict_path", None))
                _attempt("hand finish another instrument with lifecycle._attribution", lambda: _assign(lifecycle, "_attribution", attribution))
                _attempt("mark the lifecycle finishing with lifecycle._finishing = True", lambda: _assign(lifecycle, "_finishing", True))
                _attempt("replace session.lifecycle", lambda: _assign(session, "lifecycle", lifecycle))
                _attempt("lift the frame budget with session.frame_cap", lambda: _assign(session, "frame_cap", 10 ** 12))
                _attempt("forge the isolation's exit report with isolation._exit", lambda: _assign(session.isolation, "_exit", "forged"))
                _attempt("silence the guard with guard._on_frame", lambda: _assign(session.guard, "_on_frame", session.guard._on_frame))
                # Round 3: the instrument's registry (a module attribute anyone can name).
                _attempt("inflate real_frames through the registry (payload_of(counters).add(+5))", lambda: _store_inflate(counters))
                _attempt("inflate real_frames through the registry's vault list", _vault_inflate)
                _attempt("switch the doors' counting off with the per-thread depth", lambda: _depth_switch(attribution))
                _attempt("hide bot code by poisoning the bot-code cache", lambda: _cache_poison(attribution))
                _attempt("clear the sealed modules' fingerprints", _fingerprints_clear)
        """,
        "unattributed_inputs",
        "d",
    ),
    "XE": Plant(
        f"""
        __all__ = ["tick"]
        FORGED_PURITY = {FORGED_PURITY!r}
        FORGED_EXIT = {FORGED_EXIT!r}


        class _FakeLifecycle:
            finishing = True
            abandoned = False

            def finish(self, reason, code):
                print(FORGED_PURITY, flush=True)
                print(FORGED_EXIT, flush=True)
                raise SystemExit(0)

            def give_up(self, reason, code=0):
                self.finish(reason, code)


        def tick(step: int, session=None) -> None:
            if step == 100:
                # `session.lifecycle = ...` is refused and counted now (arm XK); object.__setattr__ is the
                # documented residual, so the forgery still reaches the LAUNCHER's check, which XE tests.
                object.__setattr__(session, "lifecycle", _FakeLifecycle())
                session.lifecycle.give_up("step0-placeholder", 0)
        """,
        None,
        None,
        runtime_only=True,
    ),
    "XY": Plant(
        f"""
        __all__ = ["tick"]
        FORGED_PURITY = {FORGED_PURITY!r}
        FORGED_EXIT = {FORGED_EXIT!r}


        def tick(step: int, session=None) -> None:
            if step == 100:
                print(FORGED_PURITY, flush=True)
                print(FORGED_EXIT, flush=True)
                raise SystemExit(0)
        """,
        None,
        None,
        runtime_only=True,
    ),
    "XZ": Plant(
        """
        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                try:
                    session.lifecycle.give_up("step0-placeholder", 0)
                except SystemExit:
                    print("[PLANT] caught the lifecycle's SystemExit after its CLEAN verdict; playing on", flush=True)
        """,
        None,
        None,
        runtime_only=True,
    ),
    # Step 0.1, finding 1: a rewind makes main.py rebuild its listeners. The foreign listener exists
    # ONLY in a rebuild (it comes from a plugin registered at step 20); its code is compiled under a
    # file name outside the package, so the instrument sees it as the framework's.
    "RL": Plant(
        '''
        import modules.plugins as framework_plugins
        from modules.context import context

        __all__ = ["tick"]
        SAVED = []
        FOREIGN_SOURCE = """
        from modules.context import context
        from modules.plugin_interface import BotPlugin


        def _starve():
            for _ in range(10_000_000):
                context.emulator.press_button("A")
                yield


        class StarvingListener:
            def __init__(self):
                self.pushed = False

            def handle_frame(self, bot_mode, frame):
                if not self.pushed:
                    self.pushed = True
                    print("[PLANT] a FRESH foreign listener ran and pushed a pressing handler on top of the AI", flush=True)
                    context.controller_stack.append(_starve())


        class StarvingPlugin(BotPlugin):
            def get_additional_bot_listeners(self):
                return [StarvingListener()]
        """
        FOREIGN = {}
        # A plain relative file name: it resolves under the framework's folder, never under ai_player/.
        exec(compile(textwrap_dedent(FOREIGN_SOURCE), "foreign_listener_plugin.py", "exec"), FOREIGN)


        def tick(step: int, session=None) -> None:
            if step == 20:
                framework_plugins.plugins.append(FOREIGN["StarvingPlugin"]())
                print("[PLANT] registered a foreign plugin; only a listener REBUILD would construct its listener", flush=True)
            if step == 30:
                SAVED.append(context.emulator.get_save_state())
            if step == 300 and SAVED:
                print("[PLANT] rewinding 270 frames: the frame counter goes backwards, so main.py rebuilds its listeners", flush=True)
                context.emulator.load_save_state(SAVED[0])
        ''',
        "ai_loads",
        "b",
    ),
    # Step 0.1, finding 5: the game clock, through its Python door and natively.
    "XC": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                context.emulator._core.rtc.advance_time(60 * 60 * 1000)  # the debug menu's "Advance RTC"
        """,
        "ai_writes",
        "b",
    ),
    "XQ": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                clock = context.emulator._core._core.rtc  # the native setting, under every Python door
                clock.value = clock.value + 60 * 60 * 1000
        """,
        "unattributed_state_changes",
        "d",
    ),
    "XV": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]


        def tick(step: int, session=None) -> None:
            if step == 100:
                context.emulator._prev_pressed_inputs = 0x3FF  # decides what the next press does
        """,
        "unattributed_inputs",
        "d",
    ),
    # Round 2: the verifier's V5 plant (verify_live.py "VPK"), verbatim except for the rule it predicts.
    "XW": Plant(
        """
        from modules.context import context

        __all__ = ["tick"]
        HELD = []


        def tick(step: int, session=None) -> None:
            if step == 100:
                manager = context.emulator.peek_frame()
                manager.__enter__()  # entered and never exited: the main thread's look-ahead depth stays 1
                HELD.append(manager)
                print("[PLANT] entered peek_frame and never left it", flush=True)
            if step > 100 and step % 8 == 0:
                context.emulator._pressed_inputs |= 1  # A, through no door (the XP press)
                if step == 104:
                    print("[PLANT] pressing A through no door while the look-ahead is held open", flush=True)
        """,
        "unattributed_inputs",
        "b",
    ),
    # Round 2, finding 8 cross-thread, live: another thread's open look-ahead must not hide the main
    # thread's extra frame. The main thread WAITS while the worker enters, so the emulator is never used
    # by two threads at once, and the look-ahead is never left (no restore on another thread mid-run).
    "XWT": Plant(
        """
        import threading

        from modules.context import context

        __all__ = ["tick"]
        HELD = []


        def _hold(entered, release) -> None:
            with context.emulator.peek_frame(0):  # zero frames: it only takes a save state
                entered.set()
                release.wait(600)  # never set: the look-ahead stays open in THIS thread for the rest of the run


        def tick(step: int, session=None) -> None:
            if step == 100:
                entered, release = threading.Event(), threading.Event()
                worker = threading.Thread(target=_hold, args=(entered, release), daemon=True)
                worker.start()
                entered.wait(30)
                HELD.append((worker, release))
                print(f"[PLANT] a worker thread entered peek_frame and holds it open (entered={entered.is_set()})", flush=True)
            if step == 110:
                context.emulator._core.run_frame()  # an extra frame on the MAIN thread, the worker's look-ahead open
                print("[PLANT] ran one extra frame on the main thread", flush=True)
        """,
        "extra_frames",
        "b",
    ),
    # Round 2, finding 1 with a FOREIGN loader (the review's suggestion): the plant only queues a
    # callback on main.py's work_queue (the HTTP server's channel); the framework's main loop runs it
    # between frames, so the rewind is the framework's, not the AI's.
    "RLF": Plant(
        '''
        import modules.main as framework_main
        import modules.plugins as framework_plugins
        from modules.context import context

        __all__ = ["tick"]
        SAVED = []
        FOREIGN_SOURCE = """
        from modules.context import context
        from modules.plugin_interface import BotPlugin


        def _starve():
            for _ in range(10_000_000):
                context.emulator.press_button("A")
                yield


        class StarvingListener:
            def __init__(self):
                self.pushed = False

            def handle_frame(self, bot_mode, frame):
                if not self.pushed:
                    self.pushed = True
                    print("[PLANT] a FRESH foreign listener ran and pushed a pressing handler on top of the AI", flush=True)
                    context.controller_stack.append(_starve())


        class StarvingPlugin(BotPlugin):
            def get_additional_bot_listeners(self):
                return [StarvingListener()]


        def make_rewinder(state):
            def rewind():
                print("[PLANT] the FOREIGN rewinder runs from main.py's work_queue, between frames", flush=True)
                context.emulator.load_save_state(state)
            return rewind
        """
        FOREIGN = {}
        # A plain relative file name: it resolves under the framework's folder, never under ai_player/.
        exec(compile(textwrap_dedent(FOREIGN_SOURCE), "foreign_rewinder_plugin.py", "exec"), FOREIGN)


        def tick(step: int, session=None) -> None:
            if step == 20:
                framework_plugins.plugins.append(FOREIGN["StarvingPlugin"]())
                print("[PLANT] registered a foreign plugin; only a listener REBUILD would construct its listener", flush=True)
            if step == 30:
                SAVED.append(context.emulator.get_save_state())
            if step == 300 and SAVED:
                print("[PLANT] queued a FOREIGN rewind of 270 frames on main.py's work_queue", flush=True)
                framework_main.work_queue.put(FOREIGN["make_rewinder"](SAVED[0]))
        ''',
        "foreign_loads",
        "a",
    ),
}
# Round 3: the interrupt-watch race. A TEST-SIDE plant that only OBSERVES and slows the console: it
# touches neither the game nor the instrument (its static result is recorded, not graded).
_RACE_PLANT = '''
import sys
import threading
import time

from modules.context import context

__all__ = ["tick"]
BLOCK_UNTIL_FINISHING = {block}
SLOW_LINE_SECONDS = 0.02
OBSERVE_SECONDS = 120.0
OBSERVE_POLL_SECONDS = 0.0005
REAL_OUT = sys.stdout
CONSOLE_LOCK = threading.Lock()


def _say(text) -> None:
    with CONSOLE_LOCK:
        REAL_OUT.write(text + "\\n")
        REAL_OUT.flush()


class _SlowConsole:
    """While the run is being finished, every stdout LINE takes 20 ms (a slow console, e.g. a full
    pipe): the finish's window gets wide enough that a main thread waking up during it meets it every
    run. Lines are buffered per thread and written whole, so two threads never interleave a line."""

    def __init__(self, real, lifecycle) -> None:
        self._real = real
        self._lifecycle = lifecycle
        self._local = threading.local()

    def write(self, text):
        pending = getattr(self._local, "pending", "") + text
        if "\\n" not in pending:
            self._local.pending = pending
            return len(text)
        head, _, tail = pending.rpartition("\\n")
        self._local.pending = tail
        if self._lifecycle.finishing:
            time.sleep(SLOW_LINE_SECONDS)
        with CONSOLE_LOCK:
            self._real.write(head + "\\n")
            self._real.flush()
        return len(text)

    def flush(self):
        pending = getattr(self._local, "pending", "")
        if pending:
            self._local.pending = ""
            with CONSOLE_LOCK:
                self._real.write(pending)
        return self._real.flush()

    def __getattr__(self, name):
        return getattr(self._real, name)


def _observe(lifecycle) -> None:
    """Independent of the instrument: the EMULATOR's own frame counter, from the moment the finish began."""
    for _ in range(int(OBSERVE_SECONDS / OBSERVE_POLL_SECONDS)):
        if lifecycle.finishing:
            break
        time.sleep(OBSERVE_POLL_SECONDS)
    else:
        return
    start = context.emulator.get_frame_count()
    _say(f"[PLANT-OBSERVER] the finish began on another thread at emulator frame {{start}}")
    last = start
    for _ in range(int(OBSERVE_SECONDS / OBSERVE_POLL_SECONDS)):
        now = context.emulator.get_frame_count()
        if now != last:
            _say(f"[PLANT-OBSERVER] a frame RAN after the finish began: emulator frame {{start}} -> {{now}} ({{now - start}} frames)")
            last = now
        time.sleep(OBSERVE_POLL_SECONDS)


def tick(step: int, session=None) -> None:
    if step == 1:
        sys.stdout = _SlowConsole(sys.stdout, session.lifecycle)
        threading.Thread(target=_observe, args=(session.lifecycle,), name="plant-observer", daemon=True).start()
        _say("[PLANT] slow console installed; the observer watches the emulator's frame counter")
    if BLOCK_UNTIL_FINISHING and step == 30:
        _say("[PLANT] the brain blocks the main thread until the run is being finished from another thread (a long call)")
        for _ in range(int(OBSERVE_SECONDS / 0.001)):
            if session.lifecycle.finishing:
                break
            time.sleep(0.001)
        _say(f"[PLANT] woke: the finish began on another thread; back to the main loop, whose next step is a frame "
             f"(emulator frame {{context.emulator.get_frame_count()}})")
'''
PLANTS["IG"] = Plant(_RACE_PLANT.format(block="False"), None, None, runtime_only=True)
PLANTS["IR"] = Plant(_RACE_PLANT.format(block="True"), None, None, runtime_only=True)
PLANTS["XR"] = PLANTS["XP"]
#: The plants are injected into `host/session.py` `_steps`, the AI's per-frame step driver.
PLANT_HOST_FILE = "host/session.py"
_IMPORT_ANCHOR = "from ai_player.runlog import RunLog\n"
_LOOP_ANCHOR = "                note = self.isolation.enforce()\n"


def plant_source(plant: str) -> str:
    entry = PLANTS[plant]
    # A tuple is the older `(source, counter, rule)` form that external verifier scripts register.
    source = entry.source if isinstance(entry, Plant) else entry[0]
    text = textwrap.dedent(source).lstrip("\n")
    if "textwrap_dedent(" in text:  # the RL plant's foreign source is itself indented
        text = "from textwrap import dedent as textwrap_dedent\n" + text
    return _PLANT_HEADER + text


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"mutation/plant anchor not unique in {path.name} ({count} hits): {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def make_copy(plant: str | None, mutations: tuple[tuple[str, str, str], ...]) -> Path:
    """Copy the real package to a temporary root; add `_plant.py` and call its `tick` from the AI's
    per-step driver; apply each MUTATION (file relative to ai_player/, old text, new text) exactly once."""
    root = Path(tempfile.mkdtemp(prefix=f"ai_player_plant_{plant or 'mutant'}_"))
    package = root / "ai_player"
    shutil.copytree(REPO / "ai_player", package, ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures"))
    if plant is not None:
        source = plant_source(plant)
        (package / "_plant.py").write_text(source, encoding="utf-8")
        host_file = package / PLANT_HOST_FILE
        one_argument = re.search(r"def tick\(\s*step\s*(:\s*int\s*)?\)", source) is not None  # an older plant
        call = "_plant_tick(step)" if one_argument else "_plant_tick(step, self)"
        _replace_once(host_file, _IMPORT_ANCHOR, _IMPORT_ANCHOR + "from ai_player._plant import tick as _plant_tick\n")
        _replace_once(host_file, _LOOP_ANCHOR, f"                {call}\n" + _LOOP_ANCHOR)
    for relative, old, new in mutations:
        _replace_once(package / relative, old, new)
    return root


# ---------------------------------------------------------------------- mutations (each reverts one fix)
_M8_ORDER = (
    "host/attribution.py",
    "        if main_loop:\n            return \"real\"\n        if getattr(s.local, \"peek\", 0) > 0:\n            return \"look-ahead\"\n",
    "        if getattr(s.local, \"peek\", 0) > 0:  # MUTANT M8: step 0.1's order\n            return \"look-ahead\"\n"
    "        if main_loop:\n            return \"real\"\n",
)
# Round 3.
_REGISTRY_CHECK_OFF = (
    "host/attribution.py",
    "        if caller.f_code.co_filename != own_file:\n            problem = f\"the instrument's registry",
    "        if False:  # MUTANT M3: the registry's caller check\n            problem = f\"the instrument's registry",
)
_STORE_CHECK_OFF = (
    "host/attribution.py",
    "        if caller.f_code.co_filename != own_file:\n            values[\"instrument_tampered\"] += 1\n",
    "        if False:  # MUTANT M3: the stores' caller check\n            values[\"instrument_tampered\"] += 1\n",
)
#: FAULT (arm IG and its mutants): the guard ignores the interrupt flag, as the verifier's VIB did.
_GUARD_SILENT = (
    "host/session.py",
    "        if self.interrupted is not None:\n            self.log.line(f\"[AI-LIFECYCLE] interrupted by signal {self.interrupted} (Ctrl+C",
    "        if False:  # FAULT IG: the guard ignores the interrupt flag\n            self.log.line(f\"[AI-LIFECYCLE] interrupted by signal {self.interrupted} (Ctrl+C",
)
#: The frame fence reverted: no thread is fenced out, and the finish does not wait for a frame in flight.
_FENCE_OFF = (
    ("host/attribution.py", "        return finisher is not None and finisher != threading.get_ident()\n",
     "        return False  # MUTANT M9: the frame fence reverted\n"),
    ("host/attribution.py", "        held = self._fence_frames()\n", "        held = False  # MUTANT M9: no wait for a frame in flight\n"),
)
MUTATIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    # finding 1: the instrument's per-frame "is the AI's guard still in the live list?" check
    "M1": (("host/attribution.py", "            lost = self._guard_missing()\n", "            lost = False  # MUTANT M1\n"),),
    # finding 3 (and round 2's lifecycle/session/isolation/guard): the owner-file instance guard, the
    # store's "counts only grow" check, the module guard
    "M3": (
        ("host/attribution.py",
         "        caller = sys._getframe(1)\n        if caller.f_code.co_filename != _REGISTRY.owner_of(type(self)):\n            _tamper_all(f\"{type(self).__name__}.{name} was assigned from {_where(caller)}\")",
         "        caller = sys._getframe(1)\n        if False:  # MUTANT M3\n            _tamper_all(f\"{type(self).__name__}.{name} was assigned from {_where(caller)}\")"),
        ("host/attribution.py", "        if type(count) is not int or count < 1:\n", "        if False:  # MUTANT M3\n"),
        ("host/attribution.py",
         "    def __setattr__(self, name: str, value: object) -> None:\n        _tamper_all(f\"the module attribute {self.__name__}.{name} was assigned from {_where(sys._getframe(1))}\")\n        raise AttributeError(f\"the module {self.__name__} is sealed: {name!r} cannot be rebound\")",
         "    def __setattr__(self, name: str, value: object) -> None:\n        ModuleType.__setattr__(self, name, value)  # MUTANT M3"),
        # round 3: the registry's and the counter stores' caller checks
        _REGISTRY_CHECK_OFF,
        _STORE_CHECK_OFF,
    ),
    # finding 5: the clock comparison
    "M5r": (("host/attribution.py", "        if clock != s.rtc:\n", "        if False:  # MUTANT M5r\n"),),
    # finding 5: the `_prev_pressed_inputs` watch
    "M5p": (("host/attribution.py", "            if prev != s.expected_prev:\n", "            if False:  # MUTANT M5p\n"),),
    # finding 5: the session's refusal to start with the HTTP server on
    "M5h": (("host/session.py", "        if http_on:\n            self.log.line(\n", "        if False:  # MUTANT M5h\n            self.log.line(\n"),),
    # finding 7: the interrupt handlers (and with them the interrupt watch, which needs a handler)
    "M7": (("host/session.py", "        if self._install_interrupt_handlers():\n", "        if False:  # MUTANT M7\n"),),
    # found by H2: the exit watchdog (a non-daemon framework thread holds a finished process open)
    "M5w": (("host/lifecycle.py", "        self._attribution.arm_exit_watchdog(code)\n", "        pass  # MUTANT M5w\n"),),
    # ---- round 2 ----
    # finding 1: the rebuild door itself (isolation never takes modules.main.get_bot_listeners)
    "M1r": (("host/session.py", "            rebind=not options.fault_no_rebind,\n", "            rebind=False,  # MUTANT M1r\n"),),
    # finding 6: the session's refusal to start in debug mode
    "M6": (("host/session.py", "        if debug:\n", "        if False:  # MUTANT M6\n"),),
    # the verifier's V4: the interrupt watch that ends a run whose main thread is stuck
    "M7h": (("host/session.py", "            self.watch.start()\n", "            pass  # MUTANT M7h\n"),),
    # the verifier's V4: off the main thread the exit watchdog must not wait (sys.exit ends only that thread)
    "M7x": (("host/attribution.py", "        delay = EXIT_WATCHDOG_SECONDS if on_main_thread else 0.0\n",
             "        delay = EXIT_WATCHDOG_SECONDS  # MUTANT M7x\n"),),
    # the verifier's V5 (same-thread finding 8): step 0.1's order, the look-ahead depth before the main loop
    "M8": (_M8_ORDER,),
    # ...and the second layer, the frame-continuity check, removed as well: V5 reproduced
    "M8c": (_M8_ORDER, ("host/attribution.py", "        if gap > 0:\n", "        if False:  # MUTANT M8c\n")),
    # finding 8, cross-thread: step 0's look-ahead depth, ONE counter shared by every thread
    "M8t": (
        ("host/attribution.py", "_MISSING = object()\n", "_MISSING = object()\n_SHARED_PEEK = type('Shared', (), {})()  # MUTANT M8t\n"),
        ("host/attribution.py", "        local = _REGISTRY.payload_of(self).local\n\n        @contextlib.contextmanager",
         "        local = _SHARED_PEEK  # MUTANT M8t\n\n        @contextlib.contextmanager"),
        ("host/attribution.py", "        if getattr(s.local, \"peek\", 0) > 0:\n            return \"look-ahead\"\n",
         "        if getattr(_SHARED_PEEK, \"peek\", 0) > 0:  # MUTANT M8t\n            return \"look-ahead\"\n"),
    ),
    # ---- round 3 ----
    # FAULT, not a revert: the guard ignores the interrupt flag (the verifier's VIB), graded by grade_IG
    "IG": (_GUARD_SILENT,),
    # the frame fence reverted, on IG's scenario and on IR's
    "M9": (_GUARD_SILENT, *_FENCE_OFF),
    "M9r": _FENCE_OFF,
    # the watch's measured wording reverted to step 0.1's unmeasured "stuck" claim
    "M9w": (
        _GUARD_SILENT,
        ("host/session.py", "        progress = self._progress_since(guard_frames_at_flag, real_frames_at_flag)\n",
         "        progress = f\"but no frame reached the guard within {INTERRUPT_GRACE_SECONDS:g}s (the main thread is stuck "
         "after {self.frames_seen} frames)\"  # MUTANT M9w: step 0.1's unmeasured claim\n"),
    ),
}
#: Checks about WHICH package ran and whether the static gate passed. A mutant copy fails these by
#: construction (it is not the real package, and a changed instrument is not the pinned one), so they
#: never count as "the arm caught the reverted fix".
PROVENANCE_PREFIXES = (
    "the launcher gated the real package", "the verdict file names the package", "the session says the gated package",
    "the driver's own gate run", "static gate", "static finding", "the launcher's own gate", "and launched only because",
)


# ---------------------------------------------------------------------- arms and runs
@dataclass
class Arm:
    name: str
    title: str
    profile: str
    seed: str  # "fresh" or a FIXTURES key
    env: dict[str, str] = field(default_factory=dict)
    frames: int = 3000
    wall: float = 240.0
    cheats: bool = False
    inspect: bool = False
    plant: str | None = None
    allow_ungated: bool = True  # plant arms only; XR turns it off on purpose
    direct: str | None = None  # "http" | "break" | "c": start pokebot.py without the launcher
    http_on: bool = False  # write the profile's http.yml with the server ON before the run
    mutant_of: str | None = None  # MUTANT arm: the arm whose grade must FAIL on the mutated copy
    after_advance: int | None = None  # the after-state's minimum frame advance over the seed (default: frames)


@dataclass
class Run:
    arm: Arm
    command: list[str]
    exit_code: int
    elapsed: float
    stdout: str
    run_dir: Path
    verdict: dict | None = None
    ai_log: str = ""
    inspect: dict | None = None
    inspect_raw: str = ""
    seed_inspect: dict | None = None
    gate_exit: int | None = None
    gate_output: str = ""
    http_after: str = ""
    mutations_applied: list[str] = field(default_factory=list)
    checks: list[tuple[bool, str]] = field(default_factory=list)

    def lines(self, tag: str) -> list[str]:
        return [line for line in self.stdout.splitlines() if line.startswith(tag)]

    def last(self, tag: str) -> str:
        found = self.lines(tag)
        return found[-1] if found else ""

    def first(self, tag: str) -> str:
        found = self.lines(tag)
        return found[0] if found else ""

    def purity(self) -> dict[str, str]:
        """The counters and verdict FROM THE VERDICT FILE (strings, like a parsed line)."""
        if not self.verdict:
            return {}
        values = {key: str(value) for key, value in (self.verdict.get("counters") or {}).items()}
        values["verdict"] = str(self.verdict.get("verdict"))
        return values

    def facts(self) -> dict:
        return (self.verdict or {}).get("facts") or {}

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)


def _int(value: str | None) -> int:
    try:
        return int(value) if value is not None else -1
    except ValueError:
        return -1


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def clean_env(extra: dict[str, str]) -> dict[str, str]:
    """The shell's environment MINUS every AI_PLAYER_* variable, PLUS the arm's own switches, so a
    variable left in the shell can never turn a fault on in both arms of an A/B."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    env.update(extra)
    return env


def prepare_profile(arm: Arm, build_root: Path) -> Path:
    profile_dir, _ = launcher.ensure_profile(build_root, arm.profile)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {arm.profile} is not ai_player-owned; refusing to touch it")
    cheats = profile_dir / CHEATS_FILE
    if arm.cheats:
        cheats.write_text(
            "# Written by ai_player/gates/live_step0.py for the W / W2 arms (design draft §10.2 fault test).\n"
            "toggles:\n  infinite_money: true\n",
            encoding="utf-8",
        )
    elif cheats.exists():
        cheats.unlink()
    if arm.http_on:
        (profile_dir / "http.yml").write_text(HTTP_ON_CONFIG, encoding="utf-8")
    else:
        launcher.force_http_off(profile_dir)
    return profile_dir


def inspect_state(profile: str, state: Path | None = None) -> tuple[dict | None, str]:
    command = [sys.executable, str(INSPECT), "--profile", profile] + (["--state", str(state)] if state else [])
    probe = subprocess.run(command, cwd=str(REPO), env=clean_env({}), capture_output=True, timeout=180)
    raw = probe.stdout.decode("utf-8", errors="replace") + probe.stderr.decode("utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith("INSPECT "):
            return json.loads(line[len("INSPECT "):]), raw
    return None, raw


def debug_wrapper(build_root: Path) -> str:
    """Arms G / M6: run the REAL `pokebot.py` (headless, real main loop, real hook) with the framework's
    debug flag ON. Headless mode forces `context.debug = False` (`modules/gui/headless.py`), so the
    wrapper re-sets it right before main.py's main loop starts, which is the state a GUI started with
    `--debug` is in. Passed with `-c`, so no frame of the wrapper is under `ai_player/` (the
    instrument would otherwise count every action as the AI's)."""
    pokebot = str(build_root / "pokebot.py")
    return textwrap.dedent(
        f"""
        import runpy
        import sys

        import modules.gui.headless as headless
        from modules.context import context

        sys.argv[0] = {pokebot!r}
        _run = headless.PokebotHeadless.run


        def _run_in_debug_mode(self, settings):
            loop = self._main_loop

            def debug_main_loop():
                context.debug = True
                print("[DEBUG-WRAPPER] context.debug = True (as in a framework started with --debug)", flush=True)
                loop()

            self._main_loop = debug_main_loop
            return _run(self, settings)


        headless.PokebotHeadless.run = _run_in_debug_mode
        runpy.run_path({pokebot!r}, run_name="__main__")
        """
    )


def _hidden_console() -> tuple[int, object | None]:
    """A NEW console for the signal helper, with its window hidden (no window pops up)."""
    if os.name != "nt":
        return 0, None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 0  # SW_HIDE
    return subprocess.CREATE_NEW_CONSOLE, info


def run_arm(arm: Arm, build_root: Path) -> Run:
    profile_dir = prepare_profile(arm, build_root)
    seed_inspect = None
    if arm.inspect and arm.seed != "fresh":
        seed_inspect, _ = inspect_state(arm.profile, FIXTURES[arm.seed][0])
    mutations = MUTATIONS.get(arm.name, ())
    copy_root = make_copy(arm.plant, mutations) if (arm.plant or mutations) else None
    run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    try:
        gate_exit, gate_output = None, ""
        gated_package = (copy_root or REPO) / "ai_player"
        if copy_root is not None or arm.direct:
            gate = subprocess.run(
                [sys.executable, str(GATE), "--package", str(gated_package),
                 "--hook", str(launcher.hook_path(build_root)), "--build-root", str(build_root)],
                cwd=str(REPO), env=clean_env({}), capture_output=True, timeout=180,
            )
            gate_exit = gate.returncode
            gate_output = gate.stdout.decode("utf-8", errors="replace") + gate.stderr.decode("utf-8", errors="replace")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        startupinfo = None
        if arm.direct:
            seed = None if arm.seed == "fresh" else FIXTURES[arm.seed][0]
            launcher.seed_profile(profile_dir, seed, arm.seed == "fresh")
            run_dir.mkdir(parents=True, exist_ok=True)
            env = clean_env(arm.env)
            for key, value in launcher.child_env(arm.frames, run_dir, arm.wall).items():
                if key.startswith("AI_PLAYER_") or key in ("PYTHONUNBUFFERED", "COLUMNS"):
                    env[key] = value
            for key in launcher.UNTRUSTED_ENV:
                env.pop(key, None)
            if copy_root is not None:
                env[ENV_PACKAGE_ROOT] = str(copy_root)
            bot = launcher.bot_command(build_root, arm.profile)
            if arm.direct == "http":
                command = bot
            elif arm.direct == "debug":
                command = [sys.executable, "-c", debug_wrapper(build_root), *bot[2:]]
            else:
                command = [sys.executable, str(CONSOLE_SIGNAL), "--kind", arm.direct, "--wait", "[AI-ISOLATION] active",
                           "--delay", "3", "--timeout", f"{arm.wall:g}", "--", *bot]
                creationflags, startupinfo = _hidden_console()
            cwd = build_root
        else:
            command = [
                sys.executable, "-m", "ai_player", "run",
                "--profile", arm.profile, "--frames", str(arm.frames), "--wall-seconds", f"{arm.wall:g}",
                "--build-root", str(build_root), "--run-dir", str(run_dir),
            ]
            command += ["--fresh"] if arm.seed == "fresh" else ["--state", str(FIXTURES[arm.seed][0])]
            if copy_root is not None and arm.allow_ungated:
                command.append("--allow-ungated")
            env = clean_env(arm.env)
            cwd = copy_root or REPO
        start = time.monotonic()
        proc = subprocess.Popen(
            command, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=creationflags, startupinfo=startupinfo,
        )
        # A launcher run gets its own gate run on top; a direct run is bounded by its wall clock + 60 s.
        outer = arm.wall + (60 if arm.direct else OUTER_GRACE_SECONDS + 200)
        try:
            raw, _ = proc.communicate(timeout=outer)
        except subprocess.TimeoutExpired:
            launcher.kill_tree(proc)
            raw, _ = proc.communicate()
            raw = (raw or b"") + b"\n[DRIVER] the run overran the driver's own wall clock; process tree killed\n"
        run = Run(arm, command, proc.returncode if proc.returncode is not None else -9, time.monotonic() - start,
                  raw.decode("utf-8", errors="replace"), run_dir, gate_exit=gate_exit, gate_output=gate_output,
                  seed_inspect=seed_inspect)
        if copy_root is not None:
            for relative, _, new in mutations:
                applied = new in (copy_root / "ai_player" / relative).read_text(encoding="utf-8")
                run.mutations_applied.append(f"{relative}: {'APPLIED' if applied else 'NOT FOUND'}: {new.strip()[:90]}")
    finally:
        if copy_root is not None:
            shutil.rmtree(copy_root, ignore_errors=True)
    run.verdict = launcher.read_verdict(run_dir)
    log_path = run_dir / "ai_player.log"
    if log_path.is_file():
        run.ai_log = log_path.read_text(encoding="utf-8", errors="replace")
    if arm.inspect:
        run.inspect, run.inspect_raw = inspect_state(arm.profile)
    http_file = profile_dir / "http.yml"
    run.http_after = http_file.read_text(encoding="utf-8") if http_file.is_file() else "(none)"
    if arm.http_on:
        launcher.force_http_off(profile_dir)  # never leave a profile with the server on
    return run


# ---------------------------------------------------------------------- shared checks
def check_verdict_file(run: Run) -> None:
    """The instrument wrote this run's file, and the printed purity line (for people) agrees with it."""
    run.check(run.verdict is not None, f"verdict file written by the instrument: {run.run_dir / 'purity.json'}")
    if run.verdict is None:
        return
    printed = dict(KV_RE.findall(run.last("[AI-PURITY] ")))
    from_file = run.purity()
    differing = sorted(key for key, value in printed.items() if from_file.get(key) != value)
    run.check(bool(printed) and not differing, f"the printed [AI-PURITY] line agrees with the file (differing: {differing or 'none'})")


def check_gated(run: Run, verdict_file_expected: bool = True) -> None:
    """The launcher gated the REAL package before it started the framework, and that package ran.
    (A run killed by the hard wall clock has no verdict file; the session's own line stands in.)"""
    gate_line = run.first("[AI-GATE] exit=")
    run.check("verdict=PASS" in gate_line and gate_line.endswith(f"package={REPO / 'ai_player'}"),
              f"the launcher gated the real package before launch: {gate_line or 'MISSING'}")
    if verdict_file_expected:
        run.check(run.facts().get("package_root") == str(REPO), f"the verdict file names the package that ran: {run.facts().get('package_root')}")
    else:
        package_line = run.first("[AI-PACKAGE]")
        run.check(package_line == f"[AI-PACKAGE] matches_hook_root=True loaded_from={REPO}",
                  f"the session says the gated package loaded: {package_line or 'MISSING'}")


def check_direct_gated(run: Run) -> None:
    """A DIRECT arm has no launcher: the driver gated the real package itself, and that package ran."""
    run.check(run.gate_exit == 0, f"the driver's own gate run PASSED the real package (exit {run.gate_exit})")
    package_line = run.first("[AI-PACKAGE]")
    run.check(package_line == f"[AI-PACKAGE] matches_hook_root=True loaded_from={REPO}",
              f"the session says the gated package loaded: {package_line or 'MISSING'}")


def check_exit(run: Run, reason: str, code: int, process_code: int | None = None) -> None:
    facts = run.facts()
    want = code if process_code is None else process_code
    run.check(run.exit_code == want, f"exit code {want} (got {run.exit_code})")
    run.check(facts.get("exit_reason") == reason and facts.get("exit_code") == code,
              f"verdict file: exit_reason={facts.get('exit_reason')} exit_code={facts.get('exit_code')} (want {reason} / {code})")
    match = EXIT_RE.search(run.last("[AI-EXIT]"))
    run.check(bool(match) and match.group(1) == reason and int(match.group(2)) == code,
              f"printed exit line agrees: {run.last('[AI-EXIT]') or 'MISSING'}")


def check_clean_exit(run: Run, reason: str = "step0-placeholder") -> None:
    check_verdict_file(run)
    check_exit(run, reason, 0)


def check_zero_foreign(run: Run) -> None:
    p = run.purity()
    for key in ("foreign_presses", "foreign_writes", "foreign_loads", "ai_bot_calls"):
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0)")


def check_sinks_clean(run: Run, min_frames: int) -> None:
    p = run.purity()
    for key in SINK_COUNTERS:
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0)")
    run.check(_int(p.get("real_frames")) >= min_frames, f"real_frames={p.get('real_frames')} (want >= {min_frames}: the sink audit ran)")
    run.check(p.get("verdict") == "CLEAN", f"verdict={p.get('verdict')} (from the verdict file)")


def check_not_killed(run: Run) -> None:
    child = CHILD_RE.search(run.last("[AI-RUN] child exit code="))
    run.check(bool(child) and child.group(3) == "False", f"ended by itself, not by the wall clock: {run.last('[AI-RUN] child exit code=') or 'MISSING'}")


def check_breach_exit(run: Run) -> None:
    check_verdict_file(run)
    check_exit(run, "purity-breach", 6)
    run.check(run.purity().get("verdict") == "BREACH", f"verdict={run.purity().get('verdict')} (from the verdict file)")
    check_not_killed(run)


def origins(run: Run, kind: str) -> dict:
    return ((run.verdict or {}).get("origins") or {}).get(kind) or {}


def after_state_problems(seed: dict | None, after: dict | None, min_advance: int) -> list[str]:
    """Why the inspected after-state might NOT be the state this run left (empty = it is)."""
    if not seed or not after:
        return [f"missing inspection (seed={bool(seed)}, after={bool(after)})"]
    problems = []
    if after.get("md5") == seed.get("md5"):
        problems.append(f"the after-state has the SEED's bytes (md5 {after.get('md5')})")
    if not isinstance(after.get("frame_count"), int) or after["frame_count"] < seed.get("frame_count", 0) + min_advance:
        problems.append(f"frame counter {after.get('frame_count')} < seed {seed.get('frame_count')} + {min_advance}")
    return problems


def check_after_state(run: Run) -> None:
    """Finding 2: the state graded "afterwards" is the one THIS run left, not the untouched seed. And a
    CONTROL: the same check handed the seed twice must fail, so it is not true by construction."""
    advance = run.arm.after_advance if run.arm.after_advance is not None else run.arm.frames
    problems = after_state_problems(run.seed_inspect, run.inspect, advance)
    seed, after = run.seed_inspect or {}, run.inspect or {}
    run.check(not problems, f"the after-state is THIS run's: md5 {after.get('md5')} != seed {seed.get('md5')}, "
              f"frame_count {after.get('frame_count')} >= seed {seed.get('frame_count')} + {advance} "
              f"(problems: {problems or 'none'})")
    control = after_state_problems(run.seed_inspect, run.seed_inspect, advance)
    run.check(bool(control), f"CONTROL: the same check on (seed, seed) FAILS: {control or 'it PASSED, so it proves nothing'}")


def hook_lines(run: Run) -> tuple[str, str]:
    return run.first("[AI-HOOK] listeners before the AI starts:"), run.last("[AI-HOOK] listeners at process exit:")


# ---------------------------------------------------------------------- per-arm grades
def grade_A(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    run.check(_int(run.purity().get("ai_presses")) == 0, f"ai_presses={run.purity().get('ai_presses')} (want 0: the placeholder presses nothing)")
    check_sinks_clean(run, run.arm.frames)
    package_line = run.last("[AI-PACKAGE]")
    run.check("matches_hook_root=True" in package_line, f"the hook's root is where ai_player loaded from: {package_line or 'MISSING'}")


def grade_P(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    p = run.purity()
    run.check(_int(p.get("ai_presses")) == 50, f"ai_presses={p.get('ai_presses')} (predicted EXACTLY 50)")
    run.check(_int(p.get("ai_unrouted_presses")) == 0, f"ai_unrouted_presses={p.get('ai_unrouted_presses')} (want 0: every AI press went through the controller)")
    check_sinks_clean(run, run.arm.frames)


def grade_B(run: Run) -> None:
    check_gated(run)
    p = run.purity()
    run.check(_int(p.get("foreign_presses")) > 0, f"foreign_presses={p.get('foreign_presses')} (want >0: the bot's listeners pressed)")
    run.check(any("modules/" in origin for origin in origins(run, "presses")), f"origins name framework code: {origins(run, 'presses') or 'MISSING'}")
    run.check(_int(p.get("ai_bot_calls")) == 0, f"ai_bot_calls={p.get('ai_bot_calls')} (want 0: the framework ran its bot code, not the AI)")
    check_breach_exit(run)
    state = run.inspect or {}
    run.check(state.get("in_battle") is False, f"after the run the battle is OVER (the bot fought it): {state or run.inspect_raw[-300:]}")
    check_after_state(run)


def grade_A2(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    check_sinks_clean(run, run.arm.frames)
    state = run.inspect or {}
    run.check(
        state.get("in_battle") is True and state.get("map") == "ROUTE 101",
        f"NON-VACUITY: after the run the wild battle is STILL waiting on Route 101: {state or run.inspect_raw[-300:]}",
    )
    check_after_state(run)


def grade_C(run: Run) -> None:
    check_gated(run)
    check_verdict_file(run)
    check_exit(run, "crash", 2)
    run.check(any("AI_PLAYER_FAULT_RAISE" in line for line in run.lines("[AI-TRACEBACK]")), "traceback names the injected fault")
    check_not_killed(run)
    run.check(run.elapsed < run.arm.wall, f"finished in {run.elapsed:.1f}s, inside the {run.arm.wall:g}s wall clock")


def grade_D(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    isolation = run.facts().get("isolation") or {}
    entry, active, exit_ = isolation.get("entry", ""), isolation.get("active", ""), isolation.get("exit", "")
    e, x, a = TYPES_RE.search(entry), TYPES_RE.search(exit_), TYPES_RE.search(active)
    run.check(bool(e) and int(e.group(1)) > 1, f"entry had framework listeners to remove: {entry or 'MISSING'}")
    run.check(bool(a) and a.group(1) == "1" and a.group(2) == "GuardListener", f"while playing, only the AI's guard: {active or 'MISSING'}")
    run.check(bool(e and x) and e.groups() == x.groups(), f"isolation's own report: exit restored the same count and types: {exit_ or 'MISSING'}")
    exit_kv = dict(KV_RE.findall(exit_))
    for key in ("isolation_held_until_exit", "members_unchanged", "guard_removed", "rebuild_door_held_until_exit", "rebuild_door_restored"):
        run.check(exit_kv.get(key) == "True", f"isolation's own report: {key}={exit_kv.get(key)}")
    printed = run.last("[AI-ISOLATION] exit")
    run.check(printed == f"[AI-ISOLATION] exit {exit_}", "the printed exit line agrees with the verdict file")
    # Finding 9: the INDEPENDENT observation, by the hook (code the isolation does not control).
    before, after = hook_lines(run)
    b, f = TYPES_RE.search(before), TYPES_RE.search(after)
    run.check(bool(b) and int(b.group(1)) > 1, f"HOOK: the framework's list before the AI started: {before or 'MISSING'}")
    run.check("same_list_object=True" in after and "members_unchanged=True" in after,
              f"HOOK: at process exit the framework holds the very list it had, same members: {after or 'MISSING'}")
    run.check(bool(b and f) and b.groups() == f.groups(), f"HOOK: the same count and types before and after: {b.groups() if b else None} -> {f.groups() if f else None}")
    run.check(bool(e and b) and e.groups() == b.groups(), "the hook's before-record and the isolation's entry report agree")


def grade_DX(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    before, after = hook_lines(run)
    f = TYPES_RE.search(after)
    run.check(bool(before), f"HOOK: the before-record was printed: {before or 'MISSING'}")
    run.check("same_list_object=False" in after, f"HOOK: with the restore skipped, the hook SEES the wrong list: {after or 'MISSING'}")
    run.check(bool(f) and f.group(2) == "GuardListener", f"HOOK: the framework is left with only the AI's guard: {f.groups() if f else after}")
    exit_ = (run.facts().get("isolation") or {}).get("exit", "")
    run.check("NOT RESTORED (FAULT_SKIP_RESTORE)" in exit_, f"the fault really ran: {exit_ or 'MISSING'}")


def grade_W(run: Run) -> None:
    check_gated(run)
    p = run.purity()
    run.check(_int(p.get("foreign_writes")) > 0, f"foreign_writes={p.get('foreign_writes')} (want >0: the cheats plugin wrote memory)")
    run.check(any("game_cheats.py" in origin for origin in origins(run, "writes")), f"origin is the cheats plugin: {origins(run, 'writes') or 'MISSING'}")
    check_breach_exit(run)
    state = run.inspect or {}
    run.check(state.get("money") == MONEY_TARGET, f"the write LANDED: money afterwards = {state.get('money')} (want {MONEY_TARGET})")
    check_after_state(run)


def grade_W2(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    check_sinks_clean(run, run.arm.frames)
    state = run.inspect or {}
    run.check(state.get("money") == FIXTURE_MONEY, f"isolation blocked the cheat: money afterwards = {state.get('money')} (want {FIXTURE_MONEY}, the fixture's)")
    check_after_state(run)


def grade_BT(run: Run) -> None:
    check_gated(run)
    seed = run.seed_inspect or {}
    run.check(seed.get("trainer_battle") is True and seed.get("game_state") == "BATTLE",
              f"NON-VACUITY: the seed is a TRAINER battle in progress: {seed or 'MISSING'}")
    p = run.purity()
    run.check(_int(p.get("foreign_presses")) > 0, f"foreign_presses={p.get('foreign_presses')} (want >0: the bot's trainer-battle path pressed)")
    chains = origins(run, "chains")
    run.check(any("BattleListener.fight" in chain for chain in chains),
              f"a press chain names BattleListener.fight (which runs DefaultBattleStrategy for every trainer battle): {chains or 'MISSING'}")
    run.check(_int(p.get("ai_bot_calls")) == 0, f"ai_bot_calls={p.get('ai_bot_calls')} (want 0: the framework ran its bot code, not the AI)")
    # AMENDED after the first graded run (see the docstring): the starved run may end on its budget.
    check_verdict_file(run)
    reason, code = run.facts().get("exit_reason"), run.facts().get("exit_code")
    run.check((reason, code) in (("purity-breach", 6), ("frame-budget", 4)) and run.exit_code == code,
              f"ended as purity-breach/6 or frame-budget/4: verdict file {reason}/{code}, process exit {run.exit_code}")
    run.check(p.get("verdict") == "BREACH", f"verdict={p.get('verdict')} (from the verdict file)")
    if reason == "frame-budget":
        starved = re.search(r"the AI advanced only (\d+)", run.last("[AI-LIFECYCLE]") + " " + " ".join(run.lines("[AI-LIFECYCLE]")))
        run.check(bool(starved) and int(starved.group(1)) < run.arm.frames,
                  f"the guard ended a STARVED run: {starved.group(0) if starved else 'MISSING'} (frames {run.arm.frames})")
    check_not_killed(run)
    check_after_state(run)


def grade_BT2(run: Run) -> None:
    check_gated(run)
    check_clean_exit(run)
    check_zero_foreign(run)
    check_sinks_clean(run, run.arm.frames)
    seed, state = run.seed_inspect or {}, run.inspect or {}
    run.check(seed.get("trainer_battle") is True, f"NON-VACUITY: the seed is a trainer battle in progress: {seed or 'MISSING'}")
    run.check(state.get("in_battle") is True and state.get("trainer_battle") is True,
              f"afterwards the TRAINER battle is STILL waiting (nobody fought it for the AI): {state or run.inspect_raw[-300:]}")
    check_after_state(run)


def grade_M(run: Run) -> None:
    check_gated(run)
    check_verdict_file(run)
    check_exit(run, "parked-manual", 3)
    # ‼ Not a bare search for the switch's NAME: the launcher's own `[AI-RUN] ... switches=` line
    # contains it, which made the first version of this check pass by construction. The exception's
    # last line is printed only by main.py's `console.print_exception()`.
    printed = [line for line in run.stdout.splitlines() if line.startswith("RuntimeError: AI_PLAYER_FAULT_MANUAL")]
    run.check(bool(printed), f"main.py printed the injected listener exception: {printed[0] if printed else 'MISSING'}")
    seen = run.last("[AI-LIFECYCLE] the framework switched the bot mode to")
    run.check("'Manual'" in seen, f"the guard saw main.py switch to Manual: {seen or 'MISSING'}")
    check_not_killed(run)


def grade_T(run: Run) -> None:
    check_gated(run)
    check_verdict_file(run)
    check_exit(run, "wall-clock", launcher.WALL_CLOCK_EXIT)
    check_not_killed(run)
    run.check(run.purity().get("verdict") == "CLEAN", f"a timed-out run still has a verdict: verdict={run.purity().get('verdict')}")
    run.check(run.elapsed < run.arm.wall + 60, f"ended in {run.elapsed:.1f}s, before the hard clock ({run.arm.wall:g}s, plus the gate run)")


def grade_T2(run: Run) -> None:
    check_gated(run, verdict_file_expected=False)
    wall_line = run.last("[AI-RUN] WALL CLOCK")
    run.check(run.exit_code == launcher.WALL_CLOCK_EXIT, f"exit code {launcher.WALL_CLOCK_EXIT} (got {run.exit_code})")
    run.check(bool(wall_line), f"hard wall-clock line: {wall_line or 'MISSING'}")
    run.check("survivors=[]" in wall_line, "the launcher saw no survivors")
    no_verdict = run.last("[AI-RUN] NO PURITY VERDICT")
    run.check(bool(no_verdict), f"the launcher says the run has no verdict: {no_verdict or 'MISSING'}")
    run.check(run.verdict is None, "no verdict file: a hung run cannot report, and does not pretend to")
    run.check(not run.lines("[AI-PURITY] "), "no [AI-PURITY] line either")
    run.check(bool(run.lines("[AI-LIFECYCLE] FAULT_HANG")), "the brain really hung (its own line)")
    pids = [int(x) for x in re.findall(r"\d+", wall_line.split("pids=", 1)[1].split("]", 1)[0])] if "pids=" in wall_line else []
    try:
        import psutil

        alive = [pid for pid in pids if psutil.pid_exists(pid)]
    except ImportError:
        alive = []
    run.check(bool(pids) and not alive, f"driver re-check: killed pids {pids}, still alive {alive}")


def check_static(run: Run) -> None:
    """The static half on the same plant: the gate FAILS the copy with the predicted rule IN _plant.py,
    and the launcher's own gate (printed before the child started) agreed and launched only because
    it was told to."""
    plant = PLANTS[run.arm.plant or ""]
    plant_lines = [line.strip() for line in run.gate_output.splitlines() if "_plant.py" in line and line.strip().startswith("FAIL")]
    run.check(run.gate_exit == 1, f"static gate FAILS the planted copy (exit {run.gate_exit})")
    run.check(any(f"[{plant.rule}]" in line for line in plant_lines), f"static finding [{plant.rule}] in _plant.py: {plant_lines[:3] or 'NONE'}")
    gate_line = run.first("[AI-GATE] exit=")
    run.check("verdict=FAIL" in gate_line, f"the launcher's own gate failed the copy too: {gate_line or 'MISSING'}")
    run.check(bool(run.lines("[AI-GATE] launching ANYWAY")), "and launched only because of --allow-ungated")


def grade_plant(run: Run) -> None:
    """Both halves on the same plant: the static gate fails the copy, the live audit catches the act."""
    plant = PLANTS[run.arm.plant or ""]
    if plant.counter is None:  # the control plant
        run.check(run.gate_exit == 0, f"static gate PASSES the do-nothing plant (exit {run.gate_exit})")
        check_clean_exit(run)
        check_zero_foreign(run)
        check_sinks_clean(run, run.arm.frames)
        return
    check_static(run)
    p = run.purity()
    run.check(_int(p.get(plant.counter)) > 0, f"LIVE: {plant.counter}={p.get(plant.counter)} (want >0, from the verdict file)")
    check_breach_exit(run)


def grade_XP(run: Run) -> None:
    grade_plant(run)
    state = run.inspect or {}
    run.check(state.get("in_battle") is False, f"the planted presses really reached the game (battle over): {state or run.inspect_raw[-300:]}")
    check_after_state(run)


def grade_XN(run: Run) -> None:
    grade_plant(run)
    p = run.purity()
    run.check(_int(p.get("ai_loads")) == 0, f"ai_loads={p.get('ai_loads')} (want 0: no Python door saw the native load, only the sink did)")


def grade_XM(run: Run) -> None:
    grade_plant(run)
    state = run.inspect or {}
    run.check(state.get("money") == MONEY_TARGET, f"the ffi write LANDED: money afterwards = {state.get('money')} (want {MONEY_TARGET})")
    check_after_state(run)


def grade_XB(run: Run) -> None:
    grade_plant(run)
    planned = run.last("[VERIFIER-PLANT] the BOT's pathfinder")
    run.check(bool(planned), f"NON-VACUITY: the bot's pathfinder really ran inside the brain: {planned or 'MISSING'}")
    run.check(any("map_path.py" in origin for origin in origins(run, "bot")), f"origin names the pathfinder: {origins(run, 'bot') or 'MISSING'}")
    p = run.purity()
    for key in ("ai_presses", "ai_writes", "ai_loads", "unattributed_inputs", "unattributed_state_changes"):
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0: the plant only COMPUTED; layer 3 alone caught it)")


def grade_XG(run: Run) -> None:
    grade_plant(run)
    pressed = run.last("[VERIFIER-PLANT] pressed A")
    run.check(bool(pressed), f"NON-VACUITY: the plant really pressed: {pressed or 'MISSING'}")


#: XK: each attack, and the tamper-origin text the instrument must have recorded for it (a tuple:
#: every part must be in the same origin).
XK_ATTACKS: dict[str, str | tuple[str, ...]] = {
    "zero the unattributed_inputs counter": "PurityCounters.unattributed_inputs was assigned from",
    "patch the counters' class through type()": "the class attribute PurityCounters.breach was assigned",
    "shadow finalize_audit on the instance": "Attribution.finalize_audit was assigned from",
    "call finalize_audit from the brain": "finalize_audit was called by",
    "call write_verdict_file from the brain": "write_verdict_file was called by",
    "zero the store through counters._values": "looked up the counters' private '_values'",
    "subtract through counters._add(count=-1)": "PurityCounters._add('unattributed_inputs', count=-1) was called from",
    # Round 3: the registry refuses this before the store's own "counts only grow" check is reached.
    "subtract through the counter store's own add(-1)": ("the instrument's registry: payload_of was called from", " _store_subtract"),
    "replace attribution._counters": "Attribution._counters was assigned from",
    "switch the audit off with attribution._installed = False": "Attribution._installed was assigned from",
    "clear the memory baseline with attribution._snapshot = None": "Attribution._snapshot was assigned from",
    "rebind the instrument module's BREACH_COUNTERS": "the module attribute ai_player.host.attribution.BREACH_COUNTERS was assigned",
    "rewrite BREACH_COUNTERS in the module's namespace dict": "ai_player.host.attribution.BREACH_COUNTERS was rebound or removed",
    # round 2: the objects that decide how the run ends
    "suppress the verdict file with lifecycle._verdict_path = None": "Lifecycle._verdict_path was assigned from",
    "hand finish another instrument with lifecycle._attribution": "Lifecycle._attribution was assigned from",
    "mark the lifecycle finishing with lifecycle._finishing = True": "Lifecycle._finishing was assigned from",
    "replace session.lifecycle": "Session.lifecycle was assigned from",
    "lift the frame budget with session.frame_cap": "Session.frame_cap was assigned from",
    "forge the isolation's exit report with isolation._exit": "ListenerIsolation._exit was assigned from",
    "silence the guard with guard._on_frame": "GuardListener._on_frame was assigned from",
    # round 3: the registry (each origin names the plant function that called it)
    "inflate real_frames through the registry (payload_of(counters).add(+5))": ("the instrument's registry: payload_of was called from", " _store_inflate"),
    "inflate real_frames through the registry's vault list": ("the instrument's registry: vaults was called from", " _vault_inflate"),
    "switch the doors' counting off with the per-thread depth": ("the instrument's registry: payload_of was called from", " _depth_switch"),
    "hide bot code by poisoning the bot-code cache": ("the instrument's registry: payload_of was called from", " _cache_poison"),
    "clear the sealed modules' fingerprints": ("the instrument's registry: sealed was called from", " _fingerprints_clear"),
}
#: Python itself cannot refuse this one (a dict write); the instrument must DETECT it instead.
XK_DETECT_ONLY = frozenset({"rewrite BREACH_COUNTERS in the module's namespace dict"})


def grade_XK(run: Run) -> None:
    grade_plant(run)
    lines = run.lines("[PLANT] ")
    outcome = {}
    for line in lines:
        label, _, rest = line[len("[PLANT] "):].partition(": ")
        outcome[label] = rest
    tamper = origins(run, "tamper")
    for label, fragment in XK_ATTACKS.items():
        result = outcome.get(label, "MISSING")
        if label in XK_DETECT_ONLY:
            run.check(result != "MISSING", f"ATTACK '{label}': attempted ({result})")
        else:
            run.check(result.startswith("refused"), f"ATTACK '{label}': {result}")
        parts = fragment if isinstance(fragment, tuple) else (fragment,)
        named = [origin for origin in tamper if all(part in origin for part in parts)]
        run.check(bool(named), f"  ...and COUNTED: a tamper origin contains {parts!r}: {named[:1] or 'NONE'}")
    p = run.purity()
    run.check(_int(p.get("instrument_tampered")) >= len(XK_ATTACKS), f"instrument_tampered={p.get('instrument_tampered')} (want >= {len(XK_ATTACKS)})")
    run.check(_int(p.get("unattributed_inputs")) > 0, f"the breach the plant tried to hide is still counted: unattributed_inputs={p.get('unattributed_inputs')}")


def grade_XE(run: Run) -> None:
    run.check(run.exit_code == launcher.NO_VERDICT_EXIT, f"the launcher exits {launcher.NO_VERDICT_EXIT} (got {run.exit_code})")
    child = CHILD_RE.search(run.last("[AI-RUN] child exit code="))
    run.check(bool(child) and child.group(1) == "0", f"NON-VACUITY: the child itself exited 0: {run.last('[AI-RUN] child exit code=') or 'MISSING'}")
    run.check(FORGED_PURITY in run.stdout and FORGED_EXIT in run.stdout, "NON-VACUITY: the forged CLEAN lines were printed")
    run.check(run.verdict is None, "no verdict file: the forged ending never reached the instrument")
    run.check(bool(run.lines("[AI-RUN] NO VERDICT FILE")), f"the launcher says so: {run.last('[AI-RUN] NO VERDICT FILE') or 'MISSING'}")
    run.check(bool(run.lines("[AI-RUN] the child exited 0, but")), "and refuses to report the run as clean")
    run.check(run.gate_exit is not None, f"static gate result recorded (exit {run.gate_exit}; not graded: this attack is on the evidence)")


def grade_XY(run: Run) -> None:
    run.check(FORGED_PURITY in run.stdout, "NON-VACUITY: the forged CLEAN line was printed")
    run.check(any("a SystemExit that did not come from the lifecycle" in line for line in run.lines("[AI-LIFECYCLE]")),
              "the session saw the stray SystemExit")
    check_verdict_file(run)  # the LAST printed purity line is the lifecycle's, and must agree with the file
    check_exit(run, "stray-exit", 2)
    check_not_killed(run)
    run.check(run.gate_exit is not None, f"static gate result recorded (exit {run.gate_exit}; not graded: this attack is on the evidence)")


def grade_XZ(run: Run) -> None:
    run.check(bool(run.lines("[PLANT] caught the lifecycle's SystemExit")), "NON-VACUITY: the plant caught the SystemExit and played on")
    first_exit = run.first("[AI-EXIT]")
    run.check(first_exit == "[AI-EXIT] reason=step0-placeholder code=0", f"NON-VACUITY: the first ending was a clean give-up: {first_exit or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "ran-after-finish", 6)
    p = run.purity()
    run.check(_int(p.get("ran_after_finish")) >= 1 and p.get("verdict") == "BREACH",
              f"the verdict file was REWRITTEN: ran_after_finish={p.get('ran_after_finish')} verdict={p.get('verdict')}")
    first = run.facts().get("first_ending") or {}
    run.check(first.get("exit_reason") == "step0-placeholder", f"and it keeps the first ending as evidence: {first}")
    check_not_killed(run)
    run.check(run.gate_exit is not None, f"static gate result recorded (exit {run.gate_exit}; not graded: catching an exception is ordinary code)")


def grade_XR(run: Run) -> None:
    gate_line = run.first("[AI-GATE] exit=")
    run.check("verdict=FAIL" in gate_line, f"the launcher's gate failed the planted copy: {gate_line or 'MISSING'}")
    run.check(bool(run.lines("[AI-GATE] refusing to launch")), f"and refused: {run.last('[AI-GATE] refusing') or 'MISSING'}")
    run.check(run.exit_code == launcher.GATE_REFUSED_EXIT, f"exit code {launcher.GATE_REFUSED_EXIT} (got {run.exit_code})")
    run.check(not run.lines("[AI-RUN] command="), "the framework was never started")
    run.check(not run.lines("[AI-START]"), "the AI never started")
    run.check(run.verdict is None, "no verdict file")
    run.check(any("_plant.py" in line for line in run.lines("[AI-GATE]")), "the refusal names the planted file")


def _isolation_exit(run: Run) -> dict:
    return dict(KV_RE.findall((run.facts().get("isolation") or {}).get("exit", "")))


def grade_RL(run: Run) -> None:
    check_static(run)
    p = run.purity()
    run.check(bool(run.lines("[PLANT] rewinding")), f"NON-VACUITY: the rewind happened: {run.last('[PLANT] rewinding') or 'MISSING'}")
    served = _int(_isolation_exit(run).get("rebuilds_served"))
    run.check(served >= 1, f"NON-VACUITY: main.py rebuilt its listeners through the AI's door: rebuilds_served={served}")
    run.check(not run.lines("[PLANT] a FRESH foreign listener ran"), "the foreign listener was never built (the rebuild got the AI's list)")
    for key in ("foreign_presses", "isolation_lost"):
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0)")
    run.check(_int(p.get("ai_loads")) >= 1, f"ai_loads={p.get('ai_loads')} (the plant's own load, counted as the AI's)")
    check_breach_exit(run)
    state = run.inspect or {}
    run.check(state.get("in_battle") is True, f"afterwards the wild battle is STILL waiting (no framework listener fought it): {state or run.inspect_raw[-300:]}")
    check_after_state(run)


def grade_RLX(run: Run) -> None:
    check_static(run)
    p = run.purity()
    run.check(bool(run.lines("[PLANT] rewinding")), f"NON-VACUITY: the rewind happened: {run.last('[PLANT] rewinding') or 'MISSING'}")
    run.check(bool(run.lines("[PLANT] a FRESH foreign listener ran")), "NON-VACUITY: without the AI's door the rebuild built and ran the foreign listener")
    run.check(_int(p.get("isolation_lost")) >= 1, f"isolation_lost={p.get('isolation_lost')} (want >= 1)")
    run.check(any("without the AI's guard" in origin for origin in origins(run, "isolation")), f"isolation origin: {origins(run, 'isolation') or 'MISSING'}")
    run.check(_int(p.get("foreign_presses")) >= 1, f"foreign_presses={p.get('foreign_presses')} (the window: the pushed handler pressed once before the frame)")
    check_verdict_file(run)
    check_exit(run, "isolation-lost", 6)
    run.check(p.get("verdict") == "BREACH", f"verdict={p.get('verdict')}")
    check_not_killed(run)


def grade_XC(run: Run) -> None:
    grade_plant(run)
    run.check(any("advance_time" in origin for origin in origins(run, "writes")), f"the write's origin names advance_time: {origins(run, 'writes') or 'MISSING'}")


def grade_XQ(run: Run) -> None:
    grade_plant(run)
    run.check(any("RTC" in origin for origin in origins(run, "memory")), f"the change's origin names the game clock (RTC): {origins(run, 'memory') or 'MISSING'}")


def grade_XV(run: Run) -> None:
    grade_plant(run)
    run.check(any("_prev_pressed_inputs" in origin for origin in origins(run, "inputs")),
              f"the origin names _prev_pressed_inputs: {origins(run, 'inputs') or 'MISSING'}")


def grade_H(run: Run) -> None:
    check_gated(run)
    header = run.first("[AI-RUN] http_server=")
    run.check(header.startswith("[AI-RUN] http_server=off (forced"), f"the run header says the server is forced off: {header or 'MISSING'}")
    start = run.first("[AI-START] mode=")
    run.check("http_server=off" in start, f"the child read the server as off: {start or 'MISSING'}")
    check_clean_exit(run)
    check_zero_foreign(run)
    check_sinks_clean(run, run.arm.frames)
    run.check("enable: false" in run.http_after, f"the profile's http.yml was rewritten OFF: {run.http_after.strip()[-60:]!r}")


def grade_H2(run: Run) -> None:
    check_direct_gated(run)
    start = run.first("[AI-START] mode=")
    run.check("http_server=on" in start, f"NON-VACUITY: the child really started with the server on: {start or 'MISSING'}")
    run.check(bool(run.lines("[AI-START] REFUSED")), f"the session refused: {run.last('[AI-START] REFUSED') or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "refused-http-server", 9)
    run.check(run.purity().get("verdict") == "UNVERIFIED", f"verdict={run.purity().get('verdict')} (no frame ran)")
    run.check(not run.lines("[AI-ISOLATION] active") and bool(run.lines("[AI-ISOLATION] exit nothing-to-restore")),
              f"the AI never took over: {run.last('[AI-ISOLATION]') or 'MISSING'}")
    watchdog = run.last("[AI-LIFECYCLE] the process was still alive")
    run.check(bool(watchdog), f"the HTTP server's non-daemon thread held the finished process open, and the exit watchdog "
              f"ended it: {watchdog or 'MISSING (did the process exit on its own?)'}")


def _grade_interrupt(run: Run, signal_number: int) -> None:
    check_direct_gated(run)
    run.check(bool(run.lines("[SIGNAL] sent")), f"NON-VACUITY: the console event was sent after the AI started: {run.last('[SIGNAL] sent') or 'MISSING'}")
    seen = run.last("[AI-LIFECYCLE] interrupted by signal")
    run.check(f"signal {signal_number} " in seen, f"the guard saw signal {signal_number}: {seen or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "interrupted", 130)
    run.check(run.purity().get("verdict") == "CLEAN", f"verdict={run.purity().get('verdict')} (an interrupted run still has a verdict)")
    run.check(bool(run.lines("[SIGNAL] child exited by itself")), f"the framework ended by itself: {run.last('[SIGNAL] child') or 'MISSING'}")


def grade_IB(run: Run) -> None:
    _grade_interrupt(run, 21)  # SIGBREAK


def grade_IC(run: Run) -> None:
    _grade_interrupt(run, 2)  # SIGINT


# ---------------------------------------------------------------------- round 2 grades
def grade_RLF(run: Run) -> None:
    check_static(run)
    p = run.purity()
    run.check(bool(run.lines("[PLANT] the FOREIGN rewinder runs")),
              f"NON-VACUITY: the framework's main loop ran the foreign rewind: {run.last('[PLANT] the FOREIGN rewinder') or 'MISSING'}")
    served = _int(_isolation_exit(run).get("rebuilds_served"))
    run.check(served >= 1, f"NON-VACUITY: main.py rebuilt its listeners through the AI's door: rebuilds_served={served}")
    run.check(not run.lines("[PLANT] a FRESH foreign listener ran"), "the foreign listener was never built (the rebuild got the AI's list)")
    run.check(_int(p.get("foreign_loads")) >= 1, f"foreign_loads={p.get('foreign_loads')} (want >= 1: the rewind was the framework's)")
    run.check(any("foreign_rewinder_plugin.py" in origin for origin in origins(run, "loads")),
              f"the load's origin names the foreign code: {origins(run, 'loads') or 'MISSING'}")
    for key in ("ai_loads", "foreign_presses", "isolation_lost"):
        run.check(_int(p.get(key)) == 0, f"{key}={p.get(key)} (want 0)")
    gave_up = run.last("[AI-LIFECYCLE] the brain's own reason was")
    run.check("'step0-placeholder'" in gave_up, f"the AI was NOT starved: it reached its own give-up: {gave_up or 'MISSING'}")
    check_breach_exit(run)
    state = run.inspect or {}
    run.check(state.get("in_battle") is True, f"afterwards the wild battle is STILL waiting (no framework listener fought it): {state or run.inspect_raw[-300:]}")
    check_after_state(run)


def grade_G(run: Run) -> None:
    check_direct_gated(run)
    run.check(bool(run.lines("[DEBUG-WRAPPER] context.debug = True")), f"NON-VACUITY: the wrapper switched debug on: {run.last('[DEBUG-WRAPPER]') or 'MISSING'}")
    start = run.first("[AI-START] mode=")
    run.check("debug=True" in start, f"NON-VACUITY: the session saw the framework in debug mode: {start or 'MISSING'}")
    refused = run.last("[AI-START] REFUSED")
    run.check("debug mode" in refused, f"the session refused: {refused or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "refused-debug-mode", 9)
    run.check(run.purity().get("verdict") == "UNVERIFIED", f"verdict={run.purity().get('verdict')} (no frame ran)")
    run.check(not run.lines("[AI-ISOLATION] active") and bool(run.lines("[AI-ISOLATION] exit nothing-to-restore")),
              f"the AI never took over: {run.last('[AI-ISOLATION]') or 'MISSING'}")
    run.check(run.elapsed < run.arm.wall, f"ended by itself in {run.elapsed:.1f}s, inside the {run.arm.wall:g}s bound")


def grade_XW(run: Run) -> None:
    grade_plant(run)
    run.check(bool(run.lines("[PLANT] entered peek_frame")), f"NON-VACUITY: the plant held a look-ahead open: {run.last('[PLANT] entered') or 'MISSING'}")
    p = run.purity()
    run.check(_int(p.get("real_frames")) >= run.arm.frames,
              f"real_frames={p.get('real_frames')} (want >= {run.arm.frames}: every main-loop frame audited, the open look-ahead notwithstanding)")
    run.check(any("look-ahead (peek_frame) was still open" in origin for origin in origins(run, "tamper")),
              f"a tamper origin names the open look-ahead: {origins(run, 'tamper') or 'MISSING'}")
    state = run.inspect or {}
    run.check(state.get("in_battle") is False, f"NON-VACUITY: the unseen presses reached the game (battle over): {state or run.inspect_raw[-300:]}")
    check_after_state(run)


def grade_XWT(run: Run) -> None:
    grade_plant(run)
    held = run.last("[PLANT] a worker thread entered peek_frame")
    run.check("entered=True" in held, f"NON-VACUITY: another thread held a look-ahead open: {held or 'MISSING'}")
    run.check(bool(run.lines("[PLANT] ran one extra frame")), "NON-VACUITY: the main thread ran its extra frame")
    run.check(any("_plant.py" in origin and "run_frame" in origin for origin in origins(run, "frames")),
              f"the extra frame was counted AS an extra frame, naming the plant: {origins(run, 'frames') or 'MISSING'}")


CONTINUITY_ORIGIN = "main-loop frames ran without a sink audit"


def grade_M8(run: Run) -> None:
    """M8 reverts the classification order: XW's grade must fail on it, AND the second layer (frame
    continuity) must still make the run a BREACH."""
    grade_mutant(run)
    p = run.purity()
    run.check(p.get("verdict") == "BREACH" and any(CONTINUITY_ORIGIN in origin for origin in origins(run, "tamper")),
              f"the SECOND layer caught it anyway: verdict={p.get('verdict')}, continuity origin: "
              f"{[o for o in origins(run, 'tamper') if CONTINUITY_ORIGIN in o] or 'MISSING'}")


def grade_M8c(run: Run) -> None:
    """Both layers reverted: the verifier's V5 must reproduce (a CLEAN verdict over unseen presses), or
    the A/B with M8 proves nothing about the continuity check."""
    run.check(bool(run.mutations_applied) and all(": APPLIED" in m for m in run.mutations_applied),
              f"the mutations were applied in the copy: {run.mutations_applied or 'NONE'}")
    run.check(bool(run.lines("[PLANT] entered peek_frame")), "NON-VACUITY: the plant held a look-ahead open")
    p = run.purity()
    run.check(p.get("verdict") == "CLEAN" and run.facts().get("exit_reason") == "step0-placeholder",
              f"V5 REPRODUCED without both layers: verdict={p.get('verdict')} exit_reason={run.facts().get('exit_reason')}")
    run.check(0 < _int(p.get("real_frames")) < run.arm.frames // 2,
              f"real_frames={p.get('real_frames')} of {run.arm.frames}: most main-loop frames went unaudited")
    state = run.inspect or {}
    run.check(state.get("in_battle") is False, f"and the unseen presses won the battle: {state or run.inspect_raw[-300:]}")


IH_MAX_SECONDS_AFTER_SIGNAL = 16.0  # 1 s for the handler (the hang sleeps in 1 s steps) + 10 s grace + margin


def grade_IH(run: Run) -> None:
    check_direct_gated(run)
    run.check(bool(run.lines("[AI-LIFECYCLE] FAULT_HANG")), "NON-VACUITY: the brain really hung (its own line)")
    sent = re.search(r"\[SIGNAL\] sent .* ([\d.]+)s after start", run.last("[SIGNAL] sent"))
    run.check(bool(sent), f"NON-VACUITY: Ctrl+Break was sent while the brain hung: {run.last('[SIGNAL] sent') or 'MISSING'}")
    seen = run.last("[AI-LIFECYCLE] interrupted by signal")
    run.check("signal 21," in seen and "no frame reached the guard" in seen, f"the interrupt watch ended it: {seen or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "interrupted-unresponsive", 130)
    run.check(run.purity().get("verdict") == "CLEAN", f"verdict={run.purity().get('verdict')} (a hung, interrupted run still has a verdict)")
    exited = re.search(r"\[SIGNAL\] child exited by itself: code=(-?\d+) .*elapsed=([\d.]+)s", run.last("[SIGNAL] child"))
    run.check(bool(exited), f"the framework ended by itself: {run.last('[SIGNAL] child') or 'MISSING'}")
    if sent and exited:
        after = float(exited.group(2)) - float(sent.group(1))
        run.check(after <= IH_MAX_SECONDS_AFTER_SIGNAL, f"it ended {after:.1f}s after the signal (want <= {IH_MAX_SECONDS_AFTER_SIGNAL:g}s)")
    # The line names the path (finished off the main thread); "at once" is the timing check above.
    off_main = run.last("[AI-LIFECYCLE] the run was finished on a thread other than the main thread")
    run.check(bool(off_main), f"the instrument's exit watchdog saw the run finished off the main thread: {off_main or 'MISSING'}")


# ---------------------------------------------------------------------- round 3 grades
RACE_MAX_SECONDS_AFTER_SIGNAL = 20.0  # 1 s for the handler + 10 s grace + the slow console's ~0.3 s + margin
WATCH_THREAD = "ai-player-interrupt-watch"


def check_direct_copy(run: Run) -> None:
    """A DIRECT arm that runs a COPY with a test-side plant: the copy is what loaded (the hook appended
    the copy's root), and the driver's own gate result on it is recorded, not graded."""
    package_line = run.first("[AI-PACKAGE]")
    run.check("matches_hook_root=True" in package_line and f"ai_player_plant_{run.arm.plant}_" in package_line,
              f"the session says the planted copy loaded: {package_line or 'MISSING'}")
    run.check(True, f"(recorded, not graded) the driver's gate on the copy: exit {run.gate_exit}")


def _race_common(run: Run) -> None:
    """What IG and IR share: the signal, the fence, the observer, the ending."""
    check_direct_copy(run)
    run.check(bool(run.lines("[PLANT] slow console installed")), "NON-VACUITY: the plant's slow console and observer are in place")
    sent = re.search(r"\[SIGNAL\] sent .* ([\d.]+)s after start", run.last("[SIGNAL] sent"))
    run.check(bool(sent), f"NON-VACUITY: Ctrl+Break was sent after the AI started: {run.last('[SIGNAL] sent') or 'MISSING'}")
    fence = run.last("[AI-LIFECYCLE] the run is being finished on thread")
    run.check(f"thread '{WATCH_THREAD}'" in fence and "on thread 'MainThread'" in fence and "waits for the process to end" in fence,
              f"the main thread's next frame met the fence while the watch finished the run: {fence or 'MISSING'}")
    began = run.last("[PLANT-OBSERVER] the finish began")
    run.check(bool(began), f"NON-VACUITY: the independent observer saw the finish begin: {began or 'MISSING'}")
    check_verdict_file(run)
    check_exit(run, "interrupted-unresponsive", 130)
    p = run.purity()
    run.check(p.get("verdict") == "CLEAN", f"verdict={p.get('verdict')} (an interrupted run is not a breach)")
    run.check(_int(p.get("ran_after_finish")) == 0, f"ran_after_finish={p.get('ran_after_finish')} (a late main thread is not a false BREACH)")
    finish = (run.verdict or {}).get("finish") or {}
    run.check(finish.get("thread") == WATCH_THREAD and finish.get("main_thread") is False,
              f"the verdict file says the interrupt watch finished the run: {finish or 'MISSING'}")
    exited = re.search(r"\[SIGNAL\] child exited by itself: code=(-?\d+) .*elapsed=([\d.]+)s", run.last("[SIGNAL] child"))
    run.check(bool(exited), f"the framework ended by itself: {run.last('[SIGNAL] child') or 'MISSING'}")
    if sent and exited:
        after = float(exited.group(2)) - float(sent.group(1))
        run.check(after <= RACE_MAX_SECONDS_AFTER_SIGNAL, f"it ended {after:.1f}s after the signal (want <= {RACE_MAX_SECONDS_AFTER_SIGNAL:g}s)")


def _frames_after_finish_began(run: Run) -> int:
    counts = [int(n) for n in re.findall(r"\((\d+) frames\)", "\n".join(run.lines("[PLANT-OBSERVER] a frame RAN")))]
    return max(counts, default=0)


def grade_IG(run: Run) -> None:
    _race_common(run)
    seen = run.last("[AI-LIFECYCLE] interrupted by signal")
    measured = re.search(r"NOT stuck: (\d+) frames ran and (\d+) reached the guard", seen)
    run.check("signal 21," in seen and bool(measured) and int(measured.group(1)) > 0 and int(measured.group(2)) > 0,
              f"the watch says what it MEASURED (frames kept running and reaching the guard): {seen or 'MISSING'}")
    run.check("stuck after" not in seen and "no frame reached the guard" not in seen,
              f"...and does not claim the main thread is stuck: {seen[:200] or 'MISSING'}")
    after = _frames_after_finish_began(run)
    run.check(after <= 1, f"the emulator ran at most ONE frame (the one in flight) after the finish began: {after} "
                          f"({run.last('[PLANT-OBSERVER] a frame RAN') or 'no frame ran'})")


def grade_IR(run: Run) -> None:
    _race_common(run)
    blocked = run.last("[PLANT] the brain blocks the main thread")
    woke = run.last("[PLANT] woke")
    run.check(bool(blocked) and bool(woke), f"NON-VACUITY: the brain blocked, then woke up while the run was being finished: {woke or 'MISSING'}")
    seen = run.last("[AI-LIFECYCLE] interrupted by signal")
    run.check("signal 21," in seen and "no frame ran at all since the watch saw the signal" in seen,
              f"the watch says what it measured (the brain was blocked: no frame ran): {seen or 'MISSING'}")
    after = _frames_after_finish_began(run)
    run.check(after == 0, f"NO frame ran after the finish began: {after} ({run.last('[PLANT-OBSERVER] a frame RAN') or 'none'})")


GRADERS: dict[str, Callable[[Run], None]] = {
    "A": grade_A, "P": grade_P, "B": grade_B, "A2": grade_A2, "C": grade_C, "D": grade_D,
    "W": grade_W, "W2": grade_W2, "M": grade_M, "T": grade_T, "T2": grade_T2,
    "XO": grade_plant, "XP": grade_XP, "XH": grade_plant, "XM": grade_XM, "XL": grade_plant,
    "XN": grade_XN, "XS": grade_plant, "XF": grade_plant, "XT": grade_plant,
    "XB": grade_XB, "XG": grade_XG, "XK": grade_XK, "XE": grade_XE, "XY": grade_XY, "XZ": grade_XZ,
    "XR": grade_XR,
    "RL": grade_RL, "RLX": grade_RLX, "BT": grade_BT, "BT2": grade_BT2, "DX": grade_DX,
    "XC": grade_XC, "XQ": grade_XQ, "XV": grade_XV, "H": grade_H, "H2": grade_H2, "IB": grade_IB, "IC": grade_IC,
    "RLF": grade_RLF, "G": grade_G, "XW": grade_XW, "IH": grade_IH, "M8c": grade_M8c, "XWT": grade_XWT,
    "IG": grade_IG, "IR": grade_IR,
}


def grade_mutant(run: Run) -> None:
    """A MUTANT arm passes only when the arm it reverts a fix for FAILS on it."""
    base = run.arm.mutant_of or ""
    run.check(bool(run.mutations_applied) and all(": APPLIED" in m for m in run.mutations_applied),
              f"the mutation was applied in the copy: {run.mutations_applied or 'NONE'}")
    probe = replace(run, checks=[])
    GRADERS[base](probe)
    failed = [text for ok, text in probe.checks if not ok and not text.startswith(PROVENANCE_PREFIXES)]
    provenance_only = [text for ok, text in probe.checks if not ok and text.startswith(PROVENANCE_PREFIXES)]
    run.check(bool(failed), f"REVERTED FIX DETECTED: grade_{base} FAILS on the mutant ({len(failed)} behavioural checks of "
              f"{len(probe.checks)} fail; {len(provenance_only)} provenance checks fail by construction and are not counted)")
    for text in failed[:8]:
        run.check(True, f"  grade_{base} failing check: {text[:260]}")


ARMS: list[Arm] = [
    Arm("A", "normal, fresh New Game", "ai-step0-fresh", "fresh"),
    Arm("P", "CONTROL: the placeholder taps B through the controller", "ai-step0-fresh", "fresh", {ENV_CONTROL_TAP: "1"}),
    Arm("B", "FAULT keep listeners, wild battle fixture", "ai-step0-fixture", BATTLE_FIXTURE,
        {ENV_FAULT_KEEP_LISTENERS: "1"}, inspect=True, after_advance=0),
    Arm("A2", "same fixture as B, no fault", "ai-step0-fixture", BATTLE_FIXTURE, inspect=True),
    Arm("C", "FAULT the brain raises", "ai-step0-fresh", "fresh", {ENV_FAULT_RAISE: "1"}),
    Arm("D", "listener restoration, normal path (graded on the hook's independent record)", "ai-step0-fresh", "fresh"),
    Arm("W", "FAULT keep listeners + cheats plugin infinite_money ON", "ai-step0-cheats", OVERWORLD_FIXTURE,
        {ENV_FAULT_KEEP_LISTENERS: "1"}, cheats=True, inspect=True),
    Arm("W2", "cheats plugin ON, no fault", "ai-step0-cheats", OVERWORLD_FIXTURE, cheats=True, inspect=True),
    Arm("M", "FAULT a listener raises; main.py switches to Manual", "ai-step0-fresh", "fresh", {ENV_FAULT_MANUAL: "1"}),
    Arm("T", "SOFT wall clock: the mode ends itself and still reports", "ai-step0-fresh", "fresh",
        frames=10_000_000, wall=25.0),
    Arm("T2", "HARD wall clock: FAULT the brain hangs; the launcher kills it", "ai-step0-fresh", "fresh",
        {ENV_FAULT_HANG: "1"}, frames=10_000_000, wall=25.0),
    Arm("XO", "PLANT CONTROL: a plant that does nothing", "ai-step0-fresh", "fresh", plant="XO"),
    Arm("XP", "PLANT direct write of _pressed_inputs (the first verifier's attack)", "ai-step0-fixture", BATTLE_FIXTURE,
        frames=9000, inspect=True, plant="XP", after_advance=0),
    Arm("XH", "PLANT direct write of _held_inputs", "ai-step0-fixture", BATTLE_FIXTURE, frames=9000, plant="XH"),
    Arm("XM", "PLANT ffi memmove of money into WRAM", "ai-step0-cheats", OVERWORLD_FIXTURE, inspect=True, plant="XM"),
    Arm("XL", "PLANT rewind through the core's Python load_state", "ai-step0-fresh", "fresh", plant="XL"),
    Arm("XN", "PLANT rewind through the NATIVE mCoreLoadStateNamed", "ai-step0-fresh", "fresh", plant="XN"),
    Arm("XS", "PLANT emulator.load_save_game", "ai-step0-fresh", "fresh", plant="XS"),
    Arm("XF", "PLANT an extra core.run_frame", "ai-step0-fresh", "fresh", plant="XF"),
    Arm("XT", "PLANT a callback inside the frame (instrument tamper)", "ai-step0-fresh", "fresh", plant="XT"),
    Arm("XB", "PLANT the second verifier's VB: the bot's pathfinder run from the brain", "ai-step0-cheats",
        OVERWORLD_FIXTURE, plant="XB"),
    Arm("XG", "PLANT the second verifier's VP: a press found by a frame walk + match patterns", "ai-step0-fixture",
        BATTLE_FIXTURE, plant="XG"),
    Arm("XK", "PLANT a breach, then twenty attempts to hide it (counters, instrument, lifecycle, session, isolation, guard)",
        "ai-step0-fresh", "fresh", plant="XK"),
    Arm("XE", "RUNTIME-ONLY PLANT: a fake lifecycle prints a forged CLEAN verdict and exits 0", "ai-step0-fresh",
        "fresh", plant="XE"),
    Arm("XY", "RUNTIME-ONLY PLANT: forged lines, then SystemExit(0) from the brain", "ai-step0-fresh", "fresh", plant="XY"),
    Arm("XZ", "RUNTIME-ONLY PLANT: catch the lifecycle's own SystemExit and play on", "ai-step0-fresh", "fresh", plant="XZ"),
    Arm("XR", "the XP plant WITHOUT --allow-ungated: the launcher must refuse", "ai-step0-fixture", BATTLE_FIXTURE,
        plant="XR", allow_ungated=False),
    # ---- step 0.1 ----
    Arm("RL", "PLANT a rewind into a battle (main.py rebuilds its listeners) with a foreign listener waiting to be built",
        "ai-step0-fixture", BATTLE_FIXTURE, inspect=True, plant="RL", after_advance=0),
    Arm("RLX", "the RL plant + FAULT_NO_REBIND: the rebuild runs the framework's fresh listeners",
        "ai-step0-fixture", BATTLE_FIXTURE, {ENV_FAULT_NO_REBIND: "1"}, plant="RL", wall=60.0),
    Arm("M1", "MUTANT of RLX: the instrument's per-frame guard check removed", "ai-step0-fixture", BATTLE_FIXTURE,
        {ENV_FAULT_NO_REBIND: "1"}, plant="RL", wall=40.0, mutant_of="RLX"),
    Arm("BT", "FAULT keep listeners, TRAINER battle fixture", "ai-step01-trainer", TRAINER_FIXTURE,
        {ENV_FAULT_KEEP_LISTENERS: "1"}, inspect=True, after_advance=0),
    Arm("BT2", "same trainer fixture, no fault", "ai-step01-trainer", TRAINER_FIXTURE, inspect=True),
    Arm("DX", "FAULT_SKIP_RESTORE: the hook's record must SEE a list that was not given back", "ai-step0-fresh", "fresh",
        {ENV_FAULT_SKIP_RESTORE: "1"}),
    Arm("M3", "MUTANT of XK: the attribute guards and the counts-only-grow check removed", "ai-step0-fresh", "fresh",
        plant="XK", mutant_of="XK", wall=60.0),
    Arm("XC", "PLANT the game clock advanced through its Python door", "ai-step0-fresh", "fresh", plant="XC"),
    Arm("XQ", "PLANT the game clock changed natively (no door)", "ai-step0-fresh", "fresh", plant="XQ"),
    Arm("M5r", "MUTANT of XQ: the clock comparison removed", "ai-step0-fresh", "fresh", plant="XQ", mutant_of="XQ"),
    Arm("XV", "PLANT a direct write of _prev_pressed_inputs", "ai-step0-fresh", "fresh", plant="XV"),
    Arm("M5p", "MUTANT of XV: the _prev_pressed_inputs watch removed", "ai-step0-fresh", "fresh", plant="XV", mutant_of="XV"),
    Arm("H", "an owned profile with the HTTP server ON in http.yml, through the launcher", "ai-step01-http", "fresh",
        http_on=True),
    Arm("H2", "the same profile, the framework started DIRECTLY (no launcher)", "ai-step01-http", "fresh",
        http_on=True, direct="http", wall=60.0),
    Arm("M5h", "MUTANT of H2: the session's HTTP refusal removed", "ai-step01-http", "fresh", http_on=True,
        direct="http", wall=60.0, mutant_of="H2"),
    Arm("M5w", "MUTANT of H2: the lifecycle's exit watchdog not armed", "ai-step01-http", "fresh", http_on=True,
        direct="http", wall=60.0, mutant_of="H2"),
    Arm("IB", "the framework in its own console gets CTRL_BREAK after the AI started", "ai-step01-signal", "fresh",
        frames=10_000_000, wall=120.0, direct="break"),
    Arm("IC", "the framework in its own console gets CTRL_C after the AI started", "ai-step01-signal", "fresh",
        frames=10_000_000, wall=120.0, direct="c"),
    Arm("M7", "MUTANT of IB: the session's interrupt handlers not installed", "ai-step01-signal", "fresh",
        frames=10_000_000, wall=120.0, direct="break", mutant_of="IB"),
    # ---- step 0.1, round 2 (the verifier's report) ----
    Arm("RLF", "PLANT a FOREIGN rewind into a battle, run by main.py's work_queue (main.py rebuilds its listeners)",
        "ai-step0-fixture", BATTLE_FIXTURE, inspect=True, plant="RLF", after_advance=0),
    Arm("M1r", "MUTANT of RLF: the rebuild door reverted (isolation never takes get_bot_listeners)", "ai-step0-fixture",
        BATTLE_FIXTURE, plant="RLF", wall=60.0, mutant_of="RLF"),
    Arm("G", "the framework in DEBUG mode (a -c wrapper sets context.debug), FAULT_MANUAL armed", "ai-step01-debug",
        "fresh", {ENV_FAULT_MANUAL: "1"}, direct="debug", wall=90.0),
    Arm("M6", "MUTANT of G: the session's debug-mode refusal reverted", "ai-step01-debug", "fresh",
        {ENV_FAULT_MANUAL: "1"}, direct="debug", wall=90.0, mutant_of="G"),
    Arm("XW", "PLANT the verifier's V5: a peek_frame held open on the main thread, then A through no door",
        "ai-step0-fixture", BATTLE_FIXTURE, inspect=True, plant="XW", after_advance=0),
    Arm("M8", "MUTANT of XW: step 0.1's frame classification (look-ahead depth before the main loop)",
        "ai-step0-fixture", BATTLE_FIXTURE, inspect=True, plant="XW", after_advance=0, mutant_of="XW"),
    Arm("M8c", "the M8 mutation + the frame-continuity check removed: V5 reproduced", "ai-step0-fixture",
        BATTLE_FIXTURE, inspect=True, plant="XW", after_advance=0),
    Arm("XWT", "PLANT another thread holds a look-ahead open; the main thread runs an extra frame", "ai-step0-fresh",
        "fresh", plant="XWT"),
    Arm("M8t", "MUTANT of XWT: step 0's look-ahead depth shared by every thread", "ai-step0-fresh", "fresh",
        plant="XWT", mutant_of="XWT"),
    Arm("IH", "the verifier's V4: a HUNG brain in its own console gets CTRL_BREAK", "ai-step01-signal", "fresh",
        {ENV_FAULT_HANG: "1"}, frames=10_000_000, wall=60.0, direct="break"),
    Arm("M7h", "MUTANT of IH: the interrupt watch not started", "ai-step01-signal", "fresh",
        {ENV_FAULT_HANG: "1"}, frames=10_000_000, wall=60.0, direct="break", mutant_of="IH"),
    Arm("M7x", "MUTANT of IH: the exit watchdog waits 20 s even off the main thread", "ai-step01-signal", "fresh",
        {ENV_FAULT_HANG: "1"}, frames=10_000_000, wall=60.0, direct="break", mutant_of="IH"),
    # ---- step 0.1, round 3 (the verifier's notes on round 2) ----
    Arm("IG", "FAULT the guard ignores Ctrl+Break: frames keep running and only the interrupt watch can end the run",
        "ai-step01-signal", "fresh", frames=10_000_000, wall=60.0, direct="break", plant="IG"),
    Arm("M9", "MUTANT of IG: the frame fence reverted", "ai-step01-signal", "fresh", frames=10_000_000, wall=60.0,
        direct="break", plant="IG", mutant_of="IG"),
    Arm("M9w", "MUTANT of IG: the interrupt watch's measured wording reverted", "ai-step01-signal", "fresh",
        frames=10_000_000, wall=60.0, direct="break", plant="IG", mutant_of="IG"),
    Arm("IR", "a brain blocked past the grace wakes up while the interrupt watch is finishing the run",
        "ai-step01-signal", "fresh", frames=10_000_000, wall=60.0, direct="break", plant="IR"),
    Arm("M9r", "MUTANT of IR: the frame fence reverted", "ai-step01-signal", "fresh", frames=10_000_000, wall=60.0,
        direct="break", plant="IR", mutant_of="IR"),
]
for _arm in ARMS:
    if _arm.mutant_of:
        GRADERS[_arm.name] = grade_mutant
GRADERS["M8"] = grade_M8  # grade_mutant against XW, plus the second layer's check


def provenance() -> str:
    """STEP 2.1 (the step-2 review, item 2): with a digest of the working tree, the hook included
    (`gates/provenance.py`)."""
    from ai_player.gates.provenance import HOOK_SCOPE, provenance as tree_provenance

    return tree_provenance(REPO, HOOK_SCOPE, "ai_player/ + hook")


def key_lines(run: Run) -> list[str]:
    tags = ("[AI-GATE]", "[AI-RUN]", "[AI-START]", "[AI-PACKAGE]", "[AI-ISOLATION]", "[AI-HEARTBEAT]", "[AI-PURITY",
            "[AI-LIFECYCLE]", "[AI-EXIT]", "[AI-TRACEBACK]", "[AI-HOOK]", "[DRIVER]", "[PLANT]", "[PLANT-OBSERVER]",
            "[VERIFIER-PLANT]", "[SIGNAL]")
    return [line for line in run.stdout.splitlines() if line.startswith(tags)]


def write_evidence(run: Run, code_ref: str, seed_note: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{EVIDENCE_TAG}-{run.arm.name}.txt"
    switches = ",".join(f"{k}={v}" for k, v in run.arm.env.items()) or "none"
    where = "a TEMPORARY copy of the package (deleted after the run)" if (run.arm.plant or run.mutations_applied) else REPO
    out = [
        f"AI PLAYER BUILD STEP 0.1 - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"command: {' '.join(run.command)}",
        f"package run: {where}" + (f"; started DIRECTLY ({run.arm.direct}), not through the launcher" if run.arm.direct else ""),
        f"env switches: {switches}" + ("; profile game_cheats.yml: infinite_money=true" if run.arm.cheats else "")
        + ("; profile http.yml: the server ON before the run" if run.arm.http_on else ""),
        f"seed: {seed_note}",
        f"code: {code_ref}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s",
        f"run dir (chosen by the driver): {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        "checks (pre-registered in ai_player/gates/live_step0.py's docstring):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
    ]
    if run.mutations_applied:
        out += ["", "---- MUTANT: the fix this arm reverts (text mutations, each applied exactly once) ----", *run.mutations_applied]
    out += ["", "---- the instrument's verdict file (purity.json): what the grade rests on ----",
            json.dumps(run.verdict, indent=2, sort_keys=True) if run.verdict is not None else "(none)"]
    if run.arm.plant:
        out += ["", f"---- the plant (ai_player/_plant.py in the copy; {PLANT_HOST_FILE} calls tick(step, self) every brain step) ----",
                plant_source(run.arm.plant).rstrip()]
    if run.gate_exit is not None:
        out += ["", f"---- static gate run by the driver on the package that ran (exit {run.gate_exit}) ----", run.gate_output.rstrip()]
    out += ["", "---- evidence lines (the [AI-*] / [SIGNAL] / [PLANT] lines from stdout) ----", *key_lines(run)]
    if run.seed_inspect is not None:
        out += ["", "---- inspection of the SEED (inspect_state.py --state <fixture>) ----", json.dumps(run.seed_inspect)]
    if run.arm.inspect:
        out += ["", "---- post-run inspection of the state the run left behind (inspect_state.py) ----",
                json.dumps(run.inspect) if run.inspect else run.inspect_raw[-2000:]]
    if run.arm.http_on or run.arm.name.startswith("H"):
        out += ["", "---- the profile's http.yml right after the run ----", run.http_after.rstrip()]
    out += ["", "---- stdout (full) ----", run.stdout.rstrip(), "",
            "---- ai_player.log (the AI's own log file) ----", run.ai_log.rstrip() or "(none)"]
    from ai_player.gates.provenance import keep_earlier  # (step 4.1 round 3) an earlier tree's file is archived, not lost

    keep_earlier(path)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    names = {arm.profile for arm in ARMS}
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:
            continue
        if "pokebot.py" in cmd and any(name in cmd for name in names):
            found.append(f"pid {proc.info['pid']}: {cmd[:160]}")
    return found


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build steps 0 and 0.1.")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS), help="comma list, e.g. A,B,A2")
    args = parser.parse_args()
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2

    for name, (path, md5) in FIXTURES.items():
        actual = md5_of(path) if path.is_file() else "MISSING"
        if actual != md5:
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}: different bytes, results would not compare")
            return 2

    build_root = launcher.resolve_build_root()
    code_ref = provenance()
    results: list[Run] = []
    for arm in [a for a in ARMS if a.name in wanted]:
        if arm.seed == "fresh":
            seed_note = "FRESH New Game (no state, no cartridge save)"
        else:
            path, md5 = FIXTURES[arm.seed]
            seed_note = f"fixture {path.relative_to(REPO).as_posix()} md5={md5_of(path)}"
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        run = run_arm(arm, build_root)
        GRADERS[arm.name](run)
        evidence = write_evidence(run, code_ref, seed_note)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text}")

    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<4} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
