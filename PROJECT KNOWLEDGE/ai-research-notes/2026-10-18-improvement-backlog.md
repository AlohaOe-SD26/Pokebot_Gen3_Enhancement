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

## The order (Claude's call, after the reset; re-ranked 2026-10-19 with round 2, below)

0. ✅ **DONE 2026-10-19 (`ai-agent/config.json`, pushed):** O3's interim, `keep_raw_cycles` 12 to 20, set the usual way learner
   settings change. It is the one TIME-LIMITED item: every 12 hours `prune()` deletes another cycle of A6's raw input.
1. **O3 and O4** (compress, back up), then **A1 with O1 + O6 + O7** and **P3** (the usage audit). P3 moves up because every
   saving in this file is an estimate and angle 2 contradicts A2's premise: re-rank the rest on P3's first report.
2. **A4 with N3 + P9, O5, and the stage templates (P11 + P1 + N6 + P10):** they cut what every agent and every session
   start reads, and the 53 % of context weight held by long agents, with no game code.
3. **The KB1 merge and N2 + P5** (the lookup), then **A6** and **A5**: progress accelerators built from data.
4. **A2 with R3 + N8 + R4, A3, P7, P2,** with **B1-B5, N1, N4, N10** in the lean setup (the 5.2 review's gate items too).
5. **`#28-trainer-autonomy` plus `#28-trainer-improvements`** (the learner), with **E2, O8, N11 + O9, then O2, O10**.
6. **Step 5.3, then chapters 3-4,** on **D1-D3** and **R6, R1 + R2, R5, R8 + R9, R12** (R13's rule written before any
   AI-tuner mode), with **R7, R11** during chapters 3-4.

Each step's cost is recorded in its `07` entry (P3's ledger line once it exists); re-rank when measured costs say so.

## Round 2 (2026-10-19): independent mining of the history

Four read-only notes in `2026-10-19-backlog-round2/` (angle 1 failure classes, 2 cost, 3 AI player, 4 ops). IDs are
theirs (a merged item carries each), so an item's full evidence is one lookup away. Candidates, not decisions.

- **Critic's spot checks (grep, 2026-10-19), all CONFIRMED:** `lint_docs.py:102` budgets lines only and `04-HANDOFF.md`
  is 390,563 bytes (N3); `learner.py` `load_jsonl`/`load_state` call `json.loads` with no `try` (O8); `rate_step5.py`
  `p2_reported` forces `True` on `text.startswith(P2_REPORTED)` (N8); `mode.py:104-105` `STORY_PATIENCE = 120_000`,
  `MAX_LOSSES = 3` (R1, R11); neither repro scan names `ai_player` or `ai-agent` (N10).
- ⚠ **A premise above is CONTRADICTED:** over all 980 transcripts (a context-weight proxy) evidence and log Reads are
  2.2 % and suite output 7.6 %, against `.py` source Reads 33.4 % and Bash cat/grep 36.5 % (angle 2). A2's "32-50 %" came
  from the 5.1/5.2 builders only; until P3 reconciles them, A2 rests on turns and agent-free regression.

### Folded into existing items

- **A1** + N14: a clock line, now / started / elapsed / ETA in 12-hour LA time (08 2026-09-07 misquoted it twice).
- **A4:** its `CLAUDE.md` half is DEMOTED as a cost lever (38.9 KB is under 2 % of a 600k context; angle 2 "dead
  ends"). Keep it for clarity; the lever is the handoff, punch list and README (N3 + P9).
- **B1** + R13: before any AI-tuner mode, write its fitness: progress READ FROM THE GAME plus a held-out human-likeness
  judge neither tuner nor AI can read, the leader re-graded weekly by the strict gate (08 2026-10-15, "loafing").
- **B6** + O13's probe: can `x4_headless` pin the game's seed despite KI-112? No run record holds a seed today.
- **D1** + R10: map COMPONENTS with walking-distance ties, built once; today a node is a whole map and ties break by NAME
  (`explore.py:174-203`, `goals.py:1160-1180`, recon Gap 1). UNVERIFIED that later maps share the shape.
- **E3** + O12: the System log shows an UNEXPECTED SHUTDOWN at 6:50 AM on 2026-10-17 (events 41, 6008), cause unknown:
  reword "power cut" in `#28-trainer-improvements` item 1. Update restarts are allowed 10 PM-5 AM, mid-cycle.
- **`#28-trainer-improvements` item 9** + O11: a plateau meter, "last time a strategy beat the leader by more than noise".

### A. Highest value per token

- **O3. COMPRESS the learner's raw logs instead of deleting them.** (A, TIME-LIMITED) **Evidence:** `prune()` deletes a
  cycle's raw logs every 12 hours (ai0001-ai0022 gone, ai0022 at 04:03 AM 2026-10-19), and they are A6's input; three
  `stdout.txt` went 247 MB to 7 MB (angle 4 facts 2, 5). **What:** gzip per cycle, read back, then delete; interim, no
  code: `keep_raw_cycles` 12 to 20 (about 11 GB of 79 free). **Cost / risk:** 30 lines; fault-test a kill mid-gzip.
- **O4. BACK UP the learner's data off C:.** (A) **Evidence:** `data/` (all 2,371 games) and `findings/` are git-ignored and
  exist once, on a drive 96 % full. **What:** a nightly 2-3 MB zip to another PHYSICAL disk (confirm `E:` is one), newest
  14, and a weekly snapshot committed with explicit paths from an interactive session (never by the 24/7 process).
- **O1 + O6 + O7. A session-free WATCHDOG, fed by an OPS LEDGER row per cycle.** (A; sharpens A1, B4) **Evidence:** every
  alert is a file seen only when a session runs `status`; the autostart has `RestartCount 0` and a closable `-NoExit`
  window; disk fell 81 to 58 GB in a day from outside the learner, and `cycles.jsonl` holds no time, disk or CPU to say
  why. **What:** a separate 30-minute task writes `Desktop\LEARNER-STATUS.txt` (`OK` or `NEEDS YOU: <reason>`, the disk
  slope, "restart pending") and notifies on a CHANGE only; cycle rows gain start, minutes, disk, CPU, consult seconds,
  boot and downtime. **Benefit:** a check-in costs the user a glance, not a Claude turn. **Cost:** about 80 lines.
- **O5. A NOVELTY GATE on the consult, and a rolling `DEVELOPER-NOTES.md`.** (A; sharpens C1) **Evidence:** the notes of
  2026-10-11 to 10-19 restate one message; every session start reads the 34 KB file (about 9k tokens). **What:** consult
  only when a local digest moved (top 3, wall shares, 40+ new runs), forced weekly; a repeat note is one line; keep 5
  notes; expire 3-day-old proposals; probe once if the `claude` call loads `CLAUDE.md`. **Saves:** ~1 call a day, 7k tokens.
- **O2. LONGER CYCLES, after E2.** (A, a config line) **Evidence:** in every cycle checked `runs - usable == lanes`
  (ai0034 50-38 at 12 lanes, ai0027 55-39 at 16): the cut is one game per lane per cycle, 23.7 % of 2,293 runs. **What:**
  `cycle_minutes` 720 to 1440; ESTIMATE cut share about 12 %, usable games +16 %, half the consults. **Trade:** 3 new
  strategies a day, not 6; a learner fix waits up to a day; never before E2 (a power cut would cost 24 hours).
- **P3. Commit the usage audit (`tools/usage_audit.py`), a cost line per workflow.** (A) **Evidence:** the audit behind
  "143M, 36 % of a week" is not in the repo; every saving here is an estimate. **What:** per agent calls, weight by
  category, cold re-writes, model mix, into `cost-ledger.jsonl`, cited by `07`. **Benefit:** each item becomes an A/B.
- **P11 + P1 + N6 + P10. STAGE TEMPLATES in the repo.** (A; sharpens A3, E1) **Evidence:** no workflow prompt is in the
  repo; 33 agents opened with one 1.18 MB design note; agents past 200 calls (3 %) hold 53 % of context weight; Opus-class
  agents are about 90 % of input-equivalent; LESSONS PR-1 ("fix rounds only for a FAILURE") is prose. **What:** per role a
  GOAL, READ LIST with ranges, DO-NOT-READ, STOP, RETURN CAP and the lookups (P2, N2 + P5); a WAIT RULE (background the
  long run, write E1's note, finish; hand back past about 150 calls); refix only on a verifier JSON with `all_pass: false`
  (MISSING JSON = ask a human); a MODEL per stage, moved down only after it catches a PLANTED defect (design, root cause
  and the adversarial verify stay top tier); a lint on the fields. **Risk:** the model saving is unmeasured: read the meter.
- **N3 + P9. BYTE and LINE-LENGTH budgets, and a split `ai_player/README.md`.** (A; sharpens A4) **Evidence:** spot-checked
  above; the handoff's longest line is 56,940 characters; mega-lines hid a stale line from a filtered grep (08 2026-09-01).
  **What:** `lint_docs` R8, a byte cap (handoff about 60 KB) and about 1,200 characters a line, waivers may only shrink;
  split the 514 KB README (read by 72 agents) into current and history, `prune_evidence.py` still seeing its citations
  (fault-test it). **Benefit:** a cold start from about 100k to 15k tokens. **Cost:** small.
- **N2 + P5. ONE prior-art LOOKUP before research, design or a question to the user.** (A) **Evidence:** about 10 `08`
  entries re-asked a ruled question (rule 11 is prose); `06` has 81 "USER RULING" mentions and no index; 91 % of decomp
  fetches repeat another agent's path. **What:** `RULINGS.md` (DO-NOT-REOPEN flags, linted against `06`) and a
  `facts-ledger.jsonl` (CONFIRMED needs a source, REFUTED kept, verifying TOOL, dependent code); `lookup.py` reads both.
- **P7. A QUICK unit lane and a parallel FULL lane.** (A) **Evidence:** 17 suites ran serially in 9 m 27 s, 381 s of it
  `test_check_purity` (`evidence/2026-10-16-step52reg-UNITS.txt`). **What:** `--quick` (about 25 s) per edit; `--full`
  parallel and sharded; PR-2's `regression_due.py` joins A2's runner. The full lane stays every commit's gate.
- **P2. A CODE MAP: read the function, not the file.** (A, measured by P3) **Evidence:** `story_mode.py` (7,556 lines) was
  read 549 times by 130 agents; 337 unranged Reads over 30k characters hold 22 % of Read characters. **What:**
  `codemap.py` (def, range, first docstring line) with `show <symbol>`, kept fresh by a `--check` gate.
- **N1. COUNT recurrences.** (A) **Evidence:** "broken twice belongs in a gate" (rule 6) fires only on memory: the heredoc
  rule's hook came at its sixth slip, and angle 1's table cost 25 greps over 24,000 lines. **What:** `Class:` and
  `Enforced-by:` on each new `08` entry (linted); `mistake_classes.py` lists classes with 2+ entries and no gate.
- **N4. The RETIRED-CLAIM gate, smallest form** (promotes `#24-retiredclaimgate`, open since 2026-09-03). (A) **Evidence:**
  a retracted claim survived 6+ times; one retraction took four sweeps. **What:** `WITHDRAWN: "phrase"`; any occurrence
  not near a pointer fails; fault-tested both ways. Literal survivors only; Tier 1 still owns paraphrases.
- **R3 + N8 + R4. TYPED STATUS, never a text prefix, and a run card.** (A; with A2) **Evidence:** the AI branches on
  `outcome.startswith(...)` (`brain/goals.py:558,566,2057-2099`) and 31 gate sites match those strings; the grader exempts
  a check by label prefix (spot-checked); a zero-frame no-op graded PASS (08 2026-09-02). **What:** coded outcomes with an
  AST gate on uncoded `"stuck: ..."`; a grader `Check(id, status, n, floor)` where `n < floor` is VACUOUS and fails unless
  waived; a 2 KB `run_card.json` per AI run (code, frontier, losses by fight, party PIDs, seed, digest) that only REPORTS.
- **R6. An unknown-screen DEFAULT and a SCREEN WISHLIST.** (A) **Evidence:** a menu outside `_story_menu`'s three cases
  ends the run (`brain/navigator.py:1092-1099`), as the Rustboro trader's did. **What:** a person-fair ladder (read, decline
  an unplanned yes/no, B out unless allow-listed, never A on a buy or a trade), each firing logged to a wishlist file.
  ⚠ Graded runs REPORT every firing; a default never counts as a skill.
- **R1 + R2. The AI SAVES and CONTINUES, and its memory survives a kill.** (A; proof: kill, CONTINUE, same PIDs and tile)
  **Evidence:** no skill saves (`skills/intro.py:9`); the resume file is written on a CLEAN close only (`libmgba.py:141`);
  `_Memory` is not carried (`brain/goals.py:62`); at x1 an hour is 216,000 frames. **What:** `save_game` and CONTINUE read
  by their words, saving only on a free screen (R5); one `memory.jsonl` (full lines plus deltas) stamped with play time, so
  a resume loads memory NOT NEWER than its save. UNVERIFIED first: does mGBA flush the save before a kill? No save-scum.
- **R8 + R9 (+ P13). AI-MADE STATES for repro and for the next chapter.** (A; needs R2, R3) **Evidence:** a stuck verdict
  costs the whole run again (a 59,204-frame stretch surfaced only in a 20-run sweep); a chapter-3 run from a bot save "has
  never heard DAD" (recon Gap 9). **What:** the HOST keeps the last 3 states and copies out `stuck-<code>.ss1` for
  `replay_from.py`; a passed chapter writes `checkpoints/chN-end/` (several seeds) where the next starts; one `INDEX.json`.
  **Risk:** `get_screenshot` counts as a look-ahead (`host/attribution.py:38`); each checkpoint carries a tree digest.

### B. Correctness

- **N10. The AI line gets the bot's static gates.** (B) Both repro scans skip `ai_player/` and `ai-agent/` (spot-checked),
  which hold 109 `except Exception` and 8 `while True`; pyflakes finds one harmless hit, so it starts green. Add both and
  LESSONS PL-4's bounded-loop AST rule, today's handlers recorded as ratchet debt. Cost small.
- **O8. TORN-WRITE resilience and a crash-loop breaker for the learner.** (B; with E2) No `try` on load (spot-checked), no
  fsync, and after a raise `run_agent.ps1` retries every 10 minutes forever, silently (read from code, not reproduced).
  Keep bad lines in `.bad`, a `state.json.bak`, fsync, 5 retries then `ATTENTION.md`; fault-test all three failure shapes.
- **N11 + O9. A bot update cannot silently poison a 12-hour cycle.** (B) `test_agent.py:30-31` builds parser input by
  hand; the learner pauses only after 3 EMPTY cycles (36 hours); `code_commit` moves with docs commits. A contract test of
  the REAL emitters through `parse_log`, a pause on zero parsed trainer ends, a `bot_fingerprint` to bucket rankings, and
  a 1-lane smoke game after a change. ⚠ A clone ROLLBACK is a new git verb: USER RULING first; until then, pause.
- **O10. A SENSITIVITY row for cut games (censored, not missing).** (B) 333 of the 544 cut games reached 4+ badges, and
  Treecko is cut 27 % against Torchic 21 % (about 2.7 se). `report.py` re-ranks with cut games as "at least this far" and
  prints "top-3 unchanged: yes/no". A check, not a known defect.
- **N9. REACH counters for registered hooks.** (B) Fixes and fault arms were dead because never reached (08 2026-10-14,
  09-04), which `call_census.py` cannot see. A hook at 0 over a graded sweep is loud until waived; it shows reach only.
- **N7. `check_claims.py` for lines marked `[ev: path]`.** (B, medium) A statistic republished unverified a third time (08
  2026-09-09). A marked PASS must cite evidence whose provenance digest matches its tree; unmarked lines are ignored.
- **N5. MECHANICAL first-pass mutants of changed functions.** (B) 32 of 41 hand-picked mutants turned nothing red (08
  2026-09-29). Mutate only changed functions, in the background; survivors go to the adversarial agent "to classify".
- **P4 + P6. A PINNED local decomp clone, and a PHANTOM pre-filter on it.** (B) 2,493 `gh api` decomp calls, 91 % repeats;
  `verify_knowledge.py:48` reads the moving master tip, so a check names no commit; phantom flag names ran 11-35 %. A
  gated `DECOMP_PIN`, `decomp.py`, and `prefilter_note.py`. ⚠ FOUND means the name exists, never that the claim is true.
- **R5. A FREE-SCREEN precondition.** (B) `FLAG_BADGE01_GET` flips before TM39's text and the run ends "done" mid-box
  (`mode.py:457-458`, recon Gap 4). One `settle_to_free` before "done", a post-milestone goal switch and a save.
- **R11. A DEFEAT LEDGER per named fight.** (B) `MAX_LOSSES = 3` spans chapters 1-4 (spot-checked); a person loses to a boss
  more than once. Per-fight losses, party and levels (persisted by R2) drive training and leads, graded by game counters.
- **R12. An AI KNOB REGISTRY, the prerequisite to tuning the AI.** (B; sharpens D2) About 129 constants, 15 "taste", no
  override path. `knobs.py` with range and trade; a gate that defaults equal today's literals; grader bounds never knobs.
- **R7. A GET-UNSTUCK LADDER, deploy mode only.** (B; needs R1, R3, R6) 98 goals in a row ended "stuck: ping-pong" in the
  5.2 NOHINTS arm, and a give-up exits after 33 minutes (`mode.py:471-472`). Person-fair rungs, each coded with a fault
  arm; the graded mode keeps its strict end, and a sweep fails when the last rung's rate passes a bound.

### C. Nice to have

- **R14** a static progress page for the user from a run folder (milestones in x1 time, map trail, party, the run card).
  **R15** an AI supervisor that relaunches from its save on benign exits (`host/lifecycle.py:48-60`) and stops when one
  code recurs at one frame twice. **P12** a Python `UserPromptSubmit` hook that, past about 400k of exact context, suggests
  a fresh session (C: the main chat is about 3 % of usage; hook rule S7 applies). **N12** a KI exposure table by call site
  when the bot resumes (KI-84). **N13** one `stop_runs` with a STOP file (`FrozenTree` covers the AI drivers already).

### Rejected or deferred (so nobody rebuilds them)

- **P8, evidence digests scoped to a driver's imports: REJECTED for now.** It relaxes "every evidence file names THIS
  tree" (a miss gives falsely fresh evidence), and with P7's fast full lane it saves little; `regression_due.py` stays.
- **O13, fewer control lanes and paired seeds: DEFERRED.** The ranking is plateaued and the knobs exhausted, so less
  variance buys nothing now, and the control lanes are what detect drift. Its seed probe moved to B6.
- **A "you already read this" hook: REJECTED by measurement** (11 identical re-reads in 5,909; P2 targets the real waste).
- **"Stop starting games that cannot finish": REJECTED** (each cut game becomes an idle lane; only O2 gains games).
- **O7's "prune to 2 cycles under disk pressure": REJECTED** (it deletes A6's input): compress (O3), drop lane profiles.
- **P13's bot saves as AI start states: REJECTED** (USER RULING 35, recon Gap 9); its index lives on in R8 + R9.
