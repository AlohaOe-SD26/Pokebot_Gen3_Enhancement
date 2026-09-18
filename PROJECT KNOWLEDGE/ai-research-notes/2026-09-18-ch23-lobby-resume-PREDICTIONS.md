# `#24-ch23lobbyresume` — PREDICTIONS, FILED BEFORE THE PROBE (2026-09-18)

> ⛔ Written and **committed before the probe was written or executed** (`story-drive` §1).
> Anything the run contradicts is a **RESULT**, not a probe failure.

## THE QUESTION

**Does §Ch23 actually RAISE when re-entered from the League lobby — or is that still only a trace?**

`06-DECISIONS-LOG.md` already DERIVED the raise (*"all self-skip, three times, then raises ⇒ 4 derails
⇒ Manual"*). The 2026-09-18 lobby drive MEASURED its two inputs — all ten call sites False, and
`ch23_chapter_done()` False — but **never called the function.** ⇒ the consequence is still an
inference from two measured premises. This probe calls it.

## ⭐ WHY THIS IS SAFE, AND IT IS SAFE FOR A REASON WORTH STATING

With every guard False, `do_victory_road_chapter` **yields nothing**: the body runs the three-attempt
loop, every `if` is False, `ch23_chapter_done()` stays False, and it raises. ⇒ **a single `next()` on
the generator executes the whole body and consumes ZERO emulator frames.** The bot cannot move, so it
cannot wander into the gauntlet. This is the cheapest decisive test available.

⛔⛔ **AND THE CONTROL IS THE DANGEROUS HALF — IT IS GUARDED, NOT TRUSTED.**
The control runs the SAME call from an outdoor fixture to show the instrument can see a NON-raise.
But if `ch23_chapter_done()` is False there, the call would execute **leg 5 = `enter_victory_road`**
and walk the bot into the cave. ⇒ **the control MUST test `ch23_chapter_done()` FIRST and refuse to
call the chapter unless it is already True** (in which case the function returns at
`victory_road.py:3361-3362` having run nothing). A control that is not guarded this way must be
ABANDONED, not run.

## THE ARMS

| arm | fixture | expected |
|---|---|---|
| **TREATMENT** | `post_league_lobby.ss1` (LEAGUE_1F (3,4)) | `BotModeError` naming *"failed after 3 attempts"*, position UNCHANGED |
| **CONTROL** | `post_league_shop.ss1` (EVER_GRANDE, basket bought) — ⛔ only if `ch23_chapter_done()` is already True | returns cleanly, **no raise**, nothing run |
| **VACUITY** | `post_hall4_door.ss1` (HALL4, sealed) | ⚠ see P9 — I am NOT confident, and that is the point |

## PREDICTIONS

| # | reading | prediction | falsifier |
|---|---|---|---|
| P1 | premise | on `POKEMON_LEAGUE_1F (16,10)`, tile `(3,4)` | any other position ⇒ wrong fixture |
| P2 | `ch23_chapter_done()` BEFORE | **False** | True ⇒ the whole item dissolves; the chapter would return cleanly |
| P3 | the call | **raises `BotModeError`** | returns cleanly ⇒ ⭐ the derivation in `06-DECISIONS-LOG.md` is WRONG and `#24-ch23lobbyresume` must be withdrawn |
| P4 | message | contains **"failed after 3 attempts"** | a different error ⇒ something else raised first, and THAT is the real finding |
| P5 | message | contains **three** attempt clauses, each *"every leg ran but the chapter does not grade done"* | fewer ⇒ an attempt exited by a path I have not modelled |
| P6 | position AFTER the raise | **unchanged** — still `LEAGUE_1F (3,4)` | any movement ⇒ a leg DID run, and the ten-guard reading was wrong |
| P7 | frames consumed | **0** (the generator never yields) | any yield ⇒ a leg is doing work and the safety argument above is void |
| P8 | ⭐ **CONTINUE — `calculate_path` from (3,4) to the lobby's exit landing `(9,11)`** | **SUCCEEDS** | failure ⇒ the bot is *physically* stranded too, which would be a bigger and different finding |
| P9 | VACUITY on `post_hall4_door` | ⚠ **I PREDICT IT ALSO RAISES, and I am NOT confident** | ⇒ see below |
| P10 | CONTROL on `post_league_shop` | `ch23_chapter_done()` **True** ⇒ the call returns, **no raise**, no leg run | a raise ⇒ the instrument raises everywhere and proves nothing |

⭐⭐ **P8 IS THE POINT OF THE WHOLE ITEM, AND IT IS THE DISTINCTION THE DOCS CURRENTLY BLUR.**
If P8 succeeds while P3 raises, the precise characterisation is **"physically free, logically stuck"**:
the bot can walk anywhere it likes in the lobby and out the front door, but the *chapter dispatch*
cannot make progress from there and will burn its retry budget every pass. That is a different defect
from the §Ch15/§Ch18/§Ch19 "stranded" shape this project already knows, and it should not be described
with the same word.

⚠ **P9 IS THE ROW I EXPECT TO LEARN FROM.** `post_hall4_door` is a SEALED map. The ten guards are all
False there too (measured), so by the same reasoning it should raise identically — in which case this
is NOT a lobby-specific defect at all, but a **League-wide** one, and `#24-ch23lobbyresume`'s title is
too narrow. ⛔ If it raises there too, the item must be RE-SCOPED, not quietly kept.

## ⛔ WHAT THIS PROBE DOES NOT ESTABLISH

* **FREQUENCY.** Whether a real run ever re-enters §Ch23 from the lobby is a BATCH question
  (`CLAUDE.md` §9), and nothing here answers it. A measured raise is not a measured incident rate.
* **THE FIX.** This decides only whether the defect is real and how wide it is.

## HOW THIS GETS GRADED

A **GRADED** section is appended after the runs: every P row marked ✅ met, ❌ refuted, or ⚠ unreadable,
**with the literal output line beside it**. A row that cannot be quoted was not measured.
