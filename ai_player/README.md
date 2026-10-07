# ai_player: the Emerald AI that plays the game itself

`ai_player` is a program that plays Pokemon Emerald **with its own code**: walking, exploring,
battling, menus and decisions (USER RULING 35). The story bot is only its teacher; no bot code runs in
its play loop. It reads the game by memory injection and presses the buttons itself (RULING 36).
It is built to become a **single standalone program** that loads the ROM itself and can run
unattended as an art piece (RULING 37 Q1), so the brain (`mode.py`) is framework-free and sees the
game only through abstract interfaces, everything framework-specific sits in `host/`, and no path to
the bot is hard-coded.

Design: `PROJECT KNOWLEDGE/ai-research-notes/2026-10-07-ai-player-v1-DESIGN-DRAFT.md` (sections 10
and 11 win over 2-9) and `ai-agent/HUMAN-PLAY-DESIGN.md`.

**Where it is now: build step 0.1, purity scaffolding after its adversarial review.** The brain is a
placeholder that presses nothing, waits `--frames` frames and gives up with reason `step0-placeholder`.
What step 0 delivers is the boundary every later step stands on: listener isolation (now including
the framework's listener-REBUILD door), action attribution with a sink audit and a bot-code monitor,
a verdict file only the instrument can write, a lifecycle that can never park, and two gates (static
and live) that were each broken by independent verifiers and then fixed. Step 0.1 fixed the ten
findings of the adversarial review of step 0; each fix has a live arm or a unit test that FAILS when
the fix is reverted (the mutant arms `M*` and the mutant halves of `gates/test_host.py`). Its second
round fixed what the verifier of those fixes found: a hung brain could not be stopped from its console
(`IH`), a `peek_frame` held open on the main thread switched the live audit off (`XW`, `M8`, `M8c`),
the lifecycle's state was writable unseen (`XK`), and three findings lacked the proof the review asked
for (debug mode live: `G`, `M6`; a FOREIGN rewind: `RLF`, `M1r`; a real revert of the hook: `test_host`).
Its third round fixed the two notes that verifier left: the INTERRUPT-WATCH RACE (a main thread that
woke up while the watch thread was finishing the run ran its next frame unaudited, or after the
verdict as a false `ran-after-finish` BREACH, and the watch called it "stuck" without measuring; now the
instrument's frame fence holds that frame back and the watch says what it measured: `IG`, `IR`, `M9`,
`M9w`, `M9r`, `test_host` `FrameFenceTests`), and the REGISTRY ROUTE (`_REGISTRY.payload_of(counters)
.add("real_frames", None, None, 5)` was accepted uncounted and could turn an UNVERIFIED run CLEAN; now
the registry and the counter stores answer only the instrument's own file: `XK`, `M3`, `test_host`
`UnverifiedToCleanTests`).

## Run it

From the repo root (the folder that contains `ai_player/`):

```
py -3.12 -m ai_player run --profile NAME [--frames N] [--wall-seconds S] [--fresh | --state PATH]
                          [--run-dir DIR] [--allow-ungated]
```

* **gates first**: runs `gates/check_purity.py` on THIS package and the hook it will start, prints
  `[AI-GATE] exit=N verdict=PASS|FAIL package=...`, and refuses to launch on a FAIL (exit 7) unless
  `--allow-ungated` is given (only the fault arms do that, on purpose);
* creates `sandbox-pokebot/profiles/NAME/` if missing: copies ONLY `metadata.yml` (the ROM binding)
  from an existing profile and writes a `.ai_player_profile` marker (as
  `tools/story-dev/x4_headless.py` `ensure_lane_profile` does for lanes);
* **the HTTP server is OFF for every run**: on every run of an ai_player-owned profile the launcher
  REWRITES its `http.yml` with `enable: false` and says so in the header
  (`[AI-RUN] http_server=off (forced: ...)`). The sandbox's global `profiles/http.yml` switches the
  server ON (a fork divergence), and its `work_queue` callbacks would run framework code between the
  AI's frames. A profile the launcher does not own is left alone, and the session then refuses to
  start (exit 9) if the server is on;
* `--fresh` deletes the profile's `current_state.ss1` and `current_save.sav`, so the game boots to the
  title screen and New Game; `--state PATH` copies a save state to `current_state.ss1`, which the
  emulator loads at startup (`modules/libmgba.py`, `LibmgbaEmulator.__init__`). Both refuse to touch
  a profile without the marker, so a person's own profile is never changed;
* starts `sandbox-pokebot/pokebot.py NAME -m "AI Player" -s 0 -na -hl` (the batch runner's flags:
  unthrottled, muted, headless) in a child process, with `PYTHONPATH`, `PYTHONHOME`,
  `PYTHONPYCACHEPREFIX` and `PYTHONSTARTUP` removed from its environment (they would load code from
  places the gate never read), and echoes its output;
* **two wall clocks**: a few seconds before `--wall-seconds` (10%, 5-30 s) the mode ends ITSELF with
  `reason=wall-clock code=124` and still writes its verdict; if it is stuck and cannot, the launcher
  kills the whole process tree at `--wall-seconds` (exit 124) and prints `[AI-RUN] NO PURITY VERDICT`.
  Ctrl+C in the launcher's console kills the tree too (exit 130, `[AI-RUN] INTERRUPTED`): the child
  has no console of its own, so it never sees that Ctrl+C;
* **grades the run from the verdict file**: reads `<run_dir>/purity.json` (written by the instrument,
  see below) and prints `[AI-RUN] verdict file: verdict=... exit_reason=... exit_code=...`. It exits
  with the child's exit code, except that a child exiting 0 without a CLEAN verdict file for the gated
  package makes it exit 8.

Options travel to the mode as environment variables (`ai_player/options.py`): `AI_PLAYER_FRAMES`,
`AI_PLAYER_RUN_DIR` (the run's `ai_player.log` and `purity.json` land there),
`AI_PLAYER_PACKAGE_ROOT` (the hook APPENDS it to `sys.path`, after the standard library),
`AI_PLAYER_WALL_DEADLINE`. `--build-root` / `AI_PLAYER_BUILD_ROOT` points at a different framework folder.

## Layout

| file | what it is for |
|---|---|
| `mode.py` | the BRAIN, framework-free: `Brain.play(controls, eyes)` over the abstract `Controls` / `Eyes` interfaces; returns its give-up reason (step 0: a placeholder) |
| `host/session.py` | the run inside the framework: start-up refusals (debug mode, HTTP on), Ctrl+C handlers and the interrupt watch thread, the guard callback (park, frame budget, wall clock, interrupt), listener wiring, and driving the brain one frame per `yield` |
| `host/controller.py` | the ONLY place the AI presses buttons or lets frames pass (implements `Controls`) |
| `host/isolation.py` | removes every framework listener the AI does not own, owns `modules.main.get_bot_listeners` (the rebuild door) while the AI runs, restores both on exit |
| `host/attribution.py` | the instrument: counts inputs, writes, loads, clock changes, frames and bot-code calls by origin, audits the sinks, that isolation held and that it saw every main-loop frame, writes the verdict file, seals the host modules, provides `Guarded`, arms the exit watchdog, and holds the FRAME FENCE (no thread but the finishing one runs a frame while the run is being finished) |
| `host/lifecycle.py` | the single exit door (single-entry across threads); exit codes |
| `host/launcher.py` | the CLI side (launcher process): the gate, the profile, HTTP off, the child process, the wall clocks, the verdict file |
| `options.py`, `runlog.py` | run options from the environment; the AI's own log |
| `gates/` | TEST SIDE: the purity gate and its fault tests, the host unit tests, the live proof driver, a state inspector, the trainer-fixture builder, the console-signal helper |
| `../sandbox-pokebot/plugins/custom_modes/ai_player_mode.py` | the hook: registers "AI Player", APPENDS the repo root to `sys.path`, and keeps its own before/after record of the framework's listeners (`[AI-HOOK]`); no game logic |

The subpackage is `host/`, not `platform/` (step 0's name): `platform` would shadow the standard
library's module for anything that put `ai_player/` on `sys.path`. The gate now refuses any top-level
module or folder of the package named like a standard-library module.

## The purity contract

1. **No bot code in the play loop, checked statically** (`gates/check_purity.py`, an AST walk that is
   an allowlist all the way down, the standard library included):
   * (a) framework imports only through listed DOORS, per file, and only along the attribute paths
     each door lists (the controller may use `context.emulator.press_button/hold_button/release_button`
     and nothing else; isolation may read and assign `modules.main.get_bot_listeners` and nothing else
     of `modules.main`); standard-library modules only from a list, each used ONLY as
     `module.<attribute>` with the attribute on its SURFACE (explicit for `sys`, `os`, `pathlib`,
     `traceback`, `signal` (the session only), `atexit` (the hook only), ...; otherwise a public
     attribute that is not a module, not reflective and not from `operator`/`inspect`/`importlib`/`sys`,
     judged against this Python); imports between AI modules only of names their `__all__` lists and
     defines, from files the gate read; the bot's brain refused as a backstop; no top-level module or
     folder named like a standard-library module;
   * (b) no name that writes memory, loads or resets the emulator, changes the game clock, or advances
     frames; button names only in `host/controller.py`; `match` class-pattern attributes and `getattr`
     constants count;
   * (c) the play loop imports neither the test side nor the launcher side; the launcher side does
     not import the framework; the BRAIN (`mode.py`) does not import the host side;
   * (d) no reflection: `__import__`, `exec`, `eval`, `vars`, `setattr`, `getattr` with a name chosen
     at run time, private attributes of other objects, dunders, import-system / tracing / frame
     attributes, `str.format` with attribute or index fields;
   * (e) the files the import system can load are the files the gate read: source parsed from its
     bytes (coding cookies honored), no bytecode or extension modules, no links, nothing but genuine
     cache files in `__pycache__`, and every cache file CPython would load instead of its source
     proven to hold exactly that source's code;
   * (f) only `runlog.py` and the instrument write files; nothing assigns to, or deletes, an attribute
     or item of anything it imported (a shared library, a framework object, another AI module's
     class); the hook may only `sys.path.append`;
   * (g) each host module's `__all__` is pinned in the gate, the instrument's bytes are pinned by
     sha256 (`--instrument-digest`, after a review), its run-time bot-code list must cover every
     module the backstop refuses, only the lifecycle may name its finalizers and exit watchdog, and
     only the session its isolation check (`watch_guard`). `threading` is on three narrow surfaces:
     the instrument (`local`, `Timer`, `current_thread`, `main_thread`, and `RLock`, `get_ident` for
     the frame fence), the session (`Thread`, the
     interrupt watch) and the lifecycle (`Lock`, `get_ident`, single-entry `finish`); only the
     instrument may read `context.frame`.
   The instrument (`host/attribution.py`) is exempt from (b), (d) and (f) only, because it has to
   wrap those very functions; that is why its bytes are pinned.
2. **No framework listener plays for the AI.** On entry the session removes every listener it does
   not own (it owns one: its `GuardListener`) and restores the framework's exact list on exit. This
   happens in the hook's constructor, before the framework's first listener pass. While the AI runs,
   `modules.main.get_bot_listeners` (what `main.py` calls to REBUILD its listeners after a reset or a
   state load from an earlier frame) returns the AI's own list, so no framework listener is even
   built, not for one frame. Before every real frame the instrument checks the guard is in the live
   list; if it is not, the run ends `reason=isolation-lost code=6` before that frame runs: a starved
   AI is a recorded BREACH, never a silent one. The hook independently prints the framework's list
   before the AI starts and at process exit (`[AI-HOOK] ... same_list_object=True members_unchanged=True`).
3. **Measured in every run, at the doors, at the sinks, and in the bot's own code.** The doors count
   every call to the framework's input, write (incl. the game clock's `core.rtc` methods), load and
   frame functions by origin; a foreign press also records the chain of bot functions that made it.
   The sinks catch what no door saw: keys latched with no counted press, or `_prev_pressed_inputs`
   changed between frames (`unattributed_inputs`); WRAM/IWRAM, or the game clock's native setting,
   changed between frames (`unattributed_state_changes`); frames outside the main loop
   (`extra_frames`); a removed wrapper, a new core callback, a rebound name in a sealed host module,
   a look-ahead (`peek_frame`) still open when a real frame runs, or a main-loop frame that ran without
   a sink audit (`instrument_tampered`); a real frame without the AI's guard (`isolation_lost`). A frame
   the main loop runs is ALWAYS audited, whatever look-ahead is open (a verifier held one open on the
   main thread and switched the whole audit off), and `context.frame` (one per main-loop pass) must
   advance by exactly one between audited frames: an independent count of the frames the audit must
   have seen. A `sys.monitoring`
   hook counts every function of the bot's decision code that starts while AI code is on the stack
   (`ai_bot_calls`): bot code that only COMPUTES (the pathfinder) leaves nothing at the doors or sinks.
4. **The verdict is a file, not a line.** At the end, the lifecycle's `finish` (and only it: the
   instrument refuses any other caller and counts it as tampering) has the instrument write
   `<run_dir>/purity.json` from its own counters: verdict, counters, origins, exit reason and code,
   the isolation descriptions, the package that ran. The counts live in a CLOSURE no attribute leads
   to and only grow; the instrument's REGISTRY (a module attribute anyone can name) and each counter
   store answer only code of the instrument's own file, and count every other caller (a positive count
   added through the registry turned an UNVERIFIED run CLEAN before round 3); the instrument's objects
   hold nothing, refuse attribute writes from outside its
   file and count each attempt; its classes are sealed; the host modules are sealed (rebinding a module
   attribute is refused and counted, and a write that goes around that, `vars(module)[...]`, is caught
   by a per-frame fingerprint). The objects that decide how a run ENDS, the lifecycle, the session, the
   listener isolation and the guard listener, are `Guarded` (`attribution.py`): slotted, sealed, and
   writable only from the file that defines their class, so `lifecycle._verdict_path = None`,
   `session.frame_cap = ...` or `guard._on_frame = ...` from AI code are refused and counted. The
   `run_frame` wrapper stays on as a tripwire: a real frame after the
   verdict rewrites the file as BREACH (`ran_after_finish`) and ends the process. The printed
   `[AI-PURITY] ... verdict=CLEAN|BREACH|UNVERIFIED` line is for people; any code can print one.
5. **Never parks.** Every ending is `[AI-EXIT] reason=... code=N`, a verdict file and the process
   exiting: 0 clean give-up; 2 crash (or a stray `SystemExit` from the brain); 3 parked/abandoned/
   restarted by the framework; 4 frame budget (a starved AI); 5 the brain returned without giving up;
   6 purity breach or unverified (also `isolation-lost` and `ran-after-finish`); 9 refused to start
   (the framework's debug mode, which parks a failing mode in `debug_stepping_mode`, or the HTTP server
   on); 124 wall clock; 130 interrupted (Ctrl+C / Ctrl+Break only set a flag; the guard ends the run
   with a verdict on the next frame, `reason=interrupted`; if no frame reaches the guard within 10 s,
   because the brain or anything else on the main thread is stuck, the session's INTERRUPT WATCH thread
   ends the run itself, `reason=interrupted-unresponsive`, with a verdict, and its line says what it
   MEASURED: `no frame ran at all since the watch saw the signal`, or `the main thread is NOT stuck: K
   frames ran ...`). `finish` is single-entry:
   the first thread to reach it writes the verdict and ends the process; a second thread waits for
   that. And while one thread finishes, no other thread runs a frame (the instrument's FRAME FENCE):
   the finish waits, bounded, for a frame already in flight, and a frame started on any other thread
   (a main thread that woke up late from a long call) waits for the process to end instead of running
   (`[AI-LIFECYCLE] ... waits for the process to end instead of running`); the verdict file records
   which thread finished (`finish`). After `finish`, an EXIT WATCHDOG (a daemon timer) ends the process with `os._exit` if it is
   still alive 20 s later (a non-daemon framework thread, the HTTP server's, would otherwise hold the
   interpreter open for ever), or AT ONCE when `finish` ran off the main thread, where `sys.exit` ends
   only that thread. The launcher adds 7 (the gate refused the package) and 8 (exit 0 without a CLEAN
   verdict file).

```
py -3.12 ai_player/gates/check_purity.py          # static gate (exit 0 = PASS)
py -3.12 ai_player/gates/test_check_purity.py     # its fault tests (both verifiers' probes, and the step-0.1 rows)
py -3.12 ai_player/gates/test_host.py             # unit proofs: findings 3, 4, 6, 8 (both threads), the guarded objects, the registry, the frame fence; each with its mutant
py -3.12 ai_player/gates/live_step0.py            # live proof, 63 arms (27 of step 0, 36 of step 0.1 incl. 16 mutants), ~15 min
```

## Fault and control switches

Read inside the AI's own code, never set on the happy path:

| variable | effect | the arms that use it |
|---|---|---|
| `AI_PLAYER_FAULT_KEEP_LISTENERS=1` | skip listener removal | B (wild battle), BT (trainer battle), W (cheats plugin on) |
| `AI_PLAYER_FAULT_RAISE=1` | the brain raises after 30 steps | C |
| `AI_PLAYER_FAULT_MANUAL=1` | a listener raises; `main.py` switches to Manual | M |
| `AI_PLAYER_FAULT_HANG=1` | the brain blocks the main thread (bounded at 300 s) | T2 (hard wall clock) |
| `AI_PLAYER_FAULT_NO_REBIND=1` | isolation does not take the framework's rebuild door | RLX, M1 |
| `AI_PLAYER_FAULT_SKIP_RESTORE=1` | isolation does not give the framework its list back | DX |
| `AI_PLAYER_CONTROL_TAP=1` | CONTROL: the placeholder taps B every 60 steps | P |

A forbidden action cannot be a switch in the real package (the static gate would rightly fail it), so
the PLANT arms copy the package to a temporary folder, add a `_plant.py` that does one forbidden thing
from inside the AI's play loop (`host/session.py` `_steps` calls it once per brain step), and run that
copy through the real launcher (with `--allow-ungated`) and hook. Each must fail the static gate AND be
caught live: `XP`, `XH` (inputs through no door), `XM`, `XN` (memory through no door), `XL`, `XS`
(loads), `XF` (an extra frame), `XT` (a callback inside the frame), `XB` (the bot's pathfinder run from
the brain), `XG` (a press found by a frame walk), `XK` (a breach, then twenty attempts to hide it, on
the counters, the instrument, the lifecycle, the session, the isolation and the guard listener),
`XC`, `XQ` (the game clock, through its door and natively), `XV` (`_prev_pressed_inputs`), `XW` (a
`peek_frame` held open on the main thread, then A through no door: the verifier's V5), `XWT` (a
look-ahead held open by ANOTHER thread while the main thread runs an extra frame), `RL` (a rewind
by the AI that makes `main.py` rebuild its listeners) and `RLF` (the same rewind by FOREIGN code that
the main loop runs from its `work_queue`). `XE`, `XY`, `XZ` attack the evidence instead (a fake
lifecycle printing a forged CLEAN verdict, swapped in with `object.__setattr__` because the plain
assignment is refused now; a stray `SystemExit`; catching the lifecycle's own exit), and `XR` proves
the launcher refuses an ungated package. `XO` is the do-nothing control. `IG` and `IR` (round 3) run a
TEST-SIDE plant that only observes and slows the console (every stdout line takes 20 ms while the run
is being finished, which widens the finish's window so the race is met every run; an observer thread
reads the emulator's own frame counter from the moment the finish begins): in `IG` a FAULT mutation
makes the guard ignore Ctrl+Break, so frames keep running while the watch finishes (the verifier's
VIB); in `IR` the brain blocks the main thread until the finish has begun and then returns, so the
main loop's next step is a frame (the real-code race). `M9` / `M9r` revert the frame fence on each,
and `M9w` the watch's measured wording. `H`, `H2` (HTTP), `IB`, `IC`
(Ctrl+Break, Ctrl+C in a console of the framework's own), `IH` (Ctrl+Break to a HUNG brain: the
verifier's V4), `G` (the framework in debug mode: a test-side `-c` wrapper re-sets `context.debug`
right before the main loop, which headless mode forces off) and `BT`, `BT2` (a trainer battle, from
`gates/fixtures/trainer_battle_r116.ss1`, built by `gates/make_trainer_fixture.py`) are step 0.1's.
The MUTANT arms `M1`, `M1r`, `M3`, `M5r`, `M5p`, `M5h`, `M5w`, `M6`, `M7`, `M7h`, `M7x`, `M8`, `M8t`, `M9`, `M9w`, `M9r` each
revert one fix in a temporary copy and pass only when the arm that guards that fix FAILS on it; `M8`
also shows the frame-continuity check still catching V5, and `M8c` (both layers reverted) reproduces
V5 as CLEAN, so each layer is shown to be load-bearing.

Evidence of the live proof: `ai_player/evidence/<date>-step01-<ARM>.txt` (step 0's own runs:
`<date>-step0-<ARM>.txt`).

## Known limits of step 0.1

* Static analysis cannot see values: a name bound by ASSIGNMENT is not tracked (`cls = type(obj)`
  then `cls.x = 1` is not refused). The classes the verdict depends on are sealed at run time, and
  the verdict is a file only the instrument writes; any other class the AI changes is its own.
* Python has no private memory. The run-time defenses refuse and count every ATTRIBUTE-level route
  to the instrument's state and to the lifecycle's, the session's, the isolation's and the guard
  listener's (instance, class and module attributes, the counters' private storage, negative counts,
  and since round 3 every call into the instrument's registry and counter stores from outside its
  file) and catch a module namespace rewritten behind `__setattr__`; a closure's cells, `object.__setattr__`
  (arm XE uses it on purpose), code compiled under a host file's name (the owner and caller checks
  compare file names; `gates/test_host.py` uses this route on purpose to set up the instrument with no
  emulator), a function's `__code__` reached through private module names, `gc` and `ctypes` can still
  reach anything. The static gate refuses every spelling of those in the AI's own code. That is a list
  of known routes, not a proof.
* The library surfaces are computed from the running Python's standard library: run the gate with the
  bot's Python (3.12). The gate trusts the interpreter, the standard library, site-packages and the
  framework's own code; it judges only which framework code the AI may reach.
* Bot DATA read without running bot code (a constant table) is refused only statically.
* The live audit cannot see a native change to ONLY the CPU or I/O registers, video memory or the
  cartridge save. Every route to the emulator core the two verifiers found is refused statically.
* A run killed by the HARD wall clock has no verdict file; the launcher says so. So has a run whose
  launcher got Ctrl+C (the child is killed, not interrupted, because it has no console).
* Debug mode cannot occur in a plain headless start (`modules/gui/headless.py` forces it off); arm G
  reaches it through a test-side wrapper that re-sets `context.debug` right before the real main loop,
  and its mutant M6 shows what an unrefused debug run does. In a GUI the main loop runs in a worker
  thread, where no signal handler can be installed: the session logs that, and Ctrl+C there behaves
  as before (and a run finished on that thread ends the process at once).
* The interrupt watch needs the Python signal handler to have RUN once, which happens between two
  bytecodes of the main thread. A main thread blocked inside ONE C call (a native deadlock) never runs
  it, so Ctrl+C / Ctrl+Break cannot end that run; only an outside kill (the launcher's hard wall clock,
  or closing the console) does, without a verdict. A second Ctrl+C restoring the default action was
  rejected: it would end ordinary runs without a verdict (finding 7 again).
* The frame fence holds back FRAMES, the only way anything reaches the game. A main thread that wakes
  up during the watch's finish may still run Python for the few milliseconds until the exit watchdog's
  `os._exit`: the rest of its brain step, the doors (whose wrappers come off in the finish), and, if it
  starts a new main-loop pass after the finish gave the framework its listeners back, one pass of those
  listeners. None of it can reach a frame, and the process ends without saving its state; the verdict
  covers the run up to the finish, as it does when the main thread finishes (where the framework also
  gets its listeners back before the process ends). A frame stuck in NATIVE code longer than 5 s is not
  waited for: the finish proceeds and records `frame_in_flight` in the verdict file.
* Selecting "AI Player" by hand in a GUI works, but the AI's give-up then ends that bot process (by
  design: an AI run never parks), and without a run directory there is no verdict file.
