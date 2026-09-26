# 2026-09-26 — `#24-ch23training` — DESIGN PANEL: three designs, two adversarial judges, one decisive arm

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** A 9-agent Claude workflow (`ch23-refusal-design`):
> four read-only researchers (refutation history re-checked at HEAD, a code map, decomp sizing, user
> rulings), three independent designers on different angles, two adversarial judges told to REFUTE.
> Nothing was driven. Every load-bearing claim below needs our own harness before code depends on it.

## The problem (measured — `2026-09-26-organic-frontier-RECON.md` §2)

30 of the 39 badge-8 organic runs died when `train_for_victory_road` refused: the worst under-target
battler "alone needs N frames, over the 250,000 per-call ceiling". 18 of 30 were L≤19 mules/late catches
(Marill L13 ×11), 12 were L26-37 real team members. The refusal code is unchanged at HEAD.

## What the research established

* **Victory Road never exceeds L45** (Wally's Gardevoir; every route trainer L42-45) ⇒ `TRAIN_TARGET=47`
  clears it [DECOMP `trainer_parties.h`].
* **Swap-training IS installed in production** (`StoryMode.on_battle_started` returns
  `SwapTrainBattleStrategy` when `swap_train_active() and encounter is not None`), but the refusal fires
  BEFORE `train_team`, so it never runs for the refused mons. ⛔ The harness `Ch23TrainMode` returns
  `StoryItemBattleStrategy` — any §Ch23 A/B on it is vacuous.
* The swap trigger has **no upper gap limit** (`active.level + UNDERLEVEL_MARGIN <= foe.level` and
  `can_switch()`); the switch resolves before the foe moves. ⚠ But it has **never been OBSERVED** above a
  +6 gap in production data (0 of 4,950 decisions at ≥+8), and the §Ch23 case is +27.
* In-battle switching does NOT reorder the field party (`UpdatePartyToFieldOrder`, decomp) ⇒ swapping
  does not collapse `train_team(slots={0})` into KI-84.
* **Evolution breaks the (pid, species) lookup**: Marill→Azumarill at L18, Slugma 38, Loudred 40,
  Nincada 20. `battler_identities().get((pid, species))` would raise "vanished" mid-grind.
* **HM02 Fly is in every organic bag** (given after the Route 119 rival) but **production never teaches
  it**; only 17 of 30 refused parties had a Fly-capable member (always Swellow).
* ⭐ **A PERFECT §Ch23 FIX STILL STRANDS MOST RUNS AT §Ch24:** 27 of 30 refused parties carry a
  `BENCH_SPECIES` mon below L39 (Zigzagoon L4-17, Castform L27-38) that §Ch24's ladder can only train
  with Fly (VR1F admits a trainee only at L39+). ⇒ a production Fly teach is needed downstream anyway.

## The three designs and the verdict

| design | idea | judge scores (a unblock · b safety · c provability · d rulings) | verdict |
|---|---|---|---|
| **1 — chunked (minimal)** | replace the cost refusal with bounded chunks (each ≤250k estimated, each in a real-frame purse); mules level by swap-training | J1 7·6·8·7 · J2 6·5·8·6 | ⭐ **WINNER (both judges)** — the only design that addresses all 30 inside §Ch23, and it composes with §Ch24 (anything at 47 can ladder on VR1F without Fly) |
| 2 — structural | teach Fly in production (Segment 22c) and run §Ch24's per-trainee ladder to an "arrival floor" ~39 before §Ch23 | J1 5·5·5·8 · J2 4·5·4·8 | best fit to the 2026-09-19 ruling; ≤17/30; largest surface (~500 lines) ⇒ graft `ensure_fly_knower` as the NEXT item |
| 3 — frozen core of four | readiness on the top 4 (+ Mightyena) only; mules untouched | J1 3·7·7·5 · J2 3·7·7·6 | "benching by rank" — the refuted bench in a new form; 11/30; mules strand at §Ch24 |

## MUST-FIX before Design 1 is built (union of both judges)

1. ⛔ **PROVE SWAP-TRAINING AT +27 FIRST — build nothing else until it passes.** Fix the harness to
   install swap-training exactly as production does, then an S arm (swap) vs S-control (no swap).
2. Resolve trainees by **PID only** (evolution), never `(pid, species)`.
3. After every chunk: `wait_until_truly_controllable`, re-verify the lead PID, and a basket-money check.
4. **Money:** a 1-4M-real-frame grind before leg 11 is the hazard the 2026-09-18 REVERSAL cited (a
   whiteout halves money; ₽1,741 margin). Needs a decision entry reconciling it.
5. **Ruling tension (for the USER):** the 2026-09-19 ruling says train at a level-appropriate ground,
   "Fly there, per trainee" — does its "or be swap trained" clause cover a L13 mule on L36-40 grass?
6. The endless cap: re-count cap overruns INCLUDING legs 5-11 (judge 2 recounts ~14/30, not 8).
7. The F2 "no finisher" refusal must mirror `_capable_finisher` + `get_potential_rotation_targets`.
8. `heal_on_lead_pp=True` above L38; delete the stale "train on B1F" advice (B1F is ruled out).
9. Headline caveat: this unblocks **§Ch23, not the Hall of Fame**.
