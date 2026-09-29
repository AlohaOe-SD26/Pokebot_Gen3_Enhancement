# 2026-09-29 — USER RULING 24 step 4 (a WANTED species outranks SURVIVAL MODE): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/r24oversurvival`, cut from `main`
> `9a4fbbeb`. Spec: `2026-09-28-r23-25-DESIGN.md` step 4 (a NOTE). Ruling: `06`, USER RULING 24 (*"catching should
> always be available if the bot encounters a pokemon that it wants to catch"*).

## THE CHANGE (planned)

- **`StoryMode._dex_catch_commit(encounter)`.** The dex-catch commit block of `on_battle_started`, MOVED unchanged into
  a helper that returns the catch strategy or None. The helper's `try` statement is AST-identical to HEAD's inline block
  (checked once, recorded in the graded note).
- **Flag `POKEBOT_R24_OVERSURVIVAL=1`** (default OFF), read per run into `StoryMode._r24_oversurvival`.
  - ON: the helper runs BEFORE survival mode (3+ defeats on this map ⇒ flee every wild). A wanted species is committed
    to; an unwanted one still meets survival mode.
  - OFF: the helper runs AFTER survival mode, exactly where the block ran.
  - Shiny, HM and counter catches run above both call sites and stay first.
- **Fault arm `POKEBOT_R24_FAULT_SKIPSURVIVAL=1`** (with the flag on): survival mode is skipped for UNWANTED species too.
- **NEW gate `probe_dex_catch_oversurvival.py`**, driving the real `on_battle_started` on a stubbed instance:
  - S1-S7: flag × defeats (3 / 0) × wanted.
  - S8-S10: the shiny, HM and counter branches still commit first under the flag. These read the BRANCH IDENTITY (the
    `kind` handed to `_r20_catch_start`), not a strategy class two branches share.
  - A1-A3: the per-run read, the call count plus the helper's local console import, and the registry rows.
  - Fault arms F1-F3 must each turn EXACTLY their own set red: F1 = {S3}, F2 = {S1, S5} (no early call), F3 = {S8, S9,
    S10} (a mutant hoisting the early call above the shiny branch).
- **Harness only:** `STORYRESUME_PRESET_DEFEATS="G,N=K"` makes `storyresume` start with K defeats filed on map (G, N). It
  wraps the instance's `reset_per_run_state`, because `StoryMode.run()` resets per run.

## WHY OFF IS SIDE-EFFECT-FREE AND ON IS "ONE CALL EARLIER"

With the flag on, on a survival map the helper now calls `_should_catch` for an UNWANTED species, which OFF never did
there. Its only effects are:
- `_dex_catch_last_reason`, which nothing reads;
- the `_dex_catch_logged` dedupe set;
- a `[DEXFENCE]` line.

"Already owned" verdicts are never logged (`dex_fence_log_line`). So for an OWNED species the ON arm is line-identical
to OFF. ⇒ Every live difference must come from a species that is unowned AND admitted.

## THE MEASUREMENT (M0: `main` `9a4fbbeb`, the code before this change ⇒ OFF by construction)

`storyresume` on `r20_badge1_party1_gym.ss1` (`50af0f5c`), `POKEBOT_R20_OPENFENCE=1`, `--set-balls 60`, 480,000 frames,
`random.seed(1)` (seed 2 gave the same wild sequence through f417458). Harness frame = debug-log frame − 139,500.

**Route 110 (natural survival mode).** Every wild battle below was met at FULL party HP (`[BATTLE] started`), with no
hunt armed and spare 39. The fixture starts with 1 species owned (`owned=1`), plus Marshtomp at f150300.

| Harness frame | Wild | Owned then? | M0 (OFF) |
|---|---|---|---|
| f263466, f295580 | Oddish | yes (caught f237201) | survival flee |
| f296618, f311713 | Electrike | yes (caught f235157) | survival flee |
| **f330793** | **Poochyena** | **NO** | **survival flee: a WANTED species fled** |
| **f369094** | **Wingull** (Water/Flying) | **NO** | **survival flee** |
| f401174, f417458 | Poochyena | NO | survival flee |

At debug f575098 the run stopped itself:
- **"this boss: 13 losses with no super-effective answer to Grass. Need one of: Flying, Poison, Bug, Fire, Ice"**,
  followed by `Story -> Manual`.
- The Wingull it fled at f369094 is FLYING. Recorded as the motive, NOT predicted to change the outcome (see WHAT THIS
  DOES NOT SHOW).

**Granite Cave 1F (24,7), no survival mode in M0.**

| Harness frame | Event |
|---|---|
| f60742 | Zubat (unowned) → `CATCH #41 Zubat`, the first wild battle on (24,7) |
| f64461 | Geodude (unowned) → `CATCH #74 Geodude` |
| f66385 | Zubat (now owned) → fought, no catch |

## THE ARMS AND THEIR PREDICTED READINGS

All arms use `r20_badge1_party1_gym.ss1`, `POKEBOT_R20_OPENFENCE=1`, `--set-balls 60` and `random.seed(1)`. They run
from the worktree with the step-4 code. "Lines" means `[BATTLE] started|ended`, `[CATCH]`, `[DEXFENCE]`, `[MAP]` and
`WHITEOUT` in the debug log.

| Arm | Env | Frames | Predicted |
|---|---|---|---|
| **G-OFF** | (flag unset) | 480,000 | M0 replayed: 0 differing lines; the same Manual stop at debug f575098. *One trajectory, replayed.* |
| **G-ON** | `POKEBOT_R24_OVERSURVIVAL=1` | 400,000 | 0 differing lines before debug f470293 (harness f330793), including the four OWNED survival flees (Oddish ×2, Electrike ×2). At f470293: `[DEXFENCE] CATCH #261 Poochyena — dex catch #261 (joins the party)` and `[CATCH] start kind=dex sp=Poochyena#261 … attempt=1 … party=5/6 … map=0,25`, where M0 fled. The catch's END (caught, or a bail) is recorded, not predicted: the COMMIT is the action under test |
| **P-OFF** | `PRESET 24,7=3` | 100,000 | 0 differing lines before debug f200242. There the Zubat is FLED: survival mode's console line `3 defeats on this map already`, and no `[DEXFENCE] CATCH #41` / `[CATCH] start` |
| **P-ON** | `PRESET 24,7=3` + flag | 100,000 | 0 differing lines through the Zubat (f200242) AND Geodude (f203961) catches, the same as M0. First difference at debug f205885 (the owned Zubat): survival mode FLEES it where M0 fought |
| **P-FAULT** | `PRESET 24,7=3` + flag + `FAULT_SKIPSURVIVAL=1` | 100,000 | 0 differing lines against M0 for the whole 100,000 frames. Survival mode never fires with the flag and fault on, and the preset's map is no boss key, so the preset is inert. It FIGHTS the f205885 Zubat, where P-ON flees |

The harness must print `[HARNESS] STORYRESUME_PRESET_DEFEATS applied: _defeat_counts={(24, 7): 3}` in every P arm.
A P arm without it is void.

## FALSIFIERS

- G-OFF differs from M0: the extraction or the OFF path changed behaviour.
- G-ON differs from M0 before f470293: the early call is not side-effect-free for owned species.
- G-ON flees the f470293 Poochyena: the flag does not reach the ordering.
- P-OFF catches the Zubat: the preset did not arm survival mode, and the P arms prove nothing.
- P-ON fights the f205885 Zubat: survival mode no longer applies to unwanted species.
- P-FAULT flees anything on (24,7): the fault arm is not wired.
- A differing line in any arm before its predicted divergence frame.

## WHAT THIS DOES NOT SHOW

- **Whether catching on a wall map breaks the wall.** G-ON may catch the Wingull later. Whether a Flying catch changes
  the Route 110 outcome is ONE trajectory, and grading it would read an anecdote as a result. It is recorded as seen.
- **How often a wanted species meets survival mode.** That is the batch.
- **Step 5 (the first-faint bail).** A G-ON catch may still end `bail=faint`; that is step 5's to change.
