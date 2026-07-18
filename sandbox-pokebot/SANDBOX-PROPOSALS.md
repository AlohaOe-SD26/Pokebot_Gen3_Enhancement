# Sandbox Enhancement Round — 2026-07-18

> `sandbox-pokebot/` is an isolated copy of `custom-pokebot/` where this
> round of enhancements is built and tested. **Nothing here touches the
> custom or original program.** Run it with `python install_sandbox.py`
> (repo root) or `cd sandbox-pokebot; python pokebot.py`. Items the user
> approves get promoted into custom-pokebot; the rest stay here or die.

## A. IMPLEMENTED IN THIS SANDBOX (ready for review)

> **Status (end of round, 2026-07-18):** A1–A4 all BUILT and machine-
> verified (headless test batteries + live GUI runs with the real ROM;
> evidence in SANDBOX-NOTES.md per item). Honest caveats needing REAL
> GAMEPLAY on the user's side: shiny-triggered backup, a full macro
> record→replay cycle, a live multi-map patrol, party sprites/shiny log
> with a progressed save. Everything else — backup/restore/cloud push,
> macro engine + YAML, GUI cards, scrollable column, handheld drawer —
> is verified working.

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

### A5. Handheld menu-hide + gamepad support (user-requested 2026-07-18)
- **Menu-hide**: handheld fullscreen hides the top menu bar entirely;
  opening the tool drawer (Pokéball/H/Back+Start) brings it back; closing
  hides it again; exiting handheld restores it. Live-verified.
- **Gamepad (XInput)**: the Ally's controller (or any Xbox pad) plays the
  game in Manual mode — D-Pad/left stick = movement, A/B (+X/Y as
  B/A seconds), Start/Back = Start/Select, LB/RB = L/R, and **Back+Start
  toggles the tool drawer** from the couch. Status shown in the STATUS
  card. Pad play records into macros automatically. Unit-tested with a
  stubbed controller; **needs the user's Ally for a real-pad test** (no
  controller exists on the dev machine — note: there was no controller
  support before this; upstream is keyboard-only).

### A7. Warp-aware global pathfinding (punch-list #8)
Bots can now navigate ANYWHERE: `navigate_to_anywhere(map, coords)` plans
through doors, stairs, and cave entrances using a world graph extracted
from the game's own map data (518 maps / 1,268 warp edges for Emerald,
built in 0.02 s and cached per ROM). Patrol v3 uses it automatically —
waypoints can span the whole world. Excluded on purpose: Dive routes and
save-data ("dynamic") warps; locked doors fail with a clear error.
Verified 23/23 against the real ROM (graph ground truths, cache, planner,
dry-run walking); an actual cross-warp walk needs a real save (user test).

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
