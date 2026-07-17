---
description: Finish-and-verify the current item per the Definition of Done (user-run only).
disable-model-invocation: true
---
Run the FULL Definition of Done from CLAUDE.md for the work item just completed, in order:

1. Verify the change actually works (run the project's tests/gates/build as applicable) — if verification FAILS, stop and say so: failing work is a `/checkpoint` (parked honestly), never a wrap-up.
2. Update current-state docs: `01-VISION-AND-DESIGN.md` / `02-ARCHITECTURE.md` / `05-KNOWN-ISSUES.md` as applicable; mark the item done in `03-PUNCH-LIST.md` (with date, moved to Done).
3. Append the entry to `07-CHANGELOG.md`; append to `06-DECISIONS-LOG.md` if any significant decision was made; if this item involved fixing a bug or abandoning a tried approach, append an entry to `08-MISTAKES.md` (symptom, root cause, the fix that worked, one-line prevention rule) so it isn't repeated.
4. Record any NEW directives, design decisions, or specs the user gave this session as punch-list items with their FULL specifications — wrap-up implements nothing new.
5. Update `04-HANDOFF.md` (current state, what was just done, next steps in order) and clear the "If stopped mid-task" section if this item was its subject.
6. `git add -A` and commit: `<type>: <short summary> (punch-list #N)`.
7. `git push` (on rejection: pull, verify, push again; ask before resolving conflicts destructively).

End with: item closed, docs touched, branch + commit hash, push CONFIRMED (or exactly why not).
