# ai_player: the Emerald AI that plays the game itself

`ai_player` is a program that plays Pokemon Emerald **with its own code**: walking, exploring,
battling, menus and decisions (USER RULING 35). The story bot is only its teacher; no bot code runs in
its play loop. It reads the game by memory injection and presses the buttons itself (RULING 36).
It is built to become a **single standalone program** that loads the ROM itself and can run
unattended as an art piece (RULING 37 Q1), so everything framework-specific sits behind thin
adapters in `platform/`, and no path to the bot is hard-coded.

Design: `PROJECT KNOWLEDGE/ai-research-notes/2026-10-07-ai-player-v1-DESIGN-DRAFT.md` (sections 10
and 11 win over 2-9) and `ai-agent/HUMAN-PLAY-DESIGN.md`.

**Where it is now: build step 0, purity scaffolding.** The brain is a placeholder that presses nothing,
waits `--frames` frames and gives up with reason `step0-placeholder`. What step 0 delivers is the
boundary every later step stands on: listener isolation, action attribution with a sink audit and a
bot-code monitor, a verdict file only the instrument can write, a lifecycle that can never park, and
two gates (static and live) that were each broken by independent verifiers and then fixed.

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
  from an existing profile, writes `http.yml` with the HTTP server off, and a `.ai_player_profile`
  marker (as `tools/story-dev/x4_headless.py` `ensure_lane_profile` does for lanes);
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
  kills the whole process tree at `--wall-seconds` (exit 124) and prints `[AI-RUN] NO PURITY VERDICT`;
* **grades the run from the verdict file**: reads `<run_dir>/purity.json` (written by the instrument,
  see below) and prints `[AI-RUN] verdict file: verdict=... exit_reason=... exit_code=...`. It exits
  with the child's exit code, except that a child exiting 0 without a CLEAN verdict file for the gated
  package makes it exit 8.

Options travel to the mode as environment variables (`ai_player/options.py`): `AI_PLAYER_FRAMES`,
`AI_PLAYER_RUN_DIR` (the run's `ai_player.log` and `purity.json` land there),
`AI_PLAYER_PACKAGE_ROOT` (the hook moves it to the FRONT of `sys.path`), `AI_PLAYER_WALL_DEADLINE`.
`--build-root` / `AI_PLAYER_BUILD_ROOT` points at a different framework folder.

## Layout

| file | what it is for |
|---|---|
| `mode.py` | the AI's mode logic: the session, the guard callback, the (placeholder) brain |
| `platform/controller.py` | the ONLY place the AI presses buttons or lets frames pass |
| `platform/isolation.py` | removes every framework listener the AI does not own; restores them on exit |
| `platform/attribution.py` | the instrument: counts inputs, writes, loads, frames and bot-code calls by origin, audits the sinks, writes the verdict file |
| `platform/lifecycle.py` | the single exit door; exit codes |
| `platform/launcher.py` | the CLI side (launcher process): the gate, the profile, the child process, the wall clocks, the verdict file |
| `options.py`, `runlog.py` | run options from the environment; the AI's own log |
| `gates/` | TEST SIDE: the purity gate, its fault tests, the live proof driver, a state inspector |
| `../sandbox-pokebot/plugins/custom_modes/ai_player_mode.py` | the hook: registers "AI Player", puts the package first on the path, no logic |

## The purity contract

1. **No bot code in the play loop, checked statically** (`gates/check_purity.py`, an AST walk that is
   an allowlist all the way down, the standard library included):
   * (a) framework imports only through listed DOORS, per file, and only along the attribute paths
     each door lists (the controller may use `context.emulator.press_button/hold_button/release_button`
     and nothing else); standard-library modules only from a list, each used ONLY as
     `module.<attribute>` with the attribute on its SURFACE (explicit for `sys`, `os`, `pathlib`,
     `traceback`, ...; otherwise a public attribute that is not a module, not reflective and not from
     `operator`/`inspect`/`importlib`/`sys`, judged against this Python); imports between AI modules
     only of names their `__all__` lists and defines, from files the gate read; the bot's brain
     refused as a backstop;
   * (b) no name that writes memory, loads or resets the emulator, or advances frames; button names
     only in `platform/controller.py`; `match` class-pattern attributes and `getattr` constants count;
   * (c) the play loop imports neither the test side nor the launcher side; the launcher side does
     not import the framework;
   * (d) no reflection: `__import__`, `exec`, `eval`, `vars`, `setattr`, `getattr` with a name chosen
     at run time, private attributes of other objects, dunders, import-system / tracing / frame
     attributes, `str.format` with attribute or index fields;
   * (e) the files the import system can load are the files the gate read: source parsed from its
     bytes (coding cookies honored), no bytecode or extension modules, no links, nothing but genuine
     cache files in `__pycache__`, and every cache file CPython would load instead of its source
     proven to hold exactly that source's code;
   * (f) only `runlog.py` and the instrument write files; nothing assigns to, or deletes, an attribute
     or item of anything it imported (a shared library, a framework object, another AI module's class);
   * (g) each platform adapter's `__all__` is pinned in the gate, the instrument's bytes are pinned
     by sha256 (`--instrument-digest`, after a review), its run-time bot-code list must cover every
     module the backstop refuses, and only the lifecycle may name its finalizers.
   The instrument (`platform/attribution.py`) is exempt from (b), (d) and (f) only, because it has to
   wrap those very functions; that is why its bytes are pinned.
2. **No framework listener plays for the AI.** On entry the mode removes every listener it does not
   own (it owns one: its `GuardListener`) and restores the framework's exact list on exit. This
   happens in the hook's constructor, before the framework's first listener pass. If the guard is
   ever removed, it is put back and counted as tampering.
3. **Measured in every run, at the doors, at the sinks, and in the bot's own code.** The doors count
   every call to the framework's input, write, load and frame functions by origin. The sinks catch what
   no door saw: keys latched with no counted press (`unattributed_inputs`), WRAM/IWRAM changed between
   frames (`unattributed_state_changes`), frames outside the main loop (`extra_frames`), a removed
   wrapper or a new core callback (`instrument_tampered`). A `sys.monitoring` hook counts every
   function of the bot's decision code that starts while AI code is on the stack (`ai_bot_calls`):
   bot code that only COMPUTES (the pathfinder) leaves nothing at the doors or sinks.
4. **The verdict is a file, not a line.** At the end, the lifecycle's `finish` (and only it: the
   instrument refuses any other caller and counts it as tampering) has the instrument write
   `<run_dir>/purity.json` from its own counters: verdict, counters, origins, exit reason and code,
   the isolation descriptions, the package that ran. The counters are read-only outside the
   instrument, its classes are sealed and slotted, and the `run_frame` wrapper stays on as a
   tripwire: a real frame after the verdict (someone caught the lifecycle's SystemExit and played on)
   rewrites the file as BREACH (`ran_after_finish`) and ends the process. The printed
   `[AI-PURITY] ... verdict=CLEAN|BREACH|UNVERIFIED` line is for people; any code can print one.
5. **Never parks.** Every ending is `[AI-EXIT] reason=... code=N`, a verdict file and the process
   exiting: 0 clean give-up; 2 crash (or a stray `SystemExit` from the brain); 3 parked/abandoned/
   restarted by the framework; 4 frame budget; 5 the brain returned without giving up; 6 purity
   breach or unverified (also `ran-after-finish`); 124 wall clock. The launcher adds 7 (the gate
   refused the package) and 8 (exit 0 without a CLEAN verdict file).

```
py -3.12 ai_player/gates/check_purity.py          # static gate (exit 0 = PASS)
py -3.12 ai_player/gates/test_check_purity.py     # its fault tests (both verifiers' probes, verbatim)
py -3.12 ai_player/gates/live_step0.py            # live proof, 27 arms, about 4 minutes
```

## Fault and control switches

Read inside the AI's own code, never set on the happy path:

| variable | effect | the arm that uses it |
|---|---|---|
| `AI_PLAYER_FAULT_KEEP_LISTENERS=1` | skip listener removal | B (battle fixture), W (cheats plugin on) |
| `AI_PLAYER_FAULT_RAISE=1` | the brain raises after 30 steps | C |
| `AI_PLAYER_FAULT_MANUAL=1` | a listener raises; `main.py` switches to Manual | M |
| `AI_PLAYER_FAULT_HANG=1` | the brain blocks the main thread (bounded at 300 s) | T2 (hard wall clock) |
| `AI_PLAYER_CONTROL_TAP=1` | CONTROL: the placeholder taps B every 60 steps | P |

A forbidden action cannot be a switch in the real package (the static gate would rightly fail it), so
the PLANT arms copy the package to a temporary folder, add a `_plant.py` that does one forbidden thing
from inside the brain, and run that copy through the real launcher (with `--allow-ungated`) and hook.
Each must fail the static gate AND be caught live: `XP`, `XH` (inputs through no door), `XM`, `XN`
(memory through no door), `XL`, `XS` (loads), `XF` (an extra frame), `XT` (a callback inside the
frame), `XB` (the bot's pathfinder run from the brain), `XG` (a press found by a frame walk), `XK` (a
breach, then five attempts to hide it). `XE`, `XY`, `XZ` attack the evidence instead (a fake
lifecycle printing a forged CLEAN verdict, a stray `SystemExit`, catching the lifecycle's own exit),
and `XR` proves the launcher refuses an ungated package. `XO` is the do-nothing control.

Evidence of the live proof: `ai_player/evidence/<date>-step0-<ARM>.txt`.

## Known limits of step 0

* Static analysis cannot see values: a name bound by ASSIGNMENT is not tracked (`cls = type(obj)`
  then `cls.x = 1` is not refused). The classes the verdict depends on are sealed at run time, and
  the verdict is a file only the instrument writes; any other class the AI changes is its own.
* The library surfaces are computed from the running Python's standard library: run the gate with
  the bot's Python (3.12). The gate trusts the interpreter, the standard library, site-packages and
  the framework's own code; it judges only which framework code the AI may reach.
* Bot DATA read without running bot code (a constant table) is refused only statically.
* The live audit cannot see a native change to ONLY the CPU or I/O registers, video memory or the
  cartridge save. Every route to the emulator core the two verifiers found is refused statically;
  that is a list of known routes, not a proof that none other exists.
* A run killed by the HARD wall clock has no verdict file; the launcher says so.
* After an emulator RESET the framework rebuilds its listener list; for that one frame its listeners
  run before the AI re-isolates. Step 0 never resets, and any action in that frame is still counted.
* Selecting "AI Player" by hand in a GUI works, but the AI's give-up then ends that bot process (by
  design: an AI run never parks), and without a run directory there is no verdict file.
* Never put the `ai_player/` folder itself on `sys.path`: its `platform` subpackage would shadow the
  standard library's `platform`. The repo root goes on the path.
