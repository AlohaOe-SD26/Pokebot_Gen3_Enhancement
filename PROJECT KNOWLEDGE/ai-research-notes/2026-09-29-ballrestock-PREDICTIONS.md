# 2026-09-29 — USER RULINGS 23 + 26, design v2 step 9a (BB: the ball top-off at Rustboro): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded arm. Branch `wt/ballrestock`, cut from `main` `002e5cd8`.
> Spec: `ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` §2 step 9 (a NOTE). A three-angle recon (code audit, game
> mechanics, adversarial + live fixture) came first; its output is a NOTE, and each load-bearing claim was re-read.
> The M0 and ONE Step-0 `observe` smoke run (an input read, recommended by the recon) were measured before this file.
> The graded observe arm is re-run after the code commit.

## SCOPE: step 9 is SPLIT (the recon's recommendation)

- **9a (this file):**
  - the pure module `modules/story/stock_topoff.py`;
  - consumer (a), the piggyback at the end of `heal_in_pokemon_center` (an UPSTREAM-derived file), with Rustboro as
    the only whitelisted city;
  - the gate `probe_stock_topoff.py`;
  - the live A1 arms.
- **9b (next):** consumer (b), the Sootopolis League-basket visit.
  - ⚠ The spec's consumer (b) would never buy balls: `league_reserve._shop` raises "this Mart sells none of …" when
    the basket plan is empty (`league_reserve.py:379-381`), even after the early return is relaxed.
  - The earlybasket driver's `money_drop_equals_cost` conjunct also fails by construction on any arm that buys a ball.
  - 9b must fix both first.

## WHAT THE RECON CHANGED IN THE SPEC (each is built into 9a)

- **The quantity formula went NEGATIVE below the floor.** `(money − floor)//2` rounds down in Python. So a named
  refusal ("at or below the floor") comes first, and the result is clamped at the in-game max, min(money // price,
  99). Above that max, `buy_in_shop`'s quantity loop never ends: Up wraps to 1 (`menu_helpers.c:186-188`).
- **An UNCONDITIONAL second stable wait would add ≥ 20 frames to EVERY OFF heal.** It runs only if the errand
  actually moved the avatar (gate A3).
- **"The mode is Story" became `isinstance(mode, StoryMode)`.** A string test would miss the ENDLESS RESET batch lanes
  and match every harness driver.
- **The failed-walk memo is `StoryMode._ball_topoff_failed`, reset per run.** A bag delta that is not the plan also
  counts as a failure, so a silent short purchase is not re-walked every heal.
- **`stage()` and `floor()` fail CLOSED** (no purchase, named). A stage that fell back to MID would drop the basket
  floor to ₽1,000.
- **The spec's "round down to a multiple of 10" is not a `shop.c` rule.** A final line of 10-19 still earns its
  Premier. So the remainder is MERGED into the last line: 22 is bought as [10, 12], which earns 2 Premiers and loses
  no ball.
- **`observe` has its own tag** (`why=topoff-observe`). The flag is parsed strictly; a typo is OFF WITH an error.
- **The errand runs only if the heal's exit wait reached a stable avatar,** so the recorded exit tile cannot be the
  door warp. It closes the shop BEFORE any controllable-wait, and ends facing Down, as OFF does.
- **The bounded defaults** (Q1 stays the user's; the numbers are imported, never copied):
  - TRIGGER = `DEX_CATCH_BALL_RESERVE` + `DEX_CATCH_MAX_EXPECTED_THROWS` = 20;
  - TARGET = `MAX_BALLS_PER_TRIP` = 30;
  - BATCH_CAP = ₽6,000, and half of (money − floor);
  - floor = `CASH_FLOOR`, plus 2 × the League basket's missing cost in the reserve era.
- **⚠ Found while building the gate, and pinned in row L7b rather than hidden.** The recon said hysteresis holds for
  every ball. It holds for the POKÉ BALL (₽6,000 buys 30: one visit from any spare 0..20). For the Great Ball and the
  Ultra Ball the ₽6,000 cap binds, so they take 3 and 5 visits from spare 0. That matters from 9b, and is the user's
  Q1 to weigh.
- **The Q2 facts the mechanics angle corrected** (for the user's question, not built):
  - THREE marts sell FIVE situational balls. Rustboro's Timer and Repeat come with `FLAG_MET_DEVON_EMPLOYEE`, and
    Mossdeep's Dive joins Verdanturf's Nest and Mossdeep's Net.
  - The Poké-vs-Ultra money ratio is about 2.6× at full HP and 4.7-6× on a weakened target.

## THE M0 AND THE STEP-0 READ (evidence: `tools/story-dev/evidence/2026-09-29-ballrestock-M0.txt`)

- **Trajectory:** `storyresume` on `r20_badge1_party1_gym.ss1` (50af0f5c), `random.seed(1)`, `--frames 60000`, with no
  R20/R24 env. Main `002e5cd8` (no step 9 code).
- **`--set-balls 5`, run ×2:** IDENTICAL, 52 of 52 tracked lines.
  - The post-badge-1 Rustboro heal before the rival (`story_mode.py` `_play`, `heal_in_pokemon_center` via the rival
    prep): the PC door at f174940.
  - `f175500 [hb] … balls=7 money=9940` at the nurse.
  - The exit at f176275, then `f176385 'Story: heading south — the rival is waiting in Rustboro...'`.
- **`--set-balls 25`, ×1:** the same heal, with `balls=27`.
- **The Step-0 `observe` smoke run** (new code, before this file): `f176384 [BALLS-BUY] why=topoff-observe
  mart=RustboroCity ball=Poké Ball … reason=top off 22 x Poké Ball (spare 7 <= trigger 20; budget 4470)`. Every tracked
  line is identical to M0 (52/52).
- **By hand:**
  - floor ₽1,000 (MID); budget min(6,000, (9,940 − 1,000)//2 = 4,470) = ₽4,470;
  - qty = min(30 − 7, 4,470 // 200 = 22, …) = 22, bought as [10, 12], so 2 Premiers;
  - spare 7 + 22 + 2 = 31; money 9,940 − 4,400 = ₽5,540.

## PREDICTIONS (each arm = the M0 command with `--set-balls 5` unless stated, plus the env named)

A single-run arm is attributed only if its tracked lines match M0 up to the heal's end (f176384) and it differs there,
on the errand's own line.

- **B-OFF ×2 (new code, no flag):** tracked lines identical to M0-5 (52/52), and no `[BALLS-BUY]` line. *Falsifier:*
  any reproducing difference.
- **B-TYPO (`POKEBOT_R23_BALLRESTOCK=yes`):** a printed `the ball top-off: POKEBOT_R23_BALLRESTOCK='yes' is not one
  of …: treated as OFF` line, then tracked lines identical to M0-5 and no `[BALLS-BUY]` line.
- **B-OBS (`observe`):** exactly one `why=topoff-observe` line, whose reason reads `top off 22 x Poké Ball (spare 7
  <= trigger 20; budget 4470)`. Tracked lines identical to M0-5 (52/52): observe does not move or wait.
- **B-ON (`1`), the discriminator:**
  - exactly one line, `[BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=22 premier=2 spare=7->31
    money=9940->5540 exit=X,Y back=X,Y facing=Down`, with `back` equal to `exit`;
  - tracked lines identical to M0-5 up to the heal's end;
  - the run then goes on to `heading south — the rival is waiting`.
  - ⚠ Frames after the errand shift, so nothing later is graded.
- **B-CTRL (`1`, `--set-balls 25`):** exactly one `why=topoff-none … spare=27->27 … reason=spare 27 > trigger 20`.
  Tracked lines identical to M0-25 (an empty plan yields NOTHING, so ON is frame-exact with OFF here).
- **B-FLOOR (`1`, `POKEBOT_R23_FAULT_FLOOR=9600`):** one `why=topoff-none … reason=cannot afford one Poké Ball
  (budget 170, price 200)`. Tracked lines identical to M0-5.
- **B-FLOOR2 (`1`, `POKEBOT_R23_FAULT_FLOOR=8940`):** one `why=topoff … bought=2 premier=0 spare=7->9
  money=9940->9540`. This is the single-line path: 2 < 10, so no Premier.
- **B-BOUND (`1`, `POKEBOT_R23_FAULT_ERRANDFRAMES=300`), the recovery arm:**
  - one `why=topoff-failed … reason=the errand's frame bound expired`;
  - the run still reaches `heading south — the rival is waiting`.
  - *Falsifier:* a wedge, a drop to Manual, or no `heading south`.
- **The gate `probe_stock_topoff.py`:** L1-L8 (plus L7b), A1-A6 and E1 hold. Each of M1-M9 turns exactly its pinned
  set red, and N1 turns none. The full suite stays green.

## WHAT THIS WILL NOT SHOW

- Any city but Rustboro, any ball but the Poké Ball, the Sootopolis consumer (9b), or whether the top-off changes a
  run's outcome (step 14's batch).
- The Great/Ultra multi-visit behaviour live (L7b, pure).
- The errand under an outer caller bound. `_yield_bounded` closing a heal mid-errand is a recon risk, named and not
  driven.
