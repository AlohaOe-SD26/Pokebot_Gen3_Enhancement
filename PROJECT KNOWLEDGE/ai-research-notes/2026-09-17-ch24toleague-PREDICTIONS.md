# §Ch24 — `ch24toleague` PRE-REGISTERED PREDICTIONS (2026-09-17)

⛔ **WRITTEN AND COMMITTED BEFORE THE DRIVE.** Per the `story-drive` rule: predictions and their
FALSIFIERS are filed first, and a reading that contradicts one is a **RESULT**, never a driver
failure. Graded after.

## WHAT THIS LEG IS, AND WHY IT IS ITS OWN LEG

The finished gauntlet party (`post_e4ice_FINAL.ss1`, all four battlers **L75**, Ice Beam intact) is
parked at **VICTORY_ROAD_1F (15,39)** — the grind tile. §Ch24 begins at the **League door apron
(18,6)**. Nothing connects the two today.

‼ And the obvious move does not work: **Fly is refused on `map_type=Underground`**
(`#24-flymaptype`, verified at `src/overworld.c:1366-1375` — the allow-list is ROUTE / TOWN /
OCEAN_ROUTE / CITY, exactly four). So the route is **walk out first, then Fly**:

    VICTORY_ROAD_1F (15,39)  --hold Down on the ARROW WARP (15,40)-->  EVER_GRANDE_CITY
    EVER_GRANDE_CITY         --Fly to PokemonLeague-->                 (18,6), the door apron

⭐ Both halves are already proven SEPARATELY, which is why this leg is cheap and worth doing before
anything harder: §Ch23 leg 6 holds Down on that same arrow warp (`victory_road.py:2313-2325`), and
`ch24flyto` has flown `PokemonLeague` to `((0,8),(18,6))` with `ACCEPTANCE: PASS`. **What has never
been done is the two in sequence, from THIS party.**

⛔ **THE ARROW WARP IS NOT A STEP.** `MB_SOUTH_ARROW_WARP` fires only while the player is STANDING on
the tile, FACING South and **HOLDING** Down — walking onto it does nothing (`victory_road.py:239-243`).
Hence `_walk_through_warp("Down", ...)`, which keeps pressing, and never a `navigate_to((15,40))`.

## PREDICTIONS, AND WHAT WOULD FALSIFY EACH

| # | Reading | PREDICTION | FALSIFIER — what it would mean |
|---|---|---|---|
| **R1-PREMISE** | start map + tile | `VICTORY_ROAD_1F (15,39)` | Anything else ⇒ **the fixture is not what `FIXTURES.md5` says**. Stop; do not "adapt" — re-verify the save. |
| **R2-EXITED** | map + tile after holding Down | on `EVER_GRANDE_CITY`; tile **RECORDED, not predicted** | Still on `VICTORY_ROAD_1F` ⇒ the arrow warp did not fire and the `_walk_through_warp("Down")` idiom does not work outward from (15,39). ⚠ I deliberately do **not** predict the landing tile: inbound was (18,42)→door(18,41)→(15,40), and assuming the outbound tile is the inbound one is exactly the "never inherit position across a warp" trap. |
| **R3-FLYABLE** | `map_type` at the landing | `City` | `Underground`/`Indoor` ⇒ we never actually left, and `#24-flymaptype`'s guard will (correctly) refuse the Fly. |
| **R4-FLOWN** | map + tile after the Fly | `EVER_GRANDE_CITY (18,6)` | Landing at the **Poké Center (27,49)** instead ⇒ `CB_ExitFlyMap`'s Ever Grande special-case is NOT behaving as documented, and the whole "one Fly to the door" plan needs re-measuring. |
| **R5-CONTINUE** | `neighbours_reachable` off the landing, via a REAL `calculate_path` | `4` | `< 4` ⇒ the bot arrived somewhere it cannot walk out of. ⛔ Not "somewhere reachable" — the same grade `ch24flyto` already uses, so the number is comparable. |
| **R6-ICEBEAM** | Wailord's moves at the end | `Dive, Surf, **Ice Beam**, Waterfall` | Ice Beam missing ⇒ something re-learned a move on a leg with no level-ups. This is the `#24-learnhmcoverage` tripwire and it is cheap to carry, so it is carried. |
| **R7-PIDS** | party PIDs, before vs after | identical, same order | A change ⇒ a reorder or a PC deposit happened during a walk-and-fly. `KI-101` is the stale-order shape; assert IDENTITY, never slot indices. |

### Non-reading expectations (graded, but not readings)

* `whiteouts == 0`. ⛔ **A whiteout here is a hard FAIL, not a retry**: it respawns at (18,6) — which
  looks like success — while having halved the money that `LEAGUE_BASKET` was bought with.
* `battles` — **RECORDED, NOT PREDICTED.** The step from (15,39) onto (15,40) is one tile inside a
  cave with wild encounters, so a battle is *possible* and is **not a failure**: the party is L75
  against L40 wilds. ‼ But if `battles > 0` then the run is no longer a pure navigation measurement,
  and any frame figure from it must be quoted as "including N battles".

## THE VACUITY CONJUNCT — how this grade cannot be satisfied by a no-op

⛔ The standing mechanical test is: **point the driver at its own OUTPUT fixture; if it passes, the
grade measures nothing.** Here that fixture is `post_ch24_atdoor.ss1` (already at (18,6), already on
`EVER_GRANDE_CITY`).

* `R1-PREMISE` requires the start map to be `VICTORY_ROAD_1F`. Pointed at its own output the driver
  is on `EVER_GRANDE_CITY` ⇒ it **refuses at the premise** and takes no readings.
* The grade additionally requires `moved == True` **and** `exited_from_victory_road == True` (we were
  on VR1F and are now not). Neither can be true of a run that started at the door.

⇒ A run that does nothing cannot print PASS.

## FAULT ARM

`POKEBOT_CH24_FAULT_NOEXIT=1` skips the arrow-warp exit and goes straight to the Fly. The Fly must
then be **REFUSED by `#24-flymaptype`'s guard** (`map_type=Underground`), `R3`/`R4`/`R5` must be
missing, and the run must print `ACCEPTANCE: FAIL`.

⭐ This arm is doing double duty on purpose: it proves the exit is load-bearing (without it the leg
cannot fly) **and** it re-exercises the `#24-flymaptype` guard in its natural setting rather than in
a contrived one — which matters, because that guard was added today and its arm so far is a
hand-pointed driver, not a leg that would really hit it.

## WHAT THIS LEG DELIBERATELY DOES **NOT** DO

⛔ It does not enter the League, talk to the guards, or fight anyone. It ends on the apron.
The point is to produce **one pinned fixture — the L75 party at the League door** — so that the
first real Elite Four drive starts from a known state instead of from a walk that has never been
done. Every objection in `#24-leg2spec` is about what happens *after* this tile.


---

# ✅ GRADED — 2026-09-17, ALL THREE ARMS DRIVEN

Evidence committed at `tools/story-dev/evidence/2026-09-17-ch24toleague-{TREATMENT,FAULT-NOEXIT,VACUITY}.txt`.

## TREATMENT — `ACCEPTANCE: PASS`, `missing=[]`, `battles=0`, `whiteouts=0`

| # | PREDICTED | MEASURED | verdict |
|---|---|---|---|
| R1-PREMISE | `VICTORY_ROAD_1F (15,39)` | `((24,43),(15,39))` = VICTORY_ROAD_1F (15,39) | ✅ |
| R2-EXITED | on `EVER_GRANDE_CITY`, tile RECORDED | `((0,8),(18,42))` | ✅ |
| R3-FLYABLE | `City` | `City` | ✅ |
| R4-FLOWN | `EVER_GRANDE_CITY (18,6)` | `arrived=((0,8),(18,6))`, `moved=True` | ✅ |
| R5-CONTINUE | `neighbours_reachable == 4` | `4` | ✅ |
| R6-ICEBEAM | `Dive, Surf, Ice Beam, Waterfall` | identical | ✅ |
| R7-PIDS | identical, same order | `party_pids_stable=True`, `pids_stable=True` | ✅ |

`battles = 0` — **RECORDED, and it came in below the "possible" case.** The single step onto the
arrow warp did not draw a wild encounter, so this run IS a pure navigation measurement and its frame
figures need no "including N battles" caveat.

⭐ **THE ONE READING I DELIBERATELY DID NOT PREDICT CAME BACK AS THE TEMPTING GUESS ANYWAY:** the
outbound landing is **(18,42)** — the same tile the inbound walk departed from. Declining to predict
it was still right: had it landed anywhere else, an asserted (18,42) would have failed a correct run,
and the reason for not predicting it (*never inherit position across a warp*) is unchanged by having
been lucky once.

## FAULT ARM `POKEBOT_CH24_FAULT_NOEXIT=1` — `ACCEPTANCE: FAIL`, for its own reason

    R-FLYABLE map_type=Underground
    FAILURE BotModeError: §Ch24 fly: Fly is REFUSED on `map_type=Underground` at ((24,43),(15,39))
    missing=['R-EXITED', 'R-FLYABLE', 'R-FLOWN', 'R-CONTINUE']

⇒ exactly the four downstream readings, and **the refusal came from the production guard**
(`#24-flymaptype`), not from the driver. ⭐ The arm therefore did its double duty: it proved the exit
is load-bearing (without it the leg cannot fly) **and** it exercised that guard in its NATURAL
setting — a leg that really hits it — rather than the hand-pointed driver it was first tested with.

## VACUITY — pointed at its OWN OUTPUT fixture, it refuses and takes NO readings

    PRE at=((0,8),(18,6))
    ⛔ PREMISE FAILED — this leg must start on VICTORY_ROAD_1F, not ((0,8),(18,6)).
       Refusing, and taking NO readings.
    RESULT premise_ok=False        ACCEPTANCE: FAIL

⇒ the standing mechanical test passes: **a run that does nothing cannot print PASS.**

## OUTPUT

`post_ch24_atdoor_L75.ss1`, md5 `8b8cd907db09a8316c7c8b12856c5e51` — VERIFIED BY RELOADING THE FILE:
EVER_GRANDE_CITY (18,6), all four battlers **L75**, **Wailord `Dive, Surf, Ice Beam, Waterfall`**,
bag 37 Hyper Potion / 3 Full Restore / 18 Full Heal / 3 Revive.

⚠ **ONE THING WORTH CARRYING FORWARD:** Mightyena arrives at **202/227 HP**, not full — grind
damage. That is not a defect here, and League 1F has a **nurse at (3,2) INSIDE the gate**, so leg 2's
first act can be a free full heal before the seal closes. ‼ It is the LAST one that exists
(`#24-leg2spec` O5), so leg 2 should take it rather than start the gauntlet at 89%.
