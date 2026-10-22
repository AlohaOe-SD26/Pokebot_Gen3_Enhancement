# BUILD SPEC S2-1b: the handoff slim-down (04 from about 403 KB to 60 KB or less), 2026-10-22

> The coordinator's spec, from three read-only recon reports (filed beside this as
> `2026-10-22-S2-1b-recon-{tools,content,adversarial}.md`, notes). Backlog item 7's open half
> (`2026-10-18-improvement-backlog.md`); `06` 2026-10-21 S2-1 says S2-1b "must decide how 04's `##` sections, banner and
> state-table rows are retired verbatim, and how R3's 900-line budget and R8's bytes coexist". This spec decides it.

## WHY

Every session starts by reading `04-HANDOFF.md`. It is 403 KB and 899 of 900 lines. Its live state lives inside 14
mega-lines that mix the present with months of story-bot history, out of date order. The recon measured three things:
- The three LIVE pieces alone (the line-6 banner, 24 KB; the STATE table, 72 KB; the `➡➡➡` line, 64 KB) are about
  160 KB.
- So no verbatim move of whole lines or sections can reach 60 KB.
- `archive_sweep.py` moves only `###` blocks, and 04 has none it can take.

The cost is paid in every cold start, and the mixing has misled cold starts more than once.

## THE DECISION: SNAPSHOT, THEN REWRITE

1. **Snapshot, byte for byte.** Append the WHOLE current `04-HANDOFF.md` to the END of `28-HANDOFF-ARCHIVE.md`, under
   one new heading line of your choosing that starts `# HANDOFF SNAPSHOT — 2026-10-22, the FULL pre-slim 04-HANDOFF.md,
   VERBATIM (S2-1b)`, followed by one line saying it is the exact file as of the HEAD you read and how to verify that
   (`git show <HEAD>:"PROJECT KNOWLEDGE/04-HANDOFF.md"`).
   - 28 already holds earlier verbatim snapshots with their own `#` headings and fences, so this is its established
     pattern, not a new kind of file.
   - 28 has no line budget and no byte ceiling.
   - No new numbered file: `06` 2026-08-28 says 04 is never split into "part N of M", and the split is by KIND, with
     history going to 28.
2. **Rewrite 04 from the live material only.** About 40-50 KB and at most 61,440 B. Every line is at most 1,200
   characters, so it needs NO long-line waiver. Story-bot detail is replaced by a pointer section (below).
   - This is not "trimming live content" (`06` 2026-08-22 PASS 5): the snapshot keeps every byte, and the rewrite
     keeps every LIVE item.
   - The completeness check below exists to prove that second half.

## WHAT THE NEW 04 MUST CONTAIN (in this order; every requirement here is load-bearing, the reason is given)

1. **Lines 1-5 kept as they are now:** the title, the sync note, and line 5 `**Repository:** https://github.com/...`.
   `Bootstrap-Project.ps1` rewrites or prepends that line, and CLAUDE.md says the remote URL is recorded in 04.
2. **Line 6: `**Last updated:** 2026-10-22 (...)`,** one short sentence on what changed, at most 1,200 chars.
   - `audit_doc_consistency` W2 needs it.
   - `selftest_workflows` T-2b and the doc-check template read `04-HANDOFF.md:1-7` as the banner (at most 30,000 B).
   - Put NO `#`/`##` heading containing "START HERE" or "YOU ARE HERE" anywhere (lint R2 allows at most one, and the
     marker below is not a heading).
3. **`## WHAT THIS IS`, rewritten to be TRUE today.** The current section describes only the story bot. Cover:
   - The AI player (`ai_player/`): USER RULINGS 35, 40 and 41. It plays the game itself, like a seasoned person; the
     goal is the whole game, deployable.
   - The bot tuner: `ai-agent/`, running 24/7 from its own clone `C:/Remote Projects/pokebot-learner`. It tunes the
     scripted BOT, not the AI.
   - The story bot (`sandbox-pokebot/` working build, `custom-pokebot/` promoted fork), PARKED by USER RULING 34/35.
   - The pristine upstream mirror (`40cakes repo/`).
   - The AI frontier line: `PROJECT KNOWLEDGE/ai-frontier.txt`.
4. **`## If stopped mid-task`, a REAL `##` section** (today it is a table row, so the Project Kit's session-start hook,
   regex `(?ms)^##\s*If stopped mid-task\s*(.+?)(?:^##\s|\Z)` in `.claude/hooks/session-sync.ps1`, never fires).
   - The hook injects its first 6 non-blank lines unless the body contains `Nothing pending`. So the first 6 lines must
     be the true resume point: the live-system watch now pending (O5's restart at the end of ai0041; the K=17 canary,
     then `archive-check`, then K=4; "never lower `keep_raw_cycles` below 17 before `archive-check` prints OK ai0024";
     "if `git status` says AHEAD, push first").
   - Keep the `⛅ CLOUD PHASE` note verbatim: `06` 2026-10-15 says its revert step is "drop the handoff's cloud note".
5. **`## STATE`: a table, each row at most 1,200 chars, CURRENT facts only.** Rows:
   - branch / remote, with "TRUST `git status`, NOT THIS CELL";
   - the box (bot tuner: 12 lanes, its cycle times; the AI player's frontier);
   - is code frozen? ("No ... commits here are safe ...");
   - upstream mirror: the user's PARK ruling of 2026-09-26, and the last daily check, taken TODAY from
     `40cakes repo/UPDATE-LOG.md` (the current row is stale: it says 2026-10-02 while the log says 2026-10-14 or later);
   - the newest restore point: `git tag -l "restore/*" --sort=-creatordate | head -1`;
   - **the `| sandbox ↔ custom drift |` row,** label EXACTLY as now:
     - `probe_drift_restatement.py` allows a dated drift digit ONLY in this row, and `audit_doc_consistency` needs its
       currency marker.
     - Re-measure the figure with `cd tools/story-dev && PYTHONUTF8=1 py -3.12 promote.py --check` (read-only).
     - Write today's number "as of 2026-10-22 (LATEST)". The old 312 says 31, and the old 891 says 0: resolve that
       contradiction by measuring.
     - Keep the "do NOT fix it by flipping line endings" advice: `06` 2026-09-15 says it STANDS.
   - **the git stash row VERBATIM** (`06` 2026-08-13 USER RULING: "the stash is documented in `04-HANDOFF.md`'s STATE
     table").
6. **`## ⏭ NEXT ACTIONS, IN ORDER`** (the heading must START with `## ⏭ NEXT ACTIONS`: the doc-check template reads
   `@## ⏭ NEXT ACTIONS+47`, so the queue head must sit within 47 lines of it, at most 30 KB). Under it:
   - EXACTLY ONE line beginning `>    ➡➡➡` (gate H1, regex `^>\s{2,}➡➡➡`), short, naming item 0.
   - Then the queue as separate lines, each at most 1,200 chars, in order. Take them from the current 384 chars
     0-11632 and 13600-15329 (the recon's offsets; re-find them by text), dropping only what those chars themselves
     mark DONE.
   - Then the backlog's top-15 order BY POINTER to `ai-research-notes/2026-10-18-improvement-backlog.md` (its lines 3-19
     are the authoritative order). Do not copy it.
   - Fix the false opening sentence: the current 384 opens "The story bot is the 'hands'", which USER RULING 35
     superseded.
   - A line "Remaining after this item: S2-1b part 2, the `03-PUNCH-LIST.md` slim-down (4,400/4,400 lines, about
     697 KB), by the same snapshot-then-rewrite method, its own spec."
7. **`## RULES THAT BIND EVERY SESSION`:** the live rules a session needs whatever it works on, each one line with its
   source:
   - the single-marker rule and the order of reading;
   - archive-first and the line budgets;
   - "do NOT copy a whole fork to scratch";
   - the expected-dirt rule for `party_accounting_ledger.jsonl` (commit it, never `git checkout --`);
   - never read-modify-write a doc with PowerShell;
   - the stash rule;
   - the suite is safe to run bare (the cp1252 check);
   - `probe_stale_citations.py` before trusting a `file.py:NNN`.
   Quote the old wording where it is short.
8. **`## STORY BOT (PARKED): what binds when the user resumes it`:**
   - First a pointer: the full story-bot handoff is in 28 under the snapshot heading, and `12-STORYMODE*.md` plus
     `14-AGENT-PLAYBOOK.md` hold its method.
   - The two parked branches: `wt/gradeidentity`, `wt/boxfirst`, and the "Story-bot next, when the user resumes it, in
     order" list.
   - The upstream-merge "THREE THINGS BEFORE YOU RUN STEP 2" rule.
   - Then EVERY live do-not and open item the recon found under history headings, one line each, QUOTED with its old
     line number. At least these, from `2026-10-22-S2-1b-recon-adversarial.md` §3 and `-content.md` §1:
     - never run two ROM drives at once;
     - DO NOT ADD MARILL TO BENCH_SPECIES;
     - DO NOT RE-PROPOSE WIDENING TRAIN_CATCHUP_GAP;
     - PID IS NOT UNIQUE;
     - `--build sandbox` IS MANDATORY;
     - the boss/status battle-policy change is the USER's call;
     - KI-66's OWNER filter is OPEN;
     - "P7 REFUTED, read before writing any room code";
     - DO NOT PLAN A DRIVE TO ANSWER "CAN THE PARTY WIN";
     - THE HEAL FAIL-SOFT PATH FIRED ZERO TIMES;
     - DO NOT REORDER, plus its watch condition;
     - `#24-e4healing` OPEN;
     - DO NOT REPRODUCE #2 UNDER #1's CONDITION;
     - the two facts too expensive to lose (read `ACCEPTANCE:`, not the last line; `hp_entering_<room>` is a fake
       reading);
     - the three TRAINING_GRASS rules;
     - the AST-equality promotion rule;
     - "To PROMOTE (the USER's call, never assume it)";
     - NEVER COMMIT OR EDIT THE TREE WHILE A BATCH RUNS;
     - "a chapter's acceptance test must include 'and the bot can continue'", plus the other archived-session lessons
       at old 316-328.
   - If you find more, include them. A live rule dropped here is the failure this item can cause.
9. **`# HOW TO RUN / TEST`, keeping this heading text:** `02` and `14` cite "HOW TO RUN / TEST", and gate H2 needs the
   heading plus a body of at least 10 lines.
   - The LIVE recipes VERBATIM, from the old 653-685, 710-720, 771-786, 851-852, 867-870 and 879-883.
   - ADD the learner status command: `py -3.12 "C:/Remote Projects/pokebot-learner/ai-agent/learner.py" status`.
   - ADD the one-call check-in, `py -3.12 tools/status.py`, and the sync ritual.
   - Keep NO story-bot driver recipe: H3 and H4 check every `--driver` and `.ss1` named here. Point to the snapshot for
     them instead.
10. **A short footer:** "This file is CURRENT STATE only; history is in 28".

## DEPENDENTS TO FIX IN THE SAME CHANGE

- **`tools/story-dev/selftest_workflows.py` T-2b FAULT** (about line 398) uses the REAL 04: "READ-LIST
  `04-HANDOFF.md:1-120` misses the queue (and is over 30 KB)". It passes only while the real 04 is big.
  - Re-point that FAULT arm to a SYNTHETIC handoff in its temp dir (the old shape: a banner over 30 KB in lines 1-120,
    or a queue heading outside the range), so it still FAILS for the reason it names.
  - Keep the CONTROL on the real 04.
  - Prove the new FAULT arm catches the old READ-LIST and is not vacuous.
- **`00-README.md`:** line 9 says the file's opening lines are "a stack of dated banners, most of them history". Make
  it true for the new shape (P4). Keep its `grep -n '^>    ➡➡➡'` instruction working.
- **`tools/workflows/templates/doc-check.md`:** its READ-LIST describes the old shape ("line 6 alone is over 20 KB",
  and the `➡➡➡` line "is one line of about 60 KB ... never a range around it").
  - Make that text true for the new shape, keeping the two ranges `04-HANDOFF.md:1-7` and
    `04-HANDOFF.md:@## ⏭ NEXT ACTIONS+47`.
  - Bump its `stage-template:doc-check@N` version.
  - `py -3.12 tools/workflows/lint_templates.py` must stay CLEAN.
- **`.claude/commands/wrapup.md` and `checkpoint.md`:** they say pairs "P1–P4", while CLAUDE.md has P1–P5. Their
  "If stopped mid-task" section is now a real section. Make both true.
- **The lint bookkeeping, done only through the tool:**
  - `py -3.12 tools/story-dev/lint_docs.py --rewaive 04-HANDOFF.md` drops the stale waivers, a shrink.
  - Then `--ratchet` lowers 04's ceiling. Never raise anything.
- **Do NOT edit:** 02, 03, 05, 06, 07, 08, CLAUDE.md or `run_gates.py`. The coordinator writes the changelog,
  decision and mistakes entries. If something there must change, REPORT it.

## PROOF (the build is not done until each holds; report each verbatim)

- **P-1 LOSSLESS SNAPSHOT.** A script you write in scratch, run before and after, proves three things:
  - (a) `28_after` starts with `28_before` byte for byte;
  - (b) the bytes after your heading lines equal the old `04-HANDOFF.md` byte for byte (working-tree bytes);
  - (c) the same holds against git blobs: the LF-normalized appended part equals `git show HEAD:"PROJECT
    KNOWLEDGE/04-HANDOFF.md"` with line endings normalized.
  - FAULT arm: the script fails when one byte of the appended copy is changed in a scratch copy.
- **P-2 GATES.**
  - `py -3.12 tools/story-dev/lint_docs.py` (ALL PASS), `audit_doc_consistency.py` (PASS),
    `audit_handoff_invariants.py` (H1-H5 PASS), `probe_drift_restatement.py`, `probe_runrecipe_fixtures.py`,
    `py -3.12 tools/workflows/lint_templates.py` (CLEAN) and `selftest_workflows.py` (ALL PASS).
  - Then the whole no-ROM suite: `cd tools/story-dev && PYTHONUTF8=1 py -3.12 run_gates.py --quick`.
  - Quote each summary line.
  - If `probe_runrecipe_fixtures.py`'s hand-run fault arm (`POKEBOT_RECIPEGATE_FAULT=1`) relied on a dead fixture
    named in the old 04's fences, say whether it still fails after the move, and report what it now needs. Do not
    weaken it.
- **P-3 SIZE.** The new 04: bytes, lines, and its longest line (at most 1,200).
- **P-4 THE KIT HOOK.** Run `.claude/hooks/session-sync.ps1`'s regex (Python equivalent) on the new 04. Show the 6
  lines it would inject.

## STOP CONDITIONS (report instead of improvising)

- A gate can only pass by loosening it.
- A live rule has no place in this layout.
- The new 04 cannot fit in 61,440 B without dropping a live item.
- Anything in the old 04 contradicts a ruling in 06: report it; do not choose silently.
