# 2026-09-29 — USER RULING 24 step 3 (catch during a TRAINING grind, keep the trainee as lead): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/r24catchtrain`, cut from `main`
> `57b46186`. Spec: `2026-09-28-r23-25-DESIGN.md` step 3 (a NOTE). Ruling: `06`, USER RULING 24.

## THE CHANGE (planned)

- **`decide_dex_catch(..., lift_training=False)`.** When true, the post-gym-1 refusal "a training grind is in progress"
  is skipped; nothing else changes. The flag is `POKEBOT_R24_CATCHTRAIN=1` (default OFF), read per run into
  `StoryMode._r24_catchtrain`, and the adapter passes it.
- **C3.** `StoryDexCatchStrategy` records at construction whether swap-training is active, and whether the RUNNING mode's
  flag is on. If both hold, `choose_new_lead_after_battle` returns None: a faint in the catch no longer rotates a
  slot-based grind's trainee out of slot 0. Otherwise it returns the parent's answer. The pinned call site
  `return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()` is unchanged.
- **Flag-ON-only telemetry:** `[CATCH] trainee lead=…` when a dex catch starts during swap-training, and
  `[CATCH] trainee-after lead=… same=…` at the next battle start. That is the action C3 guards (rule 7).
- **Doc fixes in code:**
  - the training refusal's watchdog comment (the watchdog counts OVERWORLD frames only, and a party join resets it);
  - `roster.py`'s claim that every story strategy returns None from `choose_new_lead_after_battle`.
- **Fault arm:** `POKEBOT_R24_FAULT_ROTATE=1` restores the parent's rotation.
- **NEW gate `probe_dex_catch_training.py`:**
  - pure predicate cases, including a one-gate-wide check (hurt still refuses with only the training lift);
  - the AST wiring and the per-run read;
  - L1 (the strategy keeps the lead only when built during training with the flag on);
  - fault arms ROTATE, an adapter passing False, and a comment-only mention.

## THE DISCRIMINATOR, MEASURED (M0: `main` `57b46186`, observe-only)

`storyresume` on `r20_badge1_party1_gym.ss1` (`50af0f5c`), `POKEBOT_R20_OPENFENCE=1`, `--set-balls 30`, 90,000 frames,
`random.seed(9)`. A seed sweep of 2-9 found 9 the only seed that draws the Lv 19 grind. Evidence:
`tools/story-dev/evidence/2026-09-29-r24catchtrain-M0.txt`.

| Frame | Party HP | Verdict (OFF) |
|---|---|---|
| f144426 | Mudkip 21/46 | skip #290 Nincada — party is not at full strength |
| f166431 | Marshtomp 7/58 | skip #276 Taillow — party is not at full strength |
| f173587 | — | `[STEP] training the team to Lv 19` |
| **f175100** | **Marshtomp 58/58 (FULL)** | **skip #276 Taillow — a training grind is in progress** |

At f175100 every later gate passes:
- spare is 32 (> 10);
- the health check passes at full HP;
- there are 0 Taillow attempts (the f166431 Taillow was refused on health, not attempted);
- the catch rate is high;
- `OPENFENCE` admits a party join at party 1.

## THE ARMS AND THEIR PREDICTED READINGS

All arms run `r20_badge1_party1_gym.ss1` with `POKEBOT_R20_OPENFENCE=1`, `--set-balls 30`, 90,000 frames and
`random.seed(9)`.

| Arm | Env | Predicted |
|---|---|---|
| **OFF** | (CATCHTRAIN unset) | M0 replayed: 0 differing `[DEXFENCE]` / `[CATCH]` / `[BATTLE] started` lines; no `trainee` line |
| **ON** | `POKEBOT_R24_CATCHTRAIN=1` | identical to OFF before f175100, **including both health refusals** (the lift is one gate wide). At f175100: `[DEXFENCE] CATCH #276 Taillow — dex catch #276 (joins the party)`, `[CATCH] trainee lead=Marshtomp#550A9BE6 …`, `[CATCH] start kind=dex sp=Taillow#276 … party=1/6`. At the next battle: `[CATCH] trainee-after … same=True`. A lead faint against an L8 Taillow at 58/58 is not expected |
| **ROT** (fault) | `CATCHTRAIN=1` + `POKEBOT_R24_FAULT_ROTATE=1` | identical to ON. **The live rotation fault is VACUOUS unless the lead faints in the catch; the rotation proof is the pure gate's L1.** Stated in advance |

**Recorded, not predicted.** If the Taillow joins the party, the "whole team" grind now has a second member below
Lv 19. How much longer training takes because of that, and whether it hits the frame ceiling, is the composition
effect the `#27-enroutejoin` audit flagged, and a batch question.

## FALSIFIERS

- OFF differs from M0.
- ON differs from OFF before f175100, or either health refusal changes: the lift is not one gate wide.
- ON refuses the f175100 Taillow: the flag does not reach the fence.
- A `trainee` line appears in OFF: the telemetry leaked.
- ON's `trainee-after` reads `same=False` with no faint in the catch battle: something other than the rotation moved
  the lead.

## WHAT THIS DOES NOT SHOW

- **C3 live**, unless the lead faints (see ROT).
- **The effect on training duration and the frame ceiling.** That is the batch.
- **Steps 4 and 5** (survival mode, the faint bail).
