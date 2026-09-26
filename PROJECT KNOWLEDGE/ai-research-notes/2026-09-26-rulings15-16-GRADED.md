# 2026-09-26 — USER RULINGS 15 + 16 — GRADED: ALL SEVEN ARMS AS PREDICTED

> Grades `2026-09-26-rulings15-16-PREDICTIONS.md` (committed `7585cb76` on branch `wt/ch24organic` BEFORE the drives).
> Evidence, committed: `tools/story-dev/evidence/2026-09-26-rulings1516-{R15-ENTER,R15-B48,R15-B47,R15-A,S1-FULL,
> S2-NOTHING,S3-FULLBASKET}.txt` (+ `.stdout.txt`). Fixtures verified (`post_league_shop` `1564948368f6`,
> `post_ch24_atdoor_L75` `8b8cd907db09`, `post_league_heal`). All drives `HARNESS_EXIT_ON_MANUAL=1`.

| arm | prediction | reading | verdict |
|---|---|---|---|
| **R15-ENTER** (L75 party, floor **65**) | R1 passes with Zigzagoon L19 + Castform L36 below; door open | `ACCEPTANCE: PASS` at floor 65 — the only party ever to win the gauntlet now passes R1 at the PRODUCTION floor | ✅ |
| **R15-B48** (`post_league_shop`, floor 48) | refuse, 3 of 6 | `3 mōn below the L48 floor — only 3 of 6 at it, RULING 15 needs 4: Zigzagoon…, Castform…, Wailord#FA51ECF3 L47`; door shut; PASS (refuse) | ✅ |
| **R15-B47** (same fixture, floor 47) | enter, 4 of 6 | `ACCEPTANCE: PASS` (door open) | ✅ **the boundary is exact** |
| **R15-A** (floor 65) | refuse, 0 of 6 | `6 mōn below the L65 floor — only 0 of 6 at it, RULING 15 needs 4`; PASS (refuse) | ✅ |
| **S1 FULL** (`post_league_heal`, empty bag) | buy the whole basket; ₽56,041 → ₽1,741 | `to_buy` = all four lines, `need_money=54300`, `money_after=1741`, `ACCEPTANCE: PASS` (identical to the 2026-09-04 capture) | ✅ ordinary path unchanged |
| **S2 NOTHING** (`post_league_shop`, basket carried) | FAIL solely on `premise_ok=False`; nothing bought | `to_buy=[]`, `need_money=0`, `nothing_to_buy=True`, `money_before == money_after == 1741`; `GRADE premise_ok=False shortfall={} missing=[] whiteouts=0 failure=None` | ✅ |
| **S3 FULLBASKET** (skip-the-fix, same fixture) | the old behaviour refuses a party that already carries the basket | `the missing basket lines [all four] cost ₽54,300 … but we hold ₽1,741 — short by ₽52,559` | ✅ **the change is load-bearing** |
| **G** gates | PASS; fault arms red | `probe_ch24_r1_refusal.py` (strict all-six rule caught ×3), `probe_ch23_basket_buy.py` (always-whole-basket caught ×4; buying raw `LEAGUE_BASKET` caught) | ✅ |

## WHAT THIS SETTLES
* ✅ RULING 15 as the user ruled it: the gauntlet opens once four members are at the floor; the proven winning shape
  (4×L75 + two stragglers) enters at L65. Training still aims to lift everyone (RULING 12's training target is untouched).
* ✅ RULING 16: leg 11 pays only for what is missing and still verifies the whole basket; the stocked case no longer
  refuses on money it does not need.

## CODE REVIEW (adversarial `reviewer`) — APPROVE, three low risks handled

1. ⚠ **S2's branch (nothing missing ⇒ skip the Mart menu) is UNREACHABLE in production today**: the only caller
   (`do_victory_road_chapter`) invokes leg 11 only when a basket line is short. S2 validates defensive code, not an
   organic path. RULING 16's real value is the PARTIAL basket — which USER RULING 18 (buy early) will make the
   normal case.
2. A stale docstring ("a second call raises") in `prepare_and_open_the_league` — corrected.
3. `r1_party_size` was unset on the unreadable-bag refusal path — now `None` there (telemetry only).

## WHAT IT DOES NOT SETTLE
* ⚠ A PARTIAL basket (some lines carried) is exercised by the pure gate only — no fixture carries a partial basket
  and seeding one would need a RAM write into the encrypted bag. The live path runs the same `buy_in_shop` call with a
  shorter list.
* ⚠ Money itself is still short for whiteout-heavy runs (3 of 3 organic arrivals) — RULINGS 17 (Amulet Coin) and 18
  (buy early with a reserve lock) are the next builds; F0 telemetry will measure the effect.
