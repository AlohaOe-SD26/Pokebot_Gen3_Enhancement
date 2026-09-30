# 2026-09-30 — USER RULING 26, design v2 step 10b (HK at Sootopolis): PRE-REGISTERED PREDICTIONS

DRIVER: earlybasket

> Filed BEFORE the code commit and before any graded arm. Branch `wt/kittopoff10b` (the design is
> `2026-09-29-kittopoff10b-DESIGN.md`, reviewed, committed `f52e1e5c`).
> ⚠ **Not blind for the gate:** `probe_kit_topoff_sootopolis.py` ran once before this file (49 rows + 46 mutants + 3
> no-ops, ALL PASS, every set exact on its first run). An adversarial mutant pass on it is RUNNING as this is filed.
> ⚠ **One smoke run happened before this file** (`--frames 400`, S-ON's flags): it printed the driver's PRE-KIT line
> (`forecast=[('Hyper Potion', 1)] raw=[] split=[] expected=[('Hyper Potion', 1)]`) and ended before any purchase.
> Those four values were already in the committed design. **Every graded arm below is blind.**

## HOW THE ARMS RUN
- The seed-1 wrapper, `--driver earlybasket --frames 16000`, sequential, profile repro-ml, as 9b's arms ran; each arm
  names its fixture, its flags and its `EB_EXPECT`. Its debug log is the ONE file it created (a listing diff).
- `POKEBOT_R27_KEYITEMS=1` whenever the kit is `1` (except S-SKIP). No battle of any kind happens in a 16,000-frame
  segment (verified statically in the design), so key-item mode cannot touch these runs: every arm predicts NO
  `[BATTLE] started` line in its debug log before the fixture restore (this driver records no `battles` reading).
- Fixtures: `post_hm07.ss1` (bc368611), `eb_after_M0a.ss1` (4eb75e57), `eb_after_A2ON.ss1` (946e3b05), all PINNED.

## THE HAND ARITHMETIC (independent of the code; the literals below come from it)
- **post_hm07:** ₽67,466. The basket plan is Revive 3 × 1,500 + Full Heal 8 × 600 + Hyper Potion 30 × 1,200 =
  4,500 + 4,800 + 36,000 = **₽45,300**, leaving **₽22,166**. The floor is 1,000 + 2 × (the missing Full Restore 3 ×
  3,000 = 9,000) = **₽19,000**. The budget is min(6,000, (22,166 − 19,000) // 2 = 1,583) = **₽1,583**. Spare 18 > the
  reserve 10: no reserve phase. Held (the reserve view) after the basket: Hyper 0 + 30 − 30 = 0, Full Heal 0 + 8 − 8 =
  0, so the kit wants Hyper 4 and Full Heal 2. Hyper: 1,583 // 1,200 = **1** (₽383 left); Full Heal: 383 // 600 = 0.
  The rest of the balls: min(30 − 18 = 12, 383 // 1,200 = 0) = 0. ⇒ **Hyper +1, no Ultra, ₽22,166 → ₽20,966.**
  9b's own (kit-less) forecast: min(12, 1,583 // 1,200 = 1) = **1 Ultra**, also ₽20,966.
- **RAWBAG on post_hm07:** the raw bag after the basket is Hyper 30 ≥ 4 and Full Heal 8 ≥ 2: the kit wants nothing,
  and the balls are 9b's: **1 Ultra**.
- **eb_after_M0a:** ₽22,166, spare 18, the basket complete (no plan): the same budget ₽1,583 and the same **Hyper 1**,
  ₽22,166 → ₽20,966. 9b's forecast here is 1 Ultra (walk True); the split is [].
- **eb_after_A2ON:** ₽20,966, spare 19: budget min(6,000, 1,966 // 2 = 983) = **₽983**. Hyper: 983 // 1,200 = 0;
  Full Heal: 983 // 600 = **1** (₽383 left). ⇒ **Full Heal +1, ₽20,966 → ₽20,366.**
- **The floor lever 30,000 on eb_after_M0a:** the floor is above the ₽22,166 wallet: nothing is affordable.

## THE ARMS

### P1: S-OFF (post_hm07, no flags, EB_EXPECT=buy): the kit's code changes nothing when OFF
GRADED-BY: frames, money_end, stock_end, memo_end
- ACCEPTANCE: PASS. `R frames = 10329` and `R money_end = 22166`, exactly 9b's M0a.
- EVERY frame-stamped debug line identical to 9b's committed `evidence/2026-09-29-ballrestock9b-M0a.debug.txt` up to
  the fixture restore; the `[EARLY_BASKET]` line has no ` kit=` and no ` balls=`.
- No `[KIT-BUY]` and no `[BALLS-BUY]` line. `R memo_end = []`.
- **FALSIFIER:** any differing frame-stamped line; any kit line.

### P2: S-BALL (post_hm07, balls `1`, EB_EXPECT=buy): step 9b unchanged
GRADED-BY: frames, money_end, balls_end, memo_end
- ACCEPTANCE: PASS; `R frames = 10880`; `R money_end = 20966`; the Ultra stack +1.
- The two `[BALLS-BUY]` lines of 9b's A2-ON (`why=topoff-forecast … plan=[('Ultra Ball', 1)] … walk=True`, then
  `why=topoff … bought=1 …`); no `[KIT-BUY]` line; `R memo_end = []`.
- **FALSIFIER:** a different purchase, frame count or line.

### P3: S-OBS (post_hm07, balls `1`, kit `observe`, key items `1`, EB_EXPECT=buy): observe buys exactly 9b's
GRADED-BY: money_end, balls_end, kit_end, kit_forecast, kit_expected, balls_split
- ACCEPTANCE: PASS; `R money_end = 20966`; Ultra +1; Hyper exactly +30 (the basket's).
- `R kit_forecast = [('Hyper Potion', 1)]`, `R balls_split = []`, `R kit_expected = []` (observe never buys).
- A2-ON's two `[BALLS-BUY]` lines plus exactly ONE `[KIT-BUY] why=kit-observe … kit=[('Hyper Potion', 1)] …
  split_balls=[] … walk=False`.
- **FALSIFIER:** a Hyper +31, no Ultra, or a missing/extra kit line.

### P4: S-SKIP (eb_after_M0a, kit `1`, key items UNSET, balls unset, EB_EXPECT=nothing): the coupling holds
GRADED-BY: money_end, kit_end, kit_forecast, kit_skip, memo_end
- ACCEPTANCE: PASS: "nothing missing", no walk, no spend (`R money_end = 22166`).
- `R kit_skip = True`, `R kit_forecast = []`; exactly ONE `[KIT-BUY] why=kit-skip` line; no `[BALLS-BUY]` line.
- **FALSIFIER:** a walk, a spend, or no skip line.

### P5: S-ON (post_hm07, balls `1`, kit `1`, key items `1`, EB_EXPECT=buy): one visit, the basket then the kit
GRADED-BY: money_end, stock_end, kit_end, balls_end, kit_expected, balls_split, memo_end
- ACCEPTANCE: PASS; `R money_end = 20966`; Hyper **+31** (30 basket + 1 kit); Full Heal +8; Revive +3; the Ultra
  stack **+0**; `R kit_expected = [('Hyper Potion', 1)]`; `R balls_split = []`; `R memo_end = []`.
- `REPORT bought` = the basket plan exactly; `REPORT kit` has `before = {'Hyper Potion': 30}` and
  `got = {'Hyper Potion': 1}`.
- Lines, in order:
  - 9b's `[BALLS-BUY] why=topoff-forecast … plan=[('Ultra Ball', 1)] … walk=True`, UNCHANGED (the design's R1);
  - `[KIT-BUY] why=kit-forecast mart=SootopolisCity kit=[('Hyper Potion', 1)] … split_balls=[] floor=19000
    walk=True`;
  - at the counter, `[BALLS-BUY] why=topoff-none … money=22166->20966` and
    `[KIT-BUY] why=kit … bought={'Hyper Potion': 1} money=22166->20966`.
- **FALSIFIER:** an Ultra bought; Hyper +30; a `partial` basket; any `-failed` line.

### P6: S-RAW (post_hm07, both `1`, key items `1`, `POKEBOT_R26_FAULT_RAWBAG=1`, EB_EXPECT=buy): ⛔ FAIL BY DESIGN
GRADED-BY: money_end, stock_end, balls_end, kit_forecast, kit_forecast_raw, kit_expected
- The skip-the-fix arm: the driver never models RAWBAG, so it expects the reserve view's Hyper 1 while production
  plans from the raw bag.
- Production: the Ultra stack **+1**, Hyper exactly **+30**, `R money_end = 20966`, a `[KIT-BUY] why=kit-none` line.
- `R kit_forecast = [('Hyper Potion', 1)]` (the driver) against `R kit_forecast_raw = []`.
- **ACCEPTANCE: FAIL, on EXACTLY these conjuncts:**
  - `bag_delta_equals_plan` (Hyper 30 against 31);
  - `balls_as_forecast` (Ultra 1 against 0);
  - `production_kit_forecast` (production [] and split [Ultra 1] against the driver's [Hyper 1] and []);
  - `kit_as_forecast` (kit {} against {Hyper 1});
  - `kit_attributed`;
  - `kit_before_after_basket` (no kit line was bought, so no `before`).
  - Every other conjunct PASSES, `money_drop_equals_cost` included (46,500 = 45,300 + 1,200 + a measured kit of 0).
- This is D4's live proof: one fault flips S-ON's Hyper Potion into an Ultra Ball.

### P7: S-KITONLY (eb_after_M0a, kit `1`, key items `1`, balls unset, EB_EXPECT=kit): a kit-only walk
GRADED-BY: money_end, kit_end, kit_expected, kit_floor, memo_end, on_gym_1f
- ACCEPTANCE: PASS; `REPORT early_basket = 'kit only'`; Hyper **+1**; `R money_end = 20966`; `R kit_floor = 19000`;
  `R memo_end = []`; no `balls` report key.
- **FALSIFIER:** a crash/fail-open (the None dereference the design found), no walk, or a different delta.

### P8: S-BOTHKIT (eb_after_M0a, both `1`, key items `1`, EB_EXPECT=kit): the EFFECTIVE ball walk
GRADED-BY: money_end, kit_end, balls_end, balls_split, memo_end
- ACCEPTANCE: PASS; `REPORT early_basket = 'kit only'`, although 9b's forecast line still says
  `plan=[('Ultra Ball', 1)] … walk=True`; Hyper **+1**; the Ultra stack **+0**; `R money_end = 20966`;
  `R balls_split = []`; `R memo_end = []` (the ball set is NOT memoised as wasted).
- **FALSIFIER:** "balls and kit only", an Ultra bought, or a `SootopolisCity` memo.

### P9: S-FH (eb_after_A2ON, kit `1`, key items `1`, balls unset, EB_EXPECT=kit): the first live status line
GRADED-BY: money_end, kit_end, kit_expected, memo_end
- ACCEPTANCE: PASS; `R kit_expected = [('Full Heal', 1)]`; Full Heal **+1**; Hyper +0; `R money_end = 20366`.
- **FALSIFIER:** no Full Heal, or a Hyper Potion bought.

### P10: S-OBS-RAISE (post_hm07, balls `1`, kit `observe`, key items `1`, `POKEBOT_RESERVE_FAULT_RAISE=1`, EB_EXPECT=buy)
GRADED-BY: money_end, balls_end, kit_forecast, kit_blocked, memo_end
- ACCEPTANCE: PASS; A2-ON's purchase (`R money_end = 20966`, Ultra +1, Hyper +30); `R kit_blocked = True`;
  `R kit_forecast = []`.
- Exactly ONE `[KIT-BUY] why=kit-failed` line; A2-ON's `[BALLS-BUY]` lines.
- `R memo_end = ['SootopolisCity:kit']`: the kit's key ALONE. The balls are unharmed (the design's R2 lesson).
- **FALSIFIER:** no Ultra, a `SootopolisCity` memo, or a fail-open.

### P11: S-VAC (eb_after_M0a, kit `1`, key items `1`, `POKEBOT_R23_FAULT_FLOOR=30000`, EB_EXPECT=kit): vacuity
GRADED-BY: kit_expected, kit_forecast
- `PREMISE FAILED for expect=kit … kit=[]`, then ACCEPTANCE: FAIL: the kit grade cannot pass having done nothing.
- `R kit_forecast = []`, `R kit_expected = []`.

### P12: S-RAWVAC (eb_after_M0a, kit `1`, key items `1`, `POKEBOT_R26_FAULT_RAWBAG=1`, EB_EXPECT=kit): ⛔ FAIL BY DESIGN
GRADED-BY: money_end, kit_end, kit_forecast, kit_forecast_raw
- The driver forecasts Hyper 1 (it ignores RAWBAG), so the premise holds. Production's raw view wants nothing:
  "nothing missing", no walk, `R money_end = 22166`.
- **ACCEPTANCE: FAIL, on EXACTLY these conjuncts:**
  - `topoff_only_visit`, `kit_bought_as_forecast`, `kit_attributed`, `meds_delta_is_kit`;
  - `money_drop_equals_cost` (0 is not > 0);
  - `walked_and_reheald`, `walked_back_across`;
  - `production_kit_forecast` and `kit_as_forecast`.
  - These PASS: `balls_as_forecast`, `kit_floor_kept`, `memo_clean`, `on_gym_1f`, `no_failure`, `no_whiteout`,
    `production_forecast`.

### P13: the gates (NOT blind: see the header)
GRADED-BY: frames
- `probe_kit_topoff_sootopolis.py` ALL PASS; the 9a, 9b, 10a and RULING 18 gates pass; the full suite passes.
- The adversarial mutant pass that is running: any mutant it finds that no row catches gets a row, is disclosed, and
  its set is written before the run that proves it.

## WHAT THIS DOES NOT SHOW
- Whether the kit wins Juan (step 14). A second seed: every arm is one trajectory, replayed.
- The budget-close arm (optional in the design; not run).
- Consumer (a) at Sootopolis stays inert by design (KI-103).
