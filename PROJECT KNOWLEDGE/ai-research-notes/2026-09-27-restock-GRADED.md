# 2026-09-27 — `#24-restockleg` F1 (USER RULING 12, "Restock, then retry"): GRADED

> Predictions: `2026-09-27-restock-PREDICTIONS.md` (commit `5480be7c`, filed BEFORE these drives). Branch `wt/restock`.
> Evidence: `tools/story-dev/evidence/2026-09-27-restock-RS{1,2,3,4}-*.txt` (+ `.stdout.txt`), and the re-drives of RS1
> and RS3 on the final code, `…-RS1-short-fix-final.*` and `…-RS3-poor-fix-final.*`.
> ⚠ ONE fixture (`post_moveset.ss1`, md5 `36e4510e…`), one trajectory per arm. This is a CORRECTNESS result, not a
> frequency.

## RESULT — ALL FOUR ARMS AS PREDICTED

| Arm | Predicted | Measured | Grade |
|---|---|---|---|
| short / fix | buys [Hyper Potion 4, Full Restore 2, Revive 1]; −₽12,300; basket full; `readiness_after_restock` = []; `E1-READY`; `E1-INSIDE` | `to_buy` exactly those three; ₽900,000 → ₽887,700 (−₽12,300); bag ends at the full basket; `readiness_after_restock` = []; readings `E1-AT-DOOR, E1-GUARDS, E1-INSIDE, E1-READY`; ends LEAGUE_1F (9,3) | ✅ |
| short / norestock (`POKEBOT_CH24_FAULT_NORESTOCK=1`) | refuses on the basket; no restock; money unchanged; no `E1-READY` | R1 raised "League basket short: Hyper Potion 26/30, Full Restore 1/3, Revive 2/3"; no `restock` key; ₽900,000 unchanged; readings [] | ✅ |
| poor / fix | restock TRIED and refused by name; R1 still refuses; money unchanged | `restock_error` "…cost ₽12,300 … but we hold ₽1,741 — short by ₽10,559, and the sellable items … would only raise ₽5,000"; `readiness_after_restock` = the same basket reason; ₽1,741 unchanged; ends (18,6) (the shop refused BEFORE walking) | ✅ |
| full / fix (the ordinary path) | no restock; money unchanged; `E1-READY` | no `restock` key; ₽1,741 unchanged; readings `E1-AT-DOOR, E1-GUARDS, E1-INSIDE, E1-READY` | ✅ |

⇒ **The A/B is short/fix vs short/norestock: the same bag and the same money. The fix enters; the arm refuses.** The
restock is what changes the outcome. The poor arm shows an unaffordable basket is not "fixed" by under-buying
(RULING 16). The full arm shows the ordinary path does not visit the Mart.

## THE REVIEW (adversarial, the full diff with the code frozen): KICK-BACK, fixed

1. **The gate's R2 did not guard the recompute (PROVEN by the reviewer's mutation).** R2 checked the ORDER of five
   substrings. Deleting the recompute left all five in place, so R2 still passed while R1 would decide on the stale
   reasons. **Fixed:** R2 now walks the AST of the restock `if`: the shop, then `stock` re-read from the bag, then
   `reasons` recomputed from THAT `stock`, then recorded. Two new fault arms (recompute deleted; bag re-read deleted)
   each FAIL. The gate now has 5 fault arms. (`08-MISTAKES.md`, 2026-09-27.)
2. **An evidence mis-citation.** The review request called a 300-frame smoke test "the `poor` case". It was an earlier
   driver version's `short` run, which printed FAIL. The graded `poor` evidence is RS3 (above).
3. **A latent fail-open (a RISK, unreachable today).** The recompute passed `report.get("r1_party_size") or 0`. A
   missing size would become 0, and `min(4, 0)` passes the level half. **Fixed:** an unrecorded size now refuses by
   name. RS1 and RS3 were re-driven on the final code (below).
4. **Found AFTER the review, by the quick suite:** `probe_ch24_r1_refusal.py` G3 ("the R1 block adds no yield") went
   red, because the restock walks to the Mart. G3 exists so that a READY party's trajectory is unchanged, and that
   still holds. **Narrowed, not removed:** a yield is allowed only inside `if ch24_should_restock(...)`, G3 asserts the
   predicate is False for a ready party, and a new fault arm (the guard widened to `if reasons:`) must FAIL. Sent back
   to the same reviewer, whose second pass PROVED a hole: the exemption matched the callee's name, so a decoy
   `if ch24_should_restock([literal], True): yield` inherited it. G3 now requires exactly ONE branch fed the real
   `reasons`; the decoy and a literal-fed guard are fault arms that FAIL. A third pass found `reasons` could be rebound
   to a forged basket reason before the guard, and `reasons = []` would have disarmed R1 itself, unchecked since R1
   shipped. New G3b: every assignment to `reasons` in the block is a `ch24_readiness_shortfall` call or a non-empty
   fail-closed literal that is not a basket reason, and nothing mutates it (fault arms: forge, disarm, append). A
   fourth pass slipped a walrus and a tuple unpack past that list of statement kinds; G3b now checks every STORE of the
   name (both are fault arms). The final form was not re-reviewed; aliasing (`r = reasons; r.append(…)`) is a known,
   unguarded gap.
5. Docs were absent at review time (they follow the drives, as planned). `02` was edited in the worktree during the
   review; it is in this item's commit.
Checked by the reviewer and NOT a defect: the restock can leave the bot anywhere in the lobby on a mid-purchase raise,
and `return_to_league_door` treats any `LEAGUE_1F` tile as a no-op; the guard talk walks to its own tile first.

## RE-DRIVE ON THE FINAL CODE

See the `-final` evidence files (RS1 short/fix at 8,000 frames; RS3 poor/fix at 5,000). The verdict lines are quoted in
`07-CHANGELOG.md` 2026-09-27.

## WHAT THIS DOES NOT SHOW

- **The real post-loss state.** `ENTERED_ELITE_FOUR` set, the guards moved, a whiteout respawn at (18,6). The fixture's
  door is still closed, so the walk to the lobby Mart with the guards moved is unmeasured. The next batch after the
  merge is the first measurement.
- A level shortfall together with a basket shortfall: the pure gate covers it (no restock); it was not driven.
- Frequency, and the money: P4r2 could afford its gap; most runs reaching §Ch24 will not (`#26-ch23money`).
- The bag heal still spends Full Restores before Hyper Potions (the recon's F2). Not changed here.
