# `--driver ch24lobby` — PREDICTIONS, FILED BEFORE THE DRIVE (2026-09-18)

> ⛔ Written and **committed before the driver was written or executed** (`story-drive` §1).
> Anything the run contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Mint a LOBBY fixture, so the §Ch24 "lobby window" is READ rather than traced.** No fixture in this
repo stands in the League lobby (`grep -c POKEMON_LEAGUE_1F saves/FIXTURES.md5` → 0), so the claim
"zero §Ch23 legs fire there" currently rests on an agent probe.

## ⛔ WHAT MAKES THIS DRIVE DANGEROUS, AND THE TWO DEFENCES

`LEAGUE_1F (9,1)` is a **STEP-ON door (`MB_NON_ANIMATED_DOOR`) into HALL5** — one tile from the
gauntlet, which is un-fleeable. A path routed north along x=9 would cross it.

1. **THE GUARDS ARE THE PRIMARY DEFENCE, AND THEY ARE WHY WE DO NOT TALK TO THEM.** While
   `ENTERED_ELITE_FOUR` is unset they stand **ON `(9,2)/(10,2)`**, *"blocking the north doors
   positionally"* (`victory_road.py:399-402`) ⇒ the planner cannot route through them.
   ⭐ This is the decision recorded on 2026-09-18: *mint the fixture on the REVERSIBLE side of an
   irreversible step first.*
2. **A PATH ASSERTION IS THE SECOND DEFENCE.** Before moving, the driver computes the route and
   **refuses to walk it if it contains any of `(9,1) (10,1) (9,2) (10,2) (1,7)`** — the two gauntlet
   doors, the two guard tiles, and the escalator to League 2F. ⛔ A tripwire also refuses to run at all
   if the stop tile is ever edited to equal a forbidden tile.

## THE ARMS

| arm | fixture / env | expected |
|---|---|---|
| **TREATMENT** | `post_ch24_atdoor_L75.ss1`, `CH24_LOBBY_CAPTURE=post_league_lobby` | `ACCEPTANCE: PASS`, fixture minted |
| **VACUITY** | a fixture already inside the League (`post_hall4_door.ss1`) | refuse at the premise, **zero readings** |
| **FAULT `NOPATHCHECK`** | `POKEBOT_CH24_FAULT_NOPATHCHECK=1` | the path assertion is skipped ⇒ the run must still NOT reach a sealed map, but the reading proves the assertion was live |

⛔ **THERE IS DELIBERATELY NO "WALK TO (9,1)" ARM.** It would enter the gauntlet and spend the fixture.

## PREDICTIONS

| # | reading | prediction | falsifier |
|---|---|---|---|
| P1 | `PRE at` | `((0,8),(18,6))` — EVER_GRANDE_CITY, the League door apron | any other tile ⇒ wrong fixture |
| P2 | flag-name vacuity assert | **PASSES** — `ENTERED_ELITE_FOUR` and `LANDMARK_POKEMON_LEAGUE` are both in `_event_flags` | a failure ⇒ the bare-name fix was wrong |
| P3 | `PRE entered_e4` | **False** (this lineage has never talked to the guards) | True ⇒ the start fixture is already post-talk, and the "positionally sealed" defence is absent |
| P4 | after the door hold | on `POKEMON_LEAGUE_1F (16,10)` | still on EG ⇒ the HOLD-Up animated-door handling failed |
| P5 | planned path to `(3,4)` | contains **none** of `(9,1) (10,1) (9,2) (10,2) (1,7)` | any hit ⇒ ⛔ REFUSE TO WALK; the guards are not where we think |
| P6 | `stop_tile` | exactly **`(3,4)`**, still on `POKEMON_LEAGUE_1F` | a sealed map ⇒ the stop-short FAILED and a gauntlet fight is starting |
| P7 | `battles` / `whiteouts` | **0 / 0** | any battle ⇒ we crossed a door |
| P8 | `POST entered_e4` | **still False** — we never talk | True ⇒ we talked by accident; the fixture is contaminated and must not be pinned as no-talk |
| P9 | lobby predicates | `inside_league=True`, `at_ever_grande_top=True`, `ch23_chapter_done=False`, `marker(sealed)=False` | `ch23_done=True` ⇒ the basket conjunct is satisfied and §Ch23 would grade done in the lobby |
| P10 | **§Ch23 leg guards in the lobby** | ⭐ **ZERO fire.** Derived per leg: 1-3 (lobby ∉ `_PRE_DEPARTURE_MAPS`), 4 (`at_ever_grande_top()` True via `inside_league()`), 5 (lobby is neither EG nor VR1F), 6-9 (not on a VR map), 10-11 (`_on_map(EG)` False) | **any leg firing is the most valuable result this drive can produce** — it would mean §Ch23 acts inside the League |
| P11 | capture | `post_league_lobby.ss1` written, md5 pinned | refused ⇒ read the guard, not the driver |

⚠ **P10 IS THE ONE I AM LEAST SURE OF**, and it is the whole point of the drive. The agent trace said
zero; my own derivation above says zero; but both are *reasoning about* the guards. This drive
**reads** them. If it disagrees with the trace, the trace was wrong and prerequisite (1)'s design needs
revisiting before implementation.

⚠ **P5 IS THE ONE THAT PROTECTS THE FIXTURE.** If it fails the run must ABORT rather than walk.

## HOW THIS GETS GRADED

A **GRADED** section is appended after the runs: every P row marked ✅ met, ❌ refuted, or ⚠ unreadable,
**with the literal log line beside it**. A row that cannot be quoted was not measured.


---

# ⭐ GRADED — 2026-09-18, AFTER THE RUNS

> Every row carries the literal log line it is graded on. **A row that cannot be quoted was not
> measured**, and is marked ⚠ rather than ✅.
> Evidence: `tools/story-dev/treat_lobby.log` (TREATMENT, minted the fixture),
> `treat10_lobby.log` (re-read with the CORRECTED ten-call-site instrument),
> `vacuity_lobby.log`, `nopathcheck_lobby.log`, `nostop_lobby.log`,
> `evidence/2026-09-18-ch23-leg-guards-TEN-CALL-SITES.stdout.txt`.

| # | verdict | the line it is graded on |
|---|---|---|
| P1 | ✅ MET | `PRE at=((0, 8), (18, 6)) tile=(18, 6)` |
| P2 | ✅ MET | `flag-name vacuity guard OK (1164 entries, names ['ENTERED_ELITE_FOUR', 'LANDMARK_POKEMON_LEAGUE'])` |
| P3 | ✅ MET | `flags={'ENTERED_ELITE_FOUR': False, 'LANDMARK_POKEMON_LEAGUE': True}` |
| P4 | ✅ MET | `IN LOBBY at=((16, 10), (9, 11)) tile=(9, 11)` — `(16,10)` is `POKEMON_LEAGUE_1F`, and `(9,11)` is exactly `LEAGUE_ENTRY_LANDING` (`victory_road.py:396`) |
| P5 | ✅ MET | `PATH SAFE — 13 waypoints, no forbidden tile. path=[(9, 10), (9, 9), (9, 8), (9, 7), (9, 6), (9, 5), (9, 4), (8, 4), (7, 4), (6, 4), (5, 4), (4, 4), (3, 4)]` — the route climbs x=9 only to **y=4**, two tiles clear of the guards at y=2 |
| P6 | ✅ MET | `STOPPED at=((16, 10), (3, 4)) tile=(3, 4)` |
| P7 | ✅ MET | `RESULT battles=0 whiteouts=0 failure=None` |
| P8 | ✅ MET | `CAPTURE GUARD on_lobby=True at_stop=True entered_e4_still_False=True battles=0` |
| P9 | ⚠ **PARTLY UNREADABLE — AND I AM NOT SCORING IT ✅** | `PREDICATES {'inside_league': True, 'at_ever_grande_top': True, 'ch23_chapter_done': False, 'wally_beaten': True}`. Three of the four predicted values are met. ⛔ **The fourth, `marker(sealed)=False`, COULD NOT BE READ: the §Ch24 marker DOES NOT EXIST IN CODE YET** — it is prerequisite (1)'s deliverable, still unbuilt. Predicting a reading of a predicate that has never been written was an error in the predictions file, not a result. |
| P10 | ⭐ **MET, AND IT IS THE RESULT THIS DRIVE EXISTED FOR — BUT THE ORIGINAL ENUMERATION WAS WRONG** | `⭐ LEG GUARDS IN THE LOBBY: fire=NONE  all={'1-3': False, '4': False, '4b-train': False, '5': False, '6': False, '7': False, '8': False, '9': False, '10': False, '11': False}` (`treat10_lobby.log`). ⛔ The first run read **nine** call sites; an adversarial reviewer found a **tenth** (the unnumbered TRAINING leg, `victory_road.py:3430-3431`) and a **nested** conjunct on leg 11. Both instruments were corrected and re-run; the verdict NONE survives at ten. |
| P11 | ✅ MET | `✅ CAPTURED -> post_league_lobby.ss1 (397312 bytes) at ((16, 10), (3, 4)) (3, 4)`; pinned `5a75ea37ed5cc07ae8b0b0a75da5e909`; ⭐ re-verified by RELOAD (`probe_ch23_leg_guards.py` loads it and reports `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (3, 4)`), never by the capture line |

## THE ARMS

| arm | expected | measured | verdict |
|---|---|---|---|
| TREATMENT | PASS, fixture minted | `ACCEPTANCE: PASS`, `readings=['L-CAPTURE','L-INLOBBY','L-LEGGUARDS','L-PATHSAFE','L-PRE','L-PREDICATES','L-STOP'] missing=[]` | ✅ |
| VACUITY (`post_hall4_door`) | refuse at the premise, **zero readings** | `FAILURE BotModeError: ... premise failed ... we are at ((16, 8), (5, 3))`, `readings=[] missing=[all six]` | ✅ |
| FAULT `NOPATHCHECK` | `L-PATHSAFE` missing, still no sealed map | `missing=['L-PATHSAFE']` — **and nothing else**; `battles=0`, still stopped at `(3,4)` | ✅ fails for its OWN reason |
| FAULT `NOSTOP` *(extra arm, not pre-registered)* | `L-STOP` + `L-CAPTURE` missing, **no fixture written** | `missing=['L-CAPTURE', 'L-STOP']`, `⛔ CAPTURE REFUSED — the guard above is not all-True`, and the refused name wrote **0** files | ✅ |

## ⛔⛔ THREE RESULTS THE PREDICTIONS DID NOT ANTICIPATE

**1. ⭐⭐ "EVERY LEG SELF-SKIPS" IS THE WRONG FRAME — §Ch23 *RAISES* IN THE LOBBY.**

⛔⛔ **CORRECTED BEFORE COMMIT — THE RAISE WAS *ALREADY DERIVED*, AND I ALMOST PUBLISHED IT AS NEW.**
`06-DECISIONS-LOG.md` already says, of wiring Segment 24: *“Any raise past that door re-enters
`do_victory_road_chapter()`, whose eleven legs are all position-gated and all self-skip, three times,
then raises ⇒ 4 derails ⇒ Manual, parked in a sealed Elite Four room.”* ‼ That file exists so a
question is never answered twice, and it is **not** in the session-start reading set — which is
exactly how it gets written to and never read from (`CLAUDE.md` §11).
⇒ **WHAT THE DRIVE ACTUALLY ADDED IS SMALLER, AND SHARPER:**
1. It **MEASURED** what was derived — `ch23_chapter_done() == False` and all ten guards False, read
   live in the lobby rather than reasoned from the source.
2. ⭐ **It moved the finding from the SEALED ROOMS to the LOBBY, and that is a different place.** The
   standing derivation is about stepping *past the League's front door* into the one-way gauntlet.
   The lobby is **`POKEMON_LEAGUE_1F (16,10)`, which the marker design deliberately EXCLUDES**
   (§Ch23's own legs 10 and 11 work there), and `06-DECISIONS-LOG.md` Decision 3 calls the lobby
   *“protected by the very property that makes the helper wrong for the marker”*. ⛔ **That protection
   is only ‘leg 4 does not wrongly fire’ — it does not prevent the raise.**
3. ⭐⭐ And the tile it measured on is not arbitrary: `heal_at_league` holds Up through the same door
   and runs `_navigate_riding_out(LEAGUE_1F, LEAGUE_NURSE_STAND)` — **`(3,4)`, the exact tile this
   fixture stands on**. ⇒ the fixture is the state §Ch23 puts *itself* in during leg 10, and §Ch23
   cannot resume from it. **That is a §Ch23 resumability hole, not a §Ch24 marker gap**, and the
   marker will never cover it because excluding the lobby is correct for the marker's own purpose.
   Filed as `#24-ch23lobbyresume`.

*(The derivation the drive confirms, restated:)*
P10 asked only *which guards fire*. It never asked **what happens when none of them do**, and the
answer is not "nothing". `do_victory_road_chapter` has exactly ONE quiet exit —
`if ch23_chapter_done(): return` (`victory_road.py:3361-3362`) — and this drive **measured
`ch23_chapter_done() == False` in the lobby**, because that predicate requires `_on_map(EG)`, the
OUTDOOR map, which the lobby is not. So: ten call sites all skip → no state changes → the chapter
still does not grade done → 3 attempts are consumed →
`raise BotModeError("Ch23 (Victory Road) failed after 3 attempts. ...")` (`:3486-3488`).
And `story_mode.py:5172-5173` calls the chapter whenever `ch23_chapter_done()` is False — which in
the lobby is ALWAYS. ⇒ **Inside its own League lobby the bot can neither finish §Ch23 nor skip it.**
This RAISES the priority of the §Ch24 marker from tidy-up to load-bearing.

**2. THE NINE-GUARD ENUMERATION WAS INCOMPLETE, AND IT WAS PUBLISHED.** See the mistakes log entry
of 2026-09-18. The tenth call site has no `LEG N` banner; leg 11's real condition is nested.
Correcting leg 11 **changed two control readings**: EVER_GRANDE degraded was published as legs
`5/10/11` and is actually **`5/10`**; basket-bought was published as `5/11` and is actually **`5`**.

**3. THE VACUITY ARM FOUND A BUG IN THIS DRIVER'S OWN GRADE.** With the premise refused, `post_flags`
was never populated, `.get(...)` returned `None`, `None is False` is False — and the driver printed
its single most alarming line, *"the guards were talked to, the north doors are now open FOREVER"*,
about a run that talked to nobody. **UNREAD is not READ-FALSE.** Fixed: three states, and an unread
now says so. ⇒ A vacuity arm is not only a test of the grade's premise; it is the arm that exercises
every diagnostic on the partial-state path.
