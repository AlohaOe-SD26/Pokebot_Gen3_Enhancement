# 2026-09-29 — USER RULING 24 step 4 GRADED: `POKEBOT_R24_OVERSURVIVAL` catches a wanted species that survival mode fled; an unwanted one is still fled; OFF is unchanged

> Predictions: `2026-09-29-r24oversurvival-PREDICTIONS.md` (`333b4988`, before the code). Code: `f961218b`. Every arm
> ran `storyresume` on `r20_badge1_party1_gym.ss1` with `POKEBOT_R20_OPENFENCE=1`, `--set-balls 60` and
> `random.seed(1)`. Evidence: `tools/story-dev/evidence/2026-09-29-r24oversurvival-*.txt` (`-GRADER.txt` is the
> line-by-line comparison against M0). Frames below are debug-log frames (harness + 139,500).

## RESULTS — every prediction held

| Arm | Env | Reading | Verdict |
|---|---|---|---|
| M0 (measure) | `main` `9a4fbbeb` | Four OWNED survival flees on Route 110, then the UNOWNED Poochyena fled at f470293; Manual stop at f575098 ("13 losses … Need one of: Flying, …") | the discriminator |
| **G-OFF** | flag unset | **0 differing tracked lines** against M0 through f573887 (268 lines, all 8 survival flees); the same Manual stop at f575098 | ✅ OFF unchanged (one trajectory, replayed) |
| **G-ON** | `OVERSURVIVAL=1` | 0 differing lines before f470293, **including the four owned survival flees** (Oddish ×2, Electrike ×2: no new line). At f470293: `[DEXFENCE] CATCH #261 Poochyena — dex catch #261 (joins the party)`, `[CATCH] start kind=dex sp=Poochyena#261 lv=12 attempt=1 badges=2 party=5/6 … map=0,25` → `end=caught thrown=2 dest=party` | ✅ |
| **P-OFF** | `PRESET 24,7=3` | 0 differing lines before f200242. There the Zubat is FLED (`[TURN 0] … -> RunAway`, the survival console line); no `[DEXFENCE] CATCH #41` | ✅ the preset arms survival mode |
| **P-ON** | preset + flag | Zubat (f200242) and Geodude (f203961) caught exactly as in M0. First difference at the OWNED Zubat of f205885: `RanAway` at f206501 where M0 won at f207856 (1 survival console line) | ✅ |
| **P-FAULT** | preset + flag + `FAULT_SKIPSURVIVAL=1` | **0 differing lines** against M0 for the whole 100,000 frames (99 lines); 0 survival lines. It FIGHTS the f205885 Zubat | ✅ the fault is wired; the preset alone is inert |

Every P arm printed `[HARNESS] STORYRESUME_PRESET_DEFEATS applied: _defeat_counts={(24, 7): 3}`.

⚠ **One disclosed deviation in the comparison.** The predictions tracked `[MAP]` lines. A ONE-FRAME map/bag read during
a warp logs `X(g,n) -> X(0,0)` and back (with `[BALLS] 62 -> 0 -> 62` in the same frame). It is excluded:
- The only such pair that differs between runs is the Granite Cave warp at f199946/7. It is present in G-OFF, G-ON,
  P-OFF and P-ON, and absent in M0 and P-FAULT.
- The other pairs (f160879, f330057) sit on the same frame in every run that reaches them.
- The next tracked line, `f200242 [BATTLE] started`, is frame-identical in all six logs.

## ALSO FOUND BY THIS STEP (the suite, before the drives)

**The first version broke every shim-driven repro.**
- It called `self._dex_catch_commit(encounter)` OUTSIDE any `try`.
- Harness drivers and repros call `StoryMode.on_battle_started(shim, …)` with a stand-in `self`, so their battle hooks
  raised `AttributeError`. `repro_ki65_unbound_party_index.py` went red; it passes on `main`.
- **Fix:** both calls go through the class. Gate case S11 carries the repro's shim, with its reading measured on
  HEAD's code; F5 turns exactly {S11} red. Recorded in 08.

**Three older gates pinned the dex site to `on_battle_started`.**
- The gates are `probe_dexcatch_bail.py` D2, `probe_r20_telemetry.py` W and `probe_dex_catch_training.py` A4.
- Each now spans both methods, with a new fault arm proving the helper half is read (D2's widening mutant, F3b, F5).

## SEEN, NOT MEASURED (one trajectory each)

- **G-ON kept catching on the wall map.** After the Poochyena it also caught a Minun at 6/6 (f504619, `dest=box`).
  Whiteouts #8-#10 followed on Route 110. The arm ended at f539500, before M0's Manual stop. **Whether a catch changes
  the Route 110 outcome is NOT graded.** The Wingull M0 fled at f508594 (Flying, the type the stop message asks for)
  was not met on G-ON's diverged path.
- **P-ON: fleeing an owned wild kept the lead healthy.** It then caught an Aron, an Abra and a Makuhita. M0 refused
  the first two ("party is not at full strength") after fighting the f205885 Zubat. The Makuhita was on the preset
  survival map itself (24,7): a second live instance of the feature.
- **The dependency on `POKEBOT_R24_CATCHHURT` is real, not theoretical.** C4 is keyed on CATCHHURT only. So in G-ON
  (OVERSURVIVAL alone), a whiteout during a catch on Route 110 counts toward the rival's losses. Route 110 is that boss's
  key. The registry row says to run the two flags together.

## WHAT THIS DOES NOT SHOW

- **How often a wanted species meets survival mode**, or whether catching there wins or loses more runs. That is the
  batch.
- **Step 5 (the first-faint bail).** Every catch here ended `caught`, so the bail never fired.
