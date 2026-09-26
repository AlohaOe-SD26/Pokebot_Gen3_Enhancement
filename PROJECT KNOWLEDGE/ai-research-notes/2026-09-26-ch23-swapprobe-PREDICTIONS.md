# 2026-09-26 — `#24-ch23training` S-ARM — PRE-REGISTERED PREDICTIONS (written BEFORE the drive)

> The decisive arm named by both judges of the design panel (`2026-09-26-ch23training-DESIGN.md`):
> **does PRODUCTION swap-training bank EXP for a L13 mule against Victory Road 1F's L36-40 wilds?**
> If it does not, the winning design (chunked training) is dead before a line of it is written.

## The instrument

`--driver ch23swapprobe` from `post_ever_grande.ss1 --inject-hmmule` (adds Marill L13, nickname MULE,
carrying Surf; displaces the last slot if the party is full). The driver resolves the MULE by nickname
→ PID, rotates it to slot 0 with production's `_rotate_lead_safely` and VERIFIES the lead PID, then runs
PRODUCTION's `train_team(target, slots={0}, grass=TRAIN_SPOT_1F, heal_center=EvergrandeCity)` — the exact
call `train_for_victory_road` makes — inside `_yield_bounded_by_frames(…, purse)`. Target = MULE level + 4
(L17), deliberately BELOW Marill's L18 evolution so a species change cannot confound the reading.
Its `on_battle_started` mirrors production: `SwapTrainBattleStrategy` when
`swap_train_active() and encounter is not None`, else `StoryItemBattleStrategy`. Every `decide_turn`
is counted (action kind + the acting mon), so the grade rests on the ACTION, not the candidate.
Control arm: `CH23SWAP_CONTROL=1` installs `StoryItemBattleStrategy` always (the 2026-09-08 shape).

## Predictions

| # | arm | prediction | falsifier |
|---|---|---|---|
| S0 | both | PREMISE: MULE present at L13 in slot 0 (PID-verified) and a party member ≥ L40 exists (a capable finisher) | premise fails ⇒ the run measures nothing; fix the fixture, do not grade |
| S1 | S | ≥1 `RotateLead` decision while the MULE is the active mon, in ≥80 % of wild battles it led | 0 RotateLead ⇒ swap does not fire at +27 in production; Design 1's class-1 premise is FALSE |
| S2 | S | the MULE's `total_exp` (by PID) INCREASES, and it reaches L17 within the purse | no EXP ⇒ the half share is not banked (e.g. a switched-out mon does not count); Design 1 dead |
| S3 | S | the MULE never faints (current_hp > 0 at every battle end) and 0 whiteouts | a faint ⇒ the switch does not beat the foe's first move |
| S4 | control | ZERO RotateLead decisions; the MULE either faints/flees or gains far less EXP per battle than S | the control also levels ⇒ the arms do not discriminate; S proves nothing about swap |
| S5 | S | EXP per battle ≈ half a solo share (~780/2 ≈ 390 at VR1F), i.e. the 0.501 divisor | ≫ or ≪ ⇒ the split model under the chunk estimator is wrong; re-derive before sizing chunks |

⚠ One fixture, one party, one trajectory per arm — this answers "CAN it", not "how often".
