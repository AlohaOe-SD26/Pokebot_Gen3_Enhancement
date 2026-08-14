# §Ch20 Room 3 — PRE-REGISTERED predictions: the first live test of the DOUBLE-BATTLE claim

> Driver: `--driver ch20room3`, anchor `post_dive.ss1`.
> `PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room3 --frames 3000000`
> Fourth in the series. Running score: Room 1 **6/7**, Room 2 **10/10**, Room 6 **8/8** — and the
> single Room 1 miss is what produced KI-77, which is why these are written first.

## WHAT IS ACTUALLY BEING TESTED

Room 3's *route* is already settled and was **confirmed live** by `--driver ch20room6`:
`calculate_path((4,15) → (8,1))` = `OK len=18` **containing `(6,5)`**. So the 7-boulder puzzle is
**optional** and the walk must cross a trainer sight tile. What has **never been observed** is the
*shape of the fight*.

**The claim: it is ONE DOUBLE BATTLE, not two singles.** `CheckForTrainersWantingBattle`
(`src/trainer_see.c:191-218`) does not stop at the first trainer — with **≥2 usable Pokémon** it
collects both, and `battle_setup.c:1272-1275` starts a double. Shelly `(9,5)` sight 6 and Grunt5
`(5,5)` sight 4 both cover `{(6,5),(7,5),(8,5)}`; sight is a **1-tile-wide LINE** (`==` on y, no
tolerance) and `FACE_LEFT`/`FACE_RIGHT` **never rotate**, so the lines are permanently fixed.
**All decomp-derived. None of it observed.**

## THE PREDICTIONS

| # | prediction | why | if it FAILS |
|---|---|---|---|
| **S1** | *(control)* Rooms 1, 2 and 6 all re-prove; `in_room3=True`. | All are `FLAG_TEMP_*` rooms that reset on every map load, so this driver redoes every one from scratch — taking **Room 1 to n=6, Room 2 to n=3, Room 6 to n=2**. Also proves the `_cross_room6()` extraction neutral. | Everything below is void, and the extraction broke something. |
| **S2** | `usable ≥ 2` before entering the sight line (expected **6**). | The fixture heals the party; nothing before Room 3 is expected to KO four members. | ‼ **This is a precondition on the MEASUREMENT, not just on safety.** Below 2 the engine fires **two sequential singles**, so a "two battles" reading would say nothing about the decomp. It is asserted *before* the walk and reported with the result precisely so a null result stays attributable. |
| **S3** | ‼ **THE DISCRIMINATING ONE: exactly ONE trainer battle, and it reports `is_double=True`.** | Read at battle start from `battle_state.is_double_battle` — the only moment the question is answerable, since afterwards there is a defeated flag but no record of how many trainers were in the fight. | **TWO separate trainer battles ⇒ the "one double battle" reading of `trainer_see.c:214-217` is REFUTED**, and the Room 3 arbitration needs correcting. **ZERO ⇒ either the route dodged the sight line (contradicting a path measured to contain `(6,5)`) or the grunts are hidden** — check `FLAG_HIDE_SEAFLOOR_CAVERN_AQUA_GRUNTS` before believing either. |
| **S4** | The walk ends in `SEAFLOOR_CAVERN_ROOM8` at `(5,12)`. | `(8,1)` is a `Non-Animated Door` → `ROOM8` warp 1, confirmed from both the decomp warp table and our ROM. | The room graph is wrong at the one hop that has been cross-checked twice. |
| **S5** | `can_continue=True` — a real step in Room 8. | The standing rule; three chapters have shipped stranded. | Room 8's arrival pocket is tighter than the grid suggests. ‼ Note Room 8's `(5,12)` is a `South Arrow Warp` back to Room 3, so a *step* will not bounce us out, but nothing may hold Down there. |
| **S6** | ≥0 wild encounters; the run survives any that fire. | Every non-warp Room 3 tile has `has_encounters=True`. | A stall is a driver defect: the post-battle continuation must be re-planned from the LIVE position. ‼ A defeated trainer still **occupies its tile**, and `TrainerMoveToPlayer` walks Shelly to `(7,5)` — so a plan made before the battle is stale after it. |

## ‼ WHAT IS DELIBERATELY **NOT** GRADED

`saw_double` is **reported, not graded**. The run's job is to deliver the bot into Room 8; the
battle shape is a *measurement of a decomp claim*. Grading on it would turn "we learned the claim
was wrong" into "the run failed" — which is exactly how a negative result gets buried instead of
recorded. The acceptance is `in_room3 and in_room8 and can_continue`.

---

# ✅ RESULT — `ACCEPTANCE: PASS` ON THE FIRST DRIVE. The bot reaches ROOM 8.
# ‼ AND THE DISCRIMINATOR PRINTED A FALSE VERDICT. The CLAIM is CONFIRMED; MY INSTRUMENT WAS WRONG.

```
[ch20room3] BATTLE #1 kind=wild    is_double=False at=('ROUTE127', (28, 16))
[ch20room3] BATTLE #2 kind=trainer is_double=False at=('SEAFLOOR_CAVERN_ROOM1', (8, 7))
[ch20room3] BATTLE #3 kind=wild    is_double=False at=('SEAFLOOR_CAVERN_ROOM2', (4, 6))
[ch20room3] ROOMS 1+2+6 re-proven; standing in ('SEAFLOOR_CAVERN_ROOM3', (4, 15))
[ch20room3] PRECONDITION usable=6 (OK — the DOUBLE battle can form)
[ch20room3] BATTLE #4 kind=trainer is_double=True  at=('SEAFLOOR_CAVERN_ROOM3', (6, 5))   <-- ‼
[ch20room3] WALK (4, 15) -> ('SEAFLOOR_CAVERN_ROOM8', (5, 12)) in_room8=True
[ch20room3] RESULT crossed=True usable=6 battles=2 saw_double=True in_room8=True
            can_continue=True
[ch20room3] ACCEPTANCE: PASS
```

## ✅ S3 — THE DECOMP CLAIM IS **CONFIRMED LIVE**

**Exactly ONE trainer battle happened in Room 3, it reported `is_double=True`, and it fired at
exactly `(6,5)`** — the tile the Room 6 run had already measured the push-free path to contain.
That is `trainer_see.c:214-217` + `battle_setup.c:1272-1275` behaving as read: both trainers'
1-tile sight lines cover the tile, neither `FACE_LEFT`/`FACE_RIGHT` rotates, and with 6 usable
Pokémon the engine collected **both trainers into one double battle**. Shelly and Grunt5 were
fought together and the walk continued straight into Room 8.

## ⛔ BUT THE DRIVER PRINTED THIS, AND IT IS FALSE

```
[ch20room3] ‼ 2 SEPARATE trainer battles — the 'one double battle' claim is REFUTED ...
```

**The discriminator counted trainer battles RUN-WIDE**, so it swept in the **Room 1 Aqua grunt** —
which is fought on *every* run and was itself a pre-registered prediction (P6 of the Room 1 note).
Two trainer battles happened *in the run*; **one** happened *in Room 3*. The verdict line named the
wrong event and would have gone into the docs as a refutation of a claim the same run CONFIRMED.

‼ **This is the exact failure this project logs most — "the instrument did not measure what it
claimed" — committed again, hours after I wrote two prevention rules about it.** The raw data was
never in doubt: the battle log records the MAP per battle, so the scoping was *available* and simply
not applied. **Fixed:** the discriminator now filters on `b[2][0] == "SEAFLOOR_CAVERN_ROOM3"` and
reports `trainer_anywhere` and `trainer_in_ROOM3` separately, so the two can never be conflated
again.

✅ **What saved it:** `saw_double` was deliberately **reported, not graded** — so the false verdict
line could not turn a confirmed claim into a failed run, and the raw `BATTLE-LOG` line printed the
per-battle map, which is what made the error visible in ten seconds instead of propagating.
*Print the raw reading next to the judgement; the judgement is the part that is wrong.*

## THE OTHER PREDICTIONS
* **S1 ✅** — Rooms 1, 2 and 6 all re-proven from scratch. **Room 1 n=6, Room 2 n=3, Room 6 n=2**,
  and the `_cross_room6()` extraction is proven neutral.
* **S2 ✅** — `usable=6`, comfortably above the threshold the double battle depends on. So the
  confirmation is attributable: it was not "we had too few to qualify".
* **S4 ✅** — ended `SEAFLOOR_CAVERN_ROOM8 (5,12)`, exactly as the warp table and our ROM agreed.
* **S5 ✅** — real step `(5,12) → (5,11)`, `'Cave'`, not Manual.
* **S6 ✅** — **two wild encounters fired** (Route 127 and Room 2 `(4,6)`, the latter *between two
  Strength pushes*) and both were ridden out. The Room 2 note flagged this as untested; it is now
  tested, and the idempotent `strength_push` design held.

## WHAT THIS RUN DOES NOT CLAIM
* **It does not solve Room 3's puzzle** — on purpose. Five irreversible pushes in a wedge-able room
  buy only the avoidance of a fight we win. The stealth sequence is recorded in the arbitration
  note if it is ever needed.
* **It is not §Ch20.** No chapter module, nothing wired into `story_mode.py`, Dive still injected.
* **It does not reach Kyogre.** Room 8's nine-push maze and Room 9 remain.
