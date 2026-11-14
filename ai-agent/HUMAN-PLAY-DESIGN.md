# How the Emerald AI should play: the human-play design (living document)

> **Source of truth for INTENT:** the user's own words, USER RULING 32 and USER RULING 33 in
> `PROJECT KNOWLEDGE/06-DECISIONS-LOG.md` (2026-10-03, verbatim). This file organises them into design pillars and
> records what the bot does today against each. Edit it as decisions are made; never contradict the rulings.

## How it is built (USER RULINGS 34 + 35)

- The AI version is the focus. The story bot is parked, not abandoned. Concepts move to the bot version later, only
  when the user says so.
- ⛔ **The AI PLAYS THE GAME ITSELF:** navigation, battles, menus and decisions, with no bot code in its play and no
  bot-like movement.
- **The bot is its TEACHER:** its logic, scripts and documentation teach what to do, how and why, as a head start.
  Every pillar below describes the AI player's behaviour. "Today" notes describe what the BOT does, which is useful
  as a lesson or as a counter-example, never as the AI's mechanism.
- The 24/7 learner in this folder tunes the BOT: teacher-side knowledge and a corpus of games. The AI player was
  still to be designed when this was written (`#28-aiagent-v2`; it is `ai_player/` now, and `04` has its state).

## The AI player's architecture: decisions so far (USER RULING 36, 2026-10-03)

| part | decision |
|---|---|
| **Eyes (perception)** | Read the game's MEMORY by injection, as the bot does: position, map, party, battle state, bag, flags. The user: "the ai sees the game like the bot by injection as it makes more sense". The emulator and memory-reading layer can be shared with the bot. |
| **Controller (action)** | The AI presses the BUTTONS itself through the emulator. |
| **Brain (behaviour)** | Entirely the AI's own: walking, exploring, battling, menus, decisions. NONE of the bot's pathfinding, battle strategies or menu scripts while it plays (RULING 35). The bot's logic and docs only TEACH it. |
| **Claude (coach)** | The FIRST version ASKS Claude for help. Later training versions can still consult Claude. In the FINAL version Claude is optional: **toggled on, with the user's OWN API key** supplied to the program, so anyone it is shared with uses their own Claude, and nothing depends on the user's personal setup. Current focus: how the FIRST version uses Claude. |
| **How each version reaches Claude** (ruling 36 addendum) | **Development / prototype / testing versions need NO API key.** They consult Claude through the CHAT: they write reports, logs and questions to files, which Claude reads and answers in sessions. They can also call the local `claude` CLI on this PC, as `consult.py` does today. **Only the PRODUCTION / final version requires an API key.** |
| **Setup prompt** (later) | The production version sends a standing INITIAL PROMPT with every request (the game, the AI's goals and personality, its current state, what kind of help it needs), so the user's own Claude is ready to help from its first reply. To be written later. |

Implications for the build:
- The dev and test path is the file mailbox (reports, logs, `inbox/` proposals, `DEVELOPER-NOTES.md`) plus the
  local `claude` CLI, so no key is needed.
- The production path is the Anthropic API, with the key taken from the user's config or environment, never
  hard-coded, behind a toggle that is OFF without a key. It carries the setup prompt.
- Every call on either path is capped and logged, as `consult.py` already does.

## The goal

Play Pokémon Emerald the way a PERSON does:
- the story;
- catching Pokémon along the way;
- picking up items;
- exploring;
- training sensibly;
- the Pokédex.

It should look and act as human as possible, and **never speedrun**. More Pokémon caught is always better; there
is no fixed target.

## Pillar 1: personalities

- The AI starts each playthrough with a PERSONALITY and keeps it. It may drift into another personality for a
  while, then come back to its starting one ("periodically changes personalities").
- **The first personalities:**
  - **Catcher:** catching Pokémon first.
  - **Story:** progressing the story. Even the fastest-minded "beat the game" personality never skips chances to
    earn money, collect items, stock up, train and catch.
  - **Trainer:** training first.
  - More will come (the user: "we will come up with more").
- **After the Elite Four and the Champion**, every personality turns to COMPLETING THE POKÉDEX.
- **"Favourite Pokémon":** each playthrough gets a random wild-catchable Emerald species as its favourite. From time
  to time the AI shiny-hunts it for a random while, until it gets one. This is never a laser focus; it is one more
  human trait, possibly a personality of its own.
- **How it maps onto the learner:** a personality = its own scoring weights + its own knob profile + its own
  behaviours. The learner tunes knobs WITHIN each personality. Today's single "balanced" score (half progress, half
  Pokédex) is a placeholder for one personality.

## Pillar 2: catching and the Pokédex

- The more caught, the better (no fixed target). A person catches new species when first met. Gemini cautioned
  that catching EVERYTHING on every route looks completionist, not human.
- **Today:**
  - a median 18.5 Pokédex at run end, against about 65-95 for a person (estimate);
  - the bot passes up about 23 new species a game for want of Poké Balls (`DEX_CATCH_BALL_RESERVE = 10`,
    `story_mode.py:1757`) and about 14 for its party-slot "runway" reserve.
- **Next:** buy plenty of balls at marts, as a person does (today `R23_BALLRESTOCK` restocks at Rustboro only).

## Pillar 3: training and battling

- Train to roughly the gym leader's level before challenging. Battle with TYPE advantages, both the Pokémon's
  types and the MOVES' types, and account for RECOIL damage when choosing moves.
- **Today:**
  - the team is about 33 at Tate & Liza, whose Pokémon are Lv 41-42 (verified);
  - boss mode re-fights after only a +1 top-up; the knob `POKEBOT_BOSSMODE_TOPUP` is being A/B'd;
  - type matchups exist for leads and counters (`team_policy`, `counter_hunt`);
  - the damage calculator has a known open fix, `#27-dmgcalcfix`;
  - whether recoil is weighed is UNAUDITED.
- ⛔ **Training must ROAM.** The user: "not spinning in place but running through areas that spawn pokemon like
  grass, sand or water". **Today the story bot trains and hunts with `spin()`, walking in place on one tile**
  (`modules/story/early_game.py` `_story_spin`, :202). That is a top human-likeness gap. The sandbox already has a
  `plugins/custom_modes/patrol.py` worth reading first.

## Pillar 4: exploring and items

- Explore and move like a person.
- **Pick up every visible item it can reach.**
- **Collect gift items** such as the Amulet Coin, Quick Claw and Black Glasses (many more), deciding for itself to
  go and get them.
- **Today:** visible item pickups are not well measured (a few `obtained` lines a game). A pickup signal is v2 work.

## Pillar 5: teams and the PC (added by the user, 2026-10-03)

- Use the Pokémon PC the way a person does: SWAP teams for the situation.
  - **Hunting teams** for Pokémon that flee: trap them with Arena Trap or Mean Look, and bring catch-helping moves
    (lower HP without fainting, inflict status).
  - **Legendary hunting teams.**
  - **Battle teams that counter a specific gym leader or the Elite Four.**
- ⭐ **VARIETY:** teams must make sense, but must NOT be the same every playthrough. If a Water counter is needed,
  pick a suitable Water type AT RANDOM among the sensible ones, so each run's counter team is relatively unique.
  Two runs should not look alike.
- **Today:**
  - The bot already hunts counters for bosses and can take a counter from the PC box (`counter_hunt`,
    `_counter_ladder`, box-first). KI-118 shows a type-only box pick failing; the fix is designed on `wt/boxfirst`.
  - Lead choice is a ranked pick (`team_policy.lead_rank_key`). Whether ties or near-ties are broken at random is
    UNAUDITED, and probably not, since it is deterministic by design.
  - Variety is new work: choose randomly among counters that are all good enough, never among bad ones.

## Pillar 6: optional activities (future notes)

- **Game Corner gambling,** if the AI feels like it. The user: "work in progress, more of a note for a future
  feature than a demand".

## Pillar 7: post-game (logged now, designed later)

- **Event Pokémon** (Deoxys, Jirachi, Mew, ...) need to be put in by cheating, by simulating Mystery Gift / Mystery
  Event. They are post-game content. Earlier notes: `PROJECT KNOWLEDGE/ai-research-notes/2026-09-25-dex-completability-RESEARCH.md`
  and the dex-hunt notes beside it.
- **Trade-only species** in the National Dex should appear in post-game wild spawn pools where they make sense,
  after the National Dex. First check whether vanilla Emerald already does any of this; if not, design it.
- **Trade-evolution Pokémon** (Machamp, Alakazam, ...) should be obtainable through a SIMULATED trade: a trainer who
  wants a random but possible Pokémon in exchange. Details later.

## What runs today vs this design

The 24/7 learner (`README.md`) measures and tunes the story bot's existing strategy knobs. It records progress,
Pokédex, catches, places explored, per-boss levels and catch-skip reasons for every game, and keeps the raw logs.
So every pillar above can be scored retroactively once it is designed. Nothing collected now is wasted.
