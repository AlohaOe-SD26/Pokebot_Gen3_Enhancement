# ⛔ `#24-trainingbrackets` IS CLOSED WITHOUT A CODE CHANGE — THE DEFECT IS NOT REACHABLE, AND THE REMEDY IS ALREADY SHIPPED (2026-09-18)

> ⛔⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** Three agents (code trace, adversarial, bracket survey)
> plus my own measurements. ✅ marks what **I** verified at FILE:LINE or measured myself.

---

## ⭐⭐ THE VERDICT

The item proposed promoting `VICTORY_ROAD_1F` into `TRAINING_GRASS` with tile `(15,39)`, plus an
`AREA_PREREQ` row and a regression gate. **Do none of it.** Five independent reasons, each verified:

### 1. ✅ THE DEFECT IS NOT REACHABLE IN PRODUCTION — I MEASURED THIS MYSELF

The item's premise was our own measured defect: `best_training_area(team_level=53)` returns
`ROUTE117 (31,16)` with **L13-14** wilds. That is TRUE — **and only at `allow=None`.**

| team level | `allow=None` (the shape the defect was measured with) | `allow=<permissive>` |
|---|---|---|
| L20 | ROUTE117 (13,14) | ROUTE111 (19,22) |
| L30-L75 | **ROUTE117 (13,14)** | **ROUTE121 (25,28)** |

⭐ **WHY:** every higher-band row in `TRAINING_GRASS` carries an `AREA_PREREQ` — `ROUTE111:"region"`,
`ROUTE115/118/119/121:"surf"` — and `allow=None` skips exactly those. The ungated remainder tops out
at ROUTE117's L13-14. **The scorer is not broken; the conservative default is doing its job.**

✅ **AND NO PRODUCTION CALLER PASSES `allow=None`.** All four pass a real predicate:
`counter_hunt.py:647` (`_counter_area_allowed`), `story_mode.py:2659` (`_maint_allow`),
`story_mode.py:3168` and `:3199` (`_allow`). ⇒ **the L13-14 answer is a harness/probe-only artifact.**

### 2. ✅ THE REMEDY IS ALREADY SHIPPED — §Ch23 ALREADY GRINDS ON THAT EXACT TILE

`victory_road.py:2087-2090`:
```python
yield from train_team(
    target, slots={0}, grass=TRAIN_SPOT_1F,
    heal_center=PokemonCenter.EvergrandeCity,
)
```
with `TRAIN_SPOT_1F = (VR1F, (15, 39))` (`:477`) — **the identical tile the item proposed to add.**
⇒ promotion would not unlock a Victory Road grind. It would re-route an already-working hardcoded
path through a generic picker that lacks the support that path has.

### 3. ⛔ THE PROPOSED REGRESSION GATE IS SELF-REFUTING — ✅ AND I REPRODUCED IT MYSELF

The third requirement I recorded was a gate asserting `best_training_grass(40) is not
VICTORY_ROAD_1F`. An adversarial pass first re-implemented the function and executed it.
✅ **I THEN REPRODUCED IT AGAINST THE LIVE MODULE**, appending the hypothetical row (and the
`AREA_PREREQ` row) in memory and restoring both afterwards: `best_training_grass(allow=None)`
returns **`VICTORY_ROAD_1F(15,39)` at L35, L40, L53 and L75** — so the assertion is false from
**L35 up**, not merely at the L40 the gate named — while `best_training_area(allow=None)` stays
ROUTE117 throughout. Score `(|41-40|, -40) = (1,-40)` beats ROUTE121's `(13,-28)`.
‼ **AND A NUANCE NEITHER PASS EXPECTED: the two pickers ALREADY DISAGREE TODAY** — with no
change at all, `best_training_grass(allow=None)` answers ROUTE121 while `best_training_area(allow=None)`
answers ROUTE117, because only the latter honours `AREA_PREREQ`. ⇒ the gate is FALSE the day the row lands,
because `best_training_grass` does no filtering at `allow=None` **by design**
(`training_areas.py:213-219`, so `decide_maintenance`'s pure decision is not disturbed).

### 4. ⛔ THE GENERIC PATH LACKS WHAT THE HARDCODED PATH HAS

* `_training_area_heal_map()` (`story_mode.py:1420-1450`) has **no `VICTORY_ROAD_*` row**, and two of
  its three consumers have **no None-guard** — `story_mode.py:3210` and `counter_hunt.py:651` both do
  `.get(map, cfg["heal"])`, silently substituting **the boss's own, possibly cross-Hoenn, heal
  centre**. Only `decide_maintenance` (`:1560-1561`) fails safe. *(Filed as `#24-healmapfallback`.)*
* `_exit_training_cave_if_inside()` no-ops for Victory Road — it is absent from `_CAVE_EXITS`
  (`early_game.py:2003-2046`, only `GRANITE_CAVE_1F` / `FIERY_PATH`).
* A bare `train_team` has **no frame cap** — only a 500-round guard (`early_game.py:2139`).
  `MAX_TRAINING_FRAMES = 250_000` is enforced by `train_for_victory_road` **before** calling
  (`victory_road.py:2020-2027`). ⇒ a generic caller inherits none of it — KI-28's 19.9M-frame shape.

### 5. ⛔ THE CODE ALREADY CARRIES A DATED WARNING AGAINST THIS EXACT CHANGE

`victory_road.py:3425-3429`: *"§Ch23's hardcoded `TRAIN_SPOT_1F` is the ONE PATH that bypasses it.
⛔ Do NOT act on that without an adversarial pass: 'training elsewhere' is one of the five
MEASURED-WRONG entries on `#24-ch23training`."* ⇒ it got its adversarial pass. It was refuted.

---

## ⭐ THE USER RULING IS SATISFIED — BY CODE THAT ALREADY EXISTS

> *"level 30s should not be fighting level 3-5 for xp"* … *"maybe we need to map and mark training
> areas for pokemon for level brackets"*

✅ §Ch23 trains a ~L47 party on Victory Road's **L36-40** wilds — a ~1.2× gap. The ruling's failure
mode does not describe production. And the bracket map the ruling asks for **already exists**, as a
proven block at `training_areas.py:27-61`.

---

## ⭐⭐ THAT BLOCK IS NOW INDEPENDENTLY CORROBORATED, DUAL-SOURCE

`training_areas.py:27` is marked **"THE L28 CEILING IS THE GAME, NOT A GAP IN THIS TABLE. PROVEN
2026-09-10 — DO NOT RE-SURVEY."** A survey agent checked it against **two** independent sources — the
pret decomp's `src/data/wild_encounters.json`, and **our own live-ROM extraction**
(`cache/encounter_index_BPEE0.json`, built by `modules/map.py`'s `gWildMonHeaders` walk against a real
loaded ROM). **38 map/method rows diffed. Zero mismatches.** The block stands.

What it confirms, unsoftened:
* **L55+: NOTHING.** The highest level on any table by any method anywhere is **50**.
* The two tables reaching 50 are both unusable: **Artisan Cave** (Smeargle) and **Route 130 / Mirage
  Island** (Wynaut) — and **Desert Underpass** (35-45) is walled by `FLAG_SYS_GAME_CLEAR`
  (`data/maps/Route114_FossilManiacsTunnel/scripts.inc`), **the very flag §Ch24 itself sets**, so it
  cannot prepare *for* the Elite Four, only follow it.
* **Victory Road B2F (L40-44) is the highest usable wild grass in the pre-clear game.**
* Safari Zone's tempting L33-40 **rate-25** tables give **zero EXP** — confirmed structurally this
  time: the Safari action table replaces Fight/Bag/Pokémon/Run with Watch/Ball/Pokéblock/GoNear/Run
  (`src/battle_main.c`), so **a KO is impossible**, not merely disallowed.

⇒ **No wild grind reaches L62-75 at a sane rate.** Best case for L60→75 is ~170-320 **wins** against
the richest wild in the pre-clear game, before travel or the 5.56%/step encounter rate.

---

## ⭐ GENUINELY NEW, AND WORTH KEEPING

* ⛔ **A CORRECTION TO OUR OWN PROVEN BLOCK.** It calls Mirage Island *"a 1/256 daily RNG gate."*
  **Wrong, and not by a little.** `src/time_events.c`'s `IsMirageIslandPresent` compares the **HIGH** 16
  bits of a daily RNG value (`GetMirageRnd() >> 16`) against the **LOW** 16 bits of **each party
  mōn's PID** (`& 0xFFFF`) ⇒ ≈6/65536 ≈
  **1-in-10,923**, about **42× rarer**. The conclusion (not a training ground) is unaffected; the
  number is fixed in place, because a wrong figure inside a DO-NOT-RE-SURVEY block is exactly what
  erodes trust in the block.
* ⭐ **VICTORY ROAD B1F'S ROCK SMASH TABLE IS L30-40 AT RATE 20** — *twice* the encounter rate of any
  Victory Road grass table (rate 10), for a band only ~2 lower than B1F's own grass. If throughput
  ever matters more than band, that is the lever. ⚠ B1F is OFF THE TABLE per USER RULING 2 — noted
  for if that is ever revisited, not proposed.

---

## ⇒ WHAT ACTUALLY REMAINS

**`#24-levelgap`** — a purpose-built §Ch24 stepped training leg driving `train_team(...,
grass=TRAIN_SPOT_1F)` directly, with its own frame budget, derived from MEASURED cost. That is
already the ruling, and nothing here changes it. **`#24-trainingbrackets` was the wrong road to it.**
