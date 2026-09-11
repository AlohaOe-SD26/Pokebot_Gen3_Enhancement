# 2026-09-11 — `#24-maintain` PREDICTIONS (pre-registered, filed BEFORE the drive)

⛔ Filed before any code is written. A reading that contradicts a prediction below is a **RESULT**,
never a driver failure.

## WHAT IS BEING BUILT

`_maintain_lagging_battler()` — one new method on the story mode, called from **exactly one seam**:
the TOP of `_prepare_for_fight`, before the sufficiency gate's early `return` at `:2202`.

```
catchup  = target - self.TRAIN_CATCHUP_GAP        # the EXACT quantity :2377 excludes on
excluded = [i for i in battlers if party[i].level < catchup]
if not excluded:                   return          # nothing is being abandoned
slot     = min(excluded, key=level)                # weakest first
ground   = best_training_grass(party[slot].level)  # ITS level, never the boss's
if ground is None:                 return          # honest stop, logged
est      = estimate_frames_to_level(party[slot], catchup, wild_max(ground))
if est is None or est > budget:    return          # fail-safe skip, logged
_rotate_lead_safely(slot)
train_team(catchup, scope="lead", grass=ground, heal_center=_training_area_heal_map()[ground_map])
```

⭐ **THE PREDICATE IS THE EXCLUSION'S OWN, AND THE TARGET IS "BECOME ELIGIBLE AGAIN".** Maintenance
does not guess a gap against party max and does not try to match the boss. It asks the one question
that matters — *which battlers is `:2377` about to abandon?* — and lifts exactly those to `catchup`,
the threshold at which the EXISTING, already-budgeted prep path will pick them up and finish the job
at the boss ground (where, being now within 6, they can actually win).
⛔ A mon 30 behind still fails the estimate gate and is SKIPPED with a reason. That is correct and is
prediction P4: no ground serves it, and pretending otherwise is the measured trap (69 battles,
0/43 HP, still L13).

### Why this seam and not a chapter loop
`_prepare_for_fight:2376-2377` is where the laggard is ABANDONED:
```python
catchup = target - self.TRAIN_CATCHUP_GAP        # 6
to_train = {i for i in battlers if party[i].level >= catchup}
```
A mon more than 6 below the boss target is excluded from prep training entirely, so it can never
close the gap while the target keeps rising. Maintaining **immediately before** that line means the
first time a mon drifts 6 behind it is topped up — long before it is 30 behind and unwinnable.

### Why `scope="lead"` and NOT `slots={i}`
⛔ KI-84. `train_team`'s slots path computes `need` from SLOT INDICES and then calls
`_rotate_lead_safely`, which permutes the party — so on the next iteration the index refers to a
different mon and `need` empties. `scope="lead"` takes the `need = [0] if …` branch
(`early_game.py:2040`) and stops on `_lead_level()`; it never touches the broken path.
⚠ Note production's relocation branch DOES call `train_team(target, slots=to_train, …)`. That is a
separate question and is NOT being changed here.

## PREREQUISITES — VERIFIED BEFORE WRITING ANY CODE (2026-09-11)
| # | claim | how verified | result |
|---|---|---|---|
| 1 | `best_training_grass` has ZERO production call sites | grep of the sandbox tree | ✅ confirmed |
| 2 | it covers every level a laggard occupies | called it for L2-45 | ✅ 9 grounds, continuous |
| 3 | every returnable ground is healable | keys vs `_training_area_heal_map()` | ✅ 9/9 |
| 4 | the exclusion at `:2376` is what abandons the laggard | read the lines | ✅ verbatim |

## PREDICTIONS (graded after the drive)

| # | prediction | falsifier — what result would mean the build is WRONG |
|---|---|---|
| P1 | With maintenance ON, a staged laggard 10 below party max is trained to within `MAINTAIN_GAP` | it is not trained at all ⇒ the seam never runs, or the gap predicate is inverted |
| P2 | With maintenance OFF (same fixture, same seed), the laggard's level is UNCHANGED | it changes anyway ⇒ **the arms do not differ and the A/B measures nothing** |
| P3 | The chosen ground matches `best_training_grass(laggard.level)`, not the boss's `cfg["grass"]` | it walks to the boss ground ⇒ it will grind unwinnably, the exact trap this item exists to avoid |
| P4 | A laggard 30 below is SKIPPED with a logged reason, not ground at | it attempts it ⇒ re-creates the unwinnable grind (69 battles, 0/43 HP, still L13) |
| P5 | Total frames spent are bounded by the estimate gate; an unknown estimate SKIPS | an unbounded grind ⇒ fail-safe is inverted |
| P6 | The party's LEAD after maintenance is the strongest battler, not the laggard | the laggard stays lead ⇒ it will be sent into the boss first |

⛔ **P2 IS THE VACUITY CONJUNCT.** If ARM-OFF and ARM-ON produce the same laggard level, the fixture
is wrong (probably already ≤ `MAINTAIN_GAP`) and NOTHING has been measured. **Compute the gap on the
fixture and show the arms differ BEFORE reporting anything** — a handed-off spec in this project once
named a fixture that made its own A/B vacuous, and the run would have read as a refutation of a true
finding.

## FAULT ARMS (each must fail for its OWN reason)
- **`POKEBOT_MAINTAIN` unset** — the shipped default; the method returns before any yield ⇒ P1 must
  go RED, P2 GREEN. *(This IS the CLAUDE.md rule 8 arm — "without X the bug survives" is a claim
  whose only currency is an arm with X removed — and it is the PRODUCTION flag, so the A/B reads as
  "on vs off" rather than "on vs on-but-sabotaged".)*
  ‼ *A separate `POKEBOT_MAINTAIN_FAULT=off` arm existed when this note was written and was DELETED
  on 2026-09-11: two switches controlling one behaviour is its own bug shape.*
- `POKEBOT_MAINTAIN_FAULT=bossground` — use `cfg["grass"]` instead of `best_training_grass` ⇒ P3 RED.
- `POKEBOT_MAINTAIN_FAULT=nobudget` — bypass the estimate gate ⇒ P4/P5 RED.

---

## ⚠ PRIOR ART — A SETTLED RULING EXISTS AND IT WAS CHECKED (added before any code was written)

`06-DECISIONS-LOG.md` 2026-09-10 **rejects** "wiring `best_training_grass` (i.e. building
`#24-maintain`)", ending *"Recorded so the next agent does not re-derive 'just call the function'."*
⛔ That ruling STANDS. It measured **late relocation to the BOSS's target level**, which is dead.
This item is the other half of the same slug and differs in the two variables the arithmetic is most
sensitive to:

| | target | ground | frames | vs 250,000 |
|---|---|---|---|---|
| ruled DEAD 2026-09-10 | the BOSS's level (L47) | ROUTE121, wild 28 | **285,167** | ⛔ over |
| this item | `target - 6` (`TRAIN_CATCHUP_GAP`) | keyed to the LAGGARD's level | **4,299 – 63,052** | ✅ under |

⭐ **The estimator was CONTROLLED before it was believed:** it reproduces the 2026-09-10 entry's own
figure — model **285,167** vs that entry's stated "~285,000", within 0.06% — using the same constants
`estimate_frames_to_level` uses. A model that could not reproduce the ruling would have been the
thing to doubt, not the ruling.

‼ **AND HOW THE RULING WAS NEARLY MISSED, which is a finding in itself:** `precheck_prior_art.py`
treats **each argv element as ONE whole-phrase term** matched against a single line. Passing a
natural-language sentence in quotes therefore returns a confident `0 hit(s)` — which reads exactly
like "this is new". Three such queries came back clean; the ruling only surfaced after a CONTROL
query for something already known to be documented (`widen TRAIN_CATCHUP_GAP`) ALSO returned 0 hits,
proving the instrument, not the tree, was quiet.
⇒ **Call it with SPACE-SEPARATED SYMBOLS, never a sentence:**
`precheck_prior_art.py TRAIN_CATCHUP_GAP best_training_grass` → 30 hits, several beside VERDICT words.
⇒ filed as its own defect; a prior-art tool whose failure mode is a reassuring silence is worse than
no tool.
