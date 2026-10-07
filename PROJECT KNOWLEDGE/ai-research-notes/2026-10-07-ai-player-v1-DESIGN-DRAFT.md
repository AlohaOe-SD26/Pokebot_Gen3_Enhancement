> DRAFT for discussion with the user (2026-10-07). Agent-synthesized from three research reports; every codebase claim cites file:line and must be verified before building.

# The AI player, v1: design draft (`#28-aiagent-v2`)

> NOTE, not a source of truth (`ai-research-notes/00-READ-THIS-FIRST.md`). The user's intent is
> `ai-agent/HUMAN-PLAY-DESIGN.md` (rulings 32-36) and `06-DECISIONS-LOG.md`; on any conflict they win.
> Inputs: report A (prior art: PokemonRedExperiments, Claude Plays Pokemon, Gemini Plays Pokemon, VPT/MimicBot),
> report B (EYES/CONTROLLER/BRAIN boundary in `sandbox-pokebot/`), report C (Claude consult design).
> The synthesizer re-read the citations below at HEAD `17a9307b`. Six of report B's line numbers were off by a few
> lines and are corrected here (table at the end of section 2). It also found one thing report B missed: the
> framework LISTENERS (section 2.2), which is the largest Ruling-35 risk in the design.

## 1. What v1 is, and is not

v1 is a **vertical slice**: a new program that starts Pokemon Emerald from New Game and, entirely by itself, plays
from the truck in Littleroot to Petalburg City. It walks, explores, battles, catches, buys, heals and talks to
people with its own code, and it reads the game the way the bot does (memory injection). It plays like a person:
it roams grass instead of spinning on one tile, it catches new species when it meets them, it picks up items it can
see, and it has a personality. When it faces a decision it cannot make (a new area, being stuck, what to do next),
it **asks Claude** through the local `claude` CLI or a file mailbox, with no API key, and it remembers the answer so it
needs to ask less over time. v1 is **not** the whole game, not a learned or reinforcement-learning agent yet, not a
replacement for the story bot (which stays parked as its teacher), and not a production build (no API key path beyond
a stub). Its real deliverables are the parts every later version stands on: the purity boundary, the eyes facade,
the controller, a world model, a navigator, a battle decider, menu and dialogue drivers, a personality, the coach,
and the measurements.

## 2. Architecture

```
 game memory --EYES (shared framework reads)--> Observation --> BRAIN (the AI's own code) --> CONTROLLER (Pad)
                                                                 |  world model / map memory      buttons, one frame
                                                                 |  navigator (roams)             per yield, every
                                                                 |  battle decider                action bounded
                                                                 |  menu + dialogue driver
                                                                 |  goal manager + PERSONALITY
                                                                 +--> CLAUDE COACH (rare, abstract plans) --> knowledge base
```

**Where the code lives (proposal; open question Q1):** a new top-level package `ai-player/`, separate from
`ai-agent/` (the teacher-side learner). One thin file `sandbox-pokebot/plugins/custom_modes/ai_player_mode.py`
registers the mode and imports only from `ai-player/`.

### 2.1 EYES: framework reads the AI may call

Only through one facade, `ai-player/eyes.py`, which builds a frozen `Observation` snapshot per decision tick. All of
these are side-effect-free memory reads (report B; lines verified):

| what | file:line |
|---|---|
| position, facing, surf/bike flags, map | `modules/player.py:248` `get_player_avatar`, `:291` `get_player_location`, `:320` `player_is_at` |
| NPCs and item balls on the map | `modules/map.py:1799` `get_map_objects`, `:1811` `get_player_map_object` |
| tiles, collision, elevation, behaviour | `modules/map.py:1742` `get_map_data_for_current_position`, `:1816` `get_map_all_tiles`, class `MapLocation` `:738` |
| warps, connections, wild tables | `modules/map.py:526` `MapWarp`, `:476` `MapConnection`, `:1885` `get_wild_encounters_for_map` |
| party / boxes / bag | `modules/pokemon_party.py:274` `get_party`, `:184` `get_party_size`; `modules/pokemon_storage.py:145`; `modules/items.py:541` `get_item_bag`, `:560` |
| flags, vars, Pokedex | `modules/memory.py:336` `get_event_flag`, `:393` `get_event_var`; `modules/pokedex.py:73` `get_pokedex` |
| battle (both sides, types) | `modules/battle_state.py:818` `get_battle_state`, `:840` `battle_is_active`, `:373` `BattleStateSide`, `:482` `BattlePokemon`, `:587` `.types` |
| opponent | `modules/pokemon.py:1536` `get_opponent` (NOT `encounter.py:124` `judge_encounter`, which is the bot's catch decision) |
| menus, text box | `modules/menu_parsers.py:170` `parse_menu`, `:191` `parse_party_menu`, `:293` `get_battle_menu`; `modules/text_printer.py:92` |
| clock | `modules/clock.py:21` `get_clock_time`; `modules/libmgba.py:258` `get_frame_count` |
| game facts (data, not logic) | `modules/data/types.json`, `moves.json` (has `effect` = `RECOIL` / `DOUBLE_EDGE` / `RECOIL_IF_MISS` for 7 moves), `species.json`, `items.json`, `event_flags/`; type chart via `modules/pokemon.py:304` `Type.get_effectiveness_against` |

Must-read before writing the facade: `PROJECT KNOWLEDGE/27-INJECTION-SURFACE.md` (the frame contract and its traps;
state can change between two yields, so the AI re-reads instead of trusting a stale snapshot).

### 2.2 CONTROLLER: buttons, frames, and the plugin seam

- **Button API** (`modules/libmgba.py`): `press_button` `:471`, `hold_button` `:478`, `is_button_held` `:485`,
  `release_button` `:492`, `get_inputs`/`set_inputs` `:459`/`:465`, bit table `input_map` `:27`. `run_single_frame`
  `:577` applies the inputs and steps one frame; `peek_frame` `:559` looks ahead without committing; save states
  `:360`/`:367`; speed `set_throttle` `:332`, `set_speed_factor` `:354`.
- **The seam:** `modules/main.py:36` `main_loop` calls `next(context.controller_stack[-1])` once per frame (`:148`),
  then `run_single_frame` (`:170`). A mode is a `BotMode` (`modules/modes/_interface.py:24`) whose `run()` (`:67`)
  yields once per frame. Plugins add modes through `modules/plugin_interface.py:13`
  `BotPlugin.get_additional_bot_modes` (example: `plugins/custom_modes/patrol.py:45`). The AI mode must also return
  True from `is_selectable_from_title_screen` (`_interface.py:53`; Story mode does so at `story_mode.py:2285`),
  because v1 starts at the title screen.
- **The AI's own Pad** (`ai-player/pad.py`): `tap(button)`, `hold(button, frames)`, `wait(frames)`, `mash_until(cond,
  max_frames)`. Every Pad action is a generator with a hard frame budget, and every press is written to the action log.

**THE LISTENER PROBLEM (not in report B; must be solved before anything else).** Every frame, before the mode runs,
`main.py:143-144` calls every framework listener (`modules/modes/__init__.py:84-110` `get_bot_listeners`), and several
of them PUSH BOT CODE that presses buttons:
- `BattleListener` (`_listeners.py:71`): on a battle it asks `bot_mode.on_battle_started` (`:108`). For a **trainer**
  battle, anything that is not a `BattleStrategy` is overridden to `BattleAction.Fight`, which runs the bot's
  `DefaultBattleStrategy` (`:110-111`, `:121-122`). So returning `BattleAction.CustomAction` (which hands battle frames
  to `run()`) works for wild battles but NOT for trainer battles. (The docstring at `_interface.py:76-78` mentions a
  `disable_default_battle_handler()` that does not exist in this tree; do not rely on it.)
- `TrainerApproachListener` (`:298`), `WhiteoutListener` (`:529`), `RepelListener` (`:468`), `PoisonListener`
  (`:497`), `PokenavListener` (`:376`), `EggHatchListener` (`:399`), `FishingListener` (`:341`),
  `SafariZoneListener` (`:573`) each push their own handlers.

Options (open question Q2): (a) **plugin-local**: the AI mode replaces `context.bot_listeners` with an AI-approved list
at start and re-applies it after every emulator reset (`main.py:132` rebuilds the list); (b) a small, documented
framework seam in `sandbox-pokebot` (for example a `BotMode` hook that lets a mode own trainer battles and opt out of
listeners), logged in `DIVERGENCE-LOG`. Recommendation: (a) for the prototype, plus the **foreign-press gate** below,
so that whichever option is chosen is measured, not assumed.

**Purity, enforced by gates (CLAUDE.md session discipline rule 6), not by prose:**
1. **Import allowlist gate** (`ai-player/gates/check_imports.py`): an AST walk of `ai-player/` and the plugin file
   fails if anything imports outside an allowlist (the EYES modules above, `modules/libmgba`, `modules/context`,
   `modules/modes/_interface`, `modules/plugin_interface`, `modules/data`). An allowlist, not a denylist, so a new bot
   module is forbidden by default. Fault test: add `import modules.map_path` and it must fail; a mention in a comment
   or docstring must not trigger it.
2. **Foreign-press gate** (instrument the ACTION, rule 7): during AI play, wrap `press_button`/`hold_button` and
   record which module issued each press. `foreign_presses` must be 0 in every acceptance run. Fault test: leave
   `BattleListener` enabled and fight a trainer; the counter must be greater than 0.

### 2.3 BRAIN: the AI's own components

**World model / map memory** (`ai-player/world.py`): per map, a grid the AI fills in as it sees it: walkable,
blocked, ledge direction, grass/water/sand (from tile behaviour), warps, NPC positions, item balls, trainers seen,
and "learned blockers" (a tile it tried to walk onto and did not move: a hidden wall, a scripted guard). It also
keeps a visit count per tile, a frontier (seen but unvisited tiles and unused warps), a wild-species-seen list per
map, and "events here" notes. It is persisted per run as JSON. The facts come from EYES; the memory and the
interpretation are the AI's.

**Navigator** (`ai-player/nav.py`, written from scratch; NOT `map_path.py`, `warp_graph.py`, `global_navigation.py`
(`:426` `navigate_to_anywhere`), `walking.py` or `higher_level_actions.py`):
- Within a map: A* over the AI's own grid, with a cost for tall grass when it is travelling (not training) and a
  cost for trainer line of sight it has learned. Between maps: a graph of warps and connections it has actually
  used, or seen, so the long-range map grows only as the AI explores.
- **Roaming, not spinning.** "Train here" means pick a grass, sand or water patch and walk *covering* paths through
  it: a random walk biased toward the least-visited tiles of the patch, with turns and occasional exits. Walking in
  place is never a training action. A spin ratio (section 7) catches regressions.
- **Stuck detection on state, not time** (report A: reward and position counters get gamed; CLAUDE.md rule 4). The
  progress signal is a change in map, a new tile, XP, a catch, an item, a flag or money. No progress for N decision
  ticks leads up a bounded ladder: re-plan, mark the tile blocked, try another frontier, back off to the last good
  map, ask the coach, then give up the goal with a written reason.

**Battle decider** (`ai-player/battle.py`), on `on_battle_started` returning `CustomAction` for wild battles (trainer
battles per Q2):
- For each usable move it scores expected damage: power x STAB x type effectiveness against the foe's live types
  (`BattlePokemon.types`, `pokemon.py:304`) x accuracy, then subtracts a **recoil** penalty (`effect` RECOIL 1/4,
  DOUBLE_EDGE 1/3, RECOIL_IF_MISS = miss chance x half of the user's HP; fractions to be verified against pokeemerald
  `battle_script_commands.c`) and weights it by its own HP. Ties within ~10% are broken at random (variety).
- Switch when the active mon is at a big type disadvantage and a party member is not. Use a Potion below a
  personality threshold. Run from wild battles it does not want (never from trainers).
- **Catch decision:** a new species triggers a catch unless balls are out. The AI weakens the foe (lower-power move,
  never a likely KO) and throws a ball, within a bounded number of turns. Catching to box when the party is full
  is normal (the game sends it to the PC).
- Its own battle menu driver reads `get_battle_menu` (`menu_parsers.py:293`) and moves the cursor itself. Not
  `battle_handler.py`, `battle_action_selection.py`, `battle_strategies/*` or `faint_chooser.py`.

**Menu and dialogue driver** (`ai-player/menus.py`): text advance (read `text_printer.py:92` state, press A, bounded),
yes/no, the start menu, party (`parse_party_menu`), the mart (buy N of an item), the Poke Center nurse, naming screens
and the clock. Every menu routine has a frame budget and a verify step ("did the cursor move / did the bag change?").

**Goal manager** (`ai-player/goals.py`): a small priority list of intents, the same vocabulary as report C's plan
steps: `explore`, `catch_new`, `pick_up_item`, `train_to(level)`, `heal`, `restock(balls)`, `advance_story(next
milestone)`, `continue_toward(map)`. Story milestones come from a data file (section 3). The personality sets the
weights.

**Personality state** (`ai-player/personality.py`): `{base, active, drift_until, favourite_species, weights, seed}`.
v1 ships the three named personalities (Catcher, Story, Trainer) as weight sets over the intents. Drift: with a small
chance each in-game hour, it switches `active` for a bounded time, then returns to `base`. The favourite species is
drawn at random from wild-catchable Emerald species at run start, and it is dormant in the slice unless that species
lives there. Everything random comes from one logged seed per run.

### 2.4 CLAUDE COACH (report C, adopted with three changes)

- **One interface:** `Coach.ask(request) -> plan | None`. Three transports, chosen by config, and the brain never
  branches on which one answered:
  - `cli` (dev default): the local `claude` CLI, built like `ai-agent/consult.py:49` `build_command`: read-only tools,
    `--max-budget-usd`, `--setting-sources user` (`:59`; it skips the project hook whose `git pull` could move HEAD),
    a timeout, and a fenced JSON reply.
  - `mailbox` (dev, async): write `ai-player/mailbox/outbox/<id>.json`; a chat session answers in `inbox/<id>.json`.
    The AI does NOT wait for it: it continues on its default and picks up the answer on a later tick.
  - `api` (production): a stub in v1, OFF unless a user key is configured, carrying the standing setup prompt later.
- **When it asks:** entering a map not in the knowledge base, a stuck ladder reaching "ask", before a boss (the rival,
  in the slice), "what next" with no forced step, a new species or item opportunity needing a detour call. **Never**
  for button presses, paths, menu steps or in-battle moves.
- **Request and response:** report C's JSON, built from the Observation. The response is a list of intents from the
  vocabulary above, never button macros. Every plan is validated against live state before use (does the map, item
  or species exist; is the step type known); invalid steps are rejected and logged.
- **Change 1 (blocking):** do not block `next()` for minutes inside the main loop. Run the CLI call on a worker
  thread while the AI stands still in a safe overworld state, yielding idle frames, with a hard timeout; on timeout
  or a bad reply, continue the current goal.
- **Change 2 (caps):** its own budget, separate from the learner's (`ai-agent/config.json` caps the learner at 2
  calls a day): `max_calls_per_day`, `max_usd_per_call`, `timeout_minutes`, all in `ai-player/config.json`. Every
  call is logged to `ai-player/data/coach_log.jsonl` (id, type, cache hit or miss, latency, exit status, accepted or
  rejected).
- **Change 3 (memory hygiene, report A on Gemini's context poisoning):** see section 4: answers are notes with
  provenance, and they are pruned.

### Report B citation corrections (verified 2026-10-07)

| report B said | actual |
|---|---|
| `main.py:34 main_loop`, `next()` at `:145` | `main.py:36`, `next()` at `:148` |
| `_on_frame_callback` set at `libmgba.py:112` | set at `:149`, called at `:604` |
| `set_throttle` `:326` | `:332` |
| `patrol.py:44 PatrolMode` | `:45` |
| `global_navigation.py:638 navigate_to_anywhere` | `:426` |
| (missing) | the framework listeners, section 2.2 |

## 3. How the bot teaches it (RULING 35)

**No bot module is imported into the play loop.** The import gate (2.2) enforces it. Teaching happens offline, as
data, through a teacher-side extractor `ai-player/teach/extract.py` that READS bot code and docs and WRITES the AI's
own knowledge files in `ai-player/knowledge/`. The extractor may import anything; the play loop may not import the
extractor.

| teacher asset | becomes | use |
|---|---|---|
| `modules/data/types.json`, `moves.json`, `species.json`, `items.json` | type chart, move table with recoil class, base stats, item effects | the battle decider and catch logic (game facts, not bot logic) |
| `ai-agent/knowledge.py:67` `BOSS_LEVELS` (from pret `trainer_parties.h`) | `bosses.json`: each boss's party levels | `train_to(level)` targets ("train to about the leader's level", pillar 3) |
| `modules/story/early_game.py` step docstrings ("STORY CONDITION" / "GOAL/END STATE", e.g. `:1438`, `:1452`) and `12-STORYMODE-DESIGN.md` | `milestones.json`: ordered story beats as `{needs flags, sets flag, where}` | the goal manager knows WHAT comes next; the AI decides HOW |
| `12-STORYMODE-DESIGN.md` Area Atlases, `tools/story-dev/maprecon.py` | optional prior hints per map (where the mart, the PC, the exits are) | allowed to seed the world model as "hearsay", which the AI marks verified only when it sees it |
| `27-INJECTION-SURFACE.md`, `14-AGENT-PLAYBOOK.md` recurring bug patterns | a traps list for the facade and the menu driver | engineering lessons, not behaviour |
| the learner's 540 scored games (`pokebot-learner/ai-agent/findings/LATEST.md`) | priors for the goal manager | buy many balls (the bot passes up about 23 species a game for want of balls: `DEX_CATCH_BALL_RESERVE = 10`, `story_mode.py:1757`); catch to box (about 14 more passed up for the party-slot reserve); train to boss level (the team is about 33 at Tate & Liza's Lv 41-42) |
| counter-examples | anti-patterns with metrics | `_story_spin` (`early_game.py:202`) is what NOT to do; `23-MEANDER-PATHING-DESIGN.md` explains why roaming raises encounter damage and trainer risk, so the AI must heal earlier |

**Demonstrations (later, low-level skills only).** Report A's best match is VPT/MimicBot: record a scripted
player's observations and button presses, then behaviour-clone. That is legitimate teaching (data, not code), but
the bot's HIGH-level behaviour is exactly what the user rejected (spinning, reserve rules, speed), so imitation would
copy bot-likeness. Rule: demonstrations may teach only motor skills (dialogue timing, menu cursor movement, door and
ledge entry, a surf mount), never what to do next. v1 does not need them, and no recorder exists today (unverified;
the bot logs events, not per-frame inputs). The AI's own action log (2.2) is the first recorder, so the AI's runs
become its own training data.

**The bot as a reference arm.** The bot plays the same slice in the harness; its time, levels and catches are the
baseline the AI is compared with (section 7), never a target to copy.

## 4. What learns, and how (realistic for an RTX 2060 6 GB)

| part | v1 | later |
|---|---|---|
| perception (EYES) | fixed code, no learning (memory reads are exact) | same |
| world model | learns per run from observation: blockers, warps, trainers; persists across runs as map knowledge | shared map knowledge across lanes |
| navigator | rules (A*, coverage roaming) | learned costs (which tiles waste time, where it gets hurt) from its own logs; small tabular or CPU models |
| battle decider | rules: type chart, STAB, accuracy, recoil | a learned move and switch scorer: a tiny model on structured features (tens of thousands of turns from its own logs), trained on CPU or the 2060; RL fine-tuning on battle-only save states once the rules plateau |
| menus and dialogue | rules with verification | stay rules (they are exact and cheap) |
| goals and personality | rules plus the knowledge base | the teacher-side learner pattern (`ai-agent/brain.py` screening plus Thompson) applied to the AI's own weights, scored by the same scorer |
| coach answers | knowledge base with provenance and TTL | fewer asks as the base fills |

Why no end-to-end RL or local LLM in v1: report A's pure-RL precedent needed 40,000+ simulated hours to reach early
Kanto and gamed its own rewards. The emulator runs about 1,030 frames a second in one clean process
(`ai-research-notes/2026-09-07-emulator-throughput-MEASURED.md`); 24 lanes together are UNMEASURED for this. A 6 GB GPU
can train small policies over structured features (party, types, HP, tile grid) comfortably, but not pixels at scale
or a useful local language model. Structured memory features (not screenshots) are what make later learning cheap.

**How Claude's answers become knowledge.** Every accepted plan is stored under its `cache_key` (map + decision type +
coarse state such as badges or dex tier) with: the question, the state summary, the answer, the transport, the time
and a confidence. It is a NOTE (the project's own rule). Its confidence rises when acting on it produced progress
within a bounded window, and falls when it led to stuck or a faint. A low-confidence entry is re-asked; an entry
that contradicts what the AI observed is retired. The store is capped per key and pruned by TTL. That is the defence
against Gemini's context poisoning, where one wrong goal entered memory and was repeated. One re-ask in 20 cache hits
catches drift (report C).

## 5. Human-likeness, built in from day one (HUMAN-PLAY-DESIGN.md)

- **Roaming (pillar 3):** training is coverage walking through a patch, never walking in place. The spin ratio is an
  acceptance metric.
- **Catching (pillar 2):** a new species is caught when first met, if a ball is available. There is no ball reserve
  rule; the AI buys balls instead (Catcher buys more). Catching when the party is full goes to the PC box. Not
  everything on every route: duplicates are skipped unless the personality says otherwise (Gemini's "completionist"
  caution).
- **Items (pillar 4):** every visible item ball (from `get_map_objects`) it can reach becomes a `pick_up_item` intent,
  ranked by detour cost. Pickups are logged, which also starts the pickup signal the learner lacks.
- **Never a speedrun:** the goal manager always interleaves explore, catch, item and train intents with story ones;
  even the Story personality takes them.
- **Personality and drift (pillar 1):** a seed-chosen base, bounded drifts, a favourite species.
- **Variety (pillar 5):** random choice among options within a tolerance of the best (moves, grass patches, routes,
  which new species to chase first), never among bad options. Two runs with different seeds must differ (section 7).
- **Plausible pacing (Q6):** small pauses, the odd look around, occasional non-optimal detours, bounded and seeded.

## 6. The v1 vertical slice: "Littleroot to Petalburg, by itself"

**Start:** a fresh boot at the title screen (development may start from saves; acceptance runs start from New Game).
**Teacher reference for the beats** (read, not called): `early_game.py` `:776` truck, `:807` clock, `:891` rival's
house, `:1013` Birch rescue and starter, `:1089` lab, `:1385` Route 103 rival, `:1433` Pokedex, `:1500` to Petalburg,
`:1521` Petalburg gym and Wally's tutorial.

**Acceptance criteria (each must hold in an acceptance run):**
1. It gets through the intro (name, gender, clock), rescues Birch and chooses a starter, by personality-weighted
   random.
2. It beats the rival on Route 103 (flag `DEFEATED_RIVAL_ROUTE103`, `early_game.py:1438`), having trained by
   roaming first.
3. It receives the Pokedex (`RECEIVED_POKEDEX_FROM_BIRCH`, `early_game.py:1452`). Verify both flag names with
   `audit_flag_names.py` before using them.
4. It catches at least **4 different species** on Routes 101-103 (stretch: 6). The candidate species come from
   `get_wild_encounters_for_map` (`map.py:1885`), never from memory or a model.
5. It heals at the Oldale Poke Center through the nurse at least once, and buys Poke Balls at least once (the Oldale
   Mart's stock conditions must be checked in the decomp).
6. It picks up at least 1 visible item ball.
7. It reaches Petalburg City and completes Wally's catching tutorial.
8. **Purity:** `foreign_presses == 0`; the import gate passes.
9. **Human-likeness:** spin ratio under 2% of training steps; no tile visited more than K times in any window (start
   K = 50, set from the bot baseline); at least M distinct tiles a training session.
10. **Never hangs:** every run ends in success or a bounded give-up with a reason, within a frame budget (start at 5x
    the bot's measured time for the same slice).
11. **Coach:** every call logged; a fault arm (the CLI killed mid-call) shows the AI continuing within the timeout.

Frequency claim: at least 6 of 8 seeded runs (2 per starter) pass 1-11. Per CLAUDE.md rule 9: drivers prove each
component correct; the 8-run batch answers "how often".

**Build order (each step proven before the next):**
0. Purity scaffolding: the plugin mode skeleton, the listener solution (Q2), both gates, each fault-tested.
1. EYES facade, `Observation`, the action log, scorer-compatible log lines (section 7).
2. Pad, then the dialogue and menu driver: the intro, yes/no, the nurse, the mart.
3. World model, then the navigator: walk to a tile, use a warp, explore the frontier, stuck ladder.
4. Battle decider: wild battles (fight, run, catch), then trainer battles.
5. Goals, personality, `milestones.json` from the extractor.
6. Coach: the `cli` transport, the knowledge base, `mailbox`; `api` stubbed.
7. Slice runs, the bot baseline arm, metrics, report.

## 7. Measurement

- **Reuse the learner's scorer.** The AI emits the SAME log lines that `ai-agent/scoring.py` already parses, so its
  games score with no new parser: catches (`CATCH_OK_RE`, `:34`), Pokedex (`DEX_RE`, `:38`), map changes (`MAP_RE`,
  `:35`), trainer results (`TRAINER_END_RE`, `:25`), money (`MONEY_RE`, `:26`), derails (`DERAIL_RE`, `:27`), starter
  (`STARTER_RE`, `:24`). Progress out of 13 and the `human_balanced` objective (`ai-agent/config.json`) then apply as
  they do to bot runs. (The heartbeat `HB_RE` `:28` names bot-specific fields; the AI emits its own heartbeat.)
- **New human-likeness metrics** (logged per run): spin ratio; distinct tiles per 1,000 steps; the most-visited tile
  count (report A's 600-revisit penalty is the precedent); catch-on-first-meet rate; balls-out events; items picked
  up; intent mix (time in explore, catch, train, story); run-to-run divergence for different seeds (the variety
  check).
- **Purity:** `foreign_presses`, import gate status.
- **Robustness:** stuck-ladder events by rung, give-ups by reason, frames per milestone.
- **Coach:** asks per hour (should fall), cache hit rate, rejected plans, cost per run.
- **Baseline:** the same numbers for the bot on the same slice, side by side.
- Rule 8: identical output from the same seed is a determinism check, not a replication; vary seeds.

## 8. Risks and mitigations (every loop bounded)

| risk | mitigation |
|---|---|
| framework listeners play for the AI (2.2) | solve before step 1; `foreign_presses` gate, fault-tested |
| bot code creeps into the AI | allowlist import gate; the extractor is the only bridge, and it writes data |
| stuck and loops (report A: every precedent looped) | progress measured on state; bounded ladder ending in a written give-up; revisit caps |
| dialogue or menu wedges | every driver routine has a frame budget and a verify step; a global watchdog on "Observation unchanged for N frames" |
| unwinnable or long battles | a turn cap; trainers can't be fled, so heal before them; whiteout handled by the AI's own dialogue driver |
| roaming raises damage (`23-MEANDER-PATHING-DESIGN.md`) | heal thresholds per personality; avoid known trainer lines when not training |
| coach hangs or costs | worker thread plus hard timeout; per-call and per-day caps; the default plan on failure; a fault arm |
| poisoned knowledge base | answers are notes with provenance, outcome-weighted confidence, contradiction retirement, TTL and caps |
| stale reads between yields (`27-INJECTION-SURFACE.md`) | re-read before every committed action; verify after it |
| CPU contention with the 24/7 learner (`config.json` `wait_if_other_bots_running: true`) | AI dev runs pause the learner; schedule acceptance batches (Q7) |
| a check that cannot fail | every gate and acceptance check gets a fault arm (rule 6); the target derives from the state reached (rule 4) |

## 9. Open questions for the user

**Q1. Where should the AI's code live?** (a) A new `ai-player/` folder plus one small plugin file in
`sandbox-pokebot` (recommended: clean separation, the gate is easy). (b) Everything inside `sandbox-pokebot/plugins`.
(c) A separate repository.

**Q2. The game framework auto-plays some things (trainer battles, trainer approach, whiteout, repel and PokeNav
messages). How strict should we be?** (a) The AI does all of them itself, the framework's helpers are switched off
from the AI's side, and nothing in the framework is edited (recommended for v1). (b) The same, but with a small
documented change in the sandbox framework to make switching off cleaner. (c) Let the framework keep the pure
"dismiss a message" helpers. Under every option the AI's own code makes the battle decisions.

**Q3. Where should the first milestone end?** (a) At the Pokedex (Route 103 rival beaten). (b) At Petalburg after
Wally's catching tutorial, with at least 4 species caught (recommended). (c) After beating Roxanne (much bigger:
Petalburg Woods, Rustboro).

**Q4. Should acceptance runs start from a real New Game?** (a) Yes, always (recommended for acceptance; development
uses saves). (b) From a save just after the intro, to skip naming and the clock.

**Q5. Claude budget for the AI's development runs?** (a) A local CLI cap such as 20 calls a day at $0.50 each,
Sonnet (recommended to start). (b) The mailbox only (free, but answers arrive when a chat session reads them). (c)
Something else.

**Q6. How human should its timing look?** (a) Efficient but roaming: human choices, machine timing. (b) Add small,
bounded pauses and detours so it also LOOKS like a person playing (recommended, moderate). (c) Strongly human pacing
(slow).

**Q7. Sharing the PC with the 24/7 learner.** (a) The learner pauses whenever the AI runs (today's behaviour). (b)
Split cores, for example 16 lanes learner and 8 AI. (c) The AI runs only overnight (recommended for (b) once
acceptance batches start; (a) is fine for development).

**Q8. Personalities in v1?** (a) All three (Catcher, Story, Trainer) as weight sets (recommended: cheap, and it
exercises variety from day one). (b) Story only for now.

## 11. The user's answers to §9 (USER RULING 37, 2026-10-07): THESE WIN over §1-§10

| Q | decision |
|---|---|
| 1 code location | `ai_player/` package at the repo root, with its own entry point (`py -3.12 -m ai_player ...`). It reaches the framework ONLY through two thin adapters (eyes = memory reads, controller = buttons/frames), plus ONE thin hook file in `sandbox-pokebot/plugins/custom_modes/`. **Built from day one to become a single standalone program** that loads the ROM itself and runs as an art piece (the user's stated plan): no hard-coded paths to the bot, and everything else behind the adapters. |
| 2 framework helpers | STRICT (option a): the AI removes every listener it does not own, from its own side, and restores them on exit. The framework is NOT edited (§10.1-2). |
| 3 milestone | **v1's goal = BADGE 1 (beat Roxanne).** Milestones are per GYM BADGE, each split into CHAPTERS that are developed and accepted one at a time. Badge 1 = Ch1 intro to the Pokédex (Route 103 rival); Ch2 Oldale to Petalburg (Wally's tutorial); Ch3 Route 104, Petalburg Woods, Rustboro; Ch4 Roxanne. §6's criteria apply per chapter, extended for Ch3-4. |
| 4 acceptance start | A real New Game for OFFICIAL acceptance runs (naming and clock included). Development may use saves. |
| 5 Claude | The everyday coach is a cheaper model (Sonnet), about 20 calls a day, at most $0.50 each. The coach, or the chat agent it talks to, MAY use a few other agents to DELIBERATE, and may ESCALATE to a higher model (Opus 5.5) for supervision, correction, intervention or deliberation. Escalations are capped and logged separately. |
| 6 pacing | HUMAN pacing, but always goal-directed and never idle: it never stands still (for now). Detours are allowed: training, exploring, item collecting, gift items, fishing, later the Game Corner. |
| 7 PC sharing | The learner drops to `max_lanes` 16 (from 24) while the AI is developed; the AI's runs use the rest. |
| 8 personalities | All three (Catcher, Story, Trainer) from day one. |

## 10. Adversarial review: findings ADOPTED into this draft (2026-10-07)

> An independent reviewer opened all ~90 citations above, and every one resolves. Paths written without a folder are
> `plugins/custom_modes/story_mode.py` and `modules/modes/util/{global_navigation,walking,higher_level_actions}.py`.
> The coordinator re-verified findings 1-3 in the code (`_listeners.py:108-122`, `modes/__init__.py:109`,
> `main.py:138-166`). **Where this section and §2-§9 disagree, this section wins.**

1. **Battles.**
   - Fact: in trainer battles the framework's `BattleListener` turns anything that is not a `BattleStrategy` into
     `Fight` with `DefaultBattleStrategy`, which is bot brain (`_listeners.py:110-111`, `:121-122`). Returning a
     `BattleStrategy` still runs the bot's `fight()`.
   - ⇒ The AI mode REMOVES `BattleListener` from `context.bot_listeners` on entry and restores the original list on
     exit. It detects battles ITSELF in `run()` (battle state from memory). The Route 103 rival is the fault arm.
2. **Purity covers memory writes too, not only button presses.**
   - Fact: plugin listeners are appended automatically (`modes/__init__.py:109`). Among them, the cheats plugin
     writes memory (money, healing) and the watchdog loads save states or switches to manual.
   - ⇒ The AI mode removes every listener it does not own.
   - ⇒ The purity metric counts foreign presses, foreign memory writes and save-state loads, and all three must be
     0.
   - ⇒ An AST gate bans calls in the AI's code to `write_symbol`, `write_to_save_block`, `set_event_flag`,
     `set_event_var`, `write_bytes`, `load_save_state` and `reset`.
   - Fault-tested by turning the cheats plugin on.
3. **Give-up and crashes end the process; they never silently restart or park.**
   - Fact: when `run()` returns, a fresh mode instance starts with no limit, and an exception switches to manual
     mode (`main.py:138-166`).
   - ⇒ Giving up = a log line plus `sys.exit(code)`, and the harness has a wall-clock kill.
   - ⇒ A fault arm injects an exception and asserts the process exits.
4. **Stuck detection counts NOVELTY only:** a map or tile first seen during the current goal, a new flag, XP, a
   catch or an item. Ping-ponging through one door is not progress. Every intent has a frame budget that progress
   does not reset.
5. **Acceptance criteria that cannot pass by doing nothing:**
   - at least T training steps and at least N wild battles before `DEFEATED_RIVAL_ROUTE103`;
   - at least 1 coach plan accepted and acted on per run;
   - every milestone is named by its flag (e.g. `THANKED_FOR_PLAYING_WITH_WALLY`, `early_game.py:1535`);
   - the starter is SEEDED per run, giving 9 runs = 3 per starter.
6. **The coach:**
   - no tools: the observation is sent inline, so it is faster and cheaper, and the coach cannot read bot code and
     pass its logic back as a plan;
   - coach-wait frames are left out of the frame budget;
   - the knowledge base is FROZEN per batch, so parallel lanes never race on it;
   - every evaluation has coach-off and coach-on arms;
   - the first-entry asks are budgeted for about 15 slice maps.
7. **Perception like a person:** `eyes.py` crops tiles and objects to the on-screen view (about ±7 by ±5 tiles),
   so the AI never beelines to items it cannot see. Travel paths get seeded variation. Wild-encounter tables are
   used on the test side only.
8. **The learner does NOT pause for a single `pokebot.py`.** It only checks between 12-hour cycles and reserves one
   thread. So either stop it with `ai-agent/STOP` (up to a 12-hour lag), or lower its `max_lanes` with a
   commit (applies at the next boundary). Q7 is restated accordingly.
9. **Game facts:**
   - `RECOIL_IF_MISS` is half the damage the move would have dealt, capped at half the TARGET's max HP
     (`battle_script_commands.c:6747-6752`).
   - Oldale Mart sells Poké Balls only after `FLAG_ADVENTURE_STARTED`, so catching begins after the Pokédex.
10. **Minor:**
    - name the package `ai_player`, with a path shim;
    - Q2 option (c) is withdrawn, because its message-dismiss presses would break purity;
    - personality drift counts steps, not the in-game clock (`libmgba.py` sets no RTC source; unverified).
