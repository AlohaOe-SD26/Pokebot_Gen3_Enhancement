# 2026-09-26 — USER RULING 19 (teach an owned TM when a gym keeps winning): GRADED

> Predictions: `2026-09-26-ruling19-gymtm-PREDICTIONS.md` (design 3 table filed at `d44e5850`; the design-4 addendum
> at `d82db53c`, both BEFORE the drives they predict). Evidence: `tools/story-dev/evidence/2026-09-26-gymtm-*.txt`
> (driver log) + `*.stdout.txt` (console). Code: branch `wt/ch24organic`, `modules/story/gym_tm_teach.py`.

## The design history (why the shipped design is the fourth)

| Design | Wall | Refuted by | What it would have done |
|---|---|---|---|
| 1 | `roster[kos]` (KO count as an index) | a decomp read — only a trainer's LEAD is party order; every replacement is the AI's pick (`battle_ai_switch_items.c` `GetMostSuitableMonToSwitchInto`) | named the wrong foe; vs a Fire/Fighting lead Skarmory comes out SECOND |
| 2 | (same) + "exclude HM carriers" | observe-only run on `fortree_gym_wedge.ss1` | excluded Sceptile, the lead, because it knows Rock Smash |
| 2b | slot rule "a move whose type another shares" | the same run | Sceptile (four types, no status) could never learn; Blaziken would have lost Double Kick (STAB) and kept Scratch |
| 3 | the LAST foe we faced, by identity | an adversarial review (Claude agent) | 10 of 14 fixture plans went to a mon the RULED lead/replacement order fields LAST (Grass / Fire-Fighting vs an all-Flying gym); a taught Rock Tomb switched off the counter ladder and the honest stop; gym TRAINER losses (Skarmory/Tropius/Pelipper) would have named walls |
| **4 (shipped)** | **our faints per foe, leader battles only, ≥2 losses** | — | see below |

**MEASURED in the live batch** (the day's `[TURN]` lines, the foe faced last before each Winona loss, 145 losses):
Skarmory 71, **Altaria 64**, Pelipper 5, Tropius 4, Swablu 1 — the wall is per run. Juan (45): Kingdra 40,
Crawdaunt 5 — nothing we own is 2x on Kingdra. 15 of the 19 runs with Winona losses had a species/level candidate
for their own wall (moves unknown from logs). ⚠ That count was the design-3 filter; design 4 (reach + duel) is stricter.

## Drives, graded against the predictions

| # | Result | vs prediction |
|---|---|---|
| P1 (design 3) | teach exactly as predicted (TM34 → Loudred#B2768B68 replacing Pound, TM34 1→0, 1,842 frames, OVERWORLD, tripwire); ACCEPTANCE FAIL | the two failing conjuncts were the DRIVER's continue check (a missing argument ⇒ `read_error`) |
| Q1 → Q1b → **Q1c PASS** | TM50 Overheat → Loudred replacing Pound, share 100%, TM50 1→0, nothing else changed | **as predicted**; Q1/Q1b failed only the driver's continue target (below) |
| Q2 → Q2b → **Q2c PASS** | TM34 Shock Wave → Loudred replacing Pound, TM34 1→0 | **as predicted** |
| **Q3 PASS** | NOTEACH: planned TM50 → Loudred, latched, nothing taught | as predicted |
| Q4 **FAIL** → fixed → **Q4c PASS** | budget 600 expired on "Delete a move?"; the first close answered the prompts only until the first no-dialogue frame (a message sits BETWEEN the two prompts), then handed to the plain B-only close, which ping-ponged "Delete a move?" ⇄ "Stop trying to teach?" and gave up in **PARTY_MENU** | **a RESULT, not a driver failure** — the recovery was wrong; the unified loop (`_leave_teach_menus`) now returns to the overworld, not taught, TM unspent (1,291 frames) |
| **Q5 PASS** | Treecko fixture vs Skarmory: `no plan` — "Sceptile would never be fielded against Skarmory" | as predicted |
| Q6 **FAIL (predicted)** | the driver pointed at Q1's own end state: Loudred now has a credible answer ⇒ `no plan` | the vacuity test holds — the grade cannot pass having done nothing |

**The continue check (Q1/Q1b/Q2/Q2b).** Aimed first at the Fortree gym door's front, then at the Pokémon Center's
door (production's next step after the preparation is `heal_in_pokemon_center(FortreeCity)`); both NO-PATH.
`probe_gymtm_reach.py` (observe-only) showed why: from `devon_scope_got.ss1`'s tile, ROUTE120 (13,16), `calculate_path`
reaches only (10,16) and (16,16) — the fixture stands on a pathfinder ISLAND (the Route 120 bridge), with or without
the teach. ⇒ For a MENU-ONLY act the honest continue grade is: the player did not move, and the same reachability probe
reads identically before and after, with a positive control (the two bridge tiles path both times). That is what
Q1c/Q2c/Q4c pass. ⚠ Filed as an observation, not a KI: the story's own navigator leaves this spot in real runs; only
the plain planner cannot from here.

## ⛔ THE REVIEW KICKED BACK A DEAD RECORDER — and the real-battle drive that answers it

The adversarial review (Claude `reviewer`) found that design 4's recorder read `_what` two lines BEFORE its assignment
inside the [TURN] instrumentation's try: an `UnboundLocalError` on every decision, swallowed by the `except`. ⇒ the
decision log never received an entry (no wall could ever be named in real play — RULING 19 a silent no-op), AND the
pre-existing `[TURN]` event stopped for EVERY battle. Q1-Q6 could not see it (they seed `_loss_foe_history`); gate G1b
could not see it (it checked the recorder's POSITION, not whether it RUNS). Fixed (below `_what`); gate G1c now executes
the real try-body with no except (its fault arm — the shipped order — fails 4 checks).

| # | Result | vs prediction (addendum 2, `096c9722`) |
|---|---|---|
| **R1 PASS** (`--driver gymtmbattle`, `fortree_gym_wedge.ss1`, production `do_fortree_gym()`, hooks delegated to a real `StoryMode`) | 4 trainer battles, decisions 31 / 13 / 6 / 40, **90 `[TURN]` events**; the three gym trainers (parties incl. Skarmory, Tropius, Swablu, Pelipper) named `None`; **Winona named `Winona`**; the team LOST to her and it was filed `{'Tropius': 1, 'Skarmory': 5}` (five of six of ours went down facing Skarmory); the won trainer battles filed nothing | **as predicted** — including the positive leader filing, which the prediction called a coin flip |

**An observation R1 made that the planner does not model:** Sceptile — which the reach filter calls "never fielded"
against Skarmory (2x incoming) — DID face Skarmory, as the LAST mon standing (its final decisions: Leaf Blade at 1 PP,
0.25x). The reach filter predicts who is sent in FIRST. It can only REFUSE a teach, so it errs conservative; on this
fixture nothing it refused could have helped (Sceptile learns only TM39, which is 1x on Skarmory).

**The review's non-blocking risks, addressed:** the decision log drops its OLDEST entry at the cap (each mon's LAST
decision is what names the wall); a taught recipient's deposit protection ends when that boss's badge is earned; the
"seen used" wait releases after 3 further leader losses. All three gated (G1c, G8, G6).

## What is NOT shown here (so nobody reads more into the drives)

* **No drive TAUGHT and then FOUGHT.** R1 proves the recorder, the naming and the filing in real battles; whether a
  taught move is then USED against the wall is for the next batch: `[GYM_TM]` events, loss lines ending
  `; Winona (the leader)`, and `[TURN] … UseMove:<taught move> … vs <wall>` in a run that taught.
* The duel estimate ignores the leader's two Hyper Potions and stat stages; `MIN_SHARE` 0.5 is a judgment, logged per
  refusal (`deals only N% of X's HP`) so a batch can calibrate it.
* Expected benefit is small and a FREQUENCY question: on the fixtures, only the Torchic core (Loudred) qualifies, and
  only vs Skarmory/Swablu/Pelipper walls; an Altaria wall has no fielded Rock Tomb learner on any fixture.
