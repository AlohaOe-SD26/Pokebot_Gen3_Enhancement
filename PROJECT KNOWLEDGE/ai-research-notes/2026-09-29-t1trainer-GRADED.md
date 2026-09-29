# 2026-09-29 — design v2 step 5 (TID/T1) GRADED: the `[TRAINER]` lines name every trainer and predict every payout exactly; they change no battle; and ONE CONTROL RUN WAS NOT A CONTROL

> Predictions: `2026-09-29-t1trainer-PREDICTIONS.md` (`41f3118f`) plus its addendum (`0b8d5e25`), both before the code.
> Code: `5d11488c`. Every arm: `storyresume` on `r20_badge1_party1_gym.ss1`, `POKEBOT_R20_OPENFENCE=1`, `--set-balls 60`,
> 120,000 frames, `random.seed(1)`. Evidence: `tools/story-dev/evidence/2026-09-29-t1trainer-*.txt`. `-GRADER.txt`
> compares EVERY `[BATTLE]` line; `-CONTROLS.txt` is the determinism record.

## RESULTS — every prediction held (with the controls read correctly)

| Arm | Reading | Verdict |
|---|---|---|
| **T1** | **152 of 152 `[BATTLE]` lines identical** to the reproducing control, every line (started, ended, TURN, ITEM-FLOW, FAINT-CHOOSER). 11 `[TRAINER]` pairs (12 starts; the rival fight at f184993 was lost, and the run ends mid-battle) plus the predicted `skip reason=no_enemy_alive` at f150064. **Every `res=Won` line reads `delta == base`, `mult=1`, `first=True`.** Brawly: `class=0x20(LEADER) lvl_last=19 base=1900 delta=1900`. The Rusturf Grunt: `0x03(TEAM_AQUA) lvl_last=11 base=220`. 0 lines contain `outcome=`, and no value contains a space | ✅ |
| **FIRSTMON** (fault) | the same 152 `[BATTLE]` lines. Brawly reads `lvl_last=16 base=1600` against the `delta=1900` the game paid (`mult=1.19`) | ✅ red, for its own reason |
| **WILDTOO** (fault) | the same 152 `[BATTLE]` lines. 24 starts: WILD battles gain pairs with `delta=0`, and `res=Won` wild lines read `mult=0` | ✅ red |
| **STRIDE2** | not driven: VACUOUS live, as pre-registered (only class 0 differs). Gate F2 | — |

**BETTER THAN PREDICTED: the two-opponent sum is shown LIVE.**
- The note said no pinned fixture holds a multi battle. But the f253550 fight on Route 109 is one:
  `opp=491+697 class=0x2F(SAILOR)+0x12(TUBER) lvl_last=13+13 base=468 delta=468 mult=1`.
- B is read only because the battle type has TwoOpponents, and A's and B's rewards SUM to what the game paid.
- The masked M0 row (f188817) is the Lass, id 604: `base=96 delta=96`.

## THE CONTROLS — a finding about the harness, not about T1

- **The pre-registered control ran THREE times** on the parent commit `03244ae7` (no T1).
  - CONTROL2 and CONTROL3 replay step 4's M0 exactly: 337 of 337 event lines.
  - **CONTROL (the first run) did NOT.** It reached the Granite Cave (24,8)→(24,7) warp ONE FRAME LATE (f215288, not
    f215287). It missed the Makuhita encounter and diverged from there. This happened before any T1 code runs, on
    code with no T1.
- **T1 matches M0 and both reproducing controls exactly.**
- ⇒ **Had the first control been the only one, T1 would have "failed" its no-behaviour-change check** on a
  divergence that T1 did not cause.
- Filed as **KI-112** (cause NOT measured) and `#27-determinism`.
- The one-frame (0,0) warp read that step 4 excluded is plausibly the same phenomenon, at a warp and varying run to
  run. That is a hypothesis only.

## FOUND BEFORE THE GRADED DRIVES (observe-only smoke runs; the addendum)

- A post-battle evolution scene RE-ENTERS the battle hook: `on_battle_started` at f150064 and `on_battle_ended` at
  f150066, same trainer.
- The first discriminator tried (`gBattleOutcome`) read `Won` at every start. It was refuted by measurement, not
  argued.
- The living-enemy count is the discriminator: 0 at the re-entry, 1-2 at every real start. It is gated as W4, with the
  mutant F7.

## WHAT THIS DOES NOT SHOW

- Rematch state (`first=` is per rematch tier) and which trainers a run SKIPS (the T3 ledger).
- An Amulet Coin battle: `mult=2` needs a player-side holder to SWITCH IN, and none exists at badge 1.
- Whether money-making pays.
- Whether ANY earlier A/B in this project replayed only by luck. KI-112 asks.
