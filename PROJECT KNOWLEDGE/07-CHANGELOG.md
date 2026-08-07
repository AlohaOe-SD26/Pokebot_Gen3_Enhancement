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

## 2026-07-19 — Dex data Phase 2: assemble static Pokédex/Item-Dex datasets (sandbox, #34/#35)
- tools/build_dex_data.py compiles modules/data/generated/pokedex_data.json
  (386 species) + itemdex_data.json (309 items) from the shipped data:
  types, stats, abilities, dex numbers, evolutions/family, wild held items,
  full learnset resolved to move names (level-up/TM-HM/tutor/egg), resolved
  sprite paths. Gap fields (dex artwork, flavor/height/weight/category,
  item map locations/mart/pickup) left null for Phase 3.
- Fact-check: 386/386 species + 309/309 items; referential integrity PASS
  (every move/ability/type/evolution/held-by resolves); species sprites
  386/386 exist; item icons 305/309 (4 obscure FR/LG keys have none).
  Caught bug: family/evolves_from/evolution targets are Gen-3 INTERNAL
  species IDs (array indices), not national-dex numbers — resolver fixed.
- Live counts (caught/shiny/held) stay runtime-merged from stats.db + save.

## 2026-07-19 — Watchdog / auto-recovery (sandbox, #22)
- modules/watchdog.py + plugins/watchdog_plugin.py + watchdog.yml + GUI
  STATUS line: detect encounter-stall / fault-drop-to-Manual / frame-freeze
  and auto-recover (re-assert mode → reload healthy savestate w/ safety
  backup → give up + loud alert). Safe-state gated, exception-guarded,
  disabled=inert. 17/17 headless battery + plugin discovery + backup
  regression green; live "Watchdog: OK" at 60 fps. Live-hunt recovery
  pending a progressed save.

## 2026-07-19 — Hunt Planner v1 (sandbox, #9)
- modules/encounter_index.py: species→where-to-hunt reverse index from the
  ROM's wild-encounter tables (per-ROM cached). GUI "Hunt" tab: pick a target
  → ranked locations (map, method, rate%, levels) + recommended bot mode,
  one click sets the mode. Reuses the sprite species picker (generalized to
  take a callback). Fact-checked 19/19 vs the real Emerald ROM (known
  encounters + no-wild for starters/legendaries); 132 species / 805 rows.
  Auto-travel-to-map deferred to v2 (needs a travel mode). Fixed a
  str.index name-resolution shadowing bug found in testing.

## 2026-07-19 — Fix tab overcrowd (KI-6) + Hunt Planner v2 auto-travel (sandbox, #9)
- KI-6 fixed: tab bar wraps to two rows for >4 tabs (legible desktop +
  handheld drawer).
- Hunt Planner v2: encounter_index.find_encounter_tile (reads map tiles
  from ROM to pick a walkable grass/water/fishing tile), hunt-target
  storage, and a new "Hunt (Custom)" bot mode that navigates to the tile
  via global nav then hunts (spin/fish). Hunt tab button = one-click
  travel+hunt. 15/15 v2 battery + live screenshots. Gap: live walk needs a
  progressed save.

## 2026-07-19 — Living-Dex orchestrator v1 (sandbox, #23)
- modules/living_dex.py (target-list derivation from encounter_index +
  pokedex owned flags, per-profile persistence) + plugins/custom_modes/
  living_dex_mode.py ("Living Dex (Custom)" mode: travel+hunt+catch each
  target then advance; catch-intent via on_battle_started; stop on
  exhausted/box-full) + a Living Dex card in the Hunt tab.
- Verified: 16/16 unit (derivation/sequencing/catch-intent), real-ROM
  fact-check (132 wild targets; starters/legendaries excluded), import +
  discovery + all-plugins-load, live in-process run. Gap: autonomous
  catch-and-advance needs a progressed save.

## 2026-07-19 — Analytics suite v1 (sandbox, #11)
- modules/analytics.py (pure) + Stats-tab ANALYTICS card: enc/hr sparkline,
  luck meter (actual vs binomial-expected shinies, 1/8192), and a pop-out
  sortable/filterable per-species stats browser with sprites. Sourced from
  stats.db. 26/26 unit tests + live screenshots. Live-meaningful data needs
  a populated stats.db (title-screen profile empty; verified via stub).

## 2026-07-19 — First-wave features + dex Phase 3a (all in sandbox, awaiting user)
- #22 Watchdog/auto-recovery (c7d25305), #9 Hunt Planner v1+v2 (6141d96f/
  4df17747; encounter index + travel-and-hunt + KI-6 tab-bar fix), #23
  Living-Dex Orchestrator (34c5f461), #11 Analytics suite (8094bb05; stats
  browser + trend + luck meter). Each self-verified (unit batteries + real-
  ROM fact-checks + live screenshots); live in-game behavior + independent
  adversarial pass pending (needs a progressed save + promotion).
- Dex Phase 3a (1b2ff82c): extracted category/height/weight/flavor for all
  386 species from the ROM's gPokedexEntries (national-dex indexed; offsets
  hex-verified; 0 mojibake; fact-checked exact). pokedex_data.json now only
  missing dex_artwork. Item-Dex still needs map_locations/mart/pickup +
  historical-tracking decision.

## 2026-07-19 — Auto-decline new move learning for leveling bots (sandbox, #39)
- battle.new_move default flipped `stop` → `cancel`: leveling bots now
  DECLINE new moves (keep moveset) instead of dropping to Manual, so hunts
  aren't interrupted. Single decision point (which_move_should_be_replaced,
  inherited by all leveling strategies); future move-intelligence seam
  documented in default.py. Verified: cancel→decline, stop→decline+Manual.
  Existing profiles need battle.yml new_move set to cancel.

## 2026-07-19 — Party visuals + gamepad-nav gating (sandbox, user adjustments)
- Larger party-strip balls (104px) with the caught-ball as a clear backdrop
  behind a bottom-anchored mon (#36); Pokémon-themed hover tooltip with type
  badges + color-coded IV grid + moves, replacing the plain text (#37);
  gamepad GUI-nav now only engages while the handheld Pokéball drawer is
  open — desktop toggle removed so it never interrupts gameplay (#38).
- Verified: py_compile + real-import + plugin/mode discovery; gamepad
  gating unit test; rendered screenshots of the enlarged ball composite +
  the themed tooltip. Filled-slot live view + controller feel need a real
  save/pad.

## 2026-07-19 — Poké Ball allowlist (#40) + larger party balls (sandbox)
- #40: catch_balls.py allowlist (default all-except-Master) filters
  catch.py's best-ball selection; CATCH BALLS GUI editor (icon checkboxes)
  in the Hunt tab; global + per-profile catch_balls.yml.
- #36 refine: party balls 104→140px, ball a bold backdrop behind the mon.
- Verified on the real Nick - Emerald save (screenshots; save md5 unchanged).

## 2026-07-19 — Living Dex opportunistic catching (#43, sandbox)
- Living Dex catches any un-owned planned species on sight (target only drives
  travel), per 11-LIVINGDEX-DESIGN. living_dex.is_wanted() +
  living_dex_mode.on_battle_started broadened, box-space-gated, outcome-gating
  implicit via live is_owned. 22/22 unit tests. Files: modules/living_dex.py,
  plugins/custom_modes/living_dex_mode.py.

## 2026-07-19 — #44 party ball: strip cleaned, ball moved to hover tooltip (sandbox)
- Left Party strip now shows clean, larger mon sprites (no ball-behind
  composite — the sizing was fighting the sprite). The caught ball moved to
  the hover tooltip as a proper icon+name row ("Caught in: <Ball>").
  Verified live on the real save (clean strip; save untouched, md5 match)
  + stub tooltip render (Ultra Ball icon + row).

## 2026-07-19 — Living-dex obtainability (evolution) + capability gating (sandbox, #41-evo/#42-easy)
- New modules/obtainability.py (evolution/wild classifier, internal-id) +
  modules/capabilities.py (save-readable Surf/rod/Rock-Smash/badge gate).
  living_dex now defers targets needing a missing capability (retried later)
  and exposes an obtainability breakdown; GUI Living Dex panel shows both.
- 30/30 offline units + live-verified on the real save (128 wild/147 evolve/
  102 special uncaught; rods detected; save md5-identical). Research half of
  #41 + #42-hard reachability still to do.

## 2026-07-19 — #41 obtainability research half: compiled + fact-checked (sandbox)
- Compiled the gift/static/roamer/in-game-trade/event/breeding/special/
  unobtainable lists for Emerald and folded them into the classifier, replacing
  the "unknown" catch-all. New data file `modules/data/emerald_obtainability.json`
  (National-Dex-keyed, Emerald-only). Fact-checked against the BPEE0 ROM's own
  `gWildMonHeaders` (the encounter index is complete — verified via the Safari
  extension) + Bulbapedia web checks; cross-checked the bot's own static/gift/
  roamer seeds.
- FINAL CENSUS (sums to 386): wild 132 · evolution 149 · gift 7 · static 8 ·
  roamer 1 · event 6 · breeding 3 · special 1 · unobtainable 79. Second honest
  denominator: 217/386 obtainable in Emerald WITHOUT trading (169 need a trade).
- `obtainability.classify()` now returns the real kind + `emerald_reachable`
  (recursive: evolution reachable iff base reachable AND no trade step);
  `plan_for()` gates wild hunting (`wild_huntable` True only for wild +
  evolution-with-wild-base — the bot never wild-hunts a gift/static/roamer/
  event/unobtainable species); new `obtainability.census()` + `ingame_trades()`.
- `living_dex.obtainability_breakdown()` now exposes the honest category split +
  BOTH denominators; the GUI Living-Dex panel shows "Owned N/386 · M/217
  obtainable in Emerald" and a gift/static/roam vs trade/event/blocked split.
- Verified: 16/16 new offline units (`tests/test_obtainability.py`) via the ROM
  header (no emulator boot). Key facts corrected against my own memory: Roselia/
  Meditite/Zangoose/Lunatone are TRADE-ONLY in Emerald; Surskit is swarm-only;
  Azurill is breeding-only; Wynaut IS wild (Route 130). Discrepancies flagged:
  Sudowoodo + Ho-Oh missing from the bot's static seed; Wynaut also a gift seed.
- Files: modules/obtainability.py, modules/data/emerald_obtainability.json,
  modules/living_dex.py, modules/gui/dashboard_gui.py, tests/test_obtainability.py.
  Full lists + citations + validation report: 11-LIVINGDEX-DESIGN.md (Phase #41-research).

## 2026-07-19 — Rulings + tooltip ball 3× + shiny opportunistic catch (sandbox)
- Latias+Latios both marked obtainable (roamer) per user ruling; obtainable
  denominator 217→218/386; test_obtainability updated, 16/16 pass.
- #46 hover tooltip caught-ball icon upscaled ~3× (24→54px via resize).
- #47 Living Dex catches any SHINY encounter even of an already-owned
  species (storage-gated); stub-verified.

## 2026-07-19 — PROMOTION BATCH-2 to custom (approved)
- Promoted the post-f0b275f3 sandbox round into custom-pokebot: #22 Watchdog,
  #9 Hunt Planner (encounter_index/hunt_mode/Hunt tab), #23 Living-Dex
  Orchestrator + #43 opportunistic + #47 shiny-of-owned, #41 obtainability
  model + census (218/386 obtainable, both denominators) + #42-easy
  capability gating, #11 Analytics, #40 catch-ball allowlist, #39 move-
  decline, the GUI evolution (#30-#38/#44/#46: tabs, handheld menu→Play,
  clean party strip + ball-in-hover 3×, gamepad-nav-gated, money+lock), and
  the generated dex datasets + tools (#34/#35 data foundation).
- 24 files promoted (17 new, 7 modified). Extensive intent-level docs:
  DIVERGENCE-LOG batch-2 entries + new DOCUMENTATION/05-hunting-and-livingdex
  + refreshed 02-custom-interface. Verified: py_compile, real-import +
  4 custom modes discovered, install --check-only, git tracking of all new
  files, live launch on the real "Nick - Emerald" save.

## 2026-07-19 — Batch-2 promotion + rulings/mods + story-mode design (Passes 1-2)
- Mods (c2707bad): Latias+Latios both obtainable (218/386), 3× tooltip ball
  (fixed a thumbnail no-op), opportunistic catch of any shiny incl. owned.
- PROMOTED batch-2 to custom (29b9aae5): watchdog, hunt planner, living-dex
  + obtainability/census + capability gating, analytics, catch-ball
  allowlist, move-decline, the GUI evolution, generated dex datasets — with
  extensive intent-level DIVERGENCE-LOG (a-i) + DOCUMENTATION/05-hunting-and-
  livingdex.md. Live-verified on the real Nick-Emerald save.
- Story-mode bot (#24) DESIGN Passes 1+2 → 12-STORYMODE-DESIGN.md: 25-chapter
  skeleton, verified (fixed Juan≠Wallace, HM04=Rusturf Tunnel, Brawly dark
  room; ADDED Mr.Briney/Mt.Pyre/Slateport-sub/Magma-Hideout; resolved all
  HM→badge gates + gym puzzles + intro symbols from the ROM). Found KI-7
  (fly_to wrong-badge bug). Build order: progress-detector → Gym1 → intro.

## 2026-07-20 — Story-mode design Pass 3 (accuracy triple-check)
- Cross-referenced every claim in 12-STORYMODE-DESIGN.md vs (A) the bot's
  ROM ground-truth (flags/vars/symbols/map/menuing badge-gates) and (B) an
  external Emerald walkthrough. Fixed 3 substantive errors incl. a Pass-2
  REGRESSION: HM06 Rock Smash is Mauville (not Route 111 as Pass 2 wrongly
  "corrected"); Fortree Gym (Ch15) needs the Devon Scope/Kecleon beat first
  (new row 14b); DELIVERED_DEVON_GOODS flag 149 = Slateport delivery not
  Rustboro return. Confirmed all 8 gyms/badges/HM-gates, late-game order,
  and the fly_to KI-7 bug. Sources agree post-fix. §9 audit table added.
  Verdict: high-confidence, safe to build against.

## 2026-07-20 — Story-mode design Pass 4 (independent re-derivation → CONVERGED)
- Re-derived gym/HM/key-item/chapter facts from scratch (ROM tables +
  menuing.py gates + 2-3 external walkthroughs), then diffed vs the doc.
  Found only 2 localized detail fixes (Petalburg Woods grunt = researcher
  rescue, Devon theft belongs to Ch5; HM01 Cut = Rustboro Cutter's House
  not Route 104). Pass 3's 5 corrections all re-confirmed (no regression).
  Resolved: Magma Emblem is a KEY ITEM (gate on bag, no flag); Mt. Pyre var
  = MT_PYRE_STATE(185). ROM vs external walkthroughs: ZERO disagreements.
  §10 audit added. VERDICT: strategic backbone CONVERGED, high-confidence,
  safe to build. Remaining unknowns are live-only (NPC tile ids, gym
  waypoints, intro timing) — engineering, not plot accuracy.

## 2026-07-20 — Fix KI-8 (party strip overlap) + KI-9 (controller stuck in menu)
Both fixed in sandbox, verified, and PROMOTED to custom (files were in sync;
only these edits differ). Live-launched on the real save "Nick - Emerald";
save md5 byte-identical after.
- **KI-8 — party strip too large.** `_PARTY_ICON_SIZE` 140 → 84 in
  dashboard_gui.py. After #44 moved the caught-ball to the hover tooltip the
  140px bare sprites were oversized and crowded the video. Screenshot confirms
  the left party column now sits clear of the emulator.
- **KI-9 — controller stuck "in menu."** Root cause: `toggle_handheld()`
  force-closed the drawer but never cleared `_gui_nav_active`, so leaving
  handheld while the drawer was open stranded the gamepad in GUI-nav mode —
  it kept stealing input and the game became unplayable. Fixes:
  1. `toggle_handheld()` now calls `set_gui_nav_active(False)`.
  2. Gamepad suppression is now DERIVED, not a cached flag: new
     `gamepad_gui_nav_engaged()` = (master toggle on AND handheld AND drawer
     open AND nav flag). `gamepad.py` calls it instead of reading
     `_gui_nav_active` directly, so the state can no longer desync.
  3. Safety valve: new "Controller GUI Control" master toggle (View menu
     checkbutton + F10 hotkey). Off = the pad is a pure game controller and
     Back+Start does nothing. Flipping off instantly drops any active GUI-nav.
  Verified by a headless state-machine battery (10/10 pass) covering the exact
  leak scenario and the toggle. (No physical-pad test available; logic-verified.)

## 2026-07-20 — Story-mode chunk 1: read-only progress detector (#24, sandbox)
New `modules/story/` package — the first buildable piece of the story bot:
- `chapters.py` — machine-readable registry of all 30 Emerald story chapters
  (0-24 + sub-chapters), each with a completion milestone (flag/var/**item**).
  `validate_registry()` confirms every name resolves (no emulator needed).
- `progress.py` — `detect_progress(reader)` → `StoryProgress` (current chapter,
  badges, HMs, objective, anomalies). Reads live memory (`detect_live()`) or the
  last save (`detect_from_save_data()`); writes nothing.
- `tests/test_story_progress.py` — 12 synthetic-reader tests, all pass.
- **Detection model (badge-anchored):** highest gym badge → chapter bracket →
  first unmet finer milestone within it. Robust to legit saves missing a stray
  flag AND to hand-edited saves with out-of-order flags/items. See design doc
  §12 + ML-5 for the two rejected strategies this replaced.
- Live-verified on the real `Nick - Emerald` save (a hand-built TEST save):
  correctly reports **ch5 (Devon errand), 1 badge**, and flags the stray Magma
  Emblem key item as an anomaly. Save `.sav` md5 unchanged (read-only).
- Sandbox only — new dev work, not promoted. Next chunk: Gym 1 (ch4) in
  isolation (design doc §6.3 step 2).

## 2026-07-20 — Story-mode chunk 2: Chapter 0 New Game intro AUTOMATED (#24, sandbox)
First piece of the story bot that actually PLAYS the game.
- `modules/story/intro.py` — `run_intro(name, gender)`: title screen → New
  Game → Professor Birch's speech → gender select → name entry → lands the
  player controllable INSIDE the moving truck. Task/GameState-driven, fully
  bounded (raises BotModeError instead of hanging).
- `modules/story/config.py` — reads name/gender from `<profile>/story.yml`
  (auto-writes a default template), 7-char cap, boy/girl.
- `plugins/custom_modes/story_mode.py` — `StoryMode` bot: fresh boot → runs the
  intro; existing save loaded → detects & reports the current chapter (chunk-1
  detector), then hands back to manual (chapters > 0 not built yet).
- Verified end-to-end on fresh throwaway profiles (never the real save):
  boy/NICK, girl/MAY, config/ASH — each lands in the truck with the correct
  name + gender; deterministic (~4600 frames). Real `.sav` untouched.
- Live facts captured in design doc §13 (drive by tasks not flags; Birch speech
  reads as MAIN_MENU state; gender is position-based; naming struct lag; first
  control = INSIDE OF TRUCK). Next chunk: step off truck → room/clock → Route
  101 rescue → choose starter → first battle.

## 2026-07-20 — Fix: Story mode couldn't be selected at the title/main menu (#24)
User hit this testing chunk 2: on a fresh, save-less game at the main menu the
Story mode showed but was greyed out. Root cause: both mode pickers
(`dashboard_gui.py:_open_mode_menu`, `emulator_controls.py`) force EVERY mode
to non-selectable while game_state is TITLE_SCREEN/MAIN_MENU (stock modes all
need an in-game overworld). But Story mode is designed to start there.
- Added `BotMode.is_selectable_from_title_screen()` (default False) as an
  opt-in; `StoryMode` overrides it to True.
- Both pickers now, at the title/main menu, offer modes where
  `is_selectable_from_title_screen() and is_selectable()` — so only Story is
  available there; all other modes stay greyed as before.
- Verified via the custom-mode loader: Story is selectable at title, sibling
  custom modes (Hunt/etc.) are not. Main loop has no game-state gate, so once
  selected the mode runs. Sandbox only.

## 2026-07-20 — PROMOTED Story Mode (chunks 1-2) to custom (#24)
User tested the Chapter 0 intro live on real hardware ("worked perfectly") and
approved promotion. Copied sandbox → custom: modules/story/ (detector + intro +
config + registry), plugins/custom_modes/story_mode.py, tests/
test_story_progress.py, modules/modes/_interface.py
(is_selectable_from_title_screen), and the two mode pickers (dashboard_gui.py,
emulator_controls.py) with the title-screen selection fix. Verified in custom:
compile clean, 12/12 story tests, live intro smoke test lands NICK/male INSIDE
OF TRUCK. DIVERGENCE-LOG (j) + DOCUMENTATION/01-custom-automations.md updated.
Sandbox and custom are now in sync for all story files.

## 2026-07-20 — Story-mode chunk B part 1: step off truck → into the house (#24, sandbox)
`modules/story/early_game.py` `walk_off_truck_and_into_house()`: from the truck,
walks out east into Littleroot, rides Mom's greeting cutscene (escort + warp
into the house + her speech), and stops controllable inside PlayersHouse_1F at
(8,7). Robust cutscene-end detection (controllable AND no-script for 15
consecutive frames — a 1-frame check stopped too early). Wired into StoryMode
after the intro. Verified from the truck-parked base and full-run from a fresh
profile. Map facts + next steps in design doc §14. Sandbox only; next: B2
(upstairs → set clock).

## 2026-07-20 — PROMOTED story chunk B part 1 (step off → into house) to custom (#24)
User tested it live ("worked perfectly"). Copied early_game.py + the wired
story_mode.py sandbox → custom; verified in custom (compile + full fresh-run
smoke test lands NICK/male inside PlayersHouse_1F (8,7)). DIVERGENCE-LOG (j) +
docs updated. Sandbox == custom for story files again.

## 2026-07-20 — Story chunk B part 2: upstairs + set the clock (#24, sandbox)
`early_game.go_upstairs_and_set_clock()`: 1F stairs → 2F bedroom → interact
with the wall clock (5,1) → accept the default time (A) → confirm Yes (the
confirm cursor defaults to NO, so Up+A). Ends controllable on 2F. Wired into
StoryMode after step-off, so a new game now runs intro → house → clock. Tested
from the clock checkpoint and full fresh run (lands NICK/male on 2F). Downstairs
→ exit is next; the 1F Vigoroth "movers" scene blocks pathfinding and needs
handling (design §14.1). Sandbox only.

## 2026-07-20 — PROMOTED story chunk B part 2 (upstairs + clock) to custom (#24)
User tested it ("setting the clock worked!"). Copied early_game.py + wired
story_mode.py sandbox → custom; verified in custom (fresh-run smoke test lands
NICK/male on 2F, clock set). DIVERGENCE-LOG (j) + changelog updated.

## 2026-07-20 — Story chunk B COMPLETE: downstairs + rival's house (#24, sandbox)
`early_game.descend_and_leave_players_house()` + `visit_rivals_house()`: after
the clock, ride out Mom's upstairs chat + the Petalburg-Gym TV scene, leave the
house, enter the rival's house (mom greets automatically), go up, touch the
Poké Ball to trigger the rival's introduction, and come back outside. Wired the
full chain into StoryMode. Full fresh-run verified: intro → house → clock →
downstairs → rival's house → meet rival → outside (Littleroot 14,9), NICK/male,
~11,800 frames. Key lesson: ride out auto-move scripts, never navigate during
them (the phantom "(8,4) block" was the TV scene). Map facts in design §14.2.
Sandbox only. Next chunk: Route 101 → starter → first battle.

## 2026-07-20 — Sandbox launches with audio off by default (#testing)
Added `install.LAUNCH_EXTRA_ARGS` (default empty; custom unaffected); the sandbox
wrapper sets it to `["--no-audio"]` so the sandbox test build starts quiet
(audio stays toggleable in-GUI). install.py + install_sandbox.py.

## 2026-07-20 — PROMOTED story chunk B (downstairs + rival's house) to custom (#24)
User tested ("worked perfectly!"). early_game.py (descend + visit_rivals_house)
+ wired story_mode.py copied sandbox → custom; verified (fresh run → Littleroot
14,9). Divergence log + changelog updated.

## 2026-07-20 — Story Chapter 1: Route 101 → random starter → first battle → lab (#24, sandbox)
`early_game.help_birch_and_choose_starter()` (+ `_go_north_to_birch_rescue`,
`_choose_starter`): walk north → Birch rescue on Route 101 → open the bag →
choose a starter (config: random/treecko/torchic/mudkip) → win the first battle
(BattleListener; StoryMode.on_battle_started→Fight) → arrive in Birch's lab.
Order of operations verified in-game first. Config added: `starter` +
`starter_nickname` in story.yml (nickname application TODO). Full fresh run with
real listeners verified: 15,425 frames → NICK/male, random starter Lv5, in
Birch's lab (1,4); random produced all 3 starters across runs. Detailed
step docs in design §15. Sandbox only. Next: finish lab → Oldale → train Lv8-10
→ rival battle.

## 2026-07-20 — Story: finish Birch's lab conversation (#24, sandbox)
`early_game.finish_birch_lab()`: answers the "give a nickname?" prompt (Yes/No
handler; B can't dismiss it), then advances the give-starter script to its end
by waiting for it to leave the stack while mashing A (stops before re-triggering
Birch's repeatable dialogue). Wired into StoryMode after help_birch. Nickname
application GATED OFF (types but doesn't persist; user-deprioritised) — always
keeps the species name; config kept for the future fix. Verified: Torchic Lv5,
controllable in the lab. Also: sandbox pokebot.py now forces audio off at
startup (reliable regardless of launch). Design §15.1.

## 2026-07-20 — Story: shiny contingency for the first battle (#24, sandbox)
StoryMode.on_battle_started() now explicitly logs and fights-through a shiny
wild in a story battle (never catches, never stops) — the story must progress
even in the rare event the scripted first-battle wild is shiny. Safe because the
default shiny-halt/catch lives in handle_encounter(), only reached when
on_battle_started returns None; returning Fight bypasses it. Unit-tested. §15.2.

## 2026-07-20 — PROMOTED story Chapter 1 (starter → first battle → lab) to custom (#24)
User tested ("worked perfectly!"). Copied early_game.py + config.py + story_mode.py
sandbox → custom (NOT the sandbox-only audio change); verified full fresh run
→ Birch's lab with starter Lv5, first battle won, shiny contingency in place.

## 2026-07-20 — Fix: finish_birch_lab was stopping mid-conversation (#24, sandbox+custom)
The lab has TWO events: GiveStarterEvent then GoSeeRival (Birch asks you to find
the rival on Route 103, a Yes/No — answer Yes; No keeps you stuck). finish_birch
_lab() only handled the first, leaving a live Yes/No when it handed to manual.
Now handles both; ends with the player controllable and able to walk out (script
inactive). Pokédex confirmed NOT given here (comes after the rival battle).
Verified full fresh run → clean handoff. Fixed in sandbox + custom.

## 2026-07-20 — Story Chapter 1 COMPLETE: travel, train Lv8-10, beat the rival (#24, sandbox)
travel_to_route103 + train_lead_to_level + fight_route103_rival. A fresh game
now plays through the first rival battle: north to Route 103 (fighting wilds en
route), grind to a random Lv 8-10 with Oldale Poké Center healing, heal to full,
beat the rival. Fixes: use LevelUpLeadBattleStrategy (DefaultBattleStrategy fled
wilds → no XP); hard-target PokemonCenter.OldaleTown (find_closest_pokemon_center
is broken); heal-to-full before the rival (trainer battle can't be fled).
StoryMode.on_battle_started → LevelUpLeadBattleStrategy. Verified piecewise with
real listeners. Design §15.3. Sandbox only.

## 2026-07-20 — PROMOTED story Chapter 1 completion (travel/train/rival) to custom (#24)
User tested ("that worked!"). early_game.py + story_mode.py copied sandbox →
custom; verified in custom (12/12 story tests; train+rival from Route 103 →
DEFEATED_RIVAL_ROUTE103 True, Mudkip Lv8, clean). Chapter 1 fully in custom now.

## 2026-07-20 — Story: return to lab + receive the Pokédex (#24, sandbox)
`early_game.return_to_lab_and_get_pokedex()` + `_navigate_through_scripts()`
helper: head back to Birch's lab after the rival (riding out the Oldale rival
intercept), receive the Pokédex + Poké Balls. Wired into StoryMode. Verified
from the post-rival checkpoint (SYS_POKEDEX_GET True). Design §16. Sandbox.

## 2026-07-20 — PROMOTED Pokédex sequence to custom (#24)
User tested ("runs perfectly to the PokeDex"). return_to_lab_and_get_pokedex +
_navigate_through_scripts copied sandbox → custom; verified (SYS_POKEDEX_GET
True). StoryMode in custom now plays fresh game → rival → Pokédex.

## 2026-07-20 — Story: travel to Petalburg City (fixed + wired) (#24, sandbox)
travel_to_petalburg now works: _navigate_leg to Oldale (past the Route 101 loop),
then navigate_to_anywhere(PETALBURG) from Oldale. Wired into StoryMode (fresh
game now plays through to arriving in Petalburg). Verified with listeners
(pokedex_done -> Petalburg, 22.1k frames). Petalburg Gym / Dad-Wally findings
captured in design §17 for the next build. Sandbox.

## 2026-07-20 — PROMOTED travel to Petalburg to custom (#24)
User tested ("got to Petalburg fine from a fresh save"). travel_to_petalburg +
_navigate_leg copied sandbox → custom; verified (reaches Petalburg (0,0)).
Custom StoryMode now plays fresh game → rival → Pokédex → Petalburg City.

## 2026-07-20 — Story Chapter 2: Petalburg Gym (Dad) + Wally catching tutorial (#24, sandbox)
do_petalburg_gym_and_wally_tutorial(): enter the gym, fire the Norman scene at
(4,108), ride out the fully-auto Wally tutorial (Route 102 Ralts catch + back).
Completion = back in the gym + controllable after visiting Route 102 (the
THANKED_FOR_PLAYING_WITH_WALLY flag is NOT set by this tutorial). Wired into
StoryMode. Verified via the listener-driven harness. KEY LESSON: test story
steps via the listener harness, not a bare next()+run_frame loop (stale state
cache gives wrong results). Design §17.1. Sandbox.

## 2026-07-20 — PROMOTED Chapter 2 (Petalburg Gym + Wally tutorial) to custom (#24)
User tested ("it worked"). do_petalburg_gym_and_wally_tutorial copied sandbox →
custom; verified via listener harness (petalburg.ss1 -> done, visited Route 102,
back in gym). Custom StoryMode now plays fresh game → ... → Dad + Wally tutorial.

## 2026-07-20 — Fix: dashboard "Hide" threw a Tkinter TclError (#gui, sandbox+custom)
`_pokeball_button.lift()` errored because it's a Canvas (Canvas aliases both
lift AND tkraise to tag_raise, which needs a tag). Replaced with
`tkinter.Misc.tkraise(self._pokeball_button)`. Non-fatal but noisy; fixed in
both builds. See ML entry.

## 2026-07-20 — Story: Petalburg -> Route 104 -> Petalburg Woods travel (#24, sandbox)
Added `travel_to_petalburg_woods()` (modules/story/early_game.py): heal at
Petalburg PC -> cross WEST to Route 104 riding out the one-time Scott cutscene
-> fight the Route 104 trainer -> enter the Woods south door. Added
`LevelUpTravelBattleStrategy` (no-flee for trainer battles; fixes the single-mon
flee-crash, ML-8) and wired both into StoryMode. Verified deterministically via
the listener harness (fresh gym save -> Petalburg Woods, 6251 frames, x2).
Map facts (collision grid, Scott script, Woods warps, door quirk) in design §16
/ ML-7 / ML-8. Sandbox-only; not yet promoted.

## 2026-07-20 — Story: cross Petalburg Woods -> Route 104 north (leg 3) (#24, sandbox)
Added `cross_petalburg_woods()` (early_game.py), wired into StoryMode. Crosses
the Woods maze: ~3 Bug-Catcher trainers fought inline + the mandatory Devon-
researcher/Aqua-grunt cutscene ridden out (grunt battle handled by the listener,
researcher gives a Great Ball), then exits the north warp onto Route 104 north.
Verified deterministically via the listener harness (woods_entered.ss1 -> Route
104 north, 16123 frames, x2). Recon via the new tools/mapdump.py. Documented a
harness-fidelity rule (per-frame state refresh; companion to ML-5) in design §16.
Sandbox-only; not yet promoted.

## 2026-07-20 — Story: Route 104 north -> Rustboro City (leg 4) (#24, sandbox)
Added `travel_route104_north_to_rustboro()` (early_game.py), wired into StoryMode
(now ends "reached Rustboro City"). Route 104 north connects directly to Rustboro
(no warp split) so a single navigate routes it (no-flee strategy for any route
trainers). Verified deterministically (route104_north.ss1 -> Rustboro (20,42),
3166 frames, x2) using the reusable harness (tools pattern) with per-frame state
refresh. Checkpoint rustboro.ss1. Sandbox-only.

## 2026-07-20 — Story: GYM 1 (Roxanne) — Stone Badge (#24, sandbox)
Added `do_rustboro_gym()` (early_game.py), wired into StoryMode. Heals at the
Rustboro Poké Center, enters the gym, navigates up to Roxanne fighting the two
gym Youngsters inline (no-flee strategy), then challenges Roxanne (face-up + A)
and rides out the battle+dialogue until BADGE01_GET. Verified deterministically
(rustboro.ss1 -> BADGE01_GET True, 21505 frames, x2; Mudkip Lv13->16, won at
21 HP). **A fresh game now auto-plays all the way to the Stone Badge.** Starter
caveat: verified with Mudkip (ideal); Torchic (Fire, weak to Rock) is an open
TODO. Checkpoint gym1_done.ss1. Sandbox-only.

## 2026-07-20 — FIX: Petalburg Woods stall (door warp) — real-bot repro (#24, ML-9)
User-reported: Story mode got stuck in Petalburg Woods in the real bot (all my
tests passed). Root cause (ML-9): (1) fragile door entry — hand-stepping onto the
warp tile with single-frame presses + per-frame map checks was flaky (warp didn't
fire → BotModeError → main.py switches to Manual = "stuck"); (2) my test harness
read player/map every frame, which masked it. Fix: new `_pass_through_door(tile,
from_map)` warps by navigating ONTO the door tile (like heal_in_pokemon_center);
replaced the hand-stepping in both Woods doors. Re-verified with a MAIN.PY-FAITHFUL
harness (no per-frame state reads, catches BotModeError): full chain wally_done ->
Woods -> cross -> Rustboro -> Gym 1 -> BADGE01_GET True, no error, 46590 frames.
The south-door fix also applies to CUSTOM (leg 2 was promoted).

## 2026-07-20 — Story: smart move-learning policy (keep Pokémon combat-capable) (#24)
User-reported gap: the bot got the "learn a new move / delete an old one?" prompt.
Stock config default is `new_move: cancel` (decline everything → starter never
improves). Added `LevelUpTravelBattleStrategy.which_move_should_be_replaced()` (a
decision override, so the config gate is bypassed for Story battles). Policy:
never touch HMs/banned moves; NEVER replace a damaging move with a status move
(guarantees a Pokémon can't end up with only non-combat moves); a new status move
only overwrites an existing status slot (else decline); a new damaging move
upgrades a status slot first, else preserves type coverage (redundant new type ->
only upgrade a weaker same-type move else decline; new-type coverage -> free a
redundant slot first, else drop the weakest). Effective power = base x Atk/SpAtk x
STAB. Unit-verified with real game objects across both branches (status-slot and
all-damaging kits) — sensible, coverage-preserving, combat-guaranteeing decisions.
Applied to BOTH builds (the strategy is promoted). Status-move UTILITY ranking is
a future refinement (#24-team).

## 2026-07-20 — Story: resume-from-anywhere (v1) + fix Wally detection flag (#24)
User-reported: resuming a save (they were in Petalburg Woods) mis-detected as
"still needs Wally". TWO fixes: (1) chapters.py Ch2 milestone changed from the
never-set THANKED_FOR_PLAYING_WITH_WALLY to HIDE_PETALBURG_CITY_WALLYS_MOM (the
real post-tutorial signal — Wally's mum leaves; found by flag-diffing pre/post
saves). (2) StoryMode.run() rebuilt as SEGMENTED resume: runs each segment only
if its completion flag isn't set, so a fresh game runs all, a resumed/hand-played
save skips what's done and continues; the Woods segment picks its sub-entry by
current map (no backtrack). Verified: gym1_done skips all -> manual;
woods_entered skips intro+Wally and resumes the crossing; petalburg skips intro.
Design §RS. Refinements (per-step resume, fly/teleport fast-travel, title Continue)
= punch-list #24-resume. Sandbox-only (depends on unpromoted legs 3-4 + gym).

## 2026-07-20 — Story: Chapter 5 (Devon errand) FULLY RECONNOITERED (#24, not built)
Mapped the whole post-Gym-1 Devon Goods chapter live from gym1_done: theft scene
trigger (RustboroCity_EventScript_StolenGoodsScene @ ~23,20 → DEVON_GOODS_STOLEN),
the Devon-employee director (EmployeeAskToGetGoods @ 30,9), the chase path
(Rustboro E → Route116 → Rusturf Tunnel WEST door Route116 (47,8) → tunnel 4,10),
tunnel warps, the grunt battle → RECOVERED_DEVON_GOODS + Peeko, and the return →
Devon Corp → RECEIVED_POKENAV. KEY LESSON: the theft cutscene has mid-scene
controllable windows → needs a FLAG-ANCHORED ride-out (press until
DEVON_GOODS_STOLEN), not the generic one (which thrashes _navigate_through_scripts).
Full plan in design §Ch5. Checkpoint post_theft.ss1. Build deferred to a fresh
session (context length) to keep quality high.

## 2026-07-20 — GUI: paginate the Load Save State popup (both builds, #24-loadpage)
The load-state popup eagerly decoded EVERY save-state screenshot (up to 128 PNGs)
on open, so a full states/ folder made it crawl (user-reported, original repo).
Rewrote load_state_window.py to paginate: 5 states/page, lazily rendering ONLY the
current page's thumbnails (Prev/Next + arrow/PageUp-Down keys + "Page X/Y (N
states)" label; nav auto-hidden for a single page; per-page PhotoImage refs freed
on flip). Opens instantly regardless of folder size. Applied to sandbox + custom;
40cakes mirror untouched. Also NOTED (not built) #24-autosave: auto chapter
save-state in sandbox with a Play-tab toggle (default on) — apply after the user
green-lights the current story build.

## 2026-07-20 — Design: DEFEAT RESPONSE system (#24-defeat, design only)
Documented what the bot should do when it LOSES a battle (user request), as a
settings-popup choice: (A) "Reload save state" (today's watchdog behaviour made a
toggle — note: the segmented resume §RS already fixes most of the "picks up from
an earlier state" problem, since the old run() stranded the bot on any restart;
also require watchdog snapshots to be clean overworld states) and (B) "Play
through & retry" (ride out the whiteout → respawn → recalc position + story
segment via §RS → matchup-assess avg level/team-size/type coverage → train/adjust
team #24-team if outmatched → escalate on repeated loss → retry). Mode B = §RS +
matchup gate + #24-team on one engine. Design §DR; punch-list #24-defeat. No code
changed (user is testing the current story build).

## 2026-07-20 — Fix(hypothesis): enable evolution to clear the Lv16 move-learn hang (#24, both builds, ML-10)
User: Treecko Lv16 (learns Pursuit) HANGS without stopping the bot. Lv16 is both
the evolution level and a move-learn; with stock stop_evolution the evolution is
cancelled and the cancelled-evolution + move-learn handoff can spin (code trace;
not yet reproduced — checkpoints won't reach Lv16 in a test run). Applied
LevelUpTravelBattleStrategy.should_allow_evolution -> True (starter evolves via
the well-tested path; also stronger for gyms, #24-evo). NEEDS USER VERIFICATION
on a real Treecko run; fallback (handle_battle AskToLearnMove-vs-EvolutionScene
precedence) documented in ML-10 if it still hangs.

## 2026-07-20 — Story: self-correction v1 — per-segment completion guard (#24-sanity, sandbox)
"Story mode needs to be smarter" (user). StoryMode.run() now runs a _guard() after
each segment: if the segment didn't reach its completion signal (flag/map) it
raises a diagnostic BotModeError naming where it actually is (→ Manual), instead
of blindly proceeding and compounding a derail — re-running Story then resumes
correctly from the real state (§RS). Also catches a gym/battle LOSS (blackout ->
not in the expected state -> guard fires -> recover on re-run). Verified no
false-fire on the happy paths (gym1_done all-skip; woods/petalburg resumes).
Design §SC. Remaining (#24-sanity): bounded auto-retry, self-locate, mid-segment
stall watch for the battle-handler hang class. Sandbox-only (part of segmented run).

## 2026-07-20 — FIX (real): Lv16 move-learn hang — battle handler exited early (#24, both builds, ML-11)
User: starters hang learning a move at Lv16 (pre-evolution); persisted after the
evolution-enable attempt. REPRODUCED with a debug Treecko Lv15 in a TRAINER battle:
pure move-learn hang (AskToLearnMove repeats, evolution task INACTIVE), flaky
(~50%), only in trainer battles. Root cause: handle_battle's `while
battle_is_active()` exits the frame the move-learn surfaces as the battle ends,
leaving the "Delete which move?" prompt unhandled. Fix (modules/battle_handler.py,
STOCK file — divergence): loop while battle_is_active() OR a move-learn/evolution
dialogue is pending, and dispatch move-replacement when the learn dialogue is
active even if the instruction moved on. Verified: trainer repro 4/4 clean (learns
Pursuit + evolves to Grovyle); wild path unchanged. Corrects ML-10 (evolution was
a red herring; should_allow_evolution=True kept as a feature).

## 2026-07-20 — FIX(2): Lv16 move-learn hang — evolution/move-learn guard-loop + hang-proof safety (#24, both builds, ML-11)
User re-reported the Treecko-Lv16 "stuck learning Pursuit" hang after the first
fix. Deep-traced the move-selection interface (debug Treecko Lv15 + real trainer
battle): my repro SELECTS THE CORRECT move (slot 1 = Leer) and completes — could
NOT reproduce the user's hang (likely a timing/speed-specific state; user runs at
32x). Two additional robustness fixes: (1) battle_handler dispatch — an evolution
scene that's NOT at its move-learn substate now routes to handle_evolution_scene
(which advances it), never the move-replacement handler (which breaks out while an
evolution task lingers → a re-dispatch spin, the likely remaining cause); (2)
handle_move_replacement_dialogue now has a bounded SAFETY (5000-frame budget) that
backs out with B if the move-learn UI ever stalls, so the bot can NEVER hard-freeze
on that screen. Verified no regression (gym repro 4/4 still learns Pursuit +
evolves; safety never false-triggers). Both stock files → DIVERGENCE-LOG.

## 2026-07-20 — FIX(3): battle no-progress watchdog — guarantee no hard-freeze (#24, both builds, ML-11)
User re-tested the current build and the Lv16 move-learn STILL hard-froze (so the
per-call move-dialogue safety wasn't enough — the spin is in handle_battle's LOOP,
which had no bound). Added a NO-PROGRESS WATCHDOG to handle_battle: if the progress
signature (battle instruction + main callback + learn-move state + party total EXP)
is unchanged for 6000 iterations, escape any menu with B and bail out of the battle
loop, returning control to the mode (whose §SC self-check recovers). Party EXP in
the signature means the long GiveExp bar-fill never false-triggers it. Verified no
regression + no false-trigger (gym repro 3/3 clean). Still could NOT reproduce the
exact hang in-harness (flaky race; user runs 32x) — this GUARANTEES it can no longer
HARD-freeze regardless of cause. Also noted #24-textread (read text-box text to
drive fragile interactions deterministically — user idea).

## 2026-07-20 — FIX(4, ROOT): Lv16 move-learn hang — robust YES/NO answering (#24, both builds, ML-11)
User pinpointed it: freezes at the "Delete a move to learn PURSUIT? YES/NO" prompt.
ROOT CAUSE: handle_move_replacement_dialogue BLIND-SPAMMED A/B to answer — which is
exactly what the game's own wait_for_yes_no_question warns against: spamming a
button to skip text ALSO gets registered as the Yes/No answer, so it can land on NO
(→ never reaches the delete screen), and the code then waited for a FIXED next-state
(SelectMoveToReplace) that never comes → hang. FIX: answer the Yes/No (and the
delete-confirm) ONLY when is_waiting_for_input() is true (matches the game's robust
yes/no pattern), and don't wait on a fixed next-state — the outer state machine
follows whatever comes, so a stray transition course-corrects (user's idea) instead
of hanging. Verified 4/4 learns Pursuit + evolves; no regression. The battle
no-progress watchdog (FIX 3) remains as a backstop.

## 2026-07-20 — FIX(5, VERIFIED): move-learn hang — direct presses + multi-move re-decide (#24, both builds, ML-11)
FINALLY reproduced reliably: a Pokémon learning MULTIPLE moves at one level (debug
Castform Lv9->10 learns 3) hung 100% at the "Delete a move? YES/NO". ROOT: (a) my
prior is_waiting_for_input() gating was WRONG in battle — battle text doesn't use
the field text-printer it checks, so it was always False and the bot NEVER pressed
-> hang; (b) the fallback pressed B in the preceding text boxes, which mis-answers
the Yes/No as NO -> decline; (c) the decision was locked to the FIRST offered move,
breaking multi-move. FIX: answer with direct presses (A=YES/learn, B=decline; the
state itself confirms the menu is up), advance the preceding text with A (premature
= YES = safe for learn, not B), and RE-DECIDE whenever the offered move changes so
each of several moves gets the right slot. Verified: Castform learns all 3 moves
3/3 (no hang); Treecko single-move + evolution unchanged. Backstops (per-call safety
+ handle_battle no-progress watchdog) remain.

## 2026-07-20 — Move-learn: TEXT-DRIVEN detection (read what the game says) (#24, both builds)
Confirmed the bot can decode on-screen text: decode_string(read_symbol(
"gDisplayedStringBattle")) reads the exact battle text (e.g. "Delete a move to
make room for WATER GUN?"). Made the move-learn robust to the flaky task/state
detection by ALSO detecting it from the text: handle_battle dispatches to the
move handler whenever move-learn text is showing (never falls through to a stray
B-press), and the handler keeps advancing with A while move-learn text is on
screen even if the state lags. Verified no regression (Castform 3-move + Treecko
single-move). Groundwork for the broader Dialogue-Awareness system (design §DA,
punch-list #24-textread).

## 2026-07-20 — Move-learn: dispatch PRIORITY fix + live stall diagnostic (ML-12, both builds)
The Lv16 move-learn STILL froze on the real 32× run despite every prior fix
passing the offline harness. Found a concrete dispatch-order bug in
`handle_battle`: the action-selection branch (`get_main_battle_callback() in
("HandleTurnActionSelectionState","sub_8012324")`) was checked BEFORE the
move-learn branch, so when that callback lingered while the post-battle "Delete a
move to make room for X?" prompt was up, the frame was consumed by
action-selection and the prompt was never dispatched to the move handler -> the
exact reported hang. FIX: reordered the dispatch so a move-learn (`AskToLearnMove`
or `_move_learn_dialogue_active()`) and an in-progress evolution scene are handled
FIRST, before action selection, item-steal, and pay-day. Also added
`_dump_battle_stall_diagnostic()`: when the in-battle no-progress watchdog trips
(~100s unchanged), it snapshots the EXACT frame — battle text, field text, script
instruction, main callback, move-learn state, and which menu tasks are active — to
the console and `<profile>/battle_stall.log`, so a persisting freeze finally yields
a precise report (closes the harness-vs-real gap, design §DA). Both builds compile;
awaiting user re-test on the real environment. The move-learn text detection was
already universal (generic phrase match + dynamic offered-move read), per the
user's "make it somewhat universal" note.

## 2026-07-20 — Lv16 move-learn hang FIXED at the root (text-driven handler, ML-13, both builds)
Found and fixed the real cause of the Treecko-Lv16 "Delete a move to learn Pursuit?
YES/NO" freeze. The Emerald BATTLE Yes/No has no backing task, so the old code could
only detect it by a fragile script-offset; when that offset never matched, the state
stayed Unknown and the fallback pressed A only when is_waiting_for_input() (the FIELD
printer, unreliable in battle) — so it pressed nothing and froze on the prompt.
Rewrote `handle_move_replacement_dialogue` to be fully TEXT/TASK-driven (design §DA):
the Yes/No is detected from the on-screen text ("make room for"/"Delete a move"), the
move-select from the reliable input task, and every other text box is advanced with A
directly (no is_waiting_for_input gate). Hardened `handle_evolution_scene`'s hand-off
the same way. Reproduced the exact hang with a faithful main.py-loop headless harness
plus FAULT INJECTION (force the fragile state Unknown + is_waiting_for_input False):
old code stalls ~10,600 frames and fails to learn the move; the fix resolves in 394
frames, learns Pursuit, evolves to Grovyle, sensible moveset — verified on BOTH
sandbox and custom. The earlier ML-12 dispatch reorder was a red herring (A/B
byte-identical) but is kept as harmless defence. Repro tool: scratchpad/repro_movelearn.py.

## 2026-07-21 — Story Chapter 5a: recover the Devon Goods (sandbox, BUILT + verified)
Built `recover_devon_goods()` (early_game.py) + wired as StoryMode Segment 5a (gated by
RECOVERED_DEVON_GOODS). After Gym 1 the Devon Goods are stolen; the bot walks Rustboro to
trigger the theft (anchor DEVON_GOODS_STOLEN), chases east onto Route 116 and across to the
Rusturf Tunnel west door (47,8) via _pass_through_door, then approaches the tunnel grunt at
(13,5) from the west and engages WITH A (B skipped the challenge) — the listener fights the
grunt, the goods are recovered and Mr. Briney frees Peeko. Every step live-verified via a
faithful main.py-loop harness from gym1_done.ss1: RECOVERED_DEVON_GOODS=True at ~f31858,
clean finish, Mudkip→Marshtomp evolved mid-chase (handled cleanly by the move-learn/evo fix).
Corrected geometry (mapdump): Devon Corp warps (11,15)/(12,15); Route116 far tiles have no
path (ledges) so target the west edge then let the global navigator cross to the door;
grunt blocks the corridor so don't pathfind past it. Checkpoint goods_recovered.ss1.
SANDBOX ONLY (Chapter 5b return→PokéNav + Rustboro rival still to build; design §Ch5).

## 2026-07-21 — Story DEFEAT / WHITEOUT recovery (sandbox, user directive) — no more save-state reloads
User #1: on defeat the bot must navigate the whiteout and continue from the respawn
point, never reload a save state (the watchdog was rewinding to older and older
states). Built (both parts verified from rustboro.ss1 with an injected lone Lv3
Poochyena that lost to Roxanne 7× and recovered every time, staying in Story mode,
no reloads, no Manual):
- Watchdog neutered for Story: `_SELF_RECOVERING_MODES = {"Story"}` — the watchdog
  never reloads a save state or auto-restarts for Story (modules/watchdog.py).
- StoryMode recovery: `on_whiteout()` flags an abort + returns True (never Manual);
  `run()` wraps the segmented resume (`_play`) in a restart loop that, on the
  post-whiteout derail, steps out of the Poké Center (`exit_building_after_whiteout`:
  respawn lands ON the exit warp (7,8), so walk above it then step down to fire it),
  waits for a stable started+overworld state (a warp transiently reads "not started",
  which had misfired the New-Game intro), and re-runs from the respawn.
  `on_battle_ended(Lost)` counts consecutive losses per LOCATION (map) for the
  retrain trigger. A shared `_STORY_ABORT` flag makes long in-segment loops bail fast.
Next: retrain-on-2nd-loss + pre-fight level thresholds + pre-gym catching. Sandbox only.

## 2026-07-21 — Story pre-fight training, retrain-on-loss, and pre-gym catching (sandbox)
Completes the user's #1 (defeat handling) + #2 (team-building) requests.
- train_team(target, scope, grass, heal) — grinds wilds until the team hits target;
  scope 'whole' rotates the lowest battler to lead, 'lead' trains only the lead.
- StoryMode._prepare_for_fight(cfg) before Gym 1: PROACTIVE target within the band
  (random, organic); REACTIVE escalation if lost here >=2× (the "+levels" strategy
  and team scope both randomized, per user, for organic variety). Roxanne band 13-17.
- catch_starter_team(target_size) + on_battle_started catch branch: catch NEW species
  (never a dup — compares by national dex #) before the gym until the party fills to
  4 (starter + 3), stopping if low on balls.
Verified: rustboro.ss1 → proactive train (Mudkip→Marshtomp L20) → beat Roxanne →
Chapter 5a; and catch Abra+Whismur+Taillow (party 1→4, no dups) → prep-train the
team. Defeat counter increments per-location (map). Grass spot: Route 116 (11,7),
east of Rustboro (101 grass tiles). Notes: Route 116 trainers over-train past the
band a bit; training a full caught team to the band is a slow grind (randomized
'lead' scope mitigates). Sandbox only.

## 2026-07-21 — Story robustness: PC exit, scene-tolerant nav, derail self-correction, Area Atlas (sandbox)
User-reported bugs + architectural direction (§AA):
- Poké Center doorway stuck (normal healing): heal_in_pokemon_center exited by
  walking ONTO the (7,8) warp, which can stop on it without firing (ML-9). Now walks
  ABOVE the door and steps down (robust warp fire). STOCK file — DIVERGENCE at promo.
- Catch/train bailed to Manual on Route 116: navigation wasn't scene-tolerant; a
  trainer sight-line aborted it. Added _navigate_riding_out (retry + ride-out) for
  training/catching.
- Derail self-correction: a NON-whiteout error re-localizes (logs stage via
  detect_live + map) and retries the segmented resume (bounded, >4 → Manual) instead
  of dropping to Manual immediately; whiteout recovery resets the derail budget.
- Design §AA "Area Atlas": the RULE — hand-craft each area's respawn point / nearby
  grass / inter-map routing / key locations BEFORE scripting it (no blanket fixes).
  Documented the region covered so far (Littleroot→Rustboro→Rusturf). Sandbox only.

## 2026-07-21 — Out-of-balls contingency COMPLETE: buy at mart (sandbox)
Retrofit per planning doc §3/§4 (the reported break). Two-part fix: (safety floor,
committed earlier) catching is resource-aware — never attempts a catch without balls;
(provisioning, this entry) buy_poke_balls(count, mart) drives the Emerald shop UI to
restock, and provision_poke_balls buys min(30, affordable) keeping a ¥500 reserve.
Wired into catch_starter_team: out of balls → buy → resume; broke → skip. Shop-UI
lessons captured in §4 (list-menu confirms need wait_until_task_is_not_active + A;
item-select and quantity-confirm each show a message to advance). Verified: buy 5 →
6→11 balls; full flow (balls forced to 2 → caught Abra → bought 30 → resumed →
team of 4 → training). Sandbox only.

## 2026-07-21 — Shop/PC mapping strategy documented + shop-agnostic buy (sandbox)
User note: each mart has its own layout AND stock/order (incl. multi-floor Lilycove
Dept Store); the E4 Poké Center has a shop+mart; and a future PC/box team-management
system is wanted. DECISION (planning doc §4/§4b): do NOT map all shops now
(unreachable → can't verify). Buy code made shop-agnostic — `_mart_item_row` reads
`sMartInfo` at runtime and moves the cursor to the item's actual row, so the same
code works at any mart regardless of stock order (verified: Rustboro row 0, buy 5 →
6→11). Map each shop's entry facts as reached (Atlas row). Poké Centers are
near-identical (generic code handles them) — only map exceptions. New punch-list:
#24-shops (map shops as reached, incl. Lilycove multi-floor) and #24-pc (PC/box team
management: locations + Deposit/Withdraw/Move/item-storage UI). Sandbox only.

## 2026-07-21 — Story resume fix (intro re-run) + post-battle freeze finding (sandbox)
User report: bot gets stuck at the first Poké Center in Oldale, "after respawn."
Investigated with the faithful main-loop harness (proven to run the identical
`main_loop` as the real bot).

FIXED (verified) — Segment 1 resume bug: the whole intro→Pokédex block was gated
only by RECEIVED_POKEDEX, so ANY recovery/resume before the Pokédex (whiteout,
derail, or a loaded save) re-ran the scripted intro FROM THE TRUCK, then tried to
navigate to the player's house from wherever it actually was (Route 103/Oldale) —
impossible → derail loop → frozen in place. Reproduced from a pre-Pokédex Route 103
save. Fix: split Segment 1 — run the scripted intro (truck→lab) only while no starter
exists (`_has_starter()`); the train→rival→Pokédex part is resumable and gated by
DEFEATED_RIVAL_ROUTE103. Now correctly resumes at training instead of looping.

FIXED (robustness) — derail budget: the progress fingerprint used event flags, which
FLICKER while read during a battle→overworld transition, so a genuine freeze could
masquerade as "progress" and loop forever. Reworked `_progress_sig` to a monotonic
party-derived fingerprint (size, lead level, total EXP); reset the derail budget only
on real progress. Recovery now patiently waits for a STABLE controllable overworld
(`wait_until_truly_controllable`, presses nothing) so a single recovery rides out a
self-healing stall instead of burning derails toward Manual.

OPEN (Bug 2, for real-PC validation) — post-battle transition freeze: during training,
after a battle ends (flee / level-up / move-learn e.g. Mudkip's Water Gun at Lv10),
the return-to-overworld transition leaves the overworld non-controllable while the bot
acts (navigate to grass, walk to the Oldale nurse to heal) → can hard-freeze (nurse
heal dialogue never starts). Confirmed real (harness == real main_loop), timing/
starter-sensitive (default starter is "random"; Treecko's overnight run got through,
Mudkip reliably hits it). Offline repro is hampered by save-state reload artifacts (a
saved mid-transition state deadlocks on reload even when the live run self-heals), so
per user decision this is to be validated on the real PC before a deeper fix. Reverted
a mis-fire battle_handler change (it keyed on gDisplayedStringBattle, which goes STALE
after battle → false positives). Sandbox only.

## 2026-07-21 — Debug logging toggle for Story-bot freeze diagnosis (sandbox)
User confirmed Bug #2 (post-battle freeze) reproduces on the real PC. Built an
opt-in extensive run logger to capture what the real bot does so freezes can be
diagnosed from a shared log file.
- NEW `modules/debug_logger.py`: OFF by default. When enabled, writes a compact,
  structured, line-flushed log to `<profile>/debug-logs/<mode>-debug-<ts>.log`
  (profiles/* is gitignored, so logs are never committed). Captures an EVENT stream
  (bot-mode changes incl. derails→Manual, story-step `context.message`, map changes,
  battle start/end+outcome, level-ups/evolutions/catches, move-learn state, explicit
  Story DERAIL/WHITEOUT events) + automatic STUCK DUMPS (a rich snapshot when nothing
  progresses for ~300 frames, INCLUDING the running generator's call stack — function
  + line — via a gi_yieldfrom walk, plus held buttons, tasks, scripts, battle text)
  + periodic heartbeats. Battles are excluded from stall detection (they legitimately
  hold still mid-turn). Fully guarded so it can never break/slow a normal run.
- GUI toggle "Debug Logging (diagnostic file)" added to the Run (bot-mode) menu in
  BOTH the native dashboard (`dashboard_gui.py`) and the classic controls
  (`emulator_controls.py`); default off; shows the log path when enabled.
- Hook: one guarded `debug_logger.on_frame(frame_info)` in `main_loop` (runs every
  frame, incl. after a drop to Manual — so it keeps logging during a freeze).
- StoryMode.run(): explicit `debug_logger.event(...)` on derail/whiteout recovery.
- VALIDATED end-to-end through the faithful harness on the exact freeze scenario: the
  log cleanly showed training → battles(+outcomes) → heal at Oldale → repeated
  self-healing ~1078-frame stalls → DERAIL #1..#5 → drop to Manual. 0 battle
  false-positives after the gate fix. This is the diagnostic picture we need from the
  user's real run.

## 2026-07-21 — Bug #2 ROOT-CAUSED + FIXED via the debug log (heal loop) (sandbox)
User ran the real bot with Debug Logging on and shared the log. The generator call
stack in the stuck dumps pinpointed the bug EXACTLY (not Mudkip-specific — it was a
Treecko run): the freeze is a HEAL → DERAIL → RE-HEAL loop.
- ROOT CAUSE: `heal_in_pokemon_center` returns immediately after the PC exit-warp,
  while the overworld is still transiently non-controllable (the controllable flag
  flickers). In the story's heal→go-to-rival flow (`fight_route103_rival`), the very
  next `navigate_to_anywhere` then throws "player avatar is currently not
  controllable" → StoryMode derails → recovery re-runs `_play` → `fight_route103_rival`
  re-heals (heal is its first step) → endless heal/leave-PC/re-enter-PC loop →
  DERAIL #1..#5 → Manual. (`train_lead_to_level`'s heal derailed too but self-healed
  because its loop navigates back to grass — that's why training survived.)
- FIX: `heal_in_pokemon_center` (higher_level_actions.py) now waits for a STABLE
  controllable overworld (20 consecutive controllable frames, bounded 300) after the
  exit warp before returning, so no caller's next navigate can choke. One root fix,
  all callers/modes benefit.
- VALIDATED in the harness (Mudkip, route103 pre-Pokédex save): 0 derails, 0 Manual;
  now trains → fights the rival → gets the Pokédex → sets off for Petalburg (was the
  exact freeze point). Debug logger gained ball-count tracking ([BALLS] events).
- NOTE: the fix let the bot get far enough to expose a SEPARATE downstream issue —
  opportunistic catching on Route 101 running out of Poké Balls → Manual (party never
  caught anything). Being investigated next (#24-freeze followup).

## 2026-07-21 — Catch never drops to Manual when out of balls (sandbox)
Exposed once the heal-loop fix let the bot reach the pre-gym catching: opportunistic
catching can burn through the 5 starter Poké Balls on bad catch RNG before restocking
at Rustboro, and stock CatchStrategy calls switch_to_manual() when it can't throw a
ball → Manual. FIX: `StoryCatchStrategy(CatchStrategy)` (story_mode.py) — if no ball
can be thrown, FLEE (`TurnAction.run_away()`) and carry on instead of Manual;
`on_battle_started` now returns it instead of `BattleAction.Catch`. Matches the user
directive (out of balls → finish the battle, never break). VALIDATED end-to-end
(route103 pre-Pokédex save, 110k frames): 0 derails, 0 Manual — trains → rival →
Pokédex → Petalburg → Wally tutorial → Route 104 → Petalburg Woods → Rustboro → Route
116 catching (team Mudkip L13 + Poochyena L4, caught via StoryCatchStrategy). Bug #2
(the user-reported Oldale freeze) + its downstream blocker are both resolved.

## 2026-07-21 — Swap-training fixes the under-levelled-mon loop (sandbox)
User (real-bot testing) hit a loop: with a very under-levelled catch (Lv2 Poochyena)
in a team led by Grovyle L17, `train_team` rotated the low mon to the lead and ground
it against too-high Route 116 wilds — it fought, nearly fainted, got rotated out to
win, healed, and repeated (glacial + loopy). User chose BOTH: swap-train now +
level-spectrum area mapping later.
- SWAP-TRAIN (now): new `SwapTrainBattleStrategy` (story_mode.py) — when the lead
  we're levelling is >= 2 levels below the wild foe, switch to the strongest healthy
  team-mate on turn 1 (before the lead takes damage); the lead still SHARES the XP
  (Gen 3) so it levels without fainting or needing a heal. Same-or-close foes it
  still solos for full XP. Gated by an `_SWAP_TRAIN` flag set only around
  `train_team` (never affects rival/gym fights). `train_team` now heals off the
  TEAM's lowest HP (`_min_battler_hp_pct`), since the mon taking hits is the strong
  team-mate, not the untouched lead. VALIDATED (route116team save, Mudkip L13 +
  Poochyena L4 + Nincada/Whismur L6): Poochyena L4→L7 steadily, **0 heals, 0 faints**,
  flee rate 25% (margin 2) — the fight-faint-heal loop is gone.
- MAPPING (later groundwork): see `modules/story/training_areas.py` + #24-trainmap.

## 2026-07-21 — Whiteout during pre-rival training now recovers (sandbox)
User (real-bot): a Torchic lost a wild battle while training before the rival →
respawned (healed) at the Oldale PC but the bot just SPUN in place there. Debug log's
generator stack pinpointed it: `train_lead_to_level` → `spin` with a stop-condition of
`_lead_level() >= target or _lead_hp_pct() <= heal_at` and NO abort check. `on_whiteout()`
sets the story abort flag (that's how gym-loss recovery works), but this one spin never
consulted it, and post-respawn its own conditions can't fire (level still < target, HP
now full) → spins forever. FINDING: only this ONE spin was affected — `train_team` and
`catch_starter_team` already checked the abort. FIX (both specific + universal): new
`_story_spin(stop_condition)` helper wraps `spin` with `story_should_abort()` baked into
the stop-condition + a trailing `_check_abort()` (raises → StoryMode.run whiteout
recovery). `train_lead_to_level` now uses it (the fix); `train_team` and
`catch_starter_team` refactored onto it too so the whiteout-aware pattern is uniform and
future spins can't silently omit it. VALIDATED: `_story_spin` unit-tested to bail with
BotModeError when the abort flag is set; WhiteoutListener confirmed to fire on any
whiteout (GameState.WHITEOUT / EventScript_FieldWhiteOut*) → on_whiteout; refactored
train_team still trains (Poochyena L4→L7, 0 errors).

## 2026-07-21 — Swap-training: finish the fight instead of fleeing on low HP (sandbox)
User refinement: during swap-training, when the trainee (fighting a close-level foe)
dropped to low HP it FLED for zero XP. Since a swapped-out mon still shares the Gen-3
EXP, it should instead switch to a team-mate that can SAFELY finish the battle (so the
trainee banks its XP), only fleeing if none can. `SwapTrainBattleStrategy.decide_turn`
now switches on TWO triggers — under-levelled (turn 1, as before) OR the trainee can't
continue (low HP / no usable move, the same tests the parent flees on) — to
`_capable_finisher()`: the strongest healthy team-mate that out-levels the foe (HP +
can-damage already ensured by get_potential_rotation_targets). If none qualifies it
falls through to the parent (flee on low HP / solo a same-or-lower foe for full XP), so
the fight completes with XP and the redundant flee-then-heal cycle is gone. VALIDATED
(route116team save): flee rate 13% (was 25%) — the remaining flees are the correct
"strong mon itself low → flee → heal" fallback; Poochyena still L4→L7, 0 errors.

## 2026-07-21 — Solidify Rustboro: resume edge fixed + Roxanne validated (sandbox)
- RESUME FIX: Segment 3's "past the Woods?" check was `_cur_map() == RUSTBORO_CITY or
  BADGE01`, so a save mid-catching/training on ROUTE 116 (the pre-gym grass, only
  reachable THROUGH Rustboro) failed it → re-ran the Woods travel → couldn't path back
  → derail (found while testing). Broadened to the whole Rustboro AREA: Rustboro city,
  ANY Rustboro building (map group 11 — gym/Devon/PC/mart/…), Route 116, or Rusturf
  Tunnel. VALIDATED: resuming from the Route 116 save now prints "already in Rustboro —
  skipping the Woods travel" and proceeds to Segment 4 (0 derails).
- LEAD THE STRONGEST before the gym: swap-training rotates a weak trainee into slot 0;
  new `_lead_strongest_battler()` puts the highest-level capable battler in the lead
  before `do_rustboro_gym` so the gym leads with our best mon (not a weak one that
  faints first).
- ROXANNE VALIDATED end-to-end (route116team save, gymtest driver): heal → lead Mudkip →
  beat the gym trainers + Roxanne → Mudkip evolved to Marshtomp L16 → STONE BADGE earned,
  0 whiteouts/Manual.
- NOTE (open): `_prepare_for_fight` can roll "train WHOLE team to Lv 15" — dragging fresh
  L4-6 helpers to gym level via swap-training (half XP) is a long grind. The main battler
  alone beats Roxanne, so training-target tuning (train battlers, not every catch) is a
  worthwhile efficiency follow-up (#24-team / #24-trainmap).

## 2026-07-21 — Training-grind fix: ready the battlers, don't grind every catch (sandbox)
User-chosen next step. `_prepare_for_fight` used a random "whole/lead" scope; "whole"
trained EVERY battler to the gym band, dragging fresh Lv4-6 catches up via half-XP
swap-training — a huge grind, and pointless (the primary mon sweeps Roxanne). Now it
trains only the mons worth readying: the STRONGEST battler (our primary) + any battler
already within `TRAIN_CATCHUP_GAP` (=6) levels of the target; fresh far-below catches are
left to level organically (#24-team). On repeated losses it adds depth (also readies the
top-3 backups). Implemented via a new `slots=` param on `train_team` (train only the
chosen slots). VALIDATED (route116team save): prep now logs "training 1 battler(s) to Lv
16 (fresh low catches left to level organically)" — Marshtomp trained solo, Poochyena
L4/Nincada L6/Whismur L6 untouched — then straight to the gym, 0 whiteouts (vs the old
"whole team to Lv 15" grind). Combined with the gym win (already validated), the full
prep→gym flow works.

## 2026-07-21 — Next chunk kickoff: Rustboro mapped + Devon-goods-return/PokéNav built (sandbox)
User: proceed with the next chunk, mapping first to harden from the start.
- MAPPED the Rustboro area statically from ROM (`get_map_data`) — Devon Corp floors +
  stairs + Mr. Stone (3F (15,5)), the rival NPC (city (16,50)), PC/Mart/Gym entrances —
  documented in 12-STORYMODE-DESIGN §Ch5b (Atlas + sequence + a HARDENING CHECKLIST
  derived from the Rustboro lessons).
- BUILT + VALIDATED `return_devon_goods_and_get_pokenav()` (early_game.py): from Rusturf,
  route to Mr. Stone on Devon Corp 3F, advance the dialogue until RECEIVED_POKENAV. Story
  now runs Devon Goods → PokéNav → clean stop on 3F (8× clean-stop, 0 hangs/derails).
- BUILT (not wired) `fight_rustboro_rival()` + `_lead_strongest_battler` reuse; fixed a
  navigation bug in it (`_navigate_through_scripts` returns on reaching the MAP not the
  tile → switched to `_navigate_riding_out`).
- BLOCKER FOUND + documented (next-session task): exiting Devon Corp after the PokéNav
  triggers a FORCED PokéNav/Match-Call tutorial — a `Task_HandleMultichoiceInput` chain
  (`RustboroCity_EventScript_PleaseSelectPokenav` ↔ `MatchCallTutorial`) that A/B and
  cursor-nav+A do NOT clear (harness-probed); it needs the PokéNav app actually opened +
  navigated. The story STOPS cleanly BEFORE it (on 3F) rather than hanging; the rival is
  wired only after this tutorial is handled. Sandbox checkpoint (not promoted — segment
  5b incomplete).

## 2026-07-21 — Chapter 5b: forced PokéNav Match-Call tutorial SOLVED + rival located (sandbox)
- SOLVED the session's blocker: the forced PokéNav/Match-Call tutorial (Rustboro Scientist,
  ON_FRAME `VAR_RUSTBORO_CITY_STATE==6`). Root-caused via WebFetch of the pokeemerald scripts
  + harness observation: intro msgboxes → start-menu multichoice (case 3 = POKéNAV) →
  PokéNav app in `POKENAV_MODE_FORCE_CALL_READY` (must place a Match Call). The app does NOT
  advance in our headless harness (proven: 150 A-presses/1500f = 0 progress).
- `skip_pokenav_match_call_tutorial()` (early_game.py): state-write to vanilla's EXACT
  post-tutorial end-state — `VAR_RUSTBORO_CITY_STATE=7` + `ROUTE104_STATE=1` + flags
  HAS_MATCH_CALL / ADDED_MATCH_CALL_TO_POKENAV / HIDE_RUSTBORO_CITY_SCIENTIST. Harness-proven:
  Scientist never fires; world-state == vanilla. Wired into `_play` §5b → clean stop.
  (Intentional divergence — DECISIONS-LOG 2026-07-21; flagged for user review.)
- Located the Rustboro rival trigger: coord-event row at **y=53 (x12-19)**, gated on
  `VAR_RUSTBORO_CITY_STATE==7` (the skip arms it). `fight_rustboro_rival()` rewritten to the
  proven staging(16,52)+Down-across-y=53 approach (harness-proven: MET_RIVAL→battle).
- Rival NOT wired: it's a TYPE-MATCHUP spike (grass Grovyle vs 4×-weak Marshtomp) — even Lv19
  Marshtomp whited out; wiring it would infinite-loop. Left built + trigger-proven pending
  type-aware lead selection. See 08-MISTAKES 2026-07-21.
- Harness: added `--driver pokenavtut|pokenavclear|pokenavskip` (dev tooling, scratchpad).

## 2026-07-21 (later) — PokéNav Match-Call tutorial done FAITHFULLY (call Mr. Stone) + fallback
Per user directive, replaced the pure state-write with a faithful play-through:
- Root cause of the headless stall FOUND: the PokéNav app's looped tasks only advance when
  the BG/OBJ renderer is ON (`context.video=True`). Added harness `--video` flag + `pokenavfaith`
  driver; used live SCREENSHOTS to read each PokéNav screen.
- `handle_pokenav_match_call_tutorial()` (early_game.py): FAITHFUL sequence — trigger the
  Scientist → pick POKéNAV → main menu Down,Down → MATCH CALL → A (list) → A (CALL) → A
  (place call to MR. STONE) → advance dialogue → B out → VAR_RUSTBORO_CITY_STATE=7.
  Harness-proven raw (STATE=7 at f893) AND via full `_play` with `--video` (app opens, call
  placed, clean stop, NO fallback used). Falls back to the state-write skip when the renderer
  is off (headless) or the nav stalls, so it never hangs.
- `_play` §5b now calls `handle_pokenav_match_call_tutorial` (was the state-write skip);
  `skip_pokenav_match_call_tutorial` is retained as the fallback. Rival still NOT wired
  (type-matchup — next: type-aware lead + attempt-cap, user-chosen).

## 2026-07-21 (later) — Rustboro rival WIRED with type-aware lead + attempt-cap (sandbox)
Per user choice ("type-aware lead + attempt-cap"):
- `_lead_best_matchup(foe_type_names)` (early_game.py): leads the CAPABLE battler with the
  lowest worst-case incoming STAB multiplier (tie-break by level). Validated vs the type
  chart: Grass is 4× on Marshtomp (Water/Ground) but 1× on our Normal/Bug-Ground mons, so it
  correctly avoids leading the 4×-weak Marshtomp into the grass rival.
- `fight_rustboro_rival` no longer sets its own lead (caller does, so the matchup lead isn't
  overridden by lead-strongest).
- `StoryMode.RIVAL_MAX_ATTEMPTS = 3` + a per-run attempt counter in `_play` §5c: bounds the
  train→fight→whiteout retry so an underleveled/bad-matchup team stops cleanly to manual
  instead of looping.
- `_play` §5c wired: `_prepare_for_fight(band 16-19)` → `_lead_best_matchup(["Grass"])` →
  `fight_rustboro_rival` → guard. Runs error-free (verified headless: enters training, no
  crash, bounded). NOT yet validated: an actual rival WIN — needs a natural post-gym team
  (the test save's L7-8 filler loses regardless of lead); the cap makes a thin team stop
  cleanly (no regression).

## 2026-07-21 (later) — Sail-leg recon: Briney mechanic understood; nav gated on a real post-rival save
- Understood the Briney sail from the decompiled script: talk to Briney (5,3) -> multichoice
  MULTI_BRINEY_OFF_DEWFORD -> pick Dewford (index 0) -> sails/warps to Dewford.
- Recon (harness `sailrecon` driver) surfaced the build gate: a SYNTHETIC post-rival state
  (rival flag set, player still mid-Rustboro) can't cross Rustboro->Route104 — walking Down
  from the rival row dead-ends at Rustboro (16,53); the real south-exit corridor + the rival
  cutscene's deposit position need a REAL post-rival save. Sail-leg build deferred to next
  session (build from a real post-rival save / recon the Rustboro-south connection first).
- Documented in design §Ch6 (SAIL-LEG RECON NOTE) + handoff.

## 2026-07-21 (later) — Fix failed-rival stuck bug + level-floor/heal before rival (from real-HW debug log)
User ran the bot on real hardware; the FAITHFUL PokéNav tutorial WORKED (called Mr. Stone).
On losing the rival, the bot stood below the rival (16,52) and dropped to Manual. Fixes:
- **BUG FIX (validated):** `fight_rustboro_rival` broke its Down-step loop on
  `MET_RIVAL_RUSTBORO`, which STAYS set after a loss — so on the post-whiteout retry it
  never stepped onto the y=53 trigger and stalled at (16,52). Now it breaks on the ACTUAL
  engage (battle active OR a rival coord-script on the stack) and raises a derail if it
  can't provoke the rival, so StoryMode retries. Harness-validated: with MET pre-set
  (simulated loss), the rival RE-ENGAGES.
- **LEVEL FLOOR (user):** `_play` §5c now trains the WHOLE team to ≥ Lv 10 (escalating
  10+2·(attempt-1)) before the rival, then band-preps the primary. Validated: all mons
  reached L10.
- **SAFE HEAL (user):** heal at the Rustboro PC right before the rival.
- **Training heal margin raised** (+8 → +22 above flee threshold) so the swap-train finisher
  heals earlier and doesn't faint mid-battle.
- KNOWN ISSUE (next): a long save-generation run surfaced a battle-framework hang — when a
  mon faints mid-training the bot can stall on the "choose your next Pokémon" menu instead
  of sending a replacement. The heal-margin bump reduces faints; the choose-after-faint path
  still needs a focused fix (user directive: all battles must survive failure). Post-rival
  SAVE not generated yet because of this.

## 2026-07-21 (later) — Full fresh run BEAT the Rustboro rival; post_rival.ss1 captured
- Ran a from-scratch headless game (new game → Rustboro rival) with the fixes. The rival was
  WON with a natural team (led Taillow L17 = Flying, the type-aware pick vs grass Grovyle;
  team all ≥10 via the level floor). NO faint-hang recurred (heal-margin mitigation + real team).
- Captured + validated `post_rival.ss1`: DEFEATED_RIVAL_RUSTBORO=True, RUSTBORO_CITY_STATE=8,
  controllable at Rustboro (16,53) — the rival cutscene leaves you there; walk south to Route 104.
  This unblocks the sail-leg build (Route 104 → Mr. Briney → Dewford → Granite Cave → Gym 2).
- The choose-after-faint framework hang did not trigger this run (mitigated); still a latent edge.

## 2026-07-21 (later) — Fix double-battle after-faint hang (choose picked the on-field partner)
User: in a double battle, when a team member faints, the bot got stuck selecting the OTHER
Pokémon already on the field (slot 2) instead of a benched one (slots 3-6).
- ROOT CAUSE: `LevelUpLeadBattleStrategy.choose_new_lead_after_faint` (modules/battle_strategies/
  level_up.py — used by the Story bot via LevelUpTravel/SwapTrain) picked the highest-HP
  battle-capable mon WITHOUT excluding the already-active battlers in a double battle. Its parent
  `DefaultBattleStrategy` DOES exclude them; the override dropped that check. So a faint could
  return the on-field partner's index → the bot strands on the "choose a Pokémon" menu.
- FIX: restore the double-battle active-battler exclusion (skip left/right battler party indices).
- A/B PROVEN (scratchpad/repro_double_faint.py, no emulator): double battle, slot0 faints —
  BEFORE returns index 1 (on-field partner, hang); AFTER returns index 2 (benched). Single-battle
  behaviour unchanged (still highest-HP benched). Likely also fixes the earlier "training faint
  hang" if that was a double battle.
- NOTE: upstream-file edit (level_up.py) — log in DIVERGENCE-LOG on promotion. (level_balancing.py
  has a similar override; not used by Story, left as-is.)

## 2026-07-21 (later) — Buy Poké Balls in batches of 10 for free Premier Balls (user directive)
The mart gives exactly ONE free Premier Ball per purchase of 10+ regular Poké Balls (only 1,
whether you buy 10/20/30). So buying in tens maximizes free Premier Balls at identical cost.
- `buy_poke_balls_in_tens(total)` (early_game.py): splits `total` into `total//10` purchases
  of 10 (each yields a Premier Ball) + a remainder purchase. Reuses the tested single-purchase
  `buy_poke_balls` per batch (re-opens the shop at the counter — cheap, low-risk).
- `provision_poke_balls` now calls it. Added `_ball_count(name)` helper.
- VALIDATED (harness, post_rival.ss1 at the Rustboro mart): buying 20 → 2 purchases →
  Poké Balls 17→37, Premier Balls 1→3 (**+2 free**), money 4984→984. Correct.

## 2026-07-21 (later) — Trainer/gym/E4 battles must fight through — fix the Roxanne switch hang
User: fighting Roxanne with Torchic (Fire, bad vs Rock) + an L6-7 bench, the bot hung
(state=PARTY_MENU) trying to switch to the weak/empty bench, then dropped to Manual.
- ROOT: `LevelUpTravelBattleStrategy.decide_turn` only intercepted trainer battles when a
  "strongest move" existed; otherwise it fell through to the parent's rotate/flee path.
  Rotating into a weak bench stalls the in-battle party-menu switch
  (battle_action_selection.py:106 `while PARTY_MENU: press A`), and fleeing a trainer battle
  raises. Either way the gym battle didn't fight through.
- FIX (our file, clean): in a trainer battle with no strongest move, KEEP ATTACKING with any
  in-PP move (Struggle if none) — never proactively rotate or flee. When the active mon
  faints, `handle_fainted_pokemon` brings in the next one (that after-faint path already
  excludes fainted/active mons — the double-battle fix). So trainer/gym/E4 battles always
  play through to a win or a clean whiteout (→ recovery), never a party-menu stall.
- VALIDATED (mock): trainer + no strongest move → returns USE_MOVE (first usable), not
  Rotate/RunAway.
- OPEN (for Fable): the underlying framework rotation-execution stall (a mid-battle switch
  into an un-sendable/mis-mapped slot can spin `scroll_to_party_menu_index` / the
  `while PARTY_MENU: press A` loop) still exists for any strategy that DOES rotate — needs a
  live repro to pin `map_battle_party_index` / the party-menu submenu handling. The Story
  bot now sidesteps it in trainer battles.

## 2026-07-21 (night, for Fable) — Fable handoff docs + sail-leg scaffold/recon
- Added `FABLE-5-KICKOFF.md` (paste-able briefing for the incoming agent) + `14-AGENT-PLAYBOOK.md`
  (craft/method) + the area-research template; wired into 00-README + a standing CLAUDE.md rule.
- Deep-mapped the Dewford→Slateport arc (§Ch6-8): accurate ROM-recon atlas, script-verified beats
  (Briney sail idx0; Steven's Letter → FLAG_DELIVERED_STEVEN_LETTER + TM47 Steel Wing), the
  Gabby&Ty DOUBLE battle in Slateport, and the reusable gym/boss prep pattern. Unvalidated bits
  tagged ⚠ VALIDATE LIVE.
- `sail_to_dewford()` scaffold: VALIDATED the Rustboro(16,53)→ROUTE104(16,0) south crossing and
  that **Briney's door = ROUTE104 (17,50)**. Discovered **Route 104 is river-split** — from the
  north strip you can't reach y≥30, so the path to Briney runs BACK through Petalburg Woods
  (Route104 N → Woods → Route104 S beach → door). That reverse-woods leg still needs building
  (precise spec in the docstring + §Ch6). Not wired into _play (unvalidated).
- Harness: post-rival save-hook now gated behind SAVE_POST_RIVAL=1 (it had clobbered post_rival.ss1
  during an unrelated mart test). Regenerated a clean post_rival.ss1 (Rustboro (16,53), STATE=8).

## 2026-07-21 (night) — COMMIT the test infrastructure so Fable inherits it (tools/story-dev/)
The faithful harness + drivers + recon scripts + checkpoint saves lived only in the previous
session's scratchpad (gone for the next agent). Committed them, generalized + documented:
- `tools/story-dev/story_harness.py` — the faithful main-loop harness (was repro_movelearn.py),
  paths now repo-relative; loads states from `saves/`; post-rival auto-save gated behind
  SAVE_POST_RIVAL=1. All ~16 drivers included (story/gymtest/pokenavfaith/saildewford/…).
- `tools/story-dev/*.py` — recon/probe/A-B scripts (maprecon, repro_double_faint, doorprobe,
  routeprobe, sailprobe), paths generalized.
- `tools/story-dev/saves/` — a 12-state progression sampler (oldale→…→post_rival) for instant
  testing; regenerate any via the story.
- `tools/story-dev/README.md` — prereqs, quick-starts, the drivers/saves tables, conventions.
- Smoke-tested from the new location (A/B proof passes; harness loads post_rival.ss1). Repointed
  the playbook + design-doc + kickoff references from `scratchpad/` to `tools/story-dev/`.

## 2026-07-22 — CHAPTER 6 COMPLETE: sail_to_dewford BUILT + VALIDATED end-to-end (sandbox)
The bot now plays post_rival.ss1 → Dewford Town unattended. Punch-list #24.
- `sail_to_dewford()` (early_game.py) rebuilt from the scaffold into the full leg:
  Rustboro (16,53) → Down across the connection → Route104 north strip → Woods north door
  (11,30) → cross Petalburg Woods SOUTHBOUND (reverse of Ch3) → inside door (17,38) →
  Route104 south beach (11,38) → Briney's door (17,50) → talk → sail → DEWFORD_TOWN dock
  (12,3). Every leg keyed off the LIVE map (idempotent, resume-safe §SC). All warp pairs
  doorprobe-verified first (full Route104 warp table now in design §Ch6).
- ‼ Decomp correction: the FIRST sail is a YES/NO (not the MULTI_BRINEY_OFF_DEWFORD
  multichoice — that's for later sails). Code handles both.
- NEW helper `_talk_to_wandering_npc(map, local_id)` — talking to a PATROLLING NPC
  (Briney local_id=1 + Peeko lap a ring around the cottage table). Strategy: OBSERVE a
  patrol lap (recording both walkers' routes) → park BESIDE his route (on nobody's
  route, never a warp tile) → face-tap+A when he transits the adjacent tile. Took 4
  proven-failed attempts to get here (spawn-tile talk / navigate-chase / greedy chase /
  on-route blocking) — the full saga + prevention rules in 08-MISTAKES + playbook §7.
- Wired into `_play` as Segment 6 (gated ¬DELIVERED_STEVEN_LETTER ∧ ¬BADGE02_GET; guard
  map==DEWFORD); end-of-content message now points at Ch7 (Granite Cave → Brawly).
- PROOF: harness `--driver saildewford` full run post_rival→Dewford, AND the real
  StoryMode `--driver story` run (Segment 6 fires, sails, clean content-end stop; a
  mid-route PokéNav Match-Call ring was ignored correctly by the listener). Checkpoint
  `tools/story-dev/saves/dewford.ss1` committed (midstuck.ss1 demoted to gitignored
  scratch). STORY_TALK_DEBUG=1 env var traces the talk helper.

## 2026-07-22 — CHAPTER 7 COMPLETE: Steven's Letter + Gym 2 (Brawly) BUILT + VALIDATED (sandbox)
The bot now plays dewford.ss1 → Letter delivered → KNUCKLE BADGE, zero derails. Punch-list #24.
- `deliver_stevens_letter()` (early_game.py): Dewford PC heal (also moves the whiteout
  respawn island-side, KI-10) → Route 106 beach → Granite Cave door (48,16) → the
  FIVE-WARP LADDER CHAIN to Steven — every cave floor is split into disconnected
  sections; the vanilla route dips through B2F: 1F (17,11) ↓ B1F (4,21)→(28,21) ↓ B2F
  (28,21)→(29,13) ↑ B1F (29,13)→(25,13) ↑ 1F (35,3) → Steven's door (5,10). Talk =
  choice-free A-through (Letter taken, TM47 given, DELIVERED_STEVEN_LETTER set, Steven
  despawns). Return = reverse chain (the 1F one-way LEDGE lets the walker shortcut
  straight to the exit) + finish with the Dewford PC heal.
- NEW `_walk_warp_chain(chain, done, label)`: generic multi-floor warp-chain walker.
  Section membership on a split floor is decided by LIVE pathability, and the step
  chosen is the FURTHEST-ALONG pathable one — first-match looped live (the 1F one-way
  ledge makes the early ladder "reachable" from the north section → 9 hops of
  ping-pong). New `_enter_warp_by_navigation` includes the last nav error in failures.
- `do_dewford_gym()`: town door (8,17) → dark gym bottom→top (trainers inline) →
  challenge tile (4,4) → Brawly → BADGE02_GET. Wired as Segments 7a/7b with the boss
  pattern (heal + `_lead_best_matchup(["Fighting"])` — picked Dustox, Bug/Poison resists
  Fighting — + attempt-band); band is FLOOR-ONLY (14,16) because Dewford has NO
  reachable training grass pre-Surf (Route 106/107/Dewford = surf-only tables; Granite
  Cave wilds L6-10 — recorded in training_areas.py).
- Segment-6 gate fixed to a PRE-SAIL MAP WHITELIST (a Granite-Cave derail had re-entered
  the sail leg and marched to Manual); checkpoint capture now rides out leftover dialogue
  before saving (dewford.ss1 v1 was taken mid-textbox → loaded non-controllable; repaired).
- PROOF: full `--driver story` run dewford.ss1 → letter → badge → clean content-end stop,
  0 derails / 0 whiteouts (ch7_run7). Checkpoint `saves/brawly_done.ss1` committed
  (extracted from current_state.ss1 via the playbook §2 recipe; flags verified).

## 2026-07-22 — CHAPTER 8a COMPLETE: sail Dewford → Slateport BUILT + VALIDATED (sandbox)
The bot now plays brawly_done.ss1 → Slateport City, healed, zero derails. Punch-list #24.
- `sail_to_slateport()` (early_game.py): Dewford Gym exit → Dewford PC heal → dock
  Briney (local_id 2 at (12,9); `approach_hint=(11,9)` because the engine only loads
  object events NEAR THE CAMERA — from across town after the PC heal the dock object
  simply isn't in RAM; live-hit + fixed) → his `multichoicedefault` menu (✓ decomp:
  gated on DELIVERED_STEVEN_LETTER; Petalburg=0/SLATEPORT=1/Cancel=2, CURSOR DEFAULTS
  TO CANCEL — answered Up ×1 → A; the stock helper presses Down-from-cursor and would
  wrap onto Petalburg) → sail → Route 109 beach → North into Slateport (trainers inline)
  → Slateport PC heal (respawn anchor, same KI-10 reasoning). Wired as Segment 8a with a
  Dewford-side whitelist gate. PROOF: `--driver story` run brawly_done → "arrived in
  Slateport City" clean stop, 0 derails/whiteouts (ch8_run2, ~40k frames).
- Checkpoint `saves/slateport.ss1` (Slateport (19,20), healed; DELIVERED_DEVON_GOODS
  verified False = the Ch8b anchor). Playbook §7 + design §Ch8 updated (Slateport city
  objects/warps probed: Stern (28,13), Gabby&Ty (28,14)/(29,13), 11 museum-queue grunts,
  PC door (19,19)).

## 2026-07-22 — SHINY = ALWAYS CATCH (user directive) + dock-stall fix + DEBUG Story modes (sandbox)
Implemented on the user's go-ahead, in the order they set. All proven.
- **SHINY ALWAYS-CATCH:** new `StoryShinyCatchStrategy` + the shiny branch is now the
  FIRST check in `on_battle_started`: wild shiny + any usable ball → attempt the catch
  (owned species included, full party → box, any story stage); balls exhausted MID-battle
  → fight through (never flee a shiny, never Manual); zero balls up front / the scripted
  tutorial battle → fight through as before. Ball choice inherits the #40 allowlist
  (Master Ball protected by default). PROOF A (no emulator, `repro_shiny_noballs.py`):
  same out-of-balls input → parent flees / shiny variant attacks. PROOF B (emulator,
  `--driver shinytest` forces wilds shiny): 19 balls → 3 thrown → outcome=CAUGHT, with
  `_should_catch` forced False (the owned-species/post-gym gating) — the shiny branch
  alone drove it. Replaces the old fight-through-only contingency the user caught on
  real HW (Shiny Poochyena fought with 32 balls in the bag).
- **DOCK-STALL FIX (real-HW bug, user's log 2026-07-22):** after the first sail the
  arrival reminder msgbox (Route104_EventScript_DeliverLetterReminder) stays open and
  every wait-for-control path presses NOTHING → the bot derail-looped at the Dewford dock
  to Manual. Fixed in THREE layers: both sail legs B-ride the arrival script before
  waiting; and the generic derail recovery now B-rides any ACTIVE script before its
  stable-controllable wait (an open dialogue can never wedge recovery again).
- **NEW Run-tab modes** (auto-registered): **"Story (DEBUG)"** = Story with the debug
  logger force-enabled, resumes from anywhere (native segmented resume). **"Story
  (DEBUG - RESET)"** = debug logger + HARD emulator reset → main menu → NEW GAME forced
  even over an existing save (gSaveFileStatus-gated Down; the save file itself is only
  overwritten if the game later saves in-game). Proven in-harness (`--driver
  storydebugreset` from a mid-game state → reset → new game → Treecko → first battle
  won); the save-present menu branch is decomp-reasoned — ⚠ validate once on the real
  profile (the user's normal setup).
- **FULL-ARC REGRESSION (also proves the dock fix end-to-end):** one `--driver story`
  run post_rival.ss1 → sail → Granite Cave letter → Brawly (KNUCKLE BADGE) → dock →
  sail → Slateport PC → clean content-end stop. ~75k frames, 0 derails / 0 whiteouts.
- Punch list: added #24-interrupt (interruption intelligence) and #24-movelock
  (Disable/Encore/Taunt-aware move choice) per the user's slate-for-later items.

## 2026-07-22 — LIVE TEST harness: "Conduct Live Tests" batch runner + /livetest command
User-designed capability for deep debug sweeps (discussed + built while their real-HW
test ran): `tools/story-dev/livetest.py` runs N independent Story runs (default 10,
default FRESH new game → the current frontier, or any saves/ checkpoint for fast
scoped sweeps), in parallel LANES (default 3), each in an isolated auto-created
`repro-live<K>` profile (a leased-profile pool guarantees two processes never share a
profile). Per run: harness log + stdout + auto-extracted summary.json (frontier
reached / hang / Manual / timeout-kill, derail + whiteout counts, shiny events, final
flags/party, last positions); plus a batch summary.json. `.claude/commands/livetest.md`
defines the workflow: pre-flight (no lanes while the user live-tests; check
END_MARKERS matches the current content-end message), run, then a LIVE TEST REPORT
reviewed WITH the user before any fix: per-anomaly frequency (x/N) + context
signature + classification (universal bug vs NUANCED SITUATION needing detection —
never blanket-fix a nuance — vs known-issue vs variance) + evidence + proposed fix +
regression risk. Batch artifacts gitignored (livetest-runs/). Smoke-tested (1 scoped
lane: runner mechanics + summarizer + end-marker detection).

## 2026-07-22 — REAL-HW TRIPLE-LOG REVIEW (user's new-PC session) + watchdog variant fix
Three user logs reviewed (one continuous session on the second PC):
- **"Story (DEBUG - RESET)" real-profile validation ✅** — from a mid-game Rustboro save
  it hard-reset and FORCED NEW GAME over the existing save (the previously ⚠-flagged
  branch), then played the fresh game clean through team-catching → ROXANNE WON → Devon
  Goods → Rusturf → PokéNav. Log ends abruptly mid Match-Call tutorial with NO stall
  dumps — consistent with the user's reported SYSTEM crash (not a bot hang); noted the
  tutorial is the most renderer-heavy sequence (possible GPU/driver trigger, unproven).
- **"Story (DEBUG)" continuation ✅✅** — on a different save from Rustboro: rival WON →
  cottage (the wandering-Briney ambush ENGAGED on real HW) → sail (Dad's mid-sail Match
  Call ignored correctly) → Dewford arrival ride-out (NO dock stall — the fix holds on
  real HW) → full Granite Cave ladder chain → Letter delivered (TM47; an L21 move-learn
  prompt handled en route) → BRAWLY WON → dock sail → Slateport PC → clean content-end.
  The ENTIRE Ch5c→Ch8a arc real-hardware validated in one run, zero derails.
- **Log 3 finding → FIXED:** the watchdog auto-restarted Story (DEBUG) after the
  intentional content-end Manual (exact-name `_SELF_RECOVERING_MODES` missed the DEBUG
  variants; also silently re-armed save-state reloads for them). `_is_self_recovering`
  prefix matcher + A/B proof. See 08-MISTAKES.

## 2026-07-22 — Parallel session: Ch8b built (BLOCKED on museum entry), livetest batch findings, fixes
While a 3-run fresh live-test batch ran, built Ch8b (Devon Goods → Capt. Stern) and hit a
real blocker; the batch itself found bugs. Net:
- **Ch8b `deliver_devon_goods_to_stern` BUILT** (museum entry → fee → 1F → 2F stairs →
  Stern (13,6) → two un-fleeable grunt battles + Archie scene → DELIVERED_DEVON_GOODS,
  scene heals the party). Interior logic sound, BUT the museum ENTRANCE is grunt-sealed at
  this story point (KI-11 — all probed, not guessed): doors (30,26)/(31,26) blocked by
  Aqua grunts id 5/18 on the only below-door tiles; hide-flag 882 unset by default with no
  map trigger. UNWIRED pending real-HW ground truth (asked the user); frontier stays the
  validated Slateport arrival. Design §Ch8b + KI-11 have the full recon.
- **livetest batch findings (its first real use, found real bugs):**
  * run01 "reached frontier in 7 min" = FALSE PASS — a reused lane profile's .sav made a
    "fresh" boot CONTINUE an old save. FIXED: the runner now wipes each lane's
    save/state/states before a fresh run. (Also: prints flush; END_MARKER dash-free.)
  * run02 (fresh, Treecko→Grovyle): real HANG — the trainee EVOLVED mid-team-catching on
    Route 116 (Fury Cutter learned) and the training spin never resumed (20k-frame stall).
    Repro saved: saves/evostall.ss1. → punch #24-evo-trainstall.
  * run03 (fresh, Torchic): played ~450k frames then hung in Rustboro. → punch
    #24-freshbatch-rustboro (under-investigated).
- **Harness:** `STORY_DEBUG_LOGGER=1` now mirrors main.py's debug-logger hook so harness
  runs get the generator-call-stack stall dumps (pinpoints silent press-nothing stalls).

## 2026-07-22 — CHAPTER 8b COMPLETE: Devon Goods → Capt. Stern (KI-11 resolved via user + decomp)
The bot now plays slateport.ss1 → Devon Goods delivered → content-end, validated. Punch #24.
- **KI-11 RESOLVED** — it was a DOCUMENTATION/SEQUENCING gap, not a state bug (exactly the
  case that prompted the /validate-docs process). The user supplied the missing story step;
  the decomp confirmed the exact flag. The Oceanic Museum is grunt-SEALED until you visit
  **Stern's Shipyard (city door (26,38)) and talk to DOCK (interior (5,5))** — his script
  runs `setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA`, clearing the entrance.
- `deliver_devon_goods_to_stern()` (early_game.py) built + wired (Segment 8b): Slateport →
  Shipyard → Dock (approach (4,5) face Right; keyed on the clear-flag) → museum door (30,26)
  walk-in → ¥50 fee (A-ride, never B) → 1F → stairs (6,1) → 2F → Stern (13,6) via (13,5)
  face Down → two BACK-TO-BACK un-fleeable grunt battles (attack-through) → Archie → the
  script HEALS the party + `DELIVERED_DEVON_GOODS` + lifts the Route 110 blockade → exit.
- Two coordinate bugs found + fixed during validation (both = approach tiles on collision
  walls): Dock approach was (5,6)=wall → (4,5); Stern approach was (13,7)=wall → (13,5).
  Prevention: pick NPC approach tiles from the collision grid, never the tile "below" by
  reflex (interiors wall NPCs on arbitrary sides).
- PROOF: full `--driver story` run slateport.ss1 → Shipyard/Dock → museum → both grunt
  battles WON → "Devon Goods delivered" clean content-end stop (one recovered 8000-frame
  cutscene-wait derail early — non-fatal; noted). Checkpoint `saves/stern_done.ss1`
  (captured via the new harness `SAVE_CHECKPOINT="FLAG:name"` hook).
- Docs: design §Ch8b rewritten with the verified sequencing (old doc had Stern at the harbor
  (28,13) — WRONG; he's museum-2F (13,6)); KI-11 marked resolved; ledger/frontier/README.

## 2026-07-22 — Escalation research capability (/escalate-sequence + reusable primer)
User directive: add a LAST-RESORT tier for story sequences that survive /validate-docs
(decomp + recon + walkthrough + reasoning + a direct ask). Instead of burning budget
thrashing, the agent pauses the beat and hands an external AI agent (default Gemini —
keeps research off Claude credits) two copy-paste prompts: a REUSABLE PRIMER (project
context + exact answer format) and a per-question prompt (the ambiguity + what's already
verified + ruled-out dead-ends). The external answer is a LEAD, verified against
decomp/harness before any code (prove every fix). Delivered: `PROJECT KNOWLEDGE/
15-ESCALATION-RESEARCH.md` (process + verbatim primer + question template + a note that
the primer is model-agnostic, so it also drives a future auto-spawned Claude sub-agent),
`.claude/commands/escalate-sequence.md`, and 00-README reading-order + process links.
Motivating case: KI-11. Not yet used — infrastructure only.

## 2026-07-22 — INTERRUPT-SAFE lead rotation: the 110k-frame training stall FIXED (user log + batch repro)
The user's real-HW DEBUG-RESET run stalled 110,435 frames mid-training on Route 116; their
log's generator stack pinpointed it: `train_team → change_lead_party_pokemon →
StartMenuNavigator.open_start_menu` with `Route116_EventScript_Joey` ACTIVE — the trainer's
sight-line fired at the exact moment the rotation opened the Start menu; a field script
locks input, the menu can never open, and the stock navigator waits UNBOUNDED. Same root
cause as the batch's #24-evo-trainstall (evostall.ss1: a leftover script after a mid-
training evolution wedged the next rotation identically).
- NEW `_yield_bounded(gen, max_frames)` — drive any sub-generator with a hard frame cap
  (unbounded stock menu navigators must never be trusted raw).
- NEW `_rotate_lead_safely(slot)` — interrupt-aware rotation (user directive: "know when
  a trainer interrupts anything"): never opens the menu while a script is active; bounds
  the menu drive (3000f); on interruption closes the half-open menu, rides the scene out
  (the battle listener fights any resulting battle), retries ×3, then continues WITHOUT
  the rotation (it's an optimization, not a requirement).
- All three story rotation sites now use it (train_team, _lead_strongest_battler,
  _lead_best_matchup).
- PROOF (repro-based A/B): story run from `saves/evostall.ss1` — the state that hung 20k
  frames in the batch — now rotates the lead successfully and training RESUMES (battles +
  EXP through the frame budget, no hang, no Manual). Closes #24-evo-trainstall; the
  user-log Joey stall is the same mechanism.

## 2026-07-22 — KI-12: the after-faint/double-battle crash CHAIN fixed (user log + faint-bench repro)
The user's gym log (130k frames wedged in the after-faint PARTY MENU) prompted a purpose-
built repro (`--inject-faintbench`: L3 lead + L4 bench vs the Rustboro gym). ONE repro
exposed a THREE-BUG CHAIN, each fixed + re-proven in sequence:
1. **Bounded party menu** (battle_handler): the stock after-faint loop pressed A UNBOUNDED;
   a mis-mapped/unsendable slot cycles menus forever. Now bounded + self-correcting
   (B-out of submenus + cursor sweep; returns after ~100s for outer re-dispatch).
2. **Chooser-None crash** (battle_handler): `choose_new_lead_after_faint` returns None on a
   weak bench → the stock `< 0` check CRASHED (TypeError) → Manual mid-battle. Now falls
   back to ANY living non-egg mon (anything beats crashing); if truly nothing alive, ride
   the loss out.
3. **The user's "double battle bug"** (battle_strategies/default): the double-battle path
   called `_handle_lead_cannot_battle` WITHOUT the required `reason` arg → TypeError →
   Manual mid-double-battle. Fixed; and the story strategy now OVERRIDES
   `decide_turn_in_double_battle` to ATTACK THROUGH trainer doubles (strongest usable move
   at whichever opponent is present; Struggle at 0 PP; never flee/rotate) — the inherited
   Default path would flee → raise in a trainer battle.
KEY INSIGHT: Emerald starts a TRUE DOUBLE battle whenever TWO trainers sight you at once
(e.g. between the Rustboro gym Youngsters) — doubles are common near paired trainers,
which is why these crashes clustered at gyms. PROOF: the repro now plays the double battle
to a natural loss → whiteout → the story recovery path (the residual Manual in the log is
the focused DRIVER lacking StoryMode's restart loop — the real bot's recovery is long-
proven). New harness flag `--inject-faintbench` committed for regression use.

## 2026-07-22 — Cave-aware training legs: the Granite Cave "not on connected maps" Manual drop FIXED
TWO user fresh-run logs failed identically: Brawly-prep training inside Granite Cave, a
trainee's HP dropped, and train_team healed toward the DEWFORD PC from INSIDE the cave —
a cross-warp-level navigation the global navigator plan-fails ("Source (35/11 @
GRANITE_CAVE_1F) and destination (2/10 @ DEWFORD_TOWN) are not on connected maps") →
derails exhausted → Manual. The grass-return leg had the mirrored flaw.
- NEW `_exit_training_cave_if_inside()` (threads the cave mouth (37,12) → Route 106
  before any PC heal) + `_goto_training_area()` (threads Route 106 (48,16) → cave before
  navigating to an in-cave spin tile). train_team now uses both.
- PROOF: new harness driver `cavetrain` runs the exact failing round-trip from
  dewford.ss1 — Dewford → cave spot (35,11) → exit → Dewford PC heal → back to the spot:
  ALL LEGS PASS (a wild-battle move-learn en route handled cleanly too).
- Prevention (playbook family): training areas inside warp-split dungeons need explicit
  door-threading on BOTH the heal leg and the return leg — never hand a cross-level
  destination to the global navigator.

## 2026-07-22 — Phantom post-evolution script was silently blocking wild encounters (batch run05 hang) FIXED
Fresh-batch run05 hung at f210,622: Grovyle evolved + learned Fury Cutter mid-training,
the battle ended, and the training spin then got ZERO encounters for 20k frames. Debug
stack proved the bot was parked inside `_story_spin`→`spin`, pressing nothing wrong —
the game itself had a script context still ACTIVE from the evolution scene, and an
active script suppresses wild-encounter generation. The KI-9 no-progress bail fired but
only re-navigated; the phantom script survived, so the bail→renavigate→spin cycle looped
invisibly forever.
- FIX (`modules/story/early_game.py`, `_story_spin`): when the spin bails on no-progress
  AND a script context is still active, B-ride the leftover scene (bounded) before the
  caller retries — encounters resume on the next round.
- PROOF: run05 stack localizes the wedge; the evostall.ss1 A/B already proved B-riding
  clears exactly this leftover script; guard proven harmless on a 260k fresh run with two
  organic evolutions+move-learns (zero hangs). Frame-exact replay of run05 is impossible
  post-change (fresh-boot RNG is deterministic only for identical code) — noted honestly.
- Also: `story_harness.py` NO-PROGRESS milestones now dump the generator call stack
  (in-battle stalls were previously unlocatable from the sig alone).

## 2026-07-22 — After-faint party menu: state-aware send-out (deterministic Ch9 wedge) FIXED
Ch9 validation deterministically hung 20k frames in the in-battle party menu after
Marshtomp fainted (Dustox also down): the script pointer had advanced to
BattleScript_FaintedMonTryChoose before the dispatch loop regained control (stock
condition matched nothing → default B-spam into a menu that can't be cancelled), and
the first "bounded sweep" replacement A-spammed blindly — with slots 0 AND 1 fainted it
lockstep-cycled popup → "no energy left" → list on the same slot forever.
- FIX 1 (`modules/battle_handler.py` dispatch): also recognize FaintedMonTryChoose.
- FIX 2 (the sweep): read cursor slot + party HP + active task each step and press the
  ONE button that advances (A to dismiss text; A on the popup only when the mon is
  alive, else B; Down toward a living slot), with press/release gaps.
- PROOF: probed the live wedge state (profile shutdown savestate) — un-wedged in ~128
  frames; the full re-run then resolved the battle and continued the story.
- Also: harness NO-PROGRESS milestones now print the generator call stack (this is what
  localized the wedge to the sweep, after two wrong hypotheses died to evidence).

## 2026-07-22 — Ch9a rival gate was keyed on a PHANTOM flag (could never pass) FIXED
Run 5 reached Manual via 5 derails: the segment/guard used "DEFEATED_RIVAL_ROUTE_110" —
a flag name that does NOT exist in Emerald's table; get_event_flag() silently returns
False for unknown names. Decomp truth (Route110_EventScript_RivalExit): the ONLY durable
signal is `setvar VAR_ROUTE110_STATE, 1` — no named flag.
- FIX: shared `route110_rival_beaten()` (VAR_ROUTE110_STATE >= 1, majority-of-3 reads;
  the mash loop additionally demands a 5-frame streak because save-block reads can TEAR
  around transitions and a one-shot check polled 30k times WILL eventually misfire).
- HARDENING: story `_done()` now raises on unknown flag names (a wrong NAME is a build
  error, not game state); new `tools/story-dev/audit_flag_names.py` sweeps all story
  flag/var name strings against the tables (run it before every chapter build).
- PROOF: run 6 passed the rival AND Wally segments end-to-end ("beat Wally — the gym
  door is clear"), reaching the Mauville Gym maze.

## 2026-07-22 — Mauville Gym maze: static-vs-LIVE map data root cause + live-grid solver (Ch9c)
Four validation runs "hung" in the gym. The debugging chain (each hypothesis killed by
evidence): after-faint menu ✗ (fixed separately), guard flag ✗ (phantom, fixed), blind
solver ✗ (bounded, still stuck) → SCREENSHOT of the wedge finally showed an electric
beam ON directly above the player while our collision map said the tile was open.
ROOT CAUSE: the gym's barriers are toggled at runtime via setmetatile into the engine's
LIVE grid (gBackupMapLayout); our get_map_data/calculate_path read the ROM's STATIC
default layout and are blind to every toggle — so "pathable" plans walked the player
into live beams forever. PROOF: live-vs-static grid diff on the captured wedge state
(saves/mauville_wedge.ss1) shows the beam tiles as live-only collision, and a held-Up
test bumps exactly where the static map says open.
- FIX (`do_mauville_gym`): the solver now reads the LIVE grid directly, learns both
  barrier configs at runtime (any switch press toggles FLAG_MAUVILLE_GYM_BARRIERS_STATE;
  a switch can't re-fire while VAR_MAUVILLE_GYM_STATE remembers it), BFS-plans over the
  combined (tile, config, last-switch) graph, and walks each leg with held directions
  judged by ARRIVAL — navigate/calculate_path are not used inside the maze at all.
- VALIDATED (run 10, 240k frames): maze solved repeatedly; bot reaches Wattson's
  approach tile and challenges him; zero hangs/derails/crashes; whiteout → heal →
  re-solve → re-challenge loop worked 8 times unattended.
- REMAINING (tracked as KI-13/#24-wattson-strength): the team LOSES to Wattson —
  Marshtomp missed Mud Shot and later auto-learned 0-power Mud Sport over its only
  Ground attack; the L17 bench folds. Needs pre-gym training prep + move-learn quality.
- Harness: progress signature now includes player position (an actively-exploring maze
  solver is not a hang); NO-PROGRESS milestones dump the generator call stack.

## 2026-07-22 — CHAPTER 9 COMPLETE: Dynamo Badge won (KI-13 resolved) + interrupt hardening
Run 14 end-to-end from stern_done.ss1: Route 110 rival → Wally → Segment 9c PREP
(band-train 20-24 at Route 117 (31,16); Taillow→Swellow and Poochyena→Mightyena evolved
during it) → live-grid maze solve → **Wattson BEATEN** ($2400, BADGE03_GET) → checkpoint
`wattson_done.ss1` (verified: badge + DEFEATED_MAUVILLE_GYM + DEFEATED_WALLY_MAUVILLE) →
clean content-end stop. What closed KI-13:
- Move-learn guard (`battle_strategies/default.py`): never learn a 0-power move — the
  Mud Sport-over-Mud-slap regression is impossible now (run 14's Marshtomp kept Mud-slap).
- Segment 9c prep (heal + `_prepare_for_fight` band 20-24 + Electric-resistant lead +
  safe heal), mirroring the Brawly pattern.
- Training tile: Route 117 (31,16) — the ONLY two-way-pathable grass from the Mauville
  road (full 162-tile sweep from the real entry tile; Route 110's grass is Cycling-Road-
  walled / ledge-one-way — runs 11-13 each died plan-failing toward unswept tiles, and
  `_navigate_riding_out`'s bail message now carries the real last error instead of
  blaming "scene interruptions").
- `_ride_out_all_scenes`: multi-part aftermath chains (Wally defeat → uncle → Scott →
  registration) are now ridden until the field stays quiet for 600 straight frames.
Also this session (real-HW log): `ensure_facing_direction` rides out field scripts
(85k-frame trainer-intro wedge fixed, regression-proven) and StoryMode gained a GLOBAL
no-progress watchdog (18k frames of total stasis → self-derail into recovery).

## 2026-07-22 (overnight) — Ch10a: HM06 Rock Smash acquired + live-grid gym exit + rival rematch fallback
- `get_rock_smash_hm()` VALIDATED (run 3 from wattson_done.ss1): live-grid gym exit
  (the static planner can't path out of the post-badge gym — the deactivated puzzle
  exists only in the LIVE grid; exit BFS also avoids OBJECT tiles after run 2 walked
  into Wattson) → cross town → SE house (32,14) → Rock Smash Guy → RECEIVED_HM_ROCK_
  SMASH → `_exit_small_interior()` (new generic one-room-door helper) → content-end.
  Checkpoint `rocksmash_got.ss1`.
- RUSTBORO RIVAL REMATCH FALLBACK (two batch runs died on this): the trigger row
  requires VAR_RUSTBORO_CITY_STATE==7 and the MEETING sets it to 8 — met-but-not-
  beaten states (organic mid-navigation meetings are FAITHFUL and fine when won; a
  loss leaves the row dead) can only rematch by TALKING to the rival object
  (local_id 15, (16,50)). fight_rustboro_rival now falls back to exactly that.
- Batch 4 (5×1.6M fresh): 2/5 FRONTIER (up from 1), 0 Manual; 2 budget-bound
  mid-Wattson (L20-26 parties — training pace, #24-train-efficiency); 1 = the rival
  wedge above. Next batch at 2M frames.

## 2026-07-22 (overnight, cont.) — Ch10b teach flow + rival vanilla-truth + Ch10c staged
- `teach_hm_move()` BUILT + VALIDATED (probed task chain; two UI bugs fixed on the way:
  the battle/evolution cursor sensor reads garbage in the overworld summary UI — the
  cursor STARTS at slot 0, so deterministic Downs; and the close-out ride must be
  STATE-AWARE or it re-answers the yes/no prompts in a loop). Marshtomp carries Rock
  Smash over Foresight. Segment 10b wired + validated via the story path
  (`rocksmash_taught.ss1`).
- RUSTBORO RIVAL VANILLA-TRUTH (replaces the earlier talk-fallback theory): win or
  LOSE there is no rematch and the story does not require the win — met-and-spent
  (MET + VAR_RUSTBORO_CITY_STATE>=8) now counts as RESOLVED in both the segment and
  its guard. Validated from the real met-and-lost wedge (rivaldead.ss1): the run
  moved on, sailed, and continued the Dewford arc. (The rematch fallback was removed
  — her talk script is only the Briney hint.)
- Ch10c (`travel_to_fallarbor` + `_smash_rock`) built + wired; validation in flight.
- Punch: +#24-hm-slaves (PC-parked HM carriers + machinery before Surf), +#24-
  knowledge-base (per-chapter items/secrets/legendaries + move-priority v2 querying
  the bot's own data), +#24-event-pokemon (endgame event legendaries — authentic
  acquisition theater, Mystery Gift spoofing candidate, user discussion first).

## 2026-07-22 (overnight, cont.) — Ch11b+11c COMPLETE: Maxie beaten, Lavaridge reached
Run 3 from meteorfalls_done.ss1: Cable Car (attendant YES-ride) → summit → grunt
sight-lines → Tabitha → MAXIE beaten → meteorite taken → Jagged Pass ledge descent →
Lavaridge PC. Checkpoint `lavaridge.ss1`. Fixes en route: (a) travel segments must be
PROGRESS-gated, not map-gated — the corridor maps are shared with later return trips
and a mid-return derail re-triggered the Fallarbor travel into the Go-Goggles-gated
desert; (b) the Cable-Car approach routes EXPLICITLY through the Fiery tunnel (the
desert "shortcut" is script-gated invisibly to collision); (c) in-state sweeps only —
hidden-NPC templates seal routes on cold boots (both "impossible" legs opened from
the real story state).

## 2026-07-23 — Ch11d COMPLETE: the Lavaridge trapdoor maze is SOLVED — HEAT BADGE won
`do_lavaridge_gym` rewritten from a guessing explorer into a solver that derives the
maze from the ROM's own map data, and Segment 11d wired into `StoryMode._play`.
- **Root cause of the long-running wedge: behaviour 59 (`MB_JUMP_SOUTH`) LEDGES.** Both
  gym floors read as sealed chambers under plain collision, so the explorer judged
  chamber after chamber exit-less and oscillated between two inert warp tiles until it
  ran out of rounds (ch11d_run9 died in the B1F (5,6)/(5,9) chamber — whose only way on
  is the y=11 ledge). Ledges are collision=1 but hoppable downward two tiles. With hops
  modelled, NO chamber is a dead end and the whole maze is a clean graph.
- Model, all three parts verified against the warp/metatile dump and the live trace:
  1F behaviour 104 = hole (falls land SAME-COORD on B1F), B1F behaviour 41 = geyser
  (launches to the same 1F coord), any other warp tile is an inert landing pad.
  State = 1F chamber; edge = fall through a reachable hole, walk to a reachable geyser.
  Backward BFS from Flannery's chamber → the next move from wherever we actually are,
  so a battle knock-off or surprise landing re-plans instead of derailing.
  Canonical chain from the entrance is **4 falls**: (8,9), (0,10), (2,3), (10,6).
- Two planning hazards handled: legs never path across another hole/geyser (it fires en
  route and discards the plan), and NPC-held tiles are excluded — four B1F geysers are
  the buried trainers' own tiles (Jace/Keegan/Jeff/Eli), and the gym guide at 1F (12,16)
  sits on the shortest path to the first hole (that stalled run 10).
- Fixed a hang class in the same function: a failed leg used to B-ride a scripted scene
  unconditionally, which spins for 18k frames when no scene exists (run 10). Recovery
  now rides out only when a script is ACTUALLY active, and a consecutive-stall budget
  raises a truthful error instead of spinning.
- **VALIDATED** (run 11, lavaridge.ss1 → `--driver story`): maze solved in ~6.3k frames,
  0 derails, Flannery beaten, `BADGE04_GET`, clean content-end. The identical chain ran
  twice in one run (a whiteout mid-way, self-recovered, then re-solved it move for move)
  — an unplanned determinism A/B. Checkpoint `saves/flannery_done.ss1`.
- ⚠ Segment 11d does NOT pre-grind: a two-way pathability sweep proved NO training grass
  is reachable from Lavaridge (Jagged Pass is one-way; Route 112's lower grass has no
  return path). Prep is a Water lead + heal. L29-31 wins but is marginal (the run 11
  whiteout). Open as #24-trainmap.
- New recon tools: `lavaridge_gym_probe.py` (warp graph), `lavaridge_gym_solve.py` (the
  static solver, prints the canonical chain), `lavaridge_tiles_probe.py` (raw
  collision/elevation/behaviour grid — this is what exposed the ledges),
  `lavaridge_objects_probe.py`, `jaggedgrass_probe.py` (two-way training-tile sweep).

## 2026-07-23 — Two real-hardware bugs from the user's DEBUG-RESET log: fixed + proven
Both reported from `Story_DEBUG__RESET...062055.log` and reproduced in-harness first.
- **Slateport museum "stuck looping at the greeter" — root cause: A is not "advance
  text", it STARTS a conversation.** Ride-outs asked for "A" so a Yes/No (the ¥50 fee)
  couldn't be declined. But standing beside the entrance attendant, every A dismissed
  her message and immediately re-opened it. The trace made it obvious: text was
  `'Please enjoy yourself.'` — the fee was already PAID — cycling `Std_MsgboxNPC`
  forever until the ride-out hit its 8000-frame timeout and derailed to Manual.
  FIX: new `_dialogue_button()` — a request for "A" now resolves per frame to **A only
  while a Yes/No or multichoice menu is genuinely on screen, and B otherwise**. B
  advances and dismisses dialogue identically but can never initiate one. Applies to
  all five A-riding call sites, so the whole class is closed.
  Also hardened `_wait_until_cutscene_over`: it no longer mashes during the
  non-controllable TAIL of a dialogue (script already ended, control not yet settled) —
  that window was a second way to re-trigger an adjacent NPC. It now presses only when
  a script is actually running or a text printer is waiting on input, and it watches
  the immediate script context as well as the global one.
  PROVEN: `museumprobe2.py` reproduces the loop on `slateport.ss1` (raises after 8000
  frames), and with the fix the same run dismisses the greeter once, walks (9,7)→(6,1)
  to the stairs, completes the Stern/Archie scene and returns cleanly.
- **Dewford: the walk back to the dock took a detour past the townsfolk.** Briney is
  STATIC at the dock (12,9) — object id 2, confirmed in the ROM's object table — so the
  wandering-NPC machinery was the wrong tool. Its `known_spot` fast path used `_step_to`,
  a GREEDY stepper with no route planning: heading east along y=11 toward (11,9) it hits
  the wall band at y=10 (x=10-13) and the fallbacks push it south into the (12,14)-(12,17)
  pocket, where it loitered for thousands of frames (exactly the positions in the user's
  log). FIX: `sail_to_slateport` now walks STRAIGHT to (11,9) with the real pathfinder,
  faces Right and talks, with the wandering procedure kept only as a fallback; and
  `_talk_to_wandering_npc`'s known-spot phase now tries the pathfinder before falling
  back to greedy stepping, which fixes the class anywhere else it is used.
  PROVEN: from `brawly_done.ss1` the dock leg is now a direct 10-tile walk (PC → y=11 →
  (9,9) → (11,9) → Briney), then aboard.
- Regression evidence: one 250k-frame run `brawly_done.ss1` → Dewford gym → sail →
  Slateport → **museum delivered** → Route 110 rival → Mauville prep, still in Story
  mode at the budget end, 1 self-recovered derail.
- New tool `tools/story-dev/mapfacts.py` (`PROBE_MAPS=` env): warps + objects + a
  passability grid for any map — how both root causes were pinned.

## 2026-07-23 — "Show Coords" debug readout + a full-game Gemini research commission
Two user-directed items, built while a fresh-start test run was in progress (so neither
touched the emulator, profiles, or save states).
- **Show Coords toggle (Play tab → CONTROLS → "Debug").** Displays the player's live tile,
  area name, map group/number and facing, so better pathing coordinates can be read off
  the screen and reported during development instead of reconstructed from a log after
  the fact. Off by default; display-only (reads state, never writes), so it is safe to
  flip mid-run. Every read is individually guarded — the readout says "(no player
  position available)" on the title screen or mid-warp rather than showing a stale
  position that might be reported as current. The preference survives a GUI rebuild
  (handheld toggle), and the label re-packs so the button can never read active with
  nothing under it.
  ⚠ Code-verified and compile-checked only — NOT yet clicked live, because the user's
  fresh-start test was running. Confirm on screen before relying on it.
- **`sandbox-pokebot/profiles/GEMINI-FULLGAME-RESEARCH.md`** — a self-contained Deep
  Research commission for a whole-game, bot-grade Emerald walkthrough (the broad
  counterpart to the surgical per-question relays in GEMINI-PROMPTS.md). It front-loads
  what "good" means for a bot rather than a human reader, prioritises everything past our
  Heat Badge frontier, and explicitly hunts the failure classes that have actually cost us
  time: hidden prerequisite steps (the Slateport Dock case), runtime-modified map layouts,
  one-way terrain, NPC patrol-vs-static, and — the Lavaridge lesson — puzzle RULES rather
  than a single solution route, so the bot can re-solve from any position. Includes a
  continuation prompt for truncated runs, a grading procedure with a known-answer control,
  and a run log. Referenced from 15-ESCALATION-RESEARCH.md.

## 2026-07-23 — HM teach made compatibility-aware + learner acquisition (user report) + Gemini full-game graded
- **The Rock Smash teach flaw (user's fresh-start test):** Segment 10b taught "the
  highest-level mon" with no compatibility check — an incompatible top mon (e.g. a
  Swellow-led party; Swellow CANNOT learn Rock Smash) loops in the party menu on
  NOT ABLE. (In the user's own log the pick happened to be Marshtomp and succeeded —
  the flaw is real, the trigger is party-composition luck.)
- **Fix, three layers, all data-driven from the ROM (works for every future HM/TM):**
  (1) `hm_learner_slot(item)` — highest-level party mon that CAN learn it (prefers one
  that already knows it, so re-runs are idempotent); (2) `ensure_hm_learner(item)` —
  when the party has nobody: derives hunting grounds (swept TRAINING_GRASS tiles whose
  land encounter tables contain a learner species — encounter tables × TM/HM learnsets,
  zero hardcoding), provisions balls if short, walks there, and catches a learner via a
  new on-sight catch branch keyed on `HM_CATCH_TARGET_DEX`; (3) `teach_hm_move` now
  hard-fails truthfully on an incompatible target instead of looping the menu.
  Route 117 (31,16) added to TRAINING_GRASS (two-way swept during Ch9).
- **A/B PROOF:** `repro_hm_learner.py` (part A: real party → picks Marshtomp L24, slot 0,
  the highest COMPATIBLE — and shows Swellow=False, the latent trigger; grounds derived:
  Rt 101/103/116/117 with real learner lists) + `--driver hmtest` (part B: whole party
  fault-injected to "cannot learn" → hunted Route 117 → CAUGHT a wild Poochyena →
  TAUGHT it Rock Smash — end-to-end through the faithful loop, RESULT: PASS).
- **Bug found on the way (own goal):** the new catch branch referenced the module-level
  `console`, but later branches in the same method import it locally — Python makes the
  name function-local EVERYWHERE, so the branch raised UnboundLocalError which the
  defensive `except` silently ate: 252 encounters, zero catches, no error. Lesson logged
  (08-MISTAKES): a swallowed exception in a decision branch fails as silent wrong
  behaviour — instrument the except before trusting the conditions.
- **Gemini full-game response GRADED** (run log in GEMINI-FULLGAME-RESEARCH.md):
  B+ — HIGH for step order, rosters, gotchas and the commissioned puzzle RULES (Fortree
  turnstiles, Aqua warp graph, Mossdeep statues, Seafloor Sokoban+reset, Sootopolis
  Hamiltonian ice, and the Sky Pillar first-visit-solid-floors trap); MEDIUM for
  identifiers — several phantom/wrong-dialect flag names (`FLAG_RECEIVED_HM03` etc.,
  `FLAG_DEFEATED_RIVAL_ROUTE119`) — every name goes through audit_flag_names.py before
  wiring. Spot-checked 10+ identifiers against our ROM-derived tables. Leads folded into
  12-STORYMODE-DESIGN §Ch12+ (⚠ unverified-external). Known-answer control still
  pending — relay PROMPT 2 (early game) to complete the grading.
- **New punch-list futures** (user directives): #24-provisions (potions + strategic
  healing, E4 stocking), #24-tms (TM decision layer), #24-pokeprofiles (per-Pokémon
  battle profiles via batched overnight research + Gemini cross-referencing; doubles as
  the sibling AI project's reference layer), #24-economy (cashflow). #24-hm-learner DONE.

## 2026-07-23 — #24-tms/#24-pokeprofiles research commission authored (Gemini relay)
`sandbox-pokebot/profiles/GEMINI-POKEPROFILES-RESEARCH.md`: a two-prompt Deep Research
commission (primer + task) for the TM/HM/tutor registry, a story-team priority tier
list, and full battle profiles for the ~20 early-game evolution lines (Batch 1). Built
to be graded hard: our ROM-extracted learnset/TM-compat data machine-checks every
acquisition claim (the known-answer control), and the primer front-loads the Gen 3
rules that change recommendations (physical/special BY TYPE, single-use TMs, HM slot
tax, Emerald-vs-R/S divergences). Batch 2+ reuses the schema with species lists drawn
from emerald_obtainability.json. Relayed to the user for Gemini; results will be graded
into the run log and folded into the future #24-pokeprofiles data layer.

## 2026-07-23 — Pokeprofiles research GRADED (machine-checked) + Gemini API relay BUILT
- **The #24-tms/#24-pokeprofiles Deep Research response graded B** via the planned
  known-answer control: `tools/story-dev/grade_pokeprofiles.py` verified 98 claims
  against the ROM-extracted data. **TM/HM compat: 59/60 (98%)** — only miss: Swellow
  cannot learn TM30 Shadow Ball (the registry's contention list is wrong there).
  **Level-up levels: 16/38 (42%) — unreliable, some invented** (Kirlia "Reflect",
  Hariyama "Cross Chop" — not in their level-up sets at all). STANDING RULE: research
  answers supply WHICH moves matter; the levels ALWAYS come from modules/data.
  Judgment layer graded HIGH (Truant+Hyper Beam overlap, Guts+Facade, Huge-Power-vs-
  special-Surf trap, Vital Throw's no-miss property, Ralts/Abra switch-training need,
  Game Corner TMs effectively repeatable via bought coins). Raw response archived
  (GEMINI-POKEPROFILES-RESPONSE-2026-07-23.md); full grading in the commission file's
  run log; TM locations remain decomp-unverified until #24-tms builds.
- **Gemini API relay BUILT + verified** (`tools/story-dev/gemini_relay.py`, user
  directive + key 2026-07-23): the agent can now query Gemini directly (one-shot,
  multi-part --file prompts, model select, --list-models, --out). Key lives GITIGNORED
  at sandbox-pokebot/profiles/gemini.key (never committed; also $GEMINI_API_KEY).
  Proven: model list + a live question. Day-one lesson captured in 15-ESCALATION:
  quick models are confidently wrong on learnset levels (both test numbers wrong) —
  the API path is for surgical questions/cross-checks; Deep Research commissions stay
  on the user-relay path; ROM data stays the only authority for game numbers.

## 2026-07-23 — KI-14 fixed + matchup-aware after-faint chooser + BOSS-TRAINING MODE (all proven)
The three items from the boss-training discussion, implemented in the agreed order.
1. **KI-14 (teach strands the start menu).** Both halves: the teach's hard-close loop
   now requires a MENU-FREE overworld (new `_menu_task_active()` — the start menu reads
   as OVERWORLD state, which is why `game_state == OVERWORLD` lied), and
   `_wait_until_cutscene_over` presses B when a menu task is up (B closes menus and can
   never START a dialogue, so the museum-greeter guarantee survives — re-proven by
   re-running the museum repro clean). PROOF: rocksmash_got.ss1 → teach → Route 113,
   0 derails (ki14_run1.log) — the exact sequence that wedged the user's run.
2. **Matchup-aware after-faint chooser** (`LevelUpTravelBattleStrategy.
   choose_new_lead_after_faint`): replaces the stock highest-HP pick with (least
   incoming STAB from the opponent's types, best own-move effectiveness vs the
   opponent's type PAIR, HP fraction, level). This was the Wattson run's real killer —
   full-HP Swellow/Ninjask (both Electric-weak) kept walking into Thunderbolts.
   PROOF: repro_faint_matchup.py A/B with real Species/Type objects — stock picks
   Swellow (bug reproduced), story picks Mightyena (neutral), and still picks Swellow
   when the foe is Ground (sanity).
3. **BOSS-TRAINING MODE** (`_prepare_for_fight` + KO telemetry in `on_battle_ended`):
   when ≥2 losses AND the configured grass is fodder (wild max + 8 < team max, read
   live from the encounter table) AND recent lost attempts KO'd ≥1 boss mon
   (gBattleResults.opponentFaintCounter, offset 0x01), prep becomes a LIGHT top-up
   (team max +1) and the boss re-attempt is the real training — Gen 3 keeps mid-battle
   XP through a whiteout (~8× the XP of a fodder wild per KO; consult archived).
   Two consecutive 0-KO attempts → classic heavy escalation. Grass-less bosses
   (Flannery) skip the grind entirely and go straight to the re-attempt.
   PROOF: repro_boss_training.py drives the REAL _prepare_for_fight through all four
   scenarios (boss mode 29 / fallback 33 / classic 23 / grass-less None) with the real
   Route 117 encounter table.
Punch list: +#24-trainersweep (exhaust one-time route trainers before grinding; Match
Call rematches later). KI-14 marked fixed in 05-KNOWN-ISSUES.

## 2026-07-23 — SWEEPER-SUFFICIENCY GATE: pre-gym prep now trains only what's needed
User observation (Combusken L20 band-training the whole team for Roxanne) + two-agent
Gemini consult (design critique + adversarial, archived in tools/story-dev/research-
gemini-sufficiency-consult-2026-07-23.md) → the proactive prep asks "do we already
have a sweeper?" before training anything. Backup tag `backup-pre-sufficiency-2026-07-23`
(pushed) is the clean revert point.
- **The gate** (`_sufficiency_verdict` + `_sweep_score`, proactive attempts only —
  losses ≥2 hand control to the reactive escalation/boss-training unchanged):
  a battler is SUFFICIENT when its best usable damaging move scores
  BP × STAB × effectiveness-vs-ACE-TYPE-PAIR × STAT-FIT ≥ 80 and its level ≥ ace−1,
  and the ace does NOT hit it super-effectively (defensive veto). Sufficient → skip
  team training entirely. Within 2 levels → targeted top-up of JUST that mon.
  No sweeper → band prep exactly as before. Doubles → always band prep.
- **Consult findings baked in:** ace full type pair, not gym primary type (the
  Altaria/Kingdra lesson); STAT-FIT scales a move by the mon's relevant attacking
  stat vs its better one — Gen 3's physical/special-by-type split means Poochyena's
  Bite (Dark=special off 30 SpA) scored a mirage 90 without it (caught by repro B).
- **Evolution lookahead** (the user's exact Torchic case): a mon that evolves within
  +3 levels is judged on the EVOLVED form's types + level-up moves at that level —
  Torchic L14 is Rock-weak and moveless, but Combusken@16 is Rock-neutral with Double
  Kick → verdict: train JUST Torchic to L16. (First cut evaluated the current form's
  defense and wrongly vetoed the line — caught by the same repro.)
- Gym cfgs gained ace data: Roxanne Nosepass L15 Rock / Brawly Makuhita L19 Fighting /
  Wattson Manectric L24 Electric. Rival cfgs have no ace → gate skips, band prep as always.
- **PROOF:** repro_sufficiency.py (6 scenarios vs real ROM data: skip / Torchic top-up /
  Mudkip sufficient / no-sweeper band / Swellow defensive veto with Marshtomp chosen /
  losses≥2 bypass) + LIVE run rustboro.ss1: gate printed "Mudkip … targeted top-up",
  trained ONE mon to 14, BEAT ROXANNE, continued into Ch5 — 58 battles in 200k frames.
- Also: gemini_relay default model → gemini-3.1-pro-preview (user directive; 2.5-flash
  documented for cheap one-liners).

## 2026-07-23 — Route 111 Rock Smash hang FIXED (the batch-8 wedge, finally): world-judged smashing + phantom-script escape
User's paired logs (12:24 = mid-Wattson training; 13:41 = a fresh run that hung at the
FIRST rock (18,101) until manually killed) closed the case the overnight batch-8 sweep
had queued: `_smash_rock`'s A-ride waited for `EventScript_SmashRock` to end — but Rock
Smash rolls a WILD ENCOUNTER (a Geodude spawned mid-smash in the user's run), and a
battle-interrupted field script can leave the script context READING active forever
while the game is fully playable. The rider timed out at 8000 frames, derailed, and the
recovery rode the same phantom in a loop.
- **`_smash_rock` rewritten**: IDEMPOTENT (a recovery re-entry that finds the rock
  object already gone is a no-op — no more A-presses into whatever stands beyond) and
  judged by the WORLD: success = the rock OBJECT disappears from the live object list,
  regardless of what the script context claims. Battle-aware by construction (a spawned
  battle pauses the generator; the judgment holds on resume). 3 bounded attempts, then
  a truthful error.
- **Phantom-script escape** in `_wait_until_cutscene_over`: ten straight seconds of
  "avatar controllable + no waiting text + no menu + script still reading active" is a
  PARKED context, not a cutscene — treat the scene as over instead of the
  8000-frame raise-and-derail loop. A real cutscene never idles like that (it locks
  the avatar, prints text, or ends).
- **PROOF**: repro_phantom_script.py fault-injects the exact hang profile — old
  semantics raise at the full timeout, fixed rider returns at ~600 frames; locked
  real scenes still time out honestly and normal endings return promptly. LIVE:
  rocksmash_taught.ss1 → both rocks smashed → Route 112 → Fiery Path → Route 113
  (smash_run1.log), no Manual, no 'never broke'.
Punch list: +#24-hm-multi (teach HMs to additional mons when genuinely an upgrade —
user note; gated on the TM decision layer to avoid HM-taxing battlers).

## 2026-07-23 — "Load Milestone State": the checkpoint library is now a GUI feature
User directive (shared-saves discussion): the repo's committed harness checkpoints
double as shared test entry points, so GUI test runs can start at any built milestone
instead of relying solely on multi-hour fresh runs.
- **`modules/story_milestones.py`** — curated, story-ordered registry over
  `tools/story-dev/saves/*.ss1` (25 catalogued milestones, Ch1 → the HEAT BADGE
  frontier + repro states; uncatalogued .ss1 files still appear, generically labeled,
  so new checkpoints are usable before the table is updated). The library path
  resolves by walking up to the repo root — works from sandbox AND custom, and a
  `git pull` always yields checkpoints matching the code under test (no copying,
  no staleness).
- **`modules/gui/milestone_window.py`** — the "Load Milestone State" popup: chapter-
  tagged two-column list (Milestone | Where/What), double-click or button to load,
  and the safety copy up top: these states are the TEST playthrough (trainer NICK),
  they replace the running session (the profile's on-disk save is only touched by a
  later in-game save — use a test profile), and they pair with the resume-anywhere
  Story modes, NOT "DEBUG - RESET" (which forces a new game).
- Wired as a button in the dashboard's GAME MENU card + Emulator menu, and into the
  classic GUI's Emulator menu. Load semantics mirror Load Save State exactly (state
  bytes → frame reset → Manual; the user starts a Story mode when ready).
- **`saves/user-reports/`** — the reverse direction: a drop folder + convention for
  the user's real-HW bug-capture states, so a reported wedge can be reproduced
  byte-for-byte in the harness instead of reconstructed from logs.
- Verified: registry resolves 26 states against the live library (25 curated + 1
  auto-labeled), GUI modules import clean. ⚠ Not yet clicked live (the user's test
  run was in progress) — confirm the popup renders on the next GUI session.

## 2026-07-23 — Cable Car boarding fixed + whiteout-mid-descent stranding recovered (Ch11b/c)
User's DEBUG run (from a personal save state) reached the frontier content and wedged
at the Mt. Chimney cable car — surfacing TWO bugs, both fixed + proven end-to-end.
- **Cable Car never boarded (the reported wedge).** `do_mt_chimney` approached (6,8)
  and faced Up — but the attendant is at (6,6) (probed live; the code's own docstring
  said (6,7), also wrong), so A hit the EMPTY tile (6,7) and boarding never fired. The
  bot then A/B-mashed the 4800-frame board-wait and derailed. FIX: approach (6,7) face
  Up (talks the (6,6) attendant), with a retry loop tolerant of a wild encounter firing
  on the walk up. Extracted as `ride_cable_car_to_summit()` (route-from-Fallarbor +
  board + exit), reused by both the ascent and the recovery below.
- **Structural STRANDING after a mid-descent whiteout.** A whiteout on a Jagged Pass
  trainer respawns the team at Fallarbor — BELOW the one-way descent, and the cable-car
  segment is gated on Magma-already-beaten so it was skipped: permanent stranding.
  Worse, Segment 11c's guard was "off the mountain", which FALSELY PASSED at the
  Fallarbor respawn, so Flannery then ran from the wrong town. FIX: (a) 11c guard now
  checks we actually reached Lavaridge (or earned BADGE04); (b) `do_jagged_descent`
  re-rides the cable car to the summit when it finds itself below the mountain and not
  yet in Lavaridge (the cable car is a permanent transit — it rides you up after Magma
  too). Jagged Pass is one-way south, so re-boarding is the only recovery.
- **PROOF (one run, meteorfalls_done.ss1 → --driver story):** cable car boarded → Maxie
  beaten → descent → team lost a Jagged trainer → whited out → respawned Fallarbor →
  RE-RODE the cable car (post-whiteout trail: Fallarbor → Fiery Path → summit station →
  Mt. Chimney → Jagged Pass → Lavaridge) → Flannery beaten → HEAT BADGE → clean
  content-end, 0 derails.

## 2026-07-23 — Rock Smash field use 6x faster + resume-from-anywhere normalizer + clean milestone
User's milestone-testing logs surfaced three things; all fixed + proven. Backup tag
`backup-pre-resume-robustness-2026-07-23` (pushed) is the revert point.
- **Rock Smash field use was ~127s for the two Route 111 rocks.** `_smash_rock`'s A
  cadence was gated on `not script_active` — but the "Use ROCK SMASH? YES/NO" prompt
  IS an active script, so A never answered YES and each rock idled ~3800 frames until
  the outer retry re-fired. Fixed: press A every 10 frames unconditionally (A opens the
  prompt, answers YES on the default cursor, and advances the smash messages; extra A
  is harmless — the post-smash tile is empty). Measured: ~1,200 frames (~20s) for both
  rocks now, a 6x speedup, 0 derails.
- **RESUME-FROM-ANYWHERE failsafe (user directive).** New `normalize_to_overworld()`
  runs at the very start of `StoryMode._play` (before any segment navigates): it brings
  the game to a stable, controllable overworld by pressing ONLY B until settled —
  advancing/closing dialogue, closing menus, cancelling Yes/No, and WAITING OUT a live
  battle. B can never start a conversation or take a destructive action (A could), so it
  is universally safe. This makes a Story mode started in ANY state resume cleanly:
  mid-menu, mid-dialogue, mid-battle, mid-cutscene. PROOF: repro_normalize.py (5 fault-
  injected entry states — start-menu, message, Yes/No, battle, clean — all settle
  B-only, battle waited, clean instant) + a LIVE heal of the actual old menu-saved
  milestone (BAG_MENU -> OVERWORLD controllable in 204 frames).
- **rocksmash_taught.ss1 milestone was saved in the BAG_MENU** (loading it landed in a
  menu). Regenerated clean via regen_rocksmash_taught.py (teach from rocksmash_got ->
  normalize -> verify -> round-trip check): it now loads to a controllable overworld at
  Mauville (32,15) with Rock Smash known. Audited the other Ch10 checkpoints
  (rocksmash_got, wattson_done) — both already clean. (The normalizer would self-heal a
  menu-saved state regardless, but a clean checkpoint is correct hygiene.)
- End-to-end: a run from the regenerated milestone smashed both rocks fast and reached
  Meteor Falls, 0 derails.

## 2026-07-23 — Ch12 DEEP-MAPPED (Lavaridge → Norman → Surf); milestone run graded clean
- **Milestone run graded (3b75c330 log): CLEAN, no fix needed.** Loaded the Lavaridge
  (Ch11c) milestone, solved the trapdoor maze perfectly 4×, beat Flannery on the 4th try
  (3 boss-training whiteouts, team L29→L32), HEAT BADGE, clean content-end. 0 real derails.
  The whiteouts are boss-training working as designed on a deliberately-weak milestone team
  at the grass-less tanky-ace Flannery; a fresh run arrives stronger. Noted #24-flannery-grind
  (low priority).
- **Ch12 deep-mapped** (§Ch12 build spec in 12-STORYMODE-DESIGN; Gemini 3.1 Pro consult
  archived research-gemini-ch12-2026-07-23.md; recon petalburg_gym_probe.py). Verified this
  session (✓): all Ch12 flags/vars (RECEIVED_GO_GOGGLES 221, RECEIVED_HM_SURF 122,
  DEFEATED_PETALBURG_GYM 1268, BADGE05_GET 2155, VAR_PETALBURG_GYM_STATE 133, the gym NPC
  hide-flags); the Petalburg gym interior (9×112, 8 trainer tiers, Norman (4,2), entrance
  (4-5,111), Wally's dad (1,7)); and **the Go-Goggles/desert are OPTIONAL** — Route 111's
  connections (South→Mauville, West→Rt112/113) prove the Lavaridge→Petalburg path never
  enters the Go-Goggles-gated desert. Left as ⚠ build-time-verify: the overland route
  connections, the gym door-path (live-solve like Mauville vs the "left door" speedrun
  route), the Norman team (Spinda/Vigoroth/Linoone/Slaking — no ROM trainer reader exists),
  and the post-Norman Surf handoff. Chapter table: Ch12 🗺️ ready to build; +Ch13 row.

## 2026-07-23 — Ch12 build STARTED (route leg WIP) + a material routing correction
Began building Ch12 (Lavaridge → Norman). `travel_lavaridge_to_petalburg` drafted in
early_game.py, **deliberately NOT wired** (frontier stays Flannery). Recon proved the
Route 112 one-way-ledge crossing (Lavaridge→Route111(13,90)) — but that exposed a
**material correction to the deep-map spec**: Route 111's middle is the Go-Goggles DESERT
and blocks the N↔S internal passage, so the Lavaridge→Mauville leg CANNOT cross Route 111
directly — it must tunnel via the FIERY PATH (reverse Ch10 travel_to_fallarbor, past the
already-smashed twin rocks). Corrected §Ch12 spec + the function's docstring with the exact
resume plan. Remaining: the Fiery-Path leg, validated Mauville→Petalburg tiles, the gym
live-solver, the Surf handoff, then wiring. New recon tools: route_probe_ch12.py,
route_chain_ch12.py. Honest checkpoint — no untested code on the frontier.

## 2026-07-23 — VALIDATION SWEEP (user-requested): 5 fresh + 5 milestone runs
Two livetest batches to check the story frontier for hangs/derails/crashes.
- **Pass 1 — 5 FRESH runs to the HEAT BADGE frontier** (--frames 3.2M): 3/5 reached the
  frontier cleanly (1 self-recovered derail each), 1 budget-bound INCOMPLETE (clean, ran
  the full 3.2M — training pace, #24-train-efficiency), 1 genuine HANG (run05: after-faint
  party-menu chooser with a 1-HP Shedinja — logged KI-15). Net: 4/5 clean, 1 real bug.
  The Match-Call/trainer-approach stalls seen mid-run SELF-RECOVERED (they are the "1
  derail" — not failures).
- **Pass 2 — 5 MILESTONE runs from rocksmash_taught.ss1** (the recent-fix arc: travel →
  cable car → Jagged descent → Lavaridge maze → Flannery): **5/5 reached the HEAT BADGE,
  0 hangs / 0 derails / 0 whiteouts.** Clean sweep — strong confirmation that all the
  frontier content built this session (KI-14, cable car + descent recovery, maze solver,
  rock-smash speed, resume normalizer, sufficiency gate, boss-training) is solid.
  (First Pass-2 attempt from wattson_done deterministically wedged at f74383 in
  travel_to_fallarbor — a wattson_done-SPECIFIC post-battle navigator gap, logged KI-16;
  rocksmash_taught travels the same code cleanly, so it is the working milestone.)
- Two bugs found + documented (KI-15 after-faint chooser residual; KI-16 wattson_done
  navigator wedge) — both intermittent/narrow, both with repros for a focused fix; NOT
  guess-patched (they touch critical battle/navigator code and need a validated repro).
  New recon tools: route_probe_ch12.py / route_chain_ch12.py (from the Ch12 build attempt).

## 2026-07-23 — KI-16 FIXED: Rock Smash returned before its field script finished (the wattson_done wedge)
Root-caused the deterministic wattson_done→Fiery-Path hang (validation Pass 2). Captured the
exact wedge state via a harness hook and found the stuck field script: `EventScript_SmashRock`
parked in `WaitForMovementFinish`. `_smash_rock` returned the instant the rock OBJECT
disappeared — but the smash script's WaitForMovementFinish runs AFTER the object is removed,
so the caller's next navigation started moving the player, CANCELLED the crumble movement, and
stranded the script active forever (avatar reads controllable, but every navigation step wedges).
Only wattson_done's RNG fired a wild battle at exactly the wrong spot to expose it; fresh runs
and rocksmash_taught happened to dodge it. FIX: after the rock object is gone, wait for the
field SCRIPT to fully clear (pressing NOTHING, so the crumble movement isn't interrupted) before
returning. PROVEN: full wattson_done → HEAT BADGE, 0 derails (was a deterministic hang at
f74383); rock-smash speed preserved (~20s/leg). Lesson (08-MISTAKES): "object gone" is not
"script done" — a field script can outlive the object it removed; wait for the SCRIPT.

## 2026-07-23 — KI-16 fix VALIDATED (5/5 wattson_done batch clean); KI-15 narrowed
Re-ran the wattson_done milestone batch that was 5/5 DETERMINISTIC HANGS before the KI-16
fix: now **5/5 reached the HEAT BADGE, 0 hangs / 0 derails / 0 whiteouts.** KI-16 confirmed
closed. KI-15 (after-faint chooser hang): ruled out the matchup chooser (returns a valid
pick for the exact run05 party); narrowed to the low-level PARTY_MENU navigation sweep
hitting a transient no-input-task state. Left documented with a repro-construction plan
(Shedinja fault-injection driver) rather than guess-patching the tuned battle handler.

## 2026-07-23 — KI-15 repro session: trigger PATH pinned; infrastructure built; race still to force
Focused attempt to reproduce the after-faint PARTY_MENU hang. Built repro infrastructure
(`--inject-shedinja-faint` party injection + the `faintrepro` no-flee spin driver) and pinned
the exact trigger PATH (previously fuzzy): the forced PARTY_MENU only opens when the strategy
ATTEMPTS TO FLEE and the active mon FAINTS that same turn (wild faster) — a race. Ruled out
several mechanisms this session (field-poison faints outside battle; low-HP leads flee before
fainting; no-flee routes through the dialogue send-out path; Wonder Guard blocks the normal
faint). NEXT: 1-HP actives SLOWER than the wild + the fleeing story strategy to force the race,
capture the transient PARTY_MENU state, then fix the sweep. Full analysis in KI-15. Did NOT
guess-patch the tuned battle handler. KI-16 (fixed this morning) remains the session's landed win.

## 2026-07-23 — KI-15 RE-DIAGNOSED: it is NOT a party-menu hang (corrects the two entries above)
Pulled the ACTUAL confirmed-hang logs (livetest-runs/…/run05 + two archive run01s) instead of
trusting the prior write-up. Finding: **the "after-faint PARTY_MENU Shedinja chooser hang" never
existed in any log** — `grep -r "SHEDINJA fainted"` across every run.log returns ZERO hits; the
cited party/coords/stack are nowhere. The prior two entries (and the KI-15 doc) chased a phantom.
The REAL KI-15, from 3 genuine 20k-frame hangs, is a **post-battle STORY-RESUME hang**: after an
inline battle (trainer/wild) interrupts story navigation/a scripted scene, the flow can't resume —
shared stale reads `cb=ReturnFromBattleToOverworld` + `instr=BattleScript_PayDayMoneyAndPickUpItems`
+ `tasks=[]`. Two manifestations: (1) `_wait_until_cutscene_over` rides forever → 8000 raise →
caller retry → loop (RUSTBORO, return_devon_goods); (2) `navigate_to` bounces between adjacent
tiles `(5,6)↔(5,7)` (ROUTE 104, after a trainer battle). Proved the after-faint sweep is ROBUST
(burn-injection repro: 5 back-to-back faints, 0 livelock) — it is NOT the cause. Added env-gated
(`KI15_TRACE`) reader+script-pointer instrumentation to `_wait_until_cutscene_over`; a faithful
`--driver story` run from goods_recovered rode the scene CLEANLY (the healthy path works — the hang
needs the rare battle-interrupt race). KI-15 remains OPEN with an accurate diagnosis + next steps
in 05-KNOWN-ISSUES. Did NOT guess-patch. Reverted the (wrong-path) battle_handler instrumentation.

## 2026-07-23 — KI-15 FIXED (both manifestations + a third found live), each proven on a captured state
Attacked KI-15 with the repro-first method; THREE distinct defects found and fixed:
1. **`navigate_to` had no no-progress bail** (manifestation 2, the ROUTE 104 `(5,6)↔(5,7)`
   bounce): its re-path loop retried FOREVER when the avatar could not advance (post-battle
   transition wedge). FIX (`walking.py`, forked file): after a leg timeout with no script
   active, wait bounded for a settled avatar, then track NET progress across re-paths —
   ~8 consecutive re-paths visiting only recently-seen tiles raises the new
   `NavigationStuckError` (a BotModeError → StoryMode's derail recovery owns it). PROVEN
   A/B by `repro_navigate_stuck.py`: oscillation + freeze spun 25k frames before, bail in
   ~230 frames after; healthy arrivals + genuinely-progressing (NPC-blocked) navs unaffected.
2. **The stale post-battle BATTLE-text wedge** (manifestation 1, RUSTBORO): a wild battle
   fled DURING a scene ride leaves `Got away safely!`/`grew to LV. N!` waiting for input
   with NO field script running, and it blocks ALL input except A (A clears it instantly;
   B NEVER does — proven frame-by-frame on the captured `ki15_gotaway_wedge.ss1`).
   ‼ KEY PROBE RESULT: that wedge is **indistinguishable from a field dialogue's parked
   `WaitForAorBPress` tail (the museum greeter) on EVERY reader — and both ignore B**.
   THREE rider-side designs failed and were reverted, each caught by re-running probes
   before commit: a broad-waiting 40-frame B→A escalation re-opened the greeter every 40
   frames; a "narrow sTextPrinters" signal read False on the real wedge; even a 450-frame
   B→A escalation looped, because the tail never expires either. The rider is therefore
   REVERTED to its old museum-green behavior (parked waits = free, return;
   `repro_cutscene_waiting_msg.py` pins that contract).
3. **The actual wedge-clearer — StoryMode.run's position-frozen persistence nudge**: the
   wedge's ONE unique property is that it BLOCKS ALL MOVEMENT. When `OVERWORLD + no
   battle + waiting-for-input + no scripts + PLAYER POSITION UNCHANGED` holds for **240
   consecutive frames**, press ONE A, then a 1200-frame cooldown. A dialogue tail can't
   match (the story keeps walking → the position changes); a live dialogue's script
   context resets the count. ‼ The first (every-frame, cb-gated) version of this nudge
   CREATED a new wedge — `cb=ReturnFromBattle` is stale after every battle, and A-mashing
   re-opened the Rustboro nurse dialogue forever (captured as `ki15_nurse_wedge.ss1`).
   navigate_to's fast bail (fix 1) feeds the derail loop whose _play re-runs give the
   nudge its counting window, so the two compose: wedge → bail ~230f → nudge A ≤240f →
   navigation succeeds.
Faithful validation (`goods_recovered.ss1 --driver story`): the wedge episodes that
previously hung terminally now SELF-RECOVER; runs end only at this thin save's DESIGNED
rival stop ("couldn't beat the rival in 3 tries" — solo L18 Marshtomp) or run the budget
out mid-progress (one 90k run crossed Rusturf → Woods → Dewford → Granite Cave, 0 Manual).
museumprobe2 green with the final (reverted) rider. New tools: `repro_navigate_stuck.py`,
`repro_cutscene_waiting_msg.py`, `probe_stuck_state.py` (frame-step any captured wedge),
`probe_press_variants.py` (which input clears a wedge), `probe_ride_fixed.py`; captured
states `ki15_gotaway_wedge.ss1` + `ki15_nurse_wedge.ss1`. Full-batch validation rides the
overnight run.

## 2026-07-24 (overnight) — CH12 BUILT + WIRED: Lavaridge→Petalburg→Norman→Surf (Segments 12a/b/c)
The whole Ch12 arc is implemented and mechanically validated live to Norman's room
(ch12_run9: 500k frames, 0 hangs / 0 Manual — travel, doors, challenge, whiteout
recovery and boss-training all exercised; the Norman WIN itself is level/RNG-bound on
the thin flannery_done test team and rides the long overnight run). Ten iterations of
build→run→probe→fix, each bug diagnosed on captured state or decomp, never guessed:
- **Route (recon overturned the 2026-07-23 note):** DIRECT Lavaridge → Route 112 ledges
  → Route 111 south — the Fiery Path is topologically USELESS here (its doors connect
  lower R112 to the R113 side), and the desert never touches the Ch10-proven corridor.
  Twin rocks respawn → southbound re-smash (18,101) from the north (idempotent).
- **Rusturf wall:** the tunnel's mid-wall is TWO permanent-flag Rock Smash rocks
  (24,4)/(24,5) (the Wanda quest — decomp/probed); smash + reunion-scene ride wired.
- **Petalburg Woods:** exit via the SOUTH-EAST door (36,38) EXPLICITLY — the warp graph
  is region-blind on the Woods-split Route 104 and exited the NORTH door onto the sealed
  half (ch12_run2); the y<38/≥39 split now gates the blocks.
- **Gym doors are SIGN SCRIPTS, not tiles** (decomp-verified after runs 4-8 wedged
  walking into a collision-blocked door): face the door from below, A, YES → warpdoor.
  Chain: Speed→(Randall)→Confusion→(Parker)→LeftStrength→(Jody)→GymLeaders→Norman.
  Walking into the closed door had exposed a NEW wedge shape (heldMovementActive stuck,
  input-starved, reload-defused — states/analysis under saves/ki15_gymdoor_wedge.ss1).
- **Surf handoff is FULLY AUTOMATIC** (decomp): the Norman-defeat script itself brings
  Wally's Dad in and warps to the HM03 handout — the rider just rides; no step-down
  trigger exists (the map has ZERO coord events; the earlier spec note was wrong).
- **Infra fixes en route:** warp-aware heal_in_pokemon_center (a post-derail resume
  healed from INSIDE the gym → "not on connected maps" → Manual, ch12_run3);
  standing-on-warp step-off-step-on in navigate_to_anywhere + _enter_warp_by_navigation;
  travel `order` covers every corridor map (a Woods derail re-ran the MAUVILLE leg
  BACKWARDS, ch12_run1); harness save-on-stuck re-arms per stall episode; jolt taps in
  navigate_to's settle-wait + follow_waypoints for input-starved post-battle freezes.
- **livetest END_MARKERS**: + "Surf taught" (Ch12 content end).

## 2026-07-24 (overnight) — KI-17 opened + sweep hardened: the after-faint reshow DMA race
Batch 20260724-004252 (5 fresh lanes, 3M frames): **3/5 reached the HEAT BADGE frontier
organically, 0 Manual** (KI-15's fix class held); 2 lanes froze IN BATTLE with the same
signature — the party menu's return-to-battle transition parked forever
(CB2_SETUPRESHOWBATTLESCREENAFTERMENU + both error-text tasks alive, input-immune).
‼ One lane's party/coords match the ORIGINAL "KI-15 Shedinja chooser" write-up verbatim —
that bug was real all along, merely mislabeled; now logged properly as KI-17 with TWO
captured states (ki17_partymenu_wedge*.ss1). Gemini decomp analysis (archived
tools/story-dev/gemini-ki17-answer.md, prompt in GEMINI-PROMPTS.md): selecting a living
mon while the "no energy left!" printer tasks are winding down exits the menu WITHOUT
destroying the printer → orphaned DMA request → ReshowBattleScreenAfterMenu waits on
IsDma3ManagerBusyWithBgCopy forever. handle_fainted_pokemon's sweep hardened per the
analysis: 24-frame post-dismiss gap, A only on a VERIFIED living cursor slot, never a
blind A when the cursor is unreadable. Validation rides the next fresh batch.

## 2026-07-24 (overnight, cont.) — Ch13a-c SKELETON built + wired (Surf arc to Fortree); Norman balance note
§Ch13 spec written (flags audited — 2 phantoms dodged: gate the rival on
HIDE_ROUTE_119_RIVAL/RECEIVED_HM_FLY, never "DEFEATED_RIVAL_ROUTE_119"/"RECEIVED_HM02")
and the skeleton BUILT + WIRED behind the RECEIVED_HM_SURF gate: `travel_to_fortree`
(Mauville → R118 Surf crossing → R119 → Fortree; the pathfinder Surfs natively once
BADGE05 + a Surf mon hold), `do_weather_institute` (Shelly; completion =
HIDE_ROUTE_119_TEAM_AQUA; Castform if a slot is free), `fight_route119_rival_and_get_fly`
(bridge rival → HM02). ⚠ First-run-validate leads: the Surf crossing, the east-bank
Steven scene, institute interior tiles. END_MARKERS += "FORTREE reached".
NORMAN BALANCE (2M-frame run): 6 attempts, boss-training cycled correctly (Mightyena
L23→33), 0 hangs/Manual — but the flannery_done test team has no Fighting answer to
Truant Slaking and hadn't broken through by budget end. Fresh teams carry Combusken —
the end-to-end validation rides the big fresh batch (5 lanes × 5M frames).

## 2026-07-24 (overnight, cont.) — Ch13d/e SKELETON: Devon Scope + Fortree Gym (Winona)
Recon (mapfacts): Route 120 Steven (13,15) + BridgeKecleon (12,16); Fortree gym-path
Kecleon (25,8) flag 969; gym door (22,11)↔(15,24); Winona (15,2) + 6 trainers. Built +
wired behind the Ch13a-c flags: `get_devon_scope` (Steven scene → Scope → flush the city
Kecleon, judged by the OBJECT disappearing) and `do_fortree_gym` (turnstile live-grid
re-path + push-into-the-door rotation fallback → Winona challenge in the Brawly
pattern; Flying-answer lead + Fortree heal in _play). END_MARKERS += "FEATHER BADGE
earned". ⚠ All of Ch13 is SKELETON pending a post-Surf save (the big fresh batch is
grinding toward one); expect first-run iteration like Ch12's (runs 1-9 found 6 bugs).

## 2026-07-24 (overnight, cont.) — ★ NORMAN BEATEN ORGANICALLY: Ch12 validated end-to-end; norman_done.ss1 captured
Big-batch lane 1 (fresh, 5M frames) beat NORMAN with a natural team (Blaziken L36 lead)
and received HM03 Surf — BADGE05_GET + DEFEATED_PETALBURG_GYM + RECEIVED_HM_SURF all
verified on the captured state, promoted to **saves/norman_done.ss1** (controllable,
Petalburg (7,6), 5-mon party). The full new-content chain (travel → Wanda wall → Woods
SE door → sign-door gym chain → Norman → automatic Surf handoff) ran organically.
The lane then dropped to Manual in Segment 12c: `ensure_hm_learner` picked ROUTE 117
hunting grounds — warp-locked from Petalburg (the warp graph calls them one region;
the plain planner can't cross the tunnel) — 10 failed navigations. FIXED: Route 102
(9,2) promoted into TRAINING_GRASS (two-way swept; hosts Lotad/Surf-learners) and the
hunt now picks the furthest-progressed ground that is STATICALLY PATHABLE from the
current position, falling back to the old pick. PROVEN live (ch13_run1 from
norman_done): hunted Route 102, caught a Zigzagoon carrier, taught Surf, and the
Surf-aware planner then opened the Route 103 river shortcut and crossed Route 118 —
Ch13a executing. Batch scorecard (20260724-070630): 1× Norman+Surf (the 12c Manual),
2× budget-INCOMPLETE deep in the Norman cycle (healthy), 2× pre-jolt-fix wedges
(their fixes landed in 54f9537e mid-batch; states batch3_run0{1,2,3,5}*.ss1 captured).

## 2026-07-24 (overnight, cont.) — Ch13a-c VALIDATED (Surf→Institute→Fly→Fortree); 13d blocked on Route 120 bridges
Eleven live iterations from norman_done proved the Ch13 skeleton segment by segment,
each failure captured + diagnosed + fixed (states saves/ch13_r*_wedge.ss1):
- **13a-c SOLID:** teach Surf (reachable-grounds hunt) → Surf-cross Route 118 →
  Route 119 north (institute-door leg tile (6,33)) → Weather Institute (deterministic
  1F-stairs→2F-Shelly sweep) → bridge opens → Route 119 rival via COORD TRIGGER (25,31)
  reached by a HELD-INPUT bridge walk (planner-blind spans) → **HM02 Fly received**
  (VAR_ROUTE119_STATE=1) → travel reaches Fortree/Route 120. Six general fixes landed
  from this (all in the playbook): phantom-escape in _ride_out_all_scenes, choice-aware
  scene rides, `_hold_walk_route` (releases the prior leg's direction), coord-trigger
  targeting, `_clear_stale_battle_message`, and Fortree-side travel `order` ranking.
- **13d BLOCKED (needs-work):** `get_devon_scope` — Steven's scene is at the Route 120
  NORTH BRIDGE (13,15); after it the avatar sits at (13,16) and the walk back to Fortree
  crosses planner-blind bridge tiles → NO-PATH → Manual (runs 8/10/11, deterministic).
  NEXT: live-probe Route 120's bridge topology (which held-input route (13,16)→Fortree
  west connection), then `_hold_walk_route` off the bridge before the city-Kecleon flush.
  13e (Winona turnstile gym) is untested behind this. Milestone for the fix: ch13_r8_wedge.
Honest boundary per the overnight directive (move on after repeated retries): 13a-c is a
real, validated advance; 13d/e resume from the captured states with a clear next step.

## 2026-07-24 (overnight, cont.) — Ch13d Devon Scope WORKS end-to-end (real path); blocker moved to the Fortree tree-bridge
Solved the Route 120 north-bridge strand (the runs 8-11 wall): Steven's scene leaves the
avatar on ISOLATED tile (13,16) — probed that EVERY direction snaps to (13,15) and the
planner NO-PATHs from it — so a HELD-INPUT route (Up→(13,15), Left→(5,15)) gets off it,
where the planner reaches Fortree. Factored `_leave_route120_north_bridge` and call it
from get_devon_scope's flush, do_fortree_gym's entry, AND _play before the gym prep
(three resume paths). Captured `saves/devon_scope_got.ss1` (post-Scope checkpoint via
SAVE_CHECKPOINT=RECEIVED_DEVON_SCOPE:devon_scope_got). RESULT (run 13, real path from
ch13_r8_wedge): the bridge escape works — the run crossed Route 120, flushed the city
Kecleon, healed at Fortree PC, and reached the **Fortree gym door (22,11)** before failing.
NEW/REMAINING blocker: Fortree is a TREE-BRIDGE city — the gym door (22,11) is reachable
only from adjacent (21,11)/(22,12), not from the main plaza (5,7) (planner-blind elevation
walkways, the Route-119/120 bridge class). NEXT: capture a clean Fortree checkpoint
(SAVE_CHECKPOINT can't key a flag here — regenerate by running to Fortree and hand-saving
when controllable at the PC), probe the held-input route plaza→(21,11), and add it to
do_fortree_gym before the door warp. Then 13e (Winona turnstile gym) is next-untested.

## 2026-07-24 — Fodder-grass prep fix + the general HM/TM teach wedge (first /orchestrate run)
Two user-reported bugs, both fixed and proven. Run as the first real test of the
orchestration pattern (doc 16): 3 cheap explorers + 1 mid implementer + mid verifier/reviewer,
with the premium tier doing triage, the spec, the judgment-dense wiring, and the gate.

**(1) TRAINING GRASS — the bot ground L3-4 wilds with a L27-31 team (user report).**
Each boss carried a hardcoded local `grass`; for NORMAN that is Route 102 (L3-4) because his
gym is the geographically EARLIEST yet is fought 5th — ~25 xp a kill, i.e. never. Now
`_prepare_for_fight` measures the local patch against the team and, when it is fodder
(`wild_max + FODDER_LEVEL_GAP(12) < team_max`), either RELOCATES to a better area or, if none
is genuinely reachable, SKIPS the grind so the boss re-attempt does the levelling (Gen 3 keeps
mid-battle xp through a whiteout: two of Norman's mons ≈ 1,200 xp). New
`training_areas.best_training_area(team_level, min_wild_max=, allow=)` + 5 new verified areas;
heals move to the PC nearest the CHOSEN area (the cave-heal lesson).
‼ RECON RESULT worth keeping: at the Norman moment there is genuinely nowhere better —
pre-Surf, everything reachable from Petalburg is L2-5 and every L19-28 band is across water or
on the far side of the Go-Goggles desert. So SKIP is the correct answer there, not travel.
Proof (decision table, norman_done.ss1): NORMAN L31 -> SKIP; WATTSON L24 / ROXANNE L17 / early
L9 -> TRAIN LOCALLY, i.e. **proven-good prep is untouched** — the gap is deliberately 12
(more conservative than the reactive boss-training check's 8) precisely so it only fires on
the pathological case.

**(2) HM/TM TEACH WEDGE — general, not Surf-specific.** `ensure_hm_learner` returned the frame
a caught mon registered, while the catch aftermath ("Give a nickname to the captured
ZIGZAGOON?") was still on screen; `teach_hm_move` then opened the BAG on top of the pending
prompt and wedged in BAG_MENU until the watchdog (evidence: ch13_run1.log f9931 — teach_hm_move
in the stack, BAG_MENU, that nickname text). Both functions now `normalize_to_overworld()`
first (B-rides the prompt; B answers the nickname "no" and can never start an NPC
conversation). Exposed every HM path, incl. Rock Smash. PROVEN A/B by the new
`tools/story-dev/repro_teach_under_dialogue.py`, which drives the REAL `teach_hm_move`
generator: pre-fix the bag-open fires onto the pending dialogue and fails; fixed, normalize
provably runs first and the bag opens; healthy no-dialogue control unaffected.

**Orchestration ledger:** delegated = 3 explorer recons + 1 implementer (data + picker) +
verifier proof + adversarial review; kept premium = triage, the spec, `_prepare_for_fight`
wiring, the reachability predicate, all thresholds, the gate. Kick-backs = 1 (explorer's
first-tile sampling produced data contradicting known ground truth). Overrides = 3, all from
MY incomplete spec, all caught by the gate: level-fit picker proposed Route 121 (past
Lilycove, Surf-gated); Route 111's tile is north of the desert so "same map" != reachable;
first threshold would have silently changed Wattson/Roxanne. Net: the pattern moved the grunt
work off-tier and the GATE, not the workers, is what protected quality — exactly doc 16's thesis.

## 2026-07-24 — 3-starter validation batch + `ensure_facing_direction` absolute bound (#24)

**Docs:** added `PROJECT KNOWLEDGE/17-PORTABLE-ORCHESTRATION-GUIDE.md` — a PROJECT-AGNOSTIC
write-up of the multi-agent structure (tier table, governing rule, 5 roles, handoff contract,
review gate, metrics, anti-patterns, 30-minute adoption path, measured outcome). Doc 16 stays
the Pokébot-specific version; 17 is the one to lift into any other Claude Code repo. Written
at user request so the structure can be logged and improved independently of this project.

**Test batch:** three starter-locked fresh runs (`profiles/starter-{treecko,torchic,mudkip}`,
`story.yml: starter: <name>`) run to their stopping point to hunt starter-specific bugs.
Results — treecko 2,195,761f / 38 maps / reached **Route 120 in `get_devon_scope` (Ch13d)**
with **Castform L25** in party (proves Weather Institute cleared); torchic 1,650,182f /
27 maps / hung at Route 111 (18,99); mudkip 2,113,515f / 34 maps / tripped the
"too many whiteout recoveries" guard. No starter-SPECIFIC logic bug found — all three failed
on shared navigation/attrition paths, which is the useful result: the chapter code is
starter-agnostic and the remaining defects are in movement and prep.

**Fix — `ensure_facing_direction` unbounded press loop** (`modules/modes/util/walking.py`).
Torchic hung at Route 111 (18,99), the SAME tile as batch2 run04. Both existing guards are
BRANCH-LOCAL, and a post-battle state exists that reaches neither: the avatar reads perfectly
settled (OVERWORLD + NOT_MOVING + NOT_MOVING), so we take the "press the direction" branch,
which RESETS `starved_frames = 0` every frame — while the press never lands and
`facing_direction` never changes. Added a branch-INDEPENDENT `total_frames > 1800` bound that
raises `BotModeError`, converting a silent forever-hang into a recoverable derail.
`repro_input_starvation.py` and `repro_navigate_stuck.py` both re-verified passing.

**Prevention rule:** a loop guard that lives inside ONE branch cannot bound a loop that can
spin in ANOTHER branch — every `while True` needs one counter incremented unconditionally at
the top, no matter how many per-branch counters it already has.

## 2026-07-24 — harness stuck-dumps now print the ACTIVE FIELD SCRIPTS (#24)

`tools/story-dev/story_harness.py`: added `_script_names()` and wired it into both the
`STUCK-OW` and `NO-PROGRESS` dumps. **Why this mattered:** three long runs all died on
Route 111 (18,99) and none of my harness logs could explain it — the harness printed tasks,
battle callback, battle instruction and the generator stack, but NOT the field-script stack.
The user's in-game DEBUG dump does print it, and that one field cracked the case: it showed
`EventScript_SmashRock` still reading ACTIVE 140,000 frames after the bot had dropped to
Manual mode and stopped pressing anything. A parked field script swallows input and wedges
every script-gated wait downstream, so it is a first-class "why is nothing progressing"
signal. Verified: `story_harness.py` parses clean (note: the file carries a UTF-8 BOM — read
it with `encoding="utf-8-sig"`, plain `utf-8` raises `SyntaxError: U+FEFF`).

**Prevention rule:** when a wedge is undiagnosable from a log, the first fix is to the DUMP,
not to the code — add the missing field before forming a theory about the bug.

## 2026-07-24 — `_navigate_riding_out` fails fast on a hopeless retry (#24)

**The bug two independent runs died on.** A user run (12:39) and my treecko starter run BOTH
wedged in `get_devon_scope`: after Steven's scene, `_leave_route120_north_bridge()` parks the
player at ROUTE120 (5,15), and the follow-up `_navigate_riding_out(FORTREE_CITY, (24,8))`
fails every time. The wedge dump shows `scripts=[]` and an idle task list — nothing is
happening, the planner simply cannot route there.

**Why a pathing failure became a watchdog death.** `_navigate_riding_out`'s retry loop exists
for scenes: a cutscene aborts the path, we ride it out, the world changed, we retry. But when
the failure is a PLAN failure with an idle field, riding out costs
`_ride_out_scripted_scene`'s 240-frame engage wait and changes nothing. `get_devon_scope`
wraps it in a 10-round loop with `tries=6` ≈ 14,400 frames of pure churn — past the 18,000
frame global watchdog. So the run died with "watchdog" instead of the planner's real message.

**Fix.** After a failure, if the field is idle (`not script.is_active` and
`player_avatar_is_controllable()`) AND the player stands on the same tile as after the previous
failure, raise immediately with the planner's own error. One ride-out is still attempted first,
so a genuine scene interruption is unaffected.

**PROVEN A/B** by `tools/story-dev/repro_navigate_failfast.py` (from `rocksmash_taught.ss1`,
state verified at load rather than trusted by name):
- unreachable dest, idle field: **1530 frames → 255 frames (83% less churn)**, and the error
  now names the real cause instead of "after 6 tries".
- control 1 — reachable dest still succeeds in 33 frames, arrival at the tile verified.
- control 2 — with the script context reporting active, the guard does NOT fire and all tries
  are exhausted exactly as before.

**NOTE:** this fixes the CHURN, not the underlying reachability. Whether ROUTE120 (5,15) →
FORTREE_CITY is genuinely unplannable (suspected planner-blind bridge, the Route 119/120 class
that `_hold_walk_route` exists for) is still being probed. The bot will now fail honestly and
fast there rather than dying to the watchdog.

**Prevention rule:** a retry loop must be able to state what it expects to CHANGE between
attempts — if nothing observable changed, retrying is not resilience, it is a way to convert a
clear error into a timeout.

## 2026-07-24 — Fortree Kecleon flush targeted a WALL tile (#24) — the two-run killer

**Root cause, probed live** (`tools/story-dev/probe_route120_to_fortree.py`). `get_devon_scope`
navigated to `FORTREE_CITY (24, 8)` to face the gym-path Kecleon. That tile is
**unreachable by game design**: `collision=1, elevation=0, tile_type='Normal',
accessible_from_direction=[False, False, False, False]` — it is ground BENEATH the
tree-bridge. The Kecleon at `(25,8)` stands on the ELEVATED walkway, which is the `x=25`
column at **elevation 3**. No path to `(24,8)` will ever exist, which is why the retry loop
spun with `scripts=[]` and an idle task list until the watchdog killed the run.

**Fix.** Target `FORTREE_CITY (25, 7)` — one tile north of the Kecleon on the same
elevation-3 walkway — and face `"Down"` instead of `"Right"`. Probed: plans from
ROUTE120 (5,15) in a single hop, no `_hold_walk_route` needed for this leg.

**The control that makes this trustworthy:** `FORTREE_CITY (5,6)` IS reachable from the same
start, and every other tile this chapter already uses (ROUTE120 (13,15)/(14,15)/(13,16),
ROUTE119 (17,34)) plans fine. So neither `calculate_path` nor the ROUTE120↔FORTREE_CITY
connection was ever broken — exactly one tile was wrong. My own hypothesis going in
(planner-blind dual-elevation bridge, the Route 119/120 class) was WRONG, and the control
is what proved it wrong rather than confirming it.

**Also corrected:** `devon_scope_got.ss1` loads at ROUTE120 **(13,16)**, not (5,15) — it is
the pre-`_leave_route120_north_bridge()` strand tile. Third save state in this repo found to
be misnamed or mis-assumed.

**Prevention rule:** before blaming the pathfinder, dump the DESTINATION tile's collision and
elevation — "unreachable" is far more often a wrong target than a blind planner, and one
control tile on the same map separates the two in seconds.

## 2026-07-24 — Ch13d resume skipped the Kecleon flush; harness task dump was broken (#24)

**Bug 1 — one gate for two jobs.** `story_mode.py` ran `get_devon_scope()` only when
`RECEIVED_DEVON_SCOPE` was unset. But that function does TWO jobs: get the Scope from Steven,
AND flush the Fortree gym-path Kecleon. So any resume that already had the Scope skipped the
flush as well — leaving the Kecleon on (25,8), the single chokepoint tile to the gym door, so
`do_fortree_gym` NO-PATHs to (22,11) forever. **Not a milestone-only artifact:** derail
recovery re-runs the resume, so in a fresh run any derail near Fortree falls into the same
trap. The Ch13d validation run derailed 5× on exactly this and never logged
"flushing the invisible thing" once. Fixed: gate on `RECEIVED_DEVON_SCOPE` OR
`HIDE_FORTREE_CITY_KECLEON` being outstanding (both sub-steps are already idempotent inside
`get_devon_scope`), plus a `_guard` on each flag so a silent skip can't recur.
STATUS: logic fix; end-to-end proof still blocked by an unrelated earlier derail in the
milestone save (`_leave_route120_north_bridge`, under diagnosis).

**Bug 2 — my own observability fix was broken (shipped 2026-07-24 in `67c777e5`).** Every
dump printed `tasks=<err 'Task' object has no attribute 'name'>`. The attribute is
`Task.symbol`, not `.name`. Fixed and CONFIRMED live — dumps now read
`tasks=['Task_WeatherMain', 'Task_RunPerStepCallback', 'Task_MuddySlope', ...]`.
While fixing it I found the PRE-EXISTING `STUCK-OW` branch carried the identical `t.name`
bug, but its bare `except` swallowed it into a silent `tasks="?"` — broken invisibly for an
unknown length of time. Removed the swallow so any future breakage announces itself.

**Prevention rule (second instance today).** A silent fallback in a debug path hides the exact
defect the debug path exists to reveal — first a filtered list reading as `[]`, now an
exception reading as `"?"`. Diagnostics must fail LOUD: print the error, never a placeholder.

## 2026-07-24 — HM moves can no longer be offered for deletion; move-learn valve survives re-entry (#24)

**User report (run 15:13, killed by hand).** A Pokémon levelled up and the bot tried to
replace an **HM move** (Rock Smash). In Gen 3 an HM cannot be forgotten — only the Move
Deleter removes one — so the game refuses and bounces back to the prompt. Two interleaved
infinite cycles resulted: `AskWhetherToLearn → SelectMoveToReplace → AskWhetherToLearn` and
`AskWhetherToLearn → ConfirmCancellation → AskWhetherToLearn`.

**Fix 1 — HM VETO at the shared dialogue layer** (`modules/battle_move_replacing.py`).
StoryMode's own policy already filters HMs on every branch and provably cannot return an HM
slot — so the trigger was NOT there. But this handler is reached by EVERY strategy: the stock
`DefaultBattleStrategy` (no HM exclusion at all), the catch strategies that inherit it, and
the `except Exception` fallback that blindly picks **slot 0** without consulting any policy.
Rather than chase an unreproducible trigger, the game's own rule is now enforced at the one
layer nothing can route around: if the chosen slot holds an HM, DECLINE instead.

**Fix 2 — the safety valve now survives re-entry.** The 6000-frame valve fired correctly, but
`battle_handler`'s outer `while battle_is_active() or _learn_or_evo_pending()` loop re-invokes
the generator FRESH, resetting `frames_in_dialogue` to 0 — so every invocation looked bounded
while the whole thing looped forever. Added module-level `_STALLED_EXITS`; three stalled exits
raise `BotModeError` so mode recovery takes over. Every NON-stalled exit resets it (both the
clean `DialogueNotActive` break AND the evolution hand-off break — the latter was missed on
the first cut and caught by the review gate, which is exactly the "counter that only
increments" failure mode).

**PROVEN A/B** (`tools/story-dev/repro_hm_move_replace_loop.py`, live, real generators):
- killer arm (`--force-slot 2`): **BEFORE** 3 invocations, still looping at 21,000 frames,
  offer never resolved → **AFTER** 1 invocation, 428 frames, declined cleanly, Rock Smash
  retained.
- control (no injection): unregressed — policy picks slot 3 (Bide), Take Down learned,
  416 frames, 1 invocation.
- control (`--force-decline`): unregressed — 428 frames, 1 invocation.
- valve simulation: fires on attempt **3** (not 1 — no over-eager abort) and raises
  `BotModeError` instead of looping.

**Prevention rule (third instance today).** A guard that is live and correct can still be
structurally unable to fire. Branch-local counters can't bound a multi-branch loop
(`ensure_facing_direction`); per-invocation counters can't bound a re-entrant caller (here).
Ask not "is there a bound?" but "what resets it, and who can reset it without fixing anything?"

## 2026-07-24 — 0-PP move selected forever in unfleeable trainer battles (#24)

**Found live** in batch2's fresh treecko run: 15,000 frames of no progress with
`instr=BattleScript_SelectingMoveWithNoPP`, `bt="There's no PP left for this move"`, inside
`EventScript_DoTrainerBattle`.

**Root cause — a wrong comment that became a wrong assumption.** All three trainer-battle
fallbacks in `story_mode.py` ended with `use_move(0)  # nothing usable → the game uses
Struggle`. Gen 3 does NOT do that: Struggle is auto-used only when EVERY move is at 0 PP (and
then the menu never appears). Hand-pick a 0-PP move while others still have PP and the game
prints "There's no PP left for this move!" and re-opens the menu — an infinite loop in a
battle that cannot be fled. And `move_is_usable` is STRICTER than "has PP" (it also rejects
disabled and zero-power moves), so a mon can fail every usability check while still holding
perfectly selectable moves.

**Fix.** A PP-only second pass before the fallback, in ALL THREE sites: `decide_turn`,
`decide_turn_in_double_battle` (found by the review gate — it carried the identical pattern,
and its own docstring names the Rustboro Youngster pair, a trainer DOUBLE battle), and the
out-of-balls shiny branch.

**PROVEN A/B** (`tools/story-dev/repro_nopp_trainer_loop.py`) against the real unmodified
`decide_turn`, with the pre-fix behaviour reproduced by starving the new loop of data rather
than reimplementing the old logic:
- BEFORE → `UseMove(0)`, slot 0 `pp=0`. AFTER → `UseMove(1)`, slot 1 `pp=10`.
- control: every move at 0 PP still falls through to `use_move(0)` so the game Struggles.
- control: when a strongest move exists, that path is untouched.
- control: ORDERING — a `move_is_usable` move still beats a PP-only candidate, so the new
  pass is a genuine last resort and never preempts the usability check.
- verified no crash path: in-battle `BattlePokemon.moves` skips empty slots (never `None`),
  and index 0 always exists since every Pokémon knows at least one move.

**Prevention rule:** a comment asserting emulator/game behaviour ("the game will handle X")
is a CLAIM, not documentation — either prove it or write the fallback so it does not depend
on the claim being true.

## 2026-07-24 — Prep grinds are now priced in frames before being committed to (#24)

**The user's original report, root-caused with measured numbers.** A fresh run spent ~2,000,000
frames grinding Route 102's L3-5 wilds and hit the frame cap one level short. Cause: the
evo-lookahead's `mon.level < evo_level <= mon.level + 3` guard budgets in LEVELS while the cost
is FRAMES. Combusken evolves to Blaziken at L36, so at L33 the bot committed to 3 "close"
levels that actually cost ~500,000 frames on that patch. The `"topup"` branch had no cost
estimate at all.

**Built:** `training_areas.estimate_frames_to_level(mon, target_level, wild_level)` +
`FRAMES_PER_WILD_BATTLE = 1433` (MEASURED — 83 real XP events via the faithful harness on the
captured save). Uses the REAL growth curve (`level_up_type.get_experience_needed_for_level`)
and the validated `xp = floor(base_exp * level / 7)` formula. Returns `None` when it cannot
estimate, and both callers treat `None` as over-budget.

**Gated:** the evo-lookahead and the sweeper top-up, on
`StoryMode.MAX_PREP_TRAINING_FRAMES = 250_000`.

**PROVEN** (`tools/story-dev/repro_prep_frame_gate.py`, real save `prenorman_fodder_grind.ss1`):
- the real failing decision — Combusken L33 → L36 on Route 102 — estimates **502,983 frames**
  → **REJECTED**.
- control — a well-matched grind estimates 34,392 frames → **ACCEPTED**.
- **regression control** — `repro_fodder_grass.py` passes UNCHANGED: Wattson trains locally on
  Route 117, Roxanne on Route 116, Norman skips the grind. Proven-good prep did not move.

**Also measured and worth recording:** the code's long-standing claim that a lost boss attempt
pays ~1,200 XP vs ~145 for a wild CHECKS OUT — KO'ing Norman's Spinda + Vigoroth pays 1,220 XP
against 28.7 for a Route 102 wild, a 42× ratio.

**Prevention rule:** a budget must be denominated in the unit you actually pay. "Within N
levels" / "within N tiles" / "N retries" all hide costs that vary by orders of magnitude with
context — price the plan, then decide.

## 2026-07-24 — Fortree Gym rotating gates SOLVED on paper; port validated against the emulator (#24-fortreegates)

**The old model was wrong in three ways** (both `12-STORYMODE-DESIGN.md` and the
`do_fortree_gym` docstring carried it), which is why the greedy
`push = "Up" if y > 3 else ...` fallback failed 100% of the time — measured: the avatar never
moved one tile across 30 rounds:
1. "State PERSISTS across exits" — FALSE. `MAP_SCRIPT_ON_TRANSITION` runs
   `RotatingGate_ResetAllGateOrientations` on EVERY warp in. Orientations reset every entry, so
   a plan from the entrance is valid on every attempt and re-entering is a legitimate reset.
2. "Runtime metatiles, live-grid class" — FALSE. Static collision NEVER changes. A gate is
   `(x, y, shape, orientation)`.
3. "When the path is sealed, push the blocking turnstile" — INCOHERENT. Gate logic is only
   consulted for a step onto a tile whose static collision is ALREADY OPEN, so a blocked tile
   is ordinary scenery that never reaches gate code. The bot was pushing walls by construction.

**The mechanics** (decomp `src/rotating_gate.c`, used by only 2 maps in the game): 8 gate
shapes (T/L forms, short/long arms), 4 orientations, a 4×4 per-gate box with only the 4 tiles
adjacent to the pivot acting as push faces; direction tables give CW/ACW + which arm, then
`has_arm` and `can_rotate` (swept tiles must be clear) decide. If an arm is present but cannot
swing, **the step is rejected — indistinguishable from a wall bump.**

**Observability: no new reader needed.** Gate bytes overlay `VAR_TEMP_0..VAR_TEMP_3`:
`orientation_i = (get_event_var(f"TEMP_{i//2}") >> (8 * (i % 2))) & 0xFF` for gates 0-7.

**Fortree's 8 gates:** (6,7)T2@90, (9,15)T2@180, (3,19)T2@90, (2,6)T1@90, (9,12)T1@0,
(6,23)T1@0, (12,22)T1@0, (6,3)L4@180.

**‼ PORT VALIDATED AGAINST THE LIVE EMULATOR.** A live probe measured which pushes work at
(4,19) — the exact tile the deepest real run died on — and the ported model agrees 4/4:
N blocked, S allowed→(4,20), W allowed→(3,19), E blocked. BFS over the real extracted collision
grid: solvable in 97 moves from the entrance (15,24), and **83 moves from (4,19)** — the bot was
never stuck, it just kept pushing the one direction that is genuinely blocked.

**Artifacts:** `tools/story-dev/fortree/{fortree_gate_solver.py,fortree_gym_map.bin,rotating_gate.c}`
and `tools/story-dev/probe_fortree_gates.py`.

**Prevention rule:** two agents reporting opposite conclusions usually means one of them
generalized from an unrepresentative sample. Reconcile by making the MODEL predict the
MEASUREMENT case-by-case — agreement on 4/4 specific cases is worth more than either report
alone.

## 2026-07-24 — Fortree Gym rotating gates SOLVED LIVE (#24-fortreegates)

**New module `modules/story/fortree_gates.py`** — a faithful port of the decomp's rotating-gate
rules (`src/rotating_gate.c`): arm-layout tables, `has_arm`, `can_rotate`, `rotate_in_direction`,
`get_rotation_info`, `try_move`, plus:
- `read_orientations()` — decodes gates 0-7 from `VAR_TEMP_0..3`
  (`(get_event_var(f"TEMP_{i//2}") >> (8 * (i % 2))) & 0xFF`). **No new memory reader needed.**
- `solve(start_xy, orientations, goal_xy=(15,3), blocked=frozenset())` — bounded BFS returning
  `"Up"/"Down"/"Left"/"Right"`, reading STATIC collision from the live map (not from a file
  under `tools/`). `blocked` carries live NPC tiles.

**`do_fortree_gym` rewritten.** The greedy `push = "Up" if y > 3 else ...` fallback is gone.
Each round: read position + orientations + live object tiles, `solve()`, execute ONE tile, and
re-plan — so a trainer interrupt self-corrects. `solve() == None` retries once WITHOUT NPC
blocking to tell "an NPC is transiently in the way" from "this gate configuration has no route";
the latter falls through to a bounded exit-and-re-enter (orientations reset on entry, so that is
a guaranteed clean slate), capped at 2 cycles. Rounds/moves/frames all bounded.
‼ `calculate_path`/`navigate_to_anywhere` are NOT used for movement inside this gym — they do
not model gates and return routes whose first step walks into a gate arm.

**PROVEN, live, through the full production listener stack** (`tools/story-dev/repro_fortree_gate_solver.py`):
- push agreement at (4,19): **4/4** vs the real emulator (N blocked, S/W allowed, E blocked).
- route lengths **83** from (4,19) and **97** from (15,24) — exact.
- 16/16 solver-predicted moves executed live, including real gate rotations.
- **Live drive reached (15,3) — `best_dist=0` — in ~38,000 frames**, self-routing around THREE
  trainer NPCs (including the one that previously hung the climb forever), zero stalls.

**The `VAR_TEMP` decode was validated the hard way.** The acceptance check on
`fortree_gym_wedge.ss1` read `(1,2,1,1,0,3,1,2)`, not the documented default. Rather than relax
the assertion, the save's own computed exit route was walked, the gym exited through the warp and
re-entered — and it then read exactly `(1,2,1,1,0,0,0,2)`. One experiment proved the decode is
right, that the save is a mid-walkthrough capture with 2 gates already turned, AND that
reset-on-entry works in practice.

**NOT done: the badge.** The isolated drive lost to Winona and whited out, because it calls
`do_fortree_gym()` directly with whatever party the save carries. Battle prep (lead selection +
heal) is the CALLER's job — `StoryMode._play` already does `_lead_best_matchup(["Flying"])` +
`heal_in_pokemon_center(FortreeCity)` first, exactly like the sibling gyms. So BADGE06 needs a
full-chapter run to confirm, not a gate fix. Filed `#24-fortreebadge`.

**Prevention rule:** when a model and a live measurement disagree, the cheapest decisive move is
often to CHANGE THE WORLD to the state the model assumes (here: exit and re-enter to force the
documented reset) rather than to argue about the reading or relax the check.

## 2026-07-24 — Fortree: a parked trainer is escaped by RESETTING the room, not by waiting (#24-fortreegates)

**User mechanic (2026-07-24):** leaving and re-entering Fortree Gym resets **NPC positions** as
well as the gate orientations. That makes the exit-and-re-enter path a FULL puzzle reset, not
just a gate reset.

**Why it mattered.** The NPC-blocked branch waited 30 frames and re-planned, forever (until the
round/frame bounds). That is correct for a WANDERING NPC, which steps aside on its own — but a
DEFEATED TRAINER never moves; its sprite stays parked wherever the approach left it. Live drive
had already proved that case hangs a climb. Waiting was therefore futile in exactly the case
that occurs most.

**Fix.** Bound the waiting (`_FORTREE_MAX_NPC_WAITS = 4`), then fall through to the
exit-and-re-enter reset, which now clears the blocking NPC as well as the gates.

**‼ And a bug in my own first cut of that fix, caught before commit:** `npc_wait_rounds` was
initialised once and never reset, making it a LIFETIME tally rather than a CONSECUTIVE-stall
counter. A 97-move climb past several trainers can legitimately wait on wandering NPCs more than
4 times in total, so those unrelated waits would have accumulated and triggered a pointless
room reset deep into a healthy climb. Now reset on every successful move. **This is the third
instance today of the same shape** (branch-local counter in `ensure_facing_direction`,
per-invocation counter in the move-learn valve, lifetime counter here) — see 08-MISTAKES.

**Verified:** solver acceptance unchanged — 4/4 live push agreement, exact 83/97 route lengths.

**Prevention rule (reinforced):** every counter that triggers an escalation must have a stated
reset condition, written down at the same time as the increment. "What resets this, and can it
fire on a healthy run?" is the question — asking it caught this one before it shipped.

## 2026-07-24 — move-learn escape: B alone was not enough (#24)

**Two of three fresh runs died on this.** Signature: `ml=Unknown`,
`instr=BattleScript_AskToLearnMove`, `bt='<MON> is trying to learn <MOVE>.'`, `wfi=True`
(the game IS waiting for input), `tasks=[]`. The HM veto did NOT fire, so this is a DISTINCT
failure from the HM case — the reader reports `Unknown` and the text-driven branches never
resolve the prompt.

**Fix.** The 6000-frame valve's escape pressed only **B** for 600 frames, which did not durably
close the offer, so the caller re-invoked and the run eventually died. Now: mostly B (declines a
YES/NO and advances text without confirming anything) with a periodic **A** every 4th frame —
because a "Stop learning <MOVE>?" confirmation only accepts A and B can never dismiss it —
widened to 1800 frames since a real multi-part message chain can outlast 600.

**Evidence base (not a guess):** the match-call A/B/C/D experiment earlier the same day showed a
stuck input-waiting prompt clears on A, on B, or on alternating, but never on zero input; and the
HM decline path resolves in ~430 frames once it is actually answered.

**Verified no regression:** both `repro_hm_move_replace_loop.py` arms unchanged — healthy path
learns Take Down over Bide in 1 invocation; forced-HM arm re-picks and also learns Take Down in
1 invocation.

**STILL OPEN (`#24-movelearn-recovery`):** when the escape ultimately fails, the `BotModeError`
is raised from inside the battle handler, which sits OUTSIDE StoryMode's derail-recovery
try/except — so the run dies instead of losing one battle. That gap cost two runs today and is
the top remaining robustness item.

**ALSO OPEN (`#24-harness-savepath`):** the harness's no-progress auto-save writes to a SINGLE
shared path (`tools/story-dev/saves/midstuck.ss1`) that every concurrent run overwrites, and
fires only once per run. With three runs in parallel the artifact is untrustworthy — which is
exactly why this bug still has no clean repro. Per-run save paths first, then repro this.

## 2026-07-25 — KI-18: double-battle after-faint swap loop + the equal-HP tie-break (#24)

**User report:** a double battle in Mauville Gym reordered the party for ~23,000 frames and never
brought in a healthy **Beautifly L23 (67/67)** while the lead sat fainted. Two DISTINCT defects,
both proven by fault injection against unmodified production code
(`tools/story-dev/repro_double_battle_swap_loop.py`):

**Defect 1 — the driver could not escape the partner's slot** (`modules/battle_handler.py`).
The after-faint party-menu sweep computed `alive_slots` from raw `current_hp > 0` ONLY. In a
DOUBLE battle the partner is alive AND on the field, so it passed the filter — and the party menu
REFUSES an already-active mon. With the cursor on that slot the sweep pressed A on it forever:
**1500 A-presses to the 6000-frame cap, zero escape.** Single battles cannot reach it (no
`right_battler` slot exists). `choose_new_lead_after_faint` already performed this exclusion; the
driver never mirrored it. Fixed by excluding on-field party indices.
A/B: fault arm **hang (1500 presses, cap hit) → resolves in 16 frames with 0 presses on the
refused slot** (steps Down off it, then selects a real bench mon). Controls unchanged: correct
cursor 8 frames, single battle 8 frames.

**Defect 2 — the equal-HP tie-break ignored level** (`modules/battle_strategies/level_up.py`).
The score was raw `current_hp` compared with a strict `>`, so on an exact tie the EARLIER party
index always won. Beautifly L23 (67/67, idx 3) could therefore never beat Mightyena L21 (67/67,
idx 2) — the user's exact observation, and a standing bug independent of the loop. Now ties break
by LEVEL, keeping `current_hp` primary (proven behaviour for every mode inheriting this strategy).
A/B: **picks idx 2 (Mightyena L21) → picks idx 3 (Beautifly L23)**; a position-swap control proves
the mechanism was slot order, not anything Beautifly-specific.

**‼ A bug in my OWN fix, caught by the repro's control arm.** The first cut used a function-local
`from modules.battle_state import get_battle_state`, which makes the name local for the WHOLE
function — so the EARLIER call at the top of `handle_fainted_pokemon` hit `UnboundLocalError`. The
control arm failed immediately and named it. Fixed by calling the existing module-level import.
Without that control this would have shipped as a crash on every faint.

**Two repro assertions were FLIPPED, and this is disclosed deliberately:** both originally asserted
the BUGGY values (`picked == 2`, and `outcome == HANG`) because they were written to CHARACTERISE
the defect. Flipping such an assertion is only legitimate when the old value documented a bug
rather than protecting correct behaviour — both now assert the fixed behaviour and carry a comment
saying what they used to assert and why it changed.

**STILL UNPROVEN (KI-18 stays open, downgraded):** no live `.ss1` of the Mauville stall exists, so
defect 1 proves the driver CANNOT ESCAPE that slot if landed there — it does not prove the live
cursor actually lands there. A stale `battle_state` snapshot feeding
`map_battle_party_index()` after a second same-turn faint is a plausible alternative route in and
is unverified. Next step: capture a live double-battle after-faint stall.

**Prevention rule:** a function-local `from X import Y` shadows a module-level `Y` for the entire
function, including code ABOVE the import. Never add one for a name the module already imports.

## 2026-07-25 — harness stall snapshots are per-run and per-stall (#24-harness-savepath)

**Two defects in one line.** The no-progress auto-save wrote a single shared
`saves/midstuck.ss1` and fired only ONCE per run:
* **Shared path** — three concurrent runs each overwrote it, so the file could not be trusted to
  belong to any particular failure. This is precisely why the move-learn stall that killed 2 of 3
  cold-start runs STILL has no clean repro, and why one earlier investigation burned effort on a
  `midstuck.ss1` that turned out to be a whiteout state from a different map.
* **Once per run** — a run usually stalls several times, and the first stall is typically a
  recoverable hiccup, not the fatal wedge. The interesting capture was the one never taken.

**Fix.** Each stall writes `saves/stalls/<profile>-f<frame>.ss1`, capped at `_STALL_SAVE_CAP = 6`
per run so a pathological run cannot fill the disk. The profile name in the filename makes
concurrent runs unambiguous. Verified live: a real run produced `b3-badge6-f945.ss1`.
`saves/stalls/` is gitignored (run artefacts, not source).

**Also removed a stale live-looking line:** the old `globals()["_stuck_saved"] = False` re-arm
reset a flag nothing reads any more. Left a comment in its place explaining why there is nothing
to re-arm — and specifically why the per-run cap must NOT be reset there, or a repeatedly-stalling
run would write unboundedly many snapshots.

**Prevention rule:** a diagnostic artefact written to a FIXED path is worthless the moment two
runs exist. Name captures after the run that produced them, and cap the count rather than the
occurrence.

## 2026-07-25 — ENDLESS RESET dropped to 1× speed after the first run (#24-endlessruns-gui)

**User report:** "on its second run it was at normal speed, it should have been set to unlimited".

**Root cause.** A derail calls `context.set_manual_mode()`, whose `enable_video_and_slow_down`
default sets **`emulation_speed = 1` AND `video = True`** (`modules/context.py:128-139`). That is
right for a human taking over, but it silently throttles the remainder of an unattended batch. My
loop restored `bot_mode` after each run and **not** the speed — so run 1 went unthrottled and
every run after it crawled at 1×, roughly a 10× slowdown on an overnight batch.

Note `emulator.reset()` was innocent — it only calls `_core.reset()` and never touches the
throttle. The slowdown came from the derail path, not the reset.

**Fix, in two halves:**
* `StoryEndlessResetMode` now captures `emulation_speed`/`video` when the batch starts and
  re-applies them after **every** run — restoring what the batch began with rather than forcing a
  value the user did not choose.
* The GUI launcher sets **unthrottled + video off** at the moment the batch is requested, because
  that is the documented intent ("start a fresh session at unthrottled speed") and the mode itself
  only preserves. Video off is the single biggest speed win and nobody watches an overnight batch
  frame by frame. The confirmation dialog now says all of this.

**Prevention rule:** when a loop restores state after an iteration, enumerate EVERYTHING the
failure path can change — not just the obvious field. `set_manual_mode` alters mode, speed, video
AND held buttons; restoring one of four looked like it worked because run 1 was always correct.

## 2026-07-25 — `compare_runs.py`: cluster run failures by signature across many logs

**Why.** The most productive debugging move in this project has been putting two run logs side by
side and noticing they died the same way — Route 111 (18,99) killed four runs across two machines
and was only identifiable that way. By eye that works for two logs; it does not work for seven,
and it silently misses "same tile, different function" (or the reverse), which is the exact
distinction that showed the (18,99) wedge was a stale reader rather than a navigation bug.

`tools/story-dev/compare_runs.py` extracts a normalised signature per log — frames, milestone
depth, failure kind, dying generator frame, location, active field scripts, whiteout/derail counts
— then GROUPS BY IT on four axes (failure kind, dying function, location, failure+location) and
marks any cluster that **spans labels**, i.e. spans machines or batches. Reads BOTH formats (the
harness's `gen ->`/`NO-PROGRESS` and the in-game debug logger's `DUMP` blocks) and states which
fields each log actually carried rather than pretending they match.

```
py -3.12 tools/story-dev/compare_runs.py --label mine tools/story-dev/night5/*.log \
                                         --label user <their-debug-log>.log
```

**Two defects found and fixed while testing it on real logs — both were the tool lying, not the
runs:**
* A fixed 400-line tail window reported `where=?` for every move-learn stall, because that failure
  drops to Manual and then emits hundreds of heartbeats, pushing the real generator stack out of
  the window. Three runs that died identically therefore looked unrelated on the "dying function"
  axis — the exact clustering the tool exists to do. Window now widens until it finds a stack.
* Position extraction reported `LITTLEROOT TOWN (-7,-7)` for late-game runs. Negative locals are
  the signature of an uninitialised/stale map read, not a place the player was — and unguarded it
  produced a 3-run "cluster" on a meaningless location. Now skips negative reads and says
  `unreliable(stale/negative read)` rather than inventing a tidy answer. Real locations
  (Route 113 / Petalburg / Route 114) appear once fixed.

**Prevention rule:** an analysis tool that cannot find a field must SAY SO, never emit a
placeholder that groups cleanly. A tidy wrong answer is worse than a visible gap, because
clustering makes coincidences look like evidence.

## 2026-07-25 — a SUCCESSFUL run no longer reports as a hang (#24-harness-finish)

**Seen on the first cold-start Badge 6 run.** The bot reached the end of built content at
f2,483,319, printed "end of built content — handing to manual", and then legitimately stopped
doing anything — so the harness's frame-based detector fired 20,000 frames later and the log ended
`HANG CONFIRMED`. A complete success, filed as a failure.

That false signal is expensive twice over: it wastes an investigation, and `compare_runs.py`
inherited it — the tool classified the successful run as `no-path`, because a **transient,
recovered** "Could not find a path" appeared earlier in the log and the tool scanned the whole file
for failure markers. So the one run that worked looked like the worst kind of failure.

**Fixes:**
* `story_harness.py` — when the no-progress detector trips, check whether the bot's message says
  "end of built content" and log `RUN COMPLETE — the bot is idle by design, not hung` instead.
* `compare_runs.py` — **success outranks everything** (reaching content-end or the Feather Badge
  ⇒ `SUCCESS`), and failure markers are judged from the TAIL, falling back to a whole-log scan only
  with an explicit `?earlier` tag so a recovered hiccup can never masquerade as the cause of death.

Verified: run1 now reads `content-end / SUCCESS`; the genuinely-failed runs still report their real
terminal causes (`whiteout-cap` in `_ride_out_all_scenes`, `hang` in
`handle_move_replacement_dialogue`).

**Prevention rule:** a detector that only knows "nothing is happening" cannot tell FINISHED from
WEDGED — it must ask why nothing is happening. And any tool that ranks failure markers must
distinguish *survived* from *terminal*, or every long run looks fatal.

## 2026-07-25 — boss non-convergence detection + Winona wired into prep (#24-counters, KI-23)

**The bug (from the user's overnight logs, cross-referenced with 5 of mine).** 198 Winona attempts,
41 losses, 41 whiteouts, never won — the last 567,000 frames spent looping challenge → lose →
whiteout → re-enter, with a party FAR ABOVE her levels (Sceptile L42 vs her L29-33). It lost
because it had no super-effective answer to Flying. The existing guard only bails when two
consecutive attempts score ZERO KOs, and a L42 Sceptile scores 1-2 every time — so it could never
fire.

**Built:** `StoryMode.PLATEAU_LOSS_THRESHOLD = 6` and
`_boss_plan_is_hopeless(cfg) -> (hopeless, needed_type_names)`. Requires ≥6 losses, then asks two
questions from data we ALREADY record: is the best KO count improving (best of the last 3 lost
attempts vs the 3 before, out of `_loss_ko_history`, which already reads `gBattleResults`), and
does any party mon have a damaging move reaching ≥2.0 against the boss's `ace_types`? Flat AND no
answer ⇒ raise `BotModeError` naming the boss, the losses, and the types that WOULD work —
computed from the real type chart, not hardcoded, so it generalises to Tate & Liza and the E4.
Fails safe: any read error returns "not hopeless", because a reader hiccup must never abort a
winnable fight.

**‼ AND THE PART THAT MADE IT ACTUALLY APPLY.** The implementer flagged that Winona **never went
through `_prepare_for_fight` at all** — she jumped straight to `do_fortree_gym()` with only a
lead-swap and a heal, so the new guard could not fire on the one boss that proved it was needed.
A correct fix that cannot reach the reported bug is not a fix. She now has a `winona_fight` cfg
(ace `Altaria L33`, Dragon/Flying, **4× weak to Ice**) and goes through prep like every other gym.

**PROVEN** (`tools/story-dev/repro_boss_plateau.py`, driving the real method):
- Winona-shaped party (Grass/Normal/Dark/Bug-Flying), flat KO history, 6 losses ⇒
  **hopeless, needed = Rock / Electric / Ice**;
- same party, RISING KO history ⇒ not hopeless (it is genuinely improving);
- same flat history but party holds an Electric answer ⇒ not hopeless;
- below the loss threshold ⇒ not hopeless.
- **Regression:** `repro_fodder_grass.py` unchanged — Norman skips the grind, Wattson and Roxanne
  still train locally. That is the path my cold-start Badge 6 run won through.

**NOT built yet:** auto-catching the counter (`#24-counters` phase 2). This converts an unbounded
loop into a bounded stop that NAMES the fix; acting on it automatically is the next step.

**Prevention rule:** when a guard is added for a specific observed failure, verify the failing
case actually REACHES the guard. Winona's prep was never wired up, so every test passed while the
real bug stayed live.

## 2026-07-25 — the COUNTER CHAIN is connected end to end (#24-counters, KI-23/24)

**The user's bug:** 198 Winona attempts, 41 losses, 41 whiteouts, never won — with a party FAR
ABOVE her levels. It lost on TYPES, not levels.

**The chain, now connected:** `_boss_plan_is_hopeless` (6 losses + flat KOs + nothing hitting the
boss's `ace_types` for ≥2.0) → `counter_plan.find_counter_candidates` (ranked catch targets over
the whole-game encounter index) → `region_reach.is_map_reachable(max_hops=4)` (region-scale
reachability from the ROM's own connections + warps).

**‼ THE RESULT THAT MATTERS.** From the verified Winona-era save (ROUTE120, Badge 5, Surf in
party), the bot now reports **Electrike on ROUTE118, tile (29,15), L24-26, 30% — REACHABLE**, and
5 of 10 candidates reachable. The OLD `_training_area_allowed` predicate returned **zero** from
that exact save. The bot goes from "I lost 41 times" to "I need Rock/Electric/Ice, and the nearest
one is an Electrike on Route 118".

**Why a NEW predicate rather than the existing one:** `_training_area_allowed` uses tile-level
`calculate_path`, which reads the Route 118/119/120 dual-elevation bridges as WALLS (KI-24) — the
same limitation that forced `_hold_walk_route()` into existence. `_counter_area_allowed` uses
`region_reach` instead. `max_hops=4` is a documented sanity FILTER, never a rank: measured hops
from ROUTE120 are Fortree 1, Route119 2, **Lilycove 2**, Route118 3, Mossdeep 4, Pacifidlog 10, so
hop count cannot separate the answer from the noise (KI-24b) — `counter_plan`'s own criteria rank.

**Fail-safe, proven in all three planner outcomes** (`tools/story-dev/repro_counter_wiring.py`):
candidates ⇒ the message names species + map; empty list ⇒ degrades to the type-only diagnosis;
**planner RAISES ⇒ the exception never escapes** and the type-only diagnosis still comes through.
That last arm matters most — a crash here would turn a diagnosed stop into an undiagnosed one,
strictly worse than the original bug.

**Regressions all green:** `repro_fodder_grass`, `repro_boss_plateau`, `repro_counter_plan`,
`repro_region_reach`.

**Promoted to `custom-pokebot/`** and verified there (modes register, both new modules import,
both new functions present).

**NOT built: execution.** The bot now NAMES the target; travelling, catching and training it is
the next task and needs a live run to validate, not a repro.

## 2026-07-25 — KI-24's scope corrected in the docs; the training-gate switch is BLOCKED (#24-regionreach)

**Doc audit finding C1 — the docs overstated the fix.** `05-KNOWN-ISSUES.md` KI-24b said flatly
"KI-24 is fixed", and `04-HANDOFF.md` told the next agent to "use `region_reach`" as if the whole
codebase already did. It does not. `region_reach` is wired into exactly ONE caller,
`_counter_area_allowed`. The training gate `_training_area_allowed` (`story_mode.py:467`, passed
as `allow=` to `best_training_area` at `:1235`) still uses tile-level `calculate_path` and still
carries every KI-24 false negative. Both files now state the scope explicitly.

**The user asked for the training gate to be switched too. It was implemented, tested, and
REVERTED — because the acceptance test says no and the test must not be silently adjusted.**
With the region test replaced by `region_reach.is_map_reachable(map_enum, max_hops=4)`,
`tools/story-dev/repro_fodder_grass.py` fails its 5th decision-table case:

```
  L31 team in Fallarbor    -> RELOCATE to ROUTE111 L19-22
  AssertionError: L31 team in Fallarbor: expected 'SKIP GRIND', got 'RELOCATE to ROUTE111 L19-22'
```

**‼ The new answer is the CORRECT one; the old expectation is a mock leak.** Measured on
`norman_done.ss1`:

* `repro_fodder_grass._stand_at()` patches only `modules.map.get_map_data_for_current_position`.
  It does **not** patch `modules.player.get_player_location` — which is exactly what the old
  `calculate_path` branch reads.
* So case 5 never evaluated "standing in Fallarbor". It evaluated the save's REAL position,
  `(PETALBURG_CITY, (7,6))`, and `calculate_path((PETALBURG_CITY,(7,6)) → ROUTE111(25,55))` raises
  `PathFindingError`. That is where `SKIP GRIND` came from — not from any judgement about Fallarbor.
* Asked honestly, BOTH oracles agree Route 111 is reachable from Fallarbor:
  `calculate_path(FALLARBOR_TOWN(14,8) → ROUTE111(25,55))` succeeds, and `region_reach` measures it
  at 2 hops. `training_areas.py`'s own comment on that entry already says "reachable from Fallarbor".

**Left for the user to rule on** (KI-24b carries the detail): fix `_stand_at()` to patch
`get_player_location` too — the honest repair, since case 5's stated intent is "what would we
decide while standing in Fallarbor" — or re-baseline case 5's expectation. Until one is chosen and
proved green, the training gate stays on `calculate_path` and KI-24 stays open for it.

**Nothing shipped in code.** `sandbox-pokebot/plugins/custom_modes/story_mode.py` and its
`custom-pokebot/` twin are byte-identical to their previous state; the acceptance test is green as
it was (baseline re-run before and after: all 5 cases pass on the unmodified tree).

## 2026-07-25 — Story Mode's user-facing doc rewritten to match reality (doc audit S11)

`custom-pokebot/DOCUMENTATION/01-custom-automations.md` was the most wrong user-facing document
in the repo: it said Story Mode "stops with the player controllable inside the moving truck" and
that "Chapters 1–24 … are still being built". That has been false for many chapters. A cold start
now reaches **Badge 6 (Winona) = end of built content — 38 maps, ~2.48M frames, 0 derails**.

Section rewritten with: the real coverage (chapter-by-chapter, through Gym 6), the real next
unbuilt content (Mt. Pyre, then the Magma hideout), how to actually run it (ROM → `story.yml` →
pick `Story`; from the overworld it resumes flag-gated rather than replaying), and a table of the
three sibling modes — `Story (DEBUG)`, `Story (DEBUG - RESET)` and **`Story (ENDLESS RESET)`**,
the in-process overnight batch runner (10 runs by default, set from the GUI's "Endless
Debug-Reset Runs…" item, 0 = forever) with its unattended-safety behaviour spelled out.

## 2026-07-25 — `04-HANDOFF.md` de-misleading pass (doc audit S4/S6/S7/S8/C3/C4)

Six places where the handoff actively pointed a fresh agent the wrong way:

* **S4** — "Current state (what's WHERE)" was 2026-07-21 text under a present-tense heading,
  ending "Frontier: PokéNav + tutorial done" (~8 chapters stale). Retitled
  "HISTORICAL — what was WHERE as of 2026-07-21 (‼ NOT current state)" with a pointer to the
  "YOU ARE HERE" section; kept for its promotion history and Rustboro-era atlas notes.
* **S7** — "Known issues: KI-1 … KI-6 fixed / Mistakes: ML-1..ML-7" understated the record by an
  order of magnitude. There are **24 KI entries and ~70 mistakes**. Now names the LIVE ones:
  **KI-17** (after-faint party-menu freeze), **KI-18** (double-battle swap loop), **KI-23**
  (Winona needs a type answer), **KI-24/24b** (partially fixed — counter selection only).
* **S6** — "Next steps (in order)" led with the daily upstream check then dex tabs and `#41`, and
  put `#24` LAST. `#24` is the only active work. Reordered around it —
  `#24-movelearn-recovery` first (killed 2 of 5 cold-start runs) — with everything else moved
  under an explicit "Parked (not active)".
* **S8** — "How to run / test" listed only `pokebot.py`/`install.py`. Added the story-bot harness
  with real commands: `story_harness.py` (drivers, `--video`, `fresh`), `endless_runs.py` (batch
  runner + failsafes), `compare_runs.py` (cross-run failure clustering), and the five `repro_*`
  regressions — plus the `py -3.12` / `PYTHONUTF8=1` prerequisites.
* **C3** — the handoff said both "five" and "two" `CLAUDE-VALIDATED-*` files. **Five** is correct
  (verified on disk: items-round1, concepts-round1/2/3, story-round1).
* **C4** — the `gh api repos/pret/pokeemerald/contents/<path>` grounding line is marked
  SUPERSEDED by the local sparse clone, with the reason (absence claims are only checkable
  against a whole tree).

## 2026-07-25 — `03-PUNCH-LIST.md` drift repaired (doc audit, item 4)

The punch list had drifted far enough that it could not be used as the work queue it claims
to be:

* **11 IDs were referenced across the changelog/handoff/known-issues but had NO entry.** Added,
  each grounded in what the record actually says: `#24-movelearn-recovery` (**open, #1 — killed
  2 of 5 cold-start runs**), `#24-whiteout` (**open, highest-cost** — the run that SUCCEEDED
  still took 80 whiteouts), `#24-npcheal` (open — blocked on a heal-at-NPC helper),
  `#24-counters` (**phase 1 DONE, phase 2 not started**), `#24-regionreach` (built + proven; gate
  table and the second caller still open), `#24-edgecost` (deferred, with the measurement that
  makes it deferrable), `#24-fortreelive` (open residual verification debt),
  `#24-harness-savepath` (DONE), `#24-harness-finish` (DONE), `#24-fortreebadge` (**SATISFIED** —
  Badge 6 won from a cold start), `#24-fortreegates` (DONE, 4/4 vs the emulator).
* **`#24-endlessruns-gui` said "STILL TO DO".** It shipped — and as something better than the
  filed plan. The planned menu-item-shells-out-to-CLI version was built first and FAILED in the
  user's hands; it shipped instead as a real in-process bot mode, `Story (ENDLESS RESET)`. Entry
  rewritten with the in-process failsafes and a note that the CLI form is NOT superseded.
* **`#24-trainmap` said the routing was all TODO.** The routing half is done —
  `best_training_area` + `AREA_PREREQ` + `estimate_frames_to_level`, called by
  `_prepare_for_fight`, relocating via `_goto_training_area`. Only the `PENDING_GRASS` spin
  tiles remain. Marked `[~]` with the remaining work named.
* **22 open `- [ ]` items were filed under `## Done`.** Moved verbatim into a new
  `## Story bot (#24) — open backlog` section (nothing reworded).
* **`## Now (active focus)` did not mention `#24`.** It now leads with it, states the current
  reach (Badge 6 = end of built content) and the four-item priority order, and marks the old
  `#V` verification sweep as parked behind it.

## 2026-07-25 — Records that were never written (doc audit M1/M2)

**M1 — five 2026-07-25 decisions appended to `06-DECISIONS-LOG.md`.** Each was recoverable from
the changelog but had no decision entry, so the reasoning (and the rejected alternatives) would
have been lost to the next agent:
1. **Local sparse decomp clone as the default grounding method** (not per-file `gh api`) — the
   reason is that ABSENCE claims are only checkable against a whole tree.
2. **`region_reach` as a NEW predicate rather than repairing `calculate_path`** — rejected fixing
   the shipped navigator (high blast radius for a caller asking the wrong question) and rejected
   heuristic tolerance widening (papers over a wrong oracle, and the failure is invisible).
3. **Hop count as a FILTER, not a rank, with `max_hops=4`** — with the measurement that forced it
   (Lilycove reads CLOSER than Route 118 from ROUTE120).
4. **Gemini Pro 3.1+ enforced in CODE rather than by doc rule** — because the doc rule is exactly
   what failed: the default was already 3.1-pro and an agent still overrode it on ~35 calls by
   copying a stale docstring example.
5. **Endless-reset as an in-process bot mode rather than a subprocess launcher** — this one
   REVERSED a shipped implementation, which makes it the most important of the five to record.

**M2 — `custom-pokebot/DIVERGENCE-LOG.md` was missing two whole modules.**
`modules/story/counter_plan.py` (185 lines) and `modules/story/region_reach.py` (496 lines) were
copied into `custom-pokebot/` by commit `72b49fd6` and never logged — a real hole in the merge map
the log exists to be. Added as BATCH-3c, with the KI-23/KI-24 motivation, the explicit note that
`calculate_path` was deliberately NOT modified, and the upstream-collision assessment.
Also added BATCH-3d, which records that `Story (ENDLESS RESET)` REVERSES BATCH-3b's launcher menu
item (3b stands as written — the file is append-only).

## 2026-07-25 — Four prevention rules retired as structurally impossible (doc audit R1-R4)

Per `CLAUDE.md`'s `/reconcile` guidance — a stale "don't do X" keeps that idea alive in every
future agent's context and costs tokens for no protection. Recorded as an append-only RETIREMENT
NOTICE at the end of `08-MISTAKES.md`; **nothing was deleted or edited**, and each retirement names
the guard that makes it safe (if that guard is ever removed, the rule becomes live again).

* **R1 RETIRED** — ML-5's badge-anchoring rule. The entry carried its own retirement condition and
  it is met: `tests/test_story_progress.py` (both builds) asserts
  `test_current_chapter_never_leaves_its_badge_bracket` over every badge level 0-8 and
  `test_hacked_save_stone_plus_stray_magma_emblem`.
* **R2 PARTIALLY RETIRED** — the phantom-flag rule. Sub-rule (a) is retired: `_done()` now raises
  on any name absent from `modules.memory._event_flags`, so a typo is a loud build error rather
  than a silent False. **Sub-rules (b) and (c) KEPT** — the guard protects `_done()`, not an agent
  reading a one-off probe (b), and nothing structurally forces a segment predicate and its guard to
  be the same function (c).
* **R3 RETIRED** — ML-4's nested-`.git` rule. `pokebot.py` now checks EVERY ancestor for a `.git`
  before considering the stock updater, in both builds; the guard is layout-agnostic rather than
  patched for our depth.
* **R4 PARTIALLY RETIRED** — the Gemini docstring-example rule. Rule 1 is retired for this tool:
  `gemini_relay.py` refuses sub-Pro-3.1 models in code. **Rule 2 KEPT** ("check YOUR invocation
  before concluding the tool is bad") — it is the rule that actually cost the day, it generalises
  to every tool here, and it has no structural guard.

## 2026-07-25 — KI-24 CLOSED on the training gate too; the test that was guarding it was broken (#24-regionreach)

**Landed:** `_training_area_allowed` now answers the region question with
`region_reach.is_map_reachable(map_enum, max_hops=_MAX_TRAINING_TRAVEL_LEGS)` instead of tile-level
`calculate_path`. Both builds, byte-identical. `calculate_path` no longer answers any region-scale
question in the story bot. Rationale (asymmetric failure modes) and the residual `KNOWN_GATES` risk
are written into the function's docstring, where the next reader will actually hit them.

**Measured effect** (`repro_counter_plan.py`, same live Winona-era position, same candidate list,
ONLY the predicate swapped):

| `_training_area_allowed` | reachable flags over the 10 Winona candidates |
|---|---|
| before (`calculate_path`) | `[False × 10]` — every candidate rejected; KI-24 in the raw |
| after (`region_reach`) | `[True × 5, False × 5]`, incl. **Route 118 Electrike: reachable** |

**‼ The bigger find: `repro_fodder_grass.py` — the regression guard for ALL training logic — had
been testing the wrong world state.** The first attempt at this switch failed its case 5 and was
REVERTED rather than forced. Investigating the disagreement instead of adjusting the expectation
showed the TEST was wrong:

* `_stand_at()` patched only `modules.map.get_map_data_for_current_position`. The predicate under
  test takes a SECOND position reading from `modules.player.get_player_location()` before calling
  `calculate_path`, and that one stayed LIVE.
* So case 5 never simulated Fallarbor. It asked about the save's real position,
  `(PETALBURG_CITY, (7,6))`, got a `PathFindingError`, and recorded it as a Fallarbor verdict.
* This file had gated the frames-based budget work and the fodder-skip itself over the preceding
  two days, printing "proven-good prep unchanged" while one of its five cases proved nothing.

**Fixed the test first, and proved the fix ALONE was green** (`560b75f6`): `_stand_at()` derives
both mocks from one source (the town's Poké Center door tile), patches both readers, and asserts
they describe the same map; `_stand_down()` restores both. **With the test fixed and
`story_mode.py` untouched, the ORIGINAL `calculate_path` code also answers `RELOCATE to ROUTE111`,
and cases 1-4 are unchanged** — so the re-baseline is provably a test fix, not a behaviour change.
Three independent sources agree Route 111 is reachable from Fallarbor: `calculate_path` succeeds
from `(14,7)`, `region_reach` measures 2 hops, and `training_areas.py`'s own comment says so.

**Verification.** `repro_fodder_grass` 5/5 green (case 5 now genuinely exercising a Fallarbor
stand); `repro_region_reach`, `repro_counter_wiring`, `repro_boss_plateau` green.

**⚠ `repro_counter_plan.py:200` is RED and deliberately NOT adjusted.** Its primary assertions pass.
What fails is a self-described non-vacuity scaffold: it runs a deliberately WIDE type set through
`_training_area_allowed` and requires at least one `False` "so both True and False genuinely occur
(not vacuous)". The fixed predicate returns `[True × 25]`, so no `False` exists — **the scaffold was
relying on the bug it was written alongside.** It is also obsolete: it existed because the Winona
set was all-`False` (vacuous) under the old predicate, and that set is now a genuine
`[True × 5, False × 5]` mix that carries the sort proof by itself. Suggested fix in KI-24b; not
applied unilaterally, because silently adjusting a test is exactly how the case-5 artefact survived
two days of green runs.

## 2026-07-25 — Non-vacuity moved to where non-vacuity lives; suite back to 5/5 (#24-regionreach)

**The red test from the KI-24 training-gate fix is resolved** (user ruling). `repro_counter_plan.py`
asserted `False in [c["reachable"] for c in wide_cands]` — "at least one candidate must be
UNREACHABLE" — as a non-vacuity guard for the reachable-first sort proof. Fixing the predicate made
the wide set all-`True`, so the required failure had nothing to find. **The guard was relying on
the bug.**

**Why it existed, and why it is now redundant:** it was a workaround for the Winona set being
VACUOUSLY all-`False` under the pre-KI-24 predicate. That set now returns
`[True × 5, False × 5]`, so it carries the sort proof by itself.

**Fix:** dropped the wide-set non-vacuity pair; the check now asserts that the **Winona set** spans
BOTH branches — the property the ordering claim actually needs, on the list this planner exists to
produce. The wide set is still sorted, as a larger-sample check. Commented in place with what it
replaced and why, so the next reader can tell a repaired test from a weakened one.

**Suite: 5/5 GREEN** — `repro_fodder_grass`, `repro_counter_plan`, `repro_counter_wiring`,
`repro_region_reach`, `repro_boss_plateau`.

**‼ Recorded as a PATTERN, not an incident (08-MISTAKES).** This was the SECOND test in one day
found to be asserting something that depended on a defect — case 5's `SKIP GRIND` needed the mock
leak; this pair needed `calculate_path`'s false negatives. Shared root cause: much of this suite
was written to CHARACTERISE defects, which produces assertions phrased as "a failure occurs here"
rather than "this property holds". Those are indistinguishable while the bug is live and diverge
the instant it is fixed. **Both were found only because a change forced them to fail — neither
would ever have been noticed while green**, so the number of remaining assertions of this shape is
unknown. Prevention rule: assert the PROPERTY you need, not a symptom of the current bug, or the
suite punishes progress. Also added as trap #4 in the handoff.

## 2026-07-25 — The move-learn run-killer: root-caused, fixed, and moved inside recovery (#24-movelearn-recovery)

**The #1 open item is closed.** It killed 2 of the 5 night5 cold-start runs outright, at f1,543,953
and f1,557,569 — roughly 1.5 million frames of progress each, thrown away over what should have
cost one skipped level-up.

**‼ The filed diagnosis was only the last link.** The punch list said "the recovery scope is the
bug, not the move-learn logic". The recovery scope *was* broken — but fixing only it would have
turned a dead run into a dead run that logged better. Reading the actual frame logs found a chain
of four defects, and the real hang was none of the suspected ones.

**Evidence.** Both deaths are the same mon in the same shape, and both wedge states were lifted
out of the run profiles before the next batch could overwrite them:
`saves/movelearn_hmwedge_quickattack.ss1` (n5-5: Combusken L32 `Scratch, Rock Smash[HM06],
Double Kick, Ember`, offered QUICK ATTACK) and `saves/movelearn_hmwedge_slash.ss1` (n5-2:
Combusken L39 `Scratch, Peck, Double Kick, Rock Smash[HM06]`, offered SLASH). Combusken is the
story bot's Rock Smash mule, and Rock Smash is both an HM and the weakest move it owns.

**The chain, in the order it fires:**
1. Config is `new_move: cancel`, so the strategy returns 4 = DECLINE. But branch (5) presses A on
   any unrecognised move-learn text, and the state genuinely reads `Unknown` during "<MON> is
   trying to learn <MOVE>." (38 frames of it in the run log). Those stray A's answer **YES** to
   the prompt the bot had decided to decline, opening the move-select screen.
2. Branch (1) then pressed A on a cursor read from `sMonSummaryScreen`, which is still being
   initialised while the screen animates in — a stale 4 while the real cursor sat on slot 1 is how
   an HM got confirmed despite the decision being DECLINE.
3. The game answers with `ShowCantForgetHMsWindow` / **`Task_HandleInputCantForgetHMsMoves`**.
   **Nothing in the bot referenced that symbol.** `get_learn_move_state()` reported it as
   `AskWhetherToLearn` (the script pointer is still parked at `BattleScript_AskToLearnMove+0x11`),
   so the bot answered a Yes/No that was not on screen.
4. **The actual hang:** with that window up, the handler fell into the "summary screen is still
   opening, just wait" branch — an UNBOUNDED wait that presses nothing. Measured on the capture:
   **zero inputs for 6,000 straight frames.** Then the escape valve's blind `B,B,B,A` produced an
   8-frame ping-pong (A re-selects the HM, B dismisses the refusal) until the 3-strike valve raised
   `BotModeError` — from inside the battle listener, where StoryMode cannot catch it.

**Fixed, four changes:**
- `LearnMoveState.CantForgetHM` + `HM_REFUSAL_TASK`, checked FIRST in `get_learn_move_state()` so
  the refusal wins over every offset-based branch. R/S/FRLG have no such task, so `task_is_active`
  returns False and those ROMs are untouched.
- New branch (0) handles it: dismiss with a single A + settle, and **LEARN from the refusal** —
  the confirmed slot is struck off (`hm_blocked`) and a replacement picked by the existing
  expendability ranking. Dismissing without striking off just returns to the same doomed pick.
  The game is the authority on what is forgettable; our `tm_hm` veto is only a prediction.
- Branch (1) now refuses to act on an untrusted cursor: no A unless the move-select input task is
  actually active, and it records which slot it confirmed so branch (0) knows what to strike.
- The summary-screen wait is BOUNDED (180 frames → back out with B). A genuine open takes ~20.

**Recovery scope (the item as filed), `modules/battle_fault.py` — new.** Battle handling is a
SIBLING generator on `context.controller_stack`, not nested in the mode, so `main_loop` catches a
battle-handler `BotModeError` before StoryMode ever sees it. The valve now offers the fault to the
mode via `request_mode_recovery()` and only raises if nobody takes it. `handle_battle` stops
driving while a fault is pending, `_wait_until_battle_is_over` releases control (deliberately
WITHOUT clearing `_in_battle`, which would re-arm the listener into the same wedge), and StoryMode
claims it inside its own `try` → one derail, not a dead run. **Opt-in by attribute**
(`handles_battle_faults`): every stock mode keeps today's behaviour exactly.

**PROOFS (all A/B, from the real captures — `repro_movelearn_hm_wedge.py`,
`repro_movelearn_fault_recovery.py`):**
| arm | before | after |
|---|---|---|
| quickattack capture | WEDGED, `BotModeError` at f23,400, 3 invocations, `B:4050 A:1350`, **no Down** | RESOLVED at **f258**, 1 invocation, `A:225 Down:5`, moveset correctly unchanged |
| slash capture | (same wedge) | RESOLVED at **f224**, 1 invocation |
| fault channel, stock mode | — | PASS: `BotModeError` → Manual at f27,583, no fault recorded (legacy preserved) |
| fault channel, opted-in mode | — | PASS: same fault at f27,584 CLAIMED by the mode, never Manual |
| real StoryMode | — | PASS: `derail #1: Story: battle handler gave up — …`, still in Story 1,500 frames later |

The stock/opt-in pair is the same battle and the same fault one frame apart; the only difference is
the opt-in attribute.

**Regression: story-bot suite 5/5 GREEN** (`repro_fodder_grass`, `repro_counter_plan`,
`repro_counter_wiring`, `repro_region_reach`, `repro_boss_plateau`), plus
`repro_hm_move_replace_loop` (clean, 1 invocation) and `repro_hm_replace_valve_forced` (still
raises at f27,583, `_STALLED_EXITS = 0`). That last one first came back at `_STALLED_EXITS = 2` and
looked like a regression — it was a BUDGET artifact (bounding the wait costs more emulator frames
per iteration, pushing the third strike past its 25,000-frame budget). Default raised to 35,000
with the reason recorded in the file.

## 2026-07-25 — Whiteout census: it is not attrition, it is gyms; and the guard against it could never fire on Norman (#24-whiteout)

**Measured the whiteouts instead of theorising about them.** Every loss in the 5 night5 runs is
logged as `Story: lost a battle at map (g, n) (defeat #N here; KO'd M of theirs first)`. Census of
all five runs (~128 losses; losses and whiteouts are 1:1 — the bot has no potion/revive layer, so
losing always means whiting out):

| map | losses | |
|---|---|---|
| `PETALBURG_CITY_GYM` | 38 | Norman |
| `MAUVILLE_CITY_GYM` | 24 | Wattson |
| `FORTREE_CITY_GYM` | 20 | Winona |
| `LAVARIDGE_TOWN_GYM_1F` | 18 | Flannery |
| `ROUTE110` | 10 | rival / trainers |
| Dewford + Rustboro gyms | 6 | Brawly, Roxanne |

**~83% of all losses are gym leaders.** The item was filed as "attrition"; the data says the cost is
almost entirely the boss-as-training-vehicle strategy, not travel or wild encounters.

**What that strategy actually delivers** (night5 run3, Norman, traced attempt by attempt):
27 losing attempts across **f1,406,000 → f1,914,000 (508,000 frames, ~19k per attempt)**; party
went Marshtomp L33→L35, Mightyena L32→L36, Swellow L30→L32 — **+2 to +4 levels total**; Shroomish
sat at **L15 the entire time**, never trained and never benched; and **KOs stayed flat at 1–2 of
Norman's 4 for all 27 attempts** — attempt #27 did no better than attempt #1. It is not slow
convergence, it is a plateau.

**‼ The machinery built to stop exactly this post-dates the logs.** The night5 batch launched at
07:36 (`aadad944`); boss non-convergence detection landed 09:47 (`32c62285`), the counter planner
10:46, the end-to-end wiring 11:53, the KI-24 gate 13:27. So the 27-attempt plateau was never
something the shipped guard failed to catch — it had no guard at all. But testing it against the
real party found that it *still* would not have caught it:

**FIXED — `_boss_plan_is_hopeless` was POWER-BLIND.** Its "do we already have an answer?" veto
accepted any damaging move with `effectiveness >= 2.0`, regardless of power. Norman's team is
entirely **Normal**, the only type super-effective against Normal is **Fighting**, and the run3
party's sole Fighting move was **Rock Smash — the 20-base-power HM the bot is REQUIRED to carry to
progress at all**. 20 × 2.0 × 1.0 = 40 effective power: super-effective on paper, useless against a
L31 Slaking. The veto fired, the plan was declared viable, and the detector was structurally unable
to protect the boss most likely to plateau.

Now the answer must be CREDIBLE: `base_power × effectiveness × STAB >= CREDIBLE_ANSWER_POWER` (60).
Chosen so genuine answers survive and chip/utility moves do not — Double Kick on Combusken
(30 × 2.0 × 1.5 = 90, the move that beat Norman organically) counts; Rock Smash (40) and a L15
Shroomish's Absorb (40) do not.

**A/B on the real night5 run3 party:** `BEFORE (power-blind) -> (False, [])` /
`AFTER (power-weighted) -> (True, ['Fighting'])`.

**Also fixed: the detector's `except Exception` was silent.** It returns `(False, [])` on error —
the same value a *working* detector returns for a healthy boss — so any bug in it is
indistinguishable from "this plan is fine" and costs ~19k frames per losing attempt, forever. It
now prints a warning saying the guard is not protecting the run. This was not hypothetical: the
first run of the new test case returned `False` because the repro's stand-in `self` lacked the new
class constant, and the `except` swallowed the `AttributeError`.

**Tests:** `repro_boss_plateau.py` gains CASE 5 (the REAL run3 party and its real KO trace
`1,1,2,2,2,2` → must be HOPELESS, naming Fighting) and CASE 6 (a weak-but-real STAB answer must
still count, guarding against over-correcting the threshold). Suite 6/6 in that file, story-bot
suite 5/5 green, plus both move-learn repros from earlier today re-verified.

**#24-whiteout is NOT closed.** The diagnosis now fires; the bot still only *stops* with a named
target. Acting on it — travel, catch, train the counter — is `#24-counters` phase 2, and the two
items are now the same problem seen from two ends.

## 2026-07-25 — Live batch validates the day's three fixes; two issues found and fixed (#24-regionreach)

**Batch `20260725-194810`** — 5 fresh cold-start lanes, 3M frames, commit `26613bcb`.
Reviewed marker in the batch dir. Scorecard vs the night5 baseline:

| | batch | night5 |
|---|---|---|
| reached frontier | **1/5** (run03, Feather Badge) | 0/5 |
| move-learn deaths | **0/5** | 2/5 |
| Norman attempts before giving up | **6** | 27 (508k frames) |
| total losses | 66 | 128 |

**All three of the day's fixes confirmed in a live run:**
* **Move-learn HM wedge** — zero valve failures, and the new `CantForgetHM` branch **fired 44
  times**, so the situation kept arising and kept being handled (positive evidence, not absence
  of the trigger).
* **Boss-plateau guard** — fired on Norman at **exactly 6 losses** in 2 runs; Petalburg-gym
  losses 38 → 14 batch-wide.
* **Counter chain, first live execution ever** — named `Makuhita (Fighting) on Granite Cave (1F),
  L6-10, 50% — reachable`, with Victory Road / Jagged Pass correctly marked UNREACHABLE.
The battle-fault channel never triggered (no wedged battles occurred) — still repro-only.

**FIXED 1 — a wrong YES from the reachability oracle cost the RUN, not a walk (2/5 runs).**
Both deaths were identical: `Could not reach (25, 55) on ROUTE111 ... from (22/6 @ MAUVILLE_CITY)`.
`training_areas.py` documents that tile as FALLARBOR-SIDE ONLY (north of the Go-Goggles desert,
which splits Route 111 into two disconnected halves), but `AREA_PREREQ` gates ROUTE111 as
`"region"` and `_training_area_allowed` answers "region" with `region_reach.is_map_reachable`,
which is TRUE from Mauville — the southern half connects. Gate passes, walk dies at the desert.
‼ `_training_area_allowed`'s own docstring argued a wrong YES "costs ONE wasted walk, which
navigation then fails RECOVERABLY and loudly". **The batch disproved it.** The picker is
DETERMINISTIC: every derail re-ran `_play`, re-picked the same tile, failed identically, and the
derail budget dropped the run to Manual. Fix makes the docstring's claim true rather than
special-casing Route 111 — so it also covers every future gap in `KNOWN_GATES`, the residual risk
that docstring already names:
* new `UnreachableDestinationError(BotModeError)` in `early_game.py` — a SUBCLASS, so every
  existing `except BotModeError` (derail recovery above all) is unchanged; it exists so an
  OPTIONAL choice can tell "not reachable from here" from "training went wrong".
* `StoryMode._training_unreachable` remembers `(standing map, target map, tile)` and the picker
  skips it. **Keyed on where we stood** because reachability is directional — Route 111 really is
  reachable from Fallarbor — so a good ground is not thrown away run-wide. Instance state, so
  ENDLESS RESET's next run starts clean.
Proof (`repro_training_unreachable.py`, 5 cases): Mauville proposes Route 111 (reproduces the
bug) → the typed failure is recorded → Mauville now picks **ROUTE117 (31,16)** instead → Fallarbor
still picks Route 111 → the error is still a `BotModeError`.

**FIXED 2 — `livetest.py`'s whiteout metric always read 0.** It counted `"WHITEOUT recovery"`, a
`debug_logger.event()` payload written to the profile's debug-log FILE, never to stdout/run.log —
the only streams the summarizer reads. It reported `0 whiteouts` for all 5 runs that had really
whited out 36/5/9/6/10 times. ‼ **Every whiteout figure in an archived batch summary is
meaningless.** Now counts `recovered from the whiteout` (a `console.print`, once per whiteout),
and gained `losses` + `losses_by_map` — automating the per-map census that was hand-computed twice
today and that redirected `#24-whiteout` from "attrition" to "83% gym leaders". Verified against
the hand counts: exact match, per-map included.

**STILL OPEN (found, not fixed): training-loop attrition has no give-up guard.** run01 lost **25
times on Route 110** while swap-training a lopsided team (Marshtomp L23 carrying Beautifly L16 /
Poochyena L12 / Whismur L12), KO count flat at 1 every time — the same plateau shape as Norman,
but `_boss_plan_is_hopeless` covers configured BOSSES only. Route 110 is now the largest single
loss cluster in the batch. Filed under `#24-whiteout`.
Minor, also filed: the diagnosis prints `"this boss"` (Norman's cfg has no `name` key), every
counter candidate says `tile unmapped`, and the top counter for a L34+ party is a **L6-10
Makuhita** — level fit may need to outrank encounter rate in phase 2.

## 2026-07-26 — SURVIVAL MODE: a map that keeps wiping us stops being treated as XP (#24-whiteout)

Closes the issue the live batch left open. run01 whited out **25 times on ROUTE110** in a single
run — wipe, respawn in the Slateport Poké Center, walk back north, wipe again — and nothing ever
noticed. It was the largest single loss cluster in the batch (31 of 66 losses batch-wide).

**Root cause.** With no `train_team` session running, `on_battle_started` falls through to
`LevelUpTravelBattleStrategy`, which fights every wild to level the lead. Its own comment states
it "flees only at low HP, **which the training loop covers by healing**" — and that is the whole
bug: on a TRAVEL leg there is no training loop, so nothing heals, and HP only ever falls across
consecutive encounters until the party wipes. Verified from the log that this was travel, not
training: the entire run logged exactly ONE "prepping — training" line (for ROUTE117), and
`set_swap_train(True)` exists only inside `train_team`, so `swap_train_active()` was False
throughout those 25 losses.

**Fix — `SURVIVAL_WHITEOUT_THRESHOLD = 3`.** Once a map has beaten us 3 times this run, wild
battles there are FLED rather than fought: get through, do not level into another whiteout.
3 rather than the boss threshold of 6 because the costs are not comparable — a lost boss attempt
still banks EXP (Gen 3 keeps mid-battle EXP through a whiteout), while a travel wipe banks almost
nothing and costs the entire walk back from the respawn Poké Center.

Scope is deliberately narrow, and each limit is asserted by the repro:
* **WILD only** — a trainer battle cannot be fled, and the boss/gym re-attempt path is untouched.
* **Not during `train_team`** — there the swap strategy plus its heal loop are the right answer,
  and fleeing would starve the grind it was sent to do.
* **Per-map, not global** — a different map with no history still fights normally.

**Proof (`repro_survival_mode.py`, 7 cases)** driving the REAL `on_battle_started`: clean map →
fights; 2 defeats → still fights (no hair-trigger); 3 defeats + wild → flees; 3 defeats + trainer
→ does NOT flee; 3 defeats + active grind → swap-trains; other map → fights; **the real run01
state (25 defeats on ROUTE110) → flees**, i.e. 22 of those 25 whiteouts would not have happened.

**‼ The first version of this silently did nothing, and the codebase had already documented why
— three lines above where I wrote it.** Other branches of `on_battle_started` do
`from modules.console import console`, which makes `console` **function-local for the entire
method**, so my block's `console.print` raised `UnboundLocalError` and my own
`except Exception: pass` ate it. The repro reported survival mode "not firing" with nothing
logged. Fixed with the same local import the HM branch uses; see 08-MISTAKES.

Suite 7/7 green (the two new repros plus the five existing), move-learn repros re-verified.

## 2026-07-26 — Validation batch: both new guards work; it also found a crash I shipped and a threshold I mis-calibrated

**Batch `20260726-052205`** (5 fresh lanes, 3M frames, commit `d7c51b0e`; `REVIEWED.md` in the
batch dir). **2/5 reached the frontier** — 0/5 → 1/5 → 2/5 across three batches. ROUTE110 losses
**31 → 7**. Route 111 nav deaths **2/5 fatal → 0 fatal**.

**Confirmed live (previously repro-only):**
* `_training_unreachable` — run04 logged "ROUTE111 (25,55) is not reachable from here — dropping
  it" and the run CONTINUED. The deterministic death loop is gone.
* SURVIVAL MODE — fired at the 3-defeat threshold; ROUTE110 losses fell from 31 to 7.
* Boss-plateau guard — run04 stopped on Wattson at 6 losses, naming Ground / Sandshrew.

**‼ FIXED 1 — survival mode CRASHED run03.** `RuntimeError: Cannot rotate Pokémon #False with
itself`, immediately after "Got away safely!". Stock
`RunAwayStrategy.choose_new_lead_after_battle()` returns **False** despite being annotated
`int | None`, and `BattleListener.fight()` rotates whenever that value `is not None` — so it
rotated to party index `False`. This was invisible upstream because the framework only ever drove
that class from `run_away_from_battle()`, which does not rotate leads; returning it from
`on_battle_started` routes it through `fight()`, which does. **A latent upstream bug that only a
new caller could expose.** Fixed with `StoryFleeStrategy(RunAwayStrategy)` returning `None`,
leaving upstream behaviour untouched. Guarded by `repro_survival_mode.py` CASE 8.

**‼ FIXED 2 — `CREDIBLE_ANSWER_POWER` mis-calibrated, 60 → 75.** run05 took **21 Norman losses**
with the guard silent. Yesterday's threshold was calibrated on Rock Smash held by a NON-Fighting
mon (20 × 2.0 × 1.0 = 40) and missed the STAB case: **Combusken is Fire/FIGHTING**, so its Rock
Smash scores 20 × 2.0 × 1.5 = **exactly 60** and passed on the boundary — the same failure the
threshold exists to prevent, arriving through STAB rather than raw power. Two REAL runs now
bracket it: **60 loses 21 times, 90 (Double Kick) wins**. 75 sits between them and still keeps
every genuine answer — Surf off a Water mon (285), Thunderbolt vs Winona (270), a plain 40-power
super-effective move (80). Pinned by `repro_boss_plateau.py` CASE 7 with run05's real party.
‼ Explicitly NOT fixed by excluding HM moves categorically: Surf / Strength / Waterfall are real
attacking moves and often the bot's best answer; only Rock Smash and Cut are weak enough to be the
problem, and the power floor already handles them.

**Test-quality note.** Fixing the crash changed the flee class name, which reddened two
`repro_survival_mode` cases that asserted `type(...).__name__ == "RunAwayStrategy"` — an
implementation detail, not the property. Rewritten to assert *"does this battle get fled"* via
`isinstance(..., RunAwayStrategy)`. Same lesson as the 2026-07-25 pattern entry: assert the
property you need, not a symptom of the current implementation.

**Still open:** run05 burned its whole 3M budget without reaching the frontier (21 of 27 losses
were Norman). At threshold 75 that party is now diagnosed hopeless and stops with a named counter
— an improvement only once `#24-counters` phase 2 can act on it. Suite: 7 files green.

## 2026-07-26 — Counter candidates are ranked by what they COST, not by how easy they are to bump into (#24-counters)

**Blocker #2 of §CC2, closed by measurement.** `find_counter_candidates` scored `rate * 1_000.0 -
level_gap`, so encounter rate outweighed level fit by ~1000×. For a L31 party that ranked a
**L6-10 Makuhita (50%)** above a **L20-22 Machop (25%)**. Priced with the project's own frame model
(`estimate_frames_to_level` + the measured `FRAMES_PER_WILD_BATTLE = 1433`), on the real save:
**Machop 75,949 frames vs Makuhita 315,260** — the preferred candidate was **4.2× more expensive**.

Now: `tier` (reachable > types answered > has a verified tile) is separated from `score`, and
within a tier candidates sort by `est_frames` = frames to FIND one + frames to TRAIN it from the
top of its band to the team's level. Rate survives as the small term it should always have been.
Fail-safe preserved: an unpriceable candidate sorts LAST in its tier (unknown cost is never
treated as cheap), and with no team level the ordering degrades to the old rate-then-gap behaviour,
so existing callers are unaffected. `score` keeps its published meaning for display.
Pinned by `repro_counter_plan.py` case 5 with the real measured pair. Suite 7 files green.

**The economics also answer §CC2's open question** ("is catching a counter even right for
Norman?"). Against the measured cost of the current behaviour — run05 lost 21× ≈ 399,000 frames,
run3 lost 27× = 508,000 — a Machop is 98,877 and a Makuhita 363,982. So it is clearly worth it for
the right candidate and marginal for the wrong one. ‼ But the only Fighting counter the live
predicate accepted was **Makuhita/Granite Cave**, i.e. ~9% better than doing nothing:
**phase 2's value is gated by REACHABILITY, not by ranking.** Widen what is legitimately reachable
before building the executor.

**‼ And blocker #3 (false reachability) is now MORE dangerous.** Cost ranking makes end-game
encounters look nearly free — Hariyama on VICTORY_ROAD is L38-42, already above the team, so it
ranks **#1** the instant anything calls it reachable. It stayed out of the live answer only
because of the `max_hops=4` distance bound, not because of an Elite Four gate. That gate must go
into `KNOWN_GATES` before phase 2 consumes a candidate list.

## 2026-07-26 — Victory Road is gated on Waterfall; one edge closes the whole cluster (#24-regionreach / #24-counters)

`KNOWN_GATES` grows its second hand-verified entry — and this one was made URGENT by the cost
ranking shipped hours earlier. Victory Road's Hariyama is **L38-42**, already above a mid-game
team, so its estimated training cost is ~0 and it ranks **#1** the instant anything calls the map
reachable. Before this it was kept out of the live counter list only by the `max_hops=4` distance
bound — a coincidence of distance, not a gate.

Probed rather than assumed: the ONLY boundary edge into the entire `VICTORY_ROAD_*` cluster is
`EVER_GRANDE_CITY (0,8) <-> VICTORY_ROAD_1F (24,43)`, and it was ungated. In Emerald that entrance
sits at the top of a **waterfall**, so HM07 is mandatory. One entry therefore closes every floor.

Also extends the capability vocabulary: `_GATE_MOVE_NAMES` gains `waterfall`, and
`_RSE_BADGE_BY_MOVE` gains `Waterfall -> BADGE08_GET` (the Rain Badge). Deliberately NOT added to
`_FRLG_BADGE_BY_MOVE`: an unknown move resolves to "capability unavailable", which CLOSES the edge
— the fail-safe direction, since a wrong NO costs a detour while a wrong YES sends the bot across
Hoenn.

Verified: `VICTORY_ROAD_1F` / `_B1F` → `reachable=False`, *"needs Waterfall at
EVER_GRANDE_CITY<->VICTORY_ROAD_1F"*; `EVER_GRANDE_CITY` stays reachable (the gate must close the
cave, not the coastline); `GRANITE_CAVE_1F` unchanged. The refusal NAMES the missing capability, so
"gated" stays distinguishable from "no path exists" — the whole point of the module (KI-24).
Pinned in `repro_region_reach.py`. Suite 7 files green.

## 2026-07-26 — OUT OF PP = a permanent livelock the HP-gated heal could never break (user's real-HW log)

**User report:** "ran into a shiny at the very start of the game before I got the Pokédex, and it
looks like that crashed the game — it tried to catch them ... maybe disable shiny logic until I get
the Pokédex flag?"

**‼ THE SHINY WAS A RED HERRING and the proposed fix would have changed nothing.** The shiny logic
worked exactly as designed: `'Story: shiny Zigzagoon — no catch possible here, fighting through.'`
It correctly saw no usable Poké Balls pre-Pokédex, took the fight-through fallback, and **won** the
battle at f1,054,368. The run then continued for another **1.86 MILLION frames**. What the user saw
as a "crash/reset" was `Story (ENDLESS RESET)` starting run 2 after the frame budget expired.

**The real bug, visible all around that shiny:** the run's outcome tally was
**3,011 `RanAway` · 5 `Won` · 1 `Lost`**, with `party=['Treecko L6 21/21']` — **full HP** in 152 of
the state dumps — parked on the Route 103 training tile at the pre-Pokédex step
`'Story: training the starter to Lv 8...'`. It fled essentially every battle, never gained a level,
and burned ~2,900,000 frames.

**Root cause — HP and PP do not deplete together.** Three facts compose into a livelock:
1. `train_team`'s heal gate is `_min_battler_hp_pct() <= heal_at` — **HP only, PP never consulted**.
2. `context.config.battle.lead_cannot_battle_action` defaults to **`"flee"`**.
3. The stock `LevelUpLeadBattleStrategy.decide_turn` takes that flee branch when
   `not any(util.move_is_usable(move))` — i.e. **out of PP, regardless of HP**.

A starter that WINS without being hit keeps full HP while its one attacking move drains. When the
last damaging PP goes, every encounter becomes "no usable move" → flee; fleeing takes no damage, so
HP stays pinned at 100% and the HP-gated heal can NEVER fire. flee → no XP → no level → spin →
flee, forever.

**Fix:** `_team_is_out_of_pp()` (no non-egg battler has a damaging move with PP left), and the
training loop now stops spinning AND heals on `low HP **or** out of PP`. A Poké Center heal
restores PP as well as HP, so this routes into the existing heal — no new mechanism. Fails safe: a
party read error returns False (assume PP remains), so a bad read can never cause an endless heal
loop, and the HP trigger is untouched.

**A/B on the exact logged state** (Treecko L6, 100% HP, Pound 0 PP, Leer 24 PP):
`old_gate=False` → `new_gate=True`. `repro_out_of_pp_livelock.py`, 6 cases, also pinning: status
moves with PP still count as dry (a 0-power move cannot train), a team-mate with PP means NOT dry,
eggs are skipped, and an unreadable party fails safe. Suite 8 files green.

**Why this matters beyond the one run:** it can strand ANY cold start, and it is invisible in the
usual signals — no error, no hang dump, full HP, the bot busily "training". Only the outcome tally
(3,011 RanAway vs 5 Won) shows it. Normally HP drops before PP so the heal fires first; this run
was unlucky in winning cleanly.

## 2026-07-26 — The validation harness was blind to the failure class that just cost a whole run

Follow-on from the out-of-PP livelock. Applying the new outcome-tally diagnostic RETROACTIVELY to
my own batch `20260726-052205` returned **zero battle outcomes for all five runs** — not because
those runs were clean, but because `story_harness.py` never logged an outcome at all. It logged
`battle_is_active -> False` and nothing more. `[BATTLE] ended (outcome=...)` comes from the GUI's
`modules/debug_logger.py`, which batch runs do not use.

**So five full cold starts could not have reported a 3,011-flee livelock even if they had hit one.**
A validation harness that cannot see "the bot flees everything" is blind to an entire failure class
— and that class had just burned ~2.9M frames of the user's real run.

Fixed in the tooling (no bot behaviour change):
* `story_harness.py` now reads `get_last_battle_outcome()` on the battle→over transition and logs
  `outcome=BattleOutcome.X`, guarded so an unreadable outcome degrades to `<unreadable>` rather
  than breaking the run.
* `livetest.py` gains `battle_outcomes` (a tally), `battles`, and a derived **`flee_rate`**, and
  the per-run console line now prints `battles=N flee=NN%` with a loud **`‼LIVELOCK?`** marker at
  ≥80% flee over ≥50 battles.

Validated against the user's real log rather than a synthetic one: `RanAway 3,011 · Won 5 ·
Lost 1` → **flee_rate 0.998**, correctly flagged.

**This is the second measurement blind spot found in two days** — after `livetest.py`'s whiteout
metric silently read 0 for every batch ever run (2026-07-25). Both had the same shape: a number
nobody had ever cross-checked against a raw count from the same logs.

## 2026-07-26 — ENDLESS RESET no longer forces the renderer off (user directive) — closes #24-pokenav-faithful's cause

**User's diagnosis, and it was right:** "I think that's due to the infinite run feature turning off
the video toggle upon reset — can we make it not mess with that and have it stay in whatever state
it's currently in?"

`StoryEndlessResetMode.run()` captured `batch_video = context.video` at batch start and re-applied
it after EVERY run. That was added for a real reason (a derail calls `set_manual_mode()`, whose
`enable_video_and_slow_down` default drops `emulation_speed` to 1 and throttled the rest of an
unattended batch — the user's earlier "on its second run it was at normal speed" report), but it
swept `video` up with the speed. Two consequences:
1. The renderer was **PINNED** to its batch-start value, so a batch begun with video off kept it
   off for every subsequent run — and the FAITHFUL PokéNav Match-Call tutorial only advances with
   the renderer ON. That is why it degraded to the last-resort state-write in **8 of 9** real-HW
   runs (`#24-pokenav-faithful`), the 1 success being a run whose renderer was still on.
2. Worse, the `except` fell back to `batch_video = **False**` — a single failed read of
   `context.video` would force the renderer OFF for an entire batch.

Now: **speed is restored, video is never touched.** If the user turns the renderer on mid-batch it
stays on. Only comments mention `context.video` in that mode now.

**Also — the PP heal is now OBSERVABLE.** The out-of-PP heal printed nothing, so a batch could not
show whether the fix ever fired (exactly the blind spot found hours earlier). It now prints
"Story: out of PP — healing at the Poké Center".

**‼ AND THAT ONE-LINE ADDITION WAS NEARLY A CRASH.** `early_game.py` has **no module-level
`console`** — it is imported locally inside three other functions only. `train_team` is not one of
them, and the heal block sits inside a `try/finally` that does NOT swallow exceptions, so a bare
`console.print` would have raised `NameError` on **every PP exhaustion** — turning a livelock into
a hard crash, i.e. strictly worse than the bug being fixed. Caught before commit by grepping the
module for `import console` rather than trusting that an import test passing meant the code ran.
**Third appearance of this scope trap in one day** (HM branch, survival mode, here). Verified by
EXECUTING the path (AST-check that `train_team` contains the local import + running the statements),
not by importing the module.

Batch `20260726-094520` (commit `0f4c734a`, first batch with outcome instrumentation): 2/5 frontier,
flee rates 1.2% / 23.8% / 2.2% / 4.3% / 6.6% — **no livelock**. Honest reading: the livelock is
intermittent (1 in 11 of the user's runs), so this is CONSISTENT with the PP fix, not proof of it;
`repro_out_of_pp_livelock.py` is the proof. run02 is an outlier worth watching (23.8% flee, 82
losses, 40 whiteouts, no frontier) — ordinary attrition, `#24-whiteout` territory. Suite 8 green.

## 2026-07-26 — ENDLESS LOOP ×4: four independent story bots, tiled in one window (#24-x4)

**What.** New `Emulator ▸ Endless Loop ×4…` command in the dashboard's bot-mode popup. It
launches FOUR independent `Story (ENDLESS RESET)` bots at once — each its own process, its own
profile, its own starter — and paints them as a 2×2 grid inside the dashboard's video area, with
the party strip and tool column left where they are. Lanes loop forever and restart
independently; all four run unthrottled and muted with debug logging on.

**Lane table** (fixed, so `P1` means Torchic in every log ever handed over):

| lane | starter | profile |
|------|---------|---------|
| P1 | torchic | `endless-P1-torchic` |
| P2 | mudkip  | `endless-P2-mudkip`  |
| P3 | treecko | `endless-P3-treecko` |
| P4 | random  | `endless-P4-random`  |

**Why the starter split is not cosmetic.** `early_game.py` already documents that Torchic has no
super-effective move against Roxanne and "may need extra training", and the 3,011-flee livelock
(2026-07-26) was a Treecko run. Stratifying by starter stops starter-specific failures from
hiding behind a lucky draw; the `random` lane keeps the sampling honest.

**New modules (sandbox):**
- `modules/tile_bridge.py` — the only thing lanes share with the dashboard: one `SharedMemory`
  block, 116 KiB per lane (240×160 RGB + a 1 KiB JSON status blob). Lock-free; the writer
  publishes pixels → status → header with `sequence` LAST, and the reader re-checks `sequence`,
  so a torn read is retried rather than shown.
- `modules/tile_mosaic.py` — the 2×2 grid renderer. Pure PIL, no Tk and no `context`, so the
  view can be rendered to a PNG and inspected without an emulator. Composes at FINAL size
  because the game frames need NEAREST upscaling and the labels do not.
- `modules/gui/tile_child.py` — the lane frontend (`PokebotTileChild`), selected by `--tile-shm`.
  `PokebotHeadless` plus a publish on the frame callback, gated to 20 Hz.
- `modules/endless_x4.py` — lane table, profile bootstrap, spawn/poll/stop, bounded auto-restart.

**Touched:** `pokebot.py` (hidden `--tile-*` / `--endless-target` flags, lane frontend selection,
lanes skip cloud-sync and the requirements check), `modules/gui/dashboard_gui.py` (menu item, tile
painting, click-to-focus, teardown on close), `modules/debug_logger.py` (`name_prefix`, so lane
logs are literally `P1-…`, `P2-…`), `plugins/custom_modes/story_mode.py`
(`ENDLESS_RESET_COMPLETED`, so a tile can show its lane's run count across the process boundary).

**Two hazards found and closed while building:**
1. `_close_window()` ends in `os._exit(0)`, so no `atexit` handler runs — without an explicit
   teardown, closing the window would have orphaned four emulator processes with no window left
   to stop them from.
2. A batch starts four processes within milliseconds. On a machine with no
   `.last-requirements-check` that would have been four concurrent `pip` installs into one
   environment. Lanes now skip the check entirely (a lane can only be spawned by a dashboard
   that has already passed it), and skip the launch-time cloud sync for the same reason.

**Verified** (this box has no `mgba`, so no live emulator run — see 04-HANDOFF for what the user
must still confirm): cross-process bridge round-trip, 4 slots, no crosstalk, unwritten slot reads
`None`; mosaic renders at 4 sizes and in every lane state (live / not booted / restarting /
stopped) with over-long messages truncated, short tile lists and corrupt frames non-fatal;
`_on_frame` publish path against a fake emulator — rate gate, RGBA and odd-size conversion, and
the two must-not-kill-a-lane cases (screen read raises, oversized message); dashboard wiring on a
real Tk canvas — paint, rate gate, no canvas-item leak over 30 repaints, all four click
quadrants, fall-through when no batch runs, clean teardown; lane profiles created with the right
starter in `story.yml` and read back correctly through `get_story_config()`, including a
hand-edited `story.yml` being reverted.

## 2026-07-26 — x4: the party strip follows the focused lane; badge recorder ships ahead of its UI (#24-x4 / #24-badges)

**1. The party strip now shows the FOCUSED LANE's team.** Click a tile, and the left strip
(and party tab, and hover tooltip) switch to that lane's Pokémon. The party belongs to
another process, so it travels in the lane's status blob and `modules/remote_party.py`
rebuilds stand-ins exposing the exact attribute surface the party UI reads — the renderer
is untouched. The attribute list was MEASURED off `dashboard_gui.py` (strip 1145-1240, tab
row 3209-3290, tooltip 1530-1700), not guessed. Clicking repaints immediately rather than
waiting for the sidebar cycle, which would otherwise leave the previous lane's team on
screen and read as "the strip isn't following".

`STATUS_BYTES` 1 KiB → 8 KiB: a real six-Pokémon team with moves and IVs measures 2,385
bytes, so the original cap would have silently dropped every party to the fallback blob.

**2. `modules/badge_log.py` — records what the team was when each badge was earned.**
Writes `<profile>/badge-log.json`; during an x4 batch that yields four independent badge
histories (P1's Roxanne team vs P4's). Polls the eight `BADGE0N_GET` flags once a second
from the main frame loop, appends across runs, and tags each record with
`run_started_frame` so records group by playthrough.
‼ It re-arms on emulator reset (hooked at `main.py`'s existing reset detection, so it
catches every reset path): the endless mode hard-resets between runs, which zeroes every
badge flag — a recorder that remembered across that would log run 1's badges and silently
never log another, in exactly the batch it was built for. The first poll of a run ADOPTS
whatever is already set without recording it, so loading a mid-game save cannot fabricate
"just earned" records with today's team attached.

**Why the recorder ships before the overlay UI the user asked for:** the UI can be built
whenever; this capture only ever records badges earned AFTER it is switched on. Every x4
run in the meantime would produce badge wins that can never be reconstructed.

**3. Log discoverability** (the user's "seems like they didn't log" — they had, in the lane
profiles): starting a batch now prints each lane's log folder to the event log; each tile's
label shows its log size (or `‼ NO LOG` in red); the lane's `debug_logger.enable()` result
is checked and reported instead of being swallowed by `try/except: pass` (it signals
failure by RETURNING an error string, so the old code was blind in both directions), and
the logger self-re-arms up to 5 times if it is ever found off.

**One genuine latent fix:** lane stdout (`P#-stdout-*.txt`) is a FILE, not a console, so
CPython block-buffered it at 8 KiB — a lane could run for minutes with nothing on disk.
Lanes now launch with `PYTHONUNBUFFERED=1`.

**Verified:** two new suites, six total, all green. `repro_x4_party.py` — every UI-read
attribute survives the round trip; `status_condition` returns the REAL enum member
(`dashboard_gui:3239` compares with `is not`, which any look-alike fails); a full 6-mon
blob fits STATUS_BYTES; the dashboard reads the focused lane and a click swaps the party;
junk/absent teams degrade to `[]`. `repro_x4_badgelog.py` — adopt-on-first-poll, record
once, poll interval, **records again after a hard reset**, accumulation across runs, a
broken party read costing the team but not the record, and every badge in the table having
its sprite on disk.

## 2026-07-26 — x4: "Park ×4 & Collect Logs" — one verified zip per batch (#24-x4-logs)

**What.** A new menu item, shown ONLY while a batch is running: `Emulator ▸ Park ×4 &
Collect Logs…`. It parks all four lanes, bundles every lane's logs into
`profiles/x4 LOGS/P1 - P4 x4 LOGs <date> <time>.zip`, verifies the zip, and only then
archives the originals into each profile's `debug-logs/Old/`. The point is to make handing
over a batch's data a single attachment instead of a scavenger hunt across four profiles.

**The order is the feature: park → copy → VERIFY → archive.**
- **Park.** Lanes are separate processes; a log still open for append can be copied
  mid-line and cannot be moved at all on Windows. This needed a parent→child command
  channel, so `modules/tile_bridge.py` gained a **parent-written** `COMMAND` region
  (`MAGIC` bumped to ...33). It is a separate region rather than extra header fields
  because the child rewrites the whole header on every publish and would clobber it. On
  `CMD_PARK` a lane drops to Manual at 1×, resets to the title screen, and CLOSES its debug
  log, then reports `parked: true`; `EndlessX4Batch.park_all()` waits for every lane to
  acknowledge before a byte is read.
- **Verify.** `modules/x4_logs.py` reopens the finished zip, runs `testzip()` for CRC
  integrity, and checks every source file is present with a matching size.
- **Archive only then.** If verification fails for any reason, nothing is moved, the zip is
  left for inspection, and the dialog says so. Losing run data to a tidy-up step that ran
  on a bad archive is the one outcome worth engineering against.

**Two interactions that would have broken it silently, both now guarded and tested:**
1. `_ensure_logging()` (the logger self-healer added earlier the same day) would have
   re-opened a parked lane's log a fraction of a second after the park closed it — so the
   collector would have archived a file another process had just resumed writing to. It
   now returns early when parked.
2. `EndlessX4Batch.poll()` auto-restarts dead lanes. A restart mid-collection would have
   started a fresh log and un-parked the batch underneath the copy. `poll()` returns early
   once `parked` is set, and `parked` is set BEFORE the wait rather than after it.

**What is archived vs. kept:** `*.log` and `*-stdout-*.txt` are per-run artefacts — bundled
and moved. `badge-log.json` is CUMULATIVE history (`modules/badge_log.py`) — bundled and
**never moved**, because archiving it would reset the badge record on every collection.
Collision-safe archiving (`name (1).log`), so repeated batches never clobber.

**Caught during development:** because `badge-log.json` is never archived, a second
collection with no new runs would have cheerfully produced a bundle of four badge files
and zero logs — a zip that looks like run data and is not. `collect()` now requires at
least one PER-RUN log and fails with "no new per-run logs were found" instead.

**Also:** the zip carries a `MANIFEST.txt` — per lane the starter, profile, file count and
a badge tally, then every file with its size and whether it was archived.

**Known cost, stated plainly:** `park_all()` BLOCKS the window briefly (typically ~100 ms,
bounded at 15 s). The dashboard has no Tk mainloop — its event queue is pumped from the
emulator frame callback — so pumping Tk from inside that wait would mean re-entering the
frame callback. A short honest freeze on an explicit user action is the safer trade. If a
lane fails to acknowledge, the user is asked before anything is collected.

**Verified:** `repro_x4_logcollect.py` (clean collection; naming incl. no ':' in the
timestamp; per-run archived and cumulative kept; manifest content; no re-bundling of
`Old/`; collision renaming; **verification failure archives nothing and does not even
create `Old/`**; `_verify` catches a missing member and a truncated zip; `archive=False`;
command channel round-trip; and a publish NOT clobbering a pending command).
`repro_x4_tile_child.py` gained park coverage: mode/speed/reset/log-closed, the
**self-healer not re-arming while parked**, command idempotence, and tiles staying live.
Suite now eight scripts, all green.

## 2026-07-26 — x4: a `random` lane now SAYS what it rolled (#24-x4)

**Trigger.** User report: "P4 is a copy of P3, it should be an independent run." P4's config
is correct (`starter: random`, re-rolled every run by
`help_birch_and_choose_starter()` → `random.choice`, verified by
`repro_x4_lanes.py`). What was missing was any way to SEE that: when the random lane rolls
Treecko it plays a Treecko run beside the pinned-Treecko P3 lane, and the tile label said
only `P4 · random`, so the two are indistinguishable on screen.

**Fix — observability, not behaviour.** `modules/story/early_game.LAST_CHOSEN_STARTER`
records the species actually resolved for the current run (and prints
`STARTER: config='random' -> playing Treecko` to the log). The lane publishes it in its
status blob and the tile label now reads `P4 · random→Treecko`, so a coincidental match is
visibly a coincidental match rather than a suspected duplicate.

**Caught by the suite while making that change:** the new `_chosen_starter()` helper was
spliced into the MIDDLE of `_status()`, cutting off its `return` — so `_status()` returned
`None` and every tile silently lost its whole status blob. `repro_x4_tile_child.py` failed
on it immediately. Added a key-completeness assertion (`lane`, `message`, `mode`, `frame`,
`parked`, `starter_chosen`, `log` all present) so this class of edit cannot pass again.

**Still open at time of writing:** whether two lanes running the SAME starter are
meaningfully independent, i.e. how far the GBA's RNG stream diverges between instances
booted from a hard reset within milliseconds of each other. The bot's own decisions are
documented as deterministic, but it does make Python-side random choices per process
(`story_mode.py:1330` training-strategy pick, `:2015` `random.randint(8, 10)` target
level), which decorrelate runs from those points on. The game-side half is being checked
against the pokeemerald decomp rather than asserted from memory.

## 2026-07-26 — ‼ Emerald cold starts were NOT independent samples; naming-screen decorrelation added

**How this surfaced.** The user reported "P4 is a copy of P3". P4's config was correct, but
the question behind it was not one anyone had asked: *are two lanes running the same
starter actually independent runs?* Verified against the pokeemerald decomp
(commit `83df84e4`, read from source — not asserted from memory):

- `gRngValue` is **0 at every hard reset** (`src/random.c`; COMMON_DATA, cleared by
  `RegisterRamReset(RESET_ALL)`, stored in no save block).
- **Emerald is NOT RTC-seeded.** `SeedRngWithRtc()` exists but sits inside `#ifdef BUGFIX`,
  and `include/config.h:48` is `//#define BUGFIX`. Emerald inherited FireRed's `main.c`.
  ‼ **Ruby/Sapphire DO seed from the RTC** (pokeruby `src/main.c:115`, unconditional) — so
  this conclusion is Emerald-specific and must not be generalised across Gen 3.
- The only per-frame advance is a bare `Random()` in `VBlankIntr()` (`src/main.c:365-366`),
  a pure function of frames since boot.
- The only single-player reseed is `SeedRngAndSetTrainerId()` → `SeedRng(REG_TM1CNT_L)`
  (`src/main.c:208-214`), reading a cycle-exact timer started when the naming screen OPENS
  (`src/naming_screen.c:412`) and read when the name is CONFIRMED (`:701`).

**Consequence:** from a hard reset, two instances fed the same frame-aligned input script
produce a **bit-identical game** — same TID/SID, same starter IVs and nature, same
encounters, same damage rolls, same crits. Four x4 lanes were closer to **one** sample than
four.

**How to read PAST batches.** Not worthless, but less independent than assumed. Lanes
diverged only once something consumed a different number of frames — a different starter
choice at Birch's bag, or the bot's own Python-side randomness (`story_mode.py:1330`
training-strategy pick, `:2015` `random.randint(8, 10)`). Everything BEFORE that — the
intro, the rival scene, the Birch rescue — ran identically across lanes, and two lanes that
rolled the same starter stayed in lockstep considerably longer. Early-game bug counts from
past batches should be read as *repeated observations of one run*, not as N samples.

**The fix — a random pause on the naming screen** (`modules/story/intro.py`). Since the
seed is taken from a timer read at name-confirm, the cycles between naming-screen open and
confirm are the ONLY externally controllable input to it; a delay anywhere earlier is
discarded by `SeedRng`. After typing the name and before confirming, the intro now idles a
random 0–120 frames. One frame shifts the seed by 280,896 mod 65,536 = **18,752**;
`gcd(18752, 65536) = 64`, so seeds cycle every 1,024 frames and a 0–120 range yields 121
distinct, well-scattered seeds for at most two seconds of wall clock. It is also more
faithful, not less: a human takes a variable moment to confirm a name.

Re-randomised per RUN, which matters as much as per lane — the endless mode hard-resets
between runs, and `gRngValue` is not saved, so without this **every run of a lane would
replay the same early game**.

`POKEBOT_RNG_DECORRELATION_FRAMES=0` restores fully deterministic cold starts, which is
what you want when REPRODUCING a bug rather than sampling. No existing `repro_*.py` is
affected — they all load save states rather than running the intro.

**Verified:** `repro_rng_decorrelation.py` — the env override (0, explicit, negative,
garbage), the random default's range and spread, the frame/seed arithmetic the design rests
on (280,896 cycles; 18,752 shift; gcd 64; 1,024-frame cycle; all 121 pauses distinct), that
the two CLOSEST reachable seeds diverge on the very first LCG draw and share nothing over
20 draws, and — asserted against the source, not the comment — that the pause really does
sit between typing and confirming.

## 2026-07-26 — Bag button + BADGE CASE overlay; and the 8th gym leader was wrong (#24-badges)

**Built.** A Bag button under the 6th party ball opens a badge-case overlay: the eight
Hoenn badges 2×4 as in the in-game case, full-colour when earned and a **black silhouette**
(shape kept, colour stripped per-pixel) when not. Hover shows the leader's details; click
pins them. The detail pane shows leader, city, type, ace, TM and the field move the badge
authorises — plus **the team that beat them**, read back from `badge-log.json`, with the
win count and timestamp when a badge has been taken many times across an endless batch.
During an x4 batch the case follows the FOCUSED LANE, exactly as the party strip does;
lanes publish their badge flags from `badge_log`'s existing poll cache, so it costs no
extra memory reads.

It is an in-window `place()`d frame, NOT a Toplevel: this module's own docstring records
that a Toplevel opens BEHIND the video in handheld fullscreen and looks like nothing
happened — and handheld is where the Bag button is most useful.

**‼ CORRECTION — the Sootopolis leader is JUAN, not Wallace.** The first badge table (in
`badge_log.py`, shipped earlier the same day) was written from memory and named Wallace,
which is Ruby/Sapphire. In Emerald `[TRAINER_JUAN_1]` is `TRAINER_CLASS_LEADER`
(`src/data/trainers.h:3268-3278`) while `[TRAINER_WALLACE]` is `TRAINER_CLASS_CHAMPION`
(`:4024-4034`) and is only battled in the Champion's Room; the game says so outright at
`data/maps/CaveOfOrigin_B1F/scripts.inc:65-69`. **Any `badge-log.json` record written
before this commit carries the wrong `leader` string for BADGE08 — the `flag` and `team`
fields are unaffected.** This is the second Gen-3-differs-across-Gen-3 trap in one session
(the first was Emerald's RTC seeding); both would have been wrong from memory.

**The whole table is now decomp-verified** (`modules/badge_case.py`), from the `_1` STORY
parties (`src/data/trainer_parties.h:3367-3613`), not the rematch parties: leaders, cities,
types, aces + levels (Nosepass 15, Makuhita 19, Manectric 24, Torkoal 29, Slaking 31,
Altaria 33, Lunatone/Solrock 42, Kingdra 46), TMs, and the badge→field-move mapping, which
is not folklore — `src/party_menu.c:117-127` orders the field-move enum to line up with the
badge flags and `:3725` enforces `FlagGet(FLAG_BADGE01_GET + fieldMove)`.
Two facts flagged rather than smoothed over: **Mossdeep is ONE trainer** (`TATE&LIZA`,
`.doubleBattle = TRUE`, a single 4-mon party — there is no `TRAINER_TATE`), and **Norman's
"Normal" type is INFERRED** from his party, because Petalburg's gym text is the one that
never states a type.

**Caught by the tests, twice.**
1. `badge_log.BADGES = tuple(...badge_case.BADGES...)` at module level *looked* like a
   derived view and was a SNAPSHOT taken at first import — so the two could drift, which is
   exactly what the "no second copy to drift" assertion caught. Now derived on every access
   via `badge_table()` + a module `__getattr__`. (Note module `__getattr__` does not fire
   for lookups *inside* the module, so the two in-module uses call `badge_table()`
   directly.)
2. The real table was left EMPTY until the decomp answer arrived, so the table-integrity
   assertions failed loudly rather than the UI quietly shipping invented leader data.

**Asset note:** the repo ships no bag artwork (`sprites/` has badges, items, Pokémon and a
few `other/` icons; the real bag lives in ROM graphics we do not extract), so the button
icon is a PIL-drawn satchel. Dropping a `Bag.png` into `sprites/other/` and loading it in
`_bag_icon()` is the swap if real art ever appears.

**Verified:** `repro_badge_case.py` — `build_case()` against a SYNTHETIC table (so the
logic does not depend on the table's contents): empty case, earned-from-flags,
earned-inferred-from-a-record, many wins per badge, `latest`/`team_summary`, and junk input
degrading rather than raising; the real table's integrity (8 badges, `BADGE01..08_GET` in
gym order, unique names, every sprite present on disk, every ace levelled); a Tk smoke test
of the overlay opening, hovering, pinning, an out-of-range index, toggling, double-close;
and the silhouette being a distinct, cached image with a missing sprite degrading to None.
Suite now ten scripts, all green.

## 2026-07-26 — First x4 bundle reviewed: three bugs in the new tooling, and where the runs actually die

**The collection itself worked** — `P1 - P4 x4 LOGs 20260726-181825.zip`, 12 MB, four lanes,
manifest and archive correct, `badge-log.json` copied and not moved. Batch ran 17:47→18:18.

### What the runs show (the actual story data)

| lane | starter | runs | won | lost | fled | whiteouts | died at |
|------|---------|------|-----|------|------|-----------|---------|
| P1 | torchic | 1 (unfinished) | 484 | 5 | 13 (2.5%) | 5 | Route 110 ×3, Mauville Gym ×2 |
| P2 | mudkip | 2 | 206 | 41 | 50 (16%) | 40 | **Route 110 ×41** |
| P3 | treecko | 1 (unfinished) | 524 | 5 | 17 (3%) | 5 | Mauville Gym ×4 |
| P4 | random→Treecko, then Torchic | 2 | 386 | 26 | 30 (6.5%) | 26 | Route 110 ×20, Mauville Gym ×6 |

- **Runs are LONG.** In 31 minutes across four unthrottled lanes only 6 runs started and
  none reached the frontier; P1 and P3 never finished a single run. Frontier work needs
  hours per lane, not minutes.
- **Route 110 is the attrition sink**, not gym leaders — P2 whited out there 41 times and
  derailed on "too many whiteouts", P4 20 times. This is `#24-whiteout` territory and the
  strongest evidence yet for it: P2 and P4 lost 66 battles between them on ONE route.
- **The two clean lanes (P1, P3) died at Mauville Gym** — Wattson, the 3rd badge. That is
  roughly the real frontier for a cold start at this commit.
- **RNG decorrelation is working:** P4 rolled Treecko then Torchic across its two runs, and
  no two lanes tracked each other.

### ‼ Three bugs in MY tooling, found by the user's own logs

**1. Badge false positives — the recorder believed garbage reads.** P1 started ONE run and
its badge log claimed **Stone ×10, Knuckle ×5, and a Balance badge** (the 5th) in a run that
reached the 2nd. Root cause found in the debug log: badge flags live in the save block, and
during a map warp save-block reads return nonsense for a frame or two — visible directly as
the MAP flipping to a garbage group and back in the same window:

    f1190097 [MAP] MAUVILLE CITY(0,2) -> MAUVILLE CITY(10,5)
    f1190101 [MAP] MAUVILLE CITY(10,5) -> MAUVILLE CITY(0,2)

The poll landing there recorded Balance, then Stone+Knuckle together one interval later.
Fixed with three independent filters: **debounce** (a flag must read set on two consecutive
polls), **once per run** (`_recorded_this_run`), and **gym order** (a badge whose
predecessors are unset is a corrupt read — Hoenn's gyms are linearly gated).

While testing the fix, a fourth bug fell out: a badge rejected by the order filter was
absorbed into the "already seen" set and could then never be recorded even once its
predecessors legitimately arrived. `_known` is now the DISPLAY set only and plays no part
in deciding what to write.

**2. The lane prefix never reached the log anyone reads.** The bundle has a 1 KB
`P1-Manual-debug-*.log` beside a 649 KB **untagged** `Story_(ENDLESS_RESET)-debug-*.log`.
`StoryDebugResetMode` re-enables the logger once per run
(`story_mode.py:2704,2733`) with no prefix, overwriting the lane's own. Passing the prefix
per call was never going to be enough — `debug_logger.set_name_prefix()` now holds it
module-wide so every caller picks it up, including ones that know nothing about lanes.
Also: the lane enabled logging BEFORE setting `bot_mode`, which is why that first file said
"Manual"; ordering fixed.

**3. Run grouping silently collapsed.** Every P4 record carried `run_started_frame=0`
despite P4 completing two runs, because `main.py`'s "frame counter went backwards"
heuristic did not fire. `StoryEndlessResetMode` now calls `badge_log.reset_for_new_run()`
directly at the top of each run — it knows exactly when one starts — and records carry a
`run_index` that increments per reset.

**Note for future analysis:** battle outcomes appear ONLY in the debug-log file, never in
stdout. Any summarizer pointed at `*-stdout-*.txt` will report `battles=0` — the same trap
`livetest.py` already documents for whiteouts. Read the `*-debug-*.log` files for outcomes.

**Verified:** `repro_badge_transient.py` (new) replays the real trace — nine warp transients
in one run must yield exactly one Stone and no phantom Balance — and drives each filter
independently, plus the prefix surviving a no-argument `enable()`.
`repro_x4_badgelog.py` updated to the debounce contract. Suite now eleven scripts, all green.

## 2026-07-26 — Startup crashes are now readable (crash log + exit pause)

**Trigger.** User: "I tried closing the program and running it again and it gives me an
error but quickly closes after I type y." The error was real but UNDIAGNOSABLE — nothing in
the bot wrote a traceback anywhere, and `install_sandbox.py` launches the bot as a
SUBPROCESS OF THE INSTALLER (`install.py:506`, `subprocess.run([bot_python, "pokebot.py"…])`),
so the traceback printed into a console that closed with it.

Worse, `pokebot.py`'s exit pause only fired when the parent process was `py.exe` — the
installer uses `python.exe`, so the one mechanism that would have held the window open was
inert in exactly the launch path most people use.

**Fixed both halves:**
- `modules/exceptions_hook.py` now writes every unhandled exception to
  `crash-<YYYYmmdd-HHMMSS>.log` beside the bot, with the profile and bot mode in a header,
  and prints the path. Fully guarded — a failure to write the crash log must never replace
  the crash.
- `pokebot.py`'s exit pause also triggers when stdin is an interactive terminal. ‼ It is
  gated on `isatty()` specifically so the ENDLESS LOOP x4 lanes (spawned with
  `stdin=DEVNULL`) and headless/piped runs still exit immediately rather than hanging
  forever on an `input()` nobody can answer.

`crash-*.log` added to `.gitignore` (diagnostic artefact, not source).

**Not yet fixed: the crash itself.** An import sweep of every module touched in the previous
commit (`debug_logger`, `badge_log`, `badge_case`, `main`, `dashboard_gui`, `tile_child`,
`story/intro`) plus `load_plugins()` is clean under the mgba stub, and this dev box has no
`mgba` so the real startup path cannot be run here. The crash log is what will identify it.

## 2026-07-26 — ‼ FIXED: `profiles/x4 LOGS/` killed the bot at startup

**The crash the user hit.** With the crash log in place, the console stayed open long
enough to read it — and it was self-inflicted:

    Starting PokeBot Gen3 dev!
    Could not load ...\sandbox-pokebot\profiles\x4 LOGS\metadata.yml, file does not exist.
    Please re-download the program or restore the missing file.

**Root cause.** `list_available_profiles()` iterates every directory under `profiles/` and
guards with `except RuntimeError`. But `load_profile()` → `load_config_file(..., strict=True)`
raises `exceptions.CriticalFileMissing`, which is a **PrettyException, not a RuntimeError** —
so the guard never fired, the exception reached the top-level hook, and the bot exited
before the profile screen. ENDLESS LOOP x4 writes its bundles to `profiles/x4 LOGS/`
(where the user asked for them), so the FIRST launch after the first successful log
collection died.

**This was never specific to the x4 folder.** Any non-profile directory under `profiles/`
would have done it — a half-copied profile, a Windows "New folder", a user's own notes.
That latent fragility has presumably always been there; the x4 bundle folder is simply the
first thing that reliably created one.

**Fix.** `list_available_profiles()` now skips entries that are not directories, and
directories with no `metadata.yml`, BEFORE trying to load them. Loading a profile **by
name** still raises the helpful `CriticalFileMissing` — that is correct there, because a
user who named a broken profile deserves to be told exactly what is wrong rather than
having it silently vanish from the list.

**Verified:** `repro_profiles_stray_dir.py` (new) — enumeration survives an `x4 LOGS`
folder containing a zip, a "New folder", a loose file and a half-copied profile directory;
underscore-prefixed entries are still skipped; a real profile is still found; and
`load_profile()` by name still raises `CriticalFileMissing`. Confirmed against the real
sandbox `profiles/` directory with an `x4 LOGS` folder present. Suite now twelve, all green.

## 2026-07-26 — Second x4 bundle: the badge fix is CONFIRMED, and a run reached the frontier

**Batch `20260726-201838`** — 18:55→20:18 (83 min), **16 runs** across four lanes.

### The badge fixes are verified against real data

`badge-log.json` is cumulative, so records were split at the fix time. **Every post-fix run
is clean**: correct gym order, no duplicates, no phantom badges.

| lane | post-fix runs | badge sequences |
|------|---------------|-----------------|
| P1 | 3 | `Stone→Knuckle→Dynamo→Heat`, `Stone→Knuckle`, `Stone→Knuckle` |
| P2 | 2 | **`Stone→Knuckle→Dynamo→Heat→Balance→Feather`**, `Stone→Knuckle→Dynamo→Heat` |
| P3 | 3 | `Stone→Knuckle` ×2, `Stone` |
| P4 | 5 | `Stone→Knuckle` ×3, `Stone` ×2 |

Compare the pre-fix bundle, where P1 recorded **Stone ×10 in a single run** plus a phantom
Balance. Lane prefixes now work too — story logs are `P1-Story_(ENDLESS_RESET)-debug-*.log`.

### ⭐ P2 FINISHED A RUN — six badges, end of built content

`run end: finished (1,992,945 frames)` with `Stone→Knuckle→Dynamo→Heat→Balance→Feather`.
Badge 6 (Winona) is the current content frontier, so that is a complete cold-start
playthrough of everything built, in ~2.0M frames.

### Where runs die has SHIFTED — and it is no longer attrition

| lane | starter | runs | Won | Lost | flee | whiteouts | top loss sites |
|------|---------|------|-----|------|------|-----------|----------------|
| P1 | torchic | 4 | 1298 | 27 | 1.3% | 27 | Petalburg Gym ×8, Mauville Gym ×7 |
| P2 | mudkip | 3 | 934 | 43 | 6.6% | 44 | **Route 110 ×19**, Petalburg Gym ×7 |
| P3 | treecko | 3 | 1456 | 10 | 2.0% | 10 | Mauville Gym ×7 |
| P4 | random (Torchic, Treecko) | 6 | 1384 | 12 | 2.5% | 12 | Mauville Gym ×7 |

In the previous bundle Route 110 dominated everything. Now **GYM LEADERS dominate** —
Mauville (Wattson) for three lanes, Petalburg (Norman) for P1. P2 remains the outlier and is
still bleeding on Route 110. The bot is getting further, and the failure has moved from
travel attrition to boss fights.

**Almost every derail is the same message: `derailed: this boss: N losses with no progress`** —
that is `_boss_plan_is_hopeless` firing and raising the counter-plan `BotModeError`. So the
counter chain correctly diagnoses "I have no answer to this type" and then **ends the run**,
exactly as documented. This is the strongest possible argument for `#24-counters` phase 2:
those runs would otherwise have continued.

### Two diagnostic bugs found and fixed

1. **`run_index` advanced by two per run** (1, 3, 5, 7, 9 — no even numbers), because
   `reset_for_new_run()` is called by BOTH `main.py`'s frame-counter detection and the
   endless mode. Deduped on "has any poll happened since the last reset?".
   ‼ My first attempt deduped on FRAME DISTANCE and was actively wrong — `get_frame_count()`
   resets with the emulator, so every run starts near 0 and every boundary looked like a
   duplicate; it would have merged an entire batch into one run. `repro_badge_transient.py`
   caught it. The second attempt used wall-clock, which works but makes the function
   untestable without sleeping. The shipped version is deterministic and needs no clock.
2. **`finished (-959,198 frames)`** — the endless mode computes
   `get_frame_count() - start_frame`, which goes negative when the emulator resets mid-run.
   A negative value also silently disabled the `MAX_FRAMES_PER_RUN` wedge guard, since
   nothing is ever greater than the cap. Now clamped, and the anomaly is reported.

## 2026-07-26 — x4 batch review (`20260726-231412`): two catastrophic endless-loop bugs fixed

Reviewed the user's four-lane overnight bundle (118 MB, 3 app launches, 4 lanes). Headline:
**the batch was producing almost no usable data while reporting most runs as successes.**

**Fixed — `sandbox-pokebot/plugins/custom_modes/story_mode.py`**
- **Per-run state never reset between runs.** `StoryEndlessResetMode.run()` loops on the same
  mode object, so `StoryMode.__init__` ran once per BATCH — under a comment asserting the
  opposite. `_rival_attempts` (cap 3) tripped on run 4 in every lane, so **runs 4+ quit at the
  Rustboro rival without fighting it** (16/20 P1, 6/9 P2, 5/8 P3; P1 run 8 logged ZERO lost
  battles yet reported "couldn't beat the rival in 3 tries"). `_defeat_counts` leaked across
  runs so boss give-up thresholds fired on borrowed losses (MT_CHIMNEY #7→#8, FORTREE #8→#9;
  P4 run 2 derailed as "6 losses" after 3). Extracted `StoryMode.reset_per_run_state()`,
  called by the endless loop at each run boundary; `_ki15_nudge_*` and `_rival_attempts` are
  now initialised there rather than materialising via `getattr` defaults.
- **Failed runs reported as "finished".** `outcome` defaulted to `"finished"` and only a
  raised `BotModeError` changed it, but a derail can call `set_manual_mode()` and return
  normally. Added a `try/except/else` that detects the hand-to-Manual exit and reports
  `stopped:`. Several dead runs had printed as `finished (0 frames)`.
  ‼ The genuine end-of-built-content return ALSO calls `set_manual_mode()`, so `StoryMode`
  now sets an explicit `_reached_end_of_content` flag before it; without that, this fix
  would have relabelled real completions as failures — P2 run 1 of the bundle reached the
  Feather Badge exactly that way. The flag is cleared per run.

**Fixed — `sandbox-pokebot/modules/badge_log.py`**
- **`run_index` still advanced by 2 per run** (P1: 1, 3, 5 … 37 over 19 runs) despite a prior
  fix. The prior adjacency dedupe could never fire, because the mode signals *before*
  `super().run()` while the hard reset happens *inside* it. Replaced with ownership:
  `reset_for_new_run(..., authoritative=True)`; main.py's frame-counter fallback stands down
  for the rest of the process. The adjacency guard was retained for the non-authoritative
  path (removing it broke `repro_badge_transient.py`).

**New repros** — `tools/story-dev/repro_endless_per_run_state.py`,
`tools/story-dev/repro_badgelog_run_index.py`. Both A/B'd: FAIL against HEAD, PASS against
the fix. Suite: **44 pass, 0 fail**, 6 environmental (need a real mgba / pre-existing).

**Environment note.** The repro suite did not run on this machine at all — `confz` and other
deps were missing, and the default `python` is 3.9 (unsupported). Installed the import-chain
deps into **Python 3.12** and verified there; `py -3.12` is the correct interpreter for these.
The handoff's claim of "13 emulator-free repros" undercounts — **44** run without an emulator.

**Confirmed healthy** (no action): badge recording is clean in all four lanes (correct gym
order, no duplicates, no gaps), and losses:whiteouts held at exactly 1:1 — no unlogged
whiteouts.

**Logged, deliberately NOT fixed blind:** `#24-leadpolicy` (the matchup lead is purely
defensive and benches the only mon that can win) and `#24-route110cap` (that rival gets no
prep and no cap — but a naive cap would have killed a run that recovered after 13 losses).
Both need a user ruling; see the punch list.

## 2026-07-27 — x4 batch review (`20260727-063751`): runaway runs are now actually stopped

**‼ This batch ran the PRE-FIX code.** It launched 2026-07-26 23:20:49, minutes after the
previous bundle and hours before the `20260726` fixes were committed — and the bot runs from
a separate working copy (`…\Pokebot_Gen3_Enhancement_old\sandbox-pokebot`) that had not been
pulled. Confirmed from the data: runs 1-3 real and runs 4+ `finished (0 frames)` in P1/P2/P4,
and `run_index` stride still 2. So it re-confirms the known bugs and adds NEW findings; it is
not a test of the fixes.

**Fixed — `sandbox-pokebot/plugins/custom_modes/story_mode.py`**
- **`MAX_FRAMES_PER_RUN` could not stop a runaway run**, only report one after it finally
  returned. Three of four lanes spent the night in a single run — P3 hung 27M frames /
  ~6.5 h at the Weather Institute (`controllable=False`, frozen position, ZERO STUCK dumps,
  so the global watchdog was itself the thing that wedged); P1 19.9M and P2 13.4M frames in
  non-converging grind loops that no progress detector can see because they are genuinely
  busy. P4 run 12 reported the cap only after burning 2x it. The batch lost ~16 of 29
  lane-hours. Added `_run_with_frame_budget()`, which steps the story generator and enforces
  the budget every 2048 yields, raising `BotModeError` into the existing derail path. It
  re-bases when the frame counter goes backwards (the mid-run hard reset), because measuring
  `now - start_frame` goes negative and silently disables the bound.
  REPRO: `tools/story-dev/repro_endless_frame_budget.py` (A: FAIL → B: PASS), covering the
  hang, the livelock, the mid-run reset, non-disturbance of legal runs, and generator close.

**Also observed, logged not fixed**
- P4 broke the 1:1 losses:whiteouts canary twice (run 1: 39 W vs 38 L; run 8 opens with a
  whiteout before any loss). Two events in 52 — consistent with a whiteout event crossing a
  run boundary rather than poison damage. The new per-run reset may already cover it; worth
  re-checking on the first post-fix batch rather than chasing now.
- New derail reasons seen: `Cannot hunt a Surf learner: no …` (P1 run 3) and a `global
  watchdog` derail (P4 run 13).

**Confirmed healthy:** badge records clean in all four lanes again (correct order, no
duplicates, no gaps), including P4 run 1, which reached the Feather Badge with 6 badges
despite 38 whiteouts.

## 2026-07-27 — Documentation correctness audit (docs 00/01/02/05/14 + one code docstring)

A verification pass over the knowledge base while the user ran batches. **Method, chosen to
avoid poisoning the docs:** read-only subagents verified claims against CODE and reported
`file:line` evidence; only the main thread edited files. Agents that cannot write cannot
introduce a bad fact. Every load-bearing agent claim was then independently re-checked
before being applied — two were wrong and were discarded (see 08-MISTAKES).

**`02-ARCHITECTURE.md` — was materially wrong about the repo's own shape**
- The folder map **omitted `sandbox-pokebot/`, where all current work happens**, plus
  `tools/`, `PROJECT KIT/`, `REMOTE START/`, `cloud-backups/`, and both installers. The
  prose meanwhile referenced sandbox-only modules, so the doc contradicted itself.
  Rewrote the map, added a "Which copy am I in?" table, and recorded that the two forks
  have genuinely diverged (ten modules exist only in sandbox).
- Corrected verified-wrong facts: recommended Python is **3.13**, not "targets 3.12"
  (`requirements.py:7`); libmgba downloads to **`<copy>/mgba/`**, not `pokebot-gen3/mgba/`
  (`requirements.py:185`); `context` is imported by **118** files under
  `sandbox-pokebot/modules/` (114 custom, 98 mirror), not "116" — that figure matched no
  copy; the declared YAML dep is **`ruamel.yaml`**, PyYAML is undeclared/transitive.
  Module counts clarified as 59 mirror / 83 sandbox / 74 custom. "23 bot automations"
  re-verified correct.
- **Added the testing section that did not exist.** The `repro_*.py` suite is the project's
  real verification bar and 02 never mentioned it, nor that it needs `py -3.12`.
- Added `debug_logger` and `badge_log` as per-frame main-loop participants.

**`01-VISION-AND-DESIGN.md` — the active copy had no intent section**
- Added a `sandbox-pokebot/` component section (purpose, why it exists, promotion rule,
  the divergence, and the different-machine caveat).
- Fixed copy-ambiguous headings: Story-Mode bot and Endless Loop ×4 named bare paths, and a
  reader following the doc's own text would have looked in `custom-pokebot/`, where the ×4
  files **do not exist**.
- Retired the stale "Future: custom automations, installer, custom interface" placeholder —
  all three are BUILT. Added real intent sections for the five custom bot modes, the
  `tools/story-dev/` verification harness, the two installers, and the custom interface.

**`05-KNOWN-ISSUES.md` — re-audited every entry against `sandbox-pokebot/`**
- Replaced the framing paragraph claiming ALL entries are upstream bugs (true only of
  KI-1…KI-5; everything from KI-6 is our own code).
- Documented that IDs are **not contiguous** — no KI-12, no KI-13; 23 distinct IDs across
  25 headings.
- Flagged six entries whose bodies still prescribe work that is already shipped — worst is
  **KI-18**, whose body says *"Do NOT patch on the hypothesis. Reproduce first"* for a fix
  that was proven and shipped (`battle_handler.py:475-501`).
- Corrected KI-24b: `KNOWN_GATES` holds **three** edges, not one (`region_reach.py:81-91`).
- **Added KI-25…KI-29**, all previously unlisted and all evidenced: the defensive-only lead
  selection (incl. the Flannery segment not doing what its own comment says), the uncapped
  Route 110 rival, the Weather Institute hard hang, the training livelocks, and the P4
  canary anomaly.

**`00-README.md`** — the reading order stopped at doc 16, making 09–11 and 17–23 plus
`ai-research-notes/` invisible to anyone following the documented ritual. Added a
"read when relevant" index.

**`14-AGENT-PLAYBOOK.md`** — added §2b (the repro suite as the verification bar, with the
sweep command and the 90s-timeout gotcha) and **§2c, a repeatable method for reviewing x4
log bundles** — now a recurring job, with the five checks and the five traps that each cost
real time. Added 10 prevention rules earned on 2026-07-26/27.

**`sandbox-pokebot/modules/story/region_reach.py`** — its module docstring still said *"NOT
wired into story_mode.py or counter_plan.py yet … wiring it in is a follow-up task"*. It has
been wired since 2026-07-25 (`story_mode.py:553` and `:606`). A stale "not done yet" note is
worse than none: it invites a future session to redo finished work.

Verification: repro suite **47 pass, 0 fail, 5 environmental** — unchanged from before the
edits.

## 2026-07-29 — Five bundles reviewed: all four harness fixes VALIDATED LIVE; the dominant remaining cost is the counter chain

Bundles: `20260727-164830`, `20260728-172826`, `20260728-221523`, `20260728-222654`,
`20260729-062040`. The running machine had pulled, so this is the first data that actually
tests the 07-26/27 work.

**All four fixes confirmed in production**
- **Per-run state reset.** `couldn't beat the Rustboro rival` fired **31 times in P2's 32
  runs** on 07-27 (pre-fix) and **zero times in every bundle after**. Runs 4+ play again.
- **Frame budget.** Max single-run frames now 1.9M–3.1M, all under the 3.5M cap; the 27M and
  30M-frame hangs are gone. It fired once (P3, 07-28) and the batch continued past it.
- **`run_index`.** Stride 1 across all four lanes in the newest bundle (was all-odd stride 2).
- **Honest outcomes.** Derails are itemised and attributable rather than reported as
  `finished`.

**Throughput.** Newest bundle: 56 runs across four lanes, **16 reached the Feather Badge
(end of built content)** — P1 ×5, P2 ×5, P4 ×4, P3 ×2. Previously that was a once-per-batch
event.

**‼ The dominant remaining cost: the counter chain diagnoses correctly, then ends the run.**
Of 36 derails in the newest bundle, **~26 (72%)** are "boss: N losses with no super-effective
answer to X. Need one of: Y" — the chain NAMES the counter it needs and then stops. Breakdown:
Electric→needs Ground ×17, Normal→needs Fighting ×9, Winona/Dragon-Flying ×3. This is
`#24-counters` phase 2 and it is now the single biggest lever by a wide margin.

**‼ Starter-specific finding — exactly what the ×4 instrument was built to expose.** P3
(Treecko) stalls at 2 badges in **11 of 14 runs**, and **10 of its 11 derails are Wattson**
("no super-effective answer to Electric. Need one of: Ground"). P2 (Mudkip) never has this
problem because Marshtomp is Water/**Ground** — immune to Electric and super-effective back.
Torchic and random sit in between. The bot's Gym-3 viability is essentially decided by the
starter, and only Mudkip is self-sufficient.

**New derail classes seen for the first time** (P1): `No party mon can learn Surf and the
party is full — needs PC box management (#24-pc)` ×2, and `Cannot hunt a Surf learner: no
Poké Balls and no money to buy any` ×1. Both are resource-exhaustion walls rather than combat
failures.

**Canary:** losses:whiteouts held at 0.99–1.01 in every lane of every bundle.

**Logged, not fixed:** a duplicate `Stone` badge on **run 1 of every batch, in all four
lanes** (`['Stone','Stone','Knuckle',…]`). Recorded as KI-30 with the cause flagged as
HYPOTHESISED, not proven.

**Analysis-method correction (mine, not the bot's).** `run_index` restarts at 1 for every
process, so grouping a cumulative `badge-log.json` by `run_index` across days MERGES separate
batches and manufactures fake duplicate/out-of-order badges. First pass over this data did
exactly that and briefly read as a badge-recorder regression. Correct method — segment by
detecting a `run_index` that does not increase — is now in `14-AGENT-PLAYBOOK.md` §2c.

## 2026-07-29 — PC investigation: story code has NEVER touched the PC; `team_policy` built (pure, capped by measurement)

**Investigation (user question: does the bot ever use the PC?).** No — and the cause is more
basic than "it never exceeds 6":
- **The only caller of `interact_with_pc` in the entire repo is stock
  `modules/modes/daycare.py`, and it only RELEASES.** No story code path deposits, withdraws
  or reads a box. Confirmed by grep across `modules/story/` and `plugins/custom_modes/`.
- `_catch_team_target = 4` (`story_mode.py:845`) caps catching at four.
- The party still reaches 5-6 — via story **gifts** (Castform etc.), not catching. Measured
  from the 2026-07-29 bundle: 4 mons in 281 badge records, 5 in 55, 6 in 27.
- So nothing can ever leave the party, and dead weight is permanent.

**Measured consequences** (363 badge-moment team snapshots, newest bundle):
- **35% of badge moments carried ≥1 mon 15+ levels below the team max**, up to FIVE at once.
- P1 reached the **Feather Badge at team-max L48 still carrying a Zigzagoon L8.**
- P1 caught a **Makuhita — Fighting, exactly Norman's counter — and carried it L8 → L9 across
  FIVE badges** while the team went L22 → L42. The answer was in the party and never usable.
- **12 derails** in that bundle were *"No party mon can learn Surf and the party is full"* —
  runs ending because a full party of dead weight left no room for an HM carrier.

**Built: `sandbox-pokebot/modules/story/team_policy.py`** — a PURE module (no memory reads,
no walking, no input) implementing design §2/§4: `dead_weight()`, `find_dead_weight()`,
`rotation_plan()`, with the HM-sole-carrier and favourite exemptions, and a rotation that
reports `worth_it` so a caller never burns a PC visit for nothing.

**‼ The spec's threshold was corrected by measurement before wiring.** Design §2's
`level < lead_level - 8` is a correct statement of "will never be caught up", but used
directly as a deposit rule it would have boxed 3+ mons in 41% of real parties, left **59%
below three mons**, and cut **132 four-mon parties to one** — the "lone starter can't rotate"
state behind KI-8. Fact and decision are now separate: the predicate is unchanged;
`rotation_plan` caps at `MAX_DEPOSITS_PER_ROTATION = 2` and never drops below
`MIN_PARTY_AFTER_ROTATION = 3`, worst-first. Post-cap over the same 363 parties: deposits of
0/1/2 only, zero parties left under three. `21-TEAM-POLICY-DESIGN.md` §2 amended.

**Not yet wired.** This module decides; nothing calls it yet. Wiring it into the heal-trip
seam needs a live emulator run and is the next step.

Repro: `tools/story-dev/repro_team_policy.py`, asserting against the REAL parties above.
Suite: **48 pass, 0 fail, 5 environmental.**

## 2026-07-29 — Backup tag created; fodder-gate defect ANALYSED and deliberately NOT changed

**Backup / revert point: tag `backup/pre-trainmap-2026-07-29`, pushed to origin.** Marks the
last known-good state before the `#24-trainmap+` work. Restore recipes (all additive — no
force-push, no `reset --hard`, because the batch machine pulls from this remote) are in
`04-HANDOFF.md §0-BACKUP`.

**Investigated the training-area gate and found a real defect — see KI-31.** The gate
relocates only when `local_max + FODDER_LEVEL_GAP < team_max_now`, i.e. it compares the WILD
level to the TEAM level. The project's own calibrated model says XP per battle is
`50.2 × wild_level / 7` — proportional to the **wild** level and independent of the team.
Measured against the real `TRAINING_GRASS` bands, the failure window is teams **below ~L17**
(since `5 + 12 = 17`): a L15 team on Route 102's L3-5 wilds forgoes a **2.8× speedup**, a L10
team 1.6×. Above L17 the gate works correctly.

**‼ NOT CHANGED, on purpose — two blockers, both real:**
1. **The conservatism is deliberate.** `tools/story-dev/repro_fodder_grass.py` states the
   contract: *"WATTSON / ROXANNE / an early team → UNCHANGED 'train locally' (the whole point
   of the conservative gap: proven-good prep must not move)"*. Teams at L10-17 are exactly
   those bosses, so any fix moves prep that currently works.
2. **The governing test cannot run here.** That repro loads a real ROM and
   `saves/norman_done.ss1`; it needs `mgba` and is one of the 5 environmental failures on this
   dev box. Changing the rule it governs, blind, is precisely the move `08-MISTAKES` warns
   about.

Proposed replacement, ready for the batch machine: swap the level-gap test for a frame-saving
test built on the existing pure `estimate_frames_to_level` — relocate when the better area at
least HALVES the estimated grind (`better_hi ≥ 2 × local_max`). Needs no new constant and no
travel measurement, which matters because travel cost is still unmeasured
(`story_mode.py:576` says so).

No behaviour changed in this entry. Suite: 48 pass, 0 fail, 5 environmental.

## 2026-07-29 — The fodder rule is now a PURE, FLAGGED decision (behaviour unchanged, KI-31)

Follow-on from the KI-31 analysis. The change that could not be made safely is now *ready*
to be made safely, without touching what the batches currently do.

**`modules/story/training_areas.py`** gains:
- `xp_per_battle(wild_level)` — the calibrated model, exposed. XP is proportional to the
  **wild** level and independent of the trainee.
- `local_patch_is_fodder(local_max, team_max, gap, *, best_available_max, rule)` — the
  decision extracted out of `_prepare_for_fight` as a PURE function, so it can be tested
  exhaustively with no emulator.
- `FODDER_RULE`, **defaulting to `"legacy"`** — the original inline expression, unchanged —
  and `"xp_rate"`, which relocates when the better area at least halves the grind
  (`XP_RATE_RELOCATE_RATIO = 2.0`; a 2× band is a 2× rate).

**`plugins/custom_modes/story_mode.py`** now routes the decision through that function. Under
the default the block behaves exactly as before, **including performing no extra area
lookup** — the probe the new rule needs is gated behind the flag, so the legacy path keeps
its original single-lookup shape.

**Proven** (`tools/story-dev/repro_fodder_rule.py`, no emulator):
- the extracted legacy path reproduces the old inline expression across **all 1,800
  `(local_max, team_max)` combinations**, 0 mismatches;
- an unknown `local_max` is never "fodder" (fail safe — never relocate on ignorance);
- the two rules disagree on **exactly L5-L17 and nowhere else**, so flipping the flag cannot
  disturb prep from L18 up;
- the new rule refuses a marginal 1.3× gain and refuses to move when nothing better is known;
- the old inline expression is gone, so the rule cannot drift into two copies.

**Boundary correction.** The hole is teams **at or below L17**, not "below 17": legacy needs
`local_max + 12 < team_max`, so with L5 wilds it is False *at* 17 and first fires at L18. The
first draft of the repro asserted the wrong boundary and failed — the off-by-one was in the
assertion, not the code. KI-31 corrected.

**TO LAND THE FIX** (needs the machine with `mgba`): run `repro_fodder_grass.py`, set
`FODDER_RULE = "xp_rate"`, run it again, compare the WATTSON/ROXANNE rows — those are what
the flag changes. Only then consider changing the default.

Suite: **49 pass, 0 fail, 5 environmental.** No behaviour changed for the running batches.

## 2026-07-29 — The fodder A/B is runnable without editing code (user pushback)

The user asked why running the KI-31 experiment required them to edit `FODDER_RULE` by hand.
Correct challenge — the handoff was wrong in three ways (full write-up in `08-MISTAKES.md`):
the interface was a source edit on a remote machine; **`install.py`'s self-healing
(`git checkout -- <drifted>`) could have silently reverted that edit**, and I had just told
them to run `install_sandbox.py` first; and nothing named the active rule in the output, so
even a successful flip could not have been attributed afterwards.

- **`POKEBOT_FODDER_RULE=xp_rate`** now selects the rule. Env-var, so it survives the
  installer, needs no code change on the batch machine, and vanishes with the shell.
- Case/whitespace normalised; an **unknown value raises** rather than falling back — a typo'd
  `xprate` quietly running `legacy` is the worst possible outcome for an A/B.
- **`active_fodder_rule_banner()`** prints the active rule and how it was set into every
  ENDLESS-RESET run header, so a bundle records which arm produced it.

The default is unchanged (`legacy`) and remains correct: the governing
`repro_fodder_grass.py` needs a real `mgba` and the early-game conservatism is deliberate.
Suite: **49 pass, 0 fail, 5 environmental.**

## 2026-07-29 — The rule banner now reaches the DEBUG LOG, not just the console

Caught from a live partial log the user shared mid-run. That log **confirmed the deployment
worked** — `StoryEndlessResetMode._run_with_frame_budget @ story_mode.py:2931` appears in the
generator call stack, and that function exists only in the 2026-07-29 commits — but it
carried **no record of which training-relocation rule was active**.

Cause: `console.print` and `modules/debug_logger.py` are **separate streams**; the debug
logger never sees console output. The banner added earlier printed to the console only, and
the debug log is the artefact actually shared for review. A run's own log must describe the
run.

Fix: the per-run header also calls `debug_logger.event(banner, category="STORY")`. Asserted
in `repro_fodder_rule.py`.

**Also verified while reading that log:** the flag would not have changed anything at that
point in the run regardless. On Route 103 (L2-4 wilds) with a L6 team, the best reachable
alternative is Route 102 (L3-5) — a 1.25× rate gain, below the 2.0× threshold — so BOTH rules
correctly decline to relocate. The two rules only diverge at boss prep; an early-game log is
not evidence either way.

Suite: **49 pass, 0 fail, 5 environmental.**

## 2026-07-29 — Debug logs are now SELF-DESCRIBING (user directive)

**User, verbatim:** *"all of this should be native to the debug logging... I should not have
to make arbitrary cmd commands to do this, why is this not native to the debug logs?
including version numbers and extensive details?"* — correct, and overdue.

The header was **two lines**: a timestamp and the log path. So a shared log could not answer
on its own which BUILD produced it (that needed `git log` on the originating machine), which
experiment ARM it belonged to (unanswerable after the fact), or what Python/ROM/profile/
emulation settings were in play. **Three separate times in two days a log had to be sent back
to the user with "please run this command".** That is the tool failing, not the user.

`modules/debug_logger.py` now emits a RUN HEADER at `enable()`:

```
--- RUN HEADER (build, config, experiment) ---
    build:         acf08ca13507 on branch main
    bot:           PokéBot Gen3 dev
    python:        3.12.4 on Windows 11
    mode:          Story (ENDLESS RESET)
    profile:       test
    rom:           <name> (<lang>) rev <n>
    emulation:     speed=0 video=False audio=False
    fodder-rule:   xp_rate (env) ratio=2.0
    env:           {'POKEBOT_FODDER_RULE': 'xp_rate'}
--- END RUN HEADER ---
```

Design points:
- **No subprocess.** `_git_facts()` reads `.git/HEAD` and the ref (with a `packed-refs`
  fallback) directly — `git` is often absent from PATH on a machine that only runs the
  installer, and a subprocess costs ~50-150 ms on Windows.
- **Every fact is optional.** Each is individually wrapped; a failure degrades that line to
  "unknown" and can never block logging.
- **A default is reported, not omitted** — `legacy (default)` vs `xp_rate (env)`, plus an
  explicit "(no behaviour env vars set)". Silence is not evidence.
- `_BEHAVIOUR_ENV_VARS` is the registry any future experiment flag must join, or a log will
  not be attributable to its arm.

Repro: `tools/story-dev/repro_debug_log_header.py`. Two of its own assertions were wrong on
first run and it caught them: one matched the word "subprocess" inside the docstring
explaining why subprocess is avoided; the other resolved `_write_run_header()` to the
function DEFINITION rather than the call site. Both fixed by anchoring after the START line
and stripping docstrings — the same "anchor on the property, not on text that also appears
elsewhere" lesson as the earlier repro drift.

Suite: **50 pass, 0 fail, 5 environmental.**

## 2026-07-29 — Full review of run log `20260729-122709`: best run yet, plus a watchdog blind spot

**The new RUN HEADER worked** — the log identified itself immediately: build `4d77685f`,
Python 3.13.2, ROM Emerald (E) rev 0, profile `test`, `speed=1 video=True`,
`fodder-rule: legacy (default)`. No commands needed. That is the whole point of it.

### This was the deepest single run on record
One run (1/10) cleared **Roxanne → Brawly → Wattson → Flannery → Norman** and reached
**Winona** — Gym 6, end of built content. **310 battles won**, 14 lost, 34 fled, 4 caught,
3 opponent-teleported. Along the way, several subsystems proved out live for the first time:

- **‼ The FAITHFUL PokéNav Match-Call tutorial PLAYED** — `"tutorial done (called Mr.
  Stone)"`, with **no state-write fallback**. The run had `video=True`. That confirms the
  renderer-gate diagnosis exactly and closes the open recurrence of `#24-pokenav-faithful`:
  the faithful path works when the renderer is on; the 8-of-9 fallback rate was a video-off
  artefact, not a breakage.
- **The economy works.** Ran out of Poké Balls → `"buying 10 Poké Balls at the mart…"` →
  `"bought Poké Balls (now have 33)"`.
- **HM-slot refusal handled** — `"The game refused that slot (HM). Replacing slot 2 instead."`
- Mauville maze, the full 8-step Lavaridge geyser/trapdoor maze, Rusturf wall (Wanda),
  Meteor Falls, Cable Car, Weather Institute (**the site of KI-27's 27M-frame hang — no hang
  this time**), Devon Scope, Route 120, the Fortree bridge — all cleared.

### The failure: a mid-battle rotation wedged the party menu (new: KI-33)
In a Fortree Gym trainer battle the bot rotated `Marshtomp L35` out for `Castform L25`,
reverted 22 frames later, rotated again, then sat in `state=3` (PARTY_MENU) at one fixed
position until stopped. This is the **open half of KI-8** — which claims the Story bot
"sidesteps this path" because its trainer strategy never proactively rotates. Something
rotated anyway; whether it was the strategy or the after-faint chooser is **not yet
established** and needs an emulator to settle.

### The bigger defect it exposed, now FIXED: KI-32
That freeze ran **~280,000 frames and produced ZERO stuck dumps** — no generator call stack,
nothing to diagnose from. Cause: stall detection did
`if st.get("battle_active"): _stall_frames = 0` on every in-battle frame, so **no in-battle
wedge could ever be reported, however long it lasted.** Same shape as KI-27, where the
watchdog was itself the thing that could not fire.

Fixed: a battle now gets a much larger THRESHOLD rather than an exemption —
`_BATTLE_STALL_DUMP_AFTER = 18_000` (5 min at 60fps; ~60× the overworld threshold and two
orders of magnitude above the longest legitimate quiet stretch). Overworld sensitivity
unchanged. Repro `tools/story-dev/repro_battle_stall_blindspot.py` proves a frozen battle now
dumps, a changing battle never does, 300/3,000/10,000-frame in-battle quiet is untouched, and
a long wedge re-dumps periodically.

### `team_policy` validated against this run's real party
Final party: `Castform L25, Dustox L31, Breloom L34, Skitty L15, Marshtomp L35` — 5 of 6
slots, with a **20-level** spread. Replaying the unwired `team_policy` predicate on it flags
**Skitty L15 and Castform L25**, and `rotation_plan` would deposit exactly those two, leaving
three. ‼ **Castform L25 is the very mon whose rotation caused the wedge.** Had the module been
wired, it would have been boxed before Fortree.

### Notes / open questions
- **`speed=1 video=True`** — throttled with the renderer on. Video is what made the faithful
  PokéNav path work, so this is a genuine tradeoff against throughput, not a misconfiguration.
- **`fodder-rule: legacy`** — `POKEBOT_FODDER_RULE` was not set, so the KI-31 A/B did NOT run.
  This is the control arm.
- 14 lost battles but only **1** `"stepping out of the Poké Center after the whiteout"` step.
  The x4 stdout counted whiteouts via a console-only message, so this is probably a
  message-availability gap in the debug log rather than a real anomaly — **worth confirming**
  before treating the 1:1 canary as measurable from debug logs alone.

Suite: **51 pass, 0 fail, 5 environmental.**

## 2026-07-29 — All DEBUG Story modes now configure emulation like an x4 lane (user directive)

The user cannot run ENDLESS LOOP x4 on their work machine (not enough power for four
emulators), but x4 lanes get a much better test config automatically and a hand-launched bot
inherited whatever the GUI had — run `20260729-122709` logged `emulation: speed=1 video=True`,
i.e. **throttled**, so 2.78M frames took hours.

`Story (DEBUG)`, `Story (DEBUG - RESET)` and `Story (ENDLESS RESET)` now call
`_apply_debug_emulation_config()`, setting **`emulation_speed = 0` (unthrottled)** and
**`video = True`** — exactly what `endless_x4.py:160` and `gui/tile_child.py:84` give a lane.
Plain `Story` is deliberately NOT touched: a human watching a normal run keeps control.

- **Video ON is load-bearing, not cosmetic.** The PokéNav Match-Call tutorial only advances
  with the renderer on; `20260729-122709` played it faithfully with no state-write fallback,
  where the user's earlier video-off runs fell back 8 times in 9.
- **‼ This supersedes the 2026-07-26 "SPEED ONLY — NEVER TOUCH `context.video`" directive.**
  That rule existed because the loop used to CAPTURE video at batch start and RE-PIN it every
  run, so a batch begun with video off stayed off for ever. The harm was pinning to an
  arbitrary value, not writing the field. Ruling + rejected alternatives in
  `06-DECISIONS-LOG.md` 2026-07-29.
- **Ordering matters and is tested:** `ENDLESS RESET` applies this BEFORE capturing
  `batch_speed`, or every run after the first is restored to the OLD speed — the 2026-07-25
  "second run crawled at 1x" bug from the other direction.
- **Escape hatch:** `POKEBOT_STORY_DEBUG_TURBO=0` leaves both settings untouched. The applied
  values show up in every debug log's RUN HEADER, so there is no ambiguity.

Repro: `tools/story-dev/repro_debug_emulation_config.py` — drives the real helper (default,
idempotence, each setting independently, all four escape-hatch spellings, a hostile context,
all three modes wired, the ordering constraint, and that plain `Story` is untouched).

Also logged in `08-MISTAKES.md`: **three** repro assertions in this session failed on first run
because a source-text anchor matched a docstring or a function definition instead of the call
site. Two of the three failed on *correct* changes. Prevention rules recorded.

Suite: **52 pass, 0 fail, 5 environmental.**

## 2026-07-29 — `xp_rate` is now the DEFAULT: a double-click must get the intended behaviour

**User question:** *"would simply running the install sandbox script by manually clicking it
work? if not then we need to ensure this install sandbox script automates the xp rate
addition."*

**Answer, established from the code:** double-clicking `install_sandbox.py` DOES work for
pull / heal / launch — it is a 45-line wrapper that sets `BOT_DIR_NAME = "sandbox-pokebot"`,
`LAUNCH_EXTRA_ARGS = ["--no-audio"]`, the log path and version suffix, then calls
`install.main()`, which does `git fetch` + `git pull --ff-only`. It runs under any Python 3.9+
(`install.py` has `from __future__ import annotations`, so its `X | None` annotations are
strings). **But a double-click cannot set an environment variable**, so the bot would have run
`legacy` — the intended rule would never actually have run.

**Fix: flip the default** rather than teach the launcher a trick.
`FODDER_RULE` now defaults to `"xp_rate"`; `POKEBOT_FODDER_RULE=legacy` is the documented way
back. Every launch path — double-click, GUI, CLI, x4 lane — now agrees, and there is a single
source of truth instead of a launcher-specific override that would drift.

**Rejected: `os.environ["POKEBOT_FODDER_RULE"] = "xp_rate"` inside `install_sandbox.py`.** It
would only apply to that one launch path, leaving the GUI and CLI on a different rule, and it
puts the value in two places.

**‼ RESIDUAL RISK, STATED PLAINLY.** `repro_fodder_grass.py` — the test that governs this
decision and the reason the default was `legacy` — **still has not been run on any machine**
(it needs a real ROM + save state). The arms provably differ only for teams at/below L17 and
only at boss prep, and every run names its rule in the log header, so the blast radius is
bounded and attributable. This is a **user-directed default, not a validated one.** If early
prep regresses: `POKEBOT_FODDER_RULE=legacy`.

**Two repro assertions had quietly depended on the old default and failed — correctly:**
- `repro_fodder_rule.py` tested the legacy arm without naming it, so flipping the default
  produced 975 "mismatches". Now every legacy assertion passes `rule="legacy"` explicitly.
- `repro_debug_log_header.py` hard-coded `"legacy" in header`. Now it asserts the **shape** —
  the header marks the rule as `(default)` and names whatever the current default is — because
  what a log reader needs is attribution, not this week's value.

Suite: **52 pass, 0 fail, 5 environmental.**

## 2026-07-29 — Analysis of three more datasets (NO code changed, at the user's request)

Datasets: single run `20260729-151635`, x4 bundle `20260729-172342` (a ~17-minute partial
batch), and the 07-28 overnight stdout carried inside that bundle.

### ‼ The KI-32 in-battle stall fix earned its keep on its first production run
P2 of `20260729-172342` emitted **71 in-battle STUCK dumps** over 210,000 frames. Before that
fix the log would have been silent — exactly as it was for the Fortree wedge, which cost a day
of not knowing. This time the dump named the culprit outright:
`handle_fainted_pokemon @ battle_handler.py:532/:537`.

That is the user's reported bug — *"training with a skitty and an Abra in the team in a double
battle but had issues selecting the Abra"* — now **KI-34**, with the party state, the task
cycle and the stack recorded. It is a LIVELOCK (state cycles, party never changes), and its
`if frames > 6000: return` bound is defeated by dispatcher re-entry (~35 re-entries).
It also **answers KI-33's open question**: the after-faint chooser, not the battle strategy.
KI-17, marked ✅ FIXED, **is not fixed for the multi-faint case**.

### A successful run now uses 87% of the frame budget — see KI-35
`20260729-151635` **completed**: six leaders including Winona, 462 wins, **3,058,007 frames**
against a 3,500,000 cap. The in-run budget added on 2026-07-27 will start killing successful
runs. Driver: **78 heal round trips in one run** — no potion layer, so every HP dip is a full
Poké Center walk. `#24-provisions` is now the dominant cost of a run.

### ‼ CORRECTION to what I told the user earlier
I said the fodder-relocation decision was "invisible in debug logs, so the xp_rate A/B cannot
be evaluated". The first half is true — it is `console.print` only (`story_mode.py:1474`,
`:1480`) and never reaches a debug log. **The conclusion was wrong:** x4 bundles ship the
per-lane *stdout*, where those messages DO appear. The A/B has been measurable all along from
an x4 bundle; only a single-lane debug log lacks it.

**Baseline (control arm) now measured** from the 07-28 overnight stdout, which predates the
`FODDER_RULE` flag entirely and therefore ran the original inline legacy rule:

| lane | runs | relocations | skipped-grind |
|---|---|---|---|
| P1 | 14 | **12** | 0 |
| P2 | 13 | **2** | 0 |
| P3 | 14 | **12** | 0 |
| P4 | 15 | **6** | 0 |

So legacy relocates **32 times across 56 runs** — it is not inert, it simply fires late in a
run once the team is 12+ levels above the local wilds. When the xp_rate overnight batch
arrives, comparing these counts is the A/B. Expect xp_rate ≥ legacy; a large jump concentrated
in early-game prep is the intended effect, and any *drop* would be a red flag.

### Confirmations
- All four lanes of `20260729-172342`: build `21b587f1`, `speed=0 video=True`,
  `fodder-rule: xp_rate (default)`, correct per-lane starters. The x4 config and the flipped
  default both propagate correctly, with no env var set.
- `rival-giveup = 0` in every lane of the overnight batch — the per-run-state fix continues to
  hold.
- losses:whiteouts 0.99–1.01 in all four lanes.
- Dead weight persists: the completed run finished carrying **Shedinja L21 beside Blaziken
  L44**; the P2 livelock party held **Skitty L15 and Abra L7** beside a L27 Marshtomp.
  `team_policy` (built, still unwired) flags these.

### Held deliberately — no code touched
`MAX_FRAMES_PER_RUN` (KI-35), the KI-34 instrumentation, and the relocation-message channel
are all identified and unmodified, pending the user's overnight x4 batch.

## 2026-07-29 — Applied the three held fixes (frame budget, KI-34 instrumentation, log channel)

**1. `MAX_FRAMES_PER_RUN` 3,500,000 → 5,000,000 (KI-35).** A run that BEAT Winona used
3,058,007 frames — 87% of the old cap — so the in-run budget added on 2026-07-27 was about to
terminate winning runs and report them as wedged. Re-derived from measured data using the
original constant's own rule (~1.5× the deepest completed run): deepest observed is 3,117,110,
so 5M gives ~1.6×. ‼ Raising it costs less than it used to: since KI-32 an in-battle wedge
emits a STUCK dump after 18,000 frames, so the cap is no longer what NOTICES a hang, only what
ENDS one — a wedge is now diagnosed ~270× sooner than the cap fires.

**2. KI-34 instrumentation — the next occurrence will name its own cause.**
`handle_fainted_pokemon` now emits via `debug_logger.event(category="BATTLE")`:
- on entry: `[FAINT-CHOOSER] alive_slots=… on_field=… party=[(slot, species, hp)…]`, with an
  explicit `‼ NO ELIGIBLE REPLACEMENT — cannot succeed` when `alive_slots` is empty. That single
  line separates the two candidate mechanisms (empty candidate set from the KI-18 on-field
  exclusion, vs printer-task branch starvation).
- on give-up: `[FAINT-CHOOSER] GAVE UP after N frames … presses={…} cursors_seen=[…]`, and it
  states outright that the dispatcher will re-enter, so a reader sees a repeating LIVELOCK
  rather than silence. The press histogram is the only thing that distinguishes *pressing the
  wrong thing* from *pressing nothing* (playbook §7) — a state trace cannot.
Counted per iteration, emitted once per invocation, so it cannot flood a log.
**The root cause is still not fixed, deliberately** — the two mechanisms need opposite fixes
and the data to choose between them does not exist yet.

**3. The fodder/relocation decision now reaches the DEBUG LOG.** Both the "relocating to X" and
"no better area — skipping the grind" messages were `console.print` only, so the effect of the
KI-31 xp_rate experiment was invisible in the one artefact describing a run. Added
`_log_story_event()` (a named mirror to `debug_logger.event`) and tagged both messages with
`[rule=…]`. **Third time this exact gap has bitten** — the rule banner, the relocation
decision, and the chooser's filter state — so the helper's docstring records the rule: *if a
decision matters to a reviewer, it goes through here as well.*

Verified: both edited modules parse and import; `_ta` is provably bound before its first use in
`_prepare_for_fight`; `MAX_FRAMES_PER_RUN` reads back as 5,000,000.
Suite: **52 pass, 0 fail, 5 environmental.**

## 2026-07-30 — Overnight batch `20260730-062818`: KI-34 diagnosed, and my own frame budget found blind

68 debug logs, **55 on build `00db4a81`** (the instrumented one), all four lanes on
`xp_rate (default)`, `speed=0 video=True`. Analysis only — no code changed.

### ‼ KI-34 is diagnosed, and one of my two hypotheses is dead
The instrumentation added the day before did exactly its job. Across **7,539 chooser entries
and 3,978 give-ups**:
- **`alive_slots` was NEVER empty (0 of 7,539)** → the "KI-18 exclusion starves the candidate
  set" hypothesis is **refuted**.
- **`presses={'A': 289}` — A and nothing else**, and **`cursors_seen=[1]`**, a single position
  that **is** in `alive_slots`.

So the cursor is already parked on a living, eligible mon and ~289 A-presses are simply not
accepted. It is the printer-task branch re-arming (`Task_PrintAndWaitForText` /
`Task_ReturnToChooseMonAfterText`) and starving every other branch. **KI-17's `post_gap = 24`
is not enough.** Located at `MAUVILLE CITY(10,0)` in 3,975 of 3,975 cases, with two `on_field`
slots — a **double battle at Mauville Gym**, exactly as the user first reported.

**Cost:** P3 burned **23,857,950 frames** (~7.8 complete runs) and finished only **5**
badge-earning runs overnight against P2's **19**. 99.9% of give-ups are P3/Treecko — the lane
with no Ground answer to Wattson, so it loses, faints, and re-rolls the chooser endlessly.

### ‼ KI-36 (NEW) — my per-run frame budget cannot fire inside a battle handler
P3 run `235303` ran **25,632,106 frames** — 5× the 5M cap — and the batch reported
`frame-cap=0`. `_run_with_frame_budget` is a **generator wrapper**, and the controller stack is
**FLAT**: `main_loop` advances only the TOP generator. That run's stack was
`[StoryEndlessResetMode.run, TrainerApproachListener.handle_trainer_approach, BattleListener.fight]`
in **8,022 of ~8,200 samples**, so the story generator — and my budget — was never stepped.

**The budget is blind to exactly the failure class it was written for**, since every wedge we
have is inside a battle handler. KI-32's stall dumps still fire because `debug_logger` is a
per-frame *listener*, not a generator. Net: **diagnosis without termination.**

### The xp_rate A/B — result is the OPPOSITE of my prediction
| arm | runs | relocations | per run |
|---|---|---|---|
| legacy (07-28 baseline) | 56 | 32 | **0.57** |
| xp_rate (this batch) | 68 | 22 | **0.32** |

I predicted "expect xp_rate ≥ legacy" and wrote that a drop would be a red flag. **It dropped.**
The likely reason is structural, not a bug: `xp_rate` requires a **2× wild-level ratio**, while
legacy fires on any **12-level gap** to the team. Late in a run the team is L35+ on L24-27
grass — legacy fires (27+12 < 40), `xp_rate` does not (28/27 = 1.04×). So `xp_rate` is *more*
permissive early and *more* conservative late, and the late-game case dominates the counts.
**Not yet judged good or bad** — it needs an outcome comparison, not a count comparison.

### Throughput
Runs reaching **6 badges (Feather / end of built content)**: P1 **8**, P2 **7**, P3 **2**,
P4 **6** = **23** of ~55 badge-earning runs (**42%**), against **16 of 56 (29%)** in the legacy
batch. Encouraging, but confounded — the raised cap, `xp_rate`, and the instrumentation all
changed at once.

### On the raised frame cap (KI-35)
4 runs exceeded the old 3.5M cap, but they are the **wedged** ones (25.6M, 10.1M, 3.54M ×2),
not legitimate long runs — the deepest *completed* runs remain ~2.9M. So this batch does **not**
demonstrate that the raise saved a good run. The raise was still correct (14% headroom on a
winning run was too tight), but it has not yet paid for itself, and I should not claim it has.

## 2026-07-30 — KI-34 FIXED (index-space bug) and KI-36 netted; both from a user screen observation

**KI-34 — `modules/battle_handler.py`.** The after-faint recovery sweep compared a cursor read
in **in-battle menu order** against an `alive_slots` set built in **regular party order**. Once
the orders diverge — exactly a double battle after switches — it judged an ON-FIELD mon
selectable, pressed A on a selection the game refuses, re-armed `Task_PrintAndWaitForText`, and
looped. Measured: `presses={'A': 289}` with a static cursor, **3,975 give-ups in P3 alone,
~23.9M frames (~7.8 complete runs)** in one night; that lane finished 5 badge-earning runs
against P2's 19.
1. `alive_slots_menu` now maps through `map_battle_party_index()` and every cursor test uses it
   — mirroring what this same function's PRIMARY path already did 60 lines earlier.
2. `FAINT_CHOOSER_GIVEUP_LIMIT = 3` per battle, then a **recoverable derail** via
   `battle_fault.request_mode_recovery()`. Never a `raise` — battle code is a SIBLING of the
   mode on a flat stack, so a `BotModeError` would reach `main_loop` and force Manual.

**KI-36 — netted, not solved.** `debug_logger` ticks every frame as a per-frame listener
(precisely why its stall dumps fired when the generator-based frame budget could not), so it
now also ENDS an in-battle wedge at 60,000 frames of identical state via the same fault channel.
**Only works with debug logging on** — a stack-independent budget in `main_loop` is still the
complete fix and stays open.

**Credit where due:** the root cause came from the user watching the screen, not from telemetry.
My instrumentation logged both integers and I read them as agreeing — they were in different
coordinate systems. Recorded in `08-MISTAKES.md`: *log the UNIT, not just the value*, and *take
a user's direct observation of the screen as primary evidence over your own telemetry.*

Repro: `tools/story-dev/repro_faint_chooser_index_space.py`. Suite: **53 pass, 0 fail, 5
environmental.**

## 2026-07-30 — KI-34 fix CONFIRMED live; it exposed KI-37 (a deadlock the fix itself created)

Two logs, both on build `4f1e02f9`: `20260730-074518` (ENDLESS RESET) and `20260730-081347`
(DEBUG - RESET).

### ✅ The KI-34 diagnosis is CONFIRMED and the fix works
`[orders DIVERGE]` appears with concrete evidence —
`alive_slots=[1, 2, 3](party-order) -> [0, 2, 3](menu-order)` — so the two party index spaces
really do diverge in practice, exactly as the user's screen observation implied.
**`GAVE UP` fell from 3,975 in a single lane to 3 per run.**

### ✅ The battle-fault hand-over works — when the mode can be reached
In the ENDLESS-RESET log the hand-over was claimed **one frame later**:
`f902223 [STORY] DERAIL #1: Story: battle handler gave up — after-faint chooser could not send
a mon out after 3 attempts (KI-34)`. Clean derail, run continues.

### ‼ KI-37 — and the fix caused it
In the DEBUG-RESET log the identical hand-over at f1,797,401 was **never claimed**, and the run
sat at `state=3` for **1,182,000 frames** until stopped by hand. KI-36's 60,000-frame net also
fired and was also unclaimed. Cause: `TrainerApproachListener.handle_trainer_approach` was an
unbounded `while script_is_active: press B` loop with **no fault check**, so it sat on top of
the controller stack starving the mode — the only thing that can consume a fault.
**`BattleListener` already had exactly this guard ~110 lines above**, with a comment naming the
identical hazard; the sibling listener never mirrored it. Third instance of that shape.
`battle_fault.py`'s own docstring predicted it: *"An unconsumed fault would be far worse than a
Manual drop."* **Fixed**; asserted in `repro_faint_chooser_index_space.py`.
**Still open:** audit every listener that can sit above the mode, and bound their loops. KI-36's
complete (stack-independent) fix would make the whole class impossible.

### ‼ KI-38 — 3 residual give-ups, and the user's text fallback has now earned its place
New press profile: `presses={'Down': 3, 'A': 273}`, `cursors_seen=[0, 2, 3, 7](menu-order)` in a
FOUR-mon party against a mapped target of menu-0. Two unexplained things the data cannot
separate: cursor **7** (almost certainly the CANCEL entry — if the walk overshoots, `Down` may
never return to the target), and 273 A-presses with the cursor reportedly reaching the target.
This is exactly the case the deferred `#24-menutext` was reserved for: reading the game's own
refusal message distinguishes "wrong target" from "right target, refused". Deferring it was the
right call — had it shipped alongside the index fix, the 3,975 → 3 improvement could not have
been attributed. **The exact string must come from the decomp, never recall.**

Suite: **53 pass, 0 fail, 5 environmental.**

## 2026-07-30 — KI-37 CONFIRMED FIXED live; failure classes now RECOVER instead of hanging

Logs `20260730-095944` (u1) and `20260730-105452` (u2), both build `d7d493d8`.

**u1 — the important one.** 3.15M frames, 3 badges (Roxanne/Brawly/Wattson), reached the Mt.
Chimney Cable Car, 448 battles won. **Six derail events, ALL SIX recovered:**
| # | cause | outcome |
|---|---|---|
| 1 | scripted event hit while pathing to (19,19) | recovered |
| 2 | **KI-34 after-faint chooser gave up** | handed over → **claimed** → derail → continued |
| 3,5,6 | global watchdog, 18,000 frames | recovered |
| 4 | **KI-36 in-battle wedge, 60,000 frames** | net fired → recovered |

**‼ KI-37 is fixed.** Hand-overs are now CLAIMED: worst stall **111,000 frames vs 1,182,000**
before, and the run continued rather than freezing until stopped by hand. The run ended by
exhausting its consecutive-derail budget and starting a fresh run — a bounded, designed exit.

**u2 — clean.** Interrupted by the user at f242,969 ("Bot stopped: Encountered Whismur"); the
remaining ~1.67M frames are idle heartbeats after the stop, not a wedge. **0 give-ups, 0
in-battle stalls, 0 hand-overs.** The faithful PokéNav Match-Call tutorial completed again
("done (called Mr. Stone)").

### Honest read
There are **no unrecovered errors**. But the recovery machinery is doing real work — roughly
six wedge events in one 3.15M-frame run — so the underlying causes are still there; they are
now *survivable* rather than fatal. Specifically still open: **KI-38** (3 residual chooser
give-ups), and a **new instance**: a wild **Slugma** encounter wedged for 111,000 frames before
the nets caught it. Both are tracked; neither blocks story work.

**Latency note:** the KI-36 net fired at f1,857,704 and the first derail landed at f1,883,706 —
**~26,000 frames to claim**. Far better than never, but not instant; worth watching if wedges
become frequent.

---

## 2026-07-30 — `#24-counters` phase 2, step 1: the HUNTING-GROUND GATE (ranking is not a gate)

**New:** `training_areas.HUNTING_GROUNDS` + `hunt_ground_tile()`; `counter_plan` candidates
now carry `hunt_tile` / `huntable`, and `counter_plan.best_huntable()` is the ONLY function an
executor may use to choose a destination. Proof: `tools/story-dev/repro_counter_huntable.py`
(offline, real ROM tables — **ALL PASS**).

### Why this had to land before any travel-and-catch code

`find_counter_candidates` ranks by estimated cost = *frames to find* + *frames to train it up
to the team's level*. A wild that is **already above the team costs ~0 to train**, so the
cost model systematically ranks **deep-endgame encounters as the CHEAPEST answers.** Measured
2026-07-30 against the real ROM tables:

| boss | needs | rank-1 candidate | huntable? |
|---|---|---|---|
| Norman | Fighting | **Hariyama, VICTORY_ROAD_B1F, L38-42** | no |
| Wattson | Ground | Sandshrew/Trapinch, ROUTE111 | yes (tile) |
| Winona | Rock/Elec/Ice | Electrike, ROUTE118 | yes (tile) |

Phase 1 only ever *printed* that list, so it was harmless. Phase 2 **travels** to it — so
shipping the executor against `cands[0]` would have walked a mid-game team toward Victory Road.
This is punch-list blockers **(3)** and **(4)** of `#24-counters`, closed together.

‼ **Not theoretical.** `repro_counter_wiring.py`, run live from the Winona-era save, has
`_counter_area_allowed` reporting **Magma Hideout, Shoal Cave and the Safari Zone as
`reachable`** — 10/10 candidates reachable. Reachability was never going to filter these.

### Whitelist, not blacklist — and it fails CLOSED

A blacklist of endgame maps would be an ever-growing list of **game facts written from
memory**, which this project forbids. The whitelist needs no claim about Mirage Tower at all:
it is simply not a ground anyone has swept, so it is refused. Two evidence-backed sources:
`TRAINING_GRASS` (two-way swept tiles) and the new `HUNTING_GROUNDS`.

`HUNTING_GROUNDS` encodes a distinction that already existed only in prose: a **training loop**
needs three legs (reach → spin → walk back to a Poké Center to heal), a **catch-and-leave hunt**
needs two (reach → leave). So `NO_RETURN_GROUNDS` is the wrong test for a hunt, and its own
FIERY_PATH entry says so in words — *"a fine CATCH-AND-LEAVE hunting ground … that is a
different use and must not go through this picker."* That prose is now a table the picker
queries, per `NO_RETURN_GROUNDS`' own header rule (ADD TO THE TABLE, never to a doc alone).

Sole entry today: **FIERY_PATH (18,19)** — the tile `story_harness.py lavaridge --driver
fierycave` actually walked (2026-07-26); legs 1 (Lavaridge → tile) and 2 (tile → out of the
cave) both PASS, and only leg 3 (the onward heal trip) fails, which a hunt never walks.

### The result that matters

All three measured derail classes now resolve to a **swept, walkable** destination — where
`03-PUNCH-LIST` recorded blocker (1) as *"every candidate has `tile: None`; there is nothing to
path to"*:

| Norman/Fighting | **Machop @ FIERY_PATH (18,19)** — matches the user's ruling exactly |
| Wattson/Ground | **Sandshrew @ ROUTE111 (25,55)** |
| Winona/Rock+Elec+Ice | **Electrike @ ROUTE118 (29,15)** |

Jagged Pass is the entry that proves the gate has teeth: it hosts Machop at **L20-22 vs Fiery
Path's L15-16 and ranks ABOVE it on cost** (134,702 vs 250,297 frames), so rank alone would
pick it — and it is refused, because `NO_RETURN_GROUNDS` records that it cannot even path
within itself.

### Behaviour unchanged this commit
`find_counter_candidates` still returns and still NAMES every candidate (the diagnostic message
keeps its value); non-huntable ones are just marked `NOT HUNTABLE` in `summarise_candidates`.
Nothing travels or catches yet — that is step 2.

### Correction to a load-bearing handoff claim
**This dev box DOES have mgba.** It is vendored at `sandbox-pokebot/mgba/`, so live repros run
here; `repro_counter_wiring.py` loaded a real save state and read party/flags on 2026-07-30.
`04-HANDOFF.md` said *"No mgba here — anything needing a live emulator must be validated on the
user's machine"* and *"nothing involving a live emulator has ever run here"*. Both are wrong,
and the cost was real: work was deferred to the user's machine that could have been proven here.
The "5 environmental" repros should be re-checked against this.

---

## 2026-07-30 — `#24-reprorot`: the four "environmental" repro failures were four different rots

All four were repaired; **none of them ever needed an emulator it did not have**. Every one
launched mGBA 0.10.2 successfully. They had been carried in the handoff as an expected
"5 environmental" for weeks, which is why nobody re-read the tracebacks.

| repro | real cause | fix |
|---|---|---|
| `repro_boss_training` | stub `self` never gained `_boss_plan_is_hopeless`, added to `_prepare_for_fight` by the KI-23 work | harvest all UPPERCASE constants off `StoryMode`; **bind the real method** |
| `repro_double_faint` | stub mon never gained `.level`, which `level_up.py:73` began scoring on with the KI-18 tiebreaker | add `level`; add a case that **covers the tiebreaker itself** |
| `repro_navigate_failfast` | asserted `startswith("raised BotModeError")`; code correctly raises `UnreachableDestinationError`, **a subclass** | assert on the exception TYPE via a new `_Outcome.raised_botmode()` |
| `repro_sufficiency` | **four compounding causes** — see below | fixture + stub + emulator |

### `repro_sufficiency` is the instructive one

It failed for four reasons at once, each hidden behind the next:
1. `ROXANNE`/`WATTSON` fixtures had **no `grass` key**, but the evolution lookahead's
   frame-cost gate reads `cfg["grass"]` to price the grind. Production configs always have
   it (`story_mode.py:2151`).
2. The stub mon had no **`total_exp`**, which `estimate_frames_to_level` reads.
3. The stub `self` had no **`MAX_PREP_TRAINING_FRAMES`** (nor `FODDER_LEVEL_GAP` for case F).
4. The script created **no emulator at all** — `set_rom()` alone does not let
   `get_wild_encounters_for_map` populate its cache, so `_wild_land_max` returned None and
   the gate rejected the plan as "estimated UNKNOWN frames".

‼ **Causes 2 and 3 produced no crash.** The lookahead is wrapped in `except Exception: pass`,
so a missing stub attribute degrades to a silently WRONG VERDICT. This is the *exact* failure
shape `_boss_plan_is_hopeless`' own comment warns about — *"a stand-in `self` missing a class
constant swallowed an AttributeError and disabled the whole diagnosis"* — recurring, this time
in the test harness. Every step of that lookahead passes on real data (sweep score 90 ≥ 80,
estimate 24,361 ≤ 250,000 frames); only the fixture was broken.

### The anti-rot measure (the part worth copying)

Both `story_mode` stubs are now `_StoryModeStub`, which
* harvests **every** UPPERCASE class constant instead of hand-listing a few — hand-listing is
  precisely what rotted (`TRAIN_CATCHUP_GAP` was listed; `PLATEAU_LOSS_THRESHOLD`,
  `CREDIBLE_ANSWER_POWER`, `MAX_PREP_TRAINING_FRAMES`, `FODDER_LEVEL_GAP` arrived later), and
* raises a **self-explaining `AttributeError`** naming the missing member, why it is missing,
  and whether to harvest it or bind the real method — because the bare
  `'types.SimpleNamespace' object has no attribute ...` read as scaffolding noise rather than
  "this test no longer runs".

Methods are **bound to the real implementation**, never re-stubbed: a stubbed verdict would
hard-code the answer under test, so the repro would keep passing while the real logic changed.

**Sweep result: 58 pass, 0 fail, 1 skip (59 scripts).** First fully-green suite. The "5
environmental" expectation is retired — any future failure should be treated as real.

---

## 2026-07-30 — `#24-counters` phase 2, step 2: the EXECUTOR (the chain finally ACTS)

The counter chain has diagnosed correctly and then ended the run since phase 1 — ~**72% of
all derails** in the 2026-07-29 batch. It now goes and gets the counter.

**New `modules/story/counter_hunt.py`** (execution; `counter_plan` stays pure planning, as
its own docstring requires). Three rungs, each bounded, each falling through to the SAME
terminal raise:
1. **ARM** — `COUNTER_CATCH_TARGET_DEX`, consumed by a new catch-on-sight branch in
   `on_battle_started` cloned from the `HM_CATCH_TARGET_DEX` branch (same gates: party
   room, a SPARE ball, not a shiny; **same local-`console` import**, whose absence silently
   ate two earlier branches — 08-MISTAKES 2026-07-26).
2. **HUNT** — travel to `best_huntable()`'s proven tile and spin, bounded by
   `HUNT_SPIN_BUDGET_FRAMES = 120,000` (~12 expected meetings of a 15% slot at the measured
   1,433 frames/wild-battle; for scale, run05 spent ~399,000 frames LOSING to Norman 21×).
3. **TRAIN** — `train_counter` brings the catch to within 2 levels of the team, gated by the
   same frame-cost estimate every other training entry point uses (UNKNOWN ⇒ decline).

### ‼ Why rung 3 is not optional garnish
Catch a L15 Machop for a L30 team and leave it untrained, and `_boss_plan_is_hopeless`
answers *"not hopeless"* for ever after — the party now HAS a Fighting move. Today's
bounded, honest stop would become an **unbounded loop** that only the 5M-frame run budget
ends. Nor can the ordinary prep be relied on to do it: `_prepare_for_fight` readies "the
strongest battler plus any battler already within `TRAIN_CATCHUP_GAP`", and a fresh catch is
outside that gap **by design** (`#24-team` leaves fresh catches to level organically).

### ‼ The bound is ONE HUNT PER BOSS PER RUN, and it had to be per-run state
A retry budget would not work, and neither would a frame budget: the chain fires from inside
`_prepare_for_fight`, which the run loop **re-enters after every lost attempt**, so "N tries"
silently becomes N *per attempt* — unbounded. **This is the KI-34 shape** (a bounded loop
re-entered by its dispatcher is still infinite; it burned 23.9M frames). So the bound lives
in `self._counter_hunts`, cleared by `reset_per_run_state()` — and the attempt is recorded
**before** the hunt runs, so a hunt that derails mid-flight still consumes its one chance
instead of being retried by the recovery path.

### The terminal raise is untouched
Every failure path — no huntable candidate, party full, no spare ball, planner throws, hunt
finds nothing, already hunted — returns False and the caller raises exactly as before.
Silent non-progress is worse than an honest stop.

### Proof — `tools/story-dev/repro_counter_hunt.py`, 15 checks, ALL PASS
Drives the REAL `_counter_ladder` and the REAL `on_battle_started`. The load-bearing case is
**#2: a second hopeless verdict for the same boss raises even though the hunt would succeed
again.** Also covers the derail-mid-hunt case, the per-run reset, all five fall-throughs, the
four catch-on-sight gates, and that `hunt()` disarms in its `finally` when the spin raises
(a hunt that dies armed would spend balls on Machop for the rest of the run).

‼ **NOT PROVEN — needs a live run:** that the bot can actually walk to Fiery Path from
Petalburg, catch a Machop, and beat Norman with it. What is proven is that every way this
can fail ends at the honest stop, and that it cannot loop.

**Harness note:** this repro needs a headless emulator + `norman_done.ss1` even though it
drives stubs — the battle-strategy constructors on the fall-through paths read the live
party. Without it, `StoryCatchStrategy()` raised inside `on_battle_started`'s
`except Exception: pass` and the POSITIVE case silently fell through, i.e. the branch looked
broken when it was not. Same trap as `repro_sufficiency` earlier today.

---

## 2026-07-30 — `#24-counters` step 2b: destination FALLBACK, because 2 of 3 rungs were inert

**New probe `tools/story-dev/probe_counter_reachability.py` — and it changed the design.**
It drives the REAL navigation (`_navigate_riding_out`, which crosses warps) from verified
save anchors to each boss's `best_huntable()` destination:

| rung | destination | driven navigation |
|---|---|---|
| **Norman → Fighting** | Machop @ FIERY_PATH (18,19) | ✅ **ARRIVED in 2,922 frames** |
| Wattson → Ground | Sandshrew @ ROUTE111 (25,55) | ❌ failed in 255 frames |
| Winona → Rock/Elec/Ice | Electrike @ ROUTE118 (29,15) | ❌ failed in 255 frames |

Route 111's tile is Fallarbor-side (north of the Go-Goggles desert); Route 118 is the KI-24
dual-elevation-bridge case where `region_reach` says yes at map scale and the tile planner
cannot route it. **So two of three bosses were burning their single per-run hunt on a place
the bot cannot walk to** — while a reachable second choice sat further down the ranked list
(Wattson also has **Nincada (Bug/Ground) @ ROUTE116 (11,7)**, on the corridor the story
already walks).

### The fix — walk the ranked list, bounded, with an asymmetry that matters
`counter_plan.huntable_candidates()` returns every huntable candidate in rank order, deduped
by `(map name, tile)` — the encounter index lists one row per species per map, so six
Geodude rows across six Magma Hideout floors are ONE destination. `_counter_ladder` now tries
up to `COUNTER_HUNT_MAX_DESTINATIONS = 3` of them.

‼ **Cheap failures cascade; expensive ones do not.**
* A **navigation** failure costs ~255 frames (the fail-fast guard) and is specific to one
  place ⇒ try the next destination, and record it in `_training_unreachable` so nothing
  re-walks it this run.
* **Arrived and caught nothing** already cost a full 120,000-frame spin ⇒ do NOT cascade.
  Cascading those would turn a bounded ladder into a multi-hundred-thousand-frame excursion.
* A **resource** wall (full party, no spare ball) applies to every destination ⇒ stop
  outright. This is why `hunt_blockers` was split into `resource_blocker()` (global) and
  `destination_blocker()` (per-candidate): collapsing them made "the party is full" and
  "that one tile is unreachable" indistinguishable, and the ladder must react differently.

### Also fixed on the way
`huntable_candidates` keyed its dedupe set on the **map object**. `MapRSE` members are
hashable, but a stand-in `SimpleNamespace` defines `__eq__`, which sets `__hash__` to None —
so the function vanished into its own `except` and returned `[]`, silently. Now keyed on the
map's NAME, which is unique per map and therefore the correct key as well as the safe one.

### Proof
`repro_counter_hunt.py` grows to **20 checks, ALL PASS**, adding: the fallback succeeds on
the second destination (16); all-unreachable still stops honestly and records each (17);
‼ the attempt count is capped however many are offered (18); an expensive failure does not
cascade (19); a resource wall stops the ladder outright (20).

**Expectation-setting for the next batch:** Wattson is the biggest derail class (17 of 29)
and its FIRST choice is unreachable. With the fallback it now tries Route 116 Nincada
instead of stopping — but that is an L6-7 catch for an ~L20 team, and `train_counter`'s
frame-cost gate may well decline it (est. 355,384 frames vs a 250,000 budget). **A Wattson
derail that survives this is not the executor failing**; read the log line, which says which.

---

## 2026-07-30 — Bot-mode popup: Story block and ×4 controls hoisted to the TOP (`#24-menuorder`)

**User request, verbatim intent:** *"I want all of them to be at the top of the list
including the 'Park' and end options for the x4 runs so its easier to find them (currently
I have to scroll around to activate them and end/park them)."*

**What was wrong.** The Play tab's `Bot mode ▾` popup ran: `Manual` → ~23 upstream modes →
a block of greyed-out modes → Debug Logging → Endless Debug-Reset → Endless Loop ×4 →
Park ×4. **The two controls used most often while a batch is running — park it and stop it —
were the last two entries**, below a block of things that cannot even be clicked.

**New order:**
```
Manual
─────────────
— STORY —
Story · Story (DEBUG) · Story (DEBUG - RESET) · Story (ENDLESS RESET)
Endless Debug-Reset Runs…
Endless Loop ×4…                 (reads "Stop Endless Loop ×4" while running)
Park ×4 & Collect Logs…          (greyed out when no batch is running)
─────────────
— OTHER MODES —  … then disabled modes … then Debug Logging
```

### Two decisions inside this, both aimed at "findable without looking"
1. **A Story mode that is not currently selectable stays in the Story block, greyed out**,
   instead of dropping to the disabled block at the bottom. An entry that MOVES with game
   state is the scrolling problem wearing a different hat.
2. **`Park ×4` is now always present, disabled when idle.** This REVERSES a deliberate
   2026-07-26 choice to hide it unless meaningful — hiding it changed the block's height, so
   everything below it shifted between visits. Stable layout beats a tidy one here.

`Manual` keeps first place: it is the stop button, its position is muscle memory, and it
costs one line above the Story block.

### The part worth keeping
The ordering moved OUT of the Tk callback into a pure function,
`dashboard_gui.build_mode_menu_plan()`, which returns a render plan; `_open_mode_menu` now
only walks it. Previously the only way to observe the order was to open a window and look.
Now `repro_mode_menu_order.py` (**14 checks, ALL PASS, no Tk and no emulator**) asserts it,
so it cannot silently drift back.

Story modes are found by **PREFIX**, not a hand-written list, so a future `Story (…)` mode
is hoisted the day it is added — hand-listed collections in this project have a measured
habit of rotting (`08-MISTAKES` 2026-07-30, twice in one day).

**Caught by the new test:** `Manual` is not a registered bot mode, so it is absent from the
selectability set — the first version of the plan rendered **the one entry that must always
work as greyed out**. Fixed with an explicit `always_enabled`, and both states are asserted.

**Scope:** `sandbox-pokebot` only. The classic GUI (`emulator_controls.py`, reachable only
via `--classic-gui`) is unchanged; `pokebot.py` launches the dashboard by default, and this
popup is the one the user actually sees.

---

## 2026-07-30 (evening) — Batch review `20260730-204036`: counter chain CONFIRMED WORKING; a separate, serious regression found

**Build `ffb062ce` (mine), 4 lanes, 17:29→20:40 (~3h11m), 34 runs started.** Compared against
bundle `20260730-062818`, build `21b587f1`. ‼ Both bundles contain the SAME leftover
`20260729-192928` stdout files (byte-identical) — segmented out before counting, per the
playbook's launch trap.

### ✅ `#24-counters` phase 2 — every designed behaviour confirmed LIVE
| behaviour | evidence |
|---|---|
| the ladder ACTS instead of stopping | 3 hunts started: `going to FIERY_PATH (18,19) to catch Machop`, `ROUTE111 (25,55) … Trapinch`, `ROUTE116 (11,7) … Nincada` |
| the step-2b destination FALLBACK cascades | 3× `— trying the next counter destination` |
| ‼ the per-run BOUND holds in the real re-entry path | 12× `already hunted a counter for this boss this run` — **it never re-hunted, and no boss looped** |
| resource wall stops the ladder outright | `blocked: the party is full` |
| honest terminal stop preserved | `no counter destination worked (Trapinch@ROUTE111: unreachable; …)` |
| rung 3 never reached | `training the counter` ×0 — correct, nothing was ever caught |

**The regression I most feared — a boss that used to stop honestly now looping — did not
happen.** That was `repro_counter_hunt` case 2's whole purpose and it held live.

### ✅ KI-39 confirmed live, and it is the binding constraint
Every hunt failed at navigation. All three destinations are out of range of where the ladder
fires, exactly as KI-39 predicts. The executor is correct; **it has nowhere it can walk to.**
`#24-counters` cannot pay off until `#24-journey` exists.

### ‼ SEPARATE, SERIOUS REGRESSION — runs no longer finish
| metric | old `21b587f1` (~13h) | new `ffb062ce` (~3h11m) |
|---|---|---|
| runs reaching **`finished`** | **29 of 60 run-ends (48%)** | **0 of 30** |
| `global watchdog — nothing progressed` | **5 total (~0.4/h)** | **94 total (~29.5/h)** |
| dominant run-end reason | `boss: N losses…` (22) | **`global watchdog` (23 of 30)** |

Configs are IDENTICAL (same Python 3.13.7, ROM, `speed=0 video=True audio=False`, fodder
rule `xp_rate`), so this is not environmental drift. The watchdog itself is unchanged since
`88a0e307` — it is not a newly-sensitive instrument, the wedging is real.
Wedge sites seen: `training N battler(s) to Lv 31 in ROUTE117`, and the
Rock Smash→Fallarbor→Meteor Falls chapter sequence at map (24,12).

### ‼ ATTRIBUTION IS NOT CLEAN — do not blame (or clear) my commits from this data
The two bundles are **16 commits apart**, and only 4 of them touch production code and are
mine (`5229e780`, `f74fab6c`, `31647da3`, `06807942`). The other 10 include the **KI-34,
KI-35, KI-36 and KI-37** fixes. The `21b587f1` bundle is in fact the already-reviewed
`20260730-062818` batch that PREDATES all of them. So this A/B compares
"before four KI fixes + before my work" against "after both", and cannot separate them.

**One hypothesis raised and REFUTED here:** that `_counter_ladder`'s
`_note_training_unreachable` calls poison the training-area picker (counter destinations
ROUTE111 (25,55) and ROUTE116 (11,7) are also `TRAINING_GRASS` tiles). Measured: only **2**
blacklist events came from the ladder (FIERY_PATH, ROUTE116); `ROUTE111 (25,55)` dominates in
**both** builds (14 new / 24 old) and is the training picker's own doing. Not the cause.

### ⏭ THE NEXT TEST MUST BE CONTROLLED, NOT LONGER
A second long batch on `ffb062ce` would add no information. Run **~1 hour on `d7d493d8`**
(the last build recorded as live-validated) and ~1 hour on `ffb062ce`, same lanes, and
compare **watchdog fires per hour** and **finish rate**. That isolates my 4 production
commits from the 10 that preceded them, which is the only open question.
‼ Note the recorded validation of `d7d493d8` was *"no unrecovered errors"* — it was never
checked against **finish rate**, so it may not be the clean baseline the handoff implies.

---

## 2026-07-30 — KI-38/KI-40 mitigation (A): `FAINT_CHOOSER_GIVEUP_LIMIT` 3 → 20, clamped and tunable

**This is a MITIGATION, not a fix.** The real fix is `#24-menutext` (B, next).

**What it changes.** `battle_handler.FAINT_CHOOSER_GIVEUP_LIMIT` defaults to **20** instead of
3, overridable with `POKEBOT_FAINT_GIVEUP_LIMIT`, and **clamped to `FAINT_CHOOSER_GIVEUP_MAX
= 200`**. Proof: `tools/story-dev/repro_faint_giveup_limit.py` — ALL PASS, pure, no emulator.

**Why.** Each give-up is one 6,000-frame invocation, so the limit is a frame budget in
disguise: 3 ≈ 18,000 frames, 20 ≈ 120,000 (2.4% of the 5M per-run budget). KI-34 introduced
the limit to bound a genuinely unbounded re-entry, and that was right — but 3 is far too tight
for a chooser that still mis-selects, and **giving up abandons an ACTIVE battle**: the party
menu is left open, the mode gets a fault its recovery cannot act on, and the run wedges.
Measured (KI-40):

| build | limit | index bug | watchdog/h | runs finished |
|---|---|---|---|---|
| `21b587f1` | none | present | 0.4 | **48%** |
| `d7d493d8` | 3 | fixed | ~20 | 0 of 2 |
| `ffb062ce` | 3 | fixed | ~29 | 0 of 30 |

The pre-fix livelock measured ~35 re-entries in one battle, so 20 restores most of that
tolerance while still terminating. KI-34's index-space fix is untouched and is what should
make the extra attempts more likely to land than they were before.

‼ **Unbounded is NOT an option, and the reason is easy to forget:** KI-36 — the per-run frame
budget is a GENERATOR WRAPPER that cannot fire while a battle handler sits on the flat
controller stack. An unbounded chooser is therefore bounded only by `debug_logger`'s
60,000-frame stall net, which exists only while debug logging is ON.

### The clamp exists because the test caught a real hole
The first version validated the env var (`>= 1`) but did not bound it, so
`POKEBOT_FAINT_GIVEUP_LIMIT=99999999999999999999` — one fat-fingered env var on the batch
machine — produced an effectively unbounded chooser and **silently reintroduced the exact
KI-36 hazard the finite limit exists to prevent.** `repro_faint_giveup_limit.py` case 4 caught
it before it shipped. The case now asserts *clamped*, not merely *no exception*.

### What to watch on the next batch
`GAVE UP` should still appear (the chooser is still wrong — that is KI-38), but
`battle handler gave up` (the hand-over) and `global watchdog` should drop sharply, and runs
should start reaching `finished` again. **If the finish rate recovers, that is the mitigation
working, NOT the bug being fixed.** Do not let it close KI-38.

**Also in this commit — `#24-menutext` groundwork (start of fix B).** The `GAVE UP` log line
now records the live `gDisplayedStringBattle` and `gStringVar4`, tagged `[#24-menutext]`.
Diagnostic only (wrapped, never branched on), so it cannot change battle behaviour — the same
move that cracked the move-learn hang (ML-11: *"read what the game ACTUALLY says"*). Indices
cannot diagnose this because the indices are the thing in doubt. **The next batch's logs
should therefore show what the screen said at each failure**, which is what makes the real
text-driven chooser buildable.

Action-menu strings fetched and verified from the decomp (`src/strings.c`, 2026-07-30) and
recorded in `03-PUNCH-LIST` so they are never re-derived or written from memory:
`SEND OUT` (`gText_SendOut`), `SHIFT`, `SWITCH`, `SUMMARY`, `CANCEL`, `ENTER`, and
`Do what with this {PKMN}?` (`gText_DoWhatWithPokemon`, shown when the ACTION menu is open).

**Fixed a brittle assertion the change exposed:** `repro_faint_chooser_index_space.py` asserted
`FAINT_CHOOSER_GIVEUP_LIMIT == 3` and went red for a deliberate, correct retune. It now asserts
the INVARIANT — the limit exists, is finite (KI-36) and is greater than the old too-tight 3.
Same brittleness class as `repro_navigate_failfast`'s string assertion, fixed the same day.

**Sweep: 61 pass, 0 fail, 1 skip.**

---

## 2026-07-31 — ‼ KI-38 FIXED: the after-faint chooser now LEARNS what the game refuses

**Measured on this box, 12 runs before / 4 runs after, same harness, same settings:**

| batch | build | runs | **hangs at `BattleScript_FaintedMonTryChoose`** | whiteouts |
|---|---|---|---|---|
| A | `77c404d5` (mitigation only) | 12 | **12 of 12** (11 at the chooser, 1 at `LocalBattleLostEnd`) | 0–9 |
| B | + this fix | 4 | **0 of 4** | 1–5 |

All four batch-B runs used their full frame budget and ended `INCOMPLETE` — they ran OUT OF
FRAMES rather than getting stuck — and whiteouts now appear, meaning battles are lost and
**recovered** instead of deadlocking.

### The bug, exactly
In the chooser loop, `A` was pressed whenever `cursor in alive_slots_menu` and `Down` **only**
when it was not. So when the game REFUSED a selection, the cursor never moved: the refusal
re-armed `Task_PrintAndWaitForText`, we dismissed it, landed on the same slot, pressed A
again — for ever. That is precisely KI-38's recorded signature (`presses={'Down': 3, 'A':
273}` with a near-static cursor), and it is why raising the give-up limit could not help.

### The fix: make the model a HINT and give the game the vote
* Press A, and if we are **still in the party menu with the printer re-armed**, that slot is
  refused. Detected STRUCTURALLY, not by matching the refusal string — so it needs no decomp
  lookup and cannot break when text changes.
* Candidates = `alive_slots_menu - refused`. **If that empties, the MODEL is wrong rather than
  the party being unusable**, so it falls back to every not-yet-refused slot.
* ‼ **It terminates:** every A-press either leaves the menu (done) or eliminates one slot for
  good, and there are at most six plus CANCEL.

**Why not correct the index model a third time.** It has already been wrong twice in two
different ways — KI-18's on-field filter, then KI-34's index space. A third correction would
be another guess against a model we keep mis-deriving. Refusal is *observable*; the index
space is inferred. Prefer the observable one.

### Also
`repro_faint_chooser_index_space.py` asserted the literal `cursor in alive_slots_menu` and
went red on correct code — the **third** name/string-anchored assertion to do so in two days.
It now asserts the invariant (both branches compare against a MENU-ORDER set) plus the new
termination guarantee (a refusal is recorded; the model's set falling empty triggers the
all-slots fallback).

**Sweep: 61 pass, 0 fail, 1 skip.**

---

## 2026-07-31 — Batch C (8 runs, build `1099e9d9`): KI-38 fix CONFIRMED; the run-killer is now the counter chain

| batch | build | runs | FRONTIER | hangs | dominant hang signature |
|---|---|---|---|---|---|
| A | `77c404d5` | 12 | **0** | 12 | `BattleScript_FaintedMonTryChoose` (11 of 12) |
| C | `1099e9d9` | 8 | **1** | 6 | `BattleScript_LocalBattleLostEnd`, `ctrl=<none>` (5 of 6) |

**KI-38: 11/12 → 1/8.** Runs go far deeper — 648-1,922 battles and 12-24 whiteouts each, versus
20-1,116 and 0-9 in batch A. Battles are now lost and RECOVERED instead of deadlocking.

### ‼ CORRECTION — the `LocalBattleLostEnd` hang is NOT a whiteout bug
It was reported as one mid-batch, on the state trace alone. It is the **aftermath** of the
mode having already exited. The stdout shows the real cause:
```
*** BotModeError -> Manual: this boss: 6 losses with no super-effective answer to
    Normal. Need one of: Fighting.                                        x3
*** BotModeError -> Manual: Winona: ... Need one of: Rock, Ice, Dragon.   x1
```
`ctrl=<none>` + `bot_mode=Manual` + `bt='NICK whited out!'` is simply "no controller is
driving the game any more". **A state trace shows where the bot IS, never why it got there —
the stdout error line is what names the cause.** (Same shape as `08-MISTAKES` 2026-07-30's
"probed with the wrong tool": a downstream symptom read as a root cause.)

### What this means
The chain of blockers is now fully ordered by evidence:
1. ~~KI-38 after-faint chooser~~ **FIXED**.
2. **The counter chain ends the run** — `#24-counters`, the ~72%-of-derails item, now the
   measured killer on a build where nothing deadlocks before it.
3. **It cannot act because of KI-39** — no cross-map journey planning, so the named counter
   (Machop @ FIERY_PATH (18,19), correctly identified as huntable) is out of navigational
   reach from where the ladder fires.
⇒ **`#24-journey` is now the highest-value item in the project.** It unblocks the thing that
is killing runs, and it is the same capability the user asked for ("map to already traveled
locations").

### Measurement caveat
`livetest` drives plain `Story`, where a `BotModeError` drops to Manual and the run ends. The
user's `ENDLESS RESET` starts a fresh run instead. **So this 1/8 frontier rate is a HARSHER
measurement than the user's batches** and the two finish rates are not directly comparable.

---

## 2026-07-31 — `tools/story-dev/x4_headless.py`: headless ENDLESS-RESET batch runner (`#24-x4headless`)

**What.** A batch runner that drives N parallel lanes of the *user's actual mode* —
`Story (ENDLESS RESET)`, headless — instead of plain `Story`. One lane is literally
`python pokebot.py <profile> -m "Story (ENDLESS RESET)" -s 0 -na -hl --endless-target N`.

**Why it was needed.** `livetest.py` drives **plain `Story`**, where a `BotModeError` reaches
`main_loop`, drops to Manual and ENDS the run. The user's batches run `ENDLESS RESET`, which
swallows that error and starts a fresh run. Every finish-rate number livetest has produced is
therefore HARSHER than the user's, and the two were never directly comparable. Now they are.

**Lane split.** `LANE_STARTERS` modulo-cycled, so one table yields both shapes the user asked
for: 4 lanes = the dashboard's `torchic/mudkip/treecko/random`; 8 lanes = **2 per starter +
2 random**, doubling every starter's sample. That doubling is the point — `#24-starter-gym3`
(Treecko stalls at Wattson in 11 of 14 runs, Mudkip never does) is starter-specific, and one
lane per starter is too thin to separate that from noise.

**The emulation assertion (the headline feature).** Speed/video were *verified, not
re-engineered*: `-s 0` → `PokebotHeadless` sets `emulation_speed = 0`; `-hl` without `-nv`
sets `context.video = True` (headless removes the GUI **window**, not the **renderer**, so
the faithful PokéNav path is fine); and `StoryEndlessResetMode.run()` calls
`_apply_debug_emulation_config()`, which forces both and re-pins the speed after every
`set_manual_mode()`. **The runner then CHECKS it** — every run writes a fresh debug log whose
RUN HEADER carries `emulation: speed=… video=…`, and the runner asserts `speed=0 video=True`
on every header for the whole batch, not just the first, because the failure being guarded is
exactly *"run 1 was fine and run 2 crawled at 1x"*. A violation aborts the batch loudly
(`--on-bad-header warn` to downgrade): a lane silently at 1x is ~20x slower and, from the
outside, looks exactly like a hang.
**Empirically confirmed** on a 2-lane 4-minute smoke batch: both lanes reported
`speed=0 video=True`, throughput **~1,211 fps/lane** (matches the documented ~1,250).

**Storage.** `tools/story-dev/x4-runs/<stamp>/` with `MANIFEST.txt`, `summary.json`, per-lane
`stdout.txt` + the debug logs from THIS window only (a profile's `debug-logs/` is cumulative
and never archived — copying it wholesale folds months-old runs into a fresh batch's numbers).
`INDEX.md` + `LATEST.txt` at the root, and **every row records the COMMIT HASH**, so a review
can never compare a batch to code it did not run.

**Two traps handled.** (1) rich wraps a lane's stdout at ~78 columns when it is a file,
physically splitting the `=== ENDLESS RESET: run N -> … ===` lines a summarizer parses —
verified in the user's own `P1-stdout-20260726-233837.txt`; lanes launch with `COLUMNS=400`.
(2) N lanes all bind HTTP :8888 and dump thread tracebacks into the logs; each lane profile
gets `http.yml` with `enable: false`.

**Metrics it reports** (per lane and batch-wide): finish rate on the *pessimistic* rule (only
the literal `finished` counts), **grouped end-reasons** (numbers normalised, so 27 Norman
derails that differ only in loss count collapse to one cause), the KI-38 canaries
(`GAVE UP` **and** `NO ELIGIBLE REPLACEMENT` — 0 for the latter is what proves a valid target
always existed), the KI-40 watchdog count, STUCK dumps + the battle script each wedged on,
battle-outcome tally + flee rate, whiteouts, losses by map, badges.

**Repro:** `tools/story-dev/repro_x4_headless.py` — 55 checks, no emulator.

## 2026-07-31 — fix: `--endless-target` was parsed and then discarded by every frontend but the tile lane

**Symptom (would have been).** A headless lane launched with `--endless-target 0` ("run
forever") would quietly stop after **10** runs.

**Cause.** `pokebot.py` applied `ENDLESS_RESET_TARGET` *inside* the `if startup_settings.
tile_shm:` branch, so only the GUI x4 tile frontend honoured it. Headless and both GUIs parsed
the flag and threw it away.

**Fix.** Extracted `apply_endless_target()` to module level and called it once, before the
frontend dispatch. Also makes the behaviour testable without booting an emulator.

**Proof.** Fault-injected A/B in `repro_x4_headless.py` §E: the same AST checker is run
against the pre-fix source recovered via `git show HEAD:…` and against the working tree; the
verdict flips from *"all 1 application(s) are inside an `if …tile_shm…` branch"* to *"2 of 2
application(s) reachable by every frontend"*. Plus three direct calls of the extracted helper.

Repro sweep after both changes: **62 pass, 0 fail, 1 skip** (`repro_x4_lanes`, by design).

## 2026-07-31 — `#24-journey` / KI-39: warp planning at MAP granularity (the real fix)

**First, a correction.** KI-39 and the handoff both said the bot *"has NO cross-map overworld
route planning"* because *"`calculate_path` only spans directly-connected maps"*. Measured
live, that is false: `map_path.py` gives every edge-connected map a global offset and a shared
`level` (Mauville and Routes 110/111/112/116/117 are all level 459), and partial reachability
proves it was trying and failing at TILE level — ROUTE110 **17/125** tiles reachable, ROUTE111
**11/173**, ROUTE117 **22/41**, VERDANTURF **14/23**. A planner that could not cross maps
would score 0. The four blocked trips had four different causes; only one was route planning.

**The genuine bug.** `WarpGraph.plan()` answers at REGION granularity, and a region is the
union-find collapse of map connections. The whole Hoenn overworld is region 0, so `plan()`
returned `[]` ("no warps needed") for every overworld to overworld trip and the warp planner
was never consulted. The proof case: VERDANTURF declares a North map CONNECTION to ROUTE116
(so they are one region), yet **0 of 40 sampled ROUTE116 tiles are walkable from Verdanturf**
while the RUSTURF_TUNNEL door at VERDANTURF (8,1) is. The declared connection is a phantom;
the only passable link is a **warp inside one region**, which `plan()` cannot express.

**What shipped**
* `WarpGraph` now KEEPS the map-level connection adjacency instead of discarding it into the
  union-find. `CACHE_VERSION` 1 to 2 so stale caches rebuild; a cache without `connections` is
  rejected rather than loaded degraded (it would revert the fix on the second launch and look
  like flakiness).
* `WarpGraph.warp_candidates(from, to, limit)` — BFS over maps with state
  `(map, has_used_a_warp)`, returning the first warp of the shortest **warp-using** route,
  then of the shortest route not using that warp, and so on. The "at least one warp"
  requirement is the point: the caller only asks after `calculate_path` has already refused
  the direct walk, so a warp-free route is one the live world has just refuted.
* `WarpGraph.map_distance()` plus a **progress filter** so dead-end interiors are not offered.
* `navigate_to_anywhere`: (1) ask `calculate_path` whether a plain walk works — unchanged
  fast path if yes; (2) otherwise take warp candidates, **validate each first leg with
  `calculate_path` before committing**, and remember warps already taken so a re-plan cannot
  ping-pong; (3) if nothing validates, fall back to today's exact behaviour so a cross-region
  journey that works now cannot start failing.
* Also fixed in the same change: `navigate_to_anywhere`'s "did the warp fire?" check compared
  **regions**. A same-region warp — precisely the class this makes plannable — leaves the
  region unchanged, so a *working* warp would have reported "Warp at ... did not trigger
  (locked or event-gated?)". It compares maps now (with a coordinate fallback for in-map
  stairs).
* `story_harness.py --driver journey` — a faithful-harness driver for the A/B.

**Proof.** `repro_journey_planner.py` (27 checks, no emulator) pins the topology and both
traps. `probe_journey_live.py` is the live fault-injected A/B in the faithful harness:
**OLD arm `arrived=False map=MAUVILLE_CITY`** (never left the starting map) vs **NEW arm
`arrived=True map=ROUTE116` in 33,725 frames**, walking Mauville to Route 117 to Verdanturf to
Rusturf Tunnel to Route 116. Control (`Mauville to ROUTE117 (31,16)`, always walkable) still
takes the unchanged fast path. Sweep: **63 pass, 0 fail, 1 skip**.

**What it does NOT fix.** The handoff claimed this unblocks the run-killer. It does not.
Measured after the fix, FIERY_PATH (the counter the ladder names) DOES get a warp route — 2
candidates, both ROUTE112 doors — and **neither first leg is walkable**, because a Rock Smash
rock seals the corridor. That is now **KI-41**, and it is the real blocker for `#24-counters`.

## 2026-07-31 — KI-41 logged: a Rock Smash rock, not route planning, is what hides Fiery Path

Column-by-column reachability on ROUTE111 from Mauville puts a hard floor at **y around
100-101** across columns 17-20 — the twin-rocks choke that
`early_game.travel_lavaridge_to_petalburg` already documents at **(18,101)**, and which
**respawns on map reload**. Consequence: ROUTE112 is **0/76** reachable from Mauville, and
Fiery Path's only two doors are on Route 112. The story only gets past it because two travel
functions hand-code a `_smash_rock` at that exact coordinate; nothing generic does. Full
write-up plus shape of the fix in `05-KNOWN-ISSUES.md` KI-41.

## 2026-07-31 — `#24-smashroute` / KI-41: clear a field-move obstacle that seals a journey

**The bot can now reach Fiery Path from Mauville, which is where the counter chain's answer
lives.** Live A/B, `story_harness.py --driver smashroute`, save `rocksmash_taught.ss1`:

| arm | result |
|---|---|
| OLD (obstacle clearing disabled) | `arrived=False map=MAUVILLE_CITY` — never left the starting map |
| **NEW** | **`arrived=True map=FIERY_PATH`, 45,305 frames** — walks the corridor, smashes the rock at ROUTE111 (18,101), arrives |

**Why this was the real blocker.** `#24-journey` made warp routes to Fiery Path plannable and
it still could not go: both candidate first legs are on ROUTE112, and ROUTE112 scores **0 of
76** sampled tiles reachable from Mauville because a Rock Smash rock seals the corridor at
ROUTE111 (18,101). Fiery Path's Machop is the counter the `#24-counters` ladder names for
Norman, so this is what has been ending runs.

**It is general, not a table.** Probed rather than assumed
(`tools/story-dev/probe_smash_choke.py`): the obstacles are ordinary object events carrying
`EventScript_RockSmash`, and `map_path` tags exactly those tiles with a
`dynamic_collision_flag`. So `modules/story/obstacle_clearing.py` reads the ROM's own object
events per map — no hand-maintained coordinate list to rot. Symbol names were COUNTED off the
ROM, never recalled: `EventScript_StrengthBoulder` 59 objects, `EventScript_RockSmash` 44,
`EventScript_CutTree` 33.

**What is actionable, and what deliberately is not.** Only Rock Smash. Cut is recorded as
known-but-never-validated (the mechanism matches — the object is removed — but it has not been
driven end to end, and a wrong YES costs a long walk to nowhere). **Strength is excluded on
purpose and must not be added without new clearing code:** a boulder is PUSHED, not destroyed,
so the "the object is gone" success test can never fire — it would burn its attempt budget and
report failure on a push that worked.

**Gates, all checked rather than assumed.** An obstacle only qualifies if its script is known,
the party knows the move AND the player holds the badge, and an orthogonally adjacent tile is
reachable RIGHT NOW (`calculate_path` from the live position — the same oracle `navigate_to`
uses). The approach and facing are derived, not hard-coded: the finder returns stand (18,102)
facing Up for northbound travel, the mirror image of the (18,100)/Down that
`early_game.travel_lavaridge_to_petalburg` hard-codes for its southbound leg.

**Hook.** `early_game._navigate_riding_out`, in its `except BotModeError` handler and
**before its fail-fast guard**. That ordering is the point: the guard is right that "the field
is idle and we have not moved, so retrying cannot change the result" — but smashing the rock
CHANGES THE WORLD, which is exactly the premise it tests. On a successful clearance the
"where we failed from" memory is reset so the guard does not misfire on the next try.

**‼ A bug this introduced and the sweep caught.** `clear_obstacle` delegates to
`_smash_rock`, which calls `_navigate_riding_out` to walk to the approach tile — i.e. a
clearance runs THROUGH the function that starts clearances. Any failure of that short walk
found the same rock again and recursed, each level with a fresh `cleared_obstacles` set: *a
bounded loop re-entered by its dispatcher is still infinite* (KI-34, 23.9M frames). It shipped
for about twenty minutes and was caught only because `repro_smashrock_battle_wedge.py` went
from sub-90s to over 500s. Fixed with a re-entrancy guard released in a `finally`.

**Proof.** `repro_obstacle_clearing.py` (24 checks, no emulator) — table honesty, the derived
approach/facing, both wrong-YES arms, and the re-entrancy guard including its release on an
exception. Plus the live A/B above. Sweep: **64 pass, 0 fail, 1 skip**.

## 2026-07-31 — `#24-smashroute` follow-up: don't freeze the emulator re-searching, and KI-42 logged

**Fix.** The obstacle search in `_navigate_riding_out` is SYNCHRONOUS — it runs several
`calculate_path` calls without yielding, so the emulator is frozen for its duration. It was
re-running on every one of the 10 retries, which on a failing navigation meant seconds of
frozen emulator per attempt. A frozen emulator is indistinguishable from a hang in a log, so
this mattered beyond speed. One empty answer is now final for the trip (riding out a scene
cannot create new rocks). Re-verified live afterwards: `arrived=True map=FIERY_PATH`.
Sweep: 64 pass, 0 fail, 1 skip.

**KI-42 logged.** Measured with the oracle the gate actually calls: FIERY_PATH is **8 hops**
from PETALBURG_CITY and `COUNTER_MAX_HOPS` is **8** — the whole Norman counter chain sits
exactly on its own limit, with zero margin, and one extra hop would filter it out **silently**
(the KI-24 shape: a false negative with no reason attached). Do not just raise the constant —
it was raised 4 to 8 on measurement, and the bound is what stops the cost model ranking
Victory Road's Hariyama first. The cheap mitigation is to LOG distance rejections.

## 2026-07-31 — KI-42 mitigation: the counter gate now SAYS why it rejected a candidate

`_counter_area_allowed` returned a bare False when a map was too far, so a rejection was
invisible: `best_huntable()` returned nothing and the ladder printed the generic "no huntable
counter candidate". With FIERY_PATH sitting at exactly 8 hops against a limit of 8, that
silent path was one map-graph hop away from swallowing the whole Norman counter chain. It now
prints and debug-logs `why_unreachable`'s reason, which already separates "reachable but N
hops away (limit M)" from "no path" and from "needs Surf". The diagnostic is wrapped so it
can never change the verdict. Sweep: 64 pass, 0 fail, 1 skip.

## 2026-07-31 — ‼ TWO BUGS IN MY OWN MEASURING INSTRUMENT, and the corrected baseline

The first 8-lane batch (`20260731-105549`, commit `289d1710`, 180 min) reported **69% finish
rate** and showed the counter chain **zero times** in `end_reasons`. Both were wrong, and the
raw logs were fine the whole time — only the reading of them was broken.

**Bug 1 — the wrap mitigation was not enough, and the repro pinned it as a feature.**
`COLUMNS=400` was set specifically to stop rich wrapping the run-outcome lines. A
counter-chain derail message is ~1,000 characters (it lists every candidate counter with map,
tile, level band and rate), so it wrapped anyway and the `(N frames) ===` tail landed on the
next line. `_RUN_END_RE` matched 1 of 7 outcomes on one lane. Worse, `repro_x4_headless.py`
contained a check asserting that a wrapped line *is unparseable* — I had encoded the
WORKAROUND as the intended behaviour, so the suite actively defended the bug. `_RUN_END_RE`
is now `re.DOTALL` with a bounded gap (so a truncated record cannot swallow the next one),
`COLUMNS` is 20000, and the repro asserts wrapped records parse.

**Bug 2 — cross-lane aggregation silently overwrote.** Batch totals used
`Counter({k: v for lane in lanes for k, v in lane.items()})`. The inner **dict comprehension**
dedupes keys, so a reason appearing in several lanes kept only the LAST lane's count. It
reported 9 end reasons for 29 non-finishing runs. Nothing looked wrong — the counts were all
plausible — and only the arithmetic failing to add up exposed it. Now a named
`_merge_end_reasons()` that accumulates, with a repro asserting a shared reason SUMS.

**`--resummarise` added.** The logs are the data; the summary is a reading of them. A parser
bug is re-read from stored logs, never re-measured — re-running three hours of emulation would
also produce a different sample and destroy the comparison being attempted.

### The corrected baseline (commit `289d1710`, 8 lanes, 180 min, 46 runs started)
| metric | value |
|---|---|
| runs ended | 38 |
| finished | 9 (**23.7%**) |
| **counter chain naming an answer it cannot reach** | **25 of 29 non-finishes (86%)** |
| — Norman (needs Fighting) | 15 |
| — Winona (needs Rock/Ice/Dragon) | 5 |
| — Wattson (needs Ground) | 5 |
| everything else | 4 (one each: cutscene, Surf-learner party full, no balls for a Surf learner, watchdog) |
| KI-38 `GAVE UP` | 20, with `NO ELIGIBLE REPLACEMENT` = 1 |

This **confirms the handoff's claim** ("~72% of derails are the counter chain") and sharpens
it to 86%, measured on a build where nothing deadlocks first. It is the control the post-fix
batch will be compared against.

## 2026-07-31 — `#24-journey` part 2: STAGED PROGRESS, because one warp at a time was not general

**Found by the post-fix batch, not by a test.** The batch showed the counter hunt FIRING for
the first time — `counter hunt — going to FIERY_PATH (18, 19) to catch Machop` appeared 4
times in the first 8 runs, where the baseline had it zero times — and then failing to travel:

```
Could not find a path from (20/17 @ PETALBURG_CITY) to (11/36 @ ROUTE112)
Story: no counter destination worked (Machop@FIERY_PATH: unreachable) — stopping honestly.
```

**Why every earlier test missed it.** `#24-journey` and `#24-smashroute` were both proven from
`rocksmash_taught.ss1` — standing in **MAUVILLE_CITY**, one map from the obstacle. The Norman
ladder does not fire there; it fires at **PETALBURG_CITY**. Measured from Petalburg:

| map | walkable from Petalburg |
|---|---|
| ROUTE104 | 31/200 tiles |
| PETALBURG_WOODS | **0/132** |
| RUSTBORO_CITY | **0/150** |
| ROUTE116 | **0/125** |

`PETALBURG_WOODS` is a separate map entered by a warp and it **splits Route 104 in two** — a
fact the ROM's map headers do not encode, since they describe ROUTE104 as one connected map.
So `warp_candidates` returned only the two ROUTE112 doors (the graph believes the whole
journey needs exactly one warp), both were behind that split, neither validated, and the
executor had nothing to do.

**The fix — `_staged_progress_warp`.** When nothing on a route to the goal is reachable, take
any reachable warp that does not INCREASE the map-graph distance to the target, then re-plan.
Both ranking rules were measured from Petalburg, not guessed:
* **distance must not increase** — every Petalburg house/gym/mart door is 9 hops from Fiery
  Path against the current 8, so this rule alone excludes all of them; the Woods entrance is 8
  and is kept;
* **more onward exits wins ties** — the Woods entrance and Mr Briney's front door are BOTH
  exactly 8, so distance cannot separate "the way onward" from "a one-room house". Exit count
  can.
Candidates are drawn from the current map and its directly-connected maps (the useful door
from Petalburg is on ROUTE104, not in the city) and each is validated with `calculate_path`;
validations are capped, because the search is synchronous and the emulator is frozen during it.

‼ **This is not the refuted "gateway waypoints" idea** (KI-39, 2026-07-30). That one
hand-picked a gateway and routed to it with `navigate_to_anywhere`, which took the same broken
same-region branch and failed identically — it could not have worked. These waypoints are
derived from the graph, ranked by measured distance, and validated before use.

**Also: `counter_hunt` now passes `tries=24`** to `_navigate_riding_out` (default 10). A
counter hunt is the longest journey the bot makes, and staged progress spends one try per leg
that ends in a recoverable error — so a budget of 10 was being exhausted **while the bot was
still advancing**. The retry count is not what protects against a hopeless loop; the fail-fast
guard is (it bails the moment the field is idle AND the position has not changed).

**Corrected in `06-DECISIONS-LOG.md`:** this morning I explicitly rejected building the
leg-list planner KI-39 sketched, reasoning that "the executor already re-plans after every
warp". That is only true once the FIRST warp is reachable. The rejection is annotated in place
rather than left to mislead the next session.

### ‼ HONEST STATUS: the long journey is IMPROVED, NOT FINISHED
Measured from `norman_done.ss1` (PETALBURG_CITY), target FIERY_PATH (18,19), production path
(`_navigate_riding_out`, the call `counter_hunt.hunt()` makes):

| build | result |
|---|---|
| before staged progress | **no progress at all** — dies in Petalburg, "Could not find a path … to (11/36 @ ROUTE112)" |
| with staged progress, `tries=10` | reaches **ROUTE116** (crosses the Petalburg Woods split, Rustboro, Route 116) |
| with staged progress, `tries=24` | reaches **ROUTE116** — *identical*, so the retry budget was never the limit |

**The remaining blocker, with evidence.** All 24 tries fail with
`The game is currently not in the overworld. Cannot navigate.` — `walking.navigate_to`'s
entry guard (`modules/modes/util/walking.py:175`). The harness heartbeat at the failure shows
`ctrl=SmashRouteMode.run state=BATTLE_STARTING`, and the surrounding log is a run of wild
encounters on Route 116 grass resolving as `BattleOutcome.RanAway`. So the bot is being asked
to navigate during the **BATTLE_STARTING transition**, not while genuinely stuck.

**Two things that follow, for whoever picks this up:**
1. `navigate_to_anywhere` waits for `GameState.OVERWORLD` at the top of its loop, so a guard
   firing at `navigate_to`'s ENTRY means the state changed between that wait and the call, or
   a `navigate_to` is being reached by a path that does not wait. Find which — do not add
   another retry.
2. ‼ **A transient "not in the overworld" must not consume a try.** `_navigate_riding_out`
   counts it the same as a real plan failure, and its fail-fast guard cannot help because that
   guard only records a position when the avatar is CONTROLLABLE — which it is not mid-battle.
   So 24 tries burned on a condition that resolves by itself in a few frames.

## 2026-07-31 — `#24-journey` part 3: never call `navigate_to` during a battle transition

**The bug.** From `norman_done.ss1` the journey reached ROUTE116 and then failed **24 times in
a row** with `The game is currently not in the overworld. Cannot navigate.` —
`walking.navigate_to`'s entry guard. The harness heartbeat at the failure read
`ctrl=SmashRouteMode.run state=BATTLE_STARTING`, in a run of wild encounters on Route 116
grass resolving as `RanAway`. The bot was never stuck; it was being asked to navigate DURING a
battle transition, a condition that clears itself in a few frames.

`navigate_to_anywhere` waits for `GameState.OVERWORLD` at the top of its loop, but not every
`navigate_to` below that is reached without yielding first — the "step off the warp tile and
walk back on" fork presses directional buttons for up to 80 frames, and an encounter starting
in that window lands squarely on the next call. A transient was being reported as a routing
failure, and `_navigate_riding_out` spent a whole retry on each one. Its fail-fast guard could
not help either: that guard only records a position while the avatar is CONTROLLABLE, which it
is not mid-battle — so it never fired and all 24 tries burned. Raising `tries` 10 -> 24 had
changed nothing, which is what proved the retry budget was never the limit.

**Fix.** `_navigate_when_ready()` waits (bounded by the same generous cap the loop already
uses) for the overworld AND a controllable avatar before delegating to `navigate_to`. All four
call sites inside `navigate_to_anywhere` go through it.

**Confirmed by the failure MOVING.** Same save, same target, after the fix the transition error
is gone entirely — the bot walks to **ROUTE116 (47,9)**, one tile from the Rusturf Tunnel door
at (47,8). Progress across the three parts: zero -> ROUTE116 -> ROUTE116 (47,9), beside the door.

### ‼ WHERE IT STANDS, AND THE ANCHOR TO RESUME FROM
`tools/story-dev/saves/journey_r116_wedge.ss1` — **verified** ROUTE116 (47,9), OVERWORLD,
controllable. Probed from that exact save, the planner is CORRECT:
* `map_distance(ROUTE116 -> FIERY_PATH)` = 6
* `warp_candidates` = the two ROUTE112 doors, neither walkable (expected — still behind the
  Route 111 rock from this side)
* **`_staged_progress_warp` returns `ROUTE116 (47,8) -> RUSTURF_TUNNEL`, and (47,8) IS walkable
  from (47,9).** The right move is available and correctly identified.

So the planner is NOT the remaining problem, and the next session must not re-derive it. The
open question is why the live run did not take that move. Leading hypothesis, **explicitly not
proven**: `used_warps` persists across iterations within one `navigate_to_anywhere` call, so if
the tunnel door was already taken earlier in the same call (into RUSTURF_TUNNEL, whose middle
is sealed by the Wanda-quest rocks, then back out) it is excluded on the second pass and the
executor falls through to the unvalidated `region_route[0]`. **Instrument which branch is taken
and what `used_warps` holds — do not guess.**

## 2026-07-31 — `#24-journey` part 4: the ROUTE116 ↔ RUSTURF_TUNNEL ping-pong, and an open question that matters more

**Found by INSTRUMENTING, after two wrong hypotheses.** I guessed twice at why the journey
stalled at ROUTE116 (47,9) — first `used_warps` exhaustion, then my own `_walk_is_possible`
fail-safe firing. Both were wrong and both were cheap to disprove; a temporary trace of the
branch taken settled it in one run:

```
[TRACE] at=ROUTE116        target=FIERY_PATH ...
[TRACE] at=RUSTURF_TUNNEL  target=FIERY_PATH ...
[TRACE] at=ROUTE116        target=FIERY_PATH ...
[TRACE] at=RUSTURF_TUNNEL  target=FIERY_PATH ...
```

The executor was **ping-ponging** ROUTE116 → RUSTURF_TUNNEL → ROUTE116 → … `used_warps` could
not stop it because **the tunnel has three separate doors**, so the trip back out is a
different edge every time. This is the playbook's "chain walker loops between floors —
within-floor reachability is DIRECTIONAL" wearing a new costume.

**Fix.** `navigate_to_anywhere` now tracks `visited_maps` for the journey, and
`_staged_progress_warp` DEPRIORITISES a warp whose destination we have already stood on.
Deprioritised, not excluded: a legitimate route can revisit a map (out of a cave and back in
by another mouth), so a visited destination is still allowed as a last resort — it just never
beats an unexplored one.

### ‼ THE OPEN QUESTION, AND IT IS BIGGER THAN THE EXECUTOR
The ping-pong fix did **not** change the outcome: from `journey_r116_wedge.ss1` the bot still
ends at ROUTE116 (47,9). Before debugging the executor any further, **answer this first**:

> **Is FIERY_PATH reachable from PETALBURG_CITY at all, in that save?**

Two hypotheses, and they need opposite work:
1. **It is reachable and the executor is still wrong.** `early_game.travel_lavaridge_to_petalburg`
   documents the Rusturf Tunnel as passable through — *"the tunnel legs ride
   `_enter_warp_by_navigation` and the interior needs no boulder removal for the
   through-path"*. If that holds here, the executor is failing to cross an interior that the
   story's hand-coded leg crosses fine, and the answer is probably in how the tunnel interior
   paths (rocks are dynamic obstacles `calculate_path` treats as walls).
2. **It is NOT reachable, and the counter chain should never have proposed it.**
   `region_reach` said "reachable, 8 hops" — but it is a pure connectivity+gates graph and
   **cannot see a Rock Smash rock or a sealed tunnel**. If the route is genuinely blocked,
   then the bot walking from Petalburg to Route 116 and stopping is a **wrong YES from the
   reachability oracle** — the exact KI-24b class this project has already paid for twice, and
   far more expensive here because the wrong answer costs a 45-minute walk before it fails.

**How to discriminate, cheaply:** load `journey_r116_wedge.ss1`, walk INTO Rusturf Tunnel by
hand (or with `_enter_warp_by_navigation`), and ask `calculate_path` from the arrival tile to
the tunnel's far-side exit. If it paths, hypothesis 1 and the bug is in the executor. If it
does not, hypothesis 2 — and the fix belongs in the counter planner, which should price a
destination's reachability with something that knows about field-move seals rather than pure
graph connectivity.

‼ **Do not skip this step and keep tuning the executor.** Every hour spent on the executor is
wasted if the destination was never reachable.

## 2026-07-31 — #24-journey part 5: SOLVED. The bot walks back out the door it came in.

**The open question from part 4 is answered, and the answer was hypothesis 1.** Probed from
the anchor save: inside RUSTURF_TUNNEL, calculate_path (4,10) -> (29,16) returns **OK, 42
waypoints**. The tunnel is passable through. The route always existed; the executor was
thrashing.

**The bug, once seen, is embarrassing and completely general.** Having just warped INTO the
tunnel, the bot is *standing on* the door back out. So walk-validation on that tile trivially
succeeds — zero steps — and it is the first candidate the BFS offers. The executor picks it,
warps back, re-plans, picks the inbound door again, and loops:
ROUTE116 -> TUNNEL -> ROUTE116 -> TUNNEL. `used_warps` cannot help, because the tunnel has
THREE doors and the return trip is a different edge each time.

**Fix.** The candidate loop now runs TWO passes: prefer a door leading somewhere NEW, and only
accept one leading back to a map already visited if nothing else validates. (The same
visited-map preference was added to `_staged_progress_warp` in part 4; it did nothing on its
own because this leg is chosen in the earlier candidate loop, which had no such check — a
reminder to fix the branch actually being taken, not the one you were looking at.)

**Result — the journey completes.** From `journey_r116_wedge.ss1`:
`RESULT arm=new arrived=True map=FIERY_PATH`.

**The full arc of #24-journey, measured from PETALBURG_CITY at each step:**
| | how far |
|---|---|
| start of day | ends the run at Petalburg; no travel attempted |
| part 1-2 (map-granular warps, staged progress) | ROUTE116 |
| part 3 (no navigate during battle transitions) | ROUTE116 (47,9), beside the tunnel door |
| **part 5 (prefer unvisited doors)** | **FIERY_PATH — arrives** |

## 2026-07-31 — ‼ `#24-journey` COMPLETE: Petalburg → Fiery Path arrives

```
RESULT arm=new arrived=True map=FIERY_PATH detail=arrived
```
From `norman_done.ss1` (**PETALBURG_CITY** — the position the Norman counter ladder actually
fires from), through the production call path (`_navigate_riding_out`, what
`counter_hunt.hunt()` calls). **The Machop that answers Norman is now reachable from where the
chain asks for it.**

### The last bug: my own optimisation, latching the wrong thing
Part 5 got the journey to **ROUTE111 (31,114)** — standing on the very map whose Rock Smash
rock at (18,101) seals the corridor — and stopped there **with obstacle clearing switched
off**. The cause was a latch I added earlier the same day:

```python
obstacle_search_exhausted = False   # ...set True on the first empty search
```
justified in its own comment with *"riding out a scene cannot create new rocks, so one empty
answer is final for this trip"*. True for scenes; **false for journeys**. The run searched once
in PETALBURG (correctly empty — the rock is seven maps away), latched, then crossed seven maps
with the feature disabled.

Fixed by keying the latch to the MAP (`obstacle_search_done_on`) instead of a boolean. That
keeps the reason the latch exists — the search is synchronous and freezes the emulator, so
repeating it on every retry costs seconds per failed navigation — while giving every new map a
fresh look.

### The full arc, all measured from PETALBURG_CITY
| step | how far it got |
|---|---|
| start of day | ends the run at Petalburg; no travel attempted |
| map-granular warp planning + staged progress | ROUTE116 |
| no `navigate_to` during battle transitions | ROUTE116 (47,9), beside the tunnel door |
| prefer doors leading somewhere NEW | ROUTE116 → FIERY_PATH (from the anchor) |
| **obstacle search re-runs per map** | **PETALBURG → FIERY_PATH, arrives** |

### What this cost, and the pattern worth remembering
Five bugs, and **four of them were mine, introduced the same day**: the latched obstacle
search, the re-entrancy loop, the ping-pong, and the walk-back-out-the-door. Each was found by
MEASURING the next failure rather than reasoning about it — and in two cases my stated
hypothesis was wrong and a single trace disproved it in one run. The one that generalises:
**an optimisation whose justification contains the word "cannot" deserves a second look —
"riding out a scene cannot create new rocks" was correct about scenes and silently wrong about
the journey the code was actually for.**

‼ **Still unmeasured:** whether the counter chain, having arrived, actually CATCHES and TRAINS
a Machop and beats Norman. Arrival is not the same claim. That is what the next batch answers.

## 2026-07-31 — ‼ THE BATCH INSTRUMENT CANNOT MEASURE FINISH RATE. Read this before quoting one.

Second batch in (`x4-runs/20260731-140514`, commit `1b9e690f`, 8 lanes, 180 min):

| metric | baseline `289d1710` | `1b9e690f` |
|---|---|---|
| runs ended | 38 | 39 |
| finished | 9 (**23.7%**) | 12 (**30.8%**) |
| counter chain as a share of non-finishes | 25/29 (86%) | 19/27 (70%) |
| — Norman (needs Fighting) | 15 | 11 |
| — Winona | 5 | 5 |
| — Wattson (needs Ground) | 5 | 3 |
| `GAVE UP` | 20 | 30 |
| global watchdog | 9 | 20 |

**It is tempting to read that as "finish rate up 7 points, Norman down 4". Do not.** Two-
proportion z test on 9/38 vs 12/39: **z = 0.70**, against the 1.96 needed for 95% confidence.
That is squarely **within noise**, and so is every other row of the table at these counts.

### What this instrument can and cannot resolve (~38 runs per arm, one 3h 8-lane batch)
| change in finish rate | runs per arm needed (80% power) |
|---|---|
| 24% → 30% | ~776 |
| 24% → 35% | ~255 |
| 24% → 40% | ~129 |
| 24% → 48% | ~62 |
| **24% → 65%** | **~23 — detectable** |

So a 3-hour batch can only detect changes of roughly **+30 percentage points or more**.
Anything smaller is unmeasurable at this sample size, no matter how confident the table looks.
Reaching ~130 runs per arm would take about **10 hours per arm** at current throughput.

### What to use instead — and this is the whole lesson
1. **Direct capability tests in the harness are worth more than a batch, and cost minutes.**
   "Does the bot reach Fiery Path from Petalburg?" is BINARY and answered definitively by one
   `story_harness.py --driver smashroute` run. Every real conclusion today came from one of
   those, not from a batch.
2. **Near-binary batch signals are trustworthy; rates are not.** The hunt firing **0 → 9 times**
   is a real, unambiguous change. "30.8% vs 23.7%" is not.
3. **Say the metric AND its uncertainty.** This project has already recorded one fix as
   "live-validated" on a metric that could not see the failure (`d7d493d8`). Quoting a finish
   rate from ~38 runs as evidence of improvement is the same error wearing a lab coat.

‼ **Do not run longer batches to chase small finish-rate deltas.** ~10 hours per arm to resolve
a 16-point difference is a poor trade against a 5-minute harness run that answers a specific
capability question outright. Use batches for what they are good at: discovering FAILURE MODES
you did not know about (which is exactly how the Petalburg travel bug was found), not for
grading improvements.

## 2026-07-31 — `#24-counters`: the chain CATCHES its counter now, and the blocker moved to training

**The batch answered the question.** `x4-runs/20260731-170603` (commit `3875843c`) shows the
counter chain working end to end through the catch, three times:

```
Story: counter hunt CAUGHT Machop (slot 5).
Story: training Machop to L35 rejected — estimated 1693806 frames exceeds the
       budget (250000). It joins the fight at L16.
```

Diagnose → travel to Fiery Path → **catch the Machop** → then field it at **L16 against
Norman's L28-31 team**. **Balance Badges earned that batch: 0.**

Note which signals are trustworthy here: `CAUGHT Machop` ×3 and `Balance Badge` ×0 are
near-binary and real. The finish rate is not — see the power analysis above.

### Fix shipped: spend the budget instead of refusing it
The gate was ALL-OR-NOTHING — train to within `TRAIN_TO_TEAM_GAP` of the team, or not at all.
A hunting-ground counter is ~15 levels below the team **by construction**, so that resolves to
NOT AT ALL essentially every time, and the chain paid for a cross-Hoenn journey and a Poké Ball
to gain nothing. It also contradicted the user's own ruling — *"price both, then
catch-and-train a Fighting type for Norman"*: catching and then declining to train is the cost
of one option with the benefit of neither.

`affordable_training_target()` (pure, injectable, `repro_counter_training_budget.py` — 14
checks, no emulator) buys the highest level the budget covers. The honest decline is preserved
for the case where not even one level is affordable, and an UNKNOWN estimate still declines.

### ‼ AND THE HONEST LIMIT, WHICH IS A DECISION FOR THE USER
This is strictly better and **it is not sufficient**, which the repro pins so nobody
over-claims it. From the measured numbers — Machop L16 → L35 = 1,693,806 frames, i.e. **~89k
frames per level**:

| budget | levels bought | resulting counter |
|---|---|---|
| 250,000 (current `MAX_PREP_TRAINING_FRAMES`) | **2** | L18 vs Norman's L28-31 |
| ~890,000 | 10 | L26 — within ~5 levels, a real answer |

So the current budget cannot make this candidate work no matter how it is spent. **The
decision is the user's**, and the economics are worth stating plainly: when the counter ladder
fires the run is otherwise OVER (it fires after 6 boss losses and ends the run), and a full run
costs 2-3M frames. Spending ~890k to save a run that would otherwise be lost is arguably a good
trade — but it is a real behavioural change and it is not mine to make unilaterally.

**Three options, to be priced against each other rather than guessed between:**
1. **Raise the counter-training budget** to ~900k (its own constant, not
   `MAX_PREP_TRAINING_FRAMES`, which serves ordinary prep). Simple; costs ~30% of a run.
2. **Pick a counter by LEVEL GAP, not just by reachability and rate.** A candidate 15 levels
   below the team is a poor answer whatever the budget. The cost model already prices training
   — the ranking should weight it much harder, or exclude candidates whose gap cannot be closed
   within budget. This is the more principled fix and does not raise any budget.
3. **Accept the underlevelled counter** and lean on the 2x STAB type advantage. Cheapest;
   untested, and an L18 against an L31 is likely still a loss. **Testable in minutes** with a
   direct harness capability test rather than another batch.

‼ Option 2 is probably right, but "probably" is exactly what this project keeps getting wrong.
**Measure option 3 first** — it is a binary question and cheap — because if an L18 counter does
beat Norman, options 1 and 2 are both unnecessary.

## 2026-07-31 — ‼ RESULT: the day's work is MEASURED, SIGNIFICANT, and the right instrument is the BADGE FUNNEL

Third batch (`x4-runs/20260731-170603`, commit `3875843c`, 8 lanes, 180 min):
**35 runs ended, 20 finished = 57.1%** against the baseline's 23.7% — **z = 2.92,
significant at 95%**, and comfortably above the ~+30 point floor the power analysis says a
3-hour batch can resolve. Counter-chain derails fell from **25 of 29 non-finishes (86%) to
8 of 15 (53%)**, and the Norman line specifically from **15 to 3** (z = −3.06, significant).

### ‼ THE BADGE FUNNEL IS A BETTER INSTRUMENT THAN FINISH RATE — use it from now on
Finish rate is ~38 binary outcomes per batch and can only resolve enormous changes. Badge
records are ~200 per batch and say **where** runs are lost. From `badge-log.json`, segmented
by batch window:

| window | Stone | Knuckle | Dynamo | Heat | Balance (Norman) | Feather (content end) |
|---|---|---|---|---|---|---|
| baseline `289d1710` | 46 | 45 | 37 | 36 | 20 | 9 |
| batch2 `1b9e690f` | 47 | 45 | 37 | 35 | 22 | 12 |
| **batch3 `3875843c`** | 43 | 42 | 32 | 31 | **24** | **20** |

Conversion through the funnel — this is the part that matters:

| window | Kn/St | Dy/Kn | Ht/Dy | **Bal/Ht** | **Fea/Bal** | **Fea/St** |
|---|---|---|---|---|---|---|
| baseline | 98% | 82% | 97% | 56% | 45% | **20%** |
| batch2 | 96% | 82% | 95% | 63% | 55% | 26% |
| **batch3** | 98% | 76% | 97% | **77%** | **83%** | **47%** |

* **Whole-funnel completion 20% → 47%** (z = 2.71, **significant**)
* **Balance → Feather 45% → 83%** (z = 2.67, **significant**) — once past Norman, the travel
  fixes help everywhere
* **Heat → Balance 56% → 77%** (z = 1.88, *just short of 95%*) — beating Norman itself
  improved, but say "directional", not "proven"

Note the early rungs are flat (98% / 97% in both) — the change is concentrated exactly where
the counter chain and long-distance travel operate, which is what makes this credible rather
than a lucky sample.

### The counter chain, end to end
`CAUGHT Machop` ×4 this batch. Every one still hit the ALL-OR-NOTHING training refusal, because
this batch predates `affordable_training_target` (commit `1c4b183d`) — so the gain above was
achieved **with the counter still entering underlevelled**, and the training fix is not yet
represented in any measurement.

### A caveat recorded honestly
`global watchdog` rose **9 → 143**. Runs now travel much further, and long journeys trip the
18,000-frame no-progress watchdog which then recovers — but this is a large jump and it has
NOT been investigated. It is not obviously harmful (the finish rate went up regardless), and it
is exactly the kind of number that turns out to matter later. **Do not dismiss it.**

### An isolated test that CONTRADICTED the batch — and why the batch wins
`--driver normancounter` injected a Machop at L18 and then L26 into
`prenorman_fodder_grind.ss1` and both whited out, implying the counter never works. The batch
says otherwise (24 Balance Badges). The isolated test is the weaker evidence: that save is a
deliberately awkward "fodder grind" scenario with a thin team, so it measures *that team's*
chances, not the counter's contribution. **A capability test is only as good as the state it
starts from** — the same lesson as testing travel from Mauville instead of Petalburg, one level
up. Do not trust the L18/L26 numbers; re-run that driver from a representative pre-Norman save
before drawing any conclusion about training levels.

## 2026-07-31 (evening) — the `global watchdog 9 → 143` caveat is a REGRESSION, not longer journeys (KI-43)

Investigated the one open caveat left by the batch3 result, using only stored logs — no
emulation was re-run (a fresh batch would have produced a different sample and destroyed the
comparison, and the box was busy with batch4 anyway).

**The handoff's hypothesis was wrong.** It read the jump as *"runs travel much further now and
long journeys trip the 18k-frame no-progress watchdog"*. Where the fires actually land:

| trips | map | fires immediately after |
|---|---|---|
| 35 | `RUSTBORO_CITY_MART` | `bought Poké Balls` |
| 31 | `LAVARIDGE_TOWN` | `BADGE: Heat Badge` |
| 3 | `ROUTE112` | — |
| 1 | `ROUTE116` | — |

Both clusters are stationary wedges at a step boundary. Nothing about journey length.

**Root cause — `_navigate_when_ready` (added by `fea2bb19`, `#24-journey` part 3):**

```
_MAX_NON_OVERWORLD_FRAMES = 60 * 60 * 5   = 18,000   (global_navigation.py:90)
global watchdog: _stall_frames >= 18,000             (story_mode.py:2002)
```

The wrapper waits for the overworld while pressing nothing and changing nothing — which is
precisely the watchdog's stall signature — and its escape hatch is budgeted at *exactly* the
watchdog's threshold. The watchdog fires on frame 18,000 (`>=`), the break needs 18,001 (`>`).
**The derail wins by one frame every time; the `break` is unreachable code**, and its
docstring's promise that "a genuine softlock still surfaces" has never once held.

The constant predates the regression, but at `289d1710` it guarded only the rare
"not in the overworld" case. `fea2bb19` added the far stickier `not
player_avatar_is_controllable()` and applied it to every `navigate_to` call, which is what
made the collision reachable.

**Measured cost beyond burned frames.** The mart restock buys in batches of ten to farm the
free Premier Ball per purchase. Ball-count transitions:

```
baseline 289d1710   (0→10)×17  (11→21)×17  (22→32)×16    three purchases, chained
batch3   3875843c   (0→10)×13  (1→11)×23   and nothing else — 36 of 36 are FIRST buys
```

Every second purchase wedges: **33/33 clean at baseline, 0/36 in batch3.** So each restock
now yields 10 balls instead of 30, loses 2 free Premier Balls, and spends a derail out of the
budget that exists to catch genuine stuck loops.

**Instrument correction.** `summary.json`'s `global_watchdog` counts over `stdout + debug
logs` and a watchdog derail is written to both (console line + `[STORY] DERAIL #N:`), so the
headline `9 → 143` is really **5 → 72**. Verified this is specific to that canary — `GAVE UP`
is debug-log-only and `BADGE:`/`losses` are stdout-only, so those are not inflated. An earlier
draft of this analysis claimed every `both`-based canary was doubled; that was too broad.

**Added** `tools/story-dev/repro_watchdog_budget_collision.py` — no emulator, reads both
constants from source, asserts the guard expires inside the watchdog window. **RED on purpose
until the fix lands** (reproduce first, then fix).

**Deliberately NOT fixed in this commit.** Batch `20260731-201554` was mid-flight and the
runner restarts crashed lanes, so any edit under `sandbox-pokebot/` would have been imported
by a restarted lane and contaminated the measurement. Queued as step 1 in the handoff.

## 2026-07-31 (late) — batch4 RESULT: the training fix fires, 7/7 training runs FAIL, funnel flat; KI-43 FIXED

### Batch 4 — `x4-runs/20260731-201554`, commit `92d220d5`, 8 lanes / 180.1 min, VERDICT OK
38 headers checked, 0 emulation violations, 0 lane restarts. **30 runs ended, 18 finished =
60.0%** (batch3: 20/35 = 57.1%).

**Badge funnel — nothing moved.** Per the standing instruction to read the funnel, not the
finish rate:

| rung | batch3 `3875843c` | batch4 `92d220d5` | z |
|---|---|---|---|
| Stone→Knuckle | 42/43 (98%) | 35/37 (95%) | −0.72 |
| Knuckle→Dynamo | 32/42 (76%) | 31/35 (89%) | 1.40 |
| Dynamo→Heat | 31/32 (97%) | 29/31 (94%) | −0.62 |
| **Heat→Balance (beating Norman)** | 24/31 (77%) | 24/29 (83%) | **0.52** |
| Balance→Feather | 20/24 (83%) | 18/24 (75%) | −0.71 |
| Stone→Feather (whole funnel) | 20/43 (47%) | 18/37 (49%) | 0.19 |

Not one rung is significant. **`affordable_training_target` did not move the needle**, and
the log says exactly why.

### WHY — the fix works, and then the bot cannot reach the training grass

| | batch3 | batch4 |
|---|---|---|
| `counter hunt CAUGHT` | 5 | 9 |
| `training … rejected` (the old all-or-nothing gate) | 4 | **0** |
| affordable target chosen (`… would cost N — training to LN instead`) | 0 | **7** |
| `training the counter —` (training actually STARTS) | 0 | **7** |
| **`counter training failed`** | 0 | **7** |

The gate is fixed: it now picks e.g. `Machop L15 -> L21 (team is L35, est 222115 frames)`.
Training then starts and **fails 7 times out of 7** — 6 with

```
UnreachableDestinationError('Could not reach (9, 2) on MapRSE.ROUTE102: the field is idle
and we are still at (45, …) … Cannot reach PETALBURG_CITY: it is not walkable from
ROUTE103, and none of the 6 candidate warp route(s) start at a tile that can be walked to
from here (tried: OLDALE_TOWN(…)×4, PETALBURG_CITY(…)×2).')
```

and 1 to a whiteout. **Zero counters were ever trained.** The counter still enters Norman at
L15-16 against L28-31, which is precisely the state batch3 was in — hence the flat funnel.

‼ **This is EXPOSED, not CAUSED, by the training fix.** In batch3 the gate refused before any
travel was attempted, so the travel failure could not be observed. Logged as **KI-44**.

### Also new in batch4 — ball starvation
`no money to buy any` end-reason: **0 → 14 occurrences (3 ended runs)**, e.g. *"Cannot hunt a
Surf learner: no Poké Balls and no money to buy any."* Consistent with KI-43: catches rose
5 → 9 while every restock bought 10 balls instead of 30.

Clean canary: KI-38's `GAVE UP` **10 → 0**.

### KI-43 — FIXED and PROVEN

`_navigate_when_ready` now uses its own `_TRANSIENT_WAIT_FRAMES = 600` (10 s) instead of
`_MAX_NON_OVERWORLD_FRAMES` (18,000 = the watchdog's own threshold). Left
`_MAX_NON_OVERWORLD_FRAMES` alone deliberately: the outer loop waits on game STATE, which
flips during a cutscene and so keeps resetting the watchdog's signature — it does not produce
the frozen signature this wrapper did.

**Proof 1 — structural, fault-injected both ways.**
`repro_watchdog_budget_collision.py` now reads whichever constant the wrapper actually uses
(parsed from its body — hardcoding the name would let the bug return under a new name).
Green at 600; re-inject `60 * 60 * 5` and 3 checks go red; restore and green again.

**Proof 2 — live A/B**, `gym1_done.ss1`, `--driver martbuy`, `BUYN=30`, 40,000 frames:

| arm | purchases completed | Premier Balls | money |
|---|---|---|---|
| OLD (`_TRANSIENT_WAIT_FRAMES = 18,000`) | **0** — no `[buy] AFTER` line at all | — | unspent |
| NEW (`= 600`) | **3** | **3** | 8628 → 2628 (30 balls) |

The old arm's stall signature names the mechanism outright: parked at `(3, 3)` with
`RustboroCity_Mart_EventScript_PokemartBasic` + `Std_MsgboxDefault` active — the shop script
is up, so `player_avatar_is_controllable()` is False, and the wrapper waits on it while
pressing nothing. Exactly the predicted shape.

## 2026-08-01 — PROMOTION: the full story-bot round sandbox → custom (BATCH-4)

On explicit user approval. **37 files, 16 new**, pre-promotion custom HEAD `9105d6d3`. Full
detail in `custom-pokebot/DIVERGENCE-LOG.md` → **BATCH-4**.

Scope was the FULL sandbox code surface rather than a curated subset, because the modules are
interdependent (`early_game` → `counter_hunt` → `obstacle_clearing`; `dashboard_gui` → the x4
bundle) and a partial promotion is exactly what would break custom. That also finally brings
across `story_milestones`/`milestone_window`, which BATCH-3 held back — `dashboard_gui` has
since taken a hard dependency on them.

**Two traps caught by checking instead of mirroring:**
1. `sandbox-pokebot/DIVERGENCE-LOG.md` is a **stale 91-line fork frozen at 2026-07-18**, while
   custom's is 606 lines through BATCH-3d. `robocopy`/blind-mirror would have destroyed 515
   lines of append-only history. Excluded, and the exclusion is recorded for future rounds.
2. `DOCUMENTATION/03-cheats.md`, `04-automation-and-sync.md`, `05-hunting-and-livingdex.md`
   exist ONLY in custom. A mirror-with-delete would have removed them. Preserved.

**Safety check before copying:** every `def`/`class`/CONSTANT in the custom copies of all 19
modified `.py` files compared against sandbox — **0 lost symbols**, +87 gained. Sandbox is a
strict superset, so no custom-only functionality was reverted.

**Verified after:** 210 files parse (0 errors); 18/18 promoted modules import; constants live
(`_TRANSIENT_WAIT_FRAMES=600`, `MAX_PREP_TRAINING_FRAMES=250000`); ML-2 git-trackability
checked on every new path; and a **live run on `--build custom`** (`gym1_done.ss1 --driver
martbuy BUYN=30`) reproduced the KI-43 fix — **3 purchases, 3 Premier Balls, 8628 → 2628**,
identical to sandbox, where the pre-fix code completed 0.

**Shipped with known open issues, stated rather than buried:** KI-44 (counter training reaches
its grass 0 of 7 times, so no counter is ever trained), ball starvation (14 events in batch4),
the still-elevated watchdog count, and the party cap of 4.

## 2026-08-01 — KI-44 fixed: a counter now trains somewhere it can reach AND heal from

`train_counter` used `cfg["grass"]`, the **boss's** patch. A Machop caught in FIERY_PATH was
sent to Norman's `PETALBURG_TRAINING_GRASS = (ROUTE102, (9, 2))` — eight maps away, through a
corridor the bot cannot cross (training failed **7 of 7** in batch4), and once there the land
wilds are **L3-4**. `story_mode.py:739` already called that patch "~25 xp a kill, i.e. never".
So the visible failure (cannot get there) was hiding a second one that no log showed: it was
not worth going.

**Probed** with `tools/story-dev/probe_counter_grass.py` (new — boots the ROM, reads the real
encounter tables, never steps a frame): ROUTE102 **L3-4** vs FIERY_PATH **L14-16**,
ROUTE112 L14-16, JAGGED_PASS L20-22.

‼ **The obvious repair is also wrong**, which is the part worth remembering: "train where you
caught it" picks FIERY_PATH, and FIERY_PATH / ROUTE112 / JAGGED_PASS are all in
`NO_RETURN_GROUNDS` — reachable and exitable, but the heal leg back to Lavaridge fails, and a
training loop needs that third leg. There was **no legal training ground at all** for a
counter caught in Fiery Path. A structural hole in the chain, not a wrong constant.

**Fix:** `counter_hunt.counter_training_ground()` asks `best_training_area` — the picker the
rest of the bot already uses, which refuses no-return grounds first, applies the winnability
guard, honours the live reachability predicate, and prefers the band closest to the trainee.
Falls back to the configured pair when it has no answer, so bosses whose grass is already
right are unchanged and a picker failure can never destroy a successful catch.

**Live probe from `lavaridge.ss1`** with the real predicate: `best_training_area(L15)` →
`ROUTE117 (31,16) L13-14`; at L20 → `ROUTE111 L19-22`; `counter_training_ground(L15, Norman
cfg)` → grass `ROUTE117 (31,16)`, heal `VerdanturfTown` — **RELOCATED, the fix fires** rather
than falling back.

**Repro:** `repro_counter_training_ground.py` asserts a PROPERTY, not an answer — no
no-return ground at any level L10-30 even with `allow=<always true>`, no unwinnable band,
never ROUTE102 for a L15 counter, and safe degradation with no ROM — so a future table edit
cannot quietly reintroduce the hole.

**Not proven yet, stated plainly:** the probe stood on LAVARIDGE_TOWN, one map short of
FIERY_PATH (18,19) where the catch happens; and the outcome (a trained counter beating
Norman) needs a batch. Batch4's lesson applies — the mechanism firing is not the funnel
moving. Next batch: read `Heat→Balance` against 24/29 (83%) and count `counter training
failed`, which was 7 of 7.

## 2026-08-01 — BATCH 5 RESULT: KI-44 is fixed and the funnel did NOT move; the blocker is now the LEAD

`x4-runs/20260801-075805`, commit `b7345ffd`, 8 lanes / 180.1 min, VERDICT OK, 42 headers,
0 violations, 0 restarts. **34 runs ended, 16 finished = 47.1%** (batch4 60.0%).

### The mechanism is FIXED — counters are trained for the first time ever

| | batch4 | batch5 |
|---|---|---|
| `counter hunt CAUGHT` | 9 | 10 |
| relocation line (`… rather than the boss's own patch`) | *(didn't exist)* | **9** |
| `training the counter —` (starts) | 7 | 9 |
| **`counter training failed`** | **7 of 7** | **2 of 9** |

```
Story: training the counter at ROUTE117 (31, 16) rather than the boss's own patch ROUTE102  ×8
Story: training the counter at ROUTE121 (44, 14) …                                          ×1
Story: training the counter — Machop L15 -> L29  ×5    Machop L16 -> L29  ×3
Story: training the counter — Combusken L31 -> L33 ×1
```
The Machop reaches **L28 and evolves to Machoke**. The picker also adapted on its own
(ROUTE121 for a L31 Combusken). Neither remaining failure is KI-44 — one whiteout abort,
one `UnreachableDestinationError`.

### And the funnel did not move

| rung | batch4 | batch5 | z |
|---|---|---|---|
| Stone→Knuckle | 35/37 (95%) | 40/42 (95%) | 0.13 |
| Knuckle→Dynamo | 31/35 (89%) | 32/40 (80%) | −1.01 |
| Dynamo→Heat | 29/31 (94%) | 29/32 (91%) | −0.43 |
| **Heat→Balance** | 24/29 (83%) | 23/29 (79%) | **−0.33** |
| Balance→Feather | 18/24 (75%) | 16/23 (70%) | −0.42 |
| Stone→Feather | 18/37 (49%) | 16/42 (38%) | −0.95 |

Nothing significant. Like-for-like on the only population the fix can affect —
**runs that ran a counter hunt: batch4 5/9 (56%) → batch5 6/10 (60%), z = 0.20.**
n=9 vs n=10 cannot resolve this; do not read either number as an effect.

‼ **Beware the seductive wrong comparison.** Within batch5, counter-hunt runs beat Norman
5/7 (71%) while runs that never needed one went 17/19 (89%). That is **selection bias, not
harm** — the chain only fires on runs already losing to Norman. The like-for-like
cross-batch comparison above is the honest one.

### ‼ WHY IT DIDN'T MOVE — the trained counter is BENCHED

Leads chosen for the Norman fight in batch5: **SHEDINJA ×9**, MARSHTOMP ×4, SWAMPERT ×4,
BLAZIKEN ×2, COMBUSKEN/LINOONE/LOUDRED/SWELLOW ×1. **MACHOKE: zero.**

`_lead_best_matchup(["Normal"])` scores `min(incoming_multiplier, -level)`, so Shedinja
(Bug/Ghost, Normal → 0×) always wins the score and the freshly-trained L29 Machoke sits in
the bag. This is **`#24-leadpolicy`**, already diagnosed with **USER RULING A+C** and never
built — and its own entry predicted this exact run: *"P4 led Shedinja L20 vs Norman … and
lost to Slaking's Faint Attack (Dark), which the model cannot see because it does not read
movepools."*

**So the blocker has moved a third time: budget → training ground → LEAD SELECTION.**
Catching and training a type counter and then not fielding it is the cost of the whole chain
with the benefit of none of it.

## 2026-08-01 — `#24-relocfloor`: the relocation floor is keyed to the trainee, not the team max

`floor = max(local_max, team_max_now - FODDER_LEVEL_GAP)` used the party's STRONGEST mon
while `need` is the stragglers, so a L35 team demanded wilds above L23 and rejected
ROUTE111 (L19-22) — the one reachable area. Measured: `no better area is available` fired
**167×** in batch4, every one on ROUTE102's L3-4 grass, teams L32-41.

Extracted as the pure `training_areas.relocation_floor(local_max, trainee_levels, gap)`.
‼ Only the floor moved — `train_team` runs with SWAP-TRAIN, so a stronger team-mate fights
and `best_training_area`'s own `team_level` argument stays the team max; keying that to the
trainee would be a second bug.

Effect with the real tables, `allow` restricted to what is reachable near Petalburg:
L35 (stragglers L12/L20) floor 23 → **None**, trainee-keyed 8 → **ROUTE111**; L36 floor 24 →
**None**, trainee 4 → **ROUTE111**; L33 already worked either way — matching the 12 real
ROUTE111 relocations observed. Repro `repro_relocation_floor_wrong_mon.py` (checks 1-3 pass
on the public API before the fix; check 4 green after).

## 2026-08-01 — `#24-leadpolicy` (ruling A+C): stop leading a 1-HP Wonder Guard mon into a boss

Batch5 proved the counter chain works end to end and the funnel still did not move, because
`_lead_best_matchup` scored ONLY defence — `min(incoming_multiplier, -level)`. Shedinja is
Bug/Ghost, so Normal → 0× wins that score outright, and the bot **led Shedinja into Norman 9
times out of 9 while the freshly-trained L29 Machoke sat in the bag.**

Implemented exactly the ruling, no more:
* **(a)** the lead must also have a **≥neutral damaging move** against the foe's types;
* **(c)** a **Wonder Guard 1-HP body** (Shedinja) is demoted — it wins a purely defensive
  score and is then deleted by any super-effective move, which this model cannot predict
  because it does not read the foe's movepool.

The rule is the pure `team_policy.lead_rank_key()` / `best_lead_index()` — `team_policy` is a
deliberately emulator-free decision module, so the whole policy is unit-testable.
`early_game._lead_best_matchup` now computes `can_attack` / `glass_wonder_guard` from the live
mon and defers to it. Both new predicates **fail SAFE** (a read error returns "can attack" /
"not Wonder Guard"), so a memory hiccup can never bench a mon.

‼ **These are SORT TERMS, NOT FILTERS.** A filter could empty the candidate set and leave no
lead at all; ordering always yields an answer and degrades to today's choice when nothing
better exists. Pinned: a lone Shedinja is still led.

‼ **Ordering is deliberate** — `incoming` stays ahead of the level tie-break, so the proven
Rustboro-rival behaviour is untouched. **Option (b) was NOT ruled and is NOT implemented**;
`repro_lead_policy.py` check 4 pins Whismur-over-Marshtomp so nobody "helpfully" changes it
without asking.

‼ **THE HONEST LIMIT, ASSERTED IN THE REPRO RATHER THAN BURIED (check 5).** On batch5's real
Norman party, A+C stops the Shedinja lead but **still does not field the counter**: Marshtomp
L35 outranks Machoke L29 because `can_attack` is binary and gives Machoke's 2× STAB no
credit. So A+C removes a demonstrably fatal lead but does not by itself make the counter
fight. Whether super-effectiveness should outrank raw level is a **new decision**, outside
ruling A+C — see the handoff.

## 2026-08-02 — `#24-pc`: the PC rotation ACTION, piggybacked on a heal

**Why this and not the lead question:** batch5's `end_reasons` say 13 of 18 non-finishes
(72%) are the counter chain stopping honestly, and its own logs name the wall — **5 runs were
blocked before the hunt could even start** by *"the party is full, so a catch would go to the
PC box (needs #24-pc)"*. `team_policy` already DECIDED what to rotate and is deliberately
pure; nothing executed it.

**Built** `modules/story/pc_trip.py` — `plan_deposits()` + `deposit_dead_weight_if_worth_it()`.
It reuses upstream's `interact_with_pc()` / `PCAction.deposit_pokemon_to_box()`, so no PC-menu
driving was written from scratch.

‼ **PIGGYBACK, NOT DETOUR** (`21-TEAM-POLICY-DESIGN.md` §4). Wired **inside**
`heal_in_pokemon_center`, between the nurse and the exit — we are already in the building for
a heal that was happening anyway, so it costs a few steps rather than a journey. It no-ops
unless `rotation_plan` reports `worth_it`, so a level party never burns a PC visit.

‼ **THE TILE IS PROVEN, NOT RECALLED.** New `tools/story-dev/probe_pc_tile.py` scans Poké
Centre map headers from the ROM: all six centres put the PC at **(10, 1)**, approachable only
from **(10, 2)** facing **Up**. Upstream `daycare.py` independently navigates to (10,2) and
faces Up, which corroborates it. `interact_with_pc` refuses unless the faced tile really is a
PC, so a wrong tile fails loudly rather than silently doing nothing.

‼ **Instrument check that mattered:** the probe first reported "no PC tiles in any centre".
That was **my call signature**, not the map — `get_map_data(map, coords)`, not
`(group, number, coords)` — and it returned 192 `TypeError`s that the scan was swallowing as
empty tiles. Checking *what the instrument actually read* turned a false "the PC does not
exist" into the answer.

**Guards, each pinned by `repro_pc_trip.py` (14 checks):** a healthy party is left alone; the
Makuhita case frees a slot and deposits chaff rather than a battler; the party never drops
below `MIN_PARTY_AFTER_ROTATION`; the wiring really is nurse → rotate → exit; every failure
path degrades instead of raising (a PC hiccup must not destroy a heal that already
succeeded); and **Pokémon OBJECTS are resolved before the first deposit, never indices** —
depositing shifts later party indices down, which is the classic way this loop deposits the
wrong mon.

**Not yet proven:** no live run has executed a deposit. The decision half, the tile, the
wiring and the failure paths are all covered without an emulator, but the menu drive itself
needs a batch or a targeted save state.

## 2026-08-02 — `#24-areaitemgate`: refuse a training area behind an ITEM gate BEFORE the trek

Second item on the autonomous plan — the 40 `is not reachable from here` events in batch5.
Split by source, they are not what the phrase suggested:

```
28  ROUTE111 (25, 55) dropped as a TRAINING option for the rest of the run
 4  ROUTE116 (11, 7) dropped likewise
 8  counter-hunt destinations (ROUTE111 x4, ROUTE116 x4)
```

The 28 come from the handler *after* `train_team` raises — **the oracle said yes and the map
disagreed**, roughly one wasted cross-Hoenn trek per run.

**Root cause.** `_training_area_allowed(map_enum, tile, prereq)` is handed the TILE and never
uses it. It asks `region_reach.is_map_reachable(ROUTE111)`, which answers at MAP granularity
and is *correctly* True — Route 111's southern half really is walkable from Mauville — while
the training tile **(25,55) sits NORTH of the Go-Goggles desert**.

‼ **The fact was already written down twice and neither copy was queryable:**
`counter_plan.huntable_candidates` ("whose tile sits north of the Go-Goggles desert") and
`early_game` ("Go-Goggles-gated by a script"). That is precisely the failure
`NO_RETURN_GROUNDS`' own header warns about — *prose in a table nobody queries*.

**Fix:** new `training_areas.AREA_ITEM_PREREQ = {ROUTE111: "Go-Goggles"}`, consulted by
`_training_area_allowed` **before** the map-granular oracle, failing CLOSED like every other
gate there. ‼ `KNOWN_GATES` could not express this: it keys map-PAIR EDGES and its values are
FIELD MOVES, whereas this barrier is INSIDE one map and the key is an ITEM.

‼ **Deliberately conservative, and worth stating:** the tile is also reachable from the
FALLARBOR side without goggles, so requiring the item can refuse a legitimately-walkable case.
That is the right trade and it is the same asymmetry this module already argues elsewhere — a
false NO costs one skipped relocation (the picker takes the next area), a false YES costs a
whole wasted trek, measured 28 times.

**Repro** `repro_area_item_gate.py` (14 checks) pins: the gate exists; **every gated item name
really exists in `items.json`** (a typo would fail closed forever and *silently*, which is the
KI-24 shape); the area entry has not drifted; the gate is evaluated before the oracle CALL and
fails closed; ungated areas are untouched.

‼ **A test bug worth recording:** the ordering check first FAILED because `.find("is_map_
reachable")` matched the function's own docstring, which discusses the oracle at length. The
code order was right; the assertion was imprecise. Anchored on the call site instead.

## 2026-08-02 — BATCH 6 RESULT: `#24-pc` caused a 47% → 5% collapse; gated and fixed

`x4-runs/20260802-160603`, commit `1700b965`, 8 lanes / 180.1 min, VERDICT OK, 45 headers,
0 violations, 0 restarts. **37 runs, 2 finished = 5.4%** (batch5: 16/34 = 47.1%).

### Both fixes did what they were built to do
| signal | batch5 | batch6 |
|---|---|---|
| `the party is full` (counter chain blocked) | 5 | **0** |
| `PC rotation — depositing` / `done` / `failed` | — | 90 / **75** / 15 |
| `dropping it as a training option` (wasted treks) | 32 | **0** |

`#24-pc`'s menu drive works live (75 successful deposits) and `#24-areaitemgate` eliminated
the wasted treks outright.

### And the batch collapsed anyway
| | batch5 | batch6 |
|---|---|---|
| finish rate | 47.1% | **5.4%** |
| `global watchdog` | 1 | **67** (24 in MAUVILLE_CITY_GYM) |
| `Cutscene did not end` | 5 | **35** |
| `relocating to` (training) | 24 | **0** |

**Cause: the rotation ran on EVERY heal.** With `MIN_PARTY_AFTER_ROTATION = 3` it deposits
until three remain — **`PC rotation done — party is now 3` 73 times out of 75**. The bot lived
the whole batch in a catch → deposit → catch cycle on a three-mon party and then wedged in
gyms it could not win. It deposited a **Shedinja L21**, a real battler.

‼ **`team_policy` was not wrong.** Its rule ("more than 8 levels behind the best is
unrecoverable") is correct, and an early-game party genuinely is four low catches that far
behind. The decision was right every time; **my wiring** was wrong — §4's "piggyback on a heal
that was happening anyway" assumes rotation is OCCASIONAL, and every-heal makes it continuous.

**Fix:** `pc_trip.ROTATE_ONLY_WHEN_PARTY_AT_LEAST = 6`. The blocker this feature exists for is
exactly one condition — `resource_blocker()` refuses a hunt only when `_party_count() >= 6` —
so that is the only moment a slot must be freed. `repro_pc_trip.py` now asserts 3-, 4- and
5-mon parties are NOT rotated while a full one still is: a **rate** test, not a decision test.

‼ **Why the existing repros missed it:** every check was about a SINGLE rotation in isolation
(right mon, respects the floor, degrades safely) and all of them still pass. None asked *how
often it would run*, and the damage was entirely in the frequency. A correct decision invoked
at the wrong cadence is invisible to a unit test.

‼ **A test-double trap, recorded:** the new rate check first FAILED on "a FULL party is still
rotated" because my stand-in party member lacked `species`/`moves`, so `view_from_party` threw
and `plan_deposits` returned an empty plan — which reads exactly like the gate working. A
false PASS was one line away; the double is now spelled out with a comment saying why.

### Also found — a NEW hang site (not caused by this change)
Lane H4 produced no output for 27 minutes while burning CPU: **866 STUCK dumps** in
`battle_menuing._select_in_menu` via `scroll_to_move`, in a Brawly trainer battle at
DEWFORD TOWN (3,3). Neither guard can see it — the global watchdog needs an *unchanged*
progress signature and a menu loop keeps changing it, and it is KI-36's documented shape
("the per-run frame budget CANNOT fire while a battle handler is on the stack"). Filed as
**KI-45**.

## 2026-08-02 — `#24-leadcounter`: the hunted counter finally gets to fight

User ruling 2026-08-02 (`06-DECISIONS-LOG`): super-effectiveness outranks raw level **only**
for a mon the counter chain caught for THIS boss — not as a general rule.

`team_policy.lead_rank_key()` gains an optional `is_hunted_counter`, and the key becomes:

    (glass_wonder_guard, not can_attack, incoming, not is_hunted_counter, -level)

‼ **Position is the design.** After `incoming`, before the level tie-break: it promotes the
counter over an EQUALLY SAFE mon and can never let a 4×-weak counter lead. `repro_lead_hunted_
counter.py` check 3 pins that, because inverting it is how this fix would become a new bug.

**Identity is the caught mon's PERSONALITY VALUE, never its party slot.** Since `#24-pc` the
bot deposits mid-run, so a slot index goes stale and would silently point at a different
Pokémon. The PID is recorded BEFORE training, because training can evolve the mon (Machop →
Machoke at L28, seen 8× in batch5) and can derail — the PID survives both.

**Per-run, on `self`.** `StoryMode._hunted_counter_pids` is reset with the rest of the per-run
state. A module-level set would survive between runs of an ENDLESS RESET batch and start
promoting a Pokémon that no longer exists — the `#24-x4-staleslate` shape, which once made a
whole batch produce almost no usable data.

Wired at the three bosses the chain can fire for: Norman (`Normal`), Wattson (`Electric`),
Winona (`Flying`). Everywhere else keeps exactly today's ordering — the ruling is scoped, and
`repro_lead_hunted_counter.py` check 2 asserts an unflagged L29 still loses to a neutral L35.

Suite 73/73.

## 2026-08-03 — BATCH 7: the gate held, the collapse mostly reversed, `#24-leadcounter` did NOT take effect

`x4-runs/20260802-215519`, commit `09c6129e`, 8 lanes / 180.1 min, VERDICT OK, 0 restarts.
**26 runs, 7 finished = 26.9%.**

### 1. The gate held — the batch6 regression is fixed
| | batch6 | batch7 |
|---|---|---|
| `PC rotation done — party is now 3` | **73 of 75** | **0** ✅ |
| … now 4 / now 5 | — | 11 / 5 |
| `PC rotation` depositing / done / failed | 90/75/15 | 16/16/**0** |

It now deposits one or two mons from a FULL party only, and every attempt succeeded.

### 2. The collapse mostly reversed — but not all the way back
| | batch5 | batch6 | batch7 |
|---|---|---|---|
| finish rate | 47.1% | 5.4% | **26.9%** (z = −1.59 vs batch5) |
| `global watchdog` | 1 | 67 | **18** |
| `Cutscene did not end` | 5 | 35 | **7** |

‼ **Not a clean recovery and I am not calling it one.** z = −1.59 cannot distinguish 26.9%
from 47.1% at n=26 vs 34 — but the watchdog at **18 vs batch5's 1** is not noise, and it is
unexplained. It fires on ROUTE118 (4), ROUTE117 (4), MAUVILLE_CITY_GYM (3), ROUTE112 (3).
**Something besides the PC rotation regressed between batch5 and batch7**, and the remaining
candidates are `#24-areaitemgate` and `#24-leadcounter`.

### 3. ‼ `#24-leadcounter` DID NOT TAKE EFFECT — 6 of 6
Every run that hunted caught AND trained a Machop to L29 (0 training failures, down from 2 of
9), and **not one led it into Norman**:
```
L02 run2: caught Machop, trained -> L29, Norman lead = SWAMPERT
L06 run1: caught Machop, trained -> L29, Norman lead = MARSHTOMP
L06 run4: caught Machop, trained -> L29, Norman lead = SWELLOW
(3 more caught+trained runs never reached a Balance Badge)
```
`_battler_slots` is permissive, so a L29 Machoke WAS a candidate; and L02 run2 won its badge
*after* the catch, so the lead call definitely ran. The fix simply did not fire.

‼ **AND I COULD NOT DIAGNOSE IT, BECAUSE I SHIPPED IT WITH NO OBSERVABILITY.** Nothing in the
log said whether `hunted_pids` was empty, whether the mon was in the candidate set, or how it
scored. **Added:** `_lead_best_matchup` now logs the choice, the whole candidate set with the
per-mon inputs that drove the key (`in=`, `atk/NOATK`, `WG`, `COUNTER`) and
`hunted_pids=<count>`. Guarded so logging can never affect the choice; pinned by
`repro_lead_hunted_counter.py` check 7. The prime suspect is an empty `hunted_pids` — a derail
between the catch and the fight would re-instantiate `StoryMode` and clear the per-run set —
but that is a HYPOTHESIS and the next batch's log will say.

### Suite note
73 scripts; one run showed `repro_x4_dashboard.py` red, then 4 consecutive passes plus one
under parallel load. Recorded as a **rare flake** (it drives tkinter), not as a regression, so
a future red on it is not mistaken for one.

## 2026-08-03 — `#24-leadpolicy` (c) flagged OFF by default: it removed a winning lead

Investigating the batch5 → batch7 regression (47.1% → 26.9%, against a stable 57/60/47%
plateau) found the likeliest cause, and it is mine.

`BADGE:` lines print only on a win. Shedinja appeared **12 times in batch5 and all 12 were
winning leads**, including **9 of the 23 Norman victories (39%)**. In batch7, with (c) active,
it appears 6 times and leads **zero** wins; Balance Badges fell 23 → 18.

I added (c) on the strength of a single narrated loss (Slaking's Faint Attack) and never
counted the wins. Wonder Guard makes Shedinja immune to Norman's entire Normal STAB.

**Change:** the demotion is now behind `POKEBOT_LEAD_DEMOTE_WONDER_GUARD`, **default OFF** —
restoring the batch5 behaviour. `lead_rank_key` is untouched and still demotes when told to;
only what the caller *reports* changed, so the pure rule stays testable both ways.
`repro_lead_policy.py` check 7 pins the default and the evidence. Suite 73/73.

‼ **Stated as a hypothesis, not a finding.** Batch7 carried FIVE changes since batch5
(`#24-relocfloor`, `#24-leadpolicy`, `#24-pc`, `#24-areaitemgate`, `#24-leadcounter`) and
correlation is not causation. The flag exists so the A/B can be *run* rather than argued.

## 2026-08-03 — BATCH 8: the Shedinja hypothesis is CONFIRMED; two more bugs found by the new logging

`x4-runs/20260803-063939`, commit `1811148a`, VERDICT OK. **24 runs, 11 finished = 45.8%.**

### ‼ CONFIRMED — `#24-leadpolicy` (c) was the regression
| | batch5 (no (c)) | batch7 (with (c)) | **batch8 ((c) off)** |
|---|---|---|---|
| Shedinja as a WINNING lead | 12 | **0** | **7** |
| Balance Badges | 23 | 18 | **21** |
| finish rate | 47.1% | 26.9% | **45.8%** |

batch7 → batch8 z = +1.39; **batch8 vs batch5 z = −0.09 — statistically indistinguishable,
i.e. fully recovered to the plateau.** The mechanism moved with it (Shedinja wins 0 → 7), so
this is not a lucky sample. `global watchdog` also fell 18 → 5.

**Verdict: option (c) removed a lead that was winning.** It stays flagged OFF.

### The new lead logging paid for itself immediately — two further bugs
`Story: lead vs Normal -> SwampertL38 (from SwampertL38 BeautiflyL23 RaltsL6 PoochyenaL10;
hunted_pids=0)` — the counter is not merely unpicked, it is **not in the party at all**.

**Bug 1 — the registry write never ran.** `get_party` is not in `_counter_ladder`'s scope, so
`_caught = get_party()[slot]` raised `NameError` into a bare `except: pass`. `hunted_pids=0`
on **all 684** logged decisions across batch8. Fixed: local import, and the handler now LOGS
instead of `pass`, plus a success line.

**Bug 2 — `#24-pc` deposited the counter.** Verbatim:
```
Story: counter hunt CAUGHT Machop (slot 5).
Story: training the counter — Machop L15 -> L29 (team is L39…).
Story: PC rotation — depositing Cascoon L5 …, Machop L17 (25 behind the team's best (L42))
```
A fresh counter is ~25 levels behind the team **by construction**, so it is textbook dead
weight by level. 2 of 5 counters were thrown away; **Shedinja ×2** as well. Two of my own
features were fighting each other — one fetches a low-level answer, the other deletes
low-level mons. Fixed: `plan_deposits` reads `_hunted_counter_pids` from the LIVE mode
instance and refuses those PIDs, logging each refusal. `team_policy` already protects the only
HM carrier for exactly this reason: a mon can be dead weight *by level* and still have a ROLE.

Suite 73/73.

## 2026-08-03 — BATCH 9: the counter chain works END TO END for the first time

`x4-runs/20260803-105323`, commit `b726fcd6`, VERDICT OK, 0 restarts. **27 runs, 10 finished
= 37.0%.**

### ‼ THE CHAIN COMPLETED — every link, for the first time
| | batch8 | batch9 |
|---|---|---|
| `counter registered (pid=…)` | didn't exist | **6 of 6 catches** |
| `hunted_pids>0` at the lead decision | **0 of 684** | **46** |
| `NOT depositing … hunted counter` | — | **4** |
| counter chosen as the Norman lead | **0** | **35** |
| **Norman WINS led by the counter** | **0** | **4 (MACHOP)** |

Norman victories by lead: SWAMPERT 4, **MACHOP 4**, BLAZIKEN 4, MIGHTYENA 3, SWELLOW 1,
SHEDINJA 1, DUSTOX 1. **A hunted counter has now won a boss fight — the first time in this
project.** Both bugs found this morning (the swallowed `NameError`, and the PC rotation
depositing the counter) are confirmed fixed live.

### The outcome did NOT move, and that was the stated expectation
| batch | rate |
|---|---|
| batch4 | 60.0% |
| batch5 | 47.1% |
| batch8 | 45.8% |
| **batch9** | **37.0%** (z = −0.64 vs batch8, −0.79 vs batch5) |

Indistinguishable from the plateau, at its low end. ‼ **Lane H6 contributed ZERO runs** — it
spent the whole batch hung on **KI-45** (`_select_in_menu`, 1,430 STUCK dumps), so this batch
is effectively 7 lanes. That is a direct, measurable cost of KI-45, not a rounding error.

**The conditional is the honest instrument** — runs that actually ran a counter hunt:

| batch | counter-hunt runs beating Norman | runs that never needed one |
|---|---|---|
| batch4 | 5/9 (56%) | 19/20 (95%) |
| batch5 | 6/10 (60%) | 17/19 (89%) |
| **batch9** | **4/6 (67%)** | 14/18 (78%) |

The gap between "needed a counter" and "never needed one" has closed from ~35 points to ~11.
‼ **n = 6. This resolves nothing on its own** — it is a direction, recorded as such, not a
result. It would take ~80-100 counter-hunt runs (8-10 batches) to call it.

### ⇒ NEXT: KI-45, not another feature
KI-45 has now cost a full lane in 2 of the last 4 batches. It is a pure loss, unrelated to any
feature, and it is the largest single measurable drag left. Fix it before adding anything.

## 2026-08-03 — KI-45 FIXED: a stock `while True` in the battle menu was hanging whole lanes

Chosen over more features because it is a pure loss and it was corrupting the sample size of
every measurement: it cost a full lane in **2 of the last 4 batches** — batch6 H4 (866 STUCK
dumps, 27 min silent) and batch9 H6 (1,430 dumps, **0 runs completed in 180 minutes**).

**Root cause** (stock `modules/battle_menuing.py`): `_select_in_menu` is `while True:`, pressing
a direction until the cursor read equals the target. If the menu is not open — or the read
returns anything outside 0..3 — no press can change it, and the movement logic still picks a
direction: `current_index=5` with `target_index=0` presses **"Up" forever**.

**Fix:** `_MAX_CURSOR_STEPS = 60` (~180 frames; a real selection needs ≤3 presses). On
exhaustion it reports via `battle_fault.request_mode_recovery()` — costing an opted-in mode
ONE recoverable derail instead of a Manual drop — and raises `BotModeError` only when no mode
can take it, preserving stock behaviour for every other mode.

‼ The message carries the **last cursor value**, because that is the diagnosis: out-of-range
means the menu was never open, stuck-in-range means the presses are not landing.

**Repro** `repro_ki45_cursor_bound.py` **drives the real generator** against a stuck cursor
rather than asserting on source text — a regression to `while True` hangs the test instead of
passing it. It also proves a normal selection still completes in ≤4 presses, and that the
recoverable channel is preferred when a mode opts in. Suite 74/74.

‼ **Two independent guards were structurally blind to this**: the global watchdog needs an
UNCHANGED progress signature (a menu loop keeps changing map/coords/state), and the per-run
frame budget is KI-36's documented "cannot fire while a battle handler is on the stack". Any
new `while True` on the battle path has no safety net but its own bound.

## 2026-08-03 — BATCH 10 + KI-46: the battle path has a CLASS of unbounded loops, not one bug

**Batch 10** (`x4-runs/20260803-164713`, commit `d8879750`): **21 runs, 8 finished = 38.1%** —
and again contaminated. **H8 completed 0 runs**, H2 only 2, both wedged ~59 minutes.

‼ **KI-45's bound fired 0 times**, and neither stalled lane had a single `_select_in_menu`
dump. The hang was at `battle_action_selection.py:55` — a **different site**. The KI-45 fix was
correct and simply did not apply.

**KI-46 filed and fixed:** `handle_battle_action_selection` reaches a bare
`else: yield; continue` whenever the controller callback matches none of its branches, and
spins there indefinitely. Bounded at `_MAX_UNRECOGNISED_FRAMES = 600` (~10 s), counting only
unrecognised frames and **resetting on every real decision**, so long battles never accumulate
toward it. Reports via `battle_fault.request_mode_recovery()`; the message carries **both
observed callbacks** so the missing branch can be identified rather than guessed.

‼ **The fix shipped with the very bug it was a sibling of.** `BotModeError` is not imported in
that module, so the first version would have raised `NameError` *instead of* the honest error —
exactly the swallowed-`NameError` shape that made `#24-leadcounter` silently dead for two
batches. It was caught only because the repro **drives the real generator** and explicitly
asserts the exception is not a `NameError`; a source-text check would have passed. Suite 75/75.

### The measurement problem, stated plainly
Three consecutive batches have been contaminated by battle-path hangs — batch9 (1 lane),
batch10 (2 lanes). Finish rates of 37% and 38.1% are therefore **low-side estimates on ~6.5-7
effective lanes**, not comparable to the clean 47-60% plateau. **No conclusion about the
counter chain's value can be drawn until a batch completes with all 8 lanes producing runs.**

Counter chain in batch10 (for the record, not as evidence): 5 registered, 2 protected from
deposit, MACHOP led 1 of 16 Norman wins; SHEDINJA led 7, consistent with the (c)-off ruling.

⇒ **NEXT: audit every remaining `while` loop under `BattleListener.fight`.** Two of them have
now each cost a lane, and both project-level guards are structurally blind to all of them.
Waiting for the next lost lane to find the third one is not a strategy.

## 2026-08-04 — KI-47: one net for the battle path's 32 unbounded loops

The audit that batch10 called for. An `ast` sweep of the battle path found **32 `while` loops
with no counter, no `break` and no `raise`** — and two of them had already each cost a full
lane (KI-45, KI-46).

‼ **The important discovery is why `handle_battle`'s OWN watchdog never fired.** ML-11's
no-progress counter is correct and **starved**: it only runs between iterations of its own
loop, and a sub-generator that yields for ever consumes the frames on its behalf, so
`_no_progress` never increments. That is the same starvation shape as KI-37 — and it means
every one of those 32 loops was unprotected in practice, not just in theory.

**Fix: `handle_battle._watch(subgen, label)`** wraps every sub-handler call and counts frames
**where they are actually consumed** — inside the sub-generator's yields — faulting after
`_SUBHANDLER_STALL_FRAMES = 3000` (~50 s) with the battle progress signature frozen. One net
covers all 32, **including loops not yet written**. It reports through
`battle_fault.request_mode_recovery()` so an opted-in mode takes one recoverable derail.

‼ **The net sits BEHIND the specific bounds on purpose** (KI-45 ≈180 frames, KI-46 600). A
tighter net would pre-empt them and destroy their specific diagnoses, leaving only "the battle
stopped progressing". The repro asserts that ordering explicitly.

‼ **Deliberately NOT bounding the other 30.** Most legitimately wait for the game to move on,
and 30 hand-picked bounds are 30 chances to pick a wrong one — the "obvious repair" trap this
project keeps hitting. Add a specific bound only where a real hang is observed; the net makes
waiting for that evidence safe.

Two mistakes avoided during the work, both caught by driving real code rather than reading it:
the constant was first inserted **between `@debug.track` and its function** (caught by an
`ast.parse` check), and the KI-46 fix had referenced `BotModeError` without importing it.
Suite 76/76.

## 2026-08-04 — BATCH 11: the first CLEAN batch in four, and the nets named the real culprit

`x4-runs/20260804-062303`, commit `fe4a2369`, VERDICT OK, 0 restarts.
**26 runs, 10 finished = 38.5%. ‼ ALL 8 LANES PRODUCED RUNS** (2-4 each) — the gate passes for
the first time since batch8.

### The nets worked, and 7 of 8 hits were ONE site
```
KI-47  7   handle_fainted_pokemon, frozen at 'BattleScript_FaintedMonTryChoose'
KI-46  1   controller0='CompleteOnInactiveTextPrinter2'   (at Norman)
```
Eight hangs that would previously have eaten a lane became bounded, recoverable derails.
‼ **7 of the 8 were caught by the GENERIC net, not the two specific bounds** — vindicating the
choice to build one net rather than 32 hand-picked bounds, and confirming there really is a
class of these rather than two bugs.

### ‼ THE REAL FINDING: KI-38 IS NOT FIXED
Every one of those 7 is `BattleScript_FaintedMonTryChoose` — **KI-38, the after-faint
chooser**, which this handoff has recorded as "FIXED 2026-07-31 AM" since the hang rate went
11/12 → 1/8. It was **mitigated, not fixed**, and it is still the dominant battle hang. The
KI-45/46/47 work did not fix it either — it converted an infinite lane into ~7 derails per
batch, which is a large improvement in lane availability and **not** a fix.

### The KI-46 diagnostic named its own gap
`controller0='CompleteOnInactiveTextPrinter2'` — a battle merely waiting for text to print was
counted as "unrecognised" and faulted. That is the bound working (it reported instead of
spinning) AND a real missing branch. **Fixed:** `CompleteOnInactiveTextPrinter`/`…2` are now
recognised wait states that do not count toward the bound. Safe to wait rather than bound
tightly, because the KI-47 net still backstops the handler at ~50 s.

### The finish rate, honestly
38.5% against the pooled clean plateau of **65/123 = 52.8%**, z = **−1.33** — not significant,
but below every individual plateau batch (z = −0.53 to −1.61 vs batch8/batch4). ‼ **This is
the first clean sample since the counter-chain work landed, and it does not show an
improvement.** With ~7 KI-38 derails per batch still occurring, that is unsurprising: the
lanes survive now, but the runs still pay for the wedges.

⇒ **NEXT: KI-38 for real** — it is 7 of 8 battle hangs and the largest identified drag. The
existing note says the true fix is `#24-menutext` (read the party-menu TEXT rather than
inferring from cursor indices), and KI-38's own evidence — `cursors_seen=[0,2,3,7]` in a
4-mon party — says the cursor MODEL is wrong, which no retry limit can fix.

## 2026-08-04 — KI-38: bound the party-menu cursor, self-correct it, and CAPTURE THE EVIDENCE

Batch11 made this the top item: the KI-47 net fired 8 times and **7 were this one site**
(`handle_fainted_pokemon` frozen at `BattleScript_FaintedMonTryChoose`) — ~7 recoverable
derails per 180-minute batch, the largest identified drag on the story bot.

**The site is `menuing.scroll_to_party_menu_index`, and it was another `while True`.**

‼ **The model is wrong, which is why no retry limit ever fixed it.** `gPartyMenu[9]` is not a
plain party index — KI-38's own evidence records `cursors_seen=[0,2,3,7]` in a **four**-mon
party, so the cursor also takes values that are not Pokémon slots (7 is CANCEL). The stock
rule `cursor < target -> Down` then walks the wrong way, or the value never responds, and the
loop spins (`presses={'Down': 3, 'A': 273}`).

**This does not claim to fix the model.** `#24-menutext` — read the menu TEXT instead of
inferring from an index — is still the fix. What changed:
1. **bounded** (40 presses) so it can never spin;
2. **self-corrects** — if the cursor stops responding for 6 presses it reverses direction once,
   which handles the commonest failure (a wrong direction guess from an out-of-range sentinel)
   instead of hammering one key hundreds of times;
3. ‼ **reports `cursors_seen`, the party size, and a pointer to `#24-menutext`.** That is the
   evidence `#24-menutext` needs to model the cursor correctly, and **every previous report of
   this bug lacked exactly that** — which is why four days of mitigations never converged.

Reports through `battle_fault.request_mode_recovery()` so an opted-in mode takes one
recoverable derail; raises `BotModeError` otherwise.

**Repro** `repro_ki38_party_cursor.py` drives the real generator against a cursor stuck on the
CANCEL sentinel: it terminates, raises the honest error (not a `NameError`), reports
`cursors seen: [7]`, tries **both** directions, and gives up in 40 presses rather than 273. It
also proves a normal scroll still takes exactly the presses needed and that an already-on-target
call makes none. Suite 77/77.

‼ **Expect the next batch to still show KI-38 derails.** The wedge is not gone; it is now
bounded, self-correcting and *diagnosable*. The number to watch is not whether the message
disappears but what `cursors seen` contains — that is what turns `#24-menutext` from a design
note into a change someone can make.

## 2026-08-04 — BATCH 12 + a decline that is now worth taking seriously

`x4-runs/20260804-1…`, commit `32ba1dec`. **28 runs, 10 finished = 35.7%**, all 8 lanes
producing runs (second clean batch running).

### The KI-38 cursor fix WORKS — and was not the cause
**0 `cursors seen` messages**: the reverse-direction self-correction rescues every scroll
before the 40-press bound. But the net still fired **9 times, 7 of them at the same handler**
(`handle_fainted_pokemon`, frozen at `BattleScript_FaintedMonTryChoose`) — the same count as
batch11.

‼ **Judging that fix by "did the KI-38 message disappear?" would have scored it a success.**
It did disappear. The wedge did not. The KI-47 net firing at an unchanged rate is the only
reason that is visible — a real instance of "rate of survival vs rate of occurrence", caught
this time because two independent instruments were watching.

⇒ The after-faint wedge is **not** in the cursor scroll. Next suspect is the loop *before* it:
`while … press A` waiting for `Task_HandleChooseMonInput` — i.e. **the menu never opens**,
rather than the cursor never moving. A second signature also appeared once:
`BattleScript_PrintCantEscapeFromBattle` in action selection (an un-fleeable battle).

### ‼ TWO CLEAN BATCHES NOW SHOW A DECLINE, AND IT IS NOT A DENOMINATOR ARTIFACT
| | clean plateau (b3/4/5/8) | clean recent (b11/12) | z |
|---|---|---|---|
| finish rate | **65/123 = 52.8%** | **20/54 = 37.0%** | **−1.94** |
| whole funnel Stone→Feather | 42.2% | 29.0% | −1.88 |

The obvious confound — hung lanes used to produce ZERO runs, so their failures never entered
the denominator — is **ruled out**: the badge funnel is per-badge-record, not per-run, and it
fell too. The loss is concentrated in the LAST rung:

| rung | plateau | recent | z |
|---|---|---|---|
| Stone→Knuckle | 95% | 96% | +0.27 |
| Knuckle→Dynamo | 82% | 74% | −1.21 |
| Dynamo→Heat | 95% | 92% | −0.78 |
| Heat→Balance | 81% | 80% | −0.20 |
| **Balance→Feather** | **71%** | **56%** | **−1.63** |

**Post-Norman is where it is lost.** `#24-leadpolicy` option **(a)** is ruled out as a cause —
it is inert: **0 of 723** logged lead decisions contained a `NOATK` candidate, so it has never
demoted anything.

⇒ **NEXT: BISECT, do not add anything.** Candidates between batch8 (45.8%) and batch11/12 are
`#24-pc` (gated), `#24-areaitemgate`, `#24-leadcounter`, and the KI-45/46/47/38 bounds. The
bounds convert hangs into derails, which is a plausible mechanism for *more completed-but-
failed runs* — but the funnel drop says play itself got worse post-Norman, which points at
`#24-areaitemgate` (it changed where the bot trains) or `#24-leadcounter` (it changed who
leads at Winona). Run one batch per suspect from a reverted build; do not guess.

## 2026-08-04 — THE DECLINE IS FOUND: `#24-areaitemgate` killed the bot's only training relocation

Bisecting the 52.8% → 37.0% decline (pooled z = −1.94). Two corrections to my own earlier
analysis on the way, both worth recording because each would have sent the bisect the wrong way:

1. I said the suspects were `#24-areaitemgate` and `#24-leadcounter` "between batch8 and
   batch11". **Wrong** — both were already in batch8's build, which scored 45.8%, on-plateau.
2. I said the funnel loss was between batch8 and batch11. **Wrong** — a PER-BATCH funnel (not
   pooled) shows Balance→Feather at **83% / 75% / 70%** in batch3/4/5 and **52-59%** from
   batch8 on. The drop is between **batch5 and batch8**.

Pooling had hidden the step change. The per-batch table is now the first thing to compute.

### The cause, measured
| batch | `relocating to ROUTE111` | Balance→Feather |
|---|---|---|
| b3 / b4 / b5 (gate off) | 19 / 12 / **24** | 83% / 75% / 70% |
| b8…b12 (gate ON) | **0** | 52-59% |

**ROUTE111 (L19-22) is the ONLY training relocation this bot ever performs.** `#24-areaitemgate`
refused it without Go-Goggles to eliminate 28 wasted treks per batch — and eliminated all 24
successful relocations with them. Real success rate before the gate: ~43% (24 vs 32). After:
zero. The team stopped being levelled for the post-Norman band and the last rung collapsed.

**Fix:** the gate is now behind `POKEBOT_AREA_ITEM_GATE`, **default OFF**. `AREA_ITEM_PREREQ`
stays — the Go-Goggles fact is correct game knowledge, it is simply not worth enforcing here,
because the failures it targets are ALREADY bounded by `_note_training_unreachable` (one
wasted trek per RUN, not per attempt). Suite 77/77.

‼ **SECOND TIME IN A WEEK.** `#24-leadpolicy` (c) removed a Shedinja lead winning 39% of Norman
fights; this removed the only training relocation. Both were REMOVALS justified by counting a
behaviour's failures and never its successes — and after the first one I wrote the prevention
rule into `08-MISTAKES` and then failed to apply it to the second. The failure line
(`dropping it as a training option`) prints; the success line (`relocating to`) is silent
unless you go looking. New rule recorded: **grep the positive counterpart of every failure
line you are about to eliminate.**

## 2026-08-04 — BATCH 13: the prediction was HALF right, and my own falsifier says keep bisecting

`x4-runs/20260804-174700`, commit `ad7307f2`. **27 runs, 12 finished = 44.4%.** All 8 lanes
produced runs.

| signal | predicted (written first) | actual | |
|---|---|---|---|
| `relocating to ROUTE111` | > 0, order 10-25 | **12** | ✅ |
| Balance→Feather | **> 65%** | **57%** | ❌ |
| finish rate | toward 45-55% | 44.4% | ✅ |

**The gate WAS blocking relocation** (0 → 12) and removing it recovered the finish rate from
35.7/38.5% to 44.4%, back level with batch8. ‼ **But Balance→Feather did not recover**, and the
falsifier recorded before the run says plainly: *"if relocations return but Balance→Feather
does NOT, the gate was not the cause"*. It was **a** cause, not **the** cause.

### The second signal, which the bisect must now follow
| batch | reloc | no-better | **fodder detected** | B→F |
|---|---|---|---|---|
| b3 | 19 | 114 | **133** | 83% |
| b4 | 12 | 167 | **179** | 75% |
| b5 | 24 | 146 | **170** | 70% |
| b8 | 0 | 73 | **73** | 52% |
| b12 | 0 | 99 | **99** | 53% |
| **b13 (gate off)** | **12** | 58 | **70** | **57%** |

`is fodder for a … team` — the bot deciding the local patch is worthless and looking for
better — fired **133-179 times** in b3/4/5 and only **70-99** since, **including b13 with the
gate off**. Normalised per run it is ~5.0/run then vs ~2.6/run now. So the bot now *considers*
relocating about half as often, and removing the item gate did not restore that.

⇒ **NEXT SUSPECT: `#24-relocfloor`** — the other change in the batch5→batch8 window that
touches training. It altered the floor fed to `best_training_area`, and the fodder test
consults a probe built from the same call. Flag it off and re-batch, exactly as with the last
two. **Do not add anything until Balance→Feather is back above 65%.**

‼ Two flags now hold reverted-because-measured behaviour and must stay `0`:
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD`, `POKEBOT_AREA_ITEM_GATE`.

## 2026-08-05 — `#24-pc` flagged OFF: it removed ~1 team member per run

The second cause of the Balance→Feather collapse, found by testing team COMPOSITION rather
than guessing at the next commit.

| batch | PC deposits | avg team size at Feather | Balance→Feather |
|---|---|---|---|
| b3 / b4 / b5 (off) | 0 | **5.65 / 5.72 / 5.81** | 83 / 75 / 70% |
| b8 (on) | 14 | **4.45** | 52% |
| b13 (on) | 18 | **4.75** | 57% |

`#24-pc` permanently removes about **one whole team member**, and the last rung fell over
exactly that transition — less depth post-Norman is less depth for Winona. It bought 5
unblocked counter hunts per batch; it cost ~1 mon on every run.

**Now behind `POKEBOT_PC_ROTATION`, default OFF.** `repro_pc_trip.py` keeps every existing
guard (gate at party≥6, protect the hunted counter, never below `MIN_PARTY_AFTER_ROTATION`,
PIDs-not-slots) — those checks now opt in explicitly, because the behaviour they pin is still
required if the flag is ever turned back on. Suite 77/77.

‼ **`#24-relocfloor` was RULED OUT without a batch**: the fodder-detection probe uses
`min_wild_max=local_max`, not the floor it changed, so it cannot affect that path. Reading the
call site beat spending 3 hours.

### THREE flags now hold reverted-because-measured behaviour — all must stay `0`
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD`, `POKEBOT_AREA_ITEM_GATE`, `POKEBOT_PC_ROTATION`.

All three were features that REMOVE or RESTRICT something, each justified by a visible failure
count with no corresponding success count, and each with the counter-evidence already sitting
in logs on disk:

| feature | counted | never counted |
|---|---|---|
| `#24-leadpolicy` (c) | 1 Shedinja loss | 12 Shedinja WINS |
| `#24-areaitemgate` | 28 wasted treks | 24 successful relocations |
| `#24-pc` | 5 blocked hunts | ~1 team member every run |

**Next batch predicts:** team size at Feather back toward ~5.7, and Balance→Feather **> 65%**.
If team size recovers and the rung does NOT, a third cause remains and the bisect continues
into `#24-leadcounter` (the only untested change left in the batch5→batch8 window).

## 2026-08-05 — REGRESSION CLOSED. Bisect ends here; story content resumes.

`x4-runs/20260805-075638`, commit `054fa8c6`, all 8 lanes producing runs.
**25 runs, 13 finished = 52.0%.**

| signal | b3/4/5 (healthy) | b8-b13 (regressed) | predicted | **actual** |
|---|---|---|---|---|
| PC deposits | 0 | 14-18 | 0 | **0** ✅ |
| relocations to ROUTE111 | 19/12/24 | 0 | > 0 | **15** ✅ |
| avg team at Feather | 5.65-5.81 | 4.45-4.75 | ~5.7 | **5.85** ✅ |
| **Balance→Feather** | 70-83% | 52-57% | **> 65%** | **76%** ✅ |
| whole funnel | 42.2% (pooled) | 28-36% | — | **42%** ✅ |
| finish rate | 47-60% | 36-44% | 45-55% | **52.0%** ✅ |

**Finish rate 52.0% against the clean plateau's 52.8% — fully recovered.** Every number the
prediction named landed inside its band, which is the strongest form of confirmation available
here: the causal story (two features silently removing things the bot needed) predicted five
independent quantities before the run, and all five came back.

### The three reverts, and what each cost
| feature | counted | never counted | recovered |
|---|---|---|---|
| `#24-leadpolicy` (c) | 1 Shedinja loss | 12 Shedinja WINS | ~20 pts finish rate |
| `#24-areaitemgate` | 28 wasted treks | 24 relocations | ~7 pts finish rate |
| `#24-pc` | 5 blocked hunts | ~1 team member/run | ~19 pts of the last rung |

‼ **STOPPING RULE SATISFIED** (`06-DECISIONS-LOG` 2026-08-05, user directive):
Balance→Feather ≥ 65%, so the regression is CLOSED and **regression-hunting ends here**. Next
work is STORY CONTENT past Winona. Only a logic-breaking bug — hang, crash, run-ending derail,
or a feature provably not doing what it says — reopens this.

‼ Three flags stay `0` permanently unless re-measured with a batch:
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD`, `POKEBOT_AREA_ITEM_GATE`, `POKEBOT_PC_ROTATION`.

## 2026-08-05 — `#24-pcoverflow`: a full party no longer refuses a catch (user ruling)

**User report that started this:** live runs still show teams of 4, and the "catch even if it
overflows into the PC" behaviour appeared not to work.

**Confirmed for the user: it was never built, and they were not running a stale script.** Two
separate things:
1. `target_size: int = 4` (and `_catch_team_target = 4`) — the party cap. Still the
   punch-list item *"party cap 4 → 6 + PC rotation — ALREADY DESIGNED, BUILD IT"*.
2. PC-overflow catching — the code did the OPPOSITE: `resource_blocker()` **refused** to hunt
   when `_party_count() >= 6`, explicitly deferred behind `#24-pc`.

**User ruling: build the real feature**, not a raised constant. Both halves, shipped together:

* **`resource_blocker` no longer refuses a full party.** The ball gate is untouched. Verified
  by AST, not text — the removed rule is still described in a comment right there, and a
  `"party is full" in source` check passes either way (it did, on the first attempt).
* **`pc_trip.box_views()` / `find_in_box()` / `withdraw_from_box()`** — read the PC, locate a
  Pokémon **by PID** (a box slot moves whenever anything is deposited), and collect it on the
  next Poké Centre heal, piggybacked between the nurse and the exit.

‼ **THE TWO HALVES ONLY MAKE SENSE TOGETHER.** Relaxing the refusal alone would be strictly
WORSE than the refusal: the counter would be caught — paid for with a cross-Hoenn journey —
and then sit in the box unusable. `repro_pc_overflow.py` asserts the wiring, not just the
functions.

‼ **It frees exactly ONE slot, and only when the party is full.** That is deliberate, not
conservatism: `#24-pc` thinned parties by ~1 mon per run and cost ~19 points of the
Balance→Feather rung. A generous withdraw would reintroduce that regression by another door.
It also refuses to deposit the very mon it came to collect, and gives up cleanly ("leaving it
boxed") when nothing is safe to deposit.

The decision layer was already there and unused: `team_policy.rotation_plan()` has taken
`box_views` and returned a `withdraw` list since it was written. What was missing was reading
the box and executing the withdraw. Suite 78/78.

‼ **NOT YET LIVE-PROVEN.** No run has caught into a box or driven a withdraw. The next batch
should show `PC — withdrawing <mon> from the box`, and the counter chain should stop reporting
`cannot hunt a counter — the party is full`. **The party cap is still 4** — raising it is a
separate change and would interact with this one, so it is deliberately not bundled here.

## 2026-08-05 — `#24-partycap`: the pre-Gym-1 team fill goes 4 → 6

**What changed (2 constants, both pre-Gym-1):**
* `modules/story/early_game.py` — `catch_starter_team(target_size: int = 4)` → `6`.
* `plugins/custom_modes/story_mode.py` — `self._catch_team_target = 4` → `6`.

**Why.** The user watches live runs and reported 4-mon teams on 2026-08-05. These two
constants are the reason; nothing else was capping the party.

**Why NOW and not last week.** `#24-pcoverflow` landed earlier the same day. Before it, a full
party made `resource_blocker` REFUSE every subsequent catch, so a cap of 6 would have shut the
counter chain off at exactly the moment the chain is load-bearing — the chain is worth ~19
points of the last badge rung. The two changes are coupled, which is why ONE batch measures
both rather than two batches measuring one each.

**Scope was checked before editing, not assumed.** Both use sites are gated pre-Gym-1: the
catch-new predicate at `story_mode.py:1051` returns `False` once `BADGE01_GET` is set, and
`catch_starter_team` is only called from the pre-Gym-1 chapter. So this moves WHEN the team
reaches 6, not whether the bot catches late. Team size at badge moments was already ~5.8.

**Verification.** `repro_pc_overflow`, `repro_team_policy`, `repro_survival_mode`,
`repro_counter_hunt` all PASS. ‼ Worth recording: **no repro pinned the production constant** —
the four repros that mention `_catch_team_target` each build their own `SimpleNamespace` shim
and set the value themselves. Nothing had to be un-asserted, and equally nothing defends the
new value. That is correct per the playbook (assert on behaviour, not source text); the batch
is the instrument here.

‼ **NOT MEASURED YET.** This entry records a code change, not an outcome. See the handoff for
the batch and the four signals to read. **If team size rises but the finish rate falls, revert
the CAP, not the overflow** — a deeper team is not free (more mons to heal, more to train), and
that exact trap has cost this project three regressions in one week.

## 2026-08-05 — `#24-cavethread` RE-SCOPED by static recon, and a probe written

**No production code changed.** This entry records a measurement and a plan change.

**What was measured.** `#24-cavethread` was about to be built as a hand-written multi-hop cave
chain table, on the premise that `_CAVE_EXITS`/`_CAVE_ENTRANCES` are single-hop and therefore
the route data for deep interiors does not exist. Replaying `WarpGraph.map_route` (BFS over
connections + warp edges) against the committed ROM-derived cache `cache/warp_graph_BPEE0.json`
— **no emulator, no ROM, no CPU contention with the running batch** — shows the graph already
knows every route, both directions:

| route | hops |
|---|---|
| `ROUTE106 -> GRANITE_CAVE_B2F` | 3 |
| `GRANITE_CAVE_B2F -> DEWFORD_TOWN` | 4 |
| `ROUTE122 -> MT_PYRE_SUMMIT` | 3 |
| `JAGGED_PASS -> MAGMA_HIDEOUT_4F` | 4 |

Map names were taken by **`ast.parse` of `map_data.py`**, never a bulk import — `modules/data`
runs generators at import and has gutted that file twice.

**Why the premise was stale.** The two tables date from 2026-07-26 and their justifying comment
reads *"the global navigator can NOT cross warp levels"*. True when written; **fixed five days
later by `#24-journey` (2026-07-31)**, which made `navigate_to_anywhere` multi-hop, self-
replanning and live-validated. `_navigate_riding_out` — which the training and hunting paths
already call — wraps it. So the tables are a legacy PRE-STEP that manually threads one door
before handing off to a navigator that now threads doors by itself.

‼ **WHAT THIS DOES NOT PROVE, stated so it is not mistaken for a result.** It refutes "the route
data is missing". It does **not** prove the bot can walk the route. `map_route`'s own docstring
warns its connection edges can be **phantoms** — the measured Verdanturf->Route116 case, where a
declared connection exists and 0 of 40 sampled tiles are actually walkable. Route known ≠ route
walkable, and treating one measurement as settling both is precisely the KI-39 error.

**The named risk.** `_walk_warp_chain` documents a **one-way ledge** on Granite Cave 1F: within-
floor reachability is DIRECTIONAL, so the graph's single `GRANITE_CAVE_1F` node is really two
disjoint sections. A map-granular planner cannot see that. The generic navigator's `used_warps`
+ revisit-deprioritisation is a plausible but unproven mitigation for it.

**Shipped: `--driver cavethread`** in `tools/story-dev/story_harness.py` (new `CaveThreadMode`).
Drives the PRODUCTION call (`_navigate_riding_out`) in two legs — IN to a deep interior, then
OUT to a heal town — and reports `[cavethread] RESULT leg=<in|out> arrived=<bool> map=<...>`.
Three deliberate design choices:
* **Destination tiles are the warp graph's own ROM `to_coords`** (where the game says you ARRIVE
  when taking that warp), so they are walkable by construction and nothing is written from memory.
* **Granite Cave is the test case on purpose** — same 3-warp depth as Mt. Pyre Summit, already
  parked for this, and it carries the hardest known hazard (the ledge). Passing it generalises.
* **The OUT leg is SKIPPED unless we actually got inside**, and says so. An out-leg driven from
  the overworld would trivially report `arrived=True` and read as a pass.

Verified by AST parse only (the box is running a batch). ‼ `story_harness.py` has a **UTF-8 BOM**
— parse it with `encoding='utf-8-sig'` or `ast.parse` raises on U+FEFF.

**Outcome if it passes:** `#24-cavethread` collapses from "build a chain system" to "delete two
stale tables", and Mt. Pyre unblocks. **If it fails:** the log names the leg and the map, which
is the actual thing to fix. Either way the next step is minutes of measurement, not days of build.

## 2026-08-05 — `#24-partycap` MEASURED AND REVERTED. The party's empty slots are the HM RUNWAY.

**Batch `20260805-122057`, code `be104e9c`, 8 lanes / 180.1 min, VERDICT OK, 27 headers
checked, 0 violations, 0 lane restarts.** Baseline: `20260805-075638` (`054fa8c6`), 52.0%.

| | baseline (cap 4) | cap 6 |
|---|---|---|
| finish rate | **13/25 = 52.0%** | **3/19 = 15.8%** |
| mean team size at Feather | 5.85 | 6.00 |

### ‼ THE FUNNEL IS WHAT MADE THIS DIAGNOSABLE — one rung moved, and only one

| rung | baseline | cap 6 | z |
|---|---|---|---|
| Stone→Knuckle | 28/31 (90%) | 25/26 (96%) | flat |
| Knuckle→Dynamo | 24/28 (86%) | 18/25 (72%) | −1.23, ns |
| Dynamo→Heat | 22/24 (92%) | 18/18 (100%) | flat |
| Heat→Balance | 17/22 (77%) | 14/18 (78%) | flat |
| **Balance→Feather** | **13/17 (76%)** | **3/14 (21%)** | **3.06** ✅ |
| Stone→Feather | 13/31 (42%) | 3/26 (12%) | |

**A deeper team is FREE through five badges.** The entire 36-point loss sits on the single
rung where **Surf** becomes mandatory. Had this been read on finish rate alone, the obvious
(and wrong) conclusion was "deeper teams cost more to heal and train" — the trap the handoff
pre-registered. The funnel says the opposite: strength was never the issue.

### ROOT CAUSE — HM coverage, not team strength

`end_reasons`: **10 of 16 non-finishes** are
`No party mon can learn Surf and the party is full`. A party pre-filled with early-route wilds
(Skitty / Mightyena / Loudred / Ninjask / Taillow) has **no Surf learner and no slot to catch
one**, so the run derails at the Surf gate and ends.

**Control (this is what makes it attributable, not suspected):** that message appears **0
times** in all 14 preceding batches, including the immediate 52.0% predecessor. It appears in
exactly one other batch ever — the original 2026-07-31 baseline.

‼ **THE INSIGHT WORTH KEEPING: the empty slots were never waste — they are the RUNWAY the HM
and counter catches land on.** At cap 4 the team still reaches a mean of **5.85** by the
Feather Badge. It fills up either way. Letting early wilds take the seats first is what breaks
it, because the mons that MUST board later (a Surf learner, a Fighting counter) then cannot.

‼ `#24-pcoverflow` does NOT rescue this, and the reason is worth stating: it lets a catch
overflow into the BOX, but a Surf learner in a box cannot be taught Surf. The guard refuses
before any catch is attempted. `withdrawing` logged **0** times all batch — **the overflow path
still has no live proof**, and this batch could never have supplied it.

### REVERTED — both constants back to 4

Per the rule pre-registered in the handoff BEFORE the data was seen ("if team size rises but
the finish rate falls, revert the CAP, not the overflow"). Both sites now carry a
do-not-raise-this comment naming the batch, the rung and the mechanism. 4 repros green.

**What is NOT reverted:** `#24-pcoverflow` stays. It was never implicated — it simply never
fired.

### The real fix, if deeper teams are still wanted (NOT built, needs a ruling)

The cap is not the lever; **HM-slot reservation** is. Options, unpriced:
1. **Reserve slots** — cap the pre-Gym-1 wild fill at 4 and let HM learners / counters claim
   the rest, which is what already happens organically (4.00 → 5.85). Lowest risk.
2. **Make room on demand** — let the HM path deposit a non-essential mon so a Surf learner can
   board. ‼ This is what the guard's own message asks for ("needs PC box management"), but it
   is the shape of `POKEBOT_PC_ROTATION`, which is disabled for costing ~19 points by
   depositing team members. Do not build it without reading that first.
3. **Cap 5** — one free seat for the Surf learner. Plausible, entirely unmeasured, needs a batch.

## 2026-08-05 — `#24-cavethread` PROBED LIVE: multi-hop threading WORKS, and stops one hop short

`story_harness.py dewford.ss1 --driver cavethread --frames 600000`, target `GRANITE_CAVE_B2F`.

```
[cavethread] leg=in from=DEWFORD_TOWN to=GRANITE_CAVE_B2F(29, 13) graph_hops=4
[cavethread] RESULT leg=in arrived=False map=GRANITE_CAVE_B1F detail=returned on the wrong map
```

### ‼ THE STALE-COMMENT FINDING IS CONFIRMED LIVE, NOT JUST STATICALLY

The bot went **DEWFORD_TOWN → ROUTE106 → GRANITE_CAVE_1F → GRANITE_CAVE_B1F** — a route
connection plus **two cave warps** — driven entirely by the generic `_navigate_riding_out` /
`navigate_to_anywhere` path, with **no chain table involved**. The `_CAVE_EXITS` comment
claiming *"the global navigator can NOT cross warp levels"* is therefore **false today**, and
`#24-cavethread` does **not** need a hand-built chain system to represent deep routes.

### WHERE IT ACTUALLY STOPS — one hop short, standing ON the ladder

It halted on **GRANITE_CAVE_B1F at (29,13)**, which `_FROM_STEVEN` documents as *the ladder
DOWN to B2F*. So it reached the correct final ladder and did not take it. That — not route
representation — is the real `#24-cavethread` defect, and it is a much smaller target.

‼ **A FLAW IN MY OWN PROBE, recorded so the next run does not inherit it.** I derived the
destination tile from the warp graph's `to_coords` and got **(29,13)**, which is one of the
worst possible test coordinates here: B1F(29,13) and B2F(29,13) are a warp PAIR at *identical
coordinates*, so "right coords, wrong floor" is indistinguishable from "arrived" by coordinate
alone. The probe survived only because it asserts on **MAP**, not coordinates. **Re-run with an
unambiguous interior B2F tile before drawing a firm conclusion about the ladder** — the current
evidence cannot fully separate "the ladder warp never fired" from "the navigator believed it had
arrived because the coordinates matched".

**Status: `#24-cavethread` is re-scoped and now has a live measurement.** Not "build a chain
system" (refuted twice, statically and live); it is "make the last ladder hop fire". Mt. Pyre
Summit is the same 3-warp shape, so this one defect very likely gates it too.

## 2026-08-05 — USER RULING `#24-hmslots` = reserve slots; deeper teams deferred to `#24-organicteam`

Closes the question `#24-partycap` opened. **No code change** — the ruling ratifies the reverted
behaviour (fill to 4, grow organically to a measured mean 5.85 by Feather). Recorded as a ruling
specifically so a future session does not read the open item as unfinished and re-raise the cap.

The user attached intent that matters more than the choice: this is a **holding position**, and
the goal is to revisit it so the bot "plays more organically like a regular player would", once
the story is mapped and there is time to do it properly. Tracked as `#24-organicteam`, gated on
story mapping. **Accepted cost meanwhile: teams look thin early — the original complaint, and
knowingly unsolved.** Rationale and the three rejected options: `06-DECISIONS-LOG.md` 2026-08-05.

## 2026-08-05 — ‼ `#24-cavethread` IS NOT A BLOCKER. Multi-hop cave threading ALREADY WORKS.

**Measured both directions with `--driver cavethread`, no chain table involved:**

```
[cavethread] leg=in  from=DEWFORD_TOWN      to=GRANITE_CAVE_B2F(29,13)  graph_hops=4
             reached_dest=True
             maps visited: DEWFORD_TOWN, ROUTE106, GRANITE_CAVE_1F, GRANITE_CAVE_B1F, GRANITE_CAVE_B2F
[cavethread] leg=out from=GRANITE_CAVE_B1F  to=DEWFORD_TOWN(17,14)      graph_hops=3
             reached_dest=True
             maps visited: GRANITE_CAVE_B1F, GRANITE_CAVE_1F, ROUTE106, DEWFORD_TOWN, DEWFORD_TOWN_HOUSE1
```

The generic `_navigate_riding_out` / `navigate_to_anywhere` path threaded **3 warps deep into
Granite Cave and back out to Dewford**. `MT_PYRE_SUMMIT` is the same 3-warp shape, so the item
that has been recorded as **"THE BLOCKER FOR ALL STORY CONTENT PAST WINONA"** is refuted.

### ‼ THE REAL GOTCHA — never pass a WARP TILE as a navigation destination

Both probe runs first read as FAILURES (`arrived=False`), and both were my probe's fault:
* IN: B2F (29,13) is a **ladder back up**, so stepping on the target warped the bot to B1F.
* OUT: DEWFORD_TOWN (17,14) is a **door**, so the bot finished inside `DEWFORD_TOWN_HOUSE1`.

**Walking onto a warp FIRES it**, so a warp-tile destination ends one map PAST the target — and
`navigate_to_anywhere` returns SUCCESS, because by its own lights it reached the tile it was
given. This is not hypothetical: 188 of 1268 graph edges (14.8%) have identical from/to
coordinates, so a coordinate-only arrival check cannot even detect the bounce.

**The probe now records the maps VISITED** (`tracked()`), which answers the real question
without needing a non-warp tile to exist — and every tile the graph knows on B2F is a ladder,
so no such tile was available from that source.

### What changed in code
Only the stale `_CAVE_EXITS` comment, corrected in place with the measurement. **The tables are
kept**: they are redundant now, not load-bearing, but harmless and cheap (they thread one door
via `_enter_warp_by_navigation`, which handles warp tiles correctly). Deleting them is a
behaviour change and would need its own measurement; nothing needs it today.

### Consequences
* **`#24-mtpyre` is UNBLOCKED** — it was waiting on this and the capability already exists.
* **Granite Cave B1F/B2F can be unparked** as training/hunting grounds (they were parked for
  exactly this reason, and it once dropped two real-hardware runs to Manual).
* ‼ Whoever builds Mt. Pyre: **pick plain walkable destination tiles, never ladders or doors.**

## 2026-08-05 — `#24-postwinona-save` DONE, and the Mt. Pyre blocker is RELOCATED to Route 120

### The save exists now — `tools/story-dev/saves/post_winona.ss1`
Generated by driving Story from `fortree_gym_wedge.ss1` (`--profile mkpostwinona`, 829,648
frames): `RUN COMPLETE — end of built content reached`. Winona fell on roughly the 11th attempt
to a L42 Mightyena. **Party: Mightyena L42 / Sceptile L42 / Swellow L39 / Skitty L17 /
Zigzagoon L3 / Castform L35 — and Zigzagoon knows SURF**, so the HM is aboard.
‼ Earlier in the same run a `"Delete a move to make room for WEATHER BALL?"` prompt repeated for
long enough to look like a move-learn wedge. **It was not** — it resolved itself and the run
continued. Recorded so the next agent does not chase it.

### ‼ THE ONE-CALL HYPOTHESIS IS REFUTED — and the failure names the real blocker
`--driver cavethread CAVE_TARGET=MT_PYRE_SUMMIT CAVE_TILE=23,7` from `post_winona.ss1`:
```
RESULT leg=in arrived=False reached_dest=False map=ROUTE120
detail=UnreachableDestinationError: Could not reach (23,7) on MT_PYRE_SUMMIT:
       the field is idle and we are still at (7,56), so retrying cannot change the result
maps visited: FORTREE_CITY, FORTREE_CITY_GYM, ROUTE120
```

**So `_navigate_riding_out(MT_PYRE_SUMMIT, (23,7))` is NOT the whole chapter.** The trip leaves
Fortree, reaches ROUTE120, and dies at **(7,56)** — before it ever gets near a cave warp.

‼ **THIS IS NOT A WARP-THREADING FAILURE.** Warp threading was proven working earlier today
(Dewford ⇄ Granite Cave B2F, 3 warps, both directions). The blocker for Mt. Pyre is **overland
pathing across ROUTE120 → ROUTE121**, which is a different problem in a different place.
Ruled out already: `calculate_path` takes `no_surfing: bool = False`, so **surfing is permitted
by default** and `_walk_is_possible` does not disable it — the party's Surf is not being ignored
at the API level.

**Next diagnostic, in this order:**
1. What is at ROUTE120 (7,56)? Dump it (`PROBE_MAPS=ROUTE120 mapfacts.py`) — Route 120 is split
   by a river and has the Kecleon/Scorched Slab area, so a split-section or an obstacle is the
   prime suspect. This is the `_staged_progress_warp` shape (ROUTE104 split by Petalburg Woods).
2. Probe `_navigate_riding_out(ROUTE121, <plain tile>)` alone — shorter trip, cleaner signal.
3. Only then re-test the full summit call.

**Added `CAVE_TILE` to the `cavethread` driver** so a PLAIN destination tile can be forced; every
tile `arrival_tile()` can derive from the warp graph is itself a warp, which is the wrong kind
of target (it fires on contact).

### ‼ ROUTE 120 (7,56) DIAGNOSED — the bot strands in a pocket chasing the ANCIENT TOMB warp

`PROBE_MAPS=ROUTE120 mapfacts.py` — ROUTE120 is **40x100** with exactly TWO warps:
```
warp[0] (7, 55)  -> ANCIENT TOMB  (8,29)
warp[1] (19, 23) -> SCORCHED SLAB (7,16)
```
The stall tile **(7,56) is directly below the Ancient Tomb door**, and the terrain shows why
that is fatal:
```
y 54 .##..#####..######...
y 55 .##..##W##..######...   <- W = (7,55) ANCIENT TOMB
y 56 ..............####...   <- bot stranded here
y 57 ..............####...
```
A wall at **x=12-17** runs down the map, so (7,56) sits in a **WESTERN POCKET** whose only
special exit is that warp. **ANCIENT TOMB is a sealed Regi chamber** — a dead end that needs the
Braille/Regi puzzle — so the pocket leads nowhere useful.

‼ **This has the exact shape of the `_staged_progress_warp` failure `#24-journey` was built for**
(ROUTE104 split in two by PETALBURG_WOODS): the planner takes any warp that does not increase
graph distance, walks to it, and re-plans. Here that walked the bot INTO a pocket. `onward_exits`
is supposed to deprioritise dead ends — **Ancient Tomb has exactly one exit, so it should have
been ranked last.** Why it was chosen anyway is the open question, and it is a bug in staged
progress, not in Mt. Pyre.

**Do NOT "fix" this by hard-coding a Route 120 waypoint.** Gateway waypoints were tried and
refuted (KI-39, 2026-07-30). The question to answer first is why a 1-exit dead end outranked the
real route — instrument `_staged_progress_warp`'s ranking at that decision.

### ‼ CORRECTION (same day) — I OVERSTATED THE ROUTE 120 DIAGNOSIS. "Sealed pocket" is NOT established.

The entry immediately above claims (7,56) sits in a **western pocket whose only exit is the
Ancient Tomb warp**. **Retracting the "sealed" half.** It was inferred from a 17-row slice of a
**100-row** map. Printing rows 56-99 shows the western column continues south to at least y≈68
and the map opens eastward further down, so the terrain does **not** plainly support "sealed",
and I am not going to defend a connectivity claim built by hand-parsing 100 rows of ASCII —
that is precisely the error-prone recall this project has a rule against.

**WHAT SURVIVES (ROM warp data, not inference):**
* ROUTE120 is 40x100 with exactly TWO warps: `(7,55) -> ANCIENT TOMB`, `(19,23) -> SCORCHED SLAB`.
* The bot stalled at **(7,56)**, which is **directly below the Ancient Tomb door**. Adjacency to
  the only nearby warp remains a strong hint that warp selection walked it there.
* ANCIENT TOMB is a sealed Regi chamber, so it is a dead end **as a destination** regardless of
  how the bot arrived.

**WHAT IS NOT ESTABLISHED:** that the bot was trapped, that staged progress chose the tomb, or
that terrain caused the failure. ‼ **Also note the ranking code argues AGAINST the tomb having
been chosen at all:** `_staged_progress_warp` filters any edge whose `map_distance(to_map,
target) > here_distance`, and Ancient Tomb's only exit is back to ROUTE120, so its distance to
MT_PYRE_SUMMIT is strictly greater — it should have been filtered before `onward_exits` ever
mattered. A theory the code contradicts needs measurement, not more reading.

**THE ACTUAL NEXT STEP — instrument, do not infer.** From `post_winona.ss1`, log inside
`navigate_to_anywhere`: which branch is taken, the `scored` list `_staged_progress_warp` builds,
and the exact `calculate_path` error. The surfaced error was truncated at 160 chars by the
driver — **raise that truncation first**, the full text likely names the failing leg.

‼ **Prevention rule: a terrain claim read off a PARTIAL map dump is a guess.** Print the whole
map or say "unknown". The first version of this entry would have sent the next session hunting a
trap that may not exist — the same failure shape as the cavethread probe earlier today, where a
confident negative turned out to be my own instrument.

### ✅ ROUTE 120 — THE ACTUAL ERROR, and it supersedes both earlier readings

Raising the driver's error truncation from 160 → 800 chars produced the diagnosis in one run:
```
UnreachableDestinationError: Could not reach (23,7) on MT_PYRE_SUMMIT:
  the field is idle and we are still at (7, 56), so retrying cannot change the result
  (Could not find a path from (7/56 @ ROUTE120) to (22/29 @ ROUTE122).)
```

**The navigator's chosen LEG is `ROUTE122 (22,29)`** — the Mt. Pyre door, the first warp of the
route. It walked to **ROUTE120 (7,56)** and from there `calculate_path` could not reach that leg.

**So the failure is a LEG-VALIDITY / POSITION problem, not a warp-threading one and not the
Ancient Tomb.** The tomb adjacency was a coincidence of position; the bot was never trying to
enter it. ‼ Both earlier readings of this failure were wrong, and the fix for both was the same
30-second change: **stop truncating the error.**

**The sharp question now, and it is a clean A/B:** does
`calculate_path(ROUTE120 -> ROUTE122 (22,29))` succeed from FORTREE / northern ROUTE120 and fail
from (7,56)? If yes, the leg validated when chosen and the bot then walked itself somewhere the
leg no longer validates — legs are validated once at selection, and the trip crosses ROUTE121
and a SURF leg on ROUTE122, with wild battles re-planning along the way (the run logged many
mid-trip `PARTY CHANGE` lines). That is a real staged-progress defect: **a leg is validated from
where you STAND, then pursued from wherever you END UP.**

‼ Note `calculate_path` spans only DIRECTLY CONNECTED maps. ROUTE120→ROUTE122 is two connections
(via ROUTE121), so whether that call can EVER succeed is itself worth measuring before assuming
position is the variable.

**Next:** run that A/B from `post_winona.ss1` (probe `calculate_path` from Fortree, from northern
ROUTE120, and from (7,56)). It separates "the leg was never reachable" from "the bot ruined its
own position", and those have completely different fixes.

### ‼‼ ROUTE 120 — ROOT CAUSE FOUND. The navigator cannot WALK ACROSS A MAP CONNECTION as a step.

**Measured from the stall save (`saves/stalls/repro-pyre2-f33678.ss1`, standing at ROUTE120 (7,56)),
via a new `CAVE_PATHCHECK` mode that asks `calculate_path` directly without walking:**

| target | result |
|---|---|
| `ROUTE121 (10,10)` | **OK — 79 waypoints** |
| `ROUTE122 (22,29)` ← the leg the navigator chose | **FAIL** |
| `ROUTE120 (20,90)` (far south, same map) | **OK — 49 waypoints** |
| `ROUTE120 (7,47)` (**9 tiles NORTH**) | **FAIL** |

**The bot was never stuck.** Route 121 was reachable the whole time.
(Bonus: (7,47) unreachable from (7,56) confirms a one-way LEDGE there — the terrain is
directional, which is why the earlier "pocket" instinct felt right. It is not a trap; south and
east are open.)

### The mechanism, in order
1. **Fast path fails** — `MT_PYRE_SUMMIT (23,7)` is not walkable from ROUTE120. Correct.
2. **`pick_leg` correctly REJECTS** the `ROUTE122 (22,29)` warp: `_walk_is_possible` says no, and
   it is right — `calculate_path` spans only **DIRECTLY CONNECTED** maps, and ROUTE120→ROUTE122
   is **two** connections (via ROUTE121). No walkability warning was logged, so this was a clean
   `PathFindingError`, not the exception fallback.
3. **`_staged_progress_warp` returns None** — and this is the gap. It scans
   `graph.warps_from(...)` only. **ROUTE120→ROUTE121 is a map CONNECTION, not a warp**, so there
   is no edge for it to offer. It has no way to express *"just walk south into the next route."*
4. **`global_navigation.py:417` then takes the leg UNVALIDATED:**
   ```python
   if region_route:
       # ...Take it unvalidated — this is precisely today's behaviour, so this
       # change can never make a cross-region journey that works now start failing.
       leg = region_route[0]
   ```
   That hands `navigate_to` the ROUTE122 tile it already knows is unreachable, which raises, and
   the whole journey dies **while a 79-waypoint path to Route 121 sat available.**

### ‼ THE FIX SHAPE (not built — measure it, then build)
Give staged progress a **CONNECTION step**: when no warp validates, walk to a reachable tile on
the **next map along `graph.map_route(current, target)`**, then re-plan. The loop already turns
partial progress into a journey — this is the connection analogue of `_staged_progress_warp`,
which only ever learned the warp half. The measurement above says it would have worked here on
the first try.

‼ **Do NOT just delete the unvalidated `region_route[0]` fallback.** Its comment claims it
preserves today's working cross-region journeys; removing it blind is the exact
remove-a-behaviour-because-a-failure-is-loud move that cost this project three regressions in a
week. Add the connection step FIRST so the fallback stops being reached, then measure whether it
is still load-bearing.

## 2026-08-05 — `#24-connstep`: the navigator can now WALK ACROSS A MAP CONNECTION as a step

**The fix.** New `_connection_step()` in `modules/modes/util/global_navigation.py`. When neither
warp picker validates a leg, it walks to a reachable tile on the **next map along
`graph.map_route()`** — but only when that hop is a genuine map CONNECTION — then lets the loop
re-plan. This is the connection analogue of `_staged_progress_warp`, which only ever learned the
warp half.

**LIVE A/B — same build, same save (`post_winona.ss1`), one variable** (`CAVE_ARM` monkeypatches
`_connection_step` to `None` for the old arm):

| arm | ends at | maps visited |
|---|---|---|
| **old** | ROUTE120 (7,56) | FORTREE_CITY, FORTREE_CITY_GYM, ROUTE120 |
| **new** | ROUTE121 (21,5) | FORTREE_CITY, FORTREE_CITY_GYM, ROUTE120, **ROUTE121** |

**The bot crosses a border it previously could not.** Repros green: `journey_planner`,
`navigate_failfast`, `navigate_stuck`, `smashrock_battle_wedge`, `smashrock_parked_script`,
`cave_exit_table`, `watchdog_budget_collision`.

### Two design choices, both deliberate
* **It sits AFTER both warp pickers and BEFORE the unvalidated `region_route[0]` branch**, so
  that branch stops being REACHED rather than being deleted. Its comment claims it keeps working
  cross-region journeys alive; that claim is untested either way, and deleting a behaviour
  because its failure is loud is what cost three regressions in one week. Leave it.
* **It never offers a WARP TILE** as the step target (walking onto one fires it), and it counts
  against `legs_taken` so an oscillation between two maps stays bounded.

### ‼ NOT DONE — the honest limits
* **NOT batch-validated.** Live A/B only, exactly like KI-43/KI-44 shipped. `navigate_to_anywhere`
  is used everywhere, so a batch must run before this is trusted or promoted.
* **Tile choice is a coarse lattice** — the first walkable, non-warp, `calculate_path`-validated
  sample. It is not aimed at the onward route, so it can land somewhere with less onward
  reachability than an ideal tile. No stranding was observed (ROUTE121 (21,5) is in a broad open
  corridor, not an island), but it is a real weakness worth revisiting.
* **Mt. Pyre is still not reachable** — the journey now dies one border later, at
  **ROUTE121 → ROUTE122**, which is an open-water SURF crossing.

### ‼ NEXT — and do NOT repeat my error here
`calculate_path` from ROUTE121 (21,5) failed to ROUTE122 (22,29)/(10,10)/(20,20) **and** to
LILYCOVE_CITY (20,20). I briefly read that as "nothing is reachable, the bot is stranded" —
**wrong**: those target tiles were picked arbitrarily and may simply be WALLS or water. The
Route 121 dump shows (21,5) sits in a wide open corridor.
**Re-run the check with COLLISION-VERIFIED target tiles** (take them from `mapfacts.py`, which
prints the passability grid) before concluding anything about the surf crossing. An arbitrary
target tile is not a measurement — that is the third time today an arbitrary tile produced a
false negative.

### ‼ CORRECTION (same day) — `#24-connstep` IS GATED **OFF**. It crossed the border and then STRANDED the bot.

The entry above reports the connection step reaching ROUTE121 and calls the weak tile choice a
theoretical concern. **It is not theoretical — it is the failure.** Measured from the new arm's
own stall save, standing at the tile the step chose, ROUTE121 (21,5):

| target | result |
|---|---|
| `ROUTE122 (22,30)` / `(10,0)` / `(30,32)` / `(3,3)` / `(22,29)` — all collision-verified | **all FAIL** |
| **`ROUTE121 (10,19)` / `(20,19)` / `(0,19)` — its OWN south edge** | **all FAIL** |
| `ROUTE121 (22,12)`, `(25,16)` — same map | **FAIL** |

**Not the surf border at all.** Route 121 has a north band and a south band that do not connect
in the sampled region, and the step put the bot in the north one. ‼ **The lattice scans `y` from
the TOP, so it is systematically biased toward NORTHERN tiles — the wrong end when the target is
south.** "First walkable tile" is a coin flip, and here it lost.

**Gated behind `POKEBOT_CONNECTION_STEP` (default `0`).** Verified: with the gate off the trip
reproduces the pre-change behaviour EXACTLY (dies at ROUTE120 (7,56), same maps visited), so the
default path is untouched and the regression risk is zero. 5 navigation repros green.

‼ **WHY OFF RATHER THAN LEFT ON:** `_connection_step` runs BEFORE the unvalidated
`region_route[0]` branch, so it can DIVERT journeys that succeed today. `navigate_to_anywhere` is
used by every chapter — that is a whole-game regression vector, on a change with no batch behind
it. "It cannot be worse, the journey fails anyway" is true only for THIS journey.

**To finish it (both needed before enabling):**
1. **Aim the tile choice at the onward route** using `map_path.py`'s global map `offset`/`level`
   (`PathTile.global_coordinates`) — pick the candidate nearest the next map along the route,
   instead of the first walkable one.
2. **Remember rejected step targets** (the `used_warps` pattern) so a re-plan offers a different
   tile rather than re-deriving the same one.
Then batch it against the **52.0%** baseline.

‼ **The lesson, and it is the same one twice in one session:** I wrote "it can land somewhere
with less onward reachability" as a caveat and shipped it anyway. **A caveat you can state is a
test you can run.** The measurement that demoted this from "works" to "gated off" took four
minutes and used a save the failing run had already written.

### `#24-connstep` — aiming implemented, and it is STILL not enough. Surf is RULED OUT.

**Implemented both items the previous entry demanded**, still behind `POKEBOT_CONNECTION_STEP=0`:
1. **Aimed tile choice** — `_global_aim_point()` reads `map_path`'s per-map global `offset` and
   `level` and sorts candidates by distance to the centre of the map AFTER next (not the final
   target, which is an interior map on a different `level` and therefore not comparable).
2. **`used_steps`** threaded through `navigate_to_anywhere`, so a re-plan cannot re-derive the
   same tile — the `used_warps` lesson.

**Result: it now does not cross at all.** With aiming on, the trip dies at ROUTE120 (7,56) —
identical to the old arm. The southern ROUTE121 candidates it now prefers are **not reachable
from ROUTE120's entry point**, so all six validations fail and it returns None.

| variant | outcome |
|---|---|
| unaimed | crosses to ROUTE121, then **strands** in the north band |
| **aimed** | **never crosses** — southern candidates unreachable from the entry point |
| gate off (default) | unchanged pre-existing behaviour |

### ‼ SURF IS RULED OUT AS THE CAUSE — measured, not assumed
```
[cavethread] SURF-GATE BADGE05_GET=True party_has_surf=True
```
`calculate_path.can_surf()` gates every water tile on exactly those two, and both are TRUE, so
**surfing is permitted by the planner.** The earlier suspicion that "Route 121 → 122 needs a surf
capability the planner lacks" is **wrong** — do not go looking for one.

### ⇒ WHAT THIS ACTUALLY MEANS (the honest boundary)
From ROUTE121 (21,5) — the north band, where the ROUTE120 connection lands — `calculate_path`
reaches **neither ROUTE121's own south edge nor any ROUTE122 tile**, with surf allowed. So the
north band is a genuine dead end *for this journey*, and no tile-selection heuristic inside
`_connection_step` can fix that: the problem is not WHICH tile on Route 121, it is that the
reachable part of Route 121 does not connect onward.

**The remaining question is topological, and needs data rather than another heuristic:** the
Route 121 dumps so far cover only x=0-46 of an **80-wide** map. The north band may join the south
band further EAST. **Dump the full width and run a reachability sweep from (21,5)** (the
`calculate_path`-per-sampled-tile method used for KI-39's partial-reachability figures) before
touching `_connection_step` again.

‼ **STOP TUNING THE HEURISTIC.** Two variants, two different failures, both inside the same
unmeasured assumption — that Route 121 is traversable from where we enter it. **Measure the map
first.** This is the "four failures, one fitted cause" shape from KI-39 in a new costume.

## 2026-08-05 — ‼‼ THE MT. PYRE BLOCKER IS A **STORY GATE**, NOT NAVIGATION. `#24-r121gate`

**Route 121's north band is sealed by THREE TEAM AQUA GRUNTS standing in the only corridor
south.** Everything else today — cave threading, ladder hops, staged progress, connection steps
— was chasing a navigation defect that was never the cause.

### The evidence chain (each step measured, none inferred)
1. **Full-width ROUTE121 dump** (80 wide; every earlier dump showed only x=0-46 — that omission
   is why this took so long). It reveals a vertical corridor at **x=30-31** running from y≈9 down
   to y=15, the only link from the north band to the south band.
2. **The corridor's top tiles are OBJECTS**: `(30,7)`, `(31,7)`, `(30,8)`, each
   `graphics_id: OBJ_EVENT_GFX_AQUA_MEMBER_M`, `script: 0x0`, `flag:
   FLAG_HIDE_ROUTE_121_TEAM_AQUA_GRUNTS`.
3. **Flag identified from our own data**, not recall — `event_flags/emerald.txt:764` →
   `914 HIDE_ROUTE_121_TEAM_AQUA_GRUNTS`.
4. **Read LIVE from the save: `HIDE_ROUTE_121_TEAM_AQUA_GRUNTS = False`** — the grunts are
   VISIBLE and blocking. (`mapfacts.py` shows the map as AUTHORED, so this check was required.)
5. **`calculate_path` confirms the seal:** from ROUTE121 (21,5), corridor tiles (30,12) and
   (31,10) are unreachable, as is Route 121's whole south edge and every ROUTE122 tile —
   **with surf allowed** (`BADGE05_GET=True`, `party_has_surf=True`, both measured).

### ‼ THE FIX IS FOUR TILES AWAY — a coord trigger, exactly like Mt. Pyre's
`data/maps/Route121/map.json`:
| trigger tiles | var gate | script |
|---|---|---|
| **(25,5) (25,6) (25,7) (25,8)** | `VAR_ROUTE121_STATE == 0` | `Route121_EventScript_AquaGruntsMoveOut` |

`Route121_EventScript_AquaGruntsMoveOut` walks the three grunts off, `removeobject`s all three,
and sets `VAR_ROUTE121_STATE = 1`. **The corridor then opens.**

**And the bot was stranded at ROUTE121 (21,5) — `calculate_path` to (25,5) is `OK, 6 waypoints`.**
It sat six steps from the trigger that unblocks the whole chapter, and no amount of navigator
tuning could ever have found it: the pathfinder sees a wall of NPCs, not a scene to fire.

### ⇒ WHAT THIS MEANS FOR THE BUILD
The Mt. Pyre chapter is a normal hand-coded leg sequence, not a generic journey:
1. `ROUTE121 (25,5)` — **fires the grunt trigger**; guard on `VAR_ROUTE121_STATE >= 1`.
2. `ROUTE122 (22,30)` — the plain tile BELOW the Mt. Pyre door (never target the door itself).
3. `MT_PYRE_1F` → `EXTERIOR` → `MT_PYRE_SUMMIT (23,7)` — the summit trigger (§Ch14a).
Steps between directly-connected maps are what `calculate_path` handles natively, which is
precisely why explicit legs work where "navigate to the summit" failed.

‼ **`#24-connstep` stays GATED OFF.** It is not needed for this chapter and it is still
unvalidated. The reason the generic call failed was never the missing connection step — it was
that the destination was unreachable for a story reason.

‼ **THE LESSON — and it is the biggest one of the session.** I spent hours treating an
UNREACHABLE DESTINATION as a pathfinding defect. **When the pathfinder says "no path", ask what
is STANDING there before asking what is wrong with the pathfinder.** A blocked corridor and a
broken planner produce the identical error string. The distinguishing check — dump the map, look
at the objects, read their hide flags live — costs minutes and was available from the first hour.

## 2026-08-06 — ‼ MT. PYRE IS BUILT AND LIVE-PROVEN. First new story content past Winona.

**The bot now plays past the end of previously-built content.** Two new chapter functions in
`modules/story/early_game.py`, wired as Segment 14 in `story_mode.py` after the Gym 6 guard:

* **`open_route121_aqua_gate()`** — walks onto `ROUTE121 (25,5)`, the coord trigger that runs
  `Route121_EventScript_AquaGruntsMoveOut`. Three Team Aqua grunts sealing Route 121's only
  corridor south move out; `VAR_ROUTE121_STATE` → 1.
* **`do_mt_pyre_summit()`** — `ROUTE122 (22,30)` → door (22,29) → `MT_PYRE_1F (3,6)` →
  `EXTERIOR (19,10)` → summit, then walks the x=23 corridor to `(23,7)`, the trigger that runs
  `MtPyre_Summit_EventScript_TeamAquaExits`.

### ‼ LIVE PROOF — end to end, from `post_winona.ss1`, 76,368 frames
```
Story: MAGMA EMBLEM obtained - end of built content.
RUN COMPLETE — end of built content reached; the bot is idle by design, not hung.
```
**End state verified against the decomp**, read live from the resulting save (now committed as
`tools/story-dev/saves/post_mtpyre.ss1`) — every flag `TeamAquaExits` sets is True:

| flag | value |
|---|---|
| `HIDE_ROUTE_121_TEAM_AQUA_GRUNTS` | **True** (grunts moved out) |
| `HIDE_MT_PYRE_SUMMIT_TEAM_AQUA` | **True** (summit scene ran) |
| `RECEIVED_RED_OR_BLUE_ORB` | **True** |
| **`HIDE_JAGGED_PASS_MAGMA_GUARD`** | **True — the Magma Hideout is now OPEN** |

Final position: standing on `MT_PYRE_SUMMIT (23,7)`. 8 repros green.

### Design decisions worth keeping
* **Explicit adjacent-map legs, not one generic journey call.** `calculate_path` spans only
  DIRECTLY CONNECTED maps, so `navigate_to_anywhere(MT_PYRE_SUMMIT, …)` from Fortree commits to
  a leg two connections away and fails — measured repeatedly on 2026-08-05. A chain of
  adjacent-map legs is what the pathfinder handles natively.
* **`_done_var()` added to `story_mode.py`, mirroring `_done`'s fail-loud rule.** `get_event_var`
  returns **-1** for an unknown name, so a typo does not read False — it reads a number that
  compares False against every threshold, forever, silently. It now raises on a phantom name.
  Both var names were checked against `modules/data/event_vars/emerald.txt` before use
  (`ROUTE121_STATE` 116, `MT_PYRE_STATE` 185).
* **Completion gated on `MT_PYRE_STATE`, never on flag 856** (`HIDE_MT_PYRE_SUMMIT_MAXIE`) —
  this project already caught 856 reading True far from Mt. Pyre, and the decomp explains it.
* **The 2F-6F interior tower is deliberately not entered** — a skippable side dungeon, not on
  the critical path.
* **Never navigate TO a warp tile.** Leg 1 targets `ROUTE122 (22,30)`, the plain tile BELOW the
  door, because walking onto a warp fires it.

### ‼ NOT DONE
**No batch.** Every run that beats Winona now continues into this segment, so the endless-reset
finish rate and run length both change. Batch against the **52.0%** baseline before treating the
finish rate as comparable — `#24-mtpyre-batch`.

## 2026-08-06 — `#24-mtpyre-batch`: Segment 14 MEASURED IN PRODUCTION. It holds.

**Batch `20260806-055947`, code `498eedd9`, 8 lanes / 180.1 min, `VERDICT OK`, 32 headers
checked, 0 emulation violations, 0 lane restarts.** Baseline: `20260805-075638` (52.0%).

### ‼ SEGMENT 14 RUNS IN PRODUCTION — and completes 9 times out of 10 that reach it
Debug logs (collected at batch end) confirm the traversal is real, not inferred:
**`MT. PYRE` 274 mentions, `ROUTE 121` 171, `ROUTE 122` 89.**
**9 runs finished with the Magma Emblem, against 10 runs that reached the Feather Badge — a
~90% conversion on the new segment.** Zero `BotModeError` from either new guard
(`Route 121:` 0, `Mt. Pyre:` 0).

### ‼ THE FINISH RATE FELL 52.0% → 37.5% AND THAT IS NOT A REGRESSION
"Finished" now REQUIRES Mt. Pyre as well as six badges, so the two numbers measure different
things. The badge funnel — every rung of which is UPSTREAM of the new code — is the honest
comparison, and **not one rung moved significantly:**

| rung | baseline | Mt. Pyre build | |
|---|---|---|---|
| Stone→Knuckle | 28/31 (90%) | 29/32 (91%) | flat |
| Knuckle→Dynamo | 24/28 (86%) | 23/29 (79%) | ns |
| Dynamo→Heat | 22/24 (92%) | 23/23 (100%) | flat |
| Heat→Balance | 17/22 (77%) | 19/23 (83%) | flat |
| Balance→Feather | 13/17 (76%) | 10/19 (53%) | **z = 1.49, ns** |
| Stone→Feather (whole) | 13/31 (42%) | 10/32 (31%) | **z = 0.88, ns** |

Balance→Feather is directionally down, but it is **the Winona rung — upstream of Segment 14,
which cannot affect it** — and `Winona: no super-effective answer to Dragon/Flying` is 4 of the
15 non-finishes. That is the long-standing Winona weakness, not new damage.

### ‼ THE WHITEOUT UPTICK IS NOT MT. PYRE'S — measured, not assumed
`too many whiteout recoveries in a row` was the top end reason (5 of 15) and rose from 2 in the
baseline, so I suspected the four Aqua-grunt trainers in the summit corridor. **Refuted by a
per-run correlation:** one run logged **0 `MT. PYRE` mentions and 3 whiteouts**, while several
runs with heavy Mt. Pyre presence (14-20 mentions) logged none. Whiteouts occur independently of
Segment 14. Left as an open item; **do not attribute it to Mt. Pyre.**

### Method note worth keeping
Mid-batch I checked `*/debug-logs/*.log` for map names, got **zero hits**, and briefly took that
as "runs finished without visiting Mt. Pyre". **The directories are EMPTY until the batch ends** —
the runner collects them at teardown. That was absence of LOGS, not absence of evidence.
‼ **Do not run map-presence checks against a live batch's `debug-logs/`.** Use `stdout.txt`
mid-flight, and the debug logs only after `VERDICT OK`.

### `#24-mtpyre-log` — Segment 14's milestones now reach stdout

The batch proved Segment 14 works but **every progress line read 0**: the five milestones were
`context.message` only, which the GUI shows and a headless lane's stdout never sees. Had the
segment failed mid-way there would have been a guard error and **no trace of how far it got**.

New `_ch14_say()` sets the message AND `console.print`s it; all five milestones route through it.
Verified live from `post_winona.ss1` — all five now appear, and the run completes in **76,367
frames, identical to before the change**, so this is purely observability. 5 repros green.

‼ **Rule: a chapter's milestones are its only in-flight diagnostic — PRINT them.** A
`context.message` that never reaches stdout is invisible to every batch, which is exactly where
a chapter's failures will be found.

## 2026-08-06 — `#24-hmteachloop` FIXED (Fix A). The teach never looped; the BUDGET expired early.

**User report:** *"the hm learning feature works but it still loops trying to teach/get out of the
teaching cycle after it teaches an hm."* Real bug, and the diagnosis overturned the obvious theory.

### ‼ THE TEACH FLOW DOES NOT LOOP. The chapter LADDER replays.
`teach skipped` = **611** across batch `20260806-055947` is **ladder-replay depth**, not HM events.
Proof: `Dynamo Badge already earned` == `HM06 already received` == `already knows Rock Smash` ==
**448 exactly**. Three unrelated predicates cannot share a count unless the number means "how many
`_play()` restarts got this deep." Restart drivers: **590 whiteouts + 138 derails**. Clustering test:
**0 of 611** skip lines lack a `resuming`/`new game` header within 40 lines — bursts, not a spin.

### THE REAL BUG — a premature-timeout FALSE NEGATIVE
`early_game.py` rode the post-teach dialogue on a flat `for _f in range(3000)`. In **7 of 19 Surf
teaches** it expired **while the teach was still progressing**, raised
`Teach flow finished but <mon> does not know Surf`, and the move was learned
**1,867-1,878 frames later** (σ≈4) in *every* case. The raise derails → `_play()` restarts at the
top of the ladder → the whole "already done" litany reprints. **That reprint is what the user saw.**

**Why exactly those 7:** all start with the **Norman battle tail** resident
(`callback=ReturnFromBattleToOverworld`), stretching the dialogue chain past 3,000 frames.
| path | n | fails |
|---|---|---|
| Rock Smash (quiet map) | 23 | **0** |
| Surf → freshly-hunted L3 Zigzagoon (free move slot, no replace dialogue) | 12 | **0** |
| **Surf → in-party 4-move mon (Swampert/Marshtomp/Linoone)** | **7** | **7** |

### THE FIX — a progress-aware budget, both bounds required
* `_TEACH_RIDE_HARD_CAP = 9000` — **ABSOLUTE**. Never "loop while progressing": this generator is
  re-entered by the derail dispatcher, and unbounded-while-progressing is the KI-34 shape that
  burned 23.9M frames. 1.85× the worst legitimate observed path (4,875).
* `_TEACH_RIDE_STALL_FRAMES = 900` — aborts when the task set ∪ learn-state ∪ the target's move
  list is unchanged. In all 7 failures that signature changed every few hundred frames, so a
  genuinely dead menu still dies fast.

‼ **The raise at the end is KEPT.** It is the only in-flow detector of a real failed teach and it
names the mon and move. Deleting a guard because its failure is loud is behind three reverts.
‼ **REJECTED: a settle-and-recheck (300-600 frames + re-check) before the raise** — it would have
fixed **0 of 7**; they needed ~1,872 frames. The ride budget was the only correct knob.

### ‼ TWO NEAR-MISSES WHILE WRITING IT, both the same shape
I referenced `get_learn_move_state` unimported, and used `from modules.debug import debug_logger`
(the module is `modules/debug_logger.py`). **In both cases the surrounding `except Exception` would
have swallowed the error and silently disabled the thing I had just added** — a stall detector that
never detects, telemetry that never emits. Both are now explicit imports with the near-miss recorded
inline. *A bare `except` around a NEW import is a silent-failure generator.*

### ‼ TELEMETRY: the old HM counters are UNUSABLE as a baseline
`already knows Surf` (163) and `already knows Rock Smash` (448) count replay depth. Inflation **5.1×
and 14×**, and **not constant** — it scales with how often that game whited out, so no fixed divisor
corrects it. Ground truth from `[STEP]`: **19 Surf + 23 Rock Smash teaches**. Closing check:
`Surf already received (182) − already knows Surf (163) = 19` — exactly the Surf teach count.
⇒ Added `debug_logger.event("TEACH OK <mon> learned <move> in <N> frames")`. Without it the fix is
provable only by the ABSENCE of an error, and a suppressed feature looks identical to a working one.
(`[STEP] '…learned…'` measured **0** against 42 real teaches — `context.message` is overwritten by
the next segment before `[STEP]` can fire. Positive control: `got HM06 Rock Smash!` is also 0.)

### ‼ VALIDATION STATUS — PARTIAL, stated plainly
Live from `norman_done.ss1`: **`TEACH OK Zigzagoon learned Surf in 85 frames`**, `Teach flow
finished but` = **0**. That proves the instrumentation works and the change does not regress the
easy path — **but 85 frames on a hunted L3 Zigzagoon IS the easy path (12/12 clean before the fix).**
That save's party (Blaziken/Shedinja/Mightyena) has no Surf-capable mon, so it hunted rather than
teaching an in-party 4-move mon. **The failing case was not exercised.**
⇒ **PRE-REGISTERED PROOF, to be read off the next batch:** `Teach flow finished but` **7 → 0** on
`*/debug-logs/*.log`, with `TEACH OK` ≈ 42 (proving teaches were not suppressed rather than fixed).
A mudkip lane reaches the Marshtomp path naturally.

### Cost, measured honestly
The ladder replay is near-free (no unconditional `yield` in a fully-done pass; ~114 frames median
per replay = **0.095%** of the batch). This bug's own cost is **~32,800 frames (0.039%)** plus 7 of
the 4-derail budget. ‼ **The real frame burn is 590 whiteouts (~18/game)** — a team-strength problem,
logged separately. The user's "wastes frames" perception is console spam plus 7 visible re-entries;
the spam itself is Fix B, not yet done.

## 2026-08-06 — ‼ `#24-pcoverflow` HAD TWO INDEPENDENT BREAKS. One is fixed and proven.

`withdrawing` has logged **0** in every batch since the feature shipped. The changelog blamed
"the Surf guard killed runs first". **Both of those explanations were wrong.** There are two
structural breaks, and EITHER ALONE guarantees zero:

### BREAK 1 (FIXED, PROVEN) — `box_views()` raised `TypeError` on every call
`pc_trip.box_views()` read:
```python
for box in getattr(storage, "boxes", lambda: [])():      # <-- calls the result
```
`PokemonStorage.boxes` is a **`@cached_property` returning a list** (`pokemon_storage.py:86`), so
this was `list()` → `TypeError: 'list' object is not callable`, **every time**. `find_in_box`
calls `box_views()` **unguarded**, so `withdraw_from_box` could never find anything.

**Proven live**, new `CAVE_BOXCHECK` probe on `post_mtpyre.ss1`:
```
BEFORE  BOXCHECK storage.pokemon_count=0 boxes_type=list
        BOXCHECK box_views() RAISED TypeError: 'list' object is not callable
AFTER   BOXCHECK box_views() OK -> 0 views, 0 mons
```

‼ **THE DEFENSIVE DEFAULT DISGUISED THE BUG.** `getattr(storage, "boxes", lambda: [])()` reads as
"be safe if `boxes` is missing" — and the fallback it supplies is a **callable**, which is exactly
what made calling the real attribute look correct. **A defensive default that changes the SHAPE of
the value is not defensive; it is camouflage.** Prevention rule added to `08-MISTAKES.md`.

### BREAK 2 (NOT YET FIXED) — the catch itself still cannot happen with a full party
Both catch-on-sight branches still require `party < 6`
(`story_mode.py:1876` counter, `:1844` HM), and `counter_hunt.hunt()`'s success test is entirely
party-based (`_party_count() > before`, `party_counter_slot(...)`, returns a PARTY slot). So with a
full party the hunt travels, arms, spins the full 120,000-frame budget, catches the counter into
the box (the game does this automatically — `GiveMonToPlayer` → `CopyMonToPC`, no prompt), and
reports "found nothing" — registering no PID, which `withdraw_from_box` is gated on.

**Landed but NOT YET WIRED** (helpers only, no behaviour change): `counter_hunt._box_count()` and
`counter_hunt.box_counter_pid(needed_types, exclude_pids)` — the box-side twin of
`party_counter_slot`, keyed on **PID** because box indices shift. Both fail toward "no change" so
they cannot fake a success.

‼ Note `box_counter_pid` had to avoid the SAME two traps: `boxes` is a property (no parens) and
`box.slots` holds `PokemonStorageSlot` **wrappers** — the mon is `slot.pokemon`. Inside its `try`,
either mistake would return None and read as "no counter in the box".

**Next:** wire Break 2 — allow the full-party catch, make the hunt's success test see a box catch,
and register the boxed PID so the existing withdraw path collects it at the next heal.

## 2026-08-06 — `#24-pcoverflow` BREAK 2 WIRED. A full party now overflows to the box and is collected.

With break 1 fixed (`box_views` raised `TypeError`), this closes the other half. Three connected
changes, one behaviour:

**1. The counter catch-on-sight branch no longer requires `party < 6`** (`story_mode.py`). The
ball gate stays — that is a resource rule, unrelated to party space. A full-party catch is fully
automatic in Emerald (`Cmd_givecaughtmon` → `GiveMonToPlayer` → `CopyMonToPC`, no prompt), the
shiny branch already relies on it, and 14×30 = 420 slots vs ~202 species means overflow is not a
real risk. If the PC ever were full the game refuses to throw the ball — a no-op, not a loss.

**2. `counter_hunt.hunt()` can now SEE a box catch.** It snapshots `_box_count()` and `_box_pids()`
before spinning; `_stop()` treats a box-count increase as success. New `box_counter_pid()` is the
box-side twin of `party_counter_slot`, keyed on **PID** because box indices shift.
‼ The PID snapshot is load-bearing: without it a counter stored by an EARLIER boss would be
reported as this hunt's catch and the ladder would "succeed" having caught nothing.

**3. Return contract widened** (one call site, so this is cheap and explicit):
`{"slot": int, "pid": int}` party catch · `{"slot": None, "pid": int}` box catch · `None` nothing.
A dict rather than a sentinel int, because a boxed catch has no party slot and a sentinel would be
indexed eventually.

**4. The caller registers the PID for BOTH cases** and, for a boxed catch, **skips training** —
a boxed mon earns no XP. It is collected at the next heal by `pc_trip.withdraw_from_box`, arriving
UNTRAINED. That is a known gap and still strictly better than the old behaviour, which was to
refuse the catch and end the run.

### ‼ THE REPRO CAUGHT THE CONTRACT CHANGE, AND THEN CAUGHT A LATENT BUG
`repro_counter_hunt` failed with `'int' object has no attribute 'get'` — the stub still returned a
bare slot. Correct behaviour from the suite. Then, with the stub fixed, it failed again:
`stand-in 'self' has no '_hunted_counter_pids'`.

‼ **That attribute was ALWAYS missing from the stub, and nothing noticed** — because the old
registration sat inside a broad `except Exception` that swallowed the `AttributeError`. It is the
same shape that made the registry always empty in production (batch8 printed `hunted_pids=0` on
**all 684** lead decisions). Moving the registration OUT of the try surfaced it immediately.
**A bare `except` around bookkeeping does not protect the feature; it hides whether the feature
exists at all.**

### Test changes, both deliberate
* **Case 12 INVERTED**: was *"a FULL party is not counter-caught"* — the rule that made the whole
  feature dead. Now asserts the catch DOES happen and overflows. This is a behaviour change with a
  batch to grade it, not a test bent to pass.
* **New cases 19b/19c/19d**: a boxed catch succeeds and does **not** train; its PID **is**
  registered (what `withdraw_from_box` is gated on); a party catch still trains and still registers.

7 repros green (`counter_hunt`, `pc_overflow`, `counter_huntable`, `counter_training_budget`,
`team_policy`, `survival_mode`, `hm_move_replace_loop`).

### ‼ NOT YET PROVEN LIVE — the pre-registered grade
No run has caught into a box and collected it. **Next batch must show:**
| counter | now | ship if |
|---|---|---|
| `withdrawing` | **0** | **≥1** — the primitive finally executes |
| `INTO THE PC BOX` (new) | n/a | ≥1 — the catch path fires |
| `no super-effective answer` (non-finishes) | **8 of 12** | ≤5 of 12 |
| **mean team size at Feather** | **~5.80** | **≥5.7 — the `#24-pc` canary; it fell 5.8→4.5 there** |
Also still owed on that batch: `Teach flow finished but` **8 → 0** (`#24-hmteachloop`).

## 2026-08-06 — batch `20260806-142418`: BOTH pre-registered grades FAILED. Overflow gated off.

`VERDICT OK`, 34 headers, 0 violations. **26 runs, 8 finished = 30.8%** (baseline `5a84c2ca`:
25 runs, 13 = **52.0%**). `global watchdog` **20 → 68**.

| grade | baseline | target | actual | verdict |
|---|---|---|---|---|
| `withdrawing` (stdout) | 0 | ≥1 | **0** | **FAIL — never fired** |
| `INTO THE PC BOX` (stdout) | n/a | ≥1 | **0** | **FAIL — never fired** |
| `Teach flow finished but` (debug) | 8 | **0** | **9** | **FAIL — second attempt** |
| `TEACH OK` (debug) | 40 | ~40 | 42 | ok — teaches not suppressed |

### The overflow path is GATED OFF — for delivering nothing, NOT for proven harm
`POKEBOT_BOX_OVERFLOW_CATCH`, default `0`. ‼ **I am not claiming it caused the regression, and
the data does not support that claim.** Of **43** watchdog STUCK dumps: **22 at party 4, 11 at
party 5, 10 at party 6.** Only 10 could possibly involve this gate; 33 are in states where it has
no effect. The wedges are battles with a mostly-dead team stuck on
`BattleScript_PrintCantEscapeFromBattle` with **no battle controller on the stack** — a
battle-handler shape, not a catch shape.

### ‼ WHY IT COULD NEVER HAVE WORKED — the user found the gap, the decomp confirmed it
A box-send shows an **EXTRA TEXT BOX** the party-catch path never shows, and **the bot has no
handling for it at all**: `grep` for `VAR_PC_BOX_TO_SEND_MON` or "sent to" across
`sandbox-pokebot/modules/` returns **ZERO**. `Cmd_givecaughtmon`
(`src/battle_script_commands.c:10055`) selects one of **four** variants —
`B_MSG_SENT_SOMEONES_PC` / `B_MSG_SOMEONES_BOX_FULL`, each `+1` once `FLAG_SYS_PC_LANETTE` is set.
**Detect the box from `VAR_PC_BOX_TO_SEND_MON`, not by parsing text** — the variable is immune to
all four wordings. Until that message is dismissed, every full-party catch risks wedging the
battle exit.
‼ **The same gap applies to `StoryShinyCatchStrategy`**, which claims to catch duplicates into the
box and has almost certainly never been exercised.

### ‼ I BUNDLED TWO CHANGES AGAIN — the mistake I keep writing rules about
This batch carried BOTH the `#24-hmteachloop` second attempt AND the overflow wiring. So the
30.8% and the watchdog tripling **cannot be attributed to either one**. `#24-partycap` +
`#24-pcoverflow` had exactly this problem, and I recorded the lesson from it two days ago.
**The next batch must carry ONE change.**

### `#24-hmteachloop` is 0-for-2 and needs a different approach
7 → 8 → **9**. Attempt 1 (budget raise + stall detector) failed because the stall detector fired
early. Attempt 2 (budget raise alone, 9,000 hard cap) still fails. Since `TEACH OK` durations are
**35-86 frames** for every success, the failures are not "slightly too slow" — **something else
ends the ride**, and the budget was never the knob. ‼ **Do not raise the cap a third time.**
Re-diagnose: instrument the exit reason (which `break` fired, at what frame, with what task set)
before changing anything.

**Repro now asserts BOTH gate arms** (off = pre-2026-08-06 behaviour; on = catch happens), so
neither side can rot and the flag cannot silently become a no-op.

---

## 2026-08-07 — `#24-pcwithdraw-proof`: the WITHDRAW half of `#24-pcoverflow` is LIVE-PROVEN

The catch half shipped yesterday: a full party no longer blocks a catch, and the mon lands in the
PC box. That is **strictly worse than the old refusal** unless the bot can get it back out, and
`withdraw_from_box` had logged `withdrawing` **0 times in every batch ever run**. Two known breaks
were fixed on 2026-08-06 (`box_views` calling a `@cached_property`; both catch branches requiring
`party < 6`), but the collect path itself remained unexecuted code. It now executes.

**New: `--driver boxwithdraw` in `tools/story-dev/story_harness.py`,** plus the fixture save
`tools/story-dev/saves/boxwithdraw.ss1` (a copy of `profiles/repro-boxcatch6/current_state.ss1` —
the end state of the proven box-catch run: party 6, box 2 = Poochyena L26 + Shuppet L26).

```
cd tools/story-dev
PYTHONUTF8=1 WITHDRAW_CENTER=LilycoveCity py -3.12 story_harness.py \
    boxwithdraw.ss1 --driver boxwithdraw --frames 400000 --profile w1
```

**Result — three consecutive runs, frame-identical:**

```
[boxwithdraw] box read: 2 views / 2 mons — ['PoochyenaL26', 'ShuppetL26']
[boxwithdraw] target=Poochyena L26 pid=2982930983
Story: PC — depositing Skitty L17 to make room for Poochyena.
Story: PC — withdrawing Poochyena from the box.
Story: PC — Poochyena is in the party; party is now 6.
[boxwithdraw] RESULT withdrew=True target=Poochyena party_before=6 party_after=6
              box_before=2 box_after=2 deposited=True map=(0, 5)
[boxwithdraw] AFTER usable=True second_heal_ok=True still_has_target=True party=6 box=2
```

Party `[Mightyena, Zigzagoon, Swellow, Skitty, Sceptile, Castform]` →
`[Mightyena, Zigzagoon, Swellow, Sceptile, Castform, Poochyena]`. Box stays at 2 — one out, one
in — which is the make-room deposit and the withdraw landing in the same PC visit, as designed.

### THREE DESIGN CHOICES IN THE PROBE, EACH OF WHICH CHANGES WHAT IT PROVES

1. **It drives the PRODUCTION call site.** The probe sets `self._hunted_counter_pids` on itself
   and calls `heal_in_pokemon_center`, because the harness makes the driver the
   `bot_mode_instance` and that is the exact attribute production reads
   (`higher_level_actions.py:218-232`). Calling `withdraw_from_box(pids)` directly would have
   proven the function works and **not** that the piggyback fires — and the piggyback is precisely
   the half that was dead.
2. **A positive control BEFORE the journey.** `box_views()` raising `TypeError` is the exact break
   that produced `withdrawing = 0`, and it fails *silently*: `find_in_box` swallows it and returns
   None, which is indistinguishable from "the mon isn't there". So the probe asserts the box reads
   and the PID re-resolves before spending a trip on it. A null result at the end would otherwise
   be unattributable.
3. **A no-op assertion, not just a positive one.** After the withdraw it heals a SECOND time at the
   same Centre and requires **exactly one** `withdrawing` line in total. With the PID now in the
   party, `find_in_box` returns None and the piggyback must return without touching the PC. A
   duplicate-withdraw loop is the regression shape that a fires-on-every-heal piggyback invites,
   and nothing else would have caught it.

### FIXTURE NOTE — the heal-fixture is required, and is not a behaviour change
The only save satisfying "full party AND non-empty box" is a previous probe's END state, so the
party arrives at ~critical HP. Runs 1 and 2 never reached a Poké Centre at all: run 1 died to a
trainer approach (`HP below threshold, and 'flee' is not allowed in a trainer battle`), run 2 won
that trainer then **lost the next and whited out** at f5333. Neither measured the withdraw.
`WITHDRAW_HEAL_FIXTURE=1` (default) restores current-HP-to-max and clears the status bitfield by
patching the party struct's unencrypted tail (`data[86:88]`, `data[88:90]`, `data[80]`). PP is
inside the ENCRYPTED substructure and is deliberately untouched — re-encrypting risks a checksum
mismatch, and no PP is needed to talk to a nurse.

Run 1 also used `DefaultBattleStrategy` for trainer battles; the story bot uses
`LevelUpTravelBattleStrategy`, which exists specifically because it **never flees a trainer
battle**. The probe now matches production for trainers and keeps Default for wilds (fleeing a
wild is allowed and is what we want while walking to a Centre).

### GAME RULE, recorded because it justifies the whole design (user, 2026-08-07)
**A boxed Pokémon is reachable ONLY at a PC terminal inside a Poké Centre** — never from a battle,
the party menu, or the overworld. So there is no cheaper retrieval point to go looking for: the
heal-piggyback is not a convenience, it is the only place the operation can happen. Any future
design that assumes a boxed mon can be fielded mid-journey is wrong by construction.

---

## 2026-08-07 — `#24-hmteachloop`: ROOT-CAUSED AND FIXED. The bot was re-arming the teach itself.

The user reported it exactly right on 2026-08-06:
> "the hm learning feature works but it still loops trying to teach/get out of the teaching cycle
> after it teaches an hm"

**The cause.** `teach_hm_move`'s ride loop drives the post-teach dialogue with an if/elif ladder.
The moment the move IS learned, both replace branches switch themselves off via `and not
_knows()` — so every remaining frame fell through to the blind fallback, `A` on one frame in
three. But a Gen 3 bag teach ENDS on **"Do you want to teach <MOVE> to another POKéMON?"**
(`Task_CallYesOrNoCallback`), and **A on that prompt means YES**: it reopens the party menu and
re-enters the teach cycle, which the A-mash then drives again. The loop was never stuck. We were
re-arming it, one frame in three, until the 9,000-frame cap killed it.

**The fix.** Once `_knows()` is true there is nothing left to accept, so the only safe button is
`B` — it declines "teach another", backs out of the bag, and cannot start an NPC conversation.

**A/B, `--driver teachfull` (new), Mightyena with four moves, `POKEBOT_HMTEACH_POSTLEARN_A`:**

| arm | ride_exit | ride_frames | learned | exit task set |
|---|---|---|---|---|
| OLD (`=1`) | `hard-cap` | **8,999** | True | `['ListMenuDummyTask', 'Task_CallYesOrNoCallback']` |
| NEW (default) | `learned` | **479** | True | clean overworld tasks |

Identical outcome (`replaced=['Taunt']`), 94.7% fewer frames, and the flow now exits on a settled
overworld instead of a dangling YES/NO prompt. `repro_hmteach_postlearn.py` — 17 checks, green;
fault-inject the branch back to `A` and 3 go red.

### ‼ WHY FOUR BUDGET ROUNDS (7 / 8 / 9 / 4 failures) FOUND NOTHING — an instrument post-mortem

1. **Only the SUCCESS path emitted telemetry.** `TEACH OK` fired on success and *nothing* fired on
   any of the five failure exits, so no batch could say which one had run. Every hypothesis about
   the cause was therefore unfalsifiable, and the only knob anyone could see was the budget. Five
   exits now emit `TEACH EXIT reason=… frame=… tasks=… learn_state=… moves=…`, which is what
   produced the diagnosis in a single ~5-minute run.
2. **‼ "Every SUCCESSFUL teach exits in 35-86 frames (n=42)" was measuring the wrong loop.** That
   line came from `TEACH OK … in {_f} frames` — and `_f` had already been REBOUND by the
   menus-closed loop below the ride, because Python leaks `for` variables into the enclosing
   scope. It was reporting menu-closing iterations. The ride's actual cost, once measured, was
   **8,999 frames**. That bogus figure is precisely what justified "the budget is irrelevant to
   successes and governs only failures", and every tuning round followed from it. Both counts are
   now reported side by side (`ride_frames=` and `close_frames=`) so they cannot be confused.
3. **The stall detector could never fire.** Its 900-frame threshold assumes a wedge is FROZEN, but
   a ping-pong keeps the task set and dialogue state changing: measured `stall_peak=171`. It was
   never stuck, it was busy — so "add a stall break" and "remove the stall break" were both
   irrelevant, which is exactly what the flat 7/8/9 failure counts were saying.

### ‼ WHY IT NEVER REPRODUCED: the existing driver tested the easy path
`--driver hmtest` teaches to a mon `ensure_hm_learner` has just CAUGHT, which has a free move slot,
so the game learns the move instantly and there is no replace dialogue at all — recorded as 12/12
clean. Every recorded failure is on a mon with FOUR moves. New `--driver teachfull` picks a party
member that is compatible, does not know the move, AND already has four moves, which is the only
combination that exercises `Task_ReplaceMoveYesNo` → summary → the post-learn prompt.
It also carries a positive control on the bag (`quantity_of`), because a missing HM makes the flow
die at "`Task_CallYesOrNoCallback` never appeared" — indistinguishable from the bug.

---

## 2026-08-07 — `#24-whiteoutloop` DIAGNOSED (analysis only, no code changed)

Done while the re-baseline batch was in flight, so it is deliberately **read-only**: stored logs
from four completed batches, no emulator, no `sandbox-pokebot/` edits (a relaunched lane
re-imports from disk, and lane L03 restarted 32 minutes in — the rule is live risk, not theory).

`#24-whiteoutloop` asked for "WHERE runs are when the loop starts" and forbade attributing it
without that. **The answer was already in every log:** each whiteout is immediately preceded by
`lost a battle at map (G,N) (defeat #K here; KO'd J of theirs first)` — map, attempt ordinal and
a progress signal, all three. The whiteout machinery itself is fine; it fires and recovers every
time. **The bug is that nothing stops the bot re-attempting a fight it keeps losing.**

| batch | defeats | at maps with NO `_prepare_for_fight` cfg |
|---|---|---|
| `20260806-174746` | 554 | 283 (51%) |
| `20260806-142418` | 547 | 271 (50%) |
| `20260806-103811` | 541 | 234 (43%) |
| `20260806-055947` | 594 | 291 (49%) |
| **total** | **2,236** | **1,079 (48%)** |

`_prepare_for_fight` is called at exactly six sites (Roxanne, the Rustboro rival, Brawly, Wattson,
Norman, Winona). **Gym 4 / Flannery has none**, and LAVARIDGE_TOWN_GYM_1F is a top-4 defeat map in
4 of 4 batches; ROUTE110 (KI-26) is #1 or #2 in 4 of 4. This also **corrects KI-26's own text**,
which claimed Route 110 and Wally were the only unprepped combat segments.

**Re-attempting mostly does not work**, which is the finding that makes a cap justifiable: of 53
sequences with ≥3 defeats at one map, the best-KO trend is **FLAT in 37, improving in 15, worse in
1**. The design premise — a lost attempt is still training, since Gen 3 keeps KO XP through a
whiteout — holds only ~28% of the time. Worst observed: `LAVARIDGE_GYM n=17 kos=[3]*17` (a
perfectly constant series) and `PETALBURG_GYM n=32`.

And where a cfg DOES exist, `_boss_plan_is_hopeless` still cannot fire: it requires **both** a KO
plateau **and** "no party mon has a ≥2.0-effective move against `ace_types`". An underlevelled
party that HAS a super-effective move fails the second test for ever — that is Petalburg's
32-attempt run.

**Fix specified, not implemented** (waiting on the batch): (1) real cfgs for Flannery and the
Route 110 rival; (2) a cfg-independent cap keyed on **flat KOs rather than attempt count**.
‼ Part 2's shape is what lets it honour KI-26's standing warning — "P2 lost 13 times and then
reached Fortree, so a cap at 6 would have killed a recovering run". The KO series is the
discriminator that warning lacked: climbing KOs mean recovering (15 of 53) and must not be
capped; `[3]×17` means it never will.

---

## 2026-08-07 — `#24-teachpathrace`: found by the new telemetry and fixed the same day

The `TEACH EXIT` instrumentation added hours earlier paid for itself on its first batch.
`20260807-102552`: **33 of 37 teaches succeeded** — and the 4 failures were **not** a regression of
the post-learn fix, but a second, independent bug that had been hiding inside the "7/8/9/4 teach
failures" four budget rounds had been chasing.

```
TEACH EXIT reason=ride:hard-cap post_select=instant-learn move=Surf frame=8999
           tasks=['ListMenuDummyTask', 'Task_BagMenu_HandleInput', 'Task_ScrollIndicatorArrowPair']
           moves=['Take Down', 'Mud Shot', 'Rock Smash', 'Muddy Water']
```

**`post_select=instant-learn` on a mon with FOUR moves is a contradiction, and that single field
is the whole diagnosis.** `Task_HandleChooseMonInput` remains up for a while after the mon is
chosen, so on a slow frame it won the race before `Task_ReplaceMoveYesNo` appeared. The flow
declared the instant-learn path, skipped the guarded replace-prompt block entirely, never answered
the prompt, and rode out the full cap stuck in the bag (`Task_BagMenu_HandleInput`).
`stall_peak=82` confirms it was churning, not frozen.

**Fix:** the instant-learn exit requires positive evidence — a genuinely free move slot, or the
move already known. With four moves there is no instant-learn path to take, so the only legitimate
exits are the replace prompt or the move being learned.

**Live proof, both branches** (`--driver teachfull`, new `TEACH_SLOT` / `TEACH_MIN_MOVES`):

| target | moves before | post_select | ride_frames | result |
|---|---|---|---|---|
| Mightyena (4) | Tackle/Taunt/Take Down/Bite | `replace-prompt` | 479 | learned, replaced Taunt |
| Zigzagoon (3) | Tackle/Growl/Surf | `instant-learn` | 252 | learned, replaced nothing |

‼ The second row is the part that is easy to skip and must not be: the fix GATES an exit, so
"the replace path still works" is only half a proof. A gate one notch too tight would strand every
free-slot teach in the 900-frame loop instead, and the replace test cannot detect that.

### ‼ The ride budget is now sized by real data for the first time
`ride_frames` across the batch's 33 successes: **154** (×9, the free-slot path) and **468-488**
(×24, the replace path). The worst legitimate ride is **488 frames** against a
`_TEACH_RIDE_HARD_CAP` of **9,000** — an ~18× margin, and the old "1.85x the worst legitimate
observed path (4,875)" justification came from the same broken `_f` measurement that produced the
bogus 35-86 figure. **Not changed here on purpose** (one change at a time, and the cap now only
governs failures, which are the thing being eliminated) — but it is now a data-backed decision
rather than a guess, and it is recorded so the next person does not re-derive it.

---

## 2026-08-07 — `#24-whiteoutloop` part 2: the hard plateau (a measurement now beats a prediction)

Batch `20260807-102552` confirmed the diagnosis: *"too many whiteout recoveries in a row —
stopping so I don't loop forever"* was the **#1 end reason, 4 of 14 non-finishes (29%)**.

`_boss_plan_is_hopeless` already had the right plateau test, but it fired only when **both** the
KO count had plateaued **and** no party mon held a credible ≥2.0-effective move. An UNDERLEVELLED
party holding a good move *on paper* therefore never gave up — measured worst case
**PETALBURG_CITY_GYM, 32 consecutive losses**, KOs stuck at 2-3 the entire way.

**The change, in one sentence:** the type-chart answer test is a **prediction**, a long flat KO
series is a **measurement**, and past `HARD_PLATEAU_LOSS_THRESHOLD = 12` the measurement wins —
the existing counter/training escalation runs instead of another identical attempt.

‼ **It is keyed on FLAT KOs across two six-attempt windows, never on attempt count.** That is the
whole design and not a detail: KI-26 records a run that lost **13 times** at ROUTE110 and then
went on to reach Fortree, so a plain "give up after N" would have killed a recovering run. A run
whose KOs are climbing never reaches the branch — the existing `recent_best > previous_best`
return fires first. Twelve is deliberately double `PLATEAU_LOSS_THRESHOLD`: this is the runaway
backstop, not the primary detector.

`repro_boss_plateau.py` gains cases 8-10, pinning all three behaviours: fires on 12 flat losses
**with** a credible answer; **does not fire** on a climbing run at 13 losses; leaves the original
no-answer diagnosis untouched. Cases 1-7 pass unchanged.

### Two implementation traps worth recording
* **The first draft used `break` to skip the answer test.** That exits only the inner move loop,
  so the NEXT battler could still `return False` — the guard would have worked or not depending
  on party order. It now skips the battler loop entirely.
* **The new class constant broke `repro_boss_plateau.py` instantly**, because its `SimpleNamespace`
  stand-in for `self` did not carry it — and `_boss_plan_is_hopeless`'s broad `except` returns
  "not hopeless", which is exactly what a HEALTHY detector returns. This is the second time a
  stale stand-in has disabled this diagnosis; the method's loud warning print is what caught it
  both times, and the stand-in now documents the trap.

### Part 1 is still open, and it is the bigger half
**Flannery / Gym 4 and the Route 110 rival have no `_prepare_for_fight` cfg at all**, so none of
this machinery — plateau, escalation, prep — runs there. They account for **48% of all defeats**
(1,079 / 2,236 across four batches) and are top-4 in 4 of 4. Adding them needs verified game facts
(training grass tile, heal centre, ace types and level; the rival's ace depends on the starter) —
probe or decomp, never recall.

---

## 2026-08-07 — `#24-whiteoutloop` part 1: the two fights that had no boss config at all

`_prepare_for_fight` had **six** call sites. Eight fights can lose. The two without a cfg —
**the Route 110 rival** and **Flannery / Gym 4** — got none of the boss machinery: no sufficiency
gate, no plateau detection, no counter escalation, no give-up. They are **48% of all defeats**
(1,079 / 2,236 across four batches), ROUTE110 is #1 or #2 in 4 of 4, and Lavaridge holds the worst
runaway seen anywhere: **17 consecutive losses with `kos=[3]*17`**, a perfectly flat series.

Nothing about this looked like a bug. The fights simply lost, quietly, for ever, because the code
that would have noticed was never wired to them. KI-26 had flagged the Route 110 half since
2026-07-27.

**Game facts, verified — not recalled** (`src/data/trainer_parties.h` via `gh`/raw):

* `sParty_Flannery1`: Numel 24, Slugma 24, Camerupt 26, **Torkoal 29** (ace, White Herb).
  → `band (24, 29)`, `ace_types ("Fire",)`, `ace_level 29`. Torkoal's typing re-checked against
  our own `modules/data/generated/pokedex_data.json`.
* `sParty_MayRoute110{Treecko,Torchic,Mudkip}` (Brendan's are identical in species and level):
  the ace is **always the L20 evolved starter that counters yours** —
  Treecko → Combusken, Torchic → Marshtomp, Mudkip → Grovyle. → `band (18, 20)`, `ace_level 20`.

### Two deliberate choices worth stating
* **Neither cfg carries a `grass` key.** `_prepare_for_fight` explicitly supports a grass-less cfg
  (*"No training grass exists for this boss (e.g. Lavaridge). The re-attempt itself is the only
  trainer available"*), and Lavaridge genuinely has none — a two-way pathability sweep
  (`jaggedgrass_probe.py`) found Jagged Pass unreachable from the town and Route 112's lower grass
  without a return path. Inventing a training tile to fill the field is exactly how KI-44 happened.
  A swept Lavaridge tile remains `#24-trainmap`.
* **The Route 110 ace derivation now names TYPE PAIRS.** It previously resolved to a single
  primary type ("Water" for Marshtomp, "Fire" for Combusken). Effectiveness against a dual-type is
  the PRODUCT over both types — the same reason Winona's cfg carries `("Dragon", "Flying")` — so
  the old version understated every matchup. Now `("Ground", "Water")` / `("Fighting", "Fire")`.

### NEW `repro_boss_cfg_coverage.py` — assert the COVERAGE, not just the behaviour
`repro_boss_plateau.py` proved the detector works. **Nothing proved it was connected**, and a
perfect detector is worth nothing at a fight that never calls it. The new test walks every
`_prepare_for_fight(<cfg>)` call site, resolves the dict literal, and requires that all seven
measured defeat maps are covered by a cfg carrying real ace data. Fault-injected RED (remove the
Flannery call → 2 checks fail).

‼ **It also caught two of my own wrong assumptions before they became "fixes"** — worth recording,
because the reflex to "fix" the code when a new test goes red is exactly the 2026-08-06 mistake:
* I asserted `ace_level` must sit inside `band`. **False.** Brawly is Machop 16 / Meditite 16 /
  **Makuhita 19** against a `(14, 16)` band — decomp-verified. `band` is the TRAINING TARGET
  range; the ace is often above it. The assertion was wrong, the data was right.
* I required `ace_types` on every cfg, which would have flagged the Rustboro rival. It records
  **0 defeats in all four batches** — there is nothing there to detect, and inventing ace data for
  a fight that never loses is churn with a real chance of being wrong. The requirement now applies
  only to maps that measurably lose.

---

## 2026-08-07 — counter-chain post-mortem from batch `20260807-102552` (analysis only)

Read-only, while the follow-up batch runs. With the whiteout loop addressed, `no super-effective
answer` is the top remaining non-finish class (**5 of 14**). The chain's lifecycle, counted:

| marker | count |
|---|---|
| `no super-effective answer` (the hopeless verdict) | 28 |
| `counter hunt — going to …` (a hunt actually starts) | 9 |
| `counter hunt CAUGHT Machop` | **6** |
| `training the counter` | 12 |
| **`counter training failed`** | **0** |
| `already hunted a counter … — not trying again` | 19 |

**Two things are working that previously were not.** The Norman rung catches its Machop **6 of 7
times (86%)**, and `counter training failed` is **0** — it was **7 of 7** in batch 4, so the
KI-44 training fix is holding in production. Neither had a clean production number before.

**The 28 verdicts split exactly 9 + 19**: nine hunts, nineteen refusals by the one-hunt-per-boss
bound. That bound is correct (it is the only thing that terminates — a per-call budget becomes
per-attempt under the re-entering dispatcher, the KI-34 shape), but it means a boss whose first
hunt fails is unwinnable for the rest of the run.

### `#24-winonaground` — Winona's counter can never be hunted, and it is an unfilled table
Eight of those refusals read `already hunted a counter for Winona this run (blocked: no huntable
counter candidate (nothing reachable with a proven spin tile))`.

`hunt_ground_tile()` is a deliberate WHITELIST that fails closed, and its entire universe is
`HUNTING_GROUNDS` = **{FIERY_PATH}** plus `TRAINING_GRASS` = {ROUTE116, ROUTE117, ROUTE102}.
Norman's Machop lives on FIERY_PATH and Wattson's Nincada on ROUTE116 — which is exactly why
those two rungs work. **No map in that set hosts a Rock/Electric/Ice wild**, so Winona's rung
resolves to "no candidate" every time and spends its one hunt saying so.

‼ **This is not a bug and the whitelist must not be widened by guessing.** Its docstring already
explains why: the cost model prices "train it up to the team's level" at ~0 for a wild already
above the team, so the raw planner ranks *endgame* maps cheapest and offers Victory Road and
Mirage Tower. A blacklist would be an ever-growing list of game facts written from memory. The
fix is to SWEEP one ground and add it with evidence, exactly as FIERY_PATH was — ROUTE118
(Electrike) is the named candidate. Tracked as `#24-winonaground` with the sweep's acceptance bar.

### `#24-ballstarve`
`Cannot hunt a Surf learner: no Poké Balls and no money to buy any` — 4 occurrences and one whole
run derailed. Consistent with KI-43's note that catches rose while each restock still buys ten
balls. It pairs with the end reason `No party mon can learn Surf and the party is full — needs PC
box management`, which the now-proven `#24-pcoverflow` withdraw path should be able to serve.
