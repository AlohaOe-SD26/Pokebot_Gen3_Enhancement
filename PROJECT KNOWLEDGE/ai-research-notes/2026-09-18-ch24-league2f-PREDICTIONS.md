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


---

# ⭐ GRADED — 2026-09-18, AFTER THE RUNS

> Evidence: `tools/story-dev/evidence/2026-09-18-ch24lobby2f-*.txt` · fixture `post_league_2f.ss1` pinned `d3c09e7af34922d28dacbf927fb7b6bc`.
> Every row carries the literal log line. A row that cannot be quoted was not measured.

| # | verdict | the line it is graded on |
|---|---|---|
| P1 | ✅ MET | `PRE at=((16, 10), (3, 4)) tile=(3, 4)` |
| P2 | ✅ MET | `PATH SAFE — 5 waypoints, exactly one warp, to EVER_GRANDE_CITY_POKEMON_LEAGUE_2F. path=[((16, 10), (3, 5), False), …, ((16, 14), (1, 6), True)]` |
| P3 | ✅ MET — ⚠ **against a CHANGED design; see “A DESIGN DEVIATION” below before quoting this row** | `GUARD SELF-TEST OK — all 3 synthetic hazards refused (['gauntlet-door waypoint', 'sealed-room waypoint', 'second warp elsewhere'])` |
| P4 | ✅ MET | `⭐ ON LEAGUE 2F — at=((16, 14), (1, 6))` |
| P5 | ⭐ **MET — AND IT SPLIT INTO TWO TILES, WHICH IS A BETTER ANSWER THAN THE ONE PREDICTED** | delivered: `at=((16, 14), (1, 6))`; then `‼ SETTLED (1, 6) -> (2, 6) before capture`. **The decomp's reciprocal warp (1,6) is CONFIRMED by measurement** — and the avatar then auto-completes a step, so the RESTING tile is `(2,6)`. Both are true; conflating them is the trap. |
| P6 | ✅ MET | `RESULT battles=0 whiteouts=0 failure=None` |
| P7 | ✅ MET | `CAPTURE GUARD on_2f=True battles=0 entered_e4_still_False=True` |
| P8 | ✅ MET | `PREDICATES {'inside_league': True, 'at_ever_grande_top': True, 'ch23_chapter_done': False, 'wally_beaten': True}` |
| P9 | ⭐ MET | `⭐ LEG GUARDS ON 2F: fire=NONE all={'1-3': False, '4': False, '4b-train': False, '5': False, '6': False, '7': False, '8': False, '9': False, '10': False, '11': False}` |
| P10 | ⭐⭐ MET | `⭐⭐ CH23 CALLED ON 2F -> BotModeError: Ch23 (Victory Road) failed after 3 attempts… frames=0 moved=False` ⇒ `#24-ch23lobbyresume`'s **LEAGUE-WIDE** claim now holds on the Cable Club floor too, measured on a third map |
| P11 | ⭐ **MET — BUT ONLY AFTER TWO DRIVER BUGS, AND THE FIRST ONE ALMOST BECAME A FALSE FINDING** | `⭐ BACK ON 1F at=((16, 10), (1, 7)) tile=(1, 7)` then `⭐ RETURNED — at=((16, 10), (3, 4))`. See below. |
| P12 | ✅ MET | `✅ CAPTURED -> post_league_2f.ss1 (397312 bytes) at ((16, 14), (2, 6))`; pinned and re-verified by RELOAD in `probe_ch23_leg_guards.py`, which reports `EVER_GRANDE_CITY_POKEMON_LEAGUE_2F (2, 6)` |

## ⭐⭐ THE HEADLINE: THE ESCALATOR ROUND TRIP IS CLOSED, AND THAT SENTENCE IS NOW *EXECUTED*

`victory_road.py:410-411` has called the escalator *"benign (2F warps straight back)"* since it was
written, and **nothing in this repo had ever run it.** It is now measured in both directions:
`(3,4) → (1,7)` warps to 2F `(1,6)`; stepping back onto `(1,6)` returns to 1F `(1,7)`; the leg then
walks home to `(3,4)`. ⇒ a stray step on the escalator is **recoverable**, not a strand.
⚠ Still true and still worth knowing: 2F is `"allow_escaping": false` — no Dig, Teleport or Escape
Rope. The escalator is the ONLY way out. It just happens to work.

## ⛔⛔ P11's TWO DRIVER BUGS — BOTH WOULD HAVE BLAMED THE GAME

**BUG 1 — A MALFORMED QUESTION THAT LOOKED LIKE A ONE-WAY POCKET.** v1 asked
`calculate_path((L2F,(1,6)) -> (L1F,(3,4)))` and got
*"are not on connected maps (note that warps don't count.)"*. ⭐ **`calculate_path` plans within
CONNECTED maps and a WARP IS NOT A CONNECTION.** The inbound leg works only because BOTH its
endpoints are declared on 1F — `(L1F,(3,4)) -> (L1F,(1,7))` — and the warp is incidental to the final
step, which is why that path's last waypoint comes back already on 2F.
‼ My own predictions file said a failure here would mean *"2F is a ONE-WAY POCKET"*. **It would not
have.** It meant the request was the wrong shape. ⇒ the fix is to express each segment on ONE map and
step ONTO the warp tile.

**BUG 2 — AIMED AT THE SETTLED TILE INSTEAD OF THE DELIVERED ONE.** Once a pre-capture settle was
added, the return read the CURRENT tile `(2,6)` as the warp tile, stepped onto an ordinary floor tile,
did not warp, and raised a message reading *"If the tile the escalator DELIVERED us to does not send
us back, `victory_road.py:410-411` is wrong."* ⛔ **That message was wrong about the game and right
about the run.** The leg now targets the RECORDED arrival tile and its failure message names which
tile it actually stepped on, so the next reader checks the leg before blaming the game.

## ⚠ A DESIGN DEVIATION BETWEEN THE PREDICTIONS AND THE IMPLEMENTATION — DECLARED, NOT BURIED

P3 was pre-registered as *“a route to a SEALED map is refused **(or unreachable)**”*. The
implementation does NOT do that: it injects **synthetic waypoints into a copy of the real path**.
⇒ **the parenthetical was the problem.** `calculate_path` to `(9,1)` is genuinely unreachable from the
lobby (the door guards block it), so that arm would have passed **for the wrong reason** on every run
— a self-test that cannot fail is the exact shape `#24-pathguardblind` was about. The synthetic
version CAN fail, and the `BLINDGUARD2F` arm proves it does.
‼ Recorded because grading P3 ✅ without saying the design changed would be scoring a prediction
against a different experiment.

## ⭐ TWO REUSABLE FACTS THIS DRIVE ESTABLISHED

1. **`calculate_path` does not route through warps for a cross-map request.** Express cross-map
   travel as per-map segments that step onto the warp tile. (This is why production uses
   `_walk_through_warp` and per-map navigation rather than one long plan.)
2. **A save taken while a step is IN FLIGHT resumes by COMPLETING that step.** Measured: capture
   logged `(1,6)`, reload rested at `(2,6)`, with the change occurring between frames 10 and 20 and
   stable to 600. ⇒ the capture line's tile is NOT the fixture's resting tile. **This is exactly why
   this project verifies a fixture by RELOAD and never by the capture line** — the rule earned its
   keep the first time it was tested here. The capture now settles before writing.

## ⛔ WHAT THIS STILL DOES NOT ESTABLISH

* **The metatile behaviour of `(1,6)`** — only that the return WORKS, not that it is specifically
  `MB_DOWN_ESCALATOR`.
* **Frequency** — nothing says a real run ever steps on `(1,7)`. Still a batch question.
* **The post-talk window** — this whole drive is on the no-talk, positionally-sealed lineage, and a
  post-talk sibling fixture is still owed.
