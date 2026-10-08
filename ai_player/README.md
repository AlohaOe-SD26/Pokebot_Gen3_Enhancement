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

**Where it is now: build step 2, the HANDS** (section "The hands (build step 2)" below): the AI presses the
buttons ITSELF, at a person's pace, for text and menus. It plays a New Game from the title screen to the
moving truck (gender and name chosen by its personality, the name TYPED on the keyboard), heals at a Pokemon
Center nurse, buys Poke Balls at a mart and sets the wall clock in the player's room. Every A that moves a
text on is pressed only when the eyes say the game waits for it, and every cursor is moved by READING it. The
eyes now also see the open menu and its cursor, the keyboard, the clock, the mart's list and quantity, and
the text on screen. Proven live through the real launcher under the unchanged purity audit
(`gates/live_step2.py`: 4 skills, 3 fault arms that show the harm a naive driver does), and by unit
tests on screens the eyes really saw (`gates/test_hands.py`). STEP 2.1 (section "Step 2.1" below) answered the
step-2 verifier's weak proofs: every A press of every skill is now checked against the GAME'S behaviour in forks
of its frame (arms WBI, WBN, WBM, WBC, with a control and a fault arm), every A press of a real run is classified,
no idle stretch is logged under a catch-all reason (the eyes see fades and scenes), the clock's fault arm is
pinned, a warp that differs in y only is played live (`live_step1.py` WARPY), and a 20-seed RATE arm measures
how often each skill succeeds. Each skill is its own brain
(`AI_PLAYER_BRAIN=intro|nurse|mart|clock`); there is no navigator yet (step 3), so the nurse, the mart and the
clock start from fixtures that stand in front of them.

**Step 1.1, the EYES after their adversarial review** (section "The eyes" below): the AI reads the game into
an immutable `Observation` (what is on screen, the party, the PC boxes, the bag, progress, a battle's two
sides), writes an ACTION LOG, and prints the lines the learner's scorer reads. A second brain, the WATCHER
(`AI_PLAYER_BRAIN=watcher`), looks every N frames and presses nothing; it is how the eyes were proven against
ground truth live (`gates/live_step1.py`, 21 arms since step 2.1 added WARPY) under the unchanged purity audit. The default brain is still
step 0's placeholder. Step 1.1 (section "Step 1.1" below) fixed the six findings of the step-1 review and two
more its new live arms found, each with a test or arm that fails when the fix is reverted.

**Step 0.1, purity scaffolding after its adversarial review.** The placeholder brain presses nothing,
waits `--frames` frames and gives up with reason `step0-placeholder`.
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
`AI_PLAYER_RUN_DIR` (the run's `ai_player.log`, `actions.jsonl` and `purity.json` land there),
`AI_PLAYER_PACKAGE_ROOT` (the hook APPENDS it to `sys.path`, after the standard library),
`AI_PLAYER_WALL_DEADLINE`. `--build-root` / `AI_PLAYER_BUILD_ROOT` points at a different framework folder.
Build step 1: `AI_PLAYER_BRAIN=placeholder|watcher` (default placeholder) and `AI_PLAYER_WATCH_EVERY=N`
(default 60) choose the brain; the launcher passes its environment to the child, so

```
AI_PLAYER_BRAIN=watcher py -3.12 -m ai_player run --profile ai-step1-eyes --frames 600 --state tools/story-dev/saves/route116team.ss1
```

watches a save for 600 frames: `[AI-EYES]` digests on stdout, the Observations in `<run_dir>/actions.jsonl`.

Build step 2: the HANDS brains, `AI_PLAYER_BRAIN=intro|nurse|mart|clock`, each play one skill and give up with
its outcome (`[AI-EXIT] reason=intro: in the truck; intended Rosa (GIRL) code=0`). Their options (read by the
brain itself through `options.py` `HandsOptions`, because the host is finished: see "The hands"):
`AI_PLAYER_SEED=N` (the run's seed; unset: drawn from the clock and logged), `AI_PLAYER_PERSONALITY=Catcher|
Story|Trainer` (unset: drawn from the seed), `AI_PLAYER_MART_ITEM` (default `POKé BALL`), `AI_PLAYER_MART_COUNT`
(default 5), `AI_PLAYER_CLOCK=HH:MM` (default: the computer's local time). For example

```
AI_PLAYER_BRAIN=intro AI_PLAYER_SEED=3 py -3.12 -m ai_player run --profile ai-step2-hands --frames 16000 --wall-seconds 900 --fresh
AI_PLAYER_BRAIN=mart AI_PLAYER_MART_COUNT=5 py -3.12 -m ai_player run --profile ai-step2-hands --frames 8000 --state ai_player/gates/fixtures/mart_rustboro.ss1
```

plays a New Game to the truck (seed 3: Catcher, GIRL, "Rosa"), and buys 5 Poke Balls in the Rustboro Mart.

## Layout

| file | what it is for |
|---|---|
| `mode.py` | the BRAIN, framework-free: `Brain.play(controls, eyes)` over the abstract `Controls` / `Eyes` interfaces; returns its give-up reason (step 0: a placeholder; step 1 adds `WatcherBrain`; step 2 adds `HandsBrain`, reached through `Brain` because the session is finished) |
| `hands/pad.py` | step 2: the PAD (every press a jittered hold and gap, a gate it names, logged; reading and thinking delays; never an idle without a reason) and `Hands`, what every skill holds (eyes, pad, the choices stream, the faults, the log) |
| `hands/dialogue.py` | step 2: advance text only on the eyes' waits, stop at every menu; start a conversation only while the player is free (`talk`) |
| `hands/menus.py` | step 2: move a cursor by reading it, choose by intent, answer a yes/no, type a name, set the clock, the "How many?" box, and the nurse (`nurse_heal`) and the mart (`mart_buy`) |
| `skills/intro.py`, `skills/clock.py` | step 2: the New Game intro from the title screen to the truck; the wall clock in the player's room |
| `personality.py` | step 2: the base personality (Catcher, Story, Trainer) and the intro's two choices, gender and name, by a personality-weighted draw from the seed |
| `eyes/screens.py` | step 2: the eyes' perception of menus and text (framework-free): which menu is open by its input task, its cursor, the keyboard's layout, the charmap, the tasks that wait for A/B |
| `eyes/observation.py` | the immutable `Observation` and its parts (framework-free): what one look sees |
| `eyes/view.py` | the AI's perception rules (framework-free): the on-screen window, tile behaviours, object kinds, the screen, when a text waits for a button (`text_printer_wait`), the story flags; tables from pret/pokeemerald |
| `eyes/party.py` | how a party Pokemon is stored, decoded by the AI's own code (framework-free) |
| `host/eyes.py` | the ONLY file that reads the game: implements `Eyes.look()` through read-only framework doors |
| `memory_log.py` | the ACTION LOG records and the SCORER LINES, built from Observations (framework-free) |
| `host/session.py` | the run inside the framework: start-up refusals (debug mode, HTTP on), Ctrl+C handlers and the interrupt watch thread, the guard callback (park, frame budget, wall clock, interrupt), listener wiring, and driving the brain one frame per `yield` |
| `host/controller.py` | the ONLY place the AI presses buttons or lets frames pass (implements `Controls`) |
| `host/isolation.py` | removes every framework listener the AI does not own, owns `modules.main.get_bot_listeners` (the rebuild door) while the AI runs, restores both on exit |
| `host/attribution.py` | the instrument: counts inputs, writes, loads, clock changes, frames and bot-code calls by origin, audits the sinks, that isolation held and that it saw every main-loop frame, writes the verdict file, seals the host modules, provides `Guarded`, arms the exit watchdog, and holds the FRAME FENCE (no thread but the finishing one runs a frame while the run is being finished) |
| `host/lifecycle.py` | the single exit door (single-entry across threads); exit codes |
| `host/launcher.py` | the CLI side (launcher process): the gate, the profile, HTTP off, the child process, the wall clocks, the verdict file |
| `options.py`, `runlog.py` | run options from the environment; the AI's own log and its action log file (`RecordFile`) |
| `gates/` | TEST SIDE: the purity gate and its fault tests, the host unit tests, the live proof drivers (`live_step0.py`, `live_step1.py`, `live_step2.py`), the eyes' unit tests (`test_eyes.py`) and ground-truth probe (`probe_eyes.py`), step 1.1's played scenarios (`probe_step11.py`) and revert proof (`revert_step11.py`), step 2's hands unit tests (`test_hands.py`), mutant proof (`revert_step2.py`) and in-process harness (`hands_harness.py`: the same brain on a throwaway emulator, its recorder, and `truth`, the second-path read of a saved state), step 2.1's press-behaviour probe (`probe_presses.py`: every A press of a skill checked against the game in forks of its frame), a state inspector, the four fixture builders (`make_trainer_fixture.py`, `make_defeat_text_fixture.py`, `make_mart_fixture.py`, `make_clock_fixture.py`: each PLAYS a save to the state it needs and prints what it did; `fixtures/` holds the results, their build printouts and the screens the eyes recorded, `hands_recorded_*.json`), the console-signal helper |
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
     of `modules.main`; the eyes, `host/eyes.py` only, sixteen READ functions (step 2 added `modules.game.get_symbol`, a
     symbol-table lookup) and
     `context.emulator.read_bytes/get_frame_count`, `context.rom.is_emerald`, each door documented in
     the gate with what it reads and why it cannot act); standard-library modules only from a list, each used ONLY as
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
py -3.12 ai_player/gates/test_eyes.py             # step 1 + 1.1 unit proofs (55 tests, each rule with its fault half), ~1 s
py -3.12 ai_player/gates/revert_step11.py         # step 1.1: each fix REVERTED in a copy of the package fails its predicted test (13 reverts + a control), ~1 min
py -3.12 ai_player/gates/live_step1.py            # step 1 + 1.1 live proof, 21 arms (the eyes against ground truth, XW: the waits fix reverted, XG: each truth check's fault half; WARP, SW, BS, BLT, BLW: step 1.1's scenarios PLAYED, with revert copies; WARPY (step 2.1): a warp differing in y only), ~25 min
py -3.12 ai_player/gates/probe_step11.py SCENARIO # one step-1.1 scenario (warp, warp_y, sign, start, trainer, catch, replay) in a throwaway emulator
py -3.12 ai_player/gates/make_defeat_text_fixture.py   # rebuilds E10's fixture by PLAYING E5's battle (then re-pin its md5)
py -3.12 ai_player/gates/test_hands.py            # step 2 + 2.1 unit proofs (37 tests, on screens the eyes recorded; each rule with its fault half), ~1 s
py -3.12 ai_player/gates/revert_step2.py          # step 2 + 2.1: each check of the REAL hands code broken in a copy (25 mutants + a control): 21 caught, 4 redundant alone (with the reason), ~2 min
py -3.12 ai_player/gates/live_step2.py            # step 2 + 2.1 live proof, 14 arms (INTRO, NURSE, MART, CLOCK; the fault arms XU, XBN, XBC; step 2.1: WBI, WBN, WBM, WBC every A press against the game, WBX its control, XTW its fault, RATE 20 seeds per skill), seed 3, ~12 min
py -3.12 ai_player/gates/live_step2.py --seed 9 --arms INTRO,XU,XBN,NURSE,MART,CLOCK,XBC,WBI,WBN,WBM,WBC,WBX,XTW   # the REPLICATION (evidence tag step2-seed9)
py -3.12 ai_player/gates/probe_presses.py BRAIN --fresh | --state PATH [--seed N] [--fault ...] [--clock HH:MM]
                                                  # step 2.1: one skill in-process, every A press checked against the game in forks of its frame
py -3.12 ai_player/gates/hands_harness.py BRAIN --fresh | --state PATH [--seed N] [--fault ungated_a|blind_count] [--record PATH]
                                                  # one hands brain in-process (development; not a purity proof); `truth STATE` reads a state
py -3.12 ai_player/gates/make_mart_fixture.py     # rebuilds the MART fixture by walking rustboro.ss1 into the mart (then re-pin its md5)
py -3.12 ai_player/gates/make_clock_fixture.py    # rebuilds the CLOCK fixture: the AI's own intro (seed 7), then walked to the clock (re-pin)
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
| `AI_PLAYER_FAULT_NO_CROP=1` | the eyes do not crop to the screen (step 1) | E2X (live_step1) |
| `AI_PLAYER_FAULT_UNGATED_A=1` | the dialogue driver presses A on its cadence with no wait gate and never stops for a menu (step 2) | XU (live_step2) |
| `AI_PLAYER_FAULT_BLIND_COUNT=1` | the menu driver moves every cursor by a count from the top, without reading it (step 2) | XBN, XBC (live_step2) |
| (a COPY of the package, not a switch) | step 2.1: the eyes' TASK_WAITS list a timer task (`Task_NewGameBirchSpeech_WaitToShowBirch`) as a wait | XTW (live_step2): the press-behaviour probe must flag every A pressed on it |

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

## The hands (build step 2)

The AI's hands for text and menus (design draft §6 build order step 2; RULING 37 Q6: human pacing, goal-directed,
never idle). Framework-free: they see the game only through `Eyes.look()` and press only through the brain's
`Controls` (the host's controller), so the instrument counts every press as the AI's (`ai_presses`).

**The pad** (`hands/pad.py`). Every press is a HOLD of a seeded, jittered 3-7 frames followed by a jittered gap of
8-18 frames (a person's 50-300 ms, never the bot's one frame; shorter than the 16 frames a step takes and than
`gKeyRepeatStartDelay`, so one press is one key everywhere). Before the A that moves a text on, a READING delay:
0.3 s + 2.4 frames a character of the page that appeared since the last press, +-20 %, at most 2.5 s; before a
choice, a 0.23-0.75 s look at the menu. Nothing idles without a reason: `idle(frames, reason)` and
`busy(reason)` both take one and LOG it (consecutive busy frames with the same reason are one record:
"watching: a scene plays", "reading along: a text is printing", "watching: the yes_no is not taking input
yet"; since step 2.1 also the fade and the scene the eyes name, "watching: the screen fades (Professor Birch's
speech)", "watching: the map loading (...)", and a real run that logs the catch-all "watching: the game is
busy" fails its arm). Every press NAMES ITS GATE, what the eyes said on the look right before it (`press` refuses an empty
gate), and the action log keeps it beside the look's digest. The seed is split into a PACING stream and a
CHOICES stream, so pacing never changes a choice.

**The rule for A** (the museum-greeter lesson, `PROJECT KNOWLEDGE/08-MISTAKES.md` 2026-07-23). `dialogue.advance`
presses A only when the eyes say `waits_for_button` on a FRESH look right before the press (a text printer in
WAIT / CLEAR / SCROLL_START, the script's `waitbuttonpress`, or, new in step 2, a TASK that polls A/B with no
printer waiting: `eyes/screens.py` TASK_WAITS, e.g. the pause after "What's your name?" and the mart's "Here
you go!"), and it STOPS without pressing the moment a menu is on screen: a choice is made by intent, by the
caller. `dialogue.talk` presses the A that STARTS a conversation only while the player is free (overworld, no
script running, field controls unlocked, nothing on screen), facing the person or thing (across a COUNTER for
the nurse and the clerk). Every other A confirms a choice whose cursor a look has just shown ON the option.

**Cursors are read, never counted** (`hands/menus.py`). `move_cursor` looks, presses ONE step toward the target,
and looks again; `choose` presses A only when the look right before it shows the cursor on the option, and
presses again if the game dropped the A (at most 3). Why: the keyboard's cursor stays on the last key typed, the
start menu remembers its row, the wall clock's "Is this the correct time?" opens on NO, a script's yes/no
ignores input for 5 frames, a multichoice for 2 to 12. `type_name` switches the page with SELECT, steps the
cursor the shorter way round (the rows wrap through the button column, `src/naming_screen.c`
HandleDpadMovement), presses A on the key, READS the text after every press (B deletes a wrong letter), then
START and A on OK. `set_clock` holds the D-pad while the clock is far (`clock_hold_frames`: the hand speeds up,
6/3/2/1 frames a minute, `src/wallclock.c`) and steps the last minutes with short presses, reading the time
after each. `set_quantity` reads "x NN" (Up +1, Right +10).

**What the eyes see now** (`eyes/screens.py`, read by `host/eyes.py`). `ScreenState.ui` is a `MenuView`: the open
menu, recognised by the TASK that runs its input (a menu's cursor struct outlives the menu), its options and
cursor, and whether it takes input yet:

| ui | what is read (pret/pokeemerald) |
|---|---|
| `yes_no`, `gender`, `mart_menu`, `multichoice` | `sMenu` (`src/menu.c` struct Menu: cursorPos @2, max @4); a script yes/no's 5-frame delay (its task's data[2]); a multichoice's option texts from the ROM's `sMultichoiceLists` |
| `main_menu` | its task's data (`src/main_menu.c` tMenuType data[0], tCurrItem data[1]) |
| `start_menu` | `sStartMenuCursorPos`, `sNumStartMenuActions`, `sCurrentStartMenuActions` |
| `naming` | `sNamingScreen` (`src/naming_screen.c` struct NamingScreenData: textBuffer @0x1800, state @0x1E10, currentPage @0x1E22, cursorSpriteId @0x1E23, template @0x1E28) and the cursor sprite's data[0], data[1]; input only in STATE_HANDLE_INPUT with the input task enabled |
| `clock` | its task's data (`src/wallclock.c` tHours data[2], tMinutes data[3]; input only while the hand is on a minute) |
| `mart_buy`, `mart_quantity` | `sMartInfo` (itemList @8, itemCount @0xC), each item's name and price from the ROM's `gItems`; `sShopData` (selectedRow @0x2006, scrollOffset @0x2008, maxQuantity @0x200A); the quantity in its task's data[1] |
| `bag`, `party` | `gBagPosition` (pocket @5, cursor and scroll per pocket); `gPartyMenu.slotId` @9 |
| `title`, `intro_movie` | Task_TitleScreenPhase3 (takes A or START); the intro movie and the title's logo animation (any key skips) |

`ScreenState.text` is the message on screen as far as it has printed, decoded by the AI's own charmap (from
`gStringVar4`, `gDisplayedStringBattle` or a ROM string), and `script_running` / `controls_locked` say whether
an A next to a person would START something. One new READ-ONLY door: `modules.game.get_symbol` (a symbol
table lookup), to know which buffer a printer's `currentChar` points into. Step 2.1 adds `ScreenState.fading`
(`gPaletteFade.active`: bit 7 of byte 7, `include/palette.h`) and `ScreenState.scene` (what plays when nothing takes
input, in a person's words: `eyes/screens.py` SCENE_CALLBACKS by `gMain.callback2`, resolved once with `get_symbol`,
then SCENE_TASKS by a task's name, then SCENE_STATES), read through the same doors (no new one).

**The skills** (`skills/intro.py`, `skills/clock.py`, `hands/menus.py` nurse_heal and mart_buy), each with ONE
goal and one loop: `advance` toward the goal, and answer every `menu:<kind>` it stops at by intent. The intro:
skip the movie and the logo with START after a moment, START at the title, NEW GAME, Birch's pages read and
moved on, BOY or GIRL by the personality's weighted draw (`personality.py`: P(GIRL) 0.6 Catcher, 0.45 Story,
0.5 Trainer: taste, not strategy), the "your name?" task wait, the name drawn from the personality's list and
TYPED (mixed case, so the page switch is used), "So it's NAME?" answered YES only if the question names the
typed name (otherwise NO, and the intro asks again), then read to the truck and STOP (nothing is pressed in the
truck). The nurse: turn to her, talk, read, YES, read to the end, then check every party Pokemon is at full HP.
The mart: talk, BUY, the item by name in the list, the quantity read, YES to the price, B out of the list, QUIT,
read the goodbye, then check the bag rose by N and the money fell by N x the listed price. The clock: face it,
talk, read, set the computer's local time (logged first), YES (the cursor opens on NO), read Mom's scene to its
end. Each brain is bounded by `--frames` and ends with the skill's outcome as its reason.

**Why the brain reads its own options.** The host is finished (no change to `ai_player/host/` but the eyes in
step 2), and the session builds `Brain(settings, say)` for every brain but the watcher with step 0's
`BrainSettings`. So `mode.py` `Brain` reads `options.HandsOptions` (the same environment the session read) and
hands the run to a `HandsBrain` when `AI_PLAYER_BRAIN` names one; for `placeholder` nothing changes.

**Proofs.** `gates/live_step2.py` runs each arm through the real launcher (the gate first, the purity instrument,
the verdict file) and grades it three ways, every check quoting both values: PURITY (CLEAN, every breach counter
0, `ai_presses` equal to twice the pad's own count: a `hold_button` and a `release_button` per press, the run
ended by itself within its budget); the GAME by a second path, from the state the run LEFT (`hands_harness.py
truth`: save block 2's name and gender by the probe's charmap, `get_party()`'s HP, the probe's bag and money
decode, save block 1's flag and variable bits, `gLocalTime`, the ROM's price), never the AI's eyes; and the
HANDS from the action log (every press has its gate; every A that moved a text was pressed on a look whose
digest says `waits=A/B(<that reason>)`; the pace). EVERY arm, the fresh ones included, first ASSERTS that the state
graded is the one this run wrote (`check_after_is_this_run`: written after the run started, its frame counter the
start's plus the run's real frames +-5, a fixture arm's md5 not the fixture's; before, the fresh arms relied on the
launcher unlinking the old state without asserting it), and that check is fault-tested on 7 synthetic runs before
any arm (`[SELFTEST]`, quoted in every evidence file: a stale mtime, a frame +-3000, no file and the fixture's md5
each fail it). Evidence `evidence/2026-10-07-step2-<ARM>.txt`:

| arm | start | what happened (quoted from the evidence) |
|---|---|---|
| INTRO | `--fresh`, seed 3 | `[AI-HANDS] intro: personality Catcher (seed; seed 3): gender GIRL (drawn with P(GIRL)=0.6), name 'Rosa'`; TRUTH `name 'Rosa' gender 1 (GIRL) map [25, 40]` (the truck); 8,664 frames, 55 presses, `ai_presses=110`; 22 A on text waits, 22 reading delays of 42-150 frames; `the AI read the name question before answering it: 'So it’s Rosa?'`; choices `main_menu cursor on 0 (NEW GAME)`, `gender cursor on 1 (GIRL)`, the keys `'R' at (5,2) of the upper page` ... `'a' at (0,0) of the lower page`, `yes_no cursor on 0 (YES)` |
| XU (fault) | the same, `AI_PLAYER_FAULT_UNGATED_A=1` | the same intent logged; HARM `name 'AAAAAAA' (intended 'Rosa'), gender 0 (BOY; intended GIRL)`: the naive A took the gender menu's default and typed the top-left key until the name was full; `243 A presses, gates ['NONE (FAULT ungated A ...)']` |
| XBN (fault) | the same, `AI_PLAYER_FAULT_BLIND_COUNT=1` | the keyboard moved by counts from the top-left key while the cursor starts on the last key typed: HARM `the name in save block 2 is 'R.qq', not 'Rosa'` (the first letter right, the rest wrong); `So it’s R.qq?` read and answered NO four times; the truck never reached in 12,000 frames |
| NURSE | `post_league_lobby.ss1` | before `[['Mightyena', 202, 227]]` not whole; TRUTH after (`get_party`) every Pokemon at full HP, Mightyena 227/227; 7 presses: turn up, talk, 2 pages, `yes_no cursor on 0 (YES)`, 1 page, the script's wait |
| MART | `gates/fixtures/mart_rustboro.ss1` | TRUTH `POKé BALL 5 -> 10: +5`, `money 6680 -> 5680: -1000 (want 5 x the ROM's price 200)`; the quantity read `x1` ... `x5, the number wanted`; 17 presses |
| CLOCK | `gates/fixtures/clock_room.ss1` | the step-2.1 run: `the time to set: 23:26 (the computer's local time)`, in the run's window; TRUTH `FLAG_SET_WALL_CLOCK=True VAR_LITTLEROOT_INTRO_STATE=6 gLocalTime [0, 23, 26, 3]` (the fixture: False, 5); `yes_no cursor on 1 (NO), wanted 0 (YES): one step up`, then YES. (The step-2 run set 22:37: this arm's time, frames and presses follow the computer's clock.) |
| XBC (fault) | the clock fixture, `AI_PLAYER_FAULT_BLIND_COUNT=1`, since step 2.1 `AI_PLAYER_CLOCK=13:37` | HARM `FLAG_SET_WALL_CLOCK=False VAR_LITTLEROOT_INTRO_STATE=5`: "Is this the correct time?" answered with the cursor on NO 55 times (the count assumed it opens on YES), the same 55 on a re-run (with the computer's time it was 50, then 51, for seed 3) |

**The REPLICATION, seed 9** (`live_step2.py --seed 9`, evidence `evidence/2026-10-07-step2-seed9-<ARM>.txt`; its
predictions were written into the script's docstring BEFORE the graded runs, from the in-process harness). The
step-2 verifier noted that re-running seed 3 gives identical numbers: a determinism check, not a replication.
Seed 9 draws another personality and other pacing (every hold, gap, reading delay and think pause), so each arm
is a SECOND trajectory with the same pass criteria. 7 of 7 PASS, `[SELFTEST] ... PASS`, no leftover emulator:

| arm | seed 3 | seed 9 (quoted) |
|---|---|---|
| INTRO | Catcher, GIRL, 'Rosa'; 8,664 frames, 55 presses | `personality Trainer (seed; seed 9): gender GIRL (drawn with P(GIRL)=0.5), name 'Luna'`; TRUTH `name 'Luna' gender 1 (GIRL) map [25, 40]`; `presses=52 frames=8792`; `22 A presses advanced a text, each on a look whose digest says waits=A/B(<that reason>)`; `22 reading delays, 43-150 frames` |
| XU | 'AAAAAAA', BOY; 4,409 frames | `name 'AAAAAAA' (intended 'Luna'), gender 0 (BOY; intended GIRL)`; `presses=247 frames=4530` |
| XBN | 'R.qq' | `the name in save block 2 is 'BELLA', not 'Luna'`; asked `'So it’s L   ?'` four times, NO each time. 'BELLA' is the game's PRESET name, written before EVERY keyboard opening (`src/main_menu.c` NewGameBirchSpeech_SetDefaultPlayerName(Random() % NUM_PRESET_NAMES)) and left in the save because the run ends during a retry |
| NURSE | 1,964 frames | `healed`, `frames=1974`; TRUTH `['Mightyena', 227, 227]` ... every Pokemon at full HP; `4 A presses advanced a text` |
| MART | 1,441 frames | `bought`, `frames=1480`; TRUTH `POKé BALL 5 -> 10: +5`, `money 6680 -> 5680: -1000 (want 5 x the ROM's price 200)` |
| CLOCK | the computer's time (23:26 in the step-2.1 run) | the step-2.1 run: `the time to set: 23:36 (the computer's local time)`, TRUTH `gLocalTime [0, 23, 36, 3]` (step 2's run: 22:38) |
| XBC | NO 55 times (13:37 pinned) | `FLAG_SET_WALL_CLOCK=False VAR_LITTLEROOT_INTRO_STATE=5`; NO 54 times (13:37 pinned; step 2's run, the computer's time: 49) |

`gates/test_hands.py` (37 tests since step 2.1, which added SceneTests and PressKindTests, below): the step-2 files import no framework and no host (fault: a planted import is
caught); `read_ui` on the bytes the host reads (the gender menu's real `sMenu` bytes, the yes/no's input delay, the
main menu, the clock, the keyboard, the intro movie); the PAGE rule on a recorded CLEAR wait (fault: the rule before
its fix reads it as empty); the keyboard table against the decomp; the host's pointer range check; the pad (a press
needs a gate; reading 18-150 frames, growing with the text; seeded jitter); and the hands driven against small
MODELS of each menu (each names its decomp source) that start in screens the eyes really RECORDED in the game
(`gates/fixtures/hands_recorded_{intro,clock,mart,nurse}.json`, from `hands_harness.py --record`): A only on
waits and never on the choice (fault ungated: A while printing and on the choice); each page's reading delay
STARTS after the page has printed and covers the whole page; the clock's yes/no that opens on NO answered YES
(fault blind: NO); nothing pressed in the nurse yes/no's input delay, by `choose` and by `move_cursor` called
directly; the gender menu and a menu whose cursor starts ELSEWHERE (fault blind: SELL instead of BUY); `choose`'s
gate is its OWN look (given a `move_cursor` that says it moved and did not, no A lands); "Rosa" typed from the
opening keyboard and from a mid-name cursor (fault blind: a wrong name); a wrong letter ('Rox') and a keyboard
that opens with text ('Kai'; the decomp's one such keyboard is Walda's phrase, `copyExistingString = TRUE`)
deleted with B, exactly 1 and 3 times; the clock set to 21:47 (fault blind: never confirmed); the quantity to x5
and x23; no talk A while a script runs (fault: with the free check removed it lands on the script). The test file
honours `AI_PLAYER_TEST_SUPPORT_ROOT` (as `test_eyes.py` does), so it runs from a copy of the package.

**Each check of the REAL code carries weight, or is documented as redundant** (`gates/revert_step2.py`, evidence
`evidence/2026-10-07-step2-REVERT.txt`). The fault switches show the tests catch a NAIVE driver; the step-2
verifier mutated the real code and found four checks no test caught. The script now breaks ONE check per copy of
the package and runs `test_hands.py` there (step 2.1 added HS, HSo and HK: the named busy reason, the scene's
callback lookup, the A-press classes; each CAUGHT, so 21 caught of 25 now): the unchanged copy passes all its tests; 18 mutants of step 2 are CAUGHT by their
predicted tests (no stop at a menu; the first wait check of `advance`; both wait checks; `talk`'s free check and
its facing; `choose`'s cursor check; `move_cursor` not reading the cursor, and not waiting for input; the keyboard's
cursor moves, its B delete and its START to OK; the quantity; the clock's outer check, and both; a press without a
gate; an unbounded reading delay; both pointer range checks), and 4 are REDUNDANT ALONE, as predicted, each with
its reason in the evidence: `advance`'s second wait check (H2-gate: a wait the eyes report ends only on a press,
`src/text.c` TextPrinterWait / TextPrinterWaitWithDownArrow, `src/scrcmd.c` WaitForAorBPress, every TASK_WAITS
task), `choose`'s input check (H11: the same frame as `move_cursor`'s last look), and the re-checks after a
'think' pause of the keyboard's OK (H5c) and the clock's time (H8b: the cursor and the hand move only on a press
or a hold). Each redundant check stays, as the press's logged gate.

**The fixtures.** `gates/fixtures/mart_rustboro.ss1` (`make_mart_fixture.py`: `rustboro.ss1`, md5 pinned in the
builder, walked 13 steps into the mart and 4 up the aisle to (3,3), across the counter from the clerk; printout
`mart_rustboro.build.json`) and `gates/fixtures/clock_room.ss1` (`make_clock_fixture.py`: the AI's OWN intro, seed 7,
"Rowan", BOY, then by this builder's presses: out of the truck, A only on the eyes' waits through Mom's two scenes,
breadth-first steps over the tiles the eyes see, up the stairs to (5,2) under the clock; `VAR_LITTLEROOT_INTRO_STATE`
5, `FLAG_SET_WALL_CLOCK` clear; printout `clock_room.build.json`). Both are pinned by md5 in `live_step2.py`. ‼ A
REBUILD DOES NOT REPRODUCE THE BYTES: measured 2026-10-07, the rebuilt states differ from the pinned ones in 8 bytes
and in `gLocalTime` only (the emulator's real-time clock is in the state; frame, map, tile, party, money and bag are
equal), so a rebuild must be re-pinned. The nurse arm uses `tools/story-dev/saves/post_league_lobby.ss1` as it is
(`LEAGUE_NURSE_STAND`, the party not whole).

**Found while building, and fixed:**
* ‼ A GARBAGE POINTER KILLED THE PROCESS. The framework's `read_bytes` bounds EWRAM and IWRAM reads (it raises) but
  not a cartridge read (a raw memmove at `address - 0x08000000`). On the frame the naming screen allocated its data,
  the template pointer held garbage and the eyes' read of it was a Windows access violation, which no `try` catches.
  Every pointer the eyes follow is now range-checked first (`host/eyes.py` `_rom_bytes`, `_ewram_bytes`; also the
  map-header and tileset reads of step 1); `test_hands.py` proves the check refuses before any read.
* The page at a paragraph break read as EMPTY: a printer waiting in CLEAR has already consumed the `\p`
  (`eyes/screens.py` page_text; a recorded wait is its test, with the old rule as its fault half).
* The text under a menu: printers that finished stay inactive, and a rule that took any printer pointing into
  `gStringVar4` reported a stale message; now printer 0's last message (or the ROM string it printed).
* `talk` spent its four facing attempts waiting for a scene to end (found by its unit test); the wait for the
  player to be free now has its own bound.

## Step 2.1: the step-2 verifier's weak proofs, made strong (2026-10-07)

The step-2 verifier passed every arm and listed five WEAK PROOFS. Each now has a proof that can fail; the
predictions were written into `gates/live_step2.py`'s and `gates/live_step1.py`'s docstrings before the graded runs.

| weak proof | what was done | proven by (evidence `evidence/2026-10-07-step2-<ARM>.txt` unless named) |
|---|---|---|
| 1. "each text A was gated" was the log agreeing with itself (the gate and the digest are ONE look), and the two task waits new in step 2 had no behavioural proof | `gates/probe_presses.py`: the real skill in a throwaway emulator; before EVERY A press it saves the frame and asks the GAME in forks of it (the state reloaded before each): is a text still printing (an active printer advancing within 8 frames, no input); does anything move in 300 frames with no input (every active printer, the box, the main callback, the tasks, the script's pointer and status, the keyboard's text); does the SAME press move it; does B, pressed instead, do exactly the same (a continue, not a choice); for the A that starts a conversation, is the player free and does a script start. Every value is the probe's own raw read; the forked run must equal an unforked `hands_harness.py` run | WBI `30 A presses`, `8 menu, 22 wait ... Wrong: none`, `f5587 wait 'task Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (': printing=False still=True A moved it at +1 ['tasks'] B-same=True`, `the forks changed nothing in the run: probe [..., 8664, 55] == unforked harness [..., 8664, 55]`; WBM `f119486 wait 'task Task_ReturnToItemListAfterItemPurchase (A or B)': printing=False still=True A moved it at +1 ['tasks'] B-same=True`; WBN, WBC (the script waits, the talks: `free=True started=True`). CONTROL WBX: the ungated fault under the same probe: `118 of 243 ungated A presses landed on a text still PRINTING, 208 on a screen that moved by itself`. FAULT XTW: a COPY of the eyes listing the timer task `Task_NewGameBirchSpeech_WaitToShowBirch` as a wait: `CAUGHT: 6 A presses gated on the fake wait, 6 flagged by the game's behaviour`, `the 22 other wait-gated presses of the same run are all proven` |
| 2. only NURSE limited the OTHER A presses (talk, menu confirms) | every real launcher arm (`check_gates`, `classify_a`) classifies EVERY A press from its look: a WAIT (`waits=A/B(<that gate>)`, no menu), a MENU confirm (that menu open and taking input, `ui=<kind>[`, nothing waiting) or a TALK (the overworld, nothing waiting, no menu); anything else fails. Still the log about itself; the GAME's side is weak proof 1's arms | INTRO `{'menu': 8, 'wait': 22}; any other: none`; NURSE `{'menu': 1, 'talk': 1, 'wait': 4}`; MART `{'menu': 5, 'talk': 1, 'wait': 3}`; CLOCK `{'menu': 2, 'talk': 1, 'wait': 7}`; `test_hands.py` PressKindTests with fault cases; `revert_step2.py` HK |
| 3. 530 frames of Birch's opening logged under the catch-all "watching: the game is busy (main_menu)" | the eyes report the FADE (`ScreenState.fading`, `gPaletteFade.active`) and the SCENE (`ScreenState.scene`, `eyes/screens.py` scene_of: the main callback, then a task, then the game state, in a person's words: "Professor Birch's speech", "the wall clock", "the map loading"); `busy_reason` names them. Every stretch the four skills stood still under the catch-all was measured first (a spy on `busy_reason`) and is now named | INTRO `55 stretches standing still, NONE under the catch-all`, the reasons `watching: Professor Birch's speech (it runs by itself: nothing on screen takes a press now)`, `watching: the screen fades (...)`; the same check on NURSE, MART, CLOCK; `test_hands.py` SceneTests (every measured stretch has a scene; every callback name is a symbol of the ROM; FAULT: no scene IS the catch-all); `revert_step2.py` HS, HSo |
| 4. the clock arms do not repeat (the time set is the computer's) | XBC's time is PINNED (`AI_PLAYER_CLOCK=13:37`): its harm does not depend on the time, so it now reproduces; CLOCK keeps the computer's time, the default a person uses, so ITS numbers still move with the hour (stated below) | XBC `the time to set: 13:37 (named by the run)`, `the cursor on NO 55 times` (predicted 55 from the in-process run) |
| 5. no live warp that differs only in y; two seeds are two trajectories, not a rate; the pacing is not measured from people | WARPY (`gates/live_step1.py`, `probe_step11.py warp_y`): a scratch search of every map's ROM warp events for a departure and an arrival tile that share x, near a fixture, found the League's 1F escalator (1, 7) -> 2F (1, 6), walked from the NURSE fixture. RATE: each skill once per seed 1-20 in-process, each graded by its second-path truth (the clock at a time spread over the day per seed). The pacing: not measurable here; still a known limit | `evidence/2026-10-07-step21-WARPY.txt`: `on all 15 of those frames the two tiles differ in y ONLY`, the eyes `settling` or `between screens` on each, `[MAP] ... -> EVER GRANDE CITY(16,14) pos=(1, 6)` at the first settled frame; WARPY-R4x (the x-only rule) CAUGHT live `[(8397753, [16, 14], [1, 7], [1, 6]), ...]`, and the same rule on arm WARP's Dewford door NOT caught (the gap closed). RATE: `intro: 20 of 20 seeds succeeded by the second-path truth ... frames 8372-8792`, `nurse: 20 of 20 ... frames 1912-1974`, `mart: 20 of 20 ... frames 1416-1534`, `clock: 20 of 20 ... frames 2455-3226` (each "below ~15% at 95% confidence, the rule of three") |

Seed 9 (`--seed 9`, evidence `evidence/2026-10-07-step2-seed9-<ARM>.txt`) ran every arm but RATE again: 13 of 13
PASS, e.g. WBI `the forks changed nothing in the run: probe ['intro: in the truck; intended Luna (GIRL)', 8792, 52]
== unforked harness [...]`, `8 menu, 22 wait`; WBM the task wait `f119517 ... still=True`; XTW `CAUGHT: 6 A presses
gated on the fake wait, 6 flagged`; XBC `the cursor on NO 54 times`. XBC seed 3 run again
(`evidence/2026-10-07-step2-repro-XBC.txt`): `55 times` again, the same frames.

The probe's forks never touch the run (`restored` on every press, and the forked run equals the unforked one in
outcome, frames and presses: a DETERMINISM check, CLAUDE.md rule 8). B-same is only asked of WAIT presses: on a
menu, A picks and B cancels (the mart's menu is the exception the probe shows: B there is QUIT, like the A the AI
pressed on QUIT).

## Known limits of step 2

* No navigator: the nurse, the mart and the clock start from fixtures in front of them, and the intro stops in the
  truck. Leaving the truck, Mom's scenes, the stairs and the walk to the clock are step 3's (the clock fixture's
  builder does them with test-side presses today).
* Text printed INSTANTLY (speed 0: menu labels, the wall clock's "Is this the correct time?") never enters
  `sTextPrinters` (`src/text.c` AddTextPrinter renders it with a temporary printer), so `ScreenState.text` then shows
  the last message printed before it. With no printer active, `text` is "what was printed last", not proof that it
  is still drawn (the start menu opened with no message shows an old one). No skill depends on it except the
  intro's name check, whose question IS printed by printer 0.
* Menus are named only where a step-2 skill needs them or the task asked: the battle menus, the PC, the summary
  screen, list menus other than the mart's are not; the bag and party report a cursor row, no option names; a
  multichoice's names come from the ROM's table only for script multichoices.
* `eyes/screens.py` TASK_WAITS is a list of the waits met so far, not every task in the game that polls A/B.
* The mart's listed price is the ROM's; the half price of Slateport's sale (`IsPokeNewsActive`) is not modelled.
* The gender and name lean of each personality is a placeholder for variety (no game reason); the name lists are
  short. The clock is set to the computer's local time (as a person would): arm CLOCK's frames, presses and hand
  holds therefore differ between runs at different hours, and only its pass criteria are fixed. XBC (step 2.1),
  WBC and RATE pin the time and reproduce exactly.
* The pacing is a plausible human tempo, not a measured one (no recording of people was available); it is clearly
  slower than the bot's one-frame presses (the intro takes ~8,700 frames, ~2.4 minutes of game time).
* The launcher arms are TWO trajectories per arm, seeds 3 and 9; re-running one seed reproduces its numbers exactly
  (INTRO 8,664 frames, NURSE 1,964, MART 1,441, XBC 55 NO answers; the harness and the live run agree too), a
  determinism check (CLAUDE.md rule 8). The RATE arm (step 2.1) is the frequency answer: 20 seeds per skill,
  in-process (the skills' code; the purity of the same code is the launcher arms'): 20 of 20 for each, so a failure
  rate below ~15% at 95% confidence, not zero; 20 seeds cannot see a rarer failure, and the starts are the same
  three fixtures (another mart, nurse or clock room is untested).
* The behaviour probe (`probe_presses.py`) asks the game about the 300 frames after a WAIT; a wait that would end by
  itself LATER than that would pass it. None of the waits the hands press on can (each polls a button with no
  timeout, the decomp lines in `revert_step2.py` H2-gate), and the XTW fault shows a timer task is caught.
* Four checks of the hands are REDUNDANT ALONE (`gates/revert_step2.py` H2-gate, H11, H5c, H8b: each repeats a check
  made a moment earlier on a thing that changes only on the AI's own press). They stay as the presses' logged gates;
  no test can catch their removal alone, and the evidence says why.

## The eyes (build step 1)

The brain sees the game only through `Eyes.look()` (`mode.py`), which returns ONE immutable
`Observation` (`eyes/observation.py`) read at one frame, stamped with the emulator's frame counter. A
part that cannot be read this frame is None and says why in `problems`; a look never raises.

| part | what | read from |
|---|---|---|
| `frame` | the emulator's frame counter | `context.emulator.get_frame_count()` |
| `screen` | the framework's game state; `overworld` / `battle` / `text` / `menu` / `transition` / `title` / `other`; the open menu (start menu, yes/no, multichoice, bag, party, summary, naming, PC storage, starter choice, main menu); whether the overworld text box is open; whether the game waits for A/B, and WHY (`wait_reason`: `script waitbuttonpress`, or `text printer N WAIT / CLEAR / SCROLL_START`); whether a battle is running | `get_game_state`, `battle_is_active`, `sFieldMessageBoxMode`, the task list, the global script context (`WaitForAorBPress` while not shut down), all 32 `sTextPrinters` (a printer in RENDER_STATE_WAIT, the `{PAUSE_UNTIL_PRESS}` of every trainer's defeat text, or CLEAR / SCROLL_START, the down arrow) and `gTextFlags` (under autoScroll nothing waits for a button) |
| `player` | map (group, number, the region-map name the bot logs use, the map's own constant), position, facing, movement (walking, running, Mach / Acro bike, surfing, underwater), elevation, the VISIBLE 16-bit trainer id (step 1.1: the secret id is never reported); `settling`: during a warp the position is None (step 1.1, below) | `gPlayerAvatar` and the player's object event (raw), save block 1's pos and location, `get_map_data_for_current_position` (once per map, after checking that the live `gMapHeader` IS that map's ROM header from `gMapGroups`: a header left from another map is refused and reported), `get_map_enum`, `get_player` |
| `view` | the 15 x 11 tiles ON SCREEN (below), each with collision, elevation, behaviour, blocked, water, wild encounters (land / water), tall grass, ledge direction, door, warp, half-visible; the objects inside it (item balls, people, cut trees, rocks, boulders, berry trees; step 1.1: every person is an "npc", no trainer label before it engages) and signs (interactable tiles); a picture (`ascii`). None while the position settles | the LIVE grid `gBackupMapLayout` (the map + its 7-tile margin, which holds the connected maps), the tilesets' attributes and `sTileBitAttributes` (ROM, read once), the map's warps and bg events (ROM), `get_map_objects` |
| `party` | species, national dex number, level, HP, status, types, moves with PP, PID (identity), the visible OT id, egg. ‼ None = NOT READ (the title screen; a torn slot makes the WHOLE party None), () = no Pokemon (step 1.1) | raw `gPlayerParty`, decoded by the AI's own `eyes/party.py` (the framework's `get_party()` looks a frame AHEAD on a torn read); names from the data tables |
| `storage` | every Pokemon in the 14 PC boxes: box, slot, PID, the visible OT id, egg (step 1.1: a catch sent to a box is seen by identity); None = not read | `gPokemonStoragePtr`, each slot's UNENCRYPTED header (no decryption) |
| `bag`, `progress` | every ball and healing item with quantities; money, badges, Pokedex owned / seen (and the owned numbers), ten story flags for badge 1 (`eyes/view.py` STORY_FLAGS: each name checked against the framework's flag table, each id against the decomp, each MEANING against the decomp script that sets it) | `get_item_bag`, `get_player`, `get_pokedex`, `get_event_flag` |
| `battle` | wild or trainer, double, the type flags, the opponent trainer id, both sides' active Pokemon (species, level, live types). The player's own: HP numbers, the HP bar, every move with PP. A FOE as a person sees it (step 1.1): the HP BAR only (filled pixels of 48, `hp` / `max_hp` None), only the moves it has USED this battle (PP below max: `ppreduce` follows "used MOVE!"), no PP; and only once it is THIS battle's (its PID is an occupied slot of `gEnemyParty`) | `get_battle_state` (`gBattleMons`), `gBattleTypeFlags`, `gTrainerBattleOpponent_A`, raw `gEnemyParty` headers |
| `last_battle_outcome` | `gBattleOutcome` (0 in a battle, the result after it) | raw |

**The window, derived and measured.** The decomp draws virtual-map metatile (j, i) at screen
(16 j, 16 i - 40) while the player stands on (7, 7) (`src/field_camera.c`: the BG scroll is the pixel
offset plus the camera pans 0 and 32, plus 8), so the screen shows dx -7..+7 and dy -5..+5 around the
player, the rows dy = -5 and +5 half (`eyes/view.py` has the derivation with its citations). Arm GEO
MEASURES it on four overworld fixtures: the player sprite's tile is drawn at screen (112, 72), the pans
are (0, 32), the columns -7..+7 and rows -5..+5 are on screen with -5 and +5 half visible; its control
(a battle fixture) does not give (112, 72). The game keeps objects alive up to dx -9..+10, dy -7..+9
(`TrySpawnObjectEvents`): those, hidden items and invisible objects are NOT in an Observation (§10.7).

**The action log and the scorer lines** (`memory_log.py`). Every look of the watcher is one JSON line
in `<run_dir>/actions.jsonl` (`frame`, `digest`, `decision`, `action`, `reason`, and the compact
Observation: each tile as `[x, y, metatile, behavior, collision, elevation, flags]`, about 10 KB a look).
The run's log gets the bot's own line formats, so `ai-agent/scoring.py` `parse_log` scores an AI run
like a bot run: `[AI-STARTER] Story: choosing X!` FIRST (observed when the last party READ was empty and
now has one Pokemon, or inferred at run start: the player's own starter-family Pokemon, else `Unknown`),
`[MAP] A -> B(g,n)` (written at the first SETTLED look on the new map), `[DEX] owned a -> b`,
`[TRAINER] end opp=N last_seen=Name#N ... res=... money=a->b`, `[AI-BATTLE] end kind=wild sp=Name#N
res=... [tutorial=wally] [player_catch=yes|none|unknown]`, `[CATCH] end ... sp=Name#N end=caught res=Caught
dest=party|box pid=XXXXXXXX`, and the `[hb]` heartbeat every 3600 frames plus one when the brain ends
(`end=1`, from the last look with a settled position and a read party), from which the scorer takes the
run's end map, position, party and length. A battle is one record from its first look with both sides,
REFRESHED by every later one (the lines name the foe of its last look), and ENDS only on a look out of
the battle whose `gBattleOutcome` is a result and whose party, boxes and money could be read: no line
ever says `res=InProgress` (the scorer counts every `res` but `Won` as a loss). A CATCH is logged only
for a NEW PID of the player's (visible OT id) in the party or a box, and `dest` is where that PID is:
`gBattleOutcome == Caught` alone is not a catch (Wally's tutorial ends Caught; the Ralts is his).

**Cost of a look** (measured 2026-10-07 in the round-2 run whose evidence is on disk,
`evidence/2026-10-07-step1-*.txt`, with the learner's 16 lanes running alongside): in-process (the probe),
30 looks per fixture, one per frame: overworld medians 1.38 to 1.59 ms (means 1.39 to 1.60, worst look
1.85 ms), a battle or a full-screen menu (no view to read) medians 0.70 to 0.79 ms (worst 1.21 ms). In the
live runs, under the purity instrument, 10 looks each: overworld medians 1.54 to 1.76 ms, battle and menu
medians 0.82 to 0.91 ms, worst look 2.40 ms. The first look of a run also reads the ROM tables it keeps
(tilesets, tile flags, the map's events) and is usually the slowest. The numbers move with the machine's
load: the step-1 verifier's own re-run measured an overworld median of 1.95 ms and a worst look of
2.96 ms (E8). Reading all 32 text printers (1152 bytes) instead of one changed none of this measurably.
Step 1.1 (the PC boxes, the VBlank check, the enemy party's PIDs) in its live run, 10 looks each: overworld
medians 1.59 to 1.99 ms (worst 2.57 ms), battle and menu medians 0.87 to 1.06 ms (worst 1.67 ms).

**Proofs.** (Step 1.1's own are in the section "Step 1.1" below.) `gates/test_eyes.py` (32 unit tests in step 1: the framework-free files import neither the framework
nor the host side; the window's edges; the behaviour table against the decomp's values and the
framework's own table; the party decoder against the framework's table and decoder for all 24
substructure orders, with a swapped-row fault; every flag name, and every flag id equal in the
framework's table and the decomp, with a wrong-id fault; the probe's charmap and the item-name
comparison; the wait rule against the decomp's render states, with the pre-fix rule and the
printer-0-only rule as faults; the scorer reading the AI's lines, with two format faults).
`gates/live_step1.py` (15 arms, evidence `evidence/<date>-step1-<ARM>.txt`): ten fixtures (a town, two
routes with tall grass and an item ball off / on screen, a wild and a trainer battle, a trainer's DEFEAT
text, an open text box, a party menu, a map edge, the League lobby's full bag) through the real launcher
with the watcher; the first look against `gates/probe_eyes.py`'s ground truth on the SAME frame (asserted
in every arm), each fact by a SECOND PATH, never the eyes' bytes and code:

| fact | the truth the arms compare with |
|---|---|
| map | (group, number): the live header byte-identical to one header of the ROM's `gMapGroups`, walked by the probe; NAME: the ROM header's region-map section -> `gRegionMapEntries`, decoded by the probe's own charmap (the decomp's `charmap.txt`) |
| position | save block 1 `pos` |
| facing | on the overworld (6 fixtures), what is DRAWN: the player sprite's `animNum` (ANIM_STD order) and its OAM hFlip (only the east frame is flipped). In a battle or a full-screen menu the overworld sprites are freed and the game keeps no second copy: those lines say CONSISTENCY ONLY |
| in battle | `gMain.inBattle` (a bit the eyes do not read) |
| party | the framework's `get_party()` (its own decryption): species, level, HP, PID, every move with PP and max PP, the status (138 moves over the ten party fixtures, 25 of them with PP used; one status other than ok, E7's paralysed Skitty); and the raw level byte |
| battle sides | the SECOND COPY the game keeps: the party struct with the battler's PID (`gPlayerParty` / `gEnemyParty`, the framework's decryption: species, level, HP, max HP, status, moves with PP and max PP) and the species table's types. The probe's raw `gBattleMons` parse is the same bytes as the eyes, so its line says CONSISTENCY ONLY |
| trainer id | the trainer who STARTED the battle, without `gTrainerBattleOpponent_A`: `gSpecialVar_LastTalked` -> the map's ROM object template -> its script's `trainerbattle` argument (`Route116_EventScript_Joey`: 322); the ROM's `gTrainers[322]` is JOEY with the live enemy party, the only one of 855 with it; the decomp's `TRAINER_JOEY 322` |
| text box | `Task_DrawFieldMessage` in the probe's own task parse (the eyes read the box's mode byte) |
| waits for a button | BEHAVIOUR, in the probe's throwaway emulator, the eyes looking at EVERY frame: text on screen, 300 frames with no input move nothing, one A press moves that text. Before and after the press, every frame on which a text PRINTS by itself must read waits=False, every idle frame from which the screen sits still until the press (which then moves that text) waits=True, and after the press every frame a text then sits still for 30 frames waits=True. Measured: 301 waiting idle frames in each battle and the text box (E4, E5, E6, E10), 200 on the party menu's printer 6 (E7), 26 printing frames before the press (E7) and 10 to 46 after it (E1, E4, E5, E6, E10), 88 to 160 still frames after it (E1, E6, E10). E2, E3, E8, E9 have no text, and E7 none after the press |
| the defeat text | E10: printer 0 in state 1 with the two bytes it consumed last FC 09 (EXT_CTRL_CODE_PAUSE_UNTIL_PRESS) and its buffer reading Joey's defeat text from the decomp's `data/text/trainers.inc`; the fixture's build printout shows it was PLAYED (22 button presses from E5's fixture) |
| menu | `gPartyMenu.menuType` = 1 (in battle) and the named `gMain.callback2` |
| objects | a raw `gObjectEvents` parse with the probe's own window test, and WHAT IS DRAWN: each object's sprite on screen relative to the player's (E1, E2, E3, E6, E8, E9: every still object drawn on its coordinates; the objects the eyes see are exactly those drawn inside the window; E2's item ball is drawn at screen x 240, past the right edge) |
| the map-header check | its fault arm: another map's ROM header written over `gMapHeader` in the probe's emulator is refused (every arm with a probe) |
| `gTextFlags` bit order | in a battle the byte is 0x03 (E4, E5, E10): the bit-fields run from bit 0, so autoScroll is bit 2 as the eyes assume |
| tiles | the ROM layout, tileset attributes and warps decoded by the probe (metatile, behaviour, collision, elevation, warp) and the framework's `MapLocation` (encounters, water, tall grass; ledges and doors by the FRAMEWORK's behaviour names), across a connected edge too; ledges (8), doors and warps in the window |
| money, badges, story flags, Pokedex | the probe's decode of the save blocks: money XOR the key; flag bits at the decomp's ids; owned / seen by the game's own rule over the three seen copies |
| balls, healing items | the bag pockets decoded by the probe, names from the ROM's `gItems`, "healing" = the ROM's use function is `ItemUseOutOfBattle_Medicine` / `ItemUseInBattle_Medicine` (E9: 7 healing items and 5 others) |

plus each fixture's documentation; the crop (an item ball the game holds at dx = +8 is absent, the
trainer at dx = +1 present) and its FAULT arm (with `AI_PLAYER_FAULT_NO_CROP=1` the ball appears); a
CONTROL on every tile check (the window shifted one column mismatches); arm XW, the waits fix REVERTED in
copies of the package (the pre-fix states {2, 3}: caught on E10 and E7; printer 0 only: caught on E7,
passes on E10; the unchanged copy passes both); arm XG, the fault half of the truth checks: 36 copies of
graded arms with ONE value made wrong, on the eyes' side or on the TRUTH's side (the sprite, a flag bit, a
ROM tile, the script's trainer, the behaviour, the task list, the menu type, the probe's frame, a second
copy's HP and PP, an object's drawn position, the header check, `gTextFlags`, the defeat text's bytes),
each caught by its own check while the unchanged copy passes; the scorer on a real run; every run CLEAN
with `ai_presses=0` and `ai_bot_calls=0`.

**The eyes missed a wait, and the verifier found it from the decomp.** Until round 2 "waits for a button"
read only `sTextPrinters[0]` in states 2 and 3 (the down arrow). The decomp has a third waiting state,
RENDER_STATE_WAIT = 1 (`include/text.h`), which `{PAUSE_UNTIL_PRESS}` enters (`src/text.c`) and which
`src/battle_message.c` appends to every trainer's lose and win text and to the whiteout text: so after
every trainer v1 beats, Roxanne included, the eyes said "not waiting" while the game waited for A. The
first natural capture was then found in a fixture already graded: the party menu's "SKITTY is already in
battle!" waits in state 1 on PRINTER 6, which the eyes did not read at all. The rule now reads all 32
printers and states 1, 2, 3 (`eyes/view.py` `text_printer_wait`), proven on E10 (a trainer's defeat text,
made by playing E5's battle to its end) and E7, each half of the fix failing on revert (arm XW).

**A story flag was wrong, and the second path found it.** The Ch2 flag was `THANKED_FOR_PLAYING_WITH_WALLY`
("Wally's catching tutorial done"); the decomp sets it only when the player talks to Wally's DAD in
Wally's house, an optional chat, so it read False on every fixture, six badges included (this project's
ML-9, repeated). The tutorial sets only variables (`VAR_PETALBURG_CITY_STATE` 2 -> 3); its scene's one
flag, `HIDE_PETALBURG_CITY_WALLYS_MOM` (set in `PetalburgCity_Gym_EventScript_BeginWallyTutorial`), replaced
it, and every entry of `STORY_FLAGS` now names the decomp script that sets it.

## Step 1.1: the step-1 review's findings, fixed (2026-10-07)

Each fix has a unit test in `gates/test_eyes.py` that FAILS when the fix is reverted (`gates/revert_step11.py`
reverts each in a copy of the package: 13 of 13 caught, the unchanged copy passes all 55 tests; R4x and R4y,
added after the step-2 verifier's mutant V4, compare ONE coordinate each: the measured warp differs in x only,
so `SettlingTests.test_the_rule` now also has a y-only and a both-differ case), and the
host-side ones a live arm in `gates/live_step1.py` that PLAYS the case in the probe's throwaway emulator with
the eyes looking at every frame (`gates/probe_step11.py`), each with its own revert copy. Evidence:
`evidence/2026-10-07-step11-*.txt`.

| finding | the fix | proven by |
|---|---|---|
| 1 Wally's tutorial logged a player `[CATCH]` | a catch only for a NEW PID whose OT is the player's VISIBLE id, in the party or a PC box (the eyes now read the boxes, `storage`); `gBattleOutcome == Caught` alone is not one: `BattleScript_WallyBallThrow` sets it with no `givecaughtmon` | `CatchTests` (R1); BLW: a real catch through the bag and the nickname screen writes `[CATCH] ... dest=party pid=7D6D2751`, the foe's PID, which the framework's party then holds; `PC BOXES` in every arm (E3: 2 Pokemon) |
| 2 battle lines: a stale foe at the start, `res=InProgress` | the record is REFRESHED by every in-battle look; it ends only on a result, on a readable look; and the eyes report a foe battler only if its PID is a Pokemon of `gEnemyParty` | `BattleLineTests` (R2a, R2b); BS: for 9 frames of a new battle `gBattleMons` held the previous battle's Abra while the foe was Poochyena: the eyes report no foe there, the line says `sp=Poochyena#261`; the step-1 code in a copy (BS-X2) writes `sp=Abra#63`; BLT: `[TRAINER] end opp=322 ... res=Won money=6680->6824 delta=144`, the game's own "got ₽144" |
| 3 perception like a person | the foe's HP is the 48-pixel HP BAR (`hp`, `max_hp` None), its moves only those USED (PP below max), no PP; every person is an "npc"; the player's id and every OT id are the VISIBLE 16 bits | `PerceptionTests` (R3a-R3d); E4/E5/E10 against the second copy (bar by the decomp's GetScaledHPFraction); E10 against the battle's own texts, replayed ("Foe MACHOP used FOCUS ENERGY!", "... LEER!"); E2: Joey (raw trainerType 1) is an "npc", and the step-1 label in a copy (E2-X) calls him "trainer"; every arm: the full 32-bit id in no record |
| 4 warp staleness | the position is reported only when the player object's tile (- 7) equals save block 1's `pos`; otherwise `settling`, no position, no view; the `[MAP]` line waits for the settled position | `SettlingTests` (R4; R4x, R4y: one coordinate compared); WARP: 6 frames of Dewford's door warp mixed map (3,5) with tile (8,8): the eyes say settling (2 frames) or between screens (4) there, and on all 689 of 700 frames where they report a position it is the save block's pos on the map the live header is; the step-1 position in a copy (WARP-X) writes `[MAP] ... -> DEWFORD TOWN(3,5) pos=(8, 8)` |
| 5 party None vs (), dest by count | `party` None = not read (a torn slot makes the whole party None), () = no Pokemon; the starter is "observed" only after an empty party was READ; `dest` is where the new PID is | `PartyNoneTests`, `CatchTests` (R5a, R5b) |
| 6 the script's waitbuttonpress, untested | `eyes/view.py` script_waits_for_button, captured live | `ScriptWaitTests` (R6); SW: Dewford's sign ends in the script's waitbuttonpress (no printer active, the box mode already hidden): 300 idle frames move nothing, waits=True on all; one A ends it; the fixture's first frame (a finished script, status 2, mode Stopped, WaitForAorBPress left behind) reads False. Reverts: both checks removed (SW-X1) caught; each alone (SW-R1, SW-R2) NOT caught (each is redundant alone); the branch removed (SW-X2) caught |

**Found by the new live arms, and fixed:** (a) the stale foe in the Observation itself (above, BS);
(b) the SAVE BLOCKS MOVE between frames: `MoveSaveBlocks_ResetHeap` (every battle start and every map load)
copies both save blocks and the PC boxes out and back with `gMain.vblankCallback` NULL, and the copy spans a
frame boundary: at a trainer battle's end, on the frame the pointers moved, the Pokedex's third copy was
half restored and the eyes read 0 owned (`[DEX] owned 5 -> 0`, then `0 -> 5`). While the VBlank callback is
NULL the eyes now withhold the player, the boxes, the bag and the progress (a problem says so); BLT's revert
copy (BLT-X) writes the drop again.

## Known limits of step 1.1

* Wally's tutorial itself was not played live (no save stands before it; reaching it means the walk to
  Petalburg and Norman's scene): the rule is proven on a synthetic run and on a real catch (BLW), and the
  decomp's `BattleScript_WallyBallThrow` is the reason.
* No look out of the battle before its result was found in the game: on the nickname screen `in_battle`
  stays True (`gMain.callback1` is still BattleMainCB1) and the result is set before `in_battle` reads
  False (BLW). The "end only on a result" rule is a guarantee, unit-tested only.
* The catch arm's RNG: delay 1 catches (the third ball), delay 0 misses with all five: one trajectory,
  replayed (rule 8), not a catch rate.
* "Between screens" withholds about 15 frames around a battle's start and end, more than the move itself
  (other transition frames NULL the callback too). The re-encryption after the move
  (`ApplyNewEncryptionKeyToAllEncryptedData`, then the new key) runs with the callback restored; a frame
  boundary inside it would mis-decode money and bag quantities for a frame. Not seen; not guarded.
* At the script's `waitbuttonpress` the box is still on screen, but its mode is already HIDDEN, so `screen`
  reads `overworld` and `text_box_open` False there; `waits_for_button` (the one an A press is gated on)
  is True.
* A foe move is "seen" when its PP is below its maximum: a two-turn move's charging turn and a Focus
  Punch that lost focus take PP with their own message, Struggle takes none, and a Leppa Berry that
  restores PP hides the move again.
* The PC boxes are read every look (33,600 bytes, no decryption); a box Pokemon's species is not decoded.
* Step 2.1 closed the gap "no live warp that differs in y only": arm WARPY plays the League's escalator (tiles
  (1, 7) and (1, 6), x equal), and the x-only rule (R4x) is caught there live while it is NOT caught on WARP's
  Dewford door. On 13 of WARPY's 15 mixed frames the eyes withhold the player as "between screens" (the VBlank
  callback is NULL); the settling rule itself decides the other 2, which is where the mutants show.

## Known limits of step 1

* The watcher looks every N frames (60 in the proofs): anything shorter than N frames can be missed, and
  a change is logged at the look that sees it. A look costs ~10 KB of action log: an hour of game time
  watched every 60 frames is ~36 MB. On a fresh boot the first look is at frame 0, before the game has
  run a frame: it reports that as its one problem and sees nothing (the framework's caches are empty).
* (Resolved in step 1.1: the foe's exact HP and its moves were reported; now the HP bar and the moves used.)
* The window is the standing-still one: the partial 16th column / 12th row while the camera scrolls a
  step is not modelled. Objects on the half-visible rows are reported. "Signs" are a map's interactable
  tiles (signposts, PCs, bookshelves, a few invisible triggers), not only signposts.
* Menus are named only for the start menu, yes/no, multichoice and the whole-screen states; list menus
  (mart, PC item lists) and the battle's own menus are not named yet. `waits_for_button` covers a script
  waiting for A/B and every text printer in a waiting state; a wait that is a TASK polling the buttons
  with no text printer waiting (the level-up stats box, a menu's cursor) is not a "waits for a button"
  here (a menu is named in `menu` instead). The autoScroll branch (no wait under `gTextFlags.autoScroll`:
  `messageautoscroll` scripts, link and recorded battles) is unit-tested only: no fixture sets it. The
  whiteout text's state-1 wait is the decomp's (`sText_PlayerWhiteout2`), not a capture: no fixture stops
  there (`ki90_whiteout_at_evergrande.ss1` showed no text in 4000 idle frames: the step-1 verifier's probe).
* The behaviour test that classifies a frame as PRINTING or WAITING is behavioural, not exhaustive: a
  text in RENDER_STATE_PAUSE for 30 frames or more after the press would read as "still" (none occurs in
  the fixtures; before the press the stricter rule "still until the press, which then moves it" applies).
* Battle statuses are graded only as `ok` (no battle fixture holds a status); the party status is graded
  on E7's paralysed Skitty. Objects mid-step are checked only to lie within one tile of their coordinates,
  and are left out of the "crop by what is drawn" check (none occurred in the fixtures).
* Facing has no second copy during a battle or a full-screen menu (the overworld sprites are freed);
  there the arms check it only for consistency (the same byte, decoded by test code), and say so. The
  map NAME's truth is the same ROM string the framework decodes, read through the ROM table and decoded
  by the probe's own charmap: a second decoder, not a second copy. Money and the bag's quantities have no
  second copy in the game either: their truth is the probe's own decoder of the same save-block bytes.
* The map-header check compares the live `gMapHeader` with the ROM header from byte 4 on: the layout
  pointer (bytes 0-3) is re-pointed at load and may differ from the ROM's (`setmaplayoutindex`). It runs
  once per map the eyes meet (the facts are kept), so a header that goes stale LATER is not re-checked.
* The behaviour test that grades `waits_for_button` presses A in the probe's own emulator, so it shows
  what one press does from the fixture's frame, not what the watcher run saw later (the watcher presses
  nothing, and its looks stay on the frozen screen).
* Out-of-map tiles were verified only across a connected edge (arm E8, 22 tiles); corner tiles and an
  edge without a connection are reported as the live grid holds them, unverified. A warp of the NEXT
  map visible across an edge is not marked `warp` (the eyes know the current map's warps only; its door
  behaviour is still marked `door`).
* Healing items were checked on two bags (E3: 1 healing and 1 other; E9: 7 and 5); no fixture holds
  berries, so the berry pocket's classification is unmeasured.
* A run started from a SAVE scores only what happens IN the run, exactly like a bot run: the scorer
  takes the Pokedex from `[DEX]` lines (written on a change, as the bot's `debug_logger.py` does), badges
  from leader wins and money from trainer-battle ends, so a watcher run on a save scores dex 0, no
  badges and no money (arm SC and E1 assert this PARITY and quote the bot's line). A New Game run, v1's
  case, starts at 0 anyway.
* The framework readers the eyes call memoise into the framework's per-frame Python cache
  (`state_cache`); nothing in the game changes. What the eyes do with a framework object's attributes is
  not tracked statically (a value, rule a's limit); the live audit counts any write, press, load, frame or
  bot code it could cause, and was 0 in every step-1 run.

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
