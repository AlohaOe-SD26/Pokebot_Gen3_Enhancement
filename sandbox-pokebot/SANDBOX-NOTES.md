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