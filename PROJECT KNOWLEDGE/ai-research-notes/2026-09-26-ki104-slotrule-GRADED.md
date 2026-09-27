# 2026-09-26 — KI-104 (the HM teach's slot rule): GRADED

> Predictions: `2026-09-26-ki104-slotrule-PREDICTIONS.md` (`e58ee1c8`, BEFORE the drives). Evidence:
> `tools/story-dev/evidence/2026-09-26-ki104-K1-oldslot.*`, `-K2-newslot.*`.

| # | Result | vs prediction |
|---|---|---|
| **K1** (`POKEBOT_HMTEACH_FAULT_OLDSLOT=1`) | `learned=True`, `replaced=['Double Kick']` | **as predicted** (the old rule; as H2b/H2c) |
| **K2** (the new picker) | `learned=True`, `replaced=['Scratch']`; Blaze Kick and Double Kick kept; the verified scroll corrected HM03 → HM04 | **as predicted** |

**Why Scratch:** Strength (Normal 80, the incoming HM) strictly dominates Scratch (Normal 40), so nothing is lost —
tier 2 of `choose_hm_slot`. Double Kick (Fighting STAB, 30 × 2) and Blaze Kick (Fire STAB) are never reached.
| **K3** (`ch23teach` on `post_badge8.ss1`, the new picker — the review asked for it) | `ACCEPTANCE: PASS`; Wailmer `[Dive, Surf, Water Gun, Rollout] -> [Dive, Surf, Waterfall, Rollout]` — **lost Water Gun** (dominated by Surf), Rollout (the only Rock move), Dive and Surf kept | **as predicted** (the 2026-09-03 PASS lost Rollout under the OLD rule) |

⚠ The pinned `post_waterfall.ss1` was captured from the OLD-rule run (Rollout lost, Water Gun kept). It stays a valid STATE
for the drivers that start from it; it is simply no longer the state production would produce at that point.
**Not shown:** the other live shapes (Mud Shot, Low Kick, Earthquake) were not driven — they are gate rows
(`probe_hmslot_rule.py` S1). The next batch after the merge should show no `learned X (lost <its only move of a type>)`
lines where a dominated or off-type move was available.
