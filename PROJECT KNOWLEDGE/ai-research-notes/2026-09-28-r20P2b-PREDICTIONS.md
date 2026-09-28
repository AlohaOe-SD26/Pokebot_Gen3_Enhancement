# 2026-09-28 — USER RULING 20 Phase 2 step P2-b (open the post-gym-1 fence, flag-gated): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/r20openfence`, cut from `main`
> `146e0421`. Spec: `2026-09-27-ruling20-phase2-BUILDSPEC.md` §4 P2-b (a NOTE).
> The discriminator below was MEASURED by two observe-only drives on the unchanged code (`146e0421`, dirty 0): X0 on
> the fixture and X1 on the control. Each is ONE trajectory. The graded arms replay it: identical output across arms up
> to the first differing verdict is a determinism check, not a replication.

## THE CHANGE (planned)

- `decide_dex_catch(..., open_fence: bool = False)`. The default keeps every existing caller and probe unchanged.
  - When it is true, the post-gym-1 refusal "party is N/6 — a catch would consume the HM/counter runway" is skipped.
    Every LATER gate still applies: an armed hunt, training, the ball reserve, a full PC, full strength, the attempt
    cap, and expected throws.
  - An admit below six says "dex catch #N (joins the party)"; at six it still says "(goes to the PC box)".
- `POKEBOT_R20_OPENFENCE=1` (default unset = OFF) sets `StoryMode._open_fence` in `reset_per_run_state` (read per
  run, like P2-a's target). The adapter passes `open_fence=self._open_fence`.
- **Fault arm `POKEBOT_R20_FAULT_OPENEARLY=1`, which deviates from the spec's `…FAULT_OPENNORESERVE`.** It makes the
  open branch admit at once, before the later gates. The spec's arm knocked out the reserve alone. The likelier way
  to build this wrong is an "open" branch that returns True at once, skipping all seven later gates together, and a
  catch battle never fights back (`catch.py`). The reserve is one of the seven, so the spec's case is covered.
- NEW gate `probe_dex_open_fence.py` (pure plus AST):
  - O0 (OFF: runway) and O1-O3e (ON: party join below six; the PC box at six, eggs counted);
  - O4-O10 (ON: each later gate still refuses);
  - O11 (pre-gym-1 unchanged);
  - A1-A3: the per-run read, the AST wiring, the registry;
  - F1-F4: the fault arm knocks over O4-O10 and leaves O0 green; a mutant passing `open_fence=False` fails A2; the
    keyword kept only in a comment still fails A2.
- `probe_dex_catch_fence.py` is NOT edited. Its C3 and `FAULT_MUST_BREAK` are the flag-off regression arm, and they
  pass because the default is False.

## DISCRIMINATOR — MEASURED (X0)

X0 ran `storyresume` on `r20_badge1_party1_gym.ss1` (`50af0f5c`) with `--set-balls 30` for 240,000 frames, on the
unchanged code. It loads at f139500, so the window ends at f379500.
- **Party:** one, Mudkip#550A9BE6 (later Marshtomp), the whole run.
- **Owned:** {Mudkip, Marshtomp}.
- **Pocket:** Poké Ball x30 and Great Ball x1 (the read-back line), so spare = 31.
- **Verdicts:** 11 `[DEXFENCE]` lines, **all "party is 1/6 — a catch would consume the HM/counter runway"**:

| Frame | Species | Party HP | Story step | What the OTHER gates say (so, the ON verdict) |
|---|---|---|---|---|
| f144426 | Nincada | 21/46 | thief chase | not at full strength |
| f166431 | Taillow | 7/58 | Devon Goods return | not at full strength |
| (f175100) | Taillow (a repeat, not logged OFF) | 58/58 | `train_team` (f173587) sets the training flag | a training grind |
| f176613 / f180818 / f186414 | Abra / Whismur / Poochyena | 55/58 | `train_team` | a training grind (checked before health) |
| — | heal at the Rustboro PC (~f190935); the rival battle is LOST f202004 (a party of one at L19; a fixture artifact, not this item) | | | |
| **f218453** | **Aron** | **61/61** | Steven's Letter, Granite Cave | **nothing: every later gate passes** (spare 31 > 10, no hunt, no training, attempt 0) |
| f226087 / f227429 / f231070 | Zubat / Geodude / Makuhita | 64/64 | Granite Cave | (after Aron the trajectories diverge) |
| f308292 / f332270 | Electrike / Gulpin | 59/75 / 75/75 | | |

**So the first encounter that can separate the arms is Aron at f218453, about 79,000 frames into the window.** The
f175100 battle was read from X0's `[BATTLE]` lines. That the training flag is on there comes from `early_game.py`
`train_team` (`set_swap_train(True)` on entry, `False` on exit).

**The control, X1:** `post_mtpyre.ss1` (`80602159`), party 6, badges 6, `--set-balls 30`, 120,000 frames. It produced
5 `[DEXFENCE]` lines:
- Shuppet f3144418 "not at full strength";
- CATCH Oddish f3209102, Linoone f3216729 and Geodude f3234271, each `dest=box`;
- Graveler f3237600 "not at full strength".

## THE ARMS AND THEIR PREDICTED READINGS

Readings: the `[DEXFENCE]` lines, and step T's `[CATCH] start kind=dex` / `[CATCH] end` lines, in each arm's debug
log. Same command for every arm: `storyresume … --set-balls 30`.

| Arm | Fixture, frames | Predicted |
|---|---|---|
| **OFF** (new code, nothing set) | fixture, 240,000 | The same 11 `[DEXFENCE]` lines as X0, frame for frame, all "runway". **0** `[CATCH] start kind=dex`. |
| **ON** (`POKEBOT_R20_OPENFENCE=1`) | fixture, 240,000 | **No "runway" verdict at all.** Before f218453: Nincada and Taillow "party is not at full strength"; Taillow, Abra, Whismur and Poochyena "a training grind is in progress"; no dex catch starts. **The first `[CATCH] start kind=dex` is `sp=Aron#304 … party=1/6 … spare=31` at f218453**, with `[DEXFENCE] CATCH #304 Aron — dex catch #304 (joins the party)`. At least one `[CATCH] end kind=dex … end=caught … dest=party pid=<a new PID, not 550A9BE6>` in the window, with `party=` one higher than at its start. |
| **FAULT** (`OPENFENCE=1` + `FAULT_OPENEARLY=1`) | fixture, 240,000 | **The first `[CATCH] start kind=dex` is `sp=Nincada#290 … party=1/6` at f144426, while the party is at 21/46.** A catch starts before the heal, which is the live signature of the skipped gates. |
| **CTRL-OFF** and **CTRL-ON** | control, 120,000 | Both identical to X1: the same 5 `[DEXFENCE]` lines, and the same 3 `[CATCH] start/end kind=dex … dest=box` (Oddish, Linoone, Geodude), same frames. |

The frame numbers are predicted exactly because the drive is a deterministic replay up to the first differing
verdict.

## FALSIFIERS

- **OFF:** any `[DEXFENCE]` line differs from X0, or any dex catch starts. Then OFF is not unchanged.
- **ON, a "runway" verdict:** the flag does not reach the fence.
- **ON, a dex catch starts before f218453**, or while the party is hurt, training, or a hunt is armed: a later gate
  was skipped.
- **ON, a party-join start that ends `dest=box`**, or a start that reads `party=6/6`: the wrong path.
- **ON, no dex catch starts in 240,000 frames:** the prediction FAILS. Investigate; it does not pass.
- **FAULT, no catch starts before the heal:** the live half of the gate's F1 is vacuous.
- **Either CTRL arm differs from X1** in any `[DEXFENCE]` or `[CATCH]` line: the flag changed the full-party path.

## WHAT THIS DOES NOT SHOW

- **Whether opening the fence costs finish rate.** The party joins consume the runway `#24-partycap` measured. Whether
  the PC-first make-room paths absorb that is the Phase 3 batch. Until then the flag stays OFF for real runs.
- **Whether a fresh low-level catch ends up leading a boss.** That is `team_policy`'s risk in the spec's §5; it is
  OPEN and not tested here.
- **Ball economy** (B, which waits on the user's §8 Q1).
- **The Rustboro rival loss.** A party of one at L19 is this fixture's artifact; a real run reaches badge 1 with a
  party of 4 (`#27-batch0927`: 25 of 25).

## ADDENDUM — filed after the first five graded arms, BEFORE the seeded arms: pairing arms by seed

**Why:** G-OFF did not replay X0. The cause is `_prepare_for_fight`'s unseeded `random.randint(16, 19)`
(`story_mode.py:3404`), the bot's deliberate "organic" training target, not the flag:
- X0 and G-ON drew 19, and a party at L18 trains to 19;
- G-OFF drew lower and skipped the grind.

So the "deterministic replay" premise above holds for the emulator, not for the bot's own Python RNG. To test OFF
frame for frame against the old code, four arms run the same `storyresume` command under `random.seed(1)`. A `runpy`
wrapper sets the seed, so the code is unchanged:

| Arm | Code | Env |
|---|---|---|
| S-OLD | `146e0421` (the main checkout) | nothing |
| S-OFF, S-OFF2 | `111da618` | nothing |
| S-ON | `111da618` | `POKEBOT_R20_OPENFENCE=1` |

**Predictions**
- **S-OFF equals S-OFF2**, frame for frame, in every `[DEXFENCE]`, `[CATCH]` and `[BATTLE] started` line: the seed
  makes the drive replayable. If not, the wrapper is insufficient. The OFF claim then rests on the pure gates and on
  G-OFF's verdicts only; that is disclosed, not a pass.
- **S-OLD equals S-OFF** on the same lines, frame for frame. Every `[DEXFENCE]` line reads "runway", and there are 0
  dex starts.
- **S-ON** has the same `[BATTLE] started` lines as S-OFF up to its first `[CATCH] start kind=dex`, which reads
  `party=1/6`. There is no "runway" verdict, and no dex start while the party is hurt or training.

**Falsifiers**
- S-OFF equals S-OFF2 but S-OLD differs from S-OFF: OFF changed behaviour.
- S-ON diverges from S-OFF before its first dex start: ON changed something besides the fence.
