2026-09-29 design v2 step 7 (RP), prediction R6: a BLIND re-derivation of the rarity lists from the decomp.

An independent agent wrote derive.py from the rule text alone, BEFORE opening our table, then compare.py.
Decomp: pret/pokeemerald at f90719c46ce710427cfcae65419a3fa684b34a8a. Inputs (not committed; fetch with
`gh api repos/pret/pokeemerald/contents/<path>?ref=f90719c4 -H "Accept: application/vnd.github.raw"` into this folder):
  src/data/wild_encounters.json, src/data/pokemon/species_info.h, include/constants/species.h,
  include/constants/pokedex.h, src/pokemon.c, include/constants/pokemon.h,
  src/data/region_map/region_map_sections.json, data/maps/map_groups.json, and data/maps/<Folder>/map.json for
  every folder in id2folder.json (saved under maps/<Folder>.json).
Run: python derive.py  (writes derived.json), then python compare.py  (reads our committed emerald_rarity.json).
compare-OUTPUT.txt is compare.py's output against the table as of the step 7 review fixes.
Result: identical in every field (131 wild rows, best rates, gender ratios, MAPSEC-ID sets, map lists, gates of every
single-MAPSEC species, reason sets, 21 legendaries, Feebas). The listed DIFFS are by design: `variant` never appears in
a row's `reasons` (it is per individual; modules/rarity.py adds it), and a size-1 gate tie reads `rod` (the documented
alphabetical tie-break; the rule uses only the size). Rows marked "(multi-mapsec, info)" are informational.
