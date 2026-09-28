# 2026-09-27 — RULING 21 swap-back after an EVOLUTION: PRE-REGISTERED PREDICTIONS

> Filed BEFORE the graded drives. Branch `wt/swapevo` (cut from `wt/restock`). Found by the Phase 2 build spec
> (`2026-09-27-ruling20-phase2-BUILDSPEC.md` §5 F4, a NOTE); verified at FILE:LINE before any code:
> `_record_fly_swap` records the fighters as `(pid, species)` in the lobby, BEFORE §Ch24 training, and
> `restore_ch24_fighters` required the party to EQUAL that list. Training takes the under-levelled trainees from ~L47
> toward L65, where many evolve. An evolved fighter therefore made the check refuse the guards, and every re-entry after
> it (the record persists).

## THE FIX UNDER TEST

`ch24_fighters_restored(party_keys, fighters)`: each recorded fighter is matched by exactly one party member with the
SAME PID whose species is the recorded one or an evolution of it (`evolves_from` walked to the base). An unrelated
species on the same PID, a de-evolution, a different PID, or a missing fighter still refuses. Arm
`POKEBOT_R20_FAULT_SWAPEXACT=1` restores the exact test. Gate `probe_r20_flybox.py` F7 (9 pure cases + the arm + wiring).

## THE DRIVE — `--driver flybox`, `post_moveset.ss1` (PINNED)

The `swap` staging (Swellow boxed, a Machop filler, so production box-first withdraws Swellow and boxes Zigzagoon), then
the RECORD is rewritten before the restore: Sceptile#863B0917 (a fighter that stays in the party) reads as "Grovyle"
(`evolved`: what the check sees after a Grovyle evolves in training) or "Mightyena" (`wrongline`: an unrelated line).
**Discriminator:** in `evolved` the party holds (863B0917, Sceptile) while the record holds (863B0917, Grovyle), so the
exact test and the fixed test DISAGREE on this input; in the untouched `swap` arm they agree.

| Arm | Predicted |
|---|---|
| `evolved` (fix) | the swap-back runs ([deposit Swellow, withdraw Zigzagoon]); `F-RESTORED`; no error; party = the six fighters |
| `evolved` + `POKEBOT_R20_FAULT_SWAPEXACT=1` (`FB_EXPECT=refuse`) | the same swap-back actions; then REFUSES by name ("RULING 21"); no `F-RESTORED` |
| `wrongline` | the same swap-back actions; REFUSES by name; no `F-RESTORED` |
| `swap` (regression) | unchanged: PASS as on 2026-09-27 |

## FALSIFIERS

- `evolved` refuses: the evolution walk does not see Grovyle → Sceptile, or the check is not the one deciding.
- `evolved` + SWAPEXACT passes: the arm is not read, or the rewrite never reached the record.
- `wrongline` passes: the check has become PID-only, which KI-78 forbids.

## WHAT THIS DOES NOT SHOW

- A real in-training evolution: the record is rewritten instead. The check's inputs are identical, so this tests the
  CHECK, not the training.
- How often the swap happens at all (it needs a Fly learner in the box and none in the party).
