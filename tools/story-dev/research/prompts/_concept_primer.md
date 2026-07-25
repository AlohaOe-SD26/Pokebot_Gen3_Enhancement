CONTEXT: I am building an autonomous story-completion bot for Pokémon EMERALD (Gen 3), driven by
a libmgba emulator with full memory read/write. I am designing SYSTEMS, and I need the
MECHANICAL CONSTRAINTS the ROM actually enforces — not opinions about what would be fun.

HOW TO ANSWER — this shape matters more than length:

## A. MECHANICS THE ROM ENFORCES (the valuable part)
The hard rules: formulas, caps, thresholds, RNG behaviour, flags/vars, what is checked and when.
Cite the pokeemerald decomp (`src/*.c`, `include/constants/*.h`, `data/maps/**/scripts.inc`) or
name the struct/field. Mark each claim **VERIFIED** / **RECALL** / **UNSURE**. An UNSURE is more
useful to me than a confident guess — every claim gets machine-checked against the ROM before it
becomes code.

## B. WHAT THE BOT CAN OBSERVE
For each mechanic: can a bot READ the relevant state from memory (which struct/field/flag), or
must it be inferred from observable side effects? This decides whether a strategy is even
implementable.

## C. OPTION SPACE
2-4 distinct strategies a bot could use, each with its mechanical cost, failure mode, and how the
bot would DETECT that it failed. Do not pick a favourite — I will make the architectural call.

## D. TRAPS
Ways an automated player can permanently lose value or wedge itself: irreversible actions,
one-time encounters, softlocks, resource exhaustion. Be exhaustive here; this is the section I
most need, because a bot repeats a mistake thousands of times.

RULES: EMERALD only — call out anywhere Ruby/Sapphire or FireRed/LeafGreen differ, since that is
the most common source of wrong answers about this game. Tables over prose. No filler.
