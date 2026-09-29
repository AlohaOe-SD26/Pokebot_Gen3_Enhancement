# 2026-09-29 — USER RULING 24 step 2 (catch while HURT, plus catch-loss accounting): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/r24catchhurt`, cut from `main` `476c9958`.
> Spec: `2026-09-28-r23-25-DESIGN.md` step 2 (a NOTE, adversarially corrected). Ruling: `06`, USER RULING 24
> (2026-09-28): *"catching should always be available … even in training and wounded pokemon."*

## THE CHANGE (planned)

- **`decide_dex_catch(..., lift_health=False)`.** When true, the post-gym-1 refusal "party is not at full strength"
  is skipped. Nothing else changes: the runway, hunt-armed, hunt-walking, training, reserve, PC full, attempts and
  expected-throws gates all still apply. Before gym 1 nothing changes; that branch has no health check.
- **The flag.** `POKEBOT_R24_CATCHHURT=1` (default unset = OFF) sets `StoryMode._r24_catchhurt` per run. The adapter
  passes `lift_health=self._r24_catchhurt`.
- **Catch-loss accounting (C4)**, active only with the flag on:
  - `on_battle_ended` reads the catch kind BEFORE `_r20_catch_end` clears it.
  - A LOST battle whose kind is `dex` is filed in a per-run `_catch_defeat_counts`, NOT in `_defeat_counts` or
    `_loss_ko_history`. So a catch loss cannot trigger survival mode or count as a boss loss on that map.
  - `team`, `hm`, `counter` and `shiny` losses keep today's accounting.
  - A flag-gated `[CATCH] loss-filed` log line records each one.
- **Fault arms** (read in production code):
  - `POKEBOT_R24_FAULT_LIFTEARLY=1` admits at the training line's position, before every later gate;
  - `POKEBOT_R24_FAULT_KINDLATE=1` reads the kind after it was cleared, so C4 never fires;
  - `POKEBOT_R24_FAULT_TEAMLOSS=1` also files `team` losses under C4.
- **NEW gate `probe_dex_catch_anytime.py`:**
  - pure predicate cases;
  - the adapter keyword by AST;
  - stubbed `on_battle_ended` cases D1 (a dex loss filed apart when ON, counted when OFF) and D2 (a team loss
    counted in both);
  - each fault arm must turn its cases red.

## THE DISCRIMINATOR, MEASURED (M0: unchanged code `476c9958`, seeded, observe-only)

`storyresume` on `post_mtpyre.ss1` (`80602159`), `--set-balls 30` (spare 31 = Poké ×30 + Premier ×1), 120,000 frames,
`random.seed(1)`. Evidence: `tools/story-dev/evidence/2026-09-29-r24catchhurt-M0.txt`.

| Frame | Verdict (OFF) | Other gates (all pass) |
|---|---|---|
| **f3144418** | **skip #353 Shuppet — party is not at full strength** | party 6/6 (box path); no hunt; not training (training is checked before health); spare 31 > 10; attempts 0; catch rate 225 |
| f3215934 | skip #264 Linoone — not at full strength | (after divergence in ON) |
| f3233881 / f3254005 | Graveler / Torkoal — not at full strength | (after divergence in ON) |

## THE ARMS AND THEIR PREDICTED READINGS

All arms run `storyresume` on `post_mtpyre.ss1` for 120,000 frames with `random.seed(1)`.

| Arm | Env / balls | Predicted |
|---|---|---|
| **OFF** | nothing set, `--set-balls 30` | M0 replayed: 0 differing `[DEXFENCE]` / `[CATCH]` / `[BATTLE] started` lines. No `[CATCH] loss-filed` line |
| **ON** | `POKEBOT_R24_CATCHHURT=1`, `--set-balls 30` | the same lines as OFF before f3144418. At f3144418: `[DEXFENCE] CATCH #353 Shuppet — dex catch #353 (goes to the PC box)`, then `[CATCH] start kind=dex sp=Shuppet#353 … party=6/6 box=0 spare=31`. **Only the START is pre-registered.** The end (caught, a faint bail, lost, or a foe self-KO) is recorded. If it ends Lost, a `[CATCH] loss-filed` line appears and no survival-mode flee follows from it |
| **OFF-9 / ON-9** | as above, `--set-balls 9` (spare 10) | both: at f3144418 the Shuppet is refused on the RESERVE ("only 10 spare balls"), because the reserve comes before health. ON-9 starts no dex catch at f3144418 |
| **LIFT-9** (fault) | `CATCHHURT=1` + `POKEBOT_R24_FAULT_LIFTEARLY=1`, `--set-balls 9` | `[CATCH] start kind=dex sp=Shuppet#353 … spare=10`, then `[CATCH] end … end=bail … thrown=0 … bail=reserve` (the in-battle reserve bail fires on the first turn). **Never a caught Shuppet.** |

## FALSIFIERS

- OFF differs from M0: the flag-OFF path changed.
- ON refuses the f3144418 Shuppet, or differs from OFF before it: the lift does not reach the fence, or changes something
  earlier.
- ON-9 starts a catch at f3144418: the lift skipped the reserve.
- LIFT-9 shows no start at f3144418: the fault arm does not reach the fence (the live half of the gate's fault proof is
  vacuous).
- LIFT-9 catches the Shuppet: the in-battle reserve bail is broken.
- A `[CATCH] loss-filed` line appears in any OFF arm: C4 leaked.

## WHAT THIS DOES NOT SHOW

- **C4 live, unless the ON catch battle happens to be LOST.** C4 is proven by the gate's stubbed D1/D2 cases either
  way.
- **How often a hurt catch whites out, and what that costs.** That is the batch.
- **Training (step 3), survival mode (step 4) and the faint bail (step 5).** Those are separate steps.
