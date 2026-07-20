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
