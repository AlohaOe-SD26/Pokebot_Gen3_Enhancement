# PRE-REGISTERED PREDICTIONS — §Ch24 S2, `fight_one_room()` in PRODUCTION (SIDNEY → PHOEBE)

**Written 2026-09-24, BEFORE the drive**, per `.claude/skills/story-drive` §1 and gate #72.
Committed first so a contradicting reading is a **RESULT**, not a driver failure.

DRIVER: ch24room

FIXTURE: **`post_sidney_L75.ss1`** — `EVER_GRANDE_CITY_SIDNEYS_ROOM (6,6)`, `ELITE_4_STATE = 1`,
Sidney beaten, Phoebe/Glacia/Drake unset, the victory msgbox still parked.
⇒ the drive **never crosses the commitment point**: the fixture is already past it.

### ⛔⛔ AND THE FIXTURE WAS CHANGED BEFORE THE DRIVE — THIS IS THE REJECTED ALTERNATIVE

`Ch24RoomMode` defaulted to **`post_sidney_door_open.ss1`**, and driving from it would have produced
a **FALSE REFUTATION of P4**. Measured offline with `probe_anchor_inventory.py`, both fixtures
stand on the same tile of the same map, and they are not remotely the same run:

| fixture | party | HP |
|---|---|---|
| `post_sidney_door_open.ss1` | Sceptile L53, Zigzagoon L19, Swellow L48, Wailord L47, Mightyena L48, Castform L36 | **139/807 (17 %), 5 FAINTED** |
| ✅ `post_sidney_L75.ss1` | Mightyena L75, Zigzagoon L19, Sceptile L75, Swellow L75, Wailord L75, Castform L36 | **1171/1211 (97 %), 0 fainted** |

The first is the **pre-climb party**, and its own manifest row says so in as many words: *"usable
for the DISMISS/DOOR question only; heal before using it as the start of anything longer."* A Phoebe
fight from five faints would very likely be lost — and the loss would have been read as *"the
generalization dropped something"*, which is the exact wrong conclusion.

⭐ **`post_sidney_L75.ss1` is ALSO the fixture the PROVEN `Ch24PhoebeMode` ran from.** That is the
point: holding the party, the position and the save byte-identical to the 2026-09-17 run leaves
**production-code-vs-harness-code as the only variable**. An experiment that changes two things
answers neither.

‼ And both fixtures report *"NOT a clean controllable overworld"* — the msgbox is parked in **both**
— so switching fixtures does **not** make P2 vacuous. That was checked, not assumed.

---

## ⛔⛔ FIRST, A CORRECTION TO MY OWN FRAMING — WRITTEN BEFORE THE DRIVE, NOT AFTER

**An earlier draft of this file claimed the headline question was *"can this party beat an Elite
Four member — it has never been driven end to end."* THAT IS FALSE, and it was false when I wrote
it.** The true state, verified by an independent inventory pass over commits, evidence files and
punch-list rows:

| room | driver | flag evidence | punch-list |
|---|---|---|---|
| SIDNEY | `Ch24ProbeMode` `:15823` | `battles=1`, `ELITE_4_STATE 0→1`, 15 HP lost, 0 faints | `#24-sidneyL75` **[x]** |
| PHOEBE | `Ch24PhoebeMode` `:17578` | `DEFEATED_ELITE_4_PHOEBE=True` | `#24-phoebeL75` **[x]** |
| GLACIA | `Ch24GlaciaMode` `:18032` | `glacia_flag=True` | `#24-glaciaL75` **[x]** |
| DRAKE | `Ch24DrakeMode` `:18482` | `DEFEATED_ELITE_4_DRAKE` | `#24-drakeL75` **[x]** |
| ⭐ **CHAMPION** | `Ch24TailProbeMode` `:19301` | **`IS_CHAMPION=True`, `SYS_GAME_CLEAR=True` in BOTH RAM AND FLASH** | `#24-tailprobe` **[x]** |

⇒ **ALL FIVE FIGHTS, THE CHAMPION INCLUDED, ARE ALREADY WON IN THE HARNESS.** The game has been
cleared. The single open §Ch24 item is `#24-e4postbattlestall` **[~]**, whose own body says:
*"WHAT REMAINS: THE WIRING, NOT A MEASUREMENT."*

⚠ **ONE PRECISION POINT, because it would be easy to over-read the table above.** The room drivers'
`ACCEPTANCE: PASS` lines say *"must REACH X and MEASURE an outcome; **winning is NOT required**"* —
so the PASS is instrument health, and the **win is carried by the flag readings**, not by the
acceptance verdict. ‼ Quote the flag, never the ACCEPTANCE line, when claiming a fight was won.
(And `Ch24TailProbeMode` is explicitly OBSERVE-ONLY: its acceptance is instrument health too.)

⇒ ‼ **The rule I broke is `CLAUDE.md` SESSION DISCIPLINE #11**: a claim of the form *"this has
never been done"* is the single most checkable kind of claim in this tree, and I pre-registered it
without grepping. A pre-registration is exactly the wrong document to carry an unchecked "never" —
it is the file a future agent trusts most, because its whole authority rests on being written first.

---

## SO WHAT IS ACTUALLY ON TEST: **PORT FIDELITY**, NOT WHETHER THE PARTY CAN WIN

USER RULING 11 (`06-DECISIONS-LOG.md:6420`) defines §Ch24 DONE as the Hall of Fame entered **from
the REAL story mode, with no fixture scaffolding, at ×1**. Against that bar:

> *"the bot has beaten the Elite Four"* is **TRUE of the harness and FALSE of the product.**

`fight_one_room()` is the **production, species-agnostic generalization** of what those three
bespoke drivers do. ⭐ **THE REAL RISK IS DROPPED KNOWLEDGE.** The proven drivers accumulated
timing that was paid for in failed drives — settles, duty cycles, post-battle waits. A
generalization is a rewrite, and a rewrite silently loses whatever its author did not notice. This
project's most expensive recurring bug shape is *a removed wait*.

⛔ **SPECIES-AGNOSTIC BY REQUIREMENT.** The user's goal is that the team lineup vary between runs,
so nothing in this leg may name a Pokémon, a move or a type. Coverage is a READINESS question for a
different predicate.

---

## PREDICTIONS, each with the falsifier that would refute it

### P1 — the premise holds and is non-vacuous.
GRADED-BY: start_at, pair
Predicted: we start in `SIDNEYS_ROOM`, `DEFEATED_ELITE_4_PHOEBE` is **False**.
**FALSIFIER:** already True ⇒ the fixture is past this unit and the leg must REFUSE, because it
would otherwise report a win it did not cause.

### P2 — the parked victory msgbox clears, and the bot becomes controllable.
GRADED-BY: leg
Predicted `dismissed = True` within the 600-frame budget, using **B** on a duty cycle.
**FALSIFIER:** not dismissed ⇒ either the fixture is not parked on a msgbox, or B is wrong here —
and walking while a script holds input presses into a locked overworld.

### P3 — the hall is crossed and the next room is entered.
GRADED-BY: leg
Predicted `R1-INHALL` then `R1-INROOM`, via `(6,2)` out of the room and `(5,2)` out of the hall.
**FALSIFIER:** stuck on either side ⇒ the door coordinates are not uniform across rooms and halls
as the three proven drivers assume. ⛔ The leg must NOT retry backward: every return warp in the
interior is MEASURED INERT, so a backward "recovery" walks at a tile that never fires — a silent
hang, which is strictly worse than a clean refusal.

### P4 — ⭐⭐ **THE PRODUCTION LEG REPRODUCES WHAT `Ch24PhoebeMode` ALREADY ACHIEVED.**
GRADED-BY: victory_flag_set, elite4_state_at_start
Predicted `DEFEATED_ELITE_4_PHOEBE` becomes **True**, `whiteouts = 0` — **matching the harness
driver's 2026-09-17 result on the same fixture and the same party.**
**FALSIFIER — AND THIS IS THE INFORMATIVE OUTCOME:** the flag stays False, or a whiteout.
⇒ Because the bespoke driver ALREADY WINS here, a loss would **not** mean "the party is too weak";
it would mean **the generalization dropped something the bespoke driver had.** ‼ That is a far more
useful failure than the one I originally wrote down, and it is diagnosable by diffing the two.

### P5 — the leg ends able to continue.
GRADED-BY: end_at
Predicted: standing in `PHOEBES_ROOM` with the flag set — exactly the premise the NEXT unit needs.
**FALSIFIER:** anywhere else ⇒ the units do not compose and the room loop is not a loop.

### P6 — the heal runs and never raises.
GRADED-BY: leg
Predicted `R1-HEALED` present. ⛔ Its failure is RECORDED, never raised: the zone is sealed behind
us, so refusing here strands the bot in a room it cannot leave.
**FALSIFIER:** the leg raises out of the heal ⇒ the no-raise contract is not implemented as written.
‼ And note the harness precedent: on 2026-09-17 I predicted this heal would do nothing and was
**WRONG** — it spent a Super Potion and Phoebe was entered at full HP. Do not re-predict "no-op".

### P7 — ⛔ THE EXIT DOOR IS OPEN IN THE **LIVE** GRID WHEN THE LEG ENDS.
GRADED-BY: leg
Predicted `R1-CONTINUE` taken, `exit_door_open_live = True`, with `(6,1)` and `(6,2)` both `0`.
**FALSIFIER:** the reading is absent ⇒ the victory script did not open the door and **the bot is
sealed in a room it cannot leave** — a FAIL however the fight went. ‼ A win is not a continuable
state: §Ch15 ended four floors underground, §Ch18 on an eleven-tile island and §Ch19 in a living
room, and **all three passed their own tests**. ⛔ It must read `_live_collision_grid`, never
`get_map_data` — `KI-74`: this door is ROM-blocked and runtime-OPENED, so a static read reports it
SHUT on a perfect run.
⚠ SCOPE: `OnLoad` re-opens the door whenever the room's DEFEATED flag is already set, so this
reading is meaningful DURING a run and would be **vacuous on a reloaded post-victory fixture**.

### P8 — THE HEAL ACTUALLY LEFT THE PARTY GAUNTLET-READY.
GRADED-BY: leg
Predicted `heal_ready = True` (the 2026-09-17 harness run measured `actions=1 ready=True` from this
same fixture, spending one Super Potion on Mightyena 187/227).
**FALSIFIER:** `False` or `None` ⇒ the heal ran and accomplished nothing, and the run must FAIL even
with a full reading set. ⛔ `R1-HEALED` is taken UNCONDITIONALLY — the heal must never raise in a
sealed zone — so **the reading set alone cannot catch this**, which is exactly the hole Drake's
`POKEBOT_CH24_FAULT_HEALNOOP=1` arm measured (`heal_ready=False, missing=[], failure=None` →
`ACCEPTANCE: PASS`).

---

## ⚠ THE CODE CHANGED BETWEEN WRITING THIS FILE AND DRIVING IT — SAID PLAINLY

Two independent reviews (a port-fidelity audit against the three proven drivers, and an adversarial
pass) ran **before** the drive and sent the leg back. Every finding below was verified by me at
`file:line` before acting on it, and **P7/P8 above exist because of them** — they are
pre-registration, not post-hoc rationalisation:

| dropped / weakened | proven value | evidence |
|---|---|---|
| ⭐ `wait_until_truly_controllable()` after the DISMISS | present in all 3 drivers | `:17750`, `:18227`, `:18684` |
| ⭐ `wait_until_truly_controllable()` after the HEAL | present in all 3 drivers | `:17783`, `:18260`, `:18736` |
| `dismiss_budget` | **3,000**, not 600 | `:17639`, `:18095`, `:18553` |
| engage budget | **4,000**, not a hardcoded 400 | `ENGAGE_BUDGET` `:18097`, `:18554` |
| the standalone `A` before the modulo loop | part of the verbatim cadence | `:18350-18351` |
| ⭐ the `heal_ready` GRADE conjunct | `heal_ok` gates acceptance | `:18970`, `:19286` |
| ⭐ the live-grid CONTINUE check | reads `_live_collision_grid` | `:18395-18427` |

‼ **The two settles are the ones that would have cost a drive.** The loop they follow exits on a
SINGLE `player_avatar_is_controllable()` reading, which that function's own docstring says
**FLICKERS** through a transition — and the very next step opens the bag menu on the strength of it.
The harness's `_player_controllable_quiet` says so in as many words: *"used here only as a LOOP-EXIT
hint, never as a grade. The real settle is `wait_until_truly_controllable()`, which every branch
calls straight after."* My first version had the hint and not the settle.

---

## ⛔ WHAT THIS DRIVE WILL NOT SETTLE

* **The other three fights**, and the Champion — whose room is structurally different (forced
  battle on entry, no `WalkInCloseDoor` seal).
* **The commitment step.** The fixture starts past it; nothing here opens a door that was shut.
* **RULING 11.** A harness driver running a production function is still not *"the real story mode,
  no fixture, at ×1"*. This is a necessary step toward that bar, not the bar itself.
* **Re-entry after a loss.** That design was reviewed and REJECTED; it needs bag and money
  conjuncts and a §Ch24-owned restock.
* **Whether a VARYING team could win.** This is one party, the curated one.
