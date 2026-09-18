# `--driver ch24hall4` — PREDICTIONS, FILED BEFORE THE RUN (2026-09-17, late)

> ⛔ Written and committed **before** the driver was executed (`story-drive` §1). Anything the run
> contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Can the bot walk to the Champion's door and STOP — deliberately not arriving?**

Rooms 1–4 all ended by walking THROUGH a door. This leg must not: crossing `HALL4 (5,2)` starts an
**unavoidable, un-fleeable championship battle**, so the leg's whole job is to get one tile away and
mint a fixture there. It is the first stop-short leg this project has built.

## WHAT IS ALREADY ESTABLISHED (verified at source/measurement, not assumed)

| # | fact | how |
|---|---|---|
| E1 | `IS_CHAMPION` is a REAL flag — id **2175** | `modules/data/event_flags/emerald.txt:1061` |
| E2 | Entering the Champion's room starts the fight with NO frame to stop in — `LoadMapFromWarp` → `ClearTempFieldEventData` zeroes `VAR_TEMP_1`; `OnFrame` is `map_script_2 VAR_TEMP_1, 0, ..._EventScript_EnterRoom`, matching on the first controllable frame; its first command is `lockall` | decomp, recon angle `champroom` |
| E3 | `"allow_escaping": false` in the room's `map.json`, and there is **no defeated-flag guard** anywhere in its script ⇒ a re-entry re-fights him at full strength | decomp |
| E4 | `navigate_to(HALL4,(5,3))` = 30 waypoints, ends `is_warp=False`, crosses no warp. The control aiming at `(5,2)` ends `is_warp=True` **already inside `CHAMPIONS_ROOM (6,12)`** | MEASURED by the adversarial recon angle |
| E5 | `navigate_to` is MAP-LOCAL: *"Warps … will not be used automatically -- but a door can be used as a destination."* | `modules/modes/util/walking.py:409-424`, read by me |
| E6 | `_pass_through_door` makes the warp the navigation DESTINATION by construction ⇒ **must not be used for HALL4's far door** | `modules/story/early_game.py`, recon |
| E7 | HALL4 is **31 steps**, `(5,33)`→`(5,2)`, the only hall on its own layout (2 warps) | MEASURED, `probe_e4_halls.py` + `probe_e4_warp_chain.py` |
| E8 | ⭐ The Hall of Fame script **clears all four `DEFEATED_ELITE_4_*` and resets `VAR_ELITE_4_STATE` to 0 BEFORE `special GameClear`** ⇒ a room-5 grade on those flags reads FALSE on success | decomp `event_scripts.s`, recon |
| E9 | Start fixture `post_drake_L75.ss1` (`51cd43a8e427`): DRAKES_ROOM (6,6), Mightyena **0/230 FAINTED**, Sceptile 73/205, **2 Revives** | MEASURED by reload, with controls |

## THE ARMS

| arm | fixture / env | expected |
|---|---|---|
| **TREATMENT** | `post_drake_L75.ss1`, `CH24_HALL4_CAPTURE=post_hall4_door` | `ACCEPTANCE: PASS`, `missing=[]`, fixture minted |
| **VACUITY** | `post_glacia_L75.ss1` (wrong map, `DRAKE=False`) | refuse at the premise, **zero readings**, FAIL |
| **FAULT `NOSTOP`** | `POKEBOT_CH24_FAULT_NOSTOP=1` | FAIL with `H-STOPSHORT` **and** `H-CAPTURE` missing |
| **FAULT `NOROOMHEAL`** | `POKEBOT_CH24_FAULT_NOROOMHEAL=1` | FAIL on `heal_ready` (non-vacuous — the fixture has a fainted mon) |

⛔ **THERE IS DELIBERATELY NO "OVERSHOOT" ARM.** An arm targeting `(5,2)` would start the
championship battle and spend the fixture. That is a measurement to make on purpose in leg B, never
as a fault injection.

## PREDICTIONS

| # | reading | prediction | falsifier |
|---|---|---|---|
| P1 | `PRE at` | `((16,3), (6,6))` — DRAKES_ROOM | any other tile ⇒ wrong fixture |
| P2 | `PRE` flags | `drake=True`, `champion=False`, `game_clear=False` | `champion=True` ⇒ the fixture is post-Wallace |
| P3 | `dismiss_presses` | **60–140.** Drake's `Text_PostBattleSpeech` is **6 pages**, the longest in the gauntlet; 77 presses cleared Phoebe's 4-page speech, so ~110 is the expectation | 500 (budget) ⇒ B is not clearing it |
| P4 | `H-HEAL` | `heal_actions = 3`, `heal_ready=True`, Mightyena **revived**, Sceptile topped up, **Revive 2 → 1** | `heal_actions=0` ⇒ the readiness predicate tolerates a fainted mon |
| P5 | `hall4_landing` | `((16,8), (5,33))` — HALL4's far-end landing | anything else ⇒ E7 wrong |
| P6 | `stopped_tile` | **exactly `(5,3)`**, still on HALL4 | ⛔ `CHAMPIONS_ROOM` ⇒ the stop-short FAILED, the warp was crossed, and a championship battle is starting |
| P7 | `battles` | **0** | any battle ⇒ the leg crossed the warp; this leg must fight nothing |
| P8 | `H-CAPTURE` | taken; `post_hall4_door.ss1` written, guard all-True | refused ⇒ read the guard, not the driver |
| P9 | run totals | `whiteouts=0` | a whiteout in a leg that fights nothing means it met Wallace |

⚠ **P3 IS THE ONE I AM LEAST SURE OF.** The dismiss count has tracked the PREVIOUS room's speech
every time (Phoebe's 4 pages → 77 presses; Glacia's 2 → 35), so 6 pages predicts ~110. If it comes
back near 35 the model is wrong and the relationship is not page-count.

## HOW THIS GETS GRADED

A **GRADED** section is appended after the runs: every P row marked ✅ met, ❌ refuted, or
⚠ unreadable, with the literal log line beside it. A row that cannot be quoted was not measured.

---

# GRADED — 2026-09-17 (late), AFTER THE RUNS

**Evidence (committed):** `tools/story-dev/evidence/2026-09-17-ch24hall4-{TREATMENT,VACUITY-WRONG-ROOM,FAULT-NOSTOP,FAULT-NOROOMHEAL-ISOLATED}.stdout.txt`
and `...-FIXTURE-VERIFY-BY-RELOAD.txt`.

## HEADLINE: ✅✅✅ **THE STOP-SHORT WORKS. THE BOT WALKED TO THE CHAMPION'S DOOR AND DID NOT ARRIVE.**
`ACCEPTANCE: PASS`, `missing=[]`, **`battles=0`**, `whiteouts=0`.
`H-STOPSHORT at=((16,8),(5,3)) tile=(5,3) on_hall4=True right_tile=True`.
`post_hall4_door.ss1` minted and pinned (`1f15cc400218`).

## THE FOUR ARMS

| arm | result | |
|---|---|---|
| TREATMENT | `ACCEPTANCE: PASS`, `missing=[]`, `battles=0`, fixture minted | ✅ |
| VACUITY (wrong room) | refused, naming BOTH failing conjuncts (`map`, `drake=False`), zero readings | ✅ |
| FAULT `NOSTOP` | `missing=['H-CAPTURE','H-STOPSHORT']`, FAIL — and the capture guard REFUSED on its own | ✅ |
| FAULT `NOROOMHEAL` | **`missing=['H-HEAL']` ALONE** + `heal_ready=None`, FAIL | ✅ isolated — see below |

‼ **THE NOROOMHEAL ARM WAS RUN TWICE, AND THE FIRST RUN WAS A CONFOUND I CAUGHT AND FIXED.**
Run 1 omitted `CH24_HALL4_CAPTURE`, so it failed on **both** `H-HEAL` *and* `H-CAPTURE` — two
independent reasons, which is precisely the flaw `#24-healgradearm` had just been closed over
("an arm that fails for several reasons at once proves nothing about any one of them"). Run 2 sets
the capture var so the only difference from the treatment is the heal, and it fails on
**`missing=['H-HEAL']` alone**. Only run 2 is committed as the arm; run 1 is discarded as invalid.

## P-ROW GRADES

| # | predicted | measured | |
|---|---|---|---|
| P1 | `((16,3),(6,6))` | exactly that | ✅ |
| P2 | `drake=True, champion=False, game_clear=False` | exactly that | ✅ |
| P3 | 60–140 presses | **`dismiss_presses = 128`** | ✅ ⭐ **and the page-count model now holds across THREE rooms**: Glacia 2 pages → 35, Phoebe 4 → 77, **Drake 6 → 128**. The dismiss count tracks the PREVIOUS room's speech, roughly linearly |
| P4 | `heal_actions=3`, revived, `Revive 2→1` | `heal_actions=3 ready=True`; Mightyena `0/230 → 230/230`; Sceptile `73 → 205`; bag `Hyper Potion 32→30, Revive 2→1` | ✅ ⚠ one refinement: the plan spent **two Hyper Potions**, not a Full Restore (`Full Restore 2→2`) — correct, because both targets are above the 200 flat-heal boundary (`#24-healfullrestorewaste`) |
| P5 | `((16,8),(5,33))` | exactly that | ✅ |
| P6 | exactly `(5,3)`, still HALL4 | `on_hall4=True right_tile=True` | ✅✅ **the load-bearing one** |
| P7 | `battles=0` | `battles=0` | ✅ |
| P8 | capture taken, guard all-True | `✅ CAPTURED -> post_hall4_door.ss1 … at ((16,8),(5,3))` | ✅ |
| P9 | `whiteouts=0` | `whiteouts=0` | ✅ |

**Every prediction met.** ⚠ That is worth one caveat rather than a victory lap: this leg is
deliberately the *easy* half — it fights nothing and crosses one door it has crossed four times
before. The hard half (Wallace + the endgame tail) is entirely ahead.

## ⭐ WHAT THE FIXTURE IS WORTH

`post_hall4_door.ss1` is the cleanest state in the gauntlet: **fully healed** (`gauntlet_ready=True`,
`fainted=[]`, `HEAL PLAN=[]`), Ice Beam intact, standing one tile from the Champion's door having
fought nothing. Leg B starts here instead of re-driving four rooms. ‼ **One Revive remains, and
there is no heal after this point** — the warp starts the fight on the first controllable frame.
