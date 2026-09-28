# 2026-09-27 — RULING 21 swap-back after an EVOLUTION: GRADED

> Predictions: `2026-09-27-swapevo-PREDICTIONS.md` (commit `769f5491`, filed BEFORE these drives). Branch `wt/swapevo`.
> Evidence: `tools/story-dev/evidence/2026-09-27-swapevo-SW{1-evolved,2-evolved-exact,3-wrongline,4-swap-regression}.*`.
> ⚠ One fixture (`post_moveset.ss1`), one trajectory per arm: a CORRECTNESS result, not a frequency.

## THE DEFECT (found by the Phase 2 build spec, §5 F4; verified at FILE:LINE before any code)

`_record_fly_swap` records RULING 21's fighters as `(pid, species)` in the League lobby, before §Ch24 training.
`restore_ch24_fighters` then required the party to EQUAL that list. §Ch24 training takes the under-levelled trainees from
~L47 toward L65, where many species evolve (e.g. Lairon → Aggron at 42, Vibrava → Flygon at 45, Shelgon → Salamence at 50). The PID survives an
evolution; the species does not. So a correct party refused the guards, and the record persisted, so every re-entry
refused again. It shipped in increment B (`wt/r20fly`, not yet merged), so no batch run has hit it.

## RESULT — ALL FOUR ARMS AS PREDICTED

| Arm | Predicted | Measured | Grade |
|---|---|---|---|
| `evolved` (fix) | swap-back runs; `F-RESTORED`; no error | actions [deposit Swellow#0B30A747, withdraw Zigzagoon#33CB74C3]; record held `Grovyle#863B0917`, party `Sceptile#863B0917`; `F-RESTORED`; no error | ✅ |
| `evolved` + `POKEBOT_R20_FAULT_SWAPEXACT=1` | same actions; REFUSES by name | same actions; "§Ch24 RULING 21: the party is not the six recorded fighters…"; no `F-RESTORED` | ✅ |
| `wrongline` | same actions; REFUSES by name | record `Mightyena#863B0917` vs party `Sceptile#863B0917`: refused by name; no `F-RESTORED` | ✅ |
| `swap` (regression) | PASS as before | PASS | ✅ |

⇒ **The A/B is `evolved` vs `evolved` + SWAPEXACT: the same staging, the same swap-back, and only the check differs.** The
fix restores; the old exact test refuses. `wrongline` shows the check is still an identity check, not PID-only.

## THE REVIEW (adversarial, the full diff): KICK-BACK, fixed

1. **Deleting the count check left the gate green** (proven by the reviewer's mutation). Added an F7 case (every fighter
   plus an extra member ⇒ refused) and a fault arm that deletes the check; it FAILS.
2. The docs followed the review, as planned.
3. ⛔ **The reviewer reverted its mutation with `git checkout --` on the UNCOMMITTED fix**, which restored the pre-fix
   file. The gate's wiring check went red and exposed it. The fix was re-applied (the diff is exactly the two original
   hunks), and the decisive pair (`evolved`, `evolved` + SWAPEXACT) was re-driven on the restored code: see the `re-`
   evidence files and `07-CHANGELOG.md` 2026-09-27. `08-MISTAKES.md` records the rule: commit before a mutating review.
Raised and not changed: the carrier's own key is still compared exactly (it is not trained, so it should not evolve;
unaudited); `_same_or_evolved` has no fail-closed fallback for an unknown species name (both inputs come from the game's
species table).

## WHAT THIS DOES NOT SHOW

- A real in-training evolution: the RECORD was rewritten instead. The check's inputs are identical, so this tests the
  check, not training.
- How often the swap happens (it needs a Fly learner in the box and none in the party).
- Known limit, documented in the gate: the species data lists Shedinja `evolves_from` Nincada, so a recorded Nincada
  matches a Shedinja on its PID. It is unreachable here, because the swap party is full (so no Shedinja can appear) and
  the count check comes first.
