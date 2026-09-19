# PRE-REGISTERED PREDICTIONS — `#24-trainingbrackets` PIECE 1 (2026-09-19)

> ⛔⛔ **WRITTEN AND COMMITTED BEFORE THE PRODUCTION EDIT.** Graded afterwards, honestly. A reading
> that contradicts a prediction here is a **RESULT**, not a failure of the instrument.

---

## THE CHANGE, AND WHY IT IS NOW REQUIRED

USER RULING 2026-09-19: train each mōn at a **level-appropriate ground**, **flying** to reach it.
✅ MEASURED: from Ever Grande the 4-hop training-travel budget refuses **every** route ground
(ROUTE121 **6** hops, ROUTE118/119 **9**, ROUTE111/117 **11**, ROUTE115 **15**); `VICTORY_ROAD_1F`
at **1 hop** is the only level-appropriate candidate in budget, and it is inert.
⇒ **without this promotion a per-trainee selector returns `None` for every trainee.**

**PIECE 1 — the data foundation only. No selector, no leg, no Fly yet.**
1. `TRAINING_GRASS` gains `(MapRSE.VICTORY_ROAD_1F, (15, 39), (36, 40))`.
2. The now-duplicate `PENDING_GRASS` row for `VICTORY_ROAD_1F` is removed (one map, one list).
3. `AREA_PREREQ[VICTORY_ROAD_1F] = "region"`.
4. `_training_area_heal_map()` gains `VICTORY_ROAD_1F -> PokemonCenter.EvergrandeCity`.
5. NEW GATE: **no production caller may pass `allow=None`** (or omit `allow`) to either picker.

---

## WHAT IS ALREADY SETTLED AND SHAPES THE DESIGN

* ⛔ **Narrowing `best_training_grass`'s `allow=None` default is REFUTED — I measured it.** It
  changes **83 of 99 levels** and makes them all worse (everything L27+ drops from ROUTE121's
  L25-28 to ROUTE117's L13-14). Its docstring's warning is correct. **Do not touch that default.**
* ⇒ Therefore the third guard is **structural, not behavioural**: forbid the dangerous CALL SHAPE
  rather than assert a picker answer. The previously proposed
  `assert best_training_grass(40) is not VICTORY_ROAD_1F` is **self-refuting** — ✅ I reproduced it
  returning VICTORY_ROAD_1F from **L35 up** once the row lands.
* ⛔ **`_CAVE_EXITS` is deliberately NOT touched.** `early_game.py` records those tables as
  *"REDUNDANT, not load-bearing"*, and a cave-heal drive MEASURED `heal_in_pokemon_center` walking
  out of `(15,39)` and back with no row. **Do not fix what is proven working.**
* The frame cap is the LEG's job (Piece 3), not the table's.

---

## PREDICTIONS

### P1 — the picker starts answering Victory Road in the L34-46 bracket, under a REAL predicate
**PREDICT:** with a permissive `allow`, `best_training_area` returns `VICTORY_ROAD_1F (15,39)` for
trainees around **L35-46**, replacing today's `ROUTE121 (25,28)`; and for L60+ it STILL returns
Victory Road (nothing higher exists).
⛔ **FALSIFIER:** if L36-46 still answers ROUTE121, the scorer is not doing what I think and the
promotion buys nothing.

### P2 — the conservative default is UNCHANGED for every level
**PREDICT:** `best_training_area(lvl, allow=None)` answers **identically before and after** at every
level 2-100, because the new row carries an `AREA_PREREQ` and that path skips prereq'd rows.
⛔ **FALSIFIER:** any change means the prereq row is not doing its job, and mid-game exposure is
real. **This is the safety prediction; if it fails I revert.**

### P3 — `best_training_grass(allow=None)` DOES change, and that is expected and harmless today
**PREDICT:** it starts answering `VICTORY_ROAD_1F` from **L35 up** — because that function ignores
`AREA_PREREQ` by design. ✅ **Harmless today because no production caller passes `allow=None`**
(all four pass real predicates: `counter_hunt.py:647`, `story_mode.py:2659`, `:3168`, `:3199`).
⭐ **This is precisely what the new gate exists to keep true.**
⛔ **FALSIFIER:** if it does NOT change, my model of that function is wrong.

### P4 — the new gate fails BEFORE it is satisfied and passes after
**PREDICT:** `probe_picker_allow_required.py` **passes on today's tree** (zero offending callers),
and its FAULT ARM — pointed at a synthetic `allow=None` call — **fails naming that call**.
⛔ **FALSIFIER:** a gate that cannot be made to fail is decoration. ‼ Note this gate is the
*opposite* shape to gate #65: there is no pre-existing defect for it to catch, so **the fault arm is
the ONLY proof it works.**

### P5 — counter-hunt execution is untouched
**PREDICT:** `hunt_ground_tile(VICTORY_ROAD_1F)` stays `None` and no `best_huntable` pick changes,
because `require_driven=True` never reads `TRAINING_GRASS`. ✅ Already measured in arm C on
2026-09-18; re-checked here because the row now really exists.
⛔ **FALSIFIER:** any change makes Victory Road a live counter-catch destination — the exact hazard
the 2026-07-26 gate comment was written about. **I would revert.**

### P6 — the gate suite goes red on STALE PROSE, and that is the suite working
**PREDICT:** the full suite FAILS on first run, naming doc/comment statements the promotion
falsifies (e.g. claims that Victory Road is inert, or that `TRAINING_GRASS` tops out at L28 as a
*table* fact). ⭐ **I am predicting a RED first run deliberately** — those gates exist to catch
exactly this, and a green first run would mean they are not watching this file.
⛔ **FALSIFIER:** if it goes green immediately, check whether those gates actually cover
`training_areas.py` before believing it.

### P7 — ⚠ THE ONE I AM LEAST SURE OF: no OTHER consumer changes behaviour
**PREDICT:** nothing outside the two pickers and the heal map behaves differently.
⛔ **FALSIFIER:** any gate failure that is not stale prose. ⚠ This is an absence claim over a large
codebase and I have been wrong about that shape twice this week. **The suite is its test, not my
confidence.**

---

## WHAT WOULD MAKE ME STOP

1. **P2 fails** — the conservative default changes ⇒ mid-game exposure is real ⇒ revert immediately.
2. **P5 fails** — Victory Road becomes huntable ⇒ revert; that guard is load-bearing.
3. A gate fails for a reason that is **not** stale prose and **not** in the four known constraints.
