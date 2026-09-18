# §Ch24 POST-WALLY GRIND — THE ECONOMICS, MEASURED, AND THE QUESTION I WAS ASKING WAS WRONG (2026-09-18)

> ⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** A 10-agent workflow (5 recon angles, each adversarially
> refuted) produced this. Everything marked ✅ was re-verified BY ME at FILE:LINE or by running it.
> Everything else is labelled with who claimed it and how.
> ⛔⛔ **DOES NOT REOPEN THE STANDING RULING.** Segment 24 stays unwired; four prerequisites are open.

---

## ⭐⭐ THE HEADLINE: THE FRAMING WAS WRONG, AND THE ADVERSARIAL ANGLE KILLED IT

I framed the next step as *"price one heal round-trip from B1F versus 1F, and the ground question is
settled."* **That framing is refuted, and I verified the refutation myself.**

✅ **`estimate_frames_to_level` — the guard that decides whether a grind runs AT ALL — contains NO heal
term and NO travel term.** Its entire computation, read line by line with comments stripped:

```
needed_exp     = level_up_type.get_experience_needed_for_level(target) - mon.total_exp
xp_per_battle  = _CALIBRATED_AVG_WILD_BASE_EXP_YIELD * wild_level / 7
battles_needed = ceil(needed_exp / xp_per_battle)
return           battles_needed * FRAMES_PER_WILD_BATTLE
```

⇒ **the heal round-trip is structurally invisible to the refusal. Pricing it cannot move the guard by
one frame.** I spent a working session optimising a variable the deciding code cannot see.
‼ And under that guard's own model the ground choice is worth **4.79%** (1F 286.9 vs B1F 301.2 modelled
xp/battle) against a required **2.05× cut** — two orders of magnitude apart.

---

## ⭐⭐ THE ACTUAL FIX IS ALREADY BUILT, AND THE GUARD ALREADY PERMITS IT

✅ **The ceiling is PER-CALL BY EXPLICIT DESIGN, and the code says so in its own words**
(`victory_road.py:2012-2019`, read by me, verbatim):

> *"⛔⛔ THE CEILING IS PER-CALL, NOT PER-TOTAL, AND THE DISTINCTION IS THE WHOLE POINT. KI-28's
> 19.9M-frame livelock was ONE `train_team` call chasing a level the local grass could never deliver —
> an unbounded call, not a large sum of bounded ones. … summing them and refusing would be measuring
> the wrong quantity … ⇒ refuse any SINGLE mon whose grind is unaffordable."*

and the test is `worst = max(estimates.items(), …)` — **one mon, one call.**
⇒ **A STEPPED GRIND, EACH STEP UNDER THE CEILING, IS ALREADY PERMITTED. NOTHING NEEDS RELAXING.**

⭐ **AND THE SHAPE EXISTS AND HAS RUN.** `Ch24GrindMode` (`story_harness.py:15393-15689`) is a stepped
loop of `train_for_victory_road(target=low+STEP)` with `STEP=2`, `MAX_STEPS=24`, `MAX_RETRIES=2`, a
save-state checkpoint after **every** step, and a refuse-to-spin break. Its checkpoint ladder
(`post_e4grind_L49 … L73 + FINAL`) is on disk from 2026-09-17.
⇒ **the work on `#24-levelgap` is to PROMOTE THAT SHAPE into production — not to invent a design, not
to fix the estimator, and not to choose a ground.**

⚠ **ONE RECORDED OBSTACLE TO STEPPING, and it must be checked before building:** `team_is_ready(target)`
(`victory_road.py:2135-2141`) raises terminally, and its Crunch clause (`:1903`) hardcodes
`CRUNCH_LEVEL = 47` instead of `target`. That is the surviving reason §Ch23's **sub-47** stepping was
refuted on 2026-09-08. *(INFERRED, by the recon and not verified by me: it does not bite a post-Wally
grind stepping UPWARD from 47, because the clause is already satisfied at 47+.)* **Verify before use.**

---

## ✅ THE ECONOMICS, NOW MEASURED FROM REAL RUN LOGS (not modelled)

| quantity | value | provenance |
|---|---|---|
| 1F heal round-trip | **~2,178 f median (n=278)** / 2,812 f mean (n=30) / ~2,306 f marginal | three angles, three different logs |
| heals per battle | **1 per 8.3** (75 heals / 623 battles) and 1 per ~10.4 (0.0964/battle) | two angles, independently |
| heal share of a grind | **10.0%** of the 623-battle run's 1,649,751 frames | control angle |
| what actually triggers a heal | **HP, never PP** — `heal_at` = 42.0% of party MIN HP; **0** out-of-PP heals in 2,928 logged battles | healfreq angle |
| `set_swap_train` effect | **not what I assumed** — `UNDERLEVEL_MARGIN = 2` cannot fire at L47+ vs L≤42 wilds; RotateLead fired in only 77/1575 (4.9%) | healfreq angle |

⭐ **WHY 1F HEALS ARE CHEAP, AND IT IS A COINCIDENCE WORTH KNOWING:** `TRAIN_SPOT_1F (15,39)` **IS**
`VR_EXIT_APRON` — one step from the arrow warp. The heal is nearly free *because the spin tile sits on
the exit*.

---

## ⛔⛔ A LATENT LANDMINE THIS TURNED UP — VERIFIED, AND UNRESOLVED

✅ **`_exit_training_cave_if_inside()` DOES NOT KNOW VICTORY ROAD.** `grep -c VICTORY_ROAD
sandbox-pokebot/modules/story/early_game.py` → **0**. `_CAVE_EXITS` (`:2003`) holds exactly two
entries: `GRANITE_CAVE_1F` and Fiery Path. Its own docstring: *"A cheap no-op anywhere that is not in
`_CAVE_EXITS`."*

And the comment it sits under (`:2154-2157`) records a MEASURED failure:
> *"CAVE-AWARE HEAL (2× real-HW Manual drops 2026-07-22): healing from INSIDE Granite Cave targeted the
> Dewford PC **across warp levels** — the global navigator can't do that ('not on connected maps').
> Exit the cave first."*

⇒ **healing from inside Victory Road works today ONLY because the 1F spin tile is already at the exit.**
A spin tile one warp deeper (i.e. B1F) would rely on the navigator crossing warp levels — the exact
documented failure. ⛔ **UNRESOLVED: I could not settle it statically** — `heal_in_pokemon_center` uses
`navigate_to_anywhere` (`higher_level_actions.py:465`), a warp-chaining graph navigator that needs live
state, **not** `calculate_path`. ⇒ **the cheap decisive experiment is a drive: park at a B1F chamber
tile, force a heal, observe.** Until then, treat "B1F can heal" as UNPROVEN.

---

## ✅ THE B1F POCKET IS SEALED — TWO INDEPENDENT METHODS AGREE

* The recon measured it by reachability from `(8,3)`: `(8,10)` and `(30,25)` both REFUSE while `(5,7)`
  is 9 wp.
* ✅ **I measured it separately** with `calculate_path` and explicit controls: **3/3 controls route**
  (ladder → each candidate, 2–3 waypoints) and **0/5 trainers are reachable** from the ladder pocket,
  as is the B2F warp.

⇒ **the five B1F trainers are not merely 16+ tiles away — they are UNREACHABLE from the grind corner**
while the puzzle is unsolved. ⭐ **And the puzzle RESETS on every warp, so the isolation is
SELF-RESTORING on every entry.** The property framed as B1F's penalty is, for a pocket-parked grind, a
guarantee.
⚠ **The honest limit:** "unreachable" means *the planner will not route it without pushing a boulder*.
The party has Strength, so the isolation is a property of the BEHAVIOUR (a parked spin pushes nothing),
not of the map.

---

## ⚠ TWO NUMBERS IN OUR OWN TREE ARE NOW IN DOUBT — RECORDED, NOT RESOLVED

1. **`~3,192` frames/battle at Victory Road** (`07-CHANGELOG.md:24640`, and I carried it into this
   workflow's brief as established). **Two independent angles measured it from real logs as 2,138 and
   2,384–2,648.** ⛔ I have NOT adjudicated this and am not asserting either figure — but a number this
   load-bearing disagreeing by ~33% must not sit unflagged. *(Note the direction: a LOWER frames/battle
   makes every grind CHEAPER than the committed analysis assumed.)*
2. **The `+22.6% battle duration cancels the +22.6% xp edge` claim is arithmetically false** (refuter):
   only the per-battle term scales, while the inter-battle gap and heal overhead are fixed. **Break-even
   is ~+45%, not +22.6%.** B1F is 30% Steel-type (Lairon 25% + Mawile 5%) vs 1F's 15%, so a higher
   frames/battle is *expected* — but the bar is +45%.

---

## VERDICT ON THE GROUND QUESTION

**B1F is ahead on every economic estimate produced (+10% to +22% xp/frame), and its two supposed
penalties are gone: the trainers are unreachable and the puzzle is untouched by a pocket grind.**
⛔ **But the ground question is NOT the blocker, and that is the whole point of this note.** Both grounds
refuse the per-call ceiling; the fix is stepping, which is already permitted and already demonstrated.
⇒ **Choose the ground LAST, after the stepped leg exists** — and only if the B1F heal is proven to
navigate at all.

## ⛔ WHAT THIS DOES NOT ESTABLISH

* No drive was run. Every frame figure here comes from EXISTING logs or from arithmetic over them.
* B1F's own frames/battle has never been measured. The recon's suggested purchase — a ~20-battle spin
  at a chamber tile — would settle it, *and would settle the heal-navigation question in the same run.*
* ‼ **One of my own probes produced a false hard-blocker and the CONTROL caught it.** Routing
  B1F→Poké Center REFUSED — but so did the 1F control, which is known to work 278 times in real logs.
  ⇒ wrong instrument, reported INCONCLUSIVE rather than as a finding. **That is the third time in two
  days a control changed the answer, and the second time it prevented a fabricated defect.**
