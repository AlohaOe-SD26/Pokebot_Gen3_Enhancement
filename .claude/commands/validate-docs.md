# /validate-docs — Cross-validate the story documentation before building a chunk

User directive 2026-07-22: the story docs (detailed but built mostly from static ROM
recon + decomp script-reading) can be SUBTLY WRONG about SEQUENCING — the "do X before Y
unlocks" chains that only a walkthrough makes obvious (e.g. KI-11: the Oceanic Museum
entrance is grunt-sealed until you talk to Dock at Stern's Shipyard — invisible in static
recon, obvious in any walkthrough). Before building a new chunk (and whenever a build hits
a wall), validate the relevant doc section against MULTIPLE sources of truth, correct it,
and re-verify.

## When
- BEFORE starting a new story chunk: validate that chunk's `12-STORYMODE-DESIGN.md`
  section (atlas + beats + gating).
- MID-BUILD when something doesn't match expectations (a sealed door, a missing NPC, a
  flag that won't set): stop and validate rather than guessing.

## The three sources of truth (cross-check, don't trust one)
1. **Decomp — mechanics & exact flags/vars** (authoritative for WHAT the game sets):
   `https://raw.githubusercontent.com/pret/pokeemerald/master/data/maps/<Map>/scripts.inc`
   and `.../map.json` (objects/warps/coord_events), `.../src/*.c`. Use WebFetch.
2. **Live ROM recon — coordinates, collision, live object/flag state** (authoritative for
   WHERE): the `tools/story-dev/*probe.py` pattern (`get_map_data`, `get_map_objects`,
   `get_event_flag/var`, `calculate_path`). Ground truth for the actual save state.
3. **Walkthroughs — step ORDER & prerequisites** (authoritative for the player SEQUENCE):
   Bulbapedia / Serebii / a written walkthrough. This is what catches the sequencing the
   other two miss. The USER is also a source — ask when a real-play detail is faster.

## Procedure
1. Read the doc section for the chunk. List every claim: warps, NPC coords, gating
   flags/vars, the step order, completion signals.
2. Check each claim against the sources above. Decomp for flags/mechanics; a probe for
   coords/collision/live state; a walkthrough for the ORDER and any prerequisite step.
3. Where they DISAGREE, the doc is wrong (or incomplete). Correct `12-STORYMODE-DESIGN.md`
   in place; note the correction in `07-CHANGELOG.md`; if it was a real trap, add a
   `05-KNOWN-ISSUES` / `08-MISTAKES` prevention note.
4. RE-VERIFY the corrected facts (re-run the probe; confirm the flag/warp; if code exists,
   run the harness segment). A correction isn't done until re-verified.
5. Only then build the chunk. Fold anything learned back into the doc + the playbook.

## Rules
- Tag every doc fact by its source & confidence: `✓ decomp`, `✓ probe`, `✓ walkthrough`,
  `⚠ VALIDATE LIVE`. Never leave an unqualified sequencing claim.
- Prefer the decomp for flags, the probe for coordinates, the walkthrough for order — and
  when two conflict, dig until you know WHY (that "why" is usually the real mechanic).
- Don't guess a state-write to paper over a sequencing gap; find the trigger (KI-11 lesson).
