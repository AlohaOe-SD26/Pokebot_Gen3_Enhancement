# 2026-09-29 — design v2 step 7 (RP) GRADED: the rare predicate is built and inert; pseudo = Bagon + Snorunt. R3 (the pre-registered control) FAILED, so the probe it guarded is cited for NOTHING, and R1/R2/R4 are graded on a SUBSTITUTE instrument that is not controlled either

> Predictions: `2026-09-29-rarepredicate-PREDICTIONS.md` (`19290f8c`, committed while the Shoal Cave measurement was
> still running). Code: `5fd35957`, plus the review fixes. The gate `probe_rarity_predicate.py` is the SPEC, not
> evidence (the predictions say why).
>
> Evidence:
> - `tools/story-dev/evidence/2026-09-29-rarepredicate-SHOALPATH.txt`: production `calculate_path`, the substitute
>   instrument, raw output.
> - `…-R6-decomp/`: the blind decomp derivation, its scripts and its output.
> - `…-SUITE.txt`: the full gate suite.
> - `…-ACCESSGATES.txt`: the disqualified probe, kept for the record ONLY.

## RESULTS

| # | Prediction | Reading | Verdict |
|---|---|---|---|
| **R1** | Snorunt's Ice Room needs Strength; Snorunt joins pseudo with `{strength, surf}` | ⚠ R1's pre-registered instrument (the verifier's flood) was DISQUALIFIED by R3, and nothing it printed is used here. Graded on a SUBSTITUTE, `probe_rarity_shoal_path.py` (production `calculate_path`). **Necessity:** the Ice Room's only entrance is the Lower Room warp (28,11). With the boulder in place, no Lower Room arrival has a path to it, while the push tile (24,3) is reachable. A room-to-room search from the Route 125 arrival reaches the Lower Room's push side and never the Ice Room. **Sufficiency:** with the boulder pushed east three times (a live boulder at (28,3)), a path exists; pushed twice, none | ✅ CONFIRMED, on a substitute stated as such |
| **R2** | The Route 125 approach needs Surf | Substitute instrument. From the cave warp (22,19) there is no on-foot path to Mossdeep, while its walkable neighbour (22,20) IS reached on foot (the control). From Mossdeep the warp is reached with Surf and not without; an on-foot path inside Mossdeep exists (the control) | ✅ CONFIRMED (substitute) |
| **R3** | The Meteor Falls control reproduces 262 / 299 in OUR ROM reader | The verifier's flood from (27,18): **296 on foot, 333 with Surf** | ❌ **FAILED.** The pre-registered consequence was applied in full: the probe is cited for NOTHING, and the Meteor Falls entries rest ONLY on their 2026-09-11 citation |
| **R4** | Spheal stays out | Substitute instrument (S3 + S4): Spheal's easiest home, the Entrance room, needs only the Surf of the approach. It is reached on foot from the Route 125 arrival | ✅ (substitute; the gate's D7 only repeats the table, so it is not the grader) |
| **R5** | The Shoal Cave entries change no species but Snorunt | After regeneration, pseudo = `{361, 371}` and no other species carries a reason (S3, S6 over the table the generator writes) | ✅ |
| **R6** | An independent decomp re-derivation gives the same lists | A fresh agent derived every list BLIND from pret/pokeemerald `f90719c4`, and only then opened our table (`evidence/…-R6-decomp/`). Identical in every field: 131 wild rows, best rates, gender ratios, MAPSEC-ID sets, map lists, the gates of every single-location species, the reason sets, all 63 MAPSEC IDs. Two differences, both BY DESIGN: `variant` is never in a row's `reasons` (it is per individual; `rarity.py` adds it), and a size-1 gate tie reads `rod` (the documented tie-break; the rule uses only the size) | ✅ CONFIRMED |
| **R7** | Nothing else moves | Full suite after the review fixes: `evidence/…-SUITE.txt`. No production file imports `modules.rarity` | ✅ |

## THE SUBSTITUTE INSTRUMENT IS NOT CONTROLLED EITHER, AND WHY THE VERDICT STANDS ANYWAY

- `calculate_path` reaches about 293 tiles on foot on Meteor Falls 1F_1R, where the controlled 2026-09-11 decoder
  reached 262. So the substitute fails the same count that disqualified the original.
- It is the MORE PERMISSIVE of the two there. Its NO-PATH readings are therefore conservative:
  - the boulder in place;
  - pushed only twice;
  - on foot from the cave warp.
  The pseudo verdict needs only those, because two gates must be NECESSARY.
- Its PATH readings (three pushes, with Surf, the room-to-room search) show SUFFICIENCY with a permissive
  instrument, and nothing in the rule depends on them.
- ⚠ The disqualified flood's "control" was agreement with `calculate_path`, but its rules were transcribed FROM
  `calculate_path`. Such agreement cannot fail, so it proves nothing. The 34-tile difference against the 2026-09-11
  decoder is a difference in REACHABILITY RULES or in counting, and its cause is NOT isolated. The verifier's
  hypothesis (elevation-0 tiles as a universal bridge) is a rules difference, and it is unmeasured.
- Consequence for the prose: the numbers 262/299/404 in `training_areas.py`'s comment and production's ~293 describe
  DIFFERENT rule sets. No code reads either.

## FOUND ALONG THE WAY

- **KI-113 (filed): the runtime encounter reader holds the DEAD Altering Cave table.** `modules/map.py` keys wild
  headers by map, so the last of Altering Cave's nine wins (Smeargle), not the live set 0 (Zubat). The generator
  reads the first header, and asserts that this is the ONLY difference between the two readers.
- **Only a Mystery Gift event script changes `VAR_ALTERING_CAVE_WILD_SET`** (`data/scripts/gift_altering_cave.inc`).
  I was about to write "nothing sets it" and checked the decomp first.
- **The review found real gaps in the gate, now fixed:**
  - L27's empty slot used species 0, so the index-0 guard hid a deleted `is_empty` guard. It now names Mew (M14).
  - `encounter_rarity` did not check the checksum or eggs. A random blob read as Lugia, and an egg of a male Skitty
    read ULTRA. Both now have notes `invalid` and `egg` (M15, M16).
  - The `--check` comparator was never fault-tested, and it alone catches edits to the gate table and the method
    rules. There is now a drifted-copy arm (C2), and a blind comparator must turn it red (M17).
- **The first S4 draft checked one hop per room and landed in the Lower Room's (19,11) pocket.** The real low-tide
  route runs through the Stairs room. S4 is now a room-to-room search.
- **Fishing tables are read on the pointer alone,** as the game does (`DoesCurrentMapHaveFishingMons`). Our ROM has
  no zero-rate table, so nothing changes.
- **Q9's Zangoose claim was wrong** (the step 7 recon), and so are its other non-Hoenn learners. Our data marks
  Scyther, Farfetch'd and Cubone unobtainable in Emerald, and Scizor and Marowak follow. Corrected in the v2 note.
- **The disqualified probe had three wrong remarks** (its STATUS banner lists them):
  - the location of `reachable_on_foot()`;
  - a "refuted" Snorunt TILE that was a map key;
  - its mismatch explanation, which is item-ball templates, not live objects.
- **UNVERIFIED (from the disqualified probe only):** the Ice Room's item balls sit at (12,8) and (12,21). Nothing here
  depends on it.

## DECISIONS (06 has the entry)

- LOCAL = from the story path (Q6's proposal); bikes are not gates.
- Min over rows; MAPSEC by ID; the summed per-table rate.
- Shiny = ULTRA; legendary is folded into RARE.
- A `note` field; the empty / index-0 / checksum / egg guards.
- A static ROM read in place of the cache.

## WHAT THIS DOES NOT SHOW

- That any rare species is met, or what step 8 does with a verdict. ⚠ Step 8 must pass `encounter.pokemon`, not the
  `EncounterInfo`: the latter reads not-rare (`adapter_error`), a trap its recon measured.
- That the gate table is complete. New Mauville, the Abandoned Ship, Artisan Cave, the Desert Underpass and the Safari
  Zone are unmeasured; their single-location species carry `gates_unmeasured`.
- Q5, Q6 and Q7 stay the user's. Q5's and Q6's texts now state the exact rules the build uses.
