# GRADED — §Ch24 S2, `fight_one_room()` in PRODUCTION (SIDNEY → PHOEBE)

Graded **2026-09-24** against `2026-09-24-ch24-room-leg-PREDICTIONS.md`, committed **before** the
drive (`30a001fc`). Evidence in `tools/story-dev/evidence/`:
`2026-09-24-ch24room.stdout.txt`, the failing first drive
`2026-09-24-ch24room-DRIVE1-battleblind.stdout.txt`, and three arms
`…-ARM-noengage`, `…-ARM-healnoop`, `…-ARM-vacuity` (all `.stdout.txt`).

**THE RUN:** `CH24_ROOM_FROM=sidney --driver ch24room` from **`post_sidney_L75.ss1`**
→ **`ACCEPTANCE: PASS`**, **all 9 readings**, `missing=[]`, `whiteouts=0`, `failure=None`,
`victory_flag_set=True`, `heal_ready=True`, ending on `PHOEBES_ROOM (6,6)`.

⇒ **THE PRODUCTION LEG REPRODUCES WHAT THE BESPOKE HARNESS DRIVER DID.** That was the question;
it is answered. ⛔ It is **not** the answer to *"can the bot beat the Elite Four"* — all five
fights, the Champion included, were already won in the harness on 2026-09-17.

---

## THE GRADE

| # | prediction | verdict | the reading it rests on |
|---|---|---|---|
| P1 | premise holds and is non-vacuous | ✅ **CONFIRMED** | `start_at = SIDNEYS_ROOM(6,6)`, `start_flag = False` |
| P2 | the parked victory msgbox clears | ✅ **CONFIRMED** | `dismissed = True` |
| P3 | hall crossed, next room entered | ✅ **CONFIRMED** | `hall_at (5,12)` → `room_at (6,11)` |
| P4 | ⭐ the production leg reproduces the harness win | ✅ **CONFIRMED — ON THE SECOND DRIVE** | `victory_flag_set = True`, `whiteouts = 0`. ⛔ **The FIRST drive REFUTED it, and the refutation was correct** — see below |
| P5 | ends able to continue | ✅ **CONFIRMED** | `end_at = PHOEBES_ROOM(6,6)` — the next unit's premise exactly |
| P6 | the heal runs and never raises | ✅ **CONFIRMED** | `heal_actions=1` |
| P7 | exit door OPEN in the LIVE grid | ✅ **CONFIRMED** | `exit_door_live = {(6,1): 0, (6,2): 0}` |
| P8 | the heal left the party gauntlet-ready | ✅ **CONFIRMED** | `heal_ready = True` |

⭐ **P6 REPRODUCED THE 2026-09-17 HARNESS RUN NUMBER FOR NUMBER**, which is the strongest evidence
of port fidelity in this document — not a similar outcome, the *same* one:
`heal_plan [(0, 'Super Potion', 'Mightyena at 187/227')]` → `heal_after Mightyena 227/227`,
`heal_actions = 1`. ‼ And I did **not** re-predict "the heal will be a no-op": that prediction was
made on 2026-09-17 and was WRONG, and the pre-registration says so.

---

## ⛔⛔ THE DEFECT THE FIRST DRIVE FOUND — AND IT IS A *STRUCTURAL* ONE, NOT A TUNING MISS

Drive 1 ended `ACCEPTANCE: FAIL`, raising *"stood at (6,6) facing (6,5) … for 4,000 frames
**without starting a battle**"* — **while the same log showed the battle happening**
(`ctrl=BattleListener.fight state=BATTLE`, Mightyena's exp climbing 430,545 → 437,193).

The frame trace names the cause exactly:

| frame | event |
|---|---|
| 3,950 | `CONTROLLER -> BattleListener.fight (state=BATTLE)` — a controller is pushed ABOVE us |
| 3,950 → 13,812 | the fight runs **9,862 frames**; this generator executes **ZERO iterations** |
| 13,812 | `CONTROLLER -> Ch24RoomMode.run` — we resume, and `battle_is_active()` is False again |
| 17,094 | the 4,000-iteration engage budget is exhausted → raise |

⇒ **`battle_is_active()` IS STRUCTURALLY UNOBSERVABLE FROM INSIDE THIS LOOP.** `main.py` advances
only the TOP of the controller stack, so the only frames on which the loop can poll are precisely
the frames on which a battle is **not** running. It is not a flaky reader or a short budget — **no
budget would ever have fixed it.**

‼ **WHY THE THREE PROVEN DRIVERS DO NOT HIT THIS:** they break on `self.battles`, set by the
`on_battle_started` **callback** — a push notification that survives the suspension. Their own
comment states the premise outright (`story_harness.py:18371`): *"a driver's generator is not
resumed until the fight ENDS, so 0 is the only value a healthy run can produce."* Production
`StoryMode` HAS the hook (`story_mode.py:3318`) but keeps **no counter**, so the leg cannot borrow
it — which is exactly why a generalization needed a new mechanism rather than a copied line.

✅ **THE FIX — DETECT THE SUSPENSION ITSELF**, which requires nothing registered anywhere: a normal
`yield` advances `context.emulator.get_frame_count()` by ~1; a `yield` a pushed controller ran
through advances it by thousands. Threshold 60 frames. Measured on the passing drive:
**`engage_suspension_frames = 9864`** — within 2 frames of the interval drive 1 was blind to.
(The victory FLAG is checked as a second signal, and `battle_is_active()` is kept as a third for
the case where we do happen to poll mid-battle.)

⇒ ⭐ **THIS IS WHY THE PRE-REGISTRATION WAS WORTH WRITING.** P4's falsifier said a loss here would
mean *"the generalization dropped something — NOT that the party is weak."* That is exactly what it
meant, and the file said so **before** the result existed. Had the fixture trap not been caught
first, this same FAIL would have arrived with a plausible wrong explanation attached (*"17 % HP and
five faints — of course it lost"*), and the structural defect would have survived.

---

## ✅ THREE FAULT ARMS, EACH FAILING FOR ITS OWN REASON

| arm | result | what it proves |
|---|---|---|
| `POKEBOT_CH24ROOM_FAULT=noengage` | `missing=['R1-CONTINUE','R1-ENGAGED','R1-WON','T-CONTINUE']`, `heal_ready=True` | walks the WHOLE unit then presses nothing ⇒ the fight readings are earned by **fighting**, not by arriving |
| ⭐⭐ `POKEBOT_CH24ROOM_FAULT=healnoop` | **`missing=[]`, `failure=None`, `whiteouts=0`, the fight WON — and `ACCEPTANCE: FAIL` on `heal_ready=False`** | the grade conjunct is the **SOLE** cause of failure. Without it this run reads PASS with a heal that did nothing |
| `CH24_ROOM_FROM=phoebe` (premise) | `readings=[]` — refuses before moving | the premise guard is live, not decoration |

‼ **`healnoop` is the one that matters**, and it is non-vacuous only because the fixture was checked:
Mightyena 187/227 = **82.4 %** against `TOP_UP_BELOW = 0.90`. It runs the REAL
`heal_party_from_bag` with `max_actions=0` — no monkeypatching, no synthetic party, the same code
path the treatment runs, bounded to do nothing.
⚠ Note `noengage` produces the **same shape** as drive 1's accidental failure. Drive 1 was, in
effect, running the `noengage` arm by mistake — it pressed the buttons and could not see the result.

---

## ⛔ WHAT THIS DRIVE DOES **NOT** SETTLE

* **The other three room pairs and the Champion.** `CH24_ROOM_FROM` has `phoebe` and `glacia` pairs
  wired, and **neither has been driven through the production leg.** Room 5 is structurally
  different (forced battle on entry, no `WalkInCloseDoor` seal) and is not this unit.
* **The sequencer.** Nothing yet CALLS `fight_one_room` five times; there is no room loop.
* **RULING 11.** This is a harness driver running a production function. DONE means the Hall of Fame
  from the **real story mode, no fixture, at ×1**. `story_mode.py:5280` is still the END OF BUILT
  CONTENT banner, and `fight_one_room` is **not wired into `_play`**.
* **The commitment step**, and **re-entry after a loss** (that design was reviewed and REJECTED).
* **A VARYING team.** One party, the curated one. The leg is species-agnostic by construction —
  nothing in it names a Pokémon, move or type — but that is an argument, not a measurement.
* ⚠ **`R1-CONTINUE` on a RELOADED fixture.** `OnLoad` re-opens the exit door whenever the room's
  DEFEATED flag is already set, so this reading is meaningful DURING a run (as here) and would be
  **vacuous** if graded from a reloaded post-victory save.
