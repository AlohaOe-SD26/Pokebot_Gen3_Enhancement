# Custom PokéBot — Documentation
> Docs in THIS folder describe our custom version only (what we changed,
> added, and why). Everything inherited unchanged from upstream is
> documented in `../../40cakes repo/DOCUMENTATION/` — don't duplicate it
> here; link to it.

## Current state
`custom-pokebot/` was forked 2026-07-17 as an exact copy of the upstream
mirror at commit `5dd898f8`.

**`DIVERGENCE-LOG.md` is the authoritative list of every intentional difference
from upstream — count them there, not here.** ⛔ This line used to carry a NUMBER
("No divergences yet", then "EIGHT user-approved promotions as of 2026-08-10")
and it went stale BOTH times — the second time for four weeks, while the log grew
to 42 entries. ⇒ ⭐ **a count kept in two places is a count that will disagree with
itself; point at the owner instead of copying its answer.**

The headline divergence is the **Story mode** (`plugins/custom_modes/story_mode.py`
plus `modules/story/`): a bot mode that plays Emerald from a cold start. Built
content runs **Littleroot → 8 badges → Seafloor Cavern → Sootopolis → VICTORY ROAD →
the Pokémon League door, with the Elite Four healing basket bought** (Segment 23,
promoted 2026-09-06 — see `DIVERGENCE-LOG.md` that date). It is DRIVEN end to end:
`--build custom --driver ch23chapter post_wally.ss1` returns `ACCEPTANCE: PASS`,
`done=True`, `whiteouts=0`.
⛔ **The next unwritten beat is §Ch24, THE ELITE FOUR** — five consecutive fights
with no nurse between rooms. `story_mode.py` hands to manual at the League door.
‼ *(This paragraph read "Segment 15 … the next unwritten beat is the Slateport
submarine" for four weeks after that stopped being true.)* ‼ Story mode is OUR addition and has no upstream counterpart, so
nothing in `../../40cakes repo/DOCUMENTATION/` describes it — the design lives
in `PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md` and the running state in
`PROJECT KNOWLEDGE/04-HANDOFF.md`.

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
