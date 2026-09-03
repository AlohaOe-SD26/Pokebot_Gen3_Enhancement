# §Ch22 CHAPTER DRIVE — RESULTS, GRADED AGAINST THE PRE-REGISTERED PREDICTIONS

> ‼ **THIS FILE IS MEASUREMENT, NOT RECALL.** Graded against
> `2026-09-03-ch22-CHAPTER-PREDICTIONS.md`, which was **committed before a single line of
> `do_sootopolis_gym_chapter()` existed** (commit `f372a780`). Driver `--driver ch22chapter`,
> fixture `post_hm07.ss1`.

---

## ⭐ THE HEADLINE: THE PREDICTION I RATED **HIGH** IS THE ONE THAT MISSED — **JUAN WAS LOST**

```
[ch22chapter] RESULT badge8=False at=SOOTOPOLIS_CITY(43, 32) city_state=5 ice_steps=64
              end_tile=(8, 6) b1f_steps=None whiteouts=1 frames=35645
[ch22chapter] BATTLES ['SOOTOPOLIS_CITY_GYM_1F(8, 3)'] outcomes=['BattleOutcome.Lost']
```

**P4 predicted a WIN at HIGH confidence, on a 4-of-4 sample. The composed run lost.**

⭐ **THE RUNNING TALLY: 6 DISTINCT DRAWS, 5 WINS, 1 LOSS.**

| draw | how it was reached | outcome |
|---|---|---|
| `ch22juan` control / j181 / j1013 / j47 | straight to the gym, four different RNG states | **Won** ×4 |
| `ch22chapter` drive 1+2, first fight | after a Poké Center heal + a longer navigation | **Lost** *(drives 1 and 2 are the SAME trajectory replayed — one draw, not two)* |
| `ch22chapter` drive 2, second fight | after a whiteout, a re-entry and a fresh ice walk | **Won** |

‼ **The proof that the chapter run is a genuinely different draw is the OUTCOME ITSELF**, not an
argument about frame counts: same fixture, same party, same production fight code — and a different
result. Only the RNG state at battle start can account for that.

‼ **And this is only valuable because the prediction was filed first.** A loss recorded after an
unrecorded expectation is a shrug; a loss against a written HIGH-confidence prediction changes what
may be claimed:

* ✅ **"the party CAN win Juan"** — measured, five times.
* ⛔ **"the party wins Juan reliably"** — **MEASURED FALSE.** ~5-in-6 on the draws in hand, and no
  document may round that to "wins".
* ⇒ **the chapter MUST own a loss branch, and drive 2 proves it does** (below).

---

## ⭐⭐ DRIVE 2: THE CHAPTER COMPLETED — BY LOSING, RECOVERING, AND WINNING THE SECOND TIME

```
[ch22chapter] RNG 0xfba6a834 -> 0xfba6a834 after 0 idle frames
[ch22chapter] !! WHITEOUT #1 - replaying what StoryMode.run does: clear the abort latch,
              leave the Poke Center, re-enter the chapter.
[ch22chapter] RESULT badge8=True at=SOOTOPOLIS_CITY(31, 33) city_state=6 ice_steps=128
              end_tile=(8, 3) b1f_steps=19 whiteouts=1 frames=64563
[ch22chapter] P7 DISCRIMINATOR - b1f_entered=True (b1f_steps=19) battles_on_B1F=0
[ch22chapter] BATTLES [GYM_1F(8,3), GYM_1F(8,3)] outcomes=['BattleOutcome.Lost','BattleOutcome.Won']
[ch22chapter] CONTINUE path to the Poke Center apron (43,32) = 23
[ch22chapter] RECOVERIES 1
```

**Three things this settles that nothing before it could:**

1. ⭐⭐ **P7 IS CONFIRMED, AND NON-VACUOUSLY: `b1f_entered=True`, `b1f_steps=19`,
   `battles_on_B1F=0`.** The post-badge descent really does cost **zero** trainer battles — the
   decomp read (`setvar VAR_0x8008, 8` + `Common_EventScript_SetGymTrainers` → all ten
   `settrainerflag`s) is now validated by a live run that walked the whole floor. ‼ Compare drive
   1, which printed the *same* `0` while never setting foot on B1F: **the number is identical and
   only one of them means anything.** That is why the grade now demands `b1f_entered` beside it.
2. ✅ **THE LOSS BRANCH WORKS, AND IT IS DRIVEN, NOT ASSERTED.** The run lost Juan, cleared the
   abort latch, walked out of the Poké Center, re-entered the gym, walked **virgin ice** (the
   puzzle reset, as measured), fought again and won. `RECOVERIES 1`.
   ⇒ the production path (`StoryAbort` → `StoryMode.run` → re-enter `_play()`) is exercised, not
   argued.
3. ✅ **THE CHAPTER ENDS OUTSIDE THE GYM WITH A REAL WAY ONWARD** — `SOOTOPOLIS_CITY (31,33)`,
   `CONTINUE = 23` waypoints to the Poké Center apron. Not the length-0 non-answer drive 1 gave.

⚠ **AND DRIVE 2 RE-PROVED DETERMINISM ON THE WAY:** `RNG 0xfba6a834 -> 0xfba6a834` at jitter 0,
and it lost the first fight **exactly as drive 1 did**. Same save, same code, same trajectory. The
`ch22chapter` sample is therefore **one draw, replayed** — the 4W/1L figure comes from the
`ch22juan` arms plus this one distinct chapter trajectory, and further chapter samples need the
jitter knob.

⚠ **Which mon faints is NOT stable.** All four `ch22juan` arms lost **Swellow**; this run lost
**Wailmer** (0/160) and Swellow survived at 5/118, having levelled to 42. ⇒ do not build anything
that assumes a particular casualty.

## ⛔⛔ DRIVE 3 (JITTERED): A **DIFFERENT** FAILURE — AND IT IS NOT A §Ch22 DEFECT

`POKEBOT_CH22JUAN_JITTER=181`. ✅ The knob perturbed (`RNG 0xfba6a834 -> 0x48d1a2db`), so this is a
third distinct trajectory. It died in the Juan fight:

```
f19485: SAVED stall state #3 to stalls/repro-ml-f19485.ss1 (bt='What will SCEPTILE do?')
f21520: *** BotModeError -> Manual: KI-47: battle sub-handler 'handle_battle_action_selection'
        ran 3001 frames with no battle progress (frozen at ('BattleScript_MoveEnd',
        'HandleTurnActionSelectionState', 'LearnMoveState.DialogueNotActive', 398269))
```
Stuck in `PARTY_MENU` on *"What will SCEPTILE do?"*.

* ✅ **THE KI-47 NET DID ITS JOB** — bounded at 3,001 frames, named its own sub-handler, no hang.
* ⛔ **AND THE RUN STILL DIED, WITH NO `ACCEPTANCE` LINE AT ALL.** The drop to Manual happens in the
  main loop's battle listener, OUTSIDE the story generator, so the driver's `try/except` never sees
  it. ⇒ **grade a §Ch22 transcript that ends with no ACCEPTANCE and a `BotModeError -> Manual` as
  KI-47, not as a hang and not as a §Ch22 defect.** (Same convention as §Ch20's `ch20room9`.)
* ⭐ **THE VALUABLE PART: KI-47 NOW HAS A DETERMINISTIC ~22,000-FRAME REPRODUCTION.** This class had
  only ever been caught opportunistically in batches, at *"a whole lane"* per hit. It is now one
  command. Recorded at the top of KI-47 in `05-KNOWN-ISSUES.md`, with the stall state.
* ⚠ **HYPOTHESIS, NOT A FINDING:** the frozen state is named `LearnMoveState.DialogueNotActive`, and
  Sceptile levels **50 → 51** in this fight in every winning run. A mid-battle level-up move prompt
  landing inside action selection is the obvious suspect — and "obvious suspect" is exactly what
  this project has been wrong about before. It needs its own probe.

⇒ **STATUS, STATED PRECISELY:** the §Ch22 chapter is **BUILT and DRIVEN to a complete, correct
finish** (drive 2: badge, fall, B1F, ladder, out, a real path onward). A **STORY RUN** through it
is **not yet reliable**, for two separate reasons that must not be conflated: the Juan fight is
stochastic (the chapter recovers — measured), and the shared battle path can freeze (KI-47 — the
chapter cannot recover, and that is not §Ch22's to fix).

## THE GRADE, PREDICTION BY PREDICTION

| # | predicted | measured | verdict |
|---|---|---|---|
| **P1** | the heal succeeds and the party is **still SIX**, HMs intact — rated ⚠ **LOW confidence**, because `deposit_dead_weight_if_worth_it()` makes Swellow (L41) and Zigzagoon (L19) eligible against Sceptile L50 | **six PIDs in, six PIDs out, every one at full HP** | ✅ **HELD** — and it was the prediction I was least sure of. The rotation plan self-gated. ⚠ It is not proven safe in general, only on this party at these levels; the `_heal_before_the_gym` assert stays. |
| **P2** | `steps=64`, `end_tile=(8,6)` | `ice_steps=64 end_tile=(8, 6)` | ✅ **HELD** |
| **P3** | the 3-step climb reaches `JUAN_STAND (8,3)` | the battle started at `SOOTOPOLIS_CITY_GYM_1F(8, 3)` | ✅ **HELD** (the battle's own map+tile is the witness) |
| **P4** | **Juan is WON**, 5/6 survivors, Swellow faints — HIGH | **`BattleOutcome.Lost`**, whiteout, respawn at (43,32) | ⛔ **MISSED — and it is the finding.** See the headline. |
| **P5** | `(8,4)`/`(8,5)` read `OPEN_STAIRS 0x207` after the puzzle — ⚠ rated the **riskiest mechanical line**, never read live by anyone | measured separately by `--driver ch22stairs`: **`(8,4) 0x20f → 0x207`, `(8,5) 0x20f → 0x207`**, `(8,6) 0x20d → 0x20e`, `(8,2) 0x22b` plain floor | ✅ **HELD, AND IT IS AN A/B IN ONE RUN** — the same column read before and after the walk. ⭐ It also confirms the adversarial finding by measurement: `(8,2)` is **plain floor**, so `_climb_to`'s locked-stair and cracked-ice guards would NOT have fired, and it really would have pressed "Up" into Juan. |
| **P6** | the fall lands on B1F `(8,6)` | drive 1: not reached. **drive 2: reached and taken** | ✅ **HELD on drive 2** |
| **P7** | ⭐ the discriminator: **B1F costs ZERO battles** after the badge | drive 1: `battles_on_B1F=0` with `b1f_steps=None` — ⛔ **VACUOUS**, zero battles for zero opportunities. **drive 2: `b1f_entered=True`, `b1f_steps=19`, `battles_on_B1F=0`** | ✅✅ **CONFIRMED on drive 2** — and drive 1 is the standing example of why the count alone proves nothing |
| **P8** | 19 steps to the ladder, then out | drive 2: **`b1f_steps=19`**, then 1F, then `SOOTOPOLIS_CITY (31,33)` | ✅ **HELD, exactly** |
| **P9** | a real `calculate_path` off the end tile | drive 1: `cont = 0` — ⛔ **the check was satisfied by the very failure it exists to catch** (a whiteout respawns the bot ON the target tile). drive 2: **`cont = 23`** | ✅ **HELD on drive 2**, and drive 1 is why the grade now demands NON-ZERO |
| **P10** | 35,000–50,000 frames | drive 1 (lost): 35,645. drive 2 (**lost, recovered, won, exited**): **64,563** | ⚠ **OVER, and correctly so** — the band was written for a clean single pass. A run containing a whole extra attempt costs a whole extra attempt. ⇒ the band applies per ATTEMPT, and this note is where that is now written down |

---

## ✅ THE TWO FAULT ARMS — AND THEY STRAND THE BOT IN **DIFFERENT** PLACES ON PURPOSE

Both must FAIL, and each attacks a different half of `ch22_chapter_done()` (badge **AND** position):

| arm | measured | why it matters |
|---|---|---|
| `POKEBOT_CH22_FAULT_NODESCEND=1` | `badge8=True at=SOOTOPOLIS_CITY_GYM_1F(8, 3)`, three attempts each raising the named fault, **`ACCEPTANCE: FAIL`**, `frames=63022` | ⭐ **stranded ON JUAN'S ISLAND with the badge in hand — a flag-only grade would have PASSED this**, which is the §Ch15 / §Ch18 / §Ch19 shape exactly |
| `POKEBOT_CH22_FAULT_STRANDED=1` | `badge8=True at=SOOTOPOLIS_CITY_GYM_1F(11, 22)`, `b1f_steps=19`, **`ACCEPTANCE: FAIL`**, `frames=64289` | stranded on the ENTRANCE side — the fall happened, the walk out did not. A guard that only caught the island half would be half a guard |

⭐ **AND `STRANDED` EARNED ITS KEEP BEYOND ITS STATED PURPOSE.** Its attempts 2 and 3 both raised
*"Ch22: the descent expects a single column; at (11, 22), target (8, 5)"* — correct refusals, but a
confusing cascade, because **the retry path did not distinguish the ISLAND side of GYM_1F from the
ENTRANCE side**. A real (non-fault) failure of the walk-out would have produced the same misleading
error. Fixed: the chapter now descends only when it is actually in the stair column at or above
`FALL_STAGING`, and walks out otherwise.
✅ **AND THE FIX IS PROVEN BY RE-RUNNING THE ARM, not by reading it**: the re-run reports
`attempt 1/2/3: every leg ran but the chapter does not grade done (badge=True, at=(11,22))` —
accurate and identical across attempts, with the column error gone, and still `ACCEPTANCE: FAIL`.

**⛔ ALL THREE ARMS WERE THEN RE-RUN UNDER THE FINAL CODE, because a grade that changed after the
runs that produced it is not evidence for those runs:**

| arm | verdict |
|---|---|
| clean | **`ACCEPTANCE: PASS`** — `badge8=True`, `SOOTOPOLIS_CITY (31,33)`, `city_state=6`, `ice_steps=64` / `ice_total=128` (`ice_ok=True`), `b1f_steps=19`, `battles_on_B1F=0` with `b1f_entered=True`, `CONTINUE=23`, `RECOVERIES 1`, `frames=64563` |
| `NODESCEND` | **FAIL**, stranded at `GYM_1F(8, 3)` with `badge8=True` |
| `STRANDED` | **FAIL**, stranded at `GYM_1F(11, 22)` with `badge8=True`, `b1f_steps=19` |

‼ `ice_total=128` on the clean arm is CORRECT and worth reading twice: attempt 1 walked the ice,
lost Juan and was archived; attempt 2 walked it again and won. **One complete 64-tile cover per
attempt** — which is exactly why the grade sums across attempts instead of reading the last one.
‼ *This is the third defect a fault arm found in code the happy path had already exercised — the
happy path cannot reach these branches, which is the entire argument for running the arms.*

## ⛔⛔ THE DRIVE FOUND TWO DEFECTS **IN ITS OWN GRADE**, AND BOTH ARE FIXED

This is the part worth carrying forward, because both are shapes this project has hit before:

1. **`battles_b1f == 0` was satisfiable by never going to B1F.** Zero battles because zero
   opportunities — *"A CANDIDATE IS NOT AN ATTEMPT"* in grade form. A run that lost the fight and
   went home would have satisfied the chapter's headline discriminator.
   ⇒ the grade now requires `b1f_steps > 0` **as well as** `battles_b1f == 0`, and the log line
   prints `b1f_entered` beside the count so the number can never be read alone.
2. **`isinstance(cont, int)` was satisfied by `cont == 0`** — a whiteout respawns the player *on*
   the Poké Center apron, so the path to it is empty. ⇒ **a can-continue check that a whiteout
   satisfies is not a can-continue check.** The grade now requires a **non-zero** path.

‼ Neither defect would have been found by reading the code. Both were found because the run took a
branch I had rated unlikely, and printed enough to see what the grade actually rested on.

## ✅ AND THE LOSS BRANCH IS NOW **DRIVEN**, NOT ASSERTED

In production a lost fight is a whiteout → `StoryAbort` → `StoryMode.run`, which clears the abort
latch, walks out of the Poké Center and re-enters `_play()` from the top; Segment 22 then re-runs
the chapter against virgin ice (the puzzle resets on every entry — MEASURED). That is a claim about
a code path, and this project's rule is that a claim of the form *"the recovery works"* is worth
nothing without an arm that exercises it. `Ch22ChapterMode` now **replays exactly what
`StoryMode.run` does** — clear the latch, `exit_building_after_whiteout()`, re-enter — up to 3
attempts, and reports `RECOVERIES`.
⚠ Capped at 3, not production's 40: a driver that can loop is a driver that can hang, and each
attempt costs ~35k frames.
