# Meandering / organic movement — design and verdict (2026-07-26)

> From a five-angle research pass: navigation-stack audit, adversarial risk analysis,
> algorithm design, puzzle catalogue, and human-perception (Gemini notes in
> `ai-research-notes/2026-07-26-pathing/`). Decisions here; evidence cited inline.
> Punch list: `#24-meander` (travel), `#24-grasswander` (training).

---

## 0. THE VERDICT UP FRONT

**Randomising TRAVEL routes is net-negative at the moment and should not ship as the first
step. Randomising TRAINING movement and TIMING is nearly free and should ship first.**

The two requests look alike and have opposite risk profiles. The reason is arithmetic.

---

## 1. Why travel meandering is dangerous — the numbers

Route 110 has `encounter_rate: 20` ⇒ `20×16/2880` = **11.11 % per step on foot**.
Path length feeds encounters **linearly**, but feeds *whiteouts* **super-linearly**, because a
whiteout forces re-traversal of the same grass.

Expected traversals per successful crossing = `1/(1−p)`. At the observed p ≈ 0.5 for a Route
110 leg:

| | exact path | +30 % longer |
|---|---|---|
| p(whiteout per traversal) | 0.500 | 1 − 0.5^1.3 = **0.594** |
| traversals per crossing | 2.00 | 2.46 |
| whiteouts per crossing | 1.00 | **1.46** |

**A 30 % longer path costs ~46 % more whiteouts on that leg.** Runs die on the whiteout cap.
This is super-linear pressure on the exact resource that kills runs.

Two discrete cliffs make it worse: **Repel is a fixed STEP budget** (expires mid-grass), and
**poison is 1 HP per 4 steps** — and a poison whiteout logs **no battle at all**.

### The worst interaction: it moves damage into the UNMITIGATED bucket
Survival mode flees wilds after 3 defeats per map — **wild-only, because trainer battles
cannot be fled**. Meandering adds wild encounters (mitigated) *and* walks into trainer sight
cones the canonical line dodged (`trainer_see.c:301-325`) — **un-fleeable, and
`_defeat_counts` escalation is boss-scoped**. That is precisely the P2 failure we just fixed:
19 losses / 44 whiteouts at ROUTE110 (34,56), a trainer ambush opened with a weak lead.

### Every prior navigation failure gets MORE likely, none get less
The Granite Cave 1F one-way-ledge ping-pong (the fix was "pick the furthest-along pathable
step" — a randomiser re-introduces the first-match bug); the Route 104 oscillation that
produced `NavigationStuckError` (its mechanism *is* mid-walk re-targeting); the KI-24
dual-elevation bridges that read as walls (a false "no path" errors nothing — **silent**);
warp-split maps; and KI-17's mid-navigation uncontrollable avatar, which meandering simply
buys more lottery tickets for.

---

## 2. The algorithm, if and when we do it: seeded per-tile cost jitter

Not waypoint sampling, not k-shortest-paths. **Add a bounded non-negative noise term to the
per-step cost already computed in `map_path.py`**, drawn from a pure hash of
`(leg_key, tile coords, elevation)` — no RNG stream, no extra search.

```python
EPSILON_MAX = 0.25
cost += eps * uniform_hash(leg_key, gx, gy, elev)   # in [0, eps)
```

**Why it is provably safe on tile-type decisions.** The existing cost model already charges
**+1000 for encounter tiles, +10000 for scripted triggers, +1000000 for warps**. Noise is
capped below 1 per step, so a 1000-tile leg accrues < 250 total. **No meander can ever flip a
grass, script, or warp decision.** Waypoint sampling has no such guarantee — it routes
*through* grass and can pick unreachable tiles.

**The bound:** `len(meander) ≤ (1 + ε) · len(exact)`, so ε = 0.25 caps deviation at 25 %.
It self-scales: on a 4-tile indoor hop no deviation is affordable at all (pure tie-breaking);
on a 60-tile route leg, up to ~15 tiles of wander.

**Reproducibility, and the retry trap:** because it is a pure hash and not a stream, a mid-leg
re-path re-derives the *identical* cost field and resumes along the same "wind" — where a
stream RNG would oscillate between two different meanders. A leg retried after an interruption
is bit-identical.

**Escape hatch:** once `no_progress_repaths >= 4` (half the wedge budget), force `ε = 0` for
the rest of the leg, so a stuck leg converges onto the path we already know terminates.

**Personality feeds ONE knob:**
`eps = 0.25 · curiosity · (1 − 0.6·caution)`, and `eps = 0` on urgent legs (heading to a
Centre, post-whiteout return, low HP). ‼ `caution` **only ever shrinks** ε — it can never
lengthen a walk, satisfying the §6 rule directly.

**Default exact, meander opt-in.** `map_path`/`walking` are shared with upstream bot modes
where a meander is pure harm. The story layer gets a thin wrapper that fills `meander` from
personality; puzzles opt out with `exact=True`.

---

## 3. Timing: the cheap win, and where it must NOT go

‼ **Never insert idle frames inside `follow_waypoints`.** Its per-waypoint budget is 20 frames
against a ~16-frame step — any inserted pause converts a healthy step into a timeout, forcing
a re-path and advancing the `_NAVIGATE_NO_PROGRESS_REPATHS = 8` counter toward a **spurious
`NavigationStuckError`**. A meander must never look like a wedge to the wedge detector.

**Do instead:** a seeded idle of 0–45 frames *between legs* and after map transitions, plus a
per-leg seeded `run=True/False`. Cap added idle at 120 frames per leg, debit it from the same
frame budget the watchdogs read, and log it.

There is precedent: the naming-screen RNG-decorrelation pause is already a seeded randomised
wait.

---

## 4. `#24-grasswander` — the request that IS nearly free

While TRAINING, extra steps mean more encounters, which is **the entire point**. The cost that
makes travel meandering dangerous is a *benefit* here.

The seam already exists: **`run_in_circle` (`walking.py:706`) proves `follow_waypoints` accepts
an arbitrary waypoint generator.** A bounded random-walk generator drops straight in with no
pathfinder change.

Must preserve all three existing guards (each has scar tissue): the whiteout abort; the
no-EXP-progress watchdog (which already un-sticks a bot that wandered out of grass); and the
leftover-script clear (an active script **suppresses** wild encounters).

Bound the walk to a **verified safe tile set** — not "anywhere walkable" — to avoid trainer
sight cones beside the patch, ledges, and hazard floors.

‼ **Verify before designing:** does turning in place generate encounters at the same rate as
stepping? If spinning is already step-equivalent this is cosmetic; if stepping is faster it is
also a throughput win. Do not assume either.

---

## 5. NO-GO list for randomness (evidence-based)

1. Any map with forced movement — Sootopolis ice (`VAR_ICE_STEP_COUNT` is stateful and can
   become unsolvable), Sky Pillar cracked floors, Aqua/Magma spin mats, Pacifidlog/Fortree
   bridges, currents, muddy slopes.
2. **Routes 118/119/120** — the reachability oracle is known wrong there (KI-24); randomness
   over a wrong oracle is undetectable.
3. Ledge-as-connection maps (Granite Cave 1F, Fortree Gym) — reachability is *directional*.
4. **Last-heal → boss legs** — whiteout cost is maximal there.
5. Within trainer range of any un-fought trainer on a travel leg — un-fleeable, unmitigated.
6. Indoor / NPC-walked maps — `calculate_path` seals rooms behind moving NPCs.
7. Any segment containing coord_events — our top derail class.
8. Inside `train_team` legs and whiteout walk-backs.

Exact-tile call sites that must never vary: `_enter_warp_by_navigation`, `_walk_warp_chain`,
`_pass_through_door`, `_walk_through_warp`, `PETALBURG_GYM_CHAIN`, and every `*_APPROACH`
tile. **There is currently NO flag in the code separating "must be exact" from "just get
there"** — which is exactly why meandering must be opt-in, never opt-out.

---

## 6. RECOMMENDED ORDER

1. **`#24-grasswander`** — organic training movement. Nearly free, visible, low risk.
2. **Timing variation at leg boundaries** — biggest perceived-realism win per unit of risk,
   and it does not lengthen any path.
3. **Per-leg instrumentation** — log `(map, planned_path_len, actual_steps, wilds, trainers,
   whiteouts)` beside the rolled personality values. ‼ Without `planned_len` vs `actual_steps`
   a meander regression is **indistinguishable from a strategy regression**, and that silent
   unattributable degradation is the real risk — more than any single mechanic above.
4. **Only then** travel meandering, at a small ε, on safe legs only, measured against the
   canary below.

**The canary we already have:** losses:whiteouts is currently **exactly 1:1**. Poison-step
faints produce whiteouts with *no battle logged*, so **the ratio breaking above 1.0 is
unambiguous evidence of step-count damage**. If the ratio holds at 1.0 while frames-per-map
rises, that is pure meander tax with no safety cost.
