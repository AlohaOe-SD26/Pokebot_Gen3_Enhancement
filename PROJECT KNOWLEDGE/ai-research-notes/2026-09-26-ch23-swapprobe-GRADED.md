# 2026-09-26 — `#24-ch23training` S-ARM — GRADED: PRODUCTION SWAP-TRAINING BANKS EXP FOR A L13 MULE AT +27

> Grades `2026-09-26-ch23-swapprobe-PREDICTIONS.md` (committed in `4e194510`, BEFORE the drive).
> Evidence, committed: `tools/story-dev/evidence/2026-09-26-ch23swapprobe-{SWAP,CONTROL}.txt` (+ stdout excerpts).
> Instrument: `--driver ch23swapprobe` from `post_ever_grande.ss1 --inject-hmmule` (md5 `18203e997edc`,
> asserted first). Party: Sceptile L51, Zigzagoon L19, Swellow L42, Wailmer L40, Mightyena L44, **MULE
> Marill L13** (Castform L36 displaced). Production `train_team(17, slots={0}, grass=TRAIN_SPOT_1F,
> heal_center=EvergrandeCity)` inside a 350,000-frame purse.

## The readings

| | SWAP (production strategy) | CONTROL (`StoryItemBattleStrategy`) |
|---|---|---|
| strategy installed | `SwapTrainBattleStrategy` | `StoryItemBattleStrategy` |
| battles | **5** | 62 |
| battles the mule led / rotated out of | 5 / **5** | 61 / **0** |
| decisions | RotateLead 6, UseMove 7 | UseMove 209, RunAway 2 |
| mule EXP | 1,757 → 4,032 (**+2,275**, 455 / battle) | 1,757 → 1,757 (**+0**) |
| mule level | 13 → **17** (target reached, `purse_finished=True`) | 13 → 13 (purse EXHAUSTED at 350,411 frames) |
| mule fainted at a battle's end | **0** | **56** |
| frames | 18,539 | 350,411 |
| whiteouts | 0 | 0 |

## Grades

| # | prediction | verdict |
|---|---|---|
| S0 | premise: MULE L13 in slot 0 (PID-verified), a finisher ≥ L40 | ✅ both arms (`premise_ok=True`, finisher L51) |
| S1 | RotateLead in ≥80 % of mule-led battles | ✅ **5 of 5 (100 %)** |
| S2 | the mule's EXP (by PID) rises and it reaches L17 in the purse | ✅ +2,275, L17 in 18,539 frames |
| S3 | the mule never faints; 0 whiteouts | ✅ 0 and 0 |
| S4 | control: 0 RotateLead; the mule faints or gains far less | ✅ 0 RotateLead, 56 faints, **+0 EXP** — it reproduces the 2026-09-08 "stepping is refuted" drive exactly, which is now shown to be an artifact of that driver not installing swap-training |
| S5 | EXP/battle ≈ half a solo share (~390) | ⚠ **455, n=5** — within the noise of 5 L36-40 wilds and far closer to half (~388) than to a solo share (~775). Not refuted; not precisely measured. |

## What this settles, and what it does not

* ✅ **The class-1 premise of the chosen design (chunked training) is TRUE:** production swap-training
  fires at +27, the mule is switched out before the foe moves, never takes a hit, and banks EXP.
* ✅ **The 2026-09-08 stepping refutation is now a MEASURED artifact**, not just a withdrawn one: its
  shape (no swap strategy) is this CONTROL arm, which gains nothing.
* ⚠ **Cost, rough:** ~3,700 frames per swap battle (18,539 / 5). At 455 EXP/battle, Marill L13→47
  (81,301 EXP) is ~179 battles ≈ **~0.66M frames** (≈3 h at ×1), vs the estimator's full-EXP 406,972.
  Above ~L38 the trainee out-levels L≤40 wilds and trigger 1 stops firing, so it solos for full EXP
  there — the true figure is somewhat lower. ⚠ One party, one trajectory per arm (rule 8).
* ⛔ **NOT tested here:** evolution mid-chunk (Marill → Azumarill at L18 — the target was 17 on
  purpose), a whiteout during the grind, the money margin, or the L26-37 team-member class.
