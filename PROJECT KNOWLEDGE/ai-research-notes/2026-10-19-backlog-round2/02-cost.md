# Backlog round 2, angle: COST AND SPEED OF THE DEVELOPMENT PROCESS (2026-10-19)

A NOTE, not a decision. It adds to `../2026-10-18-improvement-backlog.md` (items A1-E3 there are not repeated; where an
item sharpens one, it says which). Written read-only; no emulator, no state change.

## What was measured first (so the items follow the data)

Method: the 980 workflow-subagent transcripts of this project (`~/.claude/projects/C--Remote-Projects-Pokebot-Gen3-Enhancement/**/subagents/agent-*.jsonl`,
all workflows ever run, not only the AI-player steps). Tool calls were paired with their results; "context weight" of a
result = its characters x the tool calls the agent made AFTER it (every later turn re-reads it). A proxy, not a bill:
weights are approximate, and the window is all-time. The five small scripts live in this session's scratchpad only (P3
promotes them).

- **Concentration:** median agent 48 tool calls, p90 97. The 30 agents (3 %) with 200 or more calls hold **53 %** of the
  context weight; the top 10 (1,050 / 689 / 562 / 502 / 495 calls ...) hold 35 %.
- **What fills contexts (share of weight):** `.py` source Reads 33.4 %; Bash cat/head/tail/sed 18.7 %; Bash grep/rg 17.8 %
  (20,392 calls); suite and driver output 7.6 %; `ai_player/README.md` 6.3 %; research notes 2.9 %; evidence/log Reads
  only 2.2 %; `04-HANDOFF.md` 0.6 %; `gh api` 1.0 %.
  - Differs from the backlog's "raw logs and evidence are 32-50 % of a builder". That figure came from the 5.1/5.2
    builders; these are all workflows. Reconcile with P3 before re-aiming A2.
- **Idle cache expiry:** 357 turns in 68 agents re-wrote 50k+ tokens of context after a gap of more than 5 minutes (the
  prompt cache had expired) = 24 % of all cache-write tokens, about 6 % of all subagent input-equivalent (cache read 0.1x,
  write 1.25x, output 5x; the 1-hour cache option would shrink it).
- **Model mix:** Opus-class agents about 90 % of input-equivalent, Sonnet about 7 %, Haiku about 1 % (55 agents); average
  context about 266k tokens per top-tier turn.
- **Decomp fetching:** 2,493 `gh api ... pokeemerald` calls in 383 of 980 agents (39 %); 451 distinct paths, 251 of them
  fetched by 2 or more different agents = 2,400 of 2,625 fetches (91 %).
- **Serial test time:** `evidence/2026-10-16-step52reg-UNITS.txt`: 17 suites back to back, 04:44:10 to 04:53:37 (9 m 27 s).

## Dead ends, measured, so nobody builds them

- **A "you already read this" hook:** identical (file, range) re-reads by one agent were 11 of 5,909 Reads. The waste is
  many WINDOWS of one file, not repeats. (39 % of Reads touch a file the agent already read, at another range.)
- **Slimming CLAUDE.md as a cost lever** (backlog A4, second half): workers do not follow its session-start ritual
  (`04-HANDOFF.md` read by 106 of 980 agents, `14-AGENT-PLAYBOOK.md` by 5), and 38.9 KB is about 10k tokens, under 2 % of
  a 600k context. Keep it for clarity, not savings. Do the handoff and README first.

## Items

### P1 (A). Cut an agent at every wait over 5 minutes and at about 150 calls. SHARPENS A3
- **Evidence:** the concentration and cache-expiry numbers above. Step 5.2's play builder made 685 turns; 5.1 made about
  1,900 tool calls.
- **What:** a stage never waits inside a big context. It starts the run as a background script, writes its in-flight
  note (E1's file), and FINISHES; a fresh small stage (or the coordinator script, no agent) reads the summary. Past 150
  calls any agent writes its note and hands back. The thresholds go in the stage templates (P11) and are checked by P3's
  report (agents over 200 calls, cold re-writes).
- **Benefit:** the two biggest measured sinks (53 % of weight in 3 % of agents; 6 % in cold re-writes) with no code.
- **Cost / risk:** none to build; context lost at the cut, which the note covers.

### P2 (A). A code map: read the function, not the file. NEW
- **Evidence:** source Reads + cat/sed + grep = about 70 % of weight. `sandbox-pokebot/plugins/custom_modes/story_mode.py`
  (7,556 lines) was read 549 times by 130 agents; `early_game.py` is 10,226 lines; `goals.py` 2,473; `live_step3.py`
  3,622. 1,503 Reads had no offset/limit; the 337 of those over 30k characters hold 22 % of all Read characters.
- **What:** `tools/codemap.py` writes a short `CODEMAP.md` per big file (class/def, line range, first docstring
  sentence) and `codemap.py show <symbol>` prints just that body with line numbers. A `--check` gate (like
  `extract_knowledge.py --check`) keeps it fresh. Stage templates (P11) say "map first, then Read the range".
- **Benefit:** the pool it addresses is about 70 % of weight; the saving is the share of it the map avoids, which P3
  measures before and after. **Cost:** about 150 lines. **Risk:** a stale map, closed by the gate.

### P3 (A). Commit the usage audit as `tools/usage_audit.py` and run it after every workflow. NEW
- **Evidence:** the audit behind "143M, 36 % of a week" is not in the repo (`grep` finds it only quoted in 06/07 and the
  backlog). This session re-derived every number above in minutes from the transcripts. The backlog's savings
  ("-20-35 %", "-20-40 %") are estimates.
- **What:** one script: per agent calls, context weight by category (Read source / docs / cat / grep / suite),
  cold re-writes, model mix, the 10 heaviest Reads; one line per workflow appended to
  `PROJECT KNOWLEDGE/cost-ledger.jsonl`, plus the stage name. The 07 entry cites that line instead of a hand total.
- **Benefit:** every other item becomes an A/B (project rule 9); waste shows up the day it starts. **Cost:** small.
  **Risk:** none (read-only on transcripts, which stay local).

### P4 (B, with an A-grade side effect on turns). A local, PINNED decomp clone and `tools/decomp.py`. NEW
- **Evidence:** the fetch numbers above (35-77 different agents each fetched `data/maps/`, `trainer_parties.h`,
  `overworld.c`, `battle_script_commands.c`, `battle_main.c`, `layouts.json`); 71 failed calls (41 not-found);
  `08-MISTAKES.md` 2026-09-04 and playbook section N (`gh api | base64 -d` corrupts binaries on Windows);
  `verify_knowledge.py:48` and `extract_milestones.py:408-419` fetch the moving master tip every run (only `:619` reads a
  blob sha), so "checked against the decomp" names no commit; a clone was started 2026-10-14 and abandoned
  (`/tmp/claude/pokeemerald_clone` holds only an empty `.git/objects`).
- **What:** a shallow, sparse clone (`src data include`) outside the repo, pinned to a SHA written in
  `ai_player/knowledge/DECOMP_PIN`; `decomp.py {grep,show,label,flag,map}`; both extractors read it through the same
  helper; a gate fails when the clone's HEAD differs from the pin. Binaries are read as files.
- **Benefit:** removes about 4 % of all tool calls, network flake and the binary trap, and makes verification
  reproducible. Honest size: `gh api` output is only 1 % of context weight, so this is a turns and correctness win.
- **Cost:** about 120 lines and a one-off clone. **Risk:** pin drift, closed by the gate.

### P5 (A). A queryable FACTS LEDGER that also keeps REFUTED claims. NEW
- **Evidence:** 346 notes (6.4 MB) in `ai-research-notes/`, all prose; five `CLAUDE-VALIDATED-*` files; the chapter 3-4
  recon cost about 16M with 9 agents; 91 % of decomp fetches repeat a path another agent already fetched, so the same
  questions are re-asked. `CLAUDE.md` records Gemini agreeing and still wrong about 35 % of the time, a denied
  `ROUTE111_OLD_LADYS_REST_STOP`, and KI-58's four wrong offline models.
- **What:** `PROJECT KNOWLEDGE/facts-ledger.jsonl`, one line per claim: id, claim, verdict (CONFIRMED / REFUTED /
  UNVERIFIED), source (`decomp@<pin>:path:line` or an evidence file), the TOOL that verified it, date, and the code that
  depends on it. `tools/facts.py find <words>` is the first step of every recon brief; agents append before returning.
  A CONFIRMED line must carry a source (the "note never truth" rule survives); a pin change re-checks the path:line
  entries by script.
- **Benefit:** recon stops re-deriving, and a refuted hallucination stays refuted. **Cost:** a small script plus the
  brief template. **Risk:** rot, bounded by the pin and `--recheck`.

### P6 (A). A mechanical PRE-FILTER for Gemini and agent notes. NEW (needs P4)
- **Evidence:** measured phantom flag names 35 % (2.5-pro) and 11 % (3.1-pro); an invented map and script label tagged
  VERIFIED; `audit_flag_names.py` covers flags only.
- **What:** `tools/prefilter_note.py <note.md>` extracts identifiers (FLAG_/VAR_/MAP_/SPECIES_/ITEM_/MOVE_, script
  labels, path:line cites), greps each in the pinned clone and `modules/data`, and stamps found / PHANTOM. The Claude
  validator then gets only the phantoms and the load-bearing claims.
- **Benefit:** phantoms die before any Claude token; the validator reads less. **Cost:** about 150 lines.
  **Risk:** a legitimate name in another spelling is flagged (cheap to clear); the validator still owns the facts code
  depends on.

### P7 (A). A 25-second QUICK lane and a parallel FULL lane for the unit suites. NEW (A2's `run_regression.py` is the full run)
- **Evidence:** the UNITS file above: `test_check_purity` 381 s (67 % of the 9 m 27 s), `test_world` 78 s,
  `call_census` 34 s, `test_safety_gates` 27 s, `test_host` 19 s; every other suite 9 s or less (`test_goals` 217 tests
  in 2.1 s, `test_battle` 1.0 s, `check_purity` 4 s, `check_lessons` 9 s). The suites run in series although independent.
- **What:** `run_units.py --quick` runs the fast suites (about 25 s) after every edit; `--full` runs the suites in
  parallel processes and shards `test_check_purity`'s 29 tests across workers (estimate 1.5-2 minutes); `--changed`
  picks suites from `git diff --name-only` through the import graph `check_purity` already walks.
- **Benefit:** feedback about 20 times faster in the loop, fewer polling turns, shorter-lived agents (P1). **Cost:**
  small. **Risk:** parallel runs sharing temp folders or the ledger lock (fold into B4); the full lane stays the gate
  for any commit.

### P8 (B, highest care). Evidence digests scoped to the code a driver really uses. NEW
- **Evidence:** `provenance.py` digests the whole `ai_player/` diff and the rule is "every evidence file names THIS
  tree", so any edit re-stamps everything. The 5.2 changelog: "The FULL regression of steps 0-5 PASSED. provenance.py
  changed, so every suite ran" (which suites ran was an agent's judgment). Each of 5.1 and 5.2 had a build plus two
  verifier rounds, each re-running the regression.
- **What:** each evidence file records the digest of its import closure plus the data files it opened (recorded at run
  time with `sys.addaudithook`, not guessed from imports). `impact.py <diff>` lists the evidence a change makes stale.
  Backstop kept: a nightly background FULL regression (no agent tokens), and any change under `host/`,
  `gates/provenance.py` or `knowledge/` invalidates everything.
- **Fault arms (required):** mutate a transitive import, then a data file; the dependent evidence must go stale.
- **Benefit:** a fix round re-runs only the impacted drivers. **Cost:** moderate. **Risk:** the highest here, since a
  missed dependency gives falsely fresh evidence, and it relaxes "names THIS tree", which needs a `06` entry.

### P9 (A for cold starts, modest for workers). BYTE and LINE-LENGTH budgets for current-state docs, and a README split. SHARPENS A4
- **Evidence:** `lint_docs.py:102` budgets LINES (`04-` 900, `03-` 4400), but `04-HANDOFF.md` is 390,563 B (average 432
  chars per line, longest 56,940, 14 lines over 3,000), `03-PUNCH-LIST.md` 693,665 B (18 lines over 3,000 hold 112 KB),
  `ai_player/README.md` 514,440 B in 3,753 lines. In the transcripts 14.5 % of Read characters and 12 % of grep/rg
  characters sit in lines over 600 characters. A line budget passes while a cold read costs about 100k tokens.
  Workers read the README in 72 agents (6.3 % of weight) and the handoff rarely, so the payoff is mainly the
  main-session cold start and the Tier 2 reviewer.
- **What:** lint R8: a byte cap per current-state file (target handoff 60 KB, about 15k tokens) and a line cap of about
  1,200 characters outside tables and code. Split `ai_player/README.md` into a current part (Run it, Layout, Purity
  contract, now about 600 lines) and per-step history files. `prune_evidence.py` treats README citations as "cited", so
  its scan must cover the new folder. Until the split, a `tools/bgrep.py` (hit plus 120 characters, capped, `--line N`
  to expand) keeps greps off the long lines.
- **Benefit:** handoff cold start about 100k to about 15k tokens. **Cost:** a small lint and a one-off split.
  **Risk:** low (move, never delete); the evidence-citation scan is the one thing to fault-test.

### P10 (A). Model routing per stage, each cheaper tier PLANT-TESTED. SHARPENS lean rule 4
- **Evidence:** the model mix above. `.claude/agents/` already defines a Haiku explorer and Sonnet implementer,
  reviewer and verifier, but the per-workflow choice is not recorded in the repo. The orchestration playbook gives the
  price ratios (mid about 0.3x, cheap about 0.1x of top).
- **What:** a stage-to-model table inside the P11 templates. Top tier: design, root cause, the adversarial verify.
  Mid: code from a spec, running suites and reading summaries, the Tier 1/2 doc checks. Cheap: log triage, `decomp.py` and
  `codemap.py` lookups, fixture lookups. Before a stage moves down, plant a defect (a doc with a planted P1
  inconsistency, a diff with a planted bug) and require the cheaper agent to catch it, like the mutant rule.
- **Benefit:** probably the largest single lever if even a fifth of the work moves down. **Cost:** low.
  **Risk:** a weaker tier misses a defect (the plant test and keeping the top tier for the adversarial pass answer it);
  the weekly meter may weigh models differently than these ratios, so read the meter across one stage.

### P11 (A). Stage templates committed in the repo (`tools/workflows/`). NEW
- **Evidence:** the workflow prompts are not in the repo. The first Read of an agent is arbitrary: 33 agents opened with
  the same design note (`2026-09-29-r23-27-DESIGN-v2.md`, 1.18 MB returned across 36 agents), 37 with a README, 18 with
  the handoff. Nothing bounds what they read after.
- **What:** one template per role (recon, build, sweep analysis, verify, doc check). Required fields: GOAL, READ LIST
  (file and range), DO-NOT-READ (evidence folders, `INDEX.md`, whole `07`/`08`), STOP CONDITION, RETURN CAP (under 200
  words plus a file path), MODEL (P10), WAIT RULE (P1), "map first" (P2), "ask the facts ledger first" (P5). A lint
  checks the fields.
- **Benefit:** costs become reproducible and diff-able; a new session starts from the cheapest known prompt.
  **Cost:** small. **Risk:** ossified templates, which P3 would show.

### P12 (A, tiny). An exact context-size nudge in the main session. NEW
- **Evidence:** this session's transcript is 199 MB; the backlog's A1 evidence is 300k-token re-reads per health check,
  and `06` 2026-10-15 lists "a very long main chat re-read on every status message" among the four big costs. The rule
  "fresh session at each clean boundary" is prose, and the project says anything enforceable belongs in a gate.
- **What:** a `UserPromptSubmit` hook (Python) reads the LAST assistant `usage` line of the transcript (cache read +
  cache write + input = the exact context size, no estimate) and, past about 400k, adds one line: "context N k;
  handoff current? (last commit on 04-HANDOFF); suggest a fresh session after the next commit". At most once per 20
  prompts.
- **Benefit:** the main session stops growing silently. **Cost:** about 30 lines. **Risk:** nag fatigue, so the cap.

### P13 (C). A fixture and save CATALOG. NEW
- **Evidence:** `ai_player/gates/fixtures/` holds 48 files (25 `.ss1` states, 7.3 MB) from 8 `make_*fixture*.py`
  scripts; each has a `.build.json` but there is no index. `tools/story-dev/saves/` holds 175 bot checkpoint saves
  (409 MB) across the whole story, which chapters 3-4 will need.
- **What:** `INDEX.json` generated by reading each state's memory (map, badges, party species and levels, key flags,
  money) plus how it was made; `tools/find_fixture.py --map X --badges N --party-min L`. First check whether the AI
  harness loads the bot's `.ss1` files unchanged (not verified here).
- **Benefit:** a step starts from an existing state instead of building one live. **Cost:** small.
  **Risk:** a bot-made state carries bot-shaped flags, so the catalog records provenance; it is a test fixture only
  (USER RULING 35).

## The order (Claude's call, cheapest and most certain first)

1. **P3, P11, P1, P10:** no game code; they address the measured 53 % (long agents), 6 % (cold re-writes) and the model
   mix. P12 any time.
2. **P2 and P7:** the code map and the quick lane, the loop every builder lives in.
3. **P4, then P5, then P6:** the research stack, ready before chapters 3-4 recon (it also feeds A5's chapter packs).
4. **P9** with the A4 archive work.
5. **P8 last,** with its fault arms and a `06` entry. **P13** when chapters 3-4 need fixtures.

Re-rank when P3's first report is in.
