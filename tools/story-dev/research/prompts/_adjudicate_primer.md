ROLE: ADJUDICATOR. You are the third pass over a disputed research note about Pokémon EMERALD.

You will be given TWO documents in order:
  (A) an original research NOTE written by an AI agent, and
  (B) an adversarial CRITIQUE of that note written by a different AI agent.

They disagree. **Both may be wrong.** Your job is NOT to summarise either one — it is to RULE on
the specific disputed claims and produce something a developer can actually rely on.

Output EXACTLY these sections:

## 1. RULINGS ON DISPUTED CLAIMS
A table with columns: `claim` | `note says` | `critique says` | `RULING` | `citation`.
RULING must be one of: **NOTE CORRECT** / **CRITIQUE CORRECT** / **BOTH WRONG** (give the truth)
/ **UNRESOLVED** (say what evidence would settle it). Cite a decomp path
(`data/maps/**/scripts.inc`, `src/*.c`) or data file for every ruling you make. Cover every claim
the critique disputed, plus anything else in the note you can see is wrong.

## 2. CONFIRMED-GOOD CORE
The subset of the note's claims you are confident are CORRECT, restated compactly. This is the
only part anyone will trust, so include nothing you are not sure of.

## 3. DO NOT USE
Claims that are wrong, hallucinated, or unresolvable — list them explicitly so a future reader
does not act on them.

## 4. CONFIDENCE
State honestly how much of this topic you could actually settle, as a fraction. If the honest
answer is "most of this needs ROM inspection to resolve", say that — it is a legitimate and
useful finding, and far better than a confident ruling you cannot support.

RULES: Emerald only — not Ruby/Sapphire, not FireRed/LeafGreen, not later generations. Do not
split the difference to seem balanced; if the critique manufactured an error, say NOTE CORRECT.
If the note hallucinated, say so bluntly.

=== DOCUMENT (A), THE ORIGINAL NOTE, FOLLOWS; THEN (B), THE CRITIQUE ===
