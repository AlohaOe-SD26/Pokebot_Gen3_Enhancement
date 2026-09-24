# PRE-REGISTERED PREDICTIONS — the §Ch24 MULTI-RUNG climb

**Written 2026-09-24, BEFORE the drive.** Committed first so a contradicting reading is a **RESULT**,

DRIVER: ch24train

⛔⛔ **THE `GRADED-BY:` LINES BELOW WERE ADDED RETROACTIVELY ON 2026-09-24, AND SAYING SO IS THE POINT.**
The predictions themselves are unchanged — only the annotation naming each falsifier's reading key is
new. ‼ **Two of those keys did not exist when this file was pre-registered:** `exp_leak_pct` and
`pp_predicate_true` were built into `Ch24TrainMode` *after* the first drive came back, because **P3
and P4 defined their falsifiers over an exp split the driver never recorded** — the 2.2 % baseline P4
quotes came from a different driver (`Ch24SwapTriggerMode`). ⇒ this file is the worked example of the
rule it now carries, and gate **#72 (`probe_predictions_gradeable.py`)** exists so the next
predictions file cannot repeat it: every prediction must name the reading that grades it, and that
reading must be one the chosen driver actually writes.

not a driver failure — the standing rule in `.claude/skills/story-drive`.

---

## WHY THIS DRIVE, AND WHAT IT CLOSES

The leg has been driven twice, both at `floor=21`: **one rung**. Everything below is untested.

| gap | why it matters |
|---|---|
| the **multi-rung loop** | `train_team` never re-picks its ground; the rung loop is the whole reason the leg exists |
| **ROUTE115 / ROUTE118** | both are **SURF** rungs — their spin tiles are water. Nothing has driven a surf approach |
| **VICTORY_ROAD_1F** | the economics say it carries **73-94 %** of the real climb. Never driven as a training ground |
| the **PP-dry regime** | Zigzagoon's 80 PP lasts **~44 battles**. Every drive so far stopped at 29 |

⇒ `floor=40` crosses **five grounds** and ~306 battles — past every one of those thresholds —
without paying for the full ~21 h climb to L65.

**THE DRIVE:** `--driver ch24trainclimb` (a `floor=40` variant of `ch24train`), fixture
`post_ch24_atdoor_L75.ss1`, Zigzagoon **L19**.

---

## PREDICTIONS, each with the falsifier that would refute it

### P1 — the leg visits **at least four distinct grounds**.
GRADED-BY: leg_rungs
Predicted order from the production picker: ROUTE117 → ROUTE111 → ROUTE115 → ROUTE118 → ROUTE121 →
(VICTORY_ROAD_1F at L39).
**FALSIFIER:** one ground for the whole climb ⇒ the rung loop is not re-picking, and `train_team`'s
fixed `grass` is silently winning. That would make the leg no better than a single call.

### P2 — ⭐ **the two SURF rungs are reached.** ROUTE115 (spin tile `(6,53)`) and ROUTE118 (`(29,15)`) are water tiles; the approach must mount Surf.
GRADED-BY: leg_rungs
**FALSIFIER:** `no_ground` or `no_anchor` recorded for either ⇒ the ladder has a hole at L25-L27 that
the static last-mile measurement did not predict, and the climb needs a different rung there.

### P3 — ⭐⭐ **THE ONE THAT CLOSES `#24-ppscope`: the trainee's PP goes dry, and the leg HEALS rather than degrading.**
GRADED-BY: pp_predicate_true, pp_predicate_calls, exp_leak_pct
`heal_on_lead_pp=True` is passed. Past ~44 battles the all-quantified `_team_is_out_of_pp()` cannot
fire on a bench of L75s; only the new trainee-scoped term can.
**FALSIFIER — and this is the decision point:** if the exp split shows a **finisher banking a large
share**, the PP term is not firing in practice and the ladder degrades toward the 2-way cost exactly
as `#24-ppscope` predicted. That would mean the fix is correct as a predicate and **wrong in
motion** — and it is already promoted.

### P4 — the exp leak stays **small** (< 10 % to non-trainees).
GRADED-BY: exp_leak_pct, exp_to_bench, exp_to_trainees
At `floor=21` it was **2.2 %** over 14 battles. Over ~306 battles crossing the dry point, a rise
toward 50 % is the signature of P3 failing.
**FALSIFIER:** ≥ 25 % ⇒ swap-training is absorbing the climb and the ladder's premise is wrong at
scale, not just at the margin.

### P5 — **VICTORY_ROAD_1F is entered as a training ground at L39.**
GRADED-BY: leg_rungs
Its band is `(36, 40)`, so `max_wild_max = level + 1` admits it at L39 exactly.
**FALSIFIER:** it is never selected ⇒ my corrected reading of the out-level rule is still wrong, and
the economics (which give it 73-94 % of the work) are wrong with it.

### P6 — **no whiteouts.** The trainee always out-levels its band by construction.
GRADED-BY: whiteouts
**FALSIFIER:** any whiteout ⇒ the out-level rule does not make a trainee safe, and the leg needs a
survivability guard before the climb can be trusted unattended.

### P7 — the leg reports `floor_reached=True` with `still_below=[]`.
GRADED-BY: leg_floor_reached, leg_still_below, leg_all_visited
**FALSIFIER:** `rung_cap_hit`, `no_progress`, or a purse expiry ⇒ one of the three bounds I chose is
mis-sized, and the sizing came from ONE economics model.

---

## ⛔ WHAT THIS DRIVE STILL WILL NOT SETTLE

* **Castform is not trained.** `floor=40` leaves it at L36, below the real floor but above this
  drive's. Only Zigzagoon climbs.
* **It is one trajectory.** Rates from a single run have wide intervals; it can REFUTE decisively and
  support only weakly.
* **It stops at L40, not L65.** The longest single stretch of the real climb — VICTORY_ROAD_1F from
  L39 to L65, ~751 battles — is barely entered.
* **Trainer sight cones remain unmeasured** on every approach; the planner is structurally blind to
  them and these are trainer routes.
