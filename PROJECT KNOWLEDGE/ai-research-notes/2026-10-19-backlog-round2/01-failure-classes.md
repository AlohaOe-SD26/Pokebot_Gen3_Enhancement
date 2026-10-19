# Backlog round 2, angle 1: RECURRING FAILURE CLASSES still enforced by prose (2026-10-19)

A NOTE, not truth. Candidates for `2026-10-18-improvement-backlog.md`; none is a decision. Evidence was read with grep
and line ranges (08-MISTAKES.md has about 800 entries, 05-KNOWN-ISSUES.md about 136 headers). Counts below are LOWER
BOUNDS taken from entry headings, not an exhaustive tally.

- **Already covered, so NOT repeated here:** the shell-text hooks (`block_shell_text.py`, USER RULING 29: the heredoc
  rule broke six times in two sessions before it became a hook), `block_destructive_git.py`, the doc-pair gates
  (`audit_doc_consistency.py`, P1-P5), the call-site census (`ai_player/gates/call_census.py`), the story-surface
  undefined-name and silent-except gates, and backlog items A1-A6, B1-B6, C1-C2, D1-D3, E1-E3.
- **The method that found the gaps:** `ai_player/LESSONS.md` already carries a `Status:` line per lesson. Six are
  `PROSE ONLY` and sixteen `PARTIAL`, each with an undated `Needs:`. I ranked those by how often `08` shows the class
  recurring, then checked each candidate against the code so a "gap" is a measured gap.

## Seed table: classes ranked by measured recurrence

| Class | Dated 08 entries (lower bound) | Enforcement today |
|---|---|---|
| A question or definition the user (or `06`) had already ruled, re-derived or re-asked | about 10 (2026-08-23, 09-05, 09-08, 09-10, 09-13, 09-16, 09-18, 09-24, 09-26, 09-29) | PROSE (CLAUDE.md rule 11; LESSONS PR-10 says "Needs: none proposed") |
| A retracted claim survives somewhere in the tree | 6+ (2026-08-15 x3, 08-16, 09-03, 09-24 x2) | SPEC only: `#24-retiredclaimgate`, `[ ]` since 2026-09-03 |
| Code or a test arm that exists but never runs in real play | 6 (2026-09-04, 09-09, 09-12, 09-18, 09-26, 10-14) | Mutant level only (census G3). Live reach: PROSE (PF-15) |
| Gate with holes that hand-picked mutants did not find | 3 rounds (2026-09-29: 32 of 41 mutants turned nothing red; 09-30; 10-01: 103 of 155 killed) | PROSE ("tabulate the input dimensions") |
| Swallowed exception or undefined name | 5+ (2026-09-24 x2, 09-26 x2, 09-28) | GATED for the bot's story surface only. NOT for the AI line |
| A number or "enforced/proven" sentence with no evidence behind it | 5+ (2026-09-07, 09-09 third time, 09-12, 10-03, 10-16) | PROSE ("three routes", PR-3 `check_claims.py` unbuilt) |
| Runner lifecycle (stop does not stop, shared log, queued runs on edited code) | 5 (2026-09-07, 09-27, 09-29 x2, 10-03) | PARTIAL (learner clone and `FrozenTree` gate the AI drivers) |
| Doc size escaping a line budget | measured today (see N3) | NONE |

## A. High value per token

**N1. COUNT recurrences instead of remembering them: a `Class:` tag on every 08 entry, and a recurrence report.**
- **Evidence:** CLAUDE.md rule 6 says "a rule broken twice belongs in a gate", and the only trigger is an agent
  remembering. The heredoc rule reached its SIXTH slip before the hook (08 2026-09-30 x2, 2026-10-01). Rule 11 failed
  about ten times. Finding the table above took about 25 greps over 24,000 lines, which is the cost every future round
  pays again.
- **What:**
  - Each new 08 entry ends with `Class: <slug>` and `Enforced-by: <gate path | hook | none>`. A `lint_docs.py` rule
    rejects an entry dated after the cutover that lacks them.
  - `mistake_classes.py` counts entries per class, joins `LESSONS.md` statuses, and prints classes with 2+ entries
    and `none` or `PARTIAL`, newest first, in at most 10 lines. `/wrapup` and the session brief run it.
  - This note's table seeds the first tags (one cheap pass, no agents).
- **Benefit:** the second recurrence names its gate, not the sixth. The session brief shows "classes owed a gate" for
  free. **Cost:** about 80 lines plus a convention. **Risk:** tag discipline, which the lint rule enforces.
- **Priority: A.**

**N2. PRIOR-ART lookup plus a one-page RULINGS index, injected into every design/research/escalation prompt**
(sharpens LESSONS PR-10, which today says "Needs: none proposed").
- **Evidence:** the table row above (about 10 entries). 08 2026-09-29 states the cause: "agents inherit the rule only
  if the prompt carries it". `06-DECISIONS-LOG.md` is 9,510 lines with 81 mentions of "USER RULING" and NO index
  (the only hit for an index is a punch-list line).
- **What:**
  - `RULINGS.md`: at most 120 lines, one per numbered ruling (number, date, one sentence, keywords, DO-NOT-REOPEN
    flag), built once from `06`'s `## ... USER RULING N` headings.
  - `tools/story-dev/prior_art.py <terms>` greps `RULINGS.md`, `06`, `03`, `05` headings and prints at most 40 lines.
  - The workflow scripts prepend its output to every design, research and escalation prompt, and run it before any
    question goes to the user.
- **Benefit:** fewer agents spent re-deriving a ruled question (08 2026-09-08 and 09-10 each record a design built on a
  question already answered in the repo), and fewer user interruptions. **Cost:** small script and one generation pass. **Risk:** a stale index, so
  `lint_docs` checks that every `06` heading with "USER RULING N" has a line.
- **Priority: A.**

**N3. BYTE and long-line budgets for the current-state docs** (sharpens backlog A4).
- **Evidence (measured 2026-10-19):** `04-HANDOFF.md` is 390,563 bytes in 900 lines; its longest line is 56,940
  characters and 10 lines exceed 5,000. `03-PUNCH-LIST.md` is 693,665 bytes; line 137 alone is 21,701 characters.
  `lint_docs.py` R3 counts LINES only (`LINE_BUDGET`, line 102) and has no byte or line-length rule, so a line budget
  is met by joining content into one line. Mega-lines already defeated tools: this round's grep of `05` returned
  "[Omitted long matching line]", and 08 2026-09-01 records a length-filtered grep that hid the one stale mega-line.
- **What:** `lint_docs` R8: a byte budget per current-state file (set just under the post-A4 size) and a maximum line
  length (for example 1,500 characters) with a waiver list of the existing long lines that may only shrink. The A4
  archive script splits a long line instead of only moving whole items. Fault-test both ways.
- **Benefit:** A4's savings stay saved, and a cold agent can read the banner with `Read`/`grep` at all.
  **Cost:** small. **Risk:** waiver sprawl, handled by "may only shrink".
- **Priority: A.**

**N4. The RETIRED-CLAIM gate, built in its smallest form** (promotes `#24-retiredclaimgate`, open 46 days).
- **Evidence:** the table row above. Retracting one claim took four sweeps (punch list `#24-retiredclaimgate`), and
  08 2026-08-23 records three Tier 1 rounds on one item's docs. 08 (2026-09-24, about lines 20755-20770) already
  specifies it: a machine-readable `WITHDRAWN: "phrase"` line in the retraction, and a gate asserting every other
  occurrence of the phrase sits within N lines of a pointer to the retraction.
- **What:** about 100 lines; the retraction's own quotation is allowed; fault-test that a re-introduced phrase fails
  and the quotation does not. State in its docstring that it is a ratchet for literal survivors, NOT a replacement for
  Tier 1 (paraphrases still need eyes).
- **Benefit:** replaces review-agent rounds that exist only to find literal survivors. **Cost:** small.
  **Risk:** false positives teach people to bypass it, hence the both-ways fault test.
- **Priority: A.**

**N5. A MECHANICAL first-pass mutant generator for changed functions.**
- **Evidence:** hand-picked mutant sets were wrong three rounds running: a fresh agent built 41 plausible mutants and 32
  turned nothing red (08 2026-09-29); a gate killed 103 of 155 (2026-10-01); a coverage check passed because "each row
  was reddened by some mutant of MY choosing" (2026-09-29). `ai_player/gates/revert_step5.py` alone is 1,647 lines of
  hand-written mutants. Each hole was found by a paid adversarial agent.
- **What:** like `call_census.py` (changed functions by AST against HEAD), generate cheap mutants of ONLY the changed
  functions (flip a comparison, drop a statement, negate a guard, swap a constant), run the step's unit suite per mutant
  in the background, and report survivors as "to classify". Survivors are NOT failures (PF-11: a predicted-redundant
  mutant is a claim to run), so noise is bounded by a cap per function.
- **Benefit:** the adversarial agent starts from the survivor list and spends tokens only on semantic holes.
  **Cost:** medium (about 150 lines plus run time, no agent tokens). **Risk:** equivalent mutants; the cap and the
  "classify, do not fail" rule contain it.
- **Priority: A** for tokens; **B** if it must wait for N1-N4.

**N6. Encode two process rules in the workflow scripts: PR-1 and PR-2** (complements backlog A3).
- **Evidence:** LESSONS PR-1 is `PROSE ONLY` ("a fix round only for a FAILURE"; Needs: the refix stage runs only when
  the verifier JSON has `all_pass:false` with a non-empty FAILURES list). PR-2 is `PARTIAL` (Needs: `regression_due.py`,
  a suite-to-files map printing suites whose newest evidence is on another tree). Backlog A3 splits work into short
  stages but does not say the refix stage is conditional.
- **What:** a stage helper that launches the refix stage only on that JSON condition, and the small `regression_due.py`.
- **Benefit:** a refix round is a full builder context (backlog: about 600k tokens), so each avoided round is a large
  saving. **Cost:** small. **Risk:** a verifier that forgets to emit the JSON, so a missing JSON is treated as "ask a
  human", never as pass.
- **Priority: A.**

## B. Correctness: closing classes at the root

**N7. `check_claims.py` (LESSONS PR-3 and PF-18, both unbuilt).**
- **Evidence:** 08 2026-09-09 (third time republishing an unverified statistic; the "three routes" rule is prose),
  2026-10-03 ("ran end to end" with the evidence already deleted), 2026-10-16 (`LESSONS.md` claimed "Enforced"). Backlog
  B2 covers only the LESSONS "Enforced" claims.
- **What:** a line in `07` or an AI README naming a suite with PASS must cite an evidence file whose provenance digest
  (`provenance.py` already writes it) matches the tree it names, and a line with a figure must cite a file or a tool.
- **Benefit:** Tier 1 stops re-checking provenance by eye. **Cost:** medium. **Risk:** over-matching prose, so scope it to
  lines carrying the explicit marker `[ev: path]`; unmarked lines are ignored (a ratchet, not a proof).
- **Priority: B.**

**N8. TYPED verdicts (PASS, FAIL, VACUOUS, REPORTED, NOT-RUN), defined together with A2's `summary.json`.**
- **Evidence:** graders pass `(bool, text)` pairs and treat a check as "reported" by the START OF ITS TEXT
  (`rate_step5.py:1592-1601`, `P2_REPORTED` matched with `text.startswith`, forcing `True`). 08 2026-09-02 (a zero-frame
  no-op graded `ACCEPTANCE: PASS`), 2026-08-27 (a skipped reading printed PASS), 2026-10-15 ("control 0.0 in 20 of 20
  true by construction"), 2026-10-16 (bounds "Enforced" yet forced to PASS).
- **What:** one `Check(id, status, n, floor, text)` type; a check with `n < floor` is `VACUOUS` and counts as a failure
  unless waived by id; `REPORTED` is a status, not a label prefix. The summary file (A2) is written from it.
- **Benefit:** the "can this check fail" question becomes a field, and renaming a label can no longer exempt a check.
  **Cost:** medium; touches the graders once. **Risk:** migration of old evidence, so old files keep their format.
- **Priority: B.** Best done WITH A2, not after it.

**N9. REACH COUNTERS: how many runs ACTED on each new hook (LESSONS PF-15, `PROSE ONLY`).**
- **Evidence:** 08 2026-10-14 (two fixes that passed every body test and were dead because their call was never
  reached), 2026-09-04 (six of seven fault arms dead from creation), 2026-09-09 (five green arms, none called the
  function under test), 2026-09-26 (a recorder that never ran). `call_census.py` proves a MUTANT covers each call
  site; it does not show that real play ever reaches it.
- **What:** a registered hook increments `reach("hook_name")` when it ACTS; the sweep summary prints the count per
  registered hook, and a hook with 0 across the graded sweep is a loud NOTE until waived with a reason.
- **Benefit:** dead code found in one sweep instead of one review. **Cost:** small (one counter, one summary line).
  **Risk:** counters read as proof of behaviour; the docstring says they show REACH only.
- **Priority: B.**

**N10. The AI line has none of the bot's static gates: undefined names, silent excepts, unbounded loops.**
- **Evidence:** `repro_undefined_names.py` scans `modules/story`, `plugins/custom_modes` and `story_harness.py`;
  `repro_no_silent_except.py` scans the story modules and battle strategies. Neither names `ai_player/` or
  `ai-agent/` (grep of both finds no reference). `ai_player/` holds 109 `except Exception` handlers and 8 `while True`.
  A read-only pyflakes run on `ai_player/` and `ai-agent/*.py` today finds one undefined name, a harmless annotation
  (`test_goals.py:2260`, `Goal`, under `from __future__ import annotations`), so the baseline is nearly clean and the
  gate would start green. LESSONS PL-4 ("bound every loop") is `PARTIAL` with "Needs: an AST rule" unbuilt; the
  bot-side class is KI-47/KI-83.
- **What:** add `ai_player/` and `ai-agent/` to both repro scans (or give `run_units` the same three AST rules) and
  build the PL-4 rule: every `while` names its bound constant from an allowlist; a planted unbounded loop is refused.
  The 24/7 learner runs unattended for weeks, so a swallowed error there is invisible.
- **Benefit:** the cheapest class of "ran for hours and did nothing" closed for the new code. **Cost:** small.
  **Risk:** low; a ratchet records the existing handlers as debt.
- **Priority: B.**

**N11. The LEARNER'S PARSER CONTRACT: test it against the real emitters, and pause on implausible output.**
- **Evidence:** `ai-agent/scoring.py` reads the bot's log lines with regexes (`TRAINER_END_RE`, `STARTER_RE`, ...); the
  bump rule for `PARSER_VERSION` is a comment (`scoring.py:33`). The emitter (`trainer_identity.format_end`,
  `trainer_identity.py:266`) carries only the comment "`res=`, NEVER `outcome=` (two batch parsers count
  `outcome=BattleOutcome`)". `test_agent.py:30-31` builds its test line BY HAND. KI-119 (a grader excluded 27 of 78 runs
  from a mis-read identity) is this class. The learner pauses only after N consecutive cycles with NO scored runs
  (`learner.py:514-516`), so a regex that still matches but now reads zero badges would rank settings on garbage for
  a full 12-hour cycle.
- **What:** (a) a contract test that builds a context, calls the REAL `format_end` (and the other emitters), prefixes the
  frame, and feeds the result to `scoring.parse_log`, asserting the parsed fields; (b) a per-cycle plausibility pause:
  many log lines but zero parsed trainer ends, or badges above 8, writes `ATTENTION.md`.
- **Benefit:** protects each 12-hour cycle (the user's hardware time) from a silent format drift when the learner
  fast-forwards to new bot code. **Cost:** small. **Risk:** thresholds too tight, so make (b) a pause only on zero.
- **Priority: B.**

## C. Nice to have

**N12. A KI EXPOSURE table for the bot, built when the bot is un-parked** (generalises the AI-side census).
- **Evidence:** KI-84 (HIGH, open: "worked around in one chapter only, every other `slots=` caller still exposed"); 08
  2026-09-26 (a helper proven broken was fixed in one caller and left in the other for three weeks); 2026-09-18 (a guard
  checklist listed nine of ten call sites).
- **What:** a KI may carry `Affects: module.function`; a script lists its call sites by AST with `guarded / exposed /
  waived` per site. **Benefit:** "grep every caller the same day" stops being memory. **Cost:** medium.
  **Priority: C** (the bot is parked; do it when it resumes).

**N13. One `stop_runs` command with the kill discipline built in.**
- **Evidence:** 08 2026-09-27 (killing a task did not stop its loop; two runners wrote one log) and 2026-09-29 (a stopped
  runner started its next run on code being edited). The prevention rule is prose: "check a STOP file before each arm;
  list start times and kill only what started after the batch".
- **What:** the multi-arm runners share a base that checks the STOP file before each arm, and `stop_runs` writes it,
  waits, then lists leftover harness processes WITH start times (never kills by name pattern). **Benefit:** no corrupt
  evidence. **Cost:** small. **Priority: C** (the AI drivers are already covered by `FrozenTree`).

**N14. A clock line in A1's status script** (sharpens A1).
- **Evidence:** 08 2026-09-07 (an elapsed time quoted from memory, twice, with two different wrong numbers) and the
  standing user preference (12-hour Los Angeles time, started + checked + ETA together).
- **What:** the status script prints "now / started / elapsed / ETA" for the live batch in that format, so no turn
  composes it by hand. **Cost:** trivial. **Priority: C.**

## Suggested order

1. **N3, N1, N2** (documents and the recurrence counter: cheapest, and they cut what every later agent reads).
2. **N4, N6** (replace review rounds and refix rounds with a gate or a rule in code).
3. **N10, N11** (small, and they protect the unattended learner and the AI code).
4. **N8 with A2, then N9, N7, N5** (the proof-quality group, built once with the lean setup).
5. **N12-N14** when convenient.

Verification gates for any of these before building: fault-test every new gate both ways (it fails on the broken
case and does not fire on a mere mention), and run it once against the real tree to record its starting debt.
