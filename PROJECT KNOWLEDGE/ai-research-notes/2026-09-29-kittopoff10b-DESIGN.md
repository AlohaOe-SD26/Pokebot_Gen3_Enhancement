# 2026-09-29 — design v2 step 10b (HK at Sootopolis): the DESIGN, after a four-angle recon

> A NOTE refining `2026-09-29-kittopoff-SPEC.md` D11-D12, which were written before 10a was built and before
> anyone read consumer (b) closely enough to see the blockers below. It supersedes D11-D12 where they differ.
> - The recon (a workflow of four fresh Claude agents: our code, the earlybasket driver, the numbers and fixtures,
>   and an adversary) is a NOTE. Every load-bearing code claim below was re-read by the author at the cited place
>   (marked ✔). The numbers marked ⚙ were executed with the real pure functions.
> - Branch `wt/kittopoff10b`, cut from `main` `158c0b70` (10a merged).
> - ⛔ **Nothing here is built yet.** The order is: this design, an adversarial review of it, predictions (after the
>   Step-0 reads), code, gate, arms, review.

## WHY D11-D12 CANNOT BE BUILT AS WRITTEN

1. **The kit and the League basket buy the SAME item names at Sootopolis** (Hyper Potion, Full Heal).
   - ✔ The basket verifies by a per-name bag delta, with `before` read at the Pokémon Center before the walk and a
     STRICT `!=` (`league_reserve._buy_basket_lines`: `short = {n: q - bought.get(n, 0) for n, q in plan if
     bought.get(n, 0) != q}`).
   - ⇒ A kit Hyper Potion bought in the basket's `buy_in_shop` call (10a's one-call pattern) turns the basket
     "partial". The kit's own delta is also wrong if its `before` predates the basket (31, not 1).
   - ⇒ **The two sets can be separated only by TIME**, never by name: the kit is bought AFTER `_buy_basket_lines`
     returns, with its own `before` read then.
2. **9b's counter phase cannot carry a kit** (the Sootopolis twin of the spec's blocker 1).
   - ✔ `sootopolis_ball_phase` verifies ONE ball (`counted = sorted({ball, "Premier Ball"})`) against the summed
     plan, and returns early on an empty ball plan (`if not lines: … return`).
   - ⇒ Appended kit lines would read short on every visit. A kit placed after the early return would never buy on
     S-ON, where D6 gives the whole budget to the kit.
3. **The early return crashes on a kit-only visit.**
   - ✔ The else branch at `league_reserve.py` (`report["early_basket"] = "balls only"`, then `balls.get('forecast')`)
     dereferences `balls`, which is `None` when the ball flag is OFF. The `AttributeError` is swallowed by
     `stock_basket_early`'s fail-open handler: no walk, no kit, on exactly S-KITONLY's flags.
4. **The counter phase runs only for the balls.** ✔ `_shop` runs a phase only `if balls.get("mode") == "1" and not
   balls.get("blocked")`. A kit-only visit would walk, buy nothing, and walk back.
5. **The earlybasket driver's 9b conjuncts FAIL the correct S-ON and cannot grade a kit-only visit.**
   - The driver's `delta` is taken over `BUY_ORDER`, which contains the kit's names.
   - ⇒ S-ON (Hyper +31 against a plan of 30) fails `bag_delta_equals_plan`.
   - It also fails `money_drop_equals_cost` (the kit's ₽1,200 is unpriced) and `balls_as_forecast` (9b's forecast
     says 1 Ultra; D6 buys 0).
   - No expectation's premise fits S-KITONLY.
6. **The S-KITONLY fixture was not in the repo.** `eb_after_M0a.ss1` lived only in session scratch, and a
   regeneration is not byte-identical. ✅ **Fixed with this note:** it and `eb_after_A2ON.ss1` are copied into
   `tools/story-dev/saves/`, probe-verified (control PASS) and PINNED in `FIXTURES.md5`.

## VERIFIED FACTS (✔ re-read by the author; ⚙ executed)

- ✔ **The fixtures** (Step-0 reads in `evidence/2026-09-29-ballrestock9b-M0.txt`):
  - `post_hm07.ss1` (bc368611): ₽67,466. The basket costs ₽45,300, which leaves ₽22,166 at the counter. Spare 18.
  - `eb_after_M0a.ss1` (4eb75e57): ₽22,166, spare 18. The Items pocket holds Hyper 30, Full Heal 8, Revive 3 and a
    Potion ×1, so the basket is complete.
  - `eb_after_A2ON.ss1` (946e3b05): ₽20,966, spare 19, the same Items pocket, basket complete.
  - All three are in the Juan era (`BASKET_ERA`); the floor is ₽19,000 (1,000 + 2 × the missing Full Restore
    ₽9,000).
- ✔ **The reserve view is time-invariant without a fault.** `reserved_quantities()` returns the TARGET basket
  (Hyper 30, Full Restore 3, Full Heal 8, Revive 3), not what was bought. So held = max(0, raw − target) reads
  {Hyper 0, Full Heal 0} both before and after the basket lines. (⚙ the code angle: 14,112 checks, 0 differ.)
  - Only under `POKEBOT_R26_FAULT_RAWBAG` does the timing matter: the raw bag reads 0/0 before the basket and 30/8
    after.
  - ⇒ A kit FORECAST (before the walk) must add the basket plan to the raw bag, as `forecast_after_basket` does for
    money, before applying the view. Otherwise the forecast and the counter disagree under RAWBAG.
- ✔ **The Potion ×1 does not count:** D3's "held" counts the tier sold and every HIGHER tier, and Potion is lower
  than Hyper Potion.
- ⚙ **The arms' purchases** (the real `kit_wants` + `visit_plan`; limits 20/30/6000, reserve 10, HP target 4):

  | Fixture, flags | Budget | Kit | Balls | Money |
  |---|---|---|---|---|
  | post_hm07, balls `1` + kit `1` (S-ON) | 1,583 | Hyper 1 | none | 67,466 → 20,966 |
  | post_hm07, balls `1`, kit unset (S-BALL = 9b's A2-ON) | 1,583 | — | Ultra 1 | 67,466 → 20,966 |
  | post_hm07, both `1` + RAWBAG (S-RAW) | 1,583 | none (raw 30/8 ≥ 4/2) | Ultra 1 | 67,466 → 20,966 |
  | eb_after_M0a, kit `1` only (S-KITONLY) | 1,583 | Hyper 1 | — | 22,166 → 20,966 |
  | eb_after_A2ON, kit `1` only (S-FH) | 983 | Full Heal 1 | — | 20,966 → 20,366 |
  | eb_after_A2ON, both `1` (S-FHBOTH) | 983 | Full Heal 1 | none | 20,966 → 20,366 |

  - ⚠ **S-ON, S-BALL and S-RAW end on the SAME money:** a Hyper Potion and an Ultra Ball both cost ₽1,200. The
    discriminator is the ITEMS, never the money. Every grade must assert per-name deltas from literals written
    before the run.
  - ⚠ **A kit arm pointed at its own output does NOT do nothing** (unlike 9b's A2c). After S-ON or S-KITONLY
    (₽20,966, held Hyper 1) the next visit buys 1 Full Heal. That is S-FH's situation, and it is why S-FH exists.

## THE DESIGN (E1-E11; each also a `06` decision when built)

- **E1, the report shape.**
  - The kit's forecast lives in a SIBLING key `report["kit"]`, never under `report["balls"]`.
    `ball_grade.production_forecast_ok` requires `"balls" not in report` when no ball forecast was made, which is
    exactly a kit-only visit.
  - With the kit OFF (unset, `0`, or a typo) the kit forecast returns `None` and adds NO key, so the report is 9b's.
  - A D2 skip (kit `1` without key items) adds `report["kit"] = {mode, walk: False, forecast: [], skip: reason}`
    and one `[KIT-BUY] why=kit-skip` line.
- **E2, the forecast.**
  - A new `sootopolis_kit_forecast(plan, money, prices, balls)` in `stock_topoff.py`, called from
    `_stock_basket_early` on its OWN import line after 9b's call. Rewriting 9b's import line deletes the anchors of
    9b's mutants M25, N1b and N2.
  - It projects the post-basket state: money and spare as `forecast_after_basket` does, and held = the raw kit stock
    plus the basket plan, minus `reserved_quantities()` (RAWBAG: no subtraction).
  - It plans with `visit_plan(buy_balls = the ball flag is 1 and the balls are not blocked)`.
  - **When the kit BUYS, it rebinds the ball forecast to `visit_plan`'s ball lines** (as 10a's errand does): S-ON's
    `report["balls"]["forecast"]` becomes `[]` with `walk` False.
  - In observe or skip, 9b's ball forecast is untouched.
  - ⛔ **It runs in its OWN try** (10a's R2 lesson, and the adversary found a live lever):
    `POKEBOT_RESERVE_FAULT_RAISE=1` raises only on the kit's path, through `reserved_quantities` → `reserve_active`.
    A kit raise memoises only `SootopolisCity:kit`, logs one `[KIT-BUY] why=kit-failed`, sets `report["kit"]` with
    `blocked` True, and leaves the balls exactly 9b's.
  - The kit key `SootopolisCity:kit` in the memo blocks the kit alone.
  - Logs one `[KIT-BUY] why=kit-forecast …` line, the twin of 9b's `topoff-forecast`.
- **E3, the walk decision.**
  - The visit walks if the basket plan, the ball walk OR the kit walk says so.
  - The outcome of a top-off-only visit:
    - EXACTLY `"balls only"` when the balls alone walk (9b's string, which the driver's `ball_only_visit`, gate rows S2
      and P9, and the phase's `wasted` check all match);
    - `"kit only"` when the kit alone walks;
    - `"balls and kit only"` when both walk.
  - The else branch never dereferences a `None`.
- **E4, `_shop`.**
  - `topoff_only = not plan and (bool(balls.get("walk")) or bool(kit.get("walk")))`, decided from the CALLER's plan
    before the live filter (BB9B-1). The parentheses are load-bearing: a precedence slip would swallow BB9B-1's raise
    whenever the kit walks.
  - Then:
    - if the kit BUYS (kit `1`, not skipped, not blocked) → the new counter phase (E5);
    - elif balls `1` and not blocked → 9b's `sootopolis_ball_phase`, byte for byte;
    - kit `observe` → no counter work at all. Its one line is the forecast's.
- **E5, the counter phase when the kit buys** (a new `sootopolis_topoff_phase`, after the basket lines, on the same
  open menu):
  - It re-plans from the LIVE post-basket state: the live list, the wallet, and the held view read NOW. It uses
    `visit_plan` with D6's order on one budget: balls to the dex reserve + 1, the kit, the rest of the balls.
  - The ball part is planned only when the ball flag is `1` and the balls are not blocked.
  - **It buys the balls and the kit in ONE `buy_in_shop` call**, with its OWN `before` read at the phase's start,
    after the basket. Balls and kit have different names, so per-name verification separates them (10a's D7).
  - Each set is verified against its PLANNED lines and logged by its own verdict (10a's R1): `[BALLS-BUY]` only when
    ball lines were planned, `[KIT-BUY]` for the kit.
  - Memo:
    - a set's shortfall memoises its own key;
    - a raise or a close inside the phase memoises BOTH planned keys and logs both `-failed`/`-closed` lines;
    - a raise in the kit's own planning blocks only the kit (own try).
  - "Wasted", per set: a set is memoised as wasted only if the visit was top-off-only, ITS forecast walked, and ITS
    counter plan is empty.
  - ⛔ The adversary's case, fault-free on `eb_after_A2ON`: the kit walks for 1 Full Heal while the balls cannot
    afford an Ultra. The ball key must NOT be memoised.
  - It writes only under `report["balls"]` (only when the ball flag is on) and `report["kit"]`.
  - It never raises, except an abort or a close (9b's contract). `POKEBOT_R23_FAULT_BALLRAISE` raises inside it too:
    both keys are memoised, which matches 10a, where a walk failure blocks both.
- **E6, the static list.** A new `SOOTOPOLIS_STATIC_KIT_SOLD = ("Hyper Potion", "Full Heal")`. ⛔ Never
  `_static_kit_sold(center)`, which ignores `center` and returns Rustboro's list.
- **E7, kit OFF / skipped / observe is 9b.**
  - Proven like 10a's review: a differential of `158c0b70`'s `stock_topoff.py` + `league_reserve.py` against the new
    ones over a state grid, with a planted control mutant that the differential must catch.
  - Proven live: S-OFF (every frame-stamped line = 9b's M0a) and S-BALL (= A2-ON).
- **E8, the driver (D12), `--driver earlybasket`.**
  - **Reads.** It reads the medicines `MEDS` (the kit's names, Revive, and Max Potion as a D3 guard) at PRE and END,
    AFTER the ball reads, so PRE and PRE-BALLS stay byte-identical. Each value is a literal subscript write
    (`R["kit_start"]`, `R["kit_end"]`, …) so the predictions gate can see it.
  - **Its own kit forecast**, computed INDEPENDENTLY of production: raw + basket plan − `LEAGUE_BASKET` (never
    production's `_kit_held` or `reserved_quantities`, which would make a RAWBAG arm grade itself correct).
  - `R["kit_forecast_raw"]` is always printed, so every S arm shows its D4 discriminator.
  - `R["balls_expected"]` is rebound to the split when the kit buys and balls are `1`.
  - **A pure `kit_grade.py`** in `ball_grade.py`'s style:
    - `kit_action`: the per-name delta; the expected TOTAL per name (basket plan + kit, summed, because the names
      overlap); the kit part; the kit's cost;
    - `production_kit_forecast_ok`.
  - **The conjuncts become kit-aware:**
    - `bag_delta_equals_plan` compares against the per-name total;
    - the money identities add the kit's cost only when a kit was expected (9b's values stay exact);
    - `balls_as_forecast` uses the rebound expectation.
  - **A new expectation `kit`:**
    - premise: in era, in Sootopolis, no basket plan, a NON-EMPTY driver kit forecast;
    - conjuncts: a top-off-only visit whose outcome equals a constant IMPORTED from `league_reserve`; the kit bought as
      forecast and non-empty; the medicine delta equals the kit exactly; money drop = kit + ball cost > 0; the floor
      kept; walked, re-healed, walked back; on gym 1F.
  - ⛔ **A stated exception to "the driver grades by its own reads":** the bag cannot split a same-name purchase
    (basket 29 + kit 2 looks like 30 + 1). So the kit's ATTRIBUTION at Sootopolis is graded from production's
    `[KIT-BUY] why=kit` line / `report["kit"]`, and the bag reads check the per-name SUM. The basket's own split is
    verified by production BEFORE any kit is bought (`EB-BOUGHT`).
- **E9, fixtures.** `eb_after_M0a.ss1` and `eb_after_A2ON.ss1` are pinned (above).
- **E10, the gates.**
  - 9b's gate (`probe_stock_topoff_sootopolis.py`):
    - its A1 pins the early-return condition by exact text, and its mutants' anchors must each occur exactly once;
    - ⇒ write A1's new pinned text and every affected red set BEFORE the first run;
    - add the kit's env vars (`POKEBOT_R26_KITTOPOFF`, `POKEBOT_R27_KEYITEMS`, `POKEBOT_R26_FAULT_RAWBAG`,
      `POKEBOT_RESERVE_FAULT_RAISE`) to both of its `setenv` calls, because rows like S1 depend on the shell they run
      from.
  - A new gate for 10b, built with 10a's lessons already applied:
    - tabulate the input dimensions first;
    - derive expected lines from THIS design, never from the code's output;
    - match lines by prefix;
    - write faithful stubs (`_kit_held` can raise; the fake phase can be short on either set);
    - run an adversarial mutant pass before trusting it.
- **E11, what stays out.** Consumer (a) at Sootopolis stays inert (Sootopolis is not whitelisted for the heal
  errand, KI-103). There is no kit before gym 1, as before.

## THE ARMS (to pre-register after the Step-0 reads; KEYITEMS `1` whenever the kit is `1`)

All on the seed-1 wrapper with `--driver earlybasket`, as 9b's arms ran; each arm's `EB_EXPECT` is named.

| Arm | Fixture | Flags | Expect | Must show |
|---|---|---|---|---|
| **S-OFF** | post_hm07 | none | buy | every frame-stamped line = 9b's M0a |
| **S-BALL** | post_hm07 | balls `1` | buy | = 9b's A2-ON (1 Ultra, R frames 10,880) |
| **S-OBS** | post_hm07 | balls `1`, kit `observe` | buy | A2-ON's purchase and lines + ONE `kit-forecast` line |
| **S-SKIP** | eb_after_M0a | kit `1`, no key items | nothing | A2b-OFF's "nothing missing", no walk + ONE `kit-skip` line |
| **S-ON** | post_hm07 | both `1` | buy | basket; Hyper **+31**; Ultra **+0**; ₽67,466 → 20,966; `[KIT-BUY] why=kit … bought={'Hyper Potion': 1}` |
| **S-RAW** | post_hm07 | both `1` + RAWBAG | buy | Ultra **+1**; Hyper +30; a `kit-none` line; kit_forecast [] vs kit_forecast_raw… |
| **S-KITONLY** | eb_after_M0a | kit `1` | kit | outcome `kit only`; Hyper **+1**; ₽22,166 → 20,966 |
| **S-FH** | eb_after_A2ON | kit `1` | kit | Full Heal **+1**; ₽20,966 → 20,366: the FIRST live drive of the status line |
| **S-FHBOTH** | eb_after_A2ON | both `1` | kit | Full Heal +1; Ultra +0; `SootopolisCity` NOT memoised |
| **S-OBS-RAISE** | post_hm07 | balls `1`, kit `observe`, `POKEBOT_RESERVE_FAULT_RAISE=1` | buy | = A2-ON's purchase + ONE `kit-failed`; the balls unharmed |
| **S-VAC** | eb_after_M0a | kit `1` + RAWBAG, `EB_EXPECT=kit` | kit | `PREMISE FAILED` (the grade cannot pass having done nothing) |

- ⚠ **To verify at Step 0, before the predictions:**
  - that `POKEBOT_RESERVE_FAULT_RAISE=1` touches ONLY the kit's path in this driver: that R18's own flow never
    calls `reserve_active` on the way (S-OBS-RAISE's premise);
  - that no trainer battle happens in the segment (KEYITEMS differs between S-ON and S-BALL; assert
    `R["battles"] == 0` or add an S-KEY control);
  - the exact `[BALLS-BUY]`/`[KIT-BUY]` lines of each arm, in 10a's AS-BUILT form.
- The budget-close arm (9b's B3′ with the kit on) is optional. The kit changes the phase's frame offsets, so the
  close frame must be re-derived, not copied.

## OPEN, NOT DECIDED HERE

- Whether a ball phase that RAISES should also block the kit when the kit did not buy in that visit. E5 answers
  only for the combined phase; in 9b's own phase (kit off) nothing changes.
- The user's Q1 (batch sizes) still bounds every number here.
