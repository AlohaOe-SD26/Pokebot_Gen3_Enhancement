# Step 5.3 stage B prep: where the stop checks get their runs (2026-10-26)

> **STATUS: DECIDED and BUILT 2026-10-27 (the DECISION section below; `07` 2026-10-27, commit c0676255).** First a coordinator design note: stage B's plan decides it
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

## DECISION (2026-10-27): option (B), with a written coverage rule

> Stage B step 1's builder. Decided before anything was built; the build and its development check are in the builder's
> report (`stopruns-report.md`) and the 07 entry the coordinator writes.

**Why the exclusion was made (searched, not remembered).** `git log -S NO_PHASE2 -- ai_player/gates/rate_step5.py` gives
two commits: `75c2080a` (2026-10-15, step 5.1: `NO_PHASE2 = ("LOSE3", "CH2", "CH2_OFF")`, added in the SAME commit as
LOSE3, "the verifier's round") and `f29701bb` (5.3 A1: hashed it). The only stated reason anywhere is the code comment
"plans whose losses are the fault itself: never replayed by the phase-2 STOP plans". That commit's message, its 06, 07 and 08
hunks, and `2026-10-15-step51-REVIEW-FINDINGS.md` give no reason; the review has one related line ("MAX_LOSSES 3 has been
reached only in the LOSE3 copy: an altered decider, 5 of 6 runs. No unaltered run has reached it"), a disclosure about
LOSE3's own check, not about phase 2. `decomp_lookup.py ask` found no ruling (exit 3). The likely intent, inferred: phase 2
was built on 2026-10-14 ("no run reached the MAX_LOSSES stop, and the loop's count was unproven") to prove the stop on the
REAL code's losses, which were common then (2-9 per sweep), so replaying LOSE3 added runs and no coverage; and LOSE3
already exercises the stop at the real cap. Neither reason holds once natural losses stop coming (0 in 48 seeds, #40).

**Does a STOP replay of a LOSE3 run still prove what R5.STOP proves?** Yes, read word by word:
- R5.STOP asserts, of each replay in a copy with `CAP1` (`mode.py` `MAX_LOSSES = 3` -> `1`, nothing else): reason
  `play: stuck: 1 battles lost (MAX_LOSSES 1)`, the game's losses 1, the told losses 1, the report's 1, the run ended
  within `STOP_WITHIN` (6,000) frames of the GAME's record of its first loss; n = phase 1's runs with a loss, every one
  replayed. The code it proves is the loop's `_count_losses` (`battles_lost` over the navigator's `battle_log`, outcome
  `"lost"` from the game's `gBattleOutcome`, `skills/battle.py` OUTCOMES), the tell, and the loop's end.
- LOSE3's edit is ONE place in `brain/battle.py`: once its battler is L7, the DECIDER picks the status move in a wild
  battle. It is upstream of the outcome: the loss is a real game loss (gBattleOutcome 2), recorded, counted and acted on by
  unedited code. So the stop under test is the real code's; only the reason the battle was lost differs, and the stop rule
  never reads why a battle was lost. Before the first loss the replay is the base run itself (CAP1 changes nothing earlier).
- R5.STOPDEAD asserts, of each replay with `CAP1` + G46 (`stop = self._count_losses(...)` -> `stop = None`): it does NOT end
  with that reason, the game lost at least once, the report and told losses are 0, and it went on past `STOP_WITHIN`. It is
  the arm that shows the count's removal is visible. On a LOSE3 base the decider keeps losing and nothing counts: report
  0 against the game's 1 or more, the run goes on. The edits touch different anchors (`brain/battle.py`, `mode.py`), so
  they compose. In R5.LOSE3's control arm the same rows (the harness records `max_losses` 1) reach the cap and go on past
  it, so the control reads FAIL with n = the STOPDEAD runs.

**What (B) does not cover, and the coverage rule.** LOSE3 loses WILD battles only; a natural loss can be a trainer battle
(the rival). The stop path is the same for both (the outcome read is the battle skill's, for every kind), but a sweep whose
only replays are LOSE3's has exercised the stop on forced wild losses alone. Rule: (1) natural-loss replays are ALWAYS
included and never displaced by LOSE3's (`phase2_lost` takes every eligible plan's lost runs); (2) R5.STOP's and
R5.STOPDEAD's texts count their replays BY SOURCE (natural, and LOSE3's forced), so the evidence says when the stop was
exercised on forced losses only. No floor on natural losses: their rate is the AI's skill, not a property of the stop.

**Rejected.** (A) `LOSE3DEAD` (mutants LOSE3 + G46 as a phase-1 plan): fixes LOSE3's control only; R5.STOP and R5.STOPDEAD
stay VACUOUS whenever no natural loss happens (which fails the verdict), and it adds about as many long runs as (B)'s
STOPDEAD replays. (C) a waiver: rejected above.

**For 06.** *2026-10-27, step 5.3 stage B step 1: phase 2's STOP and STOPDEAD also replay LOSE3's runs (LOSE3 leaves
`NO_PHASE2`).* Reason: natural losses have become rare (0 in 48 seeds on ledger #40), so R5.STOP and R5.STOPDEAD could get
no run in a graded sweep and LOSE3's control STOPDEAD could not reach its floor of 2. A STOP replay of LOSE3 still proves
the stop: LOSE3 edits only the battle decider, upstream of the game's loss, and the stop rule reads the game's loss count,
never why. Coverage rule: natural-loss replays always stay in, and the checks' texts count replays by source. Rejected: (A)
a `LOSE3DEAD` phase-1 control (fixes LOSE3's control only); (C) waiving R5.STOP/R5.STOPDEAD (a check that cannot run proves
nothing). The old exclusion ("losses that are the fault itself", 75c2080a) had no recorded reason.
