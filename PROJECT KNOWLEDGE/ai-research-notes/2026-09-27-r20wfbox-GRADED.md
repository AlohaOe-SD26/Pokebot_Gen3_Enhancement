# 2026-09-27 — RULING 20 Phase 1, increment B (Waterfall box-first): GRADED

> Predictions: `2026-09-27-r20wfbox-PREDICTIONS.md` (`4f410744`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-wfboxfirst-{W1-saturated-fix,W2-saturated-skipfix,W3-nobox-fix,W4-ordinary-fix,W5-ordbox-fix,W6-hmpcfirst-regression}.txt`
> + `.stdout.txt`. Fixtures `post_badge8.ss1` (PINNED, md5 `723d94cc…`) and `fortree_gym_wedge.ss1` (PINNED,
> `87d390d7…`), both asserted. Drivers `--driver wfboxfirst` and `--driver hmpcfirst`.

## RESULT — all six as predicted

Graded on the recorded ACTIONS by PID: `_withdraw_hm_learner`, `teach_hm_move` and `PCAction.deposit_pokemon_to_box`.
The expected deposit was computed before the run with increment A's `make_room_victim`. The created Marill gets a
random PID per run, which the driver reads back.

| Arm | Wailmer's moves | Box | Withdrawn | Taught | Deposited | Verdict |
|---|---|---|---|---|---|---|
| **W1** saturated / fix | [Dive, Surf, Cut, Flash] | Marill | **Marill** | Marill (lost Water Gun) | **Zigzagoon 33CB74C3** | **PASS**: Wailmer still holds Dive and Surf; ends at SOOTOPOLIS (43,32), outside the centre, 4 non-adjacent exits reachable |
| **W2** saturated / `skipfix` | same | Marill | nothing | nothing | nothing | **PASS**: the refusal says "four HM moves" and names Marill's PID; no trip; box unchanged |
| **W3** nobox / fix | same | empty | nothing | nothing | nothing | **PASS**: "four HM moves" + "The box holds no usable Waterfall learner"; no trip |
| **W4** ordinary / fix | [Dive, Surf, Water Gun, Rollout] | empty | nothing | **Wailmer** (lost Water Gun) | nothing | **PASS**: no PC visit |
| **W5** ordbox / fix | same | Marill | **nothing** | **Wailmer** (lost Water Gun) | nothing | **PASS**: Marill still boxed; the party is tried before the box |
| **W6** regression `hmpcfirst` (default) | — | its Wailmer | its Wailmer | — | its make-room | **PASS**: all six readings, incl. `H-SLOT` (the returned slot points at the withdrawn carrier) |

## What this proves, and what it does not

- ⭐ **The box-first block is what collects the learner on the saturated shape.** W1 and W2 start from the same injected
  state; only the production arm differs. The old generic gate could not fire there: the saturated Wailmer is
  compatible, so `hm_learner_slot(HM07)` is not None.
- ⭐ **Box-first fires only when the party has no usable learner.** W5 has the same box as W1 but a spendable Wailmer, and
  it taught the Wailmer with no PC visit.
- ⭐ **The identity change in `_withdraw_hm_learner` holds on the generic path.** W6 is the rule-9 check: its return is now
  the slot of the PID it was asked for, and the old driver's slot reading still passes. In W1 the withdraw line names
  Marill; the old `hm_learner_slot` identity would have named the higher-level saturated Wailmer.
- The make-room deposit is increment A's rule: Zigzagoon, whose Surf Wailmer also holds. Never Wailmer, the only Dive
  carrier.
- ⚠ The ordinary teach now drops Water Gun, where the 2026-09-03 `ch23teach` evidence dropped Rollout. That predates this
  diff: the slot rule changed with KI-104 (2026-09-26), and this item does not touch `teach_hm_move`.
- **Not shown:**
  - Segment 22b end to end, and the §Ch23 run after a box-first teach;
  - frequency: how often an organic 8-badge run has a usable learner in the box. One trajectory per arm.
