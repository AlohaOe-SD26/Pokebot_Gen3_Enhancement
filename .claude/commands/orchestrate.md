# /orchestrate — run a task as orchestrator + cheap workers (premium-token efficient)

Run the task named in `$ARGUMENTS` using the tiered pattern in
`PROJECT KNOWLEDGE/16-ORCHESTRATION-PLAYBOOK.md`. You are the ORCHESTRATOR (premium tier).
Your tokens are the scarce resource; the workers' are not.

**Read §2 of the playbook before delegating anything.** The governing rule:

> Delegate only work whose success a harness/probe/test can prove without you re-reading
> the codebase. If the only way to know it worked is judgment, YOU do it.

## Step 0 — Triage (do this first, in your head, ~5 lines out loud)
Classify the task:
- **DIAGNOSE an intermittent/timing bug?** → Do NOT delegate the diagnosis. You may
  delegate *recon around it* (log triage, state probes, map facts). Say so and proceed.
- **BUILD/EDIT with a clear spec?** → Full pipeline below.
- **RECON/RESEARCH only?** → Explorer + Gemini; you just synthesize.
- **Trivial (< ~15 lines, one file)?** → Just do it. Orchestration overhead would exceed
  the saving. Say that and do it.

## Step 1 — Scout (CHEAP, parallel)
Spawn `explorer` agents (one Agent call per independent question, all in ONE message so
they run concurrently) for: which files/symbols are involved, what the map/ROM facts are,
what a long log says. Ask for `FINDINGS/ANSWER/GAPS` only.
Also fire `tools/story-dev/gemini_relay.py` in the background for any external
decomp/mechanics question (parallel with `&`; answers are LEADS to verify, never truth).

## Step 2 — Spec (PREMIUM — this is your highest-value work)
Write the spec yourself. Context quality beats worker tier, so be exact:
```
TASK / WHY / FILES (exact paths+lines) / DO NOT / ACCEPT (the command that proves it) / CONTEXT / RETURN
```
If you cannot name FILES and an ACCEPT command, the task is not ready to delegate —
scout more, or do it yourself.

## Step 3 — Implement (MID) then Prove (MID)
- `implementer` applies the spec.
- `verifier` builds/runs the A/B proof (plus a control that the healthy path is intact).
- **You write the tricky/timing-critical code yourself** — battle handler internals, the
  KI-15 nudge, navigator bail logic, anything where a removed wait is the bug.

## Step 4 — Gate (PREMIUM, diff + evidence ONLY)
Run the 5-check rubric (playbook §5): proof ran / scope / blast radius / faithfulness /
docs. Optionally spawn `reviewer` for an adversarial second opinion, and/or send the diff
to Gemini for a cross-family read — **both are advisory; the harness wins.**
**Kick-back budget = 1.** On a second failure, take it over yourself.

## Step 5 — Land it
Definition of Done stays unchanged (root `CLAUDE.md`): update current-state docs, append
changelog (+ decisions if a real choice, + mistakes with a prevention rule if a bug was
fixed), update the handoff, commit with `<type>: <summary> (punch-list #N)`, push.

## Step 6 — Report the ledger (one block, always)
```
DELEGATED:   <role → task>   ×N
KEPT PREMIUM: <what and why>
KICK-BACKS:  <n>
OVERRIDES:   <what you had to rewrite>
EVIDENCE:    <the proof command + verdict>
```
This is the §6 metric trail — it is how we learn whether the pattern is actually working.

## Never
- Delegate without FILES + ACCEPT.
- Re-read files a worker already summarized (that's the re-hydration trap that erases the
  whole saving).
- Let an LLM-vs-LLM disagreement run without a deterministic tiebreak (run the harness).
- Rebuild your own system prompt mid-session (kills prompt caching).
- Delegate the judgment call of whether to keep iterating or move on — that's yours.
