# 2026-09-27 — RULING 20 Phase 1, increment A (one deposit-victim rule): GRADED

> Predictions: `2026-09-27-r20makeroom-PREDICTIONS.md` (`b2bcc55a`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-r20mr-{P1-protect-fix,P2-protect-noprotect,R1-required-fix,R2-required-norequired}.txt`
> + `.stdout.txt`. Fixture `fortree_gym_wedge.ss1` (PINNED, md5 `87d390d7…`, asserted). Driver `--driver r20makeroom`.

## RESULT — all four arms as predicted

The deposit is graded on the recorded `PCAction.deposit_pokemon_to_box` call: the ACTION, by PID. The expected victim is
computed in the driver without the code under test.

| Arm | Owed counters | Rule consulted (required, protected → returned) | Deposited | Party after | Verdict |
|---|---|---|---|---|---|
| **P1** protect / FIX | Skitty | required=True, [Skitty] → Castform | **Castform (C978D14E) L25** | 5; Skitty still in | **PASS** |
| **P2** protect / `NOPROTECT` | Skitty | required=True, [] → Skitty | **Skitty (5CCCD8BE) L17**: the owed counter, the old live path | 5 | **PASS** |
| **R1** required / FIX | Skitty, Castform | required=True, [Skitty, Castform] → Swellow | **Swellow (0B30A747) L33**: the lowest member that is not a sole HM carrier (Sceptile holds Rock Smash, Zigzagoon holds Surf) | 5; both owed still in | **PASS** |
| **R2** required / `NOREQUIRED` | Skitty, Castform | required=True, [Skitty, Castform] → None | **nobody**: the old "nothing is safe" decline | **6** | **PASS** |

Frames per drive: P1 3,413, P2 3,431, R1 3,419, R2 2,677.

## What this proves, and what it does not

- ⭐ **Both defects exist on the live path, and both are fixed.**
  - (1) A counter still owed to its boss was boxable by the live make-room path (P2); now it is kept (P1).
  - (2) A team with no unprotected dead weight made the REQUIRED errand's make-room decline (R2); now it frees a slot
    (R1).
  Both run through production `heal_in_pokemon_center`'s `_needs_party_slot` piggyback.
- **Not shown:**
  - the HM errand end to end, i.e. `ensure_hm_learner_making_room` followed by the retry hunt;
  - `withdraw_from_box`'s own make-room step, which shares the rule and is wired statically (gate M3), but was not
    driven;
  - the badge expiry live. It is gated purely (M2) and never exercised by a drive;
  - frequency. One trajectory per arm.
- ⚠ **A policy consequence worth watching in batches:** the required fallback boxed Swellow, which is this party's
  future Fly learner. Box-first for Fly (Phase 1 item 5) is what makes that recoverable. Until it lands, a boxed Fly
  learner is only recovered by the ordinary HM paths.
