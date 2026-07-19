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
