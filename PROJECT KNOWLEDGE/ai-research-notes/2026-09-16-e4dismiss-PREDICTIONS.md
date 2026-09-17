# `--driver e4dismiss` — PREDICTIONS, FILED BEFORE THE RUN (2026-09-16)

> ⛔ Written and committed **before** the driver was executed, per `story-drive` §1. Anything below
> that the run contradicts is a **RESULT**, never a driver failure.

## THE QUESTION (one sentence)

**Does pressing `B` clear the §Ch24 post-victory msgbox and return control to the bot?**

This is the single unmeasured fact the whole §Ch24 leg-1 plan rests on. Two independent recon angles
flagged it and both DECLINED to assert it from the decomp alone
(`2026-09-16-ch24-leg1-RECON-6-ANGLES.md` §0): **no evidence file in this tree shows this msgbox ever
being dismissed by the bot.** The decomp says `Std_MsgboxDefault` ends in `waitbuttonpress`, which
accepts `JOY_NEW(A_BUTTON | B_BUTTON)` — that is a READ, and house rules say a decomp read is a note.

## FIXTURE

`saves/post_sidney_door_open.ss1`, md5 **`6231369647f8`**, PINNED 2026-09-16
(`verify_fixtures.py --assert post_sidney_door_open.ss1=62313696` → OK).
It IS the state under test: `EVER_GRANDE_CITY_SIDNEYS_ROOM (6,6)`, Sidney beaten, exit door already
open in the live grid, victory msgbox parked at `WaitForButton`, and `probe_anchor_inventory` prints
*"‼ NOT a clean controllable overworld"*. ⇒ the probe starts INSIDE the stall; the measurement costs
seconds rather than a 29,000-frame drive.
⚠ HP 139/807, **5 fainted** — fine for this question, useless as the start of anything longer.

## THE TWO ARMS (this is an A/B, not a demonstration)

| arm | env | what it does |
|---|---|---|
| **TREATMENT** | *(none)* | presses `B` on a duty cycle while the printer is parked / a script runs |
| **CONTROL** | `POKEBOT_E4DISMISS_FAULT_NOPRESS=1` | identical loop, identical budget, **presses nothing** |

⛔ **THE CONTROL IS WHAT MAKES THE RESULT MEAN ANYTHING.** Without it, "the bot became controllable"
is consistent with the box having self-cleared on a timer. CLAUDE.md rule 8: *a claim of the form
"without X the bug survives" is a CLAIM, and the only currency this project accepts for it is an arm
with X removed.*

## PREDICTIONS

| # | reading | TREATMENT | CONTROL | why |
|---|---|---|---|---|
| P1 | `controllable_before` | `False` | `False` | premise: the fixture is the stall state. **If this is `True` the probe is vacuous and must FAIL loudly.** |
| P2 | `printer_before` | active, `WaitForButton` | same | ditto — the box is up before we touch anything |
| P3 | `controllable_after` | **`True`** | **`False`** | the whole experiment |
| P4 | `frames_to_control` | < 400 | n/a (never) | 3 field presses at a 1-in-6 duty cycle ≈ tens of frames, plus msgbox draw time |
| P5 | `presses_issued` | 1–12 | **0** | decomp counts 3 field presses for Sidney (1 `\p` + 1 `\l` + 1 `waitbuttonpress`); the fixture is captured mid-sequence so ≤3 should remain |
| P6 | `script_active_after` | `False` | `True` | `release` runs only after the msgbox is done |
| P7 | `door_live_after` | `{(6,1):0,(6,2):0}` | same | the door is already open in this fixture; pressing B must not close it |
| P8 | `tile_after` | `(6,6)` | `(6,6)` | B cannot move the player; if the tile changes, something else is driving |

## FALSIFIERS — what result would mean the PLAN is wrong, not the driver

* **F1 — CONTROL also reaches `controllable_after = True`.** Then the box self-clears and the
  diagnosis is wrong: the 1,802-frame stall is not "nobody pressed a button". ⇒ the whole
  §2 "press-NOTHING wait where a press-SOMETHING helper was required" framing collapses and must be
  re-opened. **This is the single most important arm.**
* **F2 — TREATMENT does NOT reach control.** Then **B does not dismiss this box.** Possibilities, in
  the order I would check them: the box is a YES/NO or multichoice (B answers *NO* and the fix is
  wrong in a way the log would not show — recon §0's second-order unknown); or the script parks its
  context ACTIVE after `release` (the KI-15 "phantom script" family); or the duty cycle never lands a
  `JOY_NEW` edge. ⛔ **Do NOT respond by switching to `A`** — the bot is facing Sidney at (6,5) and his
  script is re-triggerable after defeat, so A risks a re-open livelock. Diagnose first.
* **F3 — `presses_issued` is large (say > 40) in a passing TREATMENT.** Then the duty-cycle/edge model
  is wrong even though the outcome was right, and the `press_button` auto-alternation reading below
  needs re-checking before anything depends on it.
* **F4 — `tile_after != (6,6)`.** Something other than this probe is moving the player; every other
  reading in the run is then suspect.

## A DISPUTE THIS RUN ALSO SETTLES (incidentally)

`story-drive` §5 says *"Pressing a button every frame is HOLDING it … press on a duty cycle (one frame
in four)."* The recon says `press_button` **auto-alternates**, and the source agrees —
`modules/libmgba.py:471-476`, docstring *"if pressed on previous frame it will be released"*, body
`self._pressed_inputs |= (self._prev_pressed_inputs & input_map[button]) ^ input_map[button]`
(`(prev & mask) ^ mask` = 0 when the bit was set last frame) ⇒ an every-frame call is a 50% duty
cycle, not a hold. **Only `hold_button` holds.**
⛔ **I am NOT betting this drive on that.** The probe uses an explicit duty cycle, which is correct
under BOTH readings. `presses_issued` (P5/F3) is what tests the model, at no risk to the result.

## WHAT THIS RUN DOES *NOT* ANSWER

1. Whether stepping on `(6,2)` actually warps to HALL1. Still owed a drive.
2. Whether Phoebe/Glacia/Drake behave identically — inferred from byte-identical ROM layouts and a
   shared helper, **not measured**.
3. Whether our KI-93 in-battle dismiss fires for a trainer lose-text (Glacia is the first that can
   exercise it — Sidney's text contains no `\p`).
4. Anything about leg 1's door BFS. This probe deliberately does **one** thing.

---

# RESULTS — GRADED AFTER THE RUN (2026-09-16)

**VERDICT: `B` CLEARS THE BOX AND RETURNS CONTROL. The control arm proves the box does not self-clear.**
Both arms `ACCEPTANCE: PASS` (they are graded by OPPOSITE expectations on the same reading, so a
grade both could satisfy would prove nothing).

| reading | TREATMENT | CONTROL (`FAULT_NOPRESS=1`) | predicted? |
|---|---|---|---|
| `controllable_before` | `False` | `False` | ✅ P1 |
| `printer_before` | `(True,'WaitForButton')` | same | ✅ P2 |
| `premise_ok` | `True` | `True` | — |
| **`controllable_after`** | **`True`** | **`False`** | ✅ **P3 — the experiment** |
| `frames_to_control` | **297** | `None` | ✅ P4 (< 400) |
| `presses_issued` | 50 | 0 | ❌ **P5 — see F3 below** |
| `prompts_cleared` | 2 | 0 | *(reading added after F3)* |
| `script_active_after` | `False` | **`True`** | ✅ P6 |
| `door_live_after` | `{(6,1):0,(6,2):0}` | same | ✅ P7 |
| `tile_after` | `(6,6)` | `(6,6)` | ✅ P8 |
| `frames_spent` | 317 | **2600 (full budget)** | — |

⭐⭐ **THE CONTROL IS THE RESULT.** It burned its **entire 2,600-frame budget — 1.4× the 1,802 frames
the real stall lasted — and never regained control**, ending with the printer still parked at
`WaitForButton` and the script still active. **Falsifier F1 did NOT fire.** ⇒ the §Ch24 post-victory
stall is caused by nobody pressing a button, and `B` is sufficient to clear it.

## ❌ F3 FIRED — AND IT WAS MY INSTRUMENT, NOT THE BOT

P5 predicted 1–12 presses; the run issued **50**. F3 said that would mean the duty-cycle/edge model
was wrong. **It did not — the PREDICTION was wrong, in a way this project has a rule for.**
`presses_issued` counts duty-cycle ticks on which the press GATE was true; 297 frames ÷ a 1-in-6
cycle ≈ 49.5, so the gate was true on essentially every tick. Most of those land during
`PrintingCharacter`, where there is nothing to dismiss. ⇒ **I instrumented the INPUT to the action,
not the action** — CLAUDE.md rule 7, in my own probe, while writing about rule 7.

Fixed rather than excused: `prompts_cleared` now counts `WaitForButton` → anything-else transitions,
i.e. prompts the game actually consumed. **Measured: 2.** The decomp predicts **3** field presses for
Sidney (one `\p`, one `\l`, one trailing `waitbuttonpress`), and this fixture is captured
*mid-sequence* (`bt='NICK got $4900 for winning!'`), which is exactly why P5 said "≤3 should remain".
⇒ **2 is CONSISTENT with the decomp's 3, and is a partial independent corroboration of it — not a
proof of it.** A run from before the money message would be the arm that tests the full count.

## ⚠ HOW MANY TRAJECTORIES THIS ACTUALLY IS — stated honestly (rule 8)

The second pinned fixture `post_sidney_door_open_b.ss1` (different bytes, captured ~1,800 frames
earlier in the same stall) returns **identical** readings: `controllable_after=True`,
`frames_to_control=297`, `prompts_cleared=2`. ⛔ **Do not read that as a replication.** Two captures
of the *same* parked moment, replayed deterministically, will agree by construction. It is a
determinism check plus a byte-level sanity check that the result is not an artifact of one save
file. **The phenomenon has been measured in ONE room, against ONE trainer.**

## WHAT IS STILL NOT ESTABLISHED

1. That stepping on `(6,2)` warps to HALL1. Still owed a drive.
2. That Phoebe/Glacia/Drake behave identically — inferred from byte-identical ROM layouts and a
   shared helper, **not measured**. Glacia is also the first room whose in-battle lose-text contains
   `\p`, so it is the first that can exercise our KI-93 in-battle dismiss at all.
3. That the *existing* helpers (`_ride_out_scripted_scene("B")` / `_wait_until_cutscene_over` /
   `normalize_to_overworld`) clear it. This probe pressed `B` on its own gate — it proves the GAME
   accepts B here, which is the load-bearing half, but the one-line insertion still has to be driven.
