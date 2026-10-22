# S2-1b recon, ADVERSARIAL angle: what goes wrong with "move everything but the live state to the archive verbatim"

Recon only; nothing in the repo was edited. Tags: MEASURED (I ran it), READ (I read the source), INFERRED, UNKNOWN.
Line numbers are from 2026-10-22, about 5:30-6:00 AM. NOTE: `04-HANDOFF.md` CHANGED WHILE I READ IT. It went from 403,243 B to
403,577 B on disk, and `git diff -U0` shows hunks at 384, 623 and 719, from concurrent uncommitted work. `git status` also shows
02, 07, run_gates.py and long_line_waivers.json modified (MEASURED).

## 0. THE PREMISE FAILS ON BYTES ALONE (MEASURED, the most load-bearing finding)

The "live state" lines are, by themselves, about 2.7x the 60 KB target. Sizes are LF-folded and come from a scratch `sizes.py`, since deleted under the cleanup rule. Each figure is the sum of utf-8 length + 1 over a line range:
- line 6, the banner: 24,098 B
- the STATE table, 298-314: 72,075 B. Row 312 (drift) is 24,961 B, row 313 (if stopped mid-task) 16,292 B, row 307 (§Ch23/24) 14,479 B.
- line 384, the single `>    ➡➡➡` START HERE line: 64,358 B
- The total for these three is about 160 KB. The whole file is 402,678 B LF (403,577 B on disk, with 899 CRLF pairs).

So a VERBATIM-only move cannot reach 60 KB. The live lines themselves have to be rewritten or condensed, which is not verbatim, or split
apart. Splitting changes them in place, and R3 refuses it: 06 2026-10-21 says "splitting 04's mega-lines alone is refused by R3 (883 -> 1,069
lines)".

The mega-lines mix live text and history inside a single line (MEASURED). Line 384 opens with the 2026-10-03 entry at offset 11. The
2026-10-21 O3 entry sits at offset 3,178, and 2026-09-28 history sits at offsets 17,609 and 17,949. The order is not chronological, so
no line-granular mover can separate those parts.

Line 384's first sentence still reads `The story bot is the "hands".` CLAUDE.md says USER RULING 35 SUPERSEDES ruling 31's "the story bot
is the hands". Keeping line 384 verbatim therefore keeps a superseded claim at the head of the live marker (READ + INFERRED).

## 1. Rulings in 06 that constrain 04, the archive or "verbatim"

`decomp_lookup.py ask "handoff"` returned 5 rulings (MEASURED). The ones that bind:
- **06:3562, 2026-08-28, "WHY 04-HANDOFF.md IS NOT SPLIT INTO PART 1 OF N"**
  - "It is an ASYMMETRIC PAIR on purpose, not numbered peers."
  - "The split is by KIND, not SIZE ... Splitting by size cuts across that line and puts stale content inside a file labelled
    current-state."
  - "If it binds every session, that is evidence the budget is wrong rather than the content, revisit it with the user then."
  - So: no 04-part-2. Any new "named home" has to be split by kind (READ).
- **06:3062, 2026-08-22, PASS 5:** "RULING: reclaim budget by ARCHIVING VERBATIM, never by trimming live content ... each script-verified
  to contain ZERO open markers before the move and each leaving a stub carrying the rule later work leans on. Rejected: deleting closed
  detail ... and raising the R3 limit." The same entry says: "Keep starving it [the cold-start agent]." (READ)
- **06:9573, 2026-10-21, S2-1:** "S2-1b must decide how 04's `##` sections, banner and state-table rows are retired verbatim, and how
  R3's 900-line budget and R8's bytes coexist." (READ)
- **06:2007, 2026-08-13, USER RULING "stash@{0} is KEPT PERMANENTLY":** "the stash is documented in `04-HANDOFF.md`'s STATE table with
  what it contains, why it is superseded, and this ruling." So STATE row 314 must stay in 04 (READ).
- **06:5293, 2026-09-15, "Fix the DRIFT METER, not the file's line endings":** "The 'do NOT fix it by flipping endings' advice in
  `04-HANDOFF.md` therefore STANDS." That advice lives in the drift text at 04:312, 624 and 891, where grep matches "flipping" (READ).
- **06:9457, 2026-10-15, CLOUD PHASE:** the revert step is "drop the handoff's cloud note". That note lives inside the mid-task row,
  04:313 ("⛅ CLOUD PHASE ..."). The mid-task row is therefore not only a resume pointer (READ).
- **06:3090, 2026-08-23:** "the pair list gains P5 ... A checklist protects exactly what it enumerates." (READ)
- **06:4308, 2026-09-05:** the "two next steps on one line" gate was rejected after it recurred "SEVEN times ... new text PREPENDED to the
  handoff banner while the sentence it superseded was left standing". So no gate catches a banner/marker double-claim (READ).
- 06:537, 2026-07-26 (route facts live in code; "Rejected: write it down more prominently in the handoff") supports moving prose
  and does not block it (READ).

## 2. 08 prevention rules about handoff edits (READ; quoted from 08-MISTAKES.md)

- 6106 (2026-08-13, P1): "update the QUEUE in the same commit as the banner ... ask 'does the QUEUE agree with the HEADLINE, and does every
  issue HEADER agree with its own BODY'".
- 7584 (2026-08-16, P2 extension): "A heading is a claim about EVERY bullet under it."
- 7732 (2026-08-16): the live item was "documented inside a section marked ARCHIVED". Rule (7758): "'Startable' is a claim about ONE
  item and expires the moment the queue reorders".
- 6154: "the REFUTED text is what leaves and the CORRECTION is what stays ... read what remains ... as if cold".
- 9988: "WHEN A CLAIM IS RETRACTED, GREP THE TREE FOR IT AND FIX EVERY HIT, AND START WITH THE SUMMARY BLOCKS".
- 10278: "A FIX IS A NEW CLAIM ... RE-RUN THE AUDIT AFTER FIXING, EVERY TIME".
- 10312: "ANY SCRIPT THAT DELETES A RANGE MUST BOUND THE RANGE AND REFUSE WHEN THE BOUND IS HIT" (it deleted HOW TO RUN).
- 12547: "If a script's output asserts 'verbatim', 'complete', or 'all', the script must verify it before writing".
- 13871: "WHEN TRIMMING FOR A BUDGET, READ WHAT THE REPLACED SPAN ACTUALLY CONTAINED ... BUDGET PRESSURE IS AN EVIDENCE HAZARD."
- 14524: "A STATUS WORD IS NOT A STATUS. Never decide 'is this closed?' by substring."
- 14630: "WHEN YOU EDIT A LINE, READ THE WHOLE LINE FIRST ... grep that line for 'RE-READ', 'IN THE SAME EDIT', and 'whenever'".
- 14651: "READ THE TOOL'S NUMBER, NOT ITS VERDICT."
- 16005: "before archiving an item, grep its body's nouns tree-wide and hoist anything it solely owns."
- 6333 / 21505: never read-modify-write a doc with PowerShell. "NEVER open(path, 'w') ON A FILE THAT ALREADY HAS CONTENT YOU CANNOT
  REGENERATE, encode to bytes first, write a temp file, os.replace last."
- 9510 / 9531: "lint_docs.py IS A PRE-EDIT CHECK, NOT A PRE-COMMIT CHECK."
- 23070: "apply the resume pointers ... BEFORE launching the review."
- 23983: "a spec that sets a size or count target ... first measures ... how much of it the tool's selection can reach." §0 shows that
  this applies to S2-1b's verbatim premise.

## 3. Live content under headings that call it history (MEASURED with the heading map; READ for content)

The H1s outside fences are at lines 1, 125, 653 and 895. The `#` lines at 662, 693-701 and 717-876 sit inside fences 656-684, 689-702
and 712-877. **In markdown scope, the 125 H1 "RETIRED HISTORY" therefore covers 126-652, which includes the STATE table, NEXT ACTIONS
and the ➡➡➡ line.** In `archive_doc_block`, `#` is not a stop prefix (`STOP_PREFIXES = ("- [", "### ", "## ", "#### ")`), so a block
anchored at 125 runs to 273.

| lines | heading or label says | live content inside |
|---|---|---|
| 17-18 | "Every banner further down is HISTORY" | 22-123: "never run two ROM drives at once" (41-42); "DO NOT ADD MARILL TO BENCH_SPECIES" (56); "DO NOT RE-PROPOSE WIDENING TRAIN_CATCHUP_GAP" (66); "PID IS NOT UNIQUE" (67); "--build sandbox IS MANDATORY" (68, 97) |
| 125-180 | "RETIRED HISTORY" | the ORDER rule (127-140); LINE BUDGETS / ARCHIVE FIRST (142-161); STEP 0 sync (163-172); preflight + run_gates (174-180) |
| 181-272 | (still under 125) | the scratch-disk caution (221-223); EXPECTED DIRT for the party_accounting ledger (236-242); the AST-equality and three-point A/B method rules (258-261); "DIGITS, NOT WORDS" (265) |
| 274-276 | "§Ch20 SHIPPED ... DETAIL in archive" | "The rules later work still leans on, kept here on purpose" |
| 316-328 | "ARCHIVED SESSIONS" | the "can continue" acceptance rule; "THE BOSS/STATUS BATTLE-POLICY CHANGE IS STILL THE USER'S CALL" (324) |
| 330-335 | "§Ch19-ERA ISSUES, MIXED" | KI-66's OWNER filter is OPEN |
| 385-402 | "PREVIOUS ENTRY" / "SUPERSEDED HISTORY" | "P7 REFUTED, READ THIS BEFORE WRITING ANY ROOM CODE" (387); "DO NOT PLAN A DRIVE TO ANSWER 'CAN THE PARTY WIN'" (390) |
| 404-439 | "(HISTORY ... ARCHIVED 2026-09-24" | "THE CAVEAT THAT MUST NOT BE LOST: THE HEAL FAIL-SOFT PATH FIRED ZERO TIMES" (424-427) |
| 441-455 | "(HISTORY ... FIXED" | "DO NOT REORDER" plus a WATCH CONDITION (451-455), with its ruling in 06 2026-09-12 |
| 469-473 | "NOT A NEXT ACTION, HISTORY" | "OPEN ... #24-e4healing" (473) |
| 480 | no `>`; a 47,608 B line in the queue | "DO NOT REPRODUCE #2 UNDER #1's CONDITION" |
| 832-841 | "ARCHIVED 2026-09-24" | "TWO FACTS TOO EXPENSIVE TO LOSE BEHIND A POINTER" |
| 895-899 | "EARLIER HANDOFF SNAPSHOTS" | "if something here is no longer true, fix it here" |

These rules do have other homes (MEASURED with `grep -c` against 06/03/05/14/28): BENCH_SPECIES 06=1, 03=4; TRAIN_CATCHUP_GAP 06=4,
03=6; "PID IS NOT UNIQUE" only 14=1 in current-state. Those homes are not checked one by one.

## 4. What a lossless verbatim move must PROVE, and what proves it today

What has to be proven (INFERRED):
- (a) The archive is append-only: archive_after starts with archive_before, byte for byte.
- (b) Every appended block equals a contiguous slice of source_before.
- (c) source_after equals source_before with each slice replaced by its pointer, and nothing else changed.
- (d) As multisets of lines: source_before = (source_after minus the pointers) + the moved blocks.
- (e) Every pointer's archive heading resolves in 28.
- (f) Every inbound pointer to 04 still resolves: section names and `04-HANDOFF.md:N` ranges.
- (g) Line endings are handled: 04 and 28 are `i/lf w/crlf`, with core.autocrlf=true (MEASURED).

What the existing tools prove (READ):
- `archive_doc_block` invariant A is `lost = [line for line in removed if line not in archive_text]`. That is a substring test against the
  WHOLE 1.25 MB archive. It is not a multiset or order test, it skips the heading line (`lines[start+1:end]`), and it is true by
  construction because `render_archive` appends the same slice. B (orphan), C (false closure) and D (zero-line move) protect the claim,
  not bytes. It writes with `write_text`, which is NON-atomic, against the 21505 rule.
- `archive_sweep` adds the slug-survival check (S-2), the written-equals-simulated tripwire, a word-sequence equality check for splits
  (`_words(new) != _words(lines)`), and a full lint rehearsal before writing. It only selects `###` blocks: its dry run said "0 would
  move, 4 skipped", and 6 `###` headings exist in 04, all inside HOW TO RUN.
- `audit_handoff_invariants`: H1 (exactly one `^>\s{2,}➡➡➡`), H2 (HOW TO RUN exists), H3 (drivers), H4 (fixtures), H5 (arm count). It
  reads 04 only. 28 holds 2 lines starting `>    ➡➡➡` (MEASURED).
- `audit_doc_citations` checks only `ident` + `file.py:LINE` definition citations. Its own docstring says "This is a
  definition-citation checker".
- `audit_doc_consistency` C5 resolves only `ai-research-notes/*.md` and `tools/story-dev/*.py` paths.
- No tool resolves (a), (d), (e) or (f) (INFERRED from the readers above).

## 5. Readers of 04 that a slim-down could mislead

- **session-sync.ps1:70** uses `'(?ms)^##\s*If stopped mid-task\s*(.+?)(?:^##\s|\Z)'`. 04 has no such heading; it is a table row at 313
  (MEASURED). So the kit's RESUME POINT never fires today. A new `## If stopped mid-task` section would start injecting its first 6
  lines at every session start.
- Bootstrap-Project.ps1:540-554 rewrites `**Repository:**` or PREPENDS it when that line is missing, then runs `git add -A`. Keep line 5.
- `00-README.md:9` says "the file's opening lines are a stack of dated banners, most of them history". That is a P4 half to update.
- `tools/workflows/templates/doc-check.md:20` reads "`04-HANDOFF.md:1-7` the banner"; line 21 reads "`@## ⏭ NEXT ACTIONS+47`".
  Inside 04, lines 154, 281 and 340 say "the banner at line 6". Anything that moves the banner breaks all of these.
- `probe_drift_restatement.py:21,73` allows a drift digit ONLY in the `| sandbox ↔ custom drift |` STATE row. Moving or renaming that row
  changes the gate. 06 2026-09-15 also endorses the advice in that row.
- `audit_doc_consistency` C3 is "within the same current-state file", and 28 is out of scope (READ). If the "PASS" half moves to 28 and
  the "BUILD --driver X" half stays in 04, the gate goes silent on exactly the 2026-08-13 P1 failure. W2 needs the `Last updated:` line.
- lint R2: line 125 is the only `#`-heading banner (it matches "YOU ARE HERE" / "START HERE"). Adding a new banner heading while 125
  stays would make R2 red. R8(c): every moved mega-line leaves a STALE waiver, which fails until `--rewaive`/`--ratchet` (READ).
- `/wrapup` (lines 12-13) and `/checkpoint` (line 12) still say "P1–P4", while 06 2026-08-23 says the Tier 1 and Tier 2 references were
  updated to P1–P5 (MEASURED). `/checkpoint` and `/health` refer to an "If stopped mid-task" SECTION, which is a row.
- Baseline (MEASURED, about 5:40 AM): lint_docs exit 0 (04 at 899/900, 03 at 4400/4400); audit_handoff_invariants exit 0;
  audit_doc_consistency exit 1 (gate count 155 vs 156, at 04:623 and 04:719, from the concurrent uncommitted run_gates.py edit).
