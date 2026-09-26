# 2026-09-26 — `#24-ch23training` CHUNKED TRAINING — PRE-REGISTERED PREDICTIONS (written BEFORE the drives)

> The build approved by USER RULING 14. Code: `victory_road.train_for_victory_road` (chunk loop,
> `ch23_chunk_target`, `ch23_swap_finisher_exists`, `_trainee_by_pid`), skip-the-fix arm
> `POKEBOT_CH23_FAULT_NOCHUNK=1`, offline gate `probe_ch23_chunk_plan.py`. Harness `Ch23TrainMode` now installs
> `SwapTrainBattleStrategy` exactly as production does. All drives: `post_ever_grande.ss1` (md5 `18203e997edc`),
> `--driver ch23train`. `--inject-hmmule` = ARM A (Marill L13 displaces Castform L36).

| # | arm | prediction | falsifier |
|---|---|---|---|
| E0a | CONTROL, `POKEBOT_CH23_ESTIMATE_ONLY=1` | no refusal; `train_chunked=[]`; `train_plan` sends every under-target battler straight to 47 (one chunk each) | any mon chunked ⇒ the ordinary path changed |
| E0b | ARM A, estimate-only | **no refusal**; `train_chunked` names the Marill; its first chunk target is **L32** (the gate's plan) | a refusal ⇒ the fix is not reached |
| E0c | ARM A + `NOCHUNK`, estimate-only | raises the organic text **`Marill#… alone needs 406,972 frames`** | anything else ⇒ the arm does not reproduce the organic death |
| E1 | ARM A, FULL | `R-READY`; the mule (by PID) ends **≥ L47 as Azumarill** (it evolves at 18 inside chunk 1 — the lookup must survive it); ≥2 chunks, every chunk banks EXP; `swap_battles > 0`; **0 whiteouts**; carriers survive; money never drops; total training under `CH23_TRAIN_PURSE_FRAMES` | any raise, a whiteout, or the mule < 47 ⇒ not proven; read the chunk table before touching anything |
| E2 | CONTROL, FULL — HEAD's `victory_road.py` vs the new one, same driver | **BIT-IDENTICAL**: same `train_post`, same battle count, same frame count — each mon is a single chunk, and `_yield_bounded_by_frames` is step-for-step identical to `yield from` | any difference ⇒ the ordinary path is not preserved; investigate before shipping |

⚠ One fixture, one party; E2 is "one trajectory, replayed" (rule 8) — it proves the ordinary path is
UNCHANGED, not how often chunked training succeeds organically (that is `#26-batch0926`'s question).
