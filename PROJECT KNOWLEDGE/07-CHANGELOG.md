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
