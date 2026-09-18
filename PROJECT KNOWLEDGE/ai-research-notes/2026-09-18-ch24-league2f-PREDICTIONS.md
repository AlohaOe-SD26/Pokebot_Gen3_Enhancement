# `--driver ch24lobby2f` — PREDICTIONS, FILED BEFORE THE DRIVER EXISTS (2026-09-18)

> ⛔ Written and **committed before the driver was written or executed** (`story-drive` §1).
> Anything the run contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Close the last piece of the "lobby window is TWO maps" debt: READ League 2F.**
`03-PUNCH-LIST.md`, the lobby SPEC note and `07-CHANGELOG.md` have each logged that a 2F reading is
owed. Nothing in this repo has ever stood on `EVER_GRANDE_CITY_POKEMON_LEAGUE_2F (16,14)` — **0 of 60
pinned fixtures**, and its arrival tile has never been measured here.

## ✅ WHAT §0 RECON ALREADY SETTLED (measured, not assumed)

| fact | how |
|---|---|
| 2F is reachable from the lobby fixture | `calculate_path((L1F,(3,4)) -> (L1F,(1,7)))` returns **5 waypoints**: `(3,5) (3,6) (3,7) (2,7)` on `(16,10)`, then **`map=(16,14) coords=(1,6) is_warp=True`** |
| ⭐ the planner routes ACROSS the warp itself | that final waypoint is on a *different map* — so `_navigate_riding_out` to the escalator tile lands the bot on 2F without any hand-rolled press loop |
| the escalator is step-on, no button | `victory_road.py:410-412` (`MB_UP_ESCALATOR`, collision 0); decomp `field_control_avatar.c` fires `DoEscalatorWarp` on step completion |
| nothing gates it | League 1F has `coord_events: []` and `bg_events: []`; warp 4 `(1,7)` carries no flag. The gauntlet doors are warps **2/3** at `(9,1)/(10,1)` — **disjoint tiles, opposite corner** |
| 2F is the Cable Club | decomp `layout: LAYOUT_POKEMON_CENTER_2F`; Union Room / Trade Center attendants. ⛔ **NOT** the Champion corridor (that is HALL5→…→HALL4) and **NOT** the Hall of Fame (`(16,11)`) |
| standing on 2F still reads "inside the League" | `victory_road.py:1380` — 2F is in `LEAGUE_INTERIOR_MAPS`, which feeds `inside_league()` → `at_ever_grande_top()` |

⚠ **DECOMP-SOURCED AND UNVERIFIED HERE:** that the return warp is 2F `(1,6)` → 1F `(1,7)`, and that
`(1,6)` carries `MB_DOWN_ESCALATOR` specifically. **This drive measures the first and does not care
about the second.**

## ⛔ THE PATH GUARD MUST BE INVERTED FOR THIS LEG, AND THAT IS THE INTERESTING PART

`Ch24LobbyMode`'s rule is *"this leg never changes map ⇒ any warp is a refusal"*. **This leg's whole
purpose is to take a warp**, so that rule cannot be reused. ⇒ the invariant becomes:

> **exactly ONE warp waypoint, and its destination map is `LEAGUE_2F (16,14)`; no waypoint may land on
> any `CH24_SEALED` map, and no waypoint may touch `(9,1) (10,1) (9,2) (10,2)`.**

⭐ **AND IT KEEPS THE SELF-TEST, POINTED THE OTHER WAY.** `#24-pathguardblind` was caught precisely
because a guard was never shown to *see* anything. So before trusting this one, the leg vets a route
it must REFUSE — the route to a **sealed** map — and refuses the whole leg if that comes back clean.

## THE ARMS

| arm | fixture / env | expected |
|---|---|---|
| **TREATMENT** | `post_league_lobby.ss1`, `CH24_2F_CAPTURE=post_league_2f` | `PASS`, 2F read, fixture minted, **returned to 1F** |
| **VACUITY** | `post_hall4_door.ss1` (already inside, wrong map) | refuse at the premise, **zero readings** |
| **FAULT `NORETURN`** | `POKEBOT_CH24_FAULT_NORETURN=1` | ends on 2F; `L2-RETURN` MISSING, `ACCEPTANCE: FAIL` |
| **FAULT `BLINDGUARD2F`** | `POKEBOT_CH24_FAULT_BLINDGUARD2F=1` | the guard's self-test must fire and the leg must walk **nothing** |

## PREDICTIONS

| # | reading | prediction | falsifier |
|---|---|---|---|
| P1 | premise | `POKEMON_LEAGUE_1F (16,10)` tile `(3,4)` | anything else ⇒ wrong fixture |
| P2 | planned route | exactly **one** `is_warp` waypoint, destination map `(16,14)`, no forbidden tile | ⇒ ⛔ REFUSE TO WALK |
| P3 | guard self-test | a route to a SEALED map is **refused** (or unreachable) | clean ⇒ the guard is blind; refuse the leg |
| P4 | after the walk | on `EVER_GRANDE_CITY_POKEMON_LEAGUE_2F (16,14)` | still on 1F ⇒ the escalator did not fire on step |
| P5 | ⭐ arrival tile | **`(1,6)`** — the decomp's reciprocal warp, **never measured in our emulator before** | any other tile ⇒ a genuinely new fact, and the decomp table is not our ground truth |
| P6 | `battles` / `whiteouts` | **0 / 0** | any battle ⇒ we crossed something we should not have |
| P7 | `ENTERED_ELITE_FOUR` on 2F | **still False** | True ⇒ something talked; the excursion is not flag-neutral |
| P8 | 2F predicates | `inside_league=True`, `at_ever_grande_top=True`, `ch23_chapter_done=False` | `at_ever_grande_top=False` ⇒ `LEAGUE_INTERIOR_MAPS` does not cover 2F in practice |
| P9 | ⭐ ten §Ch23 call sites on 2F | **ZERO fire** | any firing ⇒ §Ch23 acts on the Cable Club floor, which would be a new and worse finding than the lobby one |
| P10 | ⭐⭐ `do_victory_road_chapter()` called on 2F *(guarded: only if all ten guards are False)* | **raises `BotModeError` "failed after 3 attempts"**, `frames consumed = 0`, nothing moves | returns cleanly ⇒ the LEAGUE-WIDE claim in `#24-ch23lobbyresume` is **too broad** and must be narrowed again |
| P11 | ⭐ return | `calculate_path` routes 2F → `LEAGUE_1F (3,4)` and the walk **arrives** | no path ⇒ 2F is a ONE-WAY POCKET, which would make every earlier "benign, 2F warps straight back" note WRONG |
| P12 | capture | `post_league_2f.ss1` written and pinned | refused ⇒ read the guard, not the driver |

⚠⚠ **P11 IS THE ONE THAT MATTERS MOST AND THE ONE I AM LEAST SURE OF.** Our own code calls the
escalator *"benign (2F warps straight back)"* (`victory_road.py:410-411`) — but that sentence has
**never been executed by anything in this repo**, and the same file's neighbouring comment about guard
positions was already found to be template-sourced rather than measured. If P11 fails, a bot that
fat-fingers one step onto `(1,7)` is stranded in a room with **`allow_escaping: false`** and no Dig,
Teleport or Escape Rope — and that would be a live production hazard, not a documentation gap.

⚠ **P10 IS DELIBERATELY GUARDED.** The chapter is called ONLY if all ten guards read False, because
with any guard True the call would *execute a leg* and walk the bot somewhere unplanned. The guard is
the same one `probe_ch23_lobby_resume.py` uses, and for the same reason.

## ⛔ WHAT THIS WILL NOT ESTABLISH

* **The metatile behaviour of `(1,6)`.** Whether it is specifically `MB_DOWN_ESCALATOR` is not
  measured; only whether the return *works*.
* **Frequency.** Nothing here says a real run ever steps on `(1,7)`. Still a batch question.
* **The post-talk window.** This whole drive is on the no-talk, positionally-sealed lineage.

## HOW THIS GETS GRADED

A **GRADED** section is appended after the runs: every P row ✅ met, ❌ refuted or ⚠ unreadable, **with
the literal log line beside it**. A row that cannot be quoted was not measured.
