# Portable Multi-Agent Orchestration Guide
### Cutting premium-model spend in Claude Code without losing power, accuracy, or robustness

> **This document is deliberately project-agnostic.** It contains no Pokémon-bot specifics.
> Copy it into any Claude Code repo as-is. Everything project-specific lives in the four
> agent files and one command file it tells you to create, and those are ~20 lines each.
>
> Written 2026-07-24 from a real deployment (see §10 for the measured outcome, including
> what went wrong). Companion: the project-specific version lives in `16-ORCHESTRATION-PLAYBOOK.md`.

---

## 1. The premise, stated honestly

**Multi-agent orchestration does not reduce total token consumption. It usually increases it.**
More agents means more system prompts, more context copies, review passes, and rework.
Anyone promising "multi-agent = cheaper" is measuring the wrong thing.

What it actually buys you is **three separable wins**:

| Win | Mechanism | When it matters |
|---|---|---|
| **Premium-tier savings** | Bulk work executes on cheap models; the expensive model only plans + gates | Your constraint is a *premium quota*, not total spend |
| **Context isolation** | A sub-agent's file reads, greps, and dead ends never enter the orchestrator's window | Your constraint is the *context window* / session longevity |
| **Wall-clock speed** | Independent work runs concurrently | Your constraint is *time* |

Pick which one you're optimizing. The design below optimizes **premium-tier savings and
context isolation**, because those are the two that actually bite in long agentic sessions.

**The counterintuitive part:** the biggest saving is usually *not* the cheap model's lower
per-token price. It's that **the orchestrator never sees the 40k tokens of exploration** the
worker did to produce a 30-line answer. Context isolation beats price arbitrage.

---

## 2. The governing rule (everything else is commentary)

> ### Delegate only work whose success can be proven by something *deterministic*, without the premium model re-reading the codebase.

If the only way to know whether the work is correct is expert judgment, it stays on the
premium tier. No exceptions, no matter how well-specified it looks.

**Why this rule and not "delegate everything cheap":** an adversarial review of this design
(run before deployment, deliberately prompted to attack it) identified the failure that kills
naive versions — *the context re-hydration trap*. If your reviewer must load the codebase to
judge a diff, you pay premium rates for reading anyway and the entire saving evaporates. The
only escape is that **something other than the premium model** establishes correctness: a
test, a compiler, a linter, a type checker, a repro script, a benchmark, a schema validator.

**Corollary — this pattern's prerequisite:** you need a deterministic verification surface.
If your project has no tests and nothing mechanical that can say "this works," build that
*first*. Orchestration on top of an unverifiable codebase amplifies confident wrongness.

---

## 3. Tiers, not models

Never hardcode model names into roles. Define **tiers**, and map tiers → models in exactly
one table. When a new model launches you edit one row, not your whole workflow.

| Tier | Role in the system | Typical assignment |
|---|---|---|
| **PREMIUM** | Orchestrator, planner, final gate, the hardest code | Your best available model |
| **MID** | Implementer, test/proof writer, adversarial reviewer | Mid-tier coding model |
| **CHEAP** | Explorer, search, log triage, data extraction | Cheapest competent model |
| **EXTERNAL** | Research, second opinion from a *different model family* | A non-Claude API (e.g. Gemini) |

**Choosing a tier for a task — the reliable heuristic** (this held up across every task tested):

> **Extraction and translation are safe to delegate. Synthesis is not.**
>
> - *Extraction*: "find every call site of X", "what does this log say at frame N", "list the fields".
> - *Translation*: "convert this spec into a function", "write tests from these cases", "apply this rename".
> - *Synthesis*: deciding the design, resolving an ambiguity, inferring an unstated requirement,
>   diagnosing an intermittent bug. **← premium keeps these.**

**On adding a newly released top model:** do not adopt it on headline benchmarks. Adopt it if
it lowers **cost per unit of *first-pass-correct* work**. A pricier orchestrator pays for
itself only by removing retry loops; if your pipeline already lands first-pass, it buys
nothing. Verify the model ID exists before wiring it (a wrong ID just 404s) — and note that
external models are often *stale* about model catalogs, so don't ask one which models exist.

---

## 4. The five roles

Create these as agent definition files (`.claude/agents/<name>.md`). Each is ~20 lines of
frontmatter + charter. The charters below are generic; add your project's specific traps.

### 4.1 EXPLORER (CHEAP) — read-only recon
- **Does:** locates files/symbols/call-sites; extracts facts from data files; triages large
  logs down to the handful of relevant lines.
- **Never:** edits, judges, or diagnoses.
- **Returns:** `FINDINGS: [path:line — why]` / `ANSWER: 2-4 sentences` / `GAPS: what it couldn't determine`
- **Critical charter line:** *"Answer, don't dump."* Without this, cheap models paste whole
  files and you have re-created the context problem you were solving.
- **Second critical line:** *"Never guess a path, name, or identifier — say so in GAPS."*

### 4.2 IMPLEMENTER (MID) — executes a complete spec
- **Does:** applies a fully-specified change to named files; runs the acceptance command.
- **Never:** designs, expands scope, or "improves" adjacent code.
- **Returns:** `DIFF_SUMMARY / FILES / COMMANDS_RUN / RESULTS (raw output) / RISKS / QUESTIONS`
- **Critical charter lines:** *"Stay inside FILES — if the change needs another file, STOP and
  report it"* and *"Never remove or weaken a guard, wait, bound, or check unless told to."*
  Scope creep is the #1 cause of rejected work.

### 4.3 VERIFIER (MID) — produces evidence
- **Does:** writes/extends a test or repro that *proves* the change, runs it, reports raw output.
- **Never:** edits production code to make a test pass.
- **Returns:** `SCRIPT / HOW_RUN / BEFORE / AFTER / CONTROLS / VERDICT: PROVEN|PARTIAL|UNPROVEN`
- **Critical charter line:** *"A/B whenever possible — show the failure before the fix, and
  include a control proving the healthy path still works."* One-sided "it passes now" is weak.

### 4.4 REVIEWER (MID) — adversarial, diff-only
- **Does:** reads *only* the diff + the self-report + the evidence, and tries to break it.
- **Never:** re-reads the whole codebase (if it must, that's itself a finding).
- **Returns:** `VERDICT: APPROVE|KICK-BACK|ESCALATE / BLOCKERS / RISKS / MISSING_EVIDENCE`
- **Critical charter line:** *"Your job is to refute, not to praise."* Also give it your
  project's **historical bug shapes** — this is what makes a mid-tier reviewer genuinely
  useful instead of a name-nitpicker.

### 4.5 RESEARCHER (EXTERNAL) — different model family
- **Does:** answers questions with *checkable ground truth* (spec/protocol/API/domain facts).
- **Never:** acts as the blocking gate on code correctness.
- **Why a different family:** models share blind spots with their own family. A genuinely
  independent architecture catches things a same-family reviewer waves through.
- **Hard rule:** its output is a **lead**, verified against primary sources before use.

---

## 5. The handoff contract

This is where most of the value is. Evidence is consistent and strong: **context quality
dominates worker tier.** A mid model with the exact files and a precise spec outperforms a
top model given a vague ask. So the orchestrator's cheapest high-leverage act is writing this
well:

```
TASK:    one imperative sentence
WHY:     the user-visible symptom or goal (1-2 lines)
FILES:   exact paths (+ line ranges if known)      ← highest-value field in the whole system
DO NOT:  off-limits files; behaviors that must not change
ACCEPT:  the exact command that proves success + what its output must show
CONTEXT: facts already established (so they are not re-derived)
RETURN:  the role's output schema
```

**The readiness test:** if you cannot name `FILES` and an `ACCEPT` command, *the task is not
ready to delegate.* Scout more, or do it yourself. This single check prevents most failures.

**Return discipline:** ≤ ~40 lines, schema-shaped, no file dumps, no transcripts. If a worker
needs to show a log, it shows the ≤10 relevant lines.

---

## 6. The review gate

Approve on four checks, in order. Only #3 needs real thought — the rest are mechanical, which
is the point (mechanical checks are cheap in premium tokens).

1. **Proof ran.** Raw output from the ACCEPT command is present. Absent or paraphrased →
   automatic kick-back. *Not a judgment call.*
2. **Scope.** Files touched ⊆ FILES. Anything extra → kick-back.
3. **Blast radius.** Read the diff for *your project's* historical bug shapes. Generic
   starting set: removed/weakened guards, waits, or bounds; new unbounded loops; changed
   error handling; a new check that fires on the healthy path; reliance on a value that can
   be stale; silent behavior changes to paths that already worked.
4. **Docs/conventions.** Whatever your Definition of Done requires.

**Kick-back budget: ONE.** On a second failure the orchestrator takes the task over. This bound
is essential — without it you get *rework ping-pong*, where the premium model eventually reads
the entire failure transcript at premium rates, which is strictly worse than never delegating.

**Resolving disagreements:** deterministic evidence > premium reviewer > external reviewer.
If two models disagree about a *fact*, go verify the fact. Never let an LLM-vs-LLM debate run
without a mechanical tiebreak.

---

## 7. Metrics — detect silent failure

"Premium tokens saved" is a vanity metric; it looks great while quality quietly rots. Track:

| Metric | Healthy | What a bad value means |
|---|---|---|
| **Override rate** — % of delegated work the orchestrator ends up rewriting | < 15% | Your delegation boundary is wrong; pull that task class back |
| **Kick-backs per task** | ≤ 1 | Your specs are too vague — fix FILES/ACCEPT, not the worker tier |
| **Premium read:write ratio** | reading ≪ writing | The reviewer is re-hydrating context; the architecture isn't paying |
| **Escaped defects** — bugs found *after* a gate passed | ~0 | The cheap tier is producing plausible-wrong work your gate can't see. Stop delegating that class immediately |

Log a one-block ledger per orchestrated task: `DELEGATED / KEPT PREMIUM / KICK-BACKS /
OVERRIDES / EVIDENCE`. Without it you cannot tell whether the pattern is working.

---

## 8. Anti-patterns (each of these silently destroys the savings)

- **Re-reading what a worker already summarized.** The single most common failure.
- **Delegating without `FILES`** — the worker greps blindly, guesses, and you pay twice.
- **Delegating diagnosis** of intermittent/timing/state bugs. Cheap models generate confident,
  plausible, wrong causes, and a plausible wrong cause is worse than no answer.
- **Unlimited rework loops.** See §6.
- **LLM-on-LLM review as the *primary* gate.** It nitpicks names and misses race conditions.
  Use it as a *second* opinion behind a mechanical gate.
- **Re-running an expensive full validation to check a small fix.** Use the targeted repro.
- **Mutating the orchestrator's system prompt mid-session** — destroys prompt caching (cache
  reads are ~10% of input cost; this is a big, silent lever).
- **Orchestrating trivia.** If the task is <15 lines in one file, just do it — coordination
  overhead exceeds the saving. Have an explicit triage step that says so.

---

## 9. Adoption path (30 minutes into any repo)

1. **Confirm the prerequisite (§2):** identify the deterministic check that can prove work in
   this repo — test suite, compiler, linter, type checker, or a repro-script convention. If
   none exists, build it before adopting this pattern.
2. **Create the tier table** in a doc: tier → model, with prices. One row per tier.
3. **Create four agent files** (`.claude/agents/{explorer,implementer,verifier,reviewer}.md`)
   from §4. Pin each to a tier via `model:` frontmatter, restrict `tools:` to what the role
   needs (read-only roles get no write tools), and add your repo's traps and commands
   (interpreter invocation, how to run tests, which directories are off-limits).
4. **Create one command file** (`.claude/commands/orchestrate.md`) encoding: triage → scout →
   spec → implement → prove → gate → land → ledger.
5. **Run it on one real task and record the ledger.** Expect the first run to expose gaps in
   *your specs*, not in the workers.
6. **Feed every gate catch back into the reviewer's charter** as a named bug shape. This is
   what compounds — the reviewer gets sharper at your codebase's specific failure modes.

---

## 10. Measured outcome from the first real deployment (be sober about this)

One production task (two independent bug fixes in a mature codebase), run end-to-end through
the pattern. Delegated: 3 explorer recons, 1 implementer (data + a pure function), 1 verifier
proof, 1 adversarial review. Kept premium: triage, the spec, the judgment-dense wiring, all
thresholds, and the gate.

**Result: the gate caught six defects. Five originated in the orchestrator's own specs.**

| Caught by | Defect |
|---|---|
| Orchestrator's gate | Selector proposed an option gated behind an unmet prerequisite |
| Orchestrator's gate | "Verified" data was verified against the wrong invariant |
| Orchestrator's gate | A threshold would have silently changed already-working behavior |
| **Adversarial reviewer** | **Dead code left behind by a restructure, emitting a false log line** |
| **Adversarial reviewer** | A branch that couldn't be validated → changed to fail closed |
| Verifier's proof | 2 of 10 hand-written config entries were wrong |

**The three lessons that generalize:**

1. **The limiting factor was spec quality, not worker capability.** Every override traced to a
   disqualifier the spec omitted. When specifying a chooser/selector, enumerate the
   **disqualifiers**, not just the ranking metric — and make the acceptance command assert a
   case that must return *nothing*.
2. **The gate is the product.** Delegation moved grunt work off-tier successfully, but every
   single quality save came from the gate — the mechanical proof, the adversarial pass, or the
   orchestrator's own review. A version of this pattern without a hard gate would have shipped
   six defects while reporting a token saving.
3. **Cheap-tier output can contradict established ground truth and look authoritative.** One
   recon returned a confident, well-formatted table that was wrong (its sampling method was
   biased). It was caught only because the result contradicted something already known.
   **Always sanity-check delegated data against a fact you already hold.**

**Honest expectation:** substantial premium-token reduction on well-specified build/recon
work; **near-zero delegation, and near-zero savings, on diagnosis of subtle bugs** — that work
stays premium by design, and trying to delegate it is precisely where quality drops.
