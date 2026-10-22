---
description: Finish-and-verify the current item per the Definition of Done (user-run only).
disable-model-invocation: true
---
Run the FULL Definition of Done from CLAUDE.md for the work item just completed, in order:

1. Verify the change actually works (run the project's tests/gates/build as applicable) — if verification FAILS, stop and say so: failing work is a `/checkpoint` (parked honestly), never a wrap-up.
2. Update current-state docs: `01-VISION-AND-DESIGN.md` / `02-ARCHITECTURE.md` / `05-KNOWN-ISSUES.md` as applicable; mark the item done in `03-PUNCH-LIST.md` (with date, moved to Done).
3. Append the entry to `07-CHANGELOG.md`; append to `06-DECISIONS-LOG.md` if any significant decision was made; if this item involved fixing a bug or abandoning a tried approach, append an entry to `08-MISTAKES.md` (symptom, root cause, the fix that worked, one-line prevention rule) so it isn't repeated.
4. Record any NEW directives, design decisions, or specs the user gave this session as punch-list items with their FULL specifications — wrap-up implements nothing new.
5. Update `04-HANDOFF.md` (current state, what was just done, next steps in order) and clear the `## If stopped mid-task` section if this item was its subject (a real section since 2026-10-22: the session-start hook injects its first 6 non-blank lines as the RESUME POINT unless the section says `Nothing pending`, so a clean stop writes exactly that). ‼ Update the NEXT-ACTIONS queue in the SAME edit as the banner — a "next action" is current-state, and the queue is what a cold agent ACTS from (the 2026-08-13 audit found the banner saying "done" over a queue still saying "build it").
5b. **Tier 0 + Tier 1 of the DOC CONSISTENCY LAYER** (CLAUDE.md directive): run `lint_docs.py` and `audit_doc_consistency.py` (both must exit 0). Then spawn ONE cheap independent subagent (reviewer-shape, NOT a fork) with exactly three inputs — the doc diff, a one-paragraph claim of what this item actually did, and the pair list P1–P5 from the directive. It must QUOTE both halves of each pair; findings without both quotes are discarded. Fix findings, re-run the two gates, then proceed.
5c. **Tier 2 (session end only — skip when more items follow this one):** spawn ONE fresh cold-start agent given ONLY `04-HANDOFF.md` + `00-README.md`, no other context. It reports the exact FIRST ACTION a next session should take (with the commanding line), the P1–P5 pairs quoted, and any instruction to do a thing the same file marks done. A mismatch against what you know is true is a DOC bug — fix it and re-run Tier 0 before committing.
6. `git status --short`, account for EVERY untracked file by name, then stage EXPLICIT PATHS
   (`git add <path> ...`) and commit: `<type>: <short summary> (punch-list #N)`. Name every added
   file in the message. ‼ `git add -A` is BLOCKED by `.claude/hooks/block-blind-git-add.ps1` —
   subagents write into the tree while you work, and it swept an unreviewed file into a pushed
   commit twice on 2026-08-13.
7. `git push` (on rejection: pull, verify, push again; ask before resolving conflicts destructively).

End with: item closed, docs touched, branch + commit hash, push CONFIRMED (or exactly why not).
