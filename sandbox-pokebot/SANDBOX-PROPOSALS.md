# Sandbox Enhancement Round — 2026-07-18

> `sandbox-pokebot/` is an isolated copy of `custom-pokebot/` where this
> round of enhancements is built and tested. **Nothing here touches the
> custom or original program.** Run it with `python install_sandbox.py`
> (repo root) or `cd sandbox-pokebot; python pokebot.py`. Items the user
> approves get promoted into custom-pokebot; the rest stay here or die.

## A. IMPLEMENTED IN THIS SANDBOX (ready for review)

### A1. Backup & Restore system (user-requested)
Protects the three things that matter: **save files, savestates, profiles**
(incl. stats.db and per-profile configs like patrol.yml).
- **Local backups**: one zip per backup in `backups/<profile>/`, named by
  timestamp, with configurable retention (default keep 10).
- **Triggers**: manual (GUI button), automatic on every shiny encounter,
  and a timed interval (default every 2 h while running).
- **Cloud, two zero-friction backends**:
  1. **GitHub backend** — backups are committed + pushed to this private
     repo (`cloud-backups/<profile>/`, capped at the newest 3 per profile
     so the repo stays lean). Works today with zero new accounts: your
     repo IS the cloud. Restoring on another machine = `git pull`.
  2. **Synced-folder backend** — point it at any OneDrive/Dropbox/Google
     Drive folder; backups are mirrored there and those apps do the rest.
- **Restore**: from the GUI, pick any local/cloud backup → restored into a
  NEW profile name (never overwrites a live profile — the loaded profile
  is in use by the emulator; restoring over it would corrupt state).
- Config: `backup.yml` (global or per-profile), self-contained module —
  no upstream config-schema edits.

### A2. Macro record & replay system (user-requested "macros")
- **Record**: arm recording from the GUI while playing in Manual mode —
  every button press/duration is captured frame-accurately.
- **Save**: named macros as human-editable YAML in `macros/` (per profile).
- **Replay**: "Macro (Custom)" bot mode replays any macro once or looped —
  turning any hand-played sequence (a shop run, a soft-reset ritual, a
  daycare loop) into a one-click automation. Macros are also composable
  building blocks for future custom bots.

### A3. Patrol v2 — multi-map routes
`patrol.yml` waypoints may now specify a map: `- {map: [1, 4], at: [x, y]}`
(old `- [x, y]` still works = current map). Routes can cross directly
connected maps (upstream pathfinding limitation: warps/doors still can't
be pathed *through*).

### A4. GUI pack
- **Backups panel** in the tool column (Back up now / recent list / restore).
- **Party sprites**: each party row shows the Pokémon's sprite (shiny
  sprite when shiny) — the bot already ships every sprite.
- **Shiny log panel**: recent shinies with species + phase length.
- (All present in handheld drawer too.)

## B. PROPOSED — discuss on your return (not built yet)

| Idea | What it gives you | Effort |
|---|---|---|
| Encounter-rate trend chart | small canvas sparkline of enc/hr over the session | S |
| Stats browser window | sortable per-species table (encounters, shinies, IVs) from stats.db | M |
| Hunt planner | pick a target species → best mode + location suggested from the bot's own encounter tables | M |
| Shiny desktop notifications | toast + sound on shiny even when window is hidden (notify-py already a dep) | S |
| Catch-filter editor GUI | form-based editor for customcatchfilters.py / catch_block.yml | M |
| Profile manager UI | create/duplicate/rename/delete profiles from the GUI | S-M |
| Gamepad support | map an Xbox/Ally controller to Manual-mode inputs (XInput) — native handheld play | M |
| Multi-instance manager | run several profiles/bots at once, one aggregating dashboard | L |
| PKHeX quick-export button | one click → .pk3 of selected party/box mon | S |
| Stream overlay themes | restyle the OBS overlay to match the dashboard | S-M |
| Auto-update toast in GUI | "repo has updates — run install.py" notice at launch | S |

## C. Promotion rule
Approved sandbox features are copied into `custom-pokebot/` with their
DIVERGENCE-LOG entries and docs; the sandbox then rebases on the new
custom. Nothing is promoted without the user's explicit OK.
