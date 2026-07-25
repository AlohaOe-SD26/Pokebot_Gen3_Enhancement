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
