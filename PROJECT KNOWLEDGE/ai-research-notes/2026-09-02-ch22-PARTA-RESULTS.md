# §Ch22 PART A — LIVE PROBE: RESULTS, GRADED AGAINST THE PRE-REGISTERED PREDICTIONS

> ‼ **THIS FILE IS MEASUREMENT, NOT RECALL.** Unlike the other §Ch22 notes it reports what a live
> emulator did, so it OUTRANKS the recon wherever they disagree. Graded against
> `2026-09-02-ch22-PARTA-PREDICTIONS.md`, committed BEFORE the run.
> Driver `--driver ch22probe`, fixture `post_hm07.ss1` (md5 asserted before the run).
> Evidence: `tools/story-dev/evidence/2026-09-02-ch22probe-PARTA.txt` (+ `.stdout.txt`).

**VERDICT: `ACCEPTANCE: PASS` — P0–P5 all executed, `whiteouts=0`, `encounters=0`, `frames=3958`.**
⚠ **And every prediction held**, which is worth stating carefully: it does not mean I was clever, it
means the decomp recon was accurate — and it is now MEASURED, which is the only status that counts.

---

## 1. ⛔⛔ THE HEADLINE — THE COLLISION ORACLE IS BLIND HERE, AND IT IS NOW PROVEN BY MEASUREMENT

The probe stepped on **exactly one** ice tile — derived from the live grid, never hardcoded — and
re-read both grids:

```
P3 AT ENTRY          metatile_diff=0   collision_diff=0
P3 STEP TARGET (8, 19)   (southernmost thin ice in the player's own column)
P3 AFTER ONE STEP    metatile_diff=1 at [(8,19)]  values=[((8,19), 0x20d, 0x20e)]
P3                   collision_diff=0 at []
P3 VERDICT: the collision reader is BLIND — CONFIRMED.
```

**The floor demonstrably changed (`0x20d` thin ice → `0x20e` cracked) and `_live_collision_grid` saw
NOTHING.** ⇒ `probe_live_mapgrid.py` would report 0 differences and **PASS** on a catastrophically
wrong model of this map.

‼ **This is the first time this project has demonstrated an instrument's false negative by
MEASUREMENT rather than by argument.** The static proof (three links: our reader keeps only
`(block & 0x0C00) >> 10`; `ScrCmd_setmetatile` ORs `MAPGRID_IMPASSABLE` only when arg 4 is TRUE; the
gym passes FALSE on every one) was already convincing — and this project's own history is that
convincing arguments are exactly where the mistakes live. The A/B cost 3,958 frames.
⇒ **The working instrument is `_live_metatile_grid()` (`sootopolis.py`, added for this), and/or
`ICE_STEP_COUNT`, which the probe watched go 1 → 2 on the single step.**

## 2. THE PUZZLE IS EXACTLY AS THE DECOMP DESCRIBED — 64 TILES, THREE SECTIONS, FORCED

```
P3 THIN ICE n=64  rows=[6,7,8,9, 12,13,14, 17,18,19]
                  per_row=[10,9,9,10,  7,5,7,   2,3,2]
P3 LOCKED STAIRS (0x20F) n=6 at [(8,4),(8,5),(8,10),(8,11),(8,15),(8,16)]
```

Grouping by the stair rows gives the three sections, **from the entrance northward**:
| section | rows | tiles | unlock threshold |
|---|---|---|---|
| A | 17–19 | **7** | `ICE_STEP_COUNT` 8 |
| B | 12–14 | **19** | 28 |
| C | 6–9 | **38** | 67 |

7 + 19 + 38 = **64**, and 1 + 7 = 8, 8 + 19 = 27 (+1 unlock = 28), 28 + 38 = 66 (+1 = 67). The
arithmetic closes exactly ⇒ **every tile exactly once, zero revisits. Exact cover, confirmed live.**

## 3. THE PLANNER IS BLIND TOO — AND CONFIDENTLY SO

```
P4 calculate_path((8,19) -> Juan (8,3)): **SUCCEEDS**, 16 wp, live_walls_on_it=0
```
Sixteen waypoints straight up column x=8 — **through all six locked-stair tiles and 64 un-walked
ice tiles**, with the collision oracle calling the route clean. ⇒ `calculate_path` must NEVER be
used inside this gym; the route has to be a **precomputed table**.

## 4. THE PUZZLE RESETS ON EVERY ENTRY — WHICH IS WHAT MAKES A TABLE SAFE

```
P5 RE-ENTERED ICE_STEP_COUNT=1  metatile_diff=0
```
Walked out, walked back in: virgin ice, counter reset. ⇒ a failed attempt costs the walk, never the
chapter, and a static route table is valid on every entry. **No runtime solver is needed**, and one
would only add nondeterminism.

## 5. THE READINESS NUMBERS THE DOCS DID NOT HAVE

| reading | measured |
|---|---|
| party | **6 alive, 629/694 (91%)**, lead Swellow 52/115, `fainted_pids=[]` |
| after the heal | **694/694**, PID-keyed, `not_full=[] missing=[]` |
| **money** | ⭐ **67,466** |
| bag | Potion **1**, Super/Hyper Potion **0**, Revive **0**, Full Heal **0**, Full Restore **0**, X Attack **2**, Escape Rope 1 |

⇒ **MONEY IS NOT THE CONSTRAINT.** The recon listed "buy healing" as an option gated on unverified
money; at 67,466 the bot can afford a full stock of Hyper Potions / Revives / Full Restores. The
readiness problem is **levels and type coverage**, not funds.
⚠ The Mart's actual stock list is still UNVERIFIED — the probe did not enter the shop.
⛔ The Escape Rope is dead weight: both gym floors are `allow_escaping: false`.

## 6. ALSO CONFIRMED IN PASSING
* The Poké Center heal exits onto **(43,32)** — the apron — while the WARP is (43,31). Both numbers
  in the docs are right, for different things.
* `heal_in_pokemon_center(PokemonCenter.SootopolisCity)` works on this map, PID-verified.
* The gym apron (31,32) is 24 wp from the PC exit and 1 wp from (31,33).
* Entering the gym costs nothing and is fully reversible.

## 7. WHAT REMAINS UNMEASURED (do not build past these without settling them)
1. **The Mart's stock list and prices** — needed before a shopping leg.
2. **How under-levelled the party actually is.** Only a live Juan drive settles it, and the first one
   is EXPECTED TO LOSE — that loss is the measurement, not a failure.
3. **The route table itself.** The 64 tiles are now known live; the ORDER is not. It must be
   generated from `map.bin` and re-derived by a test, then verified live step-by-step against
   `_live_metatile_grid` before it is trusted.
4. **B1F** — never entered. The exit fall, the ten trainers, and the ladder at (11,22) are all still
   decomp-only.
