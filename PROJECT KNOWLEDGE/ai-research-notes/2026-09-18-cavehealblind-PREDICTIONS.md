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


---

# ⭐⭐ GRADED — 2026-09-18: `#24-cavehealblind` IS ANSWERED. A VICTORY ROAD GRIND CAN HEAL, AND CAN GET BACK.

> Evidence: `tools/story-dev/evidence/2026-09-18-ch24caveheal-*.txt`.
> Every row carries the literal log line. A row that cannot be quoted was not measured.

| # | verdict | the line it is graded on |
|---|---|---|
| P1 | ✅ MET | `PRE at=((24, 43), (15, 39)) tile=(15, 39)` — `(24,43)` is `VICTORY_ROAD_1F` |
| P2 | ✅ MET | `worst_hp=72.8% pp=437/480` — damaged, so the heal branch is live and the drive is not vacuous |
| P3 | ⭐ **MET** | `⭐ LEFT VICTORY ROAD — route=[[24, 43], [0, 8], [16, 12], [0, 8]] (2002 yields)` |
| P4 | ✅ MET | `visited_pokemon_center=True` — `[16, 12]` in the route is `EVER_GRANDE_CITY_POKEMON_CENTER_1F` |
| P5 | ⭐ **MET, AND THE PP HALF IS THE PART THAT MATTERED** | `HEAL EFFECT hp 72.8% -> 100.0%  pp 437/480 -> 480/480  (hp_ok=True pp_ok=True)` |
| P6 | ⭐⭐ **MET — THE ROW I FLAGGED AS LEAST CERTAIN** | `⭐⭐ RETURNED to the grind tile — at=((24, 43), (15, 39)) tile=(15, 39). The heal round trip is CLOSED.` |
| P7 | ✅ MET | `RESULT battles=1 whiteouts=0 failure=None` |
| P8 | ✅ MET | `GUARD SELF-TEST OK — 13 League/sealed maps are refused, and both synthetic probes were recognised`; `R route` contains no League-interior map |

## ⭐⭐ THE ANSWER, PLAINLY

**A grind standing on `TRAIN_SPOT_1F` inside Victory Road CAN heal at the Ever Grande Poké Center and
CAN walk back to its grass.** The route is
`VICTORY_ROAD_1F → EVER_GRANDE_CITY → EVER_GRANDE_CITY_POKEMON_CENTER_1F → EVER_GRANDE_CITY`, then a
navigate back in. It cost **2,002 yields**, **1 wild battle** and **0 whiteouts**.
⇒ ⛔ **`#24-cavehealblind` was the gating unknown for the entire §Ch24 training leg, and it is
resolved in the leg's favour.** The `_CAVE_EXITS` table not knowing Victory Road turns out not to
matter — `heal_in_pokemon_center` uses `navigate_to_anywhere`, which is multi-hop and warp-aware, and
it walked out and back without any table entry.

⭐ **AND IT ANSWERS THE PP QUESTION THE FIXTURE WAS CAPTURED FOR.** `grind_stall_ppzero.ss1` is a
pinned STALL whose slot 0 had every move at 0 PP. The heal restored **PP 437/480 → 480/480** as well
as HP ⇒ a Poké Center heal is a complete remedy for the dry-PP stall, not a partial one.

## ⚠ THREE THINGS THIS DOES **NOT** SHOW, AND ONE ARM THAT DID NOT DO ITS JOB

1. **It is ONE heal, not a grind.** 623-battle runs interleave heals with training; this measured a
   single round trip from a standing start. Frequency (≈1 heal per 8.3 battles) is measured
   elsewhere and is NOT re-measured here.
2. **The fault arm suppresses TWO readings, and I am saying so rather than glossing it.**
   `POKEBOT_CH24_FAULT_NORETURNHEAL=1` gives `missing=['C-CONTINUE', 'C-RETURN']`. That is not
   sloppiness: the CONTINUE check is taken **off the grind tile**, so it is unreachable by
   construction when the bot does not go back. ‼ But the project's own standard is *“each arm fails
   for ITS OWN reason”*, and this one fails for its own reason **plus a consequence of it**.
3. ⛔ **THE VACUITY ARM DID NOT FIRE, AND WHAT I GOT INSTEAD WAS A REPLICATION.** Pointed at
   `post_e4ice_FINAL.ss1` expecting a refusal, the guard correctly passed it through — that fixture
   is `worst_hp=89.0% pp=401/405`, below the full-HP+full-PP threshold. **No fixture in this repo is
   at full HP and full PP**, so no arm can fire that guard.
   ⇒ ⭐ What that run actually produced is a **SECOND INDEPENDENT REPLICATION**: a different fixture
   with a different **L75** party reaching the same PASS. That is genuinely worth more than a
   determinism replay (`CLAUDE.md`: identical output across runs is a determinism check, never a
   replication) — but it is **not** the test it was labelled as, and the evidence file is renamed
   `REPLICATION-L75` to stop it being cited as a vacuity arm.
   ⇒ ✅ **The guard is instead SELF-TESTED in-process, in BOTH directions** — it must call a synthetic
   full-HP/full-PP party vacuous AND must NOT call a damaged one vacuous:
   `VACUITY GUARD SELF-TEST OK — refuses full HP+PP, accepts a damaged party`. That closes the
   `#24-pathguardblind` hole (a guard whose only evidence is that it never fired).

## ‼ ONE INSTRUMENT DEFECT FOUND AND FIXED MID-DRIVE

v1 read `C-ATPC` as *“am I on the Poké Center map when the heal generator finishes?”* and recorded a
MISS — while the route trace on the very next line plainly contained the Poké Center. Cause:
`heal_in_pokemon_center` **enters, heals and walks back out**, so by the time it returns the bot is
outdoors by design. **The reading was true and then stopped being true before I looked at it.**
⇒ fixed by taking it from the ROUTE, which the sampler was already recording correctly.
‼ This is this project's own rule — *record a reading AT ITS TAKE POINT* — and the sampler one line
above was already obeying it.
