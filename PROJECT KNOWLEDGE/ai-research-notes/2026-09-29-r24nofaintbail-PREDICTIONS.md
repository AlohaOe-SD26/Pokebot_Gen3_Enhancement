# 2026-09-29 — USER RULING 24 step 5 (no first-faint bail on a dex catch): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/r24nofaintbail`, cut from `main`
> `80dd6cbc`. Spec: `2026-09-28-r23-25-DESIGN.md` step 5 (= design v2 step 4; a NOTE). Ruling: `06`, USER RULING 24
> (*"If the bot whites out or the training pokemon faints, thats ok … catching has a bit higher priority"*).

## THE CHANGE (planned)

- **Flag `POKEBOT_R24_NOFAINTBAIL=1`** (default OFF), read per run into `StoryMode._r24_nofaintbail`.
  `StoryDexCatchStrategy` reads it from the RUNNING mode at construction (`context.bot_mode_instance`), the step-3
  pattern: one source for the flag.
- **BOTH faint-bail paths, under the flag:**
  - (a) `should_flee_after_faint` returns the parent's answer (`CatchStrategy`: False ⇒ `choose_new_lead_after_faint`
    sends the next able mon).
  - (b) `_fainted_this_battle` is NOT set, so `decide_turn`'s `dex_catch_bail_reason` cannot return "a team member
    fainted". Setting only (a) would still flee on the NEXT turn (the design's C5 finding).
  - The reserve bail and the trapped-and-empty fight are unchanged.
- **Flag-ON-only telemetry** (rule 7, the action): each faint in a dex catch logs
  `[DEXCATCH-NOBAIL] a team member fainted — sending the next Pokémon and throwing on`. OFF gains no line.
- **Fault arm `POKEBOT_R24_FAULT_HALFBAIL=1`** (with the flag on): only path (a) changes. `_fainted_this_battle` is still
  set, so the next `decide_turn` bails.
- **Design deviation, decided here:** the design's second fault arm `POKEBOT_R24_FAULT_BAILWIDE` (drop every bail)
  becomes a SOURCE MUTANT in the gate, not a production env read. It proves only that the gate reads the reserve row, and
  a live run would never set it.
- **NEW gate `probe_dex_catch_nofaintbail.py`:**
  - ON + a faint: `should_flee_after_faint` is False, AND the next `decide_turn` (spare above the reserve) is the parent's
    turn.
  - ON at the reserve: still bails.
  - ON trapped and empty: fights.
  - OFF + a faint: bails on both paths.
  - Telemetry: ON logs one continue line per faint; OFF logs none.
  - The per-run read, the strategy reading the running mode, and the registry rows.
  - Fault arms: HALFBAIL, the reserve-drop mutant, a telemetry mutant without its flag guard, and a strategy that
    ignores the flag. Each must turn EXACTLY its own set red.

## THE DISCRIMINATOR (already measured: step 4's M0)

`main` `9a4fbbeb` (the pre-change code). `storyresume` on `r20_badge1_party1_gym.ss1` (`50af0f5c`),
`POKEBOT_R20_OPENFENCE=1`, `--set-balls 60`, `random.seed(1)`. Debug-log frames (= harness + 139,500). Evidence:
`tools/story-dev/evidence/2026-09-29-r24oversurvival-M0.txt` and the M0 debug log (`Story-debug-20260929-092445.log`).

| Frame | Reading (OFF) |
|---|---|
| f350678 | `[CATCH] start kind=dex sp=Gulpin#316 lv=12 attempt=1 badges=2 party=3/6 … spare=58 … map=0,25` (Route 110) |
| f351187-f358528 | the lead Zubat L10 throws ten Poké Balls at a FULL-HP Gulpin (38/38). Yawn puts Zubat to sleep; Zubat goes 28 → 7 HP |
| **f359393** | **`[DEXCATCH] [DEXCATCH-BAIL] a team member fainted`** |
| f359583 | `[CATCH] end … end=bail res=RanAway thrown=10 … bail=faint`; party Zubat, Marshtomp L23, Geodude |

Step 4's G-OFF (the step-4 code, flag unset) replayed M0 with 0 differing lines. This branch changes only the dex
strategy's faint handling, so the OFF arm is predicted to replay M0 too.

## THE ARMS AND THEIR PREDICTED READINGS

Every arm: `r20_badge1_party1_gym.ss1`, `POKEBOT_R20_OPENFENCE=1`, `--set-balls 60`, 240,000 frames (to debug f379500),
`random.seed(1)`. The comparison tracks `[BATTLE] started|ended`, `[CATCH]`, `[DEXFENCE]`, `[DEXCATCH]`, `[MAP]` and
`WHITEOUT` against M0. It excludes the one-frame `(0,0)` warp read disclosed in step 4's graded note, and nothing
else.

| Arm | Env | Predicted |
|---|---|---|
| **OFF** | (flag unset) | M0 replayed: 0 differing tracked lines through the whole arm, including `[DEXCATCH-BAIL] a team member fainted` at f359393 and `bail=faint` at f359583; no `[DEXCATCH-NOBAIL]` line anywhere |
| **ON** | `POKEBOT_R24_NOFAINTBAIL=1` | 0 differing lines before f359393. At the faint: `[DEXCATCH-NOBAIL] …` INSTEAD of `[DEXCATCH-BAIL]`. The next mon is sent in and the following turn throws (`UseItem`). The Gulpin's `[CATCH] end` is NOT `bail=faint`. Its end (caught, a reserve bail, or a whiteout) and everything after it are RECORDED, not predicted |
| **HALF** (fault) | + `POKEBOT_R24_FAULT_HALFBAIL=1` | identical to ON through the `[DEXCATCH-NOBAIL]` line and the send-in. The NEXT turn bails: `[DEXCATCH-BAIL] a team member fainted` and `[CATCH] end … bail=faint`, with `thrown=10` (no throw after the faint) |

## FALSIFIERS

- OFF differs from M0, or logs a `[DEXCATCH-NOBAIL]` line: the flag, or its telemetry, leaked.
- ON differs from M0 before f359393: the change is not confined to the faint.
- ON logs `[DEXCATCH-BAIL] a team member fainted`, or ends the Gulpin with `bail=faint`: a bail path survived.
- HALF does NOT bail on the turn after the send-in: path (b) is not what stops the bail. The design's C5 reasoning
  would then be wrong.
- Any traceback, or a Manual drop that M0 does not have before debug f379500.

## WHAT THIS DOES NOT SHOW

- **How often a faint in a dex catch now becomes a whiteout, and what that costs** (RULING 24 accepts it). That is the
  batch.
- **The dependency on `POKEBOT_R24_CATCHHURT`, as in step 4.** C4 is keyed on CATCHHURT only. With NOFAINTBAIL alone, a
  catch that ends in a whiteout on a boss-key map counts toward that boss's losses. So the registry row will say to run
  the two flags together.
