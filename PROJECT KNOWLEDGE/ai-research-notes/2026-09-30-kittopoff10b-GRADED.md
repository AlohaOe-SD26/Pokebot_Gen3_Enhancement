# 2026-09-30 — USER RULING 26, design v2 step 10b (HK at Sootopolis) GRADED: the kit rides RULING 18's League-basket visit, bought AFTER the basket; kit OFF/skip/observe is 9b exactly; all twelve predictions held (49/49), the two FAIL-by-design arms on exactly their pre-registered conjuncts

> Predictions: `2026-09-30-kittopoff10b-PREDICTIONS.md` (`3e246e81`), committed BEFORE the code commit (`ea75fe1f`)
> and before any graded arm. The design: `2026-09-29-kittopoff10b-DESIGN.md` (`f52e1e5c`, after a recon and an
> adversarial review). ⚠ P13 (the gates) was not blind, and the predictions said so. Every live arm (P1-P12) was.
>
> Evidence (frames are debug-log frames):
> - `tools/story-dev/evidence/2026-09-30-kittopoff10b-S-*.txt`: one file per arm, with its fixture, its flags, the
>   driver's lines and the debug log's driver segment;
> - `-GRADER.txt`: the grader's output (49/49). The grader was fault-tested first on the real outputs: S-BALL's files
>   graded as S-ON, S-OFF's as S-BALL, and S-BALL's as S-KITONLY each FAIL on the right discriminators;
> - `-DIFF.txt`: E7's differential; `-ADVERSARIAL.txt` and `-GATE.txt`: the gate's adversarial pass and run 3.

## RESULTS — every prediction held

| Arm | Fixture, flags | Reading | Verdict |
|---|---|---|---|
| **S-OFF** | post_hm07, none | PASS; R frames 10,329, ₽22,166; all 27 frame-stamped segment lines = 9b's committed M0a; no kit/ball line | ✅ OFF changes nothing |
| **S-BALL** | balls `1` | PASS; frames 10,880; Ultra +1; A2-ON's two `[BALLS-BUY]` lines byte for byte | ✅ 9b unchanged |
| **S-OBS** | balls `1`, kit `observe` | PASS; A2-ON's purchase and lines + ONE `[KIT-BUY] why=kit-observe … kit=[('Hyper Potion', 1)] … split_balls=[] … walk=False` | ✅ observe buys 9b's |
| **S-SKIP** | eb_after_M0a, kit `1`, no key items | PASS; "nothing missing", no walk, ₽22,166; ONE `kit-skip` line | ✅ the coupling holds |
| **S-ON** | both `1` | PASS; ₽67,466 → **20,966**; Hyper **+31**, Full Heal +8, Revive +3, Ultra **+0**; `REPORT kit.before = {'Hyper Potion': 30}`, `got = {'Hyper Potion': 1}`; the four lines in order (below) | ✅ the basket, then the kit, separated by time |
| **S-RAW** | both `1` + RAWBAG | **FAIL by design** on EXACTLY `bag_delta_equals_plan`, `balls_as_forecast`, `kit_as_forecast`, `kit_attributed`, `kit_before_after_basket`, `production_kit_forecast`; production bought Ultra +1, Hyper +30 and logged `kit-none` | ✅ D4's live proof |
| **S-KITONLY** | eb_after_M0a, kit `1` | PASS; `kit only`; Hyper +1; ₽22,166 → 20,966; no `balls` key | ✅ a kit-only walk (the None dereference the design found is gone) |
| **S-BOTHKIT** | eb_after_M0a, both `1` | PASS; `kit only` although 9b's forecast line says `plan=[('Ultra Ball', 1)] … walk=True`; Hyper +1, Ultra +0; `memo_end = []` | ✅ the effective ball walk |
| **S-FH** | eb_after_A2ON, kit `1` | PASS; Full Heal **+1**; ₽20,966 → 20,366 | ✅ the first live drive of the status line |
| **S-OBS-RAISE** | balls `1`, kit `observe`, RESERVE_FAULT_RAISE | PASS; A2-ON's purchase; ONE `kit-failed`; `memo_end = ['SootopolisCity:kit']` | ✅ a kit failure never costs the balls |
| **S-VAC** | eb_after_M0a, kit `1`, floor 30,000 | `PREMISE FAILED … kit=[]`, ACCEPTANCE FAIL | ✅ the grade cannot pass having done nothing |
| **S-RAWVAC** | eb_after_M0a, kit `1` + RAWBAG | **FAIL by design** on EXACTLY its nine pre-registered conjuncts; "nothing missing", ₽22,166 | ✅ |

- **S-ON's four lines** (the design's order, and 9b's forecast line untouched, R1):
  - `f3701177 [BALLS-BUY] why=topoff-forecast … plan=[('Ultra Ball', 1)] floor=19000 walk=True`
  - `f3701177 [KIT-BUY] why=kit-forecast … kit=[('Hyper Potion', 1)] … wants=[('Hyper Potion', 4), ('Full Heal', 2)]
    split_balls=[] floor=19000 walk=True`
  - `f3706032 [BALLS-BUY] why=topoff-none … money=22166->20966`
  - `f3706032 [KIT-BUY] why=kit … bought={'Hyper Potion': 1} money=22166->20966`
- **P13, the gates (not blind):** `probe_kit_topoff_sootopolis.py` ALL PASS (138 checks: 64 rows, 71 mutants, 3 no-ops),
  after an adversarial pass found 23 misses and a production defect (below). The 9a, 9b, 10a and RULING 18 gates pass.
  The full suite: see THE REVIEW.
- **E7, proven twice:** the differential (1,620 visit pairs and 80 `_shop` pairs, 0 differ from 9b, with planted
  controls caught) and S-OFF/S-BALL/S-OBS live.

## SEEN, NOT GRADED

- **S-ON's segment takes 10,890 frames**, 10 more than A2-ON's 10,880: the counter buys a Hyper Potion (a different
  list slot) instead of an Ultra Ball.
- **S-KITONLY and S-BOTHKIT run the same 7,486 frames, and their purchase lines fall on the same frames** (f3710241,
  f3712193). The balls' forecast line is the only difference.
- **A cosmetic wart:** a visit with the balls OFF prints `… and 0 x None (0 to the reserve + 0 after the kit)`, because
  `visit_plan`'s reason names a ball that is None. Harmless; left for the review.
- The kit at Sootopolis buys 1 Hyper Potion (post_hm07) or 1 Full Heal (A2-ON's output) per visit. Whether that pays
  for itself against Juan is step 14's question.

## FOUND ALONG THE WAY

- **The design's review found the rebind of 9b's forecast would have INVERTED the driver's check** (the right build
  failing, a build without it passing). No rebind was built; the split lives in `report["kit"]["split_balls"]`.
- **The gate's adversarial pass found 23 mutants no gate caught, and that the gate's own header claimed an
  input-dimension table the rows did not exercise.** It also found PD1: after a kit-read raise, 9b's fallback phase
  never memoised a wasted "balls and kit only" ball walk. Fixed, with row P22. Recorded in `08`.

## WHAT THIS DOES NOT SHOW

- Whether the kit wins Juan or the League (step 14). A second seed: every arm is one trajectory, replayed.
- The budget-close arm with the kit on (optional in the design; not run; gate rows P7/P18 cover the close).

## THE REVIEW

Three lenses on `ea75fe1f`, each finding put to a refuter: design conformance, a second adversarial gate pass, and
the live integration. **The production half conformed to E1-E11**; 12 findings were confirmed or plausible, and 1 was
refuted.

| Id | Verdict | What | Fix |
|---|---|---|---|
| **DC1 / LI-1** (medium) | CONFIRMED | The driver's `kit_as_forecast` sat in `common`, and the lever rule did not model `POKEBOT_R23_FAULT_BALLRAISE`. So with the kit on, `EB_EXPECT=ballfail` could never pass, and `budget` failed a correct close. It is the same class as the design review's R4 | The lever rule models BALLRAISE (`R kit_ballraise`: the kit walks and buys nothing). `ballfail` became kit-aware: its premise admits a kit-only walk, its label is the driver's `topoff_label`, and it grades `kit_phase_failed` and `both_keys_memoised`. `kit_as_forecast` is graded after `common` for every EXPECT but `budget` |
| **DC2** (low) | CONFIRMED | A set that planned no line logged the OTHER set's cost (S-ON: `[BALLS-BUY] why=topoff-none … money=22166->20966`), against E5's sentence | That set's line and report read the wallet unchanged (9b's `topoff-none` X->X). A set that bought reads the wallet after the one call (10a's convention). **E5 is amended**: the ball line stays whenever the balls are on (P5/P1 had pre-registered it) |
| **KT2-STUB1 / X2** (medium) | CONFIRMED | `_phase`'s kit dict lacked the keys production's forecast writes, and its `_inputs` floor was a constant. A counter reading the FORECAST's floor, wallet or wants passed every row; after a short basket it would spend ₽14,834 below the live floor | The stub carries `FORECAST_KEYS`, and its floor follows the fake bag. New row P23 (a short basket: live floor ₽43,000). X2 → {P23}, X3 → {P15, P19, P20, P21}, X6 → {P2} |
| KT2-X1 (low) | CONFIRMED | PD1's fix without its outcome guard was invisible | P24, PD1's negative twin; X1 → {P24} |
| KT2-X4 (low) | CONFIRMED | No forecast row bought more than one unit, so an HP target of 1 passed | O13 (wants Hyper 2; the ₽6,000 cap buys Hyper 4 + Full Heal 2); X4 → {O13} |
| KT2-X5 (low) | CONFIRMED | The counter picking its ball from the STATIC list passed (P20 runs at spare 18) | P25 (spare 8, no ball on the live list); X5 → {P25} |
| KT2-Z1 (low) | CONFIRMED | `production_kit_forecast_ok` normalising a missing forecast to [] passed G3 | G3 +2 negatives; Z1 → {G3} |
| KT2-D1, D2 (low) | CONFIRMED | The buy branch's `kit_attributed` and the kit branch's outcome label could be hollowed | Pinned in A5; DK1, DK1b, DK2 → {A5} |
| **LI-2** (low) | PLAUSIBLE | A spare that DROPS on the crossing (a catch en route) lets the reserve Ultra take the kit's budget; the kit was then memoised as "wasted" for the rest of the run. Production followed E5's rule word for word, so the flaw was in the rule | The kit is "wasted" only when its live wants are empty or the visit bought nothing. New row P26; WASTE → {P26}. **E5 is amended** |
| LI-3 | REFUTED | "The counter's kit-read fallback cannot be reached by the live lever" is true, but nothing claimed it could; the gate comment is about WHERE the stub raises | — |

- **Also fixed:** the handoff's resume pointers still said "no 10b code exists" after `ea75fe1f`; they were corrected
  in the fix commit.
- **Not taken:** a live arm buying balls and kit in ONE call at Sootopolis (the live lens's coverage gap). Neither
  fixture reaches a non-empty split next to a kit: the kit's full want costs the whole ₽6,000 cap. The combined call
  is proven live at Rustboro (10a K-ON) and by gate row P4 here.
- **The gate after the review:** ALL PASS, 160 checks (69 rows, 88 mutants, 3 no-ops). Every red set equals the set
  written before the run (`evidence/2026-09-30-kittopoff10b-REVIEW-GATE.txt`; run 4 was stopped on one A5 pin string
  mis-spelled, not a set). The differential re-run: 0 differ, both planted controls caught
  (`evidence/…-REVIEW-DIFF.txt`).
- **Found while running it: the gate was too slow for its suite.** It took 15-18 minutes against `run_gates.py`'s
  300 s FAST timeout, so the standing suite would have read it as a FAILURE. 97% of the time was `ast.parse` of the
  30,000-line harness, twice per mutant. A4/A5 now parse the driver's class only, once per source text: 6 SECONDS,
  every red set identical. The 9b gate had the same cost (220 s, 73% of its timeout); a parse cache took it to 26 s,
  with its output byte-identical.
- **The re-run and the four new arms** (DC1 reproduced on the `ea75fe1f` driver, then fixed): EXPECTED lines filed
  first in `tools/story-dev/evidence/2026-09-30-kittopoff10b-REVIEW-RERUN.txt` (pending: not yet run).
