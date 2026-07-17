# Custom PokéBot — Documentation
> Docs in THIS folder describe our custom version only (what we changed,
> added, and why). Everything inherited unchanged from upstream is
> documented in `../../40cakes repo/DOCUMENTATION/` — don't duplicate it
> here; link to it.

## Current state
`custom-pokebot/` was forked 2026-07-17 as an exact copy of the upstream
mirror at commit `5dd898f8`. **No divergences yet** — see
`DIVERGENCE-LOG.md`, which tracks every intentional difference from
upstream.

## Planned enhancements (punch list in PROJECT KNOWLEDGE/03)
- #3 Custom automations/bot modes (via the plugin system —
  `plugins/*.py`, see upstream doc 01 §plugins and doc 03 §mode contract)
- #4 One-script setup/install/update
- #5 Total custom interface
- #6 Further custom features

## Rules for working in this folder
- Every intentional change from upstream gets a `DIVERGENCE-LOG.md` entry
  (file, what, why) — this is what keeps upstream updates mergeable.
- Prefer extension points (plugins, bot modes, HTTP API) over editing
  upstream files in place.
- When the `40cakes repo/` mirror pulls an upstream update, its changes
  are reviewed against this folder per the UPDATE-LOG ritual — nothing is
  auto-applied here.
