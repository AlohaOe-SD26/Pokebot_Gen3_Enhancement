# GRADED — the §Ch24 MULTI-RUNG climb

Graded **2026-09-24** against `2026-09-24-ch24-multirung-PREDICTIONS.md`, which was committed
**before** the drive. Evidence: `tools/story-dev/evidence/2026-09-24-ch24climb-v2.stdout.txt` and
`…-v2.log`. Fixture `post_ch24_atdoor_L75.ss1` (`8b8cd907db09`, verified PINNED before the run).

**THE RUN:** `CH24_TRAIN_FLOOR=40 --driver ch24train --frames 2500000`
→ `ACCEPTANCE: PASS`, 7 readings, `missing=[]`, **264 battles, 0 whiteouts**, `failure=None`.

---

## ⛔ READ THIS FIRST: TWO DEFECTS THIS DRIVE FOUND, AND ONE IT FOUND IN THE PREDICTIONS

**(1) The leg could not train a SECOND mōn after training one inside Victory Road.** The v1 drive
climbed Zigzagoon L19→L40 across six grounds and then reported *"no reachable ground Castform
out-levels at L36"* — not a ladder hole, a **position** problem. `VICTORY_ROAD_1F` is
`map_type=Underground`, so `fly_is_legal_from_current_map()` is False ⇒ `can_fly_to_anchor` is False
⇒ `_training_area_allowed`'s **entire Fly disjunct fails for every ground**, and walking ≤4 hops from
inside a cave reaches nothing. Every `floor=21` drive missed this because none ever entered Victory
Road. ⇒ fixed by `_ch24_step_out_if_fly_illegal()` before each trainee's first ground pick.

**(2) The leg finished by leaving the bot INSIDE Victory Road.** With (1) fixed, both mōn trained —
and the leg still graded FAIL on `T-CONTINUE`, ending on `VICTORY_ROAD_1F (15,39)` with
`fly_legal_at_end=False` and no computable path to the League anchor (the exit is a door warp).
⇒ the same step-out is now a **postcondition** of `train_for_league`: *"trained the party"* and
*"left it able to proceed"* are different claims, and only the second is useful to the caller.
‼ The fix was made in the LEG, not in the CHECK — the check was right.

**(3) ⛔ TWO PREDICTIONS WERE UNGRADEABLE AS WRITTEN.** P3 and P4 define their falsifiers in terms of
an **exp split that `ch24train` never recorded**. The 2.2 % baseline P4 quotes came from a *different
driver* (`Ch24SwapTriggerMode`). The instrument was built before re-driving. See `08-MISTAKES.md`.

---

## THE GRADE

| # | prediction | verdict | the reading it rests on |
|---|---|---|---|
| P1 | ≥ 4 distinct grounds, in the picker's predicted order | ✅ **CONFIRMED** | 6 grounds, exactly `ROUTE117 → ROUTE111 → ROUTE115 → ROUTE118 → ROUTE121 → VICTORY_ROAD_1F` |
| P2 | both **SURF** rungs reached | ✅ **CONFIRMED** | `ROUTE115 25→27` and `ROUTE118 27→28`, both `finished: True` |
| P3 | PP goes dry; the leg **heals** rather than degrading | ⚠ **PARTIAL — see below** | `pp_predicate_true = 2` of `3365` calls |
| P4 | exp leak **< 10 %** to non-trainees | ⚠ **SPLIT — SEE THE CORRECTION AT THE END OF THIS FILE** | `exp_leak_pct = 8.94` (sandbox) vs **11.38** (custom) — one measurement each side of the line |
| P5 | `VICTORY_ROAD_1F` entered as a ground at **L39** | ✅ **CONFIRMED** | both trainees, `from: 39` |
| P6 | no whiteouts | ✅ **CONFIRMED** | `whiteouts=0` |
| P7 | `floor_reached=True`, `still_below=[]` | ✅ **CONFIRMED** | both, and `leg_all_visited=True` |

**Every rung `finished: True`** — 8 rungs across 2 trainees. `latch_calls=1`, `leg_latched=True`.

---

## ⚠ P3, PRECISELY — WHAT FIRED AND WHAT DID NOT

The trainee-scoped PP term **is live code in motion**: `lead_has_no_damaging_pp` returned **True 2
times** across 264 battles. That closes the half of `#24-ppscope` that mattered most — the predicate
was promoted *"proven as a predicate and unproven in motion"*, and it has now fired in motion.

⛔ **But the predicted REGIME did not materialise.** P3 expected that past ~44 battles the PP term
would carry the heal decision. It fired twice in 264. The reason is already on the record at
`03-PUNCH-LIST.md:605`: **the existing heal cadence keeps PP topped up**, so the trainee rarely
reaches dry. ⇒ the honest statement is *"the PP term is a live backstop that fires rarely"*, **not**
*"the PP-dry regime is now characterised"*.

‼ **AND THE COUNT IS AN UPPER BOUND, NOT A HEAL COUNT.** The predicate is evaluated up to twice per
heal decision (`early_game.py:2364` and `:2371`), so `true=2` means **one or two** PP-driven heals.

⛔ **WHAT THIS DRIVE STILL DOES NOT CLOSE.** `03-PUNCH-LIST.md:613` asks for the **trigger-2 firing
rate split HP-driven vs PP-driven**. That is a different code path — `SwapTrainBattleStrategy
.decide_turn`'s `(underleveled or cant_continue)` — and this drive does not instrument it. What the
drive *does* settle is the **outcome** that split was wanted for: across 264 battles including the
dry point, **91.06 % of exp stayed with the trainees**. ⇒ the mechanism split remains open; the
consequence it was meant to predict is measured.

---

## ⚠ THE NUMBER TO WATCH: THE LEAK ROSE 4× AND P4 PASSED HERE BY 1.06 POINTS — ⛔ BUT FAILED IN A
## SECOND RUN. READ THE CORRECTION AT THE END OF THIS FILE BEFORE QUOTING ANYTHING BELOW.

`floor=21` measured **2.2 %** over 14 battles. `floor=40` measures **8.94 %** over 264 — the same
direction P4's falsifier was pointed at, just short of the 10 % line and well short of the 25 %
refutation bar. One bench mōn (`FA51ECF3`) took **5,700 of the 6,910**, i.e. **82 % of all leakage**.

⛔ **Do not read 8.94 % as "the leak is bounded below 10 %".** This climb stops at **L40**; the real
floor is **L65**, and `VICTORY_ROAD_1F` carries 73–94 % of that climb — a stretch this drive barely
enters. The trend across the only two points we have is *upward*, so the L65 figure is unknown and
plausibly over 10 %. ⇒ re-measure `exp_leak_pct` on the first long run rather than assuming.

---

## ⛔ WHAT IS STILL UNDRIVEN

* **The full climb to L65.** This is `floor=40`. The longest stretch of the real climb —
  `VICTORY_ROAD_1F` L39→L65, ~751 battles — is barely entered.
* **The trigger-2 HP/PP mechanism split** (`#24-ppscope`'s remaining half).
* **Trainer sight cones** on every approach; the planner is structurally blind to them.
* **⛔ NOT "one deterministic trajectory" — SEE THE CORRECTION BELOW.** This said a single run *"refutes decisively and supports weakly"*, on the assumption that a repeat would reproduce it exactly. A second drive of the same fixture/driver/floor/profile did **not**: 253 battles vs 264, and `exp_leak_pct` 11.38 vs 8.94. ⇒ single-run percentages here carry real variance.

---

# ⛔⛔ CORRECTION, 2026-09-24b — **P4 IS REFUTED BY A SECOND MEASUREMENT**

The table above grades **P4 (exp leak < 10 %) as CONFIRMED, NARROWLY** on `exp_leak_pct = 8.94`. A
second drive — the promotion-verification run of the *same fixture, same driver, same floor, same
profile*, against `--build custom` — returned **`exp_leak_pct = 11.38`**.

| run | fork | battles | `exp_leak_pct` | P4 (< 10 %) |
|---|---|---|---|---|
| v2 | sandbox | 264 | **8.94 %** | ✅ passes |
| 2026-09-24b | custom | 253 | **11.38 %** | ⛔ **fails** |

⇒ **THE LEAK STRADDLES THE THRESHOLD, SO P4 AS STATED IS NOT SAFE.** Neither run approaches the 25 %
refutation bar, so the ladder's premise stands — but *"the leak is bounded below 10 %"* is now
**measured false**, and this file should not be read as having established it. The same bench mōn
dominates both runs: `Wailord#FA51ECF3` took **5,700 of 6,910** (sandbox) and **8,016** (custom).

**Revised verdict: P4 — ⚠ SPLIT. One measurement each side of its own line.**

## ⚠⚠ AND THE REASON THIS IS TWO MEASUREMENTS RATHER THAN ONE REPLAY

The two runs share fixture (`8b8cd907db09`), driver, floor and profile (`profiles/repro-ml`), and
after the promotion their `modules/` + `plugins/` Python is **byte-identical**. Their **rung structure
is identical** — same 8 rungs, same grounds, same level transitions. Yet **battles differ (264 vs
253) and every exp figure differs.**

⛔ `CLAUDE.md` rule 8 says *"identical output across runs is a determinism check, never a
replication"*. That rule assumes runs **are** identical. These are not, which cuts the other way:
**single-run percentages in this tree carry real variance and should be quoted with that caveat.**

‼ **THE CAUSE IS NOT ASSERTED HERE.** The two forks still differ outside the promotion's scope (root
scripts, `tests/`, `utility/`, `profiles/` contents), so this pair does not isolate fork-vs-harness.
A same-fork repeat was launched to settle it; its result belongs in this file when it lands.
