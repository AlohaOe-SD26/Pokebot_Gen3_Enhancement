# 30 — METRICS: which instrument answers which question, and at what n

> **Current-state file.** Before measuring anything, find the question here. If it is not here, the
> instrument probably does not exist yet — say so rather than reaching for the nearest number.

---

# ‼‼ WHY THIS FILE EXISTS

**Family A of the 2026-08-11 error taxonomy — "invalid instrument / wrong metric" — is the largest
family in the project.** A sample of what it produced:

* a budget **tuned four times** against a figure that was measuring a *different loop*;
* a "clean" verdict on the wrong metric that **hid a total finish-rate collapse for a day**;
* values instrumented **without their UNITS**, making a wrong comparison look verified;
* an acceptance bar computed a **different way** than the check that graded it;
* **"ALREADY PROVEN"** written down with **no sample size** — and n was 1;
* two losses read as a **RATE** when all runs were byte-identical (n was 1 again).

⇒ The cure is not "be careful". It is **knowing, before you start, which instrument can answer the
question you actually have — and which cannot.**

---

# ‼ THE ONE THING TO INTERNALISE

**The finish rate cannot resolve anything this project has ever asked of it.**

| batch series | finish rate |
|---|---|
| eight batches, ~30 runs each | 39.1 / 36.0 / 41.7 / 25.8 / 28.6 / 25.0 / 33.3 / 19.4 / 17.2% |
| pairs that reached significance | **zero** |

At ~30 runs a batch, resolving a **10-point** change needs roughly **300 runs ≈ 30 hours of
batching per question**. Battle-level metrics collect **~800 samples per batch** instead — which is
why the counter-chain fence resolved cleanly (`CAUGHT Machop` 0/7 → 6/7, **z = +3.24**) while every
finish-rate comparison around it did not.

⇒ **Grade mechanism work on battle-level metrics. Treat finish rate as a lagging indicator only,
and never quote it as evidence for a feature.**

---

# THE DECISION TABLE

| the question you have | the instrument | typical n per batch | resolvable? |
|---|---|---|---|
| **"Is this chapter complete?"** | a **story flag / var** read directly (`GROUDON_AWAKENED_MAGMA_HIDEOUT`, `SLATEPORT_HARBOR_STATE == 2`) | **1** | ✅ **YES — binary.** n=1 is sufficient because the outcome is not stochastic |
| "Did this mechanism FIRE at all?" | count its own log events (`[ITEM] using`, `TEACH OK`, `[KI-52]`) | 10s-100s | ✅ yes — presence is binary |
| "Did the counter chain CONVERT?" | `analyse_conversion.py` — hunts started vs `counter hunt CAUGHT` | 20-35 hunts | ⚠ marginal; the fence's z=+3.24 resolved, smaller effects will not |
| "Did boss win rate change?" | per KEY GROUP (leaders, Elite Four, rivals, Magma/Aqua) won/(won+lost), a Draw counted as lost, plus per-trainer first attempts: `probe_item_index_space.py` / `probe_boss_healing.py` (`#27-itemprobes`); before `[TRAINER]` telemetry, boss-length battles from `[BATTLE] ended` | ~800 battles | ✅ yes |
| "Do bosses heal, and how much?" | `probe_boss_healing.py` (opponent HP deltas in turn records, per battle class since `#27-itemprobes`) | 1,000+ heal events | ✅ yes |
| "Does the party arrive hurt?" | `probe_fainted_ace.py` (`[BATTLE] started hp=`) | ~16,700 battles | ✅ yes |
| "How many turns are lost to STATUS?" | `probe_status_tax.py` | ‼ **28 so far** | ❌ **NOT YET** — instrument validated (0/290 false positives on the clean control), rate needs independent battles |
| "Which item index space is right?" | settled by KI-101 (2026-09-16); `probe_item_index_space.py` now reports battle-level item OUTCOMES per class (`#27-itemprobes`) | ~114 requests per batch (0927) | ⚠ marginal per class |
| "Did the badge funnel move?" | `analyse_badge_funnel.py` (rung-by-rung) | 30-45 per rung | ❌ rarely — no rung has ever reached significance |
| **"Did the FINISH RATE improve?"** | — | ~30 runs | ❌ **NO. Do not ask this question of a batch.** |
| "Is this save the right ERA?" | a purpose-built probe with a NAME control, an ERA control and a PATH control (`probe_ch16_anchor.py`) | 1 | ✅ yes — binary, with controls |
| "Is this fixture the bytes I measured on?" | `verify_fixtures.py --assert name=md5` | 1 | ✅ yes |

---

# ‼ RULES FOR ANY NEW MEASUREMENT

1. **State n beside every rate. Always.** A percentage without an n is not a measurement, and
   "ALREADY PROVEN" without one is how a single lucky run became settled fact.
2. **Prove the samples are INDEPENDENT before calling anything a rate.** md5 the telemetry across
   runs. A `.ss1` replays identically, so *one fight repeated five times is still n = 1* — this
   produced both the withdrawn "wins 1 in 3" and the mis-scoped status-tax figure on 2026-08-11.
3. **Every instrument needs a CONTROL** — a case that must come out the other way. `probe_status_tax`
   is trustworthy because its clean bucket reads **0 of 290**; without that, 64.3% would mean
   nothing. A probe that returns FAIL for everything has found a common *symptom*, not a cause.
4. **Compute z before claiming a difference.** Two proportions, `z = (p1-p2) / sqrt(p(1-p)(1/n1+1/n2))`.
   |z| < 1.96 is **not resolvable** — say "directional only", never "improved".
5. **Pre-register the acceptance bar, and compute it the same way the check does.** The
   `#24-pcoverflow` batch failed its own pre-registered target honestly; by contrast a celebrated
   "15% → 50%" was computed on *reported* catches and had to be restated as 15.2% → 45.0% once
   recomputed on *real* ones.
6. **Name the SURFACE.** `*/stdout.txt` and `*/debug-logs/*.log` carry different facts, and debug
   logs are only copied into the run dir when the batch ends.
7. ‼ **Never use the Grep TOOL on `tools/story-dev/x4-runs/`** — it is gitignored and ripgrep
   returns a silent **zero**. Use Bash `grep`, and print the size of what you searched as a control.
   (This one caused an agent to be accused of fabricating data.)

---

# WHAT IS CURRENTLY UNMEASURED — stated so it is not mistaken for measured

| thing | status |
|---|---|
| `#24-teachmsgstall`, KI-51, KI-52 | promoted; **no batch has ever run with them in** |
| KI-52's fight-it-out fallback | **structurally proven only** — the live A/B was voided |
| the status tax as a RATE | instrument validated; **n = 28 over ~2 distinct battles** |
| `#24-battleitems` outcome | mechanism proven (86 events); **outcome never resolved** |
| whether roster hygiene would help | **blocked** — the box is empty because `POKEBOT_BOX_OVERFLOW_CATCH` is off (KI-54) |

⇒ **A batch running on 2026-08-11 is the first that can speak to the top three rows.**
