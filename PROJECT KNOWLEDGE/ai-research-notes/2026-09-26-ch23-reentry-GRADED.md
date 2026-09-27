# 2026-09-26 — §Ch23 leg-5 RE-ENTRY from the League plateau — GRADED: BOTH ARMS AS PREDICTED; REVIEW KICK-BACK FIXED (C5)

> Grades `2026-09-26-ch23-reentry-PREDICTIONS.md` (committed `ac3f72c9` BEFORE the live drives; its C5 addendum `e9a3b74b`
> BEFORE C5 was run). Evidence, committed:
> `tools/story-dev/evidence/2026-09-26-ch23reentry-{A1-FIX,A2-REENTRY}.txt` (+ `.stdout.txt`).
> ⚠ **A TYPO IN THE PREDICTIONS, CORRECTED HERE (not by rewriting them):** they give `post_league_heal`'s md5 prefix as
> `1a8a0269b42d`; the pin (`saves/FIXTURES.md5`) and the file are `1a8a0269b42900dd98897a41d964c1e3`. A first
> `verify_fixtures --assert` with the typo printed MISMATCH; re-asserted with the correct prefix: `OK`. Both drives ran on
> the pinned bytes.

| arm | prediction | reading | verdict |
|---|---|---|---|
| **A1 FIX** (`post_league_heal`, plateau (18,6), Wally beaten, basket empty) | PASS; leg 5 skipped; leg 11 buys the basket | `ACCEPTANCE: PASS` — `done=True on_ever_grande=True inside_victory_road=False` at (18,6), `battles=0 whiteouts=0`, 4,915 frames. `ch23_chapter_done()` requires the full `LEAGUE_BASKET` (`victory_road.py`, its `return not any(stock… < qty …)`) and the fixture started with none ⇒ leg 11 bought it | ✅ |
| **A2 REENTRY** (old guard) | FAIL — leg 5 fires at (18,42), unreachable | `ACCEPTANCE: FAIL` — `Ch23 (Victory Road) failed after 3 attempts. attempt 1: UnreachableDestinationError: Could not reach (18, 42) on MapRSE.EVER_GRANDE_CITY: the field is idle and we are still at (18, 6)` | ✅ the defect was real and the fix is load-bearing |
| **G** `probe_ch23_leg5_reentry.py` (ROM) | — (run before the predictions were committed; see their header) | PASS: `post_league_heal` / `post_ch24_atdoor` / `post_league_shop` (plateau) skip, the arm fires there; `ki90_whiteout_at_evergrande` (Wally beaten, SOUTH PC (27,49)) and `post_ever_grande` (18,42) still fire | ✅ incl. the case `wally_beaten()` alone would get wrong |
| **C5** (`POKEBOT_CH23_FAULT_PLATEAUREAD`: the position read raises) | `(False, True)` on each plateau fixture, nothing escapes | exactly: `[CH23] on_league_plateau: position/path unreadable (RuntimeError …) — treating as NOT on the plateau` ×3 fixtures, `(plateau, leg5) = (False, True)` | ✅ fails toward the old guard, never a crash |

## CODE REVIEW (adversarial `reviewer`) — KICK-BACK, FIXED

* BLOCKER: `on_league_plateau()` caught only `PathFindingError`; `get_player_location()` documents a plain `RuntimeError`
  on a corrupt read mid map change, which neither the attempt loop (`BotModeError`) nor `StoryMode.run()` catches — a
  guard that could crash, where the old guard (flags + position) could not. FIXED: any other exception ⇒ "not proven on
  the plateau" ⇒ leg 5 fires as before (story aborts still re-raise; a printed line); DRIVEN as C5.
* BLOCKER (docs): 07/08/06 entries — held for the review's outcome; they land with the code.
* Verified by the reviewer: `EverGrandeCity/map.json` has `"object_events": []` (the decomp), so `KI-103` cannot fake a
  "no path" here; the guard's cost is negligible (≤3 calls per chapter run); the south re-entry after a mid-leg-9
  failure re-fires leg 5 exactly as before (pre-existing, not introduced).

## THE LIVE BATCH SAYS THIS PATH IS REAL (interim read, 2026-09-26 ~17:30, main's code)
All five runs refused on money at leg 11 then burned derails #2-#5 on `Could not reach (18, 42) … still at (18, 6)` —
this exact defect, downstream of the money refusal. With the fix those re-entries go on to legs 10-11 (which refuse on
money again by name while money is short; RULINGS 16-18 attack the money itself).

## WHAT THIS SETTLES
* A re-entry of §Ch23 on the League plateau (after a refusal, a transient failure, or a lost `_ch24_owns_run` latch)
  now goes on to legs 10-11 instead of raising three times at an unreachable apron.
* The leg-5 guard is ONE named predicate (`leg5_should_fire`), read by the dispatch AND by
  `probe_ch23_leg_guards.py` — the hand copy the recon flagged is gone.

## WHAT IT DOES NOT SETTLE
* The Victory Road EXIT side has the same guard pattern (recon §4 "related holes"); its target was not measured.
* Whether real runs hit this path often — it needs a re-entry on the plateau; the batch's logs will show it.
