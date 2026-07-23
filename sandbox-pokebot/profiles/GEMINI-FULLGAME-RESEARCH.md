# Gemini — FULL-GAME deep research commission (Pokémon Emerald story walkthrough)

> **Why this exists (user directive 2026-07-23):** the per-question relays in
> `GEMINI-PROMPTS.md` are surgical — one stuck sequence at a time. This is the opposite:
> a single **deep research** commission covering the WHOLE game start-to-Champion at the
> same bot-grade precision we currently produce chapter by chapter. Two goals: (1) test
> whether Gemini Deep Research can one-shot something this large and useful, and (2) if
> it can, re-run it periodically so mapping detail keeps getting refined ahead of the
> build frontier instead of being derived painfully at build time.
>
> **How to use:** paste **PROMPT 1** into a fresh Gemini Deep Research chat. Do NOT paste
> the standing primer from `15-ESCALATION-RESEARCH.md` first — Prompt 1 is deliberately
> self-contained, because Deep Research works best from one complete brief. If the answer
> comes back truncated or shallow in the later chapters, use **PROMPT 2** to pull the
> remaining chapters at full depth.
>
> **House rule unchanged:** everything it returns is a **LEAD, not gospel**. Every flag,
> var, coordinate and trigger gets verified against the decomp or the harness before any
> code is written. Gemini has already earned a HIGH grade once (the Ch9 relay was precise,
> cited, and corrected one of our own docs) — and has also been confidently wrong once
> (its Lavaridge answer described same-coordinate falls correctly but missed that the gym's
> chambers are joined by jump-south LEDGES, which is what actually made the maze solvable).
> Treat both outcomes as likely.

---

## PROMPT 1 — the commission (paste into a fresh Gemini Deep Research chat)

```
I need a complete, bot-grade, step-by-step walkthrough of Pokémon Emerald (USA, Gen 3),
from a fresh save through the Elite Four and Champion. Please run this as deep research
with citations.

## Who this is for (read this first — it changes what "good" means)
This is NOT for a human player. It is the specification for an automated bot that plays
Emerald faithfully and unattended: it walks the real routes, presses the real buttons,
fights the real battles, and never cheats or teleports past content. It runs on the
40Cakes/pokebot-gen3 framework (Python driving the libmgba emulator), and it reads the
game's own memory to decide what to do next.

Consequences for your answer:
- Prose like "head north and find the gym" is useless to me. "From the Poké Center door
  at (2,10), walk east along y=11 to x=9, north to (9,9), then east to (11,9) and face
  right to talk to Mr. Briney at (12,9)" is exactly right.
- I need the game's INTERNAL identifiers, because that is how the bot detects progress:
  FLAG_* and VAR_* names, EventScript_* / map-script symbols, exact map names as the
  decomp spells them, warp indices and destinations, metatile behaviours where a puzzle
  depends on them.
- Where you cannot be exact, say so plainly and say how it could be verified in-game. A
  clearly-flagged gap is far more useful to me than a confident guess. I will be checking
  your claims against the decompilation, so wrong-but-confident costs me real time.

## Priority order (most valuable first)
I have already built and validated the bot through the Heat Badge (Gym 4, Flannery in
Lavaridge Town). So:
1. **HIGHEST VALUE — everything from the Go-Goggles / Route 111 desert onward:** Petalburg
   Gym (Norman, Gym 5), Surf, Fortree (Gym 6), the Weather Institute, Mt. Pyre, Team Magma
   / Aqua hideouts, Seafloor Cavern, Mossdeep (Gym 7), Sootopolis (Gym 8), Victory Road,
   and the Elite Four + Champion. Spend most of your effort here.
2. **Still valuable — the early game (fresh save through Lavaridge).** I have this built,
   but I want it CHECKED. If you find a step I have wrong or a prerequisite I am missing,
   that is one of the most useful things you can tell me.

## The output schema I need (per chapter)
Break the game into chapters at the natural story boundaries (a gym, a major errand, a
region crossing). For EACH chapter give me:

1. **Goal** — one line: what the player accomplishes.
2. **Entry state** — where the player starts and what must already be true (flags, badges,
   HMs, key items).
3. **Ordered steps** — numbered. For each step: the action, the exact location (map name +
   tile coordinates where you can get them), the TRIGGER (talk to NPC X at (x,y); step on
   coordinate (x,y); a flag/var reaching a value; a battle won), and what it SETS.
4. **Completion flag** — the FLAG_*/VAR_* that proves the chapter is done, i.e. what a
   program should watch to know it can move on.
5. **Battles** — every mandatory battle: trainer name, their Pokémon with LEVELS and types,
   and whether the battle can be fled. Gym leaders and rivals especially — I use the levels
   to decide how much to train first.
6. **Items/HMs acquired**, where exactly, and whether they are required or optional.
7. **Gotchas** — see the next section. This is the part I care about most.

## The failure classes that actually break my bot (please hunt for these specifically)
Every one of these has cost me real debugging time. If a chapter contains one, call it out
loudly; these are worth more to me than the main step list.

- **Hidden prerequisite steps.** A step that is easy to miss and silently gates a later one.
  My worst case: in Slateport, the Oceanic Museum is blocked by Team Aqua grunts until you
  talk to Dock at Stern's Shipyard — nothing on the museum end hints at it. Where else does
  Emerald do this?
- **Maps whose layout changes at runtime.** Barriers or floors created by script rather than
  present in the map's static layout (Mauville Gym's switch puzzle does this — the walls
  only exist in the live map grid). Which later areas do the same? (I expect the Trick
  House, the ice floors, Sky Pillar — please confirm and describe the mechanic.)
- **One-way terrain.** Ledges and slopes you cannot walk back up. I need to know when a
  route is one-way, because my bot will otherwise plan a return trip that cannot exist.
  (Jagged Pass is one-way downhill into Lavaridge, for instance.)
- **Puzzle mechanics stated as rules, not as a route.** For gym/dungeon puzzles, tell me the
  RULE the puzzle runs on, not only the solution path. For example, in Lavaridge Gym: holes
  on 1F drop you to the same coordinate on B1F, geysers on B1F launch you back up to the
  same coordinate on 1F, and the chambers are joined by ledges you can only hop southward.
  Given the rule I can solve the puzzle from any position; given only a route, my bot is
  lost the moment anything knocks it off-script. Please do this for every puzzle: the
  Mossdeep warp panels, the Sootopolis ice, Sky Pillar, the Trick House, the Regi puzzles
  if you cover them.
- **NPCs that move.** For any NPC I must talk to, tell me whether they stand STILL or walk a
  patrol route. Talking to a patrolling NPC needs a completely different approach in code.
- **Forced/unavoidable battles**, including double battles triggered by two trainers seeing
  you at once, and any battle that cannot be fled.
- **Anything that can permanently strand a player** without a specific HM, item, or badge.

## Sources and citations
- For flags, vars, scripts, coordinates, warps and mechanics: the pret/pokeemerald
  decompilation on GitHub is authoritative — data/maps/<MapName>/map.json,
  data/maps/<MapName>/scripts.inc, and src/*.c. Prefer it whenever it can answer.
- For step ORDER and prerequisites: written walkthroughs (Bulbapedia's Emerald walkthrough,
  Serebii, GameFAQs).
- Cite a source for every factual claim. If two sources disagree, tell me WHY — in my
  experience the discrepancy usually IS the real mechanic (a hidden flag set by an earlier,
  easily-missed step).
- Emerald differs from Ruby/Sapphire in places. If a source is describing R/S rather than
  Emerald, say so — I need Emerald specifically.

## Format and delivery
- Organise strictly by chapter, in play order, using the schema above.
- Tables are welcome for battles and for flag lists.
- Mark every uncertain claim inline with "UNCERTAIN:" and a note on how to verify it.
- If the whole game is too much for one response, cover the chapters in the priority order
  above, go to full depth on as many as you can, and end with an explicit list of which
  chapters you did NOT cover — do not thin out the detail everywhere to fit. Depth on
  fewer chapters beats a shallow pass over all of them.
```

---

## PROMPT 2 — continuation (only if Prompt 1 came back truncated or thin)

```
Continue the Pokémon Emerald bot-grade walkthrough at the same depth and format as before.

Cover these chapters, which your previous response did not reach or covered only shallowly:
<LIST THE CHAPTERS HERE>

Same requirements as before, and to restate the two that matter most:
- Exact tile coordinates, map names, FLAG_*/VAR_*/EventScript_* identifiers, and the
  trigger for every step.
- For any puzzle, give me the RULE it runs on rather than just a solution route, so the
  bot can re-solve it from any position after being knocked off-script.

Cite every claim (prefer pret/pokeemerald for mechanics, walkthroughs for step order), and
mark anything uncertain with "UNCERTAIN:" plus how to verify it in-game.
```

---

## Grading the result (do this when the answer comes back)
Score it the way the Ch9 relay was scored, and record the verdict here:
1. **Spot-check 5-10 claims against the decomp** — pick ones spread across the game, and
   include at least one from a chapter we have ALREADY built (a known-answer control: if it
   gets our verified facts wrong, discount the unverified ones accordingly).
2. **Check the puzzle answers hardest.** The Lavaridge lesson is that a puzzle answer can be
   accurate about the parts a human notices and still miss the mechanic that makes it
   solvable by a program.
3. **Anything that survives verification** gets folded into `12-STORYMODE-DESIGN.md` tagged
   `✓ external-research + verified`, with the citation.
4. **Anything contradicted** gets noted here so a future run of this prompt is graded with
   its known weak spots in view.

### Run log
| date | model / mode | chapters covered | grade | notes |
|------|--------------|------------------|-------|-------|
| (pending) | Gemini Deep Research | — | — | first full-game attempt, commissioned 2026-07-23 |
