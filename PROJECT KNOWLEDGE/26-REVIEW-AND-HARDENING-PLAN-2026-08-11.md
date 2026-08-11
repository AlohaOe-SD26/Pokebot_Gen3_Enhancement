# 26 — PROJECT REVIEW & HARDENING PLAN (2026-08-11)

> **Point-in-time review**, commissioned by the user to (1) audit documentation and intent, (2)
> review 26 days of progress, (3) analyse the errors made and harden the directives against
> repeats, and (4) set the future path. Written against the north star in
> `01-VISION-AND-DESIGN.md`: **an organically-faithful Emerald player, and a documented substrate
> for a future self-training AI agent.**
>
> Everything here is either **MEASURED** (a number I computed during this review) or marked as
> judgement. Nothing is asserted from memory.

---

# EXECUTIVE SUMMARY — the five things that matter

1. **The project is ~2/3 through its primary goal.** Story mode plays from Littleroot to the Magma
   Hideout — 6 of 8 badges, 16 of 24 ladder beats. Nine beats remain, including two gyms, Victory
   Road and the Elite Four.
2. **The engineering discipline here is genuinely strong**, and it is not rhetoric: **87
   `repro_*.py`** structural tests, **40 probes**, **51 scripts that fail hard**, and a mistake log
   with **164 entries in 26 days**. Most projects have none of this.
3. **‼ THE CENTRAL FINDING: writing a prevention rule does not prevent the repeat.** At least
   **12 of the 164 mistakes are self-admitted repeats**, and in several the author states the rule
   *already existed* when they broke it. The rules that actually held are the ones **converted into
   code that refuses**. This is the single highest-leverage change available.
4. **The current-state documents have decayed into archives.** `04-HANDOFF.md` is **3,239 lines of
   which only the first 163 (5%) are current**, and it carries **three competing "START HERE"
   banners**, two stale by 11 days. `03-PUNCH-LIST.md` is 3,252 lines, **~48% already-done items**.
   This directly taxes every future session and every future agent.
5. **The measurement problem is unresolved and is the main strategic risk.** Finish rate has never
   produced a resolvable result in ~8 batches. Battle-level metrics work; run-level ones do not.

---

# PART 1 — WHERE THE PROJECT ACTUALLY IS

## 1.1 Story mode: measured position
| | |
|---|---|
| built and driven | Littleroot → 6 badges → Mt. Pyre → **Magma Hideout (Groudon awakened)** |
| ladder beats done | 16 of 24 (`12-STORYMODE-DESIGN.md` §2) |
| next beat | **§Ch16 Slateport Harbor** — specced, planned, anchor verified, **no code yet** |
| remaining | Aqua Hideout (17) → Mossdeep + Space Center (18) → **Gym 7** (19) → Seafloor Cavern (20) → Sootopolis/Rayquaza (21) → **Gym 8 Juan** (22) → Victory Road (23) → **Elite Four** (24) |

‼ **The back half is harder than the front half**, and the docs should say so plainly: beats 18-24
require **Dive** (HM08), heavy Surf/Waterfall traversal, two **double battles** (Steven tag, Tate &
Liza), and an Elite Four that is five consecutive un-fleeable boss fights with no heal between
them. Every unresolved boss-response weakness compounds there.

## 1.2 What is PROVEN vs what is ASSUMED
This distinction is the project's own standard and it is worth restating as a scoreboard.

**Proven (driven, with a control):** the chapter ladder to Magma Hideout; the counter chain's
mechanism (39.1% real conversion); `#24-battleitems` firing (86 events); the teach fix (A/B);
KI-51's guard (live, 2,209 frames vs a 60,000 bound); the status telemetry (0/290 false positives).

**Assumed / unmeasured — and each is a live risk:**
* **No outcome metric exists for ANY of the three changes promoted today.** A batch is running now
  to produce the first.
* KI-52's fallback has **no live A/B** (the reproduction was lost).
* The status tax is measured at **64.3% of incapacitated turns lost** — but over ~2 distinct
  battles. The instrument is validated; the rate is not.
* Roster hygiene is **blocked** (KI-54): the box is empty and the deposit path was already measured
  harmful.

---

# PART 2 — THE ERROR TAXONOMY (164 mistakes, 26 days)

Every heading in `08-MISTAKES.md` was read and grouped. The families, largest first:

| # | family | what it looks like | representative entries |
|---|---|---|---|
| **A** | **Invalid instrument / wrong metric** | the number measured something other than what was claimed | budget tuned 4× against a figure from a different loop; "clean verdict" on the wrong metric; values instrumented without UNITS; rich-wrapped stdout read as zero; **the Grep tool's silent zero on `x4-runs/`**; "ALREADY PROVEN" with no n; two losses read as a RATE |
| **B** | **Silent failure — a guard that cannot tell "no" from "I broke"** | bare `except`, a stub missing a constant, a flag that parses and does nothing | `except` hid a NameError for two batches; a test stub disabled the logic under test **twice**; a partial mock; an assertion that also passes when the process dies |
| **C** | **Removing/altering something that was WORKING** | a feature justified by what it saves, never costed | party stripped on every heal (**finish 47%→5%**); a WINNING lead removed on one loss; **"THIRD removal-shaped feature in a week"**; a component removed on a 7→8 reading |
| **D** | **Trusting a model/proxy over the game** | the map API, a static planner, or memory instead of observed state | `map_name` read as identity (a GYM logged as a CITY); a static PASS on a runtime WALL (**third wrong answer about the same door**); reachability probed with a tool that cannot cross warps; a Hoenn route asserted from memory |
| **E** | **Fixture / anchor invalidity** | the state under test was not the state believed | the "cheap repro" silently invalidated; a fixture pinned **after** a job overwrote it; a post-Mt-Pyre question answered from a badges-1-3 save (7 probes) |
| **F** | **Unbounded or self-referential control flow** | loops with no bound, or recovery that calls itself | recovery hooked into the function recovery calls (infinite); a branch-local guard bounding a multi-branch loop; a 110k-frame menu stall; an every-frame "nudge" that was an A-mash |
| **G** | **Over-generalising from one observation** | n=1 promoted to a finding | a structural cause inferred from ONE confound; a threshold calibrated on one example; a travel fix validated only from the EASY start |
| **H** | **Doc ↔ reality drift** | the documentation described a world that no longer existed | docs described 2 folders while the code had 3 **for ten days**; a comment asserting a lifetime the code never enforced; a trap walked into that was commented **three lines above** |

## 2.1 ‼ THE REPEAT RATE — the finding that should drive everything

**At least 12 of the 164 entries are explicit, self-admitted repeats**, and the wording of several
is damning because the author knew the rule at the time:

> *"I removed a WINNING behaviour for **the second time in a week, having already written the rule
> against it**"* (2026-08-04)
> *"I named the wrong 8th gym leader, in a table I wrote from memory **an hour after writing a rule
> against exactly that**"* (2026-07-26)
> *"A test stub missing a constant disabled the logic under test, SILENTLY — **the second time**"*
> (2026-07-30)
> *"**THIRD** removal-shaped feature in a week that cost more than it saved"* (2026-08-05)
> *"the **THIRD** wrong answer about the same door"* (2026-08-10)

And on **2026-08-11 alone**, family E fired **three times in one day** — the third instance occurring
*after* I had written the prevention rule for the first, and *while* holding the file I was about to
mis-pin.

⇒ **CONCLUSION: an advisory rule in a document has a measurably poor prevention rate.** It is not
useless — it makes diagnosis fast once the mistake recurs — but it does not stop the recurrence.

## 2.2 What DID work: structural impossibility

The project already proved the alternative, and even documented the moment:
`08-MISTAKES.md` **2026-07-25 — "RETIREMENT NOTICE: four prevention rules whose mistake is now
structurally impossible."** Rules were *retired* because code made the error unreachable.

Existing structural enforcement, measured:
| mechanism | count / effect |
|---|---|
| `repro_*.py` structural tests | **87** |
| scripts that **fail hard** (`sys.exit(1)` / `SystemExit`) | **51** |
| `probe_*.py` with built-in controls | **40** |
| `gemini_relay.py` model floor | **refuses in code** — the documented case where a doc rule failed and code succeeded |
| `verify_fixtures.py` + `FIXTURES.md5` | new 2026-08-11, closes family **E** |

**`gemini_relay.py` is the canonical precedent** and its own comment says it outright: *"A doc rule
was not enough — the default was already correct and an agent still overrode it… on ~35 calls."*

---

# PART 3 — THE HARDENING PLAN (advisory → structural)

Ranked by *(repeat frequency × cost of the repeat) ÷ effort*. Each item names the family it closes.

### TIER 1 — do these first; they close the families that actually repeat

**H1. A pre-flight gate script — `preflight.py`** *(families A, E, H)*
One command every session runs before touching anything, that **fails hard**:
* `verify_fixtures.py` (PINNED saves unchanged)
* git sync state (behind/ahead/diverged) — already a hook, make it blocking
* the doc-rule linter from **H2**
* "is a batch running?" → if yes, refuse edits to `sandbox-pokebot/`
‼ It must EXIT 1, not warn. Warnings are advisory rules with extra steps.

**H2. A documentation linter — `lint_docs.py`** *(families H + the doc decay in Part 4)*
Mechanically enforceable rules, all currently violated:
* a CURRENT-STATE file (01-05) must contain **no `# HISTORY` blocks** and **at most one**
  "START HERE"/"YOU ARE HERE" banner → *04-HANDOFF currently has 3*
* no `- [x]` done items in `03-PUNCH-LIST.md` older than N days (move to changelog)
* every claim line containing a percentage or a ratio must carry an **`n=`** or a source tag
  → this is the direct fix for *"an ALREADY PROVEN row with no sample size"*
* every `[~]` partial item must name what remains

**H3. A "removal guard" checklist, enforced in the punch list** *(family C — 3+ repeats, worst cost)*
Family C caused the single worst measured regression in the project (**finish 47% → 5%**). Any item
whose change *removes, disables, deposits, skips or narrows* anything must carry, **before it may be
marked done**, a `COST:` line stating what it takes away and the measurement that bounds it.
`lint_docs.py` enforces the presence of the line; a human judges its content.

**H4. Ban the bare `except` in new bot code** *(family B — 2+ repeats, silent)*
A `repro_no_silent_except.py` that greps `sandbox-pokebot/modules/story/` and the strategies for
`except Exception:` / `except:` **without** either a `raise`, a `log(`/`debug_logger` call, or an
explicit `# noqa` justification comment. The project already uses `# noqa: BLE001` with a reason —
this makes that convention load-bearing instead of optional.

### TIER 2 — high value, more effort

**H5. Make `n=` structural in the telemetry, not the prose** *(families A, G)*
Every analysis probe should print its own sample size and its control alongside every rate — as
`probe_status_tax.py` now does. Retrofit `analyse_*.py`. A rate without an n should be impossible to
*emit*, not merely discouraged.

**H6. A fixture provenance record** *(family E)*
Extend `FIXTURES.md5` so each PINNED save records **the run that produced it** and **the md5 of the
telemetry that measured it**. Then "is this the save my result came from?" is a lookup, not a memory.

**H7. Bound-by-construction loop helper** *(family F)*
A `bounded(iterable, cap, on_exhaust)` helper used by every wait loop, so an unbounded loop is a
code smell that stands out rather than the default shape.

### TIER 3 — worth doing, lower urgency
**H8.** Retire prevention rules whose mistake is now structurally impossible (the 2026-07-25
precedent) — a stale rule costs context and dilutes the ones that matter.
**H9.** A single `METRICS.md` naming, for each question the project asks, *which instrument answers
it and at what n* — the standing cure for the measurement problem in Part 5.

---

# PART 4 — DOCUMENTATION HEALTH (measured this review)

| finding | measurement | severity |
|---|---|---|
| **`04-HANDOFF.md` is 95% archive** | 3,239 lines; current state ends at line 163 | **HIGH** — it is the #1 file every session reads |
| **Three competing "START HERE" banners** | lines 11, 780, 1051; two stale by 11 days | **HIGH** — actively misleading |
| **`03-PUNCH-LIST.md` is ~48% done items** | 100 `[x]` / 86 `[ ]` / 21 `[~]`, 3,252 lines | MED |
| `05-KNOWN-ISSUES.md` growing without retirement | 2,416 lines; KI-1..KI-55 with no "closed" section | MED |
| Doc-number collision | `15-ESCALATION-RESEARCH` vs a new `15-` created this session (renumbered to 25) | LOW (fixed) |
| Vision did not state the AI-agent north star | fixed this session | was **HIGH** |

**The rule being violated is the project's own** (`CLAUDE.md`): *"01, 02, 03, 04, 05 are
CURRENT-STATE files: edit them in place so they always describe present reality. **Remove stale
content.**"*

**Recommended remedy (safe, reversible):** move each stale banner into `07-CHANGELOG.md` (which is
append-only and already holds most of it) and cut the current-state files to present reality.
‼ **Do this as its own commit, touching nothing else**, so it can be reverted cleanly — and take a
restore point first.

---

# PART 5 — THE STRATEGIC RISK: the measurement problem

Stated plainly because it governs everything else: **the project cannot currently measure whether a
change improves outcomes.**

* Finish rate has been unresolvable in **every** batch: 25.0 → 33.3 → 16.1 → 28.6 → 19.4 → 17.2%,
  no pair significant. Resolving a 10-point change needs **~300 runs ≈ 30 hours of batching**.
* Battle-level metrics have **~800 samples per batch** and *do* resolve (the counter-chain fence:
  z = +3.24).
* ⇒ **Every mechanism change must be graded on a battle-level metric.** This is already written down;
  H5 makes it structural.

‼ **This is why the "faithful/organic" north star is strategically sound**: story content is
**binary and instantly verifiable** ("did `GROUDON_AWAKENED` get set?"), so content work does not
depend on the broken instrument. Outcome tuning does. **Prefer content until the instrument
improves.**

---

# PART 6 — FUTURE PATH

## 6.1 Story mode (the primary goal)
1. **§Ch16 Slateport Harbor** — ready to build; only the code is missing. Watch KI-53 (the
   ROUTE110 → SLATEPORT last mile).
2. **Beat 17 Aqua Hideout** — large: room keys, Electrode puzzle.
3. **Beats 18-19** — Mossdeep, Space Center, **Dive (HM08)**, Gym 7 (double battle).
4. **Beats 20-22** — Seafloor Cavern, Sootopolis, Gym 8.
5. **Beats 23-24** — Victory Road, **Elite Four** (five consecutive un-fleeable bosses).

‼ **The boss-response question gates the back half.** It is deferrable now and not at beat 24.

## 6.2 The AI-agent substrate (the second north star)
What this repo must produce for the future self-training agent, and where it already does:
| the agent will need | where it lives today | gap |
|---|---|---|
| the sensorimotor contract (memory reads, flags/vars, tasks, button timing) | `02-ARCHITECTURE`, `12-STORYMODE-DESIGN` §AA, the probes | **no single "INJECTION SURFACE" document** |
| what faithful play *means* operationally | `14-AGENT-PLAYBOOK` faithfulness rules | scattered; worth consolidating |
| negative results — what was tried and failed | `08-MISTAKES` (164), refutations, retractions | **strong; the project's most valuable asset** |
| why, not just what | `06-DECISIONS-LOG` | good |
⇒ **Proposed new doc: `27-INJECTION-SURFACE.md`** — the one place describing how the bot observes
and acts on the game. It is the highest-value missing artefact for goal #2, and it is mostly
assembly of things already known.

---

# PART 7 — RECOMMENDED SEQUENCE

| # | action | why now |
|---|---|---|
| 1 | **Read the batch** when it lands | first outcome evidence for 3 promoted changes + the status-tax rate |
| 2 | **H2 `lint_docs.py` + the 04-HANDOFF cut** | biggest per-session tax; safe; reversible |
| 3 | **H1 `preflight.py`** | closes families A/E/H mechanically |
| 4 | **H3 removal guard + H4 no-silent-except** | closes the two families with the worst measured cost |
| 5 | **Build §Ch16** | resumes the primary goal on a de-risked path |
| 6 | **`27-INJECTION-SURFACE.md`** | the missing substrate for goal #2 |
| 7 | boss response | only with the batch's rate in hand; gates beats 20-24 |

**What I deliberately do NOT recommend:** re-enabling the PC deposit path, any battle-policy change
before the batch, or grading anything on finish rate.
