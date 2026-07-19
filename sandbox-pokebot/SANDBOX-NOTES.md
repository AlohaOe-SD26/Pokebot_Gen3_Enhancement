# Sandbox Notes — changes vs custom-pokebot
> APPEND-ONLY. Every sandbox-vs-custom difference gets an entry here (this
> is the promotion checklist when the user approves a feature).

---

## 2026-07-18 — A1: Backup & Restore system
- **Added** `modules/backup_manager.py`: backup manager (a module of
  functions, not a class) — zips a profile's
  valuable data (saves, savestates, stats.db, configs; screenshots/logs
  excluded) to `backups/<profile>/<timestamp>_<reason>.zip` with retention
  pruning (default 10). Cloud backends (opt-in via `backup.yml`):
  `github` (copies newest zip to repo-root `cloud-backups/<profile>/`,
  prunes to 3, stages ONLY that path, commits + pushes — all failures
  non-fatal) and `synced_folder` (mirrors to any OneDrive/Dropbox/GDrive
  dir with its own retention). `restore_backup()` extracts into a NEW
  profile only (live profiles are never overwritten; zip-slip guarded;
  half-restores cleaned up). Hybrid logging to `logs/backup.log`.
- **Added** `plugins/backup_plugin.py`: auto-backup on every logged shiny
  (`auto_on_shiny`) + a frame listener doing timed backups every
  `interval_hours` (checks once per ~3600 frames; cheap).
- **Added** `backup.yml` (root, tracked): commented config template;
  per-profile `profiles/<name>/backup.yml` overrides it whole-file.
- **Modified** `modules/gui/dashboard_gui.py`: "BACKUPS" card in the tool
  column (last-backup age label refreshed with the KPI cycle, "Back up
  now", "Restore…" Toplevel that lists local+cloud backups and restores
  into a new profile name); backup events surface in the event log.
- **Modified** `.gitignore`: negation for the plugin (ML-2), `backups/`
  ignored (user data). Repo-root `cloud-backups/` is deliberately tracked.
- **Verified**: headless test battery (archive contents, retention,
  hash-identical restore, refusal paths, malformed/override configs,
  synced-folder backend, disabled mode) all PASS — note: originally
  13 checks of which one ("restore refuses existing profile") was a
  tautology; corrected and greatly extended in the adversarial review
  below; real GitHub cloud backup
  committed+pushed containing only `cloud-backups/…` (commit `38a0e207`,
  left in the repo as a demo); live GUI run screenshot-confirmed the card.
- **Not verified**: shiny-triggered backup end-to-end (needs a real shiny
  encounter); timed backup over hours (logic unit-reviewed only).

## 2026-07-18 — A2: Macro record & replay system
- **Added** `modules/macros.py`: macro engine — MacroStep/Macro dataclasses,
  run-length encoding of per-frame input bitfields (leading/trailing idle
  trimmed), human-editable YAML files in `profiles/<name>/macros/` (with a
  commented format header), friendly validation errors (`MacroError`),
  GUI-written replay selection in `macros/_selected.yml`, and a module-
  singleton `MacroRecorder` + frame listener that samples
  `context.emulator.get_inputs()` while armed.
- **Added** `plugins/macro_plugin.py`: registers the recorder listener.
- **Added** `plugins/custom_modes/macro_player.py`: "Macro (Custom)" bot
  mode — frame-accurate replay via `hold_button(inputs=…)`/`release_button`
  per step; loop or once; battles interrupt (default shiny/catch pipeline
  stays active) → loop mode restarts the macro from step 1, once mode
  stops to Manual. Held buttons are always released via try/finally.
- **Modified** `modules/gui/dashboard_gui.py`: compact one-row "MACROS"
  card (● Rec toggle with red recording indicator + name prompt on stop,
  macro dropdown, Loop checkbox, ▶ play → writes selection + switches to
  the Macro mode). Card placed directly under CONTROLS, and the default
  window height raised 720→860 (clamped to screen) after the A1 review
  note about column clipping — on very high DPI-scaled screens the column
  can still clip at the bottom; a scrollable tool column is a candidate
  for A4.
- **Modified** `.gitignore`: negation for `plugins/macro_plugin.py` (ML-2).
- **Verified**: py_compile; real-import discovery (both "Macro (Custom)"
  and "Patrol (Custom)" register; listener registers); headless battery —
  RLE (incl. idle trimming), YAML round-trip, listing skips `_selected`,
  selection round-trip, 6 malformed-file rejections, bitfield mapping,
  recorder empty→None; live GUI screenshot confirms the MACROS card
  renders under CONTROLS.
- **Not verified**: a real record→replay cycle against the game (test save
  sits at the title screen; needs hands-on play), battle-interruption
  behaviour in the wild.

## 2026-07-18 — A3: Patrol v2 — multi-map routes
- **Modified** `plugins/custom_modes/patrol.py`: `patrol.yml` waypoints now
  accept `- [x, y]` (current map, backward compatible) OR
  `- {map: [group, number], at: [x, y]}`; both validated with friendly
  errors (exact-key check, int-pair check incl. bool rejection). `run()`
  navigates per-waypoint to the explicit map or the mode's starting map.
  Docstring/config example updated (incl. the warp limitation note).
- **Verified**: py_compile + discovery; parse semantics test (mixed
  old/new formats accepted; 5 malformed variants rejected).
- **Not verified**: live multi-map walk (needs a progressed save).
## 2026-07-18 — A4: GUI pack + round verification
- **Modified** `modules/gui/dashboard_gui.py`:
  - Scrollable tool column: all cards now live inside a Canvas-hosted frame
    with a slim scrollbar; mousewheel scrolls whenever the pointer is over
    the column (the event log Listbox keeps its own scrolling). Fixes the
    clipping both A1 and A2 hit at small heights / high DPI; works in the
    handheld drawer too (same widget).
  - Party sprites: 32px pixel-art sprite per party row via upstream
    `modules/sprites.get_sprite()` (shiny/anti-shiny/Unown handled by
    upstream; eggs use `sprites/pokemon/Egg.png`); PhotoImages cached.
  - New SHINY LOG card: last 5 shiny phases ("✨ species — N enc") from
    `context.stats.get_shiny_log()`, refreshed on the KPI cycle.
  - Card order is now Controls, Macros, Stats, Party, Shiny log, Backups,
    Status, Event log (interactive first, telemetry last); event log has a
    bounded height inside the scroll area.
- **Verification (round exit gate):** headless — sprite paths resolve for
  edge-case names (Mr. Mime, Nidoran♀, Farfetch’d, Unown, Egg), ≤32px
  PhotoImage loads, GUI/plugins/modes all real-import, both custom modes
  discovered; `install_sandbox.py --check-only` passes (8 critical files).
  Live — real WM_MOUSEWHEEL input scrolled the column in a deliberately
  shrunken window (bottom cards reachable), and F11 + H produced handheld
  fullscreen with the drawer (screenshots: a4_desktop / a4_scrolled /
  a4_handheld_drawer in the session scratchpad); bot closed cleanly.
- **Still untested (needs real gameplay):** party sprites with a live
  party, shiny log with real entries, shiny-triggered backup, macro
  record→replay cycle, multi-map patrol run.

## 2026-07-18 — Round verification (GUI slice): hardening + dialog semantics
- **Modified** `modules/gui/dashboard_gui.py` (adversarial review fixes):
  - Mousewheel `bind_all` now bound exactly once per process (a re-`enable()`
    would previously stack handlers → multiple scroll units per notch); the
    handler also bails when the screen is disabled.
  - `disable()` now destroys the video canvas and Pokéball overlay (children
    of the root window, previously leaked over the next screen) and clears
    all dead-widget references; `update()` early-returns when disabled.
  - The per-frame sidebar refresh is wrapped in try/except: a transient
    stats/party/memory read failure can no longer kill the emulator frame
    loop (traceback printed in --debug only).
  - Restore dialog: the restore action now surfaces ANY exception (corrupt
    zip, disk error) in the feedback label instead of dying silently in
    Tk's callback handler; feedback color resets correctly after a success.
  - Shiny-log formatting moved fully inside its try block.
- **Dialog-vs-emulation semantics measured live** (documented in the module
  docstring): the Restore dialog is non-modal — emulation continues while it
  is open (bot held 61 fps, backup age label kept updating, game progressed
  intro→title behind the dialog). The macro name prompt
  (`simpledialog.askstring`) is modal — `wait_window` runs a nested event
  loop inside the frame callback, so emulation PAUSES until it closes
  (process CPU: 0.69 s/4 s normally vs 0.02 s/4 s with the prompt open,
  0.80 s/4 s after cancel). Harmless by design: recording has already
  stopped before the prompt opens. Cancelling via Esc logs
  "Recording discarded" and saves nothing (verified twice).
- **Live gauntlet (test-dashboard profile, real ROM):** column scrolled to
  bottom via real WM_MOUSEWHEEL (Status + Event log reachable), Restore
  dialog opened (listed 2 local + 1 cloud backup) and closed, macro record
  armed → inputs captured in Manual (menu navigated) → Stop → name prompt →
  Esc cancel, F11 handheld fullscreen → H drawer (all cards present,
  drawer scrolls) → Esc closed drawer (Pokéball back) → Esc restored
  desktop layout (scroll position preserved), `dashboard_ui.json` persisted
  `handheld: false`, WM_CLOSE exited cleanly. Bonus: the 2-hour interval
  auto-backup fired live during the run (reason "auto" in backup.log).
- **Known cosmetic nit (not fixed):** the Tk menu bar stays visible in
  handheld fullscreen.

## 2026-07-18 — A2/A3 adversarial verification round (bugs found & fixed)
A second agent re-verified A2/A3 against the real main-loop semantics
(`modules/main.py` re-instantiates a bot mode whenever its controller stack
empties; `run_single_frame()` applies `pressed | held` once per frame).
Three real defects found and fixed:
- **FIXED — once mode replayed forever** (`plugins/custom_modes/macro_player.py`):
  `run()` simply `return`ed when a once-mode macro finished or was
  interrupted by a battle, so the main loop immediately re-instantiated the
  mode and replayed the macro from the start — "once" behaved like "loop".
  The A2 entry's claim "once mode stops to Manual" was FALSE until now.
  Fix: `context.set_manual_mode()` on both once-mode exit paths.
- **FIXED — recorder captured bot-generated inputs**
  (`modules/macros.py` MacroRecorderListener): while armed it sampled EVERY
  frame regardless of bot mode, so hitting ▶ Play (or any mode switch) mid-
  recording leaked bot inputs into the macro. Now only Manual-mode frames
  are sampled.
- **FIXED — macros named with a leading underscore became invisible**
  (`modules/macros.py` save_macro): `_foo` saved as `_foo.yml`, which
  `list_macros()` skips (underscore files are reserved for `_selected.yml`).
  Leading underscores are now stripped and names must contain a letter/digit
  (previously `---` passed the emptiness check).
- **Hardened — Patrol** (`plugins/custom_modes/patrol.py`): explicit waypoint
  maps are now validated against MapRSE/MapFRLG at parse time (a typo like
  `map: [9, 99]` previously surfaced as "Internal Bot Error" from deep in the
  pathfinder), and `is_selectable()` now also returns True when a
  `patrol.yml` exists (a multi-map route may start on an encounter-less map).
- Verified sound (no change needed): frame-count-exact replay (hold set
  before the step's first yield, release after its last — N frames means
  exactly N emulated frames); release-on-abort via try/finally incl.
  generator close on mode switch (plus main-loop `reset_held_buttons()`
  backstops on error/Manual); loop-mode battle interruption restarts from
  step 0 with the default battle pipeline intact (`on_battle_started`
  returns None; `isolate_inputs` suppresses the macro's held buttons during
  the battle handler); RLE encode/decode + YAML round-trip; `_selected.yml`
  lifecycle (missing/stale selections raise a friendly BotModeError);
  single-threaded GUI+main-loop means no recorder races. Note: recording
  samples `get_inputs()` (last frame's applied keys), a uniform 1-frame
  offset that cancels out in replay.
- **Verified**: both headless batteries pass (original A2/A3 battery + new
  adversarial battery driving the REAL `MacroPlayerMode.run()` /
  `PatrolMode` code: replay exactness, loop repetition, battle interrupt
  once/loop, release-on-close, Manual-only recording, name hygiene, real
  waypoint parsing incl. map `[0, 0]` truthiness and nonexistent-map
  rejection); py_compile + real-import discovery still green.
- GUI-side observations (dashboard_gui.py NOT modified this round): ▶ Play
  does not stop/warn about an armed recording (the listener fix makes this
  safe, but the recording stays armed and resumes if the user returns to
  Manual); saving a macro silently overwrites an existing one with the same
  name; stopping a looping macro requires switching to Manual (upstream
  behaviour: a mode change only takes effect once the current mode's
  generators finish).

## 2026-07-18 — A1 adversarial review: bugs found & fixed
Independent verification pass over the backup system. Extended the headless
battery to 31 checks (git staging isolation, zip-slip attack zips, poisoned
configs, name collisions, hostile profile names, listener exception safety,
wall-clock throttling). 9 of the new checks FAILED on the original code;
all 31 PASS after the fixes below. Files touched: `modules/backup_manager.py`,
`plugins/backup_plugin.py` (dashboard_gui.py NOT touched).
- **FIXED (serious)** GitHub backend: `git commit` committed the ENTIRE
  index — anything the user had staged elsewhere in the repo was silently
  swept into (and un-staged by) the backup commit. Now commits with the
  `-- cloud-backups` pathspec (staging was already path-limited); user's
  staged work is left intact (test-proven). Also: all git calls now have
  timeouts (a hung push no longer stalls the frame thread forever) and a
  missing git binary / timeout is a logged warning, not a crash.
- **FIXED** timed-backup listener: `handle_frame` had no exception guard —
  any unexpected error (e.g. `retention: ten` in backup.yml raised
  ValueError from `int()`) propagated into the frame loop, which kicks the
  bot into Manual mode and silently stops the hunt. Body is now fully
  wrapped; config ints/floats are coerced defensively everywhere.
- **FIXED** interval checks were frame-counted only (3600 frames = 1 min
  at 1x, but far less wall time when fast-forwarding): added a 60 s
  wall-clock floor between checks. `interval_hours` itself was and is
  honored in wall time (zip mtime), incl. across restarts.
- **FIXED** zip-slip guard used `str.startswith` — a member resolving to a
  SIBLING folder sharing a name prefix (`profiles/vicx` vs `profiles/vic`)
  passed the guard (Python's extractall sanitization was the only thing
  preventing actual escape). Now a proper path-containment check; unsafe
  archives are refused outright instead of silently restored sanitized.
- **FIXED** corrupt/unreadable archives raised `BadZipFile`/`OSError`
  which the GUI's `except ValueError` doesn't catch (unhandled Tk callback
  error). Now converted to readable `ValueError`s; half-restores still
  cleaned up.
- **FIXED** same-second backups with the same reason overwrote each other
  (zip opened with mode "w" on an identical timestamp name); now a `-N`
  suffix uniquifies.
- **FIXED** restore profile names: trailing-space names and Windows
  reserved device names (CON, AUX, COM1…) are now refused.
- **FIXED** `list_backups` could crash if a zip was pruned between glob
  and stat; per-file guard added.
- **Reported only (GUI, not edited):** "Back up now" runs on the Tk thread
  while the emulator thread keeps writing — a manual backup can catch a
  torn `.sav`/`stats.db` mid-write (the plugin-triggered backups run on the
  frame thread and don't have this race). The restore dialog's
  `except ValueError` is now sufficient thanks to the error-conversion fix.
- **Docs corrected** in the A1 entry above: there is no `BackupManager`
  class (module of functions); the original battery was 13 checks incl.
  one tautological always-pass check, not 12.
- Behavior note (by design, now documented): the very first interval check
  (~1 min in) creates a baseline backup if the profile has none yet.

## 2026-07-18 — Round verification consolidated (main session)
Three adversarial verifiers (backup / macros+patrol / GUI+integration)
found and fixed 16 real bugs across the round (2 critical: the GitHub
backup backend could sweep the user's staged files into backup commits;
macro "once" mode replayed forever due to the main loop re-instantiating
finished modes). Test batteries now: backup 31/31, macros/patrol v2 (real
main-loop contract simulation) all green, GUI live click-through green.
OPEN MINOR ITEMS deliberately deferred to the next round (UX polish, not
defects): (1) ▶ Play doesn't auto-stop an armed recording (harmless — the
recorder now only samples in Manual — but the armed state resumes later);
(2) saving a macro silently overwrites a same-named macro; (3) stopping a
looping macro requires switching to Manual (upstream mode-switch
semantics); (4) manual "Back up now" during emulator writes can catch a
torn .sav (plugin-triggered backups are safe; a pause-during-backup
option would close it); (5) Tk menu bar stays visible in handheld
fullscreen (cosmetic).

## 2026-07-18 — Handheld menu-hide + XInput gamepad support (#10, user-requested)
**Menu-hide:** handheld fullscreen now also hides the Tk menu bar
(Emulator/Profile/View/Help) for a truly clean screen; opening the tool
drawer (Pokeball / H / Back+Start) brings the menu back, closing the
drawer hides it again, leaving handheld mode restores it permanently.
Implemented in dashboard_gui.py (_apply_menu_visibility, called from
_apply_handheld_layout AFTER the fullscreen attribute change because Tk
fullscreen recreates the native hwnd on Windows). Live-verified through
all orderings incl. exiting handheld with the drawer open (screenshots
mh_1..mh_6 in the session scratchpad).

**Gamepad (answers "controller integration does not seem to work" — it
did not exist; upstream is keyboard-only):** new modules/gamepad.py
(ctypes XInput, XInput1_4.dll -> XInput9_1_0.dll fallback, graceful
"unavailable" without them) + plugins/gamepad_plugin.py registering a
per-frame listener. Mapping: D-Pad/left stick -> GBA D-pad; A->A; B->B;
X->B; Y->A; Start->Start; Back->Select; LB->L; RB->R; Back+Start
together toggles the handheld tool drawer (suppressed from game input).
Injection only in Manual mode via the same hold/release API as the
keyboard (so macro recording captures pad play automatically); edge-based
press/release; releases everything on disconnect/mode change/error;
disconnected pads polled only ~1x/s. Status line ("Controller:
connected / not detected / unavailable") added to the STATUS card.
Verified: 19/19 stubbed-XInput unit tests (mapping, edges, deadzone,
disconnect backoff + release-all, combo edge + suppression, mode gate,
broken-context survival); live run shows "not detected" without a pad and
a clean exit. CAVEAT: real-controller end-to-end needs the user's Ally —
no pad exists on the dev machine.

## 2026-07-18 — A7: warp-aware global pathfinding (#8)
- **Added** `modules/warp_graph.py`: world graph extracted from the game's
  own map headers via the emulator (ROM data — works at the title screen,
  no save needed). Maps joined by N/S/E/W connections collapse into
  regions (union-find); every warp is a directed edge (from-tile ->
  arrival-tile). Dive/Emerge connections and dynamic warps (save-data
  destinations, 127/127) are excluded on purpose. Cached per ROM at
  `cache/warp_graph_<rom>.json` (gitignored); extraction measured at
  0.02 s for Emerald: 518 maps, 461 regions, 1268 warp edges.
- **Added** `modules/modes/util/global_navigation.py`:
  `navigate_to_anywhere(map, coords)` — BFS plan over regions, then per
  leg: upstream `navigate_to` TO the warp tile (upstream already follows a
  warp when it is the final waypoint — walking.py:367-375 + 280-frame warp
  timeout), settle, verify the region changed (friendly BotModeError for
  locked/event-gated warps), re-plan from the actual position each leg.
- **Modified** `plugins/custom_modes/patrol.py` (v3): waypoints may now be
  anywhere in the world; docstring updated.
- **Verified** (scratchpad test_warp_graph.py, 23/23 with the REAL ROM
  headless): extraction ground truths (Littleroot's three door warps both
  directions, Brendan's stairs pair, outdoor Hoenn one region, 2-warp plan
  from Brendan's 2F to Route 101, multi-leg Littleroot->Granite Cave B1F,
  Faraway Island honestly unreachable), cache round-trip + lazy singleton,
  one-way/unreachable planner semantics, dry-run generator (warp leg +
  final navigate, direct same-region, unroutable and non-firing-warp
  errors). Mode discovery still green.
- **Pending real gameplay**: an actual cross-warp walk (no in-game save on
  this machine); locked-door behavior in the wild; surf-transition routes
  (upstream limitation carried over).

## 2026-07-18 — A6: shiny alerts (#12) + update notice (#18)
- Added `plugins/shiny_alert_plugin.py` + `alerts.yml` (root template,
  per-profile whole-file override, backup.yml conventions): shiny ->
  toast (notify-py, non-blocking) + Windows system ding (async) +
  optional auto_pause->Manual (default off). All paths swallowed; logger
  "alerts". Added `modules/update_check.py`: once-per-launch daemon
  thread (git fetch + rev-list with timeouts, walk-up .git discovery),
  result polled by the sidebar refresh -> Status-card accent line
  "N update(s) available - run install.py" + highlighted event-log entry.
  GUI: `_update_label` in Status card (packed on demand), teardown-safe.
- Verified: 21-check headless battery (config layering/malformed, stubbed
  toast/sound firing + swallowing, stubbed-git behind/up-to-date/offline/
  detached/garbage, poll gating); real notify-py toast fired on this
  machine; live runs x2 (unforced: no banner, 3 s startup; forced-behind
  wrapper: banner + event entry, screenshots au_*.png). Gitignore
  negation verified via git ls-files.
- Honest gaps: end-to-end toast/ding needs a REAL in-game shiny; the
  banner path was forced via a test launcher (real "behind" state not
  reproduced against the remote to avoid resetting the working repo).

## 2026-07-18 — A8: cloud save-sync v2 (#20)
New `modules/cloud_sync.py` + wiring: exit-side sync pushes the profile
save to `cloud-backups/<profile>/` (zip + sync_manifest.json: machine,
UTC timestamp, save SHA-1) via pathspec-scoped, time-boxed git; launch-side
sync applies a newer cloud save. SAFE APPLICATION POINT: run_launch_sync()
is called in pokebot.py immediately after load_plugins() — before any GUI,
profile or emulator exists — so an apply can never race a live save file
(this is also why it is synchronous; it is fully gated on the opt-in
`sync.enabled` config, default false, so out of the box it costs nothing
and touches no network). EXIT POINT: the dashboard close path AFTER
emulator.shutdown() flushed the save — the stock close ends in os._exit(0),
so atexit never runs; killing the console window bypasses sync (documented).
CONFLICT SEMANTICS: apply only when the local save hash equals the
last-synced baseline (or the profile is fresh); otherwise local ALWAYS
wins, the GUI shows a warning line and offers "Import cloud save as new
profile…" (materialized from origin's object DB via git show — no pull of
the working tree needed). A pre-apply safety backup (reason "presync") is
always taken. Cloud state is read from origin/<branch> refs after a fetch,
falling back to the working tree when offline.
BUGS THE BATTERY CAUGHT PRE-COMMIT (both fixed): (1) exit-sync wrote its
cloud files before pulling — a second machine's ff-only pull then refused
("untracked files would be overwritten"), breaking every cross-machine
push; (2) the sync baseline was recorded even when the push FAILED, after
which a later launch believed local was "unchanged since sync" and applied
the OLDER cloud save over newer local progress (data loss). Baseline now
records only after a successful push, plus a rollback guard (cloud
manifest must be strictly newer than the baseline).
Verified: 23/23 two-machine battery over a real bare git remote (push,
apply, continuity round-trip, divergence conflict, import escape hatch,
up-to-date, offline fail-soft, disabled no-op, malformed manifest,
zip-slip refusal); A1 backup battery still fully green; live GUI run
(sync line renders, clean close, disabled = zero sync activity).
Pending real-world: an actual two-PC run over GitHub (user's desktop +
Ally) — the git transport is identical, but network auth/latency is not
exercised by the local bare remote.

## 2026-07-18 — Handheld polish: party XP bars + popups forced on top (user feedback)
- **Party XP bar**: each party row now shows a thin accent-blue experience
  bar (progress to next level, `exp_fraction_to_next_level`) with an
  "XP NN%" label, directly under the HP bar. Reuses the HP bar's proven
  place()-based fill pattern; eggs render it empty. modules/gui/dashboard_gui.py.
- **Popups behind the emulator (handheld) fixed**: in handheld fullscreen a
  plain Toplevel opened *behind* the emulator video. New `_prepare_dialog()`
  (transient + `-topmost` + lift + focus_force + grab_set + center-over-
  window) is applied to the Restore dialog. The two macro/cloud name
  prompts moved off `simpledialog.askstring` (which sank behind fullscreen)
  onto a new `_ask_text()` — a topmost, touch-friendly modal (large entry,
  big OK/Cancel, Enter/Esc bound) formatted for handheld.
- Verified: py_compile + real-import (DashboardScreen methods present).
  PENDING USER HANDS-ON: XP bar with a real (non-empty) party, and the
  dialog-on-top behavior in actual handheld fullscreen (title-screen test
  save has no party and this session is credit-constrained for a live
  driven screenshot; the fix uses the standard Windows topmost technique).
