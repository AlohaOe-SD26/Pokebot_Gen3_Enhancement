# 2026-09-29 — design v2 step 7 (RP) GRADED: the rare predicate is built and inert; pseudo = Bagon + Snorunt; the pre-registered control FAILED as written, and was handled exactly as pre-registered

> Predictions: `2026-09-29-rarepredicate-PREDICTIONS.md` (`19290f8c`, committed while the Shoal Cave measurement was
> still running). Code: `5fd35957`. Evidence: `tools/story-dev/evidence/2026-09-29-rarepredicate-SHOALPATH.txt`
> (production `calculate_path`, the load-bearing one) and `…-ACCESSGATES.txt` (the verifier's flood fill,
> supporting only). The gate `probe_rarity_predicate.py` is the SPEC, not evidence (the predictions say why).

## RESULTS

| # | Prediction | Reading | Verdict |
|---|---|---|---|
| **R1** | Snorunt's Ice Room needs Strength; Snorunt joins pseudo with `{strength, surf}` | ⚠ Its pre-registered instrument (the verifier's probe) was DISQUALIFIED by R3. Graded instead by `probe_rarity_shoal_path.py` on production `calculate_path`: the Ice Room's ONLY entrance is the Lower Room warp (28,11). With the boulder present (flag 0x11 clear), none of the three Lower Room arrivals has a path to it, while the push tile (24,3) IS reachable. With the boulder gone, arrivals (7,2) and (2,6) do reach it. The disqualified flood says the same (83 tiles without Strength, 102 with; the push East ×3 validated tile by tile) | ✅ CONFIRMED, on a substitute instrument that is stated as such |
| **R2** | The Route 125 approach needs Surf | `calculate_path` from Mossdeep (19,11) to the Route 125 cave warp (22,19): no path on foot, a path with Surf. The flood: the warp's on-foot component is an island of 91 tiles | ✅ CONFIRMED |
| **R3** | The Meteor Falls control reproduces 262 / 299 in OUR ROM reader | The verifier's flood from (27,18): **296 on foot, 333 with Surf** | ❌ **FAILED as written.** The pre-registered consequence was applied: the probe is not the citation for any entry, and the Meteor Falls entries keep their 2026-09-11 citation |
| **R4** | Spheal stays out | Spheal's easiest Shoal Cave room needs `{surf}` (gate D7) | ✅ |
| **R5** | The Shoal Cave entries change no species but Snorunt | After regeneration, S3 = `{361, 371}` and S6 (no other species carries a reason) passes | ✅ |
| **R6** | An independent decomp re-derivation gives the same lists | A fresh agent derived every list BLIND from pret/pokeemerald `f90719c4` (`wild_encounters.json`'s `gWildMonHeaders` group, `species_info.h`, `pokedex.h`, all 116 `map.json` + `region_map_sections.json`) and only then opened our table. The rate list (14), the variant list (6 genders, exact fractions), pseudo `{361, 371}`, 131 wild rows, every best_rate, gender ratio, MAPSEC-ID set and map list, and all 63 MAPSEC IDs resolved against the decomp enum: identical. Two differences, both BY DESIGN: `variant` is never in a row's `reasons` (it is per-individual; `rarity.py` adds it), and Tentacruel's size-1 gate tie reads `rod` (the documented alphabetical tie-break; the rule uses only the size) | ✅ CONFIRMED |
| **R7** | Nothing else moves | Full suite: ALL 127 ENFORCING GATES PASS. No production file imports `modules.rarity` | ✅ |

## WHAT R3'S FAILURE MEANS (and does not)

- The two methods count differently; they do not disagree about the gate.
  - The 2026-09-11 figure (262/299) came from a decomp `map.bin` decode.
  - The verifier's flood reads OUR ROM through the production tile rules, and agrees with production `calculate_path`
    on 618 of 621 tiles of 1F_1R in both arms. That includes the two decisive tiles: the B1F warp tiles (5,4) and
    (26,28) are unreachable without Waterfall under every method.
  - So "B1F needs Surf + Waterfall" stands. The 34-tile difference is a COUNTING difference whose cause is not
    isolated. The verifier's hypothesis is elevation-0 handling: production treats an elevation-0 tile as a universal
    bridge. It is not measured.
- ⚠ The verifier then REPLACED its own exit criterion with the `calculate_path` agreement, after it had seen the
  mismatch. That is real evidence, but a post-hoc criterion is not a control. The probe carries a STATUS banner saying
  so, and it is cited as supporting only.
- The Meteor Falls numbers in `training_areas.py`'s comment (262/299/404) are therefore METHOD-SPECIFIC. Production's
  pathfinder sees about 296 on foot. Nothing reads those numbers; they are prose.

## FOUND ALONG THE WAY

- **KI-113 (filed): the runtime encounter reader holds the DEAD Altering Cave table.** `modules/map.py` keys wild
  headers by map, so the last of Altering Cave's nine wins (Smeargle), not the live set 0 (Zubat). The generator
  reads the first header and asserts that this is the ONLY difference between the two readers.
- **Only a Mystery Gift event script changes `VAR_ALTERING_CAVE_WILD_SET`** (`data/scripts/gift_altering_cave.inc`).
  I was about to write "nothing sets it" and checked the decomp first.
- **Q9's Zangoose claim was wrong** (the step 7 recon): our ROM has no wild table for it, and our obtainability data
  records it as version-exclusive. It is corrected in the v2 note.
- **The recon's "4 of 8 mutants are vacuous" was right, and each one was made killable:**
  - per-map counting, by a synthetic stub (P1);
  - Cave of Origin, by a row-set check (D4);
  - Route 130, by the row count (S7);
  - `edge[1]`, by `--check` plus the record's histogram (M13).
- **Two of the verifier's side remarks were wrong,** and are corrected in its probe:
  - the `reachable_on_foot()` it compared against lives in `tools/story-dev/probe_shoal_tide.py`, not in
    `training_areas.py`;
  - it "refuted" a Snorunt TILE (24,83), which was the Ice Room's (group, number) map key. Nobody claimed it as a tile.
- **UNVERIFIED (the verifier's reading only):** the Ice Room's TM07 Hail and Never-Melt Ice balls sit at (12,8) and
  (12,21), both on foot at low tide. The old Gemini notes said (15,6), "requires Surf". Nothing here depends on it.

## DECISIONS (06 has the entry)

- LOCAL = from the story path (Q6's proposal); bikes are not gates.
- Min over rows; MAPSEC by ID; the summed per-table rate.
- Shiny = ULTRA; legendary is folded into RARE.
- A `note` field; the index-0 guard.
- A static ROM read in place of the cache.

## WHAT THIS DOES NOT SHOW

- That any rare species is met, or what step 8 does with a verdict.
- That the gate table is complete. New Mauville, the Abandoned Ship, Artisan Cave, the Desert Underpass and the Safari
  Zone are unmeasured; their single-location species carry `gates_unmeasured`.
- Q5, Q6 and Q7 stay the user's. Q6's text now names Snorunt beside Bagon.
