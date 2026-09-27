# 2026-09-27 — RULING 20 Phase 1, increment B (Strength box-first): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive. Branch `wt/r20phase1`. Recon: `2026-09-27-ruling20-incB-RECON.md` (a NOTE).
> Gate already green: `probe_r20_strengthbox.py` (pure; 4 built-in fault arms).

## THE CHANGE UNDER TEST

`ensure_strength_learner(heal_centers=())`: when no PARTY member can learn HM04 and a BOXED one can, and centres are
offered, collect the head of `boxed_hm_learner_pids(HM04, avoid=HM07)` on one Poké Centre visit, then teach it (or not,
if it already knows Strength). The heal-stop caller in `travel_to_magma_hideout_door` offers `(center,)`; the
in-hideout caller offers none and stays party-only.

## THE DRIVE — `--driver strengthbox`

- Fixture: `strength_boxfirst_mauville.ss1` (PINNED 2026-09-27, md5 `ba23ca04…`, a copy of the volatile
  `magma_1f_fail.ss1`). Read before this file was written: MAUVILLE_CITY (22,6), badges 1-6, HM04 in the bag, box empty.
  The party:
  - Sceptile 863B0917 L44 — can learn HM04, cannot learn HM07; holds the only Rock Smash
  - Zigzagoon 33CB74C3 L7 — the only Surf carrier
  - Swellow 0B30A747 L41
  - Skitty 5CCCD8BE L17
  - Mightyena 5C96EA9B L44 — KNOWS Strength
  - Castform C978D14E L35
- Injection (`debug_write_box_slot` with explicit slot indices, a frame yielded between writes; `debug_write_party`).
  A created Swampert L50 can learn HM04 AND HM07.
- Recorded ACTIONS, by PID: `_withdraw_hm_learner` calls, `teach_hm_move` calls, `PCAction.deposit_pokemon_to_box`.
- The expected make-room deposit is computed BEFORE the run with increment A's `make_room_victim`. The recon measured
  that exact party (the four non-learners + two Wingull L20) as **Skitty 5CCCD8BE**.

## PREDICTIONS

| Case (`SB_CASE` / `SB_EXPECT`) | Box / party after injection | Predicted |
|---|---|---|
| **teach / fix** | box [Swampert, Sceptile]; party = the 4 non-learners + 2 Wingull (6) | withdraw **[863B0917 Sceptile]**; one deposit, **Skitty 5CCCD8BE**; teach **[863B0917]**; Sceptile knows Strength; Swampert still boxed; ends on MAUVILLE_CITY with a non-adjacent exit reachable |
| **teach / nopref** (`POKEBOT_R20_FAULT_NOLANDPREF=1`) | same | withdraw **[Swampert]** (level order); deposit Skitty; teach Swampert; **Sceptile still boxed** |
| **teach / skipfix** (`POKEBOT_HMPCFIRST_FAULT=skipfix`) | same | the refusal *"no party member can learn HM04"* naming 863B0917; **no withdraw, no deposit, no teach**; still at (22,6); box unchanged |
| **knower / fix** | box [Mightyena, Sceptile]; party = the 4 non-learners (4) | withdraw **[5C96EA9B Mightyena]** (knows it, ranks first); **no deposit** (room); **no teach**; Sceptile still boxed |
| **party / fix** (the ordinary case) | box [Swampert]; party = the fixture minus Mightyena (5) | **no withdraw, no deposit**; teach **[863B0917]** from the party; Swampert still boxed |
| **sitetwo / fix** (no centres) | as teach | the refusal naming 863B0917 and *"no Poké Centre offered here"*; nothing moves |

**Premise conjuncts (every case):** the fixture premise above holds at runtime; the injection put exactly the planned
number of mon in the box; for every case except `party`, `land_hm_learner_slot(HM04)` is None after the injection.

**Discriminators, computed before the run:**
- teach/fix vs teach/skipfix: the same injected state (no party learner, two boxed learners). Only the production arm
  differs, so a withdraw vs a refusal separates them.
- teach/fix vs teach/nopref: `boxed_hm_learner_pids(HM04, avoid=HM07)` = [Sceptile, Swampert]; by level alone,
  [Swampert L50, Sceptile L44]. The heads differ.
- party vs teach: a party learner exists (`land_hm_learner_slot` = Sceptile's slot) vs none.

## FALSIFIERS

- **A withdrawn or taught PID differs from the table** in any arm: the rule or its wiring is wrong. This is a RESULT, not
  a driver failure; read the failing line first.
- **nopref behaves like fix:** the preference is not what the arm removes.
- **skipfix withdraws anything, or moves:** the block the arm disarms is not what withdrew the mon.
- **party withdraws:** box-first fires while a party learner exists, a regression on the ordinary path.
- **teach/fix deposits Zigzagoon:** the make-room boxed the only Surf carrier (increment A's rule is broken).

## WHAT THIS DOES NOT SHOW

- The heal loop end to end (from `post_mtpyre.ss1`, the Lilycove stop first, then Mauville). The driver calls the
  production function with the centre that loop passes.
- The in-hideout caller live. `sitetwo` calls the same function with no centres, which is what that caller does.
- Frequency. One trajectory per arm.
