# PRE-REGISTERED — §Ch24 P2: THE ONE INSTRUMENTED TAIL DRIVE

**Written 2026-09-25, BEFORE the drive.** Instrument: `_Ch24TailInstrument` bolted to
`Ch24TailProbeMode`, armed by `POKEBOT_CH24TAIL_INSTRUMENT=1` (**OFF by default** — the unarmed path
was verified to emit zero P2 output, so the proven probe is untouched).

DRIVER: ch24tailprobe
FIXTURE: `post_hall4_door.ss1` (`1f15cc400218`, PINNED and asserted)

---

## ⚠ WHAT KIND OF DOCUMENT THIS IS

This is an **OBSERVE-ONLY measurement**, not a graded leg. The probe's own `ACCEPTANCE` line is
**instrument health**, not a verdict, so there is nothing here for a PASS to game.
⇒ **I am NOT inventing confident predictions where I do not have them.** For several of these I
genuinely do not know the answer — that is why the drive exists. What IS pre-registered is the
**falsifier**: what each possible result would MEAN, fixed before I can see it. That is the half
that stops a result being rationalised afterwards.

⛔⛔ **THE DRIVE IS IRREVERSIBLE.** It steps onto `(5,2)`, fights the Champion, and runs the Hall of
Fame, the save, the credits and a `SoftReset` — it CLEARS THE GAME. ✅ A fixture restore was added
to this probe first (every other §Ch24 driver had one; this one did not), and it runs **after** the
verdict so it can never suppress a reading. ‼ The budget must let the run FINISH — a frame-capped
run never resumes the generator, so the restore would not fire.

---

## WHAT EACH SUB-PROBE SETTLES, AND WHAT EACH RESULT WOULD MEAN

### P2a — does `get_game_state()` EVER read `OVERWORLD` during the tail?
READING: `p2a_ever_overworld`, `p2a_state_histogram`, first/last OVERWORLD frame.
* **If NEVER** ⇒ the completion predicate `C-HOME` can be **one conjunct**, and the party-non-empty
  and not-on-HALL_OF_FAME terms are redundancy.
* **If EVER** ⇒ those terms are **LOAD-BEARING, not redundancy**, and a one-conjunct predicate would
  fire mid-tail — the exact shape that made the v1 probe stop before measuring anything.
‼ The existing evidence samples at 1/60 plus transitions, so *"never OVERWORLD"* is currently an
**interpolation**, not a measurement. This counts every frame.

### P2b — ⭐⭐ WOULD THE PRODUCTION WATCHDOG DERAIL A **WINNING** RUN?
READING: `p2b_prod_max_stall_streak`, `p2b_WOULD_PRODUCTION_DERAIL`, `p2b_prod_sig_exceptions`.
* **If the max streak ≥ 18,000** ⇒ **a winning run derails**, and the champion leg must be designed
  against a SPURIOUS DERAIL. This is the inversion the adversarial pass found; it is the single most
  design-relevant number in the drive.
* **If well below** ⇒ the watchdog is not the hazard the recon feared, and D5 collapses.
⛔ **THE PRIOR NUMBER (12,681) IS DEAD AND IS NOT A PREDICTION.** It was measured under the
HARNESS's 6-tuple; production's is a different 5-tuple. This instrument computes **production's own
signature**, including its `except → None` and its `_progress_sig` component mirrored faithfully —
hardcoding that component would have made my tuple change less often than production's and biased
the answer toward "would derail".
⚠ **A remaining asymmetry, stated before the result:** production resets the streak on an exception
(`_cur is None` falls to the else), and `_progress_sig`'s own `except → None` compares EQUAL to a
previous `None`, so a silent party-read failure KEEPS a streak alive. Both are mirrored, but this is
one trajectory and the reading is a **measurement of this run**, not a proof about all runs.

### P2c — is flag 1615 a real reading for the Wallace defeat?
READING: `p2c_wallace_1615_at_premise` / `_after_battle`, plus `1614` as a NEGATIVE control.
* **False at premise → True after** ⇒ 1615 is real, and it is a forensic bonus.
* **Anything else** ⇒ it is not a usable reading. ⛔ **Not load-bearing either way** —
  `on_battle_ended`'s `BattleOutcome` already answers WIN/LOSS, so a null result costs nothing.
✅ Already observed on the safe smoke: `1615=False`, **`1614=True`** — the control discriminates, so
the reader is not simply returning False for everything.

### P2d — `LAST_TALKED` at the premise.
* A **stale or wrong id** would mean `EventScript_DoNoIntroTrainerBattle`'s opening
  `applywaitmovement VAR_LAST_TALKED` runs against the wrong object under an un-releasable
  `lockall` — a candidate **permanent hang**, not a cosmetic defect.
✅ Smoke already read `-1` from a different map; the value **at HALL4 (5,3)** is what matters.

### P2e / P2f — PP and HP of every party member at `(5,3)`.
Telemetry only; settles nothing by itself.
⇒ Its purpose is to make a **first Wallace loss DIAGNOSABLE as PP exhaustion** rather than
mis-attributed to levels — 26 opponents, and **no PP restore anywhere past the lobby** (now measured:
the League Mart sells no Ether/Elixir/Leppa). ⛔ **PP must NOT become a blocking conjunct on the
strength of this** — a gate that cannot remedy is just a halt, and `(5,3)` is a strand.
P2f also decides whether **P3** (mint an unhealed fixture) is needed: only if every member is at or
above `TOP_UP_BELOW`, which would make fault arm **A4** vacuous.

### P2g — is the Champion's room readable at all after the fight?
READING: `p2g_champ_room_frames_post_battle`, `p2g_champ_room_controllable_frames`.
* **Zero controllable frames** ⇒ the room is a **latch-only region** and no leg may plan to take a
  reading there.

---

## ⛔ WHAT THIS DRIVE WILL NOT SETTLE

* ⭐ **THE WIN RATE.** Wallace has been beaten **ONCE**. This drive fights him once more, from the
  same pinned fixture. Two wins from one fixture is not a rate, and `on_whiteout` is the other exit.
* **RULING 11.** A driver, a pinned fixture, at speed — none of its four conjuncts.
* **Whether any of this survives being wired into `_play`.** That is D1, and it is out of scope.
* **`p2b`'s generality.** It measures what production's watchdog WOULD have done on **this**
  trajectory. A different route through the tail could differ.
