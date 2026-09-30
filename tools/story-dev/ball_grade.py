"""The ball part of `--driver earlybasket`'s grade (design v2 step 9b), PURE so the gate can EXECUTE it.

WHY A MODULE. The 9b review (G4) found the driver's ball grade pinned only by text: a hollowed forecast check
(`production_forecast_ok = True`) and a re-read of the end state after the fixture restore both passed the gate. The
driver now calls these two functions, and `probe_stock_topoff_sootopolis.py` D-rows execute them with mutants.

THE RULES THEY ENCODE
  * The ACTION is the driver's OWN bag delta (every ball stack, read at PRE and at the end, before the restore), never
    production's report.
  * Only unconditional balls are priced into the cost; a Premier Ball is a free bonus (a Poké-tier purchase would
    otherwise break `money_drop_equals_cost`).
  * Production's forecast must equal the driver's own; when no forecast was made (OFF, a typo, out of era), production's
    report must have NO `balls` key at all.
"""
from __future__ import annotations


def ball_action(balls_start: dict, balls_end: dict, expected_lines, prices: dict, unconditional) -> dict:
    """{delta, bought, cost, expected}: `delta` over every stack that changed, `bought` over unconditional balls only,
    `cost` = Σ price × bought, `expected` = the summed expected purchase lines."""
    names = sorted(set(balls_start) | set(balls_end))
    delta = {n: balls_end.get(n, 0) - balls_start.get(n, 0) for n in names}
    delta = {n: q for n, q in delta.items() if q}
    bought = {n: q for n, q in delta.items() if n in unconditional}
    expected: dict = {}
    for name, qty in expected_lines or []:
        expected[name] = expected.get(name, 0) + qty
    return {"delta": delta, "bought": bought, "cost": sum(prices[n] * q for n, q in bought.items()),
            "expected": expected}


def production_forecast_ok(forecast_made: bool, driver_forecast, report: dict) -> bool:
    """Production's forecast equals the driver's; with no forecast made, the report carries no `balls` key."""
    if forecast_made:
        return (report.get("balls") or {}).get("forecast") == driver_forecast
    return "balls" not in report
