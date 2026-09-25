# §Ch24 EGRESS PROOF (`C-CANCONTINUE`) — PREDICTIONS, FILED BEFORE THE DRIVE

**Date:** 2026-09-25. **Item:** `#24-championleg`. **Status at filing:** the code is written, the
ratchets are green, and **NOTHING HAS BEEN DRIVEN YET.**

## WHY THIS EXISTS

`fight_the_champion` ends in `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)` — **the player's bedroom**
(MEASURED: `usable_at` in `evidence/2026-09-25-ch24gauntlet-PASS.txt` reads map `(1,1)` tile `(4,2)`).
`C-HOME`/`C-USABLE` assert seven conjuncts and **none of them is "can the bot leave"**.
‼ §Ch15 ended four floors underground, §Ch18 on an eleven-tile island, §Ch19 in a living room —
**all three PASSED THEIR OWN TESTS.** That is the shape this reading closes.

## WHAT CHANGED

1. `HOME_MAP` is now asserted **POSITIVELY** inside `_settled()` (`not CHAMP and not HOF` is a
   negative identity that holds on ~400 other maps).
2. New reading **`C-CANCONTINUE`**: a real `calculate_path` from the end tile to `HOME_STAIRS (7,1)`.
3. New fault arm `POKEBOT_CH24_FAULT_NOEGRESS=1`, read in PRODUCTION.

## PREDICTIONS — GRADE THESE AFTERWARDS, HONESTLY

| # | Prediction | Falsifier (what would mean the build is WRONG) |
|---|---|---|
| P1 | The happy arm takes **all ELEVEN** champion readings, `C-CANCONTINUE` included, `ACCEPTANCE: PASS`. | `C-CANCONTINUE` in `missing` on the happy arm ⇒ either `(7,1)` is not the stairs, or the bot genuinely cannot leave — BOTH are results worth having, neither is a driver bug. |
| P2 | `egress_waypoints` is a **small positive integer** (roughly 3–8: the bedroom is tiny). | A huge number ⇒ the path is not what I think it is. `None`/`<unsized>` ⇒ the return type is not a list (telemetry only, not a failure). |
| P3 | The FAULT arm (`=1`) **FAILS**, raising `NO PATH to the stairs`, with `C-CANCONTINUE` in `missing` and `egress_fault_armed=True`. | If the fault arm **PASSES**, `(0,0)` is reachable and the arm is not a control at all — I must pick a genuinely unreachable target. ⛔ A guard whose arm cannot fail is DECORATION. |
| P4 | The fault arm fails **at the egress check specifically** — `C-USABLE` is still taken, only `C-CANCONTINUE` is missing. | Failing EARLIER means the arm perturbed something other than the probe (it must only change `_target`). |
| P5 | The positive map assertion does not change the happy path: `C-HOME` is still taken at the same place. | If `C-HOME` now times out, `VR._on_map(HOME_MAP)` disagrees with the measured `(1,1)` ⇒ my map constant is wrong. |

## ⚠ WHAT THIS DRIVE DOES **NOT** PROVE

* It does **not** prove the bot can walk out — only that a PATH EXISTS. Actually walking out
  (stairs → 1F → front door → Littleroot) belongs to the dex-hunt chapter.
  ⛔ `descend_and_leave_players_house()` is **INTRO-ONLY** and must NOT be reused verbatim
  post-game: it waits on Mom's chat and rides out the Petalburg-Gym TV scene, neither of which
  fires after the credits.
* It does **not** close the `floor=65` gap — see below.

## ⛔ A SEPARATE, UNCLOSED GAP, RECORDED HONESTLY (found by an adversarial review, 2026-09-25)

**The training leg at production's `floor=65` has NEVER been driven as part of this chain.** The
gauntlet PASS ran at `CH24_ENTRY_FLOOR=1`, which makes `train_for_league` a documented no-op
(`latch_calls=2` rather than 3 is the fingerprint). Training is proven separately by
`--driver ch24train`. ⇒ by the project's own *"each piece works is not the chain works"* rule — the
very rule that justified building `run_the_gauntlet` — **training-at-65 feeding this fight chain as
ONE trajectory is still two separately-proven halves.** Filed, not hand-waved.
