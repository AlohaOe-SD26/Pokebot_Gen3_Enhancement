# 2026-09-26 — §Ch23 leg-5 RE-ENTRY from the League plateau — PREDICTIONS, filed BEFORE the live drives

> Source: `2026-09-26-ch23money-RECON.md` §4 (a NOTE; its minimal fix, adopted). Build: `victory_road.on_league_plateau()`
> (on EVER_GRANDE_CITY and `calculate_path` to the Victory Road apron (18,42) raises) and `leg5_should_fire()` — the
> dispatch's leg-5 guard as ONE named predicate — now `not (wally_beaten() and on_league_plateau())` on top of the old
> guard. Skip-the-fix arm `POKEBOT_CH23_FAULT_REENTRY` restores the old guard.
> ⚠ The static ROM gate `probe_ch23_leg5_reentry.py` was already RUN (PASS: three plateau fixtures skip, the arm fires
> there, both south controls — including `ki90_whiteout_at_evergrande`, Wally beaten at the south PC (27,49) — still
> fire). Its expectations were written in the gate before that run but NOT committed first, so they are not a
> pre-registration; these live-drive predictions are.

## WHY THE DEFECT ONLY BITES ON RE-ENTRY
The dispatch evaluates leg 5's guard once per attempt, at the top. A chained run from `post_wally` passes leg 5 on
VR1F, then runs legs 6-11 in the same pass; the plateau is reached only AFTER leg 5's guard was read. A RE-ENTRY (a new
attempt, a new `_play` pass, a restart) evaluates it while standing on (18,6).

## ARMS — `--driver ch23chapter` on `post_league_heal.ss1` (`1a8a0269b42d`: plateau (18,6), Wally beaten, healed,
basket empty, ₽56,041)

| arm | predicted | falsifier |
|---|---|---|
| **A1 FIX** | `ACCEPTANCE: PASS` — legs 1-10 skip, leg 11 buys the whole basket (₽56,041 → ₽1,741, as the 2026-09-04 capture and RULING 16's S1 arm), `ch23_chapter_done()` True, no `enter_victory_road` call, a few thousand frames | leg 5 fires anyway, or the chapter fails |
| **A2 REENTRY (old guard)** | `ACCEPTANCE: FAIL` — leg 5 fires and aims at (18,42): `Could not reach (18, 42)` / `UnreachableDestinationError`; the basket is NOT bought | A2 passes (then the defect never existed on this fixture) |
