# PRE-REGISTERED PREDICTIONS — PIECE 2a: the frame purse + the out-level selector (2026-09-19)

> ⛔⛔ **WRITTEN AND COMMITTED BEFORE THE PRODUCTION EDIT.** Graded afterwards, honestly.

---

## WHY THIS IS THE SAFETY FOUNDATION AND GOES FIRST

I stated a hard prerequisite: **a frame budget lands before any live selector can route training at
Victory Road.** A bare `train_team` has only a 500-round guard, and KI-28 burned 19.9M frames on
exactly that shape.

✅ **VERIFIED AT SOURCE, AND IT IS WORSE THAN A MISSING CAP — THE EXISTING CAP COUNTS THE WRONG
THING.** `_yield_bounded` (`early_game.py:1668-1687`) is `for _ in range(max_frames): next(gen)` —
it counts **its own advances of the story generator**. But `main.py:148` advances **only the top of
the controller stack** (`next(context.controller_stack[-1])`), and a battle pushes its own
controller on top. ⇒ during a grind — which is almost entirely battle frames — **the story
generator is not being advanced, so `_yield_bounded`'s counter does not tick.** A budget expressed
in those units silently buys far more real time than it says.
⭐ The correct precedent already exists: `_FORTREE_MAX_TOTAL_FRAMES` (`early_game.py:7067-7084`)
uses `context.emulator.get_frame_count()` as *"a hard backstop independent of the above counters"*.

## THE OTHER HALF: THE LADDER LEAKS WITHOUT AN OUT-LEVEL RULE

✅ MEASURED (`probe_training_ladder.py`): asking `best_training_area` for the CLOSEST band leaks at
**L12, L18-L20, L24, L35-L38** — the trainee is 2+ below the band's top, so the swap fires and the
finisher banks an equal share. ✅ Re-measured with an out-level rule (`trainee >= hi - 1`):
**zero leaking rungs, and no level without a ground.**

---

## THE CHANGE (Piece 2a — two additions, no leg, no Fly yet)

1. **`_yield_bounded_by_frames(gen, real_frames)`** in `early_game.py` — `_yield_bounded`'s shape
   with the correct denominator: `context.emulator.get_frame_count()`. Returns True if the
   sub-generator finished, False if the bound expired. ⛔ Its docstring must state the failure mode
   it does NOT cover: a sub-generator that loops in pure Python without yielding never returns from
   `next(gen)`, so no wrapper of this shape can bound it.
2. **`max_wild_max` on `best_training_area`** — optional, default `None` (today's behaviour
   exactly). When given, refuse any area whose top wild exceeds it. A caller wanting the out-level
   rule passes `max_wild_max=mon.level + 1`.
   ⭐ WHY A NUMBER AND NOT A MARGIN: `UNDERLEVEL_MARGIN` lives in `plugins/custom_modes/story_mode.py`
   and `training_areas.py` is a `modules/` file — importing the plugin would invert the layering.
   The caller already knows the margin; the picker only needs the resulting cap.

---

## PREDICTIONS

### P1 — `max_wild_max=None` changes nothing, at every level
**PREDICT:** `best_training_area(lvl, allow=X)` returns **byte-identical** answers before and after,
for every level 2-100, at `allow=None` and at a permissive `allow`.
⛔ **FALSIFIER:** any difference. **This is the STOP condition** — an optional parameter that alters
the default is a silent behaviour change to a shared picker, and I revert.

### P2 — `max_wild_max=lvl+1` reproduces the corrected ladder exactly
**PREDICT:** it yields ROUTE117 for L15-20, ROUTE111 L21-24, ROUTE115 L25-26, ROUTE118 L27,
ROUTE121 L28-38, VICTORY_ROAD_1F L39-75 — **zero leaking rungs, no level without a ground.**
⛔ **FALSIFIER:** any leaking rung, or any level answering `None`.

### P3 — the two frame counters genuinely disagree
**PREDICT:** driving any generator that fights a battle, `get_frame_count()` advances **strictly
more** than `_yield_bounded`-style iteration counting. ⭐ I predict the ratio is **well above 1**,
and I deliberately do NOT predict a value — a figure of ~5.5× appears in the research and I have
not measured it myself.
⛔ **FALSIFIER:** if they advance together, my model of the controller stack is wrong and the whole
purse design is unnecessary.

### P4 — gate #66 still passes, and the new parameter does not widen any existing caller
**PREDICT:** all 66 enforcing gates pass; no existing call site changes behaviour.
⛔ **FALSIFIER:** any red gate not attributable to stale prose.

### P5 — ⚠ THE ONE I AM LEAST SURE OF: no other consumer of `best_training_area` breaks
**PREDICT:** adding a keyword-only parameter with a `None` default breaks nothing.
⛔ **FALSIFIER:** any caller that passes positionally beyond `team_level`. ⚠ **I was wrong about
exactly this shape yesterday** — I missed `_hm_hunting_grounds` as a third consumer of
`TRAINING_GRASS`. So this time I will **grep for every call site and name them** rather than assert
an absence, and the suite is the test, not my confidence.

---

## WHAT WOULD MAKE ME STOP
1. **P1 fails** — the default changed ⇒ revert immediately.
2. **P3 fails** — the counters agree ⇒ the purse premise is wrong ⇒ stop and re-derive.


---

# ✅ GRADED, 2026-09-19 — 4 CONFIRMED, 1 CONFIRMED-STRUCTURALLY, 0 REFUTED

| # | Prediction | Outcome |
|---|---|---|
| P1 | ⭐ **STOP** — `max_wild_max=None` changes nothing | ✅ **CONFIRMED** — omitting the parameter and passing `None` give identical answers at **every level 2-100**, for both `allow=None` and a permissive predicate. Spot checks unchanged: `allow=None` L53 → ROUTE117; permissive L53 → VICTORY_ROAD_1F. |
| P2 | `max_wild_max=lvl+1` reproduces the corrected ladder | ✅ **CONFIRMED EXACTLY** — ROUTE117 L15-20, ROUTE111 L21-24, ROUTE115 L25-26, ROUTE118 L27, ROUTE121 L28-38, VICTORY_ROAD_1F **L39-75**. **Zero leaking rungs; no level without a ground.** |
| P3 | ⭐ **STOP** — the two frame counters genuinely disagree | ✅ **CONFIRMED STRUCTURALLY, NOT NUMERICALLY — and the distinction is deliberate.** `_listeners.py:120` does `context.controller_stack.append(self.fight(action))`, and `main.py:148` advances only `controller_stack[-1]`. ⇒ during a battle the story generator underneath is **not** advanced, so `_yield_bounded`'s counter cannot tick. ⚠ **I did NOT measure the ratio** — that needs the harness's real main loop, and my prediction deliberately named no value. A ~5.5× figure appears in the research and **remains unverified by me**. |
| P4 | gate #66 passes; no caller widened | ✅ **CONFIRMED** — all 66 enforcing gates pass. |
| P5 | ⚠ no other consumer breaks | ✅ **CONFIRMED, AND THIS TIME BY ENUMERATION RATHER THAN ASSERTION.** I greped and NAMED every call site: production is `counter_hunt.py:647`, `story_mode.py:3177`, `:3208` — all keyword-only — plus ~20 in `tools/`. **No caller passes positionally beyond `team_level`**, so a keyword-only parameter with a `None` default cannot reach them. *(Yesterday I asserted this shape and missed `_hm_hunting_grounds`; enumerating is the correction.)* |

‼ **AND THE LINE-SHIFT TAX CAME DUE A THIRD TIME.** Adding 37 lines to `early_game.py` staled
**16 citations across 6 files**. Every one was caught by running `audit_doc_citations.py`
immediately after touching the `.py` — the rule written this morning, working as intended.
⚠ One was subtler than a shift: `early_game.py:2101` cited `train_team`'s **round guard**, not its
`def`. Re-pointed to the def (`:2106`); the guard now lives at `:2138`, and prose that means the
guard should say so rather than borrow the function's citation.
