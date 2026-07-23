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
