# Sandbox Notes — changes vs custom-pokebot
> APPEND-ONLY. Every sandbox-vs-custom difference gets an entry here (this
> is the promotion checklist when the user approves a feature).

---

## 2026-07-18 — A1: Backup & Restore system
- **Added** `modules/backup_manager.py`: BackupManager — zips a profile's
  valuable data (saves, savestates, stats.db, configs; screenshots/logs
  excluded) to `backups/<profile>/<timestamp>_<reason>.zip` with retention
  pruning (default 10). Cloud backends (opt-in via `backup.yml`):
  `github` (copies newest zip to repo-root `cloud-backups/<profile>/`,
  prunes to 3, stages ONLY that path, commits + pushes — all failures
  non-fatal) and `synced_folder` (mirrors to any OneDrive/Dropbox/GDrive
  dir with its own retention). `restore_backup()` extracts into a NEW
  profile only (live profiles are never overwritten; zip-slip guarded;
  half-restores cleaned up). Hybrid logging to `logs/backup.log`.
- **Added** `plugins/backup_plugin.py`: auto-backup on every logged shiny
  (`auto_on_shiny`) + a frame listener doing timed backups every
  `interval_hours` (checks once per ~3600 frames; cheap).
- **Added** `backup.yml` (root, tracked): commented config template;
  per-profile `profiles/<name>/backup.yml` overrides it whole-file.
- **Modified** `modules/gui/dashboard_gui.py`: "BACKUPS" card in the tool
  column (last-backup age label refreshed with the KPI cycle, "Back up
  now", "Restore…" Toplevel that lists local+cloud backups and restores
  into a new profile name); backup events surface in the event log.
- **Modified** `.gitignore`: negation for the plugin (ML-2), `backups/`
  ignored (user data). Repo-root `cloud-backups/` is deliberately tracked.
- **Verified**: 12-check headless battery (archive contents, retention,
  hash-identical restore, refusal paths, malformed/override configs,
  synced-folder backend, disabled mode) all PASS; real GitHub cloud backup
  committed+pushed containing only `cloud-backups/…` (commit `38a0e207`,
  left in the repo as a demo); live GUI run screenshot-confirmed the card.
- **Not verified**: shiny-triggered backup end-to-end (needs a real shiny
  encounter); timed backup over hours (logic unit-reviewed only).

## 2026-07-18 — A2: Macro record & replay system
- **Added** `modules/macros.py`: macro engine — MacroStep/Macro dataclasses,
  run-length encoding of per-frame input bitfields (leading/trailing idle
  trimmed), human-editable YAML files in `profiles/<name>/macros/` (with a
  commented format header), friendly validation errors (`MacroError`),
  GUI-written replay selection in `macros/_selected.yml`, and a module-
  singleton `MacroRecorder` + frame listener that samples
  `context.emulator.get_inputs()` while armed.
- **Added** `plugins/macro_plugin.py`: registers the recorder listener.
- **Added** `plugins/custom_modes/macro_player.py`: "Macro (Custom)" bot
  mode — frame-accurate replay via `hold_button(inputs=…)`/`release_button`
  per step; loop or once; battles interrupt (default shiny/catch pipeline
  stays active) → loop mode restarts the macro from step 1, once mode
  stops to Manual. Held buttons are always released via try/finally.
- **Modified** `modules/gui/dashboard_gui.py`: compact one-row "MACROS"
  card (● Rec toggle with red recording indicator + name prompt on stop,
  macro dropdown, Loop checkbox, ▶ play → writes selection + switches to
  the Macro mode). Card placed directly under CONTROLS, and the default
  window height raised 720→860 (clamped to screen) after the A1 review
  note about column clipping — on very high DPI-scaled screens the column
  can still clip at the bottom; a scrollable tool column is a candidate
  for A4.
- **Modified** `.gitignore`: negation for `plugins/macro_plugin.py` (ML-2).
- **Verified**: py_compile; real-import discovery (both "Macro (Custom)"
  and "Patrol (Custom)" register; listener registers); headless battery —
  RLE (incl. idle trimming), YAML round-trip, listing skips `_selected`,
  selection round-trip, 6 malformed-file rejections, bitfield mapping,
  recorder empty→None; live GUI screenshot confirms the MACROS card
  renders under CONTROLS.
- **Not verified**: a real record→replay cycle against the game (test save
  sits at the title screen; needs hands-on play), battle-interruption
  behaviour in the wild.

## 2026-07-18 — A3: Patrol v2 — multi-map routes
- **Modified** `plugins/custom_modes/patrol.py`: `patrol.yml` waypoints now
  accept `- [x, y]` (current map, backward compatible) OR
  `- {map: [group, number], at: [x, y]}`; both validated with friendly
  errors (exact-key check, int-pair check incl. bool rejection). `run()`
  navigates per-waypoint to the explicit map or the mode's starting map.
  Docstring/config example updated (incl. the warp limitation note).
- **Verified**: py_compile + discovery; parse semantics test (mixed
  old/new formats accepted; 5 malformed variants rejected).
- **Not verified**: live multi-map walk (needs a progressed save).