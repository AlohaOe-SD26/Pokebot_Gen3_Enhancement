# Changelog — Pokebot_Gen3_Enhancement
> APPEND-ONLY. Every meaningful change, fix, or addition gets a dated entry
> at the END of this file (chronological order, oldest first).
> Entry format:
>
> `## YYYY-MM-DD — short summary  (punch-list #N if applicable)`
> followed by bullets: what changed, why, files touched.

---

## 2026-07-17 — Project bootstrapped with Claude Code Project Kit
- Created PROJECT KNOWLEDGE skeleton (00–07), CLAUDE.md standing directives,
  Remote-Start launcher, git repository + remote.

## 2026-07-17 — Vendored upstream pokebot-gen3 (punch-list #1)
- Imported 40Cakes/pokebot-gen3 at upstream commit `5dd898f8` into
  `pokebot-gen3/` via `git subtree add --squash`; added `upstream-pokebot`
  remote for future upstream pulls.

## 2026-07-17 — Deep documentation pass over the codebase (punch-list #2)
- Wrote `PROJECT KNOWLEDGE/CODEBASE/00–05`: overview + five layer docs
  (core runtime/emulator, game-state decoding, bot modes/battle engine,
  GUI/web/Discord interfaces, stats/config/data/tests/distribution) —
  ~2,400 lines, intent-level human language tied to code with file:line
  references, each ending with enhancement opportunities. Produced by five
  parallel documentation agents reading the source, then synthesized.
- Wrote `Pokemon_Emerald_AI_Notes.md` (repo root): standalone transfer
  notes for the sibling Pokémon Emerald AI project (emulator harness,
  symbolic memory reading, battle observation/math, navigation primitives,
  data files, integration paths).
- Copied the user's installer-as-codebase spec into
  `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md` for punch-list #4.
- Filled in `01-VISION-AND-DESIGN.md`, `02-ARCHITECTURE.md`, seeded
  `03-PUNCH-LIST.md` (#2–#6).

## 2026-07-17 — Restructure: two-folder fork layout + daily upstream sync
- Moved the upstream mirror to `40cakes repo/pokebot-gen3/` (subtree
  re-added at the new prefix) and the codebase docs to
  `40cakes repo/DOCUMENTATION/` (with `_history/` for versioned snapshots).
- Created `custom-pokebot/` — our fork, an exact copy of upstream
  `5dd898f8` — with `DOCUMENTATION/` and `DIVERGENCE-LOG.md`.
- Added `40cakes repo/UPDATE-LOG.md` (append-only upstream sync record)
  and the daily upstream-check standing directive to CLAUDE.md.
- Updated vision/architecture docs and decisions log for the new layout.

## 2026-07-17 — Documentation verification pass (sanity check)
- Six adversarial verifier agents re-checked every claim in the seven docs
  against source: ~975 claims verified, 39 errors fixed (8 in doc 01, 7 in
  doc 02, 7 in doc 03, 6 in doc 04, 5 in doc 05, 6 in AI notes; overview
  clean). Highest-value fixes: inverted LoseOnPurpose/Explosion behavior,
  navigate_to warp/surf limits, `decide_turn` returns a tuple, OBS uses
  obs-websocket not hotkeys, `/stream_video` sends nothing while video is
  disabled, work-queue errors exit the process.
- Three upstream bugs discovered and recorded as KI-1..KI-3 in
  05-KNOWN-ISSUES.md (stale pokebot.spec; `modified_stats()` TypeError
  dead code; stale `disable_default_battle_handler` docstring).
- Lesson logged as ML-1 in 08-MISTAKES.md (verify agent-written docs
  before building on them).

## 2026-07-17 — Custom-automations framework + Patrol mode (punch-list #3, partial)
- Built the drop-in custom-modes platform in `custom-pokebot/`:
  `plugins/custom_modes_loader.py` (auto-registers BotMode subclasses from
  the new `plugins/custom_modes/` folder via the stock plugin API) and the
  first custom bot: "Patrol (Custom)" (`plugins/custom_modes/patrol.py`) —
  waypoint-loop shiny hunting configured by a per-profile `patrol.yml`.
- Zero upstream files modified (logged in custom-pokebot/DIVERGENCE-LOG.md).
- Verified: py_compile + structural smoke test (loader discovers PatrolMode
  through the real files with bot modules stubbed; config validation
  failure/success paths pass). Live run pending ROM/deps — #3 stays open.
- How-to documented in `custom-pokebot/DOCUMENTATION/01-custom-automations.md`.

## 2026-07-17 — One-script installer/updater/healer (punch-list #4)
- Added `install.py` (repo root): 6-step git-driven adaptation of the
  installer-as-codebase pattern — finds/offers 64-bit Python 3.11-3.13,
  clones or fast-forward-updates the repo, detects + consent-restores
  drifted tracked files (user data untracked → never touched), pre-runs
  the bot's dependency bootstrap, smoke-checks critical files, offers
  launch. `--check-only` (read-only) and `--yes` (unattended) modes.
- Tested end-to-end on this machine: heal restored a deliberately
  corrupted file; dependencies + libmgba installed into Python 3.12;
  fresh-empty-folder clone succeeded after fixing Windows MAX_PATH
  ("Filename too long") via `core.longpaths=true` (+ partial-clone
  cleanup); cp1252 console crash and PowerShell piped-BOM prompt bugs
  fixed. Decision recorded in 06; also added root README.md.
- FIXED CRITICAL: upstream's `.gitignore` was silently excluding the #3
  custom-modes framework from commits (found by the fresh-clone test) —
  negation rules added (divergence logged), files now tracked (ML-2).
- Upgraded #3 verification: real-import discovery test passed (actual bot
  modules under Python 3.12, PatrolMode registers).
