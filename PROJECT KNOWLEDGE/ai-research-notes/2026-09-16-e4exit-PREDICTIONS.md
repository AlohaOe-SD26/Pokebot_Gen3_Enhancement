# `--driver e4exit` — PREDICTIONS, FILED BEFORE THE RUN (2026-09-16)

> ⛔ Written and committed **before** the driver was executed (`story-drive` §1). Anything the run
> contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Can the bot actually WALK out of Sidney's room after the victory — dismiss the msgbox, cross the
room, and warp into Hall 1?**

This is the last unknown standing in front of §Ch24 leg 1. Two things are already measured and are
NOT what this asks:
* `B` clears the post-victory msgbox and control returns in 297 frames, with a no-press CONTROL
  proving the box does not self-clear (`2026-09-16-e4dismiss-PREDICTIONS.md`).
* `calculate_path` returns a 6-waypoint route to `(6,2)` that goes around the standing trainer and
  lands on `HALL1 (5,12)`, with a positive control, a negative control and a discriminator.

⛔ **NEITHER IS PROOF THE BOT CAN WALK IT.** That is `KI-48`, a standing rule in this project: *a
`calculate_path` OK is not proof the driven navigator can execute it.* This drive is the arm that
tests the navigator, not the planner.

## FIXTURE AND METHOD

`saves/post_sidney_door_open.ss1`, md5 **`6231369647f8`** (PINNED; `verify_fixtures --assert` passes).
The driver reuses shipped helpers rather than writing new machinery — the whole point of the recon:
* dismiss: press `B` on the `script_running or printer-parked` gate (the same gate
  `_wait_until_cutscene_over` uses);
* exit: **`early_game._pass_through_door((6,2), from_map)`** — *"Robustly warp through a door/warp
  tile by making it a NAVIGATION target. A warp fires on a genuine step onto the tile."*
  ⛔ Not a hand-rolled press loop: this project measured that stopping short of a door and
  hand-stepping onto it is flaky (the Petalburg-Woods stall, ML-9).

## THE TWO ARMS

| arm | env | what it does |
|---|---|---|
| **TREATMENT** | *(none)* | dismiss, then walk out through `(6,2)` |
| **CONTROL** | `POKEBOT_E4EXIT_FAULT_NOWALK=1` | dismiss, then **skip the walk** |

The control exists so "we ended in Hall 1" cannot be satisfied by anything other than the walk —
e.g. by a script warping us out on its own.

## PREDICTIONS

| # | reading | TREATMENT | CONTROL | why |
|---|---|---|---|---|
| P1 | `start_map` / `start_tile` | `SIDNEYS_ROOM` `(6,6)` | same | the fixture |
| P2 | `controllable_after_dismiss` | `True` | `True` | already measured: 297 frames |
| P3 | **`end_map`** | **`EVER_GRANDE_CITY_HALL1`** | **`SIDNEYS_ROOM`** | the experiment |
| P4 | `end_tile` | `(5,12)` | `(6,6)` | the warp backbone's predicted landing tile |
| P5 | `walk_frames` | < 3000 | n/a | 6 waypoints across a 13×14 room |
| P6 | `battles` | 0 | 0 | the room has one trainer and he is beaten |
| P7 | `can_continue` | a real `calculate_path` from the Hall1 landing to the hall's north door `(5,2)` returns OK | n/a | ⛔ "arrived" is not "can continue" |

## FALSIFIERS

* **F1 — TREATMENT does not reach Hall 1.** Then `KI-48` bites at this door: the planner's route is
  not executable. Diagnose from the harness's no-progress dump (it names the generator, tile and
  script stack) — ⛔ do NOT respond by hand-rolling a press loop onto the door tile; that is the
  flaky pattern `_pass_through_door` exists to replace.
* **F2 — CONTROL also reaches Hall 1.** Then something other than our walk moves the bot, and the
  TREATMENT result attributes to the navigator something it did not do.
* **F3 — the bot arrives but `can_continue` REFUSES.** Then leg 1 lands somewhere it cannot leave —
  the §Ch15/§Ch18/§Ch19 "passed while stranded" shape this project has hit three times.
* **F4 — `battles > 0`.** Something re-triggered the defeated trainer. The dismiss would then be
  re-opening his script, i.e. pressing the wrong button or pressing it in the wrong state.

## WHAT THIS STILL DOES NOT ANSWER

1. Phoebe / Glacia / Drake. Their ROM layouts are byte-identical and the victory script is shared,
   but that is an INFERENCE. Glacia is additionally the first room whose in-battle lose-text carries
   `\p`, so it is the first that exercises our KI-93 in-battle dismiss at all.
2. The Champion's room, which has **no pre-battle window** and ends in a scripted warp, not a tile.
3. Whether the whole gauntlet is survivable — that is healing and party strength, not routing.

---

# RESULTS — GRADED AFTER THE RUN (2026-09-16)

**VERDICT: THE BOT WALKS OUT. `KI-48` DOES NOT BITE AT THIS DOOR.** Every prediction held; no
falsifier fired. Both arms `ACCEPTANCE: PASS`, graded by opposite expectations on `end_map`.

| reading | TREATMENT | CONTROL (`FAULT_NOWALK=1`) | predicted? |
|---|---|---|---|
| `start_map` / `start_tile` | `(16,0)` `(6,6)` | same | ✅ P1 |
| `controllable_after_dismiss` | `True` (297 frames) | `True` (297) | ✅ P2 |
| **`end_map`** | **`(16,5)` = `EVER_GRANDE_CITY_HALL1`** | **`(16,0)` = `SIDNEYS_ROOM`** | ✅ **P3** |
| **`end_tile`** | **`(5,12)`** | `(6,6)` | ✅ **P4** |
| `walk_frames` | **164** | 0 | ✅ P5 (< 3000) |
| `battles` | 0 | 0 | ✅ P6 |
| `can_continue_to_hall_door_5_2` | **OK 10 waypoint(s)** | REFUSED | ✅ P7 |
| `NEGCONTROL_path_to_0_0` | REFUSED | REFUSED | — (fires on both maps) |

⭐⭐ **`end_tile = (5,12)` IS THE TILE THE WARP BACKBONE PREDICTED**, independently derived from
`map.json` by the routing recon before any of this was run. Two different methods, same tile.

⭐ **THE DISMISS REPRODUCED FROM A SEPARATE DRIVER:** `dismiss_frames = 297`, identical to
`e4dismiss`'s `frames_to_control = 297`. ⚠ Same fixture and a deterministic emulator, so this is a
consistency check across two independent implementations of the same press loop — **not** an
independent replication of the phenomenon (rule 8).

⭐ **AND THE CONTINUATION CHECK EARNED ITS KEEP.** `can_continue` REFUSES in the CONTROL arm — i.e.
it is not a formality that passes wherever you stand. That is the §Ch15/§Ch18/§Ch19 "passed while
stranded" shape being actively excluded rather than assumed away.

## WHAT IS NOW ESTABLISHED FOR LEG 1 — AND WITH NO NEW MACHINERY

1. `B` clears the post-victory msgbox; control returns in 297 frames. (A/B'd: the box does not
   self-clear.)
2. `calculate_path` routes to the runtime-opened door, around the standing trainer, and follows the
   warp. (Positive control, negative control, and a `warps_to` discriminator.)
3. **The driven navigator executes that route** via the shipped `_pass_through_door()`, arriving at
   `HALL1 (5,12)` in 164 frames. (A/B'd against a no-walk arm.)
4. From there the bot can path to the hall's north door — the entrance to Phoebe's room.

⇒ **Leg 1 is a composition of helpers that already ship.** The BFS §G' specs should not be built.

## STILL NOT ESTABLISHED (unchanged by this run)

1. Phoebe / Glacia / Drake — byte-identical ROM layouts and a shared victory script make it very
   likely, but that is an INFERENCE. Glacia is also the first room whose in-battle lose-text carries
   `\p`, i.e. the first to exercise our KI-93 in-battle dismiss at all.
2. The Champion's room: **no pre-battle window**, and it ends in a scripted warp, not a tile.
3. Whether the gauntlet is SURVIVABLE. That is healing and party strength, not routing — and the
   bag is the only healing, because the gauntlet is one-way.

---

# EXTENSION — PREDICTIONS FILED BEFORE THE RUN (2026-09-16, after a user note)

## WHY THIS EXTENSION EXISTS — A SCOPING ERROR, NOT A NEW DISCOVERY

The user pointed out: *"between each elite 4 member room, there is a straight path (in between room)
that they have to walk across when leaving the prior room, to then walk that path and actually go
through the door to the next elite 4 member, and so on, it is a longer path to the champions room."*

⛔ **THE GAUNTLET'S REPEATING UNIT IS `room → hall → next room`, AND I HAD SCOPED LEG 1 TO STOP
HALF-WAY** — at the hall LANDING `(5,12)`, treating "arrived in the hall" as the end. It is not: the
hall is a corridor that must be WALKED, and the door at its top is a second warp. Everything measured
so far ends at the landing.

**The geometry is now measured from our own map data** (`probe_e4_halls.py`, new; controls hold —
every forward door reads collision 0, every corner reads 1):

| hall (WALKING order) | steps | from → to |
|---|---|---|
| HALL5 lobby → Sidney | 10 | (5,12) → (5,2) |
| HALL1 Sidney → Phoebe | 10 | (5,12) → (5,2) |
| HALL2 Phoebe → Glacia | 10 | (5,12) → (5,2) |
| HALL3 Glacia → Drake | 10 | (5,12) → (5,2) |
| **HALL4 Drake → Champion** | **31** | **(5,33) → (5,2)** |

⇒ the user's "longer path to the champions room" is **confirmed: 31 steps vs 10**, and it agrees with
the live `can_continue_to_hall_door_5_2 = OK 10 waypoint(s)` already measured out of HALL1.
‼ **AND THE HALL NUMBERING IS NOT THE WALKING ORDER** — HALL**5** is the FIRST hall (lobby → Sidney),
then 1 → 2 → 3 → 4. A leg that iterates `HALL1..HALL5` walks the gauntlet in the wrong order.

## THE QUESTION

**Can the bot complete the full repeating unit — dismiss, leave Sidney's room, WALK HALL1, and pass
through its far door into Phoebe's room?**

## ARM

`POKEBOT_E4EXIT_CONTINUE=1` on `--driver e4exit`, from the same pinned `post_sidney_door_open.ss1`.
The existing two arms are unchanged and keep their settled acceptance.

## PREDICTIONS

| # | reading | expected | why |
|---|---|---|---|
| X1 | `hall_landing` | `EVER_GRANDE_CITY_HALL1 (5,12)` | already measured |
| X2 | `hall_walk_frames` | < 3000 | 10 steps |
| X3 | **`final_map`** | **`EVER_GRANDE_CITY_PHOEBES_ROOM`** | the experiment |
| X4 | `final_tile` | on column x=6, y in 7..13 | the entry warp is (6,13) and the script auto-walks up to (6,7); ⛔ it is sampled live and NOT asserted to a constant — the auto-walk is CONDITIONAL on `ELITE_4_STATE == 1` |
| X5 | `elite4_state_final` | **2** | Phoebe's entry script sets it; 1 would mean the entry cutscene did not run |
| X6 | `battles` | **0** | entering an E4 room does NOT start the fight — the trainer is an INTERACTION script, not a sight trigger. ⚠ Only the CHAMPION's room `goto`s straight into battle, and that is not this room |
| X7 | `whiteouts` | 0 | no fight should occur |

## FALSIFIERS

* **XF1 — `final_map` is still HALL1.** The hall walk or the far door does not execute. The repeating
  unit is then broken and leg 1 cannot chain, whatever the geometry says.
* **XF2 — `battles > 0`.** Entering Phoebe's room starts a fight unprompted ⇒ my X6 model is wrong,
  and every later leg's frame budget and healing plan must account for a fight on entry.
* **XF3 — `elite4_state_final != 2`.** The entry cutscene did not run, which per the recon means **no
  auto-walk AND no entry seal** — the bot would be standing somewhere unmodelled and the room would
  not be sealed behind it.
* **XF4 — the bot arrives but on a tile outside x=6.** The auto-walk did something other than
  `Common_Movement_WalkUp6`, and no coordinate in the spec can be trusted for rooms 2-5.

---

# EXTENSION RESULTS — GRADED AFTER THE RUN (2026-09-16)

**VERDICT: THE FULL REPEATING UNIT WORKS. `room → hall → next room` IS DRIVEN, AND IT CHAINS.**
`ACCEPTANCE: PASS`. Every prediction held; no falsifier fired.

| # | reading | measured | predicted? |
|---|---|---|---|
| X1 | `hall_landing` | `(5,12)` in HALL1 | ✅ |
| X2 | `hall_walk_frames` | **219** | ✅ (< 3000) |
| X3 | **`final_map`** | **`(16,1)` = `EVER_GRANDE_CITY_PHOEBES_ROOM`** | ✅ **the experiment** |
| X4 | `final_tile` | **`(6,7)`** | ✅ (on x=6, y in 7..13) |
| X5 | `elite4_state_final` | **2** | ✅ |
| X6 | `battles` | 0 | ✅ |
| X7 | `whiteouts` | 0 | ✅ |
| — | `can_continue_to_phoebe_6_6` | `OK 1 waypoint(s)` | one step from the trainer |
| — | `NEGCONTROL_path_to_0_0` | `REFUSED` | the control still fires on the new map |

**THE WHOLE TRANSITION, END TO END:** `SIDNEY (6,6)` —dismiss **297f**→ exit door —**164f**→
`HALL1 (5,12)` —walk the hall—**219f**→ `PHOEBE (6,7)`, `ELITE_4_STATE 1→2`, zero battles, standing
one step from the next trainer. **~680 frames for a complete inter-room transition.**

⭐⭐ **X4 IS THE THIRD INDEPENDENT CONFIRMATION OF `(6,7)`, AND THE FIRST *DIRECT* ONE.** The recon
derived it arithmetically (entry warp (6,13) − `Common_Movement_WalkUp6` = 7); the `elite4_state=0`
discriminator showed the earlier `(6,11)` was sampled mid-walk; and now the bot is MEASURED standing
on `(6,7)` after a deliberate 240-frame settle. ⇒ the `(6,7)` vs `(6,11)` question is closed, and it
closed in the note's favour.

⭐ **X5 IS NOT DECORATION.** `ELITE_4_STATE == 2` is Phoebe's ENTRY script having run, which per the
recon is what fires *both* the auto-walk and the entry seal. A `1` would have meant the cutscene did
not run ⇒ no auto-walk and **an unsealed room** (falsifier XF3). It read 2.

## ⚠ ONE INSTRUMENT WART, FOUND AND FIXED MID-RUN

The first continue run printed `can_continue_to_hall_door_5_2 = REFUSED … @ EVER_GRANDE_CITY_PHOEBES_ROOM`.
The reading is computed AFTER the continuation, so it was asking for HALL1's door while standing in
Phoebe's room — **a REFUSED that means nothing**, and exactly the "measured the wrong quantity" shape
this session already has two mistakes entries about. Fixed by deriving the target from the state the
run actually reached (session rule 4): in the next room, "can continue" means "can I reach the
trainer I came here to fight". It now reads `OK 1 waypoint(s)` and is part of the grade.

## WHAT THIS DOES *NOT* SHOW

1. **Phoebe is not fought.** The run ends standing next to her. Whether the bot can BEAT her — and
   the four after her, on one party with no nurse — is untouched.
2. Only the `SIDNEY → HALL1 → PHOEBE` instance is driven. The other three transitions share the
   geometry (`probe_e4_halls.py`: all short halls 10 steps, identical landings) and the same victory
   script, but that is an INFERENCE.
3. ⛔ **HALL4 IS 31 STEPS, NOT 10**, and the Champion's room beyond it has **no pre-battle window** —
   it `goto`s straight into Wallace's fight. That last transition is NOT this shape and must not be
   assumed to be.

---

# SIDESTEP ARM — PREDICTIONS FILED BEFORE THE RUN (2026-09-16), `#24-hallwarpdisputed`

## THE QUESTION
**Does stepping ONE TILE WEST in HALL1 warp the bot back into the cleared Sidney room?**

Two of our own docs disagree, on the exact hall leg 1 walks:
* `2026-09-04-ch24-LEAGUE-INTERIOR-ROUTING.md:139` — the backward warps are **destination-only**
  (`MB_NORMAL`, which `IsWarpMetatileBehavior` rejects), so stepping on one never fires.
* `2026-09-07-ch24-elite-four-BUILD-SPEC.md:157` + `03-PUNCH-LIST.md` — **a single sidestep warps you
  back into the cleared room.** ‼ Derived from `get_map_data(...).warps`, a warp-**EVENT TABLE**,
  which lists arrival destinations and says nothing about whether a tile can TRIGGER a warp.

**OFFLINE HALF, ALREADY MEASURED** (`probe_e4_halls.py`, all five halls): every backward tile
(4,12)/(5,12)/(6,12) reads behaviour **`'Normal'`**, collision 0. That is consistent with
destination-only and NOT with "a sidestep warps you back" — but behaviour is not the game's actual
refusal, so this arm measures the refusal.

## ARM
`POKEBOT_E4EXIT_SIDESTEP=1` on `--driver e4exit`, from the pinned `post_sidney_door_open.ss1`. It runs
the normal dismiss + exit, and then — standing on `HALL1 (5,12)` — presses **West** and logs map+tile.

## PREDICTIONS
| # | reading | expected | why |
|---|---|---|---|
| S1 | `sidestep_from` | `HALL1 (5,12)` | the measured landing |
| S2 | **`sidestep_map`** | **still `EVER_GRANDE_CITY_HALL1`** | `MB_NORMAL` cannot trigger a warp |
| S3 | `sidestep_tile` | `(4,12)` | one tile west, and it is collision 0 so the step is legal |
| S4 | `sidestep_warped` | **False** | the verdict |

## FALSIFIERS
* **SF1 — `sidestep_map` is `SIDNEYS_ROOM`.** Then the BUILD-SPEC half is right, the behaviour byte
  is NOT the whole story, and ⛔ leg 1's hall walk must be column-constrained and defensive. This
  would also mean a cleared room can be silently re-entered, which changes `ELITE_4_STATE` handling.
* **SF2 — the bot does not move at all** (`sidestep_tile` still `(5,12)`). Then (4,12) is not walkable
  in practice despite collision 0, and the hall is narrower than the grid says — also useful, and it
  would make the whole question moot.
* **SF3 — it moves somewhere other than (4,12).** The step model is wrong; distrust every other
  position reading in this driver.

## SIDESTEP RESULTS — GRADED (2026-09-16)

**VERDICT: A SIDESTEP DOES NOT WARP. `#24-hallwarpdisputed` IS SETTLED, AND THE PUNCH-LIST HALF WAS
WRONG.** All four predictions held; no falsifier fired.

    [e4exit] SIDESTEP from ((16, 5), (5, 12)) -> (16, 5)(4, 12) warped=False

| # | reading | measured | predicted? |
|---|---|---|---|
| S1 | `sidestep_from` | `HALL1 (5,12)` | ✅ |
| S2 | **`sidestep_map`** | **`(16,5)` = still `EVER_GRANDE_CITY_HALL1`** | ✅ **the experiment** |
| S3 | `sidestep_tile` | `(4,12)` | ✅ it moved — the step was legal |
| S4 | `sidestep_warped` | **False** | ✅ |

⭐ **TWO INDEPENDENT METHODS AGREE.** The behaviour byte (`probe_e4_halls.py`: all 15 backward tiles
across all five halls read `'Normal'`, i.e. `MB_NORMAL`, which `IsWarpMetatileBehavior` rejects) and
the live step (the bot stood on (4,12) and stayed). ⇒ `2026-09-04-ch24-LEAGUE-INTERIOR-ROUTING.md:139`
is RIGHT; `2026-09-07-ch24-elite-four-BUILD-SPEC.md:157` and the punch-list copy are **REFUTED**.

‼ **AND THE PROVENANCE EXPLAINS THE ERROR:** the refuted half was derived from
`get_map_data(...).warps` — a warp-**EVENT TABLE**, which lists arrival destinations. A tile can be a
warp's DESTINATION without being able to TRIGGER one. **Reading the destination table as a trigger
list is the same class as reading a candidate list as an attempt.**

⇒ **CONSEQUENCE FOR LEG 1: the hall may be walked normally.** The "column-constrained, never
sidestep" caution is retired — it was guarding against a hazard that does not exist.
⚠ Measured for HALL1 only; the other four halls share the behaviour reading but not the live step.
