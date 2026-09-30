# 2026-09-29 — USER RULINGS 23 + 26, design v2 step 9a (BB) GRADED: with `POKEBOT_R23_BALLRESTOCK=1` the post-badge-1 Rustboro heal tops off 22 Poké Balls (+2 Premier) and returns to its exit tile facing Down; OFF, observe, an empty plan, a typo and the floor arm are frame-exact with M0; the bound arm recovers

> Predictions: `2026-09-29-ballrestock-PREDICTIONS.md` (`7e7536de`, with the M0 and the Step-0 observe read, before the
> code). Code: `1daec9a4`.
>
> Evidence (frames are debug-log frames):
> - `tools/story-dev/evidence/2026-09-29-ballrestock-*.txt`: one file per arm, each with its env, its `[BALLS-BUY]`
>   lines and its tracked lines;
> - `-GRADER.txt`: the output and the grader's source.

## RESULTS — every prediction held (each bullet re-read against its own words, gate bullets included)

| Arm | Env (beyond M0) | Reading | Verdict |
|---|---|---|---|
| **B-OFF ×2** | none | 52 of 52 tracked lines identical to M0-5, whole run; no `[BALLS-BUY]` | ✅ |
| **B-TYPO** | `=yes` | printed `the ball top-off: POKEBOT_R23_BALLRESTOCK='yes' is not one of (…): treated as OFF` (once per heal: Rustboro, then Dewford); 52/52 identical; no `[BALLS-BUY]` | ✅ |
| **B-OBS** | `=observe` | one `why=topoff-observe … reason=top off 22 x Poké Ball (spare 7 <= trigger 20; budget 4470)`; 52/52 identical (it neither moves nor waits) | ✅ |
| **B-ON** | `=1` | `f178239 [BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=22 premier=2 spare=7->31 money=9940->5540 exit=16,39 back=16,39 facing=Down`; identical to M0 before the heal's end (33/33); then `heading south` | ✅ the discriminator |
| **B-CTRL** | `=1`, `--set-balls 25` | one `why=topoff-none … spare=27->27 … reason=spare 27 > trigger 20`; 52/52 identical to M0-25, whole run | ✅ ON with an empty plan is frame-exact with OFF |
| **B-FLOOR** | `=1`, fault floor 9600 | one `why=topoff-none … reason=cannot afford one Poké Ball (budget 170, price 200)`; 52/52 identical | ✅ the floor gates the purchase |
| **B-FLOOR2** | `=1`, fault floor 8940 | `why=topoff … bought=2 premier=0 spare=7->9 money=9940->9540 exit=16,39 back=16,39 facing=Down` | ✅ the single-line path (no Premier) |
| **B-BOUND** | `=1`, bound 300 frames | `f176685 why=topoff-failed … reason=the errand's frame bound expired`; no drop to Manual; the run reaches `heading south` (the rival starts at f178972 against M0's f178292) | ✅ the recovery works |

- **The gate `probe_stock_topoff.py`:** L1-L8, L7b, A1-A6 and E1 hold. M1-M9 each turn exactly their pinned rows red,
  and N1 turns none. Full suite: ALL 129 ENFORCING GATES PASS (before the code commit).

## SEEN, NOT GRADED

- **The errand took about 1,855 frames** (f176384 → f178239), against its bound of 8,000. The mart visit ran from
  f176596 to f178038.
- **The rival fight (opp 600) is LOST in every arm and in M0** (this seed, this party of one).
  - After that whiteout, ON holds ₽2,770 (5,540 / 2) against M0's ₽4,970, and 31 balls against 7.
  - The purchase spent HALF the excess over the floor, precisely so that a whiteout that halves the money cannot make
    the next heal unaffordable.
  - Whether topping off is worth that money is a batch (step 14) question.
- **The window's second heal is Dewford's**, which is not whitelisted: no line, as designed.

## FOUND ALONG THE WAY

- **The recon's hysteresis claim holds only for the Poké Ball.** Under the ₽6,000 cap the Great Ball takes 3 visits
  and the Ultra Ball 5 from spare 0. Pinned in gate row L7b; it matters from 9b, and weighs on the user's Q1.
- **The recon's "round down to 10" correction was right.** `shop.c` gives one Premier per transaction of 10+, so 22 is
  bought as [10, 12], not 20 + 2 (live: premier=2, bought=22).
- **The mechanics angle corrected Q2's facts** (not built): THREE marts sell FIVE situational balls (Rustboro's Timer
  and Repeat, with `FLAG_MET_DEVON_EMPLOYEE`; Mossdeep's Dive, Net; Verdanturf's Nest). The Poké-vs-Ultra cost ratio
  is about 2.6× at full HP and 4.7-6× on a weakened target.
- **Step 9b is NOT a small follow-up.** `league_reserve._shop` raises "this Mart sells none of …" on an empty basket
  plan, and the earlybasket driver's `money_drop_equals_cost` fails by construction on an arm that buys a ball. Both
  must change first.

## WHAT THIS DOES NOT SHOW

- Any city but Rustboro, any ball but the Poké Ball, or the Sootopolis consumer (9b).
- The Great/Ultra multi-visit behaviour live (L7b is pure).
- The errand under an outer caller bound: a `_yield_bounded` that closes the heal mid-errand leaves the recovery
  un-run (a recon risk, named).
- Whether the top-off changes a run's outcome (step 14's batch).
