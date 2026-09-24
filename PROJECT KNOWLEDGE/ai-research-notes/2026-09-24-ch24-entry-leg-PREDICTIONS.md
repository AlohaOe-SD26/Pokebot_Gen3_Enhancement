# PRE-REGISTERED PREDICTIONS — §Ch24 LEG 1, `prepare_and_open_the_league`

**Written 2026-09-24, BEFORE the drive**, per `.claude/skills/story-drive` §1. Committed first so a
contradicting reading is a **RESULT**, not a driver failure.

DRIVER: ch24entry

FIXTURE: `post_ch24_atdoor_L75.ss1` — the bot at `EVER_GRANDE_CITY (18,6)`, the League door apron,
party at L75 (so the readiness branch should be a no-op and the leg's *travel* is what is on test).

---

## WHAT THIS LEG IS, AND THE ONE THING IT REFUSES TO DO

Get the party gauntlet-ready **outside**, walk in, **talk the guards aside**, assert they moved, and
**stop on `(9,3)` facing the open door**. ⛔ It does **not** step onto `(9,1)` — that is step-on, it
is the point of no return, and nothing is built beyond it.

⭐ The reading that matters is **the assertion**, because nothing in this tree ever made it:
`ch24probe` checked only *"are we on HALL5"* — the consequence two steps later, which cannot
distinguish *"the guards moved"* from *"we got lucky"*.

---

## PREDICTIONS, each with the falsifier that would refute it

### P1 — the leg LATCHES before any button.
GRADED-BY: latch_calls
Predicted `latch_calls >= 1`.
**FALSIFIER:** `0` ⇒ the leg can be entered without owning the run, and a resumed run in the lobby
re-enters §Ch23 (`ch23_chapter_done()` requires `_on_map(EVER_GRANDE)`, false indoors).

### P2 — the premise holds: the door starts SHUT.
GRADED-BY: flag_at_start
Predicted `False`.
**FALSIFIER:** `True` ⇒ the fixture already has the guards moved and the run proves nothing about
opening anything. The driver is built to REFUSE in that case.

### P3 — ⭐⭐ THE GUARDS ACTUALLY MOVE, AND THE LEG PROVES IT RATHER THAN INFERRING IT.
GRADED-BY: flag_at_end, guard_tiles_clear
Predicted `flag_at_end=True` **and** `guard_tiles_clear=True`.
**FALSIFIER — and the two halves fail differently, which is the point:**
* flag True but tiles occupied ⇒ the flag and the world disagree; the leg must refuse to call the
  way clear (it raises).
* flag False ⇒ the A-press never took. ⚠ Either way the door is shut, and *walking at it* would be
  the silent-stall shape this project has already paid for.

### P4 — the bot ends ON the talk tile, not through the door.
GRADED-BY: end_tile
Predicted `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F` at `(9,3)`.
**FALSIFIER:** any `HALL5` reading ⇒ **the leg crossed the point of no return**, which is exactly
what this design exists to prevent. That would be the most serious possible failure here.

### P5 — the readiness branch is a NO-OP on this fixture.
GRADED-BY: leg
Predicted `leg["below_floor_before"] == []` (the party is L75), so no training runs.
**FALSIFIER:** a non-empty list ⇒ either the floor constant or `ch24_trainees_below_floor` disagrees
with the fixture record, and the *travel* half of this drive is then confounded by a 20-hour grind.

### P6 — no whiteouts.
GRADED-BY: start_at
There are no wild encounters and no trainers on `EVER_GRANDE_CITY` or in the lobby.
**FALSIFIER:** any whiteout ⇒ something fights on a route our own recon called empty.

---

## ⛔ WHAT THIS DRIVE WILL NOT SETTLE

* **The gauntlet.** Not one of the five fights is in this leg.
* **Whether the party can WIN.** The game gates entry on `FLAG_BADGE06_GET` only — no level check —
  so passing this leg says nothing about readiness to survive what is behind the door.
* **Re-entry after a loss.** `ENTERED_ELITE_FOUR` is permanent and never cleared, so a future
  gauntlet leg must not treat "healthy again" as "ready again" — a free nurse heal would otherwise
  re-pass a readiness gate forever while levels never change.
* **One trajectory**, from one fixture.

## FAULT ARMS (each must fail for its OWN reason)

| arm | must produce |
|---|---|
| `POKEBOT_CH24_FAULT_SKIPTALK=1` (read in PRODUCTION) | `E1-GUARDS` missing — proves the assertion is live, not decoration |
| `POKEBOT_CH24ENTRY_FAULT=nolatch` | `E1-LATCHED` missing — proves `latch_calls` is a real reading |
