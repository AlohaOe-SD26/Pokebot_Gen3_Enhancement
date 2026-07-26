# Vision & Design — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Source of truth for INTENT.

## One-liner
An enhanced, deeply documented fork of [40Cakes/pokebot-gen3](https://github.com/40Cakes/pokebot-gen3) — a Python shiny-hunting bot that drives Gen-3 Pokémon games (Ruby/Sapphire/Emerald/FireRed/LeafGreen) through libmgba — maintained in this repo with custom automations, a one-script installer, and a fully custom interface.

## Problem & purpose
The upstream pokebot-gen3 is powerful but its inner workings are only lightly
documented for developers. To enhance it confidently (and to reuse its
techniques elsewhere), we first need a complete, human-language map of what
every part does, why it exists, and where it plugs in. This project:
1. **Documents** the entire upstream codebase (intent + mechanics, tied to
   code with file:line references) under `40cakes repo/DOCUMENTATION/`.
2. **Mirrors** upstream in `40cakes repo/pokebot-gen3/` (git subtree,
   pristine, checked for upstream updates DAILY per the CLAUDE.md
   directive; sync history in `40cakes repo/UPDATE-LOG.md`, superseded
   docs snapshotted in `DOCUMENTATION/_history/`).
3. **Enhances** the bot in `custom-pokebot/` — our fork, documented in
   `custom-pokebot/DOCUMENTATION/`, with every intentional difference from
   upstream tracked in `custom-pokebot/DIVERGENCE-LOG.md`.
4. **Feeds a sibling project**: key findings useful to the separate
   "Pokémon Emerald AI" project (an AI that plays Emerald) are collected in
   `Pokemon_Emerald_AI_Notes.md` at the repo root.

## Goals
- Complete developer documentation of the upstream codebase (every module's
  intent described in human language, tied to code).
- Custom automations/bots (new bot modes beyond the stock ones).
- Easy setup/install/update script (see
  `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md` — Nick's
  installer-as-codebase pattern is the reference for how installers should
  feel; the final design must be reconciled with this repo being git-based).
- A total custom interface (replace/augment the stock Tkinter GUI, likely
  building on or extending the bot's HTTP API).
- Many more custom features over time (punch list is the queue).

## Non-goals (explicitly out of scope)
- Cheating beyond upstream's philosophy is not a design goal by default —
  upstream deliberately plays "as if human" (no RNG manipulation, no memory
  writes for outcomes). Deviations from this are per-feature decisions.
- Contributing back upstream is not required (we maintain our own fork),
  though clean separation of our changes keeps `git subtree pull` viable.

## Whole-program intent
A user should be able to: install the bot on a fresh Windows machine with
one script; pick a game profile; choose from stock AND custom automation
modes; watch/control everything from a modern custom interface; and trust
that the documentation explains how any part works when they want to extend
it.

## Components & their individual intent

### Upstream mirror (`40cakes repo/pokebot-gen3/`)
- **Purpose:** pristine, always-current copy of upstream (git subtree,
  remote `upstream-pokebot`, squashed; currently at `5dd898f8`).
- **Must do:** be checked against upstream daily; only change via
  `git subtree pull`.
- **Must not do / constraints:** NEVER hand-edited; never commit ROMs,
  saves, or profiles (upstream `.gitignore` covers these).

### Upstream documentation (`40cakes repo/DOCUMENTATION/`)
- **Purpose:** the human-language developer map of the ORIGINAL bot —
  per-layer docs with intent, mechanics, file:line references, plug-in
  points. `00-CODEBASE-OVERVIEW.md` is the entry point.
- **Must do:** track the mirrored commit; snapshot superseded versions to
  `_history/` before updating; log every sync in `../UPDATE-LOG.md`.

### Our fork (`custom-pokebot/` + its `DOCUMENTATION/`)
- **Purpose:** the codebase we actually enhance and ship. Forked from
  upstream `5dd898f8` on 2026-07-17.
- **Must do:** log every intentional difference from upstream in
  `DIVERGENCE-LOG.md`; document only the CUSTOM parts in its
  `DOCUMENTATION/` (link to upstream docs for inherited behavior).
- **Must not do / constraints:** upstream updates are never auto-applied
  here — they're reviewed per the UPDATE-LOG ritual.

### Story-Mode bot (`plugins/custom_modes/story_mode.py` + `modules/story/`)
- **Purpose:** a *scripted, deterministic* bot that plays Emerald from a fresh
  save through the whole story by itself (punch-list #24). Driven by observed
  game state (maps, coords, script names, flags) and hard sequences — NOT by
  learning.
- **Why it matters (its role in the bigger picture):** it is the **reference /
  scaffold for the SEPARATE "Pokémon Emerald AI" project** — an AI meant to
  learn to play the game *organically, like a human*. The Story bot provides a
  known-good, repeatable trajectory (what to do, where, in what order) and its
  documentation captures the game mechanics/map-facts/decision-points, so the AI
  project can **learn from the reference + notes to speed up its training**. The
  AI does NOT call the bot at runtime; the two never share code. "Complete the
  story unattended" is step 1; human-like behaviour is a later, separate layer.
- **Consequence for our practice:** documentation quality is a first-class
  deliverable here — capture the WHY, the game facts, and HOW they were
  discovered (recon), not just the code. Deep design + recon method live in
  `12-STORYMODE-DESIGN.md` (see its §P purpose note and §R recon playbook).

### Emerald AI notes (`Pokemon_Emerald_AI_Notes.md`)
- **Purpose:** cross-project transfer file — everything in this codebase
  useful to the separate Pokémon Emerald AI project (memory reading, input
  injection, state decoding, battle logic, headless control), written so
  that project can consume it without reading this repo.
- The Story-Mode bot (above) is the main body of that transfer: a documented
  end-to-end playthrough for the AI project to learn from.

### Endless Loop ×4 (`modules/endless_x4.py`, `tile_bridge`, `tile_mosaic`, `gui/tile_child`)
- **Purpose:** a TEST INSTRUMENT, not a gameplay feature. It exists to raise the
  rate at which the Story bot produces reviewable failure data, and to guarantee
  that data covers all three starters instead of whatever the RNG happened to
  pick. Four independent story bots run at once, each looping cold starts for
  ever, tiled 2×2 inside the dashboard so a human can watch all four and hand the
  logs over.
- **Why it is watchable rather than merely fast:** the earlier headless
  endless-runs attempt was abandoned precisely because it gave the user nothing
  to see. Throughput alone was not the missing thing; OBSERVABILITY was. A
  headless `tools/story-dev/livetest.py` batch remains the faster way to generate
  logs, and both are kept on purpose.
- **Why the starter split:** starter choice changes which failures are reachable
  (Torchic has no super-effective move vs. Roxanne; the 3,011-flee livelock was a
  Treecko run). Pinning P1/P2/P3 and rolling P4 makes starter-specific bugs
  impossible to miss by luck.
- **Design constraint it must respect:** lanes are separate PROCESSES because
  `context` is a process-wide singleton. Nothing in the bot may be refactored to
  "support multiple emulators" on this feature's account — see 06-DECISIONS-LOG.

### Future: custom automations, installer, custom interface
- Intent recorded in Goals above; each gets its own component section here
  when built.

## Design principles & style
- Upstream code style: Python 3.12, `black` formatting — match it when
  editing vendored code.
- Documentation style: intent first ("what is this FOR"), then mechanics,
  always tied to code with `file:line` references; explain why, not just what.
- Enhancements should prefer extension points (plugins, bot modes, HTTP API)
  over invasive edits to upstream files, to keep upstream merges cheap.
