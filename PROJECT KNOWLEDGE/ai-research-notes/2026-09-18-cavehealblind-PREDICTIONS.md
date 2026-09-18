# `#24-cavehealblind` — PREDICTIONS, FILED BEFORE THE DRIVER EXISTS (2026-09-18)

> ⛔ Written and **committed before the driver was written or executed** (`story-drive` §1).
> Anything the run contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Can a grind standing inside Victory Road actually HEAL — and get BACK?**

This is the gating unknown for the whole §Ch24 training leg. USER RULING 4 says time is not the
constraint and training must be level-appropriate; RULING 2 puts the grind at the Victory Road exit
side and says *heal at a Poké Center, not items*. Everything else about the grind is settled. **This
is not.**

## ✅ WHAT IS ALREADY MEASURED (so the drive only has to answer what is left)

| fact | evidence |
|---|---|
| `train_team` DOES travel — it calls `_goto_training_area` every round | `early_game.py` (call at `:2125`, function at `:2049-2068`) |
| its heal branch runs `_exit_training_cave_if_inside()` then `heal_in_pokemon_center(heal_center)` | `early_game.py:2153-2158` |
| ⛔ `_CAVE_EXITS` holds **only** `GRANITE_CAVE_1F` and `FIERY_PATH` — **Victory Road is absent** | `early_game.py:2003-2012` |
| ⇒ the cave-exit step is **a documented no-op** on Victory Road | `early_game.py:2021` — *"A cheap no-op anywhere that is not in `_CAVE_EXITS`"* |
| ⭐ but `navigate_to_anywhere` is multi-hop and warp-aware, and the tables are recorded as *"REDUNDANT, not load-bearing"* | `early_game.py:1988-1997` |
| from the Victory Road exit side `EVER_GRANDE (18,42)` the Poké Center door is **23 wp** | `evidence/2026-09-18-vr-heal-roundtrip.stdout.txt` |
| ⛔ from the **League door** side `(18,6)` it is **NO PATH** on a same-map ask | same |
| the grind tile `TRAIN_SPOT_1F (15,39)` is *"1 step from the entrance warp"* | `victory_road.py:477` |

⇒ **The route plausibly exists. Whether the navigator WALKS it has never been observed.**

## THE FIXTURE, AND WHY IT IS THE RIGHT ONE

`grind_stall_ppzero.ss1` — pinned, `VICTORY_ROAD_1F (15,39)`, **already on the grind tile**, mid-grind,
with `Wailord L61 225/309 · Surf 0/15 · Water Spout 0/5 · Waterfall 0/15` — i.e. **PP-dry**, which is
exactly the `_dry` condition that fires the heal branch.
⭐ It is also a **captured STALL nobody has diagnosed**, so this drive has a second chance of value:
it may explain that stall rather than only answering the heal question.

## ⛔ THE SAFETY CONSTRAINT THIS DRIVE MUST RESPECT

The Poké Center is on the **opposite side of Ever Grande** from the League. ⇒ the leg must **never**
route toward `POKEMON_LEAGUE_1F` or any sealed Elite Four map. A path guard refuses any waypoint on a
League-interior map, and it **self-tests on a synthetic hazard first** (the `#24-pathguardblind`
lesson: a guard whose only evidence is that it never fired has never been shown to work).
⚠ Wild encounters ARE expected while crossing Victory Road. With 0 PP the bot flees, and fleeing takes
no damage — so battles > 0 is normal here and is **not** a failure.

## PREDICTIONS

| # | reading | prediction | falsifier |
|---|---|---|---|
| P1 | premise | `VICTORY_ROAD_1F`, tile `(15,39)` | anything else ⇒ wrong fixture |
| P2 | party PRE | PP-dry (Wailord's moves at 0), HP below full | already healthy ⇒ the heal branch may no-op and the drive is **vacuous** |
| P3 | ⭐ does the heal LEAVE Victory Road? | **YES** — the map changes off `VICTORY_ROAD_1F` | NO ⇒ ⛔ **`#24-cavehealblind` is CONFIRMED AS A BLOCKER**: a Victory Road grind cannot heal, and the §Ch24 training leg needs a different design entirely |
| P4 | destination | reaches `EVER_GRANDE_CITY_POKEMON_CENTER_1F` | reaches somewhere else ⇒ read where; the navigator's route is the finding |
| P5 | heal effect | party restored — **HP full AND PP restored** | HP only ⇒ the PP half is unsolved, and PP is what stalled this fixture |
| P6 | ⭐⭐ the RETURN | navigating back to `TRAIN_SPOT_1F (15,39)` **arrives** | fails ⇒ the bot can leave but not return ⇒ a grind would drift off its grass after the first heal, which is a **worse** finding than P3 failing |
| P7 | whiteouts | **0** | a whiteout ⇒ the crossing is not safe with a PP-dry party, which itself constrains the design |
| P8 | path guard | **no waypoint on any League-interior map**, and the guard's self-test REFUSES a synthetic hazard | a clean self-test ⇒ the guard is blind; refuse the leg (the `#24-pathguardblind` shape) |

⚠⚠ **P6 IS THE ONE THAT MATTERS MOST AND THE ONE I AM LEAST SURE OF.** P3 has a plausible route
measured. The RETURN is the leg nothing has ever executed: it must re-enter a cave whose entrance is
not in `_CAVE_ENTRANCES`, and `#24-league2f` already showed that a cross-map `calculate_path` request
is **refused outright** — so the return may have to be expressed as per-map segments. If it fails, the
finding is not "healing is broken" but "**healing is one-way**", which is a different and nastier bug.

⚠ **P2 IS THE VACUITY GUARD.** If the party reads healthy the drive proves nothing, and the run must
say so loudly rather than printing a pass.

## ⛔ WHAT THIS WILL NOT ESTABLISH

* **That a full grind works.** One heal round trip is not 623 battles with heals interleaved.
* **The frequency.** Measured elsewhere at ~1 heal per 8.3 battles; this drive does not re-measure it.
* **Anything about B1F.** USER RULING 2 put the grind on the 1F exit side and took B1F off the table.

## HOW THIS GETS GRADED

A **GRADED** section is appended after the runs: every P row ✅ met, ❌ refuted or ⚠ unreadable, **with
the literal log line beside it**. A row that cannot be quoted was not measured.
