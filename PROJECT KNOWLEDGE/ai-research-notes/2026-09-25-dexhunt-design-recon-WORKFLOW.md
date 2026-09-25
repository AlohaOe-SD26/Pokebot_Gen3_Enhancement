# FOUR DESIGN QUESTIONS, RESEARCHED AND ADVERSARIALLY VERIFIED — before any code

**Date:** 2026-09-25. **Method:** a 16-agent workflow — 4 research agents (one per question), each
put through **3 distinct adversarial lenses** (citation / safety / omission). 0 errors.
**Status:** NOTE. ✅ = I verified it myself; ⚠ = agent-reported; ⛔ = a hazard to design against.
‼ **The verifiers refuted most of the research on CITATION ACCURACY while leaving the SUBSTANCE
standing.** Treat every line number here as needing re-derivation; treat the mechanisms as solid.

---

## 1 ⛔⛔ NEVER-KO — the list is BIGGER and stranger than "six legendaries"

⚠ **Destroyed permanently by a WIN:** the roaming Latias/Latios, Regirock, Regice, Registeel,
Groudon, Kyogre, Rayquaza — **and SUDOWOODO, which is ALSO destroyed by FLEEING.**
⚠ Mew / Deoxys / Lugia / Ho-Oh / the Southern Island Lati merely cost an Elite Four **re-clear**.

**FOUR TRAPS, each of which defeats the obvious guard:**
* ⛔ **THE EQUALITY TRAP.** The retail ROM tests `gBattleOutcome & B_OUTCOME_WON` with
  `B_OUTCOME_WON == 1`. ⇒ **DREW (3) and PLAYER_TELEPORTED (5) are ODD, so they kill the roamer
  too.** A guard written as `outcome == B_OUTCOME_WON` misses both. (The `#else BUGFIX` branch in
  the decomp is NOT active — `//#define BUGFIX` is commented out.)
* ⛔ **ROAR AND TELEPORT DESTROY THE ROAMER.** Both read as "non-damaging escapes" and both produce
  outcome 5. **Only `run_away()` (outcome 4) is safe.** This is the trap most likely to be walked
  into, because a "flee safely" fallback looks obviously correct.
* ⛔ **A MUTUAL KO COUNTS AS A WIN.** Recoil, Destiny Bond, Explosion and end-of-turn residual
  damage all reach outcome 3. A guard that only filters the CHOSEN MOVE will not see the roamer
  dying to Toxic on the end-of-turn tick.
* ⛔ **`gBattleTypeFlags == 0` FOR SUDOWOODO, ELECTRODE, VOLTORB AND KECLEON** — bit-identical to a
  random wild battle. A flag-only guard reports "ordinary encounter" and fights to win. **Species is
  the only discriminator for those.**

⚠ **THE LIVE SIGNAL:** `gBattleTypeFlags` bit 10 (Roamer) / bit 13 (Legendary), **plus opponent
species** for the flagless four.
✅ **OUR REPO HAS NO SUCH GUARD TODAY** (searched: no legendary / never-KO / roamer special-casing in
the battle strategy). ⇒ this must exist BEFORE any legendary is approached.
‼ And per project rule 7: log the move actually submitted and the resulting outcome — *"a guard
fired" is a CANDIDATE, not an ATTEMPT.*

---

## 2 ⭐⭐ FEEBAS — we already own the solution and it is wired to the wrong thing

⚠ **`modules/fishing.py::get_feebas_tiles()` ALREADY COMPUTES THE EXACT SIX TILES** from one 16-bit
save value (`dewfordTrends[0].rand`), and the agent verified its algorithm against the decomp
line-for-line. **But it is wired ONLY to the debug GUI**, while the real `FeebasMode` blind-sweeps
~440 tiles. ⇒ wiring the existing helper turns a multi-hour sweep into a handful of casts.

⛔ **TRAPS, and the second one is the one this project keeps paying for:**
* ⛔ **THE TILE IS THE ONE YOU FACE, NOT THE ONE YOU STAND ON**
  (`GetXYCoordsOneStepInFrontOfPlayer`). A bot that surfs ONTO a computed tile and casts is testing
  the WRONG tile and will produce a clean, confident, entirely false refutation.
* ⛔ **THE VACUITY TRAP.** A seed-driven run only visits computed tiles, so *"we found Feebas on a
  computed tile"* is **true by construction and proves nothing.** It needs an **ARM B control**:
  casts on a NON-computed tile, expecting zero Feebas.
* ⛔ **THE SEED IS NOT STABLE** — `UpdateDewfordTrendPerDay` re-sorts on every RTC day rollover, so a
  long hunt can be fishing yesterday's tiles.
* ⛔ **EVERY FAILURE MODE PRODUCES SIX VALID-LOOKING TILES AND NO EXCEPTION** (wrong save offset,
  wrong candidate count, wrong scan order). There is nothing to catch.
* ⚠ A verifier corrected the research's own cost figures — the counter it proposed bounding counts
  **BITES, not casts** — so any budget written in the wrong unit is wrong by ~2×.

---

## 3 ⛔⛔ WIDENING THE HM HUNTING GROUNDS — the naive version fails on the FIRST line

⚠ **`encounter_index` ROWS CARRY NO TILE.** They are `{map, map_name, method, rate, min/max level}`.
`ensure_hm_learner` needs `(map_enum, tile)` for `calculate_path` and `_navigate_riding_out`.
⇒ **"just use encounter_index" does not compile past the first use.** This alone settles the design.

⚠ **AND THE SCALE IS THE HAZARD:** curated 10 maps → **87**, of which **~67 are places a story-time
hunt must never walk into** — 6 Safari Zone (**ZERO EXP and you cannot attack**), 8 Magma Hideout,
8 Seafloor Cavern, 8 Mt Pyre, 5 Shoal Cave, 5 Meteor Falls (deep rooms behind Waterfall)…
⚠ **THE RANKING INVERTS INTO THE WORST CASE:** `ensure_hm_learner` takes `reversed(grounds)` —
furthest-progressed FIRST. Over 87 maps that means *"prefer Seafloor Cavern / Sky Pillar"*.
⚠ **THE CIRCULAR PICK IS MEASURED, NOT THEORETICAL:** batch `20260731-105549/L01` — seconds after
*"HM03 Surf incoming"* the hunt announced *"hunting Linoone/Zigzagoon on ROUTE119"*, **a SURF-GATED
ground, for the SURF hunt.**
⛔ **A FAIL-SAFE REACHABILITY FILTER CONVERTS A COSTLY HUNT INTO A RUN-ENDING DERAIL** —
`is_map_reachable` returns False for EVERY map on ANY read failure, so a naive "just filter by
reachable" empties the list and the leg raises.
⚠ **AND EXTENDING THE BLACKLIST IS THE WRONG SHAPE** — a 3-entry exclusion over 10 curated maps is
maintainable; over 87 it becomes *"an ever-growing list of game facts written from memory"*, which
this project forbids outright.

⇒ ⭐ **THE DESIGN: WIDEN THE TABLE, NOT THE INDEX.** Curated-list-FIRST (it has tiles, and they are
two-way SWEPT), with an `encounter_index` fallback gated behind a swept-tile whitelist, a level-band
cap, a caller-injected capability predicate (can I even use Surf yet?), and a **never-empty**
reachability rank that wraps the WHOLE chain — a verifier noted the never-empty guarantee must not
be attached to one filter while others can each empty the list alone.

---

## 4 THE PC-FIRST WIRING — five hazards, and one bug in code shipped TODAY

✅ **A BUG IN MY OWN CODE, FOUND AND FIXED.** `boxed_hm_learner_pids`'s docstring claimed *"the
caller may pass the whole list to `withdraw_from_box`, which tries them in order."* **FALSE** —
`find_in_box(pids)` iterates **THE BOX** and returns the first **BOX-ORDER** match, discarding
caller order entirely. A caller following that sentence would silently throw away the ranking and
withdraw whichever qualifying mon sits earliest in the box. ⇒ **pass `[:1]`**, and the docstring now
says so. *(Verified by reading `pc_trip.py:397-412` myself, not taken on report.)*

⚠ **FOUR MORE, each of which would have made the feature decoration or worse:**
* ⛔ **REUSING `_hunted_counter_pids` IS UNSAFE EVEN WITH SAVE/RESTORE** — the counter is boxed
  INSIDE the swapped window by `withdraw_from_box`'s own make-room deposit, and a `finally` restore
  cannot un-box it. ⇒ use a **separate attribute**.
* ⛔ **DO NOT SET `_needs_party_slot`** — `withdraw_precedence` returns `(False, "DEFERRED…")`
  whenever a deposit is also wanted (`#24-pcpingpong`), so the withdraw would be skipped **100 % of
  the time** while the log printed a tidy, plausible DEFER line.
* ⛔ **`heal_centers` DEFAULTS TO `()`** — a PC-first block that does not guard on it is a silent
  no-op: precisely the *"built, driven to a PASS, promoted, and nothing in production ever set the
  flag"* failure KI-63 records.
* ⛔ **DISARM IN A `finally`** or the hook fires on every later heal — the measured harm that keeps
  `POKEBOT_PC_ROTATION` pinned at 0.
* ⚠ **AND A LATENT EGG BUG IN THE CONSUMER:** `withdraw_from_box` counts room with a list that
  excludes eggs, while `pc_interaction._do_withdraw_actions` raises using `get_party_size()`, which
  **includes** them. A party of 5 + 1 egg breaks it. ‼ `08-MISTAKES.md` holds the identical egg bug
  in `deposit_one_dead_weight` as prior art — **the same mistake, in the sibling function.**

---

## WHAT I AM DOING WITH THIS

1. ✅ Fixed the false docstring (done — it was mine, and shipped).
2. The never-KO guard is the **highest-severity** item and must land before any legendary hunt.
3. Feebas: wire the EXISTING `get_feebas_tiles()`, with the ARM B control, not a new sweeper.
4. The hunting-ground widening is a TABLE extension, not an index swap.
⛔ Every line number above needs re-deriving at implementation time — the verifiers found the
research's citations drifted repeatedly even where the mechanism was right.
