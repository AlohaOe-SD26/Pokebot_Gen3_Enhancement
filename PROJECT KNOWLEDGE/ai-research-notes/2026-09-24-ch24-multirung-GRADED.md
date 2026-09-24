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
| P4 | exp leak **< 10 %** to non-trainees | ✅ **CONFIRMED, NARROWLY** | `exp_leak_pct = 8.94` (bench 6,910 / total 77,259) |
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

## ⚠ THE NUMBER TO WATCH: THE LEAK ROSE 4× AND P4 PASSED BY 1.06 POINTS

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
* **One trajectory.** A single deterministic run refutes decisively and supports weakly.
