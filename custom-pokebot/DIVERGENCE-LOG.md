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
