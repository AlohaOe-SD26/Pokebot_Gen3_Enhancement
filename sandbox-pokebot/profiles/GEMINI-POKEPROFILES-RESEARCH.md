# Gemini — #24-tms / #24-pokeprofiles research commission (TM registry + battle profiles)

> **Why this exists (user directive 2026-07-23):** kick-start the two knowledge-layer
> punch-list items — #24-tms (TM acquisition/allocation) and #24-pokeprofiles (per-species
> battle profiles) — with a Gemini Deep Research pass BEFORE the in-house overnight
> research program runs, so that program starts from a graded head start instead of zero.
> Results also feed the sibling Pokémon Emerald AI project's reference layer.
>
> **How to use:** TWO prompts, in order. Paste PROMPT 1 (primer) into a fresh Gemini chat,
> wait for "Ready", then send PROMPT 2 as the Deep Research task. Two prompts on purpose:
> Deep Research quality drops when framing and task compete in one message, and the primer
> keeps the chat usable for follow-up questions after the report lands.
>
> **House rule:** results are LEADS, not gospel. Our own ROM-extracted data
> (`modules/data/`: learnsets, TM/HM compatibility, stats, evolutions) machine-checks every
> acquisition claim — that is this commission's known-answer control, and it makes grading
> sharper than the story-mapping one. Judgment claims (move choices, tiers) are graded
> against Smogon RSE in-game analyses + play sense.

---

## PROMPT 1 — Primer (paste first, wait for "Ready")

```
You are a research assistant helping build a faithful, automated Pokémon Emerald
story-mode bot. This chat is dedicated to one research program: building BATTLE
PROFILES for every Pokémon obtainable in Emerald, plus a full TM/HM/tutor resource
registry — the knowledge layer the bot will use to train its team properly, teach
the right moves, and battle effectively.

## The project (context you need)
- The bot plays Pokémon Emerald (USA, Gen 3) from a fresh save toward the Champion,
  unattended and FAITHFULLY — it does what a legitimate human player does: catches its
  team in the wild, trains in grass, buys what it can afford, teaches moves via the
  real menus. No cheats, no trading, no PvP. It runs on the 40Cakes/pokebot-gen3
  framework (Python driving the libmgba emulator) and reads game memory directly.
- The profiles you help build serve TWO consumers: (1) this bot's decision layer —
  which mon to invest in, which TM goes to whom, when to evolve; (2) a sibling
  "Pokémon Emerald AI" project that will use the same profiles as its reference layer.
- IMPORTANT — what I already have, so do NOT spend effort reproducing it: the bot's
  data files already contain every species' full level-up learnset, TM/HM
  compatibility table, base stats, types, and evolution data, extracted from the ROM.
  What I need from you is JUDGMENT and SOURCING, not raw tables: which moves are
  actually WORTH using in a story run, in what order, obtained from where, and why.

## Gen 3 ground rules (get these right — they change every recommendation)
- The physical/special split is BY TYPE, not by move: Normal/Fighting/Flying/
  Ground/Rock/Bug/Ghost/Poison/Steel are physical; Fire/Water/Grass/Electric/
  Psychic/Ice/Dragon/Dark are special. A high-Attack mon wants physical-TYPE moves.
- TMs are SINGLE-USE in Gen 3. A contested TM (e.g. TM26 Earthquake) is a real
  allocation decision — flag every TM that more than one plausible team member wants.
- HMs are infinite-use but can't be forgotten without the Lilycove Move Deleter.
  An HM on a battler is a semi-permanent slot tax — factor that into movesets.
- Emerald specifics matter: Emerald's move tutors (and which are one-time vs
  repeatable), Emerald mart stock, the Mauville Game Corner TMs, Battle Frontier
  BP tutors (post-game — note them but don't build plans around them).
- This is a STORY run: no EV/IV/nature optimization, no breeding, no held-item
  metagame. "Best" means: efficient, reliable damage and utility for in-game
  trainer/gym/E4 battles, obtainable at the story phase where it's needed.

## What I need in every answer
1. Concrete recommendations with the REASONING (why this move over that one).
2. Acquisition detail for every recommended move: level-up (level), TM number +
   exactly where/when that TM is obtained in Emerald (and whether it's one-time),
   HM, or tutor (which tutor, where, one-time?).
3. Story-phase awareness: what the moveset looks like at Gym 3, at Gym 6, at the
   E4 — not just the final state.
4. A CITATION for factual claims — Bulbapedia / Serebii / Smogon's RSE in-game
   analyses for judgment calls; the pret/pokeemerald decomp for game-internal facts.
5. Explicitly flag anything UNCERTAIN, and anything where Emerald differs from
   Ruby/Sapphire or FR/LG (a frequent source of wrong TM locations).

Reply "Ready" and I will send the research commission.
```

---

## PROMPT 2 — the Deep Research commission

```
Run this as deep research. Three deliverables, in priority order. If depth forces a
cut, cut from the END of deliverable C's species list — never thin all three out.

## A. The Emerald TM/HM/tutor REGISTRY (the resource map)
For every TM01–TM50 and HM01–HM08 in Pokémon EMERALD specifically, and every move
tutor available during the main story:
- The move it teaches; where/how it is obtained (gym reward, ground item + location,
  mart + price, Game Corner + coin cost, tutor + location); the earliest story phase
  it's available (before which badge); whether it is one-time or repeatable.
- A one-line verdict for a story run: "core — save it for X", "situational", or
  "skip". For every ONE-TIME TM that multiple common team members want, name the
  contention explicitly (e.g. who else competes for TM26 Earthquake).
Present as a table. Cite the location claims — TM locations are where R/S vs
Emerald mix-ups are most common, so verify against Emerald sources.

## B. The PRIORITY TIER LIST (which mon deserves investment)
Considering ONLY Pokémon realistically obtainable in a solo-cartridge Emerald story
run (no trades, no events), tier the viable STORY-TEAM candidates:
- S/A tier: carries the run (e.g. the starters, early powerhouses worth full TM
  investment). B: solid contributor. C: usable filler. Then a separate list:
  "HM-mule tier" — mons whose job is carrying Cut/Rock Smash/Strength/Surf etc.
  with minimal team cost (e.g. Zigzagoon/Linoone), noting which HM sets each can
  cover simultaneously.
- For each S/A-tier entry: WHY (stats + movepool + availability timing), where/when
  it's caught, and the single biggest weakness the bot should plan around.
Keep this to the ~25–40 mons that actually matter for team-building decisions; the
rest can be a one-line "not worth story investment" sweep by family.

## C. FULL BATTLE PROFILES — Batch 1 (the early-game roster)
Full per-species profiles for these evolution LINES (the ones the bot actually
catches and uses before/around Gym 3 — final forms included):
  Treecko / Torchic / Mudkip (all three starter lines, all stages),
  Poochyena→Mightyena, Zigzagoon→Linoone, Wurmple→Beautifly AND →Dustox,
  Taillow→Swellow, Wingull→Pelipper, Ralts→Gardevoir, Shroomish→Breloom,
  Slakoth→Vigoroth→Slaking, Abra→Kadabra (Alakazam unreachable — no trading:
  say how to plan around a Kadabra ceiling), Whismur→Loudred→Exploud,
  Makuhita→Hariyama, Marill→Azumarill, Geodude→Graveler (same trade ceiling),
  Zubat→Golbat→Crobat, Skitty→Delcatty, Oddish line (Gloom/Vileplume/Bellossom),
  Seedot→Nuzleaf→Shiftry, Nincada→Ninjask/Shedinja.

Per species (use this exact schema):
1. ROLE — sweeper / tank / support / HM mule / bench, one line on its niche.
2. TIER + investment verdict — is it worth TMs? Which ones?
3. GOAL MOVESET (4 moves) for the endgame of a story run, each move with:
   the reason it's chosen (STAB? coverage? the Gen 3 physical/special-by-type
   logic), and its acquisition (level N / TM# + source / HM / tutor + where).
4. MOVESET BY PHASE — what its 4 slots should look like around Gym 3, Gym 6,
   and the E4 (only where it differs from a straight march to the goal set).
5. EVOLUTION TIMING — evolve on schedule, or delay for an earlier move? Be
   specific ("delay Marshtomp→Swampert? No — nothing worth waiting for").
6. HM COMPATIBILITY — which HMs it can carry without ruining its battle slots,
   and whether it SHOULD.
7. GOTCHAS — anything that would trip an automated trainer: moves that sound
   good but underperform in Gen 3, ability interactions (e.g. Truant Slaking
   needs different handling), Attract/Cute Charm complications, etc.

Format: organized, tabular where it helps, citations throughout, "UNCERTAIN:" tags
on anything you couldn't confirm from an Emerald-specific source. End with an
explicit list of anything you did NOT cover.
```

---

## Grading the result (when the answer comes back)
1. **Machine-check every acquisition claim** against `modules/data/` — a small probe can
   verify "species X learns move Y at level N / via TM#Z" for the whole response
   automatically. This is the known-answer control; score the error rate.
2. **Spot-check TM locations against Emerald sources** — the flagged R/S-vs-Emerald
   confusion class. Any wrong location invalidates that row, not the registry.
3. **Judgment claims** (tiers, move choices, evolution timing): sanity-check against
   Smogon RSE in-game analyses; disagreements are discussion items, not auto-fails.
4. Fold surviving content into the future `#24-pokeprofiles` data files (format TBD when
   that item starts) and mark this file's run log.
5. Batch 2+ (post-Gym-3 catches: Electrike, Numel, Torkoal, Spoink, Trapinch, Swablu,
   Aron, Machop-via-Emerald?, Carvanha, Wailmer, Barboach, Baltoy, Sandshrew, Slugma,
   Spheal, Snorunt, Bagon, Beldum...) reuses PROMPT 2's schema with a new species list —
   generate the list from `emerald_obtainability.json` when commissioning.

### Run log
| date | model / mode | deliverables covered | grade | notes |
|------|--------------|----------------------|-------|-------|
| (pending) | Gemini Deep Research | — | — | commissioned 2026-07-23; awaiting the user's relay |
