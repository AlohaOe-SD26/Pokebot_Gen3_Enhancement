# 2026-09-29 — design v2 step 7 (RP, the rare-species predicate): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed, and WHILE the Shoal Cave measurement below is still running (its result was not
> known when this was written). Branch `wt/rarepredicate`, cut from `main` `838eea98`. Spec:
> `ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` §2 step 7 (a NOTE). Recon: a three-angle workflow (rate/variant,
> adversarial, pseudo/locations), whose output is a NOTE; every load-bearing claim below was re-measured or is
> pending re-measurement, as marked.
>
> ⚠ **What is and is not pre-registered here.** Step 7 is PURE (the design: "Proof: pure-only"). Its gate rows were
> written WITH the code and run while it was built. They are the SPEC, not predictions, and passing them is not
> evidence of anything beyond "the code does what the rows say". The predictions below are only the readings that
> were NOT yet measured when this file was written.

## THE CHANGE (planned)

- **`tools/story-dev/rare_species_dataset.py` becomes the authoritative generator.**
  - It reads the wild tables and each map's MAPSEC byte (header 0x14) **statically from our tracked ROM**, not from the
    gitignored `cache/`. The runtime cache has a defect the recon found (`modules/map.py` keys wild headers by map, so
    Altering Cave's LAST header wins, and the cache holds the dead set 8, Smeargle). The generator takes the FIRST
    header, as the game does, and asserts the cache differs from it in exactly that one map.
  - It applies the exclusions: the unused Cave of Origin maps 1-3, and Route 130's land table.
  - It writes `sandbox-pokebot/modules/data/emerald_rarity.json`, keyed by NATIONAL dex: 131 wild species, 21
    legendaries and Feebas.
  - `--check` regenerates and diffs. The 2026-08-06 reproduction is kept, and so is warp depth, as a diagnostic
    column. Without `cache/` each prints a visible SKIP.
- **New `sandbox-pokebot/modules/rarity.py`** (inert):
  - `RareVerdict(rare, tier, reasons, note)`;
  - `load_table()`, which returns `{}` and a warning on failure;
  - PURE `classify(row, *, gender, shiny)`;
  - `encounter_rarity(pokemon)`, which never raises.
- **New gate `tools/story-dev/probe_rarity_predicate.py`** (quick; no emulator):
  - L1-L33, literal rows through the REAL `Pokemon.gender`;
  - S1-S7, full-set equality;
  - D1-D6, data facts;
  - P1-P6, the pure rule on synthetic stubs;
  - C1, `--check`;
  - M1-M13, one mutant per guard;
  - N1-N2, negative arms.
- **New measurement probe `tools/story-dev/probe_rarity_access_gates.py`** (being written by an independent verifier
  now), with its evidence file. It is the citation for every `MAP_ACCESS_GATES` entry.

## DECISIONS (each stated so a reviewer can refute it)

- **The pseudo rule's "LOCAL" is pinned to Q6's proposal.** A gate is an HM field move or a fishing rod needed to
  reach the encounter FROM THE STORY PATH. A map the story walks through adds no gate, so Victory Road's Mawile,
  Hariyama and Lairon do not qualify (Q6's own example). **Bikes are not gates:** the user named HMs and a rod (03:1846-1854),
  never a bike. The recon found the design's word "LOCAL" contradicted Q6's "off the story path"; Q6 is the text the
  user will be shown, so it wins until the user answers.
- **Gates combine as the MIN over a species' rows** (its easiest home). Under max or union, Solrock (in Bagon's room,
  but also in 1F_1R with no gate) turns pseudo.
- **Locations are counted by MAPSEC ID, never by name.** UNDERWATER_124 and UNDERWATER_126 share the name "UNDERWATER".
- **Rate = the per-table SUMMED rate** (the design's numbers already use it). A strict single-slot reading gives 34
  species.
- **Shiny → tier ULTRA.** The record's ULTRA tier means "on every encounter, even if owned", which is exactly what the
  existing shiny branch does. The design said only "every other reason is RARE" and was silent on shiny.
- **Legendary is folded into RARE, stated as such.** RULING 25 lists it as a SIBLING of rare (06:8047); step 8 treats
  all three the same way.
- **`RareVerdict` gains a `note` field** (`no_data`, `no_species`, `adapter_error:<Type>`), so the "reason: no data"
  rows are not mixed into the rare reasons.
- **Species index 0 is guarded.** Its national number reads 151 (Mew), so an empty or garbled mon would otherwise be a
  legendary.

## PREDICTIONS (graded by the named reading; none of these was measured when this file was written)

- **R1 — Snorunt (Shoal Cave Ice Room).** Graded by `evidence/2026-09-29-rarepredicate-ACCESSGATES.txt`, claim C1.
  - I predict the independent flood CONFIRMS the recon: the Ice Room is reached only after a Strength push in the
    Lower Room, with nothing else needed inside at low tide.
  - Then Snorunt 361 gets `{strength, surf}` (Surf from the story path to Route 125's island), 1 MAPSEC, and
    **joins pseudo**. The gate's literal pseudo set becomes `{361, 371}`, and L gets a Snorunt row.
  - **Falsifier:** the flood reaches the Ice Room warp at low tide with no boulder moved. Then Snorunt has `{surf}`
    and stays out, and pseudo stays `{371}`. Either result is a RESULT, and the table follows it.
- **R2 — the Route 125 approach needs Surf** (claim C2: the cave entrance is on an island). **Falsifier:** the island's
  on-foot component touches a story-path map.
- **R3 — the Meteor Falls control reproduces 262 (on foot) and 299 (with Surf) from (27,18) on 1F_1R, in OUR ROM
  reader** (claim C3). B1F_2R is unreachable without Waterfall. **Falsifier:** any other count. Then nothing else
  that probe prints is believed, and the Meteor Falls entries keep only their 2026-09-11 citation.
- **R4 — Spheal 363 stays out under either R1 outcome.** Its easiest Shoal Cave room needs only Surf.
- **R5 — the Shoal Cave entries change NO species other than Snorunt.** Graded by `S3`/`S6` after regeneration.
- **R6 — an independent reviewer who re-derives the sets from the decomp gets the same lists.** The decomp sources
  are `wild_encounters.json`, `species_info.h` and `map.json` `region_map_section`. The lists are rate 14, variant 6
  (genders and percentages), pseudo per R1, legendary 21 and special {349}. **Falsifier:** any difference. That
  would mean our static ROM read or our rule differs from the decomp.
- **R7 — nothing else moves.** The full gate suite is green, and no other gate changes status. `modules/rarity.py`
  has no importer in production code: it is inert until step 8.

## WHAT THIS WILL NOT SHOW

- That any rare species is ever met, or what step 8 does with a verdict.
- That the gate table is complete. New Mauville, the Abandoned Ship, Artisan Cave, the Desert Underpass and the
  Safari Zone are UNMEASURED. Their single-location species carry `gates_unmeasured` and are decided on their
  method gates alone.
- Anything about Q5 (the gender cut), Q6 (this "LOCAL") or Q7. They stay the user's.
