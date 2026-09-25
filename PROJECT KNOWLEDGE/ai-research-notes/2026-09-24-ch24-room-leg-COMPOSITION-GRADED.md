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
on exactly the premise the next one requires.

⛔⛔ **RETRACTION, SAME DAY, BY AN ADVERSARIAL REVIEW — AND THE TREE HAD ALREADY RULED ON IT.** The
sentence that followed here claimed *"the sequencer can now be a loop over `PAIRS`."* **That
overstates the result and is withdrawn.** `03-PUNCH-LIST.md`'s OPEN item `#24-leg2spec` says
verbatim: ***"THE 'REPEATING UNIT × 5' MODEL IS REFUTED — DO NOT BUILD IT."***
⇒ what this drive establishes is narrower and still worth having: **the ROOM-TO-ROOM MIDDLE of the
chapter is a loop over `PAIRS`.** Both ends are missing, and one was already rejected:
* ⛔ **`enter_the_league` and `ch24_chapter_done` have ZERO occurrences in the whole tree** (grep).
  There is **no bridge** from `prepare_and_open_the_league`'s stopping tile `(9,3)` through the
  SIDNEY fight into leg 1's premise — and leg 1's premise requires *already having beaten Sidney*.
  The obvious form of that bridge was designed, adversarially reviewed and **sent back**.
* ⛔ The CHAMPION room is not "a short bespoke step": it `lockall`s and walks the player into the
  fight (**no A-press trigger**), has **no defeated-flag guard** (so any re-entry re-fights Wallace
  at full strength), and the chapter ends in a **console reboot** (`#24-gameclearflag`).
* ⛔ **PP is absent from the readiness predicate and cannot be restored past the lobby**, and HALL4
  is 31 tiles — the last heal point in the game.
‼ I made this mistake in the same shape TWICE today: asserting something the punch list had already
settled. ⇒ **before writing "X can now be done", grep the punch list for X.**

*(The withdrawn sentence, kept so the retraction above is legible: ~~"The sequencer can now be a
loop over `PAIRS` rather than four bespoke branches."~~)*

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

---

## ✅ UPDATE, SAME DAY — THE OPEN QUESTION ABOVE IS NOW ANSWERED, AND THE ANSWER IS BETTER THAN THE QUESTION

The `or` was split so each signal records itself in `engage_signal`, and all three pairs re-driven
(evidence `…-{sidney,phoebe,glacia}-signal.stdout.txt`; all three still `ACCEPTANCE: PASS`):

| pair | `engage_signal` | frames |
|---|---|---|
| `sidney` → PHOEBE | `suspension` | 9,864 |
| `phoebe` → GLACIA | `suspension` | 26,772 |
| ⭐ `glacia` → DRAKE | **`victory_flag`** | — |

⭐⭐ **THE ENGAGE MECHANISM IS NOT UNIFORM ACROSS ROOMS, EVEN THOUGH THE GEOMETRY IS.** In two rooms
our A-press starts the fight. In DRAKE's room it does not: `engage_signal = victory_flag` means the
loop's FIRST reading already found the defeat flag set, so **the battle began and ENDED before the
press loop ran at all.**

⛔ **WHAT IS MEASURED vs WHAT IS INFERRED — stated separately on purpose.**
* **MEASURED:** the signal is neither `suspension-on-first-press` nor `suspension`, which are the
  only two ways this instrument can report a battle that spanned one of its own `yield`s. ⇒ the
  fight happened **before the engage loop's first iteration**. That is a deduction from the
  instrument's own exhaustive cases, not a guess.
* **INFERRED, NOT ASSERTED:** *why*. The likely mechanism is the trainer's SIGHT LINE during the
  5-tile approach from the room's entry tile `(6,11)` to `(6,6)`, with Drake at `(6,5)` facing down
  the corridor — the battle would then fire inside `_navigate_riding_out`, which is wrapped in
  `_yield_bounded_by_frames`, so its frames are absorbed there and never reach the engage loop.
  ⛔ **NOT VERIFIED.** Confirming it needs a probe that records the frame at each `_take`.

### ⇒ THE THREE SIGNALS ARE ALL LOAD-BEARING — MEASURED, NOT ARGUED

| if the leg had shipped ONLY… | what happens |
|---|---|
| `battle_is_active()` | **all three rooms fail** — drive 1 proved it directly |
| the suspension detector | **DRAKE's room fails** — the battle is absorbed by the navigate's budget, so no jump is ever seen in the engage loop |
| the victory flag | **SIDNEY's and PHOEBE's rooms cannot distinguish "won" from "never fought"** — the premise guard would have to carry the whole grade |

‼ This is the rare case where redundancy was not defensive padding: **each room genuinely needed a
different one of the three.** Had I kept the single `or`, the leg would still work — but the
write-up would have had to guess, and a guess in a write-up is how a wrong fact is born.

⇒ **CONSEQUENCE FOR THE SEQUENCER:** a room leg must NEVER assume its own press caused the battle.
`fight_one_room` already does not, and that is now measured rather than hoped.

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
