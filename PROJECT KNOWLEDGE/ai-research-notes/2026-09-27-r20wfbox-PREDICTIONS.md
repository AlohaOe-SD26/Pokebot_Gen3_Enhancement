# 2026-09-27 — RULING 20 Phase 1, increment B (Waterfall box-first): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive. Branch `wt/r20phase1`. Recon: `2026-09-27-ruling20-incB-RECON.md` (a NOTE), site "waterfall".
> Gate green before the drive: `probe_r20_wfbox.py` (pure; 3 built-in fault arms).

## THE CHANGE UNDER TEST

- `ensure_waterfall_learner(heal_centers=())`: when no PARTY member is compatible AND has a non-HM slot to spend, and a
  BOXED mon can take Waterfall now (knows it, or compatible with a spendable slot: `_boxed_waterfall_learners`), collect
  the head on one visit to the offered centre, then teach it (or not, if it already knows Waterfall). The Segment 22b
  caller offers Sootopolis.
- The refusal now separates "no compatible member" from "every compatible member is saturated", and says what the box
  check found.
- `_withdraw_hm_learner` now returns and names the slot of the PID it was asked for. It used to use
  `hm_learner_slot(item)`, which on this site names the saturated Wailmer (higher level) instead of the withdrawn mon.
- ⛔ Why the generic PC-first gate cannot serve here: on the measured shape the saturated learner is compatible, so
  `hm_learner_slot(HM07)` is not None and that gate never fires.

## THE DRIVE — `--driver wfboxfirst`

- Fixture `post_badge8.ss1` (PINNED, md5 `723d94cc…`, asserted). Per the recon: SOOTOPOLIS_CITY (31,33), badges 1-8, HM07
  in the bag, box empty. The only HM07-compatible member is Wailmer FA51ECF3 L40 [Dive, Surf, Water Gun, Rollout]. The
  driver asserts all of this at runtime.
- Recorded ACTIONS, by PID: `_withdraw_hm_learner`, `teach_hm_move`, `PCAction.deposit_pokemon_to_box`.
- The expected make-room deposit is computed BEFORE the run with increment A's `make_room_victim`. The recon measured
  **Zigzagoon 33CB74C3** (L19, dead weight; its Surf is also on Wailmer, so it is not a sole carrier).

## PREDICTIONS

| Case (`WF_CASE` / `WF_EXPECT`) | Injection | Predicted |
|---|---|---|
| **saturated / fix** | Wailmer rebuilt with [Dive, Surf, Cut, Flash] (same PID); a created Marill L30 in box slot 0 | withdraw **[Marill]**; one deposit, **Zigzagoon 33CB74C3**; teach **[Marill]**; Marill knows Waterfall; Wailmer keeps Dive and Surf; ends on SOOTOPOLIS_CITY with a non-adjacent exit reachable |
| **saturated / skipfix** (`POKEBOT_HMPCFIRST_FAULT=skipfix`) | same | the refusal names Marill's PID and says "four HM moves"; **no withdraw, no deposit, no teach**; position unchanged; box unchanged |
| **nobox / fix** | saturated Wailmer, nothing boxed | the refusal says "four HM moves" and "The box holds no usable Waterfall learner"; nothing moves |
| **ordinary / fix** | none | **no withdraw, no deposit**; teach **[Wailmer FA51ECF3]**; it keeps Dive and Surf (the pre-change behaviour, rule 9) |
| **ordbox / fix** | none, plus Marill boxed | as ordinary: Wailmer taught from the party, **no withdraw**; Marill still boxed (the party is tried before the box) |
| **regression: `--driver hmpcfirst`** (default arm, `fortree_gym_wedge.ss1`) | its own Wailmer injection | still **PASS**: its `H-SLOT` reading grades that the slot `_withdraw_hm_learner` returns points at the withdrawn carrier. That return value changed (the PID asked for, not `hm_learner_slot`), so this is the rule-9 check on the generic PC-first path |

**Premise conjuncts (every case):** the fixture premise holds; the injection's box content is as planned.

**Discriminators:**
- saturated/fix vs saturated/skipfix: the same injected state; only the production arm differs.
- saturated vs ordbox: the same box (Marill); only Wailmer's moveset differs (saturated vs spendable). This separates
  "box-first fires because the party's learner is saturated" from "box-first fires whenever a learner is boxed".

## FALSIFIERS

- **A withdrawn, taught or deposited PID differs from the table:** a RESULT; read the failing line first.
- **ordbox withdraws:** box-first fires while a usable party learner exists, a regression on the ordinary path.
- **skipfix withdraws or moves:** the block the arm disarms is not what withdrew the mon.
- **saturated/fix deposits Wailmer:** the make-room boxed the only Dive carrier (increment A's rule broken).

## WHAT THIS DOES NOT SHOW

- Segment 22b end to end (the chapter guard after the teach); the driver calls the production function with the centre
  that caller passes.
- The whole §Ch23 run after a box-first teach.
- Frequency: how often an organic 8-badge run has a usable learner boxed. One trajectory per arm.
