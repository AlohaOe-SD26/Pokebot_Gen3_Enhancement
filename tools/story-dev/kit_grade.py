"""The healing-kit part of `--driver earlybasket`'s grade (design v2 step 10b), PURE so a gate can EXECUTE it.

WHY A MODULE. Step 9b's review (G4) found a driver grade pinned only by text; `ball_grade.py` is the fix, and this is
its twin for the kit (`ai-research-notes/2026-09-29-kittopoff10b-DESIGN.md` E8).

THE RULES THEY ENCODE
  * At Sootopolis the kit and RULING 18's basket buy the SAME item names (Hyper Potion, Full Heal), so the bag can only
    ever show a per-name SUM: `expected` is the basket plan PLUS the kit, summed per name, and the kit's own part is
    the delta MINUS the basket plan (positive entries only: a short basket is the basket's failure, graded by its own
    conjuncts, never a negative "kit").
  * ⛔ A stated exception to "the driver grades by its own reads": the bag cannot split a same-name purchase (basket 29 +
    kit 2 looks like 30 + 1), so the kit's ATTRIBUTION is graded from production's `report["kit"]`, while the bag
    reads check the per-name SUM. The basket's own split is verified by production BEFORE any kit is bought.
  * The kit's cost is priced from the MEASURED kit part, and the caller adds it only when a kit was expected, so every
    kit-OFF arm keeps step 9b's money identity exactly.
  * Production's kit forecast AND its D6 ball split must equal the driver's own; when no kit forecast was made (OFF, a
    typo, out of era), production's report must have NO `kit` key at all.
"""
from __future__ import annotations


def _summed(lines) -> dict:
    out: dict = {}
    for name, qty in lines or []:
        out[name] = out.get(name, 0) + qty
    return out


def kit_action(meds_start: dict, meds_end: dict, basket_plan, kit_expected_lines, prices: dict) -> dict:
    """{delta, expected, kit, kit_expected, kit_cost}.

    `delta`: every medicine stack that changed, from the driver's own reads. `expected`: the basket plan plus the kit,
    summed per name. `kit`: the delta minus the basket plan, positive entries only. `kit_expected`: the summed kit
    lines. `kit_cost`: Σ price × `kit`."""
    names = sorted(set(meds_start) | set(meds_end))
    delta = {n: meds_end.get(n, 0) - meds_start.get(n, 0) for n in names}
    delta = {n: q for n, q in delta.items() if q}
    basket = _summed(basket_plan)
    kit_expected = _summed(kit_expected_lines)
    expected = dict(basket)
    for name, qty in kit_expected.items():
        expected[name] = expected.get(name, 0) + qty
    kit = {n: delta.get(n, 0) - basket.get(n, 0) for n in sorted(set(delta) | set(basket))}
    kit = {n: q for n, q in kit.items() if q > 0}
    return {"delta": delta, "expected": expected, "kit": kit, "kit_expected": kit_expected,
            "kit_cost": sum(prices[n] * q for n, q in kit.items())}


def production_kit_forecast_ok(forecast_made: bool, driver_kit, driver_split, report: dict) -> bool:
    """Production's kit forecast and its D6 ball split equal the driver's; with no forecast made, no `kit` key."""
    if forecast_made:
        kit = report.get("kit") or {}
        return kit.get("forecast") == driver_kit and kit.get("split_balls") == driver_split
    return "kit" not in report


def kit_attributed(report: dict, kit_expected: dict) -> bool:
    """The stated exception: production's OWN verification of the kit set (its `got`, read after the basket) equals the
    expected kit, and it says ok."""
    kit = report.get("kit") or {}
    return kit.get("got") == kit_expected and kit.get("ok") is True


def kit_before_after_basket(report: dict, meds_start: dict, basket_plan) -> bool:
    """Production's kit `before` was read AFTER the basket: for each kit item it counted, the PRE stock plus the
    basket plan (the design's R8; a kit bought inside the basket's call, or read before it, fails this)."""
    before = (report.get("kit") or {}).get("before") or {}
    basket = _summed(basket_plan)
    return bool(before) and all(before[n] == meds_start.get(n, 0) + basket.get(n, 0) for n in before)
