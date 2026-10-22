<!-- stage-template:doc-check@4 -->
You are the independent DOC-CONSISTENCY reviewer (CLAUDE.md "DOC CONSISTENCY LAYER", Tier 1) for {{task}} in the repo
C:/Remote Projects/Pokebot_Gen3_Enhancement. You did not write these docs; check them, do not edit them.

## GOAL
{{goal}}
THE CLAIM of what the item actually did: {{claim}}
Read the doc DIFF (`{{diff_cmd}}`) and, for each pair below, QUOTE BOTH HALVES and say whether they agree and whether
the handoff's queue reflects the claim:
- P1 `04-HANDOFF` banner / YOU-ARE-HERE <-> its NEXT ACTIONS queue item 0 ("X is done" above forbids "build X" below).
- P2 every touched `05-KNOWN-ISSUES` KI header (title and status words) <-> that KI's newest dated body line; and
  every `##` section heading <-> the status of EVERY bullet under it (mixed statuses need a MIXED heading).
- P3 `04-HANDOFF` STATE table and HOW TO RUN / TEST <-> this session's newest `07-CHANGELOG` entries.
- P4 `00-README` reading-order descriptions <-> the current top of each file the diff touched.
- P5 the item's own status in `03-PUNCH-LIST.md` <-> the handoff's claim about it. Grep the tree for the item's slug
  and re-read EVERY hit: a status sentence anywhere is another half of the pair.
A finding without both quotes is DISCARDED.

## READ-LIST
- `PROJECT KNOWLEDGE/04-HANDOFF.md:1-7` the banner (P1's first half; line 6 is the one-sentence `**Last updated:**`)
- `PROJECT KNOWLEDGE/04-HANDOFF.md:@## ⏭ NEXT ACTIONS+47` the NEXT ACTIONS queue head, item 0 included (P1's second
  half): 47 lines from the line `grep -n "^## ⏭ NEXT ACTIONS"` finds. The live `>    ➡➡➡ START HERE` line is the
  short line just below that heading (`grep -n "^>    ➡➡➡"`). Since S2-1b (2026-10-22) no line of 04 passes 1,200
  characters and the history is in `28-HANDOFF-ARCHIVE.md`, but read these ranges, never the whole file.
- `PROJECT KNOWLEDGE/00-README.md:1-80` the reading order
{{extra_reads?}}

## DO-NOT-READ
- `ai_player/evidence/`
- `**/INDEX.md`
- `PROJECT KNOWLEDGE/07-CHANGELOG.md` (whole; read the newest entries as a ranged slice)
- `PROJECT KNOWLEDGE/08-MISTAKES.md` (whole)
- `ai_player/README.md` (whole)
- `PROJECT KNOWLEDGE/03-PUNCH-LIST.md` (whole; grep the slug, then read ranged slices around each hit)

## STOP
Stop when P1-P5 each have a verdict with both quotes, or at 150 tool calls (WAIT-RULE). Do not edit any file.

## RETURN-CAP
words: 200
file: {{report_path}}
Write to that file, per pair: PASS or FINDING, the two quotes (file:line each), and for a FINDING the smallest edit
that would make the halves agree. Your final answer is at most 200 words plus the file's path.

## MODEL
top

## WAIT-RULE
Never wait inside a big context: this stage runs no long commands. Past 150 tool calls, write the in-flight note
`PROJECT KNOWLEDGE/in-flight/{{run}}.md` (pairs checked, pairs left) and hand back.

## MAP-FIRST
The doc files are large: find a line with `grep -n "<slug or heading>" "<file>"`, then Read a range around it. Never
Read a whole file over 30 KB.

## LOOKUP-FIRST
Before calling a statement a contradiction of a decision: `py -3.12 tools/decomp_lookup.py ask "<words>"` (it quotes
06's rulings with their do-not lines). A settled decision is not a doc bug (CLAUDE.md rule 11).

## RULES
- Read-only. No git command that modifies anything (`git diff` and `git show` only).
- Scratch only under {{scratch}}. Before your final answer, DELETE the copies, clones and repos you made there (keep only your report or verdict file): scratch is never cleaned for you, and on 2026-10-22 it filled 56 GB of the disk the bot tuner needs.
