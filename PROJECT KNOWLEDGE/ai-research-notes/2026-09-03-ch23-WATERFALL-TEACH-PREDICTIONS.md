# §Ch23 LEG 1 — TEACHING WATERFALL: PREDICTIONS **AND RESULTS** ✅ DRIVEN, `ACCEPTANCE: PASS`

> ⭐ **The predictions below were committed BEFORE the run; the RESULTS are appended at the
> bottom, unedited above that line.** All seven held, including the one rated LOW-MEDIUM.
> ⚠ But read the *"what this does NOT prove"* section — `#26-surfteachchain` **D3 did not
> fire, which is not the same as D3 being fixed**, and it stays open.

> ⛔ **COMMITTED BEFORE `--driver ch23teach` IS RUN EVEN ONCE.** A prediction filed afterwards is a
> rationalisation. Grade the drive against this file and record every miss.
> Fixture: `post_badge8.ss1` (md5 `723d94cc899f3ad2c75fbf49f9192984`) — §Ch22's own output.

## WHY THIS RUN EXISTS

An audit of the teach path concluded the forget-a-move flow is sound and would pick **Rollout**.
✅ I re-derived that arithmetic myself from `modules/data/moves.json` and agree. But the audit ended
on an honest gap, and it is the whole reason for this drive:

> ⛔ **NOT VERIFIED: that the predicted `replace_slot=3` actually EXECUTES on the emulator.** Both
> driven precedents replaced **slot 1** (`teachfull` → Taunt, `divelearner` → Defense Curl).
> **Waterfall needs slot 3 — the deepest forget-menu scroll this bot has ever attempted**, and
> `#26-surfteachchain` **D3** is armed exactly there: `_select_forget_slot` does a *blind relative
> scroll* (`for _ in range(replace_slot): press Down`), and D3's own recon says the hazard is
> **flow desync on re-entry**, needing a live probe before any code change.

⇒ **The arithmetic is certain. The menu drive is not. This run converts "should work" into
"does work" — or finds D3.**

## ⭐ THE PREDICTION THAT MATTERS MOST IS A *SAFETY* ONE

**P1 — DIVE AND SURF MUST SURVIVE.** Wailmer is the party's **sole Dive carrier**, and Dive is how
the bot leaves the Sootopolis crater at all. **Losing it strands the run in a map with zero land
connections and `allow_escaping: false`.** Surf is shared with Zigzagoon, so its loss is survivable
but still severe.
✅ The code should make this impossible by construction — `_is_hm_slot` excludes them, and Gen 3
refuses to forget an HM anyway, so there are *two* independent guards. **This run tests that both
hold in practice.** ⛔ If Dive is missing afterwards, that is a catastrophic finding and the
fixture, not the party, is what must be re-derived.

## THE REST

| # | prediction | confidence | what a miss means |
|---|---|---|---|
| P2 | the code chooses **`replace_slot = 3`** and the move that disappears is **Rollout** | HIGH — re-derived from `moves.json` by me: slots 0/1 are HM08/HM03 and excluded, no eligible slot has 0 power, so `min(base_power)` picks Rollout (30) over Water Gun (40) | the picker's rank is not what the code actually runs |
| P3 | **Wailmer knows Waterfall afterwards, matched BY PID** (`FA51ECF3`) | HIGH | the teach did not complete |
| P4 | the party is still **SIX**, same PIDs | HIGH | something deposited a member — the §Ch22 heal hazard, in a new place |
| P5 | ⚠ **the deep scroll completes without D3 firing** | ⚠ **LOW-MEDIUM — this is the risky line** | D3 is real and §Ch23's first leg needs a fix before it can ship. **That is a RESULT, not a defect in this run.** |
| P6 | bounded, `whiteouts == 0`, no hang | HIGH | every loop on this path is a `for`, unlike KI-47's `while` |
| P7 | frame cost **under 5,000** | MEDIUM | precedent: `teachfull` learned in **479** frames, but from a clean overworld with no Poké Center trip |

## WHAT IS DELIBERATELY NOT PREDICTED

* Whether the run needs a heal first. The fixture arrives at **61% HP with one member FAINTED**
  (`probe_anchor_inventory.py`), and a teach does not need a healthy party — so the drive does the
  teach **without** healing, on purpose, to keep the variable count at one.
* The exact dialogue path. Reported, never graded.

## THE ACCEPTANCE LINE

`ACCEPTANCE: PASS` requires **all** of: the premise held (Wailmer did **not** already know Waterfall
at frame 0 — otherwise the run is vacuous) **and** Waterfall present by PID **and**
⭐ **Dive present** **and** Surf present **and** Rollout gone **and** party size 6 **and**
`whiteouts == 0`.
⛔ **"The teach reported success" is NOT the grade** — the grade is the party, read from the world
afterwards. This project has been burned by a leg that reported PASS while the state it claimed was
not the state it left behind.


---

# RESULTS — GRADED AGAINST THE ABOVE (run 2026-09-03, `evidence/2026-09-03-ch23teach-WATERFALL-PASS.txt`)

**`ACCEPTANCE: PASS`, `frames=1896`, `whiteouts=0`.** Every prediction held, including the one rated
LOW-MEDIUM.

```
LEARNER production picked party slot 3 -> Wailmer (pid=4199673075)
LEARNER MOVES ['Dive','Surf','Water Gun','Rollout'] -> ['Dive','Surf','Water Gun','Waterfall']
⭐ GAINED ['Waterfall']   LOST ['Rollout']
⭐⭐ SAFETY keeps_dive=True keeps_surf=True
PARTY intact=True size 6 -> 6
```

| # | predicted | measured | verdict |
|---|---|---|---|
| **P1** | ⭐ **Dive and Surf survive** | `keeps_dive=True keeps_surf=True` | ✅ **HELD — the safety property is real.** Both guards did their job |
| P2 | `replace_slot = 3`, Rollout is lost | production picked slot 3; **`LOST ['Rollout']`** | ✅ HELD — and graded on the WORLD (which move vanished), not on the log |
| P3 | Waterfall present, by PID | present on `pid=4199673075` | ✅ HELD |
| P4 | party still SIX, same PIDs | `intact=True`, 6 → 6 | ✅ HELD |
| **P5** | ⚠ the deep scroll completes without D3 firing — **rated LOW-MEDIUM, the risky line** | completed | ✅ **HELD** — see the caveat below, which matters |
| P6 | bounded, no hang, no whiteout | `whiteouts=0`, 1,896 frames | ✅ HELD |
| P7 | under 5,000 frames | **1,896** | ✅ HELD |

## ⚠ WHAT THIS DOES **NOT** PROVE — and P5 is the one to be careful with

⛔ **D3 IS NOT REFUTED. IT SIMPLY DID NOT FIRE.** `#26-surfteachchain` D3's recorded hazard is a
**flow desync on RE-ENTRY** — `_select_forget_slot` being re-entered from the ride loop, with an
extra "replace move?" YES/NO inserted ahead of the selector. **This run never re-entered it**: the
teach went through cleanly on the first pass. ⇒ what is now measured is that **the deepest scroll
this bot has ever driven (slot 3) works on the CLEAN path**. The re-entry path remains untested, and
D3 stays open.
‼ *Saying "D3 is fine" here would be the exact shape this project keeps logging: a happy path cannot
exercise a branch it never enters.*

⚠ **And this is ONE TRAJECTORY.** The harness is deterministic for a fixed (save, driver, code)
triple — measured earlier today on the Juan fight — so a re-run is a replay, not a sample. A menu
drive has no obvious RNG dependence, so a sample is less meaningful here than for a battle; but the
honest statement is *"it works on this path"*, not *"it works reliably"*.

## WHAT IT DOES PROVE, AND IT IS THE POINT

The audit that motivated this run ended on: *"NOT VERIFIED BY ME: that the predicted Rollout pick
actually executes on the emulator … that single A/B is the cheapest thing that would convert this
audit's main finding from 'should work' to 'does work'."*
⇒ **It does work.** §Ch23's first leg is de-risked, at a cost of 1,896 frames, before a single line
of chapter code was written.
