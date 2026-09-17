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

### (j-update 2026-07-20e) Story: travel to Petalburg City
`travel_to_petalburg()` + `_navigate_leg()`: lab -> Route 101 -> Oldale (per-leg
navigate_to) then navigate_to_anywhere(PETALBURG) from Oldale (the global nav
loops on Route 101, so we get past it first). Wired into StoryMode (now ends at
Petalburg). Verified in custom (pokedex_done -> Petalburg (0,0), 22.1k frames).

### (j-update 2026-07-20f) Story Chapter 2: Petalburg Gym (Dad) + Wally tutorial
`do_petalburg_gym_and_wally_tutorial()`: enter the gym, fire the Norman scene at
(4,108), ride out the fully-auto Wally catching tutorial (Route 102 Ralts catch
+ back). Completion = back in the gym + controllable after visiting Route 102
(the tutorial doesn't set THANKED_FOR_PLAYING_WITH_WALLY). Wired into StoryMode.
Verified in custom via the listener harness (petalburg.ss1 -> done, 8.4k frames).

### (j-update 2026-07-20g) Story Chapter 3a: Petalburg -> Route 104 -> Petalburg Woods
`travel_to_petalburg_woods()` (early_game.py) + new `LevelUpTravelBattleStrategy`
(story_mode.py), wired into StoryMode. Chain: heal at Petalburg PC -> cross WEST
onto Route 104 riding out the one-time `PetalburgCity_EventScript_Scott` cutscene
at (4,12) -> fight the Route 104 trainer -> enter the Woods south door (10-11,38)
via discrete up-steps. `LevelUpTravelBattleStrategy` NEVER flees a trainer battle
(the single-mon party can't -> RuntimeError; see ML-8) and is now used for ALL
story battles (wild battles keep the flee-at-low-HP behaviour). Verified in
sandbox via the listener harness (fresh gym save -> Petalburg Woods, 6251 frames,
x2, deterministic); promoted as byte-identical source (custom compile + wiring
smoke OK). Map facts / recon in PROJECT KNOWLEDGE/12-STORYMODE-DESIGN §16 + §R.

### (j-update 2026-07-20h) FIX: Petalburg Woods south-door stall (ML-9)
The promoted `travel_to_petalburg_woods` (j-update g) hand-stepped onto the Woods
south-door warp tile — flaky in the real bot (warp didn't fire -> BotModeError ->
main.py Manual mode = "stuck in the Woods", user-reported). Fixed with the new
`_pass_through_door(tile, from_map)` helper, which warps by navigating ONTO the
door tile (like heal_in_pokemon_center) instead of hand-stepping. Byte-identical
to the sandbox fix, which was re-verified with a main.py-faithful harness
(wally_done -> Woods -> ... -> Gym 1 -> BADGE01_GET True, no error). Custom compiles.

### (k) STOCK FIX: battle handler handles end-of-battle move-learn (ML-11)
`modules/battle_handler.py` (a stock upstream file) modified: `handle_battle`'s
loop now continues while a move-learn/evolution dialogue is pending (not only
`battle_is_active()`), and dispatches the move-replacement handler when the learn
dialogue is active even if the battle instruction moved on. Fixes a hang where a
Lv-up move-learn surfacing AS a trainer battle ends was left unhandled (all
starters at Lv16). Same change in sandbox. Reproduced + verified (trainer repro
4/4 clean). Upstream candidate.

### (l) STOCK FIX(2): move-learn hang — guard-loop dispatch + safety (ML-11)
`modules/battle_handler.py`: an evolution scene not at its move-learn substate now
routes to handle_evolution_scene (advances it) rather than the move-replacement
handler (which breaks while an evolution task lingers → re-dispatch spin).
`modules/battle_move_replacing.py`: handle_move_replacement_dialogue gets a bounded
safety (5000-frame budget → back out with B) so the bot can never hard-freeze on
the "Delete which move?" screen. Same in sandbox. Verified no regression.

### (m) STOCK: battle no-progress watchdog (ML-11)
`modules/battle_handler.py`: handle_battle's loop now bails out (escape menu with
B, then break) if its progress signature (instruction + callback + learn-move
state + party EXP) is unchanged for 6000 iterations — guarantees the bot can never
hard-freeze inside a battle (the flaky Lv16 move-learn hang). EXP in the signature
keeps GiveExp from false-triggering. Same in sandbox.

### (n) STOCK FIX(ROOT): robust move-learn YES/NO answering (ML-11)
`modules/battle_move_replacing.py`: handle_move_replacement_dialogue now answers
the "Delete a move?" YES/NO (and the delete-confirm) only when is_waiting_for_input()
— blind A/B spam was mis-registering the answer and then waiting on a fixed
next-state that never came (the user-reported Lv16 hang). No fixed-target waits; the
outer loop follows the actual state. Same in sandbox. Verified 4/4 learns Pursuit.

### (o) STOCK FIX(VERIFIED): move-learn hang — direct presses + multi-move re-decide (ML-11)
`modules/battle_move_replacing.py`: reproduced reliably (a mon learning multiple
moves at one level hung 100% at the Yes/No). Fixed: answer with direct A/B presses
(is_waiting_for_input() is always False in battle -> gating never pressed -> hang),
advance the preceding text with A not B (B mis-answers Yes/No as NO), and re-decide
per offered move for multi-move. Verified Castform 3/3 learns 3 moves; Treecko
unchanged. Same in sandbox.

### (p) STOCK FIX(ROOT, ML-12): move-learn dispatch PRIORITY + live stall diagnostic
`modules/battle_handler.py`: the Lv16 move-learn still froze on the real 32× run
though every offline harness passed. Cause: `handle_battle`'s if/elif dispatch
checked the action-selection callback (`HandleTurnActionSelectionState` /
`sub_8012324`) BEFORE the move-learn branch; that callback can linger while the
post-battle "Delete a move?" prompt is up, so the frame went to action-selection
and the prompt was never handled -> hang. Fix: dispatch a move-learn
(`AskToLearnMove` / `_move_learn_dialogue_active()`) and an in-progress evolution
scene FIRST, ahead of action-selection / item-steal / pay-day. Also added
`_dump_battle_stall_diagnostic()`: on the no-progress watchdog it logs the exact
battle/field text + instruction + callback + learn-state + active menu tasks to the
console and `<profile>/battle_stall.log`. Both builds compile; awaiting user
re-test. Same in sandbox.

### (q) STOCK FIX(ROOT CAUSE, ML-13): text-driven move-learn — the ACTUAL hang fix
`modules/battle_move_replacing.py` + `modules/battle_evolution_scene.py`. The real
cause of the Lv16 Treecko/Pursuit freeze: the Emerald BATTLE "Delete a move to make
room for X?" Yes/No has NO backing task, so `get_learn_move_state()` could only
recognise it by a fragile script-offset (`BattleScript_AskToLearnMove + 0x11`); when
that offset never matched, the state stayed `Unknown` and the fallback pressed A only
when `is_waiting_for_input()` (the FIELD text-printer — unreliable in battle), so it
pressed NOTHING and froze on the prompt. Fix: rewrote `handle_move_replacement_dialogue`
to be fully TEXT/TASK-driven — detect the Yes/No from the on-screen text
("make room for" / "Delete a move") as well as the state, drive the move-select from
the reliable `Task_HandleReplaceMoveInput`, and advance every other text box with A
DIRECTLY (never gated on is_waiting_for_input). `handle_evolution_scene` hand-off
hardened the same way (breaks on state OR text OR the move-select task, with a guard).
Proven by fault-injection A/B (force the state Unknown + is_waiting_for_input False):
old code stalls ~10,600 frames and declines the move; the fix resolves in 394 frames,
learns Pursuit, evolves to Grovyle. Verified on BOTH builds. Supersedes the (p) ML-12
dispatch-order hypothesis (a red herring — kept only as harmless defence). Same in
sandbox. Repro tool: scratchpad/repro_movelearn.py.

## 2026-07-21 — PROMOTION (approved): Story-mode resilience + swap-training + debug logging
Promoted from sandbox after the user validated it on real hardware through the early
game (fresh save → past Oldale → rival → Pokédex → Petalburg → Woods → Rustboro →
pre-gym catching + training). All defect fixes were reproduced + fixed via the new debug
logger's generator-stack dumps.

WHAT (story-mode enhancements — mostly additive in our own story files):
- Defeat/whiteout recovery matured: a lost battle no longer drops to Manual and never
  reloads a save state; the run re-orients at the respawn Poké Center and resumes the
  segmented playthrough. Segment 1 made RESUMABLE (skip the scripted intro once a starter
  exists) so a mid-training recovery doesn't re-run the truck→lab intro. Derail budget
  reset on monotonic party progress.
- Fixed the "stuck at the Oldale Poké Center" heal loop: heal now returns only once the
  overworld is STABLY controllable (see upstream edit below), so the heal→go-to-rival
  navigate can't choke into an endless heal/re-heal loop.
- Out-of-balls catching flees instead of dropping to Manual (`StoryCatchStrategy`).
- SWAP-TRAINING (`SwapTrainBattleStrategy`): a weak team member levels by having a
  stronger team-mate secure the KO (Gen-3 shared EXP) — switches when the trainee is
  under-levelled OR can't safely continue (low HP / no usable move), only fleeing when no
  team-mate can safely finish. Kills the fight-faint-heal loop.
- Every story grind spin routed through a whiteout-aware `_story_spin()` (bails into
  recovery on a mid-training whiteout instead of spinning at the respawn point).
- Groundwork: `modules/story/training_areas.py` (level-spectrum of early grass +
  best_training_grass()) for future area-appropriate training.
- FILES (our custom code): modules/story/early_game.py, modules/story/chapters.py,
  modules/story/training_areas.py (NEW), plugins/custom_modes/story_mode.py.

UPSTREAM-FILE EDITS in this promotion (tracked divergences):
- modules/modes/util/higher_level_actions.py — `heal_in_pokemon_center`: (1) robust PC
  exit (walk to the tile ABOVE the door and step DOWN so the exit warp fires, instead of
  navigate_to onto the warp which can stop on it — ML-9); (2) after the exit warp, WAIT
  for a STABLE controllable overworld (20 consecutive controllable frames, bounded) so
  callers' next navigate can't choke. Benefits every mode.
- modules/main.py — one guarded `debug_logger.on_frame(frame_info)` call in main_loop
  (no-op unless debug logging is toggled on).
- modules/gui/emulator_controls.py — "Debug Logging (diagnostic file)" checkbutton added
  to the bot-mode (Run) menu; default off.
- modules/watchdog.py — Story remains in `_SELF_RECOVERING_MODES` (already logged in
  BATCH-2); unchanged intent, carried forward.

NEW custom module: modules/debug_logger.py — opt-in run logger (OFF by default, toggled
from the Run menu). Writes <profile>/debug-logs/<mode>-debug-<ts>.log with an event
stream + automatic STUCK DUMPS carrying the running generator call stack (function+line),
held buttons, tasks, scripts, battle text. Fully guarded; profiles/* is gitignored so
logs are never committed. Also toggle-wired in the native dashboard (modules/gui/
dashboard_gui.py, a custom file).

## BATCH-3 — Story-bot promotion (2026-07-24, on explicit user approval)

Promoted from `sandbox-pokebot/` after the Fortree rotating-gate puzzle was solved live.
**Scope: the story-bot bundle ONLY.** The GUI milestone feature (`modules/gui/dashboard_gui.py`
+7082 lines, `modules/gui/emulator_controls.py`, and the new `modules/gui/milestone_window.py`
/ `modules/story_milestones.py`) was deliberately LEFT in the sandbox — it is a separate,
self-contained feature (`story_milestones` ← `milestone_window` ← `dashboard_gui`), nothing in
the story bundle imports it, and 7k lines of GUI diff is its own promotion decision.

**Pre-promotion safety check:** compared every `def`/`class` name in the custom copies against
the sandbox copies for all promoted files — **zero lost symbols**, i.e. sandbox is a strict
superset, so no custom-only functionality was reverted. (Raw per-file "custom-only line" counts
look large — 838 for `story_mode.py` — but that is diff counting rewritten lines on both sides,
not lost code.)

NEW custom module: `modules/story/fortree_gates.py` — faithful port of the Emerald decomp's
rotating-gate rules (`src/rotating_gate.c`): arm-layout tables, `has_arm`, `can_rotate`,
`rotate_in_direction`, `get_rotation_info`, `try_move`, plus `read_orientations()` (decodes the
8 gates off `VAR_TEMP_0..3` — no new memory reader needed) and a bounded BFS `solve()` that reads
static collision from the live map and accepts live NPC tiles as dynamic obstacles.

Modified (all carrying 2026-07-24 fixes; see 07-CHANGELOG for the proofs):
- `modules/story/early_game.py` — Fortree gate climb (re-plan per tile, NPC-aware, bounded,
  exit-and-re-enter reset which also resets NPC positions); HM slots ineligible in the
  bag→teach expendability picker (the root cause of the user's Surf/Rock-Smash loop);
  `_navigate_riding_out` fails fast on a hopeless retry; `_leave_route120_north_bridge` guard
  narrowed to the strand column; Fortree Kecleon target corrected from the wall tile (24,8) to
  (25,7)/"Down"; turnstile fallback only rides out a scene that exists.
- `plugins/custom_modes/story_mode.py` — prep grinds priced in FRAMES
  (`MAX_PREP_TRAINING_FRAMES = 250_000`) instead of levels; 0-PP moves never selected in
  unfleeable trainer battles (all three fallbacks incl. the double-battle path); Ch13d resume
  gated on the Kecleon flush flag as well as the Scope.
- `modules/story/training_areas.py` — `FRAMES_PER_WILD_BATTLE = 1433` (MEASURED) and
  `estimate_frames_to_level()`.
- `modules/battle_move_replacing.py` — HM veto that RE-PICKS the best non-HM slot rather than
  declining; move-learn safety valve survives re-entry (`_STALLED_EXITS`, raises after 3).
- `modules/modes/util/walking.py` — phantom-script escape in `ensure_facing_direction` (the
  Route 111 (18,99) stale-reader wedge that killed four runs) + the pressing-path frame bound.
- `modules/battle_handler.py`, `battle_action_selection.py`, `battle_strategies/{default,level_up}.py`,
  `modes/util/{global_navigation,higher_level_actions}.py`, `watchdog.py`, `debug_logger.py` —
  supporting changes carried forward with the bundle.

**Post-promotion verification on custom:** 14/14 files parse; 12/12 promoted modules import
cleanly; `StoryMode` loads with `MAX_PREP_TRAINING_FRAMES=250000`, `FODDER_LEVEL_GAP=12`,
`FRAMES_PER_WILD_BATTLE=1433`, and `fortree_gates.solve`/`read_orientations` present; and the
HM re-pick proof RUN AGAINST `--build custom` reproduces the fixed behaviour (forced HM slot →
learns Take Down over Bide, Rock Smash retained, 1 invocation, no loop).

**Outstanding at promotion time:** BADGE06 itself is still unproven end-to-end
(`#24-fortreebadge` — the isolated gate drive lost to Winona because battle prep belongs to the
caller); whiteout attrition (`#24-whiteout`) is unaddressed; the GUI milestone bundle is
unpromoted by choice.

## BATCH-3b — "Endless Debug-Reset Runs…" menu item (2026-07-25)

`modules/gui/emulator_controls.py` — adds an **Endless Debug-Reset Runs…** entry to the Bot Mode
dropdown. Prompts for a run count (default 10, **0 = infinite**) and launches
`tools/story-dev/endless_runs.py` in its own console window.

Deliberately a LAUNCHER, not an in-process loop: the runner already carries failsafes that were
each earned by an observed failure — a wall-clock cap per run (frame-based watchdogs cannot see a
wedged emulator process), log-growth stall detection (a run can burn 2,000,000 frames making zero
progress and still look alive), a fresh profile per run with metadata COPIED not synthesised
("fresh boot from title" still loads the battery save; a hand-written metadata.yml lacks the ROM
reference and kills every run), one bad run never aborting the batch, and "zero frames is never
reported as success". Re-implementing that in the GUI would mean re-earning all of it.

Detached process, so closing the GUI does not stop an overnight batch. Progress is one row per run
in `tools/story-dev/endless-runs/LEDGER.md` (gitignored — run artefacts, not source).

Promoted to custom at the same time as sandbox because the user could not find the option and it
is unclear which build they launch; the path arithmetic (`parents[3]` → repo root) was verified
to resolve correctly from BOTH build directories.

## BATCH-3c — the COUNTER CHAIN modules (2026-07-25) — *logged retroactively 2026-07-25*

**‼ Logged late.** These two files landed in `custom-pokebot/` with commit `72b49fd6` and were
never recorded here; a doc audit caught the gap. Both are **purely additive** — new files in
`modules/story/`, which is our own package. No upstream file is touched by either.

**Added** `modules/story/counter_plan.py` (185 lines)
- Ranks catchable TYPE COUNTERS over the whole-game encounter index when a boss plan cannot
  converge: type coverage, then a verified spin tile, then encounter rate, then level fit.
- **Why:** KI-23. The user's overnight logs showed **198 Winona attempts, 41 losses, 41 whiteouts,
  never a win**, with a party far ABOVE her levels — it was losing on TYPES, and levelling cannot
  fix that. The bot needed to be able to answer "what should I go catch?", which nothing upstream
  or ours could do.

**Added** `modules/story/region_reach.py` (496 lines)
- Region-scale reachability from the ROM's own `MapConnections` + warps (never a hand-written
  table), with capability gates (`KNOWN_GATES`), hop distances, and a `why_unreachable()` that
  keeps "no connection path" / "needs Surf at A-B" / "reachable but N hops away" as three
  distinct answers. Fail-safe throughout: never raises into a caller.
- **Why:** KI-24. Upstream's `modules/map_path.calculate_path` is a tile-level A* and reads the
  Route 118/119/120 dual-elevation bridges as WALLS — the same limitation that forced our
  `_hold_walk_route()` into existence — so it reported ROUTE118, the real answer to Winona, as
  unreachable from ROUTE120, and failed even on a same-map Route 119 walk. **`calculate_path` was
  deliberately NOT modified**: it is correct for what it does, every mode depends on it, and the
  bug was asking it a question at the wrong scale. See `06-DECISIONS-LOG.md` (2026-07-25).

**Also modified** `plugins/custom_modes/story_mode.py` — `_counter_area_allowed` (the `allow=`
predicate that routes counter selection through `region_reach` at `max_hops=4`) and
`_counter_catch_message`. `_training_area_allowed` still uses `calculate_path` and is a known
open item (KI-24b, `#24-regionreach`).

**Upstream-merge note:** nothing here collides. `modules/story/` does not exist upstream, and the
only upstream module referenced (`map_path`, `map_data`, `map`) is read, never patched.

## BATCH-3d — `Story (ENDLESS RESET)` replaces the launcher menu item (2026-07-25)

**This REVERSES BATCH-3b above** (append-only file, so 3b stands as written — read it together
with this entry).

BATCH-3b shipped an "Endless Debug-Reset Runs…" menu item that spawned
`tools/story-dev/endless_runs.py` in its own console window. It failed in the user's hands: the
dialogs appeared and the bot they were watching sat idle, because the work was happening in a
process they could not see. "Chained debug reset bots" meant *this emulator*.

**Modified** `plugins/custom_modes/story_mode.py` (commit `52749958`, fixed by `aadad944`)
- Adds `StoryEndlessResetMode` → mode name **`Story (ENDLESS RESET)`**, a subclass of
  `StoryDebugResetMode` that simply loops the parent's `run()`. Every iteration is therefore the
  exact hard-reset → forced NEW GAME → play cycle the user already trusts, back to back in-process.
- In-process failsafes (a subprocess launcher got these for free): `BotModeError` is SWALLOWED per
  run so a crash in run 3 never costs runs 4..N; a hard `MAX_FRAMES_PER_RUN = 3_500_000` cap
  (StoryMode's own watchdog cannot catch a wedged watchdog); the bot mode is re-asserted after
  every run because a derail can call `set_manual_mode()` and silently end the batch; and the
  batch's `emulation_speed`/`video` are captured once and restored each run — `aadad944` fixed a
  user-reported bug where only run 1 was unthrottled and every run after it crawled at 1x.

**Modified** `modules/gui/dashboard_gui.py`
- The "Endless Debug-Reset Runs…" item now sets `story_mode.ENDLESS_RESET_TARGET` (default 10,
  `0` = forever) and selects the bot mode, instead of spawning a process.

**`tools/story-dev/endless_runs.py` is NOT retired** — it keeps two failsafes an in-process mode
structurally cannot have (a fresh profile per run, and wall-clock + log-growth timeouts that
survive a wedged emulator process), so it remains the right tool for a scripted batch.

**No upstream file is touched by either change.** `dashboard_gui.py` is already ours (see the GUI
batches above); `story_mode.py` is ours.

## BATCH-4 — the full story-bot round: journey planning, counter chain, x4 headless, KI-38/KI-43 (2026-08-01, on explicit user approval)

Promoted from `sandbox-pokebot/` after batch4 (`x4-runs/20260731-201554`) landed. **Scope: the
FULL sandbox code surface** — 37 files, 16 of them new. Unlike BATCH-3, nothing was held back:
the sandbox modules are interdependent (`early_game` → `counter_hunt` → `obstacle_clearing`,
and the x4 GUI bundle → `endless_x4`/`x4_logs`/`tile_*`), so a partial promotion is precisely
what would have broken custom. Pre-promotion custom HEAD: `9105d6d3`.

**Pre-promotion safety check** (same method as BATCH-3): compared every `def`/`class`/CONSTANT
name in the custom copies against the sandbox copies for all 19 modified `.py` files —
**0 lost symbols**, sandbox is a strict superset (+87 new symbols overall, e.g. `dashboard_gui`
+25, `story_mode` +17). No custom-only functionality was reverted.

### NEW modules
`modules/story/counter_hunt.py` (the type-counter ladder: diagnose a boss loss → pick a
huntable counter → travel → catch → train), `modules/story/obstacle_clearing.py` (clear a
field-move obstacle that seals a route; Rock Smash only — Strength is excluded on purpose,
a boulder is pushed not removed so the success test cannot see it), `modules/story/team_policy.py`,
`modules/badge_log.py`, `modules/badge_case.py`, `modules/battle_fault.py`,
`modules/endless_x4.py`, `modules/x4_logs.py`, `modules/tile_bridge.py`,
`modules/tile_mosaic.py`, `modules/remote_party.py`, `modules/story_milestones.py`,
`modules/gui/milestone_window.py`, `modules/gui/tile_child.py`, `tools/mapdump.py`,
`CHEATS-DESIGN.md` (a doc `modules/game_cheats.py` already referenced — custom had a dangling
pointer to it before this).

‼ `story_milestones` / `milestone_window` were the bundle BATCH-3 deliberately left behind.
They come across now because `dashboard_gui` has since taken a hard dependency on them.

### Modified
- `modules/modes/util/global_navigation.py` — **warp planning at MAP granularity** (`plan()`
  answered at REGION granularity and the whole Hoenn overworld is one region, so every
  overworld→overworld trip fell through and died); `pick_leg` two-pass warp choice preferring
  a door to somewhere NEW; `_staged_progress_warp`; `_warp_fired` compares MAPS not regions;
  **`_navigate_when_ready` + `_TRANSIENT_WAIT_FRAMES = 600` (KI-43 — see below)**.
- `plugins/custom_modes/story_mode.py` — KI-38 after-faint chooser LEARNS refusals; counter
  ladder wiring; global watchdog unchanged at 18,000 frames.
- `modules/story/early_game.py` — counter-hunt integration, obstacle search re-runs PER MAP
  (the latch that searched once in Petalburg then walked seven maps with the feature off),
  `affordable_training_target` consumption.
- `modules/story/training_areas.py`, `counter_plan.py`, `region_reach.py`, `chapters.py`,
  `intro.py`, `warp_graph.py`, `battle_handler.py`, `battle_move_replacing.py`,
  `battle_strategies/level_up.py`, `debug_logger.py`, `exceptions_hook.py`, `main.py`,
  `modes/_listeners.py`, `profiles.py`, `pokebot.py`, `gui/dashboard_gui.py` (x4 tile mosaic,
  badge case, Story block at the TOP of the Bot-mode popup), `DOCUMENTATION/01`, `02`.

### ‼ DELIBERATELY NOT PROMOTED
- **`DIVERGENCE-LOG.md`** — the sandbox copy is a **stale 91-line fork frozen at 2026-07-18**;
  this file is 606 lines through BATCH-3d. Mirroring it would have destroyed 515 lines of
  append-only history. *Any future promotion must exclude it too.*
- `SANDBOX-NOTES.md`, `SANDBOX-PROPOSALS.md` — sandbox-vs-custom meta, meaningless in custom.
- `.gitignore` — differs only by the word "Sandbox" in one comment.
- `backups/`, `profiles/`, `cache/`, `.last-update-check` — runtime artifacts, never promoted.
- `DOCUMENTATION/03-cheats.md`, `04-automation-and-sync.md`, `05-hunting-and-livingdex.md`
  exist only in custom and were **preserved** (a blind mirror would have deleted them).

### Post-promotion verification (on custom)
- **210 files parse**, 0 syntax errors.
- **18/18** promoted modules import cleanly with `sys.path` at `custom-pokebot/`.
- Constants confirmed live: `_TRANSIENT_WAIT_FRAMES=600`, `_MAX_NON_OVERWORLD_FRAMES=18000`,
  `MAX_PREP_TRAINING_FRAMES=250000`, `affordable_training_target(16,35,250k)=18`.
- ML-2 check: every new path is git-trackable (no `.gitignore` swallowing).
- **Live run against `--build custom`** — `gym1_done.ss1 --driver martbuy BUYN=30`, 40k frames:
  **3 purchases, 3 free Premier Balls, money 8628 → 2628**, identical to the sandbox arm. This
  is the KI-43 proof; before the fix the same run completed **0** purchases.

### KI-43, carried in with this promotion
`_navigate_when_ready` waited on `_MAX_NON_OVERWORLD_FRAMES` = 18,000 — the SAME number as
StoryMode's global-watchdog stall threshold — while pressing nothing and changing nothing. The
watchdog fires on frame 18,000 (`>=`), the wrapper's `break` needed 18,001 (`>`), so the derail
won by one frame every time and the escape hatch was unreachable code. Measured cost: the
Rustboro ball restock completed **0 of 36** times (baseline 33/33), buying 10 balls per trip
instead of 30. Now bounded by its own `_TRANSIENT_WAIT_FRAMES = 600`.

### ‼ OUTSTANDING AT PROMOTION TIME (known, measured, NOT fixed)
- **KI-44** — counter training cannot reach ROUTE102 from ROUTE103; training fails **7 of 7**,
  so **zero counters are ever trained** and batch4's badge funnel is flat at every rung. This
  is the story bot's current blocker and it ships with the promotion.
- Ball starvation: `no money to buy any` appeared **14×** in batch4 (3 ended runs).
- `global watchdog` still elevated (72 → 58 stdout-deduped); the summariser double-counts it.
- Party cap is still 4 (`target_size: int = 4`) — the bot catches 3 and stops, by design.

## BATCH-5 — the counter chain made usable: KI-44, `#24-relocfloor`, `#24-leadpolicy` (2026-08-02, on explicit user approval)

Promoted from `sandbox-pokebot/` after batch5 (`x4-runs/20260801-075805`) measured the chain
end to end. **Scope: 5 modified files, 0 new modules.** Pre-promotion custom HEAD `771e6213`.

**Pre-promotion safety check:** every `def`/`class`/CONSTANT in the custom copies of all 5
files compared against sandbox — **0 lost symbols**, +6 gained (`counter_training_ground`,
`relocation_floor`, `lead_rank_key`, `best_lead_index`, `_can_attack`, `_glass_wonder_guard`).

### What changed and why
* **`modules/story/counter_hunt.py` — KI-44.** `train_counter` used `cfg["grass"]`, the
  **boss's** patch, so a Machop caught in FIERY_PATH was sent to Norman's
  `PETALBURG_TRAINING_GRASS = (ROUTE102, (9,2))` — eight maps away AND **L3-4 wilds**
  (probed from the ROM's own tables; `story_mode.py:739` already called that patch "~25 xp a
  kill, i.e. never"). Training failed **7 of 7**. New `counter_training_ground()` defers to
  `best_training_area`. ‼ The obvious repair — "train where you caught it" — is WRONG:
  FIERY_PATH / ROUTE112 / JAGGED_PASS are all in `NO_RETURN_GROUNDS` because the heal leg
  fails, so there was **no legal training ground at all**. Structural hole, not a constant.
* **`modules/story/training_areas.py` — `#24-relocfloor`.** New pure `relocation_floor()`.
  The old inline `floor = max(local_max, team_max_now - FODDER_LEVEL_GAP)` keyed on the
  party's STRONGEST mon while the trainees are the stragglers, so a L35 team demanded wilds
  above L23 and rejected ROUTE111 (L19-22) — the one reachable area. `no better area is
  available` fired **167×** in batch4. ‼ Only the floor moved: swap-train means a stronger
  team-mate fights, so `best_training_area`'s `team_level` argument correctly stays team max.
* **`modules/story/team_policy.py` + `modules/story/early_game.py` — `#24-leadpolicy` (ruling
  A+C).** `_lead_best_matchup` scored ONLY defence, so it led **SHEDINJA into Norman 9 times
  out of 9** while the freshly-trained L29 Machoke sat in the bag — Bug/Ghost makes Normal 0×,
  which wins a defensive score outright, and then Slaking's Faint Attack (Dark) one-shots its
  single HP. New pure `lead_rank_key()`/`best_lead_index()`: (a) the lead must have a
  ≥neutral damaging move; (c) a Wonder Guard 1-HP body is demoted. **Sort terms, not
  filters** — a lone Shedinja is still led. Both predicates **fail SAFE**.
* **`plugins/custom_modes/story_mode.py`** — call-site wiring for the relocation floor.

### ‼ NOT PROMOTED (same list as BATCH-4 — re-read before any future round)
`DIVERGENCE-LOG.md` (the sandbox copy was a stale fork before BATCH-4; both are identical now
and **must stay that way**), `SANDBOX-NOTES.md`, `SANDBOX-PROPOSALS.md`, `.gitignore`,
`backups/`, `profiles/`, `cache/`, `.last-update-check`. **Never delete on promotion:**
`DOCUMENTATION/03-cheats.md`, `04-automation-and-sync.md`, `05-hunting-and-livingdex.md`
exist only in custom.

### Post-promotion verification (on custom)
210 files parse, 0 errors. **Targeted** imports only — never a bulk import, which on
2026-08-01 executed `modules/data/get_pret_maps.py` at import time and gutted `map_data.py`
in both builds (08-MISTAKES). Constants live: `relocation_floor(4,[12,20],12)=8`,
`best_lead_index(Shedinja/Machoke/Marshtomp)=2` (**Shedinja no longer led**),
`_TRANSIENT_WAIT_FRAMES=600`, `MAX_PREP_TRAINING_FRAMES=250000`. **Live run on
`--build custom`** (`probe_counter_grass.py --state lavaridge.ss1`): relocates to
`ROUTE117 (31,16)` heal `VerdanturfTown` — "RELOCATED (fix fired)", identical to sandbox.
Repro suite 70/70 before promotion.

### ‼ OUTSTANDING AT PROMOTION TIME
The chain now runs end to end and **the badge funnel has not moved** — batch5 Heat→Balance
83% → 79% (z = −0.33), like-for-like on counter-hunt runs 5/9 → 6/10 (z = 0.20, n too small
to resolve). `#24-leadpolicy` A+C removed the fatal lead but **still does not field the
counter**: it picks Marshtomp L35 over Machoke L29 because `can_attack` is binary and 2× STAB
earns no credit. That open question is recorded in `04-HANDOFF.md`.


---

## 2026-08-08 — PROMOTION (BATCH-6): the whiteout/teach/counter round, sandbox → custom

**User approval: explicit, 2026-08-08.** Last promotion was BATCH-5 (`2dba64d3`, 2026-08-02);
**37 sandbox commits** landed since and custom was touched by none of them, so sandbox was a
clean superset and this is a straight forward-port. Verified before copying (`git log -- custom-pokebot/`).

**Promoted: 12 modified files + 1 new.**
`modules/` — `battle_action_selection.py`, `battle_handler.py`, `battle_menuing.py`,
`menuing.py`, `modes/util/global_navigation.py`, `modes/util/higher_level_actions.py`,
`story/counter_hunt.py`, `story/counter_plan.py`, `story/early_game.py`, `story/team_policy.py`,
`story/training_areas.py`; `plugins/custom_modes/story_mode.py`; **NEW** `modules/story/pc_trip.py`.
`cache/*.json` synced. Residual code diff after the copy: **0 files**.

### WHAT THIS ROUND CHANGES, and the evidence each carries

| item | what it does | evidence |
|---|---|---|
| **`#24-pcoverflow`** (both halves) | a full party no longer refuses a catch — it overflows to the PC box, and the mon is collected at the next Poké Centre heal (`pc_trip.py`, piggybacked in `heal_in_pokemon_center`) | capability tests: `caught=True box 0→1`, then `withdrew=True … deposited=True`, 3 identical runs |
| **`#24-hmteachloop`** | after an HM is learned the ride presses only **B**. It was A-mashing onto *"teach it to another POKéMON?"* — re-arming its own teach cycle for the full 9,000-frame cap | A/B **8,999 → 479** ride frames, same outcome |
| **`#24-teachpathrace`** | the instant-learn exit needs a genuinely free move slot, not the mere presence of `Task_HandleChooseMonInput` (a task present on BOTH paths) | both branches live-proven, 479f / 252f |
| **`#24-whiteoutloop`** | boss cfgs for **Flannery** and the **Route 110 rival** (neither had one), plus a hard plateau: 12 flat-KO losses override the type-chart "we have an answer" prediction | **batch-confirmed** `20260807-160545`: end reason 4 → **0**, watchdog 11 → **0**, deepest `defeat #N` **32 → 13** |
| **`#24-movepoolcounters`** | a counter is a **move**, not a type — candidates qualify on a damaging, level-up-obtainable, credible-power move of a needed type. Plus huntability added to `tier` | **batch-confirmed** `20260807-200030`: `no huntable counter candidate` **25 → 0**; control `CAUGHT Machop` 4 → 6 |
| **`#24-counterdesertgate`** | the planner honours `AREA_ITEM_PREREQ`, so it stops sending hunts to Route 111's Go-Goggles desert | A/B on the item, both arms, control held in both |

### Post-promotion verification (on custom)
All 13 promoted files parse. **Targeted imports only** — never a bulk import, which on 2026-08-01
executed `modules/data/get_pret_maps.py` at import time and gutted `map_data.py` in both builds.
Functional check run against `custom-pokebot` directly (not sandbox), with the standing positive
control: `best_huntable` returns **Norman → Machop @ FIERY_PATH `via=type`** (control) and
**Winona → Slugma @ FIERY_PATH `via=move:Rock Throw@L15`**, identical to sandbox;
`pc_trip.withdraw_from_box` present. Counter/boss repro suite 11/11 green before promotion.

### ‼ OUTSTANDING AT PROMOTION TIME — read before trusting this build
* **`#24-counterdesertgate` has NO outcome proof.** It is A/B-proven offline but no batch has run
  on it. Acceptance when one does: `counter hunt CAUGHT Slugma` > 0 with `CAUGHT Machop` unchanged.
* **`#24-teachmsgstall` is OPEN and ships in this build.** A third teach bug: ~9 of 47 teaches
  burn the 9,000-frame cap without learning Surf. Cause identified (the **Norman battle tail** is
  still resident when Segment 12c teaches) but not fixed. It is pre-existing, not introduced here.
* **`global watchdog` end reason went 0 → 4** in `20260807-200030`, new and undiagnosed —
  plausibly the longer counter journeys this round enables.
* **The finish rate has NOT moved resolvably.** 39.1% → 36.0% → 41.7% across the three batches;
  every pairwise z is well under 1.96. Everything above is justified by near-binary counters, not
  by a rate. Do not quote a finish-rate improvement for this round.

---

## 2026-08-09 — PROMOTION: the `party_counter_slot` fence + `#24-progressiongate` (3 files)

**User-approved 2026-08-09.** Promotes the three files that had drifted since the BATCH-6
promotion (`e84b814f`). Until now `custom-pokebot` carried the **`#24-slugmaspin` regression
WITHOUT its fix**, which is what made this urgent.

| file | what changed |
|---|---|
| `modules/story/counter_hunt.py` | `party_counter_slot(needed_type_names, exclude_pids=None)` — **THE FENCE** |
| `modules/story/training_areas.py` | `AREA_PREREQ[FIERY_PATH] = "rocksmash"` (`#24-progressiongate`) |
| `plugins/custom_modes/story_mode.py` | `_party_can_rock_smash()` (move AND `BADGE03_GET`, fails closed) |

### Why the fence: it is BATCH-CONFIRMED, not merely repro-green
Batch `20260809-081643` (8 lanes / 180 min, code `16283010`, `VERDICT OK`, 0 header violations):

| batch | REAL conversion | `CAUGHT Machop` | FALSE catches |
|---|---|---|---|
| `20260808-131334` (before the regression) | 9/20 = 45.0% | 6/8 | 1 |
| `20260808-174145` (the regression) | 3/20 = 15.0% | **0/7** | **10** |
| **`20260809-081643` (this build)** | 9/23 = **39.1%** | **6/7** | **0** |

**`CAUGHT Machop` 0/7 → 6/7, z = +3.24 (resolvable)**, and **false catches 10 → 0** — reported (9)
now equals REAL (9), which was the fence's literal job. Overall conversion 15.0% → 39.1% is
z = +1.76 (directional only) and statistically indistinguishable from the pre-regression 45.0%.

### Verification — run against `custom-pokebot`, then DIFFED against sandbox
Targeted imports only (never a bulk `modules/data/*` import — that gutted `map_data.py` in both
builds on 2026-08-01). Ten checks: three files parse; `party_counter_slot` accepts `exclude_pids`;
`_party_can_rock_smash` present; `AREA_PREREQ[FIERY_PATH] == "rocksmash"`; and the gate's own A/B
— **no party/badge → FIERY_PATH gated out (fails closed); post-badge03 save → rock smash
available.**
‼ **The decisive check for a PROMOTION is not "what answer" but "does custom match sandbox".** The
identical script was run against both builds and produced **identical results on all ten checks**,
including one that returns `None`.
‼ That `None` (`best_huntable` after loading `rocksmash_taught.ss1`) is a **harness-context
artifact, not a fault**: it reproduces identically in sandbox, and the same rung demonstrably
fires in production — 7 Machop hunts / 6 catches in the batch above. It is recorded rather than
hidden because the previous promotion's control ("Norman → Machop @ FIERY_PATH, unconditionally")
is now **obsolete by design**: `#24-progressiongate` makes that answer depend on party + badge, so
asserting the old expectation would have made the check defend the behaviour this promotion adds.

### ‼ OUTSTANDING AT PROMOTION TIME — read before trusting this build
* **`#24-teachmsgstall` is OPEN and ships in this build**, as it did last time — but it is now
  **REPRODUCED deterministically** (`--driver teachfull TEACH_AFTER_TRAINER=1` from
  `journey_r116_wedge.ss1`, ~19,000 frames, identical frame twice). Cost this batch: 4 hard-caps
  against 38 successful teaches, and **zero run-ending events**. Frame burner, not a run killer.
  ‼ Three candidate causes are REFUTED with evidence (see `03-PUNCH-LIST.md`) — do not re-walk them.
* **The counter chain does not convert its wins into finished runs.** 19 of 24 non-finishes (79%)
  still end on its own "no super-effective answer" stop. Measured the same day with
  `--driver normancounter`: a Machop injected at **L18/22/26/40/55** is fielded and knocked out and
  the run loses in **all six arms**, including a control with no counter — against a team of
  L28-31. That points at how the fight is CONDUCTED, not at type coverage. Treat this build's
  counter chain as a working diagnosis engine whose premise is under question.
* **Finish rate 17.2% (5/29) this batch** — the lowest recorded. It cannot resolve a change this
  size at n=29 and must not be read as a regression, but it has not improved either.
* **KI-48 / KI-49** (travel: Route 110 → Mauville, and map-granular journeys arriving at a
  dead-end entrance) are OPEN and ship here.

### ‼ CORRECTION to the entry above, same day (2026-08-09, later)

The "OUTSTANDING AT PROMOTION TIME" note above states that a counter injected at
**L18/22/26/40/55** was "fielded and knocked out" in all six `normancounter` arms, and concludes
that boss losses point at *how the fight is conducted* rather than at type coverage.

**That is RETRACTED. All six arms measured a mon that could not attack.** `#24-bosstelemetry`
(added to sandbox after this promotion) logs one line per turn decision and showed the injected
Machop selecting Karate Chop on five consecutive turns with **PP frozen at 22 and the opponent
untouched at 143/143**, while a natural party member's Bite decremented PP and dealt damage in the
same battle. `debug_create_pokemon(moves=[LearnedMove.create(...)])` builds move slots the engine
selects but never executes. Full detail and the prevention rule: `08-MISTAKES.md` 2026-08-09.

**Nothing about the PROMOTED CODE changes** — the fence and `#24-progressiongate` are unaffected,
and their batch evidence (Machop 0/7 → 6/7, z = +3.24; false catches 10 → 0) stands. Only the
commentary about the counter chain's *value* was wrong, and it is corrected here rather than
edited above, because this log is append-only history.

---

## 2026-08-09 (later) — PROMOTION: `#24-bosstelemetry`, per-turn battle logging (1 file)

**User-approved 2026-08-09.** `modules/battle_action_selection.py` now emits **one line per turn
decision**:
```
[TURN 14] Mightyena L30 94/94 -> UseMove:Bite(pp24)  vs Slaking L31 125/143
```
Actor + level + HP, the action (for a move: its NAME and remaining PP), and the opponent with HP.

**Why it is worth a promotion on its own.** Boss losses end **79% of all non-finishing runs**, and
until now the logs recorded only `[BATTLE] started/ended` and the faint-chooser — nothing about
what was DONE on a turn. Six experiment arms were run without learning why a fight was lost. Its
first two runs immediately produced: an invalidated fixture (an injected mon selecting a move with
**PP frozen and the opponent untouched**, which retracted a same-day conclusion — `08-MISTAKES`
2026-08-09), **Norman healing** (Vigoroth 1 → 53, Slaking 27 → 136), and the observation that the
bot enters the Norman battle **with its L36 ace already at 0 HP**.

**It is LOG-ONLY, and that was verified rather than asserted:** the whole block sits inside one
`try/except` under the existing contract that *instrumentation must never affect the battle*; it
assigns none of `action` / `index` / `battler_index` / `unrecognised`; and it fires once per
DECISION, not per frame (63 records across a full gym run). Placement is the single common point
after any recognised decision, so every branch is covered by one insertion.

`custom-pokebot` and `sandbox-pokebot` are at **zero source drift** after this promotion.

### ‼ OUTSTANDING — unchanged from the earlier entry today, plus one
* The counter chain's premise is under active question. Re-run with a WORKING fixture: four arms
  (control / L18 / L22 / L26) all lose to Norman, with three visible causes and **none of them
  type coverage** — the ace arrives fainted, Norman heals, and the counter is frail. See
  `04-HANDOFF.md`. ‼ It is NOT established that the test anchor represents real runs; the next
  step is to look for the same fainted-ace signature in a batch, which this telemetry now permits.

---

## 2026-08-09 (third) — PROMOTION: `#24-bosstelemetry` part 2 — party HP at `[BATTLE] started` (1 file)

**User-approved 2026-08-09.** `modules/debug_logger.py` now records the party with HP when a
battle opens:
```
[BATTLE] started hp=[('Blaziken', 23, 120), ('Shedinja', 1, 1), ('Whismur', 52, 52), ...]
```
Log-only, inside a `try/except`, `<unreadable>` on any error, once per battle.

**It earned its place immediately by KILLING a hypothesis I was about to build on.** An earlier
probe INFERRED the opening party state from the after-faint chooser and reported that **99.4%** of
battles began with a mon already down; that was never promoted to a finding because ~99% looks
like a misreading. This field measured it directly over **16,749 battles**: **6.4%** start with any
mon fainted, **2.9%** with the ace fainted, mean party health **90.6%** (control: 35.5% of battles
start at FULL health). The single anchor that motivated the hypothesis was simply not
representative.

`custom-pokebot` and `sandbox-pokebot` are at **zero source drift** after this promotion.

---

## 2026-08-10 — PROMOTION: `#24-battleitems` — the bot uses healing items in trainer battles (3 files)

**User-approved 2026-08-10.** User directive: *"I want the bot to use items intelligently and
strategically."*

| file | what it adds |
|---|---|
| `modules/story/battle_items.py` | **NEW.** The pure decision policy — no emulator, no game state. |
| `plugins/custom_modes/story_mode.py` | `StoryItemBattleStrategy` (trainer battles only, fails open) |
| `modules/battle_action_selection.py` | fixes a real index-space bug + per-turn/flow telemetry |

**Why it exists — measured, not assumed.** Batch `20260809-155844` (16,749 battles) found the
opponent healing and the bot never doing so: Norman's `Slaking` restored **27 times, median +81
HP, max +119**, while the party did 6-8 chip damage a turn. Boss losses end **~80-88% of all
non-finishing runs**.

**The policy** (heal amounts read from `items.json`, never from memory): only below 35% HP;
**cheapest sufficient** item so a Full Restore is never burned on a scratch; **never heal into a
losing race** (if our best heal is smaller than the biggest hit taken, attack instead); and
**bounded per battle** — the opponent heals too, and two healers with no bound is an infinite
battle. `repro_battle_items.py`: **27 checks, no emulator.**

**‼ A REAL UPSTREAM BUG WAS FIXED UNDERNEATH IT.** `battle_action_use_item` converted the target
with `map_battle_party_index()` — a BATTLE-order index — and fed it to `scroll_to_party_menu_index`,
which drives the PARTY MENU cursor. Item use therefore did nothing whenever the two spaces
disagreed (measured: **5 requests → 1 potion consumed**). After the fix: **3 requests → 3
consumed, `Blaziken 23/120 → 120/120`.** ‼ Ball throwing passes no target and never enters that
branch, so catching is untouched.

**‼ THE INDEX SPACE IS CONDITIONAL, and the code knows it.** Measured over a batch: party-order
landed **19/19** when the target was party slot 0 and **never** above it; every landing above slot
0 was battle-order. The strategy now picks its first guess from the target's position and **flips
once and logs which space landed** if that guess is wrong. Validation batch `20260810-082509`:
flips **20 → 2**, both-spaces-failed **10 → 0**.

### ‼ OUTSTANDING AT PROMOTION TIME
* **NO OUTCOME METRIC HAS RESOLVED.** Finish rate across the four item-era batches reads
  **25.0 → 33.3 → 16.1 → 28.6%** at n≈30 each — mean ≈25.8%, not one pair resolvable, ~12 hours of
  batching. Boss-length battle win rate moved 51.1% → 53.3% (z = 0.88). **Do not quote this
  feature as a finish-rate improvement.** It is promoted because the MECHANISM is proven and its
  failure modes are bounded, not because outcomes moved.
* The **no-op guard** stays: if a use does not raise HP by the next decision, items are disabled
  for that battle. It costs at most one turn.
* Verified against `custom-pokebot` itself: three files parse, and the policy answers correctly on
  heal/decline/cheapest-sufficient/losing-race/bound, with the strategy, the self-correcting index
  and the same-subject guard all present.

---

## `#24-magmahideout` + `#24-strength` — the Magma Hideout chapter, and Strength

**User-approved 2026-08-10 (night).** The first new *story content* promoted since Mt. Pyre, and
the bot's first support for a **field move that moves an obstacle rather than removing it**.

| file | what it adds |
|---|---|
| `modules/story/early_game.py` | `travel_to_magma_hideout_door()`, `open_magma_hideout_entrance()`, `enter_magma_hideout()`, `do_magma_hideout()`, `do_magma_hideout_chapter()`; plus `#24-strength`: `ensure_strength_learner()`, `strength_push()`, `open_magma_hideout_1f()` |
| `plugins/custom_modes/story_mode.py` | **Segment 15** — calls `do_magma_hideout_chapter()`, guarded on the completion flag; the end-of-content marker moves to the Slateport submarine |

**Acceptance — BINARY, and that is the point.** `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT` (111), the
flag `MagmaHideout_4F_EventScript_Maxie` sets on defeat in the decomp:
```
[magmahideout] RESULT groudon=True map=MAGMA_HIDEOUT_4F at=(15, 21)
  floors=['MAGMA_HIDEOUT_1F','MAGMA_HIDEOUT_2F_1R','MAGMA_HIDEOUT_3F_1R','MAGMA_HIDEOUT_4F']
  whiteouts=0
```
No batch, no z-score, no finish-rate claim. Content is verifiable; a finish rate at n≈30 is not —
four batches read 25.0 → 33.3 → 16.1 → 28.6% and resolved nothing.

### THE ENTRY IS A STEP TRIGGER, NOT A WALK (and this had been wrong three times)
`JaggedPass_OnLoad` covers the door at `(16,18)` with `METATILE_Lavaridge_RockWall` while
`VAR_JAGGED_PASS_STATE <= 1`. A **coord_event** on one of `(21,15) (22,20) (21,20) (14,15)
(13,15)` runs `JaggedPass_EventScript_OpenMagmaHideout`, which opens the metatiles and sets the
var to **2**; the var reaches 1 by itself once the Magma Emblem is in the bag. The chapter uses
`(13,15)` — 8-10 waypoints from the descent's arrival tiles against 15-23 for the others.

‼ **`calculate_path` reported "2 waypoints" to that sealed tile the whole time**, because it
reads the ROM *layout* and cannot see a `setmetatile`. Three separate conclusions across three
weeks — "one-way ledges", "ledge-isolated, needs scripted movement", and "a real south-facing
ledge" — were all this one wall. Reachability on such a map is graded by the VAR, never the
planner.

### STRENGTH — deliberately NOT in `obstacle_clearing`
That framework's success test is *"the obstacle OBJECT IS GONE"*, and its own
`KNOWN_BUT_UNSUPPORTED` entry says why Strength cannot use it: a boulder is **pushed**, not
destroyed. So `strength_push()` tests the opposite shape — **the boulder MOVED** — and tracks it
by `local_id`, because pushing moves the PLAYER onto the boulder's old tile and a
"nothing there any more" test reads False on a push that worked.

Decomp-verified contract (`data/scripts/field_move_scripts.inc`, `src/field_player_avatar.c:754`):
interacting opens a YES/NO, `EventScript_ActivateStrength` sets `FLAG_SYS_USE_STRENGTH` (2185),
and that flag is **never cleared anywhere in the decomp** — so Strength is switched on once per
save, not per map. After activation, walking into a boulder pushes it one tile and **does nothing
at all, silently, if the destination is blocked**. That silence is why the test watches the world.

**The 1F puzzle was solved by simulation, not by eye.** A collision flood over every subset of the
three boulders showed only two subsets connect the entrance to the onward warp, and `(5,22)` must
be one of them. The chosen two-push plan was then validated against its **end state** — boulders
finishing at `[(4,22), (5,23), (7,22)]`, 295 tiles reachable including the goal — because a pushed
boulder still exists and can seal the corridor it was meant to open.

### THE DOCUMENTED "SHORTEST ROUTE" WAS UNWALKABLE — corrected
`1F (20,22) → 2F_3R` sits on a **nine-tile island**: it is an EXIT from 2F_3R, never an entrance.
1F has three collision components (299 / 70 / 9). The chapter uses the branch previously dismissed
as "longer", every leg verified connected to its arrival tile:
```
1F (25,34) -> 2F_1R [arrive (8,2)] -> (17,33) -> 3F_1R [arrive (23,3)] -> (7,21) -> 4F [arrive (46,8)]
4F: stand beside Maxie (16,21) and TALK — there is no coord trigger anywhere in the hideout.
```
‼ **Maxie is approached ADAPTIVELY**, trying all four neighbours at runtime: the static read said
`(17,21)`, the live arrival said `(15,21)`, and the winning run used `(15,21)`. Every static claim
about this dungeon has been wrong at least once.

### ‼ OUTSTANDING AT PROMOTION TIME
* **The teach dodges `#24-teachmsgstall` rather than fixing it.** 1F is Strength-gated, so the
  chapter needs an HM teach, and the natural place — inside the dungeon — is the worst one,
  because that bug wedges a teach taken right after a won battle (**0 of 3** from post-battle
  saves, against **38 of 42** in live batch `20260810-082509`). The chapter therefore teaches at a
  **heal stop**, best-effort, retrying at the next one. In the winning run Lilycove's teach failed
  (logged and skipped) and Mauville's succeeded. **The bug is still there and is still the right
  thing to fix.**
* **The teach costs a move slot on a fighter.** Only Mightyena and Sceptile can learn HM04 and
  both carry four moves; `hm_learner_slot` picks Mightyena and the expendable-slot rule takes
  **Taunt** (base power 0, a status move, so the damaging-move count holds). Zigzagoon — the
  established HM slave, with a free slot — **cannot** learn Strength.
* **The travel leg costs one whiteout.** Ch14 hands over a party that is 3 of 6 fainted with no
  Revives and the nearest Pokémon Centre 276+ waypoints away. The leg heals at Lilycove and
  Mauville and still whites out once; StoryMode's own `on_whiteout` recovery absorbs it.
* **The full chapter has been driven in two halves, not in one uninterrupted run** — the travel
  leg from `saves/post_mtpyre.ss1` and the interior from `saves/magma_door.ss1`. Both are green;
  a single cold-start pass through Segment 15 has not been observed end to end.
* ✅ **PROMOTION VERIFIED IN `custom-pokebot` ITSELF, DRIVEN — not just compiled.**
  `PYTHONUTF8=1 py -3.12 story_harness.py magma_door.ss1 --build custom --driver magmahideout`
  → `groudon=True`, floors `[1F, 2F_1R, 3F_1R, 4F]`, **0 whiteouts** — identical to the sandbox
  run. Source drift after promotion: **ZERO** (`modules/` and `plugins/` diff clean).

---

## 2026-08-11 — `#24-teachmsgstall` FIXED: the HM-teach replace prompt had a ONE-FRAME window
**Promoted with explicit user approval.** Supersedes the "OUTSTANDING AT PROMOTION TIME" bullet in
the Magma Hideout entry above — that entry says "the chapter DODGES `#24-teachmsgstall` rather than
fixing it, and the bug is still the right thing to fix". **It is now fixed.**

**Files changed: one.** `modules/story/early_game.py` (+227 / −23). Source drift after promotion:
**ZERO** (`modules/` and `plugins/` diff clean).

### The divergence from upstream
Upstream 40Cakes has no Story mode, so `teach_hm_move` is ours entirely; this is a fix inside our
own code, not a change to anything upstream ships.

### THE CAUSE — a detector with a one-frame window
The post-select loop waited on
`"Task_ReplaceMoveYesNo" in t and "Task_PrintAndWaitForText" not in t`. Frame trace
(`TEACH_TRACE=1`, `magma_door.ss1`, HM02 → Swellow) shows that is true for **exactly one frame**:
```
f3232735  tasks=['Task_ReplaceMoveYesNo']              <- the ONLY frame it is visible
f3232736  tasks=['Task_HandleReplaceMoveYesNoInput']   <- gone, and it never comes back
```
`pret/pokeemerald src/party_menu.c` explains it exactly — `Task_ReplaceMoveYesNo` displays the
yes/no menu and **sets its own task function to `Task_HandleReplaceMoveYesNoInput` in the same
frame**, i.e. it retires on the frame it becomes answerable, which is the frame the old condition
first became true.

Missing it left the loop mashing A every 12 frames, and `Task_HandleStopLearningMoveYesNoInput`
reads **A as YES = ABANDON THE TEACH**. ‼ The three "different" failure points recorded across
runs are **three phases of one road**: summary handoff (`Task_ClosePartyMenuAndSetCB2`) → "did not
learn FLY" (`Task_ClosePartyMenuAfterText`) → back in the bag, re-arming.

‼ **And this is why it read as deterministic AND intermittent at once** — the property that made
it unfalsifiable for four rounds. A `.ss1` replays identical frame timing, so a save that misses
the window misses it on every replay (0/3); live runs land on a random phase (38/42 ≈ 90%).

### The fix
1. Match **both** task spellings (`_PROMPT_TASKS`, `_STOP_TASKS`) — the input handler is up for as
   long as the prompt is answerable, so a one-frame window becomes an open-ended one.
2. An `already-advanced` exit picks the flow up past a prompt something already answered. ‼ That
   path is **non-fatal** (`_wait_for(..., required=False)`): a new run-ending class is not an
   acceptable price for this fix.
3. **B, not A, at the stop-learning prompt**, placed *before* the blind-A fallback in the ladder.
   A is still pressed to advance TEXT (41 presses over 489 frames on the passing trace) — removing
   it would trade this bug for a stall.
4. The ride ladder had the identical exposure and is fixed the same way.

### ✅ PROMOTION VERIFIED IN `custom-pokebot` ITSELF, DRIVEN — and as an A/B, not a smoke test
```
py -3.12 story_harness.py magma_door.ss1 --build custom --driver teachfull TEACH_ITEM=HM02 \
    TEACH_CANCEL_FORGET=1 [POKEBOT_TEACHWINDOW_A=1]
```
| arm | exit | result |
|---|---|---|
| OLD (`POKEBOT_TEACHWINDOW_A=1`) | `ride:hard-cap stall_peak=61 frame=8999` | **`learned=False`** |
| NEW (default) | `ride:learned stall_peak=250 frame=896` | **`learned=True`**, Fly replaced Peck |

**Frame-for-frame identical to the sandbox arms**, so the promoted copy reproduces both the bug
and the fix. `repro_teach_prompt_window.py` also passes against this build
(`REPRO_BUILD=custom`, 26 checks).

### ‼ OUTSTANDING AT PROMOTION TIME
* **The Magma Hideout chapter still teaches at a HEAL STOP, not inside the dungeon.** That routing
  was built to dodge this bug and has not been changed back. It is now belt-and-braces rather than
  a workaround, but nobody has measured whether an in-dungeon teach is safe — do that before
  moving it.
* **No production batch has run with this fix in.** The A/B is a fault-injected pair on one save.
  The live rate to beat is **38 of 42 teaches** in batch `20260810-082509`; the honest claim today
  is "the mechanism is proven and its failure mode is closed", **not** "teach reliability
  improved by N%". ‼ Do not quote an outcome number for this until a batch produces one.
* **The old repro fixture is gone and that is not recoverable.** `saves/magma_door.ss1` is
  re-captured by `--driver magmatravel` on every success, and a 2026-08-10 22:05 chapter run
  overwrote the save the original failures were measured on. The fault is injected now
  (`TEACH_MISS_WINDOW`, `TEACH_CANCEL_FORGET`), which is reproducible regardless of the save.
* **`TEACH_MISS_WINDOW=1` alone does NOT wedge a teach** — the ride ladder recovers it
  (`ride:learned`, 323f). Missing the window is **necessary but not sufficient**; where the blind
  A-mash then lands decides survival. Kept as a negative result so the next agent does not read it
  as a broken injection.

---

## 2026-08-12 — PROMOTION: §Ch18 (Mossdeep Gym) + §Ch19 (Space Center & HM08 Dive), and the KI-64 / KI-67 battle fixes (8 files)

**Promoted with explicit user approval.** The story ladder in `custom-pokebot` goes **17 → 20 of 24
beats**. All eight files are ours (upstream has no Story mode; the two `battle_strategies` changes
are fork-level policy changes to upstream code).

| file | change | +/− |
|---|---|---|
| `modules/story/mossdeep_gym.py` | **NEW** — §Ch18: the rotating-tile statue puzzle executor + chapter | 466 lines |
| `modules/story/mossdeep_gym_puzzle.py` | **NEW** — a PURE simulator of the puzzle (no emulator) | 242 lines |
| `modules/story/space_center.py` | **NEW** — §Ch19: Space Center **and** the Dive hand-over | 813 lines |
| `modules/story/early_game.py` | `StoryAbort` + `reraise_if_aborting` (KI-67) | +48 / −1 |
| `modules/story/chapters.py` | the KI-61 chapter ORDER fix (the gym must precede 19) | +24 / −6 |
| `modules/battle_strategies/default.py` | `ally_party_indices` — KI-64, the multi-battle partner guard | +53 / −0 |
| `modules/battle_strategies/level_up.py` | the same guard on the chooser the story bot ACTUALLY calls | +12 / −0 |
| `plugins/custom_modes/story_mode.py` | Segments 18 + 19, the partner guard, and a latch-leak fix | +80 / −4 |

‼ **Post-copy drift: ZERO.** Every `.py` under `modules/` and `plugins/` was compared file-by-file
after the copy — **0 differing files**, and an independent audit put the two trees at byte-identical
across all 255 code/config files. A pre-copy audit also refuted a stale claim in `CLAUDE.md` /
`02-ARCHITECTURE.md`: the "sandbox-only" modules (`endless_x4`, `tile_bridge`, `x4_logs`,
`badge_case`, …) are **already present in custom**, so there was no sandbox-only dependency to strand.

**Restore point taken BEFORE the copy:** `restore/2026-08-12-pre-ch1819-promotion` (annotated, pushed).

### ✅ VERIFIED BY DRIVING `--build custom` — three ways, because one was not enough

**1. §Ch18, `--driver mossdeepbadge`:**
```
[ch18c] RESULT badge=True map=MOSSDEEP_CITY at=(38, 10) controllable=True whiteouts=0
[ch18c] ACCEPTANCE: PASS (needs BADGE07_GET AND controllable AND out of the gym; out_of_gym=True)
```

**2. §Ch19, `--driver spacecenter` from `post_mossdeep_gym.ss1`:**
```
[ch19c] RESULT dive=True hm08=True MOSSDEEP_SPACE_CENTER_STATE=3 map=MOSSDEEP_CITY at=(19, 11)
        controllable=True whiteouts=0 frames=3558869
[ch19c] CAN-CONTINUE OK(15wp to the Pokemon Center)
[ch19c] ACCEPTANCE: PASS
```
‼ **`frames=3558869` is IDENTICAL to the sandbox run** — not merely "both passed", but the same
sequence executed to the frame.

**3. ‼ AND THE REAL LADDER, `--driver story`, because the first two do NOT exercise the wiring.**
An adversarial audit caught this before it could become a false clean bill of health: the harness
drivers call `do_space_center_chapter()` / `do_mossdeep_gym_chapter()` **directly** and never run
`StoryMode._play()`, so a green driver run says nothing about the **Segment 18/19 wiring**, the
`_done()` skip branches, or the `_guard()`s. Driven through the real ladder on custom:
```
Story: Ch19 party-select chose slots [0, 4, 2]; confirming
Story: Ch19 the multi battle with Steven has started
Story: Ch19 Space Center defended, MOSSDEEP_SPACE_CENTER_STATE=3
Story: Ch19 HM08 Dive received (RECEIVED_HM_DIVE set, HM08 in the bag)
Story: Ch19 out of Steven's house, in Mossdeep City at (19, 11)
Story: HM08 DIVE IS IN THE BAG - end of built content.
```

**4.** `probe_chapter_order.py` gained a `--build` flag in the same change — it hard-coded the
sandbox path, so the one guard that validates the KI-61 chapter ORDER could never test the fork the
user runs. **Now passes on both** (`1 / 1 saves get the right next beat`).

### ‼ OUTSTANDING AT PROMOTION TIME — read before quoting any of this
* **KI-64 is UNPROVEN ON CUSTOM.** `ally_party_indices` only does work in the partner multi battle
  *and* only when a replacement is needed. Every driven run had **zero faints**, so on custom it has
  been exercised as a **no-op**. Its logic is proven offline (`repro_multi_battle_partner.py`, 5/5,
  including the permuted-array arm); the live path is not.
* ✅ **KI-67's recovery IS now proven on custom too** — driven the same day, immediately after this
  promotion, with a deliberate loss (`--driver spacecenter2 --inject-weak --build custom`):
  ```
  WHITEOUT #1 frame 3532810 / #2 frame 3540509 (+7,699) / #3 frame 3547594 (+7,085)
  RESULT ... map=MOSSDEEP_CITY at=(28,17) controllable=True whiteouts=3 recoveries=3
  ```
  ‼ The frame deltas are the proof, not the counts — broken code burns three attempts in a handful
  of frames after ONE whiteout; this spends ~7,000 frames per attempt and produces its own whiteout
  each time, i.e. the bot really walked back from the Pokémon Center to Steven and fought again.
  **Sandbox measured +7,789 / +7,087 — custom is the same behaviour, not merely the same verdict.**
  The `ACCEPTANCE: FAIL` is correct: a lone Lv3 Poochyena cannot win that battle.
* **Two caveats on the OT-based partner guard:** a **traded** Pokémon would be misread as the ally
  and wrongly excluded (unreachable today — no trade code exists), and a 1-in-65536 TID collision
  would silently degrade it to pre-fix behaviour.
* §Ch21 remains **blocked by KI-63** — HM08 is in the bag, but no party member can learn Dive and the
  party is full.

## 2026-08-11 (second promotion of the day) — KI-51 whiteout guard, KI-52 fight-it-out fallback, and battle STATUS telemetry
**Promoted with explicit user approval.** Three files, all ours (upstream has no Story mode; the
battle-strategy change is a fork-level policy change to upstream code).

| file | change | +/− |
|---|---|---|
| `modules/story/early_game.py` | KI-51: the Maxie loop watches the MAP, not only the completion flag | +40 / −1 |
| `modules/battle_strategies/default.py` | KI-52: rotate → flee → **FIGHT ON**; never raise inside a battle | +163 / −12 |
| `modules/battle_action_selection.py` | the turn logger prints STATUS (`[Confused]`, `[Sleep]`, …) | +36 / −0 |

‼ **Pre-copy check:** the diff against `custom-pokebot` matched `git diff --numstat` for the three
sandbox commits **exactly** (36/0, 163/12, 40/1), proving custom was precisely these three changes
behind with nothing else hiding in the gap. Source drift after promotion: **ZERO**.

### ✅ VERIFIED DRIVEN IN `custom-pokebot`, on the DETERMINISTIC loss fixture
`story_harness.py magma_door_losing.ss1 --build custom --driver magmahideout` — a save that
reaches Maxie and loses the identical fight on every replay, so sandbox and custom are directly
comparable rather than merely "both ran".

**KI-51 guard — identical to sandbox, to the frame:**
```
[magmahideout] FAILED: BotModeError: Magma Hideout: left MAGMA_HIDEOUT_4F during the Maxie
challenge without Groudon awakening — almost certainly a WHITEOUT. map=(0, 2) tile=(22, 6)
party_alive=6/6 (was standing (15, 21) facing Right at Maxie (16, 21), 2209 frames in).
[magmahideout] RESULT groudon=False map=MAUVILLE_CITY at=(22, 6) whiteouts=1 frames=3295572
```
**2,209 frames** against a 60,000-frame bound, same as sandbox.

**STATUS telemetry — identical turns:** `[TURN 4] Sceptile L44 110/122 [Confused]` (8 status lines
in the run). This is the field that refuted `#24-bosstelemetry` LEAD 2.

### ‼ OUTSTANDING AT PROMOTION TIME — read before quoting any of this
* **KI-52's fallback has NO live A/B.** It is structurally proven only
  (`repro_lead_cannot_battle.py`, 34 checks, fault-injected red then green) because the
  reproduction was lost before the A/B ran — the fixture was pinned *after* an in-flight job had
  overwritten it (`08-MISTAKES` 2026-08-11). **Do not record it as live-proven.** This run does not
  exercise it either: no lead-cannot-battle event occurred.
  ✅ What *is* known: on a healthy run OLD and NEW arms completed the chapter identically, so the
  change is behaviourally inert when nothing goes wrong.
* **KI-52 is a policy change to a SHARED battle strategy**, not story-only code. It affects every
  mode that uses `DefaultBattleStrategy`. The ladder only changes what happens where the old code
  **raised**, so no previously-working path is altered — but that is reasoning, not measurement.
  ‼ Related and deliberately NOT changed: `lead_cannot_battle_action` still defaults to `flee`,
  because `flee` is correct for shiny hunting; the scope question (mode-scoped `rotate`?) is open
  and is the user's.
* **A faithfulness bug found and left alone:** `get_escape_chance` uses
  `opponent.speed < battler.speed` (strictly faster) where the decomp escapes free on faster **or
  EQUAL**. It is a different function, it did not cause KI-52, and changing escape odds affects
  every hunting mode.
* **No production batch has run with any of these in.** Nothing here has an outcome metric.

---

# PROMOTION 2026-08-12 — the §Ch15 EXIT, §Ch16 (Slateport) and §Ch17 (Aqua Hideout)

**Approved by the user 2026-08-12.** Two files changed: `modules/story/early_game.py` and
`plugins/custom_modes/story_mode.py`. Story-mode content only — **no shared subsystem is touched**,
so no other bot mode can be affected by this promotion.

**‼ VERIFIED ON THE CUSTOM BUILD ITSELF, not just diffed.** `--driver aquahideout --build custom`
from `post_harbor.ss1`:
```
[ch17] RESULT escaped=True controllable=True map=AQUA_HIDEOUT_B2F at=(24, 19) whiteouts=0 frames=3409537
[ch17] ACCEPTANCE: PASS
```
The frame count is **identical to the sandbox run** (3,409,537), i.e. the promoted build reproduces
the sandbox behaviour exactly, not merely the source.

## What is now in custom

**1. §Ch15 gained an EXIT (KI-56).** The chapter was graded binary on
`GROUDON_AWAKENED_MAGMA_HIDEOUT` — a flag set the instant Maxie falls, four floors underground — so
it PASSED on runs that ended **permanently stranded**. A BFS over the whole eight-map warp graph
reaches 18 of 20 nodes from the return tile and misses only the exit warp and Jagged Pass: there is
no walk-out, because the two Strength pushes that opened 1F reset on map reload.
Fix: `collect_hideout_escape_rope()` takes the **Escape Rope the dungeon itself provides** at
`3F_3R (9,19)`, and `use_escape_rope_to_leave_hideout()` uses it, landing on `JAGGED_PASS (16,19)`.
`do_magma_hideout_chapter()` now ENDS with `leave_magma_hideout()`, deliberately **outside** the
flag guard so a resumed run still finishes the exit. Driven PASS.

**2. §Ch16 — the Slateport submarine theft** (`do_slateport_harbor_theft`), Segment 16.
‼ It does **not** walk through the harbor door: `SlateportCity_OnTransition` parks Capt. Stern on
`(28,13)`, the only tile touching that door, whenever `VAR_SLATEPORT_CITY_STATE == 1` — a var
**Ch15's own Maxie script sets**. `SlateportCity_EventScript_CaptStern` ends with `removeobject` /
`setvar ..., 2` / `warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`, so **talking to him carries the player
in**. The door path survives only as the resume branch.

**3. §Ch17 — the Lilycove Aqua Hideout** (`do_aqua_hideout_chapter`), Segment 17.
B1F is a warp-panel maze (**21 of its 25 warps return to B1F**), so the 18-hop route was BFS-solved
from the ROM warp table and every hop is graded on **(map AND tile)** — "did the map change?" cannot
distinguish a `B1F -> B1F` panel. Acceptance `FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE`.

**4. Heal stops before long hauls** (`SLATEPORT_ROUTE_HEALS`, and Ch17 heals at Lilycove).
‼ Measured: `post_maxie.ss1` hands Ch16 a party at **8.8% HP with five of six fainted**, and the
chapter was passing only *because* a whiteout heals. Nearest-first ordering matters: a Mauville-only
version left the run frame-identical to the unhealed one up to the whiteout frame.

## ‼ OUTSTANDING AT PROMOTION TIME — read before quoting any of this
* **Every chapter here has been driven, but only a handful of times.** Ch17 has **two** passes
  (sandbox + custom, frame-identical). A `.ss1` replays identical timing, so repeated passes on one
  anchor are **n=1**, not evidence of robustness. None of this has run in a production batch.
* **The routes are STATIC.** Both hideout routes were solved from ROM warp tables with
  `calculate_path`, which cannot see the grunts standing in those corridors. They survived contact
  on the runs above; that is not the same as being robust to a grunt standing one tile over.
* **The Master Ball at `AQUA_HIDEOUT_B1F (15,9)` is NOT collected** (nor the two Electrode guarding
  it at `(16,9)`/`(16,10)`). §Ch17 walks past it. Being addressed next.
* **`post_maxie.ss1` and `post_mtpyre.ss1` are still wiped-party anchors** (9% and 11%). The heal
  stops work around that; the anchors themselves were not re-captured.

---

## 2026-08-13 — PROMOTED: `modules/story/roster.py` (NEW) + the `modules/menuing.py` `PartyMenuExit` freeze fix

**User-approved promotion.** Two files; **post-copy drift: ZERO** (every `.py` under `modules/` and
`plugins/` compared file-by-file across both forks afterwards — 0 differing, 0 missing).
Restore point taken first: **`restore/2026-08-13-pre-roster-promotion`** (annotated, pushed).

### 1. `modules/story/roster.py` — NEW. Party ORDER, addressed by PERSONALITY VALUE.

Deposit and withdraw answer *"which Pokémon are in the party"*; nothing could answer *"in what
ORDER"*. Some content requires an order — the **Regi tombs** need a specific species first and
another last, a hard gate that fails **silently** if wrong.

* `plan_reorder` / `plan_last_slot` — PURE planners. Proven exhaustively: 720 permutations
  replayed, `repro_roster_reorder.py` 16/16.
* `reorder_party()` — drives `RotatePokemon` inside the bounded, script-aware harness pattern
  `_rotate_lead_safely` already proves in production.
* ‼ **Everything is keyed on PERSONALITY VALUE, never on slot index.** A slot is stale the instant
  a swap happens. Every step re-reads the party and re-finds the PID.

### 2. `modules/menuing.py` — `PartyMenuExit.wait_for_start_menu` now RAISES instead of spinning

Upstream's give-up branch sets Manual and then **falls through with no `yield`, no `break` and no
`raise`**, so once `counter > 60` with the loop condition still true it spins in **pure Python for
ever** — and `_yield_bounded` counts `next()` returns, so a loop that never yields never returns.
**A caller-side frame bound cannot save it; the process hangs.** This fork raises a `BotModeError`
the caller already handles. ‼ Found by an **adversarial review before the first drive**, not by a
hang — and it has still never been observed firing.

### ‼ WHAT WAS VERIFIED, AND HOW — driven, not diffed

`--driver roster --build custom` → **`ACCEPTANCE: PASS`**:
```
phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True manual=False
PHASE1 476 frames · PHASE2 258 · PHASE3 0 · PHASE4 690
```
**Frame-identical to the sandbox run** (476/258/0/690) — the same sequence to the frame, not merely
"both passed". Import resolution was checked separately (`find_spec` under `custom-pokebot` on the
path) so a frame-identical result could not be a silent fallback to the sandbox tree.

Six swaps, every one landing its PID check **first attempt**, including
**`RotatePokemon(i, j != 0)` — a path nothing in this project had ever driven.**

### ‼ OUTSTANDING AT PROMOTION TIME — read before quoting any of this
* **`reorder_party()` has ZERO production callers.** This is forward-looking capability for the
  Regi arc; the only thing that exercises it is `--driver roster`.
* **The driver has been run on ONE anchor** (`post_dive.ss1`, a 6-mon party). A `.ss1` replays
  identically, so repeated passes are **n=1**. Untested: parties of <6, a party with a fainted mon
  in a slot being swapped, and any run where a field script fires mid-menu.
* **KI-71 (OPEN): roster.py's own "we were dropped to MANUAL" guard is UNREACHABLE mid-swap.**
  `main.py:145-147` clears `controller_stack` on the frame after `set_manual_mode()`, abandoning the
  suspended generator before the guard can run. The guard is honest in intent and dead in practice.
* **KI-70 (OPEN): `_rotate_lead_safely` has the same "returns before control is back" shape** that
  was fixed here — on the hottest path in the bot. Measured `controllable_on_return=True`, **n=1**,
  deliberately not fixed.
* The `PartyMenuExit` fix is proven only by construction and review — **never by a reproduced
  freeze**.

---

## 2026-08-13 (later) — PROMOTED: KI-63's Dive-learner acquisition (`deposit_one_dead_weight` + the `_needs_party_slot` piggyback)

**User-approved promotion.** Two files; **post-copy drift: ZERO** across every `.py` under
`modules/` and `plugins/`. Restore point taken first:
**`restore/2026-08-13-pre-ki63-promotion`** (annotated, pushed).

### 1. `modules/story/pc_trip.py` — NEW `deposit_one_dead_weight()`

Frees **exactly one** party slot at a Poké Centre PC. It had to be written because **neither**
existing deposit path can free a slot *before* a catch — which is what `ensure_hm_learner` needs,
since it raises on a full party *before* it ever looks for a hunting ground:
* `withdraw_from_box` opens `target = find_in_box(pids); if target is None: return` — with nothing
  yet boxed it **returns having done nothing**; its deposit block is reachable only as a side
  effect of withdrawing an already-boxed PID.
* `deposit_dead_weight_if_worth_it` *is* a standalone one-deposit primitive but is a **silent
  no-op** behind `POKEBOT_PC_ROTATION`, pinned 0 and measured harmful.

‼ The contract is a **postcondition** ("there is now room"), verified by re-reading the party —
never by "the PC call returned". It inherits `find_dead_weight`'s **sole-HM-carrier exemption**, so
the party's only Surf user cannot be boxed by it.

### 2. `modules/modes/util/higher_level_actions.py` — the `_needs_party_slot` piggyback

An **opt-in** hook inside `heal_in_pokemon_center`, between the nurse and the exit, mirroring the
two hooks already there ("piggyback, do not detour"). Deliberately **not** gated on
`POKEBOT_PC_ROTATION` — that flag fires on *every* heal and strips teams to the floor; this fires
only when a caller has explicitly asked for room.

### ‼ VERIFIED BY DRIVING `--build custom`, never by a diff

```
[setup] build=custom
[divelearner] STEP2 party 6 -> 5 freed=True            (Skitty L17 deposited)
[divelearner] STEP3 balls 19 -> 17 caught=True         (Marill L13)
[divelearner] VERIFY knows_dive=True can_dive=True surf_intact=True
              '5:MarillL13[Tackle,Dive,Tail Whip,Water Gun]'
[divelearner] ACCEPTANCE: PASS
```
**Frame-identical to the sandbox run** (both end at f36047). Import resolution checked separately
with `find_spec` under `custom-pokebot`, so a frame-identical result could not be a silent fallback
to the sandbox tree.

### ‼‼ OUTSTANDING AT PROMOTION TIME — THE HEADLINE IS NARROWER THAN "KI-63 IS FIXED"

* **THE CAPABILITY IS PROVEN; PRODUCTION IS NOT WIRED.** `_needs_party_slot` has **no setter
  anywhere in `modules/` or `plugins/`** (verified by grep) — only `--driver divelearner` sets it.
  **In a real `StoryMode` run the piggyback never fires**, `ensure_hm_learner(HM08)` still raises
  *"the party is full"*, and the chapter still ends there. Wiring `story_mode.py` to catch that
  error and set the flag is the remaining work. **Do not read this promotion as "§Ch21 is unblocked
  in production".**
* **§Ch21 itself still has to be BUILT.** This removes its blocker.
* **The learner is a Marill L13 — 36 levels below the team.** An HM slave that `find_dead_weight`
  would want to box on a later trip unless the sole-carrier exemption covers it.
* **One anchor, `post_dive.ss1`.** A `.ss1` replays identically, so two passes are **n=1**.
  Specifically untested: a party containing an **egg** (the egg-count bug this file's own history
  records was found by review, not by a run), a box that is full, and a hunt that runs out of balls.
* **The ground used is Route 117** (Marill, 10% of the land table at L13, 1,055 waypoints). The
  better Shoal Cave ground was deliberately NOT adopted here.

---

## 2026-08-14 — PROMOTION: five files, USER-APPROVED. Drift sandbox↔custom is back to ZERO.

**The user approved promotion in the same message that asked work to continue**, after being told
plainly that until it happened `custom-pokebot` still carried the derail they had watched live.

**Restore point taken FIRST and pushed:** `restore/2026-08-14-pre-promotion-5files` (annotated).
Rollback target if anything below regresses.

### What was promoted, and why each earns its place

| file | what it carries | evidence it works |
|---|---|---|
| `modules/story/counter_hunt.py` | ‼ **THE USER-OBSERVED SLUGMA/WINONA DERAIL FIX.** `box_counter_pid` now accepts a MOVE answer, not only a TYPE match; and `catch_confirmed()` replaces a party-COUNT delta with an IDENTITY verdict so a Shedinja spawn cannot fake a catch. | `repro_box_counter_move_test.py` — fault-injected A/B (exit 1 → exit 0), parity gate, 22 checks. **Re-run against THIS fork: `--build custom` → exit 0.** |
| `modules/pokemon_party.py` | **KI-78 STAGE 0 — DETECT ONLY.** Logs LOUD when two party mons share a personality value (Ninjask/Shedinja do). ⛔ Behaviour deliberately UNCHANGED; the composite-key fix is NOT written. | compile + gate suite; behaviour is by construction identical (still returns `matches[0]`) |
| `modules/map_path.py` | KI-59: the `Impassable *` entry-vector inversion + the new `blocked_exit_directions` exit rule. | `repro_impassable_dirs.py` (exit 1 → 0, 29/29 → 0/29); A/B on `VICTORY_ROAD_1F` with a byte-identical `MOSSDEEP_CITY` collateral control |
| `modules/story/early_game.py` | KI-63's `ensure_hm_learner_making_room` (frees ONE slot, retries once) + the corrected `FLAG_SYS_USE_STRENGTH` comments. | `repro_hm_slot_wiring.py` (22/22, fault-injected); the flag correction was MEASURED live (`False` right after the ROOM1→ROOM2 warp) |
| `plugins/custom_modes/story_mode.py` | KI-63's two HM call sites wired to the above. | same gate — it exists precisely because this chain had one link missing before |

### Verification — DRIVEN, not diffed (the standing rule)

* ✅ **Drift re-measured after the copy: ZERO** (`modules/` + `plugins/`, hash-compared, both
  directions — custom holds no file sandbox lacks).
* ✅ `probe_chapter_order.py --build custom` → **exit 0**.
* ✅ **`repro_box_counter_move_test.py --build custom` → exit 0**, and it now **asserts which fork
  it imported** before testing anything.
  ‼ **THE GATE WAS MADE BUILD-AWARE DURING THIS PROMOTION, BECAUSE IT COULD NOT SEE THIS FORK.**
  It hard-coded `sandbox-pokebot`, so after ANY promotion nothing verified the fix had actually
  landed here — the promoted tree could be copied incompletely and every gate would still read
  green. That is the same "chain of correct parts with one link missing" shape
  `repro_hm_slot_wiring.py` exists for, and it was live in our own promotion procedure.
* ✅ **A live drive against this fork** (`--driver ch20dive --build custom`) — result recorded in
  `07-CHANGELOG.md` for the same date.

### What this does NOT mean

* ⛔ **§Ch20 is still NOT a chapter in either fork.** No module in `modules/story/`, nothing wired
  into `story_mode.py`, and the §Ch20 drivers inject Dive with a debug write. The ladder is still
  **20 of 24** here.
* ⛔ **KI-78 is NOT fixed** — this fork now *detects* the PID collision and still acts on the first
  match, exactly as sandbox does. `pc_interaction.py`'s deposit and **release** paths remain
  exposed; the composite-key stage is planned, not written.
* ⚠ The Slugma fix is proven by a fabricated-fixture A/B, **not** by re-running the user's original
  failing scenario end to end. That repro (a Nincada evolving into a full party, then a counter
  hunt, then a heal) is still owed.

---

## 2026-08-14 (later) — PROMOTION: KI-78 Stage 1, the identity fix. USER-APPROVED. Drift back to ZERO.

**The first promotion executed by `tools/story-dev/promote.py` rather than by hand** — the
procedure encoded as a tool that REFUSES, written because the previous hand-run promotion the same
day still shipped with a hole (a gate that could not see this fork at all).

**Restore point:** `restore/2026-08-14-pre-promotion-ki78` (annotated, pushed, and **verified
present on origin by the tool before it would copy anything** — a rollback target that exists only
on one machine is not a rollback target, and the tool refuses on exactly that).

### Promoted (3 files, drift 3 → 0)

| file | what it carries |
|---|---|
| `modules/pokemon.py` | the shared `same_pokemon` predicate — identity is **(personality, species)** |
| `modules/pokemon_party.py` | `get_index_for_pokemon` on that predicate, the **R6** evolved-since-capture re-resolve, and the **physical-slot return** fix |
| `modules/pokemon_storage.py` | `contains_pokemon` moved onto the shared predicate (`get_slot_for_pokemon` already used that key — refactored so the pair cannot drift again) |

### Why this one mattered more than most

⛔ **A Shedinja carries the SAME personality value as the Ninjask it came from** (`CopyMon` is a
memcpy that never rewrites it — `src/evolution_scene.c:548-583`, `src/pokemon.c:4419-4422`), and
the spawned twin always sits in the LATER slot. The old first-match lookup therefore resolved a
request aimed at one twin to the other — and its callers are `pc_interaction.py` **DEPOSIT
(`:464`)** and **RELEASE (`:505`, permanent, no undo)**. *"Release the Shedinja"* destroyed the
Ninjask. Until this promotion `custom-pokebot` carried the **warning** for that and not the
**fix**.

### Verification — DRIVEN and BUILD-SCOPED, not diffed

* ✅ Copy verified by the tool: drift **0 in both directions**, **3/3 byte-identical**, 0 orphans.
* ✅ **`repro_pid_identity_key.py --build custom` → exit 0**, and it **asserts which fork it
  imported** before testing anything. Includes the hole case: with a gap at slot 0 the Ninjask
  must resolve to **physical slot 1**, not list position 0.
* ✅ **`repro_box_counter_move_test.py --build custom` → exit 0** (the earlier Slugma fix,
  re-confirmed live in this fork).
* ✅ A live drive against this fork — result recorded in `07-CHANGELOG.md` for the same date.

### What this does NOT mean

* ⛔ **KI-78 is not fully closed.** The residual collisions stay open and are named in its entry:
  debug-fabricated identical pairs (R2), corrupt/Bad-Egg box slots (R3), Battle Frontier rentals
  (R5), and **R6** — a mon that evolves between capture and lookup, which is handled but
  **unexercised by any live caller today**.
* ⛔ **§Ch20 is still NOT a chapter** in either fork; the ladder remains **20 of 24**.
* ⚠ The identity fix is proven by fabricated-fixture A/B and by gates, **not** by reproducing the
  user's original failing run end to end. That repro is still owed.


## 2026-08-15 — PROMOTED: party accounting Stage 0, the heal's PC reporting, and the (P4) foundations (5 files, USER-APPROVED)

Promoted from `sandbox-pokebot/` with `tools/story-dev/promote.py`, the tool that refuses.
Restore point: **`restore/2026-08-15-pre-promotion-stage0-p4`** (annotated, pushed, and verified
present ON ORIGIN by the tool before it would copy anything).

| file | what it brings to this fork |
|---|---|
| `modules/party_accounting.py` (NEW) | PARTY ACCOUNTING STAGE 0 — readers for **A** (`gPlayerPartyCount`) and per-slot occupancy, plus a divergence log (HOLE / OVERFLOW / INVALID exact, STALE sampled 1-in-300). ⛔ Wires NO call site. |
| `modules/pokemon_party.py` | Stage 0's three log-only observer hooks inside `get_party()`, and a docstring on `get_party_size()` saying which question **B** answers. |
| `modules/modes/util/higher_level_actions.py` | ‼ **The heal's three PC piggybacks now REPORT instead of failing silently.** Until this promotion, this fork's heal path collapsed *worked* / *nothing to do* / *it threw* into one silence — the state in which the user's Slugma/Winona derail was invisible. Adds `_piggyback_report()` and the pure `counter_withdraw_outcome()`. |
| `modules/debug_utilities.py` | `debug_write_box_slot()` — the (P4) fixture's missing half. ⛔ **UNPROVEN AGAINST A LIVE EMULATOR**; its own docstring says so and the P4 driver must open with a read-back control. |
| `modules/story/counter_hunt.py` | `POKEBOT_BOXCOUNTER_TYPEONLY_A` — a permanent fault hook restoring the pre-fix TYPE-ONLY behaviour on demand. Default OFF; the fix is what runs. |

### Evidence — a copy is NOT evidence, so this fork was DRIVEN

* ✅ Tool-side: drift **0 in both directions**, **5/5 byte-identical**, 0 orphans.
* ✅ **`--driver ch20dive --build custom` → `legs=6/6 at_entrance=True got_out=True
  can_continue=True  ACCEPTANCE: PASS`** — matching the sandbox result exactly.
* ✅ **Four `--build custom` gates, each ASSERTING which fork it imported before testing:**
  `repro_party_accounting.py` (33 checks), `repro_heal_piggyback_reporting.py` (20 checks),
  `repro_box_counter_move_test.py`, `repro_pid_identity_key.py` — all exit 0.
  That assertion is the check that was missing from an earlier promotion, when a gate hard-coded
  `sandbox` and therefore could not see whether the promoted fix had landed at all.

### What this does NOT mean

* ⛔ **(P4) — the end-to-end repro of the user's actual failing run — is STILL OWED.** What landed
  here is its *observability* half plus build steps 1-3. The `boxcounter` driver does not exist in
  either fork. Design: `PROJECT KNOWLEDGE/ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md`.
* ⛔ **`debug_write_box_slot` has never written to a live emulator.** Its address arithmetic is
  verified against the reader and `data[:80]` is proven a valid boxed record by gate — but the
  write itself is unexercised. Do not build on it without a read-back control.
* ⚠ **Party accounting is STAGE 0 only: it OBSERVES and decides nothing.** The measurement it
  produced (7 drives, 280,707 recomputes, no divergence) is over §Ch20 DUNGEON content with a
  STATIC party, so the party-mutating cases were never exercised. It is **not** licence to
  re-point the ~35 capacity-shaped call sites at A.
* ⛔ **§Ch20 is still NOT a chapter** in either fork; the ladder remains **20 of 24**.

### 2026-08-15 (later) — re-promoted `modules/debug_utilities.py`, DOCSTRING ONLY

`debug_write_box_slot` is now **PROVEN AGAINST A LIVE EMULATOR** — `--driver boxwrite` →
`ACCEPTANCE: PASS` (a Slugma L15 written to box 0 slot 0 and read back through the PRODUCTION
reader with matching PID, species, level and `knows_move("Rock Throw")`, `not_in_party=True`), so
its `NOT YET PROVEN` warning was retracted. ⛔ **No behaviour change — a comment only**, which is
why this was not re-driven; the drive that matters is the one named above. The docstring still
requires the (P4) driver to open with its own read-back control, because this function working in
isolation does not make a fixture correct on the day. Restore point
`restore/2026-08-15-pre-promotion-boxwrite-docstring`. Drift 1 → 0, 1/1 byte-identical.

## 2026-08-15 — `modules/story/counter_hunt.py`: the "Winona needs …/Electric" error corrected (COMMENT-ONLY, user-approved)

**Promoted:** `modules/story/counter_hunt.py`, sandbox → custom. **User-approved 2026-08-15.**
Restore point `restore/2026-08-15-pre-promotion-counterhunt-comment` (annotated, pushed, and
verified on origin by `promote.py` before it copied). Drift **1 → 0**, **1/1 byte-identical**.

**What changed, and why it is worth a promotion at all.** `box_counter_pid`'s docstring said
*"Winona needs Rock/Ice/Dragon/Electric"*. **Electric is wrong**, and had been for a year.
`needed` is derived from the boss's ACE alone (`_boss_plan_is_hopeless`, `story_mode.py:1600-1606`,
requiring `>= 2.0` across ALL ace types); Winona's ace is **Altaria L33, Dragon/Flying**; Electric
is **0.5x into Dragon** × 2.0x into Flying = **1.0 — NEUTRAL**. Production therefore never yields
it. The claim was mis-scoped rather than invented: Electric IS 2.0x on her other four (Flying)
mons. The same wrong set stood in FOUR places that were copies of one another — this file, the P4
design note, `04-HANDOFF.md`, and the Stage 1 driver — and none of them was ever checked against
the type chart until `--driver boxcounter`'s new `needed_ok` control DERIVED it and refused to run
(`derived=['Dragon','Ice','Rock'] ; literal=['Dragon','Electric','Ice','Rock'] ; needed_ok=False`).

⛔ **NO BEHAVIOUR CHANGE — every changed line is inside the docstring**, proven by a full
`diff -u custom … sandbox` read BEFORE the restore point was tagged, not asserted afterwards.

‼ **VERIFIED BY DRIVING ANYWAY, because a copy is not evidence** (and the standing rule does not
carve out comment-only changes — the previous comment-only promotion, `boxwrite-docstring` above,
explicitly skipped the drive, and this one deliberately does not):
* `--driver boxcounter2 --build custom` **ARM B** → `moved=True knows_rock_throw=True
  lead_is_counter=True noop_attributed=True`, `ACCEPTANCE: PASS`.
* `--driver boxcounter2 --build custom` **ARM A** (`POKEBOT_BOXCOUNTER_TYPEONLY_A=1`) →
  `_hunted_counter_pids=[]`, `still_boxed=True not_in_party=True`, `ACCEPTANCE: PASS`.
* Four `--build custom` gates, each of which ASSERTS which fork it imported before testing:
  `repro_box_counter_move_test`, `repro_pid_identity_key`, `repro_party_accounting`,
  `repro_heal_piggyback_reporting` — all exit 0.

## 2026-08-15 — `modules/story/pc_trip.py`: KI-79, the PC withdraw now verifies BY IDENTITY (BEHAVIOUR CHANGE, user-approved)

**Promoted:** `modules/story/pc_trip.py`, sandbox → custom. **User-approved 2026-08-15.**
Restore point `restore/2026-08-15-pre-promotion-ki79-pctrip` (annotated, pushed, verified on
origin by `promote.py` before it copied). Drift **1 → 0**, **1/1 byte-identical**.
⛔ **Unlike the `counter_hunt.py` promotion earlier the same day, this one CHANGES BEHAVIOUR.**

**What changed.** `withdraw_from_box` used to end with `after = len(get_party())` and then print
*"{name} is in the party"* — a COUNT announcing an IDENTITY. It could not fail: the make-room
deposit CANCELS the withdraw, so the count is unchanged on success (party 6 → 6) **and** when
nothing happened; and the function never raises, so a silent PC failure printed green. It now
verifies `(personality_value, species)` present in the party **AND** `contains_pokemon(target)`
False in the box — both halves, since in-party-only could be a copy and gone-from-box-only a
release — after a 2-frame yield, because party and storage are cached per frame. On failure it
prints a loud named `‼ THE WITHDRAW DID NOT LAND …` and **still does not raise**: the original
contract (a PC hiccup must not destroy a heal that already succeeded) is preserved.
Also adds the permanent `POKEBOT_PCWITHDRAW_FAULT` hook (registry §B).
‼ Identity is `(pid, species)`, never the bare PID — a Shedinja carries its Ninjask's PID (KI-78).

**‼‼ VERIFIED BY A THREE-POINT A/B, BECAUSE A BYTE-COMPARISON CANNOT PROVE WHAT RUNS.**
For a behaviour change, "1/1 byte-identical" only proves the file was COPIED. These three runs —
the first of which is capturable ONLY before the promotion, and is therefore committed — prove the
new branch is what actually EXECUTES in custom:

| # | run (all `--driver boxcounter2 --build custom`) | result | what it proves |
|---|---|---|---|
| 1 | **BEFORE** promotion, `POKEBOT_PCWITHDRAW_FAULT=1` | `Story: PC — Slugma is in the party` → **ACCEPTANCE: PASS** | the hook is ABSENT in custom; the variable is INERT |
| 2 | **AFTER** promotion, `POKEBOT_PCWITHDRAW_FAULT=1` | `‼ SKIPPING the PC interaction` + `‼ THE WITHDRAW DID NOT LAND. Slugma in_party=False still_boxed=True` → **ACCEPTANCE: FAIL** | ⇒ **the new code is LIVE in custom** — the identical command flipped |
| 3 | **AFTER** promotion, unfaulted | `Story: PC — Slugma is in the party; party is now 6.` → **ACCEPTANCE: PASS** | no regression on the happy path |

📁 Raw transcripts committed, by name:
`tools/story-dev/evidence/2026-08-15-ki79-promotion-BEFORE-custom-faultvar-set.stdout.txt`,
`…-AFTER-custom-FAULTED.stdout.txt`, `…-AFTER-custom-UNFAULTED.stdout.txt` (+ `.driver.txt` twins).
⛔ **Run 1 does NOT prove the variable was 'inert' — a run of code that never READS a variable cannot show anything about it, and its output is indistinguishable from an unfaulted run.** (A Tier 1 reviewer caught exactly that overclaim.) What run 1 DOES prove is that the identical command PASSED before the promotion. The *absence of the hook* is proven from git instead, which is stronger and re-runnable by anyone: `git show restore/2026-08-15-pre-promotion-ki79-pctrip:custom-pokebot/modules/story/pc_trip.py | grep -c POKEBOT_PCWITHDRAW_FAULT` → **0** (sandbox at the same tag → **3**; custom now → **3**).
‼ **stdout is captured separately on purpose** — production's `console.print` output, which is the
entire subject of this fix, is NOT in the driver's log. That lesson cost a Tier 1 kick-back earlier
the same day, when running arm 2 overwrote arm 1's transcript and left a true claim unverifiable.

**Also green on custom:** `boxcounter2 --build custom` **ARM A** → `ACCEPTANCE: PASS` (transcript: `tools/story-dev/evidence/2026-08-15-ki79-promotion-AFTER-custom-ARMA.stdout.txt`, which logs `ARM=A (POKEBOT_BOXCOUNTER_TYPEONLY_A='1')` so the arm is self-evidencing); and four `--build custom` gates, each of
which ASSERTS which fork it imported: `repro_box_counter_move_test`, `repro_pid_identity_key`,
`repro_party_accounting`, `repro_heal_piggyback_reporting` — all exit 0.

⚠ **What this does NOT change:** the message is now trustworthy, but no CALLER acts on it —
`withdraw_from_box` still returns nothing and still never raises. A caller that needs to KNOW
whether the counter arrived must check identity itself (which `--driver boxcounter2` does).

---

## 2026-08-16 — `plugins/custom_modes/story_mode.py`: the `CREDIBLE_ANSWER_POWER` example corrected (COMMENT-ONLY, user-approved)

**Promoted:** `plugins/custom_modes/story_mode.py`, sandbox → custom. **User-approved 2026-08-16.**
Restore point **`restore/2026-08-16-pre-promotion-credible-answer-comment`** (annotated, pushed,
and verified on origin by `promote.py` before it copied).

**What changed, in full.** The explanatory comment on `CREDIBLE_ANSWER_POWER = 75` justified the
threshold with a worked example that **does not exist**: *"Thunderbolt vs Winona (270)"*. Winona's
ace is **Altaria, Dragon/Flying**, and Electric is `0.5x` into Dragon `x 2.0x` into Flying = **1.0,
NEUTRAL**. Production agrees — it derives `needed = ['Rock', 'Ice', 'Dragon']`, with no Electric.
Replaced with a real example: **Ice Beam into Altaria (`95 x 4.0 = 380`)**, plus an inline
`⛔ NOT Thunderbolt` marker so the false example cannot come back quietly.

**⛔ WHY IT MATTERED ENOUGH TO PROMOTE.** It is the only worked example attached to the constant
that `_boss_plan_is_hopeless` uses to decide whether a party has an answer — the exact predicate the
whole KI-80 round is built on. Anyone re-tuning that threshold from its own comment would have been
calibrating against a matchup that cannot occur. It was the **FIFTH** surviving copy of that error,
and it hid from the sweep that fixed the other four because it is *prose about a threshold* and
names no type list.

### ✅ PROVED BEHAVIOUR-NEUTRAL BEFORE COPYING — not asserted from "the diff looks like comments"

```
ast.dump(ast.parse(sandbox story_mode.py)) == ast.dump(ast.parse(custom story_mode.py))
  -> IDENTICAL, 323,580 chars each
```
‼ **And that check was FAULT-TESTED so it cannot be vacuous:** flipping
`CREDIBLE_ANSWER_POWER = 75` to `76` in memory makes the comparison return **False**. A check that
cannot fail proves nothing; this one demonstrably can.
⛔ Both forks are **4135 lines** — the edit was deliberately made **net-zero on line count**, so no
`story_mode.py:NNNN` citation shifts in EITHER fork. That matters because `06`/`07`/`08` are
**append-only** and are full of such citations; they may not be rewritten to follow a line shift.

### VERIFIED BY DRIVING — because a copy is not evidence

| run (`--build custom`) | result |
|---|---|
| `--driver ki80ladder` arms 1-3, `batch2_run04_wedge.ss1` | `NOGRASS → LADDER`, `GRASS_FODDER → LADDER`, `GRASS_STRONG → PLAIN_ESCALATION` — **ACCEPTANCE: PASS** |
| `POKEBOT_KI80_ARM4=1 --driver ki80ladder`, `fortree_gym_wedge.ss1` | CONTROL-A `hopeless=False`, CONTROL-B `VICTORY_ROAD_1F 40 vs 39 → fodder False`, `OUTCOME=PLAIN_ESCALATION` — **ACCEPTANCE: PASS** |

Plus four `--build custom` gates, each of which ASSERTS which fork it imported:
`repro_box_counter_move_test`, `repro_pid_identity_key`, `repro_party_accounting`,
`repro_heal_piggyback_reporting` — **all exit 0**.
📁 Transcripts: `tools/story-dev/evidence/2026-08-16-promotion-credible-comment-AFTER-custom-arms123.stdout.txt`
and `…-arm4.stdout.txt`.

⚠ **HONEST SCOPE — what driving can and cannot prove here.** Unlike the KI-79 promotion, there is
**no three-point A/B and there cannot be one**: a comment change has no branch to flip, so no
command can go PASS→FAIL→PASS across it. The AST equality above is the *stronger* proof for this
class of change, and the drives exist to show the file still loads and behaves in custom — not to
show a new branch running. ⛔ Do not cite these drives as evidence that "the fix is live"; cite the
AST identity and the byte-compare (`1/1 byte-identical`, drift 0 both directions) for that.

---

## 2026-08-16 — `plugins/custom_modes/story_mode.py`: KI-80's DECOUPLING (a BEHAVIOUR change, user-approved)

**Promoted:** `plugins/custom_modes/story_mode.py`, sandbox → custom. **User-approved 2026-08-16.**
Restore point **`restore/2026-08-16-pre-promotion-ki80-decoupling`** (annotated, pushed, verified on
origin by `promote.py` before it copied). Result: **0 differing, 0 orphaned, 1/1 byte-identical.**

**What changed.** `:1901` `if grass_is_fodder and boss_teaches:` → **`if boss_teaches:`**, and
`:1925`'s `boss_mode = True` (with its target bump and message) moved behind a fresh
**`if grass_is_fodder:`**. One boolean had been answering two unrelated questions and gating KI-23's
counter-catch machinery on the wrong one ⇒ **giving a boss a training area silently deleted its
counter machinery**, behind a healthy-looking `"training harder before re-attempting"` line.

### ‼‼ PROVEN BY A THREE-POINT A/B AGAINST `--build custom` — a byte-compare only proves a COPY

| point (identical commands, `--build custom`) | BEFORE | AFTER |
|---|---|---|
| `POKEBOT_KI80_DECOUPLED=1` | ⛔ **FAIL** — `GRASS_STRONG -> PLAIN_ESCALATION (expected LADDER)` | ✅ **PASS** — all three arms `-> LADDER` |
| bare command (the OLD coupled expectation) | ✅ **PASS** | ⛔ **FAIL** — `GRASS_STRONG -> LADDER (expected PLAIN_ESCALATION)` |
| `POKEBOT_KI80_ARM4=1` (mirror-regression guard) | ✅ **PASS** | ✅ **PASS** — `OUTCOME=PLAIN_ESCALATION`, `drift=none` |

⇒ **the two flipping points moved in OPPOSITE directions and the invariant one did not move.** That
is what a byte-compare cannot tell you: the new branch is what RUNS in custom, and KI-23's mirror
regression did **not** come with it.
⛔ **The BEFORE half is unrepeatable once the copy happens, so it was run and COMMITTED FIRST** — in
`1c11927e`, one commit before the restore tag. That ordering is the KI-79 rule.

**Also green on custom:** four `--build custom` gates, each of which ASSERTS which fork it imported
(`repro_box_counter_move_test`, `repro_pid_identity_key`, `repro_party_accounting`,
`repro_heal_piggyback_reporting`) — all exit 0. And `repro_boss_grass_gate.py` (suite #24)
**SELF-RETIRED**: it now reports *"the counter-ladder is no longer gated on `grass_is_fodder` (the
coupling this gate guards is GONE)"* and exits 0. That is its designed end state, not a failure.
⚠ That gate is **sandbox-scoped** (it has no `--build` flag), so it speaks for sandbox only.

**BLAST RADIUS — arithmetic MEASURED, behaviour INFERRED.** Only bosses with BOTH a `grass` key and
`ace_types` can change: **Brawly** gains the machinery across his whole band (GRANITE_CAVE_1F
`wild_max` 10 vs band 14-16), **Roxanne** at `team_max` 13-16, **Wattson** at 20-22. **Norman is
unchanged** (ROUTE102 `wild_max` 4 — always fodder already, *by design*); the **Rustboro rival is
unaffected** (no `ace_types`). ‼ **No Brawly/Roxanne/Wattson run exists** — only Winona's fixtures
were driven; the rest is inference from shared code paths, and is labelled as such everywhere.

⚠ **A REAL CONSEQUENCE, STATED NOT BURIED:** at those three bosses a hopeless diagnosis can now end
a run with KI-23's honest `BotModeError` where it previously ground on. Intended (KI-23 measured the
grinding path at 198 attempts / 41 losses / 41 whiteouts without converging) and safe — the raise is
caught at `:4080-4081`, sets `outcome = "derailed"`, and does not crash a batch.

**OPEN AND TRACKED:** `#24-zerokocounter` — should `boss_teaches` come off the gate too? Not shipped
because **no arm can discriminate it** (all four seed `kos = 1`), and an audit derived that it would
need TWO new arms plus a frequency measurement first.
📁 Transcripts: `tools/story-dev/evidence/2026-08-16-ki80-PROMOTION-{BEFORE,AFTER}-custom-*`.

---

## 2026-08-16 — the KI-81 WHITEOUT GUARD: 8 handlers that silently swallowed an abort (BEHAVIOUR change, user-approved)

**Promoted:** `modules/modes/util/higher_level_actions.py`, `modules/story/pc_trip.py`,
`modules/story/mossdeep_gym.py`. **User-approved 2026-08-16.** Restore point
**`restore/2026-08-16-pre-promotion-ki81-abort-guard`** (annotated, pushed, verified on origin by
`promote.py` before it copied). Result: **0 differing, 0 orphaned, 3/3 byte-identical.**

**What it fixes.** `StoryAbort` is a `BotModeError` is an `Exception`, so **every** broad handler in
the story path catches a whiteout. KI-67 identified this and fixed the two CHAPTER retry loops that
had been *observed* failing — **the class was never swept.** Triage proved the probe does not
over-flag: `mossdeep_gym.py:465` is a *different* `try` from KI-67's, and after a whiteout it tried
the **second gym door on a dead run**, then raised *"won the badge but could not get out of the
gym"* — a **fabricated diagnosis naming doors** while the player stands outside a Pokémon Center.

### ‼‼ PROVEN BY A MEASURED BEFORE/AFTER, NOT A BYTE-COMPARE

| point (`--build custom`) | BEFORE | AFTER |
|---|---|---|
| `probe_abort_swallowing.py --build custom` | **53** candidates | ✅ **45** |
| guarded handlers, `pc_trip.py` | **0** | ✅ **3** |
| guarded handlers, `higher_level_actions.py` | **0** | ✅ **4** |
| guarded handlers, `mossdeep_gym.py` | **1** (KI-67's) | ✅ **2** |
| `PathFindingError` routed through the guard | n/a | ✅ **False** (the split survived the copy) |
| mechanism, imported from **custom** | n/a | ✅ latch clear → swallows; latch set → re-raises |

⛔ **The BEFORE half is unrepeatable once the copy happens, so it was run and COMMITTED FIRST**, in
`6de47264`. ‼ `probe_abort_swallowing.py` gained `--build` **for exactly this reason**: a
byte-compare proves a file was COPIED; only running the instrument against the fork proves the
fork's **own handlers** gained the guard.

**The guard** is `reraise_if_aborting(error)` as the **first** statement of each handler. It is
**LATCH-keyed, not type-keyed** — the point, because a retry loop that catches an error and raises a
fresh one destroys `StoryAbort`'s identity, and only the latch survives that conversion. Imports are
function-local **by necessity**: `early_game` imports `higher_level_actions` at module level.

⛔ **`withdraw_from_box`'s "Never raises" CONTRACT CHANGED** to *"never raises for a PC problem"*,
and its docstring moved in the same edit. A whiteout is not a hiccup: the player has respawned,
there is no heal left to protect, and the latch is cleared only by `StoryMode.run`.

⛔⛔ **AN ADVERSARIAL REVIEW CAUGHT A REAL DEFECT IN THE FIRST CUT, and it is worth knowing here.**
`talk_to_npc`'s handler also catches `PathFindingError`, which is a **`RuntimeError`, NOT a
`BotModeError`**. `StoryMode.run()` catches only `BotModeError`, so a re-raised `PathFindingError`
would have **escaped whiteout recovery entirely**, leaving the module-global abort latch **stuck
TRUE** — after which `ev_train.py` and `pokecenter_loop.py` (non-Story modes with no handling around
`heal_in_pokemon_center`) would re-raise a **benign** PC hiccup with no visible link to the
whiteout. **A guard that can leak a global is worse than the silence it replaced.** Fixed by
splitting the handler; AST-verified before AND after the copy.

**Also green on custom:** four `--build custom` gates that each assert which fork they imported
(`repro_box_counter_move_test`, `repro_pid_identity_key`, `repro_party_accounting`,
`repro_heal_piggyback_reporting`) — all exit 0.

⚠ **45 candidate sites REMAIN in both forks** (44 `early_game.py`, 1 `counter_hunt.py`) and are
deliberately **not** swept: CANDIDATE ≠ DOES, and `early_game.py` is the largest and most
timing-sensitive file here. Tracked as `#24-abortswallow`.
📁 Transcripts: `tools/story-dev/evidence/2026-08-16-ki81-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt`.

---

## 2026-08-16 — KI-65: a safety veto that could not evaluate now FAILS CLOSED (`modules/battle_move_replacing.py`)

**Divergence from upstream 40Cakes/pokebot-gen3.** Upstream's
`handle_move_replacement_dialogue` assigns `party_index` at exactly ONE place (`:371`) inside a
`try`. When `_read_offered_move` raises, the name is **never bound**, and two later reads of it
each sit inside a swallowing `except`:

* the **HM VETO** (`:397`, `except Exception: pass`) — the loudest possible silence, because a
  swallowed `UnboundLocalError` is indistinguishable from "the slot is not an HM, so the veto
  correctly did nothing";
* the **CantForgetHM re-pick** (`:280`, `except` → decline).

The veto's own comment calls it *"THE LAST LINE OF DEFENCE"* and names the exact path it must
cover — *"the `except` fallback right above which blindly picks slot 0 without consulting any
policy at all"*. **That fallback is precisely the path that leaves `party_index` unbound**, so the
last line of defence was structurally unable to defend against the one case it was written for.

**OUR CHANGE (two parts).** (1) declare `party_index: int | None = None` up front, turning
"unbound" into a value that can be TESTED; (2) explicit `if party_index is None:` guards at BOTH
read sites, which emit a message saying what could not be done and **DECLINE**.

⛔ **THIS IS A BEHAVIOUR DIVERGENCE, NOT A TIDY-UP.** Upstream, on that path, blindly confirms
slot 0. We decline. Rationale in `PROJECT KNOWLEDGE/06-DECISIONS-LOG.md` (2026-08-16): declining
is still an ANSWER, so the "never stall on the prompt" property is preserved, and it resolves
cleanly in ~430 frames; whereas confirming an unverifiable slot is the infinite
`AskWhetherToLearn → SelectMoveToReplace` loop that historically killed 2 of 5 overnight runs.
⚠ The cost is bounded and real: on a transient read failure the mon keeps its moves and is
re-offered on its next level-up.

**WHY IT MATTERS (measured, not argued).** With an injected MARSHTOMP whose **slot 0 is Rock Smash
(HM06)** and three forgettable moves, upstream's logic prints:
`"The game refused that slot (HM). Nothing else can be given up — declining the new move."`
**while Water Gun, Mud Shot and Bide are all forgettable — a provable lie the user can read.**

**PROMOTION EVIDENCE — a THREE-POINT A/B against `--build custom`, never a byte-compare:**

| point | build | fault_fired | lie_msg | honest_msg | gate |
|---|---|---|---|---|---|
| BEFORE | custom | 159 | **1** | 0 | **ACCEPTANCE: FAIL** |
| AFTER | custom | 87 | 0 | **1** | **ACCEPTANCE: PASS** |
| control | sandbox | 87 | 0 | 1 | **ACCEPTANCE: PASS** |

‼ `fault_fired` falling 159 → 87 on custom, to exactly the sandbox figure, is independent evidence
the new branch RUNS here rather than the file merely having been copied.
Restore point `restore/2026-08-16-pre-promotion-ki65`. Gate: `repro_ki65_unbound_party_index.py`
(#25 of 25), which drives the emulator and is fault-tested (reverting the file makes it FAIL).

⛔ **A THIRD PART WAS BUILT AND THEN REMOVED.** An `offer_read_failed` latch was added and written
up as preventing the ping-pong. An adversarial review refused the unmeasured claim, and the
isolated A/B proved it redundant — the veto guard forces `move_to_forget = 4` in the SAME iteration,
before any button is pressed. **Part (2)'s guard is the loop-preventer**; a comment at `:397` says
so, because a maintainer trusting the latch might otherwise "simplify" away the guard that works.

📁 Transcripts: `tools/story-dev/evidence/2026-08-16-ki65-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt`
and `...-CONTROL-sandbox.stdout.txt` — all three COMMITTED. ‼ The BEFORE arm was re-run against a
reconstruction of the pre-fix file from the restore tag, so it is a real transcript rather than
remembered numbers; it reproduced `fault_fired=159, lie_msg=1, ACCEPTANCE: FAIL` exactly.

⚠ **RESIDUAL, NOT CLOSED BY THIS:** a *bound but wrong* `party_index` of `-1` (from
`get_party_menu_cursor_pos`'s `set_manual_mode()` fallback) still flows past both guards —
`get_party()[-1]` is the LAST party member. A wrong-mon, not an exception. Tracked in KI-65.

---

## 2026-08-17 — KI-66: the faint chooser's on-field filter was comparing two different index spaces (`modules/battle_handler.py`)

**Divergence from upstream 40Cakes/pokebot-gen3.** In `handle_fainted_pokemon`, the set of
"Pokémon already on the field" (excluded from replacement candidates) is built from
`battler.party_index` — i.e. `gBattlerPartyIndexes`, which is in **field order** — and was compared
RAW against `party_in_menu = get_party()`. But `get_party()` is read *while the party menu is open*,
after `UpdatePartyToBattleOrder` has physically permuted `gPlayerParty` into **battle-slot order**.
The two spaces diverge, so the filter excluded the wrong slot.

**OUR CHANGE.** Map through `BattleState.map_battle_party_index` before adding to `_on_field`,
mirroring what `alive_slots` three blocks below has done since KI-34 — this filter simply never
copied it. On any mapping failure it falls back to the raw index, so the worst case is upstream's
behaviour rather than something new.

⛔ **THIS IS THE THIRD INDEX-SPACE BUG IN THIS ONE FUNCTION** (KI-18, KI-34, now KI-66), all the
same shape. A fourth is FILED but deliberately NOT changed (`#24-faintchooser-fourthspace`).

**WHY IT MATTERS (measured, in the Mossdeep Space Center multi battle alongside Steven).** The
filter excluded **Swellow while Swellow was on the BENCH** — proven by its send-out at `f21009` —
and failed to exclude the ally that WAS active. The replacement sweep was therefore left with a
candidate set containing only slots the ROM refuses unconditionally (`TrySwitchInPokemon` rejects
the partner's slots in any multi battle), costing **1263 frames against 59** on a clean faint and
tripping the harness's own `NO-PROGRESS x1200` watchdog.

**PROMOTION EVIDENCE — a THREE-POINT A/B against `--build custom`, never a byte-compare:**

| point | build | `_on_field` | faints | party-menu presses |
|---|---|---|---|---|
| BEFORE | custom | `[0,3]` then `[1,3]` ⛔ | 2 | 486 |
| AFTER | custom | `[0,1]` ✅ | 1 | 361 |
| control | sandbox | `[0,1]` ✅ | 1 | 361 |

Restore point `restore/2026-08-17-pre-promotion-ki66-onfield`. Driver: `--driver ki66faint`.
📁 Transcripts: `tools/story-dev/evidence/2026-08-17-ki66-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt`
and `...-CONTROL-sandbox.stdout.txt` — all committed.

⚠⚠ **DO NOT READ THE PRESS/FAINT COUNTS AS A SPEEDUP.** Press timing feeds battle RNG, so the after
runs are a DIFFERENT TRAJECTORY (one faint rather than two). What is controlled is CORRECTNESS:
`_on_field` equals the truth the party dump establishes, on every faint observed, before and after.

✅ **SINGLE-BATTLE REGRESSION CONTROL.** This filter runs in EVERY battle, and
`map_battle_party_index` does not return its input unchanged in a single battle. A separate A/B
(`--driver faintrepro --inject-shedinja-faint`, `route116team.ss1`, 120k frames) was **IDENTICAL**
across pre-fix and fixed builds through the whiteout — `STUCK-OW f6482`, `SAVED stall f7409`,
`NO-PROGRESS x1200 f7709`, `x3000 f9509` — so the change is **inert outside multi battles**.
📁 `evidence/2026-08-17-singlebattle-faint-{BEFORE-baseline,AFTER-onfield-fix}.stdout.txt`.

⛔ **NOT CLOSED BY THIS:** the OWNER filter (`alive_slots` has no original-trainer check) is
unfixed and proved INERT on this fixture — it needs its own discriminator. `:541-545` (the `None`
fallback, which has neither an owner nor an on-field filter) and `_util.py:522-587` are untouched.

---

## 2026-08-17 — FIVE FILES PROMOTED IN ONE ROUND (user-approved): the verdict change, the abort guards, and a comment-only correction

**Files:** `modules/story/pc_trip.py`, `modules/modes/util/higher_level_actions.py`,
`modules/story/early_game.py`, `modules/story/counter_hunt.py`, `modules/map_path.py`.
**Restore point:** `restore/2026-08-17-pre-promotion-all5` (annotated, pushed, verified on origin by
`promote.py` before it copied). Roll back HERE to undo all five.
**Executed by** `tools/story-dev/promote.py --restore-point … --go` → `5/5 byte-identical,
drift after 0, orphaned after 0`.

⛔ **A COPY IS NOT EVIDENCE.** Three groups went over together, so each carries its OWN
before/after discriminator rather than one shared "it copied":

| group | files | discriminator | BEFORE | AFTER |
|---|---|---|---|---|
| **(A) the withdraw VERDICT** (`#24-orphans` (1)) | `pc_trip.py`, `higher_level_actions.py` | `repro_withdraw_verdict.py --build custom` | **exit 1**, six named FAIL sites, and `withdraw_verdict_report` could not even be IMPORTED from custom | **exit 0**, 0 FAIL lines |
| **(B) the ABORT GUARDS** (`#24-abortswallow`) | `early_game.py`, `counter_hunt.py`, `higher_level_actions.py` | `probe_abort_swallowing.py --build custom` | **44 sites** | **36 sites** — the same number sandbox reads |
| **(C) the CAP COMMENT** (`#24-ki76correctness`) | `map_path.py` | bytes + AST | bytes DIFFER, AST equal, custom still asserted all three refuted claims | bytes IDENTICAL, AST still equal, refuted claims gone |

✅ **VERIFIED BY DRIVING THE REAL FORK, not by a diff:**
`story_harness.py saves/fortree_gym_wedge.ss1 --driver boxcounter2 --build custom` →
`verdict landed=True code=landed` and `[boxcounter2] ACCEPTANCE: PASS`.
‼ **The verdict line is the proof, not the PASS.** It is emitted only by the promoted path
(`withdraw_from_box`'s 3-tuple → the caller binding it → `withdraw_verdict_report`), and the BEFORE
measurement records that custom could not import that function at all.
Plus five `--build custom` gates that each ASSERT which fork they imported:
`repro_withdraw_verdict`, `repro_box_counter_move_test`, `repro_pid_identity_key`,
`repro_party_accounting`, `repro_heal_piggyback_reporting` — all exit 0.

‼ **THE RATCHET WAS TURNED.** `probe_abort_swallowing.py`'s custom baseline was lowered **44 → 36**;
otherwise the gain is unlocked and the ratchet goes slack. ⛔ **And the attribution is EARNED**: the
probe's own warning is *"do NOT claim the drop was caused by your change without an arm that removes
it"* — that arm exists and is committed, because the BEFORE half was captured and pushed in its own
commit (`0b1d8480`) minutes before the copy, with nothing else changing.

📁 **Transcripts, both committed:**
`tools/story-dev/evidence/2026-08-17-PROMOTION-{BEFORE,AFTER}-custom-all5.stdout.txt`.

⛔ **WHAT THIS DOES *NOT* MEAN.** (A) makes production able to READ a failed withdraw; it still does
not REACT to one — that half needs a heap-offset measurement and a USER ruling (`#24-orphans` (1)).
(C) changed a comment only: KI-76's two pathfinding defects are still OPEN (`#24-ki76correctness`).

---

## 2026-08-24 — PROMOTED: the whiteout/abort guards. `modules/story/early_game.py`. USER-APPROVED.

**What moved.** One file, `modules/story/early_game.py`, carrying three sandbox rounds:
* `#24-loopheadabort` — **17** loop-head `_check_abort()` calls, so a nav retry loop aborts at the
  LOOP HEAD instead of grinding out its full retry budget after a whiteout.
* `#24-abortrecoveryresiduals` **(b)** — the 5 handlers that fix newly exposed.
* `#24-abortrecoveryresiduals` **(c)** — the **8** handlers (7 functions) that predate all of it.

**WHY IT MATTERS HERE.** `StoryAbort` is a `BotModeError`, so a broad `except BotModeError:` absorbs
a whiteout unwind and the bot keeps playing in a state it should have abandoned. Before this,
**custom — the fork that actually ships — swallowed the unwind in all eight handlers.**

✅ **VERIFIED BY THE THREE-POINT A/B THIS PROJECT REQUIRES, NOT A BYTE-COMPARE.** A byte-compare only
proves a file was COPIED; these prove the FORK'S BEHAVIOUR moved:

| measurement | custom BEFORE | custom AFTER |
|---|---|---|
| AST abort-swallowers (reaches `_check_abort`, neither re-raises nor guards) | **8 sites / 7 functions** | **0 / 0** |
| `probe_abort_swallowing.py --build custom` | **36** | **23** |
| guarded handlers / loop-head `_check_abort` | 9 / 67 | **22 / 84** |

✅ **AND A BEHAVIOURAL ARM RUN AGAINST CUSTOM ITSELF** — the module imported explicitly from
`custom-pokebot/`, not sandbox: latch **CLEAR → exception SWALLOWED, old body runs** (ordinary
failures behave exactly as before); latch **SET → RE-RAISED** (the unwind escapes).
✅ Build-aware gates against custom: `repro_undefined_names`, `repro_no_silent_except`,
`repro_roster_reorder` (all `--build custom`), plus `repro_box_counter_move_test` and
`repro_pid_identity_key` — all exit 0.

‼ **THE RATCHET WAS TURNED IN THE SAME COMMIT.** `probe_abort_swallowing.py`'s custom baseline
**36 → 23**; otherwise the gain is unlocked and the ratchet goes slack. The forks are EQUAL again and
both now read ZERO AST swallowers. ⛔ **Attribution is EARNED, not assumed:** the BEFORE half was
captured and pushed in its own commit (`8872d71e`) minutes before the copy, with nothing else
changing — `promote.py` refuses a dirty tree precisely so the diff is the promotion and nothing else.

🔖 **Rollback point:** tag `pre-promote-2026-08-24-abortguards` (pushed).
📁 **Transcripts, both committed:**
`tools/story-dev/evidence/2026-08-24-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt`.

⛔ **WHAT THIS DOES *NOT* MEAN.** It does not make a second whiteout *during recovery* survivable —
that is `#24-abortrecoveryresiduals` (a), which was CLOSED BY ASSESSMENT (reachability VERY LOW; the
recovery window is spent on maps whose land encounter rate is 0 and `on_whiteout()` cannot fire twice
on Emerald) and deliberately NOT patched. See `06-DECISIONS-LOG.md` for that ruling and its re-open
triggers. It also does not change what the bot does when no whiteout is pending: the guard is
latch-keyed, and the CLEAR arm above is the proof.


## 2026-09-06 — PROMOTED: §Ch19 → §Ch23, FOURTEEN FILES, USER-APPROVED. Drift back to ZERO.

**The largest promotion so far.** Six NEW story modules and eight modified files move the fork's built
content from *Magma Hideout / Groudon* all the way to **the Pokémon League door with a stocked bag**.

**What moved (14 files, `promote.py` reports `byte-identical 14/14`, `drift after: 0`, `orphaned: 0`):**
```
NEW      modules/story/victory_road.py        3222 lines   §Ch23, eleven legs
NEW      modules/story/sootopolis.py          3555 lines   §Ch21
NEW      modules/story/pokemon_league.py      1439 lines   §Ch24 prep (out-of-battle healing)
NEW      modules/story/seafloor_cavern.py     1028 lines   §Ch19
NEW      modules/story/sootopolis_gym.py      1000 lines   §Ch22, gym 8
NEW      modules/story/overworld_items.py      245 lines   item-ball collection
CHANGED  plugins/custom_modes/story_mode.py   the segment dispatch through Segment 23
CHANGED  modules/story/chapters.py            the chapter table
CHANGED  modules/story/mossdeep_gym.py · modules/battle_action_selection.py
CHANGED  modules/battle_strategies/level_up.py · modules/modes/util/walking.py
CHANGED  modules/story/early_game.py · modules/map_data.py
```

**⭐ VERIFIED BY DRIVING, WHICH IS THE ONLY EVIDENCE THAT COUNTS — A COPY IS NOT.**
```
BEFORE (custom, pre-promotion):
    ModuleNotFoundError: No module named 'modules.story.victory_road'
    ⇒ custom could not run §Ch23 AT ALL.

AFTER  (custom, --build custom --driver ch23chapter post_wally.ss1 --frames 600000):
    AFTER at=((0,8),(18,6)) done=True on_ever_grande=True inside_victory_road=False
    CONTINUE neighbours_reachable=4
    RESULT battles=16 whiteouts=0 failure=None
    ACCEPTANCE: PASS
```
‼ `done=True` is a WORK-PRODUCT assertion, not a position check: `ch23_chapter_done()` passes only if
the bag holds every `LEAGUE_BASKET` line at quantity ⇒ **the Elite Four basket is provably in the bag.**
The BEFORE half was captured and pushed in its own commit (`da3c821b`) before anything moved, so
attribution is earned rather than assumed.

**✅ BUILD-AWARE GATES, ALL RUN WITH `--build custom`, ALL EXIT 0 (14):**
`repro_undefined_names`, `repro_no_silent_except`, `repro_roster_reorder`, `repro_box_counter_move_test`,
`repro_pid_identity_key`, `probe_abort_swallowing`, `probe_chapter_order`, `probe_ch14_recon`,
`probe_counter_grass`, `probe_pc_tile`, `repro_heal_piggyback_reporting`, `repro_hm_move_replace_loop`,
`repro_hm_replace_valve_forced`, `repro_ki65_unbound_party_index`.
⭐ `probe_abort_swallowing --build custom` reads **23 sites, exactly at baseline** ⇒ **this promotion
added NO new abort-swallowing debt to the fork.**

🔖 **Rollback point:** tag `pre-promote-2026-09-06-ch19-ch23` (pushed before the copy).
📁 **Transcripts (COMMITTED):** `tools/story-dev/evidence/2026-09-06-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt` — each carries the actual verdict lines. ⛔ The raw `.log` files are GITIGNORED (`tools/story-dev/.gitignore:2`) and do NOT travel; the first version of these transcripts was a `tee` of stdout that captured shutdown noise while the verdict went to the log, so they were CITED-BUT-EMPTY until rebuilt. ‼ Read an evidence file before citing it.

**⭐ ONE PRE-FLIGHT CHECK WORTH REPEATING.** Before copying, every file was grepped for sandbox-only
coupling. All hits were comments citing evidence paths — except `sootopolis.py:2197`, which is LIVE
code writing into `tools/story-dev/saves/`. It is safe: the function returns immediately unless an
env var names a capture (`if not name: return`), and `parents[3]` resolves to the repo root from
either fork. ⇒ **verify the one live hit rather than trusting that "they're all comments".**

**⛔ WHAT THIS DOES *NOT* MEAN.**
* **§Ch24 (the Elite Four) is NOT built.** Built content ends at the League door; `story_mode.py:3838`
  hands to manual there. §Ch24 must set its OWN progress marker, because `ch23_chapter_done()` requires
  the basket and will re-enter §Ch23 once the gauntlet spends it.
* **The Elite Four LEVEL GAP is open and slightly WORSE.** §Ch23 leg 9 now routes around two
  Cooltrainers to avoid a whiteout, forfeiting their EXP (and their ₽4,128, which leg 11 now covers by
  selling the Nugget).
* **`calculate_path` is still blind to trainer sight cones** — it consults only `on_enter_event_triggers`
  while spotting is a per-frame scan in `trainer_see.c`. §Ch23 works around it at one location; the
  general defect is untouched and will recur wherever a route grazes a cone.
* **`KI-91`** (a 1,200-frame self-recovering stall in leg 11) is filed, not diagnosed.

---

## 2026-09-07 — PROMOTED: `KI-95` (faint chooser) + `KI-93` (the Torment livelock), user-authorised

**Two files, both battle-path:** `plugins/custom_modes/story_mode.py` (`KI-95`) and
`modules/battle_action_selection.py` (`KI-93`, plus the env-gated `KI-96` census). Drift measured 2
before, **0 after, byte-identical 2/2, orphaned 0** in both directions.

**⭐ VERIFIED BY DRIVING, NOT BY COPYING** — `promote.py`'s own rule is *"a copy is not evidence"*:
```
--driver ch24probe --build custom --frames 200000   (post_league_shop.ss1)
  battle sub-handler KI-47 stops : 0        (was 3-6)
  SelectingTormentedMove         : 0
  outcome                        : BattleOutcome.Won   ⭐ the bot BEATS SIDNEY on the fork

grade_ki93_drive.py <custom debug-log> <harness log>   -> real exit 0
  C0 CONTROL   PASS  [KI93-CTL] fired 32x
  C1 LIVELOCK  PASS  KI-47 battle sub-handler stops = 0
  C2 JUSTIFIED PASS  0 REPICK(s) with no refusal behind them
  C3 ENGAGED   PASS  DISMISS=8 REPICK=12 — both halves live
```
📁 Transcript COMMITTED: `tools/story-dev/evidence/2026-09-07-PROMOTION-VERIFY-custom.txt`.
✅ Build-aware gates re-run against the fork: `repro_box_counter_move_test`, `repro_pid_identity_key`,
`probe_chapter_order` — all `--build custom` exit 0.
🔖 **Rollback point:** tag `pre-promote-2026-09-07` (created AND pushed before the copy — `promote.py`
refused until it existed, which is the guard working).

**‼ A TRAP THAT COST ME A GRADING PASS, WRITTEN DOWN SO IT DOES NOT REPEAT.** `--build custom` writes
its debug log under **`custom-pokebot/profiles/…/debug-logs/`**, not the sandbox's. I graded the
sandbox's newest log first and got `C0 CONTROL RED — the census never ran`, which looked like the
promotion had failed. ⇒ **when verifying a promotion, read the log the PROMOTED build wrote.**

**⛔ WHAT THIS DOES *NOT* MEAN.**
* **`KI-96` IS IN THIS FORK TOO, AND IT IS OPEN.** `modules/battle_action_selection.py:590-592` is an
  unbounded `while PARTY_MENU: press A`; it wedges the §Ch23 chain when a poisoned lead triggers a
  switch. Narrowed by three census drives (the aim, the mapping, the target's legality and the
  menu-opening are all RULED OUT) but **not fixed**.
* **The Sidney win is a ONE-SURVIVOR win** — 5 of 6 fainted, only Wailord standing, on the
  under-prepared `post_league_shop` party. Fights 2-5 are UNDRIVEN.
* **§Ch24 is still not built**, and the L60 party (`post_grind_L60.ss1`) has not reached the League
  because `KI-96` stops the chain first.

---

## 2026-09-07 (arc 2) — `KI-97`, `#24-mossdeepstrand`, `#24-countermsg` and `KI-96`'s BOUND promoted

**USER-AUTHORISED** ("promote to custom"). ⛔ The 8-lane batch was **STOPPED FIRST** — promoting under
a running measurement would make its lanes span two codebases, which is the rule
`08-MISTAKES.md` records from this same day. Then the deferred acceptance drives ran, and only then
the copy.

**PROMOTED (4 files, byte-identical 4/4, drift 0 both directions):**
* `plugins/custom_modes/story_mode.py` — `KI-97`'s Segment-13a `BADGE06_GET` gate,
  `#24-mossdeepstrand`'s Segment-18 un-strand, `#24-countermsg`'s by-species dedupe
* `modules/story/mossdeep_gym.py` — the chapter's badge early-return now leaves the gym first
* `modules/battle_action_selection.py` — `KI-96`'s 240-press bound + `request_mode_recovery`
  routing + observe-only `[KI96-REREAD]` telemetry
* `modules/story/counter_plan.py` — `answer_via` rendered in `summarise_candidates`

**✅ VERIFIED BY DRIVING AGAINST `--build custom`, not by a diff:**
```
story_harness.py saves/post_sootopolis_arrival.ss1 --driver storyresume --frames 25000 --build custom
  imported: custom-pokebot
  C1 "Could not reach (19, 6) on MapRSE.MAUVILLE_CITY"        : 0   (want 0)
  C2 "Fortree arc already complete (BADGE06) — Ch13a skipped." : 1   (want >=1, POSITIVE CONTROL)
  grade_ki97_drive.py on that log -> PASS (exit 0), C0/C1/C2/C3 all green
repro_box_counter_move_test.py --build custom -> exit 0
repro_pid_identity_key.py       --build custom -> exit 0
```
🔖 **Rollback point:** tag `pre-promote-2026-09-07-arc2` (created AND pushed before the copy —
`promote.py` refused until it existed).

**⛔⛔ WHAT THIS DOES *NOT* MEAN — read before building on it.**
* **`KI-96` IS STILL OPEN.** What is promoted is a BOUND (an unbounded `while PARTY_MENU: press A` is
  now a named, diagnosable stop after 241 presses — driven-proven) and OBSERVE-ONLY telemetry. **The
  CAUSE is not fixed.** ‼ And its round-3 root cause was **MEASURED FALSE** the same day:
  `[KI96-REREAD]` showed the battle-order array byte-identical before and after the party menu opens
  (`VERDICT=AGREE`) on a run that DID reproduce the wedge — so "recompute the menu slot after the menu
  opens" would change nothing. ⛔ **Do not re-propose it.** The live thread is that
  `get_game_state()` reports PARTY_MENU while the screen shows the ACTION-SELECT prompt.
  *(The older note in this file citing `battle_action_selection.py:590-592` has DRIFTED — cite the
  `TurnAction.RotateLead` symbol, not a line.)*
* **`KI-96`'s RECOVERY routing is UNPROVEN, not disproven.** `handles_battle_faults` appears ZERO
  times in `story_harness.py`, so `request_mode_recovery` returns False for every driver and the
  caller raises — a harness drive dropping to Manual is the CONTRACT, not a failure. See
  `#24-harness-faultgap`.
* **`#24-mossdeepstrand`'s RESCUE half is UNPROVEN.** Only its safe no-op is driven; the rescue needs
  a save on MOSSDEEP_CITY_GYM (23,8) with BADGE07 **set**, which no fixture has
  (`#24-mossdeep-strandfixture`).
* **§Ch24 is still not built**, and the batch's other blockers (`#24-tateliza-attrition`,
  `#24-ballrestock-ordering`, the L03 truck fast-fail loop) are open.

---

## 2026-09-07 (CORRECTION to the arc-2 entry above) — the "MEASURED FALSE" note was WRONG

⛔ The arc-2 entry says `KI-96`'s round-3 root cause was **MEASURED FALSE** and instructs *"do not
re-propose it"*. **That instruction is WITHDRAWN — it could suppress the correct answer.**

The probe it cited was VACUOUS: its two reads were taken five frames BEFORE the A press and 77 frames
before the party menu existed (`[KI96-STAGE] 1` on the same frame reports `state=BATTLE`).
`scroll_to_battle_action(2)` only moves the action cursor; `PlayerHandleChoosePokemon` — the only
thing that refills `gBattlePartyCurrentOrder` — cannot run until after the A press. ⇒ `VERDICT=AGREE`
compared a value with itself. **The stale-array theory is UNTESTED, not refuted.**

⛔ Also withdrawn from that entry: *"the live thread is that `get_game_state()` reports PARTY_MENU
while the screen shows the ACTION-SELECT prompt."* `get_game_state()` reads `gMain.callback2` with a
per-frame cache and is trustworthy; `bt=` and `instr=` are the stale fields. The menu is open and the
game is actively REFUSING the switch.

✅ **UNAFFECTED:** the promoted BOUND is still driven-proven, `KI-97` is still driven green, and the
promotion itself (drift 0, 4/4 byte-identical, verified against `--build custom`) stands. What changed
is a CLAIM ABOUT A CAUSE, not the behaviour of the promoted code.

---

## 2026-09-08 — PROMOTION: five files, user-authorised, VERIFIED BY DRIVING

`promote.py --restore-point pre-promote-2026-09-08 --go` — **5/5 byte-identical, drift 0 in both
directions, orphaned 0.** Restore point pushed to origin before anything was copied.

**WHAT MOVED, AND HOW WELL EACH IS PROVEN — stated per file, because they are NOT equal:**

| file | change | evidence |
|---|---|---|
| `modules/battle_action_selection.py` | `KI-96` — recompute the party-menu slot AFTER the menu opens | ✅ **driven A/B**: 241 presses + a hard stop to Manual → 27 presses + ACCEPTED, bound firings 1 → 0 |
| `modules/story/victory_road.py` | `#24-hm07teach` — `ensure_waterfall_learner()` | ✅ **driven at scale**: §Ch23 Waterfall preflight 11 of 53 → **0 of 49** |
| `modules/story/early_game.py` | `#24-hm07funnel` (`pick_land_hm_slot`) + `whiteout_budget()` | ✅ **driven at scale**: Surf+Dive party-full 7 → **0**; whiteout quota 14 (26.4%) → **4 (8.2%)** |
| `plugins/custom_modes/story_mode.py` | `KI-97` gate, Segment 22b, `#24-mossdeepstrand`, `#24-truckleak`, budget wiring | 🔶 **MIXED** — the gate and Segment 22b are driven; ⚠ `#24-truckleak` was never FAULT-ARMED |
| `modules/modes/util/higher_level_actions.py` | `#24-pcpingpong` — `withdraw_precedence()` | ⚠ **UNDRIVEN** — no targeted acceptance; it ran in the batch without a new failure class, which is evidence, not proof |

**THE VERIFICATION, AS THE STANDING RULE DEMANDS — a copy is not evidence:**
```
story_harness.py post_grind_L60.ss1 --driver ch23chapter --build custom
ACCEPTANCE: PASS   done=True   battles=12 whiteouts=0 failure=None
```
This is the SAME fixture and driver that passed on sandbox before the promotion, so it is a true
before/after **on the fork**, not a byte-compare.

**⭐ AND A SECOND, INDEPENDENT DISCRIMINATOR — a gate that was RED on custom is now GREEN.**
`probe_hm_coverage.py --build custom` passes. Its own docstring recorded that custom *"fails today
for a KNOWN correct reason (unpromoted fix)"*, so this is a measured state change on the fork rather
than a re-run of the same import. `probe_abort_swallowing.py --build custom` also passes.

**‼ HONEST ABOUT THE TWO WEAK ROWS.** `#24-pcpingpong` and `#24-truckleak` are promoted WITHOUT their
own fault-armed acceptance. They were exercised by **49 full story runs** in batch
`20260907-203713` — the batch ran this exact sandbox code (`code_commit 8a8ae2d9`, and the tree was
clean at launch, so the recorded commit is genuinely what ran) — and produced no new failure class
attributable to either. ⇒ **that is real evidence and it is NOT a targeted acceptance.** Their owed
drives (`#24-pcpingpong-accept`, `#24-truckleak-accept`, the latter needing `Up`+`B` held across a
run boundary) remain OWED, and are now owed against BOTH forks.
⛔ Rollback: `pre-promote-2026-09-08` (local + origin).


---

## 2026-09-10 — SIX FILES PROMOTED (user-authorised): the dex fence, the late-boss configs, the leg-4 League fix

**Authorised by the user 2026-09-10** ("promote, then do A/B"). Rollback: **`pre-promote-2026-09-10`**
(local + origin, created BEFORE the copy — `promote.py` REFUSED the first attempt because the tag did
not exist yet, which is the tool working).

**What moved (drift 6 → 0, 6/6 byte-identical):**
| file | what it carries |
|---|---|
| `plugins/custom_modes/story_mode.py` | `#24-dexhunt`'s catching fence (`decide_dex_catch`, PURE) + the first post-Winona loss adaptation (`tate_liza_fight`, `juan_fight`, grass-less) |
| `modules/story/victory_road.py` | §Ch23 leg 4 can no longer fire an OCEAN CROSSING from inside the League (`LEAGUE_INTERIOR_MAPS` + `inside_league()`) |
| `modules/story/training_areas.py` | the L28 ceiling PROOF + 6 staged `PENDING_GRASS` candidates — ⛔ **comment/data only, `tile=None`, behaviour-neutral** |
| `modules/debug_logger.py` | `balls=` on the heartbeat |
| `modules/story/counter_hunt.py`, `modules/story/early_game.py` | older sandbox work carried along |

### ⭐ VERIFIED BY DRIVING, NOT BY A DIFF — the standing rule
`post_vr_exit.ss1` (md5 asserted `0ad243164fd6` BEFORE the run) → `--driver ch23leagueprobe
--frames 2000 --build custom`:
**`ACCEPTANCE: PASS`**, `readings=['RL-BAG','RL-DANGER','RL-DOOR','RL-PARTY','RL-PATH','RL-TILES']`,
`missing=[]`, `failure=None`, League door path **37 wp** from the landing (18,28).
⭐ **THE DISCRIMINATOR THAT PROVES IT WAS THE CUSTOM FORK:** the run wrote its state to
`custom-pokebot\profiles
epro-ml\states\…` — a sandbox run cannot produce that path. A drive that
cannot name which fork it ran is not evidence of a promotion.
Evidence committed: `tools/story-dev/evidence/2026-09-10-promotion-ch23leagueprobe-custom.{log,stdout.txt}`.
Build-aware gates against custom: `repro_box_counter_move_test.py`, `repro_pid_identity_key.py`,
`probe_abort_swallowing.py` — all PASS.

### ‼ HONEST ABOUT WHAT IS *NOT* PROVEN
Every promoted change is gated for **CORRECTNESS** and none is proven to **HELP**:
* the dex fence has never run an A/B (that batch is next, and it is the reason for this promotion);
* the late-boss configs have never seen a live badge-7/8 loss;
* `training_areas.py` changes NO behaviour at all (verified: `best_training_grass` returns the same
  ground at every level — L5→ROUTE102, L13→ROUTE117, L20→ROUTE111, L28/35/40/47→ROUTE121).
⇒ **This promotion moves proven-correct code, not proven-useful code.** Both forks now carry the same
risk, which is exactly why the rollback tag exists.


---

## 2026-09-10 (later) — RE-PROMOTED: `story_mode.py` only, fixing a crash the earlier promotion shipped

⛔ **THE EARLIER PROMOTION THIS SAME DAY SHIPPED A CRASH TO THIS FORK.** Batch `20260910-203458`
(8 lanes, 180.1 min, VERDICT OK) crashed **11 runs at ~1.6M frames each**:
`UnboundLocalError: cannot access local variable 'PokemonCenter'`. The late-boss config dicts were
built at indent 8 — OUTSIDE their `if not _done("BADGEnn_GET")` guard — so they construct on every
pass through `_play`, and on a RESUMED run none of the twelve conditional `PokemonCenter` imports has
executed. `winona_fight`, the precedent, is at indent 12, inside its guard.

**Fixed and re-promoted** (drift 1 → 0, 1/1 byte-identical). Rollback: `pre-promote-2026-09-10b`.
Verified in THIS fork by AST rather than by a diff: both configs are inside an `if` guard, and each
guard imports `PokemonCenter`, `_lead_best_matchup` and `heal_in_pokemon_center`.

⭐⭐ **THE LESSON THIS FORK SHOULD CARRY: the first promotion's DRIVE PASSED.**
`--driver ch23leagueprobe --build custom` returned `ACCEPTANCE: PASS` — but it started from
`post_vr_exit.ss1`, a fixture whose badges are already earned, and it never re-entered `_play` from
the top. **A green drive proved the code LOADS, not that it SURVIVES A RESUME.**
⇒ **Do not promote code whose first real exercise is still ahead of it.** Promote AFTER the batch.
The rollback tag is why this cost a re-promotion instead of a bad day.


---

## 2026-09-11 — PROMOTION: three files, user-authorised — a latent CRASH FIX, shipped with the unproven part DORMANT

**Rollback tag: `pre-promote-2026-09-11b`** (local + origin, at `143b7d4f`).
Drift 3 → **0**, 3/3 byte-identical.

| file | what | kind |
|---|---|---|
| `modules/story/victory_road.py` | `yield` inside a `finally` → latent `RuntimeError` | ⛔ **CRASH FIX to code THIS FORK was already running** |
| `plugins/custom_modes/story_mode.py` | same crash fix, + `#24-maintain` **shipped DORMANT** | fix live, feature inert |
| `modules/story/training_areas.py` | Meteor Falls sealed-pocket evidence | comment-only (AST-identical) |

### Why this fork needed it
A generator that yields from a `finally` raises `RuntimeError: generator ignored GeneratorExit` when
closed while suspended in the matching `try`. CPython closes abandoned generators at GC time, and
**this fork has two live `.close()` sites that reach the affected code** — `_play_gen.close()` (fired
on any recoverable battle fault) and `inner.close()` (per-run frame budget). `train_team` can sit
suspended inside that `try` for ~100k frames, so the exposure was most of a training run.
‼ `victory_road.py` carried the bug under the comment *"⛔ IN A `finally` ON PURPOSE"* — the intent
was right, the mechanism was a crash. **A deliberate-looking comment is not evidence of safety.**

### ⭐⭐ HOW THIS PROMOTION ANSWERS THIS FORK'S OWN 2026-09-10 LESSON
That entry ends: *"A green drive proved the code LOADS, not that it SURVIVES A RESUME … **Do not
promote code whose first real exercise is still ahead of it.** Promote AFTER the batch."*
That lesson applies squarely to `#24-maintain`, whose ACTION has never executed a frame. It is
answered TWO ways rather than argued around:
1. **The feature ships INERT.** `POKEBOT_MAINTAIN` defaults OFF; unset ⇒ the method logs `dormant`
   and returns *before any yield*. Its first real exercise is therefore NOT in this fork. The crash
   fix — which is urgent and IS proven — did not have to wait for it.
2. **The drive re-entered `_play` FROM THE TOP**, which is exactly what the failed 2026-09-10
   verification did not do (it started from `post_vr_exit.ss1`, badges already earned).

### Verification — DRIVEN, not diffed
`story_harness.py mauville_prewattson.ss1 --driver story --build custom --frames 220000` → **exit 0**,
ledger row `"build": "custom"`, `frames_run: 220000`.
⭐ **The new code was REACHED, not merely loaded** — the debug log carries
`f1006807 [MAINTAIN] dormant (POKEBOT_MAINTAIN unset) — decision gated, action UNDRIVEN`, i.e. a real
`_prepare_for_fight` called it and it correctly did nothing.
**Crash scan: 0** matches for traceback / UnboundLocal / RuntimeError / "generator ignored".
⛔ **And the gate figure MOVED ACROSS THE COPY**, which a byte-compare can never show: the same gate
on the same file read **1 offender before** (`victory_road.py:2099`) and **0 after**. A copy proves a
file moved; this proves the FORK's own generators are free of the shape.
Build-aware gates against custom: `repro_box_counter_move_test` ✓ `repro_pid_identity_key` ✓
`probe_abort_swallowing` ✓ (23 sites, at baseline) `probe_yield_in_finally` ✓ (31 files, 0 offenders).
Evidence: `tools/story-dev/evidence/2026-09-11-PROMOTION-VERIFY-custom.txt`.

### What this fork now carries that is NOT proven
⛔ **`#24-maintain`'s ACTION.** Gate #55 proves the DECISION (13 cases, 3 fault arms); rotate → train
→ restore-lead has never run. It is dormant, so that is a statement about latent code, not about
behaviour. ⇒ **Do not flip `POKEBOT_MAINTAIN` on in this fork until the sandbox drive passes**, and
flip it in its own reviewable change — never as a side effect of something else.


---

## 2026-09-12 — PROMOTED: the `#24-maintain` top-up, ENABLED, plus the three fixes that made it safe

**USER-AUTHORISED** (the user chose "promote all four files" after being shown the safety result).
Restore point **`pre-promote-2026-09-12`** — created AND pushed to origin before anything moved.
Sandbox HEAD at promotion: `be3c283e`. Four files, promoted TOGETHER:

    modules/modes/util/higher_level_actions.py
    modules/story/early_game.py
    modules/story/training_areas.py
    plugins/custom_modes/story_mode.py

⛔ **WHY "TOGETHER" IS NOT A STYLE PREFERENCE.** `story_mode.py` alone would ship the fail-soft
handler with no `allow` predicate to feed it; and with the flag now defaulting ON, shipping it
without the fixes is precisely the combination that killed **406 runs** on 2026-09-12 morning.

### What this fork now DOES that it did not before
1. **The top-up runs by DEFAULT** — `POKEBOT_MAINTAIN` defaults `"1"` (was `"0"`). USER RULING; it
   overruled my recommendation. `06-DECISIONS-LOG.md` 2026-09-12 (user ruling) carries the
   DO-NOT-REOPEN and the measurements it was made against.
2. **The training-ground picker refuses grounds it cannot walk to** (`best_training_grass(..., allow=)`),
   and the errand ABANDONS instead of killing the run when it finds one anyway.
3. **The heal walk fails FAST and HONESTLY** — it rides out only genuine scripted events. Measured:
   63 real interruptions (all cleared on attempt 1) vs **128 deterministic reachability refusals**
   that were being retried 8× and reported as "a scripted event kept interrupting" — false every time.
4. **The lead rotation is guarded for slot 0.** Rotating TO slot 0 is a destructive SWAP
   (`range(slot-1)` = `range(-1)`), and slot 0 wins ties in `decide_maintenance`. Five other call
   sites already guarded it; this one did not. Caught by adversarial review BEFORE shipping.

### Verification — DRIVEN, not diffed
`story_harness.py mauville_prewattson.ss1 --driver maintain --build custom --inject-hmmule
--frames 400000` → **`ACCEPTANCE: PASS`**, exit 0.
```
[maintain] RESULT arm=ON started=True dormant=False rotation_landed=True
           level_start=13 level_end=14 catchup=14 reached=True
           p6_lead_is_strongest=True failure=None
```
⭐ **Every word of that line is load-bearing.** `arm=ON` **with no env var set** proves the new
default took effect IN THIS FORK. `dormant=False` proves the code was REACHED, not merely copied —
the previous promotion could only show `[MAINTAIN] dormant`. `level_start=13 level_end=14` proves it
actually TRAINED. `p6_lead_is_strongest=True` proves the lead was restored afterwards.
Crash scan: **0** (traceback / UnboundLocal / RuntimeError / "generator ignored").
Build-aware gates against custom: `probe_abort_swallowing` ✓ (23 sites, **exactly at baseline** —
the new handlers added no swallow debt), `probe_yield_in_finally` ✓ (31 files, 0 offenders),
`repro_pid_identity_key` ✓, `repro_box_counter_move_test` ✓.
Evidence: **`tools/story-dev/evidence/2026-09-12-promotion-maintain-custom.stdout.txt`** — the ACCEPTANCE line is IN that committed file (verified by grepping it, not by remembering it). ⚠ The paired `.log` is **NOT in the repo**: `tools/story-dev/.gitignore:2` ignores `*.log`, so no evidence `.log` has ever been tracked (0 tracked, vs 97 tracked `.stdout.txt`). ⇒ when a claim must survive in the repo, it has to rest on the STDOUT capture.

✅ **THE PREVIOUS ENTRY'S STANDING INSTRUCTION IS NOW SATISFIED AND CLOSED.** It read: *"Do not flip
`POKEBOT_MAINTAIN` on in this fork until the sandbox drive passes, and flip it in its own reviewable
change."* The sandbox drive passed, two A/Bs ran, the flip was its own reviewable change, and the
user ruled. ⇒ that sentence is HISTORY, not a live prohibition.

### ⛔ What this fork carries that is STILL NOT PROVEN — read this before trusting it
1. **The HEAL fail-soft handler has NEVER EXECUTED.** Across 102 ARM-ON runs, all 83
   `MAINTAIN ABANDONED` lines were the GROUND handler; `ABANDONED … heal walk` = **0**. Gate #57
   F1-F8 proves its SHAPE; production has never taken the path. ⇒ **a gated shape is not a driven
   path.** 18 of the 19 heal derails fire OUTSIDE the errand, where this fix does not reach.
2. **The slot-0 guard is UNDRIVEN.** The verification drive injected a mule at a non-zero slot, so
   the guard was never the branch taken. It is gated (#57 H1) and reasoned from the menu driver's
   own arithmetic — not observed.
3. **NO BENEFIT HAS BEEN MEASURED.** Two A/Bs: badges/run 2.055 vs 2.030, then **1.922 vs 2.067**.
   The feature is on because the USER RULED, not because it measured better. ⛔ Do not re-open that;
   do not claim otherwise either.

---

## 2026-09-13 — PROMOTED: the bot no longer answers "NO" to Wally (`#24-wallydecline`)

**USER-AUTHORISED** (asked explicitly; the answer was "promote now, then batch"). Restore point:
`git tag pre-wallypromote-20260913` → `4e164cbe`.

**ONE FILE PROMOTED — `modules/story/early_game.py`.** ⛔ NOT via `promote.py`, deliberately: that
tool has no per-file filter and would ALSO have shipped `higher_level_actions.py` (the heal fault
hook) and two comment-only files, none of which the user was asked about. Copied by hand, then
MD5-verified identical to sandbox. Drift 4 → 3.

### What it fixes
`fight_wally_mauville` mashed `"B" if frames % 3 else "A"` into Wally's `MSGBOX_YESNO`, and at a
Gen-3 yes/no **B IS "NO"** (`src/script_menu.c Task_HandleYesNoInput`: `case MENU_B_PRESSED:` falls
through to `gSpecialVar_Result = 0`). Declining sets `FLAG_DECLINED_WALLY_BATTLE_MAUVILLE`, which
**nothing in the decomp ever clears**, re-prompts forever, and leaves Wally standing on **(8,6) —
the sole tile the gym door (8,5) opens from**. ⇒ **124 of 143 ENDED runs died there** (= **60% of
the 207 STARTED**; the 87%-of-ENDED figure is length-biased). `finished` has been **0** in every
batch since 2026-08-26.

### The change is ADDITIVE and its default path is byte-identical
`import os`, `_int_env`, `_yes_no_menu_is_open`, `_dialogue_button` delegating to that one predicate
(same symbols, same fail-to-"B" direction), `frames = _int_env("POKEBOT_WALLY_PHASE", 0)` (unset ⇒ 0
⇒ unchanged), and the guard itself. A `diff` of the two forks shows **no removed lines** other than
the `_dialogue_button` body it now delegates.

### ⭐ VERIFIED BY DRIVING `--build custom`, BOTH DIRECTIONS
| arm | measured on the PROMOTED fork |
|---|---|
| `prod` | `ACCEPTANCE: PASS` — `reached_prompt=True declined_ever=False defeated_now=True frames=2078` (identical to sandbox) |
| `POKEBOT_WALLY_FAULT=decline` | **WEDGES** — `HANG CONFIRMED (20000 frames no progress)`, frozen on `MauvilleCity_EventScript_DeclineWallyBattle` + `WallyRequestBattleAgain` |
‼ The fault arm was run **on custom too, on purpose**: a PASS only means something if the arm that
must fail still reaches production in THIS fork. A gated shape is not a driven path — the previous
entry's own standing warning.
Evidence (committed): `tools/story-dev/evidence/wallycustom-{prod,decline}.driver.txt|.stdout.txt`.

### ⛔ What this fork carries that is STILL NOT PROVEN — read before trusting it
1. **The fix is proven CORRECT, not BENEFICIAL.** No batch has yet measured the gain. The
   adversarial review's point stands and is not rhetorical: `finished=0` across all 207 runs, and
   runs that get PAST Wally average **32.8 whiteouts** against 3.6 for those that die at him. This
   unblocks ~60% of runs to Gym 3; it will **not** produce a completion, and the freed runs will die
   somewhere downstream. A batch follows this promotion — read its terminal-map distribution, not
   just its pass rate.
2. **Only the Wally site is fixed.** 14 other blind mashers remain in this file. An audit found no
   reachable choice box at the ones it checked, but `KI-98` (a possible second site) is
   **AGENT-REPORTED AND UNVERIFIED**, and my own read of that function's docstring did not support
   it. ⛔ Do NOT blanket-apply the guard: forcing YES at a shop or item prompt spends money or wastes
   an item — a NEW bug traded for a fixed one.
3. **`KI-99` is open and unverified**: the HM06 gift may lack a bag-full guard, in which case our
   success predicate (a flag) would read TRUE while the HM never entered the bag.


---

## 2026-09-14 — `#24-e4healing` STEP 3: in-battle STATUS CURES (user-authorised promotion)

**What custom now carries that upstream does not.** `modules/story/battle_items.py` gains
`choose_status_or_revive_item()` — a policy that cures **Sleep and Freeze only** (the two statuses
that cost a turn) — and `plugins/custom_modes/story_mode.py` calls it from
`StoryItemBattleStrategy._maybe_use_item` **after** the HP policy declines, so an HP emergency always
outranks a status cure. `modules/modes/util/higher_level_actions.py` gains the
`POKEBOT_HEALWALK_FAULT` synthetic-fault helper (a test hook, default off).

**⭐ VERIFIED BY DRIVING `--build custom`, not by copying.** The project rule is that a real
behaviour promotion must be driven, and it was:

    --driver ch24probe  POKEBOT_CH24_STAGE_FREEZE=1  --build custom
    DECISION#1  status=Freeze  hp=147/147  item='Full Heal'  param=0  target=0  heal_frac=0.35
    STEP3 ACCEPTANCE: PASS (arm=LIVE; expected_cure=True observed_cure=True)
    outcome=BattleOutcome.Won   elite4_state=1   ACCEPTANCE: PASS

The HP path was observed EXECUTING in the same run (`hp=29/147 → Full Restore → hp=147/147`, and
`15/147 → 110/147`), with `ineffective=False` throughout — the no-op guard never tripped.
Evidence: `tools/story-dev/evidence/2026-09-14-ch24probe-STEP3-CUSTOMBUILD-VERIFY.stdout.txt`.

**⛔ WHAT THIS MUST NOT BE QUOTED AS.** It is proof the feature FIRES in the custom build, on one
drive, against SIDNEY. It is **not** a finish-rate or win-rate claim, and no batch has measured one.

**⛔ KNOWN LIMITS THAT SHIPPED WITH IT.**
* **REVIVE IS OFF** — `allow_revive=False` at the call site, pending `KI-100`: a cure targets the
  ACTIVE battler, a revive targets a fainted NON-active member, which is the index space behind
  KI-18/34/66.
* **Poison / Burn / Paralysis are deliberately NOT cured** — they do not cost a turn, so curing them
  trades a guaranteed attack for nothing.
* `POKEBOT_E4_FAULT_NOCURE` (fault arm) and `POKEBOT_HEAL_AT_FRACTION` (A/B knob) ship with it, both
  default-off/unset. ⚠ `HEAL_AT_FRACTION` stays **0.35**: raising it was MEASURED HARMFUL on
  2026-09-14 (the raised arm tripped the item-execution no-op guard and lost).

**Line endings:** `higher_level_actions.py` was promoted **preserving custom's CRLF**, so git shows
the 91 real added lines rather than a 1,173-line encoding flip. ⇒ `promote.py --check` will keep
reporting **1 differing file** for that reason alone — an ENCODING-ONLY residual, content identical.


---

### 2026-09-15 — the ENCODING-ONLY residual is no longer counted as drift (no file moved)

The 2026-09-14 note above records `promote.py --check` *"reporting **1 differing file** for that
reason alone — an ENCODING-ONLY residual, content identical."* That is now measured and settled:
`git rev-parse` returns the SAME blob `08b92af1…` for both forks' copies of
`modules/modes/util/higher_level_actions.py`, i.e. git itself sees no difference at all.

`promote.py` now hashes newline-normalised content and prints such files on their own line
(`line-ending-only (NOT drift, no behaviour difference)`), so the live reading is
**drift 0, orphaned 0, line-ending-only 1**.

⛔ **NOTHING WAS COPIED BETWEEN THE FORKS TO ACHIEVE THIS, and custom's CRLF is deliberately kept** —
flipping it would replace a 91-line reviewable diff with a 1,173-line ending flip. Gate #62
(`selftest_promote_drift.py`) fault-tests the change in both directions. Full rationale:
`PROJECT KNOWLEDGE/06-DECISIONS-LOG.md` 2026-09-15.


---

### 2026-09-16 — PROMOTED: the `KI-101` fix (in-battle items aimed at a STALE party order)

**Two files:** `modules/battle_action_selection.py`, `plugins/custom_modes/story_mode.py`.
**Rollback tag:** `pre-promote-2026-09-16` (local + origin, created BEFORE the copy).
**Authorisation:** the user's, after the decision was put to them explicitly and they answered
"promote if needed".

**WHAT IT FIXES.** Opening the in-battle bag makes the game refill `gBattlePartyCurrentOrder`
(`src/battle_controller_player.c:2653-2663`, `PlayerHandleChooseItem`) and permutes the party into
battle order. We computed the item target BEFORE that, so heals aimed at whatever happened to sit in
the stale slot — in the measured case, two Full Restores onto FAINTED Pokémon, after which the
strategy disabled items for the rest of a Sidney fight. It is `KI-96` on the sibling handler; the
switch path was fixed 2026-09-07 and the item path never was.

**THE CHANGE.** The DRIVER now waits (bounded 120 frames, falling back) for `GameState.PARTY_MENU`,
re-reads `get_battle_state()` and scrolls to the MAPPED slot; the STRATEGY passes intent
(`mon.party_index`) rather than a pre-resolved slot; and the no-op verdict asks **CONSUMPTION**
(did the bag count drop — `RemoveBagItem` sits only in the success branch) instead of an HP delta.

**EVIDENCE (sandbox A/B, same fixture and driver, `ACCEPTANCE: PASS` in every arm):**
  * ARM-OFF: 5 of 6 fainted, `"no effect ... disabling items"`.
  * ARM-ON : 2 of 6 fainted, `party-menu target=4 -> menu slot 0 (pre-menu value was 1)`.
  * re-drive with the consumption verdict: all three uses `✔ CONSUMED (bag count dropped)`.
  ⭐ `pre-menu value was 1` is the wrong slot the old code used, printed beside the corrected `0` —
  the log carries its own counterfactual.

**PROOF IT REACHED THIS FORK, not merely that a copy ran:** `promote.py --go` reported drift 0 both
ways and `byte-identical 2/2`; `git hash-object` independently makes both files IDENTICAL blobs
across the forks; the `KI-101` markers and the `CONSUMED (bag count dropped)` verdict are present in
`custom-pokebot/`; and the fix was VERIFIED BY DRIVING `--driver ch24probe --build custom`
(evidence `tools/story-dev/evidence/2026-09-16-ch24probe-KI101-CUSTOMBUILD-VERIFY.stdout.txt`).
‼ That last step is the one that matters: on 2026-08-14 a hand-run promotion shipped with a hole
because the gate proving the fix hard-coded the sandbox import path, so nothing checked the other
fork. A copy is not evidence.

## 2026-09-16 (later) — PROMOTED: two heal-path TEXT fixes (`pokemon_league.py`, `victory_road.py`)

**User-authorised.** Rollback tag **`pre-promote-2026-09-16b`** (local + origin, verified by
`promote.py` before it copied). `promote.py --go`: drift after **0**, orphaned **0**,
**byte-identical 2/2**.

**WHAT CHANGED — both are TEXT ONLY, no control flow:**
1. `modules/story/pokemon_league.py` — `ONE_USE_BUDGET`'s comment claimed *"Frames to spend on one
   item use"*. The loop it bounds does `wait_for_n_frames(4)` per iteration, so 900 iterations is
   **~3,600 frames**, against a MEASURED whole-seven-action heal of **2,949**. The comment was wrong
   by 4× and described a bound ~8.5× the operation it caps. ⭐ **The VALUE is deliberately unchanged**
   — lowering it is a behaviour change to the gauntlet's only healing path and no per-call cost has
   ever been measured. What shipped is the correction to the LIE.
   *(The same commit also added a module-level `_check_abort` import and an in-place note explaining
   why the obvious `ITEM_CONTEXT_TASKS` fix must not be retried — see `#24-itemcontextplural`.)*
2. `modules/story/victory_road.py` — `_budgeted`'s raise hard-coded `"Ch23: …"`. It is a SHARED
   helper and `pokemon_league.py` (§Ch24) already wraps a call in it, so a §Ch24 budget overrun
   reported itself as a §Ch23 failure. It now uses the caller's own `label`.

**VERIFIED BY DRIVING, not by the copy** (the tool's own standing rule):
`--driver ch24heal post_league_shop.ss1 --build custom` → `build=custom`, `heal_actions=7`,
`GRADE premise_ok=True ready=True revive_ok=True control_ok=True back_in_overworld=True whiteouts=0
failure=None`, **`ACCEPTANCE: PASS`**. Evidence:
`tools/story-dev/evidence/2026-09-16-ch24heal-CUSTOMBUILD-VERIFY.stdout.txt`.
Build-aware gates against the fork: `repro_pid_identity_key.py` and `repro_box_counter_move_test.py`
both print *"(importing from … custom-pokebot — verified)"* and `ALL CHECKS PASS`, exit 0.

‼ **AND A THIRD CHANGE WAS DELIBERATELY *NOT* PROMOTED, BECAUSE IT WAS MEASURED AS A REGRESSION.**
Replacing the healing path's singular `ITEM_CONTEXT_TASK` wait with the teach path's accept-any-task
loop took `ch24heal` from **PASS (7 actions)** to **FAIL (0 actions, nothing healed)** — the teach
loop is START-only, while `wait_for_task_to_start_and_finish` presses A *through* the menu to select
"Use". Reverted before promotion; filed as `#24-itemcontextplural` with the A/B.
