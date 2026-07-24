# 16 — Orchestration Playbook (premium-token efficiency without quality loss)

> **Purpose (user directive 2026-07-24):** run this project with a PREMIUM model as
> orchestrator + reviewer and cheaper Claude sub-models + the Gemini API doing the bulk
> work, so a premium quota (Fable 5; Opus 4.8 as the fallback tier) lasts far longer
> **without** losing quality, intelligence, robustness, or results.
>
> Researched with a 4-way Gemini cross-check (design / adversarial critique / concrete
> mechanics / model facts), then reconciled against what actually happened on this
> project. **The adversarial pass changed the design** — read §2 before trusting §3.

---

## 1. The one economic fact that drives everything

Multi-agent orchestration does **not** reduce TOTAL tokens — it usually increases them
(more agents, more prompt copies, review passes). What it buys is a **shift of work off
the expensive tier**, plus parallelism. So the metric is **premium tokens burned**, never
"tokens" in general.

Authoritative prices (per 1M tokens, cached 2026-06-24 — re-check at use):

| Tier (role in this playbook) | Model today | Input | Output | vs Fable 5 |
|---|---|---:|---:|---|
| **PREMIUM** — orchestrator + final gate | `claude-fable-5` | $10 | $50 | 1× |
| **PREMIUM-FALLBACK** — same role when Fable is out | `claude-opus-4-8` | $5 | $25 | 0.5× |
| **MID** — implementer, test/repro writer | `claude-sonnet-5` | $3 ($2 intro) | $15 ($10 intro) | 0.3× |
| **CHEAP** — explorer, log triage, recon | `claude-haiku-4-5` | $1 | $5 | 0.1× |
| **EXTERNAL** — research, second opinion | Gemini (relay) | — | — | separate quota |

‼ **Tier ≠ model.** Roles below name TIERS. When a new top model appears (see §7), you
change one row of this table — nothing else. That is the whole point of the design.

**The two biggest savings levers, in order:**
1. **Sub-agent context isolation.** A sub-agent's file reads, greps, and failed attempts
   never enter the orchestrator's context. This is where the real saving is — not in the
   sub-agent's own (cheaper) tokens.
2. **Prompt caching on the orchestrator** (~0.1× on cache reads). Keep the orchestrator's
   prefix byte-stable; never rebuild the system prompt mid-session.

---

## 2. What the adversarial pass proved (read this before delegating anything)

The critique was blunt and **it matches this project's own history**. Every bug that cost
real time here — KI-15's post-battle wedge, KI-17's DMA race, the planner-blind bridges —
was an intermittent, timing/state-dependent, "spooky action at a distance" bug. Those are
exactly what cheap models produce confidently-wrong answers about.

**Failure modes to design against (all real):**
- **Context re-hydration trap.** If the reviewer must read the whole codebase to judge a
  diff, the premium saving evaporates. → Reviews must be **diff + self-report + evidence**.
- **Rubber-stamp review.** A premium model approving syntactically-valid code it didn't
  write will miss a deleted 20-frame settle wait. → **Deterministic proof, not opinion.**
- **Rework ping-pong.** Cheap model fails → reviewer kicks back → context lost → repeat,
  and the orchestrator eventually reads the whole failure transcript at premium rates.
  → **One kick-back maximum, then the orchestrator takes it.**
- **LLM-reviewing-LLM theatre.** Nit-picking names while missing a race condition.
  → Gemini is for **research with checkable ground truth** (decomp, docs), not as the
  primary code gate.

**The decisive project-specific fact:** we already have the reviewer the critique says to
use — a **deterministic harness**: `story_harness.py --driver story`, `repro_*.py` A/B
scripts, `probe_*.py` state probes, `livetest.py` batches, `audit_flag_names.py`. That is
what makes delegation safe *here* when it isn't safe generically.

> **THE RULE THAT MAKES THIS WORK:**
> **Delegate only work whose success a harness/probe/test can prove without the premium
> model re-reading the codebase.** If the only way to know it worked is judgment, it stays
> on the premium tier.

---

## 3. Roles (tiers), scope, and structured returns

| Role | Tier | Does | MUST return (structured) |
|---|---|---|---|
| **Orchestrator** | PREMIUM | Plans, writes the spec + acceptance criteria, writes the critical/tricky code itself, runs the gate, owns docs/commits | — |
| **Explorer** | CHEAP | Finds files/symbols/call-sites; dumps map facts; triages long run logs to the 5 relevant lines | `{findings:[{file,line,why}], answer, gaps[]}` |
| **Implementer** | MID | Applies a FULLY-specified change to named files; no design decisions | `{diff_summary, files[], commands_run[], results, risks[], questions[]}` |
| **Verifier** | MID | Writes/extends a repro or probe that PROVES the change (A/B where possible), runs it, reports raw output | `{script, how_run, before, after, verdict, raw_tail}` |
| **Researcher** | EXTERNAL (Gemini) | Decomp/game-mechanics questions with checkable ground truth | prose → orchestrator verifies vs decomp/`audit_flag_names.py` |
| **Adversary** | EXTERNAL or MID | Tries to REFUTE a claimed fix; proposes the input that breaks it | `{refuted:bool, scenario, evidence}` |

**Never delegate (premium keeps these):**
- Diagnosing an intermittent wedge from a captured state (needs systemic inference).
- Anything touching `battle_handler.py`'s after-faint sweep, the KI-15 nudge, or the
  navigator's bail logic — small, load-bearing, timing-critical.
- Deciding *whether* a fix is faithful (§ faithfulness rules) or *whether* to move on.
- Doc judgment: changelog/mistakes/handoff wording (cheap to write, expensive if wrong).

**Safe to delegate (with a harness check):**
- Static recon: map warps/objects/connections, two-way pathability sweeps, flag audits.
- Log triage on multi-MB run logs ("find the frame where X first appears").
- Mechanical multi-site edits with an exact spec (rename, add a guard to N call sites).
- Writing a repro/probe scaffold from a described state.
- Drafting doc entries the orchestrator then edits.

---

## 4. The handoff contract (keeps premium context small)

**Orchestrator → worker** (never "go figure it out"):
```
TASK:        one sentence, imperative
WHY:         the user-visible symptom or goal (1-2 lines)
FILES:       exact paths (+ line ranges if known)   ← the single highest-value field
DO NOT:      files/areas off-limits; behaviors that must not change
ACCEPT:      the command that proves success + expected output
CONTEXT:     facts already established (so they aren't re-derived)
RETURN:      the structured schema for this role
```
Evidence (Gemini q4 §6, practitioner consensus): **context quality beats worker tier.**
A MID model with the exact files + a precise spec beats a PREMIUM model with a vague ask.
So the orchestrator's cheapest, highest-leverage act is writing FILES + ACCEPT well.

**Worker → orchestrator:** the role's schema, ≤ ~40 lines. No file dumps, no transcripts.
If a worker wants to paste a log, it must paste the ≤10 relevant lines.

---

## 5. Review gate (diff + evidence, never a re-read)

The orchestrator approves on **four checks only**:

1. **Proof ran.** The ACCEPT command was executed and its raw output is in the report.
   No output = automatic kick-back (not a judgment call).
2. **Scope.** `files[]` ⊆ FILES. Anything else touched = kick-back.
3. **Blast radius.** Read the diff for: removed waits/guards/bounds, changed loop
   conditions, changed press/timing cadence, new unbounded `while`. These are this
   project's historical bug shapes — a diff-only check catches them.
4. **Faithfulness + docs.** Natural-gameplay first; state-writes only as documented
   fallback; bounded loops; changelog/mistakes entry present if a bug was fixed.

**Kick-back budget = 1.** On a second failure the orchestrator does it itself. (Prevents
the ping-pong tax where premium ends up reading the whole failure transcript anyway.)

**Gemini's verdict is advisory, never blocking.** Reconcile: if Gemini and the harness
disagree, the **harness wins**. If Gemini and the reviewer disagree on a *fact* (a decomp
detail), verify it directly — that's how KI-17's diagnosis was accepted (it was checkable)
and how the phantom flag names were rejected.

---

## 6. Metrics — is it actually working?

Track these; "premium tokens saved" alone is a vanity metric:

| Metric | Target | Meaning if it drifts |
|---|---|---|
| **Override rate** — % of delegated work the orchestrator rewrites within a session | < 15% | Delegation boundary is wrong; pull work back |
| **Kick-backs per task** | ≤ 1 | Specs are too vague (fix FILES/ACCEPT, not the worker tier) |
| **Read:write ratio of premium tokens** | reading ≪ writing | Reviewer is re-hydrating context = design failure |
| **Escaped-bug rate** (intermittent bugs found *after* a gate passed) | ~0 | Cheap tier is producing plausible-wrong code the gate misses → stop delegating that class |

Record these in the changelog entry for any session that used orchestration.

---

## 7. Adding a new top model (e.g. an "Opus 5")

**Status 2026-07-24:** the authoritative model catalog (cached 2026-06-24) lists
Fable 5, Mythos 5 (Project Glasswing only), Opus 4.8/4.7/4.6, Sonnet 5, Sonnet 4.6,
Haiku 4.5 — **no "Opus 5."** No live Models API access from this machine (no
`ANTHROPIC_API_KEY`, no `ant` CLI) to check whether one launched in the last month. So:
do not wire an unverified model id — **verify first, then edit one table row.**

Decision procedure (cost-per-unit-of-quality, not headline price):
1. Verify it exists: `ant models list`, or `client.models.retrieve("<id>")`, or the
   Models Overview doc. Never guess an id — a wrong id 404s.
2. Slot it by price/capability into §1's table. If it beats the current PREMIUM row on
   **first-pass success rate per dollar**, it becomes PREMIUM; else it doesn't move in.
3. Measure on OUR work, not benchmarks: run one real chapter-build task at the candidate
   tier and compare (a) kick-backs, (b) escaped bugs, (c) premium tokens burned.
4. A new top model is worth it exactly when it removes retry loops. If the current
   pipeline already lands first-pass, a pricier orchestrator buys nothing.

---

## 8. Anti-patterns (these silently blow the premium budget)

- Orchestrator reading files a worker already read (re-hydration). Ask the worker.
- Delegating without FILES — the worker greps the repo at your expense in wall-clock and
  its own tokens, then guesses.
- Re-running a full 5M-frame batch to check a 3-line fix (use the captured `.ss1` + probe).
- Rebuilding the orchestrator's system prompt mid-session (kills prompt caching).
- LLM-vs-LLM debate loops with no deterministic tiebreak.
- Delegating the *diagnosis* of a timing bug (as opposed to the recon around it).
- Letting a worker "improve" adjacent code — scope creep is the #1 kick-back cause.

---

## 9. How to run it

- `/orchestrate <task>` — the recipe (`.claude/commands/orchestrate.md`).
- Agents: `.claude/agents/{explorer,implementer,verifier,reviewer}.md` — each pinned to a
  tier via its `model:` frontmatter (edit those 4 lines when the tier table changes).
- Gemini: `py -3.12 tools/story-dev/gemini_relay.py --file q.md --out a.md` (parallelizable;
  see §5 for how its answers are weighted). ‼ Gemini is STALE on model/pricing facts —
  never use it for those; it claimed "no Claude 5 family exists."
- **Fable-5 note:** when the orchestrator is Fable 5, expect long single turns and plan
  timeouts/progress accordingly; prompts written for older models are often *too*
  prescriptive and reduce its output quality — state the goal + constraints, not the steps.

---

## 10. Honest expectation

Realistic outcome on this project: **~50-70% fewer premium tokens** on chapter-build work
(recon + mechanical edits + log triage + test scaffolding move off-tier), with quality
held **because the harness — not a model's opinion — is the gate**. On intermittent-bug
diagnosis, expect ~0% delegation and no savings; that work stays premium by design, and
trying to delegate it is how quality actually drops.
