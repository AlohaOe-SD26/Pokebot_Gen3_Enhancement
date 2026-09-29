# 2026-09-29 — USER RULING 24 step 2 GRADED: `POKEBOT_R24_CATCHHURT` catches while the party is hurt; OFF is unchanged

> Predictions: `2026-09-29-r24catchhurt-PREDICTIONS.md` (`2a14de6c`, before the code). Code: `572097f0`. Every arm ran
> `storyresume` on `post_mtpyre.ss1` for 120,000 frames under `random.seed(1)`. Evidence:
> `tools/story-dev/evidence/2026-09-29-r24catchhurt-*.txt`.

## RESULTS — every prediction held

| Arm | Env / balls | Reading | Verdict |
|---|---|---|---|
| M0 (measure) | unchanged code, 30 | `f3144418 [DEXFENCE] skip #353 Shuppet — party is not at full strength` | the discriminator |
| **G-OFF** | nothing, 30 | 0 differing `[DEXFENCE]`/`[CATCH]`/`[BATTLE] started` lines against M0; no `loss-filed` | ✅ OFF unchanged (one trajectory, replayed) |
| **G-ON** | `CATCHHURT=1`, 30 | 0 differing lines before f3144418. At f3144418: **`[DEXFENCE] CATCH #353 Shuppet … (goes to the PC box)`** and `[CATCH] start kind=dex sp=Shuppet#353 … party=6/6 box=0 spare=31`; the Shuppet was **caught** (2 balls, `dest=box`) | ✅ |
| **G-OFF9 / G-ON9** | nothing / `CATCHHURT=1`, 9 (spare 10) | both refuse the f3144418 Shuppet on the RESERVE; 0 differing lines between the two arms | ✅ the lift sits after the reserve |
| **G-LIFT9** (fault) | `CATCHHURT=1` + `FAULT_LIFTEARLY=1`, 9 | `[CATCH] start … sp=Shuppet#353 … spare=10`, then `[CATCH] end … end=bail res=RanAway thrown=0 … bail=reserve` | ✅ the live half of the gate's F1; never a caught Shuppet |

**Beyond the pre-registered start (recorded, not predicted).** With the flag on, the hurt party went on to catch Oddish,
Wingull and Torkoal into the box. A Geodude attempt ended `bail=faint`: the post-gym-1 first-faint bail still stands,
and removing it is step 5.

**The whiteout is not this change's.** G-OFF and M0 lose the same battle at f3171726 and white out at f3203108. G-ON
loses the corresponding battle at f3172629. No `[CATCH] loss-filed` line appears in any arm, because no catch battle
was lost. One visible cost of catching: at that loss G-ON's Zigzagoon is L7 against G-OFF's L12. The time spent
catching was not spent battling.

## WHAT THIS DOES NOT SHOW

- **C4 live.** No catch battle was LOST in these arms. C4 is proven by the gate's stubbed D1-D3 and its KINDLATE and
  TEAMLOSS fault arms.
- **How often a hurt catch costs a faint or a whiteout, and whether catching slows the story.** Those are the batch's
  questions.
- **Training (step 3), survival mode (step 4) and the faint bail (step 5).** Those are separate steps.
