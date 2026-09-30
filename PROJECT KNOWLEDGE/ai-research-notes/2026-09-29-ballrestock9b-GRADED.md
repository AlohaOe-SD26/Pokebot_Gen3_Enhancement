# 2026-09-29 — USER RULINGS 23 + 26, design v2 step 9b (BB at Sootopolis) GRADED: the League-basket visit tops off 1 Ultra Ball after the basket in the same menu session, and walks for balls alone when the basket is complete; OFF, observe and a swallowed ball failure are frame-exact with M0; a close mid-purchase is logged and walked back. TWO PREDICTIONS FAILED (P12 on its premise, P13 on two mutant sets); a latent RULING 18 stranding is fixed

> Predictions: `2026-09-29-ballrestock9b-PREDICTIONS.md` (`c7cf1bbd`, with the Step-0 reads and M0 ×2, before the
> code commit `2f082d04`). The gate was first run after both. The live arms ran on `23ce266d` (the gate fix; no
> production code changed after `2f082d04`). The ADDENDUM P12b (`8ea30ea8`) was filed after P12 failed and before
> B3′ ran.
>
> Evidence (frames are debug-log frames):
> - `tools/story-dev/evidence/2026-09-29-ballrestock9b-<ARM>.txt`, one per arm: env, verdict lines, `[BALLS-BUY]`
>   lines, the driver segment, and the first divergence from M0a;
> - `-GRADER.txt`: the grader's final output (58 checks) and its source;
> - `-GATE.txt`: gate runs 1 (FAILED), 2 and 3;
> - `-M0.txt` (+ the two raw M0 debug logs).

## RESULTS — each prediction re-read against its own words

| P | Arm | Reading | Verdict |
|---|---|---|---|
| P1 | **A2-OFF ×2** | `R frames = 10329`, ₽22,166, PASS with the new conjuncts; **every frame-stamped debug line identical to M0a** (both runs); no Sootopolis `[BALLS-BUY]` | ✅ OFF unchanged |
| P2 | **A2-OBS** | the exact line `why=topoff-observe … plan=[('Ultra Ball', 1)] floor=19000 walk=False …`; every other line identical to M0a | ✅ |
| P3 | **A2-ON** | `why=topoff-forecast … walk=True`, then `f3706022 why=topoff mart=SootopolisCity ball=Ultra Ball bought=1 premier=0 spare=18->19 money=22166->20966 floor=19000`; ₽67,466 → 20,966 (`COST 46500`); first divergence from M0a = the ball phase's first action (f3705494 vs M0a's f3705558), before M0a's Mart exit | ✅ the discriminator; two `buy_in_shop` calls in one menu session work (the recon's F15) |
| P4 | **A2-FLOOR** | `bought=5 premier=0 spare=18->23 money=22166->16166 floor=1000`; the forecast said 5 | ✅ the basket floor is what limits A2 to one |
| P5 | **A2-RAISE** | PASS (`ballfail`): `early_basket='bought'`, 3/8/30, one `why=topoff-failed … the basket's outcome stands`; **every frame-stamped line identical to M0a** | ✅ a ball failure costs no frame and never touches the basket |
| P6 | **A2b-ON** | PASS (`balls`): "balls only", order `['EB-MART']`, basket untouched, `bought=1 … money=22166->20966` | ✅ the periodic visit |
| P7 | **A2b-OFF** | PASS (`nothing`): "nothing missing", no walk, no `balls` key, `R frames = 2462` | ✅ |
| P8 | **A2b-TYPO** | one `why=topoff-flag mart=SootopolisCity reason=POKEBOT_R23_BALLRESTOCK='yes' …: treated as OFF`; frames and tracked lines identical to A2b-OFF | ✅ |
| P9 | **A2b-RAISE** | PASS (`ballfail`): "balls only", `['EB-MART']`, one `topoff-failed`, no purchase, walked back, gym 1F | ✅ |
| P10 | **A2c** | spare 19 at load (Step-0 read); `why=topoff-forecast … spare=19->19 money=20966->20966 plan=[] floor=19000 walk=False reason=cannot afford one Ultra Ball (budget 983, price 1200)`; no walk | ✅ ON pointed at its own output does nothing |
| P11 | **A2c′** | `PREMISE FAILED for expect=balls (… balls=[])`, `ACCEPTANCE: FAIL` | ✅ the `balls` grade cannot pass having done nothing |
| P12 | **B3** | never started: `PREMISE FAILED for expect=budget (… plan=[] …)` | ❌ **FAILED on the instrument**: the `budget` premise needs a basket plan, and my prediction missed it |
| P12b | **B3′** (addendum) | `f3705535 why=topoff-closed … reason=the basket visit's budget closed the ball phase mid-purchase (R18 walks back)` at exactly frame_start + 4,358; retry walked back (`close_presses 42`), not stranded, basket bought, no Ultra, ₽22,166, gym 1F; identical to A2-ON through the ball phase's first action | ✅ |
| P13 | the gates | run 1: every row PASS, but M7 and M11 red on OTHER sets than written | ❌ **FAILED as filed** (below) |

## P13, THE GATE — what failed and what it taught

- **Run 1 was on the code commit, after the predictions.** Every row passed. 12 of the 14 written mutant sets were
  exact, plus N1. Two were not:
  - **M7** (the ball phase lets a failure escape) turned the abort row P6 red too. The cause was the gate's own stub:
    it raised a NEW exception, but the real `reraise_if_aborting` re-raises the error it was GIVEN (its docstring
    says so). So P6 was testing the stub. The stubs were made faithful.
  - **M11** (OFF returns a dict) turned O3 red too. The written set missed it: a typo IS OFF and takes the same
    branch. The set was corrected, with that reason in its label.
- **Run 2** added M15 and M16 (P6 and O7's abort half had no mutant): ALL PASS.
- **Run 3:** a coverage check (every row needs a mutant that reddens it) found K1, O6, S4, S5, S8 and A2 uncovered,
  and no row for the forecast's floor lever. O8 and M17-M25 were added, with their sets written first. All nine were
  exact on their first run: ALL PASS.
- The 9a gate and RULING 18's gate pass unchanged.
- Rules → `08`.

## THE RECON (one adversarial agent, before any code) — what it changed

- **F1, a latent RULING 18 stranding, now fixed.** It is confirmed at `sootopolis_gym.py:839-872,957`: one report dict
  serves every Juan attempt, so a second errand inherited `returned=True`, skipped the walk back, and would have
  stranded the bot on the Mart side with the menu open (KI-103).
  - The fix: `stock_basket_early` archives the previous errand first.
  - Proven by the executing gate row S9 and mutant M10, NOT by a live second attempt.
- **F2-F9, F12, F14:** built as the predictions list them. They include:
  - the `outcome_bought`, `production_forecast` and `no_ball_delta` conjuncts;
  - the `ballfail` and `balls` expectations;
  - a phase that writes only under `report["balls"]`;
  - blocking on a memo hit;
  - a 9b-specific typo line;
  - the derived memo key.
- **F13, deferred to step 10:** v2's split visit order needs the kit.

## SEEN, NOT GRADED

- **R18's basket block waits a full 1,800 frames at the counter on EVERY visit.** Its `wait_until_truly_controllable`
  never sees a controllable avatar with the shop menu open (the clerk's `lock` freezes the player; the recon's Q1).
  The watchdog's "no progress" dumps show it in M0a and every arm. It is bounded and harmless, but it is 1,800 wasted
  frames per Juan attempt: a candidate cleanup, not built.
- **A2-ON took 551 frames more than M0** (10,880 vs 10,329), for one Ultra Ball.
- **The realistic periodic visit buys nothing.** After a Juan loss the money halves (₽20,966 → ₽10,483), below the
  ₽19,000 floor. Under RULING 18's floor the Sootopolis top-off is about one Ultra per run until the League: a finding
  for Q1 and step 14.

## GRADING NOTES (disclosed)

- **A2-ON's "identical until the purchase" check was RE-OPERATIONALIZED after its first run.**
  - The first version cut at the purchase LOG frame (f3706022). That is about 530 frames after the phase starts, and
    after M0a's own Mart exit (f3705736), so it read 5 lines against 6.
  - The honest test is the first divergence. It is the ball phase's first action (f3705494 `RESUMED after 2019`
    against M0a's f3705558 `RESUMED after 2083`), sitting between the basket's shared wait and M0a's exit.
  - Both versions are in `-GRADER.txt`.
- **The grader checked more than some predictions said** (e.g. "exactly the forecast line AND the failed line" for
  P5/P9, where the prediction named only the failed line). Every such extra check passed.
- **KI-112:** every OFF arm and M0b replayed M0a exactly. Every ON arm's first divergence is its own ball phase. This
  is one trajectory, replayed: a determinism check, not a replication.

## WHAT THIS DOES NOT SHOW

- A second Juan attempt LIVE (F1's fix rests on the executing gate row S9).
- Whether the top-off pays for itself, or how often it buys in real runs (step 14).
- v2's split visit order (step 10).
- A post-game purchase (`[R-N6]`: no v2 consumer reaches one).
