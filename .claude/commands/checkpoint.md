---
description: Safely park unfinished work before stopping (user-run only).
disable-model-invocation: true
---
Safely checkpoint this session because the user must stop now — possibly resuming later from a DIFFERENT computer. Checkpoint the work AS IT IS: do not refactor, clean up, or rush to "finish quickly".

0. Decide where the in-progress work belongs:
   - If the project has NO defined verification standards (no test suite/gates/build checks), or the current work PASSES them: checkpoint directly on the current branch.
   - If the project HAS verification standards and the current work is FAILING or unverified: ask the user — (a) wip-commit to the current branch anyway, or (b) keep the main branch green: move the work to a clearly named WIP branch (`wip/<item>-<YYYYMMDD>`), restore main to its last verified state, and push BOTH branches. If the user is unavailable and the project's conventions demand a green main, default to (b).
1. Record any NEW directives, design decisions, or specs the user gave this session as punch-list items with their FULL specifications in `03-PUNCH-LIST.md` (and append to `06-DECISIONS-LOG.md` if they lock a design rule) — do NOT implement them now.
2. Update `PROJECT KNOWLEDGE/04-HANDOFF.md` → `## If stopped mid-task` section (a real section since 2026-10-22; the session-start hook injects its first 6 non-blank lines as the RESUME POINT, so put the exact next action in those lines and never the phrase `Nothing pending` while work is parked): the item (#N), exactly what is complete vs incomplete, files mid-edit and their state, the EXACT next action on resume, which branch holds the work, and — if work was parked as failing — the full debug state: what's failing, what was tried, measured results, leading hypothesis, so the next session resumes WITHOUT rediscovery. Refresh "Last updated".
2b. **Tier 0 + Tier 1 of the DOC CONSISTENCY LAYER** (CLAUDE.md directive; NOT the full Tier 2 — the user is stopping NOW): run `lint_docs.py` + `audit_doc_consistency.py` (both exit 0), then ONE cheap independent subagent (NOT a fork) checking the P1–P5 pairs against the doc diff + a one-paragraph claim — the pair check is the cheap half that catches a lying resume pointer, which is the half that strands the next machine. Findings without both quotes are discarded.
3. `git status --short`, account for every untracked file by name, then stage EXPLICIT PATHS
   (`git add <path> ...`); commit `wip: checkpoint — <short description> (punch-list #N)` on the
   branch chosen in step 0. ‼ `git add -A` is BLOCKED by `.claude/hooks/block-blind-git-add.ps1`.
4. `git push` for every branch touched. If rejected because the remote has new commits: pull, verify, push again (ask before resolving any conflict destructively). If pushing is impossible (offline / no remote), say so clearly and record it under "Gotchas / unpushed work" — the next session must know this machine holds stranded work.
5. Final report: what was checkpointed, branch(es) and commit hash, push status, and the one-line resume instruction.
