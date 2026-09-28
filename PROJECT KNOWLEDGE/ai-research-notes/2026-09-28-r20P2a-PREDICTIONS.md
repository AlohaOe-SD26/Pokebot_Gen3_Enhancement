# 2026-09-28 — USER RULING 20 Phase 2 step P2-a (the pre-gym-1 team target of 6, flag-gated): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code. Branch `wt/r20team6`, cut from `main` `97029359`. Spec:
> `2026-09-27-ruling20-phase2-BUILDSPEC.md` §4 P2-a (a NOTE).
> ⚠ HISTORY THAT BOUNDS THIS: the target went 4 → 6 once before (`#24-partycap`, 2026-08-05) and was reverted the same
> day. Finish rate fell 52.0% → 15.8% because a full party had no Surf learner and no slot to catch one. The PC-first
> make-room paths built since may have removed that cause, but that is a FREQUENCY question for the Phase 3 batch. This
> step proves only that the FLAG does what it says, and that OFF is byte-identical.

## THE CHANGE (planned)

- `POKEBOT_R20_TEAM6=1` (default unset = OFF): `reset_per_run_state` sets `_catch_team_target = 6` (else 4).
- Both readers take it from one place:
  - the fence gets `party_target=self._catch_team_target`;
  - the team loop gets `catch_starter_team(self._team_loop_target())`, which returns `_catch_team_target`.
- Flag ON only: `catch_starter_team` gains an exit `reason=none_left` when no land species on its grass is still
  admissible (unowned, not already in the party). Without it, a target of 6 on a map with fewer admissible species
  would spin toward the 250-loop guard. OFF: unchanged.
- The spec's "egg bound" is NOT built. Eggs cannot occur before gym 1 (no egg source), so it could never fire.
- Fault arm `POKEBOT_R20_FAULT_TARGETLOOP=1`: `_team_loop_target()` returns 4 while the fence keeps 6. The new gate must
  go RED, and the live ON arm must stop at 4.
- Gate `probe_catch_team_target.py`:
  - the target is 4 OFF and 6 ON;
  - the loop target equals the fence target;
  - the none_left helper on synthetic data;
  - AST wiring of both readers;
  - the fault arm must fail.

## THE DRIVE — `storyresume` on `r20_pregym1_party4_r116.ss1` (`9710585350be`), `--frames 60000`

**Discriminator, MEASURED at load** (the bot's own readers):
- party of 4: Mudkip L13, Poochyena L4, Nincada L6, Whismur L6;
- owned {Mudkip, Nincada, Poochyena, Whismur};
- Route 116 land species {Abra, Nincada, Poochyena, Skitty, Taillow, Whismur}, so **admissible now: Abra, Skitty,
  Taillow**;
- spare balls 28 (27 Poké + 1 Premier; no `--set-balls` needed).

So OFF exits at once; ON must catch.

Readings: the step T telemetry. Graded on the FIRST `[CATCHTEAM] exit` line, plus the `[CATCH] start kind=team` / `end`
lines before it.

| Arm | `[CATCHTEAM] exit` | `[CATCH] kind=team` before it |
|---|---|---|
| OFF | `reason=target target=4 party=4 … loops=0` | none |
| ON (`POKEBOT_R20_TEAM6=1`) | `reason=target target=6 party=6`, or `reason=none_left target=6 party=5` | ≥ 1 start with `end=caught dest=party`; each new party PID is one of Abra/Skitty/Taillow |
| FAULT (`POKEBOT_R20_TEAM6=1` + `POKEBOT_R20_FAULT_TARGETLOOP=1`) | `reason=target target=4 party=4 … loops=0` | none |

## FALSIFIERS

- OFF catches anything, or exits with anything but `target=4 party=4 loops=0`: OFF is not byte-identical.
- ON exits at `party=4` or with `reason=guard`: the flag does not reach the loop, or `none_left` is broken.
- ON catches a species that was owned or already in the party.
- FAULT reaches party 5 or 6 in the team loop: the arm does not isolate the loop target.
- The first `[CATCHTEAM]` line never appears within 60,000 frames: VACUOUS (not a pass).

## WHAT THIS DOES NOT SHOW

- Whether a party of 6 before gym 1 hurts the finish rate (`#24-partycap`'s measured harm). That is the Phase 3 batch.
- The effect on ball supply after badge 1 (the refuter's point: a party of 6 at badge 1 box-catches at once and drains
  balls to 10).
