# GRADED — §Ch24 THE CHAMPION LEG (`fight_the_champion`)

Graded **2026-09-25** against `2026-09-25-ch24-champion-leg-PREDICTIONS.md`, committed **before**
the drive (`04f57b8b`). Evidence: `tools/story-dev/evidence/2026-09-25-ch24champion.stdout.txt`.

**THE RUN:** `--driver ch24champion` from `post_hall4_door.ss1`
→ **`ACCEPTANCE: PASS`**, **all TEN readings**, `missing=[]`, `whiteouts=0`, `failure=None`,
`heal_ready=True`, `battles=1`, `BattleOutcome.Won`, **fixture RESTORED**.

⭐⭐⭐ **§Ch24's LAST UNBUILT PIECE IS BUILT, AND IT ASSERTS.** Wallace has now been beaten three
times — but the first two were by an **observe-only probe whose ACCEPTANCE line is instrument health
and which asserts nothing**. This is the first time a *graded production leg* has cleared the game.

---

## THE GRADE

| # | prediction | verdict | evidence |
|---|---|---|---|
| P1 | ⭐ eight raw `Up` presses fire the step-on warp | ✅ **CONFIRMED** | `C-CROSSED`, `cross = 38` frames (ledger: 43) |
| P2 | `C-ENGAGED` from the CALLBACK, not our press | ✅ **CONFIRMED** | `battles=1`, `battle_started_frame=8496840` |
| P3 | ⭐⭐ Wallace beaten, asserted on `BattleOutcome` | ✅ **CONFIRMED** | `<BattleOutcome.Won: 1>`, `whiteouts=0` |
| P4 | the endgame survives the `SoftReset` | ✅ **CONFIRMED** | `C-INHOF` at **`(16,11) (7,16)`**, `C-CLEARED`, `C-REBOOTED` |
| P5 | ⭐ the settle holds TWICE | ✅ **CONFIRMED** | `C-HOME` and `C-USABLE`, both `(1,1) (4,2)` |
| P6 | the heal leaves the party ready | ✅ **CONFIRMED** | `heal_ready=True` |
| P7 | every step comfortably inside its bound | ⛔ **REFUTED** | `intro = 36,457` against a **6,000** bound — and it did **not** refuse |

### ⭐ P1 — THE CROSSING PRIMITIVE WORKS, AND THAT WAS A REAL UNKNOWN

The probe that crossed used a different press loop; this is the production leg's own first crossing,
and it is forbidden from falling back on `navigate_to`/`_pass_through_door` (they make the warp a
*destination* — the trap a tripwire guards one tile earlier). **Eight raw `Up` presses fire it**, in
38 frames against a measured 43.

### ⭐ P4 — THE ARRIVAL TILE IS THE PROOF THE BOT NEVER WALKED A DOOR

`C-INHOF` records `(16,11) (7,16)` — **the scripted `warp`'s literal arguments**. A door the bot
walked through could not have produced that tile. ⇒ the reading distinguishes *"the script warped
us"* from *"we found our way there"*, which is the whole reason it is graded on the map and not on
proximity.

---

## ⛔⛔ P7 IS REFUTED, AND THE REFUTATION IS THE MOST USEFUL THING IN THIS DRIVE

```
intro_frames_spent  = 36,457     ← against a 6,000 bound, and it did NOT refuse
battle_frames_spent = 0          ← the fight, recorded as zero
```

**Neither number is a lie about the run; both are lies about WHICH STEP THE TIME BELONGS TO.**

The intro loop waits for `battle_started_frame`. The generator is **suspended for the entire fight**
(`BattleListener` owns the controller stack), so:
1. it never got a frame on which to evaluate its own bound — **a budget whose loop does not run
   cannot fire**; and
2. when it finally resumed, the battle had already *ended*, so the fight's frames were absorbed into
   the intro's elapsed count and S4 measured **zero**.

⇒ **A FRAME BUDGET CAN NOTICE A SUSPENSION AFTERWARDS; IT CANNOT INTERRUPT ONE.** That is a sharper
statement than the rule I already had (*"bound in frames, not iterations"*) — frames were the right
unit and still could not enforce across a starved span.
‼ **Two facts that must not be conflated:** the **GRADE was correct** — all ten readings, one
battle, `Won`, nothing mis-graded. Only the **attribution** was wrong. A run can be fully right and
its telemetry still misleading.

✅ **FIXED**: `intro_true_frames` and `fight_true_frames` are now computed from the **callback**
latches (`battle_started_frame`, `battle_ended_frame`), which fire regardless of suspension. The
loop-elapsed values are **kept** as `*_wall_frames`, because the gap between wall and true *is* the
measurement of how long the generator was starved.

⛔ **AND THE FIRST VERSION OF THAT FIX WAS ALSO WRONG — CAUGHT ONLY BECAUSE IT COULD GO NEGATIVE.**
It captured the crossing-end clock *after* the intro loop returned, i.e. after that clock had
already run through the whole battle, giving **`intro_true_frames = -34,729`**. A negative duration
is self-evidently impossible, so it was caught in seconds. ‼ An `abs()`, a `max(0, …)` or an
unsigned counter would have shipped a plausible small number instead. ⇒ **do not clamp a derived
duration — a quantity that cannot express "impossible" cannot warn you.**

### ✅ CORRECTED ATTRIBUTION (drive v3), AND AN UNEXPECTED CROSS-CHECK

```
cross 38 · intro_true 1,728 · fight_true 33,846 · chain 2,686 · endgame 14,153 · settle 451
intro_wall 36,457 · battle_wall 0 · starved_frames 883
```

`intro_true = 1,728` against the ledger's 1,648, and `fight_true = 33,846` sits inside the
30,908–34,795 band the two earlier trajectories measured.

⭐⭐ **`starved_frames = 883` IS A CORROBORATION NOBODY ASKED FOR.** It is computed here purely as
*wall − true* — how long the generator waited for a turn after the battle-end latch fired. The build
spec derived **883** from a completely different direction: *"budget on the CB2 window (30,908), not
the latch (29,959) — the latch is 883 frames early"*, i.e. from the CB2 symbol transitions.
⇒ **two independent routes to the same number**, which is what makes it a measurement of a real
offset rather than an artifact of either method. ‼ Recorded as corroboration, not as a new claim.

---

## THE FRAME LEDGER — EVERY OTHER STAGE LANDED ON THE MEASURED VALUE

| stage | this leg | prior ledger |
|---|---|---|
| crossing | **38** | 43 |
| post-battle chain | **2,686** | 2,690 |
| HoF → save → credits → reset | **14,153** | 14,161 |
| settle | **451** | 426 |

⇒ the non-battle portion of the tail is **deterministic to within a handful of frames across three
independent runs**, which is what makes the bounds trustworthy. ⛔ The fight remains the one
variable row and its ~5× bound must not be tightened.

---

## ⛔ WHAT THIS DRIVE DOES NOT SETTLE

* ⭐ **THE WIN RATE.** Three wins, one fixture, one party. Still not a rate, and `on_whiteout` is
  the other exit.
* **`cross_to_the_champions_door()`** — the HALL4 approach leg is **not built**; this leg starts at
  `(5,3)`.
* **RULING 11.** A driver, a pinned fixture, at speed — none of its four conjuncts. `story_mode.py`
  still ends at the END-OF-CONTENT banner and **nothing is wired into `_play`**.
* **The fault arms** (the spec's P4). A treatment that passes is not believed until its arms fail
  for their own reasons — `A4` in particular now has the unhealed fixture it needs.
* **PP as a gate.** `pp_at_door` is recorded as a diagnostic, never as a conjunct.
