# Automation, Backups & Sync (custom fork)

Promoted from the sandbox round on 2026-07-19. All additive — built on the
bot's own plugin/mode framework and memory tools; no upstream files edited
beyond the shared `dashboard_gui.py` / `pokebot.py` / `patrol.py`.

## Backup & restore (`modules/backup_manager.py`, `plugins/backup_plugin.py`, `backup.yml`)
- Zips a profile's saves, savestates, `stats.db` and configs to
  `backups/<profile>/` with retention pruning. Triggers: GUI "Back up now",
  every shiny, and a timed interval. Restore (GUI "Restore…") always
  creates a NEW profile — a loaded profile is never overwritten.
- Cloud backends (opt-in in `backup.yml`): **github** commits backups to
  this repo under `cloud-backups/<profile>/` (your repo IS the cloud;
  restore elsewhere with `git pull`); **synced_folder** mirrors to any
  OneDrive/Dropbox/Drive folder.

## Cloud save-sync v2 (`modules/cloud_sync.py`)
- Opt-in (`backup.yml` `sync:` block, default OFF). Launch applies a newer
  cloud save ONLY before the emulator loads and ONLY if the local save has
  not diverged; on divergence local always wins and the cloud version can
  be imported as a new profile. Exit pushes after the save flush. Desktop
  <-> handheld continuity without manual file copying.

## Macros (`modules/macros.py`, `plugins/macro_plugin.py`, `plugins/custom_modes/macro_player.py`)
- Record button presses in Manual mode (GUI Macros card) -> human-editable
  YAML in `profiles/<name>/macros/`. Replay via the "Macro (Custom)" mode,
  once or looped. Turns any hand-played routine into one-click automation.

## Patrol + global navigation (`plugins/custom_modes/patrol.py`, `modules/modes/util/global_navigation.py`, `modules/warp_graph.py`)
- "Patrol (Custom)" walks a `patrol.yml` waypoint loop. Waypoints may be
  anywhere in the world: routes are planned across warps (doors/stairs/cave
  entrances) via a ROM-extracted warp graph cached in `cache/`. Old
  `- [x, y]` (current-map) format still supported.

## Shiny alerts & update notice
- `plugins/shiny_alert_plugin.py` + `alerts.yml`: desktop toast + sound on
  shiny (works when hidden/fullscreen), optional auto-pause.
- `modules/update_check.py`: a launch-time background check shows an
  "updates available — run install.py" banner when the repo has moved.

## Game cheats
See `03-cheats.md`.
