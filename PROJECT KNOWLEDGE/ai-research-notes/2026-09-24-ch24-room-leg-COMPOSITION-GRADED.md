# GRADED — §Ch24 S2b: `fight_one_room()` **COMPOSES** ACROSS ALL THREE ROOM PAIRS

Graded **2026-09-24** against `2026-09-24-ch24-room-leg-COMPOSITION-PREDICTIONS.md`, committed
**before** the drives (`015ae88b`). Evidence:
`tools/story-dev/evidence/2026-09-24-ch24room-PHOEBE.stdout.txt` and `…-GLACIA.stdout.txt`.

**BOTH DRIVES: `ACCEPTANCE: PASS`**, all 9 readings, `missing=[]`, `whiteouts=0`, `failure=None`,
`heal_ready=True`.

| pair | from | to | end tile | exit door (live) |
|---|---|---|---|---|
| `sidney` (272c226f) | `post_sidney_L75` | PHOEBE ✅ | `PHOEBES_ROOM (6,6)` | `{(6,1):0,(6,2):0}` |
| `phoebe` | `post_phoebe_L75` | GLACIA ✅ | `GLACIAS_ROOM (6,6)` | `{(6,1):0,(6,2):0}` |
| `glacia` | `post_glacia_L75` | DRAKE ✅ | `DRAKES_ROOM (6,6)` | `{(6,1):0,(6,2):0}` |

⇒ **THE UNIT IS A UNIT.** `ROOM_EXIT_DOOR = (6,2)` and `HALL_FAR_DOOR = (5,2)` are genuinely
uniform, `objects_seen = [(6,5)]` in every room (one object, as the decomp says), and each leg ends
on exactly the premise the next one requires. **The sequencer can now be a loop over `PAIRS`
rather than four bespoke branches.**

---

## THE GRADE

| # | prediction | verdict | evidence |
|---|---|---|---|
| P1 | composes for PHOEBE → GLACIA | ✅ **CONFIRMED** | `DEFEATED_ELITE_4_GLACIA`, end `GLACIAS_ROOM (6,6)` |
| P2 | composes for GLACIA → DRAKE | ✅ **CONFIRMED** | `DEFEATED_ELITE_4_DRAKE`, end `DRAKES_ROOM (6,6)` |
| P3 | ⭐ the heal REVIVES and flips `heal_ready` | ✅ **CONFIRMED** | 3-action plan, below |
| P4 | ⭐ the heal is a NO-OP and still reports ready | ✅ **CONFIRMED** | `heal_plan=[]`, `heal_actions=0`, `heal_ready=True` |
| P5 | no whiteouts | ✅ **CONFIRMED** | `whiteouts=0` in both |

### ⭐⭐ P3 — THE HARD CASE, AND THE HEAL REASONED ITS WAY THROUGH IT

`post_glacia_L75.ss1` starts at **776/1214 (64 %) with Mightyena FAINTED** — the state the Drake
commit called *"a party the previous room broke"*. The plan the production heal produced:

```
(0, 'Revive',       'Mightyena L76 is FAINTED and is the highest-level mon still down')
(0, 'Hyper Potion', 'Mightyena at 0/230 (just revived, returns at half HP)')
(4, 'Full Restore', 'Wailord at 188/396')
```

`heal_actions = 3`, `heal_ready = True`. ‼ Note the **second** line: it knows a Revive returns a
mōn at HALF HP and tops it up in the same plan rather than declaring victory after the Revive. ⇒
the `LEAGUE_BASKET` is **not** under-provisioned for this case, which is a real (if narrow) answer
to a question S3's re-entry predicate has to price.

### ⭐ P4 — THE PREDICTION WRITTEN TO CATCH MY OWN NEW CODE, AND IT HELD

The `heal_ready` grade conjunct added in `272c226f` fails a run whose heal accomplished nothing.
The obvious way for that to be WRONG is a party that needs nothing: `heal_plan = []` would also be
"a heal that accomplished nothing". From `post_phoebe_L75.ss1` (99 %, 0 fainted) it returned
`heal_actions = 0` **and `heal_ready = True`**, because `heal_party_from_bag` sets
`heal_ready = party_is_gauntlet_ready(before)` on its early-out path.
⇒ **the conjunct distinguishes "nothing to do" from "could not do it", and is not too strict.**
‼ This was pre-registered precisely because it could have embarrassed the previous commit.

---

## ⭐ AN UNPREDICTED OBSERVATION — THE THREE ENGAGE SIGNALS ARE NOT REDUNDANT IN PRACTICE

The two drives broke out of the engage loop by **different** mechanisms:

| pair | battle span | which signal fired |
|---|---|---|
| `phoebe` | f3580 → f30350 = **26,770 frames** | the SUSPENSION detector — `engage_suspension_frames = 26772` (within 2 frames) |
| `glacia` | f5020 → f23778 = **18,758 frames** | **NOT** the suspension detector — the key is absent from a log line that is **not** truncated (it ends with its closing brace, checked) ⇒ the break came from `battle_is_active() or get_event_flag(victory_flag)`. ⚠ **The log does not distinguish WHICH of those two**, because they share one condition. Not asserted.

⇒ Keeping all three signals was not belt-and-braces padding: **each of the two runs would have
needed a different one.** A 26,770-frame battle is utterly invisible to a poll, and the suspension
detector alone would not have fired in the run where the poll happened to catch the transition.
‼ **A cheap improvement for a future session:** split that `or` so the reading records which signal
fired. Right now the instrument cannot answer a question I just had to leave open.

---

## ⛔ WHAT THESE DRIVES DO **NOT** SETTLE

* **The CHAMPION room** — not this unit (forced battle on entry, no `WalkInCloseDoor` seal), and
  deliberately NOT in `PAIRS`.
* **The sequencer and the `_play` dispatch** — still do not exist. `story_mode.py:5280` is still the
  END OF BUILT CONTENT banner.
* **RULING 11** — three harness drives from three pinned fixtures is not "the real story mode, no
  fixture, at ×1".
* ⛔ **BASKET CONSUMPTION ACROSS A WHOLE RUN.** Each leg started from its own pinned fixture with its
  own bag, so this is **three independent legs, not one four-fight gauntlet**. The Revive that
  worked here was spent from a fixture's bag, not from a bag already drained by two prior rooms.
  ‼ Do not read "the heal coped" as "the basket survives the gauntlet" — that needs a continuous run.
