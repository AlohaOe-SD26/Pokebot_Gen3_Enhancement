# Divergence Log — custom-pokebot vs upstream
> APPEND-ONLY. Every intentional difference between `custom-pokebot/` and
> the upstream mirror (`../40cakes repo/pokebot-gen3/`) gets an entry:
> date, files touched, what changed, why. This is the merge map used when
> reviewing upstream updates.

---

## 2026-07-17 — Fork point
- Forked as an exact copy of upstream commit `5dd898f8`. Only additions:
  this file and `DOCUMENTATION/` (not part of the program).
- No program-code divergences yet.

## 2026-07-17 — Custom-modes framework + Patrol mode (additive only)
- **Added** `plugins/custom_modes_loader.py` (BotPlugin that auto-registers
  modes from the new `plugins/custom_modes/` folder), `plugins/custom_modes/
  __init__.py`, and `plugins/custom_modes/patrol.py` (PatrolMode: waypoint-
  loop shiny hunting, per-profile `patrol.yml`).
- **Why:** punch-list #3 — drop-in custom automations with zero upstream
  edits (upstream `plugins/` dir is the sanctioned extension point, so
  subtree merges stay clean).
- **No upstream files modified.** Upstream ships `plugins/` empty except
  `.gitkeep`, so collisions with future upstream changes are unlikely.

## 2026-07-17 — .gitignore: track our plugins framework (first upstream-file edit)
- **Modified** `.gitignore`: upstream's blanket `plugins/` ignore became
  `plugins/*` + negations for `.gitkeep`, `custom_modes_loader.py`, and
  `custom_modes/`. Upstream ignores plugins/ because it treats them as
  user-private; our framework lives there and must ship with the repo.
  User-dropped private plugins remain ignored, as upstream intended.
- **Why:** without this, the custom-modes framework was silently excluded
  from commits (discovered by the installer's fresh-clone test; ML-2).
- **Merge note:** if upstream changes its `.gitignore`, re-apply the
  negation block.

## 2026-07-18 — Native dashboard GUI (new default window)
- **Added** `modules/gui/dashboard_gui.py`: `PokebotDashboardGui`
  (subclasses stock `PokebotGui`) + `DashboardScreen` — the fork's default
  emulator window with the web-dashboard layout: freely resizable video
  (letterboxed, nearest-neighbour), right tool column (bot mode, speed
  1×-32×/∞, video/audio, KPI tiles, party with colored HP bars, status,
  event log fed by a BotPlugin adapter), and a handheld mode (true
  fullscreen video + overlay tool drawer toggled by a canvas-drawn Pokéball
  button / H; F11 toggles the mode; Esc backs out; state persisted per
  profile in `dashboard_ui.json`). Stock menu bar preserved; in debug mode
  the stock debug tabs open in a separate "Debug" window.
- **Modified** `pokebot.py`: `--classic-gui` flag (upstream window,
  incl. OpenGL/stepping); default non-headless launch now uses the
  dashboard GUI. `StartupSettings` gained `classic_gui` field.
- **Modified** `plugins/dashboard_autoopen.py`: AUTO_OPEN now defaults to
  False (browser dashboard is opt-in; the native GUI is the interface).
- **Merge note:** upstream changes to `modules/gui/__init__.py`
  (PokebotGui) flow into the dashboard GUI via inheritance; re-check the
  overridden `_handle_key_down_event` and the `_emulator_screen` swap
  after upstream GUI refactors.

## 2026-07-18 — Smart dependency check + cffi pin fix (requirements.py)
- **Modified** `requirements.py`: added `find_missing_modules()` (inspects
  installed-package metadata via importlib.metadata + packaging) and made
  `update_requirements()` install ONLY missing/outdated modules — first run
  with everything present now takes ~2 s with no prompt and no pip calls
  (upstream unconditionally ran `pip install` per module). Falls back to
  upstream behavior if metadata inspection fails.
- **Modified** the `cffi` pin `~=1.17.1` → `>=1.17.1`: upstream's own
  aiortc→cryptography chain can require cffi 2.x on the same machine,
  which made upstream's install loop downgrade/re-upgrade cffi and made
  any version check permanently "unsatisfied". cffi's API is stable across
  1.17/2.x. (Requirements hash changes → one-time re-check for everyone.)
- **Merge note:** upstream changes to requirements.py must be re-merged
  around `find_missing_modules()` and the install block.

## 2026-07-18 — Dashboard out-of-the-box (http.yml default + auto-open plugin)
- **Modified** `modules/config/templates/http.yml`: `enable: true` by
  default (bound to 127.0.0.1 — local only) so the dashboard works without
  manual config on new profiles/global-config setups.
- **Added** `plugins/dashboard_autoopen.py`: opens the dashboard in the
  default browser ~2.5 s after profile load when the HTTP server is
  enabled (set `AUTO_OPEN = False` in the file to disable). Added to the
  .gitignore negation list.
- **Modified** `modules/web/static/custom-ui/index.html`: `?v=` cache-buster
  on style.css/app.js so browsers never serve a stale dashboard after
  updates (bump on every asset change).

## 2026-07-17 — Custom web dashboard (additive only)
- **Added** `modules/web/static/custom-ui/` (index.html, style.css, app.js):
  a self-contained web dashboard served by the bot's existing static route —
  live video, KPI tiles, party/opponent panels, mode/speed controls, manual
  pad, SSE live updates. See `DOCUMENTATION/02-custom-interface.md`.
- **Why:** punch-list #5 (total custom interface), v1. The static folder is
  served as-is by upstream (`modules/web/http.py` static route), so no
  upstream code was modified — upstream merges stay clean.

## 2026-07-19 — PROMOTED sandbox enhancement round into custom (user-approved)
The user approved ALL sandbox work for promotion. Files copied from
sandbox-pokebot; sandbox remains for future rounds. New/changed files:

- **Backup & restore + cloud** (`modules/backup_manager.py`,
  `plugins/backup_plugin.py`, `backup.yml`): zip a profile's saves/
  savestates/stats/configs with retention; auto-backup on shiny + timer;
  GitHub-repo (`cloud-backups/`) and synced-folder cloud backends; restore
  into a NEW profile only. Runtime dirs `backups/`, `logs/` gitignored.
- **Macros** (`modules/macros.py`, `plugins/macro_plugin.py`,
  `plugins/custom_modes/macro_player.py`): frame-accurate record in Manual
  mode -> per-profile YAML macros -> "Macro (Custom)" replay mode (once/loop).
- **Patrol v2/v3 + global navigation** (`plugins/custom_modes/patrol.py`,
  `modules/modes/util/global_navigation.py`, `modules/warp_graph.py`):
  multi-map waypoints routed across warps via a ROM-extracted warp graph
  (cached in `cache/`, gitignored). Old `[x,y]` format still works.
- **Gamepad + handheld menu-hide** (`modules/gamepad.py`,
  `plugins/gamepad_plugin.py`, `modules/gui/dashboard_gui.py`): XInput ->
  Manual-mode input; Back+Start toggles the drawer; handheld fullscreen
  hides the Tk menu bar (returns with the Pokéball drawer).
- **Shiny alerts** (`plugins/shiny_alert_plugin.py`, `alerts.yml`): desktop
  toast + sound on shiny, optional auto-pause.
- **Update notice** (`modules/update_check.py` + `dashboard_gui.py`):
  background launch check -> "updates available" banner.
- **Cloud save-sync v2** (`modules/cloud_sync.py`, `pokebot.py` launch hook
  + GUI exit hook): opt-in desktop<->device profile continuity via the
  GitHub backend; applies only pre-emulator, never overwrites a diverged
  local save (conflict -> import-as-new-profile). Default OFF.
- **Game cheats** (`modules/game_cheats.py`, `plugins/game_cheats_plugin.py`,
  `game_cheats.yml`, `dashboard_gui.py` CHEATS card): actions (heal/max-
  level/perfect-IVs/max-friendship/max-money/item-pack/max-balls/rare-candy)
  + toggles (infinite money, auto-heal, force-wild-species, guaranteed-shiny)
  via the bot's own memory-write toolkit; overworld-gated, exception-safe.
  See `DOCUMENTATION/03-cheats.md`.
- **GUI** (`modules/gui/dashboard_gui.py`): tabbed tool column
  (Play/Party/Stats/Cheats/Backups), party XP bars under HP, topmost/touch-
  friendly popups (fixes dialogs hiding behind the emulator in handheld),
  full 386-species sprite picker for the wild-species cheat.
- **.gitignore**: added `!` negations for the 5 new top-level plugins
  (ML-2), and ignores for `backups/` and `cache/` (runtime user data).

### Verification status at promotion (HONEST — not all independently verified)
- **Independent adversarial pass (bugs found+fixed): YES** — backup/macros/
  patrol/GUI (the 16-bug round), and game cheats (77-check adversarial pass,
  fixed a nickname-wipe bug). Gamepad + menu-hide: builder self-tests + live.
- **Builder self-verification + main-session review ONLY, NOT an independent
  adversarial pass: #8 warp pathfinding, #12 shiny alerts, #18 update notice,
  #20 cloud-sync, and the 2026-07-19 GUI polish (tabs / full-dex picker /
  XP bars / topmost dialogs).** These are byte/compile/import/live-screenshot
  verified but a dedicated adversarial verifier has NOT re-checked them.
  RECOMMENDED next: run that pass on custom before relying on cloud-sync
  (save-touching, though OFF by default) and the pathfinding walk.
- **Live in-game effects still user-pending**: cheats on a real save, macro
  record->replay, multi-map patrol walk, shiny-trigger backup/alert.

## 2026-07-19 — Disable stock auto-updater for the root-level git checkout
- **Modified** `pokebot.py`: upstream disables `run_updater()` only when
  `.git` is INSIDE the bot folder. Our `.git` is at the REPO ROOT, so the
  stock updater stayed active and (once upstream tagged release 20260504.1)
  would offer to download a 40Cakes release zip over our fork, clobbering
  divergences. Fixed to walk ancestors for `.git`. Same fix applied in
  sandbox-pokebot/pokebot.py.
- **Merge note:** re-apply if upstream refactors the updater guard.

## 2026-07-19 — PROMOTION BATCH-2 (approved): hunting/living-dex/analytics/watchdog + GUI evolution
Promoted the full sandbox round built after the first promotion (f0b275f3).
Each area below states WHAT it is, WHY it exists (user intent), and files.

### (a) Watchdog / auto-recovery (#22)
- WHAT: a health monitor that detects when the bot is stuck and recovers.
- WHY: the user runs 24/7 unattended hunts; a softlock/crash/encounter-stall
  silently wastes hours. This makes long runs trustworthy.
- HOW: detects encounter-stall (a hunting mode stops producing encounters
  for N min), an unexpected drop-to-Manual (crash), and frame-freeze
  (alert-only — a hung main thread can't be safely auto-recovered). Bounded
  recovery ladder: re-assert the mode → reload a healthy savestate (safety
  backup taken first, overworld-gated) → after max attempts give up to
  Manual + loud alert (never hammers a broken state). Config `watchdog.yml`.
- FILES: modules/watchdog.py, plugins/watchdog_plugin.py, watchdog.yml,
  GUI "Watchdog" status line in dashboard_gui.py.

### (b) Hunt Planner (#9)
- WHAT: pick a target species → see the best place(s) to hunt it + the
  recommended mode; one click travels there (global nav) and hunts.
- WHY: turns "I want species X" into an automated hunt without the user
  knowing routes/methods/encounter rates.
- HOW: modules/encounter_index.py builds a species→locations reverse index
  from the ROM's wild tables (per-ROM JSON cache), find_encounter_tile
  locates a real grass/water/fishing tile; plugins/custom_modes/hunt_mode.py
  ("Hunt (Custom)") navigates + hunts. GUI "Hunt" tab.
- MERGE NOTE: encounter_index mirrors warp_graph's headless-ROM-read + cache.

### (c) Living-Dex Orchestrator (#23, #43, #47)
- WHAT: works through a target list catching what's needed to complete the
  Pokédex, moving between hunts autonomously.
- WHY: the "ultimate idle" — set targets, walk away.
- HOW: modules/living_dex.py derives targets (uncaught + obtainable);
  plugins/custom_modes/living_dex_mode.py ("Living Dex (Custom)") travels via
  Hunt logic. #43 OPPORTUNISTIC: catches ANY wanted-uncaught species en
  route (target only drives travel). #47: also catches a SHINY even of an
  already-owned species (goal = don't miss a shiny). Reads the live dex so
  failed catches self-heal.

### (d) Obtainability model + capability gating (#41, #42-easy)
- WHAT: knows HOW each species is obtained (wild/evolution/gift/static/
  roamer/event/breeding/trade/unobtainable) and whether the player can
  currently reach a location.
- WHY: so the bot never hunts something not catchable in the wild (plans
  evolutions instead, points at reset modes for gifts/statics, marks
  trade/event/unobtainable honestly) and never targets a location gated by
  a capability (rod/HM/badge) the player lacks.
- HOW: modules/obtainability.py + modules/data/emerald_obtainability.json
  (fact-checked Emerald census, sums to 386; Latias+Latios BOTH obtainable
  per user ruling). SHOW BOTH denominators: N/386 National Dex AND 218/386
  obtainable-in-Emerald-without-trading (an honest reality — ~79 Gen-3
  species can't be caught in Emerald alone). modules/capabilities.py reads
  owned HMs/rods/badges from the save. #42-hard (HM-gated map reachability)
  is deferred to a future round.

### (e) Analytics suite (#11)
- WHAT: stats browser (sortable per-species table), encounter-rate
  sparkline, and a luck meter (actual vs binomial-expected shinies).
- WHY: shiny hunters want to see their odds/luck and per-species history.
- HOW: modules/analytics.py (pure math) + ANALYTICS card in the Stats tab.
  Sourced live from stats.db; nothing baked.

### (f) Catch-ball allowlist (#40)
- WHAT: choose which Poké Balls the bot may throw when catching.
- WHY: protect the Master Ball (and restrict to preferred balls).
- HOW: modules/catch_balls.py + catch_balls.yml (default excludes Master
  Ball); filters battle_strategies/catch.py ball selection; "CATCH BALLS"
  GUI card (checkbox+icon per ball).

### (g) Auto-decline move learning (#39)
- WHAT: when a Pokémon levels into a new move, decline by default (keep the
  4 current moves) instead of dropping the bot to Manual.
- WHY: the previous default (`stop`) interrupted every hunt on a level-up.
- HOW: battle config `new_move` default → `cancel`; the decision point is
  DefaultBattleStrategy.which_move_should_be_replaced with a `learn_best`
  seam for FUTURE intelligent move evaluation (and story mode).
- FILES: battle_strategies/default.py, config/schemas_v1.py, templates/battle.yml.

### (h) GUI evolution (#30–#38, #44, #46, tabs/handheld/cheats)
- WHAT: the dashboard's current shape.
- WHY: usability on desktop + the ROG Ally handheld.
- HOW (dashboard_gui.py): two-row tabbed tool column (Play/Party/Hunt/Stats/
  Cheats/Backups); handheld hides the Tk menu (its commands move into a
  Play-tab GAME MENU); Left Party Section = clean mon sprites with the
  caught ball shown in the themed HOVER TOOLTIP (type badges, IV grid,
  moves, 3× ball icon); gamepad GUI-navigation gated to the open drawer
  ONLY (never interrupts gameplay); adjustable money cheat + Lock.

### (i) Generated dex datasets + build tools (#34/#35 data foundation)
- WHAT: modules/data/generated/pokedex_data.json (386 species: stats,
  learnsets, evolutions, sprites, category/height/weight/flavor) +
  itemdex_data.json (309 items). tools/build_dex_data.py +
  extract_pokedex_entries.py regenerate them.
- WHY: the data backbone for the future Pokédex/Item-Dex TABS (#34/#35,
  not built yet — awaiting the user's dex-artwork/item-location decisions).

MERGE NOTES: all new plugins have .gitignore negations. gamepad.py edit =
GUI-nav gating. game_cheats.py = money field/lock + catch-adjacent. Upstream
edits to catch.py/default.py must be re-merged around the allowlist filter /
the new_move decision point.

### (j) Story Mode — auto-player (#24), Chapter 0 intro + progress detector
- WHAT: a new "Story" bot mode that plays Emerald's story. Promoted
  2026-07-20 with two chunks working:
  1. **Read-only progress detector** (`modules/story/chapters.py` +
     `progress.py`): reads a save's flags/badges/items and reports the current
     story chapter (30-chapter registry). Badge-anchored placement (highest
     gym badge = the reliable spine; finer flags/items refine within the
     bracket; anything met ahead of the badge count is flagged as a hacked/
     test-save anomaly). `tests/test_story_progress.py` (12 tests).
  2. **Chapter 0 intro + into the house** (`modules/story/intro.py`,
     `early_game.py`): title → New Game
     → Birch's speech → gender → name entry → lands controllable INSIDE the
     moving truck. Task/GameState-driven, fully bounded.
- WHY: the roadmap goal of an unattended story-completion bot, built in
  verifiable chunks (design in PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md).
- HOW: `plugins/custom_modes/story_mode.py` = the `StoryMode` bot — fresh boot
  runs the intro (name/gender from `<profile>/story.yml` via
  `modules/story/config.py`); an already-loaded save is detected & reported.
  To let the mode be picked at the title screen, `BotMode` gained
  `is_selectable_from_title_screen()` (default False; StoryMode overrides True)
  and both mode pickers (`dashboard_gui.py`, `emulator_controls.py`) honor it.
- FILES: modules/story/*, plugins/custom_modes/story_mode.py,
  modules/modes/_interface.py, modules/gui/dashboard_gui.py,
  modules/gui/emulator_controls.py, tests/test_story_progress.py.
- STATUS: chunks 1–2 done & live-verified (user tested the intro on real
  hardware). Chapters 1–24 execution is WIP. Intro currently assumes a
  save-less boot (Continue-from-title path is TODO).

### (j-update 2026-07-20) Story Mode Chapter 0 now runs through the rival intro
`early_game.py` extended: after the clock → downstairs (rides Mom's chat + the
Petalburg-Gym TV scene) → out → rival's house (auto mom greeting → upstairs →
touch Poké Ball → meet the rival) → back outside in Littleroot. Full chain wired
into StoryMode. Verified in custom (fresh run → Littleroot (14,9)).

### (j-update 2026-07-20b) Story Mode: Chapter 1 (Route 101 → starter → first battle → lab)
`early_game.py` extended with `help_birch_and_choose_starter()` +
`finish_birch_lab()`: north to Route 101 → Birch rescue → choose a starter
(config `starter`: random/specific) → win the first battle → finish the lab
conversation. `on_battle_started` returns Fight (shiny contingency: story
battles are always fought through, never caught/halted). Config `starter` +
`starter_nickname` (nickname gated off / TODO). Verified in custom (full fresh
run → Birch's lab with starter, first battle won).

### (j-update 2026-07-20c) Story Chapter 1 COMPLETE — travel/train/rival
`early_game.py`: travel_to_route103 + train_lead_to_level (spin+heal at Oldale
Poké Center, LevelUpLeadBattleStrategy) + fight_route103_rival (heal to full
then battle). StoryMode.on_battle_started → LevelUpLeadBattleStrategy. A fresh
game now plays through the first rival battle. Verified in custom (train + rival
from the Route 103 checkpoint → DEFEATED_RIVAL_ROUTE103 True, no crash).

### (j-update 2026-07-20d) Story: return to lab + Pokédex
`return_to_lab_and_get_pokedex()` + `_navigate_through_scripts()`: after the
rival, back to Birch's lab (riding out the Oldale rival intercept), receive the
Pokédex + Poké Balls. Wired into StoryMode (which now ends at the Pokédex).
Verified in custom (SYS_POKEDEX_GET True). (early_game.py also carries WIP
`travel_to_petalburg`/`_navigate_leg`, not yet wired.)
