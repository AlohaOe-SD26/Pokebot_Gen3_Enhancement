# /escalate-sequence — hand a stuck story sequence to an external research agent

User directive 2026-07-22: when a story-mode sequence can't be resolved after exhausting
the `/validate-docs` sources + reasoning + a direct ask, STOP burning budget on it. Pause
that sequence and produce two copy-paste prompts the user relays to an external AI agent
(default: Gemini — keeps research off Claude credits). The answer is a LEAD, verified
against the decomp/harness before any code. Full spec + the reusable primer live in
`PROJECT KNOWLEDGE/15-ESCALATION-RESEARCH.md`.

## Trigger (keep it RARE — last rung of the ladder)
Only after ALL are exhausted for the sequence: decomp read, live recon done, walkthrough
consulted, my reasoning + a direct ask to the user. Never a shortcut around real recon.

## What to do
1. **Pause** the current story sequence build cleanly (leave the code in a safe,
   non-hanging state; the frontier stays honestly at the last validated beat).
2. **Generate the two prompts** into a scratch file (e.g.
   `<scratchpad>/escalate-<beat>.md`):
   - **PRIMER (Prompt A):** copy VERBATIM from `15-ESCALATION-RESEARCH.md` — but ONLY if
     the user needs to set up a fresh agent (its context is stable/reusable; skip if the
     agent is already primed). Note in the file that it's a one-time / new-chat paste.
   - **QUESTION (Prompt B):** fill the template from `15-ESCALATION-RESEARCH.md` with the
     specific ambiguity, the facts I've ALREADY verified (so they aren't re-derived), the
     dead-ends I've RULED OUT, and the required answer format.
3. **Present both prompts cleanly in chat** (fenced blocks, easy to copy) AND save the
   file, so the user can paste to Gemini / a fresh agent immediately.
4. **Report what I need back** in one line, and say I'm pausing this beat pending the
   answer (offer to work on something else meanwhile).

## When the answer returns
- Treat every claim as a LEAD. VERIFY each flag/var/coord/trigger against the decomp
  (WebFetch) and/or the harness (probe or segment run) BEFORE building. Prove every fix.
- Verified → build, update the doc section (`✓ external-research + verified`), commit.
- Wrong/vague → re-ask tighter or fall back to the user. Never build on an unverified
  external claim.

## Rules
- The PRIMER is model-agnostic (Gemini today; a spawned Claude sub-agent is a possible
  future automation — see the note in `15-ESCALATION-RESEARCH.md`). Same prompt either way.
- Keep the primer in sync between here and `15-ESCALATION-RESEARCH.md` (that doc is the
  source of truth; this command references it).
