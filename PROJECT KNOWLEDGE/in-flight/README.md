# In-flight notes (git-ignored)

A workflow stage that must stop before it finishes (a long run it should not wait for, or past 150 tool calls) writes
`<run>.md` here: the stage, the files it touched, the command it started, where the summary will appear, and what to
re-verify. The stage templates in `tools/workflows/templates/` tell it to (their WAIT-RULE).

- **At session start**, a note here marks work in progress ON THIS COMPUTER. Read it before touching the files it
  names, together with the "If stopped mid-task" row of `04-HANDOFF.md`.
- The notes are git-ignored on purpose: they describe uncommitted local state, which no other computer has, and a
  committed note would outlive its run (`06-DECISIONS-LOG.md` 2026-10-21).
- Delete a note once its work is committed or discarded.
