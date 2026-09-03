# §Ch22 CHAPTER DRIVE — PREDICTIONS, FILED BEFORE THE ORCHESTRATOR IS WRITTEN

> ⛔ **THIS FILE IS COMMITTED BEFORE A SINGLE LINE OF `do_sootopolis_gym_chapter()` EXISTS.**
> That is the point: a prediction filed after the run is a rationalisation. Grade the composed
> drive against this file, and record every miss — the misses are the measurements.
> Fixture: `post_hm07.ss1` (md5 `bc3686118ac70a9aa1aa6501618adbac`), driver `--driver ch22chapter`.

## ⭐ THE ONE PREDICTION THIS DRIVE EXISTS TO TEST

**P7 — B1F COSTS *ZERO* TRAINER BATTLES AFTER THE BADGE.**

This is a **discriminator**, and the two arms genuinely differ:
* If the decomp read is right (`SootopolisCity_Gym_1F_EventScript_JuanDefeated` runs
  `setvar VAR_0x8008, 8` + `call Common_EventScript_SetGymTrainers`, which `settrainerflag`s all
  ten B1F trainers) ⇒ **`battles_on_b1f == 0`.**
* If it is wrong ⇒ **`battles_on_b1f == 3`** (Bethany, Andrea, Connie — the exact tiles
  `--driver ch22exit` already measured at `badge8=False`: (8,8), (8,17), (8,19)).

⇒ **0 versus 3 is unmissable, and the run cannot produce both.** ‼ A `3` here refutes the finding
that deleted a whole planned XP leg, and the chapter must then be re-ordered. That is why this
number is the acceptance line and not a footnote.

## THE REST, IN ORDER

| # | prediction | confidence | what a miss would mean |
|---|---|---|---|
| P1 | The Sootopolis Poké Center heal succeeds and **the party is still SIX** afterwards, with Surf and Dive on the same PIDs | ⚠ **LOW — this is the second-riskiest line here** | `heal_in_pokemon_center` calls `deposit_dead_weight_if_worth_it()`, and `DEAD_WEIGHT_LEVEL_GAP = 8` makes Swellow (L41) and Zigzagoon (L19) eligible against Sceptile L50. Zigzagoon is **not** HM-exempt (Wailmer shares Surf). A 5- or 4-mon party going into the gym is a REAL outcome, not a bug — and the leg must assert count + HMs by PID either way |
| P2 | The ice walk reproduces exactly: `steps=64`, sections `(1,7,(8,17),9) (2,19,(8,12),29) (3,38,(8,6),68)`, `end_tile=(8,6)` | HIGH — measured twice | the table or the floor model moved |
| P3 | The 3-step climb reaches `JUAN_STAND (8,3)` | HIGH | the stairs did not open |
| P4 | **Juan is WON**, 5/6 survivors, **Swellow is the one that faints** | HIGH on the win (4/4), MEDIUM on 5/6, MEDIUM-HIGH on *which* mon | ‼ **This is an INDEPENDENT 5th sample**: the composed run reaches the fight after a heal and a different navigation, so `gRngValue` at battle start differs from all four existing arms. A LOSS is a RESULT, not a defect — it would make the sample 4/5 and force the chapter to own a loss branch |
| P5 | The descent `(8,3) → (8,5)` works, because `(8,4)` and `(8,5)` read `OPEN_STAIRS 0x207` once the puzzle is complete | ⚠ **LOW-MEDIUM — THE RISKIEST MECHANICAL LINE.** ⛔ **NOBODY HAS EVER READ THOSE TWO METATILES AFTER THE PUZZLE COMPLETES.** The 0x207 value comes from the decomp (`METATILE_SootopolisGym_Stairs`, `MB_NORMAL`), not from a live read | if they still read `LOCKED_STAIRS 0x20F` (`MB_SLIDE_SOUTH`), stepping south **slides the bot back onto the cracked ice and falls it early**, from the wrong tile. ⇒ the descent MUST re-read the live metatile grid before each step and refuse, exactly as `_climb_to` does |
| P6 | The fall at `(8,6)` lands on **B1F `(8,6)`** — `warphole` preserves (x,y) | HIGH — measured | — |
| P8 | The B1F walk is 19 steps to the ladder `(11,22)`, then 1F, then out to `SOOTOPOLIS_CITY` | HIGH — measured | — |
| P9 | `can_continue`: a real `calculate_path` from the end tile to the Poké Center **apron (43,32)** returns an int | HIGH | §Ch15/18/19 each PASSED stranded; this conjunct is why |
| P10 | Total **35,000–50,000 frames** | MEDIUM | ⛔ **It must be well UNDER `ch22exit` + `ch22juan` = 52,880**, because the composed chapter walks the ice **once**, not twice. A total near 53,000 means the orchestrator is re-walking it |

## ⛔ AND ONE THING THAT IS NOT A PREDICTION BUT A PRECONDITION

**`_descend_to` DOES NOT EXIST YET.** Until it is written, a composed drive **cannot reach P6** — it
will stop at the new southward refusal in `_climb_to`:
> *"Ch22: `_climb_to` walks NORTH only, and (8,5) is SOUTH of (8,3) (y increases southward).
> Refusing rather than pressing 'Up' away from the target."*
✅ **That refusal firing is the guard WORKING, not the drive failing** — it is the whole reason the
guard was added before any composed run, and it is that guard's first live exercise. Grade it as:
*named, instant, bounded, and it names the missing helper.* The defect shape would be the OLD
behaviour: 2,700 frames of pressing "Up" into Juan's body, then an error blaming the step budget.

## WHAT IS DELIBERATELY *NOT* PREDICTED (report it, do not grade it)

* **Which of our mons does the work against Juan**, and how much HP the survivors keep. The four
  existing arms disagree wildly (Sceptile ended 141/141 twice and **32/141** once), so this is
  measured, never asserted.
* **Whether the PokéNav Match Call from `FLAG_ENABLE_JUAN_MATCH_CALL` fires on the way out.** It
  becomes possible the instant the badge is won and has never been observed here.
* **The Mart.** The stocking leg is optional and is not in this drive at all.

## THE ACCEPTANCE LINE

`ACCEPTANCE: PASS` requires **all** of: `BADGE08_GET` **and** on `SOOTOPOLIS_CITY` **and** an
integer `can_continue` **and** `whiteouts == 0` **and** `ice_steps == 64` **and**
`battles_on_b1f == 0`.
⛔ **`juan_defeated()` alone is NOT the grade** — it is True while the bot is stranded on the
20-tile island, which is the §Ch15/§Ch18/§Ch19 failure shape verbatim.
