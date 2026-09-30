# Vision & Design — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Source of truth for INTENT.

---

# ‼‼ THE NORTH STAR (user directive, 2026-08-11) — read this before anything else

Everything below serves **two** ends, and the second one is the reason the first is built the way
it is.

## 1. A bot that plays Pokémon Emerald **organically and faithfully — as if a human were playing**
Not "a bot that reaches the Hall of Fame by any means". The bot must reach it the way a person
would: walking the routes, talking to the NPCs, fighting the trainers, teaching the HMs, healing at
Centres, losing and recovering. **Faithfulness is the product, not a style preference.** This is why
`14-AGENT-PLAYBOOK.md` treats a state-write as a documented last-resort fallback that must reproduce
vanilla's exact end-state, and why "never hang / never silently derail" is a standing rule: a human
does not freeze mid-battle, and a human does not teleport.

### ⭐⭐ AND HERE IS *WHY* — THE PURPOSE, STATED BY THE USER 2026-09-18
> *“the goal is to make this bot play as human as possible (**at regular speed, not sped up**) as it
> will be an **art piece I can look at from time to time to see its progress**.”*

⇒ **THE DELIVERABLE IS SOMETHING TO WATCH, NOT SOMETHING THAT FINISHES.** That reframes three
things that had been treated as engineering preferences:
* **REGULAR SPEED IS A REQUIREMENT, NOT A FALLBACK — AND “REGULAR” MEANS ×1.** User, asked to
  confirm 2026-09-18: *“regular speed is ‘x1’ or normal speed for the actual production gameplay,
  **speed up is for dev testing** so we dont have to wait hours upon hours or even days to get
  data”*. ⇒ the carve-out is explicit and narrow: **fast-forward exists to collect DATA, never to
  play the game.**
  ✅✅ **AND THE CODE ALREADY SATISFIES THIS — VERIFIED 2026-09-18, so do not “fix” it:**
  * `modules/libmgba.py:103-104` — the emulator defaults to `_throttled = True`,
    `_speed_factor = 1`, i.e. **×1 out of the box**.
  * **ZERO speed changes exist anywhere in `sandbox-pokebot/modules/` or `plugins/`.** The only
    setter is `modules/context.py:100-105` (`emulation_speed`), driven by configuration.
  * Every unthrottle in the tree is DEV TOOLING: `tools/story-dev/story_harness.py` and the batch
    lanes (`x4_headless.py -s 0`), both via the `emulation_speed = 0` idiom.
  * ⭐ There is even a gate, `probe_gate_unthrottled.py`, whose job is to ensure dev probes ARE
    unthrottled — i.e. the project already treats “fast” as a property of the TEST HARNESS.
  ⇒ ⛔ **A future change that unthrottles production would be a VISION-LEVEL regression**, not a
  performance tweak. If runtime ever becomes a problem, the answer is not to speed up the game.
* ⛔ **SPEED/EFFICIENCY WORK IS TESTING SCAFFOLDING, NOT A PRODUCT GOAL.** The user was explicit:
  *“I know we have been figuring out the most efficient routes for this program but those are mostly
  just to be able to get to late/end game content faster for **our testing**”.* ⇒ when an
  optimisation and faithfulness conflict, **faithfulness wins** — and “this is faster” is not, by
  itself, an argument for a design.
* ⭐ **“IT TAKES A WHILE” IS ACCEPTABLE; “IT LOOKS STUPID” IS NOT.** Long training is fine. What is
  forbidden is *conspicuously unhuman* behaviour — the user's example: *“level 30s should not be
  fighting level 3-5 for xp”*. A watcher must never see the bot doing something no player would do.
  ⇒ the quality metric for training is the **level GAP between trainee and wild**, not frames spent.

## 2. A documented substrate for a FUTURE self-training AI agent

### ⭐⭐ AND THE SUBSTRATE IS *DATA*, NOT ONLY PROSE — USER DIRECTIVE 2026-09-18
> *“the bot would have as much map information as possible so it can go anywhere it can go depending
> on where in the story its at … as well as be a great resource for the **future AI pilot version of
> this program** … Remember this program is an art piece that is also **laying the foundation to help
> speed up training a ai agent** to play the game as organically as possible to be the **“v2”** of
> this art piece.”*

⇒ ‼ **THIS EXTENDS §2 IN A SPECIFIC WAY.** Until now §2 described the substrate as *documentation* —
human-language INTENT an agent could read. The user has now said the substrate also includes
**machine-readable GAME KNOWLEDGE**: where the bot can walk at each point in the story, what gates
each place, which trainers are re-fightable and what they pay.
⇒ **A generated map/traversability/trainer knowledge base is therefore not tooling — it is PRODUCT.**
It earns its keep twice: it makes this bot's routing and training look organic, and it is handed
forward to the v2 agent so that agent does not have to rediscover Hoenn by trial and error.
⚠ That is a reason to build it WELL (schema'd, regenerable, verifiable) and a reason **not** to let
it block the current bot's story progress. See `#24-mapknowledge` for the scope discipline.
The user intends to build a separate program in which **a custom AI agent trains itself to play the
game as faithfully and organically as a human would.** This repository is that project's ground
truth. That is why the documentation burden here is so much heavier than a normal bot's, and it
changes *what* must be written down:

| what must be documented | why the future agent needs it |
|---|---|
| **INTENT** — what a component is FOR, in human language | an agent can read code; it cannot recover the *purpose* a human had for it |
| **INJECTION** — how state is observed and how inputs are applied (memory reads, task/flag/var surfaces, button timing) | this is the agent's entire sensorimotor contract with the game |
| **CODE + LOGIC** — the mechanics, tied to `file:line` | so a claim can be checked rather than believed |
| **REASONING** — *why this approach and not the alternatives* | the decisions log and mistakes log are the training signal that stops the agent re-deriving dead ends |
| **WHAT WAS TRIED AND FAILED** — `08-MISTAKES.md`, refuted hypotheses, retracted findings | negative results are the scarcest and most valuable data. A future agent that only sees what worked will confidently repeat everything that did not |

‼ **THE PRACTICAL CONSEQUENCE.** A change is not "done" when the code works. It is done when a
reader — human or agent — can reconstruct *what was intended, what was observed, what was decided,
and what was rejected*, without access to this chat. That is already the Definition of Done in
`CLAUDE.md`; the north star is the reason it is worth its cost.

‼ **AND IT RAISES THE BAR ON HONESTY.** Documentation that will be used to train something must not
contain confident wrong statements. A measured result, an inference, and a guess must be
distinguishable on the page — which is why this project writes "MEASURED", "REFUTED", "UNVERIFIED"
and "n=" inline, and why retractions are recorded rather than edited away.

---

## One-liner
An enhanced, deeply documented fork of [40Cakes/pokebot-gen3](https://github.com/40Cakes/pokebot-gen3) — a Python shiny-hunting bot that drives Gen-3 Pokémon games (Ruby/Sapphire/Emerald/FireRed/LeafGreen) through libmgba — maintained in this repo with custom automations, a one-script installer, and a fully custom interface.

## Problem & purpose
The upstream pokebot-gen3 is powerful but its inner workings are only lightly
documented for developers. To enhance it confidently (and to reuse its
techniques elsewhere), we first need a complete, human-language map of what
every part does, why it exists, and where it plugs in. This project:
1. **Documents** the entire upstream codebase (intent + mechanics, tied to
   code with file:line references) under `40cakes repo/DOCUMENTATION/`.
2. **Mirrors** upstream in `40cakes repo/pokebot-gen3/` (git subtree,
   pristine, checked for upstream updates DAILY per the CLAUDE.md
   directive; sync history in `40cakes repo/UPDATE-LOG.md`, superseded
   docs snapshotted in `DOCUMENTATION/_history/`).
3. **Enhances** the bot through a THREE-STAGE flow — build in `sandbox-pokebot/`,
   promote to `custom-pokebot/` on the user's explicit OK, never touch the mirror.
   Each fork is documented in its own `DOCUMENTATION/` with every intentional
   difference from upstream tracked in its `DIVERGENCE-LOG.md`.
   (Rule: root `CLAUDE.md` §"Sandbox area". Layout: `02-ARCHITECTURE.md`.)
4. **Feeds a sibling project**: key findings useful to the separate
   "Pokémon Emerald AI" project (an AI that plays Emerald) are collected in
   `Pokemon_Emerald_AI_Notes.md` at the repo root.

## Goals
- Complete developer documentation of the upstream codebase (every module's
  intent described in human language, tied to code).
- Custom automations/bots (new bot modes beyond the stock ones).
- Easy setup/install/update script (see
  `PROJECT KNOWLEDGE/REFERENCE-INSTALLER-PATTERN.md` — Nick's
  installer-as-codebase pattern is the reference for how installers should
  feel; the final design must be reconciled with this repo being git-based).
- A total custom interface (replace/augment the stock Tkinter GUI, likely
  building on or extending the bot's HTTP API).
- Many more custom features over time (punch list is the queue).

## Non-goals (explicitly out of scope)
- Cheating beyond upstream's philosophy is not a design goal by default —
  upstream deliberately plays "as if human" (no RNG manipulation, no memory
  writes for outcomes). Deviations from this are per-feature decisions.
- Contributing back upstream is not required (we maintain our own fork),
  though clean separation of our changes keeps `git subtree pull` viable.

## Whole-program intent
A user should be able to: install the bot on a fresh Windows machine with
one script; pick a game profile; choose from stock AND custom automation
modes; watch/control everything from a modern custom interface; and trust
that the documentation explains how any part works when they want to extend
it.

## Components & their individual intent

### Upstream mirror (`40cakes repo/pokebot-gen3/`)
- **Purpose:** pristine, always-current copy of upstream (git subtree,
  remote `upstream-pokebot`, squashed; currently at `5dd898f8`).
- **Must do:** be checked against upstream daily; only change via
  `git subtree pull`.
- **Must not do / constraints:** NEVER hand-edited; never commit ROMs,
  saves, or profiles (upstream `.gitignore` covers these).

### Upstream documentation (`40cakes repo/DOCUMENTATION/`)
- **Purpose:** the human-language developer map of the ORIGINAL bot —
  per-layer docs with intent, mechanics, file:line references, plug-in
  points. `00-CODEBASE-OVERVIEW.md` is the entry point.
- **Must do:** track the mirrored commit; snapshot superseded versions to
  `_history/` before updating; log every sync in `../UPDATE-LOG.md`.

### Our promoted fork (`custom-pokebot/` + its `DOCUMENTATION/`)
- **Purpose:** the STABLE, promoted build — what we'd hand someone to run. Forked from
  upstream `5dd898f8` on 2026-07-17.
- **Must do:** log every intentional difference from upstream in
  `DIVERGENCE-LOG.md`; document only the CUSTOM parts in its
  `DOCUMENTATION/` (link to upstream docs for inherited behavior).
- **Must not do / constraints:** upstream updates are never auto-applied
  here — they're reviewed per the UPDATE-LOG ritual. **Not edited directly during a
  sandbox round** — features arrive here only by promotion, with their DIVERGENCE-LOG
  entries and docs.

### ★ The sandbox (`sandbox-pokebot/` + `SANDBOX-NOTES.md`, `SANDBOX-PROPOSALS.md`)
- **Purpose:** the EXPERIMENTAL copy where every enhancement is actually built and proven.
  **This is the default place to write code** — the two-folder mental model (mirror + fork)
  is wrong; there are three copies. Set up and launched by `install_sandbox.py`.
- **Why it exists:** enhancement rounds need somewhere to be wrong in. Keeping the promoted
  fork clean means a half-built feature can never break the build the user runs, and
  promotion becomes an explicit, reviewable act rather than a drift.
- **Must do:** carry its own `DIVERGENCE-LOG.md` + `DOCUMENTATION/`; prove changes with
  `tools/story-dev/repro_*.py` before proposing promotion; get the user's **explicit OK**
  before anything moves to `custom-pokebot/`. After promotion the sandbox is re-based on
  the new custom.
- **Constraints:** during a sandbox round, do NOT modify `custom-pokebot/` or the mirror.
- ⛔ **"IT HAS GENUINELY DIVERGED" IS FALSE AS OF 2026-08-17 — MEASURED, and the whole clause is
  retracted.** It named ten modules as sandbox-only (`endless_x4`, `tile_bridge`, `tile_mosaic`,
  `gui/tile_child`, `x4_logs`, `remote_party`, `badge_log`, `badge_case`, `battle_fault`,
  `story_milestones`) and said `story_mode.py` was "~400 lines ahead". **All ten are in BOTH
  forks and `story_mode.py` is 4,135 lines in BOTH.** `promote.py --check` reports the live drift (⛔ no digit is quoted here — run it). **A path written without a copy prefix is
  ambiguous — always prefix.**
- **‼ The bot the user actually runs is a DIFFERENT CHECKOUT on another machine.** Work
  committed here does not reach it until that machine pulls — see `04-HANDOFF.md §0a`.

### Story-Mode bot (`sandbox-pokebot/plugins/custom_modes/story_mode.py` + `modules/story/`)
- **Purpose:** a *scripted, deterministic* bot that plays Emerald from a fresh
  save through the whole story by itself (punch-list #24). Driven by observed
  game state (maps, coords, script names, flags) and hard sequences — NOT by
  learning.
- **Why it matters (its role in the bigger picture):** it is the **reference /
  scaffold for the SEPARATE "Pokémon Emerald AI" project** — an AI meant to
  learn to play the game *organically, like a human*. The Story bot provides a
  known-good, repeatable trajectory (what to do, where, in what order) and its
  documentation captures the game mechanics/map-facts/decision-points, so the AI
  project can **learn from the reference + notes to speed up its training**. The
  AI does NOT call the bot at runtime; the two never share code. "Complete the
  story unattended" is step 1; human-like behaviour is a later, separate layer.
- **Consequence for our practice:** documentation quality is a first-class
  deliverable here — capture the WHY, the game facts, and HOW they were
  discovered (recon), not just the code. Deep design + recon method live in
  `12-STORYMODE-DESIGN.md` (see its §P purpose note and §R recon playbook).

### Emerald AI notes (`Pokemon_Emerald_AI_Notes.md`)
- **Purpose:** cross-project transfer file — everything in this codebase
  useful to the separate Pokémon Emerald AI project (memory reading, input
  injection, state decoding, battle logic, headless control), written so
  that project can consume it without reading this repo.
- The Story-Mode bot (above) is the main body of that transfer: a documented
  end-to-end playthrough for the AI project to learn from.

### Endless Loop ×4 (**`sandbox-pokebot/`** `modules/endless_x4.py`, `tile_bridge`,
###   `tile_mosaic`, `gui/tile_child`, `x4_logs`, `remote_party`)
⛔⛔ **THAT CLAIM WAS FALSE AND IS CORRECTED 2026-08-17 BY MEASUREMENT.** It read *"These files exist in `sandbox-pokebot/` ONLY — none of them is in `custom-pokebot/`"*. **All ten exist in BOTH forks**, checked file by file, and `promote.py --check` reported **drift 0** *(as measured on 2026-08-17; for the live figure run it — this line is history)*. ‼ Two independent audit agents found this the same day; it had survived every doc pass since it was written. ⛔ Do not reason about the fork layout from prose — run `promote.py --check`.
- **Purpose:** a TEST INSTRUMENT, not a gameplay feature. It exists to raise the
  rate at which the Story bot produces reviewable failure data, and to guarantee
  that data covers all three starters instead of whatever the RNG happened to
  pick. Four independent story bots run at once, each looping cold starts for
  ever, tiled 2×2 inside the dashboard so a human can watch all four and hand the
  logs over.
- **Why it is watchable rather than merely fast:** the earlier headless
  endless-runs attempt was abandoned precisely because it gave the user nothing
  to see. Throughput alone was not the missing thing; OBSERVABILITY was. A
  headless `tools/story-dev/livetest.py` batch remains the faster way to generate
  logs, and both are kept on purpose.
- **Why the starter split:** starter choice changes which failures are reachable
  (Torchic has no super-effective move vs. Roxanne; the 3,011-flee livelock was a
  Treecko run). Pinning P1/P2/P3 and rolling P4 makes starter-specific bugs
  impossible to miss by luck.
- **Design constraint it must respect:** lanes are separate PROCESSES because
  `context` is a process-wide singleton. Nothing in the bot may be refactored to
  "support multiple emulators" on this feature's account — see 06-DECISIONS-LOG.

### Custom bot modes (`sandbox-pokebot/plugins/custom_modes/`, mirrored in `custom-pokebot/`)
- **Purpose:** the "custom automations" goal, delivered. Five modes exist today:
  `story_mode.py` (the centre of gravity — see above), `patrol.py` (walks a user-defined
  waypoint loop to trigger encounters — the first custom bot), `hunt_mode.py` (travel to a
  species' best wild spot, then hunt it), `living_dex_mode.py` (work a target-species list
  autonomously, #23), `macro_player.py` (replay a recorded macro frame-accurately).
- **Must do:** each is a drop-in `BotMode` — prefer this extension point over editing
  vendored files, so `git subtree pull` stays cheap.

### Party accounting (`sandbox-pokebot/modules/party_accounting.py`, new 2026-08-14)
- **Purpose:** make the bot's idea of "how big is my party" HONEST. The user identified the real
  hazard from a failing run — *no egg, but a NINJASK and a SHEDINJA*, i.e. a sixth party member
  that appeared with no catch, no menu and no bot action — and asked for detection that
  *"counts filled spaces vs empty spaces"*, kept SEPARATE from *"what the bot logged as caught"*
  (`06-DECISIONS-LOG.md` RULING D). That split is this module.
- **The three quantities, and which question each answers:** **A** `gPlayerPartyCount` answers
  CAPACITY (*is there a free slot? can a Shedinja spawn?*); **B** `len(get_party())` answers
  ITERATION and INDEXING (*what can I address?*) and can be SMALLER than A; **C** — what the bot
  believes it put there — is the bookkeeping half the user called valuable, and is **not built
  yet, on purpose**.
- **Must do:** ⛔ never let an INDEX or menu cursor derive from A — if A > B that index is out of
  range for the list the bot actually holds, and the likeliest place to discover it is mid-battle.
- **Where it stands:** **STAGE 0 — readers and a divergence log, wiring NO call site.** It exists
  to answer *"does A ever actually differ from B in a real run?"* before any decision depends on
  it. Re-pointing the capacity-shaped call sites is Stage 1 and is gated on that measurement.

### Rarity predicate (`sandbox-pokebot/modules/rarity.py` + `modules/data/emerald_rarity.json`, new 2026-09-29)
- **Purpose:** answer "is this wild Pokémon RARE?" the way the user defined it, so the catch rules can treat rare
  species differently. USER RULING 25 lifts the cap of 3 for rare, shiny and legendary species; ROSTER RULING 3 makes
  rare the duplicate exemption. RARE = legendary, Feebas, a thin encounter rate (≤ 4%), the user's "pseudo-rare"
  (one area, behind two or more HMs or a rod off the story path: Bagon, Snorunt), or the minority gender of a thin
  species (the user's male Skitty, the ULTRA tier).
- **Must do:** stay DATA. The table is generated from the ROM and gated, never hand-edited. Never raise: a verdict
  that cannot be decided is "not rare" with a note.
- **Where it stands:** built (design v2 step 7). Step 8's catch fence reads it, only with `POKEBOT_R25_RARE`. Q5, Q6 and Q7 are the
  user's to confirm.

### Trainer identity (`sandbox-pokebot/modules/story/trainer_identity.py`, new 2026-09-29)
- **Purpose:** name every trainer battle and its prize money from the game's own tables. The always-on `[TRAINER]`
  lines (design v2 step 5) make money-making measurable (RULING 26). The key-class set decides which battles may use
  healing items (RULING 27, step 6, behind `POKEBOT_R27_KEYITEMS`).
- **Must do:** carry identity and money only in the always-on lines, never a policy verdict; fail open when a side is
  unreadable, so a boss fight never loses its items to a reader bug.

### Ball top-off (`sandbox-pokebot/modules/story/stock_topoff.py`, new 2026-09-29)
- **Purpose:** keep the bot able to catch all game long (USER RULINGS 23 + 26: balls in bounded batches, the best
  ball the current shop sells, stock maintained throughout). It rides a Pokémon Center heal the story was making anyway
  ("piggyback, do not detour"): when spare balls fall to 20, it walks to that city's mart and tops off to about 30.
  At Sootopolis it rides RULING 18's League-basket visit instead, buying Ultra Balls after the basket lines; there it
  may visit for the balls alone when the basket is already complete.
- **Must do:** never spend below the floor (RULING 18's League basket stands); never change a heal when OFF, in
  `observe`, or with nothing to buy; end the heal where it would have ended (the exit tile, facing Down); never fail
  silently, and never walk into the same failure twice in a run. At Sootopolis a ball failure must never change the
  basket's outcome or skip RULING 18's walk back across the city.
- **Where it stands:** 9a (Rustboro) and 9b (the Sootopolis League-basket visit) are built behind
  `POKEBOT_R23_BALLRESTOCK` (default OFF), each live-graded. The amounts are a bounded default pending the user's Q1;
  under RULING 18's Juan-era floor, on post_hm07's wallet (₽67,466) the Sootopolis visit buys 1 Ultra Ball, and a Juan loss then drops the wallet below the ₽19,000 floor; the per-run count is unmeasured (step 14).

### Healing-kit top-off (the same module, `stock_topoff.py`, new 2026-09-29, design v2 step 10)
- **Purpose:** keep a small healing kit in the bag for the fights that matter (USER RULING 26: maintain healing items
  as well as balls). It rides the SAME visit and the SAME budget as the ball top-off. The kit is HP (4 of the best
  potion tier the mart sells, 4 being the per-battle item-use cap) plus a status cure (Full Heal ×2, else Awakening
  and Ice Heal ×1). It buys only what is MISSING, counted above RULING 18's League basket.
- **Must do:**
  - never change the ball top-off when the kit is OFF, skipped or in `observe` (step 9a byte for byte, proven over a
    16,128-state differential);
  - buy nothing unless `POKEBOT_R27_KEYITEMS=1`, because ordinary trainers would otherwise drain the kit;
  - keep balls first up to the League-dex reserve + 1;
  - never let a kit failure cost the balls, or a ball failure block the kit, unless the walk itself failed;
  - log each set by its own verdict.
- **Where it stands:** 10a (Rustboro) is built behind `POKEBOT_R26_KITTOPOFF` (default OFF), graded live 20/20 and
  reviewed. At Rustboro it turns 9a's 22 Poké Balls into 8 Poké Balls + 4 Super Potions for the same ₽4,400.
  - On the graded seed the kit was spent in the rival fight (4 uses, the cap) and did not flip that loss. Whether the
    kit pays for itself is a step 14 question.
- **10b (Sootopolis, 2026-09-30) is built behind the same flag, graded live 49/49 and reviewed**
  (`ai-research-notes/2026-09-30-kittopoff10b-GRADED.md`). The kit rides RULING 18's League-basket visit before Juan.
  - The kit and the basket buy the SAME names there (Hyper Potion, Full Heal), so the kit is bought AFTER the basket's
    lines, with its own count read after them. The basket's own check can never see a kit item.
  - Both must-dos above hold here with 9b in place of 9a. With the kit OFF, skipped or in `observe`, the visit is 9b's
    (a differential: 0 differ; live, every line of 9b's arms). A set that bought nothing logs no cost.
  - On the graded fixtures it buys 1 Hyper Potion (post_hm07's ₽22,166 after the basket, floor ₽19,000) or 1 Full
    Heal. The budget is what RULING 18's floor leaves; whether that is enough to matter against Juan is step 14's
    question.

### Damage-calculator fidelity audit (`modules/dmgaudit.py` + `tools/story-dev/audit_damage_calc.py`, new 2026-09-30, design v2 step 11)
- **Purpose:** MEASURE how far the bot's damage prediction (`calculate_move_damage_range` in
  `battle_strategies/_util.py`) strays from the damage the game really deals, BEFORE anything trusts it with a
  wanted Pokémon's life. Step 12 (weaken-to-catch) will rely on the crit maximum not KO-ing the target. It is
  measurement only; fixing the calculator is `#27-dmgcalcfix`.
- **Two halves:**
  - **M1a, offline:** a port of the decomp's damage order, checked against the calculator. It gives the worst-case
    bound the ORDER alone costs.
  - **M1b, live:** a raw `[DMGAUDIT]` log read at each turn's selection exit and the next entry, and a pure offline
    audit that pairs the reads, classifies each turn and decides the acceptance.
- **Must do:**
  - change NOTHING about a battle, flag on or off: pure memory reads, no button, no yield, no `get_battle_state()`;
  - log nothing with the flag unset;
  - never raise: a failure is one `ERR` line;
  - never discard a turn silently: every pair gets a verdict and every exclusion a named reason.
  - Every judgement lives in the audit, which is gated. A classifier bug therefore costs a re-audit, not a re-run.
- **Where it stands:** built, graded, reviewed and merged (2026-09-30; `ai-research-notes/2026-09-30-dmgcalc11-GRADED.md`), behind
  `POKEBOT_R25_DMGAUDIT` (default OFF). The recorder is inert (ON = OFF on every line) and matched every reached row of its
  pre-registered table. The calculator is MEASURED, NOT cleared: 8 clean hits against a floor of 300, all inside the
  non-crit range. The verdict is step 14's, with the flag on in both arms. `ACCEPT_MARGIN = 3` is a proposal for the
  user (the design's F8).

### Weaken-to-catch (`modules/story/weaken_catch.py` + the adapter in `story_mode.py`, new 2026-09-30, design v2 step 12)
- **Purpose:** USER RULING 25 ("implement that weaken to catch pokemon logic so it increases its catch rate"). Before
  throwing at a WANTED wild target, spend at most ONE bounded damage turn and up to three sleep/paralysis tries per battle,
  when the expected BALLS saved justify them.
- **Must do:**
  - **never KO the target while the catch is attempted.** Damage is allowed only when the target can hurt itself in
    NO way for the rest of the battle, and only while hp − X ≥ 1. (A recorded residual: after a catch is ABANDONED,
    unbounded failed flees could let a PP-exhausted target Struggle into its own recoil; see `06`.)
  - **never act on a move the game might replace:** it throws while an Encore, Torment, Disable or Imprison is in
    play, and it deals no damage against a target that knows Encore or Transform;
  - **act only in wild team/dex catch battles**, the target identified by PID;
  - **change NOTHING with the flag unset.**
- **Where it stands:** built, graded, reviewed and merged (2026-09-30), behind `POKEBOT_R25_WEAKEN` (default OFF).
  - With the flag set, stage 1 (exact-damage and status moves) almost never acts in a real run: no pinned party lead
    holds such a move. The live proof used a test lever.
  - Stage 2 (plain hits, `POKEBOT_R25_WEAKEN_CALC`) is built OFF until step 11's calculator is cleared.
  - Graded note: `ai-research-notes/2026-09-30-weaken12-GRADED.md`.

### The verification harness (`tools/story-dev/`)
- **Purpose:** the reason we can claim a fix works. It holds the FAITHFUL test harness
  (`story_harness.py`, which replicates `modules/main.py`'s loop exactly so harness
  behaviour matches the real bot), focused drivers, static-recon scripts, a committed
  `saves/` progression sampler, and **~100 `repro_*.py` reproducers and ~69 `probe_*.py`** (measured 2026-08-15; `run_gates.py` is the authority on which are STANDING gates).
- **Why it matters as INTENT, not just tooling:** the project's #1 house rule is *prove
  every fix — reproduce first, fault-inject A/B where possible*. This directory is what
  makes that rule affordable: most repros need **no emulator**, so a regression sweep is
  seconds, not a playthrough. Treat adding a repro as part of the fix, not extra credit.
- **Constraints:** run with `py -3.12` (plain `python` here is 3.9). Sweep the WHOLE suite —
  a fix that satisfies its own new repro can still break an older one's contract.
  Method: `14-AGENT-PLAYBOOK.md` §2/§2b; commands: `02-ARCHITECTURE.md` §"Testing".

### Installers (`install.py`, `install_sandbox.py` at the repo root)
- **Purpose:** the "easy setup/install/update" goal, delivered. One script, three jobs:
  install, update, heal. `install.py` targets `custom-pokebot/`; `install_sandbox.py`
  targets `sandbox-pokebot/`. Reference feel: `REFERENCE-INSTALLER-PATTERN.md`.

### Custom interface (`modules/gui/dashboard_gui.py`, `modules/web/static/custom-ui/`)
- **Purpose:** the "total custom interface" goal, delivered in both forks. The native
  dashboard is the DEFAULT window (upstream's original is behind `--classic-gui`); the
  browser dashboard is opt-in for remote viewing.
- **Design constraint:** the dashboard has **no Tk mainloop** — its event queue is pumped
  from the frame callback. See `02-ARCHITECTURE.md` for why that shapes Endless Loop ×4.

### Still future
- Further custom features as the punch list dictates; each gets a section here when built.

## Design principles & style
- Upstream code style: Python 3.12, `black` formatting — match it when
  editing vendored code.
- Documentation style: intent first ("what is this FOR"), then mechanics,
  always tied to code with `file:line` references; explain why, not just what.
- Enhancements should prefer extension points (plugins, bot modes, HTTP API)
  over invasive edits to upstream files, to keep upstream merges cheap.

## Story bot — where the intent stands (2026-08-05)

**Intent (unchanged):** a Story bot that plays Emerald from a cold start the way a person
would — faithfully, never hanging, never silently derailing — far enough to be left running.

⛔ **CORRECTED 2026-09-03 — this paragraph has now been stale by four chapters ONCE and by three chapters AGAIN, so it is the paragraph to update on every chapter that lands.** **Reality now:** the bot plays **23 of 24 story beats** and wins **all eight badges**: Littleroot → six badges → Mt. Pyre → the Magma Hideout (and out) → the Slateport submarine → the Lilycove Aqua Hideout (with the Master Ball) → the Mind Badge → the Mossdeep Space Center **and HM08 Dive** → the **Seafloor Cavern** end to end (Archie, Kyogre, the atoll escape; wired 2026-08-24) → **Sootopolis / the Sky Pillar / Rayquaza and HM07 Waterfall** (wired 2026-09-02) → **Gym 8, JUAN, and the RAIN BADGE** (wired 2026-09-03). Only **Victory Road** and the **Elite Four** remain unbuilt. ‼ *Superseded text kept for provenance:* **Reality (updated 2026-08-10 night):** it reliably reaches and beats **Winona / Gym 6** at a **52.0% cold-start finish rate** across 8 parallel lanes, and built content now runs **two chapters further**: **Mt. Pyre / the Magma Emblem** (2026-08-06) and **the Magma Hideout / Groudon** (2026-08-10, `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`, wired as Segment 15). The next unwritten beat is the **Slateport submarine**, which Maxie's defeat opens. ‼ The 52.0% figure is a Gym-6 measurement and says nothing about the two new chapters — they are graded **BINARY on their completion flags**, deliberately, because four batches at n≈30 moved the finish rate 25.0 → 33.3 → 16.1 → 28.6% and resolved nothing. **Content is verifiable; a finish rate at that sample size is not.**

**What this week actually bought.** ‼ *Written before 2026-08-06; the "no new chapters" line was
true then and is not now — **two** chapters have since shipped (Mt. Pyre, Magma Hideout), and the
Magma Hideout also brought the bot its first **Strength** support.* What the week itself bought
was that the bot's failures became *bounded and diagnosable* rather than fatal and silent:
* three battle-path hangs that each ate a whole lane are bounded (KI-45/46/47), plus one net
  covering the 32 unbounded loops that remain;
* the counter chain works end to end for the first time — it catches, trains and now *fields*
  a type counter, and a Machop has won a Norman fight;
* a full party no longer refuses a catch (`#24-pcoverflow`).

**And a correction worth keeping in the vision doc, because it shaped the design:** three
features I added made the bot measurably *worse* and were reverted behind flags. All three
REMOVED or RESTRICTED something and were justified by counting a behaviour's failures without
counting its successes. The bot's own logs print failures loudly and successes quietly, so
that asymmetry is a property of this system, not an accident. **Any future change that takes
something away must price what it takes.**
