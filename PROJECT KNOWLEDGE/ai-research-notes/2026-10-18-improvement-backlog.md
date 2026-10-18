# Improvement backlog: the AI agent, the bot tuner and the PROCESS (2026-10-18)

The user asked for improvements that make the work cheaper on usage without losing progress, results or rigor,
drawn from everything that went wrong. Each item names the EVIDENCE that motivates it, the expected benefit, the
cost and risk, and its priority.

- **Source of the numbers:** the usage audit of 2026-10-15/16, by input-equivalent tokens (`06` 2026-10-15
  "usage-safe operation"), plus this session's measurements.
- **What these are:** candidates, not decisions. Each becomes a decision (`06`) and a punch-list status when built.
- **What gets built first:** priority A items, in the lean phase right after the weekly reset.

## Where the usage actually goes (measured, so the priorities follow it)

- **About 95 % is the WORKFLOW AGENTS.** The main chat was about 3 %, and doc checks about 0.2 %.
- **Inside a builder:**
  - reading raw logs and evidence: 32-50 % of its cost;
  - writing code: 25-35 %;
  - running and waiting on suites: 15-25 %.
- **The multiplier is CONTEXT SIZE:** a builder carries about 600k tokens by mid-task and re-reads it every turn.
- **Steps cost 15-36 % of a week each:** step 5 about 60M, 5.1 about 112M, 5.2 about 143M input-equivalent.
- ⇒ The levers, in order: what agents READ, how LONG an agent lives, and how many agents a step uses.

## A. Highest value per token (build first)

**A1. A one-call STATUS script for check-ins.**
- **Evidence:** every health check this session took 3-8 tool calls, each re-reading a 300k-token chat context.
- **What:** `tools/status.py` prints one screen:
  - the learner (cycle, lanes, failures, games, the Champion trend, the consult queue, Claude reachable or not);
  - the AI player's frontier (the furthest story point reached, and when);
  - the newest evidence verdicts, disk, git sync, any in-flight workflow, and the usage estimate (the audit script,
    calibrated).
- **Benefit:** a check-in becomes one call. **Cost:** small. **Risk:** none (read-only).

**A2. SUMMARY-FIRST suites, and a regression SCRIPT.**
- **Evidence:** agents reading raw logs cost 32-50 % of a builder.
- **What:**
  - Every live, rate and revert suite also writes `<evidence>.summary.json`: the verdict, the failing checks, the key
    numbers and the tree digest, in 2 KB or less. Agents are told and tooled to read the summary, and to `grep` the
    raw log only for a named check.
  - `run_regression.py` runs every suite in the background and prints the summaries, with no agent tokens. An agent
    is called only on a failure.
- **Benefit:** an estimated -20-35 % per step. **Risk:** low, because the raw logs stay on disk.

**A3. SHORT-LIVED staged agents instead of one long builder.**
- **Evidence:** the median context is about 600k, and step 5.2's play builder made 685 turns.
- **What:** split a step into stages with fresh agents (spec, then code and unit tests, then a background sweep, then
  analysis of the summary, then a fix), each handing over through a short written note in the repo.
- **Benefit:** an estimated -20-40 %. **Risk:** context lost between stages, which the notes guard against.

**A4. SLIM documents at every session start.**
- **Evidence:** `03-PUNCH-LIST.md` is 4,400 lines and `04-HANDOFF.md` 900, both at their budgets. `CLAUDE.md` (about
  500 lines) is injected into EVERY agent, so every turn of every agent pays for it.
- **What:**
  - An archive script moves closed punch-list items and old handoff blocks into the append-only archives
    (`28-HANDOFF-ARCHIVE.md`, a punch-list archive), with a pointer line left behind. Slugs keep resolving (R-PUNCH
    rule: summarise and point, never delete).
  - Move the bot-era rules of `CLAUDE.md` (outside the managed block) into a linked `BOT-RULES.md`. Every rule is KEPT
    and only MOVED, and the move is recorded in `06`.
- **Benefit:** a smaller fixed cost on every agent turn and every cold start. **Risk:** a moved rule being missed; the
  link and the gates mitigate it.

**A5. CHAPTER RECON PACKS generated from data, not agent fan-outs.**
- **Evidence:** the chapter 3-4 recon cost about 16M (9 agents). Most of it was facts now in KB1 (species, learnsets,
  encounters) or derivable from the decomp (maps, trainers, items, flags).
- **What:** once KB1 and its next slices (trainers, items and gifts, map links, scripted events) are merged,
  `make_chapter_pack.py <chapter>` writes the pack: map links, trainers (single or double, sight, levels), items,
  gifts, the scripted events with their flags, the boss teams, and the bot's traps and levels for that chapter (from
  the bot's games, USER RULING 41). An agent is spent only on the adversarial check of the pack's load-bearing claims.
- **Benefit:** research cost per chapter falls several-fold, and the packs are re-usable for the AI's own knowledge.

**A6. EXPERIENCE RECORDS from the bot's finished games** (`#28-trainer-improvements` item 7; USER RULING 41).
- **What:** a script, not agents, over `runs.jsonl` and the batch logs. Per chapter: the team and levels at each gym,
  items used, failure points and causes, and which routes and catches mattered.
- **Benefit:** the "seasoned player" memory of a thousand playthroughs, and the largest accelerator toward the whole
  game.

## B. Correctness: making past bugs structurally impossible

**B1. A GOODHART GATE.**
- **Evidence:**
  - 5.1's errand quota equalled the grader's floor, and the AI loafed;
  - 5.2's AI uses the grader's own yield thresholds;
  - its "717 of 717 agree" was true by construction.
- **What:**
  - The grader's thresholds live in one test-side module that the AI's code may never import (an AST rule like
    `check_purity`).
  - Every graded human-likeness yield must be READ FROM THE GAME by the harness, never the AI's own report.

**B2. "Enforced" claims checked by EFFECT.**
- **Evidence:** `LESSONS.md` listed bounds as Enforced that the grader forces to PASS.
- **What:** `check_lessons` requires, for every Enforced lesson, a named mutant in a revert script that FAILS with
  the bound removed.

**B3. POSITIVE CONTROLS for every framework read the AI relies on.**
- **Evidence:** `is_waiting_for_input` stays true after `StopScript`, and it cost a failed graded sweep and a day.
- **What:** a "framework truth" suite: for each memory door the eyes use, a fixture where the true answer is known
  both ways (waiting and not waiting, in battle and not, a finished script).

**B4. ONE temp-folder factory.**
- **Evidence:** gate G5 promised cleanup, and 1,258 folders (24.3 GB) stayed behind. The agents' scratch sweeps
  bypassed the harness.
- **What:** every runner, gate copy and sweep makes its run folder through one helper that registers cleanup at
  exit, plus a sweeper of folders older than a day. A `run_units` check fails when stale AI temp folders pass a
  threshold.

**B5. PORTABLE hooks in Python.**
- **Evidence:**
  - the PowerShell hooks FAIL OPEN in the cloud (the pilot ran `git add -A --dry-run` and `git stash` unblocked);
  - their hatch prefix never reaches them (`#27-hookhatch`);
  - their parser was broken by a `# don't` comment.
- **What:** port `block-blind-git-add` and `block-commit-over-gates` to Python with `shlex`, like
  `block_destructive_git.py`, and run every hook with `python3` where PowerShell is missing.
- **Benefit:** the safety rules hold in cloud sessions too. It merges with `#27-hookhatch`.

**B6. DETERMINISM by default.**
- **Evidence:** the game reads the host clock (KI-112), so "live arms" turned out to be replays of one trajectory.
- **What:** every live arm pins the host clock and records the seed and clock in its evidence header, and the ledger
  marks a replay as a replay. Part of this exists; make it universal and gated.

## C. The bot tuner (beyond `#28-trainer-improvements` and `#28-trainer-autonomy`)

**C1. Usage-aware consults without code.**
- `config.json` is re-read every cycle, so near the weekly limit a session sets `consult.max_calls_per_day` 0 and
  back after the reset.
- Write it into the session-start checklist. The backlog cap of 2026-10-18 already avoids the wasted calls.

**C2. A CHEAP PLATEAU STOP for the bot tuner itself.**
- **Evidence:** the Champion rate was flat at 13-17 % for four weeks.
- **What:** while the bot is parked and the AI is not yet tunable, use its lanes for EXPERIENCE coverage instead of
  re-ranking tied settings: more finished games of under-covered starters and personalities, and late chapters for
  the A6 records. When the AI-player mode exists, it goes to 16 lanes on the AI (USER RULING 38).

## D. The AI player: progress per token

**D1. GENERAL SKILLS over chapter patches.**
- **Evidence:** chapter 3 alone needs double battles and passage navigation; later chapters need HMs, puzzles (the
  Mossdeep, Sootopolis and Fortree gyms), the bike and one-way ledges.
- **What:** a skill library built once, each skill with unit tests and one live proof, mapped from the bot's Area
  Atlases (which chapter needs what).
- **Benefit:** every later chapter costs less.

**D2. Personalities as DATA.** Archetype weight files (aggressive, defensive, explorer, completionist, collector …;
USER RULING 40), so a new personality is configuration, not code, and the tuner can tune it later.

**D3. A visible AI FRONTIER line.** One line in `04` and in A1's status: "AI frontier: chapter 2 (WALLY), first
reached 2026-10-14, re-proven 2026-10-16". The user measures progress by the story the AI reaches (USER RULING 41).

## E. Resilience

**E1. In-flight notes WRITTEN BY THE WORKFLOW.** Each stage of a workflow writes `PROJECT KNOWLEDGE/in-flight/<run>.md`
(stage, files touched, what to re-verify), so a dead session leaves an exact resume point without depending on the
coordinator. It complements the handoff's "if stopped mid-task" row.

**E2. Per-game recording for the tuner** (`#28-trainer-improvements` item 1): a power cut loses only the games in
progress (on 2026-10-17 it lost the whole of cycle ai0031).

**E3. Power-cut recovery:** the BIOS "restore on AC power loss" and Windows auto-login are the user's choice. The
logon autostart already worked on 2026-10-17: boot at 3:57 PM, the learner at 4:00 PM.

## The order (Claude's call, after the reset)

1. **A1** (status script) and **A4** (slim docs): the cheapest, and they cut the cost of everything after them.
2. **The KB1 merge,** then **A6** (experience records) and **A5** (chapter packs): progress accelerators built from
   data.
3. **A2 and A3** (summary-first, staged agents), in the lean setup, together with **B1-B5**. The 5.2 review's gate
   items fold in here.
4. **`#28-trainer-autonomy` plus `#28-trainer-improvements`** (the learner), with **E2**.
5. **Step 5.3, then chapters 3-4,** built on **D1-D3**.

Each step's cost is recorded in its `07` entry, and the backlog is re-ranked when the measured costs say so.
