# 2026-09-29 — USER RULINGS 23 + 26, design v2 step 9b (BB consumer b: the ball top-off at SOOTOPOLIS): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed, before the new gate has been run, and before any arm on the new code.
> Branch `wt/ballrestock9b` in the worktree `C:/Remote Projects/pokebot-wt-ch24`, cut from `main` (`e50441de`, then
> fast-forwarded to the docs-only `dcbffd17`). Spec: `ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` step 9,
> consumer (b), `[A-S9]`, A2/A2b (a NOTE). One ADVERSARIAL recon agent read a draft spec against the code before the
> build; its output is a NOTE, and each load-bearing claim below was re-read at FILE:LINE.

DRIVER: earlybasket

## WHAT IS BUILT (uncommitted at filing; the code commit follows this file)

- `modules/story/stock_topoff.py`, consumer (b):
  - PURE `forecast_after_basket`: the ball plan for the moment AFTER RULING 18's basket plan is bought (the wallet
    minus the plan's cost; the floor from the League basket still missing once the plan is in the bag).
  - `sootopolis_ball_forecast(plan, money, prices)`: called before any walk. OFF (unset or `0`) reads nothing but the
    flag and returns None. A typo is OFF with its own `why=topoff-flag mart=SootopolisCity` line. `observe` logs
    `why=topoff-observe` and never walks. `1` logs `why=topoff-forecast` and walks only if the forecast buys. A memo
    hit or a failed forecast BLOCKS (no ball walk and no counter phase).
  - `sootopolis_ball_phase(report)`: at the counter, after the basket lines. It re-plans from the live wallet, bag and
    stock list; buys through `buy_in_shop`; verifies by the bag delta of the ball bought; writes ONLY under
    `report["balls"]`; never raises; memoises a failure; logs an outer close (`topoff-closed`). Fault
    `POKEBOT_R23_FAULT_BALLRAISE=1` raises inside it with the menu open. `POKEBOT_R23_FAULT_FLOOR` is honoured as in
    9a.
- `modules/story/league_reserve.py`:
  - `_stock_basket_early` calls the forecast after the basket plan. The early return fires only if the basket plan is
    empty AND the forecast does not walk. A ball-only visit sets `early_basket = "balls only"`, with no EB-PLANNED.
  - `_shop` raises on a Mart selling none of the basket only when this is not a ball-only visit. The basket buy and
    verify moved, unchanged, into `_buy_basket_lines`. The phase runs in mode `1` unless the forecast blocked it.
  - ⭐ **A LATENT RULING 18 BUG, FIXED (the recon's F1, confirmed at `sootopolis_gym.py:839-872,957`):** §Ch22
    passes ONE report dict to every Juan attempt, so a second errand inherited `crossed`/`returned` from the first,
    `return_across_from_the_mart` returned at once (`league_reserve.py`: `if report.get("returned") or not
    report.get("crossed"): return`), and a second walk would have stranded the bot on the Mart side with the menu open
    (KI-103). `stock_basket_early` now ARCHIVES the previous errand (`previous_errands`) and starts clean. OFF on
    attempt 1 is unchanged: the dict is empty.
- `tools/story-dev/story_harness.py` `EarlyBasketMode`:
  - it reads every ball stack after the PRE line and at the end, BEFORE the fixture restore;
  - it prices only unconditional balls (never Premier);
  - it computes its OWN forecast with the pure planner;
  - new conjuncts:
    - `balls_as_forecast`, `balls_floor_kept` and `outcome_bought` in `buy`/`partial`;
    - `no_ball_delta` in `nothing`/`nobuy`/`skip`;
    - `production_forecast` in every arm (production's forecast equals the driver's; OFF has no `balls` key);
  - new expectations `balls` (a ball-only visit) and `ballfail` (the raise is swallowed, and the basket's outcome
    stands).
- NEW gate `tools/story-dev/probe_stock_topoff_sootopolis.py` (rows F1-F6, K1, O1-O7, P1-P8, S1-S9, A1-A4; mutants
  M1-M14 with exact red sets written in the file; N1), APPENDED at the end of `run_gates.py` GATES.

## WHAT THE RECON CHANGED (its findings, each checked against the code)

- **F1 (BLOCK), the stale per-attempt keys:** CONFIRMED and fixed (above). Gate S9 plus mutant M10.
- **F2 (BLOCK as written):** the draft indexed `report["balls"]["mode"]`, which would raise on OFF after EB-BOUGHT
  and pass as a fail-open. The code uses `.get`. `outcome_bought` now makes the driver FAIL such a run.
- **F3:** the phase writes only under `report["balls"]` (9a's errand pattern writes `returned`, which would end the
  walk back early). Gate P1 plus mutant M12.
- **F4:** the raise arm needs its own expectation (`ballfail`) and a basket arm (A2-RAISE), not only a ball-only arm.
- **F5:** the `balls` premise requires a non-empty expected purchase, and it has a vacuity arm (A2c′).
- **F6:** the heal's own typo print is not 9b's. 9b emits `why=topoff-flag mart=SootopolisCity`, and the typo arm
  counts that line.
- **F7:** end reads come before the restore; Premier is excluded from the cost; the driver's forecast honours the
  floor lever. Gate A4 plus mutant M14.
- **F8:** production's forecast is compared with the driver's in every arm. A memo hit or failed forecast blocks the
  counter phase too (gate O6, O7, S7).
- **F9:** B3, a budget expiring inside the ball phase.
- **F12:** the "pre-basket wallet → 5" case is the MIXED one (pre-basket wallet, post-basket floor). With the floor
  read before the basket too, it is 0.
- **F14:** the memo key is derived from `PokemonCenter.SootopolisCity.name`.
- **F13 (not built, named):** v2's visit order ("basket, then balls while spare ≤ 10, then the kit, then the rest of
  the balls") needs the kit, which is step 10. 9b fills to the target in one phase; step 10 must split it.
- **F15:** two `buy_in_shop` calls in one menu session have never been driven. A2-ON is the first proof. It fails safe
  (a raise is swallowed).

## THE STEP-0 READ AND THE M0

- **Step 0** (`post_hm07.ss1` = `bc3686118ac7…`, at load, committed code only; the control money matches RULING 18's
  record):
  - money ₽67,466;
  - ball pocket Poké 16, Premier 1, Great 1, Master 1 → spare 18;
  - basket lines all 0;
  - stage BASKET_ERA;
  - Ultra Ball ₽1,200, the only ball Sootopolis sells (R18's recorded `sold_here`).
  - Forecast: 1 Ultra (the budget is min(6,000, (22,166 − 19,000)//2 = 1,583)).
- **M0a** (code `e50441de`, `--frames 80000`): frame-exact with RULING 18's E1c.
  - `R frames = 10329`, money 67,466 → 22,166, `ACCEPTANCE: PASS (expect=buy)`.
  - Debug log `Story-debug-20260929-173949.log`; its post-purchase state `eb_after_M0a.ss1` is the A2b fixture.
- **M0b** (the committed code, content-verified: `git hash-object` equals the HEAD blob for all three files;
  `--frames 30000`): **IDENTICAL to M0a**, 10 of 10 driver-segment lines (the `[MAP]` lines and the `[EARLY_BASKET]`
  line, up to the fixture restore). `R frames = 10329`, `R money_end = 22166`, `ACCEPTANCE: PASS`. Debug log
  `Story-debug-20260929-180532.log`. This is one trajectory replayed, a determinism check, not a replication.
- **⚠ A process incident, disclosed (`08`):** I TaskStopped the first M0 runner to keep M0b off the uncommitted 9b
  code. M0a had exited one second earlier, and the runner had ALREADY launched a first M0b.
  - TaskStop killed only the bash runner, so that M0b ran on as an orphan on the then-uncommitted code (debug log
    `…175928`). It is NOT a control and is discarded.
  - Killing it was refused by the permission layer; it runs to its own cap.
  - The clean M0b shared its `--log`/stdout paths with the orphan, so M0b is graded from its OWN debug log only.
  - The arm runner now refuses to start while any `story_harness` process is alive, and it takes each arm's debug log
    by a listing diff, never by mtime.
  - A2-OFF still runs TWICE.

## GRADING RULES

- Arms run sequentially on profile `repro-ml`: seeded wrapper, `--driver earlybasket --frames 30000` (the cap only
  ends the idle tail; M0a's 80,000 matters only after its verdict).
- "Tracked lines" = `[MAP]`, `[BATTLE] started|ended`, `WHITEOUT` and `[EARLY_BASKET]` from the debug log. With the
  flag set, `[EARLY_BASKET]` gains a ` balls={…}` suffix; ON/observe arms compare the line up to it.
- KI-112: a single-run arm is attributed only if it matches M0a up to its discriminator and diverges there on its own
  line.

### P1 — A2-OFF ×2 (flag unset, `EB_EXPECT=buy`): OFF is unchanged
GRADED-BY: frames, money_end, balls_end, stock_end, on_gym_1f
- Both runs: `ACCEPTANCE: PASS (expect=buy)`, including the new conjuncts `balls_as_forecast`, `balls_floor_kept`,
  `outcome_bought` and `production_forecast` (no `balls` report key).
- `R frames = 10329`, `R money_end = 22166`, `R stock_end` = Revive 3 / Full Heal 8 / Hyper Potion 30, and
  `balls_end == balls_start`.
- Tracked lines identical to M0a; the `[EARLY_BASKET]` line byte-identical (no `balls=` suffix).
- Zero `[BALLS-BUY]` lines tagged `mart=SootopolisCity`.
- **FALSIFIER:** any difference from M0a on a tracked line or `R frames`. (Two OFF runs that agree with each other
  and not with M0a would be KI-112 or a code effect; that is reported, not explained away.)

### P2 — A2-OBS (`POKEBOT_R23_BALLRESTOCK=observe`, `buy`): observe plans and does nothing
GRADED-BY: frames, money_end, balls_end, balls_forecast
- `ACCEPTANCE: PASS`. `R frames = 10329`, `R money_end = 22166`, no ball delta, and tracked lines identical to M0a.
- Exactly one line:
  `[BALLS-BUY] why=topoff-observe mart=SootopolisCity ball=Ultra Ball bought=0 premier=0 spare=18->18 money=22166->22166 plan=[('Ultra Ball', 1)] floor=19000 walk=False reason=top off 1 x Ultra Ball (spare 18 <= trigger 20; budget 1583)`.
- `production_forecast` holds (both forecasts are `[('Ultra Ball', 1)]`).
- **FALSIFIER:** any purchase, any extra frame, a forecast other than 1 Ultra (5 would mean the pre-basket wallet;
  0 the pre-basket floor).

### P3 — A2-ON (`=1`, `buy`): one Ultra after the basket, in the same menu session
GRADED-BY: money_end, balls_end, balls_expected, stock_end, on_gym_1f
- `ACCEPTANCE: PASS`. Money 67,466 → **20,966** (basket 45,300 + ball 1,200 = `COST 46500`).
- The driver's `BALLS … bought={'Ultra Ball': 1} ball_cost=1200`. Basket delta 3/8/30 with readings in order.
- One `[BALLS-BUY] why=topoff-forecast … plan=[('Ultra Ball', 1)] floor=19000 walk=True …` line before the walk.
- Then exactly one
  `[BALLS-BUY] why=topoff mart=SootopolisCity ball=Ultra Ball bought=1 premier=0 spare=18->19 money=22166->20966 floor=19000 reason=top off 1 x Ultra Ball (spare 18 <= trigger 20; budget 1583)`.
- Tracked lines identical to M0a up to the purchase. Frames after it are not predicted: the purchase adds menu frames,
  and the crossing's encounters may change.
- The run ends on the gym's 1F, re-healed. `EB_SAVE_AFTER` → `eb_after_A2ON.ss1` (A2c's input).
- **FALSIFIER:** no purchase, a quantity other than 1, `Task_ShopMenu` not active for the second `buy_in_shop`
  (the recon's F15: a `topoff-failed` line), or `outcome_bought` False.

### P4 — A2-FLOOR (`=1`, `POKEBOT_R23_FAULT_FLOOR=1000`, `buy`): the basket floor is what limits A2 to one
GRADED-BY: money_end, balls_end, balls_expected, balls_floor
- `ACCEPTANCE: PASS`. `topoff` line `bought=5 premier=0 spare=18->23 money=22166->16166 floor=1000`.
- The forecast `plan=[('Ultra Ball', 5)]` (the budget is min(6,000, 10,583)).
- `R money_end = 16166`, and the driver's own forecast is also 5.
- **FALSIFIER:** 1 (the lever is ignored) or anything other than 5.

### P5 — A2-RAISE (`=1`, `POKEBOT_R23_FAULT_BALLRAISE=1`, `EB_EXPECT=ballfail`): a ball failure never touches the basket
GRADED-BY: frames, money_end, stock_end, balls_end, on_gym_1f
- `ACCEPTANCE: PASS (expect=ballfail)`: `early_basket` = "bought", readings in order, delta 3/8/30, no ball delta,
  money 22,166, walked back, re-healed, gym 1F.
- Exactly one `[BALLS-BUY] why=topoff-failed mart=SootopolisCity ball=- bought=0 premier=0 spare=?->? money=?->? reason=the ball phase raised RuntimeError('POKEBOT_R23_FAULT_BALLRAISE: the ball phase raises on purpose (menu open, nothing bought)'); the basket's outcome stands`.
- ⭐ The raise consumes no frame, so `R frames = 10329`, and the tracked lines are identical to M0a for the WHOLE run.
- **FALSIFIER:** an "failed open" outcome (the raise escaped), any frame difference from M0a, or a purchase.

### P6 — A2b-ON (fixture `eb_after_M0a.ss1`, `=1`, `EB_EXPECT=balls`): the periodic visit walks for balls alone
GRADED-BY: money_end, balls_end, balls_expected, stock_end, on_gym_1f
- Premise (driver): in era, in Sootopolis, basket plan [], expected purchase `[('Ultra Ball', 1)]`.
- CONFIRMED by the Step-0 read of that file, filed before this arm in `evidence/2026-09-29-ballrestock9b-M0.txt`:
  ₽22,166, spare 18, basket 3/8/30, BASKET_ERA, floor 19,000, standing at (43,32) on SOOTOPOLIS_CITY.
- `ACCEPTANCE: PASS (expect=balls)`: `early_basket` = "balls only", order `['EB-MART']`, basket untouched, and
  `bought={'Ultra Ball': 1}`.
- Money 22,166 → 20,966 (`money_drop_equals_cost` = 1,200), `balls_floor_kept`, walked back, re-healed, gym 1F.
- One `topoff-forecast … walk=True` line, then one `topoff … bought=1 premier=0 spare=18->19 money=22166->20966`.
- **FALSIFIER:** "nothing missing" with no walk (the early return still ignores balls), a raise "sells none" (`_shop`
  unchanged), or any basket delta.

### P7 — A2b-OFF (same fixture, flag unset, `EB_EXPECT=nothing`): unchanged
GRADED-BY: money_end, balls_end, frames
- `ACCEPTANCE: PASS (expect=nothing)`: "nothing missing", no walk, no spend, `no_ball_delta`, and `production_forecast`
  (no `balls` key).
- (RULING 18's own-output arm E2b read `R frames = 2462` on a different capture; the number here is not predicted.)
- **FALSIFIER:** a walk, a purchase, or a `balls` key.

### P8 — A2b-TYPO (`POKEBOT_R23_BALLRESTOCK=yes`, `nothing`): a typo is OFF, loudly, in 9b's own words
GRADED-BY: frames, money_end, balls_end
- `ACCEPTANCE: PASS`; tracked lines and `R frames` identical to A2b-OFF.
- Exactly one `[BALLS-BUY] why=topoff-flag mart=SootopolisCity reason=POKEBOT_R23_BALLRESTOCK='yes' is not one of ('', '0', 'observe', '1'): treated as OFF`.
- **FALSIFIER:** no such line (only the heal's own print), or any action difference from A2b-OFF.

### P9 — A2b-RAISE (`=1`, `FAULT_BALLRAISE=1`, `EB_EXPECT=ballfail`): a failed ball-only visit still walks back
GRADED-BY: money_end, balls_end, stock_end, on_gym_1f
- `ACCEPTANCE: PASS (expect=ballfail)`: `early_basket` = "balls only", order `['EB-MART']`, one `topoff-failed` line,
  no purchase, money unchanged, walked back, re-healed, gym 1F.
- **FALSIFIER:** stranded, "failed open", or a purchase.

### P10 — A2c (fixture `eb_after_A2ON.ss1`, `=1`, `EB_EXPECT=nothing`): ON pointed at its own output does nothing
GRADED-BY: money_end, balls_end, balls_forecast
- `ACCEPTANCE: PASS (expect=nothing)`.
- One line `[BALLS-BUY] why=topoff-forecast mart=SootopolisCity ball=Ultra Ball bought=0 premier=0 spare=19->19 money=20966->20966 plan=[] floor=19000 walk=False reason=cannot afford one Ultra Ball (budget 983, price 1200)`.
- No walk.
- **FALSIFIER:** a walk or a purchase (the floor did not bind), or a spare other than 19 at load. That would VOID this
  arm: the trigger, not the floor, would be what stopped it.

### P11 — A2c′ (same fixture, `=1`, `EB_EXPECT=balls`): the `balls` grade cannot pass having done nothing
GRADED-BY: balls_expected, balls_forecast
- `PREMISE FAILED for expect=balls (… balls=[])`, then `ACCEPTANCE: FAIL (expect=balls)`, with `no_failure` False.
- **FALSIFIER:** `ACCEPTANCE: PASS`.

### P12 — B3 (fixture `eb_after_M0a.ss1`, `=1`, `POKEBOT_RESERVE_FAULT_BUDGET` = A2b-ON's `frames_at_shop_open` + 40, `EB_EXPECT=budget EB_BUDGET_AT=shop`): the visit's budget expires INSIDE the ball phase
GRADED-BY: money_end, on_gym_1f, balls_end
- `ACCEPTANCE: PASS (expect=budget)`: budget expired, crossed and `frames_at_shop_open` present, the retry walked
  back, not stranded, re-healed and on the gym's 1F.
- Exactly one `[BALLS-BUY] why=topoff-closed mart=SootopolisCity … reason=the basket visit's budget closed the ball phase mid-purchase (R18 walks back)`.
- A ball delta of 0 or 1 is ACCEPTED, not predicted (where the purchase stood at the close).
- **FALSIFIER:** no `topoff-closed` line (a silent close), stranded, or a RuntimeError from a handler that yielded.

### P13 — the gates (run AFTER this file is committed)
GRADED-BY: frames
*(The key only satisfies the gate's format: gates are graded by their own output, quoted in the evidence.)*
- `probe_stock_topoff_sootopolis.py`: ALL PASS, with every mutant M1-M14 red on EXACTLY the set written in the file
  and N1 red on nothing.
- `probe_stock_topoff.py` (9a): ALL PASS unchanged (its mutant anchors are unique after 9b: the new phase uses
  `shopping`, `_inputs` and a commented GeneratorExit line).
- `probe_league_reserve.py`: ALL PASS unchanged.
- The full suite: all enforcing gates pass.
- **FALSIFIER:** any red row, or a mutant red on a set other than the written one. A wrong set is graded FAILED here,
  not "fixed" by editing the expectation.

## ADDENDUM — filed AFTER P12 failed on its premise and BEFORE B3′ ran (2026-09-29, 7:10 PM)

- **What happened to P12:** B3 ran on the ball-only fixture and never started. The driver refused it:
  `PREMISE FAILED for expect=budget (… plan=[], balls=[('Ultra Ball', 1)])`.
  - The `budget` expectation's premise (RULING 18's) requires a non-empty BASKET plan, and my prediction missed it.
  - **P12 is graded FAILED**, on the instrument: the code under test never ran.
  - The premise itself is right: without a basket plan a budget arm would, for R18, pass having done nothing. It is
    left unchanged.
- **B3′ tests the same thing on `post_hm07.ss1`, where the basket plan is non-empty.** The budget is set to expire
  40 frames into the ball phase, computed from MEASURED frames:
  - A2-ON's and A2-FLOOR's `REPORT frame_start = 3701177`, both;
  - the ball phase's first action is A2-ON's first divergence from M0a, at f3705494
    (`evidence/2026-09-29-ballrestock9b-GRADER.txt`);
  - so the phase starts 4,317 frames in, and `POKEBOT_RESERVE_FAULT_BUDGET = 4317 + 40 = 4357`.
  - The purchase logged ~530 frames after the phase start (f3706022), so the close lands inside `buy_in_shop`,
    before the confirm.

### P12b — B3′ (`post_hm07.ss1`, `=1`, `POKEBOT_RESERVE_FAULT_BUDGET=4357`, `EB_EXPECT=budget EB_BUDGET_AT=shop`)
GRADED-BY: money_end, stock_end, balls_end, on_gym_1f
- `ACCEPTANCE: PASS (expect=budget)`: budget expired, crossed with `frames_at_shop_open` present, the retry walked back
  (`retry_return` and `returned` both True), not stranded, re-healed and on the gym's 1F.
- The basket is bought (`R stock_end` 3/8/30, `REPORT early_basket = 'bought'`) and **no Ultra Ball** is bought
  (`R balls_end == R balls_start`), so `R money_end = 22166`.
- Exactly one `[BALLS-BUY] why=topoff-closed mart=SootopolisCity … reason=the basket visit's budget closed the ball phase mid-purchase (R18 walks back)`.
- Every frame-stamped line is identical to A2-ON's until the close.
- **FALSIFIER:**
  - no `topoff-closed` line (a silent close);
  - a RuntimeError ("generator ignored GeneratorExit": the handler yielded);
  - stranded;
  - an Ultra Ball bought, which would mean the close missed the phase;
  - a basket outcome other than "bought".

## WHAT THIS DOES NOT SHOW

- Whether the top-off is worth ₽1,200 per visit, or how often the Sootopolis visit buys in real runs (step 14).
- A second Juan attempt LIVE: F1 is proven by the executing gate row S9 and the code; no arm drives two attempts.
- The real attempt-2 wallet: after a Juan loss the money halves (20,966 → 10,483), below the 19,000 floor, so the
  realistic periodic visit buys nothing until the League. The periodic top-off at Sootopolis is mostly theoretical
  under RULING 18's floor. That is a finding for Q1 and step 14, not a defect.
- v2's split visit order (F13; step 10).
