# Changelog — Pokebot_Gen3_Enhancement
> APPEND-ONLY. Every meaningful change, fix, or addition gets a dated entry
> at the END of this file (chronological order, oldest first).
> Entry format:
>
> `## YYYY-MM-DD — short summary  (punch-list #N if applicable)`
> followed by bullets: what changed, why, files touched.

---

## 2026-07-17 — Project bootstrapped with Claude Code Project Kit
- Created PROJECT KNOWLEDGE skeleton (00–07), CLAUDE.md standing directives,
  Remote-Start launcher, git repository + remote.

## 2026-07-17 — Vendored upstream pokebot-gen3 (punch-list #1)
- Imported 40Cakes/pokebot-gen3 at upstream commit `5dd898f8` into
  `pokebot-gen3/` via `git subtree add --squash`; added `upstream-pokebot`
  remote for future upstream pulls.

## 2026-07-17 — Deep documentation pass over the codebase (punch-list #2)
- Wrote `PROJECT KNOWLEDGE/CODEBASE/00–05`: overview + five layer docs
  (core runtime/emulator, game-state decoding, bot modes/battle engine,
  GUI/web/Discord interfaces, stats/config/data/tests/distribution) —
  ~2,400 lines, intent-level human language tied to code with file:line
  references, each ending with enhancement opportunities. Produced by five
  parallel documentation agents reading the source, then synthesized.
- Wrote `Pokemon_Emerald_AI_Notes.md` (repo root): standalone transfer
  notes for the sibling Pokémon Emerald AI project (emulator harness,
  symbolic memory reading, battle observation/math, navigation primitives,
  data files, integration paths).
- Copied the user's installer-as-codebase spec into
  `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md` for punch-list #4.
- Filled in `01-VISION-AND-DESIGN.md`, `02-ARCHITECTURE.md`, seeded
  `03-PUNCH-LIST.md` (#2–#6).

## 2026-07-17 — Restructure: two-folder fork layout + daily upstream sync
- Moved the upstream mirror to `40cakes repo/pokebot-gen3/` (subtree
  re-added at the new prefix) and the codebase docs to
  `40cakes repo/DOCUMENTATION/` (with `_history/` for versioned snapshots).
- Created `custom-pokebot/` — our fork, an exact copy of upstream
  `5dd898f8` — with `DOCUMENTATION/` and `DIVERGENCE-LOG.md`.
- Added `40cakes repo/UPDATE-LOG.md` (append-only upstream sync record)
  and the daily upstream-check standing directive to CLAUDE.md.
- Updated vision/architecture docs and decisions log for the new layout.

## 2026-07-17 — Documentation verification pass (sanity check)
- Six adversarial verifier agents re-checked every claim in the seven docs
  against source: ~975 claims verified, 39 errors fixed (8 in doc 01, 7 in
  doc 02, 7 in doc 03, 6 in doc 04, 5 in doc 05, 6 in AI notes; overview
  clean). Highest-value fixes: inverted LoseOnPurpose/Explosion behavior,
  navigate_to warp/surf limits, `decide_turn` returns a tuple, OBS uses
  obs-websocket not hotkeys, `/stream_video` sends nothing while video is
  disabled, work-queue errors exit the process.
- Three upstream bugs discovered and recorded as KI-1..KI-3 in
  05-KNOWN-ISSUES.md (stale pokebot.spec; `modified_stats()` TypeError
  dead code; stale `disable_default_battle_handler` docstring).
- Lesson logged as ML-1 in 08-MISTAKES.md (verify agent-written docs
  before building on them).

## 2026-07-17 — Custom-automations framework + Patrol mode (punch-list #3, partial)
- Built the drop-in custom-modes platform in `custom-pokebot/`:
  `plugins/custom_modes_loader.py` (auto-registers BotMode subclasses from
  the new `plugins/custom_modes/` folder via the stock plugin API) and the
  first custom bot: "Patrol (Custom)" (`plugins/custom_modes/patrol.py`) —
  waypoint-loop shiny hunting configured by a per-profile `patrol.yml`.
- Zero upstream files modified (logged in custom-pokebot/DIVERGENCE-LOG.md).
- Verified: py_compile + structural smoke test (loader discovers PatrolMode
  through the real files with bot modules stubbed; config validation
  failure/success paths pass). Live run pending ROM/deps — #3 stays open.
- How-to documented in `custom-pokebot/DOCUMENTATION/01-custom-automations.md`.

## 2026-07-17 — One-script installer/updater/healer (punch-list #4)
- Added `install.py` (repo root): 6-step git-driven adaptation of the
  installer-as-codebase pattern — finds/offers 64-bit Python 3.11-3.13,
  clones or fast-forward-updates the repo, detects + consent-restores
  drifted tracked files (user data untracked → never touched), pre-runs
  the bot's dependency bootstrap, smoke-checks critical files, offers
  launch. `--check-only` (read-only) and `--yes` (unattended) modes.
- Tested end-to-end on this machine: heal restored a deliberately
  corrupted file; dependencies + libmgba installed into Python 3.12;
  fresh-empty-folder clone succeeded after fixing Windows MAX_PATH
  ("Filename too long") via `core.longpaths=true` (+ partial-clone
  cleanup); cp1252 console crash and PowerShell piped-BOM prompt bugs
  fixed. Decision recorded in 06; also added root README.md.
- FIXED CRITICAL: upstream's `.gitignore` was silently excluding the #3
  custom-modes framework from commits (found by the fresh-clone test) —
  negation rules added (divergence logged), files now tracked (ML-2).
- Upgraded #3 verification: real-import discovery test passed (actual bot
  modules under Python 3.12, PatrolMode registers).

## 2026-07-17 — Custom web dashboard v1 (punch-list #5, partial)
- Built `custom-pokebot/modules/web/static/custom-ui/` (additive; no
  upstream code edits): live video with disabled-video overlay, KPI tiles,
  party panel (HP bars/status/shiny/egg), opponent card, mode/speed/AV
  controls, manual controller pad (Manual mode only), SSE live updates +
  event log. Docs: `custom-pokebot/DOCUMENTATION/02-custom-interface.md`.
- API contract taken from verified doc 04 + source (endpoint shapes,
  SSE format, /stats keys, Pokemon property names).
- Verified against a mock bot API (aiohttp, canned payloads, SSE, video)
  with headless-Edge screenshots; fixed an inline-span HP-bar bug. Live
  run with real bot pending → #5 stays open (v2 roadmap in the doc).

## 2026-07-18 — Dashboard: handheld mode for ROG Ally X (punch-list #5)
- User live-verified dashboard v1 ("seems to work well"); Patrol (#3)
  marked WIP pending user play-test.
- Added handheld mode: fullscreen pixel-perfect video, all tools in a
  translucent slide-in drawer, custom semi-transparent Pokéball SVG toggle,
  `H`/`Esc` hotkeys, Hide button, double-tap toggle, `?handheld=1`
  bookmark param, localStorage persistence, browser-fullscreen request.
  Desktop layout reorganized (all tools in one right column) and stays
  fully responsive.
- Verified via mock server + headless-Edge screenshots at 1920×1080
  (Ally-native): handheld closed, drawer open, desktop regression.
- Daily upstream check ran (new day): upstream main unchanged at
  `5dd898f8`; UPDATE-LOG stamped.

## 2026-07-18 — Smart dependency bootstrap + dashboard discoverability (user feedback)
- requirements.py (custom fork): now detects installed packages first and
  pip-installs only what's missing/outdated (verified: satisfied first run
  = ~2 s, no prompt, no pip; injected-fake-package test correctly flags
  only the fakes). Found + fixed an upstream dependency conflict in the
  process: cffi pin loosened `~=1.17.1` → `>=1.17.1` (aiortc→cryptography
  can force cffi 2.x; upstream's loop was downgrading/re-upgrading it).
- Dashboard now works out of the box: `http.yml` template defaults to
  enabled (127.0.0.1 only), new `dashboard_autoopen.py` plugin opens the
  dashboard in the browser after profile load, and the UI assets got a
  `?v=` cache-buster so updates always reach the browser.
- Root-caused "GUI changes don't exist" report: the resize/handheld
  features live in the BROWSER dashboard (not the Tkinter window), and the
  handheld commit postdated the user's test; auto-open + cache-busting
  remove both failure modes.

## 2026-07-18 — Native dashboard GUI (punch-list #5, user direction change)
- Per user: the dashboard layout belongs in the PROGRAM's own window, not
  a browser. Built `modules/gui/dashboard_gui.py` — new default GUI
  (`--classic-gui` restores upstream's): resizable letterboxed video +
  tool column (mode/speed/AV, KPI tiles, party HP bars, status, event
  log), handheld mode (F11/H/Esc, canvas-drawn Pokéball toggle, per-profile
  persistence), stock menu bar kept, debug tabs in a separate window.
- Verified on a REAL run (Emerald ROM, fresh test-dashboard profile, game
  at title screen): all four UI states screenshot-confirmed at 4K/300%
  scaling; fixed en route: window off-screen on scaled displays (clamp +
  re-assert position), speed-row clipping, DPI-aware capture tooling,
  and learned Tk fullscreen recreates the native hwnd on Windows.
- Browser dashboard remains as opt-in remote viewing (autoopen now
  defaults off).

## 2026-07-18 — Docs aligned to the native GUI; update FLAGGED TO REVIEW
- README, 02-ARCHITECTURE (folder map + run commands), punch list #5,
  handoff, and custom DOCUMENTATION/02 updated for the native dashboard
  GUI as the default interface (browser dashboard = opt-in remote viewing).
- Per the user: everything about the native-GUI update is marked
  **FLAGGED TO REVIEW** (user approved from screenshots only; no hands-on
  visual test yet). Flags live in 03-PUNCH-LIST #5, 04-HANDOFF, and
  custom-pokebot/DOCUMENTATION/02 — clear all three after the user's test.
  (Cleared later the same day after the user's hands-on "worked!".)

## 2026-07-18 — Installer V2: robust custom setup/update/heal + ROM handling (punch-list #4)
- Rewrote `install.py` per user requirements (SCRIPT_VERSION
  2026-07-18-CUSTOM-ROBUST-V2): 7 steps with per-step exception capture
  (one broken step logs its traceback and the run continues), a ✓/⚠/✗
  step summary, meaningful exit codes, and hybrid logging (full trace to
  `install.log`, auto-rotated, gitignored).
- Self-heal widened from custom-pokebot/ to ALL tracked files (mirror,
  docs, the installer itself); fixed git-porcelain quoted-path/rename
  parsing (paths with spaces previously could not be restored).
- New ROM step: verifies ROMs in `custom-pokebot/roms/` against the
  whitelist regex-parsed from `modules/roms.py` (works before deps
  exist); if the repo provides none, sideloads `.gba` files found next to
  the script (never overwrites, warns on non-whitelisted dumps).
- Verified: clean check-only; sideload path (fake ROM copied + correctly
  flagged unknown); heal restored the deliberately-deleted 16 MB ROM
  (spaces-in-path case) and re-verified it; log/summary/exit codes all
  exercised. Updates confirmed incremental (fetch + ff-only).

## 2026-07-18 — Sandbox A1: Backup & Restore system (punch-list #7)
- Built in sandbox-pokebot only: modules/backup_manager.py (local zip
  backups with retention; GitHub-repo cloud backend committing ONLY
  cloud-backups/ and pushing; synced-folder backend; restore-to-new-profile
  with zip-slip guard), plugins/backup_plugin.py (auto-backup on shiny +
  timed interval listener), backup.yml config template, and a BACKUPS card
  in the sandbox dashboard GUI (Back up now / Restore dialog).
- Verified: 12-check headless battery all PASS; real cloud backup pushed
  (commit 38a0e207, only cloud-backups/ in it — left as demo); live GUI
  screenshot confirms the card. Details: sandbox-pokebot/SANDBOX-NOTES.md.

## 2026-07-18 — Sandbox A2+A3: macro record/replay + multi-map Patrol (punch-list #7)
- A2: macro engine (`modules/macros.py`) — record human play in Manual
  mode frame-accurately (input-bitfield RLE), save as human-editable YAML
  per profile, replay via new "Macro (Custom)" bot mode (loop/once;
  battles interrupt → loop restarts the macro, once stops to Manual; the
  default encounter pipeline stays active). GUI: compact MACROS card
  (● Rec / dropdown / Loop / ▶) under CONTROLS; recorder listener
  registered by `plugins/macro_plugin.py`.
- A3: Patrol v2 — `patrol.yml` waypoints may target specific maps
  (`{map: [g, n], at: [x, y]}`), mixed freely with plain `[x, y]` entries.
- Layout: default dashboard window height 720→860 (clamped to screen)
  after the A1 column-clipping note; interactive cards ordered above
  passive ones so short windows clip only the event log.
- Verified: compile + discovery (both custom modes + listener register),
  headless battery (RLE, YAML round-trip, 6 malformed rejections, recorder
  semantics, patrol parse semantics incl. 5 rejections), live GUI
  screenshot of the MACROS card. Real record→replay needs hands-on play
  (test save sits at the title screen). Details: SANDBOX-NOTES.md.

## 2026-07-18 — Sandbox A4: GUI pack + round verification (punch-list #7)
- Dashboard GUI (sandbox): scrollable tool column (fixes clipping at small
  heights/high DPI, works in the handheld drawer, mousewheel-driven),
  32px party sprites via upstream sprites.py (shiny/anti-shiny/Unown/Egg
  handled, PhotoImages cached), new SHINY LOG card (last 5 phases), card
  order reworked (interactive first), bounded event log.
- Round exit gate passed: headless sprite/path/import batteries,
  install_sandbox.py --check-only, and a LIVE run — real mousewheel input
  scrolled the shrunken column, F11+H reached handheld drawer; clean exit.
  Remaining caveats (need real gameplay) recorded in SANDBOX-NOTES.md and
  SANDBOX-PROPOSALS.md.

## 2026-07-18 — Sandbox: handheld menu-hide + XInput gamepad (#10, user feedback)
- Handheld fullscreen now hides the Tk menu bar; the tool drawer
  (Pokeball/H/Back+Start) brings it back; exiting handheld restores it.
  Live-verified through every ordering (Windows hwnd-recreation quirk
  handled by re-asserting the menu after the fullscreen toggle).
- Root-caused "controller integration does not seem to work": there WAS
  none (upstream is keyboard-only). Built modules/gamepad.py + plugin:
  XInput polling per frame (main thread, edge-based, Manual-mode-gated,
  release-all on disconnect/mode change, 1 s backoff when no pad),
  documented Xbox->GBA mapping, Back+Start = drawer toggle, controller
  status line in the STATUS card. 19/19 stubbed-XInput unit tests; real
  Ally pad test remains user-side.

## 2026-07-18 — Warp-aware global pathfinding (punch-list #8, sandbox)
- `modules/warp_graph.py`: world graph from the game's own map headers
  (union-find regions over map connections + directed warp edges; Dive and
  dynamic warps excluded), cached per ROM; Emerald extraction: 518 maps,
  461 regions, 1268 warp edges in 0.02 s at the title screen.
- `modules/modes/util/global_navigation.py`: navigate_to_anywhere() — BFS
  route over regions, per-leg navigate_to onto the warp tile (upstream
  follows the warp), settle + verify + re-plan; friendly errors for
  unroutable targets and non-firing (locked) warps.
- Patrol v3: world-spanning waypoints. Verified 23/23 against the real ROM
  headless (ground truths, cache round-trip, planner semantics, dry-run
  generator); real cross-warp walk pending user save. Emerald-AI notes
  updated (global navigation now exists for the sibling project).

## 2026-07-18 — Sandbox A6: shiny alerts + update notice (punch-list #12, #18)
- Shiny alerts plugin (toast via notify-py, async system ding, optional
  auto-pause; alerts.yml global/per-profile) and a launch-time
  updates-available notice (daemon-thread git check, Status-card line +
  event-log entry; silent when offline/up-to-date). 21-check headless
  battery + real-toast proof + live forced/unforced GUI runs. Both
  pending user end-to-end (real shiny; real behind-remote state).

## 2026-07-18 - Cloud save-sync v2 (punch-list #20, sandbox A8)
- New sandbox-pokebot/modules/cloud_sync.py + wiring: exit-side push of
  the profile save to cloud-backups/ (zip + manifest) and launch-side
  apply of newer cloud saves, gated to run BEFORE the emulator exists
  (pokebot.py, right after load_plugins) - the only provably safe point.
  Exit hook lives in the dashboard close path after emulator.shutdown()
  because the stock close ends in os._exit (atexit never runs).
- Conflict protection: apply only when local matches the last-synced
  baseline; otherwise local wins + GUI "Import cloud save as new
  profile..." escape hatch; pre-apply safety backup always taken;
  rollback guard against older cloud manifests. Opt-in via backup.yml
  sync block (default off).
- Verified 23/23 in a two-machine simulation over a real bare git remote;
  the battery caught two data-safety bugs pre-commit (pull-before-write
  ordering; baseline recorded on failed push enabling a rollback) - both
  fixed. A1 backup battery still green; live GUI run confirms the sync
  status line and a clean close. Real desktop-Ally run = user test.

## 2026-07-18 — Handheld polish: party XP bars + dialogs forced on top (sandbox, user feedback)
- Sandbox dashboard GUI: added an XP-to-next-level bar under each party
  member's HP bar; fixed popup dialogs (Restore, macro-name, cloud-import)
  opening BEHIND the emulator in handheld fullscreen by forcing them
  topmost/modal/centered and replacing simpledialog.askstring with a
  touch-friendly `_ask_text` modal. py_compile + real-import verified;
  XP-with-real-party and live fullscreen dialog stacking pending user test.

## 2026-07-18 — Game cheat menu (sandbox, user request)
- Added a CHEATS card + modules/game_cheats.py + plugins/game_cheats_plugin.py +
  game_cheats.yml to sandbox-pokebot: toggleable game cheats (max level, perfect IVs,
  max friendship, heal, max money, item pack, max balls, rare candy; infinite money,
  auto-heal, force wild species/level, guaranteed shiny wild), built on the bot's own
  debug_utilities write toolkit and gated on safe game state. Verified: 32/32 headless
  + 15/15 live-ROM byte checks (fabricated mons decode to exact species/level/shiny,
  valid checksum; money round-trips) + GUI screenshot. In-game effect pending a real
  save. Design + honesty: sandbox-pokebot/CHEATS-DESIGN.md.

## 2026-07-19 — Tabbed tool column + sprite species picker (sandbox, user feedback)
- Sandbox dashboard GUI: converted the tool column into a 5-tab interface
  (Play/Party/Stats/Cheats/Backups) so the handheld Pokéball drawer needs
  no scrolling; active tab persisted per profile; fixed a save/restore
  ordering bug on the tab state. Replaced the cheat force-wild-species text
  field with a searchable sprite dropdown (sprite+name button + filterable
  sprite-illustrated picker). Verified via py_compile, real-import,
  headless picker screenshots, and live-ROM screenshots of every tab +
  the handheld drawer.

## 2026-07-19 — Cheat species picker: show full dex by default (sandbox, user feedback)
- Removed the 60-row cap on the wild-species cheat picker; it now lists all
  386 Gen-3/Emerald species scrollable by default (typing still filters).
  Confirmed the species source is complete (386 unique, spot-checked
  legendaries/starters present). py_compile + headless screenshot verified.

## 2026-07-19 — Promote sandbox round into custom + fix stock-updater footgun
- Promoted ALL approved sandbox features into custom-pokebot (user-approved):
  backup/restore + cloud, macros, Patrol v3 multi-map/global-nav, gamepad +
  handheld menu-hide, shiny alerts, update notice, cloud save-sync v2, game
  cheats, tabbed GUI + XP bars + topmost dialogs + full-dex sprite picker.
  22 files (18 new, 4 modified); DIVERGENCE-LOG + DOCUMENTATION/02/03/04
  updated. Verified: py_compile, real-import + plugin discovery (no load
  errors), install.py --check-only, live launch of custom (tabbed GUI +
  cheats tab), git tracking of all new files. Commit f0b275f3.
- FIXED (footgun surfaced during promotion): stock auto-updater was active
  in the fork because pokebot.py only checked for `.git` inside the bot
  folder while ours is at the repo root — it would download a 40Cakes
  release over the fork. Guard now walks ancestors (custom + sandbox). ML-4.
- Refined 03-PUNCH-LIST (promoted items, first-wave direction) + wrote
  09-FEATURE-BRAINSTORM.md (curated future-feature catalog).
- Honest debt: #8/#12/#18/#20 + 2026-07-19 GUI polish had builder self-
  verification only (no independent adversarial pass) — verification sweep
  queued as the "Now" punch-list item.

## 2026-07-19 — Post-promotion verification sweep (independent adversarial pass)
- Two adversarial verifiers on the promoted-but-not-independently-verified
  features (custom-pokebot). 4 real bugs fixed:
  - warp_graph.py: corrupt/non-dict cache crashed the bot on first warp use
    → now rebuilds gracefully (medium).
  - global_navigation.py: navigate_to_anywhere counted per-frame non-
    overworld waits against its warp-leg budget → false route abort to
    Manual during long cutscenes; decoupled the counters (medium).
  - dashboard_gui.py: handheld-mode per-profile preference was overwritten
    to false on restore (tab-restore persisted before applying the saved
    flag) → Ally relaunched windowed; fixed (medium).
  - dashboard_gui.py: stale module docstring on dialog modality corrected.
- All batteries green (cloud-sync 23, alerts/update 21, backup, warp-graph
  23) + new adversarial batteries. Cloud-sync save-safety contract
  confirmed (save flushes before exit-sync; local never clobbered/rolled
  back). Two minor observations logged as KI-4/KI-5.

## 2026-07-19 — #30 handheld/GUI refinements + #31 adjustable money (sandbox)
- Persistent Handheld toggle in a header above the tabs (every tab); handheld
  drops the Tk menu bar entirely and surfaces its commands in a Play-tab GAME
  MENU card; new Left Party Section (6 icons left of the video, empty=Poké
  Ball, filled=mon over caught-ball composite) with index-based hover-stats
  tooltips (controller-ready for #32) on the strip AND party rows.
- #31 adjustable money cheat: editable field defaulting to current money, a
  Set action, and a Lock toggle that freezes money at the typed value.
- py_compile + real-import + unit tests + live-ROM screenshots verified;
  filled-slot composite + live hover need a progressed save.

## 2026-07-19 — Gamepad-driven GUI navigation (sandbox, #32)
- The controller now drives the dashboard GUI (focus ring across tabs/
  buttons/party, A=activate, B=back, LB/RB=tabs, D-pad/stick=move),
  distinct from in-game Manual input and mutually exclusive with it.
  Handheld: the open drawer is the nav context; desktop: Back+Start toggles.
  Focusing a party slot shows its stats tooltip (the controller "hover" the
  user asked for). modules/gui/dashboard_gui.py + modules/gamepad.py.
- Verified: 23/23 stubbed unit tests + live launch (focus ring on real
  widgets, no crash). Real-pad feel pending the user's Ally.

## 2026-07-19 — #33 GUI fixes (sandbox): left party always visible + unified show/hide
- Left Party strip now visible in handheld (was hidden behind the fullscreen
  video canvas — added lift()); stays visible on desktop including when the
  tool column is hidden.
- Desktop gains the handheld drawer's paradigm: a "Hide" button collapses the
  tool column (video fills the window), the Pokéball reopens it; state
  persisted per profile. Verified live (4 states screenshotted).
