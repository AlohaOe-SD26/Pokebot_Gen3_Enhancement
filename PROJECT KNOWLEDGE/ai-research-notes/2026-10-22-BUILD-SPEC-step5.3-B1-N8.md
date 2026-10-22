# BUILD SPEC step 5.3: B1 (the Goodhart gate) + N8's grader half (typed checks), 2026-10-22

> The coordinator's spec, REVISED after one adversarial critic (`2026-10-22-step5.3-spec-critic.md`, filed beside
> this file; its MEASURED rows are cited below as "critic Qn"). Inputs: `2026-10-21-B1-recon.md` (the gap is the
> data path, not imports) and `2026-10-22-B1-grader-recon.md` (the grader mapped check by check; `#n` = that note's
> §1 table rows). Backlog items 12 (B1 + R13) and 13's N8 half. R: = `rate_step5.py`, L: = `live_step5.py`,
> H: = `play_harness.py`, HH: = `hands_harness.py`, G: = `brain/goals.py`.

## WHY

Step 5's grade says the AI plays like a curious person. Part of that grade is the AI grading itself:
- every curiosity check takes its time WINDOWS from the AI's own log (`goal_spans(actions)`, R:951);
- the AI computes the grader's own yield rule (G:571-572 = R:915, the same 8 and 20), so "717 of 717 agree" (#51)
  is true by construction;
- the grader imports AI constants (ERRANDS R:602/R:738, ERRAND_KINDS R:827, ASIDE R:1081, MAX_LOSSES R:1992;
  live_step5 L:101 GENERIC_BUSY and L:106 pick_personality/choose_gender/choose_name), and the ledger hash covers none
  of them, nor the mutant edit texts, the mark set (`ai_player/knowledge/milestones.json`, an AI file, H:52), the
  recorder periods, or the check code (critic Q5).
- The verdict is untyped: "reported" is a text prefix (`p2_reported`, R:1592-1601); 15 of 67 rows are forced PASS; a
  zero-sample check reads PASS (08 2026-09-02).

## WHAT THE CRITIC CHANGED (and why the work is staged)

- A curiosity yield over GAME windows is likely VACUOUS (critic Q3, MEASURED on ledger #34's evidence): GREEDY's
  curiosity is 85.9 % productive by the game against the real code's 90.2 %; BEELINE has no curiosity at all, so a
  yield RATE rewards it; LOAF's signal is about 5,000 frames inside 105k-176k-frame runs. So the game-window design is
  NOT decided here: stage A2 measures first.
- #12 fails as re-sourced (MEASURED: NOTRAIN won 3+ wild battles before the rival in 13 of 18 seeds): training needs a
  steps-IN-TALL-GRASS read, unproven.
- Some properties have NO game form: curiosity spacing (#54/#55: goal KINDS in a row), a detour's chosen place (#56),
  an aside coming back (#26), a GO goal after its page (#27). They are honest DIAGNOSTICS or HONESTY checks, never
  GRADED-from-the-game.

## STAGE A1 — TYPED, HONEST, HASHED; NO CHANGE IN WHAT IS MEASURED (one build + verify round)

- **A1-1 TYPED CHECKS (N8).** Every check is `Check(id, kind, status, n, floor, inputs, text)`:
  - `kind`: `GRADED` (counts), `HONESTY` (the AI's own word judged against the game; counts), `DIAGNOSTIC` (printed,
    never counts), `REPORTED` (a measure with no bound; never counts).
  - `status`: `PASS`, `FAIL`, `VACUOUS` (`n < floor`). VACUOUS FAILS the verdict unless its id is in
    `gates/grader_waivers.json` with a reason (hashed). The forced FAIL at R:1690 becomes VACUOUS.
  - `inputs` ⊆ {`game`, `harness`, `ai`}, declared HONESTLY for today's code. Construction RAISES if a GRADED check
    names `ai` and its id is not in `gates/b1_debt.json`; a HONESTY check must name both `ai` and `game`.
  - **`b1_debt.json`** (hashed) lists every GRADED check that still reads an AI input (the AI-windowed curiosity rows,
    training #3/#12, rest #8/#16, spins #5, divergence #30/#32/#34, speedrun #36/#37/#47, patience #39, LOSE3's AI
    half...), each with the AI input named and the A2 plan. The evidence prints each as a `B1 DEBT` line. A1 does
    not shrink the grade; it makes the debt visible and typed, and A2 pays it down.
  - P2_REPORTED, `p2_reported` and every `(True, "(reported) ...")` site become kind REPORTED; nothing is forced.
  - The verdict is PASS iff every GRADED and HONESTY check is PASS (or a waived VACUOUS). Ids are stable and unique;
    the evidence prints one line per check: id, kind, status, n/floor, inputs.
  - Reclassify (critic Q1), not re-source: #40 PATIENCE_OLD is GRADED by the game (dex unreached AND frames < budget;
    MEASURED 7/7 and 7/7), the AI reason DIAGNOSTIC; #44 and #61 HONESTY with the game half from chapter 1's seen
    maps (`PlaceRecorder.maps`, H:415) and const-to-key from `MapRSE` (`sandbox-pokebot/modules/map_data.py:792`),
    not the AI's world.jsonl, with #61's skipped consts counted as n; #56 HONESTY; #54/#55, #6, #26, #27, #35, #51,
    #62, #64 DIAGNOSTIC (each listed in the evidence as a property the grade no longer counts).
  - live_step5: L:596 name/gender and L:634 told-wild become HONESTY; L:769-781 pooled spins and rest occasions
    DIAGNOSTIC; its 5.2 AI-only checks (L:381-414) DIAGNOSTIC; its GAME checks through `truth_of` stay GRADED.
- **A1-2 GRADER-OWNED VALUES (G-3).** rate_step5 and live_step5 import nothing from `ai_player.brain`,
  `ai_player.personality`, `ai_player.mode` or `ai_player.hands`, directly OR through a gates module that re-exports an
  AI value (the rule walks every `gates` module the two import). Allow-list by name: `host.launcher`, `options.ENV_*`,
  `gates.*` plumbing. ERRANDS' values, ERRAND_KINDS, ASIDE and GENERIC_BUSY become grader-owned constants with the
  same values today (so A1 changes no outcome), each commented with its source; MAX_LOSSES is recorded by the HARNESS
  in the PLAY json (H already imports `mode` lazily, H:656). L:566-573's intent comes from the launcher run's own
  record (HONESTY), not from calling the AI's chooser.
  - `test_goals.py:2647-2648` (the grader's CURIOSITY_KINDS equals the AI's) is deleted: equality is the Goodhart
    channel. A DIAGNOSTIC may print a difference.
- **A1-3 THE LEDGER HASH (critic Q5).** `registered_numbers` adds: the mutant edit TEXTS the plans use; END_SLACK,
  CURIOSITY_KINDS, NEED_KINDS, GENERIC_BUSY, REAL_PLANS, NO_PHASE2, PERSONALITIES, STARTERS; the literal bounds in the
  verdict code (#6, #9, #13, #16, and #11/#17's hardcoded `b < a`, which also start READING their bound keys); the
  recorder periods and harness parameters (Story 30, Place 10, Wait 10, STEP_RATE, PUSH_KEEP, WAIT_KEEP); the sha256
  of `ai_player/knowledge/milestones.json` and `gates/fixtures/item_flags.json`; both json lists above; and the
  sha256 of the check code (`rate_step5.py`, `live_step5.py`, `play_harness.py`, `window.py`). `ledger.py` refuses a
  graded run whose numbers sha differs from its registration (as today), which now covers the code. A test mutates
  each and sees the sha move.
- **A1-4 THE RIPPLE (critic Q6).** Re-point `revert_step5.py`'s 30 rate_step5 anchors (a missed anchor aborts the
  gate); retire G266/G267 with a line in LESSONS; re-point `test_goals.py`'s 32 rate_step5 references and its tuple/
  prefix consumers to check ids; give `check_lessons.py` check-id resolution; LESSONS entries that call a REPORTED
  bound Enforced (PF-3 `LESSONS.md:126`, PL-8 `:281`, PF-14 `:196`) are corrected to say REPORTED (carried 5.2 item
  1, closed here).
- **A1 DONE WHEN:** the typed verdict reproduces today's outcome on synthetic rows (every former PASS row is PASS,
  REPORTED or a listed DIAGNOSTIC; nothing GRADED flips); every rule above has a FAULT + CONTROL; `revert_step5.py`,
  `check_lessons.py`, `test_goals.py`, `run_regression.py --quick` and `run_gates.py --quick` pass. It cannot be
  checked against #34 offline (its run folders are gone and its evidence rows are clipped at about 3,000 chars,
  MEASURED), so A1's proof is synthetic plus one `--purpose development` smoke run of 2 seeds x 3 plans.

## STAGE A2 — THE GAME READS, THEN A MEASUREMENT (one build + verify round, then a development sweep)

- **Reads, each with a known-answer fixture both ways (B3's rule):** party HP at EVERY battle end (`party_now()` at
  H:175; cheap); the tile type under the player on each position change (`map_location.tile_type == "Tall Grass"`,
  `modules/map.py:862-863`; medium cost, read only on a move); a press log (frame, button) in HarnessControls (HH:64-91,
  today an integer) plus facing (`avatar.facing_direction`, `modules/player.py:152-153`); `frame0 =
  emulator.get_frame_count()` before the loop (H:675) with the test `frame0 + recorder.frame == get_frame_count()` at
  the end.
- **A development sweep (`--keep-runs`, fresh dev seeds, all plans) that PRINTS, per run and per plan** (CH1, NOTRAIN,
  LOAF, GREEDY, ERRANDS_OFF, DEADREST, CH2, CH2_OFF): non-battle frames per inter-mark window; slices and productive
  slices BY CRITERION (tiles, page, battle, capture, item flag); the real code's base rate outside its curiosity spans;
  grass steps before the rival; battles started below each HP fraction; game spins; and the real-vs-control gap per
  run and pooled. Evidence filed; nothing registered.
- **Then the coordinator decides each B1-debt row from the numbers** (a short addendum to this spec): re-source it to
  the game where a control separates, keep it HONESTY where the property is the AI's own claim, or DIAGNOSTIC where no
  game form separates. Stated now: a yield RATE must not be the only curiosity check (it rewards a beeline); spacing
  has no game form; a game-read check that NO control fails is not registered.

## STAGE B — THE RE-GRADE (compute; background scripts)

Bounds set on development seeds only, between the controls and the real code, each with its margin; `--register` the
next unused range (after 960); one graded sweep (20 seeds; measure its wall time beside the tuner's 12 lanes). The
verdict, check by check, is step 5's grade from then on, compared row by row with ledger #34
(`2026-10-16-step52-RATE.txt`). A graded FAIL is information, reported in the frontier note; nothing is retuned on the
held-out seeds. Carried 5.2 item (6), CH2 at 1.181 vs 1.15, is re-derived here because #47's quantity changes.

## OUT OF SCOPE

The AI's play code. Its own 8/20 tile rule stays its business: the grader stops sharing its windows and constants, so
agreement stops being by construction (correlation remains: carried 5.2 item 3 is only partly closed, and that is said).

## STOP CONDITIONS (report instead of improvising)

- A1: a GRADED check whose outcome would flip under the typed verdict: report it, do not reclassify to hide it.
- A2: a read the harness cannot make at an acceptable cost: report the cost.
- Any stage: a control that does not fail a proposed game-read bound: report the numbers; do not register.
