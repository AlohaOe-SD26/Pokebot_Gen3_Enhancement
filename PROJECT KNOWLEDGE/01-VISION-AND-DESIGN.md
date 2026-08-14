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

## 2. A documented substrate for a FUTURE self-training AI agent
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
- **‼ It has genuinely diverged.** `sandbox-pokebot/` holds ten modules that do not exist
  in `custom-pokebot/` at all (`endless_x4`, `tile_bridge`, `tile_mosaic`, `gui/tile_child`,
  `x4_logs`, `remote_party`, `badge_log`, `badge_case`, `battle_fault`, `story_milestones`),
  and its `story_mode.py` is ~400 lines ahead. **A path written without a copy prefix is
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
‼ These files exist in **`sandbox-pokebot/` ONLY** — none of them is in `custom-pokebot/`.
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

### The verification harness (`tools/story-dev/`)
- **Purpose:** the reason we can claim a fix works. It holds the FAITHFUL test harness
  (`story_harness.py`, which replicates `modules/main.py`'s loop exactly so harness
  behaviour matches the real bot), focused drivers, static-recon scripts, a committed
  `saves/` progression sampler, and **52 `repro_*.py` regression reproducers**.
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

⛔ **CORRECTED 2026-08-13 — the paragraph below was stale by four chapters.** **Reality now:** the bot plays **20 of 24 story beats**, winning **seven badges** and running Mt. Pyre → the Magma Hideout (and out) → the Slateport submarine → the Lilycove Aqua Hideout (with the Master Ball) → the Mind Badge → the Mossdeep Space Center **and HM08 Dive**. The **Seafloor Cavern** is driven through Room 3 in the harness but is **not yet a wired chapter**. ‼ *Superseded text kept for provenance:* **Reality (updated 2026-08-10 night):** it reliably reaches and beats **Winona / Gym 6** at a **52.0% cold-start finish rate** across 8 parallel lanes, and built content now runs **two chapters further**: **Mt. Pyre / the Magma Emblem** (2026-08-06) and **the Magma Hideout / Groudon** (2026-08-10, `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`, wired as Segment 15). The next unwritten beat is the **Slateport submarine**, which Maxie's defeat opens. ‼ The 52.0% figure is a Gym-6 measurement and says nothing about the two new chapters — they are graded **BINARY on their completion flags**, deliberately, because four batches at n≈30 moved the finish rate 25.0 → 33.3 → 16.1 → 28.6% and resolved nothing. **Content is verifiable; a finish rate at that sample size is not.**

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
