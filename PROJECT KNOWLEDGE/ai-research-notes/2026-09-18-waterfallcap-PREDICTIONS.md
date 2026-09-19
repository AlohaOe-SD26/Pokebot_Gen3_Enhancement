# PRE-REGISTERED PREDICTIONS — `#24-waterfallcap` (2026-09-18)

> ⛔⛔ **WRITTEN AND COMMITTED BEFORE THE PRODUCTION EDIT.** Graded afterwards, honestly. A reading
> that contradicts a prediction here is a **RESULT**, not a failure of the instrument — this file
> exists so that I cannot quietly re-interpret an outcome after seeing it.

---

## THE CHANGE

`sandbox-pokebot/modules/story/region_reach.py`, `_resolve_caps` (`:228-236`). Today it builds
`explicit` from four hardcoded keys — `surf`, `rock_smash`, `cut`, `strength` — and returns a dict
built by iterating **that dict only**. `_GATE_MOVE_NAMES` (`:100-106`) holds **five**, including
`"waterfall": "Waterfall"`, and `_RSE_BADGE_BY_MOVE` already maps `"Waterfall" -> "BADGE08_GET"`
with the comment *"Added with the Victory Road gate below."*

**The fix:** resolve every gate `_GATE_MOVE_NAMES` knows about, instead of a hardcoded four, so the
move-name table is the single source of truth and this bug class cannot recur. A `can_waterfall`
keyword is threaded through for symmetry with the existing four.

⭐ **WHY THIS SHAPE AND NOT "ADD ONE KEY":** the bug is that two tables must agree and nothing
enforced it. Adding a fifth literal leaves the same trap for a sixth gate. Deriving from
`_GATE_MOVE_NAMES` makes the trap structurally impossible, and a new gate asserts it stays that way.

---

## WHAT IS ALREADY MEASURED (not predictions — evidence, cited)

* `evidence/2026-09-18-waterfall-capability.stdout.txt` — the bug in **both** directions on 3
  fixtures; the parties **do** carry Waterfall (Wailord, `BADGE08_GET` true,
  `_live_capability('Waterfall')` true); `reachable_maps()` = **306** from Ever Grande, **3** from
  the grind tile; VR would sit **1-2 hops** away, inside `_MAX_TRAINING_TRAVEL_LEGS = 4`.
* `evidence/2026-09-18-waterfall-fix-AB.stdout.txt` — an in-process A/B of the exact fix:
  * `reachable` flips; **`huntable` never does**, on any fixture, for Fighting/Ghost/Dark;
  * **`best_huntable` (the only function an executor may act on) is IDENTICAL in both arms**;
  * every `allow=None` and `allow=_training_area_allowed` picker answer is IDENTICAL;
  * the ONE actionable change: `best_training_area(allow=_counter_area_allowed)` goes
    `None -> ROUTE121(44,14)(25,28)` — **only when standing INSIDE Victory Road**;
  * **arm C** (fix + `#24-trainingbrackets`' proposed row) leaves Victory Road **still not
    huntable**, because `hunt_ground_tile` defaults `require_driven=True` and in that mode never
    reads `TRAINING_GRASS` at all. Proven live by the contrast: the identical call at
    `require_driven=False` returns `(15, 39)`.

---

## PREDICTIONS

### P1 — the repro that pins today's answer keeps passing, for a BETTER reason
`tools/story-dev/repro_region_reach.py:218-238` asserts `is_map_reachable(VICTORY_ROAD_1F) is
False`, same for `B1F`, `EVER_GRANDE_CITY is True`, and that the refusal NAMES Waterfall.
**PREDICT: still PASSES, exit 0, output unchanged.** It loads `devon_scope_got.ss1` (`:39`), a
mid-game state around Badge 6 — no `BADGE08_GET`, no Waterfall user — so `_live_capability` resolves
False and the edge stays closed **for that party**.
⭐ **The meaning changes even though the output does not:** today it passes because *nobody* can
pass; afterwards it passes because *this party* lacks Waterfall. That is the difference between a
seal and a gate.
⛔ **FALSIFIER:** if it FAILS, my model of `_live_capability` is wrong — most likely
`devon_scope_got.ss1` has Badge 8 or a Waterfall user, or `badges=None` does not mean "read live".
**That would mean the fix is wrong, not the repro.**

### P2 — the two `"surf"` edges are untouched
`KNOWN_GATES` has exactly three rows; two are `"surf"` (Dewford ↔ Route 106/107).
**PREDICT: every Dewford/Route106/Route107 reading in `repro_region_reach.py` is byte-identical**,
including its explicit `can_surf=True/False` cases at `:108-113`.
⛔ **FALSIFIER:** any change there means I altered resolution for gates I did not intend to touch.

### P3 — the full gate suite stays green
**PREDICT: all 64 enforcing gates PASS, unchanged.** No gate asserts Victory Road reachability;
`probe_maintain_unreachable.py` / gate #55 read `TRAINING_GRASS`, which has no Victory Road row
(Victory Road is in `PENDING_GRASS` with `tile=None`, which neither picker iterates).
⛔ **FALSIFIER:** a red gate names a consumer the census missed ⇒ stop and re-census.

### P4 — the A/B's arm B becomes the new arm A
Re-running `probe_waterfall_fix_ab.py` after the fix, **PREDICT the probe declares itself VOID** —
specifically "THE ARM APPLIED BUT `is_map_reachable(VICTORY_ROAD_1F)` NEVER FLIPPED" — because the
patch and production now do the same thing, so there is no delta left to measure.
⭐ That is the CORRECT behaviour for a self-checking A/B whose subject has been fixed, and it is the
cleanest possible confirmation that production now matches the arm I measured.
⛔ **FALSIFIER:** if it still reports differences, production is NOT doing what the arm did.

### P5 — the new gate fails BEFORE the fix and passes AFTER
A new `probe_caps_resolve_every_gate.py` asserts that `_resolve_caps` resolves **every** gate string
`KNOWN_GATES` uses. **PREDICT: it FAILS on today's code naming `"waterfall"`, and PASSES after.**
⛔ **FALSIFIER:** a gate that passes before the fix is testing nothing — it would be decoration, and
this project's rule is that an unfault-tested gate is worse than none.

### P6 — the live re-measure flips, and the world stops being 3 maps
Re-running `probe_waterfall_capability.py` after the fix, **PREDICT**: on
`post_ch24_atdoor_L75.ss1` `is_map_reachable(VICTORY_ROAD_1F)` becomes **True** and
`why_unreachable` becomes `"reachable"`; from `grind_stall_ppzero.ss1`, `reachable_maps()` goes
**3 → 309** and `EVER_GRANDE_CITY` becomes reachable.
⛔ **FALSIFIER:** anything less than 309 from inside the cave means the cluster has an edge I have
not accounted for.

### P7 — ⚠ THE ONE I AM LEAST SURE OF: nothing in production consults reachability inside Victory Road
The census found **zero** `region_reach` references in `victory_road.py` and `pokemon_league.py`, so
the `None -> ROUTE121` counter-picker change should be unreachable in practice.
**PREDICT: no behavioural change in any §Ch23/§Ch24 drive.**
⛔ **FALSIFIER:** any drive that newly proposes Route 121 from inside the cave. ⚠ I rate this the
weakest prediction here: it is an absence claim over a large codebase, and **I have broken exactly
that rule once today already** (concluding "no committed artifact" from a one-directory grep). It
rests on someone else's census plus my own greps, not on a drive.

---

## WHAT WOULD MAKE ME ABANDON THE CHANGE

1. **The adversarial pass finds the omission was deliberate** — a commit message or reverted change
   showing someone left `_resolve_caps` alone ON PURPOSE. ⭐ The `:88-96` comment shows the edge was
   added deliberately to CLOSE the cluster (`#24-counters` blocker #3) because Victory Road's
   Hariyama *"ranks #1 the instant anything calls the map reachable"*. That is a real, documented
   intent to keep it shut, and it is the strongest argument against this change. My answer is that
   the same comment says *"HM07 is mandatory to stand on it"* — i.e. the author wanted a **gate**,
   not a seal — and the A/B shows the executor-level guard (`hunt_ground_tile`) holds regardless.
   **But if the history shows otherwise, I stop.**
2. **The decomp pass shows the edge needs more than Waterfall** (e.g. Surf too), making a
   single-gate model unfaithful — then the fix would make the bot believe something false.
3. **The decomp pass shows exiting Victory Road needs no field move**, which would mean the
   SYMMETRIC seal is itself wrong and the fix is incomplete rather than complete.
