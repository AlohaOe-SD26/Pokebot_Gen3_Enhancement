# 2026-09-29 — USER RULING 24 step 3 GRADED: `POKEBOT_R24_CATCHTRAIN` catches during a training grind and keeps the trainee as lead; OFF is unchanged

> Predictions: `2026-09-29-r24catchtrain-PREDICTIONS.md` (`9651365d`, before the code). Code: `c769c010`. Every arm ran
> `storyresume` on `r20_badge1_party1_gym.ss1` with `POKEBOT_R20_OPENFENCE=1`, `--set-balls 30`, 90,000 frames and
> `random.seed(9)`. Evidence: `tools/story-dev/evidence/2026-09-29-r24catchtrain-*.txt`.

## RESULTS — every prediction held

| Arm | Env | Reading | Verdict |
|---|---|---|---|
| M0 (measure) | `main` `57b46186` | `f175100 [DEXFENCE] skip #276 Taillow — a training grind is in progress`, party at full HP (58/58) | the discriminator |
| **G-OFF** | CATCHTRAIN unset | 0 differing `[DEXFENCE]`/`[CATCH]`/`[BATTLE] started` lines against M0; no `trainee` line | ✅ OFF unchanged (one trajectory, replayed) |
| **G-ON** | `CATCHTRAIN=1` | 0 differing lines before f175100, **both earlier health refusals included** (the lift is one gate wide). At f175100: `[CATCH] trainee lead=Marshtomp#550A9BE6`, then `[CATCH] start kind=dex sp=Taillow#276 … party=1/6 spare=32`, `end=caught … dest=party pid=118FF55F party=2/6`; next battle: **`trainee-after lead=Marshtomp#550A9BE6 … same=True`** | ✅ |
| **G-ROT** (fault) | + `FAULT_ROTATE=1` | 0 differing lines against G-ON | ✅ VACUOUS, as pre-registered: the lead never fainted. The rotation proof is the gate's L1 |

## SEEN, NOT MEASURED (one trajectory)

- **The training cost barely moved.** The grind ended at f195102, against G-OFF's f192380: about 2,700 frames later.
  The new L8 Taillow was NOT pulled into the Lv 19 grind. The existing catch-up gap
  (`StoryMode.TRAIN_CATCHUP_GAP = 6`) leaves a far-below catch to level organically.
- **A fresh catch led a boss fight.** Before the Rustboro rival, `_lead_best_matchup(["Grass"])` put the L8 Taillow in
  front, because Flying resists the rival's Grass starter. It opened on the rival's L13 Wingull (`[TURN 0] Taillow L8
  … vs Wingull L13`).
  - Both arms lost this fight: G-OFF with a lone Marshtomp, G-ON with the Taillow leading. So this run shows no harm.
  - It is the open risk the build spec's §5 names, seen live once.
  - ⛔ **The user has ruled on this area** (`#24-leadpolicy`, `06` 2026-07-29): options A and C were adopted, and
    **option B, weighting the level gap, was explicitly NOT adopted.** So this is recorded as a DATA POINT for that
    item, not as a proposal to revisit B.

## WHAT THIS DOES NOT SHOW

- **C3 live.** No lead fainted in a training catch. The gate's L1 (with its ROTATE fault arm) proves it.
- **How often a catch mid-grind costs training time, or hits the frame ceiling.** That is the batch.
- **Steps 4 and 5** (survival mode, the faint bail).
