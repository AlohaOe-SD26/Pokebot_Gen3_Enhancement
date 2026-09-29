# 2026-09-28 — `#27-enroutejoin` (refuse a party join while a hunt WALKS to its ground): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the fix is committed and before any graded drive. The fix was drafted in the working tree while the
> measurements below ran; none of it is committed. Branch `wt/enroutejoin`, cut from `main` `930baacf`. The driver
> options it uses were committed first (`8b580b23`, `r101hunt` `R101_ARM=healed`/`healedindoor`, `R101_FENCE=real`).
> Audit: `2026-09-28-enroutejoin-AUDIT.md` (a NOTE).

## THE CHANGE (planned)

- `early_game.hunt_walk(walk)` runs a hunt's walk with `hunt_walk_active()` True. It restores the previous value on
  return, raise and close.
- **The four walk calls are wrapped:** `ensure_hm_learner`'s `provision_poke_balls()` and `_navigate_riding_out(...)`,
  and the same two in `counter_hunt.hunt`.
- **`decide_dex_catch(..., hunt_walking=False)`** refuses a catch when `hunt_walking and open_fence and party < 6`:
  "a hunt is walking to its ground — …". It sits after the hunt-armed check. Flag OFF has already returned "runway",
  and a full party goes to the box, so **only the P2-b party-join path can reach it.** The adapter passes
  `hunt_walking=bool(_eg.hunt_walk_active())`.
- **Fault arm `POKEBOT_ENROUTE_FAULT_NOWALK=1`:** the marker always reads False.
- **Gates.** NEW `probe_hunt_walk.py` covers:
  - W1-W4: the marker during and after a walk, on a raise, on close, and nested;
  - A1: the four calls are wrapped, checked by AST;
  - A2: the adapter's keyword;
  - A3: the registry;
  - F1-F5: the fault arm, two unwrap mutants, a comment-only mutant, and a `False` adapter.

  `probe_dex_open_fence.py` gains three cases:
  - O12: ON, walking → refused;
  - O12o: OFF → still "runway";
  - O12f: ON, full party → still "PC box".

  Its F1 set now includes O12.

## THE DISCRIMINATOR, MEASURED — and why no live arm can show a walk battle being refused

Seven observe-only drives ran on the unfixed code (`930baacf` plus the driver). Each is one trajectory:
- **M-ON / M-OFF** (`r101hunt`, `R101_ARM=healed`, `R101_FENCE=real`, `random.seed(1)`, `--set-balls 20`):
  - the heal leaves the party at full HP, and it deposits one member (5 → 4);
  - the hunt picks `ROUTE103 (5, 7)`;
  - **0 walk battles**; 6 spin battles.

  Flag ON, the fence refused Wingull in the spin as "a catch-on-sight hunt is armed", where OFF said "runway".
- **M2-ON / M2-OFF, seeds 1, 2 and 3** (`R101_ARM=healedindoor`): the hunt picks `ROUTE101 (12, 10)`. **0 walk
  battles in all six.** One spin battle; exit `slot 5`.
- **M3-ON, seeds 1, 2 and 3** (`storyresume` on `r20_badge1_party1_gym.ss1`, flag ON, 480,000 frames). Seeds 1 and 2 are
  identical line for line; seed 3 differs only in the text of 6 "training the team to Lv N" lines (a different
  organic draw of targets the party already met), with every battle, catch and verdict line the same. After 6 losses to the Route 110 rival (a party of one at badge 1; the flag-off X0 hit the same
  wall), it starts the counter hunt "hunting Numel on FIERY_PATH" (f442459). Its walk met wild battles only on Route 110,
  where survival mode (3+ defeats on the map) flees BEFORE the dex fence is consulted. The run ends in Manual on the
  hopeless-boss stop.

**Why:** the hunts walk with `_navigate_riding_out(..., avoid_encounters=True)` (`early_game.py:238`), so a walk battle
needs a forced crossing: a cave floor, a grass corridor, or the step onto the spin tile. A separate agent is counting
how often that happened in real batch logs. **So no live arm here can show a real walk battle being refused. That proof
is the gates' (the O12 cases and W1-W4); the live arms prove what the fix must NOT change, plus the marker's state on a
real walk.**

## THE GRADED ARMS AND THEIR PREDICTED READINGS

All arms run on the fixed code, with `random.seed(1)`, `R101_FENCE=real`, `R101_ARM=healedindoor`, `--set-balls 20`
and `--frames 45000`:

| Arm | Env | Predicted verdict |
|---|---|---|
| **FIX-ON** | `POKEBOT_R20_OPENFENCE=1` | identical to M2-ON-s1 (`ground ROUTE101 (12, 10)`, `walk_battles 0`, `spin_battles 1`, `exit slot 5`, `party_after_walk 4`), plus **`walk_marker [True]`** |
| **FAULT-ON** | `OPENFENCE=1` + `POKEBOT_ENROUTE_FAULT_NOWALK=1` | the same verdict, with **`walk_marker [False]`** |
| **FIX-OFF** | nothing | identical to M2-OFF-s1, with `walk_marker [True]` |

**LONG-ON:** fixed code, `storyresume` on `r20_badge1_party1_gym.ss1`, flag ON, `random.seed(1)`, 480,000 frames. It
must replay M3-ON-s1 frame for frame: every `[DEXFENCE]`, `[CATCH]`, `[BATTLE] started` and `[STEP]` line. The fix
wraps the counter hunt's walk, and in that trajectory no party join happened on it.

## FALSIFIERS

- FIX-ON or FIX-OFF reads `walk_marker` other than `[True]`: the walk is not wrapped where the driver sees it.
- FAULT-ON reads `[True]`: the fault arm does not reach the marker.
- Any arm's verdict differs from its M2 twin in `ground`, `walk_battles`, `spin_battles`, `exit` or
  `party_after_walk`: the fix changed the ordinary HM hunt.
- LONG-ON differs from M3-ON-s1 in any listed line: the fix changed the ordinary story or the counter hunt.

## WHAT THIS DOES NOT SHOW

- **A real walk battle being refused, live.** None was found in 7 trajectories. It is proven by the pure gates only.
- **How often a hunt's walk meets a battle in real runs.** That is the log-count agent's question, a note.
- **The withdraw re-picks (audit site C).** They are not changed; their walks cross no land encounters.

## ADDENDUM — filed after the four graded arms and BEFORE the `healed101` arms: a LIVE walk battle

**Why:** the batch-log count (`2026-09-28-enroutejoin-FREQUENCY.md`, a NOTE) refutes "walk battles are rare":
- 81–90% of 84 real hunts met one on the walk;
- 21–26% met one where the flag would have caught a new species into the party;
- the Surf hunt's Route 101 → Route 103 walks alone met 38.

So a new driver arm, `R101_ARM=healed101` (tools only), heals, then walks the DRIVER to ROUTE101 (12, 10), then starts
the real hunt from there. That is the batch shape after the first ground failed. The driver's own walk shows as phase
"other", not the hunt's.

**Arms** (fixed code `409b5dda` plus this driver arm, `norman_done.ss1`, `random.seed(1)`, `R101_FENCE=real`,
`--set-balls 20`, `--frames 45000`):
- **H-FIX-ON:** `OPENFENCE=1`.
- **H-FAULT-ON:** `OPENFENCE=1` + `POKEBOT_ENROUTE_FAULT_NOWALK=1`.
- **H-OFF:** nothing set.

**Predictions (conditional).** With the flag ON, the driver's own walk can already catch, so a flag-OFF run cannot
preview the ON path. FIX and FAULT differ ONLY in the marker, and the marker is False outside a hunt's walk.
- **1.** H-FIX-ON and H-FAULT-ON are identical up to **B\***: the hunt's first walk battle where the party is below 6 and
  at full HP, the species is unowned, and more than 10 balls are spare.
- **2.** In **H-FIX-ON**, B\*'s row reads `phase=walk` with the fence reason "a hunt is walking to its ground — …", and
  no catch strategy. No walk-phase row starts a catch, `walk_joins` is `[]`, and the hunt reaches its spin (the exit is
  not "never caught one" at `spin_battles 0`).
- **3.** In **H-FAULT-ON**, the same battle (same frame, same species) reads `phase=walk` with a catch strategy. If the
  catch lands, `walk_joins` names it, and then:
  - if the species cannot learn Surf: the exit is `BotModeError: Hunted for a Surf learner but never caught one
    (timeout/balls).` with `spin_battles 0`;
  - if it can (Zigzagoon or Lotad): the exit is that slot, with `spin_battles 0`.
- **4.** **H-OFF:** every walk-phase fence reason is "runway" (or an earlier gate). No catch starts in any phase.

**VACUOUS** if H-FIX-ON has no B\*, i.e. no walk-phase row with the "a hunt is walking" reason. That is reported as
vacuous, not as a pass.

**Falsifiers**
- H-FIX-ON starts a catch in phase walk.
- H-FIX-ON and H-FAULT-ON differ before B\*.
- H-FAULT-ON refuses B\* (the fault arm does not reach the marker).
