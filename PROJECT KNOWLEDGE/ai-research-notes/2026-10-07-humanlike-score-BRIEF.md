# Decision brief for 2026-10-07: what should "human-like play" score?

> **For the user.** Read this before 2026-10-07. Answering the questions in §3 is the FIRST step of `#28-aiagent-v2`.
> The learner keeps collecting every signal below until then, and its raw logs are kept, so any answer can be
> applied to all past games.
> Background: USER RULING 32 (`06`); the numbers come from `2026-10-03-human-reference-NOTE.md`.

## 1. Why this needs a decision

- Today the learner ranks strategies by PROGRESS only: badges, the Elite Four and the Champion, out of 13. On its
  own that rewards speed, which goes against the goal.
- The learner already MEASURES human-like play beside it, and flags strategies that catch or explore less than
  baseline. But how much each signal counts against a badge is a judgment about what "playing like a person" means.
  That judgment is the user's.

## 2. Where the bot stands (step 14, 62 scored games)

| | the bot (median) | a typical person (Gemini estimate, unverified) |
|---|---|---|
| Pokédex owned at the end | 18.5 (Champion games: 21) | 65-95 at the Champion |
| species caught all game | 9.5 | (included in the row above) |
| team level at Tate & Liza (their Pokémon: Lv 41-42, verified) | about 33 | 37-43 |
| Champion reached | 11 of 62 | (most people finish) |

The bot's biggest reasons for passing up new species:
- too few Poké Balls, about 23 times a game;
- party slots reserved for key Pokémon, about 14;
- a training grind in progress, about 4.5.

## 3. The questions (plain English; any answer is fine)

1. **Progress vs. a full Pokédex.** Say one strategy reaches the Champion 25% of the time and catches 15 species,
   and another reaches it 20% of the time and catches 40. Which is better?
   - (a) the first: finishing matters most;
   - (b) the second: playing like a person matters more;
   - (c) it depends: tell me your trade-off, e.g. "one badge is worth about N species".
2. **How many species should it aim for by the Champion?** A casual person owns about 65-95.
   - (a) casual (about 60-80);
   - (b) keen (about 100+);
   - (c) no target, just "more is better up to a point".

   (Gemini warned that catching EVERYTHING on every route looks robotic, not human.)
3. **Training.** Should it train to roughly the gym leader's level before challenging, as most people do, even
   though that is slower?
   - (a) yes;
   - (b) only after losing;
   - (c) let the learner decide by results.
4. **Speed.** Should a faster game ever count as better, or should time not count at all, provided it doesn't
   waste time obviously?
5. **Human habits.** Which of these should it copy on purpose later?
   - leaning on the starter, plus one weak Pokémon kept only for field moves;
   - walking back to a Pokémon Center to heal;
   - fighting most optional trainers;
   - picking up visible items;
   - preferring favourite Pokémon over the "best" ones.
6. **Items.** Should picking up the items you can see on the map count toward the score? It is not measured well
   yet; adding it is a few hours' work.

## 4. Three ways to build the score (the coordinator's recommendation is B)

- **A. Progress first, with a human-likeness floor.** Rank by progress, but disqualify any strategy that catches
  or explores clearly less than baseline. Simple, but it still rewards speed above the floor.
- **B. One combined score (recommended to start).** For example: 50% progress, 35% Pokédex owned against the target
  from Q2, 15% team level against the boss's level.
  - The weights come straight from Q1-Q3, and are easy to explain and re-weight later.
- **C. Closeness to a person, milestone by milestone.** At each badge, compare the Pokédex size and team level with
  the human ranges, and reward being INSIDE the range, neither under nor over.
  - This is the most "human" option, but it leans on Gemini's ranges, which are estimates. Verify them first, with
    more sources or the user's own playthroughs.

## 5. What follows once you answer

1. The coordinator encodes the score in `ai-agent/brain.py` and gates it in `test_agent.py`.
2. The learner re-scores every past game from its kept logs.
3. Knobs then go where this brief points, the biggest catch levers first:
   - a ball-purchase / restock policy beyond Rustboro;
   - relaxing the "runway" party-slot reserve;
   - a pre-gym training target.
   Each one is a story-bot change with its usual proof.
