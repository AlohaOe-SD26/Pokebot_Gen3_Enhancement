# 2026-09-29 — design v2 step 10b (HK at Sootopolis): the DESIGN, after a four-angle recon

> A NOTE refining `2026-09-29-kittopoff-SPEC.md` D11-D12, which were written before 10a was built and before
> anyone read consumer (b) closely enough to see the blockers below. It supersedes D11-D12 where they differ.
> - The recon (a workflow of four fresh Claude agents: our code, the earlybasket driver, the numbers and fixtures,
>   and an adversary) is a NOTE. Every load-bearing code claim below was re-read by the author at the cited place
>   (marked ✔). The numbers marked ⚙ were executed with the real pure functions.
> - Branch `wt/kittopoff10b`, cut from `main` `158c0b70` (10a merged).
> - ✅ **BUILT** (`ea75fe1f`), graded 49/49 and reviewed by three lenses: `2026-09-30-kittopoff10b-GRADED.md`. The
>   build's review amended E5 and E8; each amendment is marked **[AMENDED 2026-09-30]** where it applies.
> - ✅ **The adversarial review of this design has RUN** (a fresh Claude agent, 2026-09-29; `## THE DESIGN REVIEW`
>   at the end). It found five blockers, all in the DRIVER/ARMS half: the production half survived every attack.
>   Every finding is folded into E2, E3, E5, E8, E10 and the arms table below, marked **[R<n>]**.

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
  | eb_after_A2ON, both `1` | 983 | Full Heal 1 | none | 20,966 → 20,366 |
  | eb_after_M0a, both `1` (S-BOTHKIT; the review's R6) | 1,583 | Hyper 1 | none (9b's forecast alone: Ultra 1) | 22,166 → 20,966 |

  - ⚠ **S-ON, S-BALL and S-RAW end on the SAME money:** a Hyper Potion and an Ultra Ball both cost ₽1,200. The
    discriminator is the ITEMS, never the money. Every grade must assert per-name deltas from literals written
    before the run.
  - ⚠ **A kit arm pointed at its own output does NOT do nothing** (unlike 9b's A2c). After S-ON or S-KITONLY
    (₽20,966, held Hyper 1) the next visit buys 1 Full Heal. S-FH runs on A2-ON's output instead (held Hyper 0), and
    its purchase happens to be the same, 1 Full Heal; it is NOT a test of "pointed at its own output" (the review's
    R11).

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
  - It plans with `visit_plan(buy_balls = the ball flag is 1 and the balls are not blocked)`, honouring
    `POKEBOT_R23_FAULT_FLOOR` as 9b's forecast and 10a's errand do **[R13]**.
  - ⛔ **It NEVER overwrites 9b's ball forecast [R1, R7].** `report["balls"]` keeps 9b's `forecast`, `walk` and
    `[BALLS-BUY] why=topoff-forecast` line exactly: the driver's `production_forecast` compares it with ITS 9b
    forecast, so a rebind would FAIL the right build and PASS a build that skipped it.
    - The SPLIT (D6's ball lines when the kit buys) is published as `report["kit"]["split_balls"]`.
    - The kit's forecast line prints it, so the log never reads "forecast 1 Ultra, walk=True, then silence".
  - **The EFFECTIVE ball walk** is `bool(split_balls)` when the kit buys, and 9b's `walk` otherwise. It is what E3 and
    E5 use.
  - Tags per mode **[R10]**: `why=kit-forecast` when the kit is `1`, `why=kit-observe` when it is `observe` (9b's
    `topoff-forecast`/`topoff-observe` convention; 10a's `kit-observe`).
  - ⛔ **It runs in its OWN try** (10a's R2 lesson, and the adversary found a live lever):
    `POKEBOT_RESERVE_FAULT_RAISE=1` raises only on the kit's path, through `reserved_quantities` → `reserve_active`.
    A kit raise memoises only `SootopolisCity:kit`, logs one `[KIT-BUY] why=kit-failed`, sets `report["kit"]` with
    `blocked` True, and leaves the balls exactly 9b's.
  - The kit key `SootopolisCity:kit` in the memo blocks the kit alone.
  - Logs one `[KIT-BUY] why=kit-forecast …` line, the twin of 9b's `topoff-forecast`.
- **E3, the walk decision.**
  - The visit walks if the basket plan, the EFFECTIVE ball walk (E2) OR the kit walk says so.
  - `TOPOFF_ONLY_OUTCOMES = ("balls only", "kit only", "balls and kit only")` is exported from `league_reserve`, and
    E5 and the driver IMPORT it **[R15]**.
  - The `[EARLY_BASKET]` line gains a ` kit=…` summary only when `"kit" in report`, so a kit-OFF line is 9b's byte for
    byte **[R14]**.
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
  - **Shape it to keep 9b's gate anchors [R9]:** keep 9b's `ball_only = …` line and its
    `if balls.get("mode") == "1" and not balls.get("blocked"):` line byte-identical. Add
    `topoff_only = ball_only or (not plan and bool(kit.get("walk")))`, and put the kit's dispatch BEFORE 9b's with
    its own `return`.
    - The raise's condition (9b's M5 anchor) must change to `not topoff_only`. Re-anchor M5 with its set unchanged, and
      re-derive A1/M3 (the early return) before the first run.
- **E5, the counter phase when the kit buys** (a new `sootopolis_topoff_phase`, after the basket lines, on the same
  open menu):
  - It re-plans from the LIVE post-basket state: the live list, the wallet, and the held view read NOW. It uses
    `visit_plan` with D6's order on one budget: balls to the dex reserve + 1, the kit, the rest of the balls.
  - The ball part is planned only when the ball flag is `1` and the balls are not blocked.
  - **It buys the balls and the kit in ONE `buy_in_shop` call**, with its OWN `before` read at the phase's start,
    after the basket. Balls and kit have different names, so per-name verification separates them (10a's D7).
  - Each set is verified against its PLANNED lines and logged by its own verdict (10a's R1): `[KIT-BUY]` for the kit,
    and `[BALLS-BUY]` whenever the ball flag is `1` and the balls are not blocked (`topoff-none` when no ball line
    was planned). **[AMENDED 2026-09-30, the build's review DC2]** This sentence first said "`[BALLS-BUY]` only when
    ball lines were planned"; the predictions (P5) and the gate (P1) had pre-registered the `topoff-none` line, as
    9b logs it. What the review found wrong was its MONEY: it carried the kit's cost. ⇒ A set that planned no line
    reads the wallet UNCHANGED on its line and in its report; a set that bought reads the wallet after the ONE call
    (both sets, as 10a's combined line does).
  - Memo:
    - a set's shortfall memoises its own key;
    - a raise or a close inside the phase memoises BOTH planned keys and logs both `-failed`/`-closed` lines;
    - a raise in the kit's own planning blocks only the kit (own try).
  - "Wasted", per set: a set is memoised as wasted only if the visit was top-off-only, ITS forecast walked, and ITS
    counter plan is empty. **[AMENDED 2026-09-30, the build's review LI-2]** For the kit, also: its LIVE wants are
    empty (a static/live list mismatch), or the visit bought nothing. A spare that DROPS on the crossing (a catch en
    route) lets the reserve balls take the kit's budget while its wants stand; that is a re-allocation, not a
    disagreement, and memoising it blocked a legitimate kit for the rest of the run.
  - ⛔ The adversary's case, fault-free on `eb_after_A2ON`: the kit walks for 1 Full Heal while the balls cannot
    afford an Ultra. The ball key must NOT be memoised.
  - It writes only under `report["balls"]` (only when the ball flag is on) and `report["kit"]`.
  - It publishes `report["kit"]["before"]`, its own read. The driver asserts it equals the PRE stock plus the basket
    plan, which proves the kit's `before` was read AFTER the basket **[R8]**.
  - It never raises, except an abort or a close (9b's contract).
  - **Defined terms [R15]:**
    - "the active keys" of a raise or a close are the kit key, plus the ball key when the ball flag is `1` and the
      balls are not blocked. Both are memoised; each set planned logs its `-failed`/`-closed` line.
    - `POKEBOT_R23_FAULT_BALLRAISE` raises in E5 only when the ball flag is `1` (it is the BALL fault).
    - "Wasted" uses the EFFECTIVE walks and `TOPOFF_ONLY_OUTCOMES`: a set is wasted only when the outcome is one of
      them, ITS effective forecast walked, and ITS counter plan is empty.
  - It honours `POKEBOT_R23_FAULT_FLOOR` **[R13]**.
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
  - **THE LEVER RULE [R4].** The driver MODELS every lever whose correct production response is defined:
    - the D2 skip (`kit_skip`: the forecast is `[]`);
    - `POKEBOT_RESERVE_FAULT_RAISE` (blocked: `[]`);
    - `POKEBOT_R23_FAULT_FLOOR` (the floor);
    - `POKEBOT_RESERVE_FAULT_NOBUY` (no forecast);
    - **[AMENDED 2026-09-30, the build's review DC1]** `POKEBOT_R23_FAULT_BALLRAISE` with the balls `1`: E5 raises
      before any purchase, so the kit walks and buys nothing (`R["kit_ballraise"]`, `R["kit_walk"]`). `ballfail`
      grades a kit-only walk, labels the visit by the effective walks, and asserts the kit's phase failed and both
      keys memoised. `kit_as_forecast` is graded for every EXPECT EXCEPT `budget`, where the close's point in the
      visit decides what was bought. (As built first, it sat in `common`: no build could pass `ballfail` with the
      kit on, and a correct close failed `budget`.)
    It NEVER models a skip-the-fix lever (`POKEBOT_R26_FAULT_RAWBAG`), so a RAWBAG arm must FAIL.
    `R["kit_forecast_made"]` mirrors 9b's gating (the mode in observe/1, in era, in Sootopolis, not NOBUY).
    `R["kit_expected"]` is the forecast only in mode `1` and not skipped: observe never buys.
  - `R["balls_forecast"]` stays 9b's, so `production_forecast` is unchanged **[R1]**. The driver's own split is
    `R["balls_split"]`, graded against `report["kit"]["split_balls"]`. `R["balls_expected"]` is the split when the
    kit buys and the balls are `1`, else 9b's.
  - **The kit is priced from the MEASURED delta** (the per-name delta minus the basket plan, positive entries), as 9b
    prices balls, and only when a kit was expected. 9b's money values stay exact **[R3]**.
  - **A basket-only conjunct [R8]:** `rep["bought"] == dict(plan)` (production's basket delta, read before any kit).
    It catches a build that folds the kit into the basket call with a merged verification. It holds on every 9b arm.
  - **The memo is made OBSERVABLE [R5]:** the driver sets `self._ball_topoff_failed = set()` at its start, which is
    exactly what `_memo()` looks for, and records `R["memo_end"]`. A single visit starts empty, so 9b's paths are
    unchanged. Memo claims can then be graded live.
  - **A pure `kit_grade.py`** in `ball_grade.py`'s style:
    - `kit_action`: the per-name delta; the expected TOTAL per name (basket plan + kit, summed, because the names
      overlap); the kit part; the kit's cost;
    - `production_kit_forecast_ok`.
  - **The conjuncts become kit-aware:**
    - `bag_delta_equals_plan` compares against the per-name total;
    - the money identities add the kit's MEASURED cost only when a kit was expected (9b's values stay exact);
    - `balls_as_forecast` compares with `R["balls_expected"]`: the driver's split when the kit buys, 9b's otherwise;
    - `common` gains `production_kit_forecast` (production's kit forecast AND `split_balls` equal the driver's; with no
      kit forecast made, no `kit` key) and `rep["bought"] == dict(plan)` on basket visits.
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
    - the anchors the build must move **[R9]**: A1 and M3 (the early return) and M5 (the raise). E4's shape keeps
      M6, M31, M32 and M33 byte-identical;
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

All on the seed-1 wrapper with `--driver earlybasket --frames 16000`, as 9b's arms ran; each arm's `EB_EXPECT` is
named. Revised by the design review (the arms marked **[R]**). ⛔ The predictions file must carry the HAND arithmetic
under each literal, not only the ⚙ table: the driver shares the pure functions with production, so literals computed by
them are not independent **[R16]**.

| Arm | Fixture | Flags | Expect | Must show |
|---|---|---|---|---|
| **S-OFF** | post_hm07 | none | buy | every frame-stamped line = 9b's M0a (the `[EARLY_BASKET]` line has no `kit=`) |
| **S-BALL** | post_hm07 | balls `1` | buy | = 9b's A2-ON (1 Ultra, R frames 10,880) |
| **S-OBS** | post_hm07 | balls `1`, kit `observe` | buy | A2-ON's purchase and lines + ONE `[KIT-BUY] why=kit-observe` line |
| **S-SKIP** | eb_after_M0a | kit `1`, no key items | nothing | A2b-OFF's "nothing missing", no walk + ONE `kit-skip` line; the driver's kit forecast `[]` (it models D2) |
| **S-ON** | post_hm07 | both `1` | buy | basket; Hyper **+31** (30 basket + 1 kit); Ultra **+0**; ₽67,466 → 20,966; `rep["bought"]` = the plan; `kit.before` Hyper = 30; `[KIT-BUY] why=kit … bought={'Hyper Potion': 1}`; 9b's forecast line still `[('Ultra Ball', 1)] walk=True`, and the kit line shows `split_balls=[]` |
| **S-RAW** [R3] | post_hm07 | both `1` + RAWBAG | buy | ⛔ **ACCEPTANCE FAIL, by design** (a skip-the-fix arm: the driver never models RAWBAG). Production buys Ultra **+1**, Hyper +30 and logs `kit-none`; FAILS exactly `bag_delta_equals_plan` (Hyper 30 vs 31), `balls_as_forecast` (Ultra 1 vs 0) and `production_kit_forecast`; money PASSES (measured pricing). This is D4's live proof: one fault flips S-ON's Hyper into an Ultra |
| **S-KITONLY** | eb_after_M0a | kit `1` | kit | outcome `kit only`; Hyper **+1**; ₽22,166 → 20,966 |
| **S-BOTHKIT** [R6] | eb_after_M0a | both `1` | kit | outcome **`kit only`** (the EFFECTIVE ball walk is the empty split, though 9b's forecast says 1 Ultra); Hyper **+1**; Ultra **+0**; ₽22,166 → 20,966; `SootopolisCity` NOT in `memo_end` |
| **S-FH** | eb_after_A2ON | kit `1` | kit | Full Heal **+1**; ₽20,966 → 20,366: the FIRST live drive of the status line |
| **S-OBS-RAISE** | post_hm07 | balls `1`, kit `observe`, `POKEBOT_RESERVE_FAULT_RAISE=1` | buy | = A2-ON's purchase + ONE `kit-failed`; `memo_end` = {`SootopolisCity:kit`} only; the driver models the lever (kit blocked, `[]`) |
| **S-VAC** [R2] | eb_after_M0a | kit `1`, `POKEBOT_R23_FAULT_FLOOR=30000`, `EB_EXPECT=kit` | kit | `PREMISE FAILED`: budget 0, so both forecasts are `[]` (the grade cannot pass having done nothing) |
| **S-RAWVAC** [R2] | eb_after_M0a | kit `1` + RAWBAG, `EB_EXPECT=kit` | kit | ⛔ **ACCEPTANCE FAIL, by design**: the driver forecasts Hyper 1; production (raw 30/8) plans nothing, "nothing missing", no walk |

- ✅ **Step-0 premises checked statically (2026-09-29, by the author):**
  - `POKEBOT_RESERVE_FAULT_RAISE` touches only the kit. `reserve_active` has exactly two callers:
    `reserved_quantities` (the kit's held view) and `filter_medicine_for_reserve`, which runs only in battle and
    fails unlocked. R18's visit never calls it.
  - **No battle of any kind** happens in a 16,000-frame earlybasket segment **[R12]**. The only battle in 9b's M0a log
    (f3709657) comes AFTER the driver handed the run to Manual mode, under its `--frames 80000`. The driver counts
    `self.battles`, so the predictions assert `battles == 0`.
- **Still to read at Step 0:** the exact `[BALLS-BUY]`/`[KIT-BUY]` lines of each arm, in 10a's AS-BUILT form, as each
  arm's own pre-registered literal.
- The budget-close arm (9b's B3′ with the kit on) is optional. The kit changes the phase's frame offsets, so the
  close frame must be re-derived, not copied.
- **[R11] corrected:** S-FH runs on A2-ON's output (held Hyper 0, spare 19), NOT on S-ON's. A kit arm pointed at its
  own output walks again: S-FH's own output (Full Heal 9, ₽20,366, budget 683) buys another Full Heal. The kit
  converges only after two more visits.

## OPEN, NOT DECIDED HERE

- Whether a ball phase that RAISES should also block the kit when the kit did not buy in that visit. E5 answers
  only for the combined phase; in 9b's own phase (kit off) nothing changes.
- The user's Q1 (batch sizes) still bounds every number here.

## THE DESIGN REVIEW (a fresh adversarial Claude agent, 2026-09-29; its output is a NOTE, and each finding below was
## checked by the author against the code before it was folded in)

- **Verdict:** the production half (E1-E6) survived every attack.
  - Separating the two purchases by time is correct.
  - The ⚙ table reproduced exactly.
  - No attack made a kit-OFF, observe or skip visit change 9b's purchase or R18's walk back.
  - Attacks that FAILED: a full Items pocket (a refusal returns to the buy menu uncharged, and the sets sit in
    different pockets); S-OBS-RAISE's premise; the "balls only" matchers; the reserve view's time invariance; the
    static list; the memo when the balls are blocked and the kit buys.
- **Blockers, all in the driver/arms half, each folded in:**
  - **R1:** a rebind of 9b's ball forecast inverts `production_forecast` (✔ `ball_grade.production_forecast_ok`
    compares `report["balls"]["forecast"]` with the driver's 9b forecast). Resolved: no rebind; the split goes to
    `report["kit"]["split_balls"]`; the effective walk (E2).
  - **R2:** S-VAC's "PREMISE FAILED" was impossible under E8's own rule, because a driver that ignores RAWBAG forecasts
    Hyper 1. Resolved: S-VAC uses the floor lever; the RAWBAG run is S-RAWVAC, an expected FAIL.
  - **R3:** S-RAW had no verdict, and its money conjunct hung on an unstated pricing choice. Resolved: S-RAW is an
    expected FAIL with its exact failing set; the kit is priced from the measured delta.
  - **R4:** the kit-forecast comparison was undefined for skip, blocked and observe, and would have FAILED the correct
    S-SKIP and S-OBS-RAISE. Resolved: the lever rule (E8).
  - **R5:** the memo was invisible in the driver (✔ `_memo()` returns None unless the bot mode carries a
    `_ball_topoff_failed` set; EarlyBasketMode carries none). Resolved: the driver sets one and records `memo_end`.
- **Defect-risks folded in:**
  - R6, S-BOTHKIT added: it is the only arm that tests the effective walk on a top-off-only visit;
  - R7, no observe erasure;
  - R8, `rep["bought"] == plan` and the kit's `before`;
  - R9, the anchor-preserving shape of `_shop`.
- **Nits folded in:** R10 (tags per mode), R11 (S-FH's wording), R12 (no battle of ANY kind), R13 (the floor lever),
  R14 (the `[EARLY_BASKET]` kit suffix), R15 (defined terms and `TOPOFF_ONLY_OUTCOMES`), R16 (hand arithmetic in the
  predictions).
- ⛔ **Not a second pass.** A second adversarial pass on THIS revision has not run. The predictions file's own review
  and the build's three-lens review are the next adversaries.
