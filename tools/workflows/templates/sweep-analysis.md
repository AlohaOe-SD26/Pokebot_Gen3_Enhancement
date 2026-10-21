<!-- stage-template:sweep-analysis@1 -->
You ANALYSE the result of a finished sweep or batch for {{task}} in the repo C:/Remote Projects/Pokebot_Gen3_Enhancement
(Windows; use py -3.12). The sweep ran in the background and wrote a summary; you grade it, you do not re-run it.

## GOAL
{{goal}}
THE QUESTION: {{question}}
THE PRE-REGISTERED BOUNDS (fixed BEFORE the run; never loosen one to pass): {{bounds}}
- Grade from the SUMMARY first; open a raw log only for a run the summary flags, and only a ranged slice of it.
- A batch answers a FREQUENCY question; a CORRECTNESS question needs a targeted A/B (CLAUDE.md rule 9). Say which one
  this sweep can answer, and do not claim the other.
- Identical output across runs is a determinism check, never a replication (rule 8): say "one trajectory, replayed".
- Assert IDENTITY, never position or count (rule 3): a count that nets to zero reads true when nothing happened.
- Instrument the action, not its input (rule 7): a candidate is not an attempt.

## READ-LIST
- `{{summary}}` the sweep's summary file [later]
{{extra_reads?}}

## DO-NOT-READ
- `ai_player/evidence/` (only the summary above and slices of the files it flags)
- `**/INDEX.md`
- `PROJECT KNOWLEDGE/07-CHANGELOG.md` (whole; a ranged slice is fine)
- `PROJECT KNOWLEDGE/08-MISTAKES.md` (whole; a ranged slice is fine)
- `ai_player/README.md` (whole; a ranged slice is fine)
- `**/debug-logs/` (whole raw logs; a slice of a flagged run only)

## STOP
Stop when each bound has a PASS or FAIL with the number behind it, or at 150 tool calls (WAIT-RULE). Never re-run the
sweep inside this stage and never change a bound; a sweep that needs another run is handed back with the reason.

## RETURN-CAP
words: 200
file: {{report_path}}
Write to that file: each bound, the measured value, PASS or FAIL, the run ids behind every FAIL, and which question
(frequency or correctness) the data can answer. Your final answer is at most 200 words plus the file's path.

## MODEL
top

## WAIT-RULE
Never wait inside a big context. If the summary is not there yet, do not poll in a loop: write the in-flight note
`PROJECT KNOWLEDGE/in-flight/{{run}}.md` (what is awaited, where it will appear, what to grade) and finish. Past 150
tool calls: write the same note and hand back what is graded and what is not.

## MAP-FIRST
Before reading a source file over 30 KB (a driver, a rater), map it: `grep -n "^def \|^class \|^    def " <file>`,
then Read only the range you need.

## LOOKUP-FIRST
Before explaining a result by a game mechanic: `py -3.12 tools/decomp_lookup.py ask "<words>"` (rulings, the facts
ledger, the pinned decomp). A mechanic not found there is labelled INFERRED.

## RULES
- Read-only in the repo. Scratch only under {{scratch}}.
- No git command that modifies anything.
- The learner clone C:/Remote Projects/pokebot-learner is READ-ONLY (a live batch runs there).
- Never write to Z:, E:, %LOCALAPPDATA%/pokebot-ops or the Desktop.
