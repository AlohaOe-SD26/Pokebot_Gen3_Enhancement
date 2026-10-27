# Step 5.3 stage B prep: where the stop checks get their runs (2026-10-26)

> **STATUS: a coordinator DESIGN NOTE for stage B's plan. NOT BUILT, nothing changed in code.** Stage B's plan decides it
> (with a critic) and builds it before anything registers. Written at the end of the week's budget so that stage B can
> start from it after the Wednesday 2026-10-28 reset.

## The finding (measured)

- Phase 2 of a sweep (`rate_step5.py`, `STOP_PLANS = {"STOP": ["CAP1"], "STOPDEAD": ["CAP1", "G46"]}`) replays only the
  phase-1 runs in which the GAME recorded a NATURAL battle loss. `NO_PHASE2 = ("LOSE3", "CH2", "CH2_OFF", "LOAF",
  "BLOCKED", "GREEDY")` keeps the deliberately losing plan LOSE3 out ("plans whose losses are the fault itself", a code
  comment near `MUTANT_PLANS`; no 06 or 07 entry records why).
- Natural losses have become rare as the AI improved. The sweeps' own `PHASE 2:` lines: 2026-10-14 two (`NOTRAIN` 307,
  310); 2026-10-14 two (`NOHINTS` 611, `STALL1` 609); 2026-10-15 nine (CH1, DEADREST, NOHINTS, PATIENCE, PATIENCE_OLD,
  STALL1); the graded ledger #34 (2026-10-16, 20 seeds) three (`ERRANDS_OFF` 945, `STALL1` 960, `STALL2` 945). Now:
  ledger #39 (12 seeds, every plan) one (`DEADREST` 1314); ledger #40 (48 seeds, DEADREST only) **none**. Per sweep: 3
  in 20 seeds (#34), 1 in 12 (#39), 0 in 48 DEADREST-only (#40): the rate is uncertain and seems to have fallen; it
  rests on few events (a Tier 1 reviewer corrected an earlier '1 in 60', which mixed the denominators).
- So a 20-seed graded sweep MAY give **R5.STOP and R5.STOPDEAD no run at all** (VACUOUS, which fails the
  verdict unless waived), and **R5.LOSE3's control STOPDEAD** could not reach its floor of 2 runs (the re-sourcing plan's
  (b)). This is wider than the LOSE3 control the 2026-10-25 handoff named.

## Options

- **(A) A new phase-1 control plan `LOSE3DEAD` = mutants `LOSE3` + `G46`** (Catcher seeds, like LOSE3): it loses on
  purpose and its loss count is removed, so it never stops and must fail LOSE3's "ends within N frames of the 3rd loss".
  Fixes LOSE3's control only; R5.STOP and R5.STOPDEAD still wait for natural losses.
- **(B) Let STOP and STOPDEAD also replay LOSE3's runs** (LOSE3 out of `NO_PHASE2` for the STOP plans), keeping the
  natural-loss replays. Every Catcher seed's LOSE3 run loses (3 of 4 reached a third loss on #39), so a 20-seed sweep
  gives about 7 STOP and 7 STOPDEAD runs. Fixes all three. The stop logic under test is the real code's; only the battle
  decider is the LOSE3 mutant, which is what makes the loss happen.
- **(C) Waive R5.STOP and R5.STOPDEAD when no natural loss happens.** Rejected: a check that cannot run proves nothing,
  and the waiver would hide exactly the regression it exists to catch.

## Recommendation: (B)

Stage B's plan must first argue the old exclusion ("losses that are the fault itself"): the likely worry is that a STOP
replay of LOSE3 tests the stop rule only on losses the mutant forces. The stop rule reads the GAME's loss count, not why
the battle was lost, so (B) keeps what STOP proves. If the critic finds a real reason, fall back to (A) plus a written
coverage rule for R5.STOP and R5.STOPDEAD.

## Build outline (for stage B)

1. `NO_PHASE2`: the STOP plans may replay LOSE3's runs (or a separate `STOP_BASES` naming which plans they replay).
2. Tests (`test_step53_rs.py`): FAULT, a synthetic sweep with no natural loss still gives STOP and STOPDEAD runs from
   LOSE3; CONTROL, the natural-loss replays are unchanged; the LOSE3 control arm reads FAIL with 2 or more STOPDEAD runs;
   MUTANT, LOSE3 put back into `NO_PHASE2` turns them VACUOUS (run with fresh bytecode, `08` 2026-10-25).
3. A development check on fresh Catcher seeds from 1367 (`--plans LOSE3,STOP,STOPDEAD`, about 20 minutes): each LOSE3 run
   with a loss is replayed by both; R5.STOP passes and R5.STOPDEAD reads as the control it is.
4. Then stage B as planned: bounds from the development numbers, `--register` 961-980, one graded 20-seed sweep compared
   with ledger #34. The graded sweep grows by about 14 replays.
