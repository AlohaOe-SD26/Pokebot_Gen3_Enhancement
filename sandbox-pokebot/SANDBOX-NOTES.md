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

## 2026-07-18 — Game cheat menu (user request)
- **Added** modules/game_cheats.py (CheatManager singleton), plugins/game_cheats_plugin.py
  (BotListener: throttled overworld toggles + Task_BattleStart wild overrides),
  game_cheats.yml (tracked template; per-profile override), a "CHEATS" card in
  modules/gui/dashboard_gui.py, and CHEATS-DESIGN.md. Built on the bot's own
  verified write toolkit (debug_utilities.debug_create_pokemon / debug_write_party /
  debug_write_item_bag / debug_give_max_coins_and_money) — the same code the stock
  Debug menu uses. Distinct from upstream cheats.yml (bot-behaviour cheats).
- **Cheats**: actions (overworld-gated) — Heal party, Max level 100, Perfect IVs,
  Max friendship, Max money, Item pack, Max Poké Balls, 99× Rare Candy; toggles —
  Infinite money, Auto-heal party (overworld, surgical HP/status writes outside the
  encrypted region), Force wild species=X@Lv, Guaranteed shiny wild (both mirror the
  stock ForceShinyEncounterListener: overwrite gEnemyParty at Task_BattleStart).
- **Deferred (honest)**: no/guaranteed-encounter toggles (needs RNG hook), PP restore
  (encrypted substruct), fast-egg-hatch/safari/always-bite.
- **Verified**: py_compile + real-import + plugin/listener subclass checks; 32/32
  headless battery (config layering/override/malformed, coercion, persistence,
  encryption XOR round-trip, guard-safety: toggles & wild-override never raise without
  an emulator, action off-overworld refusal); 15/15 LIVE emulator byte-verification
  (real Emerald ROM) — debug_create_pokemon(force species) decodes back to the exact
  species/level/shiny with a valid checksum for Bulbasaur L5 shiny, Gyarados L100,
  Zigzagoon L23 shiny, Pikachu L42; money encodes/decodes to 900000 with the real key.
  Live GUI screenshot (scratchpad cheats_card.png): card renders, 59fps (no per-frame
  cost). PENDING USER SAVE: actual in-game effect (party really L100, wild really
  replaced) — the title-screen test save has no party/bag to round-trip in-game.
- Every cheat is fully exception-guarded (logs to logs/game_cheats.log); one-shot
  actions are irreversible except by restoring — the card warns "back up first".
- **Adversarial verification (2026-07-18)** — 77-check live battery added
  (scratchpad/test_cheats_adversarial.py) on top of the 32 headless + 15 live:
  negative controls (corrupted mon/checksum → invalid), edge species
  (Unown/Deoxys/Mew/Wurmple/held-item/L1/L100 all fabricate valid), party rebuild
  driven through the REAL CheatManager (captures debug_write_party) proving
  nickname/PV(form)/IV/friendship/level survive + egg pass-through, auto-heal
  surgical write byte-verified live against gPlayerParty (HP+status fixed, checksum
  intact, egg untouched), trainer-battle no-override vs wild clone/force gating,
  listener throttle (1/15 frames) + single battle-start fire, unsafe-state refusal.
  All green. Backup battery (31) + module imports still pass.
- **BUG FIXED (medium, data-loss not corruption)**: party rebuild actions
  (heal/max-level/perfect-IVs/max-friendship) did not pass `nickname=` to
  debug_create_pokemon, so every rebuild WIPED custom nicknames back to the
  species default. Fixed by adding `nickname=mon.nickname` to the rebuild kwargs;
  regression-covered in the adversarial battery.

## 2026-07-19 — Tabbed tool column + sprite species picker (user feedback)
- **Tabbed tool column**: the single scrolling card stack is now a 5-tab
  interface (Play / Party / Stats / Cheats / Backups), so nothing needs
  scrolling to reach — in desktop AND the handheld Pokéball drawer. Tab bar
  above the (still-present, as a small-screen safety net) scroll area;
  active tab highlighted in accent; default "Play"; last tab persisted per
  profile in dashboard_ui.json. Grouping: Play = Controls + Macros;
  Party = Party (HP/XP/sprites) + Shiny log; Stats = KPIs + Status +
  Event log; Cheats = CHEATS card; Backups = Backups/Sync.
  - Fixed a latent bug found while wiring persistence: the initial build's
    `_show_tab("Play")` was persisting before `_restore_ui_state` read the
    saved tab, so a saved tab could never restore — build now calls it with
    `persist=False`.
- **Cheat species picker with sprites**: the force-wild-species free-text
  field is replaced by a dropdown button showing the selected species'
  sprite + name; clicking opens a searchable, sprite-illustrated picker
  (type-to-filter across ~400 species; unfiltered list capped at 60 for
  instant open; sprites lazy-loaded + cached). Feeds the same
  force_wild_species_name value as before. Sprites reuse the bot's own
  get_regular_sprite/get_shiny_sprite (shiny variant shown when the
  guaranteed-shiny toggle is on).
- Verified: py_compile + real-import + mode/plugin discovery; headless
  picker screenshots (default + filtered "char" → Charmander/Charmeleon/
  Charizard with sprites); live-ROM screenshots of all 5 tabs + the
  handheld drawer showing tabs. Scratchpad: picker_default/filtered.png,
  tab_{play,party,stats,cheats,backups,handheld_drawer}.png.

## 2026-07-19 — Cheat species picker shows the FULL dex (user feedback)
- Removed the 60-item unfiltered cap in `_open_species_picker`: the picker
  now shows all selectable species (scrollable) by default; typing still
  filters. Verified the source is complete — `_species_by_index` yields
  exactly **386 unique species** (full Gen-3 National Dex, every Emerald
  Pokémon: all 3 Hoenn starters, Rayquaza/Kyogre/Groudon/Deoxys/Jirachi/
  Latios/Latias/Mew/Milotic/etc.), no placeholders, no duplicates.
- Verified: py_compile + completeness count + headless picker screenshot
  (default list opens on Bulbasaur→Venusaur→Charmander with scrollbar).

## 2026-07-19 — #30 handheld/GUI refinements + #31 adjustable money cheat
- **#30a** Persistent Handheld toggle: moved out of the Controls card into a
  new persistent column header (`_column_header`) shown above the tabs on
  every tab. In the handheld drawer it sits right of the "TOOLS" text
  (labelled "⛶ Windowed", exits handheld); desktop shows just "⛶ Handheld".
- **#30b** Handheld menu relocation: `_apply_menu_visibility` now hides the
  Tk menu bar ENTIRELY in handheld (even with the drawer open); the stock
  menu commands were refactored into `_menu_commands()` (single source of
  truth) and surfaced as a "GAME MENU" card in the Play tab (also visible on
  desktop). Desktop keeps the normal menu bar.
- **#30c** Left Party Section: a 6-slot vertical strip left of the video
  (grid column 0 desktop; left overlay in handheld via `_layout_party_strip`).
  Empty slot = dimmed Poké Ball; filled = mon sprite alpha-composited over its
  caught-ball sprite (`_build_party_icon`, PIL); egg = egg sprite. Cached by
  species|shiny|ball. Video moved to grid column 1, tools to column 2.
- **#30d** Hover stats: `_show_party_tooltip(index)` / `_hide_party_tooltip()`
  (topmost borderless Toplevel) driven by Enter/Leave on both the strip slots
  and the party-tab rows (bound recursively; debounced). INDEX-BASED so the
  future gamepad-GUI nav (#32) can show stats for the focused slot.
- **#31** Adjustable money: `game_cheats.py` gained `get_current_money`,
  `set_money(value)` (one-shot, overworld-gated, clamped 0..999,999), and a
  `lock_money`/`locked_money_value` toggle applied in `apply_persistent_toggles`
  (lock takes precedence over infinite-money). CHEATS card gained a Money
  entry (pre-filled with current money when a save is loaded), "Set" button,
  and "Lock" checkbox; `_refresh_money_field` keeps it live unless locked/edited.
- Verified: py_compile + real-import (all new methods present), stat-format +
  empty/egg unit tests, mode discovery green, ball/egg sprite paths resolve,
  money API round-trip; LIVE launch (real ROM, test-dashboard) screenshots —
  desktop Play (party strip + persistent Handheld + GAME MENU), handheld
  drawer (no menu, TOOLS+Windowed+Hide header, menu in Play tab), Cheats tab
  (money field + Lock). Honest gap: filled-slot composite + live hover tooltip
  need a progressed save (empty party at title screen).

## 2026-07-19 — Gamepad-driven GUI navigation (#32)
- **What:** the ROG/Xbox controller can now drive the DASHBOARD (navigate +
  activate widgets), separate from the existing in-GAME Manual input.
- **Activation scheme:** Handheld — opening the Pokéball drawer (Back+Start,
  or H) turns GUI-nav ON; closing it returns control to the game (wired in
  `_set_drawer`). Desktop — Back+Start toggles GUI-nav directly.
- **Mapping (GUI-nav active):** D-pad/left-stick = move focus (edge-detected,
  one move per press); A = activate (invoke button / toggle); B = back
  (close picker/dialog → close drawer → exit nav); LB/RB = previous/next
  tab. While active, game-input injection is suppressed (mutually exclusive).
- **Focus model (DashboardScreen):** ordered registry = persistent Handheld
  button → 6 left-party slots (controller "hover" any mon on any tab, shows
  the stats tooltip via `_show_party_tooltip(index)`) → the active tab's
  enabled buttons/checkboxes (disabled skipped). Focus draws a thick accent
  ring + accent background tint (unmistakable on a handheld). Rebuilds on
  tab change / activation; guarded against destroyed widgets.
- **Thread-safety:** the gamepad listener's handle_frame runs on the Tk main
  thread, so `gui_focus_*` are called directly (no cross-thread Tk).
- **Verify:** 23/23 stubbed unit tests (focus move/wrap/activate/highlight/
  party-tooltip + gamepad routing: edge-fire, activate, tab cycle, game-
  injection suppressed while nav active, drawer/desktop activation). Live
  launch (real ROM): handheld → drawer opens → nav activates → focus ring
  on the real Handheld button, no crash, clean layout (screenshot
  n32_1_drawer_navring.png). GAP: real-pad feel + moving the ring across the
  full tab with a physical controller need the user's Ally.

## 2026-07-19 — #33 GUI fixes: left party always visible + unified show/hide
- **Fix A (left party always visible):** in handheld the strip was `place()`d
  over the video canvas, but the canvas is created AFTER the strip so it
  stacked on top and hid it. Added `_party_strip.lift()` in the handheld
  branch of `_layout_party_strip`. Now visible on the left edge of the
  fullscreen video (and unchanged/visible on desktop, incl. when the tool
  column is hidden — it lives in its own grid column 0).
- **Fix B (unified open/close in both modes):** desktop can now hide the
  tool column so the emulator fills the window, reopened by the Pokéball —
  same paradigm as the handheld drawer. New `_tools_hidden` state (persisted
  per profile in dashboard_ui.json); `_on_pokeball_clicked`/`_on_hide_clicked`
  route per mode (handheld→drawer, desktop→tool column); the desktop header
  now shows both the Handheld toggle and a "Hide" button; the Pokéball
  appears top-right when tools are hidden.
- Verified: py_compile + real-import; live launch screenshots — desktop
  open (n33_1), desktop hidden w/ Pokéball + left party (n33_2), handheld
  drawer closed w/ left party now visible (n33_3), handheld drawer open
  (n33_4). Reopen path is code-trivial (Pokéball → _set_tools_hidden(False),
  same as the open state); the live reopen click landed near the title bar
  so that one shot fell back — not a code issue.

## 2026-07-19 — Watchdog / auto-recovery (#22)
- **Added** modules/watchdog.py (singleton, survives listener rebuilds),
  plugins/watchdog_plugin.py (per-frame listener + on_logging_encounter +
  bg-thread start), watchdog.yml (config template), a "Watchdog" line in the
  GUI STATUS card. .gitignore negation for the plugin.
- **Detection signals (each guarded vs false-trips):**
  - Encounter stall — a mode that WAS producing encounters stops for
    `encounter_stall_minutes`; keyed off had-an-encounter so non-encounter
    modes never trip. The primary recoverable fault.
  - Fault drop-to-Manual — error message coincident with hunting→Manual;
    always alerts, auto-restarts if `auto_restart_on_error`.
  - Frame freeze — bg thread; frame counter frozen `softlock_seconds` =
    main loop hung → ALERT-ONLY (a hung main thread can't be safely
    auto-recovered; honest scope).
- **Recovery ladder** (main thread, safe point): re-assert mode → reload a
  recent healthy save state (in-memory snapshot or current_state.ss1, with a
  safety backup first) → after max_recovery_attempts give up (drop to Manual
  + loud alert; never hammer). note_encounter() = progress → clears fault.
- Everything safe-state (OVERWORLD) gated + exception-guarded; disabled
  config = fully inert. Alerts reuse notify-py toast + winsound.
- **Verified:** 17/17 headless battery (ladder, no-false-trip Manual/
  no-encounter/disabled, drop-to-Manual restart, safe-state gate, exception
  safety, malformed-config defaults, frame-freeze once/cleared/Manual-
  ignored); plugin discovery loads all 8 plugins; backup battery still green;
  live launch shows "Watchdog: OK" at 60 fps, clean close. GAP: real softlock
  recovery on a live hunt needs a progressed save.

## 2026-07-19 — Hunt Planner v1 (#9)
- `modules/encounter_index.py`: reverse wild-encounter index built headlessly
  from the ROM's gWildMonHeaders (via modules.map.get_wild_encounters_for_map)
  — species → [{map, pretty name, method, rate%, level range}], best-rate
  first. Per-ROM JSON cache at cache/ (corrupt/non-dict → rebuild, warp_graph
  lesson). `locations_for_species()`, `recommended_mode_for_method()`.
- Method→mode: Grass/Surfing→Spin, rods→Fishing, Rock Smash→Rock Smash;
  only offered if the mode exists (else Manual).
- GUI: new **Hunt** tab (TAB_ORDER). `_open_species_picker` generalized to
  take an on_choose callback (default = cheat) — reused for target pick.
  `_plan_hunt` shows ranked locations + recommended mode; each row's "Hunt"
  button sets that mode (`_start_hunt`). v1 sets the mode; AUTO-TRAVEL to the
  map is v2 (needs a travel bot-mode wrapping navigate_to_anywhere — a GUI
  button can't drive that generator).
- Verified: 19/19 fact-check vs the real Emerald ROM (Poochyena Route
  103/101/104 grass, Tentacool/Wingull surf, Magikarp fishing, Zubat caves,
  Treecko/Rayquaza no-wild, sorting, cache round-trip + corrupt rebuild,
  method→mode). Index: 132 species / 805 location rows. Live screenshot of
  the populated Hunt tab. Bug fixed: str.index shadowed name resolution.

## 2026-07-19 — KI-6 tab fix + Hunt Planner v2 (auto travel-and-hunt)
- KI-6: tab bar now wraps to 2 balanced rows when >4 tabs (3+3 for six) —
  legible in desktop + handheld drawer (dashboard_gui.py). Gamepad nav /
  tab persist unaffected.
- Hunt Planner v2: real one-click travel+hunt.
  - `encounter_index.find_encounter_tile(map, method)` reads a map's tiles
    from ROM (works pre-save) and returns a representative WALKABLE tile:
    Grass = land encounter tile; Surfing = surfable encounter tile; rods =
    land tile adjacent to water; else None (degrade). Scan-capped (4000).
  - `set/get_hunt_target()` store the selection (species/map/tile/method),
    persisted to profiles/<n>/hunt_target.json.
  - New `plugins/custom_modes/hunt_mode.py` "Hunt (Custom)": navigates to
    the tile via navigate_to_anywhere (avoid_encounters en route) then hunts
    (spin for grass/surf, fish loop for rods). Default encounter pipeline
    applies. No tile / no target → friendly BotModeError.
  - Hunt tab "Hunt" button now sets the target + switches to Hunt (Custom).
- Verified: py_compile + import + mode discovery (Hunt (Custom) listed) +
  all 8 plugins load; 15/15 v2 battery (real-ROM tile finder incl. Route
  103 grass tile validated as a real encounter tile + a surfable tile;
  target round-trip; mocked-nav mode plan: grass→nav+spin, rod→nav+fish,
  no-target/no-tile→error); live screenshots ki6_1 (desktop) + ki6_2
  (handheld drawer) show 6 tabs legible.
- HONEST GAP: actually walking the route + hunting needs a progressed save
  (title-screen save can't); Rock Smash has no auto-tile (degrades).

## 2026-07-19 — Living-Dex orchestrator v1 (#23)
- `modules/living_dex.py`: target-list derivation. Default source
  "uncaught_wild" = every species with a wild encounter (from
  encounter_index) that the player does NOT own (from pokedex.py owned
  flags), in National-Dex order; species with no wild location
  (legendaries/statics/starters/trade/evolve-only) are excluded. Also
  accepts an explicit picked list (non-wild/unknown → `skipped` w/ reason).
  Run + progress persisted per profile to `living_dex.json`
  (targets/done/skipped). Helpers: is_owned, progress, next_target_index.
- `plugins/custom_modes/living_dex_mode.py` — "Living Dex (Custom)" BotMode:
  iterates targets; per target resolves best location+tile
  (encounter_index.find_encounter_tile), travels via navigate_to_anywhere,
  then spin()/fish() with a stop_condition of "target now owned". CATCH
  INTENT: on_battle_started returns BattleAction.Catch only for the current
  target species when not yet owned (else None → default pipeline, so
  shinies of anything are still caught). Advances on catch (owned flip),
  SKIPS (and records) targets with no location/unreachable, STOPS to Manual
  when the list is exhausted OR boxes/party are full (never loses a catch).
  Fully exception-guarded.
- GUI: LIVING DEX card in the Hunt tab — progress ("N/M owned · next: X"),
  "Start — all uncaught wild", a custom-list builder (＋ Add species /
  Start custom (N)), and Stop & clear. disable() clears the new refs.
- Verified: py_compile + real-import; "Living Dex (Custom)" discovered
  alongside Hunt/Macro/Patrol; all 8 plugins load; 16/16 unit battery
  (derivation incl. owned-drop/no-wild-exclude/custom-skip, next-target
  sequencing, progress, catch-intent: Catch only for uncaught target, None
  for non-target/owned/trainer); real-ROM fact-check (empty pokedex → 132
  wild targets, Poochyena/Zigzagoon/Wingull/Tentacool/Zubat in, Treecko/
  Rayquaza/Mew out); live in-process run of derive→save→refresh→clear
  against the real emulator, no error.
- Honest gaps: an actual autonomous catch-and-advance RUN needs a
  progressed save (title-screen save can't walk the overworld) — sequencing
  + catch-intent verified by unit tests + code only. Clean card SCREENSHOT
  not captured (post-#33 bare-Tk harness geometry expands the grab region);
  card uses the same verified pattern as the Hunt Planner card.

## 2026-07-19 — Analytics suite v1 (#11)
- **Added** `modules/analytics.py` (pure, GUI-free): `luck_meter` (binomial
  expectation vs actual shinies at full-odds 1/8192 → expected/sigma/z/
  verdict), `TrendBuffer` (capped enc/hr ring buffer), `build_stats_rows`/
  `sort_rows`/`filter_rows` (per-species table from GlobalStats).
- **GUI** (`modules/gui/dashboard_gui.py`): an ANALYTICS card in the Stats
  tab — a Tk-Canvas enc/hr **sparkline** (sampled on the existing KPI cycle,
  no per-frame cost) + a **luck meter** line (colored by verdict) + an
  "Open stats browser…" button that pops a sortable/filterable ttk.Treeview
  of per-species stats WITH sprites (floats above the emulator via
  _prepare_dialog). All sources are stats.db (get_global_stats /
  encounter_rate); nothing baked. disable() clears the new widgets +
  destroys the browser + clears the trend buffer.
- Verified: 26/26 unit battery (luck math incl. N=0/S=0/lucky/unlucky/on-
  track, trend cap/decimation, row assembly/sort/filter); py_compile +
  real-import; mode+plugin discovery intact; live screenshots (empty state,
  populated sparkline+luck, browser with sprites). Gap: meaningful data
  needs a real hunt's stats.db (title-screen profile is empty — verified
  with a stub).

## 2026-07-19 — Auto-decline new move learning (default, all leveling bots) (#39)
- Root cause of the user's "learning a move interrupts the hunt": the battle
  config `new_move` defaulted to `stop` → dropped to Manual on every level-up
  move. Changed the fork DEFAULT to `cancel` (decline, keep the current
  moveset, hunt continues) in `modules/config/schemas_v1.py` (schema default)
  and `modules/config/templates/battle.yml` (template comment updated).
- Applies to ALL leveling bots: the single decision point is
  `DefaultBattleStrategy.which_move_should_be_replaced` (returns 0-3 = replace
  that slot, 4 = decline); every leveling strategy (LevelUp, LevelBalancing,
  Catch, etc.) inherits it. Verified: cancel→4 (decline), stop→4+Manual.
- FUTURE-INTELLIGENCE SEAM documented in default.py: smarter "is this move
  worth keeping / what to replace" logic goes in the `learn_best` branch (or
  a new `new_move` value). Config-gated so the user can switch behavior.
- NOTE: existing profiles that already copied `new_move: stop` keep it —
  set their profile/global battle.yml `new_move: cancel` (or delete the line
  to inherit the new default) to get the no-interrupt behavior.

## 2026-07-19 — Party visuals + gamepad-nav gating (#36/#37/#38)
- #36 Larger party balls: _PARTY_ICON_SIZE 52 → 104; the caught-ball is a
  full-slot backdrop (alpha 0.9), the mon rendered smaller (~62%) and
  BOTTOM-anchored so the ball's dome shows above it = clearly "behind the
  Pokémon". Empty slot = a large Poké Ball. (dashboard_gui.py _build_party_icon)
- #37 Themed hover tooltip: replaced the plain text Label with a Pokémon-
  themed card — sprite + shiny-gold name + colored TYPE badges (TYPE_COLORS
  map, luminance-based text color) + a color-coded IV grid (_iv_color
  green→red) + nature/ability/held/ball/HP + moves list. Same
  _show_party_tooltip(index)/_hide API (still gamepad-triggerable), topmost,
  rebuilt each show, on-screen clamped. Applies to left strip + Party tab.
- #38 Gamepad GUI-nav gated: removed the DESKTOP Back+Start "toggle nav"
  path (gamepad.py _toggle_ui) that was stealing gameplay control. GUI-nav
  is now active ⟺ the handheld Pokéball drawer is open; closed/desktop →
  the controller plays the game, never the GUI. Unit-verified.

## 2026-07-19 — LIVE real-save verification (Nick - Emerald, progressed party)
First test on a real in-game party (prior tests were title-screen). All
GUI/data areas render correctly on real data — NO bugs found:
- Left Party Section: 6 real party mons composited over their caught balls
  (ball visible behind), enlarged slots. ✓
- Party tab: real shiny team (Celebi Lv100 342/342 XP100%, Bulbasaur Lv9,
  Lotad, Zigzagoon, Wurmple, Sceptile) — names/levels/HP bars/XP bars/
  sprites/shiny badges all correct. ✓
- Cheats tab: Money field pre-filled with REAL money (7908); force-wild
  cheat shows Venusaur sprite. ✓
- Analytics/Stats: real stats.db — 57,436 encounters, 10 shinies, luck
  meter "10 shiny vs 7.0 expected (1/8,192) · lucky" (math correct);
  Watchdog: OK; State: OVERWORLD. ✓
- Hunt tab: Hunt Planner + Living Dex panels render. ✓
- Hover tooltip: could NOT be triggered via synthetic mouse-move in the
  harness (Tk <Enter> doesn't fire reliably on SetCursorPos while the
  emulator frame loop runs) — NOT a product bug; the tooltip's themed
  render was screenshot-verified with a stub (#37) and the real party data
  it reads is confirmed present. Needs a human mouse hover to see live.
Save left byte-identical (backed up + restored; md5 MATCH). No lingering
process.

## 2026-07-19 — Poké Ball allowlist (#40) + bigger party balls (#36 refine)
- Party balls enlarged 104→140px; ball drawn at full opacity as a backdrop,
  mon shrunk to 55% bottom-anchored so the ball's dome/band show clearly
  behind it (verified on the real Nick - Emerald party). Large mons still
  partly cover the ball — acceptable.
- #40 catch-ball allowlist: modules/catch_balls.py (config-backed set of
  allowed balls; default = all except Master Ball; global catch_balls.yml
  + per-profile override; safe default on malformed). Filtered in
  battle_strategies/catch.py `_get_best_poke_ball` (skips disallowed balls;
  no-allowed-ball falls back to the existing "no balls" behavior). GUI:
  CATCH BALLS card in the Hunt tab — a checkbox+icon per Gen-3 ball, saves
  on toggle. Master Ball also stays never-auto-thrown via catch.py's -1.
- Verified: compile/import, allowlist unit logic (default excludes Master),
  mode discovery green, live real-save screenshots (balls_1_play,
  balls_2_catchballs), save md5 unchanged.

## 2026-07-19 — Living Dex OPPORTUNISTIC catching (#43)
- The Living Dex now catches ANY un-owned species that is part of the run's
  plan when it's encountered — not just the single species it's travelling to.
  The driving target only steers movement; bonus catches happen in
  on_battle_started. modules/living_dex.py gained `is_wanted(index, run)`
  (species in run["targets"]); plugins/custom_modes/living_dex_mode.py:
  on_battle_started returns Catch for any wanted+un-owned opponent (gated on
  box space so a catch is never lost), and caches the run for cheap checks.
- No on_battle_ended bookkeeping needed: is_owned reads the live Pokédex, so
  a bonus catch auto-advances progress()/next_target_index() and a FAILED
  catch simply stays wanted (outcome-gating is implicit). Trainer battles and
  species not in the plan (custom lists) are untouched → default pipeline
  (shinies/CCF still apply).
- Verified: 22/22 unit battery (incl. non-target-but-wanted→Catch,
  owned→None, not-in-plan→None, boxes-full→None, is_wanted edge cases);
  compile + discovery green. Live catch-and-advance needs a real battle.

## 2026-07-19 — #44 party ball moved from strip to hover tooltip
- Left Party strip (`dashboard_gui.py _build_party_icon`): removed the
  ball-backdrop composite; now draws just the mon sprite at 0.9× centered
  (clean/legible). Empty slot = faded Poké Ball; egg = egg sprite. Dropped
  `ball` from the strip sprite-cache key (species|shiny only).
- Hover tooltip (`_build_tooltip_body`): the old text-only "Ball:" is now a
  proper row — a ~18px caught-ball icon + "Caught in: <Ball>" — via new
  cached `_tooltip_ball_icon()`. Held-item on its own line. Themed styling
  (type badges / IV grid / moves) unchanged; same _show_party_tooltip API.
- Verified: py_compile + real-import + mode discovery; tooltip render (stub
  Bulbasaur/Ultra Ball → ball row + icon shown); LIVE on the real
  Nick - Emerald save → clean strip (mon sprites, no ball backdrop),
  save md5-identical after run.

## 2026-07-19 — #41 obtainability (evolution half) + #42 capability gate (easy half)
- `modules/obtainability.py`: classify(species_index) in INTERNAL ids (per
  11-LIVINGDEX-DESIGN §0.1) → kind wild/evolution/unknown, evolution chain to
  base + method, automatable/needs_user (trade & item & beauty → needs_user;
  all-level + wild base → automatable). plan_for() targets the wild BASE for
  evolve-only species. The static/gift/roamer/trade/event/unobtainable split
  is left "unknown" honestly (research half, still to compile).
- `modules/capabilities.py`: can_use_method() reads the save — Surf needs the
  Surf move + Balance Badge (BADGE05); rods need the matching rod key item;
  Rock Smash needs the move + Dynamo Badge (BADGE03); Grass always ok;
  unknown methods permissive (never wrongly skip). capability_report() for GUI.
- `modules/living_dex.py`: best_reachable_location() prefers a location whose
  method the player can use now, defers (with reason) otherwise;
  obtainability_breakdown() classifies the whole uncaught dex (cached by
  owned-count).
- `plugins/custom_modes/living_dex_mode.py`: target selection now capability-
  gated — defers targets needing a capability the player lacks (retried a
  later session, NOT marked done); reports deferrals when the run pauses.
- GUI: LIVING DEX panel shows the obtainability breakdown + "You can use: …"
  capability line.
- Verified: 30/30 offline unit battery (evolution classify incl. Gyarados/
  Crobat/Vaporeon/Alakazam/Milotic/Caterpie; capability gate; best-reachable
  preference); live on the REAL Nick-Emerald save → panel showed "Uncaught:
  128 wild · 147 evolve · 102 special/trade" + "You can use: Old Rod, Good
  Rod, Super Rod" (real reads); save md5-identical.
- STILL TODO: #41 research-list compile (gift/static/roamer/trade/event/
  unobtainable) + honesty denominator; #42-HARD HM-gated map reachability;
  auto-evolve helper (level/stone) so evolve-only species auto-complete.

## 2026-07-19 — #41 obtainability RESEARCH HALF compiled + fact-checked
- `modules/data/emerald_obtainability.json` (NEW): the compiled + fact-checked
  Emerald override for the 105 base-non-wild species — kind / emerald_reachable /
  automatable / needs_user / note per species (National-Dex-keyed). Also carries
  the 4 documented in-game trades (none rescue an unobtainable species).
- `modules/obtainability.py`: classify() now consults the Emerald override for the
  base-non-wild bucket (gated on `context.rom.is_emerald`) instead of returning
  "unknown". Adds `emerald_reachable` (recursive for evolutions: base reachable
  AND no trade step), enriches the evolution reason, and adds `census()` +
  `ingame_trades()`. plan_for() adds a `wild_huntable` gate flag + `emerald_reachable`.
  Non-Emerald ROMs skip the override (those lists were only compiled for Emerald).
- `modules/living_dex.py`: obtainability_breakdown() keeps the old
  wild/evolution/special keys (backward-compat for the GUI) and ADDS the honest
  per-kind `categories` split + a `denominators` block (national_dex 386,
  obtainable_in_emerald 217, owned, owned_obtainable).
- `modules/gui/dashboard_gui.py`: Living-Dex panel label now shows BOTH
  denominators ("Owned N/386 National Dex - M/217 obtainable in Emerald") and a
  gift/static/roam vs trade/event/blocked uncaught split.
- `tests/test_obtainability.py` (NEW): 16 offline units; wires the Emerald ROM
  header via load_rom_data (no emulator) and skips cleanly if the ROM/cache is
  absent. Census sum, no-unknown, exact category counts, denominator 217/169,
  natdex round-trip, per-category spot-checks, trade-evo reachability, plan_for gate.
- CENSUS: wild 132 / evolution 149 / gift 7 / static 8 / roamer 1 / event 6 /
  breeding 3 / special 1 / unobtainable 79 = 386. 217 obtainable without trading.
- METHOD NOTE: the ROM's `gWildMonHeaders` (via the encounter-index cache) is the
  authoritative wild set and beat human memory every time — Roselia/Meditite/
  Zangoose/Lunatone = trade-only, Surskit = swarm-only, Azurill = breeding-only,
  Wynaut = wild (Route 130). Fixed a census trap: species.json index 0 placeholder
  shares Mew's dex #151 — enumerate via get_species_by_national_dex, not setdefault.
- STILL TODO: wire living_dex_mode target selection to plan_for's gate so
  gift/static/roamer route to the reset modes and trade/event/unobtainable are
  surfaced-not-hunted; add Sudowoodo + Ho-Oh to the static reset seed; auto-evolve
  helper. Verify on the REAL save when a session can boot the emulator (this pass
  was pure-data, validated against the ROM header + cache only).
