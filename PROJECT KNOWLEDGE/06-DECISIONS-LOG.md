# Decisions Log — Pokebot_Gen3_Enhancement
> APPEND-ONLY. New entries at the end. Never rewrite history — if a decision
> is reversed, append a NEW entry that supersedes the old one and says so.

---

## 2026-07-17 — Adopted the Claude Code Project Kit
- **Decision:** Standardize on the kit's CLAUDE.md directives + PROJECT
  KNOWLEDGE structure + per-item commit/push definition of done.
- **Context:** Make every session resumable by any agent with zero context.
- **Alternatives rejected:** Ad-hoc per-chat context pasting (doesn't scale,
  loses history).

## 2026-07-17 — Vendor upstream via git subtree (squashed), not clone/submodule
- **Decision:** Import 40Cakes/pokebot-gen3 into `pokebot-gen3/` with
  `git subtree add --squash` and keep an `upstream-pokebot` remote.
- **Context:** The enhanced fork must live IN this repo (user requirement),
  while still being able to absorb upstream fixes.
- **Alternatives rejected:** plain clone kept as nested repo (files not
  tracked in our repo); git submodule (poor fit for a fork we edit
  heavily); copy-without-history (loses the cheap upstream-update path).
- **Consequence:** upstream updates come via
  `git subtree pull --prefix pokebot-gen3 upstream-pokebot main --squash`;
  our edits to vendored files should prefer extension points (plugins,
  bot modes, HTTP API) to keep those merges cheap.

## 2026-07-17 — Installer enhancement will ADAPT, not literally apply, the base64 pattern
- **Decision (provisional, to finalize at punch-list #4):** The
  installer-as-codebase pattern (REFERENCE-INSTALLER-PATTERN.md) assumes a
  no-git, ~50-file pure-source program. This project is git-based and the
  bot is ~90 MB with thousands of binary assets, so a literal single-file
  base64 installer is infeasible; we will instead deliver its UX
  (one-script setup/update/heal, drift detection, protected user files)
  on top of git/subtree mechanics.
- **Alternatives:** literal base64 installer (rejected: size, binary
  assets, duplicates git's job); upstream's updater.py as-is (rejected:
  tied to upstream GitHub releases, no heal/verify step).
- **Status:** flagged for user sign-off when #4 is designed.

## 2026-07-17 — Two-folder fork layout + daily upstream sync (user directive)
- **Decision:** Restructure to (a) `40cakes repo/` holding a PRISTINE
  upstream mirror (`pokebot-gen3/`, git subtree re-added at the new
  prefix) plus all documentation about the original program
  (`DOCUMENTATION/`, with `_history/` snapshots and an append-only
  `UPDATE-LOG.md`); and (b) `custom-pokebot/` holding our enhanced fork
  with its own `DOCUMENTATION/` and `DIVERGENCE-LOG.md`. Upstream is
  checked DAILY (session-start directive in CLAUDE.md); updates are pulled
  into the mirror and its docs updated (old versions snapshotted), but
  NEVER auto-applied to the custom fork — they're listed for user review.
- **Context:** Direct user instruction 2026-07-17: keep a running,
  up-to-date record of the original repo separate from our custom version,
  with original-docs and custom-docs cleanly separated and historical doc
  versions retained.
- **Alternatives rejected:** single vendored copy enhanced in place
  (previous layout — conflated upstream tracking with our changes);
  git branches for original-vs-custom (invisible on disk, user wants
  folder-level separation).
- **Consequence:** the subtree prefix moved, so the pull command is now
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`.
  Custom and mirror start identical at upstream `5dd898f8` (git stores the
  duplicate blobs once, so repo size is unaffected).
