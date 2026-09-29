# 2026-09-28 — USER RULING 20 Phase 2 step P2-c (hunt-armed first, flag-gated): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any P2-c code exists. Branch `wt/r20huntfirst`, cut from `main` `255ee5f0`. Spec:
> `2026-09-27-ruling20-phase2-BUILDSPEC.md` §4 P2-c (a NOTE). Driver `--driver huntfirst` (`d4b8d861`).

## THE PROBLEM

Before gym 1, `decide_dex_catch` returns from its team-building branch (`if pre_badge1:`) BEFORE it checks
`hunt_armed`. So while a counter hunt is spinning for its target, a team-building species is still caught.
- `counter_hunt.catch_confirmed`'s party path is species-blind: any new PID ends the spin.
- The hunt's verdict (`party_counter_slot`) then finds no counter, and it prints "found nothing in 120000 frames"
  without having spun that long.
- It matters when team building is still active during a pre-gym-1 hunt: the party is below the team target (always
  so with `POKEBOT_R20_TEAM6`), and the hunt is the Roxanne counter ladder.

## THE CHANGE (planned)

- **The flag.** `POKEBOT_R20_HUNTFIRST=1` (default unset = OFF) sets `StoryMode._hunt_first` in
  `reset_per_run_state`, read per run like P2-a/P2-b. The adapter passes `decide_dex_catch(..., hunt_first=...)`.
- **The new check.** When `hunt_first` is on, a check placed BEFORE `if pre_badge1:` refuses in two cases:
  - `pre_badge1 and hunt_armed`: "a catch-on-sight hunt is armed";
  - `pre_badge1 and hunt_walking`: the `#27-enroutejoin` walk marker. This goes beyond the spec, deliberately: before
    gym 1 a team catch is a party join, the very thing `#27-enroutejoin` refuses on a hunt's walk.
- **Scope.** After gym 1 nothing changes; the new check requires `pre_badge1`. Training stays where it is (spec).
- **No production fault env.** Flag OFF *is* the skip-the-fix arm: the old order, byte-identical.
- **NEW gate `probe_hunt_first.py`:**
  - pure cases: OFF admits a team catch while armed; ON refuses while armed and while walking; ON leaves the unarmed
    pre-gym-1 case and every post-gym-1 case unchanged;
  - A1 the per-run read; A2 AST wiring; A3 the registry;
  - mutants: the adapter passing `hunt_first=False`, a comment-only mention, and the new check moved AFTER the
    pre-gym-1 branch (the old order). Each must fail.

## THE DISCRIMINATOR, MEASURED (unchanged code `255ee5f0` + the driver)

- **X-OFF (INVALID, disclosed).** Seeds 1–3, `POKEBOT_R20_TEAM6=1`. The driver's first version disarmed the hunt it was
  testing: `counter_armed=[]` on every spin battle, and two Nincada battles were not caught. The runs are kept only as the
  record of that driver bug.
- **X2-OFF (valid).** Seeds 1–3 are identical, with `counter_armed=[290]` on every spin battle.
  - Spin battles: Whismur, Poochyena, then **Abra at f140752, f142577 and f144228**. Each Abra reads
    `strategy=StoryCatchStrategy fence='pre-gym-1 team building (joins the party)'`: a TEAM catch attempted while the
    counter hunt is ARMED.
  - Each Abra escaped. Then Poochyena, then **Nincada at f148137**, caught as the counter.
  - Exit `hunt_return {'slot': 4, …}`, `joined ['Nincada#FE01E1CF']`, 7 spin battles, 12,967 spin frames.

**So the discriminating battle is the Abra at f140752.** The arms are identical up to it.

## THE ARMS AND THEIR PREDICTED READINGS

All arms: `--driver huntfirst` on `r20_pregym1_party4_r116.ss1` (`9710585350be`), `random.seed(1)`, `--frames 60000`,
with the P2-c code.

| Arm | Env | Predicted |
|---|---|---|
| **OFF** | `POKEBOT_R20_TEAM6=1` | identical to X2-OFF-s1, frame for frame, in every `[huntfirst] BATTLE` row and the verdict: Abra ×3 admitted as a team catch, Nincada caught at f148137 |
| **ON** | `TEAM6=1` + `POKEBOT_R20_HUNTFIRST=1` | the same rows up to f140752. **At f140752 the Abra is refused: `fence='a catch-on-sight hunt is armed'` and no catch strategy.** No spin row anywhere reads a `pre-gym-1 team building` catch. After that the path may diverge (a fought or fled Abra takes different frames). The hunt ends either by catching a NEW Nincada PID or at the bound, never with a non-counter joined |
| **C-OFF / C-ON** (control) | `TEAM6` unset (target 4 = party 4), and `HUNTFIRST` unset / `=1` | identical to each other in every row. Team building refuses at its target ("pre-gym-1 team already at its target of 4"), so moving the armed check before it changes nothing |

## FALSIFIERS

- OFF differs from X2-OFF-s1: the change touched the flag-OFF path.
- ON admits the f140752 Abra, or any team-building catch in the spin: the flag does not reach the fence.
- ON's rows differ from OFF's before f140752: the flag changed something earlier.
- C-ON differs from C-OFF: the flag changed the ordinary case (a full team target).
- ON ends with a non-Nincada in `joined`.

## WHAT THIS DOES NOT SHOW

- **How often a pre-gym-1 counter hunt runs with team building still active.** With the default target of 4 the team
  is usually full before Roxanne. With `POKEBOT_R20_TEAM6` it may not be. That is the Phase 3 batch.
- **The walk half of the change, live.** This hunt starts ON its tile, so the walk is empty. It is proven by the pure
  gate only.
- **Production would not hunt on Route 116.** `hunt_ground_tile(ROUTE116)` is None, and the whitelist fails closed.
  The driver uses the team loop's tile, and the fence/hunt interaction does not depend on the tile.

## ADDENDUM — a correction filed BEFORE any P2-c drive ran

**C-OFF / C-ON are NOT identical "in every row".** In C-ON, a team species met during the armed spin is refused FIRST by
the new check ("a catch-on-sight hunt is armed"). In C-OFF it is refused by the team target ("pre-gym-1 team already at
its target of 4"). Both are refusals, and neither returns a catch strategy.

**Corrected prediction:** C-ON and C-OFF are identical in every row's frame, phase, species and STRATEGY (the action),
and in the verdict. Only the fence REASON of such battles differs. The same holds for ON against OFF before f140752.
**Corrected falsifier:** C-ON differs from C-OFF in any row's frame, phase, species or strategy, or in the verdict.
