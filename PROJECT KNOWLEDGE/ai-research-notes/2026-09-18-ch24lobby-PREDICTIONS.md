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
