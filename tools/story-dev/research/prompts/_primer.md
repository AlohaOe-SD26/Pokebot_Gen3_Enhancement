CONTEXT: I am building an autonomous story-completion bot for Pokémon EMERALD (Gen 3),
driven by a libmgba emulator with full memory access. I need ROM-accurate facts, not
walkthrough prose.

HOUSE RULES FOR YOUR ANSWER — follow these exactly:
1. Cite the pokeemerald DECOMP where possible: file path (e.g. data/maps/<Map>/scripts.inc,
   src/*.c), script/label names, event-flag and event-var NAMES (e.g. FLAG_..., VAR_...).
2. Separate VERIFIED facts from INFERENCE/RECALL. Mark each claim. If you are unsure, say
   "UNSURE" — a marked gap is far more useful to me than a confident guess, because every
   claim gets machine-verified against the ROM before any code is written.
3. Give COORDINATES as local map coords where you can, and name the map constant
   (e.g. MAP_ROUTE113).
4. Emerald specifically — NOT Ruby/Sapphire, NOT FireRed/LeafGreen, NOT later remakes.
   Call out any place where Emerald differs from RS.
5. Be exhaustive and structured. Tables are good. Do not pad with narrative.
