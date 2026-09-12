# PREDICTIONS — enabling `POKEBOT_MAINTAIN` by default (user ruling, 2026-09-12)

⛔ **FILED BEFORE THE WORK, ON PURPOSE.** Written while the fix is still unbuilt and the verification
batch unrun, so that the acceptance bar cannot be adjusted after seeing the result. Grade this file
afterwards, item by item, and record which predictions were WRONG — a wrong prediction here is a
RESULT, not a failure of the run.

## THE SITUATION

The user has ruled that the top-up feature ships ENABLED (`06-DECISIONS-LOG.md`, 2026-09-12 user
ruling — that entry carries the DO-NOT-REOPEN). My recommendation had been OFF; the value question
is settled and is not to be re-argued.

⭐ **THE QUESTION HAS THEREFORE CHANGED, AND THAT CHANGES THE BAR.** Every previous batch asked
*"is the feature BETTER?"*. This one asks *"does enabling it make runs WORSE?"* — a **safety**
question. ⇒ the acceptance test is **ON ≤ OFF on run-enders**, NOT **ON > OFF on badges**.
⛔ Do not grade this work against the old bar; a neutral badge result is a PASS here, not a failure.

## WHAT IS BEING BUILT, IN ORDER (the order is itself a prediction)

1. Fix the heal-nav run-killer (`#26-healnavbare` part 2).
2. Resolve or BOUND the ROUTE111 frequency inflation.
3. Flip the default to ON — its own reviewable change, never a side effect.
4. Verify by batch that ON is SAFE.

**P0 — THE ORDER MATTERS AND THIS IS THE FALSIFIABLE CLAIM.** Enabling the feature multiplies the
failure modes it aggravates (heal-nav measured **15 ON vs 3 OFF**, ~5×). ⇒ if step 3 happened before
steps 1–2, a user running the feature would meet those failures at the elevated rate.
**FALSIFIER:** if the post-fix batch shows heal-nav derails in the ON arm at or above the pre-fix ON
rate (~15 per ~91 runs), the fix did not work and the ordering argument gains nothing.

## PER-ITEM PREDICTIONS AND THEIR FALSIFIERS

**P1 — The heal-nav fix eliminates the ELEVATION, not the failure.**
The underlying `heal_in_pokemon_center` walk failure is a real world condition (a scripted event
near a Poké Center door). The fix should stop it KILLING the errand's run, not stop it happening.
* PREDICT: ON-arm run-ending heal derails drop to ≈ the OFF-arm rate or to 0.
* PREDICT: the *raw* `kept interrupting the walk to … after 8 ride-outs` message still appears.
* ⛔ FALSIFIER: if that message disappears entirely, the fix suppressed the symptom instead of
  handling it — **that is a REGRESSION even though the numbers look better.** Check this explicitly.

**P2 — ⛔ THE FIX MUST NOT CHANGE BEHAVIOUR FOR THE OTHER ~40 CALLERS.**
`heal_in_pokemon_center` has ~40 call sites across the story (verified by grep, 2026-09-12).
* PREDICT: a new NARROW subclass of `BotModeError` is invisible to every existing handler, because
  a subclass still satisfies their `except BotModeError`.
* ⛔ FALSIFIER: any non-maintenance chapter changes its heal behaviour ⇒ the design is wrong.
* ⛔ **NON-NEGOTIABLE:** no broad `except BotModeError` in the errand. `StoryAbort` IS one (KI-67);
  gate #27 and `repro_no_silent_except.py` are ratcheted and must stay green.

**P3 — ROUTE111: I predict the mechanism is NOT in the decision logic.**
Measured already: the derails are 1:1 with a `relocating to ROUTE111` decision; the fodder patch is
ROUTE116 in 100% of cases in BOTH arms; and the team LEVELS at that decision are the same in both
arms. So the bot is not deciding differently — it reaches the decision 2.2× more often per run.
* PREDICT: the driver is *how often the ON arm arrives at that seam*, not *what it chooses there*.
* ⛔ FALSIFIER: evidence that the ON arm picks ROUTE111 where the OFF arm picks something else at
  the same team level would refute this and send the fix into `best_training_area` instead.
* ‼ If UNRESOLVED after research, the acceptable outcome is to **BOUND** it (stop it ending runs),
  not to leave it unhandled because the cause is unknown. A bound is shippable; a mystery is not.

**P4 — Promotion is a SEPARATE, USER-AUTHORISED step, and the hazard is real.**
Verified 2026-09-12: the default lives at `sandbox-pokebot/…/story_mode.py:2300` and
`custom-pokebot/…/story_mode.py:2296`, and the two forks' `story_mode.py` **DIFFER** (custom holds
the PRE-FIX, run-killing version).
* ⛔ PREDICT: flipping the flag ON in `custom-pokebot` WITHOUT promoting the fixes would produce the
  worst available combination — the feature enabled on top of the code that killed 406 runs.
* ⇒ the four drifted files promote TOGETHER or not at all, and only with explicit user approval.

## HOW THIS GETS GRADED

The verification batch is two arms, `--build sandbox`, and is read ONLY when finished.
Report, per arm: run count, **median run duration** (from the `debug-YYYYMMDD-HHMMSS.log` start
stamps — NOT log byte size), **badges won per run** (`^BADGE: ` lines), derail rate, and the counts
for heal-nav, ROUTE111 and the ROUTE102/117/103/101 family.

⛔ **DO NOT use `probe_maintain_window.py`'s laggard-gap episodes as an outcome metric.** Measured
2026-09-12: it flattered the HARMFUL arm because per-batch counts are uninterpretable across arms
whose runs have different lifetimes.

⛔ **A ZERO IS ONLY MEANINGFUL BESIDE ITS NON-VACUITY CONJUNCT.** Report "0 heal-nav derails" only
together with the count of heals actually attempted; a zero beside a zero means nothing. This
project has already been fooled twice by exactly that.
