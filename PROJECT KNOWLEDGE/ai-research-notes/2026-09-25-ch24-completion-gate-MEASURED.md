# §Ch24's COMPLETION GATE — why the two flags are NOT enough (MEASURED)

**Date:** 2026-09-25. **Item:** `ch24_chapter_done()` + the `_play` dispatch.

## THE QUESTION

`run_the_gauntlet` already asserts `IS_CHAMPION ∧ SYS_GAME_CLEAR` as its own final check, and that
has passed in a real drive. So: is that conjunction enough for the **GATE** that decides whether
`_play` may skip §Ch24?

## ⛔ THE DECOMP SAID NO — AND THEN A DRIVE PROVED IT

Read directly (`gh api repos/pret/pokeemerald/contents/data/scripts/hall_of_fame.inc`):

```
EverGrandeCity_HallOfFame_EventScript_SetGameClearFlags::
	special SetChampionSaveWarp
	setflag FLAG_IS_CHAMPION
```

`FLAG_IS_CHAMPION` is set **inside the Hall of Fame script**, and `FLAG_SYS_GAME_CLEAR` a few
instructions later via `special GameClear` (`src/post_battle_event_funcs.c`) — **both BEFORE the
credits and BEFORE `SoftReset(RESET_ALL)`.**

## ⭐⭐ THE ARM THAT SETTLED IT (one drive, both predicates, two instants)

`CH24_CHAMP_FROM=drake --driver ch24champion` from `post_drake_L75.ss1`, instrumented to evaluate
BOTH predicates at the instant the flags flip AND at the end of the chapter:

| sampled at | `flags_only` | `gated` | map / tile |
|---|---|---|---|
| **the INSTANT the flags flip** | **`True`** | **`False`** | `(16,11)` `(7,5)` = **`EVER_GRANDE_CITY_HALL_OF_FAME`** |
| the end of the chapter | `True` | `True` | `(1,1)` `(4,2)` = the bedroom |

⇒ **THE TWO PREDICATES DISAGREE, AND THEY DISAGREE IN THE HALL OF FAME.** A flags-only gate would
declare §Ch24 finished while the bot is still standing in it, with the credits and a SoftReset
still ahead. The `not-on-endgame-maps` conjunct is the one doing the work.
‼ This is the project's own currency rule honoured: *"a claim of the form 'without X the bug
survives' is a CLAIM, and the only currency is an arm with X removed."* This is that arm.

## ⚠ AND THE FIRST VERSION OF THIS ARM WAS IN THE WRONG PLACE — THE READING SAID SO

The first attempt put the probe beside `_take(report, "C-CLEARED")`, believing that was the moment
the flags flip. It is not: `_endgame_done` waits for `cleared` **AND** `rebooted`, so that `_take`
runs AFTER the SoftReset. That run reported `flags_only: False` at `at: ((0, 0), (-7, -7))` — a
NONSENSE COORDINATE, sampled mid-EWRAM-reload where RAM is garbage by construction.
⇒ it produced **no disagreement**, and for a while I had an unproven claim and a passing drive.
⭐ **The impossible coordinate is what exposed it** — the same way a negative duration exposed the
`intro_true_frames` bug earlier this session. Derived values that cannot be are worth printing.

## THE GATE, AS BUILT

`IS_CHAMPION` ∧ `SYS_GAME_CLEAR` ∧ NOT-on-(Champion's room, Hall of Fame) ∧ a NON-EMPTY PARTY.
⛔ **A `GameState.OVERWORLD` CONJUNCT WAS WRITTEN AND THEN REMOVED.** It discriminates nothing
here and creates a false-negative — the post-game bot is in battle constantly while dex
hunting. The ruling was *"neither a bare flash read nor a SINGLE OVERWORLD conjunct"*, which
forbids relying on it ALONE; it never required including it. RAM, never flash (RAM and flash disagree on all five §Ch24 fixtures — measured).
No position conjunct beyond the exclusion: §Ch24's end position is the bedroom and is TRANSIENT, so
requiring it would flip False the moment the post-game took a step.

## ⛔ THE SHORT-CIRCUIT'S PREMISE — MY FIRST ONE WAS REFUTED

I justified skipping §Ch24 on a cleared save as *"otherwise §Ch23 re-runs and re-buys the Elite
Four basket"*. **That is false.** `ch23_chapter_done()` already returns True forever once
`IS_CHAMPION` is set (`victory_road.py`, fixed 2026-09-24 under `#24-markerwinstate` — *"Success
was the failure case"*). Found by an adversarial review reading the current tree.
⇒ **THE REAL REASON:** nothing stops `train_for_league()` from re-running on a cleared save, and
the §Ch24 party carries mon under the L65 floor (`Zigzagoon L19`, `Castform L36`). Without the gate
a FINISHED game re-entering `_play` would start GRINDING FOR HOURS and then walk into a gauntlet it
had already won.

## ✅ AND THE DISPATCH ITSELF IS DRIVEN (the Tier 1 blocker, closed)

A reviewer refused the first submission on exactly the right grounds: the evidence proved the
PREDICATE (`ch24champion` driver) and never executed the new `if/else` + `_guard` inside
production `_play()`. ⇒ a CLEARED-GAME fixture was minted — `post_hof_cleared.ss1`, the repo's
first, `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)`, badges=12345678, party at 100% — and
`--driver storyresume` (a real `StoryMode()` on the loaded save) was pointed at it:

```
Story: Mt. Chimney already cleared — skipping.
Story: Victory Road already done — skipping.
Story: §Ch24 already done — the game is CLEARED. Skipping.
Story: THE GAME IS CLEARED (Ch24) - ... NEXT (WIP): POKEDEX HUNTING
```

Zero tracebacks, zero `BotModeError`. ⇒ the short-circuit, the `_guard` (it did not raise — the
banner is downstream of it) and the retargeted banner all execute in production.
✅ A risk I flagged in advance did NOT materialise: resuming from a cleared game **in
Littleroot**, where the story begins, did not confuse `_play` — every earlier segment
self-skipped on flags rather than position.

## ⛔⛔ WHAT IS **NOT** PROVEN BY ANY OF THIS

**USER RULING 11 is NOT met.** Everything above is a harness driver from a PINNED FIXTURE. Ruling 11
is *"Hall of Fame from a REAL story run, no fixture, at ×1"* — a full playthrough, hours long and
unattended. The CODE GAP is now closed; the PROOF is not. ⇒ the next action is that run, and it is
the user's to start, not something a drive from a save state can substitute for.
