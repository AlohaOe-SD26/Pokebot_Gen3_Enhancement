# 2026-09-27 — `#24-restockleg` F1 (USER RULING 12, "Restock, then retry"): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the graded drives. A 300-frame smoke test already ran the `short` injection at the fixture's own money:
> the restock was tried and refused by name (₽1,741 + a ₽5,000 Nugget < ₽12,300), and R1 refused. That is the `poor`
> case below. Branch `wt/restock` (cut from `wt/r20fly`). Recon: `2026-09-27-ch24-basket-restock-RECON.md` (a NOTE).
> Gate green before the drives: `probe_ch24_restock.py` (3 built-in fault arms).

## THE CHANGE UNDER TEST

In `prepare_and_open_the_league`, R1 now restocks before refusing. When the League basket is R1's ONLY reason
(`ch24_should_restock`) and the bot is on Ever Grande or in the lobby:
- it runs §Ch23 leg 11's own shop once (`stock_for_the_elite_four`). The shop buys only what is missing (RULING 16),
  refuses by name when cash plus sellable items cannot cover it, and ends back on Ever Grande;
- then R1 is decided again.

A level shortfall never triggers it. `POKEBOT_CH24_FAULT_NORESTOCK=1` skips it.

## THE DRIVE — `--driver restock`

- Fixture `post_moveset.ss1` (PINNED, md5 `36e4510e…`): EVER_GRANDE_CITY (18,6), after leg 11, the full basket
  (Hyper Potion 30, Full Restore 3, Full Heal 8, Revive 3), ₽1,741.
- The floor is set to the party's LOWEST level (L19), so R1's level half passes and no training runs. **This drive tests
  the basket half only.**
- `short` and `poor` rewrite the bag to batch run P4r2's shortfall: Hyper Potion 26, Full Restore 1, Revive 2. The
  missing lines are [Hyper Potion 4, Full Restore 2, Revive 1], ₽12,300.

## PREDICTIONS

| Case | Money | Predicted |
|---|---|---|
| **short / fix** | max (P4r2 held ₽13,636) | restock `to_buy` = [Hyper Potion 4, Full Restore 2, Revive 1]; money drops by exactly ₽12,300; the basket is full after; `readiness_after_restock` = [] and `E1-READY`; the leg continues into the lobby (`E1-INSIDE`) |
| **short / norestock** (`POKEBOT_CH24_FAULT_NORESTOCK=1`) | max | R1 **refuses** on "League basket short"; no restock; money unchanged; no `E1-READY` |
| **poor / fix** | ₽1,741 (the fixture's) | the restock is TRIED and refuses by name ("short by"); R1 still refuses; money unchanged; no `E1-READY` |
| **full / fix** (the ordinary path) | ₽1,741 | no restock; money unchanged; `E1-READY` |

## FALSIFIERS

- short/fix buys anything but the three missing lines, or R1 still refuses: the restock is not what R1 re-reads.
- norestock passes R1: the arm does not remove the restock, or R1 never needed it.
- poor passes R1 or spends money: an unaffordable basket was "fixed" by under-buying (RULING 16 forbids it).
- full visits the Mart: the predicate fires with no shortfall, a regression on the ordinary path.

## WHAT THIS DOES NOT SHOW

- The real post-loss state (ENTERED_ELITE_FOUR set, the guards moved, the whiteout respawn at (18,6)). The fixture's
  door is still closed; the lobby Mart path with the guards moved is unmeasured.
- A level shortfall together with a basket shortfall (pure-gated: no restock).
- Frequency.
